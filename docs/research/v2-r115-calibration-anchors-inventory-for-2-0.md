# R-115 答申: 第 2 期 2-0 較正側の錨の計器=錨の材料の棚卸し

<!-- hdr:v1 | 等級: B | 作成: 2026-10-14 | 範囲: 2-0 の錨の材料 -->
- **分野**: 人口学・合成人口論 #1 / 交通工学 #2 / 人間移動科学 #3 / 時間利用研究 #4 | **重要度**: (親が付ける)(計画 [v2-implementation-plan-2026-10-12](../design/v2-implementation-plan-2026-10-12.md) :71 の 2-0・[回答 10-13b](../design/v2-answers-2026-10-13b.md) §1 1-1・1-3・1-8・[仕分け](../reviews/triage-2026-10-13/README.md) §3-1・§3-3・§3-8)
- **一次確認**: **B**(親検収 2026-10-14・第334=§5 の主張 3 件を実読・再計算して一致: ① W16 の parquet で kind 1 かつ is_foreign=5,315・kind 7=17,404(全員 is_foreign)・is_foreign 計 22,719 ② `w12_generation_weights.parquet` の 10 ノードのうち鉄道 8 線の時刻の形は同一(差 < 1e-12・ピーク 8 時)で、road_gate(ピーク 8 時)と walk_gate(ピーク 10 時)だけ違う ③ R-109 :62/:64/:75 が PT の検証側の値(時刻別滞留人口・目的別の到着)を書いている)
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 作成 2026-10-14・リサーチ役サブ(Opus 5.5)。子サブ未起動・ネットワーク不使用(リポの中だけ)。**値を読んでいないもの**: 封印した層 `kddi_la`・`shibuya_jinryu`・`boundary_counts.json`(列名・`source` の欄・行数だけ)・`data/realworld_live/`・PT の検証側(c-2 の 0240〜0243 の集中量と b-4。読んだのは見出し 5 行・ゾーンの符号・行数だけ)・`diversity_anchors_v0.json` の第 30 表の値。構築側の資産(W12・W16・W17・`docs/bench/anchors/` の構築側・大都市交通センサスの透明な層)は値まで読んだ。
>
> **既存答申との関係**(重ねない): KDDI の 3 区分・30 分・20 歳未満 = [R-56](v2-r56-kddi-attribute-definition-check.md) §2・§3 / 人数の作り直しと PT の按分 = [R-109](v2-r109-population-size-rebuild-materials.md) / 勤務の時刻の公的統計 = [R-99](v2-r99-work-schedule-public-statistics.md) / 無償と申請のデータ = [R-92](v2-r92-free-and-application-data-sources.md) / 時刻別の候補一覧 = [d1_reacquisition](v2-d1-reacquisition.md) / 写像の感度腕と体の journal = [presence-shape 記録](../bench/analysis/presence-shape-2026-09-29/README.md) §9b / v1.4 の定義の親案 = [仕分け C](../reviews/triage-2026-10-13/C.md) §2-1 / 出勤 ≠ 始業 = [v2-d68-behavioral-diversity-research](v2-d68-behavioral-diversity-research.md) §2-3。

## §0 要旨(結論を先に)

1. **4 つの量とも、計器の器は今すぐ作れる**。 記録の口は既存の体の journal(`tools/c7/attr_arms.py` の `AgentCellRecorder`・エンジン不変)と W16 の体の軸で足りる。エンジンの在圏 journal(種別 × セル × 正時)では v1.4 の母集団・area 写像・滞在 30 分が出せない。駅ごとの到着と始業も体の journal から作る(ActualLog の鉄道は発車の行だけ・到着は合計 `n_arrivals` だけ)。
2. **錨の中身は 4 つで差がある**。 舞台に固有で、今の版の入力でもない錨は、較正側には無い。舞台の在圏と来街者の錨は検証側(b-4・KDDI)にしか無い。
   - 在圏のピーク時刻: 今すぐ作れる。錨は計画上の在圏(W17=入力の写し)と、W12 とセンサスから組む在圏の形(首都圏共通の形・一部が入力)の 2 本。
   - 来街者/居住者の比: 今すぐ作れる。錨は W16 の体数(写し)と計画上の在圏(写し)。勤務者/居住者の側だけ、入力でない代理がある(中核 9 町丁目の昼夜間人口比)。来街者の側の入力でない錨は、較正側では今後も手に入らない見込み(第 4 期 段 1 で PT c-2 を入れても構築の入力になる)。
   - 駅ごとの到着の波: 器は今すぐ作れる。線の割合は写し。時刻の形(W12 の重み)は 8 線とも同じで、線ごとの情報が無い。線ごとに違う材料(乗換表のピーク 1 時間・輸送定員・定期券の割合)は封印 `boundary_counts` に同じ元の行があり、使うかは親の判断待ち。
   - 勤務の始業の分布: 今すぐ作れる。第 31 表は W17 v2 の勤務窓の入力(写し)。第 8-1 表(関東大都市圏の「仕事」の 15 分)は classical では入力・mock では入力でない。PT c-2 の自宅−勤務の発生量は、今は入力でない。
3. **循環の印**: 写しになる材料は W16・W12 の線の割合・W17 v2・第 31/36 表・PT d-1。今の版で入力でない材料は time_dist_12 の時刻の形(W17 v2 の raking は採用 0%)・PT c-2 の発生量・昼夜間人口。§2 の表に印を付けた。
4. v1.4 の草案(§4)の母集団 `kind≠7` では、訪日の体 5,315 が落ちない。W16 の業務来街(kind 1)のうち `is_foreign=True` の体で、扱いは親の確認が要る(§5 主張 1)。

## §1 出典(リポ内・読んだ日はすべて 2026-10-14)

| # | ファイル・答申 | 読んだ所 |
|---|---|---|
| 1 | `docs/design/v2-implementation-plan-2026-10-12.md` | :49・:71(2-0)・:83(3-1) |
| 2 | `docs/design/v2-answers-2026-10-13b.md` | §1 1-1・1-2・1-3・1-8 |
| 3 | `docs/reviews/triage-2026-10-13/README.md`・`C.md` | README §3-1〜§3-3・§3-8 / C §2-1〜§2-3・§3 |
| 4 | `docs/design/v2-pattern-ledger.md` | §10-1〜§10-4(:215〜:262) |
| 5 | `src/shibuya/build/field/w12_external_nodes.py` | :1-30(docstring)・:47-51・:160-170・:247-268・:354-541 |
| 6 | `src/shibuya/build/pop/w16_population.py`・`data/world/v2/W16.header.json`・`w16_cohorts.json` | :1-75・:422-424・:550-562 |
| 7 | `data/world/v2/W17.header.json`・`src/shibuya/build/sched/trial.py` | expedients・:1-60・:166-370 |
| 8 | `src/shibuya/build/audit/w19_freeze.py` | :25-110(SOURCE_FAMILIES・layer_independence) |
| 9 | `tools/c7/c7lib.py`・`attr_arms.py`・`presence_yardstick.py`・`prereg_v13.py` | c7lib :1-110・attr_arms :1-80・:140-160 |
| 10 | `docs/bench/anchors/*.json`(5 本) | presence_anchors_v0・commute_time_dist_r3・ssb2021_activity_prior_v0・hunger_energy_anchors_v0(usage)・diversity_anchors_v0(source の欄だけ) |
| 11 | `src/shibuya/engine/processes/rail.py`・`engine/presence.py`・`engine/systems/state_io.py`・`engine/events/vocab.py`・`engine/arbiter.py` | rail :734-810・presence :95-130・:590-680・state_io :217-243・arbiter :60-75 |
| 12 | `data/realworld/transport_census/*.json`(5 本)・`data/calib/pt2018/MANIFEST.md` | 構造と `_meta`(time_dist_12 は値も) |
| 13 | `docs/bench/c7/prereg_arms_v1.md`・`docs/bench/analysis/presence-shape-2026-09-29/README.md` | prereg §1〜§5 / presence-shape §3・§9b |
| 14 | 答申 R-56・R-57・R-92・R-99・R-109・d66・d68 | §1 の「重ねない」に挙げた節と d66 :286・d68 :127-131 |

## §2 錨 × 材料の表

印: **〔写〕** 入力の写し(構築の入力そのもの・その直接の帰結。合否にしない・形だけ)/ **〔部〕** 一部だけ入力(腕か版で変わる)/ **〔非〕** 今の版の入力でない / **〔検〕** 検証側(使わない)/ **〔灰〕** 区分が決まっていない(親の判断)。パターン台帳 §10-3 の規則(構築に使ったものは検証に使わない)に沿って、〔写〕と〔非〕を分けた。

| 錨 | 材料と所在 | 列・軸 | 分解能 | 舞台への写像 | 今の版での役割 | 印 |
|---|---|---|---|---|---|---|
| センサス(人数) | `data/world/v2/w16_population.parquet`(390,067 行)・`w16_cohorts.json`(9 層・層ごとに出所 1 行) | agent_id・kind・purpose・age・sex・home_cell・work_cell・school_cell・direction_node・chome_key・org_id・industry_key・duty_role・pool_layer・synthetic・is_foreign ほか | 体 1 人・セル | セル → `tools/c7/area_axes_v0.json` の 5 エリア(expedient・外は −1)/ 種別 → `c7lib.KIND_TO_ATTR`(:97-107) | シミュの母集団そのもの | 〔写〕 |
| 国勢調査 2020 小地域(夜間人口・年齢 × 性) | `data/realworld/estat/国勢調査2020_小地域_*.json`・`r2ka13113/` | 町丁目 × 年齢 5 歳 × 性 | 町丁目 | W16 の chome_key・home_cell | W16 の住民の目標と raking | 〔写〕 |
| 経済センサス 2021 | `data/realworld/census_r3/station_area_industry.json` ほか | 町丁目 × 産業 | 町丁目 | W16 の org・work_cell | W16 の通勤者の目標 | 〔写〕 |
| 昼夜間人口(区計) | `data/realworld/estat/国勢調査2020_昼間人口夜間人口_渋谷区.json` | 区の昼間・夜間・流入 | 区 | — | W16 が読むが notes の `ward_anchors` に書くだけ(w16_population.py :422-424・:800)=体数に効かない | 〔非〕 |
| 昼夜間人口(中核 9 町丁目・都 第 11 表) | `docs/bench/anchors/presence_anchors_v0.json` の core9_*(親確認 09-10) | 昼間 130,167・夜間 8,810・比 14.8 | 9 町丁目(1.39 km²) | W16 chome_key で町丁目へ寄せる | 構築は読まない | 〔非〕 |
| PT 2018 d-1 | `docs/bench/pt_shibuya/pt6_summary_core0241.json`・`data/realworld/pt_tokyo/pt6_d-1_purpose_mode_od.csv` | 0241 着の目的 × 手段 | 1 日・ゾーン | — | W16 の層の比(通学・業務・私事)と W12 の徒歩・道路の流量 | 〔写〕 |
| PT 2018 c-2 発生量(舞台の外) | `data/calib/pt2018/pt6_c-2.csv`(cp932・18,345 行・29 列) | ゾーン 655(実ゾーン 615・「--」18・集計 22=`:7xxx`・`:8xxx`・`:9999`・`:8888 全計`)× 時刻 28 行(3時台以前・3〜26時台・27時台以降・時刻不明・合計)× 発生量 9 目的+計 | 1 時間・ゾーン・平日(2018 秋) | 都市圏の形=舞台に固有でない | 構築側に指定(10-13b §1 1-3)・src・tools・tests から未使用(仕分け C §2-3・2026-10-14 の grep も 0 件) | 〔非〕(3-1・4-1・第 4 期 段 1 で入力になったら〔写〕) |
| PT 2018 c-2 集中量(0240〜0243)・b-4 | 同 `pt6_c-2.csv`・`pt6_b-4.csv` | — | — | — | 検証側(10-13b §1 1-3) | 〔検〕 |
| PT 2018 c-3・c-4 | 同 `pt6_c-3.csv`・`pt6_c-4.csv` | 手段 × 時刻 / 施設 × 手段 | — | — | §10-2 にも 10-13b にも区分が無い | 〔灰〕 |
| 大都市交通センサス 駅別発着 | `data/realworld/transport_census/station_flow_12.json`(162 行) | 9 線 × 券種(定期・普通・合計)× 上下 × 乗車/降車/通過 | 1 日・線 | W12 の鉄道ノード 8 | W12 の流入=降車 − 乗換流出(券種は「合計」だけ使う) | 〔写〕(定期・普通の内訳は〔灰〕) |
| 同 時刻分布 | `time_dist_12.json`(228 行・share_of_daily) | 目的 5+合計 × 乗車/降車 × 19 区分(～6時台・7〜23時台・0時台～) | 1 時間・首都圏全体(駅別でない) | 全ノード共通 | W12 の時刻の重み・W17 v2 の raking の参照(**採用 0%**=W17.header.json の expedients) | 〔部〕 |
| 同 乗換表 | `transfer_12.json`(106 行) | gate_entry 11・transfer 79・gate_exit 12・total 4 × daily・peak_hourly(7:45〜8:44) | 1 日+朝ピーク 1 時間 | 線 | W12 は transfer 行の daily だけ使う(:262-266)。peak_hourly と gate の行は未使用 | 〔写〕/ 未使用の欄は〔灰〕 |
| 同 輸送定員 | `line_capacity_12.json`(456 行) | 事業者 × 線 × 方向 × 区間 × 着時間帯 19 区分(始発～6:59・30 分〜2 時間の幅) | 30 分〜2 時間・線 | 線 | 構築は読まない(rail.py の docstring の 2)=供給であって需要でない | 〔灰〕 |
| 同 第 13 回 駅間 OD | `station_od13_13.json`(6,347 行・2021) | 初乗り駅 × 最終降車駅 | 1 日 | — | 構築は読まない | 〔灰〕 |
| ODPT 乗降人員 | `data/realworld/odpt_passenger_survey/shibuya.json` | 事業者 × 線 × 年度 | 1 日・年度 | W12 の併記の列 | 流量には効かない(:395-405・:448-452・:479 は列に写すだけ) | 〔非〕 |
| W12 出力 | `w12_external_nodes.parquet`(10 行)・`w12_generation_weights.parquet`(2,014 行) | ノード × 目的 × 手段 × 時(重み)/ daily_inflow・daily_outflow | 1 時間・ノード | ノード → 線 | W16 の方面 OD の元(方面 JSD 0.00085 の門) | 〔写〕 |
| W17 v2 | `w17_schedule.parquet`(3,461,954 行・1 日モード=月曜 d0) | agent_id・day・seq・start_min・end_min・activity_code・place_kind・target_cell・block_kind | 分・体 | target_cell → 5 エリア/ PlanBlocks.from_weekly(derive_rule) | エンジンが実行する計画 | 〔写〕 |
| 社会生活基本調査 第 31/36 表 | `docs/bench/anchors/commute_time_dist_r3.json`(原表 `data/research_cache/estat_r3_avgtime_000032224421.xlsx`・`…427.xlsx`) | 全国 × 雇用形態 12 行 × 出勤 58 区分/帰宅 70 区分 | 15 分 | — | W17 v2 の勤務窓(逆関数法+arrival_lead・事実として渡す) | 〔写〕 |
| 同 第 8-1/8-2/8-3 表 | `docs/bench/anchors/ssb2021_activity_prior_v0.json` | 19 行動(食事 03 を除く)× 15 分 96 区分 × 性 × 就業 × 地域(00 全国・03 関東大都市圏) | 15 分 | — | classical の事前分布 | 〔部〕(classical では写し・mock では入力でない) |
| 同 第 4-1・7-1・18-1 表と第 8-1 の食事の行 | `data/calib/hunger/`・`presence_anchors_v0.json` の wake_rate | — | — | — | 「検証にだけ使う」の宣言(arbiter.py :72-75・hunger anchors の usage=K6 (i)) | 〔検〕 |
| 同 第 30 表・第 14 表・第 15-1〜15-3 表 | `data/research_cache/estat_r3_avgtime_000032224420.xlsx`・`r99/` | — | — | — | 第 30 表=影の段の比較(10-12 CA2)/ 第 14・15 表=使っていない表(§10-2 の文言で検証側) | 〔検〕 |
| PT 由来の 139 ha の滞留 | `presence_anchors_v0.json` の pt_area_daytime_peak・night_presence_estimate(渋谷区の基礎調査 概要版 H28・内閣府の頁・d66 :286「パーソントリップデータより」)/ 都の安全確保計画 Ver3.0 の 14 時台 146,309(R-109 #11) | — | — | 139 ha | 在圏の物差しが読む(b-4 と同じ種類の量) | 〔灰〕 |

## §3 量ごとの式と記録の口

### 3-0 共通

- **記録の口**: (a) エンジンの在圏 journal(`--occupancy-every 60 --occupancy-out`)=種別 × セル × 正時。年齢・体の軸・正時の間の在圏が無いので v1.4 には使えない(presence-shape §9b-5)。(b) **体の journal**(`attr_arms.py record`=`AgentCellRecorder`・毎 tick の cell と transit_state・5,000 体で 14.4 MB・既定腕でエンジンの journal と一致を確認済み=§9b-2)。(c) 計画(`engine.presence.PlanBlocks.from_weekly` を**ランと同じ derive_rule** で)。(d) 日次の記録(`state_io.day_record`: day・end_T・money・bodies・census_row・calls_by_model・clock_kind・step_seconds・bridges_count・events)と manifest(腕の設定と指紋=計器の行の鍵)。在圏と到着の欄は日次の記録に無い。(e) 出来事の記録(1-3)は世界過程の行と区切りだけ。行為(移動・到着)は LlmCall の配線の後なので、今は使えない。
- **2 腕**: `--policy mock` と `--policy classical`(5,000 体・計画実行層 on)。
- **5,000 体の重み**: 二層抽出で種別の構成が W16 と違う(CREW 14% 対 0.3%・presence-shape §9b-1)。比を出すときは種別 k の重み w_k = (W16 の k の割合)/(標本の k の割合) で戻す(未リサーチ(expedient)・宣言)。自宅が 5 エリア内の体は 143(2.9%)で、エリア別の居住者は 5〜64 体しかない。5 エリア計を主にし、エリア別には件数を添える。
- **時刻**: KDDI の 5〜28 時の 24 区分に合わせる(`c7lib.KDDI_HOUR_BINS`)。1 日ランでは 24〜28 時を同じ日の 0〜4 時で代える(宣言)。
- **既存の物差しとの関係**: `tools/c7/presence_yardstick.py` と `tools/w17/diversity_yardstick.py` は較正側と検証側の錨が混ざっている(pt_area_daytime_peak・wake_rate=第 4-1 表・第 30 表)。2-0 で流用するなら、§2 の〔検〕〔灰〕の錨を読まない設定が要る。

### 3-1 在圏のピーク時刻

- **量**: エリア a(5 エリアと 5 エリア計)の在圏 N_a(h)(§4 の母集団と滞在の数え方)の argmax(h ∈ 5..28)と、5 エリアのピークの順序(H2 と同じ形)。
- **錨 1 〔写〕 計画上の在圏**: P_a(h) = 正時 h にブロックの中にいる体の数(PlanBlocks・場所は target_cell。target_cell < 0 の職場・学校の行は W16 の work_cell/school_cell で補う=宣言)。差 N − P は「計画 → 実行のずれ」で、現実との差ではない。既存の計測は `docs/bench/c7/yardstick/w17_derive_v1_v2_v21/`。
- **錨 2 〔部〕 W12 から組む在圏の形**(5 エリア計だけ): N̂(h) = R + Σ_{t≤h} I·α(t) − Σ_{t≤h} O·β(t)。R は舞台の住民の在宅、I・O は W12 の総流入・総流出、α は time_dist_12 の降車を d-1 の目的の構成で重み付けた形(=W12 の重みの時刻の周辺)、β は乗車の形(帰宅中心・presence_anchors の homebound_boarding_time_dist_2015 と同じ元)。水準は写し・時刻の形は今の W17 v2 に入っていない。
- **錨 3 〔非〕(腕)**: 錨 2 の α・β を PT c-2 の発生量(舞台の外・§3-4 の式)で置き換え、所要時間 τ ∈ {0, 30, 60} 分だけずらす。錨 2 と錨 3 の差が、現実同士のずれ(フロア)の代わりになる。
- **今すぐ**: 作れる。舞台に固有で入力でない錨は較正側に無い(b-4・KDDI=検証側)。

### 3-2 来街者/居住者の比

- **量**: 1 日単位(§4 の 30 分)で、エリア a に数えた体を属性で分けた V_a/Res_a と W_a/Res_a(属性は §4 の area 写像・kind 写像は継続の記録として並べる)。
- **錨 1 〔写〕 W16 の体数**(kind 写像・舞台全体・2026-10-14 に再計算): 全体 来街 129,391・居住 43,622・勤務 217,054(来街/居住 2.97)/ kind≠7 で 2.57 / kind≠7 かつ age≥20 で来街 88,340・居住 37,836・勤務 210,402(来街/居住 2.33・勤務/居住 5.56)。area 写像の体数は「来る人」を数えられないので錨 2 を使う。
- **錨 2 〔写〕 計画上の在圏を属性で分けた比**(3-1 錨 1 と同じ計算)。
- **錨 3 〔非〕 中核 9 町丁目の昼夜間人口比 14.8**: (住民の残留+通勤・通学の流入)÷ 住民=**勤務者/居住者の側だけ**の代理。来街者を含まない・範囲が町丁目(5 エリアと違う)。W16 の chome_key で町丁目へ寄せた腕で比べる。R-109 は W16 の勤務+通学 249,157 を、国勢調査の昼間人口からの推し 約 18.5 万・PT 2018 の平日の到着 15.3〜19.9 万の 1.3〜1.6 倍とした=この錨は今の W16 からずれる向きを持つ。
- **フロア**: PT と KDDI の来街/勤務比 0.16〜0.27 対 1.66(`attr_arms.py` :57-59)=定義の差が大きく、比の水準は合否にしない。
- **今すぐ**: 作れる。来街者側の入力でない錨は較正側に無い。

### 3-3 駅ごとの到着の波

- **量**: 線 ℓ(W12 の鉄道ノード 8)とゲート 2(徒歩・道路)の時刻別の到着 A_ℓ(h) から、(i) 1 日の割合 s_ℓ (ii) 時刻の形 A_ℓ(h)/Σ_h A_ℓ (iii) ピーク時刻。
- **シミュ側**: 体の journal で transit_state が域外 → 舞台へ変わった tick × その体の W16 `direction_node`(計画実行層は `line_of_agent` を direction_node から作る=presence.py :670-674)。域内居住者の帰り(D-61)は線を選ばないので、帰属は direction_node とずれうる(宣言)。計画の側は ARRIVE の予定時刻 × line_of_agent で出せる。
- **錨 1 〔写〕 線の割合**: s_ℓ = daily_inflow_ℓ / Σ(station_flow_12 の降車 − 乗換流出)。W16 の方面に入っている。
- **錨 2 〔部〕 時刻の形**: W12 の重みの node × hour の周辺。**8 線とも同じ形**(再計算で最大差 < 1e-16・ピーク 8 時)。時刻の形は目的だけで決まり(:510-541)、目的 × 手段の構成は全ノード共通(docstring の expedient)。線ごとの違いの情報は無い。
- **錨 3 〔非〕(腕)**: PT c-2 の発生量の目的別の形を d-1 の目的の構成で混ぜ、τ だけずらす(全線共通)。
- **錨 4 〔灰〕 線ごとに違う材料**: transfer_12 の gate_exit の peak_hourly/daily(朝 1 時間の集中率)・line_capacity_12(着時間帯の供給の形)・station_flow_12 の定期券の割合。どれも構築は使っていないが、封印 `boundary_counts` に同じ元の行がある(`_meta.n_by_source`: line_capacity 456・transfer 212・station_od13 10・time_dist 228・station_flow 54・odpt 52・derived 38)。2-0 で使うかは親の判断(§5 空欄 1)。
- 実ダイヤ(2-3b)は供給の形で、需要の錨にはならない。無償の駅 × 時刻の一次表は無い(time_dist_12 の caveats「第13回(2021年度)には駅別×時間帯の集計表が無い」)。
- **今すぐ**: 器は作れる(エンジン不変)。線ごとの時刻の錨は材料待ち(錨 4 の判断)。

### 3-4 勤務の始業の分布

- **量**: 勤務の体(kind 0 と 2。kind 5 は通学として別の列)について、その日に初めて W16 の work_cell に 30 分以上続けて居た区間の始まり t_start の 15 分の分布(平均・分位・:00/:30 の率・最頻ビン)。活動(WORK)の開始で数えるなら、記録器に活動の列を 1 本足す。
- **注意**: 社会生活基本調査の「出勤」は家を出た時刻で、始業=出勤+片道の通勤時間(d68 研究 §2-3)。通勤時間の分布は未取得(同 :376)。
- **錨 1 〔写〕**: 第 31 表の出勤を employment_mix で混ぜ、arrival_lead(プール・欠損は 30 分)を足した分布=W17 v2 の勤務窓の作り方そのもの(trial.py の逆関数法)。
- **錨 2 〔写〕**: W17 v2 の勤務ブロックの開始(計画)。W17 v2 の LLM は渡した窓から離れている(header の duty_window_dev_min p50 67 分)ので、錨 1 と錨 2 は別の列にする。
- **錨 3 〔部〕**: 第 8-1 表 関東大都市圏・就業 × 性の「仕事」(05)の 15 分の行動者率の朝の立ち上がり(例: 05 の率が日中の最大の 50% を超える最初の 15 分。閾値は未リサーチ(expedient))。classical では入力・mock では入力でない。
- **錨 4 〔非〕**: PT c-2 の自宅−勤務の発生量(舞台の外)の発時間帯の形 S_勤務(h)(1 時間)。出勤の形として第 31 表(全国 2021)と並べると、現実同士のずれ(フロア)になる(調査年 2018 対 2021・都市圏対全国の差は宣言)。
- **除外**: 第 30 表(東京都)=CA2 の影の段の比較(検証)。`diversity_anchors_v0.json` の tokyo_weekday_depart_*・national_weekday_depart_* は第 30 表から作ったもので、2-0 では読まない。第 14・15 表(R-99)は使っていない表=検証側。
- **今すぐ**: 作れる。

**PT c-2 の構築側の式(3-1 錨 3・3-3 錨 3・3-4 錨 4 の共通)**: 目的 p の形 S_p(h) = Σ_{z∈Z} G_{z,p}(h) / Σ_{h'} Σ_{z∈Z} G_{z,p}(h')。Z=実ゾーン 615 から 0240〜0243 を除いた 611(「--」18 行を足す腕を併記)。集計行 22 は足さない(二重に数える)。h は 26 区分(時刻不明・合計を除く)で、24〜26時台と 27時台以降は翌日の 0〜3 時(1 日ランでは同じ日へ畳む)。舞台のゾーンの行は**引き算にも使わない**(全計から引くと舞台の行を読むことになる)。c-2 は年齢の軸を持たないので、v1.4 の 20 歳未満の除外は錨の側で揃えられない(通学を外した形を腕に)。

## §4 事前登録 v1.4 の定義の草案(3-1 の決定を式に・holdout は開けない)

1. **母集団**: P = {i ∈ W16 : kind_i ≠ 7 ∧ age_i ≥ 20}(W16 で 336,578 体。kind 7=17,404 体・kind≠7 で age<20=36,085 体を除く)。kind 7 は別の列に記録し、合否に入れない。**未決**: kind 1 で `is_foreign=True` の 5,315 体を除く P′ = P ∧ ¬is_foreign を本則にするか(§5 主張 1)。決まるまで P と P′ の 2 列を並べる。
2. **属性**(R-56 §2 の判定順): エリア a について、area(home_cell_i)=a → 居住者 / そうでなく area(work_cell_i)=a か area(school_cell_i)=a → 勤務者 / どちらでもない → 来街者。域外常住の home は −1。kind 写像(`KIND_TO_ATTR`)は継続の記録として並べ、合否に入れない。
3. **エリア**: `tools/c7/area_axes_v0.json`(expedient)。±50 m の感度を併記。
4. **滞在(1 日単位)**: m_{i,a,d} = Σ_t 1[area(cell_{i,t}) = a]·Δt(Δt=60 秒)。D_{a,d} = {i ∈ P : m_{i,a,d} ≥ 30 分}=**合計**で数える(仕分け C §2-1 の 5)。原典の「30分以上滞在した人を１日単位」は連続か合計かを書いていない [要確認] ので、連続の腕を感度に並べる。
5. **時間帯別**: N^θ_{a,h} = |{i ∈ D_{a,d} : 時間帯 h の中でエリア a に居た分 ≥ θ}|、θ ∈ {1 tick, 30 分}。「1 時間ごとにそれぞれカウント」の細部は原典で [要確認]。今の `attr_arms` の滞在腕は「その 1 時間の中で**連続** 30 分」で 1 日単位の条件を持たない=v1.4 には腕を 1 つ足す(器の差)。正時の標本(v1.3 の数え方)は継続の列。
6. **時刻**: 5〜28 時の 24 区分。1 日ランの 24〜28 時は同じ日の 0〜4 時で代える(宣言)。
7. **曜日**: シミュは平日 1 日(W17 v2 は月曜 d0)。KDDI の手元の表は年合算で日種が無い=「平日のシミュ対全日の現実」と宣言する。週末のランが 10-12 CA10 の条件を満たしたら、暦の年の平日の日数 n_wd と土休日の日数 n_re(内閣府の祝日の表)で重み n_wd/365・n_re/365 を付けた合成の腕を足す。
8. **不足の宣言**: 都市圏の外の国内客(国内の宿泊客を含む)はシミュに居ない(R-109・PT は都市圏の居住者だけ)。
9. **記録**: 主張腕のランで体の journal(kind・age・is_foreign・home/work/school のエリア)を必ず書く。
10. **フロア**: 0.16〜0.27 対 1.66 を併記する。
11. **線と test の層**: H1〜H5 の線は v1.3(`prereg_v13.py`)のまま。test の層は K5(2026-10-13 時点で未公開=R-114)と D1b(目視の宣言つき)。ここでは定義だけ書き、開けない。

## §5 空欄・未確認・親が確認すべき主張

**親が確認すべき主張 3 件**

1. **`kind≠7` で落ちない訪日の体が 5,315 ある**。 W16 は私事の来街の層だけ `is_foreign` を kind 7 に振り替え(`src/shibuya/build/pop/w16_population.py` :561-562)、業務来街の層(:552-556)は振り替えない。`w16_population.parquet` で再計算すると kind 1 かつ is_foreign=5,315、kind 7=17,404(全員 is_foreign)。is_foreign が「訪日」の意味なら、v1.4 の「国内居住者」の母集団に 5,315 体の訪日が残る。
2. **time_dist_12 の時刻の形は今の W17 v2 に入っておらず、8 線とも同じ形**。 根拠は `data/world/v2/W17.header.json` の expedients「raking は 12% と 0% を計算し**採用は 0%**」と、`w12_generation_weights.parquet` の node × hour の周辺の再計算(鉄道 8 ノードの最大差 < 1e-16・ピーク 8 時)・`w12_external_nodes.py` :510-541(時刻は目的だけで決まる)。この 2 つで §2 の〔部〕の印と §3-3 の「線ごとの錨は材料待ち」が決まる。
3. **PT の検証側はすでに目に触れている**。 R-109(10-12・10-13b の分け方の前)が 0240〜0243 の b-4 と c-2 の集中量を按分して値を載せた(`docs/research/v2-r109-population-size-rebuild-materials.md` :62・:64・:75、`docs/research/scripts/r109/r109_local_counts.py` :126-138)。検証に使うときは D1b と同じ「起草時に目視済み」の宣言が要る。あわせて、`v2-pattern-ledger.md` :247 の PT の行は 10-14 時点でまだ「〔要決定〕」で、10-13b §1 1-3 の「§10-2 に先に書く」が未反映(並行の作業木で直している可能性あり)。`presence_anchors_v0.json` の pt_area_daytime_peak は PT 由来の 139 ha の滞留(d66 :286)で、b-4 と同じ種類の量。

**空欄・未確認**

1. 封印 `boundary_counts` と同じ元の未使用の欄(transfer_12 の peak_hourly と gate の行・line_capacity_12・station_od13_13・station_flow_12 の定期と普通の内訳)を 2-0 で使ってよいか。W19 の `BUILD_INPUT_FAMILIES` は W12 の 4 ファイルだけで、この 3 ファイルは載っていない。
2. 第 4-1 表 a(h) の区分: arbiter は「検証にだけ使う」と宣言し、在圏の物差しは錨として読む。
3. PT c-3・c-4 の区分が §10-2 と 10-13b に無い。
4. 所要時間 τ の分布(PT の発生量 → 到着・出勤 → 始業)は未取得。片道の通勤時間の表の statInfId は未特定(d68 :376)。
5. PT c-2 の舞台への漏れ(都市圏の発生量のうち舞台に着くトリップの割合)は未計算。計算には舞台の集中量の総量が要る(0241 の 1 日の総量は d-1 で使用済み=INDEX の R-57 の行)。
6. 5,000 体の種別の重みの扱い(重みで戻すか、層別のまま並べるか)。
7. 計画上の在圏で target_cell < 0 の行の場所(W16 の work_cell/school_cell で補う案)は未検証。
8. 錨 3 の「立ち上がり」の閾値(50%)と、始業の「30 分以上続けて」は未リサーチ(expedient)。
