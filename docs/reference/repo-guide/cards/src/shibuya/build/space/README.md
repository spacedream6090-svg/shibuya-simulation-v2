# src/shibuya/build/space

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 5 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/build/space/__init__.py)

build.space — 第 5 期 空間の段の構築側(段 1 ナビメッシュ ``navmesh1``)。

- 読む試験(道筋で): `tests/test_places_guard.py`

## [mesh.py](../../../../../../../../src/shibuya/build/space/mesh.py)

build.space.mesh — 塗った格子 → ラン・門・帯(ナビメッシュの形・numba・SR13=自前)。

- 公開の関数とクラス
  - `build_strips`(関数): 1 対 1 でつながるランの縦の鎖 → ランごとの帯の番号(最初のランの順)と、帯をまたぐ門の印。
  - `extract_runs`(関数): ``label != 0`` の行ごとの連なり → (行, x0, x1, 最も多い札) の 4 配列と、行ごとの頭の索引 ``row_ptr`` (ny+1)。
  - `nearest_point_in_comp`(関数): 1 つの階の格子で、成分 ``comp`` のランの中の (x, y) に最も近い点(:func:`world.navmesh.nearest_point` と同じ寄せ方)。
  - `run_overlaps`(関数): 行 j と j+1 のランの重なり → (下のラン, 上のラン, 重なりの x0, 重なりの x1) の 4 配列(列の単位)。
  - `union_find_components`(関数): 節 n 個・辺 (ea, eb) → 連結成分の番号(各成分の最小の節の番号を代表=決定論)。
- 呼び手: `shibuya.build.space.navmesh1`
- 読む試験: `tests/build_space/test_navmesh1_units.py`
- 読む試験(道筋で): `tests/test_places_guard.py`

## [navmesh1.py](../../../../../../../../src/shibuya/build/space/navmesh1.py)

build.space.navmesh1 — 第 5 期 空間の段 1: 多層の歩ける面のナビメッシュを組む(脇の段・``build.run`` の段の外)。

- 公開の関数とクラス
  - `FloorRaster`(クラス): 1 つの階の塗り(札 uint8)と高さ(float32・NaN=未設定)。
  - `build`(関数): 材料を読んで ``out_dir`` に ``nav1_*`` と ``navmesh1.header.json`` を書く(既存の世界の資産は書き換えない)。
  - `main`(関数)
- import している内部モジュール: `shibuya.build.geo.common`・`shibuya.build.space.mesh`・`shibuya.build.space.raster`・`shibuya.build.space.sources`・`shibuya.foundation.time_consts`・`shibuya.world.navmesh`
- 読む試験: `tests/build_space/synth.py`・`tests/build_space/test_navmesh1_units.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- CLI の引数
  - `--data`
  - `--out`
  - `--params`: 既定の値を上書きする JSON
  - `--world`
- 決定の ID: 10-03/§8・10-06/§2・R-64・第 219

## [raster.py](../../../../../../../../src/shibuya/build/space/raster.py)

build.space.raster — 歩ける面の格子(0.5 m)に多角形・帯・三角形を塗る numba の部品(段 1・SR13=自前・依存を足さない)。

- 公開の関数とクラス
  - `Grid`(クラス): 格子の原点・目・大きさ(``nx`` 列 × ``ny`` 行)。原点は ``res`` の倍数に丸めて置く(階をまたいで目がそろう)。
  - `bfs_nearest_label`(関数): ``seed`` の 0 でない札を ``allow != 0`` の目の中で 4 近傍に広げる(先に届いた札が勝つ=幅優先・同じ段は行列の順)。
  - `edt_inside`(関数): ``mask != 0`` の目から ``mask == 0`` の目(の中心)までの距離[m]\(float32・印の無い目は 0)。
  - `fill_capsule`(関数): 線分 (x0,y0)-(x1,y1) から ``half_w`` 以内の目を塗る。``allow`` は :func:`fill_polygon` と同じ。
  - `fill_polygon`(関数): 偶奇の走査線で多角形を塗る。``allow`` が空(長さ 0)でなければ ``allow[j, i] != 0`` の目だけ。
  - `fill_triangles_z`(関数): 三角形 ``tri`` (n, 3, 3)=(x, y, z) の中の目に重心座標の高さを書く。``keep_max`` なら既にある値と大きい方。
  - `polygon_edges`(関数): 環(外周と穴・閉じていてもいなくてもよい)の並び → 辺の 4 配列(:func:`fill_polygon` の入力)。
- 呼び手: `shibuya.build.space.navmesh1`
- 読む試験: `tests/build_space/synth.py`・`tests/build_space/test_navmesh1_units.py`
- 読む試験(道筋で): `tests/test_places_guard.py`

## [sources.py](../../../../../../../../src/shibuya/build/space/sources.py)

build.space.sources — 段 1 のナビメッシュの材料を読む(手元のファイルだけ・ネットワークは使わない)。

- 公開の関数とクラス
  - `Road`(クラス): ``tran:Road`` 1 つ(LOD1 の面と、子の交通領域の LOD2/3 の面)。
  - `iter_w1_edges`(関数): W1 の辺(番号の順)=dict(edge, u, v, klass, band_u, band_v, layer, xy (n,2))。
  - `read_brid_triangles`(関数): 橋梁 LOD2 の構造ごとの三角形 → [(n, 3, 3) の (x, y, 標高)] の並び。
  - `read_dem_triangles`(関数): ``udx/dem/*.gml`` の TIN の三角形 → (n, 3, 3) の (x, y, 標高)。``bbox`` に頂点の掛かるものだけ(先頭の点で粗く絞る)。
  - `read_frn`(関数): ``udx/frn/*.gml`` → (横断歩道 1110 の頂点 (n,3) の並び, 地下出入口 4020 の頂点 (n,3) の並び, 統計)。
  - `read_hokoukukan_2020`(関数): 歩行空間ネットワーク 2020 → (リンクの並び=dict(props, xy), ノード id → dict(floor, x, y))。
  - `read_osm_walk`(関数): OSM の歩行系の生データ → (線の並び, 点の並び)。線=dict(id, tags, xy (n,2))・点=dict(id, tags, x, y)。id の順。
  - `read_tran_roads`(関数): ``udx/tran/*.gml`` → 範囲 ``bbox`` に掛かる ``tran:Road`` の並び(ファイル名の順・ファイルの中の順=決定論)。
  - `read_ubld_floor_triangles`(関数): 地下街 LOD4.1 の床の三角形 → ((n, 3, 3) の (x, y, 標高), 層の高さ[m 標高] の配列, 統計)。
  - `to_local`(関数): 緯度経度 → 世界の平面座標 [m]\(W0 の CRS と同じ式)。
- import している内部モジュール: `shibuya.build.geo.common`
- 呼び手: `shibuya.build.space.navmesh1`・`tools/spatial/las_pointcloud_agg.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 決定の ID: R-119
