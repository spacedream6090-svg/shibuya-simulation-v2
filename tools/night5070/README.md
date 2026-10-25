# tools/night5070 — 寝ている間に 5070 で実験を回す

回答 10-25 §6-0 の仕組み。src/ は読まず変えず、ランの出力のファイルだけを読む。運用の手順は [docs/ops/night5070-runbook.md](../../docs/ops/night5070-runbook.md)。

## 使い方(リポの根で)

```
.venv\Scripts\python.exe tools/night5070/night_run.py --experiment E1 --dry-run      # 何をするかを並べるだけ(艦隊もランも動かさない)
python tools/night5070/night_run.py --experiment E1                # 本番(艦隊を立てる → 健全性 → 実験 → 一覧 → 落とす)
python tools/night5070/register_task.py --at 01:00 --experiment E1 --print-only   # タスクの XML を見る
python tools/night5070/register_task.py --at 01:00 --experiment E1 [--wake] [--daily]   # 登録
python tools/night5070/register_task.py --delete                   # 消す
```

`--keep-fleet` を付けると最後に艦隊を落とさない。`--out` で小さな記録の根(既定 `docs/bench/night5070`)、`--data-out` で大きな出力とログの根(既定 `data/night5070`=gitignore の中)を変える。`--deadline-hours`・`--start-at` はタスクから渡る。ラン中は Windows のスリープを止める。終了コード: 0 成功/1 失敗/2 実験の名が無い/3 設定の穴/4 成功(艦隊を落とす段に失敗)。

## 設定の穴の埋め方(experiments.json)

- コマンドの中の `{{名}}` は `vars` の値で埋まる。値が `null` の名が穴で、穴が残ったまま本番を回すと艦隊を立てる前に止まる(終了コード 3)。`--dry-run` の要約に穴の一覧が出る。
- 艦隊: `WSL_DISTRO`・`MODEL`・`VLLM_BIN`・`VLLM_ENV`・`VLLM_ARGS`(要らなければ空の文字列 `""`)。説明は `vars_note`。
- 腕の引数(`E2_ARM_FLAGS` など)は JSON の配列で書く。要素がちょうど `{{名}}` の所に 1 つずつ差し込まれる。
- `estimated_minutes` は R-C の答申で埋める(空欄なら要約に「空欄」と出る)。`cost.yen_per_hour` を入れると円/シミュ日を出す。
- 実行時に埋まる名: `OUT`(小さな記録の置き場)・`DATA`(大きな出力の置き場)・`PYTHON`・`REPO`・`RUN_ID`・`ENDPOINTS`・`EXPERIMENT`。
- 艦隊の起動は既定では tmux で切り離す(コマンドはすぐ返る)。前景で回すコマンドにするなら `fleet.start.background` を `true` にし、`fleet.stop` も `wsl.exe -d <配布> -- pkill -f 'vllm serve'` に替える。`fleet.model` に期待する served-model-name を入れると健全性の確認で照合する。

## 朝に読むファイル(`docs/bench/night5070/<YYYY-MM-DD>_<実験>/`。大きな出力とログは `data/night5070/<同じ名>/`)

| ファイル | 中身 |
|---|---|
| `summary.md` | 成功/失敗・開始と終了・壁時計・呼数・エラーの先頭 20 行・結果の置き場・各実験の見積り |
| `metrics.md`・`metrics.json` | 計測の分離の一覧(§6-7)。欄ごとに出所(ファイルと鍵)を書き、取れない欄は「未計測」 |
| `night_run.json` | 段ごとの状態・秒・コマンド・ログの置き場 |
| `NIGHT_DONE` | 終わった印(中身は結果) |
| `data/night5070/<…>/logs/*.log` | 各コマンドの標準出力と標準エラー(gitignore の中) |
| `../_night_runs.log`・`../_scheduler.log` | 夜ごとの 1 行の記録・タスクの起動の出力 |

同じ日に 2 回回すと `_r2` を足す(上書きしない)。要約と一覧と `_night_runs.log` の道筋は `<REPO>`・`<HOME>`・`<PYTHON>`・`<WSLHOME>` に置き換える。ログは置き換えない。
