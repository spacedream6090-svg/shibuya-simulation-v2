# src/shibuya/manifest

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 2 本・その他 0 本(このディレクトリの直下)

下のディレクトリ: [frozen](frozen/README.md)

## [__init__.py](../../../../../../../src/shibuya/manifest/__init__.py)

(冒頭の説明なし)

- 読む試験(道筋で): `tests/tools/test_pkgmove.py`

## [world_catalog.py](../../../../../../../src/shibuya/manifest/world_catalog.py)

世界カタログ v0.2(世界被覆指標の**分母**)の実行時リーダ。

- 公開の関数とクラス
  - `WorldCatalog`(クラス): 凍結された世界カタログ。
  - `load_world_catalog`(関数): 同梱 JSON から凍結カタログを読む。
  - `verify_frozen`(関数): 凍結値との一致を検査する(分母が黙って動いていないことの門)。
- 呼び手: `shibuya.build.audit.w18_coverage`・`shibuya.world.processes.registry`
- 読む試験: `tests/build_audit/test_audit_pipeline.py`・`tests/build_audit/test_audit_units.py`・`tests/engine/state/test_move_prep_stage2.py`・`tests/test_world_catalog_sha.py`・`tests/world/processes/conftest.py`・`tests/world/processes/test_constitution.py`・`tests/world/processes/test_first_batch.py`・`tests/world/processes/test_registry.py`
