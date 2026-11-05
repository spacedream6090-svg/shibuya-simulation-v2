# tests/tools

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 19 本・その他 0 本(このディレクトリの直下)

## [test_absent_declarations.py](../../../../../../tests/tools/test_absent_declarations.py)

第340 段 2 の 6: 「無いと宣言」の一覧の計器(tools/instruments/absent_declarations.py)。

- 公開の関数とクラス
  - `gauge`(関数)
  - `test_fingerprint_moves_when_a_declaration_changes`(関数)
  - `test_record_matches_the_current_output`(関数)
  - `test_render_is_deterministic_and_lists_every_declaration`(関数)
- 決定の ID: 11-01/§10-3・11-02r/§1・11-02r/§1 #7・第 340

## [test_anchor_gauge.py](../../../../../../tests/tools/test_anchor_gauge.py)

tools/instruments/anchor_gauge.py(第 2 期 2-0・較正側の錨の計器)の試験。

- 公開の関数とクラス
  - `G`(関数)
  - `RG`(関数)
  - `test_arrays_hash_ignores_meta_and_record_tracking`(関数)
  - `test_arrivals_table_counts_transitions_by_direction`(関数)
  - `test_daily_dwell_sum_vs_continuous`(関数)
  - `test_deny_hit_raw_first_does_not_touch_fs`(関数)
  - `test_dist_stats_weighted`(関数)
  - `test_duty_open_anchor_matches_w17_v2_draw`(関数): 錨 1 は W17 v2 の勤務窓(trial.draw_windows=第 31 表の逆関数法+arrival_lead)と同じ値。
  - `test_expansion_factors_restore_kind_mix`(関数)
  - `test_first_work_run_skips_overnight_and_short`(関数)
  - `test_four_quantities_deterministic_on_synthetic_record`(関数)
  - `test_gauge_rejects_journal_outside_list`(関数)
  - `test_gauge_writes_outputs_reads_only_listed_and_compare`(関数)
  - `test_guard_rejects_sealed_path_before_reading`(関数)
  - `test_guard_rejects_unlisted_and_audit_hook`(関数)
  - `test_make_guard_rejects_sealed_and_renamed_inputs`(関数)
  - `test_order_compare_ignores_separator_and_zero_change_text`(関数)
  - `test_population_masks_use_is_foreign_and_age`(関数)
  - `test_presence_theta_and_hour_axis_24_to_28`(関数)
  - `test_ratio_block_area_attribute_and_foreign_column`(関数)
  - `test_real_record_is_invariant_and_gauge_runs`(関数): 記録器を付けても final と呼数は同じ(エンジン不変)・2 腕の計器が 4 つの量を出す。
  - `test_real_static_anchors`(関数)
  - `test_rise_slot`(関数)
  - `test_theta_compared_in_seconds`(関数): θ は分で受けて秒で比べる(刻みが 30 秒なら 20 刻み=10 分)。
  - `test_time_dist_open_bins_follow_w12`(関数)
- import している内部モジュール: `shibuya.build.sched.trial`
- 決定の ID: R-115・第 337

## [test_anchor_gauge_meal_mark.py](../../../../../../tests/tools/test_anchor_gauge_meal_mark.py)

2-0 の計器の「第 18-1 表と比べた食事時刻の結果」の印(小さな版上げ・回答 10-13b §7 の 2)。

- 公開の関数とクラス
  - `G`(関数)
  - `test_mark_is_invalid_before_the_replacement_and_valid_after`(関数)
  - `test_markdown_carries_the_mark`(関数)
- 決定の ID: 10-13b/§7

## [test_batch_width_gauge.py](../../../../../../tests/tools/test_batch_width_gauge.py)

tools/instruments/batch_width_gauge.py(第 3 期 3-2・TM4 の既定の幅の試験の道具)の試験。

- 公開の関数とクラス
  - `G`(関数)
  - `test_a_large_difference_is_outside_and_not_a_candidate`(関数)
  - `test_bad_inputs_raise`(関数)
  - `test_final_mismatch_blocks_the_candidate`(関数)
  - `test_markdown_and_table_cli`(関数)
  - `test_run_one_records_the_shape`(関数)
  - `test_salt_width_is_the_salt_compare_width_base`(関数)
  - `test_zero_difference_table_has_every_width_within_and_monotone`(関数)

## [test_commit_check.py](../../../../../../tests/tools/test_commit_check.py)

tools/commit_check.py(第330): 一覧の改行の正規化とステージとの突き合わせ。git を使わない部分だけを試す。

- 公開の関数とクラス
  - `cc`(関数)
  - `test_bad_path_pattern_hits_absolute_paths_but_not_repo_paths`(関数)
  - `test_compare_ok_when_sets_match_regardless_of_order`(関数)
  - `test_compare_reports_missing_extra_and_dup`(関数)
  - `test_normalize_handles_crlf_bom_blank_and_comment`(関数)
  - `test_read_expect_from_crlf_file`(関数)
- 決定の ID: 第 329・第 330

## [test_dm_eval.py](../../../../../../tests/tools/test_dm_eval.py)

tools/instruments/dm_eval(第 6 期 6-1 判断モデルの評価の器・GPU の前の分)の試験。

- 公開の関数とクラス
  - `g_result`(関数)
  - `scenes`(関数)
  - `syn_result`(関数)
  - `test_agreement_is_zero_distance_against_itself`(関数)
  - `test_backend_failures_are_recorded_per_scene_and_do_not_stop_the_run`(関数)
  - `test_backend_identifier_names_avoid_banned_words`(関数)
  - `test_backend_scorers_position_bias_content_vs_positional`(関数)
  - `test_backends_package_lazy_names`(関数)
  - `test_blank_cells_carry_two_kinds_of_marks`(関数)
  - `test_candidates_come_from_the_five_sources`(関数)
  - `test_change_rate_formula`(関数)
  - `test_classical_scorer_splits_same_kind_mass_and_ignores_order`(関数)
  - `test_cli_main_both`(関数)
  - `test_cli_main_consumption`(関数)
  - `test_cli_main_without_tape_experience`(関数)
  - `test_compare_section_is_outside_the_golden_digest`(関数)
  - `test_consumption_render_short_and_long`(関数)
  - `test_consumption_scene_md5_mismatch_stops_reading`(関数)
  - `test_consumption_scenes_md5_and_counts`(関数)
  - `test_consumption_scenes_shape_and_new_words`(関数)
  - `test_consumption_scenes_use_no_real_names`(関数)
  - `test_content_only_scorers_have_zero_position_bias`(関数)
  - `test_determinism_check_repeats`(関数)
  - `test_evaluate_consumption_scenes`(関数)
  - `test_evaluate_is_deterministic`(関数)
  - `test_evaluate_with_g_reference_and_free_text`(関数)
  - `test_first_number_control_is_detected`(関数)
  - `test_free_text_explicit_other_is_not_breakdown`(関数)
  - `test_free_text_kanji_numbers`(関数)
  - `test_free_text_matcher`(関数)
  - `test_free_text_matcher_on_consumption_answers`(関数)
  - `test_free_text_negative_answers_do_not_hit_the_opposite_candidate`(関数)
  - `test_free_text_scorer_trace_and_breakdown_rate`(関数)
  - `test_gpu_hours_formula_values_blank_until_measured`(関数)
  - `test_hf_backend_lazy_import_and_logits_math`(関数)
  - `test_identifier_check_catches_planted_names`(関数)
  - `test_identifier_names_avoid_banned_words`(関数)
  - `test_known_values_jsd_spearman_entropy`(関数)
  - `test_logprob_breakdown_low_mass_and_boundary`(関数)
  - `test_logprob_scorer_distribution_shape_and_determinism`(関数)
  - `test_make_consumption_v1_reproduces_the_shipped_files`(関数)
  - `test_md5_mismatch_stops_reading`(関数)
  - `test_model_factories_without_network`(関数)
  - `test_model_ports_are_ports_only`(関数)
  - `test_normalize_checks`(関数)
  - `test_numbers_outside_money_time`(関数)
  - `test_order_blind_tape_rows_say_bias_is_zero_by_construction`(関数)
  - `test_orders_are_deterministic_and_cyclic`(関数)
  - `test_pbs_null_floor_known_values`(関数)
  - `test_qty_measures_on_what_how_many`(関数)
  - `test_real_evalset_once_matches_recorded_golden`(関数)
  - `test_real_tapes_match_the_recorded_md5`(関数)
  - `test_render_individual_blocks_short_b6_long_b5_b6`(関数)
  - `test_render_is_compose_with_common_part_first`(関数)
  - `test_scene_loader_rejects_bad_rows`(関数)
  - `test_scorers_are_frozen_after_construction`(関数)
  - `test_scorers_return_distributions`(関数)
  - `test_sealed_paths_fail_before_reading`(関数)
  - `test_sign_flip_is_salt_compare_formula`(関数)
  - `test_situation_language_fields_are_declared_blank`(関数)
  - `test_softmax_and_forms`(関数)
  - `test_split_blocks_roundtrip_and_order`(関数)
  - `test_strict_mode_catches_order_dependence`(関数)
  - `test_strict_mode_mock_and_classical_identical`(関数)
  - `test_surprise_reader`(関数)
  - `test_table_new_columns_and_old_columns_kept`(関数)
  - `test_table_shape_and_no_ranking`(関数)
  - `test_tape_experience_reads_prior_calls_newest_first`(関数)
  - `test_tape_fixed_order_is_record_only`(関数)
  - `test_tape_md5_mismatch_is_reported`(関数)
  - `test_vllm_echo_mode_slices_and_headers`(関数)
  - `test_vllm_prompt_logprobs_first_token_and_generate`(関数)
  - `test_vllm_token_boundary_and_http_errors`(関数)
  - `test_write_outputs_refuses_overwrite`(関数)
- import している内部モジュール: `shibuya.core.time_consts`・`shibuya.engine.decision.port`・`shibuya.llm.contract`・`tools/instruments/dm_eval/__init__.py`・`tools/instruments/dm_eval/backends/__init__.py`・`tools/instruments/dm_eval/backends/base.py`・`tools/instruments/dm_eval/backends/hf.py`・`tools/instruments/dm_eval/backends/vllm.py`・`tools/instruments/dm_eval/bias.py`・`tools/instruments/dm_eval/cli.py`・`tools/instruments/dm_eval/judge.py`・`tools/instruments/dm_eval/situations.py`・`tools/instruments/dm_eval/table.py`・`tools/instruments/read_guard.py`
- 読む試験(道筋で): `tests/tools/test_repo_guide.py`
- 決定の ID: 11-01

## [test_event_cost_bench.py](../../../../../../tests/tools/test_event_cost_bench.py)

tools/bench/event_cost/event_cost.py(指示書 11-03 §6-1・事象 1 件あたりの固定費)の小さな試験。

- 公開の関数とクラス
  - `E`(関数)
  - `doc`(関数)
  - `fake_table`(関数)
  - `test_bad_args`(関数)
  - `test_coefficients_positive`(関数)
  - `test_day_estimate_sum_only_sum_rows`(関数)
  - `test_markdown`(関数)
  - `test_shape`(関数)
- 決定の ID: 11-03/§6-1

## [test_hm_gauge.py](../../../../../../tests/tools/test_hm_gauge.py)

tools/instruments/hm_gauge.py(第 3 期 3-3b・ヒストリーマッチングの直接判定の器)の試験(合成の値だけ=器だけ)。

- 公開の関数とクラス
  - `H`(関数)
  - `test_guards`(関数)
  - `test_implausibility_formula`(関数)
  - `test_judge_keeps_and_drops_by_the_second_largest`(関数)
  - `test_read_guard_catches_upper_case_and_junction`(関数)

## [test_las_pointcloud_agg.py](../../../../../../tests/tools/test_las_pointcloud_agg.py)

tools/spatial/las_pointcloud_agg(都の区部点群の集計・指示書 11-02 取得 1)の試験。実データは読まない。

- 公開の関数とクラス
  - `test_dem_min_dsm_max_in_one_pixel`(関数)
  - `test_detect_steps_and_curb_metrics`(関数)
  - `test_extract_rejects_other_members`(関数)
  - `test_fetch_log_first_row_and_conflict`(関数)
  - `test_fill_polygon_window_with_hole`(関数)
  - `test_fill_push_pull`(関数)
  - `test_gsi_service_points`(関数)
  - `test_identifier_names_avoid_banned_words`(関数)
  - `test_las_rejects_bad`(関数)
  - `test_las_roundtrip`(関数)
  - `test_las_without_crs_vlr_passes_by_bbox`(関数)
  - `test_load_plateau_inputs_reads_tran_gml`(関数)
  - `test_local_plane_roundtrip`(関数)
  - `test_mode_and_block_mean`(関数)
  - `test_parse_fetch_log`(関数)
  - `test_plateau_inputs_deck_sources_and_curb`(関数)
  - `test_polygons_of_rings_and_rasterize`(関数)
  - `test_run_synthetic_world`(関数)
  - `test_sealed_paths_are_refused`(関数)
  - `test_sha_mismatch_is_skipped`(関数)
  - `test_sources_have_no_absolute_paths_or_crlf`(関数)
  - `test_swapped_axes_are_refused`(関数)
  - `test_tilestore_merge_min_max`(関数)
  - `test_without_log_only_named_meshes`(関数)
  - `test_wrong_epsg_is_refused`(関数)
  - `test_zone9_origin`(関数)
- import している内部モジュール: `tools/spatial/jgd_plane.py`・`tools/spatial/las_io.py`・`tools/spatial/las_pointcloud_agg.py`
- 決定の ID: 11-02

## [test_leak_check.py](../../../../../../tests/tools/test_leak_check.py)

tools/instruments/leak_check(回答 11-01 §6・段 1 の 4 の漏洩の検査の器)の試験。

- 公開の関数とクラス
  - `test_abs_path_check`(関数)
  - `test_block_sequence_rules`(関数)
  - `test_choice_distribution_floor_and_token_forms`(関数)
  - `test_cli_argument_checks`(関数)
  - `test_cli_mock_three_types`(関数)
  - `test_cli_summary`(関数)
  - `test_distribution_tools_known_values`(関数)
  - `test_expect_md5_with_missing_file_stops`(関数)
  - `test_fictional_events_do_not_borrow_real_forms`(関数)
  - `test_fictional_names_keep_structure_and_swap_brand_only`(関数)
  - `test_identifier_check_catches_planted_names`(関数)
  - `test_identifier_names_avoid_banned_words`(関数)
  - `test_mock_is_deterministic_and_digest_excludes_time`(関数)
  - `test_model_cutoff_splits_sides`(関数)
  - `test_performance_gap_known_values`(関数)
  - `test_recall_tools_known_values`(関数)
  - `test_result_has_no_response_text`(関数)
  - `test_sealed_and_ledger_paths_refused_before_reading`(関数)
  - `test_sets_carry_no_validation_side_words`(関数)
  - `test_sets_on_disk_match_builders`(関数)
  - `test_specific_name_marks`(関数)
  - `test_summarize_pairs_known_values`(関数)
  - `test_summarize_type1_with_and_without_other`(関数)
  - `test_type1_classifiers`(関数)
  - `test_type1_counts_and_sides`(関数)
  - `test_type1_english_refusals_and_marks`(関数)
  - `test_type1_event_line_wins_over_hedge`(関数)
  - `test_type1_mix_order_depends_on_seed`(関数)
  - `test_type1_more_japanese_refusals_and_denials`(関数)
  - `test_type1_real_event_side_by_day`(関数)
  - `test_type1_real_events_mixed_and_md5`(関数)
  - `test_type1_rejects_bad_real_rows`(関数)
  - `test_type1_unknown_phrasings`(関数)
  - `test_type2_below_floor_counted`(関数)
  - `test_type2_mixed_sources_are_kept_apart`(関数)
  - `test_type2_name_blind_backend_gives_zero`(関数)
  - `test_type2_name_loving_backend_shifts_toward_name`(関数)
  - `test_type2_pairs_differ_only_by_name`(関数)
  - `test_type4_templates_have_no_reference_text`(関数)
  - `test_type4_with_refs_known_answers`(関数)
  - `test_vllm_payload_and_headers`(関数)
  - `test_vllm_type2_through_transport`(関数)
  - `test_vllm_without_key_and_failures`(関数)
- import している内部モジュール: `tools/instruments/leak_check/__init__.py`・`tools/instruments/leak_check/backends.py`・`tools/instruments/leak_check/cli.py`・`tools/instruments/leak_check/run.py`・`tools/instruments/leak_check/score.py`・`tools/instruments/leak_check/sets.py`・`tools/instruments/read_guard.py`
- 決定の ID: 11-01/§6

## [test_night5070.py](../../../../../../tests/tools/test_night5070.py)

tools/night5070(回答 10-25 §6-0): 夜の実験の起動・健全性の確認・計測の分離の一覧・タスクの XML。

- 公開の関数とクラス
  - `awake_calls`(関数)
  - `fake_fleet`(関数)
  - `nr`(関数)
  - `quiet_machine`(関数): 手元の機械の状態(WSLENV・.wslconfig・GPU)を試験から切り離す。
  - `real_cfg`(関数)
  - `rt`(関数)
  - `test_acl_note_in_summary_without_user_name`(関数)
  - `test_api_keys_differ_per_run`(関数)
  - `test_background_start_is_stopped`(関数)
  - `test_broken_tape_and_checkpoints_are_unreadable`(関数)
  - `test_check_principal_xml_rejects_tampered`(関数)
  - `test_cleanup_failure_wins_over_zero_answers`(関数)
  - `test_current_user_id_is_user`(関数)
  - `test_deadline_exceeded_stops_fleet`(関数)
  - `test_deadline_not_shorter_than_limit_is_refused`(関数)
  - `test_delete_print_only`(関数)
  - `test_dry_run_shows_safety_failures_without_stopping`(関数)
  - `test_dry_run_with_holes_lists_undecided_rules`(関数)
  - `test_dry_run_writes_summary_without_running`(関数)
  - `test_exit_codes_are_distinct`(関数)
  - `test_experiment_env_gets_fleet_key_and_logs_are_scrubbed_early`(関数)
  - `test_failed_command_writes_failure_and_stops_fleet`(関数)
  - `test_filled_vars_remove_holes_and_list_splices`(関数)
  - `test_fleet_commands_get_no_wslenv`(関数)
  - `test_full_run_keeps_default_agents_and_steps`(関数)
  - `test_health_check_fails_on_empty_completion`(関数)
  - `test_health_check_passes_with_fake_fleet`(関数)
  - `test_health_check_rejects_other_served_model`(関数)
  - `test_health_check_times_out_without_fleet`(関数)
  - `test_health_failure_stops_fleet`(関数)
  - `test_holes_stop_before_fleet`(関数)
  - `test_icacls_restricts_key_file`(関数)
  - `test_keep_fleet_still_removes_key_file`(関数)
  - `test_key_file_removal_error_still_writes_records`(関数)
  - `test_mask_paths`(関数)
  - `test_metrics_partial_stdout_without_fleet_line`(関数)
  - `test_metrics_unmeasured_when_outputs_missing`(関数)
  - `test_mock_experiment_skips_fleet`(関数)
  - `test_nested_var_holes_and_expansion`(関数)
  - `test_night_runs_log_is_masked`(関数)
  - `test_no_firewall_calls_in_experiment_commands`(関数)
  - `test_no_firewall_defender_or_network_setting_calls`(関数)
  - `test_parse_vram`(関数)
  - `test_plan_vram_shortage_and_unmeasured`(関数)
  - `test_plan_vram_three_steps`(関数)
  - `test_prestop_failure_still_measures_vram`(関数)
  - `test_prestop_runs_before_safety_and_vram_and_frees_last_night`(関数)
  - `test_print_only_masks_user_id_and_refuses_system`(関数)
  - `test_print_only_xml_battery_and_wake`(関数)
  - `test_query_vram_reads_nvidia_smi_or_unmeasured`(関数)
  - `test_read_tape_counts_and_answered_only_tokens`(関数)
  - `test_read_tape_reads_only_needed_columns`(関数)
  - `test_readme_lists_safety_rules_and_checks`(関数)
  - `test_real_config_e1_requires_answers`(関数)
  - `test_real_config_e1_smoke_holes_and_defaults`(関数)
  - `test_real_config_has_e1_to_e8_and_blank_estimates`(関数)
  - `test_real_config_holes_detected`(関数)
  - `test_register_refuses_worktree`(関数)
  - `test_require_answers_gate`(関数)
  - `test_run_dir_never_overwrites`(関数)
  - `test_safety_api_key_by_env_or_arg`(関数)
  - `test_safety_api_key_negative`(関数)
  - `test_safety_checks_endpoints_must_be_loopback`(関数)
  - `test_safety_checks_fail_each`(関数)
  - `test_safety_checks_pass_on_good_config`(関数)
  - `test_safety_checks_quoted_abbrev_and_config`(関数)
  - `test_safety_checks_read_argv_list_and_unsplittable`(関数)
  - `test_safety_checks_wsl_nat`(関数)
  - `test_safety_checks_wslenv_names_only`(関数)
  - `test_safety_env_key_twice_fails`(関数)
  - `test_safety_failure_skips_prestop`(関数)
  - `test_safety_rechecked_after_vram_adjustment`(関数)
  - `test_safety_rejects_shell_expansion`(関数)
  - `test_safety_shell_expansion_ok_on_plain_command`(関数)
  - `test_safety_violation_stops_before_fleet`(関数)
  - `test_set_and_get_flag`(関数)
  - `test_smoke_dry_run_lists_overrides`(関数)
  - `test_smoke_requires_definition`(関数)
  - `test_smoke_run_overrides_and_masks_api_key`(関数)
  - `test_start_failure_stops_fleet`(関数)
  - `test_stop_failure_marks_cleanup_failed`(関数)
  - `test_success_run_fills_metrics`(関数)
  - `test_summary_writer_failure_still_writes_all`(関数)
  - `test_trust_remote_code_in_vllm_args_stops`(関数)
  - `test_unexpected_exception_stops_fleet`(関数)
  - `test_unknown_experiment_is_config_error`(関数)
  - `test_vllm_args_list_stays_list`(関数)
  - `test_vram_adjusts_start_args_and_metrics`(関数)
  - `test_vram_bad_number_is_config_error`(関数)
  - `test_vram_flags_added_when_absent`(関数)
  - `test_vram_remeasures_once_before_shortage`(関数)
  - `test_vram_shortage_stops_before_fleet`(関数)
  - `test_vram_unmeasured_keeps_settings`(関数)
  - `test_vram_waits_for_release_after_prestop`(関数)
  - `test_wait_vram_settle_gives_up_after_limit`(関数)
  - `test_wait_vram_settle_until_two_equal_reads`(関数)
  - `test_wslenv_key_name_stops_without_reading_value`(関数)
  - `test_wslenv_secret_like_name_stops`(関数)
  - `test_xml_powershell_trigger_and_workdir`(関数)
  - `test_xml_principal_is_user_not_system`(関数)
  - `test_xml_refuses_non_user_principal`(関数)
- 環境変数: `SHIBUYA_FLEET_API_KEY`
- 決定の ID: 10-25/§6-0・11-01・R-123・第 340

## [test_realworld_fetch_jinryu.py](../../../../../../tests/tools/test_realworld_fetch_jinryu.py)

第333(R-114): 渋谷区の人流の再取得で 2025 年以降の行が開封済みの層に混ざらない(合成の行だけ・実データは読まない)。

- 公開の関数とクラス
  - `test_opened_layer_max_year_is_the_last_opened_year`(関数)
  - `test_split_k5_keeps_2024_and_earlier_and_splits_later_years`(関数)
  - `test_year_parsing_tolerates_formats`(関数)
- import している内部モジュール: `tools/realworld_fetch/shibuya_jinryu.py`
- 決定の ID: R-114・第 333

## [test_realworld_fetch_logrotate.py](../../../../../../tests/tools/test_realworld_fetch_logrotate.py)

tools/realworld_fetch/logrotate.py(第337・取得の台帳とログを日ごとに回して gzip で縮める)の試験。

- 公開の関数とクラス
  - `test_busy_writer_is_left_alone`(関数)
  - `test_cli_rotate_logs`(関数)
  - `test_crash_after_rename_loses_nothing_and_reads_once`(関数)
  - `test_day_never_goes_back_and_chunks_concatenate`(関数)
  - `test_fresh_lock_moved_by_mistake_is_put_back`(関数): 古いと見た後にほかの回しが新しい錠を作っていたら、移した錠を元へ戻して進まない(新しい錠を消さない)。
  - `test_lock_excludes_a_second_rotator_and_stale_lock_is_cleared`(関数)
  - `test_maybe_rotate_once_a_day`(関数)
  - `test_new_lines_after_rotation_follow_the_archives`(関数)
  - `test_reader_retries_when_a_rotation_runs_mid_read`(関数): 〔検収 L3〕読みの途中で回しが走っても(生きているファイルが消える・gz が増える)読み落とさない。
  - `test_reader_retries_when_the_listing_changes`(関数)
  - `test_report_and_verify_read_through_archives`(関数)
  - `test_rotate_ledger_by_jst_day_is_byte_exact`(関数)
  - `test_spec_table_is_read_only`(関数)
  - `test_stale_lock_is_cleared_only_by_the_one_that_moved_it`(関数): 〔検収 L4〕古い錠を移せなかった側(ほかの回しが先に片付けた)は進まない。
  - `test_two_rotations_in_the_same_clock_tick_keep_the_order`(関数): 〔第337〕時計の刻みが粗い(Windows の Python 3.12)と 2 回の回しが同じ rotid になる → 並びが崩れず・名が重ならない。
  - `test_utf16_log_rotates_as_one_chunk`(関数)
  - `test_verify_mismatch_keeps_the_rotating_file`(関数)
  - `test_writer_handle_blocks_rename_on_windows`(関数)
  - `test_writer_keeps_appending_during_rotations`(関数): 書き手(``ledger.append``)が追記を続けている間に何度も回す: 書き手は落ちず、行は 1 つも失わず重ならない。
- import している内部モジュール: `tools/realworld_fetch/cli.py`・`tools/realworld_fetch/ledger.py`・`tools/realworld_fetch/logrotate.py`
- 決定の ID: 第 337

## [test_realworld_fetch_odpt.py](../../../../../../tests/tools/test_realworld_fetch_odpt.py)

tools/realworld_fetch の ODPT の取得(第333): 全路線の保存・gzip・間隔・変化分だけ・欠けた時間帯・静的データの版と --check・秘密が出ないこと。ネットワークには出ない(`common._urlopen` を差し替える)。

- 公開の関数とクラス
  - `FakeODPT`(クラス): `common._urlopen` の代わり。(枠, 種類) ごとの関数が params からレコードの並びを返す。
  - `fake`(関数)
  - `test_batches_respects_size_and_budget`(関数)
  - `test_bus_capped_is_split_by_route_with_static_routes`(関数)
  - `test_cadence_skips_until_due_and_force_overrides`(関数)
  - `test_content_hash_ignores_time_fields_and_order`(関数)
  - `test_cross_host_redirect_refused_and_not_retried`(関数)
  - `test_dedupe_unchanged_info_not_saved_and_marked_in_ledger`(関数)
  - `test_due_rule`(関数)
  - `test_empty_response_writes_no_file`(関数)
  - `test_failed_part_keeps_other_parts_and_job_errors_are_isolated`(関数)
  - `test_frequent_run_skips_full_ledger_report`(関数)
  - `test_gzip_written_and_readable_and_verify_reads_both`(関数)
  - `test_no_secret_in_any_saved_file_url_or_output`(関数)
  - `test_offline_makes_zero_requests`(関数)
  - `test_open_saves_all_records_and_challenge_keeps_work_scope`(関数)
  - `test_report_includes_rt_gaps_and_disk_usage`(関数)
  - `test_rt_gap_report_counts_missing_hours_and_runs`(関数)
  - `test_rt_gap_report_first_day_starts_at_first_row_and_old_rows_cluster`(関数)
  - `test_static_or_batches_halve_when_capped`(関数)
  - `test_static_version_splits_capped_and_check_lists_newer`(関数)
- import している内部モジュール: `tools/realworld_fetch/cli.py`・`tools/realworld_fetch/common.py`・`tools/realworld_fetch/ledger.py`・`tools/realworld_fetch/odpt_rt.py`・`tools/realworld_fetch/odpt_static.py`
- 決定の ID: 10-12・第 333

## [test_repo_guide.py](../../../../../../tests/tools/test_repo_guide.py)

tools/repo_guide(段 3 ファイルのカード・11-05/§3-1 の 1)の試験。

- 公開の関数とクラス
  - `guide`(関数): build.py を読み込んだモジュール(``guide.F``・``guide.P``・``guide.R`` が部品)。
  - `real_blocks`(関数): 本物のリポのファイル → カードの節。
  - `real_code`(関数)
  - `repo`(関数)
  - `test_ascii_lines_join_with_a_space`(関数)
  - `test_card_contents_summary_public_imports_callers_tests`(関数)
  - `test_check_does_not_even_list_data`(関数)
  - `test_check_finds_differences`(関数)
  - `test_check_ignores_docs_data_and_entry_readme`(関数)
  - `test_cli_and_env_of_a_tool`(関数)
  - `test_crlf_source_gives_same_cards`(関数)
  - `test_data_files_are_never_read`(関数)
  - `test_data_size_uses_units`(関数)
  - `test_decision_ids_rules`(関数)
  - `test_decision_ids_without_prefix_list`(関数)
  - `test_decision_sort_key_breaks_ties_by_text`(関数)
  - `test_docs_index_and_entry_readme`(関数)
  - `test_git_listing_includes_untracked_and_reports_them`(関数)
  - `test_ledger_rows_and_owner`(関数)
  - `test_link_shapes_in_text_are_escaped`(関数)
  - `test_links_in_data_are_not_followed_or_sized`(関数)
  - `test_masks_words_of_both_checkers`(関数)
  - `test_missing_ledger_is_reported`(関数)
  - `test_no_data_dir_keeps_old_list_and_readme_does_not_change`(関数)
  - `test_problems_stop_at_the_listed_dir_and_hide_deep_names`(関数)
  - `test_public_inside_if_try_with_but_not_nested`(関数)
  - `test_real_bare_imports_are_resolved_or_marked`(関数): tests と tools に同じ名が 1 つだけある素の import は、解けるか、カードに印が付く(H1 の再発の守り)。
  - `test_real_cards_have_no_link_shapes_in_text`(関数)
  - `test_real_imports_and_env_match_line_regex`(関数): import と環境変数: カードと、行の正規表現(AST を使わない別の読み方)を比べる(本物の全ファイル)。
  - `test_real_item_numbers_are_attached_to_a_head`(関数): ``#N`` は接頭につながる形だけ(単独の ``#N`` は載せない)。
  - `test_real_known_edges_of_syspath_forms`(関数): 検収で落ちていた辺(ループの変数・``.parent.parent``・``parents[1]``・``ROOT / sub``)。
  - `test_real_ledger_rows_match_import`(関数)
  - `test_real_public_names_match_import`(関数): 公開の関数とクラス: カードと、実物を import した ``vars()`` を比べる(軽いモジュールの全部)。
  - `test_real_write_permits_match_import`(関数)
  - `test_relative_imports_and_import_module`(関数)
  - `test_subdirs_are_sorted`(関数)
  - `test_syspath_added_by_an_imported_module_and_by_package_init`(関数)
  - `test_syspath_forms_are_read_and_unread_ones_are_counted`(関数)
  - `test_tests_by_path_and_syspath_of_conftest`(関数)
  - `test_two_builds_same_bytes_lf_no_abs_paths`(関数)
  - `test_unparsable_file_is_reported_not_guessed`(関数)
  - `test_unresolved_bare_import_gets_a_mark`(関数)
  - `test_write_permits_from_table`(関数)
- import している内部モジュール: `shibuya.engine.state_ledger`・`shibuya.engine.systems.allow`・`shibuya.engine.systems.spec`・`shibuya.engine.systems.table`
- 環境変数: `os.environ` をまるごと使う
- 決定の ID: 10-12・10-12/D-9・10-13b・10-13b/K3・10-13b/K3 #5・10-25・10-25/§2-5・11-01・11-01/A1-2・11-01/a01・11-01/a1・11-01/§1・11-01/§1 #7・11-01/§1 #8・11-01/§1 #12・11-05/§3-1・R-9・R-9 #3・R-126・R-126 §1-4 #46・D-74・D-74 #4・第 170・第 275・第 275 #7・第 340・第 345・第 345 #2・第 1000

## [test_scan_secrets_cp932.py](../../../../../../tests/tools/test_scan_secrets_cp932.py)

第333(検収 L8): 秘密スキャンは cp932 のファイル(祝日の fixture)を文字化けで偽陽性にしない。

- 公開の関数とクラス
  - `test_cp932_file_is_decoded_not_replaced`(関数)
  - `test_cp932_fixture_is_clean`(関数)
- 決定の ID: 第 333

## [test_seal_split_337.py](../../../../../../tests/tools/test_seal_split_337.py)

第337 封印の分離の残り(回答 10-13b §7 の 5): 分けた錨のファイルと読み口の守りの試験。

- 公開の関数とクラス
  - `test_build_side_copy_equals_the_original_anchors`(関数)
  - `test_core9_calib_copies_agree`(関数)
  - `test_gauge_guard_allows_the_build_side_names`(関数)
  - `test_gauge_guard_denies_the_validation_side`(関数)
  - `test_md5_helper_is_order_free`(関数)
  - `test_old_odpt_rt_dir_is_sealed_for_both_guards`(関数)
  - `test_plan_has_a_reason_for_every_anchor_and_no_overlap`(関数)
  - `test_plan_tables_are_read_only`(関数)
  - `test_split_doc_refuses_unknown_names`(関数)
  - `test_yardstick_fixture_reads_no_validation_file_and_the_hook_works`(関数)
- import している内部モジュール: `shibuya.build.pop.w21_sources`・`tools/instruments/anchor_split.py`・`tools/instruments/read_guard.py`・`tools/w17/diversity_yardstick.py`
- 読む試験(道筋で): `tests/tools/test_repo_guide.py`
- 決定の ID: 10-13b/§7・第 337

## [test_skill_gauge.py](../../../../../../tests/tools/test_skill_gauge.py)

tools/instruments/skill_gauge.py(第 3 期 3-3b・CP14 の技量スコアの隣の生の点数)の試験。

- 公開の関数とクラス
  - `S`(関数)
  - `test_crps_known_values`(関数)
  - `test_rank_histogram_and_spread_skill`(関数)
  - `test_read_guard_on_the_input`(関数)
  - `test_scores_of_a_mock_ensemble`(関数)
  - `test_skill_next_to_raw_scores_and_fill_the_container`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.experiment.ensemble`・`tests/engine/experiment/_x33.py`

## [test_warmup_gauge.py](../../../../../../tests/tools/test_warmup_gauge.py)

tools/instruments/warmup_gauge.py(第 3 期 3-3b・CP5-6 慣らしの自動判定の器)の試験(合成の系列だけ=データ不要)。

- 公開の関数とクラス
  - `G`(関数)
  - `test_cli_and_read_guard`(関数)
  - `test_counter_paths_are_differenced_and_unmarked_ones_are_refused`(関数)
  - `test_cumulative_series_is_the_negative_control`(関数)
  - `test_difference_series_finds_what_the_raw_arm_misses`(関数)
  - `test_latter_half_is_invalid_and_extended`(関数)
  - `test_metric_table_is_read_only`(関数)
  - `test_metric_table_stock_transition_placeholder_and_bundle`(関数)
  - `test_mser_formula_by_hand`(関数)
  - `test_planted_warmup_is_found`(関数)
  - `test_question2_intervals`(関数)
  - `test_read_guard_catches_upper_case_and_junction`(関数)
  - `test_stock_warmup_days_count_from_the_series_head`(関数)
- import している内部モジュール: `shibuya.engine.experiment.warmup`
