# 状態台帳 189 行 × 書き手(HEAD `0389689`・mock/classical の 6 構成・1,000 体・窓の tick・〔改訂(第330)〕系の単位)

- 行 189・動的に書き手が見えた行 134(見えない行=この 6 構成・窓では値が変わらなかった行。書き手が無いとは限らない)。
- 系の名は草案 §2-2(〔改訂(第330)〕測りの境目を系に合わせた)。世界過程は `proc_*.json`(3 構成)。resolve の口は AST の静的な書き(SoA だけ)。
- 作り方: `ledger_writers.py`(同じ置き場)。

| 鍵 | 名前 | 置き場 | 軸1 | 軸2 | 系(動的に書いた) | 世界過程 | resolve の口(静的) |
|---|---|---|---|---|---|---|---|
| agents.cell | cell | agents | behavior | required | phase_c, presence, world | large_event, presence.step, rail | apply, initialize, place_at_external, rail_arrive, rail_depart |
| agents.node | node | agents | behavior | required | phase_c, presence, world | large_event, presence.step, rail | _apply_alight, _apply_engine_step, _board_riders, apply, initialize, place_at_external … |
| agents.band | band | agents | no | derivable | phase_c, presence, world | large_event, presence.step, rail | apply, initialize, rail_arrive |
| agents.xy | xy | agents | behavior | required | phase_c, presence, world | large_event, presence.step, rail | apply, initialize, rail_arrive |
| agents.path_next_node | path_next_node | agents | behavior | required | phase_c |  | _apply_engine_step, apply |
| agents.target_node | target_node | agents | behavior | required | phase_c, plan_boundary, presence | presence.step | _apply_alight, _apply_board, _apply_engine_step, _apply_move, _apply_sleep, _board_riders … |
| agents.kind | kind | agents | behavior | derivable |  |  | initialize |
| agents.age | age | agents | behavior | derivable |  |  | initialize |
| agents.sex | sex | agents | behavior | derivable |  |  | initialize |
| agents.hunger | hunger | agents | behavior | required | body, phase_c |  | _complete_buy, _complete_eat, _energy_meal, _energy_snack, advance_body, initialize … |
| agents.fatigue | fatigue | agents | behavior | required | body, phase_c |  | _apply_rest, advance_body, initialize |
| agents.thermal | thermal | agents | behavior | required | world | environment | initialize, set_thermal |
| agents.hunger_stage | hunger_stage | agents | behavior | required | detect |  | energy_home_meal, initialize_energy |
| agents.fatigue_stage | fatigue_stage | agents | behavior | required | detect |  |  |
| agents.thermal_stage | thermal_stage | agents | behavior | required | detect |  |  |
| agents.money | money | agents | behavior | required | phase_c |  | _board_riders, _complete_buy, _complete_eat, initialize |
| agents.holdings | holdings | agents | behavior | required | phase_c |  | _complete_buy |
| agents.activity | activity | agents | behavior | required | apply_responses, close_final, conversation, phase_c, plan_boundary, presence, world | crowd, large_event, presence.step, presence.step_plan_boundaries, rail | _apply_alight, _apply_board, _apply_buy, _apply_eat, _apply_engine_step, _apply_leave … |
| agents.talk_partner | talk_partner | agents | behavior | required | apply_responses, conversation, phase_c |  | _apply_leave, _apply_talk, join_conversation, revert_conversation, set_conversing |
| agents.transit_state | transit_state | agents | behavior | required | close_final, phase_c, presence, world | large_event, presence.step, rail | _apply_alight, _board_riders, place_at_external, rail_arrive, rail_depart |
| agents.transit_ref | transit_ref | agents | behavior | required | close_final, phase_c, presence, world | large_event, presence.step, rail | _apply_alight, _board_riders, place_at_external, rail_arrive, rail_depart |
| agents.board_line | board_line | agents | behavior | required | phase_c, plan_boundary |  | _apply_board, _apply_engine_step, _board_riders, _enter_board_queue, _serve_board_queue, apply … |
| agents.board_since | board_since | agents | behavior | required | phase_c |  | _apply_board, _apply_engine_step, _board_riders, _enter_board_queue, _serve_board_queue, apply … |
| agents.sleep_pending | sleep_pending | agents | behavior | required | phase_c, plan_boundary |  | _apply_engine_step, apply, begin_planned_sleep, wake_from_plan |
| agents.intent_action | intent_action | agents | behavior | required | activity_intent, phase_c |  | _clear_intent_fields, set_intent |
| agents.intent_target | intent_target | agents | behavior | required | activity_intent, phase_c |  | _clear_intent_fields, set_intent |
| agents.intent_kind | intent_kind | agents | behavior | required | activity_intent, phase_c |  | _clear_intent_fields, set_intent |
| agents.intent_since | intent_since | agents | behavior | required | activity_intent, phase_c |  | _clear_intent_fields, set_intent |
| agents.poi_ref | poi_ref | agents | behavior | required | phase_c, presence, world | crowd, presence.step | _board_riders, _complete_buy, _complete_eat, release_indoor |
| agents.poi_since | poi_since | agents | behavior | required | phase_c, presence, world | crowd, presence.step | _complete_buy, _complete_eat, release_indoor |
| agents.queue_poi | queue_poi | agents | behavior | required |  |  | _apply_buy, _apply_eat, _board_riders, _complete_buy, _complete_eat, _serve_poi_queue … |
| agents.queue_since | queue_since | agents | behavior | required |  |  | _apply_buy, _apply_eat, _serve_poi_queue, balk_queue |
| agents.refractory_until | refractory_until | agents | behavior | required | decide |  | clear_refractory |
| agents.last_action | last_action | agents | behavior | required | phase_c |  | apply, fail_intent, relabel_intent_failure |
| agents.last_result | last_result | agents | behavior | required | phase_c |  | _fail, _ok, apply, balk_queue, fail_intent, join_conversation … |
| agents.last_result_tick | last_result_tick | agents | behavior | required | phase_c |  | _fail, _ok, apply, balk_queue, fail_intent, join_conversation … |
| agents.fail_streak | fail_streak | agents | no | unknown | phase_c |  | _fail, _ok, apply, balk_queue, fail_intent, request_open_close |
| agents.edge_id | edge_id | agents | behavior | required | phase_c |  | _apply_engine_step, apply |
| agents.edge_s | edge_s | agents | behavior | required | phase_c |  | _apply_engine_step, apply |
| agents.focus_target | focus_target | agents | behavior | required |  |  | _advance_focus, _clear_focus, _set_focus, _settle_approach |
| agents.focus_ttl | focus_ttl | agents | behavior | required |  |  | _advance_focus, _clear_focus, _set_focus, _settle_approach |
| agents.weight_kg | weight_kg | agents | behavior | derivable |  |  | initialize_energy |
| agents.eer_kcal | eer_kcal | agents | behavior | derivable |  |  | initialize_energy |
| agents.since_meal_kcal | since_meal_kcal | agents | behavior | required | body, phase_c |  | _energy_meal, _energy_snack, initialize_energy |
| agents.energy_balance | energy_balance | agents | diag | required | body, phase_c |  | _energy_meal, _energy_snack, initialize_energy |
| agents.plan_activity | plan_activity | agents | no | unknown | day_head, plan_boundary, presence | presence.step, presence.step_plan_boundaries | set_plan_state |
| agents.plan_flags | plan_flags | agents | behavior | required | presence, world | large_event, presence.step | set_plan_state |
| agents.activity_until | activity_until | agents | behavior | required | activity_intent |  | set_activity, set_activity_until |
| agents.activity_kind | activity_kind | agents | behavior | required | activity_intent |  | set_activity |
| agents.fam_thing | fam_thing | agents | behavior | required |  |  | write_familiarity |
| agents.fam_first | fam_first | agents | behavior | required |  |  | write_familiarity |
| agents.fam_last | fam_last | agents | no | required |  |  | write_familiarity |
| agents.fam_visits | fam_visits | agents | behavior | required |  |  | write_familiarity |
| agents.fam_exposures | fam_exposures | agents | behavior | required |  |  | write_familiarity |
| agents.mem_kind | mem_kind | agents | behavior | required | memory |  | write_memory |
| agents.mem_tick | mem_tick | agents | behavior | required | memory |  | write_memory |
| agents.mem_last | mem_last | agents | behavior | required | decide, memory |  | write_memory |
| agents.mem_cell | mem_cell | agents | behavior | required | memory |  | write_memory |
| agents.mem_partner | mem_partner | agents | behavior | required | memory |  | write_memory |
| agents.mem_object | mem_object | agents | behavior | required | memory |  | write_memory |
| agents.mem_result | mem_result | agents | behavior | required | memory |  | write_memory |
| agents.mem_importance | mem_importance | agents | behavior | required | decide, memory |  | write_memory |
| agents.mem_n | mem_n | agents | behavior | required | decide, memory |  | write_memory |
| agents.sm_poi | sm_poi | agents | behavior | required | memory |  | write_store_memory |
| agents.sm_valence | sm_valence | agents | behavior | required | memory |  | write_store_memory |
| agents.sm_precision | sm_precision | agents | behavior | required | memory |  | write_store_memory |
| agents.sm_first | sm_first | agents | behavior | required | memory |  | write_store_memory |
| agents.sm_last | sm_last | agents | behavior | required | memory |  | write_store_memory |
| agents.sm_n | sm_n | agents | behavior | required | memory |  | write_store_memory |
| agents.sm_source | sm_source | agents | behavior | required | memory |  | write_store_memory |
| agents.rel_partner | rel_partner | agents | behavior | required | memory |  | write_relations |
| agents.rel_kind | rel_kind | agents | behavior | required | memory |  | write_relations |
| agents.rel_sign | rel_sign | agents | behavior | required | memory |  | write_relations |
| agents.rel_first | rel_first | agents | behavior | required | memory |  | write_relations |
| agents.rel_last | rel_last | agents | no | required | memory, relations_wake |  | write_relations |
| agents.rel_n | rel_n | agents | behavior | required | memory, relations_wake |  | write_relations |
| cells.density | density | cells | behavior | derivable | phase_c |  | apply, initialize |
| cells.density_stage | density_stage | cells | behavior | derivable | phase_c |  | apply, initialize |
| cells.noise_stage | noise_stage | cells | behavior | derivable |  |  |  |
| cells.open_count | open_count | cells | no | derivable | phase_c |  | apply, initialize |
| cells.b4_hash | b4_hash | cells | no | derivable | detect |  | apply_detection |
| pois.cell | cell | pois | behavior | derivable |  |  | apply, initialize, place_at_external, rail_arrive, rail_depart |
| pois.node | node | pois | behavior | derivable |  |  | _apply_alight, _apply_engine_step, _board_riders, apply, initialize, place_at_external … |
| pois.stock | stock | pois | behavior | required | phase_c |  | _complete_buy, discard_to_bin, restock |
| pois.price | price | pois | behavior | derivable |  |  |  |
| pois.revenue | revenue | pois | diag | required | phase_c |  | _complete_buy, _complete_eat |
| pois.capacity | capacity | pois | behavior | derivable |  |  |  |
| pois.open_from | open_from | pois | behavior | derivable |  |  |  |
| pois.open_to | open_to | pois | behavior | derivable |  |  |  |
| pois.open_now | open_now | pois | behavior | required | world | opening | request_open_close, set_open_flags |
| perception.heading | heading | perception | no | derivable |  |  | set_notice_state |
| perception.task_flag | task_flag | perception | no | derivable |  |  | set_notice_state |
| perception.invocation_distance | invocation_distance | perception | no | discardable |  |  |  |
| O1 | ActivityLayer text・until_kind | external | behavior | required | activity_intent |  |  |
| O2 | ActivityLayer text_id・_texts・_text_ids・_ | external | no | derivable | activity_intent |  |  |
| O3 | ActivityLayer _bt_agent・_bt_tick・_bt_sta | external | no | derivable |  |  |  |
| O4 | IntentLayer _payload | external | behavior | required | activity_intent |  |  |
| O5 | IntentLayer _proposals・_executing・_kept_ | external | no | discardable | activity_intent, apply_responses, phase_a |  |  |
| O6 | IntentLayer stats・ticks_sum・ticks_n | external | diag | discardable | activity_intent, apply_responses, detect, phase_a |  |  |
| O7 | FamiliarityLayer prev_cell | external | behavior | required |  |  |  |
| O8 | MemoryLayer gist・_gist_order | external | behavior | required | decide |  |  |
| O9 | MemoryLayer _session_key・_gist_done | external | behavior | required | decide, memory |  |  |
| O10 | MemoryLayer _next_session・_next_join | external | behavior | required | memory |  |  |
| O11 | MemoryLayer _target・stats・recall_stats | external | diag | discardable | decide, memory |  |  |
| O12 | StoreMemory stats | external | diag | discardable | memory |  |  |
| O13 | StoreChoice choice_poi・choice_reason・sta | external | diag | discardable | apply_responses |  |  |
| O14 | StoreChoice _b_tick・_b_off | external | no | derivable |  |  |  |
| O15 | WomExtractor stats・top・unmatched_words | external | diag | discardable | decide |  |  |
| O16 | RelationLayer _prev_cell | external | behavior | required | relations_wake |  |  |
| O17 | RelationLayer _acq_until | external | behavior | required | decide |  |  |
| O18 | RelationLayer _co_since・_co_day・_co_acti | external | behavior | required | relations_wake |  |  |
| O19 | RelationLayer _invite_salt・chosen_count・ | external | diag | discardable | apply_responses, conversation, decide, memory, relations_wake |  |  |
| O20 | ClassicalPolicy _prev | external | behavior | required | decide |  |  |
| O21 | ClassicalPolicy _gate_hazard(EnergyLayer | external | behavior | required |  |  |  |
| O22 | ClassicalPolicy _condition・_tick・_eating | external | no | discardable | decide |  |  |
| O23 | ClassicalPolicy _b_tick・_b_off・counts・by | external | no | derivable | decide |  |  |
| O24 | ClassicalPolicy home_cell・acq_fn | external | no | derivable |  |  |  |
| O25 | ClassicalChooser last_habit・stats | external | diag | discardable | apply_responses |  |  |
| O26 | TargetResolver _cat_mask_cache・stats・ent | external | diag | discardable | apply_responses |  |  |
| O27 | EnergyLayer bmr | external | behavior | derivable |  |  |  |
| O28 | EnergyLayer meal_bits・n_meals・n_snacks・c | external | diag | discardable | body, energy_after, phase_c |  |  |
| O29 | OutOfAreaMeals の予定 tick・agent・slot・from_ | external | no | derivable |  |  |  |
| O30 | OutOfAreaMeals の遅らせの表 d_agent・d_slot・d_a | external | no | derivable |  |  |  |
| O31 | OutOfAreaMeals d_armed(就寝中の食事を起床時に回す印) | external | behavior | required |  |  |  |
| O32 | HomeMeals の予定 tick・agent・slot・_start・hom | external | no | derivable |  |  |  |
| O33 | HomeMeals n_not_home・n_asleep・OutOfAreaM | external | diag | discardable |  |  |  |
| O34 | GroupNormMeter _prev_xy・_pair_keys・_pair | external | no | discardable | apply_responses, observe |  |  |
| O35 | PlanExecutor 退出の歩行 _walk_since・_walk_lin | external | behavior | required |  |  |  |
| O36 | PlanExecutor _defer_ids・_defer_deadline・ | external | behavior | required | presence, world | presence.step, rail |  |
| O37 | PlanExecutor _pulled_in_today | external | diag | required | day_head, world | large_event |  |
| O38 | PlanExecutor ev_*・arrival_*・absent・block | external | no | derivable | day_head |  |  |
| O39 | ConversationManager sessions・_of_agent・_ | external | behavior | required | apply_responses, conversation, decide |  |  |
| O40 | ConversationManager join_events | external | behavior | required |  |  |  |
| O41 | ConversationManager origin_counts ほかの計数 | external | diag | discardable | apply_responses, conversation, decide |  |  |
| O42 | Arbiter _pending・_pool・queue・_last_tick | external | behavior | required | arbiter |  |  |
| O43 | run_day の局所 pending(適用待ちの応答) | external | behavior | required | apply_responses, decide |  |  |
| O44 | run_day の局所 fleet_deferred・fleet_waiting | external | behavior | required |  |  |  |
| O45 | ChangeDetector _prev_raw | external | behavior | required | detect |  |  |
| O46 | SalientProcess rng・event_seen_tick・budge | external | behavior | required | world | salient |  |
| O47 | PublicServiceDispatchProcess rng・pending | external | behavior | required |  |  |  |
| O48 | HotelProcess rooms_occupied・bed_cell | external | behavior | required |  |  |  |
| O49 | LargeEventProcess _inside | external | behavior | required | world | large_event |  |
| O50 | RailProcess occupancy・peak_ratio・_return | external | behavior | required | close_final, day_head, phase_c, world | rail |  |
| O51 | CrowdProcess queue_action | external | behavior | required |  |  |  |
| O52 | ShelfRestockProcess backroom・_acted_toda | external | behavior | required | world | delivery_inbound |  |
| O53 | WasteCollection _cursor・waste_g_collecte | external | no | required | world | street_cleaning, waste |  |
| O54 | RoadWorks blocked_cells・occupied_edges | external | no | required | world | road_works |  |
| O55 | LastMile delivered・_cum/BusTaxi・Traffic( | external | no | derivable | day_head, world | infra, last_mile, traffic |  |
| O56 | EnvironmentProcess replay_date・stratum・_ | external | behavior | derivable | world | environment |  |
| O57 | MoneyLedger _lines・_day | external | behavior | required | close_final, day_close, phase_c |  |  |
| O58 | MoneyLedger 生ログのリング(中身) | external | no | discardable | phase_c |  |  |
| O59 | GoodsLedger _shelf・_bin・_sold_today・_day | external | behavior | required | close_final, day_close, phase_c, world | waste |  |
| O60 | GoodsLedger 配達ログのリング | external | no | discardable | phase_c, world | waste |  |
| O61 | WorldProcessRunner log(ActualLog) | external | no | discardable |  |  |  |
| O62 | UndefinedActionRegistry log・counts・prece | external | no | discardable |  |  |  |
| O63 | PerceptionRenderer のキャッシュ _b1_cache〜_b4_ | external | no | derivable | decide |  |  |
| O64 | PerceptionRenderer の口 acquaintance_fn・me | external | no | discardable | decide, memory |  |  |
| O65 | LLMBridge・TapeWriter・FleetBridge の計数・行・処 | external | no | discardable |  |  |  |
| O66 | ActivityLayer の計数 | external | diag | discardable | activity_intent, detect, phase_a |  |  |
| O67 | FamiliarityLayer stats | external | diag | discardable |  |  |  |
| O68 | StoreChoice first_by_reason・visits_by_re | external | diag | discardable | memory |  |  |
| O69 | ClassicalPolicy n_calls | external | diag | discardable | decide |  |  |
| O70 | PlanExecutor の計数と時別の控え | external | diag | discardable | close_final, observe, plan_boundary, presence, world | large_event, presence.step, presence.step_plan_boundaries, rail |  |
| O71 | Arbiter の計数 | external | diag | discardable | arbiter |  |  |
| O72 | SalientProcess の計数 | external | diag | discardable | world | salient |  |
| O73 | 世界の過程と実行器の計数 | external | diag | discardable | close_final, phase_c, world | bus_taxi, crowd, delivery_inbound, environment, infra, large_event, last_mile, opening, press, rail, road_works, waste |  |
| O74 | RailProcess arrival_train・external_line( | external | behavior | required | world | large_event, rail |  |
| O75 | CrowdProcess occupancy・queue_len・flow | external | behavior | unknown | world | crowd |  |
| O76 | EnvironmentProcess daylight・heat_stage・w | external | behavior | derivable | world | environment |  |
| O77 | MoneyLedger _flow・_last_change_day・_snap | external | diag | required | close_final, day_close, phase_c |  |  |
| O78 | MoneyLedger rejections | external | diag | discardable |  |  |  |
| O79 | GoodsLedger _shelf_age・_household_sku | external | behavior | required | close_final, day_close, phase_c |  |  |
| O80 | GoodsLedger の保存則の項(_row_sku・_waste_sku・_ | external | diag | required | close_final, day_close, world | waste |  |
| O81 | GoodsLedger n_moves・rejections | external | diag | discardable | phase_c, world | waste |  |
| O82 | UndefinedActionRegistry proposals・vocabu | external | no | unknown |  |  |  |
| O83 | UndefinedActionRegistry の計数 | external | diag | discardable |  |  |  |
| O84 | PerceptionRenderer の計数 | external | diag | discardable | decide |  |  |
| O85 | LLMBridge _interned(テープへ書いた共有ブロック) | external | no | required |  |  |  |
| O86 | LLMBridge の計数 | external | diag | discardable | decide |  |  |
| O87 | TapeWriter の書き出し待ちの行と計数 | external | no | discardable |  |  |  |
| O88 | FleetBridge _interned | external | no | required |  |  |  |
| O89 | FleetBridge の計数 | external | diag | discardable |  |  |  |
| O90 | ClassicalPolicy _ipf_cache(15 分帯ごとの c_t  | external | behavior | required |  |  |  |
| O91 | ConversationManager n_opened(開いたセッションの数) | external | behavior | required | apply_responses |  |  |
| O92 | MoneyLedger 締めの基準と生ログの位置(_snap・_flow_dai | external | diag | required | close_final, day_close, phase_c |  |  |
| O93 | GoodsLedger 配達ログの位置(_dl_pos・_dl_head・_dl | external | diag | required | close_final, day_close, phase_c, world | waste |  |
| O94 | TargetResolver named_closed(名指しの店の即時閉店の控 | external | behavior | required |  |  |  |
| O95 | CrowdProcess flow_dir8・coherence(8 方位と向き | external | diag | unknown | world | crowd |  |
| O96 | run_day の局所 replay_inbox(再生の到着待ち) | external | no | required |  |  |  |
