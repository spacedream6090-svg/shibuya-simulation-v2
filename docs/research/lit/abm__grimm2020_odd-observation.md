# Grimm et al. 2020 — ODD 第 2 次更新と補遺 S1「Observation」(個体レベルの観察の正典)

- リンク: https://www.jasss.org/23/2/7.html(補遺 S1: <https://www.jasss.org/23/2/7/S1-ODD.pdf>)| 分野: ABM 方法論 #21 / 検証と V&V #22 | 重要度: **P0**
- **一次確認**: **実読(サブ)**(2026-09-17・S1 の PDF を curl → システム python の pymupdf で全 62 頁抽出し、p.22–23 の Observation 節と p.52 の例文を逐語照合。本文 HTML も別途取得)。**親未確認**。
  - 書誌: *JASSS* **23**(2) 7、2020-03-31、**doi:10.18564/jasss.4259**。著者 19 名(Grimm, Railsback, Vincenot, Berger, Gallagher, DeAngelis, Edmonds, Ge, Giske, Groeneveld, Johnston, Milles, Nabe-Nielsen, Polhill, Radchuk, Rohwäder, Stillman, Thiele, Ayllón)。
  - S1 は **Railsback & Grimm 教科書の Chapter 03 ダウンロード**としても配布されている(<https://www.railsback-grimm-abm-book.com/E2-Downloads/Chapter03/ODD_GuidanceChecklists_2020.pdf>)。
  - **未読**: S2〜S7 補遺、11 の design concept のうち Observation 以外、Zurell et al. 2010(virtual scientist の原典)、Railsback & Johnson 2011 の原論文。

## 主張(claim)

**「観察(Observation)」は ABM 記述の標準 ODD の正式な design concept** であり、**個体レベルの観察は明示的に認められている**。観察の設計は「実験の設計」とは別項目で、**何を観察しないかを明示することが要求される**。

## 機構(mechanism)

ODD の要素の順(Fig. 1): 1 Purpose and patterns / 2 Entities, state variables and scales / 3 Process overview and scheduling / 4 Design concepts(11 概念・Observation はその 1 つ)/ 5 Initialization / 6 Input data / 7 Submodels。

### Observation 節の逐語(S1 pp.22–23)

- "This concept describes **how information from the ABM is collected and analyzed, which can strongly affect what users understand and believe about the model.**"
- "This concept is **not** intended to document how simulation experiments and model analyses are conducted, but instead to describe **how information is collected from the model** for use in such analyses."
- "Observation is important because ABMs can be complex and produce many kinds of output: **it is impossible to observe and analyze everything that happens in such a model so we must explain what results we do observe.**"
- "The ODD description needs to state how such statistics were observed: **which state variables of which agents (e.g., were agents categorized?) were observed at what times, and how they were summarized.**"
- "**It is especially important to understand whether analyses considered only measures of central tendency (e.g., mean values of variables across agents) or also observed variability among agents**, e.g., by looking at distributions of variable values across all agents."
- **個体レベルの観察**: "**Modelers sometimes also collect observations at the agent level, e.g., by selecting one or more agents and having them record their state over simulated time.** Such observations can be useful for understanding behaviors that emerge in a model."
- **virtual scientist**: "This "virtual scientist" technique (**modeling the data collector; Zurell et al. 2010**) strives to understand the biases and uncertainties in the empirical data by reproducing them in an ABM where unbiased and accurate observations are also possible."
- 記述せよ(Describe): ①"The key outputs of the model used for analyses and how they were observed from the simulations." ②"Any "virtual scientist" or other special techniques used to improve comparison of model results to empirical observations."

### 例文(S1 p.52・Railsback & Johnson 2011, *Ecol Model* 222:3305–3319)

- "Graphical output on the model interface shows the habitat type of each cell, via cell color. Bird locations are also shown."
- "**The model randomly selects one bird per day and displays a trace of its movement during the day, so foraging patterns can be observed.**"
- "**Virtual surveys** are a special kind of observation designed for comparison of model results to field surveys of bird populations; they simulate the methods used by field biologists to estimate bird densities **so that the results are affected by the same biases as the real surveys.**"

もう 1 例(Wild Dog model, Railsback & Grimm 2019 第 16 章): 絶滅確率は "the fraction of **500 replicate simulations** in which there are no dogs alive after 100 years"。著者自身が **"How long these simulations are, and how many replicates are executed, are arbitrary observation decisions."** と書いている。

### 本文側(逸話規律の裏側)

- Box 1(要素 1)"**The patterns are observations, at the individual or system level, that are believed to be driven by the same processes**"
- Box 1 "**Reporting, in the first ODD element, only those patterns that the model could capture would resemble "HARKing"**" / "**Better practice would be to report on missing patterns**"
- §3.7 "there is no specific place in ODD for emergent patterns"(→ §4.7 で patterns を要素 1 へ移した)
- §3.1 "**Describe what the program does, not what you think the model does**"(narrative の落とし穴)

**注**: "anecdote" という語は S1 にも本文にも **0 回**。逸話規律は「HARKing 禁止」「中心傾向か分布か」「何を観察しないかを書け」の 3 つの形で入っている。

## 効く箇所(seam)

- **M1(個体カルテ)は ODD の語彙で書ける**。自前宣言にしなくてよい=設計者の指紋が減る。
- **「1 日 1 個体を無作為に選び、その日の trace を出す」が査読論文の実装として存在する**=v2 の抽出規則(答申 §2 O5)と粒度(O1)の最も近い先行。
- **v2 の計器盤(3 面)は「実験・判定」の側で、M1 は「収集」の側**——S1 が両者を別項目と明記している。
- **virtual scientist** は v2 の KDDI 在圏照合(在圏の定義に合わせて数える)が既に採っている形。**場所カルテを「KDDI と同じ数え方」で作る道**がここから開く。
- **「中心傾向か分布か」**は D-68(個体の同質性)と計器盤 G-8「分布で報告」(第203)に直結。

## 「結論でなく機構として」の入れ方

- **借りない**: NetLogo の画面部品・生態学の例そのもの。
- **借りる**: (1) **Observation を ODD の 1 項目として設計書に立てる**。(2) **どの体のどの状態変数を、いつ、どう要約したかを書く**という記述義務。(3) **無作為 1 個体の trace**。(4) **virtual scientist**(観測の仕方を模す)。(5) **合わなかったパターンも書く**(HARKing 禁止)。

## 数値(出所つき)

- ODD の要素 = **7**(design concepts は **11**)。
- Wild Dog の例: **500 反復・100 年**(著者は「恣意的な観察上の決定」と明記)。
- Railsback & Johnson の例: **1 日あたり 1 羽**。

## コスト/スケール含意

S1 には計算コストの記述が無い。**個体レベル観察のコストの議論は ODD の範囲外**(答申 §2-C は OpenTelemetry 側と自前の算術で埋めている)。

## 批判・限界

- S1 は**ガイダンス文書**であって実証研究ではない。「1 羽が適切」の根拠は書かれていない(原論文未読)。
- 生態学の ABM が母集団で、**40 万体規模・LLM 判断層の話は一切無い**。
- 本メモは S1 の Observation 節と 2 つの例文のみ。**他の 10 の design concept は未読**。

## 関連

[[abm__grimm-railsback2012_pom-multiscope]](同著者の POM 側)・[[agents__park2023_generative-agents-replay]](無作為 1 体の replay)・[[transport__matsim-via_agent-facility-queries]](道具の実装形)・`../v2-micro-observation-research.md` §1-4
