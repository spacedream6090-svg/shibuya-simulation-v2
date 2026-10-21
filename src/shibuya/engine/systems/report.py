"""engine.systems.report — ランの結果の組み立て(R3・E2〜E4)(第 1 期 1-0・段 B)。

中身は HEAD ``ee3abc7`` の ``engine/run.py`` の ``run_day`` の同じ区間(``result.bridge_counters = …`` から
``return result`` の前まで)のまま。局所の名を箱から結ぶ前置きだけを足した(文は変えない・``box.runstats.`` は ``rs.``)。
読むだけ(``RunResult`` と ``RunStats`` の計画の就寝の数えに計画実行層の分を足す=HEAD と同じ)。

逐次ループ宣言: なし(ランの終わりに 1 回)。
"""

from __future__ import annotations

import time
from collections import Counter
from typing import Any

import numpy as np

from shibuya.agents.state import N_WAKE_CONDITIONS_ALL, Activity, WakeCondition
from shibuya.core.growth import check_growth
from shibuya.engine import growth_decl as GD
from shibuya.engine.calendar import WEATHER_SCHEME
from shibuya.core.rng import RNG_SCHEME
from shibuya.engine.poi_target import move_resolution_summary, resolution_summary
from shibuya.engine.processes.salient import ablation_name as _pnotice_ablation_name
from shibuya.perception.channels import BudgetMode
from shibuya.perception.renderer import P_SEE_ACTIVITY_KINDS
from shibuya.core.time_consts import SECONDS_PER_MINUTE

__all__ = ["report"]


def report(ctx: Any, b: Any) -> Any:
    """R3: ``RunResult`` の組み立て・成長の検査・在圏 journal の書き出し(HEAD run.py:4593-4965)。返り値=``RunResult``。"""
    from shibuya.engine.run import DIAG_RUN_COLUMNS, _action_usage, decision_layers_summary

    cfg, L, rs, fx = b.cfg, b.layers, b.runstats, b.fx
    agents, world = b.soa.agents, b.soa.world
    fleet_inflight = b.llm.fleet_inflight
    w17_substituted = b.day.w17_substituted
    _stopped = cfg.stopped
    activity_on = cfg.activity_on
    activity_region = cfg.activity_region
    area_source = cfg.area_source
    attendance_rate = cfg.attendance_rate
    attention_on = cfg.attention_on
    budget_mode_enum = cfg.budget_mode_enum
    chooser = cfg.chooser
    classical_habit_p = cfg.classical_habit_p
    classical_tau = cfg.classical_tau
    day_index = cfg.day_index
    derive_rule = cfg.derive_rule
    eatery = cfg.eatery
    energy_on = cfg.energy_on
    energy_rate = cfg.energy_rate
    exit_mode = cfg.exit_mode
    familiarity_k = cfg.familiarity_k
    familiarity_on = cfg.familiarity_on
    geometry = cfg.geometry
    home_meal = cfg.home_meal
    hunger_model = cfg.hunger_model
    hunger_words = cfg.hunger_words
    intent_max_ticks = cfg.intent_max_ticks
    intent_mode = cfg.intent_mode
    l4_scale = cfg.l4_scale
    meal_sleep_defer = cfg.meal_sleep_defer
    memory_n = cfg.memory_n
    memory_on = cfg.memory_on
    mock_move_target_p = cfg.mock_move_target_p
    mock_out_of_cell_target_p = cfg.mock_out_of_cell_target_p
    move_search_radius = cfg.move_search_radius
    n_agents = cfg.n_agents
    occupancy_path = cfg.occupancy_path
    outside_suppression = cfg.outside_suppression
    p_notice_ablation = cfg.p_notice_ablation
    p_notice_d50_scale = cfg.p_notice_d50_scale
    parent_run = cfg.parent_run
    plan_exec_on = cfg.plan_exec_on
    plan_sleep = cfg.plan_sleep
    policy = cfg.policy
    refractory_scale_norm = cfg.refractory_scale_norm
    response_delay = cfg.response_delay
    role_words = cfg.role_words
    run_id = cfg.run_id
    seat_area_eatery_m2 = cfg.seat_area_eatery_m2
    seat_area_retail_m2 = cfg.seat_area_retail_m2
    signage = cfg.signage
    signage_p_see = cfg.signage_p_see
    sim_days = cfg.sim_days
    sleep_suppression = cfg.sleep_suppression
    store_memory_on = cfg.store_memory_on
    store_recall_scope = cfg.store_recall_scope
    store_signage_on = cfg.store_signage_on
    store_wom_on = cfg.store_wom_on
    t_begin = cfg.t_begin
    t_end = cfg.t_end
    tick_seconds = cfg.tick_seconds
    vocab_version = cfg.vocab_version
    _fam_renderer = L.renderer
    act_layer = L.act_layer
    arbiter = L.arbiter
    bridge = L.bridge
    classical_policy = L.classical
    conv = L.conv
    energy_layer = L.energy
    fam_layer = L.fam_layer
    fleet_bridge = L.fleet_bridge
    intent_layer = L.intent_layer
    ledger = L.ledger
    mem_layer = L.mem_layer
    norm_meter = L.norm_meter
    poi_resolver = L.poi_resolver
    presence = L.presence
    rel_layer = L.rel_layer
    runner = L.runner
    wom_ex = L.wom
    awake_sum = rs.awake_sum
    awake_ticks = rs.awake_ticks
    calls_by_cond = rs.calls_by_cond
    daily_records = rs.daily_records
    day_heads = rs.day_heads
    diag_rows = rs.diag_rows
    frozen_sources_map = rs.frozen_sources_map
    intero_cross = rs.intero_cross
    layer_counts = rs.layer_counts
    leave_counts = rs.leave_counts
    ledger_growth = rs.ledger_growth
    occ_counts = rs.occ_counts
    occ_kind = rs.occ_kind
    occ_ticks = rs.occ_ticks
    occ_transit = rs.occ_transit
    per_action_total = rs.per_action_total
    phase = rs.phase
    result = rs.result
    sleep_counts = rs.sleep_tally
    state_files = rs.state_files
    talk_stats = rs.talk_stats
    calendar = fx.calendar
    fleet = fx.fleet
    perception = fx.perception
    renderer_obj = fx.renderer_obj
    schedule = fx.schedule
    start_check = fx.start_check
    walkable = fx.walkable

    result.bridge_counters = dict(bridge.counters())
    if fleet_bridge is not None:
        result.bridge_counters.update(fleet_bridge.counters())
        result.bridge_counters["fleet_reinjected"] = float(rs.n_fleet_reinjected)
        result.bridge_counters["fleet_resent"] = float(rs.n_fleet_resent)
        result.fleet_fields = dict(fleet.config.manifest_fields())
    elif rs.n_fleet_reinjected or rs.n_fleet_resent:
        # 再生が艦隊テープの繰り延べを再現したときだけ出す(D-58)。
        # mock ランは従来どおり ``fleet_*`` の欄を持たない(退化検査の約束)。
        result.bridge_counters["fleet_reinjected"] = float(rs.n_fleet_reinjected)
        result.bridge_counters["fleet_resent"] = float(rs.n_fleet_resent)
    result.conversation_counters = dict(conv.counters()) if conv is not None else {}
    if conv is not None:
        # 会話の相手の由来(行動契約書 §1-2 の対象スロットが効いているかの監査点)。
        result.conversation_counters["conv_target_named"] = int(talk_stats.get("talk_named", 0))
        result.conversation_counters["conv_fallback_same_batch"] = int(
            talk_stats.get("talk_fallback", 0)
        )
        result.conversation_counters["conv_target_absent"] = int(talk_stats.get("talk_absent", 0))
    if conv is not None:
        # 層2指摘の固定: 日末に CONVERSING の個体は活動セッションの参加者だけ(被招待側は C4 まで IDLE)
        result.conversation_counters["conversing_agents_end"] = int(
            np.count_nonzero(agents.registry.activity == int(Activity.CONVERSING))
        )
    result.renderer_counters = dict(perception.counters()) if perception is not None else {}
    # 10e(B0): 世界の資産(``world:``=騒音の地図)と世界過程(``process:``=W13・W12・影の点の W10・開いた影 W9)が
    # 読んだファイルの sha256 を同じ辞書に足す(manifest の設定の節。final・checkpoint には入らない)
    frozen_sources_map.update(
        {f"world:{k}": v for k, v in (getattr(world.assets, "asset_sources", {}) or {}).items()}
    )
    if runner is not None:
        frozen_sources_map.update(
            {f"process:{k}": v for k, v in (getattr(runner.assets, "asset_sources", {}) or {}).items()}
        )
        frozen_sources_map.update(
            {f"process:{k}": v for k, v in (getattr(runner.environment, "shadow_sources", {}) or {}).items()}
        )
    result.frozen_sources = frozen_sources_map
    # 10e(B6): 天気の規則と日ごとの記録
    result.weather = (
        runner.environment.weather_manifest() if runner is not None
        else {"scheme": WEATHER_SCHEME, "perturbed": False, "days": [], "warnings": []}
    )
    result.renderer_name = (
        "perception.Renderer" if perception is not None else type(renderer_obj).__name__
    )
    # 実際に描いた腕(注入レンダラなら**そちらの値**が正)。§3.2 ablation ① の同定欄。
    result.budget_mode = BudgetMode.parse(
        getattr(getattr(perception, "renderer", None), "budget_mode", budget_mode_enum)
        if perception is not None
        else budget_mode_enum
    ).value
    # D-99 (a): L4 呼数予算の腕(倍率は申告・``budget_per_tick`` は**実際に使った値**)。
    result.l4_scale = float(l4_scale)
    result.budget_per_tick = float(arbiter.budget)
    result.tick_seconds = int(tick_seconds)
    # ---- 10a: 暦の欄・応答の遅れ・日数(manifest の ``calendar``・``response_delay``・``sim_days``) ----
    result.calendar_fields = {**calendar.manifest_fields(sim_days), "start_check": list(start_check)}
    result.response_delay = int(response_delay)
    result.sim_days = int(sim_days)
    result.rng_scheme = RNG_SCHEME  # 10c・〔第330・RET〕counter だけ(記録)


    # ablation 第1陣 ②③⑥ の腕(manifest の同定欄)。⑥ は**実際に描いた側**が正。
    result.p_notice_ablation = _pnotice_ablation_name(
        runner.salient.ablation if runner is not None else p_notice_ablation
    )
    result.p_notice_d50_scale = (
        float(runner.salient.d50_scale) if runner is not None else float(p_notice_d50_scale)
    )
    result.refractory_scale = dict(refractory_scale_norm)
    result.signage = bool(
        getattr(getattr(perception, "renderer", None), "signage_enabled", signage)
        if perception is not None
        else signage
    )
    # D-59 (b): 注視ゲートも**実際に描いた側**が正(注入レンダラならそちらの値)。
    result.signage_p_see = float(
        getattr(getattr(perception, "renderer", None), "signage_p_see", signage_p_see)
        if perception is not None
        else signage_p_see
    )
    # AB7: 実際に描いた腕(注入レンダラなら**そちらの値**が正)。
    result.role_words = bool(
        getattr(getattr(perception, "renderer", None), "role_words", role_words)
    )
    result.intent_mode = str(
        getattr(getattr(perception, "renderer", None), "intent_mode", intent_mode)
        if perception is not None
        else intent_mode
    )
    # 語彙 v2: 実際に使った版(注入レンダラでも**エンジン側の版**が正=行動の解決はこちら)。
    result.vocab_version = str(vocab_version)
    result.action_usage = _action_usage(per_action_total, vocab_version)
    # 二層の段 2: 活動層と起床の内訳(満了入口の列は全ランで出る=層が無ければ 0)
    result.activity = bool(activity_on)
    result.eatery = str(eatery)
    result.chooser = str(chooser)
    result.policy = str(policy)
    result.classical = (
        {**classical_policy.manifest_fields(),
         "decisions_by_hour": {"meal": classical_policy.by_hour[:, 0].tolist(),
                               "activity": classical_policy.by_hour[:, 1].tolist()}}
        if classical_policy is not None
        else {}
    )
    _cs = getattr(getattr(poi_resolver, "chooser", None), "stats", None)
    result.chooser_stats = (
        {"name": str(chooser), "p_h": float(classical_habit_p), "tau": float(classical_tau),
         "activity_region": str(activity_region), "counts": dict(sorted(_cs.items()))}
        if isinstance(_cs, dict)
        else {}
    )
    result.decision_layers = decision_layers_summary(layer_counts)
    # 〔第 1 期 1-2〕看板の注視の活動の乗数は消した=manifest の欄 ``p_see_activity`` は残して値は null
    result.p_see_activity = None
    result.target_resolution = (
        resolution_summary(poi_resolver.stats, poi_resolver.entropy_sum)
        if poi_resolver is not None
        else {}
    )
    result.move_search_radius = int(move_search_radius)
    result.mock_move_target_p = float(mock_move_target_p)
    result.intent = intent_layer.counters() if intent_layer is not None else {}
    result.familiarity = bool(familiarity_on)
    result.familiarity_k = int(familiarity_k)
    result.familiarity_summary = (
        fam_layer.summary(agents, max(0, int(t_end) - 1)) if fam_layer is not None else {}
    )
    result.memory = bool(memory_on)
    result.memory_n = int(memory_n)
    result.memory_summary = (
        {
            **mem_layer.summary(agents, max(0, int(t_end) - 1)),
            "gist_bytes": mem_layer.gist_bytes(),
            # 6b: 描画側の計数(記憶の行を載せた描画・項の件数・行の tok の分布・予算で削った数)
            "render": (
                _fam_renderer.memory_summary()
                if _fam_renderer is not None and hasattr(_fam_renderer, "memory_summary")
                else {}
            ),
        }
        if mem_layer is not None
        else {}
    )
    result.store_memory = bool(store_memory_on)
    result.store_memory_summary = (
        mem_layer.store.summary(agents, max(0, int(t_end) - 1), mem_layer.tau)
        if mem_layer is not None and mem_layer.store is not None
        else {}
    )
    result.wom = (
        {
            **wom_ex.summary(tuple(getattr(world.assets, "poi_name", ()) or ())),
            "store_rows_with_wom": int(
                result.store_memory_summary.get("rows_with_source_bit", {}).get("wom", 0)
            ),
            "store_events_wom": int(mem_layer.store.stats.get("events:wom", 0)),
        }
        if wom_ex is not None and mem_layer is not None and mem_layer.store is not None
        else {}
    )
    result.relations = (
        rel_layer.summary(agents, max(0, int(t_end) - 1)) if rel_layer is not None else {}
    )
    # 第 1 期 1-7: manifest の tools(道具の数・グループの数・連絡先の印の数・店の番号の表・看板の印=計器・記録だけ)
    from shibuya.engine.tools import record as _TOOLS

    result.tools = _TOOLS.manifest_fields(fx.tools, rel_layer, agents, daily_records)
    if rel_layer is not None and conv is not None and conv.origin_names is not None:
        # C10 8b 診断行: 起点ごとの 招待/承諾/断り/期限切れ/門で落ちた(decision_layers の入口にも同じ表)
        result.relations["origins"] = conv.origin_summary()
        result.decision_layers["conversation_origins"] = conv.origin_summary()
    _sc = getattr(poi_resolver, "store_choice", None) if poi_resolver is not None else None
    result.store_choice = (
        {**_sc.summary(), "arms": {"store_wom": bool(store_wom_on), "store_signage": bool(store_signage_on),
                                   "store_recall_scope": str(store_recall_scope),
                                   "chooser": str(getattr(poi_resolver.chooser, "name", ""))}}
        if _sc is not None
        else {}
    )
    if fam_layer is not None and result.familiarity_summary:
        # 5c: 入った回の露出を活動の種別の名で(索引 → 名)
        _fs = dict(result.familiarity_summary)
        _by = {
            P_SEE_ACTIVITY_KINDS[int(k.rsplit(":", 1)[1])]: int(v)
            for k, v in fam_layer.stats.items()
            if str(k).startswith("exposures_signage_entry_by_kind:")
        }
        if _by:
            _fs["exposures_signage_entry_by_kind"] = _by
        result.familiarity_summary = _fs
    result.hunger_model = str(hunger_model)
    result.intero_crossings = {
        f"{var}_{d}{suffix}": int(intero_cross[v, k, s])
        for v, var in enumerate(("hunger", "fatigue", "thermal"))
        for k, d in enumerate(("up", "down"))
        for s, suffix in enumerate(("", "_awake_in_area"))
    }
    result.energy_rate = str(energy_rate) if energy_on else ""
    result.meal_sleep_defer = str(meal_sleep_defer)
    result.home_meal = str(home_meal)
    result.hunger_words = str(hunger_words)
    result.energy = (
        {**energy_layer.model.manifest_fields(), **energy_layer.summary(agents)}
        if energy_layer is not None
        else {}
    )
    if intent_layer is not None:
        # B5「いま <行為> のため <対象> へ向かっている」を載せた回数(描画のあるランだけ)
        _rr = getattr(perception, "renderer", None) if perception is not None else None
        result.intent["b5_lines"] = int(getattr(_rr, "intent_lines", 0))
        result.intent["b5_lines_over_budget"] = int(getattr(_rr, "intent_lines_over_budget", 0))
        # Q25: 名指しの即時閉店の B6 補足を載せた回数
        result.intent["b6_named_closed_notes"] = int(getattr(_rr, "named_closed_notes", 0))
    result.intent_max_ticks = int(intent_max_ticks)
    _nr = getattr(perception, "renderer", None) if perception is not None else None
    # 〔第 4 期 4-3 版上げ 3 回目の第 2 部〕並び(distance)と同点の切り方(hash)はランの口では選べない=設定の欄 mode・order は
    # 消した(旧値 id の再現は安定版のタグ)。同点を切った数・並べた行に距離の同点があった描画の数は観測
    result.near_tiebreak = {
        "ties_broken": int(getattr(_nr, "near_tie_breaks", 0)),
        "tie_candidates": int(getattr(_nr, "near_tie_candidates", 0)),
        "order_ties": int(getattr(_nr, "near_order_ties", 0)),
    }
    result.group_norms = (  # 第308 D-107 (a)・第309 Q150 の切替口
        {"enabled": True, **norm_meter.summary(conv=conv, result=result)} if norm_meter is not None
        else {"enabled": False}
    )
    result.mock_out_of_cell_target_p = float(mock_out_of_cell_target_p)
    result.move_resolution = move_resolution_summary(
        poi_resolver.move_stats if poi_resolver is not None else Counter(),
        result.move_bad_target,
        result.move_unreachable,
    )
    result.calls_by_condition = {
        WakeCondition(i).name: int(calls_by_cond[i]) for i in range(N_WAKE_CONDITIONS_ALL)
    }
    if act_layer is not None:
        result.activity_counters = dict(act_layer.counters())
        result.activity_kind_counts = dict(act_layer.kind_distribution())
    result.sleep_suppression = bool(sleep_suppression)
    result.plan_sleep = bool(plan_sleep)
    result.wake_rate_by_hour = [
        (awake_sum[h] / (awake_ticks[h] * n_agents)) if (awake_ticks[h] and n_agents) else 0.0
        for h in range(24)
    ]
    if presence is not None:
        for _k, _v in presence.sleep_counts.items():
            sleep_counts[_k] = sleep_counts.get(_k, 0) + int(_v)
    result.planned_sleep_counts = dict(sleep_counts)
    result.plan_executor = bool(plan_exec_on)
    result.outside_suppression = bool(outside_suppression and plan_exec_on)
    result.outside_wake_candidates = int(rs.n_outside_calls)
    result.exit_mode = str(exit_mode)
    result.attendance_rate = float(attendance_rate)
    result.derive_rule = str(derive_rule)
    result.geometry = str(geometry)
    result.geometry_hops = int(rs.geometry_hops)
    result.geometry_jammed = int(rs.geometry_jammed)
    result.area_source = str(area_source)
    result.seat_area_eatery_m2 = (
        None if seat_area_eatery_m2 is None else float(seat_area_eatery_m2)
    )
    result.seat_area_retail_m2 = (
        None if seat_area_retail_m2 is None else float(seat_area_retail_m2)
    )
    if walkable is not None:
        _wk = np.asarray(walkable, dtype=np.float64).ravel()
        if _wk.size:
            result.walkable_area_median_m2 = float(np.median(_wk))
            result.walkable_area_min_m2 = float(_wk.min())
    result.attention = bool(attention_on)
    result.leave_effects = {"leave": int(leave_counts["n_leave"]),
                            "released_indoor": int(leave_counts["n_leave_indoor"]),
                            "left_queue": int(leave_counts["n_leave_queue"]),
                            "was_conversing": int(leave_counts["n_leave_conversing"]),
                            "sessions_closed": int(rs.leave_closed),
                            # 〔第 2 期 2-4 V3〕在席の印を歩き出しで解く腕(設定)と解いた数(観測)
                            "seat_release": str(b.cfg.seat_release),
                            "released_on_walk": int(leave_counts["n_seat_released_walk"])}
    if presence is not None:
        result.presence_exit = dict(presence.exit_summary())
        result.presence_counters = dict(presence.counters())
        result.presence_summary = presence.summary()
        # 標本の無かった時(短いラン)は NaN のまま来るので 0.0 に落とす(推測で埋めない)
        result.wake_rate_in_area_by_hour = [
            (0.0 if v != v else round(float(v), 6)) for v in presence.wake_in_area_by_hour
        ]
    result.diagnostics = np.asarray(diag_rows, dtype=np.int64).reshape(-1, len(DIAG_RUN_COLUMNS))
    result.phase_seconds = phase
    if norm_meter is not None:
        result.phase_seconds["group_norms"] = float(norm_meter.seconds)  # 第308: 計器の費用(壁時計)
        result.phase_seconds["group_norms_tick_ms_max"] = float(norm_meter.tick_ms_max)  # 第309: 1 刻みの最大
    result.wall_seconds = time.perf_counter() - rs.t_start
    result.arbiter_counters = {k: dict(v) for k, v in arbiter.counters().items()}
    result.money_end = int(agents.registry.money.astype(np.int64).sum())
    result.revenue_end = int(world.pois.revenue.astype(np.int64).sum())
    # 第 2 期 2-1: 経済の段階 2 の腕のラン=現金の外から入った額と現金を通らずに払った額(conserved の式の左辺に足す)
    # 〔第 2 期 2-4 V4〕店の売上の写し pois.revenue は税抜き=店から政府へ出たレジの税を左辺から引く
    _s2 = getattr(getattr(ledger, "money", None), "stage2", None) if ledger is not None else None
    result.money_stage2_in = int(_s2.cash_terms()) - int(_s2.register_tax()) if _s2 is not None else 0
    result.min_stock = int(world.pois.stock.min()) if world.n_poi else 0

    # ---- 状態成長宣言の検査(D-R2-6) ----
    # エンジンの 5 バッファ + **O(t) ログ本体**(ActualLog・取引ログ・納品ログ)。
    # 層2レビュー指摘: 5 バッファだけを外挿しても、D-R2-6 が名指しした「O(t) が本質」の
    # ログ(ActualLog と同型)は 1 バイトも測っていなかった。診断表(``diagnostics_rows``)は
    # 元から測っている(1 刻みあたり 1 行)。
    declarations: dict[str, Any] = dict(GD.declarations())
    measured: dict[str, int] = {
        "pending_apply": rs.peak_pending * GD.PENDING_APPLY_ROW_BYTES,
        "arbiter_backlog": rs.peak_backlog * GD.ARBITER_PENDING_ROW_BYTES,
        "intent_buffer": rs.peak_intents * GD.INTENT_ROW_BYTES,
        "diagnostics_rows": len(diag_rows) * GD.DIAG_ROW_BYTES,
        "tape_rows": result.llm_calls * GD.TAPE_ROW_BYTES,
    }
    if runner is not None:
        log_decls = dict(runner.log.growth_declarations())
        raw = log_decls.get(f"{runner.log.log_id}_raw")
        agg = log_decls.get(f"{runner.log.log_id}_daily")
        raw_bytes = len(runner.log) * int(raw.bytes_per_unit) if raw is not None else 0
        if raw is not None:
            declarations[raw.name] = raw
            measured[raw.name] = raw_bytes
        if agg is not None:
            # ``ActualLog.nbytes`` = 生ログ+索引+日次集約行。生ログぶんを引けば畳み先の実測。
            declarations[agg.name] = agg
            measured[agg.name] = max(0, int(runner.log.nbytes) - raw_bytes)
    led_decls, led_measured = ledger_growth
    declarations.update(led_decls)
    measured.update(led_measured)
    if act_layer is not None:
        # 二層の段 2: 活動の文(体ごとに上書き=日をまたいで伸びない・O(体数))
        _ad = GD.activity_declaration()
        declarations[_ad.name] = _ad
        measured[_ad.name] = int(
            sum(len(t.encode("utf-8")) for t in act_layer.text)
            + act_layer.until_kind.nbytes + act_layer.text_id.nbytes
        )
    result.growth_measured = measured
    result.growth_report = check_growth(
        declarations,
        measured,
        steps=t_end - t_begin,  # 10a: 回した通しの刻みの数(1 日のランでは ``ticks``)・10d: このランの区間
        minutes_per_step=max(1, tick_seconds // SECONDS_PER_MINUTE),
        n_entities=n_agents,
    )
    # ---- 10d: 再開の欄と日ごとの記録 ----
    result.daily = list(daily_records)
    result.day_heads = list(day_heads)
    result.resume = {
        "run_id": run_id,
        "parent_run": parent_run,
        "start_T": int(t_begin),
        "end_T": int(t_end),
        "finished": not _stopped,
        "sim_days": int(sim_days),
        "daily_closes": len(daily_records),
        "state_files": list(state_files),
        "w17_weekday_substituted_days": list(w17_substituted),
        "inflight_calls_at_end": len(fleet_inflight),
        "read_seconds": round(float(rs.read_seconds), 3),
        "restore_seconds": round(float(rs.restore_seconds), 3),
    }
    result.agents = agents  # type: ignore[attr-defined]
    result.world = world  # type: ignore[attr-defined]
    result.schedule = schedule  # type: ignore[attr-defined]
    result.ledger = ledger  # type: ignore[attr-defined]
    if occupancy_path and occ_ticks:
        import json as _json
        np.savez_compressed(
            str(occupancy_path),
            ticks=np.asarray(occ_ticks, dtype=np.int64),
            cell_counts=np.stack(occ_counts),
            kind_cell_counts=np.stack(occ_kind),
            transit_kind_counts=np.stack(occ_transit),
            meta=np.asarray(_json.dumps({"tick_seconds": int(tick_seconds), "start_hour": 0, "day_index": int(day_index)}, ensure_ascii=False)),
        )
    return result
