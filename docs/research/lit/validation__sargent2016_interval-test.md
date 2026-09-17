# Sargent, Goldsman & Yaacoub 2016 — A Tutorial on the Operational Validation of Simulation Models

- リンク: https://www.informs-sim.org/wsc16papers/016.pdf | 分野: 検証と V&V #22 / 統計学・因果推論 #23 | 重要度: **P0**
- **一次確認**: **実読**(2026-09-17・サブが curl → システム python の pymupdf で全 12 頁の本文抽出。§2.2.2・§2.2.3・作例の全数値を逐語照合)。**親未確認**。WSC 2016 Proceedings pp.163–177。著者 3 名。**付録 A(一標本)・付録 B(二標本)の手続き本文は未抽出=空欄**。同著者の WSC 2015 入門編(pp.1729–1740・<https://www.informs-sim.org/wsc15papers/182.pdf>)も同日実読。

## 主張(claim)

モデル検証で知りたいのは「差がゼロか」ではなく「**差が許容精度域 (L, U) の中か**」である。古典的な仮説検定は点についての判断なので形が合わない。区間仮説検定なら形が合い、しかも**第 2 種の誤り(不正なモデルを valid と認める確率)を初めて数量化できる**。

逐語(≤125 字):
- "**one is interested in determining if the accuracy of a model is within its acceptable range of accuracy specified by L and U**"(§2.2.3)
- "**Classical hypothesis tests determinations are typically about a specific point.**"(§2.2.3)
- "**The probability of a Type I error, α, is called the model builder's risk, and the probability of Type II error, β, is called the model user's risk**"(§2.2.3・Balci and Sargent 1981 を引く)
- "**In model validation, the model user's risk is especially important and must be kept small**"(§2.2.3)

## 機構(mechanism)— 区間統計手続き

仮説形: **H0: L ≤ D ≤ U vs. H1: D < L or D > U**(D = μ_Model − μ_Reference)。

| 段 | 中身 |
|---|---|
| Step 0 | 許容精度域 (L, U) と実験条件を宣言(**開発前に**) |
| Step 1 | 統計量を選ぶ(平均の比較なら分散未知・等分散の二標本 t) |
| Step 2 | 初期標本を取る(作例 n_R=10・n_M=15)→ プール分散 |
| Step 3 | **危険曲線**(operating characteristic 曲線)を β を変えて描き、L と U で使う β を選ぶ |
| Step 4 | **標本数を増やしたときの危険曲線**を見て実行可能な n を決める |
| Step 5 | 追加標本を取り、T が受容域に入るかで判定 |

- OC 曲線の定義: "**The OC curve is defined as the probability of accepting the null hypothesis when event E prevails, denoted PA(E).**"
- 恒等式: **α_L + β_L = 1**、**α_U + β_U = 1**(作例で β=0.40 を選ぶと α=0.60)。
- 検定表 (Table 2): MODEL が Simulation Model・REFERENCE が Analytical Model なら**一標本**、REFERENCE が Simulation Model か System なら**二標本**。
- 前提: 両側のデータが **NIID**(終了型なら反復法、定常型なら反復法かバッチ平均法)。

## 効く箇所(seam)

- **事前登録 §2 の H1〜H5 はすべて「帯」の形**(JSD ≤ 0.0122・|Δ| ≤ 0.05・±1 h)。したがって**この手続きがそのまま当たる**。
- ただし **KDDI は 1 観測**なので、我々は Table 2 の**一標本の側**(参照の値が固定)。付録 A の手続きが読めていない=ここが未確認の穴。
- **いまの受入表は α だけを見て β を一度も計算していない**。3 seed のまま Step 3〜4 を回すと「この標本数では帯 (L,U) について意味のある結果が出ない」と出る可能性が高い(作例でもそうなった)。
- WSC 2015 §5.3.2「系のデータが足りないと統計結果が meaningless になる」という著者自身の留保が、我々の状況(実測 1 本・seed 3 本)に直接当たる。

## 「結論でなく機構として」の入れ方

- **借りない**: R コードと OC 曲線の作図。
- **借りる**: (1) **仮説の向き**(H0 を「帯の中」に置く)。(2) **α=製作者危険 / β=利用者危険**という呼び分け——「我々が損をする誤り」と「利用者が損をする誤り」を分けて台帳に書く。(3) **Step 3〜4 の順序**(危険曲線を見てから標本数を決める。先に標本数を決めない)。(4) **許容精度域を開発前に宣言**(WSC 2015 推奨手順 第 2 項)=事前登録の正当化。

## 数値(出所つき)

- 作例(§2.2.3・図 16〜19): (L,U)=(−0.75, 0.75)。初期 n_R=10・n_M=15 → M̄=7.067・R̄=7.300・S²_M=2.638・S²_R=2.233・S²_P=2.480。
- Step 4 で n_R=20・n_M=25 を採用 → M̄=7.120・R̄=7.800・S²_P=2.740。T の受容域 (−1.262, 1.262)・**T=−1.369 → 棄却=不合格**。D の受容域 (−0.627, 0.627)・実差 −0.680。
- **L を −1.00 に緩めると同じ T が受容域 (−1.766, 1.262) に入り合格**(帯の広さが結論を変える実例)。
- 理論値 D = 6.890 − 7.760 = −0.870 で、両判定とも理論と整合。
- §2.2.2: 単変量手続き + **Bonferroni の不等式**で同時信頼区間(s.c.i.)を作る(Balci and Sargent 1984 を指示)。

## コスト/スケール含意

- **追加ラン 0 本で Step 1〜3 まで実行できる**(既存 3 seed のプール分散で危険曲線が描ける)。
- Step 4 が「もっと標本が要る」と言ったとき、それが **D-70 の N の議論と同じ壁**に突き当たる。作例でも「the sample sizes need to be increased significantly if the hypothesis test is going to have 'meaningful results'」と書かれている。

## 批判・限界

- **正規性・独立性**を要求する(NIID)。我々の JSD やピーク時刻は正規とは限らない。
- 平均の検定に限定した説明(「他の統計的性質にも使えるが、対応する OC 曲線が計算できる場合に限る」と本文が明記)。**JSD のような距離量にそのまま当たるかは未確認**。
- 原典 Sargent (2015b) *J Simulation* doi:10.1057/jos.2014.30 は未読。付録 A・B の手続きも未抽出。
- チュートリアル論文であり、査読付きの新規性主張ではない。

## 関連

[[stats__lakens2017_tost-equivalence]](同じ発想の心理統計版)・[[stats__currie-cheng2016_output-analysis]](同じ WSC 2016 の出力解析編・Bonferroni)・[[validation__operational-validity-overview]]・`../v2-statistics-causal-research.md` §1-1
