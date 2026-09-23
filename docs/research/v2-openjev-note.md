# Open-Jev と DiffusionGemma — 親の一次読み(2026-09-23・第253)

<!-- hdr:v1 -->
- **分野**: 自然言語処理・機械学習 #27 / ソフトウェア工学 #29 | **重要度**: P1(親判断・2026-09-15 第191)
- **一次確認**: **A** = 親検収済(逐語引用または再計算つき) — 親の一次読み(2026-09-23・第253): GitHub リポ README・TypeSafe 公式ブログ・Google の HF モデルカードを親が実読。二次情報は不使用
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **分野地図**: [v2-discipline-map.md](v2-discipline-map.md)

> ユーザー依頼(2026-09-23)「BERT 系 / Open-Jev の調査」のうち **Open-Jev の部分**。BERT 系の系譜は答申 R-38([v2-r38-closed-output-judges-research.md](v2-r38-closed-output-judges-research.md))。
> **一次確認: 親が実読**(GitHub リポ本文・TypeSafe 公式ブログ・Google の HF モデルカード)。サブは使っていない(存在しないものを探させると捏造の危険があるため)。
> 既存の Jev ノート: [v2-jev-system-one-note.md](v2-jev-system-one-note.md)(第238・第242 訂正)/ 答申 [v2-r40-jev-details-research.md](v2-r40-jev-details-research.md)(第242)。

## 1. 結論(先に)

**Open-Jev は実在する。しかし第一候補にはしない。** 理由は 2 と 3(どちらも単独で落ちる)。理由 1 は**第254 で撤回**(ユーザー指示 09-23「計算資源は設計判断の軸にしない」)=導入要件として残すだけ。

| # | 理由 | 根拠 |
|---|---|---|
| 1 | ~~**手元のハードに載らない**~~ → **第254 撤回**。vLLM 経路の要件「24 GB 以上の NVIDIA GPU」・重み約 18 GB は**調達の事実**として記録する(順位の理由にしない) | リポ README |
| 2 | **精度の数値が無い**。README 自身が「答えの質は DiffusionGemma 26B-A4B の質そのもの。**自分のタスクで評価してから頼れ**」と書く。土台の DiffusionGemma は自己回帰版 Gemma 4 26B A4B より**軒並みスコアが低い**(MMLU Pro 77.6 vs 82.6・GPQA Diamond 73.2 vs 82.3) | リポ README・Google モデルカード |
| 3 | **決定論の保証が無い**。ノイズから読み、エントロピーが 0.1 を超えると**最大 4 回読み直して平均する**実装。chat 側は `seed` を無視 | リポ README |

v2 は「同 seed で bit 一致」を受入に置いている(第247 で 5,000 体の艦隊ランが別コード版と final_hash まで一致することを確かめたばかり)。3 はその線と正面から衝突する。

## 2. Open-Jev とは何か(実読)

- リポ: `razorback16/openjev`(GitHub)。説明文「Open, Jev-compatible System One decision server on DiffusionGemma」。README の見出し「Fast, calibrated, typed decisions from an open model.」
- **TypeSafe とは無関係**。README に明記: 「OpenJev is an independent project. It is not affiliated with or endorsed by TypeSafe AI.」
- **ライセンス Apache-2.0**(サーバーも、DiffusionGemma の重みも)。
- 規模の目安: star 305・fork 24・commit 23(2026-09-23 時点)。
- API は Jev と同じ形: `POST /v1/systemone` に `{state, model, questions}`。
  - `noul`(yes/no)→ `{noul: P(yes)}`
  - `choice` → `{choice, probabilities, confidence}`(**上限 128 択**。Jev は 255)
  - `score`(2〜10 段)→ `{score: Σ i·pᵢ, legend, probabilities, confidence}`
  - `confidence` = **1 − H(p)/ln K**(確率分布のエントロピーから作る計算式)
- モデル名は `openjev-0.1` / `openjev-latest` だが **`jev-latest` と `jev-preview` も受ける**=TypeSafe の SDK の既定値でそのまま刺さる。
- 速度(README の実測・RTX PRO 6000・3 問/リクエスト): 同時 1 で 10.7 req/s(p50 94 ms)・16 で 43.3 req/s・64 で 57.4 req/s。

### confidence の意味が Jev と違う
TypeSafe は「**RLCD** という訓練法で較正された確率」を売りにしている(公式ブログ「calibrated decisions: answers with epistemically honest probabilities」)。Open-Jev の `confidence` は**訓練で較正した値ではなく、出てきた確率分布のエントロピーを 1 − H/ln K に入れただけ**。名前と欄の形は同じでも中身は別物で、**Jev の較正の主張は Open-Jev には引き継がれない**。

## 3. 土台の DiffusionGemma(Google の公式モデルカードを実読)

| 項目 | 値 |
|---|---|
| 提供元・ライセンス | Google DeepMind・**Apache-2.0**(商用可・ローカル実行可) |
| 規模 | 総 **25.2B** / 活性 **3.8B**(MoE) |
| 生成方式 | **離散拡散**。「token-by-token autoregression から block-autoregressive multi-canvas sampling へ移す」・canvas 256 トークンを並列に denoise・**最大 48 denoising steps**・1 forward pass で 15〜20 トークン |
| 文脈長 | 最大 256K |
| 言語 | 「35+ 言語をすぐに使える・140+ 言語で事前学習」。**日本語の明示は無い**(個別言語名を挙げていない) |
| 速度 | H100・FP8・低バッチで 1,100 tok/s 超 |
| 自己回帰版との比較 | **軒並み低い**: MMLU Pro 77.6 vs 82.6・AIME 2026 69.1 vs 88.3・LiveCodeBench v6 69.1 vs 77.1・GPQA Diamond 73.2 vs 82.3・MMMU Pro 54.3 vs 73.8(例外: HLE 11.0 vs 8.7) |
| VRAM | モデルカードには**記載なし**。Open-Jev 側が「NVFP4 で 24 GB 以上」「ダウンロード約 18 GB」と書く |
| 決定論 | **記載なし** |

## 4. Jev 本体について、これで分かったこと(既存ノートの補強)

- TypeSafe の公式ブログは「**parallel sampler**」「単一クエリで全出力を生成」「**文字列生成をやめた**(gives up string generation)」とだけ書き、**"non-autoregressive" や "diffusion" という語は使っていない**。第242 で確認した「アーキテクチャは当面非公開」と整合する。
  → **Open-Jev が拡散モデルで実装したことは、Jev が拡散モデルである証拠ではない**。第三者が「型付き出力を並列に返す API」を再現しただけ。二次情報の中には Jev を「非自己回帰」と断定するものがあるが、**一次には無い**。
- 「幻覚しない」の根拠は**出力の構造を事前に定義しているから**であって、答えが正しいという意味ではない。ブログ自身が「**我々の数値は経験的なものではない**。スキーマ一致は保証されるので 0% を自信を持ってプロットに入れた」と書いている。第242 の「新規性はインターフェース」という読みを裏づける。
- 速度・費用の比較基準: 「40x-200x faster」「193.6x faster, 444.6x cheaper」の参照は **GPT-6 Astra と Fable 5.1 の平均**で、著者自身が「実世界の利得の**高い側**の見込み」と書き、計測は「著者のノートパソコンから西海岸で」行ったと明記している。

## 5. v2 にとっての意味

1. **Open-Jev は採らない**(§1 の 3 理由)。ただし**インターフェースの形(noul / choice / score)は参考にする価値がある**。v2 の判断器インターフェース(D-101・[詳説 §2-j](../design/v2-decision-brief-2026-09-19.md))で扱いたい質問の型と一致しており、Jev と Open-Jev が独立に同じ 3 つに落ち着いたのは、**型の選び方としては妥当**という弱い証拠になる。
2. **拡散型言語モデルという選択肢の存在は記録しておく**。Apache-2.0 で重みが公開され、ローカルで動き、並列に出力を返す器が現実に存在する。ただし (a) ~~24 GB 以上の GPU が無い~~(第254 撤回: 要件は調達の事実) (b) 日本語の裏づけが無い (c) 自己回帰版より精度が低い ので、**第一候補にはしない・測るなら腕として**。
3. **logprob を読むのが最も安い — 第253 で却下したが第254 で復活(親の訂正)**。第253 で「vLLM 公式 FAQ が logprob の安定性を非保証」を理由に却下したが、FAQ の非保証は**既定モード**の話で、v2 の艦隊は `VLLM_BATCH_INVARIANT=1` で起動し(検証ランは manifest 規則 (c) で必須)、[B14](../bench/b14_batch_invariance/README.md) で **logprobs 32/32 一致(OFF では 0/32)**を実測済み。**衝突しない**。第254 の親推奨は 第一候補=自前艦隊の logprob 判断 (G)・第二=そこから蒸留した学生・lookup 表は最低容量の基線(詳細は [R-38 答申](v2-r38-closed-output-judges-research.md) と PENDING D-101)。
4. **MCA の縛りは Open-Jev には掛からない**。Jev 本体は契約で「ベンチマーク・性能情報の公表を禁止」しているが(第242)、Open-Jev は Apache-2.0 の独立実装なので、測って公表してよい。**Jev を使わずに「System One 型の器」を論文・未踏で語れる道**がここにある。

## 6. 未確認・やっていないこと

- **重みをダウンロードしていない**(§7 の規律=読むだけ)。動作確認はしていない。
- Open-Jev の**コード本体は読んでいない**(README のみ)。`confidence` の式と API の形は README の記述による。
- DiffusionGemma の**日本語性能**の数値は見つからなかった(モデルカードは個別言語名を挙げない)。
- 12 GB に収まる量子化(3bit 等)が在るかは**未確認**。モデルカードは「Quantizations 34 models」と数だけ示し、個別の名前と VRAM を挙げていない。
- `typesafe-ai/system-one-adapter-python`(TypeSafe がベンチで LLM に構造化出力を強制するために使ったアダプタ)は**未読**。ライセンス不明。

## 7. 出典(すべて親が実読・2026-09-23)

| # | 出典 | 使った箇所 |
|---|---|---|
| 1 | `https://github.com/razorback16/openjev` | §2 全部・§1 の理由 1〜3 |
| 2 | `https://typesafe.ai/blog/introducing-system-one-models-and-jev` | §4 |
| 3 | `https://huggingface.co/google/diffusiongemma-26B-A4B-it` | §3 |

二次情報(DataCamp・MindStudio・LangChain・DEV・flaviocopes 等)は検索結果に出たが、**本ノートの記述には使っていない**。
