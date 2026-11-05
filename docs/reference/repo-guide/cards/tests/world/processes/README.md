# tests/world/processes

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 10 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../tests/world/processes/__init__.py)

(冒頭の説明なし)

## [conftest.py](../../../../../../../tests/world/processes/conftest.py)

world.processes のテスト用ファクトリ(最小の合法な宣言を作る)。

- 公開の関数とクラス
  - `make_growth`(関数)
  - `make_plan_spec`(関数)
  - `make_process`(関数)
  - `registry`(関数)
  - `test_catalog`(関数)
- import している内部モジュール: `shibuya.core.growth`・`shibuya.manifest.world_catalog`・`shibuya.world.processes.records`・`shibuya.world.processes.registry`
- 読む試験: `tests/world/processes/test_constitution.py`・`tests/world/processes/test_declarations_1101.py`・`tests/world/processes/test_records.py`・`tests/world/processes/test_registry.py`

## [test_actual_log.py](../../../../../../../tests/world/processes/test_actual_log.py)

追記専用 ActualLog: 追記・増分索引・保持窓と日次集約・遵守率・成長宣言(D-R2-6)。

- 公開の関数とクラス
  - `test_24step_smoke_extrapolates_within_cap`(関数): D-R2-6 のゲート: 24step スモークの実測を 1日/30日 へ外挿して cap と突き合わせる。
  - `test_append_and_entries`(関数)
  - `test_append_many_checks_delay_rule`(関数)
  - `test_append_many_is_vectorized`(関数)
  - `test_append_rejects_bad_delay`(関数)
  - `test_capacity_grows`(関数)
  - `test_compliance_rate_counts_aggregated_days`(関数): 保持窓で畳まれた日も数え落とさない(集約の意味が守られる)。
  - `test_compliance_rate_is_nan_without_observations`(関数)
  - `test_compliance_rate_is_the_scheduled_share`(関数)
  - `test_compliance_rate_windowed`(関数)
  - `test_dtype_is_fixed_width_and_frozen`(関数)
  - `test_evict_folds_old_days_into_daily_counts`(関数)
  - `test_evict_is_a_noop_without_retention`(関数)
  - `test_evict_remaps_the_index`(関数)
  - `test_growth_declarations_have_retention_and_a_fold_target`(関数)
  - `test_growth_gate_fails_when_the_log_grows_faster_than_declared`(関数)
  - `test_index_is_per_process_and_incremental`(関数)
  - `test_plan_compliance_uses_realizes_relations`(関数)
  - `test_plan_compliance_without_realizes_raises`(関数)
  - `test_rows_view_is_read_only`(関数)
- import している内部モジュール: `shibuya.core.growth`・`shibuya.world.processes.actual_log`・`shibuya.world.processes.first_batch`・`shibuya.world.processes.records`

## [test_constitution.py](../../../../../../../tests/world/processes/test_constitution.py)

憲法5 の機械検査(D-R2-4)と、id 集合の凍結写し ↔ Markdown の一致。

- 公開の関数とクラス
  - `test_detected_at_is_optional_and_deterministic`(関数)
  - `test_discarded_pattern_is_rejected`(関数)
  - `test_empty_declaration_is_a_violation`(関数)
  - `test_missing_doc_raises`(関数)
  - `test_output_ids_satisfy_b`(関数)
  - `test_parsers_accept_explicit_paths`(関数)
  - `test_partially_vanished_target_is_not_a_deletion_candidate`(関数)
  - `test_pattern_ledger_ids_match_the_frozen_list`(関数)
  - `test_perception_channel_ids_match_the_contract`(関数): 知覚契約書 §3 の表を読み直して凍結写しと一致することを見る(正典は Markdown)。
  - `test_plan_spec_compliance_field_violation_is_reported`(関数)
  - `test_plan_spec_scope_violation_is_reported`(関数): 型を迂回して作られた PlanSpec(公示範囲が空)も検査で捕まる。
  - `test_positive_declaration_passes`(関数)
  - `test_proposed_channel_ids_are_not_in_the_contract`(関数): PROPOSED は「まだ §3 に無い」もの。既定の検査集合にも入っていない。
  - `test_report_ok_for_a_good_ledger`(関数)
  - `test_sealed_pattern_is_rejected`(関数): パターン台帳 §2 運用規則5「以後の設計議論で言及・参照しない」。
  - `test_slots_are_not_interchangeable`(関数): パターン id を reaches に書くのは違反(スロットが違う)。
  - `test_suspended_channel_is_in_the_table_but_not_usable`(関数)
  - `test_suspended_channel_is_rejected`(関数)
  - `test_undeclared_detail_becomes_a_deletion_candidate`(関数): 知覚契約書 §1 不変条件2「宣言のない細部は削除候補として台帳に自動掲載」。
  - `test_unknown_ids_are_violations`(関数)
  - `test_vanished_target_becomes_a_deletion_candidate`(関数): 「宣言した届き先が消えた細部は、削除候補として台帳に自動的に載る」(§5)。
- import している内部モジュール: `shibuya.manifest.world_catalog`・`shibuya.world.processes.constitution`・`shibuya.world.processes.records`・`shibuya.world.processes.registry`・`tests/world/processes/conftest.py`

## [test_declarations_1101.py](../../../../../../../tests/world/processes/test_declarations_1101.py)

第340 段 2 の 6・7: 宣言の 3 欄(``drives_from``・``absent``・``input_decl``)と一覧(回答 11-01 §1・§2・§10-3)。

- 公開の関数とクラス
  - `test_absence_requires_statement_reason_and_remove_at`(関数)
  - `test_absence_type_is_frozen`(関数)
  - `test_absent_processes_of_answer_10_3`(関数)
  - `test_attached_to_world_processes`(関数)
  - `test_declaration_fields_do_not_enter_as_dict_or_the_registry_hash`(関数)
  - `test_drives_from_none_is_alone`(関数)
  - `test_filled_input_needs_every_value_and_a_source_row`(関数)
  - `test_inputs_attached_to_world_processes`(関数)
  - `test_inputs_existing_five_filled_and_new_seven_fields_only`(関数)
  - `test_routing_absent_rows_all_have_a_declaration`(関数): routing §1 の行き先「無いと宣言」の 6 行は宣言がある(#102 納品は入力として)。
  - `test_statements_are_copied_from_routing_section_3`(関数): routing §3 に文案のある宣言は文案の写し(「」の中=鉤括弧の文と一致)。
- import している内部モジュール: `shibuya.world.processes.absent`・`shibuya.world.processes.first_batch`・`shibuya.world.processes.inputs`・`shibuya.world.processes.records`・`tests/world/processes/conftest.py`
- 決定の ID: 11-01/§1・11-01/§2・11-01/§10-3・第 340

## [test_deletion_candidates.py](../../../../../../../tests/world/processes/test_deletion_candidates.py)

削除候補台帳ファイル(``runs/`` へ冪等追記)の検査。

- 公開の関数とクラス
  - `test_append_creates_and_reloads`(関数)
  - `test_append_is_idempotent`(関数)
  - `test_broken_file_raises`(関数)
  - `test_default_path_is_under_runs`(関数)
  - `test_docs_path_is_refused`(関数)
  - `test_file_is_deterministic_and_sorted`(関数)
  - `test_first_seen_is_preserved`(関数)
  - `test_load_missing_file_is_empty`(関数)
  - `test_vanished_targets_are_merged`(関数)
- import している内部モジュール: `shibuya.world.processes.constitution`・`shibuya.world.processes.deletion_candidates`

## [test_first_batch.py](../../../../../../../tests/world/processes/test_first_batch.py)

第1陣の宣言(D-R2-5 / §7.1-7.2)が**実物の設計書 id**に対して憲法5 検査を通ること。

- 公開の関数とクラス
  - `reg`(関数)
  - `test_build_without_pulled_forward`(関数)
  - `test_coverage_report_is_reportable`(関数)
  - `test_declarations_pass_constitution5_against_the_real_docs`(関数): 知覚契約書 §3 とパターン台帳を**その場で読み直した** id 集合で検査する。
  - `test_engine_rule_rows_are_all_on_the_fallback_ledger`(関数)
  - `test_every_process_declares_a_catalog_class_in_the_frozen_catalog`(関数)
  - `test_expedients_carry_sensitivity_and_repayment`(関数)
  - `test_fallback_rows_are_marked_as_agent_fallback_or_external`(関数): engine_rule は §1「エージェント化できるのに代替」か、bbox 外(B類)に限る。
  - `test_first_batch_covers_the_six_of_d_r2_5`(関数)
  - `test_first_batch_covers_the_u_goods_skeleton`(関数)
  - `test_growth_declaration_names_are_unique`(関数)
  - `test_natural_processes_are_not_fallbacks`(関数)
  - `test_no_proposed_channel_is_used_silently`(関数): PROPOSED(=§3 に無い提案 id)を宣言に紛れ込ませない。
  - `test_no_sealed_or_suspended_target`(関数)
  - `test_only_actual_log_grows_with_time`(関数): §2「**O(t) 成長する唯一の型**が ActualLog」——世界過程の状態は全て O(1)。
  - `test_plan_specs_are_announced_and_measured`(関数)
  - `test_pulled_forward_batch_matches_7_2`(関数)
  - `test_rail_and_opening_are_realized_by_engine_rule_for_now`(関数)
  - `test_registry_hash_is_stable_across_builds`(関数)
- import している内部モジュール: `shibuya.manifest.world_catalog`・`shibuya.world.processes.constitution`・`shibuya.world.processes.first_batch`・`shibuya.world.processes.records`・`shibuya.world.processes.relations`

## [test_records.py](../../../../../../../tests/world/processes/test_records.py)

レコード型3(D-R2-2)の検査。

- 公開の関数とクラス
  - `test_announcement_blocks_are_b2_b3_only`(関数)
  - `test_conf_only_on_engine_rule`(関数)
  - `test_delay_minutes_iff_delay`(関数)
  - `test_detail_requires_description`(関数)
  - `test_deviation_codes_are_frozen_and_bijective`(関数)
  - `test_duplicate_ids_in_reaches_rejected`(関数)
  - `test_engine_rule_needs_conf_coverage_repayment`(関数)
  - `test_enum_fields_are_typed`(関数)
  - `test_expedient_needs_sensitivity_and_repayment`(関数)
  - `test_growth_declaration_is_required_by_type`(関数): §3 実装原則2「状態成長の宣言を必須化」——型で強制する。
  - `test_growth_name_is_free_but_declaration_shape_is_fixed`(関数)
  - `test_minimal_process_is_valid`(関数)
  - `test_plan_spec_requires_announcement_scope`(関数): D-R2-4「公示されない計画は(a)を満たさず作れない」。
  - `test_plan_spec_requires_compliance_field`(関数)
  - `test_plan_spec_revision_bumps_version_and_transaction_time`(関数)
  - `test_plan_spec_revision_rejects_wrong_authority`(関数)
  - `test_process_as_dict_is_json_ready`(関数)
  - `test_required_fields`(関数)
  - `test_scheduled_is_the_compliance_numerator`(関数)
  - `test_validity_covers`(関数)
- import している内部モジュール: `shibuya.world.processes.records`・`tests/world/processes/conftest.py`

## [test_registry.py](../../../../../../../tests/world/processes/test_registry.py)

台帳(名前空間1つ)の登録検査・被覆報告・決定論 JSON/ハッシュ。

- 公開の関数とクラス
  - `test_add_process_and_lookup`(関数)
  - `test_add_process_rejects_unknown_target`(関数)
  - `test_add_process_runs_constitution_check`(関数): reaches も contributes も空の過程は登録できない(D-R2-4)。
  - `test_coverage_report_shares`(関数)
  - `test_detail_needs_registered_owner`(関数)
  - `test_duplicate_process_id_rejected`(関数)
  - `test_fallback_ledger_covers_relations_and_planless_processes`(関数)
  - `test_non_strict_registry_collects_instead_of_raising`(関数)
  - `test_registry_hash_changes_with_content`(関数)
  - `test_relation_targets_must_exist`(関数)
  - `test_to_json_is_deterministic_and_hash_stable`(関数)
  - `test_unknown_catalog_class_rejected`(関数)
- import している内部モジュール: `shibuya.manifest.world_catalog`・`shibuya.world.processes.records`・`shibuya.world.processes.registry`・`shibuya.world.processes.relations`・`tests/world/processes/conftest.py`

## [test_relations.py](../../../../../../../tests/world/processes/test_relations.py)

関係4本(§2)と conf宣言つきフォールバック台帳(§1 末尾)の検査。

- 公開の関数とクラス
  - `test_agent_action_subject_is_allowed`(関数)
  - `test_conf_range`(関数)
  - `test_conf_rejected_on_non_engine_rule`(関数)
  - `test_counts_as_requires_context`(関数)
  - `test_engine_rule_realizes_needs_conf_coverage_repayment`(関数)
  - `test_fallback_ledger_is_sorted`(関数)
  - `test_fallback_ledger_lists_only_engine_rule_rows`(関数)
  - `test_realizes_requires_executor_attribute`(関数): §2「realizes … 属性 executor: {llm_agent | engine_rule | none}」。
  - `test_records_requires_target_type`(関数)
  - `test_revises_version_must_be_a_revision`(関数)
- import している内部モジュール: `shibuya.world.processes.records`・`shibuya.world.processes.relations`
