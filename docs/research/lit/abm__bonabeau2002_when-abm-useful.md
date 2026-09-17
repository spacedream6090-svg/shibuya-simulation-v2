# Bonabeau 2002 — Agent-based modeling: Methods and techniques for simulating human systems

- リンク: https://doi.org/10.1073/pnas.082080899 | 全文: https://pmc.ncbi.nlm.nih.gov/articles/PMC128598/ | 分野: ABM方法論 #21 / 計算社会科学 #25 | 重要度: **P1**
- **一次確認**: **実読(サブ・PMC 全文 HTML)・親未確認**(2026-09-17)。*PNAS* 99(Suppl 3): 7280–7287(2002-05-14)。PMID 12011407 / PMCID PMC128598。Sackler Colloquium(2001-10-04〜06・Irvine)の招待論文。**pnas.org 本体は 403 で取得できず、PMC 版を読んだ**。

## 主張(claim)

ABM が他の手法に勝るのは 3 点。**創発を捉える・系の自然な記述になる・柔軟**。そして「いつ使うべきか」には具体的な 5 条件がある。

## 機構(mechanism)

### 1. 3 つの利点(逐語 ≤125 字)

「**(i) ABM captures emergent phenomena; (ii) ABM provides a natural description of a system; and (iii) ABM is flexible.**」著者は「創発を扱えることが他の 2 つを駆動している」と付す。

### 2. いつ ABM を使うか(Discussion "When Is ABM Useful?"・5 条件・逐語 ≤125 字)

- 「**When the interactions between the agents are complex, nonlinear, discontinuous, or discrete**」
- 「**When space is crucial and the agents' positions are not fixed**」(例: 避難・テーマパーク・スーパーマーケット・交通)
- 「**When the population is heterogeneous, when each individual is (potentially) different**」
- 「**When the topology of the interactions is heterogeneous and complex**」
- 「**When the agents exhibit complex behavior, including learning and adaptation**」

創発側の引き金として本文前半に挙がるもの: 閾値・if-then 規則・非線形結合で特徴づけられる振る舞い / 「memory, path-dependence, and hysteresis」/ 網の効果 / そして「**Averages will not work.**」

### 3. 難しさ・限界(逐語 ≤125 字)

- 誤用: 「**Because the technique is easy to use, one may wrongly think the concepts are easy to master.**」「This unusual combination often leads to improper use of ABM.」
- 粒度: 「**a model has to serve a purpose; a general-purpose model cannot work**」。詳細度の選択は「remains an art more than a science」。
- 人間を扱うこと: モデルは「**soft factors, difficult to quantify, calibrate, and sometimes justify**」を含む。
- 出力の読み方: 定性的にしか意味が無いとき「**one must not make decisions on the basis of the quantitative outcome of a simulation**」。
- 計算: 「**Simulating the behavior of all of the units can be extremely computation intensive and therefore time consuming**」「the high computational requirements of ABM remain a problem when it comes to modeling large systems」
- 事業応用: 「**Social simulation in business has not been very successful so far**」— 学習でなく予測を重視しすぎたため。

## 数値(出所つき)

本文に本メモが使える定量値は無い(事例紹介が中心)。

## 効く箇所(seam)

- **5 条件は「なぜ ABM でなければならないか」の既製の答え**。この repo の対象(渋谷の街路・異質な個体・位置が動く・網が複雑)は 5 条件のうち 4 つを満たす。**憲法や意義文書の 1 行を古典の語彙で書ける**。
- **「a general-purpose model cannot work」**は、世界被覆指標(WCI)が「なんでも入れる」方向に滑るのを止める外部根拠。**目的を先に決めてから被覆を決める**。
- **「計算費が大規模系での問題として残る」**は 2002 年の時点の言明。LLM 系はこれを 3〜4 桁悪化させた(→ [[mas__yang2024_oasis]]・[[compute__alves2026_llm-urban-mobility]])。

## 「結論でなく機構として」の入れ方

- **借りない**: 個別事例(NASDAQ・ISP)。
- **借りる**: (1) **5 条件を「この機能は ABM でなければならないか」の門にする**(パターン台帳ゲートの補助)。(2) 「**平均では駄目**」という判定基準 — 集計で説明できる量は LLM に回さない(この repo の分業そのもの)。(3) **定量出力を意思決定に使わない線**を受入表に書く。

## コスト/スケール含意

定量値なし。「大規模系では計算要求が問題として残る」という定性の言明のみ。

## 批判・限界

- 2002 年の招待論文。**検証・妥当性確認の手続きは扱っていない**(3 利点と 5 条件が中心)。
- 5 条件は**選言**(どれか 1 つでも当たれば使え)なのか**連言**なのかが本文から確定できない=**空欄**。
- 事業応用の否定的な評価(Fox のヒット予測)は逸話。
- pnas.org 本体は取得できていない。**頁・図表番号の突合は PMC 版に依存**。

## 関連

[[abm__axelrod1997_kiss-replication]] ・ [[abm__epstein2006_generative-sufficiency]] ・ [[abm__edmonds2019_modelling-purposes]] ・ `../v2-classical-vs-llm-simulation-research.md`
