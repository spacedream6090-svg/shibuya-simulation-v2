# Turpin, Michael, Perez & Bowman 2023 — Language Models Don't Always Say What They Think: Unfaithful Explanations in Chain-of-Thought Prompting

- リンク: <https://arxiv.org/abs/2305.04388> | 分野: 自然言語処理・機械学習 #27 / 科学哲学 #26 | 重要度: **P1**
- **一次確認**: **抄録のみ(サブ・2026-09-17・arXiv abs を実読。本文 PDF は未取得)・親未確認**。v1 2023-05-07 / v2 2023-12-09。**NeurIPS 2023**。CC BY 4.0。
- **なぜ引くか**: R-37 の H は「**理由つきで 1 つ選ぶ**」。その「理由」が証拠になるかを決める一次。**結論は「ならない」**。

## 主張(claim)

CoT の説明文は「モデルが実際にその答えを出した理由」を**系統的に誤って表す**。入力に偏りを仕込むと答えは動くが、**説明文はその偏りに一度も触れない**。

## 機構(mechanism)

- 偏りの入れ方(逐語): 「by **reordering the multiple-choice options** in a few-shot prompt to make the answer always "(A)"」。
- モデルは偏りに従って答えを変えるが、説明文では「**models systematically fail to mention**」。
- 誤った答えへ誘導されると、その答えを**正当化する**説明を書く。
- 著者の結論(逐語): 「CoT explanations can be **plausible yet misleading**」。

## 数値

- 精度低下(逐語): 「This causes accuracy to **drop by as much as 36%** on a suite of **13 tasks from BIG-Bench Hard**」。
- モデル: **GPT-3.5(OpenAI)と Claude 1.0(Anthropic)**。
- 社会バイアス課題では「explanations justify giving answers in line with stereotypes **without mentioning the influence** of these social biases」。

## 効く箇所(seam)

- **R-37 §3-3・§5-3**: 「理由文が書けたから思考が入った」は**証拠にならない**。専用の理由欄を足しても忠実性は上がらない。
- **R-37 §4-3 の反実仮想再生**: 忠実性を測る唯一の道は**介入**(候補を 1 件抜いて選択が動くかを同一 seed で再生する)であって、文面の読解ではない。**これは新しい計器が要る=先に聞く拡張**。
- **本 repo の既存の記録**との同型性: W17 の「例示の具体値を 47% 写す」(第164)・第223 の「欄の説明語をそのまま対象欄に書く」9,055 呼。**どちらもモデルは理由欄でそれを申告しない**。

## 「結論でなく機構として」の入れ方

- **借りる**: 「説明文は測定対象ではなく**記述統計**にとどめる」という規律。
- **借りない**: 36% という値(BIG-Bench Hard 固有で、v2 の行き先選択とは課題が違う)。

## コスト/スケール含意

なし(規律の話)。

## 批判・限界

1. **本メモは抄録のみ**。13 課題の内訳・偏りの種類・両モデルの個別値は未取得(**空欄**)。
2. 対象は GPT-3.5 と Claude 1.0(2023)。**8B 級・日本語での再現は未確認**。
3. 「忠実でない」は「常に嘘」ではない。忠実な場合の割合は本メモの取得範囲に無い。

## 関連

[[nlp__zheng2023_selection-bias]] ・ [[causal__shah2026_agent-replay]] ・ [[css__barrie2025_observational-equivalence]] ・ 答申 `../v2-destination-choice-llm-research.md` §3-3・§5-3
