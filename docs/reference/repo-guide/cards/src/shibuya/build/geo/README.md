# src/shibuya/build/geo

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 12 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/build/geo/__init__.py)

build.geo — 世界データ構築 W0-W6/W11(地理レーン)。

- 呼び手: `shibuya.build.geo.run`・`shibuya.build.run`
- 読む試験: `tests/build_geo/test_geo_pipeline.py`
- 読む試験(道筋で): `tests/test_places_guard.py`

## [common.py](../../../../../../../../src/shibuya/build/geo/common.py)

build.geo.common — 全段階で共有する純粋ヘルパ(ハッシュ・ヘッダ・座標・格子・層バンド)。

- 公開の関数とクラス
  - `Ctx`(クラス): 段階の実行文脈(入力データ根・出力先)。
  - `Gate`(クラス): 機械検査1件。``expected`` が None のときは「報告のみ(仕様書の空欄)」。
  - `StageResult`(クラス)
  - `band_of_layer`(関数): OSM layer 素値 → バンド。未タグ(None)は 0 とみなす(D-W3)。
  - `canonical_json_bytes`(関数): canonical JSON(キー整列・空白なし・UTF-8・非ASCIIはそのまま)。
  - `grid_ij`(関数): 座標 → 100m 格子の (ix, iy)。格子原点=世界原点、床関数。
  - `input_hash`(関数): 入力ファイル群の SHA256 を **与えられた順に** 連結して再ハッシュする。
  - `latlon_to_local`(関数): WGS84 (lat, lon) → 世界ローカル平面 (x=東, y=北) [m]。
  - `load_json`(関数)
  - `node_layer_from_incident`(関数): 接続エッジ層の多数決 → ノード層(D-W3)。
  - `param_hash`(関数)
  - `place_id`(関数): セル ID 文字列 ``g{ix}_{iy}_{band}``(D-W2)。
  - `read_parquet_columns`(関数): Parquet → 列辞書(Python リスト)。段階間の受け渡し用。
  - `sha256_bytes`(関数)
  - `sha256_file`(関数)
  - `stage_header_paths`(関数): 置き場の段の見出し(``W<番号>.header.json``)を番号の順に。〔第 4 期 4-3〕W21 の続きの段(``W21b``・``W21c``・``W21apply``
  - `write_header`(関数)
  - `write_json`(関数)
  - `write_npy`(関数)
  - `write_npz`(関数): 非圧縮 .npz。``np.savez`` は zip 内に日時を書かないので再構築でバイト一致する。
  - `write_parquet`(関数): 列辞書 → Parquet(zstd)。列順=辞書順。
- 呼び手: `shibuya.build.audit.run`・`shibuya.build.audit.w18_coverage`・`shibuya.build.audit.w19_freeze`・`shibuya.build.audit.w20_acceptance_pack`・`shibuya.build.field.common`・`shibuya.build.field.road_names`・`shibuya.build.field.w10_ruler`・`shibuya.build.geo.run`・`shibuya.build.geo.w0_crs`・`shibuya.build.geo.w11_station_exits`・`shibuya.build.geo.w1_walk_graph`・`shibuya.build.geo.w2_cells`・`shibuya.build.geo.w3_distances`・`shibuya.build.geo.w4_heights`・`shibuya.build.geo.w5_entrances`・`shibuya.build.geo.w6_poi_org`・`shibuya.build.lang.common`・`shibuya.build.lang.run`・`shibuya.build.lang.w14_signage`・`shibuya.build.lang.w15_cell_static`・`shibuya.build.pop.run`・`shibuya.build.pop.w16_population`・`shibuya.build.pop.w21_apply`・`shibuya.build.pop.w21_build`・`shibuya.build.pop.w21_build_b`・`shibuya.build.pop.w21_build_c`・`shibuya.build.run`・`shibuya.build.sched.run`・`shibuya.build.sched.trial`・`shibuya.build.sched.w17_schedule`・`shibuya.build.sched.w20_calendar_1a`・`shibuya.build.space.navmesh1`・`shibuya.build.space.sources`・`shibuya.build.vis.run`・`shibuya.build.vis.w8_visibility`・`shibuya.build.vis.w9_shadow`・`tools/build_geo/walkable_area.py`・`tools/c8/sensitivity.py`・`tools/spatial/las_pointcloud_agg.py`
- 読む試験: `tests/build_audit/test_audit_pipeline.py`・`tests/build_audit/test_audit_units.py`・`tests/build_field/test_field_pipeline.py`・`tests/build_field/test_w10_ruler.py`・`tests/build_geo/test_geo_pipeline.py`・`tests/build_geo/test_geo_units.py`・`tests/build_lang/test_w14_signage.py`・`tests/build_lang/test_w15_cell_static.py`・`tests/build_pop/test_pop_pipeline.py`・`tests/build_pop/test_w21_stage10_swap.py`・`tests/build_sched/test_w17_ingest.py`・`tests/build_sched/test_w20_w21_port.py`・`tests/build_vis/test_vis_pipeline.py`・`tests/economy/stage2/test_stage2_rules_credit_atm.py`・`tests/engine/calendar/test_calendar_shadow.py`・`tests/engine/test_weather_calendar_10e.py`・`tests/test_build_run_keep_stage.py`
- 読む試験(道筋で): `tests/test_places_guard.py`

## [poi_class.py](../../../../../../../../src/shibuya/build/geo/poi_class.py)

W6 POI の種別(cat)・サブカテゴリ(subcat)分類。**OSM タグが一次**。

- 公開の関数とクラス
  - `poi_category`(関数): OSM 生タグ → cat(13 種)。判らなければ ``None``。
  - `poi_subcategory`(関数): OSM 生タグ → subcat(閉じた語彙)。判らなければ ``None``。
  - `resolve_subcat`(関数): 1 件の POI の subcat を決める → ``(subcat, source)``。
  - `subcat_from_name`(関数): **expedient**: POI 名 → subcat。``cat`` と矛盾する語は当てない。
  - `tag_index`(関数): Overpass の ``out tags;`` 文書 → ``poi_id`` → 生タグ。
  - `tag_index_by_priority`(関数): 優先順の文書群 → ``poi_id`` → 生タグ。**要素単位で先頭の群が勝つ**。
  - `tag_tier_report`(関数): 新旧 2 群の生タグを POI ごとに比べた件数(W6 の notes 用・決定論)。
- 呼び手: `shibuya.build.geo.w6_poi_org`
- 読む試験: `tests/build_field/test_field_units.py`・`tests/build_geo/test_poi_class.py`・`tests/engine/test_eatery_place_food.py`・`tests/engine/test_intent_chooser.py`
- 読む試験(道筋で): `tests/test_places_guard.py`

## [run.py](../../../../../../../../src/shibuya/build/geo/run.py)

build.geo.run — 段階を W 番号順に実行し、ヘッダと build_manifest.json を書く CLI。

- 公開の関数とクラス
  - `main`(関数)
  - `print_gate_table`(関数)
  - `run_stages`(関数)
  - `write_build_manifest`(関数): out ディレクトリに存在する段階ヘッダから manifest を組む(W 番号順)。
- import している内部モジュール: `shibuya.build.geo`・`shibuya.build.geo.common`・`shibuya.build.geo.w0_crs`・`shibuya.build.geo.w11_station_exits`・`shibuya.build.geo.w1_walk_graph`・`shibuya.build.geo.w2_cells`・`shibuya.build.geo.w3_distances`・`shibuya.build.geo.w4_heights`・`shibuya.build.geo.w5_entrances`・`shibuya.build.geo.w6_poi_org`
- 呼び手: `shibuya.build.audit.run`・`shibuya.build.field.run`・`shibuya.build.lang.run`・`shibuya.build.pop.run`・`shibuya.build.run`・`shibuya.build.sched.run`・`shibuya.build.vis.run`
- 読む試験: `tests/build_geo/test_geo_pipeline.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- CLI の引数
  - `--data`: 入力データ根(既定 data)
  - `--out`: 出力ディレクトリ(例 data/world/v2)
  - `--quiet`
  - `--stage`: 実行する段階(繰り返し可・既定=全段階)

## [w0_crs.py](../../../../../../../../src/shibuya/build/geo/w0_crs.py)

W0 原点・座標系凍結(§1 W0)。

- 公開の関数とクラス
  - `run`(関数)
- import している内部モジュール: `shibuya.build.geo.common`
- 呼び手: `shibuya.build.audit.w19_freeze`・`shibuya.build.geo.run`
- 読む試験(道筋で): `tests/test_places_guard.py`

## [w11_station_exits.py](../../../../../../../../src/shibuya/build/geo/w11_station_exits.py)

W11 駅・出口(§1 W11・D-W13)。

- 公開の関数とクラス
  - `run`(関数)
- import している内部モジュール: `shibuya.build.geo.common`
- 呼び手: `shibuya.build.audit.w19_freeze`・`shibuya.build.geo.run`
- 読む試験(道筋で): `tests/test_places_guard.py`

## [w1_walk_graph.py](../../../../../../../../src/shibuya/build/geo/w1_walk_graph.py)

W1 歩行グラフ(§1 W1・D-W3・D-W4)。

- 公開の関数とクラス
  - `count_components`(関数): 与えられたノード集合・エッジ部分集合の連結成分数(孤立ノードも 1 成分)。
  - `prune_pendants`(関数): 次数1のノードとその接続エッジを反復除去する(ゲート用の中核グラフ)。
  - `run`(関数)
- import している内部モジュール: `shibuya.build.geo.common`
- 呼び手: `shibuya.build.audit.w19_freeze`・`shibuya.build.geo.run`
- 読む試験: `tests/build_geo/test_geo_units.py`
- 読む試験(道筋で): `tests/test_places_guard.py`

## [w2_cells.py](../../../../../../../../src/shibuya/build/geo/w2_cells.py)

W2 セル生成(§1 W2・D-W2)。

- 公開の関数とクラス
  - `run`(関数)
- import している内部モジュール: `shibuya.build.geo.common`
- 呼び手: `shibuya.build.geo.run`
- 読む試験: `tests/build_geo/test_geo_units.py`
- 読む試験(道筋で): `tests/test_places_guard.py`

## [w3_distances.py](../../../../../../../../src/shibuya/build/geo/w3_distances.py)

W3 全点対距離(§1 W3・D-W4)。

- 公開の関数とクラス
  - `build_csr`(関数): 無向辺(平行辺は最小長を採用・自己ループ除去)→ CSR 有向弧。
  - `run`(関数)
- import している内部モジュール: `shibuya.build.geo.common`・`shibuya.foundation.rng`
- 呼び手: `shibuya.build.geo.run`
- 読む試験: `tests/build_geo/test_geo_units.py`
- 読む試験(道筋で): `tests/test_places_guard.py`

## [w4_heights.py](../../../../../../../../src/shibuya/build/geo/w4_heights.py)

W4 建物・高さ(§1 W4・D-W5)。

- 公開の関数とクラス
  - `height_of`(関数): D-W5 の高さ規則。戻り値 = (h_m, src)。
  - `kind_default_h`(関数): kind → 既定高さ [m]\(expedient)。
  - `run`(関数)
- import している内部モジュール: `shibuya.build.geo.common`
- 呼び手: `shibuya.build.audit.w19_freeze`・`shibuya.build.geo.run`
- 読む試験: `tests/build_geo/test_geo_units.py`
- 読む試験(道筋で): `tests/test_places_guard.py`

## [w5_entrances.py](../../../../../../../../src/shibuya/build/geo/w5_entrances.py)

W5 入口点(§1 W5・D-W6)。

- 公開の関数とクラス
  - `nearest_node`(関数): 点群 → 最寄りノード添字と距離(同点は添字の小さい方)。
  - `run`(関数)
- import している内部モジュール: `shibuya.build.geo.common`
- 呼び手: `shibuya.build.audit.w19_freeze`・`shibuya.build.geo.run`
- 読む試験(道筋で): `tests/test_places_guard.py`

## [w6_poi_org.py](../../../../../../../../src/shibuya/build/geo/w6_poi_org.py)

W6 POI・組織の束縛(§1 W6・D-W7)。

- 公開の関数とクラス
  - `run`(関数)
- import している内部モジュール: `shibuya.build.geo.common`・`shibuya.build.geo.poi_class`
- 呼び手: `shibuya.build.audit.w19_freeze`・`shibuya.build.geo.run`
- 読む試験: `tests/build_geo/test_geo_pipeline.py`・`tests/build_geo/test_poi_class.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 決定の ID: D-97・第 281
