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
5. 安全の規則の検査が通る形にする(README「安全の規則」): `VLLM_ENV` に `VLLM_API_KEY={{API_KEY}}`(推奨。`VLLM_ARGS` の `--api-key {{API_KEY}}` でもよい)、`VLLM_ARGS` に `--host 127.0.0.1 --load-format safetensors` を入れ、`--trust-remote-code` は書かない。艦隊のクライアントが鍵を送る src の差分は、ユーザーが取り込みを決めるまで入っていない(README の冒頭の注)。`endpoints` は `http://127.0.0.1:<口>` だけ。`WSLENV` に鍵らしい名(`*_KEY`・`*_TOKEN`・`*_SECRET` を含む名)を入れない(艦隊のコマンドには `WSLENV` 自体を渡さない)。`--host`・`--api-key`・`--load-format` は各 1 回だけ書き、略記(`--hos` など)と `--config` は使わない。ホームの `.wslconfig` に `networkingMode` の mirrored を書かない。違えば night_run は艦隊を立てずに終了コード 5 で止まり、要約の「安全の規則の検査」の表に不合格の検査の名が出る。dry-run で穴が残っていると、起動のコマンドの要る検査は「未判定」と出る(穴を埋めた写しの設定で `--dry-run --config <写し>` を回すと全部を前もって確かめられる)。
6. VRAM の調整の穴: `MODEL_GB` は 5.68 で埋めた(R-123 §3 の Qwen3-8B-AWQ=5,816 MiB)。`VRAM_PLAN_GB`(設定の `--max-num-seqs` で要ると想定する量)は親が埋める(案=R-123 §2 の 0.78 × 12,227 MiB ≈ 9.31 GiB)。起動の値の既定は `fleet.vram`(`gpu_memory_utilization` 0.78・`max_num_seqs` 32・下げ方 32 → 16 → 8・余白 0.5 GB・重みの上の余裕 2 GB)。

### 1-2. 試走(`--smoke`・合図なしで回してよい)

回答 11-01 の 5070 の完了の条件 4。E1 を 500 体 × 120 刻みで回し、一連(検査 → 艦隊を立てる → 健全性 → 実験 → 一覧 → 落とす → 要約)が壊れずに通るかだけを見る。結果の数字は見ない。

```
.venv\Scripts\python.exe tools/night5070/night_run.py --experiment E1 --dry-run --smoke   # 何を回すか(--agents 500 --ticks 120)を見る
.venv\Scripts\python.exe tools/night5070/night_run.py --experiment E1 --smoke             # 試走
```

- 置き場は `docs/bench/night5070/<日>_E1_smoke/`(大きな出力は `data/night5070/<同じ名>/`)。要約の先頭に「試走 --smoke」、`night_run.json` に `smoke: true`。
- 見るもの: 結果・壁時計・呼数(参考値)・VRAM の行(空き・使った `--gpu-memory-utilization` と `--max-num-seqs`)・安全の規則の検査の表・健全性の確認の秒。
- 試走の壁時計で所要時間の見積り(`estimated_minutes`)を更新するのは親の作業(更新したら本書の冒頭の注に日付と出典を 1 行)。

### 1-3. 空き VRAM の自動の調整(机上のアプリは閉じない)

night_run は前の夜の艦隊を落とした後(使用量が連続 2 回同じになるまで 2 秒ごとに読む・最長 60 秒)、艦隊を立てる前に `nvidia-smi --query-gpu=memory.total,memory.used --format=csv,noheader,nounits` を読み(読み取りだけ)、`VLLM_ARGS` の `--gpu-memory-utilization` と `--max-num-seqs` を書き換えてから起動する。式は README「空き VRAM と起動の値の自動の調整」。

| 起動前の空き | night_run がすること |
|---|---|
| `VRAM_PLAN_GB` 以上 | `--max-num-seqs` はそのまま(32)。`--gpu-memory-utilization` は min(設定, floor((空き − 0.5)÷総量)) |
| `VRAM_PLAN_GB` 未満 | `--max-num-seqs` を 16、さらに足りなければ 8 に下げる(列ごとの量は KV が列に比例と置く=expedient) |
| `MODEL_GB` + 2 GB 未満 | 1 回測り直し、それでも足りなければ要約に「足りない」と書き、艦隊を立てずに終了コード 6。机上のアプリを手で閉じるか、夜に回し直す |
| `nvidia-smi` が読めない | 「未計測」と書き、設定の値のまま起動を試す |

起動した後に KV の場所が足りずに落ちたときは、§4 の「健全性の確認」の行と R-123 §6 の「VRAM 不足」を見る(util を 0.05 ずつ下げる・`--max-num-batched-tokens 2048` など)。

## 2. 登録

```
.venv\Scripts\python.exe tools/night5070/register_task.py --at 01:00 --experiment E1 --print-only   # XML を見る
.venv\Scripts\python.exe tools/night5070/register_task.py --at 01:00 --experiment E1 --wake         # 登録(次の 01:00 に 1 回)
schtasks /query /tn \shibuya-v2-night5070 /v /fo LIST                              # 確かめる
```

- 時刻はユーザーが決める(既定の案は 01:00)。終わりの見込みは要約の表(「01:00 に始めたときの終わり」)で見る。
- E1 の本番の登録は、ユーザーの合図「E1 を今夜 HH:MM に」を受けてから、親が `register_task.py --at HH:MM --experiment E1 --wake` で行う(README「E1 の開始の合図」)。それまでは `--print-only` で中身を見るだけ(`schtasks /create` は合図の前には回さない)。
- 合図のときの登録の試し(1 回だけ・UserId つきの XML が通るかを見る):
  1. `register_task.py --at HH:MM --experiment E1 --wake --print-only` で `<UserId>`(表示は `<USER>`)・`<LogonType>InteractiveToken`・`<RunLevel>LeastPrivilege`・`WakeToRun` を見る。
  2. 試しの名で登録する: `register_task.py --at HH:MM --experiment E1 --name shibuya-v2-night5070-try`。パスワードを求められずに通るか、`schtasks /query /tn \shibuya-v2-night5070-try /v /fo LIST` の「実行するユーザー」が本人で「ログオン モード」が対話型だけかを見る。
  3. 試しを消す: `register_task.py --delete --name shibuya-v2-night5070-try`。
  4. 通ったら本番の名で登録する(`--name` を付けない)。通らなければ登録せず、エラーの文を要約にしてユーザーに返す。
  - どれも本体のリポの根から回す(作業木から回すと register_task は終了コード 2 で止まる。XML の `WorkingDirectory` と `Set-Location` がスクリプトの位置から求めたリポの根になるため)。
- タスクはユーザー権限で動く(安全の規則 5): XML の `<UserId>` は登録する本人・`<LogonType>InteractiveToken`・`<RunLevel>LeastPrivilege`。SYSTEM などになる形は register_task が作らない(終了コード 2)。`--print-only` の表示では `<UserId>` を `<USER>` に置き換える。
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
| 安全の規則の検査(終了コード 5) | `--host 127.0.0.1`・API key(`VLLM_ENV` の先頭の `VLLM_API_KEY=` か `--api-key`)・`--load-format safetensors` が無いか 2 回以上・略記・`--trust-remote-code` か `--config` がある・`endpoints` が `127.0.0.1` でない・`WSLENV` に鍵らしい名・`.wslconfig` が mirrored | `summary.md` の「安全の規則の検査」の表(艦隊は立てていない。WSL を起動しない検査なので、前の艦隊を落とす段も回っていない。VRAM の調整の後の再検査で落ちたときは「安全の規則の再検査」の行) |
| 空き VRAM の確認(終了コード 6) | 空きが「重み + 2 GB」を下回る(机上のアプリが VRAM を使っている) | `summary.md` の「VRAM」の行。閉じられるアプリを閉じるか、時刻を替える |
| 空き VRAM の確認(終了コード 3) | `MODEL_GB`・`VRAM_PLAN_GB`・`VLLM_ARGS` の数が読めない | `summary.md` の失敗した段 |
| 応答の確認(終了コード 1) | テープの応答数が 0(要約に「応答 0(401 の疑い)」)。艦隊のクライアントが鍵を送っていない(src の差分が未取り込み)・served-model-name の違い・書式の全滅など。テープが無いか読めなければ「応答数 未計測」 | `logs/exp_*.stdout.log` の `[艦隊]` の行・`logs/fleet_log.stdout.log` |
| 艦隊を立てる | WSL の配布の名・vllm の置き場の誤り・tmux が無い | `data/night5070/<…>/logs/fleet_start.stderr.log` |
| 健全性の確認 | モデルの読み込みが `health.wait_s`(900 秒)を超えた・GPU のメモリ不足・口の番号の違い・served-model-name の違い | `logs/fleet_log.stdout.log`(vLLM のログの末尾 200 行) |
| 実験 | コードの例外・繰り延べの溢れ・締め切り(9.5 時間)の超過 | `summary.md` のエラーの先頭 20 行・`logs/exp_*.stderr.log` |
| 艦隊を落とす(終了コード 4) | tmux の会話の名の違い・既に落ちていた | `logs/fleet_stop.stderr.log`。落ちていなければ `wsl --shutdown` を手で |
| 計測の一覧の欄が「未計測(読めない: …)」 | ランが途中で落ちてテープや checkpoints が壊れている | 要約と一覧は書かれる。元のファイルは大きな出力の置き場 |

- 失敗しても艦隊は落とす(`--keep-fleet` のときだけ残す。残したときは要約にそう書く)。
- 途中で止まった段より後のコマンドは回さない。
- 同じ日に回し直すと `_r2` の置き場に書く(前の結果は消さない)。
