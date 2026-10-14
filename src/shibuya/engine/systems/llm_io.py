"""engine.systems.llm_io — LLM の往復の口(会話ターンの発話・艦隊/再生の到着の受け取り)と系 llm_receive(第 1 期 1-0)。

HEAD ``ee3abc7`` の ``run_day`` の入れ子の関数 ``_utter``・``_receive_arrivals`` を、箱を受け取る関数にしたもの(中身は同じ)。

- ``utter``: 会話ターンの発話 1 回(``conv.utterance``)・記憶の会話の行と要旨・店の記憶の口コミ(``llm_receive`` と
  ``decide`` の両方から呼ぶ=草案 §3-3 の 7)。
- ``receive_arrivals``: ④′ 艦隊(と再生の代役)の到着を受け取る(10a・A9)。届いた応答は ``max(t_apply, floor)`` で
  ``LlmIo.pending`` へ入る。
- ``sys_llm_receive``: 系。``response_delay=1`` は ``perceive_prepare`` の後(下限 ``tick``)・``2`` は ``wake_sources`` の後
  (下限 ``tick + 1``)に進行役が置く(HEAD は位置 A で ``0`` を入れ、位置 B で ``2`` のときだけ受け取る=同じ値)。

逐次ループ宣言: 到着の件数ぶん(HEAD と同じ・本番の poll と同じ件数)。
"""

from __future__ import annotations

import time
from typing import Any

from shibuya.agents.state import WakeCondition
from shibuya.engine.llm_bridge import delta_think_ticks
from shibuya.engine.wom import hear as wom_hear
from shibuya.llm.fleet import Deferred as FleetDeferred

__all__ = ["utter", "receive_arrivals", "sys_llm_receive"]


def utter(b: Any, agent_id: int, t_now: int, action: Any, comment: str, reason: str = "",
          parse: Any = None, call_id: str = "") -> None:
    """会話ターンの発話 1 回(``conv.utterance``)。6a: 記憶の会話の行と要旨(on のときだけ)。

    6b(第294 Q57 暫定): 要旨の源=ひと言が空/「なし」なら理由欄の先頭 40 字(語彙 v3)。
    7b(D-120 N3 (a)): 店の記憶 on のランだけ、発話(``wom_source``: 既定=ひと言だけ・旧=v3 で理由+対象)から店名と評価語を
    抽出し、**宛先**(会話の相手=``talk_partner``・セッションの参加者)の店の行へ伝聞として書く。
    〔第 1 期 1-8b〕腕 ``--speech-port on`` のランだけ(``layers.speech`` がある)、ひと言を発話の口に通す
    (``engine.speech.layer.speak_turn``=出来事ログに 1 回・相手の次の入力・口コミの抽出は口の (c))。``call_id`` は
    その会話の番の呼び出しの id(発話の出来事の原因)。既定の腕では ``call_id`` を読まない=今の道のまま。
    """
    agents, conv, mem_layer, wom_ex = b.soa.agents, b.layers.conv, b.layers.mem_layer, b.layers.wom
    speech = b.layers.speech  # 1-8b: 腕 on のランだけ(既定 None=今の道)
    vocab_version, store_wom_on = b.cfg.vocab_version, b.cfg.store_wom_on
    partner_before = (int(agents.registry.talk_partner[int(agent_id)])
                      if (wom_ex is not None or speech is not None) else -1)
    s = conv.utterance(agent_id, t_now, action=action, comment=comment)
    if mem_layer is not None:
        mem_layer.note_utterance(agents, int(agent_id), int(t_now), s, comment, reason)
    if speech is not None:
        from shibuya.engine.speech.layer import speak_turn

        speak_turn(b, speech, int(agent_id), int(t_now), s, comment, reason, parse, call_id, partner_before)
        return
    if wom_ex is not None and s is not None:
        tgt = getattr(parse, "target", None)
        text = wom_ex.utterance_text(
            vocab_version,
            comment=str(getattr(parse, "raw_comment", "") or comment or ""),
            reason=str(getattr(parse, "raw_reason", "") or reason or ""),
            target=str(getattr(tgt, "raw", "") or ""),
        )
        ex = wom_ex.extract(text, int(agents.registry.cell[int(agent_id)]))
        wom_ex.observe(ex)
        others = [int(p) for p in s.participants if int(p) != int(agent_id)]
        listener = partner_before if partner_before in others else (others[0] if others else -1)
        if store_wom_on:  # 7c の腕: 口コミ off=抽出は数えるが転写しない
            wom_hear(mem_layer.store, agents, int(t_now), listener, ex)


def receive_arrivals(b: Any, tick: int, floor: int) -> int:
    """④′ 艦隊(と再生の代役)の到着を受け取る(10a・A9)。返り値=書式エラーの件数。

    届いた応答は ``max(t_apply, floor)`` で ``pending`` へ入る。``response_delay=1``(既定)は①の直前で
    ``floor=tick``(=発射 +1 刻みの①で反映)、``2`` は旧の位置(②〜会話ターン起床の後)で
    ``floor=tick + 1``(=+2 刻み)。mock(``fleet_bridge is None`` かつ ``replay_inbox`` が空)は何もしない。
    """
    from shibuya.engine import run as _RUN

    _target_person, _pending_extra, _call_ref = _RUN._target_person, _RUN._pending_extra, _RUN._call_ref
    io = b.llm
    fleet_bridge, conv = b.layers.fleet_bridge, b.layers.conv
    replay_inbox, fleet_deferred, fleet_waiting, fleet_inflight = (io.replay_inbox, io.fleet_deferred,
                                                                    io.fleet_waiting, io.fleet_inflight)
    phase = b.runstats.phase
    fleet_wait_s, tick_seconds = b.cfg.fleet_wait_s, b.cfg.tick_seconds
    n_err = 0
    if fleet_bridge is None and replay_inbox:
        # ---- ④′-r 再生モードの「到着」(D-58)。**艦隊経路と同じ位置・同じ扱い** ----
        # 逐次ループ宣言: この刻みに届く件数ぶん(本番の poll と同じ件数)。
        t0 = time.perf_counter()
        for is_deferred, item in replay_inbox.pop(tick, ()):
            if is_deferred:
                fleet_deferred.append(item)
                continue
            res = item
            fleet_waiting.discard(int(res.agent_id))
            io.pending.append((
                max(res.t_apply, floor), res.wake_class, res.agent_id,
                res.condition, res.text, res.action_code, _target_person(res.target),
                *_pending_extra(res), *_call_ref(res),
            ))
            if not res.format_ok:
                n_err += 1
            if conv is not None and res.condition == int(WakeCondition.CONVERSATION_TURN):
                utter(b, res.agent_id, tick, res.parse.action, res.parse.comment,
                      res.parse.reason, res.parse, call_id=_call_ref(res)[1])
        phase["llm"] += time.perf_counter() - t0
    if fleet_bridge is not None:
        t0 = time.perf_counter()
        if fleet_wait_s > 0.0 and fleet_bridge.client.outstanding:
            fleet_bridge.client.wait_idle(timeout=fleet_wait_s)
            phase["fleet_wait"] += time.perf_counter() - t0
            t0 = time.perf_counter()
        for res in fleet_bridge.poll(now_tick=tick):
            fleet_inflight.pop(str(res.call.call_id if isinstance(res, FleetDeferred) else res.call_id), None)
            if isinstance(res, FleetDeferred):
                fleet_deferred.append(
                    (
                        int(res.call.agent_id),
                        int(res.call.condition),
                        int(res.call.wake_class),
                        int(res.call.wake_since),
                    )
                )
                continue
            fleet_waiting.discard(int(res.agent_id))
            # t_apply = 起床 + δ_perc + δ_think(§2.4)。到着が遅れたぶんは
            # **破棄せず**この刻み以降へ(締切超過=繰り延べアービタの趣旨)。
            t_apply = res.tick + delta_think_ticks(res.lane, tick_seconds)
            io.pending.append((
                max(t_apply, floor), res.wake_class, res.agent_id,
                res.condition, res.text, res.action_code, _target_person(res.target),
                *_pending_extra(res), *_call_ref(res),
            ))
            if not res.format_ok:
                n_err += 1
            if conv is not None and res.condition == int(WakeCondition.CONVERSATION_TURN):
                utter(b, res.agent_id, tick, res.parse.action, res.parse.comment,
                      res.parse.reason, res.parse, call_id=_call_ref(res)[1])
        phase["llm"] += time.perf_counter() - t0
    return n_err


def sys_llm_receive(ctx: Any, b: Any) -> None:
    """系 llm_receive(L5・L11 前半): 艦隊/再生の到着を受け取り、書式エラーの件数を scratch に置く。"""
    tick = ctx.T
    floor = tick if b.cfg.response_delay == 1 else tick + 1
    b.scratch.n_parse_errors_fleet = receive_arrivals(b, tick, floor)
