# -*- coding: utf-8 -*-
"""run_probe.py — 品質プローブv0 の実行器(サーバー側で動かす。標準ライブラリ+urllibのみ)。

vLLM の OpenAI 互換エンドポイント(複数ポート)に、モデル×問題×(⑥は3観測)を投げ、
1呼び出しごとに quality_ledger.csv へ逐次追記する。

前提(サーバー側で満たしておくこと):
  - 各 vLLM サーバーを `VLLM_BATCH_INVARIANT=1` 付きで起動していること
    (温度0でもバッチ非不変性で出力が揺れる。ベンチ台帳の実測ではコストは-2%以下)。
  - 並行度は記録対象。既定は 1エンドポイントあたり 8(--conc で変更)。
    バッチサイズが結果に効くので、比較する測定は同じ並行度で回すこと。

使い方の例:
  # まず接続確認と1問だけの試走(ネットワークなしなら --dry-run)
  python run_probe.py --endpoints http://127.0.0.1:8000 --limit 3
  # 本番(3モデルを3ポートで)
  python run_probe.py --endpoints http://127.0.0.1:8000,http://127.0.0.1:8001,http://127.0.0.1:8002 \
      --quants int8,int8,awq --out quality_ledger.csv
  # 安定性サブセット(②④のみ・temp 0.7 × R=5)
  python run_probe.py --endpoints http://127.0.0.1:8000 --stability
"""

import argparse
import csv
import io
import json
import os
import queue
import ssl
import sys
import threading
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scorer  # noqa: E402

SEED = 20260905

LEDGER_COLUMNS = [
    # --- 指定の列(この順序を変えない)---
    "model", "quant", "family", "probe_id", "variant", "tier", "seed", "score",
    "judge_type", "parse_ok", "ja_char_ratio", "out_tokens", "latency_ms", "raw_output_path",
    # --- 追加列(集計と質的分析に必要・末尾に足す)---
    "kana_ratio", "latin_ratio", "other_script_ratio", "parse_mode",
    "action", "action_src", "destination", "verdict",
    "n_violations", "violations", "gold_ok", "term_detected", "term_expected", "over_refusal",
    "hallucination_rate", "recall_rate", "diff_valid", "diff_semantic_ok",
    "prompt_tokens", "approx_tokens", "temperature", "batch_invariant", "concurrency",
    "endpoint", "engine_ver", "ts", "item_set_hash", "prompt_template_hash", "notes",
]


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

def _http_json(url, payload=None, timeout=300):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    if payload is None:
        req = urllib.request.Request(url, method="GET")
    else:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST",
                                     headers={"Content-Type": "application/json"})
    opener = urllib.request.urlopen
    with opener(req, timeout=timeout, context=ctx if url.startswith("https") else None) as r:
        return json.loads(r.read().decode("utf-8"))


def discover_model(endpoint):
    try:
        d = _http_json(endpoint.rstrip("/") + "/v1/models", timeout=30)
        return d["data"][0]["id"]
    except Exception as e:
        print("[warn] /v1/models failed for %s: %s" % (endpoint, e))
        return "unknown"


def call_chat(endpoint, model, system_block, user_block, max_tokens, temperature, seed,
              retries=3, no_thinking=True):
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system_block},
                     {"role": "user", "content": user_block}],
        "temperature": temperature,
        "top_p": 1.0,
        "max_tokens": max_tokens,
        "seed": seed,
        "n": 1,
        "stream": False,
    }
    if no_thinking:
        # Qwen3 系の思考モードを切る。受け付けないサーバーでは無視される。
        payload["chat_template_kwargs"] = {"enable_thinking": False}
    last = None
    for attempt in range(retries):
        t0 = time.time()
        try:
            d = _http_json(endpoint.rstrip("/") + "/v1/chat/completions", payload)
            dt = (time.time() - t0) * 1000.0
            txt = d["choices"][0]["message"].get("content") or ""
            usage = d.get("usage") or {}
            return txt, dt, usage.get("completion_tokens"), usage.get("prompt_tokens"), ""
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", "replace")[:300]
            except Exception:
                pass
            last = "HTTP %s %s" % (e.code, body)
            if e.code == 400 and "chat_template_kwargs" in body and no_thinking:
                no_thinking = False
                payload.pop("chat_template_kwargs", None)
                continue
        except Exception as e:
            last = "%s: %s" % (type(e).__name__, e)
        time.sleep(1.5 * (attempt + 1))
    return "", 0.0, None, None, last or "unknown_error"


# ---------------------------------------------------------------------------
# 仕事の組み立て
# ---------------------------------------------------------------------------

def build_tasks(probes, families, stability, repeats):
    """(probe, variant, tier, temperature, seed) のリストを作る。"""
    tasks = []
    for p in probes:
        if families and p["family"] not in families:
            continue
        if stability:
            if not p.get("stability_subset"):
                continue
            for i in range(repeats):
                tasks.append((p, "stab%d" % i, "", 0.7, SEED + i))
            continue
        if p["family"] == 6:
            for v in ("full", "v0", "v1"):
                tasks.append((p, v, p["family6_variants"][v]["salience_tier"], 0.0, SEED))
        else:
            tasks.append((p, "main", "", 0.0, SEED))
    return tasks


def prompt_for(p, variant):
    if p["family"] == 6 and variant in ("full", "v0", "v1"):
        d = p["family6_variants"][variant]
        return d["system_block"], d["observation"] + "\n" + p["question"], d["approx_tokens"]
    return (p["system_block"], p["observation"] + "\n" + p["question"],
            int(round((len(p["system_block"]) + len(p["observation"]) + len(p["question"])) / 1.30)))


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("--probes", default=os.path.join(here, "probes.jsonl"))
    ap.add_argument("--out", default=os.path.join(here, "quality_ledger.csv"))
    ap.add_argument("--raw-dir", default=os.path.join(here, "raw"))
    ap.add_argument("--endpoints", default="http://127.0.0.1:8000",
                    help="カンマ区切り。1エンドポイント=1モデル。")
    ap.add_argument("--models", default="", help="カンマ区切り。省略時は /v1/models から取得。")
    ap.add_argument("--quants", default="", help="カンマ区切り(int8/awq/bf16 等)。台帳の quant 列になる。")
    ap.add_argument("--engine-ver", default="")
    ap.add_argument("--conc", type=int, default=8, help="1エンドポイントあたりの並行呼び出し数。")
    ap.add_argument("--families", default="", help="例 1,3,6。省略で全系統。")
    ap.add_argument("--limit", type=int, default=0, help="先頭N件だけ流す(試走用)。")
    ap.add_argument("--stability", action="store_true", help="②④の安定性サブセットを temp0.7×R で回す。")
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--batch-invariant", default="1",
                    help="台帳に記録する値。サーバー起動時の VLLM_BATCH_INVARIANT と一致させること。")
    ap.add_argument("--dry-run", action="store_true", help="送信せずプロンプトの検査だけ行う。")
    a = ap.parse_args()

    probes = list(scorer.load_probes(a.probes).values())
    probes.sort(key=lambda p: (p["family"], p["id"]))
    fams = set(int(x) for x in a.families.split(",") if x.strip()) if a.families else None
    tasks = build_tasks(probes, fams, a.stability, a.repeats)
    if a.limit:
        tasks = tasks[:a.limit]

    hp = os.path.join(here, "item_set_hash.txt")
    item_hash = ""
    if os.path.exists(hp):
        item_hash = io.open(hp, encoding="utf-8").read().split("=")[-1].split("\n")[0].strip()

    endpoints = [e.strip() for e in a.endpoints.split(",") if e.strip()]
    models = [m.strip() for m in a.models.split(",") if m.strip()]
    quants = [q.strip() for q in a.quants.split(",") if q.strip()]

    if a.dry_run:
        print("dry-run: %d tasks, %d probes" % (len(tasks), len(probes)))
        seen = {}
        for p, v, tier, temp, sd in tasks:
            s, u, at = prompt_for(p, v)
            seen.setdefault(p["family"], []).append(at)
            if len(seen[p["family"]]) == 1:
                print("--- family %d %s (%s) approx_tokens=%d max_tokens=%d temp=%.1f"
                      % (p["family"], p["id"], v, at, p["max_tokens"], temp))
        for f in sorted(seen):
            xs = seen[f]
            print("family %d: n=%d approx_tokens mean=%d min=%d max=%d"
                  % (f, len(xs), sum(xs) // len(xs), min(xs), max(xs)))
        return

    if not models:
        models = [discover_model(e) for e in endpoints]
    while len(quants) < len(endpoints):
        quants.append("")

    os.makedirs(a.raw_dir, exist_ok=True)
    done = set()
    new_file = not os.path.exists(a.out)
    if not new_file:
        with io.open(a.out, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                done.add((r.get("model", ""), r.get("probe_id", ""), r.get("variant", "")))
        print("resume: %d rows already in ledger" % len(done))

    fh = io.open(a.out, "a", encoding="utf-8", newline="")
    writer = csv.DictWriter(fh, fieldnames=LEDGER_COLUMNS, extrasaction="ignore")
    if new_file:
        writer.writeheader()
        fh.flush()
    lock = threading.Lock()
    counters = dict(ok=0, err=0)

    def worker(ei, q):
        ep, model, quant = endpoints[ei], models[ei], quants[ei]
        safe_model = "".join(c if c.isalnum() or c in "-_." else "_" for c in model)
        rawdir = os.path.join(a.raw_dir, safe_model)
        os.makedirs(rawdir, exist_ok=True)
        while True:
            try:
                p, variant, tier, temp, sd = q.get_nowait()
            except queue.Empty:
                return
            try:
                if (model, p["id"], variant) in done:
                    continue
                sysb, userb, approx = prompt_for(p, variant)
                txt, dt, otok, ptok, err = call_chat(
                    ep, model, sysb, userb, p["max_tokens"], temp, sd)
                rp = os.path.join(rawdir, "%s__%s.txt" % (p["id"], variant))
                with io.open(rp, "w", encoding="utf-8", newline="\n") as rf:
                    rf.write(txt if txt else ("<<ERROR>> " + (err or "")))
                sc = scorer.score_call(p, txt)
                row = dict(
                    model=model, quant=quant, family=p["family"], probe_id=p["id"],
                    variant=variant, tier=tier or sc.get("tier", ""), seed=sd,
                    score=sc["score"], judge_type=p["judge"], parse_ok=sc["parse_ok"],
                    ja_char_ratio=sc["ja_char_ratio"], out_tokens=otok if otok is not None else "",
                    latency_ms=round(dt, 1), raw_output_path=os.path.relpath(rp, here),
                    kana_ratio=sc["kana_ratio"], latin_ratio=sc["latin_ratio"],
                    other_script_ratio=sc["other_script_ratio"], parse_mode=sc["parse_mode"],
                    action=sc["action"], action_src=sc["action_src"], destination=sc["destination"],
                    verdict=sc.get("verdict", ""), n_violations=sc["n_violations"],
                    violations="|".join(sc["violations"]), gold_ok=sc["gold_ok"],
                    term_detected=sc["term_detected"], term_expected=sc["term_expected"],
                    over_refusal=sc.get("over_refusal", ""),
                    hallucination_rate=sc.get("hallucination_rate", ""),
                    recall_rate=sc.get("recall_rate", ""),
                    diff_valid=sc.get("diff_valid", ""), diff_semantic_ok=sc.get("diff_semantic_ok", ""),
                    prompt_tokens=ptok if ptok is not None else "", approx_tokens=approx,
                    temperature=temp, batch_invariant=a.batch_invariant, concurrency=a.conc,
                    endpoint=ep, engine_ver=a.engine_ver,
                    ts=time.strftime("%Y-%m-%dT%H:%M:%S"), item_set_hash=item_hash,
                    prompt_template_hash="", notes=err or "")
                with lock:
                    writer.writerow(row)
                    fh.flush()
                    counters["err" if err else "ok"] += 1
                    n = counters["ok"] + counters["err"]
                    if n % 25 == 0:
                        print("  %d/%d done (err=%d)" % (n, len(tasks), counters["err"]))
            finally:
                q.task_done()

    print("endpoints=%s models=%s tasks=%d" % (endpoints, models, len(tasks)))
    t0 = time.time()
    threads = []
    for ei in range(len(endpoints)):
        q = queue.Queue()
        for t in tasks:
            q.put(t)
        for _ in range(a.conc):
            th = threading.Thread(target=worker, args=(ei, q), daemon=True)
            th.start()
            threads.append(th)
    for th in threads:
        th.join()
    fh.close()
    print("wrote %s in %.1fs (ok=%d err=%d)"
          % (a.out, time.time() - t0, counters["ok"], counters["err"]))
    print("次: python scorer.py --ledger %s --probes %s --report report.md" % (a.out, a.probes))


if __name__ == "__main__":
    main()
