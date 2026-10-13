"""economy.ledger — 金の台帳(U11)。``transfer`` **単一API**と取引フロー行列。

〔第 1 期 1-9・CP2 の段階 1〕帳簿の口(``transfer``・``transfer_many``・``purchase_many``・``endow_households``・
``endow_stores``・``depreciate``)は検査(行ごとの ``TransferStatus``)までをここで行い、通った行を基本操作
``economy.ops.transfer``(お金の「移す」の 1 つ)に渡す。**残高・流れの表・生ログを書くのは ``ops.transfer`` だけ**
(旧 ``_apply_cash``・``_record`` は ``ops.transfer`` の中に移した=値は不変)。口は ``cause``(1-3 の原因)を受け取り、
渡された行は出来事を書いて生ログの目印の列(``_raw_event_t_ns``・``_raw_event_seq``)に id を入れる。
K17(回答 10-13b §3): 生ログの輪の容量を ``TRANSFERS_PER_AGENT_PER_DAY`` = 6.5 行/体/日(実測 4.07 の 1.5 倍以上)に
広げた。溢れたら古い行を上書きして続け、溢れた行の数を計器(``meter.overflow``・manifest の ``economy.raw_overflow``)に出す。

正典(境界・経済設計書 §2.3)
- 「``transfer(payer, payee, amount, account_code)`` **単一API**・残高の直接代入は
  **静的に禁止**」。本実装の強制は二重:
  (a) 台帳が持つ配列は既定で ``writeable=False``(``_open`` の中でだけ書ける)。
  (b) ``tests/economy/test_single_write_path.py`` の AST 検査
      (``_lines`` に触れてよいのは本ファイルと ``economy/ops.py`` だけ・``_open`` を呼べるのは本ファイルだけ)。
      〔1-9〕書き手を基本操作 ``ops.transfer`` 1 つに縛る検査は ``tests/economy/cp2/test_cp2_transfer_only_writer.py``。
- 「**検算2本**(Caiani 2016): ①四重記入=取引フロー行列の行和・列和が0(開発時テスト)
  ②全主体の純資産合計=実物資産(在庫+固定資産)の価額が毎期成立(主検算・O(N)総和)」
  → 検査の実装は ``economy.checks``(本モジュールは素材=行列とスナップショットを持つ)。
- 「新規則(ex nihilo禁止)」→ ``AccountCode.ENTRY_CAPITAL`` の支払部門を
  ``accounts.ENTRY_CAPITAL_PAYERS`` に限る(``TransferStatus.EX_NIHILO``)。
- §2.7 第1陣 = 世帯・店舗・外界・銀行(預金のみ)・政府(税sinkのみ)。
- 世界過程設計書 §6 **D-R2-6**: 生の取引ログは O(t) 成長 → **日次で集約行へ畳み、
  生ログは保持窓 N 日**。``growth_declarations()`` が 5 欄の宣言を返す。
- 予算宣言表 **P4**(逐次ループの新設は宣言必須)・**M1/M8**(バイト)。

**世帯の現金は agents.money そのもの**(二重帳簿を作らない)
    ``attach_household_cash(agents.registry.money)`` で個体 SoA の ``money`` 配列を
    **そのまま**現金行に採用する。したがって:
      - 貨幣量の真値は1か所(``agents.money``)。台帳側に写しを持たない。
      - ``agents.money`` は ``AgentState.freeze()`` で読み取り専用なので、
        **resolve の ``writable()`` ブロックの外から transfer を呼ぶと ValueError**
        (= 書き込み口が resolve 1本であることの機械強制)。
        ただし ``np.add.at`` は ``writeable=False`` を**無視して書けてしまう**
        (numpy 2.5.3 実測・親へ報告)ので、``ops.transfer`` がフラグを自前で検査する(1-9 で ``_apply_cash`` から移した)。
    店舗以下の現金・預金・在庫評価額・固定資産・借入は台帳が持つ。

逐次ループ宣言(P4)
1. ``__init__`` / ``freeze`` / ``_open``: **配列本数**ぶん(5行×6部門=30本)。個体数に比例しない。
2. ``transfer``(スカラー版): 1件=1回。ベクトル処理は ``transfer_many``(Python ループ無し)。
3. ``on_day_end``: 部門数×科目数(90)の総和。個体数に比例するのは NumPy の総和のみ。

expedient(本モジュール分)
- 現金残高の制約を課さない部門 = 外界・銀行・政府(``accounts.UNCONSTRAINED_SECTORS``)。
- 同一支払者が同じ ``transfer_many`` に複数行で現れたときの判定は**行順の前置和**
  (最初に残高が尽きた行以降は同一支払者の後続行も不足扱い)。金額は行内で増加するので
  結果は行順にのみ依存し、決定論。
- 生ログの1行 24 B・容量は **N 比例**(``raw_capacity_for`` = 6.5 行/体/日 × N × 保持日数・
  下限 16,384 行)。保持窓を超えた日は先頭を進める。**D-53(2026-09-10)まで固定 262,144 行**
  だったので、cap(= 容量 × 24 B)が N に比例せず 390,067 体で「宣言だけで cap 超過」になった。
  〔1-9・K17〕係数は 3.0 → 6.5(5,000 体 mock 1 日の実測 4.07 行/体/日で 16,384 行の輪から 3,978 行が落ちていた=
  10b-prep #20)。目印の列 2 本(12 B/行)は別の宣言 ``transfer_log_event_ids``。
- 貨幣供給量 M = 世帯+店舗+雇用主の(現金+預金)。設計書は「貨幣供給量」としか書いていない
  ので、銀行の手元現金と外界の相手勘定を除く定義を自前で置いた。
"""

from __future__ import annotations

import math
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Final, Iterator, Mapping, Sequence

import numpy as np

from shibuya.core.growth import GrowthDeclaration, Retention
from shibuya.core.hashing import blake3_hex
from shibuya.economy.accounts import (
    ACCOUNT_NAMES,
    ENTRY_CAPITAL_PAYERS,
    NON_TRANSFERABLE,
    STORED_LINES,
    UNCONSTRAINED_SECTORS,
    AccountCode,
    BalanceLine,
    Sector,
    is_allowed,
)
from shibuya.economy import ops as _OPS
from shibuya.engine.ledger_api import EntityRef, TransferStatus
from shibuya.core.time_consts import NS_PER_SECOND, NS_PER_STEP, STEPS_PER_DAY

__all__ = [
    "RAW_ROW_BYTES",
    "RAW_LINK_BYTES",
    "TRANSFERS_PER_AGENT_PER_DAY",
    "MEASURED_TRANSFERS_PER_AGENT_DAY",
    "K17_MARGIN",
    "event_ids_declaration",
    "DEFAULT_RAW_CAPACITY",
    "MIN_RAW_CAPACITY",
    "DEFAULT_RETENTION_DAYS",
    "raw_capacity_for",
    "INSIDE_SECTORS",
    "DEFAULT_ASSETS_DIR",
    "EmployerTable",
    "load_employers",
    "DayClose",
    "Ledger",
    "growth_declarations",
]

#: 世界資産の既定の置き場(雇用主= W6 の組織台帳)。
DEFAULT_ASSETS_DIR: Final[str] = "data/world/v2"

#: 生ログ 1 行のバイト(tick4+部門1+索引4+部門1+索引4+金額8+科目1 = 23 → 24 に切り上げ)。
RAW_ROW_BYTES: Final[int] = 24
#: 〔1-9〕生ログ 1 行の目印の列のバイト(出来事の id=t_ns 8+seq 4)。宣言は ``transfer_log_event_ids``(1-3 の L8)。
RAW_LINK_BYTES: Final[int] = 12
#: 生ログのリングバッファ容量[行]の**据え置き既定**(``raw_capacity_for`` を使わない
#: 単体呼び出し=モジュール関数 ``growth_declarations()`` の既定値だけに残る・expedient)。
DEFAULT_RAW_CAPACITY: Final[int] = 262_144
#: N 比例容量の下限[行](expedient・D-53)。取引行は個体だけでなく**店舗**からも出る
#: (参入資本 ``endow_stores`` = POI 数ぶん・域外仕入の代金 = 納品数ぶん)ので、
#: 小さな N では 3.0×N を下回る容量になってリングが一周してしまう。
#: 16,384 行 = 393,216 B(据え置き既定 6.29 MB の 1/16)。
MIN_RAW_CAPACITY: Final[int] = 16_384
#: 生ログの保持窓[日](D-R2-6 「保持窓 N 日で退避」)。
DEFAULT_RETENTION_DAYS: Final[int] = 1
#: 1 体あたりの想定 transfer 行数/日(成長宣言の係数・輪の容量の係数)。
#: 〔1-9・K17=回答 10-13b §3〕3.0 → **6.5**(実測 4.07 行/体/日=10b-prep #20 の 1.5 倍以上=6.105 以上)。
#: 実測の値は 5,000 体 mock 1 日の 1 本だけ=係数そのものは expedient(39 万体の実測は無い)。
TRANSFERS_PER_AGENT_PER_DAY: Final[float] = 6.5
#: K17 の根拠の実測(5,000 体 mock 1 日の生ログの行 ÷ 体数)と余裕の倍率(宣言の下限=実測 × 倍率)。
MEASURED_TRANSFERS_PER_AGENT_DAY: Final[float] = 4.07
K17_MARGIN: Final[float] = 1.5
#: bbox 内で貨幣を保有する部門(貨幣供給量 M の定義・expedient)。
INSIDE_SECTORS: Final[tuple[Sector, ...]] = (Sector.HOUSEHOLD, Sector.STORE, Sector.EMPLOYER)

_N_SECTORS: Final[int] = len(Sector)
_N_CODES: Final[int] = len(AccountCode)
_TICKS_PER_DAY: Final[int] = STEPS_PER_DAY


def raw_capacity_for(
    n_households: int, retention_days: int = DEFAULT_RETENTION_DAYS
) -> int:
    """生ログのリングバッファ容量[行]を **N から**決める(D-53・2026-09-10)。

    D-R2-6 の宣言は ``per_day_growth="O(N)"`` × ``156 B/体/日``(6.5 取引 × 24 B・〔1-9・K17〕前は 3.0 取引=72 B)・
    保持窓 ``retention_days`` 日なので、**宣言投影 = 156 × N × 日数**。容量が固定(旧 262,144 行)だと
    cap が N に比例せず ``core.growth.check_growth`` の ``declared_over_cap``(宣言だけで cap 超過=失敗)になる。
    容量を N 比例にして **cap(= 容量 × 24 B)≥ 宣言投影** に揃える(6.5 × N が整数でない奇数の N では 1 日ぶんを
    切り上げる=1 日あたり 1 行未満だけ cap が大きい。日数には比例=1 日ぶんの切り上げ × 日数)。

    Args:
        n_households: 世帯数(= 個体数 N・``check_growth(n_entities=…)`` と同じ N)。
        retention_days: 生ログの保持窓[日]。

    Returns:
        行数(下限 ``MIN_RAW_CAPACITY``)。
    """
    per_day = int(math.ceil(TRANSFERS_PER_AGENT_PER_DAY * max(0, int(n_households))))
    return max(int(MIN_RAW_CAPACITY), per_day * max(0, int(retention_days)))


@dataclass(frozen=True)
class EmployerTable:
    """雇用主(組織)の最小表 = 世界データ W6 の ``w6_org.parquet`` から読む。

    Attributes:
        n: 組織数。
        employees: 組織ごとの従業者数(月次賃金の原資の目安)。
        source: 由来(パス、または ``"synthetic"``)。
    """

    n: int
    employees: np.ndarray
    source: str

    @property
    def total_employees(self) -> int:
        return int(self.employees.sum())


def load_employers(
    path: str | None = DEFAULT_ASSETS_DIR, *, n_synthetic: int = 1, employees: int = 10
) -> EmployerTable:
    """雇用主の表を読む(無ければ合成)。

    層契約により ``shibuya.world`` は import できないので、**Parquet を直接**読む
    (economy が触ってよいのは engine の Protocol と core/manifest + 外部ライブラリ)。
    """
    from pathlib import Path

    if path is not None:
        p = Path(path) / "w6_org.parquet"
        if p.exists():
            import pyarrow.parquet as pq

            table = pq.read_table(p, columns=["employees"])
            emp = np.asarray(table.column("employees").to_numpy(zero_copy_only=False),
                             dtype=np.int64)
            return EmployerTable(n=int(emp.size), employees=emp, source=str(p))
    return EmployerTable(
        n=int(n_synthetic),
        employees=np.full(int(n_synthetic), int(employees), dtype=np.int64),
        source="synthetic",
    )


@dataclass(frozen=True)
class DayClose:
    """``on_day_end`` の戻り(その日の畳み込み結果)。"""

    day: int
    flow: np.ndarray  # (部門, 部門, 科目) その日の取引フロー行列
    d_cash: np.ndarray  # (部門,) その日の現金増減
    d_deposit: np.ndarray
    d_loan: np.ndarray
    raw_rows_kept: int


class Ledger:
    """6部門の貸借対照表 SoA + 取引フロー行列 + 生ログ。

    Example:
        >>> led = Ledger(n_households=3, n_stores=2)
        >>> led.transfer(EntityRef(Sector.ROW, 0), EntityRef(Sector.HOUSEHOLD, 0),
        ...              1_000, AccountCode.CARRY_IN, tick=0)
        <TransferStatus.OK: 0>
        >>> int(led.balance(BalanceLine.CASH, Sector.HOUSEHOLD)[0])
        1000
    """

    def __init__(
        self,
        n_households: int,
        n_stores: int,
        n_employers: int = 1,
        *,
        raw_capacity: int | None = None,
        retention_days: int = DEFAULT_RETENTION_DAYS,
    ) -> None:
        """
        Args:
            n_households: 世帯数(= 個体数)。
            n_stores: 店舗数(= POI 数)。
            n_employers: 雇用主数(組織数。``data/world/v2/w6_org.parquet`` があればその行数)。
            raw_capacity: 生ログのリングバッファ容量[行]。``None``(既定)= ``raw_capacity_for``
                (**N 比例**・D-53)。明示した値は宣言の cap にもそのまま出る。
            retention_days: 生ログの保持窓[日](D-R2-6)。
        """
        if min(int(n_households), int(n_stores), int(n_employers)) < 0:
            raise ValueError("主体数は 0 以上")
        self.sizes: tuple[int, ...] = (
            int(n_households), int(n_stores), int(n_employers), 1, 1, 1
        )
        # 逐次ループ宣言1: 行数×部門数(30 本)
        self._lines: dict[int, list[np.ndarray]] = {
            int(line): [np.zeros(n, dtype=np.int64) for n in self.sizes]
            for line in STORED_LINES
        }
        self._foreign_cash = False
        self._flow = np.zeros((_N_SECTORS, _N_SECTORS, _N_CODES), dtype=np.int64)
        self._flow_daily: list[np.ndarray] = []
        self._last_change_day: list[np.ndarray] = [
            np.zeros(n, dtype=np.int32) for n in self.sizes
        ]
        self._day = 0
        self._snap = self._financial_snapshot()
        #: **期首**(台帳の生成時)の金融スナップ。T3(冗長方程式・D-85 (a))が
        #: 「期首→現在」の窓で検算①を走らせるのに使う。日ごとの増減を貯めると
        #: D-R2-6 の成長宣言(flow_matrix_daily)が動くので、**定数サイズ**のこれで済ませる。
        self._snap0 = self._financial_snapshot()
        #: 直近に畳んだ日の締め(``on_day_end`` の戻り)。**1 件だけ**保持する
        #: (日次センサスが「畳んだ当日の実数」を読むため・D-R2-6 の有界性を壊さない)。
        self._last_close: DayClose | None = None

        # 生ログ(リングバッファ)。容量は **N 比例**(D-53)= 宣言投影と等値の cap になる。
        self.retention_days = int(retention_days)
        self.raw_capacity = (
            raw_capacity_for(int(n_households), self.retention_days)
            if raw_capacity is None
            else int(raw_capacity)
        )
        cap = max(1, self.raw_capacity)
        self._raw_tick = np.zeros(cap, dtype=np.int32)
        self._raw_ps = np.zeros(cap, dtype=np.int8)
        self._raw_pi = np.zeros(cap, dtype=np.int32)
        self._raw_qs = np.zeros(cap, dtype=np.int8)
        self._raw_qi = np.zeros(cap, dtype=np.int32)
        self._raw_amt = np.zeros(cap, dtype=np.int64)
        self._raw_code = np.zeros(cap, dtype=np.int8)
        self._raw_pos = 0  # 次に書く位置(通し番号)
        self._raw_head = 0  # 保持窓の先頭(通し番号)
        self._day_marks: list[tuple[int, int]] = [(0, 0)]
        self.n_raw_dropped = 0
        # 〔1-9〕生ログの行の目印の列(出来事の id=(t_ns, seq)・出来事を書かなかった行は -1)。状態台帳の行 A(diag・
        # discardable)。宣言の係数(K17 の容量の係数)は作ったときの値を控える(manifest の economy に出す)。
        self._raw_event_t_ns = np.full(cap, _OPS.NO_EVENT, dtype=np.int64)
        self._raw_event_seq = np.full(cap, _OPS.NO_EVENT, dtype=np.int32)
        self.raw_rows_per_agent_day = float(TRANSFERS_PER_AGENT_PER_DAY)
        #: 〔1-9〕出来事の記録(1-3 の EventLog・``attach_events`` で挿す)と刻みの幅[ns](口の刻み → t_ns)。
        self._events = None
        self._step_ns = int(NS_PER_STEP)
        #: 〔1-9〕transfer の計器(行・額・原因の無い行・出来事の行・溢れ・日の締めの検算)。
        self.meter = _OPS.TransferMeter()

        #: 却下の計数(``TransferStatus`` 別・診断行の素材)。
        self.rejections: dict[int, int] = {int(s): 0 for s in TransferStatus}
        self.n_transfers = 0
        self._depth = 0
        self.freeze()

    # ---------------------------------------------------------------- 〔1-9〕出来事の記録
    def attach_events(self, sink, step_seconds: int | None = None) -> None:  # noqa: ANN001
        """1-3 の出来事の記録の口を挿す(原因を渡した transfer の行が出来事を書き、生ログに目印を付ける)。

        economy は ``engine.events`` を import できない(層の契約)ので、口は engine の側が作る
        (``engine.events.links.MoneyEventLink``・``LedgerBundle.attach_events`` が作って挿す)。

        Args:
            sink: 出来事を書く口(``MoneyEventLink``=呼べる物と ``enabled``)。``None`` で外す。
            step_seconds: 刻みの幅[秒](口の刻みの番号 → 通しの時刻 ``t_ns``)。``None`` なら今のまま。
        """
        self._events = sink
        if step_seconds is not None:
            if int(step_seconds) <= 0:
                raise ValueError("step_seconds は正")
            self._step_ns = int(step_seconds) * NS_PER_SECOND

    def _t_ns(self, step: int) -> int:
        """口の刻みの番号 → 通しの時刻[ns](刻みの頭)。"""
        return int(step) * self._step_ns

    def raw_position(self) -> int:
        """生ログの次に書く通し番号(``TransferId.first`` と同じ数え方)。"""
        return int(self._raw_pos)

    def raw_event_ids(self) -> tuple[np.ndarray, np.ndarray]:
        """保持窓内の生ログの行の目印 ``(t_ns, seq)``(``raw_rows`` と同じ並び・出来事の無い行は -1)。"""
        cap = self._raw_tick.size
        n = int(self._raw_pos - self._raw_head)
        if n <= 0:
            return np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int32)
        slot = (self._raw_head + np.arange(n, dtype=np.int64)) % cap
        return self._raw_event_t_ns[slot].copy(), self._raw_event_seq[slot].copy()

    def event_ids_between(self, first: int, last: int) -> tuple[np.ndarray, np.ndarray]:
        """通し番号 ``[first, last)`` の行の目印(輪から落ちた行は -1)。"""
        pos = np.arange(int(first), int(last), dtype=np.int64)
        t = np.full(pos.size, _OPS.NO_EVENT, dtype=np.int64)
        s = np.full(pos.size, _OPS.NO_EVENT, dtype=np.int32)
        live = pos >= self._raw_head
        if live.any():
            slot = pos[live] % self._raw_tick.size
            t[live] = self._raw_event_t_ns[slot]
            s[live] = self._raw_event_seq[slot]
        return t, s

    def economy_record(self) -> dict[str, object]:
        """manifest の ``economy`` の欄(K17 の容量と溢れ・transfer の計器)。"""
        m = self.meter
        return {
            "raw_capacity": int(self.raw_capacity),
            "raw_rows_per_agent_day": float(self.raw_rows_per_agent_day),
            "raw_row_bytes": int(RAW_ROW_BYTES),
            "raw_link_bytes": int(RAW_LINK_BYTES),
            "raw_overflow": int(m.overflow),
            "raw_overflow_policy": "上書きして数える(止めない)",
            "transfers_total": int(m.rows),
            "transfers_amount": int(m.amount),
            "transfers_uncaused": int(m.uncaused),
            "transfer_events": int(m.events),
        }

    # ---------------------------------------------------------------- 書き込みガード
    @property
    def frozen(self) -> bool:
        return self._depth == 0

    def freeze(self) -> None:
        """台帳が持つ配列を読み取り専用にする(逐次ループ宣言1)。

        **注意**: ``attach_household_cash`` で採用した外部配列(``agents.money``)の
        フラグは触らない——その配列の書き込み窓は ``engine.resolve`` が持つ。
        """
        for line, arrays in self._lines.items():
            for s, arr in enumerate(arrays):
                if self._foreign_cash and line == int(BalanceLine.CASH) and s == int(
                    Sector.HOUSEHOLD
                ):
                    continue
                arr.flags.writeable = False

    def _unfreeze(self) -> None:
        for line, arrays in self._lines.items():
            for s, arr in enumerate(arrays):
                if self._foreign_cash and line == int(BalanceLine.CASH) and s == int(
                    Sector.HOUSEHOLD
                ):
                    continue
                arr.flags.writeable = True

    @contextmanager
    def _open(self) -> Iterator["Ledger"]:
        """台帳配列を書ける窓(再入可)。**呼んでよいのは本ファイルだけ**(AST 検査)。"""
        if self._depth == 0:
            self._unfreeze()
        self._depth += 1
        try:
            yield self
        finally:
            self._depth -= 1
            if self._depth == 0:
                self.freeze()

    @contextmanager
    def _unlocked(self) -> Iterator["Ledger"]:
        """基本操作 ``economy.ops.transfer`` が台帳の配列を書く窓(``_open`` と同じ・再入可)。

        〔1-9・検収 M2〕前は公開の ``unlocked`` だった(``with led.unlocked(): led.balance(...)[i] = x`` で transfer の外から
        残高を書けた)。内部の名にし、**呼んでよいのは ``economy/ops.py`` の ``transfer`` だけ**=AST の試験
        ``tests/economy/cp2/test_cp2_write_window.py``(別名・属性の鎖・``getattr`` の文字列も見る)。
        """
        with self._open():
            yield self

    # ---------------------------------------------------------------- 参照
    def balance(self, line: int, sector: int) -> np.ndarray:
        """貸借対照表の1行×1部門の配列(**読み取り専用**)。"""
        return self._lines[int(line)][int(sector)]

    def attach_household_cash(self, money: np.ndarray) -> None:
        """世帯の現金行として個体 SoA の ``money`` 配列を採用する(写しを作らない)。

        Raises:
            ValueError: 長さが世帯数と違う / 既存の残高が 0 でない。
        """
        arr = np.asarray(money)
        if arr.ndim != 1 or arr.shape[0] != self.sizes[int(Sector.HOUSEHOLD)]:
            raise ValueError(
                f"世帯数 {self.sizes[int(Sector.HOUSEHOLD)]} と money 配列 {arr.shape} が合わない"
            )
        cur = self._lines[int(BalanceLine.CASH)][int(Sector.HOUSEHOLD)]
        if int(cur.sum()) != 0:
            raise ValueError("既に世帯現金が動いている台帳には attach できない")
        self._lines[int(BalanceLine.CASH)][int(Sector.HOUSEHOLD)] = arr
        self._foreign_cash = True
        # 期首スナップは**世帯の行だけ**差し替える。全部門を撮り直すと、attach より前に
        # 立っていた取引(``endow_stores`` の参入資本など)が期首へ吸い込まれて
        # ``_flow`` にだけ残り、締めた日の検算①(部門ごとの列和 = Δ現金)が落ちる
        # (層2レビューで日次センサスが締めた日を見るようになって初めて現れた)。
        adopted = int(arr.astype(np.int64).sum())
        snap_cash = self._snap["cash"].copy()
        snap_cash[int(Sector.HOUSEHOLD)] = adopted
        self._snap["cash"] = snap_cash
        # 期首スナップ(T3 の窓の左端)にも**同じ段差**を入れる。入れないと、採用した配列に
        # 既に載っていた現金が「フローの無い残高増」として T3 に出てしまう(日次の検算①は
        # 上の _snap のずらしで既に除いている)。既定経路では採用時点の money は 0 なので
        # 段差も 0 =1 バイトも変わらない。
        snap0_cash = self._snap0["cash"].copy()
        snap0_cash[int(Sector.HOUSEHOLD)] += adopted - int(cur.astype(np.int64).sum())
        self._snap0["cash"] = snap0_cash

    def last_change_day(self, sector: int) -> np.ndarray:
        """部門ごとの「最後に現金/預金が動いた日」(退蔵項の計上に使う)。"""
        return self._last_change_day[int(sector)]

    def net_worth(self, sector: int) -> np.ndarray:
        """純資産(導出)= 現金+預金+在庫+固定資産−借入。"""
        s = int(sector)
        L = self._lines
        return (
            L[int(BalanceLine.CASH)][s].astype(np.int64)
            + L[int(BalanceLine.DEPOSIT)][s]
            + L[int(BalanceLine.INVENTORY)][s]
            + L[int(BalanceLine.FIXED_ASSET)][s]
            - L[int(BalanceLine.LOAN)][s]
        )

    def sector_totals(self, line: int) -> np.ndarray:
        """部門別の合計(``(6,)`` int64)。"""
        return np.array(
            [int(self._lines[int(line)][s].sum()) for s in range(_N_SECTORS)], dtype=np.int64
        )

    def money_supply(self) -> int:
        """貨幣供給量 M = 世帯+店舗+雇用主の(現金+預金)(expedient な定義)。"""
        cash = self.sector_totals(BalanceLine.CASH)
        dep = self.sector_totals(BalanceLine.DEPOSIT)
        return int(sum(int(cash[int(s)] + dep[int(s)]) for s in INSIDE_SECTORS))

    @property
    def flow(self) -> np.ndarray:
        """その日の取引フロー行列 ``(部門, 部門, 科目)``(読み取り専用ビュー)。"""
        v = self._flow.view()
        v.flags.writeable = False
        return v

    @property
    def flow_daily(self) -> tuple[np.ndarray, ...]:
        """日次で畳んだ取引フロー行列(``on_day_end`` の履歴)。"""
        return tuple(self._flow_daily)

    def signed_flow(self, flow: np.ndarray | None = None) -> np.ndarray:
        """``(部門, 科目)`` の符号つき流入(受取 − 支払)。"""
        f = self._flow if flow is None else np.asarray(flow)
        return f.sum(axis=0) - f.sum(axis=1)

    def financial_delta(self) -> dict[str, np.ndarray]:
        """前回の日次締め(または生成時)からの部門別増減(現金・預金・借入)。"""
        now = self._financial_snapshot()
        return {k: now[k] - self._snap[k] for k in now}

    def _financial_snapshot(self) -> dict[str, np.ndarray]:
        return {
            "cash": self.sector_totals(BalanceLine.CASH),
            "deposit": self.sector_totals(BalanceLine.DEPOSIT),
            "loan": self.sector_totals(BalanceLine.LOAN),
        }

    # ---------------------------------------------------------------- 単一API
    def transfer(
        self,
        payer: EntityRef | Sequence[int],
        payee: EntityRef | Sequence[int],
        amount: int,
        code: int,
        tick: int,
        *,
        cause=None,  # noqa: ANN001
    ) -> TransferStatus:
        """**単一API**(§2.3)。1件の資金移動。業務上の失敗は例外にせず戻り値で返す。

        〔1-9〕検査に通った行は基本操作 ``ops.transfer`` が書く(値は不変)。

        Args:
            payer / payee: ``EntityRef(部門, 索引)``。
            amount: 金額[円](正の整数のみ)。
            code: ``AccountCode``。
            tick: 現在の刻み(生ログの時刻)。
            cause: 1-3 の原因(渡すと出来事を書き、生ログの行に目印を付ける)。

        Returns:
            ``TransferStatus``。
        """
        ps, pi = int(payer[0]), int(payer[1])
        qs, qi = int(payee[0]), int(payee[1])
        status = self._validate_scalar(ps, pi, qs, qi, amount, code)
        if status != TransferStatus.OK:
            self.rejections[int(status)] += 1
            return status
        amt = int(amount)
        c = AccountCode(int(code))
        _OPS.transfer(self, (ps, np.array([pi])), (qs, np.array([qi])), np.array([amt], np.int64),
                      _OPS.what_of(c), cause, self._t_ns(tick))
        return TransferStatus.OK

    def transfer_many(
        self,
        payer_sector: int,
        payers: np.ndarray,
        payee_sector: int,
        payees: np.ndarray,
        amounts: np.ndarray,
        code: int,
        tick: int,
        *,
        cause=None,  # noqa: ANN001
    ) -> np.ndarray:
        """ベクトル版(P4: 個体数ぶんの Python ループを作らない)。

        〔1-9〕検査に通った行は基本操作 ``ops.transfer`` が書く(値は不変)。``cause`` は 1-3 の原因。

        Returns:
            行ごとの ``TransferStatus`` を並べた ``int8`` 配列。
        """
        p = np.asarray(payers, dtype=np.int64).ravel()
        q = np.asarray(payees, dtype=np.int64).ravel()
        a = np.asarray(amounts, dtype=np.int64).ravel()
        if not (p.size == q.size == a.size):
            raise ValueError(f"行数が揃っていない: {p.size} / {q.size} / {a.size}")
        out = np.full(p.size, int(TransferStatus.OK), dtype=np.int8)
        if p.size == 0:
            return out
        ps, qs = int(payer_sector), int(payee_sector)

        head = self._validate_pair(ps, qs, code)
        if head != TransferStatus.OK:
            out[:] = int(head)
            self.rejections[int(head)] += p.size
            return out
        c = AccountCode(int(code))

        bad = a <= 0
        out[bad] = int(TransferStatus.BAD_AMOUNT)
        n_p, n_q = self.sizes[ps], self.sizes[qs]
        oob = (p < 0) | (p >= n_p) | (q < 0) | (q >= n_q)
        out[oob & (out == int(TransferStatus.OK))] = int(TransferStatus.BAD_ENTITY)

        live = out == int(TransferStatus.OK)
        if Sector(ps) not in UNCONSTRAINED_SECTORS and live.any():
            cash = self._lines[int(BalanceLine.CASH)][ps]
            need = self._running_need(p[live], a[live])
            short = need > cash[p[live]].astype(np.int64)
            idx = np.flatnonzero(live)[short]
            out[idx] = int(TransferStatus.INSUFFICIENT_FUNDS)
            live = out == int(TransferStatus.OK)

        for s in TransferStatus:
            if s != TransferStatus.OK:
                n = int(np.count_nonzero(out == int(s)))
                if n:
                    self.rejections[int(s)] += n
        if not live.any():
            return out
        _OPS.transfer(self, (ps, p[live]), (qs, q[live]), a[live], _OPS.what_of(c), cause, self._t_ns(tick))
        return out

    # ---------------------------------------------------------------- 便利な入口
    def purchase_many(
        self, buyers: np.ndarray, stores: np.ndarray, amounts: np.ndarray, tick: int, *, cause=None  # noqa: ANN001
    ) -> np.ndarray:
        """購入の金の脚(世帯→店舗・消費支出)。engine から呼ばれる唯一の購入口。"""
        return self.transfer_many(
            int(Sector.HOUSEHOLD), buyers, int(Sector.STORE), stores,
            amounts, int(AccountCode.CONSUMPTION), tick, cause=cause,
        )

    def endow_households(self, amounts: np.ndarray, tick: int = 0, *, cause=None) -> np.ndarray:  # noqa: ANN001
        """初期財布(外界→世帯・来街者持込)。**直接代入ではなく transfer**(ex nihilo 禁止)。

        expedient: 居住者の初期現金も「来街者持込」科目で入れる。設計書 §2.2 の 12 科目に
        「初期ストックの注入」に当たる科目が無いため(親へ報告済みの食い違い)。
        """
        a = np.asarray(amounts, dtype=np.int64).ravel()
        idx = np.arange(a.size, dtype=np.int64)
        return self.transfer_many(
            int(Sector.ROW), np.zeros(a.size, dtype=np.int64),
            int(Sector.HOUSEHOLD), idx, a,
            int(AccountCode.CARRY_IN), tick, cause=cause,
        )

    def endow_stores(
        self, cash: np.ndarray, tick: int = 0, *, payer: Sector = Sector.ROW, cause=None  # noqa: ANN001
    ) -> np.ndarray:
        """店舗の参入資本(創業者預金・銀行貸出・外界のいずれか由来=ex nihilo 禁止)。"""
        a = np.asarray(cash, dtype=np.int64).ravel()
        idx = np.arange(a.size, dtype=np.int64)
        return self.transfer_many(
            int(payer), np.zeros(a.size, dtype=np.int64),
            int(Sector.STORE), idx, a,
            int(AccountCode.ENTRY_CAPITAL), tick, cause=cause,
        )

    def depreciate(
        self, sector: int, index: np.ndarray, amount: np.ndarray, tick: int, *, cause=None  # noqa: ANN001
    ) -> None:
        """減価償却(**自己ループ**・現金は動かない)。固定資産と純資産だけが減る。

        設計書の 12 科目に入っているが相手方が無い(親へ報告した食い違い #1)。
        〔1-9〕通った行は基本操作 ``ops.transfer`` が自己ループ(src=dst)として書く(値は不変)。
        """
        s = int(sector)
        i = np.asarray(index, dtype=np.int64).ravel()
        a = np.asarray(amount, dtype=np.int64).ravel()
        if not is_allowed(int(AccountCode.DEPRECIATION), s, s):
            raise ValueError(f"減価償却が許されない部門: {Sector(s).name}")
        keep = (a > 0) & (i >= 0) & (i < self.sizes[s])
        if not keep.any():
            return
        _OPS.transfer(self, (s, i[keep]), (s, i[keep]), a[keep], _OPS.what_of(AccountCode.DEPRECIATION), cause,
                      self._t_ns(tick))

    def revalue_inventory(self, sector: int, values: np.ndarray) -> None:
        """在庫評価額[円]の書き換え(**金は動かない**ので transfer ではない)。

        U-Goods 側(``economy.goods``)が数量×標準原価で計算した値をここへ入れる。
        検算②の恒等式(Σ純資産 = Σ実物資産 ⟺ Σ金融純資産 = 0)は在庫の評価額に依存しない
        ——在庫は左辺と右辺の**両方**に同額で入るため。
        """
        s = int(sector)
        v = np.asarray(values, dtype=np.int64).ravel()
        if v.size != self.sizes[s]:
            raise ValueError(f"部門 {Sector(s).name} の主体数 {self.sizes[s]} と合わない: {v.size}")
        with self._open():
            self._lines[int(BalanceLine.INVENTORY)][s][:] = v

    # ---------------------------------------------------------------- 内部
    def _validate_pair(self, ps: int, qs: int, code: int) -> TransferStatus:
        try:
            c = AccountCode(int(code))
        except ValueError:
            return TransferStatus.UNKNOWN_CODE
        if c in NON_TRANSFERABLE:
            return TransferStatus.UNKNOWN_CODE
        if not (0 <= ps < _N_SECTORS and 0 <= qs < _N_SECTORS):
            return TransferStatus.BAD_ENTITY
        if c == AccountCode.ENTRY_CAPITAL and Sector(ps) not in ENTRY_CAPITAL_PAYERS:
            return TransferStatus.EX_NIHILO
        if c == AccountCode.DEPRECIATION:
            # 〔1-9・検収 M1・宣言つきの直し〕減価償却は自己ループ(固定資産だけが減る・現金は動かない)で、入口は
            # ``depreciate`` だけ。汎用の口(``transfer``・``transfer_many``)に渡すと HEAD は現金の脚で動かしていた
            # (別の口なら現金が移り・同じ口なら差し引き 0 で取引の件数だけ増える=accounts の「現金を動かさない」に反する
            # 潜在の欠陥)。行の状態 FORBIDDEN_PAIR で返す(例外にしない)。engine からの呼び手は無い=到達しない入力。
            return TransferStatus.FORBIDDEN_PAIR
        if not is_allowed(int(c), ps, qs):
            return TransferStatus.FORBIDDEN_PAIR
        return TransferStatus.OK

    def _validate_scalar(
        self, ps: int, pi: int, qs: int, qi: int, amount: int, code: int
    ) -> TransferStatus:
        head = self._validate_pair(ps, qs, code)
        if head != TransferStatus.OK:
            return head
        if not isinstance(amount, (int, np.integer)) or int(amount) <= 0:
            return TransferStatus.BAD_AMOUNT
        if not (0 <= pi < self.sizes[ps]) or not (0 <= qi < self.sizes[qs]):
            return TransferStatus.BAD_ENTITY
        if Sector(ps) not in UNCONSTRAINED_SECTORS:
            if int(self._lines[int(BalanceLine.CASH)][ps][pi]) < int(amount):
                return TransferStatus.INSUFFICIENT_FUNDS
        return TransferStatus.OK

    @staticmethod
    def _running_need(payers: np.ndarray, amounts: np.ndarray) -> np.ndarray:
        """同一支払者の**行順前置和**(重複支払者の残高判定・expedient)。"""
        order = np.argsort(payers, kind="stable")
        sp = payers[order]
        sa = amounts[order]
        csum = np.cumsum(sa)
        start = np.searchsorted(sp, sp, side="left")
        prior = np.where(start > 0, csum[np.maximum(start - 1, 0)], 0)
        running_sorted = csum - prior
        running = np.empty_like(running_sorted)
        running[order] = running_sorted
        return running

    def raw_rows(self) -> np.ndarray:
        """保持窓内の生ログ ``(n, 7)``(tick・支払部門・支払索引・受取部門・受取索引・金額・科目)。"""
        cap = self._raw_tick.size
        n = int(self._raw_pos - self._raw_head)
        if n <= 0:
            return np.zeros((0, 7), dtype=np.int64)
        slot = (self._raw_head + np.arange(n, dtype=np.int64)) % cap
        return np.stack(
            [
                self._raw_tick[slot].astype(np.int64),
                self._raw_ps[slot].astype(np.int64),
                self._raw_pi[slot].astype(np.int64),
                self._raw_qs[slot].astype(np.int64),
                self._raw_qi[slot].astype(np.int64),
                self._raw_amt[slot],
                self._raw_code[slot].astype(np.int64),
            ],
            axis=1,
        )

    # ---------------------------------------------------------------- 日次
    def on_day_end(self, day: int | None = None) -> DayClose:
        """日次の畳み込み(D-R2-6)。取引行列を集約行へ積み、生ログの保持窓を進める。

        逐次ループ宣言3: 部門×科目(90)の総和。
        """
        d = self._day if day is None else int(day)
        snap_now = self._financial_snapshot()
        close = DayClose(
            day=d,
            flow=self._flow.copy(),
            d_cash=snap_now["cash"] - self._snap["cash"],
            d_deposit=snap_now["deposit"] - self._snap["deposit"],
            d_loan=snap_now["loan"] - self._snap["loan"],
            raw_rows_kept=int(self._raw_pos - self._raw_head),
        )
        self._flow_daily.append(close.flow)
        # 〔1-9〕新しい検算 1 本: その日の transfer の額の和=流れの表の和(起点からの増え)。計器だけ(締めは止めない)
        self.meter.close_day(d, int(self._flow.sum()))
        self._flow[:] = 0
        self._snap = snap_now
        self._day = d + 1
        self._day_marks.append((self._day, self._raw_pos))
        # 保持窓 N 日: 古い日の生ログは集約行(_flow_daily)に畳まれているので先頭を進める
        cutoff_day = self._day - max(0, self.retention_days)
        for marked_day, marked_pos in self._day_marks:
            if marked_day <= cutoff_day and marked_pos > self._raw_head:
                self.n_raw_dropped += int(marked_pos - self._raw_head)
                self._raw_head = marked_pos
        self._day_marks = [m for m in self._day_marks if m[0] > cutoff_day]
        self._last_close = close
        return close

    def cumulative_close(self) -> DayClose:
        """**期首(台帳の生成時)から現在まで**を 1 つの締めに畳んだ ``DayClose``。

        T3(冗長方程式・D-85 (a))の窓。日次の締め(``on_day_end``)と同じ形で返すので、
        検算①(``checks.flow_matrix_balanced``)を**そのまま**走らせられる(再実装しない)。

        - 取引フロー行列 = 畳んだ日の集約行(``flow_daily``)+ **まだ畳んでいない当日**。
        - 部門別の増減 = 現在の残高 − 期首スナップ(``_snap0``)。
          日ごとの増減は望遠鏡的に畳まれるので、これは各日の ``DayClose`` の増減の総和に等しい。

        逐次ループ宣言(P4): 畳んだ日数ぶんの (6,6,15) 加算。**個体数にも tick 数にも
        比例しない**(保持窓 400 日 × 540 要素が上限)。
        """
        flow = np.zeros_like(self._flow)
        for f in self._flow_daily:
            flow += f
        flow += self._flow
        now = self._financial_snapshot()
        return DayClose(
            day=self._day,
            flow=flow,
            d_cash=now["cash"] - self._snap0["cash"],
            d_deposit=now["deposit"] - self._snap0["deposit"],
            d_loan=now["loan"] - self._snap0["loan"],
            raw_rows_kept=int(self._raw_pos - self._raw_head),
        )

    @property
    def last_close(self) -> "DayClose | None":
        """直近に畳んだ日の ``DayClose``(まだ 1 日も畳んでいなければ ``None``)。"""
        return self._last_close

    def close_for(self, day: int) -> "DayClose | None":
        """``day`` が**直近に畳んだ日**ならその ``DayClose`` を返す(違えば ``None``)。

        日次センサス(``economy.census.daily_census``)が「締めたあとに締めた日を評価する」
        ために使う。締めると ``self._flow`` は 0 に戻るので、締め後に現在値を読むと
        faucet/sink/残差が全部 0 の**空虚な行**になってしまう(層2レビュー指摘)。
        """
        c = self._last_close
        if c is None or int(c.day) != int(day):
            return None
        return c

    @property
    def day(self) -> int:
        return self._day

    # ---------------------------------------------------------------- 監査
    def state_hash(self) -> str:
        """全残高+取引行列の blake3(checkpoint 一致判定に使える)。"""
        parts: list[bytes] = [b"shibuya.economy.ledger/v1"]
        for line in STORED_LINES:
            for s in range(_N_SECTORS):
                arr = np.ascontiguousarray(self._lines[int(line)][s])
                parts.append(f"{int(line)}:{s}:{arr.dtype.str}".encode("ascii"))
                parts.append(arr.reshape(-1).view(np.uint8).tobytes() if arr.size else b"")
        parts.append(np.ascontiguousarray(self._flow).view(np.uint8).tobytes())
        return blake3_hex(b"\x1f".join(parts))

    def bytes_total(self) -> int:
        """台帳が確保している実バイト(生ログ込み)。"""
        own = sum(
            int(a.nbytes)
            for line, arrays in self._lines.items()
            for s, a in enumerate(arrays)
            if not (self._foreign_cash and line == int(BalanceLine.CASH)
                    and s == int(Sector.HOUSEHOLD))
        )
        own += sum(int(a.nbytes) for a in self._last_change_day)
        own += int(self._flow.nbytes) + sum(int(f.nbytes) for f in self._flow_daily)
        own += self._raw_tick.size * (RAW_ROW_BYTES + RAW_LINK_BYTES)  # 〔1-9〕目印の列 12 B/行
        return own

    # ---------------------------------------------------------------- D-R2-6
    def growth_declarations(self) -> Mapping[str, GrowthDeclaration]:
        """この台帳の状態成長宣言(``growth_measured`` と**同じ鍵**で返す)。

        engine は economy を import できない(層契約)ので、``engine.run`` の D-R2-6 ゲートは
        ``LedgerBundle`` 経由でこの 2 本を受け取る(依存逆転)。
        """
        decls = growth_declarations(
            raw_capacity=self.raw_capacity, retention_days=self.retention_days
        )
        out = {k: decls[k] for k in ("transfer_log", "flow_matrix_daily")}
        out["transfer_log_event_ids"] = event_ids_declaration(
            raw_capacity=self.raw_capacity, retention_days=self.retention_days
        )
        return out

    def growth_measured(self) -> Mapping[str, int]:
        """D-R2-6 の**実測増分バイト**(保持窓の中に残っている生ログ+集約行・〔1-9〕目印の列)。"""
        live = int(self._raw_pos - self._raw_head)
        return {
            "transfer_log": live * RAW_ROW_BYTES,
            "flow_matrix_daily": sum(int(f.nbytes) for f in self._flow_daily),
            "transfer_log_event_ids": live * RAW_LINK_BYTES,
        }

    def summary(self) -> str:
        cash = self.sector_totals(BalanceLine.CASH)
        return (
            f"[ledger] 世帯{self.sizes[0]:,} 店舗{self.sizes[1]:,} 雇用主{self.sizes[2]:,} "
            f"/ M={self.money_supply():,}円 / transfer {self.n_transfers:,}件 "
            f"/ 現金部門別 {dict(zip([s.name for s in Sector], cash.tolist()))}"
        )

    def account_totals(self, flow: np.ndarray | None = None) -> dict[str, int]:
        """科目別の総額(名前 → 円)。"""
        f = self._flow if flow is None else np.asarray(flow)
        return {
            ACCOUNT_NAMES[int(c)]: int(f[:, :, int(c)].sum()) for c in AccountCode
        }


def growth_declarations(
    *, raw_capacity: int = DEFAULT_RAW_CAPACITY, retention_days: int = DEFAULT_RETENTION_DAYS
) -> Mapping[str, GrowthDeclaration]:
    """金の台帳の状態成長宣言(D-R2-6 の 5 欄)。

    ``transfer_log`` が O(t) 再発の最有力地点(ActualLog と同型)なので、
    **保持窓 N 日 + 日次集約**を宣言に書き、``engine.run`` の実測と突き合わせる。

    ``raw_capacity`` は ``transfer_log`` の cap(= 容量 × 24 B)になる。台帳インスタンスから
    呼ぶとき(``Ledger.growth_declarations``)は **N 比例**の実容量が入るので
    cap ≥ 宣言投影(156 B/体/日 × N × 保持日数・〔1-9・K17〕前は 72 B)になる(D-53・奇数の N では切り上げの 1 行ぶん
    だけ大きい)。引数を省いた単体呼び出しは据え置きの ``DEFAULT_RAW_CAPACITY``(6.29 MB)= **N を知らない場面の目安**。
    """
    rows = (
        GrowthDeclaration(
            name="transfer_log",
            per_agent_bytes=0,
            per_cell_bytes=0,
            per_day_growth="O(N)",
            per_day_growth_coef=float(TRANSFERS_PER_AGENT_PER_DAY * RAW_ROW_BYTES),
            retention=Retention(days=retention_days, target="日次取引フロー行列(flow_daily)へ集約"),
            worst_case_ops_per_tick=0,
            cap=int(raw_capacity) * RAW_ROW_BYTES,
            cap_budget_row="S1/M8(親が割当・要 delta)",
            mechanism=True,
            note=(
                "境界・経済設計書 §2.3 の取引ログ。1 行 24 B・リングバッファで有界化し、"
                "日次で取引フロー行列へ畳む(D-R2-6 の ActualLog 規律を金の台帳へ適用)。"
                "容量は N 比例(raw_capacity_for・D-53 2026-09-10)なので cap は 156 B/体/日 × N ×"
                " 保持日数以上(〔1-9・K17〕6.5 行/体/日=実測 4.07 の 1.5 倍以上。前は 3.0 行=72 B)。"
                "溢れたら上書きして数える(manifest の economy.raw_overflow)。"
            ),
            unit="transfer",
            bytes_per_unit=RAW_ROW_BYTES,
            growth_per_simday=TRANSFERS_PER_AGENT_PER_DAY,
        ),
        GrowthDeclaration(
            name="flow_matrix_daily",
            per_agent_bytes=0,
            per_cell_bytes=0,
            per_day_growth="O(1)",
            per_day_growth_coef=float(_N_SECTORS * _N_SECTORS * _N_CODES * 8),
            retention=Retention(days=400, target="月次 MER(census.monthly_mer)へ集約"),
            worst_case_ops_per_tick=0,
            cap=16_000_000,
            cap_budget_row="S1(親が割当・要 delta)",
            mechanism=True,
            note="6×6×15 の int64 = 4,320 B/日。日次センサス(§2.4)の素材。",
            unit="day",
            bytes_per_unit=_N_SECTORS * _N_SECTORS * _N_CODES * 8,
            growth_per_simday=1.0,
        ),
        GrowthDeclaration(
            name="ledger_balances",
            per_agent_bytes=8 * 4 + 4,  # 預金・在庫・固定資産・借入(現金は agents.money)+ 最終変動日
            per_cell_bytes=8 * 5 + 4,  # 店舗(POI)側の 5 行 + 最終変動日
            per_day_growth="O(1)",
            per_day_growth_coef=0.0,
            retention=Retention(days=None),
            worst_case_ops_per_tick=0,
            cap=512_000_000,
            cap_budget_row="M8(親が割当・要 delta)",
            mechanism=True,
            note=(
                "貸借対照表 5 行 × 6 部門の SoA。日をまたいで伸びない(残高は上書き)ので"
                "**実測側には増分 0 を渡す**(定常サイズは per_agent_bytes/per_cell_bytes 欄)。"
                "40万世帯で 36 B/体 = 14.4 MB。"
            ),
            unit="entity",
            bytes_per_unit=8 * 5,
        ),
    )
    return {d.name: d for d in rows}


def event_ids_declaration(
    *, raw_capacity: int = DEFAULT_RAW_CAPACITY, retention_days: int = DEFAULT_RETENTION_DAYS
) -> GrowthDeclaration:
    """〔1-9〕生ログの行の目印の列(出来事の id=t_ns 8 B+seq 4 B=12 B/行)の成長宣言(1-3 の L8)。

    輪と同じ容量・保持窓(列は輪の行ごとに 1 つ)。軸 1 diag・軸 2 discardable(状態台帳の行 A)。
    """
    return GrowthDeclaration(
        name="transfer_log_event_ids",
        per_agent_bytes=0,
        per_cell_bytes=0,
        per_day_growth="O(N)",
        per_day_growth_coef=float(TRANSFERS_PER_AGENT_PER_DAY * RAW_LINK_BYTES),
        retention=Retention(days=retention_days, target="生ログの輪と同じ(行と一緒に上書き・畳む)"),
        worst_case_ops_per_tick=0,
        cap=int(raw_capacity) * RAW_LINK_BYTES,
        cap_budget_row="S1/M8(親が割当・要 delta)",
        mechanism=True,
        note=(
            "第 1 期 1-9: 金の生ログの行ごとの出来事の id(1-3 の EventLog の (t_ns, seq))。出来事を書かなかった行は -1。"
            "容量は輪と同じ(raw_capacity_for=6.5 行/体/日 × N × 保持日数)。"
        ),
        unit="transfer",
        bytes_per_unit=RAW_LINK_BYTES,
        growth_per_simday=TRANSFERS_PER_AGENT_PER_DAY,
    )
