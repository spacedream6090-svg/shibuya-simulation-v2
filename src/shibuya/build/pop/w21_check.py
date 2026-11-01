"""W21 段 8「点検」(PS6): 段 1〜7 の資産(住民・外から来て働く人・世帯・組織・権利・関係・お金・なじみの場所・外の人の層)を
点検の表にする。**合否は付けない**(CA8 と同じ=診断)。出力 ``w21_check.json``。

正: 設計書 §2-5 PS6(年齢・性別・世帯・職業の分布 vs 国勢調査・経済センサス/言語と国籍 vs 在留外国人統計・訪日外客/住人の
似通い=D-68 の画一性・DM6 のばらつきの比)と注(**人口の作り直しに使った統計を「合っている」の証拠にしない**=構築に使った
表との比べは「点検」の印)・計画 第 4 期 段 8(分布の食い違い・二重・全員が別人か)・§4 計器。

(a) 分布の食い違い(:func:`distribution_rows`): 区分ごとに SRMSE・JSD・最大の差の区分。比べる表が構築に使っていない区分なら
    ``basis`` が ``BASIS_NOT_BUILD``・構築に使った表なら ``BASIS_BUILD``。
    - 構築に使っていない区分: 従業地 第15-1表(舞台で働く人の男女 × 年齢 × 職業=年齢と職業の結合は段 3〜4 が作っていない)・
      2025 第15-1表(夫婦のいる世帯の夫の年齢 × 子の数・最年少の子の年齢=段 2 が作っていない結合)・東京都の外国人人口
      第1表(2026-07-01=国籍を引いた表の半年後=独立は弱い)。
    - 構築に使った表(点検): 住民の年齢 × 男女(舞台の目標)・外から来て働く人の年齢 × 男女(第11-1表)・世帯の人員と
      家族類型(舞台の目標と区の第10表)・席の地位(第6-2表)・職業 × 産業(第16-1表)・国籍(第3表)・日本語の程度(R-110)。
(b) 二重(:func:`double_rows`): 人の番号の重なり・住民 × 外から来て働く人・層の重なり(輪から通う体)・席の二重・席 × 担当・
    W16 の在庫との二重計上の見積り(段 10 で外す行の数=``w21_port10.w16_keep_table``)。
(c) 全員が別人か(:func:`uniqueness`): 属性の組(年齢・性別・世帯・職業・勤め先・家・なじみの場所の順位 1〜3)の重複と、
    重複の中で人物の文まで同じ(区別できない)組。
(d) 住人の似通い(:func:`diversity_vs_w16`): 属性ごとと組のエントロピー・ペアの距離の分布を W16 の在庫(同じ層=住民・区内で
    働く住民・外から来て働く人)と並べる。行動のばらつき(DM6)は GPU の後=欄だけ。

逐次ループ宣言(P4): 点検の行の数ぶん(≤ 20)・表の区分の数ぶん(≤ 20)・属性の数ぶん(≤ 8)。体の数に比例するループは無い。
"""

from __future__ import annotations

import csv
import io
from typing import Any, Final, Mapping

import numpy as np

from . import attr_fns as A
from . import w21_checks as WC
from . import w21_sources as S
from . import w21_tables as T

__all__ = ["SCHEMA", "CONTINENTS", "read_jukiki", "distribution_rows", "double_rows", "uniqueness", "diversity_vs_w16",
           "couple_children", "AGE17_LABELS", "PAIRS"]

SCHEMA: Final[str] = "w21c.check/1"
#: 東京都の外国人人口の表の大陸の小計の列(国籍の列ではない)。
CONTINENTS: Final[tuple[str, ...]] = ("アジア", "ヨーロッパ", "アフリカ", "北米", "南米", "オセアニア")
AGE17_LABELS: Final[tuple[str, ...]] = tuple([f"{a}-{a + 4}" for a in range(15, 95, 5)] + ["95+"])
#: ペアの距離を数えるペアの数(Philox で決まる・expedient の幅=未リサーチ)。
PAIRS: Final[int] = 200_000
_SEXW = ("男", "女")


def read_jukiki(guard: S.W21Guard, sid: str) -> dict[str, float]:
    """東京都の外国人人口の CSV(UTF-8・見出し 1 行)→ 渋谷区の行の国・地域ごとの人数(大陸の小計・総数・男・女・前年同月の
    比較の列を除く)。"""
    text = guard.source_bytes(sid).decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(text)))
    head = rows[0]
    row = next(r for r in rows[1:] if len(r) > 1 and r[1] == S.WARD_CODE)
    out: dict[str, float] = {}
    for j in range(3, len(head)):  # 逐次: 列の数(≤ 210)
        name = head[j].strip()
        if name in ("総数", "男", "女", *CONTINENTS) or name.startswith("前年同月"):
            continue
        v = row[j].strip() if j < len(row) else ""
        if v in ("", "-"):
            continue
        out[name] = float(v)
    return out


def _row(name: str, basis: str, table: str, sim: np.ndarray, tgt: np.ndarray, labels: list[str],
         note: str = "") -> dict[str, Any]:
    return {"name": name, "basis": basis, "table": table, **WC.fit_cells(sim, tgt, labels), "note": note}


def couple_children(people: Mapping[str, Any]) -> dict[str, np.ndarray]:
    """夫婦(世帯主と配偶者)のいる世帯の夫の年齢・子(続き柄が子)の数・最年少の子の年齢(子のいない世帯は −1)。"""
    hid = np.asarray(people["household_id"], dtype=np.int64)
    rel = np.asarray(people["relation"], dtype=object).astype(str)
    age = np.asarray(people["age"], dtype=np.int64)
    sex = np.asarray(people["sex"], dtype=np.int64)
    H = int(hid.max()) + 1 if hid.size and hid.max() >= 0 else 0
    ok = hid >= 0
    head_age = np.full(H, -1)
    head_sex = np.full(H, -1)
    sp_age = np.full(H, -1)
    h = rel == "head"
    head_age[hid[h & ok]] = age[h & ok]
    head_sex[hid[h & ok]] = sex[h & ok]
    s = rel == "spouse"
    sp_age[hid[s & ok]] = age[s & ok]
    ch = (rel == "child") & ok
    n_child = np.bincount(hid[ch], minlength=H)
    young = np.full(H, 999)
    np.minimum.at(young, hid[ch], age[ch])
    couple = sp_age >= 0
    husband = np.where(head_sex == 0, head_age, sp_age)
    idx = np.flatnonzero(couple)
    return {"husband_age": husband[idx], "children": n_child[idx], "youngest": np.where(n_child[idx] > 0, young[idx], -1)}


def distribution_rows(*, people: Mapping[str, Any], households: Mapping[str, Any], tg: Any, ward: Any,
                      tables3: A.AttrTables, e15: S.Derived, b15: S.Derived, nationality: np.ndarray,
                      japanese_level: np.ndarray, juki_t3: Mapping[str, float], juki_t1: Mapping[str, float],
                      rows62: list, items62: tuple[str, ...], stage_keys: list[str]) -> list[dict[str, Any]]:
    """(a) の点検の行(住民の年齢 × 男女 … 日本語の程度)。"""
    out: list[dict[str, Any]] = []
    kind = np.asarray(people["kind"], dtype=object).astype(str)
    age = np.asarray(people["age"], dtype=np.int64)
    sex = np.asarray(people["sex"], dtype=np.int64)
    res = kind == "resident"
    com = kind == "commuter"
    # ---- 住民の年齢 16 × 男女(舞台の目標=2020 の町丁目の形 × 2025 の区の総数=構築)
    a16 = np.clip(np.searchsorted(T.AGE16_EDGES[1:], age, side="right"), 0, 15)
    sim = np.zeros((16, 2))
    np.add.at(sim, (a16[res], sex[res]), 1.0)
    lab16 = [f"{e}-{e + 4}" if i < 15 else "75+" for i, e in enumerate(T.AGE16_EDGES.tolist())]
    labels = [f"{a}|{_SEXW[s]}" for a in lab16 for s in range(2)]
    tgt = np.asarray(tg.age16_sex).sum(axis=0)
    row = _row("住民の年齢 16 × 男女", WC.BASIS_BUILD, "国勢調査 2020 小地域 第3表 × 2025 第2-1表(舞台の目標)", sim, tgt, labels)
    keys = np.asarray(people["home_chome_key"], dtype=object).astype(str)
    pos = {k: i for i, k in enumerate(stage_keys)}
    ci = np.array([pos.get(k, -1) for k in np.unique(keys[res]).tolist()], dtype=np.int64)  # 逐次: 町丁目の数(42)
    ck = ci[np.unique(keys[res], return_inverse=True)[1]]
    simc = np.zeros((len(stage_keys), 32))
    okc = ck >= 0
    np.add.at(simc, (ck[okc], (a16[res] * 2 + sex[res])[okc]), 1.0)
    row["by_chome"] = WC.table_fit({"t03": (simc, np.asarray(tg.age16_sex).reshape(len(stage_keys), 32))})["t03"]
    out.append(row)
    # ---- 外から来て働く人の年齢 17 × 男女(第11-1表=構築)
    a17 = A.age17(age)
    sim = np.zeros((2, 17))
    m = com & (a17 >= 0)
    np.add.at(sim, (sex[m], a17[m]), 1.0)
    tgt = np.asarray(tables3.commuter_industry).sum(axis=2)
    out.append(_row("外から来て働く人の男女 × 年齢 17", WC.BASIS_BUILD, "国勢調査 2020 従業地 第11-1表(従業地=渋谷区)",
                    sim, tgt, [f"{_SEXW[s]}|{a}" for s in range(2) for a in AGE17_LABELS]))
    # ---- 舞台で働く人の男女 × 年齢 17 × 職業 12(従業地 第15-1表=構築に使っていない区分=年齢と職業の結合)
    area = np.asarray(people["workplace_area"], dtype=object).astype(str)
    works = np.isin(area, ["home", "stage"]) & (a17 >= 0)
    occ = np.array([A.OCCUPATION_MAJORS.index(x) if x in A.OCCUPATION_MAJORS else -1 for x in
                    np.unique(np.asarray(people["occupation_major"], dtype=object).astype(str)).tolist()],
                   dtype=np.int64)[np.unique(np.asarray(people["occupation_major"], dtype=object).astype(str),
                                             return_inverse=True)[1]]  # 逐次: 語の種類(13)
    w = works & (occ >= 0)
    sim = np.zeros((2, 17, 12))
    np.add.at(sim, (sex[w], a17[w], occ[w]), 1.0)
    tgt = np.zeros((2, 17, 12))
    o_items = [e15.items.index(next(it for it in e15.items if it.startswith(f"{L}_"))) for L in A.OCCUPATION_MAJORS]
    for si, sx in enumerate(("1_男", "2_女")):  # 逐次: 男女 × 年齢(34)
        for ai in range(17):
            key = next((k for k in e15.table if k[0] == sx and k[1].startswith(f"{ai + 1:02d}_")), None)
            if key is not None:
                tgt[si, ai] = np.nan_to_num(e15.table[key][o_items])
    labels = [f"{_SEXW[s]}|{a}|{L}" for s in range(2) for a in AGE17_LABELS for L in A.OCCUPATION_MAJORS]
    row = _row("舞台で働く人の男女 × 年齢 17 × 職業 12", WC.BASIS_NOT_BUILD,
               "国勢調査 2020 従業地 第15-1表(従業地=渋谷区=区全体の形)", sim, tgt, labels,
               "年齢と職業の結合は段 3(住民=第10-1表)・段 4(外から来て働く人=第11-1表の年齢 × 第16-1表の職業)が作って"
               "いない。周辺(男女 × 年齢)は第11-1表と同じ母集団=構築に近い。舞台と区全体の形の違いを含む")
    js = []
    for si in range(2):  # 逐次: 年齢の行ごとの職業の分布の JSD(34)
        for ai in range(17):
            if sim[si, ai].sum() >= 30 and tgt[si, ai].sum() > 0:
                js.append(WC.F.jsd(sim[si, ai], tgt[si, ai]))
    row["occupation_within_age_jsd"] = {"rows": len(js), "mean": round(float(np.mean(js)), 6) if js else None,
                                        "max": round(float(np.max(js)), 6) if js else None}
    out.append(row)
    # ---- 職業 × 産業(舞台で働く人・第16-1表=外から来て働く人の構築)
    ind = np.array([A.INDUSTRY_MAJORS.index(x) if x in A.INDUSTRY_MAJORS else -1 for x in
                    np.unique(np.asarray(people["industry_major"], dtype=object).astype(str)).tolist()],
                   dtype=np.int64)[np.unique(np.asarray(people["industry_major"], dtype=object).astype(str),
                                             return_inverse=True)[1]]
    w2 = works & (occ >= 0) & (ind >= 0)
    sim = np.zeros((20, 12))
    np.add.at(sim, (ind[w2], occ[w2]), 1.0)
    out.append(_row("舞台で働く人の産業 20 × 職業 12", WC.BASIS_BUILD, "国勢調査 2020 従業地 第16-1表(従業地=渋谷区)", sim,
                    np.asarray(tables3.commuter_occupation).sum(axis=0),
                    [f"{i}|{o}" for i in A.INDUSTRY_MAJORS for o in A.OCCUPATION_MAJORS]))
    # ---- 世帯(人員 7・家族類型 6=舞台の目標・家族類型 16 × 人員 7=区の第10表=構築)
    size = np.clip(np.asarray(households["size"], dtype=np.int64), 1, 7) - 1
    grp = np.asarray(households["family_group"], dtype=object).astype(str)
    gen = grp != "institution"
    sim = np.bincount(size[gen], minlength=7).astype(float)
    out.append(_row("一般世帯の人員 7", WC.BASIS_BUILD, "国勢調査 2020 小地域 第5-2表 × 2025(舞台の目標)", sim,
                    np.asarray(tg.hh_size).sum(axis=0), [f"{k + 1}{'+' if k == 6 else ''}" for k in range(7)]))
    gi = np.array([T.GROUPS.index(x) if x in T.GROUPS else -1 for x in np.unique(grp).tolist()],
                  dtype=np.int64)[np.unique(grp, return_inverse=True)[1]]
    sim = np.bincount(gi[gi >= 0], minlength=6).astype(float)
    out.append(_row("一般世帯の家族類型 6", WC.BASIS_BUILD, "国勢調査 2020 小地域 第6-1表 × 2025(舞台の目標)", sim,
                    np.asarray(tg.hh_group).sum(axis=0), list(T.GROUPS)))
    ft = np.asarray(households["family_type"], dtype=object).astype(str)
    ti = np.array([T.FAMILY_TYPES.index(x) if x in T.FAMILY_TYPES else -1 for x in np.unique(ft).tolist()],
                  dtype=np.int64)[np.unique(ft, return_inverse=True)[1]]
    okf = (ti >= 0) & gen
    sim = np.zeros((16, 7))
    np.add.at(sim, (ti[okf], size[okf]), 1.0)
    out.append(_row("一般世帯の家族類型 16 × 人員 7", WC.BASIS_BUILD, "国勢調査 2025 第10表【不詳補完値】(区全体の形)", sim,
                    np.asarray(ward.hh_type_size), [f"{t}|{k + 1}" for t in T.FAMILY_TYPES for k in range(7)],
                    "舞台(駅の周り)と区全体の形の違いを含む"))
    # ---- 夫婦のいる世帯の夫の年齢 × 子の数・最年少の子の年齢(2025 第15-1表=構築に使っていない区分)
    cc = couple_children(people)
    h_lab = sorted({k[0] for k in b15.table if k[0][:2].isdigit() and k[0][:2] != "00"})
    c_lab = ("1_子供なし", "21_子供が1人", "22_子供が2人", "23_子供が3人", "24_子供が4人以上")
    j0 = b15.items.index("0_総数")
    tgt = np.zeros((len(h_lab), 5))
    for hi, hl in enumerate(h_lab):  # 逐次: 夫の年齢 × 子の数(≤ 60)
        for ci_, cl in enumerate(c_lab):
            v = b15.table.get((hl, cl, "0_総数", "0_総数"))
            tgt[hi, ci_] = 0.0 if v is None else float(np.nan_to_num(v[j0]))
    h_lo = np.array([int(x.split("_", 1)[1][:2]) for x in h_lab])
    hcls = np.clip(np.searchsorted(h_lo, cc["husband_age"], side="right") - 1, 0, len(h_lab) - 1)
    kch = np.clip(cc["children"], 0, 4)
    m = cc["husband_age"] >= h_lo[0]
    sim = np.zeros((len(h_lab), 5))
    np.add.at(sim, (hcls[m], kch[m]), 1.0)
    row = _row("夫婦のいる世帯の夫の年齢 × 子の数", WC.BASIS_NOT_BUILD,
               "国勢調査 2025 第15-1表(夫の年齢 × 子供の有無・数=区全体)", sim, tgt,
               [f"{hl.split('_', 1)[1]}|{cl.split('_', 1)[1]}" for hl in h_lab for cl in c_lab],
               "W21 の夫婦=世帯主と配偶者だけ(親の夫婦・子の夫婦は数えない)・子=続き柄が子。子の数は世帯の型 × 人員(構築)から"
               "決まるが、夫の年齢との結合は作っていない")
    out.append(row)
    y_lab = sorted({k[2] for k in b15.table if k[2][:1].isdigit() and k[2] != "0_総数"})
    tgt = np.array([float(np.nan_to_num(b15.table.get(("00_総数", "2_子供あり", yl, "0_総数"), np.zeros(len(b15.items)))[j0]))
                    for yl in y_lab])  # 逐次: 年齢の階級(8)
    edges = np.array([0, 1, 3, 6, 9, 12, 15, 18])
    yy = cc["youngest"][cc["youngest"] >= 0]
    sim = np.bincount(np.clip(np.searchsorted(edges, yy, side="right") - 1, 0, 7), minlength=8).astype(float)
    out.append(_row("夫婦のいる世帯の最年少の子の年齢 8", WC.BASIS_NOT_BUILD,
                    "国勢調査 2025 第15-1表(最年少の子供の年齢=区全体)", sim, tgt, [y.split("_", 1)[1] for y in y_lab],
                    "子の年齢は第13-1表の続き柄 × 年齢を親の年齢の窓で切った(構築)=最年少の子の分布は作っていない"))
    # ---- 席の地位 5 区分(第6-2表=構築)
    st = np.asarray(people["emp_status"], dtype=object).astype(str)
    seated = np.asarray(people["org_index"], dtype=np.int64) >= 0
    sim = np.zeros(5)
    for s_, c_ in WC.CENSUS_TO_ECEN5.items():  # 逐次: 地位 8
        sim[c_] += float((seated & (st == s_)).sum())
    col = {lab: items62.index(f"{lab}|従業者数_男女計") for lab in
           ("1_個人業主", "2_無給の家族従業者", "3_有給役員", "41_無期雇用者", "42_有期雇用者", "5_臨時雇用者")}
    majors = sorted(set(WC.ECEN_MAJOR_OF_KEY.values()))
    tgt = np.zeros(5)
    for r in rows62:  # 逐次: 表の行の数
        if str(r[2]) == "2" and str(r[3]) in majors:
            v = r[-1]
            tgt += [v[col["1_個人業主"]] or 0, v[col["2_無給の家族従業者"]] or 0, v[col["3_有給役員"]] or 0,
                    v[col["41_無期雇用者"]] or 0, (v[col["42_有期雇用者"]] or 0) + (v[col["5_臨時雇用者"]] or 0)]
    out.append(_row("席に所属した人の地位 5 区分", WC.BASIS_BUILD, "経済センサス 2021 第6-2表(渋谷区・W6 にある業種)", sim, tgt,
                    list(WC.ECEN_STATUS5), "国勢調査の地位(人)と経済センサスの地位(席)は区分が対応しない"))
    # ---- 国籍(住民の外国人)と日本語の程度
    nat = np.asarray(nationality, dtype=object).astype(str)
    fo = (nat != "") & (nat != A.JAPAN)
    names3 = sorted(juki_t3, key=lambda k: (-juki_t3[k], k))
    pos3 = {k: i for i, k in enumerate(names3)}
    sim = np.bincount([pos3.get(x, 0) for x in nat[fo].tolist()], minlength=len(names3)).astype(float) if fo.any() \
        else np.zeros(len(names3))
    out.append(_row("住民の外国人の国籍", WC.BASIS_BUILD, "東京都 外国人人口 第3表(2026-01-01・渋谷区)", sim,
                    np.array([juki_t3[k] for k in names3]), names3))
    top1 = [k for k in juki_t1 if k != "その他"]
    lab1 = top1 + ["その他"]
    s1 = np.array([float((nat[fo] == k).sum()) for k in top1] + [float((fo & ~np.isin(nat, top1)).sum())])
    t1 = np.array([juki_t1[k] for k in top1] + [juki_t1.get("その他", 0.0)])
    out.append(_row("住民の外国人の国籍(上位 10+その他)", WC.BASIS_NOT_BUILD, "東京都 外国人人口 第1表(2026-07-01=別の時点)",
                    s1, t1, lab1, "国籍を引いた表(2026-01-01)の半年後=独立は弱い"))
    jl = np.asarray(japanese_level, dtype=np.int64)
    sim = np.bincount(jl[jl >= 0], minlength=6).astype(float)
    rows_ = np.where(np.isin(nat, list(A.JAPANESE_LEVEL_TABLE)), nat, "その他")
    adult = fo & (np.asarray(people["age"], dtype=np.int64) >= A.JAPANESE_LEVEL_MIN_AGE)
    tgt = np.zeros(6)
    for rname in np.unique(rows_[adult]).tolist():  # 逐次: 国籍の行(≤ 11)
        tgt += float((adult & (rows_ == rname)).sum()) * np.asarray(A.JAPANESE_LEVEL_TABLE[rname]) / 100.0
    out.append(_row("外国籍の 18 歳以上の日本語の会話の程度 6 段", WC.BASIS_BUILD,
                    "在留外国人に対する基礎調査 令和 6 年度(国籍別=R-110 §3-2 の引)× W21 の国籍の構成", sim, tgt,
                    list(A.JAPANESE_LEVELS)))
    return out


def double_rows(people: Mapping[str, Any], rights: Mapping[str, Any], org_table: Mapping[str, Any],
                keep: Mapping[str, Any]) -> dict[str, Any]:
    """(b) 二重の数(合否なし)。``keep`` は ``w21_port10.w16_keep_table`` の返り値。"""
    pid = np.asarray(people["person_id"], dtype=np.int64)
    kind = np.asarray(people["kind"], dtype=object).astype(str)
    com = kind == "commuter"
    hk = np.asarray(rights["holder_kind"], dtype=object).astype(str)
    ok_ = np.asarray(rights["object_kind"], dtype=object).astype(str)
    kd = np.asarray(rights["kind"], dtype=object).astype(str)
    emp = (hk == "agent") & (ok_ == "org") & (kd == "employ")
    holders = np.asarray(rights["holder_id"], dtype=np.int64)[emp]
    _u, c = np.unique(holders, return_counts=True)
    duty = np.asarray(people["duty_role"], dtype=object).astype(str)
    seated = np.asarray(people["org_index"], dtype=np.int64) >= 0
    no_seat_words = ("駅員", "電車運転士", "車掌", "警察官", "消防士")
    seats = np.asarray(org_table["seats"], dtype=np.int64)
    filled = np.asarray(org_table["filled"], dtype=np.int64)
    return {
        "person_id_duplicates": int(pid.size - np.unique(pid).size),
        "residents_and_commuters_same_id": int(np.intersect1d(pid[com], pid[~com]).size),
        "commuters_with_stage_home": int((com & ((np.asarray(people["home_cell"], dtype=np.int64) >= 0)
                                                | (np.asarray(people["household_id"], dtype=np.int64) >= 0))).sum()),
        "commuters_from_ward_ring": int((com & (np.asarray(people["origin_muni"], dtype=object).astype(str)
                                                == S.WARD_CODE)).sum()),
        "note_ring": "輪(渋谷区の残りの町丁目)から通う体は段 7 の輪の層 196,184 の中にもいる=層の表の重なり(宣言・体は 1 つ)",
        "people_with_two_or_more_employ_rows": int((c > 1).sum()),
        "orgs_over_capacity": int((filled > seats).sum()),
        "duty_seated": WC.counts_by(duty[(duty != "") & seated]),
        "duty_not_seated": WC.counts_by(duty[(duty != "") & ~seated]),
        "no_seat_rule_but_seated": int((np.isin(duty, no_seat_words) & seated).sum()),
        "w16_inventory": {"w16_total": keep["w16_total"], "rows_removed_stage10": keep["rows_removed_stage10"],
                          "rows_kept": keep["rows_kept"],
                          "w21_duty_double_with_kept_transport": keep["w21_duty_double_with_kept_transport"]},
    }


def uniqueness(people: Mapping[str, Any], households: Mapping[str, Any], places: Mapping[str, Any],
               long_group: np.ndarray, short_group: np.ndarray) -> dict[str, Any]:
    """(c) 属性の組の重複と、文まで同じ(区別できない)組。組=年齢・性別・世帯(家族類型の区分 × 人員・外から来る人は空)・
    職業・勤め先(組織・無ければ場所の語とセル)・家(住民=家のセル・外から来る人=常住地)・なじみの場所の順位 1〜3。"""
    pid = np.asarray(people["person_id"], dtype=np.int64)
    n = pid.size
    kind = np.asarray(people["kind"], dtype=object).astype(str)
    hid = np.asarray(people["household_id"], dtype=np.int64)
    h_id = np.asarray(households["household_id"], dtype=np.int64)
    hpos = np.full(int(h_id.max()) + 1 if h_id.size else 0, -1, dtype=np.int64)
    hpos[h_id] = np.arange(h_id.size)
    hr = np.where(hid >= 0, hpos[np.clip(hid, 0, max(hpos.size - 1, 0))], -1)
    hform = np.where(hr >= 0, np.char.add(np.char.add(np.asarray(households["family_group"], dtype=object).astype(str)[
        np.clip(hr, 0, None)], "|"), np.asarray(households["size"], dtype=np.int64)[np.clip(hr, 0, None)].astype(str)), "")
    org = np.asarray(people["org_code"], dtype=object).astype(str)
    work = np.where(org != "", org, np.char.add(np.char.add(np.asarray(people["workplace_area"], dtype=object).astype(str),
                                                            "|"), np.asarray(people["work_cell"]).astype(str)))
    home = np.where(kind == "resident", np.asarray(people["home_cell"]).astype(str),
                    np.asarray(people["origin_muni"], dtype=object).astype(str))
    pp = np.asarray(places["person_id"], dtype=np.int64)
    rk = np.asarray(places["rank"], dtype=np.int64)
    pk = np.asarray(places["place_kind"], dtype=object).astype(str)
    pi = np.asarray(places["poi_index"], dtype=np.int64)
    pos = np.full(int(pid.max()) + 1 if n else 0, -1, dtype=np.int64)
    pos[pid] = np.arange(n)
    ranks = [np.full(n, "", dtype=object) for _ in range(3)]
    for r in range(3):  # 逐次: 順位 1〜3
        m = rk == r + 1
        ranks[r][pos[pp[m]]] = np.char.add(np.char.add(pk[m], ":"), pi[m].astype(str))
    cols = [np.asarray(people["age"]).astype(str), np.asarray(people["sex"]).astype(str), hform,
            np.asarray(people["occupation_major"], dtype=object).astype(str), work, home, *ranks]
    key = cols[0].astype(object)
    for c in cols[1:]:  # 逐次: 属性の数(9)
        key = key + "|" + np.asarray(c).astype(object)
    out = WC.tuple_duplicates(key, long_group)
    out["short_text"] = {k: v for k, v in WC.tuple_duplicates(key, short_group).items()
                         if k.startswith("indistinguishable")}
    # なじみの場所を除いた組(感度の見方=場所の当てはめが別人にしている分)
    key6 = cols[0].astype(object)
    for c in cols[1:6]:  # 逐次: 属性の数(6)
        key6 = key6 + "|" + np.asarray(c).astype(object)
    out["without_familiar_places"] = WC.tuple_duplicates(key6, long_group)
    out["columns"] = ["age", "sex", "household(family_group|size)", "occupation_major", "workplace(org|area+cell)",
                      "home(cell|origin_muni)", "familiar_rank1", "familiar_rank2", "familiar_rank3"]
    out["note"] = ("区別できない=属性の組が同じで人物の文(長い版)まで同じ。外から来て働く人は世帯と家のセルを持たない(常住地の"
                   "市区町村だけ)=組が重なりやすい")
    return out


def _attrs_for_diversity(age: np.ndarray, sex: np.ndarray, industry: np.ndarray, hh_size: np.ndarray,
                         home_cell: np.ndarray, work_cell: np.ndarray) -> dict[str, np.ndarray]:
    return {"age5": np.minimum(np.asarray(age, dtype=np.int64) // 5, 18), "sex": np.asarray(sex, dtype=np.int64),
            "industry_key": np.asarray(industry, dtype=object).astype(str), "hh_size": np.asarray(hh_size, dtype=np.int64),
            "home_cell": np.asarray(home_cell, dtype=np.int64), "work_cell": np.asarray(work_cell, dtype=np.int64)}


def _hh_size(hid: np.ndarray) -> np.ndarray:
    h = np.asarray(hid, dtype=np.int64)
    ok = h >= 0
    if not ok.any():
        return np.full(h.size, -1, dtype=np.int64)
    c = np.bincount(h[ok], minlength=int(h.max()) + 1)
    return np.where(ok, c[np.clip(h, 0, None)], -1)


def _codes(cols: Mapping[str, np.ndarray]) -> np.ndarray:
    return np.stack([np.unique(np.asarray(v).astype(str), return_inverse=True)[1].reshape(-1) for v in cols.values()],
                    axis=1)


def diversity_vs_w16(people: Mapping[str, Any], w16: Mapping[str, Any], *, seed: int | str) -> dict[str, Any]:
    """(d) 住人の似通い(D-68): 属性(年齢 5 歳・男女・産業の語・世帯の人数・家のセル・勤め先のセル)の多様性を、W21 と
    W16 の在庫(種別 0・2・3=W21 が置き換える層)で並べる。行動のばらつき(DM6)は欄だけ。"""
    w21 = _attrs_for_diversity(people["age"], people["sex"], people["industry_key"], _hh_size(people["household_id"]),
                               people["home_cell"], people["work_cell"])
    k16 = np.asarray(w16["kind"], dtype=np.int64)
    sel = np.isin(k16, [0, 2, 3])
    w16a = _attrs_for_diversity(np.asarray(w16["age"])[sel], np.asarray(w16["sex"])[sel],
                                np.where(np.equal(np.asarray(w16["industry_key"], dtype=object)[sel], None), "",
                                         np.asarray(w16["industry_key"], dtype=object)[sel]),
                                _hh_size(np.asarray(w16["household_id"], dtype=np.int64))[sel],
                                np.asarray(w16["home_cell"])[sel], np.asarray(w16["work_cell"])[sel])
    return {
        "attributes": list(w21),
        "w21": {**WC.diversity(w21), "pairs": WC.pair_distance(_codes(w21), PAIRS, seed, "w21c.check.pairs.w21")},
        "w16_inventory": {**WC.diversity(w16a), "pairs": WC.pair_distance(_codes(w16a), PAIRS, seed,
                                                                         "w21c.check.pairs.w16"),
                          "rows": int(sel.sum()), "synthetic": int(np.asarray(w16["synthetic"], dtype=bool)[sel].sum())},
        "dm6_behavior_variance_ratio": None,
        "note": ("属性の多様性だけ(合否なし)。行動のばらつき(DM6 のばらつきの比)は GPU の後(段 11)=欄だけ。W16 の在庫は住民・"
                 "区内で働く住民・外から来て働く人の層(複製を含む)")}
