# tests/engine/calendar2

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 5 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../tests/engine/calendar2/__init__.py)

(冒頭の説明なし)

## [_ca2.py](../../../../../../../tests/engine/calendar2/_ca2.py)

第 6 期 6-2 カレンダー 2 の試験の共通(腕の切替・合成の台・決まった判断の規則・グループの一覧を入れる口)。

- 公開の関数とクラス
  - `Harness`(クラス): カレンダー 2 の層だけを回す合成の台(体 n・セル 9・対面の会話の器の代わり=開いている会話の番号の集合)。
  - `by_pref`(関数): 候補の語か id の好みの順で選ぶ規則(どれも無ければ (語・id) の順の最初の候補)。
  - `ca2`(関数): 腕 arm(と連絡の道具の腕 c1)を一時的に選ぶ(組み立てが読む)。
  - `choose`(関数): 仮のモデルの選びを試験の規則に差し替える(``rule(ctx, presented) -> 候補の id``)。
  - `groups_fixture`(関数): 合成の世界(母集団が無い=グループの一覧が無い)に、体 2 人ずつの家族と 10 人ずつの職場を入れる(宛先を作る)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.calendar2.layer`・`shibuya.engine.calendar2.port`・`shibuya.engine.tools.groups`・`shibuya.engine.tools.record`・`shibuya.foundation.arms.calendar2`・`shibuya.foundation.arms.contact`・`shibuya.foundation.journal.log`・`shibuya.foundation.time_consts`・`shibuya.world.state`
- 読む試験: `tests/engine/calendar2/test_ca2_runs.py`・`tests/engine/calendar2/test_ca2_units.py`・`tests/engine/calendar2/test_ca2_world.py`

## [test_ca2_runs.py](../../../../../../../tests/engine/calendar2/test_ca2_runs.py)

第 6 期 6-2 カレンダー 2 のランの試験: 既定 off は層を作らない・腕 arm の合成のラン(各自の行・出来事の記録の数が計器と合う・manifest の節と節の表・監査)・2 日と日の境目の再開=通し・腕を取り違えた再開は止まる・段 B(宣言の外 0)と負の対照・腕の行・CLI の引数とランの種類・AST の負の対照(エンジンが時刻と回数を決める直書きが無い・本人の語の原因は判断の呼びだけ・器は口だけで書く)。

- 公開の関数とクラス
  - `test_arm_rows_enter_the_hashes_only_when_the_owner_exists`(関数)
  - `test_arm_run_rows_events_and_manifest`(関数)
  - `test_ast_book_is_written_only_through_its_ports`(関数): 層は本人の予定の器の行を口(write・edit・observe・drop)だけで書く(行の欄への直の代入が無い)。
  - `test_ast_engine_does_not_decide_times`(関数)
  - `test_ast_negative_control_catches_a_backward_reminder`(関数)
  - `test_ast_negative_control_catches_planted_rules`(関数)
  - `test_ast_person_events_come_only_from_decisions`(関数)
  - `test_calls_by_model_has_the_calendar_2_breakdown`(関数): 〔問い 2〕calls_by_model に内訳 calendar_2(manifest と日次の記録)=C1 の M5 と同じ形。
  - `test_cli_flag_and_run_kind`(関数)
  - `test_default_off_builds_nothing`(関数): 〔検収 L6〕既定 off: 層・manifest の節・状態のファイルの calendar2.* の項・設定の指紋の鍵・約束の族の出来事が 0。
  - `test_event_log_on_off_does_not_change_the_arm_run`(関数)
  - `test_resuming_with_the_arm_off_stops`(関数)
  - `test_stage_b_has_no_undeclared_writes`(関数)
  - `test_stage_b_negative_control_without_the_turn_declaration_fails`(関数)
  - `test_system_declarations`(関数)
  - `test_two_days_and_resume_is_the_straight_run`(関数)
  - `with_groups`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.calendar2.layer`・`shibuya.engine.resume`・`shibuya.engine.run`・`shibuya.engine.run_kind`・`shibuya.engine.state_ledger`・`shibuya.engine.systems.table`・`shibuya.foundation.arms.calendar2`・`shibuya.foundation.journal.log`・`shibuya.foundation.manifest.sections`・`tests/engine/calendar2/_ca2.py`
- 環境変数: `SHIBUYA_SYSTEMS_CHECK`

## [test_ca2_units.py](../../../../../../../tests/engine/calendar2/test_ca2_units.py)

第 6 期 6-2 カレンダー 2 の単体の試験(合成の台=層だけ): 二人の約束は各自の行・変えられるのは自分の行だけ・変更は出来事の記録に 1 行・置き場所と確かさと元の会話の欄・壊れた予定だけ拒む・間に合わない/閉店中は記録だけ・アプリは重なりを警告する・頭の中の予定は記憶で思い出せたときだけ見える(思い出せない体には見えない負の対照・相手が居れば手がかり)・アラームは寝ていれば起きた後に見える・出来事がきっかけの実行意図・監査の負の対照・呼びの id の形。

- 公開の関数とクラス
  - `test_a_promise_becomes_each_own_row_with_fields`(関数)
  - `test_alarm_while_asleep_is_seen_after_waking`(関数)
  - `test_app_notification_then_depart_and_arrival_meters`(関数)
  - `test_app_warns_overlaps`(関数)
  - `test_arbitration_main_first_defers_the_look`(関数)
  - `test_audit_catches_forged_and_engine_causes`(関数)
  - `test_book_rows_are_each_own_and_only_the_owner_can_edit`(関数)
  - `test_broken_is_only_end_before_start_empty_place_or_no_start`(関数)
  - `test_broken_rows_are_rejected_and_only_the_app_tells`(関数)
  - `test_call_ids_do_not_collide_with_contact_and_parse_back`(関数)
  - `test_cancel_and_certainty_changes`(関数)
  - `test_change_after_the_notification_leaves_no_past_marks`(関数)
  - `test_change_candidates_safety_cap_counts_when_it_hits`(関数): 同じ時刻の行が上限より多いと、絞っても残る=安全装置(始まりの近い順に上限まで)に当たって数える。
  - `test_change_is_own_row_only_and_one_event`(関数)
  - `test_declined_offer_writes_no_rows`(関数)
  - `test_event_triggered_intention_cues_the_head_row`(関数)
  - `test_forgotten_head_row_is_not_offered_for_change`(関数): 思い出せない頭の中の行は「自分の約束を変える」の候補に出ない(取り消しも変更もできない)=負の対照。思い出せる刻みには出る。
  - `test_head_row_is_seen_only_when_recalled_negative_control`(関数): 頭の中の行は記憶で思い出せたときだけ見える。思い出せない刻みに考えても見えない(負の対照)・相手が同じ所に居れば手がかり。
  - `test_head_row_recalled_soon_after_writing_and_rehearsal`(関数)
  - `test_late_and_closed_are_only_recorded`(関数)
  - `test_many_change_candidates_are_narrowed_by_the_person`(関数): 〔検収 L4〕候補=見える行の全部。提示の番号の上限を超えると、本人が日 → 時刻で絞る(安全装置には当たらない)。
  - `test_offer_without_answer_lapses_when_the_conversation_ends`(関数)
  - `test_tentative_answer_gives_tentative_rows`(関数)
  - `test_the_proposer_chooses_own_certainty_not_the_engine`(関数): 〔検収 L1〕出した人の確かさは返事を聞いた本人が選ぶ(エンジンが返事から決めない)=相手が仮でも確定で書ける。
  - `test_time_change_moves_the_app_notification`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.calendar2.book`・`shibuya.engine.calendar2.layer`・`shibuya.engine.calendar2.port`・`shibuya.engine.contact.port`・`shibuya.foundation.journal.log`・`shibuya.foundation.time_consts`・`tests/engine/calendar2/_ca2.py`

## [test_ca2_world.py](../../../../../../../tests/engine/calendar2/test_ca2_world.py)

第 6 期 6-2 カレンダー 2 腕 arm(mock 5,000 体・1 日・世界の資産)の試験(slow・data が要る)。

- 公開の関数とクラス
  - `test_world_5000_one_day_records_meters_and_resume`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.calendar2.layer`・`tests/engine/calendar2/_ca2.py`
