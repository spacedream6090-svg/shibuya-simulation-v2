# tests/engine/bridging

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 3 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../tests/engine/bridging/__init__.py)

(冒頭の説明なし)

## [test_bridging_ledger.py](../../../../../../../tests/engine/bridging/test_bridging_ledger.py)

第 1 期 1-4 つなぎの台帳(CA8・計器の最初・計画 10-12 §1 の 3・口の約束 1-4)。

- 公開の関数とクラス
  - `decls`(関数)
  - `ledger`(関数)
  - `test_a_broken_ledger_stops_the_run_at_the_start`(関数): 検収 L10: 壊れた台帳は組み立て(ランの始め)で落ちる=1 日回した後の日の締めまで待たない。
  - `test_bad_rows_are_refused`(関数)
  - `test_build_stage_ids_are_the_c8_d44_row_ids`(関数): build の段の行の id(``W<n>#<i>``)は C8 の感度の台帳 D-44 の行と同じ項を指す(D-44 の切り詰めた文が頭に合う)。
  - `test_code_declarations_and_ledger_rows_are_one_to_one`(関数)
  - `test_counts_by_remove_at_add_up`(関数)
  - `test_declared_places_exist`(関数): 台帳の道(〔移す段 4 の下ごしらえ〕移したファイルは ``ledger_paths`` の表で今の道へ引く)にファイルがある。
  - `test_doc_rows_need_no_code_declaration`(関数)
  - `test_every_row_has_remove_at_declared_in_and_conf`(関数)
  - `test_from_dict_refuses_unknown_fields_and_duplicates`(関数)
  - `test_heading_rows_carry_the_heading_and_the_item_count`(関数): 第 4 形: 見出し 1 つで 1 行(親の判断 第334)。``what`` に見出しの文と今の項の数・id はファイルと見出しの文の
  - `test_ledger_paths_table_is_one_to_one_and_points_to_files`(関数): 表の今の道は全部ファイルがあり、台帳の道は重ならない。台帳のコードの行の道は、表を通して全部今のファイルに届く。
  - `test_literal_declarations_are_copied_verbatim`(関数): 文字列の宣言は台帳の ``what`` にそのまま写す(f 文字列と式は構築したときの値=写しの外)。
  - `test_negative_a_changed_item_count_is_caught`(関数): 見出しの下の項が増えると、同定(見出しの文)は同じでも台帳の ``what`` の項数と合わなくなる(試験が落ちる)。
  - `test_negative_a_new_conf_expedient_fails`(関数)
  - `test_negative_a_new_declaration_in_a_moved_file_is_missing_under_the_ledger_key`(関数): ファイルを動かしたふり(表に 1 行足す)でも、宣言の同定は台帳の道で作られ、台帳の行と同じ鍵になる。移したファイルに
  - `test_negative_a_new_docstring_paragraph_fails`(関数)
  - `test_negative_a_new_fallback_row_fails`(関数): 第 6 形: フォールバック台帳に行が増えると、台帳に行が無いので落ちる。
  - `test_negative_a_new_heading_fails`(関数)
  - `test_negative_a_new_item_in_a_stage_list_fails`(関数)
  - `test_negative_a_new_process_declaration_fails`(関数): 第 5 形: ``mechanism=False`` と ``repayment_due=`` の両方がある呼び出しだけ数える(成長の宣言は数えない)。
  - `test_negative_editing_a_declaration_or_dropping_a_row_fails`(関数)
  - `test_negative_removed_rows`(関数): 検収 L2: ``removed`` の行は数えず突き合わせない。まだコードにある宣言の行を removed にすると落ちる・宣言を消した
  - `test_process_and_fallback_rows`(関数): 第 5 形(世界過程 16+PlanSpec 2)と第 6 形(フォールバック台帳 5 行)=検収 M1。外す段は返済期限から。
  - `test_refractory_eleven_and_the_wake_class_are_removed_at_t3`(関数): 回答 10-13b §4-2 の 2: 不応期 11 種と起床条件のクラスは T3 で外す(各 1 行)。
  - `test_rows_and_the_ledger_are_frozen`(関数)
  - `test_rule_ids_point_to_the_rules_table`(関数): 検収 L7: 直書きの係数の行は規則の表の行に結ぶ(``rule_id`` は表にある id)。
  - `test_the_counts_by_form`(関数): 記録 r14/README.md の表と同じ数(形が増減したら記録も直す)。
  - `test_the_first_contents`(関数)
  - `test_the_ledger_sha_is_canonical`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.bridging.ledger`・`shibuya.engine.bridging.ledger_paths`・`shibuya.engine.bridging.scan`・`shibuya.engine.rules.table`・`shibuya.engine.run`・`shibuya.engine.systems.build`・`shibuya.world.processes.first_batch`・`shibuya.world.processes.relations`
- 決定の ID: 10-12/§1・10-13b/§4-2・D-44・第 334・第 336・第 337・第 342・第 346

## [test_manifest_rules_bridges.py](../../../../../../../tests/engine/bridging/test_manifest_rules_bridges.py)

第 1 期 1-4: manifest の ``bridges_count``・``rules_version``・``run_kind``・``bridges_version``(CP10・CP5-5・TM9・口の約束 1-4・検収 L1・M2)。

- 公開の関数とクラス
  - `test_cli_main_and_cli_run_decide_the_kind`(関数): ``main`` は ``run`` の決め方を使う。試験の中は ``test``・外では既定=再現・腕=arm。
  - `test_cli_run_puts_the_kind_on_the_result_and_not_in_the_fingerprint`(関数)
  - `test_daily_records_carry_the_count_and_the_version_before_events`(関数)
  - `test_missing_files_give_null_with_a_warning`(関数): 台帳と表の無い写し(``git archive`` で src だけ取った木)では欄は null(ランは止めない)。
  - `test_sections_are_config`(関数)
  - `test_the_cli_default_is_not_an_arm`(関数): ``main`` の既定の引数(``parse_args([])``)を ``run`` で受け取ると、腕は 1 つも無い=``arm_baseline`` は CLI の既定と
  - `test_the_fields_are_at_the_end_and_frozen`(関数)
  - `test_the_fields_do_not_feed_the_final_hash`(関数)
  - `test_the_rule_test_over_arm_over_reproduction`(関数)
  - `test_tool_configs_that_call_cli_run_are_arms`(関数): byte-check(10e・19 構成)と 10f の manifest の道具が ``cli.run`` に渡す構成: 既定 v3 だけが再現・ほかは腕(検収 M2)。
  - `test_values_match_the_ledger_and_the_table`(関数)
  - `two_days`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.core.time_consts`・`shibuya.engine.bridging.ledger`・`shibuya.engine.manifest_sections`・`shibuya.engine.rules.table`・`shibuya.engine.run`・`shibuya.engine.run_kind`
- 決定の ID: 11-01・11-02r・11-02r/§1・11-02r/§1 #7・11-03・11-03/§3
