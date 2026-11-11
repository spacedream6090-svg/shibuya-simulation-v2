# src/shibuya/build/audit

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 5 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/build/audit/__init__.py)

build.audit — 世界データ構築 W18/W19/W20(被覆指標・凍結・検収パック)。

- 呼び手: `shibuya.build.audit.run`・`shibuya.build.run`
- 読む試験(道筋で): `tests/test_places_guard.py`

## [run.py](../../../../../../../../src/shibuya/build/audit/run.py)

build.audit.run — 被覆指標・凍結・検収パックを W 番号順に実行する CLI。

- 公開の関数とクラス
  - `main`(関数)
  - `run_stages`(関数)
- import している内部モジュール: `shibuya.build.audit`・`shibuya.build.audit.w18_coverage`・`shibuya.build.audit.w19_freeze`・`shibuya.build.audit.w20_acceptance_pack`・`shibuya.build.geo.common`・`shibuya.build.geo.run`
- 呼び手: `shibuya.build.run`
- 読む試験(道筋で): `tests/test_places_guard.py`
- CLI の引数
  - `--data`: 入力データ根(既定 data)
  - `--out`: 出力ディレクトリ(例 data/world/v2)
  - `--quiet`
  - `--stage`: 実行する段階

## [w18_coverage.py](../../../../../../../../src/shibuya/build/audit/w18_coverage.py)

W18 カタログ写像・世界被覆指標(§1 W18・D-W19)。

- 公開の関数とクラス
  - `compute_index`(関数): 凍結カタログ行 + 実装状況 → 被覆指標(純関数・テストの入口)。
  - `parse_depth`(関数): カタログ「初回後d」欄 → 深度。``**0**`` や ``2(…)`` のような装飾を剥がす。
  - `parse_gate`(関数): カタログ「gate」欄 → 憲法5の門を通ったか(``✔`` で始まる行)。
  - `parse_n_real`(関数): カタログ「現実数量」欄 → 先頭の数(桁区切りのカンマを外す)。数が無ければ None。
  - `run`(関数)
  - `weight`(関数): w = 1 + log10(1 + N_real)(上限 6)。N_real 不明は 1(expedient)。
- import している内部モジュール: `shibuya.build.geo.common`・`shibuya.manifest.world_catalog`
- 呼び手: `shibuya.build.audit.run`
- 読む試験: `tests/build_audit/test_audit_units.py`
- 読む試験(道筋で): `tests/test_places_guard.py`

## [w19_freeze.py](../../../../../../../../src/shibuya/build/audit/w19_freeze.py)

W19 manifest 凍結(§1 W19・D-W20・運用設計書 §1.2「データ資産」「holdout封印」)。

- 公開の関数とクラス
  - `data_asset_paths`(関数): 全段階の入力ファイル(data 根からの相対パス・整列済み・重複なし)。
  - `layer_independence`(関数): holdout 層ごとに「元」「構築の入力と同じ元か」「独立か」「印」を返す(値は読まない・表だけ)。
  - `run`(関数)
  - `scan_build_sources`(関数): ``src/shibuya/build`` 配下で holdout 語を含むモジュールを探す(本モジュールは除く)。
  - `seal_layer`(関数): holdout 層 → (member_hash, メンバー表)。ファイルの中身は**開かず** sha256 だけ取る。
  - `w21_material_paths`(関数): 置き場の W21 の manifest の材料(``sources`` の元のファイルと写し)→ {data 根からの相対: manifest の md5}。
- import している内部モジュール: `shibuya.build.field.w10_noise`・`shibuya.build.field.w12_external_nodes`・`shibuya.build.field.w12_real_timetables`・`shibuya.build.field.w13_weather`・`shibuya.build.field.w7_planspec`・`shibuya.build.geo.common`・`shibuya.build.geo.w0_crs`・`shibuya.build.geo.w11_station_exits`・`shibuya.build.geo.w1_walk_graph`・`shibuya.build.geo.w4_heights`・`shibuya.build.geo.w5_entrances`・`shibuya.build.geo.w6_poi_org`・`shibuya.build.pop.w16_population`・`shibuya.build.sched.w20_calendar_1a`
- 呼び手: `shibuya.build.audit.run`・`shibuya.build.pop.w21_sources`
- 読む試験: `tests/build_audit/test_audit_units.py`・`tests/build_audit/test_w19_layer_sources.py`・`tests/build_field/test_w12_keio_switch_2_4.py`・`tests/build_field/test_w12_real_timetables.py`・`tests/build_pop/test_w21_sources.py`・`tests/build_rail/test_w12_arrivals_2_3c.py`・`tests/build_sched/test_w20_calendar_1a.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 決定の ID: 10-13b/§1・第 330・第 333

## [w20_acceptance_pack.py](../../../../../../../../src/shibuya/build/audit/w20_acceptance_pack.py)

W20 検収パック(§1 W20)。

- 公開の関数とクラス
  - `gate_table_markdown`(関数): 全段階のゲート表(markdown)。``build_hash`` を渡すと先頭に出す。
  - `run`(関数)
  - `upstream_build_hash`(関数): W20 より前の段階の出力 sha256 を W 番号順に連結した文字列の sha256。
- import している内部モジュール: `shibuya.build.geo.common`・`shibuya.build.vis.png`・`shibuya.foundation.time_consts`
- 呼び手: `shibuya.build.audit.run`
- 読む試験: `tests/build_audit/test_audit_units.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 決定の ID: 第 330
