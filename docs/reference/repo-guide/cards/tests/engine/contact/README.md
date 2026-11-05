# tests/engine/contact

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 14 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../tests/engine/contact/__init__.py)

(冒頭の説明なし)

## [_c1.py](../../../../../../../tests/engine/contact/_c1.py)

第 6 期 6-4 C1 の試験の共通(腕の切替・合成の層・決まった判断の仮のモデル)。

- 公開の関数とクラス
  - `Harness`(クラス): 連絡の層だけを回す合成の台(体 6・セル 9・家族 2 組と職場 1 つ・待ち行列つき)。
  - `by_kind`(関数): 候補の語の好みの順で選ぶ規則(どれも無ければ最初の候補)。
  - `c1`(関数): 腕 c1(と下の腕)を一時的に選ぶ(組み立てが読む)。
  - `choose`(関数): 仮のモデルの選びを試験の規則に差し替える(``rule(ctx, presented) -> 候補の id``)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.core.time_consts`・`shibuya.engine.batching`・`shibuya.engine.contact.arm`・`shibuya.engine.contact.layer`・`shibuya.engine.contact.port`・`shibuya.engine.events.log`・`shibuya.engine.tools.groups`・`shibuya.world.state`
- 読む試験: `tests/engine/contact/_c2.py`・`tests/engine/contact/test_c1_event_log_onoff.py`・`tests/engine/contact/test_c1_fixes.py`・`tests/engine/contact/test_c1_flow.py`・`tests/engine/contact/test_c1_runs.py`・`tests/engine/contact/test_c1_units.py`・`tests/engine/contact/test_c1_world.py`・`tests/engine/contact/test_c2_charge.py`・`tests/engine/contact/test_c2_exchange.py`・`tests/engine/contact/test_c2_habit.py`・`tests/engine/contact/test_c2_runs.py`・`tests/engine/contact/test_c2_video.py`

## [_c2.py](../../../../../../../tests/engine/contact/_c2.py)

第 6 期 6-4 C2(連絡の道具の残り)の試験の共通: 家・勤め先・習慣の腕・店の番号の表を渡せる合成の台。

- 公開の関数とクラス
  - `Harness2`(クラス): 連絡の層だけを回す合成の台(体 6・セル 9・家族 2 組と職場 1 つ・待ち行列つき)+家(``home_cell``)・勤め先・習慣の腕・
  - `habit_arm`(関数)
  - `loud`(関数): 全員の電話を手に持ち・音あり・イヤホンなし(気づく道を決める)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.core.time_consts`・`shibuya.engine.batching`・`shibuya.engine.contact.arm`・`shibuya.engine.contact.device`・`shibuya.engine.contact.layer`・`shibuya.engine.events.log`・`shibuya.engine.tools.groups`・`shibuya.world.state`・`tests/engine/contact/_c1.py`
- 読む試験: `tests/engine/contact/test_c2_charge.py`・`tests/engine/contact/test_c2_exchange.py`・`tests/engine/contact/test_c2_habit.py`・`tests/engine/contact/test_c2_runs.py`・`tests/engine/contact/test_c2_video.py`・`tests/engine/time/test_v30a_key_sites.py`

## [test_c1_event_log_onoff.py](../../../../../../../tests/engine/contact/test_c1_event_log_onoff.py)

第 6 期 6-4 C1 の直し=口の約束 1-3 の (1)「出来事の記録の on/off で結果が変わらない」(カレンダー 2 の検収 M3 と同じ形)。

- 公開の関数とクラス
  - `test_call_speech_inbox_holds_only_log_independent_marks`(関数): 通話の発話の口(発話の口の子)の未読の列は記録 on/off で同じ(口の目印)・記録の id は診断の表・引いたら落ちる。
  - `test_event_log_on_off_does_not_change_the_c1_arm_run`(関数): 合成 80 体・720 刻み・腕 c1(メッセージとグループの道): 記録 on/off で final と checkpoint の behavior-hash が同じ。
  - `test_event_log_on_off_does_not_change_the_c1_arm_run_with_calls`(関数): 通話を起こす合成のラン: 通話の発話の未読の列は口の目印だけ・記録 on/off で同じ・番の原因の入力は発話の行。
  - `test_negative_control_eid_in_the_behavior_row_breaks_the_on_off_equality`(関数): 負の対照: 届いた行に出来事の id を戻すと(直す前の形)記録 on/off で behavior-hash が違う。
  - `test_resume_restores_the_event_id_tables`(関数): 日の途中の再開で診断の表が戻る=再開した後の連絡の行と原因(入力の出来事 id を含む)が通しと同じ。
  - `with_groups`(関数)
- import している内部モジュール: `shibuya.engine.contact.calls`・`shibuya.engine.contact.layer`・`shibuya.engine.contact.port`・`shibuya.engine.events.log`・`shibuya.engine.run`・`shibuya.engine.speech.port`・`shibuya.engine.tools.groups`・`shibuya.engine.tools.record`・`tests/engine/contact/_c1.py`

## [test_c1_fixes.py](../../../../../../../tests/engine/contact/test_c1_fixes.py)

第 6 期 6-4 C1 の独立検収の直しの試験(H1・M1・M2・M4・M5・L8)。

- 公開の関数とクラス
  - `port_arm`(関数)
  - `test_contact_ctx_does_not_use_the_wake_class_field`(関数): 〔検収 L5〕連絡の判断の文脈の wake_class は使わない(−1)・乱数の鍵は call_id の通し番号。
  - `test_h1_arm_c1_passes_stage_b`(関数)
  - `test_h1_negative_control_without_the_bw_declaration_fails`(関数)
  - `test_l8_resume_in_the_middle_of_a_call_is_the_straight_run`(関数)
  - `test_m1_gate_is_kept_on_the_contact_side`(関数)
  - `test_m2_a_forged_llm_call_is_caught_by_the_issued_check`(関数)
  - `test_m2_ast_negative_control_catches_a_planted_rule`(関数)
  - `test_m2_ast_person_events_come_only_from_decisions`(関数)
  - `test_m4_focus_is_the_value_after_the_decisions`(関数)
  - `test_m5_arbitration_main_decision_first`(関数): 同じ刻みに主の判断の呼びがある体は、連絡の通知の判断を次の刻みに回す(仲裁)。
  - `test_m5_calls_by_model_is_unchanged_without_the_arm`(関数)
  - `test_m5_look_is_a_main_candidate_and_counts`(関数): 腕 port: 暇なときの「スマホを見る」は主の判断の候補(選ぶと同じ刻みに画面を見る)・別の暇の判断はしない・段 B も通る。
  - `with_groups`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.contact.attention`・`shibuya.engine.contact.layer`・`shibuya.engine.contact.port`・`shibuya.engine.conversation`・`shibuya.engine.decision.layer`・`shibuya.engine.decision.port`・`shibuya.engine.decision.ports`・`shibuya.engine.events.log`・`shibuya.engine.run`・`shibuya.engine.systems.table`・`shibuya.engine.tools.groups`・`shibuya.engine.tools.record`・`tests/engine/contact/_c1.py`
- 環境変数: `SHIBUYA_SYSTEMS_CHECK`

## [test_c1_flow.py](../../../../../../../tests/engine/contact/test_c1_flow.py)

第 6 期 6-4 C1 合成の流れ(連絡の層と進行役の待ち行列だけを回す台): 届く(送った時刻)・打ち終わりと着信は窓の境目・気づく/読む/返すは本人の判断・既読・チャットの状態・電話(対面の会話の仕組み)・範囲の外の人・送る文の腕 (c)・長さの上限。

- 公開の関数とクラス
  - `test_call_hits_the_safety_limit_of_turns`(関数)
  - `test_call_uses_the_conversation_mechanism_and_hang_up_is_the_person`(関数)
  - `test_device_off_holds_messages_and_rings_are_unreachable`(関数)
  - `test_group_message_and_chat_state`(関数)
  - `test_length_cap_is_recorded_in_the_layer`(関数)
  - `test_message_is_typed_until_the_boundary_and_delivered_at_send_time`(関数)
  - `test_negative_control_an_engine_rule_for_reading_is_caught`(関数): 負の対照: 判断の口を通さずに読む(エンジンが時刻を決める)形に差し替えると、監査が食い違いを数える。
  - `test_negative_control_ring_inside_the_window_fails_the_boundary_check`(関数): 負の対照: 着信の種類を窓の中で届ける(IN_WINDOW)にすると、かけた時刻と同じ時刻に鳴る=境目の確かめが落ちる。
  - `test_notice_gate_by_strength_and_focus`(関数)
  - `test_outside_person_replies_and_carries_the_origin_mark`(関数)
  - `test_pending_rows_are_rescheduled_at_the_boundary_after_a_rebind`(関数): 再開の形: 予約の表に残った送信を新しい待ち行列に結び直すと、境目の時刻で届く(通しと同じ時刻)。
  - `test_ring_arrives_at_the_window_boundary`(関数)
  - `test_screen_end_records_minutes_and_sleep_closes_the_screen`(関数)
  - `test_send_arm_c_sends_the_choice_words`(関数)
- import している内部モジュール: `shibuya.engine.batching`・`shibuya.engine.contact.attention`・`shibuya.engine.contact.deliver`・`shibuya.engine.contact.device`・`shibuya.engine.contact.layer`・`shibuya.engine.contact.port`・`shibuya.engine.conversation`・`shibuya.engine.events.log`・`tests/engine/contact/_c1.py`

## [test_c1_runs.py](../../../../../../../tests/engine/contact/test_c1_runs.py)

第 6 期 6-4 C1 ランの試験: 既定 off は何も作らない・腕 c1 の合成のラン(manifest の節・節の表・監査・描画の計数)・2 日の再開=通し(届いた箱・チャット・通話の状態を含む)・腕を取り違えた再開は止まる・ランの種類。

- 公開の関数とクラス
  - `test_arm_rows_enter_the_hashes_only_when_the_owner_exists`(関数)
  - `test_c1_synthetic_run_manifest_audit_and_sections`(関数)
  - `test_c1_two_days_resume_is_the_straight_run`(関数)
  - `test_cli_flag_sets_the_arm`(関数): CLI の ``--contact`` は環境変数より強い(組み立てが読む切替口を置く)。
  - `test_cli_run_kind_is_arm`(関数)
  - `test_default_off_builds_nothing`(関数)
  - `test_resuming_with_the_arm_off_stops`(関数)
  - `test_the_contact_system_runs_only_on_the_arm`(関数)
  - `with_groups`(関数): 合成の世界(母集団が無い=グループの一覧が無い)に、体 2 人ずつの家族と 10 人ずつの職場を入れる(宛先を作る)。
- import している内部モジュール: `shibuya.cli`・`shibuya.core.time_consts`・`shibuya.engine.contact.arm`・`shibuya.engine.contact.layer`・`shibuya.engine.manifest_sections`・`shibuya.engine.resume`・`shibuya.engine.run`・`shibuya.engine.run_kind`・`shibuya.engine.state_ledger`・`shibuya.engine.systems.conductor`・`shibuya.engine.systems.table`・`shibuya.engine.tools.groups`・`shibuya.engine.tools.record`・`tests/engine/contact/_c1.py`

## [test_c1_units.py](../../../../../../../tests/engine/contact/test_c1_units.py)

第 6 期 6-4 C1 合成の単体: 道具の状態と刺激・周辺視の形・割り込めなかった出来事の腕・チャットの状態・既読・宛先・長さの上限・体の無い人・判断の口・負の対照の監査・腕の切替。

- 公開の関数とクラス
  - `test_an_interrupt_lets_the_event_through`(関数)
  - `test_arms_and_config`(関数)
  - `test_attention_sync_orders_call_screen_talk`(関数)
  - `test_audit_catches_engine_decided_reads_and_sends`(関数)
  - `test_battery_drains_by_use_and_turns_the_device_off`(関数)
  - `test_chat_safety_cap_closes_and_counts`(関数)
  - `test_chat_state_transitions_like_a_conversation`(関数)
  - `test_contact_port_is_keyed_and_shuffle_invariant`(関数)
  - `test_contacts_from_groups_family_only_and_groups_of`(関数)
  - `test_contacts_from_relation_flags_and_bodiless_are_dropped`(関数)
  - `test_decision_serials_do_not_collide_and_have_a_limit`(関数): 〔検収 L5〕通し番号=k × 16+種類=257 回を超えてもぶつからない・上限で止まる・表は書き換えられない。
  - `test_gate_salient_removes_only_focused_and_not_interrupted`(関数)
  - `test_initial_device_state_comes_from_the_population_seed`(関数)
  - `test_length_cap_is_only_a_safety_device`(関数)
  - `test_manner_mode_and_bag_make_the_notice_weaker`(関数)
  - `test_negative_control_front_gaze_keeps_the_facts`(関数)
  - `test_people_hint_words_are_coarse`(関数)
  - `test_peripheral_vision_coarsens_the_percept_by_shape`(関数)
  - `test_read_marks_reach_the_sender_and_prune_is_bounded`(関数)
  - `test_screen_is_strong_and_an_off_device_gets_nothing`(関数)
  - `test_the_levels_are_a_shape_not_a_coefficient`(関数): 負の対照: 同じ状態からはいつも同じ段(確率を引かない)・段は SNR の閾値でだけ変わる。
  - `test_unnoticed_events_three_arms`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.contact.arm`・`shibuya.engine.contact.attention`・`shibuya.engine.contact.book`・`shibuya.engine.contact.chat_state`・`shibuya.engine.contact.deliver`・`shibuya.engine.contact.device`・`shibuya.engine.contact.layer`・`shibuya.engine.contact.port`・`shibuya.engine.conversation`・`shibuya.engine.decision.port`・`shibuya.engine.events.log`・`shibuya.engine.tools.contacts`・`shibuya.engine.tools.groups`・`shibuya.perception.contact_view`・`shibuya.perception.facts`・`tests/engine/contact/_c1.py`

## [test_c1_world.py](../../../../../../../tests/engine/contact/test_c1_world.py)

第 6 期 6-4 C1 腕 c1(mock 5,000 体・1 日・世界の資産)の試験(slow・data が要る)。

- 公開の関数とクラス
  - `test_world_5000_one_day_records_with_via_and_audit`(関数)
  - `test_world_manner_mode_and_bag_are_weaker`(関数)
  - `test_world_peripheral_vision_coarsens_the_rendered_input`(関数)
  - `test_world_resume_mid_day_is_the_straight_run`(関数)
  - `test_world_ring_arrives_at_the_window_boundary`(関数)
  - `test_world_unnoticed_three_arms_are_counted`(関数)
  - `world_runs`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.contact.layer`・`shibuya.perception.contact_view`・`tests/engine/contact/_c1.py`

## [test_c2_charge.py](../../../../../../../tests/engine/contact/test_c2_charge.py)

第 6 期 6-4 C2: 充電を本人の行動に(CT0 の共通の決まり 2・3)。

- 公開の関数とクラス
  - `test_charge_is_offered_whenever_the_person_thinks_at_home_with_a_low_battery`(関数): 〔検収 L6〕家に居て電池が閾値の下の体は、その刻みに判断したとき(連絡の判断・主の判断)にいつも充電の候補が出る
  - `test_charging_powers_on_and_releases_held_messages`(関数)
  - `test_full_is_reported_once_and_low_alerts_cross_thresholds`(関数)
  - `test_leaving_home_unplugs_and_full_alert_asks_to_stop`(関数)
  - `test_low_alert_at_home_the_person_decides_to_charge`(関数)
  - `test_mailbox_release_held`(関数)
  - `test_negative_control_no_decision_no_charge`(関数): 本人が「このまま」を選ぶ(判断なし)と家に居ても電池は増えない(エンジン規則の充電は外した)。
  - `test_not_at_home_no_charge_opportunity`(関数)
  - `test_outside_residents_are_at_home_while_outside`(関数): 〔親の判断 2026-10-23=問い 1〕住まいが範囲の外の体は範囲の外に居る刻みを家とする(範囲の外の活動は作っていない=「寝ている」が
  - `test_physics_plugged_charges_unplugged_does_not`(関数)
  - `test_power_on_only_for_a_plugged_device`(関数)
- import している内部モジュール: `shibuya.core.time_consts`・`shibuya.engine.bridging.ledger`・`shibuya.engine.contact.deliver`・`shibuya.engine.contact.device`・`shibuya.engine.contact.layer`・`shibuya.engine.contact.port`・`tests/engine/contact/_c1.py`・`tests/engine/contact/_c2.py`

## [test_c2_exchange.py](../../../../../../../tests/engine/contact/test_c2_exchange.py)

第 6 期 6-4 C2: CT5 連絡先の交換とグループ・店の番号(場所の表の側)。

- 公開の関数とクラス
  - `test_a_group_with_no_members_disappears_and_its_invites_too`(関数): 〔検収 L7〕抜けて成員が 0 人になったグループは無くなる(招待も消える)・体 → グループの索引で引く(日数で重くならない)。
  - `test_exchange_both_decide_and_both_books_get_the_mark`(関数)
  - `test_exchange_follows_arbitration_main_decision_first`(関数): 〔検収 L2〕主の判断が先: その刻みに主の判断の呼びのあった体は持ちかけるのを次の刻みに回す(例外にしない)。
  - `test_groups_make_invite_join_and_leave`(関数)
  - `test_invite_refused`(関数)
  - `test_only_the_first_turn_and_not_known_partners`(関数)
  - `test_refused_exchange_adds_nothing`(関数)
  - `test_store_number_lookup_only_where_the_place_table_has_a_number`(関数)
- import している内部モジュール: `shibuya.engine.contact.book`・`shibuya.engine.contact.layer`・`shibuya.engine.contact.port`・`shibuya.engine.tools.contacts`・`shibuya.engine.tools.places`・`tests/engine/contact/_c1.py`・`tests/engine/contact/_c2.py`

## [test_c2_habit.py](../../../../../../../tests/engine/contact/test_c2_habit.py)

第 6 期 6-4 C2: CT4 の習慣(腕 ``SHIBUYA_CONTACT_HABIT``)。

- 公開の関数とクラス
  - `test_arm_off_builds_no_table_and_uses_the_port`(関数)
  - `test_arm_switch_and_fingerprint`(関数)
  - `test_ast_negative_control_catches_a_planted_rule`(関数)
  - `test_ast_no_engine_time_or_count_rules_in_c2`(関数)
  - `test_below_threshold_goes_to_the_decision_port`(関数)
  - `test_habit_answers_when_records_are_enough`(関数)
  - `test_important_offer_goes_back`(関数)
  - `test_in_range_bodies_always_go_to_the_port`(関数): 〔親の判断 2026-10-23=問い 2〕習慣で答えるのは範囲の外に居る体だけ(CT4)。範囲の中の体は記録が足りても判断の口へ。
  - `test_no_records_no_habit_and_threshold`(関数)
  - `test_sometimes_goes_back_with_the_named_stream`(関数)
  - `test_states_from_activity_and_place`(関数)
  - `test_surprise_goes_back`(関数): 驚き=その刻みに起床条件 (i) で起きた体(割り込みと同じ入口=系 contact が刻みの頭に置く ``_interrupted``)。
  - `test_tie_takes_the_first_word_in_order`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.contact.arm`・`shibuya.engine.contact.habit`・`shibuya.engine.contact.layer`・`shibuya.engine.contact.port`・`tests/engine/contact/_c1.py`・`tests/engine/contact/_c2.py`

## [test_c2_runs.py](../../../../../../../tests/engine/contact/test_c2_runs.py)

第 6 期 6-4 C2 ランの試験(合成の世界・腕 c1 の中): 既定 off は何も作らない・manifest の節(習慣・交換・充電・ビデオ)と節の表・道具の台帳の行(腕のランだけ)・監査・習慣 off は判断の口だけ(閾値に届かない習慣 on と同じ選び)・記録 on/off で final とcheckpoint が同じ・日の途中の再開=通し(習慣の表・宛先の帳・充電を含む)・段 B・充電を外すと電源の切れた体が増える(負の対照)・既読の印が候補の文に出る。

- 公開の関数とクラス
  - `test_c1_run_sections_tools_and_audit`(関数)
  - `test_charging_by_the_person_keeps_devices_alive`(関数): 4 日: 本人が充電するラン(mock)は、充電の判断を外したラン(負の対照)より電源の切れた体が少ない。
  - `test_default_off_builds_nothing_and_counts_zero`(関数)
  - `test_event_log_on_off_same_with_habit`(関数)
  - `test_habit_records_do_not_move_anything_until_used`(関数): 習慣 off(判断の口だけ)と、閾値に届かない習慣 on(数えるだけ)は同じ選び・同じ出来事・同じ控え(数えるのは習慣の表だけ)。
  - `test_mid_day_resume_is_the_straight_run_with_c2_state`(関数)
  - `test_read_receipts_reach_the_senders_candidates`(関数)
  - `test_stage_b_with_c2`(関数)
  - `with_groups`(関数)
- import している内部モジュール: `shibuya.core.time_consts`・`shibuya.engine.contact.habit`・`shibuya.engine.contact.layer`・`shibuya.engine.contact.port`・`shibuya.engine.contact.tools`・`shibuya.engine.events.log`・`shibuya.engine.manifest_sections`・`shibuya.engine.resume`・`shibuya.engine.run`・`shibuya.engine.state_ledger`・`shibuya.engine.tools.groups`・`shibuya.engine.tools.record`・`tests/engine/contact/_c1.py`・`tests/engine/contact/_c2.py`
- 環境変数: `SHIBUYA_SYSTEMS_CHECK`

## [test_c2_video.py](../../../../../../../tests/engine/contact/test_c2_video.py)

第 6 期 6-4 C2: ビデオ通話(電話の器の種類違い)。かける/出るは本人・目の向き=画面(相手の顔)・関心の的=通話・電池の減りは通話より大きい・発話は ``Utterance``(via=ビデオ通話)で 1 回だけ記録・知覚の事実は ``tool_state`` の ``call_via``(形と版は不変)。

- 公開の関数とクラス
  - `test_percept_value_marks_the_face_without_changing_the_shape`(関数)
  - `test_via_vocabulary_is_closed_and_versioned`(関数)
  - `test_video_call_round_trip`(関数)
  - `test_video_drains_more_than_a_voice_call`(関数)
- import している内部モジュール: `shibuya.engine.contact.attention`・`shibuya.engine.contact.calls`・`shibuya.engine.contact.deliver`・`shibuya.engine.contact.device`・`shibuya.engine.contact.layer`・`shibuya.engine.contact.port`・`shibuya.engine.events.vocab`・`shibuya.perception.contact_view`・`shibuya.perception.facts`・`tests/engine/contact/_c1.py`・`tests/engine/contact/_c2.py`
