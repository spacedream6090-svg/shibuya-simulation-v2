"""W21 段 3「属性」: 材料の表から ``attr_fns.AttrTables`` を組み、住民に「属性から作る関数」をかける。

正: 答申 R-116 §1-3(第9〜12・14・16-2・16-3・18 表・就業状態等 第3-1・5-1・10-1 表・従業地 第8・11-1・15-1・16-1 表)・
§3-3(関数の形)・§5(W20 に渡す 5 属性)。

- 住民の仕事(労働力状態・従業上の地位・産業大分類と ``industry_key``・職業大分類・従業地)・学校(在学の種類・通学地)・
  居住期間を引く。周辺は町丁目 × 男女の小地域の表(「不詳」は町丁目 × 男女の既知の比=割合だけ使うので割り振りと同じ)。
- 外から来る人(通勤)の属性は同じ関数で従業地の表から引く(``kind="commuter"``)。本段では住民だけに書き、通勤の人には
  点検(``w21_checks``)で数えるだけ。
- 入力に無い属性は空欄(``""``)。公務(S)・農林漁業・鉱業・電気ガス・分類不能は ``industry_key`` に語が無い=空欄。

逐次ループ宣言(P4): 表の分類の数ぶん(産業 20・職業 12・年齢 17・地位 8)。体の数に比例するループは無い。
"""

from __future__ import annotations

import json
import re
from types import MappingProxyType
from typing import Final, Mapping

import numpy as np

from . import attr_fns as A
from . import w21_sources as S
from . import w21_tables as T

__all__ = ["build_tables", "apply_attrs", "VOCAB", "UNKNOWN_FIELDS"]

_SEX = ("1_男", "2_女")
_MAR4 = ("1_未婚", "2_有配偶", "3_死別", "4_離別")
_STATUS8 = ("11_", "12_", "13_", "2_", "3_", "4_", "5_", "6_")
_IND = re.compile(r"^([A-T])_")
_OCC = re.compile(r"^([A-L])_")
_AGE17 = re.compile(r"^(0[1-9]|1[0-7])_")

#: 段 3 の列の語(番号 → 語・−1 は "")。
VOCAB: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType({
    "labour_status": A.LABOUR,
    "emp_status": A.EMP_STATUS,
    "industry_major": A.INDUSTRY_MAJORS,
    "occupation_major": A.OCCUPATION_MAJORS,
    "workplace_kind": A.WORKPLACE,
    "school_kind": A.SCHOOL,
    "school_place": A.SCHOOL_PLACE,
    "residence_period": A.RESIDENCE,
})
#: 町丁目の「不詳」を割り振った(=割合だけ使った)表と列。
UNKNOWN_FIELDS: Final[tuple[str, ...]] = ("labour_status", "emp_status", "workplace_kind", "school", "residence_period")


def _labels(keys, pos: int, pat: re.Pattern) -> list[str]:
    return sorted({k[pos] for k in keys if pat.match(k[pos])})


def _items(d: S.Derived, pat: re.Pattern) -> list[int]:
    return [j for j, it in enumerate(d.items) if pat.match(it)]


def _status_label(d: S.Derived, dim_pos: int, prefix: str) -> str:
    return next(k[dim_pos] for k in d.table if k[dim_pos].startswith(prefix))


def build_tables(guard: S.W21Guard, keys80: tuple[str, ...], stage_idx: np.ndarray,
                 coverage: np.ndarray, r_pop: float) -> tuple[A.AttrTables, dict[str, float]]:
    """材料の表 → ``AttrTables``(凍結)と、町丁目の「不詳」を割り振った人数(2020 の町丁目の不詳 × 被覆率)。"""
    # --- 就業率(第3-1表 ÷ 2020 の遡及の補完値の一般世帯人員)
    c03 = S.read_derived(guard, "c20_c03")
    ages17 = _labels(c03.table, 2, _AGE17)
    emp = np.zeros((2, 17, 4))
    status = np.zeros((2, 4, 17, 8))
    st_items = [next(j for j, it in enumerate(c03.items) if it.startswith(p)) for p in _STATUS8]
    for si, sx in enumerate(_SEX):  # 逐次: 男女 2 × 配偶 4 × 年齢 17
        for mi, mr in enumerate(_MAR4):
            for ai, ag in enumerate(ages17):
                v = c03.table.get((sx, mr, ag, "0_総数"))
                if v is None:
                    continue
                emp[si, ai, mi] = np.nan_to_num(v[0])
                status[si, mi, ai] = np.nan_to_num(v[st_items])
    b13 = S.read_derived_merged(guard, ("c20w_b13_m", "c20w_b13_f"))
    a21 = sorted({k[3] for k in b13.table if re.match(r"^(0[1-9]|1\d|2[01])_", k[3])})
    pop = np.zeros((2, 17, 4))
    for si, sx in enumerate(_SEX):
        for mi, mr in enumerate(_MAR4):
            for ai in range(3, 21):
                v = b13.table.get((mr, sx, "0_総数", a21[ai]))
                pop[si, min(ai - 3, 16), mi] += 0.0 if v is None else float(np.nan_to_num(v[b13.item("00_総数")]))
    emp_rate = np.divide(emp, pop, out=np.full_like(emp, 0.5), where=pop > 0)

    # --- 産業(第5-1表=男女 × 産業 × 地位 → 年齢の列)
    c05 = S.read_derived(guard, "c20_c05")
    inds = _labels(c05.table, 2, _IND)
    a_items = _items(c05, _AGE17)
    industry = np.zeros((2, 17, 8, 20))
    for si, sx in enumerate(_SEX):
        for ii, ind in enumerate(inds):
            for ti, pre in enumerate(_STATUS8):
                lab = next((k for k in c05.table if k[0] == sx and k[2] == ind and k[3].startswith(pre)), None)
                if lab is not None:
                    industry[si, :, ti, ii] = np.nan_to_num(c05.table[lab][a_items])

    # --- 職業(第10-1表=男女 × 年齢 × 産業 → 職業の列)
    c10 = S.read_derived(guard, "c20_c10")
    o_items = _items(c10, _OCC)
    occupation = np.zeros((2, 17, 20, 12))
    for si, sx in enumerate(_SEX):
        for ai, ag in enumerate(_labels(c10.table, 1, _AGE17)):
            for ii, ind in enumerate(inds):
                lab = next((k for k in c10.table if k[0] == sx and k[1] == ag and k[3] == ind), None)
                if lab is not None:
                    occupation[si, ai, ii] = np.nan_to_num(c10.table[lab][o_items])

    # --- 従業地(第8表・常住地による/従業地による)
    e08 = S.read_derived(guard, "c20_e08")
    j_home, j_in = e08.item(_first(e08.items, "0021_")), e08.item(_first(e08.items, "0022_"))
    j_ow, j_ot, j_op = (e08.item(_first(e08.items, p)) for p in ("0031_", "0032_", "0033_"))
    j_work = e08.item(_first(e08.items, "1_従業地"))
    workplace = np.zeros((5, 20, 4))
    cm_status = np.zeros((20, 5))
    for ii, ind in enumerate(inds):  # 逐次: 産業 20
        rows = {k[1]: v for k, v in e08.table.items() if k[3] == ind}
        tot = rows.get(_first(rows, "0_"))
        emp_ = rows.get(_first(rows, "1_"))
        parts = [rows.get(_first(rows, p)) for p in ("11_", "12_", "13_")]
        if tot is None or emp_ is None or any(p is None for p in parts):
            continue
        other_emp = np.clip(emp_ - sum(parts), 0.0, None)
        non_emp = np.clip(tot - emp_, 0.0, None)
        for gi, v in enumerate([*parts, other_emp, non_emp]):
            v = np.nan_to_num(v)
            workplace[gi, ii] = [v[j_home], v[j_in], v[j_ow] + v[j_ot], v[j_op]]
            cm_status[ii, gi] = v[j_work]

    # --- 従業地が渋谷区の人(第11-1・16-1 表)
    e11 = S.read_derived(guard, "c20_e11")
    i_items = _items(e11, _IND)
    cm_ind = np.zeros((2, 17, 20))
    for si, sx in enumerate(_SEX):
        for ai, ag in enumerate(_labels(e11.table, 1, _AGE17)):
            v = e11.table.get((sx, ag))
            if v is not None:
                cm_ind[si, ai] = np.nan_to_num(v[i_items])
    e16 = S.read_derived(guard, "c20_e16")
    e16_o = _items(e16, _OCC)
    cm_occ = np.zeros((2, 20, 12))
    for si, sx in enumerate(_SEX):
        for ii, ind in enumerate(inds):
            lab = next((k for k in e16.table if k[0] == sx and k[2] == ind), None)
            if lab is not None:
                cm_occ[si, ii] = np.nan_to_num(e16.table[lab][e16_o])

    # --- 外から来る通学者(第1-3表・通学地=渋谷区・「うち他市区町村に常住」)〔検収 L6〕
    e13 = S.read_derived(guard, "c20_e01_03")
    j_in = e13.item(_first(e13.items, "101_"))
    cls = sorted({k[1] for k in e13.table if re.match(r"^(0[1-9]|1[0-8])_", k[1])})
    st_in = np.zeros((2, len(cls)))
    st_ages = np.zeros((len(cls), 2), dtype=np.int64)
    for ci, lab in enumerate(cls):  # 逐次: 年齢の階級(18)
        m2 = re.search(r"(\d+)～(\d+)歳", lab)
        m1 = re.search(r"(\d+)歳以上", lab)
        st_ages[ci] = (int(m2.group(1)), int(m2.group(2))) if m2 else ((int(m1.group(1)), T.MAX_AGE) if m1
                                                                        else (6, 14))  # 15 歳未満=6〜14 歳
        for si, sx in enumerate(_SEX):
            v = e13.table.get((sx, lab))
            st_in[si, ci] = 0.0 if v is None else float(np.nan_to_num(v[j_in]))

    # --- 産業 N の分け方(経済センサスの駅周辺 13 町丁目の中分類)
    ec = json.loads(guard.source_bytes("ecen21_area").decode("utf-8"))["sim_buckets"]
    n_split = (float(ec["LS"]["employees"]), float(ec["AM"]["employees"]))

    # --- 町丁目 × 男女の周辺
    shares, unknown = _chome_shares(guard, keys80, stage_idx, coverage, r_pop)
    md5 = MappingProxyType(dict(sorted(guard.opened.items())))
    t = A.AttrTables(
        emp_rate=emp_rate, status_prior=status, industry_prior=industry, occupation_prior=occupation,
        workplace_prior=workplace, commuter_industry=cm_ind, commuter_occupation=cm_occ, commuter_status=cm_status,
        student_in=st_in, student_in_ages=st_ages, n_split=n_split, md5=md5, **shares,
    )
    return t.freeze(), unknown


def _first(items, prefix: str) -> str:
    return next(x for x in items if str(x).startswith(prefix))


def _chome_shares(guard: S.W21Guard, keys80: tuple[str, ...], stage_idx: np.ndarray, coverage: np.ndarray,
                  r_pop: float) -> tuple[dict[str, np.ndarray], dict[str, float]]:
    """町丁目(舞台)× 男女の周辺の割合((C × 2, K))と、割り振った「不詳」の人数(2020 の町丁目の不詳 × 被覆率)。"""
    C = stage_idx.size
    sexes = ("男", "女")

    def stack(sa: S.SmallArea, labels) -> np.ndarray:
        out = np.zeros((C * 2, len(labels)))
        for si, sx in enumerate(sexes):
            for k, lab in enumerate(labels):
                cols = lab if isinstance(lab, tuple) else (lab,)
                out[si::2, k] = sum(np.nan_to_num(sa.col(c, sx))[stage_idx] for c in cols)
        return out

    def unknown(sa: S.SmallArea, label: str) -> float:
        v = np.nan_to_num(sa.col(label))[stage_idx]
        return float((v * coverage).sum())

    t09 = S.read_small_area(guard, "sa_t09", keys80)
    t10 = S.read_small_area(guard, "sa_t10", keys80)
    lf = stack(t09, ["労働力人口", "非労働力人口"])
    empd = stack(t10, ["総数"])[:, 0]
    labour = np.stack([empd, np.clip(lf[:, 0] - empd, 0.0, None), lf[:, 1]], axis=1)
    status = stack(t10, ["雇用者（役員を含む）", "自営業主（家庭内職者を含む）", "家族従業者"])
    t11 = S.read_small_area(guard, "sa_t11", keys80)
    ind = stack(t11, [lab for lab in t11.labels if _IND.match(lab)])
    t12 = S.read_small_area(guard, "sa_t12", keys80)
    occ = stack(t12, [lab for lab in t12.labels if _OCC.match(lab)])
    t162 = S.read_small_area(guard, "sa_t16_2", keys80)
    work = stack(t162, ["自宅で従業", "自宅外の自市区町村で従業・通学", ("自市内他区で従業・通学", "県内他市町村で従業・通学"),
                        "他県で従業・通学"])
    t14 = S.read_small_area(guard, "sa_t14", keys80)
    enrolled = [lab for lab in t14.labels if lab.startswith("（在学者）") and "不詳" not in lab]
    pre = [lab for lab in t14.labels if lab.startswith("（未就学者）") and "不詳" not in lab]
    school = stack(t14, enrolled + pre)
    enr_all = stack(t14, ["在学者", "未就学者"])
    school = _fill_family(school, enr_all, len(enrolled))
    t18 = S.read_small_area(guard, "sa_t18", keys80)
    res_labels = [lab for lab in t18.labels if lab not in ("総数", "居住期間「不詳」")]
    residence = stack(t18, res_labels)
    tot = stack(t18, ["総数"])[:, 0]
    none = np.clip(tot - enr_all.sum(axis=1), 0.0, None)
    school = np.concatenate([school, none[:, None]], axis=1)
    t163 = S.read_small_area(guard, "sa_t16_3", keys80)
    splace = stack(t163, ["自宅外の自市区町村で従業・通学", ("自市内他区で従業・通学", "県内他市町村で従業・通学"),
                          "他県で従業・通学"])
    if len(enrolled) != 6 or len(pre) != 4 or len(res_labels) != 6:
        raise ValueError(f"第14・18表の区分の数が違う(在学 {len(enrolled)}・未就学 {len(pre)}・居住 {len(res_labels)})")
    unk = {
        "labour_status": unknown(t09, "労働力状態「不詳」"),
        "emp_status": unknown(t10, "従業上の地位「不詳」"),
        "industry_major(分類不能 T は区分のまま)": 0.0,
        "workplace_kind": unknown(t162, "従業・通学市区町村「不詳・外国」") + unknown(t162, "従業地・通学地「不詳」"),
        "school": unknown(t14, "（在学者）不詳") + unknown(t14, "（未就学者）不詳"),
        "school_place": unknown(t163, "従業・通学市区町村「不詳・外国」") + unknown(t163, "従業地・通学地「不詳」"),
        "residence_period": unknown(t18, "居住期間「不詳」"),
    }
    return {
        "chome_labour": labour, "chome_status": status, "chome_industry": ind, "chome_occupation": occ,
        "chome_workplace": work, "chome_school": school, "chome_school_place": splace,
        "chome_residence": residence,
    }, unk


def _fill_family(parts: np.ndarray, totals: np.ndarray, n_first: int) -> np.ndarray:
    """在学者と未就学者の「不詳」を、それぞれの中の既知の比で割り振る(総数=在学者・未就学者)。"""
    out = parts.copy()
    for sl, ti in ((slice(0, n_first), 0), (slice(n_first, parts.shape[1]), 1)):
        s = out[:, sl].sum(axis=1, keepdims=True)
        out[:, sl] = np.divide(out[:, sl], s, out=np.zeros_like(out[:, sl]), where=s > 0) * totals[:, ti:ti + 1]
    return out


def apply_attrs(persons: dict[str, np.ndarray], tables: A.AttrTables, seed: int | str,
                counters: np.ndarray) -> dict[str, np.ndarray]:
    """住民の列(``kind``・``sex``・``age``・``marital``・``chome``・``persona_kind``・``role``)に段 3 の関数をかけ、
    数の列(番号)と語の列を足して返す。``counters`` は人ごとの鍵の語((n, 3)=町丁目の鍵・通し番号・世帯員の番号)。"""
    attrs = dict(persons)

    def key(name: str) -> A.AttrKey:
        return A.AttrKey(seed, f"w21.attr.{name}", counters)

    for name in ("labour_status", "emp_status", "industry_major", "industry_key", "occupation_major",
                 "workplace_kind", "employment_status", "school_kind", "school_place", "residence_period",
                 "w16_kind", "duty_role"):  # 逐次: 関数の数ぶん
        attrs[name] = A.call(name, attrs, tables, key(name))
    return attrs


def words(codes: np.ndarray, vocab: tuple[str, ...]) -> np.ndarray:
    """番号 → 語(−1 は "")。"""
    lut = np.array([*vocab, ""], dtype=object)
    c = np.asarray(codes, dtype=np.int64)
    return lut[np.where(c >= 0, c, len(vocab))]
