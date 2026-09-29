# R-47 答申: 古典的な活動・目的地選択モデル(ハフ型を除く)・LLM との対照・活動と注意の錨
<!-- hdr:v1 -->
- **分野**: 交通工学(活動ベース需要予測) #2 / 時間利用研究 #4 / 知覚心理学 #5 / 認知科学(記憶・習慣) #12 / 行動経済学・マーケティング科学 #16 / 小売科学・商業立地論 #17 / 自然言語処理・機械学習 #27 | **重要度**: P0(サブ判断・親が確定)
- **一次確認**: **B** = サブ実読(原典 27〔うち公式文書・業界公表 8〕・抄録 16〔うち要約モデル経由 2〕・二次 4・空欄 16 = §9)・**親検収 済(第275・下の欄)**
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 用途: D-119(System 1.5 の仮の中身を「データで較正した古典的選択モデル(分布を返す)」にする・店選びにハフ型を入れない・「古典だけ」腕・層ごとの判断の割合を毎回記録)と D-117(活動の種類=目的地つき移動/あたり/在店/その場 が看板の注視確率 p_see を変えるか)の草案の前に、先行の**入力・出力・較正データ・規模**と**数値の錨**を原典で並べる。設計の決定はしない(§8 は選択肢と根拠だけ)。
> 規律: 子サブ未起動・Web は読むだけ・ダウンロードなし・コミットなし・台帳未編集・本書の新規作成のみ。

---

---

> **親検収(2026-09-27・第275・Fable 5.1)**: 結論を変える引用のうち arXiv で読めるものを原典(HTML/PDF を標準出力に流して文字列照合・保存なし)で確認した。**一致・訂正なし**。
> - ✓ CoPB(arXiv:2402.09836 HTML): 「The strategy of integrating CoPB with gravity model can reduce the token cost by 97.7% and achieve better performance simultaneously.」
> - ✓ LLMob(arXiv:2402.14744 HTML): 「we randomly choose 100 users to model their individual activity trajectory at a 10-minute interval」/ 表 2 の MM 行「0.018 0.276 0.644 0.681」。
> - ✓ SOFAI(arXiv:2201.07050 PDF): 「the percentage of usage of S1 and S2 in each trajectory」/「after about 450 trajectories S1 is used more often than S2」。
> - △ 親未確認(JSTOR/Wiley/第三者掲載で親の経路から取れず・結論の向きは変えない): Simon 1955/1956 の逐語・Guadagni & Little の 0.875/0.812・Borgers & Timmermans 2015 の 3.64・Hyman 2010 の 25.0/51.3%・東京メトロ 2025 の 78.9%(レイアウト抽出)。設計書に写すときに再確認する。
> - §10-3(Guadagni & Little を WebFetch の自動保存一時ファイルから抽出)は「読むだけ」の範囲内と親が判定(意図した保存ではない・data/ にも置いていない)。§10-4(考慮集合の中だけの距離 logit)は**ユーザー決定「ハフ型は入れない」に触れる**ので採らない=満足化+習慣(§8-B1/B3)で行く。§10-5(個票の二次利用)は先に聞く案件として PENDING に残す。

## §0 等級と調べ方

- PDF は curl → 標準出力 → pymupdf で抽出(保存なし)。arXiv は HTML/PDF を同様に流して**生テキストへの文字列一致**で逐語を確認した。**例外 1 件**: Guadagni & Little 1983 は WebFetch が自動保存した一時 PDF から抽出した(R-45 の Concordia と同じ扱い・§10-3)。
- 逐語の確認経路が弱いもの: **[要約]** = WebFetch の要約モデル経由で生テキスト照合なし(Pieters & Wedel・Janiszewski)。**[二次]** = 他者の記述経由。
- 既存答申で親確認済みのものは再確認せず参照のみ: GenWorld・Light Society([R-38](v2-r38-closed-output-judges-research.md) §2-4)・判断の割合([R-39](v2-r39-judgment-share-research.md))・AgentSociety の欲求規則([R-44](v2-r44-code-reading-concordia-agentsociety-oasis.md))・Lyfe の非 LLM 終了/Project Sid([R-45](v2-r45-action-activity-granularity-research.md))・街路の視線配分(Fotios)と大型ビジョン VR 視認率 70.3%([チャネル予算答申](v2-channel-budget-attention-research.md) 問い2・3)・Route/Lumen([広告答申](v2-ad-information-research.md))。

| # | 出典 | 種別 | 取れた範囲 |
|---|---|---|---|
| 1 | Ben-Akiva & Bowman 2001, TR-A 35(1):1–28, doi:10.1016/S0965-8564(99)00043-9 | 原典(著者版 Draft 3・1999) | 旧著者サイト PDF(Wayback)全 47 頁 |
| 2 | Arentze & Timmermans 2004 ALBATROSS, TR-B 38(7):613–633, doi:10.1016/j.trb.2002.10.001 | 抄録 | TU/e 研究ポータル |
| 3 | Arentze, Hofman & Timmermans 2003, TRR 1831:230–239, doi:10.3141/1831-26 | 抄録 | TU/e 研究ポータル |
| 4 | Bhat, Guo, Srinivasan & Sivakumar 2004 CEMDAP, TRR 1894:57–66, doi:10.3141/1894-07 | 原典(著者版) | UT Austin 著者 PDF 全 22 頁 |
| 5 | ActivitySim 公式文書 v1.2.1(models / core)activitysim.github.io | 公式文書 | CDAP・trip purpose・scheduling・Random |
| 6 | Yamaguchi & Shimoda 2014, ASim 2014(IBPSA)pp.617–624 | 原典 | 全 8 頁 |
| 7 | Arentze & Timmermans 2009, TR-B 43(2):251–265, doi:10.1016/j.trb.2008.05.007 | 抄録 | TU/e 研究ポータル |
| 8 | 石井・福田・柳沼・日下部ほか「東京都市圏ACT の開発と都市交通政策検討への活用」第65回土木計画学研究発表会 | 原典 | ライテック公開 PDF 全 15 頁 |
| 9 | 総務省統計局「令和3年社会生活基本調査の概要」stat.go.jp/data/shakai/2021/gaiyou.html | 公式文書 | 調査の対象・集計事項 |
| 10 | Simon 1955, QJE 69(1):99–118, doi:10.2307/1884852 | 原典 | JSTOR 版スキャン(第三者掲載)§II・§III |
| 11 | Simon 1956, Psych. Rev. 63(2):129–138, doi:10.1037/h0042769 | 原典(再録) | SAGE 論集再録版(Wayback)全文・**頁は再録の頁** |
| 12 | Stigler 1961, JPE 69(3):213–225, doi:10.1086/258464 | 原典 | JSTOR 版スキャン全文 |
| 13 | Guadagni & Little 1983, Mktg Sci 2(3):203–238, doi:10.1287/mksc.2.3.203 | 原典 | JSTOR 版スキャン全文(§0 の例外経路) |
| 14 | Dubé, Hitsch & Rossi 2009(RAND JE 2010), doi:10.2139/ssrn.1361312 | 抄録 | Crossref 登録抄録 |
| 15 | Rhee & Bell 2002, J. Retailing 78(4), doi:10.1016/S0022-4359(02)00099-4 | 原典(著者版) | Penn リポジトリ PDF 抄録〜序論 |
| 16 | Hauser & Wernerfelt 1990, JCR 16(4):393–408, doi:10.1086/209225 | 原典 | MIT 掲載スキャン本文(**Exhibit の数値は画像で取れず**) |
| 17 | Reutskaja, Nagel, Camerer & Rangel 2011, AER 101(2):900–926, doi:10.1257/aer.101.2.900 | 抄録 | AEA 抄録 |
| 18 | Caplin, Dean & Martin 2011, AER 101(7):2899–2922, doi:10.1257/aer.101.7.2899 | 抄録 | AEA 抄録 |
| 19 | Huff 1963, Land Econ. 39(1):81–90, doi:10.2307/3144521 | **二次** | Liang ら 2020(arXiv:2003.10857)§3.1 の定式 |
| 20 | Borgers & Timmermans 1986, Geogr. Anal. 18(2):115–128, doi:10.1111/j.1538-4632.1986.tb00086.x | 抄録 | Crossref 登録抄録 |
| 21 | Borgers & Timmermans「Modeling pedestrians' shopping behavior in downtown areas」CUPUM 2015 | 原典 | MIT 掲載 PDF 全 20 頁 |
| 22 | Kurose, Borgers & Timmermans 2001, EPB 28(3):405–418, doi:10.1068/b2622 | 抄録 | RePEc |
| 23 | Zhu & Timmermans 2008, EPB 35:248–260, doi:10.1068/b3396 | 抄録 | RePEc |
| 24 | Zhu & Timmermans 2011, J. Geogr. Syst. 13:101–126, doi:10.1007/s10109-010-0122-8 | 抄録 | Springer |
| 25 | Zacharias 2001, J. Environ. Psychol. 21:341–352, doi:10.1006/jevp.2001.0225 | **二次** | 検索要約の抄録(原文未照合) |
| 26 | Wang ら 2024 LLMob, arXiv:2402.14744 | 原典 | HTML §4・表 2 |
| 27 | Shao ら CoPB, arXiv:2402.09836 | 原典 | HTML §4.3・§5・表 1〜2 |
| 28 | Mo ら「Large Language Models for Travel Behavior Prediction」arXiv:2312.00819 | 抄録 | arXiv abs |
| 29 | Lin ら 2023 SwiftSage, arXiv:2305.17390 | 原典 | PDF 本文+付録 |
| 30 | Yu ら 2024 Affordable Generative Agents, arXiv:2402.02053 | 原典 | HTML §5.1 |
| 31 | Ganapini ら 2022 SOFAI, arXiv:2201.07050 | 原典 | PDF 全文 |
| 32 | Laird, Rosenbloom & Newell 1986, Mach. Learn. 1:11–46, doi:10.1007/BF00116249 | 原典 | PDF §2(決定サイクル) |
| 33 | Gehl, Kaefer & Reigstad 2006, UDI 11:29–47, doi:10.1057/palgrave.udi.9000162 | 原典 | 公開 PDF 本文(**図 12 の数値は画像で取れず**) |
| 34 | Hillnhütter 2022, EPB:UAS, doi:10.1177/23998083211002839 | 抄録 | Crossref 登録抄録(CC BY) |
| 35 | Hyman ら 2010, Appl. Cogn. Psychol. 24:597–607, doi:10.1002/acp.1638 | 原典 | 公開 PDF 全文(表 1・表 2) |
| 36 | Wenczel, Hepperle & von Stülpnagel 2017, Spat. Cogn. Comput. 17:121–142, doi:10.1080/13875868.2016.1226838 | 抄録 | Semantic Scholar 登録抄録 |
| 37 | Pieters & Wedel 2007, JCR 34(2):224–233, doi:10.1086/519150 | 抄録 **[要約]** | OUP 抄録を要約モデル経由 |
| 38 | Janiszewski 1998, JCR 25(3):290–301, doi:10.1086/209540 | 抄録 **[要約]** | OUP 抄録を要約モデル経由 |
| 39 | メトロアドエージェンシー「東京メトロ広告効果調査 2025年度〈駅メディア〉」metro-ad.co.jp | 業界公表 | PDF 全 10 頁(レイアウト抽出) |
| 40 | jeki「jeki首都圏移動者調査2019」(同社ブログの引用) | 業界公表(自社引用) | ブログ本文の数値のみ |
| 41 | 福岡の商店街カメラ研究 2026, Comput. Urban Sci., doi:10.1007/s43762-026-00284-3 | 抄録 | Springer |
| 42 | Rastogi ら 2011, J. Transp. Eng. 137(10), doi:10.1061/(ASCE)TE.1943-5436.0000251 | **二次** | 検索要約の数値(原文未照合) |
| 43 | 東京都市圏交通計画協議会 データ提供ページ tokyo-pt.jp/data | 公式文書 | 施設 15 区分・提供条件 |
| 44 | e-Stat 令和3年経済センサス‐活動調査 小売業 市区町村表(sid=0004003263) | 公式文書 | 表題のみ |
| 45 | 全国家計構造調査 2019 購入先 10 区分 | **二次** | 検索要約(e-Stat 表題は確認) |
| 46 | dunnhumby「The Complete Journey」dunnhumby.com/source-files | 公式文書 | 公開ページの説明 |
| 47 | Yang ら 2015 NYC/Tokyo Check-in Dataset(Foursquare) | 公式文書 | 配布ページの説明 |

## §1 Q1 活動選択の古典モデル

**1-1 Bowman & Ben-Akiva(#1・nested logit)**: 1 日の型を 3 次元で選ぶ —「(a) the primary—most important—activity of the day, with one alternative being to remain at home for all the day's activities; (b) the type of tour for the primary activity, including the number, purpose and sequence of activity stops; and (c) the number and purpose of secondary—additional—tours」。選択肢は「a choice set of 55 alternatives in the Boston prototype」(移動なし 1+移動あり 54)。出力は分布:「yielding either a simulated activity schedule or a set of probabilities for alternatives in the choice set」。較正=「a 24 hour household travel diary survey collected in 1991」(Boston)。規模=活動パターンモデルの観測数 就業者「Number of observations = 3758」・非就業者 1474。下位(時刻・目的地・手段)の logsum が上位へ入るが「the small size indicates a rather small influence of travel utility on the choice of activity pattern」。**v2 との対応**: 「1 日の型」を先に決め中身を下位で決める階層は D-116 の二層と同じ向き。時間解像度は日・時間帯。

**1-2 ALBATROSS(#2・#3・決定木)**: 「derived from theories of choice heuristics that consumers apply when making decisions in complex environments」「predicts which activities are conducted when, where, for how long, with whom, and the transport mode involved」「A CHAID decision tree induction method is used to derive decision trees from activity diary data」。全国版では「The complete set of 27 decision trees … were newly induced from several pooled existing activity diary data sets in the Netherlands」。**出力は木の葉の規則(決定)**。日記の件数は抄録に無い=空欄。

**1-3 CEMDAP(#4・計量経済の組合せ)**: 「there are a total of 30 different models in CEMDAP」「five types of econometric models are implemented in CEMDAP: regression, hazard duration, multinomial logit, ordered probit, and location choice (with probabilistic choice set generation) models」。各モジュールは「all the relevant parameters required to produce the probability distribution for the given variable. When called upon, the module executes a forecasting algorithm to predict the corresponding choice」=**分布を持ち、呼ばれたら抽選**。較正=「the 1996 Dallas Fort-Worth (DFW) travel survey data」。試行規模=「A sub-sample of 1000 households (with a total of 2146 adults, 1473 of whom are employed)」。

**1-4 ActivitySim(#5・MNL/NL+確率表)**: CDAP は「predicts the choice of daily activity pattern (DAP) for each member in the household, simultaneously」、3 型 Mandatory/Non-mandatory/「Home: the person does not travel outside the home」。**logit でない部品**も同居: trip purpose は「assign a purpose based on an observed frequency distribution. The distribution is segmented by tour purpose, tour direction and person type」、trip scheduling は「an input lookup table of percents」(注記「Scheduling can fail if the probability table assigns zero probabilities to all the available depart times」)。時間解像度は例題で「hourly from 3 am to 3 am the next day」。乱数は「a separate, distinct, and stable random number stream for each tour type and tour number」、目的に「run the exact model with the same inputs and get exactly the same results」=**v2 の bit 一致受入と同型の要件を先行が明示**。

**1-5 東京都市圏ACT(#8・日本の実装)**: 「各モデルは基本的には多項ロジットモデル（MNL）により構築しているが，ツアー活動継続時間モデル及び立ち寄り活動継続時間モデルの2 つ関しては生存時間モデルにより構築した．また，各モデルのパラメータ推定には東京都市圏PT調査データを用いた」。継続時間は「目的地での活動時間を推計（1分単位）」、開始時刻は「1時間単位で選択」、ツアー発生回数は「計17個のモデル」。規模=「約100 万サンプルで推計したものを都市圏全体の人口に拡大」。注記「乱数シードが異なると，同じインプットでも結果が異なる」・誤差「集計値10万トリップで1%程度」。立寄目的地の説明変数「ゾーンの魅力度：事業所数、店舗数、大規模小売店舗数、保育施設数、医療施設数」=**ゾーン単位の魅力度 MNL(ハフに近い形)**。提供は都市交通計画目的に限り関東地方整備局経由(#43)。

**1-6 時間利用データからの確率モデル(#6・#9)**: Yamaguchi & Shimoda は社会生活基本調査(2006)の**個票**で、習慣行動(睡眠・仕事・食事・入浴)を先に置き、隙間を遷移確率で埋める —「After a routine behavior is ended, a random number is given to the transition probability to determine the behavior after the routine behavior」。マルコフ連鎖(Widén・Richardson)の弱点を「duration of each behavior is not necessarily reproduced」、個票依存を「only statistical data are publicly available in many countries」と整理し、公表統計だけで動く Tanimoto 法(「Mean and standard deviation of duration of activities in a day」+「Percentage of respondents who adopt the behavior (PB) at a specific time of a day」=**時間帯別行動者率**)を紹介。規模「approximately 80 thousands households … around 200 thousands」、調査票 A「20 classifications」、B「85 kinds」だが B の標本は就業男性平日「1.5 thousands」。2021 調査は「約9万1千世帯の10歳以上の世帯員約19万人」・調査票 A で「時間帯別の生活行動の状況」を集計(#9)。**v2 との対応**: D-119 の「行動者率を事前分布に」は Tanimoto 型で、公表統計だけで作れる。状態(空腹等)の係数は公表統計からは識別できない(§8-A1)。

**1-7 欲求の閾値モデル(#7)**: Arentze & Timmermans 2009「utilities of activities are a dynamic function of needs」「individuals use a utility-of-time threshold parameter to decide when to include an activity in their agenda. The threshold represents a personal perception of time pressure and is continuously adapted based on learning」。**離散選択でない古典**(閾値規則)で D-118 と接続できる形。AgentSociety の欲求閾値(R-44)は同系の実装例。

## §2 Q2 目的地・店選び(ハフ型でない古典)

**2-1 Simon の満足化(#10・#11)**: 1955 p.110「In most global models of rational choice, all alternatives are evaluated before a choice is made. In actual human decision-making, alternatives are often examined sequentially. We may, or may not, know the mechanism that determines the order of procedure. When alternatives are examined sequentially, we may regard the first satisfactory alternative that is evaluated as such as the one actually selected.」願望水準は動く:「as the individual, in his exploration of alternatives, finds it easy to discover satisfactory alternatives, his aspiration level rises; as he finds it difficult to discover satisfactory alternatives, his aspiration level falls.」1956 は**空腹の生物の探索モデル**そのもの —「(a) it explores the surface at random, watching for a food heap; (b) when it sees one, it proceeds to it and eats」「when the organism reaches either its hunger or thirst threshold, it will begin exploration」「it has a definite, fixed aspiration level」、結論「Evidently, organisms adapt well enough to “satisfice”; they do not, in general, “optimize.”」。視程 v を持ち「if there is food at any of the branch points within v moves of the organism’s present position, it can select the proper paths and reach it」。**v2 との対応**: 空腹の閾値→探索→**見えた**店へ、は D-118+D-119 の「見えている順の満足化」と構造が一致。

**2-2 探索の経済学(#12)**: 「A buyer (or seller) who wishes to ascertain the most favorable price must canvass various sellers (or buyers)-a phenomenon I shall term "search."」。習慣との接点:「goodwill may be defined as continued patronage by customers without continued search (that is, no more than occasional verification)」。広告:「Advertising is, among other things, a method of providing potential buyers with knowledge of the identity of sellers.」

**2-3 習慣・慣性(#13・#14・#15)**: Guadagni & Little「loyalty is taken to be the exponentially weighted average of past purchases of the brand, treated as 0-1 variables」。平滑定数は例示計算「(3.92)(0.875)(0.125)(1) + (2.97)(0.812)(0.188)(1) = 0.88」から**銘柄 0.875・サイズ 0.812**(係数 3.92/2.97)。較正「32 weeks of purchases of regular ground coffee by 100 households」・holdout 100 世帯・「1021 usable purchases」。Dubé ら: 慣性は構造的で「Our data are consistent with loyalty, but not with search or learning.」。**店への慣性**: Rhee & Bell「Data from 548 households taking 88,945 shopping trips among five stores」「nearly three quarters of the consumers show progressive attachment to a main store」、しかも「not simply driven by location」。

**2-4 考慮集合・知覚順(#16・#17・#18)**: Hauser & Wernerfelt が引く Hauser 1978:「The consideration sets account for 78 percent of the explainable uncertainty; the logit model accounts for only 22 percent.」市場の銘柄数は「in the range of 6 to 47」、考慮集合の平均値(消臭剤 3.9 等)は Exhibit が画像で**原典から取れず [二次]**。Reutskaja ら(視線計測):「subjects use a stopping rule to terminate the search process that combines features of optimal search and satisficing, and that subjects search more often in certain focal regions of the display, which leads to choice biases」=**見える位置が選択を歪める**。Caplin ら:「most subjects search sequentially, stopping when a "satisficing" level of reservation utility is realized」。

**2-5 歩行者の店舗選択(#20〜#25)**: Borgers & Timmermans 1986 は「three submodels: one for destination choice, one for route choice, and one for impulse stops」(Maastricht)。2015 版は「The attraction of outlets depends on the type and size of the outlets, the distance to the outlets, whether the outlets can be seen, have been passed or visited before …」、店の前では「he/she will consider visiting each outlet (randomly ordered) connected to that node」=**店の前に来たときだけの二値選択**(床面積・同種店を通過した回数・同種店に入ったか)。「Not Visit」定数 3.64(入らないのが既定)・「the rho2 is equal to 0.88」・「Over 1700 complete and circular trajectories」・「approximately 215.000 choice sets」。注意: 通りの選択には床面積×距離の項があり**ハフ型の要素を含む**。Kurose ら:「shopping pedestrians will never leave the attractive shopping streets before completing their shopping」。Zhu & Timmermans 2008: 満足化の cut-off モデルは「can fit the data equally as well as the multinomial logit model」、2011:「the heuristic models are the best for all the decisions that are modeled」「The predictions of heuristic models are slightly better than those of the multinomial logit models」(北京 王府井)。Zacharias 2001 [二次]: 人・看板・プランター・日よけを写真で入れ替えると経路の好みが移った(Montpellier・45 人)。

**2-6 ハフモデル(除外理由を書くための定義・#19 [二次])**: Liang ら 2020「The Huff model proposes that there are two major factors affecting the number of potential customers of a store, which is essentially a gravity-based spatial interaction model」、P_ij = (S_j^α / D_ij^β) / Σ_j (S_j^α / D_ij^β)(S=魅力度・D=距離・n 店すべてが分母)。**全店が選択肢集合に入る**点が、§2-1・2-4 の「見えたもの/考慮集合の中だけ」と対立する。

## §3 Q3 LLM と古典の対照(ablation)

- **LLMob(#26)**: 東京の Foursquare 系軌跡から「randomly choose 100 users」「at a 10-minute interval」。古典「Markov-based mechanic model (MM)」ほか深層 5 種と JSD で比較。通常期で MM は SD 0.018・SI 0.276・DARD 0.644・STVD 0.681、LLMob-E は 0.053・0.046・0.125・0.559。**移動距離(SD)は古典が勝ち、活動×時刻(DARD)は LLM が「roughly 1/2 to 1/3 JSD compared to the best of baselines」**。
- **CoPB(#27)**: LLM は意図列だけを作り、場所は重力モデルへ —「integrating CoPB with gravity model can reduce the token cost by 97.7% and achieve better performance simultaneously」。LLM に POI を選ばせる腕(CoPB_wo/Gravity)より品質が高いと報告。古典 TimeGeo(Tencent)は radius 0.259・itdErr 0.536、CoPB は 0.019・0.194。**ハフ除外(D-119)への反対証拠の一つ**(§8-B)。
- **Mo ら(#28)**: ゼロショット LLM と埋め込み+教師あり学習は「comparable to, and in some cases competitive with, classical models such as multinomial logit, random forest, and neural networks」。
- **SwiftSage(#29)**: LLM を呼ばない小モデル単独腕 —「only agent (770m) achieves an overall performance of 49.22」、併用で「average score of 84.7」。tokens per action は SayCan 1,855.84・ReAct 1,971.03・SwiftSage 757.07。
- **AGA(#30)**: 繰り返す推論を方策の再利用に置換 —「the cost of using only the Lifestyle Policy is 40.2% of the original … the full AGA framework is 31.1%」、25 人町で 42.7%。
- 参照のみ: Light Society の「all-LLM, all-surrogate, and per-sample weighted routing」と置換率 0〜100% 掃引・GenWorld の lookup(R-38)/Lyfe の非 LLM 終了(R-45)/AgentSociety の欲求→計画の規則部分(R-44)。**「LLM 0 呼」の完全な古典腕を置いた先行は、読んだ範囲では LLMob・CoPB の古典ベースラインと SwiftSage の Swift-only のみ**。

## §4 Q4 層ごとの判断の割合の記録

- **SOFAI(#31)**: 速い S1・遅い S2・メタ認知で「the percentage of usage of S1 and S2 in each trajectory」を図示し「after about 450 trajectories S1 is used more often than S2」。**層の使用率を時系列で報告した直接の先行**。注意: 振り分けに S1 の confidence を使う設計で、R-38/R-39 の「自己申告 confidence は妥当性の指標にならない」とは別系統。
- **Soar(#32)**: 「Every problem-solving episode consists of a sequence of decisions」、直接の知識で決まらないとき「causing an impasse」→下位目標で解く=**「どの層が決めたか」は impasse の有無として構造的に記録できる**(使用率の統計値は読んだ範囲に無い)。
- SwiftSage の tpa・AGA の費用比は割合の代理指標。R-39 のとおり**人の判断の割合を直接測った一次は無い**。ゲーム AI の behavior 使用率・ACT-R の production compilation の比率は空欄(§9)。

## §5 Q5 活動と注意(D-117 の錨)

- **歩行中の副課題(#35)**: 151 人(単独 78・通話 24・音楽 28・二人連れ 21)。道化を見たか(直接質問)通話 **25.0%**・単独 51.3%・音楽 60.7%・二人 71.4%、自発報告は 8.3/32.1/32.1/57.1%。横断時間(秒)通話 82.53・単独 74.81。「Only 25% of the cell phone users had noticed the clown」。
- **活発な店先で歩行が遅く止まる(#33)**: 「Pedestrians move slower in front of the city’s active facades, more people stop」「the number of stops and other activities is seven times greater in front of active rather than passive facades」「Moving at 5 km an hour, they have time to take in everything around them.」図 12(止まる・首を向ける %)は画像で空欄。
- **環境で頭の動きが変わる(#34)**: 「Head movements increase by 71% and looking down decreases by 54%, compared to environments designed for cars.」「Shop windows receive prolonged viewings」。
- **目的の有無で見る対象が変わる(#36〜#38)**: Wenczel ら「intentional learning led to a stronger focus on landmarks at structurally salient locations. In contrast, landmarks with a higher level of visual salience attracted generally more fixation time. This finding remained unaffected by learning intention.」=**顕著性の効果は目的に依らず、目的は「何を」見るかを変える**。Pieters & Wedel [要約]「ad informativeness is goal contingent」。Janiszewski [要約] 目的探索は「stored search routines to collect information in a deliberate manner」、探索的探索は情報が多く手順の知識が乏しいとき。
- **移動目的と速さ(#41・#42)**: 福岡の商店街カメラ 1 年分で「morning commuters walked faster and were more sensitive to temperature」(目的は時間帯からの推定と読める [推測])。Rastogi [二次]: exercise 74.57 m/min・leisure 62.44 m/min。
- **日本の交通広告(#39・#40)**: 東京メトロ調査の「広告注目率」は媒体前を通過した人に広告を提示して「細かい文字まで見た」「写真・絵（映像）・大きな文字だけ見た」「見たような気がする」と答えた割合(面接・自己申告・視線計測ではない)。渋谷駅集中展開 駅メディアは 21.3+52.3+5.3=**78.9%**(素材 5・n=526・到達率 80.2%)。**移動目的別の内訳は本文に無い**。jeki 首都圏移動者調査2019 の駅構内のすごし方「スマートフォンを使う(55.5％)」「駅のポスター・看板を見る(28.4％)」「屋外看板や街頭ビジョンを見る(19.3％)」。
- **錨の有無**: 「通勤 vs 散策」で**広告の視認率そのもの**を比べた一次は日本・海外とも見つからなかった(空欄)。錨にできるのは (i) 副課題で気づきが約半分(Hyman)、(ii) 活発な店先で停止・頭の動きが増える(Gehl・Hillnhütter)、(iii) 目的は顕著性でなく対象を変える(Wenczel)、(iv) 目的別の歩行速度差(福岡・Rastogi)の 4 本。

## §6 Q6 満足化+習慣を較正できるデータ

| データ | 中身(原文) | 公開 | v2 受入表との対応 |
|---|---|---|---|
| 社会生活基本調査 2021(#9) | 約19万人・調査票 A で「時間帯別の生活行動の状況」 | 集計表は公開・個票は二次利用の申請 [推測] | 時間帯別行動者率=**活動の事前分布**と在圏・行動分布の錨 |
| 東京都市圏 PT 2018(#43) | 「施設 15区分」(大規模小売店・小規模小売店・飲食施設 等)・「時間帯 26区分」・平日 1 日 | 集計システムは公開・個票は関東地方整備局へ申請 | 施設種別×時間帯の到着=**店カテゴリの選好**の錨(個店ではない) |
| 経済センサス R3(#44) | 「産業分類小分類別事業所数、従業者数、年間商品販売額及び売場面積（小売業）」市区別 | 公開 | 渋谷区の店の母集団(規模)。**来店の集中度は無い** |
| 全国家計構造調査 2019(#45 [二次]) | 購入先 10 区分(スーパー・コンビニ・百貨店 等)の支出 | 公開 | 業態別支出シェア=購入の業態分布の錨 |
| Foursquare Tokyo(#47) | 「573,703 check-ins in Tokyo」・2012-04-12〜2013-02-16・「fine-grained venue-categories」 | 研究用に公開 | **個人×店の繰り返し**=上位 k 店集中度・習慣の平滑定数を推定可能 |
| dunnhumby Complete Journey(#46) | 「household level transactions over two years from a group of 2,500 households who are frequent shoppers at a retailer」 | 公開 | 1 小売チェーン内(店 ID の有無は未確認)・米国食品。慣性の形の参考 |
| Rhee & Bell 型パネル(#15) | IRI 548 世帯・5 店 | 非公開 | 「主店への愛着が約 3/4」の比較値 |

- 日本の ID-POS・交通系 IC の購買履歴で公開のものは見つからなかった。**上位 k 店の占有を集計値で持つ公的統計も見つからなかった**(経済センサスは供給側の規模のみ)。

## §7 横断表

| 出典 | 入力の特徴量 | 出力 | 較正データ | 規模 | v2 で使えるか |
|---|---|---|---|---|---|
| Bowman & Ben-Akiva 2001 | 属性・下位 logsum | 55 型の確率 | Boston 1991 日記 | 就業 3,758・非就業 1,474 | 形は可。解像度は日 |
| ALBATROSS 2004/2003 | 状況・時空間制約 | 木の葉の決定 | 蘭 日記(複数統合) | 木 27 本・件数空欄 | 個票が要る |
| CEMDAP 2004 | 土地利用・属性・LOS | 分布から抽選 | DFW 1996 | 30 モデル・試行 1,000 世帯 | 部品の型(生存時間)を参照 |
| ActivitySim | 属性・世帯・時間窓 | MNL/NL の抽選+確率表 | 各都市の調査 | 都市圏 | 乱数流の設計(bit 一致)を参照 |
| 東京都市圏ACT | 属性・残り時間・ゾーン魅力度 | MNL+生存時間(1 分) | 東京 PT 2018 | 約 100 万標本 | 最も近い日本の先行。入手は目的限定 |
| Yamaguchi & Shimoda 2014 | 属性 7 類型・時刻・直前行動 | 遷移確率+継続時間分布 | 社会生活基本調査 2006 個票 | 約 20 万日記 | Tanimoto 型は公表統計で可 |
| Arentze & Timmermans 2009 | 欲求・時間予算 | 閾値規則 | 例示シミュレーション | — | D-118 と接続可(形のみ) |
| Simon 1955/1956 | 順次に見える選択肢・願望水準・空腹閾値 | 最初の満足解 | 理論 | — | 店選びの骨格そのもの |
| Guadagni & Little 1983 | 指数平滑の愛着・価格・販促 | MNL 確率 | コーヒー 100 世帯 32 週 | 1,021 購入 | 習慣項の形(定数は要再推定) |
| Rhee & Bell 2002 | 主店在籍期間・属性 | 離脱確率(probit) | IRI 548 世帯 | 88,945 回 | 慣性の比較値 |
| Hauser & Wernerfelt 1990 | 評価費用 | 考慮集合の大きさ分布 | 既存研究+Assessor | 6〜47 銘柄 | 「集合の中で選ぶ」の根拠 |
| Borgers & Timmermans 2015 | 視認・通過・既訪・床面積 | 通り選択 MNL+店前の二値 | 蘭 2 都市の聞き取り | 1,700 軌跡・21.5 万選択 | 店前二値は v2 のセル構造に近い |
| Zhu & Timmermans 2008/2011 | 閾値の異質性 | cut-off/辞書式の決定 | 北京 王府井 | 件数空欄 | 満足化が MNL と同等以上の実証 |
| Huff 1963 [二次] | 魅力度・距離 | 全店への確率 | 商圏 | — | 除外対象(全店が選択肢) |
| LLMob 2024 | 軌跡・動機 | 軌跡生成 | 東京 Foursquare 系 | 100 人 | 4 指標を古典腕の比較に流用可 |
| CoPB | 意図(LLM)+重力 | 軌跡 | 中国 2 データ | — | 反対証拠(重力が LLM の選択に勝つ) |
| SOFAI 2022 | 経験・信頼度 | S1/S2 の振り分け | 格子環境 | 1,000 軌跡 | 層使用率の記録形式 |
| Hyman 2010 | 歩行中の副課題 | 気づいた割合 | 大学広場 | 151 人 | 「その場+通話」系の減衰の錨 |
| Gehl 2006 / Hillnhütter 2022 | 店先の活発さ・環境 | 停止・頭の動き | コペンハーゲン 7 地区/抄録のみ | — | 在店・あたり の上振れの錨 |
| 東京メトロ 2025 | 媒体前通過 | 自己申告の注目率 | 駅頭面接 | 渋谷 n=526 | 駅媒体の比較値(視線ではない) |

## §8 設計の選択肢(推奨ではない)

**A. System 1.5 の古典モデルの形**
- A1 **行動者率の事前分布×条件付きロジット**(ActivitySim・T-ACT・Bowman 型): 社会生活基本調査の時間帯別行動者率(性年齢・曜日)を基準効用にし、状態(空腹の語・場所種別・カレンダー)の係数を足す。根拠 #1・#5・#8・#9。弱点: 公表統計は集計値なので**状態の係数は識別できず、置いた時点で expedient**(感度腕が要る)。
- A2 **Tanimoto/Yamaguchi 型(継続時間分布+遷移)**: 習慣行動を先に置き隙間を遷移で埋める。根拠 #6。T-ACT も継続時間は生存時間(1 分)で別モデル(#8)。二層(D-116)の「活動=持続」と相性がよい。弱点: 遷移確率は個票が要る。
- A3 **欲求閾値の規則**(Simon 1956・Arentze 2009): D-118 の収支が閾値を越えたら探索を起こす。根拠 #7・#11。係数が少なく指紋が小さいが閾値は宣言値。
- A4 **決定木**(ALBATROSS): 個票が要り、日本の公開データでは作れない(#2・#3)。
- 共通: 解像度は調査 15 分・T-ACT の開始時刻 1 時間/継続 1 分。1 分 tick に渡すには継続時間側で解像度を持つ(A2)か、15 分枠内を一様とする宣言が要る。

**B. 店選び=満足化+習慣の形**
- B1 **Simon 1955 の順次満足化**: B2 に見えている順(近い順/視認順)に評価し、願望水準を最初に超えた店。水準は見つけやすさで上下(p.111)。根拠 #10・#17・#18・#23・#24。
- B2 **店前の二値選択**(Borgers & Timmermans 2015): 店の前のセルに来たときだけ「入る/入らない」を抽選(床面積・同種店を通過した回数・既訪)。根拠 #21。v2 のセル単位の知覚と整合。
- B3 **習慣項**: Guadagni & Little の指数平滑を「最近の店」の重みに。0.875 はコーヒー銘柄の値で、店・渋谷には再推定が要る(Foursquare Tokyo で推定可能 #47)。慣性の構造性は #14・#15。
- B4 **考慮集合の中だけの MNL**(折衷): 考慮集合=見えている店∪習慣の店、その中で距離と魅力度の logit。Hauser 1978 の 78%/22% が「集合の限定が主」の根拠(#16)。**集合内はハフに近い形になる**ため、ユーザー決定「ハフ型は入れない」との関係は要確認(§10-4)。
- 反対証拠(記録): CoPB は重力モデルで場所を決める方が LLM に選ばせるより良く安い(#27)、T-ACT の立寄目的地もゾーン魅力度 MNL(#8)。ただし両者は POI/ゾーン集合を**全部知っている前提**で、v2 が歩行者の知覚範囲(B2)で選ぶ設計とは前提が違う。

**C. 活動→注意(p_see)の条件づけ**
- C1 **活動種別の乗数**(D-117 (a)): その場+副課題(通話・会話中)=Hyman の比(25.0/51.3)を下向きの錨、在店/あたり=Gehl・Hillnhütter(停止 7 倍・頭の動き +71%)を上向きの錨、目的地つき移動=基準。**乗数そのものの一次は無い=expedient・感度腕**。
- C2 **歩行速度経由**: 活動→速度(通勤は速い #41・#42)→看板の前の滞在時間→p_see。既存の知覚契約(0.1 秒刻み・δ_min)と接続する形。
- C3 **「何を見るか」だけ変える**: Wenczel(顕著性は目的に依らない)に従い p_see は据え置き、目的地つき移動では**目的に関係する看板の重み**だけ上げる。Pieters & Wedel [要約] と整合。
- 比較値: 大型ビジョン VR 70.3%(既存答申)・東京メトロ渋谷の自己申告注目率 78.9%(定義が違う=並べるときは注記)。

**D. 「古典だけ」腕の指標**
- D1 LLMob の 4 指標(SD・SI・DARD・STVD の JSD)を v2 の受入表(在圏・行動分布)と並べる。LLMob では古典 MM が SD で勝ち DARD で負けた=**「LLM が何を足すか」は活動×時刻の分布に出る**という先行の結果。
- D2 層使用率を SOFAI 形式で(時間帯×層の % を毎 run)。R-38 の Light Society の置換率掃引(0〜100%)と同じ軸で「System 2 の割合 vs 受入表の誤差」を描ける。
- D3 費用は SwiftSage/AGA 型(呼数・token/行動)を併記。

## §9 空欄・未確認

1. ALBATROSS の日記件数(抄録に無い)。2. Widén/Richardson/Tanimoto の原典(Yamaguchi の記述経由のみ)。3. ATUS を用いたマルコフ/生存モデルの原典(未読)。4. Huff 1963 原典(JSTOR のみ・二次で代替)。5. Hauser & Wernerfelt の Exhibit 数値(画像)。6. Gehl 図 12 の %(画像)。7. Zacharias 2001 本文(抄録も二次)。8. Borgers 1986 の impulse stop の関数形。9. **移動目的別(通勤/私用/散策)の広告視認率の一次(日本・海外とも)**。10. 東京メトロ調査の銀座・表参道ブロックの帰属(レイアウト抽出で不確実・渋谷ブロックのみ連続)。11. ゲーム AI の behavior 使用率・ACT-R production compilation の比率。12. dunnhumby の店 ID 列の有無。13. 社会生活基本調査の個票の利用条件(二次利用申請の要否は [推測])。14. Rastogi の数値(二次)。15. Pieters & Wedel・Janiszewski の逐語(要約モデル経由)。16. 全国家計構造調査 2019 の購入先別シェアの数値(未取得)。

## §10 親への確認依頼

1. **逐語照合**: §5 の Pieters & Wedel「ad informativeness is goal contingent」と Janiszewski の 2 句は要約モデル経由。設計書に写すなら原文照合を。
2. **東京メトロの数値の帰属**: 渋谷 78.9%(21.3/52.3/5.3・n=526)は PDF のレイアウト抽出。写すなら PDF 目視で。
3. **Guadagni & Little の取得経路**: WebFetch が自動保存した一時 PDF を抽出した(§0)。規律上の扱いの確認を。
4. **ハフ除外と CoPB の反対証拠**: §8-B4(考慮集合内の距離 logit)がユーザー決定「ハフ型は入れない」に触れるか。触れるならユーザー判断。
5. **A1 の状態係数は識別不能**: 公表統計だけでは空腹等の係数を推定できない。個票(社会生活基本調査の二次利用・PT 個票)に進むかは現実データへの接触=先に聞く案件。
6. **Simon 1956 の頁**: 再録版の頁なので、設計書には原誌 63(2):129–138 のみを書き、頁番号は付けない方が安全。
