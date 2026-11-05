# tests/engine/calendar

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 4 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../tests/engine/calendar/__init__.py)

(冒頭の説明なし)

## [test_ca1b_runs.py](../../../../../../../tests/engine/calendar/test_ca1b_runs.py)

第 6 期 6-2 カレンダー 1b(腕 ``--calendar 1b``)のランの受入の試験。

- 公開の関数とクラス
  - `arm_1b`(関数)
  - `pair`(関数)
  - `test_1b_5000_bodies_one_day`(関数)
  - `test_1b_counts_the_place_by_the_body_position_and_reoffers_after_leaving`(関数): 〔検収 H1〕計画一致率と 15 分の在場率は体の位置で数える(段の値は *_phase)。勤務中に本人の行為で舞台を出た体には、
  - `test_1b_keeps_the_w17_sleep_and_wake`(関数)
  - `test_1b_resume_equals_straight_over_two_days`(関数)
  - `test_1b_runs_and_the_person_decides_the_trips`(関数)
  - `test_1b_writes_stay_inside_the_declarations`(関数): 段 B(``SHIBUYA_SYSTEMS_CHECK``): 腕 1b の 2 日のランで、系の前後で変わった欄は宣言の書く欄の中。
  - `test_arm_1b_needs_the_population_and_the_plan_executor`(関数)
  - `test_cli_flag_run_kind_and_fingerprint`(関数)
  - `test_default_has_no_layer_and_no_manifest_key`(関数)
  - `test_default_two_days_resume_equals_straight`(関数): 既定(w17)の 2 日のランの再開=通し(層は無い・manifest に 1b の節は無い)。
  - `test_everyone_attends_after_the_lottery_was_removed`(関数): 〔11-01 段 2 の 4〕出勤率のくじは消した=全員出勤(計画実行層と同じ口 ``absent_on``・除いた理由「出勤率のくじ」は 0)。
  - `test_inbound_trains_by_the_rail_table_and_on_time`(関数): 〔検収 L2・L1〕到着の便を実装と別に鉄道の表から直に引く(準備の時刻以降に最初にホームへ入るその路線の便)・着いた刻み
  - `test_negative_backward_wake_is_caught`(関数): 植えた写し: エンジンが本当の道のり(域外の時間+歩き)から逆算した時刻に起こす(本人の記録を参照しない)→ 検査が数える。
  - `test_negative_e4_vanish_is_caught`(関数): 植えた写し(E4): 歩きが途切れた体をその場で域外へ消す → 検査が歩きの途中の消去を数える。
  - `test_negative_forced_exit_by_time_is_caught`(関数): 植えた写し: 計画実行層が管理する体の W17 の DEPART を実行する(時刻で強制的に退出)→ 検査が数える。
  - `test_negative_selecting_the_train_in_time_is_caught`(関数): 植えた写し: エンジンが約束に間に合う最も遅い便(E1)を選ぶ → 到着の便が「来た便」でないので検査が数える。
  - `w20`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.calendar_self`・`shibuya.engine.presence`・`shibuya.engine.resolve`・`shibuya.engine.resume`・`shibuya.engine.run`
- 環境変数: `SHIBUYA_CALENDAR_W20`・`SHIBUYA_SYSTEMS_CHECK`
- 決定の ID: 11-01

## [test_ca1b_unit.py](../../../../../../../tests/engine/calendar/test_ca1b_unit.py)

第 6 期 6-2 カレンダー 1b(``engine.calendar_self``・腕 ``--calendar 1b``)の合成の単体の試験。

- 公開の関数とクラス
  - `backward_assignments`(関数): 機会の時刻(``next_T``・``plan_T``)を約束の始まりや道のり(``start_T``・``d_out``・``walk_go``・``lead``)から作る代入と、
  - `test_arm_names_and_switch`(関数)
  - `test_bridges_rows_are_in_the_ledger`(関数)
  - `test_candidates_follow_the_j0_contract`(関数)
  - `test_clock_minutes_only_when_looked`(関数)
  - `test_clock_tool_row_decides_minute_reading`(関数): 〔検収 L4〕時計の道具の行を読む(知っていれば分単位で読める)。
  - `test_estimate_width_and_recent_mean`(関数)
  - `test_felt_time_form_and_rounding`(関数)
  - `test_first_entering_train_reads_the_rail_table`(関数)
  - `test_manifest_section_ledger_rows_and_system_declarations`(関数)
  - `test_mock_departs_as_planned_and_classical_uses_the_center`(関数)
  - `test_negative_backward_assignment_with_a_reference_id_is_caught`(関数)
  - `test_no_backward_assignment_in_the_layer`(関数)
  - `test_only_broken_commitments_are_rejected_and_overlaps_warn`(関数)
  - `test_placement_decides_how_the_plan_comes_back`(関数)
  - `test_relay_excludes_broken_school_and_home_work`(関数)
  - `test_reminder_times_come_through_choose`(関数)
  - `test_route_steps_counts_nodes_on_the_walk_graph`(関数)
  - `test_tool_registry_has_clock_and_forecast`(関数)
  - `test_w20_place_words_are_the_build_side_copy`(関数)
- import している内部モジュール: `shibuya.build.sched.w20_calendar_1a`・`shibuya.engine.bridging.ledger`・`shibuya.engine.calendar_self`・`shibuya.engine.calendar_shadow`・`shibuya.engine.decision.port`・`shibuya.engine.manifest_sections`・`shibuya.engine.state_ledger`・`shibuya.engine.systems.table`・`shibuya.engine.tools.registry`
- 決定の ID: R-111・R-111 §1-2 #1

## [test_calendar_shadow.py](../../../../../../../tests/engine/calendar/test_calendar_shadow.py)

第 3 期 3-1 エンジン側の影を読む口(``engine.calendar_shadow``・腕 ``--calendar-shadow {w17,1a}``)の受入の試験。

- 公開の関数とクラス
  - `arm_1a`(関数)
  - `keep_arm`(関数)
  - `one_day_pair`(関数)
  - `test_1a_does_not_move_behavior_and_keeps_the_w17_bridges`(関数)
  - `test_1a_fingerprint_and_missing_table`(関数): 1a のランだけ設定の指紋に入る(既定は今の指紋)・表が無ければ組み立てで止まる。
  - `test_1a_resume_equals_straight_over_two_days`(関数): 2 日のランを日の境目で止めて再開=通しと同じ final と同じ影の記録(影は W20・暦・日番号だけから決まる)。
  - `test_1a_shadow_comes_from_the_w20_table`(関数): 1 日のランの勤務の影は W20 の表の行(その日の曜日・ランの体)そのもの(出勤・始業・終業・帰宅の分布が一致)。
  - `test_1a_writes_stay_inside_the_declarations`(関数): 段 B(``SHIBUYA_SYSTEMS_CHECK``): 腕 1a の 2 日のランで、系の前後で変わった欄は宣言の書く欄の中(日の頭の
  - `test_arm_1a_needs_the_population`(関数)
  - `test_cli_flag_beats_the_environment`(関数): ``--calendar-shadow`` は環境変数より強い: 環境 1a でも w17 を渡せば母集団の無いランが通る(源 w17・ランの種類 reproduction)。
  - `test_cli_run_kind_and_fingerprint_follow_the_arm`(関数): CLI の 1a はランの種類 arm(w17 は reproduction)・設定の指紋には 1a のときだけ ``calendar_shadow: "1a"``。
  - `test_constants_match_the_build_side_and_the_calendar`(関数)
  - `test_default_has_no_shadow`(関数)
  - `test_guards_refuse_direct_writes`(関数): 〔検収 中 3〕影は計器だけ=外からの付け替え・消去・中身の書き込みは実行時に止まる(張り直しは relay_day の中だけ)。
  - `test_load_table_restricts_to_the_run_agents`(関数)
  - `test_manifest_section_ledger_row_and_system_declarations`(関数)
  - `test_unit_relay_day_records_follow_the_table`(関数)
  - `w20_table`(関数): W16 の全員に作り物の材料で W20 の週の表を作る(エンジンの読み口の試験=表の中身の正しさは構築側の試験)。
- import している内部モジュール: `shibuya.build.geo.common`・`shibuya.build.sched.w20_calendar_1a`・`shibuya.cli`・`shibuya.engine.calendar`・`shibuya.engine.calendar_shadow`・`shibuya.engine.manifest_sections`・`shibuya.engine.resume`・`shibuya.engine.run`・`shibuya.engine.state_ledger`・`shibuya.engine.systems.table`・`tests/build_sched/test_w20_calendar_1a.py`
- 環境変数: `SHIBUYA_CALENDAR_W20`・`SHIBUYA_SYSTEMS_CHECK`・`os.environ` をまるごと使う
