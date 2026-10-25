# R-121 今のコードで 4 層(空間・制度・人口と事業所・運行)が混ざっている所=渋谷専用の作りの洗い出しと、分離の見積り

> 作成 2026-10-25・リサーチ役(Opus 5.5)。発注=[回答 10-25](../design/v2-answers-2026-10-25.md) §1-1(4 層の定義)・§5 R-A ③。
> やったこと: `src/shibuya/` を grep と Read で読んだだけ。コードは変えていない。ネットワークは使っていない。`data/world/v2/` は `ls` と小さな JSON(`build_manifest.json`・`world_crs.json`・`nav1_meta.json` の鍵)だけを読み、parquet は開いていない。
> 場所は `path:行`(パスは `src/shibuya/` を省いた。リポの根からのものは `docs/…`)。「天神で何を入れ替えるか」と「難しさ」は本書の見立て=**未リサーチ(expedient)**。コードの外の事実(福岡の制度・統計の有無)を書いた所は「推測」「未確認」と書いた。

## §0 要旨

1. 渋谷専用の作りは 69 か所を挙げた(§1 の 72 行から「変更不要」の確認 3 行を除く)。層ごとに 空間 20・制度 13・人口と事業所 18・運行 16・判断 2。
2. 判断の仕組み(`engine/decision/`・`llm/`・記憶・知覚の組み立て)には、場所の固定は見当たらない。例外は知覚の固定文の地名と条例の文(`perception/templates.py:299-302,326`)だけ。
3. エンジンは世界資産を `--world` の道筋で読む(`cli.py:843`・`engine/run.py:2572`)。空間はほぼデータの差し替えで動く。
4. 固定が最も濃いのは構築側(`build/`)。入力のファイル名・市区町村の符号 `13113`・期待値のゲート(出口 45・セル 453/520・POI 2,337)が定数で書かれている。
5. 運行は 2 か所でコードの分岐が要る。「渋谷は 1 駅」の仮定(`engine/processes/rail.py:45,583`・`engine/presence.py:1761`・`world/assets.py:825,1248`)と、時刻表の読み口(手で入手した JR・東急の表と ODPT。GTFS の読み口は無い)。
6. 制度は規則の表(`docs/design/rules-table.json`・30 行)に寄せ始めているが、管轄の欄は無い。管轄は id の名前(`minimum_wage.tokyo` など 10 行)と `params.area` に埋まっている。営業時間の法の上限は表の外のコード(`build/field/w7_planspec.py:78` の `LAW_CAPS`)にある。
7. 時点は表にある(`asof`・`asof_basis`)。足すのは `jurisdiction` 1 欄で足りる見立て(§3)。
8. 1 バイト不変で先に出せるのは、原点の写し 3 か所の一本化と、エンジン側の定数を「場所の設定」に出す整理(既定値=今の値)。規則の表の欄を足すと表の sha(`rules_version`)が変わる。ただし状態のハッシュは変わらない見立て(§4)。
9. 親への問いは 9 個(§5)。

## §1 渋谷専用の作り(ハードコード)の一覧

入れ替え: データ=ファイルを差し替える・定数=値を場所の設定へ出す・コード=分岐か新しい読み口が要る。難しさ: 小=数行・中=1 ファイルの中で数十行・大=複数ファイルにまたがる。

| # | 層 | 場所 `path:行` | 何が固定されているか | 天神で入れ替えるもの | 難しさ |
|---|---|---|---|---|---|
| 1 | 空間 | `build/geo/common.py:58-69` | 世界の原点 `ORIGIN_LATLON=(35.6595, 139.70062)`・地盤高 `GROUND0_M=15.18`・1 度あたりの m(原点の cos)・セル `CELL_M=100` | 定数(天神の原点・地盤高) | 小 |
| 2 | 空間 | `engine/solar.py:48-49` | 原点の写し `LAT`・`LON`(日照の計算) | 定数(`world_crs.json` から読む形) | 小 |
| 3 | 空間 | `engine/economy_stage2.py:83-86` | 原点・`M_PER_DEG_*`・`CELL_M` の写し(build を import できないため) | 定数(同上) | 小 |
| 4 | 空間 | `build/field/w13_weather.py:58-60` | `LAT=C.ORIGIN_LATLON[0]`・`TZ_OFFSET_MIN=540` | 不要(原点に従う・時差は全国共通) | — |
| 5 | 空間 | `build/geo/w11_station_exits.py:36,39` | 駅の範囲 `BBOX=(35.6505, 139.6905, 35.6685, 139.7115)`+余白 300 m | 定数 | 小 |
| 6 | 空間 | `build/geo/w11_station_exits.py:42-43`・`build/geo/w5_entrances.py:38` | ゲートの期待値 出口 45・フロアガイドの結び 22・駅出口 45 | 定数(場所ごとの期待値) | 小 |
| 7 | 空間 | `build/geo/w2_cells.py:36,38` | `EXPECTED_BLOCK_EULER=1242`・`EXPECTED_CELLS_GL=453` | 定数 | 小 |
| 8 | 空間 | `build/lang/w15_cell_static.py:58,71` | `EXPECTED_CELL_ROWS=520`・B2 の予算の導出に 520 セル | 定数 | 小 |
| 9 | 空間 | `build/geo/w1_walk_graph.py:38-39,46` | 入力 `shibuya_osm_wide_v8.json`・`floorguide_shibuya.json`・総延長 186,741 m のゲート | データ+定数。v8 の JSON を作る上流の手順は `src/` の中に見当たらない | 中 |
| 10 | 空間 | `build/geo/w0_crs.py:33`・`build/geo/common.py:302`・`build/geo/w4_heights.py:33,36`・`build/geo/w5_entrances.py:34` | 同じ OSM の JSON・`building_heights_shibuya.json` | データ | 小 |
| 11 | 空間 | `build/geo/w6_poi_org.py:54-55,65,67` | POI の入力(OSM v8+`poi_patch_shibuya.json`)・`EXPECTED_POI=2337`・結合率 0.688 | データ+定数 | 中 |
| 12 | 空間 | `build/field/w7_planspec.py:69` | `EXPECTED_POI_ROWS=2337` | 定数 | 小 |
| 13 | 空間 | `build/space/sources.py:45` | PLATEAU の道筋 `13113_shibuya-ku_pref_2025_citygml_1_op/udx` | データ(福岡市の PLATEAU の道筋) | 小 |
| 14 | 空間 | `build/space/navmesh1.py:1009-1010`・`build/space/sources.py:293-294` | 歩行空間ネットワーク `shibuyananbu_*_2020.geojson` | データ(天神に同じ形の網があるかは R-A ① の範囲・未確認) | 中 |
| 15 | 空間 | `build/space/navmesh1.py:98` | `TRUNK_FUNCTIONS=(2, 3)`=PLATEAU の tran:function(国道・都道府県道) | 不要(全国共通の符号) | — |
| 16 | 空間 | `build/vis/w9_shadow.py:66-67` | 影を作る日 `SHADOW_DATES`(2026-07-28・07-13〜19) | 定数(世界の時点に従う) | 小 |
| 17 | 空間 | `build/field/w13_weather.py:48-55` | アメダス 東京 47662(44132・北の丸公園)・窓 2025-09-01〜2026-08-31・ファイル名 `tokyo47662_*` | データ+定数(福岡の地点。番号は親が確認) | 小 |
| 18 | 空間 | `build/field/w10_noise.py:66-69` | 道路交通センサス `kasyo13.csv`(13=東京都)・都の常時監視点 `tokyo_noise/r5_joji_kanshi_points.csv` | データ+コード(常時監視点の CSV は都の形。福岡県・福岡市の形は未確認) | 中 |
| 19 | 空間 | `build/field/w10_noise.py:139,347,575` | `CITY_CODE={"渋谷区":"13113","目黒区":…}`・渋谷区のセンサスの行で既定の交通量の表を作る | 定数 | 小 |
| 20 | 空間 | `build/field/road_names.py:82,231` | 区の優先順 `CENSUS_WARDS=("13113","13110","13103","13112","13104")`・「区道」の語だけで市区町村道を判定 | 定数+コード(「市道」「町道」を足す) | 小 |
| 21 | 空間 | `build/field/w10_ruler.py:85-86,160,434` | 境界 `r2ka13113`・住所の正規表現 `^(?:東京都)?(.+?区)(.*)$`・既定 `ward="渋谷区"` | データ+コード(県名の前置き・市の区の形) | 中 |
| 22 | 空間 | `engine/processes/traffic.py:47-66` | `KLASS_Q12`・`KLASS_Q24`=W10 の渋谷区のセンサスの既定値の手の写し | 定数(W10 の出力から読む形) | 小 |
| 23 | 制度 | `build/field/w7_planspec.py:78-160` | `LAW_CAPS`=風営法+東京都の施行条例(4 条の 3・5 条・11 条・13 条・15 条)・都の青少年条例 16 条・「営業延長許容地域=渋谷区 26 町丁」 | データ(規則の表へ)+コード(W7 が表を読む) | 大 |
| 24 | 制度 | `build/field/w7_planspec.py:122` | 深夜酒類「渋谷駅周辺は商業地域」=用途地域を見ずに禁止の窓を当てない | データ(用途地域の層)+コード | 中 |
| 25 | 制度 | `economy/anchors.py:105` | `MIN_WAGE_HOURLY=1_226`(東京都・R7.10.3 の直書き・つなぎ `BR-MIN-WAGE-HOURLY-1226`) | 定数 | 小 |
| 26 | 制度 | `economy/anchors.py:225-226,243,258` | 規則の id `MIN_WAGE_RULE_ID="minimum_wage.tokyo"` | 定数+コード(管轄で id を引く) | 中 |
| 27 | 制度 | `economy/taxes.py:70-71,83-84` | id `resident_tax.special_collection_tokyo_ward`・`health_insurance.kyoukai_tokyo`・`…adjustment_credit_tokyo_ward`・`…non_taxable_tokyo_ward` | 定数+コード(同上) | 中 |
| 28 | 制度 | `economy/taxes.py:389-393,439` | 住民税=`income_levy_rate_metro`+`income_levy_rate_ward`・均等割=都+区+森林環境税・調整控除=`rate_metro`+`rate_ward` | データ(欄の名を「都道府県/市区町村」の語へ・政令市の配分の違いは推測=親が一次確認) | 中 |
| 29 | 制度 | `economy/taxes.py:446` | 非課税の限度(扶養 0・23 区) | データ(市の条例の額) | 小 |
| 30 | 制度 | `perception/templates.py:299-302` | 役割知識の固定文=渋谷駅周辺の路上飲酒の禁止(18〜5 時)・客引きの防止地区(半径 700 m・過料 5 万円) | データ(管轄で引く知識の表)。知覚の文が変わる=LLM の入力が変わる | 中 |
| 31 | 制度 | `perception/templates.py:303-305` | 遺失物(24 時間・7 日)・深夜営業の制限(23〜6 時・8 業種) | 遺失物=国(不要)・深夜営業=条例(都道府県)なので要確認 | 小 |
| 32 | 制度 | `agents/population.py:87`・`build/pop/w16_population.py:1374` | 議員=渋谷区議会の定数 34 | 定数 | 小 |
| 33 | 制度 | `engine/rights/initial.py:10` | 営業許可の行 0(渋谷区の一覧は未取得) | データ | 小 |
| 34 | 制度 | `engine/calendar.py:72,77`・`build/field/common.py:165` | 内閣府の祝日 CSV(全国)・世界の時点 `DEFAULT_WORLD_START=2026-07-13` | 不要(祝日)・定数(時点は場所ごとに選べる形がよい) | 小 |
| 35 | 制度 | `docs/design/rules-table.json:36,64,99,337,376,533,567,915,1018,1051` | id に `tokyo`・`shibuya` を含む 10 行(§3) | データ | 中 |
| 36 | 人口と事業所 | `build/pop/w21_sources.py:73-74` | `WARD_CODE="13113"`・`WARD_NAME="13113_渋谷区"` | 定数 | 小 |
| 37 | 人口と事業所 | `build/pop/w21_sources.py:124-300` | 材料の表のファイル名と md5(`…東京都_渋谷区抽出.json`・東京都 外国人人口・全国家計構造調査の東京都の 2 表・経済センサス 第 28 表(渋谷区)) | データ(台帳を場所ごとに) | 中 |
| 38 | 人口と事業所 | `build/pop/w16_population.py:59-75,111` | 国勢調査の渋谷区抽出の JSON 3 本・PT 渋谷コア `docs/bench/pt_shibuya/pt6_summary_core0241.json`・`WARD_AREA="13113"` | データ+定数(PT は北部九州圏の調査があるかを R-A ① で確認・未確認) | 中 |
| 39 | 人口と事業所 | `build/pop/attr_fns.py:125,130` | 勤務地・通学地の語 `in_ward`・`other_tokyo`・`other_prefecture` | 定数(語を「区内/都道府県内/外」の一般の名へ) | 中 |
| 40 | 人口と事業所 | `build/pop/attr_fns.py:702-703,764,929` | 資産の水準 `tokyo_ratio_sav`・`tokyo_ratio_debt`・住民の常住地 `"13113"` | データ+定数 | 小 |
| 41 | 人口と事業所 | `build/pop/w21_build_b.py:188-189,296`・`build/pop/w21_outside.py:215`・`build/pop/w21_build_c.py:167` | `"13113"` と「渋谷区(舞台の外の町丁目=輪)」の直書き | 定数 | 小 |
| 42 | 人口と事業所 | `build/pop/w21_build_c.py:156-157`・`build/pop/w21_check.py:51-56` | 東京都 外国人人口(住民基本台帳)第 3 表・第 1 表の読み口 | データ+コード(福岡県・福岡市の表の形は別・未確認) | 中 |
| 43 | 人口と事業所 | `build/pop/w21_frame.py:45-80` | 1 日の枠の値(外から来る 185,000〜250,000・訪日 43,000〜85,000・乗換 700,000〜800,000・JR 通過 460,000) | データ(答申の値を場所ごとに) | 中 |
| 44 | 人口と事業所 | `build/pop/w21_outside.py:43-48` | 訪日の国籍 `JNTO_2025`(全国) | 不要(全国の表) | — |
| 45 | 人口と事業所 | `build/sched/w20_calendar_1a.py:482,499,525,541` | 行の選び `"13_東京都"`(社会生活基本調査)・`"131_特別区部"`(就業構造基本調査)・`"13113"`(経済センサス) | 定数(地域の鍵) | 小 |
| 46 | 人口と事業所 | `build/pop/w21_persona.py:362-363,663-716` | ペルソナの文「渋谷区内」「東京都の外」「渋谷に来て」 | 定数(地名の差し込み) | 小 |
| 47 | 人口と事業所 | `build/sched/w17_schedule.py:243-266,523,556,565`・`build/sched/trial.py:712,738-740,815-817,1076,1103-1125` | LLM の日課の指示文に「渋谷の中/外」「渋谷に泊まる」 | 定数(地名の差し込み)。W17 の生成のやり直しが要る | 小(コード)・大(生成) |
| 48 | 人口と事業所 | `build/sched/vocab.py:240` | 場所語の写像 `"渋谷": "路上"` | 定数 | 小 |
| 49 | 人口と事業所 | `economy/anchors.py:108-129` | 渋谷区の 1 事業所の年商・従業者 516,541・事業所 27,624・ごみ 119.6 t/日 | データ | 小 |
| 50 | 人口と事業所 | `economy/entry_capital.py:117` | 1 事業所あたり年商(渋谷区 13113) | データ | 小 |
| 51 | 人口と事業所 | `build/geo/w6_poi_org.py:56,66` | `organizations_shibuya_census.json`・`EXPECTED_ORGS=9872` | データ+定数 | 中 |
| 52 | 人口と事業所 | `engine/processes/logistics.py:51,53,103` | 宅配 `PARCELS_PER_DAY_WARD=27_000`・区の面積 `SHIBUYA_WARD_AREA_M2=15.11e6` | 定数 | 小 |
| 53 | 人口と事業所 | `engine/body/rules.py:73,94` | 倒れる率 3.0/1 万体・日(東京消防庁の件数から丸めた) | 定数 | 小 |
| 54 | 人口と事業所 | `build/audit/w19_freeze.py:43,54-57,165` | holdout の名 `shibuya_jinryu`・KDDI(渋谷区オープンデータ)・OSM の JSON | データ(天神の holdout=福岡市の歩行者通行量調査) | 中 |
| 55 | 運行 | `world/assets.py:812-822` | `RAILWAY_TO_LINE`=ODPT の railway id → 9 線の名(W11 と W12 を結ぶ唯一の表) | データ(資産の欄へ) | 小 |
| 56 | 運行 | `world/assets.py:825,1236-1251` | `HOME_STATION_TITLE="渋谷"`・ホームは 1 駅だけを探す | コード | 大 |
| 57 | 運行 | `engine/processes/rail.py:45,583`・`engine/presence.py:1761` | 「渋谷は 1 駅」=帰りの便は線を選ばない | コード(天神は複数の駅=天神・天神南・西鉄福岡(天神)。駅の数は R-A ① で確認) | 大 |
| 58 | 運行 | `engine/processes/rail.py:131-135` | `TERMINAL_LINES=("銀座線","井の頭線")` | 定数(資産の欄) | 小 |
| 59 | 運行 | `engine/processes/rail.py:142` | `FARE_YEN=180`(運賃表は未取得) | データ(事業者の運賃表) | 中 |
| 60 | 運行 | `engine/processes/rail.py:163-172,193` | 1 列車の定員 8 線・表に無い線 1,200 | データ | 小 |
| 61 | 運行 | `engine/processes/rail.py:180-191` | 混雑率の上限 8 線・東京圏 31 区間平均 139% | データ | 小 |
| 62 | 運行 | `engine/resolve.py:238,245` | 乗車待ちの打ち切り `BOARD_WAIT_LIMIT_TICKS=30`(渋谷の間隔 2.2〜5.0 分から) | 定数 | 小 |
| 63 | 運行 | `build/field/w12_external_nodes.py:126-218` | 方面ノード 10(`ext_rail_tokyu_denentoshi` … `ext_walk_gate`・`ext_road_gate`)と事業者・方面の名 | データ(事業者の表) | 中 |
| 64 | 運行 | `build/field/w12_external_nodes.py:107-111` | 大都市交通センサスの 3 表・ODPT の駅別乗降 `odpt_passenger_survey/shibuya.json`・PT 渋谷コア | データ。福岡が大都市交通センサスの対象かは未確認(推測では対象外) | 大 |
| 65 | 運行 | `build/field/w12_external_nodes.py:74,113-117,242-249` | メトロ 3 線の時刻表ファイル・等間隔のピーク本数(山手 18 など) | データ | 小 |
| 66 | 運行 | `build/field/w12_real_timetables.py:96,145,148,183-226,228,237` | 世界の時点・`HOME_STATION="渋谷"`・`FOLD_LINES`・手で入手した表 13 本の仕様(JR・東急・京王)・銀座線の ODPT の仕様・版の宣言 | データ+コード(GTFS の読み口が無い) | 大 |
| 67 | 運行 | `build/field/w12_rail_events.py:104-137` | 地下鉄 3 線と直通の相手・ODPT の駅 id → 行き先の名の手の表・種別の名 | データ+コード | 中 |
| 68 | 運行 | `build/geo/w11_station_exits.py:45-55,83-85` | ODPT の駅ファイル 9 本・「座標を持つのはメトロだけ」の扱い | データ+コード(GTFS の stops か OSM から) | 中 |
| 69 | 運行 | `build/pop/w16_population.py:121-125` | 指令 24=鉄道 4 事業者(JR東・東急・京王・メトロ)× 3 席 × 2 交代 | 定数(事業者の数から) | 小 |
| 70 | 運行 | `engine/processes/logistics.py:63-65` | バス 10 分間隔・6〜23 時(時刻表なし) | データ(バスの時刻表) | 小 |
| 71 | 判断(共通) | `perception/templates.py:326`・`perception/renderer.py:1081` | B0 の頭「あなたは渋谷の街にいる一人の人物です」 | 定数(地名の差し込み)。LLM の入力が変わる | 小 |
| 72 | 判断(共通) | `build/lang/common.py:333-340`・`build/geo/poi_class.py:201`・`engine/wom.py:99` | 固有名詞の既知語(渋谷・道玄坂・東急・山手線…)・待ち合わせ名所の語(ハチ公・モヤイ・忠犬)・支店の接尾辞(渋谷駅前店…) | 定数(場所の語の表) | 小 |

注: 層を数えるとき #4・#15・#44 は「変更不要」の確認行として数えない(§0 の 69 か所)。#34 は祝日=不要・時点=定数。
注: 識別子の grep(`shibuya|tokyo|hachiko|渋谷|東京|tokyu|東急|keio|京王|宮益|道玄坂|hikarie|ヒカリエ|scramble|スクランブル`)の当たりは 2,199 行。`from shibuya`・`shibuya.<層>`・`SHIBUYA_<切替口>` を除くと 608 行。切替口の環境変数 `SHIBUYA_*`(46 種)は製品名の前置きで場所の固定ではない。例外は `SHIBUYA_WARD_AREA_M2`(#52)だけ。

### §1 の補い(場所の語はあるが、入れ替えの対象にしなかったもの)
- `engine/arbiter.py:71`・`engine/run.py:1092-1115`: 東京都 平日の起床率 a(h)(社会生活基本調査 第 4-1 表)。照合の材料として文に書いてあるだけで、値は掛けていない。照合の道具(`tools/c7`)の側で場所ごとに差し替える。
- `world/assets.py:169`: ホームの滞留密度 3.30 人/m²(計測の 3 駅に銀座線渋谷駅を含む)。文献の値で、場所の固定ではない見立て。
- `engine/processes/civic.py:76`: 定時の報道の文「鉄道各線は平常どおり運行しています」。全国で通る文。
- `engine/processes/rail.py:155`: `EXTERNAL_HOME_PERMILLE=120`(mock の日課に方面が無いときの代わり)。場所の値ではない。
- `build/audit/w18_coverage.py:80,108`: カタログの注(渋谷区全域 27,624・149,967)。監査の文だけ。
- `build/field/w12_real_timetables.py:118`: `USE_ODPT_CHALLENGE=True`(京王の ODPT チャレンジ枠の切替口)。運行の材料の許諾の印で、天神では別の印になる。
- `engine/calendar.py:19,85`: 気象庁の季節の区分(全国)。
- `build/pop/w21_outside.py:60-66`: 浜松市の区の再編の写し(全国の市区町村の符号の対応)。場所の固定ではない。

## §2 層ごとのまとめ

### 空間(座標で引く)
- 今の固定: 世界の原点と平面近似(#1〜3)・範囲(#5)・入力のファイル名(#9〜14・17・18)・期待値のゲート(#6〜8・11・12)。
- 入り口: 構築側は定数(ファイル名と期待値)。エンジン側はデータ(`--world` の世界資産・`world_crs.json`)。
- 天神への最小の変更: 原点と範囲と入力の道筋と期待値を「場所の設定」1 つに出し、W0〜W5・nav1 を天神の材料で回す。平面近似 `111320·cos(lat)` は都市の範囲なら共通で使える。都市圏の広さ(数十 km)で誤差がどこまで出るかは未計測。
- 原点の写しが 3 か所ある(#1〜3)。値を `world_crs.json`(W0 が出す)から読む形にそろえると、場所の切替が 1 か所で済む。

### 制度(管轄=国 → 都道府県 → 市区町村と時点で引く)
- 今の固定: 規則の表の id の名前(#35)・読み手の id 定数(#26・27)・税の欄の名(#28)・表の外の法の上限(#23・24)・知覚の固定文の条例(#30・31)。
- 入り口: 規則の表=データ。id の選びは定数。W7 の法の上限と知覚の条例はコードの中の表。
- 天神への最小の変更: 規則の表に `jurisdiction` を足し、読み手は「id+管轄+日付」で引く(§3)。国の 17 行はそのまま使える。残りの 13 行は福岡県・福岡市(と協会けんぽの福岡支部)の行を足す。
- 時点はすでに表にある(`asof`・`asof_basis`=`engine/rules/table.py:9-12,136-158`)。

### 人口と事業所(都市圏)
- 今の固定: 市区町村の符号 `13113`(#36・40・41・45)・東京都の表の読み口(#37・42)・枠の値(#43)・アンカーの値(#49・50)・ペルソナと日課の文の地名(#46・47)。
- 入り口: 材料の台帳(`build/pop/w21_sources.py`)=データ。符号と語は定数。都の表の形はコード。
- 天神への最小の変更: 符号と地名を場所の設定へ出し、国勢調査・経済センサスは全国で同じ形なのでファイルの差し替えで済む。都の独自の表(外国人人口・社会生活基本調査の都の行)は福岡県の表の読み口が要る。
- 作る単位を都市圏にするなら、今の「区+輪(区の残りの町丁目)+外」の 3 帯(`build/pop/w21_frame.py:45-80`・`build/pop/w21_outside.py:17-20`)の「区」を「都市圏の中の市区町村の集まり」へ広げる設計が要る(本書の範囲の外・親の判断)。

### 運行(事業者)
- 今の固定: 線の名と事業者(#55・63・67・69)・線ごとの表(#58〜61)・時刻表の読み口(#64〜66・68)・1 駅の仮定(#56・57)。
- 入り口: 線ごとの表と 1 駅の仮定はエンジンのコード。時刻表は構築側のデータ+手の仕様表。
- 天神への最小の変更: (1) 線ごとの表(定員・混雑率・終端・運賃)を W12 の資産の欄へ移す。(2) GTFS の読み口を 1 本足す(福岡市地下鉄と西鉄の GTFS の有無は R-A ①)。(3) 複数の駅を持てるようにする(ホームのセルの探し方と帰りの便の選び方)。

### 判断の仕組み(全部の場所で共通)
- `engine/decision/`・`llm/`(`llm/contract.py:956` の駅の正規表現は全国で通る形)・`engine/memory*`・`engine/space/nav1.py`(物理の定数=歩行の速さ・勾配・階段)に場所の固定は見当たらない。
- 例外: 知覚の固定文の地名と条例(#30・71)・固有名詞の語の表(#72)。いずれも LLM の入力の文になるので、差し替えると判断の入力が変わる。

## §3 規則の表の「管轄」の欄の見立て

`docs/design/rules-table.json` の形は `shibuya.rules-table/2`。行の欄は `id`・`kind`・`asof`・`asof_basis`・`source`・`params`・`applies_to`・`note` の 8 つ(`engine/rules/table.py:177`)。管轄の欄は無い(`jurisdiction`・「管轄」の語は `src/` に見当たらない)。知らない欄は読みで止まる(`engine/rules/table.py:178-180`)。

管轄は本書の仮の振り分け(推測)。「時点」=`asof` は全行にある。「読み手」は grep で見つけた所。

| 行 | 表の行 | id | 管轄(仮) | 時点 | 読み手 |
|---|---|---|---|---|---|
| 1 | 6 | `consumption_tax.standard_rate` | 国 | asof | `economy/anchors.py:276` |
| 2 | 36 | `minimum_wage.tokyo`(2024-10-01) | 都道府県(地域別最低賃金) | asof | `economy/anchors.py:243,258` |
| 3 | 64 | `minimum_wage.tokyo`(2025-10-03) | 都道府県 | asof | 同上 |
| 4 | 99 | `minimum_wage.tokyo`(2026-10-01) | 都道府県 | asof | 同上 |
| 5 | 133 | `late_night_alcohol.residential_ban` | 国(風営法)+都道府県(施行条例 15 条) | asof(lower_bound) | 見当たらない(W7 の `LAW_CAPS` が別に持つ) |
| 6 | 164 | `labor.weekly_rest_day` | 国 | asof | `engine/calendar3/layer.py:160`・`build/sched/w20_calendar_1a.py:1003` |
| 7 | 185 | `food_business.licence` | 国(食品衛生法)+保健所を置く市区町村(特別区=区長) | asof(lower_bound) | 見当たらない |
| 8 | 226 | `building_lease.termination_notice` | 国 | asof(lower_bound) | 見当たらない |
| 9 | 260 | `labor.statutory_hours` | 国 | asof(lower_bound) | `engine/calendar3/layer.py:159` |
| 10 | 282 | `labor.overtime_premium` | 国 | asof(lower_bound) | `economy/taxes.py:679` |
| 11 | 304 | `road_use.police_permit` | 国(道路交通法)+都道府県(警察・手数料) | asof(lower_bound) | 見当たらない |
| 12 | 337 | `road_occupancy.shibuya_ward_road` | 道路管理者ごと(国道=国・都道=都・区道=区)。料金の表は区 | asof | 見当たらない |
| 13 | 376 | `outdoor_ad.tokyo_permit` | 都道府県の条例(政令市が独自の条例を持つかは未確認) | asof(lower_bound) | 見当たらない |
| 14 | 418 | `consumption_tax.reduced_rate` | 国 | asof | `economy/taxes.py:641` |
| 15 | 449 | `consumption_tax.invoice_rounding` | 国 | asof | `economy/taxes.py:616` |
| 16 | 470 | `income_tax.withholding_monthly` | 国 | asof | `economy/taxes.py:248` |
| 17 | 533 | `resident_tax.special_collection_tokyo_ward` | 都道府県+市区町村(率と均等割) | asof | `economy/taxes.py:249` |
| 18 | 567 | `health_insurance.kyoukai_tokyo` | 事業者(協会けんぽ)× 都道府県支部 | asof | `economy/taxes.py:250` |
| 19 | 685 | `child_support_levy.rate` | 国(全国一律) | asof | `economy/taxes.py:251` |
| 20 | 706 | `pension.employees_rate` | 国 | asof | `economy/taxes.py:252` |
| 21 | 781 | `employment_insurance.rate_general` | 国 | asof+`params.valid_until` | `economy/taxes.py:253` |
| 22 | 820 | `credit.total_volume_cap` | 国 | asof(lower_bound) | `economy/taxes.py:655` |
| 23 | 861 | `credit.interest_cap` | 国 | asof(lower_bound) | `economy/taxes.py:666` |
| 24 | 886 | `national_pension.premium` | 国 | asof+`params.valid_until` | 見当たらない |
| 25 | 915 | `national_health_insurance.shibuya` | 市区町村 | asof | 見当たらない |
| 26 | 952 | `consumption_tax.filing_deadline` | 国 | asof(lower_bound) | `economy/taxes.py:632`(つなぎとして読む) |
| 27 | 984 | `resident_tax.basic_deduction` | 国(地方税法の額) | asof(lower_bound) | `economy/taxes.py:260` |
| 28 | 1018 | `resident_tax.adjustment_credit_tokyo_ward` | 都道府県+市区町村(率の配分。政令市は配分が違う=推測) | asof(lower_bound) | `economy/taxes.py:261` |
| 29 | 1051 | `resident_tax.non_taxable_tokyo_ward` | 市区町村(条例の額) | asof(lower_bound) | `economy/taxes.py:262` |
| 30 | 1084 | `child_care_contribution.rate` | 国 | asof(lower_bound) | `economy/taxes.py:263` |

数え(仮の振り分けで): 国 17 行(1・6・8〜10・14〜16・19〜24・26・27・30)・都道府県 4 行(2〜4・13)・国+都道府県 2 行(5・11)・国+市区町村 1 行(7)・道路管理者ごと 1 行(12)・都道府県+市区町村 2 行(17・28)・市区町村 2 行(25・29)・事業者 × 都道府県 1 行(18)=30 行。管轄を 2 つ以上持つ行は 7 つ(5・7・11・12・17・18・28)。読み手のいない行は 8 つ(5・7・8・11・12・13・24・25)。
既存の場所の印: `params.area="東京都"`(行 2〜4)・`params.issuer`(行 7・11・12・13)。どちらも自由な文で、読み手は使っていない。

### 欄を足す形の案(案として書くだけ)
- 案 A(1 欄): `jurisdiction`=`{"level": "national|prefecture|municipality|operator", "code": "13|13113|40|40130|…", "name": "…"}`。全国地方公共団体コードを使う。国は `code: "00"`。事業者は `level: "operator"`+`code` に事業者の名(協会けんぽの支部なら `prefecture` の符号を並べて持つ)。
- 時点: `asof` が「効く最初の日」なので `effective_from` は要らない見立て。終わりは「次の版の asof」で決まる(`engine/rules/table.py:242-249`)。`params.valid_until`(行 21・24)だけ表の外にある。足すなら `effective_until` を任意の欄にする。
- 引き方: `Rules.get(id, asof)`(`engine/rules/table.py:242`)を `get(id, asof, place)` にし、place の符号から 市区町村 → 都道府県 → 国 の順で最初に当たる行を返す。id から `.tokyo`・`.shibuya`・`_tokyo_ward` を外す(例 `minimum_wage`・`resident_tax.special_collection`)。
- 境目の行(管轄を 2 つ持つ行)は、行を 2 つに割る(国の法の行と、条例の値の行)か、`jurisdiction` を並びにするか。決めるのは親。

## §4 分離の見積り

目安の数え方: §1 の行を「入れ替えるもの」で分け、ファイル数は §1 の場所の重なりを除いて数えた。行数は変える定数の行と読みの口の行の見込み(推測・±50%)。

### (a) データの差し替えだけで済む所
- エンジン側の世界資産の読み(`world/assets.py` の読み口・`engine/space/nav1.py`・知覚・判断・記憶)。`--world data/world/<場所>` で切り替わる(`cli.py:843`・`engine/run.py:2572`)。
- 規則の表の国の 17 行・祝日 CSV・訪日の国籍(#44)・PLATEAU の符号(#15)。
- 構築の段のうち入力が全国共通の形のもの: W3(距離)・W8(見え方)・W9(影=日付は定数)・W2 の算法・nav1 の構築の算法。
- 目安: 変更 0 ファイル(道筋を設定へ出した後)。

### (b) 定数を設定ファイルに出す所
- 空間: #1〜3・5〜13・16・17・19・22 → 約 17 ファイル・60〜100 行。
- 制度: #25〜27・29・32 → 約 4 ファイル・20 行。
- 人口と事業所: #36・39〜41・45〜53 → 約 16 ファイル・60〜100 行。
- 運行: 定数 #58・62・69 と、線ごとの表 #55・60・61・65・70(設定か W12 の資産の欄へ)→ 約 7 ファイル・50〜80 行。
- 判断の入力の文: #30・71・72 → 4 ファイル・20〜40 行。
- 合計 約 45 ファイル・200〜350 行。形は「場所の設定」1 本(既定=渋谷の今の値)。

### (c) コードの分岐が要る所
1. 複数の駅(#56・57): `world/assets.py`・`engine/processes/rail.py`・`engine/presence.py`・`engine/resolve.py`。大(数百行)。
2. GTFS の時刻表と駅の読み口(#64〜68): W11 と W12 の 4 ファイルに新しい読み口。大(300〜600 行)。
3. 生成の重みの元(#64): 大都市交通センサスと PT が無い場合の代わり。材料しだい(R-A ①)。大。
4. 管轄で引く規則の表(§3): `engine/rules/table.py`・`economy/anchors.py`・`economy/taxes.py`・`engine/calendar3/layer.py`。中(100〜200 行)。
5. W7 の法の上限を規則の表へ(#23・24): `build/field/w7_planspec.py`。中〜大。
6. 都道府県の独自の表の読み口(#18・42): `build/field/w10_noise.py`・`build/pop/w21_build_c.py`・`build/pop/w21_check.py`。中。
7. 住所と道路名の正規表現(#20・21): `build/field/w10_ruler.py:160`・`build/field/road_names.py:231`。小。
8. 税の欄の名の一般化(#28): `economy/taxes.py:389-393,439` と表の欄の名。小〜中。

### 層ごとの数のまとめ(§1 の行から・目安)

| 層 | §1 の行 | (a) データ | (b) 定数 | (c) コード |
|---|---|---|---|---|
| 空間 | 20 | 4(#9・10・13・14) | 13 | 3(#18・20・21) |
| 制度 | 13 | 4(#29・33・34・35) | 3 | 6(#23・24・26・27・28・30) |
| 人口と事業所 | 18 | 7 | 9 | 2(#42・47 の生成) |
| 運行 | 16 | 7 | 3 | 6(#56・57・64・66・67・68) |
| 判断(共通) | 2 | 0 | 2 | 0 |

注: 1 行が 2 つの区分にまたがるとき(「データ+コード」など)は重い方に数えた。数は本書の振り分けで、試算の幅は大きい。

### 既定の結果(19 構成の byte-check)を変えずに進める順
byte-check が比べるのは状態のハッシュ(`cli.py:598-623` の `checkpoints_payload`=`agents_hash`・`world_hash`・`population_hash`・`schedule_hash`・`combined`)と見立てた。manifest の欄(`rules_version` など)は含まない見立て(親の確認=§5 の 2)。

1. 整理の段 R0(1 バイト不変): 原点の写し 3 か所(#1〜3)を 1 つの読みにそろえる。値は同じ。
2. 整理の段 R1(1 バイト不変): エンジン側の定数(#22・52・53・55・58・60〜62・70)と知覚の文(#30・71)と語の表(#72)を「場所の設定」へ出す。既定値=今の値。文字列が 1 字でも違えば LLM の入力が変わるので、組み立てた文の sha を前後で比べる試験を先に足す。
3. 整理の段 R2(状態は不変・記録の欄は変わる): 規則の表に `jurisdiction` を足す(schema 3)。表の sha=`rules_version`(`engine/rules/table.py:278-280`)が変わる。id を改名すると計器の出どころの文字列(`economy/stage2.py:658` の `"rules:minimum_wage.tokyo@…"`)も変わる=観測の節が変わる。状態のハッシュは変わらない見立て。
4. 整理の段 R3(世界資産は不変): 構築側の定数(#5〜13・16・17・19・36〜41・45〜51)を設定へ出す。資産の中身は同じだが、段の `param_hash`・`input_hash`(`build/geo/common.py:145,154`)が変わると `build_manifest.json` の行が変わる。設定を hash に入れるかは親の判断。
5. 改良の段(天神のための新しい道・渋谷の既定は通らない): (c) の 1〜8。渋谷の既定の道は分岐の既定側に残す。

## §5 親に確かめてほしい点

1. 「場所の設定」の置き場: Python の定数の 1 モジュール(`core/` の下)/ 世界資産の中の JSON(W0 が出す `world_crs.json` の隣)/ `docs/design/` の JSON。エンジンは build を import できない(`engine/economy_stage2.py:82` の注)ので、世界資産の中に置くとエンジンと構築の両方から読める。
2. byte-check 19 構成が `rules_version` と計器の出どころの文字列を比べるか。比べるなら §4 の R2 は 1 バイト不変ではない。
3. 規則の id の改名(`minimum_wage.tokyo` → `minimum_wage`+管轄)をするか。改名はつなぎの台帳の `rule_id`(1 行・`BR-MIN-WAGE-HOURLY-1226`)と `economy/taxes.py`・`economy/anchors.py` の定数に及ぶ。
4. 管轄を 2 つ以上持つ行(§3 の 5・7・11・12・17・18・28)を割るか、並びで持つか。
5. 世界の単位: 場所ごとに別の世界資産(`data/world/<場所>/`)にするか、1 つの世界に複数の場所を持つか。都市圏ごとに作る(回答 10-25 §1-1)なら、人口の「区+輪+外」の 3 帯の作り直しが要る。
6. 複数の駅(#56・57)は改良の段になる。設計者の指紋の扱い(CLAUDE.md §2-6)で先に聞く項目か。
7. LLM で作った資産(W14 の看板・W15 のセルの文・W17 の日課)は天神で作り直しになる=GPU のランが要る。順番と予算。
8. W7 の法の上限(#23)を規則の表へ移すか。移すと W7 の入力が変わる(W7 の段の hash)。
9. 福岡の制度の値(政令市の住民税の配分・非課税の限度・屋外広告物の条例・国民健康保険)と、大都市交通センサス・PT の福岡の有無は、本書では確かめていない。一次確認の発注を別に出すか(R-A ①・②の範囲か)。

## §6 読んだ所の一覧

- 発注: `docs/design/v2-answers-2026-10-25.md:1-47,264-272`。
- 一覧の grep: `src/shibuya/**/*.py` 全体(識別子の当たり 2,199 行・絞って 608 行・`SHIBUYA_*` 46 種・`13113|EPSG|35.6…|139.[67]…|BBOX|WARD_CODE|CITY_CODE`・`^EXPECTED_…=`・規則の id の文字列・`区部|特別区|23 区`・`1 駅|ホームセル`)。
- 空間: `build/geo/common.py:40-120,302`・`build/geo/w2_cells.py:36-38`・`build/geo/w11_station_exits.py:32-100`・`build/geo/poi_class.py:198-215`・`build/space/navmesh1.py:85-158,1000-1015`・`build/space/sources.py:1-50,238-260,290-295`・`engine/space/nav1.py:96-150`・`engine/solar.py:40-56`・`engine/economy_stage2.py:78-90`・`engine/regional_clock.py:10-20,51-62`・`build/vis/w9_shadow.py:25-81,248`・`build/field/w13_weather.py:48-60`・`build/field/w10_noise.py:66-72,136-141`・`build/field/road_names.py:80-90,217-231`・`build/field/w10_ruler.py:85-86,160`・`engine/processes/traffic.py:38-72`・`build/lang/common.py:328-340`・`build/lang/w15_cell_static.py:58,71`。
- 制度: `docs/design/rules-table.json`(全 30 行を Python で読んだ・id の行は grep)・`engine/rules/table.py:1-60,136-284`・`build/field/w7_planspec.py:60-160`・`economy/anchors.py:100-130,224-284`・`economy/taxes.py:59-92,248-265,389-446`・`economy/stage2.py:655-680`・`perception/templates.py:290-333`・`engine/calendar.py:72-77`・`agents/population.py:78-92`。
- 人口と事業所: `build/pop/w16_population.py:54-176,1370-1378`・`build/pop/w21_frame.py:45-80`・`build/pop/w21_outside.py:43-66`・`build/pop/w21_sources.py`(grep の当たり)・`build/pop/attr_fns.py`(同)・`build/sched/w20_calendar_1a.py`(同)・`build/sched/w17_schedule.py`(同)・`build/sched/trial.py`(同)・`engine/processes/logistics.py:47-70`・`engine/body/rules.py:53-94`。
- 運行: `engine/processes/rail.py:110-215`・`world/assets.py:160-175,805-830,1232-1251`・`engine/resolve.py:230-246`・`engine/presence.py:1755-1765`・`build/field/w12_external_nodes.py:67-260`・`build/field/w12_real_timetables.py:94-237`・`build/field/w12_rail_events.py:63-160`。
- 判断: `llm/contract.py:953-960`・`engine/decision/`(grep で場所の語なし)。
- 試験と記録の形: `cli.py:407,598-625,843`・`engine/run.py:2572`・`engine/manifest_sections.py:1-37,72`・`tools/instruments/anchor_gauge.py:330-345`。
- 台帳: `docs/design/bridging-ledger.json`(673 行・active 643・場所の語を `what`/`why` に含む active 52 行・`rule_id` のある行 1)。
- 世界資産: `data/world/v2/` の `ls`・`build_manifest.json`(段 W0〜W20 と出力の名)・`world_crs.json`・`nav1_meta.json`(鍵だけ)。ファイル名に場所の語は無い(場所は道筋 `data/world/v2` だけで決まる)。

## 親の一次確認(第339・2026-10-25・Fable 5.1)

- 引用の実在: 本文の `path:行` 182 か所を親のスクリプトで全部確かめた(ファイルが実在し、行番号が範囲の中)。無作為の 8 か所の行を実読=どれも本文の記述と合う(例: `build/geo/w5_entrances.py:38` `EXPECTED_STATION_EXITS = 45`・`build/field/w12_external_nodes.py:74` の半蔵門線と副都心線・`economy/taxes.py:389` の都と区の率)。
- 等級: 本書は**コードの洗い出し**(一次資料=リポのコード)。§3 の管轄の振り分けと §4 の見積りは筆者の見立て=未リサーチ(expedient)と本文に明記。福岡の制度の値は未確認(§5 の 9)。
- 親の判断: §5 の問いは回答 10-25 §1-1 の「規則の表に管轄の欄を足す(仮決定・R-A の後)」の確定のときにユーザーへ出す(PENDING §3 の仮決定の行)。実装は停止中=着手しない。
