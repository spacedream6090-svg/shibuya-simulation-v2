# tools/build_geo

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 1 本・その他 0 本(このディレクトリの直下)

## [walkable_area.py](../../../../../../tools/build_geo/walkable_area.py)

tools/build_geo/walkable_area.py — C9c-1 歩行可能面積の実測化(セル別 ``walkable_m2``)。

- 公開の関数とクラス
  - `build`(関数): S1〜S7 を通してセル別 ``walkable_m2`` の parquet + ヘッダを書く。
  - `clip_polygon_to_rect`(関数): Sutherland–Hodgman で凸矩形にクリップ(venv に shapely が無いので自前)。
  - `gate_values`(関数): S7 の 3 ゲートを数える(純関数・テストから直接呼ぶ)。
  - `main`(関数)
  - `merge_cell_areas_by_lod`(関数): 同じ function コードの LOD 別セル面積 -> セルごとに 1 つの LOD を選んで束ねる。
  - `polygon_area`(関数): shoelace の絶対値[m²]\(向きは問わない)。
  - `polyline_cell_lengths`(関数): 折れ線 ``(m, 2)`` → ``(ix, iy)`` ごとの長さ[m]\(セル境界で切る)。
  - `read_gml_features`(関数): ``udx/tran/*.gml`` → function コード別の符号つき環(S1/S2 の原文どおり)。
  - `ring_cell_areas`(関数): 符号つき環の列 → ``(ix, iy)`` ごとの面積[m²]\(S3・**セル境界でクリップ**)。
  - `road_surface_width_for_klass`(関数): OSM klass → **道路面の全幅**[m]\(被覆率の分母)。表に無い klass は細街路の 4.0 m。
  - `signed_ring_area`(関数): 環 ``(n, 2)`` の shoelace の絶対値[m²]\(向きは問わない)。
  - `triangle_cell_areas`(関数): 三角形群 ``(n, 3, 2)`` → ``(ix, iy)`` ごとの面積[m²]\(S3・**セル境界でクリップ**)。
  - `unique_triangle_mask`(関数): 量子化整数の三角形 ``(n, 3, 2)`` → **最初の出現だけ True** の真偽配列。
  - `width_for_klass`(関数): OSM klass → (歩行可能幅員[m], 規則名)。表に無い klass は歩道の下限へ。
- import している内部モジュール: `shibuya.build.geo.common`
- 読む試験(道筋で): `tests/build_geo/test_c9c_walkable_area.py`
- CLI の引数
  - `--covered-min-frac`: PLATEAU 被覆と呼ぶ被覆率の下限(既定 0.5・PLATEAU 道路面 / OSM 道路面推定)
  - `--covered-min-m2`: 被覆と呼ぶ歩道部面積の下限[m²]\(診断用・既定 0.0=歩道部が 1 m² でもあれば可)
  - `--dedup`: `--source npz` のときだけ効く。xy=頂点一致の三角形を 1 枚に畳む(既定)/none=畳まない(tran_lod3.json の area_m2_by_class と一致)
  - `--gml-dir`
  - `--lod-merge`: LOD の重なりを落とす粒度。cell=セル × function コードごとに LOD3→LOD2→LOD1 の最初の 1 つだけ採る(既定)/ feature=地物単位の 1 地物 1 LOD だけ(答申 a9 の数え方)
  - `--name`
  - `--out`
  - `--plateau`
  - `--ring-dedup`: 1 地物の中で同じ環が繰り返されているときの扱い。exact=1 枚に畳む(既定・渋谷区 2025 の LOD3 は同じ三角形を 6 回持つ)/ none=畳まない(答申 a9 の数え方)
  - `--sidewalk-min-share`: 被覆と呼ぶ歩道率 sidewalk/(sidewalk+roadway) の下限(既定 0.0=検査しない)
  - `--source`: 面の出所。gml=生 CityGML(既定・区全域・1 地物 1 LOD=S1 の原文どおり)/npz=解析済み tran_lod3.npz(LOD3 + clip_rect の部分集合)
  - `--world`
- 決定の ID: 第 219
