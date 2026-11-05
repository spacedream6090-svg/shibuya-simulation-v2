# src/shibuya/build

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 3 本・その他 0 本(このディレクトリの直下)

下のディレクトリ: [audit](audit/README.md)・[field](field/README.md)・[geo](geo/README.md)・[lang](lang/README.md)・[pop](pop/README.md)・[sched](sched/README.md)・[space](space/README.md)・[vis](vis/README.md)

## [__init__.py](../../../../../../../src/shibuya/build/__init__.py)

build: オフラインの世界データ構築(W0-W20)。成果物=不変資産。実行時にimportされない。

## [catalog_freeze.py](../../../../../../../src/shibuya/build/catalog_freeze.py)

世界カタログ(docs/design/v2-world-catalog.md)の凍結器。

- 公開の関数とクラス
  - `catalog_sha16`(関数): 凍結 SHA(sha256 先頭16桁)。
  - `extract_catalog_table`(関数): カタログ本表(見出し行〜最初の空行まで)を生のまま切り出す。
  - `freeze`(関数): Markdown から凍結 JSON を生成して書き出し、その内容を返す。
  - `main`(関数)
  - `parse_catalog_rows`(関数): 本表を行の辞書リストへ。キーは見出し行の9列名、値はセルを strip したもの。
- 読む試験: `tests/test_world_catalog_sha.py`
- CLI の引数
  - `--md`
  - `--out`
  - `--version`

## [run.py](../../../../../../../src/shibuya/build/run.py)

build.run — 世界データ構築の通し実行(地理 W0-W6/W11 + 場・境界 W7/W10/W12/W13 +可視性・影 W8/W9 + 被覆指標・凍結・検収 W18/W19/W20)。

- 公開の関数とクラス
  - `KeptStageError`(クラス): ``--keep-stage`` で保つ段のヘッダ・出力がディスク上で揃っていない。
  - `main`(関数)
  - `protected_output_hits`(関数): 走らせる段のうち、昇格版の出力を上書きしてしまうもの(``--stage`` の明示が無いもの)。
  - `run_all`(関数): 指定段階を ``RUN_ORDER``(依存順)で実行する。``build_hash`` の順は W 番号順で別。
  - `stage_order`(関数): W 番号の数値順に並べる(W7 → W10 → W11 の順・文字列順ではない)。
  - `verify_kept_stage`(関数): 保つ段のヘッダを読み、ヘッダが主張する出力が在って sha256 が一致することを確かめる。
  - `write_build_manifest`(関数): out に存在する**全段階**のヘッダから manifest を組む(W 番号順)。
- import している内部モジュール: `shibuya.build.audit`・`shibuya.build.audit.run`・`shibuya.build.field`・`shibuya.build.field.run`・`shibuya.build.geo`・`shibuya.build.geo.common`・`shibuya.build.geo.run`・`shibuya.build.lang`・`shibuya.build.lang.run`・`shibuya.build.pop`・`shibuya.build.pop.run`・`shibuya.build.sched`・`shibuya.build.sched.run`・`shibuya.build.vis`・`shibuya.build.vis.run`
- 読む試験: `tests/_data_ids.py`・`tests/build_audit/test_audit_pipeline.py`・`tests/build_field/test_field_pipeline.py`・`tests/build_field/test_field_units.py`・`tests/build_pop/test_w21_build_real.py`・`tests/build_pop/test_w21_stage4_7.py`・`tests/build_pop/test_w21_stage8_9.py`・`tests/build_vis/test_vis_pipeline.py`・`tests/test_build_run_keep_stage.py`
- CLI の引数
  - `--data`: 入力データ根(既定 data)
  - `--keep-stage`: 再構築せずディスク上の出力と既存ヘッダを採る段階(繰り返し可・例 W17)
  - `--out`: 出力ディレクトリ(例 data/world/v2)
  - `--quiet`
  - `--stage`: 実行する段階(繰り返し可・既定=全段階)
- 決定の ID: 第 168・第 281
