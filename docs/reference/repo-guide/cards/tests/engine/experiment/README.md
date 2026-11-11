# tests/engine/experiment

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 10 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../tests/engine/experiment/__init__.py)

(冒頭の説明なし)

## [_x33.py](../../../../../../../tests/engine/experiment/_x33.py)

第 3 期 3-3 の試験の共通の材料(申込書の雛形・合成の世界の組み立て)。

- 公開の関数とクラス
  - `at`(関数): 刻みの頭の時刻 ``t_ns`` で口を 1 回(記録の時計をその刻みに置いてから)。
  - `form`(関数)
  - `form_dict`(関数)
  - `handle`(関数)
  - `rows`(関数)
  - `synthetic_world`(関数): 合成の世界(``World.synthetic``)+手書きの W7・W13 の世界過程 2 つ(営業時間・天気)と暦と出来事の記録。
- import している内部モジュール: `shibuya.engine.calendar`・`shibuya.experiments.port.apply`・`shibuya.experiments.port.form`・`shibuya.foundation.journal.log`・`shibuya.foundation.time_consts`・`shibuya.world.laws.environment`・`shibuya.world.laws.opening`・`tests/engine/processes/conftest.py`
- 読む試験: `tests/engine/experiment/test_cf33b_form_checks.py`・`tests/engine/experiment/test_cf33b_manifest.py`・`tests/engine/experiment/test_cf33b_switch.py`・`tests/engine/experiment/test_x33_apply.py`・`tests/engine/experiment/test_x33_branch.py`・`tests/engine/experiment/test_x33_ensemble.py`・`tests/engine/experiment/test_x33_form.py`・`tests/engine/experiment/test_x33_run.py`・`tests/tools/test_skill_gauge.py`

## [test_cf33b_form_checks.py](../../../../../../../tests/engine/experiment/test_cf33b_form_checks.py)

第 3 期 3-3b 申込書の点検(``engine.experiment.checks``)と省略できる欄(CP5-1・CP5-3・仮-24)。

- 公開の関数とクラス
  - `test_aa_keeps_the_declarations`(関数)
  - `test_base_form_is_unchanged`(関数): 3-3 の雛形(BASE)に省略できる欄は無い。
  - `test_known_to_model_is_in_the_manifest`(関数)
  - `test_naming_hits_is_one_tool_for_persona_and_contamination`(関数)
  - `test_optional_field_errors`(関数)
  - `test_optional_fields_do_not_change_old_forms`(関数)
  - `test_start0_check_flags_unexpected_changes_from_the_start`(関数)
  - `test_start0_warns_and_records_but_does_not_refuse`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.experiments.port.checks`・`shibuya.experiments.port.form`・`tests/engine/experiment/_x33.py`

## [test_cf33b_manifest.py](../../../../../../../tests/engine/experiment/test_cf33b_manifest.py)

第 3 期 3-3b manifest の ``experiment`` の足した欄・慣らしの規則の事前登録・技量スコアの隣の生の点数の欄・床の分布・封印の証拠。

- 公開の関数とクラス
  - `test_config_keys_were_appended_and_old_ones_kept`(関数)
  - `test_every_rule_item_has_a_mark`(関数)
  - `test_floor_distribution_of_aa_pairs`(関数)
  - `test_manifest_fields_of_a_form_run`(関数)
  - `test_preregistration_has_the_evidence_slot_and_the_warmup_rule`(関数)
  - `test_skill_container_has_raw_scores_next_to_the_skill`(関数)
  - `test_warmup_rule_is_a_registered_rule_not_dates`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.experiments.port.ensemble`・`shibuya.experiments.port.layer`・`shibuya.experiments.port.warmup`・`shibuya.foundation.manifest.sections`・`tests/engine/experiment/_x33.py`
- 決定の ID: R-117

## [test_cf33b_switch.py](../../../../../../../tests/engine/experiment/test_cf33b_switch.py)

第 3 期 3-3b T からの切り替えの口(``engine.experiment.switch``・CP5-2 の完成)と 4 つの確認の (c)(d) の分け(仮-24)。

- 公開の関数とクラス
  - `synth_base`(関数)
  - `test_a_leaky_box_is_caught`(関数)
  - `test_an_injected_port_can_declare_determinism`(関数)
  - `test_live_factory_answers_only_from_t0`(関数)
  - `test_meters_are_read_only`(関数)
  - `test_model_labels_and_determinism`(関数)
  - `test_replay_switch_box_is_emptied_every_step`(関数)
  - `test_run_branch_refuses_a_t0_that_is_not_a_window_head`(関数)
  - `test_run_branch_refuses_a_tape_with_rows_crossing_t0`(関数): 負の対照: T より前に出して T 以後に届く行(艦隊の到着待ち)=再生の箱に刻みの外の物が残る=止める。
  - `test_switch_leaky_box_fails_b_end_to_end`(関数): 負の対照(合成の世界の分岐): 箱を空にしない写しに差し替えると (b) が落ちる。
  - `test_switch_with_a_declared_deterministic_port`(関数)
  - `test_switch_with_a_nondeterministic_model_gives_a_floor`(関数)
  - `test_switch_with_the_classical_policy`(関数)
  - `test_switch_with_the_mock_is_deterministic`(関数)
  - `test_window_head_step`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.experiments.drive.branch`・`shibuya.experiments.drive.switch`・`shibuya.foundation.time_consts`・`shibuya.llm`・`shibuya.llm.mock`・`shibuya.runtime.inference.tape`・`tests/engine/experiment/_x33.py`

## [test_x33_apply.py](../../../../../../../tests/engine/experiment/test_x33_apply.py)

第 3 期 3-3 効かせる口 ``apply(form, world, t)``(決定 10-12 §1-1 CP6・§4-5 CP5・CP12)。合成の世界で試す。

- 公開の関数とクラス
  - `test_admit_and_the_table_writers_are_called_only_from_apply`(関数)
  - `test_branch_from_a_state_without_the_form_marks_earlier_starts_out_of_period`(関数)
  - `test_closure_enters_the_plan_once_and_the_opening_process_executes_it`(関数)
  - `test_holiday_for_a_later_day`(関数)
  - `test_inherited_run_puts_the_tables_again_without_new_rows`(関数): 再開(親が同じ申込書): 始まりが再開の時刻より前の決定は表へ当てるだけ(出来事と告知は親のランが書いた)。
  - `test_module_tables_are_read_only`(関数): 〔検収 L6〕口の表(決定の実装・理由の語)と分岐の表は読み取り専用。
  - `test_notice_rows_per_recipient`(関数)
  - `test_notice_without_recipients_is_counted_and_continues`(関数)
  - `test_opening_hours_and_event`(関数)
  - `test_the_calendar_is_written_through_its_one_mouth`(関数): 〔検収 L5〕祝日の表を書くのは暦の口 ``SimCalendar.set_holiday`` だけ(apply は辞書を直に書かない)。
  - `test_the_cause_still_cannot_be_made_outside_the_gate`(関数): 1-3 の負の対照が残る: 口の外から実験の条件の原因を作ると落ちる。
  - `test_the_entry_check_catches_a_planted_call`(関数): 負の対照: 口の外で admit(別名・直の import)・表の書き口を呼ぶ形は見つかる。別の物の admit は数えない。
  - `test_the_plan_is_put_again_after_the_day_head_and_restored_at_the_end`(関数)
  - `test_unapplied_is_recorded_and_the_run_continues`(関数)
  - `test_vocabulary_has_the_two_words`(関数)
  - `test_weather_date_swap_and_reapply`(関数)
- import している内部モジュール: `shibuya.experiments.drive.branch`・`shibuya.experiments.port.apply`・`shibuya.foundation.journal.log`・`shibuya.foundation.ports.experiment_gate`・`shibuya.foundation.vocab.events`・`shibuya.world.laws.environment`・`shibuya.world.laws.opening`・`tests/engine/experiment/_x33.py`
- 決定の ID: 10-12/§1-1

## [test_x33_branch.py](../../../../../../../tests/engine/experiment/test_x33_branch.py)

第 3 期 3-3 「T0 までテープを再生して T0 から今の方策」の分岐と R-71 の 4 つの確認(``engine.experiment.branch``)。

- 公開の関数とクラス
  - `test_branch_refuses_a_t0_outside_the_base`(関数)
  - `test_choose_state`(関数)
  - `test_cli_branch_end_to_end`(関数): CLI: 基準のランを既存の引数(--tape・--state-out・--checkpoints-out・--sim-days)で記録し、--experiment と
  - `test_input_match_negative_controls`(関数)
  - `test_pre_t0_and_aa_negative_controls`(関数)
  - `test_probe_first_divergence_and_filters`(関数)
  - `test_synthetic_branch_with_only_decision_and_notice_rows`(関数)
  - `test_synthetic_branch_with_the_classical_policy`(関数): 古典の方策(内部の状態を持つエンジンの方策)は T0 より前も方策に答えさせ、テープの答えとの食い違いを数える(0 のはず)。
  - `test_world_branch_four_checks`(関数)
  - `test_world_branch_replay_and_manifest`(関数)
  - `test_world_branch_report_file`(関数)
  - `test_world_branch_switch_and_the_split_of_d`(関数): 〔3-3b〕同じ分岐(世界資産 1,000 体・mock)が T からの切り替えの口を通る: 窓の頭・再生の箱 0・(d) の決定論の確認と床 0・
  - `test_world_branch_with_staff_5000`(関数): 〔親の判断 M3〕担当の従業者のいる世界(5,000 体=1-5 の担当 2,337 人)で同じ休業の分岐を回し、担当が実行した件数と
  - `test_world_resume_with_the_same_form_equals_straight`(関数): 申込書つきのラン(1 日目の正午から 200 店の休業)を日の境目で止めて同じ申込書で再開すると、通しのランと同じ
  - `world_branch`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.calendar`・`shibuya.experiments.drive.branch`・`shibuya.experiments.port.form`・`shibuya.foundation.manifest.sections`・`shibuya.foundation.time_consts`・`shibuya.world.assets`・`shibuya.world.laws.opening`・`shibuya.world.model.state`・`tests/engine/experiment/_x33.py`
- 決定の ID: R-71

## [test_x33_ensemble.py](../../../../../../../tests/engine/experiment/test_x33_ensemble.py)

第 3 期 3-3 探索と確認・アンサンブルの封印・事前登録(CP14)・対の差の形・技量スコアの器。

- 公開の関数とクラス
  - `test_confirm_with_the_matching_preregistration_gets_the_sealed_half`(関数)
  - `test_entrance_lets_each_form_run_only_its_half`(関数)
  - `test_explore_cannot_read_the_sealed_half`(関数)
  - `test_members_are_my_half_of_initial_times_model_times_chance`(関数)
  - `test_paired_values_go_to_salt_compare_and_give_a_p`(関数)
  - `test_seal_is_deterministic_and_exposes_only_fingerprints`(関数)
  - `test_skill_score_is_a_container_with_a_formula`(関数)
- import している内部モジュール: `shibuya.experiments.port.ensemble`・`shibuya.experiments.port.form`・`tests/engine/experiment/_x33.py`

## [test_x33_form.py](../../../../../../../tests/engine/experiment/test_x33_form.py)

第 3 期 3-3 申込書 ``ExperimentForm``(決定 10-12 §4-5 CP5-4・探索と確認・CP14)。

- 公開の関数とクラス
  - `names_in`(関数)
  - `test_aa_and_start_step`(関数)
  - `test_aa_of_a_confirm_form_round_trips`(関数): 〔検収 L4〕確認の申込書の A/A の枝は事前登録を引き継ぎ、元の登録の指紋を aa_of に残す=JSON の往復で通る。
  - `test_contradictions_are_errors`(関数)
  - `test_decision_table_levels_and_implementation`(関数)
  - `test_direct_construction_is_checked_too`(関数): 〔検収 L3〕``ExperimentForm(...)`` を直に作っても ``__post_init__`` が同じ検査を通す。
  - `test_fields_and_defaults`(関数)
  - `test_japanese_kind_aliases`(関数)
  - `test_json_round_trip_is_deterministic`(関数)
  - `test_name_check_catches_a_planted_name`(関数): 負の対照: 地名と業種名を書いた行は見つかる。
  - `test_no_place_or_business_names_in_the_experiment_code`(関数)
  - `test_preregistration_only_for_confirm_and_must_match`(関数)
  - `test_unknown_fields_are_errors`(関数)
- import している内部モジュール: `shibuya.experiments.drive.branch`・`shibuya.experiments.port.apply`・`shibuya.experiments.port.ensemble`・`shibuya.experiments.port.form`・`shibuya.experiments.port.layer`・`shibuya.foundation.ports.experiment_gate`・`tests/_places.py`・`tests/engine/experiment/_x33.py`
- 決定の ID: 10-12/§4-5

## [test_x33_run.py](../../../../../../../tests/engine/experiment/test_x33_run.py)

第 3 期 3-3 申込書をランに置く口(``layer.staged`` → 組み立て → 系 ``experiment``)・使わないとき不変・ランの種類・再開・宣言。

- 公開の関数とクラス
  - `plain`(関数)
  - `test_a_form_that_starts_after_the_run_is_out_of_period`(関数)
  - `test_cli_main_flags`(関数)
  - `test_cli_run_with_a_form_is_counterfactual`(関数)
  - `test_experiment_writes_are_within_the_declaration`(関数)
  - `test_forms_that_change_no_table_keep_every_checkpoint`(関数)
  - `test_ledger_row_x_enters_no_hash`(関数)
  - `test_manifest_section_keys_match_the_layer`(関数)
  - `test_no_form_no_system_and_null_manifest`(関数)
  - `test_owner_fields_cannot_be_replaced_and_checks_are_written_once`(関数)
  - `test_run_kind_rule`(関数)
  - `test_runtime_owner_instance_is_fully_declared`(関数): 状態台帳の網羅(10b-2・検収 2-6 の実行時の形): 申込書の持ち主のインスタンスの属性は行 X の道筋か除外の一覧にある。
  - `test_state_header_and_resume_checks`(関数)
  - `test_the_seal_is_enforced_at_the_run_entrance`(関数)
  - `test_undeclared_experiment_write_shows_in_stage_b`(関数): 負の対照: 系 experiment の宣言から X:experiment.* を外すと、段 B が宣言の外の書きとして見つける。
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.run`・`shibuya.engine.systems.overrides`・`shibuya.experiments.port.ensemble`・`shibuya.experiments.port.layer`・`shibuya.experiments.port.run_kind`・`shibuya.foundation.manifest.sections`・`shibuya.foundation.write_permit`・`shibuya.runtime.state.ledger`・`shibuya.runtime.state.ledger_ast`・`shibuya.runtime.systems.conductor`・`shibuya.runtime.systems.probe`・`shibuya.runtime.systems.table`・`tests/engine/experiment/_x33.py`
