"""economy.taxes — 第 4 期 4-2 の規則の表の machine の行の読み手(税・社会保険・消費税の端数と期限・信用の上限・割増)。

正: R-118(docs/research/v2-r118-rights-and-rules-contents.md)§2-6・§2-7・§3・§7-1・付属の 19 行・PENDING 仮-40(Q1〜Q7)・
決定 10-12 §4-11(税はレジと天引き・信用の上限は機械の検査)・CLAUDE.md §3(破れない法則とお金の計算はエンジン)。

読む行(``docs/design/rules-table.json``・``engine.rules.table``・どれも ``kind: machine``・``asof`` の日に効いている版):

| 行 | 読み手 | 呼び手 |
|---|---|---|
| ``income_tax.withholding_monthly`` | :func:`income_tax_withholding`(電算機計算の特例・甲欄・扶養 0 人=Q7) | 給料日 |
| ``resident_tax.special_collection_tokyo_ward`` | :func:`resident_tax_monthly`(前年の所得=月の賃金 × 12=Q4) | 給料日 |
| ``resident_tax.basic_deduction``(4-2b) | :func:`resident_tax_monthly`(基礎控除 43/29/15 万円・0) | 給料日 |
| ``resident_tax.adjustment_credit_tokyo_ward``(4-2b) | :func:`resident_tax_monthly`(調整控除 5%) | 給料日 |
| ``resident_tax.non_taxable_tokyo_ward``(4-2b) | :func:`resident_tax_monthly`(非課税 45 万円・未成年者 135 万円) | 給料日 |
| ``health_insurance.kyoukai_tokyo`` | :func:`deductions`(健保+介護 40〜64 歳・等級表・折半・50 銭)・:func:`enrollment`
  (〔4-2b〕``age_max_exclusive``=75 歳未満)| 給料日 |
| ``child_support_levy.rate`` | :func:`deductions`(健保の標準報酬・折半・50 銭) | 給料日 |
| ``pension.employees_rate`` | :func:`deductions`(厚年の等級表・折半・50 銭)・:func:`enrollment`
  (〔4-2b〕``age_max_exclusive``=70 歳未満) | 給料日 |
| ``child_care_contribution.rate``(4-2b) | :func:`deductions`(厚年の標準報酬 × 率・事業主だけ・切り捨て) | 給料日 |
| ``employment_insurance.rate_general`` | :func:`deductions`(賃金の総額 × 率) | 給料日 |
| ``consumption_tax.invoice_rounding`` | :func:`invoice_rounding`(1 回の購入=1 枚のレシート=1 つの税率・切り捨て) | レジ |
| ``consumption_tax.filing_deadline``(human) | :func:`filing_deadline`=つなぎの読み口(課税期間=暦年・翌年 3 月 31 日=Q1・
  検収 L1=人が納める行動の段 6-6 までのつなぎ ``DOC-rules42-tax-remit-machine``) | 日の締め |
| ``consumption_tax.reduced_rate`` | :func:`reduced_rate`(器=呼び手なし・品目と店内か持ち帰りかの段の後) | ― |
| ``credit.total_volume_cap`` | :func:`total_volume_cap`(``economy.credit.total_volume_check``=器) | ― |
| ``credit.interest_cap`` | :func:`interest_cap`(``economy.credit.interest_cap_rate``=器) | ― |
| ``labor.overtime_premium`` | :func:`overtime_premium`(器=勤務の記録の時間外が出る段の後・政令の率は未確認) | ― |

お金の動き(``economy.stage2``)は台帳の汎用の口だけを使う(本モジュールは額を出すだけ・残高を書かない)。

端数(R-118 §2-6): 社会保険料の本人の分=50 銭以下は切り捨て・50 銭を超えれば切り上げ(協会けんぽ東京の額表の注)。雇用保険の
本人の分も同じ決まりで丸める(控除の端数は答申に無い=未リサーチ(expedient)・台帳 ``DOC-rules42-rounding``)。雇用主の分=
全額の 1 円未満の切り捨て − 本人の分(未リサーチ(expedient)・同じ台帳の行)。源泉所得税=10 円未満の四捨五入(告示)・控除の
額の 1 円未満は切り上げ(告示)。住民税の月の額=年の額の 12 分の 1 の 1 円未満の切り捨て(未リサーチ(expedient)・同じ行)。

〔第 4 期 4-2b〕規則の表の空欄 3 件を埋めた値(R-118 §10-2=親の一次確認): 住民税の基礎控除・調整控除・非課税(扶養 0 の
世界)/厚年 70 歳・健保 75 歳の年齢の上限(75 歳以上の後期高齢者医療の保険料は天引きしない=空欄の宣言
``DOC-rules42b-late-elderly-medical-blank``)/子ども・子育て拠出金(事業主だけ・厚年の被保険者の標準報酬 × 0.36%)。
:func:`payroll_tables` の ``r42b``(腕 ``SHIBUYA_RULES_42B``=``engine.economy_rules.PayrollInputs.rules_42b``・既定 真)が
偽なら 4-2 の値の再現(旧道=次の版上げで消す・台帳 ``DOC-rules42b-legacy-switch``)。

〔検収 L5〕下限の印(``asof_basis=lower_bound``)の行を下限より前の日に引いたとき・``valid_until`` の後の日は、黙って
「規則なし」にせず ``RuleNotInForce`` で止める(施行の初日が分からない=効いていたかどうか分からない)。

逐次ループ宣言: なし(配列演算。Python のループは表の帯の数=10 未満ぶんだけ)。
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Final, Mapping

import numpy as np

__all__ = [
    "INCOME_TAX_RULE_ID", "RESIDENT_TAX_RULE_ID", "HEALTH_RULE_ID", "CHILD_SUPPORT_RULE_ID", "PENSION_RULE_ID",
    "EMPLOYMENT_RULE_ID", "INVOICE_RULE_ID", "DEADLINE_RULE_ID", "REDUCED_RULE_ID", "TOTAL_VOLUME_RULE_ID",
    "INTEREST_RULE_ID", "OVERTIME_RULE_ID", "READ_RULES", "BRIDGE_READ_RULES", "CARE_AGE", "FULL_TIME_BASE_HOURS", "EMPLOYEE_ITEMS",
    "EMPLOYER_ITEMS", "EMPLOYER_ITEMS_42", "BASIC_DEDUCTION_RULE_ID", "ADJUSTMENT_RULE_ID", "NON_TAXABLE_RULE_ID",
    "CHILD_CARE_RULE_ID",
    "PayrollTables", "payroll_tables", "standard_monthly", "share_50sen", "income_tax_withholding",
    "resident_tax_monthly", "Enrollment", "enrollment", "Deductions", "deductions", "invoice_rounding",
    "filing_deadline", "reduced_rate", "total_volume_cap", "interest_cap", "overtime_premium",
]

INCOME_TAX_RULE_ID: Final[str] = "income_tax.withholding_monthly"
RESIDENT_TAX_RULE_ID: Final[str] = "resident_tax.special_collection_tokyo_ward"
HEALTH_RULE_ID: Final[str] = "health_insurance.kyoukai_tokyo"
CHILD_SUPPORT_RULE_ID: Final[str] = "child_support_levy.rate"
PENSION_RULE_ID: Final[str] = "pension.employees_rate"
EMPLOYMENT_RULE_ID: Final[str] = "employment_insurance.rate_general"
INVOICE_RULE_ID: Final[str] = "consumption_tax.invoice_rounding"
DEADLINE_RULE_ID: Final[str] = "consumption_tax.filing_deadline"
REDUCED_RULE_ID: Final[str] = "consumption_tax.reduced_rate"
TOTAL_VOLUME_RULE_ID: Final[str] = "credit.total_volume_cap"
INTEREST_RULE_ID: Final[str] = "credit.interest_cap"
OVERTIME_RULE_ID: Final[str] = "labor.overtime_premium"
#: 〔第 4 期 4-2b〕空欄 3 件を埋めた行(R-118 §10-2)。
BASIC_DEDUCTION_RULE_ID: Final[str] = "resident_tax.basic_deduction"
ADJUSTMENT_RULE_ID: Final[str] = "resident_tax.adjustment_credit_tokyo_ward"
NON_TAXABLE_RULE_ID: Final[str] = "resident_tax.non_taxable_tokyo_ward"
CHILD_CARE_RULE_ID: Final[str] = "child_care_contribution.rate"
#: 本モジュールが読む machine の行(試験が規則の表の machine の行と突き合わせる)。
READ_RULES: Final[tuple[str, ...]] = (
    INCOME_TAX_RULE_ID, RESIDENT_TAX_RULE_ID, HEALTH_RULE_ID, CHILD_SUPPORT_RULE_ID, PENSION_RULE_ID,
    EMPLOYMENT_RULE_ID, INVOICE_RULE_ID, REDUCED_RULE_ID, TOTAL_VOLUME_RULE_ID, INTEREST_RULE_ID, OVERTIME_RULE_ID,
    BASIC_DEDUCTION_RULE_ID, ADJUSTMENT_RULE_ID, NON_TAXABLE_RULE_ID, CHILD_CARE_RULE_ID)
#: 〔検収 L1〕つなぎとして読む human の行(人の手続きの値を機械が使う=宣言つき・台帳 ``DOC-rules42-tax-remit-machine``)。
BRIDGE_READ_RULES: Final[tuple[str, ...]] = (DEADLINE_RULE_ID,)
#: 介護保険の第 2 号被保険者の年齢(40〜64 歳・協会けんぽの頁=規則の表の行の ``care_rate_age_40_64`` の名が持つ範囲)。
CARE_AGE: Final[tuple[int, int]] = (40, 64)
#: 「通常の労働者」の週の所定労働時間[時](週 40 時間=労基法 32 条の上限で代える=未リサーチ(expedient)・台帳
#: ``DOC-rules42-full-time-hours``・``engine.economy_rules.FULL_TIME_WEEKLY_HOURS`` はこの 4 分の 3=試験が突き合わせる)。
FULL_TIME_BASE_HOURS: Final[float] = 40.0
#: 本人の分の項目(天引きの内訳=計器の名)。
EMPLOYEE_ITEMS: Final[tuple[str, ...]] = ("health", "child_support", "pension", "employment", "income_tax",
                                          "resident_tax")
#: 雇用主の分の項目(〔第 4 期 4-2b〕子ども・子育て拠出金=事業主だけ を末尾に足した)。
EMPLOYER_ITEMS: Final[tuple[str, ...]] = ("health", "child_support", "pension", "employment", "child_care_contribution")
#: 〔第 4 期 4-2b〕4-2 の雇用主の分の項目(腕 ``SHIBUYA_RULES_42B=off``=4-2 の値の再現=次の版上げで消す)。
EMPLOYER_ITEMS_42: Final[tuple[str, ...]] = EMPLOYER_ITEMS[:4]


def _rules(rules: Any) -> Any:
    from shibuya.engine.rules import table as _RT

    return _RT.default_rules() if rules is None else rules


def _get(rule_id: str, asof: "str | _dt.date", rules: Any) -> Any:
    """``asof`` の日に効いている行。施行の前は ``None``(表の無い写し・行の無い表も ``None``)。〔検収 L5〕最初の版の asof が
    下限の印(読んだ版の施行日を下限に置いた)の行を下限より前に引いたときは ``RuleNotInForce`` で止める。"""
    from shibuya.engine.rules import table as _RT

    try:
        rt = _rules(rules)
        return rt.get(rule_id, asof)
    except _RT.RuleNotInForce:
        first = rt.versions(rule_id)[0]
        if first.asof_is_lower_bound:
            raise _RT.RuleNotInForce(f"{rule_id} の最初の版の asof {first.asof} は下限の印(施行の初日が分からない)="
                                     f"{asof} に効いていたかどうか分からない(黙って規則なしにしない)") from None
        return None
    except (FileNotFoundError, KeyError):
        return None


def _row(rule_id: str, asof: "str | _dt.date", rules: Any = None) -> Any:
    """``asof`` の日に効いている machine の行(施行の前・表の無い写し・行の無い表は ``None``)。machine でない行は止める。"""
    from shibuya.engine.rules import table as _RT

    row = _get(rule_id, asof, rules)
    if row is not None and str(row.kind) != _RT.KIND_MACHINE:
        raise ValueError(f"{rule_id} は machine の行であること(いま {row.kind!r})")
    return row


def _bridge_row(rule_id: str, asof: "str | _dt.date", rules: Any = None) -> Any:
    """〔検収 L1〕つなぎの読み口: :data:`BRIDGE_READ_RULES` の human の行だけを読む(ほかの id は止める)。"""
    from shibuya.engine.rules import table as _RT

    if rule_id not in BRIDGE_READ_RULES:
        raise ValueError(f"{rule_id} はつなぎで読む行の一覧に無い")
    row = _get(rule_id, asof, rules)
    if row is not None and str(row.kind) != _RT.KIND_HUMAN:
        raise ValueError(f"{rule_id} は human の行であること(いま {row.kind!r})")
    return row


def _src(row: Any) -> str:
    return "none" if row is None else f"rules:{row.id}@{row.asof}"


def _frac(x: Any) -> Fraction:
    return Fraction(str(x))


def _valid(row: Any, asof: "str | _dt.date") -> Any:
    """行の ``valid_until``(適用期間の終わり=雇用保険の率の年度など)。〔検収 L5〕過ぎた日は黙って 0 にせず
    ``RuleNotInForce`` で止める(次の年度の率は表に無い=足すまでランを止める)。"""
    from shibuya.engine.rules import table as _RT

    if row is None:
        return None
    until = row.params.get("valid_until") if hasattr(row.params, "get") else None
    day = asof.isoformat() if isinstance(asof, _dt.date) else str(asof)
    if until and day > str(until):
        raise _RT.RuleNotInForce(f"{row.id} の適用期間は {until} まで({day} の版は表に無い=次の年度の行を足す)")
    return row


@dataclass(frozen=True)
class _Grades:
    """標準報酬月額の等級表(下限の昇順・最後の級は上限なし)。"""

    lower: np.ndarray
    standard: np.ndarray

    @classmethod
    def of(cls, grades: Any) -> "_Grades":
        g = sorted(({"from": int(x["from_incl"]), "std": int(x["standard"])} for x in grades), key=lambda d: d["from"])
        lo = np.array([d["from"] for d in g], dtype=np.int64)
        st = np.array([d["std"] for d in g], dtype=np.int64)
        if lo.size == 0 or lo[0] != 0:
            raise ValueError("等級表は 0 円から始まる")
        return cls(lower=lo, standard=st)


@dataclass(frozen=True)
class PayrollTables:
    """給料日 ``asof`` に効いている天引きの表(行が無い項目は ``None``=その項目は 0)。"""

    asof: str
    income_tax: Any = None
    resident_tax: Any = None
    health: Any = None
    child_support: Any = None
    pension: Any = None
    employment: Any = None
    health_grades: Any = None
    pension_grades: Any = None
    sources: Mapping[str, str] = field(default_factory=dict)
    #: 〔第 4 期 4-2b〕空欄 3 件を埋めた値か(偽=4-2 の値の再現=旧道)と、その行(無い項目は ``None``=0)・年齢の上限
    #: (``age_max_exclusive``・``None``=上限なし)。
    r42b: bool = False
    basic_deduction: Any = None
    adjustment_credit: Any = None
    non_taxable: Any = None
    child_care: Any = None
    pension_age_max: int | None = None
    health_age_max: int | None = None

    @property
    def employer_items(self) -> tuple[str, ...]:
        """雇用主の分の項目(4-2b の値なら拠出金を含む 5 項目・4-2 の値の再現なら 4 項目)。"""
        return EMPLOYER_ITEMS if self.r42b else EMPLOYER_ITEMS_42

    def record(self) -> dict[str, Any]:
        out: dict[str, Any] = {"asof": self.asof, "sources": dict(self.sources)}
        if self.r42b:  # 〔4-2b〕腕 off の記録は 4-2 のまま
            out["age_max_exclusive"] = {"pension": self.pension_age_max, "health": self.health_age_max}
        return out


_TABLE_CACHE: dict[tuple[str, bool], PayrollTables] = {}


def _age_max(row: Any) -> int | None:
    """〔4-2b〕行の年齢の上限(``age_max_exclusive``=この年齢に達したら被保険者でない・欄が無ければ ``None``)。"""
    if row is None or not hasattr(row.params, "get") or row.params.get("age_max_exclusive") is None:
        return None
    return int(row.params["age_max_exclusive"])


def payroll_tables(asof: "str | _dt.date", rules: Any = None, *, r42b: bool = True) -> PayrollTables:
    """``asof`` の日に効いている天引きの 6 行(リポの表なら日ごとに 1 回だけ作る)。

    〔第 4 期 4-2b〕``r42b``(既定 真)なら空欄 3 件を埋めた行(住民税の基礎控除・調整控除・非課税=住民税の行がある日だけ引く
    (下限の印の行=住民税の年度の始まり)・子ども・子育て拠出金)と、健保・厚年の行の年齢の上限も引く。偽は 4-2 の値の再現。
    """
    day = asof.isoformat() if isinstance(asof, _dt.date) else str(_dt.date.fromisoformat(str(asof)))
    key = (day, bool(r42b))
    if rules is None and key in _TABLE_CACHE:
        return _TABLE_CACHE[key]
    it = _row(INCOME_TAX_RULE_ID, day, rules)
    rt = _row(RESIDENT_TAX_RULE_ID, day, rules)
    hi = _row(HEALTH_RULE_ID, day, rules)
    cs = _row(CHILD_SUPPORT_RULE_ID, day, rules)
    pe = _row(PENSION_RULE_ID, day, rules)
    ei = _valid(_row(EMPLOYMENT_RULE_ID, day, rules), day)
    sources = {"income_tax": _src(it), "resident_tax": _src(rt), "health": _src(hi), "child_support": _src(cs),
               "pension": _src(pe), "employment": _src(ei)}
    extra: dict[str, Any] = {}
    if r42b:  # 〔第 4 期 4-2b〕空欄 3 件を埋めた行
        bd = ac = nt = None
        if rt is not None:  # 住民税の行がある日だけ(控除の 3 行は住民税の年度の始まりに下限の印)
            bd = _row(BASIC_DEDUCTION_RULE_ID, day, rules)
            ac = _row(ADJUSTMENT_RULE_ID, day, rules)
            nt = _row(NON_TAXABLE_RULE_ID, day, rules)
        cc = _row(CHILD_CARE_RULE_ID, day, rules)
        if cc is not None and _frac(cc.params["employee_share"]) != 0:
            raise ValueError(f"{CHILD_CARE_RULE_ID} は事業主だけの拠出金(employee_share 0)であること")
        extra = dict(r42b=True, basic_deduction=bd, adjustment_credit=ac, non_taxable=nt, child_care=cc,
                     pension_age_max=_age_max(pe), health_age_max=_age_max(hi))
        sources.update({"basic_deduction": _src(bd), "adjustment_credit": _src(ac), "non_taxable": _src(nt),
                        "child_care_contribution": _src(cc)})
    out = PayrollTables(
        asof=day, income_tax=it, resident_tax=rt, health=hi, child_support=cs, pension=pe, employment=ei,
        health_grades=None if hi is None else _Grades.of(hi.params["grades"]),
        pension_grades=None if pe is None else _Grades.of(pe.params["grades"]),
        sources=sources, **extra)
    if rules is None:
        _TABLE_CACHE[key] = out
    return out


# ================================================================ 端数と等級
def standard_monthly(gross: np.ndarray, grades: _Grades) -> np.ndarray:
    """報酬月額 → 標準報酬月額(等級表の下限で引く・健保法 40 条・厚年法 20 条)。"""
    g = np.asarray(gross, dtype=np.int64)
    k = np.searchsorted(grades.lower, g, side="right") - 1
    return grades.standard[np.clip(k, 0, grades.standard.size - 1)]


def share_50sen(num: np.ndarray, den: int) -> np.ndarray:
    """額 ``num / den`` 円を「50 銭以下は切り捨て・50 銭を超えれば切り上げ」で円に(R-118 §2-6・額表の注)。"""
    n = np.asarray(num, dtype=np.int64)
    d = int(den)
    yen = n // d
    rem = n - yen * d
    return yen + (2 * rem > d).astype(np.int64)


def _half_share(base: np.ndarray, rate: Fraction) -> tuple[np.ndarray, np.ndarray]:
    """折半の保険料: (本人の分=全額の半分を 50 銭の決まりで円に, 雇用主の分=全額の 1 円未満切り捨て − 本人の分)。"""
    b = np.asarray(base, dtype=np.int64)
    p, q = int(rate.numerator), int(rate.denominator)
    full_num = b * p
    emp = share_50sen(full_num, 2 * q)
    er = np.maximum(full_num // q - emp, 0)
    return emp, er


# ================================================================ 源泉所得税(電算機計算の特例・甲欄)
def _bands_value(x: np.ndarray, bands: Any, *, ceil: bool) -> np.ndarray:
    """``[{"from","to","fixed"|"rate"+"add"|"amount"}]`` の帯の値(``to`` は含む・``None``=上限なし)。"""
    out = np.zeros(x.shape, dtype=np.int64)
    for b in bands:  # 逐次ループ宣言: 帯の数(5〜7)
        lo = int(b["from"])
        hi = b.get("to")
        m = (x >= lo) & ((x <= int(hi)) if hi is not None else True)
        if not np.any(m):
            continue
        if "fixed" in b:
            out[m] = int(b["fixed"])
        elif "amount" in b:
            out[m] = int(b["amount"])
        else:
            r = _frac(b["rate"])
            num = x[m] * int(r.numerator)
            den = int(r.denominator)
            v = -((-num) // den) if ceil else num // den
            out[m] = v + int(b["add"])
    return out


def income_tax_withholding(a: np.ndarray, tables: PayrollTables, dependents: np.ndarray | None = None) -> np.ndarray:
    """源泉所得税(月額表の甲欄の電算機計算の特例=平成 24 年財務省告示第 116 号・令和 8 年分)。

    ``a``=その月の社会保険料等を控除した後の給与等の金額。課税給与所得 B = a − 給与所得控除(別表第一・1 円未満切り上げ)−
    基礎控除(別表第二の三)− 配偶者(特別)控除と扶養控除(1 人 31,667 円 × 人数=扶養は 0 人=宣言)。税額=B × 税率 − 控除額
    (別表第四)の 10 円未満の四捨五入。〔親の判断(問い 3)〕a が月額表の甲欄の ``kou_zero_below_yen``(105,000 円)未満なら
    0 円(月額表どおり)。行が無ければ 0。
    """
    x = np.maximum(np.asarray(a, dtype=np.int64), 0)
    row = tables.income_tax
    if row is None or x.size == 0:
        return np.zeros(x.shape, dtype=np.int64)
    p = row.params
    eid = _bands_value(x, p["employment_income_deduction"], ceil=True)
    basic = _bands_value(x, p["basic_deduction"], ceil=True)
    dep = 0 if dependents is None else np.asarray(dependents, dtype=np.int64) * int(p["dependent_or_spouse_deduction_each"])
    b = np.maximum(x - eid - basic - dep, 0)
    # 〔親の判断(問い 3)〕月額表の甲欄の決まり=``kou_zero_below_yen``(105,000 円)未満は 0 円・それ以上は特例の式
    b = np.where(x < int(p["kou_zero_below_yen"]), 0, b)
    tax = np.zeros(x.shape, dtype=np.int64)
    for band in p["tax_on_taxable"]:  # 逐次ループ宣言: 帯の数(7)
        lo, hi = int(band["from"]), band.get("to")
        m = (b >= lo) & ((b <= int(hi)) if hi is not None else True)
        if not np.any(m):
            continue
        r = _frac(band["rate"])
        q = int(r.denominator)
        num = b[m] * int(r.numerator) - int(band["minus"]) * q  # 税額 × q
        tax[m] = ((num + 5 * q) // (10 * q)) * 10  # 10 円未満の四捨五入
    return np.maximum(tax, 0)


# ================================================================ 住民税の特別徴収
def resident_tax_monthly(gross: np.ndarray, tables: PayrollTables, social: np.ndarray | None = None,
                         age: np.ndarray | None = None) -> np.ndarray:
    """住民税の特別徴収の月の額=(所得割+均等割 1,000+3,000+森林環境税 1,000)÷ 12 の 1 円未満の切り捨て。

    前年の収入=今の月の賃金 × 12(Q4=未リサーチ(expedient)・台帳 ``DOC-rules42-resident-tax-base``)。〔検収 M1・親の判断〕
    合計所得=前年の収入 − 給与所得控除(源泉の別表第一を月の額面に当てた額 × 12)。

    - 4-2 の値(``tables.r42b`` 偽=旧道): 所得割=(合計所得 − 社会保険料控除(``social``=本人の社会保険料等の月の額 × 12))×
      (都民税 4%+区民税 6%)。
    - 〔第 4 期 4-2b〕課税所得=合計所得 − 社会保険料控除 − 基礎控除(:func:`_basic_deduction`)・所得割=課税所得 × 10% −
      調整控除(:func:`_adjustment_credit`・0 を下回らない)・非課税(:func:`resident_non_taxable`=``age``=今の年齢)の行は均等割も
      所得割も 0。所得割の 100 円未満の切り捨てと 6 月の端数寄せは入れていない(台帳 ``DOC-rules42b-resident-tax-rounding``)。

    行が無い日(6 月より前の年度)は 0。
    """
    return _resident_tax(gross, tables, social, age)[0]


def _resident_tax(gross: np.ndarray, tables: PayrollTables, social: np.ndarray | None,
                  age: np.ndarray | None) -> tuple[np.ndarray, np.ndarray]:
    """(住民税の月の額, 非課税の行の真偽)。"""
    g = np.maximum(np.asarray(gross, dtype=np.int64), 0)
    row = tables.resident_tax
    if row is None:
        return np.zeros(g.shape, dtype=np.int64), np.zeros(g.shape, dtype=bool)
    p = row.params
    rate = _frac(p["income_levy_rate_metro"]) + _frac(p["income_levy_rate_ward"])
    eid = (_bands_value(g, tables.income_tax.params["employment_income_deduction"], ceil=True)
           if tables.income_tax is not None else np.zeros(g.shape, dtype=np.int64))
    si = np.zeros(g.shape, dtype=np.int64) if social is None else np.asarray(social, dtype=np.int64)
    per_capita = int(p["per_capita_metro_yen"]) + int(p["per_capita_ward_yen"]) + int(p["forest_environment_tax_yen"])
    if not tables.r42b:  # 4-2 の値の再現(旧道=次の版上げで消す)
        base = np.maximum(g - eid - si, 0) * 12
        income = (base * int(rate.numerator)) // int(rate.denominator)
        annual = np.where(g > 0, income + per_capita, 0)
        return annual // 12, np.zeros(g.shape, dtype=bool)
    total = np.maximum(g - eid, 0) * 12  # 合計所得(前年の収入 − 給与所得控除)
    taxable = np.maximum(total - si * 12 - _basic_deduction(total, tables.basic_deduction), 0)
    income = (taxable * int(rate.numerator)) // int(rate.denominator)
    income = np.maximum(income - _adjustment_credit(total, taxable, tables.adjustment_credit), 0)
    exempt = resident_non_taxable(total, age, tables.non_taxable) & (g > 0)
    annual = np.where((g > 0) & ~exempt, income + per_capita, 0)
    return annual // 12, exempt


def _basic_deduction(total: np.ndarray, row: Any) -> np.ndarray:
    """〔4-2b〕住民税の基礎控除(地方税法 314 条の 2 第 2 項=合計所得の帯ごとの額・行が無ければ 0)。"""
    t = np.asarray(total, dtype=np.int64)
    out = np.zeros(t.shape, dtype=np.int64)
    if row is None:
        return out
    done = np.zeros(t.shape, dtype=bool)
    last = None
    for b in row.params["bands"]:  # 逐次ループ宣言: 帯の数(4)
        hi = b["total_income_to_incl"]
        if last is not None and (hi is not None and int(hi) <= last):
            raise ValueError(f"{row.id} の帯は昇順(上限なしは最後)であること")
        m = ~done & ((t <= int(hi)) if hi is not None else True)
        out[m] = int(b["deduction_yen"])
        done |= m
        last = None if hi is None else int(hi)
    return out


def _adjustment_credit(total: np.ndarray, taxable: np.ndarray, row: Any) -> np.ndarray:
    """〔4-2b〕住民税の調整控除(扶養 0=人的控除額の差は基礎控除の差だけ・都+区の率をまとめて 1 円未満の切り捨て)。

    課税所得が閾値以下=min(差, 課税所得)× 率・閾値超=max(差 −(課税所得 − 閾値), 下限)× 率・合計所得が上の値を超えれば 0。
    行が無ければ 0。
    """
    tx = np.asarray(taxable, dtype=np.int64)
    if row is None:
        return np.zeros(tx.shape, dtype=np.int64)
    p = row.params
    diff = int(p["personal_deduction_difference_no_dependents_yen"])
    th = int(p["taxable_income_threshold_yen"])
    r = _frac(p["rate_metro"]) + _frac(p["rate_ward"])
    base = np.where(tx <= th, np.minimum(diff, tx), np.maximum(diff - (tx - th), int(p["floor_base_yen"])))
    credit = (base * int(r.numerator)) // int(r.denominator)
    return np.where(np.asarray(total, dtype=np.int64) > int(p["not_applied_total_income_over_yen"]), 0, credit)


def resident_non_taxable(total: np.ndarray, age: np.ndarray | None, row: Any) -> np.ndarray:
    """〔4-2b〕住民税の非課税(扶養 0・23 区): 合計所得が限度以下、または未成年者(今の年齢が ``minor_age_below`` 未満・
    年齢 −1=不明は未成年者でない)で特別の限度以下。障害者・寡婦・ひとり親は材料が無い=入れていない
    (台帳 ``DOC-rules42b-non-taxable-only-minor``)。行が無ければ偽。"""
    t = np.asarray(total, dtype=np.int64)
    if row is None:
        return np.zeros(t.shape, dtype=bool)
    p = row.params
    a = np.full(t.shape, -1, dtype=np.int64) if age is None else np.asarray(age, dtype=np.int64)
    minor = (a >= 0) & (a < int(p["minor_age_below"]))
    return (t <= int(p["no_dependents_total_income_max_yen"])) | (minor & (t <= int(p["special_total_income_max_yen"])))


# ================================================================ 加入の判定
@dataclass(frozen=True)
class Enrollment:
    """体(行)ごとの加入(社会保険=健保・介護・支援金・厚年/雇用保険/源泉と住民税)と判定の材料の有無。"""

    social: np.ndarray
    employment: np.ndarray
    taxed: np.ndarray
    no_basis: np.ndarray
    care: np.ndarray
    #: 〔第 4 期 4-2b〕厚年の加入(``social``=健保の加入(75 歳未満)とは別=70 歳未満)と行の年齢(−1=不明)。
    #: ``None``=``social`` と同じ(4-2 の値)・年齢なし。
    pension: np.ndarray | None = None
    age: np.ndarray | None = None


def enrollment(inputs: Any, agents: np.ndarray, tables: PayrollTables,
               assume_full_time: np.ndarray | None = None) -> Enrollment:
    """加入の判定(R-118 §2-3・§2-6・規則の表の行の値): 週の時間の目安が通常の労働者の 4 分の 3 以上=社会保険/
    4 分の 3 未満は特定適用事業所(被保険者 ``employer_min_insured`` 人以上)で週 ``min_weekly_hours`` 時間以上かつ学生でない
    人だけ/雇用保険=週 20 時間以上(31 日以上の雇用の見込みは全員あるとみなす=宣言)/業主・家族従業者・内職は雇われる側で
    ない=どれも天引きしない(本人で納める=human)/判定の材料が無い体(役割も時間も無い)は社会保険と雇用保険に未加入
    (宣言)・源泉と住民税は雇われる側として天引きする。〔第 4 期 4-2b〕年齢の上限: ``social``(健保・介護・支援金)は
    健保の行の ``age_max_exclusive``(75)未満・``pension``(厚年・子ども・子育て拠出金)は厚年の行の ``age_max_exclusive``
    (70)未満(年齢 −1=不明は上限の内=宣言)。``tables.r42b`` が偽(4-2 の値)は上限なし=``pension`` は ``social`` と同じ。

    〔検収 M2・親の判断〕``assume_full_time``(行ごとの真偽=外の雇用主の体)の行は「被保険者 51 人以上の事業所の正社員
    (週 40 時間)」とみなす(未リサーチ(expedient)・台帳 ``DOC-rules42-outside-employer-enrolled``)。2027-10 からの
    36 人の値(``employer_min_insured_from_2027_10``)は世界の時点の外=読まない。
    """
    a = np.asarray(agents, dtype=np.int64)
    n = a.size
    if inputs is None:
        z = np.zeros(n, dtype=bool)
        return Enrollment(social=z, employment=z, taxed=np.ones(n, dtype=bool), no_basis=np.ones(n, dtype=bool), care=z,
                          pension=z, age=np.full(n, -1, dtype=np.int64))
    hours = np.asarray(inputs.weekly_hours, dtype=np.float64)[a].copy()
    emp_like = inputs.employee_like()[a].copy()
    insured = np.asarray(inputs.employer_insured)[a].copy()
    if assume_full_time is not None:
        ft = np.asarray(assume_full_time, dtype=bool).ravel()
        hours[ft] = FULL_TIME_BASE_HOURS
        emp_like[ft] = True
        insured[ft] = np.maximum(insured[ft], 51)
    known = np.isfinite(hours)
    age = np.asarray(inputs.age, dtype=np.int64)[a]
    hi = tables.health
    social = np.zeros(n, dtype=bool)
    if hi is not None:
        cov = hi.params["short_time_coverage"]
        ft = hi.params["full_time_share"]
        full_h = FULL_TIME_BASE_HOURS * float(Fraction(int(ft[0]), int(ft[1])))
        full = known & (hours >= full_h)
        short = known & (hours >= float(cov["min_weekly_hours"])) & (hours < full_h) & (
            insured >= int(cov["employer_min_insured"]))
        if bool(cov["students_excluded"]):
            short &= ~np.asarray(inputs.student, dtype=bool)[a]
        social = emp_like & (full | short)
    ei = tables.employment
    employment = np.zeros(n, dtype=bool)
    if ei is not None:
        employment = emp_like & known & (hours >= float(ei.params["min_weekly_hours"]))
    pension = social  # 4-2 の値=厚年の加入は健保と同じ
    if tables.pension_age_max is not None:  # 〔4-2b〕厚年 70 歳未満(厚年法 9 条)
        pension = social & (age < int(tables.pension_age_max))
    if tables.health_age_max is not None:  # 〔4-2b〕健保 75 歳未満(後期高齢者医療へ=健保法 3 条 1 項 7 号)
        social = social & (age < int(tables.health_age_max))
    care = social & (age >= CARE_AGE[0]) & (age <= CARE_AGE[1])
    return Enrollment(social=social, employment=employment, taxed=emp_like, no_basis=emp_like & ~known, care=care,
                      pension=pension, age=age)


# ================================================================ 天引き(1 か月分)
@dataclass(frozen=True)
class Deductions:
    """1 回の給料日の天引き(行ごとの円)。``employee``/``employer`` は項目 → 配列。"""

    employee: Mapping[str, np.ndarray]
    employer: Mapping[str, np.ndarray]
    over_gross: np.ndarray
    enrollment: Enrollment
    #: 〔第 4 期 4-2b〕住民税の非課税の行(``None``=4-2 の値)。
    resident_exempt: np.ndarray | None = None

    @property
    def employee_total(self) -> np.ndarray:
        return sum((np.asarray(v, dtype=np.int64) for v in self.employee.values()),
                   np.zeros(self.over_gross.shape, dtype=np.int64))

    @property
    def employer_total(self) -> np.ndarray:
        return sum((np.asarray(v, dtype=np.int64) for v in self.employer.values()),
                   np.zeros(self.over_gross.shape, dtype=np.int64))


def deductions(gross: np.ndarray, tables: PayrollTables, enroll: Enrollment) -> Deductions:
    """給料日の天引き(本人の分 6 項目と雇用主の分 4 項目・〔4-2b〕5 項目=子ども・子育て拠出金)。

    社会保険(健保+介護・支援金・厚年)は報酬月額=今月の額面で標準報酬月額を決める(定時決定と「前月分を控除」の時期は答申に
    無い・今月の額面で代える=未リサーチ(expedient)・台帳 ``DOC-rules42-standard-remuneration-month``)。雇用保険=額面 × 率。
    源泉所得税=額面 − 本人の社会保険料等の残りに特例の式。住民税=:func:`resident_tax_monthly`。本人の社会保険料等が額面を
    超える行は何も天引きしない(``over_gross``・計器)。本人の分の合計が額面を超えないように住民税を削る。

    〔第 4 期 4-2b〕厚年は ``enroll.pension``(70 歳未満)だけ・子ども・子育て拠出金=厚年の標準報酬月額 × 率(事業主だけ・
    1 円未満の切り捨て=雇用主の分の既存の形)・住民税は基礎控除・調整控除・非課税(``enroll.age``)を入れた値。
    """
    g = np.maximum(np.asarray(gross, dtype=np.int64), 0)
    z = np.zeros(g.shape, dtype=np.int64)
    emp = {k: z.copy() for k in EMPLOYEE_ITEMS}
    er = {k: z.copy() for k in tables.employer_items}
    soc = np.asarray(enroll.social, dtype=bool)
    pen = soc if enroll.pension is None else np.asarray(enroll.pension, dtype=bool)
    if tables.health is not None and soc.any():
        std = standard_monthly(g, tables.health_grades)
        rate = _frac(tables.health.params["rate"])
        care = _frac(tables.health.params["care_rate_age_40_64"])
        for mask, r in ((soc & ~enroll.care, rate), (soc & enroll.care, rate + care)):  # 逐次: 2 通り
            if mask.any():
                e, c = _half_share(std[mask], r)
                emp["health"][mask], er["health"][mask] = e, c
        if tables.child_support is not None:
            e, c = _half_share(std[soc], _frac(tables.child_support.params["rate"]))
            emp["child_support"][soc], er["child_support"][soc] = e, c
    if tables.pension is not None and pen.any():
        std_p = standard_monthly(g[pen], tables.pension_grades)
        e, c = _half_share(std_p, _frac(tables.pension.params["rate"]))
        emp["pension"][pen], er["pension"][pen] = e, c
        if tables.child_care is not None:  # 〔4-2b〕子ども・子育て拠出金(事業主だけ・切り捨て)
            cr = _frac(tables.child_care.params["rate"])
            er["child_care_contribution"][pen] = (std_p * int(cr.numerator)) // int(cr.denominator)
    em = np.asarray(enroll.employment, dtype=bool)
    if tables.employment is not None and em.any():
        re_ = _frac(tables.employment.params["employee_rate"])
        rr = _frac(tables.employment.params["employer_rate"])
        emp["employment"][em] = share_50sen(g[em] * int(re_.numerator), int(re_.denominator))
        er["employment"][em] = (g[em] * int(rr.numerator)) // int(rr.denominator)
    si = emp["health"] + emp["child_support"] + emp["pension"] + emp["employment"]
    over = si > g
    taxed = np.asarray(enroll.taxed, dtype=bool) & ~over
    emp["income_tax"][taxed] = income_tax_withholding(g[taxed] - si[taxed], tables)
    rt, exempt = _resident_tax(g, tables, si, enroll.age)
    room = np.maximum(g - si - emp["income_tax"], 0)
    emp["resident_tax"][taxed] = np.minimum(rt[taxed], room[taxed])
    for k in EMPLOYEE_ITEMS:  # 逐次: 項目の数
        emp[k][over] = 0
    for k in er:
        er[k][over] = 0
    return Deductions(employee=emp, employer=er, over_gross=over, enrollment=enroll,
                      resident_exempt=(exempt & taxed) if tables.r42b else None)


# ================================================================ 消費税(端数・期限・軽減税率)
def invoice_rounding(asof: "str | _dt.date", rules: Any = None) -> dict[str, Any]:
    """レジの税の端数の決まり(1 枚の適格請求書につき税率ごとに 1 回・方法は任意・商品ごとは不可=問 57)。

    今のレジは 1 回の購入=1 枚のレシート=1 つの税率で、方法は切り捨てを選んだ(未リサーチ(expedient)・方法は任意の中から)。
    行が無い日は ``{"rule": "none"}``。
    """
    row = _row(INVOICE_RULE_ID, asof, rules)
    if row is None:
        return {"rule": "none"}
    if bool(row.params.get("per_item_rounding_allowed", False)):
        raise ValueError("規則の表の端数の行が商品ごとの端数を許している(レジの 1 枚 1 回の前提と違う)")
    return {"rule": _src(row), "unit": "1 回の購入=1 枚のレシート=1 つの税率ごとに 1 回", "method": "切り捨て"}


def filing_deadline(period_year: int, rules: Any = None) -> tuple[_dt.date | None, str]:
    """課税期間 ``period_year``(暦年)の消費税の申告と納付の期限と出どころ(課税期間の末日に効いている版)。

    店の課税期間は全部「暦年」・期限は個人事業者の決まり(翌年 3 月 31 日)で代える(法人か個人か・事業年度は資料なし=
    未リサーチ(expedient)・台帳 ``DOC-rules42-tax-deadline``)。中間申告と、期限が土日祝に当たるときの扱いは入れていない。
    行が無い(課税期間の末日に版が無い)ときは ``(None, "none")``=納付しない(預かり金に積んだまま)。
    """
    end = _dt.date(int(period_year), 12, 31)
    row = _bridge_row(DEADLINE_RULE_ID, end, rules)  # 〔検収 L1〕human の行をつなぎとして読む
    if row is None:
        return None, "none"
    p = row.params
    return _dt.date(int(period_year) + 1, int(p["sole_proprietor_due_month"]), int(p["sole_proprietor_due_day"])), _src(row)


def reduced_rate(asof: "str | _dt.date", rules: Any = None) -> tuple[Fraction, str]:
    """軽減税率(国 6.24%+地方 22/78=8%)の率と出どころ(器=呼び手なし。品目の段と店内か持ち帰りかの申告の後に使う)。"""
    row = _row(REDUCED_RULE_ID, asof, rules)
    if row is None:
        return Fraction(0), "none"
    nat = _frac(row.params["national_rate"])
    loc = row.params["local_tax_ratio"]
    rate = nat * (1 + Fraction(int(loc[0]), int(loc[1])))
    if rate != _frac(row.params["combined_rate"]):
        raise ValueError(f"規則の表の軽減税率が合わない: {rate} と combined_rate {row.params['combined_rate']}")
    return rate, _src(row)


# ================================================================ 信用の上限・割増(器)
def total_volume_cap(asof: "str | _dt.date", rules: Any = None) -> dict[str, Any] | None:
    """総量規制(貸金業法 13 条の 2 第 2 項・13 条 3 項)の値: 年収の割合・収入の書類が要る額(1 社・全体)。無ければ ``None``。"""
    row = _row(TOTAL_VOLUME_RULE_ID, asof, rules)
    if row is None:
        return None
    r = row.params["cap_ratio_of_annual_income"]
    return {"ratio": Fraction(int(r[0]), int(r[1])),
            "document_over_single": int(row.params["income_document_required_over_yen_single_lender"]),
            "document_over_all": int(row.params["income_document_required_over_yen_all_lenders"]), "source": _src(row)}


def interest_cap(asof: "str | _dt.date", rules: Any = None) -> dict[str, Any] | None:
    """利息制限法 1 条の上限(``bands``=元本の帯 (下限, 上限(含まない)・None=なし, 年率) の並び・``source``)。無ければ ``None``。"""
    row = _row(INTEREST_RULE_ID, asof, rules)
    if row is None:
        return None
    bands = tuple((int(b["principal_from"]), None if b["principal_to_excl"] is None else int(b["principal_to_excl"]),
                   _frac(b["annual_rate"])) for b in row.params["rate_cap"])
    return {"bands": bands, "source": _src(row)}


def overtime_premium(asof: "str | _dt.date", rules: Any = None) -> dict[str, Any] | None:
    """時間外の割増の率の範囲(労基法 37 条 1 項=2 割 5 分以上 5 割以下の範囲で政令の率以上・月 60 時間超は 5 割以上)。

    器(呼び手なし=勤務の記録の時間外が出る段の後)。政令の率と深夜の率は答申で未確認=返さない。無ければ ``None``。
    """
    row = _row(OVERTIME_RULE_ID, asof, rules)
    if row is None:
        return None
    lo, hi = row.params["overtime_min_rate_range"]
    return {"min_rate_range": (_frac(lo), _frac(hi)), "over_60h_min_rate": _frac(row.params["over_60h_per_month_min_rate"]),
            "source": _src(row)}
