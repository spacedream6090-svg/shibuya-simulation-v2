# データ・ライセンス台帳(2026-09-01初期化)

> 法務答申([v2-legal-licensing-deep-research.md](research/v2-legal-licensing-deep-research.md))の実装。**データ資産を追加するたびに1行追記**する。
> 設計原則: ①data type単位の層分離(OSM/PLATEAU/ODPT/人流を物理分離・重複統合しない=Collective Database維持)②出力スキーマからOSM生値を排除(内部ID+集計のみ)。

| ディレクトリ | 内容 | 出典 | ライセンス | 商用 | 備考 |
|---|---|---|---|---|---|
| data/realworld | OSM抽出(地図・POI)・ODPT実ダイヤ・経済センサス・気象庁実測・国勢調査系 | OSM/ODPT/e-Stat/気象庁 | **混在**(下記行参照)・v1の取得台帳 _ledger.jsonl 同梱 | △ | 層分離の再編はPhase 2で実施 |
| data/realworld(OSM由来分) | 渋谷の地図・POI 2,337 | OpenStreetMap | **ODbL 1.0** | △ | 公開・配布時にshare-alike発火。〔訂正(第333・[仕分け §3-6](reviews/triage-2026-10-13/README.md)・[回答 10-13b](design/v2-answers-2026-10-13b.md) §1 1-6)〕旧「出力に OSM 生値を載せない設計で回避」は誤り=法務答申(v2-legal-licensing-deep-research)自身が「回避にならない」と書く。ODbL 4.4(c) により Produced Work(ビューア)を公に使うと派生 DB も公に使ったことになり **4.6 の提供義務**(派生 DB 全体か、変更の方法)がかかる。W1・W7・W11 は OSM とそれ以外が混ざる=派生 DB の見込み。提供の方法は ② 構築の道具を「変更の方法」として公開 を第一候補に ①(OSM 由来の層を ODbL で公開)・③(Collective に作り直す)と比べ、決めるのは ODPT の作品の壁打ち(S2)。それまでに各層の OSM 混在の表を作る(法律の助言ではない) |
| data/realworld(気象分) | アメダス実測(v2手元は35日=2026-07-28〜08-31。930日はv1時点) | 気象庁 | PDL 1.0相当 | ○ | 外部提供時「予報」でなく過去実績/仮想シナリオと明示(気象業務法17条) |
| data/realworld(統計分) | 経済センサス9,872社・国勢調査 | e-Stat | 政府標準利用規約2.0 | ○ | 出典表示 |
| data/plateau | 渋谷3D建物3,531棟(東京都23区・2020年度版) | 国交省PLATEAU(**著作権は各地方公共団体に帰属**=サイトポリシー§3・親実読09-07) | PDL 1.0(CC BY 4.0/ODC BY/ODbL互換宣言) | ○ | 出典表示「出典: 国土交通省 PLATEAUウェブサイト(URL)」/加工時「『3D都市モデル(Project PLATEAU)東京都23区』(国土交通省)(URL)を加工して作成」。渋谷区単独2023年度版(plateau-13113-shibuya-ku-2023)への差し替え候補 |
| data/odpt | 駅・路線マスタ | ODPT | 基本ライセンス | △ | 商用化時はCC BY/CC0/PDLの107件へ絞る(答申) |
| data/persona_pool_v2 | 100万ペルソナ(国勢調査IPF較正+LLM生成来歴) | 自家生成(上流=e-Stat統計) | 自家 | ○ | 統計からの合成=個人情報非該当と整理可(PPC Q1-17/Q1-8類推)。生成LLMのライセンス貫通に注意 |
| data/calib | v1較正パラメータ(sigma_c/theta_scale) | 自家生成 | 自家 | ○ | |
| data/ground_truth | **現実整合アンカー台帳 registry.yaml(37本・出典/holdout分割付き)** | 各アンカーの出典はregistry内に記載 | 引用 | ○ | 北極星KPIの物差し。v2で成長させる |
| data/jinryu | 渋谷人流(1kmメッシュ2019-2021・同時滞在カーブ) | data/jinryu/SOURCE.md 参照 | SOURCE.md 参照 | △ | 較正専用・生データ再配布しない |
| data/realworld/osm(2026-09-06複写・v1由来) | 渋谷OSM地図v8(ノード3,499・エッジ4,944[地上4,448/デッキ306/地下190]・POI 2,337[営業時間・価格なし]・建物7,210)+**架空組織台帳**(organizations_*.json=v1の手続き生成・seed 42・経済センサス町丁目別に較正・実在名なし=名寄せ不可)+建物高さ・横断歩道・フロアガイド | OpenStreetMap / 自家生成(上流=e-Stat) | ODbL 1.0 / 自家 | △ | 出力にOSM生値を載せない(内部ID+集計のみ)・osm_date凍結 |
| data/realworld/kddi_la(2026-09-06収載) | KDDI Location Analyzer 滞在人口・通過人口(5エリア×24h×属性・2024年)=Power BI公開ダッシュボード由来の生JSON(2万行)+渋谷区オープンデータ日次CSV(shibuya_jinryu/2026)〔訂正(第333・仕分け C #11〜#12・X1)〕「Power BI 由来」は台帳の文言の疑い(区の ArcGIS の層と欄名・行数が一致)。「日次 CSV」は誤り=`shibuya_jinryu` は 2018〜2024 の**月次**(日の欄なし・取得日のフォルダ名を日次と読み違えた)。性別の 2 表に時間帯 24 区分あり・日種の軸は無い。**封印した `shibuya_jinryu` は開封済み `kddi_la` と同じ元(5 表の列名と行数が一致)=独立でない(照合用)**。回答 10-13b §1 1-2: 一覧から消さず印を付け、test は K5(2025 年以降)と D1b の両方に | 渋谷区オープンデータ／KDDI・技研商事 | CC BY 4.0(区OD)・ダッシュボード由来分は同系列として出典表示 | △ | 較正には使わず事後検証専用(holdout)・出典表示必須 |
| data/realworld/estat(2026-09-07取得) | e-Stat API取得JSON: 国勢調査2020 昼間/夜間人口(渋谷区)・経済センサス2021 企業等ベース集計(渋谷区) | e-Stat(総務省統計局) | 政府標準利用規約2.0 | ○ | 出典表示(「e-Stat」+統計名+年次)・APIキーは環境変数のみ |
| data/realworld/estat/国勢調査2020_小地域_年齢5歳階級男女別人口_東京都_渋谷区_全階級.json(2026-09-09 親取得・tools/world_data/estat_fetch.py=ページング付き) | e-Stat API getStatsData statsDataId 8003006792(国勢調査2020 小地域集計・年齢(5歳階級)・男女別人口)・cdAreaFrom/To 131130000-131139999+区計 13113=100 地域×60 分類=6,000 値(総数/男/女×0-4〜70-74・75 歳以上・15 歳未満/15-64/65 以上の集約)。09-07 取得分(1,500 値・0010-0150 のみ=70 歳以上と男女別が欠落)と重なる 1,500 値は完全一致。区計: 総数 243,883・男 117,907・女 125,976・70-74 10,307・75+ 21,900 | e-Stat(総務省統計局) | 政府標準利用規約2.0・出典表示「政府統計の総合窓口(e-Stat)国勢調査2020 小地域集計」・APIキーは環境変数のみ | ○ | W16 年齢×性別 raking の目標(14 階級→16 階級+不詳の分離・サブ J 親判断待ち 3 の解消)。再配布しない(gitignore) |
| data/realworld/estat/A002005212020DDSWC13113-JGD2011.zip(+展開 r2ka13113/・2026-09-08 ユーザー取得・zip のため §7 例外のアーカイブ除外に該当=親は取得せず) | e-Stat 統計GIS 境界データ: 国勢調査2020 小地域(町丁・字等)渋谷区 13113・世界測地系緯度経度(JGD2011)・Shape形式(shp/shx/dbf/prj・57,768 B・sha256 88e8f889e1bb119c…)。80 ポリゴン(KEY_CODE 80 一意・HCODE 8101=町丁・字等)・属性 JINKO 合計 243,883(=夜間人口アンカー E1 と一致)・SETAI 149,967・AREA 合計 15.12 km²・bbox 139.661-139.724E/35.642-35.692N | e-Stat(総務省統計局)統計GIS | 政府標準利用規約2.0(e-Stat 利用規約)・出典表示「政府統計の総合窓口(e-Stat)境界データ(国勢調査2020 小地域・渋谷区)」 | ○ | W16 母集団合成(町丁目→セル写像=建物床面積按分・親検収=dbf を標準ライブラリで解析)。再配布しない(gitignore) |
| data/realworld/plateau_2025(2026-09-08 親複写・原本=ユーザーの Unreal プロジェクト PLATEAU_SDK_test/Content/PLATEAU/Datasets/13113_shibuya-ku_pref_2025_citygml_1_op に SDK が複写していた udx 一式・ユーザーが 2026-07-09 頃 G空間情報センターから取得) | 3D都市モデル(Project PLATEAU)渋谷区(2025年度)CityGML v1_op・製品仕様書 5.0(v1 メモ: 作成 2026-03-13)・3次メッシュ 53393585/86/95/96 の中心 4 タイルのみ(≈2.9 km²)。複写した udx: tran(4 gml・57 MB・sha256 8457ce05/18b8b0c1/a74cc75a/ad04f9b0…)・bldg(4・1.0 GB)・dem(1・385 MB)・ubld(1・33 MB)・frn(2・69 MB)・brid(4・60 MB)+codelists(metadata なし)。計 1.6 GB。**tran 実査(親・grep)**: tran:Road 3,248・TrafficArea 4,053・lod3MultiSurface 5,782・RoadStructureAttribute=sectionType のみ・**TrafficVolumeAttribute/sectionID/routeName/width/numberOfLanes=0**(交通量属性なし=W10 区間突合には使えない) | 国土交通省 PLATEAU(G空間情報センター plateau-13113-shibuya-ku-2025) | PLATEAU サイトポリシー §3=PDL1.0(CC BY 4.0/ODC BY/ODbL でも可)・出典「3D都市モデル(Project PLATEAU)渋谷区(2025年度)(国土交通省)を加工して作成」(台帳 F15 で親確認) | ○ | W4 建物高さの原本(v1 index と同源)・LOD3 歩道面(R7 群衆物理の将来入力)・地下街 ubld(UG 層)。**フル zip=2026-09-09 ユーザー取得**: 13113_shibuya-ku_pref_2025_citygml_1_op.zip(649,322,807 B・sha256 f7437469d85b1d4a…・展開 4.79 GB・19,877 entries: udx bldg 29 メッシュ 1,627 MB/tran 30/dem 2/fld 55/frn 5/luse 2/ubld 1/urf 2/veg 1/wtr 2/brid 8/lsld 2+codelists 293+schemas+metadata(udx_13113_pref_2025_op.xml・resource csv)+specification+README+索引図)。中心 4 タイルの tran は CRC 一致(同一版)。展開先 data/realworld/plateau_2025/13113_shibuya-ku_pref_2025_citygml_1_op/。再配布しない(gitignore) |
| data/realworld/osm/station_entrances_overpass.json(2026-09-07取得) | Overpass APIで取得した駅出入口ノード45件(subway_entrance 33・train_station_entrance 12・bbox 35.6505-35.6685/139.6905-139.7115・渋谷駅14・表参道5・明治神宮前2ほか) | OpenStreetMap | ODbL 1.0 | △ | 世界データ構築W11(駅→出口→セル)の入力。出力にOSM生値を載せない・attic日は取得日(2026-09-07)で凍結 |
| data/realworld/pt_tokyo/pt6_d-1_purpose_mode_od.csv(2026-09-07ユーザー取得・元名d-1.csv) | 第6回東京都市圏パーソントリップ調査(2018年度・平日1日)「表d-1 目的種類別代表交通手段別OD表」e-Stat配布CSV(cp932・346,372行・発地×着地=計画基本ゾーン4桁コード655種[集計行含む]×目的種類8+計×代表交通手段[鉄道/バス/自動車/2輪車/自転車/徒歩/その他/不明/計]・拡大トリップ数) | 国土交通省(e-Stat 政府統計コード00600550・tstat 000001151670・stat_infid 000032066127)/東京都市圏交通計画協議会 | 政府標準利用規約2.0(e-Stat配布分)。協議会HP配布分はPDL1.0準拠(tokyo-pt.jp/terms実読: 「東京都市圏交通計画協議会ホームページ(当該ページのURL)を加工して作成」・国が作成したかのような公表禁止)。出典表示: 「第6回東京都市圏パーソントリップ調査(東京都市圏交通計画協議会)を加工して作成」 | ○ | U10来街目的構成比・方面別OD重みの較正入力(mechanism昇格)。ゾーンコード→町名の対応はtokyo-pt.jp「H30_zonecode.xlsx」が必要(未取得)。生CSVは再配布しない(gitignore) 〔第311 訂正(R-57): 「ゾーンコード→町名の対応は…(未取得)」は古い文=次行で H30_zonecode.xlsx 取得済み。時間帯別の c-2/c-3/b-4/c-4 は 2026-09-30 の節〕 |
| data/realworld/pt_tokyo/H30_zonecode.xlsx(2026-09-07ユーザー取得) | 第6回PTゾーンコード表(市区町村別一覧1,660行・都県別シート・大/中/計画基本/小ゾーン+該当町丁字名) | 東京都市圏交通計画協議会 tokyo-pt.jp/data/01_01 | PDL1.0準拠(協議会利用規約・出典表示) | ○ | 渋谷区=計画基本ゾーン0240-0243・小ゾーン10。派生集計 docs/bench/pt_shibuya/*.json(集計値のみ・出典表示つき)はリポ収載可 |
| data/realworld/osm/poi_opening_hours_overpass_20260907.json(2026-09-07取得) | Overpass APIで取得した飲食・物販POIのタグ(bbox 35.6505-35.6685/139.6905-139.7115・2,164件・opening_hours 565件=26.1%・price系14件) | OpenStreetMap | ODbL 1.0 | △ | W7営業時間の上書き入力(取得分のみmechanism)。出力にOSM生値を載せない・attic日=取得日で凍結 |
| data/realworld/osm/poi_tags_overpass_20260928.json(2026-09-28 取得・親・ユーザー許可 09-26) | Overpass API で取得した POI の生タグ+座標(bbox 35.6505-35.6685/139.6905-139.7115・amenity/shop/leisure/tourism/office/craft/healthcare の node/way/relation・`out center;`・3,516 件=node 2,999/way 510/relation 7・osm_base 2026-09-27T17:22:36Z・endpoint overpass-api.de)。クエリ全文=同名 `.query.txt`。**md5 2b4723293e1d5e633d97516c732b0eb2**。用途=W6 subcat の一次根拠(hall 14・attraction 5・leisure 4 の未分類の解消=D-97 ③) | OpenStreetMap | ODbL 1.0 | △ | 生値は data/ の外に出さない。取得は読み取り目的・再配布しない |
| data/realworld/osm/road_names_overpass_20260928.json(2026-09-28 取得・親) | 道路 way の name/ref/highway と折れ線座標(同 bbox・highway=motorway/trunk/primary/secondary/tertiary/unclassified/residential/living_street/pedestrian/service・`out tags geom;`・1,328 way・name か ref あり 396・osm_base 2026-09-27T17:20:36Z・endpoint overpass-api.de)。**md5 a918465a4f557be0dffe53f2ec74b662**。用途=W10 静的騒音場の区間突合(D-1 (a)・kasyo13.csv との名寄せ) | OpenStreetMap | ODbL 1.0 | △ | 同上 |
| data/realworld/osm/bus_stops_overpass_20260928.json(2026-09-28 取得・親) | バス停ノード(同 bbox・highway=bus_stop 127+platform/bus_station=計 129 node・名前あり 128・`out center;`・**osm_base 2026-07-24T11:04:51Z**=ミラー overpass.kumi.systems の版・本家は混雑で 3 回失敗)。**md5 0c7428c35ec7b81cc0d5bd0702ca91ea**。用途=バス停 127 件の座標(街路地物・§7.2 バス運行の停留所セル) | OpenStreetMap | ODbL 1.0 | △ | 同上。版が本家より古い(2 か月)ことを注記 |
| data/realworld/osm/street_features_overpass_20260907.json(2026-09-07取得) | Overpass APIで取得した街路地物2,009要素(横断歩道612・樹木384・交通信号166・駐車場130・乗降場128・バス停127・自販機54・街灯51・消火栓50・ベンチ38ほか・同bbox) | OpenStreetMap | ODbL 1.0 | △ | 世界カタログ写像(W18)と可視物・待ち行列・交通信号の入力。出力にOSM生値を載せない・attic=取得日 |
| data/realworld/road_census_r3/(2026-09-08親取得・§7緩和後) | 令和3年度 道路交通センサス 東京都「箇所別基本表」kasyo13.csv(2.28MB・cp932)+ヘッダ定義 KasyoFormat.xlsx+説明資料 kasyorep.pdf | 国土交通省 https://www.mlit.go.jp/road/census/r3/ | 公共データ利用規約1.0/政府標準利用規約2.0(出典表示: 「令和3年度全国道路・街路交通情勢調査」(国土交通省)を加工して作成) | ○ | W10静的騒音場の交通量・旅行速度・車線数入力。区間↔OSM klass対応表はC1で作成 |
| data/realworld/tokyo_noise/(2026-09-08親取得) | 東京都環境局 令和5年度 自動車交通騒音・振動調査結果(調査結果xlsx・常時監視測定地点csv・項目説明csv・概要pdf) | 東京都環境局 https://www.kankyo.metro.tokyo.lg.jp/vehicle/noise/result/cyousakekka/reiwa5 | 東京都オープンデータ(利用規約=出典表示) | ○ | W10較正点の時点更新(H23→R5)。渋谷区行の有無はC1で確認 |
| data/juelich_ped | 歩行者実験の軌跡データ(2009 bottleneck/unidirectional open・closed・2013 unidirectional/crossing_90=軌跡txt zip 5本+metadata json 5本・146MB) | Pedestrian Dynamics Data Archive, Forschungszentrum Jülich(DOI 10.34735/ped.da)・**v1リポの取得済み資産をローカル複写(09-08・Web取得ではない)** | **CC BY 4.0** | ○ | 出典表示必須。用途=U15-5較正(段階1: 幾何ごとに独立)・U15-6検証(基本図RMSE・比流量)。Zhang 2011「施設が違えば基本図は比較不能」のため渋谷屋外流への直接適用はしない(設計書U15-5) |
| data/realworld/jma_etrn | 気象庁 過去の気象データ検索(etrn)時別値・東京(北の丸公園・block_no 47662)2026-07-28〜08-31(35日×24時=840行・raw HTML 35本+CSV+_meta.json) | 気象庁 data.jma.go.jp(hourly_s1.php・親取得 2026-09-08・1req/2s・1回限り) | 気象庁ウェブサイト利用規約(PDL 1.0 互換・出典表示) | ○ | W13 の欠測補完(bosai 10分値が 08-08〜31 の12–23時で404)。CLAUDE.md §7 公的ドメイン例外。外部提供時は「予報」でなく過去実績と明示(気象業務法17条) |

## 持ち込まなかったもの(意図的)

| 資産 | 理由 |
|---|---|
| data/odpt_challenge(73件) | **チャレンジ限定ライセンス=用途限定**・事業化に使えない可能性大→本番構成から除外(答申推奨) |
| ~~data/juelich_ped(146MB)~~ | →**09-08 U15-8承認で複写済み(上表に行追加)**。旧: U15判断まで保留 |
| v1の runs/・Chronicle成果物 | v1リポに残置(参照専用) |

## モデル方針(答申の要約)

主軸=**Qwen3系(Apache 2.0・取消不能)**・日本語補強=CALM3/Sarashina2(Apache/MIT)。Swallow/Llama系は研究フェーズ限定(二重ライセンス・命名義務)。採用時は重み+ライセンス原文をハッシュ付きアーカイブ。

## 2026-09-10 追加(C7 修正のリサーチ・読み取り目的・スクラッチに取得・リポ data/ には置かない)

| データ | 出典 URL | 取得日 | 利用規約 | 用途 |
|---|---|---|---|---|
| 令和 3 年社会生活基本調査 第 4-1 表(曜日・行動の種類・時刻区分別行動者率)| e-Stat statInfId 000032224335/341/355/371/410(www.e-stat.go.jp) | 2026-09-10 | 政府標準利用規約(第 2.0 版)=出典明記で利用可 | D-56 a(h) 表(親再計算) |
| 鉄道ダイヤの総点検結果(事業者別の停車時分設定)| https://www.mlit.go.jp/kisha/kisha05/08/080722_3/01.pdf | 2026-09-10 | 国交省サイト利用規約(出典明記) | D-51 停車時分の既定値 |
| 都市鉄道の混雑率(令和 7 年度実績)| https://www.mlit.go.jp/report/press/content/002015141.pdf ・ 002015142.pdf | 2026-09-10 | 同上 | 鉄道 §2.6 の照合値更新 |
| 第 12 回大都市交通センサス 乗換え調査(本編・概要・駅別乗換え移動時間表)| https://www.mlit.go.jp/common/001179761.pdf ・ 001178977.pdf ・ 001179223.xlsx ほか | 2026-09-10 | 同上 | D-51 ホーム到達時間 |
| 小林・岩倉(2019)土木学会論文集 D3 75(4) 273-288 | https://www.jstage.jst.go.jp/article/jscejipm/75/4/75_273/_article/-char/ja | 2026-09-10 | J-STAGE 利用規約(閲覧・引用) | 確認時間・終着 45 秒 |
| 労働者健康状況調査(平成 24 年)第 1 表-2 | e-Stat statInfId 000023628233 | 2026-09-10 | 政府標準利用規約 | 深夜業従事率 21.8% |
| 第 12 回大都市交通センサス 参考表「利用目的別乗車降車時刻分布」(xlsx・data/research_cache) | https://www.mlit.go.jp/common/001179635.xlsx | 2026-09-10 | 公共データ利用規約(PDL1.0)・出典表示 | D-66 退出時刻の形。リポ time_dist_12.json と同一・脚注「帰宅トリップの補完なし」 |
| 東京都 令和2年国勢調査による東京都の昼間人口 第11表 町丁・字等別昼間人口(推計)(CSV・data/research_cache) | https://www.toukei.metro.tokyo.lg.jp/tyukanj/2020/tj20zv1100.csv | 2026-09-10 | 東京都統計部サイトポリシー=著作権法上の引用の範囲(二次利用条件の明示なし・オープンデータカタログ同一資源は 403 で未確認) | D-66 139 ha の昼夜比。**数値の引用のみ・ファイルは再配布しない** |
| 令和3年社会生活基本調査 第4-1表 時刻区分別行動者率(xlsx・data/research_cache) | https://www.e-stat.go.jp/stat-search/file-download?statInfId=000032224335&fileKind=0 | 2026-09-10 | 政府標準利用規約(第2.0版) | D-66 東京都平日 24 時間系列(仕事・通勤通学) |
| 東京都 テレワーク実施率調査 令和7年 1・5・9・12 月(PDF 4 本・data/research_cache) | https://www.hataraku.metro.tokyo.lg.jp/hatarakikata/telework/ 配下 | 2026-09-10 | TOKYO はたらくネット サイトポリシー=著作権法上の引用の範囲 | D-66 出勤率 0.88 の在宅項。**数値の引用のみ・再配布しない** |
| 厚生労働省 令和7年就労条件総合調査 結果の概要(読み取りのみ・data/ 未保存) | https://www.mhlw.go.jp/toukei/itiran/roudou/jikan/syurou/25/dl/gaiyou01.pdf | 2026-09-10 | 政府標準利用規約 | 年休 付与 18.1/取得 12.1/取得率 66.9% |
| 内閣府 渋谷駅周辺地域都市再生安全確保計画策定業務 基礎調査 概要版(読み取りのみ・data/ 未保存) | https://www.chisou.go.jp/tiiki/toshisaisei/yuushikisya/anzenkakuho/hojokin/27hojokin/27zigyouhoukoku-shibuya.pdf | 2026-09-10 | 政府標準利用規約(内閣府) | 139 ha 滞留者 14.5 万・乗降 227 万(重複除去)・休日/平日比 0.65 |
| 令和3年社会生活基本調査 平均時刻編 第30・31・35・36表(出勤/帰宅時刻の 15 分区分構成比・xlsx 4 本・data/research_cache/estat_r3_avgtime_*.xlsx) | https://www.e-stat.go.jp/stat-search/file-download?statInfId=000032224420 ・ …4421 ・ …4426 ・ …4427 &fileKind=0 | 2026-09-11 | 政府標準利用規約(第2.0版) | D-68 P1 の勤務窓投入(第31表・全国・雇用形態別)と判定(第30表・東京都)。出勤=家を出た時刻(始業ではない)。**派生物**: `docs/bench/anchors/commute_time_dist_r3.json`(第31/36表の 15 分ビン構成比を再正規化して転記・`python -m shibuya.build.sched.trial --build-anchor` で再生成可・出典と規約は同 JSON の `source` に記載) |


## 2026-09-17 追加(レーン L-R8 幾何の容量の実測化・読み取り目的・gitignore 下の data/research_cache に取得)

| データ | 出典 URL | 取得日 | 利用規約 | 用途 |
|---|---|---|---|---|
| 階避難安全検証法に関する算出方法等を定める件(平成12年5月31日 建設省告示第1441号)PDF 19 頁 | https://www.mlit.go.jp/notice/noticedata/pdf/201703/00006493.pdf | 2026-09-17 | 国土交通省サイト利用規約(出典明記) | R-8 ③ **在館者密度**(飲食室 0.7・売場 0.5 人/m²)と**必要滞留面積**(廊下 0.3 m²/人)。答申 [v2-c9-geometry-capacity-research.md](research/v2-c9-geometry-capacity-research.md) §1-3 |
| 階からの避難に要する時間に基づく階避難安全検証法に関する算出方法等を定める件(令和2年国土交通省告示第510号)官報 PDF 68 頁 | https://www.mlit.go.jp/common/001339931.pdf | 2026-09-17 | 同上 | 上の**現行版**の確認用。**テキスト層が疎で表を抽出できず**=逐語は旧告示から採った(答申 §4 空欄 7) |
| 道路構造令(平成15年7月改正)条文 PDF 30 頁 | https://www.mlit.go.jp/road/sign/kouzourei/0.pdf | 2026-09-17 | 同上 | R-8 ① 歩道 3.5/2 m・自歩道 4/3 m・車線 2.75〜3.5 m の既定幅員。**現行版は e-Gov 法令検索 API で別途確認**(差分は答申 lit メモに記載) |
| e-Gov 法令検索 API v1(条文 XML・**data/ 未保存**・読み取りのみ) | https://laws.e-gov.go.jp/api/1/articles;lawId=345CO0000000320;article=11 / ;article=5 ・ lawId=418M60000800116;article=4 ・ lawId=336M50000008006;article=1_3 ・ /api/1/lawdata/413M60000800151 ・ /api/1/lawdata/418M60000800111 | 2026-09-17 | e-Gov 利用規約(政府標準利用規約準拠) | 道路構造令・道路バリアフリー省令・消防法施行規則・鉄道技術基準省令・旅客施設バリアフリー省令の**現行版逐語** |
| 令和3年経済センサス‐活動調査 卸売業,小売業に関する集計(統計表 ID **0004003261** 産業編(都道府県表)・**0004003263** 産業編(市区町村表))e-Stat API 応答 JSON(**data/ 未保存**・セッションのスクラッチに取得) | https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData (appId は環境変数 ESTAT_APP_ID) | 2026-09-17 | 政府標準利用規約(第2.0版)・出典表示「令和3年経済センサス‐活動調査(総務省・経済産業省)」 | R-8 ② 店舗床面積の**分布**(特別区部 小売業 中央値 80.6 m²・渋谷区 平均 174.3 m²)。答申 §1-2・lit `stats__estat2021_retail-floor-area` |
| 鈴木ほか(2012)「都市開発による鉄道駅の混雑と施設容量に関する研究」運輸政策研究 15(3) pp.002-009(**data/ 未保存**・curl → stdout → pymupdf で読取のみ) | https://www.jstage.jst.go.jp/article/tpsr/15/3/15_TPSR_15R_08/_article/-char/ja/ | 2026-09-17 | J-STAGE 利用規約(閲覧・引用) | R-8 ④ **ホーム滞留容量 3.30 人/m²**(銀座線渋谷駅を含む)・改札 56.1・ES 63.5/53.9%・表―1 の単位(人/m・分)= R-7 の空欄解消 |


## 2026-09-17 追加(レーン R-3 = D-68 経路 3 の残 10 件・読み取り目的)

| データ | 出典 URL | 取得日 | 利用規約 | 用途 |
|---|---|---|---|---|
| 令和3年社会生活基本調査 **時間帯編 第15-4表**(曜日,男女,従業上の地位,**勤務形態**,行動の種類,時刻区分別行動者率(有業者)－全国,都道府県)xlsx 1 本・約 45 MB・シート `a015_4`・15 分 96 区分(`data/research_cache/estat_r3_jikantai_000032224355.xlsx`) | https://www.e-stat.go.jp/stat-search/file-download?statInfId=000032224355&fileKind=0 | 2026-09-17 | 政府標準利用規約(第2.0版)。引用表記「令和3年社会生活基本調査結果」(総務省統計局) | R-3 ①**日本に始業時刻の分布表が無い**ことの確認と唯一の代理(「仕事」行動者率の朝の階差)・⑧**交替制勤務の時刻像**(深夜 0 時の仕事率が固定の 4.8〜14.0 倍)。答申 [v2-d68-remaining-research.md](research/v2-d68-remaining-research.md) §1-①/⑧・lit `timeuse__estat2021_timeslot-shiftwork`。再配布しない(gitignore) |
| 令和5年住宅・土地統計調査 住宅及び世帯に関する基本集計 **表58-2-1**(統計表 ID **0004021722**・家計を主に支える者の通勤時間 8 区分 × 全国/都道府県/**市区町村**)e-Stat API 応答 JSON(**data/ 未保存**・セッションのスクラッチに取得) | https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData (appId は環境変数 ESTAT_APP_ID) / 表示面 https://www.e-stat.go.jp/dbview?sid=0004021722 | 2026-09-17 | 政府標準利用規約(第2.0版)・出典表示「令和5年住宅・土地統計調査」(総務省統計局) | R-3 ②**片道通勤時間の分布**(東京都 p50 43.7 分・渋谷区 p50 33.0 分・渋谷区の自宅/住み込み 5.07%)。社会生活基本調査の同分類は平成23年で終了。答申 §1-②・lit `stats__estat2023_commute-time` |
| e-Stat API `getStatsList` / `getMetaInfo`(統計表の全数検索・分類軸の確認。**data/ 未保存**・読み取りのみ) | https://api.e-stat.go.jp/rest/3.0/app/json/getStatsList ・ /getMetaInfo ・ 一覧 HTML https://www.e-stat.go.jp/stat-search/files?page=1&layout=datalist&toukei=00200533&tstat=000001158160&tclass1=000001158164&tclass2=000001158180&tclass3=000001158184&cycle=0 | 2026-09-17 | 同上(e-Stat 利用規約) | R-3 の否定形の確認: 「始業時刻」0 件 / 社会生活基本調査の「ふだんの片道の通勤時間」は平成23年で終了 / 平均時刻編 67 表に**勤務形態軸 0 件**。答申 §1-①/②/⑧ |
| data/realworld/estat/SSB2021_*.json(11 表・令和3年社会生活基本調査 生活行動編: 趣味・娯楽 行動者率/平均行動日数 全国×年齢×種目 `0003455361`・`0003455363`・東京都×年齢×性別×種目 `0003456615`・都道府県×種目 `0003456573`・`0003456575`・スポーツ `0003455173`・`0003456409`・学習・自己啓発 `0003454971`・`0003456261`・生活時間編 総平均時間 `0003457337`)+ data/research_cache/ssb2021_kaisetsua.pdf(用語の解説) | e-Stat API getStatsData(appId は環境変数 ESTAT_APP_ID・ファイルにキー無し)・https://www.e-stat.go.jp/dbview?sid=0003456573 ほか・https://www.stat.go.jp/data/shakai/2021/pdf/kaisetsua.pdf | 総務省統計局 | **政府標準利用規約(第2.0版)**・出典表記「令和3年社会生活基本調査結果」(総務省統計局) | ○ | 2026-09-17 取得(P1 サブ・第221)。gitignore 下。人の構成要素ラウンド(趣味)の入力 |

## 2026-09-28 追加(PENDING §2 の 5 段目=D-118 エネルギー収支・D-119 古典的選択モデルの政府統計・読み取り目的・gitignore 下の data/calib/hunger に取得・取得役サブ+親検収=md5 17 本一致・表3/表4/±199/164・第18-1表・xlsx 78+3 セルの再読 一致)

| データ | 出典 URL | 取得日 | 利用規約 | 用途 |
|---|---|---|---|---|
| 日本人の食事摂取基準(2025年版)策定検討会報告書 II 各論 1-1 エネルギー(章 PDF 34 頁=刷り pp.52–85)+正誤表(令和7年3月25日)→ `data/calib/hunger/bmr_pal_2025.json`(表3 基礎代謝量基準値と参照体重・表4/表5 PAL・本文の PAL 統計・4-3 個人間差 ±199/164 kcal/日) | https://www.mhlw.go.jp/content/10904750/001316461.pdf ・ https://www.mhlw.go.jp/content/10904750/001316480.pdf(一覧 https://www.mhlw.go.jp/stf/newpage_44138.html) | 2026-09-28 | **公共データ利用規約(第1.0版)(PDL1.0)**(厚労省サイトは政府標準利用規約 2.0 ではなく PDL1.0)・出典「日本人の食事摂取基準(2025年版)」(厚生労働省)(URL)を加工して作成 | D-118 K1 (c)/K5: 体ごとの EER=基礎代謝基準値 × 体重 × PAL ふつう+個人差 N(0, 199/164)。正誤表は表3 の見出し語のみ(数値の訂正なし・表2 Schofield 係数の訂正は未採録) |
| 令和6年国民健康・栄養調査 第14表 身長・体重の平均値及び標準偏差/第15表 BMI(xlsx・e-Stat 公開 2026-09-11)→ `nhns_r6_height_weight.json` | https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040502147&fileKind=0 ・ …statInfId=000040502148… | 2026-09-28 | 政府標準利用規約(第2.0版)準拠(e-Stat 利用規約)・出典「令和6年国民健康・栄養調査」(厚生労働省)・政府統計の総合窓口(e-Stat)を加工して作成 | D-118 体重の抽選(性 × 年齢階級の平均 ± SD・全国補正値・女性は妊婦 35 名除外) |
| 同 第13表 朝・昼・夕・間別にみたエネルギー及び主要な食品群別摂取量(xlsx)→ `nhns_r6_meal_kcal.json` | https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040502146&fileKind=0 | 2026-09-28 | 同上 | D-118 K7 時間帯の比の検算(**平均は欠食者の 0 kcal を含む**=注2) |
| 同 第10表 朝・昼・夕別にみた 1 日の食事状況(xlsx)→ `nhns_r6_skip_breakfast.json` | https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040502143&fileKind=0 | 2026-09-28 | 同上 | D-118 の照合: 朝食欠食率(20 代 総数 31.1%・男 37.3%・女 26.5%・欠食=菓子等のみ+錠剤等のみ+何も食べない)・外食/調理済み食の構成 |
| 令和6年国民健康・栄養調査報告 第1部(栄養摂取状況)・第2部(身体状況)・正誤表(令和8年9月4日・第22表のみ)(PDF・照合専用) | https://www.mhlw.go.jp/content/001675212.pdf ・ https://www.mhlw.go.jp/content/001742496.pdf ・ https://www.mhlw.go.jp/content/001745757.pdf | 2026-09-28 | PDL1.0(厚生労働省) | xlsx → 報告書 PDF の写し検査(77/77 行一致・取得役)+親の xlsx 再読 81 セル一致 |
| 令和3年社会生活基本調査 時間帯編 第8-1/8-2/8-3表(曜日,男女,ふだんの就業状態,行動の種類,年齢,時刻区分別行動者率(15歳以上)－平日/土曜/日曜・全国,11大都市圏,都市階級。DB 版 ID 0003457699/0003457701/0003457703 と同内容)xlsx 3 本・各約 46 MB → `ssb2021_meal_rate_15min.json`(「03_食事」の行だけ・全国/関東大都市圏/大都市 × 性 × 就業 × 年齢 22 × 96 区分) | https://www.e-stat.go.jp/stat-search/file-download?statInfId=000032224341&fileKind=0 ・ …342… ・ …343… | 2026-09-28 | 政府標準利用規約(第2.0版)準拠(e-Stat)・出典「令和3年社会生活基本調査結果」(総務省統計局)を加工して作成 | D-118 K4/K6 (i): 食事開始の 15 分刻み分布の**照合専用(較正に使わない)**。**R-46 の訂正**: この 3 表に東京都の行は無い(全国・11 大都市圏・都市階級のみ) |
| 同 時間帯編 第7-1表(15歳以上)・第4-1表(10歳以上)(曜日,行動の種類,男女,時刻区分別行動者率－全国,都道府県)xlsx 2 本・各約 18 MB → 同 JSON(東京都 × 人口集中地区の別 × 男女 × 曜日) | https://www.e-stat.go.jp/stat-search/file-download?statInfId=000032224339&fileKind=0 ・ …000032224335… | 2026-09-28 | 同上 | 東京都の食事の 15 分刻み分布(年齢・就業の軸なし)=照合専用。第8-1表 全国総数と第7-1表 平日全国総数の 96 値は完全一致 |
| 同 主要統計表 第18-1表(都道府県,主な行動の種類別行動者率・平均時刻－平日,男女総数,15歳以上)xlsx → 同 JSON `main_table_18-1` | https://www.e-stat.go.jp/stat-search/file-download?statInfId=000032262896&fileKind=0 | 2026-09-28 | 同上 | 朝食/夕食開始の行動者率と平均時刻(全国 77.2%/7:12・88.9%/18:58、東京都 70.0%/7:29・88.2%/19:18)=照合専用。R-46 の親確認値と一致 |
| 同 統計表利用上の注意(PDF) | https://www.e-stat.go.jp/stat-search/file-download?statInfId=000032224495&fileKind=2 | 2026-09-28 | 同上 | 記号「-」(行動者皆無またはサンプル皆無=0 と欠測が区別されない)・「…」の定義 |
| 改訂版『身体活動のメッツ(METs)表』(2012年4月11日改訂・2011 Compendium of Physical Activities の日本語版・821 コード・PDF 50 頁)→ `mets_selected.json`(座位 7・立位 3・歩行 12・家事 12・仕事 13・食事/横臥/睡眠 4=51 行・字化け 7 字は画像で確認して置換) | https://www.nibiohn.go.jp/eiken/programs/2011mets.pdf(→ https://www.nibn.go.jp/eiken/programs/2011mets.pdf・リンク元 https://www.nibiohn.go.jp/eiken/programs/kenko_energy.html) | 2026-09-28 | 医薬基盤・健康・栄養研究所 利用規約(政府標準利用規約 2.0 準拠)・出典「改訂版『身体活動のメッツ(METs)表』」(国立研究開発法人医薬基盤・健康・栄養研究所)(URL)・原典 2011 Compendium(Ainsworth ほか)は第三者著作物=数値のみ利用・表の文言は再配布しない | D-118 K1 (c) の METs(歩行 17190 3.5・速歩 17200 4.3・立位作業/販売員 11600 3.0・座位 07020 1.3・**睡眠 07030 1.0**(親が PDF で再確認。英語版 2011 Compendium の 0.95 は go.jp 外のため未取得=記憶値・採らない)・食事 13030 1.5)。2024 Adult Compendium の日本語版は未取得(研究所サイトに無し) |

## 2026-09-30 追加(R-57 PT 2018 の時間帯別表=D-115 ② 来街時刻の錨・読み取り目的・gitignore 下の data/calib/pt2018 に取得)

| ファイル | 出典 URL | 取得日 | 利用規約 | 用途・注意 |
|---|---|---|---|---|
| pt6_b-4.csv・pt6_c-2.csv・pt6_c-3.csv・pt6_c-4.csv(第 6 回東京都市圏パーソントリップ調査・平成 30 年・平日 1 日・基礎集計 表 b-4 ゾーン別時刻別滞留人口/c-2 ゾーン別目的種類別発着時間帯別発生集中量/c-3 ゾーン別代表交通手段別発着時間帯別発生集中量/c-4 ゾーン別代表交通手段別発着施設別発生集中量・cp932 CSV・md5 は data/calib/pt2018/MANIFEST.md) | e-Stat 政府統計コード 00600550・statInfId 000032066122/124/125/126(https://www.e-stat.go.jp/stat-search/files?page=1&layout=datalist&toukei=00600550&tstat=000001151670&tclass1val=0&cycle=0&tclass1=000001151671&tclass2val=0) | 2026-09-30(取得役サブ・親検収=md5 4 本一致・一覧ページ実読・0241 の集中量の合計 402,439 を再計算) | e-Stat 利用規約(政府標準利用規約 第 2.0 版に準拠・CC BY 4.0 と互換・商用利用可・出典の記載と加工の記載が必要・国が作成したかのような公表は禁止=親が実読) | 来街の時刻の形の錨(渋谷=計画基本ゾーン 0240〜0243・着時間帯 × 目的)。抽出率は約 1%=ゾーン × 目的 × 1 時間のセルは誤差が大きい(時間帯を束ねて使う)。較正に使うか照合に使うかは来街者の作り直しのアジェンダで決める。出典表示「第 6 回東京都市圏パーソントリップ調査(東京都市圏交通計画協議会)を加工して作成」 |
| pt6_tebiki.pdf(データ利用の手引き・46 頁) | https://www.tokyo-pt.jp/static/hp/file/data/tebiki.pdf | 2026-09-30(同上・md5 一致) | PDL1.0 準拠(tokyo-pt.jp の利用規約) | 表の定義(発生量=発時間帯・集中量=着時間帯)と精度の目安の出典。再配布しない |

## 2026-09-30 追加 その 2(空間と記憶の設計ラウンドのリサーチ R-58・R-65・R-69・読み取り目的・gitignore 下の data/research_cache に取得)

| ファイル | 出典 URL | 取得日 | 利用規約 | 用途・注意 |
|---|---|---|---|---|
| data/research_cache/r58/(歩行空間ネットワークデータ 渋谷地区 2017 のリンク/ノード/施設・渋谷南部 2020 のリンク/ノード・整備仕様 2 本・利用規約・整備範囲図=9 本・md5 は同フォルダの MANIFEST.md) | G空間情報センター「歩行空間ネットワークデータ等」 https://www.geospatial.jp/ckan/dataset/0401 | 2026-09-30(リサーチ役・親検収=md5 9 本・規約の条文) | 歩行者移動支援サービスに関するデータサイト利用規約+政府標準利用規約 第 2.0 版(出典の記載・加工の記載・商用可)。**第 2 条 (3)「データを利用した場合…同意したものとみなします」** | 歩道の幅員・勾配・段差・屋根の属性(渋谷南部 2020 は舞台の中に 25.1 km)。**9 本のうち 3 本(2017 のリンク・2020 のリンク・2024 の仕様書)は、geospatial.jp の転送先がエラーを返したため同センターの公開バケット(amazonaws.com)から取得した=CLAUDE.md §7 の許可ドメインの一覧の外。ユーザーの判断が出るまで構築に使わない** | **〔ユーザー決定 2026-10-03(指示書 10-03 §8 3-2 R-58)〕: G空間情報センターの公開バケット(amazonaws.com)からの取得を、同センターの保管先として認める。規約=政府標準利用規約 2.0。構築に使ってよい。許可ドメインの一覧(CLAUDE.md §7)に追加済み。**
| data/research_cache/r65/(第 12 回大都市交通センサス 乗換え調査の表 12 本と報告書・第 13 回の報告書=14 本・md5 は MANIFEST.md) | https://www.mlit.go.jp/common/001179216.xlsx ほか(MANIFEST に全 URL) | 2026-09-30(リサーチ役・親検収=経路別の表から渋谷の値を再計算) | 国土交通省ウェブサイトの利用規約(PDL1.0 準拠・出典の記載) | 縦の再現の照合の材料。乗換えの表は構築の入力側で使用中のものを含む(照合に使うなら入力から外す)。公表の駅別表の渋谷のピーク 3.3 分は除数の誤り(R-65) |
| data/research_cache/r69/(令和 3 年社会生活基本調査 主要統計表 第 8 表・生活時間 第 4-1 表・第 4-3 表=3 本・md5 は MANIFEST.md) | e-Stat statInfId 000032262873・000032223881・000032223883 | 2026-09-30(リサーチ役・親検収=該当行の値) | e-Stat 利用規約(政府標準利用規約 第 2.0 版に準拠・CC BY 4.0 と互換) | 箱の中の社会(職場・学校・家)の「一緒にいた人」の錨。調査は 2021 年 10 月(緊急事態の解除の直後) |

## 2026-10-03 追加(文章の推敲スキル yomiyasu=ユーザー承認の例外・リポに写した)

| ファイル | 出典 URL | 取得日 | 利用規約 | 用途・注意 |
|---|---|---|---|---|
| `.claude/skills/yomiyasu/`(SKILL.md・scripts/yomiyasu_lint.py・scripts/yomiyasu_diff.py・references/gemini-syntax.md・references/slop-catalog.md・references/domains/{business,essay,tech}.md・LICENSE=9 本。上流の `skills/yomiyasu/` の同名ファイルと git の blob が一致。改行だけ LF に正規化) | https://github.com/nanaism/yomiyasu(commit `8d5abeebe2dd20c2db005deaddcc50be43c59c0a`・`git clone` で取得し当該 commit を checkout) | 2026-10-03(親) | MIT(著作権表示とライセンス文を同梱=LICENSE を同じフォルダに置いた) | ユーザーが読む文章の推敲(指示書 10-03 §1)。写していないもの: `.claude-plugin/`(plugin.json・marketplace.json=プロジェクトのスキルには不要。marketplace.json に作者の個人メールが含まれるため、CLAUDE.md §7「個人メールを書かない」に従い除外)と `assets/algo-artis.png`(ロゴ画像・不要)。スクリプト 2 本は標準ライブラリだけで手元のファイルを読むだけ(親が実読。ネットワークに出ない)。 |

## 2026-10-03 追加 その 2(日次の現実データの再開=指示書 10-03 §10-1・検証専用・gitignore 下の data/realworld_live/ に取得・取得は tools/realworld_fetch/ のタスク 3 本)

位置づけ: シミュレーション本体はこのデータを読まない(検証専用=holdout 側)。ODPT の運行情報は電車の運行の入力にはしない(遅延は閉ループから生まれるべきもの)。防災 XML と ODPT の運休から「外れ値の日」の印を作り較正から外す材料にする。例外は反実仮想で実際の運休の日を再現する実験だけ(条件として明記)。保存先を `data/realworld/` でなく `data/realworld_live/` にした理由は、W13・W19 が `data/realworld/amedas` を日付で絞らずに読むため(つなぎ・PENDING K10)。ライセンスの要点は v1 の記載([記録 §7](bench/analysis/wallbounce-1003/realworld-fetch-check.md))の写しで、原典の規約ページの読み直しは **未実施(親の一次確認待ち)**。

| ファイル | 出典 URL | 取得日 | 利用規約 | 用途・注意 |
|---|---|---|---|---|
| data/realworld_live/amedas/(アメダス東京 44132 の 10 分値・日次 JSON。09-23〜10-03 を後追い取得し、以後 毎日 12:00 と 翌 00:30 の前日取り直し) | https://www.jma.go.jp/bosai/amedas/ | 2026-10-03〜(毎日) | 気象庁 公共データ利用規約(第 1.0 版)/ PDL1.0 準拠(v1 の記載・未再読) | 検証専用。保持約 10 日のため毎日取る。v1 は 08-08 以降毎日半日しか残っていなかった(昼に当日を取る欠陥)。v1 の実体は v1 リポに残置 |
| data/realworld_live/jma_xml/(防災情報 XML 長期フィード 4 本のエントリ) | https://www.data.jma.go.jp/developer/xml/feed/ | 2026-10-03〜(毎日 1 回。長期フィードは約 7 日分を載せる) | 同上(未再読) | 外れ値の日の印の材料。高頻度フィードは使わない |
| data/realworld_live/wbgt/(暑さ指数 WBGT 44132 の実況の月次ファイルと予測) | https://www.wbgt.env.go.jp/ | 2026-10-03〜(提供期間 10/21 まで) | 環境省 熱中症予防情報サイト=出典明記が必須(v1 の記載・未再読) | 検証専用 |
| data/realworld_live/odpt_rt/(ODPT リアルタイム。**〔第333・2026-10-13・ユーザー決定=[回答 10-13b](design/v2-answers-2026-10-13b.md) §5 追記〕** オープン枠=運行情報 6 社・列車の在線 2 社(都営・横浜市)・バスの在線 3 社(西武バス・都営・横浜市)を**路線で絞らず全部**保存(10-13 22:55〜)。チャレンジ枠=**作品に使う範囲だけ**(東急 2 線・京王 井の頭線の運行情報と JR 3 線の在線。先回りの収集はしない=限定ライセンス 第 4 条 1 項)。旧(10-03〜10-13 22:50)は渋谷 9 路線だけ・非圧縮) | https://api.odpt.org/・https://api-challenge.odpt.org/ | 2026-10-03〜(タスクの繰り返しは **5 分**=1 日 288 回。10-03 の台帳の「10 分」は誤記) | ODPT 利用規約(オープン枠とチャレンジ枠で異なる。チャレンジ枠の生データは**再配布しない**・用途は応募作品に限る)(v1 の記載・未再読) | 検証専用(holdout)。API キーは環境変数のみ。**親の決定(第333)=間隔は案 1**: 3 種類(運行情報・列車の在線・バスの在線)とも 5 分(`odpt_rt.CADENCE`・余裕 `CADENCE_SLACK_S=60`)・変化分だけの保存は運行情報だけ(日付の変わり目は必ず保存)・gzip(`.json.gz`・圧縮 約 8〜9 倍)。根拠: 遅延は分の単位で動き 5 分の系列で遅延の日を再現できる・1 分は要求 3 倍で ODPT の要求の頻度の条件が未確認。見込み 年 約 13 GB(10〜18 GB・バスの昼の倍率 2.0 は推測)=予算 50 GB の中。1 日の実測(10-14 以降の `--report`)で置き換える。超えそうならバスの在線を 10 分に。欠けた時間帯(PC が動いている間だけ回る)は `--report` に出し期の報告へ。実測と洗い出しは [odpt-collection-2026-10-13](bench/analysis/wallbounce-1012/odpt-collection-2026-10-13/README.md) |
| data/realworld_live/odpt_static/<取得日>/(ODPT オープン枠の静的データの**版**=路線・駅・時刻表(駅・列車)・種別・方面・曜日・バスの系統・バス停・バスの時刻表・乗降人員・運賃。28 社・118 組) | https://api.odpt.org/ | 版 1=2026-10-13 22:57〜10-14 00:5x(親が実行・404 組 全部 ok・1,034,592 件・HTTP 2,833 本・106 ファイル・56 MB gzip=推測 50〜70 MB の中)。以後は**ダイヤ改正ごとに 1 回**(`--source odpt_static --check` で新しい版の有無を見る。毎日は取らない) | ODPT 利用規約(オープン枠=出典表示) | 検証と範囲を広げるときの材料(渋谷に限らず広め=ユーザー決定)。gzip・1 版 約 50〜70 MB(推測)。`odpt:BusstopPoleTimetable`(バス停ごとの時刻表)は版に入れない(親の決定=系統の時刻表で足りる・要るときに足す)。ダンプの口は転送先 `dataodpt.blob.core.windows.net` が許可の一覧の外なので使わず、検索の口を分けて取る(許可はユーザー判断=PENDING §1-1)。チャレンジ枠の静的データは取らない(今の `data/odpt/challenge/` のまま) |
| data/calendar/syukujitsu.csv(内閣府「国民の祝日」CSV・1955/1/1〜2027/11/23・1,067 行・cp932・CRLF・21,538 B・md5 733fabb6b488794a0cd3d94df4b1f24a) | https://www8.cao.go.jp/chosei/shukujitsu/syukujitsu.csv | 2026-10-03(実行役・HTTP 200・Last-Modified 2026-02-02) | 内閣府ホームページ利用規約 https://www.cao.go.jp/notice/rule.html(親が 2026-10-03 に実読: 「権利表記の記載がない限り公共データ利用規約(第1.0版)(デジタル庁)が適用されます」=PDL1.0。CSV のページ自体に別の利用ルールの明示は無い) | 10a の暦の口(祝日)。範囲外(2027/11/23 より後)の開始日は manifest の検査で止める。W13 の手書きの祝日 2 行(2026/7/20・8/11)と一致。〔第333・10-13b §1 1-4〕同じ CSV を手を加えずに tests/fixtures/calendar/syukujitsu.csv に写し(git に入る。公共データ利用規約 第 1.0 版=出典の記載で複製・再配布可。出典の行は tests/fixtures/README.md)。data/calendar/ に無い環境では試験の前に conftest が fixture から複製する(data/ の gitignore は解かない)。更新は内閣府が 2 月に載せたときに手で取得し 1 commit |

## 2026-10-03 追加 その 3(賃金をつなぐアジェンダの材料=指示書 10-03 §6 ⑧ 8-1・読み取り目的・gitignore 下の data/calib/wage に取得・実行役サブ+親が MANIFEST の md5 と行を確認)

取得は e-stat.go.jp(API は `api.e-stat.go.jp`・appId は環境変数 `ESTAT_APP_ID` から読み、URL にも記録にも書かない)。利用規約は e-Stat の利用規約(政府標準利用規約 第 2.0 版準拠)。md5 と取得日時は `data/calib/wage/MANIFEST.md`。

| ファイル | 出典 URL | 取得日 | 利用規約 | 用途・注意 |
|---|---|---|---|---|
| hojin_nenji_fy2023_2025_cash_sales_labor.csv(財務省 法人企業統計調査 時系列・金融保険以外・年度次・表 0003060791。現金・預金/売上高/給与・賞与/従業員数 × 業種 62 × 規模 6 × 2023〜2025 年度) | e-Stat API statsDataId=0003060791 | 2026-10-03(実行役) | 政府標準利用規約 2.0 | 初期の運転資金の比率(現金・預金 ÷ 月の人件費: 全産業 16.06 か月・飲食 7.20・情報通信 15.16=`wage/hojin_ratios_2025.json`) |
| ec2021_kigyo_shibuya_sales_payroll_0004006360.csv(令和 3 年経済センサス‐活動調査 企業等に関する集計 経理事項等・渋谷区。**本所が渋谷区にある企業等の全事業所ぶん**) | e-Stat API statsDataId=0004006360(cdArea=13113) | 2026-10-03(実行役) | 同 | 売上の流入の比率の候補。区内の事業所だけの値ではない点に注意 |
| chinkou_r7_sanko2_pref_industry_kibokei.xlsx・chinkou_r7_t1_tokyo_kanagawa_age.xlsx・chinkou_r7_sanko1_pref47.xlsx(厚労省 令和 7 年賃金構造基本統計調査 参考表 2・表 1(東京・神奈川)・参考表 1) | https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040421203 / 000040421173 / 000040421202 | 2026-10-03(実行役) | 同 | 賃金の水準(東京都 × 産業別の所定内給与)。月の賃金の規模の推測(区内の組織に勤める 2,421 体で約 9.7 億円/月)に使用 |

## 2026-10-03 追加 その 4(R-77 車両と混雑=指示書 10-03 §8 3-8・読み取り目的・gitignore 下の data/research_cache/r77 に取得・リサーチ役サブ+親が MANIFEST を確認)

| ファイル | 出典 URL | 取得日 | 利用規約 | 用途・注意 |
|---|---|---|---|---|
| data/research_cache/r77/(国交省の PDF 8 本: 令和 7 年度 都市鉄道の混雑率調査の報道発表本文・資料 1(平均混雑率の推移と目安)・資料 2(三大都市圏の主要区間)・資料 3(都市部の路線の最混雑区間)・ほか混雑率の目安の検討資料と国土計画局の指標。md5 と URL は MANIFEST.md) | https://www.mlit.go.jp/report/press/content/002013572.pdf ほか(MANIFEST に全 URL) | 2026-10-03(リサーチ役) | 国土交通省ホームページ利用規約(政府標準利用規約 第 2.0 版準拠) | 路線ごとの混雑率(D10′ の更新・令和 7 年度)・定員の定義・混雑率の目安の版差。親が 9 区間の値を PDF から抽出して答申と一致を確認 |

## 2026-10-03 追加 その 5(R-81 飲食店の席数=指示書 10-03 §8 3-6・読み取り目的・gitignore 下の data/research_cache/r81 に取得・リサーチ役サブ+親が PDF の表を抽出して確認)

| ファイル | 出典 URL | 取得日 | 利用規約 | 用途・注意 |
|---|---|---|---|---|
| data/research_cache/r81/tokyo_h27_insyoku_1〜6.pdf(東京都 平成 27 年 飲食店の受動喫煙防止対策に関する実態調査の報告書 6 分冊。一般飲食店 1,241・遊興飲食店 1,600。md5 は MANIFEST.md) | https://www.hokeniryo1.metro.tokyo.lg.jp/kensui/kitsuen/sanko/insyokutentaisaku/files/27insyoku_1.pdf 〜 _6.pdf | 2026-10-03(リサーチ役) | 東京都保健医療局のサイトの利用規約(**未実読**。東京都の公式サイトは政府標準利用規約準拠が通例=親の一次確認待ち) | 客席数・店舗面積・客席面積の階級別の分布(席の密度の錨)。個票は無く同時分布は空欄 |

## 2026-10-03 追加 その 6(R-67 車と交通量=指示書 10-03 §8 3-8-4・§9-4・読み取り目的・gitignore 下の data/research_cache/r67 に取得・リサーチ役サブ+親が時間帯別の比率を再計算して確認)

| ファイル | 出典 URL | 取得日 | 利用規約 | 用途・注意 |
|---|---|---|---|---|
| zkntrf13.csv・zkntrfFormat.xlsx(令和 3 年度 全国道路・街路交通情勢調査 一般交通量調査 時間帯別交通量表 東京都と見出しの定義) | https://www.mlit.go.jp/road/census/r3/data/csv/zkntrf13.csv / .../xlsx/zkntrfFormat.xlsx | 2026-10-03(リサーチ役) | 国土交通省ホームページ利用規約(政府標準利用規約 第 2.0 版準拠) | 時間帯別の配分(今の一様配分の expedient の置き換えの錨)。渋谷区 48 区間のうち 24 時間観測の一般道は 4 区間 |
| od_r3_t12_avg_occupancy.xlsx(令和 3 年度 自動車起終点調査 表 12 平均乗車人数) | https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040170742&fileKind=0 | 2026-10-03(リサーチ役) | e-Stat 利用規約(政府標準利用規約 第 2.0 版準拠) | 範囲内の車に乗る人数の推測(1.40 人) |
| mpd_01_cyousakekka.pdf・mpd_02_cyousagaiyou.pdf(警視庁 交通量統計表 調査結果・調査概要) | https://www.keishicho.metro.tokyo.lg.jp/about_mpd/jokyo_tokei/tokei_jokyo/ryo.files/01_cyousakekka.pdf / 02_cyousagaiyou.pdf | 2026-10-03(リサーチ役) | 警視庁サイトの利用規約(**未実読**=親の一次確認待ち。東京都の機関で政府標準利用規約準拠が通例) | 都内の交通量の参考。使う前に規約を読む |

## 2026-10-03 追加 その 7(R-86 行動の分類との突き合わせ=指示書 10-03 §6 ②・読み取り目的・gitignore 下の data/research_cache/r86 に取得)

| ファイル | 出典 URL | 取得日 | 利用規約 | 用途・注意 |
|---|---|---|---|---|
| data/research_cache/r86/(令和 3 年社会生活基本調査 調査票 B 第 1-7 表 総平均時間(主行動)10 歳以上 全国の xlsx 1 本・md5 b0922b68dd3df4f8e121cb46a5eaa736) | e-Stat statInfId=000032261363 | 2026-10-03(リサーチ役) | e-Stat 利用規約(政府標準利用規約 第 2.0 版準拠) | 小分類 90 の平日の総平均時間(合計 1,439 分)=被覆の表の重み |

## 2026-10-03 追加 その 8(R-89 時間厳守の錨=保留の議題 H1・読み取り目的・gitignore 下の data/research_cache/r89 に取得)

| ファイル | 出典 URL | 取得日 | 利用規約 | 用途・注意 |
|---|---|---|---|---|
| data/research_cache/r89/mlit_001995846_delay_r6.pdf(国交省「東京圏の鉄道路線の遅延『見える化』(令和 6 年度)」・md5 3052855bfd8b181c267d06eae603f20a) | https://www.mlit.go.jp/report/press/content/001995846.pdf | 2026-10-03(リサーチ役) | 国土交通省ホームページ利用規約(政府標準利用規約 第 2.0 版準拠) | 遅延証明書の発行日数(路線別・20 日あたり平均 10.0 日)=遅刻の照合の候補。親が PDF から値を抽出して確認 |

## 2026-10-06 追加 その 1(R-93 極端な密度の群衆の物理=指示書 10-06 §7 の 4・読み取り目的・gitignore 下の data/research_cache/r93 に取得)

| ファイル | 出典 URL | 取得日 | 利用規約 | 用途・注意 |
|---|---|---|---|---|
| data/research_cache/r93/mlit_pri_kkk55.pdf(国土交通政策研究 第 55 号「交通の健康学的影響に関する研究 I」2005-10・md5 ea1a28d041e4a8f2296e623084b11e1d) | https://www.mlit.go.jp/pri/houkoku/gaiyou/pdf/kkk55.pdf | 2026-10-06(リサーチ役・親が md5 を確認) | 国土交通省ホームページ利用規約(政府標準利用規約 第 2.0 版準拠) | 混雑率 260% 時代の注の引用(R-93 §3)。読むだけ・再配布しない |

取得していないもの: 産総研の人体寸法データベース 1991-92 の統計表(airc.aist.go.jp)は許可の一覧の外のドメインなので、リサーチ役が作業用の一時領域で閲覧しただけ。数値(肩幅・胸部厚径)は画像の目視読みで親は未確認(R-93 の △)。

## 2026-10-06 追加 その 2(R-90 渋谷駅のデータの再調査=指示書 10-06 §7 の 1・読み取り目的・gitignore 下の data/research_cache/r90 に取得)

| ファイル | 出典 URL | 取得日 | 利用規約 | 用途・注意 |
|---|---|---|---|---|
| data/research_cache/r90/plateau_tech_doc_0108_ver01.pdf(PLATEAU ユースケース uc24-13「地下街データを活用したナビゲーションシステム v2.0」技術検証レポート・md5 445f4a06410658cbdee0f95ba7885d8b) | https://www.mlit.go.jp/plateau/file/libraries/doc/plateau_tech_doc_0108_ver01.pdf | 2026-10-06(リサーチ役・親が md5 を確認) | 国土交通省ホームページ利用規約(政府標準利用規約 第 2.0 版準拠) | 渋谷駅の LOD4 の作られ方と範囲(R-90 §1)。読むだけ |

取得していないもの: ODPT(件数を数えただけ・生データなし)・Overpass(件数と応答の md5 だけ。overpass-api.de が 504 のとき overpass.kumi.systems に 1 回問い合わせ、時間切れで何も受け取っていない)・jeki の PDF(標準出力で読んだだけ)・駅の各社の構内図(規約により取得せず=R-90 §4・R-91 §3)。

## 2026-10-06 追加 その 3(R-96 大人の矯正後の視力=指示書 10-06 §7 の 7・読み取り目的・gitignore 下の data/research_cache/r96 に取得)

| ファイル | 出典 URL | 取得日 | 利用規約 | 用途・注意 |
|---|---|---|---|---|
| data/research_cache/r96/r5_hoken_tokei_04.xlsx(学校保健統計調査 令和 5 年度・裸眼視力と矯正の表・md5 b85806d1091f05b4aef11ff6c22d89eb) | e-Stat(www.e-stat.go.jp・転送なし。URL は MANIFEST) | 2026-10-06(リサーチ役・親が md5 を確認) | 政府標準利用規約(第 2.0 版)=出典明記で利用可(e-Stat の既存の行と同じ扱い) | 17 歳の矯正の割合(若い大人の近い錨・R-96 §3)。読むだけ |

## 2026-10-06 追加 その 4(R-99 勤務の時刻・日数・雇用形態と約束の頻度の公的統計=リサーチの指示 10-06 夜 §2 A1〜A3・C2・読み取り目的・gitignore 下の data/research_cache/r99 に取得)

| ファイル | 出典 URL | 取得日 | 利用規約 | 用途・注意 |
|---|---|---|---|---|
| data/research_cache/r99/ の xlsx 9 本(令和 3 年社会生活基本調査 時間帯編 第14表・第15-1〜15-3表、生活時間編 第68-3表・第74-6表・第74-9表/令和 4 年就業構造基本調査 地域結果 第19表/令和 3 年経済センサス-活動調査 第6-2表。md5 9 件は MANIFEST.md=親が全件一致を確認) | e-Stat(www.e-stat.go.jp・転送なし。URL は MANIFEST) | 2026-10-06(リサーチ役・親が md5 を確認) | 政府標準利用規約(第 2.0 版)=出典明記で利用可(e-Stat の既存の行と同じ扱い) | 職業別・雇用形態別の「仕事」の 15 分ごとの行動者率(始業の代理)・曜日別の仕事の行動者率・年間就業日数・従業上の地位(区まで)・交際と受診の行動者率。R-99 §1〜§4 |

## 2026-10-06 追加 その 5(R-101 範囲と周辺の学校の一覧=リサーチの指示 10-06 夜 §2 A5・読み取り目的・gitignore 下の data/research_cache/r101 に取得。学校のサイトからは取得していない)

| ファイル | 出典 URL | 取得日 | 利用規約 | 用途・注意 |
|---|---|---|---|---|
| data/research_cache/r101/schools_overpass_20261006.json(+ クエリ .query.txt・md5 8f60b8c3…) | Overpass API(overpass-api.de・osm_base 2026-10-06T14:13:27Z) | 2026-10-06(リサーチ役・親が md5 を確認) | OpenStreetMap ODbL 1.0(既存の Overpass の行と同じ扱い。派生物は ODbL) | 学校の点(`amenity=school/university/college`)の位置と名前。R-101 の一覧の突き合わせ |
| data/research_cache/r101/r7_*.csv 8 本(東京都公立学校一覧 令和 7 年 5 月 1 日時点・小/中/義務教育/高校全日制・定時制/高校住所/特別支援 2 本。md5 は MANIFEST) | 東京都教育委員会(www.kyoiku.metro.tokyo.lg.jp・転送なし) | 2026-10-06(同) | **都教委サイトポリシー「著作権について」=私的使用・引用の範囲(CC BY ではない)**。使うのは学校名・所在地・人数の事実だけ。再配布しない | 公立の小中高の一覧(範囲と周辺) |
| data/research_cache/r101/03sensyugakko・06kakusyugakko・03elementary・06juniorhigh・09high_zennichi・15high_tushin の CSV 6 本(私立・専修・各種学校の一覧 令和 8 年 4 月 1 日時点ほか。md5 は MANIFEST) | 東京都生活文化局(www.seikatubunka.metro.tokyo.lg.jp・転送なし) | 2026-10-06(同) | **生活文化局サイトポリシー 第1 著作権=私的使用・引用の範囲(CC BY ではない)**。同上 | 私立・専修・各種学校の一覧。**台帳への書き方(事実だけの利用で足りるか)はユーザーの判断待ち(PENDING §1-1)** |

## 2026-10-06 追加 その 6(R-104 LLM のエージェントと人の違い・乗換案内の見積りと実際=リサーチの指示 10-06 夜 §2 B7・C1・読み取り目的・gitignore 下の data/research_cache/r104 に取得)

| ファイル | 出典 URL | 取得日 | 利用規約 | 用途・注意 |
|---|---|---|---|---|
| data/research_cache/r104/mlit_001488012.pdf(交通分野におけるデータ連携の高度化に向けた検討会 参考資料 3 利用者アンケート 2022-03・1,457 人・md5 fc6e9d56ecdb4e2232e5e3ae897126b0) | https://www.mlit.go.jp/sogoseisaku/transport/content/001488012.pdf(転送なし) | 2026-10-06(リサーチ役・親が md5 と p.40/p.43 の図を確認) | 国土交通省ウェブサイト利用規約(政府標準利用規約準拠・出典の表示) | 乗換案内サイト・アプリの使用頻度(全体・年代別)。R-104 §C1 |
| data/research_cache/r104/mlit_001257132.pdf(鉄道における車椅子利用環境改善に向けた調査 報告書 2018-03・md5 d66fd491c1d321516004dc39c76a2b45) | https://www.mlit.go.jp/common/001257132.pdf(転送なし) | 2026-10-06(同・親が md5 を確認) | 同上 | 車椅子使用者の乗車までの時間など。R-104 §C1 |

## 2026-10-12 追加 その 7(R-107 経済の材料=リサーチの指示 10-12 改訂版 §2 F10・読み取り目的・gitignore 下の data/research_cache/r107 に取得・md5 は同じ場所の MANIFEST.md)

| ファイル | 出典 URL | 取得日 | 利用規約 | 用途・注意 |
|---|---|---|---|---|
| data/research_cache/r107/zenkokukakei2024_gaiyou0828.pdf(令和 6 年全国家計構造調査 結果の概要 2026-08-28・64 頁) | https://www.stat.go.jp/data/zenkokukakei/2024/pdf/gaiyou0828.pdf(転送なし) | 2026-10-12(リサーチ役・親が pymupdf で実読) | 政府標準利用規約(第 2.0 版) | 最初の資産の分布(EC2・構築側の候補)。親が 1527.2 万円・600 万円・1723.2 万円・34.3% を確認 |
| data/research_cache/r107/kakei_sav_2025_gai.pdf(家計調査報告 貯蓄・負債編 2025 年平均 結果の概要・二人以上の世帯・34 頁) | https://www.stat.go.jp/data/sav/sokuhou/nen/pdf/2025_gai.pdf(転送なし) | 2026-10-12(同) | 同上 | **構築と検証のどちらに置くかは判断待ち**(PENDING §1-1・パターン台帳 §10-1 の「家計調査」との整合) |
| data/research_cache/r107/zk2024_t4-22-1_savings_class.csv・zk2024_t4-4_age_sex_hhtype.csv・zk2024_t23-0_tokyo_age.csv・zk2024_t31-0_tokyo_savings_class.csv(令和 6 年全国家計構造調査 第 4-22-1・4-4・23-0・31-0 表) | https://api.e-stat.go.jp/rest/3.0/app/getSimpleStatsData(statsDataId 0004056062・0004056078・0004056039・0004056045。appId は環境変数) | 2026-10-12(同) | 同上(e-Stat API 利用規約) | 資産と負債の階級と年齢の表(構築側の候補)。appId は URL に書かない |
| data/research_cache/r107/chinkou_r7_ippan_shokushu_t6_occ_sex_age.xlsx・t9_occ_sex_emptype.xlsx・t18_occ_sex_wagedist.xlsx・chinkou_r7_tanjikan_shokushu_t2_hourly.xlsx(令和 7 年賃金構造基本統計調査 職種 第 6・9・18 表・短時間労働者 第 2 表) | https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040421121・000040421124・000040421134・000040421217&fileKind=4 | 2026-10-12(同) | 同上 | 収入の錨(属性から作る関数の入力・構築側) |
| data/research_cache/r107/kakeishohi2025_emoney_t2-2_age.xlsx(家計消費状況調査 ICT 関連 2025 年 第 2-2 表 電子マネーの利用状況・年齢別) | https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040408067&fileKind=4 | 2026-10-12(同) | 同上 | 電子マネーの**保有率**は構築側(持ち物)・**利用額**は検証側(案) |
| data/research_cache/r107/ics2025_rekinen_gaiyou.pdf・ics2025_rekinen_shukei.xls・ics_chosahyo_ja.pdf(観光庁 インバウンド消費動向調査 2025 年暦年 調査概要・集計表・調査票) | https://www.mlit.go.jp/kankocho/content/002020046.pdf・002025515.xls・002018886.pdf(転送なし) | 2026-10-12(同。xls は未読=xlrd が無い) | 同上 | 訪日客の 1 回の旅行の予算(外の決定として持ち込む額) |
| data/research_cache/r107/osm_overpass_shibuya_atm_20261012.json・osm_overpass_shibuya_payment_20261012.json(渋谷区の ATM・銀行・コンビニ・郵便局 365 要素/宿泊施設と payment タグ 190 要素。クエリは同名の .query.txt・osm_base 2026-10-11) | https://overpass-api.de/api/interpreter(Overpass API=許可の一覧の中・2026-10-03) | 2026-10-12(同) | ODbL 1.0(出典表示「© OpenStreetMap contributors」・派生データベースは同じ条件で) | ATM の場所の充実度の数え(31 件・営業時間 10%)。実データの ATM には別の取り方が要る(判断待ち) |

- 保存しなかったもの(許可の一覧の外・標準出力で読んだだけ): j-flec.go.jp の家計の金融行動に関する世論調査 2025(xlsx 2 本・pdf 2 本)・fsa.go.jp の貸金業関係資料集。**j-flec.go.jp を許可の一覧に足すかは判断待ち**(PENDING §1-1)。

## 2026-10-12 追加 その 8(R-110 ペルソナと言語の材料=リサーチの指示 10-12 改訂版 §2 F9・読み取り目的・gitignore 下の data/research_cache/r110 に取得・md5 は同じ場所の MANIFEST.md)

| ファイル | 出典 URL | 取得日 | 利用規約 | 用途・注意 |
|---|---|---|---|---|
| data/research_cache/r110/zairyu_2025-12_t2_municipality.xlsx・zairyu_2025-12_ex2_notes.pdf・zairyu_2025-12_ex3_tabledata_howto.pdf(在留外国人統計 2025 年 12 月末 表 25-12-t2 と利用上の注意・利用方法) | https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040472266・000040472268・000040472269 | 2026-10-12(リサーチ役・親がドメインを確認) | e-Stat 利用規約(政府標準利用規約 第 2.0 版に準拠) | 渋谷区 × 国籍 × 年齢 × 性(年齢と性は Power Pivot の中=Excel で開く作業はユーザー U2) |
| data/research_cache/r110/census2020_sa_h02_13_foreign.csv(令和 2 年国勢調査 小地域集計 第 2 表 東京都・外国人人口) | https://www.e-stat.go.jp/stat-search/file-download?statInfId=000032163274&fileKind=1 | 2026-10-12(同) | 同上 | 町丁目別の外国人の割合(段 3 の言語と国籍の入力の候補) |
| data/research_cache/r110/tokyo_gaikoku_2026_ga26ev0300.csv・tokyo_gaikoku_2026_ga26gv0100.csv・tokyo_gaikoku_2020_ga20hv0100.csv(東京都 外国人人口 住民基本台帳 2026-01・2026-07・2020) | https://www.toukei.metro.tokyo.lg.jp/gaikoku/2026/ga26ev0300.csv ほか | 2026-10-12(同) | **東京都の統計 サイトポリシー(CC 表示なし=著作権法の範囲の私的使用・引用。要確認)** | 渋谷区 × 国籍の最新値(13,280 人)。再配布しない・集計値だけ使う |
| data/research_cache/r110/mlit_inbound_002025122.pdf・mlit_inbound_002018884.pdf・mlit_ukeire_001998584.pdf・mlit_ukeire_001998583.pdf(観光庁 インバウンド消費動向調査の調査票と概要・受入環境整備アンケート 令和 7 年度) | https://www.mlit.go.jp/kankocho/content/002025122.pdf ほか | 2026-10-12(同) | 国土交通省のサイトの利用規約(政府標準利用規約 第 2.0 版に準拠) | 訪日客の言語の設問の有無(無い)・困ったことの調査 |
| data/research_cache/r110/tokyo_inbound_behavior_2025_bessi2.pdf(東京都 令和 7 年 国・地域別外国人旅行者行動特性調査 別紙 2) | https://www.metro.tokyo.lg.jp/documents/d/tosei/20260630_17_02 | 2026-10-12(同) | 東京都公式ホームページのサイトポリシー | 国別の特徴の概要(訪問率の数値は本文に無い。報告書本体の取得はユーザー U6) |

## 2026-10-12 追加 その 9(R-109 母集団の人数の材料=リサーチの指示 10-12 改訂版 §2 A9・読み取り目的・gitignore 下の data/research_cache/r109 に取得・md5 は同じ場所の MANIFEST.md)

| ファイル | 出典 URL | 取得日 | 利用規約 | 用途・注意 |
|---|---|---|---|---|
| data/research_cache/r109/shibuya_ankaku_plan202606_honsatsu.pdf(渋谷駅周辺地域 都市再生安全確保計画 Ver3.0 本冊・2026-06) | https://www.toshiseibi.metro.tokyo.lg.jp/documents/d/toshiseibi/toshisaisei-shibuya-ankaku-plan202606-2-pdf | 2026-10-12(リサーチ役・親がドメインを確認) | 東京都公式ホームページのサイトポリシー | 139 ha の 14 時台の滞留人口 146,309(PT 2018 から)=構築側の目安 |
| data/research_cache/r109/census2020_t04_13_workplace_by_residence.xlsx(令和 2 年国勢調査 従業地・通学地集計 第 4 表 東京都) | https://www.e-stat.go.jp/stat-search/file-download?statInfId=000032214352&fileKind=0 | 2026-10-12(同) | e-Stat 利用規約(政府標準利用規約 第 2.0 版に準拠) | 来る可能性のある人の母集団(流入元の分布) |
| data/research_cache/r109/ecensus2021_yougo.pdf(令和 3 年経済センサス 活動調査 用語の解説) | https://www.stat.go.jp/data/e-census/2021/kekka/pdf/yougo.pdf | 2026-10-12(同) | 総務省統計局 利用規約(政府標準利用規約 第 2.0 版) | 「従業者」の定義(所属で数える・派遣と出向を含む) |
| data/research_cache/r109/mlit_telework_r6_001878995.pdf・mlit_telework_r6_001878996.pdf(国交省 令和 6 年度 テレワーク人口実態調査) | https://www.mlit.go.jp/report/press/content/001878995.pdf・001878996.pdf | 2026-10-12(同) | 国土交通省 利用規約(政府標準利用規約 第 2.0 版に準拠) | 通勤の出てこない割合の目安 |

- 取得ツールがリポの外(セッションの一時領域)に自動で残した写し: train-media.net の東急の PDF(規約未確認=値は使わない)・Schläpfer ほか 2021 の PDF。リポの data/ には置いていない。

## 2026-10-12 追加 その 10(ユーザーが手で入手した公式の時刻表と駅構内図=[回答 10-12b](design/v2-answers-2026-10-12b.md) §2-1・§7 の 3・gitignore 下の data/user_timetables/・git に入れない・公開しない)

| ファイル | 出典 | 取得日 | 利用規約 | 用途・注意 |
|---|---|---|---|---|
| data/user_timetables/ 以下(JR 東日本・東急・京王・東京メトロの渋谷と周辺の駅の時刻表 PDF・駅構内図・のりば図ほか。一覧は [timetables/README.md](bench/analysis/wallbounce-1012/timetables/README.md)) | 各社の公式サイト(**ユーザーが 2026-10-12 にブラウザで手で入手**。Claude Code は取得していない) | 2026-10-12(ユーザー) | 各社の利用規約(JR 東日本・東京メトロ=自動アクセス不可・東急=私的使用の外は許諾・京王=複製と電磁的加工を断る=R-90・R-91)。**研究開発の段階でユーザーの判断で使用(商用でない)・商用の前に各社の許諾が要る**。**〔第331・[回答 10-13](design/v2-answers-2026-10-13.md) の 2〕JR の 18 本(+原宿 4 本)の頁の注記「交通新聞社の JR 時刻表 2026 年 10 月号に基づく・電磁媒体への加工を禁じる」(親が原文で確認)について、ユーザーの判断: 研究開発の段階なので使い、商用の前に JR 東日本と交通新聞社の両方に許諾を取る。京王の時刻表は NAVITIME の配信(自動化された抽出・解析を禁じる規約)なので使わず、井の頭線は ODPT チャレンジ枠で入れる(その 11)。**根拠の整理(法律の助言ではない): 発車時刻は事実で著作物でない・取り出すのは事実だけで図の表現は使わない(著作権法 30 条の 4 の情報解析に近い) | 時刻表=発車時刻・種別・行き先・平日/土休・方面・版(2 回独立に読んで突き合わせ)。構内図=改札・通路・階・エスカレーターの向き・号車の位置の事実だけ(SR17)。図そのものは使わず公開しない。取り出した表も data/ の下。NAVITIME の画面の保存(`3544.pdf` など)は使わない=`_excluded_navitime/` へ |

## 2026-10-12 追加 その 11(ODPT の公開枠とチャレンジ枠=[回答 10-12b](design/v2-answers-2026-10-12b.md) §2-2 の 4・§2-3・発注 D [odpt-check.md](bench/analysis/wallbounce-1012/timetables/odpt-check.md)・gitignore 下の data/odpt/・md5 とキーを伏せた URL は data/odpt/MANIFEST_20261012.md)

| ファイル | 出典 URL | 取得日 | 利用規約 | 用途・注意 |
|---|---|---|---|---|
| data/odpt/station_timetable_metro_chiyoda_{omotesando,meijijingumae,yoyogikoen}.json・station_timetable_metro_ginza_omotesando.json・train_timetable_metro_ginza.json・stations_metro_chiyoda_edge.json・busstop_pole_near_shibuya.json・busroute_pattern_{toei,tokyubus}.json(公開枠 9 本。代々木公園は親が取得) | https://api.odpt.org/api/v4/(キーは環境変数) | 2026-10-12(調査役と親) | 公共交通オープンデータ基本ライセンス(営利・非営利を問わず可・出典表示・第三者が再利用できる形での公開と再配布は禁止=第 8 条 4 項(1)) | 千代田線 3 駅(範囲の端)・銀座線の渋谷の到着(列車時刻表)・範囲のバス停とバス系統(都営・東急バス)。世界の時点 2026-07-13 との版の食い違いは timetables/README.md §6 に宣言 |
| data/odpt/challenge/(16 本: JR 山手線・埼京線・湘南新宿ライン、東急 東横線・田園都市線、京王 井の頭線の駅の時刻表 10 本と列車時刻表 5 本ほか) | https://api-challenge.odpt.org/api/v4/(キーは環境変数) | 2026-10-12(調査役) | **公共交通オープンデータチャレンジ限定ライセンス(2026-07-01 制定・2026-08-28 改定)**: 第 4 条 1 項 利用の目的はチャレンジへの応募に限る・第 8 条 4 項 再配布と公開の禁止・第 13 条 許諾の期間と終了時の削除(期限の日付は台帳に書かない=ユーザー指示 10-13)・JR 東日本の特定利用条件(2026-08-06・競合サービス不可・特許の通知) | **〔第331・[回答 10-13](design/v2-answers-2026-10-13.md) の 3〕ユーザーは公共交通オープンデータチャレンジに応募する。応募する作品はこのシミュレーション(shibuya-simulation-v2)かその一部。利用の目的は応募と、公式の時刻表との照合。本体の構築は公式の時刻表(ユーザーが入手)が正で、京王 井の頭線だけはチャレンジ枠の時刻表を本体に使う。** 保存した 16 本と日次取得 `realworld_live/odpt_rt` の東急・京王・JR の分は消さず続ける。再配布しない・git に入れない。**〔第332・ユーザーの記録(2026-10-13)〕 ODPT から 2026-07-04 にメール、2026-07-07 に開発者登録の完了のメールが届き、キーの使用(07-08〜)はその後。応募の作品の中身はユーザーが claude.ai で壁打ちしてから決める。**応募の締め切りと条件の調べは [odpt-challenge-2026-conditions.md](bench/analysis/wallbounce-1012/timetables/odpt-challenge-2026-conditions.md) |

| data/odpt/station_timetable_metro_fukutoshin_meijijingumae.json(公開枠・副都心線 明治神宮前 F15 の駅の時刻表 4 表)〔第331〕 | https://api.odpt.org/api/v4/(キーは環境変数・md5 は data/odpt/MANIFEST_20261013.md) | 2026-10-13(実行役 D) | 公共交通オープンデータ基本ライセンス(同上) | ユーザーが手で入手した F15 の時刻表 PDF の読み取りの照合(全件一致) |
| data/odpt/challenge/station_timetable_odakyu_odawara_yoyogihachiman.json(チャレンジ枠・小田急 代々木八幡の駅の時刻表 4 表)〔第331〕 | https://api-challenge.odpt.org/api/v4/(キーは環境変数・md5 は同 MANIFEST) | 2026-10-13(実行役 D) | チャレンジ限定ライセンス(上の行と同じ条件・小田急の特定利用条件は未読=空欄) | ユーザーが手で入手した代々木八幡の時刻表 PDF の読み取りの照合(全件一致)。用途は応募と照合 |

## 2026-10-12 追加 その 12(R-112 建物の内部と物の材料=リサーチの指示 10-06 §2 E5・読み取り目的・gitignore 下の data/research_cache/r112 に取得・md5 は同じ場所の MANIFEST.md)

| ファイル | 出典 URL | 取得日 | 利用規約 | 用途・注意 |
|---|---|---|---|---|
| data/research_cache/r112/mlit_001381403_kousoku_r2_shiryo4.pdf・mlit_001474873_indoor_map_guide_2022.pdf・mlit_001994867_bim_kakunin.pdf(国交省 高精度測位社会プロジェクト 令和 2 年度 第 1 回検討会 資料 4・屋内地図/屋内測位環境構築の手引き 2022-03・建築 BIM の取組状況) | https://www.mlit.go.jp/common/001381403.pdf ほか(MANIFEST) | 2026-10-12(リサーチ役・親がドメインを確認) | 国土交通省のサイトの利用規約(政府標準利用規約 第 2.0 版に準拠) | 渋谷駅の屋内電子地図の範囲と公開の状態・屋内地図の作り方・建築確認の BIM の時期 |
| data/research_cache/r112/tokyo_toshiseibi_digital08_3.pdf・digital07_4.pdf・digital_r03_shiryou04.pdf(東京都 都市整備局 3D デジタルマップの WG 資料) | https://www.toshiseibi.metro.tokyo.lg.jp/...(MANIFEST・同ドメインの中の転送だけ) | 2026-10-12(同) | 東京都公式ホームページのサイトポリシー | 都の 3D デジタルマップの整備状況と仕様 |
| data/research_cache/r112/osm_objects_w1_20261012.json(W1 の bbox の街路の設備・屋内タグ 2,115 要素・osm_base 2026-10-12T07:57:35Z・クエリは同名の .query.txt) | https://overpass-api.de/api/interpreter(Overpass API=許可の一覧の中) | 2026-10-12(同) | ODbL 1.0(出典表示「© OpenStreetMap contributors」・派生データベースは同じ条件で) | 物の形の公開データの数え(ベンチ・ごみ箱・自販機・駐輪場・看板・店名 2,813) |

- 読んだだけ(保存せず・一覧の外): 商業施設 23 ドメインの robots.txt と利用条件の頁(R-112 §空欄 A の表)・soumu.go.jp のカメラ画像利活用ガイドブック・Mapillary の規約・PLATEAU 標準製品仕様書の頁(mlit.go.jp)。zip・点群・施設サイトの中身は取っていない。

## 2026-10-12 追加 その 13(10e 構築側 B5=W13 の年間化・気象庁 etrn の東京 47662 の 10 分値と時別値・読み取り目的・gitignore 下の data/realworld/jma_etrn/)

| ファイル | 出典 URL | 取得日 | 利用規約 | 用途・注意 |
|---|---|---|---|---|
| data/realworld/jma_etrn/raw10min/(10 分値の頁 365 本・2025-09-01〜2026-08-31)・raw/(時別値の頁 330 本・手元に無かった日)・tokyo47662_10min_2025-09-01_2026-08-31.csv・tokyo47662_hourly_2025-09-01_2026-08-31.csv(表にしたもの)。md5・バイト数・取得時刻・URL は MANIFEST_10min.tsv・MANIFEST_hourly.tsv | https://www.data.jma.go.jp/stats/etrn/view/10min_s1.php?prec_no=44&block_no=47662&year=…&month=…&day=…&view=p1 / hourly_s1.php(同) | 2026-10-12 07:52〜08:15 UTC(実装役・2 秒に 1 回・転送と失敗 0・robots.txt は 404) | 気象庁 公共データ利用規約(第 1.0 版)=出典の記載・加工した場合はその旨の記載(自動取得についての定めは無い。親が `www.jma.go.jp` の規約の頁を読んだだけで保存せず) | W13 の年間化(窓 2025-09-01〜2026-08-31・主は 10 分値・時別値は欠けの補完)。35 日はアメダスの JSON と検算(気温・湿度・風速・降水 3,219/3,219 一致・日照は夜の空欄を 0 分として扱う=expedient)。`realworld_live/` は読まない |

## 2026-10-13 追加 その 14(ユーザーが手で入手した追加の時刻表・構内図と商業施設の平面図=[回答 10-13](design/v2-answers-2026-10-13.md) の 4・5・gitignore 下・git に入れない・公開しない)

| ファイル | 出典 | 取得日 | 利用規約 | 用途・注意 |
|---|---|---|---|---|
| data/user_timetables/ の追加分(京王 神泉の構内図・京王 下北沢の構内図と階層図=範囲の外・参考として保管・小田急 代々木八幡の時刻表と構内図〔第332・ユーザー確認: 小田急の公式サイトから保存〕・東京メトロ 代々木公園 C02 の時刻表・構内立体図・号車の図〔第332 追加〕・JR 原宿の山手線の時刻表 4 本と構内図・東京メトロ 明治神宮前の千代田線 C03 と副都心線 F15 の時刻表・構内立体図・号車の図。振り分けと一覧は [additions-2026-10-13.md](bench/analysis/wallbounce-1012/timetables/additions-2026-10-13.md)) | 各社の公式サイト(**ユーザーが 2026-10-13 にブラウザで手で入手**。Claude Code は取得していない) | 2026-10-13(ユーザー) | その 10 と同じ(研究開発の段階・事実だけ・商用の前に各社の許諾。小田急を加える)。京王の NAVITIME 配信の時刻表(神泉 `4450.pdf`・下北沢 `997.pdf`)は使わず `_excluded_navitime/` へ | 時刻表は 2 回独立に読んで突き合わせ・構内図は事実だけ(SR17・空間の段 0)。`ty01-shibuya_1.pdf` はリンク切れ(ユーザー確認 2026-10-13)=取りに行かない・AVIF の画像版で代える |
| data/user_floor_maps/{parco,omotesando_hills,markcity}/(渋谷パルコ各階・表参道ヒルズ(本館・西館・同潤館)・渋谷マークシティの平面図の画像) | 各施設の公式サイト(**ユーザーが 2026-10-13 に手で保存**。自動取得はしない=R-112 §空欄 A で除いた 4 件のうち 3 件) | 2026-10-13(ユーザー) | パルコ=私的利用以外の利用に承諾・表参道ヒルズ=書面の事前承諾・マークシティ=利用条件の頁が無い(地図の配信元 platinumaps.jp は AI のクローラと学習を robots で拒否=自動取得しない)。**研究開発の段階でユーザーの判断で使用・商用の前に各施設の許諾** | 空間の段 0 で事実(階・区画・入口・通路)だけを取り出す。図は使わず公開しない。時刻表と同じ扱い |
| (入手できず)西武渋谷店(A 館・B 館を含む) | — | — | 西武(sogo-seibu.jp)の利用条件(最終更新 2025-10-01)は私的使用を超える利用に文書の許諾が要り、禁止事項に「営業活動もしくは営利を目的とする行為、またはその準備を目的とする行為」がある(R-112 §空欄 A #15) | 図が無いので MR14 のとおり「床の広さと入口だけの 1 部屋」として扱う(既知の弱点=つなぎの台帳)。世界の時点 2026-07-13 では営業中なので建物と店は存在させる |
| 商業施設の平面図のドメイン 19 件(R-112 §空欄 A の表の 23 件から platinumaps.jp・西武・表参道ヒルズ・パルコを除いたもの。cocoti は除外のまま・web.archive.org は規約を読んでから) | 各施設の公式サイト | (未取得・読み取り目的で取得可=ユーザー承認 2026-10-13) | 各施設の利用条件(R-112 §空欄 A の表)。利用条件の頁が無い 7 件は取得の前にもう 1 度探す | 取得したら本台帳に 1 行ずつ足す。商用の前に許諾 |

## 2026-10-14 追加 その 15(第 2 期 2-3b=W12 の等間隔の推定を実ダイヤに置き換え・[記録 tt23b](bench/analysis/wallbounce-1012/tt23b/README.md)・資産は gitignore 下の data/world/v2_stage_2-3b/(活性化は 2-4)・生の行は git に入れず再配布しない)

| ファイル | 出典 | 取得日 | 利用規約 | 用途・注意 |
|---|---|---|---|---|
| data/world/v2_stage_2-3b/w12_timetables.parquet の京王 井の頭線の行(渋谷発 566 本・平日/土休) | ODPT チャレンジ枠(data/user_timetables/_extracted/odpt_challenge/=その 11 の取得物から読み取った CSV) | 2026-10-14(組み立て) | チャレンジ限定ライセンス(応募と照合の範囲・第 4 条 1 項=[回答 10-13](design/v2-answers-2026-10-13.md) の 3) | 世界資産の中だけで使う(作品=本シミュレーション)。生の行(時刻の一覧)は記録に写さず再配布しない。商用の前に扱いを決める |
| 同 parquet の JR(山手線・埼京線+湘南新宿ライン・相鉄直通)の行(1,883 本)と東急(東横線・田園都市線)の行(2,164 本) | ユーザーが手で入手した公式の時刻表 PDF の読み取り(その 10・その 14=data/user_timetables/_extracted/*_final.csv) | 2026-10-14(組み立て) | JR=交通新聞社の JR 時刻表に基づく注記あり(研究開発の段階で使用・商用の前に JR 東日本と交通新聞社の許諾=[回答 10-13](design/v2-answers-2026-10-13.md) の 2)・東急=私的使用の外は許諾が要る(研究開発の段階でユーザーの判断で使用・商用の前に許諾) | 図・PDF・CSV は公開しない。資産に入るのは発車時刻・種別・暦の事実だけ。版の宣言は w12_timetable_versions.json(JR は 2026-03-14 改正と同じ版と推測) |
| 同 parquet の銀座線の行(665 本) | ODPT オープン枠の静的データ版 1(data/realworld_live/odpt_static/2026-10-13/traintimetable_TokyoMetro.json.gz・dct:issued 2026-09-19) | 2026-10-13(取得)・2026-10-14(組み立て) | ODPT オープンデータ(出典の表示が要る)=その 11 の行のとおり | **世界の時点 2026-07-13 より後の版**と宣言([回答 10-13b](design/v2-answers-2026-10-13b.md) §2)。半蔵門線・副都心線は 7 月の取得のまま |

## 2026-10-15 追加 その 16(第 2 期 2-3c=W12 1.3.0 の到着の行と直通のまとめ・[記録 tt23c](bench/analysis/wallbounce-1012/tt23c/README.md)・資産は gitignore 下の data/world/v2_stage_2-3c/(活性化は版上げ 3 回目=4-3)・生の行は git に入れず再配布しない)

| ファイル | 出典 | 取得日 | 利用規約 | 用途・注意 |
|---|---|---|---|---|
| data/world/v2_stage_2-3c/w12_rail_events.parquet の到着の行=銀座線(平日 362・土休 307)・半蔵門線(282・209)・副都心線(259・237)と、メトロの発車の行に足した属性 | ODPT オープン枠の静的データ版 1(data/realworld_live/odpt_static/ の列車時刻表=銀座線は 9 月改正の版・半蔵門線と副都心線は 2026-03-14 の版=その 11・その 15 の取得物) | 2026-10-15(組み立て) | ODPT オープンデータ(出典の表示が要る)=その 11 の行のとおり | 世界資産の中だけで使う。**世界の時点 2026-07-13 より後の版**の宣言はその 15 と同じ。手前の駅(G02・Z02・F15)との照合に同じ取得物を使った |
| 同 parquet の井の頭線の渋谷着の行(平日 305・土休 261=566 本・列車番号つき) | ODPT チャレンジ枠(data/user_timetables/_extracted/odpt_challenge/ の `京王_井の頭線_渋谷_到着`=その 11 の取得物から読み取った CSV) | 2026-10-15(組み立て) | チャレンジ限定ライセンス(応募と照合の範囲・第 4 条 1 項=[回答 10-13](design/v2-answers-2026-10-13.md) の 3) | 世界資産の中だけで使う(作品=本シミュレーション)。生の行(時刻の一覧)は記録に写さず再配布しない。`USE_ODPT_CHALLENGE` で外せる(仮-15) |
| (資産に入れていない)チャレンジ枠の東急の駅の時刻表の `isOrigin` と JR の列車時刻表 | ODPT チャレンジ枠(その 11) | 2026-10-15(照合) | 同上 | **照合だけ**(東急の当駅始発の印 185 と分まで一致・JR は渋谷で終わる/始まる列車 0 の確認)。記録には件数だけ |
| data/user_timetables/_extracted/東急_印.{read1,read2,final}.csv と read2_raw/(TY01_2・DT01_2 の当駅始発の印 ●153・⑤28・②4=185 個の読み取り) | ユーザーが手で入手した東急の公式の時刻表 PDF(その 14)の読み取り(読み 1/2・食い違い 1 件は 300 dpi で決着・時ごとのマス 47) | 2026-10-15(読み取り) | 東急=私的使用の外は許諾が要る(研究開発の段階で使用・商用の前に東急の許諾=[回答 10-12b](design/v2-answers-2026-10-12b.md) §2-1) | 事実(当駅始発かどうか)だけ・図は使わず公開しない・ファイルも表も git に入れない。成田エクスプレスの表(その 14)は湘南新宿ラインの表への包含の確かめだけに使った |

## 2026-10-15 追加 その 17(第 4 期 4-1 段 1〜3=W21 人口の作り直しの材料・[記録 pop41](bench/analysis/wallbounce-1012/pop41/README.md)・gitignore 下の data/research_cache/pop41/・md5 は同じ場所の MANIFEST.md・資産 data/world/v2_stage_4-1/ は活性化しない=段 10)

| ファイル | 出典 | 取得日 | 利用規約 | 用途・注意 |
|---|---|---|---|---|
| data/research_cache/pop41/ の xlsx 18 本(令和 7 年国勢調査 人口等基本集計 第 12-1・15-1・19-1 表【原数値】・第 10・13-1(総数・男・女)表【不詳補完値】/ 令和 2 年国勢調査 第 2-1・10・13-1(総数・男・女)表【不詳補完値・遡及】/ 就業状態等基本集計 第 3-1・5-1・10-1 表/ 従業地・通学地集計 第 8・15-1・16-1 表) | e-Stat(www.e-stat.go.jp の file-download・statInfId と md5 は MANIFEST・`curl -sI --max-redirs 0` で 200 と転送なしを確かめた) | 2026-10-15 | 政府標準利用規約(第 2.0 版)=出典の明記で利用可。不詳補完値は参考表(加工の明記が要る) | W21 の段 2(区の雛形=世帯の型 × 人員・世帯主・続き柄・夫婦と親子の年齢差)と段 3(仕事の結合・通勤者の属性)。渋谷区の行だけを `derived/` に写して読む。取ったが使っていない 4 表(2025 第 15-1・従業地 第 15-1・2020 第 13-1 総数・小地域 第 6-3)は記録に宣言 |
| data/research_cache/pop41/ の CSV 3 本(令和 2 年国勢調査 小地域集計 東京都 第 6-2・6-3・16-3 表) | 同 | 同 | 同 | W21 の段 2(家族類型別の一般世帯人員)・段 3(通学地) |
| data/research_cache/pop41/derived/*.json 23 本 | 上の xlsx と r116 の xlsx 5 本からの写し(渋谷区の行だけ・2 回写して md5 一致) | 同 | 同(派生=値は書き換えない・元の md5 を照らす) | W21 の読み口 |
