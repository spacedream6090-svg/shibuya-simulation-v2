# tests/engine/decision

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 9 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../tests/engine/decision/__init__.py)

(冒頭の説明なし)

## [_j0.py](../../../../../../../tests/engine/decision/_j0.py)

第 1 期 1-8 J0 の試験の道具(候補の列・口の後ろの道の代役・腕の切り替え・小さなラン)。

- 公開の関数とクラス
  - `FakeBridge`(クラス): 口の後ろの今の道の代役: ``finish`` は決めた語を答え、``complete`` が渡されたらそれを呼んでから答える。
  - `FakeParse`(クラス)
  - `FakePolicy`(クラス): 古典の方策の代役(``complete_with_answer`` が答えの 5 つを返す)。
  - `FakeResult`(クラス)
  - `ctx_of`(関数)
  - `decision_arm`(関数): 腕を一時的に切り替える(試験の後は元に戻す)。
  - `vocab_candidates`(関数): 語彙の全語+よく考える(源は続ける・語彙の残り・よく考える)。
- import している内部モジュール: `shibuya.engine.llm_bridge`・`shibuya.foundation.ports.decision`・`shibuya.foundation.vocab.actions`・`shibuya.mind.judge.decision.layer`・`shibuya.mind.judge.decision.sources`
- 読む試験: `tests/engine/decision/test_j0_cause_columns.py`・`tests/engine/decision/test_j0_mock_equivalence.py`・`tests/engine/decision/test_j0_other_ratio_field.py`・`tests/engine/decision/test_j0_port_schema.py`・`tests/engine/decision/test_j0_shuffle_invariance.py`・`tests/engine/decision/test_j0_writes_declared.py`・`tests/engine/speech/test_speech_choice_utterance.py`・`tests/engine/time/test_v30a_key_sites.py`・`tests/engine/tools/test_c0_affordance_from_registry.py`

## [test_j0_cause_columns.py](../../../../../../../tests/engine/decision/test_j0_cause_columns.py)

第 1 期 1-8 J0(1-3 の検収 M2): 出来事の記録の原因の表を列(SoA)にした(受入の試験 ``test_j0_cause_columns``)。

- 公開の関数とクラス
  - `test_bytes_per_call_are_far_below_the_object_table`(関数): 1-3 の表(呼び出しごとの Python の物)は 198 B/呼(入力 0 個・HEAD の実測=記録の cause_bytes)。列は 37 B+倍化の余り。
  - `test_check_process_names_round_trip`(関数): 〔取り込み・検収 H1〕過程の原因の番号は ``Process`` の検査と同じ表 ``V.CAUSE_PROCESS_NAMES``(1-5 の ``rights`` を含む)
  - `test_column_widths`(関数)
  - `test_decision_events_carry_the_source_and_the_number`(関数): 検収 M1(口の約束 1-8 の約束 (3)): 腕 port の判断の出来事を読むと、選んだ候補の源と提示の番号が判断ごとに取れる。
  - `test_decision_events_carry_the_tape_call_id`(関数)
  - `test_eviction_keeps_every_live_cause_against_a_naive_copy`(関数)
  - `test_growth_declaration_adds_the_decision_events_only_on_the_port_arm`(関数): 検収 L2: 成長の宣言=腕 legacy は今のまま・腕 port は判断の出来事の行(出来事の行+原因の表の行)を足す。
  - `test_llm_call_source_and_number_are_checked`(関数)
  - `test_llm_call_still_validates`(関数)
  - `test_round_trip_of_the_three_kinds`(関数)
  - `test_same_cause_rows_are_merged`(関数)
- import している内部モジュール: `shibuya.engine.run`・`shibuya.foundation.journal.log`・`shibuya.foundation.ports.decision`・`shibuya.foundation.ports.experiment_gate`・`shibuya.foundation.time_consts`・`shibuya.foundation.vocab.events`・`shibuya.mind.judge.decision.layer`・`tests/engine/decision/_j0.py`

## [test_j0_cli.py](../../../../../../../tests/engine/decision/test_j0_cli.py)

第 1 期 1-8 J0: CLI ``--decision-port`` は指定したとき環境変数 ``SHIBUYA_DECISION_PORT`` より強い(1-3 の検収 L3・1-6 の L9 と同じ形)。

- 公開の関数とクラス
  - `test_cli_decision_port_beats_the_environment`(関数)
- 環境変数: `os.environ` をまるごと使う

## [test_j0_mock_equivalence.py](../../../../../../../tests/engine/decision/test_j0_mock_equivalence.py)

第 1 期 1-8 候補の口 J0: 腕 on/off の同値(口の約束 1-8 の約束 (1)(2)・受入の試験 ``test_j0_mock_equivalence``)。

- 公開の関数とクラス
  - `test_5000_agents_one_day_same_decision_sequence`(関数): 5,000 体 mock の 1 日(世界資産・語彙 v3=byte-check の w6_v3_default と同じ構成): 判断の番号列が一致。
  - `test_arm_on_off_same_final_tape_and_decision_sequence`(関数)
  - `test_legacy_arm_builds_no_layer_and_keeps_the_bridge_call`(関数)
  - `test_mock_port_ignores_the_presented_order`(関数)
  - `test_mock_port_picks_the_word_the_mock_writes`(関数)
  - `test_negative_control_shifting_the_mock_number_moves_the_final`(関数)
- import している内部モジュール: `shibuya.act.intake.parser`・`shibuya.cli`・`shibuya.engine.llm_bridge`・`shibuya.engine.run`・`shibuya.foundation.ports.decision`・`shibuya.foundation.vocab.actions`・`shibuya.llm`・`shibuya.llm.mock`・`shibuya.mind.judge.decision.layer`・`shibuya.mind.judge.decision.ports`・`tests/engine/decision/_j0.py`

## [test_j0_other_ratio_field.py](../../../../../../../tests/engine/decision/test_j0_other_ratio_field.py)

第 1 期 1-8 候補の口 J0: 「その他(自由記述)」の欄と割合の計器(C-2 の 3・受入の試験 ``test_j0_other_ratio_field``)。

- 公開の関数とクラス
  - `test_classical_port_answers_other_only_outside_the_candidates`(関数)
  - `test_default_other_share_is_unset_with_the_r108_basis`(関数)
  - `test_llm_port_puts_an_unmatched_answer_in_other`(関数)
  - `test_manifest_carries_the_ratio_field`(関数)
- import している内部モジュール: `shibuya.engine.run`・`shibuya.foundation.ports.decision`・`shibuya.mind.judge.decision.layer`・`shibuya.mind.judge.decision.ports`・`tests/engine/decision/_j0.py`
- 決定の ID: R-108

## [test_j0_port_schema.py](../../../../../../../tests/engine/decision/test_j0_port_schema.py)

第 1 期 1-8 候補の口 J0: 口の型と欄(口の約束 1-8 の受入の試験 ``test_j0_port_schema``)。

- 公開の関数とクラス
  - `test_candidate_fields_frozen_and_number_given_last`(関数)
  - `test_candidates_come_from_the_sources_and_keep_the_vocab`(関数)
  - `test_choice_fields_start_empty`(関数)
  - `test_choose_returns_the_original_id_and_the_presented_number`(関数)
  - `test_compose_short_and_long_share_the_common_head`(関数)
  - `test_context_puts_observation_and_prediction_side_by_side`(関数)
  - `test_no_literal_example_numbers_in_the_prompt_parts`(関数): DM4 の答え(数字はお金と時刻だけ)・R-97(例の数値を書かない): 提示と指示の文に数字の例を書かない。
  - `test_present_numbers_last_and_maps_back`(関数)
  - `test_sources_are_the_five_of_dm0_and_the_bridge_mark`(関数)
  - `test_surprise_words_and_hesitation`(関数)
  - `test_the_port_does_not_read_the_prediction`(関数): 口(と 3 つの実装)は予想の値を解釈しない: 予想を入れても同じ答え(驚くかは判断の側=10-03 §7)。
  - `test_three_implementations_share_one_entry`(関数)
- import している内部モジュール: `shibuya.engine.llm_bridge`・`shibuya.foundation.ports.decision`・`shibuya.foundation.ports.percept`・`shibuya.foundation.vocab.actions`・`shibuya.llm.mock`・`shibuya.mind.judge.decision.ports`・`shibuya.mind.judge.decision.sources`・`tests/engine/decision/_j0.py`
- 決定の ID: 10-03/§7・R-97

## [test_j0_shuffle_invariance.py](../../../../../../../tests/engine/decision/test_j0_shuffle_invariance.py)

第 1 期 1-8 候補の口 J0: 順のシャッフルと並べ替えの試験(C-2 の 1・受入の試験 ``test_j0_shuffle_invariance``)。

- 公開の関数とクラス
  - `test_every_permutation_of_a_small_set_keeps_the_mock_choice`(関数)
  - `test_k19_runtime_audit_on_the_port_arm`(関数): 乱数の流れの検査(K19・実行時): 腕 port で並べ替えの流れ(decision.present)は重ならず、mock の鍵の作り直しは
  - `test_permutation_test_spreads_the_position`(関数): 並べ替えの試験: 同じ問いを巡回のずらし全部で出し、選ばれた位置の分布を見る(内容は 1 つ・位置は 13 か所に散る)。
  - `test_reordering_the_candidates_keeps_the_choice`(関数)
  - `test_the_present_key_follows_agent_step_and_count`(関数)
- import している内部モジュール: `shibuya.engine.run`・`shibuya.foundation.ports.decision`・`shibuya.foundation.vocab.actions`・`shibuya.llm.mock`・`shibuya.mind.judge.decision.ports`・`shibuya.validation.static.rng_audit`・`tests/engine/decision/_j0.py`
- 決定の ID: R-108

## [test_j0_writes_declared.py](../../../../../../../tests/engine/decision/test_j0_writes_declared.py)

第 1 期 1-8 J0: 候補の口を書く系の宣言(口の約束の共通の約束「SYSTEMS の宣言に書き手を足す=段 B で宣言の外 0」)。

- 公開の関数とクラス
  - `test_declared_writes_cover_the_port_changes`(関数)
  - `test_dropping_the_events_path_fails_where_the_decision_event_is_written`(関数)
  - `test_dropping_the_j0_path_is_caught_by_stage_b`(関数)
- import している内部モジュール: `shibuya.engine.run`・`shibuya.foundation.write_permit`・`shibuya.runtime.systems.conductor`・`shibuya.runtime.systems.probe`・`shibuya.runtime.systems.table`・`shibuya.validation.static.system_overrides`・`tests/engine/decision/_j0.py`
