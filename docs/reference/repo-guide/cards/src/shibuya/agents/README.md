# src/shibuya/agents

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 5 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../src/shibuya/agents/__init__.py)

agents: 個体状態SoA/T0習慣/記憶/関係。core に依存。

- import している内部モジュール: `shibuya.agents.population`・`shibuya.agents.schedule`・`shibuya.agents.state`
- 読む試験(道筋で): `tests/tools/test_pkgmove.py`

## [population.py](../../../../../../../src/shibuya/agents/population.py)

agents.population — W16 母集団(``w16_population.parquet``)の読み込みと二層抽出。

- 公開の関数とクラス
  - `Population`(クラス): W16 母集団の列(行順=``agent_id`` の昇順)。
  - `PopulationSchemaError`(クラス): 母集団の列が欠けている・知らない語や番号がある(黙って埋めない)。
  - `load_population`(関数): W16 母集団を読む。資産が無ければ ``None``。
  - `population_available`(関数): ``<world_dir>/w16_population.parquet`` があるか。
  - `sample_population`(関数): 二層抽出(定員先取り層+統計層)。同 seed 同結果。
- import している内部モジュール: `shibuya.core.hashing`・`shibuya.core.rng`
- 呼び手: `shibuya.agents`・`shibuya.cli`・`shibuya.engine.economy_stage2`・`shibuya.engine.run`・`tools/c7/attr_arms.py`・`tools/w17/diversity_yardstick.py`
- 読む試験: `tests/build_pop/test_pop_pipeline.py`・`tests/build_pop/test_pop_units.py`・`tests/build_pop/test_w21_stage10_swap.py`・`tests/c6/test_t5_order_bias.py`・`tests/engine/rights/test_rights_from_w16.py`・`tests/engine/rights/test_staff_of_poi_equivalence.py`・`tests/engine/test_pop_w21_world.py`・`tests/engine/test_presence_derive_v2.py`・`tests/engine/test_presence_executor.py`・`tests/engine/test_relations_tenure.py`・`tests/engine/test_version_bump_10e.py`・`tests/engine/tools/test_c0_groups_from_w16.py`
- 読む試験(道筋で): `tests/engine/bridging/test_bridging_ledger.py`

## [schedule.py](../../../../../../../src/shibuya/agents/schedule.py)

agents.schedule — **mock 専用**の合成 T0 週次スケジュール(計画境界の生成器)。

- 公開の関数とクラス
  - `MockWeeklySchedule`(クラス): 合成日課(mock)。全て個体ごとの配列で持つ(個体オブジェクトを作らない)。
  - `draw_words`(関数): 個体 ``start_agent..start_agent+n_agents-1`` の生語を一括生成する(ループなし)。
  - `draw_words_per_agent`(関数): **参照実装**(T4 の定義そのまま): 個体ごとに独立の Philox から引く。
  - `synthesize`(関数): 合成日課を作る(**mock 専用**)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.core.rng`・`shibuya.core.time_consts`
- 呼び手: `shibuya.agents`・`shibuya.engine.systems.build`・`tools/c6/ablation1_fixed_vs_ranking.py`
- 読む試験: `tests/agents/test_schedule.py`・`tests/build_sched/test_weekly_loader.py`・`tests/engine/processes/conftest.py`・`tests/engine/processes/test_rail_return.py`・`tests/engine/rights/test_staff_of_poi_equivalence.py`・`tests/engine/test_10a_review_fixes.py`・`tests/engine/test_ablation23_switches.py`・`tests/engine/test_calendar_sites.py`・`tests/engine/test_conversation_invite.py`・`tests/engine/test_determinism_t1_t2_t4.py`・`tests/engine/test_intent_hold.py`・`tests/engine/test_ledger_wiring.py`・`tests/engine/test_plan_sleep_d62.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/test_vocab_v2_eat.py`・`tests/engine/test_weather_calendar_10e.py`
- 読む試験(道筋で): `tests/engine/test_two_phase.py`

## [state.py](../../../../../../../src/shibuya/agents/state.py)

agents.state — 個体状態の SoA(``core.soa.Registry`` の上)+起床条件表+結果コード。

- 公開の関数とクラス
  - `Activity`(クラス): 現在の行動状態(行動契約書 §2.1 の効果が落ちる先)。
  - `ActivityKind`(クラス): 活動の種別(``activity_kind``・二層の実装アジェンダ §2 の表)。
  - `AgentKind`(クラス): 個体の種別。
  - `AgentState`(クラス): 個体状態 SoA。``core.soa.Registry`` を1本持ち、フィールドは全て**宣言つき**(M9)。
  - `IntentKind`(クラス): 意図の対象の種類(``intent_kind``・段 2c)。``intent_target`` の意味を決める。
  - `ResultCode`(クラス): 「直前の結果」コード(行動契約書 §2.1 失敗の意味論 / §6 の 50 tok 欄の素材)。
  - `WakeCondition`(クラス): 起床条件(知覚契約書 §6 不応期表の**11 行と 1 対 1**)+ **活動の満了**(二層・段 2)。
  - `focus_code_for_person`(関数): 個体 id → ``focus_target`` の符号化(そのまま=非負)。
  - `focus_code_for_poi`(関数): POI 索引 → ``focus_target`` の符号化(``-2 - poi_id`` ≤ -2)。
  - `focus_is_person`(関数): ``focus_target`` が個体を指しているか。
  - `focus_is_poi`(関数): ``focus_target`` が POI を指しているか。
  - `focus_poi_of`(関数): ``focus_target`` → POI 索引(POI でない要素は ``-1``)。
- import している内部モジュール: `shibuya.core.soa`・`shibuya.core.types`・`shibuya.core.write_permit`
- 呼び手: `shibuya.agents`・`shibuya.agents.schedule`・`shibuya.agents.weekly`・`shibuya.cli`・`shibuya.engine.activity`・`shibuya.engine.arbiter`・`shibuya.engine.body.rules`・`shibuya.engine.body.schedule`・`shibuya.engine.calendar2.layer`・`shibuya.engine.calendar3.layer`・`shibuya.engine.calendar_self`・`shibuya.engine.change_detect`・`shibuya.engine.classical`・`shibuya.engine.commit`・`shibuya.engine.contact.attention`・`shibuya.engine.contact.habit`・`shibuya.engine.contact.layer`・`shibuya.engine.conversation`・`shibuya.engine.decision.ports`・`shibuya.engine.duties.layer`・`shibuya.engine.economy_rules`・`shibuya.engine.energy`・`shibuya.engine.familiarity`・`shibuya.engine.intent`・`shibuya.engine.memory`・`shibuya.engine.memory_shops`・`shibuya.engine.memory_store`・`shibuya.engine.norm_meter`・`shibuya.engine.poi_target`・`shibuya.engine.presence`・`shibuya.engine.processes.civic`・`shibuya.engine.processes.crowd`・`shibuya.engine.processes.environment`・`shibuya.engine.processes.goods_flow`・`shibuya.engine.processes.opening`・`shibuya.engine.processes.rail`・`shibuya.engine.processes.runner`・`shibuya.engine.processes.salient`・`shibuya.engine.relations`・`shibuya.engine.resolve`・`shibuya.engine.rights.initial`・`shibuya.engine.run`・`shibuya.engine.space.nav1`・`shibuya.engine.store_choice`・`shibuya.engine.store_memory`・`shibuya.engine.systems.body`・`shibuya.engine.systems.build`・`shibuya.engine.systems.decide`・`shibuya.engine.systems.judge`・`shibuya.engine.systems.llm_io`・`shibuya.engine.systems.report`・`shibuya.engine.systems.state_io`・`shibuya.engine.systems.talk`・`shibuya.perception.renderer`・`tools/c6/ablation1_fixed_vs_ranking.py`・`tools/c6/t7_distribution.py`・`tools/vocab/adjudicate.py`
- 読む試験: `tests/agents/test_state.py`・`tests/bench/test_refr20b_tool.py`・`tests/build_lang/test_wiring.py`・`tests/build_pop/test_pop_units.py`・`tests/build_sched/test_w17_prompts.py`・`tests/build_sched/test_weekly_loader.py`・`tests/c6/test_c6lib_scenes.py`・`tests/c6/test_t5_order_bias.py`・`tests/economy/test_accounts.py`・`tests/engine/body/body_fixtures.py`・`tests/engine/body/test_body_guard.py`・`tests/engine/bridging/test_bridging_ledger.py`・`tests/engine/calendar2/_ca2.py`・`tests/engine/calendar2/test_ca2_units.py`・`tests/engine/clock/test_tm3_step_scope.py`・`tests/engine/contact/_c1.py`・`tests/engine/contact/_c2.py`・`tests/engine/contact/test_c1_fixes.py`・`tests/engine/contact/test_c1_units.py`・`tests/engine/contact/test_c2_habit.py`・`tests/engine/memory/test_m0_store_schema.py`・`tests/engine/memory/test_m4_m5_people.py`・`tests/engine/multiday/test_md23_body_events.py`・`tests/engine/processes/conftest.py`・`tests/engine/processes/test_civic.py`・`tests/engine/processes/test_crowd.py`・`tests/engine/processes/test_goods_flow.py`・`tests/engine/processes/test_opening.py`・`tests/engine/processes/test_rail.py`・`tests/engine/processes/test_rail_board_intent.py`・`tests/engine/processes/test_salient.py`・`tests/engine/proximity/test_switch_sites.py`・`tests/engine/rights/test_rights_events.py`・`tests/engine/rights/test_staff_of_poi_equivalence.py`・`tests/engine/space/test_nav1_units.py`・`tests/engine/speech/test_speech_choice_utterance.py`・`tests/engine/speech/test_speech_on_reaches_addressee.py`・`tests/engine/speech/test_wom_from_utterance_roundtrip.py`・`tests/engine/systems/test_stage_a_guard.py`・`tests/engine/test_ablation23_switches.py`・`tests/engine/test_add_at_guard.py`・`tests/engine/test_arbiter.py`・`tests/engine/test_area_source_c9c.py`・`tests/engine/test_c9b_targets_attention.py`・`tests/engine/test_calendar_sites.py`・`tests/engine/test_change_detect_p6.py`・`tests/engine/test_classical_policy.py`・`tests/engine/test_classical_social.py`・`tests/engine/test_conversation.py`・`tests/engine/test_conversation_invite.py`・`tests/engine/test_defect_fixes_1103.py`・`tests/engine/test_energy_balance.py`・`tests/engine/test_familiarity.py`・`tests/engine/test_fleet_wiring.py`・`tests/engine/test_geometry_c9.py`・`tests/engine/test_intent_chooser.py`・`tests/engine/test_intent_hold.py`・`tests/engine/test_ledger_wiring.py`・`tests/engine/test_meal_bundle_2b.py`・`tests/engine/test_meal_gate_per_hour.py`・`tests/engine/test_memory_recall.py`・`tests/engine/test_memory_record.py`・`tests/engine/test_mock_day_w2.py`・`tests/engine/test_move_destination.py`・`tests/engine/test_norm_meter.py`・`tests/engine/test_parser_contract.py`・`tests/engine/test_plan_sleep_d62.py`・`tests/engine/test_presence_executor.py`・`tests/engine/test_presence_exit_walk.py`・`tests/engine/test_relations.py`・`tests/engine/test_relations_8b.py`・`tests/engine/test_renderer_wiring.py`・`tests/engine/test_resolve.py`・`tests/engine/test_response_delay.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_seat_release_2_4.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_sleep_suppression_d56.py`・`tests/engine/test_stage3_small_fixes.py`・`tests/engine/test_state_ledger_10b.py`・`tests/engine/test_store_choice.py`・`tests/engine/test_store_memory.py`・`tests/engine/test_tape_wiring.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/test_two_phase.py`・`tests/engine/test_undefined_action.py`・`tests/engine/test_vocab_v2_eat.py`・`tests/engine/test_weather_calendar_10e.py`・`tests/engine/test_wom.py`・`tests/engine/tools/test_c0_contacts_in_relations.py`・`tests/llm/test_contract.py`・`tests/llm/test_fleet_contract.py`・`tests/llm/test_vocab_v2.py`・`tests/perception/facts/head_renderer_136fdbb.py`・`tests/perception/facts/scenes.py`・`tests/perception/facts/test_percept_schema.py`・`tests/perception/facts/test_render_from_percept_bytes.py`・`tests/perception/test_ablation1.py`・`tests/perception/test_ablation6_signage.py`・`tests/perception/test_b4_detector_gap.py`・`tests/perception/test_b4b_queue_feed.py`・`tests/perception/test_b6_invite.py`・`tests/perception/test_hashes_state.py`・`tests/perception/test_intent_mode_open.py`・`tests/perception/test_near_tiebreak.py`・`tests/perception/test_nearby_vectorized.py`・`tests/perception/test_p_see_activity.py`・`tests/perception/test_renderer_golden.py`・`tests/perception/test_signage_p_see_gate.py`・`tests/perception/test_templates.py`・`tests/perception/test_vocab_v2_templates.py`
- 読む試験(道筋で): `tests/engine/systems/test_fix_guards.py`
- 状態台帳の行
  - SoA の列 `agents`
    - `agents.activity` activity(挙動 behavior・復元 required) 書ける系: activity_intent・apply_responses・build・calendar_2・close_final・conversation・day_close・phase_c・plan_boundary・presence・world
    - `agents.activity_kind` activity_kind(挙動 behavior・復元 required) 書ける系: activity_intent・presence
    - `agents.activity_until` activity_until(挙動 behavior・復元 required) 書ける系: activity_intent・presence
    - `agents.age` age(挙動 behavior・復元 derivable) 書ける系: build
    - `agents.band` band(挙動 no・復元 derivable) 書ける系: build・close_final・day_close・phase_c・plan_boundary・presence・world
    - `agents.board_line` board_line(挙動 behavior・復元 required) 書ける系: build・calendar_2・phase_c・plan_boundary・presence
    - `agents.board_since` board_since(挙動 behavior・復元 required) 書ける系: build・calendar_2・phase_c・plan_boundary・presence
    - `agents.cell` cell(挙動 behavior・復元 required) 書ける系: build・close_final・day_close・phase_c・plan_boundary・presence・world
    - `agents.edge_id` edge_id(挙動 behavior・復元 required) 書ける系: phase_c
    - `agents.edge_s` edge_s(挙動 behavior・復元 required) 書ける系: phase_c
    - `agents.eer_kcal` eer_kcal(挙動 behavior・復元 derivable) 書ける系: build
    - `agents.energy_balance` energy_balance(挙動 diag・復元 required) 書ける系: body・build・home_meal・phase_c
    - `agents.fam_exposures` fam_exposures(挙動 behavior・復元 required) 書ける系: familiarity
    - `agents.fam_first` fam_first(挙動 behavior・復元 required) 書ける系: familiarity
    - `agents.fam_last` fam_last(挙動 no・復元 required) 書ける系: familiarity
    - `agents.fam_thing` fam_thing(挙動 behavior・復元 required) 書ける系: familiarity
    - `agents.fam_visits` fam_visits(挙動 behavior・復元 required) 書ける系: familiarity
    - `agents.fatigue` fatigue(挙動 behavior・復元 required) 書ける系: body・build・phase_c
    - `agents.fatigue_stage` fatigue_stage(挙動 behavior・復元 required) 書ける系: detect
    - `agents.focus_target` focus_target(挙動 behavior・復元 required) 書ける系: phase_c
    - `agents.focus_ttl` focus_ttl(挙動 behavior・復元 required) 書ける系: phase_c
    - `agents.holdings` holdings(挙動 behavior・復元 required) 書ける系: phase_c・world
    - `agents.hunger` hunger(挙動 behavior・復元 required) 書ける系: body・build・home_meal・phase_c
    - `agents.hunger_stage` hunger_stage(挙動 behavior・復元 required) 書ける系: build・detect・home_meal
    - `agents.intent_action` intent_action(挙動 behavior・復元 required) 書ける系: activity_intent・phase_c
    - `agents.intent_kind` intent_kind(挙動 behavior・復元 required) 書ける系: activity_intent・phase_c
    - `agents.intent_since` intent_since(挙動 behavior・復元 required) 書ける系: activity_intent・phase_c
    - `agents.intent_target` intent_target(挙動 behavior・復元 required) 書ける系: activity_intent・phase_c
    - `agents.kind` kind(挙動 behavior・復元 derivable) 書ける系: build
    - `agents.last_action` last_action(挙動 behavior・復元 required) 書ける系: activity_intent・phase_c
    - `agents.last_result` last_result(挙動 behavior・復元 required) 書ける系: activity_intent・conversation・duties・phase_c・plan_boundary・presence・world
    - `agents.last_result_tick` last_result_tick(挙動 behavior・復元 required) 書ける系: activity_intent・conversation・duties・phase_c・plan_boundary・presence・world
    - `agents.mem_cell` mem_cell(挙動 behavior・復元 required) 書ける系: decide・llm_receive・memory
    - `agents.mem_importance` mem_importance(挙動 behavior・復元 required) 書ける系: decide・llm_receive・memory
    - `agents.mem_kind` mem_kind(挙動 behavior・復元 required) 書ける系: decide・llm_receive・memory
    - `agents.mem_last` mem_last(挙動 behavior・復元 required) 書ける系: decide・llm_receive・memory
    - `agents.mem_n` mem_n(挙動 behavior・復元 required) 書ける系: decide・llm_receive・memory
    - `agents.mem_object` mem_object(挙動 behavior・復元 required) 書ける系: decide・llm_receive・memory
    - `agents.mem_partner` mem_partner(挙動 behavior・復元 required) 書ける系: decide・llm_receive・memory
    - `agents.mem_result` mem_result(挙動 behavior・復元 required) 書ける系: decide・llm_receive・memory
    - `agents.mem_tick` mem_tick(挙動 behavior・復元 required) 書ける系: decide・llm_receive・memory
    - `agents.money` money(挙動 behavior・復元 required) 書ける系: build・phase_c
    - `agents.nav_fi` nav_fi(挙動 behavior・復元 required) 書ける系: phase_c
    - `agents.nav_node` nav_node(挙動 behavior・復元 required) 書ける系: phase_c
    - `agents.nav_of` nav_of(挙動 behavior・復元 required) 書ける系: phase_c
    - `agents.nav_ox` nav_ox(挙動 behavior・復元 required) 書ける系: phase_c
    - `agents.nav_oy` nav_oy(挙動 behavior・復元 required) 書ける系: phase_c
    - `agents.nav_t` nav_t(挙動 behavior・復元 required) 書ける系: phase_c
    - `agents.nav_tgt` nav_tgt(挙動 behavior・復元 required) 書ける系: phase_c
    - `agents.nav_wait` nav_wait(挙動 behavior・復元 required) 書ける系: phase_c
    - `agents.node` node(挙動 behavior・復元 required) 書ける系: build・close_final・day_close・phase_c・plan_boundary・presence・world
    - `agents.path_next_node` path_next_node(挙動 behavior・復元 required) 書ける系: phase_c
    - `agents.plan_flags` plan_flags(挙動 behavior・復元 required) 書ける系: build・close_final・day_close・day_head・plan_boundary・presence・world
    - `agents.poi_ref` poi_ref(挙動 behavior・復元 required) 書ける系: phase_c・plan_boundary・presence・world
    - `agents.poi_since` poi_since(挙動 behavior・復元 required) 書ける系: phase_c・plan_boundary・presence・world
    - `agents.queue_poi` queue_poi(挙動 behavior・復元 required) 書ける系: phase_c・plan_boundary・presence・world
    - `agents.queue_since` queue_since(挙動 behavior・復元 required) 書ける系: phase_c・plan_boundary・presence・world
    - `agents.refractory_until` refractory_until(挙動 behavior・復元 required) 書ける系: decide・wake_filter
    - `agents.rel_first` rel_first(挙動 behavior・復元 required) 書ける系: build・memory・relations_wake
    - `agents.rel_kind` rel_kind(挙動 behavior・復元 required) 書ける系: build・memory・relations_wake
    - `agents.rel_last` rel_last(挙動 no・復元 required) 書ける系: build・memory・relations_wake
    - `agents.rel_n` rel_n(挙動 behavior・復元 required) 書ける系: build・memory・relations_wake
    - `agents.rel_partner` rel_partner(挙動 behavior・復元 required) 書ける系: build・memory・relations_wake
    - `agents.rel_sign` rel_sign(挙動 behavior・復元 required) 書ける系: build・memory・relations_wake
    - `agents.sex` sex(挙動 behavior・復元 derivable) 書ける系: build
    - `agents.since_meal_kcal` since_meal_kcal(挙動 behavior・復元 required) 書ける系: body・build・home_meal・phase_c
    - `agents.sleep_pending` sleep_pending(挙動 behavior・復元 required) 書ける系: calendar_2・phase_c・plan_boundary・presence
    - `agents.sm_first` sm_first(挙動 behavior・復元 required) 書ける系: decide・llm_receive・memory
    - `agents.sm_last` sm_last(挙動 behavior・復元 required) 書ける系: decide・llm_receive・memory
    - `agents.sm_n` sm_n(挙動 behavior・復元 required) 書ける系: decide・llm_receive・memory
    - `agents.sm_poi` sm_poi(挙動 behavior・復元 required) 書ける系: decide・llm_receive・memory
    - `agents.sm_precision` sm_precision(挙動 behavior・復元 required) 書ける系: decide・llm_receive・memory
    - `agents.sm_source` sm_source(挙動 behavior・復元 required) 書ける系: decide・llm_receive・memory
    - `agents.sm_valence` sm_valence(挙動 behavior・復元 required) 書ける系: decide・llm_receive・memory
    - `agents.talk_partner` talk_partner(挙動 behavior・復元 required) 書ける系: apply_responses・conversation・phase_c
    - `agents.target_node` target_node(挙動 behavior・復元 required) 書ける系: activity_intent・build・calendar_2・close_final・day_close・phase_c・plan_boundary・presence・world
    - `agents.thermal` thermal(挙動 behavior・復元 required) 書ける系: build・world
    - `agents.thermal_stage` thermal_stage(挙動 behavior・復元 required) 書ける系: detect
    - `agents.transit_ref` transit_ref(挙動 behavior・復元 required) 書ける系: build・close_final・day_close・phase_c・plan_boundary・presence・world
    - `agents.transit_state` transit_state(挙動 behavior・復元 required) 書ける系: build・close_final・day_close・phase_c・plan_boundary・presence・world
    - `agents.weight_kg` weight_kg(挙動 behavior・復元 derivable) 書ける系: build
    - `agents.xy` xy(挙動 behavior・復元 required) 書ける系: build・close_final・day_close・phase_c・plan_boundary・presence・world
- 決定の ID: 10-06・11-03・D-51・D-62・D-66・D-71・D-112・D-114・D-116・D-118・D-120・D-122・第 276・第 290・第 291・第 296・第 330・第 334

## [weekly.py](../../../../../../../src/shibuya/agents/weekly.py)

agents.weekly — W17 週次活動表(``w17_schedule.parquet``)の読み込みと計画境界の取り出し。

- 公開の関数とクラス
  - `InboundStarts`(クラス): その日の**域内活動**(``place_kind != 域外``)の開始分を体行ごとに束ねた索引(D-61)。
  - `WeeklySchedule`(クラス): 週次活動表(行順=``(agent_id, day, seq)`` 昇順)。
  - `activity_to_action`(関数): 語彙版 → 活動語 → 行動語の表(v1/v2 は ``ACTIVITY_TO_ACTION`` そのもの)。
  - `apply_to_mock_schedule`(関数): 合成日課(``MockWeeklySchedule``)の拠点セルを W17 の当日の行き先で上書きする。
  - `load_weekly`(関数): W17 週次表を読む(``<world_dir>/w17_schedule.parquet``)。資産が無ければ ``None``。
  - `load_weekly_file`(関数): **ファイル名を問わず**1 つの parquet から週次表を組む。
  - `weekly_available`(関数): ``<world_dir>/w17_schedule.parquet`` があるか。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.core.hashing`・`shibuya.core.time_consts`
- 呼び手: `shibuya.engine.calendar_shadow`・`shibuya.engine.energy`・`shibuya.engine.presence`・`shibuya.engine.systems.build`・`tools/instruments/anchor_gauge.py`・`tools/w17/diversity_yardstick.py`
- 読む試験: `tests/build_pop/test_w21_stage10_swap.py`・`tests/build_sched/test_trial.py`・`tests/build_sched/test_weekly_loader.py`・`tests/engine/body/test_meal_default_w17.py`・`tests/engine/processes/test_rail_return.py`・`tests/engine/test_10a_review_fixes.py`・`tests/engine/test_energy_balance.py`・`tests/engine/test_meal_bundle_2b.py`・`tests/engine/test_plan_sleep_d62.py`・`tests/engine/test_presence_derive_v2.py`・`tests/engine/test_presence_executor.py`・`tests/engine/test_relations.py`・`tests/engine/test_relations_8b.py`・`tests/engine/test_relations_tenure.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/time/test_t0_time_consts.py`・`tests/w17/test_diversity_yardstick.py`
- 決定の ID: D-61・D-62・D-68
