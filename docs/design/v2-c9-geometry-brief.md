# C9 位置幾何(位置と注意)— 設計ラウンドの材料(事実の棚卸し・2026-09-17)

> **位置づけ: 材料のみ。決定も推奨も書かない**(親がこれを元に決定アジェンダを組む)。
> 出典は `ファイル:行` / 決定台帳の行 / PENDING の番号で示す。親が確かめていない推測には **[推測]**、
> 本調査でリポ内資産から再計算した値には **[再計算]** を付す。Web・サーバーは使っていない。
> 対象工程: S3 の先頭 **C9 位置・幾何**(`docs/design/v2-schedule-and-research-plan-2026-09.md:40` =
> 「xy 近接・容量=幾何÷1 人面積」・順序 C9→C10→C11・同 :54「C9(座標)が無いと C10 の
> 『誰が近くにいるか』が定義できない」)。

---

## §1 いまの位置の表し方(事実)

### 1.1 セル(場所)

| 項目 | 値 | 出所 |
|---|---|---|
| place_id 総数 | **520** = GL 453 / DECK 39 / UG 28 | `data/world/v2/W2.header.json` gates `n_place_ids` / notes `n_cells_by_band` |
| セルの大きさ | **100 m 角**(`cell_m: 100.0`)・全セル `area_m2 = 10000.0` | `data/world/v2/world_crs.json` / `w2_cells.parquet`([再計算] area_m2 は 520 行すべて 10000.0) |
| 座標系 | `crs: "local-m"`・`X=east,Y=north,Z=up`・原点 35.6595/139.70062・`m_per_deg_lat 111132.9` / `m_per_deg_lon 90447.033`・`ground0_m 15.18` | `data/world/v2/world_crs.json` |
| 層(band) | `UG(-1) / GL(0) / DECK(1)`・`band_of_layer` が OSM layer タグ -2..2 を 3 値へ写像 | 同上・`src/shibuya/agents/state.py:278` |
| `w2_cells.parquet` の列 | `place_id, ix, iy, band, centroid_x, centroid_y, n_nodes, n_edges, rep_node_idx, rep_node_id, block_ids, area_m2, block_area_m2`(520 行) | [再計算] pyarrow schema |
| 隣接の持ち方 | **セルの隣接表は無い**。隣接は ① グリッド添字 `ix/iy/band`(W2 のゲート `cell_4neighbour_pairs_gl=785` は検査値であって実行時の表ではない) ② **W3 の全点対 next-hop**(`w3_next_hop.npy` 3,499×3,499・48.97 MB)+`w3_cell_dist.npy`(520×520 uint16 m・max 3,758 m・mean 1,377 m) | `data/world/v2/W2.header.json` / `W3.header.json` |
| セル代表ノード | `rep_node_idx`(セル内ノード重心に最近のノード)・520 行すべて ≥0。**移動の目的地はこの 1 点に丸められる** | `W2.header.json` expedients / `src/shibuya/engine/resolve.py:869-880` |
| 街区 | `w2_blocks.parquet` 1,227 行(`area_m2` 中央値 759.1 m²・合計 3.32 km²)。**エンジンが読む箇所を見つけられなかった**(§6-8) | `W2.header.json` notes |

DECK/UG の扱い: 歩行グラフは層を跨ぐ辺を **51 本**だけ持つ(`steps_edges_crossing_bands=51`・
`edge_layer_counts` = -1:102 / -2:88 / 0:4,448 / 1:246 / 2:60)。可視性 W8 は
`band_separation_violations=0`=**層をまたいだ可視は無い**。UG は「建物ラスタを適用しない(地下街の
内部形状が無い)」・DECK 視点の眼高は GL と同じ(デッキ床高が未取得)= どちらも expedient
(`data/world/v2/W8.header.json` expedients)。影 W9 も「UG は常時日陰・DECK は GL と同じ日射」。

### 1.2 体の位置(SoA)

`src/shibuya/agents/state.py:274-286` の位置欄(M2 の内数):

| 欄 | dtype | B | 意味 |
|---|---|---|---|
| `cell` | int32 | 4 | 所属セル(place_id 索引)。-1=場外 |
| `node` | int32 | 4 | 現在の歩行グラフノード(W1 node_idx) |
| `band` | int8 | 1 | UG=-1 / GL=0 / DECK=1 |
| `xy` | float32×2 | 8 | 平面座標[m](W0 CRS) |
| `path_next_node` | int32 | 4 | 次ホップ。-1=経路なし |
| `target_node` | int32 | 4 | 移動の目的ノード。-1=目的なし |

**セル内位置は「有るが独立していない」**: `xy` は毎 tick `resolve` が
`r.xy[:] = world.assets.node_xy[node]`(`src/shibuya/engine/resolve.py:805`)で**ノード座標に上書き**
する。つまり位置の自由度はノード 3,499 個に量子化され、**同じノードに居る体どうしの距離は 0**。
セル内ノード数は 中央値 5・最小 1・最大 38([再計算] `w2_cells.parquet` の `n_nodes`)。
`_nearby_items`(`src/shibuya/perception/renderer.py:1116-1176`)はこの `xy` の差で近接上位 k を
選ぶので、近接の解像度=ノード間隔。W1 の平均辺長は 186,741 m ÷ 4,944 辺 = **約 37.8 m**
([再計算] `W1.header.json` の `total_edge_length_m` / `n_edges`)。

`TargetKind`(`src/shibuya/llm/contract.py:100-108`)= `NONE / CELL / ITEM_CATEGORY / PERSON /
STATION_OR_VEHICLE / EVENT`。表層の解釈は `parse_target`(同 :757-790): `C-0117`/`g12_34_GL`→CELL・
`P-204`/素の整数→PERSON・`…駅`→STATION_OR_VEHICLE・**それ以外の自由文は全部 ITEM_CATEGORY**・
**EVENT はこの関数から出ない**(通報/遅延報告の対象はエンジンが文脈で決める)。
契約 24 語の対象型は 移動=CELL / 乗車=STATION_OR_VEHICLE / 降車=CELL / 購入=ITEM_CATEGORY /
待機=NONE / 会話=PERSON / 並ぶ・撮影=CELL(`target_declared=False`)ほか(同 :160-495)。
語彙 v2 の「食事」は ITEM_CATEGORY 枠・コード 24(同 :562-575)。

### 1.3 移動

- **1 tick = 60 秒**(`src/shibuya/engine/clock.py:10`「既定 60 秒=1分」)。
- **1 tick = 1 ノード前進**(`src/shibuya/world/graph.py` の `step_once`)。頭注に expedient として明記:
  「合成世界(1 セル=1 ノード・100 m)では 6 km/h に一致するが、**実資産(W1)のノード間隔では
  もっと遅い**。実速度・群衆物理は U15(C4 以降)で置き換わる=**C2 の暫定**」(`world/graph.py:20-23`)。
  実資産の含意=平均 37.8 m/分 ≒ **2.3 km/h** [再計算]。
- 経路: `route_next_node` が `w3_next_hop` をファンシー添字 1 回で引く(逐次ループなし)。
- 目的地: LLM が返すのは**セル**。`_apply_move` がそれを `cell_rep_node` へ写す
  (`engine/resolve.py:869-880`)= セル内のどこへ向かうかは指定できない。
- 失敗コード(`agents/state.py:128-178`): `UNREACHABLE`(前進できない=`stuck`)・`INTERRUPTED`・
  `BAD_TARGET`(対象を特定できない)。到着で `activity=IDLE`・`target_node=-1`。

### 1.4 混雑・容量

| 定数 | 値 | 定義位置 | 用途 | タグ |
|---|---|---|---|---|
| 歩行可能面積(合成) | `CELL_SIZE_M² × 0.15` = 1,500 m² | `perception/renderer.py:98` `WALKABLE_FRACTION_SYNTHETIC` | 密度→人/m² の**分母** | expedient(頭注 :24-26) |
| 街路点 1 点の面積 | 6.25 m²(2.5 m 格子) | 同 :100 `STREET_POINT_AREA_M2` | 実資産の分母 | — |
| 実資産の分母 | `max(街路点数 × 6.25, 1500)` | 同 :509-510 `_street_aggregate` | 同上 | 0.15 は**床**として残る |
| 店舗床面積 | 既定 **80 m²**・カテゴリ別表(food 60 / shop 100 / office 200 / hotel 400 …) | `engine/processes/crowd.py:66-84` | 席数換算の分子 | expedient |
| 1 席あたり面積 | 飲食・nightlife **2.0 m²** / その他 **4.0 m²** | 同 :76-78 | 席数 c = 床面積 ÷ 1 席面積 | expedient |
| `DWELL_MAX_TICKS` | **30**(在席の上限滞在=回転率) | 同 :86 | 在席解除。語彙 v2「食事」の 20 分もこれに従う(`llm/contract.py:554`) | expedient |
| `WAIT_MAX_TICKS` | **15**(待ち行列の離脱閾値) | 同 :88 | 超えたら並ぶのをやめ `INTERRUPTED` | expedient |
| 密度段階の境界 | (1, 5, 20, 60, 150, 400, 1000) 人/セル | `world/state.py:44` `DENSITY_STAGE_EDGES` | B4 の段 | expedient(「刻みは自前」) |
| `can_admit` | 同一呼び内は**行順**で席を詰める(pk 昇順でなく行順) | `engine/processes/crowd.py:141-161` | 満席なら購入は待ち行列へ | expedient |
| M/M/c 平均待ち | `lam = queue_len / WAIT_MAX_TICKS` | 同 :256 | **観測欄のみ・行動は駆動しない**と頭注が宣言 | expedient |
| 流れの 3 値化 | `STILL_SHARE 0.20` / `COHERENT 0.50`・8 方位は診断のみ | 同 :90-94 | B4「人の流れは{flow}」 | expedient |

**事実の訂正材料**: 第177・R-8・実装計画書 §9.1(`docs/design/v2-implementation-plan.md:121`)は
「密度の分母=100 m×0.15」と書くが、**本番(実資産)経路では 0.15 は下限にしか効かない**。
[再計算] `w10_street_points.parquet` を `w2_cells` の `(ix,iy,band)` へ束ねて `max(n×6.25, 1500)`
→ 520 セルの歩行可能面積は 中央値 **4,206 m²**(= セル面積の 0.42)・平均 4,041・p25 2,456・
p75 5,419・最大 9,657・**床 1,500 m² に張り付くセルは 11.5%**。街路点を 1 つも持たないセルは 0。

### 1.5 知覚(見える / 聞こえる / 気づく)

- 可視性は**前計算**: W8 が視点 356,732 点(GL 326,849 / DECK 19,497 / UG 10,386)× 対象 9,592
  (building 7,210 / poi 2,337 / exit 45)を 2.5 m ラスタで判定。**最大視程 150 m・視野角なし
  (全方位)**・眼高 1.5 m・2.5D。1 視点あたり平均 14.5 件・T1 セル集約 43,479 行・T2 は 520×520。
  出力 5.87 MB(M10 512 MB の 1.1%)(`data/world/v2/W8.header.json`)。
- `p_notice`(人物③・顕著行為の到達)= 2 段ヒル型。`d50 = 40 m`・打ち切り **80 m**(±1 リング=9 セル)・
  `m_density` 疎 1.0 / 中 0.5 / 密 0.2・社会項半径 **15 m**・`m_load` 0.46。実装
  `src/shibuya/perception/p_notice.py`。値はすべて expedient(`docs/design/v2-perception-contract.md:68-77`)。
- 聴覚: 静的騒音場は W10(セル別段階・昼夜 2 枚)。イベント半径は
  `r = 10^((L_src − L_amb − ΔSNR)/N)`・内容 ΔSNR −3 dB / 検知 −12 dB。**傍受は可聴 r ≈ 2 m**。
  会話の可聴半径は密度に弱依存(×0.42)(同 :48-65・決定台帳 R3-7 行)。
- **同セル前提**: 会話の前提「距離 ≦ d_talk(≈1 m)」は**同一セルで代理**している。
  `src/shibuya/engine/conversation.py:24-26` が理由を明記:「C2/C3 の個体は**セル内座標を持たない**
  (`AgentState` は cell と xy を持つが会話距離の判定に使える精度が無い)」= expedient。
- 近接(人物④)は **同一セル在席者のみ**から上位 k(LOS A/B→3・C/D→2・E/F→1)+知人常掲。
  境界は expedient(`perception/renderer.py:1155-1163`)。
- 注意ゲート 段0〜3 は実装済み(`src/shibuya/perception/attention.py`)。段0=幾何(呼び出し側が渡す)・
  段1=p_see(大型 0.70 / 中小 0.14-0.40=英仏流用の expedient)・段2=件数(広告 1・顕著 1-2・傍受 1-2)・
  段3=内容キャップ `round(7.5×注視秒)`。
- **近接入替(`PROXIMITY_SWAP`)は起床条件としては no-op**: 列は在る
  (`agents/state.py:194`・不応期 15 分・`engine/commit.py:121`)が、「候補に出す過程が §9 第2陣で
  未実装」= PENDING **D-49**。ablation ③ は現状回せない。
- 注意ゲートの較正は **D-59 の判断待ち**: 広告ゼロ ablation が seed 揺らぎの 6〜8 倍で
  購入 −1.0〜−1.3 pp = AD1(第3封印行「広告全消去で絶対 1 pp 未満」)を超える。(b)= 注視確率を
  実測帯(中小媒体 0.14〜0.40・大型ビジョン 0.63〜0.78=知覚契約 §4。旧「0.14-0.79」は写し誤り=第232 訂正)の下側へ較正する案 → **ユーザー決定 D-59 (b)(第229)・実装 IMPLEMENTED #36(`--signage-p-see`・腕 AB6b-AD-NOTICE)**(`PENDING.md:79`)。

### 1.6 目印(ランドマーク)

- POI 2,337 件の `cat` 内訳 [再計算 `w6_poi.parquet`]: food 823 / shop 721 / nightlife 259 /
  office 124 / service 114 / hotel 89 / school 71 / **landmark 56** / leisure 42 / hall 18 /
  **attraction 12** / cinema 7 / education 1。`subcat` は landmark のうち worship 29 のみ。
- **「忠犬ハチ公像」は実在の POI 行**(cat=landmark)[再計算]。ほかに「ハチ公口」等の出口名 3 行。
- **文字列だけではない**: `perception/renderer.py:391-399` が W8 可視表から
  `cat ∈ {landmark, attraction}` の POI 名と駅出入口を最大 4 件拾い、`B2.landmark`
  「[B2 地物] 目印: {items}。」として描画している(`perception/templates.py:437`・予算 25 tok・
  根拠等級 **E**=知覚契約 §3.2)。= **目印は観測には出ているが、行動の対象にはならない**
  (`parse_target` は自由文を ITEM_CATEGORY に落とす)。
- `src/shibuya/build/lang/common.py:332-336` の `KNOWN_PROPER`(「ハチ公」「スクランブル」等)は
  W14/W15 の**捏造検査用**の既知固有名詞リストであって世界オブジェクトではない。
- **OSM の `tourism=artwork` / `historic=memorial` は取得していない**: W6 は v1 由来の
  `shibuya_osm_wide_v8.json` の `cat` をそのまま使う(`src/shibuya/build/geo/w6_poi_org.py:1-16`)。
  街路地物は別途 `street_features_overpass_20260907.json` に 2,009 要素
  (横断歩道 612・樹木 384・信号 166・駐車場 130・乗降場 128・バス停 127・自販機 54・街灯 51・
  消火栓 50・ベンチ 38 ほか)があるが **W6/W8 には入っていない**(`docs/data-license-ledger.md:28`)。

---

## §2 使えるデータ(事実)

| 資産 | 解像度・件数 | ファイル | ライセンス台帳の行 |
|---|---|---|---|
| PLATEAU 建物(W4) | 7,210 棟(PLATEAU 実測 3,531・高さ中央値 14.3 m・最大 231 m)。列 `h_m, levels, kind, area_m2, centroid_x/y, levels_below` | `data/world/v2/w4_buildings.parquet` | `docs/data-license-ledger.md:12`(2020年度版)・`:23`(2025年度版フル zip 4.79 GB) |
| PLATEAU tran(道路) | 2025年度版 30 メッシュ。中心 4 タイル実査: `tran:Road` 3,248・`TrafficArea` 4,053・**LOD3 面 5,782**。**幅員・車線数・交通量属性は 0 件** | `data/realworld/plateau_2025/…`(gitignore 下) | 同 `:23` |
| PLATEAU dem / ubld(地下街) | dem 2 メッシュ・ubld 1 | 同上 | 同 `:23` |
| W9 影 | 街路点 356,732 × 288 面/日(5 分刻み)・12.84 MB/日(D-2 の宣言 10 MB を超過) | `w9_shadow_2026-07-28.npy` | — |
| OSM 歩行グラフ(W1) | ノード 3,499 / 辺 4,944 / 総延長 186,741 m。klass: footway 1,937・residential 724・service 557・unclassified 529・tertiary 481・pedestrian 262・steps 193・primary 127・secondary 75 ほか。層跨ぎ 51 | `w1_nodes.parquet` / `w1_edges.parquet` | `docs/data-license-ledger.md:9,18`(ODbL 1.0) |
| OSM POI(W6) | 2,337 件(建物束縛率 0.688)+組織 9,872 社(従業者 222,849) | `w6_poi.parquet` / `w6_org.parquet` | 同 `:9,18` |
| OSM 入口(W5) | 7,261 件(`kind, ref, name, x, y, node_idx, place_id, band`) | `w5_entrances.parquet` | 同 `:9` |
| OSM 街路地物 | 2,009 要素(§1.6)= **未取り込み** | `data/realworld/osm/street_features_overpass_20260907.json` | 同 `:28` |
| 駅構内(W11) | 駅 3 タイトル(渋谷 38 出口・表参道 5・神宮前 2)= 出口 **45**・駅内グラフ ノード 60 / 辺 57・フロアガイド接続 22。屋内経路長=幾何距離 × 1.3(expedient) | `w11_*.parquet` | ODPT(`:13`) |
| 可視性(W8) | §1.5 参照。T1 356,732 行・T1 セル集約 43,479 行・T2 520×520 | `w8_t1.parquet` / `w8_t1_cell.parquet` / `w8_t2.npy` / `w8_targets.parquet` | — |
| 騒音(W10) | 街路点 356,732(`x,y,band,nearest_edge_idx`)+セル別段階 昼/夜 | `w10_*.npy` / `w10_street_points.parquet` | 道路交通センサス `:29`・都環境局 `:30` |
| SCJ 施設 214 件 | **リポに無い**。5 エリア属性つきで 214 件中 213 件が bbox 内(唯一の外れ=新宿の施設のタグ付けミス)= D-41 の昇格条件 | — | `docs/research/v2-area-boundary-definition.md:248` |
| 5 エリア写像(D-41) | `area_axes_v0.json`(楕円外縁+分割線)= **expedient**。±50 m で 5.6-8.3% のセルが移動。公的ポリゴンは存在しない | `tools/c7/area_axes_v0.json` | 区オープンデータ/KDDI `:19`(holdout) |
| PT 調査 | 第6回東京都市圏 PT(2018・平日)目的別×代表交通手段 OD(346,372 行)+ゾーンコード表 | `data/realworld/pt_tokyo/` | `:25,26` |
| 国勢調査・境界 | 小地域 80 町丁目ポリゴン(JINKO 合計 243,883・AREA 15.12 km²)+年齢5歳階級×男女 | `data/realworld/estat/` | `:21,22` |
| Jülich 歩行者実験 | 軌跡 zip 5 本+metadata 5 本・146 MB(2009 bottleneck / unidirectional open・closed / 2013 unidirectional / crossing_90) | `data/juelich_ped` | `:31`(CC BY 4.0) |

---

## §3 決定済み・未決(事実)

### 3.1 決定済み

- **群衆物理 U15-1〜8**(決定台帳「R7 群衆物理(前倒し)」行・09-08・ユーザー「U15-1〜U15-8の承認」/
  `docs/design/v2-crowd-physics.md`): CFSM 第1候補(AVM 第2・SFM 対照・**ORCA / 連続体は不採用**・
  CA は保留)/ Warp HashGrid + カーネル 2 本 / dt 掃引の数値収束テスト / LOD = LOS C 相当
  (0.43〜0.72 人/m²)超のセル+駅構内+横断待ちのみ物理・**expedient + 感度試験** /
  較正 3 段(Jülich → 自由速度 Weidmann 1.34 m/s 出発 + 年齢分布 → 施設容量: 改札 **56 人/台/分**・
  エスカレーター **95.3 / 107.8 人/分**・階段 Fruin 式)/ 検証指標 6 本 / 信号 140 s・37 s・10 s
  (個人観測 = expedient)・横断待ち行列は自前 / juelich_ped 複写済み。
- **物理コア技術路線**(決定台帳「4 物理コア技術路線」行・09-07): Python+NumPy/Numba(CPU)+
  **Warp(GPU 第一)**・移行条件を事前宣言。「群衆物理の方式(U15)は Phase 2 比較後(合意済み繰延)」。
- **場所セルの粒度**(知覚契約 §5 / §10.1 未決B・09-03): **100 m 級 + 層分離(地上 / 地下街・駅地下 /
  デッキ)**。50 m 級は「計算 3-8%・忠実度も差小(正方セルは街区を跨ぐ)」で不採用・
  第2候補=**100 m 格子 ∩ 街区**。2 解像度分離=**場所セル 100 m × 可視性格子 2.5 m**。
- **第177 M3/M4 の親推奨**(`STATUS.md:7`・**ユーザー判断待ち**): **M3** 幾何に基づく制約
  (0.15 / 80 m² / 2・4 m² を測った値へ)= 推奨「**第2陣の主題**」/ **M4** CFSM 群衆物理
  (0.62〜1.34 h/日)= 推奨「**M3 の後**」。第177 の評価本文
  (`docs/log/devlog-compressed.md:300`):「容量の規則はすでに『幾何 ÷ 1 人あたり空間』の形で、
  **発明しているのは幾何のほう**(密度の分母 100 m×0.15・店の床面積 80 m²・1 席 2/4 m²)」
  「3D は規則を消さず移す(定数が少なく・全域共通・出典つきになる=**指紋の最小化**)」
  「費用は障害でない(engine_spike 40 万体 0.62〜1.34 h/日=P1 内)」
  「限界=**LLM はセルより下を見ない**・D-67 / D-68 は直らない」。
- **原則「行動はオブジェクトの affordance 由来」**(決定台帳 :460・09-17 ユーザー「12. 推奨で」):
  「既存の動詞+対象の型(`TargetKind`)でオブジェクトの affordance として表せるか。表せるなら
  **世界データ(実在のオブジェクト・OSM/PLATEAU)を足し、動詞は足さない**。表せないときだけ動詞
  (契約行)を足す。例: 待ち合わせ=目印オブジェクト(ハチ公像等・OSM tourism=artwork /
  historic=memorial)+約束状態(関係層 C10)+`待機` × `TargetKind.PERSON`・失敗コード
  `PARTNER_NO_SHOW`。汎用動詞は少数で多様性はオブジェクトが担う(購入=物・乗車=車両・撮影=被写体)」。
  出所として「第2陣 C9/C10 の物差し」と明記されている。
- **到達点の順位**(決定台帳 :461・09-17): **C(反実仮想)が一位**・その過程で A(再現)と B(研究)の
  両方が必要。

### 3.2 D-71 の C9 起草材料(草案の欄をそのまま転記)

`docs/bench/vocab/ab7_open_s1s2_fleet/report.md` §2 / §4(実 LLM `Qwen3-8B-int8`・温度 0.0・
seed 1+2 合算・未定義行 1,275 / 36 語・プロンプト `vocab-draft-v0`)。**C9 へ回された語**:

| 位 | 語 | 行 | 体 | セル | 時間帯 | 被覆 | 判定 | 対象クラス | affordance |
|---:|---|---:|---:|---:|---:|---:|---|---|---|
| 3 | 近づく | 109 | 101 | 34 | 18 | 61,812 | NEEDS_DYNAMIC | 乗客 | `approach` |
| 4 | 近寄る | 68 | 65 | 39 | 17 | 43,095 | NEEDS_DYNAMIC | 乗客 | `approach_to_platform` |
| 5 | 見る | 69 | 61 | 17 | 19 | 19,703 | DICTIONARY_ROW_SUFFICES | ディスプレイ | `visual_inspection` |
| 6 | 進む | 23 | 23 | 22 | 8 | 4,048 | NEEDS_DYNAMIC | 通路 | `move_along` |
| 7 | 持つ | 16 | 16 | 14 | 8 | 1,792 | NEEDS_DYNAMIC | 荷物 | `carry_object` |
| 8 | 取る | 18 | 17 | 12 | 7 | 1,428 | NEEDS_DYNAMIC | 棚 | `take_item` |
| 10 | 避雨 | 18 | 18 | 16 | 1 | 288 | NEEDS_DYNAMIC | 建物 | `shelter_from_rain` |

- 被覆の式 = `distinct_agents × max(1, distinct_cells) × max(1, distinct_hours)`(同 §5 指紋)。
- 起草の欄順(決定 G)= `word, target_class, affordance, preconditions, effects, cost,
  failure_codes, conservation_accounts, pattern_ledger_row, rationale`。
- 「見る」の `DICTIONARY_ROW_SUFFICES`(見回る→移動・距離 0.80)は **親が誤判定と記した**
  (`docs/log/devlog.md:56`「s5 の『見る→見回る 0.80=辞書行で済む』は**誤判定**(意味が違う)」)。
- **動的検査 ①(発火と保存則)③(世界状態の差分)④(非退化)は未実施**= affordance をエンジンに
  実装したあとの mock ランで測る(同 report 冒頭・§6 空欄)。
- 段0 辞書の意味損失: `docs/design/v2-synonym-policy-v0.md:28,54`「観察・眺める・見物・見学・
  確認・調べる・調査・チェック → **待機**」= ★意味の損失(政策)(9 語)。「**観察 は AB7 open 80 行**、
  加えて未定義の 見る 33〜36 行(30 体)・近づく / 近寄る 74〜92 体が同じ群。**第2陣 C9(位置幾何・
  注意)の第 2 起草材料**」。同 :12, 67, 73「**対象の損失 17 行**=帰宅・探索・通勤の**目的地の情報を
  LLM から受け取らずにエンジンが決めている**=分業の線を辞書が越えている箇所。C9 の設計で
  `TARGET_HINTS` の要否を決める」。

### 3.3 未決(PENDING の該当行)

| # | 論点(要旨) | 現在の既定 / 状態 |
|---|---|---|
| M3 | 幾何に基づく制約(0.15 / 80 m² / 2・4 m²)を測った値へ | 親推奨=第2陣の主題・**ユーザー判断待ち**(`STATUS.md:7`) |
| M4 | CFSM 群衆物理(0.62〜1.34 h/日) | 親推奨=M3 の後・**判断待ち**(同) |
| D-41 | セル→5 エリア写像は expedient(±50 m で 5.6-8.3% のセルが移動)。昇格条件=① OSM 線形化 ② **SCJ 214 件の属性一致 ≥90%** ③ 区への照会 | (a) この写像で照合し感度(±50 m)を併記(`PENDING.md:66`) |
| D-49 | ablation ② p_notice d50 は A4 既定で天井(到達 10,736 / 10,736 / 10,737・候補 12,899)= 距離項に槓桿なし。A1(距離のみ)なら 10,749 / 10,799 / 10,910。③ 近接不応期は **PROXIMITY_SWAP を起床候補に出す過程が未実装 = no-op**。合成世界では ② は測れない(ノード 1 個/セル) | (a) ② は A1 併用の距離感度として再定義・③ は第2陣着手後(`PENDING.md:74`) |
| D-59 | 広告ゼロ ablation が AD1 の 1 pp 線を超える(seed 1 購入 −1.34 pp / seed 2 −1.02 pp・帰無 JSD 0.0001)。(b)= **注意ゲートの較正**(注視確率を実測帯の下側へ) | **ユーザー判断待ち**(`PENDING.md:79`) |
| D-68 | 個体の同質性。経路 **(1) 形質を状態に**(代謝・疲労・価格感度・社交性を母集団分布から SoA へ)は **設計ラウンド行き**・経路 (3) 記憶と習慣は第2陣 | 経路 1+2 は C7 前に実施済(`PENDING.md:85`) |
| D-71 | §7 段2〜4 の裁定。オフライン裁定バッチ `tools/vocab/` 実装済(IMPLEMENTED #25)。上位 10 語の判定案が**承認待ち** | 「近づく / 見る / 持つ / 取る / 避雨 → C9」(`docs/log/devlog.md:56`) |
| R-7 | 群衆物理 U15 §4 の空欄 10 件 | 「**CFSM を実装すると決めたとき**(第177 M4)」に着手(`docs/research/research-backlog.md:27`) |
| R-8 | 幾何に基づく容量の根拠 4 点: ① 歩行可能面積の実測手順(PLATEAU フットプリント+OSM 幅員の差し引き)② 店舗床面積の出所(経済センサス売場面積・階数×フットプリント)③ 1 席面積の業界標準 ④ **ホーム・改札・階段の実効容量**。改札 56・エスカレーター 95.3/107.8 は取得済だが**ホーム滞留容量は空欄** | 「**幾何に基づく制約を第2陣の主題にすると決めたとき**」(同 :28) |

### 3.4 expedient 登録簿の幾何関連行

- 実装計画書 §9.1: **E-C7-2** セル→5 エリア写像(`docs/design/v2-implementation-plan.md:588`・
  「5 エリアの公的なポリゴンは存在しない」)・**E-C7-1** 形状5指標の操作定義(:574)・
  **E-C7-3b** 種別→KDDI 属性写像(:595)・**E10** 降車セル=45 出口→25 セルへ round-robin
  (昇格条件=「構内経路(W11 の駅内グラフ)を通す **第2陣**」・:852)。
- 知覚契約 §10.3(`docs/design/v2-perception-contract.md:192-` の表): `p_notice d50 40 m` /
  `密度係数 1.0/0.5/0.2` / `打ち切り 80 m` / `負荷係数 0.46` / `社会項の半径 15 m` /
  `叫び声の到達半径 4-13 m` / `近接 k の段閾値 2・4 人/m² と 1 人 33 tok` / `注意予算の件数` /
  `内容キャップ係数 7.5 字/秒` / `中小媒体 p_see 0.14-0.40` / `不応期 9 行`。
- 群衆物理 §3: CFSM 初期パラメータ / dt 収束の許容差 / LOD 閾値と切替 / 自由速度の出発値と
  年齢写像 / 屋外多方向流への基本図適用 / 信号現示 140s・37s・10s / 待機列の形 / CA 保留。
- 世界データ側: W2「格子原点 (0,0)・100 m・層 3 値(D-W2)」「セル代表ノード=セル内ノード重心に
  最近のノード」/ W8「眼高 1.5 m・道路 8 m バッファ・2.5D」「最大視程 150 m・視野角なし」
  「遮蔽の 2.5 m ラスタ近似(横方向誤差 ≤1.25 m)」「DECK 視点の眼高=GL」「UG は建物ラスタ非適用」/
  W11「屋内経路長=幾何距離 × 1.3」。
- `build_manifest.json` の expedient は **122 行**(D-44)。うち設計書が「感度: …」を宣言して
  いるのは 14 行。

---

## §4 性能・バイト予算の制約(事実)

| 行 | 宣言 | 直近の実測 | 出所 |
|---|---|---|---|
| P1 | 物理フレーム ≤**50 ms**/フレーム(Phase 3 以降・GPU・40 万体) | 未実測 | `docs/design/v2-budget-declaration.md:21` |
| P2 | 移動+密度 ≤**5 ms**/フレーム@5 千体・≤20 ms@20,000 体 | **129.622 ms/tick @390,067 体**(判定「—」= 参考。「**予算表に 40 万体の物理行が無い=親判断**」) | 同 :22 / `docs/bench/c7/accept_c7-day-4/c7_accept.md` |
| P4 | 全新機能は ms/シミュ分@基準規模を宣言。**逐次ループの新設は宣言必須** | — | 同 :24 |
| P6 | 変化検出 ≤**2 ms**/tick@40 万体 | 定常 1.07-1.44 / セル 10% 変化 1.62-2.32 / +個体 1% 跨ぎ 2.01-2.68 ms(**D-48**=定常でしか満たさない) | 同 :26 / `PENDING.md` D-48 |
| P7 | p_notice イベント演算 0.26 MOPS/イベント・顕著イベント上限 200/tick | — | 同 :27 |
| M1 | 個体状態 ≤30 KB/体(40 万体 ≈ 12 GB) | 現 **127 B/体**(+計画実行層 2 B = 129 B) | 同 :33 / `docs/design/v2-plan-executor-design.md` §2 |
| M2 | 位置・運動・身体 ≤**128 B/体** | 位置欄の現在値 = `cell 4 + node 4 + band 1 + xy 8 + path_next 4 + target_node 4` = **25 B/体** | 同 :34 / `src/shibuya/agents/state.py:274-286` |
| M8 | RSS 総額 ≤**24 GB**/ラン | **1.530 GB**(c7-day-4・390,067 体) | 同 :40 / `c7_accept.md` |
| M10 | 可視性テーブル ≤**512 MB**・前計算 ≤5 分/ジオメトリ版 | W8 出力 **5.87 MB** | 同 :42 / `W8.header.json` |
| M12 | p_notice 用 2 B/体 + invocation distance 2 B/体 | `invocation_distance` uint16 実装済 | 同 :44 |
| S1 | 恒久記録 ≤**5 GB**/シミュ日 | **0.175 GB**(187,902,222 B) | 同 :70 / `c7_accept.md` |
| W1 | 壁時計 ≤**24 h**/シミュ日 | **9.167 h** | `c7_accept.md` |
| L4 | LLM 呼 ≤400 万/日・平均 10 呼/体/日 が制御目標 | **2,706,593 呼**(6.939 呼/体/日) | 同 |
| L2 | ablation 予約枠=総 GPU 時間の 20%(分母=W1 24 h → 4.8 h・D-47 で仮) | AB7c 3 ラン通算 5.32 h で超過(D-77 #1) | `PENDING.md` D-47・D-77 |

**セル内位置を持つ場合に増える量の「見積りの材料」(既存文書の数字のみ・親が組み立てる)**

- 体数 = **390,067**(W16 の結果。40 万は目標でなく結果=D-20)。換算: 1 B/体 = 0.39 MB・
  2 B/体 = 0.78 MB(`v2-plan-executor-design.md` §2 が実際に使った換算)・4 B/体 = 1.56 MB・
  8 B/体 = 3.12 MB。M2 の残枠は 128 − 25 = 103 B/体(位置欄以外も M2 の内数である点は要確認)。
- 群衆物理設計書 §2 の M 行見積り:「40 万体 ×(**位置 2 + 速度 2 + 半径 1**)× 4 B ≈ **8 MB** + 格子」
  (`docs/design/v2-crowd-physics.md` §2)。M8 24 GB に対し 0.03%。
- CFSM の計算量実測(engine_spike): 社会力型・2 m 格子・dt 0.5 s・**40 万体で 0.028 s/step =
  CPU 1.34 h/シミュ日**・**LOD 12% で 0.62 h**・**格子構築が支配**(0.021 / 0.028 s)
  (`docs/design/v2-crowd-physics.md` 冒頭・U15-2)。「GPU 換算 6 分」の根拠は粒子ベンチ由来で
  **推測に降格済み**(同 U15-2 注記)。
- 毎 tick 走査の現状: `world.compute_density`(`np.bincount` 1 本)・`density_stage`・
  `open_count_per_cell` が毎 tick 全体走査(`src/shibuya/engine/resolve.py:800-810`)。
- 近接の走査は **呼ごと**(起床した体 1 体につき 1 回)。C7 の性能修正前は 1 呼 17 ms・
  llm 位相 46 s/tick だった(セル人口 1.4 万・1 呼あたり 13,663 反復)
  (`src/shibuya/perception/renderer.py:1121-1130`)。呼数の実測は 2,706,593 呼/日。
- 可視性の増分: T2 を R50 m → R100 m にすると 35 MB → 140 MB(決定台帳 R3-5 行)。
  **動的遮蔽(人・車)は Phase 2 に入れず後続・P4 宣言つき**(同)。

---

## §5 候補となる決定項(親がアジェンダにする種)

> **すべて「候補」**。値の当否・優先順位は書かない。

| # | 何を決めるか | いまの値と出所 | 触れる予算・決定項 | 先行リサーチの有無 |
|---|---|---|---|---|
| 1 | **セル内位置の表現**(連続 xy / サブセル格子 / ノード量子のまま) | `xy` はノード座標で毎 tick 上書き(`resolve.py:805`)・ノード 3,499・セル内ノード中央値 5・平均辺長 37.8 m | M2 128 B/体・P2・P6・決定論(checkpoint ハッシュ)・T2 代替 | U15-2/-3(Warp HashGrid・dt 収束)/ 知覚契約 §5「2 解像度」 |
| 2 | **歩行可能面積の実測化** | 本番 = `max(街路点 × 6.25, 1500)`・中央値 4,206 m²・床張り付き 11.5% [再計算]。第177 / R-8 の「100 m×0.15」は合成と床の値 | 密度段階 `DENSITY_STAGE_EDGES`・B4・LOS・Fruin 境界・U15-4 LOD 閾値 | **R-8 ①**(PLATEAU フットプリント + OSM 幅員)= 未着手 |
| 3 | **店舗床面積と 1 席面積** | 既定 80 m²・カテゴリ別表・2 / 4 m²(`crowd.py:66-84`) | `can_admit`・待ち行列・`DWELL_MAX_TICKS` 30・D-52(廃棄が帯の外) | **R-8 ②③** = 未着手 |
| 4 | **ホーム・改札・階段の実効容量** | 改札 56 人/台/分・エスカレーター 95.3 / 107.8 は取得済。**ホーム滞留容量は空欄** | U15-5 段階3・運用設計書 §2.6(混雑率上限)・E10(降車セル round-robin) | **R-8 ④** = 空欄 |
| 5 | **目印オブジェクトの導入形**(POI cat 拡張 / 新レイヤ / OSM 再取得) | landmark 56 + attraction 12 は W6 に在り B2 地物に描画済(最大 4 件)。artwork / memorial は未取得。街路地物 2,009 要素は未取り込み | 決定台帳「affordance 由来」行・W6 の版・W8 再生成(前計算 ≤5 分)・ライセンス台帳の行追加 | 待ち合わせの実証値 = **取得不能候補**(`v2-schedule-and-research-plan-2026-09.md` §2-2) |
| 6 | **「近づく / 見る」の affordance の形**(対象 = 人 / 物 / 場所のどれを許すか) | `parse_target` は自由文を全部 ITEM_CATEGORY に落とす・EVENT は出ない(`contract.py:757-790`) | 行動語彙上限 24(D-6・v2 で 25 = 1 超過)・`TargetKind`・`ResultCode`・テンプレ凍結 SHA | D-71 report §4(`approach` / `visual_inspection`)・**R-6** affordance grounding = **未一次確認** |
| 7 | **`TARGET_HINTS` を持つか**(対象の損失 17 行) | 段0 辞書が帰宅・探索・通勤の目的地を捨て、エンジンが対象を決めている(`v2-synonym-policy-v0.md:12, 67, 73`) | 分業の線(意思 = LLM・帰結 = エンジン)・段0 辞書の版(D-73) | D-73 の決定済み分(辞書を語彙政策として扱う) |
| 8 | **会話・傍受が届く範囲の幾何**(距離減衰 + 遮蔽の事前計算) | `d_talk ≈ 1 m` は**同セルで代理**(`conversation.py:24-26`)・傍受は可聴 r ≈ 2 m・会話半径は密度に ×0.42 | M10 512 MB・P4(前計算の逐次ループ宣言)・ablation ④(ΔSNR −3/−5)・会話成立率 | 決定台帳 R3-7 行・`v2-density-hearing-verification.md` |
| 9 | **近接入替(PROXIMITY_SWAP)を起床候補に出すか** | 列・不応期 15 分は在るが候補に出す過程が未実装 = no-op(**D-49**) | L4 呼数(知覚契約 §6 が「**最大の暴発源**」と名指し)・ablation ③(±50%) | 知覚契約 §6 不応期表(GATSim 由来の expedient) |
| 10 | **注意ゲートの較正**(D-59 の (b)) | 広告ゼロで 購入 −1.0〜−1.3 pp・帰無の 6〜8 倍 | AD1(第3封印行 S3)・段1 p_see 0.14-0.79・holdout | 広告答申 `v2-ad-information-research.md` |
| 11 | **群衆物理の段階**(U15-4 LOD の閾値と切替・dt・非物理領域のメゾ所要時間) | LOS C 相当 0.43〜0.72 人/m² 超 + 駅構内 + 横断待ち。実測 12% で 0.62 h/日 | P1 50 ms/フレーム・P2・M(位置2 + 速度2 + 半径1)× 4 B ≈ 8 MB・P4 | U15-1〜8 は決定済だが **R-7 の空欄 10 件が未解消** |
| 12 | **DECK/UG の扱い**(層跨ぎ 51 辺・UG に建物ラスタなし・DECK 眼高 = GL) | `W8.header.json` expedients・`W1.header.json` `interband_links = 51` | 可視性 M10・移動の到達性・E10(構内経路は第2陣)・W11 の ×1.3 | W11 駅構内グラフ(ノード 60 / 辺 57)は既存・PLATEAU ubld 未使用 |
| 13 | **移動速度の物差し**(1 tick = 1 ノードを何に置き換えるか) | 実資産で ≒ 2.3 km/h [再計算]。頭注が「U15 で置き換わる = C2 の暫定」と宣言(`world/graph.py:20-23`) | P2・在圏の物差し(`tools/c7/presence_yardstick.py` 6 指標)・W17 計画との整合 | U15-5 段階2(自由速度 Weidmann 1.34 m/s・年齢分布 1.00〜1.60) |
| 14 | **第2陣の holdout 候補と事前登録** | C7 の holdout は KDDI 形状 5 指標 H1〜H5(D-40)・開封規律 D-43。**第2陣 holdout は未定**。C9 の出口ゲート案 = 「待ち合わせ成立 / 会話 ≫ 410/日」(`v2-schedule-and-research-plan-2026-09.md:40`) | 事前登録 v1.2(3 seed)・E-C7-5 開封規律・S4 の「第2陣 holdout(事前登録)」 | 層2 検収が開封記録の上書き問題 (A) を指摘済(`accept_c7-day-4/layer2_review.md`) |
| 15 | **5 エリア写像の昇格(D-41)を C9 でやるか** | `area_axes_v0.json` は expedient・SCJ 214 件がリポに無い・`fit_note` に「当てはめ残差であって独立検定ではない」と明記 | E-C7-2・H1 / H4 の照合値・holdout 開封 | `v2-area-boundary-definition.md` §3-2 / `v2-area-boundary-map-reading.md` |

---

## §6 空欄(読めなかった・見つからなかったもの)

1. **SCJ 施設 214 件のデータ本体**がリポに無い(D-41 昇格条件 ②)。属性一致率 ≥90% は測れない。
2. **ホーム滞留の容量**(R-8 ④)。改札・エスカレーター・階段は値があるがホームは空欄。
3. **R-7 の 10 件**(Weidmann 原典・Burstedde 2001・Hughes 2002・Menge・HyPedSim・RiMEA 版数と
   ケース数・鉄道総研 2016 の実測歩行速度・Karmakharm の歩行者 GPU・データ駆動系一次資料・
   スクランブルの公的信号現示・運輸政策研究 表―1 の単位)。Web 禁止のため本調査でも未確認。
4. **PLATEAU tran の幅員・車線数**: 中心 4 タイルの実査で `width` / `numberOfLanes` /
   `TrafficVolumeAttribute` が **0 件**(`docs/data-license-ledger.md:23`)。フル zip 30 メッシュ側は
   未実査。**LOD3 歩道面 5,782** が歩行可能面積の材料になるかは未検証。
5. **街路地物 2,009 要素**(横断歩道 612 ほか)が W6/W8 へ入っていない理由の明文化を見つけられなかった。
   世界カタログ写像(W18)の入力として台帳には載っている。
6. **P2 の 40 万体行**が予算表に無い(受入表が「親判断」と印字)。C9 で物理を足すときの物差しが未定義。
7. **D-71 上位 10 語の判定**(食事 = 採用 / 近づく・見る・持つ・取る・避雨 → C9)は**承認待ち**で、
   動的検査 ①③④ の値は空欄(report §6)。
8. `w2_blocks.parquet`(街区 1,227・`place_ids` 列つき)を**エンジンが読む箇所を見つけられなかった**
   = 死蔵の候補。知覚契約 §5 の「粒度の第2候補 = 100 m 格子 ∩ 街区」はこの資産を前提にしている。
9. 決定台帳の affordance 行が挙げる **`PARTNER_NO_SHOW` は `ResultCode`(現 20 値)にまだ無い**
   (`src/shibuya/agents/state.py:128-153`)。
10. **C9 の予算 delta 案**(セル内位置・群衆物理を入れたときの P2/M2 の新しい行)は、どの設計書にも
    まだ書かれていない。S2 の出口ゲートに「予算 delta」とあるだけ。
