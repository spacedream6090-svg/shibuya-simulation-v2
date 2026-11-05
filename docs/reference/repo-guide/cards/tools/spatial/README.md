# tools/spatial

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 3 本・その他 0 本(このディレクトリの直下)

## [jgd_plane.py](../../../../../../tools/spatial/jgd_plane.py)

jgd_plane — 平面直角座標系(JGD2011)と緯度経度の換算(numpy だけ)。

- 公開の関数とクラス
  - `latlon_to_plane`(関数): (緯度, 経度) [度] → 平面直角座標 (x=北, y=東) [m]。配列可(検算と試験の合成に使う)。
  - `plane_to_latlon`(関数): 平面直角座標 (x=北, y=東) [m] → (緯度, 経度) [度]。配列可。
- 呼び手: `tools/spatial/las_pointcloud_agg.py`
- 読む試験: `tests/tools/test_las_pointcloud_agg.py`

## [las_io.py](../../../../../../tools/spatial/las_io.py)

las_io — LAS 1.2(Point Data Format 0〜3)を標準ライブラリ+numpy で読む(laspy・PDAL を使わない)。

- 公開の関数とクラス
  - `LasFormatError`(クラス): LAS の形が想定(1.2・PF 0〜3・大きさの整合)と違う。
  - `LasHeader`(クラス)
  - `build_las_bytes`(関数): 試験用: 点の配列 → LAS 1.2 のバイト列(ヘッダ 227 B + VLR(GeoKey)+ 点)。offset は 0。
  - `parse_header`(関数): ファイルの先頭(ヘッダと VLR を含む長さ)→ ``LasHeader``。
  - `read_points`(関数): LAS のファイル → (ヘッダ, 点の memmap)。大きさ = offset + n × record を確かめる。
- 呼び手: `tools/spatial/las_pointcloud_agg.py`
- 読む試験: `tests/tools/test_las_pointcloud_agg.py`
- 決定の ID: 11-02

## [las_pointcloud_agg.py](../../../../../../tools/spatial/las_pointcloud_agg.py)

las_pointcloud_agg — 東京都 区部点群(航空レーザ 2023・LAS)→ 520 セルの床の高さ・坂・歩道の面の集計。

- 公開の関数とクラス
  - `AggParams`(クラス)
  - `Grid`(クラス): 520 セルの (ix, iy) の柱(453)と、柱の番号の引き表。
  - `MeshPartial`(クラス)
  - `TileStore`(クラス): 柱ごとの 0.25 m の DEM/DSM(図郭をまたいで min/max で合わせる)。
  - `aggregate`(関数): 柱ごとの集計 → 520 セルの行・橋梁の構造ごとの行・全体の要約。
  - `axis_check`(関数): LAS の X/Y が第 9 系の東/北か(箱の経緯度を図郭の索引と比べる)。
  - `bin_mesh`(関数): 1 図郭の LAS → 柱ごとの 0.25 m の DEM(Class 2 の最低)・DSM(全点の最高)・Class の数。
  - `build_fill_mosaic`(関数): 柱の DEM・DSM → 全体の res [m] のモザイク(DEM は穴を押し引きで埋めた版と生の版・DSM は最高)。
  - `detect_steps`(関数): 0.25 m の DEM の「平ら→段(0.10〜0.25 m)→平ら」→ (段の両側の画素の印, 段の辺の数, 判定できた辺の数)。
  - `extract_las`(関数): zip の一覧を確かめてから ``las_dir/<MESH>.las`` に展開(既にあり大きさが同じなら使い回す)。
  - `fill_polygon_window`(関数): 多角形(環の並び・偶奇則=穴を含む)→ 窓 (ny, nx) の中の画素の中心が内側か。
  - `fill_push_pull`(関数): NaN の穴を「押し引き」で埋める(2×2 の重みつき平均で粗くし、粗い値で細かい穴を埋める)。
  - `latlon_to_local_arr`(関数): 経緯度 → 世界の平面 (x=東, y=北) [m]\(common.latlon_to_local の配列版)。
  - `load_cells`(関数)
  - `load_mesh_index`(関数): lp_mesh_selected_520cells.json → {図郭: {bbox_WSEN, url, ...}}。
  - `load_plateau_inputs`(関数): PLATEAU の道路の面(歩道・車道)・建物の外形・橋梁の外形 → 柱ごとの画素。無ければ空(記録に注)。
  - `local_to_latlon`(関数)
  - `local_to_plane`(関数): 世界の平面 → 第 9 系 (東, 北)(試験の合成と検算)。
  - `main`(関数)
  - `mesh_local_rect`(関数)
  - `parse_fetch_log`(関数): ``_fetch_log.tsv`` → ({図郭: 完了の行(最初のもの)}, 無視した行)。完了=sha256 が 64 桁・bytes=expected。
  - `peak_rss_bytes`(関数): いまの作業集合と最大(Windows は psapi・ほかは resource)。
  - `plane_to_local`(関数): 第 9 系 (東=LAS X, 北=LAS Y) → 世界の平面。
  - `rasterize_bridges`(関数): PLATEAU 橋梁 LOD2 の構造ごとの三角形 → ({柱: 構造の番号 int16 (-1=無し)}, {柱: 上面の高さ float32})。
  - `rasterize_building_mask`(関数): PLATEAU 建物の三角形(壁を除く)→ {柱: bool の外形(1 画素広げる)}。
  - `rasterize_polygons`(関数): 多角形の並び → {柱: (TILE, TILE) bool}(内側の画素)。
  - `run`(関数)
  - `sample_triangles`(関数): 三角形 (n, 3, 3) → 面の上の格子点 (m, 3) と三角形の番号 (m,) を束で返す(最長辺 / step の重心格子)。
- import している内部モジュール: `shibuya.build.geo.common`・`shibuya.build.space.sources`・`tools/instruments/read_guard.py`・`tools/spatial/jgd_plane.py`・`tools/spatial/las_io.py`
- 読む試験: `tests/tools/test_las_pointcloud_agg.py`
- 読む試験(道筋で): `tests/tools/test_repo_guide.py`
- CLI の引数
  - `--cells`
  - `--jobs`
  - `--mesh-index`
  - `--meshes`: カンマ区切り。省けば取得ログで完了した全部
  - `--nav-dem`
  - `--nav-meta`
  - `--no-rasters`
  - `--out`
  - `--plateau-dir`
  - `--plateau-udx`
  - `--raw-dir`
- 決定の ID: 10-06・11-02・R-82・R-119・R-119 #11
