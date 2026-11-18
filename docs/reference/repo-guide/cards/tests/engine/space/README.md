# tests/engine/space

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 6 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../tests/engine/space/__init__.py)

(冒頭の説明なし)

## [_legacy.py](../../../../../../../tests/engine/space/_legacy.py)

〔第347 止めた切替口の削除・案 s1〕旧のセルの移動(``legacy``)を試験の中だけで選ぶ助け。

- 公開の関数とクラス
  - `legacy_space`(関数): 旧のセルの移動を選ぶ印を立てる(``mp`` が戻すまで)。
- import している内部モジュール: `shibuya.world.model.space.nav1`
- 読む試験: `tests/engine/multiday/test_md23_w9_window.py`・`tests/engine/space/test_nav1_density.py`・`tests/engine/space/test_nav1_world.py`・`tests/engine/test_pop_w21_world.py`
- 決定の ID: 第 347

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
- import している内部モジュール: `shibuya.interfaces.cli.main`・`shibuya.mind.system1.change_detect`・`shibuya.world.model.geometry`・`shibuya.world.model.navmesh`・`shibuya.world.model.scene_hash`・`shibuya.world.model.space.nav1`・`shibuya.world.model.state`・`tests/build_space/synth.py`・`tests/engine/space/_legacy.py`
- 環境変数: `SHIBUYA_NAV1_DENSITY`
- 決定の ID: 第 347

## [test_nav1_route_cache.py](../../../../../../../tests/engine/space/test_nav1_route_cache.py)

S46: nav1 の道の線の控えが結果に作用しないことの試験(控えの有り無しで返る線が 1 バイトも違わない)。

- 公開の関数とクラス
  - `check_cache_is_inert`(関数): 控え有り=控え無し=逆順の直の計算(1 バイト)と、控えが溢れる場合の一致。返り値は計器の数(確かめに使う)。
  - `direct_reversed`(関数): 控えを通らず ``NavPlanner.plan`` を直に、列の逆の順で呼ぶ(丸めは ``_shape`` と同じにする)。並びは列の順に戻す。
  - `key32`(関数): 問い合わせ (x, y, 階, 行き先, 曲がる重み) → 控えの鍵と同じ形(出発点を float32 に丸める)。
  - `make_sequence`(関数): 出発点ごとに行き先を ``per_origin`` 個と曲がる重みを引いた問い合わせ(引けない行き先も混ぜる)を ``repeat`` 回並べて
  - `real_world`(関数)
  - `route_bytes`(関数): 線の全欄 → 比べる値(配列は名・dtype・形・バイト/そのほかは名・型・repr)。None は None。
  - `synth_world`(関数)
  - `test_cache_on_and_off_give_byte_identical_lines_on_the_real_mesh`(関数)
  - `test_cache_on_and_off_give_byte_identical_lines_on_the_synthetic_mesh`(関数)
  - `test_cache_on_and_off_give_byte_identical_timed_routes_through_ensure_routes`(関数): ``ensure_routes`` の段: 体ごとに時間を載せた線(置き場の 7 欄)と返り値が、控えの有り無しで 1 バイト一致。
  - `test_cache_overflow_drops_the_oldest_and_keeps_the_lines`(関数): 上限 3 の控えに 4 つの鍵を入れると最初の鍵が捨てられ、それを引き直した線は最初の線と 1 バイト一致。
  - `via_shape`(関数): 問い合わせの列を ``_shape`` に順に当てた線の並び。``cap_watch`` なら控えの大きさが上限を超えないことも見る。
  - `without_cache`(関数): ``space`` の控えを毎回空にする(``_shape`` を呼ぶ前に ``_shape_cache.clear()``・同じ道を通る)。
- import している内部モジュール: `shibuya.world.model.assets`・`shibuya.world.model.navmesh`・`shibuya.world.model.space.nav1`・`tests/_data_ids.py`・`tests/build_space/synth.py`

## [test_nav1_units.py](../../../../../../../tests/engine/space/test_nav1_units.py)

段 1 の移動(engine.space.nav1)の受入の試験(合成の小さな面・データ不要)。

- 公開の関数とクラス
  - `space`(関数)
  - `test_crossing_floors_only_through_a_link`(関数)
  - `test_engine_does_not_decide_for_the_person`(関数): AST: nav1 は判断の層・LLM・選び手を読まない(速さは体の属性・経路は既定の重み=宣言)。
  - `test_l3_ramp_inside_is_on_the_line_and_within_the_speed_bound`(関数)
  - `test_l4_the_requested_space_takes_only_nav1_and_ignores_the_environment`(関数): 〔第347 止めた切替口の削除〕前(``test_l4_space_argument_beats_the_environment``)は ``space_env_override`` の順(引数 →
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
- import している内部モジュール: `shibuya.act.activity`・`shibuya.act.intake.parser`・`shibuya.act.intent`・`shibuya.foundation.arms.removed`・`shibuya.foundation.ports.choice`・`shibuya.foundation.vocab.agent_codes`・`shibuya.interim_bundles.calendar2.layer`・`shibuya.interim_bundles.calendar_self`・`shibuya.mind.judge.chooser`・`shibuya.mind.judge.classical`・`shibuya.mind.judge.decision.layer`・`shibuya.world.model.geometry`・`shibuya.world.model.navmesh`・`shibuya.world.model.notice_reach`・`shibuya.world.model.proximity`・`shibuya.world.model.space.nav1`・`tests/_places.py`・`tests/build_space/synth.py`
- 環境変数: `SHIBUYA_SPACE`
- 決定の ID: 10-03/§8・R-63・第 347

## [test_nav1_world.py](../../../../../../../tests/engine/space/test_nav1_world.py)

段 1 の移動(本物の世界・組んだ資産 ``data/world/v2_stage_5-1``・データの無い所では飛ばす)。

- 公開の関数とクラス
  - `legacy_stage`(関数): 〔第347〕前は ``_run("legacy")``(切替口)。試験の中だけの口で旧のセルの移動にする。
  - `nav1_stage`(関数)
  - `test_default_is_nav1_on_the_staged_world`(関数)
  - `test_l4_the_space_env_stops_a_run_and_the_argument_takes_only_nav1`(関数): 〔第347 止めた切替口の削除〕前(``test_l4_space_argument_beats_the_environment_in_a_run``)は「環境変数 legacy を置いても
  - `test_legacy_on_the_staged_world_is_legacy`(関数)
  - `test_m1_a_run_on_the_test_only_port_is_an_arm_run_through_cli_run`(関数): 〔第347・検収 M1〕試験の中だけの口(印)で旧のセルの移動にしたランは、``cli.run`` のランの種類で腕に数える(前の頼み方
  - `test_nav1_golden_w6_v3_default_on_the_activated_world`(関数)
  - `test_nav1_moves_the_final_and_records_the_meter`(関数)
  - `test_nav1_resume_equals_straight`(関数)
  - `test_nav1_without_assets_runs_legacy_and_says_why`(関数)
  - `test_q4_production_world_without_assets_stops_and_legacy_runs`(関数): 本番の形で資産が無ければ nav1 は止まる・旧のセルの移動なら回る。〔第347〕前は ``space="legacy"`` で回した(切替口)=
- import している内部モジュール: `shibuya.experiments.port.run_kind`・`shibuya.interfaces.cli.main`・`shibuya.world.model.navmesh`・`shibuya.world.model.space.nav1`・`tests/engine/space/_legacy.py`・`tests/golden_env.py`
- 環境変数: `SHIBUYA_NAV1_DENSITY`・`SHIBUYA_SPACE`
- 決定の ID: 11-01・11-03/§3・第 347
