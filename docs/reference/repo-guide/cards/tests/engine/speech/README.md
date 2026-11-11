# tests/engine/speech

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 14 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../tests/engine/speech/__init__.py)

(冒頭の説明なし)

## [_s8b.py](../../../../../../../tests/engine/speech/_s8b.py)

第 1 期 1-8b 発話の口の試験の道具(腕の切り替え・小さなラン・テープの B6 の読み出し)。

- 公開の関数とクラス
  - `run_small`(関数)
  - `speech_arm`(関数): 腕を一時的に切り替える(試験の後は元に戻す)。
  - `tape_rows`(関数): テープの呼の行(B6 の本文を ``b6`` に引いた形)。
- import している内部モジュール: `shibuya.engine.run`・`shibuya.society.speech.layer`
- 読む試験: `tests/engine/speech/test_s8_event_log_onoff.py`・`tests/engine/speech/test_speech_arm_rows_resume.py`・`tests/engine/speech/test_speech_cli.py`・`tests/engine/speech/test_speech_default_off_invariance.py`・`tests/engine/speech/test_speech_modality_field_empty.py`・`tests/engine/speech/test_speech_on_reaches_addressee.py`・`tests/engine/speech/test_speech_writes_declared.py`

## [test_s8_event_log_onoff.py](../../../../../../../tests/engine/speech/test_s8_event_log_onoff.py)

第 1 期 1-8b 発話の口(腕 ``--speech-port on``)の直し=口の約束 1-3 の (1)「出来事の記録の on/off で結果が変わらない」。

- 公開の関数とクラス
  - `on_off`(関数)
  - `test_event_log_on_off_does_not_change_the_s8_arm_run`(関数)
  - `test_negative_control_log_ids_in_the_inbox_break_the_on_off_equality`(関数): 負の対照: 未読の列の目印を記録の id に戻す(直す前の形)と記録 on/off で behavior-hash が違う。
  - `test_resume_restores_the_mark_table`(関数): 発話の直後(未読が残る刻み)で止めた再開=通し・再開した後の発話の行と原因が通しと同じ(診断の表が戻る)。
  - `test_speech_causes_point_at_logged_utterances`(関数): 発話の原因の入力の出来事 id は記録にある発話の行(診断の表から引いた)=聞こえた発話。
  - `test_unit_marks_are_log_independent_and_the_table_is_bounded`(関数)
- import している内部モジュール: `shibuya.foundation.journal.log`・`shibuya.society.speech.port`・`tests/engine/speech/_s8b.py`

## [test_speech_arm_rows_resume.py](../../../../../../../tests/engine/speech/test_speech_arm_rows_resume.py)

第 1 期 1-8b 発話の口: 腕の行(状態台帳 ``S8``=未読の列)が腕 on のランの再開で戻る(``LedgerRow.arm``・``arm_items``)。

- 公開の関数とクラス
  - `straight`(関数)
  - `test_resume_right_after_an_utterance_gives_the_straight_result`(関数)
  - `test_resuming_with_the_other_arm_stops`(関数)
  - `test_the_unread_queue_moves_both_hashes_only_when_the_arm_is_on`(関数)
- import している内部モジュール: `shibuya.runtime.state.hashes`・`shibuya.runtime.state.ledger`・`shibuya.runtime.state.resume`・`shibuya.society.speech.port`・`tests/engine/speech/_s8b.py`

## [test_speech_choice_utterance.py](../../../../../../../tests/engine/speech/test_speech_choice_utterance.py)

第 1 期 1-8b: 1-8 の予約の欄 ``Choice.utterance`` が埋まる側(検収 低6・口の約束 1-8 の約束 (4))。

- 公開の関数とクラス
  - `test_a_conversation_turn_with_a_comment_fills_the_field`(関数)
  - `test_otherwise_the_field_stays_empty`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.foundation.vocab.actions`・`shibuya.llm.mock`・`shibuya.mind.judge.decision.ports`・`tests/engine/decision/_j0.py`

## [test_speech_cli.py](../../../../../../../tests/engine/speech/test_speech_cli.py)

第 1 期 1-8b 発話の口: CLI ``--speech-port`` と腕の扱い(1-8 J0 の ``--decision-port`` と同じ形)。

- 公開の関数とクラス
  - `test_cli_speech_port_beats_the_environment`(関数)
  - `test_the_on_arm_is_an_arm_run`(関数): ランの種類(試験の外): 既定 off の既定の構成=再現・腕 on=腕(指紋の on の欄は ``test_speech_arm_rows_resume`` と
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.run_kind`・`tests/engine/speech/_s8b.py`
- 環境変数: `os.environ` をまるごと使う

## [test_speech_default_off_invariance.py](../../../../../../../tests/engine/speech/test_speech_default_off_invariance.py)

第 1 期 1-8b 発話の口: 既定 off で結果不変(口の約束 1-8b の約束 (1)(5)・受入の試験 ``test_speech_default_off_invariance``)。

- 公開の関数とクラス
  - `test_an_off_run_has_no_port_no_lines_and_no_arm_rows`(関数)
  - `test_byte_check_19_configurations_are_unchanged_with_the_default_arm`(関数)
  - `test_classical_text_is_unchanged_without_the_field_line`(関数)
  - `test_default_arm_is_off`(関数)
  - `test_mock_text_is_unchanged_without_the_field_line`(関数)
  - `test_off_state_files_and_fingerprint_have_no_speech_paths`(関数)
- import している内部モジュール: `shibuya.foundation.time_consts`・`shibuya.foundation.vocab.actions`・`shibuya.llm`・`shibuya.llm.mock`・`shibuya.mind.judge.classical`・`shibuya.runtime.state.ledger`・`shibuya.runtime.state.resume`・`shibuya.society.speech.layer`・`tests/engine/speech/_s8b.py`

## [test_speech_empty_text_errors.py](../../../../../../../tests/engine/speech/test_speech_empty_text_errors.py)

第 1 期 1-8b 発話の口: 本文の無い発話はエラー(口の約束 1-8b の約束 (3)・受入の試験 ``test_speech_empty_text_errors``)。

- 公開の関数とクラス
  - `test_a_real_turn_reaches_the_port_once`(関数)
  - `test_an_invitee_reply_reaches_the_inviter`(関数): 親の判断 A2: 返事待ちの招待への返事(セッションはまだ無い)は招待した人に届く(``to_inviter``)。空の返事は数えるだけ。
  - `test_silent_turns_do_not_reach_the_port`(関数)
  - `test_text_is_stripped`(関数)
  - `test_turns_outside_a_session_do_not_reach_the_port`(関数): セッションも返事待ちの招待も無い番は口を通さない(``no_session``)。
  - `test_utterance_without_text_is_an_error`(関数)
- import している内部モジュール: `shibuya.foundation.journal.log`・`shibuya.society.conversation`・`shibuya.society.speech.layer`・`shibuya.society.speech.port`

## [test_speech_modality_field_empty.py](../../../../../../../tests/engine/speech/test_speech_modality_field_empty.py)

第 1 期 1-8b 発話の口: 将来の音声・表情(VRM)の欄 ``modality`` は空(受入の試験 ``test_speech_modality_field_empty``)。

- 公開の関数とクラス
  - `test_a_value_is_refused_until_a_stage_adds_it`(関数)
  - `test_in_a_run_every_said_utterance_has_an_empty_modality`(関数)
  - `test_said_utterances_keep_the_field_empty`(関数)
  - `test_the_field_exists_and_starts_empty`(関数)
- import している内部モジュール: `shibuya.foundation.journal.log`・`shibuya.society.speech.port`・`tests/engine/speech/_s8b.py`
- 決定の ID: 10-13b/§1

## [test_speech_on_reaches_addressee.py](../../../../../../../tests/engine/speech/test_speech_on_reaches_addressee.py)

第 1 期 1-8b 発話の口: 腕 on で本文が口を通って出来事ログに 1 回だけ書かれ、相手の次の入力に載る(口の約束 1-8b の約束 (2)・(4)・受入の試験 ``test_speech_on_reaches_addressee``)。試験では毎回 on で通す(slow にしない)。

- 公開の関数とクラス
  - `pair`(関数)
  - `test_all_addressees_hear_and_whom_is_the_first`(関数)
  - `test_an_all_imperative_utterance_puts_no_line`(関数): 検収 低4: 全部が命令文の発話は本文の空の行を載せず、口の計器 ``all_imperative`` に数える。
  - `test_conversation_chains_carry_the_heard_ids_as_the_cause`(関数)
  - `test_each_utterance_reaches_the_addressees_next_input`(関数)
  - `test_heard_line_and_field_line_at_the_end_of_b6`(関数)
  - `test_invitee_replies_reach_the_inviter`(関数): 親の判断 A2: 被招待の返事の ひと言 は招待した人に届く(返事待ちの招待=セッションの招待の段階)。
  - `test_mock_behaviour_is_the_same_as_off_except_the_field`(関数)
  - `test_no_field_line_on_v1_and_nothing_without_the_hook`(関数)
  - `test_only_conversation_turns_get_the_field_and_the_shared_prefix_is_unchanged`(関数)
  - `test_said_equals_the_logged_rows_and_the_word_of_mouth`(関数)
  - `test_say_writes_one_event_and_queues_for_the_next_input`(関数)
  - `test_signage_table_is_unchanged`(関数): 看板・広告の表は変えない(既定の描画のバイトは不変): て形の依頼は看板の表では落ちない。
  - `test_speech_lines_are_dropped_when_the_individual_budget_is_exceeded`(関数): 検収 低2: B5(意図の行・記憶の行を含む)は発話の行の無い B6 で先に組み、発話の行は残りに入るときだけ足す。
  - `test_speech_only_imperatives_are_dropped`(関数)
  - `test_the_classical_policy_speaks_through_the_same_port`(関数): 古典の方策(G)も同じ口: 出力の欄の指示がある会話の番だけ決まった文の ひと言 を足し(方策の答え・乱数は同じ)、
  - `test_the_field_line_is_short`(関数): 親の判断 A6: 指示の行は 10 tok 以下(描画の数え方=文字数 ÷ 2)・届いた発話の行の素性タグも短い形。
  - `test_the_queue_is_bounded_and_overflow_is_counted`(関数)
  - `test_the_window_holds_only_after_the_session_closed`(関数): 親の判断 A7 と第 2 回: 開いているセッションの未読と返事待ちの招待への返事(セッションの外)は窓なし(届け先の次の
- import している内部モジュール: `shibuya.act.intake.parser`・`shibuya.agents.state`・`shibuya.foundation.journal.log`・`shibuya.foundation.text.channels`・`shibuya.foundation.text.templates`・`shibuya.foundation.vocab.actions`・`shibuya.llm`・`shibuya.llm.mock`・`shibuya.mind.judge.classical`・`shibuya.perception.attention`・`shibuya.perception.renderer`・`shibuya.society.speech.layer`・`shibuya.society.speech.port`・`shibuya.world.model.state`・`tests/engine/speech/_s8b.py`・`tests/perception/facts/scenes.py`

## [test_speech_port_schema.py](../../../../../../../tests/engine/speech/test_speech_port_schema.py)

第 1 期 1-8b 発話の口: 口の型(口の約束 1-8b の「口」・受入の試験 ``test_speech_port_schema``)。

- 公開の関数とクラス
  - `test_arm_is_off_by_default_and_checked`(関数)
  - `test_context_and_the_one_writing_port`(関数)
  - `test_ledger_arm_rows_and_arm_items`(関数)
  - `test_manifest_fields_shape`(関数)
  - `test_mora_count_is_the_declared_kana_approximation`(関数)
  - `test_the_field_line_is_the_same_text_in_llm_and_perception`(関数)
  - `test_the_word_is_appended_to_the_1_3_vocabulary`(関数)
  - `test_utterance_fields_frozen_and_mora_from_the_text`(関数)
  - `test_utterance_rejects_bad_fields`(関数)
  - `test_via_is_the_1_3_vocabulary_and_three_participants_are_allowed`(関数)
- import している内部モジュール: `shibuya.foundation.journal.log`・`shibuya.foundation.vocab.actions`・`shibuya.foundation.vocab.events`・`shibuya.perception.renderer`・`shibuya.runtime.state.ledger`・`shibuya.society.speech.layer`・`shibuya.society.speech.port`

## [test_speech_writers_ast.py](../../../../../../../tests/engine/speech/test_speech_writers_ast.py)

第 1 期 1-8b 発話の口: 未読の列と計器を書くのは口だけ(検収 低3・静的な検査)。

- 公開の関数とクラス
  - `test_negative_control_planted_writes_are_found`(関数)
  - `test_only_the_port_writes_the_queue_and_the_meter`(関数)
  - `test_the_port_itself_has_writes_that_the_scan_sees`(関数)
- import している内部モジュール: `tests/engine/ast_writers.py`

## [test_speech_writes_declared.py](../../../../../../../tests/engine/speech/test_speech_writes_declared.py)

第 1 期 1-8b 発話の口: 口を書く系の宣言(口の約束の共通の約束「SYSTEMS の宣言に書き手を足す=段 B で宣言の外 0」)。

- 公開の関数とクラス
  - `test_declared_writes_cover_the_port_changes`(関数)
  - `test_dropping_the_events_path_fails_where_the_utterance_is_written`(関数)
  - `test_dropping_the_s8_path_is_caught_by_stage_b`(関数)
  - `test_the_writing_systems_are_declared`(関数)
- import している内部モジュール: `shibuya.engine.run`・`shibuya.engine.systems.overrides`・`shibuya.foundation.write_permit`・`shibuya.runtime.systems.conductor`・`shibuya.runtime.systems.probe`・`shibuya.runtime.systems.table`・`tests/engine/speech/_s8b.py`

## [test_wom_from_utterance_roundtrip.py](../../../../../../../tests/engine/speech/test_wom_from_utterance_roundtrip.py)

第 1 期 1-8b 発話の口: 口コミの抽出が語彙 v3 でも動く(口の約束 1-8b の (c)・受入の試験 ``test_wom_from_utterance_roundtrip``)。

- 公開の関数とクラス
  - `test_legacy_path_and_the_port_write_the_same_word_of_mouth`(関数)
  - `test_the_mock_utterance_extracts_nothing`(関数)
  - `test_the_v3_parser_receives_the_comment_without_code_changes`(関数)
- import している内部モジュール: `shibuya.act.intake.parser`・`shibuya.agents.state`・`shibuya.foundation.journal.log`・`shibuya.foundation.vocab.actions`・`shibuya.llm.mock`・`shibuya.mind.memory.memory`・`shibuya.mind.memory.store_memory`・`shibuya.mind.memory.wom`・`shibuya.runtime.systems.llm_io`・`shibuya.society.conversation`・`shibuya.society.speech.layer`
