# tools/c6

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 7 本・その他 0 本(このディレクトリの直下)

## [ablation1_fixed_vs_ranking.py](../../../../../../tools/c6/ablation1_fixed_vs_ranking.py)

ablation1_fixed_vs_ranking.py — **ablation ①(義務)**「チャネル固定枠 vs 単一ランキング」。

- 公開の関数とクラス
  - `main`(関数)
  - `probe_switch`(関数): 2 つの ``BudgetMode`` で同じ場面を描き、バイト差分の有無を返す(**純関数寄り**)。
  - `run_arm`(関数): 1 構成のスモーク(budget_mode=tag を run_day へ渡す・09-09 切替口実装後)。
- import している内部モジュール: `shibuya.agents.schedule`・`shibuya.agents.state`・`shibuya.engine.resolve`・`shibuya.engine.tape`・`shibuya.foundation.text.channels`・`shibuya.perception.renderer`・`shibuya.world.state`・`tools/c6/c6lib.py`
- 読む試験: `tests/c6/test_c6lib_aggregate.py`・`tests/perception/test_ablation1.py`
- CLI の引数
  - `--max-tokens`
  - `--probe-only`: 切替口の実在確認だけして終わる
  - `--run-id`
  - `--tape-dir`: テープの置き場(既定=--out の下)
  - `--temperature`
- 決定の ID: D-58

## [c6lib.py](../../../../../../tools/c6/c6lib.py)

c6lib — C6-b 検証ハーネスの純関数と共通部品(標準ライブラリ + numpy/httpx)。

- 公開の関数とクラス
  - `RecordingLLM`(クラス): 任意の ``LLMClient`` を包んで **全プロンプトと応答**を記録する。
  - `Scene`(クラス): 1 呼 = 1 場面(指標B の抽出単位)。
  - `align_counts`(関数): 2 つの計数辞書を同じ鍵の並び(既定=和集合の昇順)へ揃える。
  - `average_stratified_reports`(関数): 同じ母集団・違う run seed の層内報告を **Fisher z 平均**でまとめ、判定をやり直す。
  - `bootstrap_mean_ci`(関数): 平均のブートストラップ CI(復元抽出)。返り値 = (点推定, 下限, 上限)。
  - `build_fleet_client`(関数): ``llm.fleet.FleetClient`` を組む(実サーバーに繋ぐのは呼び出し側の責任)。
  - `chat_once`(関数): ``/v1/chat/completions`` を 1 回叩く(品質プローブv0 ``run_probe.call_chat`` と同じ形)。
  - `chi2_2sample`(関数): 2 標本の同質性 χ² 検定(2×k 分割表)。度数 0 の列は落とす。
  - `chi2_sf`(関数): χ² 分布の上側確率(自由度 df)。
  - `classify_scene`(関数): プロンプト本文 → (制約種 id, 答えが決まるか, 駆動因)。**純関数**。
  - `common_parser`(関数): 全ツール共通の引数(``--endpoints --world --agents --ticks --out``)。
  - `discover_model`(関数): ``/v1/models`` の先頭 id(取れなければ ``""``)。
  - `endpoints_of`(関数)
  - `gammq`(関数): 正則化上側不完全ガンマ Q(a,x)。
  - `in_flight_report`(関数): ``fleet_peak_in_flight_r*`` が L6(64 in-flight/GPU)を超えていないか。
  - `jsd`(関数): Jensen-Shannon divergence(既定 bits・品質プローブv0 と同じ単位)。
  - `jsd_counts`(関数): 計数辞書 2 本の JSD[bits]。
  - `ks_2samp`(関数): 2 標本 Kolmogorov-Smirnov(D と漸近 p 値)。
  - `markdown_table`(関数): Markdown の表(数値の整形は呼び出し側)。
  - `null_jsd_reference`(関数): **帰無参照**: 同一分布から n_a / n_b 件ずつ引いた 2 標本の JSD 分布。
  - `order_bias_report`(関数): T5 の 3 量 × (Pearson, Spearman) を 1 表にする(**個体が一様な母集団向け**)。
  - `pearson`(関数): Pearson の r(片側の分散が 0 なら 0.0=「相関を検出しない」)。
  - `per_agent_call_stats`(関数): ``(agent_id, tick)`` の並び → (個体別の呼数, 個体別の呼ばれた tick の平均)。
  - `rankdata`(関数): 同順位を平均順位にする順位付け(scipy を使わない)。
  - `reversal_symmetry`(関数): **副判定**: 母集団を反転すると生の ρ の符号が返る(=種別構成の効果)ことの釘付け。
  - `reverse_population`(関数): 個体の並びを**逆順**にした母集団(T5 の ID 写像反転の対照)。
  - `run_smoke`(関数): ``shibuya.cli.run`` を叩く(台帳つきの標準入口)。
  - `scene_from_record`(関数): ``RecordingLLM`` の 1 行(``scenes.jsonl``)→ ``Scene``。
  - `scene_inventory`(関数): 場面の在庫表(全 18 種の件数・事前登録 5 種の充足・決まる場面の件数)。
  - `scenes_from_jsonl`(関数): ``scenes.jsonl``(``RecordingLLM.dump``)→ 場面。
  - `scenes_from_tape`(関数): 録画テープ(``engine.tape.Tape`` かそのパス)→ 場面。
  - `score_texts`(関数): 応答本文の並び → 書式エラー率(実効/厳密)・別名率・行動分布・役割語率・未定義率。
  - `select_metric_b_scenes`(関数): 事前登録の抽出(制約種ごと n・「答えが決まる場面」m)。**決定論**(``Scene.key`` 昇順)。
  - `spearman`(関数): Spearman の ρ(順位相関)。
  - `split_prompt`(関数): レンダラの本文 → (system 部, user 部)。
  - `stratified_order_bias_report`(関数): **種別層内**の T5(実データ用)。
  - `violation_flags`(関数): 制約違反フラグ(1=違反)。**制約種ごとに禁止行動を 1 つ持つ最小規則**。
  - `wilson_ci`(関数): 二項比率の Wilson 信頼区間(品質プローブv0 の ``wilson_ci`` と同定義)。
  - `world_dir_of`(関数)
  - `write_outputs`(関数): ``<out>/<stem>.json`` と ``<out>/<stem>.md`` を書く(改行は LF=Windows でも CRLF にしない・第307)。
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.tape`・`shibuya.foundation.manifest.schema`・`shibuya.foundation.vocab.actions`・`shibuya.llm.fleet`・`shibuya.llm.parser`・`shibuya.llm.undefined`
- 呼び手: `tools/c6/ablation1_fixed_vs_ranking.py`・`tools/c6/format_role_rates.py`・`tools/c6/metric_b_rerun.py`・`tools/c6/run_hash.py`・`tools/c6/t6_bit_reproduce.py`・`tools/c6/t7_distribution.py`・`tools/c7/c7lib.py`・`tools/c8/c8lib.py`・`tools/fig/fig_ab7_actions.py`・`tools/fig/fig_ab7c_vocab.py`・`tools/w17/diversity_yardstick.py`
- 読む試験: `tests/c6/conftest.py`・`tests/c6/test_t5_order_bias.py`
- 読む試験(道筋で): `tests/tools/test_repo_guide.py`
- CLI の引数
  - `--agents`
  - `--endpoints`: カンマ区切りの vLLM レプリカ(例 http://127.0.0.1:8000,http://127.0.0.1:8001)
  - `--model`: served-model-name(空なら /v1/models の先頭)
  - `--out`: 結果 JSON/Markdown の出力先
  - `--seed`
  - `--ticks`: 24step スモークが既定
  - `--world`: 世界資産ディレクトリ
- 決定の ID: D-28・D-58・D-71・第 307

## [format_role_rates.py](../../../../../../tools/c6/format_role_rates.py)

format_role_rates.py — **書式エラー率・役割語率・未定義率**(C6 受入表 §9.1 の形)。

- 公開の関数とクラス
  - `acceptance_rows`(関数): §9.1 C6 受入表の行(判定つき)。**純関数**。
  - `main`(関数)
  - `texts_from_jsonl`(関数)
  - `texts_from_tape`(関数)
- import している内部モジュール: `shibuya.engine.tape`・`tools/c6/c6lib.py`
- 読む試験: `tests/c6/test_c6lib_aggregate.py`
- CLI の引数
  - `--max-tokens`
  - `--mode`
  - `--responses`: 応答 jsonl(text 欄)
  - `--run-id`
  - `--tape`: 録画テープのディレクトリ
  - `--temperature`: 受入条件は温度 0.7
- 決定の ID: D-28・D-58

## [metric_b_rerun.py](../../../../../../tools/c6/metric_b_rerun.py)

metric_b_rerun.py — **指標B の事前登録つき再測**(Phase 2 実データ場面)。

- 公開の関数とクラス
  - `collect_scenes`(関数): mock ランを回して ``scenes.jsonl``(プロンプト全文)を作る。
  - `compare_passes`(関数): 指標B の 2 半分(制約違反率の差 + 行動分布 JSD)。**純関数**。
  - `main`(関数)
  - `rerun_scenes`(関数): 1 モデルへ全場面を投げて応答本文を返す(逐次・24step スモーク規模の想定)。
  - `score_pass`(関数): 1 パスの採点(違反フラグ・行動分布・書式)。
- import している内部モジュール: `shibuya.llm.mock`・`tools/c6/c6lib.py`
- 読む試験: `tests/c6/test_c6lib_aggregate.py`
- CLI の引数
  - `--collect-only`: 収集と在庫表だけ出して終わる
  - `--determined`
  - `--kinds`: (help を読めない)
  - `--max-tokens`
  - `--models`: endpoints と同順のモデル名(カンマ区切り)
  - `--null-seed-offset`: 帰無参照(同モデル seed 違い)
  - `--per-kind`
  - `--scenes`: 既存の scenes.jsonl(空なら収集から)
  - `--tape`: 録画テープ(診断用。B5/B6 が無いので再呼は不可)
  - `--temperature`

## [run_hash.py](../../../../../../tools/c6/run_hash.py)

run_hash.py — 1 ランの checkpoint ハッシュだけを JSON で吐く(**T3 の子プロセス**)。

- 公開の関数とクラス
  - `main`(関数)
- import している内部モジュール: `shibuya.engine.run`・`shibuya.world.state`・`tools/c6/c6lib.py`
- CLI の引数
  - `--cells`: 合成世界のセル数
  - `--no-ledger`: 台帳なし(engine.run.run_day 直呼び)
  - `--threads`: numba.set_num_threads(N)(0=触らない)
- 環境変数: `MKL_NUM_THREADS`・`NUMBA_NUM_THREADS`・`OMP_NUM_THREADS`

## [t6_bit_reproduce.py](../../../../../../tools/c6/t6_bit_reproduce.py)

t6_bit_reproduce.py — **T6 LLM 層 bit 再現**(検証ラン構成)。

- 公開の関数とクラス
  - `compare_tapes`(関数): 2 本のテープの応答本文を突合(**純関数**・テストはモック辞書で)。
  - `main`(関数)
- import している内部モジュール: `shibuya.engine.tape`・`tools/c6/c6lib.py`
- 読む試験: `tests/c6/test_c6lib_aggregate.py`
- CLI の引数
  - `--max-tokens`
  - `--mode`: smoke/calibration/holdout/ablation/production
  - `--run-id`: manifest の自己ハッシュ(cache_salt の第2要素)
  - `--tape-dir`: テープの置き場(既定=一時ディレクトリ)
  - `--temperature`: 検証ランは 0

## [t7_distribution.py](../../../../../../tools/c6/t7_distribution.py)

t7_distribution.py — **T7 LLM 層 分布同値**(本番構成・温度 0.7)。

- 公開の関数とクラス
  - `action_counts_from_tape`(関数): テープの応答本文 → 行動語の度数(``llm.parser`` で解釈)。
  - `distribution_report`(関数): 2 分布の JSD・χ²・帰無参照を 1 まとめに(**純関数**)。
  - `main`(関数)
  - `result_code_counts`(関数): 個体 SoA の ``last_result`` → ``ResultCode`` 名の度数。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.tape`・`tools/c6/c6lib.py`
- 読む試験: `tests/c6/test_c6lib_aggregate.py`
- CLI の引数
  - `--max-tokens`
  - `--mode`
  - `--run-id`
  - `--seed-b`: 2 本目の master_seed
  - `--tape-dir`: テープの置き場(既定=--out の下)
  - `--temperature`: 本番構成は 0.7
- 決定の ID: D-25
