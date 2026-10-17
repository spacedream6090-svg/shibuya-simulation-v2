"""W21 段 5「お金」(EC2・決定 10-12 §4-11・計画 第 4 期 段 5・回答 2-2 の 1「属性から作る関数」)。版 1.1.0。

正: 答申 R-107(結論 2=資産は**階級の度数をそのまま**・対数正規を当てない/結論 3=支払い方法の割合は**検証**(回答 10-12b §3
(2))=構築は持ち物の保有率だけ/結論 5=JICC の残高)・R-116 §1-4(#46=構築・#47 家計調査の 1 日の消費と現金の保有=**検証側
=使わない**)・回答 10-12b §3 (1)(家計調査 貯蓄・負債編=**検証**)。

- 経済の段 2-1 に「最初の資産を統計から作る」関数は無かった(``economy/anchors.py`` の財布は家計調査の 1 日の消費 × 3 日=
  検証側の表の写し・``entry_capital.py`` は店の参入資本)=二重に作らず、``attr_fns`` に新しく置いた(呼ぶのはここと、
  第 4 期 段 10 の差し替えの後の経済の段)。
- 世帯の資産(貯蓄・通貨性預貯金・負債)は世帯主の属性(世帯の種類・世帯主の年齢)で世帯ごとに引き、**18 歳以上の世帯員に
  均等に配る**(18 歳以上がいなければ世帯主=自前の規則・expedient)。外から来て働く人は自分を世帯主とする「総世帯」の表で
  引いて全部を本人に(世帯員は舞台に居ない=宣言)。施設等の世帯の人は単身の表(施設等は 1 人 1 世帯=段 2 と同じ宣言)。
- 賃金(賃金構造 令和 7 年)は雇われて働く人だけ。役員・業主・家族従業者・職業が分類不能の人は空欄(R-107 §空欄 12)。
- **空欄**: 財布の現金(構築側の公的な錨が無い=R-107 §1-7・案 (a)〜(c) は親の判断)・カードと電子マネーの有無(J-FLEC
  問 14 は検証・家計消費状況調査の保有は世帯の単位で、置き場の名が検証側の語 ``kakei`` に当たる=読まない)・口座の有無
  (J-FLEC 問 1(a)=取得していない)。JICC の異動(延滞)は使わない(R-107 の振り分けの案=検証側)。

逐次ループ宣言(P4): 表の行の数ぶん(CSV の読み)・世帯の種類 3 × 年齢 13 の傾けの解き(二分法 60 回)。体の数に比例する
ループは無い。
"""

from __future__ import annotations

import re
from typing import Any, Final, Mapping

import numpy as np

from . import attr_fns as A
from . import w21_sources as S

__all__ = ["load_wage_tables", "load_asset_tables", "jicc_holder_rate", "solve_tilt", "household_type",
           "build_money", "ADULT_AGE", "WAGE_CLASS_FLOOR_YEN", "WAGE_TOP_FACTOR"]

#: 世帯の資産を配る相手の年齢の下限(自前・expedient)。
ADULT_AGE: Final[int] = 18
#: 第18表の最も低い階級(～99.9 千円)の下の端と、最も高い階級(1,200 千円～)の上の端の倍率(自前・expedient)。
WAGE_CLASS_FLOOR_YEN: Final[float] = 80_000.0
WAGE_TOP_FACTOR: Final[float] = 1.5

_FW = str.maketrans("０１２３４５６７８９", "0123456789")
_SEXES: Final[tuple[str, str]] = ("男", "女")
_TYPES: Final[tuple[str, ...]] = ("総世帯", "二人以上の世帯", "単身世帯")


def _num(v: Any) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


# ------------------------------------------------------------------------------------------ 賃金
def load_wage_tables(guard: S.W21Guard) -> dict[str, np.ndarray]:
    """賃金構造 令和 7 年(第9・6・18 表と短時間 第2表)→ ``AttrTablesB`` の賃金の欄(企業規模計・円と時間)。"""
    O = len(A.WAGE_OCCUPATIONS)
    occ_i = {o: i for i, o in enumerate(A.WAGE_OCCUPATIONS)}
    level = np.zeros((O, 2, 2))
    bonus = np.zeros((O, 2, 2))
    hours = np.zeros((O, 2, 2))
    allw = np.zeros((O, 2))
    _d, _it, rows9 = S.read_derived_rows(guard, "wage_t9")
    forms = {"正社員・正職員計": 0, "正社員・正職員以外計": 1}
    for occ, sex, cat, v in rows9:  # 逐次: 表の行の数ぶん
        if occ not in occ_i or sex not in _SEXES:
            continue
        o, s = occ_i[occ], _SEXES.index(sex)
        if cat == "常用労働者計":
            allw[o, s] = _num(v[5]) * 1000.0
        elif cat in forms:
            f = forms[cat]
            level[o, s, f] = _num(v[5]) * 1000.0
            bonus[o, s, f] = _num(v[6]) * 1000.0
            hours[o, s, f] = _num(v[2])
    # 形態の値が無い(0)ところは常用労働者計で埋める(雇用形態の比=1)
    for f in (0, 1):
        level[:, :, f] = np.where(level[:, :, f] > 0, level[:, :, f], allw)
    hours = np.where(hours > 0, hours, np.nanmax(np.where(hours > 0, hours, np.nan), axis=2, keepdims=True))
    hours = np.nan_to_num(hours, nan=160.0)

    _d, _it, rows6 = S.read_derived_rows(guard, "wage_t6")
    nA = A.WAGE_AGE_EDGES.size
    wage_age = np.zeros((O, 2, nA))
    bonus_age = np.zeros((O, 2, nA))
    tot_w = np.zeros((O, 2))
    tot_b = np.zeros((O, 2))
    for sex, occ, age_lab, v in rows6:  # 逐次: 表の行の数ぶん
        if occ not in occ_i or sex not in _SEXES:
            continue
        o, s = occ_i[occ], _SEXES.index(sex)
        if age_lab == "計":
            tot_w[o, s], tot_b[o, s] = _num(v[5]), _num(v[6])
            continue
        m = re.search(r"(\d+)", age_lab.translate(_FW))
        lo = 0 if age_lab.startswith("～") else (int(m.group(1)) if m else 0)
        a = int(np.searchsorted(A.WAGE_AGE_EDGES, lo, side="right") - 1)
        wage_age[o, s, a], bonus_age[o, s, a] = _num(v[5]), _num(v[6])
    wage_age_ratio = np.where(wage_age > 0, np.divide(wage_age, tot_w[:, :, None], out=np.ones_like(wage_age),
                                                      where=tot_w[:, :, None] > 0), 1.0)
    bonus_age_ratio = np.where(bonus_age > 0, np.divide(bonus_age, tot_b[:, :, None], out=np.ones_like(bonus_age),
                                                        where=tot_b[:, :, None] > 0), 1.0)

    _d, items18, rows18 = S.read_derived_rows(guard, "wage_t18")
    col = [list(items18).index(o) for o in A.WAGE_OCCUPATIONS]
    lo_l: list[float] = []
    hi_l: list[float] = []
    freq = {s: [] for s in _SEXES}
    median = np.zeros((O, 2))
    for sex, lab, v in rows18:  # 逐次: 表の行の数ぶん
        if sex not in _SEXES:
            continue
        vv = np.array([_num(v[j]) for j in col])
        if "中" in lab and "位" in lab and "数" in lab and "分位" not in lab:
            median[:, _SEXES.index(sex)] = vv * 1000.0
            continue
        nums = [float(x) for x in re.findall(r"\d+\.\d+", lab)]
        if not nums or "分位" in lab or "係数" in lab:
            continue
        if sex == _SEXES[0]:
            if lab.endswith("～"):
                lo_l.append(nums[0] * 1000.0)
                hi_l.append(nums[0] * 1000.0 * WAGE_TOP_FACTOR)
            elif len(nums) == 1:
                lo_l.append(WAGE_CLASS_FLOOR_YEN)
                hi_l.append((nums[0] + 0.1) * 1000.0)
            else:
                lo_l.append(nums[0] * 1000.0)
                hi_l.append((nums[1] + 0.1) * 1000.0)
        freq[sex].append(vv)
    cls_freq = np.stack([np.stack(freq[s], axis=1) for s in _SEXES], axis=1)  # (O, 2, K)

    _d, items2, rows2 = S.read_derived_rows(guard, "wage_t2")
    it = list(items2)
    pt = {k: np.zeros((O, 2)) for k in ("hourly", "bonus", "hours_day", "days")}
    keys = {"hourly": "1時間当たり所定内給与額", "bonus": "年間賞与その他特別給与額", "hours_day": "1日当たり所定内実労働時間数",
            "days": "実労働日数"}
    for occ, v in rows2:  # 逐次: 表の行の数ぶん
        if occ not in occ_i:
            continue
        o = occ_i[occ]
        for s, sx in enumerate(_SEXES):
            for k, lab in keys.items():
                x = _num(v[it.index(f"{sx}|{lab}")])
                if x <= 0:
                    x = _num(v[it.index(f"男女計|{lab}")])
                pt[k][o, s] = x * (1000.0 if k == "bonus" else 1.0)
    return {"wage_level": level, "wage_bonus": bonus, "wage_hours": hours, "wage_all": allw,
            "wage_age_ratio": wage_age_ratio, "bonus_age_ratio": bonus_age_ratio,
            "wage_cls_lo": np.array(lo_l), "wage_cls_hi": np.array(hi_l), "wage_cls_freq": cls_freq,
            "wage_median": median, "pt_hourly": pt["hourly"], "pt_bonus": pt["bonus"],
            "pt_hours_day": pt["hours_day"], "pt_days": pt["days"]}


# ------------------------------------------------------------------------------------------ 資産
def _class_bounds(labels: list[str]) -> tuple[np.ndarray, np.ndarray]:
    lo, hi = [], []
    for lab in labels:  # 逐次: 階級の数ぶん(19)
        nums = [float(x) for x in re.findall(r"\d+", lab)]
        if "未満" in lab:
            lo.append(0.0)
            hi.append(nums[0] * 10_000.0)
        elif "以上" in lab:
            lo.append(nums[0] * 10_000.0)
            hi.append(np.inf)
        else:
            lo.append(nums[0] * 10_000.0)
            hi.append(nums[1] * 10_000.0)
    return np.array(lo), np.array(hi)


def solve_tilt(base: np.ndarray, means: np.ndarray, target: float, lo: float = -4.0, hi: float = 4.0,
               iters: int = 60) -> float:
    """重み base × mean^λ の平均が target になる λ(二分法・届かなければ端)。"""
    lm = np.log(np.maximum(means, 1.0))

    def avg(lam: float) -> float:
        w = base * np.exp(lam * (lm - lm.max()))
        return float((w * means).sum() / max(w.sum(), 1e-300))

    if target <= avg(lo):
        return lo
    if target >= avg(hi):
        return hi
    a, b = lo, hi
    for _ in range(iters):  # 逐次: 二分法の回数
        m = 0.5 * (a + b)
        if avg(m) < target:
            a = m
        else:
            b = m
    return 0.5 * (a + b)


def load_asset_tables(guard: S.W21Guard) -> dict[str, np.ndarray]:
    """全国家計構造調査 2024(東京都 第31-0・23-0 表・全国 第4-4 表)→ ``AttrTablesB`` の資産の欄(円・%)。"""
    t31 = S.read_estat_csv(guard, "zk_t31_0")
    labels = [r["貯蓄現在高階級20区分"] for r in t31 if r["表章項目"] == "世帯数分布" and r["世帯の種類３区分"] == "総世帯"
              and r["貯蓄現在高階級20区分"] != "平均"]
    K = len(labels)
    li = {lab: i for i, lab in enumerate(labels)}
    freq = np.zeros((3, K))
    cmean = np.zeros((3, K))
    srate = np.full((3, K), 100.0)
    drate = np.zeros((3, K))
    for r in t31:  # 逐次: 表の行の数ぶん
        t = _TYPES.index(r["世帯の種類３区分"]) if r["世帯の種類３区分"] in _TYPES else -1
        c = li.get(r["貯蓄現在高階級20区分"], -1)
        if t < 0 or c < 0:
            continue
        item, kind, v = r["表章項目"], r["資産・負債の種類42区分"], _num(r["value"])
        if item == "世帯数分布":
            freq[t, c] = v
        elif item.startswith("1世帯当たり") and kind.startswith("金融資産残高"):
            cmean[t, c] = v * 1000.0
        elif item.startswith("資産保有率") and kind.startswith("貯蓄保有率"):
            srate[t, c] = v
        elif item.startswith("資産保有率") and kind.startswith("負債保有率"):
            drate[t, c] = v
    lo, hi = _class_bounds(labels)
    cmean = np.where(cmean > 0, cmean, np.where(np.isfinite(hi), 0.5 * (lo + hi), lo * 1.5))

    edges5 = ["30歳未満（５歳階級）", *[f"{a}～{a + 4}（５歳階級）" for a in range(30, 85, 5)], "85歳以上（５歳階級）"]
    nA = A.ASSET_AGE_EDGES.size
    prof = {k: np.zeros((3, nA)) for k in ("sav", "srate", "dep", "debt", "drate")}
    nat = {k: np.zeros(3) for k in ("sav", "debt")}
    for r in S.read_estat_csv(guard, "zk_t4_4"):  # 逐次: 表の行の数ぶん
        if r.get("世帯区分４区分") != "全世帯" or r.get("世帯主の性別３区分") != "平均":
            continue
        t = _TYPES.index(r["世帯の種類３区分"]) if r["世帯の種類３区分"] in _TYPES else -1
        if t < 0:
            continue
        lab, kind, v = r["世帯主の年齢階級32区分"], r["資産・負債の種類42区分"], _num(r["value"])
        per = r["表章項目"].startswith("1世帯当たり")
        key = {("金融資産残高（貯蓄現在高）", True): "sav", ("通貨性預貯金", True): "dep", ("金融負債残高", True): "debt",
               ("貯蓄保有率（％）", False): "srate", ("負債保有率（％）", False): "drate"}.get((kind, per))
        if key is None:
            continue
        scale = 1000.0 if per else 1.0
        if lab == "平均" and key in nat:
            nat[key][t] = v * scale
        elif lab in edges5:
            prof[key][t, edges5.index(lab)] = v * scale
    tky = {k: np.zeros(3) for k in ("sav", "debt")}
    for r in S.read_estat_csv(guard, "zk_t23_0"):  # 逐次: 表の行の数ぶん
        if r.get("世帯区分４区分") != "全世帯" or r.get("世帯主の年齢階級32区分") != "平均":
            continue
        if not r["表章項目"].startswith("1世帯当たり") or r["世帯の種類３区分"] not in _TYPES:
            continue
        t = _TYPES.index(r["世帯の種類３区分"])
        kind = r["資産・負債の種類42区分"]
        if kind.startswith("金融資産残高"):
            tky["sav"][t] = _num(r["value"]) * 1000.0
        elif kind.startswith("金融負債残高"):
            tky["debt"][t] = _num(r["value"]) * 1000.0
    ratio_sav = np.divide(tky["sav"], nat["sav"], out=np.ones(3), where=nat["sav"] > 0)
    ratio_debt = np.divide(tky["debt"], nat["debt"], out=np.ones(3), where=nat["debt"] > 0)
    tilt = np.zeros((3, nA))
    for t in range(3):  # 逐次: 種類 3 × 年齢 13
        base = freq[t] * srate[t] / 100.0
        for a in range(nA):
            rate = prof["srate"][t, a] / 100.0
            if rate <= 0 or prof["sav"][t, a] <= 0:
                continue
            tilt[t, a] = solve_tilt(base, cmean[t], prof["sav"][t, a] * ratio_sav[t] / rate)
    return {"sav_freq": freq, "sav_cls_mean": cmean, "sav_rate_cls": srate, "sav_lo": lo,
            "sav_hi": np.where(np.isfinite(hi), hi, lo * 2.0), "debt_rate_cls": drate, "sav_mean_age": prof["sav"],
            "sav_rate_age": prof["srate"], "dep_mean_age": prof["dep"], "debt_mean_age": prof["debt"],
            "debt_rate_age": prof["drate"], "tokyo_ratio_sav": ratio_sav, "tokyo_ratio_debt": ratio_debt,
            "sav_tilt": tilt}


def jicc_holder_rate(guard: S.W21Guard) -> tuple[float, float]:
    """JICC の残高のある人(引)÷ 全国の 20 歳以上人口(国勢調査 2025 第2-5表【不詳補完値】の全国の行)。返り値=(率, 分母)。"""
    _d, items, rows = S.read_derived_rows(guard, "c25w_b02_05")
    dims = list(_d)
    ci, ni = dims.index("地域識別コード"), dims.index("地域名")
    cols = [j for j, it in enumerate(items) if re.match(r"^\d{3}_(\d+)歳", it) and int(re.match(r"^\d{3}_(\d+)", it)
                                                                                      .group(1)) >= A.CREDIT_MIN_AGE]
    pop20 = 0.0
    for r in rows:  # 逐次: 表の行の数ぶん
        if r[ci] == "a" and str(r[ni]).endswith("_全国"):
            pop20 += sum(_num(r[-1][j]) for j in cols)
    return (A.JICC_HOLDERS / pop20 if pop20 > 0 else 0.0), pop20


# ------------------------------------------------------------------------------------------ 組み立て
def household_type(family_type: np.ndarray) -> np.ndarray:
    """段 2 の家族類型 → 全国家計構造調査の世帯の種類(1 二人以上・2 単身=単独世帯 "3" と施設等)。"""
    ft = np.asarray(family_type).astype(str)
    return np.where(np.isin(ft, ["3", "institution", ""]), 2, 1).astype(np.int64)


def build_money(people: Mapping[str, np.ndarray], households: Mapping[str, np.ndarray], tables: A.AttrTablesB,
                seed: int | str) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    """体ごとと世帯ごとのお金の列(円・空欄は −1)。``people`` は段 4 の人の表(住民+外から来て働く人)、``households`` は
    段 2 の世帯の表。乱数の鍵: 世帯=(世帯の番号)・外から来る人の世帯=(人の番号)・人=(人の番号)。"""
    pid = np.asarray(people["person_id"], dtype=np.int64)
    n = pid.size
    kind = np.asarray(people["kind"]).astype(str)
    age = np.asarray(people["age"], dtype=np.int64)
    hid = np.asarray(people["household_id"], dtype=np.int64)
    # --- 世帯(段 2)
    h_id = np.asarray(households["household_id"], dtype=np.int64)
    if h_id.size and not (np.diff(h_id) > 0).all():
        raise ValueError("世帯の表は household_id の昇順(段 2 の並び)であること")
    h_type = household_type(households["family_type"])
    h_age = np.asarray(households["head_age"], dtype=np.int64)
    zero3 = np.zeros((h_id.size, 1), dtype=np.int64)
    hkey = np.concatenate([h_id[:, None], zero3, zero3], axis=1)

    def hcall(name: str, attrs: dict[str, Any], keyarr: np.ndarray, dom: str) -> np.ndarray:
        return A.call(name, attrs, tables, A.AttrKey(seed, dom, keyarr))

    ha: dict[str, Any] = {"hh_type": h_type, "head_age": h_age}
    ha["household_savings"] = hcall("household_savings", ha, hkey, "w21b.money.savings")
    ha["household_deposits"] = hcall("household_deposits", ha, hkey, "w21b.money.deposits")
    ha["household_debt"] = hcall("household_debt", ha, hkey, "w21b.money.debt")
    # 18 歳以上の世帯員の数(いなければ世帯主に全部)
    res = (kind == "resident") & (hid >= 0)
    pos = np.searchsorted(h_id, hid[res])
    adults = np.bincount(pos[age[res] >= ADULT_AGE], minlength=h_id.size)
    # --- 外から来て働く人の世帯(本人=世帯主・総世帯の表)
    com = kind == "commuter"
    ckey = np.stack([pid[com], np.zeros(int(com.sum()), dtype=np.int64), np.zeros(int(com.sum()), dtype=np.int64)],
                    axis=1)
    ca: dict[str, Any] = {"hh_type": np.zeros(int(com.sum()), dtype=np.int64), "head_age": age[com]}
    ca["household_savings"] = hcall("household_savings", ca, ckey, "w21b.money.commuter_savings")
    ca["household_deposits"] = hcall("household_deposits", ca, ckey, "w21b.money.commuter_deposits")
    ca["household_debt"] = hcall("household_debt", ca, ckey, "w21b.money.commuter_debt")
    # --- 人ごと
    share = np.zeros(n)
    hh_of = np.full(n, -1, dtype=np.int64)
    hh_of[res] = pos
    head = np.asarray(people["relation"]).astype(str) == "head"
    ad = res & (age >= ADULT_AGE)
    share[ad] = 1.0 / np.maximum(adults[hh_of[ad]], 1)
    no_adult = res & head & (adults[np.clip(hh_of, 0, None)] == 0)
    share[no_adult] = 1.0
    inst = res & (np.asarray(people["relation"]).astype(str) == "institution_resident")
    share[inst] = 1.0
    cols: dict[str, np.ndarray] = {}
    for k in ("household_savings", "household_deposits", "household_debt"):
        v = np.full(n, -1, dtype=np.int64)
        hv = ha[k][np.clip(hh_of, 0, None)]
        v[res] = np.where(hv[res] >= 0, np.round(hv[res] * share[res]), -1).astype(np.int64)
        v[com] = np.where(ca[k] >= 0, ca[k], -1)
        cols[k.replace("household_", "")] = v
    pkey = np.stack([pid, np.zeros(n, dtype=np.int64), np.zeros(n, dtype=np.int64)], axis=1)
    wa = {"emp_status": people["emp_status"], "occupation_major": people["occupation_major"], "sex": people["sex"],
          "age": age}
    wkey = A.AttrKey(seed, "w21b.money.wage", pkey)
    person_cols = {
        "person_id": pid.astype(np.int32),
        "kind": kind.astype(object),
        "wage_monthly": A.call("wage_monthly", wa, tables, wkey),
        "wage_hourly": A.call("wage_hourly", wa, tables, wkey),
        "wage_annual": A.call("wage_annual", wa, tables, wkey),
        "savings": cols["savings"], "deposits": cols["deposits"],
        "other_financial": np.where(cols["savings"] >= 0, cols["savings"] - np.maximum(cols["deposits"], 0), -1),
        "debt": cols["debt"],
        "consumer_credit": A.call("consumer_credit", {"age": age}, tables, A.AttrKey(seed, "w21b.money.credit", pkey)),
        "wallet_cash": A.call("wallet_cash", {"age": age}, tables, A.AttrKey(seed, "w21b.money.blank", pkey)),
        "card_holding": A.call("card_holding", {"age": age}, tables, A.AttrKey(seed, "w21b.money.blank", pkey)),
        "account_holding": A.call("account_holding", {"age": age}, tables, A.AttrKey(seed, "w21b.money.blank", pkey)),
        "asset_share": np.round(np.where(com, 1.0, share), 6),
        "money_basis": np.where(com, "commuter_own_household_total",
                                np.where(share > 0, "household_share_adults", "household_member_no_share")).astype(object),
    }
    hh_cols = {
        "household_id": h_id.astype(np.int32),
        "hh_type": np.array(A.HH_TYPES, dtype=object)[h_type],
        "head_age": h_age.astype(np.int16),
        "adults": adults.astype(np.int16),
        "savings": ha["household_savings"], "deposits": ha["household_deposits"],
        "other_financial": np.where(ha["household_savings"] >= 0,
                                    ha["household_savings"] - np.maximum(ha["household_deposits"], 0), -1),
        "debt": ha["household_debt"],
    }
    return person_cols, hh_cols
