"""economy.accounts — 部門・貸借対照表の行・**取引科目の列挙と faucet/sink 表**(U11 §2.1-2.2)。

正典(境界・経済設計書 §2)
- §2.1 部門(6): 世帯・店舗・雇用主・銀行・政府・外界(RoW=U10 の外界ノードと同一実体)。
- §2.2 科目: 貸借対照表**6行**(現金・預金・在庫・固定資産・借入・純資産)/
  取引フロー**12科目**(消費支出・賃金・域外仕入・税・利子・家賃・預金純増・来街者持込・
  持ち出し・参入資本・配当/内部留保・減価償却)+ **残差科目** + **退蔵項**。
- §2.2 「**faucet/sink表**: faucet=来街者持込・域外雇用主の賃金・政府給付/
  sink=域外仕入・税・持ち出し。**account_code の列挙型と1対1**・
  列挙にない科目の transfer は**実行不能**(CLAUDE.md §4「faucet/sink全登録」の実装形)」。
- §2.3 「新規則(ex nihilo禁止): 参入時の初期資本は創業者預金・銀行貸出・外界からの
  transfer 由来のみ」→ ``ENTRY_CAPITAL_PAYERS``。
- 世界過程設計書 §8 H-5: 価格の「**逸脱比例コスト(sink登録)**」→ ``DEVIATION_COST``。

逐次ループ宣言(P4)
- ``_build_table`` / ``faucet_sink_table``: **科目数 × 許可された部門対**ぶん
  (15 科目・数十行)のループ。個体数・tick 数には比例しない。

**設計書との食い違い(親へ報告・本モジュールでは解決しない)**
1. **減価償却に相手方がいない**。§2.2 は 12 科目の1つに数えるが、§2.3 の単一APIは
   ``transfer(payer, payee, amount, code)`` = 必ず2主体を要求する。本実装は
   ``DEPRECIATION`` を「**自己ループ**(payer==payee)」として受理し、現金を動かさず
   固定資産と純資産だけを落とす(``Ledger.depreciate``)。行和・列和 0 は保たれる。
2. **退蔵項(HOARD)はフローではなくストックの測度**。列挙に入れよという指示(12+残差+退蔵)
   に従って列挙には入れたが、``is_allowed`` は**全ての部門対で False** を返す
   (= transfer では使えない)。計上は ``checks.hoard_report`` が行う。
3. **逸脱比例コスト**は §8 H-5 が「sink 登録」を要求する一方、§2.2 の 12 科目には無い。
   本実装は 15 番目の科目として登録し(店舗→政府)、expedient として宣言する。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Final, Mapping

from shibuya.engine import ledger_api as api

__all__ = [
    "Sector",
    "SECTOR_NAMES",
    "BalanceLine",
    "BALANCE_LINE_NAMES",
    "STORED_LINES",
    "AccountCode",
    "ACCOUNT_NAMES",
    "FlowKind",
    "AccountSpec",
    "ACCOUNTS",
    "ENTRY_CAPITAL_PAYERS",
    "NON_TRANSFERABLE",
    "UNCONSTRAINED_SECTORS",
    "is_allowed",
    "flow_kind",
    "faucet_sink_table",
]


class Sector(IntEnum):
    """部門(§2.1 の6部門)。値は ``engine.ledger_api.SECTOR_*`` と 1 対 1。"""

    HOUSEHOLD = 0  # 世帯(住民+来街者の財布)
    STORE = 1  # 店舗(POI)
    EMPLOYER = 2  # 雇用主(組織・本部)
    BANK = 3  # 銀行(第1陣は預金のみ)
    GOVERNMENT = 4  # 政府(第1陣は税 sink のみ)
    ROW = 5  # 外界(Rest of World = U10 の外界ノードと同一実体)


SECTOR_NAMES: Final[tuple[str, ...]] = ("世帯", "店舗", "雇用主", "銀行", "政府", "外界")

assert int(Sector.HOUSEHOLD) == api.SECTOR_HOUSEHOLD
assert int(Sector.STORE) == api.SECTOR_STORE
assert int(Sector.EMPLOYER) == api.SECTOR_EMPLOYER
assert int(Sector.BANK) == api.SECTOR_BANK
assert int(Sector.GOVERNMENT) == api.SECTOR_GOVERNMENT
assert int(Sector.ROW) == api.SECTOR_ROW
assert len(Sector) == api.N_SECTORS == len(SECTOR_NAMES)


class BalanceLine(IntEnum):
    """貸借対照表6行(§2.2)。``NET_WORTH`` だけは**導出量**(配列を持たない)。

    純資産 = 現金 + 預金 + 在庫 + 固定資産 − 借入。独立に持つと検算②が恒真になり
    検査の意味が消えるため、``Ledger`` は 5 本の実配列だけを持ち NET_WORTH を計算する。
    """

    CASH = 0  # 現金
    DEPOSIT = 1  # 預金(銀行に対する債権)
    INVENTORY = 2  # 在庫(評価額[円]・数量は U-Goods 側)
    FIXED_ASSET = 3  # 固定資産
    LOAN = 4  # 借入(負債。銀行から見た預金受入もここに立つ)
    NET_WORTH = 5  # 純資産(導出)


BALANCE_LINE_NAMES: Final[tuple[str, ...]] = (
    "現金", "預金", "在庫", "固定資産", "借入", "純資産",
)
#: 実配列を持つ行(NET_WORTH は導出なので含まない)。
STORED_LINES: Final[tuple[BalanceLine, ...]] = (
    BalanceLine.CASH,
    BalanceLine.DEPOSIT,
    BalanceLine.INVENTORY,
    BalanceLine.FIXED_ASSET,
    BalanceLine.LOAN,
)


class AccountCode(IntEnum):
    """取引科目(§2.2 の 12 科目 + 残差 + 退蔵 + 逸脱比例コスト)。

    **列挙にない科目の transfer は実行不能**(§2.2)。``Ledger.transfer`` は
    ``int`` を ``AccountCode`` に変換できなければ ``UNKNOWN_CODE`` を返す。
    """

    CONSUMPTION = 0  # 消費支出
    WAGE = 1  # 賃金
    IMPORT_PURCHASE = 2  # 域外仕入
    TAX = 3  # 税
    INTEREST = 4  # 利子
    RENT = 5  # 家賃
    DEPOSIT_NET = 6  # 預金純増(現金→預金の振替。銀行側に借入=預金負債が立つ)
    CARRY_IN = 7  # 来街者持込(faucet)
    CARRY_OUT = 8  # 持ち出し(sink)
    ENTRY_CAPITAL = 9  # 参入資本(ex nihilo 禁止の対象)
    DIVIDEND_RETAINED = 10  # 配当/内部留保
    DEPRECIATION = 11  # 減価償却(自己ループ・現金を動かさない)
    RESIDUAL = 12  # 残差科目(丸め・未分類。閾値超でゲート失敗)
    HOARD = 13  # 退蔵項(**測度**。transfer には使えない)
    DEVIATION_COST = 14  # 逸脱比例コスト(§8 H-5・sink 登録・expedient)


ACCOUNT_NAMES: Final[tuple[str, ...]] = (
    "消費支出", "賃金", "域外仕入", "税", "利子", "家賃", "預金純増",
    "来街者持込", "持ち出し", "参入資本", "配当/内部留保", "減価償却",
    "残差科目", "退蔵項", "逸脱比例コスト",
)
assert len(ACCOUNT_NAMES) == len(AccountCode)


class FlowKind(IntEnum):
    """faucet/sink 表の区分(§2.2)。"""

    INTERNAL = 0  # bbox 内の移動(貨幣供給量を変えない)
    FAUCET = 1  # 外から入る(貨幣供給量+)
    SINK = 2  # 外へ出る(貨幣供給量−)
    MEASURE = 3  # 測度(transfer 不能・退蔵項)
    BOOK = 4  # 帳簿上の振替(現金移動なし・減価償却)


#: 現金残高の制約を課さない部門(expedient)。
#: 外界・銀行・政府は faucet の源であり、bbox 内の現金を「持っている」わけではない。
#: 負の現金 = 外に対する差引(= bbox 内へ流し込んだ総額)を表す会計上の相手勘定。
UNCONSTRAINED_SECTORS: Final[frozenset[Sector]] = frozenset(
    {Sector.ROW, Sector.BANK, Sector.GOVERNMENT}
)

#: 参入資本の許された出所(§2.3 ex nihilo 禁止: 創業者預金・銀行貸出・外界)。
ENTRY_CAPITAL_PAYERS: Final[frozenset[Sector]] = frozenset(
    {Sector.HOUSEHOLD, Sector.BANK, Sector.ROW}
)

#: transfer に使えない科目(測度)。
NON_TRANSFERABLE: Final[frozenset[AccountCode]] = frozenset({AccountCode.HOARD})


@dataclass(frozen=True)
class AccountSpec:
    """1科目の仕様(許可された部門対 + タグ + 由来)。"""

    code: AccountCode
    name: str
    pairs: frozenset[tuple[Sector, Sector]]
    mechanism: bool
    note: str

    @property
    def tag(self) -> str:
        return "mechanism" if self.mechanism else "expedient"


_H = Sector.HOUSEHOLD
_S = Sector.STORE
_E = Sector.EMPLOYER
_B = Sector.BANK
_G = Sector.GOVERNMENT
_W = Sector.ROW

#: 科目 → 許可された (支払部門, 受取部門) の組(**列挙と 1 対 1**)。
_PAIRS: Final[dict[AccountCode, tuple[tuple[Sector, Sector], ...]]] = {
    AccountCode.CONSUMPTION: ((_H, _S),),
    AccountCode.WAGE: ((_E, _H), (_S, _H), (_W, _H)),  # (外界,世帯)=域外雇用主の賃金(faucet)
    AccountCode.IMPORT_PURCHASE: ((_S, _W), (_E, _W)),
    AccountCode.TAX: ((_H, _G), (_S, _G), (_E, _G)),
    AccountCode.INTEREST: ((_B, _H), (_B, _S), (_H, _B), (_S, _B), (_E, _B)),
    AccountCode.RENT: ((_H, _E), (_S, _E), (_H, _W), (_S, _W)),
    AccountCode.DEPOSIT_NET: ((_H, _B), (_S, _B), (_E, _B), (_B, _H), (_B, _S), (_B, _E)),
    AccountCode.CARRY_IN: ((_W, _H),),
    AccountCode.CARRY_OUT: ((_H, _W),),
    AccountCode.ENTRY_CAPITAL: ((_H, _S), (_H, _E), (_B, _S), (_B, _E), (_W, _S), (_W, _E)),
    AccountCode.DIVIDEND_RETAINED: ((_S, _H), (_E, _H), (_S, _E), (_E, _W)),
    AccountCode.DEPRECIATION: ((_S, _S), (_E, _E), (_H, _H)),  # 自己ループ(相手方なし)
    AccountCode.RESIDUAL: tuple((a, b) for a in Sector for b in Sector),
    AccountCode.HOARD: (),  # 測度=transfer 不能
    AccountCode.DEVIATION_COST: ((_S, _G),),
}
assert set(_PAIRS) == set(AccountCode), "faucet/sink 表は account_code の列挙と 1 対 1"

_NOTES: Final[dict[AccountCode, tuple[bool, str]]] = {
    AccountCode.CONSUMPTION: (True, "家計調査2025の消費支出(§2.5 アンカー)"),
    AccountCode.WAGE: (True, "第1陣は雇用主から月次(外生)。域外雇用主分は faucet"),
    AccountCode.IMPORT_PURCHASE: (True, "sink(§2.2)。U-Goods の域外仕入と対"),
    AccountCode.TAX: (True, "sink(§2.2)。第1陣の政府は税 sink のみ(§2.7)"),
    AccountCode.INTEREST: (True, "銀行との利子(第1陣は預金のみなので既定 0)"),
    AccountCode.RENT: (True, "家賃。域外地主への支払は sink"),
    AccountCode.DEPOSIT_NET: (True, "現金↔預金の振替。銀行側に預金負債(借入行)が立つ"),
    AccountCode.CARRY_IN: (True, "faucet(§2.2)。訪日客 7.1万円/滞在は上限側目安(§2.5)"),
    AccountCode.CARRY_OUT: (True, "sink(§2.2)"),
    AccountCode.ENTRY_CAPITAL: (True, "ex nihilo 禁止(§2.3・Caiani 2016)"),
    AccountCode.DIVIDEND_RETAINED: (True, "配当/内部留保"),
    AccountCode.DEPRECIATION: (False, "相手方が無いので自己ループとして受理(expedient・矛盾#1)"),
    AccountCode.RESIDUAL: (True, "残差科目(丸め・未分類)。閾値超でゲート失敗(§2.4)"),
    AccountCode.HOARD: (False, "退蔵は**ストックの測度**。transfer 不能(expedient・矛盾#2)"),
    AccountCode.DEVIATION_COST: (False, "§8 H-5 の sink 登録。12科目に無い(expedient・矛盾#3)"),
}


def _build_table() -> Mapping[AccountCode, AccountSpec]:
    """逐次ループ宣言: 科目数(15)ぶん。"""
    out: dict[AccountCode, AccountSpec] = {}
    for code in AccountCode:
        mech, note = _NOTES[code]
        out[code] = AccountSpec(
            code=code,
            name=ACCOUNT_NAMES[int(code)],
            pairs=frozenset(_PAIRS[code]),
            mechanism=mech,
            note=note,
        )
    return out


#: 科目 → 仕様(faucet/sink 表の実体)。
ACCOUNTS: Final[Mapping[AccountCode, AccountSpec]] = _build_table()


def flow_kind(code: int, payer: int, payee: int) -> FlowKind:
    """faucet / sink / internal の判定(**規則で導く**=表の二重管理を作らない)。

    規則(§2.2 の列挙をそのまま規則化したもの):
      1. 退蔵項は測度。減価償却は帳簿上の振替。
      2. 外界から入れば faucet・外界へ出れば sink。
      3. 政府への税・逸脱比例コストは sink(第1陣の政府は税 sink のみ=§2.7)。
      4. それ以外は internal。
    """
    c = AccountCode(int(code))
    a = Sector(int(payer))
    b = Sector(int(payee))
    if c == AccountCode.HOARD:
        return FlowKind.MEASURE
    if c == AccountCode.DEPRECIATION:
        return FlowKind.BOOK
    if a == Sector.ROW and b != Sector.ROW:
        return FlowKind.FAUCET
    if b == Sector.ROW and a != Sector.ROW:
        return FlowKind.SINK
    if b == Sector.GOVERNMENT and c in (AccountCode.TAX, AccountCode.DEVIATION_COST):
        return FlowKind.SINK
    return FlowKind.INTERNAL


def is_allowed(code: int, payer_sector: int, payee_sector: int) -> bool:
    """(科目, 支払部門, 受取部門)が faucet/sink 表にあるか。

    Example:
        >>> is_allowed(AccountCode.CONSUMPTION, Sector.HOUSEHOLD, Sector.STORE)
        True
        >>> is_allowed(AccountCode.CONSUMPTION, Sector.STORE, Sector.HOUSEHOLD)
        False
    """
    try:
        c = AccountCode(int(code))
        a = Sector(int(payer_sector))
        b = Sector(int(payee_sector))
    except ValueError:
        return False
    return (a, b) in ACCOUNTS[c].pairs


def faucet_sink_table() -> tuple[tuple[str, str, str, str, str], ...]:
    """faucet/sink 表を人が読む形で返す(科目・支払・受取・区分・タグ)。

    逐次ループ宣言: 科目 × 許可部門対ぶん(数十行)。
    """
    rows: list[tuple[str, str, str, str, str]] = []
    for code in AccountCode:
        spec = ACCOUNTS[code]
        if not spec.pairs:
            rows.append((spec.name, "—", "—", flow_kind(code, _H, _H).name, spec.tag))
            continue
        for payer, payee in sorted(spec.pairs):
            rows.append(
                (
                    spec.name,
                    SECTOR_NAMES[int(payer)],
                    SECTOR_NAMES[int(payee)],
                    flow_kind(code, payer, payee).name,
                    spec.tag,
                )
            )
    return tuple(rows)
