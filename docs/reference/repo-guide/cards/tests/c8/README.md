# tests/c8

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 13 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../tests/c8/__init__.py)

(冒頭の説明なし)

## [conftest.py](../../../../../../tests/c8/conftest.py)

tests.c8 の共通フィクスチャ。

- 公開の関数とクラス
  - `ablation_runner`(関数)
  - `c8lib`(関数)
  - `dashboard`(関数)
  - `data_dir`(関数)
  - `ensemble`(関数)
  - `sensitivity`(関数)
  - `world_dir`(関数)
- import している内部モジュール: `tools/c8/ablation_runner.py`・`tools/c8/c8lib.py`・`tools/c8/dashboard.py`・`tools/c8/ensemble.py`・`tools/c8/sensitivity.py`
- 読む試験: `tests/c8/test_dashboard.py`・`tests/c8/test_sensitivity_ledger.py`

## [test_ablations_ab6b.py](../../../../../../tests/c8/test_ablations_ab6b.py)

腕 ``AB6b-AD-NOTICE``(看板の注視ゲート較正)の腕定義行 — D-59 (b)(ユーザー決定 2026-09-17)。

- 公開の関数とクラス
  - `table`(関数)
  - `test_ab6_still_resolves_by_exact_match`(関数): ``AB6`` の前方一致が 2 本に当たるようになったが、**完全一致が優先**される。
  - `test_ab6b_declares_the_ad_zero_arm_inside_itself`(関数): ``ad_zero`` ランは ⑥ の ``signage_off`` と**同一構成**(共有できる=note に宣言)。
  - `test_ab6b_is_the_last_arm_with_rank_10`(関数): 2026-09-19: AB6b の**後ろに** AB8(L4 の感度)と AB6c(⑥b の無制限版)を足した。
  - `test_ab6b_kwargs_reach_run_day`(関数): 腕定義の ``kwargs`` が ``cli.run`` → ``run_day`` → manifest まで通る(mock・極小)。
  - `test_ab6b_runs_are_the_four_arms`(関数)
  - `test_ab6b_switch`(関数)
  - `test_ab6b_uses_the_same_metrics_as_ad_zero`(関数): 比較指標は ⑥ と**同じ**(腕をまたいで同じ物差しで読むため)。
  - `test_other_arms_keep_their_markdown`(関数): **看板を触らない腕の Markdown には節が出ない**(列追加のみの規律)。
  - `test_signage_p_see_is_on_the_allow_list`(関数)
  - `test_the_ad_zero_arm_is_untouched`(関数): ⑥ の腕定義は 1 バイトも動かない(golden は AB7 のテストが持つ値)。
  - `test_the_cost_and_totals_are_arithmetic`(関数)
  - `test_the_markdown_carries_the_gate_section`(関数): ``arm_markdown`` に ``signage_p_see`` の節が出る(看板の腕だけ)。
  - `test_the_open_question_declares_the_expedients`(関数): 0.30/0.14 の選び方と規約⑧ の但し書きを**親判断待ちとして残す**(黙って決めない)。
- import している内部モジュール: `tests/c8/test_ablations_ab7.py`
- 決定の ID: D-59・第 290

## [test_ablations_ab7.py](../../../../../../tests/c8/test_ablations_ab7.py)

腕 ``AB7-OPEN-INTENT`` / ``AB7b-HINT-INTENT`` の腕定義行と、M1〜M3 の集計(open-intent 仕様書 §1・§4 (d))。

- 公開の関数とクラス
  - `table`(関数)
  - `test_ab7_is_appended_to_the_table`(関数)
  - `test_ab7_kwargs_reach_run_day`(関数): 腕定義の ``kwargs`` が ``cli.run`` → ``run_day`` までそのまま通る(mock・極小)。
  - `test_ab7_switch_and_runs`(関数)
  - `test_ab7b_freezes_the_hint_b0_sha256`(関数): 腕定義に書いた B0 の指紋が**実装の値と一致する**(文面を変えたら両方が動く)。
  - `test_ab7b_keeps_rank_8`(関数)
  - `test_ab7b_kwargs_reach_run_day`(関数): 腕定義の ``kwargs`` が ``cli.run`` → ``run_day`` までそのまま通る(mock・極小)。
  - `test_ab7b_switch_and_runs`(関数)
  - `test_arm_markdown_renders_m1_and_m3`(関数): M1/M3 の節が**列数の揃った** Markdown 表になる(閾値到達語に ★)。
  - `test_existing_arm_output_only_gains_columns`(関数): 既存腕(AB6)の出力 JSON は**列が増えるだけ**で、既存の列の値は動かない。
  - `test_grounding_matches_score_texts_on_real_texts`(関数): テープの本文から出す道筋が ``c6lib.score_texts`` と同じ分母・分子であること。
  - `test_m1_two_stage_grounding_is_recomputable`(関数): M1 は 3 つの排他な件数 ÷ 非繰り延べ行数。3 つの和は厳密に n。
  - `test_m2_m3_from_the_registry`(関数): M2 未定義率=undefined_records ÷ 解釈まで進んだ呼・M3=top_words+distinct agents。
  - `test_registry_absent_leaves_the_column_empty`(関数): 台帳が無い結果では**空辞書**(推測で埋めない)。
  - `test_the_existing_arms_are_byte_identical`(関数): **後から腕を足しても既存の腕の定義は 1 バイトも動かない**(golden は追加前の値)。
- import している内部モジュール: `shibuya.foundation.text.templates`・`shibuya.foundation.vocab.actions`・`tools/c8/c8lib.py`
- 読む試験: `tests/c8/test_ablations_ab6b.py`・`tests/c8/test_ablations_ab8.py`
- 決定の ID: D-59・第 290

## [test_ablations_ab7c.py](../../../../../../tests/c8/test_ablations_ab7c.py)

腕 ``AB7c-VOCAB-V2``(語彙 v1 vs 語彙 v2)の腕定義行 — D-71 §3(2026-09-17 ユーザー決定)。

- 公開の関数とクラス
  - `table`(関数)
  - `test_ab7c_keeps_rank_9`(関数)
  - `test_ab7c_kwargs_reach_run_day`(関数): 腕定義の ``kwargs`` が ``cli.run`` → ``run_day`` までそのまま通る(mock・極小)。
  - `test_ab7c_switch_and_runs`(関数)
  - `test_the_arm_definition_is_frozen`(関数)
  - `test_the_totals_declare_the_l2_overrun`(関数)
  - `test_vocab_version_is_on_the_allow_list`(関数)
- 決定の ID: D-59・D-71・第 290

## [test_ablations_ab8.py](../../../../../../tests/c8/test_ablations_ab8.py)

腕 ``AB8-L4-SCALE`` / ``AB6c-AD-NOTICE-UNCAPPED`` と**実現量**の欄 — 2026-09-19。

- 公開の関数とクラス
  - `mutation_runs`(関数): 既定 / 1.0 / 0.5 / 0 の 4 ラン(mock・極小)を 1 回だけ回して使い回す。
  - `table`(関数)
  - `test_compare_runs_reports_the_realized_delta`(関数)
  - `test_compare_runs_without_realized_makes_no_column`(関数): **推測で埋めない**: 片方に欄が無ければ差の欄も作らない。
  - `test_halving_the_budget_moves_the_diagnostics`(関数): 0.5 で**呼数が減り final_hash が動く**(mock でも腕が効く=予算はエンジン側の量)。
  - `test_run_metrics_carries_the_realized_block`(関数)
  - `test_the_cost_and_totals_are_arithmetic`(関数)
  - `test_the_default_and_the_explicit_0_are_byte_identical`(関数): 3 段目(D-99 (a′)・D-110): 既定は **0=無制限**=``l4_scale=0`` と同じ経路・同じバイト。
  - `test_the_existing_arms_are_byte_identical`(関数): **後ろに 2 本足しても既存 10 腕の定義は 1 バイトも動かない**。
  - `test_the_existing_metric_keys_keep_their_values`(関数): **列追加のみ**: 既存の欄は 1 つも動かない(値を別経路で作り直さない)。
  - `test_the_factor_multiplies_the_l4_share`(関数)
  - `test_the_kwargs_reach_run_day`(関数): 腕定義の ``kwargs`` が ``cli.run`` → ``run_day`` → manifest まで通る(mock・極小)。
  - `test_the_manifest_whitelist_carries_the_budget_fields`(関数)
  - `test_the_markdown_carries_the_realized_table`(関数)
  - `test_the_metrics_are_the_ad_zero_five_plus_realized`(関数)
  - `test_the_open_questions_declare_the_expedients`(関数): 『無制限=体数』の置き方と合格線の不在を**親判断待ちとして残す**(黙って決めない)。
  - `test_the_runs_and_their_kwargs`(関数)
  - `test_the_two_arms_are_appended`(関数)
  - `test_the_uncapped_arm_reaches_run_day_too`(関数): ⑥c は ⑥b の 4 構成に ``l4_scale=0`` を重ねただけ(新しい口は作っていない)。
  - `test_zero_defers_nothing`(関数): **無制限**=繰り延べが 0 件になり、呼数は上限つきのランを上回る。
  - `test_zero_means_the_agent_count`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.arbiter`・`tests/c8/test_ablations_ab7.py`
- 決定の ID: D-56・D-59・D-99・D-110・第 245・第 289・第 290

## [test_ablations_l4_pin.py](../../../../../../tests/c8/test_ablations_l4_pin.py)

第290(3 段目の問い Q29): 上限ありで回した凍結腕は ``l4_scale: 1.0`` を明示して旧構成で回る。

- 公開の関数とクラス
  - `table`(関数)
  - `test_a_pinned_arm_reruns_with_the_old_capped_budget`(関数): 回し直しても旧構成(上限あり=L4 按分)で回る=``budget_per_tick`` が按分値・倍率 1.0。
  - `test_every_run_states_its_l4_scale`(関数): ランの無い腕(AB4・AB5=未実装)を除き、全ランが ``l4_scale`` を明示している。
  - `test_the_capped_arms_are_pinned_to_the_old_budget`(関数)
- import している内部モジュール: `shibuya.engine.arbiter`
- 決定の ID: D-99・D-110・第 289・第 290

## [test_ablations_table.py](../../../../../../tests/c8/test_ablations_table.py)

ablation 第1陣 6 本の**腕定義表**のスキーマと、設計書(知覚契約書 §8)との突合。

- 公開の関数とクラス
  - `table`(関数)
  - `test_arm_by_id_forms`(関数)
  - `test_arm_markdown_renders_without_runs`(関数)
  - `test_arms_match_design_text`(関数): 設計書 §8 の逐語と腕定義表の対応(**設計書が変わったら落ちる**)。
  - `test_budget_within_l2`(関数): 共有ベースラインの見積りと ``within_l2`` フラグの**整合**を機械で守る。
  - `test_compare_runs`(関数)
  - `test_compare_runs_without_tape`(関数): テープが無い(行動分布が取れない)ときは JSD 欄を作らない=**推測で埋めない**。
  - `test_every_arm_declares_switch_state`(関数): 切替口が無い腕は**差分案**を必ず持つ(自前で src/ を触らないための規律)。
  - `test_execute_arm_notes_real_llm_required`(関数): mock で差が出ない腕は「実 LLM 必須」を印字する。
  - `test_execute_arm_refuses_unimplemented_switch`(関数): 切替口が無い腕は**回さず**差分案を印字して返る(src/ を触らないため)。
  - `test_execute_arm_rejects_unknown_kwargs`(関数)
  - `test_gpu_hours_match_the_conversion`(関数): 表の GPU 時間は ``c8lib.gpu_hours_for_calls``(C6 実測の外挿)と一致すること。
  - `test_kwargs_are_allowlisted`(関数): 腕定義表(データ)から任意のキーワード引数を通さない。
  - `test_manifest_whitelist_carries_the_arms`(関数): 腕の同定欄が ``run_metrics`` の白リストを通る(D-66 の 3 欄を含む・2026-09-11)。
  - `test_mock_ineffective_arms_are_prompt_only`(関数): mock で差が出ない腕=**プロンプト本文しか変えない**腕(①⑥⑥b⑥cと AB7・AB7b)。
  - `test_only_the_second_wave_arms_are_still_blocked`(関数): 切替口の実装状況(C6 で ①・**C8 で ②③⑥**=2026-09-09)。
  - `test_pending_kwargs_are_marked`(関数): 未実装の口を使う ``runs`` は ``pending`` 印が要る(実行器が飛ばす目印)。
  - `test_run_metrics_from_stub`(関数)
  - `test_run_metrics_handles_zero_salient`(関数)
  - `test_six_arms_in_priority_order`(関数): §8「第1陣=6 本」・rank は優先順位規則(expedient の量 × 駆動可能性 ÷ コスト)の順。
  - `test_table_markdown_is_a_valid_table`(関数)
  - `test_table_validates`(関数)
  - `test_the_added_arms_are_implemented`(関数): 第1陣より後に足した腕は**切替口つきで足す**(未実装の腕を後ろに積まない)。
  - `test_totals_match_the_arms`(関数): 合計欄は腕の積み上げと一致すること(手書きの合計がずれない)。
  - `test_validate_table_detects_breakage`(関数)
- 決定の ID: D-60・D-66・D-91・D-99・第 245・第 249

## [test_c8lib.py](../../../../../../tests/c8/test_c8lib.py)

c8lib の純関数と**設計書の走査**(漏れ検出の分母)。

- 公開の関数とクラス
  - `test_budget_row_reads_markdown`(関数): 予算宣言表は **Markdown が正典**(数値をツールに複製しない)。
  - `test_compare_counts_identical`(関数): 同じ分布どうしは JSD 0・TVD 0・帰無参照を超えない。
  - `test_compare_counts_length_mismatch`(関数)
  - `test_compare_counts_shifted`(関数)
  - `test_fmt`(関数)
  - `test_gpu_hours_for_calls`(関数): 受入報告 C6 の実測(呼 50,000=約 29 分)を再現する換算であること。
  - `test_ledger_gaps`(関数)
  - `test_markdown_table_escapes_pipes`(関数): セルの ``|`` を逃がさないと表が崩れる(T5 の「|r| ≤ 0.05」で実際に崩れた)。
  - `test_md_cell_none_and_newline`(関数)
  - `test_null_jsd_p95_degenerate`(関数)
  - `test_null_jsd_p95_is_deterministic`(関数)
  - `test_null_jsd_p95_is_small_for_large_samples`(関数): 同じ分布から 2 回引いた JSD は N が大きいほど小さい(帰無参照の性質)。
  - `test_scan_build_spec_finds_inline_sensitivities`(関数): ``- expedient: …。感度: …`` の**行の途中**の宣言も拾えること。
  - `test_scan_build_spec_ignores_outside_headings`(関数)
  - `test_scan_build_spec_marks_required`(関数): 『感度(必須)』は D-W8(既定営業時間±2h)だけ。
  - `test_scan_engine_ablation_ids`(関数): 世界過程は 1 行 1 感度試験 id(AB-*)を持つ。
  - `test_scan_first_wave_arms_is_six`(関数): 知覚契約書 §8 の第1陣は **6 本**(数が変わったら設計が動いた合図)。
  - `test_scan_plan_sensitivities_is_report_only`(関数): 実装計画書 §8 の走査は**報告用**(網羅は保証しない)。落ちずに何か返ること。
  - `test_verdict_is_one_sided`(関数)
- 決定の ID: D-66

## [test_dashboard.py](../../../../../../tests/c8/test_dashboard.py)

忠実度計器盤の**純関数**(モック入力)。R14 G-1 の3面の分け方を検査する。

- 公開の関数とクラス
  - `test_build_on_real_repo`(関数): 実リポの入力で組み立てて落ちないこと(親が叩く経路)。
  - `test_collect_ablations`(関数)
  - `test_collect_build_gates`(関数)
  - `test_collect_build_gates_missing`(関数): 入力が無ければ「未測定」。**推測で埋めない**。
  - `test_collect_calibration_empty`(関数)
  - `test_collect_calibration_has_no_gate`(関数): 面1は報告のみ=行に judge/pass を作らない。
  - `test_collect_coverage_orphans_fail_gate`(関数)
  - `test_collect_coverage_vector_not_summed`(関数): 5 値ベクトルは**加重和にしない**(方法論)=各値が別の欄で出ること。
  - `test_collect_distortions`(関数)
  - `test_collect_distortions_falls_back_to_the_frozen_archive`(関数): PENDING.md から 1 件も拾えなければ凍結した旧 PENDING を読む(出所も返す)。
  - `test_collect_distortions_reads_the_bold_rows_of_the_new_pending`(関数): 第279 以後の PENDING は ``| **D-118** K1〜K9 | …`` の形(太字+接尾辞)。id は D-NN だけ。
  - `test_collect_holdout_is_the_only_gate`(関数)
  - `test_collect_holdout_unopened`(関数)
  - `test_collect_ops_flags_only_symptoms`(関数): 面3は症状だけ。**holdout(ゲート)の行は面2の受け持ちなので出さない**(R14 G-1)。
  - `test_collect_ops_without_accept_shows_declarations`(関数)
  - `test_collect_quality`(関数)
  - `test_collect_quality_empty`(関数)
  - `test_collect_sensitivity`(関数)
  - `test_collect_verification_covers_t1_t9`(関数)
  - `test_collect_verification_leaves_unknown_empty`(関数): 根拠が無い行は空欄のまま(**推測で埋めない**)。
  - `test_collect_verification_prefers_measured_lines`(関数)
  - `test_render_marks_gate_only_on_face2`(関数)
  - `test_render_tables_are_well_formed`(関数)
  - `test_render_without_inputs`(関数)
- import している内部モジュール: `tests/c8/conftest.py`
- 決定の ID: D-1・D-2・D-33・D-38・D-59・D-99・D-102・D-118・第 245・第 279

## [test_ensemble.py](../../../../../../tests/c8/test_ensemble.py)

アンサンブル運用(R14 G-4/G-5/G-8)の設計器と面2の計器(純関数)。

- 公開の関数とクラス
  - `test_crps_empty`(関数)
  - `test_crps_of_deterministic_forecast_is_absolute_error`(関数)
  - `test_crps_rewards_a_well_placed_spread`(関数): 観測を含む幅の方が、外した決定論予測より CRPS が小さい。
  - `test_implausibility`(関数)
  - `test_run_seed_differs_by_index_and_manifest`(関数): 『異なる run_index で RNG 状態が衝突しない』(R14 G-5)。
  - `test_run_seed_feeds_core_rng`(関数): 出た seed が実際に ``core.rng`` の鍵導出に通ること(型の相性)。
  - `test_run_seed_is_a_positive_63bit_int`(関数)
  - `test_run_seed_is_deterministic`(関数)
  - `test_run_seed_rejects_negative_index`(関数)
  - `test_spec_budget_scales_with_runs`(関数)
  - `test_spec_default_is_eight_runs`(関数): R14 G-8「初回=seed 群 8 本」(expedient)。
  - `test_spec_face2_gate_is_implausibility`(関数)
  - `test_spec_flags_w1_overrun`(関数): 1 ラン単体で W1(24 h)を超える規模は open_questions に出る。
  - `test_spec_markdown_tables_well_formed`(関数)
  - `test_spec_reporters_are_face_scoped`(関数): reporters は面1/面2 の指標だけ(R14 G-4)。
  - `test_spec_run_table_has_resume_key`(関数): G-6「``(manifest_sha256, run_index)`` を主キーとする完了済みラン表」。
  - `test_spec_varies_only_master_seed`(関数): 決定台帳「アンサンブル=**master_seed のみ変更**」。
  - `test_spread_skill_ratio_about_one_when_calibrated`(関数): **観測もメンバーの 1 本**であるとき(完全に信頼できるアンサンブル)比は 1 の近く。
  - `test_spread_skill_ratio_detects_underdispersion`(関数): 幅が狭すぎる(自信過剰)アンサンブルは比が 1 を大きく下回る。
  - `test_spread_skill_ratio_shape_checks`(関数)
- import している内部モジュール: `shibuya.foundation.rng`

## [test_places_rule_copies.py](../../../../../../tests/c8/test_places_rule_copies.py)

元の置き場の規則の写し 2 か所が同じ答えを返すこと(再検収 第 3 回 5 の (2))。

- 公開の関数とクラス
  - `test_both_copies_give_the_same_answer_on_a_made_tree`(関数)
  - `test_both_copies_give_the_same_answer_on_the_current_tree`(関数)
  - `test_both_copies_share_the_schema_and_the_help`(関数)
  - `test_both_copies_stop_on_a_file_without_a_row`(関数): 表に無いファイル(中身のある新しい頭・新しいファイル)はどちらも止まり、0 バイトの新しい頭はどちらも受ける。
  - `test_both_copies_stop_on_the_same_bad_maps`(関数)
  - `tree`(関数)
- import している内部モジュール: `tests/_places.py`

## [test_sensitivity_ledger.py](../../../../../../tests/c8/test_sensitivity_ledger.py)

expedient 感度試験の**台帳**(漏れ検出つき)と、構築段階の対照(小データ)。

- 公開の関数とクラス
  - `ledger`(関数)
  - `strip_site_lines`(関数): 読み口の「:行番号」を落とす(意味のある内容=「資産の出力名 ← ファイル」まで)。台帳には行番号を残し、
  - `test_act_d44_key_remap_and_pending_rows`(関数): 〔第330・ACT〕番号のずれた行(W13#5=前の W13#6)は D-44 の結果を前の鍵から引き、増えた・文言の変わった行は
  - `test_code_strings_skip_docstrings`(関数): 読み口は**コードの**文字列だけ(docstring・式文の文字列は数えない)。
  - `test_criterion_is_one_sided`(関数)
  - `test_d44_column_is_consistent`(関数): 判定不能 111 行(〔2-4〕前 107)すべてに 6 値の状態。集計・分類ごとの規則(iii=対照を定義できない・読まない=対象外)・判定と JSD が合う。
  - `test_d44_leaves_existing_ledger_parts_unchanged`(関数): 既存の 19 行・過程 22 本・旧注記・判定列(a)(c)・3 分類は不変(D-44 は ``d44`` と ``d44_summary`` にだけ足す)。
  - `test_d44_markdown_has_the_section`(関数)
  - `test_d44_open_hours_metric_matches_hand_count`(関数): 営業中 POI×時 の指標: 月曜 0-12 時の 1 POI は営業 12・休業 156(168 時)。日跨ぎは週で巻く。
  - `test_d44_read_only_controls_recompute_from_the_live_world`(関数): 読むだけの対照(W2#4・W5#2・W7#2)はいまの世界資産から計算し直しても記録と同じ JSD。
  - `test_d44_regenerates_from_the_result_files`(関数): 台帳の d44 列は結果の記録(d44_results.json・mock_controls.json)から作り直しても同じ。
  - `test_d44_results_follow_the_rule_and_hold_no_paths`(関数): 結果の記録: 各変種の検出=JSD>帰無・行の検出=主の変種のどれか・宣言側の再計算が資産と一致・基準の再構築が
  - `test_d44_validation_catches_bad_rows`(関数)
  - `test_done_rows_have_results`(関数)
  - `test_every_design_sensitivity_is_covered`(関数): 構築仕様書 §2 の『感度: …』14 行が**全部**台帳にあること(漏れ検出の本体)。
  - `test_ledger_markdown_is_a_valid_table`(関数)
  - `test_ledger_validates`(関数): 自己検査+**設計書との突合**(漏れがあればここで落ちる)。
  - `test_manifest_judgment_block_is_consistent`(関数): build_manifest の expedient 全行の判定列(3 値+既存の台帳行)が行・集計・規則の文言と合うこと。
  - `test_manifest_judgment_markdown_has_the_rule_and_the_table`(関数)
  - `test_manifest_judgment_matches_the_live_manifest`(関数): 台帳の判定列は data/world/v2/build_manifest.json から作り直しても同じ(既存の台帳行の書き出しは 1 行ずつに当たる)。
  - `test_manifest_judgment_validation_catches_bad_rows`(関数)
  - `test_missing_row_is_detected`(関数): 1 行落とすと『漏れ』として検出されること(検出器そのものの検査)。
  - `test_open_questions_flag_the_gap`(関数): 設計書が感度を宣言していない expedient が親判断待ちとして残っていること。
  - `test_process_ablation_caveat_is_recorded`(関数): ``--ablate AB-PNOTICE-A0`` が salient 過程ごと止める罠を台帳が持っていること。
  - `test_process_ablation_ids_match_source`(関数): 世界過程の AB-* id は**コードが正典**(台帳が古くなったら落ちる)。
  - `test_read_graph_column_is_consistent`(関数): 判定不能の行だけに 3 値(読む/読まない/不明)・集計・読まない行の一覧が合う。既存の判定列は変えない。
  - `test_read_graph_matches_the_source`(関数): 台帳の依存グラフはいまの src から作り直しても同じ(実データの manifest があるとき)。
  - `test_read_graph_validation_catches_bad_rows`(関数)
  - `test_required_row_is_marked`(関数): 『感度(必須)』は D-W8 だけ=台帳もそう持つこと。
  - `test_run_row_fills_verdict`(関数)
  - `test_runner_names_exist`(関数)
  - `test_site_line_normalization_keeps_the_file_but_drops_the_line`(関数): 行番号だけのずれは通り、読み口のファイルが変わる・増える・消えると落ちる(正規化で検出力を失わない)。
  - `test_triage_column_is_consistent`(関数): エンジンが読む行だけに 3 分類(i/ii/iii)・対照の候補・費用の見込み。集計と表(未リサーチの明記)が合う。
  - `test_triage_validation_catches_bad_rows`(関数)
  - `test_w12_hour_uniform_already_uniform`(関数): 既に一様なら対照と一致=**駆動しえない**側の答えが出せること。
  - `test_w12_hour_uniform_small`(関数): 全部 8 時に寄った重み vs 一様=最大級の差(JSD が帰無を大きく超える)。
  - `test_w12_jr_phase_hour_bins_can_be_blind`(関数): 10 分間隔を 5 分ずらすとどのビンでも数が変わらない=**測れない**ことの記録。
  - `test_w12_jr_phase_moves_10min_bins`(関数): 等間隔 15 分の便を半運転間隔(7.5 分)ずらすと 10 分ビンは動く/時別は動かない。
  - `test_w12_jr_phase_shifts_only_expedient_rows`(関数): 実ダイヤ(``source='real'``)は動かさない。
  - `test_w13_and_w12_real_assets`(関数)
  - `test_w13_temp_plus_skips_missing_rows`(関数)
  - `test_w13_temp_plus_small`(関数): 気温 +1.5 ℃ の対照: 段階が上がった行だけが数えられること。
  - `test_w13_temp_plus_zero_delta_is_no_op`(関数): Δ=0 なら分布は 1 バイトも動かない(対照の健全性)。
  - `test_w16_area_apportionment_real`(関数): 床面積按分 vs 面積按分: 人数は保存され、配置は入れ替わる。
- import している内部モジュール: `tests/c8/conftest.py`
- 決定の ID: D-44・第 200・第 306・第 307・第 308・第 310・第 311・第 313・第 330・第 336
