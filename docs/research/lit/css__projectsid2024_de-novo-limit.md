# Altera.AL et al. 2024 — Project Sid: Many-agent simulations toward AI civilization(de novo の限界)

- リンク: https://arxiv.org/abs/2411.00114 | DOI: https://doi.org/10.48550/arXiv.2411.00114 | 分野: 計算社会科学 #25 / 科学哲学 #26 | 重要度: **P0**
- **一次確認**: **実読(サブ・arXiv HTML `arxiv.org/html/2411.00114v1` 本文)・親未確認**(2026-09-17)。v1 のみ(2024-10-31)。cs.AI 主・cs.MA 副。Comments「35 pages, 14 figures」。**journal-ref 無し=査読の有無は不明**。著者は Altera.AL ほか 13 名。**取得は付録 D の途中で切れている=付録 E(プロンプト)未読**。
- **本メモの範囲**: アーキテクチャ(PIANO)は扱わない。**「何が創発しなかったか」と「何を種として入れたか」と「実際に回した規模」の 3 点だけ**を採る。既存答申 [v2-science-claims-research.md](../v2-science-claims-research.md) §2 の記述(等級 **D**)の一次確認にあたる。

## 主張(claim)

Minecraft 上で 10〜1000+ 体の LLM エージェント社会を回し、役割分化・集団規則の遵守と変更・文化/宗教の**伝播**を示した。ただし**社会的革新そのものを de novo に生み出すことはできない**、と著者自身が限界節で明記している。

## 数値・逐語(出所つき)

### 1. de novo の限界(§7 Limitations・**本メモの核**)

基盤モデルが人間の知識で訓練されている以上、エージェントは(逐語 ≤125 字)

> 「**they cannot simulate de novo emergence of societal innovations and infrastructures**」

例として挙がるもの(逐語 ≤125 字): 「**such as the emergence of democratic systems, fiat economies, or communication systems**」。
もう 1 つの限界(逐語 ≤125 字): エージェントは「**lack robust innate drives—such as survival, curiosity, community—that catalyze genuine societal development**」。

→ **既存答申の「著者自身が『de novo の社会的革新はシミュレートできない』と明記」は §7 で裏づけられた。**

### 2. 宗教は創発ではなく注入(§5.3・§5.3.2・§8.4)

- Pastafarianism は創発ではなく「**a fixed doctrine introduced and propagated by a specific group of agents designated as Pastafarian priests**」(§5.3)。
- 種の数(逐語 ≤125 字): 「**with the exception of 20 priests that worship Pastafarianism**」(§5.3)。§8.4 は「**20 agents in the town of Meadowbrook who are spawned as Pastafarians**」。**500 体中 20 体 = 4%**。
- 改宗の測定は**キーワードの使用**("Pastafarian"/"Spaghetti Monster" = 直接・"Pasta"/"Spaghetti" = 間接)であり、**信念の測定ではない**(§5.3.2)。

→ 既存答申の「宗教は 20 体シード注入」は裏づけられた。**加えて「改宗の測定が語の使用だけ」という重要な限界が既存答申に落ちている。**

### 3. 実際に回した規模(§5.3・§8.4)— **抄録と本文が食い違う**

- 逐語(≤125 字): 「**We have also simulated societies with over 1000 agents, but these runs exceeded the computational constraints**」(Minecraft サーバの制約)で「causing agents to be sporadically unresponsive」。
- したがって「**the results below are analyzed using a single 500-agent simulation**」(§5.3)。
- その 1 本の設定(§8.4): 「**500 agents all spawned within a 1000 by 1200 area, run for 9000 seconds**」。6 つの町(各約 33 体)+ 農村約 302 体。
- **抄録は「10 - 1000+ AI agents」、§6 Discussion は「a thousand agents」と書く**。**分析に使われたのは 500 体 1 本**。

### 4. 課税と集合規則(§5.2・§8.3)

- 設定(§8.3): 「**25 constituents who participate in voting and taxation, 3 influencers**」+ 選挙管理 1 体。20 分ラン・中点で憲法改正・各側 5 回の徴税期(120 秒間隔・入金窓 20 秒)・条件ごとに 4 反復。
- 基準(§5.2・逐語 ≤125 字): 「**agents deposited roughly 20% of their inventory, as stipulated by the constitution, into the community chest**」。
- 反税改正後(逐語 ≤125 字): 「**when the tax rate decreased from 20% to 5-10%, agents reduced taxes paid from 20% to 9%**」。
- 対照 2 種: 憲法を凍結すると税率は変わらない / アーキテクチャを削ると賛税・反税の**両方で税率が上がった**。
- **法そのものは研究者が事前に書いたもの**でエージェントが作ったのではない(§5.2)。取締りは無い(§8.3: 「chose not to incorporate guards or police within these simulations」)。

→ 既存答申の「反税派で納税率 20%→9%」は裏づけられた(**ただし「反税派で」ではなく「反税の憲法改正後に」**が正確。さらに **N は 25+3+1 体の別実験**であって 500 体ランではない)。

## 効く箇所(seam)

- **「LLM 社会シムで創発は起きるか」の問いに、この分野で最も大規模な試みの著者自身が引いた線**。§7 の 1 文は、[[css__barrie2025_observational-equivalence]] の観測的同値と**別経路で同じ結論**に至る(Barrie は「区別できない」、Sid は「原理的にできない」)。2 本並べると、**「創発した」と書く主張の根拠が非常に細くなる**。
- **「伝播は起きるが創造は起きない」**という切り分けは、この repo の造語・組織形成の観察(CLAUDE.md §3「促進せず観察する」)の位置づけを外から支える。**観察して「出なかった」は分野の既定の結果**であって失敗ではない。
- **規模の主張の読み方**: 抄録の「1000+」は**実行したが分析していない**。この repo が規模を主張するときの作法の反面教師(**分析に使った本数を書く**)。
- **改宗を語の使用で測った**のは、この repo の「会話から関係を抽出」(C10 R9′)と同じ計測の型。**同じ弱点(語の使用 ≠ 状態の変化)を持つ**ことを先に書いておく材料。

## 「結論でなく機構として」の入れ方

- **借りない**: PIANO アーキテクチャ、Minecraft の実質。
- **借りる**: (1) **「de novo の創発は期待しない」を設計書の前提として明記**(著者の逐語を引く)。(2) **種を入れた要素は「種の数/全体」で書く**(20/500 = 4%)。(3) **「実行した規模」と「分析した規模」を分けて書く**。(4) **語の使用で測った量は「状態の変化」と呼ばない**。

## コスト/スケール含意

500 体 × 9,000 秒 = 1 本。1000 体超は**サーバ側の制約で分析に使えなかった**。計算費の記載(GPU・トークン・金額)は取得範囲に無い=**空欄**。

## 批判・限界

- **査読の有無不明**(journal-ref 無し・v1 のみ)。
- **抄録と本文で規模の書き方が食い違う**(1000+ vs 分析は 500 体 1 本)。
- 課税実験は **N=25+3+1・4 反復**。seed 間分散の報告は取得範囲に無い。
- 改宗の測定が語の使用のみ。
- 付録 E(プロンプト)未読。
- 「de novo にできない」は**論証ではなく著者の見立て**(限界節での一言)。反証の実験は行われていない。

## 関連

[[css__barrie2025_observational-equivalence]] ・ [[abm__epstein2006_generative-sufficiency]] ・ [[validation__larooij2025_generative-abm-validation]] ・ `../v2-classical-vs-llm-simulation-research.md` ・ `../v2-science-claims-research.md`
