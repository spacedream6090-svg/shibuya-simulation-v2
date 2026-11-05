# tools/bench/event_cost

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 1 本・その他 0 本(このディレクトリの直下)

## [event_cost.py](../../../../../../../tools/bench/event_cost/event_cost.py)

事象 1 件あたりの Python の固定費を測る小さな道具(指示書 11-03 §6-1・v3 の核の材料)。

- 公開の関数とクラス
  - `Pools`(クラス): 輪で使い回す乱数の表(Python の int の list)。件数に比例するメモリを持たない。
  - `SoA`(クラス): 体の配列(35 万体ぶん)。束の演算の相手。
  - `batch_kernel`(関数): 束の 1 回の処理(expedient=未リサーチの代表の形): 読み → 算術 → 書き → 次の時刻。NumPy の呼び 6 回。
  - `build_heap`(関数)
  - `day_estimate`(関数): coefs: 名前 → ns/事象。各行の 1 日の秒と、合計の行の和。
  - `load_event_rows`(関数)
  - `machine_info`(関数)
  - `main`(関数)
  - `measure_argmin`(関数)
  - `measure_batch`(関数)
  - `measure_dispatch`(関数)
  - `measure_heap`(関数)
  - `measure_round`(関数): mode: 'single'=束の種類が 1 つ / 'mixed'=束の中で種類が混ざり Python で分ける / 'scalar'=k=1 の Python。
  - `measure_window_scan`(関数)
  - `run`(関数)
  - `to_markdown`(関数)
- 読む試験(道筋で): `tests/tools/test_event_cost_bench.py`
- CLI の引数
  - `--agents`: (3)(4)(5) の体の配列の大きさ
  - `--argmin-max`: (5) argmin を測る件数の上限(1 件が O(体数))
  - `--batch-sizes`: (3)(4) の束の大きさ k の一覧
  - `--coef-count`: 1 日の見積りに使う係数の件数の点
  - `--counts`: 事象の件数の一覧(カンマ区切り・既定 10000)
  - `--event-table`: R-130 §4 の event_table.json
  - `--floor-ms`: 事象の無い刻みの床(ms/刻み)
  - `--heap-size`: (1)(4) の列の大きさ(既定=35 万体に 1 件ずつ)
  - `--heap-sweep`: (1) の列の大きさの感度の一覧(任意・例 1000,30000,345858)
  - `--kinds`: (2) の種類の数の一覧
  - `--md`: 表の Markdown の出力先(任意)
  - `--no-gc`: 測る間 gc を止める(既定は止めない=実際の核に近い)
  - `--out`: 生の値の JSON の出力先(無ければ標準出力)
  - `--quiet`
  - `--repeats`: 各点の繰り返し(中央値を取る)
  - `--seed`
  - `--single-from`: この件数以上は 1 回だけ測る
  - `--windows`: (5) の窓の走査を測る窓の数
- 決定の ID: 11-03/§6-1・R-130・R-133
