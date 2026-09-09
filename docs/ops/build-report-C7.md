# 受入報告 C7(40 万体×1 シミュ日・本番相当)— 進行中(2026-09-09)

> 形式は build-report-C0〜C6 と同じ: 親(Fable)が自分で実行した出力のみを証拠とする。
> ブランチ `build/c5-c8`。サーバー(SSH エイリアス・7×A5000・Python 3.10 venv)で実行。

## 0. 構成

| 項目 | 内容 | 状態 |
|---|---|---|
| ドレスリハーサル | 390,067 体×1,440 tick・mock LLM | **親の tmux 操作ミス(`kill-window -t c5:c7` が前方一致で c7dress を殺した)で 1.6 h 時点で消失**。代替=本番ラン自体の実測+12 tick mock(下記) |
| 本番ラン c7-day-1 | 390,067 体×1,440 tick・実 LLM(7×Qwen3-8B INT8・温度 0.7・max_tokens 96・mode production・`--fleet-wait-s 120`・tape 記録) | **09-09 19:39 開始**(`~/c5/run_c7.sh`) |
| 受入計器 | tools/c7(occupancy_series・holdout_compare・c7_accept・c7lib・area_axes_v0.json=セル→5 エリア写像 expedient)・tests/c7 58 本 | サブ S 完了(09-09 20:10)・engine の在圏 journal フック=親が結線 |

## 1. 受入項目(§9.1 C7)と結果(追記予定)

| 項目 | 基準 | 結果 |
|---|---|---|
| 壁時計 | ≤24 h/シミュ日(W1) | |
| M8 RSS | ≤24 GB | |
| S1 出力 | ≤5 GB | |
| 決定論 T2 | 同 seed 再ラン一致(40 万体は 1 回=checkpoint 自己整合+5,000 体の再ラン一致で代替=D-39) | |
| 診断行 | 繰り延べ/昇格/縮退/抑止+保存則 2 検算 | |
| 被覆指標 WC-6 | | |
| holdout 照合 | 事後 1 回のみ(KDDI 形状 5 指標) | |

## 1b. 性能の発見(09-09 20:00・本番ラン開始直後)
- 12 tick mock @390,067 体: **内訳 llm 46,079 ms/tick**(呼 2,709/tick)・arbiter 616・movement 13.7・合計 47 s/tick → 1 日 18.8 h(エンジンだけ)。本番ランの vLLM ログでも tick 周期 ≈60 s(=24 h 超の見込み)。
- cProfile(3 tick・8,126 呼): `perception/renderer.py:1091 <dictcomp>` 101 s/7,173 呼=**14 ms/呼**・`_nearby_items` の生成式が 1 呼あたり 13,663 反復=**B5 近接個体の候補をセル内全個体の Python 反復で作っている**(5,000 体では 0.27 ms/呼で見えなかった)。→ サブ R にベクトル化+(tick, セル)キャッシュを依頼(出力バイト不変が条件)。修正後に本番ランを再起動する(現行ランは fallback として継続)。
- 在圏 journal(holdout 照合の入力)のフックは本番ラン開始時に未実装だった→親が engine/run.py に `occupancy_every/occupancy_path`(毎正時のセル別在圏+種別別)を追加し、再起動ランから記録する。

### 1c. 性能修正(サブ R・09-09 20:30)と再起動
- `perception/renderer._nearby_items` をベクトル化(セル順の連続座標配列・逆置換で自分を除去・sqrt は採った件だけ・知人は範囲比較)。**出力バイト不変**(旧実装を逐語で持つ照合テスト 7 本・5,000 体 checkpoint d5d79337… 不変・golden 不変)。PC 実測 390,067 体×3 tick: llm 16,908→**690 ms/tick**(24.5×)・1 呼 6.24→0.255 ms。
- **サーバー実測(親・3 tick mock @390,067)**: llm 46,079→**1,624 ms/tick**・arbiter 691・detect 68・合計 **3.49 s/tick**(→エンジン単独 ≈1.4 h/日)。
- 本番ランを **c7-day-2** として再起動(vectorized renderer+在圏 journal `--occupancy-every 60`)。c7-day-1(60 s/tick 見込み・在圏 journal なし)は停止。

## 2. ログ(追記予定)
