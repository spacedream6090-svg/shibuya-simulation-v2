"""engine.scheduler — 起床イベントの1分tickバケット配列+tick内秒オフセット順序+繰り延べ待ち行列。

正典
- 実装計画書 §3: 「スケジューラ: 1分tickの**バケット配列**+tick内は秒オフセット(δ_perc)で
  ``np.argsort`` 整列。**heapq は遠未来予約のみ**。``scheduler(state)->ndarray[int64]`` の**純関数**。」
- 運用設計書 §2.5: 同時刻イベント =
  ``(t_sim_ns, class_rank[institution −1・conversation 0・plan_boundary 1・individual 2・cell 3],
  blake3(…), subject_id)`` の昇順。
- 運用設計書 §2.3: δ_perc は世界時刻を進めず tick 内順序としてのみ使う。
- 知覚契約書 §6: 繰り延べは**破棄でなく繰り延べ**。**4クラス固定優先**(会話ターン > 計画境界 >
  個体変化 > セル変化)+クラス内は待ち時間/許容遅延の降順+``T_max`` 超過で1段昇格
  (starvation-free)+同一体の保留起床は合流+なお不足なら下位2クラスを縮退実行。
- 予算宣言表 §7-5: 繰り延べ量・昇格数・縮退実行数・不応期による抑止数を**起床クラス別/シミュ日**で
  必ず記録(診断行4列)。列名は ``manifest.schema.DIAG_COLUMNS`` を**再輸出**して使う
  (engine は manifest を import してよい=実装計画書 §3。二重定義にしない。
  なお列名そのものは manifest 側で「未リサーチ・C4 で確定」と宣言済み)。
- 予算宣言表 P3: イベント処理スループット **≥10万イベント/秒**(``tests/engine`` で機械検査)。

本モジュールの担当と非担当
- 担当: 予約(bucket/heap)・**順序づけの純関数**・取り出し・取り消し・再予約、
  繰り延べ待ち行列の**データ構造と診断カウンタ**。
- 非担当(subD): 繰り延べの**裁定規則**(クラス内順序の具体値・T_max・縮退の中身)、
  二相コミットの reserve→arbitrate→commit、resolve。
  ``DeferralQueue`` は「入れる・数える・出す」だけを提供し、どれを出すかは呼び出し側が決める。

逐次ループ宣言(P4)
1. ``Scheduler.schedule_many``: **バッチ中の相異なる tick 数**ぶんのループ(個体数ではない)。
2. ``Scheduler._advance_to``: 経過 tick 数ぶんのループ(リングのスロット掃除)。
3. ``Scheduler._drain_heap``: 地平内に入った**遠未来予約の件数**ぶんの heapq ループ。
4. ``core.hashing.wake_tiebreak_array``: イベント数ぶんの blake3 ループ(同モジュールで宣言済み・
   実測 約2.0M件/秒)。
個体数に比例する Python ループは持たない(整列・突合はすべて NumPy)。

expedient(本モジュール分)
- 地平 ``HORIZON_TICKS = 1,440``(1 シミュ日)。設計書は「heapq は遠未来予約のみ」としか
  書いておらず H の値を与えていない。1 日ぶんのリング=1,440 スロットは
  「その日のうちに起きる予約は配列・翌日以降は heap」という素直な線引き。
- 整列鍵から ``seq``(予約連番)を**除く**。含めると挿入順が結果に漏れ、T3(並列不変性)・
  「挿入順を並べ替えても出力不変」が壊れるため。完全に同一の (agent, offset, class) が
  重複したときの ``due_events`` の行順は入力順(安定ソート)=**その場合 agent_id 列は不変**。
- 取り消しは ``seq`` の集合で持ち、取り出し時にマスクする(tombstone 方式)。
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass
from typing import Final, Iterable, Mapping, Sequence

import numpy as np

from shibuya.core.hashing import wake_tiebreak_array
from shibuya.core.types import (
    DEFERRAL_CLASSES,
    EventClass,
    NS_PER_SECOND,
    DEFAULT_TICK_SECONDS,
)
from shibuya.manifest.schema import DIAG_COLUMNS

__all__ = [
    "HORIZON_TICKS",
    "COL_AGENT",
    "COL_OFFSET",
    "COL_CLASS",
    "COL_SEQ",
    "N_COLS",
    "DIAG_COLUMNS",
    "TickState",
    "order_indices",
    "scheduler",
    "ordered_events",
    "coalesce_agents",
    "Scheduler",
    "DeferralQueue",
]

#: 遠未来予約を heapq へ回す地平(tick)。expedient(上記)。
HORIZON_TICKS: Final[int] = 1_440

COL_AGENT: Final[int] = 0
COL_OFFSET: Final[int] = 1
COL_CLASS: Final[int] = 2
COL_SEQ: Final[int] = 3
N_COLS: Final[int] = 4

_EMPTY = np.empty((0, N_COLS), dtype=np.int64)


# --------------------------------------------------------------------------------------
# 純関数側(実装計画書 §3「scheduler(state)->ndarray[int64] の純関数」)
# --------------------------------------------------------------------------------------
@dataclass(frozen=True)
class TickState:
    """1 tick 分の起床イベント(純関数 ``scheduler`` の入力)。

    Attributes:
        tick: 対象 tick。
        events: 形 ``(n, 4)`` の int64 配列。列 = (agent_id, offset_ns, class_rank, seq)。
        run_salt: タイブレーク用ハッシュの塩(manifest の run_salt)。
    """

    tick: int
    events: np.ndarray
    run_salt: bytes = b""

    def __post_init__(self) -> None:
        ev = np.asarray(self.events)
        if ev.ndim != 2 or ev.shape[1] != N_COLS:
            raise ValueError(f"events は (n, {N_COLS}) の配列: {ev.shape}")
        if ev.dtype != np.int64:
            raise ValueError(f"events は int64: {ev.dtype}")
        object.__setattr__(self, "events", ev)

    @property
    def n(self) -> int:
        return int(self.events.shape[0])


def order_indices(state: TickState) -> np.ndarray:
    """``state.events`` を規約順に並べる**添字の置換**を返す(純関数)。

    順序 = ``(offset_ns, class_rank, blake3 タイブレーク, agent_id)`` の昇順(運用設計書 §2.5)。
    ``seq`` は鍵に含めない(挿入順を結果に漏らさないため)。
    """
    ev = state.events
    if ev.shape[0] == 0:
        return np.empty(0, dtype=np.int64)
    agent = ev[:, COL_AGENT]
    offset = ev[:, COL_OFFSET]
    cls = ev[:, COL_CLASS]
    tie = wake_tiebreak_array(state.run_salt, int(state.tick), cls, agent)
    # np.lexsort は最後の鍵が第一優先
    return np.lexsort((agent, tie, cls, offset)).astype(np.int64, copy=False)


def scheduler(state: TickState) -> np.ndarray:
    """規約順に並べた **agent_id の配列**(int64)を返す純関数。

    同じ入力(挿入順を並べ替えたものを含む)からは常に同じ出力になる。
    """
    return np.ascontiguousarray(state.events[order_indices(state), COL_AGENT])


def ordered_events(state: TickState) -> np.ndarray:
    """規約順に並べた ``(n, 4)`` イベント配列(純関数)。"""
    return np.ascontiguousarray(state.events[order_indices(state)])


def coalesce_agents(ordered_agent_ids: np.ndarray) -> np.ndarray:
    """順序を保ったまま同一個体の重複を1件に畳む(知覚契約書 §6 運用規定②「1呼に合流」)。

    Args:
        ordered_agent_ids: ``scheduler`` の出力(順序つき)。

    Returns:
        最初の出現だけを残した agent_id 配列(ベクトル化・ループなし)。
    """
    if ordered_agent_ids.size == 0:
        return ordered_agent_ids
    _, first_idx = np.unique(ordered_agent_ids, return_index=True)
    return ordered_agent_ids[np.sort(first_idx)]


# --------------------------------------------------------------------------------------
# 状態を持つ側(バケット配列 + 遠未来 heap)
# --------------------------------------------------------------------------------------
class Scheduler:
    """1分tick のバケット配列(リング)+遠未来 heapq の起床予約器。

    Example:
        >>> s = Scheduler(run_salt=b"run")
        >>> _ = s.schedule(agent_id=7, tick=3, offset_ns=213_000_000)
        >>> s.due(3)
        array([7], dtype=int64)
    """

    def __init__(
        self,
        *,
        run_salt: bytes = b"",
        horizon_ticks: int = HORIZON_TICKS,
        start_tick: int = 0,
        tick_seconds: int = DEFAULT_TICK_SECONDS,
    ) -> None:
        """
        Args:
            run_salt: タイブレークハッシュの塩(manifest 由来)。
            horizon_ticks: バケット配列(リング)の長さ。これを超える先の予約は heapq。
            start_tick: 最初に取り出す tick(これより前の予約は拒否)。
            tick_seconds: 1 tick の秒数(offset_ns の範囲検査に使う)。
        """
        if horizon_ticks <= 0:
            raise ValueError("horizon_ticks は正")
        if tick_seconds <= 0:
            raise ValueError("tick_seconds は正")
        self.run_salt = bytes(run_salt)
        self.horizon_ticks = int(horizon_ticks)
        self.tick_seconds = int(tick_seconds)
        self._tick_ns = self.tick_seconds * NS_PER_SECOND
        self._base_tick = int(start_tick)
        self._ring: list[list[np.ndarray]] = [[] for _ in range(self.horizon_ticks)]
        self._ring_tick: list[int] = [-1] * self.horizon_ticks
        self._heap: list[tuple[int, int, int, int, int]] = []  # (tick, offset, cls, seq, agent)
        self._cancelled: set[int] = set()
        self._next_seq: int = 0
        self._n_pending: int = 0

    # ---- 状態 ----
    @property
    def base_tick(self) -> int:
        """まだ取り出していない最古の tick。"""
        return self._base_tick

    @property
    def pending(self) -> int:
        """未消化の予約件数(取り消し済みを含まない概数=tombstone は取り出し時に除く)。"""
        return self._n_pending

    @property
    def far_future_pending(self) -> int:
        """heapq 側(地平の外)の件数。"""
        return len(self._heap)

    # ---- 予約 ----
    def schedule(
        self,
        agent_id: int,
        tick: int,
        offset_ns: int = 0,
        event_class: EventClass | int = EventClass.PLAN_BOUNDARY,
    ) -> int:
        """1件の起床を予約し、予約 id(``seq``)を返す。"""
        seq = self.schedule_many([agent_id], [tick], [offset_ns], [int(event_class)])
        return int(seq[0])

    def schedule_many(
        self,
        agent_ids: Sequence[int] | np.ndarray,
        ticks: Sequence[int] | np.ndarray,
        offset_ns: Sequence[int] | np.ndarray | int = 0,
        event_classes: Sequence[int] | np.ndarray | int = int(EventClass.PLAN_BOUNDARY),
    ) -> np.ndarray:
        """複数の起床をまとめて予約する(ベクトル化)。

        Args:
            agent_ids: 個体 id 配列。
            ticks: 起床 tick 配列。
            offset_ns: tick 内オフセット[ns](スカラー可)。
            event_classes: class_rank(スカラー可・``EventClass`` の値)。

        Returns:
            予約 id(``seq``)の int64 配列(入力と同じ並び)。

        Raises:
            ValueError: 過去 tick への予約 / offset_ns が tick 長の外 / 長さ不一致。
        """
        aid = np.asarray(agent_ids, dtype=np.int64).ravel()
        tks = np.asarray(ticks, dtype=np.int64).ravel()
        n = aid.size
        if tks.size != n:
            raise ValueError("agent_ids と ticks の長さが違う")
        off = np.broadcast_to(np.asarray(offset_ns, dtype=np.int64), (n,))
        cls = np.broadcast_to(np.asarray(event_classes, dtype=np.int64), (n,))
        if n == 0:
            return np.empty(0, dtype=np.int64)
        if np.any(tks < self._base_tick):
            raise ValueError(f"過去 tick への予約(base_tick={self._base_tick})")
        if np.any(off < 0) or np.any(off >= self._tick_ns):
            raise ValueError(f"offset_ns は 0..{self._tick_ns - 1}")

        seq = np.arange(self._next_seq, self._next_seq + n, dtype=np.int64)
        self._next_seq += n

        rec = np.empty((n, N_COLS), dtype=np.int64)
        rec[:, COL_AGENT] = aid
        rec[:, COL_OFFSET] = off
        rec[:, COL_CLASS] = cls
        rec[:, COL_SEQ] = seq

        near = tks < self._base_tick + self.horizon_ticks
        if np.any(near):
            self._push_ring(tks[near], rec[near])
        far_idx = np.flatnonzero(~near)
        # 逐次ループ宣言2: 地平外の件数ぶん(通常は少数)
        for i in far_idx:
            row = rec[i]
            heapq.heappush(
                self._heap,
                (
                    int(tks[i]),
                    int(row[COL_OFFSET]),
                    int(row[COL_CLASS]),
                    int(row[COL_SEQ]),
                    int(row[COL_AGENT]),
                ),
            )
        self._n_pending += n
        return seq

    def _push_ring(self, ticks: np.ndarray, rec: np.ndarray) -> None:
        order = np.argsort(ticks, kind="stable")
        sticks = ticks[order]
        srec = rec[order]
        uniq, starts = np.unique(sticks, return_index=True)
        ends = np.append(starts[1:], sticks.size)
        # 逐次ループ宣言1: バッチ中の相異なる tick 数ぶん(個体数ではない)
        for u, s, e in zip(uniq.tolist(), starts.tolist(), ends.tolist()):
            slot = u % self.horizon_ticks
            if self._ring_tick[slot] != u:
                if self._ring_tick[slot] != -1 and self._ring[slot]:
                    raise AssertionError(
                        f"リングのスロット衝突(slot={slot}: {self._ring_tick[slot]} vs {u})"
                    )
                self._ring_tick[slot] = u
                self._ring[slot] = []
            self._ring[slot].append(np.ascontiguousarray(srec[s:e]))

    # ---- 取り消し・再予約 ----
    def cancel(self, seq: int) -> bool:
        """予約を取り消す(tombstone)。既に取り出し済み/取り消し済み/未知なら False。

        Note:
            存在確認のためリング(地平ぶんのスロット)と heap を走査する
            = **O(地平スロット数)**。「取り消しは稀」という前提の設計=expedient。
            大量取り消しが必要になったら seq→tick の索引を持つ形へ変える(その場合は
            予約1件ごとの Python ループが増えるため P3 実測で判断する)。
        """
        s = int(seq)
        if s in self._cancelled or self._find(s) is None:
            return False
        self._cancelled.add(s)
        self._n_pending -= 1
        return True

    def reschedule(
        self,
        seq: int,
        new_tick: int,
        new_offset_ns: int | None = None,
        new_event_class: EventClass | int | None = None,
    ) -> int:
        """予約を取り消して新しい時刻へ入れ直し、**新しい seq** を返す。

        Note:
            「取り消し+再予約」で実装する(元の seq は無効化される)。繰り延べ(§6)は
            これを使って「破棄でなく先送り」を表す。
        """
        s = int(seq)
        old = self._find(s)
        if old is None:
            raise KeyError(f"未知または取り出し済みの予約: {seq}")
        agent, off, cls, _ = old
        self.cancel(s)
        return self.schedule(
            agent,
            new_tick,
            off if new_offset_ns is None else int(new_offset_ns),
            cls if new_event_class is None else int(new_event_class),
        )

    def _find(self, seq: int) -> tuple[int, int, int, int] | None:
        """seq → (agent_id, offset_ns, class_rank, tick)。無ければ None(リング+heap を走査)。"""
        s = int(seq)
        if s < 0 or s >= self._next_seq:
            return None
        for slot, tick in enumerate(self._ring_tick):
            if tick < 0:
                continue
            for chunk in self._ring[slot]:
                hit = np.flatnonzero(chunk[:, COL_SEQ] == s)
                if hit.size:
                    row = chunk[hit[0]]
                    return int(row[COL_AGENT]), int(row[COL_OFFSET]), int(row[COL_CLASS]), tick
        for t, off, cls, hs, agent in self._heap:
            if hs == s:
                return agent, off, cls, t
        return None

    # ---- 取り出し ----
    def _advance_to(self, tick: int) -> None:
        if tick < self._base_tick:
            raise ValueError(f"tick={tick} は base_tick={self._base_tick} より過去")
        # 逐次ループ宣言2: 経過 tick 数ぶん(スロット掃除)
        for t in range(self._base_tick, tick):
            slot = t % self.horizon_ticks
            if self._ring_tick[slot] == t:
                self._ring[slot] = []
                self._ring_tick[slot] = -1
        self._base_tick = int(tick)
        self._drain_heap()

    def _drain_heap(self) -> None:
        limit = self._base_tick + self.horizon_ticks
        moved: list[tuple[int, np.ndarray]] = []
        # 逐次ループ宣言3: 地平内に入った遠未来予約の件数ぶん
        while self._heap and self._heap[0][0] < limit:
            t, off, cls, seq, agent = heapq.heappop(self._heap)
            row = np.array([[agent, off, cls, seq]], dtype=np.int64)
            moved.append((t, row))
        if moved:
            ticks = np.array([m[0] for m in moved], dtype=np.int64)
            rec = np.concatenate([m[1] for m in moved], axis=0)
            self._push_ring(ticks, rec)

    def events_at(self, tick: int) -> TickState:
        """指定 tick の未消化イベントを ``TickState`` にまとめる(取り消し済みは除く)。"""
        self._advance_to(tick)
        slot = tick % self.horizon_ticks
        if self._ring_tick[slot] != tick or not self._ring[slot]:
            return TickState(tick=int(tick), events=_EMPTY, run_salt=self.run_salt)
        chunks = self._ring[slot]
        ev = chunks[0] if len(chunks) == 1 else np.concatenate(chunks, axis=0)
        if self._cancelled:
            mask = ~np.isin(ev[:, COL_SEQ], np.fromiter(self._cancelled, dtype=np.int64))
            if not mask.all():
                ev = ev[mask]
        return TickState(tick=int(tick), events=np.ascontiguousarray(ev), run_salt=self.run_salt)

    def due(self, tick: int, coalesce: bool = False) -> np.ndarray:
        """指定 tick に起床する個体 id を**規約順**で返す(int64 配列)。

        Args:
            tick: 対象 tick(``base_tick`` 以上)。
            coalesce: True なら同一個体の重複起床を1件に畳む(§6 運用規定②)。

        Note:
            取り出しても予約は消えない(同じ tick を再度呼べば同じ列が返る=純関数性)。
            消費は ``consume(tick)`` で明示的に行う。
        """
        state = self.events_at(tick)
        ids = scheduler(state)
        return coalesce_agents(ids) if coalesce else ids

    def due_events(self, tick: int) -> np.ndarray:
        """``due`` と同じ順序で ``(n, 4)`` の生イベント配列を返す。"""
        return ordered_events(self.events_at(tick))

    def consume(self, tick: int) -> int:
        """指定 tick のバケットを空にして、消化した件数を返す。"""
        self._advance_to(tick)
        slot = tick % self.horizon_ticks
        n = 0
        if self._ring_tick[slot] == tick:
            cancelled = (
                np.fromiter(self._cancelled, dtype=np.int64, count=len(self._cancelled))
                if self._cancelled
                else None
            )
            for chunk in self._ring[slot]:
                seqs = chunk[:, COL_SEQ]
                if cancelled is None:
                    n += int(seqs.size)
                    continue
                dead = np.isin(cancelled, seqs)
                n += int(seqs.size) - int(np.count_nonzero(dead))
                self._cancelled.difference_update(cancelled[dead].tolist())
            self._ring[slot] = []
            self._ring_tick[slot] = -1
        self._n_pending -= n
        return n


# --------------------------------------------------------------------------------------
# 繰り延べ待ち行列(データ構造と診断カウンタのみ。裁定規則は subD)
# --------------------------------------------------------------------------------------
class DeferralQueue:
    """4クラス固定優先の繰り延べ待ち行列(知覚契約書 §6)。

    保持するもの: クラス別の待ち行列(個体 id・理由コード・繰り延べ tick)と、
    診断行4列 ``(deferred, promoted, degraded, suppressed)`` の**クラス別カウンタ**。

    保持しないもの(= subD が決める): クラス内の並べ替え規則・``T_max``・昇格の発火条件・
    縮退の中身。本クラスは ``promote`` / ``degrade`` / ``suppress`` を**呼ばれたら数える**だけ。
    """

    def __init__(self, classes: Iterable[EventClass] = DEFERRAL_CLASSES) -> None:
        self.classes: tuple[EventClass, ...] = tuple(classes)
        self._index: dict[int, int] = {int(c): i for i, c in enumerate(self.classes)}
        self._agents: list[list[int]] = [[] for _ in self.classes]
        self._reasons: list[list[int]] = [[] for _ in self.classes]
        self._since: list[list[int]] = [[] for _ in self.classes]
        self._reason_codes: dict[str, int] = {}
        self._reason_names: list[str] = []
        self._counters = np.zeros((len(DIAG_COLUMNS), len(self.classes)), dtype=np.int64)

    # ---- 理由の intern ----
    def reason_code(self, reason: str) -> int:
        """理由文字列 → 連番コード(intern)。"""
        code = self._reason_codes.get(reason)
        if code is None:
            code = len(self._reason_names)
            self._reason_codes[reason] = code
            self._reason_names.append(reason)
        return code

    def reason_name(self, code: int) -> str:
        return self._reason_names[int(code)]

    def _slot(self, cls: EventClass | int) -> int:
        try:
            return self._index[int(cls)]
        except KeyError:
            raise ValueError(f"繰り延べ対象外のクラス: {cls!r}(対象={self.classes})") from None

    # ---- 出し入れ ----
    def defer(self, agent_id: int, cls: EventClass | int, reason: str, tick: int = 0) -> None:
        """1件を繰り延べる(=破棄しない。診断 ``deferred`` を1加算)。"""
        i = self._slot(cls)
        self._agents[i].append(int(agent_id))
        self._reasons[i].append(self.reason_code(reason))
        self._since[i].append(int(tick))
        self._counters[DIAG_COLUMNS.index("deferred"), i] += 1

    def defer_many(
        self,
        agent_ids: Sequence[int] | np.ndarray,
        cls: EventClass | int,
        reason: str,
        tick: int = 0,
    ) -> None:
        """複数件をまとめて繰り延べる。"""
        i = self._slot(cls)
        ids = np.asarray(agent_ids, dtype=np.int64).ravel().tolist()
        code = self.reason_code(reason)
        self._agents[i].extend(ids)
        self._reasons[i].extend([code] * len(ids))
        self._since[i].extend([int(tick)] * len(ids))
        self._counters[DIAG_COLUMNS.index("deferred"), i] += len(ids)

    def promote(self, agent_id: int, cls: EventClass | int, to_cls: EventClass | int | None = None) -> None:
        """``T_max`` 超過などで1段(既定)上のクラスへ移す(診断 ``promoted`` を1加算)。

        Args:
            agent_id: 対象個体。
            cls: 現在のクラス。
            to_cls: 移動先。None なら1段上(``self.classes`` の1つ前)。最上位なら移動しない。
        """
        i = self._slot(cls)
        try:
            pos = self._agents[i].index(int(agent_id))
        except ValueError:
            raise KeyError(f"クラス {cls!r} に個体 {agent_id} の保留がない") from None
        reason = self._reasons[i].pop(pos)
        since = self._since[i].pop(pos)
        self._agents[i].pop(pos)
        j = self._slot(to_cls) if to_cls is not None else max(0, i - 1)
        self._agents[j].append(int(agent_id))
        self._reasons[j].append(reason)
        self._since[j].append(since)
        self._counters[DIAG_COLUMNS.index("promoted"), j] += 1

    def pop_class(self, cls: EventClass | int, k: int | None = None) -> np.ndarray:
        """クラスの先頭から ``k`` 件(None なら全件)取り出して agent_id 配列を返す。

        並べ替え規則(待ち時間/許容遅延の降順など)は呼び出し側の責務。
        """
        i = self._slot(cls)
        n = len(self._agents[i]) if k is None else min(int(k), len(self._agents[i]))
        out = np.array(self._agents[i][:n], dtype=np.int64)
        del self._agents[i][:n]
        del self._reasons[i][:n]
        del self._since[i][:n]
        return out

    def pending(self, cls: EventClass | int) -> np.ndarray:
        """クラスの保留 agent_id 配列(順序は投入順)。"""
        return np.array(self._agents[self._slot(cls)], dtype=np.int64)

    def waiting_ticks(self, cls: EventClass | int, now_tick: int) -> np.ndarray:
        """クラスの各保留の待ち tick 数(クラス内順序づけの材料)。"""
        i = self._slot(cls)
        return int(now_tick) - np.array(self._since[i], dtype=np.int64)

    def __len__(self) -> int:
        return sum(len(a) for a in self._agents)

    # ---- 診断カウンタ ----
    def degrade(self, cls: EventClass | int, n: int = 1) -> None:
        """縮退実行(小モデル・観測ブロック削減)を計数(``degraded``)。"""
        self._counters[DIAG_COLUMNS.index("degraded"), self._slot(cls)] += int(n)

    def suppress(self, cls: EventClass | int, n: int = 1) -> None:
        """不応期による抑止を計数(``suppressed``)。"""
        self._counters[DIAG_COLUMNS.index("suppressed"), self._slot(cls)] += int(n)

    def counters(self) -> Mapping[str, Mapping[str, int]]:
        """診断行4列 × 起床クラス別の計数(予算宣言表 §7-5)。"""
        return {
            col: {cls.name: int(self._counters[r, i]) for i, cls in enumerate(self.classes)}
            for r, col in enumerate(DIAG_COLUMNS)
        }

    def totals(self) -> Mapping[str, int]:
        """診断行4列の合計。"""
        return {col: int(self._counters[r].sum()) for r, col in enumerate(DIAG_COLUMNS)}
