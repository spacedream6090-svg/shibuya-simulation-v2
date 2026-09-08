"""economy.anchors — §2.5 の**金額アンカー**(公的値・mechanism)と初期財布/月次賃金。

正典(境界・経済設計書 §2.5「金額アンカー(公的値・mechanism)」)
| 量 | 値 | 出典 |
- 世帯消費支出: 二人以上 314,001円/月(≈10,300円/日)・単身 173,042円/月(≈5,700円/日)・
  総世帯 259,880円/月 — 家計調査2025年平均(実読)
- 消費性向・黒字率: 勤労者世帯(二人以上)65.0%/35.0%・預貯金純増 177,061円/月 — 同上
- 来街者持込(上限側目安): 訪日客の滞在中消費 7.1万円 — 東京観光財団R5(実読)
- 賃金フロア: 東京都最低賃金 1,226円/時(R7.10.3) — 台東区公式(実読)
- 店舗の売上規模(区・1事業所あたり年商): 宿泊飲食 8,532万円・卸小売 1億3,152万円・
  生活関連娯楽 2,253万円 — 経済センサス2021活動調査(e-Stat API・親取得09-07)
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
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Final, Mapping

import numpy as np

from shibuya.economy.accounts import AccountCode, Sector

__all__ = [
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
SALES_PER_ESTABLISHMENT: Final[Mapping[str, int]] = {
    "宿泊・飲食": 85_320_000,
    "卸売・小売": 131_520_000,
    "生活関連・娯楽": 22_530_000,
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
           "経済センサス2021活動調査 渋谷区 卸売・小売: 6,311事業所・98,856人"),
    Anchor("sales_life_leisure", SALES_PER_ESTABLISHMENT["生活関連・娯楽"], "円/年/事業所",
           "経済センサス2021活動調査 渋谷区 生活関連・娯楽: 2,286事業所"),
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


#: 種別 → 1日あたり消費支出[円](expedient な写像)。
DAILY_SPENDING_BY_KIND: Final[tuple[int, ...]] = (
    SPEND_SINGLE_PER_DAY,  # 通勤者(単身相当)
    VISITOR_CARRY_IN // 5,  # 来街者(滞在中消費 7.1万円 ÷ 5 = 1日相当の目安)
    SPEND_SINGLE_PER_DAY,  # 従業者
    SPEND_MULTI_PERSON_PER_DAY,  # 居住者(二人以上相当)
    SPEND_SINGLE_PER_DAY,  # 指令
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


def monthly_wage_amounts(hours: np.ndarray, premium: float = 1.0) -> np.ndarray:
    """月次賃金[円] = 労働時間 × 最低賃金 × 割増係数(外生・§2.7 第1陣)。"""
    h = np.asarray(hours, dtype=np.float64).ravel()
    return np.rint(h * float(MIN_WAGE_HOURLY) * float(premium)).astype(np.int64)


def monthly_wages(
    ledger,
    employers: np.ndarray,
    households: np.ndarray,
    hours: np.ndarray,
    tick: int,
    *,
    premium: float = 1.0,
    from_row: bool = False,
) -> np.ndarray:
    """雇用主(または域外雇用主)→ 世帯の月次賃金を**一括** transfer する。

    Args:
        ledger: ``economy.ledger.Ledger``。
        employers: 支払側の索引(``from_row=True`` なら無視され 0 に置かれる)。
        households: 受取側の世帯 id。
        hours: 月間労働時間。
        tick: 現在 tick。
        premium: 最低賃金への割増係数(expedient)。
        from_row: True なら域外雇用主(faucet)。

    Returns:
        行ごとの ``TransferStatus``。
    """
    amounts = monthly_wage_amounts(hours, premium)
    hh = np.asarray(households, dtype=np.int64).ravel()
    if from_row:
        payers = np.zeros(hh.size, dtype=np.int64)
        payer_sector = int(Sector.ROW)
    else:
        payers = np.asarray(employers, dtype=np.int64).ravel()
        payer_sector = int(Sector.EMPLOYER)
    return ledger.transfer_many(
        payer_sector, payers, int(Sector.HOUSEHOLD), hh, amounts,
        int(AccountCode.WAGE), tick,
    )
