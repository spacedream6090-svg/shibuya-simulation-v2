# 古典的社会シミュレーション vs LLM 社会シミュレーション — 何が変わり、何が変わらないか(L-CLS・2026-09-17)

<!-- hdr:v1 -->
- **分野**: 計算社会科学 #25 / ABM方法論 #21 / 科学哲学 #26 | **重要度**: P0(親判断)
- **一次確認**: **B** = 出典あり・空欄を明示(§4 に集約)。本答申の中心 13 本は**サブが本文を実読**(うち 4 本は PDF を pymupdf で全頁抽出)。**親の一次確認は未実施** **→ 親確認 3 件(第214)**: PIMMUR(arXiv 2509.18052 v4・2026-09-10)抄録「Across 576 studies reported in 350 recent papers」「65.2% of cases」「50.6% of prompts」+版注記「Added more studies in our systematic audit (350 papers; 576 simulations)」/ Anthis et al. 2025(2504.02234v2)§4.5.2「We have not yet seen, but we encourage, preregistration of LLM simulation predictions」・§1 Hewitt 2024「70 preregistered」「91% of the variation in average treatment effects」/ Project Sid §5.2「agents reduced taxes paid from 20% to 9%」(憲法改正後)・§8.3「29 agents: 25 constituents」+3 influencers+1 manager・§5.3「20 priests that worship Pastafarianism」(500 体中)。他は親未確認
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **分野地図**: [v2-discipline-map.md](v2-discipline-map.md) ・ **文献**: [lit/](lit/)

> 位置づけ: ユーザー依頼 2026-09-17。**外側(文献)の物差しだけを作る**。この repo が実際にどれを満たしているかの判定は本書の仕事ではない(repo 側の反映監査は別レーン)。§3 の判定基準 10 項にも**この repo の自己評価は書かない**。
> 読み方: 引用は原文の逐語(≤125 字)。節・段落・表番号を付けたものは取得範囲で確認済み、付かないものは**位置が確定していない**。数値の再計算・図からの読み取りが残る箇所は §4 に全部書いた。

---

## 0. 3 行の結論

1. **変わっていない要求のほうが多い**。再現性(Axtell の 3 段)・複数パターン同時照合(POM)・感度と摂動・目的の宣言・識別問題の自覚は、1971〜2019 年の古典 ABM が既に要求していたもので、LLM 系はそれを**免除されていない**。LLM 系の「新しい規律」と呼ばれているもの(頑健性監査・事前登録・多ラン報告)は、ほぼ全部が古典側の要求の**再発見か、LLM 固有の摂動軸への拡張**である。
2. **本当に新しく壊れたのは 3 つだけ**。(a) **決定論**——古典 ABM では「seed を保存して再実行すれば完全に同じ」が既定値だった(Epstein 2006 が明言)。(b) **事前知識の漏洩**——モデルが答えを既に知っている可能性は古典 ABM には無い失効経路で、しかも「創発」と**観測上区別できない**(Barrie & Törnberg 2025)。(c) **費用**——古典 ABM は 1.2 億体を 32 コア 1 台・半日で回す(Axtell 2016)。LLM 系は 100 万体・1 step に A100 27 枚 × 18 時間(OASIS)。
3. **本当に新しく可能になったのは 1 つ**。**行動則を書かずに役割知識を重みから引き出せる**こと(Argyle 2023 の algorithmic fidelity / Horton 2023 の homo silicus)。古典 ABM は「単純な規則で複雑な結果」(Axelrod の KISS)を要求せざるを得なかったが、それは**規則を人が書いていたから**である。ただしこの利得は (b) と表裏で、**同じ性質が「創発」の主張を無効化する**。

---

## 1. 問いごとの表

### 1-1. 古典の系譜が「良いモデル」に要求したもの(問い 1)

| 文献 | 一次確認 | 要求したこと(逐語または節) | この物差しでの位置 |
|---|---|---|---|
| **Schelling 1971**(*J. Math. Sociol.* 1(2):143–186・DOI 10.1080/0022250X.1971.9989794) | **二次**(原典は tandfonline 403 で未取得。Axelrod 1997 §2 と Epstein 2006 §IV の実読を経由) | 閾値(「近隣の 1/3 超が別種なら動く」=Axelrod の要約)から分居が出る。Epstein 2006 §IV 評: 「important because—even though highly idealized—it offers a powerful and counter-intuitive insight」 | **単純さの価値**の原点。ただし Epstein は「right in all details ではない(そう主張してもいない)」と明記 |
| **Epstein & Axtell 1996 / Epstein 1999・2006**(Sugarscape・生成社会科学) | **実読**(2006 Remarks・27 頁) | `∀x(¬Gx ⊃ ¬Ex)`「If you didn't grow it, you didn't explain it」。**逆は不成立**:「generative sufficiency is a necessary, but not sufficient condition for explanation」「the mapping … might be many-to-one」 | **生成 ≠ 説明**。生成できたものは **candidate explanation** |
| **Axelrod 1997/2003**(KISS・docking) | **実読**(2003 更新版・19 頁) | 「The complexity of agent-based modeling should be in the simulated results, not in the assumptions」。**ただし目的依存**:「if a simulation is used to train the crew of a supertanker … simplicity of the model is not [important]」 | **単純さは目的条件つき**。再現の 3 段(numerical identity / distributional equivalence / relational equivalence) |
| **Axtell, Axelrod, Epstein & Cohen 1996**(docking) | **二次**(Axelrod 1997 §4 の実読経由。CMOT 原典は未取得) | 同値検定の帰無の罠:「it creates an incentive for investigators to test equivalence with small sample sizes」→「specify in advance the magnitude of the difference that will be considered meaningful」 | **TOST と事前登録の 1996 年版** |
| **Gilbert & Troitzsch**(教科書の検証章) | **未取得(空欄)** | — | §4 の残務 |
| **Bonabeau 2002**(*PNAS* 99(S3):7280–7287) | **実読**(PMC 全文) | 3 利点「(i) ABM captures emergent phenomena; (ii) … natural description …; (iii) ABM is flexible」。5 条件(相互作用が複雑/空間が本質で位置が動く/母集団が異質/相互作用の位相が複雑/学習と適応)。「**Averages will not work.**」 | **なぜ ABM でなければならないか**の門 |
| **Macal & North**(ABM の tutorial) | **実読**(WSC 2009 版 PDF・pymupdf。**J. Simulation 4:151–162 版は Springer 認証壁で未取得**) | エージェントの**必須 3 性質**(autonomous and self-directed / modular or self-contained / social, interacting with other agents)+**任意 4 性質**(環境に住む・明示的な目標・学習と適応・資源属性)。「there is no universal agreement on the precise definition of the term "agent"」。ABMS が広がった理由 4 つ(相互依存の複雑化/従来扱えなかった系/**ミクロデータの粒度**/計算力) | **「agent-based」を名乗る条件**。目標や適応は**必須ではない**と明記 |
| **Grimm 2005 POM / ODD 2020** | **既読**([[lit/abm__grimm-railsback2012_pom-multiscope]]・[[lit/abm__grimm2020_odd-observation]]) | 「1 つのパターンは間違った理由でも合う」(equifinality)・弱いパターンを束ねる・パターン=却下のフィルタ。ODD S1: 個体 trace を出せ・平均だけか分布も見たかを書け・**HARKing 禁止** | **多重照合**が等結果性への処方 |
| **Windrum, Fagiolo & Moneta 2007**(JASSS 10(2)8) | **実読** | 較正・検証の 3 系統(Indirect Calibration / Werker-Brenner / History-Friendly)。中核問題 6 つ。**識別問題**: Haavelmo 1944「it is impossible for statistical inference to decide between hypotheses that are **observationally equivalent**」 | **「観測的同値」は 1944 年の語**。LLM 系の新語ではない |
| **Boero & Squazzoni 2005**(JASSS 8(4)6) | **実読** | 型が 3 つ(case-based / typifications / theoretical abstractions)。**抽象ほど検証が重い**:「the level of abstraction implies the need of a strong and extensive empirical validation」 | **型を宣言すれば要求量が決まる** |
| **Epstein 2008「Why Model?」**(JASSS 11(4)12) | **実読** | 予測以外の 16 の理由。「The choice … is whether to build **explicit** ones」。§1.10「**Explanation Does Not Imply Prediction**」 | **予測を目的に据えない道**の正典 |
| **Edmonds et al. 2019「Different Modelling Purposes」**(JASSS 22(3)6) | **実読** | 7 目的と目的別の合格条件。「**establishing a simulation for one purpose does not justify it for another**」。Prediction の定義に「data that is **not currently known**」 | **本書の §3 の骨格**。古典側で最も新しく最も使える物差し |
| **Edmonds & Hales 2003**(JASSS 6(4)11) | **実読** | 「**An unreplicated simulation is an untrustworthy simulation**」。独立 2 本の再実装・別言語・別人。整合しないなら機能を切って戻す | **再現は 1 本では足りない** |
| **Axtell 2016**(AAMAS 2016 pp.806–816) | **実読**(11 頁) | 1.2 億体(実寸)・約 12 母数で**約 24 の経験的事実**を同時再現。32 コア/256 GB・半日 | **実寸 ABM は 2016 年に達成済み**。規模は新規性にならない |

**要求を 6 語でまとめると**: 目的を言え / 単純さの理由を言え / 生成は候補にすぎない / パターンは複数当てろ / 再現は独立に / 識別問題を自覚しろ。

### 1-2. LLM 系が持ち込んだもの(問い 2)

**新しく可能になったこと**

| 文献 | 一次確認 | 可能になったこと |
|---|---|---|
| **Park et al. 2023**(2304.03442) | **既読**([[lit/agents__park2023_generative-agents-replay]]) | **行動則を書かずに一日を生成する**。評価は「無作為に選んだ 1 体の replay + 記憶ストリーム全開示」。逸話を数に降ろす 3 段(物語→全員への聞き取り→記憶での裏取り)。453 応答の 1.3% が幻覚 |
| **Argyle et al. 2023**(2209.06899・*Political Analysis*) | **実読**(§3・§4・§6・§7・§9) | **algorithmic fidelity** の 4 条件(Social Science Turing Test / Backward Continuity / Forward Continuity / Pattern Correspondence)と **silicon sampling**。「偏りは fine-grained and demographically correlated」だから条件づけで部分集団の分布が出る |
| **Horton 2023**(2301.07543・v2 2026-02) | **抄録のみ** | LLM は「**implicit computational models of humans -- a Homo silicus**」。「LLMs can be used like economists use Homo economicus」= **賦存・情報・選好を与えて振る舞わせる** |
| **Aher, Arriaga & Kalai 2023**(2208.10264・ICML 2023 oral) | **抄録のみ** | **Turing Experiment (TE)**: チューリングテストが「simulating a single arbitrary individual」なのに対し TE は「**simulating a representative sample of participants in human subject research**」。古典 4 実験(Ultimatum / Garden Path / Milgram / Wisdom of Crowds)で再現 |
| **Gao et al. 2024**(2312.11970・37 頁) | **抄録のみ** | LLM×ABM の最初期の体系サーベイ。4 領域(cyber / physical / social / hybrid)。課題は「environment perception, human alignment, action generation, and evaluation」 |
| **Piao et al. 2025 AgentSociety**(2502.08691) | **既読**([[lit/compute__agentsociety2025_parallel_framework]]) | 実 LLM で 1 万体級・並列基盤・実時間比の提示 |
| **Yang et al. 2024 OASIS**(2411.11581) | **既読**([[lit/mas__yang2024_oasis]]) | 100 万体。**規模で現象が変わる**(herd は 100 体で出ず 10,000 体で出る)。Table 2: 1M で 18.0 h/step・A100 27 枚 |

**新しく壊れたもの**

| 壊れたもの | 一次の根拠 | 古典側の既定値 |
|---|---|---|
| **決定論** | [[lit/nlp__atil2024_nondeterminism]]: 温度 0 でも同一出力は保証されない | Epstein 2006 §IV「**This determinism is why, when we save the seed and re-run the program, we get exactly the same run again.**」= 完全同一が既定 |
| **事前知識の漏洩** | Barrie & Törnberg 2025(2505.23796): 「the observed behaviors are **indistinguishable from memorization of the training corpus**」。Larooij & Törnberg 2025: 「**Data leakage represents a serious risk for such validation approaches**」 | 古典 ABM には存在しない失効経路(規則を人が書くから) |
| **同質性** | [[lit/mas__wang2026_s-researcher]]: 「LLM の応答分散は人間の 20–300 倍小さい」。Anthis 2025 §3.1: 11–20 ゲームで LLM はほぼ常に 19 か 20(人間の中央値 17) | 古典 ABM では異質性は**母数として書くもの**(Epstein 2006 §II「every individual is explicitly represented」) |
| **書式感受性** | [[lit/validation__ye2026_robustness-audits]]: 同内容・別書式のペルソナで協力率 76 pt 差(gpt-5.2・N=30 seed) | 古典 ABM にペルソナ書式という次元が無い |
| **検証の不能感** | Larooij & Törnberg 2025: 35 本中 **15 本が主観のみ**・22 本が主観を主手段。「At worst, validation consists of asking an LLM to evaluate the plausibility of its own output」 | Windrum 2007 の 3 系統・Boero & Squazzoni 2005 の型別要求が既にあった |
| **費用** | OASIS 1M: 18.0 h/step × A100 27。[[lit/compute__alves2026_llm-urban-mobility]]: LLM 判断層は規則ベースの 2.6〜5.1 倍 | Axtell 2016: 1.2 億体・32 コア 1 台・半日 |
| **実験下にあることの看破** | PIMMUR(2509.18052 v4): 「Frontier LLMs correctly identified the underlying social experiment in **65.2% of cases**」 | 古典 ABM のエージェントは実験を知らない |

### 1-3. 検証の要求の対照(問い 3)→ §2 の表

### 1-4. 「創発」の扱い(問い 4)

| 立場 | 一次の言明 | 含意 |
|---|---|---|
| **古典(Epstein 2006 §IV)** | 「Merely to generate is not necessarily to explain (at least not well).」「generative sufficiency is a **necessary, but not sufficient** condition for explanation.」「the mapping from the set of microspecifications to the macroscopic explanandum might be **many-to-one**.」 | 生成できた = **説明の候補**。競合候補の裁定には別の証拠(実験心理・データ)が要る |
| **古典(Schelling の閾値)** | 「a family will move only if more than one third of its immediate neighbors are of a different type」(Axelrod 1997 §2 の要約・**原典未読**) | 創発の説得力は**微視則の単純さ**から来る。書いた規則が全部見えている |
| **LLM(Project Sid 2411.00114)** | **§7 Limitations の逐語(実読で確認)**: 基盤モデルが人間の知識で訓練されている以上「**they cannot simulate de novo emergence of societal innovations and infrastructures**」「such as the emergence of democratic systems, fiat economies, or communication systems」。また「**lack robust innate drives—such as survival, curiosity, community**」。宗教は創発でなく注入(§5.3: 「with the exception of **20 priests** that worship Pastafarianism」= 500 体中 20 体) | **生成の上限が著者自身の申告として存在する**。「伝播は起きるが創造は起きない」。ただし論証ではなく限界節の見立て |
| **LLM(Barrie & Törnberg 2025)** | 「observationally equivalent to a series of LLM agents mapping the payoff description to its pretraining knowledge」。14 モデル × 各 10 回の看破テストで「the models were able to correctly identify each of these dimensions」 | **創発と事前知識の再生が観測上同値**。Ashery の対策(書式変種・無意味文字列・メタプロンプト)は「None of the mitigation steps … guards sufficiently against this risk」 |
| **LLM(PIMMUR v4)** | 65.2% が実験を看破・**50.6% のプロンプトが制約で結果を先決め**・5 実験の再現で「reported collective phenomena often vanish or reverse」 | 創発の主張の多くが**方法の産物** |

**判定**: LLM 系の「創発」は、古典側の語彙では **Windrum 2007 §2.3(5) の識別問題に競合仮説が 1 つ増えた**だけである。新しい問題ではなく、**新しい競合候補**。Epstein の many-to-one 写像の 1 本が「事前学習の再生」になった。
**処方は 2 つしか提示されていない**(Barrie & Törnberg 段落 13–16): (a) LLM が見ていない場面を作る (b) 内部を覗く(sparse autoencoder による解釈可能性プロービング・next-token perplexity)。**(a) は「公開文献に載っていないデータで照合する」と同義**。

### 1-5. 規模と時間(問い 5)

| 系統 | 体数 | 計算 | 出所 | 一次確認 |
|---|---|---|---|---|
| Schelling 分居 | 盤上の数十〜数百 | 手作業(1971 年は碁盤とコイン) | — | **二次** |
| Sugarscape | **未取得(空欄)** | — | Epstein & Axtell 1996 | **未取得** |
| **Axtell 2016(米国民間部門)** | **1.2 億(実寸 1:1)** | **32 コア・256 GB のワークステーション 1 台・定常到達まで「約半日」** | AAMAS 2016 §4 | **実読** |
| MATSim(100% スイス) | 730 万 | 1,000 反復に約 116 日 = **1 反復 ≈ 2.8 h** | [[lit/compute__matsim2020_hermes]] | **実読** |
| Park 2023 Generative Agents | **25** | 2 ゲーム日 | [[lit/agents__park2023_generative-agents-replay]] | サブ実読 |
| Park 2024 面接型 | 1,052 | — | Anthis 2025 §1 経由 | **二次** |
| **OASIS** | **100 万** | **1 step = 18.0 h・A100 27 枚**(10 万で 3.0 h・5 枚/1 万で 0.2 h・2 枚) | [[lit/mas__yang2024_oasis]] Table 2 | **実読** |
| AgentSociety | 1 万(実 LLM) | 並列基盤 | [[lit/compute__agentsociety2025_parallel_framework]] | **実読** |
| **Project Sid** | 抄録は「10 - 1000+」だが、**分析に使ったのは 500 体 1 本**(§5.3: 1000 体超は Minecraft サーバの制約で「sporadically unresponsive」)。課税実験は別建てで 25+3+1 体 | 500 体 × 9,000 秒。**計算費の記載なし** | 2411.00114 §5.3・§8.4 | **実読** |

**規模が効く先行**: OASIS の herd 効果(100 体では出ず 10,000 体で明示的に出現)。
**規模が効かない/逆に壊す先行**: Edmonds & Hales 2003 §9.13 — Riolo モデルは**個体数を 2 倍にすると贈与が消える**。同 §9.2・§9.12 — 比較演算子を `≤` から `<` に変える、タグに微小雑音を足すだけでも消える。
**含意**: 規模は単調に効くのでも効かないのでもない。**「規模を上げたら現象が出た/消えた」は実験で示す量**であり、規模そのものが新規性でも妥当性でもない。Axtell 2016 が示すとおり、**実寸は LLM を使わなければ 2016 年に既に達成されている**。

### 1-6. この分野の「よい研究」の判定基準(問い 6)

| 出所 | 何を見るか |
|---|---|
| **Edmonds et al. 2019(JASSS)** | **7 目的のどれを名乗るか、その目的の合格条件を満たすか**。目的の混同 6 型に名前が付いている(特に Explanation→Prediction)。「A confused, conflated or unclear modelling purpose … a recipe for bad science」 |
| **Edmonds & Hales 2003(JASSS)** | 「the description of the simulation should be sufficient for others to be able to **replicate**」「independently replicated by others … before the simulation or the results are taken seriously」 |
| **Grimm 2020 ODD**(既読メモ) | 記述標準。**平均だけか分布も見たかを書け・合わなかったパターンも書け(HARKing 禁止)** |
| **Boero & Squazzoni 2005(JASSS)** | **型(case-based / typification / abstraction)を宣言**し、型に応じたミクロデータ取得戦略を示す。verification と validation を分ける |
| **Larooij & Törnberg 2025** | 最小限の物差し 3 点 = **目的との整合 / 外部的接地(人のデータか pre-registered experimental benchmarks)/ 頑健性(多ラン+感度)** |
| **Ye et al. 2026** | 何を摂動し・何が安定で・何が敏感で・**何を監査しなかったか**を報告せよ。主張の型(探索的/機構/政策)に監査量を合わせよ |
| **Anthis et al. 2025 §4.5.2** | 分布外の評価は**訓練データに未収載のデータ**で。「We have not yet seen, but we encourage, **preregistration of LLM simulation predictions**」 |

**「モデル比較の標準」はあるか** → **部分的にしか無い**。
- **ある**: Axtell et al. 1996 の **3 段の同値**(numerical identity / distributional equivalence / relational equivalence)。これは 30 年間使える語彙で、いまも代替が出ていない。
- **ある**: Edmonds & Hales 2003 の**整合の 4 技法**(初期 tick で比較・2 標本 KS 検定・機能を切って戻す・別言語別人で 2 本)。
- **無い**: 共通ベンチマーク、共通の合格線。Windrum 2007 §5.2 の未解決課題 (4) が「**十分に強い経験的テストの定義**」であり、Boero & Squazzoni 2005 §1.10 は「**a unique method for empirically calibrating and validating ABMs does not exist, yet**」と書いている。Argyle 2023 §3 も「we do not propose specific metrics or numerical thresholds」と明記。**20 年間、合格線は各自が宣言するものだった**。
- **注意**: ユーザーの依頼にあった「**Squazzoni 2012 の批判**」は、探した範囲では **JASSS の論文としては存在しない**。2012 年の Squazzoni は Wiley の単著書 *Agent-Based Computational Sociology*(JASSS 16(1) に書評あり)。**JASSS 上の方法論批判に最も近いのは Boero & Squazzoni 2005**(本書で実読)。**JASSS の投稿規程・査読基準のページ本文は取得できなかった**(§4)。

---

## 2. 対照表(古典の要求 × LLM の新規性 × 検証項目)

**読み方**: 「古典の要求」は 1971〜2019 年の文献が明示的に課したもの。「LLM で変わったこと」はその要求の**成立条件が壊れた/新しい軸が増えた**部分。「いま要る形」は両方を満たす最小の手続き。

| 項目 | 古典の要求(出所) | LLM で変わったこと(出所) | いま要る形 |
|---|---|---|---|
| **再現性・決定論** | **3 段で宣言する**: numerical identity(同一 RNG・同一 seed が必要)/ distributional equivalence / relational equivalence(Axtell et al. 1996 via Axelrod §4)。「save the seed and re-run → exactly the same run」が既定値(Epstein 2006 §IV) | **最上段が原理的に届かない**。温度 0 でも同一文字列は保証されない([[lit/nlp__atil2024_nondeterminism]])。バッチ・並列・ハードウェアで揺れる | **どの段を主張するかを明示**。同一性を主張する層(テープ再生・表参照)と、分布同値でしか主張できない層(LLM 出力)を**分けて書く**。古典側でも浮動小数点の機械差で経路依存が連鎖した実例がある(Axelrod §4) |
| **較正と holdout** | 3 系統のどれかを宣言(Windrum 2007 §4)。型に応じたミクロデータ取得戦略(Boero & Squazzoni 2005 §4)。**抽象ほど検証は重い**(同 §4.60) | **較正がプロンプト調整に退化**する:「"calibration" is thus reduced to prompt engineering, and generally aimed at improving face-validity」(Larooij & Törnberg)。さらに **holdout が訓練データに入っている**可能性が新しく生じた | **holdout は「未知」だけでなく「未公刊」でなければならない**。Anthis §4.5.2 は訓練カットオフとの前後関係で測れと書く。**データの取得日とモデルのカットオフの関係を書く**のが新しい必須欄 |
| **パターン照合** | 複数同時。Explanation を名乗るなら**典型 3〜5**(Edmonds 2019)。1 つのパターンは間違った理由でも合う(POM)。Axtell 2016 は**約 12 母数で約 24 の事実** | **公刊された stylized fact での照合は漏洩の疑いがかかる**(Larooij & Törnberg §Validation against well-known social patterns)。スケールフリー網・エコーチェンバー等が名指しされている | パターン台帳の各行に「**このパターンは公刊されているか**」の欄。公刊済みパターンは**多重照合の頭数に入れても主張の重みを下げる** |
| **感度・ablation** | 感度解析・雑音・多ラン・**非本質過程の入替**・反証実験(Edmonds 2019 Explanation)。「several dozen simulation runs … different random number seeds」(Axelrod §3.2)。統計的有意と**実質的有意**を分ける | **摂動軸が増えた**: TRAILS-D 8 次元 + TRAILS-R 5 次元(書式・指示階層・言い回し・文脈表現・順序)([[lit/validation__ye2026_robustness-audits]])。Anthis の 5 つの壁(Diversity / Bias / Sycophancy / Alienness / Generalization)は**それと直交する別の軸** | **被覆表**を作り、**監査しなかった次元を明示する**(Ye §6)。腕の数は主張の型で決める |
| **説明** | 生成は**候補**にすぎない(Epstein 2006)。many-to-one。裁定には実験か機械的探索 | 競合候補に「**事前学習の再生**」が加わった(Barrie & Törnberg)。しかも**観測上区別できない** | 「創発」と書く行の隣に「**事前知識の再生で説明できないか**」の 1 行。**看破テスト**(モデルに「この設定は何のモデルか」と聞く)は安い |
| **予測の主張** | 予測は目的の 1 つにすぎない(Epstein 2008 の 16 理由)。**説明は予測を含意しない**(§1.10)。Prediction を名乗る条件は「モデラーが当時知らなかったデータ」(Edmonds 2019) | **使ってよい範囲が「予備・探索」まで**と外から言われている(Anthis §1・§5)。事前登録は**推奨されているが様式が無い**(Anthis §4.5.2・Larooij の 1 行) | **目的を 1 つ宣言**し、Prediction を名乗るなら「誰がいつ知らなかったデータか」を書く。名乗らないなら Explanation / Description の合格条件で判定する |
| **費用** | 実寸 1.2 億体 = 32 コア・256 GB・半日(Axtell 2016)。非実用の判定は **N×T**(必要ラン数 × 1 本の時間)で下る([[lit/compute__matsim2020_hermes]]) | 3〜6 桁悪化。OASIS 1M = 18 h/step・A100 27 枚。LLM 判断層は規則ベースの **2.6〜5.1 倍**([[lit/compute__alves2026_llm-urban-mobility]])。Ye の N=30 seed は実寸では不可能 | **費用を N×T で宣言**し、**監査を下見規模で・本番を少 seed で**の 2 段構えにする。古典側の実寸と**体あたり・step あたりで正規化して**並べる |
| **倫理** | ODD の記述標準・コード公開(Edmonds & Hales 2003)。被験者性は薄い | **個体軌跡の再識別**([[lit/ethics__demontjoye2013_unicity]]: 4 点で 95% が一意・粗化は 1/10 乗でしか効かない)。**silicon sampling の悪用可能性**(Argyle §9「dangerous potential」)。LLM 自身が実験下だと気づく(PIMMUR 65.2%) | **個体カルテは公開しない線**を数値根拠つきで引く。「特定個人の模擬ではない」を明記(Argyle §3) |

---

## 3. 「良い LLM 社会シミュレーション」の判定基準 10 項

> **この repo の自己評価は書かない**(別レーンの仕事)。各項は「文献がそう要求している」という事実だけを述べる。

| # | 基準 | 何を見るか | 出典(逐語または節) |
|---|---|---|---|
| **1** | **目的を 1 つ宣言している** | 7 目的(prediction / explanation / description / theoretical exposition / illustration / analogy / social learning)のどれを名乗るかが書いてあるか。複数なら**それぞれ別に正当化**しているか | Edmonds et al. 2019: 「establishing a simulation for one purpose does not justify it for another」「re-justified with respect to **each** of the claimed purposes **separately**」。軽い版は Epstein 2008 の 16 理由 |
| **2** | **「予測」を名乗るなら未知かつ未公刊のデータで検証している** | 予測対象のデータが**当時モデラーに知られていなかった**か。さらに **LLM の訓練データに入っていないか**(取得日 vs モデルのカットオフ) | Edmonds 2019: Prediction = 「reliably anticipate … data that is **not currently known**」・out-of-sample fitting では足りない。Anthis 2025 §4.5.2: 「use data that is not yet incorporated in training data」 |
| **3** | **「生成できた」と「説明した」を分けて書いている** | 創発・再現の主張が **candidate explanation** として書かれているか。**等結果性(many-to-one)**への言及があるか | Epstein 2006 §IV・§V[1]: 「generative sufficiency is a necessary, but not sufficient condition for explanation」「A microspecification that generates the explanandum is a **candidate explanation**」 |
| **4** | **パターンを複数同時に照合し、母数より照合数が多い** | Explanation を名乗るなら**同時照合 3〜5 以上**。合わなかったパターンも書いてあるか | Edmonds 2019(Explanation の合格条件)・[[lit/abm__grimm-railsback2012_pom-multiscope]](1 つのパターンは間違った理由でも合う)・Grimm 2020 ODD(HARKing 禁止)・Axtell 2016(約 12 母数 vs 約 24 の事実) |
| **5** | **モデルの型と、単純/複雑の選択理由が書いてある** | case-based / typification / theoretical abstraction のどれか。KISS を採るならその目的条件が成り立つか | Boero & Squazzoni 2005 §3.2・§4.60(抽象ほど検証が重い)。Axelrod 1997 §2(KISS は「基礎過程の理解」が目的のときだけ。訓練・予測が目的なら単純さは要らない) |
| **6** | **再現の段を宣言し、同値は事前に幅を決めて検定している** | numerical identity / distributional equivalence / relational equivalence のどれを主張するか。同値の検定で**小標本にする誘因**を潰しているか | Axtell et al. 1996 via Axelrod §4: 3 段の定義+「specify in advance the magnitude of the difference that will be considered meaningful」。現代形は [[lit/stats__lakens2017_tost-equivalence]]・[[lit/validation__sargent2016_interval-test]] |
| **7** | **独立な再実装か、それに代わる検査を通している** | 別言語・別人での再実装、または整合の 4 技法(初期 tick 比較・2 標本 KS・機能切り戻し・多言語実装)。**更新順序・同点処理・終了条件**が明文化されているか | Edmonds & Hales 2003 §10.1・§11.2・§12.2: 「An unreplicated simulation is an untrustworthy simulation」。壊れた実例は Axelrod §4 の 4 類型(曖昧さ・欠落・明快だが誤り・ソース/浮動小数点) |
| **8** | **主観評価・自己採点を検証の主軸にしていない** | 検証手法が分類されているか(人の判断 / 既知パターン / 人のデータ / 内部整合 / 他モデル)。**内部整合を validation と呼んでいないか** | Larooij & Törnberg 2025: 35 本中 15 本が主観のみ・「At worst, validation consists of asking an LLM to evaluate the plausibility of its own output」・「内部整合性は verification であって validation ではない」。Boero & Squazzoni 2005 §5.2 も 2 脚を分ける |
| **9** | **「創発」の主張に事前知識の排除が添えてある** | 場面が公刊物にあるか。**看破テスト**(モデルに設定の正体を聞く)を通したか。**エンジン側のハードコードで説明できる分を引いたか** | Barrie & Törnberg 2025: 「indistinguishable from memorization of the training corpus」「the inventory pruning rule is hard-coded into their simulation code」。PIMMUR v4: 看破 65.2% / 制約による先決め 50.6%。古典側の同型は Windrum 2007 §2.3(5) の識別問題 |
| **10** | **摂動の被覆・ラン数・費用(N×T)を宣言している** | 何を振り、何が安定で、何が敏感で、**何を監査しなかったか**。ラン数と、統計的有意と実質的有意の区別。費用を N×T で書いているか | Ye et al. 2026 §6(報告様式・TRAILS-D 8 × TRAILS-R 5)・Anthis 2025 の 5 つの壁・Axelrod 1997 §3.2(several dozen runs・2 種の有意性)・[[lit/compute__matsim2020_hermes]](N×T)・OASIS Table 2・Axtell 2016 §4 |

**この 10 項の出自の内訳**: 古典 ABM だけに由来 = #1, #3, #4, #5, #6, #7(6 項)/ LLM 系だけに由来 = #9(1 項)/ 両方 = #2, #8, #10(3 項)。
→ **「LLM 社会シミュレーションの良し悪しを測る物差し」の 6 割は、LLM 以前から存在していた。**

---

## 4. 空欄(親が埋める・または残務台帳へ写す)

### 4-1. 取得できなかった一次資料

| # | 資料 | 何が要るか | 障害 |
|---|---|---|---|
| L-CLS-1 | **Schelling 1971**(*J. Math. Sociol.* 1(2):143–186) | 抄録・閾値の原文値・"spatial proximity model" と "bounded neighborhood model" の 2 モデルの記述 | tandfonline が 403。本書の記述は Axelrod 1997 §2 と Epstein 2006 §IV の**二次** |
| L-CLS-2 | **Gilbert & Troitzsch** *Simulation for the Social Scientist*(検証章) | 教科書が課している検証手続き | 書籍・未取得 |
| L-CLS-3 | **Macal & North 2010**(*J. Simulation* 4:151–162・DOI 10.1057/jos.2010.3) | 誌版の文言 | **代替として WSC 2009 版(Proceedings of the 2009 Winter Simulation Conference, pp.86–98)を実読済み**。誌版との異同のみ残る |
| L-CLS-4 | **Epstein & Axtell 1996** *Growing Artificial Societies* | **Sugarscape の典型的な体数**(問い 5 の表が 1 行空いている) | 書籍・未取得 |
| L-CLS-5 | **Axtell, Axelrod, Epstein & Cohen 1996**(CMOT・docking 原典) | 3 段の同値の原文定義・同値検定の手続き | 未取得。本書は Axelrod 1997 §4 経由の**二次** |
| L-CLS-6 | **JASSS 投稿規程・査読基準** | 「よい研究」の判定基準の公式版 | `jasss.org/admin/submit.html` は題名のみで本文が取得できない(JS 依存)。**問い 6 の「査読者が見るもの」は文献の要求で代用した** |
| L-CLS-7 | **Barrie & Törnberg 2025 Figure 1** | **看破率の百分率**(本文に数値が無い) | 図の読み取りが要る |
| L-CLS-8 | ~~**Project Sid**(2411.00114)~~ **閉じた** | ~~de novo の逐語~~ | **§7 で確認済み**([[lit/css__projectsid2024_de-novo-limit]])。残るのは**付録 E(プロンプト)と計算費**。なお既存答申の「納税率 20%→9%」は正確には「**反税の憲法改正後**」であり、**500 体ランではなく 25+3+1 体の別実験**(§8.3)。既存答申には**改宗の測定が語の使用だけ**(§5.3.2)という限界が落ちている |
| L-CLS-9 | **Ashery et al. 2025**(*Science Advances* 11(20): eadu9368) | Barrie & Törnberg が反論している側の原文 | 未取得 |
| L-CLS-10 | **Horton 2023 / Aher 2023 / Gao 2024** | 本文(いまは**抄録のみ**) | 時間切れ |

**リンクの到達性**(2026-09-17・本レーンで curl 確認): 本書と新設メモが張った URL は、**arXiv・JASSS・PMC・doi.org(JASSS/Political Analysis)の 13 本が HTTP 200**。**`doi.org/10.1080/0022250X.1971.9989794`(Schelling)と `doi.org/10.1073/pnas.082080899`(Bonabeau)は 403**——これは DOI が死んでいるのではなく**出版社の着地ページが自動クライアントを弾いている**(Bonabeau は PMC 版で全文を読めている)。

### 4-2. 数値の食い違い(親の一次確認が要る)

| # | 内容 | 影響 |
|---|---|---|
| L-CLS-11 | **PIMMUR(2509.18052)の数値が版で変わっている**。既存答申 [v2-science-claims-research.md](v2-science-claims-research.md) §2 は「**39 研究の 89.7%** が妥当性原則違反・LLM の **50.8%** が実験下を看破・**61%** のプロンプトが結果を先決め」と書いているが、**現行 v4(最終改訂 2026-09-10)の抄録は「576 studies reported in 350 recent papers」「65.2%」「50.6%」**。コメント欄に「Added more studies in our systematic audit (350 papers; 576 simulations)」とある | 既存答申の 3 数値が**古い版のもの**。引用しているすべての箇所を版指定つきに直す必要がある |
| L-CLS-12 | **Hewitt et al. 2024 の統計量**。Anthis 2025 §1 は「70 本の事前登録実験・GPT-4 が ATE の分散の **91%** を説明(測定誤差調整後)」、既存答申は「Ashokkumar+(Nature 2026)= 70 事前登録実験 469 効果で **r=0.85**・未公刊でも r=0.90」。**同一研究か別研究か、統計量の定義が違うだけか**が未確定 | 「予測妥当性への転回」の根拠の強さが変わる |
| L-CLS-13 | **Axtell 2016 の所要時間**。原文が「approximately half a day a day of wall time」(誤植)で、**半日か 1 日か確定できない** | 古典との費用比較の桁 |
| L-CLS-14 | **Axelrod 1997 の版差**。読んだのは 2003 年更新版。**1997 年 Springer 版(pp.21–40)/ Complexity 3(2):16–22 との異同は未確認** | 3 段の同値の文言 |
| L-CLS-15 | **Epstein 2006 Remarks の書誌**。Handbook of Computational Economics の**巻・章番号・頁・DOI が未確認** | 引用の体裁 |
| L-CLS-16 | **Axtell 2016 の恒久リンク**。AAMAS 2016 予稿集 pp.806–816 の **ACM DL / IFAAMAS の恒久 URL が未確認**。読んだのは大学公開アーカイブ | 出典の追跡性 |

### 4-3. 埋まらなかった問い

- **「モデル比較の標準」**: 共通ベンチマークも共通の合格線も**存在しないことを確認した**(Windrum 2007 §5.2(4)・Boero & Squazzoni 2005 §1.10・Argyle 2023 §3 の 3 つが独立にそう書いている)。ただし **「存在しない」を主張するには網羅探索が足りない**(3 本の言明の日付は 2005・2007・2022)。**2023 年以降に標準が作られたかは未探索**。
- **Squazzoni 2012 の批判**: 依頼にあった文献は **JASSS 論文としては見つからなかった**(Wiley の単著書と判断)。**代替として Boero & Squazzoni 2005 を実読した**が、ユーザーが意図した文献が別にある可能性は残る(Squazzoni 2010 *History of Economic Ideas* 18(2):197–233 / Squazzoni & Casnici 2013 JASSS 16(1):10 / Bianchi & Squazzoni 2015 WIREs が候補)。
- **Anthis の処方の内部矛盾**: Diversity の処方(interview-based prompting)と Sycophancy の処方(ペルソナのロールプレイを避けよ)は**両立しない可能性がある**。本論文はこの緊張を解いていない。**この repo の W17 v2(面接形式の自己生成)はこの矛盾の真ん中にある**が、判定は別レーン。

---

## 5. lit README の索引行(追記用・本書で新設した 13 本)

> [lit/README.md](lit/README.md) §索引の表にそのまま足せる形。**追記は親が行う**(本レーンは台帳を編集していない)。

| メモ | 分野 | 一次確認 | 何のために引くか |
|---|---|---|---|
| [abm__epstein2006_generative-sufficiency](lit/abm__epstein2006_generative-sufficiency.md) | 科学哲学 #26 / ABM方法論 #21 | B(サブ実読・pymupdf 27 頁・親未確認) | **「生成できた ≠ 説明した」の原典**・`∀x(¬Gx⊃¬Ex)` の逆は不成立・**many-to-one(等結果性)**・「seed を保存して再実行 = 完全同一」が古典の既定値 |
| [abm__axelrod1997_kiss-replication](lit/abm__axelrod1997_kiss-replication.md) | ABM方法論 #21 / 検証とV&V #22 | B(サブ実読・pymupdf 19 頁・親未確認) | **再現の 3 段**(numerical identity / distributional / relational)・**同値検定の帰無の罠=TOST の 1996 年版**・**KISS は目的条件つき**・再現が壊れた 4 類型 |
| [abm__edmonds2019_modelling-purposes](lit/abm__edmonds2019_modelling-purposes.md) | ABM方法論 #21 / 科学哲学 #26 | B(サブ実読・JASSS 本文・親未確認) | **7 目的と目的別の合格条件**=判定基準の骨格・「予測」の定義(未知データ)・**Explanation は同時照合 3〜5**・目的の混同 6 型 |
| [abm__edmonds-hales2003_replication](lit/abm__edmonds-hales2003_replication.md) | 検証とV&V #22 / ソフトウェア工学 #29 | B(サブ実読・JASSS 本文・親未確認) | 「**An unreplicated simulation is an untrustworthy simulation**」・**数値が合っても結論が別物だった実例**・整合の 4 技法・**個体数 2 倍で現象が消えた**(規模の非単調) |
| [abm__windrum2007_empirical-validation](lit/abm__windrum2007_empirical-validation.md) | 検証とV&V #22 / ABM方法論 #21 | B(サブ実読・JASSS 本文・親未確認) | 較正・検証の 3 系統・中核問題 6 つ・**「観測的同値」は Haavelmo 1944 の語**(LLM 系の新語ではない)・「十分に強い経験的テストの定義」が未解決課題 |
| [abm__boero-squazzoni2005_empirical-embeddedness](lit/abm__boero-squazzoni2005_empirical-embeddedness.md) | ABM方法論 #21 / 検証とV&V #22 | B(サブ実読・JASSS 本文・親未確認) | **モデルの 3 型と型別の要求**・**抽象ほど検証が重い**・verification と validation の 2 脚・「唯一の較正/検証法は存在しない」 |
| [abm__epstein2008_why-model](lit/abm__epstein2008_why-model.md) | 科学哲学 #26 | B(サブ実読・JASSS 本文・親未確認) | **予測以外の 16 の理由**・「**Explanation Does Not Imply Prediction**」・第一目標を古典の語彙で書くための語 |
| [abm__bonabeau2002_when-abm-useful](lit/abm__bonabeau2002_when-abm-useful.md) | ABM方法論 #21 / 計算社会科学 #25 | B(サブ実読・PMC 全文・親未確認) | **ABM を使う 5 条件**・「**Averages will not work**」・「a general-purpose model cannot work」=被覆の暴走を止める線 |
| [abm__axtell2016_120m-agents](lit/abm__axtell2016_120m-agents.md) | ABM方法論 #21 / 計算機科学(並列)#28 | B(サブ実読・pymupdf 11 頁・親未確認) | **実寸 1.2 億体を 32 コア 1 台・半日**=規模は新規性にならない・**約 12 母数で約 24 の事実**・GPU/ベクトル機が計算アーティファクトを生んだ |
| [css__barrie2025_observational-equivalence](lit/css__barrie2025_observational-equivalence.md) | 計算社会科学 #25 / 科学哲学 #26 | B(サブ実読・arXiv HTML・親未確認) | **創発と事前知識の再生は観測上同値**・**看破テスト**という安い道具・処方は「見ていない場面を作る」か「内部を覗く」の 2 つだけ |
| [css__anthis2025_llm-social-simulations](lit/css__anthis2025_llm-social-simulations.md) | 計算社会科学 #25 / 検証とV&V #22 | B(サブ実読・arXiv HTML・親未確認) | **事前登録の外部根拠 2 本目**(§4.5.2)・**5 つの壁**・「使えるのは予備・探索まで」・訓練カットオフとの前後で分布外を測れ |
| [css__argyle2023_algorithmic-fidelity](lit/css__argyle2023_algorithmic-fidelity.md) | 計算社会科学 #25 / 人格心理学 #13 | B(サブ実読・arXiv HTML の §3/§4/§6/§7/§9・親未確認) | **algorithmic fidelity の 4 条件**と silicon sampling=「LLM が新しく可能にしたこと」の原点・**合格線は著者自身が提案していない**・「特定個人は模擬できない」 |
| [css__projectsid2024_de-novo-limit](lit/css__projectsid2024_de-novo-limit.md) | 計算社会科学 #25 / 科学哲学 #26 | B(サブ実読・arXiv HTML・親未確認) | **「de novo の社会的革新は模擬できない」の逐語と節(§7)**・宗教は 500 体中 20 体の注入(§5.3)・**分析に使ったのは 500 体 1 本**(抄録の 1000+ は分析外)・既存答申 §2 の 3 主張の一次確認 |
