"""5 段目 5c(活動 → 知覚の乗数・D-117 M1〜M4)の計測。

使い方(リポジトリの根から)::

    python docs/bench/analysis/energy-classical-2026-09-28/p_see_activity_measure.py \\
        --world data/world/v2 --out docs/bench/analysis/energy-classical-2026-09-28/p_see_activity_arms.json

腕(mock 5,000 体・seed 1・語彙 v3・空腹 energy=CLI の既定・``--familiarity on``=露出カウンタを使う)は
:data:`ARMS`= p_see {1.0, 0.30} × 乗数表 {既定(全部 1.0)・通話 0.49・連れ 1.39・目的地つき移動 0.5・3 つ全部}
+ 広告ゼロ(⑥ の対照)+ 古典だけ腕(``--policy classical --chooser classical``)× p_see 0.30 × {既定・3 つ全部}。
各腕で 看板のあるセルの描画・抽選・載った件数を活動の種別で層別(manifest ``p_see_activity``)・親しみの表の
露出(描画/入った回・入った回の活動の種別)・入力トークン(セル群・プロンプト)・購入/食事/行為の分布
(=AD 腕の指標。mock も classical もプロンプトの看板を読まないので動かないはず)を控える。

絶対パスは書かない。壁時計は標準出力だけ(決定論でない)。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

ENGINE_CONTINUE = "(エンジン継続)"
PHONE = {"phone": 0.49}
COMPANION = {"companion_talk": 1.39}
MOVE = {"move_to": 0.5}
ALL3 = {**PHONE, **COMPANION, **MOVE}
BASE = {"vocab_version": "v3", "familiarity": "on"}
ARMS: dict[str, dict[str, Any]] = {}
for _p, _tag in ((1.0, "p100"), (0.30, "p030")):
    for _name, _tab in (("identity", None), ("phone_0_49", PHONE), ("companion_1_39", COMPANION),
                        ("move_to_0_5", MOVE), ("all3", ALL3)):
        ARMS[f"{_tag}_{_name}"] = {"signage_p_see": _p, **({"p_see_activity": _tab} if _tab else {})}
ARMS["ad_zero"] = {"signage": False}
ARMS["classical_p030_identity"] = {"signage_p_see": 0.30, "policy": "classical", "chooser": "classical"}
ARMS["classical_p030_all3"] = {"signage_p_see": 0.30, "policy": "classical", "chooser": "classical",
                               "p_see_activity": ALL3}


def summarize(name: str, kw: dict[str, Any], res: Any) -> dict[str, Any]:
    m = res.run_manifest_fields()
    rc = dict(res.renderer_counters)
    fam = dict(res.familiarity_summary or {})
    au = {k: v for k, v in res.action_usage.items() if k != ENGINE_CONTINUE}
    return {
        "arm": name, "args": kw, "final_hash": res.final_hash, "llm_calls": int(res.llm_calls),
        "p_see_activity": m.get("p_see_activity", {}),
        "renderer": {k: rc[k] for k in sorted(rc) if k.startswith(("signage", "prompt_tokens",
                                                                    "tokens_"))},
        "exposures": {k: v for k, v in fam.items() if str(k).startswith("exposures")},
        "purchases": int(res.column("purchases").sum()), "meals_in_area": int(res.meals),
        "action_usage_llm": au,
    }


def main(argv: list[str] | None = None) -> int:
    from shibuya import cli

    ap = argparse.ArgumentParser(description="5 段目 5c の計測")
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--agents", type=int, default=5_000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    rows = []
    for name, extra in ARMS.items():
        kw = {**BASE, **extra}
        t0 = time.perf_counter()
        res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, **kw)
        row = summarize(name, kw, res)
        rows.append(row)
        print(f"{name}: final {row['final_hash'][:16]} calls {row['llm_calls']:,} "
              f"({time.perf_counter() - t0:.1f}s)", flush=True)
    doc = {"schema": "shibuya.bench/p-see-activity-2026-09-28/1", "n_agents": args.agents,
           "seed": args.seed, "arms": rows}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n",
                              encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
