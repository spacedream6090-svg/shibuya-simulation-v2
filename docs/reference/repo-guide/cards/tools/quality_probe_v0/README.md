# tools/quality_probe_v0

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 8 本・その他 9 本(このディレクトリの直下)

その他のファイル: `README.md`・`item_set_hash.txt`・`item_set_hash_2line.txt`・`item_set_hash_f1var.txt`・`judge_protocol.md`・`probes.jsonl`・`probes_2line.jsonl`・`probes_f1var.jsonl`・`run_b10_b11.sh`

## [analyze_f1var.py](../../../../../../tools/quality_probe_v0/analyze_f1var.py)

analyze_f1var.py — ① v0/v1変種の追試を集計(指標Bの制約半分)。入力: results/quality_ledger.csv(原本 main 行) + results_f1var/quality_ledger_f1var.csv(v0/v1 行)出力: Markdown(stdout)。違反率 main/v0/v1・対応ありΔ(v1−v0)のブートストラップ95%CI・不一致対の数・場面別の行動表・gold(F1-08)・過剰拒否(F1-04)。

- 公開の関数とクラス
  - `base_of`(関数)
  - `var_of`(関数)
- CLI の引数
  - `sys.argv` を直接読む

## [build_f1_variants.py](../../../../../../tools/quality_probe_v0/build_f1_variants.py)

build_f1_variants.py — 系統①(制約つき8場面)に観測2水準(v0/v1)の変種を作る。目的: 指標B(制約違反率の差)の「制約半分」を埋める(親Claude 2026-09-06・ユーザーGo)。規則: build_probes.py の TRIM と同じ切り詰め/充填規則を、既存の①観測文(=ほぼv1サイズ)へ適用する。v1: 可視3・看板1・近景1・近接3・傍受/広告/固定文言なし(=main−α) v0: 可視8・看板4・構成1・印象1・近景2・近接4・所持2行目・関係/可視差分/被注視・傍受1・直近2・記憶1制約を担う情報(所持金・営業時間表示・条例区域・所持スロット・距離)は両水準に残る=試験は「周辺情報の増減が制約充足を変えるか」。B0(system)は両水準で同一(交絡回避・⑥と同じ方針)。expected は原本をそのままコピー(採点規則は不変)。出力: probes_f1var.jsonl(16問・id="F1-0Nv0"/"F1-0Nv1"・family=1・variant='main' で走らせる)。

- 公開の関数とクラス
  - `main`(関数)
  - `render`(関数)
  - `split_vis`(関数)
- import している内部モジュール: `tools/quality_probe_v0/build_probes.py`

## [build_probes.py](../../../../../../tools/quality_probe_v0/build_probes.py)

build_probes.py — 品質プローブv0 の問題セット probes.jsonl を決定論的に生成する。

- 公開の関数とクラス
  - `S`(関数)
  - `adj`(関数)
  - `approx_tokens`(関数): 日本語の概算トークン数。1.30文字/トークンの粗い係数(答申§4-3=実測を推奨)。
  - `b0`(関数): level: 'qa' | 'short' | 'mid' | 'long'
  - `build`(関数)
  - `main`(関数)
  - `noise_band`(関数): 用途地域と時刻から法定境界に釘付けした騒音段階を返す(環境確保条例 規制基準)。
  - `qa`(関数)
  - `refl`(関数)
  - `render_scene`(関数)
- 呼び手: `tools/quality_probe_v0/build_f1_variants.py`
- CLI の引数
  - `--out`

## [make_visual_review.py](../../../../../../tools/quality_probe_v0/make_visual_review.py)

make_visual_review.py — ユーザー目視12問の提示用 Markdown を probes.jsonl から生成する。

- 公開の関数とクラス
  - `main`(関数)
- import している内部モジュール: `tools/quality_probe_v0/scorer.py`
- CLI の引数
  - `--ledger`
  - `--out`
  - `--probes`

## [run_judge.py](../../../../../../tools/quality_probe_v0/run_judge.py)

run_judge.py — 系統②のペア比較判定(judge_protocol.md jp-v0.1 の実装)。

- 公開の関数とクラス
  - `call`(関数)
  - `extract_prompt_template`(関数): §3 の最初のコードブロック本文を返す。
  - `extract_references`(関数): §4 の表から probe_id -> 参照回答 を返す。
  - `http_json`(関数)
  - `main`(関数)
  - `parse_reason`(関数)
  - `parse_verdict`(関数): A / B / tie を返す。読めなければ tie。
- CLI の引数
  - `--endpoints`: model=url を3つカンマ区切り。例 Qwen3-8B-int8=http://127.0.0.1:8000,...
  - `--ledger`
  - `--out`
  - `--probes`
  - `--protocol`

## [run_probe.py](../../../../../../tools/quality_probe_v0/run_probe.py)

run_probe.py — 品質プローブv0 の実行器(サーバー側で動かす。標準ライブラリ+urllibのみ)。

- 公開の関数とクラス
  - `build_tasks`(関数): (probe, variant, tier, temperature, seed) のリストを作る。
  - `call_chat`(関数)
  - `discover_model`(関数)
  - `main`(関数)
  - `prompt_for`(関数)
- import している内部モジュール: `tools/quality_probe_v0/scorer.py`
- CLI の引数
  - `--batch-invariant`: 台帳に記録する値。サーバー起動時の VLLM_BATCH_INVARIANT と一致させること。
  - `--conc`: 1エンドポイントあたりの並行呼び出し数。
  - `--dry-run`: 送信せずプロンプトの検査だけ行う。
  - `--endpoints`: カンマ区切り。1エンドポイント=1モデル。
  - `--engine-ver`
  - `--families`: 例 1,3,6。省略で全系統。
  - `--limit`: 先頭N件だけ流す(試走用)。
  - `--models`: カンマ区切り。省略時は /v1/models から取得。
  - `--out`
  - `--probes`
  - `--quants`: カンマ区切り(int8/awq/bf16 等)。台帳の quant 列になる。
  - `--raw-dir`
  - `--repeats`
  - `--stability`: ②④の安定性サブセットを temp0.7×R で回す。

## [scorer.py](../../../../../../tools/quality_probe_v0/scorer.py)

scorer.py — 品質プローブv0 の採点器(標準ライブラリのみ)。

- 公開の関数とクラス
  - `aggregate`(関数): モデルごとの集計を返す。
  - `check_constraints`(関数): 違反した制約の一覧を返す。
  - `check_diff`(関数)
  - `check_gold`(関数)
  - `check_termination`(関数)
  - `dest_equal`(関数)
  - `extract_action`(関数): 行動をスカラー語彙へ写像する。行動欄→本文の順に探す。
  - `extract_destination`(関数)
  - `extract_verdict`(関数)
  - `load_ledger`(関数)
  - `load_probes`(関数)
  - `main`(関数)
  - `parse_output`(関数): 寛容パーサ。①JSONを試す ②行正規表現で抽出 ③どちらも駄目なら format_error。
  - `score_call`(関数)
  - `score_reflection`(関数)
  - `script_ratios`(関数)
  - `strip_think`(関数): Qwen3 等の思考ブロックを除去する(判定前に必ず通す)。
  - `verdict_lines`(関数): ゲート判定の文面を返す。
  - `wilson_ci`(関数)
  - `wilson_lb`(関数): Wilson スコア区間の下限。既定 z=1.6449 = 片側95%(ゲート用)。両側95%は z=1.96。
- 呼び手: `tools/quality_probe_v0/make_visual_review.py`・`tools/quality_probe_v0/run_probe.py`・`tools/quality_probe_v0/selftest.py`
- CLI の引数
  - `--adjacent`: 行き先一致に隣接セル許容を既定で使う
  - `--ledger`
  - `--probes`
  - `--report`

## [selftest.py](../../../../../../tools/quality_probe_v0/selftest.py)

selftest.py — 採点器の機能テスト(LLM不要・標準ライブラリのみ)。合成した「良い出力」「破綻した出力」を通して、採点器が意図どおり動くかを確かめる。python selftest.py で実行。全て PASS なら終了コード0。

- 公開の関数とクラス
  - `ck`(関数)
- import している内部モジュール: `tools/quality_probe_v0/scorer.py`
