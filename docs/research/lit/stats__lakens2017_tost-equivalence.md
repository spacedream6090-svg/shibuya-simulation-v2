# Lakens 2017 — Equivalence Tests: A Practical Primer for t Tests, Correlations, and Meta-Analyses

- リンク: https://doi.org/10.1177/1948550617697177 | 分野: 統計学・因果推論 #23 | 重要度: **P0**
- **一次確認**: **実読**(2026-09-17・サブが PMC 全文 PMC5502906 を取得し、Introduction / Testing for Equivalence / Setting Equivalence Bounds / Equivalence Tests for Differences Between Two Independent Means の 4 節を逐語照合)。**親未確認**。*Soc Psychol Personal Sci* 8(4):355–362・CC BY 4.0。

## 主張(claim)

「有意差が無かった」は「差が無い」ではない。**差が実質的に意味のある大きさより小さいことを主張したいなら、帰無仮説を反転させた検定(同値検定)が要る**。最も単純な実装が **TOST(two one-sided tests)**。

逐語(≤125 字):
- "A very simple equivalence testing approach is the 'two one-sided tests' (TOST) procedure"(Introduction)
- "Two composite null hypotheses are tested: H01: Δ ≤ −ΔL and H02: Δ ≥ ΔU."(Introduction)
- "**In the TOST procedure, the null hypothesis is the presence of a true effect of ΔL or ΔU,**"(Testing for Equivalence)
- "and the alternative hypothesis is an effect that falls within the equivalence bounds"(同)

## 機構(mechanism)

1. **上下の同値境界 (−ΔL, ΔU) を、意味のある最小効果量(SESOI)から先に決める**。
   - "an upper (ΔU) and lower (−ΔL) equivalence bound is specified based on the smallest effect size of interest"
2. **片側検定を 2 回**行う。t_L = (M̄1 − M̄2 − ΔL)/(σ·√(1/n1+1/n2))、t_U = 同(ΔU 版)。式 1(Welch 版は式 3)。
3. 決定則: "**The two one-sided tests are rejected if tU ≤ −t (df, α), and tL ≥ t (df, α)**"
4. **実務上の近道**: "**To conclude equivalence (Scenario A), the 90% CI around the observed mean difference should exclude the ΔL and ΔU values**"(α=0.05 のとき 90% CI)。
5. NHST と併用すると**帰結は 4 通り**: "statistically different from zero but not statistically equivalent, statistically different from zero and statistically equivalent" / "or undetermined (neither statistically different from zero nor statistically equivalent)"

## 効く箇所(seam)

- 事前登録 §2 の合格線(H1 JSD ≤ 0.0122・H4 |Δ| ≤ 0.05・H5 |Δ| ≤ 0.10)は**そのまま同値境界**として読める。足りないのは **CI を付けて、その端が線の内側にあるかを見る**段だけ。**追加ラン 0 本**。
- **H1 のように量が距離(≥ 0)の場合は片側**: H0: JSD ≥ Δ vs H1: JSD < Δ。TOST ではなく one-sided test 1 本で足りる。
- SESOI の決め方が「**集められる最大標本で決まってしまう**」という著者の指摘("the maximum sample size you are willing to collect implicitly determines your SESOI")は、我々では「**回せる最大 seed 数が主張できる帯を決めてしまう**」と読み替わる。3 seed で言える帯は下の数値のとおり。

## 「結論でなく機構として」の入れ方

- **借りない**: TOSTER パッケージ・メタ分析版・相関版。
- **借りる**: (1) **90% CI が帯の内側 ⇒ 同値**という 1 行の決定則。(2) **4 帰結の言い分け**——「線を割った」「線の内側だと言えた」「どちらとも言えない(undetermined)」を受入表の判定語彙に入れる。いまの PASS/FAIL には **undetermined が無い**。(3) **境界は先に決める**(事前登録で既に満たしている)。

## 数値(自由度 2=3 seed に当てた再計算・親が計算すべき値)

- 片側 α=0.05 の t、自由度 2 = **2.9200**。
- **相対幅で書いた必要条件**: 同値を主張できるのは **帯 ≥ |偏り| + (2.9200/√3)·CV = |偏り| + 1.686·CV**。
- 実測 CV(第204)に当てると、偏り 0 でも: 昼(CV 0.0038)→ 最小帯 **0.64%**、深夜 05 時(CV 0.0325)→ 最小帯 **5.48%**。
- 参考: 両側 95% の相対半幅は d₃ = 248.4·CV(自由度 2 の t=4.3027)。

## コスト/スケール含意

追加ラン 0。既存の 3 seed の標準偏差だけで計算できる。**同値検定は検出力を要求する向きなので、seed が少ないと「同値」と言えなくなる**(「差が無い」を帰無に置いた現行より**厳しい**方向)。これが Robinson & Froese の言う「立証責任をモデルに戻す」の実務上の意味。

## 批判・限界

- 心理学の文脈で書かれており、**シミュレーション検証への適用例は本論文には無い**(V&V 側は [[validation__sargent2016_interval-test]])。
- 正規性・等分散の仮定(Welch 版で緩和)。
- SESOI の決め方は本質的に**分野の合意**であり統計では決まらない、と著者自身が書いている。
- Schuirmann (1987) の原典と Wellek の書籍は**未読**(有料)。一様最強不変性の主張は本論文経由の二次。

## 関連

[[validation__sargent2016_interval-test]]・[[stats__currie-cheng2016_output-analysis]]・`../v2-statistics-causal-research.md` §1-1・事前登録 v1.3 の S1-b
