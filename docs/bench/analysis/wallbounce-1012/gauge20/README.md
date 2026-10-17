# 第 2 期 2-0 較正側の錨の計器(記録)

- 段: 計画 [v2-implementation-plan-2026-10-12](../../../../design/v2-implementation-plan-2026-10-12.md) の 2-0(回答 10-13b §1 1-8=仕分け 3-8)。
- 設計の正: 答申 [R-115](../../../../research/v2-r115-calibration-anchors-inventory-for-2-0.md) の §2〜§4。
- 実装役: Opus 5.5(2026-10-14)。commit はしていない(親が検収して取り込む)。
- **エンジンは変えていない**。src の差は 0 行で、`git diff --stat -- src` は空。計器は記録を読んで計算するだけの道具である。
- **合否は書かない**。〔写〕の錨は構築の入力の写しなので、差は形だけを見る。「現実に近づいた」と書けるのは holdout の開封(S1)の後だけである。

## §0 要旨

1. 常設の計器 `tools/instruments/anchor_gauge.py` を作った。2 つの段に分かれる。
   - `record` の段: ランを回し、体の journal を取る。
   - `gauge` の段: journal と構築側のファイルだけを読み、4 つの量を出す。
2. gauge の段で計器が読むファイルは、許可の一覧(`tools/instruments/read_guard.py`)で縛った。一覧の外と、封印・検証側・〔灰〕の語を含む道筋は、開く前に落ちる。Python の `open` は監査フックでも見張る。record の段でエンジンが開くファイルは、道筋だけを控えて記録に残す(§3)。
3. 最初の 1 回は HEAD `2bc7a4b` で、mock と古典の 2 腕を回した(5,000 体・seed 1・1 日・計画実行層 on)。置き場は [2026-10-14_2bc7a4b/anchor_gauge.md](../../../instruments/anchor_gauge/2026-10-14_2bc7a4b/anchor_gauge.md)(JSON も同じ場所)。
4. 記録器を付けても、final と呼数は付けないランと同じだった。mock は `5f7ae9ff24005314` と 65,597 呼で、1-8 の byte-check の既定 v3 と同じ値。古典は `202a05a22c5bd8e1` と 93,460 呼。
5. 錨 1(3-4)の勤務窓を計器の中で引き直した。W17 v2 が段 2 のプロンプトに書いた窓と、標本の対象 2,332 体の全員で一致した。
6. PT c-2 の錨(3-1・3-3・3-4)と、3-3 の錨 4〔灰〕は、器だけを置いた空の列である。

## §1 作ったもの

| ファイル | 中身 |
|---|---|
| `tools/instruments/anchor_gauge.py`(新規) | 計器。部分コマンドは `record`(1 腕の journal)・`gauge`(4 つの量)・`run`(2 腕を記録して計器を回す=版上げごとの記録)・`compare`(前の版との差の表) |
| `tools/instruments/read_guard.py`(新規) | 許可の一覧と監査フック(`ReadGuard`)。封印の層だけを落とす `sealed_only()` はランを包むのに使う |
| `tests/tools/test_anchor_gauge.py`(新規) | 試験 19 本(slow 1・実データ 2) |
| `docs/bench/instruments/anchor_gauge/calib_anchors_v0.json`(新規) | 中核 9 町丁目の昼夜間人口比(〔非〕)。`presence_anchors_v0.json` の core9_* 3 行を写した(後述) |
| `docs/bench/instruments/anchor_gauge/preregistration_v1_4_draft.md`(新規) | 事前登録 v1.4 の定義の草案(計器の式の形・holdout は開けない) |
| `docs/bench/instruments/anchor_gauge/2026-10-14_2bc7a4b/`(新規) | 最初の 1 回の `anchor_gauge.json`・`anchor_gauge.md` |
| 本書 | 記録 |

**共有のファイルは触っていない**: `engine/systems/table.py`・状態台帳・凍結の表・`cli.py`・manifest の末尾・`docs/design/*.md`・PENDING・STATUS・台帳。

**記録の口**(R-115 §3-0 の (b) と (c))について。体の journal は `tools/c7/attr_arms.AgentCellRecorder` で取る。これは `engine.resolve.apply` を包み、刻みごとに cell と transit_state を控える。このほかに、ランの関数を 2 つ包んで参照を控える。

- `PlanExecutor.__init__`
- `engine.run._resolve_population`

どちらも戻り値は変えない。控えた参照から、次の 4 つを journal(`anchor_journal_<腕>.npz`)に足す。

- 計画上のセル(刻み × 体)
- 計画の到着(ARRIVE の予定)
- W17 の勤務の行の始まり
- 母集団の 10 列

ランの間は `ReadGuard.sealed_only()` を載せた。封印の層を開いたら、そこでランが落ちる。

## §2 4 つの量の式(R-115 §3 からの差分)

共通の取り決めは次のとおり。定義の全文は v1.4 の草案にある。

- 母集団は P′ = age ≥ 20 かつ is_foreign でない(本則・仮採用)。
- 1 日単位の 30 分は**合計**で数える。連続は腕にした。
- 時間帯別は θ = 1 分を既定にし、30 分を腕にした。
- 時刻は 5〜28 時で数え、24〜28 時は同じ日の 0〜4 時で代える。
- 拡大係数 ω_k = N_k / n_k を掛けて W16 の規模に戻す。値は標本で、種別 0〜3・5〜7 が 84〜94、指令 4 が 1.0、乗務 8 が 1.76。

| 量 | R-115 §3 の式 | 計器で決めた所(差分) |
|---|---|---|
| 3-1 ピーク時刻 | N_a(h) の argmax と順 | 列は 5 エリア・5 エリア計(どれかのエリア)・舞台全体。腕は 合計/連続 × θ 1/30 と、正時の標本(v1.3)。母集団の腕は P と全員 |
| 3-1 錨 1〔写〕計画 | P_a(h)=ブロックの中の体 | 計画上のセルは行の target_cell で決める。負の行は 職場 → work_cell・学校 → school_cell・自宅 → home_cell で補う。補えない行は「舞台の中・セル不明」で、舞台全体には数え、エリアには数えない。**数え方は R-115 の「正時の標本」と違う**: 計器は計画のセルにもランと同じ v1.4 の数え方(1 日の合計 30 分・時間帯に θ 分)を当てた(ランとの差を数え方の違いで汚さないため)。計画の正時の列は出していない(検収 L3=宣言) |
| 3-1 錨 2〔部〕W12 | N̂(h)=R+I·Σα−O·Σβ | α は W12 の重みの時刻の周辺(全ノード)。β は time_dist_12 の乗車の**帰宅**(「帰宅中心」の字どおり)で、腕は合計。R は W16 の居住者(P′)で、I と O は W12 の 1 日の流入と流出の和。値は時間帯の終わりの在庫。舞台全体の流量なので、5 エリア計と舞台全体の列にだけ並べる |
| 3-2 V/Res・W/Res | 1 日単位の在圏を属性で分ける | 計はエリアの数の和。訪日(is_foreign かつ 20 歳以上)は別の列。kind の写像は継続の列 |
| 3-2 錨 1〔写〕W16 | kind の写像の体数 | kind の写像は舞台全体(P′・P・全員)。area の写像は、エリアごとの W/Res だけを出す(来街者は W16 の体数から数えられない) |
| 3-2 錨 2〔写〕計画 | 計画の在圏の比 | 計画の来街の行は target_cell を持たない。来街の種別でセル不明が 99% 以上のときは、計画の V を**空**にする(0 とは書かない) |
| 3-2 錨 3〔非〕中核 9 | chome_key で寄せた腕 | セル → 町丁目は、W16 の居住者の chome_key の多数決で決める。居住者の居ないセルは、最も近い格子の町丁目にした(GL 134 枚=1.34 km² で、原典は 1.39 km²)。W16 の静的な比は「夜=居住者・昼=夜−流出+流入(全年齢)」。ランと計画の比は「夜=中核 9 の居住者(ω)・昼=居住者か勤務・通学先が中核 9 の体で、10〜16 時に 30 分以上居た体(ω)」 |
| 3-3 到着の波 | transit_state 域外 → 舞台 × direction_node | 到着は transit_state が 1・2 → 0 に変わった刻み。0 刻み目は数えない。母集団は全員(W12 の流量に年齢の軸が無い)。方面の無い体は「none」の行。計画の側は ARRIVE の予定 × direction_node |
| 3-3 錨 1〔写〕・錨 2〔部〕 | 線の割合・時刻の形 | 割合は W12 の daily_inflow から出す。W12 の重みの和と最大差 0 で一致した。形は W12 の重みのノード × 時刻 |
| 3-4 始業 | work_cell に 30 分以上続けて居た最初の区間の始まり | 対象は kind 0・2・P′・work_cell ≥ 0 かつ work_cell ≠ home_cell(自宅で従業は除く)。0 時から続く区間は前日の続きとして除いた。15 分の在席の率の立ち上がり(最大の 50%)も出す |
| 3-4 錨 1〔写〕 | 第 31 表+arrival_lead(W17 v2 の作り方) | `trial.draw_windows` を対象の体に当てた。素材はプールの雇用形態・arrival_lead_min・職業・学校段階・曜日。duty_activity は `w17_schedule.build_facts` の分岐の kind 0・2 に効く部分を当てた。欠勤は本番と同じく曜日ごとに引き、月曜(d0)に働く体だけを残す |
| 3-4 錨 2〔写〕 | W17 v2 の勤務ブロックの開始 | 計画の日の行のうち、最初の「勤務」の行の始まり(0 時から続く行は除く) |
| 3-4 錨 3〔部〕 | 第 8-1 表の朝の立ち上がり | 平日・関東大都市圏・有業者・年齢総数の「仕事」(05)を、男女の推定人口で混ぜた。15 分の枠の 0 番は 0:00 で、エンジンの `minute // 15` と同じ読み。12:00 の昼の谷の位置でも確かめた。閾値 50% は expedient |

## §3 読んだファイル

### gauge の段(全部が構築側)

計器の段(`gauge`)が読んだのは次だけである。どれも R-115 §2 の〔写〕〔部〕〔非〕に当たる。各ファイルの md5 は `anchor_gauge.md` の末尾に載せた。

| 役割 | 道筋 | R-115 の印 |
|---|---|---|
| W16・W16_chome | `data/world/v2/w16_population.parquet`・`w16_chome.parquet` | 〔写〕 |
| W2_cells | `data/world/v2/w2_cells.parquet` | 写像の入力 |
| W12_nodes・W12_weights | `data/world/v2/w12_external_nodes.parquet`・`w12_generation_weights.parquet` | 〔写〕 |
| area_axes | `tools/c7/area_axes_v0.json` | expedient |
| time_dist_12 | `data/realworld/transport_census/time_dist_12.json` | 〔部〕 |
| commute_r3 | `docs/bench/anchors/commute_time_dist_r3.json`(第 31/36 表) | 〔写〕 |
| ssb_8_1 | `docs/bench/anchors/ssb2021_activity_prior_v0.json`(第 8-1〜8-3 表・食事 03 を除く) | 〔部〕 |
| calib_anchors | `docs/bench/instruments/anchor_gauge/calib_anchors_v0.json` | 〔非〕 |
| pool | `data/persona_pool_v2/L1〜L5/part-*.jsonl`(必要な行だけ json.loads・md5 はファイル全体) | 〔写〕(W16/W17 の素材) |
| journal | `anchor_journal_mock.npz`・`anchor_journal_classical.npz`(作業用の場所・名だけを記録) | ランの記録 |

**落とす語**(`read_guard.py`)は 2 段に分けた。

- 封印・現実の生の取得・PT の検証側(ランの間も落とす): `kddi`・`jinryu`・`boundary_counts`・`realworld_live`・`/holdout/`・`holdout_compare`・`calib/pt2018`・`pt6_c-2`・`pt6_b-4`・`pt6_c-3`・`pt6_c-4`
- 計器の段で足すもの(検証側と〔灰〕): `diversity_anchors`(第 30 表由来)・`presence_anchors`(〔灰〕と〔検〕が混ざる)・`hunger_energy_anchors`・`calib/hunger`(第 4-1 表など)・`000032224420`(第 30 表)・`research_cache/r99`(第 14・15 表)・`line_capacity_12`・`transfer_12`・`station_od13_13`・`station_flow_12`(〔灰〕の欄を持つ)

守る根は `data/`・`docs/`・世界資産の置き場・プールの置き場で、この下は一覧の外を開けない。

### record の段でエンジンが開いたファイル(検収 M1)

record の段は、エンジン(`cli.run`)が前から読む入力を開く。計器は、ランの間に Python の `open` が `data/`・`docs/`・`tools/`・世界資産の置き場の下で開いた道筋を監査フックで控え、journal の meta(`record_opened_files`)と版ごとの `anchor_gauge.md` の末尾に残す(値は書かない・計器はその値を使わない)。最初の 1 回では **20 本**(mock 19 本・classical 20 本)だった。

| 道筋 | 腕 | 〔検〕〔灰〕との混ざり |
|---|---|---|
| `data/calendar/syukujitsu.csv` | 両方 | — |
| `data/realworld/osm/street_features_overpass_20260907.json` | 両方 | — |
| `data/world/v2/build_manifest.json` | 両方 | — |
| `data/world/v2/w10_noise_stage_day.npy`・`w10_noise_stage_night.npy`・`w10_street_points.parquet` | 両方 | — |
| `data/world/v2/w12_external_nodes.parquet`・`w12_timetables.parquet` | 両方 | — |
| `data/world/v2/w13_weather_days.parquet`・`w13_weather_hourly.parquet` | 両方 | — |
| `data/world/v2/w14_signage.parquet`・`w15_cell_static.parquet` | 両方 | — |
| `data/world/v2/w3_cell_dist.npy`・`w3_next_hop.npy`・`w9_shadow_2026-07-13.npy` | 両方 | — |
| `docs/bench/anchors/hunger_energy_anchors_v0.json` | 両方 | **混ざる**: 第 4-1・7-1・18-1 表の「検証にだけ使う」行が同じファイルにある(K6 (i))。エンジンの空腹のモデルが前から読む入力。計器の段では落とす語 `hunger_energy_anchors` |
| `docs/bench/anchors/ssb2021_activity_prior_v0.json` | classical | — (〔部〕・食事 03 は入っていない) |
| `docs/design/bridging-ledger.json`・`rules-table.json`・`v2-budget-declaration.md` | 両方 | — |

- 封印の層(`kddi`・`jinryu`・`boundary_counts`・`realworld_live`・PT の検証側)は 1 本も無い。ランは `sealed_only` の守りの中で最後まで走った(開こうとしたら落ちる)。
- pyarrow の読みは監査に出ない。表の parquet は Python の `open` でも開かれたもので、pyarrow だけで読んだ parquet はこの表に載らない。

### 計器の外で 1 回だけ読んだもの

道具は読まない。次の 3 つである。

- `presence_anchors_v0.json` の 1〜36 行目。中身は見出しと core9_* の 3 行で、`calib_anchors_v0.json` へ写すために読んだ。36 行目で次の項の名(`pt_area_daytime_peak`)が目に入ったが、値は見ていない。
- 錨 1 の確かめに、`data/world/v2/w17v2/w17v2_stage2_prompts.jsonl` の対象の体の行を読んだ(W17 v2 の構築の入力)。
- `data/` の直下のディレクトリの名の一覧を見た。封印の層の中は開いていない。

## §4 最初の 1 回(HEAD `2bc7a4b`・5,000 体・seed 1・1 日)

全表は [anchor_gauge.md](../../../instruments/anchor_gauge/2026-10-14_2bc7a4b/anchor_gauge.md) にある。差は「ラン − 錨」の形だけを見たもので、合否はない。

| 腕 | final | 呼数 | bridges_count | rules_version |
|---|---|---|---|---|
| mock | `5f7ae9ff24005314` | 65,597 | 286 | `e26d43b4207b5301` |
| classical | `202a05a22c5bd8e1` | 93,460 | 286 | `e26d43b4207b5301` |

### 3-1 在圏のピーク時刻(合計・θ 1 分・P′)

| 列 | mock | classical | 錨 1〔写〕計画 | 錨 2〔部〕W12(β=帰宅) |
|---|---|---|---|---|
| 中心 | 9 | 9 | 11 | — |
| 北西 | 12 | 10 | 11 | — |
| 北東 | 9 | 9 | 11 | — |
| 南東 | 9 | 10 | 14 | — |
| 南西 | 12 | 12 | 12 | — |
| 5 エリア計 | 10 | 10 | 11 | 13 |
| 舞台全体 | 10 | 12 | 12 | 13(腕 β=合計 14) |

- ピークの順は次のとおり(早い順。左が早い)。
  - mock: 中心 → 北東 → 南東 → 北西 → 南西
  - classical: 中心 → 北東 → 北西 → 南東 → 南西
  - 計画: 中心 → 北西 → 北東 → 南西 → 南東
- 時刻の形の JSD(底 2)は、ラン対計画が 0.0002〜0.075、ラン対 W12 が 0.022〜0.031。
- 計画では、舞台の中に居るがセルが分からない分が 34.8% あった。内訳は来街の種別が 100%、それ以外が 24.0%。計画のエリア別の在圏は来街者を含まない(§6 の 4)。

### 3-2 来街者/居住者の比(5 エリアの和・area の写像)

| | mock | classical | 錨 2〔写〕計画 | 錨 1〔写〕W16 |
|---|---|---|---|---|
| V/Res | 34.9 | 30.0 | 空(セル不明) | kind の写像・舞台全体: P′ 2.20・P 2.33 |
| W/Res | 9.70 | 16.05 | 16.23 | area の写像 16.4・kind の写像 5.56 |
| 来街/勤務 | 3.60 | 1.87 | — | フロア: PT 2018 0.16〜0.27 対 KDDI 1.66(合否にしない) |

- 中心エリアの居住者は標本で 2 体しかいない。エリア別の比は件数と並べて読む。
- 錨 3〔非〕中核 9 町丁目の昼夜間人口比は 14.8(都 第 11 表)。これに対する値は次のとおり。
  - W16 の静的な比: 23.37(夜 8,524・昼 199,219)。R-109 が書いた「W16 の勤務+通学は国勢調査の推しの 1.3〜1.6 倍」と同じ向きのずれである。
  - ランの比: mock 18.57・classical 21.41(居住者 n=100)
  - 計画の比: 21.21

### 3-3 駅ごとの到着の波(ω・全員)

- 線の割合: ランと錨 1〔写〕(W12 の daily_inflow)の差は、10 ノードとも ±0.011 以内だった(mock の最大は徒歩ゲートの −0.010、classical も同じ)。
- ピーク: ランは 7〜9 時、錨 2〔部〕は鉄道 8 線とも 8 時で、徒歩ゲートは 10 時。8 線の形が同じなのは R-115 §5 主張 2 のとおり。
- 形の JSD: mock 0.057〜0.116、classical 0.073〜0.247。どちらも最大は徒歩ゲート。
- 到着の延べ数: mock 8,009、classical 5,604、計画の ARRIVE 5,687。mock は出入りが多い。

### 3-4 勤務の始業の分布(kind 0・2・対象 2,346 体)

| 列 | n | 平均 | p50 | 最頻の 15 分 | :00/:30 の率 | 立ち上がり(50%) |
|---|---|---|---|---|---|---|
| mock ラン | 852 | 13:03 | 12:06 | 9:30 | 0.045 | 9:30 |
| classical ラン | 2,252 | 10:05 | 9:29 | 8:45 | 0.032 | 9:15 |
| 錨 1〔写〕第 31 表+lead | 1,939 | 9:04 | 8:37 | 8:30 | 0.029 | — |
| 錨 2〔写〕W17 v2 の勤務の行 | 2,336 | 9:15 | 8:40 | 8:30 | 0.046 | 8:30(計画のセルの在席) |
| 錨 3〔部〕第 8-1 表 仕事 | — | — | — | — | — | 8:30 |

- 差(ラン − 錨 1)は、classical で平均 +61 分・p50 +52 分。mock は平均 +240 分で、mock では始まりが取れた体が 36%(852/2,346)しかない。
- mock の体は、職場のセルに 30 分続けて居ることが少ない。classical では 96% の体で始まりが取れたので、計器の欠陥ではない(記録)。

## §5 材料待ちの列

| 量 | 錨 | 状態 |
|---|---|---|
| 3-1 | 錨 3〔非〕PT c-2 の発生量で α・β を置き換える腕 | 材料待ち(c-2 は tokyo-pt.jp の同意ページ越しで、手元に無い) |
| 3-3 | 錨 3〔非〕PT c-2 の目的別の形 | 材料待ち |
| 3-3 | 錨 4〔灰〕線ごとに違う材料(transfer_12 の peak_hourly・line_capacity_12・station_flow_12 の定期と普通) | 読まない(boundary_counts と同じ元・親の判断待ち=R-115 §5 空欄 1) |
| 3-4 | 錨 4〔非〕PT c-2 の自宅−勤務の発生量 | 材料待ち |

## §6 限界と仮採用(10-13b §0-3=既定 off の腕・後から戻せる形)

1. **母集団 P′(is_foreign で除く)を本則にした**のは、発注による仮採用。回答 10-13b §1 1-1 の文言は「訪日(kind 7)」なので、ユーザーの確認が要る。P(kind≠7)は継続の列として並べた。5 エリア計のピークは P でも全員でも 10 時で変わらない。
2. 1 日単位の 30 分を**合計**にし、時間帯別の θ を **1 分**にした。原典はどちらも [要確認] である。連続と θ 30 分は腕として並べた。
3. **ω_k = N_k / n_k** は未リサーチ(expedient)。
4. **計画上のセル**: W17 v2 の来街の行は target_cell を持たない。そのため計画の V は空で、計画のエリア別の在圏は来街以外の種別の行だけになる。来街以外の種別でも、舞台の中に居る分の 24% はセルが分からない(昼食の飲食店の行など)。
5. **W12 から組む在圏**(3-1 錨 2): 舞台全体の流量で、5 エリアには分けない。β の目的は帰宅を本則にした(R-115 の「帰宅中心」の字どおり)。I と O には年齢の軸が無い。
6. **中核 9 町丁目**: セル → 町丁目の写像(居住者の多数決+最近傍)と、昼の窓 10〜16 時は expedient。ランの比は標本の居住者 100 体から出している。e-Stat の境界で作り直す腕は作っていない。
7. 3-3 の到着は direction_node に帰属させた。域内居住者の帰りは線を選ばないので、ずれうる(R-115 §3-3 の宣言)。
8. 3-4 の始まりは「work_cell に 30 分以上続けて居た最初の区間」で決めた。活動の列(勤務)では数えていない(記録器に列を足すとエンジンを包む所が増えるので見送った)。
9. seed 1・1 日・5,000 体の 1 本だけで、ばらつきは測っていない。
10. **監査フックに出ない抜け道は 5 つある**(検収 L7・`read_guard.py` の docstring にも書いた)。
    - pyarrow(`parquet.read_table`・`pyarrow.fs`): 計器は parquet を読み口の検査(`read_parquet`)で縛る。md5 を取るときの Python の open は監査にも出る。
    - sqlite3: 計器は使わない。
    - subprocess(外のコマンドが読む): 計器は record と run の段の git と子プロセスだけで使う。
    - os.listdir・os.scandir(名だけ): 計器はプールの part の名の一覧にだけ使う。
    - hard link(一覧にある名で、実体が別のファイル): 見分けられない。
11. 落とす語の `kddi` は広い。道筋のどこかにその語があれば落ちる(安全側)。試験の名にもこの語を使えない。
12. 監査フックは一度入れると外せない。守りが無いときは何もしない。
13. 計器は CI に入れていない(data が要る)。版上げのたびに手で `run` を回す。
14. **out と `--compare` のフォルダは、渡した場所の下を全部許す**(検収 L9)。守る根(`data/`・`docs/`)そのものを渡すと根の下が開けてしまうので、渡すのは記録のフォルダ(`docs/bench/instruments/anchor_gauge/<版>/`)か作業用の場所に限る(誤用の宣言・道具では縛っていない)。
15. **journal の md5 は再現しない**(検収 L10): meta に壁時計が入るので、同じランでも md5 が変わる。同じランかは配列だけの hash(`journal_arrays_sha16`・meta を除く)で見る。
16. **record の段はエンジンが前から読む入力を開く**(検収 M1): `hunger_energy_anchors_v0.json`(〔検〕の行が混ざる)を含む。計器はその値を使わない。一覧は §3 の表と、版ごとの `anchor_gauge.md` の末尾に残す。

## §7 試験

`tests/tools/test_anchor_gauge.py` には 23 本ある(検収の直しで 4 本足した=§9)。

- 単体 10 本: 母集団の絞り、ω、合計と連続、θ と 24〜28 時、属性と訪日の列、到着、始業の検出、分布の統計、開端のビン、立ち上がり。
- 合成の記録で 4 つの量が決定的に出る 1 本: 手で数えた値と合う。
- 錨 1 が W17 v2 の勤務窓と同じ値になる 1 本。
- 許可の一覧 3 本: kddi_la と shibuya_jinryu の道筋の負の対照、監査フック、名を変えたファイルの差し込み。
- 書き出しと `--compare` の 1 本、一覧の外の記録を渡すと落ちる 1 本。
- 実データ(`requires_data("world_v2", "realworld:transport_census/time_dist_12.json")`)1 本。
- slow 1 本(`requires_data("world_v2", "persona_pool", "realworld:transport_census/time_dist_12.json")`): 2 腕で、記録器の有無で final と呼数が同じこと、ランの段の控えに封印の道筋が無いこと、同じランを 2 回取ると配列の hash が同じこと、計器が回ること。

結果(最初の版=検収の前):

- `-m "not slow"`: 18 passed(1.7 秒)
- slow を含む全部: 19 passed(4 分 34 秒・slow の 1 本が 272 秒=4 本のラン)
- 隣の試験 `tests/tools`・`tests/c7`(slow を除く): 215 passed(6.7 秒)

検収の直しの後の結果は §9 にある。
- byte-check は不要(src の差 0)。代わりに、記録器の有無で final と呼数が同じことを 2 腕で確かめた(§0 の 4)。

## §8 再現の手順(リポの根・作業木の src)

```
python tools/instruments/anchor_gauge.py run --scratch <作業用の場所>
#  → docs/bench/instruments/anchor_gauge/<日付>_<commit>/
python tools/instruments/anchor_gauge.py run --scratch <作業用の場所> --compare docs/bench/instruments/anchor_gauge/2026-10-14_2bc7a4b
#  → 同じフォルダに compare_vs_2026-10-14_2bc7a4b.md
```

journal(1 腕で約 1.8 MB)は作業用の場所に置き、記録には名・md5・配列だけの hash を書く。壁時計は 1 腕あたり約 50〜75 秒で、計器の段は約 10 秒。どちらも決定論ではない。

## §9 検収の直し([review.md](review.md)=条件つき受入・中 1・低 10)

| # | 直したこと |
|---|---|
| M1 | record の段で、ランの間に Python の `open` が開いた道筋を監査フックで控える(`ReadGuard.sealed_only(track_roots=…)`)。journal の meta の `record_opened_files` に残し、計器の段で落とす語に当たる行に印を付ける。`anchor_gauge.md` の冒頭を「gauge の段では」と限り、末尾に「record の段でエンジンが開いたファイル」の表を足した。§3 にも表を足した。最初の 1 回で開いたのは 20 本で、〔検〕の行が混ざるのは `hunger_energy_anchors_v0.json` の 1 本(エンジンが前から読む入力・計器はその値を使わない)。封印の層は 0 本 |
| L1 | §4 の「P 2.34」を 2.33 に(2.3348 を 1 回だけ丸める) |
| L2 | 草案 §1 の差を「20 歳以上で 5,268 体(全年齢では 5,315 体)」に。W16 で数え直した(P 336,578・P′ 331,310・P にだけ居る 5,268・P′ にだけ居る 0) |
| L3 | §2 の表に、3-1 錨 1(計画)は R-115 の「正時の標本」でなく v1.4 の数え方を当てた、と宣言した(直していない) |
| L4 | `presence_hourly` の θ を分で受けて秒で比べる(居た刻みの数 × 刻みの秒 ≥ θ × 60 秒)。時間の数は `shibuya.core.time_consts`(`STEP_SECONDS`・`SECONDS_PER_MINUTE`・`SECONDS_PER_HOUR`・`MINUTES_PER_HOUR`・`MINUTES_PER_DAY`・`HOURS_PER_DAY`)から取り、計器の中の直書きの 60・3600・24・1440 を消した。刻み 30 秒の試験を足した |
| L5 | ピークの順の区切りを `→`(早い順・左が早い)に。前の版との比べでは、`/order` の値を区切りの記号によらず並びの列で比べる |
| L6 | 実データの試験 2 本の `requires_data` に `realworld:transport_census/time_dist_12.json` を足した(`<置き場>:<相対の道筋>` の形は `tests/_data_ids.py` の登録表の `realworld` で通る=表は変えていない) |
| L7 | 監査に出ない抜け道 5 つ(pyarrow・sqlite3・subprocess・os.listdir/scandir・hard link)を §6 の 10 と `read_guard.py` の docstring に宣言した |
| L8 | `deny_hit` は、まず生の文字列(渡した形・絶対の形)で語を照らし、当たれば `realpath` を取らない(ファイルシステムに触らない)。落とすときの文言も名だけにした。試験は `_real` を「呼ばれたら落ちる」に差し替えて、本物の封印の道筋への check が `realpath` を取らないことを確かめる |
| L9 | §6 の 14 に、out と `--compare` のフォルダの許し方(渡した場所の下を全部許す・渡すのは記録のフォルダか作業用の場所に限る)を宣言した |
| L10 | journal の meta に配列だけの hash(`journal_arrays_sha16`・meta を除く)を足し、計器は読むときに確かめて記録の表に並べる。md5 が再現しないことは §6 の 15 に書いた |
| 他 | 差が 0 のときの比べの md は「変わった値は無い」と書く(検収 §7 の見た目の指摘) |

**最初の記録の作り直し**: 直した後の計器で、HEAD `2bc7a4b` の 2 腕を回し直し、`2026-10-14_2bc7a4b/` を作り直した。前の記録の写し(作業用の場所)と `--compare` で比べた結果は [compare_vs_2026-10-14_2bc7a4b_first.md](../../../instruments/anchor_gauge/2026-10-14_2bc7a4b/compare_vs_2026-10-14_2bc7a4b_first.md) にある。

| 比べたもの | 前 | 今 |
|---|---|---|
| 要約の値(2 腕・156 件) | — | **変わった 0 件** |
| final・呼数 | mock `5f7ae9ff24005314`・65,597 / classical `202a05a22c5bd8e1`・93,460 | 同じ |
| journal の配列の hash | mock `c529ac4832c86f04` / classical `47d076641b2531a8` | 同じ |
| journal の md5 | mock `27de87d1…` / classical `f42d5267…` | mock `9604aeea…` / classical `258ed6d5…`(meta の壁時計と新しい欄で変わる=L10) |

**試験**(直しの後): `tests/tools` を slow も含めて回して **52 passed**(6 分 51 秒)。計器の試験 23 本を含み、slow の 1 本は 408 秒(2 腕 × 3 本のラン)。計器の試験だけを `-m "not slow"` で回すと 22 passed(2.5 秒)。

**検収役の確かめごと 1**(`tests/c7` の試験が fixture で `presence_anchors_v0.json` を読む)は、親が台帳で扱う。計器側は触っていない。実装役も最初の版の確かめで `tests/c7` を回したので、そのプロセスの中でこのファイルが開かれた(値は出力に出ておらず、見ていない)。直しの後は `tests/tools` だけを回した。

## §10 親の検収(第334・Fable 5.1)

- **ディスク実在**: 上の §1 のファイルが作業木にあることを確認した(`git status`=新規 10 本・`src` の差 0 行・CR 0・絶対パスとホスト名の grep 0 件)。
- **試験(親の実行)**: `tests/tools`(not slow)51 passed・3.6 秒。slow の 1 本(5,000 体 2 腕)は §10-1 に追記する。
- **byte-check**: `src` を変えないので回さない(§7 の記録器なし/ありの final と呼数の一致、検収役の独立の 4 通りの一致で足りる)。
- **独立検収**([review.md](review.md)=条件つき受入・中 1・低 10)→ §9 のとおり全部直した。検収役の負の対照 51/51 が落ちたこと、3-2 と 3-4 の独立の再計算の一致、錨の写し検査の一致を受入の根拠にする。
- **封印の境界(宣言・値は読んでいない)**: ① 実装役が `presence_anchors_v0.json` の 1〜36 行目を計器の外で読んだ(core9 の写しのため・36 行目は次の項の名だけ・値は 37 行目=親がファイルの鍵の並びだけで突き合わせ)。② 検収役が「130,167」で docs を grep したとき d66 の 1 行(PT 由来の滞留の数=〔灰〕の種類)が出力に出た(確かめには使っていない)。③ 既存の試験 `tests/c7` の fixture は `presence_anchors_v0.json` を試験のプロセスの中で開く(値は出力に出ない)=本体の全体試験でも毎回開いている。扱いは PENDING §1-1b 仮-13(〔灰〕は決まるまで検証側と同じ・2-4 でファイルを較正側/検証側に分ける)。
- **宣言とコードの食い違い(検収で発覚・親が判断待ちに)**: `engine/energy.py` が `hunger_energy_anchors_v0.json` の第 18-1 表(東京の朝食・夕食の平均時刻)と 15 分の食事率から作った既定の食事時刻を使う(:366-371・:492・:600)。同じファイルの usage と R-115 §2 :67 は「検証にだけ使う」と宣言している。PENDING §1-1 に行を足した(親案 (b)=2-4 で W17 v2 の計画の分布に置き換え・第 18-1 表は検証専用のまま)。本段では §3 の表に宣言するだけ=コードは触らない。
- **仮採用の扱い**: §6 の 1〜13 のうち、P′(1)は仮-8(R-115)で既に仮採用、θ・合計/連続・ω_k・β・中核 9 の写像・計画の V が空・CI に入れない(2〜6・13)は PENDING §1-1b 仮-12 にまとめた。〔灰〕(錨 4・`pt_area_*`)は仮-13。
- **検収役の確かめてほしいこと**への親の答え: (1) `tests/c7` は検収の手順から外す(以後の検収の発注文に「tests/c7 は回さない」を書く)(2) 上の②=宣言だけ (3) M1 は §3 の表と journal の meta の控え(直し済み)(4) P′ はユーザーの確認待ち(仮-8)(5) `time_dist_12` は W12 の構築の入力=〔部〕のまま(矛盾なし)。
- **判定**: 受入(第 2 期 2-0 の完了)。次の版上げ(2-4)で `run` を回し `--compare` で前の版との差を出す。

### §10-1 slow の試験(親の実行)

- `tests/tools/test_anchor_gauge.py -m slow`(5,000 体・2 腕・実データ): 1 passed・408.6 秒(6 分 49 秒)。
