# -*- coding: utf-8 -*-
"""ca31(第 3 期 3-1 暦 1a 影)の記録の道具: W20 の週の表(全員)の統計と、構築側の錨との差(合否にしない)。

読むもの(構築側だけ): 組んだ資産 ``data/world/v2_stage_3-1`` の ``w20_calendar_1a.parquet``・材料の表
``w20_calendar_1a_materials.json``(第74-9・74-6・19・6-2 表から抜いた値)・第 31/36 表の錨
``docs/bench/anchors/commute_time_dist_r3.json``。検証側(第 14・15・68-3・30 表・PT・人流)は読まない。

出すもの(``--out`` の JSON):
- 曜日ごとの勤務の約束の率(勤務の約束を持つ体のうち)と、材料の曜日の率(第74-6表の雇用されている人・第74-9表の総数)。
- 出勤・帰宅の 15 分の分布と、同じ雇用形態の構成で混ぜた第 31/36 表の分布の JSD(入力の写し=差は抽選と切り詰めだけ)。
- 週の日数の分布と平均(予定=第74-6表の率の和)と、第19表の平均の日数 ÷ (365/7) の加重平均(年間の整合の計器=診断)。
- 通勤時間・空欄の数・場所の種類・地位の出どころ。
- 〔第337〕勤務の行を持ちうる体(``emp_row ≥ 0``=週の勤務日が 0 の体を含む)の週の日数・35 条の対象(無期・有期・臨時)と
  対象の外の別の週の日数(週 1 日の休みの確かめ=対象に 7 日の体が居ない)・第 31/36 表の行ごとの曜日の率(実現)と第74-6表の
  率(予定)とその差。

使い方(リポの根で・作業木の src): ``python docs/bench/analysis/wallbounce-1012/ca31/tools/stats_ca31.py --out <JSON>``
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

SLOTS = 96


def _hist(v: np.ndarray) -> np.ndarray:
    v = v[v >= 0]
    return np.bincount((v % 1440) // 15, minlength=SLOTS)[:SLOTS].astype(np.float64)


def _jsd(p: np.ndarray, q: np.ndarray) -> float:
    p = p / p.sum()
    q = q / q.sum()
    m = 0.5 * (p + q)

    def kl(a: np.ndarray, b: np.ndarray) -> float:
        k = a > 0
        return float(np.sum(a[k] * np.log2(a[k] / b[k])))

    return round(0.5 * kl(p, m) + 0.5 * kl(q, m), 5)


def _anchor_hist(table: dict, row: str) -> np.ndarray:
    """錨の行の構成比を 15 分の枠に配る(開端の 60 分のビンは 4 つの枠に等分=ビン内一様)。"""
    out = np.zeros(SLOTS)
    share = np.asarray(table["rows"][row]["share"], dtype=np.float64)
    share = share / share.sum()
    for b, s in zip(table["bins"], share):
        k = int(b["width_min"]) // 15
        for j in range(k):
            out[((int(b["start_min"]) + 15 * j) % 1440) // 15] += s / k
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    from shibuya.engine.calendar_shadow import STAGE_DIR

    ap.add_argument("--stage", default=STAGE_DIR)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    import pyarrow.parquet as pq

    stage = REPO / args.stage
    t = pq.read_table(stage / W.OUTPUT_NAME).to_pydict()
    t = {k: np.asarray(v) for k, v in t.items()}
    mat = W.load_materials(stage / W.MATERIALS_NAME)
    anchor = TR.load_anchor()
    wd, cm = t["weekday"], t["commit"]
    workers = np.unique(t["agent_id"][(cm == W.COMMIT_WORK)])
    emp_row_day0 = t["emp_row"][wd == 0]
    agents_day0 = t["agent_id"][wd == 0]
    is_worker = np.isin(agents_day0, workers)
    out: dict = {"stage_file_sha16": __import__("hashlib").sha256((stage / W.OUTPUT_NAME).read_bytes()).hexdigest()[:16]}
    # ---- 曜日の率 ----
    n_w = int(workers.size)
    rate = [round(float(((cm == W.COMMIT_WORK) & (wd == d)).sum()) / n_w, 4) for d in range(7)]
    out["work_rate_by_weekday_among_workers"] = rate
    out["material_rates"] = {
        "74-6 雇用されている人(平日/土/日)": [round(x, 3) for x in mat.rate74(mat.t746, "1_うち雇用されている人|0_総数")],
        "74-9 総数(平日/土/日)": [round(x, 3) for x in mat.rate74(mat.t749, "総数")],
    }
    # ---- 週の日数 ----
    per = np.bincount(np.searchsorted(workers, t["agent_id"][cm == W.COMMIT_WORK]), minlength=n_w)
    out["days_per_week_hist"] = np.bincount(per, minlength=8).astype(int).tolist()
    out["days_per_week_mean"] = round(float(per.mean()), 4)
    rows_w = emp_row_day0[is_worker]
    md = [mat.mean_days(W.EMP_ROWS[int(r)], "total") / (365 / 7) for r in rows_w]
    out["t19_days_per_week_weighted_gauge"] = round(float(np.mean(md)), 4)  # 第19表=年間の整合の計器(診断)
    # ---- 〔第337〕勤務の行を持ちうる体(週の勤務日 0 を含む)・雇われる側と自営の別・行ごとの曜日の率 ----
    n_all0 = int(agents_day0.size)
    days_all = np.bincount(np.searchsorted(agents_day0, t["agent_id"][cm == W.COMMIT_WORK]), minlength=n_all0)
    cap = emp_row_day0 >= 0
    out["capable_bodies"] = int(cap.sum())
    out["capable_zero_day_bodies"] = int((cap & (days_all == 0)).sum())
    out["capable_days_per_week_hist"] = np.bincount(days_all[cap], minlength=8).astype(int).tolist()
    out["capable_days_per_week_mean"] = round(float(days_all[cap].mean()), 4)
    st0 = t["status"][wd == 0]
    emp_side = cap & np.isin(st0, list(W.REST_STATUSES))
    self_side = cap & ~np.isin(st0, list(W.REST_STATUSES))
    out["days_per_week_hist_by_side"] = {
        "35 条の対象(無期・有期・臨時)": np.bincount(days_all[emp_side], minlength=8).astype(int).tolist(),
        "対象の外(個人業主・無給の家族・有給役員)": np.bincount(days_all[self_side], minlength=8).astype(int).tolist()}
    by_row = {}
    for r_i, rname in enumerate(W.EMP_ROWS):
        m = cap & (emp_row_day0 == r_i)
        if not m.any():
            continue
        ids = agents_day0[m]
        on = (cm == W.COMMIT_WORK) & np.isin(t["agent_id"], ids)
        real = [float((on & (wd == d)).sum()) / int(m.sum()) for d in range(7)]
        plan = [float(x) for x in np.clip(W._day_weights(mat, "", rname), 0.0, 1.0)]
        rz = [float(np.mean(real[:5])), real[5], real[6]]
        # 平日は 5 曜日それぞれの差の最小(どの平日も下回らないか)も出す
        by_row[rname] = {"bodies": int(m.sum()),
                         "realized_weekday_sat_sun": [round(x, 4) for x in rz],
                         "plan_74_6_weekday_sat_sun": [round(x, 4) for x in plan],
                         "diff_weekday_sat_sun": [round(a - b, 4) for a, b in zip(rz, plan)],
                         "min_weekday_diff": round(min(real[:5]) - plan[0], 4)}
    out["rate_by_emp_row"] = by_row  # duty_role の体(第74-9表の比)を含む=予定の率と少しずれる
    # ---- 出勤・帰宅の分布と第 31/36 表(同じ雇用形態の構成で混ぜた)----
    weekday_work = (cm == W.COMMIT_WORK) & (wd < 5)
    mix = np.bincount(t["emp_row"][weekday_work].astype(np.int64), minlength=len(W.EMP_ROWS)).astype(np.float64)
    dep_a = sum(mix[i] * _anchor_hist(anchor["depart"], W.EMP_ROWS[i]) for i in range(len(W.EMP_ROWS)) if mix[i] > 0)
    ret_a = sum(mix[i] * _anchor_hist(anchor["return"], W.EMP_ROWS[i]) for i in range(len(W.EMP_ROWS)) if mix[i] > 0)
    dep_w = _hist(t["depart_min"][weekday_work].astype(np.int64))
    ret_w = _hist(t["return_min"][weekday_work].astype(np.int64))
    st_w = _hist(t["start_min"][weekday_work].astype(np.int64))
    en_w = _hist(t["end_min"][weekday_work].astype(np.int64))
    out["jsd_vs_anchor_31_36"] = {"depart": _jsd(dep_w, dep_a), "return": _jsd(ret_w, ret_a)}
    out["hist15_weekday_work"] = {"depart": dep_w.astype(int).tolist(), "start": st_w.astype(int).tolist(),
                                  "end": en_w.astype(int).tolist(), "return": ret_w.astype(int).tolist(),
                                  "anchor_depart_mix": [round(x / dep_a.sum(), 6) for x in dep_a],
                                  "anchor_return_mix": [round(x / ret_a.sum(), 6) for x in ret_a]}
    lead = t["lead_min"][weekday_work].astype(np.int64)
    out["commute_min_weekday"] = {"n": int(lead.size), "mean": round(float(lead.mean()), 2),
                                  "p10_p50_p90": [float(x) for x in np.quantile(lead, [0.1, 0.5, 0.9])]}
    # 15 分ごとの約束の行動者率(平日の月曜・全員が分母)
    m0 = (wd == 0) & (cm == W.COMMIT_WORK)
    s0 = np.clip(t["start_min"][m0].astype(np.int64), 0, 1440)
    e0 = np.clip(t["end_min"][m0].astype(np.int64), 0, 1440)
    heads = np.arange(SLOTS) * 15
    act = [(int(((s0 <= h) & (e0 > h)).sum())) for h in heads]
    n_all = int((wd == 0).sum())
    out["actor_rate15_monday"] = [round(a / n_all, 5) for a in act]
    # ---- 空欄・場所・地位の出どころ ----
    out["blanks_monday"] = {"no_commitment": int(((wd == 0) & (cm == 0)).sum()),
                            "school_time": int(((wd == 0) & (cm == W.COMMIT_SCHOOL) & (t["start_min"] < 0)).sum())}
    pk = t["place_kind"][(wd == 0) & (cm > 0)]
    out["place_kind_monday"] = {W.PLACE_WORDS[k]: int((pk == k).sum()) for k in range(len(W.PLACE_WORDS)) if (pk == k).any()}
    ss = t["status_source"][wd == 0]
    out["status_source"] = {W.STATUS_SOURCE_WORDS[k]: int((ss == k).sum()) for k in range(len(W.STATUS_SOURCE_WORDS))}
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in out.items() if k not in ("hist15_weekday_work", "actor_rate15_monday")},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
