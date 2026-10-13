"""engine.memory_store — 記憶の器 M0(第 1 期 1-6・MR-0・MR11 (b)・MR16)。

口の約束: ``docs/design/v2-foundation-contracts-2026-10-13.md`` の「1-6 記憶の器 M0」。置き場は口の約束の
``engine/memory/store.py`` でなく 1 本のモジュール ``engine/memory_store.py``(親の判断=今の ``engine/memory.py`` を
package にせず、import-linter と setuptools の検査の中に置く)。計画 1-6=M0 は**器と出どころだけ**
(強さの秒化・容量の廃止・表の統合は M1 の腕)。決定 10-12 §4-6 MR-0・MR11 (b)・MR16・回答 10-13b §3(テープの列は版 4 の
中で足してよい)。

記憶の行(体ごとに ``n_rows`` 行の範囲 ``[体 × n_rows, (体 + 1) × n_rows)``=SoA の列)
    - ``event_id``(目印): 出来事の id ``(t_ns, seq)``(1-3 の ``EventId``)。同じ鍵の出来事が重なった行は**最後の出来事**を
      指す(今の表の ``mem_last``・``mem_cell`` と同じ「最後の回」)。
    - ``strength``(System 1 の数=MR-0・LLM には見せない): 回数 ``n``・重要度 ``importance``・最初に書かれた時刻
      ``first_ns``。想起の強さ A はこれと「いま」から System 1 が計算する(M0 は今の式=``engine.memory.activation_rows``・
      刻みの単位の近似 #56。秒化は M1)。
    - ``annotation``(一人ずつの注釈): 会話の要旨(今の ``MemoryLayer.gist`` と同じ 40 字・体あたり 16 件・古い順に落とす)。
    - ``origin``(出どころの欄=範囲の外からの印): ``None``=出来事の記録(1-3)にある出来事への目印 / ``"legacy"``=記録に
      無い出来事(体の出来事=1-3 では体の系を記録に配線していない)の**仮の行**。
    - ``shown``(録画=MR16): 最後に LLM に見せた時刻 ``t_ns``(−1=まだ見せていない)。この呼び出しで見せたか=
      ``shown_ns`` がその呼び出しの時刻と同じか。
    仮の出来事の表(``_lg_*``): 記録に無い出来事の中身(種類・相手・対象・結果・セル)。行と同じ番地 k に置き、目印は
    ``(t_ns, −1 − k)``(seq が負=記録の外の仮の id。記録の id の seq は 0 以上なので重ならない)。体の出来事が出来事の
    記録に載る段で、仮の行は記録の目印に置き換わる(この表は消える)。仮の行はつなぎ=外す段は親が台帳(1-4)で決める
    (候補 1-8)。

書く口は 2 つ: :meth:`MemoryStore.remember`(出来事を覚える=同じ鍵は重ねる・空の行・満杯なら score 最小を追い出す=
今の表 ``engine.memory`` と同じ規則)と :meth:`MemoryStore.mark_shown`(録画)。ほかに再開のときの作り直し
:meth:`MemoryStore.rebuild`(系の外だけ・行 M0 の欄だけ)(記憶の表から作り直す=状態台帳の行 M0 は「作り直せる」)と、テープの列へ渡す控えの取り出し
:meth:`MemoryStore.take_shown`。欄の付け替えは ``__setattr__`` が落とす(配列の中身の書き換えは口の中だけ=約束)。

読み口 :meth:`MemoryStore.recall` は ``MemoryView`` の組を返す。``MemoryView`` は LLM に見せる形=言葉(はっきり/うろ覚え
=強さの段)と中身の粗さ(MR-0)と中身の ID(描き方が語にする)だけで、強さの数を持たない。:func:`render_memories` は
``MemoryView`` を今の描き方(B5「記憶」の 1 行・テンプレ v1.3)と同じバイトの文にする(1-2 の ``Percept`` への結線は
1-2 の取り込みの後)。

腕(切替口): ``--memory-store events``(環境変数 ``SHIBUYA_MEMORY_STORE``・:func:`set_arm`)。既定 ``mem``=今の表だけ
(器を作らない=final・テープ不変)。``events`` で ``--memory on`` のランに器を作り、今の表に書く所で同じ出来事を器にも
書き、想起を器から引く(候補は今の表の想起と同じ=同値の試験)。テープに列 ``recalled_event_ids`` を 1 つ足す(版 4 の
中)。器は結果を変えないので設定の指紋には入れない(出来事の記録の切替口と同じ扱い)。腕の名は manifest
``memory_summary.memory_store.arm`` に出る。

先例(形だけ借りた): AI Town ``convex/aiTown/agentDescription.ts`` ほかの ``memoryFields``(MIT・共有の会話を
``conversationId`` で指し、本人視点の要約・重要度・最後に引いた時刻を持つ)。R-113 の 1-6 の節。コードは写していない。

**未リサーチ(expedient)**: 言葉の段の境目(A ≥ τ を「はっきり」=想起の閾値と同じ)・中身の粗さの段(M0 は「そのまま」
だけ)・仮の出来事の表の形・テープの列の値の形(``"t_ns:seq"`` の文字列)。

逐次ループ宣言(P4): ``remember`` は配列演算(1 回の呼びで 1 体 1 件・追い出した行の注釈を落とすのは追い出しの件数ぶん)。
``recall`` は 1 体の ``n_rows`` 行の配列演算と、ほかの表の候補がある(7c)ときの k 件で止まる走査(≤ n_rows+店の行)。
``mark_shown`` は見せた行の数ぶん(≤ 3)。``rebuild`` は注釈の件数ぶん(再開のときに 1 回)。``summary`` は配列演算。
"""

from __future__ import annotations

import fnmatch
import functools
import os
from collections import Counter, OrderedDict
from datetime import datetime
from types import MappingProxyType
from typing import Any, Callable, Final, Mapping, NamedTuple, Sequence

import numpy as np

from shibuya.core.time_consts import NS_PER_SECOND, NS_PER_STEP
from shibuya.engine.events.log import EventId
from shibuya.engine.familiarity import place_thing
from shibuya.engine.memory import (
    EVENT_KINDS,
    GIST_PER_AGENT,
    IMPORTANCE,
    IMPORTANCE_MAX,
    KIND_NAMES,
    MEMORY_D,
    MEMORY_W_I,
    MEMORY_W_R,
    RECALL_TAU,
    STORE_ITEM_KIND,
    RecallItem,
    activation_rows,
)
from shibuya.engine.systems import guard as _G

__all__ = [
    "ARM_MEM",
    "ARM_EVENTS",
    "ARMS",
    "arm",
    "set_arm",
    "ORIGIN_LEGACY",
    "ORIGINS",
    "CLARITY_WORDS",
    "GRAIN_WORDS",
    "TAPE_COLUMN",
    "ROW_BYTES",
    "LEGACY_BYTES",
    "ROW_PATH",
    "SHOWN_PATH",
    "Cue",
    "LegacyEvent",
    "MemoryView",
    "ShopPool",
    "RecallReport",
    "MemoryStore",
    "clarity_of",
    "event_id_text",
    "to_item",
    "render_memories",
]

# ================================================================ 腕(切替口)
#: 既定=今の記憶の表(``mem_*``)だけ。
ARM_MEM: Final[str] = "mem"
#: 記憶の器(出来事の記録への目印)を作って想起を器から引く腕。
ARM_EVENTS: Final[str] = "events"
ARMS: Final[tuple[str, ...]] = (ARM_MEM, ARM_EVENTS)
_ARM: str = os.environ.get("SHIBUYA_MEMORY_STORE", ARM_MEM).strip().lower() or ARM_MEM
if _ARM not in ARMS:
    raise ValueError(f"SHIBUYA_MEMORY_STORE は {ARMS} のどれか(いま {_ARM!r})")


def arm() -> str:
    """いまの腕(``mem``=既定・``events``=記憶の器)。組み立てのときに読む。"""
    return _ARM


def set_arm(name: str) -> None:
    """腕を選ぶ(CLI ``--memory-store``・試験の切替口)。組み立ての時に読む(ランの途中で変えても、そのランは変わらない)。"""
    global _ARM
    if str(name) not in ARMS:
        raise ValueError(f"--memory-store は {ARMS} のどれか(いま {name!r})")
    _ARM = str(name)


# ================================================================ 閉じた表
#: 出どころの欄の値(閉じた表・列には番号)。``None``=出来事の記録にある出来事。``"legacy"``=記録に無い出来事の仮の行。
ORIGIN_LEGACY: Final[str] = "legacy"
ORIGINS: Final[tuple[str | None, ...]] = (None, ORIGIN_LEGACY)
_ORIGIN_NAMES: Final[tuple[str, ...]] = ("log", ORIGIN_LEGACY)  # manifest の鍵(None は "log")
_EMPTY_ORIGIN: Final[int] = -1
_LEGACY_CODE: Final[int] = 1
#: 言葉(強さの段・MR-0)。M0 の境目は想起の閾値 τ(A ≥ τ=はっきり)=expedient。M0 の想起は A ≥ τ の行だけを返す。
CLARITY_WORDS: Final[tuple[str, ...]] = ("はっきり", "うろ覚え")
#: 中身の粗さ(MR-0)。M0 は「そのまま」だけ(粗くする段と描き方は M1 以降)。
GRAIN_WORDS: Final[tuple[str, ...]] = ("そのまま",)
#: テープの列(録画 MR16・腕 on のランだけ calls.parquet の末尾に足す=版 4 の中)。``recalled_rows`` と同じ並びで、
#: 見せた記憶の行の目印 ``"t_ns:seq"``(器の外の行=店の評価の行は空文字)。
TAPE_COLUMN: Final[str] = "recalled_event_ids"

#: 記憶の行の列(属性の名・型・空の値)。``ROW_BYTES`` はこの和。
_ROW_COLS: Final[tuple[tuple[str, Any, int], ...]] = (
    ("_ms_ev_t_ns", np.int64, -1),      # 目印の時刻
    ("_ms_ev_seq", np.int32, 0),        # 目印の seq(負=仮の出来事の番地 −1−k)
    ("_ms_n", np.uint16, 0),            # 強さ: 回数
    ("_ms_imp", np.uint8, 0),           # 強さ: 重要度
    ("_ms_first_ns", np.int64, 0),      # 強さ: 最初に書かれた時刻
    ("_ms_origin", np.int8, _EMPTY_ORIGIN),  # 出どころ(−1=空の行)
    ("_ms_shown_ns", np.int64, -1),     # 録画: 最後に見せた時刻
)
#: 仮の出来事の表(行と同じ番地)。今の表 ``mem_*`` と同じ型。
_LEGACY_COLS: Final[tuple[tuple[str, Any, int], ...]] = (
    ("_lg_kind", np.uint8, 0),
    ("_lg_partner", np.int32, 0),
    ("_lg_object", np.int32, 0),
    ("_lg_result", np.uint8, 0),
    ("_lg_cell", np.int32, 0),
)
ROW_BYTES: Final[int] = int(sum(np.dtype(t).itemsize for _n, t, _f in _ROW_COLS))
LEGACY_BYTES: Final[int] = int(sum(np.dtype(t).itemsize for _n, t, _f in _LEGACY_COLS))
_COL_NAMES: Final[tuple[str, ...]] = tuple(n for n, _t, _f in _ROW_COLS + _LEGACY_COLS)
#: 行 M0R(録画)の列。作り直し(``rebuild``)は触らない。
_SHOWN_COLS: Final[frozenset[str]] = frozenset({"_ms_shown_ns"})

#: 状態台帳の道筋の代表(系の宣言 ``writes.paths`` がこれに当たれば書いてよい=段 C と同じ実行時の検査)。
ROW_PATH: Final[str] = "M0:mem_layer.memory_store._ms_n"
SHOWN_PATH: Final[str] = "M0R:mem_layer.memory_store._ms_shown_ns"

#: 今の表の「店の行と重なる」種類(購入・食事・並ぶ・看板)=7c の重なりの鍵(``engine.memory._SHOP_OBJ_KINDS`` と同じ)。
_SHOP_KINDS: Final[tuple[int, ...]] = (
    EVENT_KINDS["buy"], EVENT_KINDS["eat"], EVENT_KINDS["queue"], EVENT_KINDS["signage"],
)


_COL_SPEC: Final[Mapping[str, tuple[Any, int]]] = MappingProxyType(
    {n: (t, f) for n, t, f in _ROW_COLS + _LEGACY_COLS})


def _column(name: str, size: int) -> np.ndarray:
    t, f = _COL_SPEC[name]
    return np.full(int(size), f, dtype=t)


@functools.lru_cache(maxsize=256)
def _permit_has(permit: frozenset[str], path: str) -> bool:
    return path in permit or any(fnmatch.fnmatchcase(path, x) for x in permit if "*" in x)


def _check_permit(path: str, what: str) -> None:
    p = _G.PATHS_PERMIT
    if p is not None and not _permit_has(p, path):
        raise PermissionError(f"系 {_G.CURRENT} は記憶の器の{what}({path.split(':')[0]}:mem_layer.memory_store.*)を"
                              "書く宣言を持たない(1-6・writes.paths)")


# ================================================================ 型
class Cue(NamedTuple):
    """想起の手がかり(System 1 が体の状態から作る=今の 6b の q・ID の一致)。負/0 は「無し」。"""

    cell: int = -1
    partner: int = -1
    obj: int = -1
    kind: int = 0
    result: int = -1


class LegacyEvent(NamedTuple):
    """出来事の記録に無い出来事(仮の行の中身)。配列か整数。``t_ns`` はその回の時刻。"""

    t_ns: Any
    kind: Any
    partner: Any
    obj: Any
    result: Any
    cell: Any


class MemoryView(NamedTuple):
    """LLM に見せる形(MR-0): 言葉(``clarity``)と中身の粗さ(``grain``)と中身の ID。**強さの数は持たない**。

    ``row``・``event_id``・``origin``・``first_ns`` は録画の同定(描き方は使わない)。``when_ns`` は描き方の時刻(最後の回)。
    7c の店の評価の行(器の外=今の ``sm_*``)は ``kind=STORE_ITEM_KIND``・``row=n_rows+店の行``・``event_id=None``。
    """

    row: int
    event_id: EventId | None
    origin: str | None
    clarity: str
    grain: str
    kind: int
    partner: int
    obj: int
    result: int
    cell: int
    annotation: str
    when_ns: int
    first_ns: int
    valence: int = 0
    source: int = 0


class ShopPool(NamedTuple):
    """ほかの表の候補(M0 は 7c の店の評価の行=今の ``sm_*``)。器の行と同じ score の順で競わせる。"""

    score: np.ndarray
    live: np.ndarray
    match: np.ndarray
    key: np.ndarray
    view: Callable[[int], MemoryView]


class RecallReport(NamedTuple):
    """1 回の想起の計数(``MemoryLayer`` が manifest の ``memory_summary.recall.counts`` に足す)。"""

    empty: bool
    rows_used: int
    rows_used_below_tau: int
    rows_candidate: int
    rows_candidate_below_tau: int
    filled: int
    dedup_skipped: int
    picked: int


def clarity_of(a: float, tau: float) -> str:
    """強さ A → 言葉(MR-0)。A ≥ τ=はっきり・それ以外=うろ覚え(境目は expedient)。"""
    return CLARITY_WORDS[0] if float(a) >= float(tau) else CLARITY_WORDS[1]


def event_id_text(eid: EventId | None) -> str:
    """目印 → テープの列の文字列 ``"t_ns:seq"``(無ければ空文字)。"""
    return "" if eid is None else f"{int(eid[0])}:{int(eid[1])}"


def to_item(v: MemoryView, ns_per_step: int) -> RecallItem:
    """``MemoryView`` → 今の描き方が読む ``RecallItem``(刻みの番号に戻す=今の表と同じ値)。"""
    return RecallItem(
        row=int(v.row), last_tick=int(v.when_ns) // int(ns_per_step), kind=int(v.kind), partner=int(v.partner),
        obj=int(v.obj), result=int(v.result), cell=int(v.cell), gist=str(v.annotation), valence=int(v.valence),
        source=int(v.source), first_tick=int(v.first_ns) // int(ns_per_step),
    )


# ================================================================ 器
class MemoryStore:
    """記憶の器 M0(体ごとの行の範囲・SoA の列)。書く口は :meth:`remember` と :meth:`mark_shown`。

    Args:
        n_agents: 体の数。
        n_rows: 体あたりの行数(今の表 ``memory_n`` と同じ=M0 は容量も今のまま。容量の廃止は M1)。
        step_seconds: 1 刻みの秒(目印の時刻 ``t_ns`` と刻みの番号の換算=今の式の単位)。
        minutes_per_step: 今の式の L の単位(``MemoryLayer.minutes_per_tick`` と同じ値を渡す)。
        d・w_r・w_i・tau: 今の式の定数(``engine.memory``)。
    """

    __slots__ = _COL_NAMES + (
        "n", "n_rows", "ns_per_step", "minutes_per_step", "d", "w_r", "w_i", "tau", "tape_on",
        "_ms_note", "_ms_note_order", "_ms_tape", "_ms_stats", "_ms_last",
    )

    def __init__(self, n_agents: int, n_rows: int, *, step_seconds: int, minutes_per_step: float,
                 d: float = MEMORY_D, w_r: float = MEMORY_W_R, w_i: float = MEMORY_W_I,
                 tau: float = RECALL_TAU) -> None:
        if int(n_agents) < 0 or int(n_rows) < 1 or int(step_seconds) < 1:
            raise ValueError("n_agents ≥ 0・n_rows ≥ 1・step_seconds ≥ 1")
        self.n = int(n_agents)
        self.n_rows = int(n_rows)
        self.ns_per_step = int(step_seconds) * NS_PER_SECOND
        self.minutes_per_step = float(minutes_per_step)
        self.d = float(d)
        self.w_r = float(w_r)
        self.w_i = float(w_i)
        self.tau = float(tau)
        #: テープに列を足すランか(組み立てが :meth:`attach_tape` で立てる)。立っていなければ録画の控えを持たない。
        self.tape_on = False
        size = self.n * self.n_rows
        # 記憶の行の列(_ROW_COLS)と仮の出来事の表(_LEGACY_COLS)。型と空の値は表から
        self._ms_ev_t_ns = _column("_ms_ev_t_ns", size)
        self._ms_ev_seq = _column("_ms_ev_seq", size)
        self._ms_n = _column("_ms_n", size)
        self._ms_imp = _column("_ms_imp", size)
        self._ms_first_ns = _column("_ms_first_ns", size)
        self._ms_origin = _column("_ms_origin", size)
        self._ms_shown_ns = _column("_ms_shown_ns", size)
        self._lg_kind = _column("_lg_kind", size)
        self._lg_partner = _column("_lg_partner", size)
        self._lg_object = _column("_lg_object", size)
        self._lg_result = _column("_lg_result", size)
        self._lg_cell = _column("_lg_cell", size)
        #: 注釈(番地 → 文字列)と体ごとの順(古い順に落とす=今の ``MemoryLayer._gist_order`` と同じ)。
        self._ms_note: dict[int, str] = {}
        self._ms_note_order: dict[int, "OrderedDict[int, None]"] = {}
        #: 録画の控え(呼び出しの鍵 (体, t_ns, 起床の級) → 見せた行の目印の組の列)。テープの列へ渡すと消す。
        self._ms_tape: dict[tuple[int, int, int], list[tuple[str, ...]]] = {}
        #: 計数(manifest ``memory_summary.memory_store.counts``)。
        self._ms_stats: Counter = Counter()
        #: 最後の想起の計数(``MemoryLayer`` が読む)。
        self._ms_last: RecallReport = RecallReport(True, 0, 0, 0, 0, 0, 0, 0)

    def __setattr__(self, name: str, value: Any) -> None:
        # 欄は最初の 1 回(組み立て)だけ置ける。付け替えは口の中で object.__setattr__ を使う(テープの印・最後の想起の計数)
        if not hasattr(self, name):
            object.__setattr__(self, name, value)
            return
        raise AttributeError(f"記憶の器の欄 {name} は付け替えられない(書く口は remember・mark_shown)")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"記憶の器の欄 {name} は消せない(消してから付け替える抜け道を閉じる)")

    # ------------------------------------------------------------------ 範囲と読み口
    def rows_of(self, agent: int) -> range:
        """体 ``agent`` の行の範囲(番地)。"""
        i = int(agent)
        if not 0 <= i < self.n:
            raise IndexError(agent)
        return range(i * self.n_rows, (i + 1) * self.n_rows)

    def has_rows(self, agent: int) -> bool:
        """体に記憶の行が 1 つでもあるか。"""
        r = self.rows_of(agent)
        return bool((self._ms_origin[r.start:r.stop] >= 0).any())

    def event_id(self, agent: int, row: int) -> EventId | None:
        """体の行 ``row`` の目印(空の行は ``None``)。"""
        g = self.rows_of(agent).start + int(row)
        if not 0 <= int(row) < self.n_rows or self._ms_origin[g] < 0:
            return None
        return (int(self._ms_ev_t_ns[g]), int(self._ms_ev_seq[g]))

    def origin(self, agent: int, row: int) -> str | None:
        g = self.rows_of(agent).start + int(row)
        o = int(self._ms_origin[g])
        if o < 0:
            raise KeyError((agent, row))
        return ORIGINS[o]

    def shown_ns(self, agent: int, row: int) -> int:
        """録画: 体の行を最後に見せた時刻(−1=まだ)。"""
        return int(self._ms_shown_ns[self.rows_of(agent).start + int(row)])

    def annotation(self, agent: int, row: int) -> str | None:
        return self._ms_note.get(self.rows_of(agent).start + int(row))

    @property
    def last_recall(self) -> RecallReport:
        return self._ms_last

    @property
    def store_counts(self) -> dict[str, int]:
        """計数の写し(manifest ``memory_summary.memory_store.counts``)。"""
        return {k: int(v) for k, v in sorted(self._ms_stats.items())}

    def attach_tape(self) -> None:
        """テープに列 ``recalled_event_ids`` を足すランで、録画の控えを持つようにする(組み立てが 1 回だけ呼ぶ)。"""
        object.__setattr__(self, "tape_on", True)

    # ------------------------------------------------------------------ System 1 の数(M0=今の式)
    def _activation(self, g0: int, g1: int, now_step: int) -> np.ndarray:
        return activation_rows(self._ms_n[g0:g1], self._ms_first_ns[g0:g1] // self.ns_per_step, int(now_step),
                               self.minutes_per_step, self.d)

    def _evict_scores(self, a: np.ndarray, now_step: int) -> np.ndarray:
        """体の配列 → ``(体, n_rows)`` の score(今の ``MemoryLayer.scores`` と同じ: float32 に丸めて float64 へ)。"""
        N = self.n_rows
        n = self._ms_n.reshape(self.n, N)[a]
        first = self._ms_first_ns.reshape(self.n, N)[a] // self.ns_per_step
        A = activation_rows(n, first, int(now_step), self.minutes_per_step, self.d)
        s = self.w_r * A + self.w_i * self._ms_imp.reshape(self.n, N)[a].astype(np.float64)
        s[self._ms_origin.reshape(self.n, N)[a] < 0] = -np.inf
        return s.astype(np.float32).astype(np.float64)

    # ------------------------------------------------------------------ 書く口 1: 覚える
    def remember(self, agent: Any, event_id: Any, strength: Any, origin: str | None, *,
                 annotation: Sequence[str | None] | None = None) -> np.ndarray:
        """出来事を覚える → 書いた行(体の範囲の中の番号・入力の並び)。

        Args:
            agent: 体(整数か 1 次元の配列)。**1 回の呼びで 1 体 1 件**(今の表の書き手と同じ回の分け方)。
            event_id: 目印。``origin="legacy"`` のときは :class:`LegacyEvent`(記録に無い出来事の中身)=器が行と同じ
                番地に仮の出来事を書き、目印 ``(t_ns, −1 − 番地)`` を付ける。
            strength: System 1 の重みの素(M0=重要度の固定表の base: 失敗 3・会話 2・成功/気づき/看板 1)。新しい行は
                初回 +1・上限 4、重ねた行は base(今の表の規則 M3 (b)・Q56)。回数は重ねるごとに +1。
            origin: ``"legacy"``(M0 で書けるのはこれだけ)か ``None``(記録の出来事=体の出来事を記録に載せる段で使う)。
            annotation: 一人ずつの注釈(会話の要旨・入力の並び・``None`` は付けない=既存の注釈は残す)。
        """
        _check_permit(ROW_PATH, "行")
        _check_permit(SHOWN_PATH, "計数と新しい行の録画の印")
        if origin != ORIGIN_LEGACY:
            raise ValueError("M0 で器に書けるのは出どころ legacy(出来事の記録に無い体の出来事)だけ。記録の出来事への"
                             "目印(出どころ None)は、体の出来事を記録に載せる段(親が台帳で決める・候補 1-8)で中身の写像と一緒に足す")
        if not isinstance(event_id, LegacyEvent):
            raise TypeError("出どころ legacy の目印は LegacyEvent(仮の出来事の中身)")
        a = np.atleast_1d(np.asarray(agent, dtype=np.int64))
        m = a.size
        if m == 0:
            return np.zeros(0, dtype=np.int64)
        if np.unique(a).size != m:
            raise ValueError("remember は 1 回の呼びで 1 体 1 件(同じ体の出来事は回を分ける)")
        if (a < 0).any() or (a >= self.n).any():
            raise IndexError("体の番号が範囲の外")
        ev = LegacyEvent(*(np.broadcast_to(np.asarray(x, dtype=np.int64), (m,)) for x in event_id))
        if (ev.t_ns < 0).any():
            raise ValueError("出来事の時刻 t_ns は 0 以上")
        base = np.broadcast_to(np.asarray(strength, dtype=np.int64), (m,))
        ann = None if annotation is None else list(annotation)
        if ann is not None and len(ann) != m:
            raise ValueError("annotation は出来事と同じ数")
        N = self.n_rows
        now_step = int(ev.t_ns[0]) // self.ns_per_step
        if (ev.t_ns // self.ns_per_step != now_step).any():
            raise ValueError("1 回の呼びの出来事は同じ刻み")
        used = self._ms_origin.reshape(self.n, N)[a] >= 0
        rk = self._lg_kind.reshape(self.n, N)[a].astype(np.int64)
        hit = (used & (rk == ev.kind[:, None])
               & (self._lg_partner.reshape(self.n, N)[a].astype(np.int64) == ev.partner[:, None])
               & (self._lg_object.reshape(self.n, N)[a].astype(np.int64) == ev.obj[:, None])
               & (self._lg_result.reshape(self.n, N)[a].astype(np.int64) == ev.result[:, None]))
        found = hit.any(axis=1)
        slot = np.where(found, np.argmax(hit, axis=1), -1)
        empty = ~used
        new = ~found
        has_empty = empty.any(axis=1)
        slot = np.where(new & has_empty, np.argmax(empty, axis=1), slot)
        evict = new & ~has_empty
        if bool(evict.any()):
            slot[evict] = np.argmin(self._evict_scores(a[evict], now_step), axis=1)  # 同点は行番号の小さい方
            self._ms_stats["evictions"] += int(np.count_nonzero(evict))
            for x, y in zip(a[evict].tolist(), slot[evict].tolist()):  # 追い出した行の注釈を落とす(件数ぶん)
                self._drop_note(int(x), int(y))
        g = a * N + slot
        old_n = self._ms_n[g].astype(np.int64)
        n_new = np.where(found, np.minimum(old_n + 1, 65_535), 1)
        first = np.where(found, self._ms_first_ns[g], ev.t_ns)
        imp = np.where(found, np.minimum(base, IMPORTANCE_MAX),
                       np.minimum(base + IMPORTANCE["first_bonus"], IMPORTANCE_MAX))
        # 仮の出来事(行と同じ番地)と目印(最後の回)
        self._lg_kind[g] = ev.kind.astype(np.uint8)
        self._lg_partner[g] = ev.partner.astype(np.int32)
        self._lg_object[g] = ev.obj.astype(np.int32)
        self._lg_result[g] = ev.result.astype(np.uint8)
        self._lg_cell[g] = ev.cell.astype(np.int32)
        self._ms_ev_t_ns[g] = ev.t_ns
        self._ms_ev_seq[g] = (-1 - g).astype(np.int32)
        self._ms_n[g] = n_new.astype(np.uint16)
        self._ms_imp[g] = imp.astype(np.uint8)
        self._ms_first_ns[g] = first
        self._ms_origin[g] = _LEGACY_CODE
        self._ms_shown_ns[g[new]] = -1  # 新しい記憶(空の行・追い出した行)はまだ見せていない
        self._ms_stats["remember"] += int(m)
        self._ms_stats["merged"] += int(np.count_nonzero(found))
        self._ms_stats["new_rows"] += int(np.count_nonzero(new))
        self._ms_stats["legacy_events"] += int(m)
        if ann is not None:
            for x, y, t in zip(a.tolist(), slot.tolist(), ann):  # 注釈のある出来事の数ぶん(会話の要旨=1 件)
                if t is not None:
                    self._put_note(int(x), int(y), str(t))
        return slot.astype(np.int64)

    # ------------------------------------------------------------------ 注釈(今の要旨と同じ規則)
    def _drop_note(self, agent: int, row: int) -> None:
        if self._ms_note.pop(agent * self.n_rows + row, None) is not None:
            self._ms_note_order.get(agent, OrderedDict()).pop(row, None)

    def _put_note(self, agent: int, row: int, text: str) -> None:
        od = self._ms_note_order.setdefault(agent, OrderedDict())
        od.pop(row, None)
        od[row] = None
        self._ms_note[agent * self.n_rows + row] = text
        while len(od) > GIST_PER_AGENT:  # 体あたり 16 件まで(古い順に落とす)
            old, _ = od.popitem(last=False)
            self._ms_note.pop(agent * self.n_rows + old, None)
            self._ms_stats["notes_dropped"] += 1

    # ------------------------------------------------------------------ 書く口 2: 録画
    def mark_shown(self, agent: int, rows: Sequence[int], t_ns: int, *,
                   call: tuple[int, int, int] | None = None) -> tuple[str, ...]:
        """LLM に見せた行の録画(MR16)。``rows`` は描き方が載せた行(``n_rows`` 以上=器の外の行は印を付けない)。

        返り値は ``rows`` と同じ並びの目印の文字列(器の外・空の行は空文字)。``call``(呼び出しの鍵)を渡し、テープに
        列を足すランなら、テープの列へ渡すまで控える(:meth:`take_shown`)。
        """
        _check_permit(SHOWN_PATH, "録画")
        i = int(agent)
        g0 = self.rows_of(i).start
        out: list[str] = []
        for r in rows:  # 見せた行の数ぶん(≤ 3)
            r = int(r)
            g = g0 + r
            if 0 <= r < self.n_rows and self._ms_origin[g] >= 0:
                self._ms_shown_ns[g] = int(t_ns)
                out.append(f"{int(self._ms_ev_t_ns[g])}:{int(self._ms_ev_seq[g])}")
                self._ms_stats["shown_rows"] += 1
            else:
                out.append("")
        ids = tuple(out)
        self._ms_stats["shown_calls"] += 1
        if call is not None and self.tape_on:
            self._ms_tape.setdefault((int(call[0]), int(call[1]), int(call[2])), []).append(ids)
        return ids

    def take_shown(self, call: tuple[int, int, int]) -> tuple[str, ...]:
        """テープの列の値を取り出す(呼び出しの鍵ごとに古い順・無ければ空)。テープの書き手が 1 行ごとに 1 回呼ぶ。"""
        _check_permit(SHOWN_PATH, "録画の控え")
        key = (int(call[0]), int(call[1]), int(call[2]))
        q = self._ms_tape.get(key)
        if not q:
            self._ms_stats["tape_rows_without_shown"] += 1
            return ()
        ids = q.pop(0)
        if not q:
            del self._ms_tape[key]
        self._ms_stats["tape_rows"] += 1
        return ids

    # ------------------------------------------------------------------ 読み口: 想起
    def recall(self, agent: int, t_ns: int, k: int, *, cue: Cue | None = None, pool: ShopPool | None = None,
               tau: float | None = None) -> tuple[MemoryView, ...]:
        """1 体の想起 → ``MemoryView`` の組(score の降順・k 件まで)。M0=今の 6b・7c の規則(同値の試験で確かめる)。

        手がかり ``cue`` に一致する行(相手 ∨ 対象 ∨ セル ∨ 直前の結果と同じ種類・結果)のうち ``A ≥ τ`` を score の
        降順に k 件、足りなければ ``A ≥ τ`` の残りから score の順に補う。``pool``(ほかの表の候補=7c の店の行)がある
        ときは同じ score の順に並べ、同じ店の行は先に選んだ方だけ(今の 7c)。計数は :attr:`last_recall`。
        """
        _check_permit(SHOWN_PATH, "想起の計数")
        i = int(agent)
        kk = int(k)
        th = self.tau if tau is None else float(tau)
        r = self.rows_of(i)
        g0, g1 = r.start, r.stop
        used = self._ms_origin[g0:g1] >= 0
        n_pool = 0 if pool is None else int(np.asarray(pool.score).size)
        if not bool(used.any()) and n_pool == 0:
            object.__setattr__(self, "_ms_last", RecallReport(True, 0, 0, 0, 0, 0, 0, 0))
            return ()
        A = self._activation(g0, g1, int(t_ns) // self.ns_per_step)
        score = self.w_r * A + self.w_i * self._ms_imp[g0:g1]
        kind = self._lg_kind[g0:g1]
        part = self._lg_partner[g0:g1]
        obj = self._lg_object[g0:g1]
        res = self._lg_result[g0:g1]
        cel = self._lg_cell[g0:g1]
        c = Cue() if cue is None else cue
        match = np.zeros(self.n_rows, dtype=bool)
        if int(c.partner) >= 0:
            match |= part == int(c.partner)
        if int(c.obj) >= 0:
            match |= obj == int(c.obj)
        if int(c.cell) >= 0:
            match |= (cel == int(c.cell)) | (obj == int(place_thing(int(c.cell))))
        if int(c.kind) > 0 and 0 <= int(c.result) <= 255:
            match |= (kind == int(c.kind)) & (res == int(c.result))
        match &= used
        live = used & (A >= th)
        counts = (int(np.count_nonzero(used)), int(np.count_nonzero(used & ~live)),
                  int(np.count_nonzero(match)), int(np.count_nonzero(match & ~live)))
        filled = 0
        dedup = 0
        picked: list[tuple[int, int]] = []  # (0=器の行 / 1=ほかの表, 番号)
        if pool is None:
            cand = np.flatnonzero(match & live)
            cand = cand[np.lexsort((cand, -score[cand]))][:kk]
            picked = [(0, int(j)) for j in cand.tolist()]
            if len(picked) < kk:
                rest = np.flatnonzero(live & ~match)
                rest = rest[np.lexsort((rest, -score[rest]))][: kk - len(picked)]
                filled = int(rest.size)
                picked += [(0, int(j)) for j in rest.tolist()]
        else:
            kd = kind.astype(np.int64)
            shop_like = np.isin(kd, _SHOP_KINDS)
            ob = obj.astype(np.int64)
            ep_key = np.where(shop_like & (ob >= 0), ob, -1)
            p_score = np.asarray(pool.score, dtype=np.float64)
            p_live = np.asarray(pool.live, dtype=bool)
            p_match = np.asarray(pool.match, dtype=bool)
            p_key = np.asarray(pool.key, dtype=np.int64)

            def order(ep_mask: np.ndarray, st_mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
                e = np.flatnonzero(ep_mask)
                s = np.flatnonzero(st_mask)
                sc_ = np.concatenate([score[e], p_score[s]])
                ty = np.concatenate([np.zeros(e.size, dtype=np.int64), np.ones(s.size, dtype=np.int64)])
                ix = np.concatenate([e, s]).astype(np.int64)
                o = np.lexsort((ix, ty, -sc_))
                return ty[o], ix[o]

            keys: set[int] = set()
            for (tys, ixs), is_fill in ((order(match & live, p_match & p_live), False),
                                        (order(live & ~match, p_live & ~p_match), True)):
                for typ, j in zip(tys.tolist(), ixs.tolist()):  # 逐次: k 件で止まる(同じ店の重なりは飛ばす)
                    if len(picked) >= kk:
                        break
                    key = int(ep_key[j]) if typ == 0 else int(p_key[j])
                    if key >= 0 and key in keys:
                        dedup += 1
                        continue
                    picked.append((typ, j))
                    if key >= 0:
                        keys.add(key)
                    if is_fill:
                        filled += 1
        views: list[MemoryView] = []
        for typ, j in picked:  # 高々 k(≤ 3)
            if typ == 1:
                views.append(pool.view(j))  # type: ignore[union-attr]
                continue
            g = g0 + j
            views.append(MemoryView(
                row=int(j), event_id=(int(self._ms_ev_t_ns[g]), int(self._ms_ev_seq[g])),
                origin=ORIGINS[int(self._ms_origin[g])], clarity=clarity_of(float(A[j]), th), grain=GRAIN_WORDS[0],
                kind=int(kind[j]), partner=int(part[j]), obj=int(obj[j]), result=int(res[j]), cell=int(cel[j]),
                annotation=self._ms_note.get(g, ""), when_ns=int(self._ms_ev_t_ns[g]),
                first_ns=int(self._ms_first_ns[g]),
            ))
        object.__setattr__(self, "_ms_last", RecallReport(False, *counts, filled, dedup, len(picked)))
        self._ms_stats["recall_calls"] += 1
        return tuple(views)

    # ------------------------------------------------------------------ 再開: 記憶の表から作り直す
    def rebuild(self, kind: np.ndarray, first_step: np.ndarray, last_step: np.ndarray, cell: np.ndarray,
                partner: np.ndarray, obj: np.ndarray, result: np.ndarray, importance: np.ndarray, n: np.ndarray,
                notes: dict[tuple[int, int], str], note_order: dict[int, "OrderedDict[int, None]"]) -> int:
        """今の記憶の表(``(体, n_rows)`` の配列)と要旨から器を作り直す(再開のとき・状態台帳の行 M0=作り直せる)。

        M0 の器の行は全部が記憶の表の写し(出どころ legacy)なので、行・仮の出来事・強さ・注釈は同じ値に戻る。目印の
        seq は番地から決まるので通しのランと同じ。書くのは行 M0 の欄だけ(録画・控え・計数=行 M0R は触らない=再開の器は
        空から始まる)。系の中(ランの途中)では呼べない。→ 行の数。
        """
        if _G.CURRENT is not None:
            raise RuntimeError(f"記憶の器の作り直しは再開の組み立て(系の外)だけ(いまの系 {_G.CURRENT})")
        _check_permit(ROW_PATH, "行の作り直し")
        N = self.n_rows
        shape = (self.n, N)
        kd = np.asarray(kind)
        if kd.shape != shape:
            raise ValueError(f"記憶の表の形 {kd.shape} が器 {shape} と違う")
        used = (kd != 0).reshape(-1)
        g = np.flatnonzero(used)
        for name, _dt, fill in _ROW_COLS + _LEGACY_COLS:
            if name not in _SHOWN_COLS:  # 行 M0 の列だけ(録画の列は行 M0R)
                getattr(self, name)[:] = fill
        self._lg_kind[g] = kd.reshape(-1)[g]
        self._lg_partner[g] = np.asarray(partner).reshape(-1)[g]
        self._lg_object[g] = np.asarray(obj).reshape(-1)[g]
        self._lg_result[g] = np.asarray(result).reshape(-1)[g]
        self._lg_cell[g] = np.asarray(cell).reshape(-1)[g]
        self._ms_ev_t_ns[g] = np.asarray(last_step, dtype=np.int64).reshape(-1)[g] * self.ns_per_step
        self._ms_ev_seq[g] = (-1 - g).astype(np.int32)
        self._ms_n[g] = np.asarray(n).reshape(-1)[g]
        self._ms_imp[g] = np.asarray(importance).reshape(-1)[g]
        self._ms_first_ns[g] = np.asarray(first_step, dtype=np.int64).reshape(-1)[g] * self.ns_per_step
        self._ms_origin[g] = _LEGACY_CODE
        self._ms_note.clear()
        self._ms_note_order.clear()
        for agent, od in note_order.items():  # 注釈の件数ぶん(体あたり ≤ 16)
            new = self._ms_note_order.setdefault(int(agent), OrderedDict())
            for row in od:
                text = notes.get((int(agent), int(row)))
                if text is not None:
                    new[int(row)] = None
                    self._ms_note[int(agent) * N + int(row)] = text
        return int(g.size)

    # ------------------------------------------------------------------ 実行時の検査(器=記憶の表の写し)
    def check_against_table(self, agent: np.ndarray, rows: np.ndarray, *, kind: np.ndarray, partner: np.ndarray,
                            obj: np.ndarray, result: np.ndarray, cell: np.ndarray, first_step: np.ndarray,
                            last_step: np.ndarray, n: np.ndarray, importance: np.ndarray) -> None:
        """書いた行の器の値が記憶の表の値と同じかを配列で比べ、違えば ``RuntimeError``(読むだけ・M0 の宣言の前提)。

        比べるのは仮の出来事(種類・相手・対象・結果・セル)・強さ(回数・重要度・最初の時刻)・目印(最後の時刻と
        seq=−1−番地)・出どころ(legacy)。書きの検査の切替口(``SHIBUYA_WRITE_GUARD``)でも外さない(器の値は
        ハッシュに入らない=ずれても final とハッシュに出ないので、ここで止める)。逐次ループ宣言: なし(配列演算)。
        """
        a = np.asarray(agent, dtype=np.int64)
        g = a * self.n_rows + np.asarray(rows, dtype=np.int64)
        ns = self.ns_per_step
        pairs = (
            ("種類", self._lg_kind[g], kind), ("相手", self._lg_partner[g], partner), ("対象", self._lg_object[g], obj),
            ("結果", self._lg_result[g], result), ("セル", self._lg_cell[g], cell), ("回数", self._ms_n[g], n),
            ("重要度", self._ms_imp[g], importance),
            ("最初の時刻", self._ms_first_ns[g], np.asarray(first_step, dtype=np.int64) * ns),
            ("目印の時刻", self._ms_ev_t_ns[g], np.asarray(last_step, dtype=np.int64) * ns),
            ("目印の seq", self._ms_ev_seq[g], -1 - g), ("出どころ", self._ms_origin[g], np.full(g.size, _LEGACY_CODE)),
        )
        bad = [name for name, got, want in pairs
               if not np.array_equal(np.asarray(got).astype(np.int64), np.asarray(want).astype(np.int64))]
        if bad:
            raise RuntimeError(f"1-6 M0: 記憶の器の値が記憶の表と食い違う({'・'.join(bad)})=器は表の写し")

    # ------------------------------------------------------------------ 計器
    def summary(self) -> dict[str, Any]:
        """manifest ``memory_summary.memory_store``: 腕の名・行数・出どころの分布・録画(計器)。"""
        o = self._ms_origin
        used = o >= 0
        per = used.reshape(self.n, self.n_rows).sum(axis=1) if self.n else np.zeros(0, dtype=np.int64)
        by = np.bincount(o[used].astype(np.int64), minlength=len(ORIGINS))
        return {
            "arm": ARM_EVENTS,
            "n_rows": int(self.n_rows),
            "row_bytes": int(ROW_BYTES),
            "legacy_row_bytes": int(LEGACY_BYTES),
            "rows": int(np.count_nonzero(used)),
            "agents_with_rows": int(np.count_nonzero(per > 0)),
            "origins": {_ORIGIN_NAMES[k]: int(by[k]) for k in range(len(ORIGINS))},
            "annotations": int(len(self._ms_note)),
            "shown_rows_live": int(np.count_nonzero(used & (self._ms_shown_ns >= 0))),
            "tape_pending": int(sum(len(v) for v in self._ms_tape.values())),
            "counts": self.store_counts,
        }


# ================================================================ 描き方(今の B5「記憶」の 1 行と同じバイト)
def render_memories(views: Sequence[MemoryView], *, clock: Callable[[int], datetime], poi_names: Sequence[str],
                    place_ids: Sequence[str], now_ns: int = 0, ns_per_step: int = NS_PER_STEP) -> str:
    """``MemoryView`` の組 → B5「記憶」の 1 行(今の描き方=``perception.renderer`` の項と行の組み立て・テンプレ v1.3)。

    ``clock`` は刻みの番号 → 世界内日時(描画の ``clock_fn`` と同じ口)。項の時刻は ``when_ns``(最後の回)、負なら
    ``now_ns``。チャネル 60 tok で末尾の項から落とす所までが描き方(個体枠 300 との突き合わせは描画の側=B5・B6 の
    本文が要る)。M0 の言葉は全部「はっきり」・粗さは「そのまま」(今のテンプレには言葉の欄が無い)。それ以外は
    ``ValueError``(描き方は M1 以降で決める)。0 件は空文字。
    """
    from shibuya.agents.state import RESULT_TEXT
    from shibuya.perception import normalize as _N
    from shibuya.perception.renderer import compose_memory_line, memory_item_text

    texts: list[str] = []
    for v in views:  # 想起の件数ぶん(≤ 3)
        if v.clarity != CLARITY_WORDS[0] or v.grain != GRAIN_WORDS[0]:
            raise ValueError(f"M0 の描き方は「{CLARITY_WORDS[0]}・{GRAIN_WORDS[0]}」だけ(いま {v.clarity}・{v.grain})")
        when = int(v.when_ns) if int(v.when_ns) >= 0 else int(now_ns)
        h, m = _N.format_time(clock(when // int(ns_per_step)))
        texts.append(memory_item_text(to_item(v, ns_per_step), hhmm=f"{h}:{m}", poi_names=poi_names,
                                      place_ids=place_ids, result_text=RESULT_TEXT))
    return compose_memory_line(texts)[0]
