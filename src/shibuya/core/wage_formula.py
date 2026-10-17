"""core.wage_formula — 職業 × 性 × 年齢 × 雇用形態の賃金の式と表の読み解き(賃金構造基本統計調査 令和 7 年=R-107)。

正: ユーザー決定 2026-10-17(回答 10-13b §7 の 3)・決定 10-12 §4-11(EC2)・答申 R-107 §1-1・記録 pop41b §4・wage_occ。

4-1 段 5 の ``build.pop.w21_money.load_wage_tables`` の読み解きと ``build.pop.attr_fns._wage_quantile``・``_wage`` の式を
ここへ移した(式も演算の順も同じ=W21 の資産の sha は変わらない=二重に作らない)。実行時(``economy.wages``・2-1 の給料日)と
構築(``build.pop``)の両方が呼ぶ。**numpy と ``core.rng`` だけを読む**: build が economy の包みを読むと engine と llm まで
読まれる(4-1 段 8〜9 の ``test_persona_build_does_not_import_or_call_llm``)ので、層のいちばん下に置いた(検収の後の直し)。
世界の状態も、ファイルも、規則の表も読まない(読み口と最低賃金の床は ``economy.wages``)。

W16 の体の写像(:data:`OCCUPATION_OF_PERSONA_WORD`・:data:`FORM_OF_PERSONA_EMPLOYMENT`・**未リサーチ(expedient)**・つなぎの台帳
``DOC-wage_occ-*``・外す段 4-3=W21 への差し替え)・写せない体の平均・最低賃金の床の式(:func:`apply_floor`・床の値は呼び手が
規則の表から渡す)・月の時間の目安(:func:`month_hours`)も同じ場所。

乱数: 体ごとの分位 u は ``core.rng.philox_array``(用途名 :data:`WAGE_DOMAIN`=母集団の側・0 語目を空け 1 語目に体の鍵=
``k19_counter_array``・1 語だけ引く)。``build.pop.attr_fns.AttrKey.uniform`` と同じ引き方(試験が突き合わせる)。

逐次ループ宣言(P4): 表の行の数ぶん(読み解き)・写せない体の平均は職種 11 × 性 2 の数ぶん。体の数に比例するループは無い。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

import numpy as np

from shibuya.core.rng import k19_counter_array, philox_array, unit_float

__all__ = [
    "WAGE_OCCUPATIONS", "WAGE_AGE_EDGES", "WAGE_CLASS_FLOOR_YEN", "WAGE_TOP_FACTOR", "SEXES",
    "FORM_REGULAR", "FORM_NON_REGULAR", "FORM_PART_TIME", "WAGE_DOMAIN", 
    "WAGE_TABLE_FIELDS", "WageTables", "parse_wage_tables", "wage_quantile", "wage_values",
    "wage_uniform", "OCCUPATION_OF_PERSONA_WORD", "FORM_OF_PERSONA_EMPLOYMENT", "BASIS_OCCUPATION", "BASIS_AVERAGE",
    "BASIS_GIVEN", "BASIS_NAMES", "occupation_wages", "median_check", "month_hours",
    "apply_floor",
]

#: 職業大分類(国勢調査 A〜K)→ 賃金構造基本統計調査の職種(大分類)の名(同じ分類=日本標準職業分類)。L(分類不能)は無い。
WAGE_OCCUPATIONS: Final[tuple[str, ...]] = (
    "管理的職業従事者", "専門的・技術的職業従事者", "事務従事者", "販売従事者", "サービス職業従事者", "保安職業従事者",
    "農林漁業従事者", "生産工程従事者", "輸送・機械運転従事者", "建設・採掘従事者", "運搬・清掃・包装等従事者",
)
#: 賃金構造 第6表の年齢階級の下の端(～19・20-24 … 65-69・70～=12 階級)。
WAGE_AGE_EDGES: Final[np.ndarray] = np.array([0, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70], dtype=np.int64)
WAGE_AGE_EDGES.flags.writeable = False
#: 第18表の最も低い階級(～99.9 千円)の下の端と、最も高い階級(1,200 千円～)の上の端の倍率(自前・expedient=4-1 段 5 の宣言
#: ``EX-build.pop.w21_build_b-dc566aac``)。
WAGE_CLASS_FLOOR_YEN: Final[float] = 80_000.0
WAGE_TOP_FACTOR: Final[float] = 1.5
#: 性の語(番号 0=男・1=女=W16 の ``sex`` と同じ)。
SEXES: Final[tuple[str, str]] = ("男", "女")
#: 雇用形態(0=一般の正社員・正職員・1=一般の正社員・正職員以外・2=短時間労働者)。
FORM_REGULAR: Final[int] = 0
FORM_NON_REGULAR: Final[int] = 1
FORM_PART_TIME: Final[int] = 2
#: 体ごとの分位の乱数の用途名(母集団の側=``engine.run.POPULATION_RNG_DOMAINS``)。
WAGE_DOMAIN: Final[str] = "economy.wage"

_FW = str.maketrans("０１２３４５６７８９", "0123456789")


def _num(v: Any) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


# ------------------------------------------------------------------------------------------ 表の読み解き
def parse_wage_tables(rows9: Sequence[Sequence[Any]], rows6: Sequence[Sequence[Any]], items18: Sequence[str],
                      rows18: Sequence[Sequence[Any]], items2: Sequence[str],
                      rows2: Sequence[Sequence[Any]]) -> dict[str, np.ndarray]:
    """賃金構造 令和 7 年(第9・6・18 表と短時間 第2表の写しの行)→ 賃金の欄(企業規模計・円と時間)。

    4-1 段 5 の ``build.pop.w21_money.load_wage_tables`` の中身を移した(同じ式・同じ順)。返り値の鍵は
    :data:`WAGE_TABLE_FIELDS`(``build.pop.attr_fns.AttrTablesB`` の賃金の欄と同じ名)。
    """
    O = len(WAGE_OCCUPATIONS)
    occ_i = {o: i for i, o in enumerate(WAGE_OCCUPATIONS)}
    level = np.zeros((O, 2, 2))
    bonus = np.zeros((O, 2, 2))
    hours = np.zeros((O, 2, 2))
    allw = np.zeros((O, 2))
    forms = {"正社員・正職員計": 0, "正社員・正職員以外計": 1}
    for occ, sex, cat, v in rows9:  # 逐次: 表の行の数ぶん
        if occ not in occ_i or sex not in SEXES:
            continue
        o, s = occ_i[occ], SEXES.index(sex)
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

    nA = WAGE_AGE_EDGES.size
    wage_age = np.zeros((O, 2, nA))
    bonus_age = np.zeros((O, 2, nA))
    tot_w = np.zeros((O, 2))
    tot_b = np.zeros((O, 2))
    for sex, occ, age_lab, v in rows6:  # 逐次: 表の行の数ぶん
        if occ not in occ_i or sex not in SEXES:
            continue
        o, s = occ_i[occ], SEXES.index(sex)
        if age_lab == "計":
            tot_w[o, s], tot_b[o, s] = _num(v[5]), _num(v[6])
            continue
        m = re.search(r"(\d+)", age_lab.translate(_FW))
        lo = 0 if age_lab.startswith("～") else (int(m.group(1)) if m else 0)
        a = int(np.searchsorted(WAGE_AGE_EDGES, lo, side="right") - 1)
        wage_age[o, s, a], bonus_age[o, s, a] = _num(v[5]), _num(v[6])
    wage_age_ratio = np.where(wage_age > 0, np.divide(wage_age, tot_w[:, :, None], out=np.ones_like(wage_age),
                                                      where=tot_w[:, :, None] > 0), 1.0)
    bonus_age_ratio = np.where(bonus_age > 0, np.divide(bonus_age, tot_b[:, :, None], out=np.ones_like(bonus_age),
                                                        where=tot_b[:, :, None] > 0), 1.0)

    col = [list(items18).index(o) for o in WAGE_OCCUPATIONS]
    lo_l: list[float] = []
    hi_l: list[float] = []
    freq: dict[str, list[np.ndarray]] = {s: [] for s in SEXES}
    median = np.zeros((O, 2))
    for sex, lab, v in rows18:  # 逐次: 表の行の数ぶん
        if sex not in SEXES:
            continue
        vv = np.array([_num(v[j]) for j in col])
        if "中" in lab and "位" in lab and "数" in lab and "分位" not in lab:
            median[:, SEXES.index(sex)] = vv * 1000.0
            continue
        nums = [float(x) for x in re.findall(r"\d+\.\d+", lab)]
        if not nums or "分位" in lab or "係数" in lab:
            continue
        if sex == SEXES[0]:
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
    cls_freq = np.stack([np.stack(freq[s], axis=1) for s in SEXES], axis=1)  # (O, 2, K)

    it = list(items2)
    pt = {k: np.zeros((O, 2)) for k in ("hourly", "bonus", "hours_day", "days")}
    keys = {"hourly": "1時間当たり所定内給与額", "bonus": "年間賞与その他特別給与額", "hours_day": "1日当たり所定内実労働時間数",
            "days": "実労働日数"}
    for occ, v in rows2:  # 逐次: 表の行の数ぶん
        if occ not in occ_i:
            continue
        o = occ_i[occ]
        for s, sx in enumerate(SEXES):
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


#: 賃金の欄の名(:func:`parse_wage_tables` の鍵の順)。
WAGE_TABLE_FIELDS: Final[tuple[str, ...]] = (
    "wage_level", "wage_bonus", "wage_hours", "wage_all", "wage_age_ratio", "bonus_age_ratio", "wage_cls_lo",
    "wage_cls_hi", "wage_cls_freq", "wage_median", "pt_hourly", "pt_bonus", "pt_hours_day", "pt_days")


@dataclass(frozen=True)
class WageTables:
    """実行時の賃金の表(配列は書き込み禁止)。欄の名と形は ``build.pop.attr_fns.AttrTablesB`` の賃金の欄と同じ。

    ``md5`` は写しのファイル名 → md5(manifest に出す)。
    """

    wage_level: np.ndarray
    wage_bonus: np.ndarray
    wage_hours: np.ndarray
    wage_all: np.ndarray
    wage_age_ratio: np.ndarray
    bonus_age_ratio: np.ndarray
    wage_cls_lo: np.ndarray
    wage_cls_hi: np.ndarray
    wage_cls_freq: np.ndarray
    wage_median: np.ndarray
    pt_hourly: np.ndarray
    pt_bonus: np.ndarray
    pt_hours_day: np.ndarray
    pt_days: np.ndarray
    md5: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in WAGE_TABLE_FIELDS:
            a = np.array(getattr(self, name), dtype=np.float64, copy=True)
            a.setflags(write=False)
            object.__setattr__(self, name, a)
        object.__setattr__(self, "md5", MappingProxyType(dict(self.md5)))


# ------------------------------------------------------------------------------------------ 額の式
def wage_quantile(tables: Any, occ: np.ndarray, sex: np.ndarray, u: np.ndarray) -> np.ndarray:
    """第18表の所定内給与額の階級の度数(職種 × 男女)から分位 u の値[円/月](階級の中は一様=宣言)。"""
    f = tables.wage_cls_freq[occ, sex]  # (n, K)
    c = np.cumsum(f, axis=1)
    tot = c[:, -1]
    k = np.minimum((c < (u * tot)[:, None]).sum(axis=1), f.shape[1] - 1)
    prev = np.where(k > 0, c[np.arange(k.size), np.maximum(k - 1, 0)], 0.0)
    fk = f[np.arange(k.size), k]
    pos = np.divide(u * tot - prev, fk, out=np.full(k.size, 0.5), where=fk > 0)
    lo, hi = tables.wage_cls_lo[k], tables.wage_cls_hi[k]
    return np.where(tot > 0, lo + np.clip(pos, 0.0, 1.0) * (hi - lo), np.nan)


def wage_values(tables: Any, occ: np.ndarray, sex: np.ndarray, form: np.ndarray, ok: np.ndarray, age: np.ndarray,
                u: np.ndarray, *, unknown_age_ratio_one: bool = False) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(所定内給与[円/月], 時間あたり[円], 年の賃金[円])。対象外(``ok`` が偽)は −1。

    一般(正社員・正職員/以外): 第18表の階級の度数(職種 × 男女=雇用形態と年齢をまとめた形)の分位 u の値 × 年齢の比
    (第6表)× 雇用形態の比(第9表の形態 ÷ 常用労働者計)。年の賃金=12 × 月+賞与(第9表の形態 × 第6表の年齢の比)。
    短時間: 第2表の 1 時間あたり × 第18表の形(分位 u の値 ÷ 中位数)・月=時間あたり × 1 日の時間 × 日数・年=12 × 月+賞与。
    比をかけ合わせるのは独立の仮定(expedient=4-1 段 5 の宣言)。4-1 段 5 の ``attr_fns._wage`` の中身を移した(同じ式)。

    ``unknown_age_ratio_one``: 年齢が負(分からない)の行の年齢の比を 1(=計)にする(実行時の写せない体だけ。構築の呼び手は
    渡さない=今までどおり年齢の階級の端に寄せる)。
    """
    occ = np.asarray(occ, dtype=np.int64)
    sex = np.asarray(sex, dtype=np.int64)
    form = np.asarray(form, dtype=np.int64)
    ok = np.asarray(ok, dtype=bool)
    age = np.asarray(age, dtype=np.int64)
    n = occ.size
    monthly = np.full(n, -1.0)
    hourly = np.full(n, -1.0)
    annual = np.full(n, -1.0)
    q = wage_quantile(tables, occ, sex, np.asarray(u, dtype=np.float64))
    ac = np.clip(np.searchsorted(WAGE_AGE_EDGES, age, side="right") - 1, 0, WAGE_AGE_EDGES.size - 1)
    gen = ok & (form <= 1) & np.isfinite(q)
    if gen.any():
        o, s, f, a = occ[gen], sex[gen], form[gen], ac[gen]
        ratio = np.divide(tables.wage_level[o, s, f], tables.wage_all[o, s], out=np.ones(o.size),
                          where=tables.wage_all[o, s] > 0)
        age_r = tables.wage_age_ratio[o, s, a]
        bon_r = tables.bonus_age_ratio[o, s, a]
        if unknown_age_ratio_one:
            unk = age[gen] < 0
            age_r = np.where(unk, 1.0, age_r)
            bon_r = np.where(unk, 1.0, bon_r)
        m = q[gen] * age_r * ratio
        h = np.divide(m, tables.wage_hours[o, s, f], out=np.full(o.size, -1.0), where=tables.wage_hours[o, s, f] > 0)
        monthly[gen], hourly[gen] = m, h
        annual[gen] = 12.0 * m + tables.wage_bonus[o, s, f] * bon_r
    pt = ok & (form == 2) & np.isfinite(q) & (tables.pt_hourly[occ, sex] > 0)
    if pt.any():
        o, s = occ[pt], sex[pt]
        shape = np.divide(q[pt], tables.wage_median[o, s], out=np.ones(o.size), where=tables.wage_median[o, s] > 0)
        h = tables.pt_hourly[o, s] * shape
        m = h * tables.pt_hours_day[o, s] * tables.pt_days[o, s]
        hourly[pt], monthly[pt] = h, m
        annual[pt] = 12.0 * m + tables.pt_bonus[o, s]
    r = lambda x: np.where(x >= 0, np.round(x), -1).astype(np.int64)  # noqa: E731
    return r(monthly), r(hourly), r(annual)


def wage_uniform(seed: int | str, counters: np.ndarray) -> np.ndarray:
    """体ごとの分位 u(用途名 :data:`WAGE_DOMAIN`・``counters`` は (n, ≤3) の鍵の語・1 語だけ引く)。

    ``build.pop.attr_fns.AttrKey(seed, WAGE_DOMAIN, counters).uniform()[:, 0]`` と同じ値(試験が突き合わせる)。
    """
    c = np.asarray(counters, dtype=np.int64)
    if c.ndim == 1:
        c = c[:, None]
    cols = [c[:, j] for j in range(c.shape[1])]
    return unit_float(philox_array(seed, WAGE_DOMAIN, k19_counter_array(*cols), words=1))[:, 0]


# ------------------------------------------------------------------------------------------ W16 の体の写像
#: ペルソナの ``occupation_major`` の語 → 賃金構造の職種の番号(同じ名の語=日本標準職業分類の大分類)。
#: **未リサーチ(expedient)**: ペルソナの職業の語は v1 の生成器が付けた語で、国勢調査の抽選ではない(つなぎの台帳
#: ``DOC-wage_occ-persona-map``・外す段 4-3=W21 への差し替え)。「非就業」「通学」と空の語は写せない。
OCCUPATION_OF_PERSONA_WORD: Final[Mapping[str, int]] = MappingProxyType(
    {name: i for i, name in enumerate(WAGE_OCCUPATIONS)})
#: ペルソナの ``employment`` の語 → 賃金構造の雇用形態。**未リサーチ(expedient)**: 非正規=正社員・正職員以外(W16 の語に
#: 短時間の印は無い)・役員・自営業主・家族従業者=賃金構造の対象外(R-107 §1-1 の空欄)なので正社員・正職員の表で
#: (同じ台帳の行)。ここに無い語(非就業・空)の体は正社員・正職員の表で引く(雇用の行がある体だけが払われる)。
FORM_OF_PERSONA_EMPLOYMENT: Final[Mapping[str, int]] = MappingProxyType({
    "正規": FORM_REGULAR, "非正規": FORM_NON_REGULAR, "役員": FORM_REGULAR, "自営業主": FORM_REGULAR,
    "家族従業者": FORM_REGULAR,
})
#: 体ごとの賃金の出どころ(0=職種 × 性 × 年齢 × 雇用形態・1=写せない体の平均・2=与えられた値=W21 の ``wage_monthly``)。
BASIS_OCCUPATION: Final[int] = 0
BASIS_AVERAGE: Final[int] = 1
BASIS_GIVEN: Final[int] = 2
BASIS_NAMES: Final[tuple[str, ...]] = ("occupation", "average", "given")


def _codes(codes: Any, vocab: Sequence[str], table: Mapping[str, int]) -> np.ndarray:
    """語の番号(``vocab`` の索引・負=語なし)→ 表の値(表に無い語は −1)。"""
    c = np.asarray(codes, dtype=np.int64)
    lut = np.array([table.get(str(w), -1) for w in vocab] + [-1], dtype=np.int64)  # 逐次: 語の種類の数
    return lut[np.where((c >= 0) & (c < len(vocab)), c, len(vocab))]


def _average(tables: Any, rows: np.ndarray, o_known: np.ndarray, s_known: np.ndarray, form: np.ndarray,
             age: np.ndarray, u: np.ndarray) -> np.ndarray:
    """写せない体 ``rows`` の月の賃金: 職種 × 性ごとの値(同じ u・雇用形態・年齢)の第18表の労働者数の重みの平均(−1=値なし)。

    ``o_known``/``s_known`` が 0 以上の行はその職種・性だけで平均する。逐次: 職種 11 × 性 2。
    """
    weights = np.asarray(tables.wage_cls_freq, dtype=np.float64).sum(axis=2)  # (職種, 性)
    num = np.zeros(rows.size)
    den = np.zeros(rows.size)
    for o in range(len(WAGE_OCCUPATIONS)):  # 逐次: 職種 11 × 性 2
        for s in (0, 1):
            take = ((s_known < 0) | (s_known == s)) & ((o_known < 0) | (o_known == o))
            if not take.any() or weights[o, s] <= 0:
                continue
            k = rows[take]
            v, _h, _a = wage_values(tables, np.full(k.size, o), np.full(k.size, s), form[k], np.ones(k.size, bool),
                                    age[k], u[k], unknown_age_ratio_one=True)
            good = v >= 0
            idx = np.flatnonzero(take)[good]
            num[idx] += weights[o, s] * v[good]
            den[idx] += weights[o, s]
    out = np.full(rows.size, -1, dtype=np.int64)
    have = den > 0
    out[have] = np.round(num[have] / den[have]).astype(np.int64)
    return out


def occupation_wages(tables: Any, *, occ_code: Any, occ_vocab: Sequence[str], emp_code: Any,
                     emp_vocab: Sequence[str], sex: Any, age: Any, seed: int | str, counters: Any,
                     given: Any = None) -> tuple[np.ndarray, np.ndarray]:
    """体ごとの月の賃金[円](所定内給与)と出どころ(:data:`BASIS_NAMES` の番号)。純粋(表と入力を読むだけ)。

    - 職業の語が写せる体: :func:`wage_values`(職種 × 性 × 年齢 × 雇用形態・分位 u は :func:`wage_uniform`)。
    - 写せない体(:data:`BASIS_AVERAGE`): 職種ごとの値(同じ u・同じ雇用形態・同じ年齢)の、第18表の労働者数(職種 × 性の階級の
      度数の和)の重みの平均。性が分からない(負)体は男女も同じ重みで平均・年齢が分からない体は年齢の比 1。
    - ``given``(W21 の ``wage_monthly``=0 以上の行)があればその値(:data:`BASIS_GIVEN`)。
    """
    occ = _codes(occ_code, occ_vocab, OCCUPATION_OF_PERSONA_WORD)
    form = _codes(emp_code, emp_vocab, FORM_OF_PERSONA_EMPLOYMENT)
    form = np.where(form >= 0, form, FORM_REGULAR)
    sex = np.asarray(sex, dtype=np.int64)
    age = np.asarray(age, dtype=np.int64)
    n = occ.size
    u = wage_uniform(seed, counters)
    out = np.full(n, -1, dtype=np.int64)
    basis = np.full(n, BASIS_AVERAGE, dtype=np.int8)
    mapped = (occ >= 0) & (sex >= 0)
    if mapped.any():
        m, _h, _a = wage_values(tables, occ[mapped], sex[mapped], form[mapped], np.ones(int(mapped.sum()), bool),
                                age[mapped], u[mapped], unknown_age_ratio_one=True)
        out[mapped] = m
        basis[mapped] = np.where(m >= 0, BASIS_OCCUPATION, BASIS_AVERAGE)
    rest = np.flatnonzero(out < 0)
    if rest.size:
        # 1 回目: 職業が分かる体はその職種の中で(性が分からなければ男女の平均)・2 回目: まだ値の無い体は職種を問わない
        got = _average(tables, rest, occ[rest], sex[rest], form, age, u)
        again = got < 0
        if again.any():
            got[again] = _average(tables, rest[again], np.full(int(again.sum()), -1), sex[rest[again]], form, age, u)
        out[rest] = got
        basis[rest] = BASIS_AVERAGE
    if given is not None:
        g = np.asarray(given, dtype=np.int64).ravel()[:n]
        gi = np.flatnonzero(g >= 0)
        out[gi] = g[gi]
        basis[gi] = BASIS_GIVEN
    return out, basis


def month_hours(tables: Any, *, occ_code: Any, occ_vocab: Sequence[str], emp_code: Any, emp_vocab: Sequence[str],
                sex: Any) -> np.ndarray:
    """〔検収 M1〕体ごとの月の所定内の時間の目安[時](最低賃金の床=時給 × この時間)。

    一般(正社員・正職員/以外)=第9表の所定内実労働時間(職種 × 性 × 雇用形態)・短時間=第2表の 1 日の時間 × 実労働日数。
    職業が写せない体(と性が分からない体)は、:func:`occupation_wages` の平均と同じ重み(第18表の労働者数)の平均。
    雇用形態の写像は :func:`occupation_wages` と同じ。W17 の勤務時間は読まない。逐次: 職種 11 × 性 2。
    """
    occ = _codes(occ_code, occ_vocab, OCCUPATION_OF_PERSONA_WORD)
    form = _codes(emp_code, emp_vocab, FORM_OF_PERSONA_EMPLOYMENT)
    form = np.where(form >= 0, form, FORM_REGULAR)
    sex = np.asarray(sex, dtype=np.int64)
    gen_h = np.asarray(tables.wage_hours, dtype=np.float64)  # (職種, 性, 2)
    pt_h = np.asarray(tables.pt_hours_day, dtype=np.float64) * np.asarray(tables.pt_days, dtype=np.float64)

    def hours_of(o: np.ndarray, s: np.ndarray, f: np.ndarray) -> np.ndarray:
        return np.where(f == FORM_PART_TIME, pt_h[o, s], gen_h[o, s, np.minimum(f, 1)])

    out = np.full(occ.size, np.nan)
    mapped = (occ >= 0) & (sex >= 0)
    out[mapped] = hours_of(occ[mapped], sex[mapped], form[mapped])
    rest = np.flatnonzero(~mapped)
    if rest.size:
        weights = np.asarray(tables.wage_cls_freq, dtype=np.float64).sum(axis=2)
        num = np.zeros(rest.size)
        den = np.zeros(rest.size)
        for o in range(len(WAGE_OCCUPATIONS)):  # 逐次: 職種 11 × 性 2
            for s_ in (0, 1):
                take = ((sex[rest] < 0) | (sex[rest] == s_)) & ((occ[rest] < 0) | (occ[rest] == o))
                if not take.any() or weights[o, s_] <= 0:
                    continue
                h = hours_of(np.full(int(take.sum()), o), np.full(int(take.sum()), s_), form[rest[take]])
                num[take] += weights[o, s_] * h
                den[take] += weights[o, s_]
        out[rest] = np.where(den > 0, num / np.where(den > 0, den, 1.0), np.nan)
    return out


def apply_floor(monthly: np.ndarray, hours: np.ndarray, yen_per_hour: float | None) -> tuple[np.ndarray, np.ndarray]:
    """〔検収 M1〕最低賃金法の床(4 条 2 項=足りない部分は最低賃金と同じ定めとみなす)。時給(月 ÷ 月の時間の目安)が床を
    下回る体の月の賃金を、床 × 月の時間の目安(円に丸める)に上げる。``yen_per_hour`` が ``None``(規則の表にその日の版が
    無い)なら床なし。戻り=(床を当てた月の賃金, 床に当たった体の印)。値の無い体(負)と時間の無い体はそのまま。"""
    m = np.asarray(monthly, dtype=np.int64)
    if yen_per_hour is None:
        return m.copy(), np.zeros(m.size, dtype=bool)
    h = np.asarray(hours, dtype=np.float64)
    ok = (m >= 0) & np.isfinite(h) & (h > 0)
    floor_amt = np.zeros(m.size, dtype=np.int64)
    floor_amt[ok] = np.rint(float(yen_per_hour) * h[ok]).astype(np.int64)
    raised = ok & (m < floor_amt)
    return np.where(raised, floor_amt, m), raised


def median_check(tables: Any, wages: np.ndarray, basis: np.ndarray, occ_code: Any, occ_vocab: Sequence[str],
                 emp_code: Any, emp_vocab: Sequence[str], sex: Any, who: np.ndarray | None = None,
                 min_n: int = 1) -> list[dict[str, Any]]:
    """計器(構築側の点検=合否なし): 職種 × 性ごとの月の賃金の中央値と、第18表の中位数(一般労働者)との差。

    ``who`` は数える体(``None``=全部)。写せた体(:data:`BASIS_OCCUPATION`)で雇用形態が一般の体だけを数える。
    """
    occ = _codes(occ_code, occ_vocab, OCCUPATION_OF_PERSONA_WORD)
    form = _codes(emp_code, emp_vocab, FORM_OF_PERSONA_EMPLOYMENT)
    sex = np.asarray(sex, dtype=np.int64)
    sel = np.zeros(occ.size, dtype=bool)
    sel[np.arange(occ.size) if who is None else np.asarray(who, dtype=np.int64)] = True
    sel &= (np.asarray(basis) == BASIS_OCCUPATION) & (form >= 0) & (form <= 1)
    out: list[dict[str, Any]] = []
    for o in range(len(WAGE_OCCUPATIONS)):  # 逐次: 職種 11 × 性 2
        for s in (0, 1):
            m = sel & (occ == o) & (sex == s)
            if int(m.sum()) < int(min_n):
                continue
            med = float(np.median(np.asarray(wages)[m]))
            ref = float(tables.wage_median[o, s])
            out.append({"occupation": WAGE_OCCUPATIONS[o], "sex": SEXES[s], "n": int(m.sum()),
                        "median": int(round(med)), "r107_median": int(round(ref)),
                        "ratio": round(med / ref, 4) if ref > 0 else None})
    return out
