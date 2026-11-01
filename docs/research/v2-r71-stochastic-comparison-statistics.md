# R-71 答申: 確率的なシミュレーションの比較の統計手順(共通乱数・符号反転の並べ替え検定・二重の並べ替え検定・効果の大きさと信頼区間・必要な本数)

<!-- hdr:v1 -->
- **分野**: 統計学・因果推論 #23 / ABM 方法論 #21 / 検証と V&V #22 / ゲーム産業(常設レーン) | **重要度**: P1(指示書 [v2-wallbounce-decisions-2026-10-03](../design/v2-wallbounce-decisions-2026-10-03.md) §6 ⑮・§6 ⑦ 7-4・§11 第 1 群「統計手順」。10f の salt の道具の設計)
- **一次確認**: **B**(サブ実読。原典本文 23・抄録/二次 11・未読 6。空欄は §9)・既存答申との重なりを §0-2 で確認・親検収 済(第316・2026-10-03: p の下限 1/2^n・2/2^n と Holm の 8 対を再計算・D-46 の N を t で再計算(13/44 本)・Farine & Carter 2022 の double permutation と Klein 2024 の 10 倍超を原典で確認。等級 A−)
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 作成 2026-10-03・リサーチ役サブ(Opus 5.5)。子サブ未起動・Web は読むだけ(PDF は WebFetch が保存したものを pymupdf で抽出、走査画像の PDF は頁を画像にして目視)・コミットなし・台帳/設計書/src 未編集。
> 先に読んだ記録: PENDING §5「追加 D」(salt 3/5/3 は物理の D 層の後に測り直す)・[pending-archive](../log/pending-archive-2026-09-28.md) の D-46 行・[状態と乱数の棚卸し](../bench/analysis/wallbounce-0930/state-inventory-refresh.md) 表 3・[D-102 の土台のアジェンダ](../design/v2-d102-foundation-implementation-agenda.md) §1・§3(10c・10f)・[再開と決定論 v0.1](../design/v2-resume-determinism-draft.md) §5・`src/shibuya/core/rng.py`(Philox4x64・鍵 = blake3(seed, domain)・カウンタ = tick/個体)・`tools/c7/seed_exchangeability.py`。

## 結論(5 行)

1. **符号反転の並べ替え検定は、対の本数 n で p の下限が決まる**。片側は 1/2^n、両側は 2/2^n である [再計算]。salt 3 本の両側は 0.25、5 本は 0.0625 で、両側 α=0.05 には 6 対、片側には 5 対が要る。指標 5 本を Holm で読むなら 8 対が要る(§2-3)。いまの 3/5/3 本では検定は成り立たず、「差・幅・差÷幅」の記述にとどまる。
2. **共通乱数(CRN)は分散を減らすとは限らない**。差の分散は (σ1² + σ2² − 2ρσ1σ2)/n で、相関 ρ が正のときだけ得をする(Owen §8.6)。在庫モデルでは ρ が負になり分散が増えた(Wright & Ramsay 1979・抄録)。v2 の乱数は既に「用途の鍵 × カウンタ」の形で、Owen と Random123 が勧める同期の形と同じである。ABM でも、用途ごとに乱数の流れを分けて CRN を作り、必要な本数を 10 倍超減らした例がある(Klein ほか 2024)。そのため、既存答申 R-25 の「部分 CRN では 5.6% しか縮まない」は v2 には悲観的すぎる可能性がある(推測)。ρ は毎回実測して出力する。
3. **「二重の並べ替え検定」という名前で確立しているのは Farine & Carter 2022 の double permutation である**。走の中の観測を時間と場所の枠の中で入れ替えて期待値を作り、観測値との差(偏差の点数)を次にノードの並べ替えで検定する。偏差の点数を使わない場合、第一種の誤りは 26〜60% に達した。二重の方式では 4.7〜7.0% に下がった。指示書の意図がこれかは確認が要る(候補)。似た名前の DSP(Dekker ほか 2007)は回帰の補正の方式で、別物である。
4. **少本数では、ブートストラップの百分位の区間は狭すぎる**(Hesterberg 2015)。対の差の t 区間と、並べ替え検定を反転した区間(到達できる信頼水準が飛び飛びになる)を並べる。効果の大きさは差の生の値と比を主にする。d_z(差の平均 ÷ 差の SD)は CRN で差の SD が縮むほど大きくなるので、CRN の無い比較とは並べない(Lakens 2013 の定義からの推測)。
5. **D-46 の N=(CV/r)² は、相対の標準誤差を r にする式である**。95% の信頼区間の半幅を r にする式ではない [再計算]。CV 0.0325 で半幅 2% には 13 本、1% には 44 本が要る(D-46 の行は 3 本と 11 本)。CV を 2 本から測ると、SD の 95% 区間は 0.45〜31.9 倍に広がる [再計算・正規の仮定]。そのため、Stein の 2 段階法か Hoad の逐次法(n=3 から始め、相対精度を満たした後に 5 本先まで維持を確かめる)で決め、差を比べるときは各腕の CV ではなく対の差の SD を使う。

## §0 出典の表

等級: **◎** 原典本文で数値まで逐語確認(本書では pymupdf の本文抽出か頁画像の目視) / **○** 原典本文を読んだが、逐語は WebFetch の抜粋による(親の再取得で ◎ にできる) / **△** 抄録・二次 / **×** 未読(空欄)

| # | 出典 | URL | 等級 | 読んだ範囲 |
|---|---|---|---|---|
| 1 | Owen A.B.『Monte Carlo theory, methods and examples』第 8 章 Variance reduction §8.6 Common random numbers と章末注 | https://artowen.su.domains/mc/Ch-var-basic.pdf | ◎ | §8.6 全部・章末注の同期の節 |
| 2 | Glasserman P. & Yao D.D. 1992「Some Guidelines and Guarantees for Common Random Numbers」Management Science 38(6):884-908 | https://business.columbia.edu/sites/default/files-efs/pubfiles/4261/glasserman_yao_guidelines.pdf | ◎ | 抄録・§1・§2.3 Synchronization |
| 3 | Wright R.D. & Ramsay T.E. 1979「On the Effectiveness of Common Random Numbers」Management Science 25(7):649-656 | https://doi.org/10.1287/mnsc.25.7.649 | △ | 抄録(検索の要約と IDEAS の書誌)。#2 が「Some empirical results」として引用 |
| 4 | Klein D.J., Abeysuriya R.G., Stuart R.M., Kerr C.C. 2024「Noise-free comparison of stochastic agent-based simulations using common random numbers」arXiv:2409.02086 | https://arxiv.org/abs/2409.02086 | ○ | HTML 版 v2 の方法と結果 |
| 5 | Salmon J.K., Moraes M.A., Dror R.O., Shaw D.E. 2011「Parallel random numbers: as easy as 1, 2, 3」SC11 | https://www.thesalmons.org/john/random123/papers/random123sc11.pdf | ◎ | 抄録・§1・§2 冒頭 |
| 6 | Rossetti M.D.『Simulation Modeling using the KSL』§9.2 Variance Reduction Techniques | https://rossetti.github.io/KSLBook/ch9VRTs.html | △ | 頁は 404。検索の要約の抜粋のみ |
| 7 | Ernst M.D. 2004「Permutation Methods: A Basis for Exact Inference」Statistical Science 19(4):676-685 | https://doi.org/10.1214/088342304000000396 | ◎ | §4.1・§4.2・§5 冒頭 |
| 8 | Winkler A.M., Ridgway G.R., Webster M.A., Smith S.M., Nichols T.E. 2014「Permutation inference for the general linear model」NeuroImage 92:381-397 | https://pmc.ncbi.nlm.nih.gov/articles/PMC4010955/ | ○ | 交換可能性・ISE(符号反転)・p 値の下限 |
| 9 | Phipson B. & Smyth G.K. 2010「Permutation p-values should never be zero」SAGMB 9(1) Art.39 | https://arxiv.org/abs/1603.05766 | △ | 抄録 |
| 10 | Fisher R.A. 1935『The Design of Experiments』§21(対の比較) | なし | × | #7 §5 の引用のみ |
| 11 | Good P.『Permutation Tests』 | なし | × | 未読 |
| 12 | Farine D.R. & Carter G.G. 2022「Permutation tests for hypothesis testing with animal social network data: Problems and potential solutions」Methods in Ecology and Evolution 13(1):144-156 | https://pmc.ncbi.nlm.nih.gov/articles/PMC9297917/ | ○ | 抄録・double permutation の定義・表の誤り率・betweenness の注意 |
| 13 | Dekker D., Krackhardt D., Snijders T.A.B. 2007「Sensitivity of MRQAP Tests to Collinearity and Autocorrelation Conditions」Psychometrika 72(4):563-581 | https://pmc.ncbi.nlm.nih.gov/articles/PMC2798974/ | ○ | QAP の定義・DSP の定義 |
| 14 | Krackhardt D. 1988「Predicting with networks: nonparametric multiple regression analysis of dyadic data」Social Networks 10(4):359-381(と 1987 の QAP の論文) | https://doi.org/10.1016/0378-8733(88)90004-4 | △ | #13 の引用と検索の要約のみ |
| 15 | Anderson M.J. & ter Braak C.J.F. 2003「Permutation tests for multi-factorial analysis of variance」J. Stat. Comput. Simul. 73(2):85-113 | https://doi.org/10.1080/00949650215733 | △ | 抄録 |
| 16 | van Borkulo C.D. ほか 2023「Comparing network structures on three aspects: A permutation test」Psychological Methods 28(6):1273-1285(著者の原稿版) | https://cvborkulo.com/wp-content/uploads/2021/12/comparing-network-structures-on-three-aspects.pdf | ◎ | 抄録・手順の 3 段 |
| 17 | Lakens D. 2013「Calculating and reporting effect sizes to facilitate cumulative science」Frontiers in Psychology 4:863 | https://pmc.ncbi.nlm.nih.gov/articles/PMC3840331/ | ○ | 式 4・6・7・9・10 と推奨 |
| 18 | Hesterberg T. 2015「What Teachers Should Know About the Bootstrap」The American Statistician(arXiv:1411.5279) | https://ar5iv.labs.arxiv.org/html/1411.5279 | ○ | 抄録・§2.3・§5(一部切れ) |
| 19 | Cliff N. 1993「Dominance statistics: Ordinal analyses to answer ordinal questions」Psychological Bulletin 114(3):494-509 | https://doi.org/10.1037/0033-2909.114.3.494 | △ | 二次の定義のみ |
| 20 | Efron B. 1987(BCa)/Efron & Tibshirani『An Introduction to the Bootstrap』 | なし | × | 未読 |
| 21 | Cumming G.(信頼区間の推奨) | なし | × | 未読 |
| 22 | Stein C. 1945「A Two-Sample Test for a Linear Hypothesis Whose Power is Independent of the Variance」Ann. Math. Statist. 16(3):243-258 | https://doi.org/10.1214/aoms/1177731088 | △ | 書誌と二次の要約(Project Euclid の PDF は取得拒否) |
| 23 | Chow Y.S. & Robbins H. 1965「On the Asymptotic Theory of Fixed-Width Sequential Confidence Intervals for the Mean」Ann. Math. Statist. 36(2):457-462 | https://doi.org/10.1214/aoms/1177700156 | ◎ | 457 頁(式 1〜3・定理の前まで。頁画像を目視) |
| 24 | Hoad K., Robinson S., Davies R. 2007「Automating DES Output Analysis: How Many Replications to Run」WSC 2007 | https://www.informs-sim.org/wsc07papers/060.pdf | ◎ | §1〜§2.3・結果の要約 |
| 25 | Law A.M. 2015「Statistical Analysis of Simulation Output Data: The Practical State of the Art」WSC 2015 | https://www.informs-sim.org/wsc15papers/188.pdf | ◎ | 全文 |
| 26 | Lee J.-S. ほか 2015「The Complexities of Agent-Based Modeling Output Analysis」JASSS 18(4)4 | https://jasss.soc.surrey.ac.uk/18/4/4.html | ○ | §2.3〜§2.17・表 1(L-B 答申で親が ◎ 済み) |
| 27 | Lorscheid I., Heine B.-O., Meyer M. 2012 CMOT 18:22-62 | https://doi.org/10.1007/s10588-011-9097-3 | △ | 抄録と #26 の引用(L-B 答申でも原典は空欄) |
| 28 | Secchi D. & Seri R. 2017 CMOT 23(1):94-121 | https://doi.org/10.1007/s10588-016-9218-0 | △ | 本書では抄録のみ(L-B 答申で親が PDF 実読済み) |
| 29 | ten Broeke G., van Voorn G., Ligtenberg A. 2016 JASSS 19(1)5 | https://www.jasss.org/19/1/5.html | ○ | §5.4〜§5.9・§6.2 |
| 30 | Thiele J.C., Kurth W., Grimm V. 2014 JASSS 17(3)11 | https://jasss.org/17/3/11.html | ○ | §2.4・§2.13・§2.14・§3.5・§3.8 |
| 31 | Holm S. 1979「A Simple Sequentially Rejective Multiple Test Procedure」Scand. J. Statist. 6:65-70 | https://www.ime.usp.br/~abe/lista/pdf4R8xPVzCnX.pdf | ◎ | 65〜67 頁(頁画像を目視) |
| 32 | Benjamini Y. & Hochberg Y. 1995 JRSS B 57:289-300 | https://doi.org/10.1111/j.2517-6161.1995.tb02031.x | △ | 抄録(手続きの式は #33 で確認) |
| 33 | Storey J.D. 2002「A direct approach to false discovery rates」JRSS B 64(3):479-498 | https://genomics.princeton.edu/storeylab/papers/directfdr.pdf | ◎ | §1・式 (12)(BH の手続きの記述) |
| 34 | ICH E9「Statistical Principles for Clinical Trials」(1998) | https://database.ich.org/sites/default/files/E9_Guideline.pdf | ◎ | §2.2.2 Primary and Secondary Variables |
| 35 | Deng A., Xu Y., Kohavi R., Walker T. 2013「Improving the Sensitivity of Online Controlled Experiments by Utilizing Pre-Experiment Data」WSDM 2013(CUPED) | https://exp-platform.com/Documents/2013-02-CUPED-ImprovingSensitivityOfControlledExperiments.pdf | ◎ | 抄録・§3.2(式 3〜5・7) |
| 36 | Fiedler G. 2014「Deterministic Lockstep」Gaffer On Games | https://gafferongames.com/post/deterministic_lockstep/ | ○ | 決定論の定義・checksum・浮動小数 |
| 37 | Petrov A. 2026「How to Debug Desync in Deterministic Lockstep Games」Bugnet Blog | https://bugnet.io/blog/how-to-debug-desync-in-deterministic-lockstep-games | △ | 業界ブログ(一次の技術文書ではない) |
| 38 | He H. ほか(Thinking Machines Lab)2025「Defeating Nondeterminism in LLM Inference」 | https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/ | ○ | 主張・実験・速度 |
| 39 | Law A.M. & Kelton W.D.『Simulation Modeling and Analysis』/ Law 2015 第 5 版 | なし | × | 未読(CRN の同期と逐次手続きの原文) |
| 40 | Nelson B.L.『Foundations and Methods of Stochastic Simulation』 | なし | × | 未読 |

数: ◎ 12・○ 11・△ 11・× 6(計 40)。

### §0-2 既存答申との重なり(CLAUDE.md §2-4 の確認)

| 既存答申 | 既にカバーしていること | 本書で足すこと |
|---|---|---|
| [L-B 反復回数](v2-replication-count-research.md)(第200) | Lorscheid/Lee の CV 安定・Hoad の相対精度・Law の n ∝ 1/精度²・Ritter と Secchi & Seri の検出力・ECMWF の少数メンバー | 符号反転の検定の p の下限と本数・Chow-Robbins と Stein・D-46 の式の読み方(§5) |
| [R-25 統計と因果](v2-statistics-causal-research.md)(第209) | 多重比較(Bonferroni の作例)・同値検定(TOST・Sargent)・Monte Carlo 検定の p ≥ 1/s・CRN(Currie & Cheng・Murphy 2013 の完全 −93.6% / 部分 −5.6%)・3 seed の t の算術 | CRN の同期の作法と分散が増える条件・ABM での CRN の実例(Klein 2024)・LLM の推論の非決定・Holm と BH・二重の並べ替え検定・効果量と少本数の区間・ゲームの決定論の確認 |
| [lit/causal__shah2026_agent-replay](lit/causal__shah2026_agent-replay.md) | 「ローカル・単一の流れ・固定 seed なら再生できる」 | 同じ (seed, 呼) でもバッチの組み方で出力が変わる点(#38) |

**写しの注意(親の確認事項)**: D-46 の行(pending-archive)の「深夜を 2% で言うなら 3 本・1% なら 11 本」は N=(CV/r)² で、r は**相対の標準誤差**である(§5-1)。R-25 は 5 指標の家族 99% で「N≈20」と t 分布に直している。本書の 95% 単独の値は 13 本と 44 本である。

## §1 共通乱数(CRN)

### 1-1 定義と分散の式
- Owen §8.6(逐語): 二つの推定の分散は「Var(D̂com) = 1/n (σf² + σg² − 2ρσfσg)」「Var(D̂ind) = 1/n (σf² + σg²)」(式 8.21)。「When ρ > 0 we are better off using common random numbers. There is no guarantee that ρ > 0.」
- Owen は CRN を結合(coupling)として述べる。「Common random numbers provide a particularly close coupling between X and X̃.」
- Glasserman & Yao 1992 抄録(逐語): 「though CRN has been observed to work well with a broad range of models, the class of systems for which it is provably advantageous has remained rather limited」。保証の条件は単調性と連続性である(「stressing the roles played by monotonicity and continuity properties」)。
- **CRN の効きの物差し [再計算]**: 式 8.21 の比 Var(D̂com)/Var(D̂ind) = 1 − 2ρσfσg/(σf² + σg²) は、CRN の対だけから推定できる。各腕の salt 間の分散で σf²・σg² を、対の差の分散で分子を出す。比が 1 を超えたら CRN で損をしている。

### 1-2 分散が増える例と、単調性の条件
- Wright & Ramsay 1979(抄録・△): 典型的な在庫モデルで「the CRN technique induces negative correlation and thus augments variance」。各入力に別の流れを割り当てて全部を共通にする設計は「usually, but not necessarily」最大の分散低減になる。
- Glasserman & Yao 1992(逐語): 「to check the benefit of CRN, look at what happens when events change order」。保証の条件は、状態の並びではなく事象の時刻に置く(「we put conditions on the timing of events, rather than the sequence of states」)。
- Klein 2024 で効きが小さくなる条件: 効果が大きいとき、母集団が大きくよく混ざるとき、期間が長いとき(VMMC の介入が「eventually affects most agents」)。
- **v2 への読み(推測)**: LLM の選択は乱数に対して単調ではない。また店に着く順のような事象の順序が腕で入れ替わる。そのため ρ が負になる指標がありうる。ρ と §1-1 の比を毎回出力して確かめる。

### 1-3 乱数の流れの同期(synchronization)
- Owen(逐語): 第 2 段階で使う乱数を、第 1 段階で合格しても取っておく。「To keep the simulation synchronized, we always reserve the values Z11, ..., Z30 for the second stage, even when the test is accepted at stage 1.」
- Owen の章末注(逐語): 「the solution is to give h a different random number stream for each value of θ that we use」「Another is to hash the value of θj into a seed (or a stream identifier) for h to use.」
- Glasserman & Yao §2.3: 同期は「"corresponding" random variables across simulations are generated from the same random numbers」という推奨として文献にある。著者らはこの「folklore on synchronization」を部分的に裏づけた。
- Rossetti §9.2(△・検索の要約): 乱数の源ごとに別の流れを割り当て、同期できない変数は独立な流れにする。
- Klein 2024(○): 決定ごとに独立な流れを割り当てる(「We assign independent PRNG streams to each and every decision」)。各 step で流れを初期状態に戻して k 回跳ばし、1 step で 1 回だけ呼ぶ。個体には「slot」を割り当て、乱数の配列の位置として使う。生まれた個体の slot は親の乱数から決める。ペアの乱数は 2 個体の乱数から作る(u_ij = xor(u_i·u_j, u_i − u_j)/M64)。並べ替えによる無作為の組み合わせは CRN を壊す(「Shuffle-based random pairing is not CRN-safe」)。
- Klein 2024 の数値(○): PPH(10 万体・250 seed)で母体死亡の SE が 6.2 倍と 1.75 倍に縮み、必要な本数が 38 倍と 3 倍減った [再計算: 6.2²=38.4・1.75²=3.06]。SIR の被覆 5% で 10 倍超、90% で約 20%。HIV では介入から 5・20・50 年で、感染回避の削減倍率が 24・2.3・1.4。
- Klein 2024 の確認の形: 改変前の一致はビット一致の検査ではなく、Pearson 相関の時系列で示した(中央の乱数の方式では「The drop in PCC … begins early in the simulation, following the first random draw difference」)。

### 1-4 カウンタ型の乱数で CRN を作る
- Salmon ほか 2011(逐語): 「independent, keyed transformations of counters produce a large alternative class of PRNGs」。鍵つきの全単射を「xn = bk(n)」と書く。「at least 2^64 unique parallel streams of random numbers, each with period 2^128 or more」。全部が TestU01 の BigCrush を通る。
- **v2 の現状(事実・コード)**: `core/rng.py` は Philox4x64 で、鍵 = blake3(master_seed ‖ domain)、カウンタ = (tick, 個体, …) の最大 4 語である。個体数を増やしても既存の個体の列は変わらない(docstring の T4)。これは Owen の「流れの識別子に θ をハッシュする」形と、Klein の「決定ごとの流れ」に当たる。個体の ID が固定なので、Klein の slot の工夫は要らない(推測)。
- **v2 で同期を壊すもの(棚卸し表 3 からの読み・推測)**: (i) 状態を持つ乱数 2 本(`world.salient`・`world.public_service_dispatch`)。腕で引く回数が変わると、それ以後の列がずれる。10c でカウンタ型にすれば解ける。(ii) 鍵に日番号の無い 19 件。複数日では日ごとの独立性の問題で、CRN の対の間では同じに働く。(iii) LLM の応答(§1-5)。

### 1-5 LLM の推論の非決定
- He ほか 2025(○): 推論の非決定の主因はバッチ不変性の欠如である(「the load (and thus batch-size) nondeterministically varies!」)。温度 0 で 1000 回の生成から 80 通りの文が出た(最多 78 回)。バッチ不変のカーネルでは 1000 回とも同一になった。代わりに 26 秒が 55 秒(改良版で 42 秒)に延びた。
- Fiedler 2014(○): 同じ機械でも、コンパイラ・OS・CPU の違いでは決定論にならない(「probably not even deterministic between debug and release builds」)。
- **v2 への読み(推測)**: 腕で一部の体のプロンプトが変わると、同じバッチに入る他の体の出力も変わりうる。CRN を LLM の側まで通すには、呼ごとのサンプラの種を (salt, 体, 絶対 tick, 起床級) から作ることと、バッチ不変の推論の 2 つが要る。v2 の決定論の方針(同じ環境・同じテープ)は再生の一致を求めるもので、腕の間の一致は求めていない。今の実 LLM のランは部分 CRN に当たる。mock と古典の方策の腕では、エンジン側の乱数だけなので完全 CRN に近い。

### 1-6 「改変した時点までは 2 本の記録が一致する」の確認の形
- Fiedler 2014(逐語): 「given the same initial condition and the same set of inputs」「your simulation gives exactly the same result」。物理の状態の checksum を毎フレーム取れば一致する(「you could take a checksum of your entire physics state at the end of each frame and it would be identical」)。
- Petrov 2026(△・業界ブログ): 毎 tick の状態の checksum を部品ごとに分け、最初に食い違った部品を調べる(「Always investigate the first subsystem that diverges, not the most obviously broken one」)。入力の hash を状態の hash と並べ、入力が一致して状態が違うならシミュレーションの側が原因と読む。
- **文献の形のまとめ**: (a) 入力の一致(母集団・世界・日課・manifest の差は腕の欄だけ) (b) 改変の時刻 T0 より前の全 checkpoint の状態 hash の一致 (c) T0 以後で最初に食い違った tick と部品を報告 (d) 同じ設定を腕として 2 回回して差が厳密に 0(A/A)。
- v2 には (a) の道具(`tools/c7/seed_exchangeability.py`)と、(b) の材料(checkpoint の 5 本の hash・10b の behavior-hash)がある。

## §2 対の並べ替え検定(符号反転)

### 2-1 定義
- Winkler 2014(○): 符号反転の行列 S_j は「a N × N diagonal matrix whose non-zero elements consist only of + 1 or − 1」。前提は「the joint distribution of the error terms is invariant with respect to sign flipping」で、正規性は要らないが対称性が要る(「ise relaxes normality, although symmetry (i.e., non-skewness) of distributions is required」)。符号の組の最大数は 2^N。1 標本の検定(対の差を含む)に向く。
- Ernst 2004 §5(逐語): 対のデータの並べ替えは「paired data (Fisher, 1935, Section 21; Ernst and Schucany, 1999)」に当たる。原典の Fisher §21 は未読(空欄)。
- CRN の対で回した腕と基準の差 D_i(i = 1..n)は、帰無仮説「腕は効かない」のもとで 0 のまわりに対称である。この対称性が符号反転の前提になる(推測。salt が交換可能で、腕と基準の役を入れ替えても分布が同じという読み)。

### 2-2 p 値の計算
- Ernst 2004 §4.2(逐語): 無作為の並べ替えでは「p̂ = (1 + Σ I(ti ≥ t*)) / (M + 1)」で、p は「no smaller than 1/(M + 1)」。Dwass 1957 の方式で、検定は正確のままである(「The test remains exact and conditionally distribution-free」)。
- Winkler 2014(○): 「the smallest possible p-value is 1/J, not zero」。Phipson & Smyth 2010(△): 0 にすると p を約 1/m 小さく見積もる。
- 両側の p(Ernst §4.1・逐語): 「p = P(|T − t̄| ≥ |t* − t̄| | H0)」。符号反転の分布は 0 のまわりで対称なので、片側の 2 倍と同じになる [再計算]。
- n が小さいとき(2^n ≤ 100 万程度)は全部の符号の組を数える(正確検定)。それより大きいときは M 回の無作為の組で上の式を使う(親の案)。

### 2-3 本数と p の下限 [再計算]

| 対の数 n | 符号の組 2^n | 片側の p の下限 1/2^n | 両側の下限 2/2^n |
|---|---|---|---|
| 3 | 8 | 0.125 | 0.25 |
| 4 | 16 | 0.0625 | 0.125 |
| 5 | 32 | 0.03125 | 0.0625 |
| 6 | 64 | 0.0156 | 0.03125 |
| 7 | 128 | 0.0078 | 0.0156 |
| 8 | 256 | 0.0039 | 0.0078 |

- 両側 α=0.05 に届く最小は **6 対**、片側(向きを事前に宣言)は **5 対**。
- Holm で k 本の指標を並べると、最小の p は α/k 以下でなければならない。両側で k=2 か 3 なら 7 対、k=5 なら 8 対、k=10 なら 9 対、k=20 なら 10 対が要る。
- 効果が非常に大きくても下限は変わらない。AB7 の「効果が seed 差の 700 倍」(R-25)でも、3 対の両側の p は 0.25 である。

### 2-4 片側と両側・同順位・0 の差
- 片側は、向きを事前登録したときだけ使う(ICH E9 の事前の特定の考え方からの推測)。
- 差の平均を統計量にする場合、差が 0 の対は符号を反転しても値が変わらない。順位(Wilcoxon 型)を使う場合は 0 と同順位の扱いの規則が要る。Good の本の原文は未読(空欄)。

## §3 「二重の並べ替え検定」の同定

| 候補 | 何を二重にするか | 出典 | 指示書の語との合い方 |
|---|---|---|---|
| **A. double permutation** | 走の中の観測を時間と場所の枠で入れ替えて(pre-network permutation)期待値を作り、偏差の点数 = 観測 − 期待を出す。それをノードの並べ替え(QAP など)で検定する | Farine & Carter 2022(○) | **名前として確立している唯一のもの** |
| B. 2 段の並べ替え(ノードのラベル × 腕) | 走の中ではノードの並べ替え、走の間では腕の並べ替え(符号反転) | 確立した文献は見つからない(空欄)。Anderson & ter Braak 2003 の「項ごとに入れ替える単位を変える」考え方(△)に近い | 構成としては自然。名前は無い |
| C. DSP(double semi-partialing) | MRQAP で交絡 Z を X から抜いた残差を並べ替え、Z を回帰に 2 回入れる | Dekker ほか 2007(○) | 名前に「double」があるが、目的は回帰係数の検定で別物 |

### 3-1 Farine & Carter 2022 の中身(○)
- 定義(逐語): 「using pre‐network permutations to adjust the values for each node or edge before conducting a node permutation test」。偏差の点数は「We call this observed–expected difference the deviation score (e.g. ∆degree)」。
- 二つの片方だけの弱点(抄録の要約): 走の中の入れ替えは交絡(空間・時間・観測の偏り)を扱えるが、「社会構造が無作為」という帰無しか検定できない。ノードの並べ替えは、交絡が観測された網を形づくっていないときにしか使えない。
- 第一種の誤り(次数): 効果なし(Sim 1)で走の中の入れ替えだけだと 26.0%、二重で 4.7%。Sim 2(偏りなし)で 37.8% と 5.2%。観測の偏りありでノードの並べ替えだけだと 60.4%、二重で 7.0%。Sim 3 で 18.6% と 5.2%。
- 注意: betweenness では第二種の誤りが 86.2% と高く、「we cannot recommend any solution for hypothesis testing with betweenness in the presence of nuisance effects」。

### 3-2 関連する確立した手法
- QAP(Dekker 2007・逐語): 「This is equivalent to applying the same permutation to the row and column indices of Y.」。この並べ替えは「keeps intact the autocorrelation structure of the observations arranged in the square matrix」。起源は「Mantel, 1967; Hubert, 1987; Krackhardt, 1987」。MRQAP は Krackhardt 1988。
- DSP(Dekker 2007・逐語): 「As such Z enters the regression twice, hence the "double."」。Freedman-Lane と DSP が最も頑健で、検定統計量が pivotal(t など)なら 5 方式とも良くなる(抄録の要約)。
- NCT(van Borkulo ほか 2023・逐語): 2 群のデータを「pooled and repeatedly, randomly resampled (without replacement) into two data sets matching the original sample sizes」として、網を推定し直して統計量の参照分布を作る。比べる量は網の構造・辺の強さ・全体の強さの 3 つ。2 群が独立な横断データであることが前提で、CRN の対には直接は合わない(推測)。

### 3-3 判定
- 「二重の並べ替え検定」が既存の名前を指すなら、Farine & Carter 2022 の double permutation である(同定)。
- 指示書が「走の中のノードの並べ替え × 走の間の腕の並べ替え」の 2 段を意図している可能性もある(候補 B)。どちらかはユーザーに確かめる。

## §4 効果の大きさと信頼区間

### 4-1 効果の大きさ
- Lakens 2013(○): d_z = M_diff / SD_diff = t/√n(式 6・7)。「the unit of analysis is no longer X or Y, but their difference, Z」。d_av = M_diff / ((SD1 + SD2)/2)(式 10)は相関を無視する。d_rm(式 9)は相関を補正する。Hedges の補正 g_s = d_s × (1 − 3/(4(n1 + n2) − 9))(式 4)は独立 2 群の式で、d_s は「especially for small samples (n < 20)」で偏る。
- Lakens の推奨: 被験者内の設計では d_rm か d_av を報告する。d_z は検出力の計算と、個体の中の問いに向く。
- **v2 への読み(推測)**: CRN は差の SD を縮めるので、同じ腕でも d_z は CRN の有無で変わる。主に報告するのは差の生の値・基準に対する比・差の SD とし、d_z は「CRN の対の d_z」と明記して CRN の無い比較とは並べない。d_av も並べると、腕の効果を salt 間のばらつきの単位で読める。
- Cliff の delta(△・二次の定義): δ = Pr(x1 > x2) − Pr(x1 < x2)。順序だけを使う。対の版の定義の原文は未読(空欄)。

### 4-2 信頼区間
- Hesterberg 2015(○・逐語): 「the common bootstrap percentile interval badly under-covers in small samples」。ブートストラップの分布は「too narrow, by a factor of √((n−1)/n) for the mean」。「Bootstrapping does not overcome the weakness of small samples as a basis for inference.」「for the very smallest samples, you may not want to bootstrap」。
- 対の再標本化で作れる異なる標本の数 [再計算]: n=3 で 10 通り、n=5 で 126 通り(n 個から重複を許して n 個を選ぶ組の数)。区間の端が飛び飛びになる。
- 並べ替え検定の反転による区間(Ernst §4.1・逐語): 位置のずれを仮定すれば「estimate Δ with a permutation confidence interval by inverting the permutation test」。例では「A 94.90% confidence interval」のように、到達できる水準が飛び飛びになる。符号反転で n=5 なら、両側の到達水準は 1 − 2j/32(93.75%・87.5% …)で 95% は作れない。n=6 で 96.9% が作れる [再計算・概算]。
- BCa の原典と、少本数での BCa の被覆率は未読(空欄)。
- **v2 への読み(親の案)**: n ≤ 10 では、対の差の t 区間(正規を仮定)と並べ替えの反転区間(到達水準を明記)を並べて出す。百分位のブートストラップは n ≥ 20 程度までは使わない(Hesterberg の n=10 の注意からの推測)。

## §5 必要な本数の決め方

### 5-1 D-46 の式の読み方 [再計算]
- D-46 の N=(CV/r)² は CV/√N = r、つまり相対の標準誤差を r にする式である。95% の信頼区間の半幅を r にするには t_{N−1,0.975}·CV/√N ≤ r を N について解く。
- CV 0.0325(深夜・第204)での値:

| 狙い | (CV/r)² | t を入れた最小 N |
|---|---|---|
| r = 2% | 2.6 → 3 本 | 13 本 |
| r = 1% | 10.6 → 11 本 | 44 本 |

- 3 本での半幅は 8.07%(R-25 の d₃ と一致)。
- CV を 2 本から測ったときの不確かさ: SD の 95% 区間(自由度 1・カイ二乗・正規の仮定)は推定値の 0.45〜31.9 倍。3 本で 0.52〜6.28 倍、5 本で 0.60〜2.87 倍 [再計算]。Lee 2015 も「c_V will exhibit substantial variance for small sample sizes」と注意する(○)。

### 5-2 2 段階法・逐次法・相対精度
- Stein 1945(△・二次の要約): 第 1 段の標本で分散を推定し、その推定から全体の標本数を決める。統計量は第 1 段の分散だけを使うので、帰無のもとで厳密に t 分布になる。原文の式は未読(空欄)。
- Chow & Robbins 1965(◎・457 頁): 幅 2d・被覆 α の区間 I_n = [x̄_n − d, x̄_n + d]。分散が既知なら n = (a²σ²)/d² 以上の最小の整数(式 1)。未知なら v_n = n⁻¹Σ(x_i − x̄_n)² + n⁻¹(式 2)とし、N = 「smallest k ≥ 1 such that v_k ≤ (d²k)/a_k²」(式 3)で止める。仮定は「0 < σ² < ∞」だけ。定理は漸近(d → 0)の性質である。
- Hoad ほか 2007(◎・逐語): 精度を「the ½ width of the Confidence Interval expressed as a percentage of the cumulative mean」と定義し、d_n = 100·t_{n−1,1−α/2}·s_n/(√n·X̄_n) とする。手順は「Let n = 3 … While Convergence Criteria not met」。d_n が目標以下になったら kLimit 本先まで維持を確かめる。例は d_required = 5%・kLimit = 5 で、n = 8 で初めて満たし、9〜13 本で維持を確認する。look ahead で、双峰の出力のモデル(R8)の被覆の失敗が直った。
- Law 2015(◎・逐語): 「If we increase the sample size from n to 4n, then the half-length of the confidence interval … will decrease by a factor of approximately 2」。10 本で半幅が推定値の 1% 未満の例で、半幅を 1/3 にするには「approximately 90 replications」。
- Law 2015 の落とし穴(逐語): 「Failure to determine the statistical precision of simulation output statistics by the use of a confidence interval」。

### 5-3 ABM での実践
- Lee 2015(○): c_V の連続する差が E 未満で以後も維持される n を最小本数とする(Lorscheid の方法)。平均が 0 に近い指標では c_V が n_min を過大にする(「we urge some caution in using c_V」)。検出力の式 n_min ≥ 2(s²/δ)(t_{ν,1−α/2} + t_{ν,1−β/2})²。効果量 0.5・検出力 0.80 で理論 64〜65 本、ABM で 65 本。
- ten Broeke 2016(○): 既定の設定で 10,000 本回し、CV は「largely stabilised after a few hundred replicates」。感度解析では OFAT に 10 本、回帰に 5 本、Sobol' に 0 本。salt 間の分散は全体の分散の 0.88% で、本数を増やす必要がないと判断した。
- Thiele 2014(○): 各設定で 10 本回して平均した。本番では「determine the number of repetitions by running the model with an increasing number of repetitions」とし、CV がほぼ一定になる本数を採る。非線形の入出力では「this assumption may not be fulfilled」。
- Secchi & Seri 2017(△): 2010〜2013 年の組織研究の ABM 55 本の多くが検出力不足。詳細は L-B 答申(親 ◎)。

### 5-4 D-46 の規則と整合する形(親の案)
1. 比べたいのが**差**なら、各腕の CV ではなく**対の差の SD**(CRN の対)で本数を決める。CRN が効けば差の SD は小さく、本数が減る。
2. 第 1 段(パイロット)を n0 本で回し、差の SD を測る(Stein の形)。n0 は 5 以上を勧める(§5-1 の SD の不確かさと、§2-3 の片側の下限から)。
3. 全体の本数 N は t_{N−1}·s_D/√N ≤ r·|基準の平均| を満たす最小の N とし、下限を符号反転の検定が成り立つ 6 本とする。
4. N が大きく先に決めにくい指標は、Hoad の逐次法(d_n ≤ 目標で kLimit 本先まで維持)で 1 本ずつ足す。
5. 「1% なら 11 本」のような (CV/r)² の値は、相対の標準誤差の目標として残し、信頼区間の目標と区別して書く。

## §6 複数の指標の同時比較

- Holm 1979(◎・67 頁の図と本文): 得られた水準を小さい順に並べ、順に α/n, α/(n−1), …, α/1 と比べる(「In the sequentially rejective Bonferroni test the obtained levels are compared to the numbers α/n, α/(n−1), …, α/1」)。古典の Bonferroni はいつでもこれに置き換えられ、誤りの確率は増えない。
- Benjamini & Hochberg 1995(△ 抄録 / 手続きは Storey 2002 ◎): 「k̂ = max{k : p(k) ≤ (k/m)α}」で、p(1)〜p(k̂) を棄却すると「FDR ≤ α」。FDR は誤って棄却した割合の期待値で、全部の帰無が真のときは FWER と同じになる(抄録)。
- ICH E9 §2.2.2(◎・逐語): 「There should generally be only one primary variable.」「The primary variable should be specified in the protocol, along with the rationale for its selection.」「The primary variable should generally be the one used when estimating the sample size」。
- **v2 への読み(親の案)**: 腕と反実仮想の実験ごとに主要な指標を 1 つ事前登録(既存の prereg の形)し、本数は主要な指標で決める。副次の指標は Holm(家族の誤り)で読み、探索の多数の指標(行動コード別など)は BH で読む。§2-3 のとおり Holm は本数の下限を押し上げる。

## §7 ゲームと産業の知見(常設レーン)

- **CUPED**(Deng ほか 2013・◎): 実験前の値 X を制御変量にして Ŷcv = Ȳ − θX̄ + θE(X)(式 3)、最適な θ = cov(Y, X)/var(X)(式 4)で var(Ŷcv) = var(Ȳ)(1 − ρ²)(式 5)。Bing で「we can reduce variance by about 50%」。
- CUPED と CRN の関係(推測): 両方とも相関を使って差の分散を減らす。A/B テストは個体を同時に 2 腕に入れられないので、実験前の値で代わりに相関を作る。シミュレーションは同じ乱数で同じ個体を両腕に置けるので、CRN の対の差は θ = 1 の制御変量に当たる。T0 > 0 の反実仮想では T0 前の区間が 2 本で一致するので、その区間を CUPED の X にしても差には何も足さない。
- **決定論の再生と checksum**(Fiedler 2014・○、Petrov 2026・△): 同じ初期条件と同じ入力でビット一致、毎フレームの checksum、部品ごとの hash、最初に食い違った部品から調べる。§1-6 の確認の形の産業の根拠である。
- **LLM の推論**(He 2025・○): バッチ不変のカーネルで 1000 回の生成が同一になり、速度は約半分。CRN を LLM の側まで通すときの費用の目安になる。
- ゲームの「同じ種で 2 つの版を比べる統計手順」(A/B のバランス調整など)の公式文献は見つからなかった(空欄)。

## §8 v2 への当てはめ(すべて親の案・未リサーチの構成を含む)

### 8-1 10f の道具の入出力
**入力**
- salt の対の一覧: (salt, 基準のラン, 腕のラン)。対ごとに salt が同じであること。
- 改変の時刻 T0(絶対 tick。腕が最初から違うなら 0)。
- 指標の一覧: 主要 1 つ(事前登録の ID)・副次・探索の区分、片側か両側か(片側は向きを登録したときだけ)。
- 検定の種類: 符号反転(既定。2^n ≤ 2^20 なら全数、超えたら M 回の無作為で (b+1)/(M+1))。
- ネットワークの比較のときは、走の中の入れ替えの枠(時間と場所の幅)。

**自動の確認(CRN の健全性)**
1. 入力の一致: `seed_exchangeability` の拡張で、manifest の差が腕の欄だけであること。母集団・日課・世界の hash が対の間で同じであること。
2. T0 より前の全 checkpoint の behavior-hash(10b)が対の間で一致すること。食い違ったら最初の tick と、どの hash(agents・world・activity)かを出して止める。
3. A/A: 基準を 2 回回して全 checkpoint が一致すること(10f の「同じ環境で 2 回回して一致」と同じ)。
4. T0 以後の最初の食い違いの tick と hash を記録する(腕の効きの始まりの記録)。

**出力(指標ごと)**
- 差の平均・基準に対する比・差の SD・対の数 n。
- 対の差の t 区間(95%)と、並べ替えの反転区間(到達した水準を明記)。
- 正確な p(片側/両側)と、その n で到達できる最小の p。最小の p が α を超えるなら「検定不能(本数不足)」と出す。
- 副次の指標は Holm の補正の p、探索の指標は BH の q。
- d_z(「CRN の対」と明記)と d_av。
- CRN の効きの比 Var(D)/(Var(X_基準) + Var(X_腕)) と ρ。比が 1 を超えたら警告する。
- 既存の 3 列(差・salt 間の幅・差 ÷ 幅)も残す。

### 8-2 腕の比較の最小本数
- 開発中の 3/5/3 本は指示書どおり残す(⑦ 7-4)。ただし道具は、3 本では両側の p ≥ 0.25 で「記述のみ」と出す。
- 「腕が効く」と主張する比較は 6 対以上(両側 α=0.05)。向きを事前登録すれば 5 対。主要な指標が 1 つの場合の値で、副次を Holm で読むなら §2-3 の表で増やす。
- 追加 D(物理の D 層の後の測り直し)のときに、各指標の対の差の SD と CRN の効きの比を測り、§5-4 の手順で本数を決め直す。

### 8-3 反実仮想のアンサンブルの本数(D-46 と ⑦ 7-4)
- 基準と改変を同じ salt の組で回し(CRN の対)、主要な指標の対の差の SD から §5-4 で N を決める。下限は 6 本。
- 39 万体のアンサンブル(D-46 の 3 seed)は水準(在圏の帯など)の記述で、反実仮想の差の検定には足りない。差を言うときは 5,000 体などの安い階層で N を確保するか、39 万体で 6 対以上を回すかを選ぶ(判断はユーザー)。
- ⑫ の I_i の分母の「シミュのばらつき」は各腕の salt 間の SD で、CRN の対の差の SD とは別の量である。

### 8-4 ネットワークの構造の比較の手順
1. 主要なネットワークの統計量を 1 つ事前登録する(次数の分布の要約・クラスタ係数・最大成分の割合など)。betweenness は Farine & Carter の注意により主要にしない。
2. 走ごとに、会話や同席の観測を時間と場所の枠の中で入れ替えて期待値を作り、偏差の点数 = 観測 − 期待を出す(Farine & Carter の第 1 段。枠は v2 の辺の作り方、つまり近接と同席に合わせる)。
3. 腕と基準の対ごとに偏差の点数の差を取り、§2 の符号反転で検定する(第 2 段。CRN で体の ID が対の間でそろうので、走の間の単位は salt の対にする)。
4. 「辺の変化が職場の共有のような 2 者の性質と関係するか」を問うときだけ、走の中で MRQAP(Freedman-Lane か DSP、t のような pivotal な統計量)を使う。

## §9 空欄の一覧
1. Fisher 1935 §21(対の比較の符号反転)の原文。
2. Good『Permutation Tests』の、片側と両側・同順位・0 の差の扱いの原文。
3. Law & Kelton / Nelson の教科書の、CRN の同期と逐次手続き(相対精度 γ)の原文。
4. Wright & Ramsay 1979 の本文(在庫モデルで ρ が負になった数値)。
5. BCa の原典(Efron 1987)と、少本数(n ≤ 10)での BCa と対の再標本化の被覆率。
6. Cumming の信頼区間の推奨。
7. Cliff の delta の対(従属)の版の定義の原文。
8. Stein 1945 の 2 段階の n の式の原文。
9. Krackhardt 1987・1988 の本文。
10. 「走の中のノードの並べ替え × 走の間の腕の並べ替え」を二重と呼ぶ確立した文献(候補 B)。
11. LLM の確率出力(離散の選択)での CRN の単調性・相関の文献。
12. ゲーム産業の「同じ種で 2 つの版を比べる」統計手順の公式文献(GDC など)。
13. Rossetti『KSL』§9.2 の本文(頁が 404)。
14. d_z の小標本の補正の式(Lakens 2013 の式 4 は独立 2 群の g_s)。

## §10 ライセンス台帳と INDEX に足す行の案

**ライセンス台帳**: データファイルの取得なし(PDF は WebFetch が保存したものを読んだだけ)=追加行なし。

**INDEX 行の案**:
`| 10-03 | [r71-stochastic-comparison-statistics](v2-r71-stochastic-comparison-statistics.md) | なし | **B** | 統計学・因果推論 #23 / ABM 方法論 #21 / V&V #22 / ゲーム産業 | R-71 比較の統計手順: 符号反転の p の下限 1/2^n(両側 α=0.05 に 6 対)・CRN の式と分散が増える条件と同期(Owen・Glasserman & Yao・Klein 2024)・二重の並べ替え = Farine & Carter 2022 と同定(候補 B は空欄)・少本数の区間(Hesterberg)・D-46 の (CV/r)² は相対 SE(95% 半幅なら 2% に 13 本)・Holm/BH/ICH E9・CUPED・決定論の checksum・10f の道具の入出力案 |`
