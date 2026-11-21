# tools/world_data

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 2 本・その他 0 本(このディレクトリの直下)

## [estat_fetch.py](../../../../../../tools/world_data/estat_fetch.py)

estat_fetch — e-Stat API(getStatsData)を **ページング付き** で取得し、data/realworld/estat/ の既存 JSON と同じ形 {"meta","classes","values"} で保存する(親レーン用)。

- 公開の関数とクラス
  - `fetch_all`(関数)
  - `main`(関数)
- CLI の引数
  - `--area-extra`: 範囲外で追加取得する cdArea(カンマ区切り・例 区計 13113)
  - `--area-from`
  - `--area-to`
  - `--out`
  - `--stats-data-id`
- 環境変数: `ESTAT_APP_ID`

## [pt_od_summary.py](../../../../../../tools/world_data/pt_od_summary.py)

第6回東京都市圏PT 表d-1(目的種類別代表交通手段別OD表)の渋谷ゾーン集計(W12/D-W22用)。

- 公開の関数とクラス
  - `load_rows`(関数)
  - `main`(関数)
  - `summarize`(関数)
- CLI の引数
  - `--out`
  - `--src`
  - `--zones`: 渋谷の計画基本ゾーン4桁コード
