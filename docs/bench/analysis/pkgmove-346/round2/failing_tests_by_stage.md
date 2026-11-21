# 全段の木で落ちた試験(試験の役へ渡す一覧・道具の役 round2)

全段を当てた木(foundation → … → delete → interim_bundles)の範囲の試験で落ちた試験の関数ごとに、段ごとの木で回し直して最初に落ちる段と、原因の類。数は node id の数(引数つきは 1 つずつ)。

## 類

- **A**: 頭の写しの固定のバイト(古い commit の写しの import を道具が書き換え、sha256 の固定が外れる)=親の決定 10
- **B**: つなぎの台帳の道(台帳の code_at・declared_in を今の道と比べる)=親の決定 1。`ledger_paths.ledger_path`/`current_path` を使う
- **C**: 凍結の名を今の置き場として使う(凍結の名で import・凍結の名から道を作る)。`class_path()` を使う
- **G**: 包みの頭を属性で読む(`from shibuya.engine import body as B` の後の `B.set_arm`)=親の決定 3 の試験の側
- **F**: pytest の印の警告の型の置き場の字面(`ignore::shibuya.engine.processes.environment.WeatherWarning`)=凍結のクラスの名と同じ字面なので道具は書き換えない。読めずに xdist の worker が落ち、範囲の試験が途中で止まる
- **E**: 作った木・差し込むコードの一部だけを道具が書き換えて食い違う(ファイルの道の鍵は書き換わり、ディレクトリの名や判定の表は古いまま)
- **I**: 読み込みの順(import の副作用)に頼る(エンジンを読むと llm の頭も読まれる、を確かめる)。頭の再輸出を除いた後は読まれない
- **H**: tools の下の道具(試験の役の受け持ちの外)が古い置き場を持つ: tools/c8 の包みの名の表・ディレクトリの走査
- **H(道具の役が直した)**: tools/repo_guide/guide_permits.py の f 文字列の道(親の裁定 tests1 の 5 で直した=全段の木 try6 で通る)
- **D**: 道具が触らない形の道・名(ディレクトリの道・`shibuya.` の無い点の名・包みの名の表・`parents[k]` の数え・`/` の結合が2 つの式に分かれる・docs の記録の道具・src の宣言の文の道を is_file する)

## 一覧

| 最初に落ちる段 | 類 | 試験(ファイル::関数) | id の数 |
|---|---|---|---:|
| s00_base | 前から | `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report` | 1 |
| s01_foundation | A | `tests/economy/cp2/test_cp2_nine_ops_equivalence.py::test_the_copies_are_the_head_blobs` | 1 |
| s01_foundation | B(道具の役が直した) | `tests/engine/bridging/test_bridging_ledger.py::test_heading_rows_carry_the_heading_and_the_item_count` | 1 |
| s01_foundation | D | `tests/engine/decision/test_j0_port_schema.py::test_no_literal_example_numbers_in_the_prompt_parts` | 1 |
| s01_foundation | E | `tests/engine/events/test_e_cause_three_kinds.py::test_static_check_catches_every_planted_form` | 3 |
| s01_foundation | F | `tests/engine/experiment/test_x33_apply.py` | 1 |
| s01_foundation | D | `tests/engine/experiment/test_x33_form.py::test_no_place_or_business_names_in_the_experiment_code` | 1 |
| s01_foundation | D | `tests/engine/memory/test_m0_store_schema.py::test_store_imports_only_allowed_layers` | 1 |
| s01_foundation | A | `tests/engine/speech/test_speech_on_reaches_addressee.py::test_an_all_imperative_utterance_puts_no_line` | 1 |
| s01_foundation | A | `tests/engine/speech/test_speech_on_reaches_addressee.py::test_heard_line_and_field_line_at_the_end_of_b6` | 2 |
| s01_foundation | A | `tests/engine/speech/test_speech_on_reaches_addressee.py::test_no_field_line_on_v1_and_nothing_without_the_hook` | 1 |
| s01_foundation | A | `tests/engine/speech/test_speech_on_reaches_addressee.py::test_speech_lines_are_dropped_when_the_individual_budget_is_exceeded` | 1 |
| s01_foundation | C | `tests/engine/state/test_class_ids.py::test_allowed_class_refuses_a_path_that_points_to_another_class` | 1 |
| s01_foundation | C | `tests/engine/state/test_class_ids.py::test_frozen_json_maps_each_value_to_the_qualname_of_its_class` | 1 |
| s01_foundation | C | `tests/engine/state/test_class_ids.py::test_table_keys_and_declarations_are_exactly_the_classes_in_src` | 1 |
| s01_foundation | E | `tests/engine/systems/test_fix_guards.py::test_permit_check_catches_planted_switches` | 1 |
| s01_foundation | D | `tests/engine/test_salt_seed_split_10f.py::test_static_scan_catches_aliases_and_keyword_domains` | 1 |
| s01_foundation | E | `tests/engine/test_state_checks_10f.py::test_t5_static_fifth_word_caller_fails` | 1 |
| s01_foundation | C | `tests/engine/test_state_format_10f.py::test_u3_value_class_fields_match_the_class` | 1 |
| s01_foundation | D | `tests/engine/time/test_t0_time_consts.py::test_module_level_aliases_elsewhere_are_the_same_value` | 1 |
| s01_foundation | A | `tests/perception/facts/test_render_from_percept_bytes.py::test_19_configs_render_the_same_bytes_as_head` | 19 |
| s01_foundation | A | `tests/perception/facts/test_render_from_percept_bytes.py::test_counters_match_head` | 13 |
| s01_foundation | A | `tests/perception/facts/test_render_from_percept_bytes.py::test_negative_control_one_byte_change_is_caught` | 1 |
| s01_foundation | A | `tests/perception/facts/test_render_from_percept_bytes.py::test_render_without_prepare_and_out_of_area_cells` | 1 |
| s01_foundation | A | `tests/perception/facts/test_render_from_percept_bytes.py::test_synthetic_scenes_render_the_same_bytes_as_head` | 13 |
| s01_foundation | E | `tests/tools/test_bytecheck.py::test_root_scanner_counts_the_paths_helpers` | 1 |
| s02_world | D | `tests/build_rail/test_w12_arrivals_2_3c.py::test_engine_reader_is_not_called_from_any_process` | 1 |
| s02_world | H | `tests/c8/test_c8lib.py::test_scan_engine_ablation_ids` | 1 |
| s02_world | H | `tests/c8/test_sensitivity_ledger.py::test_d44_column_is_consistent` | 1 |
| s02_world | H | `tests/c8/test_sensitivity_ledger.py::test_ledger_validates` | 1 |
| s02_world | H | `tests/c8/test_sensitivity_ledger.py::test_process_ablation_ids_match_source` | 1 |
| s02_world | H | `tests/c8/test_sensitivity_ledger.py::test_read_graph_column_is_consistent` | 1 |
| s02_world | H | `tests/c8/test_sensitivity_ledger.py::test_read_graph_matches_the_source` | 1 |
| s02_world | H | `tests/c8/test_sensitivity_ledger.py::test_triage_column_is_consistent` | 1 |
| s02_world | G | `tests/engine/body/test_body_manifest.py::test_arm_switch_reads_env_and_cli` | 1 |
| s02_world | G | `tests/engine/body/test_body_manifest.py::test_manifest_body_keys_and_sections` | 1 |
| s02_world | G | `tests/engine/body/test_body_manifest.py::test_manifest_fields_without_a_layer_are_null` | 1 |
| s02_world | G | `tests/engine/body/test_body_manifest.py::test_the_arm_is_not_in_the_fingerprint_and_marks_the_run_kind` | 1 |
| s02_world | G | `tests/engine/body/test_body_manifest.py::test_world_assets_reserve_equals_sweep_with_thermal_boundaries` | 1 |
| s02_world | G | `tests/engine/body/test_body_reserve.py::test_activity_change_replans_the_reservation` | 1 |
| s02_world | G | `tests/engine/body/test_body_reserve.py::test_felt_guard_refuses_a_table_that_disagrees_with_the_window` | 1 |
| s02_world | G | `tests/engine/body/test_body_reserve.py::test_felt_negative_control` | 2 |
| s02_world | G | `tests/engine/body/test_body_reserve.py::test_felt_reserve_equals_sweep` | 1 |
| s02_world | G | `tests/engine/body/test_body_reserve.py::test_negative_control_shifting_the_reservation` | 2 |
| s02_world | G | `tests/engine/body/test_body_reserve.py::test_reserve_equals_sweep_with_outside_writers` | 8 |
| s02_world | G | `tests/engine/body/test_body_reserve.py::test_resume_with_the_reserve_arm_equals_the_straight_run` | 1 |
| s02_world | G | `tests/engine/body/test_body_reserve.py::test_run_day_reserve_equals_sweep` | 3 |
| s02_world | B(道具の役が直した) | `tests/engine/bridging/test_bridging_ledger.py::test_doc_rows_need_no_code_declaration` | 1 |
| s02_world | D | `tests/engine/contact/test_c1_fixes.py::test_m2_ast_person_events_come_only_from_decisions` | 1 |
| s02_world | B | `tests/engine/rights/test_rights_from_w16.py::test_blank_bridges_are_active_rows_of_the_ledger` | 1 |
| s02_world | E | `tests/engine/rights/test_rights_schema.py::test_negative_outside_writes_are_caught` | 1 |
| s02_world | E | `tests/engine/rules/test_rules_table_schema.py::test_only_the_manifest_and_the_daily_record_import_the_table` | 1 |
| s02_world | E | `tests/engine/rules/test_rules_table_schema.py::test_the_reader_check_sees_every_import_form` | 2 |
| s02_world | D | `tests/engine/space/test_nav1_units.py::test_m5_hop_walk_steps_legacy_is_one_step_per_node_and_nav1_uses_the_speed` | 1 |
| s02_world | E | `tests/engine/state/test_names_frozen.py::test_shaped_pattern_finds_both_forms_inside_japanese_text` | 1 |
| s02_world | E | `tests/engine/test_state_checks_10f.py::test_t4_axis1_reading_a_no_attribute_in_a_behavior_place_fails` | 1 |
| s02_world | E | `tests/tools/test_repo_guide.py::test_ledger_rows_and_owner` | 1 |
| s02_world | E | `tests/tools/test_repo_guide.py::test_subdirs_are_sorted` | 1 |
| s02_world | E | `tests/tools/test_repo_guide.py::test_write_permits_from_table` | 1 |
| s02_world | D | `tests/world/processes/test_declarations_1101.py::test_inputs_existing_five_filled_and_new_seven_fields_only` | 1 |
| s03_economy | D | `tests/economy/test_single_write_path.py::test_engine_does_not_import_economy` | 1 |
| s04_act | D | `tests/bench/test_refr20b_tool.py::test_gates_outside_table_symbols_are_defined_in_their_files` | 1 |
| s05_mind | D | `tests/engine/contact/test_c2_habit.py::test_ast_no_engine_time_or_count_rules_in_c2` | 1 |
| s05_mind | D | `tests/engine/decision/test_j0_port_schema.py::test_three_implementations_share_one_entry` | 1 |
| s05_mind | D | `tests/engine/memory/test_mr65_guards.py::test_new_modules_respect_the_layer_contract` | 1 |
| s06_society | B | `tests/engine/tools/test_c0_phone_table_empty_and_declared.py::test_the_blank_is_declared_in_the_bridging_ledger` | 1 |
| s07_runtime | I | `tests/build_pop/test_w21_stage8_9.py::test_persona_build_does_not_import_or_call_llm` | 1 |
| s07_runtime | B(道具の役が直した) | `tests/engine/bridging/test_bridging_ledger.py::test_a_broken_ledger_stops_the_run_at_the_start` | 1 |
| s07_runtime | B | `tests/engine/memory/test_mr65_review_fixes.py::test_bridge_ids_use_the_stage_names_of_answer_6_2` | 1 |
| s07_runtime | D | `tests/engine/test_env_and_sections_10f.py::test_o75_split_flow_dir8_and_coherence_are_diag` | 1 |
| s07_runtime | H(道具の役が直した) | `tests/tools/test_repo_guide.py::test_real_ledger_rows_match_import` | 1 |
| s07_runtime | D | `tests/tools/test_repo_guide.py::test_real_public_names_match_import` | 1 |
| s07_runtime | H(道具の役が直した) | `tests/tools/test_repo_guide.py::test_real_write_permits_match_import` | 1 |
| s09_validation | D | `tests/engine/test_add_at_guard.py::test_systems_modules_have_no_state_ufunc_at` | 1 |
| s11_interim_bundles | D | `tests/engine/calendar2/test_ca2_runs.py::test_ast_book_is_written_only_through_its_ports` | 1 |
| s11_interim_bundles | D | `tests/engine/calendar2/test_ca2_runs.py::test_ast_engine_does_not_decide_times` | 1 |
| s11_interim_bundles | D | `tests/engine/calendar2/test_ca2_runs.py::test_ast_person_events_come_only_from_decisions` | 1 |
| s11_interim_bundles | D | `tests/engine/calendar3/test_ca3_runs.py::test_ast_book_is_written_only_through_its_ports` | 1 |
| s11_interim_bundles | D | `tests/engine/calendar3/test_ca3_runs.py::test_ast_engine_does_not_decide_times_or_contents` | 1 |
| s11_interim_bundles | D | `tests/engine/calendar3/test_ca3_runs.py::test_ast_person_events_come_only_from_decisions` | 1 |
| s11_interim_bundles | D | `tests/engine/duties/test_du_units.py::test_ast_offer_conditions_have_no_time_literals` | 1 |
| s11_interim_bundles | D | `tests/engine/duties/test_du_units.py::test_ast_person_events_come_only_from_decisions` | 1 |

類ごとの id の数: A 53・B 3・C 4・G 24・F 1・E 15・I 1・H 7・H(道具の役が直した) 2・D 25・B(道具の役が直した) 3・前から 1

## 直した後の全段の木(try6)で増えた 1 本

- `tests/tools/test_repo_guide.py::test_missing_ledger_is_reported`(類 E・runtime の段から): 作った木の台帳と系の表を消して、カードの入口に「`state_ledger.py が無い`」が出ることを確かめる。消す道は道具が新しい置き場に書き換え、`guide_permits.py` も新しい置き場を見るようになった(§10-10 の 5)ので、出る文は「`src/shibuya/runtime/state/ledger.py が無い`」になり、期待の字面(古いファイルの名)と合わない。try5 で通っていたのは、`guide_permits.py` が古い道を見ていて、作った木にも古い道が無かったから。
- try6 の全段の木で `tests/engine/bridging/`(全部)と `tests/tools/test_repo_guide.py` を回した結果: bridging は全部通る・repo_guide は 5 本落ちる(上の E 3・D 1 と、この 1 本)。
