# 5070 の夜の実験の運用手順

回答 10-25 §6-0 の「寝ている間に回す仕組み」の手順書。道具は [tools/night5070](../../tools/night5070/README.md)。

> **R-C の答申が出たら親が追記する**: 艦隊の起動のコマンド(WSL2 の配布・vLLM の版と引数・tmux の要否)、各実験の所要時間の見積り(`estimated_minutes`)、円/シミュ日の単価(`cost.yen_per_hour`)。追記したら、この節の下に日付と出典を 1 行ずつ書く。

## 0. 前提

- E1 は、2-7(返事待ちの体への再送の穴)を直す前は「動くかどうかの確認」に限る。呼数の計測は 2-7 の後(回答 10-25 §6-0)。
- E3・E4(30 日)は §6-1 の 3(開始日検査の上限ほか)の後でないと開始日検査で止まる。
- タスクは「対話のログオンのときだけ」動く(WSL2 はユーザーのセッションで動くため)。サインアウトしない。画面のロックは構わない。ラン中は night_run がスリープを止める(`SetThreadExecutionState`・終わりに戻す)。始まる前のスリープは `--wake` で起こす。
- 電池で動いているときも始め、電池に切り替わっても止めない(ODPT の取得タスクとの違い)。
- ランは本体のリポの根で回す(`data/world/v2` などの data が要る。作業木には data が無い)。
- 出力は 2 か所に分かれる。小さな記録(`summary.md`・`metrics.json`・`metrics.md`・`night_run.json`・`NIGHT_DONE`)は `docs/bench/night5070/<YYYY-MM-DD>_<E>/`、根に `_night_runs.log` と `_scheduler.log`。大きな出力(テープ・状態の npz・checkpoints.json)とログは `data/night5070/<YYYY-MM-DD>_<E>/`(gitignore の中)。

## 1. 登録の前(昼のうちに)

1. 設定の穴を埋める: `tools/night5070/experiments.json` の `vars`(説明は `vars_note`)。
2. 空実行で確かめる: `.venv\Scripts\python.exe tools/night5070/night_run.py --experiment E1 --dry-run`。要約の「設定の穴」が空で、「回すはずのコマンド」が意図どおりかを見る。
3. 艦隊だけを手で試す(任意): `fleet.start` のコマンドを手で回し、`curl http://127.0.0.1:8000/v1/models` が返るか、`fleet.stop` で落ちるかを見る。WSL が切り離した過程を残さない場合は `fleet.start.background` を `true` にし、vLLM を前景で回すコマンドに替える。そのときは `fleet.stop` も `wsl.exe -d <配布> -- pkill -f 'vllm serve'` に替える(tmux の会話が無いため)。起動の前にも stop を 1 回回す(前の夜の残りの掃除・失敗は無視)。
   `fleet.model` に期待する served-model-name を入れると、健全性の確認で `/v1/models` の名と照合する(空なら照合しない)。
4. ランの前の確認(docs/ops/v2-server-lessons.md §9 B): mock 5,000 体の checkpoint が手元と同じか・1 呼の全体の締め切りがあるか(`--fleet-wait-s`)・書き終わりが規模に対して有界か。

## 2. 登録

```
.venv\Scripts\python.exe tools/night5070/register_task.py --at 01:00 --experiment E1 --print-only   # XML を見る
.venv\Scripts\python.exe tools/night5070/register_task.py --at 01:00 --experiment E1 --wake         # 登録(次の 01:00 に 1 回)
schtasks /query /tn \shibuya-v2-night5070 /v /fo LIST                              # 確かめる
```

- 時刻はユーザーが決める(既定の案は 01:00)。終わりの見込みは要約の表(「01:00 に始めたときの終わり」)で見る。
- 毎晩回すなら `--daily`。実験を替えるときは同じ名で登録し直す(`/f` で上書き)。消すときは `--delete`。
- 起動は ODPT のタスクと同じ形(`powershell.exe -NoProfile -WindowStyle Hidden -Command "Set-Location …; & <python> tools/night5070/night_run.py … *>> docs/bench/night5070/_scheduler.log"`)。登録は本体の `.venv` の python で行う(その python がタスクの python になる)。
- 実行時間の上限はタスクが `--max-hours`(既定 10 時間)、night_run の締め切りは上限 − 0.5 時間(艦隊を落とす時間を残す)。締め切りが上限以上なら登録しない。

## 3. 朝の確認

1. `docs/bench/night5070/_night_runs.log` の最後の行で、結果と置き場を見る。night_run が起動する前に落ちたときは `_scheduler.log` を見る。
2. その置き場の `summary.md` を読む(成功/失敗・壁時計・呼数・エラーの先頭 20 行)。先頭に「艦隊が落ちていない」と出ていたら `wsl --shutdown` を手で回す(結果は「成功(後始末に失敗)」・終了コード 4)。E1 の呼数は 2-7 の直しの前の参考値。
3. 成功なら `metrics.md` で計測の分離の一覧を見る(§6-7)。「未計測」の欄は、ランの出力に元の数が無いもの。
4. ラン後の確認(v2-server-lessons.md §9 C): 保存則・センサス・繰り延べ・書式エラーを最初に見る。テープから再集計して一致するか。
5. git に入れるかは親が決める。入れるのは `docs/bench/night5070/` の小さな記録だけ(大きな出力とログは `data/night5070/` にあり git に入らない)。入れる前に道筋の検査(`tools/commit_check.py --paths-only`)を回す。

## 4. 失敗の型

| 失敗した段 | よくある原因 | 見る所 |
|---|---|---|
| 設定を読む(終了コード 3) | 穴が残っている | `summary.md` の「設定の穴」 |
| 艦隊を立てる | WSL の配布の名・vllm の置き場の誤り・tmux が無い | `data/night5070/<…>/logs/fleet_start.stderr.log` |
| 健全性の確認 | モデルの読み込みが `health.wait_s`(900 秒)を超えた・GPU のメモリ不足・口の番号の違い・served-model-name の違い | `logs/fleet_log.stdout.log`(vLLM のログの末尾 200 行) |
| 実験 | コードの例外・繰り延べの溢れ・締め切り(9.5 時間)の超過 | `summary.md` のエラーの先頭 20 行・`logs/exp_*.stderr.log` |
| 艦隊を落とす(終了コード 4) | tmux の会話の名の違い・既に落ちていた | `logs/fleet_stop.stderr.log`。落ちていなければ `wsl --shutdown` を手で |
| 計測の一覧の欄が「未計測(読めない: …)」 | ランが途中で落ちてテープや checkpoints が壊れている | 要約と一覧は書かれる。元のファイルは大きな出力の置き場 |

- 失敗しても艦隊は落とす(`--keep-fleet` のときだけ残す。残したときは要約にそう書く)。
- 途中で止まった段より後のコマンドは回さない。
- 同じ日に回し直すと `_r2` の置き場に書く(前の結果は消さない)。
