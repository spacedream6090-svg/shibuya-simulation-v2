"""W21 の計器(答申 R-116 §3-4=段 8 の先取り・**合否は付けない**)。出力 ``w21_checks.json``。

- **分布の食い違い**: 町丁目 × 表ごとの SRMSE・JSD(``fitting``)・誤差の絶対値の和。**構築に使った表なので点検だけ**
  (検証の証拠にしない=設計書 PS6 の注)。属性の表は町丁目 × 男女の組ごとの割合で比べる。
- **二重**: 区内で働く住民(自宅・区内)の数(=従業地の就業者 375,270 と経済センサスの席の両方に入る人)・派遣社員の住民・
  運輸業の住民(乗務員と鉄道業の従業者の重なりの手がかり)。
- **全員が別人か**: 人の id の重なり 0・(世帯, 世帯員の番号)の重なり 0・世帯主はちょうど 1 人・配偶者は 1 人まで・
  複製(``synthetic``)0 体・属性の組の完全一致の割合(診断)。
- **家族の整合**: 子が親より年上の人 0・親との差が 15 歳未満の子の数・15 歳未満の世帯主 0・夫婦の年齢差の分布。
- **不詳の割り振り**の数(表ごと)・**空欄**の数(列ごと)。

逐次ループ宣言(P4): 表の数ぶん(≤ 16)と町丁目の数ぶん(42)。体の数に比例するループは無い。
"""

from __future__ import annotations

from typing import Any, Mapping

import numpy as np

from . import fitting as F

__all__ = ["table_fit", "uniqueness", "family", "blanks", "overlap"]


def _fit_rows(sim: np.ndarray, tgt: np.ndarray) -> dict[str, Any]:
    """行(単位)ごとの SRMSE・JSD と、全体の和の SRMSE・JSD・誤差の絶対値の和。"""
    sim = np.asarray(sim, dtype=np.float64)
    tgt = np.asarray(tgt, dtype=np.float64)
    sr, js = [], []
    for i in range(sim.shape[0]):  # 逐次: 単位(町丁目 or 町丁目 × 男女)の数ぶん
        if sim[i].sum() > 0 and tgt[i].sum() > 0:
            sr.append(F.srmse(sim[i], tgt[i]))
            js.append(F.jsd(sim[i], tgt[i]))
    agg_s, agg_t = sim.sum(axis=0), tgt.sum(axis=0)
    ok = agg_s.sum() > 0 and agg_t.sum() > 0
    return {
        "units": len(sr),
        "srmse_mean": round(float(np.mean(sr)), 6) if sr else None,
        "srmse_max": round(float(np.max(sr)), 6) if sr else None,
        "jsd_mean": round(float(np.mean(js)), 6) if js else None,
        "jsd_max": round(float(np.max(js)), 6) if js else None,
        "abs_error_sum": round(float(np.abs(sim - tgt).sum()), 3),
        "stage_srmse": round(F.srmse(agg_s, agg_t), 6) if ok else None,
        "stage_jsd": round(F.jsd(agg_s, agg_t), 6) if ok else None,
        "sim_total": round(float(sim.sum()), 3),
        "target_total": round(float(tgt.sum()), 3),
    }


def table_fit(counts: Mapping[str, tuple[np.ndarray, np.ndarray]]) -> dict[str, Any]:
    """{表の名: (数え, 目標)} → 表ごとの点検(目標が割合の表は呼び手が数に直して渡す)。"""
    return {name: _fit_rows(s, t) for name, (s, t) in sorted(counts.items())}


def share_target(codes: np.ndarray, group: np.ndarray, eligible: np.ndarray, share: np.ndarray
                 ) -> tuple[np.ndarray, np.ndarray]:
    """属性の番号 → (組 × 区分の数え, 組の大きさ × 割合の目標)。"""
    G, K = share.shape
    e = eligible & (codes >= 0)
    sim = np.zeros((G, K))
    np.add.at(sim, (group[e], codes[e]), 1.0)
    size = np.bincount(group[eligible], minlength=G).astype(np.float64)
    s = share.sum(axis=1, keepdims=True)
    tgt = np.divide(share, s, out=np.zeros_like(share), where=s > 0) * size[:, None]
    return sim, tgt


def uniqueness(persons: Mapping[str, np.ndarray], attr_cols: tuple[str, ...]) -> dict[str, Any]:
    pid = np.asarray(persons["person_id"])
    hh = np.asarray(persons["household_id"])
    no = np.asarray(persons["member_no"])
    rel = np.asarray(persons["relation"]).astype(str)
    pair = hh.astype(np.int64) * 16 + no.astype(np.int64)
    heads = np.bincount(hh[rel == "head"], minlength=int(hh.max()) + 1 if hh.size else 0)
    spouses = np.bincount(hh[rel == "spouse"], minlength=heads.size)
    cols = [np.asarray(persons[c]).astype(str) for c in attr_cols]
    combo = cols[0].astype(object)
    for c in cols[1:]:
        combo = np.char.add(np.char.add(combo.astype(str), "|"), c)
    _, inv, cnt = np.unique(combo, return_inverse=True, return_counts=True)
    shared = cnt[inv] > 1
    return {
        "person_id_duplicates": int(pid.size - np.unique(pid).size),
        "household_member_duplicates": int(pair.size - np.unique(pair).size),
        "households_without_exactly_one_head": int((heads[np.unique(hh[rel != "institution_resident"])] != 1).sum()),
        "households_with_two_or_more_spouses": int((spouses > 1).sum()),
        "synthetic": int(np.asarray(persons["synthetic"]).sum()),
        "attribute_tuple_columns": list(attr_cols),
        "attribute_tuple_shared_share": round(float(shared.mean()), 6) if shared.size else None,
        "attribute_tuple_distinct": int(cnt.size),
    }


def family(persons: Mapping[str, np.ndarray]) -> dict[str, Any]:
    hh = np.asarray(persons["household_id"], dtype=np.int64)
    rel = np.asarray(persons["relation"]).astype(str)
    age = np.asarray(persons["age"], dtype=np.int64)
    sex = np.asarray(persons["sex"], dtype=np.int64)
    H = int(hh.max()) + 1 if hh.size else 0
    head_age = np.full(H, -1)
    head_age[hh[rel == "head"]] = age[rel == "head"]
    head_sex = np.full(H, -1)
    head_sex[hh[rel == "head"]] = sex[rel == "head"]
    sp_age = np.full(H, -1)
    sp_age[hh[rel == "spouse"]] = age[rel == "spouse"]
    ch = rel == "child"
    pa = np.where(sp_age[hh[ch]] >= 0, np.minimum(head_age[hh[ch]], sp_age[hh[ch]]), head_age[hh[ch]])
    gap = pa - age[ch]
    couples = sp_age >= 0
    hus = np.where(head_sex[couples] == 0, head_age[couples], sp_age[couples])
    wif = np.where(head_sex[couples] == 0, sp_age[couples], head_age[couples])
    d = hus - wif
    bins = [-100, -10, -5, -2, 0, 1, 3, 6, 11, 100]
    hist, _ = np.histogram(d, bins=bins)
    par = rel == "parent"
    gc = rel == "grandchild"
    gp = rel == "grandparent"
    cs = rel == "child_spouse"
    return {
        "children_older_than_a_parent": int((gap < 0).sum()),
        "children_parent_gap_under_15": int((gap < 15).sum()),
        "parents_younger_than_head": int((age[par] < head_age[hh[par]]).sum()),
        "parents_gap_under_15": int((age[par] - head_age[hh[par]] < 15).sum()),
        # 〔検収 L2〕孫・祖父母は世帯主と親子の最小の差の 2 倍(30 歳)以上・子の配偶者は世帯主より 15 歳以上若い
        "grandchildren": int(gc.sum()),
        "grandchildren_gap_under_30": int((head_age[hh[gc]] - age[gc] < 30).sum()),
        "grandparents": int(gp.sum()),
        "grandparents_gap_under_30": int((age[gp] - head_age[hh[gp]] < 30).sum()),
        "child_spouses_gap_under_15": int((head_age[hh[cs]] - age[cs] < 15).sum()),
        "heads_under_15": int((age[rel == "head"] < 15).sum()),
        "couples": int(couples.sum()),
        "husband_minus_wife": {
            "mean": round(float(d.mean()), 3) if d.size else None,
            "quantiles_10_50_90": [int(x) for x in np.percentile(d, [10, 50, 90])] if d.size else None,
            "histogram_bins": bins, "histogram": hist.astype(int).tolist(),
        },
    }


def blanks(persons: Mapping[str, np.ndarray], cols: tuple[str, ...]) -> dict[str, int]:
    out = {}
    for c in cols:  # 逐次: 列の数ぶん
        v = np.asarray(persons[c])
        out[c] = int((v.astype(str) == "").sum()) if v.dtype == object or v.dtype.kind in "US" else int((v < 0).sum())
    return out


def overlap(persons: Mapping[str, np.ndarray]) -> dict[str, Any]:
    wk = np.asarray(persons["workplace_kind"]).astype(str)
    st = np.asarray(persons["emp_status"]).astype(str)
    ind = np.asarray(persons["industry_major"]).astype(str)
    return {
        "residents_working_at_home_or_in_ward": int(np.isin(wk, ["home", "in_ward"]).sum()),
        "note_working_in_ward": "この人数は従業地の就業者(第11-1表 375,270=区全体)と経済センサスの席(段 4)の両方に入る=二重に数えない",
        "residents_dispatched": int((st == "dispatched").sum()),
        "note_dispatched": "経済センサスは派遣先でなく派遣元の所属で数える(R-109 の 16,526 人=区全体・引)",
        "residents_in_transport_H": int((ind == "H").sum()),
        "note_transport": "乗務員と鉄道業の従業者の重なりの手がかり(乗務員は段 4・W16 は v1 の在庫 1,258)",
    }
