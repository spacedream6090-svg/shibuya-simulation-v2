"""engine.ledger_api — 台帳の**依存逆転インターフェース**(Protocol と語彙だけ・実装は economy)。

正典
- 実装計画書 §3 の層契約: 層は ``census > economy > engine > … `` の順で、上→下の import
  のみ。**economy は engine を import してよいが engine は economy を import できない**
  (pyproject の import-linter 契約 ``layers``)。それでも
  境界・経済設計書 §2.3 の「``transfer(payer, payee, amount, account_code)`` **単一API**・
  残高の直接代入は静的に禁止」を resolve に効かせる必要がある。
  → 本モジュールが **Protocol(構造的型)だけ**を持ち、economy 側の実装体を
  ``engine.resolve`` / ``engine.run`` へ**注入**する(依存逆転)。
- 世界過程設計書 §7.1(U-Goods): ``move_goods(from, to, qty, sku, account_code)`` 単一API。
  金(U11)と同型なので Protocol も2本立てにする(``MoneyLedger`` / ``GoodsLedger``)。
- 行動契約書 §2「購入・乗車は保存則対象」/ 運用設計書 §2.2「書き込み口は resolve 1本」。

**なぜ engine 側に部門番号(``SECTOR_*``)を置くのか**
    resolve は「世帯が店舗へ払った」という事実を台帳へ渡す必要がある。科目
    (``AccountCode``)は economy の語彙なので engine には置かず、``purchase_many`` の
    ような**意味のある単位のメソッド**で隠す(engine は「購入が成立した」しか言わない)。
    部門番号だけは ``EntityRef`` の型として境界に露出するので、ここを正典にして
    economy 側 ``Sector`` と一致することをテストで強制する
    (``tests/economy/test_accounts.py::test_sector_codes_match_engine_api``)。

逐次ループ宣言(P4): なし(本モジュールは型定義のみ・実行時コードを持たない)。

expedient(本モジュール分)
- ``TransferStatus`` の値の並び(設計書は「業務上の失敗は例外にしない」とまでは書いていない。
  行動契約書 §2.1 の ``ResultCode`` と同じ思想=**失敗は戻り値**にした)。
- ``LedgerBundle`` という束ね方(設計書は金と物を別APIとしか言っていない)。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Any, ContextManager, NamedTuple, Protocol, runtime_checkable

import numpy as np

__all__ = [
    "SECTOR_HOUSEHOLD",
    "SECTOR_STORE",
    "SECTOR_EMPLOYER",
    "SECTOR_BANK",
    "SECTOR_GOVERNMENT",
    "SECTOR_ROW",
    "N_SECTORS",
    "TransferStatus",
    "EntityRef",
    "MoneyLedger",
    "GoodsLedger",
    "LedgerBundle",
]

#: 部門番号(境界・経済設計書 §2.1 の6部門。economy.accounts.Sector と 1 対 1)。
SECTOR_HOUSEHOLD: int = 0
SECTOR_STORE: int = 1
SECTOR_EMPLOYER: int = 2
SECTOR_BANK: int = 3
SECTOR_GOVERNMENT: int = 4
SECTOR_ROW: int = 5
N_SECTORS: int = 6


class TransferStatus(IntEnum):
    """``transfer`` の結果コード(**業務上の失敗は例外にしない**=行動契約書 §2.1 と同思想)。

    ``BAD_ENTITY`` 以降はプログラム誤りに近いが、ベクトル版(``transfer_many``)で
    行ごとに返す必要があるので同じ列挙に入れる。
    """

    OK = 0
    BAD_AMOUNT = 1  # 金額が 0 以下 / 非整数
    UNKNOWN_CODE = 2  # 列挙にない科目(§2.2「列挙にない科目の transfer は実行不能」)
    FORBIDDEN_PAIR = 3  # faucet/sink 表にない (支払部門, 受取部門) の組
    INSUFFICIENT_FUNDS = 4  # 現金不足(不可逆な資源移動はエンジン=原則1)
    BAD_ENTITY = 5  # 主体 id が範囲外
    EX_NIHILO = 6  # 参入資本が許された出所以外(Caiani 2016 の ex nihilo 禁止)


class EntityRef(NamedTuple):
    """台帳の主体参照 = (部門, 部門内の索引)。

    索引の意味は部門ごと: 世帯=agent_id・店舗=poi_id・雇用主=org_id・
    銀行/政府/外界=0(単一主体)。
    """

    sector: int
    index: int


@runtime_checkable
class MoneyLedger(Protocol):
    """金の台帳(U11)。実装は ``shibuya.economy.ledger.Ledger``。"""

    def unlocked(self) -> ContextManager[Any]:
        """台帳が持つ配列を書き込み可能にする文脈(resolve の書き込み窓と入れ子にする)。"""
        ...

    def transfer(
        self, payer: EntityRef, payee: EntityRef, amount: int, code: int, tick: int
    ) -> TransferStatus:
        """単一API(境界・経済設計書 §2.3)。残高の直接代入はこれ以外に存在しない。"""
        ...

    def transfer_many(
        self,
        payer_sector: int,
        payers: np.ndarray,
        payee_sector: int,
        payees: np.ndarray,
        amounts: np.ndarray,
        code: int,
        tick: int,
    ) -> np.ndarray:
        """ベクトル版(P4: 個体数ぶんの Python ループを作らない)。行ごとの ``TransferStatus``。"""
        ...

    def purchase_many(
        self, buyers: np.ndarray, stores: np.ndarray, amounts: np.ndarray, tick: int
    ) -> np.ndarray:
        """購入の金の脚(世帯→店舗・消費支出)。engine は科目名を知らない。"""
        ...

    def attach_household_cash(self, money: np.ndarray) -> None:
        """世帯の現金行として個体 SoA の ``money`` 配列を**そのまま**採用する(写しを作らない)。

        これにより台帳への書き込みも ``AgentState.writable()`` の窓の中でしか成立しない
        (= 世界への書き込み口が resolve 1本であることの機械強制が台帳にも及ぶ)。
        """
        ...

    def endow_households(self, amounts: np.ndarray, tick: int) -> np.ndarray:
        """初期財布(外界→世帯)。**直接代入ではなく transfer で入れる**=ex nihilo 禁止。"""
        ...

    def on_day_end(self, day: int) -> Any:
        """日次の畳み込み(取引行列の集約・生ログの保持窓・D-R2-6)。"""
        ...


@runtime_checkable
class GoodsLedger(Protocol):
    """物の台帳(U-Goods・世界過程設計書 §7.1)。実装は ``shibuya.economy.goods.GoodsLedger``。"""

    def unlocked(self) -> ContextManager[Any]:
        ...

    def can_sell(self, stores: np.ndarray) -> np.ndarray:
        """店舗ごとに「売れる棚があるか」の bool(resolve の前提条件検査用)。"""
        ...

    def sell_many(self, stores: np.ndarray, tick: int) -> np.ndarray:
        """販売(棚→世帯・1 行 1 個)。行ごとの成否 bool を返す。"""
        ...

    def aggregate_stock(self, stores: np.ndarray | None = None) -> np.ndarray:
        """店舗の棚在庫合計(``world.pois.stock`` はこの写しであり、書くのは resolve だけ)。"""
        ...

    def on_day_end(self, day: int) -> Any:
        ...


@dataclass(frozen=True)
class LedgerBundle:
    """resolve / run へ注入する台帳の束(金・物)。どちらも ``None`` 可(C2 互換経路)。"""

    money: MoneyLedger | None = None
    goods: GoodsLedger | None = None

    def end_of_day(self, day: int) -> None:
        """日次の畳み込みを両台帳へ流す。"""
        if self.money is not None:
            self.money.on_day_end(day)
        if self.goods is not None:
            self.goods.on_day_end(day)
