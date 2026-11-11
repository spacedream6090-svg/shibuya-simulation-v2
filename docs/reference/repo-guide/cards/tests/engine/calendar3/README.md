# tests/engine/calendar3

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 5 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../tests/engine/calendar3/__init__.py)

(冒頭の説明なし)

## [_ca3.py](../../../../../../../tests/engine/calendar3/_ca3.py)

第 6 期 6-2 カレンダー 3 の試験の共通(腕の切替・合成の雇い主の口の表・グループの一覧・決まった判断の規則)。

- 公開の関数とクラス
  - `FakeRights`(クラス): 合成の権利台帳(雇用の行=体 → 組織 体の番号 // UNIT)。
  - `by_pref`(関数): 候補の語か id の好みの順で選ぶ規則(どれも無ければ (語・id) の順の最初の候補)。
  - `ca3`(関数): 腕 arm(と C1・カレンダー 2 の腕・試験用の印)を一時的に選ぶ(組み立てが読む)。
  - `choose`(関数): カレンダー 3 の仮のモデルの選びを試験の規則に差し替える(``rule(ctx, presented) -> 候補の id``)。
  - `roster_fixture`(関数): 合成の世界(母集団が無い=W20 と雇用の行が無い)に、合成の雇い主の口の表とグループの一覧(家族 2 人・職場 10 人)を入れる。
  - `synthetic_roster`(関数)
  - `synthetic_table`(関数): 合成の W20 の週の表(奇数の体=週ごと・偶数の体=毎週固定・月〜金に勤務・場所の種類=建物)。
- import している内部モジュール: `shibuya.engine.calendar3.roster`・`shibuya.engine.tools.record`・`shibuya.foundation.arms.calendar2`・`shibuya.foundation.arms.calendar3`・`shibuya.foundation.arms.contact`・`shibuya.foundation.time_consts`・`shibuya.mind.plan.calendar3_port`・`shibuya.society.tools.groups`
- 読む試験: `tests/engine/calendar3/test_ca3_runs.py`・`tests/engine/calendar3/test_ca3_units.py`・`tests/engine/calendar3/test_ca3_world.py`・`tests/engine/time/test_v30a_key_sites.py`

## [test_ca3_runs.py](../../../../../../../tests/engine/calendar3/test_ca3_runs.py)

第 6 期 6-2 カレンダー 3 のランの試験(合成 80 体・組織と雇用の行つき): 雇い主が週 1 回だけ組む・正規は触らない・候補の枠が W20 の約束の形から来る(労働時間の行と営業時間は読むだけ=超えたら記録)・働く人の行がカレンダー 2 の形で入る・休みの申し出 → 受ける/断るが本人の判断・C3 の連絡が C1 の口を通る(監査 0)・祝日の日付のラン・2 日(日 → 月)と再開=通し・段 B 0・記録 on/off 同じ・既定 off で層が無い・腕の取り違えの再開は止まる・CLI・AST の負の対照(エンジンが時刻や中身を決める直書きが無い)。

- 公開の関数とクラス
  - `sunday_run`(関数)
  - `test_arm_needs_contact_and_calendar2`(関数)
  - `test_arm_rows_enter_the_hashes_only_when_the_owner_exists`(関数)
  - `test_ast_book_is_written_only_through_its_ports`(関数)
  - `test_ast_engine_does_not_decide_times_or_contents`(関数)
  - `test_ast_negative_control_catches_engine_rules`(関数)
  - `test_ast_negative_control_catches_planted_causes`(関数)
  - `test_ast_person_events_come_only_from_decisions`(関数)
  - `test_c3_contacts_go_through_the_c1_mouth_and_audits_are_clean`(関数)
  - `test_cli_flag_and_run_kind`(関数)
  - `test_compose_on_friday_without_the_trial_mark`(関数): 試験用の印の無い月曜始まりの 5 日(連続する平日)でも金曜(4 日目)に翌週(次の月曜=7 日目)を組む。
  - `test_contact_without_calendar3_has_no_sinks_and_no_window_paths`(関数)
  - `test_declined_rest_keeps_the_row`(関数)
  - `test_default_off_builds_nothing`(関数): 既定 off: 層・manifest の節・状態のファイルの calendar3.* の項・設定の指紋の鍵・勤務の族の出来事・C1 の控えの口が 0。
  - `test_employer_composes_once_a_week_for_weekly_workers_only`(関数)
  - `test_event_log_on_off_does_not_change_the_arm_run`(関数)
  - `test_holiday_run_is_common_knowledge_and_runs`(関数)
  - `test_labor_rows_and_store_hours_are_only_recorded`(関数)
  - `test_manifest_section_and_calls_by_model`(関数)
  - `test_rest_request_answer_and_apply_are_decisions`(関数)
  - `test_resuming_with_the_arm_off_stops`(関数)
  - `test_roster_is_built_after_restore_and_resume_matches_without_monkeypatch`(関数)
  - `test_roster_is_not_built_at_assembly`(関数): 組み立ての口は表を作る口だけを渡す(表は最初の刻みの頭=ensure_roster)。
  - `test_seven_days_negative_control_no_charge_decision`(関数): 〔第 6 期 6-4 C2 検収 L10〕負の対照: 充電の判断を「このまま」に固定すると、7 日で誰も充電せず(電池が増えない)、電源の切れた体と
  - `test_seven_days_with_the_trial_mark_compose_once_on_friday`(関数): 月曜始まりの 7 日(週末を含む=試験用の印): 組むのは金曜の 1 回だけ(0 日目は月曜=0 日目の組む機会は無い)。
  - `test_stage_b_has_no_undeclared_writes`(関数)
  - `test_stage_b_negative_control_without_the_read_declaration_fails`(関数)
  - `test_sunday_start_without_the_trial_mark_still_stops`(関数): 試験用の印の無いランは開始日の検査を今のまま止める(日曜始まり)。
  - `test_system_declarations`(関数)
  - `test_trial_run_fills_the_start_check_field`(関数)
  - `test_two_days_sunday_to_monday_and_resume_is_the_straight_run`(関数)
  - `test_work_rows_have_the_calendar2_form`(関数)
  - `test_workers_per_unit_match_the_roster_fixture`(関数)
  - `with_real_rights`(関数): 雇い主の口の表は差し替えない(権利台帳=合成の世界の開閉の過程の台帳から本物の道で作る)。W20 の週の表(世界の資産)と
  - `with_roster`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.calendar`・`shibuya.engine.calendar3.layer`・`shibuya.engine.calendar3.roster`・`shibuya.engine.contact.layer`・`shibuya.engine.run`・`shibuya.experiments.port.run_kind`・`shibuya.foundation.arms.calendar3`・`shibuya.foundation.journal.log`・`shibuya.foundation.manifest.sections`・`shibuya.mind.plan.calendar3_port`・`shibuya.mind.plan.contact_port`・`shibuya.mind.plan.promise_book`・`shibuya.runtime.state.ledger`・`shibuya.runtime.state.resume`・`shibuya.runtime.systems.conductor`・`shibuya.runtime.systems.table`・`tests/engine/calendar3/_ca3.py`
- 環境変数: `SHIBUYA_SYSTEMS_CHECK`

## [test_ca3_units.py](../../../../../../../tests/engine/calendar3/test_ca3_units.py)

第 6 期 6-2 カレンダー 3 の単体の試験: 雇い主の口の表(組織ごとのシフトを組む人・週ごとの働く人・正規は触らない・枠=W20 の約束の形)・暦の常識(祝日の問い合わせの口・常識の文)・店の決まり(枠だけ)・労働時間の行(human=読むだけ)・判断の呼びの id・監査の負の対照・腕の切替口と設定。

- 公開の関数とクラス
  - `test_arm_switch_and_config`(関数)
  - `test_audit_catches_forged_and_engine_causes`(関数)
  - `test_call_ids_do_not_collide_with_contact_or_calendar2`(関数)
  - `test_common_knowledge_knows_holidays_for_everyone`(関数)
  - `test_labor_rows_are_human_and_read_only`(関数)
  - `test_port_mock_is_uniform_over_candidates_and_deterministic`(関数)
  - `test_promise_book_has_the_work_kind_at_the_end`(関数)
  - `test_roster_outside_employer_and_no_employer_are_not_scheduled`(関数)
  - `test_roster_store_unit_and_self_scheduling`(関数)
  - `test_roster_units_scheduler_and_weekly_workers_only`(関数)
  - `test_roster_without_table_or_population_is_empty`(関数)
- import している内部モジュール: `shibuya.engine.calendar`・`shibuya.engine.calendar3.knowledge`・`shibuya.engine.calendar3.layer`・`shibuya.engine.calendar3.roster`・`shibuya.foundation.arms.calendar3`・`shibuya.foundation.journal.log`・`shibuya.foundation.ports.decision`・`shibuya.mind.plan.calendar2_port`・`shibuya.mind.plan.calendar3_port`・`shibuya.mind.plan.contact_port`・`shibuya.mind.plan.promise_book`・`shibuya.world.facts.rights.initial`・`tests/engine/calendar3/_ca3.py`

## [test_ca3_world.py](../../../../../../../tests/engine/calendar3/test_ca3_world.py)

第 6 期 6-2 カレンダー 3 の世界の試験(slow・data): 5,000 体の日曜 1 日(試験用の印)=権利台帳の雇用の行と W20 の週の表から雇い主の口の表ができ、雇い主が組んで C3 の連絡が C1 の口を通る(監査 0)。

- 公開の関数とクラス
  - `test_world_5000_sunday_composes_and_audits_are_clean`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.calendar3.layer`・`shibuya.engine.contact.layer`・`tests/engine/calendar3/_ca3.py`
