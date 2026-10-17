# 封印の分離の残りと ODPT の取得のログの圧縮 — 検収の記録

- 検収役 Opus 5.5(実装は見ていない)。作業木の枝 `tidy/seal-split-and-logs`(土台 `32fb262`=本体 HEAD と同じ・commit の無い変更)。
- **封印の層と検証側の錨の値は読んでいない**。見たのは、ファイルの名・大きさ・行の数・JSON の鍵の名・錨の欄の名(schema)・md5 と真偽だけ。diversity の分離の確かめでは、出典の欄から表の番号(第 N 表)と著者名だけを正規表現で抜いた(実装役と同じ範囲)。
- **申告(検収役の手順の事故)**: T0 の検査で `git diff`(消した `diversity_anchors_v0.json` の行を含む)を `grep -i tick` に通したとき、`yardstick` に当たった元のファイルの `purpose` と `note` の文 4 行が画面に出た。出た文は 15 分ビンのラベルの説明と物差しの欄の名だけで、錨の値(value・values・low・high)は含んでいない。
- 道具は本体の `.venv` の python・`PYTHONIOENCODING=utf-8`・`PYTHONPATH` に作業木の `src`。作業用の置き場は `_bc_review`(つなぎを .NET で外してから消した)。

## 判定: **受入**(条件 0・直すとよい点は低 6)

既定の結果は動いていない(自分の 4 構成も 25 欄が全部同じ)。分けた 2 本を合わせると元と一致する(錨 17/17・見出しの鍵も一致)。守りの語の追加は負の対照で効いている(HEAD の守りでは開いてしまう道筋が、作業木の守りでは開く前に落ちる)。`tests/c7` は監査フックの下で 168 passed で、封印と検証側の本物のファイルを 1 つも開かない。ログの回しは、本物のログの写しでもバイト単位で元に戻り、別のプロセスの書き手や PowerShell の `*>>` と並べても行が欠けず重ならない。実際の置き場の既存分の圧縮が未実施なのは、本体の古い読み手が gz を読めないためで、取り込みの前に回さないという判断は正しい(親が取り込みの後に回す)。

## 1. 結果不変 ✓

| 何を | 実装役 | 検収役(自分で回した) |
|---|---|---|
| byte-check の構成 | 19/19・25 欄とも同じ(`byte_check_seal.json` の 19 行を全部読んだ=moved は全部空・差分の欄は全部 0)。side の JSON(`_bc/head.json`・`seal.json`)も読んだ: head は `src_is_worktree=False`・seal は `True`・`tree_missing` 空・`env`/`kw` 空=腕の既定は今の道 | 4 構成(w6_v3_default・w6_v3_activity_off・w6_v1_default・v3_mem_rel)を本体 HEAD `32fb262` の写し(`git archive` で src・錨 3 本・設計の表 5 本・w6-regen+data へのつなぎ=.NET で外した)と作業木で回して compare=**4/4・25 欄とも同じ**・`tree_missing` 空 |
| final(w6_v3_default) | `b8eadcb51e8705e7`・calls 64,528 | `b8eadcb51e8705e7`・64,528 |
| final(w6_v3_activity_off) | `c88ba9104f45f897` | `c88ba9104f45f897`・50,006 |
| final(w6_v1_default) | `e1288e092ddaca86` | `e1288e092ddaca86`・51,655 |
| final(v3_mem_rel) | `768b2262e3b0999e`・67,794 | `768b2262e3b0999e`・67,794 |
| 2 日の通し | v3_mem_rel `31c9b19409e18b2f`/145,675・w6_v3_default `b346bb6e3ecc60af`/138,946・19 欄とテープの列が同じ | 回していない(JSON を読んだ。src の差は build の 2 行だけ=実行時に import されない・lint-imports で確認) |
| 再開=通し | final 同じ・境目の後の checkpoint 4 点が同じ | 同上 |

土台は本体 HEAD と同じ(`32fb262`)=rebase の見込みの差は無い(並行の作業木が `w21_sources.py`・`read_guard.py` を触れば語の行で当たりうる=§9 の一覧どおり)。

## 2. 口と約束 ✓(本段は整理=新しい口は道具だけ)

- 読み口: `diversity_yardstick.load_anchors(path | paths | None)`・`merge_anchor_docs`(同じ錨の名は止める)・`DEFAULT_ANCHORS_PATHS`(構築側+検証側)。`logrotate.read_bytes_all`/`read_text_all`/`maybe_rotate`/`rotate_one`・`ledger.read_all` は gz を通す・`ledger._append_text` は書く口 1 つ。記録 §3・§5-1 の記述と一致。
- 受入の試験と試験の対応: byte-check(JSON)・負の対照(`test_gauge_guard_denies_the_validation_side`・`test_make_guard_rejects_sealed_and_renamed_inputs`・`test_old_odpt_rt_dir_is_sealed_for_both_guards`)・md5(`test_build_side_copy_equals_the_original_anchors`)・監査フック(`test_yardstick_fixture_opens_no_validation_file_and_the_hook_works`)・gz の行数(`test_rotate_ledger_by_jst_day_is_byte_exact` ほか)・錠(`test_lock_excludes_a_second_rotator_and_stale_lock_is_cleared`)・書き手が落ちない(`test_writer_keeps_appending_during_rotations`)。
- 無いもの: **`tests/c7` が較正側だけを開くことを固定する試験**(記録の測りだけ=L1)。
- 〔決定〕の反映: 仮-13(〔灰〕は検証側)=Schneider 2013 の 5 本を検証側へ ✓・§10-3(Song・Alessandretti は検証に使わない)=構築側へ ✓・10-13b §5 追記(保存するときに gzip)✓・§0-6(整理=不変)✓。

## 3. 発注文の各項

| 項 | 判定 | 根拠 |
|---|---|---|
| 1 混在の棚卸し | △ | 表は錨 7 本・世界資産の列・PT・r99・hunger を網羅。抜け=`data/research_cache/r107/`(家計調査 `kakei*`=§10-1 の検証専用と、W21 が読む賃金 `chinkou_*`・全国家計構造調査 `zk2024_*` が同じディレクトリ=ファイルで分かれている・W21 #47 の語で縛られている)・`data/realworld/pt_tokyo/`(d-1=〔写〕・混在なし)・`data/research_cache/estat_r3_avgtime_000032224420.xlsx`(第 30 表=語で縛られている)・`data/research_cache/r89/`。どれも混在の形ではない(L2) |
| 2 分離の残り | ✓ | `diversity_anchors_v0.json` → 構築側 6+`p0_prior`/検証側 11。自分で再計算=§6 |
| 3 他の層の確認 | ✓ | 名前・大きさ・数・鍵の名だけ(§8 (c))。`odpt_rt` の未圧縮 `.json` は今 4,988 本(`_last_fetch.json` を含む=実装役の 4,987 と合う)・`.json.gz` は 5,682 本(増えている) |
| 4 ログの圧縮 | △ | 仕組み ✓・写しで ✓。実際の置き場の既存分は未実施(申告どおり。本体の古い読み手が gz を読まない=取り込みの前に回すと日次の報告が過去の行を失う=回さない判断は正しい) |
| 5 記録と台帳 | ✓ | つなぎの台帳に混在の宣言の行が無いことを確かめた(実装役の申告と同じ) |

「できなかったこと」の申告(既存分の圧縮・エンジンが空腹の検証側を読む・決定が要る 4 点)は実態と合う(§8 (e))。

## 4. 守り ✓

- 書く口: ログの回しは `_logs/` の下だけに書き、生きているファイルは `os.replace` の改名だけ。台帳の追記は `ledger._append_text` の 1 本。
- 実行時の表: 守りの語は tuple(`SEALED_TOKENS`・`GAUGE_EXTRA_DENY_TOKENS`・`VERIFY_SIDE`)。`anchor_split.PLANS` と `Plan.why`、`logrotate._SPEC` は素の dict(道具なので低・L5)。
- **負の対照(自分で植えた)**: 守りの下で `open` を試み、開けたら直ちに閉じる(読まない)。

| 守り | 道筋 | HEAD `32fb262` | 作業木 |
|---|---|---|---|
| 計器(`GAUGE_DENY_TOKENS`) | `docs/bench/anchors/diversity_validation_anchors_v0.json` | 開いた | **SealedPathError** |
| W21(`W21Guard.for_build`) | 同上 | 開いた | **VerificationSideError** |
| 封印だけ(`sealed_only`・エンジンのランを包む) | 同上 | 開いた | 開いた(設計どおり=エンジンの守りは封印の層だけ) |
| 計器 | `data/realworld/odpt_rt/README.md` | 開いた | **SealedPathError** |
| 封印だけ | 同上 | 開いた | **SealedPathError** |
| W21 | 同上 | NotAllowedError(一覧の外) | **VerificationSideError** |
| 計器 | `diversity_build_anchors_v0.json` | — | 落とさない(`deny_hit` None) |

## 5. 宣言と凍結 ✓

`engine/` と状態台帳・凍結の表・`src/shibuya/cli.py`・つなぎの台帳は差分に無い(`git diff --stat`)。src の差は `build/pop/w21_sources.py` の語 2 つだけ(W21 の manifest は行の id だけを書く=`verify_side_rows`・ソースの sha は取っていない)。manifest の欄は byte-check の `frozen_sources` を含む 25 欄が同じ。

## 6. 同値(独立の再計算)

| 量 | 実装役 | 検収役 | 方法 |
|---|---|---|---|
| 錨ごとの md5 | 17/17 | **17/17** | `git show 32fb262:` の元と、作業木の 2 本を自分のスクリプトで読み、錨ごとに `json.dumps(sort_keys=True)` の md5 を比べた(真偽と数だけ出した) |
| 鍵の和=元 | true | **true**・重なり 0・構築 6/検証 11 | 同上 |
| 見出しの鍵 | — | `created`・`schema`・`version` は両方で元と同じ・`p0_prior` は構築側で元と同じ・`purpose`・`rules` は検証側で元と同じ(構築側の `purpose` は道具が書いた新しい文) | 同上 |
| 区分の根拠 | 第 30 表 6・Schneider 5/第 31 表 1・Song 3・Alessandretti 2 | **同じ**(出典の欄の表番号と著者名だけを抜いた) | 正規表現 `第\s*(\d+)\s*表` と著者名の一覧 |
| 台帳の回し(写し) | 13,914,161 B・32,685 行 → 415,317 B・71 塊 | **14,330,552 B・33,453 行 → 429,300 B・71 塊(2026-08-07〜10-17)**・ほどくと元とバイト列も md5 も同じ・`read_all` 33,453 行(壊れた行 0)・回した後の追記 3 行が後ろにつながる・2 回目の回しで行が同じ・3 回目は empty | 本物の 3 本を作業用の置き場へ写して `maybe_rotate(force=True)`(実装役の測りの後に台帳が伸びた分だけ大きい) |
| `_scheduler_odpt.log` | 9,485,768 B・84,031 行 → 108,669 B | **9,497,800 B・84,219 行 → 108,828 B・1 塊**・バイト列が同じ | 同上 |
| `_scheduler.log` | 102,020 B・901 行 → 3,909 B | **102,020 B・901 行 → 3,909 B**・同じ | 同上 |
| 書き手が追記し続ける間の回し | 400 行・開き直しの負の対照あり | **別のプロセスの `ledger.append` 1,500 行 × 3 試行**・回し 40〜49 回・busy 10〜22 回・書き手の失敗 0・読めた行=0..1499 の順で欠けも重なりも無し・rotating の残り 0 | 作業用の置き場 |
| PowerShell 5.1 の `*>>` が開いている間 | (Python の手の内で確かめた) | **回しは 14 回とも busy(改名が共有違反で失敗)**・書き終えた後に rotated・40 行が全部読める。2 回目の `*>>` は新しいファイルを BOM `fffe` から作り、つないだ読みで 45 行 | タスクと同じ `powershell.exe -Command "& python … *>> log"` |

## 7. 試験

| 何を | 結果 |
|---|---|
| 指定の範囲(`tests/engine tests/tools tests/economy/cp2 tests/c8 tests/engine/bridging`・状態台帳・10f の 3 本)+`tests/w17`+`tests/build_pop/test_w21_sources.py`(`-n 2 --dist loadfile -m "not slow"`) | **3,081 passed・1 skipped・failed 0・errors 0**(26 分 14 秒)。1 回目(`-n 2`)は機械が混んでいて 50 分の上限で 96% のところで切れた(落ちた 2 件は切ったときの node down=試験の落ちではない)ので、`-n 4` で回し直した(junit で failures 0・errors 0 を確かめた) |
| `tests/build_pop tests/build_audit`(`-m "not slow"`) | 168 passed |
| `tests/c7` 単独(監査フック=子プロセスにも載る `sitecustomize` で `open` を数えた) | **168 passed**(2.7 秒)。封印・検証側・〔灰〕の語に当たった `open` は、合成の置き場の `…/kddi_la/la.json` 4 回と道具のモジュール `holdout_compare.py` の読み込みだけ。錨は較正側 `presence_calib_anchors_v0.json` 1 回だけ |
| `tests/w17`+`test_seal_split_337.py`+古い commit の写しの試験 2 本(同じフック) | 48 passed。検証側の名に当たったのは、番人の差し替え先(無いファイル)1 回と負の対照の植えたファイル(作業用の置き場)だけ。構築側 `diversity_build_anchors_v0.json` は 5 回。古い commit の写しの 2 本は `hunger_energy_anchors_v0.json`(その版のエンジンが開く混在の 1 本)を作業用の置き場に書き出す=1 本ずつ(前は錨のディレクトリを丸ごと) |
| `lint-imports --no-cache`(作業木の src) | 5 kept・0 broken |
| `tools/scan_secrets.py`(変えた・足したファイル 19 本。検証側の錨の 1 本は除く) | CLEAN |
| 改行 | 変えた・足したファイルは全部 LF |

## 8. 抜け道と記録

- (a) 区分の表: §3 の項 1 のとおり(抜けは混在の形でない 4 か所=L2)。分けたファイルの値は元と一致(§6)。検証側のファイルは計器の守りと W21 の守りの一覧に載り、負の対照で落ちる(§4)。エンジンは diversity の錨を開かない(src の grep で読む所 0)。
- (b) `tests/c7`: fixture は較正側だけを開く(監査フックで 1 回)。単独で通る(168)。CI-1(`.github/workflows/ci.yml`)はもともと `tests/c7` を除いていない。**全体試験に戻してよい**(親が手元の引数から `--ignore=tests/c7` を外す)。
- (c) 他の層の確認: 記録 §6 の手順は名前・大きさ・本数・鍵の名・列の名。`boundary_counts.json` は `_meta.sources_present`(出典の名の一覧)まで読んでいる=封印のファイルの中のメタデータ(値ではないが「列の名だけ」より一歩深い=L6)。
- (d) ログの圧縮: §6 のとおり。元のログは `data/`(gitignore 下=`git check-ignore` で確認)。実際の置き場は未実施(`_logs/` も rotating も無いことを確かめた=途中の残りなし)。
- (e) 不変: §1。記録(README・JSON 3 本)に絶対パス・ホスト名・個人名は無い(grep)。§9 の触った共有ファイルの一覧は `git diff --stat` と合う(共有でない `tools/w17`・`tests/w17`・錨 3 本は §2・§3 にある)。
- 実装役の「決定が要る」4 点の前提(名前と schema だけで確かめた): (1) `presence_validation_anchors_v0.json` の錨の名は `attendance_rate`・`full_population`・`homebound_boarding_time_dist_2015`・`night_presence_estimate`・`pt_area_daytime_peak`・`wake_rate_tokyo_weekday` の 6 本=名の上では 2 本が構築の入力の写し(time_dist の 2015 年版・体数)=前提は事実。(2) R-115 §2 は ODPT 乗降人員を〔非〕、W21 の #17 は語 `passenger_survey` で検証側。W12 は `odpt_survey_value/measure/year` の列を書き、エンジンは `node_id`・`kind`・`lines` だけ(`world/assets.py`)・W21 は `WORLD_COLUMNS` で読まない=前提は事実。(3) `motif_threshold` は物差しの数え方の閾値(`diversity_yardstick.py` :986)=前提は事実。(4) `odpt_rt/` の未圧縮の `.json` は 4,988 本(うち 1 本は `_last_fetch.json`)=前提は事実。

## 欠陥(すべて低・受入を妨げない)

| # | 重さ | 場所 | 中身 | 直し方 |
|---|---|---|---|---|
| L1 | 低 | `tests/c7`(試験なし) | `tests/c7` が較正側だけを開くことは記録の測りだけで、試験で固定していない。戻した後に誰かが fixture を混在の名へ戻しても落ちない | `tests/c7/conftest.py` にセッションの監査フック(検証側の語を開いたら落とす)を 1 本。または CI-1 の時に `read_guard.deny_hit` を `open` に掛ける |
| L2 | 低 | README §1 の表 | 抜け: `data/research_cache/r107/`(家計調査〔検〕と賃金・全国家計構造調査の構築側が同じディレクトリ=ファイルで分かれている)・`data/realworld/pt_tokyo/`(〔写〕)・第 30 表の原表 `estat_r3_avgtime_000032224420.xlsx`・`data/research_cache/r89/`。§10-1 の研究の値(R-89・CT・住宅・土地統計)はファイルが無い(W21 の語で縛る)ことを 1 行書くとよい | 表に 4 行と注 1 行 |
| L3 | 低 | `logrotate.iter_chunks`(:130-143) | 読み手は錠を取らない。読みの途中で別のプロセスが回すと、`live.exists()` の後の改名で `FileNotFoundError`、または一覧の後に回った塊を読み落とす。台帳を回すのは日が変わった最初の回だけで、読むのは 12:00 と 0:30 の日次の報告=重なる窓はごく小さい | 読み口で `FileNotFoundError` のときに一覧を取り直して 1 回やり直す(または読み手も錠を共有で取る) |
| L4 | 低 | `logrotate._lock`(:172-186) | 古い錠の掃除が「見て消して作る」の 3 手=2 つの回しが同時に古い錠を見ると、後の側が先の側の新しい錠を消して両方が入れる(600 秒より古い錠が残っている時だけ) | 古い錠は `os.replace` で別名に移してから作り直す(移せた側だけが進む) |
| L5 | 低 | `anchor_split.PLANS`・`Plan.why`・`logrotate._SPEC` | 素の dict(1-3 の教訓は `MappingProxyType`)。道具なので実害は小さい | `MappingProxyType` に包む |
| L6 | 低 | README §6 の `boundary_counts.json` の行 | 封印のファイルの `_meta.sources_present` の中身(出典の名)まで読んでいる。値ではないが、発注文の「名前と schema だけ」より深い | 次からは鍵の名と行・列の数までに留める(今回の記述は残してよい=親の判断) |
| L7 | 低 | `tests/tools/test_realworld_fetch_logrotate.py` :115・`tests/tools/test_seal_split_337.py` :115 | 新しい試験の関数名に「open」が入る(発注文の規律「open を新しい識別子に入れない」)。`yardstick` は既存の名 | 名を `…_handle_blocks_rename…`・`…_reads_no_validation_file…` に |

ほかに気づいた点(欠陥ではない):

- ログ(`_scheduler*.log`)は塊が 1 つで、名の日は改名したファイルの最後の書き込みの日。既存の 9 MB(10-03 からの分)は 1 本の gz(日は取り込みの日)になる。日ごとの gz は回し始めた翌日から。0:30 の回で回した ODPT のログは、中身の多くが前日なのに名は当日になる。
- `tests/w17` は検証側の作り物の値で回る(「既存の assert が通る形」)。本物の第 30 表との距離を見る試験は無くなった(封印の分離の代償=実装役の記録どおり)。
- `test_seal_split_337.py` の `_Recorder` は import の時に外せない監査フックを足す(`on` の時だけ数える)。
- `tests/tools/test_realworld_fetch_logrotate.py` :106 は `LR.os.replace`(=`os.replace` そのもの)を monkeypatch で差し替える。並列の他の試験とは別のプロセス(`--dist loadfile`)なので実害は無い。
- 作業木に未追跡の `_bc/`(実装役の byte-check の置き場)が残る。gitignore に当たらないので取り込みで載せない。

## 親に確かめてほしいこと

1. 取り込みの後に本体で `--rotate-logs` を回す(タスクの回の合間に。ODPT のログは自分のタスクが開いている間は busy で次の回へ回る=PowerShell の `*>>` で確かめた)。回した後に `--report` の未取得日が前と同じかを 1 回見る。
2. `tests/c7` を全体試験に戻すかどうか(戻すなら L1 の試験を同時に)。
3. 実装役の「決定が要る」4 点(前提はどれも事実)。
