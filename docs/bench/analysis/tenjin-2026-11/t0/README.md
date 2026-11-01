# 天神(福岡市)の段 0「材料」 取得の記録(t0)

> 取得役(Opus 5.5)・2026-11-01 17:40〜17:54 UTC(日本時間 11-02 02:40〜02:54)。発注=[指示書 11-02 研究と取得](../../../../design/prompt-2026-11-02-research.md) 取得 4。許可の根拠=CLAUDE.md §7 の 2026-11-02 の文 ④(R-120 §4-2 の Q1〜Q8)。正=[R-120](../../../../research/v2-r120-tenjin-and-national-stage0-materials.md)(T/N の番号)・[R-121](../../../../research/v2-r121-four-layer-separation-survey.md) §2(四層)。形は渋谷の [sp0](../../spatial-2026-10/sp0/README.md) に合わせた。
> 置き場は gitignore 下の `data/tenjin/<層>/<材料名>/`(層=spatial・rules・population_business・transit)。索引 `data/tenjin/index.csv`(349 行・UTF-8・LF・全ファイルに sha256)。取得ログ `data/tenjin/_fetch_log.jsonl`(278 行=1 行 1 要求)。規約と robots.txt の写しは `data/tenjin/_terms/<ホスト>/`。合計 2,841,539,369 B。
> していないこと: commit・git add・台帳の編集・子サブの起動・pip・API キーの使用(環境変数 `ESTAT_APP_ID` はあるが、境界の zip は API を通らないので使っていない)・封印の層の読み出し。作業用の `data/tenjin/_tmp/` は最後に消した。
> 取り方: Python の http.client(識別子 `shibuya-sim-v2-research/0.1`)。転送は自動では追わず、Location のホストが許可の一覧の中のときだけ追う。1 秒に 1 回以下(BODIK は robots の Crawl-delay 2 に合わせて 2.05 秒)。失敗は 3 回まで。

## §1 取った/取らなかった表

日時はすべて 2026-11-01(UTC)。sha256 は主なファイルだけを載せた(全部は index.csv)。

| R-120 # | 材料 | 層 | 結果 | 置き場(data/tenjin/) | 大きさ(B) | sha256 | 取得 UTC |
|---|---|---|---|---|---|---|---|
| T1 | PLATEAU 福岡市 2024 CityGML(v4)の zip | spatial | **取った**・天神の udx だけ展開(§4・§7) | spatial/plateau_fukuoka_2024/40130_fukuoka-shi_city_2024_citygml_2_op.zip | 992,977,577 | `c27e723be17461bf72946dd2c56abb1412795d6be9283a03043aeee4b8e12803` | 17:48〜17:50 |
| T1 | 同 索引図(v4)の PDF | spatial | 取った | 同 40130_indexmap_op.pdf | 4,203,628 | `d57d8ab2bc5402ecf61dfb22d929f5463cbc1a5bf3b1f027965a3ed549ddc4a8` | 17:48 |
| T1 | 同 CKAN のメタデータ | spatial | 取った(meta) | 同 ckan_package_show.json | 936,715 | `e525d981ec433eebb688005d6dec364556a665dafebb99bd6c3fdec5a01106f2` | 17:48 |
| T1 | 同 3D Tiles/MVT・関連データ・v3 の zip | spatial | 取らず(発注は CityGML だけ) | — | — | — | — |
| T7 | 歩行空間ネットワーク 2018(博多の森・博多駅・天神駅)CSV と Shape の zip | spatial | 取った・展開 | spatial/walk_network_2018/ | 32,824 と 188,993 | `01e8d17cc244ae4076fd411420f05e1248e7b780ca8894a4e430e66f778b5219`(csv)・`1c0a465194ea4d2929b31c284db194e4f36e2133533a69ebdca3c9fbc799e4a9`(shp) | 17:42 |
| T7 | 同 2019(博多駅周辺) | spatial | 取った・展開(天神は含まない) | spatial/walk_network_2019/ | 22,351 と 59,717 | `80b3fd30072fbbd0d4fb87ef8c69978ee830abf455a8107cac85ffb55946570d`(csv)・`48a3942ead9c842f2a4bcc90afe3fd8bc9b68a8073942f94ffa429fcee3d664e`(shp) | 17:42 |
| T10 | 地下鉄の駅の位置(subway202607-3.csv) | spatial | 取った | spatial/subway_station_location/ | 4,127 | `00ac4404a9d1badc4214b2f3e8a0fccfcb08e55714656bcd7071a49d101389ee` | 17:42 |
| T30(N3) | e-Stat 2020 小地域の境界・福岡市中央区 40133(Shape・JGD2011・1 回) | spatial | 取った・展開 | spatial/estat_small_area_boundary_40133/A002005212020DDSWC40133.zip(応答の名前は `A002005212020DDSWC40133-JGD2011.zip`)・r2ka40133/ | 100,071 | `1326fa15fcdf996ec55cad20f22f3cb3943608affb901c67d88d867bde756480` | 17:50 |
| T8 | 飲食店営業等営業許可施設一覧(令和 8 年 9 月 30 日現在) | population_business | 取った | population_business/food_business_permits/r8.9.csv | 843,316 | `6b49029a17d0972137a924faff35d52e7900cd05f5210fa516cd7ac11cbc3cc1` | 17:42 |
| T25 | 平成 26 年経済センサス基礎調査 町丁・大字別(BODIK の XLSX 3 表) | population_business | 取った | population_business/econ_census_2014_chocho/ | 583,721・140,931・160,101 | `e75b4c6f…`・`89a9ec1c…`・`4348128e…`(全桁は index.csv) | 17:42 |
| T25 | 平成 24 年の町丁・大字別 | population_business | 取らず(BODIK の平成 24 年の行は市と区の表だけで、町丁の表が見つからない) | — | — | — | — |
| T25 | 経済センサス 2021 の町丁(e-Stat) | population_business | 取らず(発注の 8 件の外。e-Stat の取得は Q8 の境界だけ) | — | — | — | — |
| T26 | 登録人口(日本人・公称町別・男女・5 歳)CSV 22 本+定義書 PDF | population_business | 取った | population_business/registered_population_age5/ | 23 本・9,785,179 | index.csv | 17:42〜17:43 |
| T27 | 登録人口(日本人・公称町別)月次 CSV 57 本(2024-09〜2026-09) | population_business | 取った | population_business/registered_population_town_monthly/ | 57 本・7,346,629 | index.csv | 17:43〜17:45 |
| T27 | 同 世帯員数別 CSV 2 本(2024-09・2025-09) | population_business | 取った | population_business/registered_population_household_size/ | 167,690 と 123,244 | `13a59cf1…`・`5ea7531b…` | 17:42 |
| T31 | 福岡市繁華街の人流データ(ISIT・人流 55 本・マスク検知 55 本・設置箇所 1 本) | population_business | 取った(値は開いていない・§6 の 5) | population_business/aicamera_peopleflow/ | 111 本・77,741,622 | index.csv | 17:45〜17:49 |
| T4 | 都心部歩行者交通量等調査 天神 地上(令和 6・令和 3・平成 28・平成 23)と調査概要 | population_business | 取った(**再配布しない**) | population_business/pedestrian_count_survey/ | r06 4,920,252・r03 12,380,570・h28 12,284,717・h23 11,514,205・概要 191,101 | `4aa9b2cf…`(r06)・`a4cb5004…`(r03)ほか index.csv | 17:44 |
| T5 | 同 天神 地下(4 回分) | population_business | 取った(再配布しない) | 同 | r06 3,135,262・r03 2,835,106・h28 2,159,589・h23 2,287,456 | `db50f647…`(r06)・`fb4f6186…`(r03)ほか | 17:44 |
| T6 | 同 過去調査との比較(天神 地上・地下) | population_business | 取った(再配布しない) | 同 01_hikaku_tenjin_walker.pdf・03_hikaku_tenjin_under.pdf | 9,800,458・4,873,139 | `2ac7b77d…`・`20d08e11…` | 17:44 |
| T29(N13) | 法人番号 全件・福岡県(CSV・Unicode・令和 8 年 10 月 30 日更新・1 回) | population_business | 取った・展開 | population_business/houjin_bangou_fukuoka/40_fukuoka_all_20261030.zip | 10,162,784 | `c1af72d3e73284ac01dce78003e10e8cde728167a183ab4438f0647a0f1d4747` | 17:49 |
| N10 | 都市雇用圏(UEA)の zip | population_business | **取らず**(頁に利用条件の記載が無い・§2) | — | UEA_2020.zip は HEAD で 50,634 B | — | — |
| N14 | 食品衛生申請等システムの公開情報 | population_business | **取らず**(robots が公開の検索の場所 `/faspub/` を Disallow・規約が営利目的の再利用を禁じる・§2) | — | — | — | — |
| T28 | 北部九州圏 PT の概要版 | population_business | **読むだけ**(保存していない・要点は §2 の下) | — | 3,528,423(sha256 `d811628400ca3df4ecf03ee70388151ed373a4c8d029b23cd17d0fe8cd504481`) | — | 17:53〜17:54 |
| T9 | 地下鉄駅別乗車人員(XLSX) | transit | 取った | transit/subway_station_ridership/upload-.xlsx | 26,869 | `7b7f38866b5938085884591601f996dabeb41775578f199480a651832336df55` | 17:42 |
| T15 | 福岡市営渡船の GTFS(令和 8 年 1 月 30 日更新) | transit | 取った・展開 | transit/ferry_gtfs/data.zip | 17,479 | `f86901536657b9d831a5b858631ec8df10d7ad3d01678a29f36b7f59151b0806` | 17:45 |
| T13(N8) | GTFS データリポジトリの福岡県の一覧(API) | transit | 取った(meta) | transit/gtfs_data_jp_fukuoka/feeds_pref40_raw.json | 36,181 | `51370c304c26560bdb6883beffedc03573eae71d08da3147fd2e600eb5a95d58` | 17:47 |
| T13(N8) | 福岡市の分の GTFS の zip(今宿姪浜線乗合バス) | transit | **取らず**(転送先が一覧の外・§3。サイトの規約も読めていない・§6 の 1) | — | — | — | — |
| — | 規約の頁と robots.txt(10 ホスト・17 ファイル) | _terms | 取った(meta) | _terms/<ホスト>/ | 計 410,291 | index.csv | 17:40〜17:51 |

- 制度(rules)の層: 8 件の取得先には制度の材料が無い(最低賃金・条例などは別の出どころ)。`data/tenjin/rules/` は作っていない。
- 渋谷と同じく、応答そのまま(`*_raw.html`・`*_raw.json`・ダウンロードしたファイルそのもの)と、展開したもの(`extracted/`・`r2ka40133/`)と集計(`summary*.json`・`zip_listing*.json`)を分けた。
- 集計で分かったこと(値は検証の候補を除いて事実の数だけ):
  - **T1**: 天神の建物の LOD2 は **ある**(R-120 の未確認を埋めた)。3 次メッシュ 50303301 は Building 2,085 のうち lod2Solid 588・50303302 は 1,937 のうち 491。ほかの 4 メッシュは 14〜87。道路(tran)は LOD1 の Road が 1 メッシュ 304〜839。frn・brid・ubld は zip に無い(R-120 §0 の 3 と同じ)。`spatial/plateau_fukuoka_2024/summary_tenjin_udx.json`。
  - **T7**: 2018 の天神の部分(駅の周り約 1.6 km の箱=expedient)はノード 516・両端が入るリンク 637・範囲 北緯 33.5863〜33.5920・東経 130.3957〜130.4169。floor は全部 0(地上だけ・地下街は入っていない)。width は 2 が 295・3 が 165・99(不明)が 92。`spatial/walk_network_2018/summary_tenjin.json`。
  - **T10**: 駅の CSV の天神駅は 33.59132167, 130.39850167(発注の 33.5912N 130.3989E と一致)。出口の位置は入っていない(列は名称・郵便番号・住所・緯度・経度・URL)。
  - **T29**: 219,583 行のうち中央区(市区町村コード 133)28,161・所在地が「天神」で始まるもの 5,313(閉鎖を含む・絞り込みなし)。`population_business/houjin_bangou_fukuoka/summary.json`。
  - **T31**: カメラ 6 台は那珂川の福博であい橋・清流公園・夢回廊橋・春吉橋(中洲・春吉。天神駅の東 0.6〜1.0 km・±1 km の箱の中)。**天神駅の周りの通りには無い**。人流のファイルは 2022-04〜2026-10(R-120 の「最新 2026-09」から 1 か月増えた)。ほかに「マスク検知データ」55 本がある。`population_business/aicamera_peopleflow/summary_meta.json`。
  - **T4/T5**: PDF はどれも A3 横の 2 頁(令和 6 年度の地上だけ 4 頁=天神と今泉 × 平日と休日)で、地図の上に 7〜20 時の計を書いた形。**1 時間ごとの値は載っていない**(R-120 の未確認を埋めた)。平成 28 年度の地下は文字の層が 36 字/頁で、ほぼ画像。

## §2 規約の要点の表(ドメインごと)

| ドメイン | robots.txt | 規約の頁(読んだ日 2026-11-01 UTC) | 出典表示の文 | 商用 | 自動取得・生成 AI | 判断 |
|---|---|---|---|---|---|---|
| data.bodik.jp | `User-agent: *` は /user/・/admin/・/dataset/*?* などを Disallow(API とリソースのダウンロードは対象外)。AI と検索のボット(ClaudeBot を含む)に Crawl-delay 2 | odcs.bodik.jp/401307/tos/(福岡市オープンデータ利用規約) | 規約 第7条: ① データセットのメタデータの作成者欄の組織 ② リソースの名前 ③ リソースの URL | 可(CC BY 4.0) | 禁じる文なし。第1条「数値データ、簡単な表・グラフ等…は著作権の対象ではありません」 | 取った(2.05 秒間隔) |
| odcs.bodik.jp | `/wp-content/uploads/*.pdf$` だけ Disallow | 同上 | 同上 | 同上 | 同上 | 規約を読むだけ |
| www.city.fukuoka.lg.jp | 751 行の Disallow。調査の PDF・頁・渡船の頁は対象外 | /sub/tyosakuken.html(2018-11-22): 著作権は原則福岡市・「私的使用のための複製」や「引用」の外は無断で複製・転用できない・オープンデータは odcs.bodik.jp | 調査 PDF: 規定なし(引用なら出所の明示)。渡船の GTFS: 福岡市オープンデータサイト利用規約に準じる(CC BY 4.0) | PDF は不可(私的使用・引用の範囲)。GTFS は可 | 禁じる文なし | PDF は取ったが再配布しない。GTFS は取った |
| assets.cms.plateau.reearth.io | 404(無い) | PLATEAU Site Policy(www.mlit.go.jp/plateau/site-policy/)§3: 公共データ利用規約 第1.0版に準拠・3D 都市モデルの著作権は各地方公共団体・CC BY 4.0 と互換 | 「出典：国土交通省 PLATEAUウェブサイト(当該ページのURL)」型。加工したら加工の旨。国が作ったように見せない | 可 | 禁じる文なし | 取った |
| www.geospatial.jp | **`Disallow: /*?*`**(クエリ付きの URL を全部 Disallow) | (今回は読み直していない。データのライセンスは CKAN の license 欄=PLATEAU Site Policy) | — | — | — | CKAN の package_show を 1 回呼んだ(robots を読む前・§6 の 4) |
| www.pref.fukuoka.lg.jp | /cgi-bin/ などを Disallow・`Allow: /` | /contents/this-site-mensekietc.html(2026-07-07): 著作権は原則福岡県・免責・リンクはメールで知らせる | 記載なし | 記載なし | 禁じる文なし | 読むだけ(発注どおり) |
| gtfs-data.jp | `Disallow:`(空=全部可) | 利用規約は `docs.gtfs-data.jp/site/kiyaku.pdf`(SPA の JavaScript の中のリンク)。**ホストが一覧の外**・画像だけの PDF(3 頁)で文字が無い=**読めていない**(§6 の 1) | フィードごとの license 欄=CC BY 4.0(福岡県の 41 フィード全部) | フィードは可 | 不明(規約を読めていない) | 一覧(API)だけ取った |
| api.gtfs-data.jp | 403(robots.txt を返さない) | 同上 | 同上 | 同上 | 同上 | フィードの zip は転送先が一覧の外で止めた(§3) |
| www.csis.u-tokyo.ac.jp | /wp-admin/ だけ Disallow | /UEA/ と uea_code.htm・uea_data.htm に**利用条件の記載なし**。フッターは「Copyright© 2015(2020) Yoshitsugu Kanemoto All Rights Reserved.」 | 記載なし | 記載なし | 記載なし | **取らず**(発注の「記載が無ければ取らず」) |
| i2fas.mhlw.go.jp | **`Disallow: /faspub/`**(公開の検索の画面の form の action が `/faspub/IO_S010301.do`)ほか /faspte/・/manual/ など | /termsofuse.htm: §2 コンテンツは公共データ利用規約 第1.0版(出典「食品衛生申請等システム」(厚生労働省))。ただし §3 2) ウ「利用者は、これらの情報について**営利目的での複製・頒布等、再利用しないことに同意**するものとします」 | 「出典：「食品衛生申請等システム」（厚生労働省）（当該ページのURL）」 | 規約の中で食い違う(PDL1.0 と営利の再利用の禁止) | robots が検索の場所を禁じる | **取らず** |
| www.houjin-bangou.nta.go.jp | 404(無い) | /riyokiyaku/index.html: 公共データ利用規約 第1.0版 | 「出典：国税庁法人番号公表サイト（国税庁）（当該ページのURL）」・加工したら加工の旨・国が作ったように見せない | 可 | 禁じる文なし | 取った(1 回) |
| www.e-stat.go.jp | /core/・/admin/・/search/ などを Disallow(/gis/ は対象外) | /terms-of-use: 複製・公衆送信・翻案など自由・商用可・数値データは著作権の対象外 | 「出典：政府統計の総合窓口(e-Stat)（https://www.e-stat.go.jp/）」・加工の旨 | 可 | 禁じる文なし | 取った(1 回) |
| www.mlit.go.jp | (読んでいない) | PLATEAU Site Policy(上の行) | — | — | — | 規約を読むだけ |

**北部九州圏 PT の概要版の要点(読むだけ・保存していない)**: 頁 `/contents/hokubukyusyuken-persontrip5.html`(ページ ID 0796583・2020-11-20 更新)。第 5 回は平成 29 年度〜令和元年度。概要版は 18 頁(R2.3・北部九州圏都市交通計画協議会)で**全頁が画像**(文字の層なし)。目次は 1 調査について(p2)・2 圏の概要(p3)・3 人の動きの概況(p5)・4 自動車(p10)・5 公共交通(p13)・6 交通と居住地(p15)・7 これからの交通(p16)。p2「第5回調査では、約18万人の方に協力していただいています」。頁の本文: 1 人 1 日のトリップ数はほぼ横ばい・地区間の移動は福岡市・北九州市を中心に増加・鉄道の利用は概ね全年齢で増加(特に 15〜34 歳)。**集計表やデータの貸出の手続きは頁にも概要版の目次にも無い**(R-120 §4-3 と同じ)。事務局 5 者(九州地方整備局 企画部 広域計画課・福岡県 都市計画課・佐賀県 まちづくり課・北九州市 都市交通政策課・福岡市 交通計画課)。

## §3 転送先で止まったもの

| ホスト名 | 元の URL | 何 | 扱い |
|---|---|---|---|
| `prodgtfsdatareposharedinfrasta-filebucketcdfcd6de-1qqhtsxlwh6la.s3.amazonaws.com`(署名つきの一時 URL) | https://api.gtfs-data.jp/v2/organizations/fukuokacity/feeds/ImajukuMeinohamaLine/files/feed.zip?rid=current | 福岡市の GTFS(今宿姪浜線乗合バス)の zip の実体 | HEAD で 302 を見て止めた(本体は取っていない)。ログの署名の部分は伏せた |
| `docs.gtfs-data.jp` | http://docs.gtfs-data.jp/site/kiyaku.pdf | GTFS データリポジトリの利用規約(サイトの JavaScript の中のリンク・転送ではない) | **1 回だけメモリに読んだ**(200・1,075,902 B・保存していない)。画像だけの 3 頁で文字が取れず、2 回目(頁を画像にして読む)は実行の前に許可の判定で止まった=規約は読めていない |

## §4 zip の中身の確認(一覧の要約)

各 zip は展開の前に一覧を同じフォルダの `zip_listing.json` に残した(名前・大きさ・日付・拡張子の数・実行ファイルの印)。実行ファイルの拡張子(exe・dll・bat・ps1・sh・js・py ほか)は、どの zip にも無かった。

| zip | ファイル数 | 展開後の合計(B) | 中身 | 展開 |
|---|---|---|---|---|
| 40130_fukuoka-shi_city_2024_citygml_2_op.zip | 1,195 | 19,479,889,123 | gml 1,156・xml 32(codelists ほか)・xsd 2・pdf 2・xlsx 1・csv 1・md 1。udx の中: bldg 383・tran 400・dem 29(2 次メッシュの 4 分の 1 ごと・計 11.1 GB)・fld 295・htd 10・luse 12・lsld 11・tnm 8・urf 8・iur 2。**frn・brid・ubld は無い** | 天神の 8 メッシュの bldg と tran(16 本)と dem 2 本(503033_00・503023_50)だけ=18 本・1,615,737,875 B。ほかは zip のまま |
| fukuoka_20181009_csv.zip | 3 | 238,089 | facility・link・node の csv | 全部 |
| fukuoka_20181009_shp.zip | 19 | 2,335,386 | facility・link・node の shp 一式(cpg・dbf・prj・qpj・shp・shx)と **zip が 1 本入れ子**(facility.zip 94,048 B=同じ shp 一式 18 本の写し) | 外側は全部。入れ子の zip は展開せず一覧だけ(zip_listing_nested_facility_zip.json) |
| fukuoka_20191026_csv.zip | 4 | 147,817 | csv 3・Metadata(CSV)_SJIS.txt | 全部 |
| fukuoka_20191026_shp.zip | 19 | 1,365,857 | shp 一式 3 組・Metadata(SHP)_SJIS.txt | 全部 |
| A002005212020DDSWC40133.zip | 4 | 209,137 | shp・shx・dbf・prj | 全部 |
| 40_fukuoka_all_20261030.zip | 2 | 47,825,647 | CSV 1(47,825,159 B・UTF-8)と OpenPGP の署名 .csv.asc(488 B) | 全部 |
| data.zip(渡船の GTFS) | 15 | 179,113 | txt 12(agency・routes・stops・trips・stop_times・fare_*・translations・feed_info ほか)と **csv 3**(calendar.csv・calendar_dates.csv・payload.csv) | 全部(csv はデータの表で実行ファイルではない) |

- 渡船の GTFS は calendar を `calendar.csv` の名で持つ(規格の名前は `calendar.txt`)。読み口を作るときは注意。feed_info は 2026-01-01〜2027-12-31・版 2.0。

## §5 ライセンス台帳の行の案

台帳の形(| ディレクトリ | 内容・出典 URL | 取得日時 UTC | ライセンス(規約の要点・出典表示の文) | 大きさ・md5/sha256・用途 |)のまま。親が足す。sha256 の全部は `data/tenjin/index.csv`。

```
| data/tenjin/spatial/plateau_fukuoka_2024/(CityGML v4 の zip=展開していない部分を含む・索引図 PDF・CKAN のメタデータ・extracted/udx/ に天神の bldg 8・tran 8・dem 2) | 3D都市モデル(Project PLATEAU)福岡市(2024年度) v4。頁 https://www.geospatial.jp/ckan/dataset/plateau-40130-fukuoka-shi-2024 。実体 https://assets.cms.plateau.reearth.io/assets/c5/263250-3d72-486d-8b76-f8c62aaaca03/40130_fukuoka-shi_city_2024_citygml_2_op.zip(転送なし・Last-Modified 2026-03-12)と https://assets.cms.plateau.reearth.io/assets/ad/51f25f-ca37-4a39-ae92-24cc89c4dad2/40130_indexmap_op.pdf | 2026-11-01 17:48〜17:50 | PLATEAU Site Policy §3(公共データ利用規約 第1.0版に準拠・CC BY 4.0 と互換・3D 都市モデルの著作権は福岡市)。出典「3D都市モデル(Project PLATEAU)福岡市(2024年度)」(国土交通省)(https://www.geospatial.jp/ckan/dataset/plateau-40130-fukuoka-shi-2024)を加工して作成。国が作ったように見せない | zip 992,977,577 B sha256 c27e723be17461bf72946dd2c56abb1412795d6be9283a03043aeee4b8e12803・索引図 4,203,628 B sha256 d57d8ab2bc5402ecf61dfb22d929f5463cbc1a5bf3b1f027965a3ed549ddc4a8・展開 18 本 1,615,737,875 B。天神の段 1(建物の外形と階・LOD2・道路 LOD1・地形)。R-120 T1 |
| data/tenjin/spatial/walk_network_2018/ と walk_network_2019/(CSV と Shape の zip・展開) | 福岡市 歩行空間ネットワークデータ(平成30年10月=博多の森陸上競技場・博多駅・天神駅/令和元年10月=博多駅周辺)。https://data.bodik.jp/dataset/034bb06f-c433-4fba-abbe-a9079f8558fa ・https://data.bodik.jp/dataset/efee2abf-cbc7-407e-9aa4-fc458252e055 | 2026-11-01 17:42 | CC BY 4.0(福岡市オープンデータ利用規約・作成者 総務企画局 ICT戦略課)。出典「福岡市 総務企画局 ICT戦略課『福岡市（博多の森陸上競技場、博多駅、天神駅）の歩行空間ネットワークデータ』(リソースの URL)」 | 4 zip 計 303,885 B(sha256 01e8d17c…・1c0a4651…・80b3fd30…・48a3942e…)。天神の部分=ノード 516・地上だけ。段 1 の幅と段差。R-120 T7 |
| data/tenjin/spatial/subway_station_location/ | 地下鉄位置情報(福岡市地下鉄) subway202607-3.csv。https://data.bodik.jp/dataset/caf51a86-c429-4e15-a033-658de1de1945 | 2026-11-01 17:42 | CC BY 4.0(作成者 交通局)。出典「福岡市 交通局『福岡市営地下鉄の駅』(リソースの URL)」 | 4,127 B sha256 00ac4404a9d1badc4214b2f3e8a0fccfcb08e55714656bcd7071a49d101389ee。駅の点(出口なし)。R-120 T10 |
| data/tenjin/spatial/estat_small_area_boundary_40133/(zip と r2ka40133/) | 国勢調査 2020 小地域(町丁・字等)境界 福岡市中央区 40133 Shape JGD2011。https://www.e-stat.go.jp/gis/statmap-search/data?dlserveyId=A002005212020&code=40133&coordSys=1&format=shape&downloadType=5&datum=2011(転送なし・API キー不使用・1 回) | 2026-11-01 17:50 | e-Stat 利用規約(複製・翻案・商用可)。出典「政府統計の総合窓口(e-Stat)(https://www.e-stat.go.jp/)」・加工の旨 | 100,071 B sha256 1326fa15fcdf996ec55cad20f22f3cb3943608affb901c67d88d867bde756480。段 3 の地名帳 L1。R-120 T30 |
| data/tenjin/population_business/food_business_permits/ | 福岡市 飲食店営業等営業許可施設一覧(令和8年9月30日現在)r8.9.csv。https://data.bodik.jp/dataset/5925a9fb-3326-4499-9acd-7b18c03d5e32 | 2026-11-01 17:42 | CC BY 4.0(作成者 保健医療局 食品安全推進課)。出典「福岡市 保健医療局 食品安全推進課『福岡市内飲食店営業等営業許可施設一覧（令和8年9月30日現在）』(リソースの URL)」。2021-06-01 以降の許可は含まない | 843,316 B sha256 6b49029a17d0972137a924faff35d52e7900cd05f5210fa516cd7ac11cbc3cc1・3,918 行。段 0 の SR15。R-120 T8 |
| data/tenjin/population_business/econ_census_2014_chocho/ | 平成26年経済センサス-基礎調査 事業所に関する集計 町丁・大字別集計(XLSX 3 表)。https://data.bodik.jp/dataset/fddf5568-2af5-4480-a352-9ff2f531f5db | 2026-11-01 17:42 | CC BY 4.0(作成者 福岡市総務企画局)。出典「福岡市総務企画局『第１表 産業（大分類）別民営事業所数…』(リソースの URL)」ほか | 3 本 884,753 B(sha256 は index.csv)。段 0 の町丁目の事業所。R-120 T25 |
| data/tenjin/population_business/registered_population_age5/ | 福岡市 登録人口(日本人・公称町別・男女別・5歳階級別)自治体標準オープンデータセット(2004〜2025 の各 9 月末 22 本+データ項目定義書)。https://data.bodik.jp/dataset/093aecce-a5a3-4446-a133-986e3399ad05 | 2026-11-01 17:42〜17:43 | CC BY 4.0(作成者 総務企画局 統計調査課)。出典「福岡市 総務企画局 統計調査課『令和7年（2025年）9月末現在』(リソースの URL)」ほか。日本人だけ | 23 本 9,785,179 B(sha256 は index.csv)。段 2。R-120 T26 |
| data/tenjin/population_business/registered_population_town_monthly/ と registered_population_household_size/ | 福岡市 登録人口(日本人・公称町別)月次 57 本(2024-09〜2026-09)と世帯員数別 2 本。https://data.bodik.jp/dataset/0b01e765-2813-4103-afae-cdac833e7d0d ・https://data.bodik.jp/dataset/46cc9f86-7a45-446b-8b4e-82a0686b8b35 | 2026-11-01 17:42〜17:45 | CC BY 4.0(作成者 総務企画局 統計調査課)。出典は上と同じ形 | 59 本 7,637,563 B(sha256 は index.csv)。段 2 の世帯の検算。R-120 T27 |
| data/tenjin/population_business/aicamera_peopleflow/(**検証の候補・値は開いていない**) | 福岡市繁華街の人流データ(人流 2022-04〜2026-10 の 55 本・マスク検知 55 本・AIカメラ設置箇所 1 本)。https://data.bodik.jp/dataset/639cde20-5f12-4770-9404-3941e5d32656 | 2026-11-01 17:45〜17:49 | CC BY 4.0(公益財団法人九州先端科学技術研究所)。出典「九州先端科学技術研究所『福岡市繁華街の人流データ』(リソースの URL)」。欠損は 2022 年度の中央値で置き換え・欠損の旗 NaN=1 | 111 本 77,741,622 B(sha256 は index.csv)。カメラは中洲・春吉の 6 台。検証の候補(§6 の 5)。R-120 T31 |
| data/tenjin/population_business/pedestrian_count_survey/(**再配布しない・検証の候補**) | 福岡市 都心部歩行者交通量等調査 天神 地上・地下(令和6・令和3・平成28・平成23 年度)・過去調査との比較・調査概要の PDF 11 本と目次の頁 3 本。https://www.city.fukuoka.lg.jp/jutaku-toshi/kaihatsu/toshi/hokousya_kotsuryo.html | 2026-11-01 17:44 | 福岡市ホームページの著作権の規定(https://www.city.fukuoka.lg.jp/sub/tyosakuken.html): 私的使用のための複製・引用の外は無断で複製・転用できない。**オープンデータではない**。値を写すときは引用の範囲で出所(PDF の名前と頁)を明示 | PDF 11 本 66,381,855 B(r06 地上 sha256 4aa9b2cf3c6e666a7a4ef21128f7cfc43cb73a26ff7e626d7695cbdf061be502 ほか index.csv)。検証(test)の候補。R-120 T4〜T6 |
| data/tenjin/population_business/houjin_bangou_fukuoka/(zip・展開した CSV・集計) | 法人番号 全件 福岡県 CSV(Unicode)令和8年10月30日更新 40_fukuoka_all_20261030.zip。https://www.houjin-bangou.nta.go.jp/download/zenken/index.html(頁のトークンつきの POST・selDlFileNo=28480・転送なし・1 回) | 2026-11-01 17:49 | 公共データ利用規約 第1.0版。出典「国税庁法人番号公表サイト（国税庁）(https://www.houjin-bangou.nta.go.jp/)」を加工して作成 | 10,162,784 B sha256 c1af72d3e73284ac01dce78003e10e8cde728167a183ab4438f0647a0f1d4747・CSV 47,825,159 B・219,583 行(中央区 28,161)。段 0 の SR14。R-120 T29 |
| data/tenjin/transit/subway_station_ridership/ | 福岡市 地下鉄駅別乗車人員(1日平均) upload-.xlsx。https://data.bodik.jp/dataset/aa87a835-44b2-4730-a194-6e0676d45182 | 2026-11-01 17:42 | CC BY 4.0(作成者 総務企画局 ICT戦略課)。出典は上と同じ形 | 26,869 B sha256 7b7f38866b5938085884591601f996dabeb41775578f199480a651832336df55。駅の量の照合。R-120 T9 |
| data/tenjin/transit/ferry_gtfs/(zip と extracted/) | 福岡市営渡船 GTFS フィードデータ(令和8年1月30日更新)。https://www.city.fukuoka.lg.jp/kowan/kyakusen/shisei/documents/data.zip(頁 https://www.city.fukuoka.lg.jp/kowan/kyakusen/shisei/shieitosen_opendata.html) | 2026-11-01 17:45 | CC BY 4.0(福岡市オープンデータサイト利用規約に準じる)。出典「福岡市 港湾空港局『GTFSフィードデータ（令和８年１月３０日更新）』(URL)」。運航を保障しない | 17,479 B sha256 f86901536657b9d831a5b858631ec8df10d7ad3d01678a29f36b7f59151b0806。範囲の外(参考)。R-120 T15 |
| data/tenjin/transit/gtfs_data_jp_fukuoka/(一覧だけ) | GTFS データリポジトリ API の福岡県の一覧 https://api.gtfs-data.jp/v2/feeds?pref=40 | 2026-11-01 17:47 | API のメタデータ。各フィードの license 欄は CC BY 4.0。サイトの利用規約は未読(画像だけの PDF・ホストが一覧の外) | 36,181 B sha256 51370c304c26560bdb6883beffedc03573eae71d08da3147fd2e600eb5a95d58・41 フィード(西鉄・交通局・JR 九州は無い)。R-120 T13 |
```

## §6 問い

1. **GTFS データリポジトリの規約(docs.gtfs-data.jp)**: 規約の PDF は一覧の外の `docs.gtfs-data.jp` にあり、画像だけで文字が取れなかった(§3)。フィードの zip の実体も一覧の外の S3(§3)。福岡市の分は今宿姪浜線(天神を通らない)だけなので、天神の段 0 への影響は小さい(推測)。`docs.gtfs-data.jp` と実体の S3 を一覧に足すか、ユーザーが規約を目で読むか、取らないままにするか。
2. **発注のメッシュ番号の食い違い**: 発注の 50303563・50303564・50303553・50303554 は JIS X 0410 の式では北緯 33.625〜33.642・東経 130.663〜130.688(天神の東約 27 km)を指し、天神ではない。§7 の検算で 50302391・50302392・50303301・50303302・50303311・50303312(+箱に 20 m だけかかる 50303321・50303322)にした。展開した GML の範囲(gml:Envelope)で天神を確かめた。
3. **PLATEAU の DEM の大きさ**: DEM は 2 次メッシュの 4 分の 1 ごとの 1 ファイルで、天神の分だけで 2 本・1.44 GB(展開後)。段 1 で要る範囲だけ切り出すなら、残りを消してよいか。
4. **geospatial.jp の robots**: `Disallow: /*?*` がある。CKAN の package_show を 1 回(17:48Z)呼んだ後に robots を読んだ。渋谷の sp0 も同じ API を使っている。今後この CKAN のメタデータは、頁の HTML から読むか、API を使ってよいと決めるか。
5. **検証の候補の封印**: T4〜T6(通行量調査の PDF)と T31(AI カメラの人流)は R-120 で「検証」の用途。今回は大きさ・頁の数・文字の層の形・列の名・カメラの位置だけを見て、値は読んでいない(R-120 が本文に写した数を除く)。渋谷の `data/jinryu/` のように test の層として封印するか(するなら置き場を `data/tenjin/` の外へ移すか、index.csv の role を変えるか)。
6. **都市雇用圏(N10)**: 頁に利用条件が無いので取っていない(UEA_2020.zip は 50,634 B・Last-Modified 2026-10-13)。作者(金本良嗣)か CSIS に問い合わせるか、論文の定義(金本・徳岡 2002)から自前で組むか。
7. **食品衛生申請等システム(N14)**: robots が `/faspub/`(公開の検索)を Disallow し、規約が営利目的の再利用を禁じる。2021-06 以降の天神の営業許可は、OpenPOI が中に持つ同システムの分(sp0 §16 の注=PDL1.0 と表記)で代えるか、取らないままにするか。OpenPOI の表記と i2fas の規約の「営利の再利用の禁止」が食い違う点は要確認。
8. **PT(T28)**: 概要版は画像だけで集計表も貸出の手続きも無い。事務局への問い合わせはユーザー(R-120 §4-3 と同じ)。
9. **経済センサス 2021 の町丁(T25 の e-Stat の分)と国勢調査 2020 の小地域(T23)**: 発注の 8 件に入っていないので取っていない。e-Stat の統計表の取得(API なしのファイルの頁)を次に足すか。
10. **制度の層**: 8 件の取得先からは制度の材料が出ない。福岡県の最低賃金・福岡市の条例などは別の発注が要る(R-121 §2 の制度)。

## §7 天神の 3 次メッシュの検算

JIS X 0410: 1 次=緯度 40 分 × 経度 1 度(コード=⌊緯度×1.5⌋ と ⌊経度−100⌋)、2 次=1 次を 8 × 8(緯度 5 分 × 経度 7.5 分)、3 次=2 次を 10 × 10(緯度 30 秒 × 経度 45 秒)。

- 天神駅 北緯 33.5912・東経 130.3989:
  - 1 次: ⌊33.5912 × 1.5⌋ = ⌊50.3868⌋ = 50・⌊130.3989 − 100⌋ = 30 → **5030**(南端 33.3333・西端 130.0)
  - 2 次: (33.5912 − 33.3333) ÷ (5/60) = 3.094 → 3・(130.3989 − 130.0) ÷ 0.125 = 3.191 → 3 → **503033**(南端 33.5833・西端 130.375)
  - 3 次: (33.5912 − 33.5833) ÷ (30/3600) = 0.944 → 0・(130.3989 − 130.375) ÷ (45/3600) = 1.912 → 1 → **50303301**(北緯 33.58333〜33.59167・東経 130.3875〜130.4)
- ±1 km の箱: 緯度 ±1/111.32 = ±0.00898 度・経度 ±1/(111.32 × cos 33.5912°) = ±0.01078 度 → 北緯 33.58222〜33.60018・東経 130.38812〜130.40968。
- 箱にかかる 3 次メッシュ(0.001 度の格子で数えた):

| 3 次メッシュ | 北緯 | 東経 | 展開した GML の範囲(bldg の gml:Envelope) |
|---|---|---|---|
| 50302391 | 33.57500〜33.58333 | 130.3875〜130.4000 | 33.5748〜33.5835・130.3874〜130.4001 |
| 50302392 | 33.57500〜33.58333 | 130.4000〜130.4125 | 33.5749〜33.5836・130.3999〜130.4126 |
| 50303301(駅) | 33.58333〜33.59167 | 130.3875〜130.4000 | 33.5832〜33.5918・130.3874〜130.4004 |
| 50303302 | 33.58333〜33.59167 | 130.4000〜130.4125 | 33.5831〜33.5922・130.3997〜130.4129 |
| 50303311 | 33.59167〜33.60000 | 130.3875〜130.4000 | 33.5913〜33.6005・130.3874〜130.4004 |
| 50303312 | 33.59167〜33.60000 | 130.4000〜130.4125 | 33.5916〜33.6001・130.3998〜130.4128 |
| 50303321(北の縁・20 m) | 33.60000〜33.60833 | 130.3875〜130.4000 | 33.5998〜33.6086・130.3874〜130.4006 |
| 50303322(北の縁・20 m) | 33.60000〜33.60833 | 130.4000〜130.4125 | 33.5998〜33.6088・130.3997〜130.4126 |

- 箱の北端 33.60018 は 33.6 を 0.00018 度(約 20 m)だけ越えるので、50303321・50303322 も展開した(小さい=bldg 4.7 MB と 11.7 MB)。
- 発注の 4 つ(50303563・50303564・50303553・50303554)は 2 次メッシュ 503035(東経 130.625〜130.75)の中で、天神ではない(§6 の 2)。
- DEM は 2 次メッシュの 4 分の 1 ごと(接尾辞 00=南西・50=北西。zip の中の名で判断・GML の範囲で確認): 503033_dem_6697_00(北緯 33.5833〜33.6250・東経 130.375〜130.4375)と 503023_dem_6697_50(北緯 33.5417〜33.5833・同)で 8 メッシュを覆う。
