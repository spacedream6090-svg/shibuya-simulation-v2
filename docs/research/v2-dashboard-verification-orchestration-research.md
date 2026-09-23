# R14 忠実度計器盤・検収戦略・実験オーケストレーション — 事前リサーチ答申(正典化)

<!-- hdr:v1 -->
- **分野**: 検証とV&V・UQ #22 / 予測科学(アンサンブル) #24 | **重要度**: P0(親判断・2026-09-15 第191)
- **一次確認**: **A** = 親検収済(逐語引用または再計算つき) — 親検収(2026-09-08)。逐語引用つき。空欄 6 件(R-14)
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **分野地図**: [v2-discipline-map.md](v2-discipline-map.md)

> **親検収(Fable・2026-09-08)**: サブ(Opus 5・子サブなし・リポ書込なし・ハーネスがファイル書込を遮断=テキスト返答を親が保存)の最重要5件を親が原典で確認した。✔=一致。
> - ✔ **TRACE 8要素(Grimm et al. 2014, Ecol. Model. 280:129-139・無料PDF親抽出)**: 1 Problem formulation(意思決定の文脈・利害関係者・問い・適用範囲)/2 Model description(ODD推奨)/3 Data evaluation("The quality and sources of numerical and qualitative data used to parameterize the model, both directly and inversely via calibration, and of the observed patterns that were used to design the overall model structure")/4 Conceptual model evaluation(単純化仮定の批判的評価)/5 Implementation verification/6 Model output verification/7 Model analysis("(1) How sensitive model output is to changes in model parameters (sensitivity analysis), and (2) how well the emergence of model output has been understood")/8 Model output corroboration("How model predictions compare to independent data and patterns that were not used, and preferably not even known, while the model was developed, parameterized, and verified")。「六つのevaludation要素はAugusiak et al. (2014)参照」=要素3-8がevaludationの6要素。Augusiak 2014の要旨自体はScienceDirect 403・Semantic Scholarで要旨非公開=未読(TRACE本文の定義で代替)。
> - ✔ **hmer(arXiv 2209.05265・Iskauskas et al.・PDF親抽出)**: 実行不能度 "I²_i(x) = (E_Di[f_i(x)] − z_i)² / (Var_Di[f_i(x)] + Var[e_i] + Var[ε_i])"(Vernon et al. 2014)・多出力は最大値 I_M(x)=max_i I_i(x)・"if I(x) is 'small' then we cannot rule out the possibility that x would give rise to a good match to data; x is deemed non-implausible, or not-yet-ruled-out (NROY)"・カットオフ "We may appeal to Pukelsheim's 3σ rule (Pukelsheim 1994), which suggests that for a unimodal continuous distribution 95% of the probability mass is within 3σ of the mean, to suggest a good starting point for a cut-off is I = 3"・波 "We apply a series of iterations, called waves, which discard regions of the parameter space at each wave"。
> - ✔ **AgentSociety(arXiv 2502.08691v2)**: "To facilitate research collaboration, we opt for mlflow with centralized server capabilities, rather than local storage-based metric recording tools like tensorboard" / "we adapt the mlflow API and implement a parallel-safe metric logging utility class and functions"。GUIはDB+MQTTに接続し対話・アンケート投下が可能。
> - ✔ **Generative Agents(arXiv 2304.03442v2)**: 評価者100名(Prolific)・5条件(完全/内省なし・計画なし/内省なし/観測・内省・計画なし/人間クラウドワーカー)・TrueSkill(μ,σ)→Kruskal-Wallis→Dunn→Holm-Bonferroni・完全版 μ=29.89(σ0.72)・観測内省計画なし μ=21.21(0.70)・人間 μ=22.95(0.69)・d=8.16("eight standard deviations")・H(4)=150.29, p<0.001。サブの数値は正しい(dの大きさはTrueSkill尺度によるもの)。
> - 空欄のまま: Augusiak 2014要旨・Grimm & Railsback 2012 POM定義文・Science 2005・SBC(Stan)は要約経由・Siepe et al. 2024(321記事/31.2%・反復回数の式)・ECMWF spread-skill原文・Snakemake/Nextflow/Ray原文・SRE本の逐語(要約経由)・OASIS NRMSE・EconAgent r=−0.619・ADEMP-PreRegの項目リスト・History Matching for ABM(arXiv 2501.00616)・2022年評価記述標準プロトコル・LLMエージェント評価サーベイ(2507.21504)。いずれも設計書では「要約経由」として扱い、採用は骨格のみ(数値の引用はしない)。
> - 適用先: 計器盤・検収・オーケストレーション設計書(草案) docs/design/v2-dashboard-verification-orchestration.md。

> 作成: 2026-09-08 / 実行=Opus 5 リサーチサブ / 等級: [A]原文実読(サブは該当なし・親が5件昇格)・[B]WebFetch要約経由・[C]検索スニペット・[未読]。

## 要約(6行)
1. ABM検証の既成枠組み=POM(多パターン同時照合=フィルタ)+evaludation 6要素+TRACE 8ブロック。v2のパターン台帳はPOMの直系、計器盤はTRACEの model output verification(較正側)と corroboration(holdout側)を別面に分ければ枠組みが揃う。
2. ゲート(合否)と報告(観察)の分離は、SREの「症状でページ・原因はデバッグ用」「全pageはactionable」がそのまま転用可。ABM文献側に明文化例なし=v2独自(expedient)。
3. 合否線を事前に引く既成手法=History Matching(implausibility I≤3・NROY・波)とSBC(rank一様性・片側性: 落ちたら不合格、通っても合格ではない)。
4. 多ラン管理の最小仕様=NetLogo BehaviorSpace(掃引×repetitions×reporters×stop条件・run番号→seed・並列時のRNG衝突警告・table逐次書き出し)。Covasim MultiSim(n_runs/reseed)・MATSim(固定seedでも共進化で実質非決定)も参照点。
5. 失敗再開・来歴=Snakemake/Nextflow(中間結果ディスク書き・自動リトライ)・Ray Tune(checkpoint再開)。実験追跡=AgentSocietyがmlflow採用(親確認)。
6. 事前登録=ADEMP-PreReg(Siepe et al. 2024・OSF)。LLM社会シム側の計器=Generative Agents(TrueSkill+Kruskal-Wallis)・OASIS(scale/depth/max breadthのNRMSE)・EconAgent(Phillips曲線/Okun法則の符号と相関)。

## 1. ABM検証の枠組み(POM・evaludation・TRACE・SBC・History Matching)
- POM: 複数パターンをフィルタとして用いる多基準の設計・選択・較正(Grimm & Railsback 2012 [C])。検証用パターン群と妥当性確認用パターン群の分離(Annals of Botany 2018 [C])。弱いパターンを複数束ねると強い単一パターン以上の情報(Grimm系譜 [C])。
- evaludation 6要素=TRACE要素3-8(親確認・上記)。
- SBC(Stan Users Guide [B]): rank一様性・χ²・bin期待≥5・明示p値の合否線なし。sbi tutorial [C]: U字=過分散・山形=過小分散・偏り=バイアス。「必要条件であって十分条件でない」。PLOS One 2024 [B]: 較正手続きの検収を本体検証から分離・p>0.05で一様示唆・CRPS。
- History Matching(hmer・親確認): I²=(E−z)²/(Var_emu+Var_obs+Var_disc)・I_M=max・I≤3(Pukelsheim 3σ≒95%)・波で棄却。ABMへの適用(arXiv 2501.00616)は未読。

## 2. 多ラン/アンサンブル管理
- BehaviorSpace [B]: "All combinations of the specified values will be run." / `random-seed (474 + behaviorspace-run-number)` / スレッド既定 floor(0.75×CPU) / 並列時「very, very small chance…same random number generator state」/ table=逐次書き出し・spreadsheet=終了時のみ。
- Covasim MultiSim [B]: n_runs・reseed(単一simは既定true/リストは既定false)。
- MATSim [C]: config固定seedで同一乱数列、ただし共進化で実質非決定(出典2本は別)。
- ECMWF [C]: spread-skill ratio(アンサンブル幅/RMSE≈1)・CRPS(reliability/resolution分解)・スコアカード様式(未読)。
- Snakemake/Nextflow [C]: 中間結果ディスク書き・自動リトライ。Ray Tune [C]: checkpoint再開。MLflow 4構成・W&B(Runs/Projects/Artifacts・Sweeps)[C]。AgentSociety mlflow(親確認)。SimEngine(arXiv 2403.05698)未読。

## 3. 事前登録
- ADEMP-PreReg(github bsiepe/ADEMP-PreReg [B]): Monte Carloシミュレーション研究向け汎用テンプレ(Aims/Data-Generating Mechanisms/Estimands/Methods/Performance Measures・OSF登録可)。理由文 "researchers have ample degrees of freedom at every step of the study pipeline" / "it is rather easy to (inadvertently or not) change a data-generating mechanism until it favors a method of choice"。
- Siepe et al. 2024 Psychological Methods [C]: 321記事中31.2%がシミュレーション研究・反復回数の正当化/Monte Carlo誤差/再現コードの不足・反復回数を目標MCSEから逆算する式(未確認)。
- 「HARKing」をシミュレーション文脈で扱う一次文献は特定できず(空欄)。

## 4. LLMエージェント・シミュレーションの評価指標
- Generative Agents(親確認): believability 5領域(self-knowledge/memory/plans/reactions/reflections)インタビュー・100評価者・TrueSkill→KW→Dunn→Holm-Bonferroni・人間を1条件として並置。
- OASIS(2411.11581v4 [B]): scale/depth/max breadth のNRMSE(誤差約30%前後)・群極化=GPT-4o-mini判定・同調=post score・コスト表(5×A100・100万体で27.0 A100/18h per step)。
- EconAgent(2310.10436v3 [C]): Phillips曲線/Okun法則の再現(r=−0.619)・ルールベースは符号を誤る・知覚アブレーションで変動が減少。
- AgentSociety(親確認): mlflow・GUI(対話・アンケート)・性能節(messaging throughput/latency)・ツールボックス(インタビュー・サーベイ・介入)。
- サーベイ(2507.21504・2507.19364)未読。

## 5. 計器盤UIの設計原則(SRE)
- Google SRE本 Ch.6 [B]: 4ゴールデンシグナル(Latency/Traffic/Errors/Saturation)・通知3階級(pages/tickets/logging)・「症状でページ、原因はデバッグ」・"every page be 'actionable'"。バーンレート警報(SRE Workbook Ch.5・未読・二次記事 [C])。

## サブの適用提案(A-F・親が設計書草案で採否を整理)
A 計器盤3面(較正面=報告のみ/holdout面=唯一のゲート・k*/運用面=赤黄緑・actionableのみ)+SBC片側性の明記/B 検収=TRACE 8ブロックを工程別受入基準表に写像/C オーケストレーション=manifestにEnsembleSpec(seed群)とSweepSpec(掃引)の2型・seed=f(manifest_sha, run_index)・逐次書き出し既定・完了済みラン表で再開・mlflow Tracking採用候補/D アンサンブル計器=CRPS+spread-skill+スコアカード様式/E 事前登録=ADEMP 5見出し+ラン本数のMCSE逆算+リポ内凍結ファイル/F 分布一致(NRMSE・JSD)+符号一致の最小ゲート+believability(人手要)+コスト表。

## 参照一覧
WebFetch [B]: mc-stan.org SBC・arxiv 2502.08691(abs/v1)・docs.netlogo.org/behaviorspace・arxiv 2411.11581v4・arxiv 2304.03442(abs/v2)・sre.google Ch.6・github ADEMP-PreReg・cos.io blog・PLOS One 0315429。失敗→親再取得: TRACE 2014 PDF(親抽出✔)・arxiv 2209.05265 PDF(親抽出✔)。WebSearchのみ [C]: PMC3223804・PMC5906917・brv.12729・science.1116681・S0304380013005450・S0304380014000611・S0304380022001685・jasss 23/2/7・sbi tutorial・d-nb.info MATSim・arxiv 2506.07345・Covasim docs・ECMWF 15865/166/festschrift・AMS WAF 2000・ACM 3676288.3676290・Ray docs・wandb・PMC7616844・pubmed 39541533・PMC11525092・arxiv 2310.10436v3・2507.21504・2507.19364・2403.05698・2602.15317・incident.io・Gelman A6n41。親再確認: 2502.08691v2・2304.03442v2・TRACE PDF・hmer PDF・Semantic Scholar(Augusiak要旨非公開)。
