# tools/bench_spikes

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 3 本・その他 0 本(このディレクトリの直下)

## [batch_invariance_check.py](../../../../../../tools/bench_spikes/batch_invariance_check.py)

batch_invariance_check.py — B14: vLLM のバッチ不変性(VLLM_BATCH_INVARIANT=1)の自検証と再現性テスト(サーバー・8B INT8・契約書v1サイズ)。T6a 不変性: 同じ32プロンプト(温度0)を「単独(逐次)」と「他200件と混在(並行)」で送り、出力が一致する割合。T6b 再現性(温度0.7・seed固定): 同一リクエストを2回(混在環境を変えて)送り、出力一致率。T6c 版間: 同一プロンプト・同一seedの出力ハッシュを保存(後日の別版/別GPU比較用)。入力=品質プローブv0の①②⑥v1(59問)から32本+充填用200本(⑥のv0/full)。

- 公開の関数とクラス
  - `call`(関数)
  - `load_probes`(関数)
  - `main`(関数)
  - `run_set`(関数)
- CLI の引数
  - `--label`
  - `--model`
  - `--out`
  - `--probes`
  - `--url`

## [crowd_physics_bench.py](../../../../../../tools/bench_spikes/crowd_physics_bench.py)

crowd_physics_bench.py — 群衆物理(社会力モデル型)の1ステップを40万体・CPU(numba並列)で計測するスパイク。配置: 6.93km²相当の領域に、30%の個体を面積5%の「混雑地区」に集中(渋谷駅周辺のピーク相当)。近傍探索=一様格子(2m)。各個体は半径2m内の近傍から反発力(指数)を受け、目標速度へ緩和。計測: 1ステップの実時間 → dt=1.0/0.5/0.1秒で1シミュ日(86,400秒)へ外挿。物理対象をLOD(混雑セルのみ)に絞った場合(対象10%)も計測。

- 公開の関数とクラス
  - `build_grid`(関数)
  - `run`(関数)
  - `sfm_step`(関数)
- CLI の引数
  - `--n`
  - `--seed`
  - `--steps`

## [engine_tick_bench.py](../../../../../../tools/bench_spikes/engine_tick_bench.py)

engine_tick_bench.py — v2エンジンの1tick処理を40万体規模で模した計測(設計判断用スパイク・シム本体ではない)。設計(知覚契約書/行動契約書/認知設計書/実装スタック答申)に沿った代表段階を、Python+NumPy(+numba任意)で実装し、段階ごとの実時間を計測して1シミュ日(1,440tick)へ外挿する。LLM呼び出しはしない(観測レンダリングと出力パースのみ再現)。

- 公開の関数とクラス
  - `h64`(関数)
  - `k_move`(関数)
  - `k_needs`(関数)
  - `move_np`(関数)
  - `needs_np`(関数)
  - `parse2`(関数)
  - `render_individual`(関数)
- CLI の引数
  - `--calls-per-day`
  - `--cells`
  - `--events-per-tick`
  - `--n`
  - `--seed`
  - `--ticks`
- 環境変数: `NO_NUMBA`
