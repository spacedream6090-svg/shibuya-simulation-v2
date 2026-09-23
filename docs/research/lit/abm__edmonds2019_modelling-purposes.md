# Edmonds et al. 2019 — Different Modelling Purposes

- リンク: https://www.jasss.org/22/3/6.html | DOI: https://doi.org/10.18564/jasss.3993 | 分野: ABM方法論 #21 / 科学哲学 #26 / 検証とV&V #22 | 重要度: **P0**
- **一次確認**: **実読(サブ・JASSS 本文 HTML)・親未確認**(2026-09-17)。JASSS 22(3) 論文 6。受理 2019-06-08・公開 2019-06-30。著者 10 名(Edmonds, Le Page, Bithell, Chattoe-Brown, Grimm, Meyer, Montañola-Sales, Ormerod, Root, Squazzoni)。**取得した HTML で JASSS の段落番号が落ちていたため、位置は節見出しで示す**(親は段落番号を補うこと)。

## 主張(claim)

シミュレーションの「良さ」は**目的ごとに違う基準で判定される**。1 つの目的で正当化されたモデルは、**別の目的では正当化されない**。目的の混同は「bad science のレシピ」。

## 機構(mechanism)— 7 つの目的と、それぞれの合格条件

| 目的 | 定義(逐語 ≤125 字) | Table 1 の必須特徴 | 合格に要るもの |
|---|---|---|---|
| **Prediction** | 「**the ability to reliably anticipate well-defined aspects of data that is not currently known to a useful degree of accuracy**」(via computations using the model) | 「**Anticipates unknown data**」 | 当時**モデラーが知らなかった**データを当てた事例が複数・適用範囲と精度の明示・較正と真の予測の分離・コード公開。**既知データや「見たことのある holdout」への当てはめは不可**(Meese & Rogoff の 40 中 37 の失敗を引く) |
| **Explanation** | 「**establishing a possible causal chain from a set-up to its consequences in terms of the mechanisms in a simulation**」 | 「**Uses plausible mechanisms to match outcome data in a well-defined manner**」 | 機構が対象の既知事実と対応・何を説明するかの明示・**複数パターンの同時再現(典型 3〜5)**・感度解析/雑音/多ラン・非本質過程の入替・反証の試み |
| **Description** | 「**an attempt to partially represent what is important of a specific observed case (or small set of closely related cases)**」 | 「**Relates directly to evidence for a set of cases**」 | 依拠した証拠・選択性・偏りの明示(ODD 級の記述標準)。**記述した事例を超える一般性を主張しない** |
| **Theoretical exposition** | 「**establishing then characterising (or assessing) hypotheses about the general behaviour of a set of mechanisms**」 | 「**Systematically maps out or establishes the consequences of some mechanisms**」 | 検査済み・公開・文書化されたコード・仮説の範囲・極端条件を含む広い感度試験・設計された反証実験の系列。**観測世界については何も主張しない** |
| **Illustration** | 「**to communicate or make clear an idea, theory or explanation**」 | 「**Shows an idea clearly as a particular example**」 | 合格は**明快さ**であって真実性でも完全性でもない。「これは例示だけだ」と書くこと |
| **Analogy** | 「**when processes illustrated by a simulation are used as a way of thinking about something in an informal manner**」 | 「**Provides a way of thinking about something; gives insights**」 | 「証拠との厳密な関係を意図していない」と明記し、そこから先の推論をしない |
| **Social learning** | 「**a tool for social learning when it encapsulates a shared understanding … of a group of people**」 | 「**Facilitates communication or agreement**」 | 共有理解・信頼・対話。関係者の力の非対称への配慮(critical companion posture)。**他の目的の経験的裏づけにはならない** |

### 目的の混同(§"Some Confusions of Purpose")

逐語(≤125 字):

- 「**establishing a simulation for one purpose does not justify it for another**」
- 「**It is the lazy assumption that one purpose naturally or inevitably follows from another that is the danger.**」
- 結論(斜体): 「**A confused, conflated or unclear modelling purpose leads to a model that is hard to check, can create misleading results**」…「a recipe for bad science」
- 序: 目的を変えて再利用するなら「needs to be re-justified with respect to **each** of the claimed purposes **separately**」

名前の付いた混同 6 つ: Theoretical exposition→Explanation / Description→Explanation / **Explanation→Prediction** / Illustration→Theoretical exposition / Illustration→Prediction(Limits to Growth)/ Social learning→Prediction(Cevennes)。

### 「予測」の定義の 4 要素

reliable(既知の条件下で働く)/ データが**モデラーにとって未知**(out-of-sample fitting では足りない)/ 予測対象は値・パターン・関係のいずれでもよいが曖昧さなく検査可能 / 精度が用途に対して有用。**「モデルを回して出力を得る」という弱い意味の predict は明示的に却下**。forecast と prediction の区別は採らない。

## 数値(出所つき)

- Explanation の合格条件として「複数パターンの同時再現 = **典型 3〜5**」(POM 由来・Grimm が共著者)。
- Meese & Rogoff の **40 中 37** の予測失敗(二次引用)。

## 効く箇所(seam)

- **この論文は「良い LLM 社会シミュレーション」の判定基準の骨格をそのまま与える**。判定は「何点か」ではなく「**どの目的を名乗り、その目的の合格条件を満たしているか**」。
- **「予測」を名乗る条件が非常に厳しい**。「モデラーが当時知らなかったデータ」=封印 holdout はこの条件を満たしうるが、**開封後に較正したら満たさない**。この repo の事前登録+封印はこの条件の実装形にあたる(充足の判定は別サブ)。
- **Explanation の「複数パターン同時 3〜5」**は、パターン台帳ゲートに数の下限を与える唯一の外部根拠。
- **混同 #3 Explanation→Prediction** は、LLM 社会シムで最も起きやすい誤り(「もっともらしく振る舞った」→「だから予測できる」)。

## 「結論でなく機構として」の入れ方

- **借りない**: 7 目的の分類を設計書の章立てにすること。
- **借りる**: (1) **ラン/答申ごとに目的を 1 つ宣言する欄**(受入表の頭)。(2) **Explanation を名乗るときは同時照合パターン数を書く**(3〜5 が下限の目安)。(3) **Prediction を名乗るときは「誰がいつ知らなかったデータか」を書く**。(4) **目的を変えて再利用したら再正当化する**規律。

## コスト/スケール含意

Explanation の要求(多ラン+感度+非本質過程の入替+反証実験)は**計算費の主要因**。目的を Explanation に据えると費用が跳ね上がることを事前に見積もれる。

## 批判・限界

- **査読誌の論説的な立場表明**であり、7 目的の分類自体に経験的裏づけは無い(著者らも網羅性を主張していない)。
- 目的が**複数ある場合**の扱いが弱い(「それぞれ別に正当化せよ」で終わる)。実務では目的は混ざる。
- LLM を使う系は想定外(2019 年)。**「訓練データに答えが入っている」という予測の失効経路は扱われていない**=[[css__barrie2025_observational-equivalence]] と [[validation__larooij2025_generative-abm-validation]] で補う必要がある。
- 取得 HTML で段落番号が落ちた。**親は段落番号を補って引用位置を確定すること**。

## 関連

[[abm__epstein2008_why-model]] ・ [[abm__grimm-railsback2012_pom-multiscope]] ・ [[validation__larooij2025_generative-abm-validation]] ・ [[abm__edmonds-hales2003_replication]] ・ `../v2-classical-vs-llm-simulation-research.md`
