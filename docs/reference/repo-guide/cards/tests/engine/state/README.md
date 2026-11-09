# tests/engine/state

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 4 本・その他 2 本(このディレクトリの直下)

その他のファイル: `class_ids_frozen.json`・`names_frozen.json`

## [__init__.py](../../../../../../../tests/engine/state/__init__.py)

(冒頭の説明なし)

## [test_class_ids.py](../../../../../../../tests/engine/state/test_class_ids.py)

移す段 1(返事その 7 §4-2 の 3・計画 docs/reference/package-map-final-2026-11-09.md §7-1): クラスの名の固定の表。

- 公開の関数とクラス
  - `src_classes`(関数)
  - `test_entry_functions_go_through_the_table`(関数)
  - `test_every_allowed_class_name_is_rebuilt`(関数)
  - `test_excluded_classes_never_reach_a_hash_or_the_state_file`(関数): 載せないクラスは今の名を返す。持つ行(出来事の記録 E・実験の層 X)は軸 1 diag・軸 2 discardable(ハッシュにも状態の
  - `test_one_to_one_and_back_to_the_current_name`(関数)
  - `test_pretend_move_keeps_a_short_run_and_resume`(関数)
  - `test_pretend_move_keeps_hash_state_file_and_fingerprint_bytes`(関数)
  - `test_table_keys_are_exactly_the_classes_in_src`(関数)
  - `test_values_match_the_frozen_json`(関数)
- import している内部モジュール: `shibuya.core.types`・`shibuya.engine.arbiter`・`shibuya.engine.class_ids`・`shibuya.engine.events.log`・`shibuya.engine.resume`・`shibuya.engine.run`・`shibuya.engine.scheduler`・`shibuya.engine.state_codec`・`shibuya.engine.state_hashes`・`shibuya.engine.state_ledger`・`shibuya.engine.systems.probe`

## [test_move_prep_stage2.py](../../../../../../../tests/engine/state/test_move_prep_stage2.py)

移す段 2-2〜2-5(返事その 7 §4-2・計画 docs/reference/package-map-final-2026-11-09.md §7-3): 下ごしらえ(結果は変えない)。

- 公開の関数とクラス
  - `test_find_upward_walks_from_the_start_directory`(関数)
  - `test_index_refuses_a_function_name_split_across_files`(関数)
  - `test_only_core_paths_reads_dunder_file_on_the_run_side`(関数)
  - `test_readers_resolve_the_same_files_as_before`(関数)
  - `test_resolve_files_list_reads_the_resolve_module`(関数)
  - `test_rng_aliases_follow_the_module_name`(関数): 置き場を替えたふり(名だけ替える)でも、3 つの import の形の呼び手を見つける。
  - `test_rng_audit_names_come_from_the_rng_module`(関数)
  - `test_roots_are_the_same_paths_as_before`(関数)
  - `test_static_check_names_come_from_the_modules`(関数)
  - `test_world_catalog_package_name_comes_from_the_module`(関数)
- import している内部モジュール: `shibuya`・`shibuya.core.budget`・`shibuya.core.paths`・`shibuya.core.rng`・`shibuya.engine.bridging.ledger`・`shibuya.engine.bridging.scan`・`shibuya.engine.classical`・`shibuya.engine.energy`・`shibuya.engine.resolve`・`shibuya.engine.resume`・`shibuya.engine.rng_audit`・`shibuya.engine.rules.table`・`shibuya.engine.systems`・`shibuya.engine.systems.allow`・`shibuya.engine.systems.static_check`・`shibuya.manifest.world_catalog`・`shibuya.world.processes.constitution`

## [test_names_frozen.py](../../../../../../../tests/engine/state/test_names_frozen.py)

移す段 2-1(返事その 7 §4-2 の 3・計画 docs/reference/package-map-final-2026-11-09.md §7-2): 名前を変えてはいけない文字列。

- 公開の関数とクラス
  - `test_frozen_file_has_the_declared_shape`(関数)
  - `test_hash_headers_are_the_frozen_multiset`(関数)
  - `test_other_path_shaped_names_are_kept_by_value`(関数)
  - `test_path_shaped_rng_domains_are_kept_by_value`(関数)
  - `test_rng_domain_tables_keep_their_keys`(関数)
  - `test_version_ids_are_the_frozen_multiset`(関数)
- 決定の ID: 第 346
