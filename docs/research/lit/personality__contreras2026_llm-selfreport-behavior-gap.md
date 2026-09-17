# Contreras 2026 — An LLM-Native Psychometric Instrument Reveals a Self-Report–Behavior Gap Across 25 Models

- リンク: https://arxiv.org/abs/2606.09843 | 分野: 自然言語処理・機械学習 #27 / 検証と V&V・UQ #22 | 重要度: **P1**(**LLM-as-judge への直接の警告**)
- **一次確認**: **実読**(2026-09-17・サブが arXiv PDF を WebFetch 取得 → pymupdf で本文抽出 → 要旨と序論を逐語照合。**結果節の表は未転記=部分実読**)。**親未確認**。arXiv:2606.09843 v3(2026-07-07)・CC BY 4.0・著者 Juan Manuel Contreras(独立研究者)。

## 主張(claim)

「LLM の自己申告が行動を予測しない」のは、**人間の特性カテゴリを押しつけたせい**なのか、それとも**LLM の自己申告そのものの性質**なのか。これを分けるため、**人間心理学から借りるのではなく、LLM の行動からボトムアップに次元を導いた最初の心理測定尺度**を作った。結論: **LLM に固有の構成概念でも乖離は消えない**。したがって「人間とのミスマッチ」説は成り立たない。

## 数値(要旨)

- **300 項目**(240 Likert + 60 シナリオ)を **25 LLM・17 モデル系統**に **各 30 回**実施。
- 探索的因子分析で **5 因子**: **Responsiveness / Deference / Boldness / Guardedness / Verbosity**。**全因子 Tucker φ ≥ .957・α ≥ .930**。
- **2,500 の自由記述サンプル**を **151 人の人間**と **3 つの LLM 審査の合議**で評定。
- 逐語(≤125 字): "Humans and judges agreed about model behavior (¯r = .51), but self-report predicted neither the ratings nor objective text measures"
- **唯一の部分的例外は Verbosity**。人間評定に対する基準信頼性上限の **74%** に達する。ただし**生の出力長とは連動しない**。
- **★2 つ目の乖離**: Responsiveness では**自己申告は LLM 審査と相関(r = .53)したが、人間とは相関しなかった(r = .04)**。人間と審査は otherwise 一致(r = .59)。**3 つの測定すべてを 1 つの潜在構成が駆動するという説を形式的に棄却(p = .007)**。
- 表層特徴(長さ・書式・熱意マーカー)を統制しても、この共有分散は消えない。

序論が引く既知の問題(いずれも本メモでは二次): プロンプト書式・選択肢順への感受性(Gupta et al. 2024・Xie et al. 2025)/ **モデル能力とともに強まる黙従・社会的望ましさ**(Salecha et al. 2024・Dorner et al. 2023)/ 人間の因子構造が再現しない(Peereboom et al. 2025 ほか)。

## 機構(mechanism)

**自己申告項目と LLM 審査は、人間の観察者が共有しない分散源を共有している**。おそらくアラインメントで形づくられた「自己記述の様式」が両方に効く。だから「LLM に性格を与えて、LLM に評価させて、効いたと確認する」ループは**内部で閉じてしまう**。

## 効く箇所(seam)

- **本 repo の検証設計への直撃**: 指標 B(行動分布 JSD)・呼数・保存則のような**客観量**で測る現行方針は正しい側。**LLM 審査を検収に使う箇所があれば、この共有分散の汚染を疑う**。
- [[validation__ye2026_robustness-audits]] の TRAILS や [[validation__larooij2025_generative-abm-validation]] の「35 本中 15 本が主観のみ」と同じ系譜の警告。
- 「合議の中での一致率(within-ensemble reliability)を見れば LLM 審査は妥当」という検査は、**この交絡を検出できない**と著者が明記。

## 「結論でなく機構として」の入れ方

「LLM 審査を使わない」という禁止にはしない(コストが跳ねる)。**使うなら、人間評定または客観量との一致を別に測る**という手続きに落とす。

## コスト/スケール含意

本 repo での追試は不要。**既存の検収で LLM 審査を使っている箇所の棚卸し**が実務。

## 批判・限界

1. **結果節の表を未転記**(部分実読)。因子ごとの詳細な相関行列は未確認。
2. **独立研究者の単著・arXiv 未査読**(v3・2026-07)。
3. 5 因子(Responsiveness 等)は**この項目プールと 25 モデルに依存**。別の項目プールで再現するかは未検証。
4. 行動の指標は自由記述サンプルへの評定と客観テキスト指標。**エージェント的な行動(道具使用・意思決定)ではない**。

## 関連

- [[personality__han2025_llm-personality-illusion]]
- [[validation__larooij2025_generative-abm-validation]]
- [[validation__ye2026_robustness-audits]]
- 答申 [v2-personality-traits-research](../v2-personality-traits-research.md) §3-2
