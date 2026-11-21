# tools/gen

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 1 本・その他 0 本(このディレクトリの直下)

## [fleet_gen.py](../../../../../../tools/gen/fleet_gen.py)

fleet_gen — 1回限りの静的生成(W14 看板文・W15 セル静的文・W17 スケジュール)を vLLM 艦隊へ流す運搬役。

- 公開の関数とクラス
  - `build_payload`(関数)
  - `call_once`(関数)
  - `discover_model`(関数)
  - `get_models`(関数)
  - `load_done`(関数)
  - `main`(関数)
  - `replica_of`(関数)
  - `request_sha256`(関数)
- CLI の引数
  - `--conc`: 1 エンドポイントあたりの並行数
  - `--endpoints`: カンマ区切り http://host:port
  - `--failures`: 失敗記録 jsonl(既定 <out>.failures.jsonl)
  - `--limit`: 先頭 N 件だけ(試走)
  - `--model`: served-model-name。省略時は /v1/models の先頭
  - `--out`
  - `--prompts`
