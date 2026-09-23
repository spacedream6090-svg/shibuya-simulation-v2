# Barrie & Törnberg 2025 — Emergent LLM behaviors are observationally equivalent to data leakage

- リンク: https://arxiv.org/abs/2505.23796 | DOI: https://doi.org/10.48550/arXiv.2505.23796 | 分野: 計算社会科学 #25 / 科学哲学 #26 / 自然言語処理 #27 | 重要度: **P0**
- **一次確認**: **実読(サブ・arXiv HTML `arxiv.org/html/2505.23796v1` 本文)・親未確認**(2026-09-17)。v1 のみ(2025-05-26)。cs.CL 主・cs.GT 副。**Comments 欄・journal-ref ともに無し=査読の有無は不明**。著者 Christopher Barrie, Petter Törnberg。**本文に節番号が無い**(References と "1 Appendix" のみ)ため位置は段落で示す。**付録は未読**。

## 主張(claim)

Ashery et al. が *Science Advances* で報じた「LLM 対が名付けゲームで**自発的に言語規範を創発する**」という結果は、**事前学習で既に見た規範の再生**として同じくらいよく説明できる。両者は**観測上区別できない**。

## 機構(mechanism)

### 1. 何が争点か(段落 1・8)

対象は Ashery et al., *Science Advances* 11(20): eadu9368 (2025-05)。主張は「interacting LLMs spontaneously exhibit emergent norms characteristic of simulated models of human populations」。

反論の核(段落 8・逐語 ≤125 字): 観測された規範は「**observationally equivalent to a series of LLM agents mapping the payoff description to its pretraining knowledge**」(of coordination games)。言い換え: エージェントは人間のように振る舞っているのかもしれないし、「**they could simply be reproducing what they know agents tend to do in the context of these games**」。

抄録の逐語(≤125 字): 「**the models simply reproduce conventions they already encountered during pre-training**」「**the observed behaviors are indistinguishable from memorization of the training corpus**」。

### 2. 証拠(段落 9–12・Figure 1)

- 原論文の system prompt をそのまま使い、**14 モデル(Llama・DeepSeek・Mistral・Gemma・Claude・GPT 系)に各 10 回**問う: 「Does this setup remind you of any existing model or theory in social science?」+ 成功後の最適手・大域収束の 2 問。
- 回答は gpt-4.1 が 3 次元(協調ゲームと同定できたか・最適手・収束)で注釈し、「**We then manually verify all of these annotations.**」
- 結果は **Figure 1 にしか無い**(図題「Percentage of runs per model where the model correctly identifies the dimension from the prompt」)。**本文に具体的な百分率は書かれていない**。本文の言明は「the models were able to correctly identify each of these dimensions」(ほとんどのモデルで)と「They are less able to predict the global convergence of the model—but many of the models manage this too」。
- 著者自身の留保: 「**the model does not explicitly identify this as a 'naming game' setup**」。gpt-4.1 の例示回答は "Coordination Game" と呼んでいる。

### 3. 原論文の対策がなぜ足りないか(段落 3・5–7)

原論文の対策は、箇条書き/物語形式のプロンプト変種・無意味文字列や数値の選択肢・払い戻しの理解を確認するメタプロンプト・「利得が対称だから事前に最適戦略は無い」という補足資料の議論。判定(逐語 ≤125 字): 「**None of the mitigation steps taken by the authors guards sufficiently against this risk.**」
理由 2 つ: 「**The inventory pruning rule is hard-coded into their simulation code**」(収束は機械的に起きる)/ 難読化(unicode トークン等)は「**is unlikely to prevent the LLM from recognizing the general structure of the game with sufficient certainty**」。

### 4. 提案(段落 13–16・逐語 ≤125 字)

- 「**One solution would be to 'invent' some completely novel game that the LLM has definitely not seen before.**」
- 有望な道具: 「**interpretability probing with sparse autoencoders**」・「**the measurement of next-token perplexity based on a given prompt setup**」
- 総括: 漏洩は「a fundamental and intractable issue without strict control over the training data」であり、「**the question of data contamination should be at the heart of future research in this area**」。

## 数値(出所つき)

- 14 モデル × 各 10 回(段落 9)。
- **百分率は Figure 1 のみ=未取得(空欄)**。親が Figure 1 を読んで数値を確定すること。

## 効く箇所(seam)

- **「創発」を主張するときの立証責任の形**を決める。古典側の語彙で言えば、これは [[abm__windrum2007_empirical-validation]] §2.3(5) の**識別問題(Haavelmo 1944 の "observationally equivalent")に競合仮説が 1 つ増えた**という事態。[[abm__epstein2006_generative-sufficiency]] の many-to-one 写像の LLM 版。
- **処方は 2 つしかない**: (a) LLM が見ていない場面を作る (b) 内部を覗く(SAE・perplexity)。**この repo の holdout(公開文献に無い在圏データ)は (a) の実装形**にあたる。逆に**公刊された stylized fact での照合は (a) を満たさない**([[validation__larooij2025_generative-abm-validation]] の data leakage 警告と同じ結論)。
- 「**シミュレーションコードに焼き込まれた規則が収束を機械的に起こしていた**」という指摘は、**エンジン側の規則が LLM の手柄に見える**という一般的な事故の型。この repo の「世界の変化はエージェント行動の結果として」という原則の検査項目になる(エンジン規則で説明できる部分を先に引き算する)。

## 「結論でなく機構として」の入れ方

- **借りない**: 名付けゲームの実質、Ashery への評価。
- **借りる**: (1) **「創発」と書く行の隣に「この結果を事前知識の再生で説明できないか」の 1 行**を必ず置く。(2) **看破テスト**(モデル自身に「この設定は何のモデルか」と聞く)を C8 の腕に足す候補 — 費用はほぼゼロ。(3) **エンジン規則で説明できる分を先に引く**(ハードコード由来の収束を創発と呼ばない)。

## コスト/スケール含意

看破テストは 14 モデル × 10 回のプロンプト。**この repo の規模でも 1 時間以内**。

## 批判・限界

- **査読なし・v1 のみ・コメント欄なし**。原論文への反論という性格上、片側の主張。
- **数値が図にしか無い**。本文で百分率を述べていないので、「どのモデルが何%」は再現できない。
- 「観測的同値」の**形式的な定義は与えていない**(段落 8 の 1 文が全て)。
- 「完全に新しいゲームを発明する」という提案は**実行可能性の検討が無い**(LLM は一般的なゲーム構造を認識できる、と著者自身が別の段落で書いている)。
- 付録未読。

## 関連

[[abm__epstein2006_generative-sufficiency]] ・ [[abm__windrum2007_empirical-validation]] ・ [[validation__larooij2025_generative-abm-validation]] ・ [[validation__ye2026_robustness-audits]] ・ `../v2-classical-vs-llm-simulation-research.md`
