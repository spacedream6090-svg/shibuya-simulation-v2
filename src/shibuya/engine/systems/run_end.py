"""engine.systems.run_end — ランの終わりの系(drain・close_final)(第 1 期 1-0)。

中身は HEAD ``ee3abc7`` の ``engine/run.py`` の ``run_day`` の同じ区間のまま。系の関数は ``(ctx, b)`` を受け取り、
区間の外から来る名前を箱から結ぶ前置き(局所の割り当ての表 ``local-assignment.json`` と同じ写像)と、
刻みの中の受け渡しを ``TickScratch`` へ書く後置きだけを足した(文は変えない・``box.`` は ``b.``)。
``engine.run`` で定義された補助(``_split_due`` など)は呼ぶ時に ``engine.run`` から引く(試験の差し替えが効く)。

逐次ループ宣言: 区間の中の宣言は HEAD のまま(各関数の中の注を見る)。ほかに新しい逐次ループは無い。
"""

from __future__ import annotations

import functools
from typing import Any

from shibuya.engine.llm_bridge import delta_think_ticks
from shibuya.engine.systems import state_io as _STATE_IO
from shibuya.llm.fleet import Deferred as FleetDeferred

__all__ = ["sys_drain", "sys_close_final"]


def sys_drain(ctx: Any, b: Any) -> None:
    """drain(HEAD run.py の同じ区間・文は変えない)。"""
    from shibuya.engine import run as _RUN
    _save_state = functools.partial(_STATE_IO.save_state, b)
    fleet_bridge = b.layers.fleet_bridge
    fleet_deferred = b.llm.fleet_deferred
    fleet_inflight = b.llm.fleet_inflight
    replay_inbox = b.llm.replay_inbox
    result = b.runstats.result
    t_end = b.cfg.t_end
    tick_seconds = b.cfg.tick_seconds
    total_ticks = b.cfg.total_ticks
    tpd = b.cfg.tpd
    _call_ref = _RUN._call_ref
    _pending_extra = _RUN._pending_extra
    _target_person = _RUN._target_person
    _stopped = t_end < total_ticks
    if _stopped and t_end % tpd != 0:
        _save_state(t_end, finished=False, closed=False)

    # ---- 艦隊の残りを吸い切る(**捨てない**)。テープを閉じる前に置く ----
    # 10d: 止めたランは吸わない(出したが返っていない呼は状態に書いた=再開のランが出し直す)
    if fleet_bridge is not None and _stopped:
        fleet_bridge.close()
    elif fleet_bridge is not None:
        n_late = 0
        # ``now_tick=total_ticks``= ラン終端(最後の刻みの 1 つ先)。再生側はこの値の項目を
        # 「刻みのループ中には届かなかった」として同じ位置で処理する(D-58)。
        for res in fleet_bridge.drain(now_tick=total_ticks):
            fleet_inflight.pop(str(res.call.call_id if isinstance(res, FleetDeferred) else res.call_id), None)
            if isinstance(res, FleetDeferred):
                fleet_deferred.append(
                    (int(res.call.agent_id), int(res.call.condition),
                     int(res.call.wake_class), int(res.call.wake_since))
                )
                continue
            n_late += 1
            b.llm.pending.append((
                res.tick + delta_think_ticks(res.lane, tick_seconds), res.wake_class,
                res.agent_id, res.condition, res.text, res.action_code,
                _target_person(res.target), *_pending_extra(res), *_call_ref(res),
            ))
        result.fleet_drained_at_end = n_late
        # ラン終端でも答えが返らなかった呼(**次ランへ持ち越す**の監査点。0 が正常)
        result.fleet_unanswered_at_end = len(fleet_deferred)
        fleet_bridge.close()
    elif replay_inbox and not _stopped:
        # ---- 再生の終端処理(D-58): 刻みのループ中に届かなかった分=本番の drain 相当 ----
        n_late = 0
        for t in sorted(replay_inbox):  # 逐次ループ宣言: 残件数ぶん(通常 0)
            for is_deferred, item in replay_inbox[t]:
                if is_deferred:
                    fleet_deferred.append(item)
                    continue
                n_late += 1
                b.llm.pending.append((
                    item.t_apply, item.wake_class, item.agent_id, item.condition,
                    item.text, item.action_code, _target_person(item.target),
                    *_pending_extra(item), *_call_ref(item),
                ))
        replay_inbox.clear()
        result.fleet_drained_at_end = n_late
        result.fleet_unanswered_at_end = len(fleet_deferred)


def sys_close_final(ctx: Any, b: Any) -> None:
    """close_final(E1・HEAD run.py:4551-4592): テープを閉じる・世界過程の最後の日の締め(鉄道の最後の便を流す)・
    最後の日の台帳の締め・締めの後の 2 本のハッシュ・日の記録・最後の状態の書き出し(文は変えない)。"""
    L, cfg, rs = b.layers, b.cfg, b.runstats
    bridge, runner, ledger = L.bridge, L.runner, L.ledger
    result = rs.result
    _stopped = cfg.stopped
    total_ticks, sim_days, checkpoint_every, t_end, tpd, state_out = (
        cfg.total_ticks, cfg.sim_days, cfg.checkpoint_every, cfg.t_end, cfg.tpd, cfg.state_out)
    _ledger_close = functools.partial(_STATE_IO.ledger_close, b)
    _eod_hashes = functools.partial(_STATE_IO.eod_hashes, b)
    _day_record = functools.partial(_STATE_IO.day_record, b)
    _save_state = functools.partial(_STATE_IO.save_state, b)
    bridge.close()
    result.runner = runner  # type: ignore[attr-defined]
    # 第 1 期 1-3: 出来事の記録も ``runner`` と同じく後付けの属性で渡すだけ(RunResult の欄は増やさない=既存の出力は不変)
    result.event_log = L.events  # type: ignore[attr-defined]
    # 第 1 期 1-8 J0: 候補の口の層(腕 port のランだけ・既定 None)も同じ形で渡す(manifest の decision_port が読む)
    result.decision_layer = L.decision  # type: ignore[attr-defined]
    # 第 1 期 1-8b: 発話の口(腕 on のランだけ・既定 None)も同じ形で渡す(manifest の speech_port が読む)
    result.speech_layer = L.speech  # type: ignore[attr-defined]
    # 第 2 期 2-2 段 11a: 近接の層(腕 distance のランだけ・既定 None)も同じ形で渡す(manifest の proximity が読む)
    result.proximity_layer = L.proximity  # type: ignore[attr-defined]
    # 〔第 3 期 3-3〕申込書の持ち主(申込書を渡したランだけ・既定 None)も同じ形で渡す(manifest の experiment が読む)
    result.experiment_layer = L.experiment  # type: ignore[attr-defined]
    # 〔第 3 期 3-5〕本人の体の層(どの腕でも組み立てが置く)も同じ形で渡す(manifest の body が読む)
    result.body_layer = L.body  # type: ignore[attr-defined]
    # 〔第 3 期 3-1〕暦 1a の影(腕 1a のランだけ・既定 None)も同じ形で渡す(manifest の calendar_shadow が読む)
    result.calendar_shadow_layer = L.calendar_shadow  # type: ignore[attr-defined]
    # AB7 の M1-M3(接地率・未定義率・上位未定義語)は §7 の台帳が持つ。``runner`` と同じく
    # **後付けの属性**として渡すだけ(RunResult の欄は増やさない=既存の出力は不変)。
    result.undefined_registry = bridge.undefined  # type: ignore[attr-defined]
    if runner is not None:
        # D-R2-6: ActualLog は O(t) が本質 → 保持窓を過ぎた生ログを日次集約行へ畳む
        if not _stopped:  # 10d: 止めたランは締めない(日の境目で止めたならループの中で締め済み)
            runner.end_of_day(max(0, total_ticks - 1))
        result.registry_hash = runner.registry_hash
        result.constitution_ok = runner.constitution_ok
        result.replay_date = runner.replay_date
        result.process_seconds = dict(runner.phase_seconds)
        result.process_counters = runner.counters()
        result.actual_log_rows = int(runner.log.n_appended)
        result.compliance_rate = float(runner.compliance().rate)
        result.salient_events = int(runner.salient.n_events)
        result.noticed = int(runner.salient.n_noticed)
        result.dispatches = int(runner.dispatch.n_dispatched)
        result.restocks = int(runner.shelf.n_role_actions + runner.shelf.n_fallback)
        result.deliveries = int(runner.delivery_inbound.n_runs)
        result.parcels = int(runner.last_mile.delivered.sum())
        result.bus_arrivals = int(runner.bus_taxi.n_arrivals)
        result.hotel_checkins = int(runner.hotel.n_checkin)
        result.waste_tonnes_per_day = float(runner.projected_waste_tonnes_per_day())
        _ws = runner.waste_sink_report()  # 第304 Q135 (a): 店だけの静的な帯+内訳 3 つ(報告だけ)
        if _ws is not None:
            result.waste_sink = dict(_ws)
            result.waste_band = (float(_ws["band_store_t"][0]), float(_ws["band_store_t"][1]))
    ledger_growth: tuple[dict[str, Any], dict[str, int]] = ({}, {})
    if ledger is not None:
        # 最後の日の締め(10d: 締めの中身は ``ledger_close``=途中の日と同じ・1 日のランは今のまま)
        ledger_growth = _ledger_close(sim_days - 1) if not _stopped else ledger.growth_parts()
    # ---- 10b 検収後 P2: 日の締め(runner.end_of_day・ledger.end_of_day)の**後**の 2 本(10d はこちらを使う) ----
    # 最後の checkpoint は締めの前なので、台帳の日番号・当日の売れ行き・センサスの項が違う。final も checkpoint の
    # 位置も変えない(読むだけ・manifest の ``state_hashes_end_of_day`` に別に出す)。
    if checkpoint_every and not _stopped:
        result.state_hashes_end_of_day = _eod_hashes()
    if not _stopped:
        _day_record((t_end - 1) // tpd)
        if state_out is not None:  # 10d: ランの最後の状態(finished: true=これへの再開は拒否)
            _save_state(total_ticks, finished=True, closed=True)
    rs.ledger_growth = ledger_growth  # report が読む(HEAD の局所 ``ledger_growth``)
