# tests/c6

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 10 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../tests/c6/__init__.py)

tests.c6 — C6-b 検証テスト(T3/T5/T9・L4/L6)と ``tools/c6`` 純関数の検査。

## [_fake_vllm.py](../../../../../../tests/c6/_fake_vllm.py)

プロセス内の偽 vLLM(OpenAI 互換の最小面・**非ストリーミングのみ**)。

- 公開の関数とクラス
  - `FakeVLLM`(クラス): ``/v1/models`` と ``/v1/chat/completions``(JSON)だけを返す偽サーバー。
- 読む試験: `tests/c6/test_l4_l6_budget.py`
- 読む試験(道筋で): `tests/perception/test_ablation1.py`

## [conftest.py](../../../../../../tests/c6/conftest.py)

tests.c6 の共通フィクスチャ。

- 公開の関数とクラス
  - `c6lib`(関数)
  - `tools_dir`(関数)
  - `world_dir`(関数)
- import している内部モジュール: `tools/c6/c6lib.py`
- 読む試験: `tests/c6/test_l4_l6_budget.py`・`tests/c6/test_t3_parallel_invariance.py`・`tests/c6/test_t5_order_bias.py`・`tests/c6/test_t9_diagnostics.py`

## [test_c6lib_aggregate.py](../../../../../../tests/c6/test_c6lib_aggregate.py)

応答の採点・違反判定・出力(Markdown/JSON)と、各ツールの純関数部分。

- 公開の関数とクラス
  - `test_ablation1_probe_detects_that_the_switch_is_effective`(関数): §3.2 の義務 ablation の切替口が**効いている**ことを固定する(C6 で実装)。
  - `test_alias_usage_is_counted_and_broken_down`(関数): 英語ラベル(C6 以前からある別名)でも ``alias_used`` は立つ=内訳が出る。
  - `test_common_parser_has_the_five_required_flags`(関数)
  - `test_format_error_gate_needs_both_the_rate_and_the_sample_size`(関数)
  - `test_format_error_rate_is_reported_both_effective_and_strict`(関数): C6 のラベル別名を許した実効と、許さない厳密の二重(親判断 D-28)。
  - `test_format_role_acceptance_rows_render_the_c6_table`(関数)
  - `test_format_role_marks_a_small_sample_as_insufficient`(関数)
  - `test_format_role_table_separates_effective_and_strict_verdicts`(関数): 実効は合格・厳密は不合格、という組み合わせが表に出る(D-28 の読み分け)。
  - `test_kinds_outside_the_table_are_never_flagged`(関数)
  - `test_markdown_table_shape`(関数)
  - `test_metric_b_compare_passes_reports_both_halves`(関数)
  - `test_metric_b_null_pass_is_reported_when_given`(関数)
  - `test_score_texts_counts_format_errors_and_actions`(関数)
  - `test_score_texts_uses_the_canonical_two_line_writer`(関数)
  - `test_split_prompt_cuts_at_the_first_individual_block`(関数)
  - `test_t6_compare_tapes_detects_a_single_mismatch`(関数)
  - `test_t6_flags_calls_present_in_only_one_tape`(関数)
  - `test_t6_manifest_note_says_it_does_not_claim_bit_reproduction`(関数)
  - `test_t7_distribution_report_carries_jsd_null_and_chi2`(関数)
  - `test_t7_gate_is_declared_undecided`(関数)
  - `test_undefined_rate_excludes_words_the_stage0_dictionary_rescues`(関数): 段0 辞書(``map_synonym``)で救えた語は未定義に数えず、写像先の契約語として数える。
  - `test_violation_flags_use_the_banned_action_table`(関数)
  - `test_world_dir_of_returns_none_for_a_missing_path`(関数)
  - `test_write_outputs_writes_both_files`(関数)
- import している内部モジュール: `shibuya.llm.contract`・`shibuya.llm.parser`・`shibuya.llm.undefined`・`tools/c6/ablation1_fixed_vs_ranking.py`・`tools/c6/format_role_rates.py`・`tools/c6/metric_b_rerun.py`・`tools/c6/t6_bit_reproduce.py`・`tools/c6/t7_distribution.py`
- 決定の ID: D-25・D-28

## [test_c6lib_scenes.py](../../../../../../tests/c6/test_c6lib_scenes.py)

場面抽出(指標B の事前登録)の純関数 — **モックテープ / モック記録**で検査。

- 公開の関数とクラス
  - `test_classify_scene_finds_the_interoception_driver`(関数)
  - `test_classify_scene_finds_the_plan_boundary_driver`(関数)
  - `test_classify_scene_reads_the_failure_reason`(関数)
  - `test_classify_scene_returns_plain_for_a_scene_without_drivers`(関数)
  - `test_failure_word_table_is_one_to_one_with_result_text`(関数)
  - `test_inventory_is_ok_when_all_five_kinds_are_stocked`(関数)
  - `test_inventory_reports_shortfall_against_the_preregistration`(関数)
  - `test_plan_boundary_reason_snippets_come_from_the_template`(関数)
  - `test_preregistered_kinds_are_the_declared_five`(関数)
  - `test_real_tape_blocks_lack_the_individual_sections`(関数): 実ランのテープは共有ブロックだけ = ``partial=True``(再呼に使えない印)。
  - `test_recording_llm_captures_full_prompts`(関数)
  - `test_scenes_from_a_mock_tape`(関数)
  - `test_selection_can_be_restricted_to_other_kinds`(関数)
  - `test_selection_is_deterministic_and_disjoint`(関数)
  - `test_unknown_failure_word_is_not_forced_into_a_kind`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.tape`・`shibuya.llm`・`shibuya.perception.templates`

## [test_c6lib_stats.py](../../../../../../tests/c6/test_c6lib_stats.py)

``tools/c6/c6lib`` の統計(相関・KS・JSD・帰無参照・ブートストラップ・χ²)。

- 公開の関数とクラス
  - `test_average_stratified_reports_keeps_a_real_bias`(関数): 本物のバイアスは平均しても残る(平均が甘くならない)。
  - `test_average_stratified_reports_refuses_mismatched_strata`(関数)
  - `test_average_stratified_reports_shrinks_the_sampling_noise`(関数): seed ごとに符号が飛ぶ ρ は平均するとゼロへ寄る(閾値を当てるのは平均側)。
  - `test_bootstrap_is_deterministic_for_a_fixed_seed`(関数)
  - `test_bootstrap_mean_ci_contains_the_point_estimate`(関数)
  - `test_chi2_2sample_detects_a_shifted_categorical`(関数)
  - `test_chi2_2sample_drops_all_zero_columns`(関数)
  - `test_chi2_sf_matches_textbook_critical_values`(関数)
  - `test_gate_fails_on_the_partial_correlation_alone`(関数): 層ごとの ρ が小さくても、**全層に同じ向き**で乗るバイアスは部分相関が捕まえる。
  - `test_jsd_counts_aligns_missing_keys`(関数)
  - `test_jsd_is_zero_for_equal_and_one_bit_for_disjoint`(関数)
  - `test_ks_2samp_is_zero_for_identical_samples`(関数)
  - `test_ks_2samp_separates_shifted_distributions`(関数)
  - `test_nan_rows_are_dropped_before_correlating`(関数)
  - `test_null_jsd_reference_brackets_the_observed_value_for_same_distribution`(関数)
  - `test_order_bias_report_flags_a_planted_id_bias`(関数)
  - `test_pearson_matches_numpy_and_guards_degenerate_input`(関数)
  - `test_per_agent_call_stats_counts_and_means`(関数)
  - `test_rankdata_averages_ties`(関数)
  - `test_reversal_symmetry_accepts_a_sign_flip_and_rejects_a_persistent_bias`(関数): 副判定 ``|ρ_順 + ρ_逆| ≤ 0.05``。
  - `test_spearman_is_one_for_a_monotone_nonlinear_map`(関数)
  - `test_stratified_report_rejects_a_mismatched_strata_length`(関数)
  - `test_stratified_report_reports_per_stratum_size_and_calls`(関数)
  - `test_stratified_report_separates_composition_from_processing_order`(関数): **種別構成の差**は層内では消える(W16 の ID が塊で並ぶことへの対処)。
  - `test_stratified_report_still_catches_a_within_stratum_bias`(関数): 層の中に処理順バイアスを植えたら検出する(層化しても盲目にならない)。
  - `test_weights_are_call_counts_not_head_counts`(関数): 加重平均の重みは**呼数**(呼がほぼ 0 の層に平均を薄めさせない・親指示 09-09)。
  - `test_wilson_ci_known_values`(関数)

## [test_l4_l6_budget.py](../../../../../../tests/c6/test_l4_l6_budget.py)

**L4 / L6 予算の読み取り**(C6 受入「L4/L6予算」)。

- 公開の関数とクラス
  - `test_a_recorded_fleet_run_can_be_checked_offline`(関数): 親がサーバーで回した診断行を ``SHIBUYA_C6_FLEET_COUNTERS``(JSON)で渡して検査する。
  - `test_a_run_without_a_fleet_reports_no_in_flight_counters`(関数): mock ランに ``fleet_*`` は立たない(=艦隊ランでだけ検査が効く)。
  - `test_fleet_smoke_keeps_in_flight_within_l6`(関数): **偽 vLLM 2 本**に対する 24step スモークで in-flight が L6 を破らない。
  - `test_fleet_smoke_unlimited_defaults_the_queue_to_the_agent_count`(関数): 第289 Q28(D-55): 枠が体数より狭い艦隊(``max_in_flight`` 8 → 既定の枠 32)× 無制限 × 枠 未指定。
  - `test_fleet_smoke_unlimited_keeps_real_concurrency_within_l6_and_notes_the_queue`(関数): 3 段目(D-99 (a′)・D-110): 既定=呼数無制限の艦隊スモーク。
  - `test_in_flight_report_flags_a_breach`(関数)
  - `test_l4_and_l6_are_read_from_the_budget_table`(関数)
  - `test_l4_cap_holds_for_a_5000_agent_day_on_the_synthetic_world`(関数)
  - `test_l4_cap_holds_on_the_real_world`(関数): 上限スイッチ ``l4_scale=1.0``(旧挙動)で按分上限と制御目標が守られる。
  - `test_l6_caps_are_derived_from_the_table_not_hard_coded`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.arbiter`・`shibuya.engine.run`・`shibuya.llm.fleet`・`shibuya.manifest.schema`・`tests/c6/_fake_vllm.py`・`tests/c6/conftest.py`
- 環境変数: `SHIBUYA_C6_FLEET_COUNTERS`
- 決定の ID: D-55・D-56・D-99・D-110・第 289・第 337

## [test_t3_parallel_invariance.py](../../../../../../tests/c6/test_t3_parallel_invariance.py)

**T3 並列不変性**(運用設計書 §1.4「スレッド 1/8/32 で同一結果」)。

- 公開の関数とクラス
  - `test_no_parallel_loop_exists_in_the_engine_at_run_time`(関数): 「並列度の口」の不在を機械で固定する(増えたら T3 の測り方を変える合図)。
  - `test_t3_final_hash_is_identical_across_thread_counts`(関数)
  - `test_t3_in_process_set_num_threads_does_not_change_the_result`(関数)
  - `test_t3_on_the_real_world_at_5000_agents`(関数): 実データ 5,000 体 × 24 tick(§9.1 C6 のスモーク規模)。
- import している内部モジュール: `shibuya.engine.resolve`・`tests/_places.py`・`tests/c6/conftest.py`
- 環境変数: `os.environ` をまるごと使う

## [test_t5_order_bias.py](../../../../../../tests/c6/test_t5_order_bias.py)

**T5 順序バイアス**(運用設計書 §1.4「24step スモークで個体 ID 順との相関 **|r| ≤ 0.05**」)。

- 公開の関数とクラス
  - `test_t5_conversation_partner_rule_is_stirred_not_id_ordered`(関数): ``pair_partners`` の並びを釘付ける(09-09 の是正後)。
  - `test_t5_long_horizon_diagnostic_reports_the_bias_per_wake_class`(関数): 240 tick・予算無制限の診断ラン。**起床クラス別**に ID 相関を出す(合否は付けない)。
  - `test_t5_order_bias_on_the_real_world`(関数): 実データは**種別層内**で判定する(生の相関は種別構成を拾うので報告値)。
  - `test_t5_order_bias_on_the_synthetic_world`(関数)
  - `test_t5_report_shape_is_the_three_declared_quantities`(関数)
  - `test_t5_reversed_population_shows_the_bias_is_composition_not_order`(関数): ``agent_id`` の写像を反転した対照。
- import している内部モジュール: `shibuya.agents.population`・`shibuya.agents.state`・`shibuya.engine.commit`・`shibuya.engine.run`・`shibuya.llm.mock`・`shibuya.world.state`・`tests/c6/conftest.py`・`tools/c6/c6lib.py`
- 決定の ID: D-56・D-62・D-64・D-66

## [test_t9_diagnostics.py](../../../../../../tests/c6/test_t9_diagnostics.py)

**T9 診断行**(運用設計書 §1.4「診断行 4 列(繰り延べ/昇格/縮退/抑止)+ **保存則 2 検算**の存在(全ラン)」・§1.2 出力節「診断行4列+保存則2検算がなければ較正・holdoutに使わない」)。

- 公開の関数とクラス
  - `test_t9_manifest_fields_survive_for_the_run_record`(関数): 診断行と一緒に manifest へ載る同定欄(§1.2 出力節)。
  - `test_t9_on_the_real_world_smoke`(関数)
  - `test_t9_the_four_columns_actually_carry_numbers`(関数): 「存在するが常にゼロ」を弾く: 需要 > 予算のランでは繰り延べ・縮退が立つ。
  - `test_t9_the_four_diagnostic_columns_exist_in_the_run_table`(関数)
  - `test_t9_two_conservation_checks_are_present_and_pass`(関数): 保存則 2 検算 = 取引残差(``residual``)と在庫残差(``goods_residual_units``)。
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.run`・`shibuya.manifest.schema`・`shibuya.world.state`・`tests/c6/conftest.py`
- 決定の ID: D-56
