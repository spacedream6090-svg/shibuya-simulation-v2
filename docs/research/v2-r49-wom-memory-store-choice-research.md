# R-49 答申: 記憶・口コミ(WOM)にもとづく店選び — 伝播モデル・評価の効果・出どころ別の重み・記憶の減衰・記憶の候補集合・LLM シミュの場所記憶・計測
<!-- hdr:v1 -->
- **分野**: 行動経済学・マーケティング科学 #16 / 社会ネットワーク科学 #14 / 認知科学(記憶・習慣) #12 / 小売科学・商業立地論 #17 / 計算社会科学 #25 | **重要度**: P0(サブ判断・親が確定)
- **一次確認**: **B** = サブ実読(原典本文 17〔うち業界公表 3〕・抄録 10・二次 12・空欄 = §9)・**親検収 済(第278・下の欄)**
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 用途: 店ごとの記憶(評価の向き・出どころ=自分で行った/人から聞いた/看板/ネット・確からしさ・記憶した時刻)を構造化し、会話(System 2)から「店名と評価」を抽出して書き、店選び(System 1.5=古典的選択モデル)が「見えている店」+「記憶にある評価の良い店」から選ぶ設計の前に、先行の形と数値の錨を並べる。前提は [草案 §2-2](../design/v2-hunger-choice-attention-draft.md)(見えている順の満足化+習慣・距離減衰なし・ハフ型は入れない)。設計の決定はしない(§8 は候補と区分だけ)。
> 規律: 子サブ未起動・Web は読むだけ(PDF は curl → 標準出力 → pymupdf・保存なし)・ダウンロードなし・コミットなし・台帳未編集・本書の新規作成のみ。

---

> **親検収(第278・2026-09-27・親=Fable 5.1)**
> - 一次照合した引用(親が同じ URL を curl → 標準出力 → 文字列照合・保存なし): ✓ リクルート 2024(#12)「グルメサイト、口コミサイト」26.4%・「店構えや店先のメニューなど」22.2%・「家族・友人・知人等からの口コミ」14.7%・SNS 11.1%・3 圏域計 n=6,487(表の行「6,487 26.4 22.2 14.7 11.1 …」も一致)/ ✓ Generative Agents(#27)「Our decay factor is 0.995」「exponential decay function over the number of sandbox game hours since the memory was last retrieved」/ ✓ CitySim(#36)「daily decay with λ = 0.03」「imputed from the k = 10 most similar visited locations」「affinity, trust, and familiarity」「σ_b(0)=0.25 and σ_o=0.2」/ ✓ Luca 2016(#6)「a one-star increase in Yelp rating leads to a 5-9 percent increase in revenue」「largest when a restaurant has many reviews」/ ✓ Zhao ら 2013(#19)「We model the review credibility as the precision」「1,919 book purchases by 243 consumers」。
> - 訂正: なし(数値の写しは一致)。「店頭で決めた初回 ≈ 5%」は 2 調査の掛け算=[推測]のまま設計書へ(§10-5 どおり)。
> - 写し検査・訂正の伝播検査・循環参照検査・フロア併記検査: 設計書への写し先は [記憶・口コミ・ネットの草案](../design/v2-memory-wom-internet-draft.md) §1(D-120)。循環参照=「既存答申」経由の EPR γ・初回 22.5%・Watts & Dodds は親確認済みの行を引いており D 等級ではない。フロア併記=eWOM 弾力性の研究間 SD(.526/1.491)を §2 で併記済み。holdout(C1/C3/C4)に口コミの定数を当てない運用に親も同意(§10-1)。
> - 規律上の判定(取得経路など): 子サブなし・保存なし・登録なし=規律内。AgentSociety のコード読みは R-44 と同じ commit の raw を標準出力で読んだ=読むだけ。

## 要約

1. **伝播モデル**: Bass 型(p≈0.03/q≈0.38 は二次経由=△・しかも台帳 C4 は **holdout** なので較正に使えない)、Goldenberg ら 2001 の確率セルオートマトン(強い紐帯/弱い紐帯/広告の 3 確率。「弱い紐帯は強い紐帯と同等以上」は追試で「3 分の 1 未満」と否定)、Watts & Dodds 2007(既存答申)。v2 の「同セルの会話で聞く」(B4b)に写せるのは **接触ごとの伝達確率**の形で、集計の p・q は照合専用。
2. **評価の効果(米国)**: Yelp 1 星で売上 5〜9%(独立店のみ・チェーンは効果なし=Luca ◎)、半星で満席 +19 pp(Anderson & Magruder △)、1 星レビューの効果 > 5 星(Chevalier & Mayzlin ◎)。eWOM の弾力性は量 .236・評価 .417(メタ分析 ◎・研究間 SD 1.491 と散らばりが大きい)。食べログの因果推定は見つからなかった(空欄)。
3. **日本の「通りがかり」**: 初めて利用した夕方以降の店で「期待に最も影響した情報源」は グルメサイト・口コミサイト **26.4%**・**店構えや店先のメニューなど 22.2%**・家族・友人・知人等からの口コミ **14.7%**・SNS **11.1%**(リクルート 2024・n=6,487・業界 ◎)。外食回数の 22.5% が初回(2018・親確認済)。掛け合わせると「店頭で決めた初回」は外食全体の **5% 前後**[推測・調査の混合]。
4. **出どころ別の重み**: **比の数値の錨は無い**。順序の錨だけ(対面の口コミ > 印刷・自分の既存の印象があると口コミの効果が消える=Herr ら ○/知人の推薦 83% > ブランドサイト 70% > ネットの消費者意見 66% の信頼=Nielsen 業界 ○)→ **宣言+感度腕**。
5. **「確からしさ」を数値にした先行はある**: ベイズ学習の「信号の精度」(Erdem & Keane 1996=使用経験と広告を雑音つき信号として更新・指数平滑より適合/Zhao ら 2013=「review credibility as the precision」/Luca=レビュー数が多いほど反応が大きい)、忘却=想起の雑音が時間とともに増える(Mehta ら 2004)、CitySim の Kalman(σ_o=0.2・σ_b(0)=0.25・中立への回帰 λ=0.03/日)。
6. **減衰の桁が 2 桁散る**: GA 0.995/時(半減 5.8 日・根拠の記述なし)/CitySim λ=0.03/日(半減 22.8 日)/ACT-R d=0.5(べき・CMU 教材の「normal value」・v2 は既決)/WOM の持ち越し 21 日 vs 販促イベント 5 日(Trusov ◎)/広告の効果期間 6〜9 か月(Leone ○)・業界の半減 2〜5 週(△)→ 宣言+感度腕。
7. **「見える店+記憶の店」の合成**: Lynch & Srull の stimulus/memory/mixed の区別(△)、想起が評価と独立に選択を動かす(Nedungadi ○)、「見える・通った・入ったことがある」を同じ式に入れた歩行者の店選び(Borgers & Timmermans 2015=R-47)、探索 vs 回帰 P_new=ρS^−γ(EPR・γ は親確認済)が骨格。
8. **LLM シミュの場所記憶**: 場所×評価を構造化して持つのは **CitySim だけ**(4 次元の信念+不確かさ・**訪問したときだけ更新**)。**出どころ(伝聞/看板/ネット)で分けた場所の記憶は、読んだ範囲では無い**。GA・Lyfe・RecAgent は自由文、AgentSociety v1 は店の評価記憶なし(重力=密度/距離²)。
9. **計測**: Salganik ら 2006 の「独立の世界 1 つ vs 社会的影響の世界 8 つ」で Gini と不予測性 U を測った設計が、口コミ腕 × 看板腕 × seed(=世界)にそのまま写せる。
10. **LLM の失敗様式**: 伝聞の脚色(GA)・評価の同調収束(RecAgent: 3〜8 点→6〜7 点)・有名ブランドへの偏り(CitySim)→ 抽出は**閉じた POI 集合への照合**が前提。

## §0 等級と調べ方・出典表

- 等級: **◎** = 原典(本文または公式抄録)を生テキストで文字列照合し、親も同じ URL で再取得できる / **○** = 原典実読だが抄録のみ・第三者掲載・レイアウト抽出 / **△** = 二次経由(他論文の記述・検索要約) / **×** = 未確認。[業界] = 査読なしの公表調査。[サブ計算] = 本書での算術。
- 既存答申で扱ったものは再確認せず参照: Watts & Dodds 2007・Bakshy 2011・Goel 2016・Centola 2010・Berger & Schwartz 2011([広告答申](v2-ad-information-research.md) 方面 3)/ホットペッパー 2018・EPR(Song 2010)([選好ベクトル答申](v2-preference-vector-research.md) §2・親確認 4 件)/Hauser & Wernerfelt・Borgers & Timmermans・Guadagni & Little([R-47](v2-r47-classical-choice-attention-research.md) §2)/CitySim の渋谷 POI 偏り([lit](lit/leisure__bougie2025_citysim-shibuya-poi.md))/AgentSociety v1 のコード([R-44](v2-r44-code-reading-concordia-agentsociety-oasis.md) と同じ commit を再読)。

| # | 書誌 | URL | 等級 | 取れた範囲 |
|---|---|---|---|---|
| 1 | Sultan, Farley & Lehmann 1990, JMR 27(1):70–77 | https://doi.org/10.1177/002224379002700107 | △ | Nam 2011 経由の p・q のみ |
| 2 | Nam 2011「Demystifying the Bass Diffusion Model」WP | https://web-docs.stern.nyu.edu/marketing/SNamPaper.pdf | ○ | 本文(上の引用と q の過大推定の主張) |
| 3 | Goldenberg, Libai & Muller 2001, Mktg Lett 12(3):211–223 | https://doi.org/10.1023/A:1011122126881 | ○ | Springer 抄録 |
| 4 | Winzar 2007, ANZMAC 2007 pp.173–179(追試) | https://researchers.mq.edu.au/en/publications/a-replication-and-extension-of-goldenberg-libai-amp-muller-a-comp | ○ | 抄録 |
| 5 | Trusov, Bucklin & Pauwels 2009, JM 73(5):90–102 | https://www.anderson.ucla.edu/documents/areas/fac/marketing/bucklin_effects.pdf | ◎ | 著者版全文 |
| 6 | Luca 2016, HBS WP 12-016 | https://www.hbs.edu/ris/Publication%20Files/12-016_a7e4a5a2-03f9-490d-b093-8f951238dba2.pdf | ◎ | 全文 41 頁 |
| 7 | Anderson & Magruder 2012, EJ 122(563):957–989 | https://doi.org/10.1111/j.1468-0297.2012.02512.x | △ | 抄録を検索要約経由(PDF 取得失敗) |
| 8 | Chevalier & Mayzlin 2006, JMR 43(3):345–354(NBER w10148) | https://www.nber.org/system/files/working_papers/w10148/w10148.pdf | ◎ | 抄録 |
| 9 | You, Vadakkepatt & Joshi 2015, JM 79(2):19–39 | https://business.ucf.edu/wp-content/uploads/2015/04/meta-analysis-JM-published.pdf | ◎ | 全文(表 3) |
| 10 | Babić Rosario ら 2016, JMR 53(3):297–318 | https://digitalcommons.du.edu/marketing_fac/2/ | ○ | 機関リポジトリ抄録 |
| 11 | Muchnik, Aral & Taylor 2013, Science 341:647–651 | https://doi.org/10.1126/science.1240466 | △ | 検索要約の抄録 |
| 12 | リクルート ホットペッパーグルメ外食総研 2024-05-28 | https://www.recruit.co.jp/wp-content/uploads/2025/07/20240528_gourmet_01.pdf | ◎[業界] | PDF 全 9 頁(4〜5 頁の表はレイアウト抽出) |
| 13 | セルウェル「近所の飲食店利用実態調査」2017-10-27 | https://kyodonewsprwire.jp/release/201710277281 | ○[業界] | リリース本文 |
| 14 | 広田・高橋 2014, 東京都市大 情報メディアジャーナル 15 | https://www.comm.tcu.ac.jp/cisj/15/assets/15_03.pdf | ◎ | 全 5 頁(小川 2003 は本論文経由=△) |
| 15 | Herr, Kardes & Kim 1991, JCR 17(4):454–462 | https://econpapers.repec.org/RePEc:oup:jconrs:v:17:y:1991:i:4:p:454-62 | ○ | 抄録 |
| 16 | Bickart & Schindler 2001, JIM 15(3):31–40 | https://doi.org/10.1002/dir.1014 | △ | 検索要約 |
| 17 | Cheung & Thadani 2012, DSS 54(1):461–470 | https://doi.org/10.1016/j.dss.2012.06.008 | △ | 検索要約 |
| 18 | Nielsen「Global Trust in Advertising 2015」 | https://www.nielsen.com/insights/2015/global-trust-in-advertising-2015/ | ○[業界] | 公式ページ本文(調査方法は △) |
| 19 | Zhao, Yang, Narayan & Zhao 2013, Mktg Sci 32(1):153–169 | https://doi.org/10.1287/mksc.1120.0755 | ○ | 抄録(EconPapers) |
| 20 | Erdem & Keane 1996, Mktg Sci 15(1):1–20 | https://doi.org/10.1287/mksc.15.1.1 | ○ | 抄録(推定値の表は未取得) |
| 21 | Mehta, Rajiv & Srinivasan 2004, QME 2(2):107–140 | https://doi.org/10.1023/B:QMEC.0000027775.65062.50 | ○ | Springer 抄録 |
| 22 | East, Hammond & Wright 2007, IJRM 24(2):175–184 | https://doi.org/10.1016/j.ijresmar.2006.12.004 | △ | 検索要約の抄録 |
| 23 | East, Hammond & Lomax 2008, IJRM 25(3):215–224 | https://doi.org/10.1016/j.ijresmar.2008.04.001 | ○/△ | 抄録冒頭(EconPapers)○・所見は △ |
| 24 | Anderson 1998, J. Service Res. 1(1):5–17 | https://doi.org/10.1177/109467059800100102 | △ | 検索要約の抄録 |
| 25 | CMU ACT-R「Suggested Input to ACT-R Tutorial」 | http://act-r.psy.cmu.edu/wordpress/wp-content/uploads/2012/12/1006notesfortutorial.pdf | ◎ | スライド本文 |
| 26 | Anderson & Schooler 1991, Psych Sci 2(6):396–408 | https://doi.org/10.1111/j.1467-9280.1991.tb00174.x | ○ | 第三者掲載 PDF 全 14 頁 |
| 27 | Park ら 2023 Generative Agents, arXiv:2304.03442 | https://arxiv.org/abs/2304.03442 | ◎ | HTML v2 §3.4.1・§4.1・§4.2・§7.1 |
| 28 | Leone 1995, Mktg Sci 14(3):G141–G150 | https://doi.org/10.1287/mksc.14.3.G141 | ○ | 抄録(EconPapers) |
| 29 | Joseph 2006「Understanding Advertising Adstock Transformations」MPRA 7683 | https://mpra.ub.uni-muenchen.de/7683/ | △ | 本文(Leone・業界値の要約) |
| 30 | Zielske 1959, JM 23(3):239–243 | https://doi.org/10.1177/002224295902300301 | × | 書誌のみ(数値未取得) |
| 31 | Nedungadi 1990, JCR 17(3):263–276 | https://econpapers.repec.org/RePEc:oup:jconrs:v:17:y:1990:i:3:p:263-76 | ○ | 抄録 |
| 32 | Lynch & Srull 1982, JCR 9(1):18–37 | https://doi.org/10.1086/208893 | △ | 定義は #33・#34 経由 |
| 33 | Rottenstreich, Sood & Brenner 2007, JCR 33(4):461–469 | https://bear.warrington.ufl.edu/brenner/papers/rsb-generate-jcr07.pdf | ◎ | 著者版全文 |
| 34 | Kronlund, Whittlesea & Yoon(Handbook 章・in press) | http://spartan.ac.brocku.ca/~consumercognitio/Files/Kronlund%20Whittlesea%20&%20Yoon%20in%20press%20Handbook.pdf | ○ | 本文(二次の定義) |
| 35 | Lynch, Marmorstein & Weigold 1988, JCR 15(2):169–184 | https://doi.org/10.1086/209155 | △ | 検索要約 |
| 36 | Bougie & Watanabe 2025 CitySim, arXiv:2506.21805 | https://arxiv.org/abs/2506.21805 | ◎ | HTML §3.1.2・§3.1.3・§3.2.2・付録 |
| 37 | Lyfe Agents, arXiv:2310.02172 | https://arxiv.org/abs/2310.02172 | ◎ | HTML §2.3・§4・付録 A.3 |
| 38 | RecAgent(User Behavior Simulation with LLM based Agents), arXiv:2306.02552 | https://arxiv.org/abs/2306.02552 | ◎ | HTML(記憶・同調の節) |
| 39 | Agent4Rec(On Generative Agents in Recommendation), arXiv:2310.10108 | https://arxiv.org/abs/2310.10108 | ◎ | HTML §2.1.2 |
| 40 | AgentSociety v1 `cityagent/blocks/mobility_block.py` @8cc5bb9a9c27 | https://github.com/tsinghua-fib-lab/agentsociety | ◎ | raw を標準出力で読んだ(94–160 行) |
| 41 | Salganik, Dodds & Watts 2006, Science 311:854–856 | https://www.princeton.edu/~mjs3/salganik_dodds_watts06_full.pdf | ◎ | 著者掲載 PDF(本文+SOM 抜粋) |

## §1 Q1 WOM の伝播モデル

- **1-1 Bass/Sultan(#1・#2 △)**: Nam 2011 の本文「Meta-analysis across 150 diffusion cases shows that the rate of innovation (p) is 0.03 and the rate of imitation (q) is 0.38 (Sultan, Farley, and Lehman 1990)」。同じ論文の後段は「(p=0.03 and q=0.38) of the meta analysis across 213 published applications」と**件数が食い違う**(原典抄録の件数は検索要約で 213 [未確認])。Nam 自身は逐次発売で「commonly observed overestimation on contagion effects (WoM effects)」が起きると主張=**q は過大推定されやすい**。台帳 C4(Bass 拡散 p≈0.03/q≈0.38)は **holdout** なので、v2 の伝達確率をこれに合わせて調整してはならない(較正が holdout に触れる)。p・q の時間単位は元データの期間(多くは年次)[推測]。
- **1-2 Goldenberg, Libai & Muller 2001(#3 ○)**: 確率セルオートマトンで「strong ties」(自分の群の中)と「weak ties」(他群の知人)と広告を分ける。抄録の結論「The influence of weak ties is at least as strong as the influence of strong ties.」「External marketing efforts (e.g., advertising) are effective. However, beyond a relatively early stage of the growth cycle of the new product, their efficacy quickly diminishes」「When personal networks are small, weak ties were found to have a stronger impact on information dissemination than strong ties.」。3 確率の範囲(広告 [0.0005, 0.005]・強い [0.01, 0.07]・弱い [0.005, 0.01])は 2018 年の後続論文の記述として検索要約に出たが本文は 403 で**未確認(×)**。
- **1-3 追試(#4 ○)**: 「a near-exact replication, reported in this paper, found that weak-ties had less than one third of the influence of strong-ties」「leads us to be sceptical of the original findings」。**弱い紐帯の優位は頑健でない**。
- **1-4 影響者と複雑感染(既存)**: 大規模カスケードは影響者でなく「影響されやすい個体の臨界質量」(Watts & Dodds)・平均カスケード 1.14/1.3(Bakshy/Goel=台帳 C1・AD5)・クラスタ網で採用 54% vs 38%(Centola=C3)・WOM の 75% 超が対面(Berger & Schwartz)。既存答申の結論「**看板=単純感染・口コミ=複雑感染を同じチャネルにしてはならない**」は本件でも前提。
- **1-5 WOM と獲得の弾力性(#5 ◎)**: SNS の会員獲得で「The long-run elasticity of signups with respect to WOM is estimated to be 0.53」「about 20 times higher than the elasticity for marketing events, and 30 times that of media appearances」(0.53 vs 0.026 / 0.017)・持ち越し「continues to significantly impact the firm's new signups for 21 days」、イベントは「significant for only five days」。**対象はオンライン招待で、飲食店ではない**。
- **1-6 v2 のセル世界への写し方**(形の比較):

| モデル | 単位 | v2 での対応 | 写せるか |
|---|---|---|---|
| Bass(ABM 形) | 期ごとに 外部 p + 模倣 q×(接触者中の既知者の割合) | p=看板の注視(AD 腕 p_see)/q=同セルの会話で店の話を聞く | **形は可**。集計 p・q は holdout 照合専用 |
| Goldenberg CA | 強い紐帯・弱い紐帯・広告の 3 確率 | 強い=C10 の関係辺(知人)/弱い=同セルの非知人/広告=看板 | 形は可・3 確率は宣言(追試で比が不安定) |
| 閾値(Watts & Dodds・Centola) | 複数の出どころからの補強で採用 | 「別々の 2 人から聞いたら候補に入る」=確からしさの累積で表せる | 可(確からしさの閾値は宣言) |
| VAR(Trusov) | 集計の時系列 | 照合の形(WOM の持ち越し日数) | 照合用のみ |

## §2 Q2 口コミ・評価が店の選択/売上に与える効果

- **Luca 2016(#6 ◎・ワシントン州の売上データ)**: 「(1) a one-star increase in Yelp rating leads to a 5-9 percent increase in revenue, (2) this effect is driven by independent restaurants; ratings do not affect restaurants with chain affiliation」。ベイズ学習と整合:「market responses to changes in a restaurant’s rating are largest when a restaurant has many reviews」「affected by the number of reviews and whether the reviewers are certified as “elite” by Yelp, but is unaffected by the size of the reviewers’ Yelp friends network」。
- **Anderson & Magruder 2012(#7 △)**: 半星の丸め RD で「An extra half-star rating causes restaurants to sell out 19 percentage points (49%) more frequently, with larger impacts when alternate information is more scarce」(検索要約の抄録・PDF 未取得)。
- **Chevalier & Mayzlin 2006(#8 ◎)**: 「the impact of 1-star reviews is greater than the impact of 5-star reviews」(書籍)。
- **メタ分析(#9 ◎・#10 ○)**: 「electronic word-of-mouth volume (valence) elasticity is .236 (.417)」(51 研究・量 339・評価 271 の弾力性)。**フロア併記**: 表 3 の研究間 SD は量 .526(範囲 −1.443〜3.08)・評価 1.491(−5.86〜7.73)=平均の数倍。独立系レビューサイトほど大きい。Babić Rosario ら「On average, eWOM is positively correlated with sales (.091)」(1,532 効果量・96 研究)。
- **同調(#11 △)**: 最初の 1 票を無作為に操作すると「positive social influence increased the likelihood of positive ratings by 32% and created accumulating positive herding that increased final ratings by 25% on average」、負の操作は共同体が修正。
- **日本**: 食べログ評点の因果推定(RD 等)は**見つからなかった(空欄)**。広田・高橋 2014(#14 ◎)の擬似サイト実験は「クチコミの数と星の数が独立に影響するのではなく相乗的に影響すること，クチコミの数は10 件と50 件では差がみられないが100 件になると特に星が多い場合に指数的に影響を与える」=**件数(=確からしさ)と評価の積**の形。
- **日本の「通りがかり」(最優先の錨)**:

| 出典 | 設問・母集団 | 値 | 等級 |
|---|---|---|---|
| リクルート 2024(#12) | 首都圏・関西・東海の 20〜69 歳・マクロミル・2024-04-01〜11・有効 9,606。「一番最近で夕方以降に初めて利用した飲食店」の「お店への期待の持ち方に最も影響の大きかった情報源」(n=6,487) | グルメサイト・口コミサイト **26.4** / 店構えや店先のメニューなど **22.2** / 家族・友人・知人等からの口コミ **14.7** / SNS **11.1** / 以下 8.0・5.7・3.5・2.2・2.1・0.9・0.6・その他 2.6(合計 100.0 [サブ計算]=実質単一回答) | ◎[業界]。**5 位以下のラベル帰属は縦書き抽出で不確実**。SNS=4 位は本文の性年代値(20 代女性 28.1 等)と列が一致 |
| 同上 | 性年代 | 店構え: 50 代女性 27.8・60 代女性 29.0 / SNS: 20 代男性 26.2・20 代女性 28.1 | ◎[業界] |
| 同上 | お店を選んだ経緯(n=7,956) | 主に自分 3,928・自分も関わった 2,043・**主に他の人 1,986(25.0% [サブ計算])** | ◎[業界] |
| リクルート 2018(既存 lit) | 首都圏 20〜64 歳・1 週間の外食回数 | 初回 **22.5%**(親確認済)/目的型来店 43.2%([サブ値]・親未確認) | ◎[業界] |
| セルウェル 2017(#13) | 全国 20 代〜50 代以上 1,000 人・ネット・2017-10-02〜04 | 近所の飲食店の情報源「お店の前を通りがかったとき」74.0%/常連店を知ったきっかけ「店の前を通りがかったとき」49.8%・「家族・友人の紹介」79.8%・「ダイレクトメール」65.7% | ○[業界]。**合計が 100% を大きく超え尺度の定義が本文に無い**=比較には使わない |

→ 満足化(見えている店)と記憶候補の比の目安: 初回訪問の約 2 割が店頭情報で決まり、初回は外食の約 2 割 → **店頭で決めた初回 ≈ 0.225×0.222 ≈ 5%**(時間帯・母集団の違う 2 調査の掛け算=[推測]・holdout ではなく較正帯の候補)。残り約 8 割はリピート(記憶)で、この区別は草案 §2-2 の「習慣 p_h」と「満足化」の比に対応する。

## §3 Q3 出どころ別の信頼・重み

- **対面 > 印刷・既存の印象で消える(#15 ○)**: 「A face-to-face WOM communication was more persuasive than a printed format (experiment 1). Although a strong WOM effect was found, this effect was reduced or eliminated when a prior impression of the target brand was available from memory or when extremely negative attribute information was presented」=**自分の経験 > 対面の口コミ > 文字情報**の順序。vividness・負の情報の効果を accessibility-diagnosticity で説明。
- **利用者の掲示板 > 企業サイト(#16 △)**: 12 週後、掲示板で調べた群のほうが製品への関心が高い。**統合モデル(#17 △)**: 刺激・発信者・受信者・反応の 4 要素、source credibility は発信者側の因子。
- **信頼の割合(#18 ○[業界])**: 世界 60 か国のネット利用者で「83% ... trust the recommendations of friends and family」「66% say they trust consumer opinions posted online—the third-most-trusted format」・ブランドサイト 70%。**日本の値は未取得**。「信頼」と「実際に効いた情報源」は別物(日本では §2 のとおりグルメサイト 26.4 > 知人 14.7)。
- **確からしさ=精度として推定した先行**:
  - Zhao ら 2013(#19 ○):「We model the review credibility as the precision with which product reviews reflect the consumer’s own product evaluation.」「1,919 book purchases by 243 consumers」「consumers learn more from online reviews of book titles than from their own experience with other books of the same genre」「fake reviews increase consumer uncertainty」。**注意**: 比べているのは「その本のレビュー」と「同ジャンルの別の本の経験」で、同じ店の自分の経験ではない。
  - Erdem & Keane 1996(#20 ○):「both usage experience and advertising exposure give consumers noisy signals about brand attributes. Consumers use these signals to update their expectations of brand attributes in a Bayesian manner.」、ベイズ形は「fit the data very well relative to flexible ad hoc functional forms such as exponential smoothing」(洗剤)。**経験と広告の信号分散の推定値は未取得(×)**。
  - Luca(§2)の件数・elite 依存も同じ形。CitySim は観測の雑音 σ_o を 1 つだけ置く(§6)。
- **向き(正/負)の非対称**: 正:負の口コミの発生は平均 3:1、正の口コミは主に自分の主銘柄についてで市場シェアに比例して分布(East ら 2007 △)/正の口コミの効果は概して負より大きく、口コミ前の購買確率(多くは 0.5 未満)に強く依存(East ら 2008 △)/満足と口コミは非対称の U 字・不満の側が多いが「common suppositions concerning the size of this difference appear to be exaggerated」(Anderson 1998 △)/1 星の効果 > 5 星(§2)。
- **伝聞の再伝播**: @コスメ利用者で「82.7％が…誰かに伝えた経験」、うち「自分で試したことのない化粧品についてのみ伝えたことがある」は「2.1％」(小川 2003・#14 経由 △)=**人は主に自分の経験を話す**。GA でも伝聞の確かさは下がる:「certain of what he’s supposed to do at the party but uncertain if the party actually exists in the first place」(#27 ◎)。
- **錨の有無**: 順序(自分 > 対面の伝聞 > 文字・看板)と「精度で重みづける」形は錨あり。**出どころ間の比(例: 伝聞は自分の何分の 1 か)の数値は、飲食店でも一般でも見つからなかった**=宣言+感度腕。

## §4 Q4 記憶の減衰

| 出典 | 形 | 定数 | 半減などの換算 [サブ計算] | 等級 |
|---|---|---|---|---|
| GA §4.1(#27) | 最後に**想起**してからのゲーム内時間の指数減衰:「Our decay factor is 0.995」。recency・importance・relevance を min-max で [0,1] にし、α はすべて 1 | 0.995/時 | 半減 138 時間 ≈ **5.8 日** | ◎(値の根拠の記述なし) |
| ACT-R(#25・#26) | 基底活性 ln(Σ t_j^−d):「:bll – the exponent in the formula – normal value: a half, i.e., 0.5」。環境の必要確率もべき(指数形は「not sup- ported」・Ebbinghaus で「The exponent .126 can be taken as the forgetting rate」) | d=0.5 | べき=半減は一定でない(1 回提示で 1 時間→1 日に t^−0.5 は 1→0.20) | ◎/○。**v2 のエピソード記憶は d=0.5 で既決**([記憶アジェンダ M2](../design/v2-memory-agenda.md)) |
| CitySim(#36) | 1 日ごとに中立 0.5 へ回帰「b_i,d ← (1−λ) b_i,d + λ b_0,d」・訪問で Kalman | λ=0.03/日・σ_b(0)=0.25・σ_o=0.2 | 中立への距離の半減 **22.8 日** | ◎(較正の記述なし) |
| RecAgent(#38) | 忘却確率 g(M)=1−(s+r)/2·max(r^β, δ)(s,r=正規化した recency・importance) | β>1・δ(値は本文になし) | — | ◎ |
| Lyfe(#37) | 時間でなく**重複で忘れる**:「existing memories with similarity scores above this threshold against incoming memories are deemed redundant and are removed」 | 閾値 θ | — | ◎ |
| Mehta ら 2004(#21) | 「consumers recall their prior evaluations with noise」・忘却は「an increasing and concave function of time」(洗剤のスキャナデータで推定) | 推定値は未取得 | — | ○ |
| Trusov 2009(#5) | WOM の効果の持ち越し | 21 日 vs イベント 5 日 | — | ◎ |
| Leone 1995(#28) | 広告の持ち越し:「the average advertising duration interval is of brief duration—typically between six and nine months」 | 6〜9 か月 | — | ○ |
| Joseph 2006(#29) | Adstock の半減:「half-life range around 7- 12 weeks (Leone 1995), while industry practitioners typically report half- lives between 2-5 weeks, with the average for Fast Moving Consumer Goods (FMCG) Brands at 2.5 weeks」 | 2〜12 週 | — | △(Broadbent 1979 原典は未読) |
| Zielske 1959(#30) | 同じ 13 回を毎週 vs 4 週ごとに郵送した想起の比較 | 数値未取得 | — | × |

→ **形は 3 系統**(指数=GA・中立への回帰=CitySim・べき=ACT-R)に加え「確からしさ(雑音)が増える」(Mehta)。**値は 5.8 日〜数か月と 2 桁以上散り、どれも店の評価の記憶を較正したものではない**=宣言+感度腕(例: 半減 6 日/23 日/べき d=0.5 の 3 点)。

## §5 Q5 記憶に基づく考慮集合と「見える店+記憶の店」の合成

- **分類(#32 △・#33 ◎・#34 ○)**: Rottenstreich ら「Lynch and Srull classified the former type of decisions as “stimulus based” and the latter type as “memory based.”」(店頭で選ぶ vs 家で買い物リストを作る)。Kronlund ら「stimulus-based (all relevant information is physically present at the time of judgment or choice) and mixed (a combination of memory-based and stimulus- based) decisions (Lynch & Srull, 1982). However, purely stimulus-based decisions are relatively rare」。**v2 の「見える店+記憶の店」は mixed choice そのもの**。Rottenstreich らの実験 1 はフルーツサラダの占有率 47%(stimulus)vs 45%(memory)で差が小さい。
- **想起が評価と独立に選択を動かす(#31 ○)**: 「For a brand to be selected in memory-based choice, the consumer must recall that brand and fail to recall other brands that might otherwise be preferred.」「Results provide evidence for the influence of memory during the brand-choice process.」。Lynch ら 1988(#35 △)は「思い出せる(accessible)かつ診断的(diagnostic)な入力を使う」。
- **既存答申の錨**: 考慮集合は 2〜5 件(Honka ら総説・R-37/R-47)/歩行者の店選びで「The attraction of outlets depends on … whether the outlets can be seen, have been passed or visited before」(Borgers & Timmermans 2015・R-47 §2-5 [サブ値・親未確認])=**見える・通った・入った を 1 本の式に入れた直接の先行**(ただし通りの選択には距離項あり)。
- **探索 vs 回帰の比の錨(既存・親確認)**: EPR「Pnew = ρS^-γ」「γ = 0.21±0.02」(ρ≈0.6 はサブ値)。訪問済みの場所数 S で P_new = 0.43(S=5)・0.37(10)・0.32(20)・0.26(50)・0.23(100)[サブ計算]。ホットペッパー 2018 の初回 22.5% と桁が合う(**ただし EPR の「場所」は携帯の基地局セルで飲食店ではない**)。
- **合成の型(先行から取れる 3 つ)**:

| 型 | 中身 | 先行 | v2 での含意 |
|---|---|---|---|
| (a) 二段 | まず「戻る/探す」を抽選(P_new)→ 戻るなら記憶の店から、探すなら見える順の満足化 | EPR・Pappalardo の returner/explorer | 草案 §2-2 の p_h を P_new の形に置き換えられる。記憶の店の中の選び方は評価×確からしさ |
| (b) 和集合に同じ得点 | 見える店 ∪ 記憶の店 に「見える」「通った」「入った」「評価」を説明変数として 1 つの式 | Borgers & Timmermans 2015・CitySim(未訪問は類似店から補完) | 係数が増える=指紋が大きい。ロジットにすると「ハフ型は入れない」との関係を要確認 |
| (c) 想起優先 | 思い出せた店のうち願望水準を超えるものがあれば行く、無ければ見える順の満足化 | Nedungadi・Simon(R-47)・Lynch ら 1988 | 定数は願望水準と想起の閾値だけ。記憶の店が遠いときの扱いが別に要る |

## §6 Q6 LLM 社会シミュレーションの店/場所の記憶

| 系 | 記憶の形 | 場所×評価の構造化 | 出どころの区別 | 減衰 | 口コミで場所の評価が変わるか |
|---|---|---|---|---|---|
| Generative Agents(#27) | 自由文の記憶ストリーム+importance(LLM が 1〜10) | 無い | 無い | 0.995/時(§4) | 会話で知識が伝わる(立候補の件 4%→32%・パーティ 4%→52%・「None who claimed to know about this information had hallucinated it」)。ただし脚色:「they still exhibited instances of hallucination where they embellished their knowledge」 |
| Lyfe Agents(#37) | 自由文+要約と重複による忘却 | 無い | 無い | 重複で削除 | 部活選びが友人の会話で動く(56% vs 22%)・「information has a reasonable chance of being spread (or lost) at every step」 |
| RecAgent(#38) | 感覚・短期・長期の自由文 | 無い(映画) | 無い | べきの忘却確率 | 1 対 1 の会話と 1 対多の発信で記憶が変わる。同調:「in the beginning, the scores are more evenly distributed in the range from 3 to 8, but finally concentrate to 6 and 7」 |
| Agent4Rec(#39) | 「factual memory mainly contains the list of recommended items, along with user feedback」+感情の記憶 | 品目×自分の評価(推薦系) | 自分のみ | — | 無い(他者との会話なし) |
| **CitySim(#36)** | 空間記憶の信念 b_i ∈ R^4(price・atmosphere・satisfaction・convenience)+不確かさ σ_b | **有る** | **自分の訪問のみ**(LLM が訪問ごとに多次元の観測 o_i を書く) | 中立へ λ=0.03/日 | **無い**: 会話の後に更新されるのは相手への「affinity, trust, and familiarity scores」。未訪問の店は「imputed from the k = 10 most similar visited locations」 |
| AgentSociety v1(#40) | ストリーム記憶(R-44) | **無い** | — | — | 店は `weight = density / (distance**2)` の重力で抽選(候補 50 を 1/√距離で標本)。記憶は半径の LLM プロンプトに入るだけ |

- **結論**: 構造化した場所×評価の記憶は CitySim だけで、しかも自分の訪問でしか更新しない。**出どころ(自分/伝聞/看板/ネット)を持つ場所の記憶、会話から店の評価を抽出して他者の記憶に書く先行は、読んだ範囲では無い**。
- **失敗様式(抽出の前提)**: 脚色(GA)・同調収束(RecAgent)・「positive bias toward well-known or branded POIs」と「LLM popularity bias」(CitySim・既存 lit と本文)。→ LLM が書いた店名が世界に無い/別の店に化ける危険は、**閉じた POI 集合への照合**と「照合できなかった割合」の計測で抑えるしかない [推測]。

## §7 Q7 計測(口コミの伝播と店の集中を AD 腕と並べる)

- **Salganik ら 2006(#41 ◎)**: 「14,341 participants」を独立条件と社会的影響条件に無作為に割り付け、影響条件は互いに見えない 8 つの世界。不平等は Gini(市場占有率 m_i の対差の平均を 0〜1 に正規化)、不予測性 U は同じ曲の占有率の世界間の差の平均。独立の世界は 1 つなので「we randomly split the single world into two subpopulations … averaged the results over 1000 of these splits」。結果「all eight social influence worlds (dark bars) exhibit greater inequality」「Increasing the strength of social influence increased both inequality and unpredictability of success.」。**Gini と U の数値は図のみ=空欄**。
- **v2 に写す計測セット**(候補):

| 指標 | 式/定義 | 出典 | 並べ方 |
|---|---|---|---|
| 店の集中 | 訪問の Gini・上位 k 店の占有率・HHI(Σ m_i²)を業態別に | Salganik(Gini) | 2×2 腕: 口コミ off/on × 看板 off/on(AB6 系)× seed |
| 不予測性 | 同じ店の占有率の seed 間の差の平均(U) | Salganik | seed=「世界」。独立条件は seed 内の分割で基準をとる |
| 伝播の広がり | 店 X を知っている体の割合の時系列/伝聞の木の大きさ・深さ | GA §7.1・台帳 C1/AD5 | C1(平均 1.3・99% 1 世代)は **holdout=照合のみ** |
| 決め手の内訳 | 訪問ごとに「見えていた/自分の記憶/伝聞/看板」を記録し割合を出す | SOFAI 形式(R-47 §4)・リクルート 2024 | 初回訪問の「店頭 22.2%」と並べる(較正帯候補) |
| 正負の口コミ比 | 抽出した評価の正:負 | East ら 2007(3:1 △) | 同上 |
| 口コミの偏り | 店ごとの言及数の占有率 vs 訪問の占有率 | East ら 2007(正の口コミは市場シェアに比例 △) | 相関と傾き |
| 抽出の失敗率 | 照合できなかった店名/全抽出 | GA・CitySim の失敗様式 | LLM 腕のみ |
| 再訪率 | 訪問に占める初回の割合 | ホットペッパー 2018(22.5%・親確認) | 較正帯(既存 lit は holdout 不可と判定) |
| 訪問則 | ρ_i(r,f) ∝ (rf)^−η | Schläpfer 2021(既存 lit) | 口コミで η が崩れないか |

- **規律上の注意**: 台帳 C1・C3・C4 は holdout。**口コミの伝達確率・重み・減衰をこれらに当てて調整すると較正が holdout に触れる**。調整に使えるのは較正帯と宣言した行(ホットペッパー等)だけ。

## §8 v2 への写し方(候補と区分・推奨ではない)

区分: **エンジン**=エンジンで実行可能 / **GM**=GM 裁定行き / **なし**=実行手段なし。

| # | 候補 | 区分 | 定数 | 錨 or 宣言 | 根拠 |
|---|---|---|---|---|---|
| W1 | 店の記憶の行: POI ID・評価の向き(3 段)・出どころ(自分/伝聞/看板/ネット)・確からしさ・記憶した時刻・回数 | エンジン | 行数上限 N・1 行のバイト | **宣言**(バイト予算を先に宣言) | CitySim(4 次元+σ)・Agent4Rec |
| W2 | 自分の訪問で書く(評価の向き=結果コード or LLM の 3 値ラベル) | エンジン | 結果コード→向きの対応表 | 宣言 | CitySim(LLM が観測)・記憶アジェンダ M12(ResultCode 由来) |
| W3 | 会話から「店名と評価」を抽出して聞き手の記憶に書く | System 2 の出力 → エンジンで閉じた POI 集合に照合・不一致は捨てて数える | 照合の規則 | 宣言 | 先行なし(§6)・脚色/偏りの失敗様式 |
| W4 | 看板から書く(評価は持たず「知っている」だけ) | エンジン(B2 の看板行=AD 腕) | — | — | 広告答申(看板=単純感染) |
| W5 | ネットの評価 | **なし**(v2 にオンライン評価の場が無い)。実在の評点を外から入れるのは現実データ・holdout 汚染の恐れ=**先に聞く** | — | — | §2(効果の実証はほぼすべてオンライン評価) |
| W6 | 確からしさの更新=出どころ別の雑音 σ_src でベイズ/Kalman | エンジン | σ_自分 < σ_伝聞 < σ_看板 | **順序は錨**(Herr・Nielsen・Zhao)・**比は宣言+感度腕** | Erdem & Keane・Zhao・Luca・CitySim |
| W7 | 忘却 | エンジン | (a) A(m) の d=0.5 に揃える(既決と整合)/(b) 中立への回帰 λ/(c) 雑音の増加 | 宣言+感度腕(半減 6 日/23 日/べき) | §4 |
| W8 | 候補集合の合成(§5 の型 a/b/c) | エンジン(System 1.5) | P_new または p_h・願望水準 | 帯は錨(初回 22.5%・EPR γ)・形は宣言 | §5 |
| W9 | 記憶の店が遠いときの扱い(距離項なしの決定の下で) | エンジン | 予定・移動可能圏で候補から外す(到達可能性の制約) | **親判断**(R-37 は「到達可能性による候補集合の制約」を許容と整理) | R-37・草案 §2-2 |
| W10 | 伝聞の再伝播(聞いた話をさらに話すか) | System 2 に任せる(エンジンは強制しない)・観測だけ | — | 目安のみ(小川 2003 の 2.1% △) | §3 |
| W11 | 集まりの店選び(主に他の人が選ぶ 25%) | GM(誰が決めるかの裁定)or 同行者の記憶を使う | — | 宣言 | リクルート 2024 |
| W12 | 計測と腕(§7 の表)・口コミ off 腕=独立条件 | エンジン(manifest) | seed 数 | — | Salganik |

## §9 未確認一覧

1. Sultan ら 1990 の原典(p=0.03・q=0.38・件数 150 か 213 か)=Nam 2011 経由のみ(△)。
2. Goldenberg ら 2001 の 3 確率の範囲・7^5=16,807 通りの設計(本文未取得・後続論文は 403=×)。
3. Anderson & Magruder 2012 の 19 pp・49%(抄録を検索要約経由=△・PDF 取得失敗)。
4. Muchnik ら 2013 の 32%・25%(△)。
5. East ら 2007 の 3:1・East ら 2008 の所見・Anderson 1998 の U 字(いずれも検索要約=△)。
6. Bickart & Schindler 2001・Cheung & Thadani 2012・Lynch ら 1988・Lynch & Srull 1982 の原文(△)。
7. Erdem & Keane 1996 の経験/広告の信号分散・Mehta ら 2004 の忘却の推定値・Zhao ら 2013 の精度の推定値(抄録のみ=×)。
8. Zielske 1959 の想起率・Broadbent 1979 の半減(×)。
9. Nielsen 2015 の日本の値・調査方法の原文(△/×)。
10. リクルート 2024 の情報源 5 位以下のラベル帰属(縦書き抽出)。
11. 食べログ・ぐるなび等の日本の評点の因果効果(見つからず=空欄)。
12. **対面口コミの伝播率**(聞いた人のうち何%が次に話すか)の一次(既存答申と同じく空欄)。
13. **出どころ別の重みの比**・**店の評価の記憶の減衰**の一次(見つからず=空欄)。
14. Salganik ら 2006 の Gini・U の数値(図のみ)。
15. Lyfe の忘却閾値 θ・RecAgent の β・δ の値。

## §10 親への確認依頼

1. **holdout の線**: C4(Bass)・C1・C3 に口コミの定数を当てない運用でよいか。較正に使えるのはホットペッパー等の較正帯だけ、で整合するか。
2. **W9 は「ハフ型は入れない」に触れるか**: 記憶の店を到達可能性で切るのは距離減衰ではないが、境界の判定を。
3. **W5(ネット評価)は現実データへの接触**: 入れるならユーザー判断(先に聞く)。
4. **リクルート 2024 の表の帰属**: 5 位以下を使う場合は PDF 5 頁を目視で。
5. **2 調査の掛け算(≈5%)** は推測。設計書に写すなら「推測」の注記を保つ。
