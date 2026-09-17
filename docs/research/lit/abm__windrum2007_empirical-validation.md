# Windrum, Fagiolo & Moneta 2007 — Empirical Validation of Agent-Based Models: Alternatives and Prospects

- リンク: https://www.jasss.org/10/2/8.html | 分野: 検証とV&V #22 / ABM方法論 #21 / 科学哲学 #26 | 重要度: **P0**
- **一次確認**: **実読(サブ・JASSS 本文 HTML)・親未確認**(2026-09-17)。JASSS 10(2) 論文 8。受理 2007-01-08・公開 2007-03-31。段落番号は JASSS の §x.y 表記。

## 主張(claim)

ABM の経験的検証には**単一の標準手続きが無い**。実務で使われている較正・検証のやり方は大きく 3 系統に分かれ、どれも**識別問題(under-determination)**を原理的には解けない。

## 機構(mechanism)

### 1. 3 つのアプローチ(§4)

| 名 | 逐語(≤125 字) | 出所 | 段 |
|---|---|---|---|
| **Indirect Calibration Approach** | 「**first performs validation, and then indirectly calibrates the model**」「a pragmatic four-step approach to empirical validation」 | Dosi et al. 2006 | §4.4–4.9 |
| **Werker-Brenner Approach** | 「**a three-step procedure for empirical calibration**」「one tries to pick empirical parameters directly to calibrate the model」。第 3 段は "methodological abduction" | Werker & Brenner | §4.10–4.17 |
| **History-Friendly Approach** | 「**a calibration approach which uses particular historical traces in order to calibrate a model**」 | Malerba et al. | §4.18–4.25 |

著者は注 14 で「この 3 つは網羅ではなく、最もよく使われるものを選んだ」と明記。

### 2. 経験的検証の 6 つの中核問題(§2.3)

1. Concretisation vs. isolation / 2. As-if assumptions / 3. Strong vs. weak apriorism / 4. Analytical tractability vs. descriptive accuracy / 5. **The identification / under-determination problem** / 6. The Duhem-Quine thesis

### 3. 識別問題(§2.3(5)・本メモの核)

逐語(≤125 字): 「**different models can be consistent with the data that is used for empirical validation**」。計量経済学でいう identification problem として、Haavelmo (1944) を引く: 「**it is impossible for statistical inference to decide between hypotheses that are observationally equivalent**」。

§4.12: 「**assessing fitness amongst a class of models does not automatically help us identify a true underlying model**」。
§4.14: 「**The most common reason for under-determination in economics is the bias and incompleteness the available datasets.**」

### 4. ABM の頑健性を損なう 4 領域(§1.4–1.7)

model diversity / lack of comparability / lack of standard techniques / model–data relationship。

### 5. 未解決の 5 課題(§5.2)

(1) 経験に基づくモデル構築の代替戦略(**KISS / KIDS / TAPAS**)(2) 過剰母数化の帰結 (3) 政策分析における反実仮想の有用性と含意 (4) **十分に強い経験的テストの定義** (5) データセットの入手可能性・品質・偏り。

## 数値(出所つき)

なし(方法論のレビュー)。分類の次元は 4 つ(§3.3–3.6: object under study / goal of analysis / modelling assumptions / method of sensitivity analysis)。

## 効く箇所(seam)

- **「観測的同値(observationally equivalent)」は 1944 年の計量経済学の語であり、ABM 側には 2007 年に既に輸入されていた**。[[css__barrie2025_observational-equivalence]] の 2025 年の主張は、**新しい問題ではなく、LLM という新しい競合仮説(事前学習の再生)が候補集合に 1 つ増えた**という読み方が正確。
- **3 アプローチのどれを採ったかを宣言する**のが古典側の最低限。この repo の「較正と holdout の分離+アンカー台帳」は Indirect Calibration に最も近いが、**どれを名乗るかは未宣言**(別サブの監査対象)。
- **未解決課題 (4)「十分に強い経験的テストの定義」**は、受入表の合格線を決める作業そのものが 2007 年時点で分野の未解決問題だったことを示す=この repo の合格線が expedient であることは分野標準からの逸脱ではない。

## 「結論でなく機構として」の入れ方

- **借りない**: 3 アプローチのどれかをそのまま実装すること(経済 ABM 固有の手続き)。
- **借りる**: (1) **6 つの中核問題を「先に書く」欄**にする(特に 5 と 6)。(2) **識別問題を主張の強さの上限として明記する**(「このパターンを再現したから機構が正しい」とは言えない)。(3) KISS / KIDS / TAPAS の**3 択を宣言する**(この repo は「舞台データは KIDS 的に豊かに・機構はパターン駆動で最小に」=方法論 Phase 2 の中庸解に相当)。

## コスト/スケール含意

なし。

## 批判・限界

- 2007 年。**ベイズ較正・history matching・近似ベイズ計算は入っていない**(→ [[stats__ogara2025_history-matching-abm]])。
- 経済 ABM(進化経済学・産業動態)に強く偏っている。生態学側の POM / ODD は言及が薄い。
- 3 アプローチの**優劣は付けていない**。選択の基準は読者に委ねられる。

## 関連

[[abm__boero-squazzoni2005_empirical-embeddedness]] ・ [[abm__grimm-railsback2012_pom-multiscope]] ・ [[css__barrie2025_observational-equivalence]] ・ [[stats__ogara2025_history-matching-abm]] ・ `../v2-classical-vs-llm-simulation-research.md`
