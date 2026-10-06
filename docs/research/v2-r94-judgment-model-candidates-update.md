# R-94 答申: 判断モデルの候補の再調査(R-83 の更新・日本語・人の割合との一致・連続した量・2 段の形)

<!-- hdr:v1 -->
- **分野**: 自然言語処理・機械学習 #27 / ソフトウェア工学 #29 / 研究倫理・情報法 #31 / 認知科学 #12 | **重要度**: P1(指示書 [v2-wallbounce-decisions-2026-10-06](../design/v2-wallbounce-decisions-2026-10-06.md) §7 の 5・§3。判断モデルの草案 DM1・DM3・DM10・DM13・段 J1)
- **一次確認**: **B**(サブ実読。出典 38 本 = ○ 33・△ 4・× 1・空欄 17 件は §空欄)・親検収 済(第323・2026-10-06: 即断のモデルカードの値=Apache-2.0・314,614,274 パラメータ・bench_ja 300 件・choice 0.880・RPS 0.075・AUROC 0.844・371 ms(285K)・第 1 選択肢 5/300・学習データは単一の生成モデルの合成データ、を親が本文で逐語確認。6.6 問/秒は GitHub の latency.md(○)。手元の GPU RTX 5070 12,227 MiB を親も nvidia-smi で確認。ChaosNLI の JSD・S1MB の順位・d1 と LFM の規約の逐語は親は未確認=写し検査は使うときに))
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 作成 2026-10-06・リサーチ役サブ(Opus 5.5)。子サブ未起動・Web は読むだけ(モデルカードと README は curl の出力を読み、作業用の一時領域にだけ置いた。リポには置いていない)。重みの取得・pip install・API の登録と呼び出しはしていない。`data/research_cache/r94/` への取得物はなし。コミットなし・台帳/設計書/src 未編集。
> 既存答申との関係: 本家 Jev の規約(MCA §2.3(b) の蒸留禁止・レート上限)と、Clef・Clef-flash・JEV-27B・OpenJev(openjev/openjev)・decider・Kev・Laya・pplx-decider の基本情報と Decision Index・JevBench は [R-83](v2-r83-jev-type-decision-models.md) §1〜§3 を正とし、ここでは繰り返さない。本家の仕様と弱点は [R-40](v2-r40-jev-details-research.md)、閉じた出力の判断器の系譜は [R-38](v2-r38-closed-output-judges-research.md)、判断の割合は [R-39](v2-r39-judgment-share-research.md)、熟考の割合と人らしさは [R-88](v2-r88-llm-humanlikeness-deliberation-vision.md)、razorback16 版の Open-Jev は [v2-openjev-note.md](v2-openjev-note.md)、本家の概要は [v2-jev-system-one-note.md](v2-jev-system-one-note.md)。本書は **R-83(2026-10-03)以後の差分**(新しい候補・日本語の実測・人の票との一致の値・新しい規約)を中心に書く。
> 対象の草案: [判断モデルの設計ラウンドの草案](../design/v2-decision-model-design-round-draft.md) v1.1(DM1〜DM13・段 J0〜J5)。
> 時点の書き方: 各データの「時点」はモデルカードの更新日か記事の日付。世界の基準の日付(未決・候補は W13 の実日 2026-07-28 の週)より後のものばかりだが、判断モデルは世界の中のデータではなく道具なので、時点の差は「モデルの知識の締切」(§5-3)にだけ効く。

## 結論(5 行)

1. **日本語で実測された判断モデルが初めて見つかった**。即断(sokudan-ja-310m・Apache-2.0・3.1 億・ModernBERT-ja 基盤)は、日本語の業務文 300 件で選択の正解率 0.880・段階の RPS 0.075・真偽の AUROC 0.844(作者の測定)。CPU(Core Ultra 9 285K)で 3 問 1 件 中央値 371 ms・batch 32 で 6.6 問/秒。学習スクリプトも公開されている。ただし学習データは単一の生成モデルの合成データで、文は平均 134 トークンと短い。Laya の多言語版は同じ 300 件で段階の第 1 水準を 1 度も選ばなかった(0/300)。
2. **人の票の割合との一致を測った判断モデルの値が 1 系統だけある**。OpenDecider の ChaosNLI(1 問 100 人の票)で、人の票の分布との JSD は本家 Jev 0.148・Laya 0.174・OpenDecider-small 0.040・large-td 0.030(作者の測定)。教師は公開ライセンスの LLM 2 本(Qwen3-235B・DeepSeek V4.1 Flash)を温度で較正してから平均したもの。人どうしのばらつき(フロア)は出典に無い(空欄)。英語のみ。
3. **「見たことのない課題で順位が大きく変わる」事実は 2 つの出どころで確かめた**。S1MB(2026-09-30・23 モデル)では、bekko-400m が全体で 2 位なのに汎化の 6 ベンチでは 12 位。作者は学習と評価で 77 の部分集合の名前が重なると書いている。GLiNER2.5-Decide は自社の 17 課題で 1 位(60.2%)だが、Decision Index 0.2.1 の補正後の点は 11.21 で、Kev-9B(38.48)より低い。公開の点数で選ばず、v2 の封印行で測る必要がある(R-83 §3-2 と同じ帰結)。
4. **Liquid AI の d1 は API の規約が v2 の使い方とぶつかる**。2026-09-30 改訂の規約 §6 は、送った内容と出力を Liquid AI が「学習・微調整・評価・試験」に使う許諾を含む。出力で他のモデルを学習させることも禁じている。無料枠(`d1:free`)は文字だけ。比較の腕として使えるのは公開の場面だけで、封印行は送れない。手元で動く土台の LFM2 系は重みが公開されているが、LFM Open License v1.0 は年間売上 1,000 万ドル以上の法人の商用利用を許していない。日本語版 LFM2.5-1.2B-JP-202606 は日本語のベンチマークを公表している。ただし判断の土台としての日本語のゼロショット値は低い(JNLI 17.15%・第三者の測定)。
5. **段階の語で量を決める形(DM13 (a))には位置の偏りが付きまとう**。即断・Laya・Kev・Lev で、段階の問いの第 1 水準が選ばれにくい偏りが報告されている。v2 では、段階の分布がそのまま人の分布になるので、J1 で「全選択肢を同じ文にした対照」と「順の逆転」の試験が必要になる(案)。J1 に載せる順位の案は、①即断(日本語・CPU・見張りの候補)②Clef-flash(Jev 互換・画像・GPU 後)③Open-Jev-9B か Kev-9B(学習コードがあり、分布に合わせる LoRA の土台)④OpenDecider(人の票との一致の参照)。手元の機械では、どれもインストールと重みの取得が要るので測っていない(§6・先に聞く)。

## §0 出典の表

印: **○** 本文を自分で読んだ(カードや README は全文か該当の節)/ **△** 抄録・検索要約・二次資料のみ / **×** 読めなかった

| # | 著者・機関 | 時点 | 題名 | URL | 印 | 何に使ったか |
|---|---|---|---|---|---|---|
| 1 | Yuichi Tateno(hotchpotch) | 2026-09-30 | S1MB: comparing System One Decision Models across 100+ benchmarks | https://huggingface.co/blog/hotchpotch/system-one-mosaic-benchmark | ○ | 全体と汎化の 2 つの表・注意書き |
| 2 | GeneLab | 2026-09-29 更新(v0.2.1) | `GeneLab/sokudan-ja-310m` モデルカード | https://huggingface.co/GeneLab/sokudan-ja-310m | ○ | 即断の精度・較正・位置の偏り・限界 |
| 3 | hiroki-abe-58 | 2026-09-28 | sokudan `docs/latency.md` | https://github.com/hiroki-abe-58/sokudan/blob/main/docs/latency.md | ○ | CPU と GPU の速さ |
| 4 | GeneLab_999 | 2026-10-01 | Decision models are English-first. I measured them in Japanese, then built one. | https://dev.to/genelab_999/decision-models-are-english-first-i-measured-them-in-japanese-then-built-one-1p12 | ○ | Laya・Lev の日本語の値・typed-decisions-ja |
| 5 | hiroki-abe-58 | 2026-10-06 読み | sokudan リポジトリのファイル一覧(GitHub API) | https://github.com/hiroki-abe-58/sokudan | ○ | 学習スクリプトの有無(`scripts/train.py` ほか)のみ |
| 6 | Fastino | 2026-09-28 更新 | `fastino/GLiNER2.5-Decide` モデルカード | https://huggingface.co/fastino/GLiNER2.5-Decide | ○ | 出力の形・自社の 17 課題の表 |
| 7 | Fastino(Mary Newhauser) | 2026-09-24 | GLiNER2.5-Decide: An Open-Weight Model for Structured Decision Making | https://fastino.ai/blog/gliner-2-5-decide-open-weight-decision-model | ○ | CPU の遅延・LoRA・制約つきの同時の判断 |
| 8 | Fastino | 2026-09-28 更新 | `fastino/GLiNER2.5-multi-Decide` モデルカード | https://huggingface.co/fastino/GLiNER2.5-multi-Decide | ○ | 多言語版の規模・ライセンス(該当の行のみ) |
| 9 | Manjunath Janardhan | 2026-10 | `manjunathshiva/opendecider-medium-td` モデルカード | https://huggingface.co/manjunathshiva/opendecider-medium-td | ○ | ChaosNLI の JSD・ECE・教師・学習 |
| 10 | 同 | 2026-10-05 更新 | `manjunathshiva/opendecider-nano` モデルカード | https://huggingface.co/manjunathshiva/opendecider-nano | ○ | CPU の遅延・メモリ |
| 11 | 同 | 2026-10 | `manjunathshiva/opendecider-small` モデルカード | https://huggingface.co/manjunathshiva/opendecider-small | ○ | ChaosNLI の JSD・メモリ・GGUF |
| 12 | LocalLLaMA | 2026-10 読み | `LocalLLaMA/typed-decisions` データセットカード | https://huggingface.co/datasets/LocalLLaMA/typed-decisions | ○ | d1 の値・依頼の形で値が変わる記録(先頭の表まで) |
| 13 | hotchpotch | 2026-09-30 更新 | `hotchpotch/bekko-system-one-v0-400m` モデルカード | https://huggingface.co/hotchpotch/bekko-system-one-v0-400m | ○ | ライセンス未定・汎化の限界 |
| 14 | Zefan Cai | 2026-09-20 | `ZefanCai/Open-Jev-9B` モデルカード | https://huggingface.co/ZefanCai/Open-Jev-9B | ○ | 学習・評価・ライセンス |
| 15 | 同 | 2026-09 | `ZefanCai/Open-Jev-27B-v1.1` モデルカード | https://huggingface.co/ZefanCai/Open-Jev-27B-v1.1 | ○ | 学習の行数・重なりの検査(該当の節) |
| 16 | 同 | 2026-09 | `ZefanCai/Open-Jev` データセットカード | https://huggingface.co/datasets/ZefanCai/Open-Jev | ○ | 学習データの中身(Jev の予測ではないとの記述) |
| 17 | 同 | 2026-10-06 読み | Open-Jev README(GitHub) | https://github.com/Zefan-Cai/Open-Jev | ○ | TypeSafe との関係・コードの MIT(該当の段落) |
| 18 | Alex Wortega | 2026-10-01 更新 | `AlexWortega/openjev` モデルカード | https://huggingface.co/AlexWortega/openjev | ○ | MIT・Qwen3.5-4B・順に依存しない作り(該当の段落) |
| 19 | Cloudflare | 2026-10-01 更新 | `Cloudflare/clef-flash` モデルカード(R-83 #6 の読み直し) | https://huggingface.co/Cloudflare/clef-flash | ○ | Jev の API と互換の明記・入力上限・評価の表 |
| 20 | Hugging Face API | 2026-10-06 読み | `Cloudflare/clef`・`clef-flash` のメタデータ | https://huggingface.co/api/models/Cloudflare/clef | ○ | パラメータ数(27,356,728,560・9,409,813,744) |
| 21 | Jared Palmer | 2026-09-30(v2) | `jaredpalmer/kev-9b` モデルカード | https://huggingface.co/jaredpalmer/kev-9b | ○ | 封印した評価・言語・常駐メモリ(該当の節) |
| 22 | Convai Innovations | 2026-10 読み | `convaiinnovations/laya` モデルカード | https://huggingface.co/convaiinnovations/laya | ○ | 多言語版の構成・RLCD の説明・限界(該当の節) |
| 23 | Perplexity | 2026-10 読み | `perplexity-ai/pplx-decider-v1-27b` モデルカード | https://huggingface.co/perplexity-ai/pplx-decider-v1-27b | ○ | 全文(約 49 GiB・学習データの記載なし) |
| 24 | argos1111 | 2026-09-19 | `argos1111/modernbert-ja-310m-jev` モデルカード | https://huggingface.co/argos1111/modernbert-ja-310m-jev | ○ | 日本語の第 2 の候補・LFM2.5-1.2B のゼロショット値 |
| 25 | mlboydaisuke | 2026-10-02 | `ModernBERT-Ja-310M-Decision-LiteRT`(HF API のメタデータのみ) | https://huggingface.co/mlboydaisuke/ModernBERT-Ja-310M-Decision-LiteRT | △ | #24 の派生であることとライセンスだけ |
| 26 | Liquid AI | 2026-10-06 読み | Decision Models(docs) | https://docs.liquid.ai/lfm/models/decision-models | ○ | d1 の 3 型・`d1:free` は文字だけ・画像のトークン |
| 27 | Liquid AI | 2026-10-05 | Introducing d1: The most capable decision model, now with vision | https://www.liquid.ai/blog/d1-decision-model | ○ | 遅延 200〜300 ms・単価・重みの予定 |
| 28 | Liquid AI | Last updated SEP 30, 2026 | Terms of Service | https://www.liquid.ai/terms-conditions | ○ | §6 の学習への利用の許諾・出力で他のモデルを学習させる禁止 |
| 29 | OpenRouter | 2026-10-06 読み | Liquid: d1 | https://openrouter.ai/liquid/d1 | ○ | 単価と文脈長(FAQ の段落) |
| 30 | Liquid AI | 2025〜2026 | `LiquidAI/LFM2-1.2B` モデルカード | https://huggingface.co/LiquidAI/LFM2-1.2B | ○ | 対応言語・学習の構成・LoRA の手順 |
| 31 | Liquid AI | 同上 | LFM Open License v1.0(同リポの LICENSE) | https://huggingface.co/LiquidAI/LFM2-1.2B/blob/main/LICENSE | ○ | 定義(Threshold)と §5 |
| 32 | Liquid AI | 2026-05-26 | `LiquidAI/LFM2.5-1.2B-JP-202606` モデルカード | https://huggingface.co/LiquidAI/LFM2.5-1.2B-JP-202606 | ○ | 日本語のベンチマークの表・知識の締切 |
| 33 | Hugging Face API | 2026-10-06 読み | LiquidAI の公開モデルの一覧(178 件) | https://huggingface.co/LiquidAI | ○ | 日本語版と LFM2.5 の系統の有無と日付 |
| 34 | multimodalart ほか | 生成 2026-09-28 | Jev Decision Index 0.2.1 `data/index.json`(R-83 #8 の読み直し) | https://huggingface.co/spaces/multimodalart/jev-decision-index | ○ | GLiNER・LFM2.5-RLCD・Kev・Laya の補正後の点と ECE |
| 35 | Rafe & Das | 2026-09-29 | Benchmarking System One decision models against trained classifiers and language models for automated decision gates(arXiv:2610.00346) | https://arxiv.org/abs/2610.00346 | △ | 抄録(はい/いいえを入れ替えると Jev が 100 問あたり 50.5 問で答えを変える) |
| 36 | (著者は検索要約のみ) | 2026-09 | Evaluating System One Models for Agent Security Decisions(arXiv:2609.33401) | https://arxiv.org/abs/2609.33401v1 | △ | 検索要約のみ(精度と較正と方針を一緒に評価すべき、という結論) |
| 37 | MarkTechPost・DataNorth・AlphaSignal ほか | 2026-09-29〜10 | d1 の報道 | https://www.marktechpost.com/2026/09/29/liquid-ai-releases-d1-a-decision-model-that-returns-calibrated-probabilities-with-zero-output-tokens/ | △ | 検索要約のみ(d1 の多言語の主張・重み非公開) |
| 38 | Liquid AI(X の投稿) | 2026-09-29 | d1 の発表の投稿 | (検索要約のみ) | × | 「multilingual evals で勝つ」の原文は読めず |

R-83 の出典(TypeSafe の MCA・models.md・Clef のブログ・Kev と decider の README・JevBench など)は R-83 の印のまま引く。

## §1 R-83 からの変化(要約)

| 項目 | R-83(2026-10-03) | 今回(2026-10-06) | 出典 |
|---|---|---|---|
| 日本語の評価 | OpenJev の 4 言語の合計だけ | **日本語専用の判断モデルが 2 つ**(即断・argos1111)。日本語の評価セット bench_ja(300 件)と typed-decisions の日本語訳(1,600 件)が公開。Laya 多言語版と Lev の日本語の値が出た | #2・#4・#24 |
| 人の票の割合との一致 | 判断モデルでの測定は空欄 | **OpenDecider が ChaosNLI の JSD を 7 系統で報告**(英語) | #9・#11 |
| 新しい候補 | 10 系統 | GLiNER2.5-Decide(Fastino)・OpenDecider・bekko-system-one・Open-Jev(ZefanCai)・openjev(AlexWortega)・Lev・d1(Liquid AI)・LFM2.5-RLCD(第三者)。名前が同じ「Open-Jev」は少なくとも 4 つある(§2-2) | #1・#6・#9・#13・#14・#18・#27・#34 |
| 見たことのない課題での順位 | decider-4b の公開 43 対 封印 19 | S1MB の汎化の表と、GLiNER の自社評価と Decision Index の食い違い(§3) | #1・#7・#34 |
| Clef | Jev の API との互換は R-83 に記載なし | カードに「The Clef-Flash API is fully compatible with Jev and SystemOne.」。入力の上限は既定 16,384 トークン | #19 |
| API 型の比較の腕 | 本家 Jev のみ | d1(Liquid AI)。規約 §6 で送った内容の学習への利用を許諾させる | #26〜#28 |

## §2 候補ごとの表

### 2-1 主な表(公開の形・規模・入出力・日本語・追加学習・較正・速さ・規約)

空欄は「カードや README に記載が無い」の意味。数値はすべて作者の自己測定で、条件(機械・問いの数・評価セット)を併記する。

| 候補 | 公開の形・ライセンス(時点) | 規模・必要なメモリ | 入力 | 出力の形 | 日本語の精度 | 人の行動データでの追加学習・LoRA | 確率の合い方(較正) | 手元の機械での速さ(公表値) | 規約の注意 |
|---|---|---|---|---|---|---|---|---|---|
| **即断 sokudan-ja-310m v0.2.1** | 重み・コード Apache-2.0。基盤 sbintuitions/modernbert-ja-310m(MIT)。評価データ CC BY 4.0(2026-09-29) | 314,614,274 パラメータ。GPU で 1.3 GB(#4) | 日本語の文字列(dict は `key: value` に直されて出力が変わる) | choice の確率・score(累積リンクの順序ヘッド・水準の数は依頼ごと)・bool の確率 | **bench_ja 300 件: choice 0.880・score RPS 0.075・score acc 0.817・bool AUROC 0.844**(多数決 0.380・0.197)。typed-decisions-ja のゼロショット 0.424(ラベルの事前 0.483 より下) | 学習スクリプトあり(`scripts/train.py`・`distill_train.py` ほか)。全体の微調整(LoRA の記述なし)。8 本の重みの平均(model soup) | bool だけ温度 T=2.070(ECE 0.181→0.105)。choice と score は未較正(温度で RPS が悪化)。P(top1)≥0.99 の 224 件中 14 件(6.25%)が誤答。bool は true を過少に予測(平均 0.133・正例率 0.297) | CPU(Core Ultra 9 285K・24 スレッド): 3 問 1 件 中央値 371 ms・p95 583 ms・batch 32 で 6.6 問/秒。RTX 5090: 22.8 ms・259 問/秒。M1 Max の MLX fp16 で 1 問 10.2〜10.4 ms | 作者は Jev を一度も呼んでいない(MCA §2.3(b) のため)と明記 |
| **modernbert-ja-310m-jev**(argos1111) | **CC BY-SA 4.0**(2026-09-19)。学習データの JGLUE が CC BY-SA | 315,203,329 パラメータ | 「質問: … 状況: …」と候補の対 | 候補ごとに 1 つのスコア → softmax で choice・score・noul | JGLUE test: JNLI 92.62%・JCommonsenseQA 92.40%(train で学習済み)。学習に無い課題: livedoor 9 分類 35.6%・JMMLU 34.8%(LFM2.5-1.2B のゼロショットは 46.8%・43.6%) | 変換コードあり(jev_local) | 空欄 | 空欄(R9700 で API 経由の計測のみ) | 継承の条件(SA)が派生物に及ぶ。義務の範囲は本書では判断しない |
| **Clef-flash / Clef** | Apache-2.0(R-83)。カードに Jev の API と完全互換と明記(2026-10-01) | 9,409,813,744 / 27,356,728,560 パラメータ(HF API)。H200 1 枚で試験と記載 | 文字・JSON・画像・動画。既定の上限 16,384 トークン | 選択肢ごとに 1 つのロジット(choice・score・noul)。score は期待値つき | **空欄**(R-83 §8 の 7 のまま) | 重みは Apache-2.0。手順は公開なし | 空欄(R-83) | 空欄(遅延の中央値 38.8 ms / 209.3 ms のみ・R-83) | Jev の出力の使用の記述なし(R-83 §2-2) |
| **Open-Jev-9B**(ZefanCai) | LoRA とヘッドは Apache-2.0、コードは MIT。基盤 Qwen3.5-9B は別に取得(2026-09-20) | 基盤 9B+LoRA r8+スカラーのヘッド。GPU 必要(量は記載なし) | 文字・JSON。候補ごとに 4,096 トークンまで(超えると拒否) | 候補ごとに独立に採点 → choice の分布・noul の確率・score の分布と期待値 | 空欄(学習データは英・中・トルコ語の合成。日本語の評価なし) | `.[train]` で学習コードあり。LoRA r8 | 温度 1.897(512 行で当てた)。自前の test で ECE 0.0077・OOD で 0.0374(合成の課題) | 空欄 | 学習データは「TypeSafe/Jev の学習データやモデルの予測ではない」と明記(#16) |
| **openjev**(AlexWortega) | MIT。基盤 Qwen3.5-4B(2026-10-01) | 4B・2B・0.8B | 文字(画像の記載あり) | 選択肢ごとに 1 回の前向き計算で「選択肢の順に依存しない」と明記 | 空欄(英語) | 空欄 | 空欄 | 空欄 | 学習データに JevBench の問題は入っていないと記載 |
| **Kev-9B v2**(Kev 1.0) | Apache-2.0(2026-09-30) | 9.65B(Decision Index)。CUDA で常駐約 22 GB | 文字。65,536 トークンまで受け付け、検証済みは 8,192 | noul・choice・score(R-83) | **「languages other than English」は範囲外と明記** | 手順と学習コードあり(R-83)。LoRA r16 | 温度 T=2.19。封印した test で ECE 0.034 | 空欄 | 「No output of Jev … was used.」 |
| **OpenDecider**(nano・small・small-td・medium-td・large-td) | Apache-2.0(2026-09-27〜10-05) | nano 約 4 億(Ettin エンコーダ)・small 4B LoRA・medium-td 30B-A3B(約 61 GB)・large-td 80B-A3B(約 160 GB) | 文字・JSON | choice・score・noul の全選択肢の確率 | **英語のみ**と明記 | 教師の蒸留+短い微調整の手順を記載。LoRA r16(small 以上) | ECE(200 問の一般の判断): nano 0.092・small 0.087・large-td 0.083・Jev 0.164。**ChaosNLI の JSD は §4** | nano: CPU のみで 1 問 0.1〜0.7 s(約 2 GB)・L40S 16 ms。small: CPU は「slow・not recommended」(約 17 GB) | 教師は Qwen3-235B-A22B(Apache-2.0)と DeepSeek V4.1 Flash(MIT)。Claude と GPT の出力は不使用と明記 |
| **GLiNER2.5-Decide / multi-Decide**(Fastino) | Apache-2.0(2026-09-24) | 340M(英語・DeBERTa-v3-large)/ 287M(多言語) | 文字+問いの型の一覧。規則(含意・排他・個数・順序の範囲)も書ける | 問いごとの確率と確信度+全体が規則を満たすか。順序の尺度は "0"〜"10" のラベルで | 多言語版は「multilingual」とだけ。日本語の値は空欄 | 全体の微調整と LoRA に対応と明記 | 空欄(Decision Index の ECE は 0.0884・多言語版 0.2538) | 48 vCPU の Xeon で 64 トークン p50 167.3 ms・V100 38.3 ms | 学習データの記載なし(空欄) |
| **Laya / laya-multilingual** | Apache-2.0(R-83) | 421M / 322M(mmBERT-base) | 文字。多言語版は 8,192 トークンまで | choice・score・noul | **sokudan の作者の測定(bench_ja)**: choice 0.747・score RPS 0.232(多数決 0.197 より悪い)・bool AUROC 0.523。段階の第 1 水準を 300 件中 0 回。typed-decisions-ja: 0.348 | Kaggle の微調整のノートあり | 温度の後 ECE 0.081(自前)。生の ECE 0.213 | CPU で 193〜464 ms(preload 時) | 「RLCD」で学習と自称(本家の RLCD とは別物。#22) |
| **bekko-system-one v0**(17M・68M・400M) | コードは MIT(GitHub)。**重みのライセンスは未定**(カードに「This card does not assign a license.」) | 17M・68M・400M | 英語 | noul・choice・score | 空欄(英語のみ) | 学習ツールあり | 「not guaranteed to be calibrated」 | RTX 5090 で 2 択 1.38〜5.11 ms。17M と 68M はブラウザの CPU で動く | 重みのライセンスが決まるまで採用できない |
| **pplx-decider-v1-27b** | Apache-2.0(R-83) | 約 49 GiB の重み | 文字・画像 | choice・noul | 空欄(Belebele 94.00% のみ) | 案内なし | 空欄(Decision Index の ECE 0.0178) | 空欄 | 学習データの記載なし |
| **OpenJev**(openjev/openjev) | 重み CC BY-NC 4.0(R-83) | | | | 4 言語の合計のみ(R-83) | | | | 非商用。採らない(R-83・DM1) |
| **JEV-27B / -VL** | | | | | | | | | Jev の出力で学習と自己申告。採らない(R-83・DM1) |
| **d1**(Liquid AI) | **重み非公開・API のみ**。`d1`(有料・画像可)と `d1:free`(文字のみ)。重みは「upcoming models」で公開予定と記載(2026-10-05) | 非公表 | 文字・JSON・画像(有料版のみ) | noul・choice・score(Jev と同じ形・`/decisions/v1/systemone`) | 空欄(多言語で勝つという主張は検索要約のみ・#38 ×) | 不可(微調整なし) | 第三者: typed-decisions で ECE 0.124・KL 0.475(Jev 0.144・1.442) | 文字の判断 200〜300 ms(公式)。入力 $0.04/M トークン。文脈長は OpenRouter で 65,536 | **規約 §6 で送った内容と出力の学習への利用を許諾させる。出力で他のモデルを学習させるのは禁止**(§5-1) |
| **LFM2 / LFM2.5**(Liquid AI・判断モデルではなく土台の候補) | 重み公開。**LFM Open License v1.0**(年間売上 1,000 万ドル以上の法人の商用利用は許諾外) | LFM2: 354M・742M・1.17B・2.57B。LFM2.5 に 230M〜8B-A1B・エンコーダ 230M/350M | 文字(VL 版は画像) | 生成モデル(判断ヘッドは無い) | LFM2: 対応 8 言語に日本語。**LFM2.5-1.2B-JP-202606**: JMMLU 54.19・J-MIFEval 79.08・J-GSM8K 62.20(作者の表)。判断の土台としてのゼロショット: JNLI 17.15%・JComQA 68.87%(#24 の第三者測定) | LoRA の手順(Unsloth・TRL)あり。第三者の RLCD 版あり(Decision Index で LFM2.5-2.6B-RLCD 6.76・350M-RLCD 1.38、ECE 0.2545・0.5681) | 判断の較正は上の RLCD 版の値のみ | CPU 向けと明記(Qwen3 比で CPU の prefill と decode が 2 倍と自称)。GGUF・ONNX あり | 知識の締切 Mid-2024(LFM2.5-1.2B-JP-202606) |

### 2-2 名前の整理(「Open-Jev」は少なくとも 4 つ)

| 名前 | 公開者 | 基盤 | ライセンス | v2 の扱い |
|---|---|---|---|---|
| Open-Jev(razorback16) | razorback16 | DiffusionGemma 26B-A4B | Apache-2.0 | 採らない(OpenJev のノート) |
| OpenJev(openjev/openjev) | 組織 openjev | qwen3_5 のタグ | 重み CC BY-NC 4.0 | 採らない(非商用・R-83) |
| Open-Jev-2B/9B/27B-v1.1 | ZefanCai | Qwen3.5 / Qwen3.8 | アダプタ Apache-2.0・コード MIT | J1 の候補(§7) |
| openjev(v5) | AlexWortega | Qwen3.5-4B ほか | MIT | 参考(英語・情報が少ない) |

指示書の「Open-Jev」がどれを指すかは指示書に無い。本書は 4 つを並べ、親の判断に任せる。

### 2-3 見つからなかった名前

- 指示書の列挙のうち、**見つからなかった名前は無い**。ただし「Clef と Clef-flash が Qwen 27B と 9B」は、R-83 のとおり基盤が Qwen3.8-27B と Qwen3.5-9B で、世代が違う。
- 「即断」の公開の名前は `GeneLab/sokudan-ja-310m`(Hugging Face)、コードは `hiroki-abe-58/sokudan`(GitHub。`shortcut-guide/sokudan` という同名のリポも検索に出たが、中身は読んでいない)。似た名前の別物に「即答 sokuto」(MI-1222)がある。
- 指示書に無い新しい名前として、Lev(sokudan の作者が日本語で測った英語のモデル。カードは読んでいない)・AnyJev・Tev1(togethercomputer)・JevK5・meraGPT Decider 1・Featherless Simple Jev が出典に出てくる。本書では値を引くだけで、カードは読んでいない(空欄)。

## §3 見たことのない課題で順位が大きく変わった事実

### 3-1 S1MB(2026-09-30・23 モデル・137 ベンチ・英語)

Borda 点(各ベンチで 1 位 100・最下位 0 を平均)の順位。全体は 137 ベンチ、汎化は合成の 6 ベンチ(600 問。GPT-6-Astra が作り、人の確認なし)(#1)。

| モデル | 全体の順位(Borda) | 汎化の順位(Borda) | 変化 |
|---|---|---|---|
| Jev 1.13 | 1(86.51) | 1(97.73) | 0 |
| bekko-system-one-v0-400m | **2(76.21)** | **12(48.11)** | **10 下がる** |
| Open-Jev-9B(ZefanCai) | 3(72.54) | 2(88.26) | 1 上がる |
| Open-Jev-27B-v1.1 | 4(72.35) | 3(87.50) | 1 上がる |
| Tev1-4B-experimental | 5(71.67) | 6(83.33) | 1 下がる |
| kev-9b | 6(70.52) | 5(83.71) | 1 上がる |
| kev-4b | 7(68.81) | 7(73.48) | 0 |
| JevK5 | 8(67.49) | 4(85.98) | 4 上がる |
| bekko-system-one-v0-68m | 10(62.23) | 17(21.21) | 7 下がる |
| decider-0.8b | 14(42.65) | 11(50.76) | 3 上がる |

- 作者の説明: bekko は「学習の一覧と S1MB の評価の一覧で 77 の部分集合の名前が共通」。テストの分割では学習していないが、課題と分野に慣れていると点が出やすい(#1)。
- 作者の注意: 汎化の 6 ベンチは「学習データの重なりが無いことを保証しない」「難しい問題での差は分からない」(#1)。
- Borda 点は「比べるモデルの顔ぶれが変わると値が変わる」(#1)。

### 3-2 自社の評価と第三者の評価の食い違い(GLiNER2.5-Decide)

| 評価 | GLiNER2.5-Decide | 比較 | 出典 |
|---|---|---|---|
| Fastino の fast-decisions(17 課題・各 300 問・自社で生成した「unseen」の評価) | **1 位 60.2%**(1B 版 59.6%・JevK5 57.6%・Laya 46.6%) | | #6・#7 |
| Decision Index 0.2.1(43 ベンチ・偶然の水準を 0 に補正) | **11.21**(ECE 0.0884) | Kev 9B 38.48・Decider 4B 40.7・pplx-decider 56.4・Laya 6.04 | #34 |

Fastino 自身も「This is an internal benchmark, not JevBench」と書いている(#7)。課題の種類(業務の振り分け)に特化した評価と、知識や推論を含む広い評価で、順位が逆になる。

### 3-3 そのほかの「依頼の形で値が変わる」記録

- typed-decisions のカード: 第三者の計測で、Jev のはい/いいえの正解率は「1 依頼 1 問」で 0.843、「ほかの問いと一緒」で 0.788(#12)。
- arXiv:2610.00346 の抄録: 社会科学の問いで、はいといいえを入れ替えると Jev は 100 問あたり 50.5 問で答えが変わる。微調整した判断モデルは基盤より入れ替えによる変化が減る(#35・△)。
- Laya のカード: 「Languages usable 45 of 51」と書くが、即断の作者の日本語の計測では段階の問いが多数決より悪い(#4・#22)。

**v2 にとっての事実**: 公開の点数の順位は、評価の中身と学習データの重なりで入れ替わる。DM1 の主の選択は v2 自身の場面(封印行)で測った値で決める必要がある(R-83 §3-2 と同じ)。

## §4 人の選び方の割合との一致・確率の合い方

### 4-1 人の票の分布との距離(ChaosNLI・英語)

ChaosNLI は 1 問に 100 人の票がある自然言語推論のデータ。OpenDecider の作者が同じ問題で全モデルを測った値(#9・#11)。

| モデル | ChaosNLI の JSD(人の票の分布との距離・小さいほど近い) | ECE(200 問の一般の判断) |
|---|---|---|
| TypeSafe Jev 1.13 | 0.148 | 0.164 |
| Laya | 0.174 | 0.327 |
| Laya typed-decisions | 0.111 | 0.162 |
| OpenDecider-nano | 0.045 | 0.092 |
| OpenDecider-small | 0.040 | 0.087 |
| OpenDecider-small-td | 0.040 | 0.107 |
| OpenDecider-medium-td | 0.035 | 0.110 |
| OpenDecider-large-td | 0.030 | 0.083 |

- **フロアの併記**: 人の票の半分ずつの間の JSD(人どうしのばらつき)は、出典に無い(空欄)。したがって「0.030 は人に十分近い」とは言えない。
- 教師の作り方: 「Two openly licensed teachers … scored every training question through token log-probabilities, each temperature-scaled on held-out gold labels before averaging」(#10)。正解ラベルで温度を合わせた教師の平均の確率を学ぶので、確率の目標は「正しさ」の側である。それでも人の票の分布に近づいた。理由は出典に無い(空欄。推測としては、2 つの教師の平均で分布が平らになった可能性)。
- 200 問の評価は「about ±3 points」と作者が書く(#9)。
- R-83 §4 との関係: R-83 は「Jev 型のモデルを人の行動データで較正した例は見つからなかった」とした。本書の値は**人の判断の割れ方(推論の票)**との一致で、移動や購買の行動データではない。行動データで較正した例は今回も見つからなかった(空欄)。

### 4-2 ECE のフロア(評価セットによるばらつき)

本家 Jev 1.13 の ECE は、評価セットにより **0.074(Decision Index)・0.144(typed-decisions)・0.164(OpenDecider の 200 問)・0.246(Laya のカード)** と 3 倍以上動く(#9・#12・#22・R-83 §3-1)。typed-decisions のカードも「ECE in particular is computed differently by different submitters」と書く(#12)。候補どうしの ECE の差は、同じ評価セット・同じ定義の値どうしでしか比べられない。

### 4-3 日本語での確率の癖(即断の自己報告)

| 癖 | 値 | 出典 |
|---|---|---|
| 真偽で true を過少に予測 | 平均 P(true) 0.133・正例率 0.297。温度で 0.164→0.098 のずれに縮むが、閾値 0.5 の判定は変わらない | #2 |
| 自信過剰 | P(top1)≥0.99 の 224 件中 14 件(6.25%)が誤答 | #2 |
| 「その他」を選ばない | 正解が「その他」の 38 件で 11 件(recall 0.289)。ただし P(その他)の順位は取れている(AUROC 0.94) | #2 |
| 段階 4 水準で第 1 水準を避ける | 300 件中 5 件(v0.1 の 3 本は 58・16・62 件)。3 水準では 78〜99 件 | #2 |
| 学習の再現 | 同じコード・同じ seed の 2 回の学習で M5 が 0.720 と 0.826 | #2 |

## §5 規約とライセンスの注意(R-83 §2-2 に足す分)

### 5-1 d1(Liquid AI)の規約(Last updated SEP 30, 2026)

- §6「License to Liquid AI」: 「You also grant Liquid AI and its affiliates a worldwide, non-exclusive, royalty-free license to use Your Content to develop and improve Liquid AI's models, products, and services, including through training, fine-tuning, evaluation, and testing.」。Your Content には「prompts, questions, instructions, … data … together with outputs generated for you」が入る(#28)。
- 禁止事項: 「use the Services or outputs to develop, train, fine-tune, or improve other AI models」(#28)。
- 結果の性質: 「Similar inputs may produce different results」(#28)。
- 版の変更: 更新で「results, confidence values, or performance」が変わりうる(#28)。
- **含意(事実の範囲)**: 封印行や v2 の世界の状態を送ると、Liquid AI の学習と評価に使われうる。見張りのモデルの教師には使えない。本家 Jev の MCA §2.3(b) と同じく、出力で学習させる道は閉じている(R-83 §1)。本家 Jev は「Jev is not trained on customer requests or responses」(R-83 #1)で、この点は d1 の方が不利。オプトアウトの条項は、読んだ範囲では見つからなかった(空欄)。

### 5-2 LFM Open License v1.0

- 「"Threshold" shall mean annual revenue of 10 million United States dollars ($10,000,000) or more.」「Any Commercial Use of the Work or a Derivative Work by a Legal Entity that exceeds the Threshold is not licensed under this Agreement.」(#31)。
- 今の v2 は個人の研究で、この条件に当たらない(推測)。ただし長期構想の商用化で、売上が閾値を超える相手(顧客や買収先)が使うと許諾の外になる(推測)。採用するならライセンス台帳に条件を書く必要がある。

### 5-3 そのほか

- **bekko の重み**: ライセンス未定(#13)。決まるまで採用の候補にできない。
- **argos1111 の重み**: CC BY-SA 4.0(#24)。派生物に同じ条件が及ぶ(条件の範囲の判断は本書ではしない)。
- **Jev の出力の使用**: 即断は「Jev を一度も呼んでいない」、Kev・decider は「使っていない」、OpenDecider は「教師は公開ライセンスの 2 本」、Open-Jev(ZefanCai)は「Jev の予測ではない」と明記。Clef は「社内の合成データ」とだけ(R-83)。GLiNER2.5-Decide・pplx-decider・Laya の学習データは記載なし(空欄)。typed-decisions のラベルの元(「teacher」)が何かは空欄で、Laya-td と OpenDecider の td 系はこの train を使っている(#9・#12・#22)。
- **知識の締切**: LFM2.5-1.2B-JP-202606 は「Mid-2024」(#32)。世界の基準の日付(2026-07-28 の週)の店や出来事は、モデルの知識ではなく入力(state)で渡す必要がある(推測)。他の候補の締切は空欄。

## §6 手元の機械での速さ

- 手元の機械(2026-10-06 に確認): CPU Intel Core Ultra 7 265K(20 スレッド)・メモリ 31.2 GB・GPU NVIDIA GeForce RTX 5070(12,227 MiB)。
- システムの python 3.12.10 と `.venv` のどちらにも torch・transformers・onnxruntime・safetensors・huggingface_hub が入っていない。どの候補も**追加の pip install と、Hugging Face からの重みの取得が要る**。重みの取得先(huggingface.co)は CLAUDE.md §7 の許可の一覧の外。したがって**どれも測っていない(要インストール=先に聞く)**。
- 公表値から見た目安(推測。v2 の入力の長さで測ったものではない):
  - 即断: CPU の batch 32 で 6.6 問/秒(24 スレッドの 285K)。移動と購入の約 248 万回/日(R-83 §7-1)を CPU だけで回すと 248 万 ÷ 6.6 ≒ 37.6 万秒 ≒ **約 104 時間/シム日**。RTX 5090 の 259 問/秒なら約 2.7 時間/シム日(RTX 5070 での値は空欄)。即断は文の平均 134 トークンで学習しており、v2 の人ごと 300 トークン(DM4 の親推奨)を超える入力では精度が下がる(400〜799 トークン帯の AUROC 0.859・学習ごとに 0.763〜0.889)(#2)。
  - OpenDecider-nano: CPU のみで 1 問 0.1〜0.7 s・約 2 GB(#10)。
  - GLiNER2.5-Decide: 48 vCPU で 64 トークン 167.3 ms(#7)。
  - 9B 級(Clef-flash・Open-Jev-9B・Kev-9B)は bf16 で重みだけで約 18.8 GB(9.4B × 2 バイト・推測)で、12 GB の RTX 5070 には量子化なしでは載らない(推測)。Kev-9B はカードで約 22 GB の常駐。

## §7 2 段の形(常に見張る軽いモデル+実際に判断するモデル)の候補の組み合わせ(案・3 つ)

R-83 §6 と DM10 のとおり、見張りの教師は本家 Jev と d1 にはできない(両方の規約)。教師はオープンなモデルにする。

| 組 | 見張り(常時・軽い) | 判断(呼ばれたとき) | 向く理由 | 弱み |
|---|---|---|---|---|
| **A** | 即断 sokudan-ja-310m | Clef-flash(9B) | 見張りは日本語の実測があり CPU で動く。判断は Jev の API と互換で、画像も読む。両方が `/v1/systemone` の形なので口が 1 つで済む(即断は `sokudan serve` で互換のサーバーを持つ・#2) | Clef-flash の日本語・決定論・処理量が空欄。即断は短い文と業務の問い合わせの領域で学習 |
| **B** | 即断、または GLiNER2.5-multi-Decide(287M・多言語・規則つき) | Open-Jev-9B か Kev-9B に、人の行動データで分布に合わせる LoRA を足したもの(DM3 (b)) | 判断の側の学習コードが公開されていて、DM3 の本線(分布に合わせる損失)をそのまま当てられる。Open-Jev は候補ごとに独立に採点するので、選択肢の順の偏りが出にくい作り(推測) | 判断の側は英語のみと明記(Kev)か、日本語の評価なし(Open-Jev)。日本語での値は J1 で測るまで空欄 |
| **C** | OpenDecider-nano の手順(公開ライセンスの教師から蒸留)で、日本語の基盤(ModernBERT-ja か LFM2.5-Encoder)に作る自前の見張り | LFM2.5-1.2B-JP-202606(数値を出す量の生成)+組 A か B の判断モデル | すべて手元の CPU と小さな GPU に載る大きさ。数値で決める量(DM13 の値段・時刻)を生成で出す口を持つ | 自前の見張りは未リサーチの作業(expedient)。LFM は判断の土台としての日本語のゼロショット値が低く(JNLI 17.15%)、RLCD 版も Decision Index で低い(6.76)。ライセンスに売上の閾値 |

どの組でも、見張りの教師ラベルは DM10 のとおり「上の層を呼んだ結果、行動が変わったか」で、教師は判断の側のオープンなモデル。

## §8 本人が連続した量を決める場面に向く出力の形(DM13・§3)

### 8-1 各候補が返せる形

| 形 | 中身 | 返せる候補 | 注意 |
|---|---|---|---|
| **段階の語の分布**(score) | 水準ごとの確率+期待値 | Clef・d1・Open-Jev(分布と期待値)・Kev(1〜255 段・R-83)・decider(2〜10 段・R-83)・即断(累積リンク・水準の数は依頼ごと)・OpenDecider・Laya・bekko・GLiNER("0"〜"10" をラベルとして) | **第 1 水準を避ける偏り**: 即断(4 水準で 5/300)・Laya 多言語版(0/300・日本語でも英語でも)・Kev と Lev(全水準を同じ文にした対照で第 1 水準の確率が低い)(#2・#4)。Lev は順と逆順の平均で段階の正解率が英語 6.9 点・日本語 8.7 点上がった。即断では同じ対策で精度が保てず見送り(#2・#4) |
| **数値の候補の中の選択**(choice) | 「500 円」「1,000 円」などの候補ごとの確率 | すべての候補(選択肢の上限は Kev・decider 255・R-83。Open-Jev は候補ごとに 4,096 トークン) | 候補の刻みを人(設計者)が決める。刻みが結果を動かすので expedient の印が要る(推測) |
| **自由な数値** | 数字そのもの | 判断モデルには無い。生成の LLM(LFM2.5-1.2B-JP・自前の艦隊)だけ | 丸い値への偏りは R-97(第 4 群の 8)の対象 |
| **確率の分布からの抽選** | 上のどれでも、seed つきで 1 つ引く | すべて | v2 の既定の使い方(R-83 §4-2 のトゥールーズの例と同じ形) |

### 8-2 量の種類ごとの向き(事実の対応づけ。採否は親の判断)

| 量の種類(指示書 §3) | 向く形 | 理由 |
|---|---|---|
| 人が数字で考えない量(声の大きさ・歩く速さ・相手との距離) | 段階の語の分布 → エンジンが人ごとに物理の値へ | 判断モデルの score の形がそのまま使える。ただし位置の偏りが分布の形を変えるので、J1 で対照の試験が要る |
| 人が数字で考える量(値段・払う金額・時刻) | 生成の LLM の数値、または数値の候補の choice | 判断モデルは自由な数値を出せない。choice にすると刻みが設計者の指紋になる |

## §空欄(17 件)

1. Clef・Clef-flash の日本語の評価・ECE・決定論・処理量(R-83 §8 の 5〜7 のまま)。
2. Kev-9B・Open-Jev-9B・OpenDecider・GLiNER2.5-multi-Decide・pplx-decider の日本語の値(Kev と OpenDecider は英語のみと明記)。
3. d1 の対応言語の一覧・日本語の値・レート上限・パラメータ数・決定論(公式の資料に無い。「多言語で勝つ」の投稿の原文は読めず #38)。
4. d1 の規約のオプトアウト(送った内容を学習に使わせない手続き)の有無。
5. ChaosNLI の人どうしのばらつき(JSD のフロア)。
6. 判断モデルを移動・購買・時間利用などの人の行動データで較正した例(R-83 §8 の 15 のまま)。
7. 判断モデルを人の集団のシミュレーションに使った例(R-83 §8 の 14 のまま)。
8. OpenDecider の蒸留で人の票に近づいた理由の分析。
9. typed-decisions のラベルの元(カードの「teacher」が何か)。
10. GLiNER2.5-Decide・Laya・pplx-decider の学習データ。
11. Lev・AnyJev・Tev1・JevK5・meraGPT Decider 1 のカード(値を引いただけで読んでいない)。
12. `shortcut-guide/sokudan` と `hiroki-abe-58/sokudan` の関係。
13. 手元の CPU(Core Ultra 7 265K)と RTX 5070 での各候補の実測(インストールと重みの取得が要る=先に聞く)。
14. 9B 級を 4 ビットなどに量子化したときの判断の精度と、RTX 5070 に載るか。
15. Qwen3.5・Qwen3.8 系の候補の知識の締切。
16. 即断の文の長さを v2 の入力(300 トークン前後)にしたときの精度の実測(作者の値は 400〜799 トークン帯のみ)。
17. 判断がユーザーに要るもの: 指示書の「Open-Jev」がどれか(§2-2)、d1 を比較の腕に使うか(規約 §6)、LFM と argos1111 のライセンスの条件を受け入れるか、重みの取得先(huggingface.co)を許可の一覧に足すか。

## §v2 への当てはめ(案・未決。親が判断する材料)

### 9-1 段 J1(モデルの試験)に載せる候補の順位(案)

| 順 | 候補 | 役 | 載せる理由 | 先に確かめること |
|---|---|---|---|---|
| 1 | 即断 sokudan-ja-310m | 見張りの候補・日本語の基準の小モデル | 日本語の実測・Apache-2.0・CPU・学習スクリプト・Jev 互換のサーバー | v2 の場面(300 トークン前後)での精度。段階 4 水準以上の位置の偏り |
| 2 | Clef-flash(9B) | 判断の主の候補(GPU 後) | Apache-2.0・Jev 互換の明記・画像・Decision Index の多くの行で上位(カードの表) | 日本語の値・決定論(DM9)・RTX 5070 に載るか |
| 3 | Open-Jev-9B か Kev-9B | 較正(DM3 (b))の土台 | 学習コードの公開。分布に合わせる LoRA を当てられる。Open-Jev は順に依存しにくい作り(推測) | 日本語の値。Kev は英語のみと明記 |
| 4 | OpenDecider-small(英語) | 人の票との一致の参照の腕 | 判断モデルで唯一、人の票の分布との JSD を報告。公開ライセンスの教師から蒸留する手順の手本 | 日本語は範囲外。手順の手本として読むのが主 |
| 5 | GLiNER2.5-multi-Decide | 見張りの第 2 候補 | 多言語・CPU・LoRA・規則つきの同時の判断 | Decision Index の補正後の点が低い(多言語版 4.26) |
| 6 | d1(API) | 比較の腕(公開の場面だけ) | Jev と同じ形・無料枠 | 規約 §6(送った内容が学習に使われうる)。封印行は送らない。DM12 の決まりを d1 にも当てる |
| 7 | LFM2.5-1.2B-JP-202606 | 数値を出す量(DM13 (a) の後半)の生成の腕 | 日本語のベンチマークの公表・CPU 向け | LFM のライセンスの売上の条件 |
| 採らない | JEV-27B(-VL)・OpenJev(openjev/openjev)・bekko(重みのライセンス未定)・pplx-decider(学習データの記載なし・英語の評価のみ) | | R-83・本書 §5 | |

### 9-2 J1 で足す試験(案)

- **位置の偏りの対照**(DM13 のため): 全水準を同じ文にした対照・第 1 水準の率・順と逆順の平均。即断と Lev の作者の手順(Laya の `presentation_checks.py`)を日本語の状態で使う(#4)。
- **はい/いいえの入れ替えの試験**(arXiv:2610.00346 の形・#35)。
- **ECE と分布の距離は同じ評価セット・同じ定義で**(§4-2)。
- **人の票との一致**: 日本語の判断の割れ方のデータで JSD を測る。データの候補は空欄(英語の ChaosNLI だけが見つかった)。

### 9-3 試験の前に要るインストールと取得の一覧(すべて先に聞く)

| 物 | 何のため | 量や条件 |
|---|---|---|
| torch(CPU 版。GPU で測るなら RTX 5070 に合う CUDA 版)・transformers・safetensors・tokenizers・huggingface_hub | どの候補にも要る | 即断は Python 3.11〜3.13(手元は 3.12.10) |
| `pip install sokudan` | 即断 | 重み約 3.1 億パラメータ |
| `pip install gliner2` | GLiNER2.5-(multi-)Decide | |
| `pip install opendecider` | OpenDecider-nano(参照の腕) | 約 2 GB |
| Open-Jev のリポを clone して `pip install -e '.[train]'`(transformers 5.10.2・PEFT 0.19.1) | Open-Jev-9B | 基盤の Qwen3.5-9B は別に取得。GPU が要る |
| Kev のリポ | Kev-9B | CUDA で約 22 GB の常駐(RTX 5070 には載らない) |
| Clef-flash の同梱コード+pillow(torch 2.11・transformers 5.10.2 で試験と記載) | Clef-flash | 約 9.4B パラメータ。GPU 後 |
| llama.cpp 系(GGUF)か transformers | LFM2.5-1.2B-JP-202606 | CPU で動く |
| Hugging Face からの重みの取得 | すべて | **huggingface.co は CLAUDE.md §7 の許可の一覧の外**。取得ごとにライセンス台帳へ行(LFM は売上の条件・argos1111 は CC BY-SA) |
| Liquid AI のアカウントと API キー | d1 | 規約 §6 の受け入れ=ユーザーの判断。キーは環境変数だけ |

### 9-4 草案への影響(案)

- DM1: 候補の表に即断・Open-Jev(ZefanCai)・OpenDecider・GLiNER・d1・LFM を足す。DM1 (b) の「Clef-flash と Kev-9B/decider を並べる」は、日本語の基準として即断を足す形が考えられる(推測)。
- DM3: 「Jev 型を人の割合に合わせた例は無い」は、「人の票の分布(ChaosNLI)に近づけた例は 1 系統ある(英語・作者の測定・フロア空欄)」に更新できる。行動データで較正した例は今も空欄。
- DM10: 見張りの教師に使えないものに d1 を足す(規約)。
- DM12: 比較の腕に d1 を足し、本家 Jev と同じ決まり(公開の場面だけ・出力を学習に使わない)に加え、「送った内容が先方の学習に使われうる」を書く。
- DM13: 段階の語の形には位置の偏りがあると材料に足し、J1 の試験に対照を足す。

## lit README 追記行

| R-94 | 判断モデルの候補の再調査(R-83 の更新: 即断ほか日本語の判断モデル・OpenDecider の人の票との一致・S1MB と GLiNER の順位の入れ替わり・d1 の規約・LFM のライセンス・2 段の組・連続した量の出力の形) | 2026-10-06 | B(親検収 未) | [v2-r94-judgment-model-candidates-update.md](v2-r94-judgment-model-candidates-update.md) |
