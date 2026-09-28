"""engine.intent — **意図の保持**(段 2c・D-112 ①・D-114 案 A・第288)。

正典: ``docs/design/v2-intent-chooser-implementation-agenda.md`` §3(段 2c)。

購入/食事/並ぶ/会話/就寝の対象が**現在セルに無く解決できる**とき(名指しの店が見えている・カテゴリ
の店が近傍にある・会話の相手が別セル・寝床=自宅が別セル)、エンジンは行為を「意図」
(SoA ``intent_action``/``intent_target``/``intent_kind``/``intent_since``)に保存し、**目的地つき移動**
(活動層 ``activity_kind=MOVE_TO``・``until_kind=ARRIVAL``)を始める。歩いている間は場所の変化
(``CELL_BLOCK``)で起こさない。着いたら **LLM を呼ばず**エンジンが意図の行為を実行する(System 1・
呼数 0)。乗車の意図(``board_line``・D-51)・就寝の意図(``sleep_pending``・D-62)と同じ
「判断 1 回・実行は世界」の形。

1 tick の流れ(``engine.run`` の結線)
1. ① 応答の適用(Phase A の LLM 分): ``commit.intents_from_responses(..., intent_hold=本層)`` が
   セル外の対象の行を**移動**に変え、元の行為を :meth:`IntentLayer.propose` へ渡す。
2. ② 起床の絞り込み: :meth:`IntentLayer.suppress_wakes` が意図を持つ体の ``CELL_BLOCK`` と
   ``ACTIVITY_EXPIRY``(着いた=到着満了)を落とす(件数を数える)。
3. ⑤ Phase A の合流: :meth:`IntentLayer.arrival_intents` が**着いた体**(``IDLE``・在圏・対象のセルに
   居る)の意図の行為を ``IntentBatch`` にする(読むだけ)。この tick に適用される応答が意図を
   **上書きする**行為(世界に触れる行為・行き先の変わる移動)なら含めない(「superseded」)。
   **保つ**行為(なし・待機・行き先が同じ移動=親決定 Q20)なら意図はそのまま: 着いた体はその応答の
   行を LLM の intent から外して意図を実行し、歩いている体はその応答を適用したうえで歩き続ける
   (``resolve._apply_wait`` は意図を持って歩いている体を止めない)。
4. ⑦ Phase C: ``resolve.apply`` が意図を上書きする行為を適用した体の意図を消す(新しい応答・
   実行した意図・落選)。成否は ``last_result``。
5. Phase C の後(活動層の ``after_resolve``/``settle_events`` の後): :meth:`IntentLayer.after_apply` が
   (i) 実行した意図の結果を数え、LLM が言っていた活動(文・「まで」)を**実行の tick から**戻す
   (失敗∧活動なし → 次 tick 満了=失敗即時の規則はそのまま)(ii) 提案の移動が始まった体に意図を立て、
   活動を目的地つき移動(到着まで)にする(始まらなかった体=経路なしは ``UNREACHABLE`` の主語を
   元の行為に書き換える)(iii) 意図を持つ体を掃除する: 計画境界(域外へ出た=DEPART・就寝の実行/
   意図=SLEEP)で捨てる・歩いて ``INTENT_MAX_TICKS`` を超えたら ``TOO_FAR``・行き止まり
   (``UNREACHABLE``)・それ以外で歩みが止まった(会話の承諾など)は捨てる。

値を決めるのは本モジュール・世界への書き込みは ``engine.resolve``(``set_intent`` / ``clear_intent`` /
``fail_intent`` / ``relabel_intent_failure`` / ``set_activity_until``)と活動層(``force_arrival`` /
``after_resolve``)だけ(運用設計書 §2.2 Phase C の単一書き手)。

Python 側の状態 = 意図を持つ体の**活動の控え**(``ActivityPayload``・着いて実行した後に戻す)。
体数ぶんの配列は持たない(意図を持つ体の数ぶんの辞書=高々体数・日をまたいで伸びない)。
``state_hash`` で checkpoint に混ぜる(活動層のハッシュと一緒)。

逐次ループ宣言(P4)
1. :meth:`IntentLayer.propose`: この tick に意図にした**応答の数**ぶん(≤ 1 tick の呼数)。
2. :meth:`IntentLayer.after_apply`: 実行した意図・提案の数ぶん(≤ 1 tick の呼数+着いた体の数)。
   掃除は配列演算(意図を持つ体の集合に対するマスク)。
3. :meth:`IntentLayer.state_hash`: 意図を持つ体の数ぶん(checkpoint のときだけ)。

expedient(宣言・アジェンダ §3)
- ``INTENT_MAX_TICKS = 60``(感度腕 30/120・``--intent-max-ticks``)。超えたら ``TOO_FAR``(歩みを
  止めて次 tick に満了=考え直す)。
- 「着いた」= ``IDLE``・在圏・就寝の意図なし・(店/寝床は)対象のセルに居る。会話の相手は着いた時点の
  相手の位置を見る(同じセルでなければ ``PARTNER_GONE``=``resolve._apply_talk`` の判定のまま)。
- 着いて実行する行為の対象はプロポーズ時に選んだ店(カテゴリで選んだ店も**同じ店**=着いてから
  セル内の別の店に選び直さない)。
- **親決定 Q20**: 「なし」「待機」と行き先が同じ移動は意図を保つ(「新しい行為が無い」)。保った体の
  活動は目的地つき移動(到着まで)に戻し、着いた後に戻す活動は**意図を立てたときの応答の活動**のまま
  (途中の「なし」の活動欄は使わない=宣言)。
- **親決定 Q21**: 名指しの店は意図を立てる時点で営業中・(購入は)在庫を見る(2a の候補と同じ)。閉店なら
  歩かずに ``CLOSED`` を即時に返す(``engine.poi_target``)。到着時の ``CLOSED`` は途中で閉店した場合だけ。
- **親決定 Q22**: 計画就寝の意図(``sleep_pending``)が立っている体には寝床の意図を立てない(排他)。
- **親決定 Q23**: 会話の相手の行き先は意図を立てた時点の相手のセル(追わない)。
- 実行の優先度キーの ``t_notice`` は tick 開始(自発=C0)。同じ店に来た LLM 由来の買い手より先。
- ``TOO_FAR`` の結果文言「遠すぎて時間切れ」(``agents.state.RESULT_TEXT``)。
- **親決定 Q19**: 乗車の意図(``board_line``・D-51)は別経路のまま(統合は D-122 S1=到達の時間予算の回)。
"""

from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any, Final, Mapping, Sequence

import numpy as np

from shibuya.agents.state import (
    INTENT_NONE,
    Activity,
    IntentKind,
    ResultCode,
    WakeCondition,
)
from shibuya.engine import commit as C
from shibuya.engine import resolve as R
from shibuya.engine.activity import ActivityPayload
from shibuya.llm.contract import NO_TARGET, UNTIL_DEFAULT_MINUTES, UntilKind

__all__ = [
    "INTENT_MAX_TICKS",
    "INTENT_MAX_TICKS_ARMS",
    "INTENT_ACTIONS",
    "IntentLayer",
    "intent_summary",
]

#: 意図の上限[tick](アジェンダ §3-4・宣言・expedient・感度腕 30/120)。歩いてこれを超えたら ``TOO_FAR``。
INTENT_MAX_TICKS: Final[int] = 60
#: 感度腕(``--intent-max-ticks``)。
INTENT_MAX_TICKS_ARMS: Final[tuple[int, ...]] = (30, 60, 120)
#: 意図にできる行為(購入/食事/並ぶ/会話/就寝)。
INTENT_ACTIONS: Final[tuple[int, ...]] = (C.ACT_BUY, C.ACT_EAT, C.ACT_QUEUE, C.ACT_TALK, C.ACT_SLEEP)
#: 行為コード → manifest の鍵(語彙 v3 の語)。
_ACTION_KEY: Final[Mapping[int, str]] = {
    C.ACT_BUY: "購入", C.ACT_EAT: "食事", C.ACT_QUEUE: "並ぶ", C.ACT_TALK: "会話",
    C.ACT_SLEEP: "就寝",
}
_KIND_KEY: Final[Mapping[int, str]] = {int(k): k.name.lower() for k in IntentKind}
#: 着いた後に戻す活動が無い(応答に活動欄が無かった)体の既定(活動なし・既定 60 分)。
_DEFAULT_PAYLOAD: Final[ActivityPayload] = ActivityPayload(
    text=NO_TARGET, until_kind=int(UntilKind.DEFAULT), until_value=UNTIL_DEFAULT_MINUTES,
    wander=False,
)
_POI_KINDS: Final[tuple[int, ...]] = (int(IntentKind.POI_NAMED), int(IntentKind.POI_CATEGORY))


class IntentLayer:
    """意図の保持(``engine.run`` が活動層と一緒に作る=語彙 v3・``--activity on``・``candidates``)。

    Args:
        n_agents: 体数。
        world: 世界(POI のセルを読む)。
        max_ticks: 意図の上限[tick](``INTENT_MAX_TICKS``)。
    """

    def __init__(self, n_agents: int, world: Any, *, max_ticks: int = INTENT_MAX_TICKS) -> None:
        if int(max_ticks) < 1:
            raise ValueError(f"intent_max_ticks は 1 以上(いま {max_ticks})")
        self.n = int(n_agents)
        self.world = world
        self.max_ticks = int(max_ticks)
        self._poi_cell = np.asarray(world.pois.cell, dtype=np.int64)
        #: この tick の提案(体 → (行為, 対象, 種類, 行き先セル))。``after_apply`` で消費する。
        self._proposals: dict[int, tuple[int, int, int, int]] = {}
        #: この tick に着いて実行する体 → (行為, 種類, 立てた tick)。``after_apply`` で消費する。
        self._executing: dict[int, tuple[int, int, int]] = {}
        #: 意図を持つ体の**活動の控え**(着いて実行した後に戻す)。
        self._payload: dict[int, ActivityPayload] = {}
        #: この tick に「保つ」応答(なし・待機・同じ行き先の移動)を適用する歩いている体(Q20)。
        self._kept_walk: set[int] = set()
        self.stats: Counter = Counter()
        self.ticks_sum = 0
        self.ticks_n = 0

    # ------------------------------------------------------------------ ① 提案(commit から)
    def propose(
        self,
        agent_id: np.ndarray,
        action: np.ndarray,
        target: np.ndarray,
        kind: np.ndarray,
        dest: np.ndarray,
    ) -> None:
        """セル外の対象を意図にする**提案**(移動が始まった後に ``after_apply`` が立てる)。"""
        # 逐次ループ宣言1: 意図にした応答の数ぶん
        for a, c, t, k, d in zip(
            np.asarray(agent_id).tolist(), np.asarray(action).tolist(),
            np.asarray(target).tolist(), np.asarray(kind).tolist(), np.asarray(dest).tolist(),
        ):
            self._proposals[int(a)] = (int(c), int(t), int(k), int(d))
            self.stats["proposed"] += 1
            self.stats[f"proposed_by_kind:{_KIND_KEY.get(int(k), str(k))}"] += 1

    def note(self, key: str, n: int = 1) -> None:
        """提案の手前で落ちた件数などを数える(``commit`` から・例 ``bed_skipped_sleep_pending``)。"""
        if int(n):
            self.stats[str(key)] += int(n)

    # ------------------------------------------------------------------ ② 起床の絞り込み
    def suppress_wakes(
        self, agents: Any, tick: int, agent: np.ndarray, cond: np.ndarray, cls: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """意図を持つ体の ``CELL_BLOCK``(場所の変化)と ``ACTIVITY_EXPIRY``(到着満了)を落とす。"""
        if agent.size == 0:
            return agent, cond, cls
        a = np.asarray(agent, dtype=np.int64)
        hold = np.asarray(agents.registry.intent_action)[a] != INTENT_NONE
        if not bool(hold.any()):
            return agent, cond, cls
        c = np.asarray(cond, dtype=np.int64)
        cb = hold & (c == int(WakeCondition.CELL_BLOCK))
        ex = hold & (c == int(WakeCondition.ACTIVITY_EXPIRY))
        self.stats["cell_block_suppressed"] += int(np.count_nonzero(cb))
        self.stats["expiry_suppressed"] += int(np.count_nonzero(ex))
        keep = ~(cb | ex)
        return agent[keep], cond[keep], cls[keep]

    # ------------------------------------------------------------------ ⑤ 着いた体の実行
    def _at_dest(self, agents: Any, ids: np.ndarray) -> np.ndarray:
        """店/寝床の意図は対象のセルに居るか(会話の相手は常に真=相手の位置は実行時に見る)。"""
        r = agents.registry
        kind = np.asarray(r.intent_kind)[ids].astype(np.int64)
        tgt = np.asarray(r.intent_target)[ids].astype(np.int64)
        cell = np.asarray(r.cell)[ids].astype(np.int64)
        out = np.ones(ids.size, dtype=bool)
        poi = np.isin(kind, _POI_KINDS)
        if np.any(poi):
            safe = np.clip(tgt[poi], 0, max(0, self._poi_cell.size - 1))
            out[poi] = (tgt[poi] >= 0) & (self._poi_cell[safe] == cell[poi])
        bed = kind == int(IntentKind.BED)
        out[bed] = cell[bed] == tgt[bed]
        return out & (cell >= 0)

    def arrival_intents(
        self, agents: Any, space: Any, tick: int, llm: C.IntentBatch | None = None
    ) -> tuple[C.IntentBatch, C.IntentBatch]:
        """着いた体の意図の行為(Phase A のエンジン側 intent・**読むだけ**)と、合流する LLM の intent。

        Args:
            llm: この tick に適用する LLM 由来の intent(``commit.intents_from_responses`` の出力)。

        Returns:
            ``(着いた体の intent, LLM の intent)``。後者は「保つ」応答(なし・待機・同じ行き先の移動)を
            返した**着いた体**の行だけを外したもの(その体は意図を実行する)。意図を上書きする応答の
            体は着いていても実行しない(``superseded``・``resolve.apply`` が意図を消す)。
        """
        r = agents.registry
        llm = llm if llm is not None else C.IntentBatch.empty()
        self._kept_walk = set()
        ia = np.asarray(r.intent_action)
        hold = np.flatnonzero(ia != INTENT_NONE).astype(np.int64)
        if hold.size == 0:
            return C.IntentBatch.empty(), llm
        kept_rows = np.zeros(0, dtype=np.int64)
        if len(llm):
            la = np.asarray(llm.agent_id, dtype=np.int64)
            idx = np.flatnonzero(ia[la] != INTENT_NONE)
            if idx.size:
                code = np.asarray(llm.action_code, dtype=np.int64)[idx]
                kept = R.intent_kept_by(agents, self.world, la[idx], code,
                                        np.asarray(llm.target_id, dtype=np.int64)[idx])
                self.stats["dropped:superseded"] += int(np.count_nonzero(~kept))
                self.stats["kept:none_or_wait"] += int(np.count_nonzero(kept & (code != C.ACT_MOVE)))
                self.stats["kept:same_dest_move"] += int(np.count_nonzero(kept & (code == C.ACT_MOVE)))
                hold = hold[~np.isin(hold, la[idx[~kept]])]
                kept_rows = idx[kept]
        if hold.size == 0:
            return C.IntentBatch.empty(), llm
        eligible = (
            (np.asarray(r.activity)[hold] == int(Activity.IDLE))
            & (np.asarray(r.transit_state)[hold] == 0)
            & (np.asarray(r.sleep_pending)[hold] == 0)
        )
        ids = hold[eligible]
        if ids.size:
            ids = ids[self._at_dest(agents, ids)]
        if kept_rows.size:
            la = np.asarray(llm.agent_id, dtype=np.int64)
            due_kept = np.isin(la[kept_rows], ids)
            self._kept_walk = {int(a) for a in la[kept_rows[~due_kept]].tolist()}
            if bool(due_kept.any()):
                # 着いた体の「保つ」応答は外す(意図の行為を実行する=一体一件)
                keep = np.ones(len(llm), dtype=bool)
                keep[kept_rows[due_kept]] = False
                llm = llm.take(np.flatnonzero(keep))
                self.stats["kept:due_response_dropped"] += int(np.count_nonzero(due_kept))
        if ids.size == 0:
            return C.IntentBatch.empty(), llm
        act = np.asarray(r.intent_action)[ids].astype(np.int64)
        tgt = np.asarray(r.intent_target)[ids].astype(np.int64)
        kind = np.asarray(r.intent_kind)[ids].astype(np.int64)
        since = np.asarray(r.intent_since)[ids].astype(np.int64)
        res = np.full(ids.size, -1, dtype=np.int64)
        poi = np.isin(kind, _POI_KINDS)
        res[poi] = space.poi(tgt[poi])
        per = kind == int(IntentKind.PERSON)
        res[per] = space.partner(tgt[per])
        bed = kind == int(IntentKind.BED)
        res[bed] = space.sleep(tgt[bed])
        for a, c, k, s0 in zip(ids.tolist(), act.tolist(), kind.tolist(), since.tolist()):
            self._executing[int(a)] = (int(c), int(k), int(s0))
        self.stats["arrived"] += int(ids.size)
        batch = C.IntentBatch(
            agent_id=ids,
            action_code=act.astype(np.int8),
            target_id=tgt.astype(np.int32),
            resource_id=res.astype(np.int32),
            t_notice_ns=np.full(ids.size, C.tick_start_ns(int(tick)), dtype=np.int64),
        )
        return batch, llm

    # ------------------------------------------------------------------ Phase C の後
    def after_apply(
        self,
        agents: Any,
        tick: int,
        act_layer: Any,
        applied: tuple[Sequence[int], Sequence[int], Sequence[Any]] | None = None,
    ) -> None:
        """(i) 実行した意図の結果と活動の戻し (ii) 意図を立てる (iii) 掃除(``TOO_FAR`` を含む)。

        ``act_layer.after_resolve``/``settle_events`` の**後**に呼ぶ(提案の体の活動を目的地つき移動に
        上書きし、実行した体の活動を LLM の言った活動に戻すため)。
        """
        t = int(tick)
        r = agents.registry
        self._settle_executions(agents, t, act_layer)
        self._settle_kept(agents, t, act_layer)
        self._settle_proposals(agents, t, act_layer, applied)
        self._sweep(agents, t, act_layer)
        # 控えの掃除: 意図を持たない体の控えは捨てる
        if self._payload:
            ia = np.asarray(r.intent_action)
            for a in [a for a in self._payload if int(ia[a]) == INTENT_NONE]:
                del self._payload[a]

    def _settle_executions(self, agents: Any, t: int, act_layer: Any) -> None:
        if not self._executing:
            return
        r = agents.registry
        ids = np.fromiter(self._executing.keys(), dtype=np.int64, count=len(self._executing))
        codes = np.fromiter((v[0] for v in self._executing.values()), dtype=np.int64,
                            count=ids.size)
        since = np.fromiter((v[2] for v in self._executing.values()), dtype=np.int64,
                            count=ids.size)
        applied_now = np.asarray(r.last_result_tick)[ids] == t
        res = np.asarray(r.last_result)[ids].astype(np.int64)
        act = np.asarray(r.activity)[ids]
        for j in range(ids.size):  # 逐次ループ宣言2: 実行した意図の数ぶん
            key = _ACTION_KEY.get(int(codes[j]), str(int(codes[j])))
            if not bool(applied_now[j]):
                self.stats["exec_not_applied"] += 1
                continue
            if int(res[j]) == int(ResultCode.OK):
                if int(act[j]) == int(Activity.WAITING):
                    self.stats["done_queued"] += 1
                self.stats["done"] += 1
                self.stats[f"done_by_action:{key}"] += 1
            else:
                name = ResultCode(int(res[j])).name.lower()
                self.stats["failed"] += 1
                self.stats[f"failed:{name}"] += 1
            self.ticks_sum += int(t - since[j])
            self.ticks_n += 1
        if act_layer is not None:
            pls = [self._payload.get(int(a), _DEFAULT_PAYLOAD) for a in ids.tolist()]
            act_layer.after_resolve(agents, t, ids.tolist(), codes.tolist(), pls)
        for a in ids.tolist():
            self._payload.pop(int(a), None)
        self._executing.clear()

    def _settle_kept(self, agents: Any, t: int, act_layer: Any) -> None:
        """Q20: 「保つ」応答を適用した歩いている体の活動を目的地つき移動(到着まで)に戻す。"""
        if not self._kept_walk:
            return
        r = agents.registry
        ids = np.fromiter(sorted(self._kept_walk), dtype=np.int64, count=len(self._kept_walk))
        self._kept_walk = set()
        ids = ids[
            (np.asarray(r.intent_action)[ids] != INTENT_NONE)
            & (np.asarray(r.activity)[ids] == int(Activity.MOVING))
        ]
        if ids.size and act_layer is not None:
            act_layer.force_arrival(agents, ids, t, count=False)

    def _settle_proposals(
        self, agents: Any, t: int, act_layer: Any,
        applied: tuple[Sequence[int], Sequence[int], Sequence[Any]] | None,
    ) -> None:
        if not self._proposals:
            return
        r = agents.registry
        props = self._proposals
        self._proposals = {}
        ids = np.fromiter(props.keys(), dtype=np.int64, count=len(props))
        vals = list(props.values())
        action = np.fromiter((v[0] for v in vals), dtype=np.int64, count=ids.size)
        target = np.fromiter((v[1] for v in vals), dtype=np.int64, count=ids.size)
        kind = np.fromiter((v[2] for v in vals), dtype=np.int64, count=ids.size)
        started = (
            (np.asarray(r.last_result_tick)[ids] == t)
            & (np.asarray(r.last_result)[ids] == int(ResultCode.OK))
            & (np.asarray(r.last_action)[ids] == int(C.ACT_MOVE))
            & np.isin(np.asarray(r.activity)[ids], (int(Activity.MOVING), int(Activity.IDLE)))
            & (np.asarray(r.transit_state)[ids] == 0)
        )
        ok = ids[started]
        if ok.size:
            R.set_intent(agents, ok, action[started], target[started], kind[started], t)
            if act_layer is not None:
                act_layer.force_arrival(agents, ok, t)
            pmap: dict[int, Any] = {}
            if applied is not None:
                for a, _c, p in zip(*applied):
                    pmap[int(a)] = p
            for a in ok.tolist():
                p = pmap.get(int(a))
                self._payload[int(a)] = p if p is not None else _DEFAULT_PAYLOAD
            self.stats["set"] += int(ok.size)
            for c in action[started].tolist():
                self.stats[f"set_by_action:{_ACTION_KEY.get(int(c), str(c))}"] += 1
        bad = ids[~started]
        if bad.size:
            # 移動が始まらなかった(経路なし=UNREACHABLE・対象不正)=主語を元の行為に
            failed_now = (np.asarray(r.last_result_tick)[bad] == t) & (
                np.asarray(r.last_result)[bad] != int(ResultCode.OK)
            )
            fb = bad[failed_now]
            if fb.size:
                R.relabel_intent_failure(agents, fb, action[~started][failed_now])
                for code in np.asarray(r.last_result)[fb].tolist():
                    self.stats[f"set_failed:{ResultCode(int(code)).name.lower()}"] += 1
            self.stats["set_failed"] += int(bad.size)

    def _sweep(self, agents: Any, t: int, act_layer: Any) -> None:
        r = agents.registry
        hold = np.flatnonzero(np.asarray(r.intent_action) != INTENT_NONE).astype(np.int64)
        if hold.size == 0:
            return
        ts = np.asarray(r.transit_state)[hold]
        act = np.asarray(r.activity)[hold]
        sp = np.asarray(r.sleep_pending)[hold]
        depart = ts != 0
        sleep = ~depart & ((act == int(Activity.SLEEPING)) | (sp != 0))
        plan = depart | sleep
        moving = ~plan & (act == int(Activity.MOVING))
        since = np.asarray(r.intent_since)[hold].astype(np.int64)
        too_far = moving & ((t - since) > self.max_ticks)
        idle = ~plan & (act == int(Activity.IDLE))
        at_dest = np.zeros(hold.size, dtype=bool)
        if np.any(idle):
            at_dest[idle] = self._at_dest(agents, hold[idle])
        due = idle & at_dest
        stuck = (
            idle & ~at_dest
            & (np.asarray(r.last_result)[hold] == int(ResultCode.UNREACHABLE))
            & (np.asarray(r.last_result_tick)[hold] == t)
        )
        other = ~(plan | moving | due | stuck)
        if np.any(plan):
            R.clear_intent(agents, hold[plan])
            self.stats["dropped:plan_depart"] += int(np.count_nonzero(depart))
            self.stats["dropped:plan_sleep"] += int(np.count_nonzero(sleep))
        if np.any(too_far):
            ids = hold[too_far]
            self.ticks_sum += int((t - since[too_far]).sum())
            self.ticks_n += int(ids.size)
            R.fail_intent(agents, ids, ResultCode.TOO_FAR, t)
            if act_layer is not None:
                R.set_activity_until(agents, ids, t + 1)  # 考え直す(失敗即時の規則と同じ)
            self.stats["too_far"] += int(ids.size)
        if np.any(stuck):
            R.relabel_intent_failure(agents, hold[stuck])
            self.stats["dropped:unreachable_en_route"] += int(np.count_nonzero(stuck))
        if np.any(other):
            R.clear_intent(agents, hold[other])
            self.stats["dropped:interrupted"] += int(np.count_nonzero(other))

    # ------------------------------------------------------------------ 監査
    def state_hash(self) -> str:
        """活動の控え(体 id 順)→ sha256(checkpoint に活動層のハッシュと一緒に混ぜる)。"""
        h = hashlib.sha256()
        # 逐次ループ宣言3: 意図を持つ体の数ぶん
        for a in sorted(self._payload):
            p = self._payload[a]
            h.update(int(a).to_bytes(4, "little", signed=True))
            h.update(hashlib.sha256(str(p.text).encode("utf-8")).digest())
            h.update(int(p.until_kind).to_bytes(2, "little", signed=True))
            h.update(int(p.until_value).to_bytes(4, "little", signed=True))
            h.update(b"\x01" if p.wander else b"\x00")
        return h.hexdigest()

    def counters(self) -> dict[str, Any]:
        return intent_summary(self.stats, self.ticks_sum, self.ticks_n, self.max_ticks)


def intent_summary(stats: Mapping[str, int], ticks_sum: int, ticks_n: int,
                   max_ticks: int = INTENT_MAX_TICKS) -> dict[str, Any]:
    """計数 → manifest ``intent`` の形(アジェンダ §3-6)。"""
    def sub(prefix: str) -> dict[str, int]:
        return {
            k[len(prefix):]: int(v) for k, v in sorted(stats.items())
            if k.startswith(prefix) and int(v)
        }

    return {
        "max_ticks": int(max_ticks),
        "proposed": int(stats.get("proposed", 0)),
        "proposed_by_kind": sub("proposed_by_kind:"),
        "set": int(stats.get("set", 0)),
        "set_by_action": sub("set_by_action:"),
        "set_failed": int(stats.get("set_failed", 0)),
        "set_failed_by_result": sub("set_failed:"),
        "arrived": int(stats.get("arrived", 0)),
        "done": int(stats.get("done", 0)),
        "done_queued": int(stats.get("done_queued", 0)),
        "done_by_action": sub("done_by_action:"),
        "failed": int(stats.get("failed", 0)),
        "failed_by_result": sub("failed:"),
        "too_far": int(stats.get("too_far", 0)),
        "dropped": sub("dropped:"),
        # 親決定 Q20: 意図中の なし/待機・同じ行き先の移動(保持)と、着いた体のその応答を外した件数
        "kept": sub("kept:"),
        # 親決定 Q22: 計画就寝の意図が立っていて寝床の意図にしなかった件数
        "bed_skipped_sleep_pending": int(stats.get("bed_skipped_sleep_pending", 0)),
        "exec_not_applied": int(stats.get("exec_not_applied", 0)),
        "cell_block_suppressed": int(stats.get("cell_block_suppressed", 0)),
        "expiry_suppressed": int(stats.get("expiry_suppressed", 0)),
        # 意図を立ててから実行(成否を問わず)/ TOO_FAR までの平均 tick
        "mean_ticks": round(ticks_sum / ticks_n, 3) if ticks_n else 0.0,
    }
