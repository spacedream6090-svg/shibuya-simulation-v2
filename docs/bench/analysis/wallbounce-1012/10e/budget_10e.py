"""10e(E2): 保存の予算の再宣言の材料=日の境目の状態のファイル(npz+json)の大きさと読み書きの時間を 5,000 体で測る。

各構成を mock 5,000 体・seed 1・2 日のランで T=1440(日の境目)で止めて状態を書き、ファイルのバイト数・展開した後の
合計(npz の部品の宣言の合計=``state_codec.MAX_UNCOMPRESSED_BYTES`` と比べる量)・書きと読みの時間(中央値 3 回)を出す。
39 万体(W16 の母集団 390,067 人)への外挿は線形(**推測**)。

    python docs/bench/analysis/wallbounce-1012/10e/budget_10e.py --scratch <短い作業用> --out <置き場>/budget_10e.json

絶対パスは JSON に書かない。
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
import zipfile
from pathlib import Path

N_FULL = 390_067
CONFIGS = {
    "v3_default": {"vocab_version": "v3", "activity": True},
    "v3_mem_rel": {"vocab_version": "v3", "memory": "on", "relations": "on"},
    "v3_all_arms": {"vocab_version": "v3", "memory": "on", "relations": "on", "store_memory": "on",
                    "familiarity": "on"},
}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--agents", type=int, default=5_000)
    ap.add_argument("--only", default="")
    args = ap.parse_args(argv)
    from shibuya import cli
    from shibuya.engine import resume as RS
    from shibuya.engine import state_codec as SC

    out: dict = {"agents": args.agents, "n_full": N_FULL, "max_uncompressed_bytes": SC.MAX_UNCOMPRESSED_BYTES,
                 "runs": {}}
    names = [s for s in args.only.split(",") if s] or list(CONFIGS)
    for name in names:
        kw = CONFIGS[name]
        st = Path(args.scratch) / f"budget_{name}"
        res = cli.run(n_agents=args.agents, seed=1, world_dir="data/world/v2", sim_days=2, state_out=st,
                      stop_at_tick=1440, **kw)
        f = res.resume["state_files"][-1]
        path = st / f["file"]
        size = path.stat().st_size
        with zipfile.ZipFile(path) as z:
            unz = sum(int(i.file_size) for i in z.infolist())
        bundle = RS.read_state(path)
        w, r = [], []
        for i in range(3):
            t = time.perf_counter()
            RS.write_state(st / f"w{i}" / "x.npz", bundle)
            w.append(time.perf_counter() - t)
            t = time.perf_counter()
            RS.read_state(st / f"w{i}" / "x.npz")
            r.append(time.perf_counter() - t)
        per = size / args.agents
        per_unz = unz / args.agents
        out["runs"][name] = {
            "final": res.final_hash[:16], "bytes": size, "bytes_per_agent": round(per, 1),
            "uncompressed_bytes": unz, "uncompressed_per_agent": round(per_unz, 1),
            "write_s_median": round(statistics.median(w), 3), "read_s_median": round(statistics.median(r), 3),
            "extrapolated_bytes_390k": int(per * N_FULL), "extrapolated_uncompressed_390k": int(per_unz * N_FULL),
            "uncompressed_390k_over_cap": bool(per_unz * N_FULL > SC.MAX_UNCOMPRESSED_BYTES),
        }
        print(name, out["runs"][name], flush=True)
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
