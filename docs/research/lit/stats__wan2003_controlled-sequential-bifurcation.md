# Wan, Ankenman & Nelson 2003 — Controlled Sequential Bifurcation: A New Factor-Screening Method for Discrete-Event Simulation

- リンク: https://www.informs-sim.org/wsc03papers/070.pdf | 分野: 統計学・因果推論 #23 / ABM 方法論 #21 | 重要度: **P0**(D-44 の「十分の線」)
- **一次確認**: **実読**(2026-09-17・サブが curl → システム python の pymupdf で全 9 頁抽出。§1 群スクリーニングの前提・§2.3 目的の 2 閾値・§3.3 まとめ・§4 実験評価を逐語照合)。**親未確認**。WSC 2003 Proceedings pp.565–573。雑誌版は Wan, Ankenman & Nelson (2006) *Operations Research* 54(4):743–755(**未読**)。

## 主張(claim)

因子が多い(数十〜数百)シミュレーションで、**全因子を個別に試すのは無駄**。群でまとめて試し、重要でない群は丸ごと捨てる(逐次二分法 SB)。ただし確率的シミュレーションでは SB に**性能保証が無い**。CSB は 2 段階検定を入れて、**因子ごとの第 1 種の誤り α と各段の検出力 γ を同時に保証する**。

逐語(≤125 字):
- 群スクリーニングの原理: "**The fundamental idea is to identify the important/unimportant factors as a group to save experimental effort**"
- 前提: "**In group screening the effects of the factors that are grouped together must have the same sign, and a main-effects model is typically assumed**"

## 機構(mechanism)— 2 つの閾値が肝

§2.3 の目的(逐語):
- "for those factors with effects ≤ Δ0, we require the procedure to control the **Type I Error** of declaring them important to be ≤ α"
- "for those factors with effects ≥ Δ1 we require the procedure to provide **power** for identifying them as important to be ≥ γ"
- "Those factors whose effects fall between Δ0 and Δ1 are considered important and we want the procedure to have **reasonable, though not guaranteed, power**"

手続き:
1. 全因子を 1 群にして群効果を検定。
2. 重要なら 2 つの部分群に分割。重要でなければ**群ごと不要と判定**。
3. 群が単一因子になるまで繰り返す(step-down 構造が因子ごとの第 1 種の誤り制御を含意)。
4. 各段は**二段階検定**で検出力 γ を保証。

その他(§3.3 逐語): "The procedure does not require an equal variance assumption, and **is valid with or without common random numbers**."

## 効く箇所(seam)

- **D-44 の「どこまでやれば十分か」の線を、文献の語彙で書ける**。方法論ゲート「expedient は感度試験で結果を駆動していないことを証明する」は現行のラン費用では満たせない(第195・第200)。CSB の語彙に置き換えると:
  **「expedient は、宣言した Δ0 以下の効果しか持たないことを、宣言した検出力 γ で示す」**。
  Δ0・Δ1・α・γ の 4 つを宣言すれば、「証明した」の意味が確定する。
- **Δ0 の置き方(親案・未リサーチ)**: seed 間 JSD の実測(在圏 5 エリア×24h で 0.000162 bits・行動 24 語で 0.00007)に定数倍。これは第202・第204 で既に測ってある。
- **CRN の有無を問わない**ので、我々が部分 CRN しか持てない(→ [[stats__currie-cheng2016_output-analysis]])という制約と両立する。
- **前提の「同符号」が実務上の難所**。122 行の expedient を束ねるには、各行が出力をどちら向きに押すかを先に宣言する必要がある。

## 「結論でなく機構として」の入れ方

- **借りない**: CSB のアルゴリズム実装・二段階検定の具体式。
- **借りる**: (1) **2 閾値 (Δ0, Δ1)** という言い方——「これ以下は駆動していないとみなす」「これ以上は必ず捕まえる」「間は保証しない」。(2) **群を丸ごと捨てる**という発想を D-44 (a)(入力側 JSD の片側規則)の正当化に使う。(3) **step-down が因子ごとの誤り制御を含意する**という構造(家族単位の誤りを設計で吸収する)。

## 数値(出所つき)

- 実験評価 §4: 合成の主効果モデル・**K = 10 因子**・**1,000 回のマクロ反復**で P{因子 i が重要と宣言される確率} を推定。
- Case 1: (β1,…,β10) = (2, 2.44, 2.88, 3.32, 3.76, 4.2, 4.64, 5.08, 5.52, 6)、Δ0=2・Δ0+Δ1 までを張る。**β1 は 0.05 未満、β6〜β10 は 0.95 以上**であるべき、という設計。
- 誤差 SD = m·(1 + I·群効果の大きさ)、I=0 が等分散・I=1 が不等分散。m = 1(大)/ 0.1(小)。
- 結果: 分散が小さいときは Cheng 法と同程度だが CSB の方が早く検出力に達する。**分散が大きい / 不等分散のとき Cheng 法は第 1 種の誤りと検出力の両方の制御を失う**。CSB は全ケースで制御を保つ。
- **本論文に必要ラン数の閉じた式は無い**("although the number of replications required to achieve this does differ substantially by case")。

## コスト/スケール含意(親の再計算・k=122)

| 方式 | 必要ラン数 | 39 万体(9.17 h) | 5,000 体(0.5 h) |
|---|---|---|---|
| 現行 OFAT(122 × 対照 × 2 seed) | 244 | 93 日 | **5.1 日** |
| Morris N=4(N(k+1)) | 492 | 188 日 | 10.3 日 |
| Sobol' N=64(N(k+2)) | 7,936 | 3,032 日 | 165 日 |
| **SB/CSB(重要因子 5 と仮定・設計点 48 × 3 反復)** | **144** | 55 日 | **3.0 日** |
| **SB/CSB(重要因子 2・設計点 26 × 3 反復)** | **78** | 30 日 | **1.6 日** |

- **結論**: **k=122 では Morris も Sobol' も現行 OFAT より高い**。安いのは群スクリーニングだけで、しかも 1.5〜3 倍どまり。**39 万体では設計を変えても解けない**——**5,000 体の階層に移すのが本筋**。
- 設計点数の見積り **2m·log₂(k/m)+2 は親の見積り(expedient)**。原典 Bettonvil & Kleijnen (1997) *EJOR* 96(1):180–194 は有料で**未読**。

## 批判・限界

- **主効果モデルを仮定**する。D-60(固定枠が結果を駆動した実例)が示すように、我々の系には交互作用がある=前提が怪しい。
- **同符号の前提**。122 行の符号を事前に宣言できるか未検証。
- 検証が合成データのみ(実モデルでの評価なし)。
- 必要ラン数の式が無い。
- 逐次なので**並列化しにくい**(艦隊運用と相性が悪い可能性)。

## 関連

Shi & Chen (2017) "Controlled Morris Method", WSC 2017 pp.1819–1830 <https://www.informs-sim.org/wsc17papers/includes/files/146.pdf>(**同日サブ実読**): 逐次確率比検定で "**Type I and Type II familywise error rates**" を制御。Morris 設計の費用は **B が (k+1)×k 行列 × N 軌跡 = N(k+1) ラン**。数値例 k=20・n0=20・α=β=0.1 で最終標本は因子ごと **20〜189**。Morris の μ–σ 図について著者は "**more of a commonsense rule than a rigorously justified screening method**" と明記。
[[stats__tenbroeke2016_sensitivity-abm]]・[[stats__secchi-seri2017_power-abm]]・`../v2-statistics-causal-research.md` §1-5
