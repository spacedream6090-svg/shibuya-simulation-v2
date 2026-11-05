# tests/vocab

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 5 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../tests/vocab/__init__.py)

(冒頭の説明なし)

## [conftest.py](../../../../../../tests/vocab/conftest.py)

tests.vocab の共通フィクスチャ。

- 公開の関数とクラス
  - `adjudicate`(関数)
  - `registry_from_tape`(関数)
- import している内部モジュール: `tools/vocab/adjudicate.py`・`tools/vocab/registry_from_tape.py`
- 読む試験: `tests/vocab/test_registry_from_tape.py`

## [test_adjudicate.py](../../../../../../tests/vocab/test_adjudicate.py)

``tools/vocab/adjudicate.py``(段2 起草 + 段3 静的検査)の検査。

- 公開の関数とクラス
  - `test_bad_affordance_and_bad_account_and_bad_code_are_rejected`(関数): (s1) affordance は snake_case /(s2) 失敗コードは大文字 SNAKE /(s3) 科目は科目表に実在。
  - `test_batch_budget_holds_the_rest`(関数): 件数予算(既定 10)を超えた語は ``HELD_BUDGET``(保持のみ)。
  - `test_below_threshold_is_held_not_dropped`(関数): N=10 体未満は起草せず**保持する**(全件保持・決定 A (b))。
  - `test_existing_failure_code_is_reuse_not_collision`(関数): 既存 ``ResultCode`` の名前は**再利用**(不採用にしない)。別名前空間の名前は衝突。
  - `test_far_word_is_not_a_duplicate_and_keeps_the_column`(関数): 距離が遠い語は重複でない。文字が 1 つも一致しない語は最近傍を**空**にする。
  - `test_fingerprints_are_six_and_record_the_model`(関数): 決定 G: 指紋 6 つ/決定 K: 裁定モデル名・温度・エンドポイント数を記録。
  - `test_load_registry_rejects_a_foreign_json`(関数)
  - `test_main_writes_json_and_md_without_absolute_paths`(関数): ``drafts.json`` と ``report.md`` が出て、**絶対パスを含まない**。
  - `test_missing_required_field_is_rejected`(関数): 必須欄(決定 B (b))が欠けたら不採用。理由に欄名が出る。
  - `test_mock_adjudicator_is_deterministic_and_empty_by_design`(関数): mock は**決定論の定型**(意味を作らない)。2 回呼んでバイト一致。
  - `test_near_existing_surface_is_judged_dictionary_row`(関数): 既存表層に近い語(距離 ≥ 0.75)は「辞書行の追加で済む」= 新語ではない(s5)。
  - `test_policy_json_is_a_faithful_copy_of_the_dictionary`(関数): ``synonym_policy_v0.json`` は段0 辞書の写し(本文 §2・§3 と一致)。
  - `test_prompt_is_the_frozen_template_plus_json_spec`(関数): 起草プロンプトは ``ADJUDICATION_TEMPLATE`` の前半を再利用した固定文。
  - `test_rank_is_the_coverage_of_agents_cells_hours`(関数): 順位は 体数×セル数×時間帯数(件数=行数ではない)。決定 A (c)。
  - `test_review_keyword_is_auto_rejected`(関数): 保存則・性能予算に触れる語(§7 段3)は自動不採用。
  - `test_two_runs_are_merged_by_sum_of_rows_and_union_of_coverage`(関数): seed 1/2 の合算: 行数は和・体は (由来, id) の併合・セル/時間帯は併合。
- import している内部モジュール: `shibuya.cli`・`shibuya.llm`・`shibuya.llm.undefined`

## [test_registry_from_tape.py](../../../../../../tests/vocab/test_registry_from_tape.py)

``tools/vocab/registry_from_tape.py``(テープ → 未定義台帳 JSON)の検査。

- 公開の関数とクラス
  - `test_ab7_seed1_open_matches_the_parent_report`(関数): AB7 seed 1 open のテープから台帳を再構成すると、親報告 §1 の値に一致する。
  - `test_cell_regex_reads_the_b2_place_block`(関数): セル ID の抽出は [B2 場所] の文面に依る(**取れなければ 0 件**・別の値にはならない)。
  - `test_main_writes_a_relative_path_json`(関数)
  - `test_missing_tape_is_an_error_not_an_empty_ledger`(関数)
  - `test_relative_keeps_outside_paths_as_a_bare_name`(関数): リポジトリ外のパスは**名前だけ**にする(絶対パスを記録に残さない)。
- import している内部モジュール: `shibuya.cli`・`tests/vocab/conftest.py`

## [test_undefined_out.py](../../../../../../tests/vocab/test_undefined_out.py)

``python -m shibuya.cli --undefined-out PATH``(D-71 段2 バッチの入力口)の検査。

- 公開の関数とクラス
  - `test_default_run_does_not_write_the_undefined_ledger`(関数): 既定は**書かない**(``--census-out`` と同じ作法)。
  - `test_payload_is_a_pure_function_of_the_registry`(関数): ``undefined_registry_payload`` は台帳だけから決まる純関数(集計の式を固定する)。
  - `test_payload_without_a_registry_is_empty_not_guessed`(関数): 台帳の無いラン(スタブ)は**空で返す**(推測で埋めない)。
  - `test_undefined_out_does_not_move_the_checkpoint_series`(関数): **既定経路のバイト不変**: ``--undefined-out`` を足しても checkpoint 列は同じ。
  - `test_undefined_out_writes_the_batch_input`(関数): 渡すと JSON が出る。版・記録リング・集計・カウンタが揃う。
- import している内部モジュール: `shibuya.cli`・`shibuya.llm`・`shibuya.llm.undefined`
- 決定の ID: D-71・第 277
