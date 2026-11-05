# tests/engine/processes

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 17 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../tests/engine/processes/__init__.py)

(冒頭の説明なし)

## [conftest.py](../../../../../../../tests/engine/processes/conftest.py)

世界過程(C4 第1陣 前半)のテスト用フィクスチャ。

- 公開の関数とクラス
  - `fake_plan_assets`(関数): ``rows`` = ``[(poi, weekday, start, end), …]`` の営業時間 PlanSpec。
  - `fake_timetable_assets`(関数): 1 駅 2 路線・平日のみの最小時刻表を持つ ``ProcessAssets``。
  - `fake_weather_assets`(関数): 1 層 2 日・全時刻同じ暑さ段の気象資産(影グリッドは無し)。
  - `make_agents`(関数): 初期化済み(凍結済み)の個体状態と mock 日課。
  - `make_world`(関数)
- import している内部モジュール: `shibuya.agents.schedule`・`shibuya.agents.state`・`shibuya.engine.resolve`・`shibuya.world.assets`・`shibuya.world.state`
- 読む試験: `tests/engine/experiment/_x33.py`・`tests/engine/processes/test_absent_processes_1102.py`・`tests/engine/processes/test_civic.py`・`tests/engine/processes/test_crowd.py`・`tests/engine/processes/test_environment.py`・`tests/engine/processes/test_goods_flow.py`・`tests/engine/processes/test_logistics.py`・`tests/engine/processes/test_opening.py`・`tests/engine/processes/test_rail.py`・`tests/engine/processes/test_rail_board_intent.py`・`tests/engine/processes/test_rail_return.py`・`tests/engine/processes/test_rate_rules_1101.py`・`tests/engine/processes/test_rng_scheme_10c.py`・`tests/engine/processes/test_runner.py`・`tests/engine/processes/test_salient.py`・`tests/engine/processes/test_traffic.py`・`tests/engine/rights/test_rights_events.py`・`tests/engine/rights/test_staff_of_poi_equivalence.py`・`tests/engine/test_defect_fixes_1103.py`

## [test_absent_processes_1102.py](../../../../../../../tests/engine/processes/test_absent_processes_1102.py)

〔11-02r §1 #7〕「無い」と宣言した過程 5 件を止める切替口 ``engine.absent_processes`` の試験(過程ごとの正と負の対照)。

- 公開の関数とクラス
  - `arm_restore`(関数)
  - `test_cli_rejects_a_wrong_arm_name`(関数)
  - `test_collapse_still_happens_but_nobody_is_dispatched_when_stopped`(関数): 倒れる事象そのもの(rate_rules の collapse)はこの腕に依らない。止めた腕では出動も到着(警察の顕著行為)も無い。
  - `test_dispatch`(関数)
  - `test_infra`(関数)
  - `test_infra_peak_hour_is_minus_one_when_stopped`(関数): 〔検収 低-5〕止めた腕の山の時は −1(全部 0 の argmax=0 時に見せない)。旧道は 0〜23。
  - `test_resume_through_run_day_checks_the_arm`(関数): 〔検収 低-6〕run_day を通す再開: 同じ腕なら通しのランと final が同じ・違う腕なら止める(ValueError)。
  - `test_road_works`(関数)
  - `test_road_works_plan_is_the_same_in_both_arms`(関数)
  - `test_run_manifest_section`(関数)
  - `test_runner_hands_the_arm_to_the_five_processes`(関数)
  - `test_state_header_and_resume_check`(関数)
  - `test_street_cleaning_leaves_litter_when_stopped`(関数): ポイ捨ての旧道(rate_rules legacy)でごみを生じさせ、掃除の巡回の腕だけを変える。
  - `test_the_default_arm_is_stopped_and_names_are_checked`(関数)
  - `test_waste_collection`(関数)
  - `tiny_runs`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.core.time_consts`・`shibuya.engine.absent_processes`・`shibuya.engine.processes.civic`・`shibuya.engine.processes.goods_flow`・`shibuya.engine.processes.logistics`・`shibuya.engine.processes.runner`・`shibuya.engine.processes.salient`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.world.assets`・`shibuya.world.processes.absent`・`shibuya.world.processes.actual_log`・`tests/engine/processes/conftest.py`・`tests/engine/processes/test_goods_flow.py`
- 決定の ID: 11-02r・11-02r #7・11-02r/§1・11-02r/§1 #7・11-02r/§2-2・11-03/§3

## [test_civic.py](../../../../../../../tests/engine/processes/test_civic.py)

公共サービス出動・報道/公式発信・ホテル・インフラ・大規模イベントのテスト。

- 公開の関数とクラス
  - `test_dispatch_arrival_resolves_the_incident`(関数)
  - `test_dispatch_delay_is_lognormal_around_the_median`(関数)
  - `test_dispatch_rejects_an_unknown_cell`(関数)
  - `test_hotel_bed_lets_a_visitor_sleep_away_from_home`(関数): ``resolve._apply_sleep`` がホテルの客室を寝床として認める(満室なら ``NO_BED``)。
  - `test_hotel_checkin_is_capped_by_the_rooms_and_reports_no_bed`(関数)
  - `test_hotel_checkout_frees_the_rooms`(関数)
  - `test_hotel_rests_without_hotel_pois`(関数)
  - `test_infra_load_grows_with_occupancy_and_reports_a_peak`(関数)
  - `test_large_event_pulls_visitors_in_and_sends_them_back`(関数)
  - `test_press_is_due_only_at_the_fixed_minutes`(関数)
  - `test_press_line_carries_the_feature_tag_and_no_imperative`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.commit`・`shibuya.engine.processes.civic`・`shibuya.engine.resolve`・`shibuya.world.assets`・`tests/engine/processes/conftest.py`
- 決定の ID: 11-01・11-02r/§1・11-02r/§1 #7

## [test_crowd.py](../../../../../../../tests/engine/processes/test_crowd.py)

混雑場・流れ・屋内占有・待ち行列(D-R2-5 第1陣 + §7.2 初回実装)のテスト。

- 公開の関数とクラス
  - `test_apply_without_a_crowd_process_never_serves`(関数)
  - `test_buying_registers_occupancy_and_full_shops_queue`(関数)
  - `test_flow_dir8_is_quantised_into_eight_sectors`(関数)
  - `test_flow_is_coherent_when_everyone_heads_the_same_way`(関数)
  - `test_flow_is_still_when_nobody_moves`(関数)
  - `test_flow_vocabulary_has_three_values_like_the_renderer`(関数): レンダラの ``FLOW_WORDS`` は 3 値。8 方位は併置(描画には出さない)。
  - `test_mean_wait_is_finite_and_zero_without_a_queue`(関数)
  - `test_occupancy_is_released_after_the_dwell_limit`(関数)
  - `test_queue_balks_after_the_wait_threshold`(関数)
  - `test_queue_disbands_when_the_shop_closes`(関数)
  - `test_queue_is_served_fifo_when_a_seat_frees_up_d113_3`(関数)
  - `test_queue_rows_gives_the_b4b_material`(関数)
  - `test_queue_service_switch_off_keeps_the_old_behaviour`(関数)
  - `test_seats_are_derived_from_the_category`(関数)
  - `test_served_body_that_can_no_longer_pay_leaves_the_queue`(関数)
  - `test_waiting_bodies_take_the_seat_before_newcomers`(関数): FIFO: 空いた席は、この tick に来た買い手より先に並んでいた体が取る。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.commit`・`shibuya.engine.processes.crowd`・`shibuya.engine.resolve`・`shibuya.perception.templates`・`tests/engine/processes/conftest.py`
- 決定の ID: D-113・第 268

## [test_environment.py](../../../../../../../tests/engine/processes/test_environment.py)

昼夜・天候・体感温度(D-R2-5 第1陣 1-2 行目)のテスト。

- 公開の関数とクラス
  - `test_daylight_phase_follows_sunrise_and_sunset`(関数)
  - `test_replay_date_is_deterministic_and_inside_the_weekday_stratum`(関数)
  - `test_select_day_is_gone`(関数)
  - `test_shade_bit_is_read_per_cell`(関数): セルごとに日陰ビットを引く(全セル同値ではない)。
  - `test_shade_multiplies_the_thermal_by_the_contract_factor`(関数): 知覚契約書 §3「内受容 … 影グリッド(**係数0.86**)」。
  - `test_synthetic_world_falls_back_to_a_fixed_mild_day`(関数)
  - `test_thermal_follows_the_heat_stage_without_shade`(関数)
  - `test_thermal_is_evaluated_on_the_five_minute_grid`(関数): 正規化規約⑨(5 分丸め)= D-W10 の影グリッド刻みと同一。
- import している内部モジュール: `shibuya.engine.processes.environment`・`shibuya.world.assets`・`tests/engine/processes/conftest.py`
- 決定の ID: 第 330

## [test_goods_flow.py](../../../../../../../tests/engine/processes/test_goods_flow.py)

物の流れ(補充・納品・廃棄物収集・街路清掃)のテスト。

- 公開の関数とクラス
  - `test_delivery_delay_is_recorded_as_a_deviation`(関数)
  - `test_delivery_runs_once_per_store_inside_the_window`(関数)
  - `test_household_consumption_lands_in_the_sink`(関数)
  - `test_leftovers_go_to_the_bin_then_out_of_the_bbox`(関数)
  - `test_litter_rises_with_density_and_is_swept_on_the_shift`(関数)
  - `test_reorder_point_is_the_declared_fill_ratio`(関数)
  - `test_restock_moves_goods_and_pays_the_import_leg`(関数)
  - `test_restock_needs_backroom_stock`(関数): 行動契約書 §2.2 の失敗語彙「バックヤードに在庫なし」が立つ。
  - `test_restock_permission_is_staff_in_the_same_cell`(関数)
  - `test_shelf_rests_without_a_goods_ledger`(関数)
  - `test_waste_band_is_reported_even_when_out_of_band`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.economy.accounts`・`shibuya.economy.goods`・`shibuya.economy.ledger`・`shibuya.engine.ledger_api`・`shibuya.engine.processes.goods_flow`・`shibuya.engine.processes.opening`・`shibuya.engine.resolve`・`shibuya.world.assets`・`tests/engine/processes/conftest.py`
- 読む試験: `tests/engine/processes/test_absent_processes_1102.py`・`tests/engine/processes/test_rate_rules_1101.py`
- 決定の ID: 11-01・11-02r/§1・11-02r/§1 #7

## [test_logistics.py](../../../../../../../tests/engine/processes/test_logistics.py)

宅配ラストマイル・バス/タクシー・道路工事(§7.2 前倒し)のテスト。

- 公開の関数とクラス
  - `test_bus_arrives_on_an_equal_interval_plan`(関数)
  - `test_bus_rests_without_stop_data`(関数)
  - `test_bus_stops_come_from_osm_and_land_on_cells`(関数): OSM の ``highway=bus_stop`` 127 点がセルへ写像される(座標欠落は幹線へ置く=expedient)。
  - `test_parcels_are_delivered_on_the_hourly_curve`(関数)
  - `test_parcels_are_the_ward_number_scaled_by_the_bbox_area`(関数)
  - `test_parcels_follow_the_household_weights`(関数)
  - `test_road_works_occupy_at_night_and_clear_in_the_morning`(関数)
  - `test_road_works_rest_without_road_data`(関数)
- import している内部モジュール: `shibuya.engine.processes.logistics`・`shibuya.world.assets`・`shibuya.world.state`・`tests/engine/processes/conftest.py`
- 決定の ID: 11-01・11-02r/§1・11-02r/§1 #7

## [test_opening.py](../../../../../../../tests/engine/processes/test_opening.py)

営業時間 PlanSpec と役割行動「開閉店」(D-R2-5 第1陣 6 行目)のテスト。

- 公開の関数とクラス
  - `test_engine_rule_fallback_is_counted`(関数): §1 末尾のフォールバック台帳=``executor=engine_rule`` の行。
  - `test_flags_follow_the_plan_and_override_the_c2_default`(関数)
  - `test_has_permission_requires_staff_kind_and_same_cell`(関数)
  - `test_inactive_without_a_plan_spec`(関数)
  - `test_open_close_without_permission_is_not_stopped`(関数): 〔第 1 期 1-5・CP3・検収 L2〕権利の無い開閉も止めない(旗は確定・結果は OK)。許可のない行動の印は出来事の
  - `test_open_matrix_follows_the_intervals`(関数)
  - `test_open_matrix_selects_the_weekday`(関数)
  - `test_open_matrix_wraps_intervals_past_midnight`(関数): W7 の ``end`` は 1440 超(日跨ぎ)がある(実データで 1,918 区間)。
  - `test_role_action_is_used_when_the_staff_is_on_site`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.processes.opening`・`shibuya.engine.resolve`・`shibuya.world.assets`・`tests/engine/processes/conftest.py`

## [test_rail.py](../../../../../../../tests/engine/processes/test_rail.py)

鉄道運行(D-R2-5 第1陣 3 行目)+ 乗車/降車(行動契約書 §2.1・運用設計書 §2.6)のテスト。

- 公開の関数とクラス
  - `test_accept_quota_is_capped_by_two_hundred_percent`(関数)
  - `test_accept_rate_matches_the_run_manifest_section_2_6`(関数)
  - `test_alight_succeeds_only_while_the_train_is_at_the_platform`(関数)
  - `test_alight_when_the_train_does_not_stop_returns_no_stop`(関数)
  - `test_alight_without_rail_is_no_stop_c2_compatible`(関数)
  - `test_boarding_in_another_cell_walks_to_the_nearest_platform`(関数): **D-51 (b)**: ホーム以外で乗車を選ぶと、世界が最寄りホームへの移動を組む。
  - `test_boarding_over_the_congestion_cap_returns_train_full`(関数)
  - `test_boarding_succeeds_on_the_platform_and_pays_the_fare`(関数)
  - `test_boarding_without_a_train_waits_on_the_platform`(関数): **D-51 (a)**: 列車が居なくても失敗にせず、ホームで待つ(意図が消えない)。
  - `test_boarding_without_the_fare_returns_fare_short`(関数)
  - `test_carry_out_account_code_matches_economy`(関数): ``engine`` は科目名を知らない=**番号だけ**を持つ。値の一致はここで強制する。
  - `test_congestion_caps_are_the_official_values`(関数): 線別混雑率上限(D10′ の照合対象)。**D-51 で 5 行を令和7年度(2025)実績へ更新**。
  - `test_daily_train_count_matches_the_real_timetable_rows_for_that_calendar`(関数): ゲート: 路線別の便数が W12 のその暦の行数と一致する。
  - `test_dep_ticks_are_sorted_for_the_searchsorted_window`(関数)
  - `test_departure_moves_riders_to_the_external_node`(関数)
  - `test_departures_are_logged_as_scheduled`(関数)
  - `test_dwell_is_a_per_line_table_terminal_is_two_ticks`(関数): D-51 (c): 通過型 1 tick(60 秒)・終端(銀座線・井の頭線)2 tick。
  - `test_left_behind_is_counted_as_a_diagnostic_row`(関数): §2.6 (iii) 乗り残しの診断行(``left_behind`` / ``left_behind_rate``)。
  - `test_riders_are_never_lost`(関数)
  - `test_trains_at_platform_covers_the_dwell_window`(関数)
  - `test_trains_per_line_matches_the_timetable_rows`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.economy.accounts`・`shibuya.engine.commit`・`shibuya.engine.processes.rail`・`shibuya.engine.resolve`・`shibuya.world.assets`・`shibuya.world.processes.actual_log`・`shibuya.world.state`・`tests/engine/processes/conftest.py`
- 決定の ID: D-51

## [test_rail_board_intent.py](../../../../../../../tests/engine/processes/test_rail_board_intent.py)

D-51 乗車の意図保持(2026-09-10・ユーザー決定 (c))のテスト。

- 公開の関数とクラス
  - `test_an_intent_that_stopped_walking_is_swept`(関数): 自分の行動以外(会話に引き込まれた等)で歩みが止まった意図は掃除される。
  - `test_another_action_drops_the_intent_but_wait_keeps_it`(関数)
  - `test_board_without_rail_is_no_train_c2_compatible`(関数)
  - `test_fare_short_drops_the_intent`(関数)
  - `test_off_platform_board_walks_waits_and_boards_on_the_fixed_tick_sequence`(関数): ホーム外で乗車 → 4 tick 歩く → 待つ → 発車 tick に乗る(tick 列を固定)。
  - `test_queue_is_served_fifo_and_capped_by_the_accept_quota`(関数): ``board_since`` 昇順 → agent_id 昇順。乗れなかった体は**待ち続ける**。
  - `test_riders_are_conserved_and_no_one_is_left_riding`(関数): 3 値の和 = 個体数(毎 tick)・最終発車のあと **RIDING は 0**。
  - `test_riding_agents_cannot_board_again`(関数)
  - `test_the_rest_of_the_queue_boards_the_next_train`(関数)
  - `test_the_walk_is_deterministic_for_the_same_situation`(関数): 同じ状況を 2 回作ると ``state_hash`` が一致する(T2・決定論)。
  - `test_waiting_is_cut_off_after_the_limit_and_returns_no_train`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.commit`・`shibuya.engine.processes.rail`・`shibuya.engine.resolve`・`tests/engine/processes/conftest.py`
- 決定の ID: D-51

## [test_rail_return.py](../../../../../../../tests/engine/processes/test_rail_return.py)

D-61 域内居住者の帰りの便(2026-09-10・ユーザー決定 (a))のテスト。

- 公開の関数とクラス
  - `test_activities_outside_the_bbox_do_not_call_the_rider_back`(関数): ``place_kind == 域外`` の活動は域内活動ではない(域外に居たままでよい)。
  - `test_apply_to_mock_schedule_attaches_the_weekly_table_for_the_rail_process`(関数): D-61 の結線: ``run.py`` を変えずに鉄道へ週次表を届ける口。
  - `test_event_arrivals_are_dropped_from_the_return_queue`(関数): 18:00 に会場へ引き込まれた体の**古い割当**は発火しない(二重到着・早戻りなし)。
  - `test_event_leavers_get_a_return_train`(関数): 21:00 の退場(``rail_depart`` 直呼び)にも帰りの便が付く。
  - `test_external_residents_are_never_assigned_a_return_train`(関数): 域外居住者が乗って出ても、帰りの便は**割り当てない**(事前割当の便で戻る)。
  - `test_home_in_bbox_rider_returns_on_the_first_train_after_the_next_activity`(関数): 次の域内活動が 250 分 → ``enter_tick >= 250`` の最初の便(300)で降りる。
  - `test_inbound_starts_skips_only_outside_activities_and_orders_by_minute`(関数): **D-61 追補**: 落とすのは ``place_kind == 域外`` の行だけ(未解決セルは残す)。
  - `test_rider_conservation_holds_on_every_tick`(関数): 在圏 + 乗車中 + 域外 = 個体数(全 tick)。
  - `test_rider_whose_activity_is_after_the_last_train_stays_outside`(関数): 終電後(``want`` 以降にホームへ入る便が無い)も戻らない=``return_no_train``。
  - `test_rider_without_a_next_in_bbox_activity_stays_outside`(関数)
  - `test_the_static_pre_assignment_of_external_residents_still_works`(関数): 域外居住者の**事前割当**(``_arr_order``/``_arr_start``)は帰りの便と混ざらない。
  - `test_the_train_chosen_is_the_earliest_one_at_or_after_the_activity_start`(関数): 開始 200 ちょうど → ``enter_tick == 200`` の便(その時刻の便を飛ばさない)。
  - `test_two_identical_runs_agree_bit_for_bit`(関数)
  - `test_unresolved_cell_activities_still_call_the_rider_back`(関数): **(vi) D-61 追補**: ``target_cell < 0`` でも ``place_kind != 域外`` なら域内活動。
  - `test_without_a_weekly_table_nobody_comes_back`(関数): 週次表の無いラン(合成世界・``--no-population``)= D-61 前の挙動のまま。
- import している内部モジュール: `shibuya.agents.schedule`・`shibuya.agents.weekly`・`shibuya.engine.commit`・`shibuya.engine.processes.civic`・`shibuya.engine.processes.rail`・`shibuya.engine.resolve`・`tests/engine/processes/conftest.py`
- 決定の ID: 11-01・D-61

## [test_rate_rules_1101.py](../../../../../../../tests/engine/processes/test_rate_rules_1101.py)

〔11-01 段 2 の 3・4〕率の形の規則を外す切替口 ``engine.rate_rules`` の試験(規則ごとの正と負の対照)。

- 公開の関数とクラス
  - `arm_restore`(関数)
  - `day_runs`(関数): 〔検収 L2〕世界資産(台帳つき)の 200 体で 1 日(1,440 刻み)=05:00 の売れ残り・05〜08 時の納品・08〜21 時の宅配・
  - `test_attendance_rate_is_gone_from_run_day_and_the_cli`(関数)
  - `test_calvo_is_not_wired_into_the_engine`(関数): ``economy.pricing`` の Calvo の口は src のどこからも呼ばれていない(結線しない=価格は固定)。
  - `test_collapse_off_over_a_day_has_no_events_but_legacy_does`(関数)
  - `test_collapse_rate_is_zero_off_and_three_legacy`(関数)
  - `test_event_injection`(関数)
  - `test_leftover_waste`(関数)
  - `test_legacy_refuses_by_the_acceptance_rate`(関数)
  - `test_legacy_spreads_the_arrivals`(関数)
  - `test_litter`(関数)
  - `test_negative_calvo_wiring_is_caught_through_aliases`(関数): 負の対照: 別名の import・相対の import・完全修飾の呼び出し・from import を植えると捕まる。
  - `test_off_everyone_takes_the_latest_train_that_is_in_time`(関数)
  - `test_off_keeps_only_the_two_hundred_percent_cap`(関数)
  - `test_parcels`(関数)
  - `test_run_manifest_counts_rise_in_legacy_and_are_zero_off`(関数): 〔検収 L2〕同じ 1 日のランで、旧道は催し・売れ残り・ポイ捨て・宅配の件数が立ち、off は全部 0(倒れる率は off で 0)。
  - `test_state_header_and_resume_check`(関数)
  - `test_the_default_arm_is_off_and_names_are_checked`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.presence`・`shibuya.engine.processes.civic`・`shibuya.engine.processes.goods_flow`・`shibuya.engine.processes.logistics`・`shibuya.engine.processes.rail`・`shibuya.engine.processes.salient`・`shibuya.engine.rate_rules`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.world.processes.actual_log`・`tests/engine/processes/conftest.py`・`tests/engine/processes/test_goods_flow.py`・`tests/engine/test_presence_executor.py`
- 決定の ID: 11-01・11-02r/§1・11-02r/§1 #7

## [test_rng_scheme_10c.py](../../../../../../../tests/engine/processes/test_rng_scheme_10c.py)

10c: 状態を持つ乱数 2 本(顕著行為の発生・出動の遅れ)をカウンタ型にする(10c の切替口 ``rng_scheme``)。

- 公開の関数とクラス
  - `poisson_z`(関数): tick ごとの件数(ポアソン・期待値 ``lam``)→ (合計の z, 分散の指数の z)。
  - `test_a_tape_from_before_10e_is_not_replayed`(関数): 〔改訂(第330・RET)〕前は「記録の無いテープ(10c より前)は stateful とみなして警告 1 回で再生する」。stateful を
  - `test_cli_flag_is_shared_by_engine_run_and_cli`(関数): 〔改訂(第330・RET)〕``--rng-scheme`` を消した(渡すと argparse が止める)。暦の引数の口は engine.run と cli で同じ。
  - `test_counter_adds_no_state_to_restore_and_drops_the_two_generators`(関数): 〔改訂(第330・RET)〕前は stateful のランと道筋ごとに比べた(stateful を消した)。いまは: 2 つの道筋は「無い」の印
  - `test_counter_calls_the_dispatch_in_ascending_agent_id`(関数)
  - `test_counter_collapse_at_T_does_not_depend_on_earlier_ticks`(関数): 〔改訂(第330・RET)〕前は後半で「stateful は前の tick を回したかで変わる」を比べた(stateful を消した)。
  - `test_counter_dispatch_delay_depends_only_on_T_cell_k`(関数): 状態を持たない: 前に何件出動したかで (T, セル, k) の引きが変わらない(通し番号を使っていない)。
  - `test_counter_dispatches_in_one_cell_and_tick_draw_different_delays`(関数): ``test_civic.py`` の 400 件(同じ tick・16 セル × 25 件)を counter で。
  - `test_counter_k_restarts_for_each_tick_and_cell`(関数)
  - `test_counter_keeps_no_generator`(関数): 〔改訂(第330・RET)〕前は「stateful は Generator を持ち counter は持たない」。stateful を消したので、どの過程も
  - `test_counter_run_twice_is_identical`(関数): 〔改訂(第330・RET)〕前は最後に「stateful に変えると引きが変わる」を見た(stateful を消した)。
  - `test_counter_streams_have_their_own_names_and_word0_is_zero`(関数): 検収 M3・M9: counter の用途名は stateful と別・カウンタの 1 語目は 0(単体で守る)。
  - `test_day_key0_enters_the_key`(関数): 検収 T2: ``--day`` が違うランは counter の乱数が違う(鍵から ``day_key(0)`` を落とすと落ちる)。
  - `test_per_tick_counts_match_the_known_poisson_rate`(関数): 〔改訂(第330・RET)〕前は stateful と counter の両方で見た(stateful を消した=counter だけ)。
  - `test_poisson_z_catches_a_ten_percent_lower_rate`(関数): 線の検出力の既知の答え: 期待値 1,500 件に対して 10% 少ない率なら合計の z < −3。
  - `test_run_day_has_no_scheme_argument_and_writes_the_manifest`(関数): 〔改訂(第330・RET)〕切替口 ``rng_scheme`` を消した(渡すと TypeError)。manifest の ``rng_scheme`` は counter の記録。
  - `test_run_day_passes_day_key0_to_the_counter_key`(関数): 検収 T2(ランの経路): 顕著行為の鍵の時刻は ``day_key(0)`` × 1,440 + T。
  - `test_run_tick_key_is_day_key_times_ticks_per_day_plus_T`(関数)
  - `test_run_tick_key_multiplies_by_the_ticks_per_day_not_1440`(関数): 検収 T1: tick 30 秒なら 1 日の tick 数は 2,880(定数 1,440 にすると落ちる)。
  - `test_scheme_values_and_default_is_counter`(関数)
  - `test_the_tape_carries_the_scheme_and_the_replay_matches`(関数): 〔改訂(第330・RET)〕前は「counter で録って stateful で再生すると止まる」「stateful のテープ」も見た(消した)。
  - `test_two_day_counter_keys_carry_T`(関数): (v) 2 日目の顕著行為と出動の鍵が 1 日目と違う(T が鍵に入っている)。〔改訂(第330・RET)〕前は最後に
- import している内部モジュール: `shibuya.cli`・`shibuya.core.rng`・`shibuya.engine.absent_processes`・`shibuya.engine.processes.civic`・`shibuya.engine.processes.salient`・`shibuya.engine.rate_rules`・`shibuya.engine.run`・`shibuya.engine.state_hashes`・`shibuya.engine.state_ledger`・`shibuya.engine.systems.state_io`・`shibuya.engine.tape`・`tests/engine/processes/conftest.py`・`tests/engine/test_tape_wiring.py`
- 読む試験: `tests/engine/test_env_and_sections_10f.py`
- 決定の ID: 11-01・11-02r/§1・11-02r/§1 #7・第 330

## [test_runner.py](../../../../../../../tests/engine/processes/test_runner.py)

世界過程の実行器(台帳 → 実装の橋)のテスト。

- 公開の関数とクラス
  - `test_a_registry_that_fails_constitution_5_cannot_run`(関数): 届き先(reaches/contributes)の実在検査に落ちる台帳では過程を動かせない。
  - `test_actual_log_records_departures_and_compliance_is_computable`(関数)
  - `test_constitution_check_runs_at_construction`(関数)
  - `test_enabled_selects_only_the_named_processes`(関数)
  - `test_every_declared_process_id_exists_in_the_ledger`(関数): 実装が名乗る過程 id は全て台帳(first_batch)に実在する。
  - `test_flow_is_exposed_for_the_renderer`(関数)
  - `test_process_modules_do_not_import_build_or_economy`(関数): 層契約: engine → world/agents/perception/llm/core/manifest。build/economy は不可。
  - `test_process_modules_never_open_a_write_window`(関数): ``.writable(`` / ``.thaw(`` を呼ぶのは resolve だけ(世界過程も例外にしない)。
  - `test_processes_can_be_disabled_by_ablation_id`(関数)
  - `test_processes_can_be_disabled_by_process_id`(関数)
  - `test_registry_hash_is_exposed_and_stable`(関数)
  - `test_riders_are_conserved_from_the_start`(関数)
  - `test_step_accumulates_per_process_wall_time_and_counters`(関数)
- import している内部モジュール: `shibuya.engine.processes.runner`・`shibuya.world.processes.first_batch`・`tests/engine/processes/conftest.py`

## [test_salient.py](../../../../../../../tests/engine/processes/test_salient.py)

顕著行為(人物③)と ``p_notice`` の結線のテスト。

- 公開の関数とクラス
  - `test_a_collapse_triggers_a_dispatch_and_the_arrival_is_salient`(関数)
  - `test_ablation_a0_uses_the_constant_reach`(関数): A0(定数 0.54)では距離・向きに依らず約半数が気づく。
  - `test_ablation_ids_map_to_the_five_stages`(関数)
  - `test_broadcasts_do_not_consume_the_salient_event_budget`(関数): 放送は人物③ではない: 200/tick の顕著イベント予算も p_notice も通さない。
  - `test_candidates_come_from_the_same_cell_and_its_neighbours`(関数)
  - `test_cell_lines_are_capped_by_the_stage_two_budget`(関数)
  - `test_collapse_events_reach_someone_and_wake_them`(関数)
  - `test_cross_neighbours_are_the_four_orthogonal_cells`(関数)
  - `test_event_budget_caps_two_hundred_per_tick`(関数)
  - `test_event_seen_tick_marks_everyone_in_the_event_cell_d113_2`(関数): 事象のセルに居た全員(B4 に行が出た体)の ``event_seen_tick`` がその tick になる。
  - `test_event_seen_within_uses_an_inclusive_window`(関数)
  - `test_notice_state_is_two_bytes_per_agent_and_written_through_resolve`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.core.types`・`shibuya.engine.absent_processes`・`shibuya.engine.processes.civic`・`shibuya.engine.processes.salient`・`shibuya.engine.rate_rules`・`shibuya.perception.attention`・`shibuya.perception.p_notice`・`tests/engine/processes/conftest.py`
- 決定の ID: 11-01・11-02r/§1・11-02r/§1 #7・D-113・第 267

## [test_traffic.py](../../../../../../../tests/engine/processes/test_traffic.py)

断面自動車交通(§7.2 初回実装・C 類 + B 類域外発生)のテスト。

- 公開の関数とクラス
  - `test_cell_aggregate_matches_the_edge_sum`(関数)
  - `test_daily_vehicle_km_and_through_share`(関数)
  - `test_day12_window_carries_the_census_day_volume`(関数)
  - `test_hourly_sums_equal_the_24h_volume`(関数): 検算: Σ_h 時間帯別交通量 = 24 時間交通量。
  - `test_inactive_without_road_assets`(関数)
  - `test_klass_defaults_match_the_w10_header`(関数): ``build`` は実行時に import できないので値を転記した。ずれを機械検査する。
  - `test_non_road_klasses_carry_no_traffic`(関数)
  - `test_step_only_switches_on_the_hour`(関数)
- import している内部モジュール: `shibuya.engine.processes.traffic`・`shibuya.world.assets`・`tests/engine/processes/conftest.py`
