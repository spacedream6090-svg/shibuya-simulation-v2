# R-117 答申: E2 反実仮想と介入・アンサンブル・ヒストリーマッチング・慣らしの自動判定(MSER-5)の先例と既存の実装

<!-- hdr:v1 -->
- **分野**: 統計学・因果推論 #23 / ABM方法論 #21 / 検証とV&V・UQ #22 / 予測科学(アンサンブル) #24 / 交通工学 #2 / 計算社会科学 #25 / ソフトウェア工学 #29 | **重要度**: P1(計画 §7 の「E2 → 3-3・CP5-6」。3-3 の残り=CP5-1 の順・CP5-3・CP5-6・艦隊の分岐・L2〜L4 と、第 7 期の慣らしの自動判定の材料)
- **一次確認**: **B**(サブの自己評価。◎ 30・○ 12・△ 13・× 5=計 60。内訳は §0)・**親検収**: 済(第336・2026-10-15)。親が実読して一致: Hoad & Robinson 2011(informs-sim の PDF=頁 495-503・打ち切り点が後半なら無効で既定 10% のバッチを足す・累積の値と極値は使えない・レプリケーションの平均に当てる §3.1・周期の出力は決定の図の CYCLE)/ Franklin & White 2008(頁 541-546・文献欄の Schruben 1982 は 30(3):151-153 と誤記=原典は 569-590)/ Leutbecher ら 2017(ECMWF の受理稿を curl で実読: 「initial uncertainties だけのアンサンブルは underdispersive で reliability を欠く」の逐語あり・「乱数だけでは狭すぎる」に当たる文は無し)/ pymser(BSD-3-Clause・2026-06-26 にアーカイブ=読み取り専用)。**親未確認(△)**: 「最後の 5 バッチを候補にしない」の出所(2011 の本文で見つけていない=2008/2010 の可能性)・SPPT が P−E の偏りを約 10 倍にした節・O'Gara 2025 の数値・HM の本数の表。親の判断は PENDING 仮-24
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 作成 2026-10-15・リサーチ役サブ(Opus 5.5)。子サブは起動していない。Web は読むだけ。論文の PDF は、取得ツール(WebFetch)が自動で残した一時の写しか、標準出力に流した本文を pymupdf で抽出して読んだ(リポの `data/` にも本書の横にも何も置いていない)。GitHub のコードは raw の本文を標準出力で読んだ(clone・install なし)。コミットの固定は §0 の表に書いた。途中で GitHub の API の回数の上限に当たったので、一部のライセンスはファイルの頭書きか DESCRIPTION で確かめた。コミットなし・台帳/設計書/src は未編集。
> 既存答申との関係(重ねない・引く): 共通乱数・対の並べ替え検定・p の下限と対の本数・Holm と BH・効果量・4 つの確認の文献の形・Hoad 2007 の逐次の本数 = [R-71](v2-r71-stochastic-comparison-statistics.md)(A−)/ 反復の本数の 3 系譜・ECMWF のアンサンブルの大きさ・fair CRPS の解析的な補正 = [L-B 反復回数](v2-replication-count-research.md)(A)/ History Matching の位置(代理層が先・1 波 1,000 ラン)・GET・同値検定 = [R-25](v2-statistics-causal-research.md)(B)/ hmer の非含意度の式・SBC = [計器盤と検収](v2-dashboard-verification-orchestration-research.md)(A)/ O'Gara 2025 の数値 = [lit ノート](lit/stats__ogara2025_history-matching-abm.md)(B・親未確認=本書 §3-2 で原典と突き合わせた)/ AgentSociety v1 の介入の型・Concordia の外からの出来事・SocioVerse2 の抄録 = [R-113](v2-r113-e1-foundations-existing-implementations.md) §3(B)/ GA と AgentSociety の計画の階層 = [R-43](v2-r43-code-reading-ga-aitown-humanoid.md)・[R-44](v2-r44-code-reading-concordia-agentsociety-oasis.md)/ STRESS と MultiVeStA の要約(C 等級) = [c10](v2-c10-initial-relations-research.md) §3-3。
> 対象の決定: [指示書 10-12](../design/v2-wallbounce-decisions-2026-10-12.md) §4-5(CP5-1〜CP5-6・CP14・探索と確認・複数ランの作り方)・§1-2・§5 / [要件](../design/v2-requirements.md) の「予測はアンサンブルで」/ [計画](../design/v2-implementation-plan-2026-10-12.md) 3-3 の行と §4 の CP14 の親案 / [3-3 の記録](../bench/analysis/wallbounce-1012/cf33/README.md) / PENDING 仮-20。**決定項は書き換えない。** §4-6 と §6 は親が判断する材料で、未決。
> ライセンスの扱い: GPL・AGPL・研究用だけの許諾のコードは仕組みを書くだけで写さない。Apache-2.0・MIT・BSD は「出典を付けて使える」と書く(使う前にファイルの頭書きを親が確かめる)。

## 結論(7 行)

1. **3-3 の形(申込書・T0 での分岐・4 つの確認・A/A の枝・封印)を一揃いで持つ実装は見つからなかった。** 近い先例は部品ごとにある。前後で同じ乱数を使う MATSim の「quenched」な乱数(Horni ら 2012。全体の乱数列を凍結する方式は「1 本のランで乱数を 1 個余分に引くと、以後の全部の決定の quench が壊れる」と書く)、決定点で走行中のシミュを複製する cloning(Hybinette & Fujimoto 1997)、シナリオを事前に定義して公開リポに置き、複数のモデルで投影する COVID-19 Scenario Modeling Hub(Howerton ら 2023)。LLM 社会シミュ(Generative Agents・Williams 2023・AgentSociety・OASIS)の介入は、初期の記憶やプロンプトの条件と、対照群と処置群の比較だった。A/A の枝と共通乱数の確認を持つものは無かった。Concordia の checkpoint からの再開は、docstring に「モデルを決定論にしない」と書いてある。
2. **予期しない出来事の先例は、反復学習で慣らさない。** MATSim で地下鉄の運休を扱った Müller ら 2020 は、反復学習では「住人が運休を前もって知ってしまう」ので、1 回の反復と途中の再計画で回し、知らせる時刻だけを変えた政策ケースを比べた。v2 の CP5-1(最初からの改変は経験を後で作る)は、住人が始めから知っている改変にだけ当てはまる。
3. **10-12 §1-2 の「ECMWF の教訓」は前半だけ一次確認できた。** ECMWF の論文は「初期の不確かさだけを表すアンサンブルは広がりが足りず、信頼度を欠くと知られている」と書く(Leutbecher ら 2017)。「乱数だけでは狭すぎる」に当たる文は見つけていない。同じ論文は、物理の傾向を確率的に揺らす SPPT が降水と蒸発の収支の偏りを約 10 倍にしたと報告する。v2 で「モデルを揺らす」ときは、保存則の内側で揺らす必要がある。
4. **CP14 の技量スコア(1 − 誤差/基準の誤差)は、Gneiting & Raftery 2007 の式 (8) で最適の点数が 0 の場合に当たる。** 同論文は「この形の技量スコアは、元の点数が proper でも一般に proper でない」と書く。技量スコアと並べて、生の点数(アンサンブルなら fair CRPS)・rank histogram・広がりと誤差の比(√((M+1)/M) の補正つき)を出す形を勧める。
5. **ヒストリーマッチングの本数は、代理モデルを使う先例で 1 波 500〜2,011 本、代理モデル無しの社会 ABM で通し 420〜3,185 本だった**(Andrianakis 2015 の第 4 波以後・Vernon 2014・O'Gara 2025 の 50 点 × 20〜25 本・McCulloch 2022)。v2 の 5,000 体を mock で 1 シム日 約 40 秒(cf33 の 2 日 79.2 秒からの推測)とすると、代理モデル無しで候補 40 個 × 5 本 × 14 日に約 31 時間(直列・推測)。実 LLM では回せない(D-46 の旧見積り 5,000 体 0.5 時間/本)。安い層で回して実 LLM は診断の数本に絞り、層の差を「モデルの食い違い」の分散に入れる形を勧める(推測)。
6. **慣らしは MSER-5 が先例の比較で最も自動化に向くと選ばれ、実装の作法も書かれている**(Hoad ら 2008・Hoad & Robinson 2011: 打ち切り点が後半なら無効として 10% 延長・最後の 5 バッチは候補にしない・複数本を平均してから当てる・累積の系列は使わない・周期のある出力はサイクル単位でまとめる)。v2 は暦と天気が日ごとに変わる系なので、原系列には当てず「差の系列」を 1 シム日ごとにまとめて MSER を当てる手順を提案する(問い 2=改変の枝 − A/A の枝、問い 1=開始日から始めたラン − 前から始めて慣れたラン)。差の系列に当てる形の先例は見つけていない(未リサーチ・expedient)。
7. **比較表は 24 行(§5)。** 写せる(Apache・MIT・BSD)のは pymser(BSD-3)の MSER-m・pymbar(MIT)の平衡の検出・mogp-emulator(MIT)の非含意度・scoringrules(Apache-2.0)の fair CRPS・Concordia(Apache-2.0)の checkpoint ほか。MATSim(GPL-2.0 以上)・OpenABM-Covid19 と CovidSim(GPL-3.0)は読むだけ。MultiVeStA は研究用のバイナリだけの許諾なので、手順を論文から読むだけにする。

## §0 出典の表

等級: **◎** 原典の本文で数値・文を逐語確認(PDF の本文抽出か、コードの raw)/ **○** 原典の本文を読んだが、逐語は取得ツールの抜粋による(親の再取得で ◎ にできる)/ **△** 抄録・二次・検索の要約だけ / **×** 読めなかった・未読(空欄)

| # | 出典 | URL | 等級 | 読んだ範囲 |
|---|---|---|---|---|
| 1 | Franklin W.W. & White K.P. 2008「Stationarity tests and MSER-5: exploring the intuition behind mean-squared-error-reduction in detecting and correcting initialization bias」WSC 2008: 541-546 | https://www.informs-sim.org/wsc08papers/064.pdf | ◎ | 全文(式 1・2・§5.4・結論・文献) |
| 2 | Hoad K., Robinson S., Davies R. 2008「Automating warm-up length estimation」WSC 2008: 532-540(doi 10.1109/WSC.2008.4736110) | https://www.informs-sim.org/wsc08papers/063.pdf | ◎ | 全文(表 1・§3〜§6) |
| 3 | Hoad K. & Robinson S. 2011「Implementing MSER-5 in commercial simulation software and its wider implications」WSC 2011: 495-503 | https://www.informs-sim.org/wsc11papers/044.pdf | ◎ | §1〜§3.4(式・図 2 の手順・図 4 の決定の図・§3.2 の累積の試験) |
| 4 | Sánchez P.J. & White K.P. 2011「Interval estimation using replication/deletion and MSER truncation」WSC 2011 | https://www.informs-sim.org/wsc11papers/043.pdf | ◎ | §1〜§4(MSER の式・複数本の扱い) |
| 5 | Warwick AutoSimOA「warm-up methods」の一覧(2007-11 更新・46 の方法) | https://warwick.ac.uk/fac/soc/wbs/projects/autosimoa/current_work/website_warmup_methods_total_doc.pdf | ◎ | 表 1・Welch・MSER-m・Beck・Tocher の項 |
| 6 | Mahajan P.S. & Ingalls R.G. 2004「Evaluation of methods used to detect warm-up period in steady state simulation」WSC 2004: 663-671 | https://www.informs-sim.org/wsc04papers/080.pdf | ◎ | 抄録・結論 |
| 7 | Taylor S.L. 2010「Analyzing methods of mitigating initialization bias in transportation simulation models」修士論文(Georgia Tech) | https://www.nctspm.gatech.edu/sites/default/files/u46/taylor_stephen_l_201012_mast_Analyzing%20methods%20of%20mitigating%20initialization%20bias%20in%20transportation%20simulation%20models.pdf | ◎ | 要旨・§4.2・§5 の冒頭 |
| 8 | Vandin A., Giachini D., Lamperti F., Chiaromonte F.「Automated and distributed statistical analysis of economic agent-based models」arXiv:2102.05405 v2(JEDC 2022, doi 10.1016/j.jedc.2022.104458) | https://arxiv.org/abs/2102.05405 | ◎ | 抄録・§3.2(Algorithm 2〜5)・脚注 5 |
| 9 | Taylor S.J.E. ほか 2018「Applying the STRESS guidelines for reproducibility in modeling & simulation」WSC 2018(STRESS-ABS の表を再掲) | https://www.informs-sim.org/wsc18papers/includes/files/061.pdf | ◎ | 表 4(項目 4.1〜4.3) |
| 10 | White K.P. 1997「An effective truncation heuristic for bias reduction in simulation output」Simulation 69(6):323-334 | https://doi.org/10.1177/003754979706900601 | △ | 書誌と #3 の逐語の引用だけ |
| 11 | White K.P., Cobb M.J., Spratt S.C. 2000「A comparison of five steady-state truncation heuristics for simulation」WSC 2000: 755-760 | https://www.informs-sim.org/wsc00papers/abstracts/an2.htm | △ | 抄録(検索の要約経由) |
| 12 | Hoad K., Robinson S., Davies R. 2010「Automating warm-up length estimation」JORS 61(9):1389-1403 | https://doi.org/10.1057/jors.2009.87 | △ | 書誌と抄録(本文の写しは 403) |
| 13 | Schruben L.W. 1982「Detecting initialization bias in simulation output」Operations Research 30(3):569-590 | https://doi.org/10.1287/opre.30.3.569 | △ | IDEAS の抄録の要約 |
| 14 | Monks T. ほか「Strengthening the reporting of empirical simulation studies: introducing the STRESS guidelines」J. of Simulation 13(1):55-67 | https://doi.org/10.1080/17477778.2018.1442155 | × | 本文は 403。項目は #9 で確認 |
| 15 | Welch P.D. 1983「The statistical analysis of simulation results」(The Computer Performance Modeling Handbook) | なし | × | 原典未読。手順は #5 の要約だけ |
| 16 | Chodera J.D. 2016「A simple method for automated equilibration detection in molecular simulations」(bioRxiv 021659) | https://www.biorxiv.org/content/10.1101/021659v1 | ○ | 抄録 |
| 17 | Oliveira F.L. ほか 2024「pyMSER - An open-source library for automatic equilibration detection in molecular simulations」JCTC 20(19):8559-8568 | https://doi.org/10.1021/acs.jctc.4c00417 | △ | README の書誌だけ |
| 18 | Horni A., Nagel K., Axhausen K.W. 2012「High-resolution destination choice in agent-based demand models」VSP 作業論文 12-07(TU Berlin) | https://svn.vsp.tu-berlin.de/repos/public-svn/publications/vspwp/2012/12-07/2012-02-06-HorniNagelAxhausen.pdf | ◎ | §1.3.2・§1.4 |
| 19 | MATSim 利用者の手引き「Terminology」 | https://matsim.org/docs/userguide/terminology | ○ | relaxed/stationary・ExpBetaPlanSelector の項 |
| 20 | Müller S.A., Leich G., Nagel K. 2020「The effect of unexpected disruptions and information times on public transport passengers: a simulation study」Procedia Computer Science 170:745-750(CC BY-NC-ND 4.0) | https://depositonce.tu-berlin.de/items/e603847b-87f5-4bcd-99aa-ed332d1d29b5/full | ◎ | 抄録・§2・§3 |
| 21 | Hybinette M. & Fujimoto R. 1997「Cloning: a novel method for interactive parallel simulation」WSC 1997 | https://www.informs-sim.org/wsc97papers/0444.PDF | ◎ | 抄録・§1 |
| 22 | Hybinette M. & Fujimoto R. 2001「Cloning parallel simulations」ACM TOMACS 11(4):378-407 | https://doi.org/10.1145/508366.508370 | △ | 書誌と講演の抄録(検索経由) |
| 23 | Kerr C.C. ほか 2021「Covasim: an agent-based model of COVID-19 dynamics and interventions」PLoS Comput Biol 17(7):e1009149 | https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1009149 | ○ | 介入・複数ラン・較正・ライセンスの節 |
| 24 | Williams R. ほか 2023「Epidemic modeling with generative agents」arXiv:2307.04986 v1 | https://arxiv.org/abs/2307.04986 | ◎ | 方法・結果・補足の該当部分 |
| 25 | Park J.S. ほか 2023「Generative agents: interactive simulacra of human behavior」arXiv:2304.03442 | https://arxiv.org/abs/2304.03442 | ◎ | §3.1・§7.1 |
| 26 | Piao J. ほか 2025「AgentSociety: large-scale simulation of LLM-driven generative agents…」arXiv:2502.08691 | https://arxiv.org/abs/2502.08691 | ◎ | §7(分極・扇動的な投稿・UBI・ハリケーン)の該当部分 |
| 27 | Yang Z. ほか 2024「OASIS: open agent social interaction simulations with one million agents」arXiv:2411.11581 | https://arxiv.org/abs/2411.11581 | ◎ | §3.2・付録 F の繰り返し |
| 28 | Zhang X. ほか 2026「SocioVerse2」arXiv:2609.24911 v1 | https://arxiv.org/abs/2609.24911 | ○ | 抄録 |
| 29 | Klein D.J. ほか 2024「Noise-free comparison of stochastic agent-based simulations using common random numbers」arXiv:2409.02086 v2 | https://arxiv.org/abs/2409.02086 | ○ | 抄録(R-71 #4 と同じ) |
| 30 | Leutbecher M. ほか 2017「Stochastic representations of model uncertainties at ECMWF: state of the art and future vision」QJRMS(受理稿・doi 10.1002/qj.3094) | https://www.ecmwf.int/sites/default/files/medialibrary/2017-10/qj3094_accepted.pdf | ◎ | 要旨・§1・§2.1・§4.1・§4.3・§7.1 |
| 31 | Buizza R., Miller M., Palmer T.N. 1999「Stochastic representation of model uncertainties in the ECMWF ensemble prediction system」QJRMS 125:2887-2908 | https://www.ecmwf.int/en/elibrary/8451-stochastic-representation-model-uncertainties-ecmwf-ensemble-prediction-system | △ | 書誌と #30 の引用だけ |
| 32 | Gneiting T. & Raftery A.E. 2007「Strictly proper scoring rules, prediction, and estimation」JASA 102(477):359-(doi 10.1198/016214506000001437) | https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf | ◎ | §2.3(式 8)・§4.2(CRPS) |
| 33 | Hamill T.M. 2001「Interpretation of rank histograms for verifying ensemble forecasts」MWR 129:550-560 | https://ckanprod.data-commons.k8s.ucar.edu/dataset/interpretation-of-rank-histograms-for-verifying-ensemble-forecasts | ○ | 抄録(UCAR の記録) |
| 34 | Fortin V. ほか 2014「Why should ensemble spread match the RMSE of the ensemble mean?」J. Hydrometeorology 15(4):1708-1713 | なし | △ | #35 の引用(式 15)だけ |
| 35 | Price I. ほか「GenCast: diffusion-based ensemble forecasting for medium-range weather」arXiv:2312.15796 | https://arxiv.org/abs/2312.15796 | ◎ | 付録 E.2.2・E.2.3 |
| 36 | Koehler E., Brown E., Haneuse S. 2009「On the assessment of Monte Carlo error in simulation-based statistical analyses」Am. Stat. 63(2):155-162 | https://pmc.ncbi.nlm.nih.gov/articles/PMC3337209/ | ○ | §2.1・§4(式 7〜10) |
| 37 | Howerton E. ほか 2023「Evaluation of the US COVID-19 Scenario Modeling Hub for informing pandemic response under uncertainty」Nat. Commun. 14:7260 | https://pmc.ncbi.nlm.nih.gov/articles/PMC10661184 | ○ | 方法と結果の該当部分 |
| 38 | Hawkins E. & Sutton R. 2009「The potential to narrow uncertainty in regional climate predictions」BAMS 90(8):1095-1107 | https://doi.org/10.1175/2009BAMS2607.1 | △ | 検索の要約だけ(大学の記録は取得の防御で読めず) |
| 39 | Haber S. & Stornetta W.S. 1991「How to time-stamp a digital document」J. Cryptology 3(2):99-111 | https://doi.org/10.1007/BF00196791 | △ | 検索の要約だけ |
| 40 | Cox D.R. 1975「A note on data-splitting for the evaluation of significance levels」Biometrika 62(2):441-444 | https://doi.org/10.1093/biomet/62.2.441 | △ | 検索の要約(Vovk arXiv:2008.11474 の紹介)だけ |
| 41 | Wagenmakers E.-J. ほか 2012「An agenda for purely confirmatory research」Perspect. Psychol. Sci. 7(6):632-638 | https://doi.org/10.1177/1745691612463078 | × | 403 |
| 42 | Vernon I., Goldstein M., Bower R.G. 2010「Galaxy formation: a Bayesian uncertainty analysis」Bayesian Analysis 5(4):619-670 | https://doi.org/10.1214/10-BA524 | △ | 書誌と抄録の要約(出版社の頁は取得の防御で読めず) |
| 43 | Vernon I., Goldstein M., Bower R.G. 2014「Galaxy formation: Bayesian history matching for the observable universe」Statistical Science 29(1):81-90(arXiv:1405.4976) | https://arxiv.org/abs/1405.4976 | ◎ | §3・§4(式 6・表 2) |
| 44 | Andrianakis I. ほか 2015「Bayesian history matching of complex infectious disease models using emulation: a tutorial and a case study on HIV in Uganda」PLoS Comput Biol 11(1):e1003968(CC BY 4.0) | https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003968 | ○ | 方法と結果の該当部分(一部の数値は画像で読めず) |
| 45 | O'Gara D. ほか 2025「Improving policy-oriented agent-based modeling with history matching: a case study」arXiv:2501.00616 | https://arxiv.org/abs/2501.00616 | ◎ | 手法の節・表 1 |
| 46 | McCulloch J. ほか 2022「Calibrating agent-based models using uncertainty quantification methods」JASSS 25(2):1 | https://www.jasss.org/25/2/1.html | ○ | 方法・3 つの例・結論 |
| 47 | Malleson N. ほか 2020「Simulating crowds in real time with agent-based modelling and a particle filter」JASSS 23(3):3 | https://www.jasss.org/23/3/3.html | ○ | 方法・結果・限界 |
| 48 | Pukelsheim F. 1994「The three sigma rule」Am. Stat. 48(2):88-91 | なし | △ | #45 の引用文だけ |
| 49 | McKinley T.J. ほか 2018「Approximate Bayesian computation and simulation-based inference for complex stochastic epidemic models」Statistical Science 33(1):4-18 | なし | × | 未読 |
| 50 | Concordia `concordia/prefabs/simulation/generic.py`(commit `c18c968a653202b1291ae3c3322082588c5440f7`・Apache-2.0) | https://github.com/google-deepmind/concordia | ◎ | L586-640(`save_checkpoint`・`load_from_checkpoint`) |
| 51 | pymser `src/pymser/pymser.py`(commit `797a8ed33450ed9c97e4b981a0549743e3cf66f4`・BSD-3-Clause・2026-06 から読み取り専用の保管) | https://github.com/IBM/pymser | ◎ | L70-204・L574-600 |
| 52 | pymbar `pymbar/timeseries.py`(commit `ed40ec3bbef03bb08938ad1a74d459b0d1ab81f7`・MIT) | https://github.com/choderalab/pymbar | ◎ | L771-836(`detect_equilibration`) |
| 53 | mogp-emulator `mogp_emulator/HistoryMatching.py`(main・MIT) | https://github.com/alan-turing-institute/mogp-emulator | ◎ | クラスの docstring・`__init__`・`get_implausibility` の引数 |
| 54 | hmer の DESCRIPTION(master・版 1.6.2・MIT + file LICENSE)と hubEnsembles の DESCRIPTION(main・MIT + file LICENSE) | https://github.com/andy-iskauskas/hmer ・ https://github.com/hubverse-org/hubEnsembles | ◎ | Title・Version・License の行 |
| 55 | MultiVeStA の license フォルダ(Research Use Binary License 1.0) | https://github.com/andrea-vandin/MultiVeStA | ◎ | License.html の §1・§2 |
| 56 | scoringrules `scoringrules/_crps.py`(main・Apache-2.0) | https://github.com/frazane/scoringrules | ◎ | `crps_ensemble` の引数と docstring |
| 57 | scores の rank histogram の手引き | https://scores.readthedocs.io/en/stable/tutorials/Rank_Histogram.html | ○ | 関数名・Hamill の引用 |
| 58 | MATSim の Java の頭書き(`matsim/src/main/java/org/matsim/core/controler/Controler.java`・main) | https://github.com/matsim-org/matsim-libs | ◎ | L1-17(GPL-2.0 以上) |
| 59 | GitHub API のライセンス欄(AgentSociety・OASIS・generative_agents・Concordia・starsim・covasim・OpenABM-Covid19・covid-sim・xskillscore・properscoring・Urban-Analytics/uncertainty・Urban-Analytics/dust・mogp-emulator・EMAworkbench) | https://api.github.com/repos/ | ◎ | `license.spdx_id` の値(2026-10-15) |
| 60 | Java Modelling Tools(JMT)の MSER-5 の実装とライセンス | なし | × | #4 が「MSER-5 を初期化の方法に選んだ」と書くことだけ確認 |

数: ◎ 30・○ 12・△ 13・× 5(計 60)。

### §0-2 既存答申との重なり(CLAUDE.md §2-4 の確認)

| 既存答申 | 既にカバーしていること | 本書で足すこと |
|---|---|---|
| [R-71](v2-r71-stochastic-comparison-statistics.md) | CRN の式と同期・カウンタ型の乱数・LLM の推論の非決定・4 つの確認の文献の形・対の符号反転の p の下限(両側 6 対)・Holm/BH・Hoad 2007 の逐次の本数・Klein 2024 | 反実仮想の器の先例(MATSim の政策ケースと quenched・cloning・Concordia の checkpoint・LLM 社会シミュの介入の作り方)・Koehler 2009 の MC 誤差 |
| [L-B 反復回数](v2-replication-count-research.md) | Lee・Siepe・ten Broeke・Ritter・Secchi & Seri・ECMWF の 51 本と fair CRPS の補正 | ECMWF の「初期だけでは広がりが足りない」の一次の文・SPPT が収支を崩した報告・評価の器(rank histogram・spread/skill・技量スコアの proper でない注意) |
| [R-25](v2-statistics-causal-research.md) §1-3(c)・S2-d | History Matching の位置(代理層の後)・1 波 50 点 × 20 本 | Vernon の波の実数・Andrianakis と McCulloch の本数・代理モデル無しの直接の HM・v2 の費用の見積り(推測) |
| [計器盤と検収](v2-dashboard-verification-orchestration-research.md) | hmer の非含意度の式・I ≤ 3・SBC | mogp-emulator(Python・MIT)の既定(閾値 3・2 番目の大きさ) |
| [c10](v2-c10-initial-relations-research.md) §3-3 | STRESS と MultiVeStA の要約(C 等級) | 両方の原典(STRESS-ABS 4.1 の文・MultiVeStA の Algorithm 3 と許諾)・MSER-5 の原典群 |
| [R-113](v2-r113-e1-foundations-existing-implementations.md) §3 | AgentSociety v1 の介入の型・Concordia の `__external__`・SocioVerse2 の抄録(介入で枝を分ける) | Concordia の checkpoint の docstring・SocioVerse2 の「時点を保証した外部データ」 |

**写し検査(O'Gara 2025)**: lit ノートの「第 1 波 50 点 × 25 本・以後 50 点 × 20 本・閾値 3.0/3.0/2.7/2.5・NROY 7.23% → 5.58% → 2.14% → 0.82%・40⁴ の格子で約 2.5 年」を原典の PDF の本文で突き合わせ、全部一致した(#45)。R-25 S2-d の「1 波 = 50 設計点 × 20 反復 = 1,000 ラン」も第 2 波以後の値と一致する。

## §1 反実仮想と介入の先例

### 1-1 同じ出発点からの差(共通乱数・分岐点 T での切り替え)

- **MATSim の quenched な乱数**(#18 ◎): 2 つの方式を挙げる。(a)「Freezing the applied global sequence of random numbers, meaning that a Monte Carlo method with the same random seed is used before and after the introduction of a policy measure」、そうすれば「Differences in the outcome can thus be directly attributed to the policy measure」。(b) 人と選択肢の組ごとに誤差項を計算して保存する。(a) の弱点を「one additional random number, drawn in one run but not in the other, completely destroys the "quench" for all decisions computed later in the program」と書き、(b) は 10⁶ 人 × 10⁶ 選択肢で 4 TB になると見積もる。AMOS・Albatross・NYC・Tel Aviv・Sacramento/Portland の活動モデルの多くは (a) だった(著者への聞き取り)。v2 の「用途の鍵 × カウンタ」の乱数(R-71 §1-4)は、(b) を保存せずに計算で作る形に当たる(本書の読み)。
- **MATSim の政策の比較の現状**(#19 ○): 用語の頁は「In theory, one should have unbiased samples before and after the introduction of the policy, but at this point this is not implemented and it is also computationally considerably more expensive than what is done now」と書く。また「innovation」(新しい経路や時刻を作る)を止めない限り「the result is not truly stationary」とする。基準と政策の比較は、1 本ずつの緩和した状態どうしで行っているのが標準と読める(推測)。
- **cloning**(#21 ◎・#22 △): 「Potential branches or choices can be specified interactively and interjected into the on-going simulation as decision points. Once a decision point is defined, different "futures" are computed by cloning the simulation」。複製の間で共通の計算を繰り返さないために「virtual logical processes」を置く。v2 の分岐は、走行中の状態を複製する代わりに「日の境目の状態+T までテープの再生」で同じ前半を作り直す(CP5-2)。前半を共有する目的は同じで、作り方が違う。
- **Concordia の checkpoint**(#50 ◎): `save_checkpoint` は段ごとに全員の状態を JSON に書き、`load_from_checkpoint` は深い写しから戻す。docstring は「This does not restore engine cursors or make arbitrary components, shared external services or models deterministic」と書く。分岐の口はあるが、T までの一致を確かめる仕組みは無い。v2 の (b)(T0 より前の全 checkpoint の一致)とテープの再生はこの欠けを埋める形で、先例より厳しい。
- **ABM の CRN**: Klein ら 2024(#29 ○)は「eliminates noise due to misaligned random numbers, a first for agent-based modeling」と書き、必要な本数が 10 倍超減った例を報告する。詳細は R-71 §1 にあり、ここでは繰り返さない。

### 1-2 A/A の枝(介入なしの 2 本の差=ばらつきの床)

- 3-3 の (d) は「A/A の枝 2 本と基準が厳密に同じ」を確かめる(決定論の確認)。先例で同じ確認を持つものは見つからなかった。
- 床としての A/A に近いのは次の 3 つ。ECMWF は物理の揺らしの効果を「initial perturbations only (IP only)」の実験と比べ、46 事例 × 20 メンバーで対の t 検定の 95% 区間を出す(#30 ◎)。OASIS は 2 つの話題でシミュを 10 回ずつ繰り返し、雑音の投稿がある話題では広がりの曲線が分かれたと報告する(#27 ◎)。Covasim は複数本の 10〜90 パーセンタイルを既定の幅にする(#23 ○)。
- **v2 への読み(推測)**: 実 LLM の艦隊で T0 から回すと、A/A の枝はバッチの組み方で基準と一致しなくなる(R-71 §1-5)。そのとき (d) は「決定論の確認」(mock・古典・テープ)と「床の分布」(実 LLM の A/A の対の差)の 2 つに分ける必要がある(§6-2)。

### 1-3 介入の「申込書」に当たるもの

| 先例 | 介入の書き方 | いつ・誰が実行するか | 比べ方 | 出典 |
|---|---|---|---|---|
| MATSim(Müller ら 2020) | 基準ケース(運休なし)と政策ケース(U9 を 07:30〜08:30 に両方向で運休)。政策ケースどうしは「乗客に知らせる時刻」だけが違う(運休の前の 06:30〜07:20 を含む) | エンジンが運休を当て、知らせる時刻に住人が途中で再計画する。全員が同時に知る仮定 | 基準と比べて移動時間が増えた住人(1,408 体=10% 標本で 14,080 人)だけを集計 | #20 ◎ |
| Covasim | 「interventions are modeled as changes to parameter values」。開始日つきの β の減少・検査数・接触の追跡。自作の介入は関数で書ける | エンジンが日付で当てる | 複数ランの区間。シナリオを並列に回して比べる | #23 ○ |
| COVID-19 Scenario Modeling Hub | 主催が公衆衛生の相手から問いを受けて設計し、2 × 2 の表の 4 シナリオ(NPI・接種・変異株の性質ほか)を投影の約 1 か月前に決める。仕様は公開の GitHub に置き、各チームが同じリポに投影を出す | 各チームが自分のモデルで独立に実行 | trimmed-LOP のアンサンブル・WIS と予測区間の被覆率・素朴なモデルとの比較。現実に近かったシナリオの週(292 週=31%)だけを評価 | #37 ○ |
| AgentSociety | 対照群(介入なし)と処置群(同質の相手とだけ話す/異質な相手と話す・扇動的な投稿を置く・アカウントの停止や辺の削除)。v1 のコードでは workflow の型(環境・状態の直接の書き換え・メッセージ・任意の関数)=R-113 §3 | エンジンと LLM | 群どうしの割合の比較。本文に乱数の種の記述は見つからなかった | #26 ◎ |
| OASIS | Muchnik 2013 の野外実験に合わせ、最初に「いいね」1 つ・「よくないね」1 つ・何もなしの 3 群に投稿を分ける | エンジン | 群の平均点と 95% 区間。人の実験の値と並べる | #27 ◎ |
| Generative Agents | 選挙の立候補とパーティーの情報を、初期化の時に 1 人の記憶に入れる。「内なる声」で本人に指示もできる | 本人の記憶と会話 | 2 日後に 25 体へ面接し、知っている割合(4% → 32%・4% → 52%)。繰り返しの本数の記述は読んだ範囲に無い | #25 ◎ |
| Williams ら 2023 | プロンプトの「関連する記憶」を実験条件で変える(体調の知らせ・町の感染の割合を新聞で知る)。ウイルスと町には架空の名(Catasat・Dewberry Hollow)を使い「to avoid any unknown biases in LLM」 | LLM が外出するかを決め、ABM が感染を進める | 100 体で 3 条件 × 10 本(1 本 約 2 時間)・1,000 体で 7 本(1 本 約 80 時間) | #24 ◎ |
| SocioVerse2 | 「forks counterfactual branches via interventions」・研究そのものを版で管理・21 の実データの源を「point-in-time guarantees」つきで供給 | 不明(抄録だけ) | 不明 | #28 ○ |

- **3-3 との差(先例に無いもの)**: (1) 申込書に「問い」と「主の指標 1 つ」を持たせる先例は見つからなかった(SMH は評価の物差しを hub 全体で決めている)。(2) 全部の先例で、介入はエンジンが実行するか、本人の記憶やプロンプトに直接入る。「決定だけを入れ、準備と実行は世界の中の人がする」(CP6)の先例は見つからなかった(未確認=探した範囲は本表の 8 件)。(3) 知らせる時刻を介入の欄として持つのは Müller ら 2020 だけで、v2 の「告知」(CP5-4)に当たる。
- **CP5-3 との対応**: Williams は名前の偏りを避けるために架空の名を使った。v2 の CP5-3(ペルソナの文が改変した物を名指ししていないか機械で探す)と同じ向きの用心である。SocioVerse2 は外部データに時点の保証を付け、モデルの知識の切れ目より後の予測を検証に使っている(抄録)。v2 のパターン台帳の運用規則 9(混入の疑い)と同じ向きである。

### 1-4 効果の推定と検定(本数・対の差・多重比較)

- 本数・対の差の分布・符号反転の検定・Holm/BH は R-71 §2〜§6 のとおり(両側 6 対・向きを事前登録した片側 5 対)。本書では繰り返さない。
- **MC 誤差の報告**(#36 ○): Koehler ら 2009 は MC 誤差を「the standard deviation of the Monte Carlo estimator, taken across hypothetical repetitions of the simulation」と定義し、平均の形の量なら σ̂/√R で推定する。必要な本数は、試しの本数の部分集合ごとに MC 誤差を測り、1/√R に原点を通る回帰をかけて傾き β̂ を得て、R = (β̂/目標の MC 誤差)² で決める(式 10)。論文の例では、割合の偏りを ±1 の幅に収めるのに 10,000 本超、被覆率に約 2,500 本が要った。v2 で主に使うのは R-71 §5-4 の「対の差の SD から決める」形で、Koehler の式は「その本数で MC 誤差がいくらか」を manifest に書く欄として足せる(推測)。
- **事例をまたぐ対の比較**(#30 ◎): ECMWF の研究開発は、低い解像度・20 メンバー・46 事例で費用を約 1/25 にし、対の t 検定で差の 95% 区間を出す。v2 の「5,000 体の安い階層で本数を確保する」(D-46 (a)・R-71 §8-3)と同じ考え方の先例である。

### 1-5 3-3 の形との対応と差(まとめ)

| 3-3 の要素 | 近い先例 | 同じ点 | 違う点 |
|---|---|---|---|
| 申込書(種類・対象・中身・始まり・終わり・告知・問い・比べる指標) | SMH のシナリオの仕様・Covasim の介入・AgentSociety v1 の workflow・Müller の政策ケース | 介入を事前に欄で固定し、始まりの時刻を持つ | 問いと主指標を申込書に持つ例は無い。実行はどれもエンジンか本人の頭の中 |
| T0 での分岐(テープの再生) | cloning・Concordia の checkpoint・MATSim の途中の再計画 | 前半を共有して後半だけ違える | 先例は前半を複製するか、決定論を保証しない。テープで作り直して確かめる例は無い |
| 4 つの確認 (a)〜(d) | MATSim の quenched(入力の一致)・R-71 §1-6 の Fiedler と Petrov(状態のハッシュ・最初の食い違い) | 同じ種で前後を比べる | 4 つを毎回の分岐で自動で走らせる例は無い |
| A/A の枝 | ECMWF の IP only・OASIS の繰り返し・Covasim の区間 | 介入なしの揺らぎを床として測る | 「厳密に同じ」を確かめる決定論の A/A は v2 だけ |
| 封印(探索と確認・単位は初期状態) | Cox 1975 の分割(探してから別の半分で検定)・SMH の事前の公開 | 仮説を作るデータと確かめるデータを分ける | 分割の単位を「初期状態」に決めた例は無い(cf33 の親の判断 M2) |
| 事前登録の指紋(sha256 と blake3) | SMH の公開リポ・Haber & Stornetta 1991 のハッシュの時刻印 | 予測の中身を先に固定する | §2-4 |
| 技量スコア | Gneiting & Raftery の式 (8)・SMH の素朴なモデル | 単純な基準との比 | §2-3 |

## §2 アンサンブル

### 2-1 揺らす源(初期状態・モデル・偶然)

- **ECMWF**(#30 ◎): 初期の摂動はアンサンブル同化(EDA)と特異ベクトルから作る(§7.1)。モデルの不確かさは SPPT(物理の傾向を p = (1 + μr)p_D の形で揺らす)と SKEB(2010-11 から)で表す。要旨は「The inclusion of stochastic schemes to represent model uncertainties has improved the probabilistic skill of the ECMWF ensemble by increasing reliability and reducing the error of the ensemble mean」。§1 は「An ensemble that represents only initial uncertainties consistent with the true distribution of initial condition errors is known to be underdispersive and therefore will lack reliability (e.g. Wilks 2005; Palmer et al. 2005)」と書く。
  - **10-12 §1-2 の写し検査**: 「初期状態だけでは狭すぎる」は上の文で支持される(◎)。「乱数だけでは狭すぎる」に当たる文は本書の範囲では見つけていない(ECMWF の運用は常に初期の摂動を含むため、比べる実験が無い)。親が設計書の注の文を直すかを判断する(§6-1)。
  - **保存則への注意**(◎): SPPT は大気の湿りを系統的に減らし、10 年平均で降水 − 蒸発の偏りを −0.016 から −0.16 mm/日に広げた(30 日予報でも 0.03 から −0.15)。v2 の「モデルを揺らす」(判断モデルや LLM の札を替える・expedient の値を揺らす)は、お金と物の保存則(CLAUDE.md §4)を内側で守る形でなければならない。揺らしの腕ごとに締めの検算を回すことを勧める(推測)。
- **複数のモデル**(#37 ○): SMH は 4〜9 チームのモデルを 1 回ごとに集め、最高と最低を除いて平均する trimmed-LOP をアンサンブルとした。アンサンブルの 95% 区間の被覆は約 78〜80%、個々のモデルの中央値は約 40〜42% だった。モデルの違いを残す集め方が単独のモデルより信頼できたと報告する。v2 の「モデル」の軸(札=mock・古典・判断モデル・LLM)の集め方の先例になる。
- **データと矛盾しない初期状態を何通りか**(#23 ○・#45 ◎): Covasim の事例は較正した 8 組のパラメタを使った。O'Gara は HM で残った領域から試料を引き、ABC の事前分布に使った。v2 の「初期状態 × モデル × 偶然」の「初期状態」を HM の残りから引く形は、この 2 つと同じ向きである(§3)。
- **源ごとの分解**: 気候の予測で、内部変動・モデル・シナリオの 3 つに不確かさを分ける Hawkins & Sutton 2009 が定番(#38 △・本文未読)。v2 の 10-12 の「揺らしの源ごとに分布の幅を分解して報告」は、初期状態 × モデル × 偶然の釣り合った格子(各組に偶然を複数本)で、偶然の分散(組の中)・初期状態の分散・モデルの分散を分散成分として推定する形が素直(具体の推定式は未リサーチ・expedient)。

### 2-2 本数の決め方

- 対の差で言う本数は R-71 §5-4(パイロット 5 本以上・対の差の SD・下限 6 対)、水準の本数と fair CRPS は L-B のとおり。ECMWF の研究開発は 20 メンバー × 46 事例(#30 ◎)、Covasim の既定の区間は 10〜90 パーセンタイル(#23 ○)。
- MC 誤差の報告(Koehler の式 7 と式 10)を manifest に足す案は §1-4 のとおり(推測)。
- 探索と確認で初期状態を半分ずつに分けるので、確認の半分に「6 対以上」を確保するには、初期状態の数 × 偶然の本数を倍で用意することになる(cf33 §5 の封印の形からの算術)。

### 2-3 分布の評価(CRPS・rank histogram・spread/skill・技量スコア)

- **CRPS**(#32 ◎): CRPS(F, x) = −∫(F(y) − 1{y ≥ x})² dy(式 20・正の向き)。負の向きで使えば観測と同じ単位になり、点の予測なら絶対誤差に一致する(「it generalizes the absolute error to which it reduces if F is a deterministic forecast」)。そのため、アンサンブルの CRPS と点の基準(去年の同じ日・平均・前の週)の絶対誤差をそのまま比べられる。有限メンバーの偏りの補正(fair CRPS)は L-B と scoringrules の `estimator="fair"`(#56 ◎)。
- **rank histogram**(#33 ○): 平らな形は信頼度の必要条件で十分条件ではない(「a flat rank histogram, usually taken as a sign of reliability, can still be generated from unreliable ensembles」)。U 字は広がり不足のほか条件つきの偏りでも出る。検定するなら、標本は時刻と場所で独立とみなせるほど離す。v2 では、時刻別の滞在人口のような指標で 15 分ごとの標本は独立でないので、日や区域でまとめてから描く必要がある(推測)。
- **広がりと誤差の比**(#35 ◎・#34 △): メンバーと観測が交換可能なら Skill ≈ √((M+1)/M)·Spread(Fortin ら 2014 の式 15。広がりは 1/(M−1) の分散の平均の平方根)。比が 1 より小さければ広がり不足。
- **技量スコア**(#32 ◎): 式 (8) S_skill = (S_fcst − S_ref)/(S_opt − S_ref)。誤差(負の向き・最適 0)では 1 − 誤差/基準の誤差で、CP14 の親案と一致する。基準は「typically a climatological forecast」。ただし「Unfortunately, skill scores of the form (8) are generally improper, even if the underlying scoring rule S is proper」。**v2 への案**: 技量スコアは器のまま(cf33 §5)とし、生の点数と基準の生の点数を同じ記録に並べる。複数の予測の優劣は生の点数で決める(mechanism=原典の注意)。
- **基準の作り方の先例**(#37 ○): SMH の素朴なモデルは「cases will remain at current levels for the entire projection period with historical variance」で、Forecast Hub と同じ比較相手を使った。v2 の「前の週」を点ではなく過去のばらつきつきの分布にすれば、CRPS で比べられる(推測)。

### 2-4 封印の形式(事前登録・ハッシュの公開)

- **SMH**(#37 ○): 最終の仕様を公開の GitHub に置き、各チームが同じリポに投影を出した。仕様の確定から公開まで平均 5 週間(2〜10 週)。評価で「現実に近かったシナリオ」を後から選ぶと結果が予測の側に有利に傾きうる、と自ら注意している。v2 の CP14 は「外れも同じ場所に書く」なので、どのシナリオを評価するかの規則も封印の束に入れる必要がある(推測)。
- **ハッシュの時刻印**(#39 △): Haber & Stornetta 1991 は、文書そのもののハッシュに時刻を付け、利用者が日付を前にも後にもずらせない手順を示した(要約経由)。v2 の「blake3 と sha256 を `docs/predictions/` に置き、git の履歴を証拠にする」は同じ考え方だが、手元の git のコミットの時刻は書き換えられる。外の時刻の証拠(公開リポへの push の記録や第三者の時刻印)をどうするかは未リサーチ(§6-7)。
- **探索と確認の分割**(#40 △): Cox 1975 は、データを 2 つに分け、片方で仮説(検定の統計量)を選び、もう片方で検定する手順の効率を約 80% と見積もった(二次の紹介経由)。cf33 の封印は「初期状態の正準の JSON の sha256 の順で先頭の半分」で、乱数で分ける代わりに再現できる順で分けている。分けた後で探索の側が確認の側を覗けない仕組み(ランの入口の検査)を持つのは v2 の独自の構成である。

## §3 ヒストリーマッチング(較正)

### 3-1 Vernon・Goldstein・Bower の手順

- 定義(#43 ◎): 観測 z と系の真の値 y を z = y + e、モデルの食い違いを ε とし、代理モデル(emulator)の平均と分散から非含意度 I²(x) = |z − E(f(x))|² / [Var(f(x)) + Var(ε) + Var(e)](式 6)を出す。出力が複数なら I_M(x) = max I(x) などで束ね、大きい領域を除いて「nonimplausible」な領域にランを足し、代理モデルを作り直して繰り返す。残りが空なら「a strong warning of problems with our simulator or with our data」。
- 較正との違い(#43 ◎): 「History matching may be compared with model calibration which aims to identify the one "true" value of the input parameters」。真の値が 1 つと信じないか、良い入力が存在するか分からないときに HM を使う。「it is often good practice to history match first」。
- 波の実数(#43 ◎・表 2): 17 入力の Galform で、1 波のラン 993 → 1,414 → 1,620 → 2,011 → 2,000、閾値は I_2M 2.7・I_3M 2.3(第 4 波から I_M 3.2、第 5 波 2.5)、残った割合 14.9% → 5.9% → 1.6% → 0.26% → 0.039%。各波で代理モデルの点検に 200 本の診断のランを回した。2010 年の原典(#42)は本文を読めていない(△)。
- 閾値 3 の由来(#45 ◎): 「A common cutoff value I(θ) is 3, inspired from (Pukelsheim 1994) showing that at least 95% of any continuous unimodal distribution is contained within three standard deviations」(#48 は △)。

### 3-2 ABM への適用

| 先例 | モデル | 入力・出力 | 波と本数 | 確率的なモデルの扱い | 出典 |
|---|---|---|---|---|---|
| Andrianakis ら 2015 | ウガンダの HIV の個体ベースのモデル(1 本 10 分〜3 時間・240 ノード) | 22 入力・18 出力 | 9 波(+第 10 波 500 本)。第 1 波 220 点の maximin LHS(+検証用 20 点)、第 4 波から 1 波 500 本。最初の 3 波は I_M ≤ 3、以後は 3 つの判定 | 出力ごとに平均の代理モデルを作り、ばらつきを「Ensemble Variability」の項として分母に足す。最後の領域で 18 出力すべてに合う確率 65% | #44 ○ |
| O'Gara ら 2025 | Covasim(シアトル都市圏・1 本 約 30 秒) | 4 入力 | 第 1 波 50 点 × 25 本、以後 50 点 × 20 本。閾値 3.0/3.0/2.7/2.5・NROY 7.23% → 0.82% | 反復で平均と分散を分けて推定する異分散のガウス過程。「model replicates are essential to separate signal from noise」 | #45 ◎ |
| McCulloch ら 2022 | Sugarscape・鳥の移動・スコットランドの農家の意思決定(RISC) | 2〜数入力 | Sugarscape 10 波・他は 3 波。代理モデルを作らず LHS で直接回す。HM だけで 420 本、HM+ABC で 3,185 本(ABC だけの先行研究は 11,000 本超)。RISC は 1,600 本。各点の繰り返し 200/30/100 本 | 分母に観測・シミュ・モデルの 3 つの分散。ABC の閾値も ε = 3(V_o + V_s + V_m) | #46 ○ |

- **MATSim・交通のシミュの HM の先例**は本書では見つけていない(未リサーチ)。

### 3-3 ABC・ベイズ較正・データ同化との違い

- HM は「合わない領域を除く」、ABC は事後分布を作る。McCulloch は HM の残りを ABC の事前分布にすると本数がほぼ半分になると報告する一方、区間が狭すぎて真の値を含む率が下がる場合があると注意する(#46 ○)。Andrianakis は HM の利点を「the exclusion of implausible space is possible without considering the full set of inputs and outputs simultaneously」と書く(#44 ○)。
- v2 の目的は「データと明らかに合わない初期状態を除き、残りからアンサンブルの初期状態を引く」(10-12 §4-5)なので、事後分布の重みまでは要らない。HM だけで足りる(推測)。ABC は、初期状態に確率の重みを付けたくなった時の候補として残す。
- **データ同化**(#47 ○): Malleson ら 2020 の粒子フィルタは、観測が来るたびに観測に近い粒子(モデルの写し)を残す。粒子の数は体の数に対して指数的に増え、最大 10,000 粒子で 30〜40 体まで足りた。v2 はスナップショットの DT で、実時間の同期は要らない(CLAUDE.md §3)ので、今の段では採らない。

### 3-4 「較正データと holdout の分割」との整合

- HM に使ってよい観測は、パターン台帳 §10 の較正の側だけ(10-12 §4-5「使う現実データは較正用だけで、検証用には触れません」)。HM に使ったデータは §10-3 で検証に使わないものに入る。混在していた錨ファイルは 2-4 V6(第334 の commit)で較正の側と検証の側に分かれたので、HM の出力 f(x) を作る道具は較正の側のファイルだけを開き、検証の側の名を開かないことを試験で強制する(2-4 V6 の read_guard と同じ形・推測)。
- 分母の Var(ε)(モデルの食い違い)は、v2 の「歪む場所の宣言」を数にしたもの(lit ノートの指摘)。O'Gara は ε = 0 と置いたが、v2 は置けない。食い違いを宣言しないと HM の判定の幅が決まらない。

### 3-5 必要な本数と、v2 の費用(推測)

- 費用の前提(実測の写し): cf33 §4 の分岐の例で、5,000 体・世界の資産・mock・2 日の基準のランが 79.2 秒(1,000 体は 19.9 秒)。1 シム日あたり約 40 秒は、2 日の値を半分にした推測。実 LLM は今の手元に艦隊が無く、D-46 の旧見積り(サーバー時代)は 5,000 体で 0.5 時間/本(1 日)。
- **代理モデル無しの直接の判定**(McCulloch 型): 初期状態の候補が離散(母集団と環境の seed の組)なら代理モデルは要らない。候補 40 × 繰り返し 5 本 × 14 シム日 × 40 秒 = 112,000 秒 ≈ 31 時間(直列・mock・推測)。並列の数で割れる(CPU の数は未確認)。
- **代理モデルを使う波**(O'Gara・Andrianakis 型): 連続の生成の母数があるとき。1 波 1,000 本 × 7 シム日 × 40 秒 ≈ 78 時間/波(直列・mock・推測)。4 波で約 311 時間。
- **実 LLM**: 1,000 本 × 7 日 × 0.5 時間 = 3,500 時間/波(旧見積り)で回せない。**案(推測)**: HM の波は安い層(mock か古典か判断モデル)で回し、実 LLM は各波の診断のラン(Vernon の 200 本に当たる役)を数本〜数十本に絞り、安い層と実 LLM の差を Var(ε) に入れる。これは R-25 S2-d の「代理層が先」と同じ結論になる。
- 慣らしの期間(§4)が決まらないと 1 本の長さが決まらないので、順番は「慣らしの判定 → HM」になる(推測)。

## §4 慣らし(warm-up)の自動判定=CP5-6

### 4-1 MSER と MSER-5 の定義

- MSER(#4 ◎): 出力の列 y_1…y_n を打ち切り点 d で分け、後ろの部分の平均 Ȳ(n, d) を推定量とする。MSER(n, d) = S²(n, d)/(n − d)、S²(n, d) = (1/(n − d)) Σ_{i=d+1}^{n} (y_i − Ȳ(n, d))²。打ち切り点 d* = argmin MSER(n, d)。系列が相関していても、最小にする点を探すだけなら定数倍は無視できる(同論文 §2)。
- 考え方(#1 ◎): 終わりの方の観測が定常をよく表すと置き、後ろから観測を足していく。定常の間は平均の信頼区間の幅が縮み、定常でない観測が入ると幅が広がり始める。MSER-5 は 5 個ずつの平均にして「help to ensure the monotonic behavior of the decrease in confidence interval width」。White 1997 の言葉は「select a truncation point that minimizes the width of the CI about the truncated sample mean」(#3 ◎ の引用・#10 は △)。
- MSER-5(#3 ◎): 「acts upon batched (batch size of 5) data」。式は b = ⌊n/5⌋ 個のバッチの平均に当てる。

### 4-2 比較の結果(Hoad・White・Franklin・Mahajan・Taylor)

- **Hoad ら 2008**(#2 ◎): 文献から 42 の方法を集め(Warwick の一覧 #5 では 46)、自動化の容易さ・一般性・精度で絞り、試験した。「From the preliminary results obtained, the MSER-5 truncation method performed the best and the most consistently」。人工データ 3,048 組で試し、中間の 2,016 組 × 100 回=201,600 本のうち失敗(打ち切り点 > n/2)は 7.4%、その 88% 超が自己相関の最も強い ARMA(5,5) だった。5 本を平均したデータは、単独のランより偏りを大きく除けた。自己相関が強いほど打ち切り点を短く見積もる。外れ値に敏感。
- **White ら 2000**(#11 △): 5 つの規則を 168 の実験で比べ、MSER の 2 つの変種が Schruben 系の 3 つより良かった(抄録の要約)。
- **Franklin & White 2008**(#1 ◎): 108 の実験で、KPSS の定常性の検定が MSER-5 より偏りを除けたのは 4 件、t 検定で勝ったのは 7 件だけ。相関を補正した分散(PPVR)を使っても改善しなかった。減衰しない振動の偏りには、どの規則も一貫しては効かなかった。
- **Mahajan & Ingalls 2004**(#6 ◎): 「there is no method which works well for all types of models」。Welch の方法は「highly subjective」。Warwick の一覧の要約では、長い実行で MSER-5 を勧めた(#5)。
- **Taylor 2010**(#7 ◎・交通のシミュ VISSIM): Welch の方法を「consistency and ease of implementation」で勧めた。MSER は所要時間と網の中の車の数で打ち切り点がそろわなかった。25 秒のバッチの MSER-1 と 5 秒のバッチの MSER-5 は同じ結果になった(覆う時間の長さが同じため)。**v2 への読み**: 「5」という数より、1 バッチが覆うシム時間が効く。
- **Sánchez & White 2011**(#4 ◎): MSER は「effective and efficient at mitigating bias, robust across alternate forms of biasing functions, computationally trivial」で研究者の合意ができつつあると書く。Java Modelling Tools は MSER-5 を初期化の方法に選んだ(#60 の実装は未確認)。

### 4-3 Welch・Schruben ほか

- **Welch の方法**(#5 ◎ の要約・#15 原典 ×): k 本のランの各時点の平均を作り、窓 w の移動平均を描き、平らになった点を目で選ぶ。自動化できないので Hoad ら 2008 は外した(#2 ◎「requires a user to judge the smoothness and flatness of a moving average plot」)。v2 では判定には使わず、報告の図(計器盤)に載せる点検として使える(推測)。
- **Schruben 1982**(#13 △): 出力を標準化した検定の系列に変え、既知の極限の確率過程と比べて初期化の偏りを検定する。Hoad ら 2008 は Schruben の最大の検定を頑健さで外し、順位の検定は 2 本の論文の記述が食い違って再現できないとした(#2 ◎)。打ち切った後に残りの偏りを検定する用途なら候補に残る(推測)。
- **周期の規則**(#5 ◎): Tocher のサイクルの規則=「The initial transient period is over if the longest cycle distinguished in the behaviour of the simulated system has been executed at least 3 or 4 times」(Pawlikowski 1990 は「No results concerning the effectiveness of this rule are available」)。Beck の周期の出力の方法=最初の週の各時刻の値を、後の週の同じ時刻と比べる。
- **平衡の検出(分子シミュ)**: Chodera 2016 は、本番の区間の「実質的に相関のない標本の数」を最大にする点を選ぶ(#16 ○)。pymbar の `detect_equilibration` は Neff = (T − t + 1)/g_t を最大にする t を返す(#52 ◎)。MSER と別の原理なので、感度の腕の 2 本目に使える(推測)。

### 4-4 実装の作法(Hoad & Robinson 2011 ほか)

| 作法 | 原典の書き方 | 出典 |
|---|---|---|
| 最後のバッチは候補にしない | 最後の数個がたまたま近いと標準誤差が最小になり、打ち切り点を終わりに置いてしまう。既定で最後の 5 バッチ(5 × 5 = 25 点)では統計量を計算しない | #3 ◎ |
| 後半の打ち切り点は無効 | 打ち切り点が後半に落ちたら「invalid」とし、既定で 10% のバッチを足して計算し直す。無効が決まった回数続いたら止めて利用者に図を見せる | #3 ◎(失敗の定義 Lsol > n/2 は #2 ◎) |
| 複数本は平均してから当てる | 複数本の各時点の平均の系列に当てる。平均で滑らかになり、より頑健だった | #3 ◎・#2 ◎ |
| 累積の系列は使わない | 累積の平均や最大・最小は時間とともに分散が縮むので、打ち切り点が終わりに寄る。偏りの無い累積の平均の系列 100 本(長さ 1,100)で、前半に打ち切り点が出たのは 7% だけ。分解した(期間ごとの)値に直して当てる | #3 ◎ |
| 周期のある出力はサイクルでまとめる | 決定の図で「steady state cycle」の出力は「Batch Cycles」に進む | #3 ◎ |
| 出力ごとに当てる | 枠組みは利用者が選んだ出力ごとに MSER-5 を複製して回す | #3 ◎ |
| 本ごとに打ち切り点が違うとき | (1) 最大の打ち切り点で全部をそろえる (2) 長さで重みを付けた推定量 w_j = (n − d_j*)/N | #4 ◎ |
| 打ち切りの後の長さ | 慣らしの終わり w の後に、実行の長さを w の倍数で取る(既定 2 倍・Law & Kelton を引用) | #8 ◎ |
| 報告 | STRESS-ABS 4.1「State if a warm-up period has been used, its length and the analysis method used to select it」 | #9 ◎ |

- **既存の実装の差**(◎): pymser は 1 バッチの大きさを引数に取り、打ち切り点の候補を n − 3 番目まで(最後の 2 つを除く)とし、1e-9 未満の値を最大に置き換えてから最小を取る。打ち切り点が全体の 75% 以上なら警告を出す(#51)。Hoad の「後半なら無効・最後の 5 バッチを除く」とは値が違う。MultiVeStA の autoWarmup は MSER ではなく、128 個のバッチの平均の正規性(Anderson-Darling)と 1 次の自己相関の検定が通るまで、バッチの長さを倍にしていく(既定 B = 128・bs = 16・b = 4・minVar = 1e-7)(#8)。

### 4-5 ABM・周期のある系・定常に達しない系

- **ABM での使用例**: 社会 ABM で MSER-5 を使った論文は見つけていない(本書の検索の範囲。Vandin らは「decisions about … how many steps to "cut" up front as transient … deeply influence an analysis」と書き、MSER の代わりにバッチ平均の検定を使う=#8 ◎)。交通では Taylor 2010(#7)が MSER と Welch を比べた。
- **定常に達しない系**: Hoad & Robinson は、出力が過渡か定常か定常の周期かの判断(「What」の判断)は自動にせず利用者が決める、と書く(#3 ◎)。MATSim の用語の頁は、新しい計画を作り続ける限り「not truly stationary」とする(#19 ○)。v2 の基準のランは実日の暦と実際の天気(10e の既定)で進むので、日ごとの原系列は天気・曜日・祝日で動き続け、厳密には定常に達しない。
- **v2 の周期**: 1 日(1,440 刻み)・1 週(平日と週末)・1 か月(給料日=EC6 の暦)。Tocher の規則をそのまま当てると、最も長い周期を 3〜4 回=週なら 3〜4 週、月なら 3〜4 か月になる(算術)。10-12 の「最低 1 週間」は未リサーチの値のまま。

### 4-6 推奨の手順と parameter(親が判断する材料・未決)

印: **mechanism** = 先例の原典の作法か、v2 の既決の規律から導けるもの / **expedient** = 先例の無い本書の構成(未リサーチ)で、感度の腕が要るもの。

**問い 1(慣らし=基準のランの慣らしの日数)**

| 段 | 中身 | 印と根拠 |
|---|---|---|
| 0 指標の選び方 | 速い指標(1 人 1 日の外出・訪問・食事の回数など)と遅い指標(1 人 1 日に新しく結んだ約束の数・その日の終わりのグループの数・知り合いの数)。累積や 7 日の移動合計は使わず、日ごとの量(流量)か日の終わりの在庫にする。忘れることが無い在庫(知り合いの数が減らない作り)は定常に達しないので、流量(新しく知った数・忘れた数)に直す | 累積を使わない=mechanism(#3)。指標の一覧=expedient(CP5-6 の例示から) |
| 1 差の系列を作る | 同じ初期状態で、本番の開始日から始めるラン A と、k 日前から始めて慣れたラン B を回す。共通の日付の日ごとの差 D_t = A_t − B_t を作る(暦と天気の動きは両方に同じに入るので差で消える)。始まりの刻みが違うので、A と B は共通乱数の対にはならず、偶然の揺らぎは差に残る(段 3 の平均で減らす) | expedient(先例なし・Beck の「同じ時刻どうしを比べる」と発想は同じ)。k は 28 日を仮の値とする(Tocher の週 3〜4 回=expedient) |
| 2 まとめの単位 | 1 バッチ = 1 シム日(1,440 刻み)。さらに 5 日ずつにはまとめない(日のまとめが 5 個まとめの役を果たす) | 周期でまとめる=mechanism(#3)。「5 にしない」=expedient(Taylor の「覆う時間が効く」=#7 が根拠の材料) |
| 3 複数本の平均 | 初期状態ごとに偶然の対を 5 本以上回し、D_t を平均してから当てる | mechanism(#2・#3)。5 本=expedient(Hoad の試験の値) |
| 4 MSER を当てる | d* = argmin MSER(n, d)。候補は d ≤ n − 5(最後の 5 日を除く)。d* > n/2 なら無効として 10% 延ばす(切り上げで最低 1 日)。3 回無効なら「未収束」と記録して報告 | mechanism(#3・#2)。3 回=expedient |
| 5 指標を束ねる | 慣らしの日数 W = 有効だった指標の d* の最大。指標ごとの d* と有効/無効を manifest に記録(CP5-6「日数は結果として記録」) | 出力ごとに当てる=mechanism(#3)。最大で束ねる=expedient |
| 6 測る期間 | 測る期間は W 以上(全体で 2W 以上) | mechanism(#8 の既定 2 倍) |
| 7 点検 | Welch の図(計器盤)・pymbar の Neff の最大の点(感度の腕)・週の周期の残りの点検(差の系列で曜日の平均が 0 から離れていないか) | 点検=expedient |

- 必要な長さの算術: d* = 7 日を有効と判定するには n ≥ 14 日(後半の規則)。最後の 5 日の除外と合わせて、基準のランは少なくとも 14 日が要る。mock で 5,000 体・5 対なら、A が 14 日 × 5 本、B が(28 + 14)日 × 5 本で計 280 シム日、× 40 秒 ≈ 3.1 時間/初期状態(直列・推測)。
- 月の周期の指標(お金の流れなど)は、14〜28 日では Tocher の規則を満たせない。慣らしの対象から外し、「推移として報告する指標」に分ける案を出す(expedient・§6-5)。

**問い 2(3 区間=構え・切り替わり・新しい日常)**

| 段 | 中身 | 印と根拠 |
|---|---|---|
| 1 区間の定義 | 構え=告知(notice.at)から実行の時刻まで(申込書の欄で決まる・判定は要らない)。切り替わり=実行の時刻から新しい日常の始まりまで。新しい日常=判定で見つけた点から終わりまで | 決定 10-12 CP5-6 のとおり |
| 2 差の系列 | 改変の枝 − A/A の枝(同じ初期状態・同じ偶然の seed・同じ分岐の点)の日ごとの差を、6 対以上で平均する。暦・天気・曜日は対の両方に同じに入るので差で消える | 対の差=mechanism(R-71・CRN)。日ごと=expedient |
| 3 判定 | 実行の時刻から先の差の系列に、問い 1 の段 4 と同じ MSER の規則を当て、d* を「新しい日常の始まり」とする。新しい日常の水準は 0 でなくてよい(MSER は水準の値を問わない) | mechanism(#1・#3)。差の系列に当てる形=expedient |
| 4 共通の窓 | 対は全部同じ窓で比べる。平均の系列で 1 つの d* を決め、全対に当てる(本ごとの最大でそろえる #4 の (1) は感度の腕) | 対の設計=mechanism。どちらを主にするか=expedient |
| 5 事前登録 | 登録するのは日付ではなく、判定の規則と parameter(指標・まとめの単位・最後の除外・後半の規則・延長の幅・無効の回数) | mechanism(探索と確認の規律・R-71 §6 の ICH E9) |
| 6 細かい切り替わり | 切り替わりの区間の中の形は、15 分ごと(15 刻み)の差の系列で記述する(判定には使わない) | expedient |

- 実行の後に必要な長さ: 新しい日常の始まりが実行の 7 日後なら、後半の規則で実行の後に少なくとも 14 日が要る(算術)。
- 先例の注意: 打ち切り点は自己相関が強いと短く出やすい(#2)。日ごとの差の系列でも、在庫の指標は日をまたいで相関するので、短すぎる判定に注意する。

### 4-7 既存の実装(Python の MSER-5 ほか)

- pymser(#51・BSD-3-Clause・出典を付けて写せる): `calculate_MSEm(data, batch_size)` が MSER-m の曲線を、`MSERm_index` が最小の点を返す。候補の範囲・小さい値の置き換え・75% の警告は Hoad の作法と違うので、写すなら §4-6 の規則に合わせて書き換える。依存に PyTorch がある。2026-06 から読み取り専用の保管。
- pymbar(#52・MIT): `detect_equilibration(A_t, fast, nskip)`。MSER とは別の原理(Neff の最大)。
- MultiVeStA(#55・研究用のバイナリだけの許諾=非商用・再配布の制限): 手順(Algorithm 3〜5)を論文から読むだけ。
- R の MSER の実装と JMT のコードは未確認(× #60)。
- 実装の量の見立て(推測): MSER の本体は 20 行程度(式が単純)。v2 で自前に書いて pymser と同じ入力で値が一致するかを試験で確かめる形が、依存を増やさずに済む。

## §5 既存の実装の比較表

| # | 名 | 何ができるか | ライセンス | v2 で使える部分 | 扱い |
|---|---|---|---|---|---|
| 1 | MATSim | 基準ケースと政策ケース・途中の再計画・quenched な誤差項 | GPL-2.0 以上(#58) | 政策ケースの作り方と「知らせる時刻」の欄・quenched の 2 方式の考え方 | 読むだけ |
| 2 | Covasim(今は starsimhub) | 開始日つきの介入・複数ラン・Optuna の較正 | MIT(#59)。論文の時点は CC BY-SA 4.0(#23)=版ごとに確認 | 介入の型の一覧(負の対照=v2 が持たない「エンジンが実行」の型) | 写せる(版を確認) |
| 3 | Starsim | Covasim の後継・CRN(Klein 2024 の著者) | MIT(#59) | 用途ごとの乱数の流れの作り(R-71 §1) | 写せる(中身は本書で未読) |
| 4 | OpenABM-Covid19 | 疫学 ABM の介入 | GPL-3.0(#59) | なし | 読むだけ(中身未読) |
| 5 | CovidSim | 疫学 ABM の介入 | GPL-3.0(#59) | なし | 読むだけ(中身未読) |
| 6 | Concordia | 段ごとの checkpoint の保存と復元・外からの出来事の印 | Apache-2.0(#59) | checkpoint の JSON の形と、復元で深い写しを取る作法 | 写せる |
| 7 | AgentSociety | workflow の介入の型・対照群と処置群 | Apache-2.0(#59) | 申込書の型の検査の形(R-113 §3) | 写せる |
| 8 | OASIS | 初期の評価で群を分ける・繰り返し | Apache-2.0(#59) | 群の分け方の例 | 写せる |
| 9 | Generative Agents | 初期の記憶に情報を入れる・内なる声 | Apache-2.0(#59) | 情報の広がりの測り方(面接) | 写せる(内なる声は v2 の禁止に当たる) |
| 10 | Williams ら(GABM-Epidemic) | プロンプトの条件で介入・架空の名 | 未確認(論文は CC BY-NC-ND 4.0) | 架空の名で偏りを避ける作法 | 読むだけ(未確認) |
| 11 | SocioVerse2 | 介入で枝を分ける・研究の版・時点の保証 | 未確認(抄録は「open-source」) | 時点の保証の考え方 | 読むだけ(中身未読) |
| 12 | COVID-19 Scenario Modeling Hub と hubEnsembles | シナリオの仕様の公開・trimmed-LOP・WIS | hubEnsembles は MIT(#54) | 仕様と投影を公開リポに置く運用・集め方 | 写せる(R) |
| 13 | ECMWF IFS のアンサンブル | EDA と特異ベクトル・SPPT・SKEB | 公開のコードではない | 揺らしの源の分け方・IP only との対の比較 | 文書だけ |
| 14 | scoringrules | CRPS(fair を含む 7 つの推定量)ほか | Apache-2.0(#56) | fair CRPS | 写せる |
| 15 | scores | rank histogram ほか | Apache-2.0(#59) | rank histogram | 写せる |
| 16 | xskillscore・properscoring | CRPS などの点数 | Apache-2.0(#59。properscoring は保管) | 点数の検算の相手 | 写せる(中身未読) |
| 17 | hmer | HM と代理モデル(R) | MIT(#54) | 非含意度と波の手順 | 写せる(R) |
| 18 | mogp-emulator | ガウス過程の代理モデル・`HistoryMatching`(既定の閾値 3・2 番目に大きい値) | MIT(#53) | 非含意度の計算の形 | 写せる |
| 19 | Urban-Analytics/uncertainty | ABM の HM と ABC(McCulloch 2022 のコード) | MIT(#59) | 代理モデル無しの直接の HM | 写せる(中身未読) |
| 20 | Urban-Analytics/dust | ABM の粒子フィルタ(Malleson 2020) | MIT(#59) | 今は採らない | 写せる(中身未読) |
| 21 | pymser | MSER-m・ADF の検定・自己相関の時間 | BSD-3-Clause(#51) | MSER の曲線(作法は書き換え) | 写せる |
| 22 | pymbar | Neff 最大の平衡の検出 | MIT(#52) | 感度の腕の 2 本目 | 写せる |
| 23 | MultiVeStA | autoWarmup・autoRD・autoBM | 研究用のバイナリだけ(#55) | 手順(論文) | 読むだけ |
| 24 | EMA workbench | 探索的なモデル化・シナリオの発見 | BSD-3-Clause(#59・検索の API) | 探索の段の道具の候補 | 中身未読 |

行数: 24。

## §6 3-3 の残りと CP5-6 への含意・未リサーチ・親に確かめてほしいこと

### 6-1 3-3 の残りへの含意(親が判断する材料・未決)

- **CP5-1(最初からの順)**: Müller 2020 の理由(反復で慣らすと住人が運休を前もって知る)から、「最初から」で回してよいのは、住人が始めから知っている改変(その世界が初めからそうだった)に限られる。予期しない出来事の改変は途中から(T0 > 0)で回し、経験を作り直さない。申込書の検査に「始まり 0 で、告知が無い(または予期しないと書いた)改変」を拒むか警告する欄を足す案がある(推測)。
- **CP5-3(経験は改変の後・ペルソナの点検)**: Williams の架空の名・SocioVerse2 の時点の保証が同じ向きの先例。名指しの検査に加え、LLM が実在の出来事として知っている改変(実在の閉店や運賃の改定など)は、モデルの知識による混入の疑いを記録する欄があるとよい(推測)。
- **CP5-6**: §4-6 の手順。慣らしの判定は 1 本の長さを決めるので、HM と本数の見積りより先に置く。
- **艦隊の分岐**: 実 LLM で T0 から回すと、A/A の枝は基準と厳密には一致しない(R-71 §1-5・Concordia の docstring)。(d) を「T0 より前の一致と mock・古典での決定論の確認」と「T0 以後の A/A の対の差=床の分布」に分ける必要がある。(c) の「最初の食い違い」も、実 LLM では A/A でも出るので、改変の枝と A/A の枝の最初の食い違いの時刻の差を比べる形になる(推測)。
- **L2〜L4**: 先例の介入は、運休(MATSim)・パラメタの変更(Covasim)・シナリオの軸(SMH)で、どれもエンジンが当てる。v2 の「決定だけ入れて人が実行する」は L2 の柵や通路の開閉でも同じ規律になるので、担当の勤務と居場所(6-6・カレンダー 3)が前提になる(cf33 §4 の「担当の実行 1・つなぎ 199」と同じ問題)。L4 の「来る人の構成」は SMH のシナリオの軸に当たり、初期状態のアンサンブル(HM の残り)と組み合わせる設計が要る(推測)。

### 6-2 未リサーチ・推測の一覧

- 差の系列に MSER を当てる形(問い 1 の「2 つの出発点の差」・問い 2 の「改変 − A/A」)= expedient。先例は見つけていない。
- 1 バッチ = 1 シム日・最大で束ねる・無効 3 回で止める・慣れたランの先行 28 日・5 対 = expedient。
- 揺らしの源ごとの分散の分解の推定式 = 未リサーチ。
- HM と慣らしの費用(1 シム日 約 40 秒・31 時間・78 時間/波・3.1 時間/初期状態)= 推測(mock の 2 日の実測を線形に伸ばした値)。
- 外の時刻の証拠(第三者の時刻印・公開リポへの push の記録)= 未リサーチ。
- 社会 ABM で MSER-5 を使った例・MATSim の HM の例・区域ごとの時計の社会 ABM の実装 = 見つけていない。

### 6-3 親に確かめてほしいこと

1. **10-12 §1-2 と要件の「ECMWF の教訓」の写し**: #30 の逐語(初期だけでは広がり不足)で前半は一次確認できた。「乱数だけでは狭すぎる」は ECMWF の文では確認できていない。要件の「一次確認待ち」の注をどう直すか。
2. **(d) A/A の分け方**: 艦隊の分岐の前に、(d) を決定論の確認と床の分布に分けるか(§6-1)。
3. **CP5-6 の手順**: §4-6 の差の系列の案(expedient)を採るか、原系列に MSER を当てて天気と暦の変動を宣言で済ませるか。
4. **指標の作り方**: 知り合いの数のような単調な在庫を流量に直す規則を、計器の側(CA8 の一覧など)で先に決めるか。忘却が無い作りのままなら、遅い指標は未収束と出続ける。
5. **周期**: 週の周期は差の系列で消える前提にしたが、月の周期(給料日)の指標を慣らしの対象から外して「推移の指標」にするか。
6. **HM の入力**: v2 の初期状態の候補が離散の seed の組だけなら代理モデル無しの直接の判定で足りる。連続の生成の母数を持つかは、§1-6(係数で持たない)と第 4 期の人口の作り直しの決め方による。
7. **CP14 の封印の時刻の証拠**: 手元の git の履歴だけで足りるとするか、公開リポへの push や第三者の時刻印を足すか。
8. **CP5-1 の検査**: 「始まり 0 の予期しない改変」を申込書の検査で拒むか(Müller 2020 の理由)。

## §付録 10-06 の E2 の残り(CA・TM・System 1/1.5/2・道具)のカバー状況

本書は新しく調べていない。既存答申の見出しと本文の該当部分で、カバーの有無だけを確かめた。

| 項目 | カバーしている既存答申 | 空欄 |
|---|---|---|
| CA カレンダーと予定の変更 | [R-102](v2-r102-schedule-change-and-punctuality.md)(予定の変更の頻度・きっかけ・変えたがらない傾向・遅刻)・[R-89](v2-r89-prospective-memory-punctuality.md)・[R-103](v2-r103-surprise-prospective-memory-future-thinking.md) §2(予定を思い出す仕組み)・[R-43](v2-r43-code-reading-ga-aitown-humanoid.md) と [R-44](v2-r44-code-reading-concordia-agentsociety-oasis.md) の Q7(GA・AgentSociety の計画の階層のコード) | 予定の表を道具として持ち、変更を記録する LLM エージェントの実装のコード読み |
| TM 連続時間と区域ごとの時計 | [R-73](v2-r73-time-model-des.md)(時間刻みと事象駆動・PDES の同期・LLM 社会シミュの例)・R-113 §2(時計の型と待ち行列) | 区域ごとに違う時計を持つ社会 ABM の実装例(R-73 §2 は PDES の原理まで) |
| System 1/1.5/2・驚きで考え始める | R-103 §1(驚きの仕組みと量・熟考への切り替えの研究・設計に使えない理由)・[R-41](v2-r41-cognitive-architecture-precedents.md) §1(「System 1.5」の名が LLM 論文と衝突) | 驚きで LLM の呼び出しを起こす既存の実装のコード読み |
| 道具(カレンダー・乗換案内・メッセージ) | [R-85](v2-r85-communication-tools.md)(道具の一覧と使われ方・LLM 社会シミュのメッセージと SNS)・[R-104](v2-r104-llm-agent-human-gaps-and-transit-app-accuracy.md) §2(乗換案内の使用率と見積りの外れ)・R-113 §8(道具の台帳の実装) | カレンダーと乗換案内を道具として持つ LLM エージェントの実装(R-113 §8 は「知っている/知らない」の欄を持つ実装は無いと書く) |

## §空欄

1. Welch 1983 の原典(#15)。
2. Monks ら STRESS の本文(#14)と DES・SD の表の項目。
3. Hoad ら 2010 JORS の本文(#12)と、MSER-5 の最終の推奨の文の逐語。
4. White 1997・White ら 2000 の本文(#10・#11)。
5. Schruben 1982・Schruben, Singh, Tierney 1983 の本文(#13)。Franklin & White 2008 の文献の欄は Schruben 1982 の頁を「30(3):151-153」と書いており、IDEAS の 569-590 と食い違う(原典の側の誤記と読む)。
6. Vernon ら 2010 の本文(#42。2014 の要約で代えた)。
7. Hamill 2001・Fortin 2014 の本文(#33・#34)。
8. Hawkins & Sutton 2009・Haber & Stornetta 1991・Cox 1975・Wagenmakers 2012 の本文(#38〜#41)。
9. McKinley ら 2018(HM と ABC の比較の総説・#49)。
10. Andrianakis 2015 の第 9 波の残りの割合と、初期の繰り返しの本数(画像で読めず)。
11. JMT の MSER-5 の実装とライセンス(#60)。R の MSER の実装。
12. 社会 ABM で MSER-5 を使った論文・MATSim の HM の例・区域ごとの時計の社会 ABM。
13. 差の系列に MSER を当てる手順の先例。
14. 予測の封印に第三者の時刻印を使ったシミュの先例。
15. xskillscore・properscoring・Urban-Analytics/uncertainty・dust・EMA workbench・Starsim の中身(ライセンスだけ確認)。

## §INDEX に足す行の案(本書では追記しない。親が入れる)

| 10-15 | [r117-e2-counterfactual-ensemble-warmup-precedents](v2-r117-e2-counterfactual-ensemble-warmup-precedents.md) | 406 | **B**(サブ自己評価 ◎ 30・○ 12・△ 13・× 5・親検収 未) | 統計学・因果推論 #23 / ABM方法論 #21 / 検証とV&V・UQ #22 / 予測科学(アンサンブル) #24 / 交通工学 #2 | R-117 E2(計画 §7 → 3-3・CP5-6): 3-3 の形を一揃いで持つ先例は無し(MATSim の quenched・cloning・SMH・Concordia の checkpoint は部品)・予期しない改変は反復で慣らさない(Müller 2020)・ECMWF「初期だけでは広がり不足」を一次確認(乱数だけの部分は未確認)・技量スコアは proper でない注意・HM の本数と v2 の費用(推測)・MSER-5 の作法と差の系列の案(expedient)・比較表 24 行 |

取得したデータは無い(ライセンス台帳に足す行は無い)。
