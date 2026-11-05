# tests/bridging

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 3 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../tests/bridging/__init__.py)

(冒頭の説明なし)

## [test_decision_rows_1101.py](../../../../../../tests/bridging/test_decision_rows_1101.py)

第340 段 2 の 2: 判断ごとの行(``DEC-…``)とその欄(tools/ledger/add_decision_rows_1101.py)。

- 公開の関数とクラス
  - `doc`(関数)
  - `test_base_rows_are_byte_identical`(関数)
  - `test_existing_rows_are_kept`(関数)
  - `test_one_row_per_routing_decision`(関数)
  - `test_pattern_columns_tool_is_idempotent_and_keeps_cells`(関数)
  - `test_rows_load_as_bridges_with_the_new_fields`(関数)
  - `test_tool_is_idempotent_on_the_current_ledger`(関数)
  - `tool`(関数)
- import している内部モジュール: `shibuya.engine.bridging.ledger`
- 決定の ID: 11-01/§10-1・11-02r/§1・11-02r/§1 #7・11-03/§3・第 340・第 342

## [test_drives_from_vs_scoring.py](../../../../../../tests/bridging/test_drives_from_vs_scoring.py)

第340 段 2 の 2: 循環の機械検査(回答 11-01 §3)=``drives_from`` とパターン台帳の「採点する系」・``burned`` の突き合わせ。

- 公開の関数とクラス
  - `by_id`(関数)
  - `overlaps`(関数)
  - `reg`(関数)
  - `rows`(関数)
  - `scoring`(関数)
  - `subjects`(関数)
  - `test_absence_stage_matches_the_dec_row`(関数)
  - `test_case_collapse_rate_w3_is_out_of_validation_until_the_body_formula`(関数)
  - `test_case_parcel_delivery_w2_is_absent_and_w2_stays_an_anchor`(関数)
  - `test_case_price_beta_is_not_calibrated_to_e7`(関数)
  - `test_d5p_and_e5_are_on_the_validation_side`(関数): 〔11-02r/§1 #6〕D5′ は検証へ移し「今は入力と重なるので採点できない(burned)」、E5 は検証(既知の循環として宣言)。
  - `test_drives_from_values_are_known_systems`(関数)
  - `test_engine_stopped_flags`(関数): True=口が無い判断・採用と解雇・発注と、率の規則(``engine.rate_rules`` の既定 off)で止まった 5 件と、〔11-02r §1 #7〕
  - `test_every_declared_process_has_drives_from`(関数): 世界の台帳の過程と PlanSpec は全部 drives_from を書いた(未記入は 0)。
  - `test_known_rows_in_the_pattern_ledger_have_a_declaration`(関数): 台帳の「既知の循環」の行には宣言の表の行がある(2 か所の突き合わせ)。宣言の行は台帳に有る ID だけ。
  - `test_negative_control_overlap_fails_unless_burned_or_stopped_absence`(関数)
  - `test_next_bump_rows`(関数)
  - `test_no_mismatch_after_rate_rules`(関数): 宣言はあるがエンジンがまだ動かしている重なり(中-3)=率の規則を外す段(ce52662)の後は 0。
  - `test_no_stale_declaration`(関数): どの重なりにも当たらない宣言は残さない(代打の条件 ⑤ の宣言は (c) で見る)。
  - `test_no_undeclared_circularity`(関数): 〔11-02r §1 #6〕例外の付かない重なりは全部宣言つき(警告)。宣言の無い重なりは 0(=落とす)。
  - `test_pattern_ledger_has_scoring_and_burned_for_every_row`(関数)
  - `test_stand_in_overlaps_are_declared`(関数): 〔11-02r §1 #6〕代打の条件 ⑤ の重なりも 2 段: 宣言の無いものは落とす・宣言つきは警告。宣言は全部当たる。
  - `test_suspect_rows_contributes`(関数)
  - `test_two_tiers_on_a_synthetic_example`(関数): 〔11-02r §1 #6〕合成の例: 宣言の無い重なりで落ち、宣言つきで警告だけ。例外(burned)はどちらにも入らない。
- import している内部モジュール: `shibuya.engine.absent_processes`・`shibuya.engine.rate_rules`・`shibuya.world.processes.absent`・`shibuya.world.processes.circularity`・`shibuya.world.processes.constitution`・`shibuya.world.processes.first_batch`
- 決定の ID: 11-01/§2・11-01/§3・11-02r・11-02r/§1・11-02r/§1 #6・11-02r/§1 #7・第 340・第 342
