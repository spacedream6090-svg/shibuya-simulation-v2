# Currie & Cheng 2016 — A Practical Introduction to Analysis of Simulation Output Data

- リンク: https://www.informs-sim.org/wsc16papers/013.pdf | 分野: 統計学・因果推論 #23 / OR | 重要度: **P0**
- **一次確認**: **実読**(2026-09-17・サブが curl → システム python の pymupdf で全 15 頁抽出。§5.2 反復数・§5.3 CRN・§6.1 二系比較・§6.2 多系比較と表 2 を逐語照合)。**親未確認**。WSC 2016 Proceedings pp.118–131。

## 主張(claim)

シミュレーション出力の解析で最初に要る道具は 4 つ: ウォームアップ長・反復数・**共通乱数(CRN)**・**系の比較(2 系は対応のある差、多系は Bonferroni)**。結語の 2 点は「**検定する前にデータの性質(独立性・正規性・時間依存)を必ず確かめよ**」「**検定の前に必ず図を描け**」。

## 機構(mechanism)

### (1) 反復数(§5.2)
相対誤差版: 反復数 n^r_ε は **p ≥ n かつ t_{1−α/2;p−1}·S(n)/(|ȳ(n)|·√p) ≤ ε/(1+ε)** を満たす最小の p。
- 警告(逐語): "**There is the potential for inaccuracy in the suggested values of n … especially for small values of n**"

### (2) 共通乱数(§5.3)
- "**The most useful and arguably the most widely used of the variance reduction techniques is that of Common Random Numbers (CRN)**"
- 原理: "when we are comparing different system configurations, we will reduce the variability if we run each of the system configurations under similar conditions"
- 実装の要点(逐語): "**you should try to ensure that the same random numbers in the stream are being used to generate the same variables**"
- 「同じ乱数列を使えばよい」では不十分("A first attempt … however, a little more care needs to be taken")。

### (3) 2 系の比較(§6.1)
対応のある差 Δi = yi(1) − yi(2)、CI = Δ̄(n) ± t_{n−1,1−α/2}·√Var[Δ̄(n)]。
- "**The method of Common Random Numbers … can be very useful for reducing the width of the confidence interval for a fixed value of n**"
- 正規性が疑わしければ図示 + ブートストラップ(Efron & Tibshirani 1998)。

### (4) 多系の比較(§6.2)— **本メモの中心**
- "**As the number of confidence intervals calculated increases, the confidence we have that all of the statements that we make are true decreases.**"
- Bonferroni の不等式: "Pr[all statements S_l, l = 1,…,C, are true] ≥ 1 − Σ_{l=1}^{C} α_l"
- 助言: "**it is worth spending some time before running the simulations to ensure that only necessary comparisons are being made**"

## 効く箇所(seam)

- **§6.2 の作例が我々の H1〜H5 と同じ C=5**。「各 90% の CI を 5 本並べたら、全部が正しい確率は 50%」という数がそのまま当たる。
- **§5.3 の CRN は「腕どうし」の比較にしか効かない**。holdout(現実は 1 本)には効かない——D-70 (d) の位置づけを直す根拠。
- **§5.2 の警告**は第204 の「N=(CV/r)² で 3 本」という逆算が n=2 の CV に基づいていることへの留保として使える。

## 「結論でなく機構として」の入れ方

- **借りない**: M/M/1 や TB/HIV の作例そのもの。
- **借りる**: (1) **Bonferroni の作例の数え方**(C 本の主張 → 家族の α は和で増える → 個別を (100 − α_family/C)% に締める)。(2) **対応のある差の CI**=C8 ablation の標準形。(3) **「必要な比較だけにする」**——指標を増やすほど帯が広がるので、H1〜H5 のうち**主張に使うものを事前に絞る**。(4) **結語の 2 点**(検定前に性質を確かめる・必ず図を描く)を受入表の作法に。

## 数値(出所つき)

- §6.2 表 2 の作例: ジンバブエの TB/HIV モデル・**介入 5 種**を基準と比較。各 α=0.10 → "**there is only a 50% chance that all of the confidence intervals contain their respective means**"。
- 家族 90% にするには "**we would need to compute (100−10/5)% = 98% confidence intervals for each individual result**"。
- 表 2 の効果(90% CI → 98% CI): 介入1 1.31 [−0.85, 3.48] → [−1.75, 4.37] / 介入4 55.8 [18.89, 92.70] → [3.61, 107.99] / 介入5 5.22 [0.01, 10.43] → [**−2.15**, 12.59](**98% にすると 5 が有意でなくなる**)。
- §6.1 作例: 50 反復・平均差 43・分散 170・自由度 49 → 90% CI [−21, −65]。Anderson–Darling の p=0.090 で正規性を棄却せず。
- §5.3 作例: M/M/1 二系(到着率 1・平均サービス 0.9 と 0.93)・5,000 客・10 対 — CRN 対の差の分散が明らかに小さい(図 6)。

## コスト/スケール含意

- Bonferroni は**ラン数を増やさずに主張を弱める**(帯が広がる)か、**同じ主張を保つためにラン数を増やす**かの二択。著者は "If there is a need to achieve an overall precision, then the effect will be to increase the number of simulation replications." と明記。
- 我々の数: 3 seed で 5 指標 Bonferroni(家族 95%)にすると相対半幅は **573.0·CV**(非補正は 248.4·CV)= **2.3 倍広がる**。

## 批判・限界

- 入門チュートリアルで、新規手法の提案ではない。多重比較の詳細は Banks et al. (2009) §12.2 に投げている(**未読**)。
- Bonferroni は保守的。Holm・FDR には触れていない。
- CRN の実装(どの乱数をどの変数に割り当てるか)は Law (2014) §11.2 に投げている(**未読**)。

## 関連

[[validation__sargent2016_interval-test]](同じ WSC 2016)・[[stats__hoad2007-law2020_replication-ci]](逐次停止則)・[[stats__myllymaki2024_global-envelopes]](Bonferroni を 1 本に畳む道)・`../v2-statistics-causal-research.md` §1-1・§1-2
