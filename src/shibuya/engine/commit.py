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
  対数正規のばらつき σ_ln=0.20 と注意係数 m_att は C3(知覚レンダラ)で入れる。
- ``SLEEP_SLOTS_PER_CELL = 200``(就寝スロットの容量)。契約書に値がない。
- 第2希望が無いので同一tick内の再試行は**空回り**する(残容量 0)。機構だけ置き、
  未解決件数を診断へ出す(設計書の「未解決者数は診断行へ」を満たすため)。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Sequence

import numpy as np

from shibuya.agents.state import WakeCondition
from shibuya.core.hashing import priority_key_array
from shibuya.core.types import DEFAULT_TICK_SECONDS, NS_PER_SECOND
from shibuya.llm.contract import ACTION_CODES as _CONTRACT_ACTION_CODES
from shibuya.llm.contract import ACTION_VOCAB_12
from shibuya.llm.contract import UNDEFINED_ACTION
from shibuya.llm.parser import parse_two_line

__all__ = [
    "UNDEFINED_ACTION",
    "parse_action",
    "pair_partners",
    "engine_continuations",
    "intents_from_responses",
    "ACTION_WORDS",
    "ACTION_CODES",
    "ENGINE_STEP",
    "ACT_MOVE",
    "ACT_BOARD",
    "ACT_ALIGHT",
    "ACT_BUY",
    "ACT_WAIT",
    "ACT_TALK",
    "ACT_LEAVE",
    "ACT_REPORT",
    "ACT_HELP",
    "ACT_REFUSE",
    "ACT_REST",
    "ACT_SLEEP",
    "DELTA_PERC_BASE_NS",
    "EXPECTATION_K",
    "SLEEP_SLOTS_PER_CELL",
    "IntentBatch",
    "ResourceSpace",
    "CommitPlan",
    "delta_perc_ns",
    "arbitrate_resources",
]

#: 行動語(行動契約書 §2.1 の 12 語・順序=表の出現順)。**正典は ``llm.contract``**。
ACTION_WORDS: Final[tuple[str, ...]] = ACTION_VOCAB_12
#: 行動語 → コード(``llm.contract.ACTION_CODES`` と**同一の値**。二重定義を作らない)。
ACTION_CODES: Final[dict[str, int]] = dict(_CONTRACT_ACTION_CODES)

ACT_MOVE: Final[int] = ACTION_CODES["移動"]
ACT_BOARD: Final[int] = ACTION_CODES["乗車"]
ACT_ALIGHT: Final[int] = ACTION_CODES["降車"]
ACT_BUY: Final[int] = ACTION_CODES["購入"]
ACT_WAIT: Final[int] = ACTION_CODES["待機"]
ACT_TALK: Final[int] = ACTION_CODES["会話"]
ACT_LEAVE: Final[int] = ACTION_CODES["退去"]
ACT_REPORT: Final[int] = ACTION_CODES["通報"]
ACT_HELP: Final[int] = ACTION_CODES["手伝い"]
ACT_REFUSE: Final[int] = ACTION_CODES["断る"]
ACT_REST: Final[int] = ACTION_CODES["休憩"]
ACT_SLEEP: Final[int] = ACTION_CODES["就寝"]

#: エンジン内部の継続(経路の1歩)。LLM 由来ではないので負のコード。
ENGINE_STEP: Final[int] = -1

#: δ_perc の基準[ns](単純反応時間 213 ms・知覚契約書 §6)。
DELTA_PERC_BASE_NS: Final[int] = 213_000_000
#: 予期クラス係数 k(C0自発0 / C1予期あり1.0 / C2注意内の社会変化1.6 / C3予期なし4.9 / C4突発6.1)。
EXPECTATION_K: Final[tuple[float, ...]] = (0.0, 1.0, 1.6, 4.9, 6.1)
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
}

#: 就寝スロットの1セルあたり容量(expedient)。
SLEEP_SLOTS_PER_CELL: Final[int] = 200


def delta_perc_ns(condition) -> np.ndarray:
    """起床条件 → δ_perc[ns](予期クラス別の定数・expedient)。"""
    cond = np.asarray(condition, dtype=np.int64)
    k = np.asarray(
        [EXPECTATION_K[_CONDITION_EXPECTATION.get(int(c), 0)] for c in cond.ravel()],
        dtype=np.float64,
    )
    return np.rint(k * DELTA_PERC_BASE_NS).astype(np.int64).reshape(cond.shape)


@dataclass(frozen=True)
class IntentBatch:
    """Phase A の出力(SoA)。1 個体につき 1 件までに畳んである。

    Attributes:
        agent_id: int64。
        action_code: int8(``ACTION_CODES`` の値 / ``ENGINE_STEP``)。
        target_id: int32(行動語で意味が変わる: セル / POI / 相手個体)。-1=なし。
        resource_id: int32(``ResourceSpace`` の番号)。-1=競合しない。
        t_notice_ns: int64(**tick 開始 + δ_perc**。pk の第1要素)。
    """

    agent_id: np.ndarray
    action_code: np.ndarray
    target_id: np.ndarray
    resource_id: np.ndarray
    t_notice_ns: np.ndarray

    def __post_init__(self) -> None:
        n = self.agent_id.size
        for name in ("action_code", "target_id", "resource_id", "t_notice_ns"):
            if getattr(self, name).size != n:
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
        )

    def take(self, idx) -> "IntentBatch":
        i = np.asarray(idx, dtype=np.int64)
        return IntentBatch(
            self.agent_id[i],
            self.action_code[i],
            self.target_id[i],
            self.resource_id[i],
            self.t_notice_ns[i],
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


# ------------------------------------------------------------------ Phase A(intent 収集)
#: パーサが行動語を取れなかったときのコード(行動契約書 §7 段1「未定義行動レコード」)。
#: **正典は ``llm.contract.UNDEFINED_ACTION``**(値 −2)を import している。


def parse_action(text: str) -> int:
    """2行形から行動語を取り出してコードにする(**正典パーサへの薄い委譲**)。

    Returns:
        ``ACTION_CODES`` の値(12 語)。取れない/12 語の外(役割語を含む)なら
        ``UNDEFINED_ACTION``。

    Note:
        C2 ではここに最小写像を置いていたが、C3 で正典のパーサ
        (``llm.parser.parse_two_line``・ラベル基準の寛容行指向・知覚契約書 §2.5)が入ったので
        **委譲に置き換えた**(パーサを2つ持たない)。§2.2 の役割語は ``_APPLY`` に対応分岐が
        無い(効果先は C4)ため、ここでは 12 語だけをコード化し、他は未定義扱い=``resolve`` が
        「待機」に落とす(§2 共通必須事項③の安全弁)。
    """
    if not text:
        return UNDEFINED_ACTION
    word = parse_two_line(text).action
    if word is None:
        return UNDEFINED_ACTION
    return int(ACTION_CODES.get(word, UNDEFINED_ACTION))


def pair_partners(agent_id: np.ndarray, cell: np.ndarray) -> np.ndarray:
    """同一セルに居る**起床中の**個体から会話相手を決める(決定論・ループなし)。

    規則(expedient): セル内の最小 id を相手にする。最小 id 本人の相手はセル内の 2 番目。
    同じ相手を複数人が指名する=**会話招待の資源競合**が起きる(設計書 §2.2「会話招待=
    1件だけ通し」を Phase B で実際に効かせるための形)。

    Returns:
        ``agent_id`` と同じ並びの相手 id(単独セルなら -1)。
    """
    a = np.asarray(agent_id, dtype=np.int64)
    c = np.asarray(cell, dtype=np.int64)
    out = np.full(a.shape, -1, dtype=np.int64)
    if a.size == 0:
        return out
    order = np.lexsort((a, c))
    sa, sc = a[order], c[order]
    starts = np.flatnonzero(np.concatenate(([True], sc[1:] != sc[:-1])))
    counts = np.diff(np.append(starts, sc.size))
    first = np.repeat(sa[starts], counts)
    second = np.repeat(np.where(counts > 1, sa[np.minimum(starts + 1, sc.size - 1)], -1), counts)
    partner = np.where(sa == first, second, first)
    partner = np.where(c[order] < 0, -1, partner)
    out[order] = partner
    return out


def engine_continuations(agents, space: ResourceSpace, tick: int) -> IntentBatch:
    """Phase A のエンジン内部分: 移動中の個体の「経路の1歩」。

    δ_perc は 0(**自発**=予期クラス C0)。資源競合なし。
    """
    from shibuya.agents.state import Activity  # 局所 import(層は engine>agents で合法)

    moving = np.flatnonzero(
        (agents.registry.activity == int(Activity.MOVING)) & (agents.registry.target_node >= 0)
    ).astype(np.int64)
    n = moving.size
    return IntentBatch(
        agent_id=moving,
        action_code=np.full(n, ENGINE_STEP, dtype=np.int8),
        target_id=agents.registry.target_node[moving].astype(np.int32),
        resource_id=np.full(n, -1, dtype=np.int32),
        t_notice_ns=np.full(n, tick_start_ns(tick), dtype=np.int64),
    )


def intents_from_responses(
    agents,
    world,
    space: ResourceSpace,
    tick: int,
    agent_id: np.ndarray,
    condition: np.ndarray,
    action_code: np.ndarray,
    *,
    home_cell: np.ndarray | None = None,
    work_cell: np.ndarray | None = None,
) -> IntentBatch:
    """Phase A の LLM 由来分: 行動コード → 対象と資源を**エンジンが**決めて intent にする。

    行動契約書 §1 の「対象」欄は C3 のパーサが読む。C2 は行動語だけを LLM から受け取り、
    対象は文脈からエンジンが導く(**expedient**・そのぶん「対象を間違える」失敗は起きない)。

    Args:
        agents / world: 現在状態(**読むだけ**)。
        space: 資源名前空間。
        tick: 現在 tick。
        agent_id: 呼んだ個体(昇順でなくてよい)。
        condition: 起床条件(δ_perc の予期クラスに使う)。
        action_code: ``parse_action`` の結果(``UNDEFINED_ACTION`` を含む)。
        home_cell / work_cell: 移動・就寝の既定の行き先(mock スケジュール由来)。

    Returns:
        ``IntentBatch``(1 個体 1 件)。
    """
    a = np.asarray(agent_id, dtype=np.int64)
    n = a.size
    code = np.asarray(action_code, dtype=np.int64).copy()
    # 未定義行動は「待機」へ落とす(行動契約書 §7 段1・resolve が結果コードを付ける)
    code_out = np.where(code == UNDEFINED_ACTION, ACT_WAIT, code).astype(np.int8)
    target = np.full(n, -1, dtype=np.int64)
    resource = np.full(n, -1, dtype=np.int64)
    if n == 0:
        return IntentBatch.empty()

    cell = agents.registry.cell[a].astype(np.int64)

    # 移動: 行き先=職場/自宅のうち今いない方(mock)。無ければ現在セル。
    is_move = code_out == ACT_MOVE
    if np.any(is_move):
        if home_cell is not None and work_cell is not None:
            hc = np.asarray(home_cell, dtype=np.int64)[a]
            wc = np.asarray(work_cell, dtype=np.int64)[a]
            dest = np.where(cell == wc, hc, wc)
        else:
            dest = cell
        target = np.where(is_move, dest, target)

    # 購入: 現在セルの POI(最小 id)。無ければ -1 → 失敗(在庫切れ扱いでなく対象不正)。
    is_buy = code_out == ACT_BUY
    if np.any(is_buy):
        poi_cell = world.pois.cell.astype(np.int64)
        order = np.lexsort((np.arange(poi_cell.size), poi_cell))
        sorted_cells = poi_cell[order]
        pos = np.searchsorted(sorted_cells, cell, side="left")
        pos_c = np.clip(pos, 0, max(0, sorted_cells.size - 1))
        found = (sorted_cells.size > 0) & (sorted_cells[pos_c] == cell)
        poi = np.where(found, order[pos_c], -1)
        target = np.where(is_buy, poi, target)
        resource = np.where(is_buy & (poi >= 0), space.poi(np.maximum(poi, 0)), resource)

    # 会話: 同一セルの起床者から相手を選ぶ(資源=相手)。
    is_talk = code_out == ACT_TALK
    if np.any(is_talk):
        partner = pair_partners(a, cell)
        target = np.where(is_talk, partner, target)
        resource = np.where(
            is_talk & (partner >= 0), space.partner(np.maximum(partner, 0)), resource
        )

    # 就寝: 寝床=自宅セル(資源=そのセルの就寝スロット)。
    is_sleep = code_out == ACT_SLEEP
    if np.any(is_sleep):
        bed = np.asarray(home_cell, dtype=np.int64)[a] if home_cell is not None else cell
        target = np.where(is_sleep, bed, target)
        resource = np.where(is_sleep & (bed >= 0), space.sleep(np.maximum(bed, 0)), resource)

    t0 = tick_start_ns(tick)
    return IntentBatch(
        agent_id=a,
        action_code=code_out,
        target_id=target.astype(np.int32),
        resource_id=resource.astype(np.int32),
        t_notice_ns=(t0 + delta_perc_ns(condition)).astype(np.int64),
    )
