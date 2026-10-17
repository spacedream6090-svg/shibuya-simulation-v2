# 封印の分離の残りと ODPT の取得のログの圧縮(整理=既定の結果は 1 バイトも変えない)の実装の記録

- 実装役 Opus 5.5。作業木の枝 `tidy/seal-split-and-logs`(土台 HEAD `32fb262` → 検収の直しの後に本体の最新 `13e9c90` へ早送り=§11)。commit は親。独立検収は [review.md](review.md)(受入・低 7)。
- 正: [回答 10-13b](../../../../design/v2-answers-2026-10-13b.md) §7 の 5(封印の分離の残り・ODPT のログの圧縮)・§0-6(整理の段=byte-check 19 構成で不変)・§5 追記(保存するときに圧縮)・PENDING 仮-13(〔灰〕は決まるまで検証側)・[R-115](../../../../research/v2-r115-calibration-anchors-inventory-for-2-0.md) §2・§5・[パターン台帳](../../../../design/v2-pattern-ledger.md) §10・2-4 V6([vb24](../vb24/README.md) §V6)。
- **封印の値・検証側の錨の値は 1 つも読んでいない・書いていない**。見たのはファイルの名・大きさ・行の数・JSON の鍵の名・出典の欄から抜いた表の番号(第 N 表・著者名=R-115 と同じ「source の欄だけ」・数字は伏せて読んだ)だけ。

## 0. 結論

1. **残っていた混在は 1 本だった**: `docs/bench/anchors/diversity_anchors_v0.json` に第 30 表〔検〕・Schneider 2013〔灰〕と、第 31 表〔写〕・Song 2010/Alessandretti 2018(§10-3=構築・初期化に使ったので検証に使わない)・設計書 §5 の前値 `p0_prior` が 1 本に混ざり、全体試験の `tests/w17` の fixture がこのファイルを開いていた(監査フックで 3 回)。**鍵の名で 2 本に分けた**(構築側 6 本+`p0_prior`/検証側 11 本・値は変えていない・合わせると元と鍵と値の全部で同じ・錨ごとの md5 17/17 同じ)。読む側(物差し `tools/w17/diversity_yardstick.py`・試験の fixture)を直し、`tests/w17` は構築側のファイル+検証側の作り物だけを開く。
2. `presence_anchors_v0.json`・`hunger_energy_anchors_v0.json` の分離は 2-4 V6 で済んでいた(本段は確かめただけ)。**エンジンが空腹の検証側のファイル(第 18-1 表と 15 分の食事率)を読む形は残る**=回答 10-13b §7 の 2(第 18-1 表の置き換え=§2 の 6 (a)・小さな版上げ)の仕事で、整理の段では直せない(読む先を変えると既定の結果が動く)。
3. **`tests/c7` は全体試験に戻せる**: 監査フックで数えると、`tests/c7`(168 本)が開いた封印・検証側の名のファイルは 0(当たったのは合成の置き場の `…/kddi_la/la.json` 4 回と道具のモジュール `holdout_compare.py` の読み込みだけ)。CI-1 はもともと `tests/c7` を含む。親の手元の全体試験の `--ignore=tests/c7` は外せる(親が引数を変える)。
4. 守りの語に 2 つ足した: `diversity_validation_anchors`(計器の段・W21 の #57)と `realworld/odpt_rt`(v1 の頃の ODPT リアルタイムの置き場=今の `realworld_live/odpt_rt` と同じ種類なのに、どの守りの語にも当たっていなかった=封印の層・W21 の #16)。
5. **ODPT のログの圧縮の仕組み**を取得の道具に入れた(`tools/realworld_fetch/logrotate.py`・日ごとに回して gzip・書き手を止めない・原子的な置き換え・台帳の読み手は gz を読む)。**実際の置き場の既存の分の圧縮は回していない**(下の §5-3=権限の判定で止まった/台帳は本体の取得の道具がまだ古い読み手=取り込みの後に回すのが安全)。台帳の写しで測ると 13,914,161 B・32,685 行 → gz 415,317 B(71 日の塊)・ほどくと元と 1 バイトも違わず・読み口の行数も同じ。
6. byte-check 19 構成=**19/19 で 25 欄とも HEAD と同じ**([byte_check_seal.json](byte_check_seal.json))。5,000 体・2 日の通しは 2 構成で比べた欄が全部同じ([two_days_head_vs_seal.json](two_days_head_vs_seal.json))・日の境目の再開=通し([resume_seal_5000.json](resume_seal_5000.json))。

## 1. 区分の表(ファイルまたは列の単位)

印は R-115 §2: 〔写〕入力の写し / 〔部〕一部だけ入力 / 〔非〕今の版の入力でない / 〔検〕検証側 / 〔灰〕区分が未決(仮-13=検証側と同じ扱い)。§10-3=構築・初期化に使ったので検証に使わない。

| ファイル(または列) | 中の区分 | 分かれているか | 読む側 |
|---|---|---|---|
| `docs/bench/anchors/commute_time_dist_r3.json` | 第 31/36 表〔写〕だけ | ファイルで分かれている | 構築 `build/sched/trial.py`・`w20_calendar_1a.py`・2-0 の計器 |
| `docs/bench/anchors/ssb2021_activity_prior_v0.json` | 第 8-1〜8-3 表〔部〕(食事 03 の行は入れていない=R-115 §2) | 分かれている | エンジン `engine/classical.py`・計器・判断モデルの評価 |
| `docs/bench/anchors/hunger_energy_build_anchors_v0.json` | DRI・NHNS 第 14/13 表・METs(構築側) | 分かれている(2-4 V6) | エンジン `engine/energy.py` |
| `docs/bench/anchors/hunger_energy_validation_anchors_v0.json` | 第 10 表・第 18-1 表・15 分の食事率(検証専用の宣言) | 分かれている(2-4 V6) | **エンジン `engine/energy.py` が読む**(既定の食事時刻=§7 の 2 で置き換える・本段では直さない) |
| `docs/bench/anchors/presence_calib_anchors_v0.json` | 中核 9 町丁目〔非〕だけ | 分かれている(2-4 V6) | `tools/c7/presence_yardstick.py`・図・`tests/c7` |
| `docs/bench/anchors/presence_validation_anchors_v0.json` | PT 由来〔灰〕2・第 4-1 表〔検〕1・time_dist_12 の写し 1(〔部〕と同じ元)・W16 の体数の写し 1(〔写〕)・研究の推定 1(expedient) | 検証側の 1 本に寄せてある(保守側=仮-13)。〔写〕〔部〕の元の 2 本を較正側へ移すかは**親の判断**(§6) | `tools/c7/presence_yardstick.py`(検証の物差し)・図 |
| **`docs/bench/anchors/diversity_anchors_v0.json`(本段で分けた)** | 第 30 表〔検〕6・Schneider〔灰〕5/第 31 表〔写〕1・Song 3・Alessandretti 2(§10-3)・`p0_prior` | **混在 → 2 本に分けた**(§2) | `tools/w17/diversity_yardstick.py`・`tests/w17` |
| `docs/bench/instruments/anchor_gauge/calib_anchors_v0.json` | 中核 9 町丁目〔非〕(2-0 の計器の写し) | 分かれている。`presence_calib_anchors_v0.json` と同じ値の写しが 2 本ある(値と単位が同じことを試験で固定) | 2-0 の計器 |
| `data/calib/hunger/`(原表の置き場) | 構築側の表(bmr・METs・NHNS 第 13/14 表・第 8-1〜8-3 表)と検証側の表(第 4-1・7-1・10・18-1 表・15 分の食事率)が**同じディレクトリ** | ファイルで分かれている(1 ファイル 1 区分)。計器の守りはディレクトリごと落とす(保守側) | 生成器 `tools/hunger/*`(通常は回さない) |
| `data/calib/pt2018/pt6_c-2.csv` | 発生量(構築側)と集中量(0240〜0243=〔検〕)が 1 本 | **列で分かれている**(`w21_sources.read_pt_c2_build_side`=集中量の列は配列にしない・W21 の組み立ては開かない) | 試験の合成ファイルだけ |
| `data/calib/pt2018/pt6_b-4.csv`・`pt6_c-3.csv`・`pt6_c-4.csv` | b-4〔検〕・c-3/c-4〔灰〕 | ファイルで分かれている | 読む口なし(守りが落とす) |
| `data/realworld/transport_census/station_flow_12.json` | 券種「合計」〔写〕と定期・普通の内訳〔灰〕 | **行で分かれている**(W12 `rail_flows` が「合計」の行だけ使う)。ファイルは W19 の凍結の入力(md5)で、分けると世界の凍結が動く=分けない | 構築 W12 |
| `data/realworld/transport_census/transfer_12.json` | transfer の daily〔写〕と peak_hourly・gate の行〔灰〕 | 行で分かれている(W12 は `kind == transfer` の daily だけ) | 構築 W12 |
| `data/realworld/transport_census/time_dist_12.json` | 〔部〕だけ | 分かれている | W12・2-0 の計器 |
| `line_capacity_12.json`・`station_od13_13.json` | 〔灰〕だけ | 分かれている(構築は読まない・計器の守りが落とす) | 読む口なし |
| `data/realworld/odpt_passenger_survey/shibuya.json` | W21 の #17(駅の事業者別の利用者数=検証側)・W12 は流量に効かない併記の列 `odpt_survey_*` に写すだけ | 列で分かれている(エンジンは `w12_external_nodes` の `node_id`・`kind`・`lines` だけ・W21 は `WORLD_COLUMNS` で `odpt_survey_*` を読まない=試験あり)。区分の食い違い(W12 は〔非〕・W21 は検証側)は親の判断(§6) | W12(写すだけ) |
| `data/research_cache/r99/` | 構築側の表(第 74-6・74-9 表など)と検証側の表(第 14・15・68-3 表)が同じディレクトリ | ファイルで分かれている(`R99Guard` が名で縛る) | 構築 W20cal |
| `data/research_cache/r107/`(〔検収 L2〕) | 家計調査 `kakei*`(§10-1=検証専用)と、賃金 `chinkou_*`・全国家計構造調査 `zk2024_*`・OSM の ATM と支払い(W21 段 4〜7 の構築側)が同じディレクトリ | ファイルで分かれている(1 ファイル 1 区分)。W21 の #47 の語 `kakei` で家計調査の名を落とす | 構築 W21(構築側のファイルだけ) |
| `data/realworld/pt_tokyo/`(〔検収 L2〕) | PT d-1〔写〕・ゾーンの表 | 分かれている(混在なし) | 構築 W16・W12 |
| `data/research_cache/estat_r3_avgtime_000032224420.xlsx`(〔検収 L2〕) | 第 30 表の原表〔検〕だけ | 分かれている(計器の語 `000032224420`・W21 の #57 で落とす) | 読む口なし |
| `data/research_cache/r89/`(〔検収 L2〕) | R-89 の答申の材料(PDF 1 本) | 1 本 1 区分 | 読む口なし |
| W12 の出力 `w12_external_nodes.parquet` | `daily_inflow` ほか〔写〕/ `odpt_survey_*`(#17 の写し) | 列で分かれている(上) | エンジン・W21・計器 |

- 〔検収 L2〕§10-1 の研究の値(R-89 の思い出しの錨・CT の値・住宅・土地統計の通勤時間ほか)は data の下にファイルが無い=W21 の検証側の一覧の語(#45・#49・#50 ほか)で名を縛るだけ。

## 2. 分けたファイルと分け方

道具 [`tools/instruments/anchor_split.py`](../../../../../tools/instruments/anchor_split.py)(2-4 V6 の道具と同じ作法=JSON を読んで鍵の名で振り分けて書くだけ・値を画面に出さない・名が表に無い錨は止める)。

| 元(消した) | 構築側(検証に使わない側) | 検証側 |
|---|---|---|
| `diversity_anchors_v0.json` | `diversity_build_anchors_v0.json`=`depart_on_00_30_band_by_employment`(第 31 表〔写〕)・`song_pi_max`・`song_regularity_R`・`song_top2_locations_share`(Song 2010=§10-3)・`activity_set_capacity`・`activity_set_jaccard_decay_lambda`(Alessandretti 2018=§10-3)・`p0_prior`(設計書 §5 の前値=現実の錨ではない)・見出し 3 つ・道具が書いた `purpose`・`split_from` | `diversity_validation_anchors_v0.json`=第 30 表の 6 本〔検〕(`tokyo_weekday_depart_*` 4・`national_weekday_depart_*` 2=出典の欄は東京も全国も第 30 表)・Schneider 2013 の 5 本〔灰〕(`motif_*` 3・`daily_locations_*` 2=区分が未決なので仮-13 のとおり検証側)・元の `purpose`・`rules`・見出し・`split_from` |

- 確かめ(`anchor_split.py check diversity --rev 32fb262`): `merged_equals_original: true`・`keys_equal: true`・`anchors_md5_equal: 17/17`・`build_extra_equal: true`・`no_overlap: true`(真偽と数だけ)。構築側の錨ごとの md5 は試験に固定した(`tests/tools/test_seal_split_337.py`)。
- 錨の名の区分の根拠は道具の表 `PLANS["diversity"].why`(錨ごとに 1 行)。

## 3. 読む側の変更

| ファイル | 変更 |
|---|---|
| `tools/w17/diversity_yardstick.py` | `DEFAULT_ANCHORS_PATHS`(構築側+検証側)・`merge_anchor_docs`(同じ錨の名が 2 本にあれば止める)・`load_anchors` は 1 本・複数・既定の 2 本を受ける・`--anchors` は複数可。物差しの数え方と出力の形は同じ |
| `tests/w17/conftest.py`・`test_diversity_yardstick.py` | fixture は**構築側のファイル+検証側の作り物**(鍵の名だけ同じ・`source: synthetic(test)`・M1 の閾値は試験の docstring の 0.5%)。番人(セッションの autouse)=既定の道筋で読もうとすると検証側を無いファイルに差し替えて落とす。CLI の試験 2 本は `--anchors` に作り物を渡す。assert は緩めていない。試験 3 本を足した |
| `tools/instruments/read_guard.py` | 封印の語に `realworld/odpt_rt`・計器の段の語に `diversity_validation_anchors`(計器 5 本の守りは全部これを使う) |
| `src/shibuya/build/pop/w21_sources.py` | 検証側の一覧の #16 に `realworld/odpt_rt`・#57 に `diversity_validation_anchors`(行の id は同じ=W21 の manifest は動かない) |
| `tests/perception/facts/test_percept_is_scratch.py`・`tests/engine/test_state_format_10f.py` | 古い commit の写しの木に `docs/bench/anchors` を丸ごと写していた(監査フックで、混在の錨 3 本の写しを作業用の置き場に書き出していた)→ **その版のエンジンが開く 2 本だけ**(`hunger_energy_anchors_v0.json`・`ssb2021_activity_prior_v0.json`=その版の src を grep して確かめた)を写す |
| `tests/tools/test_anchor_gauge.py` | 守りの負の対照に `diversity_validation_anchors_v0.json` と `data/realworld/odpt_rt/…` を足した |

## 4. 負の対照と開いたファイルの数え方

- 監査フックの差し込み(作業用の置き場の pytest の差し込み=`open` の監査イベントのうち、封印・検証側・〔灰〕の語 29 個のどれかを含む道筋を試験ごとに数える・名だけ控える)で、全体試験(`-m "not slow and not gpu"`・`tests/c7` を含む)を直しの**前**に回した: 封印・検証側の名を開いた試験のうち、本段で直すべきものは `tests/w17`(`diversity_anchors_v0.json` 3 回)と古い commit の写しの 2 本(混在の 3 本の写し)。ほかは (a) エンジンが空腹の検証側を読む(エンジンを回す試験の全部=§7 の 2 の仕事)・(b) W19 の凍結が封印の層の md5 を取る(設計どおり=値は使わない)・(c) W12 の構築の入力(上の表の〔写〕と〔灰〕の行)・(d) 守りの負の対照の作り物の道筋(合成の置き場)・(e) 道具のモジュール名 `holdout_compare.py` の読み込み。
- 直しの**後**(同じ差し込み・同じ印の全体試験): `tests/w17` が開いた検証側の名は**番人の差し替え先(無いファイル)1 回だけ**(前は `diversity_anchors_v0.json` 3 回)・古い commit の写しの 2 本は混在の 3 本の写しが消え、その版のエンジンが開く `hunger_energy_anchors_v0.json` だけ(前は 4 本・3 本)・`tests/c7` は前も後も封印・検証側の本物のファイルを 0 回(合成の置き場の `…/kddi_la/la.json` 4 回と道具のモジュール 2 回)・`diversity_validation_anchors_v0.json` の名を開いたのは負の対照の植えたファイル(作業用の置き場)だけ。残るのはエンジンが空腹の検証側を読む分(試験ファイル 73 本=前と同じ・§7 の 2)と (b)〜(e)。
- 物差しの fixture の負の対照(`test_yardstick_fixture_reads_no_validation_file_and_the_hook_works`): 構築側だけを読むと数は 0・作り物の置き場に検証側の名のファイルを植えて開くとフックが数える。
- 守り: 計器の守り(`read_guard.deny_hit`)は検証側 3 本の名を落とし、構築側・較正側 5 本の名は落とさない。W21 の語の表に足した 2 語がある(試験)。

## 5. ODPT の取得のログの圧縮

### 5-1 仕組み(`tools/realworld_fetch/logrotate.py`・`ledger.py`・`cli.py`)

- 対象: `_ledger.jsonl`(UTF-8 の JSON Lines=`ledger.append` が書く)・`_scheduler_odpt.log`・`_scheduler.log`(タスクの PowerShell の `*>>` が書く=UTF-16 LE)。
- 回し方: (1) 回す側どうしは錠 `_logs/.rotate.lock`(排他の作成・600 秒より古い錠は外す)。(2) 生きているファイルを `<名>.rotating.<rotid>` へ `os.replace` で改名(Windows では書き手が開いている間は改名が共有違反で失敗する=何もせず次の回へ・書き手は止めない)。改名の後の書き手は新しいファイルを作る。POSIX では改名の前に開いた書き手の追記が終わるまで flock で待つ(書き手は錠を取った後に手の内のファイルが今の名と同じかを確かめ、違えば開き直す)。(3) バイト列を日ごとの連続した塊に分ける(台帳は行の `ts_utc` の JST の日・日は前へ戻らない/ログは最後に書かれた日 1 つ)→ 塊ごとに一時の名で gzip を書いて `os.replace` で `_logs/<YYYY-MM>/<名>.<日>.r<rotid>.p<k>.gz`。(4) 置いた gz を全部ほどき、つないだバイト列が改名したファイルと同じことを確かめてから改名したファイルを消す(違えば gz を消して残す)。(5) 途中で落ちたら `rotating` が残る=次の回の最初に片付ける。読み手は `rotating` の残っている rotid の gz を使わない=同じ行を 2 度読まない。
- 読み口: `logrotate.read_bytes_all`・`read_text_all`(gz → 残った rotating → 生きているファイルの順=元の並び)。台帳の読み手 `ledger.read_all` はこれを通す(`--report` と日次の報告は gz を読む)。`--verify` は名が `_` で始まるファイルを見ないので gz は対象の外。
- 書き手: `ledger.append` は回しの改名の瞬間に開けなかったら少し待って開き直す(Windows=PermissionError・最大 200 回 × 10 ms)。
- いつ回すか: 取得の通常の回(`cli.main` の最後)で、その日にまだ回していないものを回す(状態 `_logs/_rotate_state.json`・開いているものは黙って次の回へ)。ODPT のタスク(5 分ごと)は自分のログを開いたまま走るので、`_scheduler_odpt.log` は日次のタスク(12:00)と前日のアメダスのタスク(0:30)の回で回る。台帳と `_scheduler.log` は日が変わった最初の ODPT の回で回る。手で回すのは `--rotate-logs`(日に依らず回す)。標準ライブラリだけ(タスクはシステムの Python 3.12 で動く)。

### 5-2 試験(`tests/tools/test_realworld_fetch_logrotate.py`・13 本・合成の置き場だけ)

JST の日の境目で分かれる・ほどくと 1 バイトも違わない(gz の行数=元の行数=`read_all` の行)・回した後の追記が後ろにつながる・日が前へ戻る行と壊れた行と終わりの改行の無い行・UTF-16 のログ(BOM・回した後の新しいファイル)・書き手が開いている間は回さない(改名の失敗の差し替え+Windows の本物の手の内)・2 つ目の塊で落ちる → 書いた gz を消して rotating を残す → 読み口は rotating を読む → 残った gz があっても 2 度読まない → 次の回で片付く・ほどいた gz が違えば残す・**書き手が 400 行を追記し続ける間に回し続けて、書き手は落ちず行は欠けず重ならない**(8 回くり返して通る)・錠(2 つ目の回しは止まる・古い錠は外す)・1 日 1 回・`--rotate-logs`・`--report` と `--verify` が gz の置き場で通る。

負の対照(作業用の置き場の道具・合成の置き場・Windows): 書き手の開き直しを外す(`APPEND_TRIES=1`=前の `ledger.append` と同じ)と、400 行の追記の間に回しを 13〜15 回かけて **書き手の PermissionError が 10〜14 回/試行**(5 試行)。開き直しあり(既定 200)では 0 回/5 試行(回し 17〜23 回)・読めた行=書けた行(どちらも欠けも重なりも無い=落ちた書き手の行は書かれていない)。=本体の古い `ledger.append` が動いている間に実際の台帳を回すと、改名の瞬間に追記した回が落ちうる(§5-3 で台帳を回さなかった理由の 1 つ)。

### 5-3 実際の置き場(既存の分)

| ファイル | 前(大きさ・行) | gz の見込み | 回したか |
|---|---|---|---|
| `_ledger.jsonl` | 13,922,828 B・32,701 行(2026-10-17 の測り) | 写しで回した: 13,914,161 B・32,685 行 → 415,317 B(71 日の塊=2026-08-07〜10-17)・ほどくと元と同じ・`read_all` 32,685 行(壊れた行 0)。写しは消した | **回していない**(本体の取得の道具=タスクが動かす `tools/realworld_fetch` はまだ古い読み手=台帳の gz を読まない。取り込む前に回すと、日次の報告と `--report` が過去の行を見なくなる) |
| `_scheduler_odpt.log` | 9,485,768 B・84,031 行(UTF-16) | 108,669 B(メモリの中で縮めてほどいて同じ・書いていない) | **回していない**(実行の権限の判定で止まった=元を消す操作) |
| `_scheduler.log` | 102,020 B・901 行 | 3,909 B(同) | 同上 |

回す手順(親かユーザー・取り込みの後): 本体で `python tools/realworld_fetch/rw_fetch_daily.py --rotate-logs --out-dir data\realworld_live`(タスクの回の合間=開いているものは busy と出て次の回で回る)。取り込みの後はタスクの回が日に 1 回ずつ自動で回す。

## 6. 他の封印の層の確認(名前と schema だけ)

| 層 | 見たもの | 同じ形の混在 | 読む口 |
|---|---|---|---|
| `kddi_la` | `data/realworld/kddi_la/` に 1 本(6.8 MB)・表は滞在の 2 表(列の名は試験の合成の形と同じ) | 1 本の中は全部が封印=混在なし | `tools/c7/holdout_compare.py` だけ(開封は事後 1 回・門番つき・開封済み) |
| `shibuya_jinryu`(と `_k5`) | `data/realworld/shibuya_jinryu/2026/…` に 10 本(滞在・通過 × 性・年齢・属性の CSV と JSON) | 混在なし(全部が封印・`kddi_la` と同じ元=10-13b §1 1-2 で「照合用」) | なし(W19 の md5 だけ) |
| `boundary_counts.json` | 鍵 `_meta`・`counts`(1,050 行・列 17)。〔申告・検収 L6〕実装役はこれに加えて `_meta.sources_present`(出典の名の一覧=大都市交通センサスの 5 系(station_flow・time_dist・transfer・line_capacity・station_od13)+ODPT 乗降人員+導出)まで読んだ=値ではないが「名前と schema だけ」より一歩深い。次からは鍵の名と行・列の数までに留める | **中身が構築の入力の写し(〔写〕〔部〕)と〔灰〕の混ざった封印の 1 本**=10-13b §1 1-2 で「照合用(独立でない)」と決めた形。読む口が無いので分けない(分けるには値を読む) | なし(W19 の md5・2-0 の計器は〔灰〕の印の欄だけで値は空) |
| `data/realworld_live/odpt_rt/` | `.json.gz` 5,391 本(運行情報・在線・バスの在線 × 事業者・チャレンジ枠を含む)・圧縮の前の形の `.json` 4,987 本(2026-10-03〜第333 の前=縮めていない)・`_last_fetch.json`・README | 混在なし(全部が検証専用・静的の版 `odpt_static/` は別のディレクトリ=構築側) | 取得の道具の `--verify`(`_meta` の形だけ)。src は読まない |
| `data/realworld/odpt_rt/`(v1 の頃) | 3 本(2026-08-07・10-03) | 混在なし。**どの守りの語にも当たっていなかった**=本段で語を足した | なし |
| PT の検証側 | `data/calib/pt2018/` の 4 本+手引き・MANIFEST | c-2 だけ発生量と集中量が 1 本(列で分かれている=§1)。b-4・c-3・c-4 は 1 本 1 区分 | `w21_sources`(c-2 は列を絞る口・試験の合成だけ) |
| 区民意識調査の個票 | data の下に該当の名のファイルなし(未取得) | — | W21 の #42 の語で落とす |

## 7. byte-check・2 日・再開

| 何を | 道具と条件 | 結果 |
|---|---|---|
| byte-check 19 構成([byte_check_seal.json](byte_check_seal.json)) | 10e の道具 `byte_check_10e.py side`(5,000 体・seed 1・1 日・テープつき・`PYTHONHASHSEED=0`)。head=土台 `32fb262` の `git archive`(src・エンジンが開く錨 3 本・設計の表 5 本・w6-regen)+`HEAD_TREE_FILES` の data 3 本の**写し**(つなぎ=junction は権限の判定で作れなかった=祝日の CSV と OSM の 2 本をそのまま写した・`tree_missing` は空)・世界は本体の `data/world/v2` | **19/19 で 25 欄とも同じ**(w6_v3_default `b8eadcb51e8705e7`/64,528・v3_mem_rel `768b2262e3b0999e`/67,794・v3_classical `ca25874a5e4acb79`/93,017・v3_classical_mem_rel `9dd9d5684891b57c`/105,363=vb24 の V6 の値と同じ) |
| 2 日の通し([two_days_head_vs_seal.json](two_days_head_vs_seal.json)) | mr65 の道具 `arms_mr65.py side --arms default --days 2`・v3_mem_rel と w6_v3_default・head の写しと作業木 | 比べた 19 欄とテープの列ごとの sha が全部同じ(v3_mem_rel `31c9b19409e18b2f`/145,675・w6_v3_default `b346bb6e3ecc60af`/138,946) |
| 再開=通し([resume_seal_5000.json](resume_seal_5000.json)) | 同じ道具の `resume`(v3_mem_rel・5,000 体・2 日・日の境目で保存 → 再開) | final `31c9b19409e18b2f` が同じ・境目の後の checkpoint 4 点が同じ・呼数が同じ(mr65 の記録と同じ値) |

- src の差は `build/pop/w21_sources.py` の 2 行だけ(層の契約で build は実行時に import されない=lint-imports の契約が kept)。エンジンが開く追跡ファイル(`HEAD_TREE_FILES`)は 1 本も変えていない。

## 8. 試験

| 何を | 印 | 結果 |
|---|---|---|
| 全体(作業木・`tests/c7` を含む・監査フックの差し込みつき) | `-m "not slow and not gpu" -n 8 --dist loadfile` | **5,560 passed・1 failed・1 skipped・1 xfailed**(14 分 30 秒)。落ちた 1 件は既知の `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`(作業木の `data` が本体へのつなぎで起きる落ち=前の段の記録と同じ)。この中に `tests/engine`・`tests/tools`・`tests/economy/cp2`・`tests/c8`・`tests/engine/bridging`・状態台帳・10f・`tests/w17`・取得の道具の試験を含む |
| 直しの前の同じ全体 | 同じ | 5,528 passed・2 failed(上の ab7 と `tests/engine/test_relations_tenure.py::test_switch_is_checked_and_on_the_cli_and_sets_the_default_tau`=並列のときだけの落ち・単独では通る・直しの後の全体では通った)・1 skipped・1 xfailed |
| `tests/c7` 単独(監査フックつき) | `-m "not slow and not gpu"` | **168 passed**・封印・検証側の本物のファイルを開いた回数 0 |
| 本段の試験(`tests/tools/test_seal_split_337.py`・`test_realworld_fetch_logrotate.py`・`tests/w17`・`test_anchor_gauge.py`・`test_warmup_gauge.py`・`tests/build_pop/test_w21_sources.py`・`test_realworld_fetch_odpt.py`) | `-m "not slow and not gpu"` | 134 passed |
| 層の契約 `lint-imports --no-cache` | — | 5 kept・0 broken |
| 秘密の検査 `tools/scan_secrets.py`(変えたファイルと足したファイル=検証側の錨の 1 本を除く=元のファイルと同じ中身) | — | CLEAN |

## 9. 触った共有ファイル(並行の作業木とぶつかりうる所)

- `src/shibuya/build/pop/w21_sources.py`(検証側の一覧の 2 行に語を 1 つずつ=4-1 段 8〜9 の作業木と同じファイル)。
- `tools/instruments/read_guard.py`(語を 2 つ)・`tests/tools/test_anchor_gauge.py`(負の対照に 2 つ)。
- `tests/engine/test_state_format_10f.py`・`tests/perception/facts/test_percept_is_scratch.py`(写しの木の錨の道筋)。
- `tools/realworld_fetch/{cli,ledger}.py`(取得の道具)。状態台帳・凍結の表・`src/shibuya/cli.py`・つなぎの台帳は触っていない。
- つなぎの台帳: 混在の錨の宣言の行は無かった(`混在`・錨のファイル名・ログの名で 467 行を探して 0 件)=閉じる行も注を足す行も無い。

## 10. 限界・親の判断

1. **エンジンは空腹の検証側のファイルを読む**(第 18-1 表・15 分の食事率)=§7 の 2 の置き換え(小さな版上げ)で直す。置き換えた後に「エンジンが検証側の錨を読まない」試験を入れる(本段の監査フックの差し込みがそのまま使える)。
2. `presence_validation_anchors_v0.json` の 6 本のうち 2 本は構築の入力の写し(`homebound_boarding_time_dist_2015`=time_dist_12・`full_population`=W16 の体数)で、仮-13 の保守側で検証側に置いてある。較正側へ移すか(移すと 2-0 の計器が読める)。
3. ODPT 乗降人員(`odpt_passenger_survey/shibuya.json`)の区分が W12/R-115(〔非〕=写すだけ)と W21(#17=検証側)で食い違う。W12 の出力の列 `odpt_survey_*` に写っている(エンジンと W21 は読まない)。
4. Schneider 2013 の 5 本は区分が未決(〔灰〕=検証側に置いた)。`motif_threshold` は物差しの数え方の閾値として使う=検証側のファイルにあると物差しは検証側を開かないと回らない。
5. W12 の生の入力(station_flow_12・transfer_12)は行で分かれているだけ。ファイルを分けるには W12 の入力の道筋と W19 の凍結が動く(版上げ)。
6. 実際のログの既存の分の圧縮は回していない(§5-3)。台帳は取り込みの後に回す。古い取得の道具(本体)の `ledger.append` は改名の瞬間に開けないと落ちうる(Windows・回しは日に 1 回・改名はマイクロ秒)=取り込みで直る。
7. `odpt_rt/` に第333 の前の縮めていない `.json` が 4,987 本ある(§6)。縮めるかは親の判断(本段の範囲はログ 3 本)。
8. 監査フックは Python の `open` の監査イベントだけを見る(pyarrow・subprocess の読みは見えない=read_guard の docstring の 5 つの抜け道と同じ)。

## 11. 検収の後の直し(受入・低 7=[review.md](review.md)・親の判断)と rebase

| 番 | 直したこと | 確かめ |
|---|---|---|
| L1 | `tests/c7/conftest.py` に番人の監査フック(試験ごとの autouse の fixture の間だけ効く=tests/c7 の試験だけ): リポの `data/`・`docs/` の下(つなぎの両方の形)で `read_guard.GAUGE_DENY_TOKENS` の語を含む道筋を `open` しようとしたら開く前に PermissionError。合成の置き場(tmp)と道具のモジュール(tools/)は対象の外。試験 `tests/c7/test_seal_guard_337.py`(7 本=無いファイルの名 6 つで開く前に落ちる・較正側と合成の置き場は通る) | `tests/c7`(`-m "not slow and not gpu"`)175 passed(168+番人の 7) |
| L2 | §1 の表に 4 行(`r107`・`pt_tokyo`・第 30 表の原表・`r89`)と §10-1 の研究の値の注 1 行(名前と区分だけ) | — |
| L3 | `logrotate.iter_chunks`: 読む前と後で一覧(gz・rotating)が違うか `FileNotFoundError` なら一覧を取り直してやり直す(3 回まで)。返り値は list | 試験 2 本(読みの途中で回る=生きているファイルが消える/読んだ後に回って一覧が変わる → 2 回目で全部読める) |
| L4 | 古い錠の掃除 `_clear_stale`: `os.replace` で別名へ移せた側だけが進む(移せなければ RotateBusy)。移したものが古くなかった(見た後に新しい錠が作られていた)ら元の名へ戻して RotateBusy | 試験 2 本(ほかの回しが先に片付けた → 進まない/新しい錠を移してしまった → 戻して進まない・墓の名が残らない) |
| L5 | `anchor_split.PLANS`・`Plan.why`(`_WHY`)・`logrotate._SPEC` を `MappingProxyType` に | 試験 2 本(書くと TypeError) |
| L6 | §6 の `boundary_counts.json` の行に、`_meta.sources_present`(出典の名の一覧)まで読んだことを申告として残した(中身の記述はそのまま=親の判断) | — |
| L7 | 新しい試験の関数名から open を外した(`test_writer_handle_blocks_rename_on_windows`・`test_yardstick_fixture_reads_no_validation_file_and_the_hook_works`) | — |

- rebase: 本体の最新 `13e9c90`(`32fb262` の後に 4-1 段 8〜9=build 側と文書)。重なるのは `src/shibuya/build/pop/w21_sources.py` だけ=控え(本段の版・土台の版)→ 作業木の版を戻して `git merge --ff-only build/spatial-d102-prep` → `git merge-file`(衝突 0)→ 本段の 2 語だけが差に残る。ほかの変えたファイルは本体側で動いていない。
- byte-check(既定の 4 構成・本体 `13e9c90` の写し=`HEAD_TREE_FILES` の追跡ファイル+data 3 本の写し・作業用の置き場 `_bc2`): **4/4 で 25 欄とも同じ**([byte_check_seal_4cfg_13e9c90.json](byte_check_seal_4cfg_13e9c90.json)=w6_v3_default `b8eadcb51e8705e7`/64,528・w6_v3_activity_off `c88ba9104f45f897`/50,006・w6_v1_default `e1288e092ddaca86`/51,655・v3_mem_rel `768b2262e3b0999e`/67,794)。つなぎ(junction)は使わず data 3 本を写した(前の回と同じ)。
- 試験(rebase の後): `tests/c7 tests/tools tests/w17 tests/engine/bridging tests/economy/cp2 tests/c8`(`-n 2 --dist loadfile -m "not slow and not gpu"`)**682 passed・failed 0**(1 分 46 秒・取得の道具の試験は `tests/tools` の中=`tests/realworld_fetch` は無い)。`lint-imports --no-cache` 5 kept・0 broken。秘密の検査 CLEAN。


## §親の検収(第337・Fable 5.1・rebase の後)

- 本体 9fc0b71(カレンダー 1b の文書の後) へ rebase(実装役が 13e9c90 へ控え+早送り+merge-file で(`w21_sources.py` は 4-1 と重なる=衝突 0)・親が 8169d4b(カレンダー 1b)→ 9fc0b71 へ rebase=衝突なし)→ e7221b9。範囲の試験(engine・tools・**c7(監査フックつき)**・w17・bridging・cp2・c8)****3,274 passed・1 skipped**(1,265 秒・8169d4b の上で)**。
- 親の byte-check 4 構成(本体 HEAD の src vs 作業木の src)=**final 同じ・25 欄とも差なし**(`parent_head_vs_seal_4cfg.json`)。整理=既定の結果は 1 バイトも変えない(実装役 19/19・検収役 4/4)。
- **data 無しの写し(detached の作業木・junction なし)で CI-1 と同じ引数の全体試験(tests/c7 を含む)=**5,383 passed・281 skipped・failed 0**(1,232 秒・CI の印=`-m "not gpu and not slow" -n 2 --dist loadfile`・tests/c7 は監査フックつきで通過)**。
- 独立検収([review.md](review.md))=受入(高 0・中 0・低 7=c7 の監査フック・区分の表の抜け 4 か所・読み手の再試行・錠の掃除・MappingProxyType・boundary_counts の申告・試験名の open)→ 全部直した(§11)。検収役の独立の再計算(錨ごとの md5 17/17・区分の根拠・台帳とログの回転を写しで=バイト一致・書き手が追記し続ける間の回転 1,500 行 × 3 試行で欠け 0・PowerShell の `*>>` が開いている間は busy・守りの負の対照=HEAD では開く 2 本が作業木では開く前に落ちる・tests/c7 を監査フックの下で 168 passed=実在の封印/検証側のファイルを開かない)は全部一致。親の判断: `tests/c7` は L1 の番人つきで**全体試験に戻す**(手元の全体試験の引数から `--ignore=tests/c7` を外す・CI-1 は元から含む)・実体のログの回転と `odpt_rt/` の未圧縮 json 4,988 本の圧縮は取り込みの後に親が回す(検証つき)・区分の 3 件(presence_validation の構築の入力の写し 2 錨・ODPT 乗降人員の区分の食い違い・Schneider の motif_threshold)は PENDING §1-1。
- 判定: **受入**(整理=結果不変)。
