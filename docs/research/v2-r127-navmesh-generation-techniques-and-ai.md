# R-127 答申: ナビメッシュ生成の技術と AI(段 0 の空間の材料を天神と全国へ広げる)

<!-- hdr:v1 | 等級: (親検収の前) | 作成: 2026-11-01 | 範囲: 回答 11-01 §13 R-K・prompt 11-01 研究の R-K -->
- **分野**: ゲーム・VR 技術の輸入(常設レーン) / 地理情報科学 / 歩行者動力学 | **重要度**: (親が付ける)
- **一次確認**: 未(§6 の出典表の等級は本書の自己申告)
- **既存答申との関係**(重ねずに番号で引く): ナビメッシュの実装候補・探索の費用・ライセンス(Recast/Detour・JuPedSim・CGAL・shapely)= [R-59](v2-r59-navmesh-implementations.md)。3 次元のデータの実在 = [R-58](v2-r58-3d-data-inventory.md)。屋内と物のデータ源 = [R-112](v2-r112-indoor-and-object-data-sources.md)。渋谷の段 0 の材料 = [R-119](v2-r119-spatial-stage0-sources.md) と [sp0 の記録](../bench/analysis/spatial-2026-10/sp0/README.md)。天神と全国の材料 = [R-120](v2-r120-tenjin-and-national-stage0-materials.md)。本書は「何から・どれだけ自動で歩ける面を作れるか」と「渋谷の手順を天神へ持っていくと何が空くか」だけを扱う。
- 規律: 子サブは起動していない。Web は読むだけ(WebSearch・WebFetch)。データ・重み・コードは取得していない(pip・clone なし)。WebFetch は PDF を読むとき本体をツールの作業用の場所(リポの外)に自動で残す。本書では国交省の PDF 2 本(001900528・002018907)と Project Sidewalk の論文 1 本がそうなり、pymupdf で文字の層だけを scratch に取り出して読んだ(リポと data/ には入れていない)。Overpass には 1 回も問い合わせていない。封印の層(data/jinryu ほか)と `*_validation_anchors_v0.json` は開いていない。
- 印: ◎ 原典の本文・ソース・PDF の文字層を自分で読み、引いた文を確かめた / ○ 原典の頁を読んだが、要約を通して読んだ部分がある / △ 検索の要約だけ。推測は「推測」と書く。本書の自前の組み立ては「未リサーチ(expedient)」と書く。読んだ日はすべて 2026-11-01。

## §0 要旨

1. 歩ける面を作る手法は、①ゲームエンジン型(Recast 系: 3D の形をボクセルにして歩ける面を自動で取り出す)、②地図型(道路縁や歩道の線から帯を作る)、③計測型(点群・写真から学習や形の解析で取り出す)、④屋内モデル型(IFC・IndoorGML・平面図)、⑤群衆シミュレーションの実務型(CAD を取り込み、階段と接続口は人が描く)の 5 つに分かれる。
2. 渋谷の navmesh1 は①の考え方(格子に塗る・Detour の off-mesh 接続)を②の入力に当てた作りで、点群と平面図はまだ入力にしていない。歩ける面 853,077 m² のうち約 3 割(283,325 m²)は、福岡市の PLATEAU に無い地物(道路 LOD2/3・横断歩道・地下街・橋梁)から来ている。
3. 全国で同じ形でそろう入力で最も強いのは基盤地図情報の道路縁である。国交省は令和 7 年 7 月の検討で、点群や航空写真の機械学習より「基盤地図情報から形状データを生成する手法が最も効果的」と結論し、生成率を「8 割前後」と書いた(◎)。ただし横断歩道・立体交差・広場は取れず、手で直す。
4. 国交省は 2026 年に AI で幅員・縦断勾配・段差を自動で取り出す現地実証を始めた(池田市・10 月下旬〜12 月・成果は 2027-01〜02)。入力の種類は報道発表に書いていない。
5. 航空写真の学習(Tile2Net)はズーム 19 を勧め、18 未満は不可とする。地理院の全国最新写真はズーム 18 までなので、日本で使えるかは未確認(推測で足りない側)。
6. 天神で空くのは主に地下(天神地下街・地下鉄のコンコース)と駅の構内である。PLATEAU にも公開の点群にも無く、自動で埋める公開の手法は見つからなかった。手で描くか OSM の屋内タグか「無いと宣言」のどれかになる。
7. 生成 AI で間取りを推定する手法(HouseDiffusion ほか)は住宅が中心で、推定した床は現実の通路と一致する保証がない。回答 11-01 の原則に照らすと、推定の床を錨の答え合わせに使う所へ置くのは危うい(推測)。
8. 現実との整合で最も大きいのは、天神の通行量調査の地下 80 地点である。地下の面が無いと、この 80 地点は測れなくなる。

---

## §1 いまの渋谷の作り(段 0 → 段 1)

- 段 0(取得)は R-119 と sp0 の記録のとおり。段 1 の構築 `src/shibuya/build/space/navmesh1.py`(1.1.0)の入力は `build/space/sources.py` の docstring に書かれた次の 7 つだけで、都の点群・3dcel・平面図・土地利用現況 GIS は**まだ読んでいない**(◎ リポ)。
  PLATEAU 渋谷区 2025 の道路 tran(LOD1 面・LOD2/3 の TrafficArea)・都市設備 frn(横断歩道 1110・地下出入口 4020)・地形 dem/地下街 LOD4.1 の床/橋梁 LOD2 の上面/OSM の歩行系(段 0 の #9)/歩行空間ネットワーク 2020(渋谷南部)/W1(OSM 由来の歩行グラフ)/W2(100 m のセル)。
- 作り方は「階ごとに 0.5 m の格子へ出どころの札つきで塗る(先に塗ったものが勝つ)→ 行ごとのラン → 門 → 帯 → A* と funnel」。上下の接続口は Detour の off-mesh 接続と同じ形(階段 225・スロープ 13・EV 6・ES 1)。考え方は Recast のボクセル化に近いが、3D の三角形を落とすのではなく 2D の地物を塗る(◎ sp1 §1-1)。
- 出どころ別の面積(sp1 §1-2 の表の写し・単位 m²): PLATEAU 610,411(歩道部 126,395・LOD1 の面=住宅街の型 327,087・歩道部の無い車道部 128,985・横断歩道 1,378・地下街の床 15,094・橋梁の上面 11,473)/既定の幅 208,961(幹線の縁 2 m 53,923・W1 の線 91,667・OSM の線 57,978 ほか)/OSM の幅つき 18,897・歩行空間 NW 3,353/つなぎの帯 8,730。歩ける面積の合計は 853,077(地上 797,320・デッキ 32,169・地下 23,588)。
- 本書の計算: 福岡市の PLATEAU(R-120 T1=道路 LOD1 だけ・地下街・都市設備・橋梁なし)に無い地物の分=126,395+128,985+1,378+15,094+11,473=283,325 m²(合計の 33.2%)。出どころの和は重なりの扱いで合計と少し違う(850,352)ので、割合は目安。

## §2 比較表(A)

列: 手法 / 入力 / 出力 / 屋内外・階層 / 自動化の度合い / ライセンス / 実績(都市規模) / 出典・等級。番号の [S..] は §6。

### 2-1 ゲームエンジン型

| 手法 | 入力 | 出力 | 屋内外・階層 | 自動化 | ライセンス | 実績 | 出典・等級 |
|---|---|---|---|---|---|---|---|
| Recast & Detour | 三角形の 3D の形(何でも) | ボクセル → 領域 → 輪郭 → 多角形のメッシュ+詳細メッシュ | 重なった階も扱える(heightfield の layer=`rcBuildHeightfieldLayers`)。段は `walkableClimb`(越えられる段の高さ)、坂は `walkableSlopeAngle` で自動に決まる。EV・ES・飛び降りは off-mesh 接続を人が置く | 形があれば全自動。パラメータ(セルの大きさ cs・ch・tile)は人 | zlib | Unity・Unreal・Godot・O3DE が使う(README の記述)。都市規模の公開の例は見つからず | [S1] ○・[S2] ○・[S3] ◎・R-59 N9 |
| Unity NavMesh(AI Navigation 2.0) | 描画メッシュか物理コライダー・地形 | NavMesh Data(タイルごと) | 階の明示なし。リンクは自動生成(Generate Links)か手で置く | Bake のボタン 1 つ。既定のボクセル=エージェント半径の 1/3・タイル 256 ボクセル | Unity の規約 | PLATEAU の学習教材 TOPIC36 が横須賀の道路 tran に NavMesh を焼く例(建物と道路の間の板は手で置く) | [S4] ○・[S34] ○ |
| Unreal Engine の navmesh | 衝突の形 | RecastNavMesh(タイル・多角形ごとの費用) | 頁に階の記述なし | Bounds Volume を置くと自動で作る | Epic の規約 | — | [S5] ○ |
| Godot | 描画か物理の形・手で渡す配列 | 3D=ボクセル・2D=輪郭の多角形の切り貼り | 頁に階の記述なし | 背景のスレッドで自動。形の読み込みは主スレッド | MIT(本書では未確認) | — | [S6] ○ |

### 2-2 都市規模の歩行者ネットワーク(地図型・計測型)

| 手法 | 入力 | 出力 | 屋内外・階層 | 自動化 | ライセンス | 実績 | 出典・等級 |
|---|---|---|---|---|---|---|---|
| OSM の歩道タグ(footway=sidewalk・crossing・kerb) | 人の編集 | 線と点のグラフ | level・layer のタグ(付与は場所しだい) | 人の手 | ODbL | 米国 54 都市の比較。属性は surface が最も多く、kerb・smoothness・width は「ほぼ無い」(Seattle・Chicago・NYC)。メリーランド州 6,103 点で、Street View に歩道がある所の OSM の一致は 30.2%(見落としが 2,866 点・逆は 11 点) | [S14] ○・[S15] ○ |
| 同(渋谷の実数) | 段 0 #9 | — | level 166・tunnel 92・bridge 57 | — | ODbL | footway 1,297 本 68.6 km のうち width 4 本(0.3%)・kerb 0 | sp0 §3 ◎ リポ |
| OpenSidewalks Schema 0.3(2026-01-27) | OSM 互換の編集・市のデータ | GeoJSON のグラフ(Node・Edge・Zone) | **level の規定なし・エレベーターの型なし**。歩道・横断・縁石(raised/rolled/lowered/flush)・階段(step_count) | 規格。検査器あり | LICENSE の種類は頁に書かれていない | 米 TDEI の 6 郡ほか(検索の要約 △) | [S12] ○ |
| sidewalkify(AccessMap) | 道路の中心線+左右の歩道の有無 | 中心線から平行にずらした歩道の線 | なし | 全自動の推定。横断と縁石は推定できない(作者の発言) | 未確認 | AccessMap(Seattle ほか) | [S13] △ |
| Tile2Net(Hosseini ら 2023) | 正射の航空写真(ズーム 19 推奨・18 未満不可・19≈30 cm/px) | 歩道・横断歩道・小道の多角形と中心線のネットワーク(GeoParquet) | なし(上から見える所だけ) | 推論は全自動(GPU 1 枚)。対応地域は米国の州・郡のみ。「production には未だ」 | BSD-3 | Boston・Cambridge で歩道と横断歩道の 90% 以上を認識(MIT News) | [S8] ○・[S9] ○・[S10] ○・[S11] △ |
| Project Sidewalk | Google Street View を人が見て付ける | 縁石の切り下げ・無い切り下げ・障害物・路面の点 | なし | 人の手(群衆)+学習の補助を研究中 | コードは公開(種類は未確認) | DC で 18 か月・797 人・205,385 点・2,941 マイル。2025 年に 35 都市・8 か国(△) | [S16] ◎・[S17] △ |
| UrbanVGGT(Tan & Zhang 2026) | Street View の 1 枚 | 歩道の幅(m) | なし | 全自動。カメラの高さで縮尺を合わせるのが最も効く | 未記載 | DC で平均絶対誤差 0.252 m・95.5% が 0.5 m 以内・3 都市 527 区間 | [S18] ○ |
| Mapillary | 群衆の街路写真 | 物体検出・地物の点(API) | なし | 自動検出 | 画像は CC BY-SA。自動の取得は公開の API だけ | 世界 | [S19] △(CLAUDE.md §7 で「検討だけ」) |
| 国交省 歩行空間ネットワークデータ整備仕様(2018-03 改訂で屋内外シームレス・2024-07 に新仕様) | 現地調査・専用ソフト | ノードとリンク+段差・幅員・縦断勾配ほかの属性 | 屋内外。階の属性あり | 人の手が中心 | 公共データ利用規約 1.0(ckan.hokonavi の 43 件中 40 件) | 2018-12 時点で 30 地域約 1,300 km(検索の要約)。ckan.hokonavi.go.jp は 43 件で**福岡は無い**(天神は BODIK の 2018 のみ=R-120 T7) | [S20] ○・[S22] ○・[S23] ○・[S29] ○ |
| 国交省 技術検討(令和 7 年 7 月・参考資料 1) | 基盤地図情報・MMS 点群・航空写真・カメラ・プローブ | 形状データ(リンクとノード)とバリア情報 | 2 次元。立体交差は不可 | 基盤地図情報からの生成が◎(80% 以上抽出)。点群・画像の機械学習は△(50% 以下)。横断歩道の画像検出は○(手動を含む)。プローブは技術検討課題 | 国の資料 | 生成率 8 割前後・座標の精度 1/2500(1〜2 m のずれ) | [S30] ◎ |
| 国交省 歩行空間ネットワークデータ整備システム(2026-03-30 試験公開) | 基盤地図情報を入れて自動抽出 → 現地計測を入力(ガイドライン案の手順) | 歩行空間ネットワークデータ | — | いまは閲覧だけ。編集は次年度 | — | 赤羽駅周辺 | [S24] ○・[S31] ◎ |
| 国交省 AI の現地実証(2026-09-03 募集・10-16 池田市を選定) | 発表文に書かれていない | 幅員・縦断勾配・段差の自動抽出 | — | AI | — | 現地 10 月下旬〜12 月・取りまとめ 2027-01〜02 | [S26] ○・[S27] ○ |
| 基盤地図情報(地理院) | 1/2500 の都市計画基図ほか | 道路縁・建築物の外周線ほか 13 項目 | なし | 全国で整備済み | 地理院の規約(利用者登録) | 都市計画区域内の平面の誤差 2.5 m 以内・高さ 1.0 m 以内 | [S32] ○ |
| 前田(IPSJ・航空写真+電子地図) | 電子地図の歩道の面・航空写真 | 幅員つき歩道ネットワーク | なし | 自動(横断歩道は写真から) | 論文 | JR 山手線の範囲 | [S59] △ |

### 2-3 3D 都市モデル・屋内モデル型

| 手法 | 入力 | 出力 | 屋内外・階層 | 自動化 | ライセンス | 実績 | 出典・等級 |
|---|---|---|---|---|---|---|---|
| PLATEAU 道路 LOD2/3 → 歩道の面 | CityGML の TrafficArea・AuxiliaryTrafficArea | 歩道部・車道部の面 | 屋外。LOD3 で高さ | 国交省は「LOD2 以上で形状データ、LOD3 以上でバリア情報を生成できる可能性」と書く | PLATEAU サイトポリシー | 渋谷(navmesh1)。福岡は道路 LOD1 だけ | [S31] ◎・R-120 T1 |
| PLATEAU LOD1-2 道路モデル自動作成ツール | 道路縁の Shape・航空写真 | LOD1/LOD2 の道路 CityGML | 屋外 | 自動(LOD2 は 12〜16 cm の写真で学習した AI) | 公開(種類は未確認) | 令和 5 年度の調査業務 | [S36] △ |
| IFC → IndoorGML(ifc2indoorgml・Teo & Yu 2017・IFC2BCM 2025) | BIM(IFC の IfcSpace・IfcDoor) | 部屋=節・扉=辺のグラフ | 屋内・階あり | 自動〜半自動。BIM が要る | ifc2indoorgml は「open-source」(種類は頁に無い) | 大学の建物・病院の例 | [S37] ○・[S38] △・[S39] △ |
| CityGML LOD4・平面図 → 航行モデル(Liu & Zlatanova 2013) | CityGML LOD4・平面図 | 論理の航行モデル | 屋内 | 自動の実験 | 論文 | — | [S40] △ |
| 国交省 屋内電子地図(渋谷駅・令和元年度) | 階層別屋内地理空間情報の仕様 | 階ごとの平面と歩行空間 NW | 屋内・B2〜3F | 人の手 | — | 新しい銀座線の区域は作成を断念 | R-112 ◎ リポ |

### 2-4 点群型

| 手法 | 入力 | 出力 | 屋内外・階層 | 自動化 | ライセンス | 実績 | 出典・等級 |
|---|---|---|---|---|---|---|---|
| PDAL filters.smrf(Pingel 2013) | 航空 LiDAR | 地面の分類 | 屋外の地面 | 自動(パラメータ 5 つ) | PDAL の種類は頁に無い(R-119 #30 の扱い) | 標準の部品 | [S44] ○ |
| Balado ら 2019(点群から直接の経路探索) | 屋内の点群 | 床の格子 → 航行グラフ | 屋内・複数の床と階段(主な床からの近さで検出) | 自動。数値の精度は抄録に無い | CC BY 4.0(論文) | ISPRS の屋内ベンチマーク 2 件 | [S41] ○ |
| Staats ら 2019・Flikweert ら 2019 | MLS の点群+歩いた軌跡 | 歩ける面(水平・坂・階段)・IndoorGML のグラフ | 屋内・階段と坂 | 自動。軌跡が要る | 論文 | TU Delft の建物 | [S42] △・[S43] △ |
| 国交省 3 次元地図整備システム(2025-05-23 試行) | 多様な点群の統合 | 歩行空間の 3 次元地図(点群) | 屋内の記述なし | 動く物の除去と統合。申請制 | 申請 | 自治体・大学・民間 | [S25] ○ |
| 国交省 点群からのバリアの抽出の試験 | 車載 MMS・台車 MMS・バックパック・ハンディ・スマホの LiDAR | 段差(2 cm)・幅員・縦断勾配 | 屋外 | 自動。車載と台車は 2 cm を正しく取れ、バックパック・ハンディ・スマホは高さのばらつきで誤って拾う。幅員は路上設備の陰で取れない所あり。勾配は 1% 程度の誤差 | 国の資料 | — | [S30] ◎ |

### 2-5 学習による手法(画像・平面図・言語)

| 手法 | 入力 | 出力 | 屋内外・階層 | 自動化 | ライセンス | 実績 | 出典・等級 |
|---|---|---|---|---|---|---|---|
| 航空写真のセグメンテーション(Tile2Net・国交省の画像領域分割) | 航空写真 | 歩道の面 | 上から見える所だけ。国交省は「ビルの陰などで歩行空間が見えない場合がある」と書く(検索の要約) | 自動 | 手法ごと | 国交省の評価は△(50% 以下) | [S8] ○・[S30] ◎ |
| 平面図の解析(CubiCasa5K ほか) | 平面図の画像 | 部屋・壁・扉の多角形 | 屋内 1 階ずつ | 自動。住宅の図(フィンランド)5,000 枚で学習 | 未確認 | 部屋の正解率は約 84%(TUM の資料の要約) | [S45] △ |
| VLM・LLM で平面図をグラフに(Floorplan2Guide 2025・DeFazio 2024) | 平面図の画像+OCR | 航行の知識グラフ・案内文 | 屋内 | 自動(few-shot)。DeFazio は扉と札を人が足す | 論文 | Claude 3.7 Sonnet の 5-shot で短い経路 92.31%・中 76.92%・長 61.54%。グラフにすると直接の画像推論より 15.4% 高い | [S46] ○・[S47] △ |
| LLM で OSM のタグを提案(Juhász ら 2023) | Mapillary の写真の記述+文脈 | 道のタグ(歩道の有無など) | 屋外 | 半自動(人の記述か BLIP-2) | 論文 | マイアミの小区域。記述を詳しくすると最大 29%・文脈を足すと最大 20% 上がる | [S48] ○ |
| 生成 AI で間取り(HouseDiffusion 2023・境界つき拡散 2024・Ibrahim ら 2024) | 部屋のグラフ・外形・設計の文 | ベクトルの間取り | 屋内 1 階 | 自動の生成 | 論文 | RPLAN(住宅)が中心。Ibrahim は複数の建物の型を謳うが抄録に数値なし | [S49] △・[S50] ○・[S51] △ |

### 2-6 群衆シミュレーションの実務(何を手で描くか)

| 製品 | 入力 | 出力 | 階層 | 手で描くもの・自動のもの | ライセンス | 実績 | 出典・等級 |
|---|---|---|---|---|---|---|---|
| MassMotion(Oasys) | FBX・IFC・DWG・2D の図 | 歩ける面・扉・階段の物 | 3D | IFC から links と portals を自動で見分ける(事例の要約) | 商用 | 空港・駅・競技場 | [S52] ○・[S53] △ |
| PTV Viswalk | DWG(閉じた折れ線を層ごとに面か障害物に)・IFC(床を面・壁を障害物・階段を取り込む) | 階ごとの歩ける面 | 階あり | 面は取り込み可。**階段・坂・ES・動く歩道は長方形で人が描き、上と下の階を指定する**。触れる面は自動で 1 つに合わせる | 商用 | — | [S54] △・[S55] ○ |
| Pedestrian Dynamics(InControl) | CityGML・BIM・CAD/DXF・3DS ほか | 環境を自動で組む | 3D | 経路はゲーム産業由来の手法(パンフレット) | 商用 | — | [S56] △ |
| Vadere | GUI で描く・JSON。OSM からの変換は課題票 #145 | 2D の地形・EikMesh(非構造メッシュ) | 2D | 人の手が中心 | LGPL | — | [S57] △・R-59 N16 ◎ |
| JuPedSim 1.4 | shapely の多角形(穴=障害物) | 1 つの多角形の中の歩行 | 頁に階の記述なし(R-59: 3D の経路エンジンは未リリース) | 形はコードで渡す | LGPL-3 | — | [S58] ○・R-59 N3 |

## §3 段 0 の汎用化(B)

### 3-1 渋谷の手順を「全国でそろう入力」と「渋谷だけの入力」に分ける

| navmesh1 の塗りの段(sp1 §1-1) | 渋谷の面積 m² | 入力 | 全国 | 天神で同じ手順を回すと(推測の印は R-120 の材料からの読み) |
|---|---|---|---|---|
| ① 歩道部・島(LOD2/3) | 126,395 | PLATEAU 道路 LOD2/3 | △(都市ごと) | **空く**(福岡は LOD1 だけ=R-120 T1) |
| ② 横断歩道 1110 | 1,378 | PLATEAU frn | △ | **空く** → ⑤ の OSM で代える(天神の付与率は未確認) |
| ③ 歩道部の無い車道部 | 128,985 | PLATEAU LOD2/3 | △ | **空く** → ④ の規則に落ちる |
| ④ LOD1 の規則(住宅街の型=面全体・幹線=外の縁 2.0 m 仮) | 327,087+53,923 | PLATEAU 道路 LOD1+W1 の道の種類 | ○(PLATEAU の道路 LOD1 は多くの都市にある・推測) | **埋まる**。ただし天神の幹線(渡辺通り・明治通り)の広い歩道は 2.0 m 仮で過小になりうる(推測) |
| ⑤ 横断の帯(OSM の線と点) | 16,060+5,393 の一部 | OSM | △ | 埋まる(付与率は未確認) |
| ⑥⑦ OSM と W1 の線・面の無い車の道 | 57,978+91,667 ほか | OSM(W1 も OSM 由来=R-82) | △ | 埋まる(付与率は未確認) |
| デッキ(階 1・2) | 32,169 | W1 の層・OSM の layer・歩行空間 NW 2020・PLATEAU 橋梁 LOD2(11,473) | ×(橋梁・NW は一部の都市) | 橋梁は**空く**。天神はデッキが少ない見込み(推測) |
| 地下(階 −1〜−4) | 23,588 | PLATEAU 地下街 LOD4.1(15,094)・OSM の層つきの線 | × | **空く**。天神地下街(延床約 53,300 m²・R-120 T16 △)と地下鉄の天神・天神南のコンコース |
| 上下の接続口 245 | — | W1(181)・PLATEAU 地下出入口 4020・歩行空間 NW 2020(59) | △ | frn が無いので OSM の entrance と steps だけ。地下の接続口は地下の面と一緒に空く |
| 高さ | — | PLATEAU dem(TIN) | ○(地形 LOD1 は福岡にある=R-120 T1)+基盤地図 DEM | 埋まる |
| 幅員 4 区分 | 3,353 | 歩行空間 NW 2020 | ×(43 件・福岡なし) | 天神駅の 2018 版だけ(BODIK・範囲は狭い=R-120 T7) |
| 範囲(W2 のセル)・区界 | — | e-Stat の境界・W1 | ○ | 埋まる |

- 渋谷だけの材料(都の点群・3dcel・土地利用現況 GIS・平面図・ユーザーの手の図)は、navmesh1 はまだ読んでいない(§1)。したがって「全国でそろう材料だけで組む」(回答 10-25 §1-1)の線は、いまの段 1 では **PLATEAU の都市ごとの差** と **地下・駅の構内** の 2 点に集まる。
- 置き換えの候補(未リサーチ(expedient)の組み立て): ①③④ の代わりに、基盤地図情報の道路縁と道路構成線の間を歩道の面にする国交省の方式([S30] ◎)を塗りの段に足すと、PLATEAU の LOD に依らない全国で同じ手順になる。国交省の資料の規則は「幅員 5.5 m 未満は道路中心に生成・5.5 m 以上は両側端部に生成」。navmesh1 の住宅街の型と幹線の型の分け方とは別の線引きである。

### 3-2 R-120 §2-1 の表の「段 1 歩ける面」の行を更新する案

| 段 | ○ の材料だけで埋まるもの | 空くもの |
|---|---|---|
| 段 1 歩ける面(R-120 の行) | PLATEAU の道路 LOD1 と建物・基盤地図情報・地理院タイル・OSM(△) | 地下街と駅の中・幅と段差 |
| 段 1 歩ける面(本書の更新案・推測を含む) | 地上の歩道の面=基盤地図情報の道路縁(生成率 8 割前後・1〜2 m のずれ)+PLATEAU 道路 LOD1 の規則/高さ=PLATEAU 地形 LOD1 と基盤地図 DEM/横断=OSM(△)/上下の段差の大半=Recast 型の `walkableClimb` の自動判定(推測) | 地下街・地下鉄のコンコース・ビルの地下階とその接続口(公開の材料なし)/横断歩道の位置(基盤地図に無い)/幅員と段差の実測(天神駅の 2018 版の外)/広場・ロータリー・立体交差(国交省の資料も手動) |

## §4 自動化の候補(C・順位なし)

| 埋めたいもの | 候補の手法 | 埋まる見込み(根拠) | 手で描く残り(推測) |
|---|---|---|---|
| 歩道の無い所・歩道の幅 | 基盤地図情報の道路縁(国交省方式)・sidewalkify 型の中心線のずらし・Street View の幅推定(UrbanVGGT)・OSM の width | 形は 8 割前後([S30])。幅は Street View で 0.25 m の誤差(米国 DC・[S18])。OSM の width は渋谷で 0.3%(sp0) | 交差点の複雑な所・広場・ロータリー・駐車場(国交省の「自動取得が困難なケース」)。天神の範囲で数十か所(推測) |
| 横断歩道 | OSM の crossing・航空写真の物体検出・PLATEAU frn(LOD3 の都市だけ) | 写真の物体検出は○(手動を含む・[S30]) | OSM に無い横断。渋谷は highway=crossing 620 点(sp0)。天神は未確認 |
| 屋内の階と通路 | IFC → IndoorGML・平面図の解析(CubiCasa 型・VLM)・OSM の indoor・生成 AI の間取り | BIM は公開されていない(渋谷駅の uc24-13 も非公開=R-112)。平面図は施設の規約で自動の取得と加工ができない所が多い(R-120 §1(d)・大丸は抜粋や要約にも事前の許諾)。生成 AI は住宅が中心 | 商業施設の通路は施設ごとに手か「無いと宣言」 |
| 地下街 | OSM の indoor・平面図(天神地下街は platinumaps=自動で取らない型)・点群(天神は公開なし) | 公開の自動の手法は見つからなかった | 天神地下街の通路(全長約 590 m=R-120 §3-1 △)と、ビルの地下階への出入口。延床 53,300 m² は店を含むので、通路の面は 1〜2 万 m² 程度(推測) |
| 駅の構内 | OSM の駅の屋内(渋谷は 720 地物)・歩行空間 NW(都営大江戸線 12 駅はチャレンジの期間だけの公開)・国交省 屋内電子地図 | 福岡市地下鉄・西鉄の構内の公開データは見つからなかった | 天神・天神南・西鉄福岡(天神)の 3 駅の改札・コンコース・ホームの階段(推測) |
| 段差と階段 | Recast の `walkableClimb` と `walkableSlopeAngle`・点群(車載や台車の MMS)・OSM の steps と kerb・歩行空間 NW の段差の区分 | 3D の形があれば段と坂は自動で決まる([S3])。点群は MMS なら 2 cm を取れる([S30])。天神には公開の点群が無い | 階段の向きと幅・ES の向き・EV の位置(Viswalk も人が描く=[S55]) |

- 渋谷との比べ(本書の計算): 渋谷の地下の面 23,588 m² のうち PLATEAU 地下街の床は 15,094 m²(64%)。天神では同じ役の材料が 0 なので、地下の面はほぼ全部が手か OSM になる(推測)。

## §5 現実との整合(D・回答 11-01 §0-8・§14)

錨の候補(天神): (a) 都心部歩行者交通量等調査の断面の通行量(令和 6 年度=地上 136 地点・地下 80 地点・平日と休日・R-120 T4・T5)/(b) 滞在の量(人流 1 km メッシュ 2019〜2021・ISIT の AI カメラ=R-120 T31・T32)/(c) 経路の分布(迂回・階の使い分け・出口の分担。いま天神で測れる公開の材料は見つかっていない)。空間は回答 11-01 §1 の区分で「式」、その材料は「入力」にあたる。

| 手法 | 動く錨 | 測れなくなる・危うくなる点 |
|---|---|---|
| 地下を作らない(無いと宣言) | (a) 地上の地点が過大になる(地下を歩く人が地上へ出る・推測) | **(a) の地下 80 地点が測れない**。地上と地下の分担そのものが答え合わせの外になる |
| 地下を手で描く・OSM の indoor | (a) 地下の地点・(c) 階の使い分け | 描いた人の判断が通路の幅と接続口に入る。描く時点と調査の時点(2024-10〜11・天神ビッグバンの工事で通行不可の所あり=R-120)を合わせないと、工事中の通路を歩かせる |
| 基盤地図情報の道路縁(国交省方式) | (a) 地上の地点の配分(1〜2 m のずれは断面の数にはほぼ効かない・推測)・密度と速さ(幅が変わると Kladek の係数が動く) | 横断歩道が無いので、横断の位置を別の材料で置かないと (c) が規則の産物になる |
| LOD1 の規則の幹線 2.0 m(仮) | 密度と速さ・(a) の幹線の歩道の地点 | 2.0 m は渋谷で決めた仮の値。天神へそのまま持っていくと、G2(渋谷で較正した係数のまま天神で検証)の落差に空間の誤差が混ざる |
| Recast 型の自動の段の判定 | (c) 横断の位置(段を越えられる高さの決め方で、縁石を越えて渡れるかが変わる) | `walkableClimb` は人が決める値。値の感度試験が要る |
| 航空写真・Street View の学習 | 形と幅 | 学習した都市(米国)と違う街並みで誤りの向きが分からない。撮影の年と調査の年がずれる |
| 点群(MMS など) | 段差・勾配・幅 | 天神に公開の点群が無い。渋谷の 3dcel は 2017 年の計測(sp0 §7)で、2026 年の世界とずれる |
| プローブ(人の動いた跡)から形を作る | (b)(c) | **循環になる**。人流の答えと同じ種類のデータで道を作ると、経路の分布の答え合わせが作り方の写しになる(回答 11-01 §0-6 の機械検査の対象・推測) |
| 生成 AI で間取りを推定 | (a) 地下・屋内の地点・(c) | 推定の通路が現実に無い可能性。推定した床の上の値は錨と比べる前に「推定」の札を付けて分ける必要がある(推測) |
| 通行量の地点の値で幅や接続口を合わせる | (a) | **使ってはいけない**(較正が test の層に触れる)。天神の令和 6 年度の値は形づくりに使わない |

## §6 出典の表(読んだ日 2026-11-01)

| # | 出典 | URL | 等級 |
|---|---|---|---|
| S1 | Recast `Docs/_1_Introduction.md` | https://github.com/recastnavigation/recastnavigation/blob/main/Docs/_1_Introduction.md | ○ |
| S2 | Recast README(zlib・tiled・TileCache・採用エンジン) | https://github.com/recastnavigation/recastnavigation | ○ |
| S3 | `Recast/Include/Recast.h`(rcHeightfieldLayer・walkableClimb・walkableSlopeAngle・cs/ch・tileSize) | https://raw.githubusercontent.com/recastnavigation/recastnavigation/main/Recast/Include/Recast.h | ◎ |
| S4 | Unity AI Navigation 2.0 NavMesh Surface | https://docs.unity3d.com/Packages/com.unity.ai.navigation@2.0/manual/NavMeshSurface.html | ○ |
| S5 | Unreal Basic Navigation | https://dev.epicgames.com/documentation/en-us/unreal-engine/basic-navigation-in-unreal-engine | ○ |
| S6 | Godot Using navigation meshes | https://docs.godotengine.org/en/stable/tutorials/navigation/navigation_using_navigationmeshes.html | ○ |
| S8 | Tile2Net README | https://github.com/VIDA-NYU/tile2net | ○ |
| S9 | Tile2Net BASICS.md(ズーム 19 推奨・18 未満不可・対応地域) | https://github.com/VIDA-NYU/tile2net/blob/main/BASICS.md | ○ |
| S10 | MIT News 2023-03-15 | https://news.mit.edu/2023/open-source-tool-mapping-sidewalks-0315 | ○ |
| S11 | Hosseini ら 2023 CEUS 101950 | https://doi.org/10.1016/j.compenvurbsys.2023.101950 | △ |
| S12 | OpenSidewalks Schema | https://github.com/OpenSidewalks/OpenSidewalks-Schema | ○ |
| S13 | sidewalkify | https://github.com/AccessMap/sidewalkify | △ |
| S14 | Omar ら 2022(OSM の歩道の信頼度・米国 50 都市超) | https://arxiv.org/abs/2210.02350 | ○(kerb・width の文は検索の要約) |
| S15 | Nichols ら 2026 Prev Chronic Dis 23:260255 | https://www.cdc.gov/pcd/issues/2026/26_0255.htm | ○ |
| S16 | Saha ら CHI 2019 Project Sidewalk(PDF の文字層) | https://makeabilitylab.cs.washington.edu/media/publications/Saha_ProjectSidewalkAWebBasedCrowdsourcingToolForCollectingSidewalkAccessibilityDataAtScale_CHI2019.pdf | ◎ |
| S17 | Project Sidewalk の展開(35 都市・8 か国) | 検索の要約(PacTrans の頁は保守中で読めず) | △ |
| S18 | Tan & Zhang 2026 UrbanVGGT | https://arxiv.org/abs/2603.22531 | ○ |
| S19 | Mapillary 利用規約 | https://mapillary.com/legal | △ |
| S20 | 国交省 報道 2018-03-27(屋内外シームレスに改訂) | https://www.mlit.go.jp/report/press/sogo23_hh_000089.html | ○ |
| S21 | 国交省 総合政策局 歩行者移動支援の新着 | https://www.mlit.go.jp/sogoseisaku/soukou/news.html | ○ |
| S22 | 国交省 報道 2025-09-30(オープンデータサイト) | https://www.mlit.go.jp/report/press/sogo23_hh_000182.html | ○ |
| S23 | ckan.hokonavi.go.jp の一覧 3 頁(43 件) | https://ckan.hokonavi.go.jp/dataset/ | ○ |
| S24 | 国交省 報道 2026-03-30(整備システム試験公開・nwd-editor.hokonavi.go.jp) | https://www.mlit.go.jp/report/press/sogo23_hh_000190.html | ○ |
| S25 | 国交省 報道 2025-05-23(3 次元地図整備システム) | https://www.mlit.go.jp/report/press/sogo23_hh_000178.html | ○ |
| S26 | 国交省 報道 2026-09-03(AI 現地実証の募集) | https://www.mlit.go.jp/report/press/sogo23_hh_000193.html | ○ |
| S27 | 国交省 報道 2026-10-16(池田市を選定) | https://www.mlit.go.jp/report/press/sogo23_hh_000196.html | ○ |
| S28 | 国交省 報道 2026-10-16(ガイドラインとバリアフリー施設等データ整備仕様) | https://www.mlit.go.jp/report/press/sogo23_hh_000195.html | ○ |
| S29 | 国交省 仕様の頁(2024-07 新仕様・2018-03 旧仕様・2026-10 の 2 本) | https://www.mlit.go.jp/sogoseisaku/soukou/sogoseisaku_soukou_tk_000056.html | ○ |
| S30 | 国交省 政策統括官付「これまでの技術的な検討内容」令和 7 年 7 月 参考資料 1(PDF の文字層) | https://www.mlit.go.jp/sogoseisaku/soukou/content/001900528.pdf | ◎ |
| S31 | 「歩行空間における移動支援サービスの取組に関するガイドライン(Ver.1.0)」【案】修正箇所抜粋 参考資料 3(PDF の文字層・2026 年〇月の案) | https://www.mlit.go.jp/sogoseisaku/soukou/content/002018907.pdf | ◎(案の抜粋) |
| S32 | 地理院 基盤地図情報とは(13 項目・精度) | https://www.gsi.go.jp/kiban/towa.html | ○ |
| S33 | 地理院タイル一覧(seamlessphoto はズーム 14〜18) | https://maps.gsi.go.jp/development/ichiran.html | ○ |
| S34 | PLATEAU Learning TOPIC36(Unity NavMesh・横須賀) | https://www.mlit.go.jp/plateau/learning/tpc36/ | ○ |
| S35 | PLATEAU Pedestrian-Simulation-Model-for-artisocCloud(西新宿・Apache-2.0) | https://github.com/Project-PLATEAU/Pedestrian-Simulation-Model-for-artisocCloud | ○ |
| S36 | PLATEAU Auto-Create-tran-lod1-2-tool | https://github.com/Project-PLATEAU/Auto-Create-tran-lod1-2-tool | △ |
| S37 | ifc2indoorgml(Diakité ら 2022) | https://ual.sg/post/2022/06/05/ifc2indoorgml-an-open-source-tool-for-generating-indoorgml-from-ifc/ | ○ |
| S38 | Teo & Yu 2017 | https://isprs-archives.copernicus.org/articles/XLII-4-W2/167/2017/ | △ |
| S39 | IFC2BCM(Jia ら 2025 SoftwareX) | https://doi.org/10.1016/j.softx.2024.101975 | △ |
| S40 | Liu & Zlatanova 2013 | 検索の要約(DOAJ) | △ |
| S41 | Balado ら 2019 | https://isprs-archives.copernicus.org/articles/XLII-2-W13/753/2019/ | ○ |
| S42 | Staats ら 2019 IJUS | https://ideas.repec.org/a/taf/rjusxx/v23y2019i3p369-390.html | △ |
| S43 | Flikweert ら 2019 | https://isprs-annals.copernicus.org/articles/IV-2-W5/271/2019/ | △ |
| S44 | PDAL filters.smrf | https://pdal.io/en/stable/stages/filters.smrf.html | ○ |
| S45 | CubiCasa5K(Kalervo ら 2019) | https://arxiv.org/abs/1904.01920 | △ |
| S46 | Ayanzadeh & Oates 2025 Floorplan2Guide | https://arxiv.org/abs/2512.12177 | ○ |
| S47 | DeFazio ら 2024 | https://arxiv.org/abs/2409.12842 | △ |
| S48 | Juhász ら 2023 | https://arxiv.org/abs/2306.03204 | ○ |
| S49 | HouseDiffusion(CVPR 2023) | https://arxiv.org/abs/2211.13287 | △ |
| S50 | Ibrahim ら 2024 | https://arxiv.org/abs/2412.06859 | ○ |
| S51 | Takeuchi ら 2024(境界つきの拡散) | https://doi.org/10.1145/3681756.3697884 | △ |
| S52 | MassMotion の製品の頁 | https://www.oasys-software.com/products/massmotion/ | ○ |
| S53 | MassMotion の IFC 自動の割り当て(事例) | 検索の要約(oasys-software.com の事例の頁は 404) | △ |
| S54 | Viswalk AutoCAD からの取り込み | https://cgi.ptvgroup.com/vision-help/VISSIM_2024_ENG/Content/8_VISWALK/Konstruktionsele_CADImport.htm | △ |
| S55 | Viswalk 構造要素のモデル化 | https://cgi.ptvgroup.com/vision-help/VISSIM_2024_ENG/Content/8_VISWALK/Konstruktionsele_mod.htm | ○ |
| S56 | Pedestrian Dynamics パンフレット | https://pmcorp.com/wp-content/uploads/2024/09/PD-Product-Brochure-US-2024.pdf | △ |
| S57 | Vadere(LGPL・課題票 #145) | https://gitlab.lrz.de/vadere/vadere/issues/145 | △ |
| S58 | JuPedSim Geometry | https://www.jupedsim.org/stable/concepts/geometry.html | ○ |
| S59 | 前田(IPSJ・幅員つき歩道 NW) | https://ipsj.ixsq.nii.ac.jp/record/195340/files/IPSJ-HCI19182023.pdf | △ |

- 写し検査の注: Project Sidewalk の DC の距離は、検索の要約が「1,075 マイル」、論文の抄録が「audited 2,941 miles」と食い違う。本書は抄録(◎)を採った。2,941 は重複を含む監査の延長とみられる(推測)。
- S7 は欠番(R-59 を参照に回した)。

## §空欄

1. 天神の OSM の歩行系と屋内のタグの付与率(footway=sidewalk・crossing・level・indoor・天神地下街の有無)。Overpass には問い合わせていない。
2. 国交省の AI 現地実証の入力の種類(別添の募集要領と参考資料 1 を読んでいない)。
3. 歩行空間ネットワークデータ整備仕様 2024 年 7 月版の中身(新旧比較表を含む・未読)。
4. Recast の off-mesh 接続と TileCache の詳細(R-59 N9 で既読のものは引いた)。Unity の Links Generation の頁(未読)。
5. MassMotion の取扱説明書(Floor・Link・Stair・Portal の定義と自動生成の範囲)。Pedestrian Dynamics の一次の文書。
6. OpenSidewalks・ifc2indoorgml・Project Sidewalk・PLATEAU の道路自動作成ツールのライセンスの種類。
7. 地理院 seamlessphoto のズーム 18 の地上の解像度(頁に記載なし)と、福岡市が持つ高解像度の航空写真の公開の有無。
8. PLATEAU 福岡市の道路 LOD1 の範囲が天神を全部覆うか(R-120 T1 の未確認と同じ)。
9. 天神の地下で、福岡市・西鉄・福岡地下街開発が屋内の 3D・BIM・歩行空間 NW を出しているか(検索では見つからなかっただけ)。
10. 国交省の「2018-12 時点で 30 地域約 1,300 km」は検索の要約だけで、原典の PDF を読んでいない。
11. Overture Maps の transportation 層の歩道の扱い(調べていない)。

## §親に聞きたいこと

1. **天神の OSM の付与率を数えるか**: Overpass(許可の一覧の中)に、天神の範囲の数え上げだけ(`out count`)を問い合わせてよいか。取得の記録(日付・クエリ・md5)とライセンス台帳の行が要る。§3-1 の「付与率は未確認」の 4 行がこれで埋まる。
2. **基盤地図情報の道路縁を塗りの段に足す腕を作るか**: 回答 10-25 §2-1 で基盤地図情報を足すと決まり、登録はユーザーの手。渋谷で「全国の材料だけの版」(PLATEAU LOD1+基盤地図の道路縁+OSM)を組み、いまの navmesh1 との差(面積・塊・セルの歩ける面積)を測れば、天神へ持っていく前に空間の誤差の大きさが分かる。実装の停止(10-25)と段 0〜3 の解除(prompt 11-01)のどちらに入るかの判断が要る。
3. **地下と駅の構内の扱い**: 天神では、手で描く・OSM の indoor・「無いと宣言」のどれを既定にするか。「無いと宣言」なら通行量調査の地下 80 地点は答え合わせから外れる(§5)。手で描くなら、描く人と描く時点(令和 6 年度の調査の時点の工事の状態)を決める必要がある。
4. **推定の床(生成 AI・平面図の解析)を入れてよいか**: 回答 11-01 §0-2 の「まだ判断の口が無い過程は無いと宣言」は判断の話で、空間の推定には直接当たらない。推定した床を「入力(推定)」の札で入れるか、入れないかの線引きを聞きたい。
5. **幹線の縁 2.0 m(仮)などの空間の仮の値を「較正の係数の台帳」(回答 10-25)に数えるか**: 数えるなら、天神へ持っていくときの係数の数に入る。
6. **航空写真の道を追うか**: Tile2Net はズーム 19 を勧め、地理院の全国最新写真はズーム 18 まで。福岡市の航空写真を探す・問い合わせるのはユーザーの手になる。国交省の評価(画像領域分割=△)と合わせると優先度は低いと読むが、親の判断を聞きたい。
7. **ckan.hokonavi.go.jp と nwd-editor.hokonavi.go.jp**: どちらも許可の一覧の外。渋谷の歩行空間 NW は G空間情報センターから取っているが、新仕様(2024-07)のランク区分のデータはこのサイトにある。取得を足すかはユーザーの判断。

## 親の一次確認(第340・2026-11-01・Fable 5.1)

- 国交省「これまでの技術的な検討内容」(令和 7 年 7 月・政策統括官付・参考資料 1・26 頁・S30 の PDF の文字を親が抽出して実読): 「国土地理院の基盤地図情報から、形状データを生成する手法が最も効果的であることを確認」「形状データの生成率は8割前後と高い。データの座標精度は1/2500(1～2mのズレ)。横断歩道に関する情報は整備されていない」「2次元の整備であることから立体交差部が取得不可」「ロータリーや公園等の広い歩道は取得できな(い)」「公園・広場等の面中心が明確でない…箇所は手動編集が必要」=本文 §0 の 3 と一致(◎)。凡例「◎:80%以上抽出、○:50～80%抽出可、△:50%以下人による抽出」。
- 面積の再計算(sp1 §1-2 の表を親が実読): 歩ける面の合計 797,320+28,685+3,484+8,985+6,083+5,863+2,657=853,077 m²・福岡の PLATEAU に無い地物の分 126,395+128,985+1,378+15,094+11,473=283,325 m²(33.2%)=一致(◎)。
- 等級: S1〜S59 のうち親が原文で確かめたのは S30 と sp1 の表。Recast.h の引用・Tile2Net の zoom の条件・Project Sidewalk の距離(抄録で 2,941 マイル=筆者が検索の要約の 1,075 を訂正)・池田市の実証(2026-10)は筆者の等級のまま。
- 親の判断(ユーザーへ・PENDING §1-1): 問い 1(天神の OSM のタグの付与率を数えるだけの Overpass の問い合わせ)=Overpass API は許可の一覧にある(CLAUDE.md §7・10-03)ので親の判断で可(日付・クエリ・生データ・md5 を記録・ODbL は台帳に)。問い 7(`ckan.hokonavi.go.jp`・`nwd-editor.hokonavi.go.jp`=国交省の歩行空間ネットワークの目録と編集の場)=一覧の外=承認待ち。問い 2(渋谷を「全国の材料だけ」で組み直して誤差を測る腕)=11-01p の段に無い=着手しない(段 0 の汎用化の計画の題として PENDING §3 へ)。問い 3〜6 は天神の段の設計で決める。
