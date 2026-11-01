# 第 2 期 2-3b 鉄道の実ダイヤ(W12 1.2.0・構築側だけ)

> 実行役(Opus 5.5)の記録。親の検収の前。commit していない。作業木 `2-3b/timetables`(土台 `f2405e3`)。
> 発注: 親(Fable 5.1)。正: [回答 10-13](../../../../design/v2-answers-2026-10-13.md) の 7(W12 の等間隔の推定を実ダイヤに置き換える)・[回答 10-13b](../../../../design/v2-answers-2026-10-13b.md) §2(銀座線は 9 月改正の版)・時刻表の記録 [README](../timetables/README.md) §7(版の宣言・成田エクスプレス・相鉄線直通・銀座線)。
> **エンジン不変**(`src/shibuya/engine/` の差 0 行)。世界の資産の差し替え(活性化)は 2-4 で親が行う。本体の `data/world/v2/` は書いていない(新しい資産は `data/world/v2_stage_2-3b/`)。
> 本書には件数・本数・版・md5 だけを書き、**発車の時刻は書かない**。ODPT チャレンジ枠(京王)の生の行は写さない。

## 0. 結論

- W12 の時刻表を **全 8 線とも実ダイヤ**にした(版 1.1.0 → **1.2.0**)。等間隔の推定で残る線は **0**(ゲート `equal_interval_lines_remaining`=0)。行は 9,014 → **6,273**。
- **土休 > 平日 の欠陥(第330 §6)は消えた**。前は等間隔の 5 線とも土休 > 平日だった。後は 8 線とも土休 ≦ 平日(ゲート `lines_holiday_gt_weekday`=0・§4)。
- 銀座線は 9 月改正の版(ODPT オープン枠の静的データ版 1・dct:issued 2026-09-19)。**世界の時点(2026-07-13)より後の版**と宣言した(§5)。渋谷発はユーザーの G01(9 月改正)の読み取りと時刻の多重集合で全件一致(平日 360・土休 305)。
- 方面ノード(`w12_external_nodes.parquet`)と生成の重み(`w12_generation_weights.parquet`)はバイト一致(動かない)。よって W16・W17 は作り直していない。
- **動いた量**(HEAD の資産 → 2-3b の資産・4 構成): 4 構成とも final が動いた(版上げの材料・§9)。manifest の `frozen_sources` で動いたのは W12 の時刻表の 1 行だけ(帰属がはっきりしている)。
- 切替口 `USE_REAL_TIMETABLES=False` で 1.1.0 の時刻表(parquet の sha256・params・input_hash・notes・ゲート)がそのまま戻ることを確かめた。ヘッダの `stage_version` は 1.2.0 のまま、expedients は等間隔の道の 1 行になる(検収 L2・H1=§13)。
- 親に確かめてほしい点(§12): 湘南新宿ラインを埼京線に畳んだこと・山手線の上り/下りの写像(推測)・発注の一覧の外の試験 5 本の直し・ライセンス台帳の行の案。

## 1. 作ったもの・変えたもの

| ファイル | 種類 | 中身 |
|---|---|---|
| `src/shibuya/build/field/w12_real_timetables.py` | 新規 | 実ダイヤの読み口。表の白い一覧 `USER_TABLES`(12 表)・方面の写像(docstring に表)・CSV の照らし(会社・路線・駅・方面・平日土休が一覧と違えば止まる)・臨時の特急を外す規則(◆ の確かめ)・畳み(`FOLD_LINES`)・重複の除去・ODPT の列車時刻表の読み(起点=渋谷)・版の宣言の表・入力の層(W19 用) |
| `src/shibuya/build/field/w12_external_nodes.py` | 変更 | 版 1.2.0。切替口 `USE_REAL_TIMETABLES`(既定 True)・`metro_timetables_in_use()`(実ダイヤでは半蔵門線・副都心線だけ)。時刻表の組み立てを実ダイヤに。派生(オフピーク比・ピーク本数・初終発)は実ダイヤ(全線・平日/土休それぞれ)から計算し直す。新しい出力 `w12_timetable_versions.json`。新しいゲート 6 つ。False の道は 1.1.0 と同じ |
| `src/shibuya/build/audit/w19_freeze.py` | 変更 | `SOURCE_FAMILIES` と `BUILD_INPUT_FAMILIES` に入力の層 3 つ(`user_timetables`・`odpt_challenge`・`odpt_static`)。資産の表は W12 が実際に読むファイルだけ(銀座線の 7 月の駅の時刻表は外れ、実ダイヤの入力 26 本が入る) |
| `tests/build_field/test_w12_real_timetables.py` | 新規 | 20 件(data 不要 17・data が要る 3)。§10 |
| `tests/_data_ids.py` | id を足す | `user_timetables`・`odpt_static` |
| `tests/build_field/test_w12_pm_peak_switch.py` | 直し(一覧の外) | `run()` を通す 2 件を `USE_REAL_TIMETABLES=False`(等間隔の道)で回す |
| `tests/build_field/test_field_pipeline.py` | 直し(一覧の外) | W12 の `source` の集まりを新しい値に・等間隔の行の土休/平日の検査を「残る線 0・土休 ≦ 平日」に・data の印に 2 id |
| `tests/build_audit/test_audit_units.py` | 直し(一覧の外) | `realworld_live/` の下で W19 に載るのは ODPT の静的データ版 1 だけ、の形に(日次の amedas は今のまま載らない)・docstring を直し、`odpt_rt` と別の日付の `odpt_static` の偽のファイルを置く負の対照を 1 本足した(検収 L1) |
| `tests/build_audit/test_audit_pipeline.py`・`tests/build_vis/test_vis_pipeline.py` | 直し(一覧の外) | data の印に 2 id(全段の構築が W12 の実ダイヤの入力を読むため) |
| `docs/design/bridging-ledger.json` | 行の出し入れ(親の許可・検収 H1) | W12#4〜#8・BR-W12-HOLIDAY-GT-WEEKDAY を removed・新しい宣言の行 9 つ・BR-W11-SHINSEN-EXIT と HD-engine.processes.rail-1af925f4 の外す段を 2-3c に(§13) |
| `src/shibuya/engine/bridging/ledger.py` | 1 行(親の指示) | 外す段の閉じた表 `PLAN_STAGES` に `2-3c` を足した(台帳の読み口=シミュレーションの挙動は変えない) |
| `tests/engine/bridging/test_bridging_ledger.py` | 直し(一覧の外) | 形ごとの数 expedients 139 → 143(§13) |
| 本書 | 新規 | 記録と golden(末尾) |

## 2. 使った表と使わない表(名だけ)

**使った表**(渋谷の発車・平日と土休の 2 ファイルずつ): JR_山手線_渋谷_内回り・JR_山手線_渋谷_外回り・JR_埼京線_渋谷_大宮方面・JR_埼京線_渋谷_大崎方面・JR_相鉄線直通_渋谷_相鉄線方面・JR_湘南新宿ライン_渋谷_北行・JR_湘南新宿ライン_渋谷_南行・東急_東横線_渋谷_横浜方面・東急_副都心線_渋谷_和光市方面・東急_田園都市線_渋谷_中央林間方面・東急_半蔵門線_渋谷_押上方面・京王_井の頭線_渋谷_吉祥寺方面(チャレンジ枠)。ほかに `JR_注記.final.csv`(◆ の確かめだけ)・ODPT オープン枠の静的データ版 1 の `traintimetable_TokyoMetro.json.gz`(銀座線)・今の 7 月の取得の `station_timetable_metro_hanzomon.json`・`station_timetable_metro_fukutoshin.json`。

**使わない表**(26 表):

| 理由 | 表 |
|---|---|
| 成田エクスプレス(湘南新宿ラインの表に 104 本とも含まれる=README §7) | JR_成田エクスプレス_渋谷_成田空港方面・JR_成田エクスプレス_渋谷_新宿方面 |
| 到着の表(渋谷の発車だけを使う) | 京王_井の頭線_渋谷_到着 |
| 渋谷の外の駅 | JR_山手線_原宿_内回り・JR_山手線_原宿_外回り・京王_井の頭線_神泉_吉祥寺方面・京王_井の頭線_神泉_渋谷方面・メトロ_副都心線_明治神宮前_和光市方面・メトロ_副都心線_明治神宮前_渋谷方面・メトロ_千代田線_明治神宮前_代々木上原方面・メトロ_千代田線_明治神宮前_北綾瀬方面・メトロ_千代田線_代々木公園_代々木上原方面・メトロ_千代田線_代々木公園_北綾瀬方面・小田急_小田原線_代々木八幡_小田原方面・小田急_小田原線_代々木八幡_新宿方面・メトロ_千代田線_表参道_代々木上原方面・メトロ_千代田線_表参道_北綾瀬方面・メトロ_半蔵門線_表参道_押上方面・メトロ_半蔵門線_表参道_渋谷方面・メトロ_銀座線_表参道_浅草方面・メトロ_銀座線_表参道_渋谷ゆき・東急_東横線_代官山_横浜方面・東急_東横線_代官山_渋谷方面・東急_田園都市線_池尻大橋_中央林間方面・東急_田園都市線_池尻大橋_渋谷方面 |
| 照合だけ(構築の入力にしない) | メトロ_銀座線_渋谷_浅草方面(G01・9 月改正=ODPT オープン枠と全件一致を試験で確かめる) |

## 3. 方面の写像の表

`direction` の値の集まりは今の W12 と同じ {上り, 下り, TokyoMetro.Asakusa, TokyoMetro.Oshiage, TokyoMetro.Wakoshi} に保った(エンジンの向きの番号 `didx` を振り直さない)。今の等間隔の行の「上り/下り」は対称で意味を持たなかったので、各社の線の向きの定義に合わせて決めた。

| 表(会社・路線・方面) | line | 向き | 根拠 |
|---|---|---|---|
| JR東日本 山手線 品川・東京方面(内回り) | 山手線 | 上り | 線路名称の山手線は品川起点(品川〜新宿〜田端)=渋谷 → 品川は起点の側(**推測・未リサーチ**) |
| JR東日本 山手線 新宿・池袋方面(外回り) | 山手線 | 下り | 同上(渋谷 → 新宿は終点の側) |
| JR東日本 埼京線・川越線 大宮・川越方面(下り) | 埼京線 | 下り | 頁の題名 |
| JR東日本 埼京線・川越線 大崎方面(上り) | 埼京線 | 上り | 頁の題名 |
| JR東日本 相鉄線直通 相鉄線方面(下り) | 埼京線 | 上り | 題名は「下り」だが渋谷から大崎の向き(南行)。ODPT の埼京線 南行=大崎方面+相鉄線方面で全一致([extraction-jr.md](../timetables/extraction-jr.md) §6)=向きで合わせた |
| JR東日本 湘南新宿ライン 高崎・宇都宮方面(北行) | 埼京線(畳む) | 下り | 北行=大宮方面と同じ向き |
| JR東日本 湘南新宿ライン 横浜・大船方面(南行) | 埼京線(畳む) | 上り | 南行=大崎方面と同じ向き |
| 東急 東横線 横浜・元町・中華街・新横浜・二俣川方面 | 東横線 | 下り | 東急の表の方面(下り)=時刻表の記録 README §2-1 |
| 東急 副都心線(東横線直通・東急の標準時刻表)池袋・和光市・森林公園・飯能方面 | 東横線 | 上り | 東急の表の題名「TY01_渋谷(上り)」=東横線から副都心線へ直通する便 |
| 東急 田園都市線 二子玉川・長津田・中央林間方面 | 田園都市線 | 下り | 東急の表の方面(下り) |
| 東急 半蔵門線(田園都市線直通・東急の標準時刻表)押上・久喜・南栗橋方面 | 田園都市線 | 上り | 東急の表の題名「DT01_渋谷(上り)」 |
| 京王 井の頭線 吉祥寺方面(渋谷発・チャレンジ枠) | 井の頭線 | 下り | 渋谷が起点(渋谷〜吉祥寺)・ODPT の railDirection=Outbound |
| ODPT 銀座線 渋谷が起点の列車 | 銀座線 | TokyoMetro.Asakusa | `odpt:railDirection` の末尾(今の値のまま) |

- **湘南新宿ラインを埼京線に畳んだ理由**(expedient・切替口 `fold_lines={}`): エンジンは方面ノード `ext_rail_jr_saikyo_shonan` を `lines[0]`=埼京線に畳んで線を引く(`world.assets` の E2)。線別の定員・混雑率上限の表(`engine.processes.rail`)にも湘南新宿ラインの行が無い。別の線にすると、その方面ノードの体が湘南新宿ラインの便に乗れず、定員が既定値(1,200 人)になる。どちらもエンジンの変更が要るので、2-3b では畳んだ。線の数(8)と線の索引も今のまま。
- **東横線・田園都市線の「上り」**は、直通の副都心線・半蔵門線の便と同じ列車(ODPT と 1 対 1 で一致=[extraction-tokyu-metro.md](../timetables/extraction-tokyu-metro.md) §5)。W12 では線ごとに 1 回ずつ現れる(今の等間隔の行と同じ形=`through_running_caveat` の範囲)。
- 井の頭線と銀座線は渋谷が終点なので、渋谷の発車は 1 方向だけ(今の銀座線と同じ)。着く体も発車の便から降りる(エンジンの便=発車の前の停車時分にホームに居る区間)。

## 4. 線ごとの本数(前=1.1.0・後=1.2.0)

| 線 | 前の元 | 後の元 | 平日 前→後 | 土休 前→後 | 前 土休>平日 | 後 土休>平日 |
|---|---|---|---|---|---|---|
| 山手線 | 等間隔 | ユーザー提供の PDF(JR) | 474→513 | 686→507 | はい | いいえ |
| 埼京線(湘南新宿ライン・相鉄線直通を含む) | 等間隔 | ユーザー提供の PDF(JR) | 502→453 | 724→410 | はい | いいえ |
| 東横線 | 等間隔 | ユーザー提供の PDF(東急) | 634→607 | 914→559 | はい | いいえ |
| 田園都市線 | 等間隔 | ユーザー提供の PDF(東急) | 714→573 | 1,028→425 | はい | いいえ |
| 井の頭線 | 等間隔 | ODPT チャレンジ枠 | 714→305 | 1,028→261 | はい | いいえ |
| 銀座線 | ODPT(7 月の取得) | ODPT オープン枠 静的データ版 1(9 月改正) | 325→360 | 276→305 | いいえ | いいえ |
| 半蔵門線 | ODPT(7 月の取得) | 同じ | 289→289 | 209→209 | いいえ | いいえ |
| 副都心線 | ODPT(7 月の取得) | 同じ | 259→259 | 238→238 | いいえ | いいえ |
| 計 | | | 3,911→3,359 | 5,103→2,914 | | |

- 行の計 9,014(等間隔 7,418+実 1,596)→ **6,273**(`source` ごと: `real` 995・`real_user_pdf_jr_east` 1,883・`real_user_pdf_tokyu` 2,164・`real_odpt_challenge_keio` 566・`real_odpt_open_metro_2026-09` 665)。
- 井の頭線の前は 2 方向 × 357/514 本(等間隔の上り・下り)。後は渋谷発の 1 方向だけ(§3)。

向きごと(後):

| 線 | 向き | 平日 | 土休 |
|---|---|---|---|
| 山手線 | 上り(内回り) | 250 | 250 |
| 山手線 | 下り(外回り) | 263 | 257 |
| 埼京線 | 上り(大崎方面 85/69+相鉄線方面 46/46+湘南新宿 南行 95/90) | 226 | 205 |
| 埼京線 | 下り(大宮方面 131/115+湘南新宿 北行 96/90) | 227 | 205 |
| 東横線 | 上り | 259 | 238 |
| 東横線 | 下り | 348 | 321 |
| 田園都市線 | 上り | 289 | 209 |
| 田園都市線 | 下り | 284 | 216 |
| 井の頭線 | 下り | 305 | 261 |
| 銀座線 | TokyoMetro.Asakusa | 360 | 305 |
| 半蔵門線 | TokyoMetro.Oshiage | 289 | 209 |
| 副都心線 | TokyoMetro.Wakoshi | 259 | 238 |

1 時間の本数(後・全向きの和・運行日の時台):

| 線 | 平日 最大(時台) | 土休 最大(時台) | 平日 朝 7〜9 時の最大 / 昼 10〜15 時の平均 | 土休 同 |
|---|---|---|---|---|
| 山手線 | 36(8) | 34(16) | 36 / 24.7 | 27 / 30.7 |
| 埼京線 | 44(8) | 29(9) | 44 / 22.8 | 29 / 23.0 |
| 東横線 | 45(8) | 33(8) | 45 / 32.2 | 33 / 32.2 |
| 田園都市線 | 49(8) | 27(9) | 49 / 25.8 | 27 / 24.3 |
| 井の頭線 | 25(8) | 17(10) | 25 / 15.5 | 16 / 15.3 |
| 銀座線 | 28(8) | 20(10) | 28 / 20.0 | 19 / 20.0 |
| 半蔵門線 | 27(8) | 14(9) | 27 / 12.5 | 14 / 12.0 |
| 副都心線 | 24(8) | 15(8) | 24 / 13.8 | 15 / 14.0 |

- **重複の除去**: 0 件(同じ line・向き・暦・発車時刻の行は無かった。畳んだ埼京線でも 0)。
- **臨時の特急を外した**: 4 本(土休の湘南新宿ライン 北行 1・南行 3=踊り子 3・サフィール踊り子 1)。4 本とも `JR_注記.final.csv` で ◆(運転日注意)が付くことを読みの段で確かめた(付いていなければ止まる)。
- 派生(実ダイヤ・全線): オフピーク比 平日 0.6019・土休 0.9635(前はメトロ 3 線から 0.5411・0.9778)。朝ピーク(7〜9 時の 1 時間の最大・全線の和)平日 278・土休 178。初終発(全線)は平日・土休とも初発が 4 時台・終発が 0 時台(時刻は資産のヘッダの notes にだけ書く)。今は等間隔の線が 0 なので、これらはどの行にも使っていない(notes とゲートだけ)。`metro_*` の欄はメトロ 3 線(銀座線は 9 月改正)の値: 朝ピーク 平日 79・土休 47(初終発のゲート `metro_first/last_departure_plausible` は PASS のまま)。

## 5. 版の宣言(`w12_timetable_versions.json`=資産の隣)

`source` の列とは別に、線ごとの版を JSON に書いた(時刻の一覧は載せない)。関係の符号: `before`=世界の時点より前の版(頁か ODPT に改正日)・`before_inferred`=前の版と推測(改正日の記載なし)・`after`=後の版(宣言)。

| 線 | 表の版の記載 | 宣言 | 世界の時点(2026-07-13)との関係 |
|---|---|---|---|
| 山手線・埼京線 | 「JR 時刻表 2026 年 10 月号に基づく(改正日の記載なし)」 | 2026-03-14 改正と同じ版と推測(ODPT チャレンジ枠 dct:issued 2026-03-14 と全表で一致・extraction-jr.md §7)。土休の ◆ 特急 4 本は臨時と見て外した | before_inferred |
| 東横線・田園都市線 | 2026-03-14(東急の表の右下・第330 の読み取り) | 上りは東急が出す副都心線・半蔵門線の標準時刻表(ODPT 2026-03-14 と全件一致) | before |
| 井の頭線 | 2026-07-03(チャレンジ枠の dc:date) | dct:issued 2025-03-17(平日)/2025-03-15(土休)。改正日の欄は無い(空欄)。07-03〜07-13 に改正が無ければ時点に効いていた版(推測) | before_inferred |
| 銀座線 | 2026-09-19(dct:issued・665 本とも)・dc:date 2026-09-24 | ODPT オープン枠の静的データ版 1=9 月改正 | **after** |
| 半蔵門線・副都心線 | ODPT の駅の時刻表 dct:issued 2026-03-14(2026-07-07 取得) | 今の 7 月の取得のまま | before |

**銀座線の宣言**: 銀座線の時刻表は、世界の時点(2026-07-13)より後の 2026-09-19 改正の版である([回答 10-13b](../../../../design/v2-answers-2026-10-13b.md) §2 のユーザー決定)。時点の版(07-07 取得・平日 2025-03-15/土休 2025-11-01・平日 325/土休 276 本)は W12 の入力から外した(ファイルは `data/odpt/` に残る・記録として残す)。

入力の md5(`w12_timetable_versions.json` の `inputs` と同じ):

| 層 | ファイル | md5 | バイト |
|---|---|---|---|
| user_timetables | JR_山手線_渋谷_内回り_平日_final.csv | 62094feaaeaef6b98b9631c158a4ce95 | 43,308 |
| user_timetables | JR_山手線_渋谷_内回り_土休_final.csv | bbfe131324b99241a0ec315af8f41d7d | 43,372 |
| user_timetables | JR_山手線_渋谷_外回り_平日_final.csv | e51d5b7cf4ae695a94127c3fd252ac91 | 45,574 |
| user_timetables | JR_山手線_渋谷_外回り_土休_final.csv | 4e3ee9b47717700bd6089cd5e2a8e77a | 44,587 |
| user_timetables | JR_埼京線_渋谷_大宮方面_平日_final.csv | 99b3ccd5a9fac13e245707a312aef291 | 23,369 |
| user_timetables | JR_埼京線_渋谷_大宮方面_土休_final.csv | fe96ff457fe3a36ce8b5d57e3c747ebe | 20,413 |
| user_timetables | JR_埼京線_渋谷_大崎方面_平日_final.csv | eacb319166addddac200cd53e63a0090 | 14,747 |
| user_timetables | JR_埼京線_渋谷_大崎方面_土休_final.csv | 32f90d95663bee54f2231b52dfeb1a20 | 11,852 |
| user_timetables | JR_相鉄線直通_渋谷_相鉄線方面_平日_final.csv | 240900d4ba45f1cd3ba39816cd6eaf76 | 7,785 |
| user_timetables | JR_相鉄線直通_渋谷_相鉄線方面_土休_final.csv | 2055bb39a28696bc1ae43cb39f6a2575 | 7,786 |
| user_timetables | JR_湘南新宿ライン_渋谷_北行_平日_final.csv | c529f997422408dc705252c98bd59abc | 18,148 |
| user_timetables | JR_湘南新宿ライン_渋谷_北行_土休_final.csv | b0c5dd9337ecf174aa3978211f31c899 | 17,249 |
| user_timetables | JR_湘南新宿ライン_渋谷_南行_平日_final.csv | 774994d96653f4507f73c113d8e7f364 | 17,821 |
| user_timetables | JR_湘南新宿ライン_渋谷_南行_土休_final.csv | 63d8303596da92687ee2f4a69fed900a | 17,539 |
| user_timetables | 東急_東横線_渋谷_横浜方面_平日_final.csv | 6d6bc49ee874fe9554537a27c95a9941 | 50,326 |
| user_timetables | 東急_東横線_渋谷_横浜方面_土休_final.csv | 0be120b6b21a0f25e7eafe4efe336167 | 46,353 |
| user_timetables | 東急_副都心線_渋谷_和光市方面_平日_final.csv | 8ee8c6b525ae05f114db4a6be997162f | 45,583 |
| user_timetables | 東急_副都心線_渋谷_和光市方面_土休_final.csv | 4d19091841145c8eb9470605873610fa | 41,678 |
| user_timetables | 東急_田園都市線_渋谷_中央林間方面_平日_final.csv | af8938df2209e7c97a6f51c36411b754 | 37,817 |
| user_timetables | 東急_田園都市線_渋谷_中央林間方面_土休_final.csv | 3bdb514728e9c09e1729a7ccd9645208 | 28,890 |
| user_timetables | 東急_半蔵門線_渋谷_押上方面_平日_final.csv | 5881b4d4898e542d581115eb35e72e69 | 47,416 |
| user_timetables | 東急_半蔵門線_渋谷_押上方面_土休_final.csv | 06c9e85904386d38df81fcb7301908f8 | 34,329 |
| user_timetables | JR_注記.final.csv | 69c9d18f435c5dc973c386dbc0c58039 | 9,486 |
| odpt_challenge | 京王_井の頭線_渋谷_吉祥寺方面_平日_odpt.csv | b2eff6084b9f6b5a5edeebca1a496303 | 36,379 |
| odpt_challenge | 京王_井の頭線_渋谷_吉祥寺方面_土休_odpt.csv | 4d8d3a4925c4a6176c344f00be0a8c07 | 31,068 |
| odpt_static | traintimetable_TokyoMetro.json.gz(2026-10-13 のフォルダ) | de513ef2348f3834cdb5154f9930ae08 | 915,498 |
| (今の取得) | station_timetable_metro_hanzomon.json | e9b558b736ad779fbde1a3f59b0b5849 | 174,820 |
| (今の取得) | station_timetable_metro_fukutoshin.json | ca33f88c0179b62dd5d1e8e67590b498 | 175,638 |

## 6. 残る等間隔の線=0 の検査

- ゲート `equal_interval_lines_remaining`(期待値 0): 等間隔の推定の対象だった線(田園都市線・東横線・井の頭線・山手線・埼京線・湘南新宿ライン)のうち、実ダイヤの行が無い線(畳んだ線は畳み先に行があれば埋まったと数える)の数=**0**。`real_lines_have_both_calendars`=True(8 線とも平日と土休の行がある)。
- 試験 `test_no_rail_line_is_left_for_equal_interval_statically`(data 不要): 方面ノードの線は全部、表の白い一覧(畳みを含む)・メトロ 2 線・銀座線で埋まる。
- 等間隔の関数 `equal_interval_departures` は残した(実データの無い線が出たときだけ使う)。そのときはヘッダの expedients にモジュールの表 `EQUAL_INTERVAL_TIMETABLE_EXPEDIENTS` の 1 行が足され、残る線の名と夕ピークの規則は notes(`equal_interval_lines`・`equal_interval_pm_rule`)に書く。今の expedients には等間隔の行が無い(実ダイヤの宣言は `REAL_TIMETABLE_EXPEDIENTS` の 8 行=§13)。

## 7. W19 の層の元・凍結の表

- `SOURCE_FAMILIES` に構築の入力の層を 3 つ足した(元の語=層の名): `user_timetables`(ユーザーが各社の公式サイトから手で入手した時刻表の読み取り=JR・東急)・`odpt_challenge`(ODPT チャレンジ枠=京王)・`odpt_static`(ODPT オープン枠の静的データ版 1=銀座線)。`BUILD_INPUT_FAMILIES` に同じ 3 つ(入力のパスは `w12_real_timetables.input_rel_paths` から組む=手書きの重複なし)。封印の 3 層の判定は今のまま(3 層とも「照合用(独立でない)」・理由も同じ)。
- 凍結の表(`w19_freeze.json` の `data_assets`): 66 → **91** 件。足したのは実ダイヤの入力 26 本(ユーザー提供の読み取り 23・チャレンジ枠 2・静的データ版 1 の 1)、外したのは `odpt/station_timetable_metro_ginza.json`(W12 が読まなくなった)。W19 の表は sha256 とバイト数を持つ(md5 は §5 の版の表に)。`data_assets_missing`=0・`holdout_not_referenced_in_build_code`=0。
- W19 の版(1.0.0)は変えていない(params の `source_families` が変わったので param_hash は動く)。

## 8. 資産の組み立て(活性化はしない)

1. 写し: `data/world/v2/` の直下のファイル 100 本と `acceptance/` を `data/world/v2_stage_2-3b/` に本物のコピーで写した(sha256 が全部一致・ハードリンクではない)。写さなかったもの: W17 のプロンプトと応答の jsonl 15 本(計約 3 GB)と下位のフォルダ(`trials*`・`w17v1_backup`・`w17v2*`)。エンジンも W12 の構築も読まない。
2. 写しが HEAD の資産と同じに動くことの確かめ: 写し(作り直す前)で byte-check の 4 構成を回し、HEAD の資産の side と **25 欄とも全部同じ**(`frozen_sources` を含む)。
3. 作り直し: リポの根で(作業木の `src` を `PYTHONPATH` に)

   ```
   python -m shibuya.build.run --out data/world/v2_stage_2-3b --data data \
       --stage W12 --stage W18 --stage W19 --stage W20 \
       --keep-stage W0 … --keep-stage W11 --keep-stage W13 … --keep-stage W17
   ```

   W12 と、W12 の出力を写す W18〜W20 だけを走らせ、他の 17 段は `--keep-stage`(出力の sha256 をヘッダと照らしてから採る)。全段がそろうので `build_manifest.json` を正典として書いた(`kept` に 17 段)。終了コード 0(走らせた段のゲートは全部 PASS)。
4. 動いたファイル(HEAD の資産と比べた): `w12_timetables.parquet`(`c548b2bb7ecd5c21` → **`7ef7ab9038348e59`**)・新しい `w12_timetable_versions.json`・`W12.header.json`・`wc_index.json`(W18 の「鉄道運行」の `n_sim` 9,014 → 6,273)・`W18.header.json`・`w19_freeze.json`・`W19.header.json`・`acceptance/gate_table.md`・`acceptance/summary.json`・`W20.header.json`・`build_manifest.json`。**動かなかった**: `w12_external_nodes.parquet`(`031fe09e9a566eff`)・`w12_generation_weights.parquet`(`eb85f8acf5a20809`)ほか 96 ファイル。
5. 活性化(本体の `data/world/v2/` への差し替え)は 2-4 で親が行う。差し替えるファイルは上の 4 の一覧。
   - 切替口 False(1.1.0 の時刻表の再現)で組み直すときの注(検収 L2): ヘッダの `stage_version` は 1.2.0 のまま、expedients は `EQUAL_INTERVAL_TIMETABLE_EXPEDIENTS` の 1 行になる(1.1.0 の 5 行は台帳で removed)。時刻表・方面ノード・重みの parquet と params・input_hash・notes・ゲートは 1.1.0 と同じなので、ヘッダ・manifest・build_hash だけが 1.1.0 とバイト一致しない。

6. 最後の作り直し(方面の写像の根拠の文言=params を直した後): 同じ指図で 2 回続けて走らせ、`build_hash` `591c854352dcff06…` が一致(決定的)。`w12_timetables.parquet` `7ef7ab9038348e59`・`w12_timetable_versions.json` `4ee484eb75037467`・方面ノード・重みは §9 の side を取ったときと同じ(エンジンが読むファイルは同じ)。動いたのは W12〜W20 のヘッダ・`w19_freeze.json`・受入パックの 2 本・`build_manifest.json`(`fd4aeccc605fa481`)だけ。W12 のヘッダ `e37a14e320afcfc8`。

## 9. 動いた量(2-4 の束の材料)

byte-check(`10e/byte_check_10e.py` の `side`・`--world` の引数で資産を指定・作業木の `src`・5,000 体・seed 1・1 シミュ日・4 構成)。前=HEAD の資産 `data/world/v2`・後=`data/world/v2_stage_2-3b`。写しを作り直す前の side は前と 25 欄とも同じ(§8 の 2)。**動いて当然=▲ではなく版上げの材料**。

| 構成 | final 前→後 | 呼数 前→後 | blocks の行 | 行動の延べ | 気づき | 食事 | 出動の平均の遅れ[分] |
|---|---|---|---|---|---|---|---|
| w6_v3_default(v3 既定) | `5f7ae9ff24005314` → `4bcca9f0216362bb` | 65,597 → 65,400(−197) | 7,975 → 8,157 | 291,935 → 296,016 | 237 → 302 | 4,559 → 4,400 | 8.2 → 10.8 |
| w6_v3_activity_off | `e0054a837c6ec4c1` → `dee82f1ebaa73ebe` | 50,301 → 50,155(−146) | 2,660 → 2,698 | 173,688 → 174,152 | 719 → 471 | 3,342 → 3,360 | 7.6 → 8.0 |
| w6_v1_default(v1 既定) | `24375ee3dab349e8` → `2c0e05968641f380` | 51,835 → 51,835(0) | 2,731 → 2,744 | 180,082 → 180,450 | 692 → 496 | 0 → 0 | 10.2 → 7.2 |
| v3_mem_rel(記憶+関係) | `73a78288ab5e1498` → `c506dec249bb4328` | 69,111 → 69,114(+3) | 8,544 → 8,453 | 298,472 → 299,407 | 396 → 190 | 4,658 → 4,691 | 10.2 → 9.2 |

- 4 構成とも final が動いた。動かなかった欄: 顕著行為 10・崩落 5・出動 5・到着 5・暦の欄(開始日・再生日・曜日)・`rng_scheme`・テープの列の名前。v1 既定は呼数と呼びの行数が同じで、行動・blocks・気づきが動いた。
- **`frozen_sources` で動いたのは `process:w12_timetables.parquet` の 1 行だけ**(`c548b2bb7ecd5c21` → `7ef7ab9038348e59`)。`process:w12_external_nodes.parquet` を含む他の行は同じ=動いた量はすべて W12 の時刻表から来る。
- 行動で動いたのは乗車・移動・(エンジン継続)ほか全般(例 v3 既定: 乗車 5,467 → 5,459・移動 9,018 → 9,379・食事 5,069 → 4,937)。便の時刻と本数が変わり、体の着く時刻と駅での待ちが変わるため(推測・分解はしていない)。
- 気づき(`noticed`)は構成によって大きく動く(10e の B3 と同じ型=第330 §B3 の表)。

**到着の波**(`tools/instruments/anchor_gauge.py` の `run`=2 腕 mock・classical を `record` → `gauge`・3-3 駅ごとの到着の波・ω で戻す・合否なし)。前=HEAD の資産・後=2-3b の資産(どちらも作業木の `src` で回し直した。前の mock の final は 2-0 の最初の記録 `2026-10-14_2bc7a4b` と同じ `5f7ae9ff24005314`)。計器の出力は作業用の置き場(`_bc/gauge_out/`・git の外)に置き、本書には表だけを写す。

| 腕 | final 前→後 | 呼数 前→後 | 到着の数(体・ω の前) | 計画の到着 |
|---|---|---|---|---|
| mock | `5f7ae9ff24005314` → `4bcca9f0216362bb` | 65,597 → 65,400 | 8,009 → 8,037 | 5,687 → 5,687 |
| classical | `202a05a22c5bd8e1` → `f62a8d0ba0aa952f` | 93,460 → 93,685 | 5,604 → 5,603 | 5,687 → 5,687 |

3-3 の前後(割合=全ノードの到着に占める割合・ピーク=到着が最も多い時台・JSD=錨 2〔部〕W12 の時刻の形との差):

| ノード | mock 割合 前→後 | mock ピーク 前→後 | mock JSD 前→後 | classical 割合 前→後 | classical ピーク 前→後 | classical JSD 前→後 |
|---|---|---|---|---|---|---|
| ext_rail_tokyu_denentoshi | 0.1997→0.1979 | 9→8 | 0.0729→0.0638 | 0.2014→0.2014 | 9→8 | 0.0948→0.0831 |
| ext_rail_tokyu_toyoko | 0.1333→0.1330 | 8→9 | 0.0703→0.0795 | 0.1374→0.1375 | 8→9 | 0.0936→0.1033 |
| ext_rail_keio_inokashira | 0.0855→0.0872 | 7→8 | 0.0662→0.0760 | 0.0810→0.0810 | 7→7 | 0.0963→0.1080 |
| ext_rail_jr_yamanote | 0.1860→0.1825 | 9→8 | 0.0675→0.0584 | 0.1853→0.1854 | 9→8 | 0.0786→0.0728 |
| ext_rail_jr_saikyo_shonan | 0.0419→0.0416 | 9→9 | 0.0776→0.0765 | 0.0419→0.0419 | 8→8 | 0.0828→0.1032 |
| ext_rail_metro_hanzomon | 0.1793→0.1820 | 8→8 | 0.0601→0.0580 | 0.1763→0.1759 | 8→8 | 0.0729→0.0725 |
| ext_rail_metro_fukutoshin | 0.0735→0.0734 | 7→7 | 0.0569→0.0562 | 0.0713→0.0714 | 7→7 | 0.0804→0.0804 |
| ext_rail_metro_ginza | 0.0753→0.0766 | 9→9 | 0.0584→0.0594 | 0.0792→0.0792 | 9→9 | 0.0830→0.0877 |
| ext_walk_gate | 0.0078→0.0077 | 9→9 | 0.1158→0.1270 | 0.0078→0.0078 | 9→9 | 0.2467→0.2467 |
| ext_road_gate | 0.0178→0.0181 | 9→9 | 0.0508→0.0577 | 0.0184→0.0184 | 9→9 | 0.0978→0.0978 |

- 線の割合はほぼ動かない(mock で ±0.0035 以内・classical で ±0.0004 以内)。到着の帰属は W16 の方面ノード(不変)なので、割合は母集団で決まり、時刻表は着く時刻を動かす。
- ピークの時台が動いた線: 田園都市線と山手線は 9 → 8 時台(2 腕とも)、東横線は 8 → 9 時台(2 腕とも)、井の頭線は mock で 7 → 8 時台。実ダイヤでは朝の 8 時台の本数が多い線(田園都市線 49 本/時・山手線 36 本/時=§4)ほど 8 時台に寄った。
- 午前 4 時台(28 時の区分)に着く体が新しく出た(山手線・井の頭線・田園都市線・半蔵門線で 0.1〜0.8%)。実ダイヤには 4 時台に発車する便(JR 山手線)があり、前の初発(等間隔の推定とメトロ=5 時台)より早いため(推測)。
- 錨 2〔部〕(W12 の生成の重みの時刻の形)との JSD は、田園都市線・山手線で小さくなり、東横線・井の頭線で大きくなった。錨 2 は構築の入力の写し(〔部〕)で合否にしない。
- 計器の要約の値 156 件のうち変わった 52 件(3-1 のピーク 1・3-2 の比 25・3-3 の割合 14 とピーク 7・3-4 の始業 5)。3-4 の始業の平均は mock 783.2 → 792.4 分・classical 605 → 606 分。

## 10. 試験

- **新しい試験** `tests/build_field/test_w12_real_timetables.py` 19 件(data 不要 16・data が要る 3)。data 不要: 方面の写像の表(設計の写し)・合成の CSV 3 行(相鉄線直通の表が埼京線の上りに・0 時台)と畳み・会社/方面/駅/暦の照らし(違えば止まる)・暦の写像とファイル名・運行日の分(T0 の定数と運行日の切れ目で計算・5 件)・時刻の範囲・重複の除去・臨時の特急(◆ が無ければ止まる・JR の表の外には当てない)・ODPT の列車時刻表(合成の 2 列車+他の線・暦の外は止まる)・「等間隔で残る線 0」の静的な検査・世界の時点=暦の既定・W19 の入力の層と資産の表。data が要る: `run()` の線ごとの本数が本書の golden と一致・ゲートが全部 PASS・列と向きの集まり・版の表(銀座線=after・畳み・入力の md5・時刻を載せない)/切替口 False で 1.1.0 の本数(9,014・等間隔 7,418・実 1,596)に戻り、方面ノードと重みは実ダイヤと同じ sha256/銀座線の ODPT オープン枠の渋谷発=ユーザーの G01 の読み取り(時刻の多重集合で一致・G01 は照合だけ)。
- **一覧の外の直し**(§1 の表の 5 本)を含む build の試験の全体(作業木・最後のコード): `tests/build_field`・`tests/build_audit`・`tests/build_vis`・`tests/build_geo`・`tests/build_lang`・`tests/build_pop`・`tests/build_sched`・`tests/test_build_run_keep_stage.py`・`tests/engine/time` = **855 passed・1 xfailed(9 分 49 秒)**。全段の構築を 3 回回す試験(field・audit・vis の pipeline)を含む。`tests/engine/time/test_t0_literal_count.py`(時間の直書き)も通る。
- **data の無い環境の再現**(`src`・`tests`・`pyproject.toml`・本書だけの写し): 直した 7 本で 37 passed・28 skipped(data の要る試験は `requires_data` の一律の理由で飛ぶ・新しい id `user_timetables`・`odpt_static` が効く)。
- 秘密の検査(`tools/scan_secrets.py`・変えた 11 本): CLEAN。

## 11. 限界と仮採用

1. **JR の改正日は推測**: 頁は「JR 時刻表 2026 年 10 月号に基づく」で改正日の記載が無い。ODPT チャレンジ枠(dct:issued 2026-03-14)と全表で一致したことから、2026-03-14 改正と同じ版で世界の時点に効いていたと推測した(README §7・extraction-jr.md §7)。07-17 から 10 月号までの改正の有無は否定できない。
2. **成田エクスプレスの表は使わない**: 湘南新宿ラインの表に同じ時刻・行き先・種別で 104 本とも含まれる(二重に数えない)。
3. **土休の ◆ 臨時の特急 4 本は外した**(README §7・extraction-jr.md の親検収 (2)=推測)。見分けは種別(踊り子・サフィール踊り子)で、◆ の印を読みの段で確かめる。平日の ◆(湘南新宿 北行 5・成田エクスプレス 新宿方面 5)と土休のほかの ◆ は ODPT にある便なので残した。◆ の便が 07-13 に走ったかは頁から分からない。
4. **相鉄線直通**: 渋谷から相鉄線へ行く便(46/46)は「相鉄線方面」の表を埼京線の上り(南行)に入れた。相鉄線から来て北へ行く便は大宮方面の表に入っている(README §7 で確認済み)。
5. **湘南新宿ラインを埼京線に畳んだ**(§3・expedient)。別の線にする形(`fold_lines={}`)はエンジン側の表(定員・方面ノードの線)とそろえる段で決める。
6. **山手線の上り/下り**は線路名称の慣行による推測(未リサーチ・ネットワーク不可)。エンジンは向きを便の並びの決め方にしか使わないので、本数と時刻は変わらない(向きの番号の集まりも同じ)。
7. **京王はチャレンジ枠**: 利用はチャレンジへの応募(作品=本シミュレーション)と照合の範囲(odpt-challenge-2026-conditions.md)。生の行は本書・版の表・試験の golden に写していない(本数と版だけ)。
8. **銀座線は世界の時点より後の版**(§5)。時点の版との本数の差: 平日 +35・土休 +29。
9. 東横線・田園都市線の上りと副都心線・半蔵門線は同じ列車が線ごとに 1 回ずつ現れる(直通の二重=今の形と同じ・§3)。
10. 1 日の便の総数が減った(平日 3,911 → 3,359・土休 5,103 → 2,914)。等間隔の推定が本数を多めに置いていた(井の頭線は 2 方向 × 等間隔)ため。

## 12. 親に確かめてほしい点

1. **湘南新宿ラインの畳み**(§3): 2-3b では埼京線に畳んだ(線は 8 のまま)。別の線にするなら、エンジンの線別の定員・混雑率上限の表と方面ノードの線の引き方(E2)を同じ版で直す必要がある。
2. **山手線の上り/下り**(§3・推測): 内回り=上り・外回り=下りでよいか(線路名称の品川起点による)。
3. **発注の一覧の外の試験を直した**(§1 の表の 6 本): 既存の試験が「等間隔の行がある」「`realworld_live/` の下は W19 に載らない」「形ごとの数 139」を前提にしていた。直しは最小(切替口 False で回す・新しい値・data の印・数)。
4. **試験の置き場**: 発注は `tests/build/test_w12_real_timetables.py` だが、`tests/build/` は無く W12 の試験は `tests/build_field/` にあるので、そこに置いた。
5. **2-4 の活性化のときに動くもの**(本段では触っていない): `tools/c8/sensitivity.py` の S-W14-JRPHASE(等間隔の位相をずらす対照=等間隔の行が 0 になるので対象が無い)と `tests/c8/test_sensitivity_ledger.py` の build_manifest の expedient の数(123)と digest。W12 の expedients は 8 → 11 行になり、等間隔の 5 行が消える。
   - **つなぎの台帳で外す段が 2-3b だった 8 行の扱い**(検収 L5・親の指示で台帳を直した=§13):

     | 行 | 中身 | 扱い |
     |---|---|---|
     | W12#4 | 等間隔ダイヤ(F10)・上下同数 | removed(2-3b・2026-10-14) |
     | W12#5 | 山手線ピーク本数=資料3の中央 18 | removed |
     | W12#6 | オフピーク比はメトロ実ダイヤから移植 | removed |
     | W12#7 | 夕ピーク本数=朝ピークと同数 | removed |
     | W12#8 | 初終発時刻はメトロ平日ダイヤから移植 | removed |
     | BR-W12-HOLIDAY-GT-WEEKDAY | 等間隔の推定で土休 > 平日 | removed(実ダイヤで 8 線とも土休 ≦ 平日) |
     | BR-W11-SHINSEN-EXIT | W11 の神泉の出口(井の頭線の終点の到着の元) | 外す段を **2-3c** に(2-3b は渋谷の発車だけ) |
     | HD-engine.processes.rail-1af925f4 | rail.py の見出し「expedient(本モジュール分)」の下の項 6 個(停車と折返しほか) | 外す段を **2-3c** に |
6. **W19 の版**: 1.0.0 のまま(注の「資産の作り直しは版上げ 2 回目で」に当たる)。上げるかは親の判断。
7. **ライセンス台帳に足す行の案**(親が書く):
   - 京王 井の頭線(ODPT チャレンジ枠): 出典=公共交通オープンデータチャレンジ 2026 の限定ライセンスのデータ(駅の時刻表・列車時刻表・dc:date 2026-07-03)。利用の範囲=チャレンジへの応募(作品=本シミュレーション)と照合。W12 の構築の入力に使う(世界の資産 `w12_timetables.parquet` に渋谷発 566 本として入る)。再配布と公開はしない(生の行を記録・版の表・試験に写さない)。許諾の期限は限定ライセンスのとおり(期限の日付は台帳に書かない=回答 10-13 の扱い)。
   - ユーザー提供の時刻表の読み取り(JR 東日本・東急): 出典=ユーザーが 2026-10-12〜13 に各社の公式サイトから手で入手した PDF の読み取り(事実だけ=発車時刻・種別・行き先・平日/土休・方面・版)。利用の範囲=研究開発の段階(商用でない)。W12 の構築の入力に使う(JR 1,883 本・東急 2,164 本)。図と PDF は公開しない・CSV も git に入れない。商用の前に JR 東日本と交通新聞社・東急の許諾(回答 10-12b §2-1・回答 10-13 の 2)。
   - ODPT オープン枠の静的データ版 1(東京メトロの列車時刻表・2026-10-13 のフォルダ): 出典=公共交通オープンデータセンター(ODPT 利用規約・出典の表示)。W12 の構築の入力(銀座線 665 本)。
   - 世界の資産 `w12_timetables.parquet` に上の 3 つの由来の発車時刻が入る(`source` の列で見分けられる)。資産は git に入れない(今と同じ)。

## 13. 検収の直し(独立の検収=条件つき受入・高 1・低 5 → 親の指示で直した)

| # | 重さ | 指摘 | 直し |
|---|---|---|---|
| H1 | 高 | 時刻表の expedient を局所のリストに移し `StageResult(expedients=[..., *timetable_expedients])` で渡したので、つなぎの台帳の走査器(`engine/bridging/scan.py` の形 B)に中身が見えず `tests/engine/bridging` が 11 件落ちた(旧の W12#4〜#8 が孤児・星付きの 1 件が台帳に無い) | 宣言をモジュールの表にした: `REAL_TIMETABLE_EXPEDIENTS`(実ダイヤ 8 行)・`EQUAL_INTERVAL_TIMETABLE_EXPEDIENTS`(等間隔の道 1 行=1.1.0 の 5 行をまとめた)を `res.expedients.extend(<表>)` で足す。動的な中身(残る線の名・夕ピークの規則)は notes へ。台帳(親の許可): W12#4〜#8 と BR-W12-HOLIDAY-GT-WEEKDAY を removed(why の末尾に 2-3b・2026-10-14 と理由)・新しい宣言の行 9 つ(id=`EX-build.field.w12_external_nodes-<走査器の鍵>`・remove_basis=inferred・外す段は下の表)・BR-W11-SHINSEN-EXIT と HD-engine.processes.rail-1af925f4 の外す段を 2-3c に。`PLAN_STAGES` に 2-3c を足した。形ごとの数 expedients 139 → 143・active の行 286 → 289(全 295 行)。`tests/engine/bridging` 49 passed(土台と同じ数) |
| L1 | 低 | `test_audit_units` の docstring が古い・`odpt_rt` の負の対照が無い | docstring を「`realworld_live` の下は `odpt_static`(構築側の版)だけ載る・`odpt_rt`(検証専用)は載らない」に。`odpt_rt` の偽のファイル 2 本と別の日付の `odpt_static` の偽のファイルを置いても資産の表が変わらない試験を 1 本足した |
| L2 | 低 | 切替口 False でもヘッダの `stage_version` は 1.2.0 | 宣言を §8 の 5 に 1 行(expedients も等間隔の道の 1 行になる=H1 の直しの結果) |
| L3 | 低 | 「時刻を載せない」の検査が語 `departure` だけ | ISO の日時を除いた `HH:MM` の形が 0 件の検査を足し、紛れ込んだ時刻を見つける負の対照を 1 本足した |
| L4 | 低 | `realworld_live` の下は検証専用、という読み方との食い違い | 本段では直さない(親の判断=静的データ版 1 は構築側と発注に明記・W19 の資産の表は `odpt_static` の 1 本だけで `odpt_rt` は載らない=L1 の試験) |
| L5 | 低 | §12 の 5 に外す段 2-3b の 8 行が無い | §12 の 5 に表を足した |

新しい宣言の行(9 つ・`what` は表の文そのまま):

| 表 | 番 | 中身(短く) | 外す段 |
|---|---|---|---|
| REAL_TIMETABLE_EXPEDIENTS | 1 | 渋谷の発車の表だけ(到着の表は使わない) | 2-3c |
| 同 | 2 | 方面の上り/下りの写像(山手線は推測・相鉄線直通は向きで) | 7 |
| 同 | 3 | 湘南新宿ラインを埼京線に畳む | 6-2(エンジンの E2 と同じ段) |
| 同 | 4 | 土休の ◆ 特急 4 本を臨時と見て外す | 7 |
| 同 | 5 | JR の版=2026-03-14 改正と同じと推測 | 7 |
| 同 | 6 | 銀座線=世界の時点より後の版 | 7 |
| 同 | 7 | 井の頭線の版=チャレンジ枠の dct:issued が時点に効いていたと推測 | 7 |
| 同 | 8 | 東横線・田園都市線の上り=直通と同じ列車(直通の二重) | 2-3c |
| EQUAL_INTERVAL_TIMETABLE_EXPEDIENTS | 1 | 等間隔ダイヤの道(切替口 False と実データの無い線だけ) | 2-4(活性化の後に切替口を残すかを決める段・仮) |

- 直しの後の資産: `data/world/v2_stage_2-3b/` は作り直していない(build_hash `591c854352dcff06…` のまま)。直した後のコードで W12 を一時の置き場で組み、`w12_timetables.parquet` `7ef7ab9038348e59`・`w12_timetable_versions.json` `4ee484eb75037467`・方面ノード・重みが stage の資産と sha256 一致(src/build の差は宣言の形と文だけ)。stage の資産の W12 のヘッダの expedients は直す前の文のまま(2-4 で組み直すときに今の文になる)。
- 親の読み: 京王チャレンジ枠の行を本体の世界資産に入れるのは回答 10-13 の 3・7(作品=本シミュレーション・チャレンジ枠は応募と照合用)に沿う。生の行は再配布しない。最終の確認はユーザー(親が PENDING に載せる)。

直しの後の試験(作業木・rebase の前=土台 `f2405e3`): `tests/build_field tests/build_audit tests/engine/time tests/engine/bridging` = **292 passed・1 xfailed(9 分 51 秒)**(`tests/engine/bridging` は 49 passed=土台と同じ数)。新しい試験は 20 件(L3 の負の対照 1 を足した)・`test_audit_units` に L1 の負の対照 1。lint-imports 5 kept・0 broken。台帳の直しの後の byte-check(v3 既定・stage の資産): final `4bcca9f0216362bb`・呼数 65,400=§9 と同じ(台帳の件数は manifest の欄だけで final に入らない)。

本体の枝(`e52c07e`)への rebase: 変えたファイル 11 本の控え → 土台に戻す → 早送り(`e52c07e`)→ 3 方向の merge-file。10 本は衝突なし。`tests/engine/bridging/test_bridging_ledger.py` の 1 か所(形ごとの数の行=1-7 が heading 79 → 80、2-3b が expedients 139 → 143 を同じ行で変えた)は、親の承認した案(両側の注を残し `expedients: 143, heading: 80`)で解いた。rebase の後: 走査器の数 expedients 143・heading 80・台帳と 1 対 1(active 291・全 298 行=1-7 の 288/289 に 2-3b の −6/+9)。`tests/build_field tests/build_audit tests/engine/time tests/engine/bridging` = **292 passed・1 xfailed(8 分 30 秒)**。data の無い写しで直した 7 本+新しい 1 本 = 39 passed・28 skipped(`user_timetables` 2・`odpt_static` 1 で飛ぶ)。lint-imports 5 kept・0 broken。W12 を一時の置き場で組んだ出力(時刻表・版の表・方面ノード・重み)は stage の資産と sha256 一致(資産は作り直していない)。

- `src/shibuya/engine/bridging/ledger.py` の `PLAN_STAGES` に `2-3c` を足した(親が受け入れ・台帳の読み口だけ=シミュレーションの挙動は変えない)。

<!-- golden-begin -->
```json
{
 "dedup_removed": {},
 "legacy_110": {
  "equal_interval_rows": 7418,
  "real_rows": 1596,
  "rows_total": 9014
 },
 "rows_by_line_calendar": {
  "井の頭線": {
   "SaturdayHoliday": 261,
   "Weekday": 305
  },
  "副都心線": {
   "SaturdayHoliday": 238,
   "Weekday": 259
  },
  "半蔵門線": {
   "SaturdayHoliday": 209,
   "Weekday": 289
  },
  "埼京線": {
   "SaturdayHoliday": 410,
   "Weekday": 453
  },
  "山手線": {
   "SaturdayHoliday": 507,
   "Weekday": 513
  },
  "東横線": {
   "SaturdayHoliday": 559,
   "Weekday": 607
  },
  "田園都市線": {
   "SaturdayHoliday": 425,
   "Weekday": 573
  },
  "銀座線": {
   "SaturdayHoliday": 305,
   "Weekday": 360
  }
 },
 "rows_by_source": {
  "real": 995,
  "real_odpt_challenge_keio": 566,
  "real_odpt_open_metro_2026-09": 665,
  "real_user_pdf_jr_east": 1883,
  "real_user_pdf_tokyu": 2164
 },
 "rows_total": 6273,
 "table_counts": {
  "JR_埼京線_渋谷_大宮方面": {
   "SaturdayHoliday": 115,
   "Weekday": 131
  },
  "JR_埼京線_渋谷_大崎方面": {
   "SaturdayHoliday": 69,
   "Weekday": 85
  },
  "JR_山手線_渋谷_内回り": {
   "SaturdayHoliday": 250,
   "Weekday": 250
  },
  "JR_山手線_渋谷_外回り": {
   "SaturdayHoliday": 257,
   "Weekday": 263
  },
  "JR_湘南新宿ライン_渋谷_北行": {
   "SaturdayHoliday": 91,
   "Weekday": 96
  },
  "JR_湘南新宿ライン_渋谷_南行": {
   "SaturdayHoliday": 93,
   "Weekday": 95
  },
  "JR_相鉄線直通_渋谷_相鉄線方面": {
   "SaturdayHoliday": 46,
   "Weekday": 46
  },
  "odpt_static:TokyoMetro.Ginza": {
   "SaturdayHoliday": 305,
   "Weekday": 360
  },
  "京王_井の頭線_渋谷_吉祥寺方面": {
   "SaturdayHoliday": 261,
   "Weekday": 305
  },
  "東急_副都心線_渋谷_和光市方面": {
   "SaturdayHoliday": 238,
   "Weekday": 259
  },
  "東急_半蔵門線_渋谷_押上方面": {
   "SaturdayHoliday": 209,
   "Weekday": 289
  },
  "東急_東横線_渋谷_横浜方面": {
   "SaturdayHoliday": 321,
   "Weekday": 348
  },
  "東急_田園都市線_渋谷_中央林間方面": {
   "SaturdayHoliday": 216,
   "Weekday": 284
  }
 },
 "temporary_trains_excluded": {
  "JR_湘南新宿ライン_渋谷_北行": {
   "SaturdayHoliday": 1
  },
  "JR_湘南新宿ライン_渋谷_南行": {
   "SaturdayHoliday": 3
  }
 }
}
```
<!-- golden-end -->

## §14 親の検収(第334・Fable 5.1・rebase の後)

- 本体 e52c07e へ rebase(衝突 1 か所=test_bridging_ledger.py の数の行・親が案を承認)。範囲の試験(bridging・build_field・build_audit・engine/time・engine/systems)418 passed・1 xfailed(3 分 28 秒)。
- 親の byte-check 4 構成(本体 HEAD の src vs 作業木の src・**本体の既定の資産 data/world/v2 のまま**)=final 同じ・25 欄とも差なし(parent_head_vs_tt23b_4cfg.json)=エンジン側の差は PLAN_STAGES の 1 行だけで、資産を差し替えない限り結果は不変。資産の差し替え(活性化)は 2-4 で動いた量と一緒に記録する。
- 独立検収(review.md)=条件つき受入(高 1・低 5)→ 全部直した。検収役の本数の数え直し 12 マス・資産の再現 107 ファイル・切替口 False の sha256・動いた量 1 構成の再現が一致したことを受入の根拠にする。
- 封印の境界: 検収役・実装役とも封印の層を開いていない。W19 が holdout の層の sha256 を取る(方式 S・中身は解かない)のは既存のとおり。
- 親の判断: 京王チャレンジ枠の行を本体の資産に入れる読み(回答 10-13 の 3・7)=PENDING 仮-15 でユーザーの最終確認。ライセンス台帳 その 15。終点の到着と直通の二重計上は 2-3c(計画に行を足す)。
- 判定: 受入(第 2 期 2-3b の完了)。
