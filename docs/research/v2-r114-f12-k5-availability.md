# R-114 答申: F12 K5(時刻別滞在人口の 2025 年以降)の公開状況

<!-- hdr:v1 | 等級: B | 作成: 2026-10-13 | 範囲: F12 -->
- **分野**: 人間移動科学 #3 / 法学(規約・著作権) #11 | **重要度**: (親が付ける)(リサーチの指示書 [v2-research-request-2026-10-06](../design/v2-research-request-2026-10-06.md) :123 F12)
- **一次確認**: **B**(親検収 2026-10-13・第333=§5 の主張 1・2 を件数だけ返す問い合わせと層のメタデータで実読して一致: 年 2025/2026 の行は 0 件・dataLastEditDate 2025-05-14T01:44 UTC。値は読んでいない)
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 作成 2026-10-13・リサーチ役サブ(Opus 5.5)。子サブ未起動・Web は読むだけ(WebSearch・WebFetch)。**CSV・GeoJSON は開いていない。人数の欄は一度も要求していない。** ArcGIS の層には、メタデータ(`?f=json`)と、件数だけの問い合わせ(`returnCountOnly=true`)と、`年`・`月` の欄の重複なしの値(`returnDistinctValues=true`)だけを投げた。投げた先の `services3.arcgis.com` と `www.arcgis.com` は取得の許可の一覧の外(読むだけ)。`data/` は読んでいない。リポで読んだコードは `tools/realworld_fetch/shibuya_jinryu.py` だけ(§4-3 の根拠)。PDF 1 本(§1 #12)は WebFetch が自動で残した一時の写しを pymupdf で読んだ(リポには入れていない)。コミットなし・台帳/設計書/src 未編集。
>
> **既存答申との関係**(重ねない): 渋谷の時刻別の候補一覧と区の 6 層の中身 = [d1_reacquisition](v2-d1-reacquisition.md) ② a-1〜a-4・b-1・d-1 / 国交省 1 km の打ち切りと有償の料金(KLA 1 ID 年額 240 万円・ドコモ・Agoop) = [R-92](v2-r92-free-and-application-data-sources.md) #1・#2・#33〜#38・§2-1 / KDDI の区分と日種の定義 = [R-56](v2-r56-kddi-attribute-definition-check.md) / 安全確保計画の訪日客の月別(2024-05〜2025-04) = [R-109](v2-r109-population-size-rebuild-materials.md) :230 / 候補 ② と §10 = [パターン台帳](../design/v2-pattern-ledger.md) :133・:223-224・:248・:261 / 同じ元の判定 = [仕分け C](../reviews/triage-2026-10-13/C.md) #10〜#12。

## §0 要旨(結論を先に)

1. **K5 は今は手に入らない。** 渋谷区オープンデータの KDDI Location Analyzer の 6 層は、どれも年が 2018年〜2024年で、2025年・2026年の行は 0 件(2026-10-13 に件数だけ問い合わせた・§2)。6 層ともデータの最終編集(`dataLastEditDate`)は 2025-05-14(UTC)で、その後は一度も変わっていない。区のオープンデータ一覧の表では、この 7 行の「対象期間」「更新頻度」がどちらも空(null)。
2. **いつ出るかは、どこにも書かれていない。** 区のダッシュボードの頁・区の FAQ(「適宜更新していく予定です。」)・都の TDPF での区の発表(2025-11-17)のどれにも、2025 年分を載せる予定は無い。今の 6 層は 7 年分を 2025-05-14 に一度に載せたもので、毎年足す型だという証拠は無い。区は一覧の表を 2026-04-24 に更新しているが、KDDI の行は 2025-05-14 のまま。前年分を翌年 5 月に載せる型なら 2026-05 に 2025 年分が出ているはずで、出ていない [推測]。
3. **出るなら形は今と同じになる見込み** [推測]: ArcGIS の表(幾何なし)・月次・列は `名称・種別・年・月・時間帯・性別・人数_の合計・ObjectId`(時間帯は性別の 2 表だけ)・日種(平日/休日)の軸なし・CC BY 4.0・CSV/GeoJSON/API。
4. **区のダッシュボード(Power BI)の頁は 2026-07-22 に更新された**。2025 年分が入ったかは、JS 描画なので確かめられない。区の FAQ は「SHIBUYA CITY DASHBOARDからのデータダウンロードはできません。」と書き、要望は問い合わせフォームへ回している。
5. **無料で、加工と保存が許される形で 2025 年以降の渋谷の時刻別滞在人口を出しているところは、見つからなかった。** KDDI の無料トライアルは「トライアル中の分析結果、成果物は、外部への持ち出しを禁止いたします。」で、test の層には使えない。D1b(国交省 1 km)は 2019〜2021 年で止まっている(「2022年以降の公開予定はございません」・R-92 で親確認済み)。

## §1 出典(読んだ日はすべて 2026-10-13・逐語は WebFetch の読み取り器を通したもの)

| # | 出典 | URL | 読んで分かったこと |
|---|---|---|---|
| 1 | SHIBUYA OPEN DATA の検索 API | https://city-shibuya-data.opendata.arcgis.com/api/search/v1/collections/dataset/items?q=Location%20Analyzer&limit=50 | 6 件(numberMatched 6)・作成 6 件とも 2025-05-14・更新 2025-08-07(5 件)/2025-05-14(通行の属性別)・license CC-BY-4.0・期間の記述なし |
| 2 | ArcGIS の item の JSON(滞在の性別) | https://www.arcgis.com/sharing/rest/content/items/4ea66bd8bec444fab1e2afbeb72e52df?f=json | 説明は提供元の表記(KDDI・技研商事)と au の同意ユーザーの注記だけ・licenseInfo「CC BY」・更新頻度と期間の記述なし |
| 3 | 6 層のメタデータ(例: 滞在の性別) | https://services3.arcgis.com/UtdeFTavkHfI94t2/arcgis/rest/services/131130_taizaijinkou_seibetu/FeatureServer/0?f=json | type Table(幾何なし)・description と copyrightText が空・timeInfo なし・editingInfo(§2)・列(§2) |
| 4 | 件数だけの問い合わせ(例) | 同上の `/query?where=年 LIKE '%2025%' OR 年 LIKE '%2026%'&returnCountOnly=true&f=json` | 6 層とも `{"count":0}`。照合: 滞在の性別で `年 LIKE '%2024%'` は 2,880 件(書式の確認) |
| 5 | 区のオープンデータ一覧の表 | https://services3.arcgis.com/UtdeFTavkHfI94t2/arcgis/rest/services/131130_open_data_list/FeatureServer/0?f=json | 列に「対象期間」「更新頻度」「最終更新日」あり。KDDI の行は e_0210_001〜008(005 は欠番)の 7 行・最終更新日 2025-05-14・対象期間 null・更新頻度 null・形式 json・API 有・CC BY 4.0。表の最終編集は 2026-04-24 |
| 6 | 区の頁「渋谷駅周辺の滞在・通行人流ダッシュボード」 | https://www.city.shibuya.tokyo.jp/kusei/tokei_shibuya/shibuya-data/shibuya_city_dashboard_peopleflow_KDDI.html | 「2026年7月22日」更新・「国内居住者の渋谷駅周辺における人流・通行量を可視化」・5 エリアと 3 ストリート・期間と更新頻度の記述なし・オープンデータへのリンクなし |
| 7 | 区の FAQ | https://www.city.shibuya.tokyo.jp/kusei/tokei_shibuya/shibuya-data/shibuya-data-faq.html | 「適宜更新していく予定です。」・ダッシュボードからのダウンロード不可・要望は問い合わせフォーム(頁の更新日 2024-02-19) |
| 8 | 都 TDPF 令和 7 年度第三回の区の発表(Speaker Deck の文字起こし) | https://speakerdeck.com/data_rikatsuyou/ling-he-7nian-du-di-3hui-tdpfkomiyuniteiibento | オープンデータとダッシュボードの紹介はあるが、人流の 2025 年分の予定は無い。R7 年度は観光動向レポートを「人流・アンケートデータで更なる拡張しつつ」検討中(23 枚目) |
| 9 | KDDI Location Analyzer の無料トライアル | https://k-locationanalyzer.com/trial | 「開始日含む2週間」・会社名/自治体名が必須・フリーメール不可・目的は導入に向けた検証・成果物の外部への持ち出し禁止・終了後は得た情報を削除 |
| 10 | 同 用語解説 | https://k-locationanalyzer.com/about/glossary | 周辺滞在人口は「平日と休日を分けて算出され」る(有償の製品には日種の軸がある)・準リアルタイムは約 2 時間半前まで 30 分単位 |
| 11 | G空間情報センター(国交省 1 km) | https://www.geospatial.jp/ckan/api/3/action/package_show?id=mlit-1km-fromto | 集計期間 2019-01〜2021-12・「2022年以降の公開予定はございませんので、ご了承ください。」・政府標準利用規約・metadata_modified 2024-10-04 |
| 12 | 都 景況指標ダッシュボード コラム第 3 回(PDF・作成 2025-03-24) | https://keikyou-dashboard.metro.tokyo.lg.jp/contents/reports/pdf/3.pdf | KDDI Location Data で都内の主要な駅周辺の人出の「前週」比・都内 10 エリア・20 歳未満と訪日客を含まない・前月比と前年比は追加の予定 |
| 13 | 都オープンデータカタログ API(渋谷区) | https://catalog.data.metro.tokyo.lg.jp/api/3/action/package_search?fq=organization:t131130 | 渋谷区の 17 件に人流・滞在人口なし |
| 14 | 全国うごき統計 見える化マップ(ソフトバンク・運営はパシフィックコンサルタンツ) | https://ugokimap.jp/ | 閲覧だけ・規約は私的利用などの外の複製・翻案・公衆送信を禁止、公表と営利は事前の許諾・期間の記述なし |
| 15 | Snowflake の Agoop の告知(2023-02-13) | https://www.snowflake.com/news/agoop-launches-population-traffic-human-flow-data-on-snowflake-marketplace/?lang=ja | 無償サンプルは「東京都新宿区付近、2022年12月1日の約1時間分」の 50 m メッシュ。完全版は有償 |

## §2 区の KDDI 層の表(値は読んでいない。行数・期間・列・日付だけ)

| 名前(区の表題) | item id(先頭) / 層 | 年 | 行数 | 2025 年以降の行 | データの最終編集(UTC) | item の更新 | 列(名称・種別・年・月 の後) |
|---|---|---|---|---|---|---|---|
| 滞在人口データ(性別) | 4ea66bd8 / 131130_taizaijinkou_seibetu | 2018〜2024(2024 は 1〜12 月) | 20,112 | 0 | 2025-05-14 01:44 | 2025-08-07 | 時間帯・性別・人数_の合計・ObjectId |
| 滞在人口データ(属性別) | ed587c11 / 131130_taizaijinkou_zokuseibetu | 2018〜2024 | 1,257 | 0 | 2025-05-14 02:02 | 2025-08-07 | 属性・人数_の合計・ObjectId |
| 滞在人口データ(年代別) | 8cde42f2 / 131130_taizaijinkou_nendaibetu(サービス名は和文) | 2018〜2024 | 2,514 | 0 | 2025-05-14 02:11 | 2025-08-07 | 年代・人数_の合計・ObjectId |
| 通行人口データ(性別) | ed98b7cf / 131130_tsuukoujinkou_seibetu | 2018〜2024 | 12,096 | 0 | 2025-05-14 02:21 | 2025-08-07 | 時間帯・性別・人数_の合計・ObjectId |
| 通行人口データ(属性別) | e0747cc1 / 131130_tsuukoujinkou_zokuseibetu | 2018〜2024 | 756 | 0 | 2025-05-14 02:27 | 2025-05-14 | 属性・人数_の合計・ObjectId |
| 通行人口データ(年代別) | bcaecf7e / 131130_tsuukoujinkou_nendaibetu | 2018〜2024 | 1,512 | 0 | 2025-05-14 02:31 | 2025-08-07 | 年代・人数_の合計・ObjectId |
| 滞在人口データ(海外) | 9ca6c9d1 / (不明) | (不明) | (不明) | (不明) | 一覧の表では 2025-05-14 | item は 403(公開されていない) | 一覧の概要は「国籍別に集計」 |

- 共通: 6 層とも ArcGIS の表(幾何なし)・`年`・`月` は文字列(例「2024年」「1月」)・日の欄と日種の欄は無い・ライセンス CC BY 4.0・取得の形は CSV/GeoJSON(ハブ)と FeatureServer の API。年の範囲は 6 層とも `年` の重複なしの値で確かめた。月の範囲(1〜12 月)は滞在の性別の 2024 年だけで確かめた。
- 行数のうち 滞在の性別 20,112・通行の性別 12,096 は、仕分け C #12 の手元の行数と一致する(手元の層と今の公開の層が同じ版だという傍証)。
- 区の一覧で、概要に KDDI・Agoop・人流・位置情報・モバイル空間を含む行は e_0210 系の外に 0 件。区の層には「時刻別」「日別」「平日/休日別」の滞在人口の 2025 年以降の分は無い。近いのは施設の人数カウンター(peoplecountlog・入場者数・R-92 では 2025-12 で更新終了)だが、施設の入場者で滞在人口ではない。

## §3 代替(D1b ほか)

| 候補 | 2025 年以降 | 時刻の粒度 | 条件 | test の層に使えるか |
|---|---|---|---|---|
| D1b 国交省 全国の人流オープンデータ 1 km(Agoop) | **無い**(2019-01〜2021-12・予定なし・#11) | 昼・深夜・終日の 3 区分・全日/平日/休日 | 政府標準利用規約・無償・登録 | 使える(別ベンダ・ただし過去の年)。手元にある(R-92 §2-1) |
| 区の Power BI ダッシュボード | 不明(頁は 2026-07-22 更新・#6) | 不明 | ダウンロード不可・要望は問い合わせフォーム(#7) | 区への要望しだい=ユーザーの判断 |
| KDDI Location Analyzer(有償) | 有る(継続) | 1 時間・平日/休日(#10) | 1 ID 年額 240 万円(税別・R-92 #38) | 買うかはユーザー。K5 と同じパネル(R-56) |
| 同 無料トライアル | 有る | 同上 | 2 週間・法人/自治体・成果物の持ち出し禁止・終了後に削除(#9) | **使えない** |
| 都 景況指標ダッシュボード(KDDI Location Data) | 有る(週次) | 時刻別でない(前週比) | 閲覧だけ・渋谷が 10 エリアに入るか未確認(#12) | 使えない(比だけ) |
| 都オープンデータカタログ | 渋谷区の人流は無い(#13) | — | — | 無い |
| ドコモ 人口マップ / 有償の人口分布 | 閲覧は直近 24 時間と前年同月(d1 b-1) / 有償は 1 時間・平休日別 | 1 時間 | 閲覧だけ / 1 市区町村 1 か月 50 万円(R-92 #34) | 無償の範囲では使えない |
| 全国うごき統計 見える化マップ | 不明(#14) | 時間別の移動量の画面あり | 閲覧だけ・私的利用の外は禁止 | 使えない |
| Agoop | 有償(R-92 #36・#37)・無償は新宿区付近の約 1 時間の見本だけ(#15) | 1 時間級 | 見積り | 無償の範囲では使えない |
| 渋谷の AI カメラ 100 台(2023 年発表・一部をオープンデータ化の予定) | 公開は見つからない | — | — | 量が違う(通行・入店) |

## §4 v2 への含意(test の層の選び方)

1. **K5 は「公開待ち・時期不明」と書く** [案]。事前登録を K5 待ちにすると止まる。いま組める test は D1b だけ(別ベンダ・2019〜2021 の過去の年・目視の宣言つき=回答 10-13b 1-2)。K5 は「出たら足す 2 本目」として登録しておくのが現実的。
2. **見張り方(値を見ない)** [案]: 許可ドメイン内の検索 API(#1)の `modified` と、層の件数だけの問い合わせ(#4 の形)で、2025 年分の有無と行数が値を見ずに分かる。後者の `services3.arcgis.com` は取得の許可の一覧の外なので、定期の見張りにするなら先に承認が要る。
3. **混入の危険**: 区が同じ item に 2025 年の行を足す形なら、取得器 `tools/realworld_fetch/shibuya_jinryu.py` は年で切らない(`parse_csv` は全行を残す)ので、`--force` で取り直すと K5 の行が開封済みの層に入る。取り直す前に「2024 年まで」で切るか、K5 を別の封印層として保存する口が要る(W19 の `SOURCE_FAMILIES` に足す層の候補)[案]。
4. **独立性**: K5 は `kddi_la` と同じ元・同じパネル(R-56)で、独立なのは「時点」だけ(候補 ② の注意と同じ)。ベンダの独立は D1b だけが持つ。K5 と D1b の両方を test にする決定とは整合する。
5. **日種の軸**: 区の層には日種が無い。K5 が同じ形で出ても平日だけの比較は組めない(仕分け C #11 の訂正と同じ)。有償の KLA には平日/休日がある(#10)。
6. **2025 年分を早く得る道は 3 つで、どれもユーザーの判断**: (a) 区の問い合わせフォームで公開の予定を聞く (b) ダッシュボードのデータの提供を要望する (c) KLA を買う。費用は (a) が最も安い [案]。

## §5 空欄・未確認・親が確認すべき主張

空欄・未確認:
- 区が 2025 年分を載せる予定の有無と時期(公開の記述なし。問い合わせはしていない)。
- Power BI ダッシュボードに 2025 年分が入ったか(JS 描画・データの取り出しは POST が要り WebFetch では読めない)。
- 2025-05-14 より前に同じ層の旧版があったか=更新の周期(アーカイブは読んでいない)。
- 「滞在人口データ(海外)」(e_0210_001)が 403 になる理由(非公開化か削除か)・時刻の軸・期間。e_0210_005 の欠番の中身。
- 景況指標ダッシュボードの 10 エリアに渋谷が入るか(頁は JS 描画)。KLA の料金シミュレーションの頁も JS で読めず、料金は R-92 #38 に拠る。
- 都 TDPF の区の発表の PDF 本体は 10 MB を超えて読めず、Speaker Deck の文字起こしで代用した(30・42・44〜69 枚目は文字なし)。
- 検索の要約にだけ出た「都のデジタルツインに 2019-07〜2024-04 の渋谷の滞在人口(Agoop)」は原典を確かめられず、本答申では使っていない。

親が確認すべき主張 3 件:
1. 6 層とも 2025・2026 年の行が 0 件で、年は 2018〜2024 — 例 https://services3.arcgis.com/UtdeFTavkHfI94t2/arcgis/rest/services/131130_taizaijinkou_seibetu/FeatureServer/0/query?where=%E5%B9%B4%20LIKE%20%27%252025%25%27%20OR%20%E5%B9%B4%20LIKE%20%27%252026%25%27&returnCountOnly=true&f=json (件数だけ返る。値は返らない)
2. 6 層の `dataLastEditDate` は 2025-05-14 で、区の一覧の表では KDDI の 7 行の「対象期間」「更新頻度」が null — https://services3.arcgis.com/UtdeFTavkHfI94t2/arcgis/rest/services/131130_taizaijinkou_seibetu/FeatureServer/0?f=json と https://services3.arcgis.com/UtdeFTavkHfI94t2/arcgis/rest/services/131130_open_data_list/FeatureServer/0/query?where=%E3%83%95%E3%82%A1%E3%82%A4%E3%83%AB_ID%20LIKE%20%27e_0210%25%27&outFields=*&returnGeometry=false&f=json
3. KLA の無料トライアルは成果物の外部への持ち出しを禁じ、終了後の削除を求める — https://k-locationanalyzer.com/trial (区の頁の更新日 2026-07-22 も合わせて: #6 の URL)
