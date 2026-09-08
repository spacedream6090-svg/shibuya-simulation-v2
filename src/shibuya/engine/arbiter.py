"""engine.arbiter — 繰り延べアービタ(知覚契約書 §6 の裁定規則)。

正典(逐語)
- 「**繰り延べの優先規則(決定09-06・A案)**: v2 は恒常過負荷(U≈17.4/10=1.74)で回るため、
  **EDF(締切順)は主規則にしない**(過負荷 U>1 では domino effect で全タスクが締切を落とす・
  固定優先は下位だけが落とす=Lipari 実読)。規則=**4クラス固定優先: 会話ターン > 計画境界 >
  個体変化 > セル変化**+クラス内は待ち時間/許容遅延の降順+**T_max 超過で1段昇格
  (starvation-free)**+同一体の保留起床は合流+なお不足なら**下位2クラスを縮退実行**
  (小モデル・T1短縮・観測ブロック削減)。」
- 「①抑止された起床は**破棄ではない**(状態トリガは次回起床時に最新状態を読む=情報は失われない)
  ②タイマーは**体×条件ごと**・同一体の複数条件が同時に明けたら**1呼に合流**
  ③不応期は『暴発の上限』の装置で、**平均を10呼/体/日に合わせるのはアービタの仕事**」
- 予算宣言表 **L4**: 「上限400万呼/日(o64)/**平均10呼/体/日が繰り延べアービタの制御目標**」。
- 予算宣言表 §7-5: 「繰り延べ量・昇格数・縮退実行数・不応期による抑止数を**起床クラス別/
  シミュ日**で必ず記録(診断行4列)」= ``DIAG_COLUMNS``。
- 運用設計書 §2.5: 同時刻イベントのタイブレーク第3要素 = ``blake3(run_salt‖tick‖class‖agent)``
  (``core.hashing.wake_tiebreak_array``)。

**設計書との運用差(親へ報告・黙って解決しない)**
    C2 の指示は「``DeferralQueue`` の上に載せる」。``engine.scheduler.DeferralQueue`` は
    保管庫として使う(クラス別 FIFO)。ただし**診断計数はアービタ側で持つ**:
    ``DeferralQueue`` の ``promote()`` は「クラス内リストの ``list.index`` で1件ずつ動かす」
    設計で、過負荷時(保留数千件×昇格数百件/tick)に O(保留数×昇格数) になり W2 を壊す。
    本モジュールは昇格を**待ち時間からの純関数**(``eff_class``)として毎tick 再計算し、
    計数だけを ``DIAG_COLUMNS`` の同じ 4 列 × 4 クラスで持つ(``counters()`` の形は
    ``DeferralQueue.counters()`` と同一)。

純関数性(T3 の前提)
    ``arbitrate()`` は入力の**並び順に依存しない**。候補配列を任意に並べ替えても
    選抜集合・選抜順序・診断計数は同一(``tests/engine/test_arbiter.py`` の性質テスト)。
    整列鍵 = ``(eff_class 昇順, 待ち tick 降順, pk 昇順, agent_id 昇順)``。

逐次ループ宣言(P4)
- ``Arbiter.step``: **クラス数(4)** ぶんのループのみ。候補数・個体数に比例するループなし
  (整列・突合・累積和はすべて NumPy)。

expedient(本モジュール分)
- ``T_MAX_TICKS``(昇格までの待ち tick)= 会話3/計画境界10/個体変化30/セル変化60。
  契約書は「T_max 超過で1段昇格」としか言わず値を与えていない(「クラス内の具体値は
  expedient(感度試験必須)」と明記)。
- 昇格は**累積**(``eff_class = max(0, class − waited // T_max[class])``)。1段ずつ動かす
  実装と違い、待ち続ければ必ず最上位に達する=starvation-free が算術で保証できる。
- ``DEGRADE_COST_FACTOR = 0.5``(縮退実行1呼を通常呼 0.5 呼ぶんとして予算に数える)。
  契約書は「小モデル・T1短縮・観測ブロック削減」としか言わず**コスト比を与えていない**。
  この係数は**トークン/計算量の予算**にだけ効き、**呼数の上限(L4)には効かない**
  (下の「L4 は呼数の硬い上限」)。
- 縮退は「予算が足りないときだけ」下位2クラス(個体変化・セル変化)に適用する。
- ``POOL_CAP_TICKS = 2``(端数繰越の上限を 2 tick ぶんに切る)。L4 は 1 日総量の行なので
  tick ごとの床(``floor``)で捨てると総量が届かない。繰越を無制限にすると夜間に溜めた枠で
  昼に暴発するので、繰越の在庫に蓋をした(**expedient**: 契約書は繰越を規定していない)。

**L4 は呼数の硬い上限(バグ修正・2026-09-08)**
    予算行 L4 は「**上限400万呼/日**(=憲法1の監査点)」。実測ランは 5,000 体で 56,488 呼
    = 11.30 呼/体/日 で、按分上限 50,000 呼(34.72 呼/tick × 1,440)を **13% 超えていた**。
    原因は本モジュールの ⑤ で、縮退実行を ``cost=0.5`` として**累積コスト**で切っていたこと
    (縮退呼が 2 件で 1 枠 → 呼数は上限の最大 2 倍まで通る)。縮退が減らすのは 1 呼あたりの
    トークン/計算量であって**呼の本数ではない**ので、L4 の監査点としては誤り。
    修正: 選抜数を ``floor(その tick に使える呼数)`` で**必ず**頭打ちにする
    (``n_sel = min(コスト基準, 呼数基準)``)。会話ターンは④の固定優先で先頭に並ぶので、
    上限が効いても会話は予算の中で最優先のまま(設計どおり呼数の約45%を占める)。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping, Sequence

import numpy as np

from shibuya.agents.state import N_WAKE_CONDITIONS, REFRACTORY_MINUTES
from shibuya.core.hashing import wake_tiebreak_array
from shibuya.core.types import DEFERRAL_CLASSES, EventClass
from shibuya.engine.scheduler import DIAG_COLUMNS, DeferralQueue

__all__ = [
    "T_MAX_TICKS",
    "DEGRADE_COST_FACTOR",
    "DEGRADE_CLASSES",
    "POOL_CAP_TICKS",
    "L4_CALLS_PER_DAY",
    "L4_REFERENCE_AGENTS",
    "call_budget_per_tick",
    "WakeCandidates",
    "ArbiterDecision",
    "arbitrate",
    "Arbiter",
]

#: 昇格までの待ち tick(クラス別・expedient)。
T_MAX_TICKS: Final[dict[int, int]] = {
    int(EventClass.CONVERSATION): 3,
    int(EventClass.PLAN_BOUNDARY): 10,
    int(EventClass.INDIVIDUAL): 30,
    int(EventClass.CELL): 60,
}
#: 縮退実行1呼のコスト比(expedient)。
DEGRADE_COST_FACTOR: Final[float] = 0.5
#: 縮退の対象=下位2クラス(知覚契約書 §6)。
DEGRADE_CLASSES: Final[tuple[int, ...]] = (int(EventClass.INDIVIDUAL), int(EventClass.CELL))
#: 端数の繰越に許す在庫[tick ぶん](expedient)。
POOL_CAP_TICKS: Final[float] = 2.0

#: 予算行 L4(呼/シミュ日・40万体基準)。
L4_CALLS_PER_DAY: Final[int] = 4_000_000
L4_REFERENCE_AGENTS: Final[int] = 400_000
_TICKS_PER_DAY: Final[int] = 1_440

#: 不応期[tick](= 分。tick_seconds=60 なので 1 分 = 1 tick)。
REFRACTORY_TICKS: Final[np.ndarray] = np.asarray(REFRACTORY_MINUTES, dtype=np.int32)


def call_budget_per_tick(
    n_agents: int,
    *,
    calls_per_day: int = L4_CALLS_PER_DAY,
    reference_agents: int = L4_REFERENCE_AGENTS,
    ticks_per_day: int = _TICKS_PER_DAY,
) -> float:
    """予算行 L4 を tick あたり・当該規模へ按分した呼数。

    ``4,000,000 / 1,440 × n / 400,000``。5,000 体なら **34.72 呼/tick**
    (=10 呼/体/シミュ日=L4 の制御目標)。
    """
    if n_agents < 0:
        raise ValueError("n_agents は 0 以上")
    return float(calls_per_day) / float(ticks_per_day) * (float(n_agents) / float(reference_agents))


@dataclass(frozen=True)
class WakeCandidates:
    """1 tick 分の起床候補(全て同じ長さの配列)。

    Attributes:
        agent_id: int64。
        condition: int8(``agents.state.WakeCondition``)。
        class_rank: int64(``core.types.EventClass``)。
        since_tick: int64(**最初に起床条件が立った tick**。待ち時間の基準)。
    """

    agent_id: np.ndarray
    condition: np.ndarray
    class_rank: np.ndarray
    since_tick: np.ndarray

    def __post_init__(self) -> None:
        n = self.agent_id.size
        for name in ("condition", "class_rank", "since_tick"):
            if getattr(self, name).size != n:
                raise ValueError(f"WakeCandidates.{name} の長さが agent_id と違う")

    def __len__(self) -> int:
        return int(self.agent_id.size)

    @classmethod
    def empty(cls) -> "WakeCandidates":
        return cls(
            np.empty(0, dtype=np.int64),
            np.empty(0, dtype=np.int8),
            np.empty(0, dtype=np.int64),
            np.empty(0, dtype=np.int64),
        )

    @classmethod
    def concat(cls, parts: Sequence["WakeCandidates"]) -> "WakeCandidates":
        parts = [p for p in parts if len(p)]
        if not parts:
            return cls.empty()
        return cls(
            np.concatenate([p.agent_id for p in parts]),
            np.concatenate([p.condition for p in parts]),
            np.concatenate([p.class_rank for p in parts]),
            np.concatenate([p.since_tick for p in parts]),
        )

    def take(self, idx: np.ndarray) -> "WakeCandidates":
        return WakeCandidates(
            self.agent_id[idx], self.condition[idx], self.class_rank[idx], self.since_tick[idx]
        )


@dataclass(frozen=True)
class ArbiterDecision:
    """1 tick 分の裁定結果(純関数 ``arbitrate`` の出力)。"""

    tick: int
    #: 実際に呼ぶもの(**選抜順**)。
    selected: WakeCandidates
    #: 選抜されたものの実効クラス(昇格後)。
    selected_eff_class: np.ndarray
    #: 縮退実行するもののマスク(``selected`` と同じ長さ)。
    selected_degraded: np.ndarray
    #: 次 tick へ繰り延べるもの(順序は選抜順の続き)。
    deferred: WakeCandidates
    #: 不応期で抑止されたもの(**破棄ではない**=状態トリガは次回起床で最新値を読む)。
    suppressed: WakeCandidates
    #: 同一体の複数条件を1呼に合流した件数(クラス別)。
    merged_per_class: np.ndarray
    #: 診断行 4 列 × 4 クラスの増分。
    diag: np.ndarray

    @property
    def n_calls(self) -> int:
        return int(len(self.selected))

    def counters(self) -> Mapping[str, Mapping[str, int]]:
        return {
            col: {c.name: int(self.diag[r, i]) for i, c in enumerate(DEFERRAL_CLASSES)}
            for r, col in enumerate(DIAG_COLUMNS)
        }


def _class_slot(class_rank: np.ndarray) -> np.ndarray:
    """class_rank(0..3)→ ``DEFERRAL_CLASSES`` の添字(同値だが明示する)。"""
    return np.clip(class_rank.astype(np.int64), 0, len(DEFERRAL_CLASSES) - 1)


def arbitrate(
    candidates: WakeCandidates,
    tick: int,
    budget: float,
    run_salt: bytes,
    refractory_until: np.ndarray | None = None,
) -> ArbiterDecision:
    """繰り延べアービタの**純関数**本体(入力の並び順に依存しない)。

    Args:
        candidates: この tick の起床候補(新規+保留の合併)。
        tick: 現在 tick。
        budget: この tick に使える呼数(``call_budget_per_tick``)。
        run_salt: タイブレークハッシュの塩。
        refractory_until: ``(n_agents, K)`` int32(体×条件ごとの「次に起床してよい tick」)。
            None なら不応期の抑止をしない。

    Returns:
        ``ArbiterDecision``。
    """
    n_classes = len(DEFERRAL_CLASSES)
    diag = np.zeros((len(DIAG_COLUMNS), n_classes), dtype=np.int64)
    merged = np.zeros(n_classes, dtype=np.int64)
    if len(candidates) == 0:
        empty = WakeCandidates.empty()
        return ArbiterDecision(
            int(tick), empty, np.empty(0, dtype=np.int64), np.empty(0, dtype=bool),
            empty, empty, merged, diag,
        )

    agent = candidates.agent_id.astype(np.int64)
    cond = candidates.condition.astype(np.int64)
    cls = candidates.class_rank.astype(np.int64)
    since = candidates.since_tick.astype(np.int64)

    # ---- ① 不応期(§6 運用規定①: 抑止は破棄ではない) ----
    if refractory_until is not None:
        ru = np.asarray(refractory_until)
        if ru.ndim != 2 or ru.shape[1] != N_WAKE_CONDITIONS:
            raise ValueError(f"refractory_until は (n_agents, {N_WAKE_CONDITIONS})")
        blocked = ru[agent, cond] > int(tick)
    else:
        blocked = np.zeros(agent.size, dtype=bool)
    sup_idx = np.flatnonzero(blocked)
    live_idx = np.flatnonzero(~blocked)
    if sup_idx.size:
        np.add.at(diag[DIAG_COLUMNS.index("suppressed")], _class_slot(cls[sup_idx]), 1)
    suppressed = candidates.take(sup_idx)

    agent, cond, cls, since = agent[live_idx], cond[live_idx], cls[live_idx], since[live_idx]
    live = candidates.take(live_idx)
    if agent.size == 0:
        empty = WakeCandidates.empty()
        return ArbiterDecision(
            int(tick), empty, np.empty(0, dtype=np.int64), np.empty(0, dtype=bool),
            empty, suppressed, merged, diag,
        )

    # ---- ② T_max 超過で昇格(累積・starvation-free) ----
    waited = np.maximum(0, int(tick) - since)
    tmax = np.asarray([T_MAX_TICKS[int(c)] for c in DEFERRAL_CLASSES], dtype=np.int64)
    tmax_of = tmax[_class_slot(cls)]
    steps = waited // tmax_of
    eff_class = np.maximum(0, cls - steps)
    # 「昇格数」は**事象の数**(待ちが T_max の倍数に達した tick だけ 1 件)。
    # 昇格中の件数を毎tick 数えると 1 件が何十回も計上され、§7-5 の「昇格数/シミュ日」が壊れる。
    promoted_mask = (waited > 0) & (waited % tmax_of == 0) & (cls > 0)
    if promoted_mask.any():
        np.add.at(
            diag[DIAG_COLUMNS.index("promoted")], _class_slot(eff_class[promoted_mask]), 1
        )

    # ---- ③ 同一体の合流(§6 運用規定②) ----
    pk = wake_tiebreak_array(run_salt, int(tick), eff_class, agent)
    # 代表の選び方: (eff_class 昇順, 待ち降順, pk 昇順, condition 昇順)
    rank = np.lexsort((cond, pk, -waited, eff_class, agent))
    first = np.ones(rank.size, dtype=bool)
    sorted_agent = agent[rank]
    first[1:] = sorted_agent[1:] != sorted_agent[:-1]
    keep = np.sort(rank[first])
    dropped = agent.size - keep.size
    if dropped:
        drop_mask = np.ones(agent.size, dtype=bool)
        drop_mask[keep] = False
        np.add.at(merged, _class_slot(eff_class[drop_mask]), 1)
    agent, cond, cls, since = agent[keep], cond[keep], cls[keep], since[keep]
    waited, eff_class, pk = waited[keep], eff_class[keep], pk[keep]
    live = live.take(keep)

    # ---- ④ 固定優先の整列 ----
    order = np.lexsort((agent, pk, -waited, eff_class))
    agent, cond, cls, since = agent[order], cond[order], cls[order], since[order]
    waited, eff_class, pk = waited[order], eff_class[order], pk[order]
    live = live.take(order)

    # ---- ⑤ 予算の割り当て(足りなければ下位2クラスを縮退) ----
    cost = np.ones(agent.size, dtype=np.float64)
    degrade = np.zeros(agent.size, dtype=bool)
    if float(agent.size) > float(budget):
        degrade = np.isin(eff_class, np.asarray(DEGRADE_CLASSES, dtype=np.int64))
        cost = np.where(degrade, DEGRADE_COST_FACTOR, 1.0)
    n_sel = int(np.searchsorted(np.cumsum(cost), float(budget) + 1e-9, side="right"))
    # **L4 は呼数の硬い上限**: 縮退は 1 呼あたりのトークン/計算量を下げるだけで、呼の本数は
    # 減らさない。コスト基準だけで切ると縮退呼が 2 件で 1 枠になり、Σ呼/日が上限を超える
    # (実測 11.30 呼/体/日 > 10)。呼数基準 ``floor(budget)`` で必ず頭打ちにする。
    n_sel = min(n_sel, int(np.floor(float(budget) + 1e-9)), agent.size)
    sel = slice(0, n_sel)
    rest = slice(n_sel, agent.size)

    selected = live.take(np.arange(n_sel))
    deferred = live.take(np.arange(n_sel, agent.size))
    sel_degraded = degrade[sel]
    if sel_degraded.any():
        np.add.at(
            diag[DIAG_COLUMNS.index("degraded")], _class_slot(eff_class[sel][sel_degraded]), 1
        )
    if deferred.agent_id.size:
        # 「繰り延べ量」は**新しく繰り延べられた件数**(この tick に立った起床が通らなかった数)。
        # 既に保留中の件を毎tick 数え直すと 1 件が何十回も計上される(backlog は診断列
        # ``pending_wakes`` が持つ)。
        newly = since[rest] == int(tick)
        if newly.any():
            np.add.at(
                diag[DIAG_COLUMNS.index("deferred")], _class_slot(eff_class[rest][newly]), 1
            )

    return ArbiterDecision(
        tick=int(tick),
        selected=selected,
        selected_eff_class=eff_class[sel].copy(),
        selected_degraded=sel_degraded.copy(),
        deferred=deferred,
        suppressed=suppressed,
        merged_per_class=merged,
        diag=diag,
    )


class Arbiter:
    """毎tick の裁定+保留の持ち越し+診断計数の積み上げ(1 シミュ日ぶん)。

    ``engine.scheduler.DeferralQueue`` をクラス別 FIFO の**保管庫**として使い、
    起床条件 id と ``since_tick`` は同じ順序の並行配列で持つ(``DeferralQueue`` は
    取り出し時に理由コードを返さないため)。診断計数はモジュール docstring のとおり
    アービタ側で持つ。

    Example:
        >>> arb = Arbiter(n_agents=10, run_salt=b"s", budget=2.0)
        >>> c = WakeCandidates(np.array([1, 2, 3]), np.array([10, 10, 10], dtype=np.int8),
        ...                    np.array([3, 3, 3]), np.array([0, 0, 0]))
        >>> d = arb.step(0, c)
        >>> d.n_calls   # 3件>予算2 → 縮退印は付くが**呼数は L4 の硬い上限**で 2 件
        2
    """

    def __init__(
        self,
        n_agents: int,
        run_salt: bytes,
        budget: float | None = None,
        *,
        classes=DEFERRAL_CLASSES,
    ) -> None:
        self.n_agents = int(n_agents)
        self.run_salt = bytes(run_salt)
        self.budget = float(budget) if budget is not None else call_budget_per_tick(n_agents)
        self.queue = DeferralQueue(classes)
        self.classes = tuple(classes)
        #: 端数の繰越在庫[呼](L4 は 1 日総量の行なので tick ごとの floor で捨てない)。
        self._pool = 0.0
        self._pool_cap = float(self.budget) * POOL_CAP_TICKS
        #: 使えたのに使わなかった枠の累計(診断)。
        self.budget_unused = 0.0
        self._pending = WakeCandidates.empty()
        self._last_tick = 0
        self._diag_total = np.zeros((len(DIAG_COLUMNS), len(self.classes)), dtype=np.int64)
        self._merged_total = np.zeros(len(self.classes), dtype=np.int64)
        self.n_calls_total = 0

    # ---- 保留 ----
    @property
    def pending(self) -> WakeCandidates:
        """繰り延べ中の候補(次 tick に再合流する)。"""
        return self._pending

    def n_pending(self) -> int:
        return len(self._pending)

    def _store(self, deferred: WakeCandidates) -> None:
        """保管庫(``DeferralQueue``)を貼り替える。逐次ループ宣言: クラス数 4 ぶん。"""
        self._pending = deferred
        for cls in self.classes:
            self.queue.pop_class(cls)  # 前 tick 分を捨てる(保持は _pending 側)
        if len(deferred) == 0:
            return
        for cls in self.classes:
            ids = deferred.agent_id[deferred.class_rank == int(cls)]
            if ids.size:
                self.queue.defer_many(ids, cls, "arbiter.deferred", int(self._last_tick))

    # ---- 1 tick ----
    def step(
        self,
        tick: int,
        candidates: WakeCandidates,
        refractory_until: np.ndarray | None = None,
    ) -> ArbiterDecision:
        """新規候補と保留を合わせて裁定し、落選分を保留に積む。"""
        self._last_tick = int(tick)
        merged_in = WakeCandidates.concat([self._pending, candidates])
        # L4 の総量を落とさずに呼数を硬く切るため、端数を繰り越す(在庫は 2 tick ぶんで頭打ち)。
        self._pool = min(self._pool + self.budget, self._pool_cap)
        decision = arbitrate(merged_in, tick, self._pool, self.run_salt, refractory_until)
        self._pool -= float(decision.n_calls)
        self.budget_unused = max(0.0, self._pool)
        self._store(decision.deferred)
        self._diag_total += decision.diag
        self._merged_total += decision.merged_per_class
        self.n_calls_total += decision.n_calls
        return decision

    # ---- 診断(予算宣言表 §7-5) ----
    def counters(self) -> Mapping[str, Mapping[str, int]]:
        """診断行 4 列 × 起床クラス別の累積(``DeferralQueue.counters`` と同じ形)。"""
        return {
            col: {c.name: int(self._diag_total[r, i]) for i, c in enumerate(self.classes)}
            for r, col in enumerate(DIAG_COLUMNS)
        }

    def totals(self) -> Mapping[str, int]:
        """診断行 4 列の合計。"""
        return {col: int(self._diag_total[r].sum()) for r, col in enumerate(DIAG_COLUMNS)}

    @property
    def merged_total(self) -> int:
        """合流(1呼にまとめた)件数の累計。"""
        return int(self._merged_total.sum())
