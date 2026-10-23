"""第 2 期 2-4 V3: 在席の印 ``poi_ref`` の数え方の前後(prox22 の ``tools/probe_poi_ref.py`` と同じ数え方+世界の置き場と腕)。

在席の体 × 刻みのうち、店のセルの外に居る数・歩いている(MOVING)数・同じ単位の組 × 刻みのうちその体を含む組の数を数える
(``CrowdProcess.step`` を包むだけ=final は包まないランと同じ)。5,000 体・seed 1・1 日・語彙 v3・記憶 on(prox22 と同じ構成)。

    python docs/bench/analysis/wallbounce-1012/vb24/tools/seat_probe_vb24.py --world data/world/v2_stage_2-4 \
        --proximity distance --seat-release walk      # 1 行の JSON
    # 切替口: --seat-release legacy(歩き出しでは解かない=V3 の前)

腕は組み立ての前に置く(``engine.proximity.set_arm``・``engine.seat_release.set_arm``)。``--seat-release`` は V3 の後の
src でだけ渡せる(前の src には口が無い=省く)。
"""

from __future__ import annotations

import argparse
import json
import sys

import numpy as np


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--proximity", default="")
    ap.add_argument("--seat-release", default="")
    ap.add_argument("--agents", type=int, default=5_000)
    a = ap.parse_args(argv)
    from shibuya import cli
    from shibuya.agents.state import Activity
    from shibuya.engine import proximity as P
    from shibuya.engine.processes import crowd as C

    if a.proximity:
        P.set_arm(a.proximity)
    if a.seat_release:
        from shibuya.engine import seat_release as SR

        SR.set_arm(a.seat_release)
    st = {"steps": 0, "seated": 0, "seated_moving": 0, "seated_other_cell": 0, "seated_not_shopping": 0,
          "max_seated_other_cell": 0, "pairs_same_unit": 0, "pairs_same_unit_other_cell": 0, "max_unit_size": 0,
          # 店のセルの外に居る在席の体の内訳(歩き出しの道=乗車へ向かう・就寝へ帰る・そのほか)
          "other_cell_boarding": 0, "other_cell_sleep_walk": 0, "other_cell_moving_other": 0, "other_cell_not_moving": 0}
    orig = C.CrowdProcess.step

    def step(self, t):  # noqa: ANN001
        r = self.agents.registry
        pr = np.asarray(r.poi_ref).astype(np.int64)
        s = pr >= 0
        if s.any():
            pc = np.asarray(self.world.pois.cell, dtype=np.int64)
            cell = np.asarray(r.cell).astype(np.int64)
            act = np.asarray(r.activity)
            oc = s & (cell != pc[np.clip(pr, 0, None)])
            st["steps"] += 1
            st["seated"] += int(s.sum())
            st["seated_moving"] += int((s & (act == int(Activity.MOVING))).sum())
            st["seated_other_cell"] += int(oc.sum())
            st["seated_not_shopping"] += int((s & (act != int(Activity.SHOPPING))).sum())
            st["max_seated_other_cell"] = max(st["max_seated_other_cell"], int(oc.sum()))
            mv = act == int(Activity.MOVING)
            board = np.asarray(r.board_line) >= 0
            sleepw = np.asarray(r.sleep_pending) == 1
            st["other_cell_boarding"] += int((oc & board).sum())
            st["other_cell_sleep_walk"] += int((oc & ~board & sleepw).sum())
            st["other_cell_moving_other"] += int((oc & mv & ~board & ~sleepw).sum())
            st["other_cell_not_moving"] += int((oc & ~mv & ~board & ~sleepw).sum())
            _u, cnt = np.unique(pr[s], return_counts=True)
            st["pairs_same_unit"] += int((cnt * (cnt - 1) // 2).sum())
            st["max_unit_size"] = max(st["max_unit_size"], int(cnt.max()))
            ok = s & ~oc
            _u2, cnt2 = np.unique(pr[ok], return_counts=True)
            st["pairs_same_unit_other_cell"] += int((cnt * (cnt - 1) // 2).sum() - (cnt2 * (cnt2 - 1) // 2).sum())
        return orig(self, t)

    C.CrowdProcess.step = step
    res = cli.run(n_agents=a.agents, seed=1, world_dir=a.world, vocab_version="v3", memory="on")
    st["final"] = res.final_hash[:16]
    st["calls"] = int(res.llm_calls)
    st["proximity"] = P.arm()
    try:
        from shibuya.engine import seat_release as SR

        st["seat_release"] = SR.arm()
        st["released_on_walk"] = int(res.run_manifest_fields()["leave_effects"].get("released_on_walk") or 0)
    except ImportError:
        st["seat_release"] = "(口なし)"
    st["share_other_cell"] = round(st["seated_other_cell"] / max(1, st["seated"]), 4)
    st["share_moving"] = round(st["seated_moving"] / max(1, st["seated"]), 4)
    st["share_pairs_other_cell"] = round(st["pairs_same_unit_other_cell"] / max(1, st["pairs_same_unit"]), 4)
    sys.stdout.reconfigure(newline="\n")  # 改行は LF
    print(json.dumps(st, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
