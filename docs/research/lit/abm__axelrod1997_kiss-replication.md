# Axelrod 1997/2003 — Advancing the Art of Simulation in the Social Sciences

- リンク: https://doi.org/10.1007/978-3-662-03366-1_2 | 分野: ABM方法論 #21 / 検証とV&V #22 / 科学哲学 #26 | 重要度: **P0**
- **一次確認**: **実読(サブ・pymupdf 19 頁)・親未確認**(2026-09-17)。読んだのは **2003 年更新版**(*Japanese Journal for Management Information System*, Vol. 12, No. 3, Dec. 2003・著者自身が「1997 年 Springer 版 pp.21-40 の updated version」と 1 頁目に明記)。取得先は公開アーカイブ `faculty.sites.iastate.edu/tesfatsi/archive/tesfatsi/AdvancingArtSim2003.Axelrod.pdf`(**正規ドメインではない**=親は Springer 版 DOI か Complexity 3(2):16-22 で再確認のこと)。**1997 年原版との異同は未確認**。

## 主張(claim)

シミュレーションは帰納でも演繹でもない**第三の科学の仕方**であり、その価値は主に **discovery**(発見)にある。良いエージェントモデルは「**仮定を単純に・結果を複雑に**」(KISS)。そして分野が成熟するために決定的に欠けているのは **replication(再現・docking)**である。

## 機構(mechanism)— 3 つの柱

### 1. 第三の道(§2)

逐語(≤125 字): 「**Simulation is a third way of doing science. Like deduction, it starts with a set of explicit assumptions. But unlike deduction, it does not prove theorems.**」「**a simulation generates data that can be analyzed inductively**」。ただし「**the simulated data comes from a rigorously specified set of rules rather than direct measurement of the real world**」。

シミュレーションの目的は 7 つ(§2): **prediction / performance / training / entertainment / education / proof / discovery**。科学としての価値は「principally in prediction, proof, and discovery」。

### 2. KISS の**適用条件**(§2・ここが重要)

逐語(≤125 字): 「**This requires adhering to the KISS principle, which stands for the army slogan "keep it simple, stupid."**」理由は 2 つ、いずれも**認識論ではなく研究共同体の事情**である: 「**Both the researcher and the audience have limited cognitive ability.**」「**Simplicity is also helpful in giving other researchers a realistic chance of replicating one's model**」。

**KISS は無条件ではない**(§2 末尾・逐語 ≤125 字): 「**if a simulation is used to train the crew of a supertanker, or to develop tactics for a new fighter aircraft, accuracy is important and simplicity of the model is not.**」→ **目的が「基礎過程の理解」のときだけ単純さが要る**。予測・訓練が目的なら「the assumptions that go into the model may need to be quite complicated」。

結論の一句: 「**The complexity of agent-based modeling should be in the simulated results, not in the assumptions of the model.**」

### 3. Replication の 3 段(§4・Axtell, Axelrod, Epstein & Cohen 1996 の docking 研究から)

| 段 | 名 | 逐語(≤125 字) |
|---|---|---|
| 最強 | **numerical identity** | 「**The most demanding standard is "numerical identity", in which the results are reproduced exactly.**」「numerical equivalence can only be achieved if the same random number generator and seeds are used」 |
| 実用 | **distributional equivalence** | 「**Distributional equivalence is achieved when the distributions of results cannot be distinguished statistically.**」 |
| 最弱 | **relational equivalence** | 「**two models have the same internal relationship among their results**」(例: ある量が時間の二次関数・母数について単調減少) |

**同値検定の帰無の罠**(§4・3 点目・逐語 ≤125 字): 「**The problem with this approach is that it creates an incentive for investigators to test equivalence with small sample sizes.**」処方は「**specify in advance the magnitude of the difference that will be considered meaningful and then use sample sizes large enough**」= **同値検定(TOST)と事前登録の 1996 年版**。

## 数値(出所つき)

- docking 作業量: 「**took about 60 hours of work**」(§4・Axelrod の文化変容モデル × Sugarscape)。
- 8 モデルの再実装(Conway Life・Garbage Can・Schelling 残留傾向・Axelrod GA・March Organizational Code・Alvin & Foley 市場・NK Patch・Riolo Tag)は **Swarm で全 8 本が relational equivalence に到達**。「In most cases, the results were so close that we probably attained distributional equivalence as well, **although we did not perform the statistical tests to confirm this.**」
- ラン数(§3.2・逐語 ≤125 字): 「**it is necessary to do several dozen simulation runs using identical parameters (using different random number seeds)**」。統計手法は「regression if the changes are quantitative, and analysis of variance if the changes are qualitative」。2 つの有意性を分けよ: 「**are the differences statistically significant … and are the differences substantively significant**」。
- **Schelling の閾値の孫引き**(§2・Axelrod の要約): 「**The model assumes that a family will move only if more than one third of its immediate neighbors are of a different type**」。→ **Schelling 原典は未読なのでこれは二次**。

## 再現が壊れた 4 類型(§4・公刊物の側の欠陥)

1. **曖昧さ** — エージェントの更新順序・同点時の処理・図中の変数の意味・表の除数。「Some of these ambiguities … were resolved by seeing which of two plausible interpretations reproduced the original data. **This is a dangerous practice**」
2. **欠落** — 公刊データが分布同値の検定に足りない。変数が +1/0/−1 を取るのに 2 値に見える書き方。
3. **明快だが誤り** — 終了条件が本文と実ランで違う / 本文と付録が矛盾 / 本文がソースコードと違う。
4. **ソース側** — 印字が潰れた古いプリントアウトしか無い / **浮動小数点表現の機械差**。逐語(≤125 字): 「**is 9/3 exactly equal to 2 + 1? In one implementation of the model it was, but in another implementation it was not.**」「In models with nonlinear effects and path dependence, a small difference can have a cascade of substantive effects.」

さらに **サンプリングの微差が長期ランで効いた**実例(§4): 原版は復元抽出、Sugarscape 版は非復元抽出 →「**This seemingly minor difference in the two versions of the model made a noticeable difference in some very long simulation runs.**」

## 効く箇所(seam)

- **「テープ再生で最終ハッシュ一致」は Axtell の 3 段の最上段(numerical identity)**にあたる。古典側の語彙で名前が付く。ただし Axelrod 自身が「同一乱数生成器と seed が要る」と条件を付けているので、**LLM 推論を含む系では原理的に最上段に届かない**([[nlp__atil2024_nondeterminism]] の温度 0 でも同一出力は保証されない、と同じ線)。→ **段を分けて宣言する**のが正しい形。
- **同値の帰無の罠**は [[stats__lakens2017_tost-equivalence]] と同一論点の 1996 年版。**古典 ABM 側に 20 年以上前から要求があった**という事実は、この repo の TOST 採用の位置づけを変える(新規でなく標準の履行)。
- **浮動小数点の機械差 → 経路依存の連鎖**は、決定論の再生を「同一機械・同一ビルド」に限定する根拠。
- **KISS の適用条件**は、この repo のように「目的が予測・再現」の系に KISS を機械的に当てるのが誤りであることの一次根拠。

## 「結論でなく機構として」の入れ方

- **借りない**: KISS を憲法にすること(Axelrod 自身が目的依存だと言っている)。
- **借りる**: (1) **再現の 3 段の語彙**を受入報告に入れる。(2) **再現が壊れた 4 類型**をそのまま「自分の公刊物の点検表」にする(順序・同点処理・終了条件・本文とコードの一致)。(3) **「実質的有意」と「統計的有意」を分けて書く**欄。

## コスト/スケール含意

docking 1 本 = 約 60 時間(人手)。8 モデルの再実装は「a good deal more work than we had expected」。**再現は安くない**。

## 批判・限界

- 2003 年更新版。**1997 年原版との差分は未確認**(親が確認すること)。
- 統計の処方は粗い(「several dozen runs」に根拠の計算が無い)。反復数の現代的な決め方は [[stats__secchi-seri2017_power-abm]]・[[stats__siepe2024_simulation-study-template]] の側。
- Schelling の閾値 1/3 は本文の孫引きで、**原典 Schelling 1971 は未読**。
- Complexity 3(2):16-22 版の頁・行は未確認。

## 関連

[[abm__epstein2006_generative-sufficiency]] ・ [[abm__edmonds-hales2003_replication]] ・ [[abm__edmonds2019_modelling-purposes]] ・ [[stats__lakens2017_tost-equivalence]] ・ [[nlp__atil2024_nondeterminism]] ・ `../v2-classical-vs-llm-simulation-research.md`
