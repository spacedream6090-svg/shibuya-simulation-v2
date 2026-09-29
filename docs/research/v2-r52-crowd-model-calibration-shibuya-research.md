# R-52 答申: 歩行者の群集モデルの較正値と渋谷(スクランブル交差点・駅周辺)の計測研究 — 定数・時間刻み・基本図・対人距離・渋谷の公開データの有無(U-9)

<!-- hdr:v1 -->
- **分野**: 歩行者動力学 #18 / 交通工学 #2 / 地理情報科学 #9 / 人間移動科学 #3 | **重要度**: P0([D-122 草案](../design/v2-spatial-physics-layer-draft.md) §3-4 の較正の錨・PENDING の U-9)
- **一次確認**: **B** = サブ実読(原典本文・コード 24・抄録 4・二次/報道 4・空欄 = §9)・**親検収 済(第283・下の欄)**
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 用途: (1) D-122「物理エンジン粒度の空間層」の較正の錨(歩行速度・対人距離・密度-速度・群れ・時間刻み)、(2) U-9「渋谷の歩行者流データ(横断者数・密度・軌跡)が政府・自治体ドメインにあるか/有償か/無いか」の判定材料。設計の決定はしない(§8 は候補と区分だけ)。
> 既存答申で済んでいる錨は引用だけ: Weidmann/Kladek(v_f 1.34・γ 1.913・ρ_max 5.4)・Bosina & Weidmann(希望速度 1.00〜1.60 m/s・体幅)・Fruin LOS・Sorokowska/Hall・森田 2004 = [C9 答申](v2-c9-position-attention-research.md) §1.2/§1.3/§1.5、Zhang 2011・Seyfried 2009・ORCA のデッドロック・SUMO–JuPedSim = [R-7](v2-crowd-physics-research.md)、Moussaïd 2010/2011 = [R-42](v2-r42-social-methodology-precedents.md) §3・[R-41](v2-r41-cognitive-architecture-precedents.md) §7、鈴木ほか 2012・告示 1441 の在館者密度 = [R-8](v2-c9-geometry-capacity-research.md)。
> 規律: 子サブ未起動・Web は読むだけ(PDF は curl → 標準出力 → pymupdf・保存なし・データファイルの取得なし)・登録/API 呼び出しなし・コミットなし・台帳未編集・本書の新規作成のみ。手元の `data/juelich_ped/`(metadata 5 本)・`data/jinryu/SOURCE.md`・`data/realworld/README.md`・道路交通センサス R3 の列名だけ読んだ(holdout の値は開いていない)。

---

> **親検収(第283・2026-09-28・親=Fable 5.1)**
> - 一次照合した引用(親が同じ URL を curl → 標準出力 → 文字列照合・保存なし): ✓ JuPedSim `CollisionFreeSpeedModelState.hpp`「double timeGap{1};」「double v0{1.2};」「double radius{0.2};」・`collision_free_speed_model.cpp`「("strength_neighbor_repulsion") = 8.0」・`simulation.py`「dt: float = 0.01」/ ✓ Helbing & Molnár 1995「V⁰αβ = 2.1m2s−2, σ = 0.3m」「∆t = 2s」「τα = 0.5s」/ ✓ Helbing・Farkas・Vicsek 2000「Ai = 2 · 103 N and Bi = 0.08 m」「k = 1.2 · 105 kg s−2」/ ✓ ShibuyaSocial「280 s, corresponding to two cycles of the traffic light」「Estimated by manual count ∼1000 ∼1000 ∼2000」「The RMSE was 0.17 m/s for Flow 1 and 0.20 m/s for Flow 2」/ ✓ PLATEAU 技術資料 No.22「678 … 4,431」「2021年3月11日」「データ借用元：渋谷区」「調査員が歩⾏者交通量をカウント」/ ✓ 渋谷区交通戦略 第 2 章「919,700 … 1,177,360」「平成29 年渋谷中心地区流動計測調査報告書（渋谷再開発協会）」。
> - 訂正: なし。図 2-6 の平日/休日の系列割り当ては本文との整合による推測=○ のまま。
> - 写し検査・訂正の伝播検査・循環参照検査・フロア併記検査: 写し先=[空間層の草案](../design/v2-spatial-physics-layer-draft.md) §3-4(錨 A1〜A16)・PENDING U-9。**訂正の伝播 2 件を親が実施**: R-7(信号 140 s は個人ブログのみ → 学術 2 本で補強)・R-42 §7-3(3,000 の一次なし → 朝日 2016-04-22 まで追跡・計測の一次は依然なし)=両答申の末尾に注記。フロア併記=基本図の文献間 2 倍幅(§2)・3,000 人/周期と繁華街調査の比較不能(§4-1)を併記済み。
> - 規律上の判定(取得経路・封印の扱い §10-3): 取得なし=規律内。**封印の判定(親)**: パターン台帳に「スクランブル通行量」の封印行は無く、封印(test)は `shibuya_jinryu`・`boundary_counts` の層だけ。本書の A17〜A20(ShibuyaSocial の手計数・JSAI の OD・区の 11 時間合計・道玄坂の時間帯別・センター街 2000 年)は**公刊の粗い値で、設計者が見た=validation(開封済み)扱い**とし、較正には使わない(宣言)。U15-6 の「holdout 面: スクランブル通行量」は封印値が存在しないので「validation 面」に読み替える(群衆物理設計書へ注記)。ATR(研究目的のみ)は較正に使わない(収益化構想との整合=ユーザー判断が要る)。

## 要約

1. **定数は原典とコードで揃った**。社会力(Helbing & Molnár 1995: V⁰ 2.1 m²/s²・σ 0.3 m・U⁰ 10 m²/s²・R 0.2 m・τ 0.5 s・2φ 200°・c 0.5・v₀ ~ N(1.34, 0.26) m/s)、Helbing・Farkas・Vicsek 2000(m 80 kg・τ 0.5 s・A 2×10³ N・B 0.08 m・k 1.2×10⁵ kg/s²・κ 2.4×10⁵ kg/(m·s)・直径 0.5〜0.7 m)、CFSM 原典(v₀ 1.2・ℓ 0.3 m・T 1 s・a 5・D 0.1 m)、GCFM 原典(a_min 0.18 m・τ_a 0.53 s・b 0.2〜0.25 m)、JuPedSim の既定値(4 模型分・コードで逐語)。**RVO2 のライブラリには既定値が無い**(全引数必須・例題が 0.25 s と 15/10/10/10/1.5/2.0 を使う)。
2. **時間刻み**: 原典の積分刻みは GCFM・CFSM とも **0.01 s**(陽的 Euler)で、JuPedSim の既定も `dt = 0.01`(「既定のままを推奨」)。RVO2 の例題は 0.25 s。HM1995 の「∆t = 2 s」は**積分刻みではなく**視野楕円の先読み時間。v2 の engine_spike の 0.5 s は原典の 50 倍=U15-3 の dt 掃引が必要という R-7 の結論は変わらない。
3. **基本図のフロア**: 研究間で最大比流量 **1.0〜2.0 (m·s)⁻¹**・その密度 **1.3〜2.3 m⁻²**(Zhang ら 2012 の文献比較)。一方向と双方向は ρ > 1.0 m⁻² で形が違う。単列は必要長 d = 0.36 + 1.06 v(Seyfried 2005)。文化差あり(Chattaraj 2009・抄録)。
4. **日本の値**: 横断歩道の青時間は「一般的には歩行速度を**秒速1メートル**」(警視庁・一次)=**設計上の下限であって観測平均ではない**。告示 1441(旧版)の避難歩行速度 60 m/分(百貨店・劇場・ホテル)/78 m/分(学校・事務所)/階段 27〜47 m/分。**日本の実測**は大阪の 2 人連れ(Zanlungo ら 2017・N ≈ 1,000 組): 仕事 1.27 m/s・余暇 1.12 m/s・70 歳以上 0.89 m/s・並び幅 0.58〜0.72 m(関係別)。データは ATR が**研究目的のみ無償**で公開。
5. **渋谷スクランブルの横断者数に公的一次は無い**。「1 回 3,000 人」「平日 26 万・休日 39 万」は朝日新聞 2016-04-22 が渋谷センター街の Web と**渋谷再開発協会の非公開調査(2014)**を元に書いた値(Wikipedia の出典欄で追跡)=報道。学術は 2 本: ShibuyaSocial(arXiv 2025・8K 映像 50 分・軌跡 407 本・手計数で 1 流 50 分 ≈ 1,000 人・**信号 1 周期 140 s を「280 s = 2 周期」で明記**)と JSAI 2022(ライブカメラ観測の OD 表 計 4,968 人/h・現示 (37,10,4)(44,3,3)(33,3,3) s)。
6. **公的に在るのは断面交通量の「合計」と「図」だけ**: 渋谷区 交通戦略(令和 2 年 3 月)に 10〜21 時の 11 時間合計(平成 16〜28 年・渋谷再開発協会の流動計測調査)と地点別の図(画像)。区は調査員カウントの歩行者交通量調査を持つが**非公開**で、国交省 PLATEAU の実証(uc22-040)が**区から借用**して道玄坂の時間帯別(2021-03-11)を報告書に載せた=**照会で入手できた前例**。警視庁の交通量統計は**車両と自転車だけ**(歩行者は対象外)。東京都の環境影響評価図書は**閲覧のみ・DL 不可・著作権は事業者**。
7. **U-9 の判定(事実のみ)**: 渋谷の**横断者数・密度-速度・軌跡の公開データ(政府・自治体ドメイン)は無い**。区の断面交通量は「在るが非公開」。有償は KDDI LA・ジオテクノロジーズ(GPS 点)・国際航業(Wi-Fi OD)ほか(粒度はメッシュ/点=横断者数・軌跡は出ない)。**日本の公開軌跡は大阪(ATR)だけ**。D 層(D-122)のミクロ照合を渋谷の公開データで行う道は現時点で無い。

## §0 等級と調べ方・出典表

等級: **◎** 原典本文(またはソースコード)で数値まで逐語確認 / **○** 原典は読めたが、図のラベル順・系列の対応に推測を含む、または査読前 / **△** 抄録・報道・検索要約・二次 / **×** 未確認(本文に数値を写さない)。**[再計算]** はサブの計算、**[推測]** は原典に無い解釈。

| # | 出典 | URL | 等級 | 読んだ範囲 |
|---|---|---|---|---|
| 1 | Helbing & Molnár 1995 *PRE* 51:4282(arXiv cond-mat/9805244) | https://arxiv.org/abs/cond-mat/9805244 | ◎ | PDF 全文・§IV |
| 2 | Helbing, Farkas & Vicsek 2000 *Nature* 407:487(arXiv cond-mat/0009448) | https://arxiv.org/abs/cond-mat/0009448 | ◎ | PDF 全文 |
| 3 | RVO2 Library(snape/RVO2・commit 75822bb・2026-09-26) | https://github.com/snape/RVO2 | ◎ | `src/RVOSimulator.h/.cc`・`examples/Circle.cc/Roadmap.cc/Blocks.cc` |
| 4 | Tordeux, Chraibi & Seyfried「Collision-free speed model for pedestrian dynamics」(arXiv 1512.05597・2015-12-17 投稿) | https://arxiv.org/abs/1512.05597 | ◎ | PDF 全文・図 2・§2.2・§3 |
| 5 | Chraibi, Seyfried & Schadschneider「Generalized Centrifugal Force Model for Pedestrian Dynamics」*PRE* 82:046111(arXiv 1008.4297) | https://arxiv.org/abs/1008.4297 | ◎ | PDF 全文・§III/§IV/§VII |
| 6 | JuPedSim(PedestrianDynamics/jupedsim・master commit 098099e・2026-09-23・最新リリース v1.4.2) | https://github.com/PedestrianDynamics/jupedsim | ◎ | `python_bindings_jupedsim/*.cpp`・`libsimulator/src/OperationalModels/*/…State.hpp`・`simulation.py` |
| 7 | Zhang, Klingsch, Schadschneider & Seyfried 2012 *J Stat Mech* P02002(arXiv 1107.5246) | https://arxiv.org/abs/1107.5246 | ◎ | PDF 全文 |
| 8 | Seyfried ら 2005「The Fundamental Diagram of Pedestrian Movement Revisited」(arXiv physics/0506170) | https://arxiv.org/abs/physics/0506170 | ◎ | PDF 全文 |
| 9 | Chattaraj, Seyfried & Chakroborty 2009「Comparison of Pedestrian Fundamental Diagram Across Cultures」(arXiv 0903.0149) | https://arxiv.org/abs/0903.0149 | △ | 抄録 |
| 10 | 警視庁「歩行者横断秒数の延長」(更新 2021-09-21) | https://www.keishicho.metro.tokyo.lg.jp/kotsu/iken_yobo/shingo_faq/crosswalk_extention.html | ◎ | 全文 |
| 11 | 井料美帆 2014「信号付横断歩道における歩行者クリアランス時間設定方法の日米比較」生産研究 66(4):345 | https://doi.org/10.11188/seisankenkyu.66.345 | ◎ | PDF p.1-3 |
| 12 | 平成 12 年建設省告示第 1441 号(旧版・国交省掲載) | https://www.mlit.go.jp/notice/noticedata/pdf/201703/00006493.pdf | ◎ | 第二 2 項の表(現行 令和 2 年告示 510 号は未照合=R-8 と同じ空欄) |
| 13 | RiMEA 4.1.1(2025-09-11・旧 4.0.0 は 2022-04-28・CC BY-ND 4.0) | https://rimea.de/wp-content/uploads/2025/09/rimea-4.1.1-d-e-1.pdf | ◎ | §3.2.2・§3.2.4・付録 2 の試験一覧・Test 1 |
| 14 | Zanlungo ら 2017「Intrinsic group behaviour」*PLOS ONE* 12(11):e0187253 | https://doi.org/10.1371/journal.pone.0187253 | ◎ | PDF 表 1〜4・Data set 節 |
| 15 | ATR「Pedestrian tracking with group annotations」(DIAMOR/ATC) | http://www.irc.atr.jp/sets/groups/ | ◎ | ページ全文(License 節) |
| 16 | Vanumu, Rao & Tiwari 2017 *Eur Transp Res Rev* 9:49(レビュー・OA) | https://doi.org/10.1007/s12544-017-0264-6 | ◎(レビューの記述として) | 本文(d-nb.info 配布 PDF) |
| 17 | Gérin-Lajoie ら 2005 *Motor Control* 9:242 / 2008 *Gait Posture* 27:239 | https://pubmed.ncbi.nlm.nih.gov/16239715/ ・ https://pubmed.ncbi.nlm.nih.gov/17512201/ | △ | PubMed 抄録のみ |
| 18 | Costa 2010「Interpersonal Distances in Group Walking」*J Nonverbal Behav* 34:15 | https://doi.org/10.1007/s10919-009-0077-y | △ | 検索要約の抄録のみ(本文有料) |
| 19 | Sakurai, Kajio & Yamamoto「ShibuyaSocial: Multi-scale Model of Pedestrian Flows in Scramble Crossing」(arXiv 2512.18550・2025-12-21・東京大学) | https://arxiv.org/abs/2512.18550 | ○(査読前) | PDF 全文 |
| 20 | 大神・乘濵・秋本・鶴岡「深層強化学習によるスクランブル交差点の信号制御」JSAI 2022 3N3-GS-10-03 | https://www.jstage.jst.go.jp/article/pjsai/JSAI2022/0/JSAI2022_3N3GS1003/_pdf | ◎(記載として)/値は △ | PDF p.1-2 |
| 21 | 渋谷区「渋谷駅周辺地域交通戦略」(令和 2 年 3 月)第 2 章・第 4 章・第 9 章 | https://www.city.shibuya.tokyo.jp/kankyo/shuhen-machizukuri/eki-kanremplan/syuhen_koutu.html | ○ | 章 PDF のテキスト層(地図は画像) |
| 22 | 国交省 PLATEAU uc22-040 と技術資料 No.22(パシフィックコンサルタンツ/フォーラムエイト・2023) | https://www.mlit.go.jp/plateau/use-case/uc22-040/ ・ https://www.mlit.go.jp/plateau/file/libraries/doc/plateau_tech_doc_0022_ver01.pdf | ○ | 資料 p.16・33・36・40 |
| 23 | 国交省 PLATEAU uc22-004(技術資料 No.45)・uc22-023・uc24-07 | https://www.mlit.go.jp/plateau/use-case/uc22-004/ ほか | ◎ | 活用データ一覧・検証結果の節 |
| 24 | 警視庁「交通量統計表」(令和 5・6 年) | https://www.keishicho.metro.tokyo.lg.jp/about_mpd/jokyo_tokei/tokei_jokyo/ryo.html | ◎ | ページ・調査概要 PDF・主要交差点(区部)PDF |
| 25 | 東京都「東京都における繁華街利用実態調査」(平成 13 年 3 月) | https://www.sangyo-rodo.metro.tokyo.lg.jp/toukei/pdf/monthly/chusho/hankagai.pdf | ◎ | PDF 全 7 頁 |
| 26 | 国交省 関東地方整備局 東京国道事務所「渋谷駅周辺整備(交通結節点事業)」 | https://www.ktr.mlit.go.jp/toukoku/toukoku00032.html | ◎ | ページ |
| 27 | 東京都環境局「渋谷駅街区開発事業」変更届(環境影響評価図書) | https://www.kankyo.metro.tokyo.lg.jp/assessment/information/toshokohyo/publishdetail/300_shibuyaeki_tosho_hen3 | ◎ | 利用上の注意 |
| 28 | 渋谷区「渋谷駅周辺の滞在・通行人流ダッシュボード」 | https://www.city.shibuya.tokyo.jp/kusei/tokei_shibuya/shibuya-data/shibuya_city_dashboard_peopleflow_KDDI.html | ◎ | 対象エリア・ストリートの定義のみ |
| 29 | 東京大学 CSIS「JoRAS において、初めて GPS ベースの実人流データセットの提供を開始」 | https://www.csis.u-tokyo.ac.jp/research/jorasgps/ | ◎ | ページ |
| 30 | Gupta ら 2018「Social GAN」(arXiv 1803.10892) | https://arxiv.org/abs/1803.10892 | ◎ | Evaluation Metrics 節 |
| 31 | 渋谷スクランブル交差点(ja.wikipedia・raw)→ 朝日新聞 2016-04-22 p.29 | https://ja.wikipedia.org/wiki/渋谷スクランブル交差点 | △(報道の孫引き) | 本文と ref 定義 |
| 32 | Cao, Seyfried, Zhang, Holl & Song 2017 *J Stat Mech* 033404(多方向流の基本図) | https://doi.org/10.1088/1742-5468/aa620d | × | 書誌のみ(Jülich 機関リポジトリは bot 遮断) |

## §1 群集モデルの較正値と時間刻み(問い 1)

### 1-1 定数

| モデル | 値(単位) | 逐語(抜粋) | # | 等級 |
|---|---|---|---|---|
| 社会力 HM1995 | v₀ ~ 正規 平均 1.34 m/s・SD 0.26 m/s・v_max = 1.3 v₀ / V⁰ 2.1 m²s⁻²・σ 0.3 m / U⁰ 10 m²s⁻²・R 0.2 m / τ 0.5 s / 2φ = 200°・視野外の重み c = 0.5 / 歩道幅 10 m | 「mean ⟨v0⟩= 1.34ms−1 and standard deviation √θ = 0.26ms−1」「V0αβ = 2.1m2s−2, σ = 0.3m and U0αB = 10m2s−2, R = 0.2m」「For ∆t in formula (4) we took ∆t = 2s, and for the relaxation times we used τα = 0.5s」「2ϕ = 200◦」「c = 0.5」 | 1 | ◎ |
| 社会力 HFV2000(避難) | m 80 kg・τ 0.5 s・A 2×10³ N・B 0.08 m・k 1.2×10⁵ kg s⁻²・κ 2.4×10⁵ kg m⁻¹ s⁻¹・直径 2r ~ 一様 [0.5, 0.7] m・v₀ ≈ 0.6(relaxed)/1(normal)/≲1.5(nervous)m/s・1 m 扉で 0.73 人/s(v₀ ≈ 0.8) | 「With Ai = 2 · 103 N and Bi = 0.08 m」「k = 1.2 · 105 kg s−2 and κ = 2.4 · 105 kg m−1s−1」「uniformly distributed pedestrian diameters 2ri in the interval [0.5 m, 0.7 m]」。**全員同一値**の理由=「to minimise the number of parameters for reasons of calibration and robustness」 | 2 | ◎ |
| ORCA/RVO2 | **ライブラリの既定値は無い**(既定コンストラクタは `timeStep_(0.0F)`・`defaultAgent_(NULL)`=`setAgentDefaults` か全引数つき `addAgent` が必須)。例題: Circle = `setTimeStep(0.25F)`・`setAgentDefaults(15.0F, 10U, 10.0F, 10.0F, 1.5F, 2.0F)`(neighborDist・maxNeighbors・timeHorizon・timeHorizonObst・radius・maxSpeed の順)/ Roadmap・Blocks = 0.25・(15, 10, 5, 5, 2, 2)。単位は場面の任意単位(m と明記されない) | コード逐語 | 3 | ◎(論文値は ×) |
| CFSM 原典 | v₀ 1.2 m/s・ℓ(直径)0.3 m・T(time gap)1 s・反発 a = 5・D = 0.1 m(図 2 に D = 0.02 m も併記)・系 9 m × 3 m | 「V(s) = min{v0,max{0,(s−ℓ)/T}}」「v0 = 1.2 m/s ℓ= 0.3 m T = 1 s … a = 5 D = 0.1 m D = 0.02 m」 | 4 | ◎ |
| CFSM(JuPedSim 既定) | 模型: strength_neighbor_repulsion **8.0**・range_neighbor_repulsion **0.1**・strength_geometry_repulsion **5.0**・range_geometry_repulsion **0.02** / 体: timeGap **1**・v0 **1.2**・radius **0.2**(=直径 0.4 m で原典の ℓ 0.3 と違う) | `py::arg("strength_neighbor_repulsion") = 8.0` ほか・`double timeGap{1}; double v0{1.2}; double radius{0.2};` | 6 | ◎ |
| GCFM 原典 | 希望速度 平均 1.34・SD 0.26 m/s・τ 0.5 s・質量 1(単位化)・進行方向の半軸 a = a_min + τ_a v(a_min 0.18 m・τ_a 0.53 s)・横の半軸 b_min 0.2 m・b_max 0.25 m(25 m × 1 m 回廊で較正)・反発強さ η は重なり率 o(v) と振動 o(s) の曲線の交点で選ぶ(値は本文に無し) | 「We set amin = 0.18 m and τa = 0.53 s」「bmin = 0.2 m and bmax = 0.25 m」「τ … is set to 0.5 s, i.e. τ ≫∆t」 | 5 | ◎(η は ×) |
| GCFM(JuPedSim 既定) | 模型: strength_neighbor_repulsion 0.3・strength_wall_repulsion 0.2・max_*_interaction_distance 2・max_*_interpolation_distance 0.1・max_neighbor/geometry_repulsion_force 9/3 / 体: mass 1.0・tau 0.5・v0 1.2・Av 1.0・AMin 0.2・BMin 0.2・BMax 0.4(**原典の a_min 0.18・b_max 0.25 と違う**) | コード逐語 | 6 | ◎ |
| SFM(JuPedSim 既定) | 模型: body_force 120000・friction 240000 / 体: mass 80・desiredSpeed **0.8**・reactionTime 0.5・agentScale 2000・obstacleScale 2000・forceDistance 0.08・radius 0.3 =**HFV2000 の避難値の並び**(v₀ 0.8 は HFV のボトルネック条件と同じ値) | コード逐語 | 6 | ◎ |
| AVM(JuPedSim 既定) | 模型: pushout_strength 0.3・rng_seed 42 / 体: strengthNeighborRepulsion 8.0・rangeNeighborRepulsion 0.1・wallBufferDistance 0.1・anticipationTime 1.0・reactionTime 0.3・timeGap 1.06・v0 1.2・radius 0.2 | コード逐語 | 6 | ◎ |

### 1-2 時間刻み

| モデル | 刻み | 根拠(逐語 or 再計算) | # |
|---|---|---|---|
| CFSM | **0.01 s**(陽的 Euler) | 「explicit Euler numerical scheme with time step dt = 0.01 s」。衝突なしは**連続時間で**証明(配置集合 Q_i が不変集合)。**離散化での条件は本文に無い**。[推測] 1 刻みの移動 v₀·dt(0.012 m)が隙間 s − ℓ の解像度より十分小さいことが暗黙の前提 | 4 |
| GCFM | **0.01 s**(Euler・固定刻み・並列更新) | 「Euler scheme with fixed-step size ∆t = 0.01 s」「τ ≫∆t」。重なりの不在(距離 ≥ s₀)は「not guaranteed」と明記 | 5 |
| JuPedSim(全模型) | **0.01 s** 既定 | `dt: float = 0.01`「It is recommended to leave this at its default value.」 | 6 |
| SFM | 原典(HM1995・HFV2000)に積分刻みの記載なし | HM1995 の「∆t = 2 s」は式 (4) の先読み時間=**積分刻みではない**。[再計算] HFV の接触剛性 k = 1.2×10⁵ kg/s²・m = 80 kg → ω = √(k/m) ≈ 38.7 rad/s(周期 0.16 s)→ 陽的 Euler が接触中に安定な上限 dt < 2/ω ≈ **0.052 s**(教科書的条件の当てはめ=[推測]) | 1, 2 |
| ORCA/RVO2 | 例題 **0.25 s** | Tordeux ら(#4)の整理: 速度障害物系は「by construction collision-free if the time step is smaller than a horizon time of anticipation」 | 3, 4 |
| v2 | tick 60 s・engine_spike dt 0.5 s | R-7/U15-3 の dt 掃引(0.01〜1.0)の結論は不変。**0.25 s(RVO2 例題)を掃引点に足す**のは候補 | [U15](../design/v2-crowd-physics.md) |

## §2 基本図・歩行速度(問い 2)

- **既出**(引用のみ): Weidmann/Kladek v/v₀ = 1 − exp(−1.913(1/ρ − 1/5.4))・v_f 1.34(Kretz 2015)/ Bosina & Weidmann 希望速度 1.00〜1.60 m/s / Fruin LOS 境界(A ≤0.308 … F >2.153 人/m²・最大 85.96 人/分/m)/ 森田 2004 神戸ルミナリエ 0.85〜4.37 人/m²・0.03〜1.8 m/s = [C9 §1.2-1.3](v2-c9-position-attention-research.md)。Zhang 2011 v₀ 1.55 ± 0.18(ドイツ人学生 42 名)・「施設が違えば基本図は比較不能」/ Seyfried 2009 ボトルネック 1.61〜2.31 (m·s)⁻¹ = [R-7 §3](v2-crowd-physics-research.md)。鉄道総研 2016「約 40 年前の推定式より低い」(数値なし)= C9。
- **双方向流と文献フロア**(#7 ◎): 「The density values where the specific flow reach the maximum range from about 1.3 m−2 to 2.3 m−2. Also the maximum specific flows from different studies range from about 1.0 (m·s)−1 to 2.0 (m·s)−1.」/ 抄録「differences in the shape of the relation for ρ > 1.0 m-2. The maximum of the specific flow in unidirectional streams is significantly larger than that in all bidirectional streams examined.」/ Weidmann の図は「an idealized fundamental diagram obtained by collecting and fitting 25 other experiments」。**= 基本図の照合では研究間で 2 倍幅のばらつきが床**(フロア併記)。
- **単列**(#8 ◎): 「a linear relationship with d = 0.36+1.06 v gives the best fit」(d = 1 人の必要長 m)。1.34 からのずれは「the instruction to the test persons not to hurry」。[再計算] v = 1.34 なら d = 1.78 m(1 次元密度 0.56 人/m)。
- **文化差**(#9 △): 「the speed of Indian test persons is less dependent on density than the speed of German test persons」→ 独国実験の基本図の日本への直輸入は検定なしでは言えない(U15-5 段階 2 の expedient 宣言を支持)。多方向流(4 方向交差)の基本図 Cao ら 2017(#32)は書誌のみ=×。
- **日本の設計値**: 警視庁(#10 ◎)「歩行者用信号の青時間は、横断歩道の長さによって異なります。一般的には歩行速度を秒速1メートルとして道路を渡りきれるよう調整しています。歩行速度が遅い高齢者や子供が多く利用する場所については、より多くの時間を出すよう考慮しています。」/ 井料 2014(#11 ◎)「青点滅は…L/2V となる」「青と青点滅時間の合計で，歩行者が横断に必要な時間L/V を確保する」「なお歩行速度Vは通常1.0m/s を用いる」。**1.0 m/s は「青のうちに渡りきれる」ための設計下限で、観測された平均速度ではない**。高齢者の延長時の想定速度は警察の公開資料に見つからず=×。
- **避難設計の法定値**(#12 ◎・旧版): 歩行速度(m/分)= 劇場: 階段上り 27・下り 36・客席 30・その他 60 / 百貨店・展示場・共同住宅・ホテル: 上り 27・下り 36・その他 60 / 学校・事務所: 上り 35・下り 47・その他 78。[再計算] 60 = 1.00 m/s・78 = 1.30 m/s・27 = 0.45・36 = 0.60・35 = 0.58・47 = 0.78 m/s。同告示の有効流動係数 90 人/(分·m)(出口が直接地上)。
- **RiMEA 4.1.1**(#13 ◎): 「According to Weidmann [2] the average walking speed of men is 10.9 % higher than that of women. This results in a mean free walking speed of 1.41 m/s for men and 1.27 m/s for women.」/ 移動制約者 0.46〜0.76 m/s(表 2)/ 標準母集団=男女 50%・年齢 正規 平均 50・SD 20・10〜85 歳 / 年齢別の速度曲線は図 3 のみ(数値表なし=×)。
- **日本の実測・年齢と目的**(#14 ◎・大阪 ATC の商業施設回廊・2 人連れのみ・集団速度 V と各人の速度 > 0.5 m/s の点だけ): 表 1 目的別 V = 余暇 **1118**・仕事 **1271** mm/s(N 716/372・効果量 δ 0.832)/ 表 4 最小年齢別 V = 0-9 歳 1143・20-29 歳 1181・30-39 歳 1204・60-69 歳 1028・70 歳以上 **886** mm/s。著者の注意「attempts to verify our findings in different environments should be directed not at specific quantitative figures … but at qualitative patterns」。
- **目的の順序**(#16 ◎ レビューの記述): 「According to Daamen [3] higher walking speeds were observed for pedestrians travelling for business followed by commuters, shoppers and then pedestrians walking in leisure. Especially, higher free speeds are observed in transfer stations compared to shopping areas.」。Weidmann の目的別の数値は原典未読のため**本書に写さない**(§9)。
- **渋谷の横断中の速度**(#19 ○): 平均速度の時系列は図のみ。本文「in reality pedestrians walk faster, trying to finish crossing before the traffic light turns red」(定性)。

## §3 対人距離・群れ(問い 3)

- **既出**: Moussaïd 2010 集団率 55%(A)/70%(B)・N = 260/1093 群・隊形の V/逆 V = [R-42 §3-1](v2-r42-social-methodology-precedents.md)。Sorokowska 2017 選好距離(見知らぬ人 1.35・知人 0.92・親しい人 0.32 m・日本は対象外)・Hall の帯(二次)・Bosina & Weidmann 表 2(体幅 0.49/0.33・奥行 0.29/0.17・親密距離 0.20/0.15 m・反応時間 0.80/0.40 s)= [C9 §1.5](v2-c9-position-attention-research.md)。
- **日本の 2 人連れの間隔**(#14 ◎・mm): 関係別(表 2)並び幅 x = 同僚 **718**・恋人 **600**・家族 **583**・友人 **662** / 間隔 r = 851・714・863・792 / 前後差 y = 334・291・498・314 / V = 1274・1099・1094・1138。目的別(表 1)x = 余暇 628・仕事 713。「couples walking very close and abreast, colleagues walking at a larger distance, and friends walking more abreast than family members」。
- **日本の公開軌跡**(#15 ◎): DIAMOR(大阪の商業施設と駅を結ぶ 2 本の直線回廊・レーザー測域)2 日 + ATC 6 日(3-D 距離センサ)・各日 10-11・12-13・15-16・19-20 時の 1 時間 × 4・列 = 時刻・ID・x/y/z [mm]・速度 [mm/s]・進行角・体の向き・集団注記。**License「The datasets are free to use for research purposes only.」**
- **3 人連れの隊形**(#18 △): 1,020 組(イタリア)・「The most frequent spatial arrangement in triads was a "<" formation」・混合 2 人は並びやすい。cm の値は本文有料=×。
- **パーソナルスペース**(#17 △): 2005「Participants systematically maintained an elliptical PS during circumvention, but they adjusted its size according to different environmental factors」/ 2008「The shape and size of PS were maintained across walking speeds, and a smaller PS was generally observed on the dominant side」。**楕円の半径(縦約 2 m・横約 0.5 m とする二次の記述)は原典未確認=×**。
- **日本人の対人距離の分類**: 西出 1985(排他域 < 50 cm・会話域 50 cm〜1.5 m・近接域 1.5〜3 m・相互認識域 3〜20 m)は**二次のみ**(原典「建築と実務」No.5 は未取得)=△。

## §4 渋谷の計測研究・データ(問い 4)

### 4-1 スクランブル交差点の横断者数 — 数値の出所の追跡

| 主張 | 追跡の結果 | 等級 |
|---|---|---|
| 1 回の青で最大 3,000 人 | Wikipedia 本文「2016年の渋谷センター街のウェブサイトによると1回の青信号(2分間隔)で多いときに3,000人」の出典は**朝日新聞 2016-04-22 p.29「【東京はてな】渋谷交差点、1回で3千人横断?」**(井上恵一朗)。**計測の一次は見つからない**(R-42 §7-3 と同じ判定・出所は一段深く追えた) | △(報道の孫引き) |
| 平日 26 万・休日 39 万人/日 | 同じ朝日記事が「**2014年の渋谷再開発協会の流動計測調査を基に算定**」。協会の調査は 1968 年から続くとされるが、Web 上に報告書・データは無い(協会の該当ページは見出しのみ) | △ |
| 1 回 1,000 人以上 | Wikipedia 冒頭(CNN.co.jp 動画) | × |
| 学術 1: ShibuyaSocial | 「50-min daytime video data were collected on a weekday」「(a) Estimated by manual count ∼1000 ∼1000 ∼2000」(Flow 1 = 駅 → 横断歩道 / Flow 2 = 逆方向の 2 流・交差点全体ではない)。[再計算] 50 分 = 21.4 周期 → 2 流で ≈ 93 人/周期 | ○ |
| 学術 2: JSAI 2022 | 歩行者 OD 表(人/h)を「渋谷駅周辺交通戦略第2章…のデータ及び渋谷スクランブル交差点のライブカメラにおいて2021年10月25日13時ごろに観測したデータをもとに規定」。[再計算] 表の合計 4,968 人/h → 140 s 周期で ≈ 193 人/周期(コロナ期・観測手順の記載は簡略) | △ |
| 信号周期 | ShibuyaSocial「280 s, corresponding to two cycles of the traffic light」(= **140 s**)/ JSAI 2022「(青，黄，赤)で表すと，(37, 10, 4)，(44, 3, 3)，(33, 3, 3)」[再計算] 合計 140 s。U15-7 の個人ブログ値(140/37/10)と**学術 2 本が一致**。警視庁・区の公的な現示は依然なし | ○ |

**フロア併記**: 3,000 人/周期は [再計算] 77,143 人/h に当たり、東京都の繁華街調査で最多地点(センター街入口)の 12 時間平均 9,464 人/h(§4-3)の約 8 倍。26 万/日を 24 時間に均すと ≈ 421 人/周期・39 万で ≈ 632 人/周期 [再計算]。定義(ピーク/平均・全方向/一部の流れ・年・コロナ期)がすべて違うので**比は比較不能**で、「3,000 はピーク時の最大」と読むのが最も矛盾が少ない=[推測]。

### 4-2 渋谷を対象地にした学術計測

- **ShibuyaSocial**(#19・東京大学・JST さきがけ): 高層ビルから 8K・30 FPS で撮影 → SMILETrack で検出追跡 → 射影行列で 2 次元化。全追跡できたのは 407 本(Flow 1 183・Flow 2 224 = 手計数の 18%/22%)・1 本あたり平均 2,591/2,260 フレーム・学習は 5 FPS に間引き。検証: 横断歩道内の人数 RMSE **2.34/1.88 人**・平均速度 RMSE **0.17/0.20 m/s**・位置誤差 0.068/0.070 m・経路辺の正解率 99.7/99.5%。OD データについて「usually commercially available … the data cannot be used without statistical processing」。**軌跡データの公開の記載は見つからない**=×。撮影日は本文に無い。
- **JSAI 2022**(#20): SUMO で再現・歩行者 OD 4 地点・車両は台/h。ライブカメラ(YouTube)観測。
- **PLATEAU uc22-040**(#22・道玄坂): 経路選択の非集計モデル(GAUSS でパラメータ推定)・Wi-Fi 人口統計(国際航業・2019 年 10 月・**購入**)を**区の断面交通量に合わせて拡大**。
- 未読: Narahara 2010(UC-win/Road によるスクランブルの模擬)・『渋谷 にぎわい空間を科学する』(渋谷学叢書 5・2017)=書誌のみ。土木学会・建築学会でスクランブルを対象地にした軌跡・密度・速度の論文は本調査の検索では表面化しなかった(「無い」とは断定しない)。

### 4-3 公的データ

- **渋谷区 交通戦略(令和 2 年 3 月)**(#21): 図 2-4/2-5「歩行者交通量(平日/休日ピーク時)」の出典=「現況交通量調査(平成27年～平成29年実施)および渋谷中心地区流動計測調査(平成28年実施)」(**地点の値は画像で、テキストでは取れない**)。図 2-6「歩行者交通量の推移(10時～21時の11時間合計)」出典「平成29年渋谷中心地区流動計測調査報告書(渋谷再開発協会)」・注「渋谷駅中心地域内の全交通量調査箇所における断面交通量の合計値」: 平成 16・20・24・28 年 = **平日 919,700・987,158・1,016,908・1,019,692 / 休日 1,093,648・1,096,198・1,239,406・1,177,360**(系列の割り当ては本文「平日については年々緩やかに増加…休日は平成20年から平成24年に大幅に増加し、その後減少」と合う側に置いた=[推測])。第 9 章は評価指標に「歩行者交通量(路線別、時間帯別、平休日別)」、取得方法に「実態調査、ビッグデータ活用」を挙げる。
- **渋谷区の歩行者交通量調査の実在と非公開**(#22 技術資料 No.22 p.33・36): 「渋谷区が実施した交通量調査(調査員が歩行者交通量をカウント)結果を、方向別・時間帯別に集計したデータ」「データ借用元:渋谷区」。道玄坂の時間帯別(2021-03-11 木・7:00〜20:00・13 時間連続): 7 時台から 678・1,187・1,859・1,923・2,311・3,176・3,656・3,666・3,425・3,579・3,952・3,810・4,431 人(図の数値ラベルの順)[再計算] 13 時間計 37,653 人。**緊急事態宣言の期間中の平日**。拡大後 OD 渋谷駅⇔道玄坂上 31,279 人/12h(平日)。
- **東京都 繁華街利用実態調査**(#25 ◎・平成 12 年 9〜10 月): 11 繁華街 165 地点・10〜22 時。「最も歩行者通行量が多かったのは、渋谷の「センター街入口」。10 時から22 時までの12 時間に平日で113,568 人が通行している」「休日でも11 万2 千人」。「本調査以降、同様の調査は行っていません」「報告書の配布、販売はありません」。
- **国交省 東京国道**(#26 ◎): 国道 246 号横断歩道橋(西口 昭和 43 年・東口 昭和 48 年・幅員 1.5〜5.0 m)「歩行者交通量(約20万人/日)」(計測年は記載なし)。
- **警視庁 交通量統計表**(#24 ◎): 「都県境及び東京都内の主要交差点等」「2か年で244か所」。計測対象は大型/普通の乗用・貨物・二輪車と**自転車(歩道上を含む)**で**歩行者は計測しない**。渋谷区内は地点 504「渋谷署前」(明治通り×玉川通り)が見え、スクランブルは地点に無い。
- **道路交通センサス R3 箇所別基本表**(手元 `road_census_r3/kasyo13.csv` の列名): 自転車歩行者道の設置率・幅員はあるが**歩行者交通量の列は無い**。
- **東京都 環境影響評価図書**(#27 ◎): 渋谷駅街区の図書は「図書データの著作権は事業者にあり、事業者の許諾を得ないで複製、転用等を行うことは禁止」「閲覧のみ可能、印刷及びダウンロードは不可」。
- **既に手元にある公的系**: KDDI LA の滞在 5 エリア+**通行 3 ストリート(宮益坂・道玄坂・表参道)**(区ダッシュボード #28・`kddi_la`/`shibuya_jinryu`・holdout)/ 全国の人流オープンデータ 1 km(国交省・Agoop 換算・`data/jinryu`・holdout)/ 駅乗降(ODPT・大都市交通センサス)。いずれも**横断者数・軌跡ではない**。

### 4-4 有償・民間(存在と条件だけ・登録/API 呼び出しなし)

| 提供者 | 何が在るか(根拠) | 条件 | 等級 |
|---|---|---|---|
| KDDI・技研商事(KDDI Location Analyzer) | 区のダッシュボード・区 OD(CC BY 4.0)で一部公開(#28・[realworld の README](../../data/realworld/README.md)) | 詳細は有償 SaaS=[未確認] | ◎(公開分) |
| ジオテクノロジーズ | 渋谷駅 1 km・年齢性別つき人流(2021-05〜10)を PLATEAU uc22-004 が**購入**(#23 技術資料 No.45)/ CSIS JoRAS「実人流データ」(提供: 同社・東京都・2023 年 5 月・約 300 万トリップ/日・点データ)(#29) | JoRAS は CSIS 共同研究申請+提供元の確認(「通常より審査期間が長くなることがあります」)。公益条件の原文は [未確認] | ◎ |
| 国際航業(Wi-Fi 人口統計) | 町丁目ゾーン間 OD・年代性別(2019-10)を uc22-040 が**購入**(#22) | 有償 | ◎ |
| ブログウォッチャー・Agoop・unerry | PLATEAU uc24-07 の変換ツールに定義がプリセット(#23) | 有償=[未確認] | ◎(存在) |
| NTT ドコモ(モバイル空間統計) | 区の産業・観光ビジョン(2018)が使用([jinryu の SOURCE.md](../../data/jinryu/SOURCE.md)) | 有償=[未確認] | △ |
| LocationMind ほか | — | [未確認] | × |

## §5 人流の検証に使われた指標(問い 5)

| 指標 | 先行 | 値・定義 | # |
|---|---|---|---|
| 基本図の一致(施設別・Voronoi 密度) | Zhang 2011/2012・U15-6 | 文献間フロア: 最大比流量 1.0〜2.0 (m·s)⁻¹・その密度 1.3〜2.3 m⁻² | 7・R-7 |
| 標準試験群 | RiMEA 4.1.1 付録 2 | 16 試験(1〜3 所定速度の維持[廊下・上り・下り]・4 基本図の計測・5 反応時間・6 角・7 属性の割付・8 パラメタ研究・9 大空間からの退出・10/11 避難経路の割付/選択・12a〜d ボトルネック・13 階段の基本図・14 経路選択・15 大群衆の角・16 1 次元基本図)。Test 1 は「typical pedestrian speed of 1.33 m/sec: the speed should be set at a value between 4.5 and 5.1 km/h. The travel time should lie in the range of 26 to 34 seconds」 | 13 |
| 軌跡の誤差 | Social GAN ほか | ADE「Average L2 distance between ground truth and our prediction over all predicted time steps」・FDE「The distance between the predicted final destination and the true final destination」(m) | 30 |
| 渋谷で測られたもの | ShibuyaSocial | 横断歩道内の人数と平均速度の時系列(信号 2 周期)の RMSE・位置誤差・経路辺の正解率(§4-2) | 19 |
| 面の一致 | PLATEAU uc22-023(西新宿) | KDDI LA の平常時人流とヒートマップ比較で「70%以上の一致」(最短経路モデルより高い) | 23 |
| 破綻統計・レーン | U15-6(重なり率・壁貫通・逆走・立往生・order parameter) | CFSM 原典はレーン形成を確認し、希望速度に SD 0.1 m/s の雑音を足すと崩れると報告 | 4・U15 |

## §6 錨の表(D-122 §3-4 へ写す候補)

| # | 量 | 値 | 出典 | 等級 | 用途の区分(候補) |
|---|---|---|---|---|---|
| A1 | 自由速度(代表値) | 1.34 m/s(SD 0.26 = HM1995・GCFM が使用) | #1・#5・C9 | ◎ | 移送(段階 2) |
| A2 | 希望速度の幅 | 1.00〜1.60 m/s | C9(Bosina & Weidmann) | ◎(既出) | 移送 |
| A3 | 性差 | 男 1.41・女 1.27 m/s(+10.9%) | #13(Weidmann 経由) | ◎(RiMEA の転記) | 移送 |
| A4 | 日本の目的差 | 仕事 1.27・余暇 1.12 m/s(2 人連れ) | #14 | ◎ | 移送(向きとして) |
| A5 | 日本の年齢差 | 20-29 歳 1.18・60-69 歳 1.03・70 歳以上 0.89 m/s(2 人連れの最小年齢) | #14 | ◎ | 移送 |
| A6 | 横断の設計速度 | 1.0 m/s(下限・観測平均ではない) | #10・#11 | ◎ | 渡り切り判定の下限 |
| A7 | 避難設計速度(法定・旧版) | 1.00/1.30 m/s・階段 0.45〜0.78 m/s | #12 | ◎ | 照合外(設計値) |
| A8 | 密度-速度 | Kladek γ 1.913・ρ_max 5.4 | C9 | ◎(既出) | 較正(段階 1)の初期値 |
| A9 | 基本図の文献フロア | J_s,max 1.0〜2.0 (m·s)⁻¹・ρ 1.3〜2.3 m⁻² | #7 | ◎ | 照合の許容幅 |
| A10 | 単列の必要長 | d = 0.36 + 1.06 v m | #8 | ◎ | 列(D2)の間隔 |
| A11 | 体の大きさ | CFSM ℓ 0.3 m(原典)/ JuPedSim 半径 0.2 m / HFV 直径 0.5〜0.7 m / 体幅 0.33〜0.49 m | #4・#6・#2・C9 | ◎ | 較正 |
| A12 | time gap・緩和時間 | T 1 s(CFSM)・1.06 s(AVM 既定)・τ 0.5 s(SFM/GCFM) | #4・#6・#1 | ◎ | 較正 |
| A13 | 積分刻み | 0.01 s(原典・JuPedSim)/ 0.25 s(RVO2 例題) | #4〜#6・#3 | ◎ | dt 掃引の端点 |
| A14 | 集団率 | 55%/70% | R-42 | ◎(既出) | 移送 |
| A15 | 2 人連れの並び幅 | 0.58〜0.72 m(関係別)・余暇 0.63/仕事 0.71 m | #14 | ◎ | 群れの隊形 |
| A16 | 信号周期 | 140 s(学術 2 本・公的値なし) | #19・#20 | ○ | expedient の等級上げ候補(U15-7) |
| A17 | スクランブルの流量 | 2 流 ≈ 2,000 人/50 分(手計数)・OD 計 4,968 人/h | #19・#20 | ○/△ | 照合(holdout) |
| A18 | 渋谷の断面合計 | 11 時間合計 平日 1.02×10⁶・休日 1.18×10⁶(H28) | #21 | ○ | 照合(holdout) |
| A19 | 道玄坂の時間帯別 | 13 時間計 37,653 人(2021-03-11) | #22 | ○ | 照合(holdout・コロナ期) |
| A20 | センター街入口 | 113,568 人/12h(平日・2000 年) | #25 | ◎ | 照合(古い) |

## §7 渋谷データの取得可否の判定表(U-9)

CLAUDE.md §7 の例外 = mlit.go.jp・e-stat.go.jp・metro.tokyo.lg.jp・geospatial.jp・jma・env.go.jp・tokyo-pt.jp。**下位ドメイン(keishicho./sangyo-rodo./kankyo.metro.tokyo.lg.jp・ktr.mlit.go.jp)が例外に入るかは親の判断**。本答申では何も取得していない。

| # | データ源 | ドメイン | §7 例外 | 取得可否(事実) | 内容・粒度 | 横断者数/密度/軌跡 |
|---|---|---|---|---|---|---|
| U1 | 渋谷区 交通戦略 第 2 章 | files.city.shibuya.tokyo.jp | **外**(区公式だが lg.jp でなく一覧に無い) | PDF 公開(読める) | 11 時間合計の推移・地点図(画像) | ×/×/× |
| U2 | 渋谷区 歩行者交通量調査(原データ) | —(非公開) | — | **非公開・区からの借用の前例あり**(PLATEAU uc22-040) | 地点×方向×時間帯・調査員カウント | 断面のみ/×/× |
| U3 | 渋谷再開発協会 流動計測調査 | shibuya-redvip.com | 外(民間団体) | **Web に無い** | 断面交通量(区の図の出所) | 断面のみ/×/× |
| U4 | PLATEAU 技術資料 No.22 | mlit.go.jp | **内** | PDF 公開 | 道玄坂 1 地点の時間帯別(2021-03-11) | 断面のみ/×/× |
| U5 | 警視庁 交通量統計表 | keishicho.metro.tokyo.lg.jp | 内(下位) | CSV/PDF 公開 | 車両・自転車のみ | ×/×/× |
| U6 | 東京都 繁華街利用実態調査 | sangyo-rodo.metro.tokyo.lg.jp | 内(下位) | PDF 公開・報告書は非配布 | センター街入口 12h の 1 値(2000 年) | 断面のみ/×/× |
| U7 | 東京国道 渋谷駅周辺整備 | ktr.mlit.go.jp | 内(下位) | ページ公開 | 歩道橋 約 20 万人/日(概数) | 断面のみ/×/× |
| U8 | 東京都 環境影響評価図書 | kankyo.metro.tokyo.lg.jp | 内(下位) | **閲覧のみ・DL/複製不可・著作権は事業者** | 開発ごとの現況交通量(未閲覧) | 不可 |
| U9 | 道路交通センサス R3(手元) | mlit.go.jp | 内 | 取得済み | 箇所別基本表に歩行者の列なし | ×/×/× |
| U10 | KDDI LA(区 OD・ダッシュボード) | city.shibuya.tokyo.jp ほか | 外 | 取得済み(holdout) | 滞在 5 エリア・通行 3 ストリート×時間 | ×/×/× |
| U11 | 全国の人流オープンデータ | geospatial.jp/mlit.go.jp | 内 | 取得済み(holdout) | 1 km メッシュ滞在 | ×/×/× |
| U12 | ShibuyaSocial の軌跡 | arxiv.org | 外 | 公開の記載なし | 407 本・50 分・2 流 | ○(一部)/×/○(非公開) |
| U13 | ATR DIAMOR/ATC | irc.atr.jp | 外(研究機関) | **研究目的のみ無償**・DL 可 | 大阪の回廊・商業施設の軌跡と集団注記 | 渋谷ではない |
| U14 | Jülich Data Archive(手元 5 本) | ped.fz-juelich.de | 外 | 取得済み・CC BY 4.0 | 実験室(一方向 open/closed・ボトルネック・一方向 2013・90° 交差)。**双方向回廊は手元に無い**(アーカイブには在る=R-7) | 実験室 |
| U15 | 有償(KDDI・ジオテクノロジーズ・国際航業・Agoop ほか) | 各社 | 外 | 購入/申請 | メッシュ・点・OD | ×/メッシュ/点 |

**判定(事実の要約)**: 横断者数=**公的一次なし**(報道値と学術 2 本のみ)/ 密度-速度=**渋谷の実測なし** / 軌跡=**公開なし**(渋谷の学術は非公開・日本の公開は大阪)/ 断面交通量=**区に在るが非公開**(照会で借用の前例)。

## §8 v2 への写し方(候補と区分・推奨ではない)

1. **段階 1(mechanism・較正)**: 手元 Jülich 5 本で CFSM/AVM の基本図とボトルネックを幾何別に合わせる(U15-5 のまま)。**不足の候補**: 双方向回廊(Zhang 2012 系・同アーカイブ・CC BY 4.0)と多方向交差(Cao 2017)=スクランブルは多方向流なので、取得の可否は親判断。初期値は §1 の原典値と JuPedSim 既定の**どちらを使うかを宣言**(ℓ 0.3 vs 半径 0.2・a_min 0.18 vs 0.2・b_max 0.25 vs 0.4 の差がある)。
2. **段階 2(移送・expedient)**: 自由速度を A1〜A5 から個体化する形(性別 × 年齢 × 目的)。**日本の実測は大阪の 2 人連れ(A4/A5)だけ**で単独歩行者の値ではない=宣言。1.0 m/s(A6)は**速度の分布ではなく**「青のうちに渡り切れるか」の下限検査に使う形がある。
3. **dt**: U15-3 の掃引に 0.25 s(RVO2 例題)を足し、SFM を対照に回すなら [再計算] の 0.05 s 付近で発散するかを収束試験で確かめる形。
4. **群れ**: 集団率(A14)と並び幅(A15)で 2 人連れの隊形を置き、3 人は「<」(Costa・△)。パーソナルスペースの楕円は原典数値が取れていない=expedient。
5. **信号**: 140 s を個人ブログから「学術 2 本の一致」へ等級を上げる候補(公的値は空欄のまま)。JSAI の 3 相と U15-7 の 37/10 が数値では一致するが、相と方向の対応は原典で要確認。
6. **分割(較正/validation/test)の候補**: 較正 = Jülich・ATR(研究目的のみ=v2 の用途で使えるかは規約の判断)・原典の定数 / validation = KDDI 通行 3 ストリート(既存・開封済み)・区の 11 時間合計の推移(A18)・道玄坂の時間帯形(A19) / test = `shibuya_jinryu`(既存・封印)・スクランブルの周期あたり流量(A17)・センター街(A20)。**本書に数値を書いた量は「設計者が見た」扱いになる**(§10-3)。
7. **D-106/D 層の条件**: 「照合データが台帳に入るまで作らない」(D-106 (a))の照合データは、渋谷では公開で揃わない。道は (i) 大阪・独の軌跡で機構だけ合わせ、渋谷は断面で照合 (ii) 区への照会(U2)(iii) 自前観測(ShibuyaSocial 型の撮影=個人情報・倫理の判断が要る)(iv) 有償、の 4 つ。

## §9 未確認一覧(本文に数値を写していないもの)

1. van den Berg ら 2011(ORCA)論文中の実験の刻みと既定値(gamma.cs.unc.edu の PDF が空応答)。
2. Weidmann 1993/Buchmüller & Weidmann 2006 の**目的別速度・SD**(ETH Research Collection が HTTP 500・検索要約に出た値は写さない)。RiMEA 図 3 の年齢曲線の数値。
3. GCFM の η の選定値(図 4 のみ)。
4. Costa 2010 の cm 値・Gérin-Lajoie 2008 の楕円半径・Hall 1966 原典・西出 1985 原典。
5. Alhajyaseen & Nakamura 2010/2011(名古屋の信号横断歩道・年齢群別の速度・高齢者で容量最大 30% 減)本文(ScienceDirect 403・レビュー #16 の要約のみ)。
6. Cao ら 2017(多方向流の基本図)本文。
7. 告示 1441 の現行版(令和 2 年告示 510 号)の歩行速度表(R-8 と同じ空欄)。
8. 渋谷区 交通戦略 図 2-4/2-5 の地点値(画像)・図 2-6 の系列割り当て(本文との整合で推測)・PLATEAU No.22 の時間帯ラベルの順(図)。
9. 区の歩行者交通量調査の原データの提供条件・調査年の一覧。
10. ShibuyaSocial の撮影日・対象横断歩道の特定・データ公開の可否。JSAI 2022 の Phase 1 が歩行者現示か。
11. 警視庁/区によるスクランブルの公的な信号現示。高齢者等感応信号の延長時の想定速度。
12. モバイル空間統計・LocationMind・Agoop の利用条件・CSIS JoRAS の「公益」条件の原文。
13. J-STAGE での渋谷スクランブル対象の土木学会・建築学会論文(横断検索で表面化せず=「無い」とは断定しない)。

## §10 親への確認依頼

1. **親が一次確認すべき数値 5 件**(URL と探す文字列):
   - (a) JuPedSim の既定: `https://raw.githubusercontent.com/PedestrianDynamics/jupedsim/master/libsimulator/src/OperationalModels/CollisionFreeSpeedModel/CollisionFreeSpeedModelState.hpp` で「double timeGap{1};」「double v0{1.2};」「double radius{0.2};」、同リポ `python_bindings_jupedsim/collision_free_speed_model.cpp` で「("strength_neighbor_repulsion") = 8.0」、`python_modules/jupedsim/jupedsim/simulation.py` で「dt: float = 0.01」。
   - (b) HM1995 と HFV2000: arXiv PDF cond-mat/9805244 の p.7-8 で「αβ = 2.1m2s−2, σ = 0.3m」「∆t = 2s」「τα = 0.5s」、cond-mat/0009448 の p.4-5 で「Ai = 2 · 103 N and Bi = 0.08 m」「k = 1.2 · 105 kg s−2」。
   - (c) ShibuyaSocial: arXiv PDF 2512.18550 で「280 s, corresponding to two cycles of the traffic light」「Estimated by manual count ∼1000 ∼1000 ∼2000」「The RMSE was 0.17 m/s for Flow 1 and 0.20 m/s for Flow 2」。
   - (d) PLATEAU 技術資料 No.22(https://www.mlit.go.jp/plateau/file/libraries/doc/plateau_tech_doc_0022_ver01.pdf)PDF 36 頁で「678」〜「4,431」の並び・「2021年3月11日」「データ借用元」、33 頁で「調査員が歩」(行者交通量をカウント)。
   - (e) 渋谷区 交通戦略 第 2 章(https://files.city.shibuya.tokyo.jp/assets/12995aba8b194961be709ba879857f70/032add40cb1a4c7592a1c4ceda327f2e/assets_kankyo_000050292.pdf)PDF 8 頁で「919,700」〜「1,177,360」と「平成29 年渋谷中心地区流動計測調査報告書」。
2. **写し先と訂正の伝播**: D-122 草案 §3-4(較正の錨)・U15 設計書 U15-7(信号 140 s の等級)・PENDING の U-9 行(§7 の判定)。R-7 の「スクランブル 140 秒は個人ブログのみ」と R-42 §7-3 の「3,000 の一次なし」は、**前者を学術 2 本で補強・後者は出所(朝日 2016 → センター街 Web/渋谷再開発協会 2014)まで追跡**できた=両答申への注記の要否。
3. **封印の扱い**: §4 と §6 に渋谷の計測値(A17〜A20)を書いた。これらを test に回すなら「設計者が見た」扱いになる。**本書を正典化する前に、test 候補の値を本書から外して封印ファイルへ移すか**の判断を仰ぐ。
4. **規約**: ATR データは「research purposes only」、RiMEA は CC BY-ND 4.0、Jülich は CC BY 4.0。v2 の収益化構想との関係で ATR を較正に使えるかは親/ユーザーの判断。
