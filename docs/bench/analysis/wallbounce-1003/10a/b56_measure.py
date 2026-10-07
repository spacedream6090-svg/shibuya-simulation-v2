"""10a の準備: テープ版 4 に B5・B6(本人ブロック)の本文を入れたときの容量を測る。

使い方(リポのルートで):

    python b56_measure.py run --arm default --tape <作業用>/tape_default --out <作業用>/default.json
    python b56_measure.py run --arm mem_rel_store --tape <作業用>/tape_mem --out <作業用>/mem.json

やり方:
- ``src`` は編集しない。このプロセスの中でだけ ``PerceptionRendererAdapter.render`` を包み、
  知覚側の ``Rendered.blocks["B5"]``・``["B6"]`` のバイト列を描画ごとに控える(エンジンの挙動は不変。
  包みは値を読むだけ)。
- ランは ``shibuya.cli.run``(mock・5,000 体・seed 1・1 シミュ日・テープつき)。
- テープ(calls.parquet・blocks.parquet)の行数とバイト、B5・B6 の大きさの分布、
  B5・B6 を calls に 2 列足して zstd / gzip で書き直したときの増分を測る。

絶対パスは JSON に書かない。壁時計は参考の値。
"""

from __future__ import annotations

import argparse
import gzip
import io
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

ARMS: dict[str, dict[str, Any]] = {
    # 現行の既定(w6_regen_measure の v3_default と同じ呼び方)
    "default": {"vocab_version": "v3", "activity": True},
    # 記憶・関係・店の記憶を ON にした腕
    "mem_rel_store": {"vocab_version": "v3", "activity": True, "memory": "on",
                      "relations": "on", "store_memory": "on"},
}


def _dist(a: np.ndarray) -> dict[str, float]:
    if a.size == 0:
        return {"n": 0}
    return {
        "n": int(a.size),
        "mean": round(float(a.mean()), 1),
        "p50": float(np.percentile(a, 50)),
        "p95": float(np.percentile(a, 95)),
        "max": int(a.max()),
        "min": int(a.min()),
        "sum": int(a.sum()),
    }


def cmd_run(args: argparse.Namespace) -> int:
    import pyarrow as pa
    import pyarrow.parquet as pq

    from shibuya import cli
    from shibuya.engine import llm_bridge as lb

    rec: dict[str, list[bytes]] = {"B5": [], "B6": [], "text": []}
    orig = lb.PerceptionRendererAdapter.render

    def wrapped(self: Any, **kw: Any) -> Any:
        inner = self.renderer
        if not getattr(inner, "_b56_wrapped", False):
            inner_render = inner.render

            def capture(*a: Any, **k: Any) -> Any:
                out = inner_render(*a, **k)
                rec["B5"].append(bytes(out.blocks["B5"]))
                rec["B6"].append(bytes(out.blocks["B6"]))
                rec["text"].append(len(out.text.encode("utf-8")).to_bytes(4, "little"))
                return out

            inner.render = capture  # type: ignore[method-assign]
            inner._b56_wrapped = True
        return orig(self, **kw)

    lb.PerceptionRendererAdapter.render = wrapped  # type: ignore[method-assign]

    tape = Path(args.tape)
    t0 = time.perf_counter()
    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, tape_path=str(tape),
                  **ARMS[args.arm])
    wall = time.perf_counter() - t0

    calls_p = tape / "calls.parquet"
    blocks_p = tape / "blocks.parquet"
    calls = pq.read_table(calls_p)
    blocks = pq.read_table(blocks_p)
    n_rows = int(calls.num_rows)
    n_render = len(rec["B5"])

    b5 = np.array([len(x) for x in rec["B5"]], dtype=np.int64)
    b6 = np.array([len(x) for x in rec["B6"]], dtype=np.int64)
    b56 = b5 + b6
    prompt = np.array([int.from_bytes(x, "little") for x in rec["text"]], dtype=np.int64)
    uniq5 = set(rec["B5"])
    uniq6 = set(rec["B6"])

    # B5・B6 の本文を calls に 2 列足して書き直す(版 4 の形の近似)。行の順と描画の順が揃う前提は
    # 行数と描画数が一致するときだけ置く(一致しなければ描画順のまま別の表で測る)。
    aligned = n_rows == n_render
    b5s = [x.decode("utf-8") for x in rec["B5"]]
    b6s = [x.decode("utf-8") for x in rec["B6"]]
    if aligned:
        t4 = calls.append_column("b5_text", pa.array(b5s, pa.string())).append_column(
            "b6_text", pa.array(b6s, pa.string()))
    else:
        t4 = None
    sizes: dict[str, Any] = {}
    for comp in ("zstd", "gzip"):
        buf = io.BytesIO()
        pq.write_table(calls, buf, compression=comp)
        base = buf.tell()
        only = pa.table({"b5_text": pa.array(b5s, pa.string()), "b6_text": pa.array(b6s, pa.string())})
        buf2 = io.BytesIO()
        pq.write_table(only, buf2, compression=comp)
        row: dict[str, Any] = {"calls_rewritten_bytes": base, "b56_only_table_bytes": buf2.tell()}
        if t4 is not None:
            buf3 = io.BytesIO()
            pq.write_table(t4, buf3, compression=comp)
            row["calls_plus_b56_bytes"] = buf3.tell()
            row["increment_bytes"] = buf3.tell() - base
            row["increment_per_call"] = round((buf3.tell() - base) / max(1, n_rows), 2)
        sizes[comp] = row
    raw_concat = b"\n".join(rec["B5"]) + b"\n" + b"\n".join(rec["B6"])
    gz_concat = len(gzip.compress(raw_concat, 6))

    doc = {
        "schema": "shibuya.bench/wallbounce-1003/10a-b56/1",
        "arm": args.arm,
        "args": ARMS[args.arm],
        "agents": args.agents,
        "seed": args.seed,
        "final_hash": res.final_hash[:16],
        "llm_calls": int(res.llm_calls),
        "tape": {
            "calls_rows": n_rows,
            "calls_bytes": calls_p.stat().st_size,
            "blocks_rows": int(blocks.num_rows),
            "blocks_bytes": blocks_p.stat().st_size,
            "total_bytes": calls_p.stat().st_size + blocks_p.stat().st_size,
            "bytes_per_call": round((calls_p.stat().st_size + blocks_p.stat().st_size) / max(1, n_rows), 2),
            "calls_bytes_per_call": round(calls_p.stat().st_size / max(1, n_rows), 2),
            "compression": "zstd(TAPE_COMPRESSION)",
            "column_names": calls.column_names,
        },
        "renders": n_render,
        "renders_equal_rows": aligned,
        "b5_bytes": _dist(b5),
        "b6_bytes": _dist(b6),
        "b5_plus_b6_bytes": _dist(b56),
        "prompt_text_bytes": _dist(prompt),
        "b56_share_of_prompt": round(float(b56.sum()) / max(1, int(prompt.sum())), 4),
        "unique_b5": {"n": len(uniq5), "bytes": sum(len(x) for x in uniq5)},
        "unique_b6": {"n": len(uniq6), "bytes": sum(len(x) for x in uniq6)},
        "compressed": sizes,
        "gzip_concat_b56": {"raw_bytes": len(raw_concat), "gzip6_bytes": gz_concat},
        "wall_s_reference": round(wall, 1),
    }
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8",
                              newline="\n")
    if args.samples:
        idx = np.linspace(0, max(0, n_render - 1), num=min(5, n_render), dtype=int)
        lines = [f"--- 描画 {int(i)} ---\n[B5]\n{b5s[i]}\n[B6]\n{b6s[i]}\n" for i in idx]
        Path(args.samples).write_text("".join(lines), encoding="utf-8", newline="\n")
    print(json.dumps({k: doc[k] for k in ("arm", "final_hash", "llm_calls", "renders", "b5_plus_b6_bytes")},
                     ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("run")
    sp.add_argument("--arm", choices=sorted(ARMS), required=True)
    sp.add_argument("--tape", required=True)
    sp.add_argument("--out", required=True)
    sp.add_argument("--samples", default="")
    sp.add_argument("--world", default="data/world/v2")
    sp.add_argument("--agents", type=int, default=5_000)
    sp.add_argument("--seed", type=int, default=1)
    args = ap.parse_args(argv)
    return {"run": cmd_run}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
