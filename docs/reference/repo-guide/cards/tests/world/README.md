# tests/world

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 2 本・その他 0 本(このディレクトリの直下)

下のディレクトリ: [processes](processes/README.md)

## [__init__.py](../../../../../../tests/world/__init__.py)

world 層のテスト。

## [test_world.py](../../../../../../tests/world/test_world.py)

world のテスト: 合成小世界・資産読み込み・next-hop・セル/POI レジストリ。

- 公開の関数とクラス
  - `test_density_matches_bincount`(関数)
  - `test_density_stage_is_monotone`(関数)
  - `test_load_or_synthetic_falls_back`(関数)
  - `test_missing_assets_raise`(関数)
  - `test_next_hop_reaches_every_target`(関数): 1 tick=1 ノードで必ず目的地に着く(格子は連結)。
  - `test_open_mask_default_hours`(関数)
  - `test_real_assets_load_and_map`(関数)
  - `test_real_assets_routing_is_vectorized`(関数)
  - `test_route_returns_minus_one_for_invalid`(関数)
  - `test_synthetic_is_deterministic`(関数)
  - `test_synthetic_shapes`(関数)
  - `test_world_freeze_guard`(関数)
- import している内部モジュール: `shibuya.world.assets`・`shibuya.world.model.state`
