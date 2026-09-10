# データ・ライセンス台帳(2026-09-01初期化)

> 法務答申([v2-legal-licensing-deep-research.md](research/v2-legal-licensing-deep-research.md))の実装。**データ資産を追加するたびに1行追記**する。
> 設計原則: ①data type単位の層分離(OSM/PLATEAU/ODPT/人流を物理分離・重複統合しない=Collective Database維持)②出力スキーマからOSM生値を排除(内部ID+集計のみ)。

| ディレクトリ | 内容 | 出典 | ライセンス | 商用 | 備考 |
|---|---|---|---|---|---|
| data/realworld | OSM抽出(地図・POI)・ODPT実ダイヤ・経済センサス・気象庁実測・国勢調査系 | OSM/ODPT/e-Stat/気象庁 | **混在**(下記行参照)・v1の取得台帳 _ledger.jsonl 同梱 | △ | 層分離の再編はPhase 2で実施 |
| data/realworld(OSM由来分) | 渋谷の地図・POI 2,337 | OpenStreetMap | **ODbL 1.0** | △ | 公開・配布時にshare-alike発火。出力にOSM生値を載せない設計で回避 |
| data/realworld(気象分) | アメダス実測(v2手元は35日=2026-07-28〜08-31。930日はv1時点) | 気象庁 | PDL 1.0相当 | ○ | 外部提供時「予報」でなく過去実績/仮想シナリオと明示(気象業務法17条) |
| data/realworld(統計分) | 経済センサス9,872社・国勢調査 | e-Stat | 政府標準利用規約2.0 | ○ | 出典表示 |
| data/plateau | 渋谷3D建物3,531棟(東京都23区・2020年度版) | 国交省PLATEAU(**著作権は各地方公共団体に帰属**=サイトポリシー§3・親実読09-07) | PDL 1.0(CC BY 4.0/ODC BY/ODbL互換宣言) | ○ | 出典表示「出典: 国土交通省 PLATEAUウェブサイト(URL)」/加工時「『3D都市モデル(Project PLATEAU)東京都23区』(国土交通省)(URL)を加工して作成」。渋谷区単独2023年度版(plateau-13113-shibuya-ku-2023)への差し替え候補 |
| data/odpt | 駅・路線マスタ | ODPT | 基本ライセンス | △ | 商用化時はCC BY/CC0/PDLの107件へ絞る(答申) |
| data/persona_pool_v2 | 100万ペルソナ(国勢調査IPF較正+LLM生成来歴) | 自家生成(上流=e-Stat統計) | 自家 | ○ | 統計からの合成=個人情報非該当と整理可(PPC Q1-17/Q1-8類推)。生成LLMのライセンス貫通に注意 |
| data/calib | v1較正パラメータ(sigma_c/theta_scale) | 自家生成 | 自家 | ○ | |
| data/ground_truth | **現実整合アンカー台帳 registry.yaml(37本・出典/holdout分割付き)** | 各アンカーの出典はregistry内に記載 | 引用 | ○ | 北極星KPIの物差し。v2で成長させる |
| data/jinryu | 渋谷人流(1kmメッシュ2019-2021・同時滞在カーブ) | data/jinryu/SOURCE.md 参照 | SOURCE.md 参照 | △ | 較正専用・生データ再配布しない |
| data/realworld/osm(2026-09-06複写・v1由来) | 渋谷OSM地図v8(ノード3,499・エッジ4,944[地上4,448/デッキ306/地下190]・POI 2,337[営業時間・価格なし]・建物7,210)+**架空組織台帳**(organizations_*.json=v1の手続き生成・seed 42・経済センサス町丁目別に較正・実在名なし=名寄せ不可)+建物高さ・横断歩道・フロアガイド | OpenStreetMap / 自家生成(上流=e-Stat) | ODbL 1.0 / 自家 | △ | 出力にOSM生値を載せない(内部ID+集計のみ)・osm_date凍結 |
| data/realworld/kddi_la(2026-09-06収載) | KDDI Location Analyzer 滞在人口・通過人口(5エリア×24h×属性・2024年)=Power BI公開ダッシュボード由来の生JSON(2万行)+渋谷区オープンデータ日次CSV(shibuya_jinryu/2026) | 渋谷区オープンデータ／KDDI・技研商事 | CC BY 4.0(区OD)・ダッシュボード由来分は同系列として出典表示 | △ | 較正には使わず事後検証専用(holdout)・出典表示必須 |
| data/realworld/estat(2026-09-07取得) | e-Stat API取得JSON: 国勢調査2020 昼間/夜間人口(渋谷区)・経済センサス2021 企業等ベース集計(渋谷区) | e-Stat(総務省統計局) | 政府標準利用規約2.0 | ○ | 出典表示(「e-Stat」+統計名+年次)・APIキーは環境変数のみ |
| data/realworld/estat/国勢調査2020_小地域_年齢5歳階級男女別人口_東京都_渋谷区_全階級.json(2026-09-09 親取得・tools/world_data/estat_fetch.py=ページング付き) | e-Stat API getStatsData statsDataId 8003006792(国勢調査2020 小地域集計・年齢(5歳階級)・男女別人口)・cdAreaFrom/To 131130000-131139999+区計 13113=100 地域×60 分類=6,000 値(総数/男/女×0-4〜70-74・75 歳以上・15 歳未満/15-64/65 以上の集約)。09-07 取得分(1,500 値・0010-0150 のみ=70 歳以上と男女別が欠落)と重なる 1,500 値は完全一致。区計: 総数 243,883・男 117,907・女 125,976・70-74 10,307・75+ 21,900 | e-Stat(総務省統計局) | 政府標準利用規約2.0・出典表示「政府統計の総合窓口(e-Stat)国勢調査2020 小地域集計」・APIキーは環境変数のみ | ○ | W16 年齢×性別 raking の目標(14 階級→16 階級+不詳の分離・サブ J 親判断待ち 3 の解消)。再配布しない(gitignore) |
| data/realworld/estat/A002005212020DDSWC13113-JGD2011.zip(+展開 r2ka13113/・2026-09-08 ユーザー取得・zip のため §7 例外のアーカイブ除外に該当=親は取得せず) | e-Stat 統計GIS 境界データ: 国勢調査2020 小地域(町丁・字等)渋谷区 13113・世界測地系緯度経度(JGD2011)・Shape形式(shp/shx/dbf/prj・57,768 B・sha256 88e8f889e1bb119c…)。80 ポリゴン(KEY_CODE 80 一意・HCODE 8101=町丁・字等)・属性 JINKO 合計 243,883(=夜間人口アンカー E1 と一致)・SETAI 149,967・AREA 合計 15.12 km²・bbox 139.661-139.724E/35.642-35.692N | e-Stat(総務省統計局)統計GIS | 政府標準利用規約2.0(e-Stat 利用規約)・出典表示「政府統計の総合窓口(e-Stat)境界データ(国勢調査2020 小地域・渋谷区)」 | ○ | W16 母集団合成(町丁目→セル写像=建物床面積按分・親検収=dbf を標準ライブラリで解析)。再配布しない(gitignore) |
| data/realworld/plateau_2025(2026-09-08 親複写・原本=ユーザーの Unreal プロジェクト PLATEAU_SDK_test/Content/PLATEAU/Datasets/13113_shibuya-ku_pref_2025_citygml_1_op に SDK が複写していた udx 一式・ユーザーが 2026-07-09 頃 G空間情報センターから取得) | 3D都市モデル(Project PLATEAU)渋谷区(2025年度)CityGML v1_op・製品仕様書 5.0(v1 メモ: 作成 2026-03-13)・3次メッシュ 53393585/86/95/96 の中心 4 タイルのみ(≈2.9 km²)。複写した udx: tran(4 gml・57 MB・sha256 8457ce05/18b8b0c1/a74cc75a/ad04f9b0…)・bldg(4・1.0 GB)・dem(1・385 MB)・ubld(1・33 MB)・frn(2・69 MB)・brid(4・60 MB)+codelists(metadata なし)。計 1.6 GB。**tran 実査(親・grep)**: tran:Road 3,248・TrafficArea 4,053・lod3MultiSurface 5,782・RoadStructureAttribute=sectionType のみ・**TrafficVolumeAttribute/sectionID/routeName/width/numberOfLanes=0**(交通量属性なし=W10 区間突合には使えない) | 国土交通省 PLATEAU(G空間情報センター plateau-13113-shibuya-ku-2025) | PLATEAU サイトポリシー §3=PDL1.0(CC BY 4.0/ODC BY/ODbL でも可)・出典「3D都市モデル(Project PLATEAU)渋谷区(2025年度)(国土交通省)を加工して作成」(台帳 F15 で親確認) | ○ | W4 建物高さの原本(v1 index と同源)・LOD3 歩道面(R7 群衆物理の将来入力)・地下街 ubld(UG 層)。**フル zip=2026-09-09 ユーザー取得**: 13113_shibuya-ku_pref_2025_citygml_1_op.zip(649,322,807 B・sha256 f7437469d85b1d4a…・展開 4.79 GB・19,877 entries: udx bldg 29 メッシュ 1,627 MB/tran 30/dem 2/fld 55/frn 5/luse 2/ubld 1/urf 2/veg 1/wtr 2/brid 8/lsld 2+codelists 293+schemas+metadata(udx_13113_pref_2025_op.xml・resource csv)+specification+README+索引図)。中心 4 タイルの tran は CRC 一致(同一版)。展開先 data/realworld/plateau_2025/13113_shibuya-ku_pref_2025_citygml_1_op/。再配布しない(gitignore) |
| data/realworld/osm/station_entrances_overpass.json(2026-09-07取得) | Overpass APIで取得した駅出入口ノード45件(subway_entrance 33・train_station_entrance 12・bbox 35.6505-35.6685/139.6905-139.7115・渋谷駅14・表参道5・明治神宮前2ほか) | OpenStreetMap | ODbL 1.0 | △ | 世界データ構築W11(駅→出口→セル)の入力。出力にOSM生値を載せない・attic日は取得日(2026-09-07)で凍結 |
| data/realworld/pt_tokyo/pt6_d-1_purpose_mode_od.csv(2026-09-07ユーザー取得・元名d-1.csv) | 第6回東京都市圏パーソントリップ調査(2018年度・平日1日)「表d-1 目的種類別代表交通手段別OD表」e-Stat配布CSV(cp932・346,372行・発地×着地=計画基本ゾーン4桁コード655種[集計行含む]×目的種類8+計×代表交通手段[鉄道/バス/自動車/2輪車/自転車/徒歩/その他/不明/計]・拡大トリップ数) | 国土交通省(e-Stat 政府統計コード00600550・tstat 000001151670・stat_infid 000032066127)/東京都市圏交通計画協議会 | 政府標準利用規約2.0(e-Stat配布分)。協議会HP配布分はPDL1.0準拠(tokyo-pt.jp/terms実読: 「東京都市圏交通計画協議会ホームページ(当該ページのURL)を加工して作成」・国が作成したかのような公表禁止)。出典表示: 「第6回東京都市圏パーソントリップ調査(東京都市圏交通計画協議会)を加工して作成」 | ○ | U10来街目的構成比・方面別OD重みの較正入力(mechanism昇格)。ゾーンコード→町名の対応はtokyo-pt.jp「H30_zonecode.xlsx」が必要(未取得)。生CSVは再配布しない(gitignore) |
| data/realworld/pt_tokyo/H30_zonecode.xlsx(2026-09-07ユーザー取得) | 第6回PTゾーンコード表(市区町村別一覧1,660行・都県別シート・大/中/計画基本/小ゾーン+該当町丁字名) | 東京都市圏交通計画協議会 tokyo-pt.jp/data/01_01 | PDL1.0準拠(協議会利用規約・出典表示) | ○ | 渋谷区=計画基本ゾーン0240-0243・小ゾーン10。派生集計 docs/bench/pt_shibuya/*.json(集計値のみ・出典表示つき)はリポ収載可 |
| data/realworld/osm/poi_opening_hours_overpass_20260907.json(2026-09-07取得) | Overpass APIで取得した飲食・物販POIのタグ(bbox 35.6505-35.6685/139.6905-139.7115・2,164件・opening_hours 565件=26.1%・price系14件) | OpenStreetMap | ODbL 1.0 | △ | W7営業時間の上書き入力(取得分のみmechanism)。出力にOSM生値を載せない・attic日=取得日で凍結 |
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
