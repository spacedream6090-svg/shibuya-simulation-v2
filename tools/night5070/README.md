# tools/night5070 — 寝ている間に 5070 で実験を回す

回答 10-25 §6-0 の仕組み。src/ は読まず変えず、ランの出力のファイルだけを読む。運用の手順は [docs/ops/night5070-runbook.md](../../docs/ops/night5070-runbook.md)。

> **src の差分 1 件=ユーザーの判断待ち**: 艦隊のクライアント `src/shibuya/llm/fleet.py` が環境変数 `SHIBUYA_FLEET_API_KEY` を読んで `Authorization: Bearer` を付ける差分(10 行余り・変数が無ければ要求はこれまでと同じ・試験 `tests/llm/test_fleet_auth.py`)を作業木 stage/n5070-1101 に用意した。src の解除の範囲(11-01p の段 0〜3・5)の外なので、取り込むかはユーザーが決める。取り込むまでは、vLLM を API key つきで立てると `shibuya.cli` の呼が 401 で通らない(試走 `--smoke` は「応答 0(401 の疑い)」で失敗する見込み)。

## 使い方(リポの根で)

```
.venv\Scripts\python.exe tools/night5070/night_run.py --experiment E1 --dry-run      # 何をするかを並べるだけ(艦隊もランも動かさない)
.venv\Scripts\python.exe tools/night5070/night_run.py --experiment E1 --dry-run --smoke   # 試走で何を回すかを並べる
python tools/night5070/night_run.py --experiment E1 --smoke        # 試走(E1 を 500 体 × 120 刻みで。一連が通るかだけを見る)
python tools/night5070/night_run.py --experiment E1                # 本番(前の艦隊を落とす → 検査 → VRAM → 立てる → 健全性 → 実験 → 応答の確認 → 一覧 → 落とす)
python tools/night5070/register_task.py --at 01:00 --experiment E1 --print-only   # タスクの XML を見る
python tools/night5070/register_task.py --at 01:00 --experiment E1 [--wake] [--daily]   # 登録
python tools/night5070/register_task.py --delete                   # 消す
```

`--keep-fleet` を付けると最後に艦隊を落とさない。`--out` で小さな記録の根(既定 `docs/bench/night5070`)、`--data-out` で大きな出力とログの根(既定 `data/night5070`=gitignore の中)を変える。`--deadline-hours`・`--start-at` はタスクから渡る。ラン中は Windows のスリープを止める。

段の順: 設定を読む → 安全の規則の検査(WSL を起動しない検査=設定・環境・argv の形。違えば前の艦隊を落とす段もしない)→ 前の艦隊を落とす(前の夜の残りの掃除・失敗は無視して進む)→ 空き VRAM の確認(使用量が落ち着くまで待つ・足りなければ 1 回測り直す)→ 安全の規則の再検査(VRAM の調整で書き換えた後の argv に)→ 鍵のファイル → 艦隊を立てる → 健全性の確認 → 実験 → 応答の確認(E1 と試走)→ 艦隊を落とす → 鍵のファイルを消す → 記録。前の夜の艦隊が VRAM を持ったままでも、落として返し終わってから測る。

| 終了コード | 意味 |
|---|---|
| 0 | 成功・dry-run |
| 1 | 失敗(コマンドの失敗・健全性の確認・締め切り・E1 と試走の「応答 0」)。後始末にも失敗したときは 4 を優先し、要約に両方を書く(結果「失敗(後始末にも失敗)」) |
| 2 | 引数と設定の誤り(argparse の誤り・実験の名が無い・`--smoke` でその実験に `smoke` の定義が無い)。`register_task.py` は主体がユーザー権限でない・締め切りが上限以上・作業木から登録しようとしたときも 2 |
| 3 | 設定の穴が残っている・`fleet.vram` や `VLLM_ARGS` の数が読めない |
| 4 | 成功(艦隊を落とす段に失敗)。朝に `wsl --shutdown` を手で |
| 5 | 安全の規則に違う(艦隊は立てていない) |
| 6 | VRAM が足りない(空きが重み + 2 GB を下回る・艦隊は立てていない) |

## 試走 `--smoke`

実験の定義の `smoke.vars` を `vars` に重ねて回す。E1 は `{"AGENTS": 500, "TICKS": 120}`(既定の `vars` は `AGENTS` 5,000・`TICKS` 1,440=1 日)。置き場の名に `_smoke` を足し、`summary.md` と `night_run.json` に `smoke: true` の印を付ける。ランの名は `night5070-E1-smoke-<日時>`。`--dry-run` と併せると、回すはずのコマンドが 500 体 × 120 刻みで並ぶ。結果の数字は見ない(見るのは動いたか・所要・呼数・VRAM)。
- 刻み数は `smoke.vars.TICKS` で延ばせる(既定 120=0〜2 時。mock では 500 体 × 120 刻みで LLM の呼が 14 本)。
- 昼の窓で試走するには、src の側に開始の刻みの引数が要る(段 3 の問い)。今は 0 時から回る。

E1(試走を含む)は `require_answers: true` で、成否の条件に「テープの応答数 > 0」を足す。応答数は、繰り延べでなく出力トークンが 1 以上の行の数(4xx などで本文が空の行は数えない)。テープに `tokens_out` の列が無いときは、繰り延べでない行の数で数える(4xx の行が繰り延べでないとして記録されると 0 にならないので、いまのテープの形=列ありを前提にしている)。見るのは 0 かどうかだけで、数は要約に出さない(呼数は参考値のまま)。0 なら失敗(終了コード 1・要約に「応答 0(401 の疑い)」)。テープが無いか読めなければ「応答数 未計測」で失敗にする。

## 空き VRAM と起動の値の自動の調整

机上のアプリは閉じない前提で、艦隊を立てる前に `nvidia-smi --query-gpu=memory.total,memory.used --format=csv,noheader,nounits` を読む(読み取りだけ。1 枚目の GPU)。空き=総量−使用。GB は GiB(1,024 MiB)。

- `--gpu-memory-utilization` = min(設定の値, floor((空き − 0.5 GB) ÷ 総量 を小数 2 桁))。
- `--max-num-seqs`: 空きが `VRAM_PLAN_GB`(設定の列の数で要ると想定する量)を下回るなら 32 → 16 → 8 と下げる。列 n で要る量は次の式と置く(**expedient**=KV が列の数に比例するという仮定。感度試験はしていない):
  `要る量(n) = MODEL_GB + 2 GB + (VRAM_PLAN_GB − MODEL_GB − 2 GB) × n ÷ 設定の列の数`。32 から順に、空きが要る量(n)以上になる最初の n を使う。8 でも足りなければ 8 を使う。
- 穴の出どころ: `MODEL_GB` = 5.68(R-123 §3 の Qwen3-8B-AWQ の safetensors 2 本=5,816 MiB。親の指示 11-01 で埋めた)。`VRAM_PLAN_GB` は穴のまま(親が後で埋める。出どころの案は R-123 §2 の構成=`--gpu-memory-utilization 0.78` × 12,227 MiB ≈ 9,537 MiB ≈ 9.31 GiB)。
- 前の艦隊を落とした後、`nvidia-smi` を 2 秒ごとに読み、使用量が連続 2 回同じ値になるか 60 秒で打ち切るまで待ってから測る(2 秒・60 秒は expedient)。要約に「VRAM の待ち: 待った秒数・前後の使用量・読んだ回数」を書く。
- 空きが「重み(`MODEL_GB`)+ 2 GB」を下回れば、1 回だけ測り直す(要約に「VRAM の測り直し」)。それでも足りなければ、要約に「足りない」と書き、艦隊を立てずに終了コード 6。
- `VLLM_ARGS` を JSON の配列で書き、argv の 1 要素を `{{VLLM_ARGS}}` にした形では、調整の後も配列のまま要素に分けて差し込む。
- `nvidia-smi` が無い・読めないときは「未計測」と書き、設定の値のまま進める。
- 設定の値は `VLLM_ARGS` の `--gpu-memory-utilization`・`--max-num-seqs`。書いていなければ `fleet.vram` の `gpu_memory_utilization`(0.78=R-123 §2)・`max_num_seqs`(32)を使い、決めた値を `VLLM_ARGS` の末尾に足す。
- 決めた値は要約の「VRAM」の行と、計測の分離の一覧の欄「空き VRAM(起動前)」「gpu-memory-utilization(使った値)」「max-num-seqs(使った値)」に出る。

## 安全の規則

回答 11-01 の 5070 の指示書(`docs/design/prompt-2026-11-01-5070.md`)の「安全の規則」の文のまま:

1. 艦隊は `127.0.0.1` にだけ束縛。WSL は既定の NAT(mirrored にしない)。Windows のファイアウォールに受信の規則を足さない。API key を付け、クライアント側にだけ渡す。
2. `--load-format safetensors`。`trust_remote_code` は切る(判断モデルで trust_remote_code が要るものは候補から外し、その旨を表に)。重みの sha256 を台帳に。
3. pip は PyPI と pytorch.org だけ、版を固定(できれば hash つき)。重みは公式リポだけ。
4. ODPT の鍵などの環境変数を WSL に継承させない(`WSLENV` に入れない)。艦隊は鍵を必要としない。
5. 夜間のタスクはユーザー権限(SYSTEM にしない)。動かすのはリポの中のスクリプトだけ。Defender やネットワークの設定に触らない。
6. 以上を `tools/night5070/README` の「安全の規則」に書き、night_run の起動時に 1 と 2 を検査して、違えば起動しない。

### 各条に対応する検査

night_run の検査は、艦隊を使う実験の起動時(前の艦隊を落とす段の前=WSL を起動する前。VRAM の調整で argv を書き換えた後にもう一度)に、値を埋めた後の `fleet.start` のコマンド(`VLLM_ARGS` が入った形)と設定の `endpoints` と、子のコマンドに渡す環境変数に対して行う。起動のコマンドは `shlex` で語に切ってから見る(`bash -lc` の文字列の中もさらに切る。引用符は外れる)。`--host`・`--api-key`・`--load-format` は各ちょうど 1 回だけを合格にし、2 回以上・引用符つきの別の値・空の値・接頭辞の略記(`--hos`・`--load` など)は不合格。`--trust-remote-code` と `--config` は 1 回でもあれば不合格(略記も)。語に切れない文字列に旗の名があれば不合格。穴の `{{名}}` を埋めた後の語に `$`・バッククォート・`{`・`}` があれば不合格(シェルの展開は検査から見えないため。道筋は `$HOME` などを使わずにそのまま書く)。結果は要約の「安全の規則の検査」の表と `night_run.json` の `safety` に出る。

`--dry-run` では表に並べるだけで止めない。設定の穴が残っているときは、穴に依らない検査(`rule1.endpoints_loopback`・`rule1.wsl_nat`・`rule4.wslenv`)だけを判定し、起動のコマンドの要る 6 件(`rule1.vllm_host`・`rule1.api_key`・`rule2.safetensors`・`rule2.no_trust_remote_code`・`rule2.no_config_file`・`rule12.no_shell_expansion`)は「未判定」として要約の「未判定の規則」に並べる。出荷の設定(`VLLM_ARGS` などが穴)の dry-run はいつもこの形になる。

| 条 | 検査の名 | どこで | 失敗のとき |
|---|---|---|---|
| 1 | `rule1.endpoints_loopback` — 設定の `endpoints` の host が `127.0.0.1` だけ(`localhost` も不可) | night_run の起動時 | 艦隊を立てない・終了コード 5 |
| 1 | `rule1.vllm_host` — `--host 127.0.0.1` がちょうど 1 回(略記なし) | 同上 | 同上 |
| 1 | `rule1.api_key` — `VLLM_ENV` の**先頭の語**が `VLLM_API_KEY={{API_KEY}}`(推奨・起動のコマンドにその語がある・VLLM_ENV の中の `VLLM_API_KEY=` はちょうど 1 回)か、`--api-key {{API_KEY}}` がちょうど 1 回。両方無い・`--api-key` が 2 回以上・値が空か違う・略記は不合格。文字列のほかの場所の `VLLM_API_KEY=` は数えない | 同上 | 同上 |
| 1 | `rule1.wsl_nat` — ホームの `.wslconfig` の `networkingMode` が未記入か `nat`(mirrored・bridged などは不合格。ファイルが無ければ既定の NAT) | 同上 | 同上 |
| 2 | `rule2.safetensors` — `--load-format safetensors` がちょうど 1 回(略記なし) | 同上 | 同上 |
| 2 | `rule2.no_trust_remote_code` — `trust-remote-code`(`trust_remote_code`)の文字列・旗・略記が無い | 同上 | 同上 |
| 2 | `rule2.no_config_file` — `--config` が無い(設定のファイルの中の host や trust_remote_code は検査で見えない) | 同上 | 同上 |
| 1・2 | `rule12.no_shell_expansion` — 起動のコマンドの語に `$`・バッククォート・`{`・`}` が無い(`$VAR`・`$(…)`・`$'--host'` などのシェルの展開で検査を隠せないように) | 同上 | 同上 |
| 4 | `rule4.wslenv` — 艦隊のコマンド(wsl.exe)に渡す環境から `WSLENV` を外す(Windows の環境変数を WSL に継承させない)。そのうえで `WSLENV` に鍵らしい名(`KEY`・`TOKEN`・`SECRET` を `_` で区切られた部分に持つ名、または `PASSWORD`・`PASSWD`・`APIKEY`・`CREDENTIAL(S)` を含む名。例 `ODPT_API_KEY`・`HF_TOKEN`・`DB_PASSWORD`)があれば不合格(名だけを見る・値は読まない) | 同上 | 同上 |
| 5 | `rule5.task_principal` — タスクの XML の `<UserId>` が登録する本人で、SYSTEM・LocalService・NetworkService・機械のアカウント(末尾 `$`)でない・`<LogonType>InteractiveToken`・`<RunLevel>LeastPrivilege`・`<GroupId>` が無い(`register_task.check_principal_xml`) | register_task の XML を作るとき | 登録しない・終了コード 2 |
| 5 | `rule5.task_workdir` — 登録するリポの根が作業木でない(道筋に `wt_` で始まる部分がある・`.git` がファイル=git worktree なら登録しない。`--print-only` は注を出すだけ) | register_task の登録のとき | 登録しない・終了コード 2 |
| 1・5 | `rule5.no_firewall_calls` — `night_run.py` と `register_task.py` と `experiments.json` のコマンド(argv)に、ファイアウォール・Defender・ネットワークの設定を変える呼び(`netsh`・`New-NetFirewallRule`・`Set-MpPreference` など)が無い | 試験(`tests/tools/test_night5070.py`) | 試験が落ちる |
| (VRAM) | 空きが「重み + 2 GB」を下回る(前の艦隊を落とし、使用量が落ち着くまで待ってから測る・足りなければ 1 回測り直す) | night_run の起動時 | 艦隊を立てない・終了コード 6 |

2 の「重みの sha256 を台帳に」と 3(pip の出所と版の固定)は機械の検査が無い。取得の手順(runbook)と親の検収で守る。

### API key の扱い

- 艦隊を使う実験の本番では、ランごとに `secrets.token_urlsafe(32)` で鍵を作り、大きな出力の置き場の `api_key` に置く(新しく作る・POSIX では本人だけが読める 0o600)。Windows では作った直後に `icacls <file> /inheritance:r /grant:r <USERNAME>:F` で本人だけに絞る(失敗しても続け、要約の「鍵のファイルの ACL」の行に書く。行にユーザー名は書かない)。艦隊を落とした後(後始末の段の後)に消し、要約に「API key のファイル: 消した」と 1 行書く(`--keep-fleet` でも消す。艦隊はまだ鍵を持つ)。
- vLLM への渡し方は 2 つ。推奨は `VLLM_ENV` の先頭の語に `VLLM_API_KEY={{API_KEY}}`(vLLM のプロセスの引数には出ない。wsl.exe の起動の引数=`bash -lc` の文字列には出る)。`VLLM_ARGS` に `--api-key {{API_KEY}}` でもよい。どちらかが無ければ起動しない(終了コード 5)。vLLM が `VLLM_API_KEY` を読むことは、使う版で確かめていない(未確認)。
- 健全性の確認の 2 本の呼(`/v1/models` と `/v1/chat/completions`)に `Authorization: Bearer` で付ける。
- 実験のコマンド(`shibuya.cli`)には環境変数 `SHIBUYA_FLEET_API_KEY` で渡す(実験のコマンドの環境にだけ入れる。艦隊の起動・落とすコマンドの環境からは外す)。受け口の src の差分はユーザーの判断待ち(冒頭の注)。
- 要約・計測の一覧・`night_run.json`・`_night_runs.log` は、書くときに鍵の値を `<API_KEY>` に置き換える(コマンドの並びも書くときに置き換える)。`data/night5070/<…>/logs/*.log` は、そのコマンドが終わった直後に置き換え、最後にもう一度全部を見直す。`--dry-run` の鍵は印 `<API_KEY>` のまま。
- 鍵が残る場所(night_run は手を入れない): ①そのコマンドが動いている間の、そのコマンドのログ(背後で起動した艦隊のログは最後まで) ②WSL の中の vLLM のログ(`VLLM_LOG`。vLLM が起動の引数を写す。night_run が集めた末尾 200 行の写しは置き換える) ③WSL の中のプロセスの一覧(引数の形 `--api-key` のとき)と、Windows の `wsl.exe` の起動の引数(どちらの形でも。同じ人の別のプロセスから読める) ④ラン中の `api_key` のファイル(ラン後に消す)。

## E1 の開始の合図

E1 の本番は、ユーザーの合図を待ってから始める(試走 `--smoke` と判断モデルの比較は合図なしで進める)。ユーザーが送る一言は次の形:

> E1 を今夜 HH:MM に

親はその時刻で `register_task.py --at HH:MM --experiment E1 --wake` を登録する(登録は合図を受けたときだけ。それまでは `--print-only` で中身を確かめるだけ)。登録の前に `--print-only` で XML の主体(`<UserId>` は表示では `<USER>`)・`WakeToRun`・締め切りを見る。登録は本体のリポの根から回す(XML の `WorkingDirectory` と `Set-Location` はスクリプトの位置から求めたリポの根になるため。作業木から登録しようとすると終了コード 2 で止まる)。終わりの見込みは試走の実測で更新した要約の表で見る。

## 設定の穴の埋め方(experiments.json)

- コマンドの中の `{{名}}` は `vars` の値で埋まる(`vars` の値の中の `{{名}}` も埋まる。例 `VLLM_ARGS` の中の `{{API_KEY}}`)。値が `null` の名が穴で、穴が残ったまま本番を回すと艦隊を立てる前に止まる(終了コード 3)。`--dry-run` の要約に穴の一覧が出る。
- 艦隊: `WSL_DISTRO`・`MODEL`・`VLLM_BIN`・`VLLM_ENV`(推奨 `VLLM_API_KEY={{API_KEY}}`)・`VLLM_ARGS`(安全の規則の検査に `--host 127.0.0.1 --load-format safetensors` が要る)・`MODEL_GB`(5.68)・`VRAM_PLAN_GB`(穴)。説明は `vars_note`。
- 腕の引数(`E2_ARM_FLAGS` など)は JSON の配列で書く。要素がちょうど `{{名}}` の所に 1 つずつ差し込まれる。
- `estimated_minutes` は R-C の答申で埋める(空欄なら要約に「空欄」と出る)。`cost.yen_per_hour` を入れると円/シミュ日を出す。
- 実行時に埋まる名: `OUT`(小さな記録の置き場)・`DATA`(大きな出力の置き場)・`PYTHON`・`REPO`・`RUN_ID`・`ENDPOINTS`・`EXPERIMENT`・`API_KEY`。
- 艦隊の起動は既定では tmux で切り離す(コマンドはすぐ返る)。前景で回すコマンドにするなら `fleet.start.background` を `true` にし、`fleet.stop` も `wsl.exe -d <配布> -- pkill -f 'vllm serve'` に替える。`fleet.model` に期待する served-model-name を入れると健全性の確認で照合する。

## 朝に読むファイル(`docs/bench/night5070/<YYYY-MM-DD>_<実験>/`。大きな出力とログは `data/night5070/<同じ名>/`)

| ファイル | 中身 |
|---|---|
| `summary.md` | 成功/失敗・開始と終了・壁時計・呼数・VRAM・安全の規則の検査・エラーの先頭 20 行・結果の置き場・各実験の見積り |
| `metrics.md`・`metrics.json` | 計測の分離の一覧(§6-7)。欄ごとに出所(ファイルと鍵)を書き、取れない欄は「未計測」 |
| `night_run.json` | 段ごとの状態・秒・コマンド・ログの置き場・`smoke`・`safety`・`vram` |
| `NIGHT_DONE` | 終わった印(中身は結果) |
| `data/night5070/<…>/logs/*.log` | 各コマンドの標準出力と標準エラー(gitignore の中) |
| `data/night5070/<…>/api_key` | ランごとの鍵(gitignore の中・ラン後に消す) |
| `../_night_runs.log`・`../_scheduler.log` | 夜ごとの 1 行の記録・タスクの起動の出力 |

同じ日に 2 回回すと `_r2` を足す(上書きしない)。試走は `_smoke`、空実行は `_dryrun` を足す。要約と一覧と `_night_runs.log` の道筋は `<REPO>`・`<HOME>`・`<PYTHON>`・`<WSLHOME>` に置き換える。ログの道筋は置き換えない(鍵の値だけ置き換える)。
