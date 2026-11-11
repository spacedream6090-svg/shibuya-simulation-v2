# tests/build_pop

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 11 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../tests/build_pop/__init__.py)

(冒頭の説明なし)

## [test_pop_pipeline.py](../../../../../../tests/build_pop/test_pop_pipeline.py)

W16 母集団合成の統合テスト(実データ必須・CI では skip)。

- 公開の関数とクラス
  - `built`(関数)
  - `test_acceptance_lines_from_the_decision_ledger`(関数): SRMSE 性別 <0.01・年齢 <0.13・方面 JSD <0.01・空セル 0%。
  - `test_age_raking_uses_all_sixteen_classes_and_prorates_the_unknown`(関数): ④ raking: 16 階級 × 性別の**結合表**・年齢不詳は階級を作らず按分する。
  - `test_all_gates_pass`(関数)
  - `test_direction_shares_follow_w12_weights`(関数): ⑤ 方面 OD: 一様事前を捨て、W12 の生成用重みへ寄る。
  - `test_duty_role_column_carries_the_functional_roster`(関数): 定員先取り層の判定材料(役割名)が母集団の列に載っている。
  - `test_eighty_chome_match_estat_population`(関数): dbf の JINKO と e-Stat 小地域の人口総数が 80 件すべて一致する。
  - `test_loader_reads_the_published_population`(関数)
  - `test_output_columns_and_byte_size`(関数): 出力の列と 1 体あたりバイト(予算報告用の実測)。
  - `test_pool_inventory_matches_meta`(関数): ① 在庫棚卸し: 層別件数が meta.json と一致(1,000,000 体)。
  - `test_population_backed_full_day_5000_agents`(関数): (f) 5,000 体 × 1 シミュ日(mock LLM)・保存則不変(予算行 W2 ≤10 分)。
  - `test_population_backed_run_conserves_money`(関数): (f) 母集団を載せたランがエンジンを通る・保存則が保たれる・同 seed 同ハッシュ。
  - `test_public_anchors_are_the_source_of_the_targets`(関数): 目標体数が公的値から来ていること(在庫比ではない)。
  - `test_rebuild_is_byte_identical`(関数): D-W20 T1: 同じ入力からの再構築で出力とヘッダがバイト一致する。
- import している内部モジュール: `shibuya.build.geo.common`・`shibuya.build.pop.w16_population`・`shibuya.engine.run`・`shibuya.world.facts.population_reader`・`shibuya.world.model.state`・`tests/_data_ids.py`・`tests/_time_gates.py`

## [test_pop_units.py](../../../../../../tests/build_pop/test_pop_units.py)

build.pop の単体テスト: Shapefile 最小パーサ・点包含・床面積按分・IPF・二層抽出。

- 公開の関数とクラス
  - `test_age_edges_are_identical_across_the_layer_boundary`(関数)
  - `test_ipf_fills_rows_whose_seed_is_all_zero`(関数): 目標が正なのに種が全 0 の行は一様種で埋める(構造的ゼロと標本ゼロを区別できない)。
  - `test_ipf_hits_both_margins`(関数): (c) IPF が行・列の周辺分布へ収束する。
  - `test_ipf_keeps_structural_zeros`(関数): 種の 0 セルは 0 のまま(実行可能な目標のとき周辺は厳密に一致する)。
  - `test_ipf_rejects_mismatched_totals`(関数)
  - `test_jsd_is_zero_for_identical_and_one_for_disjoint`(関数)
  - `test_kind_codes_are_identical_across_the_layer_boundary`(関数)
  - `test_point_in_polygon_square`(関数): (b) 点包含: 内・外・辺の外側。
  - `test_polygon_with_hole_excludes_inner_points`(関数): 穴つき(2 パート)は交差数の偶奇で内側が抜ける。
  - `test_property_floor_apportionment_fills_every_cell`(関数): (b) 空セルの充填: 候補建物があるセルは必ず 1 体以上(合計は不変)。
  - `test_property_largest_remainder_is_exact_and_monotone`(関数): (b) 床面積按分の性質: 合計が厳密・重みの大きい方が小さくならない。
  - `test_reserved_kind_matches_the_dispatcher_code`(関数)
  - `test_reserved_layer_is_decided_by_role_not_by_pool_layer`(関数): (層2 中-1) プール層 L5 の全件ではなく役割表で決める。
  - `test_reserved_roles_exist_in_the_build_side_role_vocabulary`(関数): 役割名は W16 が publish する語(``RAIL_CREW_ROLES``+指令)と綴りが一致する。
  - `test_reserved_roles_table_is_the_functional_minimum`(関数): 役割表そのものの釘付け(答申 §Q6-b: 乗務・指令・議員・警察/消防・公共交通)。
  - `test_sampling_more_than_available_returns_everything`(関数)
  - `test_sampling_smaller_than_the_reserved_layer_takes_only_the_reserved`(関数)
  - `test_shapefile_roundtrip`(関数): (a) テスト内で作った .shp/.dbf を自前パーサで読み戻せる。
  - `test_srmse_matches_the_reference_definition`(関数): SRMSE=sqrt(K·ΣΔ²)。性別(K=2)は片側 0.5 ポイントで 0.01 = 決定台帳のライン。
  - `test_start_cell_falls_back_to_work_then_school`(関数): 域外常住の体は 勤務→通学→fallback の順で初期セルに置かれる。
  - `test_two_stage_sampling_is_stratified_and_deterministic`(関数): (d) 統計層は (種別×年齢階級×性別) で比例配分・同 seed 同結果。
  - `test_two_stage_sampling_keeps_the_reserved_layer_whole`(関数): (d) 定員先取り層(``RESERVED_ROLES`` の役割+指令)は縮尺しない。
  - `test_unsupported_shape_type_raises`(関数): 対応範囲外(点)は黙って読まずに例外(範囲の狭さを機械で保証)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.build.pop.fitting`・`shibuya.build.pop.shapefile`・`shibuya.build.pop.w16_population`・`shibuya.world.facts.population_reader`

## [test_w21_activate.py](../../../../../../tests/build_pop/test_w21_activate.py)

第 4 期 4-1 段 1〜3 の活性化の道具(``pop41/tools/stage_pop41.py``)を合成の置き場で通す。

- 公開の関数とクラス
  - `test_apply_refuses_when_live_differs_from_plan`(関数)
  - `test_plan_apply_verify_revert_materialize`(関数)
  - `tool`(関数)

## [test_w21_attr_fns.py](../../../../../../tests/build_pop/test_w21_attr_fns.py)

W21 段 3「属性から作る関数」(``attr_fns``)の単体。

- 公開の関数とクラス
  - `test_blank_rules`(関数)
  - `test_calendar_inputs_are_the_five_w20_attributes`(関数)
  - `test_commuters_use_workplace_tables_and_are_employed`(関数)
  - `test_functions_are_pure_and_deterministic`(関数)
  - `test_incoming_students_draw_sex_age_and_school_kind_and_blank_the_rest`(関数): 〔検収 L6〕外から来る通学者: 男女と年齢は表の階級から・在学の種類は年齢の窓の在学の 6 区分から・ほかは空欄。
  - `test_mapping_tables_have_the_declared_rows`(関数)
  - `test_missing_input_columns_are_refused`(関数)
  - `test_negative_control_tables_are_read_only`(関数): 〔検収 L3〕表は書き換えられない(写像は MappingProxyType・配列は書き込み禁止)。
  - `test_rake_draw_moves_counts_to_the_group_margins`(関数)
  - `test_w16_employment_maps_the_five_words_and_blank_to_non_employed`(関数): 〔親の判断=W20 との接続〕employment_status → W16 の employment の 6 値(None と空欄は非就業)。
- import している内部モジュール: `shibuya.build.pop.attr_fns`・`shibuya.build.pop.w21_attrs`・`shibuya.build.pop.w21_build`・`shibuya.build.pop.w21_frame`・`shibuya.build.pop.w21_households`・`shibuya.build.pop.w21_tables`

## [test_w21_build_real.py](../../../../../../tests/build_pop/test_w21_build_real.py)

W21 を実データで組む(``requires_data("world_v2")``+W21 の材料=無ければ飛ばす)。

- 公開の関数とクラス
  - `built`(関数)
  - `test_anneal_on_off_arms`(関数)
  - `test_default_build_is_unchanged`(関数)
  - `test_distribution_check_is_recorded_for_every_table`(関数)
  - `test_everyone_is_distinct_and_families_are_consistent`(関数)
  - `test_frame_blanks_and_no_verify_side_values`(関数)
  - `test_golden_counts_and_build_hash`(関数)
  - `test_materials_are_build_side_and_pt_is_never_opened`(関数)
  - `test_seed_changes_people_but_not_the_frame`(関数)
  - `test_two_builds_are_byte_identical`(関数)
- import している内部モジュール: `shibuya.build.pop`・`shibuya.build.pop.w21_build`・`shibuya.build.pop.w21_frame`・`shibuya.build.pop.w21_households`・`shibuya.build.pop.w21_sources`・`shibuya.build.run`

## [test_w21_households.py](../../../../../../tests/build_pop/test_w21_households.py)

W21 段 2「世帯と人」の合成の単体(小さな町丁目 3 つ・材料の表は使わない)。

- 公開の関数とクラス
  - `test_anneal_on_reduces_error_off_keeps_and_counts_are_kept`(関数)
  - `test_assign_categories_counts_by_largest_remainder`(関数)
  - `test_composition_and_family_consistency`(関数)
  - `test_composition_table_covers_every_type_and_size`(関数)
  - `test_draws_are_deterministic_and_seed_sensitive`(関数)
  - `test_draws_have_no_empty_windows_and_heads_with_parents_stay_under_the_cap`(関数)
  - `test_feasible_other_relations_keep_every_window_non_empty`(関数): 〔検収 L2〕窓が空になる続き柄は引かない: 孫と祖父母は世帯主と 30 歳(親子の最小の差 × 2)以上・子の配偶者は世帯主 30 歳以上。
  - `test_foreign_count_per_chome_is_hit_without_overshoot`(関数)
  - `test_household_cells_hit_the_chome_margins_and_are_integers`(関数)
  - `test_place_households_by_level_class_with_fallbacks`(関数)
  - `test_singles_follow_the_chome_residual_targets`(関数): 単独世帯の世帯主は町丁目の残りの目標で引く=町丁目の年齢 × 男女の誤差が、区の分布だけで引くより小さい。
- import している内部モジュール: `shibuya.build.pop.w21_households`・`shibuya.build.pop.w21_tables`

## [test_w21_sources.py](../../../../../../tests/build_pop/test_w21_sources.py)

W21(第 4 期 4-1 段 1〜3)の材料の台帳と読み口の守り(read_guard)。

- 公開の関数とクラス
  - `test_audit_hook_stops_raw_open_of_verify_side_and_unlisted_files`(関数)
  - `test_build_sources_do_not_name_sealed_layers`(関数)
  - `test_negative_control_out_inside_the_main_v2_is_refused`(関数): 〔検収 M1〕``--out`` が本体の v2・読む世界資産・既存の資産の置き場の中なら、何も書かずに止める。
  - `test_negative_control_pt_c2_layout_mismatch_reads_no_values`(関数): 「自宅以外からの私事」が発生量の塊に無い形(列の並びが想定と違う)なら、値の列のイベントを出さずに止める。
  - `test_negative_control_pt_c2_refuses_columns_outside_the_allow_list_before_opening`(関数): 許可の外の列(集中量)を頼むと、ファイルを開く前に止まる(open も値の列のイベントも出ない)。
  - `test_negative_control_verify_side_paths_are_stopped_before_opening`(関数): 負の対照: 検証側の語のある道筋は、許可の一覧に足しても(=構築側と取り違えても)開く前に止まる。
  - `test_negative_control_write_mode_into_the_main_v2_is_stopped`(関数): 〔検収 M1〕本体の v2(読むのは許す世界資産)へ書き込みのモードで開くと止まる・出力先は書ける。
  - `test_pt_c2_reads_only_the_allowed_columns`(関数): 〔検収 L1〕見出しの行だけで列の位置を決め、値は許可の 2 列+ゾーン・時間帯だけを読む(集中量の列は読み込まない)。
  - `test_registry_is_build_side_and_never_verify_side`(関数)
  - `test_unlisted_paths_are_stopped_and_listed_ones_pass`(関数)
  - `test_verify_side_is_the_eleven_rows_of_r116`(関数)
  - `test_w21_build_cannot_open_pt_c2`(関数)
- import している内部モジュール: `shibuya.build.audit.w19_freeze`・`shibuya.build.pop.w21_build`・`shibuya.build.pop.w21_sources`
- 決定の ID: R-116

## [test_w21_stage10_swap.py](../../../../../../tests/build_pop/test_w21_stage10_swap.py)

第 4 期 4-3 段 10「差し替え」(``build.pop.w21_apply``)の受入の試験。

- 公開の関数とクラス
  - `test_activation_plan_table_and_verify`(関数)
  - `test_commute_line_and_substitute_language_in_persona`(関数): 〔仮-33 (9)〕電車の人の通勤の行に通う駅の口の路線の名・〔(7)〕型の無い言語は日本語の型で代えて印。
  - `test_crews_take_the_functional_quota_and_crew_donors_by_role`(関数): 〔検収 M2〕担当の体は機能定員まで(人ごとの Philox の順)・乗務員の提供者は同じ担当の語から・居なければ止まる。
  - `test_donor_levels_widen_and_missing_kind_stops`(関数)
  - `test_donor_reuse_over_the_limit_stops`(関数): 〔検収 L4〕1 人の提供者を使ってよい回数(3 回)に達したら使わない=受け手が残れば止まる(合成の入力)。
  - `test_donor_rows_are_copied_and_cells_retargeted`(関数)
  - `test_merge_keeps_w16_rows_and_sorts_by_agent_id`(関数)
  - `test_number_meter_skips_digits_inside_names`(関数): 〔仮-33 (5)〕名(POI と組織の名)の中の数字は数字の計器から除く(名を渡さなければ今までどおり数える)。
  - `test_output_guard_and_versions`(関数)
  - `test_rail_lead_stays_blank_for_the_w20_default`(関数): 〔親の判断=検収 L6〕電車の人の片道は空欄(W20 の既定 30 分)=舞台の中の道のりでは埋めない。
  - `test_real_asset_gates_and_counts`(関数)
  - `test_real_engine_reads_the_swapped_population_and_w17`(関数)
  - `test_reserved_mask_skips_commuter_and_worker_kinds`(関数): 〔検収 M2〕差し替えの母集団の W21 の行は、役割の名を持っていても種別 0・2 なら先取りしない(機能定員の外=統計層)。
  - `test_rights_rows_pass_the_engine_initial_table`(関数)
  - `test_unknown_w16_group_stops`(関数)
  - `test_w16_group_actions_follow_the_parent_decisions`(関数)
  - `test_w20_direct_rows_from_eight_statuses_and_unknown_stops`(関数)
  - `test_w20cal_params_are_the_337_version`(関数)
  - `test_w21_columns_are_a_bijection_from_person_ids`(関数)
  - `test_w21_columns_stop_on_unknown_entry_kind_and_gaps`(関数)
- import している内部モジュール: `shibuya.build.geo.common`・`shibuya.build.pop.w21_apply`・`shibuya.build.pop.w21_build_b`・`shibuya.build.pop.w21_build_c`・`shibuya.build.pop.w21_persona`・`shibuya.build.sched.w20_calendar_1a`・`shibuya.build.sched.w20_w21_port`・`shibuya.world.facts.population_reader`・`shibuya.world.facts.rights.initial`・`shibuya.world.facts.rights.ledger`・`shibuya.world.facts.weekly_reader`・`tools/instruments/dm_eval/situations.py`
- 決定の ID: 第 337

## [test_w21_stage4_7.py](../../../../../../tests/build_pop/test_w21_stage4_7.py)

第 4 期 4-1 段 4〜7(W21 の続き=``w21_build_b``)の受入の試験。

- 公開の関数とクラス
  - `built`(関数)
  - `test_activation_tool_shape`(関数): 活性化の道具(``pop41b/tools/stage_pop41b.py``)は段 1〜3 の道具の plan 以下を使い、書くファイルは段 4〜7 の出力。
  - `test_build_money_distributes_household_assets_to_adults`(関数)
  - `test_check_out_b_protects_v2_base_and_existing_dirs`(関数)
  - `test_class_seats_and_role_aware_filling`(関数)
  - `test_commute_facts`(関数)
  - `test_commuter_and_role_functions`(関数)
  - `test_consumer_credit_adults_only`(関数)
  - `test_default_build_is_unchanged`(関数)
  - `test_departments_division_arm`(関数)
  - `test_departments_one_supervisor_and_sizes`(関数)
  - `test_duty_role_rules`(関数)
  - `test_familiar_places_rules_and_chunk_independence`(関数)
  - `test_fill_seats_min_of_seats_and_people_proportional_and_deterministic`(関数)
  - `test_household_assets_zero_share_tilt_and_debt`(関数)
  - `test_module_tables_are_read_only`(関数): 〔検収 L7〕モジュールの表は書き換えられない。
  - `test_money_functions_are_pure_and_follow_blank_rules`(関数)
  - `test_nightlife_is_zero_under_20_and_love_hotel_under_18`(関数): 〔検収 L1〕夜の店は 20 歳未満 0(カラオケを除く)・ラブホテルは 18 歳未満 0=人の年齢で切る(18・19 歳の負の対照)。
  - `test_outside_ring_total_and_missing_origins_are_renormalized`(関数): 〔検収 L3・L6〕表に無い流入元は除いて重みの和 1・輪の和は渡した値(段 1 の枠)に合う。
  - `test_outside_strata_layers_and_blanks`(関数)
  - `test_read_guard_r99_copy_is_blocked_and_pop41b_copy_is_listed`(関数)
  - `test_read_guard_stops_verify_side_tables`(関数)
  - `test_real_golden_counts_and_hash`(関数)
  - `test_real_materials_and_world_columns`(関数)
  - `test_real_rights_rows_pass_engine_grant`(関数): 〔検収 L9〕閉じた表の行は engine の ``Rights.grant`` が全部受け付け、閉じた表の外の行ははじかれる。
  - `test_real_status_split_is_applied_before_seats`(関数): 〔第 4 期 4-3 段 10・仮-33 (2)〕外から来て働く人の地位の分けを席の前に入れた(W21c 1.2.0 の数え直しと同じ数)。
  - `test_real_structure_and_checks`(関数)
  - `test_real_two_builds_are_byte_identical`(関数)
  - `test_registry_has_stage_4_to_6_functions_with_stage_marks`(関数)
  - `test_relation_pairs_all_ordered_pairs_within_groups`(関数)
  - `test_residence_capacity_and_known_places_laws`(関数)
  - `test_resident_workplaces_rules`(関数)
  - `test_stage_worker_targets_census_number_with_ecen_distribution`(関数)
  - `test_store_owners_same_building_and_industry`(関数)
  - `test_weekly_hours`(関数)
- import している内部モジュール: `shibuya.build.pop`・`shibuya.build.pop.attr_fns`・`shibuya.build.pop.w21_build_b`・`shibuya.build.pop.w21_checks`・`shibuya.build.pop.w21_money`・`shibuya.build.pop.w21_org`・`shibuya.build.pop.w21_outside`・`shibuya.build.pop.w21_prior`・`shibuya.build.pop.w21_sources`・`shibuya.build.run`・`shibuya.world.facts.rights.ledger`
- 決定の ID: 第 337

## [test_w21_stage8_9.py](../../../../../../tests/build_pop/test_w21_stage8_9.py)

第 4 期 4-1 段 8〜9 と段 10 の材料(W21 の続き=``w21_build_c``)の受入の試験。

- 公開の関数とクラス
  - `base12`(関数): 〔第 4 期 4-3 段 10〕段 4〜7 を 1.2.0(地位の分けを席の前に)で組んだ置き場(段 1〜3 の資産の写しを足す)。
  - `built`(関数)
  - `test_big_five_is_an_arm_with_blank_default`(関数)
  - `test_check_out_c_protects_v2_bases_and_existing_dirs`(関数)
  - `test_commuter_status_split_follows_table_6_2_ratios`(関数)
  - `test_compose_blocks_with_the_engine_compose_and_6_1_lengths`(関数)
  - `test_couple_children_counts`(関数)
  - `test_cp5_3_naming_by_id_does_not_count_same_name_chains`(関数)
  - `test_cp5_3_naming_check_finds_planted_names`(関数)
  - `test_distribution_rows_shape_and_basis_marks`(関数): 分布の点検の表の形(行の名・印・区分の数)。構築に使っていない区分の行は 4 つ(従業地 第15-1表・2025 第15-1表 2・
  - `test_diversity_is_monotone_in_clones`(関数)
  - `test_double_rows_find_planted_doubles`(関数)
  - `test_fit_cells_shape_and_max_diff`(関数)
  - `test_language_functions_are_pure_and_follow_blank_rules`(関数)
  - `test_module_tables_and_defaults`(関数)
  - `test_numbers_are_only_money_and_time_by_the_6_1_meter`(関数)
  - `test_override_port_reads_new_text_and_keeps_original`(関数)
  - `test_persona_build_does_not_import_or_call_llm`(関数): 組み立て(import と ``build_tables``)で ``shibuya.llm`` が読み込まれない・名の照合(``naming_check``=engine を遅れて
  - `test_persona_does_not_reference_llm_ports`(関数)
  - `test_persona_is_deterministic_and_short_is_prefix_of_long`(関数)
  - `test_persona_languages_and_blank_templates`(関数)
  - `test_prefix_mismatches_and_read_only_facts`(関数)
  - `test_read_guard_language_verify_side_files_are_not_allowed`(関数): 在留外国人統計と訪日外客の統計の検証側の区分(言語の結果=受入環境のアンケート・行動特性調査の満足度=R-110 §3-5 の
  - `test_read_guard_stops_the_11_verify_side_rows`(関数)
  - `test_real_golden_counts_and_hash`(関数)
  - `test_real_materials_are_build_side`(関数)
  - `test_real_store_staff_rows_pass_engine_grant`(関数)
  - `test_real_structure_and_instruments`(関数)
  - `test_real_two_builds_are_byte_identical`(関数)
  - `test_real_w20_attributes_table_is_the_port_output`(関数)
  - `test_record_has_no_personal_text`(関数): 記録(README と JSON)に個人の文が無い: 例は合成の 1 人(``persona_meter.example``)の文だけ。資産があれば、体の
  - `test_registry_has_stage_9_and_10_functions`(関数)
  - `test_relation_category_from_the_persons_view`(関数)
  - `test_status_split_table_reads_the_table_6_2_columns`(関数)
  - `test_store_staff_rows_round_robin_head_first_and_engine_grant`(関数)
  - `test_tuple_duplicates_finds_planted_duplicates_and_indistinguishable_groups`(関数)
  - `test_uniqueness_counts_planted_same_tuples`(関数)
  - `test_w16_keep_table_actions`(関数)
  - `test_walk_minutes_share_one_function`(関数)
  - `test_words_and_money_formats`(関数)
- import している内部モジュール: `shibuya.build.pop.attr_fns`・`shibuya.build.pop.w21_build_b`・`shibuya.build.pop.w21_build_c`・`shibuya.build.pop.w21_check`・`shibuya.build.pop.w21_checks`・`shibuya.build.pop.w21_money`・`shibuya.build.pop.w21_persona`・`shibuya.build.pop.w21_port10`・`shibuya.build.pop.w21_sources`・`shibuya.build.pop.w21_tables`・`shibuya.build.run`・`shibuya.build.sched.w20_w21_port`・`shibuya.foundation.ports.decision`・`shibuya.llm`・`shibuya.world.facts.rights.initial`・`shibuya.world.facts.rights.ledger`・`shibuya.world.model.geometry`・`tests/_places.py`・`tools/instruments/dm_eval/situations.py`
- 決定の ID: R-110
