# tests/llm

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 9 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../tests/llm/__init__.py)

(冒頭の説明なし)

## [test_contract.py](../../../../../../tests/llm/test_contract.py)

llm.contract の**転記テスト**(行動契約書 §2.1/§2.2 の表が1行も欠けていないこと)。

- 公開の関数とクラス
  - `test_cell_prefix_is_stripped_only_when_the_rest_is_a_cell_id`(関数): 第271: 「セルg-1_0_GL」(B2「現在地はセルg-1_0_GL」の写し)をセルとして読む。
  - `test_codes_are_stable_and_disjoint`(関数)
  - `test_every_2_1_word_has_a_spec_with_target_kind_and_failures`(関数)
  - `test_every_role_word_carries_its_permission_holder`(関数)
  - `test_expedient_rows_are_tagged_as_in_the_contract`(関数): 契約書がタグ **expedient** と書いた行(通報・手伝い・並ぶ/撮影)。
  - `test_output_form_constants_match_section_1`(関数)
  - `test_parse_target_keeps_the_raw_string_and_extracts_ids`(関数)
  - `test_parse_target_never_raises_on_odd_input`(関数)
  - `test_parse_target_recognises_the_declared_surface_forms`(関数)
  - `test_parse_until_constants_and_none`(関数)
  - `test_parse_until_reads_the_six_forms_and_the_default`(関数)
  - `test_role_words_split_from_the_shared_table_rows`(関数): 「発車/停車」「並ぶ/撮影」は表では1行=2語に割った(元の行名を残す)。
  - `test_target_category_suffix_is_stripped_before_parsing`(関数): 「食品のカテゴリ」→ 物カテゴリ「食品」。実在名・セル・人 ID の読み方は不変。
  - `test_target_placeholder_words_are_read_as_no_target_but_keep_raw`(関数): 第223(D-89): 観測テンプレートの欄説明語を写した応答は対象なし(raw は診断用に残す)。
  - `test_the_twelve_words_are_the_contract_table_in_order`(関数)
  - `test_v3_codes_do_not_move_and_removed_words_are_vacant`(関数): 既存コードは 1 つも動かない・2/4/10 は欠番・なし は末尾の 25。
  - `test_v3_compat_reads_both_directions`(関数): VOCAB_COMPAT["v3"]: 待機/休憩 → なし(旧テープを v3 で読む)/ なし → 待機(v3 → 旧版)。
  - `test_v3_engine_codes_are_the_cross_cutting_words`(関数)
  - `test_v3_every_word_passes_the_gate_instead_of_a_count_limit`(関数): D-92 (a): v3 の門は「契約行+コード」。上限 24 の assert は v3 に掛けない(v1 は残す)。
  - `test_v3_none_is_the_never_failing_safety_valve`(関数)
  - `test_v3_placeholders_are_read_as_no_target_only_in_v3`(関数)
  - `test_v3_queue_is_cross_cutting_and_not_a_role_word`(関数)
  - `test_v3_target_wander_and_base_words`(関数)
  - `test_v3_two_line_form_round_trips`(関数)
  - `test_v3_word_sets_follow_the_agenda_table`(関数)
  - `test_vocabulary_limit_of_the_contract_is_respected`(関数): §2「種別あたりの語彙上限24語」。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.foundation.vocab.actions`
- 読む試験(道筋で): `tests/tools/test_repo_guide.py`
- 決定の ID: D-89・D-92・D-116・第 223・第 271・第 274・第 275・第 275 #6・第 275 #7

## [test_fleet.py](../../../../../../tests/llm/test_fleet.py)

C6-a 艦隊接続の検収テスト(**プロセス内の偽 vLLM**・実サーバーへは繋がない)。

- 公開の関数とクラス
  - `FakeVLLM`(クラス): プロセス内の偽 vLLM(OpenAI 互換の最小面)。注入つまみは属性で切り替える。
  - `fleet2`(関数): 2 レプリカの偽艦隊。
  - `fleet3`(関数)
  - `make_config`(関数)
  - `mkcall`(関数)
  - `test_all_replicas_down_defers_and_does_not_drop`(関数)
  - `test_bridge_parses_and_records_real_response_to_tape`(関数)
  - `test_bridge_passes_deferred_through_untouched`(関数)
  - `test_connection_error_retries_same_then_other`(関数): 接続エラー = 同一レプリカ 1 回 → 別レプリカ 1 回(§7)。
  - `test_counters_account_for_every_call`(関数): 任意の混合注入でも ok+deferred+undefined+error の合計 = 呼数(呼を捨てない)。
  - `test_dictionary_candidate_skips_the_temperature_zero_regeneration`(関数): 語彙外でも §7 段0 の辞書で救える語は**再生成しない**(無駄な 1 呼を出さない)。
  - `test_e2e_timeout_defers`(関数)
  - `test_fleet_client_is_drop_in_for_existing_llm_bridge`(関数): ``FleetClient`` は ``llm.LLMClient`` 契約を満たす=既存 bridge にそのまま挿さる。
  - `test_format_error_regenerates_at_temperature_zero`(関数): 書式エラー = 温度 0 で 1 回再生成(§7)。再生成で通れば format_retry_ok。
  - `test_format_error_twice_falls_to_undefined_five_stages`(関数): 再生成後も語彙一致しなければ未定義行動5段(§7)へ。
  - `test_format_retry_still_fires_for_真の書式崩れ`(関数): 別名でも辞書でも読めない応答は、従来どおり温度 0 で 1 回再生成する。
  - `test_http_5xx_is_a_connection_error`(関数)
  - `test_in_flight_returns_to_zero_after_drain`(関数)
  - `test_label_alias_counts_strict_errors_without_regenerating`(関数): 別名で読めた応答は**温度 0 の再生成をしない**(実効基準)が、厳密側には計上する。
  - `test_model_discovery`(関数)
  - `test_out_of_vocabulary_action_is_counted_as_dictionary_mapped`(関数): 語彙外の行動語は §7 段0 の辞書で救い、``fleet_dictionary_mapped`` に計上する。
  - `test_payload_carries_cache_salt_seed_and_no_structured_outputs`(関数)
  - `test_plan_batch_groups_same_cell_bucket_onto_distinct_replicas`(関数)
  - `test_plan_batch_least_in_flight_on_imbalance`(関数)
  - `test_plan_batch_least_in_flight_when_saturated`(関数)
  - `test_plan_batch_without_group_spread_follows_pure_mod_n`(関数)
  - `test_positional_reading_is_counted`(関数): ラベルを省いた並びを位置で読んだ応答を ``fleet_positional_used`` に数える。
  - `test_queue_full_is_non_blocking`(関数): キュー満杯 = 非ブロッキングで「入らなかった」を返す(アービタが繰り延べる)。
  - `test_route_primary_is_deterministic_mod_n`(関数)
  - `test_smoke_all_ok`(関数)
  - `test_t2_lane_uses_thinking_and_infra_clip_ceiling`(関数)
  - `test_temperature_and_max_tokens_are_configurable_and_recorded`(関数): ``--temperature 0.7 --max-tokens 96`` 相当が payload と manifest 欄に載る。
  - `test_ttft_timeout_defers_not_discards`(関数): TTFT 超過 = 繰り延べ(破棄禁止・憲法1)。再試行はしない。
- import している内部モジュール: `shibuya.engine.llm_bridge`・`shibuya.foundation.hashing`・`shibuya.foundation.manifest.schema`・`shibuya.foundation.vocab.actions`・`shibuya.llm`・`shibuya.llm.fleet`・`shibuya.runtime.inference.tape`
- 読む試験: `tests/engine/test_10a_review_fixes.py`・`tests/engine/test_fleet_wiring.py`・`tests/engine/test_response_delay.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_state_ledger_10b.py`・`tests/engine/test_tape_deferred.py`・`tests/engine/test_version_bump_10e.py`・`tests/engine/time/test_v30a_key_sites.py`・`tests/perception/facts/test_percept_is_scratch.py`

## [test_fleet_auth.py](../../../../../../tests/llm/test_fleet_auth.py)

艦隊の API key(環境変数 ``SHIBUYA_FLEET_API_KEY``)のヘッダ(tools/night5070 の安全の規則 1)。

- 公開の関数とクラス
  - `test_bearer_header_when_env_set`(関数)
  - `test_no_header_without_env`(関数)
- import している内部モジュール: `shibuya.llm.fleet`

## [test_fleet_contract.py](../../../../../../tests/llm/test_fleet_contract.py)

C6-a 艦隊接続の契約テスト(層契約・純関数・性質)。HTTP サーバーを立てない軽い側。

- 公開の関数とクラス
  - `test_bridge_result_fields_mirror_engine_bridge_result`(関数): ``FleetBridgeResult`` は ``engine.llm_bridge.BridgeResult`` の欄を包含する。
  - `test_budget_rows_are_read_not_duplicated`(関数)
  - `test_cache_salt_differs_per_mode_and_is_stable`(関数)
  - `test_config_rejects_bad_input`(関数)
  - `test_default_timeouts_follow_plan_section7`(関数)
  - `test_every_call_is_accounted_for`(関数): 性質: 任意の呼集合で **返る結果の数 = 呼数**・**帳尻 = 呼数**(呼を捨てない=憲法1)。
  - `test_fleet_module_imports_no_forbidden_layer`(関数): ``llm`` は engine/perception/world/agents を import しない(AST での二重化)。
  - `test_l6_default_is_read_from_the_budget_table`(関数)
  - `test_lane_think_tokens_matches_engine_canon`(関数): ``LANE_THINK_TOKENS`` は層契約のための複製=engine 側の正典と同値を機械で固定する。
  - `test_manifest_fields_record_verification_run_settings`(関数)
  - `test_max_tokens_follows_u19_infra_clip`(関数)
  - `test_plan_batch_is_a_permutation_and_deterministic`(関数)
  - `test_routing_spreads_over_seven_replicas_like_the_plan`(関数): §7「レプリカ配分=xxhash(call_id) mod 7」。実艦隊規模で偏りが極端でないこと。
  - `test_seed_is_a_function_of_call_id_and_run_seed`(関数)
  - `test_single_replica_has_no_alternate_and_is_counted`(関数): レプリカ 1 本では「別レプリカ 1 回」が退化する=診断行に残す。
  - `test_split_system_user`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.build`・`shibuya.economy.ledger`・`shibuya.engine.llm_bridge`・`shibuya.engine.resolve`・`shibuya.foundation.budget`・`shibuya.foundation.manifest.schema`・`shibuya.llm.fleet`・`shibuya.perception.renderer`・`shibuya.world.model.state`・`tests/_places.py`
- 決定の ID: D-58

## [test_mock_v3.py](../../../../../../tests/llm/test_mock_v3.py)

mock 方策の語彙 v3 化(二層の段 3・D-116・第277・アジェンダ §3)。

- 公開の関数とクラス
  - `test_bad_form_is_refused`(関数)
  - `test_default_mock_follows_the_vocab_version`(関数)
  - `test_v1_form_is_the_default_and_unchanged`(関数)
  - `test_v3_draw_rules`(関数)
  - `test_v3_form_is_read_strictly_by_the_v3_parser`(関数)
  - `test_v3_is_deterministic_and_counter_based`(関数)
- import している内部モジュール: `shibuya.act.intake.parser`・`shibuya.engine.run`・`shibuya.foundation.vocab.actions`・`shibuya.llm`・`shibuya.llm.mock`
- 決定の ID: D-116・第 277

## [test_parser.py](../../../../../../tests/llm/test_parser.py)

llm.parser のテスト(ラベル基準の寛容行指向・**例外を投げない**・往復)。

- 公開の関数とクラス
  - `test_c6_a_missing_label_is_still_a_format_error`(関数)
  - `test_c6_alias_table_shapes`(関数)
  - `test_c6_dictionary_candidate_is_empty_when_the_word_is_in_the_vocabulary`(関数)
  - `test_c6_dictionary_candidate_is_reported_at_the_first_judgement`(関数)
  - `test_c6_dictionary_mapping_is_carried_on_the_parse_result`(関数): 段0 の写像は ``undefined`` の仕事。パーサは**結果を載せる口**だけ持つ。
  - `test_c6_dictionary_mapping_keeps_role_word_flag`(関数)
  - `test_c6_escaped_newline_is_read_as_a_line_break`(関数): テープに ``ため  \n行動:`` の形(literal backslash-n)で残った応答も読む。
  - `test_c6_every_new_alias_is_accepted_and_flagged`(関数)
  - `test_c6_first_occurrence_wins_when_both_対象_and_目的地_appear`(関数)
  - `test_c6_full_width_colon_and_full_width_space_with_aliases`(関数)
  - `test_c6_out_of_vocabulary_and_out_of_dictionary_word_stays_undefined`(関数): 語彙外かつ辞書外は**拾わない**(=§7 段1 へ。段0 の表は undefined 側のテスト)。
  - `test_c6_positional_both_values_after_the_action_word`(関数)
  - `test_c6_positional_does_not_fire_when_the_action_word_is_not_the_first_token`(関数): 「行動: すぐに 移動 なし」型は位置で読める形ではない=触らない(誤読の予防)。
  - `test_c6_positional_does_not_fire_without_a_spare_token`(関数)
  - `test_c6_positional_only_対象_is_missing`(関数)
  - `test_c6_positional_values_are_free_text_and_are_not_rejected`(関数): 対象/ひと言は自由文=意味不明でも落とさない(切り詰め規則は従来どおり)。
  - `test_c6_positional_with_a_label_alias_in_the_same_line`(関数)
  - `test_c6_positional_with_an_unknown_action_word_still_recovers_the_slots`(関数)
  - `test_c6_positional_without_a_second_value_defaults_ひと言_to_なし`(関数)
  - `test_c6_positional_ひと言_keeps_its_spaces`(関数): 対象は1トークン・ひと言は**残り全部**(自由文なので落とさない)。
  - `test_c6_positional_ひと言_pushed_into_the_対象_field`(関数)
  - `test_c6_smoke_目的_is_read_as_対象`(関数)
  - `test_c6_smoke_目的地_is_read_as_対象`(関数)
  - `test_c6_smoke_観察_is_a_vocabulary_problem_not_a_label_problem`(関数): 3例目はラベルは正しく**行動語だけが語彙外**=書式は落ちたまま §7 段0 へ回る。
  - `test_c6_spaces_around_the_label_are_absorbed`(関数)
  - `test_c6_three_lines_with_free_prose_is_still_a_format_error`(関数)
  - `test_c6_trailing_escaped_newline_inside_a_value_is_dropped`(関数)
  - `test_canonical_labels_are_not_counted_as_aliases`(関数)
  - `test_d113_every_tape_surface_maps_to_対象`(関数)
  - `test_d113_positional_behaviour_without_unknown_labels_is_unchanged`(関数)
  - `test_d113_unknown_label_before_both_positional_values`(関数)
  - `test_d113_unknown_label_token_is_skipped_and_recorded`(関数): 別名表に無い「語+コロン」は値ではない: 読み飛ばして診断に残し、次のトークンを対象に。
  - `test_d113_unknown_label_without_a_value_is_a_missing_field`(関数)
  - `test_d113_目標_is_read_as_対象_not_as_a_value`(関数)
  - `test_degenerate_inputs_never_raise`(関数)
  - `test_duplicate_labels_keep_the_first_value`(関数)
  - `test_fenced_and_bulleted_and_bold_output`(関数)
  - `test_find_action_word_prefers_the_earliest_then_longest`(関数)
  - `test_first_vocabulary_word_in_the_action_field_wins`(関数)
  - `test_four_line_probe_form_is_accepted_and_行き先_maps_to_対象`(関数)
  - `test_free_text_fallback_does_not_read_the_reason_field`(関数): 理由欄の中の語は拾わない(ラベル済みの範囲は走査対象外)。
  - `test_full_width_colon_and_brackets`(関数)
  - `test_label_order_and_alias_choice_do_not_change_the_reading`(関数): ラベルの**順序**と**表層の選び方**を変えても、読み取り結果は変わらない。
  - `test_labels_packed_into_one_line_are_split`(関数)
  - `test_missing_action_label_falls_back_to_free_text`(関数)
  - `test_particles_after_the_action_word`(関数)
  - `test_random_junk_never_raises`(関数)
  - `test_role_word_is_recognised_and_flagged`(関数)
  - `test_strict_two_line_form`(関数)
  - `test_think_block_is_stripped`(関数)
  - `test_truncation_is_a_flag_not_a_failure`(関数)
  - `test_unknown_action_word_is_not_guessed_when_the_label_exists`(関数): 行動ラベルがあるのに語彙外なら**拾わない**(=§7 段0 の辞書写像へ回す)。
  - `test_v0_aliases_stay_inside_the_old_acceptance_metric`(関数): ``行き先``/``一言`` は C6 以前からの別名=``strict_format_ok`` は**真のまま**。
  - `test_v1_results_carry_empty_v3_fields`(関数)
  - `test_v3_act_words_still_need_the_target_label`(関数)
  - `test_v3_activity_is_truncated_not_rejected`(関数)
  - `test_v3_alias_label_is_lenient_but_not_strict`(関数)
  - `test_v3_comment_is_not_required_but_is_still_read`(関数)
  - `test_v3_dictionary_mapping_uses_the_v3_role_set`(関数)
  - `test_v3_draft_examples`(関数)
  - `test_v3_empty_and_degenerate_inputs_never_raise_and_carry_defaults`(関数)
  - `test_v3_five_labels_are_the_contract`(関数)
  - `test_v3_none_and_queue_are_vocabulary_words`(関数)
  - `test_v3_none_may_omit_the_target_label_decision_275_4`(関数): 第275 #4: 行動=なし なら対象ラベルの省略を許す(対象=なし・``target_omitted`` を残す)。
  - `test_v3_positional_all_three_after_the_action_word`(関数)
  - `test_v3_positional_defaults_activity_and_until`(関数): 「行動: 移動 自宅」型: v1 の comment_defaulted と同じく位置で読んだ応答だけ既定へ倒す。
  - `test_v3_positional_does_not_fire_when_the_action_word_is_not_first`(関数)
  - `test_v3_positional_does_not_fire_without_a_spare_token`(関数)
  - `test_v3_positional_overflow_from_the_activity_field`(関数)
  - `test_v3_positional_overflow_from_the_target_field`(関数)
  - `test_v3_random_junk_never_raises`(関数)
  - `test_v3_removed_words_are_unknown_and_the_dictionary_offers_none`(関数)
  - `test_v3_unknown_label_is_skipped_in_positional_reading`(関数)
  - `test_v3_v1_shaped_output_is_a_format_error`(関数): v1 の形(ひと言 で終わる)を v3 で読むと 活動・まで が欠ける(補わない)。
  - `test_v3_wander_target_and_base_word_hints`(関数)
  - `test_v3_well_formed_output`(関数)
  - `test_v3_well_formed_output_round_trips`(関数)
  - `test_well_formed_output_round_trips_through_format_two_line`(関数)
- import している内部モジュール: `shibuya.act.intake.parser`・`shibuya.foundation.vocab.actions`
- 決定の ID: D-89・D-113・D-116・第 223・第 266・第 274・第 275・第 275 #4

## [test_undefined.py](../../../../../../tests/llm/test_undefined.py)

llm.undefined のテスト(行動契約書 §7「未定義行動の受理」5段)。

- 公開の関数とクラス
  - `ScriptedLLM`(クラス): 裁定LLMの差し替え(``LLMClient`` 契約・呼数を数える)。
  - `test_adopt_requires_an_action_spec`(関数)
  - `test_c6_additions_do_not_shadow_the_existing_table`(関数): 既存の写像は C6 追加後も変わらない(部分一致の最長優先が壊れていない)。
  - `test_c6_precedent_is_not_reported_as_a_dictionary_mapping`(関数): 段4(判例)は ``source="precedent"``=辞書写像とは別に数える。
  - `test_c6_stage0_maps_the_commute_words_to_移動`(関数): ``--fleet-debug-dir`` 実測の ``unknown_action_word`` 96 の第2群(通勤 16)。
  - `test_c6_stage0_maps_the_search_and_look_words_without_any_llm_call`(関数)
  - `test_c6_stage0_policy_locomotion_vs_stationary`(関数): 方針: 移動を伴う探索→移動 / その場の観察・確認→待機(既存「様子を見る→待機」に接続)。
  - `test_c6_vocabulary_words_are_not_in_the_dictionary`(関数): ``通報``/``退去``/``購入`` は §2.1 の12語=語彙一致で通るので辞書に入れない。
  - `test_c6_words_outside_both_the_vocabulary_and_the_dictionary_reach_stage1`(関数)
  - `test_dictionary_v5_changes_only_the_rule_rows_and_the_listed_words`(関数)
  - `test_dictionary_v5_has_no_removed_word_as_a_destination`(関数): アジェンダ §1-3: 辞書 v5 の写像先に 待機/休憩/降車 が 1 行も無い。
  - `test_dictionary_v5_is_selected_only_by_vocab_v3`(関数)
  - `test_dictionary_v5_keeps_the_action_side`(関数)
  - `test_dictionary_v5_maps_activity_and_removed_rows_to_none`(関数)
  - `test_no_adjudicator_means_no_stage2`(関数)
  - `test_registry_in_v3_maps_to_none_and_offers_v3_words`(関数)
  - `test_registry_works_with_the_project_mock_llm`(関数): 裁定側に ``MockLLM`` を挿しても契約(1呼・状態遷移)は壊れない。
  - `test_reject_keeps_the_word_out_of_the_vocabulary`(関数)
  - `test_stage0_dictionary_maps_without_any_llm_call`(関数)
  - `test_stage0_partial_match_prefers_the_longest_surface`(関数)
  - `test_stage0_target_is_the_engines_job_for_帰る`(関数): 「帰る」は移動へ写すが、対象(=自宅セル)は**エンジンが決める**=ヒントだけ返す。
  - `test_stage1_log_is_bounded`(関数)
  - `test_stage1_records_counts_and_returns_the_failure_feedback`(関数)
  - `test_stage2_fires_once_at_the_threshold_of_n_distinct_agents`(関数)
  - `test_stage2_prompt_asks_for_the_five_contract_fields`(関数)
  - `test_stage2_repeats_from_the_same_agent_do_not_reach_the_threshold`(関数)
  - `test_stage3_clean_rows_stay_merely_proposed`(関数)
  - `test_stage3_rows_touching_conservation_need_parent_review`(関数)
  - `test_stage4_adoption_makes_the_second_occurrence_deterministic`(関数)
  - `test_stage4_can_add_a_brand_new_word_to_the_runtime_vocabulary`(関数)
  - `test_stage4_needs_parent_review_rows_are_only_adopted_explicitly`(関数)
  - `test_synonym_table_is_versioned`(関数)
  - `test_target_hints_v5_add_the_base_words_for_the_target_field`(関数)
- import している内部モジュール: `shibuya.foundation.vocab.actions`・`shibuya.llm`・`shibuya.llm.undefined`
- 決定の ID: D-116・第 274

## [test_vocab_v2.py](../../../../../../tests/llm/test_vocab_v2.py)

語彙 v2(横断語「食事」)の契約側 — D-71 §3 E/F/H(ユーザー決定 2026-09-17)。

- 公開の関数とクラス
  - `test_compat_table_reads_the_new_word_as_the_old_one`(関数)
  - `test_compat_targets_are_words_of_the_old_vocabulary`(関数): 読み替え先は**必ず旧版に実在する語**(比較のための橋が壊れていないこと)。
  - `test_dictionary_v3_is_only_a_diff_on_top_of_v1`(関数): v3 = v1 の表 + 差分。**差分以外の行は 1 つも変わらない**。
  - `test_dictionary_v3_maps_the_eating_family_to_the_new_word`(関数)
  - `test_eat_is_unknown_in_v1`(関数): 既定(v1)では「食事」は語彙外=未定義行動の経路へ行く。
  - `test_parser_reads_the_new_word_only_in_v2`(関数)
  - `test_parser_v1_results_are_unchanged_for_every_v1_word`(関数)
  - `test_stage0_still_works_for_the_untouched_rows_in_v2`(関数)
  - `test_the_eat_code_is_appended_not_inserted`(関数): 既存コード(12 語 0..11・役割語 12..23)は 1 つも動かず、食事は**末尾の 24**。
  - `test_the_eat_contract_row_is_declared`(関数)
  - `test_the_registry_resolves_the_eating_family_in_v2`(関数)
  - `test_unknown_vocab_version_is_refused`(関数)
  - `test_v1_dictionary_and_its_version_do_not_move`(関数)
  - `test_v1_objects_are_untouched`(関数): v1 の語彙・コード・契約表は**同一オブジェクト**(名前を足しただけ)。
  - `test_v2_appends_one_cross_cutting_word`(関数)
  - `test_v2_vocabulary_exceeds_the_declared_limit_by_one`(関数): §2「種別あたり 24 語」を **1 語超える**ことを機械で可視化する(封印は D-71 §3 J 待ち)。
- import している内部モジュール: `shibuya.act.intake.parser`・`shibuya.agents.state`・`shibuya.foundation.vocab.actions`・`shibuya.llm.undefined`
- 決定の ID: D-71・第 274
