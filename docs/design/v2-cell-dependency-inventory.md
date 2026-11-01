# セル依存の全リスト(指示書 09-30 §1-3「最初にやること」)

> 作成: 実行役サブ(Opus 5.5)・2026-09-30・**読むだけの調査**(コード・資産・テストは変更していない)。親の検収前の草稿。
> 目的: 「何でも兼ねる 100 m 升目」としてのセルを 4 つの役割(① 近傍の索引=細かい格子 2〜5 m / ② 環境の場=場ごとのラスタ / ③ 名前のある場所=地名帳 / ④ 照合の区域=データ側の区域・テープから事後集計)に分ける設計ラウンドの材料。
> 対象: `src/shibuya/` 全層・`tools/`・設計書 4 本(知覚契約・行動契約・世界データ構築仕様・予算宣言)・`tests/`・世界資産(`data/world/v2/`)。
> 表記: 「事実」はコード・資産・記録で確かめたこと。「推測」「案」はそう書く。§5 の段階案は**未リサーチ(expedient)**。

---

## 0. 前提の事実(セルとは何か・いまの既定)

- **セル = `place_id` = 100 m 格子 (ix, iy) × 層 (UG/GL/DECK)**。実資産 520 個(GL 453・DECK 39・UG 28)。一辺 `CELL_SIZE_M = 100.0`(`src/shibuya/world/assets.py:84`)・格子原点 (0,0)・`floor(x/100)`(同 `:383-384`)。ID の文字列は `g{ix}_{iy}_{band}`(`src/shibuya/build/geo/common.py:114-120`)。
- 体の欄 `registry.cell`(int32・`-1`=場外)(`src/shibuya/agents/state.py:505`)。node 幾何では `cell = node_cell[node]`(`src/shibuya/engine/resolve.py:1447`)、edge 幾何では「近い方の端点」のセル(`src/shibuya/engine/geometry.py:370-398`)。
- 世界の状態 `world.cells`(density・density_stage・noise_stage・open_count・b4_hash)は**セル単位の SoA**(`src/shibuya/world/state.py:120-131`)。
- 既定 checkpoint の腕(CLI 既定): 語彙 v3・幾何 node・活動層 on・候補の解決 candidates・意図層 on・世界過程 on・会話 on・2 人会話。**既定 off**: memory・store_memory・relations(→同席・知人出現の起床・招待の重み)・familiarity・3 人会話・classical 方策・在圏 journal(`occupancy_every=0`)。
- **重要な事実(検算 §3 と関係)**: 実距離の会話判定(C9b G7)が立つのは `attention_on = (geometry == "edge") and (vocab_version == "v2")` のときだけ(`src/shibuya/engine/run.py:2103`)。**既定の語彙 v3 に `--geometry edge` を足しても実距離にならない**(同セル代理のまま)。指示書 §0-5 の 2 番「まず既存の `--geometry edge` の腕で」は、この条件をそのまま使うと v3 では効かない。

---

## 1. 依存の表(分類ごと)

凡例: 置き換え先 = ①近傍の索引 / ②環境の場 / ③地名帳 / ④照合の区域 / その他 / 不要。checkpoint = 既定 checkpoint(v3・node)への影響。テスト = そのキーワードを含むテストファイル数(カッコ内はそのファイル内のテスト関数の総数=**上限**。キーワードに直接触れる関数だけの数ではない)。全テスト関数は 2,746・うちセル/セルの語を含むファイルは 178 中 137。

### 1-A 知覚・起床(指示書の列挙)

| # | 分類 | ファイル:行(代表) | セルを何に使っているか | 置き換え先 | checkpoint | 影響するテスト | 難しさ |
|---|---|---|---|---|---|---|---|
| A1 | 知覚 B2/B4/B4b の共有(prefix) | `perception/renderer.py:1306-1314`(ブロック組立)・`:1383-1447`(`_b2` とキャッシュ鍵 `(cell, shown)`)・`:1725-1760`(`_b4`・鍵 `(cell, B4 欄ハッシュ)`)・`:2299-2331`(単一ランキングのセル池)・`perception/templates.py:148-163`(BLOCK_GROUP の `cell` 群・予算 250) | B2=セル代表点からの可視物・看板・ランドマーク・路面、B4=セル密度段(LOS)・騒音段・顕著行為、B4b=セルの行列・活動行。**同セル×5 分帯×種別で B0〜B4b がバイト一致**(規約⑧)。キャッシュ・prefix・dormant 抑止の三役 | ①(近傍)+②(場の値を本人の xy で読む)+③(「いまいる場所」の語)。共有は「同じ場所語・同じ時間帯」単位へ縮む | 動く | バイト一致/同セル系 31 ファイル(477)・perception 14 ファイル | 大: 知覚契約 §2.2/§2.4⑧/§2.5 の改訂が要る・B2 の文面資産 W15 がセル鍵 |
| A2 | B2 の可視物の資産 | `perception/renderer.py:715`(`w8_t1_cell.parquet`)・`:761-762`(W15 凍結文)・`world/assets.py:455-533`(`load_poi_own_cell_visibility`/`load_visible_pois_by_cell`) | 2.5 m 視点(239,028 点)の可視をセルへ集約した表を B2・選び手・意図に使う | ②(視点ごとの `w8_t1.parquet` は既にある=点単位で引ける)+③ | 動く | build_vis 2・build_lang 3 | 中: 点単位の T1 は資産に在る(`data/world/v2/w8_t1.parquet`)。W15 凍結文はセル ID の関数なので作り直しか廃止 |
| A3 | 変化検出の起床 (i) | `engine/change_detect.py:287-385`(`_cell_changes`・変化セルの在席者を起こす numba ループ `:102-122`)・`world/state.py:130`(`b4_hash`)・`engine/resolve.py:782-783` | セル B4 の描画欄のハッシュが変わったら、そのセルの全員を `CELL_BLOCK` で起こす | ①(周りの人数・近づいた出来事)+②(本人位置の場の値の段が跨いだか)=本人単位の安い信号 | 動く | change_detect/CELL_BLOCK/b4_hash 20 ファイル(310) | 大: P6 予算行(40 万体・≤2〜3 ms)の作り直し・起床の総量(L4)が変わる |
| A4 | 近接 top-k の同セル制限(B5 人物④) | `perception/renderer.py:1918-2001`(`_nearby_items`: 候補=`cell_start..cell_end` の同セル在席者)・`:2543-2556`(`_cell_index` の CSR)・`:1970-1995`(会話相手・知人・焦点も「同セルなら」載せる) | 近接 k 人の候補集合をセル在席者に限る。セル境界の 1 m 隣は候補外、同セルなら 100 m 先も候補 | ①(半径 r の近傍探索・密度で k 逓減は据え置き) | 動く | nearby 系 11 ファイル(165) | 中: 索引を差し替えれば描画ロジックは流用可。node 幾何の重なり(距離 0)の問題は残る |
| A5 | 顕著行為の到達(p_notice)と「知覚済み」 | `engine/processes/salient.py:13-15`(80 m を**同一セル+4 近傍**で代用)・`:262`(`_mark_seen` はセル単位)・`:391`(`_candidates`)・`perception/p_notice.py:14,86`(打ち切り 80 m=±1 リング 9 セル) | 事象の座標=セル代表ノード。到達候補=十字 5 セル。B4 に載ったセルの全員を「知覚済み」(通報の前提)に | ①(80 m 半径)+事象の実座標 | 動く | salient/p_notice 15 ファイル(281) | 中: 距離関数(Hill 型)は既にある。候補を近傍索引に替える |
| A6 | 知人出現の起床(8b) | `engine/relations.py:855-880`(`_same_cell_hits`)・`:934-960`(`acquaintance_candidates`: 前 tick と違うセルに知人が**同セルに現れた**) | 知人の出現=同セルへの出入り。距離は見ない | ①(半径 r に入った) | 動かない(relations 既定 off) | copresent/acquaint 6 ファイル(93) | 小: 配列演算の置換。ただし出入りの定義(r とヒステリシス)を決める要 |
| A7 | 起床のクラス名 | `agents/state.py:295,316`(`WakeCondition.CELL_BLOCK`・許容遅延 30 分)・`core/types.py:106-131`(`EventClass.CELL`)・`engine/arbiter.py:110-115`(T_max 60・縮退対象) | 「場所の変化」の級の名と優先順位 | その他(名前だけ。意味を「本人の周りの変化」へ) | 動かない(名の変更だけなら) | 多数(起床系) | 小 |
| A8 | 活動層の表示(B4b 活動行)・「あたり」 | `engine/activity.py:452-475`(`cell_rows`=同セル全員の活動文を B4b に 1 行)・`:29-30,75-76,134-151,402-418`(「あたり」=同層・Chebyshev ≤2 セル) | 近景の活動行の単位・近傍歩行の行き先 | A1 と同じ(近景)+③(「あたり」=地名帳の同じ層の近い場所)or ①(半径 m) | 動く | wander/cell_rows 9 ファイル(214) | 中 |

### 1-B 会話・同席・関係(指示書の列挙)

| # | 分類 | ファイル:行(代表) | セルを何に使っているか | 置き換え先 | checkpoint | 影響するテスト | 難しさ |
|---|---|---|---|---|---|---|---|
| B1 | 会話の成立条件(同セル代用) | `engine/resolve.py:2437-2454`(`talk_within_reach`: 既定は `ca == cb`・腕では**同セル かつ** ≤2 m)・`:2457-2476`(`_apply_talk`: 同セルでなければ `PARTNER_GONE`)・`engine/conversation.py:24-26,76,356-363`(開始ゲート `not_same_cell`) | 「距離 ≤ d_talk」をセル一致で代理(契約書は同一セル∧距離) | ①(距離 ≤2 m・層/階の一致は別の欄で) | 動く | same_cell/talk_within_reach 15 ファイル(296) | 中: 距離版は既に在る(腕)。v3 で立たない結線と、node 幾何の重なりの扱いが要る |
| B2 | 招待・返事待ち・相互指名 | `engine/run.py:1446-1453`(`_settle_pending_invites`)・`:3303-3350`(`register_pending`/`invite` に `same_cell`)・`engine/conversation.py:490-520`(返事待ちも同セル) | 被招待が答える時点の同セル検査 | ① | 動く | 同上に含む | 小〜中 |
| B3 | 3 人会話の参加 | `engine/run.py:3290-3300`(`conv.join` の前に `talk_within_reach`) | 会話中の相手に加わる条件 | ① | 動かない(既定は 2 人) | conversation 系に含む | 小 |
| B4 | 会話の離脱 | `engine/conversation.py:710-756,785-790`(`_left_cell`=開始セルと違えば `left_cell` で終了)・`engine/run.py:3364-3370`(腕では 3 m の実距離) | 離脱=セルを出た | ①(3 m のヒステリシス=既存の腕) | 動く | 同上 | 小 |
| B5 | 会話相手の既定(名指しなし) | `engine/commit.py:460-508`(`talk_partners`: 名指しは同セルなら採用)・`:510-560`(`pair_partners`: 同セル最小 id/撹拌順)・`engine/relations.py:773-830`(`choose_talk_partners`: 同セルの辺の相手+2 m 内の知人) | 「話しかける相手」の候補集合=同セルの起床中の体 | ①(半径 r の起床中の体) | 動く(pair_partners は既定経路) | conversation_invite・relations 系 | 中: 「誰に話しかけるか」の既定が半径で大きく変わる |
| B6 | 手伝い・放送の前提 | `llm/contract.py:264,270,307-308`(手伝い=同一セル)・`:447-451`(放送=当該セルの聴覚イベント)・行動契約書 表 l.25・l.38 | 契約の前提文 | ① | 不明(手伝い・放送のエンジン実装の有無は未確認=§6) | contract 系 | 小 |
| B7 | 傍受 | `agents/state.py:294,315`(`OVERHEARD` の級だけ)・`engine/change_detect.py:40`(「傍受は C2 では検出しない」)・`engine/wom.py:34,73`(非宛先・傍受は未実装) | **コードの依存は無い**(未実装)。知覚契約 §2.2 B5「傍受」と §3.7 聴覚(可聴 1-2.5 m を同セルで代理=`engine/commit.py:473`)が設計上セル前提 | ①(可聴半径) | 動かない | — | 小(設計だけ) |
| B8 | 同席(COPRESENT・Q91) | `engine/relations.py:137`(定義=同セル・2 m 内・連続 5 分)・`:889-930`(`copresent_step`) | 同セルかつ 2 m。node 幾何では同ノード=距離 0 で水増し(指示書 §1-2 追加 A) | ① | 動かない(既定 off) | copresent 系 6 ファイル(93) | 小 |
| B9 | 初期関係網(C10)の共在 | `engine/relations.py:194-270`(`slot_cells`/共在の分=W17 の**同じセル・同じ 15 分枠**)・`:353-400`(`initial_edges`: 組織/学校**セル**で組を作る) | 同僚・同級生の「共在時間」を「同じセルに居た時間」で数える | ③(同じ建物・同じ組織)or その他(W16 の組織 ID) | 動かない(relations 既定 off) | initial_edges/slot_cells 2 ファイル(34) | 中: W16/W17 がセルしか持たない(D2 と連動) |
| B10 | 箱の中の社会(オフィス・学校・家) | 現状は職場/自宅に居る体=そのセルの代表ノードに集まる(`engine/resolve.py:505-508`・`:2785`)→同セルなので会話できる | 屋内に位置が無いことをセルが隠している | その他(指示書 §3-2 F=空間を持たない組織化された部屋) | 動く | — | 大: 新しい仕組み(§2 の 1 番) |

### 1-C 行き先・行為の成立(指示書の列挙+見つけた別名)

| # | 分類 | ファイル:行(代表) | セルを何に使っているか | 置き換え先 | checkpoint | 影響するテスト | 難しさ |
|---|---|---|---|---|---|---|---|
| C1 | LLM の対象欄「セル○○」とパーサ | `perception/templates.py:678`(B2 場所「現在地はセル{place_id}({band})です。」)・`:310,321,526`(v1/v2 の「対象: <セルID …>」)・`llm/contract.py:129-140`(`TargetKind.CELL`)・`:929-946`(`C-0117`/`g<ix>_<iy>_<band>`/「セル」接頭辞の正規表現)・`:1059-1130`(`parse_target`) | 行き先を格子 ID で言わせ・読む。第271 で「セルg-1_0_GL」の写し(移動 10,751 呼)を救済した経緯 | ③(地名帳の語・層を重ねた「いまいる場所」) | 動く | 行き先系 23 ファイル(479) | 大: 地名帳の構築・LLM の自由記述照合(指示書 §1-5)が前提 |
| C2 | 行き先のセル → 代表ノード | `engine/resolve.py:1607-1640`(`_apply_move`: `dest_node = cell_rep_node[tgt]`)・`world/assets.py:246`(`cell_rep_node`)・`build/geo/w2_cells.py:17`(代表=セル内ノード重心に最も近いノード) | セルへの移動=代表ノードへの移動 | ③(地名帳の点・範囲なら範囲内の一点・施設なら入口)+ナビメッシュ | 動く | 同上 | 中 |
| C3 | カテゴリ語の近傍探索・移動の上書き | `engine/poi_target.py:31-48,197-203`(`MOVE_SEARCH_RADIUS_CELLS=5`・`cell_dist` の昇順)・`engine/commit.py:647-660`(`move_dest`=セル) | 「近くのコンビニ」をセル距離表の近い 5 セルで探す | ①/その他(経路コストの問い合わせ・半径 m) | 動く | MOVE_SEARCH 系に含む・cell_dist 4 ファイル(42) | 中 |
| C4 | 購入・食事・並ぶの成立=「店のセルに居る」 | `engine/commit.py:566-590`(`_poi_in_cell`)・`engine/poi_target.py:17-24,376-380,423-526`(候補=現在セルの POI・名指しが無ければ `named_out_of_cell`)・`engine/intent.py:191-203`(着いた=対象のセルに居る)・`engine/resolve.py:2258-2280`(食事の前提) | 「店に着いた」をセル一致で判定。店の入口・店内の区別なし | ③(施設=入口/L1 の箱の中)+① | 動く | intent 38 ファイル(517)・_poi_in_cell 2(42) | 大: 「店の中」という状態の定義(L1 箱)が要る |
| C5 | 権限行動(開店・補充・収集)の同セル | `engine/processes/opening.py:160-170,190`・`engine/processes/goods_flow.py:190-211` | 担当従業者が POI と同セル | ③(同じ建物/入口の近く) | 動く | goods_flow/opening に含む | 小〜中 |
| C6 | 乗車・降車・ホーム | `engine/resolve.py:1796-1805`(`_platform_table`: ホーム=セル・代表ノード)・`:1852-1893`(乗車=ホームのセルに居る)・`:2109-2114,2775-2787`(降車・到着=ホームのセルの代表ノードへ)・`engine/processes/rail.py:272-329`(`line_cell`/`platform_cell`) | 駅のホーム=セル | ③(駅の地名帳)+その他(形のない駅の縦の接続=指示書 §1-7 E) | 動く | platform_cell 系 9 ファイル(137) | 中〜大: 3 次元の段(縦の接続)と一緒に作る |
| C7 | 就寝の場所と容量 | `engine/commit.py:158-159`(`SLEEP_SLOTS_PER_CELL=200`・expedient)・`:316-337`・`engine/resolve.py:2568-2584`(寝床=自宅セルに居る)・`:632-730`(計画就寝)・`engine/processes/civic.py:240-292`(`hotel_of_cell`=セルの先頭ホテルへ寄せる) | 自宅/宿=セル。容量=セルあたり 200 | ③(住戸/建物=L1・ホテル POI 単位) | 動く | SLEEP_SLOTS/hotel 9 ファイル(208) | 中: 住居の単位(W16 が建物床面積按分でセルに配っている)と連動 |
| C8 | 拠点(自宅・職場・学校)の型 | `agents/population.py:109-111,154-166`・`agents/schedule.py:105-144`・`engine/run.py:1346-1407`(母集団のセル索引の検査と写し)・`llm/undefined.py:32-33,216-219,414`(「帰る」→ 自宅セルはエンジンが解決) | 拠点がセル索引 | ③(建物/POI/組織 ID) | 動く | home_cell 等 23 ファイル(423) | 大: W16/W17 資産の作り直し(D2) |
| C9 | 意図層 | `engine/intent.py:5-18,133-203`(セル外の対象を意図に・`CELL_BLOCK` を落とす) | 「セル外」という区分 | ③(地名帳の場所外/視界外) | 動く | intent 38 ファイル(517 の一部) | 中 |
| C10 | 口コミのチェーン店選び・店の記憶の到達判定 | `engine/wom.py:22-23,196-272`(話し手のセルに近い順=`cell_dist`)・`engine/store_choice.py:121-162`(`cell_dist / 歩速 ≤ 次の予定まで`) | 距離をセル間距離表で | その他(経路コストの問い合わせ) | 動かない(store_memory 既定 off) | wom 3(36) | 小 |
| C11 | 選び手の距離 | `engine/chooser.py:15-16,78`(`cell_dist`・同セルは距離 0)・`engine/poi_target.py:526` | 候補の距離 | その他(本人 xy → 入口の経路長) | 動く(既定 nearest) | cell_dist 4(42) | 中 |

### 1-D 環境・密度(指示書の列挙)

| # | 分類 | ファイル:行(代表) | セルを何に使っているか | 置き換え先 | checkpoint | 影響するテスト | 難しさ |
|---|---|---|---|---|---|---|---|
| D1 | 密度(在席数・LOS 段・減速) | `world/state.py:228-232`(`compute_density`=セル bincount)・`:67-73`(段の境界=人/セル)・`engine/geometry.py:173-204,263-274`(edge 腕: セル別歩行可能面積で人/m²・Kladek 減速はセル単位)・`perception/renderer.py:26,628,841-859`(分母=街路点数×6.25 m² の expedient) | 混雑の単位 | ①(近傍の局所密度)+②(混雑の場) | 動く | density/walkable 27 ファイル(424) | 中〜大: 物理(D 層)と同時。LOS の語は据え置き可 |
| D2 | 歩行可能面積 | `world/assets.py:128-160`(`load_walkable_area_m2`)・`tools/build_geo/walkable_area.py:330-445,813-856`(PLATEAU/OSM をセル境界でクリップ) | 密度の分母をセルで集計 | ②(面そのもの=ナビメッシュ) | 動かない(既定 legacy) | 含む | 小(ナビメッシュが置き換える) |
| D3 | 騒音 | `world/assets.py:534-586`(`_noise_stage_per_cell`=W10 街路点 356,732 点の最頻値)・`world/state.py:403-425`(`noise_stage_for_tick`)・`engine/processes/traffic.py:20-26,78-149`(`cell_vehicles`=辺を始点セルへ集約・騒音の動的項の素) | 場をセルの最頻値へ潰す | ②(W10 の点・ラスタはそのまま在る) | 動く | noise/shade 15 ファイル(278) | 小: 元の場は点単位で在る |
| D4 | 日陰・暑さ | `engine/processes/environment.py:27-29,155-265`(セル代表点に最も近い街路点 1 点の日陰ビット→体のセルの値) | 同上 | ②(W9 の影の面を本人 xy で) | 動く | 同上 | 小 |
| D5 | 流れ(B4 の流れの語) | `engine/processes/crowd.py:142-166,265-343`(`flow`/`flow_dir8` がセル単位) | 流れの向きの集約 | ①/② | 動く | crowd に含む | 小〜中 |
| D6 | 視線表 | `build/vis/w8_visibility.py:649-670`(T2=セル×セルの float16 行列 `w8_t2.npy`)・予算 M10 | セル間の見通し | ②(点単位 T1) | 動かない(**T2 は実行時に読まれていない**=`src/` の grep `w8_t2` がビルド段だけ) | build_vis 2 | 不要になる可能性 |
| D7 | 距離表 | `build/geo/w3_distances.py:4-12,188-200`(`w3_cell_dist.npy` uint16・代表ノード間の最短経路)・`world/assets.py:241` | 近さの一次近似(C3/C10/C11 が読む) | その他(経路探索の費用を実測=指示書 §1-4) | 動く | cell_dist 4(42) | 中 |

### 1-E 計器・照合・記録(指示書の列挙)

| # | 分類 | ファイル:行(代表) | セルを何に使っているか | 置き換え先 | checkpoint | 影響するテスト | 難しさ |
|---|---|---|---|---|---|---|---|
| E1 | 群/規範の計器(D-107) | `engine/norm_meter.py:9,23-26,86-97,136-140,298-309`(同行=**同セル**∧同じ行き先ノード∧2 m・駅=出口セル/ホームセル) | 同行の組の列挙鍵・場所種別 | ①(組の列挙は近傍索引)+③(駅の範囲) | 動かない(読むだけの計器) | norm_meter 1 | 小 |
| E2 | 5 エリアの写像 | `tools/c7/c7lib.py:30,186-340`(セル格子中心 → 5 エリア・`area_axes_v0.json`)・`:456-468`(個体の (cell, kind) → エリア×属性)・`tools/c7/occupancy_series.py:12,57-101` | KDDI の 5 エリアへの割付をセル単位で | ④(本人 xy を直接エリアのポリゴンへ) | 動かない(事後集計) | c7 7 ファイル・AreaMap 4(45) | 小: xy を記録すれば写像は点で引ける |
| E3 | 在圏 journal | `engine/run.py:3462-3469,3908-3917`(`cell_counts`=セル別在席・`kind_cell_counts`=種別×セル・正時など `occupancy_every` ごと) | 照合の単位がセル | ④(本人位置のテープから事後集計=指示書 §5-3) | 動かない(既定 0) | occupancy 11 ファイル(185) | 中: 位置テープの設計(バイト予算)が要る |
| E4 | テープ | `engine/tape.py:96-105`(列に位置もセルも無い)・`tools/vocab/registry_from_tape.py:17-24,63-92`(セル ID を B2 ブロックの文面から**復元**) | テープは**セル列を持たない**。B2 の文面にセル ID が入っているのを計器が当てにしている | ④+③(位置と地名帳 ID を列で持つ) | 動かない | vocab 3 | 小〜中 |
| E5 | 退出・在圏の計器(9a) | `engine/presence.py:747-809,968-973`(出口セル・ホームセルの時別在圏) | 駅の範囲=セル | ③(駅・出口の地名帳) | 動かない(計器)・一部動く(降車セルの引き先) | platform 系に含む | 小 |
| E6 | 記憶の「どこで」 | `agents/state.py:637,655-660`(`mem_cell`・場所の符号 `−(cell+2)`)・`engine/memory.py:14-15,354-376,438-440,657-709`(想起の一致=同じセル)・`perception/renderer.py:160-228`(B5 の記憶文の場所=`place_ids[cell]`=格子 ID) | 記憶の場所・想起の手がかり | ③(地名帳の階層 ID=指示書 §1-5「記憶のどこでも同じ単位」) | 動かない(memory 既定 off) | mem_cell/place_thing 4(63) | 中: 記憶の作り直し(§3-2)と束ねる |
| E7 | 親しみの「場所」・看板の露出 | `engine/familiarity.py:12-13,33-38,107-112,230-300`(場所=セルに入った回・入った回×そのセルの看板) | 慣れの単位=セル | ③(地名帳の場所・道) | 動かない(familiarity 既定 off) | familiar 5(73) | 小 |
| E8 | 古典の腕 | `engine/classical.py:11,95,295-378`(見える飲食店=同セル or W8・同セルで食事中の人 ×1.2・駅=ホームのセル) | 周囲の条件をセルで | ①+③ | 動かない(既定 mock) | classical 8(145) | 小(ただし §0-3 の「公平な比較相手」に効く) |
| E9 | 艦隊の prefix キャッシュ(順序) | `llm/fleet.py:11-12,67,336-373,595-622`(`(cell, 5 分帯)` で束ねて隣り合わせに発射・同一 GPU 回避)・`engine/run.py:238,3123-3124`(`LLMCall(cell=…, time_bucket=tick//5)`)・`manifest/schema.py:251-285`(`cell_affinity`・M11 の `cell_tok`) | 同じ prefix の呼を近くに並べる鍵 | その他(並べる鍵を「種別→場所語」へ)。共有の実効は §4 | 不明(mock ランの結果が発射順に依存するかは未確認) | fleet 36 ファイル(591) | 小 |
| E10 | 予算・状態成長の宣言 | 予算宣言 P6(139 セル)・P7(±1 リング 9 セル)・M10(T1/T2 セル)・M11(セル依存 ≤250)・`core/growth.py:118-139,232-234`(`per_cell_bytes`)・`core/soa.py:55-81,230-232`(`Registry.for_cells`) | 予算の単位 | その他(行の書き直し)。`per_cell_bytes` の多くは実体が POI 側(economy)で名前だけ | 動かない | test_budget_table ほか | 小(文書)〜中(P6 は再実測) |

### 1-F 世界過程・世界資産・母集団

| # | 分類 | ファイル:行(代表) | セルを何に使っているか | 置き換え先 | checkpoint | 影響するテスト | 難しさ |
|---|---|---|---|---|---|---|---|
| F1 | 宅配 | `engine/processes/logistics.py:10-18,54-55,81-120`(bbox 面積=セル数×1 万 m²・世帯数でセルへ配分)・`engine/processes/runner.py:230-242` | 配達先の単位 | ③(建物)or ④(区域) | 動く | 世界過程 4(31) | 小 |
| F2 | バス停・道路占用 | `world/assets.py:966-1050`(`_bus_stop_cells`)・`logistics.py:14,176-198`(`blocked_cells`) | 停留所=セル | ③(停留所の点) | 動く | 同上 | 小 |
| F3 | 街路清掃 | `engine/processes/goods_flow.py:551-600`(ごみストック=セル・8 セル/tick 掃く) | 場の単位 | ②(ラスタ)or 街路区間 | 動く | 同上 | 小 |
| F4 | 収集ルート | `goods_flow.py:35,118-119,400-424`(セル順のルート) | 巡回順 | その他(経路) | 動く | goods_flow | 小 |
| F5 | 救急・報道・イベント | `engine/processes/civic.py:14-24,126-151,191-230`(出動=セル・報道=全セル・イベント=会場セル) | 事象の場所・到達範囲 | ①/③ | 動く | 含む | 小 |
| F6 | 鉄道到着・域外の出入り | `engine/resolve.py:2757-2803`(`rail_arrive`=ホームのセルの代表ノード)・`build/field/w12_external_nodes.py:379-470`(方面ノード→ `attached_place_ids`) | 出入り口=セル | ③(駅・出口・ゲートの点) | 動く | platform 系 | 中 |
| F7 | W2 セル生成 | `build/geo/w2_cells.py:1-151`(`w2_cells.parquet`・`w2_blocks.parquet` 街区 1,242→帰属セル) | すべての place_id の源 | ①〜④へ分解。街区は地名帳の (a) 候補 | 動く | build_geo 3 | 大(全体の土台) |
| F8 | W5/W6/W11 の写像 | `build/geo/w5_entrances.py:9-13,133-147`・`w6_poi_org.py:21-22,123-145,277`(POI/組織のセル)・`w11_station_exits.py:6-7,202-248`(駅→出口→セル) | 入口・POI・出口の所属セル | ③(入口・POI・出口は点として既に在る) | 動く | build_geo に含む | 小〜中 |
| F9 | W15 B2 セル静的文 | `build/lang/w15_cell_static.py:1-73`(520 行・LLM 生成・凍結) | B2 の文面資産 | ③(地名帳の語の静的文へ作り直し)or 廃止 | 動く | build_lang 3 | 中: LLM 生成の段=GPU 要・§2-6 の「先に聞く」 |
| F10 | W16 母集団 | `build/pop/w16_population.py:6-11,124,164,282-311`(自宅=町丁目→建物床面積でセルへ・勤務=組織/駅の格子セル・学校セル) | 拠点がセル索引 | ③(建物/組織/学校 POI の ID) | 動く | build_pop 2・sensitivity | 大: 母集団の再構築(§2-6「先に聞く」) |
| F11 | W17 週次表 | `build/sched/w17_schedule.py:132-133,356-414`・`agents/weekly.py:16,130-131,205-331`(`target_cell`=自宅/職場/学校だけ解決・他は −1) | 行き先がセル | ③ | 動く | build_sched 5・w17 2 | 中: 解決済みは拠点だけなので写し替えで足りる可能性(推測) |
| F12 | W20 検収パック・W18 被覆 | `build/audit/w20_acceptance_pack.py:8-11,140-167`・`w18_coverage.py:73-74` | 図と被覆の単位 | その他 | 動かない | build_audit 1 | 小 |
| F13 | 合成世界 | `world/assets.py:24-31,642-700`(1 セル=1 ノードの 4 近傍格子・n_cells 139) | CI の小世界の構造そのもの | その他(合成ナビメッシュ) | 動かない(実資産の checkpoint には無関係)・テストは全面 | `World.synthetic(n_cells` 49 ファイル(756) | 中: テスト基盤の作り直し |
| F14 | 型・ID | `core/types.py:34-151`(`CellId`・`INVALID_CELL_ID`)・`world/graph.py:41-94`(`cell_of`) | 型 | その他 | 動かない | core 4 | 小 |

### 1-G 研究ツール(tools/)

| # | 分類 | ファイル | セルを何に使っているか | 置き換え先 | 難しさ |
|---|---|---|---|---|---|
| G1 | C7 受入・在圏の物差し・属性腕 | `tools/c7/c7lib.py`・`occupancy_series.py`・`attr_arms.py`・`presence_yardstick.py`・`prereg_v13.py` | E2/E3 のセル写像 | ④ | 小 |
| G2 | C6/C8 | `tools/c6/run_hash.py:33-88`(`--cells`)・`ablation1_fixed_vs_ranking.py:51-133`(`tokens_cell_mean`)・`tools/c8/sensitivity.py:86,230-290`(町丁目→セル按分の感度) | 合成セル数・セル群の tok・W16 の按分 | その他 | 小 |
| G3 | 語彙・テープ | `tools/vocab/registry_from_tape.py`・`adjudicate.py` | B2 文面からセル ID を復元 | ③/④ | 小 |
| G4 | 品質プローブ | `tools/quality_probe_v0/build_probes.py`(60 箇所) | プローブ文にセル ID | ③ | 小(凍結プローブの版を分ける要) |
| G5 | ベンチ | `tools/bench_spikes/engine_tick_bench.py`(セル hash・セル順整列)・`crowd_physics_bench.py:32-106`(**既に細かい格子の近傍索引**=①の雛形) | — | ① | 小 |
| G6 | W17 多様性の物差し | `tools/w17/diversity_yardstick.py:76,192,266,715-737`((場所種別, cell) の相異数) | 場所の数え方 | ③ | 小 |
| G7 | 食事の錨 | `tools/hunger/build_hunger_anchors.py`(8 箇所) | 未精査(§6) | — | — |

### 1-H 誤検出(セルの語だが本件と無関係)

`core/budget.py:32-158`・`build/catalog_freeze.py:88-107`・`world/processes/constitution.py:185-245`・`tools/c8/c8lib.py:111-126`・`tools/c8/dashboard.py:333-343`・`build/sched/trial.py:221-241`(表のセル)/`agents/population.py:17,25`・`build/pop/w16_population.py:32`・`w16` の「年齢階級×性別セル」(層別の升)/`build/vis/w8_visibility.py:122-126,381`・`w9_shadow.py:160`(DEM・ビンの升)/`engine/scheduler.py:205-457`(`_cancelled`)。

### 1-I 分類ごとの件数(本表の行数)

| 区分 | 行数 |
|---|---|
| A 知覚・起床 | 8 |
| B 会話・同席・関係 | 10 |
| C 行き先・行為の成立 | 11 |
| D 環境・密度 | 7 |
| E 計器・照合・記録 | 10 |
| F 世界過程・資産・母集団 | 14 |
| G 研究ツール | 7 |
| **合計** | **67 行**(誤検出 1-H を除く) |

置き換え先の内訳(各行の最初に書いたもの 1 つで数えた): ① 近傍の索引 21・② 環境の場 6・③ 地名帳 22・④ 照合の区域 4・その他/不要 13・未精査 1(G7)。
checkpoint(A〜F の 60 行・G は研究ツールで対象外): 動く 37・動かない 21・不明 2(B6・E9)。

`src/shibuya/` のセル/セルの語の出現は 94 ファイル・約 3,000 箇所(grep `cell|セル` の行数・大小無視。1-H の誤検出を含む)。上位: renderer 261・assets 248・w16 140・run 133・poi_target 133・resolve 129・commit 108。

---

## 2. セルが無くなると成立しなくなる仕組み

1. **箱の中の会話(オフィス・学校・家)**: 職場/自宅に居る体は、いまはそのセルの代表ノードに集まっている(`engine/resolve.py:505-508`)ので同セル=会話できる。実距離にすると屋内に位置が無く、同僚・家族と話せない(指示書 §3-2 F の穴)。口コミ・関係辺の維持(Q91)・昼/飲み会の人流に効く。
2. **店・飲食店の「中に居る」**: 購入・食事・並ぶ・意図の到着はすべて「店のセルに居る」で判定(C4)。セルが無いと「店に着いた/店内に居る」状態が定義されない(L1 の箱か入口の近傍の定義が要る)。
3. **ホームで電車に乗る**: 乗車・降車・到着・ホームの待ち行列はホームのセルで判定(C6)。駅の縦の接続(形のない駅)を先に持たないと乗れなくなる。
4. **寝る**: 寝床=自宅セル・容量=セルあたり 200・ホテル=セルの先頭ホテル(C7)。住戸/建物の単位が要る。
5. **権限行動**: 開店・補充・収集は「担当者が POI と同セル」(C5)。
6. **行き先を言う**: LLM は B2 の「現在地はセルg…」を見て格子 ID で行き先を書き、エンジンは代表ノードへ歩かせる(C1・C2)。地名帳ができるまで行き先の語が無い。
7. **起床の半分(場所の変化)**: 起床 (i) はセル B4 のハッシュ変化でセルの全員を起こす(A3)。本人単位の信号に置き換えないと、場所の変化で誰も起きなくなる。
8. **知覚の共有(prefix・B2/B4 のキャッシュ・dormant 抑止)**: ハッシュ三役の鍵がセル(A1)。
9. **顕著行為の到達と通報の前提**: 候補=十字 5 セル・「知覚済み」=セル単位(A5)。
10. **初期関係網**: 同僚/同級生の共在=W17 の同じセル・同じ 15 分枠(B9)。
11. **母集団と週次表**: 拠点がセル索引(C8・F10・F11)。
12. **密度・混雑の語・減速・騒音・日陰の値**: いずれもセルの値を本人に配っている(D1〜D5)。場の値の読み口を本人の xy に替えれば済むものが多い(騒音・日陰の元の場は点単位で在る)。
13. **照合**: 5 エリアの写像と在圏 journal がセル単位(E2・E3)。テープに位置の列が無い(E4)ので、セルを外すと事後集計の素が無くなる。
14. **CI の合成世界**: 1 セル=1 ノードの格子(F13)。テストの 49 ファイルがこれで世界を作る。

---

## 3. 検算: 「同じ 100 m セル=会話できる・141 m 離れても会話でき、1 m 隣でもできない」

**結論: 既定(node 幾何・語彙 v3)ではコードのとおり。ただし 141 m は理論上の上限で、実資産では最大 133.65 m。**

- 会話の成立条件: `engine/resolve.py:2437-2454`(`talk_within_reach`)。既定 `by_distance=False` では `ok = (ca == cb) & (ca >= 0)` だけ=**同じセル索引なら距離を見ない**。`_apply_talk`(`:2457-2476`)が同セルでなければ `PARTNER_GONE`。開始ゲート `engine/conversation.py:356-363`(`not_same_cell`)・返事待ち `engine/run.py:1446-1453`・成立 `:3303-3350`・3 人会話 `:3290-3300`・離脱 `engine/conversation.py:785-790`(開始セルと違えば終了)も同じ。
- `by_distance=True` の腕(`attention_on`=edge 幾何 **かつ語彙 v2**・`engine/run.py:2103`)でも **「同セル かつ ≤2 m」**(`resolve.py:2449-2454`)。同セルを残した理由は「層を跨いだ 2 m を成立させないため」(`:2442`)。したがって**腕でも「1 m 隣でも別セルなら不成立」は残る**。
- セルの大きさ: 一辺 100 m(`world/assets.py:84`)・`floor(x/100)` の半開区間 [100i, 100(i+1))。同じセルの 2 点の距離の上限は対角 100√2 ≈ **141.42 m**(到達はしない上限)。
- 実資産での実測(node 幾何=体は歩行グラフのノードに居る・3,499 ノード・520 セル):
  - 同セルのノード対 20,556 組: 中央値 39.7 m・p90 80.0 m・**最大 133.65 m**・2 m 超が 99.59%・50 m 超が 37.8%。
  - 2 m 以内のノード対 101 組のうち **16 組が別セル**(うち 12 組は層の違い=GL/DECK/UG・4 組は格子の境界)。1 m 以内は 10 組のうち 3 組が別セル(3 組とも層の違い)。
  - 読み: 「1 m 隣でもできない」の実例は、格子境界の 4 組に加え、層違いの 12 組(同じ xy の上下=デッキと地上)。後者は階が違うので**会話できないのが正しい**場合がある=置き換え後も「層/階の一致」を別の欄で残す要(推測)。
- 付記: node 幾何では同じノードに居る体どうしの距離は 0(`resolve.py:1452` で `xy = node_xy`)。同席・B5 近接・偶然の出会いの 2 m 判定は node 幾何の重なりで水増しされる(指示書 §1-2 追加 A と一致)。

---

## 4. LLM の入力のうちセル共有の部分(B0〜B4)の割合

**結論: トークン比でセル依存群(B2+B4+B4b)は入力の約 16%。「約 2 割」は、ブロック順により B3 も共有から外れる分を足すと 16〜27% の幅に入る。ただしスループットへの効きは、実資産の 520 場所ではすでに小さいという既存ベンチがある。**

- 実資産・全日・実 LLM のラン(C7 day-3・描画 2,805,670 回): 平均 tok = 共有静的 642.8 / **セル 147.5** / 個体 133.3 / 合計 923.7(`docs/bench/c7/accept_c7-day-3/run_cli_summary.txt:16`)→ セル群 **15.97%**。day-4 も同じ(147.3/923.5=15.95%)。別の腕(`docs/bench/analysis/energy-classical-2026-09-28/p_see_activity_arms.json`): 152.0/(745.8+152.0+121.7)=14.9%。
- ブロック順 `("B0","B1","B2","B3","B4","B4b","B5","B6")`(`perception/templates.py:133`): 共有静的の B3(時間帯・天候・予算 100 tok)が B2 の**後ろ**に在る。B2 が個体ごとになると、prefix キャッシュは B0+B1 で切れ、B3 も共有から外れる。**B3 の実測 tok は記録なし**(記録はグループ合計だけ)。上限は予算の 100 tok → (147.5+100)/923.7 = **26.8%**。B3 を B2 の前へ動かせば 16% に留まる(バイトが変わる=知覚契約の改訂)。
- 数値は描画時のトークン推定(`perception/channels` の推定)で、トークナイザの実数かは**未確認**。
- スループットへの効き(合成ベンチ・8B INT8・vLLM・2026-09-02/03):
  - 階層 prefix(全体 600+種別 200+セル 200+個体 500): 種別まで共有=650.93 tok/s(ヒット 53.3%)・セルまで共有(32 セル)=720.07 tok/s(57.7%)→ **セル層を失うと −9.6%**(c32・o128)(`docs/research/v2-observation-format-research.md:233-235`)。
  - 「セル 128 超ではセル節を足しても種別止まりと同等(KV プール 82.9k tok に載りきらず LRU 追い出し)」(`docs/bench/README.md:35`)・BN-2C「実効セル上界は 10-40 セル・100 m 格子 139 は既に圏外」(`:43`)。実資産は 520 場所。
  - 読み(推測): 実資産の規模では、セル層の prefix 共有はトークン比の 16% ほどには効いていない可能性が高い。「共有が崩れたときの費用」は、実 LLM で B2 を個体化した腕と現行を比べる実測(指示書 §1-3 の検証項目)でしか確定しない。**実 LLM のランでの prefix ヒット率の記録は見つからなかった**(`docs/bench/` を `prefix|pc_hit|命中` で grep・C7 の summary の「命中率 1.000」はレンダラのキャッシュ命中で vLLM のものではない)。

---

## 5. 段階的に外す順番の案(**親への案・未リサーチ=expedient**)

依存の向き: 資産(W2/W3/W16/W17)→ 世界の状態(`world.cells`)→ 行為の成立・行き先 → 知覚・起床 → 計器。外すのは**読む側(下流)から**、各段で「セル版」と「新版」を切替口で並べ、旧挙動をバイト一致で再現できる状態を保つ(指示書 §0-1-4)。

| 段 | 対象(表の行) | 切替口を置く場所(案) | 既定 | 前提 |
|---|---|---|---|---|
| 0 | 口だけ作る: `SpatialIndex`(近傍の問い合わせ `within(agent, r)`・`same_level(a,b)`)・`FieldSampler`(場の値を xy で引く)・`PlaceResolver`(地名帳)・`ZoneMap`(xy→照合区域)。いずれも**セル版の実装を既定**にして中身は今と同じ | `engine/`(新モジュール)・`world/` | セル版=バイト不変 | なし |
| 1 | 計器と記録: E1 同行・E2 5 エリア・E3/E4 位置の列をテープへ(本人 xy と地名帳 ID)・E7/E8 | `tools/c7`・`engine/norm_meter.py`・`engine/tape.py`(列の追加) | 計器は既定の値を変えない | 位置テープのバイト予算の宣言 |
| 2 | 会話・近接: B1〜B5・B8・A4・A6。**v3 でも立つ独立の切替口**(`--proximity cell|distance`)にし、`attention_on`(edge∧v2)との結合を外す | `engine/resolve.py:talk_within_reach`・`engine/conversation.py` の開始/離脱・`perception/renderer.py:_nearby_items` の候補・`engine/relations.py:_same_cell_hits`・`engine/commit.py:pair_partners` | cell | 箱の中の社会(B10=§3-2 F)を同じ段か直後に(屋内の会話が消える穴を開けたまま既定にしない) |
| 3 | 環境の場: D3 騒音・D4 日陰・D5 流れ・D1 密度(近傍の局所密度)。値の段は同じ語彙に落とす | `world/state.py:noise_stage_for_tick`・`engine/processes/environment.py`・`engine/geometry.py`(Kladek) | cell | 物理(D 層)と一緒が自然(推測) |
| 4 | 起床と到達: A3 変化検出(本人単位の安い信号)・A5 顕著行為(80 m 半径)・A8 | `engine/change_detect.py`(検出器を差し替え可能に)・`engine/processes/salient.py:_candidates` | cell | P6 の再宣言と実測(40 万体) |
| 5 | 知覚の共有: A1/A2(B2/B4 を本人の位置・向き・目の高さで描く・B3 を B2 の前へ・キャッシュ鍵・E9 の並べる鍵) | `perception/renderer.py:render` のブロック組立・`perception/templates.py:BLOCK_IDS`・`llm/fleet.py` の並べ替え鍵 | cell | 知覚契約の改訂(§2.2/§2.4⑧/§2.5/§6)・実 LLM での費用の実測 |
| 6 | 行き先と行為の成立: C1/C2(地名帳の語・パーサ)・C3/C11(経路コスト)・C4/C5(店の中=L1 箱/入口)・C6(駅の縦の接続)・C7(住戸/ホテル POI)・C9・E6/E7(記憶・親しみの場所) | `llm/contract.py:parse_target`・`engine/poi_target.py`・`engine/resolve.py:_apply_move/_apply_sleep/_platform_table`・`engine/intent.py` | cell | 地名帳・ナビメッシュ・L1/L2 建物・形のない駅 |
| 7 | 資産と母集団: F7〜F11(W2 を地名帳と索引へ分解・W3 は経路探索へ・W8 T2 は廃止候補・W15 は作り直しか廃止・W16/W17 の拠点を建物/組織 ID へ)・F1〜F6 の世界過程・B9 初期関係網・F13 合成世界 | `build/` の各段(新しい段を足し旧段は残す)・`world/assets.py:load_assets` | 旧資産 | 生成のやり直し=§2-6「先に聞く」 |
| 8 | 旧経路の削除: `world.cells`・`registry.cell`・`CELL_BLOCK` の意味の書き換え・予算行 | — | — | 全段の版上げ後 |

- 指示書の例(計器 → 会話/近接 → 変化検出 → 知覚の共有 → 行き先)とは、段 3(環境の場)を起床より前に入れた点が違う。理由: 起床の新しい信号(本人位置の場の段の跨ぎ)が場の読み口を使うため(推測)。
- 段 2 と段 5 は「近傍の索引」を共有する。段 2 で作る索引の API を段 5 の描画も使う形にすると、近接 top-k の候補と会話の候補が同じ定義になる(案)。
- 版上げ: 段 2〜6 はどれも既定 checkpoint を動かす。指示書 §0-1-4 に従い、切替口で旧挙動を残したまま実装し、既定の切り替えは束ねて 1 回(案)。

---

## 6. 未確認の項

1. 手伝い・放送(B6)がエンジンで実装されているか(`llm/contract.py` の契約行だけ確認・`engine/` で `help|broadcast|手伝い|放送` を精査していない)。
2. 艦隊の発射順(`(cell, 5 分帯)` の並べ替え)が mock ランの結果に影響するか(E9 の checkpoint 欄を「不明」にした)。
3. B3 の実測 tok(§4)・描画の tok がトークナイザ実数か推定か。
4. 実 LLM ランでの vLLM prefix ヒット率(記録なし)。
5. `tools/hunger/build_hunger_anchors.py`(8 箇所)・`tools/fig/*` の中身は精査していない。
6. テスト件数はキーワードを含むファイルの全テスト関数の数(上限)で、キーワードに直接触れる関数の数ではない。golden/checkpoint 系は 55 ファイル(818)で、段 2〜7 の既定化のたびに更新が要る見込み(推測)。
7. P6(変化検出)を本人単位の信号に替えたときの費用は未計測(指示書 §1-3 の検証項目)。
8. 近接入替の起床 (ii)(知覚契約 §6)は未実装(`engine/change_detect.py:40`)で、セル依存のコードは無い(設計だけセル前提)。
