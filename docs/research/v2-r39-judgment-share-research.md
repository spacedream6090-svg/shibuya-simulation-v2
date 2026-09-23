# R-39 答申: 人の思考のうち「判断(意思決定)」が占める割合 / システム 1・2 の比率と発火条件

<!-- hdr:v1 -->
- **分野**: 認知科学(記憶・習慣) #12 / 自然言語処理・機械学習 #27 / ABM方法論 #21 | **重要度**: P0(親判断・2026-09-15 第191)
- **一次確認**: **B** = 出典あり・空欄を明示(残務台帳へ写し済みまたは要写し) — サブ実読(PDF 6 本・2026-09-18・第242)+親確認 4 件(Hofmann/De Neys/Kahneman & Klein の抄録一致・Milli 2017 PDF 逐語一致)。Frederick 2005 Table 1・Evans & Stanovich Table 1・Klinger 2013 逐語は親未確認
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **分野地図**: [v2-discipline-map.md](v2-discipline-map.md)

> **親検収(第242・2026-09-18)**: ファイル実在・台帳不編集・子サブ不使用を確認。親の一次確認: Hofmann 2012 抄録(Europe PMC: N=205・7,827 報告)一致・De Neys & Glumicic 2008 抄録(base rate をほとんど言及せず・潜時/再生で検知)一致・Kahneman & Klein 2009 抄録(環境の予測可能性+学習機会・主観的経験は指標にならない)一致・Milli, Lieder & Griffiths 2017 は CoCoSci PDF で逐語一致(「optimal number of systems depends on the variability of the environment and the costliness of metareasoning」)。**親未確認**: Frederick 2005 Table 1(出版 PDF に到達できず・親の記憶とは一致)・Evans & Stanovich 2013 Table 1・Klinger 2013 の逐語・Hofmann 本文の 49.9/47/42/48/69.6(抄録外)。派生値 21%(0.499×0.42)は答申の明記どおり派生。訂正 2 件(「Hybrid Constitutional Architectures」は不在・Klinger & Cox の比率は未取得)は妥当。lit 行 18 は答申内に留置(lit note 未作成・R-23b3 と同じ扱い)。

> **親検収(第242・2026-09-18)**: ファイル実在・台帳不編集・子サブ不使用を確認。親の一次確認: Hofmann 2012 抄録(Europe PMC: N=205・7,827 報告)一致・De Neys & Glumicic 2008 抄録(base rate をほとんど言及せず・潜時/再生で検知)一致・Kahneman & Klein 2009 抄録(環境の予測可能性+学習機会・主観的経験は指標にならない)一致・Milli, Lieder & Griffiths 2017 は CoCoSci PDF で逐語一致(「optimal number of systems depends on the variability of the environment and the costliness of metareasoning」)。**親未確認**: Frederick 2005 Table 1(出版 PDF に到達できず・親の記憶とは一致)・Evans & Stanovich 2013 Table 1・Klinger 2013 の逐語・Hofmann 本文の 49.9/47/42/48/69.6(抄録外)。派生値 21%(0.499×0.42)は答申の明記どおり派生。訂正 2 件(「Hybrid Constitutional Architectures」は不在・Klinger & Cox の比率は未取得)は妥当。lit 行 18 は答申内に留置(lit note 未作成・R-23b3 と同じ扱い)。

> 依頼(第241・ユーザー): 「人の思考の中で**判断(意思決定)**が占める割合をリサーチしてほしい。思考にはシステム 1/2 があるはず。判断=速い層(型付きの小モデル)・思考=遅い層(LLM)に分け、LLM を呼ぶかどうかの判断まで速い層に任せる構成を考えている。」
> 担当: リサーチサブ(Opus 5)・子サブ不使用・Web は読むだけ・ファイル保存なし(PDF はメモリ上で読解)。
> **設計は書かない**(親とユーザーが決める)。含意は事実の含意に限る。
> 関連既存: docs/research/v2-thought-frequency-anchors-note.md(第240・思考頻度の錨)・docs/research/v2-jev-system-one-note.md(第238・型付き判断)。本答申は重複を避け、**割合**と**発火条件**に絞る。

確認の別: **原典**=原論文の本文を自分で読んだ / **抄録**=出版社の抄録のみ / **二次**=著者の後年レビュー・citing paper・検索要約経由 / **未読**=本文に到達できず。

---

## 1. 要約(10 行以内)

1. **「思考のうち判断が何%」を直接測った研究は見つからなかった**。経験サンプリングは「欲求」「心のさまよい」「内言」は測るが、「決めた瞬間」は測っていない。**「1 日 35,000 回」は一次資料なし**(採用しない)。Wansink & Sobal 2007 の 226.7 も採用しない。
2. 最も近い一次値は Hofmann ら 2012(JPSP・N=205・7 日×7 回・応答 10,558): **欲求あり 49.9%**・欲求のうち **47% が他の目標と葛藤**(「まったく葛藤なし」53.2%)・**42% が抵抗され**・**48% が実行**。抵抗しなかった場合の実行率 **69.6%**。
3. そこから親の算術: **応答した瞬間の約 21%(0.499×0.42)が「意識的に抑える/選ぶ」瞬間**、約 23%(0.499×0.468)が葛藤を含む瞬間。これは「判断の割合」の**下界の代理**であって「判断の割合」そのものではない。
4. 思考の質(Heavey & Hurlburt 2008・DES・30 名×10 瞬間): 内言 26%・内的視覚 34%・**無象徴思考 22%**・感情 26%・感覚 22%。Klinger 系(Klinger 2013 の自己引用): 課題非依存の思考は覚醒思考の **約 1/3〜1/2**・夢様の痕跡 25%・分節の中央値 **5 秒**。
5. Type 1/2 の**定義**(Evans & Stanovich 2013 Table 1)は速さではない: Type 1=**作業記憶を必要としない・自律的**、Type 2=**作業記憶を必要とする・認知的デカップリング/心的シミュレーション**。「速い/遅い」は**定義ではなく相関**。既定は default-interventionist(Type 1 が既定解を出し、Type 2 が介入する**かもしれない**)。
6. Type 2 が介入する頻度の実証は「課題ごとの誤答率」でしか測られていない: De Neys & Glumicic 2008 は不一致問題の正答 **20% 未満**・base rate 言及 **18%**、Frederick 2005 CRT は **3,428 名で平均 1.24/3・33% が全問不正解・17% が全問正解**。つまり**介入は既定では起きない**。
7. ただし**葛藤の検知(監視)は安価で常時走っている**: De Neys & Glumicic は言語報告に葛藤が出ないのに、潜時・base rate の再読・不意打ち再生で検知の証拠を得て「**発見的思考は常に分析的監視を伴う**」と結論(**監視 ≠ 介入**)。
8. 速い判断が熟考に劣らない条件は 2 つだけ(Kahneman & Klein 2009): **(a) 環境が十分に規則的で妥当な手がかりがある (b) その規則を学ぶ機会(長期の練習+速く曖昧でないフィードバック)**。両方揃わない領域では速い判断は系統的誤りになる。
9. 計算モデルの先行: **速い系と遅い系を持つこと自体が最適になる条件**が形式的に出されている(Milli, Lieder & Griffiths 2017/2021: 系の最適個数は**環境のばらつき**と**メタ推論のコスト**で決まり、2 系が最適なときは第 1 系が速く誤りやすく第 2 系が遅く正確)。人の脳では**信頼度(reliability)による調停**が測られている(Lee, Shimojo & O'Doherty 2014)。CLARION は「**認知モードの選択**(明示/暗黙/その混合)」をメタ認知サブシステムの職務として明文化している。
10. LLM 側の「小さい門番が大きいモデルを呼ぶ」は確立: FrugalGPT(小型 DistilBERT のスコアが閾値 0.96/0.37 を超えなければ次を呼ぶ・**最大 98% のコスト削減**)、RouteLLM(**2 倍超**)。ただし**社会シミュレーションでの動的な毎決定ルーティングの先行例は見つからなかった**(社会シミュ側は「一部の体だけ LLM・残りは ABM」という**静的な階層**が主流)。

---

## 2. 問い 1: 「判断(決める)」が思考に占める割合

### 2-1. 直接測った研究(結論: **無い**)

| 研究 | 方法・N | 数値(逐語) | 出典 URL | 確認 |
|---|---|---|---|---|
| — | — | **該当なし**。覚醒中の思考サンプリングで「この瞬間は決めている/選んでいる」を符号化した研究は、今回の探索(ESM/EMA/DES/thought sampling × decision/choice)では見つからなかった | — | — |
| 「1 日 35,000 回の決定」 | — | **一次資料なし**。出所は大学ブログの「various internet sources estimate that an adult makes about 35,000 remotely conscious decisions each day」であり、研究ではない | https://go.roberts.edu/leadingedge/the-great-choices-of-strategic-leaders | 二次(検索要約・**採用しない**) |
| Wansink & Sobal 2007(食の決定 226.7 回/日) | 質問紙 N=139 の構成値 | Claassen, Mata & Hertwig 2025(*Appetite* 209:107928)が分解質問の加法性バイアスの人工物と批判 | https://doi.org/10.1016/j.appet.2025.107928 | 二次(第240 で既に「使わない」判定) |

### 2-2. 最も近い一次値: 欲求・葛藤・抵抗の経験サンプリング

Hofmann, Baumeister, Förster & Vohs (2012) *Journal of Personality and Social Psychology* 102(6):1318–1335, doi:10.1037/a0026545。**PDF 本文を読んだ**(大学ホストの全文)。

| 量 | 数値(逐語) | 確認 |
|---|---|---|
| 標本・設計 | 「A sample of 205 adults wore beepers for a week. They furnished 7,827 reports of desire episodes」/「Each day, seven signals were distributed throughout a time window of 14 hr」/ 応答率「completed 92.2% of signals」 | **原典** |
| いま欲求がある割合 | 「Participants indicated at least one current desire on half (49.9%) of the occasions at which they were beeped and responded (N = 10,558), reported at least one recent desire on 26.7% of occasions, and reported neither a current nor recent desire on 27.6% of occasions.」 | **原典** |
| 葛藤 | 「Average level of conflict was M = 1.08 (on a 0–4 scale), with 53.2% of desires rated as not conflicting at all, 14.7% as mildly conflicting, 12.4% as somewhat conflicting, 10.9% as quite conflicting, and 8.8% as highly conflicting.」/ 考察では「Almost half of those desires (47%) were described as conflicting at least somewhat with the person's other goals, values, or motivations.」 | **原典** |
| 抵抗・実行 | 「On average, desires were actively resisted on 42% of occasions and enacted on 48% of occasions.」 | **原典** |
| 抵抗しなかった時の実行率 | 「when participants did not attempt to resist, the desire-related behavior was enacted 69.6% of the time on average」 | **原典** |
| 欲求の強さ | 「Average desire strength (measured from 0 to 7) was moderate (M = 4.08), with 6.3% of desires receiving the highest possible rating of 'irresistible.' The median experienced desire duration was 16–20 min.」 | **原典** |
| 欲求の内訳 | 食 28.1%・睡眠 10.3%・飲み物 8.6%・メディア 8.1%・余暇 7.2%・社交 7.1%・衛生 5.9%・喫煙 4.8%・性 4.6%・仕事 3.0%・コーヒー 2.9%・酒 2.7%・運動 2.6%・買い物 2.2%・その他 1.9% | **原典** |
| 個人差 | 「frequency of desire was remarkably consistent across persons: None of our personality or situational variables predicted higher or lower total frequency of desire.」 | **原典** |
| 状況の効果 | 「resistance was less likely when enactment models were present (M = 0.28) compared to absent (M = 0.38)」/ 他者が居ると実行は下がる(抵抗時 0.18 vs 0.26・非抵抗時 0.73 vs 0.82)/ 葛藤は職場で高く(M=1.58)他人の家で低い(M=0.87) | **原典** |
| 同一データの領域別論文 | Hofmann, Vohs & Baumeister (2012) *Psychological Science* 23(6):582–588, doi:10.1177/0956797612437426 | **未読**(出版社 403・大学ホスト PDF は JS 壁。領域別の抵抗率・成功率の表は取得できず) |

**親の算術(原典には無い派生値・要注意)**: 応答した瞬間のうち
- 「いま欲求があり、かつ抵抗している」= 0.499 × 0.42 ≈ **21%**
- 「いま欲求があり、かつ少しでも葛藤している」= 0.499 × 0.468 ≈ **23%**
- 「いま欲求があり、実際に行動に移した」= 0.499 × 0.48 ≈ **24%**

### 2-3. 思考の様態の割合(「判断」ではないが上限の目安になる)

| 研究 | 方法・N | 数値(逐語) | 出典 URL | 確認 |
|---|---|---|---|---|
| Heavey & Hurlburt 2008, *Consciousness and Cognition* 17(3):798–810 | DES・30 名×10 瞬間(層化標本) | 内言 26%・内的視覚 34%・**無象徴思考(unsymbolized thinking)22%**・感情 26%・感覚 22%。「five phenomena occurring quite frequently (22% or more) and the other 11 phenomena occurring quite infrequently (3% or less)」。個人差は内言 0〜75%・無象徴思考 0〜80% | https://doi.org/10.1016/j.concog.2007.12.006 / 著者ホスト PDF | **原典**(第240 で親が読了・本答申は再掲) |
| Klinger 2013, *Front. Psychol.* 4:415(自著レビュー) | 自身の thought sampling 群のまとめ | 課題非依存の思考は「constitutes between about a third and a half of waking thoughts」(Klinger & Cox 1987–1988・Andrews-Hanna 2010a・Killingsworth & Gilbert 2010 を引用)/「25% of waking thought samples were rated by participants as having at least a trace of dream-like qualities」(Klinger & Cox 1987–1988)/ 分節長「median estimates of segment duration were 5 s in both settings」、平均 9 s(実験室)・14 s(日常)(Klinger 1978)/ 16 時間で約 4,000 分節(Klinger 1990) | https://doi.org/10.3389/fpsyg.2013.00415 | **原典**(PMC 本文・数値は Klinger 自身の引用=原章そのものは未読) |
| Klinger & Cox 1987–1988, *Imagination, Cognition and Personality* 7(2):105–128/129 | ビーパー・N=29・1,425 機会・Thought-Sampling Questionnaire | 8 直交因子のひとつが **Operantness (directedness)**。抄録の「約 1/3 が主に無方向・別の 1/3 が刺激非依存・約 1/4 が夢様」は**検索要約経由**で、**本文・抄録ともに到達できず**(SAGE 403・Semantic Scholar は abstract elided・Bangor リポジトリは抄録なし・PsycNET は bot 遮断) | https://doi.org/10.2190/7K24-G343-MTQW-115V | **未読**(operant/respondent の比率の逐語は**空欄**) |

### 所見(問い 1)

- 「判断の割合」を名指しで測った一次資料は**存在しない**と書くのが正しい。代わりに使える一次値は **(a) 欲求のある瞬間 49.9%**、**(b) そのうち葛藤 47%・抵抗 42%**、**(c) 方向づけられた(operant)思考が全体の 1/2〜2/3**(Klinger 系・ただし比率の逐語は未取得)。
- 重要な非対称: Hofmann らの枠組みでは **葛藤が抵抗(=自己制御の発動)を呼ぶ**(「increasing conflict predicted a higher likelihood of resistance (Blog = 0.53, p < .001)」)。**欲求の強さは抵抗を予測しない**(「Desire strength ... did not reliably predict resistance (Blog = –0.031, p = .17)」)。つまり日常の「熟考の引き金」は強度ではなく**葛藤**である、という一次証拠がある。
- 「判断」を「欲求と目標が衝突して抑制/選択が要る瞬間」と定義するなら、その割合は**覚醒の 2 割前後**(派生値)。「判断」を「行き先・買う物などの選択」まで広げると測定は無い。

---

## 3. 問い 2: Type 1 / Type 2 の定義・比率・発火条件

### 3-1. 現行定義(Evans & Stanovich 2013)

Evans, J. St. B. T., & Stanovich, K. E. (2013). Dual-Process Theories of Higher Cognition: Advancing the Debate. *Perspectives on Psychological Science*, 8(3), 223–241. doi:10.1177/1745691612460685。**PDF 本文を読んだ**(大学研究室ホスト)。

Table 1「Clusters of Attributes Frequently Associated With Dual-Process and Dual-System Theories of Higher Cognition」(逐語・イタリック=定義的特徴):

| | Type 1 process (intuitive) | Type 2 process (reflective) |
|---|---|---|
| **Defining features** | Does not require working memory / Autonomous | Requires working memory / Cognitive decoupling; mental simulation |
| Typical correlates | Fast / High capacity / Parallel / Nonconscious / Biased responses / Contextualized / Automatic / Associative / Experience-based decision making / Independent of cognitive ability | Slow / Capacity limited / Serial / Conscious / Normative responses / Abstract / Controlled / Rule-based / Consequential decision making / Correlated with cognitive ability |
| (dual-system 版の追加属性) | System 1 (old mind): Evolved early / Similar to animal cognition / Implicit knowledge / Basic emotions | System 2 (new mind): Evolved late / Distinctively human / Explicit knowledge / Complex emotions |

注(逐語): 「Italicized attributes are the proposed defining characteristics in the current article.」

本文(逐語): 「We will argue that only the features italicized in Table 1 are defining characteristics of the two types of processing. Specifically, Type 2 processing is distinguished from autonomous Type 1 processing by its nature—involving cognitive decoupling and hypothetical thinking—and by its strong loading on the working memory resources that this requires. By contrast, other features are simply correlates that occur under well-defined conditions and are neither necessary nor defining features.」

アーキテクチャ(逐語): 「our own theories (in common with others, most notably that of Kahneman & Frederick, 2002 ...) are default-interventionist in structure (a term originally coined by Evans, 2007b). Default-interventionist theories assume that fast Type 1 processing generates intuitive default responses on which subsequent reflective Type 2 processing may or may not intervene.」

批判側: Melnikoff & Bargh 2018「The Mythical Dual-Process Typology」*Trends in Cognitive Sciences* 22(4):280–293 — **未読**(抄録のみ確認)。

### 3-2. Type 2 が介入する頻度(課題ごとの実測)

| 研究 | 方法・N | 数値(逐語) | 出典 URL | 確認 |
|---|---|---|---|---|
| De Neys & Glumicic 2008, *Cognition* 106(3):1248–1299 | Exp.1 思考発話・base rate 無視問題(不一致/一致/中立 各 6 問) | 「accuracy on the incongruent problems was very low. Participants were clearly biased by the salient description and selected the correct response in fewer than 20% of the cases」/ 「base rates ... mentioned only 18% of the time」/「on the 80% of the [incongruent problems that were erred] ...」 | https://doi.org/10.1016/j.cognition.2007.06.002(著者ホストの uncorrected proof を読了) | **原典** |
| 同上・言及と正答の結合 | 不一致 72 試行 | 「the few times that participants did mention the base rates on the incongruent problems (n = 13, out of a total number of 72 trials) they also tended to solve the problem correctly (n = 11 out of these 13 trials or 85% correct when base rates mentioned)」/「whenever participants did manage to give the correct response (n = 14) they typically also referred to the base rates (n = 10 out of these 14 trials or 71% base rates mentioned when correct)」 | 同上 | **原典** |
| 同上・別材料での追試 | 14 名・不一致 4 問=56 試行 | 「Only 21% of the problems were solved correctly (i.e., n = 12 correct responses out of a total of 56 trials) and base rates were mentioned in fewer than 20% of the cases (i.e., n = 11 out of 56). When the problem was solved erroneously base rates were only mentioned 11% of the time (i.e., n = 5 out of 44).」 | 同上 | **原典** |
| 同上・**監視は成功している**証拠 | 潜時・不意打ち再生・再読 | 抄録(逐語):「Verbal protocols showed no direct evidence for an explicitly experienced conflict. ... However, more implicit measures of conflict detection such as participants' retrieval of the base rate information in an unannounced recall test, decision making latencies, and the tendency to review the base rates indicated that the base rates had been thoroughly processed. On control problems where base rates and description did not conflict this was not the case.」/ 結論:「at least in case of the classic base rate neglect phenomenon, heuristic thinking seems to be always accompanied by successful analytic monitoring. Whenever the base rates and description disagree people will detect this conflict and consequently redirect attention towards a deeper processing of the base rates.」 | 同上 | **原典** |
| 同上・再生率 | 中立 vs 一致 | 中立問題「they correctly identified which group was the largest 66% of the time」/ 一致問題「Because base rates were hardly explicitly considered, correct base rate recall reached only 36%」。**不一致問題の再生率の数値は図(Fig. 2)にのみ有り、本文に数値は無い=空欄** | 同上 | **原典**(不一致の数値は未取得) |
| 同上・潜時 | Fig. 3/4 | 本文の逐語: 高得点群(n=22・平均正答 44%)は不一致問題に「took more time to solve the incongruent problems ... F(1,41) = 6.61, MSE = 29.66, p < .015」。**「約 5 秒余分」という具体値は図のみで本文になく、検索要約は二次**。潜時の秒数は**空欄** | 同上 | **原典**(秒数は未取得) |
| Frederick 2005, *J. Econ. Perspect.* 19(4):25–42 | CRT 3 問・3,428 名・35 研究・26 か月 | Table 1「Overall / 1.24 / 33% / 28% / 23% / 17% / 3428」(平均 CRT・0/1/2/3 問正答の%・N)。最高 MIT 2.18(0 問 7%・3 問 48%・N=61)、最低 University of Toledo 0.57(0 問 64%・3 問 5%・N=138)、Princeton 1.63、Carnegie Mellon 1.51(N=746)、Michigan Ann Arbor 1.18(N=1267) | https://doi.org/10.1257/089533005775196732(Wayback 経由の出版 PDF を読了) | **原典** |
| 同上・直感解の性質 | — | 逐語:「Here, an intuitive answer does spring quickly to mind: '10 cents.' But this 'impulsive' answer is wrong. ... nearly everyone who does not respond '10 cents' does, in fact, give the correct response: '5 cents.'」 | 同上 | **原典** |
| Meyer, Spunt & Frederick(bat & ball 追試・**未刊行ドラフト "EXTREMELY ROUGH DRAFT"**) | 6 研究・計 2,619 名(UCLA 551・Yale 275・オンライン 766/533 など) | 警告(問題文の色分け)条件と統制の正答率「only slightly better with a warning than without one, (45% vs. 50% correct, z(1,363) = 1.95, p = .051), a surprisingly small effect of a rather heavy-handed manipulation」 | 大学ワークショップ配布 PDF(law.yale.edu) | **原典だが未刊行**(引用は慎重に) |
| Pennycook, Fugelsang & Koehler 2015, *Cognitive Psychology* 80:34–72(三段階モデル) | 理論+実験 | ハイライト(逐語):「We develop a three-stage model to explain what causes analytic thinking to occur. The model distinguishes conflict detection and decoupling as early and late sources. Bias can be caused by failures at either early or late stages.」複数の Type 1 出力が競合しうる | https://doi.org/10.1016/j.cogpsych.2015.05.001 | **抄録/ハイライトのみ**(本文 **未読**・ScienceDirect は有料) |
| Evans 2007「default-interventinist」原典 | — | Evans & Stanovich 2013 の引用で確認(上記) | — | 二次(Evans 2007 本体は **未読**) |

### 所見(問い 2)

- 「Type 2 は思考の何%で発火するか」を**日常で**測った研究は無い。実験室の課題では「**既定では発火しない**」が答え: 不一致 base rate 問題で 80% が直感解、CRT で 33% が 3 問とも直感解・平均 1.24/3。
- 一方で**葛藤の検知(監視)は安価で常時走っている**(De Neys)。設計語彙としては「監視(常時・安い)」と「介入(まれ・高い)」を分けるべきで、原典はこれを **shallow monitoring + optional deeper processing** と表現している。
- **驚き・予測誤差が熟考を起こす**という直接の一次証拠として今回確認できたのは、(i) De Neys の不一致条件での潜時延長・再読・再生の上昇、(ii) Hofmann らの「葛藤 → 抵抗」の係数(Blog = 0.53, p < .001)、(iii) 神経側の信頼度ベース調停(§5-2 の Lee ら 2014)。「期待違反が反応時間を延ばす」ことの**一般的な**一次資料は今回の探索範囲では確認できていない(**空欄**)。

---

## 4. 問い 3: 速い判断の質(規則的な環境なら任せられるか)

Kahneman, D., & Klein, G. (2009). Conditions for intuitive expertise: A failure to disagree. *American Psychologist*, 64(6), 515–526. doi:10.1037/a0016755。**PDF 本文を読んだ**。

| 主張 | 逐語 | 確認 |
|---|---|---|
| 2 つの必要条件 | 「we explore two necessary conditions for the development of skill: high-validity environments and an adequate opportunity to learn them」 | **原典** |
| 認識モデルからの導出 | 「The recognition model implies two conditions that must be satisfied for an intuitive judgment (recognition) to be genuinely skilled: First, the environment must provide adequately valid cues to the nature of the situation. Second, people must have an opportunity to learn the relevant cues.」/「A crucial conclusion emerges: Skilled intuitions will only develop in an environment of sufficient regularity, which provides valid cues to the situation.」 | **原典** |
| 高妥当性/ゼロ妥当性 | 「We describe task environments as 'high-validity' if there are stable relationships between objectively identifiable cues and subsequent events or between cues and the outcomes of possible actions. Medicine and firefighting are practiced in environments of fairly high validity. In contrast, outcomes are effectively unpredictable in zero-validity environments. To a good approximation, predictions of the future value of individual stocks and long-term forecasts of political events are made in a zero-validity environment.」 | **原典** |
| 妥当性と不確実性は両立する | 「Validity and uncertainty are not incompatible. Some environments are both highly valid and substantially uncertain. Poker and warfare are examples. The best moves in such situations reliably increase the potential for success.」 | **原典** |
| 学習条件 | 「An environment of high validity is a necessary condition for the development of skilled intuitions. Other necessary conditions include adequate opportunities for learning the environment (prolonged practice and feedback that is both rapid and unequivocal).」 | **原典** |
| 主観的確信は使えない | 「Subjective confidence is therefore an unreliable indication of the validity of intuitive judgments and decisions.」/「The safe way to evaluate the probable accuracy of a judgment (our own or someone else's) is by considering the validity of the environment in which the judgment was made as well as the judge's history of learning the rules of that environment.」 | **原典** |

### 所見(問い 3)

- 「速い層に**規則的な環境の判断だけ**任せる」は、この論文が**そのまま支持する**構図である(高妥当性=速い層に任せてよい・ゼロ妥当性=任せてはいけない)。
- ただし論文が同時に釘を刺すのは、**「速い層自身の確信度」は任せてよいかの指標にならない**こと。任せてよいかは**環境の妥当性**と**学習機会**という**外から測る 2 量**で決めよ、と書いてある。この点は「小モデルの confidence で LLM を呼ぶか決める」設計に対する**最も強い一次の反証材料**になりうる(事実の含意としてのみ記す)。

---

## 5. 問い 4: 計算モデルの先行(速い/遅いの分割と、遅い層の呼び出し判断)

### 5-1. メタ推論・resource-rational

| 研究 | 位置づけ | 数値/逐語 | 出典 URL | 確認 |
|---|---|---|---|---|
| Russell & Wefald 1991, *Artificial Intelligence* 49(1–3):361–395 | 「計算そのものを行為として選ぶ」枠組みの原典 | 抄録(逐語):「In this paper we outline a general approach to the study of metareasoning, not in the sense of explicating the semantics of explicitly specified meta-level control policies, but in the sense of providing a basis for selecting and justifying computational actions. This research contributes to a developing attack on the problem of resource-bounded rationality, by providing a means for analyzing and generating optimal computational strategies.」 | https://doi.org/10.1016/0004-3702(91)90015-C | **抄録のみ**(本文 **未読**・有料) |
| Lieder & Griffiths 2020, *Behavioral and Brain Sciences* 43:e1 | resource-rational analysis の総説 | 「We identify the rational use of limited resources as a unifying principle underlying these diverse approaches, expressing it in a new cognitive modeling paradigm called resource-rational analysis.」 | https://doi.org/10.1017/S0140525X1900061X | **抄録のみ**(本文 **未読**。無料 PDF は研究室ホストにあるが今回は未取得) |
| **Milli, Lieder & Griffiths 2017**, AAAI-17, 4422–4428 | **「なぜ 2 系なのか」を形式的に解いた**最重要先行 | 抄録(逐語):「A possible approximation that humans may use to do this is to only metareason over a finite set of cognitive systems that perform variable amounts of computation. The highly influential 'dual-process' accounts of human cognition, which postulate the coexistence of a slow accurate system with a fast error-prone system, can be seen as a special case of this approximation. ... **We find that the optimal number of systems depends on the variability of the environment and the costliness of metareasoning. Consistent with dual-process theories, we also find that when having two systems is optimal, then the first system is fast but error-prone and the second system is slow but accurate.**」/ 本文:「the conditions under which we would most expect to see two cognitive systems like the ones suggested by dual-process theories are when the environment has high variability but there is also a correspondingly high enough cost of metareasoning that the optimal number of cognitive systems is only two」/「As the costliness of metareasoning decreases, the optimal number of systems increases.」 | https://doi.org/10.1609/aaai.v31i1.11156(研究室ホスト PDF を読了) | **原典** |
| Milli, Lieder & Griffiths 2021, *Cognition* 217:104881 | 上の雑誌版 | 抄録(逐語・検索要約経由):「we find that there is a plausible range of conditions under which it is optimal to be equipped with a fast system that performs no deliberation ('System 1') and a slow system that achieves a higher expected accuracy through deliberation ('System 2')」 | https://doi.org/10.1016/j.cognition.2021.104881 | **抄録のみ**(本文 **未読**) |

### 5-2. 人の脳での「呼び出し判断」の実測

Lee, S. W., Shimojo, S., & O'Doherty, J. P. (2014). Neural Computations Underlying Arbitration between Model-Based and Model-free Learning. *Neuron*, 81(3), 687–699. doi:10.1016/j.neuron.2013.11.028。

| 量 | 逐語 | 確認 |
|---|---|---|
| 調停の原理 | 「we provide evidence for an arbitration mechanism that allocates the degree of control over behavior by model-based and model-free systems **as a function of the reliability of their respective predictions**」 | 抄録(**原典本文は未読**) |
| 脳部位 | 「A region of inferior lateral prefrontal cortex (ilPFC) bilaterally was found to correlate with the reliability of both the model-based and the model-free systems (peak z scores were 5.18, and 4.45, respectively), although activity in these areas correlated best with the reliability of whichever system had the maximum reliability (max(RelMB,RelMF; peak z score: 5.68; p < 0.05 FWE)」 | 二次(全文ページの引用・**未読**) |
| 信頼度の計算 | model-based の信頼度は**状態予測誤差(SPE)**から、model-free の信頼度は**報酬予測誤差(RPE)**から | 二次 |
| どちらが何%の試行を支配したか | **報告なし**(探索した範囲では試行割合の数値は見つからなかった)=**空欄** | — |

補助: Daw, Niv & Dayan 2005 *Nat Neurosci* 8:1704(不確実性に基づく前頭前野と線条体の競合)は Milli らが引用。**未読**。

### 5-3. 認知アーキテクチャ

| 研究 | 数値/逐語 | 出典 | 確認 |
|---|---|---|---|
| Sun, Zhang & Mathews 2006, *Cognitive Systems Research* 7(4):327–338(CLARION のメタ認知サブシステム MCS) | MCS の職務の列挙(逐語):「(6) **cognitive mode selection: selection of explicit processing, implicit processing, or a combination thereof (with proper integration parameters), in the ACS**, (7) setting parameters of the ACS and the NACS ...」。層の選択は確率的:「With the probability PTL, if there is at least one rule indicating an action in the current state, we use the outcome from the rule set; otherwise, we use the outcome of the bottom level (which is always available). With the probability PBL(=1 − PTL), we use the outcome of the bottom level. The selection probabilities may be variable, determined through a process known as ''probability matching'': that is, **the probability of selecting a component is determined based on the relative success ratio of that component**.」。抄録:「Some currently popular cognitive architectures lack sufficiently complex built-in meta-cognitive mechanisms.」 | https://doi.org/10.1016/j.cogsys.2005.09.001(著者ホスト PDF を読了) | **原典** |
| ACT-R | 探索の範囲では**メタ認知専用モジュールは存在しない**(メタ認知は当該アーキテクチャ上の**モデル**として実装される)。逐語は取れず | — | **未確認**(否定の断言はしない。ACT-R 側の一次確認は **未実施**) |

### 5-4. LLM 側: 小さい門番が大きいモデルを呼ぶ

| 研究 | 数値(逐語) | 出典 | 確認 |
|---|---|---|---|
| Chen, Zaharia & Zou 2023, FrugalGPT(arXiv:2305.05176) | 抄録:「We review the cost associated with querying popular LLM APIs—e.g. GPT-4, ChatGPT, J1-Jumbo—and find that these models have heterogeneous pricing structures, with fees that can differ by two orders of magnitude. ... **Our experiments show that FrugalGPT can match the performance of the best individual LLM (e.g. GPT-4) with up to 98% cost reduction or improve the accuracy over GPT-4 by 4% with the same cost.**」/ 具体機構:「We employ a **DistilBERT tailored to regression as the scoring function**. It is important to note that DistilBERT is considerably smaller and therefore less expensive than all LLMs considered here. ... the learned FrugalGPT sequentially calls GPT-J, J1-L, and GPT-4. For any given query, it first extracts an answer from GPT-J. **If the score of this answer is greater than 0.96, the answer is accepted as the final response. Otherwise, J1-L is queried. J1-L's answer is accepted as the final response if its score is greater than 0.37; otherwise, GPT-4 is invoked**」/「The scoring function can be obtained by training a simple regression model that learns whether a generation is correct from the query and a generated answer.」 | https://arxiv.org/abs/2305.05176(PDF 本文を読了) | **原典** |
| Ong ら 2024, RouteLLM(arXiv:2406.18665) | 抄録:強/弱 2 モデル間のルータを選好データで学習し、「significantly reduces costs-by over 2 times in certain cases-without compromising the quality of responses」。強弱ペアを差し替えても転移する | https://arxiv.org/abs/2406.18665 | **抄録のみ**(本文 **未読**) |
| Zhang ら 2025, DPT-Agent(arXiv:2502.11882・ACL 2025 Main) | System 1 =「Finite-state Machine (FSM) and code-as-policy」で高速・制御可能な決定、System 2 =「Theory of Mind (ToM) and asynchronous reflection」。動機は**リアルタイム同時協調での遅延** | https://arxiv.org/abs/2502.11882 | **抄録のみ**(本文・数値は **未読**) |
| DynamicMind(arXiv:2506.05936) | 学習可能な「Mind Router」が fast/normal/slow を切り替える | https://arxiv.org/abs/2506.05936 | **未読**(検索要約のみ) |

### 5-5. 社会シミュレーションでの先行(**動的ルーティングは見つからなかった**)

| 研究 | 事実 | 出典 | 確認 |
|---|---|---|---|
| Taillandier ら 2025, Integrating LLM in Agent-Based Social Simulation(arXiv:2507.19364・v3 2026-09-07) | **PDF 本文を読んだ**。結合様式として挙げられているのは「**LLM-as-Subroutine**」と「**LLM-as-Policy**」。SLM について逐語:「An intermediate solution is provided by **Small Language Models (SLMs)**, which can potentially combine some of the contextual flexibility of language models with substantially lower inference costs. ... **whether SLMs provide sufficient behavioural fidelity for a given application remains an empirical question and should be evaluated independently of their computational advantages.**」/ LLM-as-Policy:「Once the policy has been extracted, the simulation can be executed without repeated calls to the original LLM, substantially reducing inference costs」/ 中心的な懸念として「**physics washing**」(厳密な環境が未検証の行動層に不当な信用を与える) | https://arxiv.org/abs/2507.19364 | **原典** |
| **訂正**: 「Hybrid Constitutional Architectures」 | 検索要約はこの語をこの論文のものとして提示したが、**PDF 全文(29 ページ)を grep した結果、"Constitutional" という語は本文に存在しない**。この語は**使わない**(検索要約の誤り) | 同上 | **親サブの一次確認による否定** |
| HiSim(Mou ら 2024)系 / LLM+拡散モデル併用(arXiv:2510.16366) | 社会シミュ側の主流は「**少数の中核エージェントだけ LLM・残りは ABM/数値モデル**」という**静的な**階層 | — | **未読**(検索要約のみ・数値なし) |
| 「毎決定ごとに速い層が LLM を呼ぶか決める」社会シミュ | 今回の探索では**該当例を発見できず**=**無い**(探索の範囲で) | — | — |

---

## 6. 問い 5: 「思考の切り替わり」と「判断」の対応

| 研究 | 数値 | 確認 |
|---|---|---|
| Tseng & Poppenk 2020, *Nat Commun* 11:3480 | 思考の切り替わり中央値 **約 6.5 回/分**(7T fMRI・184 名)。**これは脳のメタ状態遷移であって「判断」ではない**。著者も遷移≒新しい思考の等置に慎重 | 既存(第240・親が **原典**を読了。docs/research/v2-thought-frequency-anchors-note.md H1) |
| 判断の頻度を直接測った研究 | **無い**。今回の探索でも見つからなかった。§2-1 のとおり「35,000 回」も「226.7 回」も錨にしない | — |
| 遷移と判断の対応づけを試みた研究 | **無い**(探索の範囲で) | — |

---

## 7. シミュレーションへの含意(事実の含意のみ・設計案は書かない)

1. **「判断の割合」を根拠に層の予算を割り当てることはできない**。一次資料が無いため、そこに数字を置けばそれは設計者の指紋になる。使える錨は「欲求 49.9%・葛藤 47%・抵抗 42%(Hofmann ら)」「方向づけられた思考 1/2〜2/3(Klinger 系・比率の逐語は未取得)」に限られる。
2. **Type 1/Type 2 の切り分け基準は「速さ」ではなく「作業記憶とデカップリングの要否」**(Evans & Stanovich 2013)。したがって「速い=小モデル/遅い=LLM」を二重過程理論で正当化するなら、分割線は**速度**ではなく「**仮定的思考(いまと違う状態を心的にシミュレートする)を要するか**」に置くのが原典に忠実である。
3. **監視と介入は別物**。De Neys は「監視は常に成功し、介入はほとんど起きない」と報告した。したがって「葛藤検知器」を安く常時走らせることは人の実測と整合し、「熟考を毎回走らせる」ことは整合しない。
4. **熟考の引き金は強度ではなく葛藤**(Hofmann ら: 葛藤→抵抗 Blog=0.53, p<.001 / 欲求の強さ→抵抗 は非有意 p=.17)。「強い欲求が来たから LLM を呼ぶ」は一次資料と逆向き。
5. **速い層に任せてよいかは、速い層の確信度ではなく環境の妥当性と学習機会で決まる**(Kahneman & Klein 2009)。「主観的確信は妥当性の信頼できない指標」と明記されている。一方 LLM 工学側の実装(FrugalGPT・RouteLLM)は**まさにスコア/確信度で門番を作っている**。この二つは**別の主張**であり、混ぜて根拠にはできない。
6. **2 系構成が最適になる条件は形式化されている**(Milli ら 2017): 環境のばらつきが大きく、かつ**メタ推論のコストが十分高い**とき。メタ推論が安くなるほど最適な系の数は**増える**。つまり「門番を薄く安くする」ほど、理論上は 2 系より多系に寄る。
7. **社会シミュレーションでの先行は「静的な階層」**(一部の体だけ LLM)であって、**毎決定の動的ルーティングは前例が見つからない**。前例が無いこと自体は、パターン台帳ゲート(「どの現実パターン照合に使うか」)を自前で書き切る必要があることを意味する。
8. Taillandier ら 2025 の **physics washing** の指摘は、速い層を増やして呼数を減らす方向の変更が「環境の厳密さで行動層の未検証を覆う」形にならないかの検査を要求する。

---

## 8. 未読・空欄の一覧

| 項目 | 理由 |
|---|---|
| Klinger & Cox 1987–1988 本文/抄録(operant vs respondent の比率の逐語) | SAGE 403・Semantic Scholar は abstract elided・Bangor は抄録なし・PsycNET は bot 遮断。**「約 1/3 が無方向」は検索要約経由の二次**。Klinger 2013 の自己引用「a third and a half of waking thoughts」で代用した |
| Klinger 1978「Modes of normal conscious flow」原章 | 有料書籍章。中央値 5 秒・平均 9/14 秒は Klinger 2013 経由 |
| Hofmann, Vohs & Baumeister 2012 *Psychological Science*(領域別の抵抗率・成功率) | 出版社 403・大学ホスト PDF は JS 壁。領域別表は取得できず |
| De Neys & Glumicic 2008 の不一致問題の再生率の数値・潜時の秒数 | 図(Fig. 2/3/4)にのみ存在し本文に数値なし。「約 5 秒余分」は二次 |
| Pennycook, Fugelsang & Koehler 2015 本文 | ScienceDirect 有料。ハイライト/抄録のみ |
| Lieder & Griffiths 2020 BBS 本文 | 抄録のみ |
| Milli, Lieder & Griffiths 2021 *Cognition* 本文 | 抄録のみ(2017 AAAI 版は本文読了) |
| Russell & Wefald 1991 本文 | 有料。抄録のみ |
| Lee, Shimojo & O'Doherty 2014 本文 | 抄録+全文ページ引用のみ。**どちらの系が何%の試行を支配したかの数値は見つからず** |
| Daw, Niv & Dayan 2005 | 未読 |
| Evans 2007(default-interventionist の原典) | 未読(Evans & Stanovich 2013 経由) |
| Melnikoff & Bargh 2018(批判側) | 未読 |
| RouteLLM / DPT-Agent / DynamicMind の本文・数値 | 抄録のみ |
| ACT-R にメタ認知モジュールが無いことの一次確認 | **未実施**(否定は断言しない) |
| 「期待違反が反応時間・熟考を延ばす」一般的な一次資料 | 今回の探索では特定できず |
| HiSim ほか社会シミュの静的階層の数値(体数・コスト) | 未読 |
| 「判断の頻度」「思考に占める判断の割合」を直接測った研究 | **存在を確認できなかった=無い(空欄)** |

---

## lit README 追記行

| 分野 | 著者 年 | タイトル | URL | 何が取れたか |
|---|---|---|---|---|
| 認知(日常の欲求・葛藤・自己制御) | Hofmann, Baumeister, Förster & Vohs 2012 | Everyday Temptations: An Experience Sampling Study of Desire, Conflict, and Self-Control (*JPSP* 102:1318) | https://doi.org/10.1037/a0026545 | N=205・7 日×7 信号・応答 10,558。欲求あり 49.9%・葛藤 47%(非葛藤 53.2%)・抵抗 42%・実行 48%・非抵抗時の実行 69.6%。葛藤→抵抗 Blog=0.53 / 欲求強度→抵抗は非有意 |
| 認知(内的経験の頻度) | Heavey & Hurlburt 2008 | The phenomena of inner experience (*Consciousness and Cognition* 17:798) | https://doi.org/10.1016/j.concog.2007.12.006 | 内言 26%・内的視覚 34%・無象徴思考 22%・感情 26%・感覚 22%(30 名×10 瞬間)。個人差 0〜75/80% |
| 認知(思考流の次元) | Klinger 2013 | Goal commitments and the content of thoughts and dreams: basic principles (*Front. Psychol.* 4:415) | https://doi.org/10.3389/fpsyg.2013.00415 | 課題非依存の思考=覚醒思考の 1/3〜1/2・夢様の痕跡 25%・分節 中央値 5 秒(平均 9/14 秒)・16 h で約 4,000 分節。Klinger & Cox 1987–88 の数値の自己引用元 |
| 二重過程理論(定義) | Evans & Stanovich 2013 | Dual-Process Theories of Higher Cognition: Advancing the Debate (*Perspect. Psychol. Sci.* 8:223) | https://doi.org/10.1177/1745691612460685 | Table 1 の逐語。定義的特徴は Type 1=作業記憶不要・自律的 / Type 2=作業記憶必要・認知的デカップリング。速い/遅いは相関にすぎない。default-interventionist の定義 |
| 二重過程理論(葛藤検知) | De Neys & Glumicic 2008 | Conflict monitoring in dual process theories of thinking (*Cognition* 106:1248) | https://doi.org/10.1016/j.cognition.2007.06.002 | 不一致問題の正答 <20%・base rate 言及 18%・言及時 85% 正答・正答時 71% 言及。追試 21%/<20%/11%。監視は常に成功・介入はまれ |
| 二重過程理論(直感回答率) | Frederick 2005 | Cognitive Reflection and Decision Making (*J. Econ. Perspect.* 19:25) | https://doi.org/10.1257/089533005775196732 | CRT Table 1: N=3,428・平均 1.24/3・0 問 33%・1 問 28%・2 問 23%・3 問 17%。MIT 2.18〜Toledo 0.57 |
| 二重過程理論(三段階モデル) | Pennycook, Fugelsang & Koehler 2015 | What makes us think? A three-stage dual-process model of analytic engagement (*Cognitive Psychology* 80:34) | https://doi.org/10.1016/j.cogpsych.2015.05.001 | 葛藤検知(早期)とデカップリング(後期)を分離。バイアスはどちらの失敗でも起きる(抄録のみ) |
| 直感の妥当性 | Kahneman & Klein 2009 | Conditions for intuitive expertise: A failure to disagree (*American Psychologist* 64:515) | https://doi.org/10.1037/a0016755 | 熟達直感の 2 条件(高妥当性環境+学習機会)の逐語。高妥当性/ゼロ妥当性の定義。主観的確信は妥当性の指標にならない |
| メタ推論(原典) | Russell & Wefald 1991 | Principles of metareasoning (*Artificial Intelligence* 49:361) | https://doi.org/10.1016/0004-3702(91)90015-C | 計算行為の選択と正当化の枠組み(抄録のみ) |
| メタ推論(資源合理性) | Lieder & Griffiths 2020 | Resource-rational analysis (*BBS* 43:e1) | https://doi.org/10.1017/S0140525X1900061X | 限られた資源の合理的使用という統一原理(抄録のみ) |
| メタ推論(なぜ 2 系か) | Milli, Lieder & Griffiths 2017 | When Does Bounded-Optimal Metareasoning Favor Few Cognitive Systems? (AAAI-17, 4422) | https://doi.org/10.1609/aaai.v31i1.11156 | 系の最適個数=環境のばらつき×メタ推論コストの関数。2 系が最適なとき第 1 系は速く誤りやすい・第 2 系は遅く正確。メタ推論が安くなるほど最適系数は増える |
| メタ推論(雑誌版) | Milli, Lieder & Griffiths 2021 | A rational reinterpretation of dual-process theories (*Cognition* 217:104881) | https://doi.org/10.1016/j.cognition.2021.104881 | 熟考しない速い系+熟考する遅い系が最適になる条件域が存在(抄録のみ) |
| 神経(調停機構) | Lee, Shimojo & O'Doherty 2014 | Neural Computations Underlying Arbitration between Model-Based and Model-free Learning (*Neuron* 81:687) | https://doi.org/10.1016/j.neuron.2013.11.028 | 予測の**信頼度**で制御権を配分。ilPFC が両系の信頼度と max を符号化(peak z 5.18/4.45/5.68)(抄録+全文引用) |
| 認知アーキテクチャ | Sun, Zhang & Mathews 2006 | Modeling meta-cognition in a cognitive architecture (*Cognitive Systems Research* 7:327) | https://doi.org/10.1016/j.cogsys.2005.09.001 | CLARION の MCS が「認知モードの選択(明示/暗黙/混合)」を担う逐語。層選択は成功率に基づく probability matching |
| LLM(カスケード) | Chen, Zaharia & Zou 2023 | FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance (arXiv:2305.05176) | https://arxiv.org/abs/2305.05176 | 小型 DistilBERT のスコアが閾値(0.96/0.37)未満なら次のモデルへ。最大 98% コスト削減・同コストで精度 +4%。API 価格差は 2 桁 |
| LLM(ルーティング) | Ong ら 2024 | RouteLLM: Learning to Route LLMs with Preference Data (arXiv:2406.18665) | https://arxiv.org/abs/2406.18665 | 選好データで強/弱モデル間のルータを学習・場合により 2 倍超のコスト削減(抄録のみ) |
| LLM エージェント(二重過程) | Zhang ら 2025 | Leveraging Dual Process Theory in Language Agent Framework for Real-time Simultaneous Human-AI Collaboration (DPT-Agent, arXiv:2502.11882, ACL 2025) | https://arxiv.org/abs/2502.11882 | System 1=FSM+code-as-policy / System 2=ToM+非同期内省。動機はリアルタイム協調の遅延(抄録のみ) |
| 社会シミュレーション(批判的総説) | Taillandier ら 2025 | Integrating LLM in Agent-Based Social Simulation: Opportunities and Challenges (arXiv:2507.19364) | https://arxiv.org/abs/2507.19364 | LLM-as-Subroutine / LLM-as-Policy の結合様式・SLM は「行動忠実度は経験的問題」・physics washing。**"Hybrid Constitutional Architectures" は本文に存在しない**(検索要約の誤りを一次確認で否定) |
