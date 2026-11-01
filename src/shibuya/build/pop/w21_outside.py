"""W21 段 7「外の人」(計画 第 4 期 段 7・設計書 §2-1 の 3 種類のペルソナ・PENDING 仮-23)。版 1.1.0。

正: 設計書 §2-1(範囲の中・周りの輪・遠く+体のない遠くの人。遠くの人の「誰がいるか」は世帯・家族構成の実データから)・
答申 R-116 §1-5(#52 国勢調査 2025 第2-5/10/12-3 表・#53 2020 第4表の流入元・#54 訪日=JNTO と都・#55 人々のつながりの調査=
体のない遠くの人の頻度の候補・#56 輪)・R-109(乗り換えだけの人 70〜80 万・JR で通るだけの人 約 46 万=構築側の値)・R-110 §3-5
(JNTO 2025 の国籍別)・PENDING 仮-23(**都市圏の私事・業務の来街の 1 日の人数は空欄**=「来るか」は本人の判断の結果)。

**作るのは層の表(人は作らない=「粗く」)**。〔検収 L5〕**層は母集団の表で、互いに重なる**: 外から来て働く人
(commuter)のうち常住地が渋谷区(輪)の体は輪(ring)の人数の中にもいて、流入元の市区町村の通勤者は来る可能性のある人
(potential_visitor)の人口の中にもいる=段 10・11 で輪や遠くの人を体にするときは commuter の体を除く(二重に作らない)。1 行=層 × 属性(常住地・男女・年齢の階級・国籍)× 人数(その層の母集団の数)・
流入元の重み・**出現の確からしさは空欄**(段 11 の後に本人の判断の結果から出す)。外から来て働く人だけは段 4 で体を作った
(行は体の数を集計した層)。

| 層(``layer``) | 帯 | 人数の出どころ | 体 |
|---|---|---|---|
| commuter | 範囲の中 | 段 4 で作った体の集計(常住地 × 男女 × 年齢 5 歳) | あり |
| student_in | 範囲の中 | 第4表の渋谷区へ通学する人(15 歳未満を含む)の常住地ごと=区全体・**舞台の分は空欄**(学校の定員が要る) | なし |
| ring | 周りの輪 | 渋谷区の町丁目の被覆率の外の分(段 2 と同じ「2020 の形 × 2025 の区の総数」・町丁目 × 男女 × 年齢 16 階級) | なし |
| potential_visitor | 遠く | 第4表の流入元(1,892 市区町村=2020 の符号で 1,896・浜松市の旧 7 区を新 3 区へ寄せた)の 2025 の人口(第2-5表・男女 × 年齢 5 歳)・重み=流入元の通勤通学の割合 | なし |
| inbound | 範囲の中 | 訪日 1 日 43,000〜85,000(段 1 の枠=引)・国籍の割合=JNTO 2025(引)・**渋谷の訪問率は空欄** | なし |
| transfer_only・through_jr | 範囲の中 | 段 1 の枠の行(引)=枠と分布だけ | なし |
| visitors_metro_private_business・visitors_domestic_outside_metro | 範囲の中 | **空欄**(仮-23・材料なし) | なし |
| bodiless_contact | 遠く | **空欄**(人数は未リサーチ)・世帯は ``w21_outside_households``(流入元の第10表・第12-3表) | なし |

逐次ループ宣言(P4): 表の行の数ぶん(市区町村 1,892 × 男女)。体の数に比例するループは無い。
"""

from __future__ import annotations

import re
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

import numpy as np

from . import w21_sources as S
from . import w21_tables as T

__all__ = ["JNTO_2025", "AGE5_LABELS", "origins", "muni_population", "outside_strata", "outside_households",
           "OUTSIDE_COLUMNS"]

#: JNTO 2025 年 国籍別 訪日外客数(確定値・上位 15 と総数=R-110 §3-5 の写し=引)。残りは「その他」。
JNTO_2025: Final[Mapping[str, int]] = MappingProxyType({
    "韓国": 9_459_711, "中国": 9_095_931, "台湾": 6_763_424, "米国": 3_306_820, "香港": 2_517_399, "タイ": 1_233_103,
    "豪州": 1_058_396, "フィリピン": 885_023, "カナダ": 688_019, "ベトナム": 678_594, "インドネシア": 640_577,
    "マレーシア": 636_575, "英国": 535_004, "フランス": 457_566, "ドイツ": 429_479,
})
JNTO_2025_TOTAL: Final[int] = 42_683_301
#: 年齢 5 歳の階級(0-4 … 95-99・100 歳以上=21)。
AGE5_LABELS: Final[tuple[str, ...]] = tuple([f"{a}-{a + 4}" for a in range(0, 100, 5)] + ["100+"])
#: 出力の列。
OUTSIDE_COLUMNS: Final[tuple[str, ...]] = (
    "layer", "band", "origin_code", "origin_name", "nationality", "sex", "age_class", "count", "count_low",
    "count_high", "unit", "inflow_weight", "has_bodies", "appearance_prob", "mark", "source",
)

_MUNI_LEVELS: Final[tuple[str, ...]] = ("0", "2", "3")
#: 〔検収 L3〕2020 の市区町村の符号 → 2025 の表の符号(区の再編=浜松市 2024-01-01: 中・東・西・南区 → 中央区・北区と
#: 浜北区 → 浜名区・天竜区 → 天竜区)。北区の三方原地区は中央区へ移ったが、区の単位で寄せる(expedient)。
MUNI_CODE_2025: Final[Mapping[str, tuple[str, str]]] = MappingProxyType({
    "22131": ("22138", "浜松市中央区"), "22132": ("22138", "浜松市中央区"), "22133": ("22138", "浜松市中央区"),
    "22134": ("22138", "浜松市中央区"), "22135": ("22139", "浜松市浜名区"), "22136": ("22139", "浜松市浜名区"),
    "22137": ("22140", "浜松市天竜区"),
})


def _f(v: Any) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def origins(guard: S.W21Guard) -> dict[str, Any]:
    """第4表(従業地=渋谷区)→ 流入元の市区町村(5 桁の符号・名・15 歳以上の就業者・通学者(15 歳未満を含む)・総数)と、
    区の中の行(自宅で従業・自宅外の区内・通学)。"""
    dims, items, rows = S.read_derived_rows(guard, "c20_t04")
    d = list(dims)
    c_cat, c_lvl, c_name = d.index("常住地"), d.index("地域識別コード（常住地）"), d.index("地域名（常住地）")
    j_tot, j_wk, j_st = items.index("0_総数"), items.index("11_15歳以上就業者"), \
        next(i for i, x in enumerate(items) if x.startswith("R1_"))
    codes, names, workers, students, total = [], [], [], [], []
    pos: dict[str, int] = {}
    inside: dict[str, dict[str, float]] = {}
    for r in rows:  # 逐次: 表の行の数ぶん(≈2,000)
        cat, lvl, name, v = str(r[c_cat]), str(r[c_lvl]), str(r[c_name]), r[-1]
        if name.endswith("_全国"):
            inside[cat] = {"total": _f(v[j_tot]), "workers": _f(v[j_wk]), "students": _f(v[j_st])}
            continue
        if not cat.startswith("02_") or lvl not in _MUNI_LEVELS or not name[:5].isdigit():
            continue
        code, nm = MUNI_CODE_2025.get(name[:5], (name[:5], name[6:]))
        if code in pos:  # 2025 の符号に寄せた区を合わせる
            i = pos[code]
            workers[i] += _f(v[j_wk])
            students[i] += _f(v[j_st])
            total[i] += _f(v[j_tot])
            continue
        pos[code] = len(codes)
        codes.append(code)
        names.append(nm)
        workers.append(_f(v[j_wk]))
        students.append(_f(v[j_st]))
        total.append(_f(v[j_tot]))
    return {"codes": np.array(codes, dtype=object), "names": np.array(names, dtype=object),
            "workers": np.array(workers), "students": np.array(students), "total": np.array(total), "inside": inside}


def muni_population(guard: S.W21Guard, codes: Sequence[str]) -> tuple[np.ndarray, list[str]]:
    """国勢調査 2025 第2-5表【不詳補完値】→ (市区町村, 男女 2, 年齢 5 歳 21) の人口と、表に無い符号の一覧。"""
    dims, items, rows = S.read_derived_rows(guard, "c25w_b02_05")
    d = list(dims)
    c_sex, c_code, c_lvl = d.index("男女"), d.index("2025年_地域コード"), d.index("地域識別コード")
    ages = [(j, int(m.group(1))) for j, it in enumerate(items) if (m := re.match(r"^\d{3}_(\d+)歳", it))]
    idx = {c: i for i, c in enumerate(codes)}
    out = np.zeros((len(codes), 2, len(AGE5_LABELS)))
    seen = set()
    for r in rows:  # 逐次: 表の行の数ぶん(≈3,900)
        if str(r[c_lvl]) == "a":
            continue
        i = idx.get(str(r[c_code]))
        if i is None:
            continue
        s = 0 if str(r[c_sex]).startswith("1_") else 1
        seen.add(str(r[c_code]))
        v = r[-1]
        for j, a in ages:  # 逐次: 各歳(101)
            out[i, s, min(a // 5, 20)] += _f(v[j])
    return out, [c for c in codes if c not in seen]


def _group_of(item: str) -> str | None:
    head = item.split("_", 1)[0]
    if head in T.GROUP_OF_TYPE:
        return T.GROUP_OF_TYPE[head]
    return None


def outside_households(guard: S.W21Guard, codes: Sequence[str], names: Sequence[str]) -> dict[str, np.ndarray]:
    """体のない遠くの人(流入元の市区町村)の世帯の層: 第10表(家族類型の区分 6 × 世帯人員 7)と第12-3表(家族類型の区分 6
    × 世帯主の年齢 5 歳)。どちらも一般世帯の数。"""
    idx = {c: i for i, c in enumerate(codes)}
    rows_out: dict[str, list[Any]] = {k: [] for k in ("origin_code", "origin_name", "family_group", "hh_size",
                                                      "head_age_class", "households", "basis")}

    def add(i: int, grp: str, size: int, hage: str, val: float, basis: str) -> None:
        rows_out["origin_code"].append(codes[i])
        rows_out["origin_name"].append(names[i])
        rows_out["family_group"].append(grp)
        rows_out["hh_size"].append(size)
        rows_out["head_age_class"].append(hage)
        rows_out["households"].append(val)
        rows_out["basis"].append(basis)

    dims, items, rows = S.read_derived_rows(guard, "c25w_b10_muni")
    d = list(dims)
    c_name, c_size = d.index("地域名"), d.index("世帯人員の人数")
    groups = [(j, _group_of(it)) for j, it in enumerate(items)]
    for r in rows:  # 逐次: 表の行の数ぶん
        i = idx.get(str(r[c_name])[:5])
        m = re.match(r"^(\d)_", str(r[c_size]))
        if i is None or not m or m.group(1) == "0":
            continue
        acc: dict[str, float] = {}
        for j, g in groups:  # 逐次: 類型の数ぶん
            if g is not None:
                acc[g] = acc.get(g, 0.0) + _f(r[-1][j])
        for g in T.GROUPS:
            if acc.get(g, 0.0) > 0:
                add(i, g, int(m.group(1)), "", acc[g], "c25w_b10")
    dims, items, rows = S.read_derived_rows(guard, "c25w_b12_03")
    d = list(dims)
    c_name, c_age = d.index("地域名"), d.index("世帯主の年齢")
    groups = [(j, _group_of(it)) for j, it in enumerate(items)]
    for r in rows:  # 逐次: 表の行の数ぶん
        i = idx.get(str(r[c_name])[:5])
        lab = str(r[c_age])
        if i is None or not re.match(r"^\d{2}_", lab) or lab.startswith("00_"):
            continue
        acc = {}
        for j, g in groups:
            if g is not None:
                acc[g] = acc.get(g, 0.0) + _f(r[-1][j])
        for g in T.GROUPS:
            if acc.get(g, 0.0) > 0:
                add(i, g, -1, lab.split("_", 1)[1], acc[g], "c25w_b12_03")
    return {k: np.array(v, dtype=object if k in ("origin_code", "origin_name", "family_group", "head_age_class",
                                                  "basis") else (np.int16 if k == "hh_size" else np.float64))
            for k, v in rows_out.items()}


def outside_strata(*, org: Mapping[str, Any], pop: np.ndarray, missing: Sequence[str], commuters: Mapping[str, Any],
                   ring_age16_sex: np.ndarray, ring_keys: Sequence[str], frame_rows: Sequence[Mapping[str, Any]],
                   ring_total: float | None = None) -> dict[str, np.ndarray]:
    """層の表(:data:`OUTSIDE_COLUMNS`)。``org`` は :func:`origins` の返り値・``pop`` は :func:`muni_population`・
    ``commuters`` は段 4 の外から来て働く人(``origin_muni``・``sex``・``age``)・``ring_age16_sex`` は輪の目標
    (町丁目 × 16 × 2)・``frame_rows`` は段 1 の枠の行。``ring_total`` を渡すと輪の行の和をその値に比で合わせる
    〔検収 L6〕=段 1 の枠の行(区の総数 − 住民の体の数)と同じ値にする。"""
    cols: dict[str, list[Any]] = {k: [] for k in OUTSIDE_COLUMNS}

    def add(**kw: Any) -> None:
        for k in OUTSIDE_COLUMNS:
            cols[k].append(kw.get(k, {"count": None, "count_low": None, "count_high": None, "inflow_weight": None,
                                      "appearance_prob": None, "sex": -1, "has_bodies": False}.get(k, "")))

    frame = {r["layer"]: r for r in frame_rows}
    codes, names = org["codes"], org["names"]
    tot = np.where(np.isin(np.asarray(codes).astype(str), list(missing)), 0.0, org["total"])
    w = tot / max(tot.sum(), 1.0)  # 〔検収 L3〕表に無い符号を除いて和 1 に正規化し直す
    # --- 外から来て働く人(体あり=段 4 の集計)
    oc = np.asarray(commuters["origin_muni"]).astype(str)
    sx = np.asarray(commuters["sex"], dtype=np.int64)
    a5 = np.minimum(np.asarray(commuters["age"], dtype=np.int64) // 5, 20)
    name_of = dict(zip(codes.tolist(), names.tolist()))
    name_of.setdefault("13113", "渋谷区(舞台の外の町丁目=輪)")
    key = np.char.add(np.char.add(oc, "|"), np.char.add(sx.astype(str), np.char.add("|", a5.astype(str))))
    uk, cnt = np.unique(key, return_counts=True)
    for k, c in zip(uk.tolist(), cnt.tolist()):  # 逐次: 層の組の数ぶん
        o, s, a = k.split("|")
        add(layer="commuter", band="in_area", origin_code=o, origin_name=name_of.get(o, ""), sex=int(s),
            age_class=AGE5_LABELS[int(a)], count=float(c), unit="persons", has_bodies=True, mark="計算",
            source="段 4 の体(従業地 第11-1・8・16-1 表・第4表の流入元)")
    # --- 渋谷区へ通学する人(区全体・舞台の分は空欄)
    for i in np.flatnonzero(org["students"] > 0).tolist():  # 逐次: 流入元の数ぶん
        add(layer="student_in", band="in_area", origin_code=codes[i], origin_name=names[i],
            count_low=float(org["students"][i]), count_high=float(org["students"][i]), unit="persons_ward_total",
            inflow_weight=float(w[i]), mark="空欄", source="国勢調査 2020 第4表(渋谷区へ通学=区全体)・舞台の分は空欄")
    # --- 周りの輪(渋谷区の残りの町丁目)
    rs = float(np.clip(ring_age16_sex, 0.0, None).sum())
    ring_scale = (float(ring_total) / rs) if (ring_total is not None and rs > 0) else 1.0
    for c in range(ring_age16_sex.shape[0]):  # 逐次: 町丁目の数ぶん
        for s in range(2):
            for a in range(16):
                v = float(ring_age16_sex[c, a, s]) * ring_scale
                if v <= 0:
                    continue
                lo = int(T.AGE16_EDGES[a])
                lab = f"{lo}-{lo + 4}" if a < 15 else f"{lo}+"
                add(layer="ring", band="ring", origin_code=str(ring_keys[c]), origin_name="渋谷区の町丁目(被覆率の外の分)",
                    sex=s, age_class=lab, count=round(v, 6), unit="persons", mark="計算",
                    source="国勢調査 2020 小地域 第3表 × 2025 第2-1表 ×(1 − 被覆率)=段 2 と同じ方法・和は段 1 の枠の行に合わせた")
    # --- 来る可能性のある人(遠く)
    for i in range(len(codes)):  # 逐次: 流入元の数ぶん(1,892)
        if codes[i] in missing:
            continue
        for s in range(2):
            for a in range(len(AGE5_LABELS)):
                v = float(pop[i, s, a])
                if v <= 0:
                    continue
                add(layer="potential_visitor", band="far", origin_code=codes[i], origin_name=names[i], sex=s,
                    age_class=AGE5_LABELS[a], count=v, unit="persons_resident", inflow_weight=float(w[i]), mark="計算",
                    source="国勢調査 2025 第2-5表【不詳補完値】・重み=2020 第4表の通勤通学の流入の割合")
    # --- 訪日(国籍の割合=JNTO 2025・1 日の幅=段 1 の枠)
    fr = frame.get("visitors_inbound", {})
    lo, hi = (fr.get("value") or [None, None])
    rest = JNTO_2025_TOTAL - sum(JNTO_2025.values())
    for nat, v in [*JNTO_2025.items(), ("その他", rest)]:
        share = v / JNTO_2025_TOTAL
        add(layer="inbound", band="in_area", nationality=nat,
            count_low=None if lo is None else round(lo * share, 1), count_high=None if hi is None else round(hi * share, 1),
            unit="persons_per_day", inflow_weight=round(share, 6), mark="引",
            source="段 1 の枠(R-109 §2)× JNTO 2025 国籍別の割合(R-110 §3-5)・渋谷の訪問率は空欄")
    # --- 枠だけの層(人は作らない)と空欄の層
    for layer in ("transfer_only", "through_jr", "visitors_metro_private_business", "visitors_domestic_outside_metro"):
        r = frame.get(layer, {})
        v = r.get("value")
        add(layer=layer, band="in_area", count_low=None if v is None else float(v[0]),
            count_high=None if v is None else float(v[1]), unit="persons_per_day",
            mark=r.get("mark", "空欄"), source=str(r.get("source", "")))
    r = frame.get("bodiless_contacts", {})
    add(layer="bodiless_contact", band="far", unit="persons", mark="空欄",
        source="人数は未リサーチ(人々のつながりに関する基礎調査=候補)・世帯は w21_outside_households")
    out: dict[str, np.ndarray] = {}
    for k in OUTSIDE_COLUMNS:
        v = cols[k]
        if k in ("count", "count_low", "count_high", "inflow_weight", "appearance_prob"):
            out[k] = np.array([None if x is None else float(x) for x in v], dtype=object)  # 空欄は null
        elif k == "sex":
            out[k] = np.array(v, dtype=np.int8)
        elif k == "has_bodies":
            out[k] = np.array(v, dtype=bool)
        else:
            out[k] = np.array(v, dtype=object)
    return out
