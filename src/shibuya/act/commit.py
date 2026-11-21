"""engine.commit — 二相コミットの Phase A(intent 収集)と Phase B(資源ごとの裁定)。

正典(逐語・運用設計書 §2.2)
    ``Phase A (read-only・並列可): 全個体が現在状態を読み intent を出す(LLM由来のintentは
    前tickまでに届いた応答から)``
    ``Phase B (arbitrate・決定論): 資源ごとに intent を集め 優先度キー昇順で確定``
    ``pk = ( ceil_ns(t_notice)=tick開始+δ_perc[秒オフセット],``
    ``       blake3(run_salt‖tick‖resource_id‖agent_id) )   # 辞書式``
    ``Phase C (commit・単一書き手): engine.resolve が確定分だけ適用。``
- 「FLAME GPU 2 の propose→rank→move と1対1(mechanism)。優先度をハッシュで導出=メモリ0・
  再現性は上。**atomic 演算による直接更新は禁止**(GPU で順序が非決定)。」
- 「反復=同一tick内1回(第2希望)まで、以後は次tick(expedient)。**未解決者数は診断行へ**。」
- 「競合クラス別: 席・最後の1個=pk昇順(**在庫減算は Phase C のみ=保存則**)/
  会話招待=1件だけ通し応答判定は通った後/乗車=§2.6/注視・傍受=競合なし/権限行動=原則1人。」
- 「確率と優先度を混ぜない(必要な確率性は pk のハッシュ撹拌に押し込む)。」
- 運用設計書 §2.3: δ_perc は**世界時刻を進めず** tick 内のナノ秒欄としてのみ使う。

逐次ループ宣言(P4)
- ``arbitrate_resources``: **再試行ラウンド数**(既定 1)ぶんのループのみ。intent 数・個体数に
  比例するループなし(整列・群の先頭検出・順位づけはすべて NumPy)。

expedient(本モジュール分)
- 資源 ID の名前空間(POI → 会話相手 → 就寝スロット の順に連番)。設計書は
  ``resource_id`` の割り当てを定めていない。
- δ_perc は**予期クラス別の定数**(知覚契約書 §6 の k=0/1.0/1.6/4.9/6.1 を 0.213 秒に掛けた値)。
  対数正規のばらつき σ_ln=0.20 と注意係数 m_att(知覚契約書)は入っていない(δ_perc は予期クラスの定数のまま)。
- ``SLEEP_SLOTS_PER_CELL = 200``(就寝スロットの容量)。契約書に値がない。
- 第2希望が無いので同一tick内の再試行は**空回り**する(残容量 0)。機構だけ置き、
  未解決件数を診断へ出す(設計書の「未解決者数は診断行へ」を満たすため)。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Sequence
import numpy as np
from shibuya.foundation.vocab.agent_codes import WakeCondition
from shibuya.foundation.hashing import priority_key_array
from shibuya.foundation.types import DEFAULT_TICK_SECONDS, NS_PER_SECOND
from shibuya.foundation.vocab.act_codes import DELTA_PERC_BASE_NS, EXPECTATION_K, SLEEP_SLOTS_PER_CELL

__all__ = [
    "IntentBatch", "ResourceSpace", "CommitPlan", "delta_perc_ns", "arbitrate_resources",
]


#: 起床条件 → 予期クラス(expedient: 会話/計画境界=予期あり・内受容=自発・セル変化=予期なし)。
_CONDITION_EXPECTATION: Final[dict[int, int]] = {
    int(WakeCondition.CONVERSATION_TURN): 1,
    int(WakeCondition.PLAN_SLEEPING): 0,
    int(WakeCondition.PLAN_WORKING): 0,
    int(WakeCondition.PLAN_GENERAL): 0,
    int(WakeCondition.PLAN_TRANSIT): 0,
    int(WakeCondition.INTEROCEPTION): 0,
    int(WakeCondition.ACQUAINTANCE): 2,
    int(WakeCondition.PROXIMITY_SWAP): 2,
    int(WakeCondition.BEING_WATCHED): 2,
    int(WakeCondition.OVERHEARD): 2,
    int(WakeCondition.CELL_BLOCK): 3,
    int(WakeCondition.ACTIVITY_EXPIRY): 0,  # 自分で決めた持続の区切り=自発(C0・expedient)
}


def delta_perc_ns(condition) -> np.ndarray:
    """起床条件 → δ_perc[ns](予期クラス別の定数・expedient)。"""
    cond = np.asarray(condition, dtype=np.int64)
    k = np.asarray(
        [EXPECTATION_K[_CONDITION_EXPECTATION.get(int(c), 0)] for c in cond.ravel()],
        dtype=np.float64,
    )
    return np.rint(k * DELTA_PERC_BASE_NS).astype(np.int64).reshape(cond.shape)


def _concat_s2(parts: Sequence["IntentBatch"]) -> tuple[np.ndarray | None, np.ndarray | None]:
    """〔2-1〕任意の 2 列の連結(どの部分も持たなければ ``None``=今のまま・持たない部分は空の値で埋める)。"""
    has_c = any(p.call_id is not None for p in parts)
    has_f = any(p.s2_flags is not None for p in parts)
    cid = None
    if has_c:
        cid = np.concatenate([p.call_id if p.call_id is not None else np.full(len(p), None, dtype=object)
                              for p in parts])
    flg = None
    if has_f:
        flg = np.concatenate([p.s2_flags if p.s2_flags is not None else np.zeros(len(p), dtype=np.int8)
                              for p in parts]).astype(np.int8)
    return cid, flg


@dataclass(frozen=True)
class IntentBatch:
    """Phase A の出力(SoA)。1 個体につき 1 件までに畳んである。

    Attributes:
        agent_id: int64。
        action_code: int8(``ACTION_CODES`` の値 / ``ENGINE_STEP``)。
        target_id: int32(行動語で意味が変わる: セル / POI / 相手個体)。-1=なし。
        resource_id: int32(``ResourceSpace`` の番号)。-1=競合しない。
        t_notice_ns: int64(**tick 開始 + δ_perc**。pk の第1要素)。
        call_id: 〔第 2 期 2-1〕行ごとの呼の id(object・``None``=呼でない行)。経済の段階 2 の腕のランだけ判断の系が
            付ける(既定 ``None``=列を持たない=今のまま)。購入・食事・引き出しの金の行の原因 ``LlmCall(call_id)``。
        s2_flags: 〔第 2 期 2-1〕行ごとの段階 2 の印(int8・``S2_*`` のビット)。``call_id`` と同じく腕のランだけ。
    """

    agent_id: np.ndarray
    action_code: np.ndarray
    target_id: np.ndarray
    resource_id: np.ndarray
    t_notice_ns: np.ndarray
    call_id: np.ndarray | None = None
    s2_flags: np.ndarray | None = None

    def __post_init__(self) -> None:
        n = self.agent_id.size
        for name in ("action_code", "target_id", "resource_id", "t_notice_ns"):
            if getattr(self, name).size != n:
                raise ValueError(f"IntentBatch.{name} の長さが agent_id と違う")
        for name in ("call_id", "s2_flags"):
            v = getattr(self, name)
            if v is not None and v.size != n:
                raise ValueError(f"IntentBatch.{name} の長さが agent_id と違う")

    def __len__(self) -> int:
        return int(self.agent_id.size)

    @classmethod
    def empty(cls) -> "IntentBatch":
        return cls(
            np.empty(0, dtype=np.int64),
            np.empty(0, dtype=np.int8),
            np.empty(0, dtype=np.int32),
            np.empty(0, dtype=np.int32),
            np.empty(0, dtype=np.int64),
        )

    @classmethod
    def concat(cls, parts: Sequence["IntentBatch"]) -> "IntentBatch":
        parts = [p for p in parts if len(p)]
        if not parts:
            return cls.empty()
        return cls(
            np.concatenate([p.agent_id for p in parts]),
            np.concatenate([p.action_code for p in parts]),
            np.concatenate([p.target_id for p in parts]),
            np.concatenate([p.resource_id for p in parts]),
            np.concatenate([p.t_notice_ns for p in parts]),
            *_concat_s2(parts),
        )

    def take(self, idx) -> "IntentBatch":
        i = np.asarray(idx, dtype=np.int64)
        return IntentBatch(
            self.agent_id[i],
            self.action_code[i],
            self.target_id[i],
            self.resource_id[i],
            self.t_notice_ns[i],
            None if self.call_id is None else self.call_id[i],
            None if self.s2_flags is None else self.s2_flags[i],
        )

    def one_per_agent(self) -> "IntentBatch":
        """同一個体の重複 intent を1件に畳む(LLM 由来 > エンジン継続・並び順に依存しない)。"""
        if len(self) <= 1:
            return self
        # 主鍵=agent_id、次に「LLM 由来を優先」(action_code>=0 を先に)、次に action_code, target
        llm_first = (self.action_code < 0).astype(np.int64)
        order = np.lexsort(
            (self.target_id, self.action_code, llm_first, self.agent_id)
        )
        sorted_agent = self.agent_id[order]
        first = np.ones(order.size, dtype=bool)
        first[1:] = sorted_agent[1:] != sorted_agent[:-1]
        return self.take(np.sort(order[first]))


@dataclass(frozen=True)
class ResourceSpace:
    """資源 ID の名前空間(POI / 会話相手 / 就寝スロット)。"""

    n_poi: int
    n_agents: int
    n_cells: int

    @property
    def partner_offset(self) -> int:
        return int(self.n_poi)

    @property
    def sleep_offset(self) -> int:
        return int(self.n_poi) + int(self.n_agents)

    @property
    def size(self) -> int:
        return int(self.n_poi) + int(self.n_agents) + int(self.n_cells)

    def poi(self, poi_id) -> np.ndarray:
        return np.asarray(poi_id, dtype=np.int64).astype(np.int32)

    def partner(self, agent_id) -> np.ndarray:
        return (np.asarray(agent_id, dtype=np.int64) + self.partner_offset).astype(np.int32)

    def sleep(self, cell_id) -> np.ndarray:
        return (np.asarray(cell_id, dtype=np.int64) + self.sleep_offset).astype(np.int32)

    def capacity(self, resource_id, poi_stock, poi_capacity) -> np.ndarray:
        """資源 ID → この tick に受け入れられる件数。

        POI は ``min(1 tick 受け入れ数, 在庫)``(**在庫の減算は Phase C**=保存則)。
        会話相手は 1 件(招待は1件だけ通す)。就寝スロットは ``SLEEP_SLOTS_PER_CELL``。
        """
        r = np.asarray(resource_id, dtype=np.int64)
        out = np.zeros(r.shape, dtype=np.int64)
        is_poi = (r >= 0) & (r < self.partner_offset)
        is_partner = (r >= self.partner_offset) & (r < self.sleep_offset)
        is_sleep = r >= self.sleep_offset
        if np.any(is_poi):
            pid = r[is_poi]
            out[is_poi] = np.minimum(
                np.asarray(poi_capacity, dtype=np.int64)[pid],
                np.maximum(0, np.asarray(poi_stock, dtype=np.int64)[pid]),
            )
        out[is_partner] = 1
        out[is_sleep] = SLEEP_SLOTS_PER_CELL
        return out


@dataclass(frozen=True)
class CommitPlan:
    """Phase B の出力。"""

    tick: int
    #: 確定した intent(Phase C が適用する)。
    confirmed: IntentBatch
    #: 落選した intent(``ResultCode.LOST_ARBITRATION`` を返し次 tick へ)。
    losers: IntentBatch
    #: 再試行ラウンド数(設計書「同一tick内1回まで」)。
    rounds: int
    #: 資源競合が起きた件数(= 落選 + 再試行で通った件数)。
    n_conflicts: int

    @property
    def n_unresolved(self) -> int:
        """未解決者数(診断行へ)。"""
        return int(len(self.losers))


def _rank_within_resource(resource: np.ndarray) -> np.ndarray:
    """整列済み ``resource`` に対する群内順位(0 始まり)。ループなし。"""
    if resource.size == 0:
        return np.empty(0, dtype=np.int64)
    starts = np.flatnonzero(np.concatenate(([True], resource[1:] != resource[:-1])))
    counts = np.diff(np.append(starts, resource.size))
    return np.arange(resource.size, dtype=np.int64) - np.repeat(starts, counts)


def arbitrate_resources(
    intents: IntentBatch,
    tick: int,
    run_salt: bytes,
    space: ResourceSpace,
    poi_stock: np.ndarray,
    poi_capacity: np.ndarray,
    *,
    retry_rounds: int = 1,
) -> CommitPlan:
    """Phase B: 資源ごとに pk 昇順で確定する(**世界は書き換えない**)。

    Args:
        intents: Phase A の intent(1 個体 1 件に畳んであること)。
        tick: 現在 tick。
        run_salt: 優先度キーの塩。
        space: 資源 ID の名前空間。
        poi_stock / poi_capacity: 容量計算の材料(**読むだけ**)。
        retry_rounds: 同一 tick 内の再試行回数(設計書 §2.2「1回(第2希望)まで」)。

    Returns:
        ``CommitPlan``。
    """
    if len(intents) == 0:
        return CommitPlan(int(tick), IntentBatch.empty(), IntentBatch.empty(), 0, 0)

    free = np.flatnonzero(intents.resource_id < 0)
    contend = np.flatnonzero(intents.resource_id >= 0)
    confirmed_parts = [intents.take(free)]
    n_conflicts = 0
    pending = contend
    rounds = 0
    # 逐次ループ宣言: 再試行ラウンド数ぶん(既定 1+1)。intent 数には比例しない。
    for round_index in range(int(retry_rounds) + 1):
        if pending.size == 0:
            break
        rounds = round_index + 1
        sub = intents.take(pending)
        pk = priority_key_array(run_salt, int(tick), sub.resource_id, sub.agent_id)
        # 辞書式 (resource, t_notice, pk, agent) の昇順
        order = np.lexsort((sub.agent_id, pk, sub.t_notice_ns, sub.resource_id.astype(np.int64)))
        res_sorted = sub.resource_id[order].astype(np.int64)
        rank = _rank_within_resource(res_sorted)
        cap = space.capacity(res_sorted, poi_stock, poi_capacity)
        if round_index > 0:
            cap = np.zeros_like(cap)  # 第2希望が無いので残容量ゼロ(C2 の expedient)
        admitted = rank < cap
        win_local = order[admitted]
        lose_local = order[~admitted]
        if round_index == 0 and lose_local.size:
            n_conflicts += int(lose_local.size)  # 落選は初回裁定で1回だけ数える(層2指摘: 再試行で二重計上しない)
        confirmed_parts.append(sub.take(np.sort(win_local)))
        pending = pending[np.sort(lose_local)]
    losers = intents.take(pending) if pending.size else IntentBatch.empty()
    confirmed = IntentBatch.concat(confirmed_parts)
    return CommitPlan(int(tick), confirmed, losers, rounds, n_conflicts)


def tick_start_ns(tick: int, tick_seconds: int = DEFAULT_TICK_SECONDS) -> int:
    """tick 開始のナノ秒(δ_perc を足す基準)。"""
    return int(tick) * int(tick_seconds) * NS_PER_SECOND
