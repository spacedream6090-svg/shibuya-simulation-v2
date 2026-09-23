<!-- 層2(別 Fable)の独立検収報告・2026-09-12・原文のまま(パスのみマスク) -->
# 層2 独立検収: C7 再ラン c7-day-3(2026-09-12)

- 検収役: 層2(親とは別の Fable)。HEAD `7533747`(第169)・ブランチ build/c5-c8・`git status` clean。
- 規律遵守: コミット/push/リポ内書き換え/サブ起動/ssh/data/realworld 読み取り/holdout 開封は**行っていない**。書いたのは本ファイルのみ。一時出力は `scratchpad/d68/layer2_tmp/` 配下。

## 結論: **条件付き合格**

1. 受入表 16 行は同じ入力で再実行して**親の出力と完全一致**(CRLF 差のみ)。T2-c の 4 点×5 ハッシュと final_hash `62e7c16e42ee78bd…` を自分で突合して一致。holdout を開けた痕跡なし。
2. ただし **`data/world/v2` の W17 が v2 第 2 回へ昇格(第168)した後、実データ golden 3 本が更新されておらず pytest が 3 failed**(退化検査の要 ② を含む)。合格の条件=親が値を再確定して golden を張り直すこと。
3. 在圏の物差しの「前=c7-day-2 03 時 221,090」は**実は mock 5,000 体×78.01 の換算値**(本物の c7-day-2 は 212,487)。方向と結論は変わらないが、build-report §1h・devlog・コミット文の出典表記を正すこと。訪日は全 17,404 体が W17 で宿泊施設就寝=「域外常住のはず」の前提は不適切(D-66 指標から外すべき)。

## 検収表

| # | 対象 | 親の主張 | 自分の再計算値 | 一致 | 所見 |
|---|---|---|---|---|---|
| 1-1 | 受入表(c7_accept.py 再実行) | 判定 11/16・合格 11・不合格 0・PASS | 同じ入力(summary/time_v/--out-bytes 195,139,226/--manifest checkpoints.json/--wc wc_index.json/--determinism t2a_1,t2a_2/--full replay_checkpoints.json)で **json/md とも親と同一**(`diff --strip-trailing-cr` 差なし) | 一致 | 親が渡した --manifest の実体は記録なし。holdout_open を持たない manifest なら何を渡しても同じ表になる |
| 1-2 | W1 壁時計 | 9.495 h | summary 34,182.30 s = 9.4951 h/time -v 9:29:43 = 9.4953 h | 一致 | |
| 1-3 | M8 RSS | 1.505 GiB | 1,578,092 kB = 1.5050 GiB | 一致 | |
| 1-4 | S1 出力バイト | 0.182 GiB | 194,949,218+74,951+4,053+111,004 = 195,139,226 B = 0.1817 GiB | 一致 | サーバー側の 4 ファイル実サイズは未確認(ssh 禁止・依頼文の値を使用) |
| 1-5 | L4 呼数 | 2,805,670(7.19/体) | summary・tape_stats.json rows とも 2,805,670 | 一致 | |
| 1-6 | T2-c: checkpoints vs replay 4 点 | 全点一致・final 一致 | tick 359/719/1079/1439 の combined/population_hash/schedule_hash/agents_hash/world_hash **全 20 値一致**。final_hash 両方 `62e7c16e42ee78bd0359…`。summary「最終 62e7c16e42ee78bd」と前方一致。population/schedule は全点単一値。docs 写し == data/runs 実体。manifest(fleet 欄除く)一致 | 一致 | 再生そのもの(40 分・サーバー)は再実行していない=成果物の突合のみ |
| 1-7 | T2-a | 4 点 vs 4 点 OK | t2a_1.json == t2a_2.json(5,000 体・final `ba01bd0beed19666…`)。scratch d68 の原本とも同一。README(第168)の checkpoint ba01bd0b と整合 | 一致 | 2 ラン自体は再実行していない |
| 1-8 | HOLD/SEAL 未開封 | 未照合 | checkpoints.json の top-level/manifest とも `holdout_open` 無し・docs/bench/c7 に holdout* 無し・`git status` clean・HEAD の 16 ファイルに data/ 無し・data/ は gitignore | 一致 | |
| 2-1 | 物差し after(c7-day-3) | 03 時 29,322/09 時 172,265/12 時 223,643/昼夜比 09/03 5.88・12/03 7.63/起床率差 03 0.128・12 0.019・最大 0.518@23 | 同 journal+summary で再実行 → after 側 JSON が親記録と**完全同一**(path 除く) | 一致 | |
| 2-2 | 物差し before「c7-day-2」 | 03 時 221,090/09 時 264,075/12 時 239,423/昼夜比 1.19/17 of 20 | 親記録の before 入力 = `<scratch>/d66/occ_base.npz`(**5,000 体 mock・×78.0134**)。同入力で再実行 → 17/20 で一致。**本物の c7-day-2(390,067 体・docs/bench/c7/occupancy_series_c7-day-2.json)を before にすると 03 時 212,487/09 時 253,757/12 時 242,780/昼夜比 1.194・1.143 → 判定可 10 指標中 10 が現実側**(種別・起床率は series に無く判定不能) | 数値は再現・**出典ラベル不一致** | mock は実 c7-day-2 を +4.0〜4.1% で過大(設計書 §12「4% 以内」の範囲)。結論は不変だが「221,090 = c7-day-2」は誤記 |
| 2-3 | 「訪日=域外常住のはず」の前提 | 見直す(次) | W17 day0: 訪日 17,404 体すべて home_cell=−1 かつ**全員に 宿泊施設 で就寝の行あり**(target_cell は全て −1)。03 時 5 エリア在圏 12,843 = 73.8% | — | 前提は**不適切**: 訪日は設計上「舞台の宿で寝る」体。D-66 種別から訪日を外すと 03 時 D-66 種別 15,855→3,012(全体比 0.541→0.103)。「訪日 在圏 小さいほど良い」行は向きが逆 |
| 3-1 | pytest(derive_v2 + executor) | (親は 第166 で 137 passed=v1 表時点) | **36 passed, 3 failed**(23.5 s) | 不一致 | 下記「問題 1」 |
| 3-2 | 本番表(第 2 回)の域外居住者ブロック分布 day0 | 親は第 1 回の値のみ | **v1** [92 / 160,033 / 133,575 / 47,861 / 4,756 / ≥5:128] 平均 1.704 本/日(計 590,430)→ **v2** [1,269 / 254,605 / 85,421 / 5,076 / 74 / 0] 平均 1.273 本/日(計 440,971)。域内居住者は v1==v2(本数・start/end 一致)。v2 の 0 本 1,269 = summary「終日域外 1,269」 | (親未提示) | 第 1 回表は手元に無く親の [36/99,212/…]→[298/282,273/…] は未確認 |
| 3-3 | 合成行 10 例((a)3 例・(b)3 例・(c)4 例) | 設計書 §2 追補の規則 | 全例が §2 追補の文どおり(詳細は下) | 一致 | 文どおりだが意味上の穴 4 種を規模つきで下に記す |
| 4-1 | W17 v2 ゲート | 全ゲート PASS・被覆≥0.999 の体 0.999075 | w17_gates.json: parse 0.009141・coverage_ge_0999 0.999075・gaps 385・night 0・has_sleep 0.996239・engine 修正 0。ingest_r2.log の gate 行 13 本すべて PASS。被覆<0.999 の体 361 = (1−0.999075)×390,067=360.8 | 一致 | README「失敗 0」に対し gates は n_failed_agents **1,814**(parse 落ち行を持つ体)。定義違い(呼の失敗 0 vs 行のパース失敗)だが README に無い |
| 4-2 | W17 md5(README) | parquet 3113e9ba・header e270b128・gates 82525fd4 | `3113e9ba7abb…`・`e270b1287de8…`(data と docs の header 同一)・`82525fd461fa…`。v1 退避 data/world/v2/w17v1_backup/ 実在 | 一致 | |
| 4-3 | 多様性の物差し(本番 parquet で再実行・37 s) | 出勤代理 :00/:30(15 分ビン)0.649・最頻ビン占有 0.110・H 4.83 | M3b(15 分ビン)**0.6485**・最頻 08:00 / **0.1099**・H **4.8279** bit。after 側 JSON が親記録(w17v2_r2/ で計測)と label/source 以外**同一** | 一致 | 昇格後の表 = 計測時の表であることも同時に確認。gates の M3b on_00_30 0.1276 は「分ちょうど」定義で README の 0.649(15 分ビン)とは別物 |

## 見つけた問題(重大→軽微)

### 問題 1(中): W17 昇格後に実データ golden 3 本が古いまま=HEAD で pytest が赤

- 再現: `PYTHONUTF8=1 .venv/Scripts/python.exe -m pytest tests/engine/test_presence_derive_v2.py tests/engine/test_presence_executor.py -q -o addopts=""` → 3 failed / 36 passed。
  1. `test_presence_derive_v2.py::test_v2_rule_on_the_real_w17_matches_the_parent_verified_counts`: 期待 v1 [85,766/214,998/45,631/50](docstring も「現行 W17 **v1 表**」)・実測 [92/160,033/133,575/47,861]。
  2. `test_presence_executor.py::test_null_arm_reproduces_the_recorded_checkpoint`(§7 ②「退化検査の要」): 期待 `c96baf821c9a046f`・実測 `b4ad8140fe4176db…`。
  3. `test_presence_executor.py::test_derive_folding_matches_the_parent_verified_counts`: 期待 306,410 本・実測 590,430 本。
- 原因: 第168(334e8a5)で `data/world/v2/w17_schedule.parquet` を v2 第 2 回へ昇格したが、同コミットは tests/ を触っていない(`git show --stat 334e8a5`)。第166 の「137 passed」は v1 表での値。
- 含意: 帰無腕の退化検査 ② が機能していない状態で c7-day-3 が回っている。**親が本番表で値を再確定して golden を張り直す**(または v1 退避表を fixture で明示する)まで C7 の「検収=テスト緑」は言えない。コードの誤りではなく釘の古さ、という読みで整合(域内居住者 v1==v2、0 本 1,269 = summary の終日域外と一致)。

### 問題 2(中〜軽): 在圏の物差しの before「c7-day-2」は mock 5,000 体×78.01 の換算値

- 再現: `docs/bench/c7/yardstick/after_c7-day-3_vs_c7-day-2/presence_yardstick.json` の `before.path` = `<scratch>/d66/occ_base.npz`・`before.n_agents` = 5000・`scale.factor` = 78.0134。`scratchpad/d66/base_summary.txt` 1 行目 `[run] n=5000`。
- 本物: `docs/bench/c7/occupancy_series_c7-day-2.json`(source = scratchpad/c7/occupancy.npz・390,067 体)は 03 時 **212,487**・09 時 253,757・12 時 242,780。`docs/bench/c7/yardstick/before_c7-day-2/` も同値。
- 含意: 設計書 §12 が「前後比較は mock でよい(4% 以内)」と事前登録しているので手続きは可。しかし build-report-C7 §1h・devlog 第169・コミット文の「c7-day-2 03 時 221,090→29,322」は出典が違う。**「mock 5,000×78.01(第143 基準)」と書き直す**か、本物の series を before にして 212,487→29,322 と書く(私の再実行: `--before-series docs/bench/c7/occupancy_series_c7-day-2.json --before-n-agents 390067` → 判定可 10/10 が現実側)。

### 問題 3(中・設計上の穴=v2 の効き目の範囲): 乗車区切りの無い域外居住者が 55.7%

- 本番表 day0: 域外居住者 346,445 のうち乗車区切り(乗車行/移動・域外行)が **0 の体 193,012(55.7%)**(分布 0..5: [193,012 / 46,852 / 94,115 / 11,977 / 487 / 2])。v2 はこれらを「全区間」で読むので v1 とほぼ同じ(平均本数 1.357→1.295)。これらの体の v2 ブロック 249,946 本のうち **77.5%(193,665)が「移動 駅」行で始まる**=自宅側の駅から在圏扱い。平均スパン 547 分(乗車あり体 386 分)。
- 含意: v2 が直したかった「自宅側の行を舞台の中と読む」欠陥は、乗車行を書かなかった過半の体には残る(本数ではなく**到着時刻の前倒しと在圏の延び**として出る=昼間 1.3〜1.7 倍(D-67)の一部はこれかもしれない)。§2 追補の文どおりの挙動なので不一致ではないが、根治 D-69 の必要性を裏づける規模として記録。
- 再現: `layer2_tmp/w17_noride.py`。

### 問題 4(軽): 偶奇規則の意味上の穴 3 種(いずれも設計書の文どおり・規模つき)

| 型 | 規模(本番表 day0・域外居住者) | 読み方 | 所見 |
|---|---|---|---|
| (a) 乗車が奇数 ≥3(3,5) | 11,979 体(≥3 は 12,466) | 最後の乗車の**後**のランを在圏に採り、その後の自宅行へ乗車なしで帰る=5,056 体(錨なし 4,096) | 「帰りの乗車の後の店」を在圏に読む=v2 の動機と逆。奇数側=行きの仮定の帰結 |
| (a') 乗車が 1 つ・錨なし・前後とも滞在 | 1,269 体 | 乗車前の滞在を落とし乗車後を採る(その 1 本を「行き」と仮定)。救済(後に滞在なし)は 122 体 | 「帰りだけ書いた+帰宅後の店」型は逆に読まれる |
| (b) 錨が偶数区間と奇数区間の両方 | 12,036 体(錨あり 269,055 中) | 最初の錨ランの偶奇で非錨ランを選ぶ(合成 (b3): 乗車前 target_cell≥0 の買物→勤務*→帰りの乗車→食事 = 食事も在圏) | 文どおり。錨が両側にある体では偶奇の情報量が無い |
| (c) 乗車も錨も無し | 2,296 体(うち 0 本 1,042) | 滞在のあるランは全部在圏・移動だけは落とす | 文どおり |

### 問題 5(軽・表記): README「390,067 呼・失敗 0・切断 0」と w17_gates.json `n_failed_agents` 1,814

- gates は `n_with_response` 390,067・`response_rate` 1.0(=呼の失敗 0 と整合)だが、`n_failed_agents` 1,814・`failed_agent_ids` 1,814 件(bad_time でパース落ち行 32,182 を持つ体と読める)。README に「パース落ち行を持つ体 1,814(0.46%)」の一言が無い。tools/w17 内に `failed_agent_ids` の定義を grep で見つけられず=意味は未確認。

### 問題 6(軽・表外): summary の「廃棄 11.271 t/日 (band 83.7-155.5) **NG**」

- run_cli_summary.txt の C4 後半行に NG があるが受入表 16 行の対象外(表の仕様どおり)。親の報告にも出てこない。判定するかは親判断。

### 参考(不一致ではない)

- summary の「計画実行: 昼夜比 09-03 **3.58**」と物差しの 5.88 は定義が違う(計画側 vs 5 エリア journal)。併記時は注意。

## 合成例の結果(域外居住者 home_out=True・`PlanBlocks.from_weekly(..., derive_rule=)`)

| 例 | 行の並び(分) | v1 | v2 | §2 追補との整合 |
|---|---|---|---|---|
| (a1) 乗車 3・錨あり | 就寝 自宅 0-400/移動 駅 400-440/乗車 440-500/勤務 職場* 500-720/乗車 720-760/食事 飲食店 760-840/乗車 840-880/買物 物販店 880-960/休憩 自宅 | [(400,440),(500,720),(760,840),(880,960)] | [(500,720),(880,960)] | 錨ラン=区間1→奇数側。区間2 の食事は落ち、区間3 の買物は採る=文どおり |
| (a2) 乗車 3・錨なし | 就寝/移動 駅 500-540/乗車/買物 600-720/乗車/娯楽 780-900/乗車/食事 960-1020/休憩 自宅 | [(500,540),(600,720),(780,900),(960,1020)] | [(600,720),(960,1020)] | 奇数側。最後の乗車の後の食事が在圏(問題 4(a)) |
| (a3) 乗車 4・錨が区間1と3 | 乗車/勤務* 440-700/乗車/食事 740-800/乗車/勤務* 840-1100/乗車/休憩 自宅 | [(440,700),(740,800),(840,1100)] | [(440,700),(840,1100)] | 文どおり |
| (b1) 錨が区間1(職場*)と区間2(宿泊施設) | 乗車/勤務* 440-1000/乗車/就寝 宿泊施設 1040-1440 | [(440,1000),(1040,1440)] | 同左 | 錨は常に採る=文どおり |
| (b2) 錨が区間0(学校)と区間2(職場*) | 勤務 学校 400-600/乗車/食事 640-700/乗車/勤務 職場* 740-1200/休憩 自宅 | [(400,600),(640,700),(740,1200)] | [(400,600),(740,1200)] | 最初の錨=区間0→偶数側。区間1 の食事は落ちる=文どおり |
| (b3) 錨が区間0(買物 cell≥0)と区間1(職場*) | 買物 物販店 cell7 400-480/乗車/勤務* 520-1000/乗車/食事 飲食店 1040-1100/休憩 自宅 | [(400,480),(520,1000),(1040,1100)] | 同左 | 最初の錨=区間0→偶数側→区間2 の帰宅側の食事が在圏(問題 4(b)) |
| (c1) 乗車も錨も無し・滞在あり | 移動 駅 500-540/買物 540-700/食事 700-760/移動 駅 760-800/休憩 自宅 | [(500,800)] | [(500,800)] | 全区間=文どおり(域内居住者なら [(0,1440)]) |
| (c2) 移動 駅 だけ | 移動 駅 500-540 | [(500,540)] | [] | 滞在なしランは落とす=文どおり |
| (c3) 域外行で割れた 2 ラン | 買物 500-600/休憩 域外 600-660/娯楽 660-800 | [(500,600),(660,800)] | 同左 | 「休憩 域外」は区切りでない=文どおり |
| (c4) 「移動 域外」×2 で挟む | 移動 域外/買物 540-700/移動 域外/食事 740-800 | [(540,700),(740,800)] | [(540,700)] | 移動・域外行が区切り=文どおり |

## 実行したコマンドと所要時間(合計 約 25 分・うち計算時間 約 2 分)

| 手順 | コマンド(要旨) | 所要 |
|---|---|---|
| HEAD/状態 | `git log -1`・`git status`・`git show --stat HEAD`・`git show --stat 334e8a5` | 数秒 |
| 受入表再実行 | `.venv/Scripts/python.exe tools/c7/c7_accept.py --summary …/run_cli_summary.txt --time-v …/run_time_v.txt --out-bytes 195139226 --manifest …/checkpoints.json --wc data/world/v2/wc_index.json --determinism …/t2a_1.json …/t2a_2.json --full …/replay_checkpoints.json --out layer2_tmp/accept` → `diff --strip-trailing-cr` | 1 s |
| checkpoint 突合 | Python(json 読み・4 点×5 ハッシュ・final・summary 16 桁・docs vs data/runs) | <1 s |
| pytest | `pytest tests/engine/test_presence_derive_v2.py tests/engine/test_presence_executor.py -q -o addopts=""`(2 回・--tb=short 版を `layer2_tmp/pytest_presence.txt` に保存) | 24 s + 22 s |
| 物差し ×3 | `tools/c7/presence_yardstick.py --journal data/runs/c7-day-3/occupancy.npz --summary …/run_summary_c7-day-3.txt` (a) after のみ (b) `--before-series docs/bench/c7/occupancy_series_c7-day-2.json --before-n-agents 390067` (c) `--before scratchpad/d66/occ_base.npz --before-summary …/base_summary.txt`(親の再現)→ `layer2_tmp/yk_*` | 各 ≤1 s |
| 多様性 | `tools/w17/diversity_yardstick.py --parquet data/world/v2/w17_schedule.parquet --world data/world/v2 --out layer2_tmp/div_r2` | 37 s |
| W17 分布+合成例 | `layer2_tmp/w17_blocks_and_synth.py`(出力 `.out`) | 2 s |
| 穴の規模 | `layer2_tmp/w17_holes.py`・`layer2_tmp/w17_noride.py` | 各 2 s |
| md5/照合 | `md5sum` W17 parquet/header/gates・`diff` header・README/ingest_r2.log/w17_gates.json 読み | 数秒 |

## 確かめられなかったこと(理由つき)

1. **サーバー側の実体**(tape の calls.parquet 194,949,218 B・blocks.parquet・T2-a の 2 ラン・T2-c 再生の実行)— ssh 禁止。成果物ファイルの突合のみ。S1 は依頼文の数値をそのまま使用。
2. **HOLD/SEAL** — holdout は開封禁止。未照合のまま(親の主張と同じ)。
3. **親が c7_accept.py に渡した --manifest の実体** — コマンド行が devlog/build-report に無い。checkpoints.json で表は再現でき、holdout_open を持たない限り結果は不変。
4. **第 1 回 W17 表での分布**(親の v1 [36/99,212/149,924/91,536]→v2 [298/282,273/56,122/7,394])— 第 1 回表がディスクに無い(w17v1_backup は v1 表)。本番(第 2 回)表の値は本書 3-2 に出した。
5. **WC-5 0.004056 / WC-6 0** — `data/world/v2/wc_index.json` の値をそのまま使用(世界ビルド成果物の再計算はしていない)。
6. **`n_failed_agents` 1,814 の定義** — tools/w17・src/shibuya/build の grep で該当語が見つからず、意味は推定(パース落ち行を持つ体)。
7. **d66/occ_base.npz(mock 5,000 の before)の生成 HEAD** — base_summary.txt の先頭 5 行(n=5000・呼 37,111・保存則 OK)以上は追っていない。
