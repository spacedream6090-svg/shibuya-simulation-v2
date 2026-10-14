# 第 2 期 2-4 版上げ 2 回目(vb24)の検収の記録

> 検収役(Opus 5.5)。実装は見ていない。対象は枝 `2-4/version-bump-2` の段の commit で、親が本体の HEAD `5f38e37` へ rebase した後の hash で書く: V1 `be108b7` → V2 `ec5bdb9` → V3 `ab4a0d0` → V4 `01d5cd4` → V5 `7a3531b` → V6 `7e5d33e` → V7 `a231ef9`(土台 `5f38e37`)。
> rebase の前の列(土台 `9f631b0`・V1 `cf13eb5` 〜 V7 `686b56c`)との差は `git range-diff` で確かめた。V4 だけが「!」(予算の宣言の 1 行の並び=本体の 2-3 の行の後に V4 の行)で、ほかの 6 段は「=」。木の差(`686b56c` → `a231ef9`)は `5f38e37` の文書 5 本(IMPLEMENTED・PENDING・STATUS・予算の宣言・計画)だけで、`src`・`tests`・`tools` は同じ。rebase の途中(数分)に作業木から読んだ結果は捨て、検収はすべて `a231ef9` の木(作業木=`a231ef9` と同じ・`git diff` 空)で行った。
> 世界資産は親が活性化した後に見た(`data/world/v2`=build_hash `6a7d34e8…`・退避先 `data/world/v2_pre_2-4`)。
> **封印の規律**: 封印の層と検証側の錨(`presence_validation_anchors_v0.json`・`hunger_energy_validation_anchors_v0.json`)の値は読んでいない。V6 は鍵の名・sha256・真偽だけで確かめた。`tests/c7` は回していない(試験のコードは読んだ=§5)。作業用の置き場は `_bc_review/`(終わりに消す)。head の写しには錨はエンジンが開く 3 本だけを写した。

## 判定

**条件つき受入**。動いた量(V1〜V4)と結果不変(V5・V6)は、1 構成を切替口で 1 段ずつ戻して全部の段で再現した。旧値も 25 欄とも再現した。V6 の分け方も鍵の集合と値の真偽で元と同じだった。
条件は 1 つある。**高 H1**(`tests/c7` の fixture を較正側だけにしたので、CI-1 で `tests/c7/test_presence_yardstick.py` が落ちる見込み)を push の前に直すこと。ほかの欠陥は中 1・低 8 で、記録と台帳の直しと親の判断で済む。

## 欠陥(重さ順)

| 番 | 重さ | 段・ファイル | 中身 | 直し方 |
|---|---|---|---|---|
| H1 | 高 | V6 `tests/c7/test_presence_yardstick.py` | fixture `anchors` が較正側 `presence_calib_anchors_v0.json`(錨 3 本=`core9_*`)だけを読む。ところが同じファイルの合成の世界の試験の少なくとも 6 本(216・238・256・270・286・368 行で呼ぶ・ほかに同じ fixture を使う 312・341 行の 2 本)は `yard.measures(pres, anchors, …)` を呼び、`tools/c7/presence_yardstick.py` の `measures` は `_distance`(`a["night_presence_estimate"]`・`a["pt_area_daytime_peak"]`)と `_wake_rows`(`a["wake_rate_tokyo_weekday"]`)を無条件に引く=検証側にしか無い鍵で `KeyError` になる(静的に読んだ・回していない)。これらの試験は `requires_data` も `slow` も付かず、CI-1(`.github/workflows/ci.yml` の `pytest -q -m "not gpu and not slow"`=`tests/c7` を外さない)で回る=**push すると CI-1 が赤になる見込み**(10-13b §0-4「CI-1 は常に緑」)。実装役は記録 §V6 と締め-4 の 7 で「落ちる見込み(未確かめ)」と書いている | 合成の値の代役を fixture に置く(較正側の 3 本+検証側の鍵の名だけを持つ作り物の錨=値は試験の中で作る)。こうすると検証側のファイルを開かずに `measures` の道を通せる。または錨の要る試験に理由つきの `skip` を付ける。どちらでも、push の前に CI-1 と同じ引数で `tests/c7/test_presence_yardstick.py` を回して緑を見る(回すのは親=検収役の規律の外) |
| M1 | 中 | V1 `vb24/tools/activate_vb24.py`・記録 §V1-2 | 退避先 `data/world/v2_pre_2-4/` は置き換えた 11 本と `MANIFEST.sha256`・`plan.json` だけを持つ(12 項目)。**エンジンの `--world` に渡せる前の資産ではない**。前の資産でランを回す道は `revert`(本体の v2 を書き戻す)しかない。検収では、本体の v2 の直下のファイル(W17 の jsonl を除く)の写しに退避の 11 本を重ね、足した 3 本を除いて作業用の置き場に組んだ(104 本)。`verify --live <その置き場> --want before` で build_hash `5ff1bacf…` と 14 本の sha256 が「同じ」になった | `activate_vb24.py` に、作業用の置き場へ前の資産を組んで確かめる口を足す(`materialize --out <dir>`=写しと `verify --want before`)。少なくとも記録 §V1-2 に組み方を 1 段書く。旧値の再現(前の資産+切替口 3 つ)をランで見る道がこれで残る |
| L1 | 低 | V4 記録 §0・§V4-1・予算の宣言・commit の文 | 39 万体の金と物の輪の合計「約 246.6 MB」は丸めた値の和(224.7+9.4+12.5)。バイトで足すと 224,678,592+12,482,144+9,361,608=**246,522,344 B=246.5 MB**(M8 の約 1.0% は変わらない) | 246.5 MB に直す |
| L2 | 低 | V2〜V4 の比べの JSON(`v2cell_vs_v1`・`v3legacy_vs_v2`・`v4off_vs_v3`・`v2fix_vs_v2`) | 切替口は環境変数で渡したが、side の `kw` は `{}` のままで、JSON にはラベル(`v2cell` ほか)しか残らない=JSON だけでは何を戻したかが分からない | 今後の byte-check の side に `SHIBUYA_*` の環境変数を書く欄を足す(10e の道具)。今回は記録 §V2-3・§V3-4・§V4-3 の文が正 |
| L3 | 低 | V6 の波及 | 消した錨のファイルを開く古い道具が 3 本残る: `docs/bench/analysis/wave2-2026-09-30/meal_bundle_measure.py`(266 行)・`docs/bench/analysis/energy-classical-2026-09-28/energy_measure.py`(43 行)・`classical_measure.py`(40 行)=回し直すと `FileNotFoundError`。`10e/byte_check_10e.py` の docstring の手順は錨を 3 本と書いたまま(V6 より後の head では 4 本=記録 §V6 の末尾にはある)。`docs/bench/instruments/anchor_gauge/calib_anchors_v0.json` の出どころの文は `presence_anchors_v0.json` を名指す | 古い道具は凍結の印か 2 本の読み口(`energy.load_anchors()`)へ。docstring と出どころの文は新しい名を併記する。記録 締め-4 の 5(名の変更の波及)に 3 本を足す |
| L4 | 低 | 記録の頭・§0・§V1-2 | 頭の「土台 HEAD `9f631b0`」は rebase の後は `5f38e37`(src は同じ)。§0 の「活性化の前なので…落ちる」と §V1-2 の「写すのは親」は、活性化の後の今は古い | 取り込みのときに、親の活性化(`verify` 同じ・build_hash `6a7d34e8…`)の 1 行と土台の hash を足す |
| L5 | 低 | 記録 §V3-3 | 席の探りの final(`89e1a968…`/`fe7f4ec7…`)は byte-check の w6_v3_default の V2/V3 の final と違うが、呼数(64,635・64,526)は同じ。探りの道具はテープなしで回す(`seat_probe_vb24.py` 78 行)=10d からの既知(テープの有無で final がずれる)と読めるが、記録に説明が無い | §V3-3 の表の下に 1 行(テープなしのラン=final は byte-check と違う・呼数は同じ) |
| L6 | 低 | 記録 締め-5 | V1 の「golden の 10 ファイル」は §V1-7(張り替えた 9 ファイル)と commit(golden 9 本+新しい 2 本)と食い違う | 9 に直す |
| L7 | 低 | つなぎの台帳 | 2-4 が終わっても `remove_at: "2-4"` の active の行が 9 本残る(記録 締め-4 の 2 の一覧と同じ=親の判断待ち)。ほかに 2-1 の行が 10 本残る(2-4 の前から=`BR-DOC-RESIDENT-CASH-ACCOUNT`・`HD-economy.*-1af925f4` ほか)。外す段が過ぎた行を見張る試験は無い | 親が外す段を改める。外す段が過ぎた active の行を数える試験を足すかを決める(本段の外) |
| L8 | 低 | V7 の commit | V6 の状態で回した 2-0 の計器の記録(`docs/bench/instruments/anchor_gauge/2026-10-14_vb24-V6/`)が V7 の commit に入る(記録 締め-3 に書いてある=段をまたぐ混入ではなく記録の置き場) | そのままでよい(親が段の並びを気にするなら V6 へ) |

## 1. 段ごとの commit の中身 ✓

- `git log --stat 5f38e37..a231ef9` の各段の変更は発注の段に収まる。前の段のコードに後の段の中身が入っていない: V1・V2 の木に `seat_release` の語は無い。V1 の木に近接の `DEFAULT_MODE` は無い。V3 の木に経済の `DEFAULT_ARM` は無い。V5 の木に分けた錨の名は無い。
- 記録 締め-5「触った共有ファイル」と commit の一覧は合う(V1: build の 4 本・c8 の 5 本・設計書・試験・2-0 の計器 V1/V2: `cli`・`proximity`・`renderer`・`state_ledger`・`systems` の 5 本/V3: `seat_release`(新)・`resolve`・`manifest_sections`・`systems` の 6 本/V4: 経済 2 本・`economy_stage2`・`resolve`・`systems` 2 本・台帳・予算の宣言/V5: `manifest_sections`・`experiment/branch`/V6: 錨 2 本 → 4 本・`energy`・道具 5 本・試験 3 本)。食い違いは L6 の数え方だけ。
- 後から見つけた直しは、それが属する段の commit に入っている(V1 のつなぎの台帳の試験・V3 の系の表の `reads`)。
- 試験の定数は段ごとにその段のコードと合う。`CONFIG_PATHS_SHA256` は V1・V2 で `415620b0…`、V3・V4 で `ac930362…`、V5 以降で `417f0818…`。
- 段をまたぐ置き場は L8 の 1 件だけで、記録に書いてある。
- 変えたファイル 113 本(足した/変えた 111 本+消した 2 本)のうち、足した/変えた 111 本の commit の中身に CR は 0 本。秘密の走査(`tools/scan_secrets.py`・同じ 111 本)は CLEAN。

## 2. V1 資産 ✓

- `activate_vb24.py verify --live data/world/v2 --want after` → 「同じ」(終了コード 0)。`--live data/world/v2_stage_2-4 --want after` も「同じ」。build_hash は v2・`v2_stage_2-4` とも `6a7d34e858e07210…`。
- 道具の `verify` は動いた 14 本と build_hash しか見ないので、直下の全部も独立に比べた。v2 と `v2_stage_2-4` の比べる対象(W17 の jsonl を除く直下+`acceptance/`)は 107 本ずつで、名の集合も sha256 も全部同じ。
- W12: `w12_timetables.parquet`(`7ef7ab90…`)・`w12_timetable_versions.json`(`4ee484eb…`)・`w12_external_nodes.parquet`・`w12_generation_weights.parquet`・`wc_index.json`(`a05f5438…`)は 2-3b の資産(`v2_stage_2-3b`)と sha256 が同じ。
- W9: 影 8 日(07-13〜07-19・07-28)はどれも 12,842,624 B で、2-3 の資産(`v2_stage_2-3`)と sha256 が同じ(07-18 `143400d4…`・07-19 `82f5e4f3…`)。
- 前の資産: §M1 の組み方で build_hash `5ff1bacf7fd9c773…` と 14 本の「前」の sha256 が「同じ」。組んだ資産の `w12_timetables.parquet` と `wc_index.json` は 2-3 の資産(W12 は前のまま)と同じ。
- W9 のゲート(案 A・13,000,000 B/日)の根拠: `v1_w9_shapes.json` は 8 日とも `file_bytes` 12,842,624=288 面 × 44,592 B(=⌈356,732/8⌉)+npy の見出し 128 B。W9 の見出しは `points` 356,732、ゲート `shadow_bytes_per_day_le_budget` は値 12,842,624・期待 13,000,000・PASS。余白は 1.2%。B 案(昼の面だけ 7.4〜7.6 MB・zlib 3.0 MB)の数も JSON と記録で合う。案 A は仮採用で、親の判断待ち(記録 締め-4 の 1)。宣言の置き場は予算の宣言ではなく設計書 D-W10(`v2-world-data-build-spec.md` に改訂の行)。

## 3. 動いた量の独立の再現 ✓

w6_v3_default(5,000 体・seed 1・1 日・テープつき)を 10e の道具 `byte_check_10e.py one` で回した(作業木の src は `PYTHONPATH`、切替口は環境変数=CLI の `--proximity` ほかと同じ `set_arm` の口、資産は `--world`)。

| ラン | src | 資産 | 切替口 | final / 呼数 | 記録の段 |
|---|---|---|---|---|---|
| A | 本体 HEAD `5f38e37` の写し | 前の資産(§M1 で組んだ・`5ff1bacf…`) | — | `5f7ae9ff24005314` / 65,597 | base と同じ |
| E | 作業木 | `data/world/v2`(`6a7d34e8…`) | proximity cell・seat legacy・economy off | `4bcca9f0216362bb` / 65,400 | V1 と同じ |
| D | 作業木 | 同上 | seat legacy・economy off | `7857ecb16b9665cd` / 64,635 | V2 と同じ |
| C | 作業木 | 同上 | economy off | `f6488d4d5eadf5ca` / 64,526 | V3 と同じ |
| B | 作業木 | 同上 | 既定 | `b8eadcb51e8705e7` / 64,528 | V4(=V5・V6)と同じ |

- 段ごとの呼数の差(この構成): V1 −197・V2 −765・V3 −109・V4 +2。記録の各段の表の w6_v3_default の行と同じ。
- 実装役の side(作業用の置き場 `_bc/side_base`・`side_v1`〜`side_v4`・`side_v6`)と、この構成の 25 欄を比べた。A=base・E=V1・D=V2・C=V3・B=V4・B=V6 で、**6 組とも 25 欄が全部同じ**。実装役は `v2_stage_2-4` で回し、検収役は活性化した `data/world/v2` で回した=活性化した資産は組んだ資産と挙動も同じ。
- E と D の差は 15 欄で、記録 §V2-2 の w6_v3_default の「15/25」と同じ。
- 19 構成の合計(+1,088・−10,046・−2,266・−40)は、記録の比べの JSON の `calls_delta` を足し直して同じ。final が動いた構成の数(19・18・15・19)と、V5・V6 の動いた欄 0 も同じ。締め-1 の表(4 構成 × 7 段)は、比べの JSON を段の順につないで作り直して全部同じ(つなぎの切れ目なし)。
- V4 の 2 日(`v4_two_day.json`): 7 本とも `conserved` は真・溢れ 0。行/体と世帯の現金の 1 体の増減は記録 §V4-4 の表と同じ。再開の JSON 4 本は `same_final` と `checkpoints_after_boundary_same` が真。

## 4. 旧値の再現 ✓

- ラン F=作業木の src+切替口 3 つを全部旧値(`SHIBUYA_PROXIMITY=cell`・`SHIBUYA_SEAT_RELEASE=legacy`・`SHIBUYA_ECONOMY_STAGE2=off`)+前の資産(§M1)→ `5f7ae9ff24005314` / 65,597。
- A(本体 HEAD の既定+前の資産)と `compare` で比べ、**25 欄とも同じ**(動いた欄 0・`frozen_sources` を含む)。

## 5. V6 の分け方 ✓(試験は H1)

- **鍵の集合の等式**(`git show 9f631b0:` の元と、今の 2 本。値は画面に出していない):
  - 在圏: 元の上の段の鍵 {`anchors`・`created`・`purpose`・`rules`・`schema`・`version`}=較正側 ∪ 検証側 −{`split_from`}=**真**。`anchors` の子は元 9=較正側 3+検証側 6・重なり 0。2 本を合わせると元の `anchors` と値まで同じ=真。較正側の錨の名は `core9_day_night_ratio`・`core9_daytime_population`・`core9_night_population`。`rules` は検証側だけにあり、元と同じ。`purpose` は検証側が元と同じで、較正側は道具が書いた文。
  - 空腹: 元の上の段の鍵 13 本=構築側 ∪ 検証側 −{`split_from`}=**真**。構築側は `dri2025`・`nhns_t14_weight`・`nhns_t13_meal_kcal`・`mets_2012`。検証側は `nhns_t10_breakfast_skip`・`ssb2021_t18_1_weekday`・`ssb2021_meal_rate_15min`・`derived`。見出し 4 本は両方にあり、どちらも元と同じ。`sources` は 4/2 に分かれ(重なり 0)、合わせると元と同じ。各錨の値も、置かれた側で元と同じ(真偽だけ)。
  - sha256(先頭 16): 元の在圏 `f07f72457bd42641` → 較正側 `8c52d3ead468fac3`・検証側 `e516dc7f3d124fcf`。元の空腹 `282a79cc868a3485` → 構築側 `7191bbfe335f0298`・検証側 `7646f372c7cb658e`。
- `energy.py`: `load_anchors()` は 2 本を 1 つの辞書に戻す。元の 1 本の辞書と比べると**同じ=真**で、鍵の並びだけが違う(md5 は 2 本のバイト列をつないだ値に変わる=manifest の `energy.anchors_md5` が動くことは記録どおり)。読み口は検証側のファイルを読む形のまま(docstring と記録 §V6 に「PENDING §1-1 の判断待ち」と書いてある)。
- `tools/instruments/read_guard.py`: 計器の段で落とす語(`GAUGE_EXTRA_DENY_TOKENS`)に `presence_validation_anchors`・`hunger_energy_validation_anchors` を足した。前の 2 語は残る。語は部分文字列で照らすので、較正側 `presence_calib_anchors` と構築側 `hunger_energy_build_anchors` は落ちない(前の 2 語に当たらない)。構築側は 2-4 の前は混在の 1 本ごと落ちていたので、計器から読めるようになったのは構築側の値だけ(DRI・NHNS 第 13/14 表・METs=構築の入力)。
- `tests/c7` の fixture は較正側だけを読む形(読んだ・回していない)。ただし H1 のとおり、その fixture で回る試験の少なくとも 6 本が検証側の鍵を引く。
- **新しい露出ではない**: 元の 2 本は V6 で git の木から消えたが、履歴(`9f631b0` ほか)には残る。分けた 2 本の値は元の値の写しで、値は前から git にある=分けたことで新しく露出した値は無い。

## 6. V5 ✓

- `manifest_sections.py` を段ごとに git から読んで `config_paths()` を数え直した。base・V1・V2 は 217 本で `415620b0…`。V2 → V3 で `leave_effects.seat_release` が 1 本増えて 218 本・`ac930362…`(V3 の切替口の設定)。V4 → V5 は `group_norms.cost` が消えて `group_norms.cost.note` が増えただけで `417f0818…`。V5 → V7 は変化なし。**`CONFIG_PATHS_SHA256` の動きはこの移動だけで説明できる**。
- 結果は不変: `v5_vs_v4.json` は 19 構成とも動いた欄が 0。
- `experiment/branch.py` の `RESUME_DERIVED` は注だけの変更(2-4 より前の基準との比べのために残す)。

## 7. 試験 ✓(`tests/c7` は H1)

作業木(=`a231ef9`)・活性化した資産・`PYTHONPATH` に作業木の `src`・`PYTHONDONTWRITEBYTECODE=1`(作業木に書かない)。

| 何を | 引数 | 結果 | 時間 |
|---|---|---|---|
| 発注の 21 の場所(`tests/economy`・`tests/engine/{proximity,systems,events,time,bridging,experiment,multiday}`・`tests/build_{field,vis,audit}`・`tests/c8`・`test_activation_2_4.py`・`test_seat_release_2_4.py`・`test_resume_10d.py`・`test_state_ledger_10b.py`・`test_state_checks_10f.py`・`test_env_and_sections_10f.py`・`tests/perception`・`tests/llm`・`tests/test_cli.py`) | `-n 2 --dist loadfile -m "not slow"` | **2,093 passed・1 xfailed・failed 0**(data が無くて飛ばした試験 0) | 23 分 49 秒 |
| `tests/economy` の slow | `-n 2 --dist loadfile -m slow` | **26 passed** | 12 分 47 秒 |
| 層の契約 `lint-imports --no-cache` | — | **5 kept・0 broken**(229 ファイル) | — |

- 活性化の試験 `tests/engine/test_activation_2_4.py` は、親が写した後の今の資産で通る(記録 §0 の「写すまで落ちる」は解けた)。
- 警告は 1 件で、W9 の影の窓の外の日(07-20)に近い日(07-19)の影を読んだ印(`BR-SHADOW-NEAREST-DAY`=宣言どおり)。
- 回した後も作業木に変化は無い(`git status` は検収の記録と作業用の置き場だけ・`__pycache__` の数も同じ)。
- 時間は、別の python のプロセス(4 本並列)と重なった区間がある=参考。

## 8. 記録と台帳 ✓(低 L1・L4・L6・L7)

- 絶対パス・ホスト名・個人名: 足した/変えた 111 本を、ドライブの文字・利用者のフォルダ・作業木の名・机上のフォルダの語・個人の名で検索して 0 件。
- つなぎの台帳(段ごとに git から数えた): base〜V3 は 347 行(active 338・removed 9)。V4 で `DOC-ec21-ring-coefficient` と `DOC-ec21-revenue-tax-inclusive` が removed になり、`DOC-ec21-uncaused-rows-arm-off` の `remove_at` が 2-4 → 4-1 に変わった。V4〜V7 は active 336・removed 11。記録 §V4-1(active 338 → 336・2 行を removed・1 行を狭めて 4-1)と合う。ほかの段では台帳の行は動かない。宣言と行の 1 対 1 は `tests/engine/bridging` が見る(§7)。`remove_at: "2-4"` で残る active の 9 行は、記録 締め-4 の 2 の一覧と同じ(L7)。
- 予算の宣言の V4 の改訂: 5,000 × 16.0=80,000 行 × 36 B=2.88 MB。390,067 × 16.0=6,241,072 行 × 36 B=224,678,592 B=224.7 MB。係数 6.5 は 2,535,436 行=91.3 MB で、比は 2.46(約 2.5 倍)。前の合計 113.1 MB(=60.9+30.4+12.5+9.4)と後の合計 246.5 MB(L1)。M8 24 GB の 1.03%。2-1 の実測(0 日目 8.824・2 日の和 14.226)に対して 16.0 は 1.1 倍以上・1.5 倍以上で、2-4 の 2 日(8.591+5.418=14.009)も 16.0 未満・溢れ 0。数は合う(246.6 だけ L1)。
- 切替口の一覧(§V7): 残す 5(`--proximity cell`・`--seat-release legacy`・`--economy-stage2 off` と `--economy-stage2-parts`・`USE_ODPT_CHALLENGE`・`--proximity-d`)と消す候補 10 行がある。本段で既定を変えた 3 つは残す側にあり、旧値の再現の確かめの節を指す。CLI の `--proximity`・`--seat-release`・`--economy-stage2` は環境変数と同じ `set_arm` を呼ぶ(`cli.py` 1440〜1453 行)。

## 親に確かめてほしいこと

1. **H1**: push の前に `tests/c7/test_presence_yardstick.py` の fixture を直し、CI-1 と同じ引数で緑を見る(検収役は `tests/c7` を回さない)。
2. 取り込みのとき、記録に親の活性化の 1 行(`verify` 同じ・build_hash `6a7d34e8…`・退避先 `v2_pre_2-4` は 11 本の退避で前の資産そのものではない=M1)と、土台の hash `5f38e37` を足す(L4)。
3. W9 のゲートの案 A(仮採用)を決め、PENDING §2 の「W9 の 10 MB/日のゲートは本体でも FAIL=2-4」の行を片付ける。
4. つなぎの台帳で外す段が 2-4 のまま残る 9 行の外す段(L7・記録 締め-4 の 2)。
5. 実装役の作業用の置き場 `_bc/tree/data/` の下にはつなぎ(junction)が並ぶ。`_bc` を消すときは、つなぎを先に外す。検収役の `_bc_review/` につなぎは無い(作業木の `data` を通して読んだ)。
