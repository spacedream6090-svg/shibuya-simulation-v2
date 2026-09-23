# 未決B「場所セル(prefix共有単位)の粒度」判断根拠リサーチ

<!-- hdr:v1 -->
- **分野**: 地理情報科学 #9 / 計算機科学(並列・決定論) #28 | **重要度**: P1(親判断・2026-09-15 第191)
- **一次確認**: **B** = 出典あり・空欄を明示(残務台帳へ写し済みまたは要写し) — 出典痕跡 47 件。空欄節あり
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **分野地図**: [v2-discipline-map.md](v2-discipline-map.md)

対象: docs/design/v2-perception-contract.md §5 未決B / §2.2 B2・B4 / §10。
作成: 2026-09-04。実行=Opus 5サブ。**リポ書き込みなし・スクラッチのみ**。

---

## ① 結論(冒頭10行)

1. **第1候補=100m格子(139セル)を維持**。ただし理由は「キャッシュが100mを要求するから」ではない。
2. **キャッシュ経済は粒度をほとんど選ばない**。実測の傾き(セル数8→512で−8%=**1倍化あたり約−1.3%**)を139→556に外挿すると**約−2.7%**。独立に立てた解析モデルの上界でも**−8%**。100m vs 50mの計算代償は**3〜8%**でしかない。
3. **忠実度も粒度をほとんど選ばない**。東京の街区は1辺30m級(未検証)〜109m(1町)で、**100mでも50mでも正方セルは必ず街区を跨ぐ**=可視物集合の不均質は粒度でなく**単位の型**の問題。50mにしても「代表点の可視集合」問題は解けない。
4. したがって決め手は**較正コスト**: B2静的言語化はセルごとに人手較正(R3-6a)が要る。139→556は**画像・VLM・人手が4倍**。9/24前のPhase 2では139が唯一現実的。
5. 100mには独立した現実側の裏付けがある: **Gehlの社会的視野の上限=100m**(人の動きが見える限界)・**日本の伝統街区単位1町=109.09m**・**H3 res10=15,048m²(正方換算122.7m)**・**UEレプリケーショングラフの事実上の既定セル=10,000uu=100m**・**UE5 World Partition既定=128m**。100m級は現実側と実装側が独立に収束している帯域。
6. **反証側も明示**: Rosserら(2017)は150m格子より**街路ネットワーク単位が hit rate で20〜25%優位**、機構は「同一セル内で高リスク街路が低リスク街路に打ち消される」生態学的誤謬。Weisburdの犯罪集中則は**street segmentが実証済みのミクロ地点単位**。Barkerのbehavior settingも不定形。**「場所」の人間側の正しい単位は正方形ではない**——これは押さえた上で先送りする決定である。
7. よって推奨は**「100m格子で凍結、ただしセルIDを place_id という抽象にして、後で blockface(格子∩街区)/道路セグメントへ差し替え可能にする」**。粒度でなく**単位型**を将来の可変軸に置く。
8. **BN-1の設計を変えるべき**。実測でセル数の感度が弱いのは、**生存セル集合が総セル数でなく並行度(c=64)で律速される**ため(§③で導出・実測−8%を再現)。BN-1の軸は「セル数」でなく「**バッチあたりdistinctセル数 d**」「**セル節長 B_cell**」「**Zipf指数**」であるべき。
9. **契約書の数値矛盾を1件発見**: ベンチはセル節=200tokで測ったが、契約§2.2のセル依存部は**B2 350+B4 150=500tok**。**2.5倍**。ベンチのセル数感度はこの分だけ楽観側。BN-1はB_cell=500で測り直すこと。
10. **設計上の別の衝突を1件発見**: 100mセルは平均約2,878体を含む(40万体/139)。B4の「行列・人だかり・グループ上位k」を100mセル共有ブロックに置くのは意味が薄い(構造物の知覚スケールはGehlの25m級)。**prefix共有単位(大きくしたい)と構造物報告単位(小さくしたい)は要求が逆**。§④に階層化案。

---

## ② ユーザーがまず読む大枠

**問いの立て方が実はずれている。** 「100mか50mか」は、計算側でも忠実度側でも差が小さい低リスク決定だった。リサーチで出てきた本当の分岐は3つ。

- **分岐A(今回の推奨=100m)**: 粒度そのもの。計算3〜8%、忠実度ほぼ差なし、較正コスト4倍。→ 100m。ほぼ自明。
- **分岐B(先送りを明示的に決める)**: 正方格子 vs 不定形(街区面/道路セグメント)。**先行研究は不定形側に軍配**(Rosser 20-25%優位・Weisburd・Barker)。しかし実装・ベンチ再現性・ablation軸としては格子が圧倒的に楽。→ 今は格子、ただし `place_id` 抽象で退路を残す。ここを「知らずに格子にした」のか「知って格子にした」のかが、後で台帳に効く。
- **分岐C(粒度より効く未測定レバー)**: **セルアフィニティ・ルーティング**(同一セルの起床を同一GPUに寄せる/起床キューをセル単位でバッチ化)。DP7が線形(100.2-100.4%)でNUMA中立と実測済みなので、ルーティング側の自由度は丸ごと空いている。粒度で取れるのが数%なのに対し、ここは**セル節のヒット率を直接押し上げる**。ベンチ第3段の残測定「セッションアフィニティ」がこれ。→ **BN-4として新設を推奨**。

つまり「未決Bは100mで閉じてよい。ただし閉じ方を2つ足す(place_id抽象・BN-1の軸差し替え)。そして節約の本命はBN-4に移す」というのが本答申。

---

## ③ 問い1-6の証拠

### 問い1: 現実の「場所」の粒度

**(1-a) 歩行者が「同じ場所にいる」と感じる距離——Gehlの社会的視野**

Jan Gehlの「社会的視野(social field of vision)」は上限**100m**で、「人が動いているのが見える」限界。**50〜70m**で個人が誰か分かる(髪の色・特徴的な体の動き)。**22〜25m**で表情と主要な感情が読める。300〜500mでは人か動物か茂みかの区別しかつかない。
出典(実読): [Planetizen "How the 'Social Field of View' Impacts Street Life"](https://www.planetizen.com/news/2023/09/125446-how-social-field-view-impacts-street-life) ※ページ本体は403で読めず、**検索結果本文経由の引用**。原典は Gehl, *Cities for People* (2010)。**原典は未読**。

含意: **100mセル=「同じ場所にいる人が互いに見える」上限とちょうど一致**。ただし正方100mセルの対角は**141.4m**でこの上限を超える。50mセルの対角は70.7mで「個人が誰か分かる」帯に収まる。→ 忠実度で50mを推す唯一の定量的根拠はこれ。ただし契約書はB5に「知人∩セル+近接他者上位3-4」を個体ブロックとして持つので、共在の主張はB2/B4だけから来ていない=この論拠の重みは限定的。

**(1-b) proxemics(参考・スケールが2桁小さい)**

Hallの4帯: 親密 <0.45m / 個人 0.45-1.2m / 社会 1.2-3.6m / 公共 >3.6m。
出典(検索結果本文): [EBSCO Research Starters: Proxemics](https://www.ebsco.com/research-starters/social-sciences-and-humanities/proxemics)。**原典Hall未読**。
含意: 会話・傍受(契約§3の可聴r≈2m)のスケールであって、場所セルのスケールではない。**場所セルをproxemicsで決めてはいけない**。

**(1-c) isovist/space syntaxの空間単位**

isovist=ある視点から直接見える領域。凸空間(convex space)・軸線・セグメント・isovistが space syntax の幾何実体。isovist は Tandy(1967)提案・Benedikt(1979)拡張。
出典(検索結果本文): [Batty, "Exploring isovist fields", EPB 2001](https://journals.sagepub.com/doi/10.1068/b2725) / [Springer: Typification of the Pedestrian Surrounding Space](https://link.springer.com/chapter/10.1007/978-3-642-19789-5_14)。**本文未読(要旨レベル)**。

**重要な反証データ(実読・要旨全文)**: Ericson, Chrastil & Warren (2021) *"Space syntax visibility graph analysis is not robust to changes in spatial and temporal resolution"*。VRとモーショントラッキングで30のsyntactic測度と高解像度歩行軌跡を突き合わせ、**10段階のグリッド解像度**でダウンサンプル。要旨(Semantic Scholar経由で全文引用取得):
> "Overall, correlations declined with increasing grid resolution and were sensitive to data transformations. Moreover, simulations revealed spuriously high correlations (e.g. R² = 1) with sparsely sampled data (<23 locations). These results strongly suggest that syntactic–behavioral correlations are not robust to changes in spatiotemporal resolution..."

出典: [DOI 10.1177/2399808319897624](https://journals.sagepub.com/doi/10.1177/2399808319897624)(要旨はSemantic Scholar APIで実読・本文PDFは403で未読)。
※検索スニペットに「5m→3mでR²が.456→.625に上昇」とあったが**本文未読・未検証**。
含意: **空間解像度の選択は結果を動かす=mechanismではなくexpedient**。契約§8の「ablation予約: 場所セル粒度」は正しい判断。粒度を選んだ後、必ず感度試験が要る。

**(1-d) behavior setting(不定形単位の理論的根拠)**

Barkerのbehavior setting=「時間的・空間的な限界を持つ社会物理的統合システム」で、人の行動の最良の予測子は個人特性でなく**setting(場所・時刻・活動)**。学校・公園・診療所・店・コミュニティセンターが心理学的分析の正当な単位になった。「behaviour settings can provide a clear boundary」。
出典(検索結果本文): [Phil. Trans. R. Soc. B 379:20230283 "Reclaiming behaviour settings"](https://pmc.ncbi.nlm.nih.gov/articles/PMC11338576/) / [Springer "Behavior Setting"](https://link.springer.com/rwe/10.1007/978-3-031-70581-6_505-1)。**本文未読(要旨・検索本文レベル)**。
含意: 人間側の「場所」は店・広場・街路であって正方形ではない。契約の`place_id`抽象化の理論的裏付け。

**(1-e) 街区寸法**

| 単位 | 寸法 | 出典 | 確度 |
|---|---|---|---|
| 日本「1町」 | **60間=109.09m**(11町=1200m) | [ja.wikipedia 町(単位)](https://ja.wikipedia.org/wiki/町_(単位)) **実読** | 高(単位定義) |
| 江戸期の町(街区) | 約109×109m | [janejacobsjapan(ブログ)](https://janejacobsjapan.com/2018/09/08/hierarchy-of-japanese-streets-version-2/) 検索本文経由 | 低(二次・ブログ) |
| 東京23区の最頻街区面積 | **800〜900m²**、正方換算1辺**約29.2m** | [JPSJ 92, 104801 (2023) Akiba, Wang, Sato, Shima](https://journals.jps.jp/doi/10.7566/JPSJ.92.104801) | **未検証**(本文もPDFも403・DOI/著者/誌はCrossrefで実読確認・数値は検索スニペットのみ) |
| 東京の道路 | 最広=外堀通り45m、**86%が幅5m以下** | 同上スニペット | **未検証** |
| バルセロナEixample | 113m角(隅切り20m) | [WhiteClouds/Grokipedia系](https://www.whiteclouds.com/how-big-is/how-big-is-a-city-block/) 検索本文 | 中(定説) |
| ポートランド | 260×260ft = **79×79m** | 同上 | 中 |
| マンハッタン | 約80×270m | 同上 | 中 |
| 京都 | 約60×120m | 検索本文 | 低 |

**渋谷駅周辺の街区は何m角が典型か → 一次データでは特定できなかった。** Web上に渋谷区限定の街区面積分布は見つからず。使える代理値は上表のみ。
**推奨(1時間作業)**: PLATEAU(渋谷区はLOD2整備済)またはOSMの道路中心線から街区ポリゴンを生成し、bbox 2.0×1.9km 内の街区面積分布(中央値・IQR・正方換算1辺)を**自前で1回測る**。これは推測でなく実測で決められる量であり、未決Bの唯一の「渋谷固有」の入力になる。

**(1-f) 商業集積の単位(渋谷実データ)**

- 渋谷センター街「メイン通り」は**約350m**([Wikipedia 渋谷センター街](https://ja.wikipedia.org/wiki/渋谷センター街) 検索本文 / [TEMPOLY](https://magazine.tempoly.jp/area/centergai-hanya/))。→ **100m格子で3.5セル、50m格子で7セル**にまたがる。「センター街にいる」という人間の場所感覚は1セルに収まらない。
- センター街公式データ(**実読**): 渋谷駅からセンター街への通行は**平日約5〜6万人/日・休日約7〜8万人/日**。スクランブル交差点は**1回の青信号で多い時約3,000人**。渋谷駅乗降(2014)320万人超/日(JR東74万+東急115万+メトロ99万+京王井の頭33万)。
  出典: [センター街データ](https://center-gai.jp/about/data/) **実読**
- スクランブル交差点の通行量には諸説: 平日26万・休日39万(2014渋谷再開発協会の流動計測に基づく算定)、多い時1日50万。出典: [ja.wikipedia 渋谷スクランブル交差点](https://ja.wikipedia.org/wiki/渋谷スクランブル交差点) 検索本文経由・**原典未読**。

---

### 問い2: 先行実装のセルサイズ

| 系 | セル/ゾーン単位 | 数値 | 出典・確度 |
|---|---|---|---|
| **UE ReplicationGraph GridSpatialization2D** | 空間セル | `float SpacialCellSize = 10000.f;`(UE単位1uu=1cm → **100m**)、`SpatialBias = (-150000, -200000)` | [locus84/LocusReplicationGraph の LocusReplicationGraph.h](https://raw.githubusercontent.com/locus84/LocusReplicationGraph/master/Source/LocusReplicationGraph/Public/LocusReplicationGraph.h) **raw実読**。EpicのShooterGame例の移植版。**Epic公式の既定値は公式ドキュメントに記載なしを確認**([UE5.7 Replication Graph doc](https://dev.epicgames.com/documentation/en-us/unreal-engine/replication-graph-in-unreal-engine) を実フェッチ→セルサイズの記載なし)。**確度: 中(コミュニティ移植の実コード。Epic本体ソースは未読)** |
| **UE5 World Partition** | ストリーミングセル | 既定 **12800uu = 128m**、ロード範囲 25,600cm=256m | [StraySpark(ブログ)](https://www.strayspark.studio/blog/ue5-world-partition-deep-dive-streaming-hlod) 検索本文経由。**確度: 低-中(二次・公式ドキュメント未確認)** |
| **Photon Fusion 2 (AoI)** | Interest Cell | **Cell Size = 32m**(16mにすると同期体積が65%減)、AoI Grid既定 **1024 cube**、Shared Modeでは変更不可 | [Photon Fusion 2 doc](https://doc.photonengine.com/fusion/v2/technical-samples/fusion-multi-peer-area-of-interest) 検索本文経由(ページ本体はCloudflareで取得不可)。**確度: 中** |
| **Second Life** | Region(=1シミュレータプロセス) | **256×256m = 65,536m²**、垂直4096m、約29,000リージョン、1サーバに4リージョン以上 | [Second Life Wiki: Introduction To SL Geography / Grid Map And Dimensions](https://wiki.secondlife.com/wiki/Introduction_To_Second_Life_Geography) 検索本文経由。**確度: 高(定説)** |
| **空間ハッシュ(群衆・粒子)** | セル = 相互作用半径 | セル辺=平滑長h、または全次元で2h(近傍が自セル+隣接26セルに必ず入る) | [Zhyhallo, SCITEPRESS 2024](https://www.scitepress.org/Papers/2024/124157/124157.pdf) ほか、検索本文経由。**確度: 中(標準的な設計則)** |
| **H3** | ヘクス | res 8=**737,327.598 m²**(辺0.531km) / res 9=**105,332.513 m²**(辺0.201km) / res 10=**15,047.502 m²**(辺0.0759km) / res 11=**2,149.643 m²** | [h3geo.org Tables of Cell Statistics](https://h3geo.org/docs/core-library/restable/) **実読** |
| **Uber の運用res** | サージ料金 | res **8** が通例(約0.5km²・「1〜2ブロック」相当) | ブログ二次(akshayghalme/Medium)経由。**確度: 低(公式blogでは未確認)** |
| **日本の標準地域メッシュ** | 3次=**約1km** / 4次(1/2)=**約500m** / 5次(1/4)=**約250m** / 6次(1/8)=**約125m** / 10分の1細分=**100m** / 20分の1=**50m** | [e-Stat 地域メッシュ統計](https://www.e-stat.go.jp/pdf/gis/chiiki_mesh_toukei.pdf) / [ESRIジャパン 標準地域メッシュ](https://www.esrij.com/gis-guide/gis-other/mesh/) 検索本文経由。**確度: 高(制度定義)** |
| **人流データの実務標準** | 基地局系は**空間250〜500m・時間1時間**が代表仕様。モバイル空間統計は全国500m・**都心部125m**。国交省人流オープンデータは**1kmメッシュ** | [ESRIジャパンblog](https://blog.esrij.com/archives/69141) / [e-Stat モバイル空間統計](https://www.e-stat.go.jp/bigdataportal/dataintro/130) / [国交省](https://www.mlit.go.jp/tochi_fudousan_kensetsugyo/tochi_fudousan_kensetsugyo_fr17_000001_00006.html) 検索本文経由。**確度: 中-高** |
| **都医学研 滞留人口モニタリング** | **500mメッシュ**・1時間単位。渋谷センター街・歌舞伎町等の主要繁華街 | [東京都医学総合研究所](https://www.igakuken.or.jp/r-info/monitoring.html) **実読** |
| **MATSim** | リンク(施設は個別建物・区画) | 活動地点はゾーンでなく個別建物/区画。実務では**500m超のリンクを分割・20m未満の連結リンクを統合**(AToM/Melbourne) | [AToM arXiv:2112.12071](https://arxiv.org/pdf/2112.12071) 検索本文経由。**確度: 中** |

**収束の観察**: ゲーム側のAOIセルは **32m(Photon) / 100m(UE RepGraph) / 128m(UE5 WP) / 256m(SL region)**。都市データ側は **100m/125m/250m/500m**。H3 res10 = 15,048m² = **正方換算122.7m**。**100〜130mが両側の共通帯**。139セル(100m)はこの帯の下端に位置し、外れ値ではない。

---

### 問い3: キャッシュ経済

**(3-a) 実測(社内ベンチ・docs/bench/README.md 実読)**
- 8B INT8 KVプール **≈82.9k tok**。無キャッシュ時1req=1,628tok → 実効並行**≈49**。
- 共有1,000tokで1reqのKVが628tokに縮み実効並行**49→132**、ヒット率実測**67.4%**(理論66.7%)。
- 現実的階層prefix(全体600+種別200×10+セル200×N+個体500=1,500tok)で **セル数8→512の感度は−8%のみ**。セル128超は種別止まりと同等(LRU追い出しの定常状態)。
- **Zipf混雑は一様より+6〜8%**(現実の渋谷型は保守側でなく有利側)。
- 並行度の膝 **c=64/GPU**(KV使用率0.58)。c128でKV1.00に張り付きTTFTのみ悪化。
- DP7線形 **100.2-100.4%**、NUMA効果ゼロ。

**(3-b) なぜセル数の感度が弱いのか——機構の導出 [計算・本答申の主張]**

LRUの生存セル集合は**総セル数でなく、バッチ内で触られるdistinctセル数**で決まる。到着が一様ランダムなら、並行度 c=64 のバッチが N セルから引く distinct セル数の期待値は

  E[d] = N · (1 − (1 − 1/N)^c)

| N(セル数) | E[d] @c=64 |
|---|---|
| 8 | 8.0 |
| 32 | 27.8 |
| 128 | 50.5 |
| **139(100m)** | **51.4** |
| 512 | 60.3 |
| **556(50m)** | **60.5** |

**Nを64倍(8→512)しても distinct は7.5倍にしかならず、64で飽和する。** これが「セル数感度が弱い」実測の機構。→ **総セル数は支配変数でない。支配変数は d(=並行度と到着局所性)**。

検算: バッチあたりprefillトークン量 ≈ 全体600 + 種別2,000 + **E[d]×B_cell** + 64×500(個体)。B_cell=200で N=8 → 36,200 tok、N=512 → 46,660 tok。比1.29 → モデルは**−22%**を予測、実測は**−8%**。**モデルは約2.6倍の過大予測**(理由の候補: デコード時間による希釈、chunked prefillの重なり、バッチ間のLRU残存)。→ **モデルは方向は当たるが倍率は当たらない。以下の外挿は幅で述べる。**

**(3-c) 100m(139) vs 50m(556) の代償 [計算]**
- **実測傾きからの外挿(推奨値)**: 8→512は6ダブリングで−8% ⇒ **約−1.3%/ダブリング**。139→556は2ダブリング ⇒ **約−2.7%**。
- **解析モデルの上界**: B_cell=500(契約書の実値)でE[d]差 60.5−51.4=9.1セル×500tok=4,550tok / バッチ総prefill約59,100tok ⇒ **+7.7%のprefill増 ⇒ 最大−8%**。
- **結論: 50m格子の計算代償は3〜8%**。粒度決定を支配する量ではない。

**(3-d) 契約書とベンチの不整合 [発見]**
ベンチのセル節=**200tok**、契約§2.2のセル依存部=**B2 350 + B4 150 = 500tok**。**2.5倍**。同じ論法でセル節が2.5倍になると、KVプール中のセルブロック占有も2.5倍。実測の破綻点「セル128超」は 128×200=**25,600tok がセルブロック予算の実効上界**を意味する ⇒ **B_cell=500なら実効上界は約51セル**。139セルは既にこれを2.7倍超過している(＝現状でもセル節は全ては常駐していない)。**BN-1は必ずB_cell=500で測り直すこと。**

**(3-e) 同時生存セル数の見積り法 [提案]**
- 定義: N_live(t) = LRU保持窓 T_LRU 内に1件以上の起床があったセル数。
- 推定式: E[N_live] = Σ_c (1 − exp(−λ_c · T_LRU))、λ_c = セルcの起床レート。
- λ_c の供給源: 渋谷区SHIBUYA CITY DASHBOARD(KDDI Location Analyzer・**5エリア+3街路**)、都医学研500mメッシュ、モバイル空間統計125m(都心部)。
- T_LRU の見積り: T_LRU ≈ (セルブロック予算 tok) / (新規セル節到着レート tok/s) = 25,600 / (d_new × B_cell / batch時間)。
- Zipf側の上界: 「上位20%の街路が交通の80%」(Jiang)を当てはめると **139セル中の上位28セルが起床の80%**を担う ⇒ ホット作業集合 ≈ 28×500 = **14,000tok**。KVプール82.9kに対し17%。**常駐可能**。これが実測の「Zipfは一様より+6〜8%」の説明。

**(3-f) Zipf偏りの外部証拠(実読)**
Bin Jiang, *"Street Hierarchies: A Minority of Streets Account for a Majority of Traffic Flow"*(欧州都市):
> "the 20 percent of top streets accommodate 80 percent of traffic flow (20/80)" / "the 1 percent of top streets account for more than 20 percent of traffic flow (1/20)"

出典: [arXiv:0802.1284](https://arxiv.org/abs/0802.1284) **要旨実読**。
渋谷側の一次データ: 上記センター街データ(実読)——スクランブル交差点1青信号3,000人 vs 区全体15.11km²。**単一の50m級交差点に日26〜39万人**(諸説・原典未読)。極端なZipf。

**(3-g) LLM側の一般則(参考)**
- vLLMはKVを固定長ブロック(通常16トークン)で管理し、**完全一致ブロックのみがヒット**(部分一致は不可)。CPU側blockプールが hash→block マップと**LRU free-block queue**を持つ。出典: [vLLM Automatic Prefix Caching](https://docs.vllm.ai/en/stable/design/prefix_caching/) 検索本文経由。
- SGLang/RadixAttentionは**LRU退避 + cache-aware scheduling**の併用でヒット率を上げる。「up to 5x higher throughput」。出典: [LMSYS blog 2024-01-17](https://www.lmsys.org/blog/2024-01-17-sglang/) **実読**(cache-aware schedulingの具体機構の記載はなし)。
- **含意: 「スケジューラを共有prefix認識にする」ことが先行実装で確立された定石**。これが本答申の BN-4 提案(セルアフィニティ/セル単位バッチ化)の外部根拠。
- **見つからなかったもの**: 「distinctな共有prefixの本数 × キャッシュ容量 → ヒット率」を空間的到着過程の下で定量化した先行研究。§3-bの導出は**本答申の自作**であり、先行文献の裏付けはない。

---

### 問い4: 忠実度側の代償

**(4-a) 何を失うか**
セル代表点 p_c の可視物集合 V(p_c) と、個体位置 q の V(q) の差。契約§5は「B5には位置依存の差分だけ(通常は空)」としているが、**「通常は空」は仮定であって未検証**。

**(4-b) 見積り法 [提案・追加計算コストほぼゼロ]**
契約R3-5で**2.5m可視性格子の V が全格子点について前計算済み**になる。したがって:
- 各セル c について、内部の全2.5m格子点 q の V(q) を既に持っている。
- 測る量: `add(q) = |V(q) \ V(p_c)|`(B5に足す分)、`del(q) = |V(p_c) \ V(q)|`(取り消す分)、`J(q) = Jaccard(V(q), V(p_c))`。
- セルあたり統計: median/p90 の add・del、および `E[add]×(1物あたりトークン)` = **B5に落ちる実バイト量の直接推定値**。
- 判定基準(事前登録推奨): `p90(add) × tok/物 > B5予算350tok × X%` なら粒度不足。X はユーザー決定。
- **これは推測でなく実測できる量。BN-1の前に1回まわすべき。**

**(4-c) 2解像度(2.5m可視性格子 × 100m場所セル)の整合**
- 街路キャニオンでは isovist は街路軸方向に強く伸び、建物で不連続に落ちる。isovist field は遮蔽境界で不連続(Benedikt/Battyのisovist場の基本性質・**要旨レベルの理解、本文未読**)。
- したがって V の変化を支配するのは**セル辺長でなく「セル内に何本の街路が入り、何回街区を跨ぐか」**。
- 東京の街区が1辺29m級(未検証)〜109m(1町)である以上、**100m格子も50m格子も必ず複数街路・複数街区を含む**。→ **正方格子の粒度を変えても V の不均質は解けない**。これが本答申の中心的な発見。
- **isovistの空間自己相関の相関距離(range)を数値で与えた文献は見つからなかった**(semivariogram一般論しか出ない)。→ §4-bで自前実測するしかない。

**(4-d) 解像度依存性の警告(実読)**
Ericson et al. 2021(§1-c)は、space syntaxの予測力が**空間・時間解像度に対して頑健でない**ことを実証。粗い/疎いサンプリングは相関を**見かけ上高く**することさえある(<23地点でR²=1の擬似相関)。
→ **場所セル粒度は mechanism ではなく expedient**。契約§8の ablation 予約は正しい。

**(4-e) 別の忠実度衝突 [発見]**
40万体 / 139セル = 平均 **2,878体/セル**。B4の「行列・人だかり・グループ上位k」を100mセルの共有ブロックに置くと、数千人の中の上位kになり、個体から見て**ほぼ無関係な構造物**が届く。人間側の構造物知覚スケールはGehlの**22-25m(表情)〜50-70m(個人識別)**。
**提案(階層prefix化)**: ブロック順序を B0 → B1 → **B2(セル静的・100m)** → B3 → **B4(セル動的・100m: 密度LOS/騒音段階のみ)** → **B4b(サブセル動的・25m級: 行列/人だかり/グループ上位k)** → B5(個体)。
- サブセルブロックは**全セルブロックの後**に置くので、同セル異サブセルの個体は B4 までprefixを共有し、同サブセルの個体は B4b まで共有する。ベンチ第3段が既に測った「階層prefix」の構造そのもの。
- コスト: distinct な共有ブロックが1階層増える。§3-bの E[d] 論法で見積れる(サブセル数 ≈ 16×セル数だが、E[d] は c=64 で飽和するので追加ヒット損は小さいはず)。**BN-1に軸として追加を推奨**。

---

### 問い5: 不定形セル(街区・道路セグメント) vs 正方格子

**(5-a) 不定形が優位という実証(実読・最重要)**

Rosser et al., *"Predictive Crime Mapping: Arbitrary Grids or Street Networks?"* (J Quant Criminol; PMC6979510):
- 格子側: **150m角セル**、セル内に15点をランダム配置してリスク推定。
- ネットワーク側: Ordnance Survey MasterMap の街路セグメント、**約30mごとにサンプル点**。
- 結果: カバレッジ5%で「approximately 20% more crime identified」、10%で「mean improvement of 25%」、全体で「hit rate that is **1.2 times as good** as the grid-based equivalent for most coverage levels」。「the improvement in accuracy is highly significant at all coverage levels tested (from 1 to 10%)」。
- 機構(格子の欠点): 「a high-risk segment if it is 'cancelled out' by a low risk segment in the same grid cell」= **生態学的誤謬**。
- 機構(ネットワークの利点): 街路網が実際の移動経路と犯行者の認知空間を規定する。運用上も「特定の街路セグメント」で表現される予測の方が展開しやすい。
- 格子の利点として挙げられているのは「simpler computation and visualization」のみ。

出典: [PMC6979510](https://pmc.ncbi.nlm.nih.gov/articles/PMC6979510/) **実読**。

**(5-b) 街路セグメントがミクロ地点の実証済み単位である(検索本文)**

Weisburdの犯罪集中則: シアトルの縦断研究で**毎年、犯罪の50%が街路セグメントの4.7〜6.1%に集中**。都市横断でも「50%の犯罪が2.1〜6.0%の街路」「25%が0.4〜1.6%」というバンド内。単位は一貫して **street segment**。
出典: [JQC "The law of crime concentration at places: Editors' introduction"](https://link.springer.com/article/10.1007/s10940-017-9342-0) / [crimrxiv](https://www.crimrxiv.com/pub/ar2dfs8s) 検索本文経由。**本文未読**。
含意: 契約§3の「人物③顕著な行為(U18犯罪創発の入口)」と **U18は街路セグメント単位で書かれた文献群の上に乗る**。格子セルで実装すると、U18の較正時に文献の単位と自分の単位が食い違う。

**(5-c) space syntax側の単位**
軸線(axial line)= 街路が曲がるまでの最長の延長。セグメント = 交差点間の街路長。近年はセグメントマップの方が精度が高いとされる。
出典: [spacesyntax.online 表現法](https://www.spacesyntax.online/applying-space-syntax/urban-methods-2/representations-of-space/) / [11th SSS: Road centre line simplification](https://spacesyntax.com/wp-content/uploads/2017/09/Road-centre-line-simplification-principles-for-angular-segment-analysis.pdf) 検索本文経由。**本文未読**。

**(5-d) MAUP(単位の恣意性の一般理論)**
MAUPは**scale effect**(粒度)と**zone effect**(区画の形)の2つ。「An optimal cell size for one statistic (e.g. spatial density) may not be optimal for another (e.g. transition probabilities)」。
出典: [Esri GIS Dictionary: MAUP](https://support.esri.com/en-us/gis-dictionary/modifiable-areal-unit-problem) / [Zhang & Kukadia 2005](https://journals.sagepub.com/doi/10.1177/0361198105190200109) 検索本文経由。
含意: **場所セルは1つの統計に最適化された単位でしかありえない**。契約が場所セルに背負わせている役割は3つ(①prefix共有キー ②変化検出器 ③dormant再送抑止)+ B2/B4の内容単位。**①②③は大きいセルを好み、B2/B4内容は小さく均質なセルを好む**。これがMAUPの本プロジェクト版。

**(5-e) 不定形の欠点(格子側の実利)**
- **ベンチ再現性**: セル数が可変・面積が不均一だと、ベンチの「セル数8/32/128/512」パラメータ化と ablation の軸が壊れる。格子は `floor(x/100), floor(y/100)` で決定論的・ハッシュ安定。
- **ID安定性**: OSM/PLATEAUの更新で街路が1本変わるとセグメント分割が変わり、**place_idが変わる=B2バイト列のハッシュが変わる=文面凍結(§1条5)を破る**。格子IDは外部データ更新に不変。**これは契約§1条5との整合性という重い論点**。
- **実装**: 街区/セグメント生成パイプライン(道路中心線→簡略化→ポリゴン化→建物対応付け)が新規に要る。UE/Photon/SL/H3 いずれも**格子系**であり、既製の実装知見も格子側にしかない。
- **カバレッジ**: 広場・駅コンコース・地下街はセグメント単位に落ちない(渋谷は特にこれが多い)。

---

### 問い6: 推奨と感度試験設計

**(6-a) 第1候補 = 100m格子(139セル)。決定の根拠は優先順に:**
1. **較正コスト**(支配的): B2静的言語化はR3-6aで標本点を60/20/20分割し、Mapillary画像+VLM+人手較正。**139→556はこの人手が4倍**。9/24前にPhase 2最小骨格を立てる制約下で556は非現実的。
2. **計算代償が小さい**: 50mの代償は**3〜8%**(§3-c)。粒度で稼げる量は誤差レベル。
3. **忠実度差も小さい**: 正方格子である限り街区跨ぎは避けられず、50mにしても V の不均質は解けない(§4-c)。50mの唯一の定量的利点はセル対角70.7m < Gehl 100m だが、共在の主張はB5が担うので重みは限定的。
4. **100m級は現実側と実装側の共通帯**: Gehl 100m / 1町109.09m / H3 res10 122.7m / UE RepGraph 100m / UE5 WP 128m / モバイル空間統計都心部125m。**外れ値でない**ことが独立に確認できる。

**(6-b) 同時に決めるべき2件(粒度と分離して)**
- **B-2: セルIDを `place_id` 抽象にする**。実装は `grid100(x,y)` だが、契約書とコードは place_id を不透明トークンとして扱い、将来 `blockface(grid100 ∩ 街区)` や `street_segment` に差し替え可能にする。**§1条5(文面凍結)との整合のため、place_id → B2バイト列 の対応表を版管理し、単位型の変更は必ず delta+感度試験を伴う改版として扱う**。
- **B-3: B4を2層に割る**(§4-e)。B4=セル(100m)の場(密度LOS・騒音段階)、B4b=サブセル(25m級)の構造物(行列・人だかり・グループ上位k)。順序は B4 → B4b → B5。

**(6-c) 感度試験の設計(BN-1の差し替え)**

**BN-1改(計算側・vLLMベンチ)**——軸を「セル数」から差し替える:
| 軸 | 水準 | 理由 |
|---|---|---|
| **B_cell**(セル節長) | **200 / 500 / 800** tok | 契約実値は500。ベンチは200で測っていた(§3-d)。**必須** |
| **d**(バッチあたりdistinctセル数) | 8 / 16 / 32 / **64** | §3-bの真の支配変数。起床キューをセル単位でバッチ化するかで制御 |
| **Zipf α** | 0(一様) / 1.0 / 1.5 | 渋谷型偏りの再現。実測で+6〜8%既知 |
| **階層数** | 3層(全体/種別/セル) / **4層(+サブセル)** | B-3案の計算代償の測定 |
| セル数 N | 139 / 556 (**確認用の2点だけ**) | 主軸から降格。「N は d を通してしか効かない」の確認 |
判定: (i) N を主軸から外しても throughput が d と B_cell で説明できるか(§3-bモデルの検証)。(ii) 4層化の追加損が何%か。(iii) B_cell=500 での 139 vs 556 の実測差(予測3〜8%)。

**BN-4(新設・推奨)——セルアフィニティ**:
DP7の7枚に対し (a) ラウンドロビン(現状) (b) `hash(place_id) mod 7` アフィニティ (c) ホットセル(上位20%)は全枚に複製し残りをアフィニティ、の3条件で throughput と負荷不均衡を測る。**理論上、各GPUのセル作業集合が 1/7 になる**(139→20セル・500tok×20=10,000tok)ので、セル節が完全常駐する。ただしZipf(20/80)で(b)は不均衡になるはずで、(c)が本命。**粒度で稼げる数%より大きい可能性が高く、ベンチ第3段の残測定「セッションアフィニティ」の具体化**。

**忠実度側の感度試験(§8 L2 ablation枠「場所セル粒度」の具体化)**:
1. **B5差分の直接測定**(§4-b・LLM不要・2.5m可視性格子だけで完結。**最優先・最も安い**): place_id を {100m格子, 100m格子∩街区(blockface), 50m格子, 道路セグメント} の4通りに変え、`add/del/Jaccard` の分布を比較。事前登録した閾値で粒度の可否を判定。
2. **行動指標の分布差**: 同一シード・同一シナリオで4通りを走らせ、滞留時間・立ち寄り率・経路選択の分布を比較。expedientの証明要件「結果を駆動していない」はここで満たす。
3. **識別テスト(R3-6b)**: 深層カーネル二標本検定のスコアが粒度で動くか。動くなら粒度は expedient として台帳に残り続ける。

**(6-d) 却下した候補と理由**
- **50m格子(556)**: 較正コスト4倍に見合う忠実度利得がない(§4-c)。**ただし §4-b の測定で p90(add) が閾値を超えたら復活させるべき**。今は「棄却」でなく「保留・測定待ち」。
- **道路セグメント単位(第1候補としては却下)**: 実証的には最も強い(§5-a/5-b)が、(i) place_id が外部データ更新で変わり文面凍結を破る (ii) 広場・駅コンコース・地下街を覆えない(渋谷ではこれが致命的) (iii) ベンチのパラメータ化と ablation 軸が壊れる。**Phase 3以降の昇格候補として `place_id` 抽象で退路を残す**。
- **街区単位(不定形)**: 同上。ただし **「100m格子 ∩ 街区」(blockface)** は決定論的(格子IDは不変・街区は切るだけ)なので、文面凍結と両立する**唯一の準不定形案**。§6-cの忠実度試験で第2候補として同時投入することを推奨。

---

## ⑤ 未発見・未確認の正直な列挙

**読めなかった/確認できなかったもの**
1. **渋谷の街区面積分布**——Web上に一次データなし。上表の東京値(800-900m²・29.2m)は **JPSJ論文の検索スニペットのみで、論文本文もPDFも403で読めていない**。著者・誌・DOIはCrossrefで実読確認済み。**この数値を設計根拠に使う前に、PLATEAU/OSMで自前実測すること**。
2. **Ericson et al. 2021 の本文**——要旨はSemantic Scholar API経由で**全文引用として実読**。本文PDFは403。「5m→3mでR²が.456→.625」は**検索スニペットのみ・未検証**。
3. **Gehlの原典 *Cities for People* (2010)**——未読。100m/25m/50-70m はすべて**二次資料(Planetizen等)の検索本文経由**。ページ本体も403。数値は複数の二次資料で一致しているが、**原典未確認**。
4. **UE ReplicationGraph の Epic公式既定セルサイズ**——Epic公式ドキュメント(UE5.7)を実フェッチしたが**セルサイズの記載なし**。10,000uu=100m は **コミュニティ移植リポ(locus84)のヘッダを raw で実読**したもの。Epic本体ソース(要認証)は未確認。
5. **UE5 World Partition 既定128m**——ブログ二次のみ。公式ドキュメント未確認。
6. **Photon Fusion のセルサイズ32m**——Photon公式ドキュメントURLだが、ページ本体はCloudflareで取得できず**検索結果本文経由**。
7. **Uber H3 res8 = サージ単位**——ブログ二次のみ。Uber公式blogでは未確認。
8. **Weisburd の原典**——検索本文経由。JQC本文未読。数値(4.7-6.1% / 2.1-6.0% / 0.4-1.6%)は未検証。
9. **Barker の behavior settings 原典**——未読。Phil Trans R Soc B のレビューも要旨・検索本文レベル。
10. **isovist の空間自己相関の相関距離(range)を m で与えた文献**——**見つからなかった**。semivariogram の一般論しか出ない。§4-b の自前測定が唯一の道。
11. **「distinct な共有prefix本数 × キャッシュ容量 → ヒット率」を空間到着過程の下で定量化した先行研究**——**見つからなかった**。§3-b の E[d] 導出は**本答申の自作**であり、外部の裏付けはない。実測−8%を約2.6倍過大予測する(自認)。
12. **渋谷スクランブル交差点の日通行量(26万/39万/50万)**——Wikipedia の検索本文経由・**原典(2014渋谷再開発協会 流動計測調査)未読**。
13. **KDDI Location Analyzer のメッシュサイズ・時間粒度**——渋谷区ダッシュボードのページを実読したが**開示なし**。5エリア(駅中心/北西/北東/南東/南西)と3街路(宮益坂・道玄坂・表参道)の構成は実読確認。**各エリアの面積は不明**。
14. **Boeing の世界都市街路網指標における東京の street_length_avg**——ページを実読したが個別都市値は掲載されておらず、Harvard Dataverse を見る必要がある。**未取得**。「米国典型都市圏160m」は検索本文経由・未検証。
15. **群衆シム(RVO/ORCA・social force)の実装で使われる空間ハッシュのセル辺長の具体値**——一般則(=相互作用半径 or 2h)しか得られず、**歩行者向けの具体的な m 値は未取得**。

**本答申が「推測」としてしか言っていないもの**
- [推測] 100mセルが街区を跨ぐことによる V の不均質が「大きい」——**測っていない**。§4-b が測定手順。大きくない可能性もある(渋谷中心部は幅の広い街路が少なく、キャニオンが深いので、逆に代表点が街路方向だけを見て済むかもしれない)。
- [推測] BN-4(セルアフィニティ)が粒度より効く——**未測定**。DP7線形性とKV容量の算術からの期待値にすぎない。
- [推測] B4b(サブセル25m)の追加損が小さい——E[d] が c=64 で飽和するという同じ論法からの期待値。**未測定**。
