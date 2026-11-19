"""act.ops.intent_writes — 割る段で ``engine/resolve.py`` を割った割り先(全ファイルの表 §4・名の表は
``tools/pkgmove/map.toml`` の割る行)。

中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の
方針は、主な割り先 ``act/apply.py`` に残した元の docstring を読むこと。
"""

from __future__ import annotations

from typing import Final
import numpy as np
from shibuya.foundation.vocab.agent_codes import INTENT_NONE, IntentKind, Activity, ResultCode
from shibuya.world.model.agent_table import (
    AgentState,
)
from shibuya.foundation.vocab.act_codes import ACT_MOVE, ACT_NONE, ACT_WAIT, ENGINE_STEP
from shibuya.world.model.state import World
from shibuya.foundation.write_guard import _require_thawed

__all__ = [
    "set_activity", "set_activity_until", "set_intent", "clear_intent", "fail_intent", "relabel_intent_failure",
    "INTENT_KEEP_ACTIONS", "intent_kept_by",
]


#: 段 2c: 意図(``intent_action``)を**保つ**行為(親決定 Q20=ユーザー決定「意図は達成か失敗まで保持」)。
#: エンジン継続=歩いている途中 / なし・待機=「新しい行為が無い」。これに加えて**行き先が同じ移動**も
#: 保つ(``intent_kept_by``)。それ以外=世界に触れる行為(購入/食事/並ぶ/会話/乗車/就寝/退去/通報/
#: 手伝い/断る)と行き先の変わる移動は意図を上書きする(=消す)。
INTENT_KEEP_ACTIONS: Final[tuple[int, ...]] = (ENGINE_STEP, ACT_NONE, ACT_WAIT)


def set_activity(agents: AgentState, agent_id, until, kind) -> None:
    """**活動の持続と種別**を書く(二層の段 2・``engine.activity`` が値を決める・書き手は本関数)。

    Args:
        agent_id: 体(重複なし)。
        until: ``activity_until``(満了の tick・``-1``=活動なし)。
        kind: ``ActivityKind``。

    ``activity_columns`` の無いラン(v1/v2・``--activity off``)では呼ばれない。
    """
    a = np.asarray(agent_id, dtype=np.int64)
    if a.size == 0:
        return
    with agents.writable():
        _require_thawed(agents)
        agents.registry.activity_until[a] = np.asarray(until, dtype=np.int64).astype(np.int32)
        agents.registry.activity_kind[a] = np.asarray(kind, dtype=np.int64).astype(np.int8)


def set_activity_until(agents: AgentState, agent_id, until) -> None:
    """``activity_until`` だけを書き換える(到着・会話成立の満了=二層の段 2)。"""
    a = np.asarray(agent_id, dtype=np.int64)
    if a.size == 0:
        return
    with agents.writable():
        _require_thawed(agents)
        agents.registry.activity_until[a] = np.asarray(until, dtype=np.int64).astype(np.int32)


# ---------------------------------------------------------------- 段 2c 意図の保持
def _clear_intent_fields(r, a: np.ndarray) -> None:
    """意図の 4 欄を「なし」に戻す(``writable`` の内側から呼ぶ)。"""
    r.intent_action[a] = np.int8(INTENT_NONE)
    r.intent_target[a] = np.int32(-1)
    r.intent_kind[a] = np.int8(int(IntentKind.NONE))
    r.intent_since[a] = np.int32(-1)


def intent_kept_by(agents: AgentState, world: World, agent_id, code, target) -> np.ndarray:
    """意図を持つ体に適用する行為が意図を**保つ**か(段 2c・親決定 Q20・**読むだけ**)。

    ``INTENT_KEEP_ACTIONS``(エンジン継続・なし・待機)と、**行き先が同じ移動**(対象セル=いま
    歩いている目的ノードのセル・着いていれば今いるセル)が真。``engine.intent`` が上書きの件数を
    数えるのにも同じ 1 本を使う。
    """
    a = np.asarray(agent_id, dtype=np.int64)
    c = np.asarray(code, dtype=np.int64)
    t = np.asarray(target, dtype=np.int64)
    keep = np.isin(c, INTENT_KEEP_ACTIONS)
    mv = c == ACT_MOVE
    if bool(mv.any()):
        r = agents.registry
        tn = np.asarray(r.target_node, dtype=np.int64)[a]
        node_cell = np.asarray(world.assets.node_cell, dtype=np.int64)
        cur = np.where(tn >= 0, node_cell[np.maximum(tn, 0)], np.asarray(r.cell, dtype=np.int64)[a])
        keep = keep | (mv & (t == cur) & (cur >= 0))
    return keep


def set_intent(agents: AgentState, agent_id, action, target, kind, tick: int) -> None:
    """**意図を立てる**(段 2c・値は ``engine.intent`` が決める)。

    Args:
        agent_id: 体(重複なし)。
        action: 保持する行為コード(購入/食事/並ぶ/会話/就寝)。
        target: 対象(``kind`` で意味が決まる: POI 索引 / 個体 id / セル)。
        kind: ``IntentKind``。
        tick: 立てた tick(``intent_since``)。
    """
    a = np.asarray(agent_id, dtype=np.int64)
    if a.size == 0:
        return
    with agents.writable():
        _require_thawed(agents)
        r = agents.registry
        r.intent_action[a] = np.asarray(action, dtype=np.int64).astype(np.int8)
        r.intent_target[a] = np.asarray(target, dtype=np.int64).astype(np.int32)
        r.intent_kind[a] = np.asarray(kind, dtype=np.int64).astype(np.int8)
        r.intent_since[a] = np.int32(int(tick))


def clear_intent(agents: AgentState, agent_id) -> None:
    """意図を消す(計画境界・割り込み・経路の行き止まり=段 2c)。結果コードは書かない。"""
    a = np.asarray(agent_id, dtype=np.int64)
    if a.size == 0:
        return
    with agents.writable():
        _require_thawed(agents)
        _clear_intent_fields(agents.registry, a)


def fail_intent(agents: AgentState, agent_id, code: ResultCode, tick: int) -> None:
    """意図を**失敗で終える**(段 2c の満了=``TOO_FAR``)。

    直前に試みた行為(B6 の主語)=意図の行為・結果コード=``code``・歩みを止める
    (``MOVING`` → ``IDLE``・目的ノードを外す)・意図を消す。
    """
    a = np.asarray(agent_id, dtype=np.int64)
    if a.size == 0:
        return
    with agents.writable():
        _require_thawed(agents)
        r = agents.registry
        r.last_action[a] = r.intent_action[a]
        r.last_result[a] = int(code)
        r.last_result_tick[a] = int(tick)
        moving = a[r.activity[a] == int(Activity.MOVING)]
        r.activity[moving] = int(Activity.IDLE)
        r.target_node[a] = -1
        _clear_intent_fields(r, a)


def relabel_intent_failure(agents: AgentState, agent_id, action=None) -> None:
    """既に書かれた失敗(移動の ``UNREACHABLE``)の**主語を意図の行為に**して意図を消す(段 2c)。

    ``action`` を渡すとその値を主語にする(意図を立てる前=移動が始められなかった体)。
    ``None`` なら保持中の ``intent_action``(経路の途中で行き止まり)。結果コードは動かさない。
    """
    a = np.asarray(agent_id, dtype=np.int64)
    if a.size == 0:
        return
    with agents.writable():
        _require_thawed(agents)
        r = agents.registry
        if action is None:
            r.last_action[a] = r.intent_action[a]
        else:
            r.last_action[a] = np.asarray(action, dtype=np.int64).astype(np.int8)
        _clear_intent_fields(r, a)
