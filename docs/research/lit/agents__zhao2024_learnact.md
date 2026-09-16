# Zhao et al. 2024 — Empowering Large Language Model Agents through Action Learning (LearnAct)

- リンク: https://arxiv.org/abs/2402.15809 | 分野: ABM 方法論 #21 / 自然言語処理 #27 | 重要度: **P0**
- **一次確認**: **実読**(2026-09-17・サブが abs + `arxiv.org/html/2402.15809v2` 本文 §4.1/§4.2/§5.3/§5.5/Table 4/Table 5 を取得)。**親未確認**。v1 2024-02-24 / v2 2024-08-08。著者 Haiteng Zhao, Chang Ma, Guoyin Wang, Jing Su, Lingpeng Kong, Jingjing Xu, Zhi-Hong Deng, Hongxia Yang。

## 主張(claim)

**LLM エージェントの行動空間は固定されているのが普通で、それが成長の上限になっている**。失敗した課題のエラーから、**行動そのもの(Python 関数)を作り直す**。

- 抄録: 「LLM agents typically operate within fixed action spaces, limiting their potential for growth」
- 抄録: 「LLM revises and updates the currently available actions based on the errors identified in unsuccessful training tasks」

## 機構(mechanism)— D-71 に最も近い形

- **オフライン**(§4.1 訓練相 / §4.2 テスト相)。テスト時は学習しない:「After completing the learning phase, the agent possesses an updated action space and refined policy instructions.」/「In the testing phase, the agent attempts to solve problems in the same procedure as the SolveProblem process」。
- **失敗が引き金・1 反復に 1 件**(§4.1): 「Then a failed problem with action error is sampled with SelectErrorCase operator」。SelectErrorCase は「This step identifies error-inducing steps in action sequences based on the environment's feedback」——前提未達・効果なし・名前や引数の誤りを環境フィードバックから拾う。
- **停止条件は「行動エラーが消えるまで」**(§4.1): 「until successfully solving all the instances with no action errors or exceeding maximum optimization steps」。**頻度閾値ではない**。
- **草案は best-of-K**(§4.1): K 個サンプルし「μ = p_succ + p_stepacc」で採点、最良を採る。
- **更新は 2 種**(§4.1): 「We address errors by implementing either function updates or writing notes.」/「Consequently, ActionLearn can freely update the entire action space in each iteration.」
- **削除・統合の記述は無い**。§5.5「the number of actions tends to increase after learning」。

## 数値(出所つき)

- §5.3: 「For each task, we randomly select 3 instances for the training set, with the remaining instances used for testing.」/「The sampling number in our method is set to 4.」
- §5.5(Fig.3 右): 「**achieving optimal results within just two iterations**」。加えて「**excessive optimization for these mistakes can lead to overfitting to specific training cases**」=**回しすぎは害**。
- **Table 5(平均行動数・学習前→後)**: Robotic Planning **3.75 → 3.83** / AlfWorld **3.44 → 3.50**。=**行動は増えるが、ほとんど増えない**。
- **Table 4(更新の内訳)**: 関数更新 **0.86**(Robotic)/ **0.92**(AlfWorld)、ノート記入 0.14 / 0.08。=**大半は既存行の書き換え**。
- 抄録: AlfWorld で ReAct+Reflexion 比 **+32%**。
- 計算量(付録 A.2): O(MKI)(M=訓練事例・K=サンプル数・I=最大反復)。

## 効く箇所(seam)

[行動契約書 §7](../../design/v2-action-contract.md) 段2〜4 全体。D-71 の親案(未定義台帳 → 裁定 → 検査 → 採用 → 次ランから有効)は、**LearnAct の訓練相/テスト相の分離とほぼ同型**。

## 「結論でなく機構として」の入れ方

- **借りない**: Python 関数表現、AlfWorld の数値、best-of-K の採点式。
- **借りる**: (1) **「学習相とラン相を分ける」**——ユーザー決定の外部先行。(2) **「2 反復で最適・それ以上は過学習」**=裁定バッチを何周も回すと**訓練データ(そのランの偶然)に合わせに行く**という警告。v2 では「1 ラン 1 バッチ・採用は少数」で運用する根拠。(3) **Table 5 の増分(+0.08 行)**=**語彙はほとんど増えないのが正常**。24 語 → 25〜26 語が現実的な見込みで、「たくさん増えないから失敗」と判定しない物差し。(4) **Table 4 の内訳**=草案テンプレに「**新語か、既存行の書き換えか**」を選ばせる設計(D-71 答申 §2-B)。

## コスト/スケール含意

O(MKI)。v2 に写すと M=裁定に回す未定義語の数・K=草案のサンプル数・I=バッチの反復数。**2 反復で足りる**なら、語 30 × K 4 × I 2 = 240 呼 ≒ ランの外で数分。**ランの呼数予算には一切乗らない**。

## 批判・限界

- 課題が「解ける/解けない」で採点できる領域(Robotic Planning・AlfWorld)。**v2 には正解が無い**(現実整合アンカーとの距離が代理)。
- 訓練事例 3 件は極小。分散の報告が乏しい。
- **削除・統合が無い**ので、長期に回すと行動空間が汚れる(本論文の実験は短い)。
- 「行動エラーが消えるまで」を v2 に写すと**未定義行動をゼロにしようとする**ことになり、**穴台帳(D-50)の観測価値を潰す**——v2 は「消す」でなく「並べる」に読み替える必要がある。

## 関連

[[agents__wang2024_workflow-memory]] ・ [[agents__wang2025_programmatic-skill-induction]] ・ [[agents__yu2024_affordable-generative-agents]] ・ [D-71 答申](../v2-d71-vocab-growth-research.md) §1.2・§2-A/B/D ・ PENDING D-50(穴台帳)
