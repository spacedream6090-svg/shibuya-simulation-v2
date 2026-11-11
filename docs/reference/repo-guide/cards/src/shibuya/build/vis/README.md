# src/shibuya/build/vis

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 5 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/build/vis/__init__.py)

build.vis — 世界データ構築 W8/W9(可視性・影レーン)。

- 呼び手: `shibuya.build.run`・`shibuya.build.vis.run`
- 読む試験(道筋で): `tests/test_places_guard.py`

## [png.py](../../../../../../../../src/shibuya/build/vis/png.py)

最小の PNG 書き出し(zlib + PNG チャンクのみ・PIL/matplotlib 非依存)。

- 公開の関数とクラス
  - `Canvas`(クラス): RGB キャンバス。世界ローカル平面 [m] → 画素(y は上が北)の写像つき。
  - `encode_png`(関数): (H,W) uint8 グレー or (H,W,3) uint8 RGB → PNG バイト列。
  - `ramp_rgb`(関数): 0..1 の配列 → RGB uint8((...,3))。NaN は最初の色。
  - `write_png`(関数): PNG を書いてバイト数を返す。
- 呼び手: `shibuya.build.audit.w20_acceptance_pack`
- 読む試験: `tests/build_vis/test_vis_units.py`
- 読む試験(道筋で): `tests/test_places_guard.py`

## [run.py](../../../../../../../../src/shibuya/build/vis/run.py)

build.vis.run — 可視性・影レーンの段階を W 番号順に実行する CLI。

- 公開の関数とクラス
  - `main`(関数)
  - `run_stages`(関数)
- import している内部モジュール: `shibuya.build.geo.common`・`shibuya.build.geo.run`・`shibuya.build.vis`・`shibuya.build.vis.w8_visibility`・`shibuya.build.vis.w9_shadow`
- 呼び手: `shibuya.build.run`
- 読む試験: `tests/build_vis/test_vis_pipeline.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- CLI の引数
  - `--data`: 入力データ根(既定 data)
  - `--out`: 出力ディレクトリ(例 data/world/v2)
  - `--quiet`
  - `--stage`: 実行する段階

## [w8_visibility.py](../../../../../../../../src/shibuya/build/vis/w8_visibility.py)

W8 可視性テーブル(§1 W8・D-W9)。

- 公開の関数とクラス
  - `Scene`(クラス): 遮蔽ラスタ。``ground_z``/``top_z``/``owner`` は同じ (ny, nx) 格子。
  - `build_scene`(関数): 建物 footprint + DEM → 遮蔽ラスタ(``Scene``)。
  - `run`(関数)
- import している内部モジュール: `shibuya.build.geo.common`
- 呼び手: `shibuya.build.vis.run`・`shibuya.build.vis.w9_shadow`
- 読む試験: `tests/build_vis/test_vis_units.py`
- 読む試験(道筋で): `tests/test_places_guard.py`

## [w9_shadow.py](../../../../../../../../src/shibuya/build/vis/w9_shadow.py)

W9 影グリッド(§1 W9・D-W10「5分刻み」)。

- 公開の関数とクラス
  - `all_shadow_plane`(関数): 全点日陰の1面(``np.packbits`` 互換・端数ビットは 0 で埋める)。
  - `remove_stale_shadows`(関数): ``out`` の ``w9_shadow_<日付>.npy`` のうち ``dates`` に無い日のファイルを消し、消した名前を返す。
  - `run`(関数)
  - `sun_vector`(関数): (高度 [deg], 方位 [deg・北から時計回り], 単位水平方向の x 成分…) ではなく
- import している内部モジュール: `shibuya.build.field.w13_weather`・`shibuya.build.geo.common`・`shibuya.build.vis.w8_visibility`・`shibuya.core.time_consts`
- 呼び手: `shibuya.build.vis.run`
- 読む試験: `tests/build_vis/test_vis_pipeline.py`・`tests/build_vis/test_vis_units.py`・`tests/engine/multiday/test_md23_w9_window.py`・`tests/engine/test_activation_2_4.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 決定の ID: 10-12b・第 330
