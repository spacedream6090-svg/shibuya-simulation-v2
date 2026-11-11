# src/shibuya/world

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 2 本・その他 0 本(このディレクトリの直下)

下のディレクトリ: [body](body/README.md)・[facts](facts/README.md)・[laws](laws/README.md)・[ledger](ledger/README.md)・[model](model/README.md)・[processes](processes/README.md)・[things](things/README.md)

## [__init__.py](../../../../../../../src/shibuya/world/__init__.py)

(冒頭の説明なし)

- 読む試験(道筋で): `tests/test_places_guard.py`・`tests/tools/test_pkgmove.py`

## [assets.py](../../../../../../../src/shibuya/world/assets.py)

world.assets — 世界データ資産(W1/W2/W3/W6)の読み込みと、CI 用の合成小世界。

- 公開の関数とクラス
  - `ProcessAssets`(クラス): 世界過程(C4 第1陣)が読む静的資産。**全欄が空でも動く**(合成世界)。
  - `WorldAssets`(クラス): 実行時 NumPy に落とした世界資産(不変)。
  - `array_sha256`(関数): 配列の並び(dtype・形・中身)の sha256。10e(B0): 騒音の集約後のセル別の段の補助の指紋。
  - `assets_available`(関数): 資産ディレクトリに必要な 6 ファイルが揃っているか。
  - `check_area_source`(関数): 歩行可能面積の出所の検査(``run_day`` が**資産を読む前**に呼ぶ=manifest が嘘をつかない)。
  - `file_sha256`(関数): ファイルの中身の sha256(16 進・1 MiB ずつ読む)。10e(B0): manifest の ``frozen_sources`` に書く値。
  - `hash_free_cat_code`(関数): カテゴリ名 → 0..2 の価格帯コード(**決定論・ハッシュを使わない**)。
  - `load_assets`(関数): ``data/world/v2`` の資産を読む(W1/W2/W3/W6・騒音は W10)。
  - `load_poi_own_cell_visibility`(関数): W8 → POI ごとの「**自分のセルの視点から見える数**」(``(n_poi,)`` int32・無ければ 0)。
  - `load_process_assets`(関数): ``data/world/v2`` から世界過程(C4 第1陣)の資産を読む。
  - `load_process_assets_or_synthetic`(関数): 資産があれば読み、無ければ空の ``ProcessAssets``(全過程が休む)。
  - `load_visible_pois_by_cell`(関数): W8 → セルごとの「そのセルの視点から見えている POI」(CSR)。
  - `load_walkable_area_m2`(関数): ``c9c_walkable_area.parquet`` → ``place_ids`` の順に並べた歩行可能面積[m²]。
  - `synthetic_assets`(関数): CI 用の合成小世界(1 セル=1 ノードの 4 近傍格子)。
- import している内部モジュール: `shibuya.foundation.rng`・`shibuya.foundation.time_consts`
- 呼び手: `shibuya.cli`・`shibuya.engine.change_detect`・`shibuya.engine.poi_target`・`shibuya.engine.run`・`shibuya.perception.renderer`・`shibuya.runtime.systems.assemble`・`shibuya.world.laws.civic`・`shibuya.world.laws.environment`・`shibuya.world.laws.logistics`・`shibuya.world.laws.opening`・`shibuya.world.laws.rail`・`shibuya.world.laws.runner`・`shibuya.world.laws.traffic`・`shibuya.world.model.geometry`・`shibuya.world.model.graph`・`shibuya.world.model.state`
- 読む試験: `tests/_data_ids.py`・`tests/economy/test_entry_capital.py`・`tests/engine/duties/_du.py`・`tests/engine/experiment/test_x33_branch.py`・`tests/engine/processes/conftest.py`・`tests/engine/processes/test_absent_processes_1102.py`・`tests/engine/processes/test_civic.py`・`tests/engine/processes/test_environment.py`・`tests/engine/processes/test_goods_flow.py`・`tests/engine/processes/test_logistics.py`・`tests/engine/processes/test_opening.py`・`tests/engine/processes/test_rail.py`・`tests/engine/processes/test_traffic.py`・`tests/engine/rights/test_staff_of_poi_equivalence.py`・`tests/engine/test_activation_2_4.py`・`tests/engine/test_area_source_c9c.py`・`tests/engine/test_assets_10e_b0_b1.py`・`tests/engine/test_calendar_10e_e3.py`・`tests/engine/test_calendar_sites.py`・`tests/engine/test_geometry_c9.py`・`tests/engine/test_intent_chooser.py`・`tests/engine/test_presence_executor.py`・`tests/engine/test_processes_run.py`・`tests/engine/test_waste_sink_report.py`・`tests/engine/test_weather_calendar_10e.py`・`tests/perception/facts/head_renderer_136fdbb.py`・`tests/world/test_world.py`
- 読む試験(道筋で): `tests/engine/test_state_ledger_10b.py`・`tests/engine/test_two_phase.py`・`tests/test_places_guard.py`
- 決定の ID: 11-03・11-03/§2・D-66・D-84・D-96・D-112・D-114・第 330
