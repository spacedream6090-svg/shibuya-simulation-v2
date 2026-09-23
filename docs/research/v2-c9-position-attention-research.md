# v2-c9-position-attention-research — 位置・速度・注意・会話距離・目印の先行研究(C9 決定 G1〜G7 の裏づけ)

<!-- hdr:v1 -->
- **分野**: 人間移動科学 #3 / 歩行者動力学(群衆物理)#18 / 認知科学(記憶・習慣)#12 / 計算社会科学 #25(+ 知覚心理学 #5・ゲームエンジン工学 #30) | **重要度**: **P0**
- **一次確認**: **B → 親確認 3 件(第207)**: Bosina & Weidmann STRC 2018 PDF p.6 Table 2「Desired walking speed vd [m/s] | 1.00 | 1.60 | Bosina and Weidmann (2017)」(親 curl+pymupdf)=**「年齢係数」ではなく希望速度の幅**/ Kladek 式の再計算(歩行可能面積 4,206 m²: 1,000 人/セル→ρ 0.238・v 1.339 m/s / 1,811→1.318 / 3,018→1.207 / 14,000→3.33 人/m²・0.265 m/s)一致 / Sorokowska 2017・Hall・Itti・岡田・一宮は親未確認。実読 = Bosina & Weidmann 2018(STRC PDF 全 33 頁)/ Kretz 2015(ar5iv 本文)/ Itti-Koch-Niebur 1998(TPAMI 6 頁)/ 森田ほか 2004(AIJ 技報 PDF 6 頁)/ 岡田・横山 2019(MERA PDF 1 頁)/ 一宮・松村 2026(CPIJ 関西 PDF 4 頁)/ Sorokowska ほか 2017(著者最終稿 PDF 36 頁)/ Unreal Engine 公式 AI Perception ドキュメント / Generative Agents(ar5iv 本文)・AgentSociety(arXiv HTML)・CitySim(arXiv HTML)・GATSim(arXiv PDF 56 頁)。**未取得 = Weidmann 1993 原典(ETH Research Collection の bitstream が HTTP 500・旧 e-collection は DNS 不達)・Hall 1966 原典・Lynch 1960 原典・Kim/Van Velsen/Hill 2005(出版社有料・抄録も削除)**
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **分野地図**: [v2-discipline-map.md](v2-discipline-map.md)

> 目的: [C9 決定アジェンダ](../design/v2-c9-geometry-agenda.md) の **G1〜G7** を先行研究の一次資料で裏づける/覆す。材料は [C9 材料](../design/v2-c9-geometry-brief.md)。
> 表記: **[実読]** = 本文/表/節を実際に読んだ。**[要旨]** = 抄録・公式ページの要約まで。**[書誌のみ]** = 本文が取れていない。**[再計算]** = 本書で計算した。逐語は原文のまま **≤125 字**。
> **推奨は書いてよいが決定は親とユーザー**(§2)。規律: 子サブ未起動・コミットなし・既存ファイル未編集(本書と `lit/` の新規 8 本のみ)・holdout 未開封・サーバー未使用。
> 読解手段の注記: 調査の途中で WebSearch/WebFetch が使用上限に当たったため、後半は **URL を直接読む方式**(HTML/PDF をストリームで取得し `pymupdf` で本文抽出。保存はスクラッチのみ・リポには置いていない)に切り替えた。取得先は arxiv.org / strc.ch / jstage.jst.go.jp / rtri.or.jp / 大学リポジトリ / dev.epicgames.com。

---

## §1 問いごとの表

### 1.1 問い1 — LLM エージェント系は「セル内位置」をどう表しているか

| 出典 | 逐語・節 | 位置の型 / 近接の判定 / 速度 | G へ |
|---|---|---|---|
| **Generative Agents**(Park et al. 2023, [arXiv:2304.03442](https://arxiv.org/abs/2304.03442))**[実読]** ar5iv §3.1.1・§3.2・§5・§5.1・Fig.2 | §5「The Smallville sandbox game environment is built using the Phaser web game development framework」/ §5「an environment map and collision map that we authored, are imported into Phaser」/ §5.1「as a tree data structure, with an edge in the tree indicating a containment relationship in the sandbox world」/ §5「sending all agents and objects that are within a **preset visual range** for each agent to that agent's memory」/ §5.1「we use traditional game path algorithms to animate the agent's movement」 | **タイル格子 + 包含木**(場所と物の入れ子)。近接 =「preset visual range」だが **本文に数値が無い**(本文中「radius」「tile」「grid」は 0 件。付録 A/B は取得が切れており未確認)。速度 = ゲームの経路アニメーション(m/s の記述なし) | **G1**。先行の代表例が「格子 + 木」で、**近接半径を論文に書いていない** |
| **AgentSociety**(Piao et al. 2025, [arXiv:2502.08691](https://arxiv.org/abs/2502.08691))**[実読]** HTML v2 §4.1・§4.2・§4.3・§3.3・§5.4 | §4.2「road networks, defined by lanes, roads and junctions to encode traffic accessibility」/ §4.2「positions, speeds, and accelerations are updated dynamically according to kinematic principles and predefined rules」/ §4.2「Pedestrians navigate sidewalks at a constant speed and follow the traffic signals at junctions」/ §4.3「offline interactions based on spatial proximity remain an indispensable component」/ §5.4 実装は「simplified into sending messages to specific targets」 | **車線上の連続運動学**(位置・速度・加速度を持つ)。ただし **歩行者は定速**(値は本文に無い)。**近接の距離閾値は本文に無い** — 対面相互作用はメッセージ送信に簡約 | **G1/G7**。連続位置を持つ系でも **会話の距離判定は書かれていない** |
| **CitySim**(Bougie & Watanabe 2025, [arXiv:2506.21805](https://arxiv.org/abs/2506.21805), EMNLP 2025 Industry 215-229)**[実読]** HTML §3・§3.2.2・§3.3・§4.4・§4.6・App.A/B/C.1 | §3「in a dynamic, graph-structured urban environment」/ App.B 擬似コード「move(poi, vehicle)」/ App.A「Simulation operates with a 5 minute timestep, and all random seeds are fixed for reproducibility.」/ §3.3「Face-to-face interactions occur when agents are co-located in same space.」/ App.A「Face-to-face interactions are limited to one partner per 30-minute tick」/ §4.6「Comparison of simulated (left) and real-world (right) crowd density heatmaps in Shibuya, Tokyo.」/ §4.6「CitySim sometimes underestimates crowd in small streets」 | **POI 単位**(座標も格子も持たない)。近接 = **同一空間に居ること**(距離なし)・相手は 30 分に 1 人。速度・所要時間の式は **本文のどこにも無い**(移動は AgentSociety のエンジンに委譲)。既定 1,000 体・走査は 10^3〜10^6 で 9.0×10⁻³ 〜 0.183 s/step | **G1/G7**。**「渋谷の密度を再現した」と主張する系が位置を POI に丸めている** = v2 の現状(ノード量子)と同格かそれ以下 |
| **GATSim**(Liu, Li & Ma 2026, [arXiv:2506.23306](https://arxiv.org/abs/2506.23306) v3)**[実読]** PDF §3.1 | §3.1「The transportation network is formally described by a graph G = (V, E)」/ §3.1「Each facility is spatially associated with a specific node in the transportation network.」/ §3.1「a point-queue system … with **instantaneous movement between queue positions rather than continuous spatial dynamics**」/ §3.1「hierarchical transportation network representation strategy utilizing three complementary formats: graph, tilemap, and bitmap」 | **ノード/リンク量子化**。連続位置を明示的に持たない(点待ち行列)。速度 = リンク容量と待ち行列。**近接・会話の記述は無い** | **G1**。v2 の現状(`xy` を毎 tick ノード座標で上書き)と **同型の先行が実在** = 現状 (a) は欠陥ではなく一つの選択肢。ただし GATSim は会話・近接を持たない |

**問い1 の判定**: **格子(GA)・車線上の連続運動学(AgentSociety)・POI(CitySim)・ノード量子(GATSim)の 4 通りがすべて実在**し、**近接の判定距離を数値で書いた先行は 4 本のうち 0 本**。`preset visual range`(GA)・`co-located in same space`(CitySim)・`spatial proximity`(AgentSociety)はいずれも語のまま。**「近接距離を数値で宣言する」こと自体が v2 の差分になる**。

### 1.2 問い2 — 歩行者の自由速度と「1.00〜1.60」の出所

| 出典 | 逐語・節 | 数値 | G へ |
|---|---|---|---|
| **Bosina & Weidmann 2018**「Creating a generic model of the pedestrian fundamental diagram」18th Swiss Transport Research Conference, [strc.ch/2018/Bosina_Weidmann.pdf](https://www.strc.ch/2018/Bosina_Weidmann.pdf) **[実読]** 全 33 頁・**Table 2**(p.5)・Table 3・§3.3.1 | Table 2 表題「Range of values for the pedestrian characteristics used for modelling the fundamental diagram.」/ 行「**Desired walking speed vd [m/s] / Minimum 1.00 / Maximum 1.60 / Source: Bosina and Weidmann (2017)**」/ 同表「Body width wB [m] 0.49 / 0.33」「Body depth dB [m] 0.29 / 0.17」「**Intimate distance dI [m] 0.20 / 0.15 / Hall (1966)**」「Reaction time tr [s] 0.80 / 0.40」/ p.10「The fundamental diagram for walkways presented by Weidmann (1993) is well within this range.」 | **1.00〜1.60 は「希望歩行速度 vd の m/s の幅」。係数ではない。** 出所は Bosina & Weidmann 2017(Physica A 468:1-29, [doi:10.1016/j.physa.2016.09.044](https://doi.org/10.1016/j.physa.2016.09.044)・200 本超の文献集約・**本文は有料で未読**) | **G2 の訂正**。§2-B |
| **repo 内の記述**: [群衆物理設計書](../design/v2-crowd-physics.md) U15-5 段階2 / [群衆物理答申](v2-crowd-physics-research.md) :49 | 設計書「Weidmann 1.34 m/s …**母集団合成の年齢構成で個体分布(1.00〜1.60)を作る**」/ 答申 :49「**Bosina & Weidmann 2018(サブ実読): 希望歩行速度1.00–1.60 m/s**・体幅0.49–0.33m」 | **repo は元から m/s と書いている**。**「年齢係数(1.00〜1.60)」という語は [C9 決定アジェンダ](../design/v2-c9-geometry-agenda.md) G2 が初出**(2026-09-17)= アジェンダ側の読み違い | **G2**。掛け算にすると **1.34〜2.14 m/s = 4.8〜7.7 km/h**[再計算] |
| **Weidmann 1993** 原典(Transporttechnik der Fussgänger, Schriftenreihe des IVT Nr. 90, ETH Zürich) | — | **原典を取得できなかった**。ETH Research Collection の記録ページ(handle `20.500.11850/47999`)は生きているが **bitstream が HTTP 500**、旧 e-collection は **DNS 不達**。**年齢別歩行速度表は本調査でも未確認 = 空欄** | **G2**。年齢で配分するなら別の一次資料が要る(§3-1) |
| **鉄道総研 2016 年度主要な研究開発成果 21「駅構内における旅客の群集密度と歩行速度」**([rtri.or.jp/rd/seika/2016/4-21.html](https://www.rtri.or.jp/rd/seika/2016/4-21.html))**[実読]** ページ全文 | 「旅客の歩行速度は現在使用されている**約40年前の推定式による値よりも低い傾向**にあることがわかりました。」/ 図 1 表題「旅客の歩行速度と密度の計測手法」/ 手法 = 小型ウェアラブルデバイスで足元の歩行動作から速度・周囲との距離から密度 | **公開ページに数値は 1 つも無い**(m/s・人/m²・比較対象の式名・著者名・報告番号すべて記載なし)= **R-7「鉄道総研 2016 の実測歩行速度」は数値未取得のまま**。ただし **向き(日本の駅では従来式より遅い)は一次で取れた** | **G2**。**Weidmann は上振れ側の可能性** = 感度腕「自由速度 ×0.8」の根拠 |

**問い2 の判定**: **「年齢係数 1.00〜1.60」という量は repo にも先行にも存在しない**。存在するのは **希望歩行速度そのものの幅 1.00〜1.60 m/s**(STRC 2018 Table 2 で逐語確認)。**年齢別の歩行速度表は本調査では一次で取れなかった**(Weidmann 1993 原典が取得不能・Bosina & Weidmann 2017 本文が有料)。

### 1.3 問い3 — 密度による減速(基本図)

| 出典 | 逐語・節 | 数値 | G へ |
|---|---|---|---|
| **Kretz 2015**「The Social Force Model and its Relation to the Kladek Formula」([arXiv:1512.01426](https://arxiv.org/abs/1512.01426))**[実読]** §2「Introduction Part II: the Kladek Formula」 | 式 (1)「v̄m = v̄f (1 − e^{−γ(1/ρ − 1/ρmax)})」/ §2「Weidmann applied the Kladek formula to describe the speed-density relation of uni-directional pedestrian flow」/ §2「Weidmann's parametrization of the Kladek formula to describe uni-directional, two-dimensional pedestrian dynamics is」→ 式 (7) **v_f = 1.34 m/s** / 式 (8) **γ = 1.913 1/sqm** / 式 (9) **ρ_max = 5.4 1/sqm** / 式 (10)「a = γ/ρmax ≈ 0.354」 | **R-7 の空欄「γ = 1.913 は未確認」が解消**(arXiv 一次・式番号つき)。参照 [10] = Weidmann 1993・[11] = Buchmüller & Weidmann 2006 | **G2**。**式はこの 1 本で足りる** |
| **Fruin 1971**(HRR 355)。repo が [群衆物理答申](v2-crowd-physics-research.md):14 で **親照合済み** | 親照合の逐語「Maximum flow volumes of **26.2 and 24.7** pedestrians per minute per foot of walkway」「**35 sq ft** per person」 | **[再計算]** LOS 境界(sq ft/人 → 人/m²・1 sq ft = 0.09290304 m²): **A ≤0.308 / B 0.308–0.431 / C 0.431–0.718 / D 0.718–1.076 / E 1.076–2.153 / F >2.153**。最大流 26.2 → **85.96 人/分/m**・24.7 → **81.04 人/分/m** | **G2/G8/G10**。U15-4 の「LOS C 相当 0.43〜0.72 人/m²」は本再計算と一致 |
| **森田・阪田・高木・山本 2004**「祝祭街路における群集密度と歩行特性に関する研究—神戸ルミナリエを中心として」日本建築学会技術報告集 No.20, 307-312([doi:10.3130/aijt.10.307_2](https://doi.org/10.3130/aijt.10.307_2))**[実読]** PDF 6 頁・表 2・表 3・図 8/9 | 「転倒を誘発するような周囲の圧力がなく、**安全に歩行するためには2〜3人/㎡、安全に静止するためには3〜4人/㎡**までの群集密度に抑える必要があると推測される」/ 表 3 表題「神戸ルミナリエにおける群集密度と歩行速度の計測結果」/ 比較対象 =「直線型の**J.J フルーイン式**、ベキ乗型の**木村・伊原式**、反比例型の**戸川式**」 | 屋外・祝祭街路の実測(2001-12-23 来場 58.1 万人 / 2002-12-22 68.6 万人 / 2002-12-23 44.8 万人)。表 3 の範囲は **密度 0.85〜4.37 人/m²・速度 0.03〜1.8 m/s**、空いた区間(「人まばら」)は **0.93〜1.27 m/s**。**PDF が画像スキャン + OCR 層のため区間別の対応は親が原典で再確認すべき** | **G2**。U15-5 が「屋外広幅員・多方向流の基本図は実験室データに無い = expedient」と宣言した穴に **日本の屋外実測が 1 本入る**。ただし祝祭 = 鑑賞歩行で自由速度は 1.34 より低い |
| **[再計算] v2 のセルへの当てはめ** | — | 歩行可能面積の中央値 **4,206 m²**([C9 材料](../design/v2-c9-geometry-brief.md) §1.4)で割ると `DENSITY_STAGE_EDGES` 最上段 **1,000 人/セル = 0.238 人/m² = Fruin LOS A**(Weidmann 式で **v = 1.339 m/s** = 自由速度のまま)。**LOS C の入口は 1,811 人/セル**・上端 **3,018 人/セル**。C7 実測の最混雑セル人口 **1.4 万**(同 §4)は **3.33 人/m² → v = 0.265 m/s** | — | **G2/G8/G10**。§2-C |

**問い3 の判定**: 式(Kladek/Weidmann)と LOS 境界は **一次で揃った**。日本の駅の実測(鉄道総研 2016)は **向きだけ** 取れ数値は空欄、日本の屋外実測は **祝祭街路 1 本** が取れた。

### 1.4 問い4 — 「注意の焦点」を状態として持つ先行

| 出典 | 逐語・節 | 機構・数値 | G へ |
|---|---|---|---|
| **Itti, Koch & Niebur 1998**「A Model of Saliency-Based Visual Attention for Rapid Scene Analysis」IEEE TPAMI 20(11):1254-1259([doi:10.1109/34.730558](https://doi.org/10.1109/34.730558))**[実読]** 6 頁全文(著者最終稿 PDF の大学配布コピーで取得・**出版社版は未取得**) | §1「a spatially circumscribed region of the visual field, the so-called "**focus of attention**," which scans the scene」/ §2.2「1) The FOA is shifted to the location of the winner neuron;」/ §2.2「3) local inhibition is transiently activated in the SM, in an area with the size and new location of the FOA」/ §2.2「but it also prevents the FOA from immediately returning to a previously-attended location.」/ §2.2「Such an "**inhibition of return**" has been demonstrated in human visual psychophysics」/ §2.2「a small excitation is transiently activated in the SM, in a near surround of the FOA ("**proximity preference**" rule of Koch and Ullman)」 | **注意の焦点 = 1 個の状態**(位置)。遷移は勝者総取り。**FOA は 30–70 ms で次へ跳び、注意した領域は 500–900 ms 抑制される**(§2.2・心理物理の観測に合わせた値) | **G4**。「注意の焦点 1 欄」は **視覚注意計算モデルの標準形**。加えて **IOR = 不応期の原型**・**proximity preference = 近い対象へ移りやすい** |
| **Unreal Engine 公式「AI Perception in Unreal Engine」**([dev.epicgames.com](https://dev.epicgames.com/documentation/en-us/unreal-engine/ai-perception-in-unreal-engine))**[実読]** ページ全文 | 「AI Perception Component which acts as a **stimuli listener** and gathers registered Stimuli Sources.」/ 「**On Target Perception Updated** (for target selection)」/ 「**Dominant Sense** property can be used to assign a Sense that should take precedence over other senses when determining a sensed Actor's location.」/ AI Sight「**Sight Radius**: The max distance over which this sense can start perceiving.」「**Lose Sight Radius**: The max distance in which a seen target is no longer perceived」/「**Peripheral Vision Half Angle Degrees**」/「**Auto Success Range from Last Seen Location**」/ 各センス共通「**Max Age**: Determines the duration in which the stimuli generated by this sense becomes forgotten (0 means never forgotten).」 | 産業側の標準形: ① **取得半径と喪失半径を別に持つ**(ヒステリシス) ② **視野角を持つ** ③ **刺激に寿命(Max Age)がある** ④ **感覚に優先順位(Dominant Sense)** ⑤ **最後に見た位置からの自動成功範囲**(対象の粘り) | **G4/G7**。v2 は ①〜⑤ の **どれも持っていない**(W8 は視野角なし・全方位・打ち切り 150 m)。§2-D |
| **repo が引く出典の状態**: [知覚契約](../design/v2-perception-contract.md) §3.1・§4 | §3.1「歩行者が他の歩行者を注視する距離の中央値は **10.3 m**(IQR 8.3-12.3・昼13.0/夜8.9・注視480 ms = Fotios 2015)」/ §4「顕著性順位 = **視角(サイズ/距離)×局所輝度コントラスト**(+動き・逸脱度)」/ §4「積形はフロア付き対数加算として実装(Itti & Koch が否定したのは線形和)」/ §4「逸脱度優先 = Jovancevic-Misic & Hayhoe 2009」 | **本調査で一次確認できたのは Itti 系のみ**。Fotios 2014/2015・Jovancevic-Misic & Hayhoe 2009・Cowan 2001 は **本調査では当たっていない**。**「Itti & Koch が否定したのは線形和」という逐語は 1998 年 TPAMI 版には無い**(あるのは正規化演算子 N(.) の議論「globally promotes maps in which a small number of strong peaks of activity … is present」) | **G4**。§3-4 |
| **Kim, Van Velsen & Hill 2005**「Modeling Dynamic Perceptual Attention in Complex Virtual Environments」IVA/LNCS 3661([doi:10.1007/11550617_23](https://doi.org/10.1007/11550617_23))**[書誌のみ]** | 本文・抄録とも取得できず(索引側が `openAccessPdf: CLOSED`・抄録は出版社により削除) | 仮想人間に **動的な知覚注意** を持たせた系譜として名前だけ記録。**本書では主張の根拠にしない** | **G4**(§3-5) |

**問い4 の判定**: **「注意の焦点を 1 個の状態として持ち、対象を離れたら抑制する」形は、認知科学(Itti 1998 の FOA + IOR)と産業(UE の Perception + Sight/Lose Sight/Max Age)の両方に明示的先行がある**。G4 案(`待機` × 対象 = 注意の焦点・4 B/体)は **両者の最小形**。**足りないのは「外れる条件」**(喪失半径・寿命)。

### 1.5 問い5 — 会話が成立する距離

| 出典 | 逐語・節 | 数値 | G へ |
|---|---|---|---|
| **Sorokowska ほか 2017**「Preferred Interpersonal Distances: A Global Comparison」J Cross-Cult Psychol 48(4):577-592([doi:10.1177/0022022117698039](https://doi.org/10.1177/0022022117698039))**[実読]** 著者最終稿 PDF 36 頁・Materials and methods・Table 2 | 「Our study was comprised of **8,943 participants** … inhabiting 53 study sites in **42 countries**.」/ 「Answers were given on a distance (**0-220 cm**) scale anchored by two human-like figures」/ 「distance to (1) a stranger, (2) an acquaintance and (3) a close person … reflected … (1) social distance; (2) personal distance; and (3) intimate distance (Hall, 1966)」/ Table 2 Intercept **135.14**(社会)・**91.72**(個体)・**31.85**(親密) | **見知らぬ人 1.35 m・知人 0.92 m・親しい人 0.32 m**(42 か国の多水準モデル切片)。**日本は 42 か国に含まれない**(本文中「Japan」の出現は参考文献 1 件のみ)[実読による確認]。**回答尺度の上限が 220 cm** = 2 m 超は測れていない | **G7**。**d_talk = 2 m は「見知らぬ人への選好距離 1.35 m」より 0.65 m 広い** = 会話する二人が実際に取る距離をほぼ全部覆う |
| **同上・Hall 1966 の再掲**(Classifying social distance 節)**[二次]** | 「(1) public distance (**above 210 cm**) … (2) social distance, maintained during more formal interactions (**122-210 cm**) … (3) personal distance, maintained during interactions with friends (about **46 to 122 cm**) … (4) intimate distance … (**from 0 to 46 cm**)」 | **Hall 1966 の原典は未取得**。二次の再掲では **社会距離の上限が 210 cm・公衆距離は 210 cm 超**。依頼文の「社会 3.6 m」(原典の 4-12 ft に相当)と **帯の切り方が食い違う** | **G7**。**どちらで読んでも 2 m は「会話が成立する側の上限」**= 裏づけになる。ただし **原典の帯は未確認** |
| **Bosina & Weidmann 2018** Table 2(§1.2 と同じ表)**[実読]** | 「**Intimate distance dI [m] 0.20 / 0.15 / Hall (1966)**」 | 歩行者基本図モデルが **Hall を 0.15〜0.20 m の「体の間に残す最小距離」として使っている**(Hall の 0-46 cm 帯のさらに内側) | **G7/G1**。**Hall の帯はモデルに入れるとき 1 つの数に落ちる**という先行の作法 |
| **一宮・松村 2026**(§1.6 と同じ)**[実読]** | 「待機者の **8 割以上がスマートフォンを操作**していた」 | 現代の待ち合わせでは **相手を目視で捜さない** = 会話開始前の「見る」が減っている | **G4/G7**。焦点が人でなく端末に行く現実がある |

**問い5 の判定**: **G7 の 2 m は支持される**。屋外・群衆での会話距離の実測は本調査では見つからず(ISO 9921 は R-10 の既出なので当たっていない)、代わりに **選好距離の 42 か国実測(日本は非対象)** と **歩行者モデルが Hall を使う実例** が取れた。**「密度が上がると会話距離が縮む」ことを直接測った一次資料は見つからなかった**(= v2 の ×0.42 は依然 expedient)。

### 1.6 問い6 — 目印(landmark)を待ち合わせの場所にする先行

| 出典 | 逐語・節 | 数値 | G へ |
|---|---|---|---|
| **一宮・松村 2026**「スマートフォンの普及による待ち合わせ行動の変化に伴う待ち合わせ場所のアメニティ空間としての可能性に関する研究」日本都市計画学会関西支部研究発表会講演概要集 24:149-152([doi:10.11361/cpijkansai.24.0_149](https://doi.org/10.11361/cpijkansai.24.0_149))**[実読]** PDF 4 頁 | 「かつての待ち合わせ行動は、**特定のランドマークを頼りに相手を「捜索」するプロセス**を伴い、その場所は待ち合わせの象徴としての空間的価値を有していた。」/ 「スマートフォンの普及後、リアルタイムでの位置共有や連絡が可能となり、かつての「捜索」するプロセスは大幅に削減された」/ 評価軸 =「**認知性(ランドマーク性・視認性)**」と「**快適性(休息性・環境・安心感)**」の 2 軸 | 大阪駅周辺 4 地点。**合流後滞在時間の平均**(外れ値上下 0.2% 除外): 通過型(高認知性・低快適性)= BIGMAN 前広場 **3 秒**・アトリウム広場 **7 秒**。滞在型(低認知性・高快適性)= 時空の広場 **1 分 35 秒**・カリヨン広場 **1 分 19 秒**。BIGMAN 前は寄りかかり **41.8%(18/43 件)**・スマホ利用 **72%**、カリヨン広場は座位 **61.4%(27/44 件)** | **G6**。**目印は「見つけやすさ(認知性)」の軸であって「居心地(快適性)」の軸ではない**。**合流したら 3〜7 秒で去る** |
| **岡田・横山 2019**「駅における待ち合せ時の滞留傾向とその変遷に関する定量的研究」人間・環境学会誌(MERA)22(1):29([doi:10.20786/mera.22.1_29](https://doi.org/10.20786/mera.22.1_29))**[実読]** PDF 1 頁 | 「これまで、駅における待ち合わせを目的とした滞留行動を扱ってきた研究において共通して述べられてきたことは、『**いかに待ち合わせ相手とすばやく合流できるかが重視される**。』ということである」/ 方法「図面上に設定した位置からの可視領域を求め、空間の**視認性**の高低を定量的に捉える」/ 結果「**視点からの視領域が重なる部分が最も滞留人数が多く**」/ 考察「**視認性の高い空間であり、かつ人の流動から離れている場所は滞留を喚起する**」/ 「ガラス面は滞留場所として好まれない。ディスプレイは、発光による不快感や見る人の多さから、滞留が起こりにくい」 | 都内の複数駅を目視調査(1 回目とその 5 分後の計 2 回)。**具体的な倍率・視点間隔・壁からの離隔は PDF の埋め込みフォントが壊れており抽出できなかった**(親が原典で再確認)。参考文献に「中丸:駅改札口における待ち合わせによる滞留行動の研究(早稲田大学修士論文)」 | **G6**。**v2 は W8(視点 356,732 点 × 対象 9,592)を既に持つ** = 「目印」を POI の `cat` で決めずに **可視領域の重なりから計算できる** |
| **Lynch 1960『都市のイメージ』**。v1 リポの文献メモ `docs/lit/urban__lynch1960_image-of-the-city.md`**[二次・v1 メモ経由・原典未読]** | v1 メモ「人は都市を **5 要素(path/edge/district/node/landmark)** で心的地図化する」/ v1 メモが立てた方針「★ **landmark/node/district を hardcode しない**。空間は座標・通行可能性・POI という affordance のみ与え、『どこが landmark か』は**エージェントの移動・言及の集中から創発**させ、head/tail 則で**事後測定**(no-fingerprint 原則に完全合致)」 | **原典未読**。v1 メモが引く計算論版 = Jiang [arXiv:1212.0940](https://arxiv.org/abs/1212.0940)(INPUT 2012, 111-121)**[実読・抄録]**「the image of the city can be **quantitatively derived automatically** using computer technology and geospatial databases of the city」/ キーワード「head/tail division rule, legibility, imageability, power law, scaling, and hierarchy」 | **G6 への反対材料**。v1 では「目印を宣言しない」で合意していた。**G6 (a) = landmark 68 件を目印に昇格 は v1 方針の逆** = 覆すなら宣言が要る |
| **渋谷ハチ公前の待ち合わせ実証** | — | **J-STAGE を「ハチ公 渋谷」で検索(全 126 件)したが、待ち合わせ行動の実証研究は 1 件も無い**(上位は動物文化史・秋田犬ブランド・駅前広場の屋外広告の注視特性)。[残務台帳が「取得不能候補」とした見立て](../design/v2-schedule-and-research-plan-2026-09.md) は **本調査でも覆らなかった = 「無い」** | — | **G6**。ハチ公固有の値は使えない。使えるのは **大阪駅 4 地点** と **駅一般** の値 |

**問い6 の判定**: **「目印を待ち合わせ場所にする」ことの日本の実証は 2 本あり、どちらも「目印そのもの」ではなく「視認性(可視領域)」を説明変数にしている**。そして **2026 年の一次資料が「スマホ普及で目印を頼りに捜索する過程は大幅に削減された」と明言**している。**渋谷ハチ公前の実証は無い**。

---

## §2 G1〜G7 への含意(**推奨は書くが決定は親とユーザー**)

### A. G1(セル内位置の表現)— 先行は割れている。決め手は「距離の関数を持っているか」

- **4 系統すべてが実在**(§1.1)。**v2 の現状(ノード量子)は GATSim と同型で、先行と比べて欠陥ではない**。
- ただし v2 は GATSim と違い **会話・近接・傍受・被注視**を持ち、この 4 つは **すべて距離の関数として設計書に書かれている**(知覚契約 §3・§4)。**距離の関数を持ちながら距離を持たない**のが現状の不整合であって、「先行がやっているから」ではない。
- **先行は近接半径を論文に書いていない**(GA の `preset visual range`・CitySim の `co-located`)。**v2 が d_talk・傍受 r・近接 k を数値で宣言すれば、この点では先行より明示的**になる=第一目標(現実整合アンカー台帳)と整合。
- **推奨(サブ)**: **G1 (b) 辺上連続**に賛成。理由は「先行がやっているから」ではなく **§2-C の再計算(密度段階が全部 LOS A の内側)がセル集約のままでは群衆の効果が出ないことを示す**から。

### B. G2(移動速度)— **アジェンダの「年齢係数(1.00〜1.60)」は読み違い。文言の修正が要る**

- **確定した事実**: 1.00〜1.60 は **希望歩行速度そのもの(m/s)の幅**(STRC 2018 Table 2 に「Desired walking speed vd [m/s] 1.00 / 1.60」と逐語)。**repo の設計書・答申も一貫して m/s と書いている**。「年齢係数」という語は **C9 アジェンダ G2 が初出**。
- **掛け算にすると** 1.34 × [1.00, 1.60] = **1.34〜2.14 m/s = 4.8〜7.7 km/h**[再計算]。7.7 km/h は走行域で、Weidmann の ρ_max = 5.4 とも整合しない。
- **推奨(サブ)**: G2 (b) の文言を「**自由速度を 1.00〜1.60 m/s の個体分布から引く(Weidmann の 1.34 m/s は分布の代表値・幅は Bosina & Weidmann 2017 由来)**」に直す。**年齢による配分はやらない**——年齢別表の一次資料が取れていない(§3-1)。年齢を使うなら **R-7 に「年齢別歩行速度表の一次取得」を新しい行として起こす**。
- **速度の含意**[再計算]: 1 tick = 60 s。1.34 m/s → **80.4 m/tick = 平均辺長 37.8 m の 2.13 本**。現状の 1 node/tick は **0.63 m/s = 2.27 km/h**。つまり **(b) を入れると移動は約 2.1 倍速くなる**(1.00 m/s なら 1.59 本・1.60 m/s なら 2.54 本)。**在圏の形が動く = 再受入が要る**というアジェンダの判断は正しい。
- **下振れの証拠**: 鉄道総研 2016 が「**約 40 年前の推定式より低い傾向**」と一次で言っている。**感度腕「自由速度 ×0.8」の根拠**になる(数値が無いので腕の値は expedient)。

### C. G2/G8/G10 の連動 — **いまの密度段階は 7 段すべて Fruin LOS A の内側**[再計算]

| v2 の段(人/セル) | 人/m²(÷ 4,206 m²) | Fruin LOS | Weidmann v(ρ) |
|---:|---:|---|---:|
| 1 | 0.0002 | A | 1.340 m/s |
| 20 | 0.0048 | A | 1.340 |
| 150 | 0.0357 | A | 1.340 |
| 400 | 0.0951 | A | 1.340 |
| **1,000(最上段)** | **0.238** | **A** | **1.339** |
| (1,811) | 0.431 | **C の入口** | 1.317 |
| (3,018) | 0.718 | C の上端 | 1.207 |
| **14,000(C7 実測の最混雑セル)** | **3.33** | **F** | **0.265** |

- **含意 1**: 最上段(1,000 人/セル)に達しても **Weidmann 式の減速はほぼゼロ**(1.340 → 1.339 m/s)。**G2 (b) の「密度で減速」は、段階そのものを触らなければ実質 no-op**。
- **含意 2**: 逆に C7 実測の最混雑セル(1.4 万人)では **0.265 m/s** = いまの 1 node/tick(0.63 m/s)の **半分以下**。**速度の効果は中間ではなく両端に出る**。
- **含意 3**: U15-4 の LOD 閾値(LOS C 相当)は **1,811〜3,018 人/セル**[再計算]。**この線を跨ぐセルが何個あるかを測るのが G10 の先決**。
- **推奨(サブ)**: G2 (b) を入れるなら、同じ回で **密度段階の刻みを LOS 境界に合わせ直す**か、少なくとも **「いまの刻みでは減速が効かない」ことを受入表に書く**。刻みを触るのは決定項なので **ユーザー判断**。

### D. G4(「見る」= 注意の焦点)— **1 欄で足りるが「外れる条件」が要る**

- **Itti 1998 の FOA は 1 個の位置**、**UE の Perception も対象 1 個(Dominant Sense で決める)**。**「注意の焦点 1 欄(4 B/体)」は先行と同じ粒度**。
- **両先行とも「外れる」機構を持つ**: Itti = **IOR(注意した領域を 500–900 ms 抑制)**、UE = **Lose Sight Radius(取得半径より広い喪失半径)** + **Max Age(刺激の寿命)**。**G4 案には外れる条件が書かれていない**。
- **推奨(サブ)**: G4 (b) に **2 つの要素を足す** — ① **焦点の寿命**(何 tick で消えるか。UE の Max Age 型) ② **喪失距離 > 取得距離**(ヒステリシス。UE の Sight/Lose Sight 型)。どちらも expedient として宣言し、① は G11 の `TARGET_GONE` と同じ場所で判定できる。**バイトは焦点 4 B + 寿命 1 B = 5 B/体**(390,067 体で **1.95 MB**[再計算]・M2 の残枠 103 B/体に対し無視できる)。
- **注意**: Itti の IOR は **ms 単位**、v2 の起床不応期は **分単位**で **4 桁違う**。借りるのは **形(注意したら戻りにくい)だけ**で、値は借りない。

### E. G3(「近づく」)— 先行から足せるのは「到達距離」でなく「終了条件」

- 「approach を動詞として持つ LLM エージェント」の一次資料は本調査では当たっていない(§1.1 の 4 本はいずれも `move(poi)` 型)。
- ただし **UE の「Auto Success Range from Last Seen Location」**(一度見た対象は指定距離内なら見えたことにする)は、**「近づく」途中で対象を見失う問題**への産業側の答え。**G11 の `TARGET_GONE` を出す前に「最後に見た位置へ向かう」猶予を置く**形が先行にある。**推奨は書かない**(G3 の選択肢の外)。

### F. G6(目印)— **実証は「目印」でなく「視認性」を説明変数にしている。しかも現代は弱まっている**

- **岡田・横山 2019**: 待ち合わせの滞留は **可視領域の重なり × 流動からの距離**。**v2 は W8 を既に持つ**ので、**「目印かどうか」を POI の `cat` で決めずに可視領域の重なりから計算できる**。これは **v1 の Lynch メモの方針(landmark を hardcode しない・事後測定する)とも一致**する。
- **一宮・松村 2026**: **待機者の 8 割以上がスマホを操作**・「かつてのランドマークを頼りに捜索する過程は大幅に削減された」。**v2 の DT は現代のスナップショット**なので、**「目印を見つけて合流する」機構を強く入れると現実より古い渋谷になる**。
- **合流後の滞留は 3〜7 秒**(高認知性・低快適性の広場)。**待ち合わせ成立後に在席が続く前提を置くと現実より長くなる**。
- **推奨(サブ)**: G6 は (a) を採るとしても、**「目印性」を POI 属性でなく W8 の可視領域集計から出す第 2 案を並記**して、どちらが v1 の no-fingerprint 方針と整合するかをユーザーに選ばせる。**OSM artwork/memorial の取得 (b) は、この 2 本から見ると優先度が低い**(目印の網羅より視認性の計算の方が効く)。

### G. G7(会話・傍受が届く範囲)— **2 m は裏づけられる。密度で縮める根拠は無い**

- **2 m は、見知らぬ人への選好距離 1.35 m(42 か国・N = 8,943)より広く、Hall の社会距離の上端(二次再掲で 210 cm)とほぼ同じ**。**会話している二人の実距離をほぼ全部覆う** = 偽陰性が出にくい側の設定。
- **[再計算] 半径 2 m の円内の人数** = ρ × 12.57 m²。1,000 人/セル(0.238 人/m²)で **3.0 人**、LOS C 上端(0.718)で **9.0 人**、C7 最混雑(3.33)で **41.8 人**。**近接上位 k(疎3/中2/密1)と桁が合うのは疎〜中**で、**密では候補が 40 人を超える** = **k の切り方が効くのは密側**。
- **会話半径を密度で ×0.42 する根拠は本調査では見つからなかった**(屋外・群衆での会話距離の実測が無い)= **expedient のまま**。
- **推奨(サブ)**: G7 (b) に賛成。**ただし d_talk は「成立」と「離脱」で別の値にする**(UE の Sight/Lose Sight 型)。同じ 2 m で判定すると境界上の二人が毎 tick 会話を作っては壊す(D-49 が「近接入替は最大の暴発源」と名指ししたのと同じ形)。

---

## §3 空欄(本調査で埋まらなかったもの)

1. **Weidmann 1993 原典**。ETH Research Collection の記録ページは生きているが **bitstream が HTTP 500**、旧 e-collection は **DNS 不達**。→ **年齢別歩行速度表・γ の導出は未確認**(γ の値自体は Kretz 2015 で式番号つきに取れた)。
2. **Bosina & Weidmann 2017(Physica A 468:1-29)本文**。有料。**1.00〜1.60 m/s の中身(何本の研究の何パーセンタイルか・年齢別の内訳があるか)は未確認**。STRC 2018 Table 2 の転記までが本書の根拠。
3. **鉄道総研 2016 の数値**。公開ページに m/s も人/m² も無く、**「約 40 年前の推定式」が何式かも書かれていない**。R-7 の該当行は **向きだけ埋まり数値は空欄のまま**。
4. **知覚契約 §3/§4 が引く出典の一次確認**: Fotios 2014/2015(注視 480 ms・中央値 10.3 m)・Jovancevic-Misic & Hayhoe 2009・Cowan 2001 は **本調査では当たっていない**。**「Itti & Koch が否定したのは線形和」という逐語は 1998 年 TPAMI 版には無い**(親要確認)。
5. **Kim, Van Velsen & Hill 2005**(仮想人間の動的知覚注意)は **出版社有料・抄録も削除**で本文未取得。Hill 1999 の原典も未取得。
6. **Hall 1966 原典**。二次(Sorokowska 2017)の再掲では **社会距離 122-210 cm・公衆距離 210 cm 超**で、依頼文の「社会 3.6 m」(原典の 4-12 ft)と **帯の切り方が違う**。**どちらが原典の記述かは未確認**。
7. **屋外・群衆での会話距離の実測**。見つからなかった。**会話半径の密度依存(×0.42)の外部根拠は無いまま**。
8. **森田ほか 2004 表 3 の個々の数値**。PDF が画像スキャン + OCR 層で区間別の対応が壊れている。**範囲(密度 0.85〜4.37 人/m²・速度 0.03〜1.8 m/s)までしか保証できない**。
9. **岡田・横山 2019 の数値**。埋め込みフォントが壊れており、視点間隔・壁からの離隔・滞留密度の倍率が抽出できない。**質的な結論(視認性 × 流動からの距離)のみ**。
10. **渋谷ハチ公前の待ち合わせ実証**。J-STAGE 全 126 件に該当なし = **「無い」**。
11. **Generative Agents の `preset visual range` の数値**。本文に無く、付録 A/B が取得できなかった。
12. **LLM エージェント系で近接距離を数値で宣言した先行**。4 本すべてで **見つからなかった**。
13. **ホーム滞留容量(R-8 ④)**。本調査の対象外だが、J-STAGE 検索の過程で「駅昇降施設の最大捌け人数」(土木学会論文集 D3, [doi:10.2208/jscejipm.69.I_595](https://doi.org/10.2208/jscejipm.69.I_595))が候補として見えた。**本書では読んでいない**。

---

## §4 [lit README](lit/README.md) の索引に足す行(**本書では追記しない** — 親が入れる)

| メモ | 分野 | 一次確認 | 何のために引くか |
|---|---|---|---|
| [crowd__bosina-weidmann2018_fd-generic-model](lit/crowd__bosina-weidmann2018_fd-generic-model.md) | 歩行者動力学 #18 / 人間移動科学 #3 | B(サブ実読・第206・親未確認) | **「1.00〜1.60」は年齢係数でなく希望歩行速度の m/s 幅**(Table 2 逐語)・体幅/反応時間/Hall 親密距離を 1 表で持つ |
| [crowd__kretz2015_kladek-formula](lit/crowd__kretz2015_kladek-formula.md) | 歩行者動力学 #18 | B(サブ実読・第206・親未確認) | **Weidmann の速度−密度式を式番号つきで**(v_f 1.34・γ 1.913・ρmax 5.4)= R-7 の γ 空欄が埋まる |
| [crowd__morita2004_kobe-luminarie](lit/crowd__morita2004_kobe-luminarie.md) | 歩行者動力学 #18 | B(サブ実読・第206・親未確認) | **日本の屋外・多方向流の実測**(U15-5 が「実験室データに無い」と宣言した穴)・安全密度 2〜3 人/㎡ |
| [percep__itti1998_saliency-foa](lit/percep__itti1998_saliency-foa.md) | 知覚心理学 #5 / 認知科学 #12 | B(サブ実読・第206・親未確認) | **注意の焦点 = 1 個の状態**・**IOR 500–900 ms**・proximity preference = G4 の形の原型 |
| [gameeng__unreal_ai-perception](lit/gameeng__unreal_ai-perception.md) | ゲームエンジン工学 #30 | B(サブ実読・公式ドキュメント・第206・親未確認) | **取得半径と喪失半径を分ける**・刺激の寿命(Max Age)・Dominant Sense = G4/G7 の「外れる条件」 |
| [urban__okada2019_station-waiting](lit/urban__okada2019_station-waiting.md) | GIScience #9 / 認知科学 #12 | B(サブ実読・第206・親未確認) | **待ち合わせの滞留位置 = 可視領域の重なり × 流動からの距離** = W8 で計算できる |
| [urban__ichimiya2026_meeting-place-amenity](lit/urban__ichimiya2026_meeting-place-amenity.md) | GIScience #9 / 時間利用研究 #4 | B(サブ実読・第206・親未確認) | **認知性 × 快適性の 2 軸**・**合流後滞在 3〜7 秒 vs 1 分 19〜35 秒**・**待機者の 8 割以上がスマホ** |
| [psych__sorokowska2017_interpersonal-distance](lit/psych__sorokowska2017_interpersonal-distance.md) | 人格心理学 #13 / 会話分析・語用論 #15 | B(サブ実読・第206・親未確認) | **見知らぬ人 1.35 m・知人 0.92 m**(N = 8,943・42 か国・**日本は含まれない**)= G7 の 2 m の裏づけ |

**作らなかったメモ**(§1.1 の表で足りると判断): Generative Agents・AgentSociety・CitySim・GATSim の 4 本。**位置の型以外は C9 の決定に効かない**ため。親が別件で要ると判断したら起こす。
