# tests/engine/space

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 4 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../tests/engine/space/__init__.py)

(冒頭の説明なし)

## [test_nav1_density.py](../../../../../../../tests/engine/space/test_nav1_density.py)

段 5-1b 抽出のランの密度の推定の 3 案(腕 ``SHIBUYA_NAV1_DENSITY {cell,neighborhood,unscaled}``)の試験。

- 公開の関数とクラス
  - `synth_mesh`(関数)
  - `test_arm_reaches_the_run_and_does_not_move_legacy`(関数)
  - `test_b4_density_stage_comes_from_the_nav_stage_only_when_asked`(関数): 変化検出の B4 の密度の段: los_stage を渡せばそれ(nav1)・渡さなければ density ÷ 歩ける面積(legacy)。
  - `test_cell_contacts_edges_and_corners_on_the_same_floor_only`(関数)
  - `test_cell_is_the_stage_1_formula_bit_for_bit`(関数)
  - `test_default_is_neighborhood_and_manifest_names_the_estimator`(関数)
  - `test_modes_default_and_environment`(関数)
  - `test_neighborhood_pairs_keep_w2_8_neighbours_of_the_same_band`(関数)
  - `test_scale_one_makes_cell_equal_unscaled`(関数)
  - `test_synth_neighbours_follow_the_surface`(関数)
  - `test_three_estimators_match_the_hand_calculation`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.change_detect`・`shibuya.engine.geometry`・`shibuya.engine.space.nav1`・`shibuya.world.navmesh`・`shibuya.world.state`・`tests/build_space/synth.py`
- 環境変数: `SHIBUYA_NAV1_DENSITY`・`SHIBUYA_SPACE`

## [test_nav1_units.py](../../../../../../../tests/engine/space/test_nav1_units.py)

段 1 の移動(engine.space.nav1)の受入の試験(合成の小さな面・データ不要)。

- 公開の関数とクラス
  - `space`(関数)
  - `test_crossing_floors_only_through_a_link`(関数)
  - `test_engine_does_not_decide_for_the_person`(関数): AST: nav1 は判断の層・LLM・選び手を読まない(速さは体の属性・経路は既定の重み=宣言)。
  - `test_l3_ramp_inside_is_on_the_line_and_within_the_speed_bound`(関数)
  - `test_l4_space_argument_beats_the_environment`(関数)
  - `test_link_capacity_and_first_come_first_served`(関数)
  - `test_link_times_sr11`(関数)
  - `test_long_link_is_not_faster_than_walking`(関数)
  - `test_m4_density_denominator_is_area_times_population_scale`(関数)
  - `test_m4a_surface_counts_leave_out_the_agents_inside_buildings`(関数)
  - `test_m5_hop_walk_steps_legacy_is_one_step_per_node_and_nav1_uses_the_speed`(関数)
  - `test_p_notice_tiny_distance_is_one_without_overflow`(関数): 連続の位置で出る、ごく近い距離の一次検出(s^e が溢れる所)は極限の 1(NaN にしない)。
  - `test_q3_b6_mark_text_for_nav1_and_no_b8`(関数)
  - `test_q4_production_world_is_the_one_with_a_build_hash`(関数)
  - `test_resume_replans_the_same_route`(関数)
  - `test_slope_factor_matches_r63_table`(関数)
  - `test_speed_bound_inside_and_arrival`(関数)
  - `test_speed_is_the_body_attribute`(関数)
  - `test_turn_weights_fixed_and_person_range_deterministic`(関数)
  - `test_unique_position_per_agent_per_step`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.calendar_self`・`shibuya.engine.geometry`・`shibuya.engine.proximity`・`shibuya.engine.space.nav1`・`shibuya.perception.p_notice`・`shibuya.world.navmesh`・`tests/build_space/synth.py`
- 環境変数: `SHIBUYA_SPACE`
- 決定の ID: 10-03/§8・R-63

## [test_nav1_world.py](../../../../../../../tests/engine/space/test_nav1_world.py)

段 1 の移動の切替口(本物の世界・組んだ資産 ``data/world/v2_stage_5-1``・データの無い所では飛ばす)。

- 公開の関数とクラス
  - `legacy_stage`(関数)
  - `nav1_stage`(関数)
  - `test_default_is_nav1_on_the_staged_world`(関数)
  - `test_l4_space_argument_beats_the_environment_in_a_run`(関数)
  - `test_legacy_on_the_staged_world_is_legacy`(関数)
  - `test_nav1_golden_w6_v3_default_on_the_activated_world`(関数)
  - `test_nav1_moves_the_final_and_records_the_meter`(関数)
  - `test_nav1_resume_equals_straight`(関数)
  - `test_nav1_without_assets_runs_legacy_and_says_why`(関数)
  - `test_q4_production_world_without_assets_stops_and_legacy_runs`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.world.navmesh`・`tests/golden_env.py`
- 環境変数: `SHIBUYA_NAV1_DENSITY`・`SHIBUYA_SPACE`
- 決定の ID: 11-01・11-03/§3
