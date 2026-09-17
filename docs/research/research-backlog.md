# リサーチ残務台帳(2026-09-14・第178)

> 位置づけ: 「まだ調べていない/調べ切っていない」ものの索引。ユーザーの依頼(09-14「今残っているリサーチすべきことを書き出して欲しい」)で作成。各行の出所は答申・設計書・PENDING に既にあり、本書は**集めただけ**(新しい判断はしていない)。
> 規律: CLAUDE.md §2-4(各決定ラウンド前にリサーチ→出典・数値は親が一次確認)・§5(リサーチサブは子サブを起動しない)。
> 読み方: **ブロッキング**=これを済ませないと次の設計判断ができない/**着手時義務**=その機能を実装すると決めた時点で必須/**債務**=既に使っている数値の裏取りが残っている/**取得**=調べる対象は分かっていて入手が残っている。

---

## 1. 第2陣の設計ラウンドの前(ブロッキング)

| # | 何を | なぜ要る | 出所 |
|---|---|---|---|
| R-1 | **分野地図の答申**: 各分野に「検証済みの定量モデルが存在するか」「日本の公的データに錨があるか」を一次資料で確かめ、この repo が採用した形とのずれを列挙して決定アジェンダへ写す | 第2陣の主題選びの根拠。**骨組みは第180 で作った**([v2-discipline-map.md](v2-discipline-map.md)・32 分野・答申の有無つき)が、一次確認は未着手 | devlog 第172・第180 |
| R-2 | **LLM 社会シミュ文献 17 件の本文実読**: #4 同一性漂流・#5 議論バイアス・#6 StateAct・#8 状態表現・#10 GAMA(計算費の表)・#11 Larooij & Törnberg(PMC 全文)・#12 2603.00113(処方側の記述)・#13 頑健性監査(事前登録の推奨の有無)・#15 Causal Agent Replay・#17 Steering Geometry・#18 Procedural Graphs。各件を「採用済み/第2陣で採用/該当せず」に確定し決定アジェンダへ写す。#14(2026-06 事前登録)の実体探索 | **完了(第202)**: 12 件を本文実読 → 答申 [v2-r2-llm-social-sim-fulltext-check.md](v2-r2-llm-social-sim-fulltext-check.md)+lit 12 本(親確認 4 件: OASIS・GAMA・Ye・Larooij)。空欄 18 行は答申 §3(図中のみの数値・付録未読・#14「事前登録論文」の実体は #13 にも無し)。決定候補 5 件(報告様式=分布 / verification≠validation / 漏洩疑い欄 / TRAILS 被覆表 / v1 S-16 の移植)→ **PENDING D-75** | [v2-llm-social-sim-timeline-seed.md](v2-llm-social-sim-timeline-seed.md) §4 |
| R-3 | **個体の同質性の残 10 件**: 日本の始業時刻分布表・片道通勤時間の分布(令和3年の表 ID)・Schneider 2013 Fig.3 の p(ID) 数値・Schlich & Axhausen 2003 原典・inverse scaling と REAL Sampling の本文・2604.01520 の扱い・Song 2010 の追試値・交替制の出勤時刻・日本 PT へのモチーフ適用研究・TrajLLM の定量評価 | D-68 経路 3(記憶・習慣)の設計に直接効く → **第212 完了** [v2-d68-remaining-research.md](v2-d68-remaining-research.md)(lit 8・親確認 3): 始業時刻分布表は存在せず代理=時間帯編 15-4 表(東京都 p50 8:45・`:00+:30` 66%)・片道通勤時間は令和3年に無く住宅土地統計 58-2-1(東京都 p50 43.7 分・渋谷区 33.0)・交替制の 0:00 仕事率は固定の 4.8 倍(全国)/14 倍(東京都)=親再計算・Schneider Fig.3 数値なし(追試 11〜17 型/83〜90%)・Lu 2013 Π_max 0.88・REAL(ベースの次トークン)と 2605.09995(instruct の意味的多様性)は**別の層**・TrajLLM に定量評価なし・2604.01520「20–300 倍」は本文に裏づけ表なし → **PENDING D-81**。空欄 10 | [v2-d68-behavioral-diversity-research.md](v2-d68-behavioral-diversity-research.md) §8 |
| R-4 | **ミクロ観察の先行例**: エージェント個体の追跡・検査 UI(Generative Agents の replay/inspect・Concordia の GM ログ・AgentTorch ほか)。抽出規則(逸話を結論にしない作法)の先行 | 第177 M1 の設計判断の材料。自前設計の比重が高いかを先に知る → **第211 完了** [v2-micro-observation-research.md](v2-micro-observation-research.md)(lit 6・親確認 3): 自前の比重は小さい(粒度=ODD・読み口=Concordia/Via・抽出=head/tail・逸話規律=GA/POM)。指紋は N=1,000 と店名伏せの 2 点。**個体×tick 全記録は S1 の 92%=不可、場所カルテは 0.5%**。O6「再生で事後に作る」なら追加ラン 0・S1 追加 0 → **PENDING D-80** | devlog 第177 |
| R-4b | **v1 リサーチ資産の棚卸し**(第181): v1 固有の答申 127 本+文献メモ 44 本を「v2 の問いでも生きる/読み替えが要る/v1 固有で捨てる」に仕分ける。**社会ネットワーク科学・UQ・科学哲学の 3 つは v1 に素材がある**([v2-discipline-map.md](v2-discipline-map.md) §6-4) | 新規リサーチより安い。R-2 の一部(Larooij & Törnberg)も v1 の読解メモで前倒しできる | devlog 第181 |
| R-5 | **40 万体の可視化手法**: deck.gl / Cesium / Unity DOTS / UE5 Mass の実績と限界の**再確認**(答申 v2-game-frontend-research は 09 月初旬。**第203 訂正**: 同答申の「UE5 City Sample 35,000 人が公開実績上限」は**出典未確認**=Epic 公式3ページ(City Sample ドキュメント / Matrix Awakens ブログ / UE5.0 リリースノート)に体数の明示が無く"thousands of MetaHuman agents" / "tens of thousands of AI agents" 止まり(答申 [v2-r23-primary-check-batch1.md](v2-r23-primary-check-batch1.md) §2-4 #12)。**本項の残務に「Epic の GDC/Talks を一次で当たる」を追加**) | 第177 M2 の段階案を決める | [v2-game-frontend-research.md](v2-game-frontend-research.md) |

---

## 2. 実装に着手したら義務(着手時リサーチ)

| # | 何を | 発火条件 | 出所 |
|---|---|---|---|
| R-6 | **穴台帳(D-50)の深掘り**: affordance grounding・action-space discovery・BDI の失敗意味論・MATSim events 解析・HCI の breakdown analysis・Sid の行動ループ。既に軽リサーチした出典(MATSim `stuckAndAbort`・Voyager・AGA・Emergence World・MAST・AgentErrorTaxonomy・ACCORD)は**未一次確認**。**第204 追記(L-D71・サブ指摘・親未確認)**: ACCORD(2606.16432)の正式名は Action-Conditioned Contextual Grounding で抄録に affordance の語は無い(D-50 側の言い換え)/ Emergence World(2606.08367)の指標名は **M11=Tool Expansion**(親確認: §5.3「exactly two agent-authored tools」)/ 「試みたが環境が支えない行動」→語彙追加の手続きを書いた先行は LearnAct 1 本のみ | 穴台帳を作ると決めたとき | PENDING D-50 |
| R-7 | **群衆物理 U15 の空欄**: Weidmann 原典(**取得不能**=ETH bitstream 500・第207)・Burstedde 2001・Hughes 2002・Menge・HyPedSim(LOD 前例)・RiMEA の版とケース数・鉄道総研 2016 の実測歩行速度(**公開ページに数値なし**・第207)・Karmakharm の歩行者 GPU・データ駆動系の一次資料・スクランブルの公的信号現示・~~運輸政策研究 表―1 の単位~~(**第207 解消**: 行見出し「1分あたりの流動人数」・図の軸「流動量(人/m・分)」・親確認)・~~γ=1.913~~(**第207 解消**: Kretz 2015 式(1)(7)(8)(9)・親再計算) | CFSM を実装すると決めたとき(第177 M4) | [v2-crowd-physics.md](../design/v2-crowd-physics.md) §4 |
| R-8 | **幾何に基づく容量の根拠**(新規・第177 M3): ①セルの歩行可能面積(いま 100 m × 0.15 は expedient)の実測手順=PLATEAU 建物フットプリント+OSM 道路幅員からの差し引き ②店舗の床面積(いま既定 80 m²)の出所候補=経済センサス売場面積・建物階数×フットプリント ③1 席あたり面積(2/4 m²)の業界標準 ④ホーム・改札・階段の実効容量の公表値(鉄道会社・国交省)。U15-5 段階3(改札 56 人/台/分・エスカレーター 95.3/107.8 人/分)は取得済みだが**ホーム滞留の容量は空欄** → **第207 L-R8 で埋まった**([v2-c9-geometry-capacity-research.md](v2-c9-geometry-capacity-research.md)): ホーム 3.30 人/m²・整列 4.00〜4.50(鈴木 2012・親確認)/ 席 4.0 m² は消防法施行規則と逐語一致(mechanism 化可)・飲食は 1.43〜3.0 の帯(既定 3.0 推奨)/ 売場面積 特別区部 中央値 80.6 m²(e-Stat・親未確認)/ 歩行可能面積: 現行式は「道路面(車道込み)」相当=PLATEAU tran 歩道部 897,556 m²(親再計算)で置換手順あり。残務=渋谷駅のホーム面積・OSM 幅員タグの被覆・DECK/UG | 幾何に基づく制約を第2陣の主題にすると決めたとき | 第177・crowd.py・renderer.py の頭注 **第219 訂正**: 歩道部 897,556 m² は重複計上込み(一意化後 331,434)・「現行式=道路面」は不成立(比 0.506)。C9c-1 で実装済み |
| R-9 | **VLA・身体性の方向**: 第139 で所見だけ置いた「頭脳ではなく行動ラベル取得/身体化対照群/ロボット住民」を答申にするか | ユーザーが方向を決めたとき | PENDING(判断待ち)・devlog 第139 |

---

## 3. 答申の債務(いま使っている数値の一次確認が残っている)

| # | 何を | 状態 | 出所 |
|---|---|---|---|
| R-10 | **知覚 §10.2 の残**: 日本語成人の最大読書速度(cpm)の正典値・中小媒体の p_see(0.14-0.40 は英仏流用)・ISO 9921 数表と Lazarus 原典・Milgram 1969 原典・Hyman 2010 の群別 n | F-5 として登録済み | [v2-perception-contract.md](../design/v2-perception-contract.md) §10.2 |
| R-11 | **p_notice 系の 10 件**: Simons & Chabris の内訳・Haun 2021 の E2(孫引きの疑い→原典 JOV)・周辺視の運動検出閾値・Bouma 定数・視覚探索スロープ・Johnson 原典のサイクル数・ANSI S3.5-1997 の発声努力 SPL・IEC/EN 62676-4 の DORI・夜間の認識距離・群衆遮蔽度の 4 段 | **サーチスニペットのみ/規格本文未確認**が大半 | [v2-p-notice-research.md](v2-p-notice-research.md) 補足 |
| R-12 | **会話契約の二次引用**: Mastroianni 2021 PNAS(原典 403・持続時間の分布は空欄)・Sellen 1995・Robbins & Karan 2020(press release 経由)・Zhou 2005(要旨のみ)・Mollenhorst 2014(原典未読=内層の年間入替率が空欄)・ALFWorld の "Nothing happens." | 行動・会話契約書が依存 | [v2-action-conversation-contract-research.md](v2-action-conversation-contract-research.md) 空欄一覧 |
| R-13 | **聴覚**: hearing_verification の汚染除去版の正典化・Forssberg(原典不明のまま空欄)・消防法条文の e-Gov 直接確認(~~API 404~~ → **第199: e-Gov API v1 は生きている**=`/api/1/articles;lawId=…;article=…`。HTML は JS で本文が取れない) | F-6 として登録済み | PENDING F-6 |
| R-14 | **計器盤**: Augusiak 2014 要旨・Siepe 2024 の反復回数式・ECMWF 原文(**→ 第200 で取得済み**: [v2-replication-count-research.md](v2-replication-count-research.md))・~~History Matching for ABM(2501.00616)~~(**第209 実読**: 非含意度・閾値 3=Pukelsheim 1994・4 波で NROY 7.23%→0.82%・1 波=50 設計点×20 反復)・LLM エージェント評価サーベイ(2507.21504)・2022 年の評価記述標準プロトコル | 面2(予測)の指標選定が依存 | [v2-dashboard-verification-orchestration.md](../design/v2-dashboard-verification-orchestration.md) §4 |
| R-15 | **倫理・公開**: OASIS 付録 I 全文・Generative Agents §8.3 の残り・日本心理学会倫理規程・Five Safes 原文・EU AI Act 50 条(2) 原文・HF データセットカード原文・犯罪学 ABM の倫理 | 公開・論文化の段で要る | [v2-ethics-safety-operations.md](../design/v2-ethics-safety-operations.md) §4 |
| R-16 | **F-8 サーベイ由来の 4 件**: PIMMUR 6 原則の準拠表・Unawareness 監査の実 LLM 出力での自己言及率・数日連続稼働のドリフト観察・行動分散アンカー(2604.01520 考察節は本文未読) | ユーザー判断待ち | PENDING F-8 |

---

## 3b. 索引を作って判明したこと(2026-09-15・第191)

**[INDEX.md](INDEX.md) を新設**(v2 には答申の索引が 1 つも無かった。v1 には `docs/references.md` と `docs/research-scope.md` があった)。73 本に一次確認の等級 A〜E を機械判定で付けたところ、次が出た。

| # | 何を | なぜ要る | 状態 |
|---|---|---|---|
| **R-23** | **2026-08-30〜09-01 の答申 33 本の一次確認**。この 33 本は **URL を 1 件も含まない**(出典痕跡の合計 0〜17・うち 9 本は完全にゼロ)。09-02 以降の 40 本は中央値 62 件。断層の理由は **2026-09-03 のサブ捏造申告事件**で CLAUDE.md §5(親一次確認)が入る**前**のバッチだから | これらを根拠に新しい決定をしないため。**救い: 33 本に P0 は 1 本も無い**(P1 24・P2 9)。P0 の答申はすべて 09-02 以降 | **第1批 完了(第202)**: 設計書が実際に引く 8 本(legal-licensing・science-claims・engine-llm-boundary・llm-serving・pattern-ledger・game-frontend・game-tech-import・memory-retrieval)の決定に効く **28 主張**を一次確認 → [v2-r23-primary-check-batch1.md](v2-r23-primary-check-batch1.md)。一致 22(条件つき 6)・数値不一致 3・出典なし 1・原典より強い 2 → **PENDING D-74**(値を直す 4 件: パターン台帳 C1「中央値 1.3」は平均 / significance の future work 記述 / UE5 35,000 / Ruri 71.53<71.65)。親一次確認 3 件(Goel 2016 PDF・Law in Silico HTML・Ruri モデルカード)・Dunbar 1995 は有料で親未確認・UE5 の不在は親未確認。**第2批の先頭**=ファイル名では引かれていないが CLAUDE.md §3 の背骨「4 答申が同一分業に到達」を成す economy-sfc / conversation / llm-mobility(mobility-field)/ institutions。参照ゼロ 16 本は特徴値 grep(答申 §5-2 案 b)で棚卸し。DECIDED 行の撤回は無し。**第2批 完了(第208)**: 背骨 4 答申・32 主張 → 一致 22・不一致 2・出典なし 1・原典より強い 6([v2-r23-primary-check-batch2.md](v2-r23-primary-check-batch2.md))。**「独立収束」は過程レベルで不成立**・D4 修正3 の Sid 根拠は「実証」でない・0.8 は出典なし・Decoupling は住居移転データ → **PENDING D-78**。第3批=残り 16 本+循環参照検査・フロア併記検査 |
| **R-24** | ~~法学 #11 の答申 2 本が D 等級~~ → **第199 で再診断**: W7 はその 2 本に**依存していない**(両本に風営法の言及ゼロ)。実際の根拠は world-data-build-spec F13/D-W8 と round2-research B5(URL は巻末一括・条文ごとの紐付けなし)。**答申 [v2-w7-law-primary-check-research.md](v2-w7-law-primary-check-research.md) で法学 #11 を D→B(第199)→A(第200: 親が風営法 13/22/32 条・都条例 4 条の 2/4 条の 3/5/11/13/15 条・規則 5/6 条・青少年条例 15 条の 4/16/26 条を全て再取得・逐語一致)**。残務=告示番号・告示日/施行令 8・22 条/特定遊興 許容地域 2/用途地域の機械可読レイヤ/住居集合地域の定義(条例 3 条 1 項 1 号)/告示 PDF の親再取得。round2-research B5 の条文ごとの URL 紐付けは未着手 | 突合で **D-72(コードと条文の不一致 8 件)** が出た(第200 で ⑦特別日・⑧興行場等の未写像を追加) | **一次確認は完了・残務 6 件**(第200) |
| **R-25** | **統計学・因果推論 #23 と犯罪学 #32 に答申が 1 本も無い**(索引で数え直した結果。第180 の「答申が無い 4 分野」とは数え方が違う=第180 は主題として扱った答申、索引は紐づく答申) | #23 は事前登録・共通乱数・反実仮想の出所。**D-70(N を減らす設計)が直接ここに依存する** | **第 1 答申 完了(第209)** [v2-statistics-causal-research.md](v2-statistics-causal-research.md)(lit 8・親確認 3): 5 指標家族の 95% は 3 seed で 昼 ±2.2%/深夜 ±18.6%(**第204 の「3 本で深夜 2%」は単独指標の数**)・GET は seed 3 本で p≥0.25=検定不可(s≥20)・CRN は腕間のみ・History Matching(2501.00616)を実読=R-14 残務解消・CSB で D-44 を 5,000 体階層へ → **PENDING D-79**。空欄 13(JSD 帰無分布・O'Brien-Fleming・Bettonvil & Kleijnen の式 ほか) |
| **R-26** | **C 等級 1 本**(ad-information・痕跡 143 件だが空欄節が無い)。空欄が無いのか未整理なのか未判定 | 社会ネットワーク科学 #14 の唯一の答申 | 読めば済む(web 不要) |
| **R-27** | **反復回数(L-B)の空欄 5 件**(第200・答申 [v2-replication-count-research.md](v2-replication-count-research.md) §4): Lorscheid 2012 の本文(有料・図書館経由)/ Law 教科書の逐次手続きの原文(版・章・式番号)/ Secchi & Seri 式 (2) の係数の逐語(PDF テキスト層に無い)/ Leutbecher 2019 QJRMS 査読版 / ECMWF が「51」を選んだ明示文書 | D-70・D-44・G-8 の根拠の穴。手続きは二次で確認済みなので**決定は進められる** | 未着手(第200) |

**逆引き表が無い**: どの答申がどの DECIDED 行の根拠かは決定台帳側からしか辿れない。索引 §5 に記載。

---

## 4. 公的データの取得待ち(調べる先は分かっている)

| # | 何を | 状態 | 効く先 |
|---|---|---|---|
| R-17 | **PT 2018 c-2/b-4**(ゾーン別目的別発着時間帯別発生集中量・時刻別滞留人口) | tokyo-pt.jp の同意ページ越し=**ブラウザ操作が要る**(ユーザーの手) | D-23 の JSD 合格線・E1 到着便・内閣府 PDF の図の数値化 |
| R-18 | **OSM 道路名の再取得**(Overpass・primary/secondary の name/ref) | D-1 (a)・公的ドメイン外・数 KB・読み取りのみ | W10 騒音場の区間突合(いま 0/202・ゲート FAIL 2 本) |
| R-19 | **5 エリア境界の座標化** | D-41 の昇格条件=OSM 線形化 / SCJ 施設 214 件の属性一致 ≥90% / 区への照会 | holdout 照合の写像(いま expedient・±50m で 5.6-8.3% が移動) |
| R-20 | **都環境局 自動車交通騒音の最新年度表**(渋谷 5 点の時点更新) | H23 で代替中 | W10 |
| R-21 | **チェーン公式の営業時間表**(上位 300 件の手入力・API 規約=法務レーン)・**駅構内図の手入力** | D-W8・駅構内グラフの精度 | W7・W11 |
| R-22 | **PLATEAU 渋谷区 2023 年度版+追加メッシュ**(D-W5b)・**再生候補日の選定**(D-W15) | 未決 | W4・W13 |

---

## 4b. 答申がまったく無い分野(第180 の照合で判明)

| 分野 | なぜ要る | 優先 |
|---|---|---|
| **社会ネットワーク科学** | 会話 0.04%・情報が広がらない。関係の構造と伝播の形が無い | 高。**v1 に素材あり**(R-4b で読み替え) |
| **物質フロー分析(都市代謝)** | 廃棄が現実の帯の 1/9(D-52)。発生源の台帳が店舗の期限切れ在庫だけ | 高(同上) |
| **不確実性の伝播(UQ)** | 受入表は点の判定しかしない。誤差がどう伝わるかの設計が無い | 中。v1 `uncertainty-audit` が出発点 |
| **科学哲学(モデルの認識論)** | 「妥当」「再現」が何を言うことかの整理。第一目標の言葉そのもの | 中。v1 `measurement__validation-overview` が実務側を押さえている |

---

## 5. 将来ラウンド(工程外・PENDING §4)

- **F-1** 行5 価格(店主 LLM がスカラーを出す)の実証リサーチ。先行(EconAgent 等)は方程式のみで、桁を外す逸脱が非ゼロという警告あり。
- **F-2** UGC 輸入 26 提案の個別採否(R8 判例化 5 段・MER/残差/退蔵 ほか)。
- **F-3** 犯罪・逸脱の創発(機会構造・コンテンツ安全答申との整合・向社会性バイアス・検証装置)。
- **F-4** R17 の新論点(実在企業の効果を公表することの是非)。
- **F-7** 日本語補強モデル(CALM3/Sarashina2)の目視 12 問比較。要否はユーザー判断。

---

## 6. 取得不能と確認済み(再探索しない・時間を使わない)

| 何を | 確認した範囲 |
|---|---|
| 渋谷駅の時間帯別乗降人員 | 大都市交通センサス e-Stat 117 表・JR東日本・東急の公表ページ=**公表系に存在しない** |
| 来街者の来訪頻度の公的分布 | 区の意識調査・東京都繁華街利用実態調査(2001 以後同様の調査なし)=**見つからず** |
| 日本人来街者の平日滞在時間 | TCVB は訪日・土日・12-20 時のみ。センター街は通行量のみ=**見つからず** |
| 「試みたが環境が支えない行動」を採掘して砂場の欠落を監査する研究 | D-50 の軽リサーチ=**見当たらず**(自前設計の比重が高い) |
| 5 エリアの町丁目リストによる定義 | 指針 2010・都の景観指針=**未発見** |
| 平日休日比(KDDI) | 6 レイヤに曜日軸なし=**測定不能**(深夜残存率で代替) |

---

## 7. この台帳の使い方

- 新しい答申を書いたら、その末尾の「空欄(未確認)」を**本書へ写す**(答申の中に埋もれさせない)。
- 一次確認が済んだ行は本書から消して、答申側に確認日と手段を書く(PENDING と同じ作法)。
- **ブロッキング(§1)だけがラウンドを止める**。§3 の債務は使っている数値の裏取りなので、値が動いたときに影響範囲を再計算する用意だけしておく。

## 3c. リサーチ反映の監査で出た取りこぼし(2026-09-17・第214)

| # | 何を | 出所 | 状態 |
|---|---|---|---|
| **R-28** | **監査の取りこぼし候補 62 項+設計済・未実装 82 項**(全 80 答申・484 項の 5 値監査: 実装済 44.2%・部分 21.5%・設計済未実装 16.9%・未採用 4.5%・未判定 12.8%)。上位: 人流の二次モーメント指標(滞留・Zipf・EPR)が計器に 0 件 / 反実仮想渋谷の常設対照ラン / 艦隊バックプレッシャ 3 段・TiDi / T2 内省の実呼 / prereg v1.3 の統計が `holdout_compare.py` に無い / AB2〜AB5 未実施 / 保存則 T3 / seed 交換可能性検査 / 決定台帳に「根拠答申」列が無い | [v2-research-reflection-audit.md](v2-research-reflection-audit.md)・[-p1p2.md](v2-research-reflection-audit-p1p2.md) | **決定(第215)**: ①②④ 今週(① 第215 実装サブ着手)・③⑤ S2・⑥ 第2陣・⑦ 進めてよい範囲 |
| R-29 | PIMMUR(2509.18052)の引用を版指定つきに直す(v4: 350 論文/576 実験・65.2%・50.6%)。既存答申 science-claims・F-8 | L-CLS 親確認 | 注記済み(答申・F-8)・本文の一括訂正は未 |
| R-30 | 事前登録の外部根拠+1: Anthis et al. 2025 §4.5.2「we encourage, preregistration of LLM simulation predictions」(親確認)→ prereg を「分野の推奨の履行」へ書換 / Hewitt 2024 と Ashokkumar 2026 が同一研究か未確定 | L-CLS | prereg v1.3 に反映(第214) |
