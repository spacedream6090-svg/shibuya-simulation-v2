# 独立検収: stage/n5070-1101(5070 の検証の準備・night5070 の安全の規則・--smoke・VRAM の調整)

- 検収役: Opus 5.5(実装を見ていない立場)・2026-11-01
- 対象: 作業木 `C:\wt_n5070`(枝 stage/n5070-1101・土台 a09809c)の未 commit の差分
- 発注の文: `docs/design/prompt-2026-11-01-5070.md`(「許可」「安全の規則」1〜6・「完了の条件」4・5・6)
- 書いたのは本書 1 本だけ。commit・add・子サブ・ネットワーク・艦隊の起動・タスクの登録・taskkill はしていない。自分の対照は scratchpad(以下 `<SCRATCH>`)の下で回した。

## 0. 判定

**条件つき受入。** 受入の条件は 2 つ。H1(VRAM の検査が前の艦隊を落とす段より先にある)を直すこと。H2(src の差分)の扱いをユーザーが決めること。安全の規則 1・2・4 の負の対照は 9 本とも終了コード 5 で止まり、艦隊を立てる段もコマンドも回らなかった。鍵の値は記録にもログにも残っていなかった。

### 検収中に作業木が変わった(先に報告)

検収を始めた 21:0x の時点では src/ の差分は無く、試験は 106 本だった。21:18〜21:25 に、検収役以外の誰かが次を書き換えた: `src/shibuya/llm/fleet.py`(+16 行)、新しい `tests/llm/test_fleet_auth.py`、`night_run.py`、`experiments.json`、`README.md`、runbook、`tests/tools/test_night5070.py`。21:20 には書きかけの状態で、`_remove_api_key_file` が未定義のまま呼ばれて NameError になっていた。そこで 4 分間変化が止まるのを待ち、21:25 の状態を検収した。本書の結論はすべて次の版のファイルについてのもの(sha256 の先頭 16 桁。21:32 に再確認して不変)。

| ファイル | sha256(先頭 16) |
|---|---|
| tools/night5070/night_run.py | 593da700de10f459 |
| tools/night5070/register_task.py | d6da0b7378820405 |
| tools/night5070/experiments.json | b6b286ef7ec7b4d3 |
| tools/night5070/README.md | 06cf8bdd93a9f8b8 |
| tests/tools/test_night5070.py | 743d0d39e96926fb |
| docs/ops/night5070-runbook.md | 80567d50d8e6f4fa |
| src/shibuya/llm/fleet.py | d618b9f2d96ebe96 |
| tests/llm/test_fleet_auth.py(未追跡) | 0f479acea95d36ac |

`git diff --stat a09809c` は 7 ファイル・+1,285/−73。うち src は `src/shibuya/llm/fleet.py` の 16 行。

## 1. 試験

- `tests/tools/test_night5070.py`: **114 passed**(検収を始めたときは 106 本。書き換えで 8 本増えた)
- `tests/llm/test_fleet_auth.py`: 4 passed(新しい試験。src の差分に付いている)
- コマンドは発注のとおり(`PYTHONIOENCODING=utf-8 PYTHONPATH=<wt>\src <本体>\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider -o addopts="" -rf …`)。

## 2. 自分の対照の結果

道具は `<SCRATCH>/rev/controls.py` と `<SCRATCH>/rev/leak.py`。設定の写しの穴は埋めて回した。`run_logged` を差し替えたので、艦隊の起動の段は無害な python に置き換わり、もし回れば印のファイルを残す。stop・collect_log・実験のコマンドも、印のファイルを書くだけの python に置き換えた。VRAM の値は `query_vram` を差し替えて与えた。

| 対照 | 結果 | 回ったコマンド | 鍵のファイル | NIGHT_DONE・summary |
|---|---|---|---|---|
| endpoints に `0.0.0.0` | rc 5・`rule1.endpoints_loopback` | なし | 無い | 有る |
| endpoints に `localhost` | rc 5・同上 | なし | 無い | 有る |
| `--host` 無し | rc 5・`rule1.vllm_host` | なし | 無い | 有る |
| `--host 0.0.0.0` | rc 5・同上 | なし | 無い | 有る |
| `--api-key` 無し(`VLLM_API_KEY=` も無し) | rc 5・`rule1.api_key` | なし | 無い | 有る |
| `--trust-remote-code` あり | rc 5・`rule2.no_trust_remote_code` | なし | 無い | 有る |
| `--load-format` 無し | rc 5・`rule2.safetensors` | なし | 無い | 有る |
| `WSLENV=FOO/u:ODPT_API_KEY/u`(環境を差し替え) | rc 5・`rule4.wslenv` | なし | 無い | 有る |
| VRAM の空き 6,227 MiB(重み 5.7 GB + 2 GB に足りない) | rc 5・失敗した段=空き VRAM の確認 | なし | 無い | 有る |
| VRAM の空き 10,727 MiB・健全性で落ちる | rc 1・util 0.78・seqs 32→16 | prestop・start・log・stop | ラン後に消えた | 有る |

- `--dry-run --smoke`(出荷の設定): rc 0。置き場の名は `2026-11-01_E1_smoke_dryrun`、要約の題に「試走 --smoke」、`--agents 500 … --ticks 120` が並んだ。data の置き場は作られない。ただし設定に穴が 9 個(MODEL・VLLM_ARGS・VLLM_BIN・VLLM_ENV・VRAM_PLAN_GB・WSL_DISTRO ほか)残っているため、安全の規則の検査は「未判定」と出た(L2)。
- `--smoke` を smoke の定義の無い実験(E3)に付けると rc 2。
- `register_task.py --at 01:00 --experiment E1 --wake --print-only`: rc 0。`<UserId>&lt;USER&gt;</UserId>`・`InteractiveToken`・`LeastPrivilege`・`WakeToRun true`・`PT10H`・`--deadline-hours 9.5` が出た。表示にユーザー名もドメイン名も出ない(python の道筋は `&lt;HOME&gt;`)。`USERNAME=SYSTEM` と `USERNAME=PC$` はどちらも rc 2 で登録しない。
- README の「安全の規則」の 1〜6 を、指示書の該当節と 1 行ずつ機械で突き合わせた: 6 行とも同じ文。

## 3. 鍵の漏れの検査

`leak.py` で鍵の値を既知の値に固定した。127.0.0.1 の上に偽の vLLM(Bearer が合わなければ 401)を立て、艦隊の起動のコマンドに引数を全部 echo させ、ログを集める段には `api_key=<鍵>` を echo させ、実験のコマンドには環境の `SHIBUYA_FLEET_API_KEY` を echo させた。そのうえで `--smoke` の本番の道筋を回した。

- rc 0。偽の vLLM が受けた Authorization は全部 `Bearer <正しい鍵>`(健全性の確認の 2 本)。
- ラン後に out と data の下の全ファイルを鍵の値で検索した: **0 件**。summary.md・metrics.json・metrics.md・night_run.json・NIGHT_DONE・_night_runs.log・logs/*.log のどこにも残っていない。ログの中では `<API_KEY>` に置き換わっている。
- 実験のコマンドの環境には鍵がある(ログには `<API_KEY>` と出る)。艦隊の起動・stop・ログを集めるコマンドの環境には無い(`None`)。
- `api_key` のファイルはラン後に消えている(`api_key_removed: 消した(艦隊を落とした後)`)。
- 要約と記録 6 本に、`C:\`・`C:/` の絶対パスとユーザー名は出ない。
- 残る場所は README「API key の扱い」が挙げた 4 か所。①ラン中のログ ②WSL の中の `VLLM_LOG` ③プロセスの一覧 ④ラン中の鍵のファイル。どれも記述どおりで、検収役は実機の WSL では確かめていない(L5 を見る)。

## 4. 欠陥

### 高

**H1. VRAM の検査が「前の艦隊を落とす」段より先にある。前の夜の艦隊が残っていると、その夜は rc 5 で止まり、残った艦隊も落とさない。**
段の順は `設定を読む → 安全の規則の検査 → 空き VRAM の確認 → 前の艦隊を落とす → 艦隊を立てる` になっている(対照の night_run.json で確認)。前の夜の `--keep-fleet`、後始末の失敗(rc 4)、手で立てた艦隊のどれかが 8B の重みと KV を持ったまま(約 9〜10 GB)だと、空きが「重み + 2 GB」を下回って rc 5 になる。prestop は回らず、`fleet_started=False` なので後始末の stop も回らない。prestop を置いた理由(前の夜の残りの掃除)が、一番必要な場面で効かない。
再現: `controls.py` の `vram_low`(空き 6,227 MiB)の段の並びを見る。prestop の段が無い。
直し方の案: prestop を VRAM の確認の前に動かす(prestop は「艦隊を立てる」ではないので、安全の規則の検査の後ならよい)。または prestop の後に測り直す。

**H2. 作業木に src の差分がある(発注の「src/ に変更が無いこと」に当たる)。取り込まなければ、完了の条件 4 の試走は実験の段で LLM の呼が通らない。**
`src/shibuya/llm/fleet.py` に、環境変数 `SHIBUYA_FLEET_API_KEY` から `Authorization: Bearer` を付ける 16 行が入っている(試験 `tests/llm/test_fleet_auth.py` 4 本)。README の冒頭は「ユーザーの判断待ち」と明記している。実装役の自己申告「src の fleet.py は Authorization を送らない(src は止めている)」は、検収を始めたときには正しかった。いまの作業木では事実と違う。規則 1 の「API key を付ける」を守れば、受け口が無い限り `shibuya.cli` の呼は全部 401 になる。この差分を取り込むか、試走だけ鍵なしにする切替を作るか、どちらにするかの決定が要る。

### 中

**M1. 試走の「成功」は LLM の呼の成否を見ない。401 で全部の呼が落ちても「成功」と出るおそれがある(未確認)。**
fleet.py は 4xx を `_FatalHTTP` から `fatal` に分類し、結果は `Outcome.ERROR_OTHER`(繰り延べと同じ扱い)。この場合 `shibuya.cli` が 0 で終わる可能性がある。night_run の成否は終了コードだけで決まる。README の冒頭は「試走も実験の段で失敗する見込み」と書くが、検収役は cli を回していないので(書いてよいファイルの制限のため)確かめていない。試走で見る「動いたか」には、テープの応答数 > 0(`llm.answered`)か、書式エラー率 < 1 を成否の条件に足すことを勧める。

**M2. 安全の規則の検査に抜け道がある(引数の文字列を正規表現で読むため)。** 次の形は検査に合格する。どれも vLLM(argparse)では最後の値が勝つ。
- `--host 127.0.0.1 … --host '0.0.0.0'`: 引用符つきの値は `_flag_values` が拾わない。
- `--host 127.0.0.1 … --hos 0.0.0.0`: argparse の略記(vLLM の構文解析が略記を禁じているかは未確認)。
- `--load-format safetensors … --load-format 'pt'`、`--api-key <鍵> … --api-key ''`: 上と同じ理由。
- `VLLM_API_KEY=<鍵>` は文字列のどこにあっても合格する(`echo VLLM_API_KEY=<鍵>;` でもよい)。
- `--config x.yaml` の中の `trust-remote-code` や host は見えない。
再現: `controls.py` の probe 群(`quoted_second_host` ほか。不合格の検査が `[]` と出る)。
直し方の案: bash に渡す文字列を `shlex.split` で切ってから旗を読む。値の引用符を外す。`--host`・`--load-format`・`--api-key` はちょうど 1 回だけを合格にする。旗の接頭辞に当たる語(`--ho`・`--hos`・`--load` など)は拒む。`--config` は拒む。設定を書くのはリポの中の人だけなので、悪意より書き間違いへの備えになる。

**M3. 規則 4 の検査は禁止の名の一覧(黒の一覧)なので、`HF_TOKEN`・`GITHUB_TOKEN` などの鍵は WSLENV に入っていても合格する。**
指示書は「ODPT の鍵**など**」と書いている。いまの一覧は `ODPT_API_KEY`・`ODPT_CHALLENGE_API_KEY`・`API_KEY`・`SHIBUYA_FLEET_API_KEY` の 4 つだけ。再現: `probe wslenv HF_TOKEN: []`。
直し方の案: 艦隊のコマンドに渡す環境から `WSLENV` を外す(何も継承させない)。または許す名の一覧(白の一覧)にする。

### 低

**L1. `VLLM_ARGS` を JSON の配列で書き、argv の 1 要素を `{{VLLM_ARGS}}` にすると、VRAM の調整の後に 1 本の文字列へ潰れる。**
`_args_str` と `set_flag` で文字列に戻すため、`['vllm','serve','--host 127.0.0.1 --max-num-seqs 16']` になる(調整の前は要素に分かれていた)。README は `background: true` のとき「vllm serve を前景で回すコマンドに書き換える」と勧めているので、この形を書く人が出やすい。出荷の設定(bash -lc の文字列の中)では起きない。

**L2. 設定に穴が残っていると、dry-run でも安全の規則の検査が「未判定」になる。** 出荷の設定ではいつもそうなるので、dry-run で検査の形を前もって確かめられない。穴に依らない検査(endpoints・WSLENV・.wslconfig)だけでも先に判定して表に出すとよい。

**L3. 禁止の文字列の試験(`rule5.no_firewall_calls`)が `.py` の 2 本しか見ない。** 実際に回るコマンドは `experiments.json` の argv(`wsl.exe … bash -lc …`)にある。`experiments.json` も検索の対象に足すとよい。

**L4. 終了コードの重なり。** argparse の使い方の誤りも 2 で終わるので、「実験の名が無い」の 2 と区別できない。3 は「設定の穴」と「fleet.vram の数が読めない」を兼ねる。5 は「安全の規則」と「VRAM 不足」を兼ねる(違いは要約を読めば分かる)。朝の判断に響くのは 5 の兼用だけで、記録で分かるので低とした。

**L5. `VLLM_ENV` の形でも、鍵は Windows の `wsl.exe` の引数(`bash -lc "tmux … \"VLLM_API_KEY=<鍵> vllm serve …\""`)に出る。** README の「引数の並びに鍵が出ない」は vLLM のプロセスについてだけ正しい。同じ人の別のプロセスからは読める。手元の 1 人用の機械なので低。README の文を「vLLM のプロセスの引数には出ない(wsl.exe の起動の引数には出る)」に直すとよい。vLLM が `VLLM_API_KEY` を読むことを README は「未確認」と書いている(正直な表記なのでそのままでよい)。

**L6. `_remove_api_key_file` が `finally` の鎖の中で try に包まれていない。** 中で捕まえるのは OSError だけなので、ほかの例外が出ると `_finish` が回らず、要約と NIGHT_DONE が書かれない。起こる見込みはごく低い。`_finish` の前の呼びは全部 try で包むと、「どの失敗でも要約と NIGHT_DONE を書く」性質が守れる。

**L7. 作業木から `register_task.py` を回すと、XML の `Set-Location` と `WorkingDirectory` が作業木の道筋になる。** `--print-only` の出力では `Set-Location 'C:\wt_n5070'` だった。本番の登録は、取り込んだ後に本体のリポから行う手順を runbook に 1 行足すとよい。

**L8. Windows の鍵のファイルは ACL を絞らない(自己申告のとおり)。** 置き場はユーザーのプロファイルの下なので、継承の権限は本人・SYSTEM・Administrators に限られる見込み。ラン後に消えることも確かめた。低。

### 確かめて問題が無かった所

- `_finish` は、rc 5 の 9 本・rc 1(健全性で落ちる)・rc 0 のどれでも、summary.md・metrics.json・metrics.md・night_run.json・NIGHT_DONE と `_night_runs.log` の 1 行を書いた。
- `--smoke` は置き場の名に `_smoke` を足し(`_r2` の規則も効く)、ランの名は `night5070-E1-smoke-<日時>`。本番の E1 の記録を上書きしない。
- VRAM の式の端: 使用が総量を超えたら空き 0 として rc 5 になる。総量 0・`[N/A]`・空の出力はどれも None として「未計測」になり、設定の値のまま進む。GPU が 2 枚なら 1 枚目を使う。境界(重み 5.7 GB + 2 GB = 7,884.8 MiB)では 7,900 MiB が合格・7,880 MiB が不合格で、式どおり。`seqs_setting` が段の一覧より大きい(64)ときは、64 も段に加える。
- `check_principal_xml` は SYSTEM・機械のアカウント・GroupId を拒む(試験とコマンドの両方で確認)。

## 5. 自己申告との差

| 自己申告 | 検収の結果 |
|---|---|
| 試験 106 本 | 検収を始めたときは 106 本。いまは 114 本(+ fleet_auth の 4 本)。作業木が検収中に変わった |
| 鍵の置換はランの最後にまとめて行う | いまはコマンドごとの直後と最後の 2 回(README にも記載)。ラン中の背後のログと WSL の `VLLM_LOG` に鍵が残る点は変わらない |
| API key のファイルの ACL を絞っていない | そのとおり。いまはラン後に消す(L8) |
| MODEL_GB と VRAM_PLAN_GB は穴のまま | そのとおり |
| src の fleet.py は Authorization を送らない | いまの作業木では送る差分がある(H2)。README は判断待ちと明記 |
| `VLLM_ARGS` に `--api-key` が必須 | いまは `VLLM_ENV` の `VLLM_API_KEY=` でもよい(推奨)。検査は「どちらかがあれば合格」 |
| 安全の規則の検査 7 つ・rc 5 | 7 つとも負の対照で rc 5 を確認。ただし M2・M3 の抜け道がある |
| 申告に無かったもの | H1(prestop と VRAM の順)・M1(試走の成否)・L1〜L7 |

## 6. 親への問い

1. H2: `src/shibuya/llm/fleet.py` の受け口の差分は、11-01p の src の解除の範囲の外。ユーザーに判断を求めるか。取り込まない場合、試走(完了の条件 4)を鍵なしで回す例外を作るか(規則 1 に当たるので、ユーザーの承認が要る)。
2. 検収中に作業木を書き換えたのは誰か(親か、実装役の続きか)。21:20 には書きかけで NameError が出る瞬間があった。並行で直すなら、検収はその書き換えが終わってから発注してほしい。
3. M1: 試走の成否に「テープの応答数 > 0」を足すことを、2-7 の直しの前の範囲として認めるか(呼数そのものは参考値のまま。見るのは 0 か 0 でないかだけ)。
4. H1 の直し(prestop を VRAM の確認の前へ)は、§2-6 の「進めてよい(事後報告)」に当たると検収役は読む。それでよいか。

---

## §再検収(第340・2 回目)

- 2026-11-01 21:49〜。前と同じ規律で行った(読むだけ・書いたのは本書の追記だけ・艦隊の起動/schtasks /create/taskkill はしていない)。今回は作業木が動かなかった。
- 対象の sha256(先頭 16): night_run.py `f43264726faf5340`・register_task.py `9b42b1230708f86a`・experiments.json `504d521410893538`・README.md `1a3aab9db9c838ed`・test_night5070.py `30b057b691fe803b`・runbook `a167f43fef62db47`・src/shibuya/llm/fleet.py `d618b9f2d96ebe96`(前回から不変=親の申告どおり)・tests/llm/test_fleet_auth.py `0f479acea95d36ac`。

### 試験

- `tests/tools/test_night5070.py`: **158 passed**
- `tests/llm`(test_fleet_auth.py を含む): **348 passed**
- 計 506 passed で親の申告と合う。親の文の「162」は、158 に test_fleet_auth.py の 4 本を足した数と読む。

### 前回の指摘ごとの結果

| 番号 | 結果 | 確かめたこと |
|---|---|---|
| H1 | **一部だけ直った** | 段の順は `設定 → 前の艦隊を落とす → 安全の規則 → VRAM → 立てる` になった(対照の night_run.json で確認)。ただし、落とした直後に待たずに測る(新しい N1 を見る) |
| H2 | 直っていない(ユーザーの判断待ちのまま) | fleet.py は前回と同じ sha256。README の冒頭の注も残っている |
| M1 | 直った | `require_answers: true`(E1)。偽のテープで確かめた: tokens_out=5 の行が 2 本なら rc 0・「応答あり」。tokens_out=0 なら rc 1・「応答 0(401 の疑い)」。テープが無ければ「応答数 未計測」で rc 1 |
| M2 | 直った(前回の 4 つ) | 前回の抜け道 4 つは今は不合格になる: `--host '0.0.0.0'` → vllm_host・`--hos 0.0.0.0` → vllm_host・`--load-format 'pt'` → safetensors・`--api-key ''` → api_key。`--config` → no_config_file。シェルの展開による残りは N2 |
| M3 | 直った | 艦隊のコマンド(prestop・start・collect_log・stop)の環境から `WSLENV` を外した(`fleet_env`)。名の検査は `*_KEY`・`*_TOKEN`・`*_SECRET` の形で、`HF_TOKEN:GITHUB_TOKEN` は不合格。`DB_PASSWORD`・`ODPTAPIKEY`・`CREDENTIALS` は名の検査を通るが、WSLENV そのものを渡さないので継承は起きない(L-b) |
| L1 | 直った | 配列の `VLLM_ARGS` は調整の後も配列のまま(`['vllm','serve','--host','127.0.0.1','--max-num-seqs','16',…]`)。`--max-num-seqs=8` の形も置き換わる |
| L2 | 直った | 出荷の設定の `--dry-run --smoke`: endpoints・wsl_nat・wslenv は判定され、起動のコマンドが要る 5 件は「未判定」と並ぶ |
| L3 | 直った | `test_no_firewall_calls_in_experiment_commands` が experiments.json の argv(start・stop・collect_log と全部の実験)を検索する |
| L4 | 直った | 5=安全の規則・6=VRAM 不足に分けた。2=引数と設定の誤り(argparse の誤りも 2。定義に含めた)・3=穴と数の読めない |
| L5 | 直った | README は「vLLM のプロセスの引数には出ない。wsl.exe の起動の引数=bash -lc の文字列には出る」と正しく書いている |
| L6 | 直った | `_remove_api_key_file` を try で包んだ |
| L7 | 直った | `worktree_reason` が `wt_` と `.git` がファイルの場合を見分け、作業木からの登録は rc 2。`--print-only` は出力したうえで注を stderr に書く(作業木で確認) |
| L8 | 直った | Windows では `icacls <鍵のファイル> /inheritance:r /grant:r <USERNAME>:F`。対照のランで `icacls で本人だけ(継承を外した)` と記録された。対象は鍵のファイルだけ |

### 自分の負の対照(2 回目)

`<SCRATCH>/rev/controls2.py`。前回と同じ形で、艦隊の起動の段は差し替えてあり、prestop・stop・実験は印を書くだけの python。

| 対照 | 結果 | 回ったコマンド |
|---|---|---|
| endpoints の `0.0.0.0`・`localhost` | rc 5・endpoints_loopback | prestop だけ |
| `--host` 無し・`--host 0.0.0.0` | rc 5・vllm_host | prestop だけ |
| 鍵無し | rc 5・api_key | prestop だけ |
| `--trust-remote-code` | rc 5・no_trust_remote_code | prestop だけ |
| `--load-format` 無し | rc 5・safetensors | prestop だけ |
| `WSLENV=FOO/u:ODPT_API_KEY/u` | rc 5・wslenv | prestop だけ |
| VRAM の空き 6,227 MiB | **rc 6**・失敗した段=空き VRAM | prestop だけ |
| 空き 10,727 MiB・健全性で落ちる | rc 1 | prestop・start(差し替え)・log・stop |

10 本とも、艦隊を立てる段は回っていない。鍵のファイルは残っておらず、NIGHT_DONE と summary はある。prestop が安全の規則の検査より先に回るのは、新しい段の順のとおり(L-c)。

M2 の追加の探り(`safety_checks` を出荷の start の argv の形で直接呼んだ):

| 形 | 結果 |
|---|---|
| 正しい引数の形・正しい `VLLM_ENV` の形 | 合格(偽の不合格は無い) |
| `; echo VLLM_API_KEY=<鍵>`(引数の鍵なし) | 不合格(api_key) |
| `; vllm serve m --host 0.0.0.0` | 不合格(vllm_host・safetensors) |
| `$'--host' 0.0.0.0`(bash の ANSI-C の引用) | **合格**(N2) |
| `$EXTRA`・`$(cat …)`・`` `cat …` `` を末尾に | **合格**(N2) |
| `VLLM_ENV="VLLM_API_KEY=<鍵> VLLM_API_KEY="` | **合格**(N3) |
| `--host '127.0.0.1'`(引用符つきの正しい値) | 合格(前回は偽の不合格だった。改善) |
| `.wslconfig` の `networkingMode=bridged` | 合格(L-a) |

### 鍵の漏れの再確認(偽の vLLM で `--smoke`)

`<SCRATCH>/rev/leak2.py`。前回の leak.py と同じ形で、実験のコマンドが偽のテープ(`calls.parquet`)を書くように替えた。

- 偽の vLLM が受けた Authorization は全部 `Bearer <正しい鍵>`。
- tokens_out=5 のランは rc 0、tokens_out=0 のランは rc 1。どちらも、ラン後に out と data の全ファイルを鍵の値で検索して **0 件**。ログの中では `<API_KEY>` に置き換わっている。
- 鍵は実験のコマンドの環境にだけ入り(`SHIBUYA_FLEET_API_KEY`)、prestop・start・collect_log・stop の環境には入らない。
- 鍵のファイルはラン後に消えている。記録 6 本に絶対パスとユーザー名は出ない。
- `register_task.py --print-only`: `<UserId>&lt;USER&gt;`・InteractiveToken・LeastPrivilege・WakeToRun true。ユーザー名は 0 件。`USERNAME=SYSTEM` は rc 2。

### 新たな欠陥

**中**

**N1. 前の艦隊を落とした直後に、待たずに VRAM を測る。** H1 の直しの残り。既定の stop は `tmux kill-session` で、すぐ返る。vLLM のプロセス(エンジンの子のプロセスを含む)が終わって GPU のメモリを返すまでには時間がかかるため、直後の `nvidia-smi` はまだ使用中の量を読むおそれがある。そうなると、前の夜の艦隊が残っていた夜、つまり H1 が守ろうとした場面で、また rc 6 になる。`grep` で確かめたところ、prestop と VRAM の確認の間に待ちも測り直しも無い。実機では確かめていない(艦隊の起動は禁止のため)。
直し方の案: prestop が「落とした」(rc 0)ときは、空きが増えなくなるまで数秒ごとに測り直す(例: 最大 60 秒)。または、VRAM が足りないときに 1 回だけ待って測り直してから rc 6 にする。

**低**

**N2. シェルの展開は検査で見えない。** `$'--host' 0.0.0.0`、`$VAR`、`$(…)`、`` `…` `` を start の文字列に書くと、shlex は bash と違う語に切るので合格する。設定を書くのはリポの中の人だけなので、書き間違いで起きる形ではない。直し方の案: vllm の部分の語に `$`・`` ` ``・`{` を含むものがあれば不合格にする。

**N3. `VLLM_ENV` の先頭の語だけを見るので、後ろの `VLLM_API_KEY=`(空の値)で上書きできる。** 直し方の案: `VLLM_ENV` の中の `VLLM_API_KEY=` は、ちょうど 1 回だけを合格にする。

**L-a. `.wslconfig` は `mirrored` だけを拒む。** `bridged` などは通る。vLLM は WSL の中の 127.0.0.1 に束縛するので、実害は小さい。指示書の文(「既定の NAT」)に合わせるなら、`nat` か未記入だけを合格にする。

**L-b. 名の検査は `*_KEY/TOKEN/SECRET` の形なので、`PASSWORD`・`APIKEY`(下線なし)・`CREDENTIALS` は通る。** 艦隊の環境から WSLENV を外したので実害は無い。検査は表示の役だけになる。

**L-c. prestop(`wsl.exe … tmux kill-session`)が安全の規則の検査より先に回る。** 艦隊を立てるわけではないので、規則 6 の文には反しない。ただし WSL の VM はここで起動する(mirrored の `.wslconfig` でも起動してから検査で止まる)。問題にするほどではないが、要約の段の表で順が分かるようにしてあることは確認した。

**L-d. 安全の規則の検査は、VRAM の調整で書き換える前の argv に対して行う。** 書き換えるのは `--gpu-memory-utilization` と `--max-num-seqs` の 2 つだけなので、実害は無い。書き換えた後の argv にもう一度検査をかけると確実になる。

**L-e. 後始末に失敗した(rc 4 になるはずの)ランでも、応答 0 なら rc 1 になる。** 要約の先頭の「艦隊が落ちていない」の行は残るので、朝に気づける。

**L-f. テープに `tokens_out` の列が無いときは、`answered`(繰り延べでない行)で数える。** 4xx の行が繰り延べでないとして記録されると、0 にならない。いまのテープには列があるので、念のための注。

### 判定(2 回目)

**条件つき受入。** 前回の高 1・中 3・低 8 のうち、H1 の半分と H2 を除く全部が直った。M2 の抜け道 4 つ・H1 の段の順・M3 の WSLENV を自分の対照で確かめ、鍵の漏れは 0 件。残る条件は 2 つ。
1. **N1(中)**: prestop の後に VRAM の解放を待つか測り直す。E1 の本番の前に直すことを勧める。
2. **H2**: `src/shibuya/llm/fleet.py` の差分をユーザーが取り込むかの判断。取り込まなければ、`require_answers` により試走は「応答 0」で rc 1 になる(黙って成功にはならない)。

N2・N3・L-a〜L-f は低で、取り込みを止める理由にはならない。
