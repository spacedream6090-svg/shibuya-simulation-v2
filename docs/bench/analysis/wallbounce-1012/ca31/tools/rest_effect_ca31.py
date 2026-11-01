# -*- coding: utf-8 -*-
"""ca31(第 3 期 3-1)週 1 日の休み(労働基準法 35 条 1 項)が曜日の率をどれだけ下げるかを、行ごとに分けて数える道具。

同じ属性・地位・材料で、規則の表の行のまま(``rest``)と、週の休みの数を 0 にした写し(``no_rest``)の 2 本を作り、第 31/36 表の
行ごとの曜日の率(平日の平均/土/日)と、その差(休みの効果=抽選の揺れを除いた量)を出す。期待の効果は
−P7 × q_d(P7=7 日とも勤務を引く確率=Π p・q_d=その曜日の働かない率の比=休みの曜日の選び方)。予定の率は第74-6表の行。
読むもの(構築側だけ): 組んだ資産の置き場の W16 とペルソナ・材料の表・第 31/36 表の錨・規則の表。

使い方(リポの根で・作業木の src): ``python docs/bench/analysis/wallbounce-1012/ca31/tools/rest_effect_ca31.py --out <JSON>``
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

from shibuya.build.sched import trial as TR  # noqa: E402
from shibuya.build.sched import w20_calendar_1a as W  # noqa: E402
from shibuya.engine.calendar_shadow import STAGE_DIR  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default=STAGE_DIR)
    ap.add_argument("--data", default="data")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    st = REPO / args.stage
    a = W.attributes_from_world(st, REPO / args.data)
    mat = W.load_materials(st / W.MATERIALS_NAME)
    anchor = TR.load_anchor()
    emp = W.draw_employment_status(a, mat, anchor)
    rule = W.load_weekly_rest_rule()
    runs = {"rest": W.calendar_from_attributes(a, emp, mat, anchor, rest_rule=rule),
            "no_rest": W.calendar_from_attributes(
                a, emp, mat, anchor, rest_rule={**rule, "params": {**rule["params"], "min_rest_days_per_week": 0}})}
    n = a.n
    er = np.asarray(emp.emp_row)
    target = np.isin(np.asarray(emp.status), list(W.rest_statuses_of(rule)))
    out: dict = {"rule": rule["id"], "applies_to_status": rule["params"].get("applies_to_status"),
                 "weekly_rest_inserted": runs["rest"]["counters"]["weekly_rest_inserted"], "rows": {}}
    for r_i, rname in enumerate(W.EMP_ROWS):  # 逐次: 行の数(10)
        m = er == r_i
        if not m.any():
            continue
        p = np.clip(W._day_weights(mat, "", rname), 0.0, 1.0)
        res: dict = {"bodies": int(m.sum()), "rest_target_share": round(float(target[m].mean()), 4),
                     "plan_74_6": [round(float(x), 4) for x in p]}
        for lab, o in runs.items():
            r = (o["columns"]["commit"].reshape(n, 7) == W.COMMIT_WORK)[m].mean(axis=0)
            res[lab] = [round(float(r[:5].mean()), 4), round(float(r[5]), 4), round(float(r[6]), 4)]
        res["rest_effect"] = [round(x - y, 4) for x, y in zip(res["rest"], res["no_rest"])]
        res["rest_minus_plan"] = [round(x - y, 4) for x, y in zip(res["rest"], res["plan_74_6"])]
        p7 = np.array([p[0]] * 5 + [p[1], p[2]])
        w = 1.0 - p7
        q = w / w.sum() if w.sum() > 0 else w
        P7 = float(np.prod(p7)) * res["rest_target_share"]
        res["expected_effect"] = [round(-P7 * float(q[:5].mean()), 4), round(-P7 * float(q[5]), 4),
                                  round(-P7 * float(q[6]), 4)]
        out["rows"][rname] = res
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
