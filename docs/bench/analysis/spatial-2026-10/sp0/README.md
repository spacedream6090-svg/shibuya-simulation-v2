# 第 5 期 空間の段 0「材料」 取得の記録(sp0)

> 実装役(Opus 5.5)・2026-10-21〜。発注=R-119 §1 B の行のうち §2 の 12 行(#17・#18 を含む)を除いたもの(#9〜#16・#19)。正=[R-119](../../../../research/v2-r119-spatial-stage0-sources.md)・CLAUDE.md §7(許可の一覧)。置き場は gitignore 下の `data/spatial/<材料名>/`。1 行ごとの取得ログ(機械用)は `data/spatial/_fetch_log.jsonl`。commit は親。
> 範囲: 世界の bbox(OSM v8 meta.bbox)= 南 35.6505・西 139.6905・北 35.6685・東 139.7115(`src/shibuya/build/geo/w11_station_exits.py` の BBOX・約 3.8 km²=R-82 の W1)。

## 途中経過(上から順に追記)

- 2026-10-21 12:59Z **#9 OSM の歩行系** 取得=済。overpass-api.de(許可の一覧の Overpass API のドメイン・POST・転送なし・200)。クエリ `data/spatial/osm_walk/query_walk.overpassql`(世界の bbox・way highway=footway|steps|elevator|corridor|pedestrian|path と footway=*・indoor=corridor/node kerb・barrier=kerb・highway=crossing・footway=crossing・highway=elevator・entrance・`out meta geom`=編集日つき)。生データ `osm_walk_raw.json` 1,531,932 B・md5 `0f699e45c7e3d72f1d0a4ea58f47746b`・osm_base 2026-10-21T12:58:21Z。数え上げ `summary.json`。注: R-119 の列挙に pedestrian・path を足した(13.6 km の主な種類=R-82 §7 の「取らずに済ませる案」)。
- 2026-10-21 13:00Z **#10 OSM の駅の屋内** 取得=済。overpass-api.de(POST・転送なし・200)。クエリ `data/spatial/osm_station_indoor/query_station_indoor.overpassql`(R-90 §3 と同じ範囲 35.6555,139.6990,35.6620,139.7050 と同じ条件・出力だけ `out meta geom` に変えた=形と編集日つき)。生データ `osm_station_indoor_raw.json` 596,194 B・md5 `19c1feb902c47e7ae2445fbb4801ede0`・osm_base 2026-10-21T13:00:20Z。地物 720(way 461・node 256・relation 3。R-90 の 2026-10-06 は 703)・level 601・indoor 303・railway=platform 11・elevator 37・steps 119・turnstile 10・subway_entrance 25・indoor=corridor 29。
- 2026-10-21 13:02〜13:08Z **#11 東京都 区部点群** **取得せず(転送先・実体のホストが一覧の外)**。読んだもの: CKAN `package_show?id=tokyopc-23ku-2024`(www.geospatial.jp・200・転送なし)を `data/spatial/tokyo_pointcloud_23ku/ckan_package_show.json`(203,646 B・md5 `d8587c4c5a93ce543931b30660115374`)に保存。分かったこと: (1) 7 リソースのうち geospatial.jp に置かれているのは索引図の zip(64,888,110 B・PDF の索引図と書かれている)だけ。その URL は 302 で同じ geospatial.jp の `fs_download/…?preview=False` へ転送され、そこが **500(CloudFront の Error)** を返す(HEAD と GET の両方・13:03Z と 13:04Z)=図郭の一覧が取れない。(2) LAS の zip・DSM/DEM の PBF・等高線・**規約の PDF** の置き場は `gic-tokyo.s3.ap-northeast-1.amazonaws.com`、点群の 3D ビューア(3dview.tokyo-digitaltwin.metro.tokyo.lg.jp・TerriaMap)の目録は `tokyodt-open-catalog-bucket.s3.ap-northeast-1.amazonaws.com`。CLAUDE.md §7 が認める amazonaws.com は G空間情報センターの公開バケット(歩行空間ネットワークデータ=R-58 の `gsic-opendata`)だけで、この 2 つは名前が別=**一覧の外**として取らない(R-119 §2 の注・§4 の 3 の「親の確認が要る」)。(3) 都のデジタルツインの案内のサイトの `pointcloud_manual.pdf`(metro.tokyo.lg.jp・4,295,084 B・md5 `044e6a0e3c189d75c932c28604fb6b3b`)は取ったが、中身はスマートフォンの LiDAR の手引きで、区部点群の図郭や取得の手順は無かった(段 1 では使わない)。容量の空欄(R-119 §4 の 2)は埋まらず。
- 2026-10-21 13:05Z **#12 e-Stat 小地域の境界(区外)** 取得=済。www.e-stat.go.jp(`gis/statmap-search/data?dlserveyId=A002005212020&code=<区>&coordSys=1&format=shape&downloadType=5&datum=2011`・転送なし・200)。目黒区 13110(55,494 B・md5 `eef570d904616973cd91bbeec118b2bc`・88 ポリゴン)・港区 13103(101,195 B・md5 `113dcd517306676b0c4a3ddfb7b06b98`・140 ポリゴン)。`unzip -l` で中身が shp/shx/dbf/prj の 4 本だけと確かめてから `r2ka13110/`・`r2ka13103/` に展開(zip は 1 区 1 回)。**区の確認(R-119 §4 の 9 を埋めた)**: 世界の bbox を約 50 m の格子 1,591 点に切り、渋谷区(手元 r2ka13113)・目黒区・港区のポリゴンに点を当てた(標準ライブラリの点の内外判定)=渋谷 1,465・目黒 93・港 33・どれにも入らない 0。世田谷区など他の区は要らない。
- 2026-10-21 13:07〜13:08Z **#13 法人番号 全件(東京都)** 取得=済。www.houjin-bangou.nta.go.jp(nta.go.jp の下・`/download/zenken/index.html` へ頁のトークンつきの POST・転送なし・200・robots.txt は無い=エラーの頁)。**CSV 形式・Unicode** の東京都 分割 1・2(令和 8 年 9 月 30 日更新)を取った(R-119 は Shift-JIS の表の数を引くが、文字の欠けを避けるため Unicode にした=同じ中身の別の符号化)。`13_tokyo_all_20260930_01.zip` 37,260,999 B・md5 `55ea2ebc76f421d50d85d48fb357c471`/`_02.zip` 24,391,327 B・md5 `32ccfdbde1ae1d9ef947342952ee96a6`。`unzip -l` の中身=各 CSV 1 本と OpenPGP の署名の `.csv.asc`(488 B の文字)だけ=実行ファイルなし → 展開(CSV 183,500,967 B と 120,349,312 B・UTF-8)。規約=サイトの利用規約(公共データ利用規約 第 1.0 版に準拠・出典「国税庁法人番号公表サイト(国税庁)」・加工の旨・国が作ったように見せない)を 13:07Z に読んだ。集計 `summary_shibuya.json`(R-119 §4 の 13 の一部): 全 1,369,547 行・渋谷区 111,647 行・閉鎖でない最新 97,697 法人・うち住所に階の表記(「N 階」「NF」「地下 N」の正規表現=expedient)26,910(27.5%)・建物名らしい語 29,467(30.2%)。W1(13 町丁目)への絞り込みは段 1 で(未集計)。
- 2026-10-21 13:09〜13:15Z **#14 東京都 土地利用現況調査 GIS(令和 3 年区部)** 取得=済。カタログ API `package_show?id=t000008d2000000019`(catalog.data.metro.tokyo.lg.jp・200・13,395 B・md5 `fb6cd152e2f5705795db06ef1d2eb309`)で置き場が `data.storage.data.metro.tokyo.lg.jp/toshiseibi/R03.zip`(metro.tokyo.lg.jp の下=一覧の中・**R-119 §4 の 8 の「置き場のホスト」を埋めた**)と分かり、HEAD で転送なし・200 を確かめてから 1 回取った: 362,584,455 B(カタログの表記 371,195,904 B とは違う=表記は概数とみられる)・md5 `c8bf77469cbc932e11f641820c3bbd20`・Last-Modified 2025-02-11。`unzip -l` の中身=シェープ 2 組(土地利用現況・建物現況の shp/shx/dbf/prj/sbn/sbx)・データベース定義書の PDF・注意事項の docx の 15 本=実行ファイルなし → `R03区部全域/` に展開(1,320,952,802 B・名前は cp932)。**属性(§4 の 8 を埋めた)**: 建物現況 1,808,305 棟(渋谷区 CODE2=113 は 38,505)=地上階数 BV_3・地下階数 BV_4・構造 BV_5・用途 BV_6/BV_7(官公庁・事務所・専用商業・住商併用・宿泊・遊興・独立住宅・集合住宅ほか)・建築物の高さ BV_15・下面の高さ BV_14・計測高さ BV_16・町丁目(CODE5・NAME2)。定義書に無い列 `FLOOR` が 1 つある(中身は未確認)。土地利用現況 815,736 区画(渋谷区 20,090)。座標は平面直角座標系第 9 系。集計 `summary_shibuya_buildings.json`・`summary_shibuya_landuse.json`。**規約(§4 の 8)**: カタログの表記は「その他」。注意事項の docx は「国土地理院長の承認(平29国関公第444号)を得て作成した東京都地形図(S=1:2,500)を使用(6都市基交第513号)」「資料作成等で引用される際には、著作権法上の手続き等が生じるため…問い合わせ」と書き、定義書の PDF には「本書の無断転載、複製を禁じます」とある=**公表物に図や値を載せる前に都市整備局への問い合わせが要る(問い 2)**。
- 2026-10-21 13:12〜13:13Z **#15 渋谷区オープンデータ** **一覧だけ取得・データの実体は取らず(転送先が一覧の外)**。ハブの検索 API(city-shibuya-data.opendata.arcgis.com・200・転送なし)を `data/spatial/shibuya_opendata/hub_search_items.json`(261,959 B・md5 `9d0fc8625874ead3fa8282e40a1ede9b`・100 件=全 111 件のうち 1 頁目。次の頁の link は返らなかった)。対象の一覧(食品等営業許可・診療所/歯科・病院・薬局・助産所・施術所・店舗販売業・商店会・公衆トイレ・駐輪場の入出庫)は**全部が `services3.arcgis.com/UtdeFTavkHfI94t2/…/FeatureServer` の層**(R-119 §4 の 10 を埋めた)。ハブのダウンロードの口を転送なしで確かめた: `/api/download/v1/items/e68f…/csv?layers=0` は 302 で `services3.arcgis.com/…/replicafilescache/…csv` へ、`/datasets/e68f…_0.csv` は 301 で `hub.arcgis.com/api/download/…` へ転送=どちらも一覧の外 → 取得せず(R-119 §2 の #23 の承認待ち)。
- 2026-10-21 13:13〜13:21Z **#16 OpenPOI API** 取得=済。api.openpoiapi.com(転送なし・全部 200・robots.txt は 404)。仕様 `openapi.json`(16,781 B・md5 `aac465b2d73e4b129db109d4bd86d548`・API の版 1.0.0・license 欄「MIT (API) / 元データは提供元ごとに異なるライセンス」)と入口 `api_root.json`(406 B・md5 `52e4ce559fe525d61f399096ccb49714`・facility_count 3,179,528=R-76 の 3,372,487 から減った)。`/v1/search?bbox=…&limit=200` を世界の bbox から四分木(200 件なら 4 分割)で 1 秒に 1 回・373 回=`openpoi_search_quadtree.jsonl`(応答をそのまま・`licenses`/`attributions` は配列のまま・16,912,492 B・md5 `4b5926d932fc6c5e0ed06a2b224f5e52`)。**取り込みの門(R-76 §7-2・R-119 §4 の 12 を埋めた)** `summary.json`: 重複を除いて 22,335 件・bbox の外 0・同じ座標に 10 件以上=171 点(3,715 件・最大 162 件)・category=unknown 8,906(39.9%)・level が空でないもの 1 件・source=overture 12,787/jff(食品営業許可)9,491/国土数値情報 p29 35・p05 20・n02 2。**注(R-76 の前提との違い)**: OpenPOI は今は「東京都渋谷区食品等営業許可・届出一覧」(CC BY 4.0)と「厚生労働省 食品衛生申請等システム(オープンデータ)」(PDL1.0)を中に持つ(attribution で約 8,600 件)。OpenPOI を入力に使うと区の許可が照合に使えなくなる(R-76 §4-4 ①)ことが、jff の分でははっきり当てはまる。規約(docs.openpoiapi.com の legal・R-76 が 2026-09-26 版を読んだ)はドメインが取得の対象の外なので今回は読み直していない。
- 2026-10-21 13:23〜13:33Z **#19 商業施設の平面図 17 ドメイン** **確認と図の URL の索引だけ。図そのものは保存していない**(10-12 §4-12 R-91「図そのものは保存も配布もせず、事実だけ」を正とした=問い 3)。ドメインごとに robots.txt → 規約の頁(「自動・クロール・スクレイピ・ロボット・AI・人工知能・機械学習・生成・解析・ダウンロード・営利・許諾・複製」の語)→ フロアガイドの頁(HTML は解析だけして捨て、md5 と大きさだけ記録)→ 図の URL に HEAD、の順。結果は `data/spatial/floor_maps_check/` の `check_robots.jsonl`・`check_terms.jsonl`・`check_pages.jsonl`・`floor_map_assets_index.csv`(128 行・md5 `fd78b5759662ea1351c24356226c2d22`)。**robots と規約で禁止のものは 0**(R-112 と同じ。自動・AI の語は規約の禁止の文に無い。全部が「私的利用を超える利用は許諾」型か頁なし)。ドメインごとの結果は下の §2 の表。**接続できない 3 ドメイン**: shibuyastream.jp・shibuyastream.pictona.jp・shibuyacast.jp(curl exit 7「Could not connect to server」・13:24Z と 13:26Z・手元の環境の制限か相手の拒否かは不明=問い 4)。**一覧の外の置き場**: 東急プラザの頁に `stg.tokyu-plaza.com`(検証用のホストとみられる)の PDF・ハンズの階の図は `shibuya.hands.net`・`shibuya.tokyu-hands.co.jp`・ロフトの画像は `loft-images.s3.ap-northeast-1.amazonaws.com`=どれも HEAD もしていない。
- 2026-10-21 13:33Z #11 の索引図の zip をもう 1 度だけ試した=同じ 500(CloudFront の Error)。

## §1 取った行(R-119 §1 B の 11 行のうち)

| R-119 # | 材料 | 置き場(data/spatial/) | 主なファイル・大きさ・md5 | 取得(UTC) | 転送 | ライセンス |
|---|---|---|---|---|---|---|
| 9 | OSM の歩行系 | osm_walk/ | osm_walk_raw.json 1,531,932 B `0f699e45c7e3d72f1d0a4ea58f47746b` | 10-21 12:59 | なし | ODbL 1.0 |
| 10 | OSM の駅の屋内 | osm_station_indoor/ | osm_station_indoor_raw.json 596,194 B `19c1feb902c47e7ae2445fbb4801ede0` | 10-21 13:00 | なし | ODbL 1.0 |
| 12 | e-Stat 小地域の境界(目黒区・港区) | estat_small_area_outside/ | 13110 の zip 55,494 B `eef570d904616973cd91bbeec118b2bc`・13103 の zip 101,195 B `113dcd517306676b0c4a3ddfb7b06b98`(+展開) | 10-21 13:05 | なし | 政府標準利用規約 2.0 |
| 13 | 法人番号 全件(東京都・Unicode) | houjin_bangou_tokyo/ | _01.zip 37,260,999 B `55ea2ebc76f421d50d85d48fb357c471`・_02.zip 24,391,327 B `32ccfdbde1ae1d9ef947342952ee96a6`(+展開 CSV 303,850,279 B) | 10-21 13:07〜13:08 | なし | 公共データ利用規約 1.0 |
| 14 | 都 土地利用現況 GIS(令和 3 年区部) | tokyo_landuse_2021_ku/ | R03.zip 362,584,455 B `c8bf77469cbc932e11f641820c3bbd20`(+展開 1,320,952,802 B) | 10-21 13:09 | なし | カタログ「その他」・公表前に問い合わせ |
| 16 | OpenPOI | openpoi/ | openpoi_search_quadtree.jsonl 16,912,492 B `4b5926d932fc6c5e0ed06a2b224f5e52`(373 回・22,335 件) | 10-21 13:14〜13:21 | なし | 出どころごとに混在 |

- 一部だけ(メタデータ・確認の記録): #11(CKAN のメタデータと手引きの PDF)・#15(ハブの一覧 100 件)・#19(17 ドメインの robots/規約/頁の確認と図の URL の索引 128 行)。
- ライセンス台帳: [その 19](../../../../data-license-ledger.md) に 9 行。段 1 が読む索引は `data/spatial/index.csv`(51 行・path・kind=fetched/extracted_from_zip/derived/query・bytes・md5・source_url・fetched_utc・license・role)。機械用の取得ログは `data/spatial/_fetch_log.jsonl`(14 行)。

## §2 取らなかった行と理由

| R-119 # | 材料 | 理由 |
|---|---|---|
| 11 | 東京都 区部点群の zip | 図郭の一覧(索引図の zip)は geospatial.jp の転送先 `fs_download` が 500(13:03Z・13:04Z・13:33Z)。LAS の zip・DSM/DEM・規約の PDF は `gic-tokyo.s3.ap-northeast-1.amazonaws.com`、ビューアの目録は `tokyodt-open-catalog-bucket.s3…`=CLAUDE.md §7 の amazonaws.com の許可(G空間の公開バケット `gsic-opendata`=歩行空間 NW)とは別のバケット=**一覧の外**(問い 1) |
| 15 | 渋谷区オープンデータの実体 | ハブの口が `services3.arcgis.com`(302)・`hub.arcgis.com`(301)へ転送=一覧の外(R-119 §2 #23 の承認待ち) |
| 17・18 | 3dcel の点群と OBJ | 発注で除外(R-119 §2) |
| 19 | 平面図の図そのもの | 10-12 §4-12 R-91「図そのものは保存も配布もせず」=索引だけにした(問い 3) |
| §2 の 12 行・§E | 基盤地図情報・航空写真・Overture・gBizINFO・店の公式サイト・らくらくおでかけネット・jeki・点群の道具・Mapillary・駅の公式サイト・NAVITIME・train-media・cocoti・web.archive.org | 発注で除外。pip の新しい依存は入れていない(集計は標準ライブラリと手元の pymupdf だけ) |

**#19 のドメインごとの結果**(2026-10-21・robots/規約は R-112 §空欄 A の読みと突き合わせた。「図の数」は索引の行で、写真やボタンの画像が少し混ざる):

| R-112 # | ドメイン | robots.txt | 規約の頁(禁止の語) | フロアガイド | 図の URL(HEAD 200 の数・合計 B) |
|---|---|---|---|---|---|
| 1 | www.shibuya-scramble-square.com | 無し(HTML) | /terms/ 許諾が要る型・自動/AI の語なし | 各階の PNG | 16・2,184,144 |
| 2 | www.hikarie.jp | `Disallow:` 空 | /terms/ 同上 | 飲食の 5 階(?floor=)| 12・6,919,507 |
| 3 | www.tokyu-dept.co.jp | Sitemap だけ | 頁なし(/sitepolicy/・/site/・/privacy/ は 404) | ShinQs 8 階の PDF と JPG・フードショー 3 区画の JPG | 19・3,347,730 |
| 4・5 | shibuyastream.jp・shibuyastream.pictona.jp | 接続できない | 接続できない | 接続できない | 0 |
| 7 | shibuya109.jp | /wp-admin/ だけ | 頁なし(/terms/ ほか 404) | 各階の PNG 10 | 10・大きさは返らず |
| 8 | magnetbyshibuya109.jp | /wp-admin/ だけ | 頁なし | 各階の PNG 10(R 階を含む) | 10・大きさは返らず |
| 9 | www.tokyu-plaza.com | 空 | /use/ 許諾が要る型 | インライン SVG 1・PDF 1 | 1・4,168,401(`stg.` の PDF は一覧の外で触らず) |
| 10 | shibuya-fukuras.jp | 404 | /about/ に著作権の条項なし | 各階の PNG 7 ほか | 10・1,052,889 |
| 11 | www.s-markcity.co.jp | /wp/wp-admin/ だけ | 頁なし(/terms/ ほかはトップへ 302) | `<canvas>`(platinumaps)=図は取らない。頁の文字だけ | 0(アイコンのみ) |
| 13 | mitsui-shopping-park.com | クエリ付きの shopguide などを Disallow(floorguide.html は対象外) | /policy/ お願いの形 | 6 区画の PNG と floormap.png | 7・344,903 |
| 14 | www.shibuya-sakura-stage.com | 500 | /terms/ 許諾が要る型 | 案内図 PNG と店の写真 | 27・3,061,595 |
| 16 | www.loft.co.jp | LP と店 2 件を Disallow | /copyright/ 承諾が要る型 | 店の頁(shop_id=189)に図なし・画像は S3(一覧の外) | 0 |
| 17 | shibuyacast.jp | 接続できない | 接続できない | 接続できない | 0 |
| 18 | www.0101.co.jp | OAI-AdsBot・OAI-SearchBot を Allow | /user_guide/ 著作権の条項なし | JavaScript の描画(静的 HTML に図なし) | 0 |
| 19 | store.hands.net・info.hands.net | 404・403 | info.hands.net/help/ 許諾が要る型 | /shibuya/floor/ の文字(12,918 字)・図は shibuya.hands.net ほか(一覧の外) | 0 |
| 21 | gyre-omotesando.com | wp-admin ほかだけ | 頁なし(/terms/・/sitepolicy/ は 404) | 各階の PNG 6 | 6・1,128,365 |

## §3 R-119 §4 の空欄の埋まり

| §4 の番号 | 中身 | 今回 |
|---|---|---|
| 1 | OSM の歩行系の容量と付与率 | **埋まった**: 応答 1.53 MB。footway 1,297 本・68.6 km のうち width 4 本(0.19 km=0.3%)・kerb 0・level 166・tunnel 92・bridge 57・incline 8・footway=crossing 377/sidewalk 368。steps 260 本・width 0・incline 120。pedestrian 92 本・9.8 km・width 0。node の kerb=lowered 24・flush 10・no 3・barrier=kerb 29・highway=crossing 620(`osm_walk/summary.json`)。**width は実質使えない**(残る 13.6 km は既定幅=expedient のまま) |
| 2 | 点群の図郭の数と総容量 | 埋まらず(索引図が 500) |
| 3 | 点群の実体のホスト | **埋まった**: `gic-tokyo.s3.ap-northeast-1.amazonaws.com`(LAS・DSM/DEM・規約の PDF)。許可が及ぶかは問い 1 |
| 8 | 土地利用現況 GIS の属性・ライセンス・置き場 | **埋まった**: 置き場 `data.storage.data.metro.tokyo.lg.jp`・建物現況に地上/地下階数・構造・用途(細分類つき)・高さ・町丁目。ライセンスの本文はカタログに無く、注意事項と定義書の文は §1 と台帳のとおり。PLATEAU 2025 の luse との関係は段 1 で |
| 9 | e-Stat の区外の区と容量 | **埋まった**: 目黒区・港区(他区 0)・55,494 B と 101,195 B |
| 10 | 区オープンデータの実体のホスト | **埋まった**: 対象の一覧は全部 `services3.arcgis.com/UtdeFTavkHfI94t2/…/FeatureServer`。容量は未確認のまま |
| 12 | OpenPOI の W1 の件数と容量 | **埋まった**: 22,335 件・16.9 MB(373 回)・unknown 39.9%・積み重なり 171 点 |
| 13 | 法人番号の W1 の件数と建物名・階の割合 | 一部: 渋谷区の閉鎖でない最新 97,697 法人・階の表記 27.5%・建物名らしい語 30.2%(正規表現=expedient)。W1(13 町丁目)への絞り込みは未集計 |
| 15 | 平面図の頁の無い 7 件の規約 | 一部: tokyu-dept・109・MAGNET・マークシティ・GYRE は今回も頁なし・フクラス /about/ とマルイ /user_guide/ は著作権の条項なし。pictona は接続できず |
| 16 | 平面図のファイル数と容量 | 一部: 索引 128 行・HEAD で大きさが返ったもの合計 22,228,642 B(109・MAGNET は大きさが返らず・ストリームとキャストは接続できず)。MAGNET は各階の PNG・ロフトは店の頁に図なし・ハンズは文字の頁+一覧の外の図・GYRE は各階の PNG |

## §4 容量の実測

- data/spatial/ の合計 2,073,535,094 B(51 ファイル)。内訳: 土地利用現況 1,683,554,191 B(zip 362,584,455+展開 1,320,952,802 ほか)・法人番号 365,504,877 B(zip 61,652,326+CSV 303,850,279 ほか)・OpenPOI 16,938,246 B・点群のメタデータ 4,498,730 B・OSM 2,133,948 B・e-Stat 504,203 B・区の一覧 261,959 B・平面図の確認 138,940 B。
- R-119 の見積り 8.5〜10.5 GB(ほぼ点群)は、点群を取らなかったので当たらない。点群を除いた見積り(約 0.43 GB の zip)に対し、zip は 0.42 GB(展開を含めると 2.07 GB)。空き容量は取得の前に 391 GB。

## §5 次の段(段 1)が読む形

- 索引 `data/spatial/index.csv`(UTF-8・ヘッダつき)。列: `row`(R-119 の #)・`material`(フォルダ名)・`path`(リポの根からの相対)・`kind`(fetched / extracted_from_zip / derived(集計・確認の記録) / query)・`bytes`・`md5`・`source_url`・`fetched_utc`・`license`・`role`(input / diagnostic / meta)。
- 座標系: OSM・OpenPOI=WGS84 経緯度・e-Stat=JGD2011 経緯度・土地利用現況=平面直角座標系第 9 系(JGD2011)。法人番号は住所の文字だけ(座標なし)。

## §6 問い(取らずに止めたもの・判断が要るもの)

1. **点群(#11)の置き場**: LAS の zip と規約が `gic-tokyo.s3.ap-northeast-1.amazonaws.com`(都のバケットとみられる)。CLAUDE.md §7 の「この点群の zip に限って自動取得を許可」が、この S3 のバケットに及ぶか。及ぶなら、索引図(geospatial.jp は 500)の代わりに同じバケットの目録か PBF の図郭タイルから範囲の図郭を決める手順になる。展開した生データを残さず集計するには、LAS を標準ライブラリで読むか、新しい依存(laspy など=R-119 §2 #30)の承認が要る。
2. **土地利用現況 GIS(#14)の公表**: 注意事項は「資料作成等で引用される際には…問い合わせ」・定義書は「無断転載、複製を禁じます」。手元の研究開発で使うのは今のままでよいか。結果を外に出す前に都市整備局へ問い合わせるか(ユーザーの手)。
3. **平面図(#19)の図の保存**: 10-12 §4-12 R-91 は「図そのものは保存も配布もせず、事実だけ」。段 1 で事実を取り出すときに、図を一時に読む(メモリか scratch で読み、事実を写したら消す)形でよいか、data/ の下に置いてよいか。今回は索引だけにした。
4. **接続できない 3 ドメイン**: shibuyastream.jp・shibuyastream.pictona.jp・shibuyacast.jp は curl が「Could not connect to server」(他の 14 ドメインはつながる)。手元のネットワークの制限(サンドボックスなど)か相手の拒否かは分からない。サンドボックスの外し方は試していない。
5. **一覧の外の置き場**(どれも触っていない): `stg.tokyu-plaza.com`(東急プラザの頁が指す検証用とみられる PDF)・`shibuya.hands.net` と `shibuya.tokyu-hands.co.jp`(ハンズの階の図)・`loft-images.s3…amazonaws.com`(ロフトの画像)・`hub.arcgis.com`(区のデータ)。
6. **OpenPOI の中身の変化**: 今の OpenPOI は渋谷区の食品等営業許可と厚労省の食品衛生申請等システムを中に持つ(R-76 の時点の説明と違う)。R-76 案 B(照合・診断に置く)と「区の許可を直接取る」の関係を見直すか。
