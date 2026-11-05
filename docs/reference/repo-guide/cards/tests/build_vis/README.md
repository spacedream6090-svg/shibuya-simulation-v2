# tests/build_vis

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 3 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../tests/build_vis/__init__.py)

(冒頭の説明なし)

## [test_vis_pipeline.py](../../../../../../tests/build_vis/test_vis_pipeline.py)

build.vis の統合テスト(実データ必須・CI では skip)。

- 公開の関数とクラス
  - `built`(関数)
  - `test_headers_declare_expedients_and_catalog`(関数)
  - `test_only_known_gates_fail`(関数)
  - `test_rebuild_is_byte_identical`(関数): D-W20 の T1: W8/W9 を作り直しても出力 sha256 が一致する。
  - `test_w8_band_separation_and_reasonable_visibility`(関数)
  - `test_w8_outputs_and_shapes`(関数)
  - `test_w8_precompute_budget_and_m10`(関数)
  - `test_w9_shadow_planes`(関数)
- import している内部モジュール: `shibuya.build.geo.common`・`shibuya.build.run`・`shibuya.build.vis.run`・`shibuya.build.vis.w9_shadow`・`tests/_data_ids.py`
- 決定の ID: 第 330

## [test_vis_units.py](../../../../../../tests/build_vis/test_vis_units.py)

build.vis の単体テスト(実データ不要)。

- 公開の関数とクラス
  - `test_all_shadow_plane_padding`(関数)
  - `test_los_over_the_wall_when_high_enough`(関数)
  - `test_los_target_own_building_does_not_occlude_itself`(関数)
  - `test_los_wall_blocks_behind_but_not_beside`(関数)
  - `test_packbits_roundtrip`(関数)
  - `test_png_rejects_bad_shapes`(関数)
  - `test_png_roundtrip_gray_and_rgb`(関数)
  - `test_ramp_and_canvas`(関数)
  - `test_rasterize_drops_walls_thinner_than_pitch`(関数): 2.5m ラスタ近似の**既知の穴**: 格子中心を1つも含まない薄い建物は遮蔽に効かない。
  - `test_rasterize_marks_wall_cells_only`(関数)
  - `test_remove_stale_shadows_keeps_only_the_listed_days`(関数): 〔改訂(第330 B5)〕一覧に無い日の影のファイルを消す(エンジンが glob で拾うため)。面の表は残す。
  - `test_sun_azimuth_is_south_at_solar_noon_and_east_in_morning`(関数)
  - `test_sun_vector_matches_w13_elevation`(関数)
  - `test_terrain_occludes`(関数)
- import している内部モジュール: `shibuya.build.field.w13_weather`・`shibuya.build.vis.png`・`shibuya.build.vis.w8_visibility`・`shibuya.build.vis.w9_shadow`
- 決定の ID: 第 330
