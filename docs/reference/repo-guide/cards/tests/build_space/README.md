# tests/build_space

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 3 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../tests/build_space/__init__.py)

(冒頭の説明なし)

## [synth.py](../../../../../../tests/build_space/synth.py)

合成の小さな面のナビメッシュ(段 1 の試験の材料・データ不要)。

- 公開の関数とクラス
  - `build_synth`(関数)
  - `cells`(関数)
  - `dem`(関数)
  - `edges_list`(関数)
  - `fake_assets`(関数): ``engine.space.nav1.NavSpace`` が読む資産の形(W1 と W2 の一部)。
  - `floors`(関数)
- import している内部モジュール: `shibuya.build.space.navmesh1`・`shibuya.build.space.raster`
- 読む試験: `tests/build_space/test_navmesh1_units.py`・`tests/engine/space/test_nav1_density.py`・`tests/engine/space/test_nav1_units.py`

## [test_navmesh1_units.py](../../../../../../tests/build_space/test_navmesh1_units.py)

段 1 ナビメッシュの構築の部品(合成の小さな面・データ不要)。

- 公開の関数とクラス
  - `synth_mesh`(関数)
  - `test_b9_ramp_limit_is_1_12_and_1_8_under_16_cm`(関数)
  - `test_bfs_nearest_label_spreads_inside_allow_only`(関数)
  - `test_cell_mapping_and_band_fallback`(関数)
  - `test_close_gaps_fills_corner_touch_and_one_metre_gap`(関数)
  - `test_edt_inside_known_distances`(関数)
  - `test_fill_capsule_width_and_if_zero_priority`(関数)
  - `test_fill_polygon_square_area_and_hole`(関数)
  - `test_m1_function_2_3_are_trunk_first_and_9020_keeps_the_w1_copy`(関数)
  - `test_m3_fill_nearest_maps_cell_less_squares_to_the_nearest_ground_cell`(関数)
  - `test_m3_mask_by_cells_removes_the_cell_less_squares_only`(関数)
  - `test_m3_synth_surface_is_inside_the_cells`(関数)
  - `test_min_area_rect_of_rotated_square`(関数)
  - `test_runs_portals_strips_and_components`(関数)
  - `test_short_gaps_only_bounded_and_short`(関数)
  - `test_sr10_feature_rules`(関数)
  - `test_synth_assets_and_gates`(関数)
  - `test_synth_build_twice_same_sha`(関数)
  - `test_synth_routes_inside_and_across_floors`(関数)
- import している内部モジュール: `shibuya.build.space.mesh`・`shibuya.build.space.navmesh1`・`shibuya.build.space.raster`・`shibuya.world.model.navmesh`・`shibuya.world.model.navmesh_route`・`tests/build_space/synth.py`
- 決定の ID: 第 219
