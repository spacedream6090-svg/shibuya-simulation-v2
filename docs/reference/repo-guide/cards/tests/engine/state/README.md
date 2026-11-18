# tests/engine/state

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 6 本・その他 3 本(このディレクトリの直下)

その他のファイル: `class_ids_frozen.json`・`mind_world_reads_frozen.json`・`names_frozen.json`

## [__init__.py](../../../../../../../tests/engine/state/__init__.py)

(冒頭の説明なし)

## [shaped_names.py](../../../../../../../tests/engine/state/shaped_names.py)

移す段 2-1 の拾い(検収 M4): 短いランの manifest・run_meta・テープの見出し・ハッシュに入る文字列から、モジュールの道の形の部分を拾う。凍結(``names_frozen.json`` の ``run_path_shaped``)の道具と試験が使う(試験の本体ではない)。

- 公開の関数とクラス
  - `collect_here`(関数): このプロセスで構成 ``name`` を回して拾う(子のプロセスの中で呼ぶ=ハッシュの口を差し替える)。
  - `run_config`(関数): 子のプロセスで構成 ``name`` を回して拾った結果(``repo`` で回す=data の相対の道筋・``src`` を読む)。
  - `shaped`(関数): 文字列の中の道の形の部分(出てくる順)。
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.run`・`shibuya.runtime.state.hashes`
- 読む試験: `tests/engine/state/test_names_frozen.py`
- CLI の引数
  - `sys.argv` を直接読む
- 環境変数: `SHIBUYA_CALENDAR`・`SHIBUYA_CALENDAR_2`・`SHIBUYA_CALENDAR_3`・`SHIBUYA_CONTACT`・`SHIBUYA_CONTACT_HABIT`・`SHIBUYA_DECISION_PORT`・`SHIBUYA_DUTIES`・`os.environ` をまるごと使う

## [test_class_ids.py](../../../../../../../tests/engine/state/test_class_ids.py)

移す段 1(返事その 7 §4-2 の 3・計画 docs/reference/package-map-final-2026-11-09.md §7-1): クラスの名の固定の表。

- 公開の関数とクラス
  - `src_classes`(関数): (「モジュール.クラス名」→ ``__qualname__``, 置き場で凍結の名を宣言するクラスの名)。
  - `test_allowed_class_refuses_a_path_that_points_to_another_class`(関数): 検収 M6: 凍結の名の import 先(``_PATH_OF``)が別のクラスを指せば ``StateFormatError`` で止まる。
  - `test_cp12_type_keeps_its_frozen_name_on_the_probe_path`(関数): 検収 M1: 実験の条件の型は表に書けない(CP12)ので置き場で凍結の名を宣言する。probe の外の状態の digest の経路
  - `test_default_run_resume_and_probe_meet_no_unknown_shibuya_type`(関数): 検収 M2: 止める口を数える口に替えて、既定のラン(止めて再開)と系ごとの指紋つきのランを回す=表に無い型 0 件。
  - `test_entry_functions_go_through_the_table`(関数)
  - `test_every_allowed_class_name_is_rebuilt`(関数)
  - `test_frozen_json_maps_each_value_to_the_qualname_of_its_class`(関数)
  - `test_one_to_one_and_back_to_the_current_name`(関数)
  - `test_pretend_move_keeps_a_short_run_and_resume`(関数)
  - `test_pretend_move_keeps_hash_state_file_and_fingerprint_bytes`(関数)
  - `test_swapping_two_values_is_caught`(関数): 突然変異(``ActivityKind`` と ``AgentKind`` の値の入れ替え)を、名の集合でなく写像が落とす。
  - `test_table_keys_and_declarations_are_exactly_the_classes_in_src`(関数)
  - `test_unknown_shibuya_types_stop_and_others_keep_their_names`(関数)
- import している内部モジュール: `shibuya.engine.run`・`shibuya.foundation.journal.log`・`shibuya.foundation.ports.experiment_gate`・`shibuya.foundation.queues.scheduler`・`shibuya.foundation.types`・`shibuya.mind.system1.wake`・`shibuya.runtime.state.class_ids`・`shibuya.runtime.state.codec`・`shibuya.runtime.state.hashes`・`shibuya.runtime.state.resume`・`shibuya.runtime.systems.probe`

## [test_mind_world_reads.py](../../../../../../../tests/engine/state/test_mind_world_reads.py)

心の読みの一覧の固定(返事その 7 §4-2 の 2・計画 docs/reference/mind-world-reads-2026-11-09.md §9・11-16 の裁定)。

- 公開の関数とクラス
  - `compare`(関数): 組ごとの違い(空なら同じ)。
  - `defined_symbols`(関数): 最上位の関数・クラス・``クラス.メソッド`` の名。
  - `frozen`(関数)
  - `frozen_counts`(関数)
  - `load_frozen`(関数)
  - `main`(関数): 今の ``key_counts`` を JSON で出す(表を直すときの材料。表の注 ``other_object`` と ``owner`` は手で合わせる)。
  - `mind_reads`(関数): 走査の結果 → (鍵 → 数, 割り先を引けない読みの場所)。
  - `split_dest`(関数): 割るファイルの記号 → 割り先(記号の完全一致 → クラスの名 → 最上位の文は最初の割り先)。引けなければ None。
  - `symbols_by_line`(関数): 行 → 囲む最上位の関数・クラス・``クラス.メソッド`` の名(最上位の文は空)。
  - `test_mind_reads_match_the_frozen_table`(関数): 今の心の読みが、固定の表と組ごとに同じ(増えても減っても落ちる・落ちたら文の直し方に従う)。
  - `test_negative_controls`(関数): 負の対照: 読みが 1 つ増えると「増えた」、1 つ減ると「減った」、割り先を引けない読みは unknown に出る。
  - `test_other_object_notes_point_at_frozen_keys`(関数): 別物(列と同じ名の別の物の欄)の注は、表の組の数の内側にある。
  - `test_owner_table_covers_the_declared_columns`(関数): 持ち主の表が宣言の列(``agents``)と同じ集合で、重ならない。
  - `test_scope_is_current`(関数): 範囲の表が今の木を指している。割る段で割るファイルが無くなったら、ここで落ちる(割り先の表を作り直す)。
- import している内部モジュール: `shibuya.runtime.state.ledger_ast`・`tests/_places.py`
- 決定の ID: 11-16

## [test_move_prep_stage2.py](../../../../../../../tests/engine/state/test_move_prep_stage2.py)

移す段 2-2〜2-5(返事その 7 §4-2・計画 docs/reference/package-map-final-2026-11-09.md §7-3): 下ごしらえ(結果は変えない)。

- 公開の関数とクラス
  - `test_find_upward_walks_from_the_start_directory`(関数)
  - `test_index_refuses_a_function_name_split_across_files`(関数)
  - `test_index_refuses_a_table_name_split_across_files_and_merges_distinct_ones`(関数): 〔検収 L2〕頂上の表の名(関数を指す代入)がファイルをまたいで重なれば止める。重ならなければ 2 本を 1 つの閉包にする。
  - `test_only_core_paths_reads_dunder_file_on_the_run_side`(関数)
  - `test_readers_resolve_the_same_files_as_before`(関数)
  - `test_resolve_files_list_reads_the_resolve_module`(関数)
  - `test_rng_aliases_follow_the_module_name`(関数): 置き場を替えたふり(名だけ替える)でも、3 つの import の形の呼び手を見つける。
  - `test_rng_audit_names_come_from_the_rng_module`(関数)
  - `test_roots_are_the_same_paths_as_before`(関数)
  - `test_static_check_names_come_from_the_modules`(関数)
  - `test_world_catalog_package_name_comes_from_the_module`(関数)
- import している内部モジュール: `shibuya`・`shibuya.engine.resolve`・`shibuya.foundation.budget`・`shibuya.foundation.decl.bridging`・`shibuya.foundation.paths`・`shibuya.foundation.rng`・`shibuya.mind.judge.classical`・`shibuya.runtime.state.ledger_ast`・`shibuya.runtime.state.resume`・`shibuya.runtime.systems.allow`・`shibuya.validation.static.bridging_scan`・`shibuya.validation.static.rng_audit`・`shibuya.validation.static.system_static_check`・`shibuya.world.body.energy`・`shibuya.world.facts.rules.table`・`shibuya.world.ledger.constitution`・`shibuya.world.ledger.world_catalog`・`tests/_places.py`

## [test_names_frozen.py](../../../../../../../tests/engine/state/test_names_frozen.py)

移す段 2-1(返事その 7 §4-2 の 3・計画 docs/reference/package-map-final-2026-11-09.md §7-2): 名前を変えてはいけない文字列。

- 公開の関数とクラス
  - `test_frozen_file_has_the_declared_shape`(関数)
  - `test_hash_headers_are_the_frozen_multiset`(関数)
  - `test_other_path_shaped_names_are_kept_by_value_and_count`(関数)
  - `test_path_shaped_rng_domains_are_kept_by_value_and_count`(関数)
  - `test_rng_domain_tables_keep_their_keys`(関数)
  - `test_run_outputs_contain_exactly_the_frozen_path_shaped_names`(関数): 短いランの manifest・run_meta・テープの見出し・ハッシュから拾った道の形の部分が凍結と同じ(検収 M4)。
  - `test_shaped_pattern_finds_both_forms_inside_japanese_text`(関数)
  - `test_version_ids_are_the_frozen_multiset`(関数)
- import している内部モジュール: `shibuya`・`tests/engine/state/shaped_names.py`
- 決定の ID: D-118・第 346・第 347
