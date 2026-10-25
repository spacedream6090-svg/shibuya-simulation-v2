"""economy.anchors — §2.5 の**金額アンカー**(公的値・mechanism)と初期財布/月次賃金。

正典(境界・経済設計書 §2.5「金額アンカー(公的値・mechanism)」)
| 量 | 値 | 出典 |
- 世帯消費支出: 二人以上 314,001円/月(≈10,300円/日)・単身 173,042円/月(≈5,700円/日)・
  総世帯 259,880円/月 — 家計調査2025年平均(実読)
- 消費性向・黒字率: 勤労者世帯(二人以上)65.0%/35.0%・預貯金純増 177,061円/月 — 同上
- 来街者持込(上限側目安): 訪日客の滞在中消費 7.1万円 — 東京観光財団R5(実読)
- 賃金フロア: 東京都最低賃金 1,226円/時(R7.10.3) — 台東区公式(実読)
- 店舗の売上規模(区・1事業所あたり年商): 宿泊飲食 8,532万円・卸小売 13億1,523万円・
  生活関連娯楽 2億2,527万円 — 経済センサス2021活動調査(e-Stat API・親取得09-07)
  (D-16 訂正・小さいもの③: 卸小売と生活関連娯楽は旧版が生値の 1/10=末尾 1 桁落ちの転記だった)
- 従業者総数(区): 516,541人(2021)/民営事業所 27,624 — 同上
世界過程設計書 §7.1 + パターン台帳 W1
- 廃棄 sink の band: 渋谷区 令和6年度ごみ 43,663 t/年度 = **119.6 t/日**(区ポータル・親実読)

逐次ループ宣言(P4): なし(``initial_wallets`` は NumPy のベクトル生成のみ)。

expedient(本モジュール分)
- 個体種別 → 1日あたり消費支出の写像(``DAILY_SPENDING_BY_KIND``)。家計調査は世帯の
  ライフステージ別であって「通勤者/来街者/従業者/居住者」ではない。
- 初期財布の分布形 = **対数正規**(中央値 = 日消費 × 3 日ぶん・σ=0.6)。§2.6 が
  「財布の現金初期分布」を expedient に挙げている通り、分布形の出典は無い。
- 月次賃金 = 労働時間 × 最低賃金 × 割増係数(既定 1.0)。設計書 §2.7 は「賃金=雇用主から
  月次(外生)」としか言わない。賃金の分布・割増の根拠は空欄。
- ``WalletKind`` の数値は ``shibuya.agents.state.AgentKind`` と同じ並びだが、層契約により
  economy から agents を import できないので**値を写して**持つ
  (``tests/economy/test_anchors.py::test_wallet_kind_matches_agent_kind`` が一致を強制)。

〔第 2 期 2-1〕規則の表(``engine.rules.table``・``docs/design/rules-table.json``)の最初の読み手: ``min_wage_hourly(asof)``
(東京都の最低賃金=``minimum_wage.tokyo`` の ``yen_per_hour``・その日に効いている版。表に版の無い日=2026-10-01 より前は
直書きの ``MIN_WAGE_HOURLY``=1,226 円(R7.10.3)に戻す=つなぎの台帳 ``BR-MIN-WAGE-HOURLY-1226``・外す段 4-2)と
``consumption_tax_rate(asof)``(``consumption_tax.standard_rate`` の国+地方の合計の率を分数で)。``monthly_wage_amounts``
は時給 ``hourly`` を渡せる(既定は今までどおり ``MIN_WAGE_HOURLY``=既存の呼び手と試験の値は不変)。
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from enum import IntEnum
from fractions import Fraction
from typing import Final, Mapping

import numpy as np

from shibuya.economy.accounts import AccountCode, Sector

__all__ = [
    "MIN_WAGE_RULE_ID",
    "CONSUMPTION_TAX_RULE_ID",
    "min_wage_hourly",
    "min_wage_floor",
    "consumption_tax_rate",
    "Anchor",
    "ANCHORS",
    "SPEND_MULTI_PERSON_PER_DAY",
    "SPEND_SINGLE_PER_DAY",
    "SPEND_TOTAL_PER_MONTH",
    "CONSUMPTION_PROPENSITY",
    "SAVINGS_PER_MONTH",
    "VISITOR_CARRY_IN",
    "MIN_WAGE_HOURLY",
    "SALES_PER_ESTABLISHMENT",
    "EMPLOYEES_SHIBUYA",
    "ESTABLISHMENTS_SHIBUYA",
    "WASTE_TONNES_PER_DAY",
    "WASTE_TONNES_PER_YEAR",
    "WASTE_BAND_RATIO",
    "WalletKind",
    "DAILY_SPENDING_BY_KIND",
    "WALLET_DAYS",
    "WALLET_SIGMA",
    "initial_wallets",
    "monthly_wage_amounts",
    "monthly_wages",
]


@dataclass(frozen=True)
class Anchor:
    """1つの現実整合アンカー(値+単位+出典文字列+等級)。"""

    key: str
    value: float
    unit: str
    source: str
    grade: str = "A"  # 公的統計の直接値 = A


# ---------------------------------------------------------------- 家計(家計調査2025)
#: 二人以上世帯の消費支出[円/日](314,001円/月 ÷ 30.44)。
SPEND_MULTI_PERSON_PER_DAY: Final[int] = 10_300
#: 単身世帯の消費支出[円/日](173,042円/月)。
SPEND_SINGLE_PER_DAY: Final[int] = 5_700
#: 総世帯の消費支出[円/月]。
SPEND_TOTAL_PER_MONTH: Final[int] = 259_880
#: 勤労者世帯(二人以上)の消費性向。
CONSUMPTION_PROPENSITY: Final[float] = 0.650
#: 預貯金純増[円/月](退蔵率の基準)。
SAVINGS_PER_MONTH: Final[int] = 177_061
#: 訪日客の滞在中消費[円](上限側目安・来街者持込の較正材料)。
VISITOR_CARRY_IN: Final[int] = 71_000
#: 東京都最低賃金[円/時](R7.10.3)。
MIN_WAGE_HOURLY: Final[int] = 1_226

# ---------------------------------------------------------------- 事業所(経済センサス2021)
#: 大分類 → 1事業所あたり年商[円/年](渋谷区)。
#: 出典の行: 令和3年経済センサス‐活動調査 事業所に関する集計 産業横断的集計 表 2-1(e-Stat 統計表 0004006322)
#: 表章項目 156-2021「1事業所当たり売上(収入)金額」[万円]・area 13113(渋谷区)・経営組織 cat02=0(総数)・
#: 産業大分類 cat01 = M / I / N の値 8,532 / 131,523 / 22,527 万円 × 10,000。
#: **D-16 訂正(小さいもの③)**: 旧版は I=131,520,000・N=22,530,000(=生値の 1/10・「1億3,152万」「2,253万」の
#: 末尾 1 桁落ちの転記)。M は 4 桁なので一致していた。``entry_capital.SALES_PER_ESTABLISHMENT_BY_INDUSTRY``
#: (生値)と同じ値になった。**ランは読まない**(照合の物差しだけ=``ANCHORS`` の表)。
SALES_PER_ESTABLISHMENT: Final[Mapping[str, int]] = {
    "宿泊・飲食": 85_320_000,
    "卸売・小売": 1_315_230_000,
    "生活関連・娯楽": 225_270_000,
}
#: 渋谷区の従業者総数(民営事業所・2021)。
EMPLOYEES_SHIBUYA: Final[int] = 516_541
#: 渋谷区の民営事業所数(2021)。
ESTABLISHMENTS_SHIBUYA: Final[int] = 27_624

# ---------------------------------------------------------------- 廃棄(区ポータル・W1)
#: 渋谷区のごみ[t/日](令和6年度 43,663 t/年度 ÷ 365)。
WASTE_TONNES_PER_DAY: Final[float] = 119.6
#: 渋谷区のごみ[t/年度](可燃 40,810 / 不燃 1,433 / 粗大 1,421)。
WASTE_TONNES_PER_YEAR: Final[int] = 43_663
#: band の幅(±30%・expedient。設計書は「band」としか言っていない)。
WASTE_BAND_RATIO: Final[float] = 0.30

#: 出典文字列つきのアンカー表(センサス出力・検収パックに貼る)。
ANCHORS: Final[tuple[Anchor, ...]] = (
    Anchor("household_spend_multi_per_day", SPEND_MULTI_PERSON_PER_DAY, "円/日",
           "家計調査2025年平均: 二人以上世帯 314,001円/月(実読)"),
    Anchor("household_spend_single_per_day", SPEND_SINGLE_PER_DAY, "円/日",
           "家計調査2025年平均: 単身世帯 173,042円/月(実読)"),
    Anchor("household_spend_total_per_month", SPEND_TOTAL_PER_MONTH, "円/月",
           "家計調査2025年平均: 総世帯 259,880円/月(実読)"),
    Anchor("consumption_propensity", CONSUMPTION_PROPENSITY, "比",
           "家計調査2025: 勤労者世帯(二人以上)消費性向 65.0%/黒字率 35.0%"),
    Anchor("savings_per_month", SAVINGS_PER_MONTH, "円/月",
           "家計調査2025: 預貯金純増 177,061円/月(退蔵率の基準)"),
    Anchor("visitor_carry_in", VISITOR_CARRY_IN, "円/滞在",
           "東京観光財団R5 渋谷調査: 訪日客の滞在中消費 7.1万円(範囲定義は不明瞭)"),
    Anchor("min_wage_hourly", MIN_WAGE_HOURLY, "円/時",
           "東京都最低賃金 1,226円/時(R7.10.3・台東区公式で実読)"),
    Anchor("sales_lodging_food", SALES_PER_ESTABLISHMENT["宿泊・飲食"], "円/年/事業所",
           "経済センサス2021活動調査 渋谷区 宿泊・飲食: 3,366事業所・従業者41,530"),
    Anchor("sales_wholesale_retail", SALES_PER_ESTABLISHMENT["卸売・小売"], "円/年/事業所",
           "経済センサス2021活動調査 渋谷区 卸売・小売: 6,311事業所・98,856人・1事業所当たり 131,523万円"
           "(表 0004006322・156-2021・D-16 訂正)"),
    Anchor("sales_life_leisure", SALES_PER_ESTABLISHMENT["生活関連・娯楽"], "円/年/事業所",
           "経済センサス2021活動調査 渋谷区 生活関連・娯楽: 2,286事業所・1事業所当たり 22,527万円"
           "(表 0004006322・156-2021・D-16 訂正)"),
    Anchor("employees_shibuya", EMPLOYEES_SHIBUYA, "人",
           "e-Stat API(親取得09-07): 渋谷区 民営事業所27,624・従業者516,541人(2021)"),
    Anchor("waste_tonnes_per_day", WASTE_TONNES_PER_DAY, "t/日",
           "渋谷区 令和6年度ごみ 43,663 t/年度(可燃40,810/不燃1,433/粗大1,421)=119.6 t/日"),
)


class WalletKind(IntEnum):
    """財布の初期化に使う個体種別(``agents.state.AgentKind`` と**同じ値**・写し)。"""

    COMMUTER = 0  # 通勤者
    VISITOR = 1  # 来街者
    WORKER = 2  # 従業者
    RESIDENT = 3  # 居住者
    DISPATCHER = 4  # 指令
    STUDENT = 5  # 通学者(W16)
    REGULAR_VISITOR = 6  # 定期来街者(W16)
    FOREIGN_VISITOR = 7  # 訪日来街者(W16)
    CREW = 8  # 乗務員・職務者(W16)


#: 種別 → 1日あたり消費支出[円](expedient な写像)。
DAILY_SPENDING_BY_KIND: Final[tuple[int, ...]] = (
    SPEND_SINGLE_PER_DAY,  # 通勤者(単身相当)
    VISITOR_CARRY_IN // 5,  # 来街者(滞在中消費 7.1万円 ÷ 5 = 1日相当の目安)
    SPEND_SINGLE_PER_DAY,  # 従業者
    SPEND_MULTI_PERSON_PER_DAY,  # 居住者(二人以上相当)
    SPEND_SINGLE_PER_DAY,  # 指令
    # --- C5(W16)で足した種別。公的アンカーが別に無いので既存行の写し(expedient)---
    SPEND_SINGLE_PER_DAY,  # 通学者(単身相当・扶養関係は表現しない)
    VISITOR_CARRY_IN // 5,  # 定期来街者(来街者と同じ)
    VISITOR_CARRY_IN // 5,  # 訪日来街者(アンカーは訪日客 7.1 万円/滞在そのもの)
    SPEND_SINGLE_PER_DAY,  # 乗務員・職務者
)
#: 初期財布 = 日消費 × この日数(expedient)。
WALLET_DAYS: Final[float] = 3.0
#: 対数正規の σ(expedient)。
WALLET_SIGMA: Final[float] = 0.6
#: 財布の下限・上限[円](expedient・外れ値で int32 を溢れさせない)。
WALLET_MIN: Final[int] = 1_000
WALLET_MAX: Final[int] = 2_000_000


def daily_spending(kinds: np.ndarray) -> np.ndarray:
    """種別配列 → 1日あたり消費支出[円]。"""
    k = np.clip(np.asarray(kinds, dtype=np.int64), 0, len(DAILY_SPENDING_BY_KIND) - 1)
    return np.asarray(DAILY_SPENDING_BY_KIND, dtype=np.int64)[k]


def initial_wallets(n: int, kinds: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """初期財布[円]を対数正規で引く(expedient・§2.6「財布の現金初期分布」)。

    中央値 = 種別ごとの日消費 × ``WALLET_DAYS``。``rng`` は ``core.rng.stream`` の
    Generator を渡す(決定論)。

    Example:
        >>> from shibuya.core.rng import stream
        >>> w = initial_wallets(4, np.zeros(4, int), stream(1, "economy.wallet"))
        >>> bool((w >= WALLET_MIN).all())
        True
    """
    n = int(n)
    median = daily_spending(np.asarray(kinds)[:n]).astype(np.float64) * float(WALLET_DAYS)
    draw = median * np.exp(rng.normal(0.0, float(WALLET_SIGMA), size=n))
    return np.clip(np.rint(draw), WALLET_MIN, WALLET_MAX).astype(np.int64)


#: 〔2-1〕規則の表の行の id(東京都の最低賃金・消費税の標準税率)。
MIN_WAGE_RULE_ID: Final[str] = "minimum_wage.tokyo"
CONSUMPTION_TAX_RULE_ID: Final[str] = "consumption_tax.standard_rate"


def min_wage_hourly(asof: "str | _dt.date", rules=None) -> tuple[int, str]:  # noqa: ANN001
    """〔2-1〕``asof`` の日に効いている東京都の最低賃金[円/時]と出どころ(規則の表の最初の読み手)。

    表に版がある日(2026-10-01 以後)は規則の表の ``yen_per_hour``(1,280 円)・版の無い日(施行の前)は直書きの
    ``MIN_WAGE_HOURLY``(1,226 円=R7.10.3・つなぎの台帳 ``BR-MIN-WAGE-HOURLY-1226``)に戻す。表のファイルが無い写しも
    直書きに戻す。

    Returns:
        ``(円/時, 出どころ)``(出どころは ``"rules:<id>@<asof>"`` か ``"anchors.MIN_WAGE_HOURLY"``)。
    """
    from shibuya.engine.rules import table as _RT

    try:
        rt = _RT.default_rules() if rules is None else rules
        row = rt.get(MIN_WAGE_RULE_ID, asof)
    except (_RT.RuleNotInForce, FileNotFoundError, KeyError):
        return int(MIN_WAGE_HOURLY), "anchors.MIN_WAGE_HOURLY"
    return int(row.params["yen_per_hour"]), f"rules:{MIN_WAGE_RULE_ID}@{row.asof}"


def min_wage_floor(asof: "str | _dt.date", rules=None) -> tuple[int | None, str]:  # noqa: ANN001
    """〔賃金の小さな版上げ・検収 M1〕最低賃金法の床(4 条 2 項)の値[円/時]と出どころ=規則の表の ``minimum_wage.tokyo``
    (``kind: machine``)の ``asof`` の日に効いている版だけ。:func:`min_wage_hourly` と違い**直書きの値に戻さない**: 表に版の
    無い日(施行の前)・表の無い写しは ``(None, "none")``=床なし(宣言=記録 wage_occ §13)。machine でない行は止める。
    """
    from shibuya.engine.rules import table as _RT

    try:
        rt = _RT.default_rules() if rules is None else rules
        row = rt.get(MIN_WAGE_RULE_ID, asof)
    except (_RT.RuleNotInForce, FileNotFoundError, KeyError):
        return None, "none"
    if str(getattr(row, "kind", "machine")) != "machine":
        raise ValueError(f"{MIN_WAGE_RULE_ID} は machine の行であること(いま {row.kind!r})")
    return int(row.params["yen_per_hour"]), f"rules:{MIN_WAGE_RULE_ID}@{row.asof}"


def consumption_tax_rate(asof: "str | _dt.date", rules=None) -> tuple[Fraction, str]:  # noqa: ANN001
    """〔2-1〕``asof`` の日に効いている消費税の国+地方の合計の率(分数)と出どころ。

    率は表の ``national_rate``(7.8%)× (1 + 地方の比 22/78)=10%(表の ``combined_rate`` と同じことを確かめる)。
    表に版の無い日・表の無い写しは率 0(=税を取らない)と出どころ ``"none"``。
    """
    from shibuya.engine.rules import table as _RT

    try:
        rt = _RT.default_rules() if rules is None else rules
        row = rt.get(CONSUMPTION_TAX_RULE_ID, asof)
    except (_RT.RuleNotInForce, FileNotFoundError, KeyError):
        return Fraction(0), "none"
    nat = Fraction(str(row.params["national_rate"]))
    loc = row.params["local_tax_ratio"]
    rate = nat * (1 + Fraction(int(loc[0]), int(loc[1])))
    if rate != Fraction(str(row.params["combined_rate"])):
        raise ValueError(f"規則の表の消費税の率が合わない: {rate} と combined_rate {row.params['combined_rate']}")
    return rate, f"rules:{CONSUMPTION_TAX_RULE_ID}@{row.asof}"


def monthly_wage_amounts(hours: np.ndarray, premium: float = 1.0, *, hourly=None) -> np.ndarray:  # noqa: ANN001
    """月次賃金[円] = 労働時間 × 時給 × 割増係数(外生・§2.7 第1陣)。

    〔2-1〕``hourly``(円/時・スカラーか体ごとの配列)を渡せる。既定 ``None`` は ``MIN_WAGE_HOURLY``(今までどおり)。
    """
    h = np.asarray(hours, dtype=np.float64).ravel()
    w = float(MIN_WAGE_HOURLY) if hourly is None else np.asarray(hourly, dtype=np.float64)
    return np.rint(h * w * float(premium)).astype(np.int64)


def monthly_wages(
    ledger,
    employers: np.ndarray,
    households: np.ndarray,
    hours: np.ndarray,
    tick: int,
    *,
    premium: float = 1.0,
    from_row: bool = False,
    hourly=None,  # noqa: ANN001
    payer_sector: int | None = None,
    method: int = 0,
    cause=None,  # noqa: ANN001
    amounts=None,  # noqa: ANN001
) -> np.ndarray:
    """雇用主(または域外雇用主)→ 世帯の月次賃金を**一括** transfer する。

    〔第 2 期 2-1〕経済の段階 2 の給料日(``economy.stage2.MoneyStage2.payroll``)が最初の呼び手。``hourly``(時給=規則の表の
    最低賃金)・``payer_sector``(雇用主か店=店の担当従業者)・``method``(口座=世帯の銀行預金へ)・``cause``(過程 payroll)
    を渡せる。既定は今までどおり(雇用主から現金・``MIN_WAGE_HOURLY``)。

    Args:
        ledger: ``economy.ledger.Ledger``。
        employers: 支払側の索引(``from_row=True`` なら無視され 0 に置かれる)。
        households: 受取側の世帯 id。
        hours: 月間労働時間。
        tick: 現在 tick。
        premium: 最低賃金への割増係数(expedient)。
        from_row: True なら域外雇用主(faucet)。
        hourly: 時給(円/時・スカラーか行ごと)。``None``=``MIN_WAGE_HOURLY``。
        payer_sector: 支払側の部門(``None``=雇用主。``from_row`` が優先)。
        method: 支払いの方法(``ops.METHOD_CASH``=0・``ops.METHOD_ACCOUNT``=1=世帯の口座へ)。
        cause: 1-3 の原因(``None``=出来事を書かない)。
        amounts: 〔賃金の小さな版上げ〕行ごとの額[円](渡せば ``hours``・``hourly``・``premium`` は使わない=賃金の腕
            ``occupation`` の月の賃金=``economy.wages``)。``None``=今までどおり 時間 × 時給 × 割増。

    Returns:
        行ごとの ``TransferStatus``。
    """
    if amounts is None:
        amounts = monthly_wage_amounts(hours, premium, hourly=hourly)
    else:
        amounts = np.asarray(amounts, dtype=np.int64).ravel()
    hh = np.asarray(households, dtype=np.int64).ravel()
    if from_row:
        payers = np.zeros(hh.size, dtype=np.int64)
        payer_sector = int(Sector.ROW)
    else:
        payers = np.asarray(employers, dtype=np.int64).ravel()
        payer_sector = int(Sector.EMPLOYER) if payer_sector is None else int(payer_sector)
    if int(method) == 0 and cause is None:  # 今までの呼び方(引数を足さない=値は不変)
        return ledger.transfer_many(
            payer_sector, payers, int(Sector.HOUSEHOLD), hh, amounts,
            int(AccountCode.WAGE), tick,
        )
    return ledger.transfer_many(
        payer_sector, payers, int(Sector.HOUSEHOLD), hh, amounts,
        int(AccountCode.WAGE), tick, method=int(method), cause=cause,
    )
