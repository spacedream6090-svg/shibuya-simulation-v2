#!/usr/bin/env python3
"""fleet_gen — 1回限りの静的生成(W14 看板文・W15 セル静的文・W17 スケジュール)を vLLM 艦隊へ流す運搬役。

設計上の位置: 構築段階(build/*)は**純関数**でなければならない(世界データ構築仕様 §2.1)。LLM 呼び出しは
非決定な外部 I/O なので段階の外に置く。段階は「プロンプト jsonl を書く」→本ツールが「応答 jsonl を作る」→
段階が「応答を入力資産としてハッシュし検証・凍結する」。本ツールは標準ライブラリのみ(サーバー上でも動く)。

入出力
- 入力 prompts.jsonl: 1 行 1 呼 ``{"id": str, "system": str, "user": str, "max_tokens": int,
  "temperature": float, "seed": int, "repeat": int(既定 1)}``。``repeat`` は同一プロンプトを何回生成するか
  (W14 の「同店 2 回生成でバイト一致」ゲート用)。
- 出力 responses.jsonl: 1 行 1 生成 ``{"id", "rep", "model", "endpoint", "text", "finish_reason",
  "prompt_tokens", "completion_tokens", "latency_s", "request_sha256", "ts"}``。追記型・再実行は済みの
  (id, rep) を飛ばす(resume)。

失敗の意味論(実装計画書 §7): 接続エラー=同一レプリカ 1 回→別レプリカ 1 回。e2e タイムアウト 300 s(expedient)。
それでも失敗した呼は ``failures.jsonl`` に記録し**破棄しない**(再実行で拾う)。レプリカ配分= ``blake2b(id) mod N``
(xxhash は標準ライブラリに無いので blake2b で代用・分配の目的は同じ)。

使い方(サーバー上)::

    python3 fleet_gen.py --prompts w14_prompts.jsonl --out w14_responses.jsonl \
        --endpoints http://127.0.0.1:8100 --model Qwen3-32B-AWQ --conc 8

逐次ループ宣言(P4): 呼び出しループは ThreadPoolExecutor(conc×endpoints 並行)。段階本体ではないので性能予算の対象外。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import queue
import sys
import threading
import time
import urllib.error
import urllib.request

E2E_TIMEOUT_S = 300


def _post_json(url: str, payload: dict, timeout: int = E2E_TIMEOUT_S) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def discover_model(endpoint: str) -> str:
    d = _post_json.__wrapped__(endpoint) if hasattr(_post_json, "__wrapped__") else None  # pragma: no cover
    raise RuntimeError("unreachable")


def get_models(endpoint: str) -> list[str]:
    with urllib.request.urlopen(endpoint.rstrip("/") + "/v1/models", timeout=30) as r:
        d = json.loads(r.read().decode("utf-8"))
    return [m["id"] for m in d.get("data", [])]


def request_sha256(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def build_payload(model: str, item: dict, rep: int) -> dict:
    # seed は rep ごとにずらさない: 「同一 seed・同一プロンプトで 2 回」がバイト一致ゲートの定義。
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": item["system"]},
            {"role": "user", "content": item["user"]},
        ],
        "max_tokens": int(item.get("max_tokens", 256)),
        "temperature": float(item.get("temperature", 0.0)),
        "seed": int(item.get("seed", 0)),
        "top_p": 1.0,
        "chat_template_kwargs": {"enable_thinking": bool(item.get("thinking", False))},
    }


def call_once(endpoint: str, payload: dict) -> tuple[str, str, int, int]:
    d = _post_json(endpoint.rstrip("/") + "/v1/chat/completions", payload)
    ch = d["choices"][0]
    usage = d.get("usage", {})
    return (
        ch["message"].get("content") or "",
        ch.get("finish_reason", ""),
        int(usage.get("prompt_tokens", 0)),
        int(usage.get("completion_tokens", 0)),
    )


def replica_of(item_id: str, n: int) -> int:
    return int.from_bytes(hashlib.blake2b(item_id.encode("utf-8"), digest_size=8).digest(), "little") % n


def load_done(out_path: str) -> set[tuple[str, int]]:
    done: set[tuple[str, int]] = set()
    if os.path.exists(out_path):
        with open(out_path, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                    done.add((r["id"], int(r["rep"])))
                except Exception:
                    continue
    return done


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--prompts", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--endpoints", required=True, help="カンマ区切り http://host:port")
    ap.add_argument("--model", default="", help="served-model-name。省略時は /v1/models の先頭")
    ap.add_argument("--conc", type=int, default=8, help="1 エンドポイントあたりの並行数")
    ap.add_argument("--limit", type=int, default=0, help="先頭 N 件だけ(試走)")
    ap.add_argument("--failures", default="", help="失敗記録 jsonl(既定 <out>.failures.jsonl)")
    args = ap.parse_args(argv)

    endpoints = [e.strip() for e in args.endpoints.split(",") if e.strip()]
    model = args.model or get_models(endpoints[0])[0]
    fail_path = args.failures or (args.out + ".failures.jsonl")
    done = load_done(args.out)

    items: list[dict] = []
    with open(args.prompts, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))
    if args.limit:
        items = items[: args.limit]
    jobs: list[tuple[dict, int]] = []
    for it in items:
        for rep in range(int(it.get("repeat", 1))):
            if (it["id"], rep) not in done:
                jobs.append((it, rep))
    total = len(jobs)
    print(f"[fleet_gen] model={model} endpoints={len(endpoints)} jobs={total} (skipped done={len(done)})", flush=True)

    q: queue.Queue[tuple[dict, int]] = queue.Queue()
    for j in jobs:
        q.put(j)
    lock = threading.Lock()
    out_f = open(args.out, "a", encoding="utf-8")
    fail_f = open(fail_path, "a", encoding="utf-8")
    counters = {"ok": 0, "fail": 0, "ctok": 0}
    t0 = time.time()

    def worker(ep_idx: int) -> None:
        while True:
            try:
                it, rep = q.get_nowait()
            except queue.Empty:
                return
            primary = replica_of(it["id"], len(endpoints))
            order = [endpoints[primary], endpoints[primary], endpoints[(primary + 1) % len(endpoints)]]
            payload = build_payload(model, it, rep)
            rsha = request_sha256(payload)
            err = ""
            for ep in order:
                t1 = time.time()
                try:
                    text, fin, ptok, ctok = call_once(ep, payload)
                    rec = {
                        "id": it["id"], "rep": rep, "model": model, "endpoint": ep, "text": text,
                        "finish_reason": fin, "prompt_tokens": ptok, "completion_tokens": ctok,
                        "latency_s": round(time.time() - t1, 3), "request_sha256": rsha,
                        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    }
                    with lock:
                        out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        out_f.flush()
                        counters["ok"] += 1
                        counters["ctok"] += ctok
                        n = counters["ok"] + counters["fail"]
                        if n % 200 == 0 or n == total:
                            el = time.time() - t0
                            print(f"[fleet_gen] {n}/{total} ok={counters['ok']} fail={counters['fail']} "
                                  f"{counters['ctok']/max(el,1e-9):.0f} ctok/s {el:.0f}s", flush=True)
                    err = ""
                    break
                except (urllib.error.URLError, TimeoutError, OSError, KeyError, ValueError) as e:
                    err = f"{type(e).__name__}: {e}"
                    time.sleep(1.0)
            if err:
                with lock:
                    fail_f.write(json.dumps({"id": it["id"], "rep": rep, "error": err, "request_sha256": rsha},
                                            ensure_ascii=False) + "\n")
                    fail_f.flush()
                    counters["fail"] += 1

    threads = [threading.Thread(target=worker, args=(i,), daemon=True)
               for i in range(args.conc * len(endpoints))]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    out_f.close()
    fail_f.close()
    el = time.time() - t0
    print(f"[fleet_gen] DONE ok={counters['ok']} fail={counters['fail']} ctok={counters['ctok']} "
          f"wall={el:.0f}s ({counters['ctok']/max(el,1e-9):.0f} ctok/s)", flush=True)
    return 0 if counters["fail"] == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
