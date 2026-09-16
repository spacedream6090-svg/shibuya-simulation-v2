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

from dataclasses import dataclass, field
from enum import IntEnum
from typing import (
    Any,
    Callable,
    ContextManager,
    Mapping,
    NamedTuple,
    Protocol,
    Sequence,
    runtime_checkable,
)

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
    "DayCloses",
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
        """日次の畳み込み(取引行列の集約・生ログの保持窓・D-R2-6)。**締めを返す**。"""
        ...

    def close_for(self, day: int) -> Any:
        """``day`` が直近に畳んだ日ならその締めを返す(日次センサスが読む)。"""
        ...

    def growth_declarations(self) -> Mapping[str, Any]:
        """D-R2-6 の宣言(``growth_measured`` と同じ鍵)。engine が economy を import
        できないので**台帳自身が名乗る**(依存逆転)。"""
        ...

    def growth_measured(self) -> Mapping[str, int]:
        """D-R2-6 の実測増分バイト。"""
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

    def restock_many(
        self,
        stores: np.ndarray,
        qty: np.ndarray,
        tick: int,
        *,
        money: Any | None = None,
        slot: np.ndarray | None = None,
    ) -> np.ndarray:
        """補充・納品(外界→棚・faucet 域外仕入)。``money`` を渡すと代金も transfer する。"""
        ...

    def to_bin_many(
        self, stores: np.ndarray, qty: np.ndarray, tick: int, slot: np.ndarray | None = None
    ) -> np.ndarray:
        """売れ残りを廃棄ビンへ(棚→ビン・C 類排出)。"""
        ...

    def collect_waste(self, stores: np.ndarray | None, tick: int) -> float:
        """廃棄物収集(ビン→bbox 外・sink)。搬出質量[g]。"""
        ...

    def consume_many(self, sku_ids: np.ndarray, qty: np.ndarray, tick: int) -> np.ndarray:
        """世帯の消費(所持→sink)。"""
        ...

    def waste_band(self, days: int | None = None) -> Any:
        """廃棄 sink の t/日 band 判定(検算②・台帳行 W1)。"""
        ...

    def aggregate_stock(self, stores: np.ndarray | None = None) -> np.ndarray:
        """店舗の棚在庫合計(``world.pois.stock`` はこの写しであり、書くのは resolve だけ)。"""
        ...

    def on_day_end(self, day: int) -> Any:
        ...

    def close_for(self, day: int) -> Any:
        ...

    def growth_declarations(self) -> Mapping[str, Any]:
        ...

    def growth_measured(self) -> Mapping[str, int]:
        ...


class DayCloses(NamedTuple):
    """``LedgerBundle.end_of_day`` の戻り(その日の締め)。

    Attributes:
        day: 畳んだ日。
        money: ``MoneyLedger.on_day_end`` の戻り(``economy.ledger.DayClose``)。
        goods: ``GoodsLedger.on_day_end`` の戻り(締め辞書)。
    """

    day: int
    money: Any | None
    goods: Any | None


@dataclass(frozen=True)
class LedgerBundle:
    """resolve / run へ注入する台帳の束(金・物)。どちらも ``None`` 可(C2 互換経路)。

    Attributes:
        census: 日次(軽量)センサス行を作る呼び出し可能(``day -> 行の Mapping``)。
            **engine は economy を import できない**(層契約 ``economy > engine``)ので、
            ``economy.census.daily_census`` はここへ**注入**する(依存逆転)。
            ``None`` なら ``engine.run`` はセンサス行を持たない(``census_pass=False``)。
        census_write: 日次センサス/月次 MER を**ファイルに書く**呼び出し可能
            (``(day, 出力ディレクトリ) -> 書いたパスの並び``)。``census`` と同じ理由で
            economy 側(``cli.write_census_files``)から注入する。``engine.run`` は
            ``census_out`` を渡されたときだけ呼ぶ(**既定 None=1 バイトも書かない**)。
    """

    money: MoneyLedger | None = None
    goods: GoodsLedger | None = None
    census: Callable[[int], Mapping[str, Any]] | None = None
    census_write: Callable[[int, str], "Sequence[str]"] | None = None
    #: ``end_of_day`` が畳んだ**直近の締め**(``daily_census`` が読む用の控え)。
    #: frozen dataclass なので中身だけ差し替える(比較・ハッシュからは外す)。
    last_close: dict[str, Any] = field(default_factory=dict, compare=False, repr=False)

    def end_of_day(self, day: int) -> DayCloses:
        """日次の畳み込みを両台帳へ流し、**その日の締めを返す**。

        締めると取引フロー行列も当日の廃棄も 0 に戻る。日次センサスを「締めたあとに
        現在値で」回すと faucet/sink/廃棄が全部 0 の空虚な行になりゲートが素通りするので、
        締めは捨てずにここで保持する(層2レビュー指摘の固定)。
        """
        close = self.money.on_day_end(day) if self.money is not None else None
        goods_close = self.goods.on_day_end(day) if self.goods is not None else None
        closes = DayCloses(int(day), close, goods_close)
        self.last_close.clear()
        self.last_close.update(day=closes.day, money=closes.money, goods=closes.goods)
        return closes

    def daily_census(self, day: int) -> Mapping[str, Any] | None:
        """注入された日次センサスを回す(境界・経済設計書 §2.4)。

        ``day`` が ``end_of_day`` で畳んだ日なら、行は**締めた日の実数**になる
        (``economy.census.daily_census`` が台帳の ``close_for(day)`` から締めを引く)。

        ゲート失敗は**例外にしない**(呼び出し側が診断の赤として扱う)。行の作成そのものが
        失敗したときも ``None`` を返して**ランを止めない**(センサスは観測であって世界ではない)。
        """
        if self.census is None:
            return None
        return self.census(int(day))

    def write_census(self, day: int, out_dir: str) -> tuple[str, ...]:
        """日次センサス/月次 MER をファイルへ書く(``census_out`` を渡されたときだけ)。

        注入が無ければ**何も書かずに空を返す**(既定経路は 1 バイトも動かない)。
        書き手は economy 側(``cli.write_census_files``)。
        """
        if self.census_write is None:
            return ()
        return tuple(str(p) for p in self.census_write(int(day), str(out_dir)))

    def growth_parts(self) -> tuple[dict[str, Any], dict[str, int]]:
        """両台帳の D-R2-6(宣言, 実測増分バイト)を 1 組に畳む。

        engine は economy を import できない(層契約)ので、``engine.run`` の成長ゲートは
        **台帳自身が名乗る**宣言をここで受け取る(依存逆転)。宣言と実測は必ず同じ鍵で返す
        (片方だけだと ``core.growth.check_growth`` が「未測定」として落とす)。
        """
        decls: dict[str, Any] = {}
        measured: dict[str, int] = {}
        for led in (self.money, self.goods):
            if led is None:
                continue
            d = getattr(led, "growth_declarations", None)
            m = getattr(led, "growth_measured", None)
            if d is None or m is None:
                continue
            got_d, got_m = dict(d()), {k: int(v) for k, v in m().items()}
            keys = set(got_d) & set(got_m)
            decls.update({k: got_d[k] for k in keys})
            measured.update({k: got_m[k] for k in keys})
        return decls, measured
