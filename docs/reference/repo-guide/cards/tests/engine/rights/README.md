# tests/engine/rights

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 9 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../tests/engine/rights/__init__.py)

(冒頭の説明なし)

## [rights_writers.py](../../../../../../../tests/engine/rights/rights_writers.py)

第 1 期 1-5(検収 M1): 権利台帳の中身を書く所を AST で集める道具(試験の補助・src は読むだけ)。

- 公開の関数とクラス
  - `Write`(クラス)
  - `is_col`(関数)
  - `iter_sources`(関数)
  - `ledger_violations`(関数)
  - `ledger_writes`(関数): 台帳の置き場の中の書き(列の中身・差し替え・``_write``/``_grow`` の呼び出し)。
  - `outside_touches`(関数): 台帳の置き場の外から中身に触る所(``path:行 形``)。
- import している内部モジュール: `shibuya.world.facts.rights.ledger`
- 読む試験: `tests/engine/rights/test_rights_schema.py`

## [test_no_permission_count.py](../../../../../../../tests/engine/rights/test_no_permission_count.py)

第 1 期 1-5(口の約束 1-5 の約束 (1)): 権限で止める検査が今の既定で当たった回数を 19 構成で数える。

- 公開の関数とクラス
  - `NoPermissionHit`(クラス): ▲ の印: 今の既定で権限の検査が当たった(縮めると結果が動く=第 2 期へ)。
  - `test_live_count_is_zero_or_marked`(関数): 19 構成の生きた数え(約 70 秒=``slow``・検収 L9)。既定 v3 の 1 構成だけは ``slow`` の外(軽い版)。
  - `test_negative_a_hit_is_marked_but_not_failed`(関数): ▲ の印の負の対照: 当たりが 1 つでもあれば警告(落とさない)・0 なら何も出ない。
  - `test_recorded_count_on_five_thousand_bodies`(関数): 道具で数えた 5,000 体の表(HEAD の側=止める検査・作業木の側=記録に替えた後)。0 でなければ ▲ の印。
  - `test_the_nineteen_configs`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.llm_bridge`・`shibuya.engine.resolve`

## [test_rights_events.py](../../../../../../../tests/engine/rights/test_rights_events.py)

第 1 期 1-5(CP3・決定 10-12 §1-4): 権利で止めていた分を止めずに記録に替えた。

- 公開の関数とクラス
  - `WordLLM`(クラス)
  - `test_a_default_run_records_nothing`(関数)
  - `test_an_employee_word_without_employment_is_counted_not_written`(関数)
  - `test_duty_words_are_not_judged_and_everyone_words_are_allowed`(関数)
  - `test_open_close_without_the_right_is_not_stopped_and_is_ok`(関数)
  - `test_record_without_a_log_counts_only_and_checks_lengths`(関数)
  - `test_role_words_inside_the_decide_system`(関数)
  - `test_the_opening_process_records_a_revoked_staff_and_still_opens`(関数)
  - `test_the_word_and_the_cause_name`(関数)
  - `test_without_the_check_nothing_is_counted_and_the_code_is_the_same`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.llm_bridge`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.foundation.journal.links`・`shibuya.foundation.journal.log`・`shibuya.foundation.vocab.actions`・`shibuya.foundation.vocab.events`・`shibuya.llm`・`shibuya.world.facts.rights.ledger`・`shibuya.world.facts.rights.record`・`shibuya.world.laws.opening`・`shibuya.world.ledger.actual_log`・`tests/engine/processes/conftest.py`
- 読む試験: `tests/engine/duties/test_du_runs.py`
- 決定の ID: 10-12/§1-4

## [test_rights_from_w16.py](../../../../../../../tests/engine/rights/test_rights_from_w16.py)

第 1 期 1-5 権利台帳の最初の中身(計画 1-5 の 4 つ・決定 10-12 §4-5 CP4)。

- 公開の関数とクラス
  - `full`(関数)
  - `test_a_sampled_run_population`(関数): 5,000 体の抽出(byte-check と同じ seed 1)でも、雇用の行=``org_id`` を持つ体。組み立ての材料の関数を通す。
  - `test_blank_bridges_are_active_rows_of_the_ledger`(関数)
  - `test_employment_rows_equal_the_bodies_with_an_org_id`(関数)
  - `test_no_population_means_no_employment_rows`(関数)
  - `test_the_four_contents_and_their_blanks`(関数)
- import している内部モジュール: `shibuya.foundation.decl.bridging`・`shibuya.foundation.decl.ledger_paths`・`shibuya.runtime.systems.assemble`・`shibuya.world.facts.population_reader`・`shibuya.world.facts.rights.initial`・`shibuya.world.facts.rights.ledger`・`tests/_places.py`
- 決定の ID: 10-12/§4-5

## [test_rights_manifest.py](../../../../../../../tests/engine/rights/test_rights_manifest.py)

第 1 期 1-5(口の約束 1-5 の約束 (3)): 権利台帳の行数と種類の分布を manifest に出す(計器)。

- 公開の関数とクラス
  - `res`(関数)
  - `test_no_world_processes_means_none`(関数)
  - `test_rebuild_gives_the_same_ledger`(関数)
  - `test_rights_is_the_last_key_and_observed`(関数)
  - `test_the_record_does_not_move_the_result`(関数): 権利台帳の中身を空にしても(担当の表は同じに読む)final と呼数は同じ=manifest の欄は記録だけ。
  - `test_values_come_from_the_ledger`(関数)
- import している内部モジュール: `shibuya.engine.run`・`shibuya.foundation.manifest.sections`・`shibuya.foundation.time_consts`・`shibuya.world.facts.rights.initial`・`shibuya.world.facts.rights.ledger`・`shibuya.world.laws.opening`
- 決定の ID: 11-01・11-02r/§1・11-02r/§1 #7・11-03/§3

## [test_rights_schema.py](../../../../../../../tests/engine/rights/test_rights_schema.py)

第 1 期 1-5 権利台帳の器(CP4): ``Right`` の欄・凍結・書く口は ``grant``/``revoke`` の 2 つだけ・``__setattr__`` の守り。

- 公開の関数とクラス
  - `test_attributes_cannot_be_rebound_or_deleted`(関数)
  - `test_bad_rights_are_refused`(関数)
  - `test_fields_follow_the_contract`(関数)
  - `test_grant_round_trips_every_value`(関数)
  - `test_grant_takes_only_a_right`(関数)
  - `test_holds_and_holders_of_follow_the_time_window`(関数)
  - `test_negative_a_third_write_port_is_caught`(関数)
  - `test_negative_outside_writes_are_caught`(関数)
  - `test_nothing_outside_touches_the_ledger`(関数)
  - `test_object_setattr_cannot_place_internal_names`(関数): ``Rights`` は ``__slots__`` だけ(``__dict__`` なし)=名の無い属性は ``object.__setattr__`` でも置けない(検収 M1)。
  - `test_only_two_write_ports_inside_the_ledger`(関数)
  - `test_readers_hand_out_copies`(関数)
  - `test_revoke_ends_a_right_once`(関数)
  - `test_right_is_frozen_and_slotted`(関数)
  - `test_tables_are_read_only`(関数)
  - `test_the_runtime_limit_is_the_mangled_slot`(関数): 限界(記録 r15/README.md): 名を変えた slot の名を知って ``object.__setattr__`` で触る形は実行時に止まらない
  - `test_values_are_normalised`(関数)
- import している内部モジュール: `shibuya.world.facts.rights.ledger`・`tests/engine/rights/rights_writers.py`

## [test_rules42_rights.py](../../../../../../../tests/engine/rights/test_rules42_rights.py)

第 4 期 4-2 権利台帳の種類(Q3=PENDING 仮-40): 信用の契約(credit)・道路の区間・看板・閉じた表の「所有 → 店」。

- 公開の関数とクラス
  - `test_credit_rows_read_and_write`(関数)
  - `test_initial_rows_are_unchanged_no_owner_credit_road_or_signboard_rows`(関数)
  - `test_licences_on_road_segments_and_signboards`(関数)
  - `test_old_codes_are_kept_and_new_kinds_are_appended`(関数)
  - `test_own_store_is_in_the_closed_table`(関数)
- import している内部モジュール: `shibuya.world.facts.rights.initial`・`shibuya.world.facts.rights.ledger`

## [test_staff_of_poi_equivalence.py](../../../../../../../tests/engine/rights/test_staff_of_poi_equivalence.py)

第 1 期 1-5: ``staff_of_poi`` の丸振りを権利台帳の ``employ`` の行からの読みに置き換えても、同じ割り当てを返す。

- 公開の関数とクラス
  - `head_assign_staff`(関数): POI → 担当従業者(``kind=従業者`` を決定論で丸振り・expedient)。-1=担当なし。
  - `test_open_close_asks_the_ledger_and_stays_the_same`(関数): 開閉の役割行動の権利は台帳に聞く(担当は台帳から読んだ=全部 許可あり)。結果は HEAD と同じ形(OK と旗)。
  - `test_rebuild_keeps_the_values_and_the_shared_array`(関数)
  - `test_same_assignment_for_edge_kinds`(関数)
  - `test_same_assignment_on_synthetic_worlds`(関数)
  - `test_same_assignment_on_the_real_population`(関数): 実データ(5,000 体の抽出・seed 1)の種別と POI の数。SoA は母集団の種別を写した形(組み立てと同じ)。
  - `test_zero_pois`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.resolve`・`shibuya.runtime.systems.assemble`・`shibuya.world.assets`・`shibuya.world.facts.mock_schedule`・`shibuya.world.facts.population_reader`・`shibuya.world.facts.rights.initial`・`shibuya.world.facts.rights.ledger`・`shibuya.world.laws.opening`・`shibuya.world.model.state`・`tests/engine/processes/conftest.py`
