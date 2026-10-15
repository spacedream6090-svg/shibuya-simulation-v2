"""W21 の計器(答申 R-116 §3-4=段 8 の先取り・**合否は付けない**)。出力 ``w21_checks.json``。

- **分布の食い違い**: 町丁目 × 表ごとの SRMSE・JSD(``fitting``)・誤差の絶対値の和。**構築に使った表なので点検だけ**
  (検証の証拠にしない=設計書 PS6 の注)。属性の表は町丁目 × 男女の組ごとの割合で比べる。
- **二重**: 区内で働く住民(自宅・区内)の数(=従業地の就業者 375,270 と経済センサスの席の両方に入る人)・派遣社員の住民・
  運輸業の住民(乗務員と鉄道業の従業者の重なりの手がかり)。
- **全員が別人か**: 人の id の重なり 0・(世帯, 世帯員の番号)の重なり 0・世帯主はちょうど 1 人・配偶者は 1 人まで・
  複製(``synthetic``)0 体・属性の組の完全一致の割合(診断)。
- **家族の整合**: 子が親より年上の人 0・親との差が 15 歳未満の子の数・15 歳未満の世帯主 0・夫婦の年齢差の分布。
- **不詳の割り振り**の数(表ごと)・**空欄**の数(列ごと)。

〔段 4〜7〕``w21_checks_b.json`` の計器(合否なし): 席と人数の差・役割の分布(経済センサス 第6-2表と点検)・権利台帳と関係の
行の数・資産の分布(東京都の階級の度数と点検)・なじみの場所の数と順位の法則の再現(構築に使った法則=診断だけ)・外の人の層。

逐次ループ宣言(P4): 表の数ぶん(≤ 16)・町丁目の数ぶん(42)・業種の数ぶん(15)・世帯の種類(2)。体の数に比例するループは無い。
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping

import numpy as np

from . import fitting as F

__all__ = ["table_fit", "uniqueness", "family", "blanks", "overlap", "share_target", "role_distribution", "counts_by",
           "degree_summary", "savings_class_fit", "loglog_slope", "ECEN_MAJOR_OF_KEY", "ECEN_STATUS5", "CENSUS_TO_ECEN5"]


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


# ================================================================================ 段 4〜7(W21 の続き・``w21_checks_b.json``)
#: W16 の 15 語 → 経済センサス 第6-2表の産業(大分類の符号・N は生活関連と娯楽をまとめた N のまま)。
ECEN_MAJOR_OF_KEY = MappingProxyType({"IT": "G", "WR": "I", "FB": "M", "PS": "L", "LS": "N", "AM": "N", "RE": "K",
                                      "SV": "R", "MW": "P", "ED": "O", "FI": "J", "CN": "D", "MF": "E", "TR": "H",
                                      "CS": "Q"})
#: 第6-2表の従業上の地位(5 区分にまとめる)と、国勢調査の地位の写し(派遣は経済センサスでは派遣元=有期にまとめる=自前)。
ECEN_STATUS5 = ("個人業主", "無給の家族従業者", "有給役員", "無期雇用者", "有期・臨時雇用者")
CENSUS_TO_ECEN5 = MappingProxyType({"regular": 3, "dispatched": 4, "part_time": 4, "executive": 2, "employer": 0,
                                    "self_employed": 0, "home_worker": 0, "family_worker": 1})


def role_distribution(person_industry_key: np.ndarray, person_status: np.ndarray, seated: np.ndarray,
                      ecen_rows: list, ecen_items: tuple) -> dict[str, Any]:
    """席に座った人の地位(5 区分)の分布と、経済センサス 第6-2表(渋谷区・産業大分類)の分布(点検だけ・合否なし)。"""
    ik = np.asarray(person_industry_key).astype(str)
    st = np.asarray(person_status).astype(str)
    sel = np.asarray(seated, dtype=bool)
    col = {lab: ecen_items.index(f"{lab}|従業者数_男女計") for lab in
           ("1_個人業主", "2_無給の家族従業者", "3_有給役員", "41_無期雇用者", "42_有期雇用者", "5_臨時雇用者")}
    major_rows = {str(r[3]): r[-1] for r in ecen_rows if str(r[2]) == "2"}
    out: dict[str, Any] = {}
    for key, major in sorted(ECEN_MAJOR_OF_KEY.items()):  # 逐次: 業種の数ぶん(15)
        v = major_rows.get(major)
        if v is None:
            continue
        tgt = np.array([v[col["1_個人業主"]] or 0, v[col["2_無給の家族従業者"]] or 0, v[col["3_有給役員"]] or 0,
                        v[col["41_無期雇用者"]] or 0, (v[col["42_有期雇用者"]] or 0) + (v[col["5_臨時雇用者"]] or 0)],
                       dtype=np.float64)
        m = sel & (ik == key)
        sim = np.zeros(5)
        for s, c in CENSUS_TO_ECEN5.items():  # 逐次: 地位 8
            sim[c] += float((m & (st == s)).sum())
        ok = sim.sum() > 0 and tgt.sum() > 0
        out[key] = {"seated": int(m.sum()), "sim_share": np.round(sim / max(sim.sum(), 1), 4).tolist(),
                    "ecen_share": np.round(tgt / max(tgt.sum(), 1), 4).tolist(),
                    "srmse": round(F.srmse(sim, tgt), 6) if ok else None,
                    "jsd": round(F.jsd(sim, tgt), 6) if ok else None, "ecen_major": major}
    return {"status5": list(ECEN_STATUS5), "by_industry": out,
            "note": "国勢調査の地位(人)と経済センサスの地位(席)は区分が対応しない(無期≠正規・派遣は派遣元)=点検だけ"}


def counts_by(values: np.ndarray) -> dict[str, int]:
    u, c = np.unique(np.asarray(values).astype(str), return_counts=True)
    return {str(a): int(b) for a, b in zip(u, c)}


def degree_summary(u: np.ndarray, n: int) -> dict[str, Any]:
    deg = np.bincount(np.asarray(u, dtype=np.int64), minlength=n)
    has = deg[deg > 0]
    return {"people_with_edges": int(has.size), "mean": round(float(has.mean()), 3) if has.size else None,
            "quantiles_50_90_99": [int(x) for x in np.percentile(has, [50, 90, 99])] if has.size else None,
            "max": int(has.max()) if has.size else None}


def savings_class_fit(sim_class: np.ndarray, sim_type: np.ndarray, freq: np.ndarray, rate_cls: np.ndarray,
                      zero: np.ndarray) -> dict[str, Any]:
    """世帯の貯蓄の階級の分布(0 円は 25 万円未満の階級へ)と東京都の世帯数分布(第31-0表)の点検(合否なし)。"""
    out = {}
    for t, name in ((1, "multi"), (2, "single")):  # 逐次: 種類 2
        m = sim_type == t
        sim = np.bincount(sim_class[m], minlength=freq.shape[1]).astype(np.float64)
        tgt = freq[t]
        out[name] = {"households": int(m.sum()), "srmse": round(F.srmse(sim, tgt), 6), "jsd": round(F.jsd(sim, tgt), 6),
                     "zero_share": round(float(zero[m].mean()), 4) if m.any() else None,
                     "table_zero_share_tokyo": round(float((freq[t] * (100.0 - rate_cls[t]) / 100.0).sum()
                                                           / max(freq[t].sum(), 1)), 4)}
    return out


def loglog_slope(x: np.ndarray, y: np.ndarray) -> float | None:
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    ok = (x > 0) & (y > 0)
    if ok.sum() < 2:
        return None
    return round(float(np.polyfit(np.log(x[ok]), np.log(y[ok]), 1)[0]), 4)
