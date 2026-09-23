# R-40 答申: TypeSafe AI「Jev」の詳細調査(2026-09-18・リサーチサブの一次読み)

<!-- hdr:v1 -->
- **分野**: 自然言語処理・機械学習 #27 / ソフトウェア工学 #29 / 研究倫理・情報法 #31 | **重要度**: P0(親判断・2026-09-15 第191)
- **一次確認**: **B** = 出典あり・空欄を明示(残務台帳へ写し済みまたは要写し) — サブ実読(docs .md 全頁・HN・MCA・2026-09-18・第242)+親確認 8 件(models/state/jaggedness/primitives/constants の逐語・HN 3 コメント本文・MCA 3 条項・Every・Cloudflare)。Vercel changelog・cookbook std・OpenRouter 不在は親未確認
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **分野地図**: [v2-discipline-map.md](v2-discipline-map.md)

> **親検収(第242・2026-09-18)**: ファイル実在・台帳不編集・API 呼び出し/登録なしを確認。親の一次確認(docs.typesafe.ai を直接取得): models.md「250,000 tokens per second / 1,200 requests per minute」「64k tokens per request; 32k tokens for `state` plus the longest question」・concepts/state.md「Each request evaluates one state」「CJK scripts … currently have lower accuracy」・model-jaggedness/jev-1.13.md「Jev suffers from context rot」と refund 0.72 / not_refund 0.47 = 1.19 の実例・primitives.md 11.5x/9.6x と約 32,000 tok 予算・constants.md DEFAULT_TIMEOUT 10.0 =**全て一致**。HN は Algolia API で item 49718727「exactly right!」・49718824「architecture is close to the chest for now, but we have talked about writing a paper」・49719245「yes a general model / no training at all」を**本文一致**で確認(投稿者 CompleteSkeptic=自ブログ言及から CEO 本人と推定)。MCA は typesafe.ai/legal/mca で「publish benchmarks or performance information about the Services」「Process Telemetry without restriction」「train a model to imitate the output」を**逐語一致**で確認。Every 記事(12 passages・7 欠陥中 6・0.35 s vs 8.83 s・約 580 倍・3 回とも同じ見落とし)と Cloudflare ページ(typesafe/jev・32,000 tokens・Third-party)も実読一致。**親未確認**: Vercel changelog・cookbook の std 0.0102・OpenRouter 不在・第238 ノートの訂正候補は反映済み(下記)。lit 行 18 は答申内に留置。

> **親検収(第242・2026-09-18)**: ファイル実在・台帳不編集・API 呼び出し/登録なしを確認。親の一次確認(docs.typesafe.ai を直接取得): models.md「250,000 tokens per second / 1,200 requests per minute」「64k tokens per request; 32k tokens for `state` plus the longest question」・concepts/state.md「Each request evaluates one state」「CJK scripts … currently have lower accuracy」・model-jaggedness/jev-1.13.md「Jev suffers from context rot」と refund 0.72 / not_refund 0.47 = 1.19 の実例・primitives.md 11.5x/9.6x と約 32,000 tok 予算・constants.md DEFAULT_TIMEOUT 10.0 =**全て一致**。HN は Algolia API で item 49718727「exactly right!」・49718824「architecture is close to the chest for now, but we have talked about writing a paper」・49719245「yes a general model / no training at all」を**本文一致**で確認(投稿者 CompleteSkeptic=自ブログ言及から CEO 本人と推定)。MCA は typesafe.ai/legal/mca で「publish benchmarks or performance information about the Services」「Process Telemetry without restriction」「train a model to imitate the output」を**逐語一致**で確認。Every 記事(12 passages・7 欠陥中 6・0.35 s vs 8.83 s・約 580 倍・3 回とも同じ見落とし)と Cloudflare ページ(typesafe/jev・32,000 tokens・Third-party)も実読一致。**親未確認**: Vercel changelog・cookbook の std 0.0102・OpenRouter 不在・第238 ノートの訂正候補は反映済み(下記)。lit 行 18 は答申内に留置。

> 依頼: 親ノート `docs/research/v2-jev-system-one-note.md`(第238・親の直読)より深く、**一次資料で**埋める。用途はユーザー検討中の構成「Jev = 速い層(判断のベース)/LLM = 遅い層/LLM を呼ぶかの門も Jev」。
> 規律: 子サブ不使用。Web は読むだけ(curl→stdout / WebFetch / WebSearch)。**ファイル保存・ダウンロードなし**。API キー取得・待機リスト登録・API 呼び出しは**していない**。
> 確認の別: **一次(原典を実読)** / **一次(ベンダー主張・原典を実読)** / **二次** / **未読**。ベンダーの主張と第三者の検証を分ける。

---

## 1. 要約(10 行以内)

1. **仕様は公開されている**。`docs.typesafe.ai` に全ページの Markdown(`.md` 付与)があり、**文脈長 64k/32k・レート 250,000 tok/s かつ 1,200 req/min・$0.042/MTok・Choice 255・Score 2〜10・US ホスト**まで原典で確認できた(第238 時点の「未公開」は解消)。
2. 追加で**「jaggedness(弱点)ページ」**が公開されており、数・日付・カウント・大きな state・敵対入力・否定/間接の苦手が**ベンダー自身の言葉**で列挙されている。
3. **1 リクエスト = 1 state**。質問は並列だが、**体が違えば state が違うのでリクエストを束ねられない**。5,000 体の tick ごと呼びは 1,200 req/min に**直撃**する(§5-d)。
4. **決定論の保証は無い**。公式 FAQ「Is Jev deterministic?」は JS 展開のため**未読**。代わりに自社 cookbook が **15 回反復で平均 std 0.0102**(LLM の temperature 0 より小さい)を示すが、**毎回 uid を変えており「同一入力の再現性」は測っていない**と自認。温度パラメータは存在しない。
5. **日本語は「精度が落ちる」と明記**(英語が主学習言語・CJK は「accepted but currently have lower accuracy」)。state は文字列/JSON オブジェクト/配列が可。
6. **アーキテクチャ・パラメータ数・RLCD の報酬設計・較正の測り方は非公開**。CEO は HN で「architecture is close to the chest for now」「we have talked about writing a paper」。論文なし。
7. **CEO 自身が「基本的にゼロショット分類器」という要約に "exactly right!" と同意**(HN・一次)。新規性はモデルクラスよりインターフェースと価格に寄る。
8. **評価の件数・信頼区間は非公開**。evals サイトに件数の記載は無い(「711 件」は二次記事の数字で、サイト上では確認できなかった)。参照ラベルは GPT-6 Astra と Claude Fable 5.1 の平均。
9. **独立検証は小規模 2 件のみ**(Every: 12 文・7 欠陥中 6 検出/約 25 倍速・約 580 倍安、Empryo: 5 判断点)。しかも **MCA §2.3(f) がベンチマーク公表を禁止**している。
10. **待機リスト以外の入口が 3 つある**: Vercel AI Gateway(`typesafe-ai/jev`)・Cloudflare Workers AI(`typesafe/jev`)・OpenRouter(プロバイダページは存在するが公開モデル API に掲載なし=未確認)。

---

## 2. 問い 1: API の限界

| 項目 | 値(逐語) | 出典 URL | 確認の別 |
|---|---|---|---|
| エンドポイント | `POST https://api.typesafe.ai/v1/systemone` / `Authorization: Bearer <API_KEY>` | https://docs.typesafe.ai/api.md | 一次(実読) |
| モデル一覧 | 「`GET /v1/models` returns the names your account can send in the `model` field」 | https://docs.typesafe.ai/models.md | 一次(実読) |
| **文脈長** | 「**64k tokens per request; 32k tokens for `state` plus the longest question**」/「The 64k budget covers the `state` plus all questions combined; the 32k budget applies to the `state` plus the single longest question.」 | https://docs.typesafe.ai/models.md | 一次(実読) |
| 文脈長(別記・**不一致**) | 「The number of questions in one request is limited only by the request's token budget, which the state and the questions share. **The budget is around 32,000 tokens, roughly 150,000 characters of English text.**」 | https://docs.typesafe.ai/primitives.md | 一次(実読) |
| 文脈長(第三者ホスト) | Cloudflare の Jev ページは context length **「32,000 tokens」** と記載 | https://developers.cloudflare.com/ai/models/typesafe/jev/ | 一次(実読) |
| **1 呼あたり質問数** | 上限の数値は無い。「limited only by the request's token budget」(上記) | https://docs.typesafe.ai/primitives.md | 一次(実読) |
| **Choice の上限** | 「A Choice question accepts **up to 255 options**, and adding options costs a few tokens each」 | https://docs.typesafe.ai/primitives/choice.md | 一次(実読) |
| Choice 255 超の扱い(ベンダー実装) | 「Jev supports a cardinality up to 255. For the higher cardinality choices, we do a **2 stage-system of scoring independently then making an explicit choice**, hence the occassional slowdown.」(Wikiracing デモの註) | https://typesafe.ai/blog/introducing-system-one-models-and-jev | 一次(ベンダー主張・実読) |
| **Score の段数** | 「`criteria`: An ordered array of level descriptions, from the low end of the scale to the high end. **Needs at least two levels and takes up to 10.**」 | https://docs.typesafe.ai/primitives/score.md | 一次(実読) |
| API 参照側の Score 記述 | 「An ordered array of level descriptions. **You must include at least two levels.**」(上限の記載なし) | https://docs.typesafe.ai/api.md | 一次(実読) |
| **レート制限** | 「**250,000 tokens per second / 1,200 requests per minute**」/「A request over either limit returns `429 Too Many Requests`.」 | https://docs.typesafe.ai/models.md | 一次(実読) |
| レート制限の不安定さ | 「**Rate limits are adjusting dynamically.** We are serving a very large volume of demand, and the limits above **can change without notice** while we do, as upcoming large GPU deals land and we let in more users. … **Higher limits are available on custom and enterprise plans.**」 | https://docs.typesafe.ai/models.md | 一次(ベンダー主張・実読) |
| **並列度** | 明示の同時接続上限の記載は**無い**(上の 2 本のみ)。SDK は sync/async 両方あり | https://docs.typesafe.ai/sdk/python.md ・ models.md | 一次(実読・記載なしを確認) |
| **バッチ API** | **無い**。llms.txt の全索引・api.md に batch エンドポイントは登場しない。並列化の手段は「1 リクエストに複数質問」のみ | https://docs.typesafe.ai/llms.txt ・ api.md | 一次(実読・不在を確認) |
| **タイムアウト** | Python SDK `DEFAULT_TIMEOUT = 10.0`(「Default timeout in seconds for each HTTP operation.」) | https://docs.typesafe.ai/sdk/python/api/constants.md | 一次(実読) |
| 再試行(SDK 既定) | `RetryPolicy(max_retries=2, backoff_initial=0.5, backoff_max=5.0, backoff_jitter=0.25, http_statuses={408,429,*range(500,600)}, respect_retry_after=True, timeout=30.0)` /「Total retry budget in seconds per SDK call, including the initial attempt and delays」 | https://docs.typesafe.ai/sdk/python/api/retries.md | 一次(実読) |
| エラーコード | `401` / `422 Unprocessable Entity` / `429 Too Many Requests` / **`529 Overloaded`**(「TypeSafe is temporarily overloaded. Retry after a short delay.」) | https://docs.typesafe.ai/api.md | 一次(実読) |
| リクエスト ID | 「The `x-typesafe-request-id` response header」 | https://docs.typesafe.ai/sdk/python/api/exceptions.md | 一次(実読) |
| **地域** | 「The Services are hosted in the **United States** ("U.S.")」/ 評価は「run from our laptops on the **West Coast** (this is where our service is currently based)」 | https://typesafe.ai/legal/privacy-policy ・ https://typesafe.ai/blog/introducing-system-one-models-and-jev | 一次(実読) |
| 入力の型 | 「Text only. String, JSON object, or array of text values. **No image, audio, or video input.**」 | https://docs.typesafe.ai/models.md | 一次(実読) |
| 環境変数 | `TYPESAFE_API_KEY` / `TYPESAFE_BASE_URL` / `TYPESAFE_DEFAULT_MODEL` / `TYPESAFE_LOG_LEVEL` | https://docs.typesafe.ai/sdk/python/api/constants.md | 一次(実読) |

**質問の独立性(設計上重要)**: 「Questions in the same request are **independent**: one answer does not become context for another question. If a later judgment depends on an earlier answer, **make a second request in code**.」(https://docs.typesafe.ai/primitives.md ・一次)

**バッチの効き(ベンダー計測)**: 「batching: **12.2x cheaper, 10.0x faster**」(GDPR 記事に 13 問。`TYPESAFE_MODEL = "jev-1.12"`)。同じ実験を `primitives.md` は「**11.5x cheaper and 9.6x faster**」と引用しており、**ドキュメント内で数値が食い違う**(版差と思われる)。出典: https://docs.typesafe.ai/cookbooks/parallel_questions.md ・ https://docs.typesafe.ai/primitives.md(いずれも一次実読)。

---

## 3. 問い 2: 料金・課金・利用規約・データ取扱い

| 項目 | 値(逐語) | 出典 URL | 確認の別 |
|---|---|---|---|
| 価格 | 「Price (per Btok / per Mtok) **\$42 / \$0.042**」/「**Charged per input token. Output tokens are free.** A Btok is a billion tokens and an Mtok is a million tokens.」 | https://docs.typesafe.ai/models.md | 一次(実読) |
| 最低料金・無料枠 | 数値の記載は**無い**。課金は**クレジット前払い制**: 「Customer must obtain TypeSafe-managed credits that are consumed by each Input」/ Purchased Credits は「expire on the earlier of (y) the end of the Term and (z) the date that is **12 months after the purchase date**」/ Promotional Credits は「TypeSafe may, but has **no obligation to**, issue Promotional Credits」 | https://typesafe.ai/legal/mca | 一次(実読) |
| 企業契約 | 「Higher limits are available on **custom and enterprise plans**. Contact sales@typesafe.ai.」 | https://docs.typesafe.ai/models.md | 一次(実読) |
| 学習利用 | 「**We will not train or fine tune any artificial intelligence or machine learning models on your prompts or other Input.**」/ MCA 4.1「The foregoing license does not grant TypeSafe the right to, and TypeSafe will not, include Customer Data in a dataset used to train (i.e., to modify the model weights of) any artificial intelligence or machine learning models **without Customer's prior consent**.」 | https://typesafe.ai/legal/privacy-policy ・ https://typesafe.ai/legal/mca | 一次(実読) |
| **テレメトリ(注意点)** | MCA 4.3「"Telemetry" means information generated in connection with the Services, such as technical logs, **hashes, summary statistics and classifications, metrics, and learnings** related to Customer's use of the Services. TypeSafe may **Process Telemetry without restriction**, including to improve the Services or TypeSafe's other products and services.」 | https://typesafe.ai/legal/mca | 一次(実読) |
| 保存 | 「We retain personal data about you for as long as reasonably necessary to provide you with the Services, or otherwise in support of our business or commercial purposes.」(**具体的な保存日数の記載なし**) | https://typesafe.ai/legal/privacy-policy | 一次(実読) |
| ZDR | 「We also offer **zero data retention (ZDR) for enterprise customers.** Contact privacy@typesafe.ai」 | https://docs.typesafe.ai/legal.md | 一次(実読) |
| ZDR(第三者ゲートウェイ経由) | Vercel: 「Jev supports **Zero Data Retention and No Training, enabled per request**」/ コード例 `gateway: { zeroDataRetention: true }` | https://vercel.com/changelog/typesafe-ai-jev-now-available-on-ai-gateway | 一次(Vercel の記述を実読) |
| 副処理者 | 「Customer provides general authorization for Typesafe to engage the following subprocessors as described in https://trust.typesafe.ai/subprocessors」/ 新規副処理者は「reasonable advance notice」+「object … within **15 days**」 | https://typesafe.ai/legal/data-processing | 一次(実読) |
| EU 移転 | 「Module 2 (controller-to-processor) of the EU SCCs …(g) the governing law is the law of **Ireland**」 | https://typesafe.ai/legal/data-processing | 一次(実読) |
| **SLA・稼働率** | **無い**。保証は「TypeSafe warrants to Customer that the Services will **perform materially as described in its Documentation**」のみ。「TYPESAFE DOES NOT WARRANT THAT CUSTOMER'S USE OF THE SERVICES WILL BE **UNINTERRUPTED OR ERROR-FREE**」。救済は 30 日以内の是正努力と未使用前払分の返金のみ | https://typesafe.ai/legal/mca | 一次(実読) |
| サポート | 「commercially reasonable efforts to support the Services in accordance with its standard support policies」/ support@typesafe.ai | https://typesafe.ai/legal/mca | 一次(実読) |
| **オンプレ/自前ホスト** | **不可**(MCA は「TypeSafe-hosted web interface … and the TypeSafe-hosted application programming interface」のみを許諾。オンプレ・重み配布・自己ホストの条項は**無い**)。さらに §2.3 が「reverse engineer, decompile, disassemble」「model distillation, train a model to imitate the output of the Services」を禁止 | https://typesafe.ai/legal/mca | 一次(実読・不在を確認) |
| **ベンチマーク公表の禁止(重要)** | §2.3(f) 「Customer will not … **(f) publish benchmarks or performance information about the Services**」 | https://typesafe.ai/legal/mca | 一次(実読) |
| **版の固定方法** | エイリアス `jev-latest` → `jev-1.13.0`、`jev-preview` → `jev-1.13.0`。「**An alias moves when a new release ships, so the answers behind it can change without a change on your side.** The response's `model` field reports the versioned ID that answered … **If you have tuned confidence thresholds against a specific version, pin that version's ID instead of the alias** and move to the new one on your own schedule.」/「Versioned IDs such as `jev-1.13.0` are accepted by the `model` field whether or not they appear in the list.」 | https://docs.typesafe.ai/models.md | 一次(実読) |
| 変更通知 | MCA 2.5「TypeSafe will use **commercially reasonable efforts** to provide advance notice of any updates to the API that TypeSafe believes will materially and adversely impact Customer's ability to integrate the API」(モデル更新そのものの通知義務は明記なし) | https://typesafe.ai/legal/mca | 一次(実読) |
| 顧客専用の微調整 | 「Jev is **not fine-tuned or LoRA-adapted with customer data**. … **the same weights serve every account.**」 | https://docs.typesafe.ai/models.md | 一次(実読) |
| 出力の権利 | 「TypeSafe does not claim ownership of Input and TypeSafe disclaims ownership of Output. TypeSafe hereby assigns to Customer all of its right, title, and interest, if any, in the Output.」 | https://typesafe.ai/legal/mca | 一次(実読) |

---

## 4. 問い 3: アーキテクチャと学習(公開情報の限り)

### 4-1. ベンダーの説明(逐語)

| 項目 | 逐語 | 出典 | 確認の別 |
|---|---|---|---|
| スタック全体 | 「We built a new stack entirely focused on automation: with a **new model architecture, parallel sampler for maximum efficiency**, and training method we call Reinforcement Learning for Calibrated Decisions (RLCD).」 | https://typesafe.ai/blog/introducing-system-one-models-and-jev | 一次(ベンダー主張・実読) |
| ホームページの同旨 | 「We built a new class of models, System One Models, to be natively used by machines. We're building with **a new architecture, a new sampler, and a new training algorithm**: Reinforcement Learning for Calibrated Decisions (RLCD).」 | https://typesafe.ai/ | 一次(ベンダー主張・実読) |
| **「並列サンプラー」の説明の全文** | 上記 2 文が**全て**。表で補足されるのみ: 「Sampling — **Parallel.** Generates all outputs in a single query. Incredibly efficient and hardware-aware.」(LLM 側は「**Sequential.** Generates one token at a time, each conditioned on the last.」) | https://typesafe.ai/blog/introducing-system-one-models-and-jev | 一次(実読・これ以上の説明は無いことを確認) |
| 並列である理由(CEO・HN) | 「**strings (and all sequential data structures) are not allowed at all — this is how we make sure all outputs can be computed in parallel (thus no output token cost)**」 | https://news.ycombinator.com/item?id=49719122 | 一次(CEO 本人の書き込み・実読) |
| **RLCD の説明の全文** | 「**Reinforcement learning for calibrated decisions** trains TypeSafe to return decisions and calibrated probabilities instead of generated text.」+「RLCD optimizes for a different output contract: The model does not generate text. It returns decisions and probabilities. **Higher probability should correspond to a greater chance that the answer is correct.**」+ 較正の定義(0.2 は約 20%・0.8 は約 80%・1.0 は 100%)+「These rates describe **groups of predictions**, not a guarantee about any single answer.」 | https://docs.typesafe.ai/introduction/machine-learning-primer.md | 一次(ベンダー主張・実読) |
| RLCD の目的関数 | 「Optimizes for … **Calibrated decisions: answers with epistemically honest probabilities on System One tasks.**」(報酬関数・損失・較正指標は**非公開**) | https://typesafe.ai/blog/introducing-system-one-models-and-jev | 一次(実読) |
| **基盤モデルからの派生か** | AI primer の図の alt 文が「**Pretrained language models** branch into muted RLHF and RLVR paths and an emphasized **RLCD decision-model path**」。本文も「**Pretrained language models have been adapted in two major ways. TypeSafe adds a third.**」→ **事前学習済み言語モデルからの派生**という位置づけ。ただし「技術的には言語モデルではない」とも: 「it is a structured data model, but **technically not a language model** (it doesn't generate language)」(CEO・HN) | https://docs.typesafe.ai/introduction/machine-learning-primer.md ・ https://news.ycombinator.com/item?id=49718437 | 一次(実読) |
| **パラメータ規模** | **公開なし**(docs・ブログ・HN のどこにも記載なし) | — | 未公開(不在を確認) |
| **アーキテクチャ開示** | CEO: 「**architecture is close to the chest for now, but we have talked about writing a paper**」 | https://news.ycombinator.com/item?id=49718824 | 一次(CEO 本人・実読) |
| **「ゼロショット分類器か」** | HN ユーザー petesergeant「This is basically a **zero-shot classifier** that can accept raw text (or structured text) as an input, and is able to classify that text as accurately (they claim) as a frontier-level LLM.」→ CEO の返答は**「exactly right!」**の一言 | https://news.ycombinator.com/item?id=49718727 | 一次(CEO 本人・実読) |
| 「Large Classification Model」要約への同意 | HN ユーザーの要約(「instead of autoregressive string output it instead outputs structured type-safe 'decisions' with probabilities/confidence scores, each generated in parallel … more like a Large Classification Model than a Large Language Model … all of this while still being instruction-tuned」)に対し CEO「**very accurate!** the one nuance I'd get into is I'd call it **"zero-shot" over "instruction-tuned"** (the latter often implies a particular distribution), but very safe for sharing」 | https://news.ycombinator.com/item?id=49719101 | 一次(CEO 本人・実読) |
| 顧客ごとの学習 | 質問「Is this actually a general model, or does it need training on the the data set it answers?」→ CEO「**1. yes a general model / 2. no training at all / 3. but it is focused on "System 1" tasks (more human judgment, less math reasoning)**」 | https://news.ycombinator.com/item?id=49719245 | 一次(CEO 本人・実読) |
| 構造化出力(constrained decoding)との差 | CEO「**constrained decoding (OpenAI-style structured outputs) make models dumber** unfortunately — the short+dense version is that simply masking logits is insufficient because **if ever a model was assigning probability to an invalid token, the model is by definition confused.** you'd be better off erroring IMO」 | https://news.ycombinator.com/item?id=49718849 | 一次(CEO 本人・実読) |
| 敵対入力 | CEO「we have played with this! the fascinating thing we've found so far is that **adversarial examples for our model are quite different from that of LLMs** so that they work even better together」 | https://news.ycombinator.com/item?id=49718450 | 一次(CEO 本人・実読) |
| 文字列生成をやらせた場合 | CEO「you could, but it the model is not optimized for text … **generating text is highly complicated and requires mode dropping to make long cohesive text**」 | https://news.ycombinator.com/item?id=49718416 | 一次(CEO 本人・実読) |
| **較正の測り方** | **非公開**。docs は「Calibration is measured across groups of predictions; it does not guarantee that an individual answer is correct.」と書くのみで、ECE・信頼度曲線・較正曲線の公開は**無い** | https://docs.typesafe.ai/concepts/system-one.md | 一次(実読・不在を確認) |
| **訓練データの出所** | ブログ FAQ に「Where does our training data come from?」の**見出しは存在するが、回答本文は静的 HTML に無い**(下記 §8)。CEO の関連発言: 「I don't want to shill my blog too much, but I will say **data is probably far most interesting than architecture**: https://www.completeskeptic.com/p/the-bitterest-lesson」 | https://typesafe.ai/blog/introducing-system-one-models-and-jev ・ https://news.ycombinator.com/item?id=49718824 | 見出しのみ一次/**回答は未読** |
| **「Is Jev just a smaller LLM?」** | ホームページ FAQ とブログ FAQ の両方に**見出しは存在するが、回答本文は静的 HTML に無い**(§8) | https://typesafe.ai/ ・ https://typesafe.ai/blog/... | **未読** |
| 論文・技術報告 | **無い**(CEO「we have talked about writing a paper」= 未執筆) | https://news.ycombinator.com/item?id=49718824 | 一次(実読) |
| 講演(AI Engineer・Databricks 等) | **見つからなかった**。一次の発信は X スレッド・ローンチブログ・HN スレッド(491 コメント)に限られる | — | 未発見 |

### 4-2. jaggedness ページ(弱点のベンダー自認・2026-09-17 レビュー)

`jev-1.13` の既知の弱点(出典 https://docs.typesafe.ai/model-jaggedness/jev-1.13.md・一次実読)。**9 項目**を逐語で:

1. **Literal reading** — 「`jev-1.13` answers the question you wrote, not the one you meant. Scoping words, negations, and implied conditions are read at face value.」
2. **Math and Numbers** — 「**Jev is not a calculator.**」/ 計数「`jev-1.13` **does not count reliably**. … The model recognizes the shape of an answer rather than tallying, and **the error grows with the size of the thing being counted.**」/ 数値表現「questions about colors using hex values will underperform compared to those using the English names」/ Score の内挿「**`jev-1.13`'s score levels are weak in numerical calibration.** It will not be able to help you reconstruct the exact number by interpolating between the nearest two levels.」
3. **Date and time comparison** — 「`jev-1.13` reads dates as text, not as ordered quantities.」
4. **Indirection** — 「A question about a property of a property or something that requires multiple hops of reasoning costs accuracy.」
5. **Large state full of irrelevant detail** — 「**Accuracy falls as the state grows with content unrelated to the decision.** Unrelated detail acts as a distractor」/ 末尾の註「**Jev suffers from context rot**, so unrelated material in the `state` costs you accuracy.」(※ `introduction.md` の「does not create context-rot」は**質問を足すことについて**の話で、state については逆の注意を書いている)
6. **Adversarial content** — 「State is data, and `jev-1.13` **does not treat it as hostile by default.** Content written to adversarially steer the model … can move the answer. We expect to improve on this in the future.」
7. **Contradictory instructions and criteria**
8. **Common-sense structural invariants** — 「**`jev-1.13` is extremely consistent, meaning you should expect quantitatively similar outputs for semantically similar inputs.** However there are many structural invariants one might imagine to hold that simply aren't guaranteed」。実例: 同じ問いを Noul と yes/no Choice で聞くと `noul` 0.22 に対し Choice `yes` 0.01(confidence 0.97)。肯定と否定を別々の Noul で聞くと `refund` 0.72・`not_refund` 0.47・**合計 1.19**。「**don't rely on expected structural invariance** … don't hold the model to arithmetic identities between separate questions.」
9. **Generation** — 「`jev-1.13` is not trained to generate text. While you can force it to by chaining choices, this will not work well and will be very slow.」

---

## 5. 問い 4: 評価の再現性

### 5-1. evals.typesafe.ai(ベンダー自身の評価)

| 項目 | 値(逐語/実測値) | 出典 | 確認の別 |
|---|---|---|---|
| 参照ラベル | 「we assume there is a correct compute graph (a "workflow" represented in code) and **use the predictions of the largest, smartest, and most expensive external models as reference probabilities**」/ 「the reference labels are generated via an **average of the responses of GPT-6 Astra and Claude Fable 5.1, both at high thinking**, answering every question in the harness. All other models are evaluated using the provider's default reasoning settings.」 | https://evals.typesafe.ai/ | 一次(実読) |
| **件数** | **記載なし**。4 ページ(index/security_incidents/agent_trace_observability/invoice_processing/customer_service)を全文抽出しても「N cases」の記載は無い。※二次記事の「711 cases」は、同ページの SVG 座標 `translate(322 711)` 等に由来する可能性が高く、**サイト上では確認できなかった** | https://evals.typesafe.ai/ | 一次(実読・不在を確認) |
| **信頼区間** | **記載なし** | https://evals.typesafe.ai/ | 一次(不在を確認) |
| **公開データ** | ダウンロードリンク・GitHub リンクは**無い**。あるのは 4 ワークフローの説明図と、モデル別の例示ケース(「A handful of cases: for each model, one where it alone differs from the other two; one where all three miss the reference; one where all three agree.」) | https://evals.typesafe.ai/ | 一次(不在を確認) |
| 4 課題平均(workflow 腕) | Jev **67.8% / \$0.0004 / 0.4 s** ・ sol 74.1% / \$0.0836 / 23.3 s ・ opus 5 73.1% / \$0.1761 / 37.8 s ・ terra 67.9% / \$0.0304 / 10.1 s ・ sonnet 5 67.8% / \$0.1174 / 78.1 s ・ luna 66.8% / \$0.0033 / 12.9 s ・ DS v4 pro 65.5% ・ DS v4 flash 64.4% ・ haiku 4.5 53.6% | https://evals.typesafe.ai/ | 一次(実読) |
| 課題別(Jev / 最良 LLM) | Security Incidents **61.7%** / opus 5 66.2% ・ Agent Trace **71.6%** / sol 76.6% ・ Invoice **61.8%** / sol 79.1% ・ Customer Service **76.0%** / sol 78.3% | https://evals.typesafe.ai/ | 一次(実読) |
| prompt 腕(参考・分解の効果) | opus 5 64.8→73.1 ・ haiku 4.5 18.1→53.6 ・ luna 51.9→66.8 ・ sol 63.4→74.1。「Averaged across the four example tasks, **every model is more accurate, cheaper and faster in the workflow than it is with the same policy as a prompt.**」 | https://evals.typesafe.ai/ | 一次(実読) |
| バイアスの自認 | 「These content of these workflows were not deliberately chosen nor constructed to make our model look good, and are not in our training distribution. **However, they were made by individuals on our model capabilities team, so some bias could exist.**」/「We use the average of GPT-6 Astra and Fable 5.1 as the reference answer, which **biases answers towards OpenAI and Anthropic's models.**」/「The LLMs use our **System One LLM wrapper** … this tends to be **slower and more expensive** than giving decisions without probabilities.」 | https://typesafe.ai/blog/introducing-system-one-models-and-jev | 一次(ベンダー自認・実読) |
| 幻覚 0% の根拠 | 「**Our number is not empirical.** Schema matching is guaranteed, thus we can confidently add 0% into the plots.」(LLM 側の数値は OpenRouter 由来で「there almost certainly is bias here」と自認) | 同上 | 一次(実読) |

### 5-2. 第三者(独立)の検証

| 出所 | 何を測ったか(逐語) | 独立性 | 確認の別 |
|---|---|---|---|
| Every(Dan Shipper 他) | 「the same four writing checks across **12 synthetic passages**」「six clear versions and six with deliberately introduced problems」/「Jev took a **median of 0.35 seconds per passage, versus 8.83 seconds for Fable 5.1 at high effort**」「roughly **25 times faster**」「Its estimated cost was about **580 times lower** than Fable's」/「**Jev caught six of the seven intended defects; Fable caught all seven.**」/「**Jev missed it in all three runs**」/ 著者の別実験「all 27 of my Every articles, alongside 10 deliberately AI-styled counterparts」「the same 21 questions concurrently across all articles, returning **777 judgments**」「**1,709 judgments** for an estimated total cost of less than a cent」 | 独立(早期アクセス利用者) | 一次(実読・WebFetch 経由の逐語) |
| Every の留保 | 「Just how well it gets the job done is still an open question.」「I'd want a **more thorough accuracy check before putting it into production**.」「Compare the model's accuracy to existing LLMs, and make sure it's accurate enough for your use case.」 | 同上 | 一次(実読) |
| Empryo | 5 判断点への組み込みと計測を公開していると報じられている(本答申では**原典未読**) | 独立を称する | **未読**(§8) |
| GitHub での再現 | 検索範囲では**独立再現リポジトリは見つからなかった**。二次記事が「a same-night Hugging Face reproduction」に触れるが URL は特定できず | — | **未確認** |
| **構造的な障害** | MCA §2.3(f)「Customer will not … **publish benchmarks or performance information about the Services**」 → API 経由の第三者ベンチマークは**契約上禁止**されている | https://typesafe.ai/legal/mca | 一次(実読) |

### 5-3. System One adapter(github.com/typesafe-ai/system-one-adapter-python)のコード

| 論点 | コードが示す事実 | 出典 | 確認の別 |
|---|---|---|---|
| 目的 | 「A drop-in replacement for `typesafe_sdk`'s `system_one` evaluation API, **backed by LLM APIs instead of TypeSafe**. Useful for comparing TypeSafe against an LLM on cost/speed/intelligence.」 | README.md | 一次(実読) |
| **確率の取り方** | **logprobs は一切使わない**。JSON Schema の各ラベルに `[0,1]` の確率フィールドを作り、**LLM に確率を書かせる**。`_schema.py` 冒頭: 「each a probability in `[0, 1]` carrying that label's criterion as its description」/ `Probability = Annotated[float, Meta(ge=0, le=1)]` | src/system_one_adapter/_schema.py | 一次(実読) |
| 正規化 | `normalize_probabilities_of_all_answers(...)`: 合計と 1 の差 `error` を測り、`PROBABILITY_TOLERANCE = 1e-6` を超え、かつ `enabled` なら `rescale_probabilities`(合計 0 なら一様分布)。元の分布は `original_probabilities` に保存 | `_utils/probability_normalization.py` | 一次(実読) |
| discrete モード | 「`probabilities = {answer: float(answer == selected) for answer in answers}`」= 選ばれた 1 つに 1.0 を立てるだけ | 同上 | 一次(実読) |
| **confidence の式(アダプタ実装)** | `choice_confidence = (max(p) - 1/n) / (1 - 1/n)` / `score_confidence = 1 - E[|i - mode|] / MAD_uniform`(`MAD_uniform = Σ|i - (n-1)/2| / n`) | `_utils/confidence_metrics.py` | 一次(実読) |
| **注意: 本家 Jev の式とは一致しない** | docs の Score 例(probabilities `{0:0.05, 1:0.3, 2:0.65}`・score 1.6・**confidence 0.78**)に上式を当てると **0.40**。Choice 例(`{0.08, 0.85, 0.07}`・**confidence 0.82**)に当てると **0.775**。→ アダプタの式は LLM 側の再実装であり、**Jev の confidence 統計量が同一である確証は無い**(docs は「`confidence` is a statistic computed from the probability distribution」としか書かない) | docs/api.md ・ docs/confidence.md ・ 上記コード | 一次(実読)+ サブの再計算 |
| 構造化出力 | OpenAI 側は Responses API + `{"type":"json_schema", "name":"evaluation", "schema":..., "strict": True}`(prompted 時は `{"type":"json_object"}`)。`store=False` を指定。Anthropic 側は `max_tokens` 既定 4,096 | `providers/openai.py` ・ `providers/anthropic.py` ・ README | 一次(実読) |
| **再試行の扱い(2 層)** | (a) **transient**: `typesafe_sdk.RetryPolicy`(408/429/5xx・指数バックオフ)。(b) **corrective**: `n_retry_malformed_structure` — スキーマ検証に落ちたとき、会話履歴+訂正メッセージを付けて再送。README「The transient retry count and time budget apply **separately to each provider request**. Corrective requests **share the evaluation's `n_retry_malformed_structure` allowance** and preserve the earlier responses and correction messages.」`response.usage` に `n_retries` / `n_retries_malformed_structure` / `latency`、`response.debug` に `llm_attempts` / `retry_reasons` / 確率正規化の診断 | README.md ・ `_client.py` | 一次(実読) |
| ライセンス | MIT(`LICENSE` 1,068 bytes) | リポジトリツリー | 一次(実読) |

---

## 6. 問い 5: 本シミュレーションに関わる技術点

### (a) 決定論性・再現性

| 項目 | 値(逐語) | 出典 | 確認の別 |
|---|---|---|---|
| 公式 FAQ の見出し | ホームページに「**Is Jev deterministic?**」というアコーディオン項目が**存在する**が、**回答本文は静的 HTML に含まれない**(JS 展開時に初めて DOM に載る)。curl・WebFetch・JS レンダリング型プロキシのいずれでも回答は取れなかった | https://typesafe.ai/ | **未読(理由: クリックしないと DOM に載らない)** |
| 温度の概念 | **API に温度・seed・top_p のパラメータは無い**(api.md のリクエスト本体は `state` / `model` / `questions` の 3 つのみ)。自社 cookbook も「reasoning models and **TypeSafe run without a temperature setting**」 | https://docs.typesafe.ai/api.md ・ https://docs.typesafe.ai/cookbooks/consistency_noul_cookbook.md | 一次(実読・不在を確認) |
| 反復のばらつき(ベンダー計測) | 自動車保険クレーム 1 件・**14 問の Noul を 15 回反復**(`jev-latest`・2026-09-11 サンプル)。「**TypeSafe's mean per-question probability standard deviation is `0.0102`, below all LLM probability conditions here.** Its `covered` answers span `0.43` to `0.53`, **crossing a `0.5` decision threshold.**」/「the LLM answers move from run to run, **at temperature `0` too**」 | https://docs.typesafe.ai/cookbooks/consistency_noul_cookbook.md | 一次(ベンダー主張・実読) |
| **その計測の決定的な限界(ベンダー自認)** | 「Every query also gets a **fresh `uid`**, a throwaway unique value that changes each run while leaving the claim and rubric unchanged. It appears in the LLM prompt and as an extra field in the TypeSafe state. **This setup cannot separate sensitivity to the irrelevant field from variation that would occur on identical requests.**」 | 同上 | 一次(実読) |
| 「自己一貫」の位置づけ | ホームページは「reliable, fast, **self-consistent**, and type-safe」と書き、**deterministic とは書かない**。jaggedness ページも「**extremely consistent** … you should expect **quantitatively similar** outputs for **semantically similar** inputs」 | https://typesafe.ai/ ・ https://docs.typesafe.ai/model-jaggedness/jev-1.13.md | 一次(実読) |
| 第三者の反復観察 | Every: 「Jev **missed it in all three runs**」(3 回反復で同じ見落とし=その入力では安定) | https://every.to/also-true-for-humans/... | 一次(実読) |

**結論(事実として言えること)**: 同一 state・同一 questions に対して同じ確率が返るという**保証は公開されていない**。ベンダー計測の std 0.0102 は**同一入力の反復ではない**(uid が毎回変わる)。温度に相当する調整つまみは API に無い。

### (b) 日本語

| 項目 | 逐語 | 出典 | 確認の別 |
|---|---|---|---|
| 言語対応 | 「Jev accepts natural-language text. **English is the primary training language and where accuracy is currently best. Other languages, including CJK scripts, are handled but not equally well; test on your own content before relying on Jev for a non-English workload, and pay close attention to Confidence when routing.**」 | https://docs.typesafe.ai/models.md | 一次(実読) |
| 同旨(State ページ) | 「Jev's primary training language is English; other languages, **including CJK scripts, are accepted but currently have lower accuracy**」 | https://docs.typesafe.ai/concepts/state.md | 一次(実読) |
| 日本語の定量評価 | **無い**(evals は英語のみ) | https://evals.typesafe.ai/ | 一次(不在を確認) |

### (c) state に JSON を渡せるか

**渡せる。** api.md: 「`state` … type `string | object | array` required」。concepts/state.md の表:

| Format | Useful for | Example |
|---|---|---|
| String | A message, article, or passage | `"My card was charged twice."` |
| Object | Named fields, related records, or **application state** | `{"message": "My card was charged twice.", "order_id": "A-104"}` |
| Array | A sequence of messages or records | `["Hi", "My customer number is TS1337.", ...]` |

「**Use an object for most requests** so each part of the state has a descriptive name and its relationships remain clear.」/ 質問側からの参照は「Reference nested state with backticked paths such as `` `ticket.messages[0].text` ``」(SKILL.md)。ただし「array **of text values**」であり、数値は semantic 表現に直せと jaggedness が勧めている(§4-2 の 2)。
出典: https://docs.typesafe.ai/api.md ・ https://docs.typesafe.ai/concepts/state.md ・ https://raw.githubusercontent.com/typesafe-ai/skills/main/skills/typesafe-ai/SKILL.md(いずれも一次実読)

### (d) 1 呼に「行動語 Choice(25)+行き先 Choice(4)+LLM を呼ぶかの Noul」を混ぜたときの費用・遅延

**仮定(全て明記・サブの算術。ベンダーの計測ではない)**
- A1: state = **500 入力トークン**(感度のため 200 / 1,000 も併記)。
- A2: 質問ブロック ≈ **450 トークン** = 行動語 Choice(25 選択肢 × 約 12 tok + 指示 25 ≒ 325)+ 行き先 Choice(4 × 20 + 25 ≒ 105)+ Noul(指示+criteria ≒ 40)。
- A3: 価格 \$0.042/MTok(入力のみ課金・出力無料)。
- A4: レート制限 1,200 req/min かつ 250,000 tok/s(models.md)。
- A5: **1 リクエスト = 1 state**(api.md)。体ごとに state が違うので**複数体を 1 リクエストに束ねられない**。
- A6: 遅延 70〜500 ms(ベンダーが西海岸の自社近傍から計測した値。**日本からの往復は未公開**)。

| 量 | 計算 | 結果 |
|---|---|---|
| 1 呼のトークン | 500 + 450 | **950 tok** |
| 1 呼の費用 | 950 / 1e6 × \$0.042 | **\$0.0000399**(≈ 0.004 円/呼 @150円/\$) |
| state 200 の場合 | 650 tok | \$0.0000273 |
| state 1,000 の場合 | 1,450 tok | \$0.0000609 |
| **腕 A: 現行 L4 の呼数(50,000 呼/シム日)** | 50,000 × 950 = 47.5 Mtok | **\$2.00 / シム日** |
| 腕 A'(実測 7.38 呼/体/日 = 36,900 呼) | 35.1 Mtok | \$1.47 / シム日 |
| **腕 C: 5,000 体 × 10 分ごと(720,000 呼/シム日)** | 684 Mtok | **\$28.7 / シム日** |
| **腕 B: 5,000 体 × 毎 tick(7.2M 呼/シム日)** | 6.84 Gtok | **\$287 / シム日** |

**律速はトークンではなくリクエスト数**:
- トークン制限 250,000 tok/s ÷ 950 tok = **263 req/s = 15,789 req/min** → 1,200 req/min の方が **13 分の 1** で先に当たる。つまり実効上限は **1,200 req/min = 20 req/s = 1.728M req/日(実時間)**。
- 現行の腕は **5,000 体 × 1 シム日を実時間 40〜120 分**で回している。
  - 腕 A(50,000 呼)を 40 分で → **1,250 req/min = 上限の 104%**(**わずかに超過**)。120 分なら 417 req/min で余裕。
  - 腕 C(720,000 呼)を 40 分で → 18,000 req/min = **上限の 15 倍**。
  - 腕 B(7.2M 呼)を 40 分で → 180,000 req/min = **上限の 150 倍**。
- 20 req/s を遅延 0.3 s で埋めるには**同時 6 本**、0.5 s なら**同時 10 本**の in-flight が要る(Little の法則)。SDK の既定タイムアウトは 10 s/HTTP 操作・再試行予算 30 s。
- 実時間 24 h をフルに使っても **1.728M 呼/日 = 5,000 体で 345 呼/体/日**が上限(現行 L4 の 10 呼/体/日 の 34 倍)。

**遅延**: 質問を足しても応答時間はほぼ変わらない(「Adding questions barely changes the response time and costs only the tokens for the extra questions」primitives.md)ので、上の 3 質問を 1 呼にまとめるのは**遅延ではなくトークンだけの追加**。逆に 3 呼に分けると state を 3 回送るので約 3 倍の費用(cookbook の 13 問で 12.2 倍安と同じ算術)。

### (e) Claude Code 用スキル(typesafe-ai/skills)

| 項目 | 内容 | 出典 | 確認の別 |
|---|---|---|---|
| リポジトリ構成 | `.claude-plugin/marketplace.json`(382 B)・`.claude-plugin/plugin.json`(320 B)・`LICENSE`(MIT)・`README.md`(1,336 B)・`skills/typesafe-ai/SKILL.md`(**10,040 B**)・`skills/typesafe-ai/LICENSE`。**docs が言う「its reference files」は実在しない**(SKILL.md 1 本のみ) | https://api.github.com/repos/typesafe-ai/skills/git/trees/main?recursive=1 | 一次(実読) |
| 導入 | `claude plugin marketplace add typesafe-ai/skills` → `claude plugin install typesafe@typesafe-ai`。他エージェントは `npx skills add typesafe-ai/skills --skill typesafe-ai` | https://docs.typesafe.ai/agent-skill.md | 一次(実読) |
| 中身の要点(逐語) | 「**The live TypeSafe docs are the source of truth. Read them as part of the task.**」/「Mintlify serves Markdown by **appending `.md`** to a page path」/「**Ask independent questions over the same state together**, including useful speculative questions. They run in parallel and **cannot see one another's answers**.」/「Question IDs are for code and **are not sent to the model**」/「**Typed output guarantees the interface, not truth.** System One models are trained for calibrated decisions; **validate their performance in the target domain.**」/「A Noul near 0.5 means **similar probability for yes and no, not medium intensity**.」/「Choice/Score confidence summarizes **distribution concentration, not overall workflow correctness or permission to act**.」 | https://raw.githubusercontent.com/typesafe-ai/skills/main/skills/typesafe-ai/SKILL.md | 一次(実読) |
| 運用上の助言 | 「Put the constants (questions and thresholds) in **a single place** so they're easy to review. **Agents aren't great at writing questions**, so expect to edit collaboratively with them.」/「If all you care about is choosing the best option, you just need to choose the option with the highest confidence (rather than setting a confidence threshold). **If you have a specific statistical algorithm in mind, you should probably be using probabilities instead of confidence.**」 | https://docs.typesafe.ai/agent-skill.md | 一次(実読) |
| 未読の参照 | SKILL.md が挙げる `https://docs.typesafe.ai/migrating-to-v1.md` は **llms.txt の索引に無い**(本答申では未読) | — | **未読** |

### (f) 入口(待機リスト以外)

| 経路 | 事実(逐語) | 出典 | 確認の別 |
|---|---|---|---|
| TypeSafe 直 | 早期アクセス・待機リスト。console.typesafe.ai/keys で API キー | https://typesafe.ai/ ・ https://docs.typesafe.ai/agent-skill.md | 一次(実読) |
| **Vercel AI Gateway** | 2026-09-16 公開。モデル id `typesafe-ai/jev`。**AI SDK 7 以降の `experimental_evaluate` 経由のみ**(「Evaluation is available through the AI SDK only. It is **not supported through the OpenAI-compatible, Anthropic-compatible, or Cohere-compatible endpoints.**」)。型名は `boolean`(=Noul)/`choice`/`score`。confidence は `result.providerMetadata.typesafe.confidence`。ZDR は `gateway: { zeroDataRetention: true }` | https://vercel.com/docs/ai-gateway/modalities/evaluation ・ https://vercel.com/changelog/typesafe-ai-jev-now-available-on-ai-gateway | 一次(実読) |
| **Cloudflare Workers AI** | モデル id `typesafe/jev`(応答の version は `jev-1.13.0`)。context length **32,000 tokens**。`env.AI.run` と `/ai/run` REST。「Third-party」タグ=TypeSafe 提供・TypeSafe の規約が適用。価格の数値はページに無し | https://developers.cloudflare.com/ai/models/typesafe/jev/ | 一次(実読) |
| OpenRouter | `openrouter.ai/typesafe` と `openrouter.ai/typesafe/jev-latest` は **HTTP 200 を返す**が、**公開モデル API(`/api/v1/models`・446 件)に typesafe/jev の項目は無い**(2026-09-18 読み) | https://openrouter.ai/api/v1/models | 一次(実読・不在を確認) |

---

## 7. 問い 6: 類似の「型付き判断モデル」

| 系統 | 代表 | Jev との違い(事実) | 出典 | 確認の別 |
|---|---|---|---|---|
| **構造化出力(constrained decoding)** | OpenAI Structured Outputs | **形は保証するが確率は返さない**。「ensures the model will always generate responses that adhere to your supplied JSON Schema」「you don't need to worry about the model … hallucinating an invalid enum value」。一方で「**In some cases, the model might not generate a valid response that matches the provided JSON schema.** This can happen in the case of a refusal …」と**例外**を明記し、`refusal` フィールドを返す。**選択肢上の確率分布・confidence の記述は無い**。生成は依然として自己回帰=出力トークン課金あり | https://developers.openai.com/api/docs/guides/structured-outputs | 一次(実読) |
| 同(ベンダーの反論) | — | CEO「constrained decoding (OpenAI-style structured outputs) **make models dumber** … simply masking logits is insufficient because if ever a model was assigning probability to an invalid token, the model is by definition confused」 | https://news.ycombinator.com/item?id=49718849 | 一次(CEO 主張・実読) |
| Anthropic 側 | Claude Messages API | 構造化出力は `output_config: {format: {...}}` と tool の `strict: true` がある(claude-api スキルの API 一覧で確認)。**同一覧に `logprobs` / `top_logprobs` パラメータは登場しない**=トークン確率を取り出す公開手段は確認できなかった。生成は自己回帰で出力トークン課金あり | claude-api スキル(バンドル版 2.1.273)の API 一覧 | 一次(スキル同梱資料を実読・不在を確認) |
| **logprobs 系の判定** | OpenAI Chat Completions | `logprobs`「Whether to return log probabilities of the output tokens or not.」/ `top_logprobs`「An integer **between 0 and 20** specifying the maximum number of most likely tokens to return at each token position」。→ **選択肢を 1 トークンに符号化すれば擬似的に分布が取れる**が、(i) 上位 20 件まで、(ii) トークン化に依存、(iii) 較正の保証は無い。`seed` は「**Determinism is not guaranteed**」 | https://developers.openai.com/api/docs/api-reference/chat/create | 一次(実読) |
| **自前 vLLM の logprobs** | 本プロジェクトの艦隊 | Jev と違い **本物のトークン分布**が取れる(アダプタが使っていないのは対象が外部 API だから)。費用は借用 GPU なので実質ゼロ。※本節は事実の対比であって設計案ではない | — | 既知(親ノート §4) |
| **アダプタ方式(LLM に確率を書かせる)** | typesafe-ai/system-one-adapter-python | **logprobs を使わず**、JSON Schema の確率フィールドに LLM が書いた数値を読み、必要なら合計 1 に再スケールするだけ(§5-3)。合計が 1 にならないことがある前提のコードになっている | https://github.com/typesafe-ai/system-one-adapter-python | 一次(実読) |
| **ゼロショット分類器** | — | CEO 自身が「basically a zero-shot classifier」という要約に「exactly right!」(§4-1)。**差分は「較正を目的関数にした学習(RLCD)」と「1 リクエストに多数の質問を並列で載せられる製品形」** | https://news.ycombinator.com/item?id=49718727 | 一次(実読) |
| Guardrails 系 | — | Jev のベンダーが想定用途として自ら挙げている(「Screen every message going into and out of an LLM app with one TypeSafe request」cookbook `llm_guardrails`)=競合というより適用領域 | https://docs.typesafe.ai/llms.txt | 一次(実読) |

> **未リサーチ(expedient の明示)**: Cohere Classify / HuggingFace の NLI ゼロショット分類(bart-large-mnli 等)/ GLiNER / DSPy の typed signatures / 適合予測(conformal prediction)は、二次記事(HN まとめ)で名前が挙がるのみで、**本答申では原典を読んでいない**。§8 に空欄として挙げる。

---

## 8. 本シミュレーションへの含意(事実の含意のみ・設計案は書かない)

1. **「体ごと 1 リクエスト」が構造的に決まっている**。質問の並列は 1 state 内でしか効かないため、5,000 体分を束ねる手段は無い。よって呼数 = リクエスト数となり、**1,200 req/min が実効の上限**。現行の 1 シム日 40 分・50,000 呼という腕は、**ちょうど上限の 104%** に当たる(§6-d)。
2. **費用の桁は、現行の呼数なら小さい**(\$2/シム日)。ただし「毎 tick 全体」に広げると \$287/シム日になり、**費用より先にレート制限が壁になる**。
3. **レート制限は「予告なく変わる」とベンダーが明記**しており、実験計画の再現性(同じ壁の下で 2 seed 回す)を外部要因に委ねることになる。
4. **決定論は保証されていない**。エンジン側の乱数で分布から抽選して seed 再現性を作る設計は、**返ってくる確率そのものの再現性には依存できない**(同一入力の反復は公開計測が無い)。ベンダーの std 0.0102 は uid を変えた反復であり、この用途の証拠にはならない。
5. **日本語は精度が落ちるとベンダーが明記**。渋谷の体の state・行動語・行き先ラベルは日本語が自然だが、**英語化するか、日本語のまま自前で精度を測るか**のどちらかが必要になる事実がある。
6. **数・時刻・日付は苦手**とベンダー自身が列挙(§4-2)。本シミュの state は時刻・所持金・距離・混雑度などの数値が主成分であり、**数値をそのまま渡す設計は jaggedness の 2・3 に正面から当たる**。「semantic 表現に直せ・算術はコードで」がベンダーの指示。
7. **大きな state は精度を下げる**(「Jev suffers from context rot」)。体の内面・記憶・周辺状況を全部載せる方向とは逆向きの制約。
8. **Noul と Choice の間に算術的な整合は無い**(refund 0.72 + not_refund 0.47 = 1.19)。「LLM を呼ぶかの Noul」と「行動語 Choice」の閾値を共有したり、片方で較正した閾値を他方へ持ち越すことはベンダーが明示的に禁じている。
9. **confidence の統計量は非公開**で、公開されているアダプタの式は docs の例と一致しない(§5-3)。confidence を門の閾値に使うなら、**自分のデータで較正し直す以外に根拠が無い**。
10. **説明(理由文)は出ない**。テープの「理由」列・会話・内省は Jev では埋まらない(「System One models **do not write replies, produce code, or generate explanations of their reasoning**」concepts/system-one.md)。
11. **state は米国のサーバーへ出る**。学習利用は契約で否定されているが、**Telemetry(ハッシュ・要約統計・分類・metrics・learnings)は無制限に処理される**と MCA 4.3 が定める。封印データ・holdout・現実データの値を state に含めない規律は、この条項の存在によりいっそう重い。
12. **ベンチマークの公表が契約で禁止**(§2.3(f))。本プロジェクトが Jev 腕の比較結果を devlog・答申・Discord に出すことは、**MCA の文言に抵触しうる**(公開の範囲・"performance information" の解釈は法務判断であり、サブの判断事項ではない)。
13. **版の固定は可能**(`jev-1.13.0` を直接指定)。エイリアスに閾値を結ぶなとベンダー自身が書いている。
14. **待機リストを通さない入口が 2 つ確認できた**(Vercel AI Gateway・Cloudflare Workers AI)。いずれも TypeSafe の規約が適用され、Vercel 経由は AI SDK 7 の `experimental_evaluate` に限定される。
15. **評価の件数・信頼区間が非公開**であるため、Jev の 67.8% と opus 5 の 73.1% の差が統計的に何を意味するかは、**現在の公開情報では判定できない**。

---

## 9. 未読・空欄の一覧

| # | 項目 | 理由 |
|---|---|---|
| 1 | ホームページ FAQ の回答 9 本(「Is Jev just a smaller LLM?」「How is this different from JSON mode or structured outputs?」「How can Jev be so fast and inexpensive?」「Can you make Jev even faster?」「Are these prices temporary or subsidized?」「What is Jev good at? Where does it struggle?」「Can Jev still get things wrong?」**「Is Jev deterministic?」**「How do I get started or ask a question?」) | Framer のアコーディオンが**閉じた状態では DOM に本文を載せない**。curl・WebFetch・JS レンダリング型プロキシのいずれでも見出しのみ。展開には実クリックが要る |
| 2 | ブログ FAQ の回答 5 本(「Why was a new training algorithm needed?」「What use cases is Jev good for?」「Is Jev just a smaller LLM?」「How does Jev perform against public benchmarks?」**「Where does our training data come from?」**「These are results are kinda crazy - how is it possible?」) | 同上 |
| 3 | evals の件数・信頼区間・生データ | サイトに記載が無い(不在を確認)。二次記事の「711 cases」は SVG 座標由来の可能性が高く**採用しない** |
| 4 | Almeida の講演(AI Engineer / Databricks Data+AI Summit)・podcast 文字起こし | 検索範囲では**存在を確認できなかった** |
| 5 | X スレッド本文の逐語 | X は認証なしで本文を取得できず。二次記事経由の引用のみ(本答申では数値に使っていない) |
| 6 | Empryo の検証記事(empryo.com/blog/jev-and-the-harness) | 時間内に原典を読めなかった |
| 7 | Forbes 記事 | 有料 |
| 8 | trust.typesafe.ai(副処理者一覧・セキュリティ方針・SOC2 等) | JS アプリ(6,914 B のシェルのみ)で静的取得不可 |
| 9 | `https://docs.typesafe.ai/migrating-to-v1.md` | SKILL.md から参照されるが llms.txt の索引に無い |
| 10 | Cohere Classify / HF ゼロショット NLI / GLiNER / DSPy / conformal prediction の原典 | §7 の比較を広げる余地。本答申では**未リサーチ(expedient と明示)** |
| 11 | 「a same-night Hugging Face reproduction」の実体 | 二次記事が言及するのみ。URL を特定できず |
| 12 | 日本からの実測遅延・p95/p99・実効同時接続数 | 公開なし(API 呼び出しは依頼どおり行っていない) |
| 13 | Jev の confidence の正確な定義式 | 非公開。アダプタの式は docs の例と一致しない(§5-3)ため代用不可 |
| 14 | 無料枠・最低課金額の数値 | MCA はクレジット制の枠組みのみを定め、金額は Order 依存 |

---

## 10. 本答申と親ノート(v2-jev-system-one-note.md)の差分(訂正候補)

| 親ノートの記述 | 本答申での確認 |
|---|---|
| 「文脈長・1 呼あたりの質問数上限・レート制限・モデル規模は**未公開**」 | **文脈長(64k/32k)とレート制限(250,000 tok/s・1,200 req/min)は公開されている**(models.md)。質問数上限はトークン予算のみ。モデル規模は依然として未公開 |
| 「Score(2〜10 段)」 | 正しい。出典は primitives/score.md の「Needs at least two levels and takes up to 10」(api.md 側は下限のみ記載) |
| 「confidence は分布の形から計算・統計量は未公開」 | 正しい。加えて**アダプタの公開式は docs の例と一致しない**ことを確認 |
| 「エンコーダ型分類器かどうかは推測の域」 | アーキテクチャは依然非公開だが、**CEO が「basically a zero-shot classifier」に "exactly right!" と同意**した一次発言がある |
| 「(Doom デモ)10 判断/秒・約 \$7/h」 | ブログ原文で確認(「making 10 queries a second (which ends up costing ~\$7/hour)」) |
| 評価の「件数・信頼区間は未記載」 | 正しい(4 ページ全文抽出で確認)。二次記事の「711 件」は採用しない |

---

## lit README 追記行

| 分野 | 発行者 年 | タイトル | URL | 何が取れたか |
|---|---|---|---|---|
| LLM/型付き判断API | TypeSafe AI 2026 | Models(Jev のモデルカード) | https://docs.typesafe.ai/models.md | 文脈長 64k/32k・レート 250,000 tok/s と 1,200 req/min・\$42/Btok・言語対応(CJK は精度低)・版固定の方法・顧客微調整なし |
| LLM/型付き判断API | TypeSafe AI 2026 | API reference(System One 評価エンドポイント) | https://docs.typesafe.ai/api.md | リクエスト/レスポンス全スキーマ・Noul/Choice/Score の型・エラー 401/422/429/529・温度や seed が無いこと |
| LLM/型付き判断API | TypeSafe AI 2026 | Primitives (Questions) | https://docs.typesafe.ai/primitives.md | 質問は 1 リクエスト内で独立・依存なら 2 回目のリクエスト・トークン予算 ≈32,000(約 15 万字) |
| LLM/型付き判断API | TypeSafe AI 2026 | Choice / Score / State | https://docs.typesafe.ai/primitives/choice.md ・ /primitives/score.md ・ /concepts/state.md | Choice 255 上限・Score 2〜10 段・state は string/object/array |
| LLM/信頼性 | TypeSafe AI 2026 | Jev 1.13 jaggedness(既知の弱点) | https://docs.typesafe.ai/model-jaggedness/jev-1.13.md | 数・日付・計数・大 state・敵対入力・構造的不変量の不成立(Noul と Choice の不整合の実数値) |
| LLM/学習法 | TypeSafe AI 2026 | AI primer(RLCD) | https://docs.typesafe.ai/introduction/machine-learning-primer.md | RLCD の説明全文・較正の定義・事前学習済み LM からの派生という位置づけ |
| LLM/再現性 | TypeSafe AI 2026 | Self-consistency: nouls(cookbook) | https://docs.typesafe.ai/cookbooks/consistency_noul_cookbook.md | 14 問 ×15 反復で平均 std 0.0102・**uid を毎回変えるので同一入力の再現性は測れない**とベンダーが自認 |
| LLM/バッチ | TypeSafe AI 2026 | Parallel questions(cookbook) | https://docs.typesafe.ai/cookbooks/parallel_questions.md | 13 問の一括で 12.2 倍安・10.0 倍速(jev-1.12)。primitives.md の 11.5/9.6 と食い違う |
| LLM/評価 | TypeSafe AI 2026 | Workflow evals | https://evals.typesafe.ai/ | 4 課題 ×9 モデル ×(workflow/prompt)の精度・費用・秒。**件数と信頼区間の記載が無いこと** |
| LLM/製品 | TypeSafe AI 2026 | Introducing System One Models & Jev | https://typesafe.ai/blog/introducing-system-one-models-and-jev | 並列サンプラーの説明全文・255 超のときの 2 段処理・評価バイアスの自認・幻覚 0% が非経験的であること |
| LLM/契約 | TypeSafe AI 2026 | Master Customer Agreement / Privacy Policy / DPA / Legal | https://typesafe.ai/legal/mca ・ /legal/privacy-policy ・ /legal/data-processing ・ https://docs.typesafe.ai/legal.md | **ベンチマーク公表禁止(2.3(f))**・Telemetry 無制限利用(4.3)・学習利用の否定・SLA なし・オンプレ条項なし・US ホスト・ZDR は企業向け |
| LLM/一次発言 | Hacker News 2026 | Introducing System One Models and Jev(491 コメント・CEO 参加) | https://news.ycombinator.com/item?id=49717558 | 「zero-shot classifier」への "exactly right!"・architecture is close to the chest・constrained decoding 批判・一般モデルで顧客学習なし |
| LLM/第三者検証 | Every 2026 | Mini-Vibe Check: TypeSafe's Jev Judged Everything I've Written in 0.7 Seconds | https://every.to/also-true-for-humans/mini-vibe-check-typesafe-s-jev-judged-everything-i-ve-written-in-0-7-seconds | 独立小規模試験: 12 文・7 欠陥中 6 検出・中央値 0.35 s vs 8.83 s・約 580 倍安・3 回とも同じ見落とし |
| LLM/アダプタ実装 | TypeSafe AI 2026 | system-one-adapter-python(MIT) | https://github.com/typesafe-ai/system-one-adapter-python | 確率は LLM に書かせて正規化(logprobs 不使用)・confidence の式・2 層の再試行 |
| LLM/エージェント技能 | TypeSafe AI 2026 | TypeSafe agent skill(SKILL.md) | https://raw.githubusercontent.com/typesafe-ai/skills/main/skills/typesafe-ai/SKILL.md | 質問設計の指針・「Typed output guarantees the interface, not truth」・Noul 0.5 の意味 |
| LLM/提供経路 | Vercel 2026 | AI Gateway: Evaluation modality / Jev changelog | https://vercel.com/docs/ai-gateway/modalities/evaluation ・ https://vercel.com/changelog/typesafe-ai-jev-now-available-on-ai-gateway | `typesafe-ai/jev` を AI SDK 7 の `experimental_evaluate` 経由で利用可・ZDR/No Training をリクエスト単位で指定 |
| LLM/提供経路 | Cloudflare 2026 | Workers AI model: Jev (typesafe) | https://developers.cloudflare.com/ai/models/typesafe/jev/ | `typesafe/jev`・context 32,000 tokens・third-party 扱い |
| LLM/比較対象 | OpenAI 2026 | Structured Outputs guide / Chat Completions API reference | https://developers.openai.com/api/docs/guides/structured-outputs ・ https://developers.openai.com/api/docs/api-reference/chat/create | 構造化出力はスキーマ遵守のみで確率を返さない・refusal 例外・logprobs/top_logprobs(0〜20)・seed は決定論を保証しない |
