# tests/build_audit

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 4 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../tests/build_audit/__init__.py)

(冒頭の説明なし)

## [test_audit_pipeline.py](../../../../../../tests/build_audit/test_audit_pipeline.py)

build.audit の統合テスト(実データ必須・CI では skip)。

- 公開の関数とクラス
  - `built`(関数)
  - `test_build_manifest_carries_assets_and_seal`(関数): build_manifest.json が(W19 ヘッダ経由で)資産表と封印を持つ。
  - `test_full_rebuild_gives_identical_build_hash`(関数): D-W20 の再構築テスト T1(W8 込みなので slow)。
  - `test_stage_order_is_numeric_and_complete`(関数)
  - `test_w18_coverage_index`(関数)
  - `test_w19_freeze_assets_and_seal`(関数)
  - `test_w20_acceptance_pack`(関数)
- import している内部モジュール: `shibuya.build.geo.common`・`shibuya.build.run`・`shibuya.manifest.world_catalog`・`tests/_data_ids.py`

## [test_audit_units.py](../../../../../../tests/build_audit/test_audit_units.py)

build.audit の単体テスト(実データ不要)。

- 公開の関数とクラス
  - `test_alias_and_quantity_maps_point_at_real_classes`(関数)
  - `test_compute_index_commission_and_undercount`(関数)
  - `test_compute_index_known_answers`(関数)
  - `test_compute_index_on_frozen_catalog_is_bounded`(関数)
  - `test_gate_table_markdown_lists_failures`(関数)
  - `test_gate_table_markdown_when_all_pass`(関数)
  - `test_holdout_static_scan_flags_a_planted_reference`(関数)
  - `test_holdout_tokens_cover_all_layers`(関数)
  - `test_math_helpers_are_pure`(関数)
  - `test_parse_depth_and_gate`(関数)
  - `test_parse_n_real`(関数)
  - `test_seal_member_hash_is_deterministic_and_order_free`(関数)
  - `test_upstream_build_hash_is_output_digest_chain`(関数): パックの build_hash = 出力 sha256 を W 番号順に連ねた sha256(build.run と同じ作り方)。
  - `test_w19_assets_are_only_the_files_w13_reads`(関数): 〔改訂(第330 B5)〕W19 の資産表は W13 が実際に読むファイルだけ。``realworld/amedas``(旧の rglob の先・日次取得の
  - `test_w19_assets_never_list_the_realtime_odpt_layer`(関数): 〔第 2 期 2-3b・検収 L1〕負の対照: data 根に ``realworld_live/odpt_rt/``(検証専用)と別の日付の
  - `test_weight_formula_and_cap`(関数)
- import している内部モジュール: `shibuya.build.audit.w18_coverage`・`shibuya.build.audit.w19_freeze`・`shibuya.build.audit.w20_acceptance_pack`・`shibuya.build.field.w12_real_timetables`・`shibuya.build.field.w13_weather`・`shibuya.build.geo.common`・`shibuya.manifest.world_catalog`
- 決定の ID: 第 330

## [test_w19_layer_sources.py](../../../../../../tests/build_audit/test_w19_layer_sources.py)

第333: W19 の「層の元」の表(回答 10-13b §1 1-2)。値は読まない・表だけの試験。

- 公開の関数とクラス
  - `test_build_input_families_come_from_w12_constants`(関数)
  - `test_every_holdout_layer_has_a_source_family`(関数)
  - `test_independence_rows_cover_all_layers_in_order`(関数)
  - `test_shibuya_jinryu_and_boundary_counts_are_marked_not_independent`(関数)
- import している内部モジュール: `shibuya.build.audit.w19_freeze`
- 決定の ID: 10-13b/§1・第 333
