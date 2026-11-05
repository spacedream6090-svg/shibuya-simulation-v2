# tests/c7

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 13 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../tests/c7/__init__.py)

tests.c7 — C7 受入計器(``tools/c7``)の純関数検査。

## [conftest.py](../../../../../../tests/c7/conftest.py)

tests.c7 の共通フィクスチャ。

- 公開の関数とクラス
  - `accept`(関数)
  - `c7lib`(関数)
  - `hold`(関数)
  - `occ`(関数)
  - `seal_hit`(関数): リポの data/・docs/ の下で守りの語を含む道筋なら、その語(無ければ None)。ファイルシステムには触らない。
  - `synth_holdout`(関数): 合成 holdout を書いて、``(path, doc)`` を返す。
  - `synth_holdout_doc`(関数): **合成 holdout**(KDDI 生 JSON と同じ形の偽データ)。
  - `toy_axes`(関数): 合成の境界定義(原点中心・南北軸=x=0・東西軸=y=0・中心=原点の小矩形)。
  - `world_dir`(関数)
- import している内部モジュール: `tools/c7/c7_accept.py`・`tools/c7/c7lib.py`・`tools/c7/holdout_compare.py`・`tools/c7/occupancy_series.py`・`tools/instruments/read_guard.py`
- 読む試験: `tests/c7/test_area_map.py`・`tests/c7/test_holdout_compare.py`・`tests/c7/test_seal_guard_337.py`
- 決定の ID: 第 337

## [test_accept_table.py](../../../../../../tests/c7/test_accept_table.py)

C7 受入表(``c7_accept.py``)とラン要約の読み取りの検査。

- 公開の関数とクラス
  - `test_budget_limits_reads_markdown`(関数)
  - `test_build_table_flags_budget_overrun`(関数)
  - `test_build_table_full_pass`(関数)
  - `test_build_table_missing_diag_rows`(関数)
  - `test_build_table_missing_inputs_are_unjudged`(関数)
  - `test_cli_full_option_fills_t2c_only`(関数)
  - `test_cli_writes_outputs`(関数)
  - `test_determinism_detects_divergence`(関数)
  - `test_determinism_full_match`(関数)
  - `test_determinism_prefix_mode`(関数): T2-b: 部分再ランは前方一致で合格・食い違えば不合格。
  - `test_determinism_reads_run_hash_payload`(関数): ``tools/c6/run_hash.py`` の payload(文字列リスト)も読める。
  - `test_dir_bytes`(関数)
  - `test_parse_run_summary`(関数)
  - `test_parse_run_summary_missing_fields_stay_none`(関数): 読めなかった欄は None のまま(**推測で埋めない**)。
  - `test_parse_time_v`(関数)
  - `test_selfconsistency`(関数)
  - `test_selfconsistency_checks_replay_final_hash_prefix`(関数): --full(テープ再生)は本番 summary の 16 桁 final_hash と前方一致することも要求する。
  - `test_table_markdown_mentions_t2_substitution`(関数)
- 決定の ID: D-54

## [test_area_map.py](../../../../../../tests/c7/test_area_map.py)

セル→5エリア写像(``c7lib.classify_cells`` / ``build_area_map``)の検査。

- 公開の関数とクラス
  - `test_area_map_json_roundtrip`(関数)
  - `test_axes_file_is_declared_expedient`(関数): 境界定義ファイルは **expedient** と当てはめの経緯を必ず宣言している。
  - `test_build_area_map_shape_and_ha`(関数): 格子中心での分類・面積[ha]は GL セルだけ数える。
  - `test_classify_dilate_moves_boundary`(関数): ±dilate で外縁と中心が膨らむ(感度試験の口が効いている)。
  - `test_classify_toy_quadrants`(関数): 合成幾何: 4 象限 + 中心 + 圏外が期待どおりに落ちる。
  - `test_polyline_side_signs`(関数): 折れ線の左右判定: 北→南の線は西が負、西→東の線は北が正。
  - `test_real_world_map_gate`(関数): 実資産(520 セル)で 5 エリアが全て非空・面積帯を満たす。
  - `test_real_world_sensitivity_reported`(関数): ±50m の感度が測れて、動くセルが 2 割未満(写像が崩壊していない)。
- import している内部モジュール: `tests/c7/conftest.py`

## [test_attr_arms.py](../../../../../../tests/c7/test_attr_arms.py)

KDDI 写像の感度腕(在圏の形 9b・``tools/c7/attr_arms.py``)の検査(合成データ)。

- 公開の関数とクラス
  - `aa`(関数)
  - `test_agent_axes_follow_rows_and_guard_the_row_rule`(関数)
  - `test_area_map_is_resident_first_then_worker_then_visitor`(関数)
  - `test_dwell0_kind_arm_equals_the_engine_journal_formula`(関数): 体の journal の既定腕(kind・滞在 0・20 歳未満を含む)= 種別 × セルの集計 → ``kind_cell_to_area_attr``。
  - `test_dwell30_needs_a_continuous_stay_inside_the_hour`(関数)
  - `test_exclude_under20_drops_the_young`(関数)
  - `test_kind_journal_rows_list_what_cannot_be_computed`(関数)
  - `test_kind_maps_differ_only_for_students`(関数)
  - `test_recorder_restores_resolve_apply`(関数)
  - `test_shape_metrics_do_not_judge_and_leave_h1_blank`(関数)
- import している内部モジュール: `shibuya.engine.resolve`・`tools/c7/attr_arms.py`
- 読む試験(道筋で): `tests/tools/test_repo_guide.py`

## [test_holdout_compare.py](../../../../../../tests/c7/test_holdout_compare.py)

holdout 照合の検査。**本物の KDDI データは開かない**——合成 holdout だけを使う。

- 公開の関数とクラス
  - `test_area_composition_detects_shift`(関数)
  - `test_check_seal_detects_mismatch`(関数)
  - `test_check_seal_empty_members_raises`(関数)
  - `test_find_table_nested`(関数)
  - `test_five_metrics_identical_passes`(関数)
  - `test_five_metrics_level_invariant`(関数): **絶対水準は判定に効かない**(D1′「値は形状と比のみ」)。
  - `test_five_metrics_missing_inputs_are_not_measured`(関数)
  - `test_five_metrics_shifted_peaks_fail`(関数): ピークを 5 時間ずらすと H1(形)と H2(ピーク)が落ちる。
  - `test_guard_allows_first_open`(関数)
  - `test_guard_refuses_second_open`(関数)
  - `test_guard_requires_explicit_flag`(関数)
  - `test_hour_bin_conversion`(関数)
  - `test_load_seal_unknown_layer`(関数)
  - `test_metrics_markdown_has_all_rows`(関数)
  - `test_prereg_thresholds_are_declared`(関数): 事前登録案が『案』であること・下限対照が v1 テンプレ水準であることを固定する。
  - `test_read_holdout_shapes`(関数)
  - `test_read_holdout_unknown_table_raises`(関数)
  - `test_report_does_not_leak_absolute_levels`(関数): 報告に**実数(拡大推計値)**が出ない=D1′『形状と比のみ』の機械的な確認。
  - `test_resolve_fields_aliases_and_failure`(関数)
  - `test_resolve_fields_explicit_override`(関数)
  - `test_second_write_keeps_the_first_record_in_history`(関数): 第176(層2 指摘 A): --force の 2 本目で主張腕の初回開封の証跡が消えない。
  - `test_sim_from_occupancy_shape_check`(関数)
  - `test_tau_undefined_is_reported_not_hidden`(関数): 全エリアが同じピーク時刻だと τ-b は定義できない。FAIL にしつつ理由を残す。
- import している内部モジュール: `tests/c7/conftest.py`
- 決定の ID: 第 176

## [test_occupancy_series.py](../../../../../../tests/c7/test_occupancy_series.py)

在圏時系列(標本化・エリア集計・形状の量・journal)の検査。

- 公開の関数とクラス
  - `test_by_area_and_hour_table`(関数)
  - `test_counts_to_area_attr_matches`(関数)
  - `test_hour_table_averages_repeated_hours`(関数): 同じ時に複数標本(5分刻み)があれば平均する。
  - `test_journal_roundtrip`(関数)
  - `test_kendall_tau_known`(関数)
  - `test_kind_cell_to_area_attr`(関数): 種別×セル → エリア×属性(``KIND_TO_ATTR`` の写像が効く)。
  - `test_recorder_context_manager_restores_on_error`(関数)
  - `test_recorder_does_not_write_world`(関数): 標本化は**読み取りだけ**(密度配列の同一性・内容が変わらない)。
  - `test_recorder_samples_every_and_restores`(関数): ``every`` の倍数だけ標本化し、detach で元の ``apply`` に戻る。
  - `test_series_cell_count_mismatch_raises`(関数)
  - `test_shape_quantities`(関数): 時刻シェア・ピーク時刻・深夜残存率・エリア構成の定義を数値で固定する。
  - `test_toy_map_is_one_cell_per_quadrant`(関数)

## [test_prereg_v13.py](../../../../../../tests/c7/test_prereg_v13.py)

事前登録 **v1.3**(seed アンサンブル判定)の検収。**本物の holdout も本物の occupancy も読まない**。

- 公開の関数とクラス
  - `test_a_all_inside_with_small_sd_passes`(関数)
  - `test_b_near_the_line_with_large_sd_is_undecided_and_needs_more_seeds`(関数)
  - `test_b_unsolvable_when_the_mean_sits_on_the_line`(関数): 平均が線ちょうど=距離 0 は seed をいくら足しても解けない(None)。
  - `test_c_all_outside_fails`(関数)
  - `test_c_fail_beats_undecided_inside_one_metric`(関数): 1 統計量が fail・もう 1 つが undecided なら指標は fail(1 ラン版の AND と同じ向き)。
  - `test_c_lower_bound_line_fails_when_entirely_below`(関数): 下限の線(Pearson r ≥ 0.80)は区間が全部下なら fail。
  - `test_d_h3_is_descriptive_and_not_counted`(関数)
  - `test_e_alpha_other_than_001_is_refused`(関数)
  - `test_e_family95_half_width_matches_t995_df2`(関数)
  - `test_e_integer_statistic_uses_min_max`(関数): H2 の ``n_within`` は整数なので区間は seed ごとの最小/最大。
  - `test_e_mixed_lines_across_seeds_raise`(関数)
  - `test_e_one_seed_is_refused`(関数)
  - `test_e_undefined_tau_is_failed_not_hidden`(関数): τ-b が 1 本でも未定義なら fail に倒し、理由を残す(推測で埋めない)。
  - `test_e_unmeasured_metric_is_not_counted`(関数)
  - `test_f_deterministic_ensemble_crps_is_absolute_error`(関数)
  - `test_f_fair_crps_needs_two_members`(関数)
  - `test_f_fair_crps_reuses_c8_estimator`(関数)
  - `test_f_fair_crps_second_term_ratio_is_m_over_m_minus_1`(関数)
  - `test_f_fair_crps_table_over_area_hour_cells`(関数)
  - `test_g_report_declares_get_is_not_a_test`(関数)
  - `test_g_report_without_optional_blocks`(関数)
  - `test_get_envelope_counts_and_is_not_a_test`(関数)
  - `test_get_envelope_detects_outside_hours`(関数)
  - `test_get_envelope_shape_mismatch_raises`(関数)
  - `test_h1_day_window_length_mismatch_raises`(関数)
  - `test_h1_day_window_slices_and_renormalises`(関数)
  - `test_h1_judged_on_day_window_and_24h_kept_as_description`(関数)
  - `test_h1_without_day_window_says_so`(関数)
  - `test_h_cli_default_prereg_version_is_v12`(関数)
  - `test_h_default_report_is_byte_for_byte_the_v12_text`(関数): ``report`` の既定(``v13_section=None``)は v1.2 の文面そのまま。
  - `test_h_ensemble_verdict_does_not_mutate_inputs`(関数)
  - `test_h_v12_result_dict_is_plain_five_metrics`(関数): ``compare`` は ``five_metrics`` そのまま=v1.3 の追加で結果 dict が変わらない。
  - `test_i_main_refuses_before_touching_the_seal`(関数): 版と本数の不整合は**封印に触る前**に落ちる(``--open-seal`` は一切渡さない)。
  - `test_i_unknown_version_and_empty_list`(関数)
  - `test_i_v12_with_many_occupancy_is_an_explicit_error`(関数)
  - `test_i_v13_accepts_two_or_more`(関数)
  - `test_i_v13_with_one_occupancy_is_an_explicit_error`(関数)
  - `test_interval_verdict_three_values`(関数)
  - `test_j_apply_ensemble_verdict_moves_ensemble_to_top_level_and_keeps_seed1`(関数): 第216(親): v1.3 ではトップレベル n_pass/n_measured/pass がアンサンブル判定。seed 1 の点判定は seed1_v12 に残る。入力は壊さない。
  - `test_seeds_needed_search_is_monotone_and_bounded`(関数)
  - `v13`(関数)
- import している内部モジュール: `tools/c7/prereg_v13.py`・`tools/c8/ensemble.py`
- CLI の引数
  - `--prereg-version`
- 決定の ID: 第 216・第 333

## [test_presence_yardstick.py](../../../../../../tests/c7/test_presence_yardstick.py)

``tools/c7/presence_yardstick.py`` の検査。

- 公開の関数とクラス
  - `amap`(関数)
  - `anchors`(関数): 〔2-4 V6・検収 H1〕較正側のファイル+検証側の作り物(:func:`synth_validation_anchors`)。
  - `hour_mult`(関数): 時別の倍率(既定 1・``peak`` で持ち上げる)。
  - `synth_journal`(関数): 合成 journal(``T=24``・``C=6``)。``counts[t,k,c] = hm[t]*KIND_W[k]*CELL_W[c]``。
  - `synth_validation_anchors`(関数): 検証側の錨の**作り物**(値は試験の中で作る=検証側のファイルの値ではない)。
  - `test_anchors_json_has_source_and_tag`(関数): 台帳の全項目に source / verified_by / tag があり、値を持つ。
  - `test_before_after_delta_and_closer`(関数): before/after の差の符号と「現実側へ近づいたか」の bool。
  - `test_check_anchors_rejects_missing_fields`(関数): source が無い/tag が不正/値が無い台帳は**落ちる**(推測で埋めない)。
  - `test_cli_writes_json_and_md`(関数): CLI が ``presence_yardstick.json`` と ``.md`` を書く(写像表は合成を注入)。
  - `test_compare_symmetry_when_moving_away`(関数): 逆向き(現実から離れる)なら closer は False になる。
  - `test_display_path_hides_the_personal_directory`(関数): 第176: 記録に書く anchors_path はリポ内なら <repo>/ 相対・外ならそのまま。
  - `test_in_area_wake_rate_line_wins_over_the_d62_line`(関数): **D-66**: ``起床率(在圏)/時`` があれば a(h) との比較にそちらを使う。
  - `test_journal_rows_and_ratios`(関数): 合成 journal(C=6・T=24)→ 在圏行・昼夜比が手計算と一致する。
  - `test_kind_at_03_breakdown`(関数): 03 時の種別内訳: D-66 の 5 種の合計と全体比。
  - `test_md_and_json_state_which_wake_rate_definition_was_used`(関数): §4 の md/json が**どちらの定義で測ったか**を明記する(前後で定義が違えばその旨も)。
  - `test_parse_summary_lines`(関数): ``起床率/時`` ``D-62 計画就寝`` ``呼/時`` ``[run] n=`` を実書式から読む。
  - `test_runs_without_summary`(関数): ``--summary`` が無くても表は出る(起床率・計画就寝は None のまま=推測しない)。
  - `test_scaled_column_is_linear`(関数): 縮尺列 = 生値 × (target / n_agents)・線形で expedient と明記される。
  - `test_series_json_route`(関数): 集計済み JSON(area_hour_counts)からも表が出る(bbox と種別は空欄)。
  - `test_series_rejects_wrong_shape`(関数): (24,5) でない ``area_hour_counts`` は落とす。
  - `test_summary_feeds_wake_and_sleep_rows`(関数): 要約を渡すと a(h) との差と D-62 計数が入り、個体数の出所が要約になる。
  - `yard`(関数)
- import している内部モジュール: `tools/c7/c7lib.py`・`tools/c7/occupancy_series.py`・`tools/c7/presence_yardstick.py`
- 決定の ID: D-62・D-66・第 173・第 176・第 204

## [test_salt_compare_10f.py](../../../../../../tests/c7/test_salt_compare_10f.py)

10f 第 2 段 T2: salt の道具の読む役(``tools/c7/salt_compare.py``)を既知の答えで確かめる(純関数・ランを回さない)。

- 公開の関数とクラス
  - `test_arm_keys_only_differing_values_and_trees_only_for_dicts`(関数): 検収 S3-4: 両方の腕で同じ値の引数は腕の欄にしない・下の木を許すのは値が辞書の引数だけ。
  - `test_crn_health_three_values`(関数): 検収 S2: A/A が無いと ok=None(未検査)・全部通れば True・落ちれば False(未検査より落ちたが先)。
  - `test_crn_ratio_warns_when_negatively_correlated`(関数)
  - `test_d46_two_formulas_match_r71`(関数): R-71 §5-1: CV 0.0325 で 2% は (CV/r)²→3 本・半幅なら 13 本、1% は 11 本・44 本。
  - `test_derived_keys_need_declared_values`(関数): 検収 S3-3: 導かれる欄は {base, arm, reason} で宣言し、実際の値と違えば落ちる。理由だけの古い形は止める。
  - `test_diff_over_width_is_labelled_as_descriptive`(関数): 検収 S3-2: 差 ÷ 幅の読み方の注記が全部の行に付き、記述のみの行の注記にも書かれる。
  - `test_environment_seed_modes`(関数): 10f 第 2 段の直し(S1): 対の間で環境の seed が違えば落ちる・fixed で salt ごとに違えば落ちる・salt なら許し、
  - `test_five_pairs_need_a_preregistered_direction_and_six_pairs_test_two_sided`(関数)
  - `test_holm_and_bh_known_example`(関数): 手計算: p = 0.01, 0.04, 0.03, 0.005(α=0.05)。
  - `test_holm_family_of_five_needs_eight_pairs`(関数): R-71 §2-3: Holm で 5 本なら最小の線は 0.01 → 両側 7 対(2/128=0.0156)では届かず 8 対(0.0078)で届く。
  - `test_input_match_synthetic`(関数)
  - `test_known_two_arms_three_pairs_hand_values`(関数): 既知の 2 腕(差が分かっている合成の例)。基準 10,12,14・腕 11,15,16 → 差 1,3,2。
  - `test_main_exit_codes`(関数): 再検収 T5: ``main`` の終了コードは CRN の健全性が ok なら 0・fail なら 1・未検査なら 3。
  - `test_p_floor_table`(関数): R-71 §2-3 の表: 片側 1/2^n・両側 2/2^n。全部同じ向きの差で下限に届く。
  - `test_perm_ci_six_pairs_is_min_max_at_96_9_percent`(関数)
  - `test_pre_t0_first_divergence_and_aa_synthetic`(関数)
  - `test_pre_t0_without_checkpoints_is_unchecked`(関数): 検収 S2: T0 > 0 で T0 より前の checkpoint が 0 本なら「未検査」(ok は None)。T0 = 0 は対象外で True。
  - `test_primary_must_be_one`(関数)
  - `test_seed_type_matters`(関数): 検収 S3-8: 1 と "1" は core.rng で別の鍵=同じ母集団の seed とみなさない。
  - `test_sign_flip_matches_brute_force`(関数): 全部の符号の組を itertools で数えた p と一致(0 と同点を含む)。
  - `test_six_pairs_reach_2_over_64`(関数)
  - `test_t_quantile_matches_the_table`(関数)
  - `test_three_pairs_say_descriptive_only`(関数)
- import している内部モジュール: `tools/c7/salt_compare.py`
- 決定の ID: R-71

## [test_seal_guard_337.py](../../../../../../tests/c7/test_seal_guard_337.py)

〔第337 検収 L1〕tests/c7 の番人(``conftest._seal_hook``)の試験。

- 公開の関数とクラス
  - `test_guard_lets_calibration_side_and_tmp_through`(関数)
  - `test_guard_refuses_before_opening`(関数)
- import している内部モジュール: `tests/c7/conftest.py`
- 決定の ID: 第 337

## [test_seed_ensemble.py](../../../../../../tests/c7/test_seed_ensemble.py)

``tools/c7/seed_ensemble.py``(N seed の帰無参照・prereg v1.3 §7)の検収。実データは読まない。

- 公開の関数とクラス
  - `test_cli_refuses_to_overwrite_existing_output`(関数)
  - `test_cli_run_argument_needs_label_equals_path`(関数)
  - `test_identical_seeds_give_zero_spread`(関数)
  - `test_jsd_is_symmetric_bounded_and_zero_on_equal`(関数)
  - `test_r25_parent_recomputation_reproduces`(関数): 第209 の親再計算: 3 seed・CV 0.0038(昼中央値)→ ±2.2% / 0.0325(深夜最大)→ ±18.6%。
  - `test_three_seeds_cv_and_pairwise_null_reference`(関数)
  - `test_two_seeds_reproduce_fig_seed_pair_cv`(関数): n=2 の ddof=1 標本 SD は |a−b|/√2=fig_seed_pair.summarize と同じ CV。
- import している内部モジュール: `tools/c7/seed_ensemble.py`
- 決定の ID: 第 209

## [test_seed_exchangeability.py](../../../../../../tests/c7/test_seed_exchangeability.py)

``tools/c7/seed_exchangeability.py``(D-83 ⑦)の検収。合成 checkpoints.json のみ。

- 公開の関数とクラス
  - `test_cli_writes_json_and_refuses_overwrite`(関数)
  - `test_declared_equivalent_passes_with_reason_and_only_for_listed_values`(関数)
  - `test_flatten_and_equivalent_parsing`(関数)
  - `test_identical_config_is_exchangeable_with_only_allowed_diffs`(関数)
  - `test_must_match_and_tick_list_mismatch_fail`(関数)
  - `test_population_hash_dependence_is_reported_not_failed`(関数)
  - `test_unexplained_manifest_diff_fails`(関数)
- import している内部モジュール: `tools/c7/seed_exchangeability.py`
- 決定の ID: D-83
