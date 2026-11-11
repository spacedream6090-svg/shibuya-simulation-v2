# tests/engine/events

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 8 本・その他 2 本(このディレクトリの直下)

その他のファイル: `manifest_events_keys_frozen.json`・`writes_paths_events.json`

## [__init__.py](../../../../../../../tests/engine/events/__init__.py)

(冒頭の説明なし)

## [test_e_cause_three_kinds.py](../../../../../../../tests/engine/events/test_e_cause_three_kinds.py)

第 1 期 1-3 出来事の記録: 原因は 3 種類だけ・実験の条件の口は 1 か所(CP12)。口の約束 1-3 の受入の試験``test_e_cause_three_kinds``。

- 公開の関数とクラス
  - `offenders`(関数): ``rel`` で型 ``Experiment`` を作れる形(参照・import・文字列の名・記録の置き場の動的な取り出し)。
  - `test_a_fake_cause_is_rejected_by_the_event_and_the_log`(関数)
  - `test_a_fourth_cause_type_cannot_be_defined`(関数)
  - `test_append_checks_the_gate_for_experiment_causes_reuse`(関数): 読み戻した実験の原因を、口の外で別の出来事に付けて書くと落ちる(使い回し)。
  - `test_append_gate_check_stays_on_when_the_write_guard_is_off`(関数)
  - `test_append_rejects_a_forged_experiment_made_without_init`(関数): ``object.__new__`` と ``type(e).__new__`` で ``__init__`` を飛ばした偽物も、書くときに落ちる。
  - `test_gate_is_the_one_way_in`(関数): 正の対照: 口を通せば実験の条件の原因で 1 行書ける。
  - `test_no_module_outside_the_gate_names_the_experiment_type`(関数)
  - `test_runtime_alias`(関数)
  - `test_runtime_check_stays_on_when_the_write_guard_is_off`(関数)
  - `test_runtime_direct`(関数)
  - `test_runtime_getattr`(関数)
  - `test_runtime_other_ways`(関数)
  - `test_static_check_catches_every_planted_form`(関数)
  - `test_the_allowed_places_do_name_the_type`(関数): 正の対照(静的): 許した 2 か所は実際に型の名を書いている(許しの表が空回りしていない)。
  - `test_three_kinds_only`(関数)
- import している内部モジュール: `shibuya.foundation.journal.log`・`shibuya.foundation.ports.experiment_gate`・`shibuya.foundation.write_permit`
- 決定の ID: 第 334

## [test_e_log_invariance.py](../../../../../../../tests/engine/events/test_e_log_invariance.py)

第 1 期 1-3 出来事の記録: 記録の有無で結果が変わらない(口の約束 1-3 の約束 (1)・受入の試験 ``test_e_log_invariance``)。

- 公開の関数とクラス
  - `test_nineteen_configs_on_and_off_give_the_same_final`(関数)
  - `test_on_and_off_give_the_same_results`(関数)
  - `test_two_days_and_state_files_are_the_same`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.run`・`shibuya.foundation.journal.log`・`shibuya.foundation.time_consts`

## [test_e_log_links_actual.py](../../../../../../../tests/engine/events/test_e_log_links_actual.py)

第 1 期 1-3 出来事の記録: ActualLog の行と出来事が 1 対 1 に目印で結ばれる(口の約束 1-3 の約束 (2)・受入の試験``test_e_log_links_actual``)。1-3 で配線した系(世界過程=world・最後の便=close_final)の分。

- 公開の関数とクラス
  - `test_real_world_run_links_every_actual_log_row`(関数)
  - `test_run_links_every_actual_log_row`(関数)
  - `test_unit_append_and_append_many_link_one_to_one`(関数)
  - `test_unit_eviction_keeps_the_links_on_their_rows`(関数)
  - `test_unit_no_sink_or_disabled_means_no_mark`(関数)
  - `test_unit_unknown_process_id_is_an_error`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.run`・`shibuya.foundation.journal.links`・`shibuya.foundation.journal.log`・`shibuya.foundation.time_consts`・`shibuya.world.laws.runner`・`shibuya.world.ledger.actual_log`・`shibuya.world.ledger.records`

## [test_e_log_schema.py](../../../../../../../tests/engine/events/test_e_log_schema.py)

第 1 期 1-3 出来事の記録: ``Event`` の欄・凍結・id の決定性(口の約束 1-3 の受入の試験 ``test_e_log_schema``)。

- 公開の関数とクラス
  - `test_close_day_counts_and_retention`(関数)
  - `test_disabled_log_writes_nothing`(関数)
  - `test_event_is_frozen_and_slotted`(関数)
  - `test_fields_follow_the_contract`(関数)
  - `test_ids_are_time_and_sequence`(関数)
  - `test_invalid_fields_are_rejected`(関数)
  - `test_numpy_integers_are_normalized`(関数)
  - `test_resume_at_a_step_boundary_gives_the_same_ids`(関数)
  - `test_round_trip_of_every_field`(関数)
  - `test_row_bytes_and_growth_declaration`(関数): 1 行のバイト(列の型の和)と D-R2-6 の 5 欄の宣言(1-3 の見込み=expedient・ランの成長の報告にはまだ載せない)。
  - `test_same_run_gives_the_same_ids`(関数)
  - `test_writer_cannot_set_the_id_or_write_into_the_past`(関数)
- import している内部モジュール: `shibuya.engine.run`・`shibuya.foundation.journal.log`・`shibuya.foundation.time_consts`・`shibuya.foundation.vocab.events`

## [test_e_manifest_events.py](../../../../../../../tests/engine/events/test_e_manifest_events.py)

第 1 期 1-3 出来事の記録: 1 日の記録の行数と種類の分布を manifest に出す(口の約束 1-3 の約束 (3)・計器)。

- 公開の関数とクラス
  - `test_daily_counts_add_up`(関数)
  - `test_daily_records_end_with_the_events_field`(関数)
  - `test_top_level_keys_are_unchanged`(関数)
  - `two_days`(関数)
- import している内部モジュール: `shibuya.engine.run`・`shibuya.foundation.journal.log`・`shibuya.foundation.manifest.sections`・`shibuya.foundation.time_consts`

## [test_e_vocab_is_closed.py](../../../../../../../tests/engine/events/test_e_vocab_is_closed.py)

第 1 期 1-3 出来事の記録: ``what`` の語彙表は閉じている(表の外はエラー)・4 つの族の写しが元の表と同じ。

- 公開の関数とクラス
  - `test_every_word_of_the_table_is_accepted`(関数)
  - `test_families_are_copies_of_their_sources`(関数)
  - `test_process_names_are_closed`(関数)
  - `test_via_and_where_are_closed`(関数)
  - `test_vocab_size_and_uniqueness`(関数)
  - `test_what_outside_the_table_is_an_error`(関数)
  - `test_word_helper_and_family`(関数)
- import している内部モジュール: `shibuya.economy.accounts`・`shibuya.economy.goods`・`shibuya.foundation.journal.log`・`shibuya.foundation.vocab.actions`・`shibuya.foundation.vocab.events`・`shibuya.world.laws.runner`
- 決定の ID: 10-13b/§3

## [test_e_writes_declared.py](../../../../../../../tests/engine/events/test_e_writes_declared.py)

第 1 期 1-3 出来事の記録: 書き口は系の宣言 ``writes.paths`` の ``E:events.*`` に載り、宣言の外の書きは落ちる(口の約束 1-3 の約束 (4))。

- 公開の関数とクラス
  - `test_declared_writes_cover_the_event_changes`(関数)
  - `test_declaring_systems_match_the_frozen_list`(関数)
  - `test_events_write_allowed_reads_the_paths_permit`(関数)
  - `test_paths_permit_is_assigned_only_in_the_guard`(関数)
  - `test_undeclared_write_fails_at_run_time`(関数)
  - `test_undeclared_write_shows_in_stage_b`(関数)
- import している内部モジュール: `shibuya.engine.run`・`shibuya.foundation.write_guard`・`shibuya.foundation.write_permit`・`shibuya.runtime.state.ledger`・`shibuya.runtime.systems.conductor`・`shibuya.runtime.systems.probe`・`shibuya.runtime.systems.table`・`shibuya.validation.static.system_overrides`
