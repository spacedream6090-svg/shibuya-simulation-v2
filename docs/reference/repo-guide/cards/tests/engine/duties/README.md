# tests/engine/duties

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 5 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../tests/engine/duties/__init__.py)

(冒頭の説明なし)

## [_du.py](../../../../../../../tests/engine/duties/_du.py)

第 6 期 6-6 ② 第 1 部 店の仕事の試験の共通(腕の切替・合成の世界=店・担当・雇用の行・店の決まり=営業時間の表・物の台帳・判断の差し替え)。

- 公開の関数とクラス
  - `by_pref`(関数): 候補の id の好みの順で選ぶ規則(どれも無ければ (語・id) の順の最初の候補)。
  - `choose`(関数): 店の仕事の仮のモデルの選びを試験の規則に差し替える(``rule(ctx, presented) -> 候補の id``)。
  - `du`(関数): 腕 arm を一時的に選ぶ(組み立てが読む)。
  - `duty_events`(関数)
  - `fresh`(関数): 毎回作り直す世界と台帳(ランごとに新しい物が要る)。
  - `plan_assets`(関数): 店の決まり(W7 の形の営業時間の表)。曜日 0〜6 と祝日の行(7)に同じ区間。``per_poi`` で店ごとに替えられる。``src`` は
  - `world_fixture`(関数): 合成の世界・物の台帳・店の決まりを組み立ての口に入れる(``run_day(**kw, **extra)`` の ``extra`` を返す)。店の担当は今の
- import している内部モジュール: `shibuya.cli`・`shibuya.core.time_consts`・`shibuya.engine.duties.arm`・`shibuya.engine.duties.port`・`shibuya.engine.rights.initial`・`shibuya.engine.rights.ledger`・`shibuya.engine.systems.build`・`shibuya.world.assets`・`shibuya.world.state`
- 読む試験: `tests/engine/duties/test_du_runs.py`・`tests/engine/duties/test_du_world.py`・`tests/engine/time/test_v30a_key_sites.py`

## [test_du_runs.py](../../../../../../../tests/engine/duties/test_du_runs.py)

第 6 期 6-6 ② 第 1 部 店の仕事を働く人の体へ: ランの試験(合成 80 体・1 セル・店 2=店 0 は担当あり・店 1 は担当なし・店の決まり=9:00〜21:00・物の台帳つき)。

- 公開の関数とクラス
  - `day_run`(関数)
  - `test_a_second_employee_acts_and_coverage_is_split_by_origin`(関数): 店 ST に W21c の雇用の行が 2 行(体 30 → 体 9 の順)・店 UN は丸振り。体 30 を起きていない扱いにすると 2 人目(体 9)が
  - `test_a_sleeping_staff_is_bridged_like_an_absent_one`(関数): 担当が店で寝ている店は担当が居ない店と同じ(開閉の過程の REPLACEMENT)=寝ている体の代わりに店が止まらない。
  - `test_arm_needs_the_world_processes`(関数)
  - `test_arm_rows_and_system_declarations`(関数)
  - `test_audit_catches_forged_causes`(関数)
  - `test_cli_flag_and_run_kind`(関数)
  - `test_default_off_builds_nothing`(関数)
  - `test_discard_is_a_closing_task_and_the_morning_bridge_skips_it`(関数)
  - `test_event_log_on_off_does_not_change_the_arm_run`(関数)
  - `test_labor_rows_are_recorded_and_do_not_stop`(関数)
  - `test_llm_bridge_hands_the_role_word_to_the_sink`(関数)
  - `test_manifest_section_and_calls_by_model`(関数)
  - `test_no_restock_offer_when_the_backroom_is_empty`(関数)
  - `test_restock_is_the_persons_decision_and_the_engine_does_not_restock_a_staffed_store`(関数)
  - `test_restock_presence_ignores_the_agent_kind`(関数): 担当が種別 従業者でない(通勤者=W21c の担当)店を模して has_permission をいつも偽に=腕 arm のつなぎは店に居て起きている
  - `test_resuming_with_the_arm_off_stops`(関数)
  - `test_role_words_from_the_main_decision_take_effect_at_the_store`(関数)
  - `test_staffed_store_is_unlocked_by_the_person_and_the_other_by_the_bridge`(関数)
  - `test_stage_b_has_no_undeclared_writes`(関数)
  - `test_stage_b_negative_control_without_the_declaration_fails`(関数)
  - `test_store_rules_carry_the_source_mark`(関数)
  - `test_the_offer_moves_with_the_store_rules`(関数)
  - `test_two_days_and_resume_is_the_straight_run`(関数)
  - `test_vocabulary_is_closed_and_appended`(関数)
  - `test_without_the_decision_the_shelf_is_not_restocked_by_the_engine_at_a_staffed_store`(関数)
  - `test_without_the_decision_the_staffed_store_stays_closed`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.duties.arm`・`shibuya.engine.duties.layer`・`shibuya.engine.duties.port`・`shibuya.engine.events.log`・`shibuya.engine.events.vocab`・`shibuya.engine.llm_bridge`・`shibuya.engine.manifest_sections`・`shibuya.engine.processes.goods_flow`・`shibuya.engine.rate_rules`・`shibuya.engine.resolve`・`shibuya.engine.resume`・`shibuya.engine.run`・`shibuya.engine.run_kind`・`shibuya.engine.state_ledger`・`shibuya.engine.systems.table`・`shibuya.llm.contract`・`shibuya.world.processes.records`・`tests/engine/duties/_du.py`・`tests/engine/rights/test_rights_events.py`
- 環境変数: `SHIBUYA_SYSTEMS_CHECK`
- 決定の ID: 11-01

## [test_du_units.py](../../../../../../../tests/engine/duties/test_du_units.py)

第 6 期 6-6 ② 第 1 部 店の仕事の単体の試験: 店の決まりの口(担当だけが知る・区切り・常識の文)・仮のモデル(一様・決定論・閉じた語)・呼びの id・腕の切替口・AST の負の対照(本人の語の原因は判断の呼びだけ・候補を出す条件に時刻の直書きが無い)。

- 公開の関数とクラス
  - `test_arm_switch`(関数)
  - `test_ast_negative_control_catches_planted_causes`(関数)
  - `test_ast_negative_control_catches_time_literals`(関数)
  - `test_ast_offer_conditions_have_no_time_literals`(関数)
  - `test_ast_person_events_come_only_from_decisions`(関数)
  - `test_call_ids_do_not_collide_with_other_ports`(関数)
  - `test_first_per_store_takes_the_first_eligible_row`(関数): 〔検収 M1〕雇用の行(店の順)のうち候補になれる行の、店ごとの最初の行(1 店 1 刻み 1 人)。
  - `test_mock_port_is_uniform_deterministic_and_closed`(関数)
  - `test_only_the_staff_knows_the_store_rules`(関数)
  - `test_store_rules_follow_the_table_rows`(関数)
  - `test_store_rules_source_mark`(関数): 〔検収 M3〕出どころの印(W7 の列 src)・実データには印を付けない・列が無ければ不明。
  - `test_store_rules_without_a_table_know_nothing`(関数)
- import している内部モジュール: `shibuya.engine.calendar3.port`・`shibuya.engine.decision.port`・`shibuya.engine.duties.arm`・`shibuya.engine.duties.knowledge`・`shibuya.engine.duties.layer`・`shibuya.engine.duties.port`・`shibuya.engine.rights.ledger`

## [test_du_world.py](../../../../../../../tests/engine/duties/test_du_world.py)

第 6 期 6-6 ② 第 1 部 店の仕事の世界の試験(slow・data): 5,000 体の 1 日(腕 arm)=担当が店に居る店を本人が開け閉めし、エンジンのつなぎは担当が居ない/寝ている店だけ(担当の行動の ActualLog は SCHEDULED)・監査 0・計器の節がある。

- 公開の関数とクラス
  - `test_world_5000_one_day_with_the_duties_arm`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.duties.layer`・`tests/engine/duties/_du.py`
