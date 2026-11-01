# -*- coding: utf-8 -*-
"""ca31(第 3 期 3-1)つなぎの台帳 ``BR-W17-IO-SLEEP`` の量を数える道具(検収 低 5)。

数え方(エンジンの読み口そのもの=W17 v2 の月曜の行・K9 で全部の日がこの行):
- 来街者=W16 の種別 1・6・7(来街・常連の来街・外国人の来街)。
- 来訪(在圏の行)のある体=``engine.presence.PlanBlocks.from_weekly``(読み口 ``derive_rule``=既定 v2・域外居住は
  W16 の ``home_cell < 0``・出勤率の除外なし)で在圏ブロックが 1 本以上の体。参考に読み口 v1(域外居住の自宅側の行を
  在圏に読む)の数も出す(ca31 の最初の数え 95,976 は v1 相当の行の数えだった)。検収の数え 95,974 は、v2 で「いちばん
  長いブロックが 5 分以上」の体の数と一致する(差の 1 体=月曜のブロックが 23:40〜23:44 の交流 4 分だけの常連の来街者)。
  台帳の量はエンジンの読み口そのもの(v2・長さを問わない)を使う。
- 就寝の行=月曜の活動「就寝」の行の数・その体の数・うち舞台に住む体(``home_cell ≥ 0``)・宿泊施設の行を持つ体。

読むもの: ``data/world/v2/w16_population.parquet``・``data/world/v2/w17_schedule.parquet``(本体の世界資産=読むだけ)。
使い方(リポの根で・作業木の src): ``python docs/bench/analysis/wallbounce-1012/ca31/tools/count_w17_bridges_ca31.py --out <json>``
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
sys.path.insert(0, str(REPO / "src"))

from shibuya.agents.weekly import ACTIVITY_WORDS, load_weekly_file  # noqa: E402
from shibuya.build.pop import w16_population as W16  # noqa: E402
from shibuya.engine import presence as P  # noqa: E402

VISITOR_KINDS = (W16.KIND_VISITOR, W16.KIND_REGULAR_VISITOR, W16.KIND_FOREIGN_VISITOR)
MONDAY = 0
#: 参考の数え(検収の数えとの突き合わせ)の短いブロックの境(分)。台帳の量には使わない。
SHORT_MIN = 5


def count(world: Path) -> dict:
    import pyarrow.parquet as pq

    pop = pq.read_table(world / "w16_population.parquet", columns=["agent_id", "kind", "home_cell"]).to_pydict()
    aid = np.asarray(pop["agent_id"], dtype=np.int64)
    kind = np.asarray(pop["kind"], dtype=np.int64)
    home_out = np.asarray(pop["home_cell"], dtype=np.int64) < 0
    weekly = load_weekly_file(world / "w17_schedule.parquet").restrict_to(aid)
    visitor = np.isin(kind, VISITOR_KINDS)
    out: dict = {"agents": int(aid.size), "visitors": int(visitor.sum()), "day": MONDAY}
    for rule in P.DERIVE_RULES:
        b = P.PlanBlocks.from_weekly(weekly, MONDAY, home_out, derive_rule=rule)
        has = b.blocks_per_agent() > 0
        out[f"visitors_with_blocks_{rule}"] = int((has & visitor).sum())
        if rule == P.DERIVE_RULE_DEFAULT:
            longest = np.zeros(b.n_agents, dtype=np.int64)
            np.maximum.at(longest, b.agent_of_block, (b.end - b.start).astype(np.int64))
            short = has & visitor & (longest < SHORT_MIN)
            out[f"visitors_with_blocks_{rule}_longest_ge_{SHORT_MIN}min"] = int((has & visitor & ~short).sum())
            out["short_only_visitors"] = [
                {"agent_id": int(aid[i]), "kind": int(kind[i]), "longest_block_min": int(longest[i])}
                for i in np.flatnonzero(short)]
    out["derive_rule_default"] = P.DERIVE_RULE_DEFAULT
    # 就寝の行(月曜)=週次表の CSR(体行 × 曜日)から行の体と曜日を開く
    k = np.repeat(np.arange(weekly.n_agents * 7, dtype=np.int64), np.diff(np.asarray(weekly.day_offset, dtype=np.int64)))
    row_agent, day = k // 7, k % 7
    act = np.asarray(weekly.activity, dtype=np.int64)
    pk = np.asarray(weekly.place_kind, dtype=np.int64)
    sleep = (day == MONDAY) & (act == ACTIVITY_WORDS.index("就寝"))
    sa = np.unique(row_agent[sleep])
    lodg = np.unique(row_agent[sleep & (pk == P.PLACE_KIND_LODGING)])
    out.update({
        "sleep_rows": int(sleep.sum()), "sleep_agents": int(sa.size),
        "sleep_agents_home_in": int((~home_out[sa]).sum()), "sleep_agents_lodging": int(lodg.size),
    })
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    res = count(Path(args.world))
    res["world"] = Path(args.world).as_posix()
    Path(args.out).write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(res, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
