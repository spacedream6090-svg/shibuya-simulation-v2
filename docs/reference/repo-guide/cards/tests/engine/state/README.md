# tests/engine/state

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 2 本・その他 1 本(このディレクトリの直下)

その他のファイル: `class_ids_frozen.json`

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
