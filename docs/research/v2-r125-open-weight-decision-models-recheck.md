# R-125 答申: 公開重みの判断モデルの再検証(11-01/§13 R-J)=5070(12 GB)で比べる候補の一覧

<!-- hdr:v1 -->
- **分野**: 自然言語処理・機械学習 #27 / ソフトウェア工学 #29 / 研究倫理・情報法 #31 | **重要度**: P1([回答 11-01](../design/v2-answers-2026-11-01.md) §11・§13 R-J、[指示書 11-01](../design/prompt-2026-11-01.md) 段 1 の 2・3、[5070 の指示書](../design/prompt-2026-11-01-5070.md)「柔軟にしてほしい所」と「安全の規則」2)
- **一次確認**: **B**(サブ実読。出典 37 本=◎ 33・○ 2・△ 1・× 1。空欄 14 件は §空欄)・親検収 未
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 作成 2026-11-01・リサーチ役サブ(Opus 5.5)。子サブ未起動。重みの取得・pip・git clone・ファイルの保存はしていない。読み方は 2 通り。(1) WebFetch(頁を Markdown にして小さなモデルが要点と引用を返す=引用は返ってきた文のまま)。(2) Hugging Face の `api/models/<repo>` の JSON を python の urllib で標準出力に読んだだけ(37 本・保存なし・§3 の「API」の欄)。カードの数値は (1) 経由なので、正典化の前に親の写し検査を勧める。コミットなし・台帳/設計書/src 未編集。
> 既存答申との関係: 本家 Jev の規約と 10-03 時点の 10 系統は [R-83](v2-r83-jev-type-decision-models.md)、10-06 時点の候補・日本語・規約は [R-94](v2-r94-judgment-model-candidates-update.md) を正とし、繰り返さない。本書は **10-06 以後の変化**と **R-94 の空欄の埋め**(配布の形・trust_remote_code・ライセンス・出自・VRAM)だけを書く。5070 の環境(常駐アプリが 2,081 MiB を使う・vLLM 0.28.0 案)は [R-123](v2-r123-rtx5070-qwen3-8b-runbook.md) を正とする。第 2 世代(活性+ヘッド)は R-126 の範囲。

## §0 要旨

1. **一覧はこの 1 か月で 10 倍に増えた**。S1MB のブログ(2026-09-30)は 23 本のまま。ところが結果のデータセット `hotchpotch/s1mb-result` は 2026-10-30 更新で **218 のモデルの枠**を持つ。awesome 系は 3 本(公開重み 43・28・54 項目)。4B 以下の公開重みは名前だけで 100 を超える。全部を手で読むのは無理なので、§5 に「API の JSON だけで落とす一次の検査」を案として書いた。
2. **S1MB は英語だけではなくなった**。`japanese-v1`(27 課題・入力は非公開)が加わった。ただし測られているのは同じ作者の日本語モデル **saihai**(310M と 8B)の 2 本だけ(◎ データセットのカード)。
3. 11-01 の例 10 本のうち、**4B 以下で除外の 4 条件と trust_remote_code の両方を通るのは 6 系統**。OpenJev(AlexWortega)4B/2B/0.8B・JevK5 4B/2B・decider-0.8b・minojev・JevForge-0.8B・laya 系の 3 本。bekko(ライセンス未定+trust_remote_code)と Tev1(重みのライセンスが「調整中」)は除外。kev・Open-Jev-2B(ZefanCai)・von は**判断ヘッドを `.pt`(pickle)で配る**ので「safetensors のみ」に当たらない(保留)。
4. **日本語を学習か評価に含むのは 4B 以下で 6 本**。即断(ja のみ・Apache・safetensors・独自コードなし)・saihai-310m(ja/en・Apache・**trust_remote_code**)・Vela-2.0-0.3B(17 言語に ja・trust_remote_code)・d1-omni-600M と d1-3B(ja・trust_remote_code・LFM のライセンス)・laya-multilingual(50 言語に ja・R-94 で日本語の成績が悪い)。安全の規則 2 をそのまま当てると、**日本語で測った値がある候補は即断だけ**になる。
5. 本家 Jev の出力からの蒸留を明記した 4B 以下の公開重みは、読んだ範囲には無い。ただし JevK5 は教師に GPT-6 Luna(OpenAI の API)を使い、カードは「OpenAI の規約に従う」と書く(◎)。
6. 推論の形はほぼ全部「候補の上の分布を 1 回で返す」(dm_eval の Choice)。候補ごとに独立に点を出すもの(Score)は Open-Jev-2B・JevForge・OpenJev(NLI)。Tev1 だけが文字を生成する(Noul・それ以外)。
7. (G) の基準は vLLM の `logprobs`・`prompt_logprobs` に加え、最新の文書に **`logprob_token_ids`(指定した最大 128 個のトークンの確率を返す)** がある(◎)。0.28.0 にあるかは未確認。`Qwen/Qwen3-8B-AWQ` は vLLM のバッチ不変の試験済みの一覧に載る(◎)。

## §1 出典の表(読んだ日はすべて 2026-11-01)

等級: ◎ 原文を読んだ(API の JSON・カード・README の該当の節)/ ○ 要約・二次 / △ 検索の要約だけ / × 読めなかった

| # | 出典 | URL | 等級 | 使った所 |
|---|---|---|---|---|
| 1 | S1MB ブログ(hotchpotch・Published September 30, 2026) | https://huggingface.co/blog/hotchpotch/system-one-mosaic-benchmark | ◎ | 23 本の表・TP/AP・英語のみの記述 |
| 2 | `hotchpotch/s1mb-result` のカード | https://huggingface.co/datasets/hotchpotch/s1mb-result | ◎ | japanese-v1・「54 measurements across two model folders」 |
| 3 | 同 tree API(lastModified 2026-10-30) | https://huggingface.co/api/datasets/hotchpotch/s1mb-result/tree/main | ◎ | 218 の枠の名前 |
| 4 | 同 saihai-310m の枠の tree | https://huggingface.co/api/datasets/hotchpotch/s1mb-result/tree/main/hotchpotch__saihai-v1-310m | ◎ | 日本語 27 課題の名前 |
| 5 | S1MB-leaderboard(Space) | https://huggingface.co/spaces/hotchpotch/S1MB-leaderboard | × | 動的な頁で表が読めず |
| 6 | awesome-decision-models(AnotiaWang・146 commits・fork 146) | https://github.com/AnotiaWang/awesome-decision-models | ◎ | 公開重み 43 項目(研究所 18・コミュニティ 25)・API 11 |
| 7 | awesome-system-one(yanng981・「last checked … on 2026-10-02」・28 models) | https://github.com/yanng981/awesome-system-one | ◎ | 28 項目 |
| 8 | awesome-system-one(andyrewlee・93 commits) | https://github.com/andyrewlee/awesome-system-one | ◎ | 公開重み 54 項目・API 23 |
| 9 | HF API `api/models/<repo>`(37 本) | https://huggingface.co/api/models/ | ◎ | ライセンスの tag・言語の tag・architectures・auto_map・safetensors の総数・ファイルの拡張子・sha |
| 10 | `hotchpotch/bekko-system-one-v0-400m` カード | https://huggingface.co/hotchpotch/bekko-system-one-v0-400m | ◎ | 「This card does not assign a license.」・trust_remote_code=True |
| 11 | `togethercomputer/Tev1-4B-experimental` カード | https://huggingface.co/togethercomputer/Tev1-4B-experimental | ◎ | 重みのライセンス「being finalized」・1 文字を生成 |
| 12 | `jaredpalmer/kev-4b` カード | https://huggingface.co/jaredpalmer/kev-4b | ◎ | head.pt・常駐 14.3 GB・T=2.41 |
| 13 | `alibiserikbay/JevK5` カード | https://huggingface.co/alibiserikbay/JevK5 | ◎ | 教師 2 本・約 9 GB・bit-identical |
| 14 | `AlexWortega/openjev` カード | https://huggingface.co/AlexWortega/openjev | ◎ | NLI・0/231・MIT |
| 15 | `ZefanCai/Open-Jev-2B` カード | https://huggingface.co/ZefanCai/Open-Jev-2B | ◎ | 候補ごと 4,096 トークン・温度 1.5188 |
| 16 | `Mapika/decider-0.8b` カード | https://huggingface.co/Mapika/decider-0.8b | ◎ | 教師 Qwen3.5-27B・English only |
| 17 | `wfzyx/von` カード | https://huggingface.co/wfzyx/von | ◎ | option_marker.pt・Archived |
| 18 | `convaiinnovations/laya` カード | https://huggingface.co/convaiinnovations/laya | ◎ | 3 変種・pip laya・ECE |
| 19 | `zeredy879/minojev` カード | https://huggingface.co/zeredy879/minojev | ◎ | 凍結の Qwen3-1.7B+0.8M のヘッド |
| 20 | `AndeyTait/JevForge-0.8B` カード | https://huggingface.co/AndeyTait/JevForge-0.8B | ◎ | 学習の出所 3 つ・文脈 32,768 |
| 21 | `GeneLab/sokudan-ja-310m` カード | https://huggingface.co/GeneLab/sokudan-ja-310m | ◎ | v0.2.1 のまま・パッケージ 0.3.0 |
| 22 | `hotchpotch/saihai-v1-310m` カード | https://huggingface.co/hotchpotch/saihai-v1-310m | ◎ | 日本語 S1MB の値・trust_remote_code |
| 23 | `hotchpotch/saihai-v1-8b` カード | https://huggingface.co/hotchpotch/saihai-v1-8b | ◎ | llm-jp-4.1-8b-thinking・17.2 GB |
| 24 | `vllm-sr/Vela-2.0-0.3B` カード | https://huggingface.co/vllm-sr/Vela-2.0-0.3B | ◎ | 17 言語・Gemma の tokenizer の規約 |
| 25 | `LiquidAI/d1-3B` カード | https://huggingface.co/LiquidAI/d1-3B | ◎ | trust_remote_code・lfm1.0 |
| 26 | `internlm/Intern-Decision-4B` カード | https://huggingface.co/internlm/Intern-Decision-4B | ◎ | 選択肢 62 まで・ECE |
| 27 | `h2oai/h2o-lightning-4b` カード | https://huggingface.co/h2oai/h2o-lightning-4b | ◎ | 改造した vLLM・9.3 GB |
| 28 | `Valen-Team/Valen-4B` カード | https://huggingface.co/Valen-Team/Valen-4B | ◎ | trust_remote_code・GGUF の不合格 |
| 29 | jiwo の README | https://github.com/jiwidi/jiwo | ◎ | eljiwo/jiwo-4b・0.8b・英語のみ |
| 30 | vLLM `SamplingParams`(latest developer preview) | https://docs.vllm.ai/en/latest/api/vllm/sampling_params.html | ◎ | logprobs・prompt_logprobs・logprob_token_ids |
| 31 | vLLM Structured Outputs(2026-10-24 の版) | https://docs.vllm.ai/en/latest/features/structured_outputs.html | ◎ | choice・guided_* の廃止 |
| 32 | vLLM Batch Invariance(2026-10-19 の版・beta) | https://docs.vllm.ai/en/latest/features/batch_invariance.html | ◎ | Qwen3 8B-AWQ が試験済み |
| 33 | `Qwen/Qwen3-8B-AWQ` の API | https://huggingface.co/api/models/Qwen/Qwen3-8B-AWQ | ◎ | apache-2.0・AWQ 4 ビット |
| 34 | `vllm-sr/Decision-2.0-Nox-4B`・`kirp/jpt-4b`・`isHeSatoshi/smalljev-semantic-v9` の API | (#9 と同じ形) | ◎ | custom_code・cc-by-nc-4.0・.pt |
| 35 | Hakky の記事(saihai の紹介) | https://book.st-hakky.com/news/japanese-decision-model-saihai-benchmark | ○ | 訓練セットで学習した旨の二次の要約 |
| 36 | PyPI `sokudan` | https://pypi.org/project/sokudan/ | △ | 検索の要約に「Release: v0.3.0」 |
| 37 | jiwo・Valen の HF の検索 API | https://huggingface.co/api/models?search= | ○ | リポ名の特定だけ |

## §2 一覧の読み直し(A)

### 2-1 一覧ごとの本数

| 一覧 | 読んだ日 | 載っていた本数 | 4B 以下の公開重み(目安) | 注 |
|---|---|---|---|---|
| S1MB ブログ(#1) | 2026-11-01 | 23(Jev 1.13 を含む) | 19 | 09-30 の時点の表のまま |
| S1MB の結果(#3) | 2026-11-01 | 218 の枠(+ファイル 3) | 名前からの推測で約 100 | reranker などの比較用の枠を含む。日本語の結果は 2 枠だけ(#2) |
| S1MB の順位表(#5) | 2026-11-01 | 読めず(×) | | 動的な頁 |
| awesome-decision-models(#6) | 2026-11-01 | 公開重み 43・API 11 | 約 25 | 原本は AnotiaWang。fork が 5 つ以上ある(検索の結果) |
| awesome-system-one(#7 yanng981) | 2026-11-01 | 28 | 約 15 | 「last checked … 2026-10-02」 |
| awesome-system-one(#8 andyrewlee) | 2026-11-01 | 公開重み 54・API 23・抽出 1 | 約 25 | 同じ名前の一覧が 2 つある。指示書の指す方は不明(§親に聞きたいこと 6) |

### 2-2 10-31 の例との照合

| 10-31 の例 | 見つかった正式の名前(リポ) | 状態 |
|---|---|---|
| OpenJev 4B/2B/0.8B | `AlexWortega/openjev` の下位フォルダ `qwen3.5-4b-nli-v5`・`qwen3.5-2b-nli-v5`・`qwen3.5-0.8b-nli-v2s-long`(S1MB の「OpenJev-4B (Alex)」ほか) | あり。組織 openjev の `openjev/openjev`(27B・CC BY-NC 4.0)とは別物 |
| Open-Jev 2B | `ZefanCai/Open-Jev-2B` | あり |
| kev 4B/0.8B | `jaredpalmer/kev-4b`・`kev-0.8b` | あり。S1MB の結果には kev-0.5b・0.6b・8b の枠も増えた(#3) |
| bekko-system-one 400M/68M | `hotchpotch/bekko-system-one-v0-400m`・`-68m`(と `-17m`) | あり。ライセンスは今も未定 |
| decider-0.8B | `Mapika/decider-0.8b` | あり。S1MB の結果に decider-2b・4b・2b-vision も載る |
| JevForge-0.8B | `AndeyTait/JevForge-0.8B` | あり(2026-10-16 に更新) |
| laya | `convaiinnovations/laya`・`laya-typed-decisions`・`laya-multilingual` | あり |
| minojev | `zeredy879/minojev` | あり |

消えたものは無い。von は残っているが「Archived. Von is no longer maintained」(#17)。

### 2-3 10-06 以後に増えた、比べる価値の高いもの(4B 以下)

- **日本語**: saihai-v1-310m(2026-10-14 作成・ja/en・Apache-2.0)・saihai-v1-8b(llm-jp-4.1-8b-thinking・9B 級=クラウド)。Vela-2.0-0.3B(vllm-sr・17 言語に ja)。d1-3B と d1-omni-600M(Liquid AI の重みの公開・ja の tag)。
- **研究所の 4B 以下**: Intern-Decision 0.8B/2B/4B(internlm・2026-09-26 作成)・h2o-lightning-4b(H2O・v1.4.2)・Decision-2.0 の Kai-0.6B/Eos-0.8B/Sol-2B/Nox-4B(vllm-sr)・Valen 0.8B/2B/4B・jiwo 0.8b/4b。
- 名前だけで中身を読んでいないもの(4B 以下・S1MB の結果か awesome にある): §5 の末尾に並べた。

## §3 候補の表(B)=S1MB の 4B 以下 19 本+既存の口の即断+日本語の saihai-310m

### 3-1 配布と権利(API の JSON とカード)

列の印: safetensors は「重みとヘッドが全部 safetensors か」。trc は trust_remote_code(auto_map か custom_code の tag か、カードが要ると書くか)。独自=作者の pip パッケージかリポのコードが推論に要る。

| 名 | 公式リポ | パラメータ | safetensors | trc・独自コード | ライセンス(商用) | 学習データの出自 | 更新日 | 等級 |
|---|---|---|---|---|---|---|---|---|
| bekko-system-one-v0-400m / 68m / 17m | hotchpotch/bekko-system-one-v0-* | 395M / 68M / 16.8M | ○(本体 .safetensors・ONNX あり) | **trc 要**(カードの例が `trust_remote_code=True`)・inference_v0.py | **未定**(「This card does not assign a license.」) | 既存の NLP・検索のデータを 3 型に変換+合成。教師の名は無い。評価と 77 の部分集合の名が重なる | 2026-09-30 | ◎ |
| Tev1-4B-experimental | togethercomputer/Tev1-4B-experimental | 4,659,865,088 | ○ | trc なし(標準の Qwen3_5ForConditionalGeneration) | **重みは未定**(「being finalized」)。基盤は Apache-2.0 | 記載なし(Qwen3.5-4B の SFT・データの出典ごとの条件) | 2026-09-23 | ◎ |
| Tev1-0.8B-experimental | togethercomputer/Tev1-0.8B-experimental | 873,438,784 | ○ | trc なし | ライセンスの tag なし(4B と同じ扱いと推測) | 同上 | 2026-09-25 | ◎(ライセンスは推測) |
| kev-4b / kev-0.8b | jaredpalmer/kev-4b・kev-0.8b | 4.21B / 753M(S1MB の TP) | **×(head.pt)**+LoRA の .safetensors | 独自(Kev のリポを `uv sync`) | Apache-2.0(アダプタとヘッド・基盤とも) | 「No output of Jev … was used.」公開データの元ラベル+プログラムで作った合成+名のない公開重みの教師 2 本が一致した行 | 2026-10-01 | ◎ |
| JevK5(4B)/ JevK5-2B | alibiserikbay/JevK5・JevK5-2B | 4,205,751,296 / 1,881,825,088 | ○ | 独自(jevk5 の runtime。Hub の generate の例は判断の読み口ではない) | Apache-2.0(重み) | 教師 Qwen3.6-27B(3,270 問)と **GPT-6 Luna**(14,138 問・OpenAI の規約に従うと明記)+人のラベル 30,052 件。Jev は不使用と明記 | 2026-09-25 / 09-24 | ◎ |
| OpenJev-4B / 2B / 0.8B(Alex) | AlexWortega/openjev の下位フォルダ | 4.54B / 2.21B / 853M(S1MB) | ○(使う 3 フォルダは model.safetensors。.pt は 35B 用のヘッドだけ) | trc の記述なし。標準の `AutoModelForSequenceClassification`+`subfolder` | MIT | 公開データの NLI 化。MMLU 等の **test の分割も学習に入れた**と明記。Jev は比較の列だけ。リポに `code/distill_teacher.py` があるが教師の名は読めず(△) | 2026-10-01 | ◎ |
| Open-Jev-2B | ZefanCai/Open-Jev-2B | 1.88B(S1MB・基盤込み) | **×(package/checkpoint/head.pt)** | 独自(GitHub の Open-Jev のローダー)。基盤 Qwen3.5-2B は別に取得 | アダプタとヘッド Apache-2.0・コード MIT | release-v2 の 80,816 行(合成の評価・R-94 #16 では「Jev の予測ではない」) | 2026-09-20 | ◎ |
| decider-0.8b | Mapika/decider-0.8b | 752,393,024 | ○ | 独自(`pip install git+https://github.com/Mapika/decider`)。重みは標準の Qwen3_5ForCausalLM | Apache-2.0 | 教師 **Qwen3.5-27B** の書いたデータ+公開データ・1.47M 例 | 2026-09-22 | ◎ |
| von | wfzyx/von | 394,781,696 | **×(option_marker.pt)** | 独自(von-sdk>=1.3.7) | Apache-2.0 | 公開のラベルつきデータ約 29 万+合成。教師の名なし。**保守終了** | 2026-10-19 | ◎ |
| laya / laya-typed-decisions | convaiinnovations/laya・laya-typed-decisions | 421,293,830 | ○ | 独自(`pip install laya`)。独自の architectures `LayaTypedDecisions`(auto_map なし) | Apache-2.0(tag に commercial-use) | 学習の資料名なし。typed-decisions 版はその train で学習(ラベルの元の「teacher」は R-94 空欄 9 のまま) | 2026-10-03 | ◎ |
| laya-multilingual | convaiinnovations/laya-multilingual | 321,908,998 | ○ | 同上 | Apache-2.0 | 同上 | 2026-10-03 | ◎ |
| minojev | zeredy879/minojev | 凍結の Qwen3-1.7B+ヘッド約 0.8M | ○(本体とヘッドとも) | 独自(minojev パッケージ) | Apache-2.0。「No NC-licensed data」 | banking77・CLINC150・Amazon Polarity・GSM8K の 8,000 件(既存のラベル) | 2026-09-20 | ◎ |
| JevForge-0.8B | AndeyTait/JevForge-0.8B | 854M(S1MB) | ○(best.safetensors) | 独自(GitHub の jevforge の Predictor・28 本の .py) | Apache-2.0 | 「14,842 Open-Jev-derived, 15,347 general and 5,811 Mind2Web」。S1MB のラベルは不使用 | 2026-10-16 | ◎ |
| 即断 sokudan-ja-310m | GeneLab/sokudan-ja-310m | 314,614,274 | ○ | 独自(`pip install sokudan`・PyPI)。repo に .py なし | Apache-2.0(基盤 MIT) | 合成のみ。生成者は **qwen3:30b-a3b-instruct-2507**。Jev を呼ぶコードなし | 2026-09-29(v0.2.1 のまま) | ◎ |
| saihai-v1-310m | hotchpotch/saihai-v1-310m | 約 310M(名前から) | ○(3 本) | **trc 要**(auto_map・custom_code) | Apache-2.0(ruri の基盤と同じ)。学習データは再許諾しない | bekko v0 の 840,947 判断+日本語 131,171 判断(LLM-jp の生成 14,400 を含む)。日本語 7 データの train を含む | 2026-10-15 | ◎ |

### 3-2 推論の形・日本語・VRAM・決定論・較正

接続形は dm_eval の当て口へのつなぎ方。**C**=提示した候補の上の分布を 1 回で返す(Choice)。**S**=候補ごとに独立に点を出し、こちらで正規化(Score)。**N**=文字の生成など、それ以外(Noul)。Jev の型の名(noul=はい/いいえ・score=段階)と字が重なるので注意(§親に聞きたいこと 5)。VRAM はパラメータ数 × バイト数(16 ビット 2・32 ビット 4・4 ビット 0.55 と置いた)で、作業の領域を 1〜2 GB 足す=**推測**。5070 で使えるのは常駐アプリを除いて約 10 GB(R-123 §0 の 1)。

| 名 | Jev の型 | 接続形・入出力 | 上限 | 日本語 | VRAM 16 ビット / 32 ビット / 4 ビット(推測) | 決定論の記述 | 較正の記述 |
|---|---|---|---|---|---|---|---|
| bekko 400m | choice・noul・score・ranking | C(state_json と criteria) | 文脈 7,999・候補 3,800 | なし(「this release targets English」) | 0.8 / 1.6 / — | 「BF16 rounding can change … occasionally the selected candidate」 | 「not guaranteed to be calibrated」 |
| Tev1-4B | 型の記述なし | **N**(2〜24 の選択肢から 1 文字を生成・temperature 0)。確率は vLLM の logprob で取る必要(推測) | 記載なし | 未評価と明記 | 9.3 / — / 2.6 | temperature 0 の推奨のみ | 未評価と明記 |
| kev-4b | noul・choice 1〜255・score 1〜255 | C(pointer head) | 検証済み 8,192 | 英語のみ(範囲外と明記) | 8.4 / — / 2.3。**カードの常駐 14.3 GB・「about 16 GB free」=そのままでは載らない** | fp32 との差 0.017 以内・答えの変化なし。順で答えが変わりうる | T=2.41・ECE 0.013〜0.101 |
| JevK5 | noul・choice・score | C(答えの文字の次トークンの logit の softmax・17 択以上は勝ち抜き) | 16,384(学習は 2,048) | 英語のみ | 8.4 / — / 2.3。カード「~9 GB for bf16」 | runtime 0.2.2/0.3.0 で 231 問が bit-identical | T=1.22・ECE 0.035 |
| OpenJev-4B(Alex) | noul(NLI の含意の確率) | **S**(候補ごとに「仮説」を作り 1 回ずつ・共通の前置きは 1 回) | 0.8B 版のみ 4k と記載 | 英語のみ | 9.1 / — / 2.5(NVFP4 版のフォルダあり) | 0/231 で bit-identical・逆順でも 0/231 | ECE の記載なし・較正なし |
| OpenJev-2B / 0.8B(Alex) | 同上 | S | 0.8B は 4k | 英語のみ | 4.4 / 1.7 | 同上 | 同上 |
| Open-Jev-2B | choice・noul・score | **S**(候補ごとにスカラーのヘッド・温度で正規化) | 候補ごとに 4,096(超えると拒否) | 記載なし | 3.8 / — / 1.0 | 記載なし(「No GPU inference was repeated」) | T=1.5188・test ECE 0.0116・OOD 0.1056 |
| decider-0.8b | choice 2〜255・score 2〜10・noul | C(答えの位置の文字の logit の softmax) | 記載なし(5〜8k の評価あり) | 「English only」 | 1.5(カード 1.4〜1.5 GB)/ — / — | 記載なし(R-83 で「バッチの形が同じなら決定的」) | in-task ECE 0.032・held-out 0.096・T=1.03 |
| kev-0.8b | 4b と同じ | C | 4b と同じ | 英語のみ | 1.5 / — / — | 4b と同じ形(数値は読んでいない) | 読んでいない(未確認・kev-0.8b のカード) |
| von | choice・score・noul | C([MASK] の印ごとに logit) | 8,192 | 「English only」 | — / 1.6(カード 1.5 GB fp32) | 1.2 から順に不変(1.1 は 49.5% 反転) | 入力ごとの温度・sealed ECE 0.107 |
| laya / typed | choice・score・noul | C(候補ごとの [MASK]) | 英語 512 / typed 1,024 | なし(多言語版を使えと明記) | 0.84 / — / — | 保証の記述なし | 出荷時は過信。温度の当て直しで ECE 0.466→0.081 |
| laya-multilingual | 同上 | C | 1,024(8,192 まで延長可) | ja の tag あり・日本語の値はカードになし(R-94: bench_ja choice 0.747・RPS 0.232) | 0.64 / — / — | 同上 | ECE 0.314→0.106 |
| minojev | choice・boolean・score | C(候補ごとの特徴量+集合の注意) | 記載なし | 英語のみ | 3.4 / — / 1.0 | 記載なし | 種ごとの温度・ECE 0.014(200 件) |
| JevForge-0.8B | choice・noul・score | **S**(候補ごとのスカラー→問いの中で softmax) | 32,768(学習の多くは 768 以下) | 英語の評価のみ | 1.7 / — / — | FP32 と BF16 の 9 問で argmax 一致(「not all-input proof」) | 温度 3 つ・ECE の記載なし |
| 即断 | choice・score・bool | C(文字列の state のみ) | 学習は平均 134・p95 237 トークン。400〜799 で精度が下がる | **ja のみ・bench_ja 300 件で choice 0.880** | — / 1.3(R-94: GPU 1.3 GB) | 推論は torch と MLX で argmax 一致。学習は再現しない | bool だけ T=2.070・choice と score は未較正 |
| saihai-310m | noul・choice・score(1〜64 問) | C | 候補 3,800(学習 4,096/2,048) | **ja/en・S1MB japanese-v1 の Task Avg 30.19**(Choice 40.99・Score 26.27)。英語 40.59 | 0.62 / 1.24 / — | 「Backend and precision changes can change probabilities」 | 「not guaranteed correctness rates」 |

dm_eval の場面は候補 13 個+「その他」(dm61 README §3)。上の上限はどれも 13 択を受ける(Tev1 は 24 まで・JevK5 は 16 まで 1 回)。文の長さは t300 の短い版で中央 516.5 字・t1000 で 1,724.5 字(同 §2)。即断は学習の長さを超える側に入る見込み(推測)。

## §4 除外の判定(C)

除外の 4 条件=(1) ライセンス不明か商用不可 (2) 本家 Jev の出力からの蒸留と明記 (3) 公式リポでない (4) safetensors で配布されていない。trust_remote_code は別の印(5070 の安全の規則 2 では候補から外す)。

| 名 | 判定 | 理由と出典 |
|---|---|---|
| bekko 400m/68m/17m | **除外** | (1) 重みのライセンス未定(#10)。加えて trc 要 |
| Tev1-4B / 0.8B | **除外** | (1)「release license … is being finalized」(#11)。0.8B は tag なし(#9) |
| kev-4b / kev-0.8b | **保留**(4) | ヘッドが head.pt(#9・#12)。4b は常駐 14.3 GB で 5070 にそのままでは載らない |
| Open-Jev-2B | **保留**(4) | package/checkpoint/head.pt(#9) |
| von | **保留**(4) | option_marker.pt(#9)。保守終了 |
| JevK5 / JevK5-2B | 候補 | 4 条件に当たらない。注=教師データの一部が GPT-6 Luna の出力(#13)。規約の及ぶ範囲は本書では判断しない |
| OpenJev 4B/2B/0.8B(Alex) | 候補 | MIT・使うフォルダは safetensors。注=test の分割を学習に入れたので公開ベンチの値は使えない(#14) |
| decider-0.8b | 候補 | 注=推論の読み口は GitHub のパッケージ(PyPI でない) |
| laya 系 3 本 | 候補 | 注=pip の laya が要る |
| minojev | 候補 | |
| JevForge-0.8B | 候補 | 注=GitHub のコード(28 本の .py が repo にある) |
| 即断 | 候補(既存の口 `SokudanScorer`) | |
| saihai-v1-310m | **trc の印** | auto_map と custom_code(#9・#22)。4 条件には当たらない |
| Vela-2.0-0.3B・Decision-2.0-Nox-4B | **trc の印** | auto_map(#9・#34)。Vela の tokenizer は Gemma の規約(#24) |
| d1-3B・d1-omni-600M | **trc の印**+(1) 条件つき | lfm1.0(R-94 §5-2=年商 1,000 万ドル以上の法人の商用は許諾外)。カード「load it with `trust_remote_code=True`」(#25) |
| Valen-4B | **trc の印** | auto_map(#9・#28) |
| Intern-Decision-4B | 候補(注) | Apache-2.0・safetensors。注=repo の inference.py を使う(trc ではないが同じくコードを動かす) |
| h2o-lightning-4b | 候補(注) | Apache-2.0・safetensors。注=「vLLM 0.30.0 plus 30 changed Python files」の改造版か、素の vLLM で片方向の読み(#27)。重み 9.3 GB で 5070 にほぼ一杯 |
| jiwo-4b / 0.8b | 候補(注) | Apache-2.0・safetensors。注=学習データ非公開(#29) |
| kirp/jpt-4b | **除外** | (1) cc-by-nc-4.0(#34) |
| isHeSatoshi/smalljev-semantic-v9 | **除外** | (1) ライセンスの tag なし・(4) .pt 2 本(#34) |
| openjev/openjev・StartLux・Torchcast・Vev | **除外** | (1) 非商用(#9・#6・#8) |
| TurinTech の圧縮版(GGUF) | **除外** | (3) 第三者の変換(#6)・(4) GGUF |
| JEV-27B・JEV-9B(autotrust) | **除外**(9B 以上) | (2) Jev 1.13 からの蒸留と明記(R-83・#6) |

(2) に当たる 4B 以下は読んだ範囲に無い。awesome-system-one(#8)は「no model entry states it was distilled from Jev」で、Jev の答えでローカルのモデルを学習させる道具(Jevstiller・jimothy)は「Applications」の側に載る。

## §5 S1MB の結果と awesome にある、ほかの 4B 以下(一次の検査は未)

**一次の検査の案(expedient・未リサーチ)**: 重みを取らずに `api/models/<repo>` の JSON だけで、(a) `license:` の tag が商用可の名か (b) `.pt`・`.bin`・`.gguf` が無いか (c) `auto_map`・`custom_code` が無いか (d) 言語の tag、を機械で見て落とす。本書の 37 本はこの形で読んだ(§1 #9)。カードを読むのは残ったものだけにする。5070 の準備の段で tools/ に置ける(書くかは親の判断)。

名前だけ確かめたもの(リポの名・一覧の記載のサイズとライセンス。中身は**未確認**。埋め方はそれぞれの `huggingface.co/api/models/<repo>` とカード)。

- awesome(#6〜#8)から: Strands Decider 2B(strands-labs・Apache-2.0 か記載なし=一覧で食い違い)・Standard One 3B(StandardThinking・Apache-2.0・Ministral 3)・Phocinae-Largha-150M-v1(Apache-2.0・英中)・OpenThai-SystemOne 0.8B(iapp・Apache-2.0・タイ語と英語)・Saina Helm 2 0.8B(記載なし)・NanoJev 0.6B(MIT)・agent-jev 0.6B(Apache-2.0)・jev-style 0.8B/2B(Apache-2.0)・PlayJev・OneJev 0.8B/4B(Apache-2.0)・jevos 1B(MIT・GGUF)・Lev 4B LoRA(記載なし)・RSI-Jev 4B・imajev 2b/4b(Apache-2.0)・NeoHorse-Jev-4B(Apache-2.0)・Wald-4B(Apache-2.0)・dwight-4b(Apache-2.0・営業の通話の英語のみ)・dohnuts 0.8B・julia-1 144M・WaterSheep・Jeva 4B・vegaml・Rizzo Flow 1.7B/4B・Anarkali 68M・open-jev-deberta-v3-large 434M(kotobalabs・Apache-2.0・英語・ヘッドは safetensors=#9)・GLiNER2.5-multi-Decide 287M(Apache-2.0・safetensors のみ・custom_code なし=#9)・OpenDecider-nano(Apache-2.0・safetensors のみ=#9)。
- S1MB の結果の枠(#3)から(名前で 4B 以下と推測): AnkitAI TinyJev-4B/0.6b・CountingSheep vev-4b(非商用=#8 の Vev)・FrontiersMind Lumma-fev-0.6b・Hanno-Labs bosun-v3.1-0.6b/1.7b・LMDHQ vision-jev-0.8b・LibertAIDAI deem-0.8-v1・Mapika decider-2b/4b/2b-vision・OmniJev OneJev1.5/1.6 の 0.8B・4B・PelaAI KnowLine 0.8B/2B/4B(Gen1〜5)・UserMoonlight intelif-qwen3-4b・abhishek085 spark-s1-4b-v6・alibiserikbay JevK5-Lite・apus-ailab APUS-OpenJev-v1-4B・caiovicentino1 Eikos-4B・carrtesy EXAONE-4.0-1.2B-JEV(EXAONE の基盤のライセンスは未確認)・crh225 plumb-4b・davidburhans gevva-e2b/e4b・dhtocks malkuth-2b/4b・evalengine decision-4b・everettjf ezjev-4b-s2・flymy-ai decision-2b-preview/4b-v1.1/4b-v1.2・franckverrot lev-350m・frontier-infra jebadiah-4b-v2・heman10x rlcd-modernbert-151m・jaredpalmer kev-0.5b/0.6b・jerichosiahaya Naluri-308M・kirp jpt-0.8b(4b は NC)・kpiya kas-4b・kshetrajna12 reflex-qwen3.5-4b-lora・mghafiri qwen3.5-0.8B-decision-model・mohamedlotfy50 sifr-0.8b-v3・mstrasser Jeff-Qwen3.5-0.8B/2B・Jeff-Gemma4-E2B・notnotsamuel LFM2.5-350M-RLCD(LFM の条件)・monotykamary LFM2.5-2.6B-RLCD(同)・pngwn system-one-qwen3.5-4b-scorer(v2b)・shgao rsi-jev-v5.0-vl-3b/v6.1-vl-4b・sthanika-ai sieve-2b・theaviv Lev1-3.7B・uneeverse unee-0.8b/2b・vllm-sr Decision-2.0 の Kai-0.6B/Eos-0.8B/Sol-2B・d3 系・wayfind metask-jev-4b-policy-mix。名前からサイズが読めない枠(needle3・DM-JEPA・Jeff-1・hopper・dinah-0・matilda-jev・verdict-small・XERON-0.1・certo・aplomb-1・this-that-model・jet・lavoir・amos-1-large・Manchego・superion_s1・mini-Jev・JADE・JEVision)も未確認。

## §6 (G) 案の基準=Qwen3-8B の logprob(D)

| 項目 | 内容 | 出典・等級 |
|---|---|---|
| 重み | `Qwen/Qwen3-8B-AWQ`。license:apache-2.0・AWQ 4 ビット・Qwen3ForCausalLM・safetensors 2 本(.pt/.bin/.py なし)・lastModified 2025-05-21・sha 4da05a8edb | #33・#9 ◎(R-123 §3 と一致) |
| 出力の確率 | `logprobs`「Number of log probabilities to return per output token … When set to -1, return all `vocab_size` log probabilities.」上限は `--max-logprobs` | #30 ◎ |
| 前置きの確率 | `prompt_logprobs`「Number of log probabilities to return per prompt token.」(候補の語を前置きの末尾に足して、その語の確率を読む形に使える) | #30 ◎ |
| 指定の語だけ | `logprob_token_ids`「Specific token IDs to return logprobs for. … useful for scoring tasks where you want to compare probabilities of specific label tokens.」最大 128 個(`MAX_LOGPROB_TOKEN_IDS = 128`)。前置き側は `prompt_logprob_token_ids` | #30 ◎(latest developer preview。0.28.0 にあるかは未確認) |
| 候補に縛る | `structured_outputs` の `choice`「the output will be exactly one of the choices」。サーバーは `extra_body={"structured_outputs": {"choice": [...]}}`。旧 `guided_choice` は v0.12.0 で削除 | #31 ◎。logprob と組むときの記述は無い |
| 決定論 | `VLLM_BATCH_INVARIANT=1`(beta)。対象は compute capability 8.0 以上。試験済みの一覧に「Qwen3 dense (… 8B, 4B-AWQ, 8B-AWQ)」 | #32 ◎。sm_120 は明記なし(R-123 §0 の 3 と同じ) |

dm_eval の `GScorer` は「1 トークン目の確率」の口(judge.py)。13 個の候補の番号(1〜13)の最初のトークンの確率を `logprob_token_ids` で取り、提示した候補の上で正規化すれば C の形になる(推測・番号が 2 桁になる 10〜13 は 1 トークン目が重なるので、番号の付け方を決める必要がある)。構造化の `choice` で縛ると確率は縛った後の分布になるかもしれない(推測・文書に記述なし)。基準には縛らない logprob を使う方が安全(推測)。

同じ形で、**標準の architectures の判断モデル**(decider-0.8b=Qwen3_5ForCausalLM・JevK5=Qwen3_5ForCausalLM・Tev1)も、作者の推論コードを使わず vLLM の logprob で「答えの文字の確率」を読める可能性がある(推測)。ただし作者のプロンプトの形と温度の値を写す必要がある(decider と JevK5 は Apache-2.0=出典を付ければ写せる・CLAUDE.md §2 の 4)。Qwen3.5 の構造が vLLM 0.28.0 で動くかは未確認。

## §7 9B 以上=クラウドで測る候補(E)

印はすべて「クラウド」。詳細は読んでいない(R-83・R-94 の値を引く)。

| 名 | パラメータ | ライセンス | 注 |
|---|---|---|---|
| Open-Jev-9B / 27B-v1.1(ZefanCai) | 7.94B / 25.64B(S1MB) | Apache-2.0 | ヘッドが head.pt(9B=#9)。(4) で保留 |
| kev-9b / kev-27b | 7.94B(S1MB)/ 27B | Apache-2.0 | head.pt(#9) |
| JevK5-9B | 9B | Apache-2.0 | 約 19 GB(#13) |
| Clef-flash / Clef | 9.4B / 27.4B | Apache-2.0 | R-83・R-94 |
| saihai-v1-8b | 8,590,200,832(API)・LlamaForCausalLM | Apache-2.0(llm-jp-4.1-8b-thinking) | **日本語・japanese-v1 Task Avg 49.77**。BF16 で約 17.2 GB。trc 要。GGUF 版あり(安全の規則の外) |
| pplx-decider-v1.1-27b / v1.2・flash | 27B / 4B flash(一覧の記載) | V1.1 は Apache-2.0 | flash 4B は重みの公開の有無が未確認 |
| Intern-Decision・Valen・h2o の 9B 以上・Decision-2.0-Lux-9B・Vela 9B | 9B 級 | Apache-2.0(一覧) | 未読 |
| JEV-27B・JEV-9B | 27B / 9B | Apache-2.0 | **除外**(Jev からの蒸留と明記) |

## §8 dm_eval の当て口へのつなぎ方(まとめ)

- 当て口の形は `Scorer.score(situation, candidates, *, text) -> 分布`(judge.py)。どの候補も `_score` の中で「text を state、候補の語を選択肢」にして分布を返せばよい。口だけの `_ModelPort` を 1 本ずつ足す形になる(推測)。
- **C の候補**(1 回で分布): decider・JevK5・kev・laya 系・von・minojev・即断・saihai・Vela・d1・Intern-Decision・h2o・jiwo。並びを変えた 4 通りの対照試験(dm61 README §5)がそのまま効く。
- **S の候補**(候補ごとに独立): Open-Jev-2B・JevForge・OpenJev(Alex)。作りの上で位置の偏りが出にくい(OpenJev は逆順で 0/231 を報告)。OpenJev は NLI なので、「この人は〇〇をする」の仮説の文をこちらで作る必要がある=**文面が設計者の指紋になる**(推測)。
- **N の候補**: Tev1(除外)。
- 厳密モード(`strict_check`・B14 の 32/32)は、作者が bit-identical を報告するもの(OpenJev・JevK5)から先に通る見込み(推測)。

## §空欄(14 件)

1. S1MB の順位表(#5)の 10 月の版と、日本語の部の順位(Space が動的で読めず。埋め方=Space の app のファイル一覧か `s1mb-result` の各枠の metadata.json)。
2. S1MB の結果の 218 枠のうち、§3 にないもののライセンス・配布の形(§5 の一次の検査で埋める)。
3. Tev1 の重みのライセンスがいつ決まるか(カードの更新を待つ)。
4. head.pt を `torch.load(weights_only=True)` で安全に読めるか、safetensors に変えてよいか(ライセンスの上は Apache-2.0。手順は親の判断)。
5. `logprob_token_ids` が vLLM 0.28.0 にあるか(0.28.0 の docs の SamplingParams の頁)。
6. Qwen3.5 系(Qwen3_5ForCausalLM・DeltaNet)の判断モデルを vLLM 0.28.0 で読めるか。
7. Intern-Decision・jiwo・Valen・h2o の学習データの出自(Intern は arXiv 2610.22131 が出典とカードにある=未読)。
8. Valen の対応言語(カードに記載なし)。Vela 2.0 と d1 の日本語の評価値(カードに無い)。
9. kev-0.8b・Tev1-0.8B・bekko 68m/17m のカードの個別の数値(本書は 4b・4B・400m のカードの記述を当てた)。
10. 日本語の字とトークンの比(tokenizer ごと。dm61 README §2 の空欄と同じ)。
11. JevK5 の教師データ(GPT-6 Luna の出力)に OpenAI の規約がどう及ぶか(本書では判断しない)。
12. 2 つの awesome-system-one のどちらを指示書が指すか。
13. EXAONE-4.0-1.2B-JEV の基盤のライセンス。
14. 5070 で 4B 級を 16 ビットで載せたときの実測(重みの取得が要る=段 1 の 3 の作業)。

## §親に聞きたいこと

1. **trust_remote_code の扱い**。規則 2 のとおり外すと、日本語の候補は即断だけになる(saihai-310m・Vela・d1 が外れる)。「repo の .py を親が読み、版(sha)を固定してから許す」例外を作るか。saihai-310m は S1MB の日本語の部で測られた唯一の 4B 以下。
2. **独自コードの扱い**。trc でなくても、ほぼ全部の候補が作者の pip パッケージか GitHub のコードを要る(decider・kev・Open-Jev・JevForge は GitHub からの導入=「git clone 禁止」に当たる)。代わりに、Apache/MIT の読み口のコードを読んで dm_eval の当て口の中に出典つきで書き直す道がある(§6 の末尾)。どちらにするか。
3. **.pt のヘッド**(kev・Open-Jev・von)を除外のままにするか、safetensors に変える手順を許すか。
4. **ライセンスの受け入れ**。JevK5(GPT-6 Luna の出力を含む学習)・d1(LFM の年商の条件)・Vela(Gemma の tokenizer の規約)・laya-typed-decisions(ラベルの元が不明)を候補に残すか。
5. **語の重なり**。指示書の Choice/Score/Noul(接続形)は Jev の型の名(choice・score=段階・noul=はい/いいえ)と字が同じで意味が違う。表と dm_eval の欄で別の語にするか(案: 一括・候補ごと・それ以外)。
6. 一覧の固定。awesome-system-one は yanng981 版と andyrewlee 版の 2 つがある。両方を読み直しの対象にしてよいか。S1MB はブログ(23)ではなく結果のデータセット(218)を正にするか。
7. **日本語の無い候補をどうするか**。4B 以下の大半は英語のみ。dm_eval の 340 場面は日本語。(a) 日本語のまま流す (b) 英訳した場面も流して差を見る (c) 英語のみの候補は比較の参照に留める、のどれにするか。(b) は翻訳の文面が指紋になる。
8. §5 の一次の検査(API の JSON だけで落とす)を tools/ に置くか。置くなら、どの条件で落とすかを親が先に決める。

## 親の一次確認(第340・2026-11-01・Fable 5.1)

- `hotchpotch/s1mb-result`(親が HF の API の JSON とカードを実読): lastModified 2026-10-30T00:02:43Z・license other(source-dependent-results-terms)・カードに「Both english-v1 and japanese-v1 measurements belong in this Dataset」「54 measurements across two model folders, with 27 benchmarks / 8,067 judgments per model」=japanese-v1 が 27 課題・2 モデルの枠=一致(◎)。**218 のモデルの枠**は一覧が長く(2.7 MB)親は数えていない(筆者の読み=○)。japanese-v1 で測られた 2 モデルの名は、カードが「PelaAI/KnowLine-4B-Gen4 と convaiinnovations/laya-multilingual の評価は残す(JDMB-v1 の旧結果は消した)」と書くのに対し本文は saihai の 2 枠とする=**要確認**(フォルダの一覧で親が確かめる)。
- `AlexWortega/openjev`(カードを親が実読): MIT・v5 の 4B/2B/0.8B(Qwen3.5 の NLI の cross-encoder=`Qwen3_5ForSequenceClassification`・3 ラベル)・`OpenJev.decide` が選択肢ごとに 1 回ずつ前向きで entailment を正規化(`normalized_entailment_v1`)・safetensors のタグあり・trust_remote_code の記述なし(35B だけ helper の .py)・Jev からの蒸留の記述なし(「No JevBench item … was ever in the mixture」・MMLU 等の test split を学習に含む)=本文 §3 の判定(候補・Score・NLI の仮説文が要る)と一致(◎)。
- 等級: 37 本のカードのうち親が原文で確かめたのは上の 2 つ(+R-123 で `Qwen/Qwen3-8B-AWQ`)。残りは筆者の読み(カードの抜き出しは小さなモデル経由=写し検査を要する)。vLLM の `logprob_token_ids`・`structured_outputs` の `choice` は筆者の◎のまま。
- 親の判断(ユーザーへ・PENDING §1-1「判断モデルの候補の採否」): 問い 1(trust_remote_code の例外=.py を親が読み sha を固定したら許す)=親案 許す(日本語の候補が即断だけになるのを避ける。安全の規則 2 の例外として台帳に書く)。問い 2(作者のコードを git clone せず、Apache/MIT の読み口を出典つきで dm_eval に書き直す)=親案 そのとおり。問い 3(`.pt` のヘッドを safetensors へ変換)=親案 変換の手順(torch.load は weights_only=True)を記録して許す。問い 4(JevK5=Luna の出力を含む・d1=LFM の年商の条件・Vela=Gemma の tokenizer)=ユーザーの判断。問い 6(一覧の正)=S1MB の結果 218 と awesome 2 本の両方を読み、4B 以下を全部候補に(11-01g のとおり)。問い 7(英語のみの候補に日本語の場面)=流して破綻率の列で見る。問い 8(API の JSON で落とす一次の検査)=tools/ に置く(段 1)。

## 親の一次確認の追記(第341・2026-11-02・Fable 5.1・[指示書 11-02 返事その 2](../design/prompt-2026-11-02-reply2.md) §1 #2 の付け足し)

- **§0 の 2「japanese-v1 で測られているのは saihai(310M と 8B)の 2 本だけ」はカードと食い違う。** `hotchpotch/s1mb-result` のカード(親が 2026-11-02 に実読・最新 commit「Remove historical JDMB measurements pending fresh S1MB evaluations」)の「Japanese results」の節は、日本語の測定を `hotchpotch/S1MB-japanese-v1` に対して公開するとし、**「The S1MB evaluations for PelaAI/KnowLine-4B-Gen4 and convaiinnovations/laya-multilingual are retained … 54 measurements across two model folders, with 27 benchmarks / 8,067 judgments per model」**と書く。カードに saihai の語は無い。
- 一方 `hotchpotch__saihai-v1-310m/` の tree(親が実読)には 165 本の測定ファイルがあり、うち日本語の課題名(jnli・jsts・jcommonsenseqa・jamp・janli・kuci・jmmlu-japan・gpqa-ja ほか 27 本程度)のファイルが入る。ただし道筋に `japanese-v1` の印は無く、同フォルダの `metadata.json` は学習データの露出の登録(dataset `hotchpotch/saihai-v1-310m-dataset`・`relationship: same_source_family`)で、評価の版や日付の欄は無い。
- **判定**: 一覧の正(11-02r §1 #2 ⑤=R-125 の表)を決める前提として、**japanese-v1 の公式の 2 本=KnowLine-4B-Gen4 と laya-multilingual(カードの文)**とする。saihai の日本語の測定は「版の印の無いファイル(JDMB-v1 の歴史の可能性・推測)」として扱い、表の saihai の japanese-v1 Task Avg(30.19・49.77)は**出どころを要確認**の印に落とす。確かめるには `viewer-summary.json`(19 MB・LFS)を読む(次の着手のときに取得日つきで)。
