# tests/bench

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 2 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../tests/bench/__init__.py)

(冒頭の説明なし)

## [test_refr20b_tool.py](../../../../../../tests/bench/test_refr20b_tool.py)

第 2 期 2-0b の道具 ``docs/bench/analysis/wallbounce-1012/refr20b/tools/measure_refractory.py`` の試験(data 不要)。

- 公開の関数とクラス
  - `M`(関数)
  - `test_activity_gate_and_scale_check_from_synthetic_rows`(関数)
  - `test_activity_gate_count_is_carried_into_the_row_and_table`(関数)
  - `test_arm_names_and_plan`(関数)
  - `test_compare_rows_finds_only_real_differences`(関数)
  - `test_eleven_flags_are_accepted_by_parse_refractory_scale`(関数)
  - `test_extrapolate_known_answer`(関数)
  - `test_factor_zero_means_no_suppression_in_the_arbiter`(関数): 既知の答え: 1 刻み前に条件 i で呼んだ体 i が、いま同じ条件 i で起きる。
  - `test_gates_outside_table_symbols_are_defined_in_their_files`(関数): 表の外の門の一覧: 名と出典だけ・出典は「ファイル+記号」(行番号なし)・その記号の定義がファイルに実在する。
  - `test_rank_of_eleven_c_arms_breaks_ties_by_condition_index`(関数)
  - `test_seed_spread`(関数)
  - `test_table_from_three_synthetic_manifests_is_deterministic`(関数)
  - `test_write_outputs_writes_json_and_markdown_without_absolute_paths`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.cli`・`shibuya.engine.arbiter`・`shibuya.engine.resolve`
- 決定の ID: D-56・D-62・D-66
