"""act.ops.talk — 割る段で ``engine/resolve.py`` を割った割り先(全ファイルの表 §4・名の表は
``tools/pkgmove/map.toml`` の割る行)。

中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の
方針は、主な割り先 ``act/apply.py`` に残した元の docstring を読むこと。
"""

from __future__ import annotations

from typing import Any, Final
import numpy as np
from shibuya.foundation.vocab.agent_codes import Activity, ResultCode
from shibuya.world.model.agent_table import (
    AgentState,
)
from shibuya.foundation.vocab.act_codes import TALK_OPEN_METERS
from shibuya.act.gate import _fail, _ok
from shibuya.foundation.write_guard import _require_thawed
from shibuya.act.ops.shop import balk_queue, release_indoor

__all__ = [
    "revert_conversation", "end_conversation", "set_conversing", "join_conversation",
]


def join_conversation(agents: AgentState, joiner, partner, tick: int) -> None:
    """**3 人目の参加**(C10 8a・D-93 (d)・``--conv-max-participants 3`` のランだけ)。

    会話の相手が会話中で ``PARTNER_BUSY`` になった体を、相手のセッションに入れる: 参加者を CONVERSING・
    ``talk_partner``=名指しした相手(**主相手**・相手の側の主相手は書き換えない)・直前の結果を ``OK`` に
    書き直す(失敗ではなかった)。セッション表の参加者は ``engine.conversation`` が持つ。
    """
    a = np.asarray(joiner, dtype=np.int64)
    if a.size == 0:
        return
    b = np.asarray(partner, dtype=np.int64)
    with agents.writable():
        _require_thawed(agents)
        r = agents.registry
        r.activity[a] = int(Activity.CONVERSING)
        r.talk_partner[a] = b.astype(np.int32)
        r.last_result[a] = int(ResultCode.OK)
        r.last_result_tick[a] = int(tick)


def revert_conversation(agents, agent_ids: np.ndarray) -> None:
    """招待が不応答/ゲート却下だったとき、resolve が CONVERSING にした招待側を IDLE へ戻す。

    行動契約書 §3「不応答は『無視された』イベント(呼を消費しない)」。層2レビュー(C3)の指摘:
    resolve が先に CONVERSING を書き、ConversationManager.invite が後で None を返すため
    セッション無しの CONVERSING が残っていた。世界状態への書き込みは resolve のみ(本関数はその内側)。
    """
    ids = np.asarray(agent_ids, dtype=np.int64)
    if ids.size == 0:
        return
    with agents.writable():
        r = agents.registry
        r.activity[ids] = int(Activity.IDLE)
        r.talk_partner[ids] = -1


def end_conversation(agents, agent_ids: np.ndarray) -> dict[str, int]:
    """〔11-03 M10〕終わったセッションの参加者を解放する(行動契約書 §3「終了はエンジン」)。

    活動が **CONVERSING の参加者だけ** IDLE に戻し、ほかの活動(会話の番に選んだ移動・休み・待機・在店・就寝・IDLE)は
    変えない。相手の欄 ``talk_partner`` は全員 −1 に戻す。旧道(腕 legacy)は ``revert_conversation`` で全員を IDLE に
    していた(会話の番で歩き出した体が道の途中で止まる・寝た体や買った体も IDLE になる)。世界状態への書き込みは
    resolve のみ(本関数はその内側)。

    Returns:
        戻さなかった体の数(活動の名 → 数・計器 ``n_conversation_end_kept_activity``)。
    """
    ids = np.asarray(agent_ids, dtype=np.int64)
    if ids.size == 0:
        return {}
    with agents.writable():
        r = agents.registry
        act = np.asarray(r.activity[ids], dtype=np.int64)
        talking = act == int(Activity.CONVERSING)
        r.activity[ids[talking]] = int(Activity.IDLE)
        r.talk_partner[ids] = -1
    kept, n = np.unique(act[~talking], return_counts=True)
    return {Activity(int(k)).name: int(c) for k, c in zip(kept.tolist(), n.tolist())}


def set_conversing(agents: AgentState, inviters, invitees) -> None:
    """会話成立時に**両側**を CONVERSING にする(C6・09-09)。

    C3/C4 は招待側だけを CONVERSING にしていた(被招待側の離脱をセルで検出する回避策)。
    C6 で被招待側が**自分の呼で承諾する**ようになったので、成立した時点で両側を
    セッション参加状態にする(行動契約書 §3「終了はエンジン」=両側の解放も
    ``engine.run`` の ``conv.step`` が行う)。世界状態への書き込みは resolve のみ。
    """
    a = np.asarray(inviters, dtype=np.int64)
    b = np.asarray(invitees, dtype=np.int64)
    if a.size == 0:
        return
    with agents.writable():
        _require_thawed(agents)
        r = agents.registry
        r.activity[a] = int(Activity.CONVERSING)
        r.activity[b] = int(Activity.CONVERSING)
        r.talk_partner[a] = b.astype(np.int32)
        r.talk_partner[b] = a.astype(np.int32)


#: 声をかけられない相手の状態(C6・09-09)。
#: **会話中**=行動契約書 §2.1 の失敗「相手が会話中」(``PARTNER_BUSY``)。
#: **就寝中**=声をかけても応答できない(起床(ii) の被招待で起こす対象にしない)。
#: C3 は「相手が **IDLE** であること」を要求していたが、それだと移動中・待機中・
#: 買い物中の相手に声をかけられず、C6 の 1 日ランで会話が 1 件も成立しなかった
#: (**expedient**: 「話しかけられる状態」の正典は無い。ablation 対象)。
_UNADDRESSABLE: Final[tuple[int, ...]] = (int(Activity.CONVERSING), int(Activity.SLEEPING))


def talk_within_reach(agents, a, b, *, by_distance: bool, rule: Any = None) -> np.ndarray:
    """会話が届くか(**C9b G7**)。``by_distance=False`` は現行の「同一セル代理」。

    ``True`` のときは同一セルに加えて ``距離 ≤ TALK_OPEN_METERS``(2 m)を課す
    (行動契約書 §3 開始ゲート「同一セル ∧ 距離≦d_talk」の後半を**実距離で**満たす)。
    同一セルを残すのは層(UG/GL/DECK)を跨いだ 2 m を成立させないため。

    〔第 2 期 2-2 段 11a〕``rule``(``engine.proximity.ProximityRule``・腕 ``--proximity distance``)を渡すと、同じセルの
    条件を外し「舞台の中・同じ層・距離 ≤ d、または同じ B5 の単位」で見る(``by_distance`` より強い)。``None``(既定)は
    今のまま。

    逐次ループ宣言(P4): なし。
    """
    if rule is not None and rule.is_distance:
        return rule.reach(agents, a, b)
    r = agents.registry
    ca = np.asarray(r.cell, dtype=np.int64)[a]
    cb = np.asarray(r.cell, dtype=np.int64)[b]
    ok = (ca == cb) & (ca >= 0)
    if not by_distance:
        return ok
    xy = np.asarray(r.xy, dtype=np.float64)
    d = xy[a] - xy[b]
    return ok & (np.sqrt((d * d).sum(axis=-1)) <= TALK_OPEN_METERS)


def _apply_talk(agents, world, aid, tgt, tick, out, schedule) -> None:
    """会話: 同一セル・相手が応答可能・自分でない → 招待成立(成否は被招待の呼が決める)。

    **C9b G7**: ``out.talk_by_distance`` が真のランでは「同一セル」に ``≤2 m`` が加わる
    (離脱は ``TALK_LEAVE_METERS``=3 m・判定は ``engine.conversation.step``)。
    """
    r = agents.registry
    has = (tgt >= 0) & (tgt < agents.n) & (tgt != aid)
    partner = np.clip(tgt, 0, max(0, agents.n - 1))
    same_cell = has & talk_within_reach(
        agents, aid, partner, by_distance=out.talk_by_distance, rule=out.proximity
    )
    if out.talk_by_distance or out.proximity is not None:  # 第 2 期 2-2: 腕 distance も実距離の成立を数える
        out.n_talk_by_distance += int(np.count_nonzero(same_cell))
    pact = r.activity[partner]
    addressable = same_cell & ~np.isin(pact, _UNADDRESSABLE)
    idle = addressable
    _fail(agents, aid[~has], ResultCode.BAD_TARGET, tick, out)
    _fail(agents, aid[has & ~same_cell], ResultCode.PARTNER_GONE, tick, out)
    _fail(agents, aid[same_cell & ~addressable], ResultCode.PARTNER_BUSY, tick, out)
    win = np.flatnonzero(idle)
    if win.size == 0:
        return
    speakers = aid[win]
    r.activity[speakers] = int(Activity.CONVERSING)
    r.talk_partner[speakers] = partner[win].astype(np.int32)
    out.n_conversations += int(win.size)
    _ok(agents, speakers, tick, out)


def _apply_leave(agents, world, aid, tgt, tick, out, schedule) -> None:
    """退去: **所属解除**(行動契約書 §2.1「会話・待ち行列・施設からの所属解除。会話は CLOSING を経て
    閉じる」・**失敗しない**)。

    9a(D-112 ④・欠陥の修正): 第263 まで IDLE 化と会話相手の解除だけで所属が残っていた。いまは
    在店(``poi_ref``)→ ``release_indoor``・待ち行列(``queue_poi``)→ ``balk_queue``・会話中 →
    ``out.leave_conversing`` に控え、``engine.run`` が会話マネージャの終了経路(``close_now`` 理由
    「退去」→ CLOSING → TERMINAL)で閉じる。「帰る」の意味は持たない(域外へは出ない)。
    逐次ループ宣言(P4): なし(ベクトル処理)。
    """
    r = agents.registry
    if aid.size == 0:
        return
    indoor = aid[r.poi_ref[aid] >= 0]
    if indoor.size:
        release_indoor(agents, indoor)
    queued = aid[r.queue_poi[aid] >= 0]
    if queued.size:
        balk_queue(agents, queued, int(tick))  # 結果は下の _ok で OK に戻す(失敗しない行動)
    talking = aid[r.activity[aid] == int(Activity.CONVERSING)]
    if talking.size:
        out.leave_conversing.append(np.asarray(talking, dtype=np.int64).copy())
    out.n_leave += int(aid.size)
    out.n_leave_indoor += int(indoor.size)
    out.n_leave_queue += int(queued.size)
    out.n_leave_conversing += int(talking.size)
    r.activity[aid] = int(Activity.IDLE)
    r.talk_partner[aid] = -1
    _ok(agents, aid, tick, out)
