# R-83 答申: Jev 型の決定モデル(本家の規約の現状・オープンなモデルの一覧・評価と汚染・確率の意味の違い・見張りの小さなモデル・v2 への当てはめ)

<!-- hdr:v1 -->
- **分野**: 自然言語処理・機械学習 #27 / ソフトウェア工学 #29 / 研究倫理・情報法 #31 / 交通工学(離散選択) #2 / 認知科学 #12 | **重要度**: P1(指示書 [v2-wallbounce-decisions-2026-10-03](../design/v2-wallbounce-decisions-2026-10-03.md) §7-4・§11 第 3 群「R-a Jev 型の決定モデル」・PENDING H8)
- **一次確認**: **B**(サブ実読。出典 36 本=◎21・○3・△8・×4・空欄 19 件は §8)・親検収 済(第319・2026-10-03: TypeSafe models.md の「100K tokens per second / 80 requests per second」「adjusting dynamically」「Jev is not trained on customer requests or responses」と、MCA(Last updated Sep 23, 2026)§2.3 に benchmark の条項が無く (b) に distillation と imitate が残ることを原典で確認。Decision Index の ECE 0.074・JEV-27B の学習データの自己申告は親未読。等級 A−)
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 作成 2026-10-03・リサーチ役サブ(Opus 5.5)。子サブ未起動・Web は読むだけ(JSON は curl の標準出力を python で読んだだけで保存していない。重みは取得していない)・API 登録や呼び出しなし・コミットなし・台帳/設計書/src 未編集。
> 既存答申との関係: 本家 Jev の仕様・規約・弱点の一覧は [R-40](v2-r40-jev-details-research.md)(第242)、閉じた出力の判断器の系譜と cascade/router は [R-38](v2-r38-closed-output-judges-research.md)、判断が思考に占める割合と呼び出し判断は [R-39](v2-r39-judgment-share-research.md)、razorback16 版 Open-Jev は [v2-openjev-note.md](v2-openjev-note.md)(第253)、Clef の遅延は [R-73](v2-r73-time-model-des.md) #38。本書はそれらを**繰り返さず**、10-03 時点の変化と、それ以後に出たオープンなモデルと評価だけを足す。R-40 の記述と食い違う点は §1 に「R-40 からの変化」として明記する。

## 結論(5 行)

1. **本家 Jev の規約は 2 点変わった**。今の基本契約(MCA。2026-09-23 改訂)の §2.3 には、R-40 時点(09-18)にあった「ベンチマークや性能情報を公表しない」の条項がありません。「出力で蒸留する、出力を真似るモデルを学習させる、競合品を作る」の禁止は残っています。レート上限は「1 分 1,200 回」から「**毎秒 80 回(1 分 4,800 回)・毎秒 10 万トークン**」に変わりました。今も「予告なく変わる」と書かれています。決定論の公式回答は今回も読めませんでした(空欄)。第三者の評価表には「API の出力が前回の計測から 20 問で変わった」という記録があります。
2. **オープンなモデルは 10 系統を詳しく読んだ**。うち Clef(27B)と Clef-flash(9B)は Apache-2.0 で、学習データは Cloudflare 社内の合成データと書かれ、Jev の出力を使ったという記述はありません。JEV-27B(と画像版)は「Jev 1.13 の出力分布 498,010 行」で学習したと自分で明記しています。Kev と decider は「Jev の出力は使っていない」と明記しています。OpenJev(openjev/openjev)は重みが**非商用**(CC BY-NC 4.0)です。日本語を含む評価を出しているのは OpenJev だけで、それも 4 言語をまとめた値です。
3. **評価は 2 本の第三者の表がある**(Decision Index 0.2.1 と JevBench v1.5)。Jev の較正誤差(ECE)は Decision Index で **0.074** で、確信の平均 0.81 に対して正答率 0.74(自信過剰の側)です。公開の問題と封印した問題のずれの実例として、decider-4b v2 の yes/no 問題が「公開 43 対 封印 19」(偶然補正後)と報告されています。封印した問題の結果にも「見られていないことの証明ではない」と評価者自身が書いています。
4. **確率の意味の違いを埋める先行例はある**。どれも「人の選択データで分布を合わせて学習する」形です。調査の回答分布に最初のトークンの確率を合わせる微調整(Cao ほか 2025)、手段選択で JSD 0.000245 を出した微調整(Alsaleh & Farooq 2025)、行動実験 1,000 万選択での微調整(Centaur)があります。**Jev 型のモデルを人の行動データで較正した例と、社会シミュレーションで使った例は見つからなかった**(空欄)。
5. **v2 への当てはめは親の案です(§7)**。最初に置き換える対象は「購入」(39%)です。古典モデル(D-119)と自前の logprob の腕 (G) は物差しとして並べて残します。評価は個体・小集団・群衆の 3 段で行い、厳密モードは「重みを手元に置く・バッチの形を固定する・不変性を実測する」の 3 条件にします。費用の見積り(推測)では、移動と購入の約 248 万回/日を本家 API に送ると、上限だけで実時間 **約 8.6 時間/シム日**かかります。

## §0 出典の表

等級: **◎** 原典本文で数値まで逐語確認 / **○** 一部推測を含む・本文の一部だけ / **△** 抄録のみ / **×** 未読(空欄)

| # | 出典 | URL | 等級 | 読んだ範囲 |
|---|---|---|---|---|
| 1 | TypeSafe docs「Models」 | https://docs.typesafe.ai/models.md | ◎ | 全文(料金・レート・言語・版の固定) |
| 2 | TypeSafe「Master customer agreement」(Last updated Sep 23, 2026) | https://typesafe.ai/legal/mca | ◎ | §2.3・§4.1〜4.3・§6(HTML を文字列化して全文検索) |
| 3 | TypeSafe「Acceptable Use Policy」(Last updated Sep 23, 2026) | https://typesafe.ai/legal/acceptable-use-policy | ◎ | 全文検索(benchmark・distill・imitate の語の有無) |
| 4 | Cloudflare blog 2026-10-01「Introducing Clef」 | https://blog.cloudflare.com/clef-decision-models/ | ◎ | 本文(基盤・学習・遅延の表・評価の表) |
| 5 | Hugging Face `Cloudflare/clef` モデルカード | https://huggingface.co/Cloudflare/clef | ◎ | カード全文 |
| 6 | Hugging Face `Cloudflare/clef-flash` モデルカード | https://huggingface.co/Cloudflare/clef-flash | ◎ | カード全文 |
| 7 | Cloudflare Workers AI「clef」 | https://developers.cloudflare.com/workers-ai/models/clef/ | ◎ | 文脈長・価格・画像の上限・問いの数 |
| 8 | Jev Decision Index 0.2.1 `data/index.json`(生成 2026-09-28) | https://huggingface.co/spaces/multimodalart/jev-decision-index | ◎ | JSON 全体(全 70 件の点数・ECE・遅延・Jev の欄) |
| 9 | 同 `data/methodology.json` | 同上 | ◎ | 全文検索(除外の理由・汚染・ハードウェア) |
| 10 | 同 README | 同上 | ◎ | 全文 |
| 11 | Hugging Face `autotrust/JEV-27B` | https://huggingface.co/autotrust/JEV-27B | ◎ | カード全文 |
| 12 | Hugging Face `autotrust/JEV-27B-VL` | https://huggingface.co/autotrust/JEV-27B-VL | ◎ | カード全文 |
| 13 | Hugging Face `openjev/openjev` | https://huggingface.co/openjev/openjev | ◎ | カード全文 |
| 14 | Hugging Face `convaiinnovations/laya` | https://huggingface.co/convaiinnovations/laya | ◎ | カード全文 |
| 15 | Hugging Face `perplexity-ai/pplx-decider-v1-27b` | https://huggingface.co/perplexity-ai/pplx-decider-v1-27b | ◎ | カード全文 |
| 16 | GitHub `jaredpalmer/kev` README | https://github.com/jaredpalmer/kev | ◎ | README 全文 |
| 17 | GitHub `Mapika/decider` README | https://github.com/Mapika/decider | ◎ | README 全文(Limits・Runs on・Train your own・Standing) |
| 18 | 同 `docs/SERVING.md` | https://github.com/Mapika/decider/blob/main/docs/SERVING.md | ○ | §5 の表と決定論の節。GPU の種類は読めず |
| 19 | GitHub `fstandhartinger/jevbench` README | https://github.com/fstandhartinger/jevbench | ◎ | README 全文 |
| 20 | 同 `docs/METHOD-v1.5.md`(2026-09-25 凍結) | https://github.com/fstandhartinger/jevbench/blob/main/docs/METHOD-v1.5.md | ◎ | §0・§1・§4・§5 |
| 21 | Benchmark Heaven「JevBench」掲示板(v1.5.6) | https://benchmarkheaven.com/jev-models | ○ | 上位の行と集計の注記のみ(途中で切れた) |
| 22 | GitHub `allebee/jevk5` README | https://github.com/allebee/jevk5 | ◎ | 独立評価の段落 |
| 23 | Hugging Face `Qwen/Qwen3.8-27B` | https://huggingface.co/Qwen/Qwen3.8-27B | ◎ | ライセンス・言語・画像・文脈長 |
| 24 | Binz ほか「Centaur: a foundation model of human cognition」arXiv:2410.20268 | https://arxiv.org/abs/2410.20268 | △ | 抄録 |
| 25 | Cao ほか 2025「Specializing Large Language Models to Simulate Survey Response Distributions for Global Populations」NAACL 2025・arXiv:2502.07068 | https://arxiv.org/abs/2502.07068 | △ | 抄録 |
| 26 | Meister, Guestrin & Hashimoto 2024「Benchmarking Distributional Alignment of Large Language Models」arXiv:2411.05403 | https://arxiv.org/abs/2411.05403 | △ | 抄録 |
| 27 | Mo ほか「Large Language Models for Travel Behavior Prediction」arXiv:2312.00819 | https://arxiv.org/abs/2312.00819 | △ | 抄録 |
| 28 | Alsaleh & Farooq 2025「Towards Locally Deployable Fine-Tuned Causal Large Language Models for Mode Choice Behaviour」arXiv:2507.21432 | https://arxiv.org/abs/2507.21432 | △ | 抄録 |
| 29 | GitHub `Ytlse/llm-urban-mode-choice`(トゥールーズの手段選択シミュ) | https://github.com/Ytlse/llm-urban-mode-choice | ○ | README のみ(結果の数値なし) |
| 30 | Santurkar ほか 2023「Whose Opinions Do Language Models Reflect?」arXiv:2303.17548 | https://arxiv.org/abs/2303.17548 | △ | 抄録 |
| 31 | Guo ほか 2017「On Calibration of Modern Neural Networks」arXiv:1706.04599 | https://arxiv.org/abs/1706.04599 | △ | 抄録(R-38 と同じ出典) |
| 32 | Schuster ほか 2022「Confident Adaptive Language Modeling」(CALM)NeurIPS 2022・arXiv:2207.07061 | https://arxiv.org/abs/2207.07061 | △ | 抄録 |
| 33 | Liu ほか「Toward LLM-Agent-Based Modeling of Transportation Systems」arXiv:2412.06681 | https://arxiv.org/abs/2412.06681 | × | 検索要約のみ(本文未読) |
| 34 | Centaur の Nature 版(s41586-025-09215-4) | https://www.nature.com/articles/s41586-025-09215-4 | × | 認証へ転送されて読めず |
| 35 | 検索要約の「Decider 2B は Amazon の投稿」 | (検索要約のみ) | × | 原典に当たれず。#17 の README は個人(Mapika)名義で、Amazon の記述は無い |
| 36 | TypeSafe ホームページの FAQ「Is Jev deterministic?」 | https://typesafe.ai/ | × | R-40 と同じく回答本文は読めず |

## §1 本家 Jev の規約と仕様の現状(R-40 からの変化)

| 項目 | R-40 時点(2026-09-18・第242 親確認) | 今回(2026-10-03) | 出典 |
|---|---|---|---|
| ベンチマーク・性能情報の公表 | §2.3(f)「publish benchmarks or performance information about the Services」を禁止 | **§2.3 にこの条項は無い**。今の (f) は「interfere with the operation of the Services」。AUP にも benchmark の語は無い。MCA の改訂日は「Last updated Sep 23, 2026」 | #2・#3 |
| 蒸留・出力を真似る学習 | §2.3 で禁止 | **残っている**。§2.3(b)「use the Services or any Output (defined below) to perform model distillation, train a model to imitate the output of the Services, or develop (or to facilitate the development of) a similar or competing product or service」 | #2 |
| 違反時 | (R-40 に記載なし) | §6「TypeSafe may immediately suspend Customer's access … if: (a) Customer breaches or otherwise violates Section 2.3 (License Restrictions)」 | #2 |
| テレメトリ | §4.3 で無制限に処理 | **変わらず**。§4.3「TypeSafe may Process Telemetry without restriction」。§4.1 は「in perpetuity, any Customer Data (i) to derive and generate Telemetry」 | #2 |
| 学習への利用 | 同意なしに顧客データで学習しない | **変わらず**(§4.1・models.md「Jev is not trained on customer requests or responses.」) | #1・#2 |
| **レート上限** | 「250,000 tokens per second / 1,200 requests per minute」 | **「100K tokens per second / 80 requests per second」**(1 分 4,800 回)。「Measured in tokens per second and requests per second」。「Rate limits are adjusting dynamically … can change without notice」の注記は残る | #1 |
| 料金 | \$0.042/Mtok(入力のみ) | 変わらず | #1 |
| 文脈長 | 64k/32k | 変わらず | #1 |
| 入力 | テキストのみ | 変わらず(「No image, audio, or video input.」) | #1 |
| 日本語 | 「CJK … lower accuracy」 | 変わらず | #1 |
| 版 | `jev-latest` → `jev-1.13.0` | 変わらず。`jev-preview` も同じ版を指す | #1 |
| 決定論 | 公式回答は読めず | **今回も読めず**(空欄)。第三者の記録 2 件: Decision Index の Jev 欄「Its answers on this sample differ from the Sep-19 board rows in 20 choices: API output drifted since the board run; scores are unchanged.」(分母の件数は空欄)。JEV-27B のカードは教師(Jev)について「non-deterministic (4.3 % answer changes)」と記す(測り方の詳細は空欄) | #8・#11 |

**含意(事実の含意のみ)**
- 公表禁止が消えたので、R-40 §8-12 の「腕の結果を出すと MCA に抵触しうる」は**今の文言では当たらない**。ただし MCA は予告の仕組みが「Last updated」の日付だけであり、契約時点の版が効く。採用の時点で読み直す必要がある。
- 蒸留禁止は残る。v2 が本家 Jev の出力で小さな見張りのモデルを学習させる案(指示書 §7-4 の 2 段)は、**本家の出力を教師にした時点で §2.3(b) に当たる**。教師はオープンなモデル(Clef など)にする必要がある。
- レート上限は R-40 の 4 倍になった。それでも §7-4 の呼び出し量には足りない(§7-4 の試算)。

## §2 オープンなモデルの一覧(詳しく読んだ 10 系統)

### 2-1 一覧の表

空欄は「カードや README に記載が無い」の意味。処理量は公表値をそのまま写し、条件(GPU・同時数・問いの数)を併記する。

| モデル | 公開者・ライセンス | 元のモデル(基盤) | 出力の形・上限 | 日本語の評価 | 決定論・バッチ不変 | 処理量の公表値 | 画像 | 追加学習 | Jev の出力で学習したか |
|---|---|---|---|---|---|---|---|---|---|
| **Clef** | Cloudflare・Apache-2.0(「following the base model Qwen/Qwen3.8-27B」) | Qwen3.8-27B。ブログ「By freezing Qwen3.8-27B for Clef … we jointly optimized the routing head alongside rank-256 low-rank adapters」。カードは「post-trained from Qwen/Qwen3.8-27B」 | noul・choice・score。選択肢の上限は記載なし。Workers AI は 1 回に「1 to 64 questions」。出力は「one logit per allowed option」 | 空欄(ブログ・カードとも言語の記載なし) | 空欄(記載なし) | 空欄。遅延のみ: 中央値 209.3 ms・p95 238.6 ms(43 本の評価) | あり(「vision encoder」・Workers AI は画像 4 枚まで) | 重みは Apache-2.0。カードに手順なし。Cloudflare の微調整基盤を予告 | 記述なし。学習データは「our own internal synthetic datasets permutating field orders, prompts, and schema structures」 |
| **Clef-flash** | Cloudflare・Apache-2.0 | Qwen3.5-9B | Clef と同じ | 空欄 | 空欄 | 空欄。遅延のみ: 中央値 38.8 ms・p95 122.4 ms | あり | Clef と同じ | Clef と同じ |
| **JEV-27B** | AutoTrust AI・Apache-2.0 | Qwen3.8-27B の文字の部分(凍結)+108.9M の判断ブロック | noul・choice 2〜256・score 0〜5。17 択以上は vLLM が必要で「labels past P were never seen in training」 | 空欄(「multilingual behaviour … was not systematically measured」) | 「Values can differ in the third decimal between runs」「results depend slightly on which requests are batched together」 | B200 1 枚: 128 件まとめて 1 件 4.2 ms(約 240 件/秒)・単発 137 ms | 文字版はなし(VL 版あり) | LoRA r=16 の手順の記載あり。利用者向けの追加学習の案内はなし | **あり**。「498,010 rows, TypeSafe Jev 1.13 full output distributions via OpenRouter」 |
| **JEV-27B-VL** | AutoTrust AI・Apache-2.0 | JEV-27B+視覚 | choice 2〜256 | 空欄(タグは English のみ) | 「`--max-num-seqs 8` is required」。超えると「vLLM's LoRA path for this multimodal model class returns wrong System 1 probabilities」 | B200 1 枚: 画像 6 枚つき 4,000 件を 316 秒(約 13 件/秒) | あり(画像の判断は「zero-shot」) | 同上 | **あり**(Jev の分布との KL 約 0.017・一致 95.8%) |
| **OpenJev**(openjev/openjev) | 組織 openjev。**重みは CC BY-NC 4.0**(非商用)。コードは Apache 2.0。商用は別契約 | タグは qwen3_5。名前は本文に無い | choice・noul・score。「Up to 52 options per question in a single pass」 | **一部あり**: MASSIVE(ドイツ語・フランス語・ヒンディー語・日本語)80.4% → 85.8%(240 問の合計。日本語だけの値は無い) | 空欄。選択肢の順を入れ替えると 2.3% で答えが変わる | 「7 requests per second on distinct 1,200-token pages at concurrency 8, on a single GPU」 | あり(1 リクエスト 1 枚) | 案内なし | 記述なし |
| Open-Jev(razorback16) | Apache-2.0 | DiffusionGemma 26B-A4B | 既存ノート参照 | 既存ノート参照 | 既存ノート参照(読み直しで平均する=非保証) | 既存ノート参照 | | | 無関係と明記 |
| **decider**(2b・4b・12b・35b-a3b ほか) | Mapika(個人)・Apache-2.0 | Qwen3.5-2B/4B/35B-A3B-Base、12b は Gemma-4-12B-it | Choice 2〜255・Score 2〜10・Noul | **「English only.」** | 「Answers are deterministic for a fixed batch shape and not across batch shapes (bf16 reduction order)」。参照との差は argmax の 0.1〜0.16%・確率差は最大 0.05(4B)。llama.cpp で行を詰めると「moves the probabilities … by up to 0.16 in Q4_K_M」 | 4B: 同時 8 で 21.1 req/s(1,000 リクエスト・8,247 問。GPU の種類は空欄) | 視覚版は開発中 | **手順と学習データの作り方を公開**(約 95 の公開データ・1 エポック GH200 で 5.3 時間) | **なし**。「Nothing was distilled from Jev.」教師は手元の Qwen3.5-27B |
| **Kev**(0.8b・4b・9b・27b) | jaredpalmer・Apache-2.0 | Qwen3.5-Base(0.8b・4b・9b)、Qwen3.8-27B | noul・choice 1〜255・score 1〜255 | 空欄 | 「Asking questions together or separately produces probabilities within 4e-6 in the fp32 tests」。bf16 の配信と fp32 の評価の差は最大約 0.03(GPU)で、「the top answer changes on about one question in 300」 | 64 同時・6 問: 4B が H100 で 100.8 req/s、9B が H100 で 79.5、27B が H100 で 28.9 | 空欄 | **手順を公開**(「A Kev-4B training run costs about \$1 on an H100」) | **なし**。「No Jev outputs were used for training.」 |
| **Laya** | Convai Innovations・Apache-2.0 | ModernBERT-large(395M)+判断ヘッド。多言語版は mmBERT-base | choice・score・noul。選択肢の文字数の予算 192 トークン(英語)/256(多言語) | 空欄(「100+ languages」と書くが日本語の個別の値なし) | 空欄 | T4 1 枚で「103–332 questions/sec batched」 | 空欄 | Kaggle の手順あり | 記述なし(Jev の値は「third-party published, never measured here」) |
| **pplx-decider-v1-27b** | Perplexity・Apache-2.0 | Qwen3.8-27B | choice・noul。上限の記載なし | 空欄(Belebele 94.00% のみ) | 空欄 | 空欄 | あり | 案内なし | 記述なし |

Decision Index は、上の 10 系統のほかに**全 70 件**の自前ホストのモデル(LoRA・判断ヘッド・推論の工夫だけのもの・拡散型・エンコーダ型)を同じ問題で測っている(#8。Clef は 09-28 の生成時点で未掲載)。

### 2-2 権利面の整理(事実のみ)

- **JEV-27B と JEV-27B-VL は Jev の出力で学習したと自分で書いている**(OpenRouter 経由)。重みは Apache-2.0 だが、教師データの取得が TypeSafe の MCA §2.3(b)(出力で蒸留しない)に当たるかどうかは、データを集めた者と TypeSafe の間の問題である。v2 がその重みを使うことの法的な位置は**本答申では判断しない**(指示書 §7-4 のとおりユーザーへ相談)。
- **Clef・Kev・decider は Jev の出力を使っていないと明記**している(Clef は「社内の合成データ」と書くだけで、否定の明記ではない)。
- **OpenJev(openjev/openjev)は重みが非商用**。v2 の目的のうち商用化(長期構想)と衝突する。
- **Clef の評価の表の一部は TypeSafe の評価課題(請求書・顧客対応・セキュリティ事案・エージェントの記録)**で、Jev との比較を Cloudflare が自分で出している(#4)。公表禁止が消えた後の比較である。

## §3 評価の論文とベンチマーク

### 3-1 2 本の第三者の評価

| 評価 | 規模と形 | Jev の値 | 出典 |
|---|---|---|---|
| **Decision Index 0.2.1**(HF Space・有志) | 120,340 リクエスト・43 ベンチマーク(採点 38)・5 分野を等重み・偶然の水準を 0 に補正した値が見出し。ハードウェア「1 x NVIDIA RTX PRO 6000 (Blackwell Server Edition, 96 GB), one GPU per run」 | 見出しの値 **57.91**(補正前 68.09)。ECE **0.074**・確信の平均 0.8115・正答率 0.7393・Brier 0.3558(32 ベンチマーク・6 分の 1 抽出・72,594 件) | #8・#9 |
| **JevBench v1.5**(Benchmark Heaven) | 1 系あたり 1,624 判断(公開 904・封印 720)。知能の半分を封印から。4 軸(知能・較正・速さ・費用)の合成 | v1.5.6 の掲示板で知能 72.0・較正 88.0(#21・○) | #19〜#21 |

オープンなモデルの上位(Decision Index の見出しの値。ECE): Rune 26B-A4B v3 57.44(0.120)・Decider chat Gemma-4-31B 57.33(0.047)・pplx-decider-v1-27b 56.40(0.018)・Jebadiah 27B 54.67(0.014)。27B 級の自前ホストのモデルは Jev(57.91)と同じ帯にある。4B 級は 40 前後(decider-4b 40.70・Kev 4B 34.64)、1B 未満は 20 未満(#8)。

**フロア(実データ同士のばらつき)の併記**: 全 70 件の ECE は 0.014(Jebadiah 27B)から 0.568(LFM2.5-350M-RLCD)まで。同じ Jev でも、Laya のカードは自分の評価セットで「Jev 0.246」と書いている(#14)。**ECE は評価セットで 3 倍以上動く**ので、Jev の「較正済み」は特定の問題の集まりについての値である。

### 3-2 公開の問題と封印した問題のずれ(汚染)

| 事例 | 中身(逐語) | 出典 |
|---|---|---|
| JevBench の過学習の罰 | 「gap = I_open − I_sealed」「excess = gap − G_med」「penalty = max(0, 1 − max(0, excess − 8) / 100)」。「8 points is about 2.5 × the SE of one system's gap」(1 系のずれの標準誤差は約 3.2 点=推測の割り算)。v1.4 は「A public-to-sealed accuracy gap above 25 percentage points reduces Intelligence」 | #19・#20 |
| decider-4b v2 | 「held back by Intelligence on the sealed yes/no (Noul) items: 43 open against 19 sealed, chance-corrected」(24 点のずれ) | #17 |
| JevK5 と Jev | 封印 308 問で「JevK5 answered 33.1% correctly and Jev answered 36.7%」。評価者はこの集まりを「unusually difficult」と書く(=公開と封印の難しさが揃っていない) | #22 |
| 封印の限界 | 「The held-out split is sent to the services being evaluated in order to get predictions. Not public is not the same as not seen, and this is not a contamination proof.」。v1.5 では「The 303 unpublished v1.2 items have already been sent to operator APIs, so they no longer count as a holdout.」 | #19・#20 |
| Decision Index の除外 | reflex-4b を外した理由「that adapter was trained on 800 MMLU-Pro test items」。較正の計算でも「Rows an entrant trained on count as wrong here too.」 | #8・#9 |
| 予測問題の汚染 | ForecastBench について「unpublished Jev cutoff means contamination not certified」 | #9 |

**v2 にとっての事実**: 公開の点数だけで選ぶと、公開の問題に合わせたモデルを選ぶおそれがある。v2 の検証は v2 自身の封印行(holdout)で行う必要があり、封印行を外部 API に送った時点で封印ではなくなる(JevBench の 303 問と同じ構図)。

### 3-3 社会シミュレーション・人の選択の予測での使用例

- **Jev 型のモデルを人の集団のシミュレーションに使った例は見つからなかった**(空欄)。見つかった用途は、エージェントの道具選び・ガードレール・ゲームの操作(decider の Tetris など)・分類である。
- 人の選択の予測に LLM を使った先行は §4 にまとめる(どれも Jev 型ではなく、自己回帰の LLM か、その微調整)。

## §4 確率の意味の違いをどう埋めるか

### 4-1 違いの中身

- Jev の RLCD の目的は「Higher probability should correspond to a greater chance that the answer is correct.」(R-40 §4-1)。Clef も「Brier loss to refine probability calibration」で、正解ラベルに対する損失である(#4)。
- Kev の較正も「Each checkpoint ships with a fitted temperature」で、正解に対する温度である(#16)。
- v2 が要るのは「この状況の人が A を選ぶ割合」である。正解が 1 つに決まらない問いで、正しさに較正したモデルは**確信の側へ寄る**(正しさの較正は、答えが割れる場面でも 1 つに賭けるほど得をする)。この部分は推測で、直接測った文献は見つからなかった(空欄)。
- 関連する事実: LLM は「describe the opinion distribution」の方が「simulate such distributions」より正確(Meister ほか 2024・#26・△)。人の意見の分布とのずれは、属性で誘導しても残る(Santurkar ほか 2023・#30・△)。

### 4-2 埋め方の先行例

| 方法 | 先行例 | 結果(抄録の範囲) | v2 との距離 |
|---|---|---|---|
| **分布そのものに合わせる微調整** | Cao ほか 2025(#25) | 「a fine-tuning method based on first-token probabilities」で調査の回答分布とのずれを減らす。未見の問い・国・調査でも他の方法を上回る。ただし「even our best models struggle … especially on unseen questions」 | Jev 型の出力(選択肢ごとのロジット)は 1 トークン目の確率と同じ形なので、この損失はそのまま当てられる(推測) |
| **手段選択の微調整** | Alsaleh & Farooq 2025(#28) | 11 個の 1〜12B の LLM・3 つのデータ・396 構成。微調整した LiTransMC が重み付き F1 0.6845・JSD 0.000245 で、離散選択モデルと機械学習の分類器を上回る | PT 2018 の手段選択と同じ種類の課題。手元で動く大きさ |
| **行動実験での微調整** | Centaur(#24) | 「over 60,000 participants performing over 10,000,000 choices in 160 experiments」で微調整し、未見の参加者で既存の認知モデルより良い | 選択の分布そのものを学ぶ前例。基盤と数値は抄録に無い(空欄) |
| **ゼロショットの予測** | Mo ほか(#27) | 多項ロジットなどと「comparable to, and in some cases competitive with」 | 分布が合うかは抄録に無い |
| **LLM の確率から抽選する ABM** | トゥールーズの手段選択(#29) | 「A decision-maker returns one probability per itinerary」「The executed itinerary is drawn from those probabilities with a fixed seed」。調査に当てはめたロジットを基準として並べ、手段の割合を EMD・JSD・L1 で採点 | v2 の「分布から seed つきで抽選」と同じ形。結果の数値は README に無い(空欄) |
| **後処理の温度** | Guo ほか 2017(#31・R-38 既出) | 1 パラメータの温度スケーリングが多くのデータで有効 | **温度 1 つでは順位は変わらない**(Kev「Calibration is a single temperature. It can't reorder confidences」#16)。割合の形を直すには足りない場合がある |

### 4-3 v2 で使える人の行動データ(既存の決定との接続)

- PT 2018 の行き先と手段の選択、社会生活基本調査の活動の事前分布(D-119 で既に使っている)、購買は空欄(v2 が持つ購買の個票は確認できていない)。
- どの方法でも、較正用と封印用を**先に分ける**(CLAUDE.md §4)。外部 API へ封印行を送らない(§3-2)。

## §5 候補 (G)・古典モデル(D-119)との関係

| | 何か | 強み | 弱み | 出典 |
|---|---|---|---|---|
| (G) 自前艦隊の logprob 判断 | vLLM の 8B 級の 1 トークン目の確率。`VLLM_BATCH_INVARIANT=1` で logprobs 32/32 一致を実測(B14) | **バッチ不変を実測済み**。今の艦隊のまま動く | 選択肢の表層形の競合(R-38 §2-2-1)。較正は後処理が要る | [v2-openjev-note.md](v2-openjev-note.md) §5・R-38 |
| Jev 型(Clef ほか) | 状態と型つきの問いから、1 回の前向き計算で全選択肢の確率 | 1 回で複数の問い(驚き 0〜5 と行動を同時に)。画像も入る | **バッチ不変は未測定**(Clef は記載なし。decider は「バッチの形が違えば一致しない」と明記) | §2 |
| 古典モデル(D-119) | 社会生活基本調査の事前分布+食事の門+満足化の選び手。LLM 0 呼 | 現実の割合に直接つながる。速い | 個人の文脈に反応しない | PENDING #58 |

**関係の事実**: (G) と Jev 型はどちらも「選択肢ごとの確率を 1 回で返す」もので、違いは学習(正しさへの較正を学習したか)と製品の形である。Jev 型の多くは Qwen の上の LoRA と判断ヘッドで(§2)、(G) の艦隊と同じ系統の基盤の上に作られている。

## §6 蒸留した小さな見張りのモデル

| 先行の系統 | 例 | 何を判定するか | 出典 |
|---|---|---|---|
| early-exit | CALM(Schuster ほか 2022) | 1 トークンごとに「確信が十分なら途中の層で出る」。最大約 3 倍の高速化 | #32 |
| cascade | FrugalGPT | 小さなスコアラが閾値を超えなければ次を呼ぶ | R-38 §2-3(既出) |
| router | RouteLLM | 学習したルータが強いモデルと弱いモデルを振り分ける | R-38 §2-3(既出) |
| 小さな判断モデル | Kev 0.8B・decider-2b・Laya | L4 で 62.8 req/s(Kev-0.8B・64 同時・6 問)、CPU 8 スレッドで 0.12〜0.31 s(decider-2b・GGUF)、T4 で 103〜332 問/秒(Laya) | #16・#17・#14 |

**09-25 §4.4 との接続(事実)**: §4.4 のラベルは「上の層を呼んだ結果、行動が下の層の答えから変わったか」。これは cascade の「呼ぶべきだったか」と同じ形の教師である。R-39 §5-5 のとおり、社会シミュで動的に呼び分ける先行は見つかっていない。見張りの小さなモデルは、Kev・decider の手順(LoRA と判断ヘッド、1 回の学習が 1 ドル級)で作れる大きさである(#16)。教師を本家 Jev にすると §1 の蒸留禁止に当たる。

## §7 v2 への当てはめ(**親の案**。以下はすべてリサーチ役の推測で、決定ではない)

### 7-1 費用と上限の見積り(推測)

| 量 | 計算 | 結果 |
|---|---|---|
| 移動と購入の呼び出し | 約 270 万回/日 × (53% + 39%) | 約 248 万回/日(移動 143 万・購入 105 万) |
| 本家 API で流す時間 | 248 万 ÷ 80 回/秒 | **約 8.6 時間/シム日**(レートだけ。950 トークン/回ならトークンの上限は 105 回/秒で、回数の上限が先に当たる) |
| 決定モデル約 1,950 万件/日(R-73)を本家 API で | 1,950 万 ÷ 80 | 約 67.7 時間/シム日 |
| 同じ 248 万件を自前の GPU で | Kev-4B(H100・100.8 req/s)/ Kev-27B(H100・28.9)/ JEV-27B(B200・約 240 件/秒) | 約 6.8 / 23.9 / 2.9 GPU 時間 |
| 1,950 万件を自前で | 同上 | 約 53.7 / 187 / 22.6 GPU 時間 |

自前の値は**短い文・6 問**などの公表条件のもので、v2 の入力(1 呼あたり約 1,428 トークン・R-73)では遅くなる(推測)。Clef の処理量は公表が無く空欄。

### 7-2 H8 の壁打ちの問い(案・8 本)

| 番号 | 問い | 親の案(推測) |
|---|---|---|
| H8-1 | 主役のモデルは自前ホストか API か | 自前ホスト。本家 API は回数の上限と決定論の非保証で主役に向かない(§1・§7-1)。API は比較の腕に |
| H8-2 | 最初の候補 | Clef-flash(9B・Apache-2.0・Jev の出力なし・画像可)と Kev-9B または decider-4b(手順が公開・Jev の出力なし)を並べて測る。JEV-27B は権利面でユーザーに相談(指示書 §7-4) |
| H8-3 | 最初に置き換える判断 | **購入(39%)から**。選択肢が店と品目で閉じていて、正しさの較正と人の割合のずれを測りやすい。移動(53%)は行き先と手段が PT 2018 で照合できるので 2 番目 |
| H8-4 | 確率の意味の違いをどう埋めるか | 較正用の行動データで「分布に合わせる損失」の LoRA を足す(Cao 型)。温度だけで済ませない。較正と封印は先に分ける |
| H8-5 | (G) と D-119 の扱い | (G) と D-119 は消さず、物差しとして同じ場面で並べる腕にする(切替口) |
| H8-6 | 評価の形 | 個体: 状況を固定した場面の選択の分布(D-100 の再問い評価器)。小集団: 世帯・職場での組み合わせ。群衆: PT 2018 と人流の割合。どの段でも Jev 型と (G) と D-119 を並べる |
| H8-7 | 厳密モード(⑨の (c))の条件 | ①重みを手元に置く ②バッチの形を固定する(decider の記述どおり形が変わると一致しない) ③B14 と同じ形で不変性を実測して合格する。満たせないモデルは厳密モードでは使わない |
| H8-8 | 見張りの小さなモデル | §4.4 のラベルで、教師はオープンなモデル(本家 Jev は使わない)。1B 未満から始め、呼び漏れを測るため一定割合を無作為に上の層へ回す(09-25 §4.4 の注記と同じ) |

## §8 空欄の一覧(19 件)

1. 本家 Jev の決定論の公式回答(FAQ の本文が JS 展開で読めない)。
2. 本家 Jev のレート上限が変わった日付(今の models.md に日付が無い)。
3. MCA の旧版の全文(R-40 の逐語の記録しか無い。改訂日は Sep 23, 2026)。
4. Decision Index の「20 choices」の分母の件数と、JEV-27B の「4.3 %」の測り方。
5. Clef・Clef-flash の決定論とバッチ不変。
6. Clef・Clef-flash の処理量(件/秒/GPU)と遅延の測定の GPU・同時数(Cloudflare の表の Jev・Kev-9B・Laya・djev の遅延は Decision Index の値と一致するので同じ計測系の可能性があるが、推測)。
7. Clef・Clef-flash の日本語の評価・ECE・選択肢の上限・学習データの詳細。
8. JEV-27B・Kev・pplx-decider・Laya の日本語の評価(OpenJev は 4 言語合計のみ。decider は英語のみと明記)。
9. pplx-decider-v1-27b の処理量・決定論・学習データ。
10. OpenJev(openjev/openjev)の基盤の名前・学習データ・決定論。
11. decider の SERVING.md の表の GPU の種類。
12. JevBench の各モデルの公開と封印の値(集計しか公開されない)と、検索要約にあった G_med の値(原典で確認できず)。
13. Decision Index に Clef が入った結果(09-28 の生成時点では未掲載)。
14. Jev 型のモデルを人の集団のシミュレーションに使った例。
15. Jev 型のモデルを人の行動データ(手段・行き先・時間利用・購買)で較正した例。
16. 正しさへの較正が、答えの割れる問いで確信の側へ寄ることを直接測った文献。
17. Centaur の基盤と数値(抄録のみ。Nature 版は読めず)。
18. トゥールーズの手段選択の結果の数値。
19. v2 が持つ購買の個票の有無。

## lit README 追記行

| R-83 | Jev 型の決定モデル(本家の規約の現状・オープン 10 系統・Decision Index と JevBench・確率の意味の違い・見張り) | 2026-10-03 | B(親検収 未) | [v2-r83-jev-type-decision-models.md](v2-r83-jev-type-decision-models.md) |
