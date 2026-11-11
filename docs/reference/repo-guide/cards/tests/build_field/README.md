# tests/build_field

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 8 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../tests/build_field/__init__.py)

(冒頭の説明なし)

## [test_field_pipeline.py](../../../../../../tests/build_field/test_field_pipeline.py)

build.field の統合テスト(実データ必須・CI では skip)。

- 公開の関数とクラス
  - `built`(関数)
  - `test_all_stages_present_in_w_order`(関数)
  - `test_build_is_fast_enough`(関数)
  - `test_headers_declare_expedients_and_catalog`(関数)
  - `test_only_known_gates_fail`(関数)
  - `test_rebuild_is_byte_identical`(関数)
  - `test_w10_calibration_all_seven_points_within_3db`(関数): D-W11 の完了条件: **R5 の7点すべて**で残差 ≤3 dB(宣言値)。
  - `test_w10_noise`(関数)
  - `test_w12_external_nodes`(関数)
  - `test_w13_weather`(関数)
  - `test_w7_plan_spec`(関数)
- import している内部モジュール: `shibuya.build.geo.common`・`shibuya.build.run`・`tests/_data_ids.py`
- 決定の ID: 第 330

## [test_field_units.py](../../../../../../tests/build_field/test_field_units.py)

build.field の単体テスト(データ不要・CI で常に走る)。

- 公開の関数とクラス
  - `test_category_defaults_cover_every_catsub_pair_w6_can_emit`(関数): W6 が出しうる (cat, subcat) 対は全部 CATEGORY_DEFAULTS にある。
  - `test_citation_article_numbers_are_fixed`(関数): 答申 §3 ②: 規則6条2項は**時**(午前1時)・地域は 条例4条の2第2項+規則5条+告示。
  - `test_day_weather_type_rules`(関数)
  - `test_daylight_phase_vocabulary`(関数)
  - `test_db_helpers`(関数)
  - `test_default_week_respects_closed_days`(関数)
  - `test_equal_interval_departures_headways`(関数)
  - `test_equal_interval_departures_hourly_count_equals_declared`(関数): 〔改訂(第330)・答え 10-12b 1-1〕1 時間の本数=宣言(60 の約数でない本数でも)。
  - `test_equal_interval_departures_pm_peak_defaults_to_am`(関数): D-W14 の本数表は朝ピークのみ=夕ピークは朝と同数に置く(明示の既定値)。
  - `test_equinox_day_length_is_about_12h`(関数)
  - `test_expedients_ledger_registers_the_law_gaps`(関数): 答申 §3 の ①⑦⑧④ が expedient 台帳に載っていること(方法論「全cap/近似にタグ」)。
  - `test_geometry_factor_lane_positions`(関数)
  - `test_hour_shares_sum_to_one`(関数)
  - `test_hour_weather_vocabulary`(関数)
  - `test_hourly_flows_split`(関数)
  - `test_intervals_in_prohibited_window_is_zero_after_apply`(関数): 適用後の不変条件(ゲート intervals_over_law_cap_after_apply)を関数の水準で。
  - `test_l_wa_hand_computed`(関数)
  - `test_l_wa_speed_clamped_for_nonsteady`(関数)
  - `test_laeq_at_is_energy_sum_over_lanes`(関数)
  - `test_lane_energy_coeff_matches_written_formula`(関数)
  - `test_law_cap_clips_opening_side_pachinko`(関数): D-W8 ぱちんこ 4号=23:00-翌10:00 営業不可 → 09:00-23:30 は 10:00-23:00 になる。
  - `test_law_cap_game_center_splits_24h`(関数): ゲームセンター 5号=1:00-10:00 営業不可 → 24時間営業は 0:00-1:00 と 10:00-24:00 に割れる。
  - `test_law_cap_none_is_identity`(関数)
  - `test_law_cap_opening_side_by_law_key`(関数): 開店側の切り上げ(D-W8 の営業不可時間欄)を業態ごとに1本ずつ。
  - `test_law_cap_truncates_and_drops`(関数)
  - `test_law_cap_values_match_dw8_table`(関数)
  - `test_law_key_for_new_subcats_falls_back_to_the_cat`(関数): 新しい subcat は法規上限表に行を持たない=cat の行に落ちる(上限は動かない)。
  - `test_law_key_prefers_osm_tag`(関数)
  - `test_minor_entry_limit_is_still_mapped_to_three_and_four_only`(関数): ⑧ は**登録だけ**(写像は足さない=生成値が動かない)。
  - `test_new_subcat_rows_inherit_the_parent_cat_row`(関数): 足した subcat 行は親 cat の行をそのまま継ぐ。
  - `test_node_defs_shape`(関数)
  - `test_noise_stage_boundaries_pegged_to_environmental_standard`(関数)
  - `test_normalize_jp_route_names`(関数)
  - `test_offpeak_ratio_from_uses_own_rows`(関数): 平日と土休は**別の行集合**から同じ式で比を導く(土休が平日の値を借りない)。
  - `test_parse_holiday_hours`(関数): 〔改訂(第330 B6)〕PH(祝日)の規則を祝日の 1 日ぶんの区間として拾う(週表は変えない)。
  - `test_parse_opening_hours_comma_separated_rules`(関数): ``Mo-Fr …, Sa …`` は規則の並び・``Mo-Th, Su …`` は曜日の列挙(割らない)。
  - `test_parse_opening_hours_day_ranges`(関数)
  - `test_parse_opening_hours_off`(関数)
  - `test_parse_opening_hours_uniform`(関数)
  - `test_parse_opening_hours_unsupported`(関数)
  - `test_partial_run_does_not_touch_build_manifest`(関数): 一部段階だけのランは build_manifest.json を書き換えず partial を書く。
  - `test_prohibited_window_expansion_repeats_daily`(関数): 営業不可窓は毎日繰り返す(23:00-翌10:00 は当日 0:00-10:00 でもある)。
  - `test_propagation_at_10m`(関数)
  - `test_rail_flows_uses_total_ticket_only`(関数)
  - `test_read_etrn_10min_csv_buckets_like_the_amedas_json`(関数): 観測の時刻の時で畳む(01:00=1 時台)・24:00 は翌日の 0 時台・夜の日照の空欄=0・窓の外は捨てる。
  - `test_read_holidays_csv`(関数)
  - `test_route_match_prefix_and_city`(関数)
  - `test_season_of_matches_the_engine_calendar`(関数): build は engine を import しない。表の写しがエンジンの気象庁の区分と一致すること。
  - `test_select_day_deterministic`(関数)
  - `test_select_day_varies_with_seed`(関数)
  - `test_service_day_minutes`(関数)
  - `test_solar_elevation_peaks_near_local_noon`(関数)
  - `test_stage_order_is_numeric`(関数)
  - `test_street_points_on_a_single_edge`(関数)
  - `test_sun_times_within_3_min_of_published_tokyo_values`(関数)
  - `test_time_bin_mapping`(関数)
  - `test_violability_rule_is_unchanged_so_the_parquet_does_not_move`(関数): ③ は**保留**(D-72)。窓の有無で決める規則のままであること=生成列が動かない。
  - `test_w13_window_constant_and_inputs`(関数): 〔改訂(第330 B5)〕窓は定数・入力は窓の名前の CSV 2 本と祝日 CSV だけ(rglob をやめた)。
  - `test_wbgt_and_heat_stage`(関数)
  - `test_weekday_kind_holiday`(関数)
  - `test_write_build_manifest_without_stages_run_is_full`(関数): 既定(stages_run=None)は「全段階を走らせた」= 従来どおり build_manifest.json。
- import している内部モジュール: `shibuya.build.field.common`・`shibuya.build.field.street_grid`・`shibuya.build.field.w10_noise`・`shibuya.build.field.w12_external_nodes`・`shibuya.build.field.w13_weather`・`shibuya.build.field.w7_planspec`・`shibuya.build.geo.poi_class`・`shibuya.build.run`・`shibuya.engine.calendar`
- 決定の ID: 10-12b・D-72・第 330

## [test_w10_road_names.py](../../../../../../tests/build_field/test_w10_road_names.py)

段 1c(D-1 (a)): W10 の道路名の突合(``build.field.road_names``)と W10 の切替口。

- 公開の関数とクラス
  - `test_census_key_rules`(関数)
  - `test_edge_midpoints_are_arc_length_midpoints`(関数)
  - `test_match_report_counts_road_edges_only_in_the_totals`(関数)
  - `test_q7_restricts_candidates_to_named_ways_of_the_same_class`(関数): 段 1c′ Q7: 住宅地の辺は隣の幹線(名前つき・6 m)にも、名前の無い自分の way にも写らない。
  - `test_q9_restricts_candidates_to_the_same_band`(関数): 段 1c′ Q9: 地上(GL)の辺は真上の高架(DECK)の way を拾わず、同じ層の way を拾う。
  - `test_sections_for_key_uses_the_ward_order_and_road_kind`(関数)
  - `test_the_filters_need_the_edge_attributes`(関数)
  - `test_the_nearest_way_wins_even_if_it_has_no_name`(関数): 自分の way(名前なし・0 m)の隣を幹線(名前あり・6 m)が走っても、幹線の名前を拾わない。
  - `test_w10_declares_the_switch_and_the_input`(関数)
  - `test_w10_off_noise_field_equals_the_pre_1c_asset`(関数): OFF の騒音場 4 本は、段 1c 前の資産(W10 1.0.0 の出力)とバイト一致する。
  - `test_w10_refined_q7_q9_on_real_data`(関数): 段 1c′: Q7+Q9 の絞り込みで当てうる辺 246 → 225・primary+secondary 190 → 202。
  - `test_w10_road_name_match_on_real_data`(関数): 実データ: 写像率・名寄せ・primary/secondary 190/202・残差は突合に依存しない・OFF は当てない。
  - `test_way_band_follows_layer_then_tunnel_and_bridge`(関数)
- import している内部モジュール: `shibuya.build.field.common`・`shibuya.build.field.road_names`・`shibuya.build.field.w10_noise`・`tests/_data_ids.py`
- 決定の ID: 09-30・D-1・第 284・第 330

## [test_w10_ruler.py](../../../../../../tests/build_field/test_w10_ruler.py)

W10 の物差し(W10 の Q6・2026-09-30)と ON+Q7 のゲート(W10 の Q7)。

- 公開の関数とクラス
  - `test_address_forms_become_status_codes_not_exceptions`(関数)
  - `test_chome_name_from_address`(関数)
  - `test_chome_name_from_address_raises_only_when_unparseable`(関数)
  - `test_default_on_q7_reproduces_the_promoted_w10_outputs`(関数): 〔改訂(第330 B4)〕既定(ON+Q7)の W10 の出力 6 本は、昇格版の build_manifest の sha256 と一致する。
  - `test_kanji_number`(関数)
  - `test_measure_near_marks_road_values_beyond_the_grid_band`(関数): 道路から ROAD_BAND_M(8 m・D-W9)より遠い格子の値は、値を残して印を付ける。
  - `test_measure_near_rejects_nan`(関数)
  - `test_measure_near_returns_known_values`(関数)
  - `test_measure_near_ties_pick_one_grid_point_for_day_and_night`(関数): 同距離(0.5 m)の 2 点: 格子の番号の小さい方(添字 1)を採り、昼も夜も同じ点から読む。
  - `test_on_q7_gates`(関数): ON+Q7(W10 の Q7): 当てた辺 225・primary+secondary 202/202(PASS)・階級の不一致 0・最大 10 倍。
  - `test_parse_address`(関数)
  - `test_points_to_segments_min_dist`(関数)
  - `test_polygon_centroid_of_an_l_shape`(関数)
  - `test_projection_uses_the_canonical_function`(関数): 小地域の投影は正典 ``geo.common.latlon_to_local`` と同じ値(写しを持たない)。
  - `test_raising_one_grid_point_moves_only_the_max_of_the_radii_that_contain_it`(関数): 幾何が効く検算: (0, 80) の service 点(e-Stat の点から 80 m)だけを +20 dB すると、
  - `test_road_facing_point_ties_take_the_lower_grid_index`(関数)
  - `test_ruler_places_the_five_shibuya_points_on_the_promoted_field`(関数)
  - `test_ruler_rows_returns_the_known_difference_on_a_synthetic_field`(関数)
  - `test_ruler_rows_shifts_exactly_with_the_field`(関数): 騒音場を一様に +k dB すると、全ての差がちょうど +k 動く(物差しの線形性)。
  - `test_ruler_values_on_the_off_field`(関数): README §W10 の見出しの数値(段 1c の昇格版=OFF の騒音場)を固定する。
  - `test_ruler_values_on_the_on_q7_field`(関数): ON+Q7 の騒音場で物差しが最も動く所: No.82 の road_facing/max/r25 が +7/+6 → +5/+3(夜 −3)。
  - `test_summarize_diffs`(関数)
  - `test_switch_off_reproduces_the_pre_10e_w10_outputs`(関数): 〔改訂(第330 B4)〕切替口 OFF(旧値の再現)の W10 の出力 6 本は、段 1c の資産の sha256 と一致する。
- import している内部モジュール: `shibuya.build.field.common`・`shibuya.build.field.road_names`・`shibuya.build.field.w10_noise`・`shibuya.build.field.w10_ruler`・`shibuya.build.geo.common`・`shibuya.build.pop.shapefile`・`tests/_data_ids.py`
- 決定の ID: 第 330

## [test_w12_keio_switch_2_4.py](../../../../../../tests/build_field/test_w12_keio_switch_2_4.py)

〔第 2 期 2-4 V1〕W12 の京王(ODPT チャレンジ枠)の切替口 ``w12_real_timetables.USE_ODPT_CHALLENGE``。

- 公開の関数とクラス
  - `test_switch_default_reads_every_table`(関数)
  - `test_switch_off_drops_only_the_challenge_tables`(関数)
  - `test_switch_off_rebuilds_inokashira_by_equal_interval`(関数)
  - `test_w19_asset_table_follows_the_switch`(関数)
- import している内部モジュール: `shibuya.build.audit.w19_freeze`・`shibuya.build.field.common`・`shibuya.build.field.w12_external_nodes`・`shibuya.build.field.w12_real_timetables`・`tests/_data_ids.py`

## [test_w12_pm_peak_switch.py](../../../../../../tests/build_field/test_w12_pm_peak_switch.py)

W12 の夕ピークの切替口が ``run()`` の出力で効くこと(第330 B2・答え 10-12b 1-2)。

- 公開の関数とクラス
  - `test_default_has_no_pm_table`(関数): 既定の表は無い(他社の比 0.79 などを当てはめない)・既定は夕=朝。
  - `test_pm_peak_for_line_rules`(関数)
  - `test_switch_changes_pm_peak_in_run_output`(関数)
  - `test_switch_without_table_raises`(関数)
- import している内部モジュール: `shibuya.build.field.common`・`shibuya.build.field.w12_external_nodes`・`shibuya.build.field.w12_real_timetables`・`tests/_data_ids.py`
- 決定の ID: 10-12b・D-44・第 330

## [test_w12_real_timetables.py](../../../../../../tests/build_field/test_w12_real_timetables.py)

W12 の実ダイヤの読み口(第 2 期 2-3b・``build/field/w12_real_timetables.py``)。

- 公開の関数とクラス
  - `test_calendar_mapping_and_file_names`(関数)
  - `test_dedup_keeps_the_first_and_counts`(関数)
  - `test_departure_min_is_the_service_day_minute`(関数)
  - `test_ginza_open_static_matches_the_user_pdf_reading`(関数): 銀座線の ODPT オープン枠(9 月改正)の渋谷発は、ユーザーの G01(9 月改正)の読み取りと時刻の多重集合で一致
  - `test_hhmm_check_catches_a_planted_time`(関数): L3 の検査の負の対照: ISO の日時は除き、紛れ込んだ発車の時刻は見つける。
  - `test_hhmm_rejects_out_of_range`(関数)
  - `test_mapping_table_is_the_declared_one`(関数)
  - `test_no_rail_line_is_left_for_equal_interval_statically`(関数): 方面ノードの線は全部、実ダイヤの表(畳みを含む)かメトロ 2 線+銀座線で埋まる=等間隔で残る線 0。
  - `test_odpt_train_timetable_two_synthetic_trains`(関数)
  - `test_real_run_counts_match_the_record_golden`(関数)
  - `test_rows_from_table_rejects_a_wrong_heading_or_station`(関数)
  - `test_synthetic_csv_three_rows_map_to_w12_rows`(関数)
  - `test_temporary_trains_need_the_diamond_mark`(関数)
  - `test_w19_input_families_and_asset_paths`(関数)
  - `test_world_time_point_matches_the_calendar_default`(関数)
- import している内部モジュール: `shibuya.build.audit.w19_freeze`・`shibuya.build.field.common`・`shibuya.build.field.w12_external_nodes`・`shibuya.build.field.w12_real_timetables`・`shibuya.engine.calendar`・`shibuya.foundation.time_consts`・`tests/_data_ids.py`
- 決定の ID: 第 330
