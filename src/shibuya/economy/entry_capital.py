"""economy.entry_capital — 店舗の**参入資本を経済センサスから按分**する(D-13・C5)。

正典
- 境界・経済設計書 §2.3「**ex nihilo 禁止**: 参入時の初期資本は創業者預金・銀行貸出・
  外界からの transfer 由来のみ」→ 注入は今までどおり ``Ledger.endow_stores``
  (外界 → 店舗・科目 ``ENTRY_CAPITAL``)。**本モジュールは金額を決めるだけ**で、
  残高の直接代入はしない。
- 同 §2.5「店舗の売上規模(大分類・区レベル)= 経済センサス2021活動調査」。
- PENDING D-13「店舗参入資本 200,000 円×2,337 店=467.4M 円=貨幣供給の 93%(expedient)
  → C5 で経済センサス『1 事業所当たり売上』から按分に置換(設計側の指示)」。

**原理**(1 行)::

    参入資本[円/店] = 1事業所当たり年商(産業大分類) ÷ 365 × 運転資金日数 k × 原価率 × 母集団比

- **1事業所当たり年商**: 経済センサス2021活動調査(令和3年)・渋谷区(13113)・表章項目
  ``156-2021``「1事業所当たり売上(収入)金額」[万円]・経営組織=総数。
  出典ファイル: ``data/realworld/estat/経済センサス2021_事業所ベース_産業大分類_従業者売上_渋谷区.json``
  (e-Stat GET_STATS_DATA・親取得 2026-09-07)。**値は本モジュールに転記**する
  (``data/`` は gitignore 下=CI から読めない。``anchors`` と同じ扱い)。
- **運転資金日数 k**: 参入資本が食われる先は域外仕入(納品・補充)なので、資本は
  「k 日ぶんの仕入」を賄えればよい。k は設計書に無い=**expedient(既定 30 日)**。
- **原価率**: 域外仕入は**標準原価**(価格 ÷ 内生フロア k・§8 H-2)で払う
  (``goods.receive_delivery``)。よって必要額は年商ではなく**年商×原価率**。
  原価率は ``goods.CATEGORY_K``(コンビニ 5.0/飲食 3.3/物販 2.9)の逆数
  =20%/30%/35%(既存の決定項の再利用・新しい定数を置かない)。
- **母集団比**: n 体のランは実人口の n/400,000 の需要しか流さない(``engine.arbiter``
  の L4 予算が ``n/L4_REFERENCE_AGENTS`` で按分するのと同じ規約)。実スケールの
  運転資金をそのまま入れると 5,000 体のランで店舗現金が貨幣供給の 99.9% を占める。

**親判断待ち(本モジュールでは解決しない)**
1. **``anchors.SALES_PER_ESTABLISHMENT`` は I(卸売・小売)と N(生活関連・娯楽)が
   10 分の 1**。センサス ``156-2021`` の生値は I=131,523 万円・N=22,527 万円
   (=13億1,523万円・2億2,527万円)だが、設計書 §2.5 と ``anchors`` は
   「1億3,152万円」「2,253万円」=**末尾 1 桁が落ちた転記**になっている
   (M 宿泊・飲食 8,532 万円は 4 桁なので影響なし=一致)。本モジュールは**生値**を使う。
   設計書・``anchors`` は決定項なので書き換えていない。
2. **中分類が無い**。I は卸売業と小売業の合算で、POI の ``shop``(小売の店構え)に
   卸売の年商が混ざる。区レベルの中分類別売上は e-Stat のこの表に無い(大分類まで)。
3. **町丁目別が無い**。この表は区計 1 行(``area`` は 13113 の 1 値)。POI ごとの立地差
   (駅前/裏通り)は按分に入らない。
4. **売上が公表されない大分類がある**: D 建設・F 電気ガス・G/G1 情報通信・H 運輸・
   J 金融保険・O/O1 教育(学校)・Q/Q1 複合サービス・R/R1 は ``･･･``(調査していないもの)、
   Q2 は ``X``(秘匿)。``office`` を G(情報通信)へ寄せられないのはこのため
   (G2 情報サービス業だけは公表=1,231,510,000 円/年)。

expedient(本モジュール分・登録簿 §8 の C5 経済節へ登録)
- 運転資金日数 ``WORKING_CAPITAL_DAYS`` = 30 日(出典なし)。
- ``POI_CAT_TO_INDUSTRY``(POI カテゴリ 16 値 → 産業大分類)。特に
  ``office``→L(学術研究,専門・技術サービス業)・``landmark``→N・``service``→R2。
- 最低額 10,000 円/上限 50,000,000 円/1,000 円単位で切り捨て。運用スケール
  (5,000〜400,000 体)では**どちらの端も発動しない**=按分がそのまま出る。下限が効くのは
  約 1,883 体未満のとき(最小カテゴリ M 宿泊飲食が 10,000 円を割る)。
- **従業者数による店規模補正はしない**: POI に従業者欄が無く、``w6_org`` との結合鍵
  ``place_id`` は 100 m 格子(店舗単位ではない)。センサスの「1事業所当たり従業者数」は
  大分類ごとの定数なので年商と同じ情報しか持たない。
- 1 店あたり年商の**分布形は置かない**(点=大分類の平均)。設計書 §2.6 は「1店あたり
  年商の分布形」を expedient に挙げているが、決定論を優先し乱数を使わない。

逐次ループ宣言(P4): なし(POI 数ぶんの NumPy ベクトル演算のみ)。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping, Sequence

import numpy as np

from shibuya.economy import goods as GD
from shibuya.economy.accounts import BalanceLine, Sector

__all__ = [
    "CENSUS_SOURCE",
    "SALES_PER_ESTABLISHMENT_BY_INDUSTRY",
    "INDUSTRY_NAMES",
    "UNPUBLISHED_INDUSTRIES",
    "POI_CAT_TO_INDUSTRY",
    "DEFAULT_INDUSTRY",
    "WORKING_CAPITAL_DAYS",
    "DAYS_PER_YEAR",
    "FULL_SCALE_AGENTS",
    "MIN_ENTRY_CAPITAL_YEN",
    "MAX_ENTRY_CAPITAL_YEN",
    "ROUND_TO_YEN",
    "COST_RATIO_BY_BAND",
    "price_band",
    "industry_of",
    "population_scale",
    "annual_sales",
    "store_entry_capital",
    "EntryCapitalReport",
    "entry_capital_report",
    "ledger_entry_capital_share",
]

#: 転記元(親一次確認・2026-09-07 取得)。
CENSUS_SOURCE: Final[str] = (
    "経済センサス2021活動調査(令和3年)・渋谷区13113・表章項目156-2021"
    "「1事業所当たり売上(収入)金額」[万円]・経営組織=総数(e-Stat GET_STATS_DATA)"
)

#: 産業大分類コード → 表示名(センサスの ``cat01``)。
INDUSTRY_NAMES: Final[Mapping[str, str]] = {
    "AB": "農林漁業",
    "E": "製造業",
    "G2": "情報通信業(情報サービス業，インターネット附随サービス業)",
    "I": "卸売業，小売業",
    "K": "不動産業，物品賃貸業",
    "L": "学術研究，専門・技術サービス業",
    "M": "宿泊業，飲食サービス業",
    "N": "生活関連サービス業，娯楽業",
    "O2": "教育，学習支援業(その他の教育，学習支援業)",
    "P": "医療，福祉",
    "R2": "サービス業(政治・経済・文化団体，宗教を除く)",
}

#: 産業大分類 → 1事業所当たり年商[円/年](センサス ``156-2021`` の万円値 × 10,000)。
SALES_PER_ESTABLISHMENT_BY_INDUSTRY: Final[Mapping[str, int]] = {
    "AB": 82_650_000,  # 8,265 万円
    "E": 1_586_160_000,  # 158,616 万円
    "G2": 1_231_510_000,  # 123,151 万円
    "I": 1_315_230_000,  # 131,523 万円
    "K": 578_340_000,  # 57,834 万円
    "L": 444_010_000,  # 44,401 万円
    "M": 85_320_000,  # 8,532 万円
    "N": 225_270_000,  # 22,527 万円
    "O2": 154_390_000,  # 15,439 万円
    "P": 361_200_000,  # 36,120 万円
    "R2": 640_430_000,  # 64,043 万円
}

#: 売上が使えない大分類(``･･･``=調査していないもの / ``X``=秘匿 / ``-``=該当なし)。
UNPUBLISHED_INDUSTRIES: Final[Mapping[str, str]] = {
    "AR": "･･･", "CR": "･･･", "C": "-", "D": "･･･", "F": "･･･", "G": "･･･",
    "G1": "･･･", "H": "･･･", "J": "･･･", "O": "･･･", "O1": "･･･", "Q": "･･･",
    "Q1": "･･･", "Q2": "X", "R": "･･･", "R1": "･･･",
}

#: POI カテゴリ → 産業大分類(**expedient**)。実資産 w6_poi の 13 値 + 合成世界の 3 値。
POI_CAT_TO_INDUSTRY: Final[Mapping[str, str]] = {
    # --- 実資産(data/world/v2/w6_poi.parquet の cat・2,337 件)
    "food": "M",  # 飲食店 823
    "shop": "I",  # 物販 721
    "nightlife": "M",  # バー・クラブ 259(飲食サービス業)
    "office": "L",  # 事務所 124(G 情報通信は売上が ･･･=非公表のため L)
    "service": "R2",  # 各種サービス 114
    "hotel": "M",  # 宿泊 89
    "school": "O2",  # 学習塾等 71(O1 学校教育は売上が ･･･)
    "landmark": "N",  # 名所 56(事業所とは限らない=最も薄い N へ)
    "leisure": "N",  # 娯楽 42
    "hall": "N",  # ホール 18
    "attraction": "N",  # 遊戯施設 12
    "cinema": "N",  # 映画館 7
    "education": "O2",  # 教育 1
    # --- 合成世界(world.assets.SYNTHETIC_POI_CATS)
    "コンビニ": "I",
    "飲食": "M",
    "物販": "I",
}
#: 写像に無いカテゴリの既定(最も薄い大分類)。
DEFAULT_INDUSTRY: Final[str] = "N"

#: 運転資金の日数 k(**expedient**・出典なし)。
WORKING_CAPITAL_DAYS: Final[float] = 30.0
#: 年商 → 日商の除数(``anchors.WASTE_TONNES_PER_DAY`` と同じ 365 日)。
DAYS_PER_YEAR: Final[float] = 365.0
#: 母集団比の分母(``engine.arbiter.L4_REFERENCE_AGENTS`` と同値・等価テストで固定)。
FULL_SCALE_AGENTS: Final[int] = 400_000
#: 参入資本の下限・上限[円]と丸め単位(**expedient**)。
MIN_ENTRY_CAPITAL_YEN: Final[int] = 10_000
MAX_ENTRY_CAPITAL_YEN: Final[int] = 50_000_000
ROUND_TO_YEN: Final[int] = 1_000

#: 価格帯(0=コンビニ/1=飲食/2=物販)→ 原価率(``goods.CATEGORY_K`` の逆数・§8 H-2)。
#: = (0.20, 0.303…, 0.344…)。``pricing.K_BY_KIND`` は**業態順**(高級/平均/ドル箱)で
#: 並びが違うので使わない(``goods.CATEGORY_K`` がカテゴリ順の正)。
COST_RATIO_BY_BAND: Final[tuple[float, ...]] = tuple(
    1.0 / float(k) for k in GD.CATEGORY_K
)


def price_band(cat: str) -> int:
    """カテゴリ名 → 価格帯 0..2。

    ``world.assets.hash_free_cat_code`` の**写し**(層契約のため economy から world を
    引かない・``tests/economy/test_entry_capital.py`` が等価を強制する)。
    """
    c = str(cat)
    if "conv" in c or "コンビニ" in c or "shop" in c:
        return 0
    if "food" in c or "飲食" in c or "restaurant" in c or "cafe" in c:
        return 1
    return 2


def industry_of(cat: str) -> str:
    """POI カテゴリ → 産業大分類コード(未知は ``DEFAULT_INDUSTRY``)。"""
    return POI_CAT_TO_INDUSTRY.get(str(cat), DEFAULT_INDUSTRY)


def population_scale(n_agents: int | None) -> float:
    """母集団比 ρ = n / 400,000(``None`` なら 1.0=実スケール)。"""
    if n_agents is None:
        return 1.0
    return max(0.0, float(int(n_agents)) / float(FULL_SCALE_AGENTS))


def annual_sales(poi_cat: Sequence[str]) -> np.ndarray:
    """POI ごとの 1事業所当たり年商[円/年](``(n_poi,)`` int64)。"""
    return np.array(
        [SALES_PER_ESTABLISHMENT_BY_INDUSTRY[industry_of(c)] for c in poi_cat],
        dtype=np.int64,
    )


def store_entry_capital(
    poi_cat: Sequence[str],
    *,
    n_agents: int | None = None,
    scale: float | None = None,
    days: float = WORKING_CAPITAL_DAYS,
    cost_basis: bool = True,
    bands: np.ndarray | Sequence[int] | None = None,
    min_yen: int = MIN_ENTRY_CAPITAL_YEN,
    max_yen: int = MAX_ENTRY_CAPITAL_YEN,
    round_to: int = ROUND_TO_YEN,
) -> np.ndarray:
    """店舗ごとの参入資本[円](``(n_poi,)`` int64・**決定論**・乱数なし)。

    Args:
        poi_cat: POI のカテゴリ名(``world.assets.poi_cat``)。
        n_agents: ランの個体数(母集団比 ρ=n/400,000 に使う)。``scale`` 指定時は無視。
        scale: 母集団比を直接指定(``1.0`` = 実スケール)。
        days: 運転資金の日数 k。
        cost_basis: True なら年商×原価率(=仕入額)、False なら年商そのもの。
        bands: 価格帯 0..2 を外から渡す(``None`` なら ``price_band`` で導く)。
        min_yen: 下限[円]。
        max_yen: 上限[円]。
        round_to: 丸め単位[円](切り捨て)。

    Returns:
        ``(n_poi,)`` int64 の参入資本。合計は ``int(result.sum())``。

    Example:
        >>> store_entry_capital(["food", "shop"], n_agents=5_000).tolist()
        [26000, 270000]
    """
    cats = [str(c) for c in poi_cat]
    n = len(cats)
    if n == 0:
        return np.zeros(0, dtype=np.int64)
    rho = float(scale) if scale is not None else population_scale(n_agents)
    sales = annual_sales(cats).astype(np.float64)
    if cost_basis:
        if bands is None:
            b = np.array([price_band(c) for c in cats], dtype=np.int64)
        else:
            b = np.asarray(bands, dtype=np.int64).ravel()[:n]
        ratio = np.asarray(COST_RATIO_BY_BAND, dtype=np.float64)[
            np.clip(b, 0, len(COST_RATIO_BY_BAND) - 1)
        ]
    else:
        ratio = np.ones(n, dtype=np.float64)
    raw = sales / float(DAYS_PER_YEAR) * float(days) * ratio * float(rho)
    step = max(1, int(round_to))
    rounded = np.floor(raw / step).astype(np.int64) * step
    return np.clip(rounded, int(min_yen), int(max_yen)).astype(np.int64)


@dataclass(frozen=True)
class EntryCapitalReport:
    """参入資本の検算(合計・大分類別・貨幣供給に対する比率)。"""

    n_stores: int
    total_yen: int
    days: float
    scale: float
    cost_basis: bool
    #: (大分類コード, 店数, 合計[円], 1店あたり[円])を店数降順で。
    by_industry: tuple[tuple[str, int, int, int], ...]
    household_cash_yen: int | None = None
    money_supply_yen: int | None = None
    share_of_money_supply: float | None = None

    def as_text(self) -> str:
        head = (
            f"[参入資本] {self.n_stores:,} 店 / 合計 {self.total_yen:,} 円 "
            f"(k={self.days:g} 日・rho={self.scale:.5f}・"
            f"{'仕入基準' if self.cost_basis else '売上基準'})"
        )
        if self.share_of_money_supply is not None:
            head += (
                f" / 貨幣供給 {self.money_supply_yen:,} 円の "
                f"{self.share_of_money_supply * 100:.2f}%"
            )
        rows = [
            f"  {code:<3} {INDUSTRY_NAMES.get(code, code)[:18]:<20} "
            f"{n:>5} 店 {tot:>16,} 円 ({per:,}/店)"
            for code, n, tot, per in self.by_industry
        ]
        return "\n".join([head, *rows])


def entry_capital_report(
    capital: np.ndarray,
    poi_cat: Sequence[str],
    *,
    days: float = WORKING_CAPITAL_DAYS,
    scale: float = 1.0,
    cost_basis: bool = True,
    household_cash_yen: int | None = None,
) -> EntryCapitalReport:
    """参入資本の検算行を作る(合計 = 個別和・大分類別内訳・貨幣供給比)。

    ``household_cash_yen`` を渡すと、貨幣供給 M(=世帯+店舗+雇用主の現金・雇用主は
    第1陣で 0)に対する店舗側の比率を入れる。台帳から直に測る版は
    ``ledger_entry_capital_share``。
    """
    a = np.asarray(capital, dtype=np.int64).ravel()
    cats = [str(c) for c in poi_cat][: a.size]
    total = int(a.sum())
    codes = np.array([industry_of(c) for c in cats], dtype=object)
    rows: list[tuple[str, int, int, int]] = []
    for code in sorted({str(c) for c in codes.tolist()}):
        m = codes == code
        cnt = int(m.sum())
        tot = int(a[m].sum())
        rows.append((code, cnt, tot, int(tot // cnt) if cnt else 0))
    rows.sort(key=lambda r: (-r[1], r[0]))
    money = None
    share = None
    if household_cash_yen is not None:
        money = int(household_cash_yen) + total
        share = (total / money) if money else None
    return EntryCapitalReport(
        n_stores=int(a.size),
        total_yen=total,
        days=float(days),
        scale=float(scale),
        cost_basis=bool(cost_basis),
        by_industry=tuple(rows),
        household_cash_yen=None if household_cash_yen is None else int(household_cash_yen),
        money_supply_yen=money,
        share_of_money_supply=share,
    )


def ledger_entry_capital_share(ledger) -> tuple[int, int, float]:
    """台帳から直に測る (店舗の現金+預金[円], 貨幣供給 M[円], 比率)。

    D-13 の「467.4M 円=貨幣供給の 93%」を再現・追跡するための検算。
    """
    cash = ledger.sector_totals(BalanceLine.CASH)
    dep = ledger.sector_totals(BalanceLine.DEPOSIT)
    store = int(cash[int(Sector.STORE)] + dep[int(Sector.STORE)])
    m = int(ledger.money_supply())
    return store, m, (store / m if m else 0.0)
