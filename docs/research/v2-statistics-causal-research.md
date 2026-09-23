# 答申: 多重比較・同値検定・共通乱数・反実仮想の評価 — 統計学と因果推論 #23 の第 1 答申(2026-09-17・レーン R-25)

<!-- hdr:v1 -->
- **分野**: 統計学・因果推論 #23 / 検証と V&V #22 | **重要度**: **P0**(D-70 の次のゲート・D-44 の省き方・事前登録 v1.3・到達点 C「反実仮想の精度」の物差しが依存)
- **一次確認**: **B**(サブ Opus 5 が 11 出典を実読して逐語採取。うち PDF 5 本は pymupdf で本文抽出・HTML/PMC 6 本は本文取得。**抄録のみ = 3 件**(Marshall & Galea 2015・Ramdas et al. 2023・Robinson & Froese 2004)。**親一次確認は未了**——§2 の決定に使う前に §5 の「親が最初に一次確認すべき 3 件」を通すこと) **→ 親確認 3 件(第209)**: Sargent, Goldsman & Yaacoub 2016(informs-sim 016.pdf・親 pymupdf)「α, is called the model builder's risk, and … β, is called the model user's risk」「H0: L ≤ D ≤ U vs. H1: D < L or D > U」/ Myllymäki & Mrkvička(arXiv 1911.06583v4)「p = Σ 1(Mi ≤ M1) / s」・交換可能性の要件(=seed 3 本で p ≥ 0.25 は親再計算で成立)/ 3 seed の算術(t(2)=4.303・9.925 → d₃=248.4·CV / 573.0·CV・CV 0.0038→±2.18%・0.0325→±18.6%)一致。**訂正**: 「深夜 2% を家族で言うには N≈87 本」は親再計算で **N≈20 本**(t 分布・α=0.01 両側・CV 0.0325: N=20 で ±2.08%)。Murphy 2013(CRN −93.6%/−5.6%)は親未確認(PMC の ID 違い)
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)(R-25・R-14) ・ **lit**: [lit/README.md](lit/README.md)(本答申と同時に 8 本) ・ **判断**: PENDING D-70・D-44・D-46 / 事前登録 [prereg_arms_v1.md](../bench/c7/prereg_arms_v1.md) §6 / 計器盤 G-8

> **問い**: holdout 照合(5 指標 × 3 seed)で「現実の帯の中にある」と言うには、どの手続きが要るか。ablation の対照は共通乱数で何本減らせるか。正解の無い反実仮想はどう検証するか。
> **答え(要旨)**: 4 つ分かった。(i) **いまの H1〜H5 は「差が無い」を帰無に置いており、検出力が低いほど合格しやすい向きに傾いている**——シミュレーション V&V にはこれを反転させた既製手続きがある(Sargent の**区間仮説検定**=モデル製作者危険 α / モデル利用者危険 β)。(ii) **「実測が 3 本の幅の中にある」は Monte Carlo 検定であり、s 本では p の下限が 1/s**。seed 3 本(+実測=s=4)では **p ≥ 0.25** で、α=0.05 の判定は原理的に不可能。帯は記述にとどまる。**α=0.05 の大域包絡には s ≥ 20(= seed 19 本)**。(iii) **共通乱数(CRN)は腕の比較にしか効かず、holdout には効かない**。しかも実測では**完全 CRN が分散 −93.6% に対し部分 CRN は −5.6%**——腕ごとにプロンプトが変わる我々は部分 CRN の側で、D-70 (d)「CRN で N を減らす」の期待値は小さい。(iv) **D-44 は設計を良くしても解けない**: k=122 では Morris(N(k+1) ≥ 492 ラン)も Sobol' も現行 OFAT 244 ランより高い。**逐次群スクリーニング(SB/CSB)だけが安く、かつ 1.5〜3 倍どまり**。→ 解は「安い階層(5,000 体・0.5 h)へ移す」+「検出可能効果量の床を宣言する」の 2 つ。

---

## 1. 問いごとの一次確認(逐語・式・v2 への含意)

### 1-1. 多重比較と同値検定(H1〜H5 の家族単位の誤り / 「帯の中にある」の言い方)

| 出典 | 逐語(原文・節) | 数値・式 | v2 への含意 |
|---|---|---|---|
| **Currie & Cheng (2016)** "A Practical Introduction to Analysis of Simulation Output Data", WSC 2016, pp.118–131 <https://www.informs-sim.org/wsc16papers/013.pdf> | §6.2 Comparing Many Systems: "**As the number of confidence intervals calculated increases, the confidence we have that all of the statements that we make are true decreases.**" / "Pr[all statements S_l, l = 1,…,C, are true] ≥ 1 − Σ α_l" / 作例: "**there is only a 50% chance that all of the confidence intervals contain their respective means**" / "**we would need to compute (100−10/5)% = 98% confidence intervals for each individual result**" | C=5・各 α=0.10 → 家族 α=0.5。家族 90% には個別 **98%** | **5 指標に 5 回の 90% CI を並べると家族の信頼は 50%**。我々の H1〜H5 はまさに C=5。個別を 98%(または 99%)に締めるか、**1 本の大域検定に畳む**かの二択(§1-4 が後者) |
| **Sargent, Goldsman & Yaacoub (2016)** "A Tutorial on the Operational Validation of Simulation Models", WSC 2016, pp.163–177 <https://www.informs-sim.org/wsc16papers/016.pdf> | §2.2.3 Interval Hypothesis Test: "**one is interested in determining if the accuracy of a model is within its acceptable range of accuracy specified by L and U**" / "**Classical hypothesis tests determinations are typically about a specific point.**" / "Type I error is that of rejecting the validity of a valid model, and Type II error is that of accepting the validity of an invalid model" / "**The probability of a Type I error, α, is called the model builder's risk, and the probability of Type II error, β, is called the model user's risk**" / "**In model validation, the model user's risk is especially important and must be kept small**" / 仮説形: "H0: L ≤ D ≤ U vs. H1: D < L or D > U" / §2.2.2: "The univariate techniques can be used to develop c.i.'s and **with the use of Bonferroni's inequality** … s.c.i.'s" | 作例: (L,U)=(−0.75, 0.75)・n_R=10/n_M=15 で開始 → **危険曲線を見て n_R=20/n_M=25 へ増やす** → T=−1.369 が受容域 (−1.262, 1.262) の外 = **不合格**。L を −1.00 に緩めると同じ T が受容域 (−1.766, 1.262) に入り **合格**。α_L + β_L = 1(選んだ β=0.40 → α=0.60) | **これが「現実の帯の中にある」の V&V 版の正典**。H0 を「帯の外」ではなく「帯の中」に置いた**区間仮説**で、我々の H1〜H5 と同じ形(H1 は JSD ≤ 0.0122 という片側の帯)。**いまの我々は α(製作者危険)だけを気にして β(利用者危険=不正なモデルを通す確率)を一度も計算していない**。Sargent 手順の Step 3〜4(危険曲線を見て標本数を決める)は 3 seed のまま実行できる |
| **Sargent (2015)** "An Introductory Tutorial on Verification and Validation of Simulation Models", WSC 2015, pp.1729–1740 <https://www.informs-sim.org/wsc15papers/182.pdf> | §1: model validation = "**substantiation that a computerized model within its domain of applicability possesses a satisfactory range of accuracy consistent with the intended application of the model**" / §1: "**A model's acceptable range of accuracy should be specified prior to starting the development of the model or very early in the model development process.**" / §5.3.2: 比較の 3 経路 = "(1) the use of graphs to make a subjective decision, (2) the use of confidence intervals to make an objective decision, and (3) the use of hypothesis tests" / §5.3.2: 統計が使えない理由 "(b) there is an insufficient quantity of system data available, which causes the statistical results to be 'meaningless'" | 推奨手順 8 項の第 2 項 = **許容精度域を開発前に決めておくこと** | **事前登録 v1.0〜v1.2 は既にこの第 2 項を満たしている**(PREREG_V0 の線を先に固定)=文献準拠。足りないのは「線」を**区間仮説として検定する**段。Sargent 自身が「系のデータが足りないと統計が無意味になる」と書いており、**KDDI が 1 観測しかない我々は一標本検定の側**(同論文 Table 2 の Simulation Model vs Reference) |
| **Lakens (2017)** "Equivalence Tests: A Practical Primer…", *Soc Psychol Personal Sci* 8(4):355–362, doi:10.1177/1948550617697177(CC BY 4.0) | Introduction: "A very simple equivalence testing approach is the 'two one-sided tests' (TOST) procedure" / "Two composite null hypotheses are tested: H01: Δ ≤ −ΔL and H02: Δ ≥ ΔU." / Testing for Equivalence: "**In the TOST procedure, the null hypothesis is the presence of a true effect of ΔL or ΔU,**" / "**To conclude equivalence (Scenario A), the 90% CI around the observed mean difference should exclude the ΔL and ΔU values**" / 4 帰結: "statistically different from zero but not statistically equivalent, statistically different from zero and statistically equivalent" / "or undetermined" | 決定則 "The two one-sided tests are rejected if tU ≤ −t (df, α), and tL ≥ t (df, α)" | **「90% CI が帯の内側に収まれば同値」= 3 seed でも今日できる**。ただし片側 α=0.05 の t は自由度 2 で **2.920**。相対幅で書くと **必要な帯 ≥ |偏り| + 1.686·CV**(下の再計算)。**「有意差なし」と「同値」は別の結論**であり、我々の「帯の中」は後者 |
| **Robinson & Froese (2004)** "Model validation using equivalence tests", *Ecol Model* 176(3–4):349–358, doi:10.1016/j.ecolmodel.2004.01.013 | **抄録のみ**(有料)。抄録: "Previously, such validation has commonly used the hypothesis of no difference as the null hypothesis, that is, the null hypothesis is that the model is acceptable. This is unsatisfactory, because **using this approach tests are more likely to validate a model if they have low power**" / "**they flip the burden of proof back onto the model**" | — | **いまの H1〜H5 の弱点を一文で言い当てている**: 「差が無い」を帰無に置くと**検出力が低いほど合格しやすい**。3 seed は検出力が低い=いまの形のままだと「3 本で合格」は褒め言葉にならない。**立証責任をモデル側に戻す**のが同値検定 |

**親が再計算した数(3 seed・自由度 2)**

| 量 | 式 | 値 |
|---|---|---|
| 両側 95% の相対半幅 | d₃ = 100·t_{2,0.975}·CV/√3、t=4.3027 | **d₃ = 248.4·CV** |
| 上に 5 指標 Bonferroni(家族 95%・個別 α=0.01) | t_{2,0.995}=9.9248 | **d = 573.0·CV** |
| 上に 5 指標 Bonferroni(家族 90%・個別 α=0.02) | t_{2,0.99}=6.9646 | **d = 402.1·CV** |
| TOST の片側(α=0.05) | 必要な帯 ≥ 偏り + t_{2,0.95}·CV/√3、t=2.9200 | **必要な帯 ≥ 偏り + 1.686·CV** |
| 参考(8 seed・第200 答申) | d₈ = 83.6·CV | — |

**実測 CV(第204・c7-day-4 seed 1 vs 2)に当てると:**

| 指標の CV | d₃(単独 95%) | d(5 指標 Bonferroni・家族 95%) | 偏り 0 での同値可能な最小帯 |
|---|---|---|---|
| 時刻別 CV 中央値 **0.0038**(昼) | **0.94%** | **2.18%** | **0.64%** |
| 時刻別 CV 最大 **0.0325**(05 時・深夜) | **8.07%** | **18.6%** | **5.48%** |

→ **昼は 3 seed で家族 95% でも ±2.2% を主張できる。深夜は ±18.6% までしか言えず、「深夜を 2% で」は 3 seed では成立しない**(第204 の「3 本で深夜 2%」は**単独指標・非 Bonferroni** の数で、5 指標家族に直すと届かない)。→ **事前登録 v1.3 の争点**。

---

### 1-2. 共通乱数(CRN)と対照腕の分散低減

| 出典 | 逐語(原文・節) | 数値・式 | v2 への含意 |
|---|---|---|---|
| **Currie & Cheng (2016)** WSC 2016 §5.3・§6.1 | "**The most useful and arguably the most widely used of the variance reduction techniques is that of Common Random Numbers (CRN)**" / "when we are comparing different system configurations, we will reduce the variability if we run each of the system configurations under similar conditions" / "**you should try to ensure that the same random numbers in the stream are being used to generate the same variables**" / §6.1 対応差: "Δi = yi(1) − yi(2)" ・CI = "Δ̄(n) ± t_{n−1,1−α/2}·√Var[Δ̄(n)]" / "**The method of Common Random Numbers … can be very useful for reducing the width of the confidence interval for a fixed value of n**" | 例示: M/M/1(平均サービス時間 0.9 vs 0.93)・5,000 客・10 対 — 独立対と CRN 対の差の分散を図 6 で対比 | **CRN は「対照どうし」にしか効かない**。**holdout(現実は 1 本しかない)には効かない**——H1〜H5 の分散低減にはならない。効くのは **ablation(AB1〜AB7c)と腕間差**だけ |
| **Murphy, Klein, Smolen, Klein & Roberts (2013)** "Using Common Random Numbers in Health Care Cost-Effectiveness Simulation Modeling", *Health Serv Res* 48(4):1508–1525, doi:10.1111/1475-6773.12044 | 目的 "(1) to create identical patient populations across treatment arms" / "to eliminate the differences between treatment arms that are not due to actual differences in the comparators" / 実測 "**the same CI achieved simulating 1,000 patients using Full CRNs required simulating 16,000 patients without using CRNs**" / 同期 "**Identical random numbers across cohorts may still not guarantee common patients because of the lack of event synchronization**" / 危険 "**In these cases, the use of CRNs can actually increase variance**" / "CRNs may be inappropriate where model interactions of multiple variables exist." | **完全 CRN: 増分費用の平均の分散 −93.6%・95% CI 半幅 −74.7%**。**部分 CRN(初期特性のみ共通)は −5.6% / −2.8%**。実効標本 **16 倍** | **決定的**: 我々の腕はプロンプト内容が変わるため LLM 側のサンプラ列は同期できない(トークン数が変われば列がずれる)=**部分 CRN**。部分 CRN の実測利得は **5.6%**(実効標本 1.06 倍)。→ **D-70 (d)「共通乱数で N を減らす」は、いまの設計では効かない**。効かせたいなら**エンジン側の乱数を用途別・個体別の副流に分ける**(母集団抽出・初期配置・p_notice・繰り延べの各々に別 seed)実装が要る。そこまでやっても「完全 CRN」には届かない |
| **Shah (2026)** Causal Agent Replay(既読 lit) | "a single-stream local model with a fixed seed replays exactly" / 共通乱数は "hard across divergent LLM contexts" として将来課題 | — | **我々は「再生できる側」だが「共通乱数を持てる側」ではない**。テープ再生(T2-c)で同一性は確認できるが、腕が違えば文脈が分岐する |

**我々の数への当てはめ**: AB7 の腕間 JSD 0.052〜0.054 に対し seed 間 JSD 0.00007(第202)= **効果は seed 差の 700 倍**。**分散低減が律速ではない**——「駆動している」は 2 seed で既に言える。CRN が要るのは **効果が seed 差と同程度の腕**(D-44 の 108 行の大半がここ)。そこでも部分 CRN では 5.6% しか縮まない。

---

### 1-3. 反実仮想の評価(正解が無い問題)

#### (a) 因果の枠でシミュレーション介入を定式化した先行

| 出典 | 逐語(原文・節) | v2 への含意 |
|---|---|---|
| **Marshall & Galea (2015)** "Formalizing the Role of Agent-Based Modeling in Causal Inference and Epidemiology", *Am J Epidemiol* 181(2):92–99, doi:10.1093/aje/kwu274 | **抄録のみ**(有料)。"describing how **agent-based models can be used to simulate counterfactual outcomes in the presence of complexity**" / 有用な条件 = "the hypothesized causal mechanisms exhibit a high degree of interdependence between multiple causal effects" / "**interference (i.e., one person's exposure affects the outcome of others) is present and of intrinsic scientific interest**" / 留保 "theoretical and practical issues impede the capacity of agent-based methods to examine and evaluate causal effects" | **ABM が潜在結果の枠で正当化される条件は「干渉(interference)がある」場合**。渋谷の混雑・待ち合わせ・店舗容量はまさに干渉。**到達点 C の主張の型を「個体の平均処置効果」ではなく「干渉のある系の集団反応」に置くべき**という示唆。**識別仮定(consistency / exchangeability / positivity)の本文は未読=空欄** |
| **Dyer, Bishop, Felekis, Zennaro, Calinescu, Damoulas & Wooldridge (2023)** "Interventionally Consistent Surrogates for Agent-based Simulators", arXiv:2312.11158 | §2.2 "**Observe that an ABM can be modelled as a SCM by expressing its implicit underlying causal structure.**" / §2.3 Def.3: "An exact τ-ω transformation is a τ-ω transformation such that τ_#(P_{M_ι}) = P_{M′_{ω(ι)}}, ∀ι ∈ I." / §1 目標 = 代理が "(approximately) preserve the behaviour of the ABM under equivalent policy interventions" / §5.2 実測: **観測データだけで学習した代理は封鎖の効果を逆向きに予測**("the observationally trained surrogate predicts that the lockdown will temporarily increase infections") | **ABM = SCM と書ける**ことの明示先行。**代理モデル(低忠実度層)を作るなら、介入下のデータで学習しないと介入効果を取り違える**——D-70 (c)「15 分/シミュ日の surrogate」を将来やるなら、**観測ランだけで学習してはいけない**という設計上の禁則。数値: 介入学習 vs 観測学習の AMSE(×10⁻¹ 中央値)= LODE-RNN **3.350 vs 18.47**、LRNN **3.475 vs 49.44**、LODE **8.150 vs 22.39** |
| **Shah (2026)** Causal Agent Replay(既読) | `do_resample`/`do_action`/`do_observation`/`do_context`/`do_policy` の 5 演算・point-of-commitment 則 | 手番単位の介入代数。**個体 1 体の検死**に使う道(既存メモ) |

#### (b) 正解が無いときの妥当性の検証法

| 出典 | 逐語(原文・節) | 数値 | v2 への含意 |
|---|---|---|---|
| **Lipsitch, Tchetgen Tchetgen & Cohen (2010)** "Negative Controls: A Tool for Detecting Confounding and Bias in Observational Studies", *Epidemiology* 21(3):383–388, doi:10.1097/EDE.0b013e3181d61eeb | §Choice of negative controls: "a negative control outcome is connected to A through all possible confounding routes but **not causally**" / 目的 "**to reproduce a condition that cannot involve the hypothesized causal mechanism**" / 実験生物学の原型 "to repeat the experiment under conditions in which it is expected to produce a null result" / 条件 "we call the negative control outcome N 'U-comparable' to Y" / 図2 "N should ideally have the same incoming arrows as Y, except that A does not cause N" / 解釈 "**a null finding of A-N implies that the A-Y association is not likely biased**" / 限界 "**A properly selected negative control is a sensitive, but blunt, tool**" / "the magnitude of bias … cannot generally be inferred from the magnitude of a detected A-N" | — | **「正解が無いときに何を測るか」の唯一の一次的な答え**。我々への写像: **負の対照介入 = 現実で効果が無いと分かっている介入**(例: 建物の内部レイアウトだけ変える・名称だけ変える・エリア外の店を開閉する)。それで在圏や行動分布が動いたら、**その分は機構でなく実装の漏れ**。**プラセボ腕(同構成で seed だけ変える)= 既に持っている**(seed 間 JSD 0.000162)——これは「A/A 検定」であり、負の対照の最小形 |
| **Hut & Masoero (2026)** "Can AI Agents Simulate A/B Test Outcomes? A Validation Framework for Agentic Experimentation", arXiv:2608.02345v3(CC BY 4.0) | §2.1 "**A Simulated Randomized Controlled Trial (S-RCT) replaces live traffic with computational surrogates**" / §2.1 式(4) 2 層分解: "The approximation error is the gap between the simulator's population-level prediction and the true ATE" ・"the finite-sample gap between the realized N_agt-agent estimate and the simulator-population ATE" / "**These two layers are independently addressable: calibration targets the first; principled agent selection targets the second**" / §3 "a benchmark of I=67 historical marketing A/B test treatment pairs" / "**every agent is bound to a specific real customer who participated in the historical experiment**" / §4.2 Phase 1 = "both arms render the control context (**an A/A simulation with zero treatment effect by construction**)" / §5 限界 "in a prospective setting, the triggering population is unknown and **no ground truth is available for calibration**" | **67 件の過去 A/B 試験で逆行検証**。素の基盤モデル: **sign accuracy 0.70 / sign overlap 0.70**(ただし "sign overlap 0.70 falls below the 0.75 a no-conviction forecast attains" = **無内容の予測に負けている**)。効果量は系統的に過大。2 段階事前期較正で二乗予測誤差 **約 77 倍**改善(**67 件でなく 16 件の部分集合**)。被験者内設計で標準誤差 **約 2.4 倍**改善 | **到達点 C の物差しとして、いま世界にある最も近い先行**。3 つ借りる: (1) **「反実仮想の精度」= 過去の実施済み介入を当てられるか**(逆行検証)という定義 (2) **誤差を 2 層に分ける**(エージェント近似誤差 / 部分標本誤差)=「seed を増やせば直る分」と「直らない分」を分離する枠 (3) **A/A シミュレーション(同一文脈を両腕に流す)を較正の第 1 相に置く**= 我々の seed 間 JSD がそのまま第 1 相になる。**警告**: LLM 腕は**向きは当てるが大きさを過大に出す**(既知の「LLM は効果量を大きく出す」と一致)。**「向きと桁に留める」作法は、この論文の実測が裏づけている** |
| **Pangallo & del Rio-Chanona (2024)** "Data-Driven Economic Agent-Based Models", arXiv:2412.16591v1(CC BY 4.0) | §5.1 "Traditionally, validation of ABMs has focused on replicating stylized facts and broad empirical regularities." / "**this comes at the risk of overfitting, as complicated models with many parameters can easily fit a few stylized facts.**" / "**Recently, more rigorous validation has been possible through out-of-sample forecasting.**" / "we consider that stylized facts should be the minimum bar for ABMs." / §5.3 "**Data-driven ABMs should always aim at reproducing the actual dynamics as a baseline**" / "**and then test how alternative policies may have led to different outcomes in some specific historical episode.**" / §4 "What makes this model's counterfactuals trustworthy is that the model was able to reproduce the dynamics" | — | **反実仮想の信頼性は「実際に起きたことを先に再現できたか」に還元される**という明示的な作法。**我々の A(再現)と C(反実仮想)の順序=この作法と同じ**。ただし本論文は**負の対照・プラセボ・自然実験の語を一切使っていない**(全文確認)=**この分野の作法はまだ「まず再現」以上に細かくなっていない** |

#### (c) History Matching for ABM(R-14 の残務を閉じる)

| 出典 | 逐語(原文・節) | 数値 | v2 への含意 |
|---|---|---|---|
| **O'Gara, Kerr, Klein, Binois, Garnett & Hammond** "Improving Policy-Oriented Agent-Based Modeling with History Matching: A Case Study", arXiv:2501.00616(v1 2024-12-31・CC BY 4.0) | §Emulation and History Matching: "**History matching is a technique that uses emulator models to rule out regions of the parameter space which are unlikely to match empirical data**" / 生成過程 "Y = g(θ) + σ²_MD(θ) + σ²_ε" / 非含意度 "|Y − μ̂_g(θ)| / √(σ̂²_g(θ) + σ̂²_MD + σ̂²_ε) ≥ I(θ)" / 多出力 "we use the maximum implausibility measure across Q outputs I_M(θ) = max_{i∈Q} I_i(θ)" / "**Any remaining points after applying the cutoff are deemed 'Not Yet Ruled Out' (NROY)**" / 閾値の出所 "**A common cutoff value I(θ) is 3, inspired from (Pukelsheim 1994) showing that at least 95% of any continuous unimodal distribution is contained within three standard deviations**" / 空 NROY の意味 "if we were not able to identify non-implausible model parameters, this would require revisiting both the model itself and the model discrepancy" | 1 ラン **約 30 秒**。第 1 波 = maximin ラテン超方格 **50 設計点 × 25 反復**、以降 **50 × 20 反復**。**4 波**: 閾値 3.0 → 3.0 → 2.7 → 2.5、NROY 標本 184,974(**7.23%**)→ 142,813(5.58%)→ 54,848(2.14%)→ **21,114(0.82%)**。代理面の評価格子 40⁴ = **2,560,000 点**(実機なら「約 2.5 年」の計算を「数分」で) | **R-14 の空欄を閉じる**。手続きは 4 段: ① 出力を選ぶ(時刻を絞った少数のスカラー) ② 反復を確保して**信号と雑音を分離**(20〜25 反復/設計点) ③ **非含意度 3 で領域を削る** ④ 波を重ねて閾値を締める。**我々への直訳**: 出力 = H1〜H5、σ_MD = **「歪む場所」の宣言(D-72 ①⑦・D-67・D-52)を数量化したもの**——本論文は σ_MD を 0 と置いており、**我々は 0 と置けない**(= 我々の非含意度は分母が大きい = 削られにくい)。**費用**: 1 ラン 30 秒の系で 50×20=1,000 ラン/波。我々は 9.17 h/ラン ⇒ **39 万体では 1 波も回せない**。**5,000 体(0.5 h)でも 1 波 500 h = 21 日**。→ **History Matching は代理(emulator)とセットでしか成立しない**。D-70 (c) の前提 |

---

### 1-4. 関数データ(24 h 曲線・5 エリア)の比較

| 出典 | 逐語(原文・節) | 数値・式 | v2 への含意 |
|---|---|---|---|
| **Myllymäki & Mrkvička (2024)** "GET: Global envelopes in R", *J Stat Softw* 111(3):1–40, doi:10.18637/jss.v111.i03(arXiv:1911.06583v4) | §2.1 定義(式 2): "**A 100(1−α)% global envelope is a set (T^(α)_low, T^(α)_upp) of envelope vectors … such that the probability that Ti falls outside this envelope in any of the d points is equal to α**" / "**global means that the envelope is given with the prescribed coverage 100(1−α)% simultaneously for all the elements of the multivariate or functional statistic**" / §2.1 p 値: "p = Σ_{i=1}^{s} 1(M_i ≤ M_1) / s" / §2.1 図的解釈: 棄却理由は "inspecting for which k = 1,…,d the data vector T1 is outside the global envelope" / §2.1 前提: "**In order to obtain an exact Monte Carlo test … the exchangeability of the test vectors Ti is required.**" / §2.2 推奨: "**for testing, if just possible, we recommend to use a large number of simulations**" / "If the type of extremeness is unknown, then the 'area' measure can be preferred." / 付録 C: 合成帰無では "the classical Monte Carlo test can be liberal or conservative" | 論文中の作例の本数 = **nsim 199 / 999 / 1999 / 2999**。p の下限 = **1/s** | **これが「実測が 3 本の幅の中にあるか」(事前登録 v1.2 (ii))の正典形**。3 つ分かる: (1) **d=120(5 エリア × 24 h)の全点に同時の被覆**を与えるので、**§1-1 の Bonferroni は不要になる**(1 本の大域検定に畳める)。(2) **p = #{M_i ≤ M_1}/s ⇒ seed 3 本 + 実測 1 本 = s=4 では p ≥ 0.25**。**α=0.05 の判定は原理的に不可能**——3 本の帯は**記述**であって検定ではない。α=0.05 には **s ≥ 20(seed 19 本)**、著者推奨の水準なら 199〜2,999 本。(3) **交換可能性が要る**——これは L-B 答申の ECMWF(fair score の前提)と**同じ条件**。空間統計と気象アンサンブルの 2 系譜が独立に同じ前提へ収束している |
| **Currie & Cheng (2016)** §6.1 | "**If the data are not normal … techniques such as bootstrapping … may be helpful**"(Efron & Tibshirani 1998 を指示) | — | 正規性が怪しい JSD・ピーク時刻には**ブートストラップ**。ただし **seed 3 本のブートストラップは無意味**(再標本の台が 3 点)——**ブートストラップの単位を seed でなく「体」または「時刻ブロック」に置く**なら 39 万体から作れる(親案・未リサーチ) |
| **JSD の帰無分布**(χ² 近似・推定量の偏り) | **見つからず**。Grosse et al. (2002) *Phys Rev E* 65:041905 が原典と目されるが **APS 有料・arXiv 版を確認できず**。二次の記述(検索要約)では 2N·ln2·D が自由度 k−1 の χ² に漸近するとされるが、**一次未確認** | — | **空欄**(§3)。当面は **構成ごとの実測帰無**(seed 対の JSD)で代用する現行方針が、文献の裏づけを待たずに正しい側。DTW の帰無分布も**未調査=空欄** |

**我々の数への当てはめ(親が再計算)**

| 判定の形 | 必要 seed 数 | 39 万体(9.17 h/本) | 5,000 体(0.5 h/本) |
|---|---|---|---|
| 記述の帯(検定でない) | 3 | 27.5 h | 1.5 h |
| 大域包絡 α=0.05(s ≥ 20) | **19** | **174 h = 7.3 日** | **9.5 h** |
| 著者の推奨水準(nsim=199) | 199 | 1,825 h = 76 日 | 100 h = 4.2 日 |

→ **α 付きの曲線判定をやるなら 5,000 体の階層で**。39 万体は「帯を描いて記述する」用途に限る。

---

### 1-5. 感度試験の省き方の統計(D-44)

| 出典 | 逐語(原文・節) | 数値・式 | v2 への含意 |
|---|---|---|---|
| **Wan, Ankenman & Nelson (2003)** "Controlled Sequential Bifurcation: A New Factor-Screening Method for Discrete-Event Simulation", WSC 2003, pp.565–573 <https://www.informs-sim.org/wsc03papers/070.pdf> | §1 群スクリーニングの原理: "**The fundamental idea is to identify the important/unimportant factors as a group to save experimental effort**" / 前提 "**In group screening the effects of the factors that are grouped together must have the same sign, and a main-effects model is typically assumed**" / §1 SB: "If the group's effect is important … then the group is split into two subgroups." / §2.3 目的の 2 閾値: "for those factors with effects ≤ Δ0, we require the procedure to control the Type I Error of declaring them important to be ≤ α; and for those factors with effects ≥ Δ1 we require the procedure to provide power for identifying them as important to be ≥ γ" / "Those factors whose effects fall between Δ0 and Δ1 are considered important and we want the procedure to have reasonable, though not guaranteed, power" / §3.3 "The procedure does not require an equal variance assumption, and **is valid with or without common random numbers**." | 検証は合成主効果モデル(K=10)・**1,000 回マクロ反復**・宣言は α と γ の 2 つ | **D-44 の「どこまでやれば十分か」の線を文献の語彙で書ける**。**2 閾値 (Δ0, Δ1)** = 「これ以下なら駆動していないと言ってよい」と「これ以上なら必ず捕まえる」。第200 の指摘「ゲートの文言を検出可能効果量の床つきに書き直す」は、**CSB の Δ0/Δ1 をそのまま採れば済む**。**CRN の有無を問わない**ので §1-2 の制約とも両立 |
| **Shi & Chen (2017)** "Controlled Morris Method: A New Distribution-Free Sequential Testing Procedure for Factor Screening", WSC 2017, pp.1819–1830 <https://www.informs-sim.org/wsc17papers/includes/files/146.pdf> | 抄録: "**the sequential probability ratio test-based multiple testing procedure adopted by CMM enables to identify the factors with significant main and/or interaction effects while controlling Type I and Type II familywise error rates at desired levels**" / §2 Morris 設計: "**B … is a (k+1)×k sampling matrix**" ・ "To obtain N (N ≥ 2) independent elementary effects for each factor, Morris suggests to use N random forms of ΔB" / §2 "Morris (1991) recommends to use a graph plotting μ̂j vs. σ̂j with two lines corresponding to μ̂j = ±2σ̂j/√N … **Such a practice, however, is more of a commonsense rule than a rigorously justified screening method.**" | 数値例: k=20・初期標本 n0=**20**・目標 **α = β = 0.1**・閾値 20 / 30 / 40 / 60・1,000 回マクロ反復。最終標本数は因子ごとに **20(大多数)〜189**(必要なところにだけ増やす) | **Morris の費用は N·(k+1)**。**k=122 では N=4 でも 492 ラン**——現行 OFAT の 244 ランより**高い**。**Morris は我々の D-44 を救わない**。救うのは (i) **逐次**(必要な因子にだけ標本を足す。CMM は 20 → 最大 189) (ii) **群**(SB/CSB)。また Morris の有名な「μ–σ 図」は**厳密な手続きではない**と著者が明言 |
| **ten Broeke et al. (2016)**(既読・L-B) | OFAT 10 反復 / 回帰 5 / Sobol' 0・"The mean output variance over replicates is 0.88% of the output variance over all samples." | — | **反復 0〜10 で済ませる根拠**。Sobol' は反復 0 でよいが**基底標本 N が大きい**(N(k+2))ので k=122 では総ラン数が爆発 |

**親が再計算した D-44 の算術(k=122)**

| 方式 | 必要ラン数 | 39 万体(9.17 h) | 5,000 体(0.5 h) |
|---|---|---|---|
| 現行 OFAT(122 行 × 対照 × 2 seed) | 244 | 2,237 h = **93 日** | 122 h = **5.1 日** |
| Morris N=4(N(k+1)=4×123) | 492 | 4,511 h = 188 日 | 246 h = 10.3 日 |
| Morris N=10 | 1,230 | 11,279 h = 470 日 | 615 h = 25.6 日 |
| Sobol' N=64(N(k+2)=64×124) | 7,936 | 72,773 h = 3,032 日 | 3,968 h = 165 日 |
| **SB/CSB(重要因子 m=5 と仮定)** 設計点 ≈ 2m·log₂(k/m)+2 = **48**・3 反復 | **144** | 1,320 h = 55 日 | **72 h = 3.0 日** |
| **SB/CSB(m=2)** 設計点 ≈ 26・3 反復 | **78** | 715 h = 30 日 | **39 h = 1.6 日** |
| **入力側 JSD の片側規則(D-44 (a))** | **0** | 0 | 0 |

→ **結論 3 つ**: ① **設計を変えても 39 万体では解けない**(最良でも 30 日)。② **5,000 体の階層に移せば SB/CSB で 1.6〜3 日**=実行可能。③ **Morris も Sobol' も k=122 では OFAT より高い**——「Sobol'/Morris なら安い」は k が小さいときの話で、**我々には当てはまらない**(第200 の D-44 追記「Sobol'/回帰なら反復 0/5 で済む」は**反復数の話であって設計点数の話ではない**=誤読の危険。要訂正)。

> **SB の設計点数 2m·log₂(k/m)+2 は親の見積り(未リサーチ・expedient)**。Bettonvil & Kleijnen (1997) 原典は有料で**未読**(§3)。実測の傍証として二次に「281 入力から 15 個を特定」「92 因子を 19 組合せで 10 個に絞った」という記述があるが **一次未確認**。

---

### 1-6. 事前登録の版管理と停止則

| 出典 | 逐語(原文・節) | v2 への含意 |
|---|---|---|
| **Ramdas, Grünwald, Vovk & Shafer (2023)** "Game-theoretic statistics and safe anytime-valid inference", arXiv:2210.01948v2(*Statist. Sci.* 38(4) 掲載と二次にあるが**arXiv 頁には journal-ref なし**) | **抄録のみ**。"**Safe anytime-valid inference (SAVI) provides measures of statistical evidence and certainty**" / "e-processes for testing and confidence sequences for estimation" / "**that remain valid at all stopping times**" / "accommodating continuous monitoring and analysis of accumulating data" / "**optional stopping or continuation for any reason**" / "These measures crucially rely on **test martingales, which are nonnegative martingales starting at one.**" | **「seed を 1 本足してもう一度見る」を正当化する唯一の枠**。α 消費関数(O'Brien-Fleming 等)は**見る回数を先に決める**必要があるが、**信頼列(confidence sequence)は理由を問わず追加・停止してよい**。我々の運用(サーバーが空いたら 1 本足す)にはこちらが合う。**本文未読=手続きは書けない(§3)** |
| **Sargent (2015)** WSC 2015 §7 推奨手順 | 第 1 項: "An agreement be made **prior to** developing the model between (a) the model development team and (b) the model sponsors … that specifies the decision-making approach and **a minimum set of specific validation techniques**" / 第 8 項: "If the simulation model is to be used over a period of time, **develop a schedule for periodic review of the model's validity**" | **事前登録の版管理は V&V の推奨手順の第 8 項そのもの**。「開封後は追記のみ」(v1.1 §5)は第 1 項に対応。**足りないのは「定期再検証の日程」**——第3陣・次の封印データの取得時期を事前登録に書く |
| **Currie & Cheng (2016)** §5.2 | 相対精度の反復数: "the number of replications, n^r_ε … is the minimum value of p such that p ≥ n and t_{1−α/2;p−1}·S(n)/(|ȳ(n)|·√p) ≤ ε/(1+ε)" / 注意 "**There is the potential for inaccuracy in the suggested values of n … especially for small values of n**" | **n=3 で推定した S(n)・ȳ(n) から n を逆算するのは著者自身が「不正確になりうる」と警告**。第204 の「N=(CV/r)² で 2.6 本 → 3 本」は**この警告の範囲内**(自由度 1〜2 の CV)。**3 本目が揃ったら CV を取り直して N を再計算する**のが作法 |
| **Siepe et al. (2024)**(既読・L-B) | 反復数は MCSE 目標から逆算して事前登録で宣言 | 既存 |
| **O'Brien-Fleming (1979) / Lan & DeMets (1983)** の α 消費 | **一次未確認**(有料)。**空欄**(§3) | — |

---

## 2. 決定アジェンダの候補(ユーザー判断待ち・親の推奨つき)

> 規律: 以下はすべて**提案**。実装・台帳更新・設計書改訂は含まない。すべて**追加ラン 0 本**で実行できる(S5-a を除く)。

### S-1. 事前登録 v1.3(**開封前・seed 3 本目の完走前に決める**)

| # | 決める項 | 選択肢 | 親の推奨 | 費用 |
|---|---|---|---|---|
| **S1-a** | **多重比較の扱い**(H1〜H5 の家族) | (a) 何もしない(現行) / (b) **Bonferroni で個別 α=0.01**(家族 95%) / (c) **Holm**(段階的・(b) より強い) / (d) 「5 指標は独立な主張でなく 1 つの主張の 5 面」と宣言して家族単位の補正を**しない**理由を書く | **(b)+(d) の併記**。数を出すときは Bonferroni 版と非補正版を**両方**表に載せ、「合否は非補正で、家族の主張は Bonferroni で」と**用途を分けて宣言**する | 0 ラン |
| **S1-b** | **「帯の中にある」の検定形** | (a) 現行(点推定と線の比較) / (b) **90% CI の上端が線の内側**(TOST 片側・Lakens) / (c) **Sargent の区間仮説検定**(α と β の危険曲線つき・一標本) | **(b) を必須・(c) を併記**。(b) は追加ラン 0 で今日できる。(c) は β(=不正なモデルを通す確率)を初めて数える | 0 ラン |
| **S1-c** | **深夜(H3 代替)の扱い** | (a) 現行の線のまま合否を出す / (b) **「3 seed では深夜は ±18.6%(家族 95%)までしか言えない」と事前に宣言**し、深夜は**記述のみ**に格下げ / (c) seed を増やす | **(b)**。(c) はサーバー返却で不可 | 0 ラン |
| **S1-d** | **曲線の帯の位置づけ** | (a) 「実測が 3 本の幅の中にあるか」を**検定**として書く / (b) **Monte Carlo 検定の p 下限 1/s を明記し、s=4 では p ≥ 0.25 = 検定ではないと宣言**した上で**記述**として出す | **(b)**。(a) のまま出すと層2 検収で落ちる | 0 ラン |
| **S1-e** | **fair 化(有限 M の罰)** | (a) 生の JSD / (b) **(1+1/M) の補正を併記**(M=3 → +33.3%) / (c) JSD の推定量の偏りを解析的に引く | **(b)**。(c) は帰無分布の一次が未確認(§3)なので**今は採らない** | 0 ラン |
| **S1-f** | **停止則** | (a) 3 本で確定(現行 v1.2) / (b) **「開封後に seed を足しても本 holdout の主張は変えない」を明記**(=逐次解析にしない) / (c) 信頼列(SAVI)を採る | **(a)+(b)**。(c) は本文未読で手続きが書けない | 0 ラン |

### S-2. D-70(次の性能ゲート)への追加材料

| # | 論点 | 本答申が足したこと | 親の推奨 |
|---|---|---|---|
| **S2-a** | **(d)「共通乱数で N を減らす」の評価** | **腕ごとにプロンプトが変わる我々は部分 CRN しか持てず、実測利得は分散 −5.6%(実効標本 1.06 倍)**(Murphy 2013)。完全 CRN の −93.6% は**同じ個体に同じ乱数を同じ用途で流せる系**の数 | **(d) を「N を減らす道」から降ろす**。残すなら**エンジン側の乱数を用途別副流に分ける**実装(母集団抽出・初期配置・p_notice・繰り延べ)を先に決め、**効果は 5% 級と見積もる**。**holdout には CRN は一切効かない**ことを台帳に明記 |
| **S2-b** | **判定に要る N の再計算** | 大域包絡 α=0.05 に **seed 19 本**。5 指標 Bonferroni で深夜を 2% で言うには CV 0.0325 で **N=(573·0.0325/2)² ≈ 87 本** | **39 万体で α 付きの判定は諦める**。α 付きは **5,000 体の階層**(0.5 h)へ。39 万体は「1 回の記述」に使う |
| **S2-c** | **(c) surrogate への前提** | Dyer 2023: **観測ランだけで学習した代理は介入効果を逆向きに出す**(AMSE 3.35 vs 18.47) | **(c) を将来やるなら「介入下のランで学習する」を前提条件として今のうちに宣言**しておく(後から足せない性質) |
| **S2-d** | **History Matching の位置** | 1 波 = 50 設計点 × 20 反復 = 1,000 ラン。39 万体では 1 波も回せない | **D-70 (c) の代理層が入るまで History Matching は着手しない**。入れる順序は「代理 → 非含意度 → 波」 |

### S-3. C8 の解析計画(ablation の対照)

| # | 決める項 | 親の推奨 |
|---|---|---|
| **S3-a** | 対照の型 | **対応のある差**(同 seed の対)で CI を出す(Currie §6.1)。腕間 JSD は既に seed 差の 700 倍なので**検出は問題ない**——問題は「駆動していない」側 |
| **S3-b** | 「駆動していない」の言い方 | **CSB の 2 閾値 (Δ0, Δ1) を宣言**し、「Δ0 以下 = 駆動していないとみなす」「Δ1 以上 = 必ず捕まえる」「間は保証しない」と書く。**Δ0 は seed 間 JSD の実測(在圏 0.000162 bits / 行動 24 語 0.00007)に定数倍を掛けて置く**のが自然(親案・未リサーチ) |
| **S3-c** | 多重性 | ablation の腕数が増えたら **familywise(CMM の言う Type I/II familywise)** で管理。腕 1 本ずつ α=0.05 では 10 腕で家族 α ≈ 0.40 |
| **S3-d** | 帰無参照 | **構成ごとに実測で置く**(第202 の指摘)は文献的にも正しい(GET の「交換可能性」= 帰無を外から借りられない) |

### S-4. 反実仮想の主張の作法(到達点 C)

| # | 決める項 | 親の推奨 |
|---|---|---|
| **S4-a** | **主張の型** | **「向きと桁」に留める**を規律として明文化。根拠は Hut & Masoero 2026 の実測(**向きは 0.70 で当たるが無内容予測の 0.75 に負ける・大きさは系統的に過大**)+ 既存の「LLM は効果量を大きく出す」 |
| **S4-b** | **物差し** | **S-RCT の 2 層分解**を採る: 誤差 = ①エージェント近似誤差(seed を増やしても消えない)+ ②部分標本誤差(seed で消える)。**いまの seed 間 JSD は ② の測定であって ① の測定ではない**——この区別を計器盤 G-8 に入れる |
| **S4-c** | **負の対照** | **効果が無いはずの介入を 1 本足す**(例: 建物名だけ変える・エリア外の店舗を開閉する・提示順だけ入れ替える)。動いたらその分は実装の漏れ。**A/A(同構成・別 seed)は既に持っている**=最小形は達成済み |
| **S4-d** | **逆行検証の候補** | 渋谷で**実施済みの介入**(施設の開業・閉業・工事による動線変更・イベント)を当てられるかを、**次の封印データの取得時に先に**設計する。Pangallo & del Rio-Chanona の作法「まず実際の動きを再現し、次に特定の歴史的挿話で別の政策を試す」 |
| **S4-e** | **ABM を因果の枠に置く根拠** | Marshall & Galea 2015 の「**干渉があるときに ABM が正当化される**」を到達点 C の位置づけの出典にする(**抄録のみ=親一次確認が要る**) |

### S-5. D-44(感度試験の省き方)

| # | 決める項 | 親の推奨 |
|---|---|---|
| **S5-a** | **階層の移動** | **感度試験を 5,000 体の階層へ移す**。39 万体では最良の設計(SB/CSB)でも 30 日。5,000 体なら SB/CSB で **1.6〜3.0 日**、現行 OFAT でも 5.1 日 |
| **S5-b** | **設計の選択** | **群スクリーニング(SB/CSB)**。**Morris も Sobol' も k=122 では OFAT より高い**(492〜7,936 ラン)——第200 の追記は**反復数の話を設計点数の話と取り違えている**ので訂正が要る |
| **S5-c** | **ゲートの文言** | 「expedient は感度試験で結果を駆動していないことを証明する」→ **「expedient は、宣言した Δ0 以下の効果しか持たないことを、宣言した検出力 γ で示す」** に書き直す(CSB の語彙) |
| **S5-d** | **0 ラン規則(D-44 (a))** | **維持**。文献的にも「入力側の分散が条件間分散に比べて小さいことを測って追加不要を示す」(ten Broeke)と同型。**ただし片側**(駆動していないことは示せるが、駆動していることは示せない) |
| **S5-e** | 群を作る前提 | CSB の前提「**群にまとめる因子の効果は同符号でなければならない**」。122 行を束ねるなら**符号の向きを先に宣言**する必要がある=束ね方の設計が先 |

---

## 3. 空欄(見つからなかった / 一次未確認)

1. **Robinson & Froese (2004)** の本文(有料)。抄録の「検出力が低いほど合格しやすい」は逐語で取れたが、**同値検定をモデル検証に当てる具体手続き(ε の決め方・回帰版)は未読**。続報 Robinson, Duursma & Marshall (2005) *Tree Physiol* 25:903–913 も未読。
2. **Marshall & Galea (2015)** の本文(有料)。**識別仮定(consistency / exchangeability / positivity)を ABM にどう写すかの節が未読**——到達点 C の理論的位置づけはここに依存。無料全文の所在を未確認。
3. **Ramdas et al. (2023)** SAVI の本文(抄録のみ)。**信頼列の具体的な構成・我々の seed 追加に当てはめる手続きは書けない**。journal-ref も arXiv 頁には無い。
4. **O'Brien-Fleming (1979) / Lan & DeMets (1983)** の原典。α 消費関数の形・境界の式は**一次未確認**。
5. **Bettonvil & Kleijnen (1997)** *EJOR* 96(1):180–194 の本文(有料)。**逐次二分法の必要ラン数の式は一次未確認**——§1-5 の 2m·log₂(k/m)+2 は**親の見積り(expedient)**。二次に「281 入力 → 15 個」「92 因子を 19 組合せ」があるが未確認。
6. **Morris (1991)** *Technometrics* 33(2):161–174 の原典(有料)。**N(k+1) の費用式は Shi & Chen 2017 の記述(B が (k+1)×k 行列)から復元した二次**。
7. **JSD の帰無分布**: Grosse et al. (2002) *Phys Rev E* 65:041905 は APS 有料で読めず、**arXiv 版を見つけられなかった**。2N·ln2·D の χ²(k−1) 漸近は**二次(検索要約)のみ**。**JSD 推定量の有限標本偏り(Miller-Madow 型の補正)も未調査**。
8. **DTW の帰無分布・ブートストラップ CI**: **未調査**(時間切れ)。Sakoe & Chiba (1978) も未確認。
9. **関数データの band test の別系統**(Cuevas et al. 2004 の functional ANOVA・Degras 2011 の同時信頼帯・Pini & Vantini の区間毎検定): **未調査**。GET(大域包絡)1 本で答えたので、他系統との比較ができていない。
10. **Benjamini & Hochberg (1995) / Holm (1979)** の原典: **一次未確認**(有料)。§2 S1-a の (c) Holm を選ぶなら先に読む必要。FDR を 122 行の screening に当てる話も未調査。
11. **Balci & Sargent (1984)** "Validation of simulation models via simultaneous confidence intervals" の原典: 未読(Sargent 2016 が引くのみ)。**Balci & Sargent (1981)** の費用・危険解析も未読。
12. **Sargent (2015b)** *J Simulation*, doi:10.1057/jos.2014.30(区間統計手続きの原典)と **Sargent, Goldsman & Yaacoub (2016) 付録 A・B の手続き本文**: 未読。S1-b (c) を採るならここが必読。
13. **Wellek** *Testing Statistical Hypotheses of Equivalence and Noninferiority*(書籍・有料): 未読。TOST の一様最強不変性の主張は Lakens 経由の二次。

→ すべて [research-backlog.md](research-backlog.md) の R-25 の下に置く候補。**R-14 の「History Matching for ABM(2501.00616)」は本答申 §1-3(c) で閉じた**。

---

## 4. lit README に足す行(索引の末尾に追加する候補)

```
| [validation__sargent2016_interval-test](validation__sargent2016_interval-test.md) | 検証とV&V #22 / 統計学 #23 | B(サブ実読・第208・親未確認) | **「帯の中にある」を検定する正典**=区間仮説検定・モデル製作者危険 α / 利用者危険 β・α+β=1 の作例 |
| [stats__lakens2017_tost-equivalence](stats__lakens2017_tost-equivalence.md) | 統計学・因果推論 #23 | B(サブ実読・第208・親未確認) | **TOST の手続き**・「90% CI が帯の内側」で同値・**3 seed での必要帯 = 偏り + 1.686·CV** |
| [stats__currie-cheng2016_output-analysis](stats__currie-cheng2016_output-analysis.md) | 統計学・因果推論 #23 / OR | B(サブ実読・第208・親未確認) | **Bonferroni の作例(5 比較 × 90% → 家族 50%・個別 98% が要る)**+CRN+対応のある差の CI |
| [causal__lipsitch2010_negative-controls](causal__lipsitch2010_negative-controls.md) | 統計学・因果推論 #23 | B(サブ実読・第208・親未確認) | **正解が無いときの検証法の原典**・U-comparability・「鋭いが鈍い道具」 |
| [stats__ogara2025_history-matching-abm](stats__ogara2025_history-matching-abm.md) | 統計学・因果推論 #23 / ABM方法論 #21 | B(サブ実読・第208・親未確認) | **R-14 の残務を閉じる**・非含意度と閾値 3・4 波で NROY 7.23%→0.82%・**代理なしでは成立しない** |
| [stats__myllymaki2024_global-envelopes](stats__myllymaki2024_global-envelopes.md) | 統計学・因果推論 #23 | B(サブ実読・第208・親未確認) | **曲線の同時帯**=Bonferroni を 1 本に畳む道・**p の下限 1/s ⇒ 3 seed では α=0.05 不可**・交換可能性 |
| [stats__wan2003_controlled-sequential-bifurcation](stats__wan2003_controlled-sequential-bifurcation.md) | 統計学・因果推論 #23 / ABM方法論 #21 | B(サブ実読・第208・親未確認) | **D-44 の「十分の線」の語彙**=2 閾値 Δ0/Δ1・群スクリーニング・**CRN の有無を問わない** |
| [validation__hut2026_simulated-rct](validation__hut2026_simulated-rct.md) | 検証とV&V #22 / 計算社会科学 #25 | B(サブ実読・第208・親未確認) | **到達点 C の物差しの唯一の近い先行**・67 件の逆行検証・**向き 0.70(無内容予測 0.75 に負ける)**・誤差の 2 層分解 |
```

---

## 5. 親が最初に一次確認すべき 3 件(§2 の決定に直接効く順)

1. **Sargent, Goldsman & Yaacoub (2016) §2.2.3 と付録 A**(<https://www.informs-sim.org/wsc16papers/016.pdf>)—— S1-b (c) の可否が「一標本の区間統計手続きが KDDI の 1 観測に適用できるか」で決まる。**本答申は付録 A の逐語を取っていない**。
2. **Myllymäki & Mrkvička (2024) §2.1 の p = Σ1(M_i ≤ M_1)/s**(arXiv:1911.06583v4)—— S1-d と S2-b の根拠。**「seed 3 本では p ≥ 0.25」は本答申の最も強い主張**で、ここが崩れると事前登録 v1.3 の形が変わる。
3. **Murphy et al. (2013) の完全 CRN −93.6% / 部分 CRN −5.6%**(doi:10.1111/1475-6773.12044)—— S2-a で **D-70 (d) を降ろす**根拠。数値 1 つで方針が変わるので、表の該当行の再計算まで。

> 次点(§1-5 の算術に効く): **Bettonvil & Kleijnen (1997) の必要ラン数の式**が読めれば、SB の設計点数 2m·log₂(k/m)+2 という親の見積りを実測値に置き換えられる。有料なので R- 番号で保留。
