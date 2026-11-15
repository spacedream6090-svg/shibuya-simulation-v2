<!-- hdr:v1 | 等級: B(第347 親の一次確認=末尾の表) | 作成: 2026-11-16 | 範囲: 返事その 8(11-16)§7-1 R-152 モデルの候補の棚卸し -->
# R-152 モデルの候補の棚卸し(住民の LLM の候補の一覧・選び直しの物差しの材料・判断モデルの第 1 世代の順の変わり方・1 つにするか並べるか混ぜるかの先例)

- **分野**: 自然言語処理・機械学習 #27 / 計算機科学(並列・決定論) #28 / 計算社会科学 #25 / 認知科学 #12 | **重要度**: 発注文に記載なし(親が付ける)。材料にする所は [返事その 8(11-16)](../design/prompt-2026-11-16-reply8.md) §7-1 の R-152 と、[壁打ちの記録](../reference/wallbounce-record-2026-11-02_05.md) の 2-61・2-64・2-51 と U22
- **一次確認**: B(第347 親の一次確認=末尾の表)。筆者がこの回に読んだ出典は 52 本(◎ 37・○ 9・△ 6)。既存答申からの引用は R-83・R-94・R-123・R-125・R-141・R-142・R-147・R-149・R-150 と、dm_eval の記録 2 本(dm61・dm-eval-11-01)。読めなかったものは §8。
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 作成 2026-11-16・リサーチ役(Opus 5.5)。子サブは起動していない。作ったのは本書 1 本だけで、コード・台帳・設計書・INDEX は 1 バイトも変えていない。commit も git add もしていない。封印の層(holdout・test の層)には触れていない。発注文が開かないと定めた文書(IMPLEMENTED.md・build-report-C7*/C8*・G1 のバックテストの計画・パターン台帳)は開いていない。重み・データセットの取得、pip、clone はしていない。
> **取り方の注**: 頁は WebSearch と WebFetch で読んだ。WebFetch は頁を小さなモデルに通して答えを返すので、本書の数値は写しの段を 1 つ経ている。Hugging Face のモデルの一覧と作成日・ライセンスの欄は、`huggingface.co/api/models` の JSON を WebFetch で読んだ(R-125 と同じ読み方。保存はしていない)。GitHub の issue と PR も WebFetch で読み、gh と curl は使っていない。10 万字を超える頁は前の 10 万字だけ読んだもの([S36][S38][S48])がある。[S38] の 10 万字より後は、2 回目の読み込みで道具の側の内容の検査に止められて読めず、取り直していない(§8 の U2)。
> **断られた頁**: 無し。403・robots・規約の禁止には当たっていない。404 が 1 本([S55]・コミュニティの迎合の試験の紹介の頁)で、別の経路・ミラー・キャッシュでは取りに行っていない。**Web の道具は利用の上限に当たらなかった**。
> 等級: ◎=原典か公式の文書・カード・API の JSON・issue と PR の本文を読んだ/○=要旨だけ/△=検索の抜粋だけ。筆者の組み立ては【見立て】、根拠の無い置き方は【推測】と書く。**推薦は書かない**。決めるのはユーザー。
> 既存答申との関係(重ねない): GDN を持つ模型(Qwen3.5-9B など)の状態の大きさ・日本語の値・vLLM の保存の口・#42960 と #45819 の 11-05 までの経緯は [R-147](v2-r147-continual-learning-persistent-state.md)(**B**)、Qwen3-8B の癖の実測(数の偏り・並び・AWQ での縮み・SimBench・Cheung の省略の偏り)は [R-149](v2-r149-llm-judge-model-biases-and-remedies.md)(**B**)、5070 の構成と Qwen3-8B AWQ の VRAM は [R-123](v2-r123-rtx5070-qwen3-8b-runbook.md)(**B**)、KV の量は [R-142](v2-r142-activation-tape-capture.md)(**B**)、操舵とベクトルは [R-141](v2-r141-persistent-state-vectors-and-steering.md) と [その追補](v2-r141-addendum-sae-and-persona-vectors.md)、判断モデルの候補は [R-83](v2-r83-jev-type-decision-models.md)・[R-94](v2-r94-judgment-model-candidates-update.md)・[R-125](v2-r125-open-weight-decision-models-recheck.md)、Centaur・Oh & Gobet・HumanLM は [R-150](v2-r150-learning-from-human-behavior-data.md)(**B**)を正とする。本書は値を再掲せず番号で引き、足りない分だけを足す。

## §0 要旨

1. Qwen3-8B(HF の作成 2025-04-27)の後に出た公式のリポの公開モデルで、8B 級・日本語可・Apache-2.0 か同等の条件に入りうるのは、Qwen3.5-9B・Gemma 4 E4B と 12B・Ministral 3 8B・Granite 4.1 8B と 4.2 8B・llm-jp-4 の 8B(instruct・thinking・4.1 thinking)・Qwen3-Swallow-8B・DeepSeek-R1-0528-Qwen3-8B・Qwen3-VL-8B・Qwen3-4B-2507 だった。Qwen の 3.6・3.8 世代に 8B 級は無い。Nemotron-Nano-9B-v2-Japanese は NVIDIA 独自のライセンスで「同等」かは要判断(§2)。
2. 第三者が同じ表で測った日本語の平均(Swallow v2)は、Qwen3.5-9B 0.534・Qwen3-Swallow-8B-RL 0.510・Nemotron JP 0.503・Qwen3-8B 0.491・Gemma 4 E4B 0.484・llm-jp-4-8b-thinking 0.448 だった。Gemma 4 12B・Ministral 3・Granite・llm-jp-4.1 はこの表に無い [S19]。
3. 考える形の切り替えはモデルで違う。Qwen3-8B は切り替えと文ごとの切り替えができる。Qwen3.5-9B・Granite 4.2・Nemotron JP・Gemma 4 は切り替えだけができる。Qwen3-Swallow は常に考え、Ministral 3 と llm-jp-4 と Qwen3-VL は考える版と考えない版が別の重みになっている(§2-2)。
4. 読んだ範囲で公式の 4 ビットの重みがあるのは、Qwen3-Swallow-8B(AWQ)・Gemma 4(QAT の w4a16)・Granite 4.2(NVFP4・MXFP4)だった。Qwen3.5 の公式の量子化は 27B 以上にしか無い。今の取得の許可は、住民の LLM の重みを `Qwen/` の公式に限っている(CLAUDE.md §7 の 11-01 の項)。
5. 毎回同じ答えについて。vLLM のバッチ不変の試験済みの一覧(11-04 の版)に、§2 の候補で名前が載るのは Qwen3-8B とその AWQ だけだった。GDN の #42960 と PR #45819 は 11-16 の時点でも open で、PR は needs-rebase。11-12 の報告では、PR を 0.33.0 に当てると bs1 と bs16 はビット単位で一致したが、デコードと前読みの間のずれが残った [S31][S32][S33]。
6. 上下を守る力の値は少ない。Qwen3-8B は、前置きと利用者の文が食い違う組で前置きを守った率が 0.60、利用者への有用さが 0.27 だった [S36]。AgentDojo の難しい組では、外から紛れた命令による攻撃の成功率が Qwen3-8B 47.2%・Qwen3.5-9B 43.2%・gpt-oss-20B 44.0% だった [S38]。人らしさ・迎合・断り・均質化は、候補のモデルの値がほとんど空欄だった。
7. 判断モデルの dm_eval の値は、GPU を使う前なのでまだ空である。人の票の分布との一致を測った唯一の値(R-94 の ChaosNLI)は、OpenDecider 0.030〜0.040 に対して本家 Jev 0.148・Laya 0.174 で、4 倍を超える開きがある。人の物差しを足すと順が大きく動きうる。教師が Qwen の系統の候補は「Qwen3-8B との一致」で有利に出うる(同じ系統のモデルは誤りがそろう=[S44])【見立て】。
8. 先例では、12 個の LLM の予測の平均が 925 人の集団と差が無かった [S46]。データを共有すると結果がそろい、土台を共有したときは調整の仕方しだいだった [S45]。Llama-3 系の 8B のモデル 15 種類(一般 1・専門の微調整 14)を 48 体の網に置いた実験では〔親の訂正 第347: もとの文は「15 体の実験」。15 はモデルの種類の数で、1 つの網は 48 体〕、人物の役は全体の合意をほとんど変えず、別のモデルを混ぜると合意が大きく動いた(d=1.41)[S48]。社会シミュの設計の変数で、結果に最も効いたのは土台の LLM だった [S49]。
9. 推薦は書いていない。§6 に比べの表を、§7 に壁打ちで決める題を置いた。

## §1 問いと前提

### 1-1 問い(返事その 8 §7-1 の R-152)

1. 住民の LLM の候補。条件は公式のリポ・Apache-2.0 か同等・8B 級(4 ビットで 12 GB に入る)・日本語が使える。Qwen3-8B の後に出た公開モデルの一覧(出た日・大きさ・ライセンス・日本語の力・考える形の切り替え・公式リポの URL)。§2。
2. 物差しの材料。軸は人らしさ・上下を守る力・迎合と断りの率・皆が同じになる癖・毎回同じ答えを出せるか・速さと VRAM。軸ごとに測り方の先例と、候補ごとに公表されている値を集める。§3。
3. 判断モデルの第 1 世代(MD-22)の候補について、今の物差し(Qwen3-8B との一致・迷いの合い方)に「人の判断との合い方」を足すと、候補の順がどう変わりうるか。§4。
4. 「1 つにする・ランごとに並べる・住民ごとに混ぜる」の先例。§5。

### 1-2 前提(記録と設計書)

- 記録 2-61(U22):住民の LLM の既定は Qwen3-8B の 4 ビット(11-01 の 5070 の指示)。同じ条件でより新しい公開モデルがあれば候補に足す決まりはある。ただし、選ぶ物差しは工学の列(Qwen3-8B との一致・広がり・位置の偏り・決定論・秒と VRAM・日本語の破綻率)で、人らしさの物差しが無い。
- 記録 2-64:住民の LLM を複数にするなら、(B) ランごとに替えて分布を並べる形を先にし、(A) 1 回のランの中で住民ごとに混ぜる形は腕にする(割り当てはランダム・性格や種別と結び付けない)。「1 つにするか・並べるか・混ぜるか」をモデルの選び直しの物差しに足す。
- 記録 2-51:モデル選びの軸に「毎回同じ答えを出せるか」「何本余計に要るか」を、速さ・精度と並べる。
- 記録 2-63 の ②:上下を守れるモデルを選ぶか学ばせる。
- MD-22([03-mind.md](../design/spec/03-mind.md)):判断モデルの第 1 世代は、公開の重みの判断モデル(学習なし)。4B 以下を 5070 の dm_eval で比べて選ぶ。比べの列は、8B の logprob との一致・広がり・位置の偏り・決定論・1 判断の秒と VRAM・日本語の破綻率・「迷いの分布が Qwen3-8B と合うか」。
- **取得の許可**(CLAUDE.md §7 の 11-01 の項):住民の LLM の重みは `Qwen/` の公式のリポだけ、判断モデルは各モデルの公式のリポ(S1MB か awesome の一覧がリンクする先)だけ。safetensors だけ・`trust_remote_code` は切る。**§2 の `Qwen/` 以外の候補の重みを取るには、ユーザーの許可が先に要る**(本書は事実として書くだけ)。
- 5070 で使える VRAM は、常駐のアプリを除いて約 10 GB(12,227 MiB のうち 2,081 MiB を常駐のアプリが使う=R-123 §1・R-125 §3-2)。

### 1-3 条件の読み方【見立て】

- 「8B 級」は「4 ビットで 12 GB に入る」と読み、4B〜12B を表に入れた。12B(Gemma 4 12B)は境目の行として入れた。20B 以上(gpt-oss-20b ほか)は表の外の行に置いた。
- 「Apache-2.0 か同等」は、MIT を同等の側に置いた。NVIDIA・PFN・Liquid・Tencent などの独自のライセンスは「要判断」とした。同等かどうかは法的な判断で、本書では決めない。
- 「出た日」は 2 つ書いた。HF の API の `createdAt`(リポを作った日で、公開より前のことがある)と、カードが書く発表日である。

## §2 問 1 住民の LLM の候補

### 2-1 一覧(条件に入りうるもの)

調べた発行元は Qwen・google・mistralai・ibm-granite・llm-jp・tokyotech-llm(Swallow)・nvidia(日本語版)・sbintuitions・deepseek-ai・pfnet・allenai・meta-llama・microsoft・openai・swiss-ai の 15 である(§8 の U16 に調べていない発行元を書いた)。

| # | 名(公式のリポ) | HF の作成日 / 発表日 | 大きさ | ライセンス | 構造の注 | 出典 |
|---|---|---|---|---|---|---|
| 0 | **Qwen3-8B(今の既定)** `Qwen/Qwen3-8B`・AWQ は `Qwen/Qwen3-8B-AWQ` | 2025-04-27 / 空欄 | 8.19B(8,190,735,360) | Apache-2.0 | 全注意・36 層 | [S4] ◎ |
| 1 | **Qwen3.5-9B** `Qwen/Qwen3.5-9B` | 2026-02-27 / 空欄 | 9B(札の safetensors の表示は 10B=画像の部分込み) | Apache-2.0 | GDN 24 層+全注意 8 層(`8 × (3 × GDN → 1 × Gated Attention)`)・画像の符号器つき | [S2] ◎・R-147 §4-1 |
| 2 | Qwen3.5-4B `Qwen/Qwen3.5-4B` | 2026-02-27 / 空欄 | 4B(名から) | 空欄(9B と同じ系統。この版のライセンスの欄は読んでいない) | GDN の混成 | [S1] ◎ |
| 3 | **Gemma 4 12B** `google/gemma-4-12B-it` | 2026-05-23 / 空欄(技術報告 arXiv 2607.02770・7 月 2 日) | 11.95B | Apache-2.0(リンク先は Gemma 4 のライセンスの頁) | 局所の窓 1,024 と全体の注意の混成・符号器なしの多モード | [S6] ◎ |
| 4 | **Gemma 4 E4B** `google/gemma-4-E4B-it` | 2026-03-02 / 空欄 | 実効 4.5B(埋め込み込み 8B) | Apache-2.0 | 層ごとの埋め込み(PLE)・窓 512 と全体の混成 | [S7] ◎ |
| 5 | **Ministral 3 8B** `mistralai/Ministral-3-8B-Instruct-2512` | 2025-10-31 / 空欄(名は 2512・論文 arXiv 2601.08584 は 1 月 13 日) | 言語 8.4B+画像 0.4B | Apache-2.0 | 公開の重みは FP8 | [S9][S10] ◎ |
| 6 | **Granite 4.2 8B** `ibm-granite/granite-4.2-8b` | 2026-08-07 / 2026-08-25 | 8B(safetensors の表示は 9B) | Apache-2.0 | 密な Transformer・40 層・GQA(KV 8) | [S11][S12] ◎ |
| 7 | Granite 4.1 8B `ibm-granite/granite-4.1-8b` | 2026-04-06 / 2026-04-29 | 8B(同 9B) | Apache-2.0 | 密な Transformer・40 層 | [S13] ◎ |
| 8 | **llm-jp-4.1-8b-thinking** `llm-jp/llm-jp-4.1-8b-thinking` | 2026-09-15 / 空欄 | 8.59B | Apache-2.0 | 密・llama 型・32 層 | [S14][S15] ◎ |
| 9 | llm-jp-4-8b-instruct `llm-jp/llm-jp-4-8b-instruct` | 2026-03-30 / 空欄 | 8.59B | Apache-2.0 | 同上(SFT だけ・考えない版) | [S16] ◎ |
| 10 | **Qwen3-Swallow-8B-RL-v0.2** `tokyotech-llm/Qwen3-Swallow-8B-RL-v0.2`(AWQ-INT4 版あり) | 2026-01-24 / 2026-02-20 | 8B | Apache-2.0 | Qwen3 の継続事前学習+SFT+RLVR | [S17][S18] ◎ |
| 11 | DeepSeek-R1-0528-Qwen3-8B `deepseek-ai/DeepSeek-R1-0528-Qwen3-8B` | 2025-05-29 / 空欄 | 8.19B | MIT | Qwen3-8B と同じ構造(tokenizer の設定は DeepSeek-R1-0528) | [S22] ◎ |
| 12 | Qwen3-VL-8B-Instruct `Qwen/Qwen3-VL-8B-Instruct` | 2025-10-11 / 空欄 | 8.77B | Apache-2.0 | 画像と文。考える版は別のリポ(名から) | [S29] ◎・[S1] |
| 13 | Qwen3-4B-Instruct-2507 `Qwen/Qwen3-4B-Instruct-2507` | 2025-08-05 / 空欄 | 4.02B | Apache-2.0 | Qwen3ForCausalLM | [S30] ◎ |
| 14 | NVIDIA-Nemotron-Nano-9B-v2-Japanese `nvidia/NVIDIA-Nemotron-Nano-9B-v2-Japanese` | 空欄 / 2026-02-17 | 9B | **NVIDIA Nemotron Open Model License**(商用可と書く。同等かは要判断) | Mamba-2 と MLP が主で、注意は 4 層だけ | [S20] ◎ |

- **Qwen の後の世代に 8B 級は無い**: Qwen3.6 は 27B と 35B-A3B(2026-04)、Qwen3.8 は 27B・2.4T-A95B・Flash-Next(2026-08)だけだった [S1]。Qwen3.8-Flash-Next は総 125B(動くのは 6B)で、ライセンスの欄は `qwen-community-1.0` だった [S3]。Qwen3.8-27B のライセンスの欄は読んでいない。
- Qwen-Drive-1.0-4B(2026-08-27)は名から運転の用途と読めるので、表に入れていない【推測】。WebWorld-8B(2026-02-13)は中身を読んでいない。
- 表に入れなかった Swallow の版: Qwen3-Swallow-8B の CPT と SFT(RL 版の前の段)、Medical-Qwen3-Swallow-8B(医療)[S17]。

### 2-2 日本語の力と考える形

日本語の値は、測った人が違う列をまたいで比べない(R-147 §4-2 と同じ扱い)。第三者の値は Swallow v2 の事後学習の表 [S19] だけで、これは開発元の値と別の列に置いた。

| # | 名 | Swallow v2(第三者)日本語平均 / JamC-QA / M-IFEval(ja)/ MMLU-ProX(ja)/ 日本語 MT-Bench | 開発元の値(日本語か多言語) | 札の言語 | 考える形の切り替え | 出典 |
|---|---|---|---|---|---|---|
| 0 | Qwen3-8B | 0.491 / 0.401 / 0.611 / 0.711 / 0.689 | Nejumi 4 の総合 0.690(NVIDIA の札が引く値)| 100 以上の言語 | `enable_thinking`(既定 True)で止められる。True のときは `/think`・`/no_think` で文ごとに切り替えられる | [S19][S20][S4] ◎ |
| 1 | Qwen3.5-9B | **0.534** / 0.489 / 0.518 / 0.784 / 0.707 | MMMLU 81.2・MMLU-ProX 76.3・INCLUDE 75.6・IFEval 91.5・IFBench 64.5 | 201 の言語(日本語の名は無い) | 既定は考える。`enable_thinking: False` で止める。文ごとの切り替えは「公式には無い」 | [S19][S2] ◎ |
| 2 | Qwen3.5-4B | 0.456 / 0.395 / 0.456 / 0.750 / 0.618 | — | — | 空欄(9B と同じ系統と【推測】) | [S19] ◎ |
| 3 | Gemma 4 12B | 表に無い | MMMLU 83.4・IFBench 74 | 140 以上の言語で事前学習・35 以上をすぐ使える(日本語の名は無い) | 前置きの頭に `<|think|>` を置くと考える。外すと止まるが、空の考えの欄は出る | [S6] ◎ |
| 4 | Gemma 4 E4B | 0.484 / 0.424 / 0.637 / 0.670 / 0.758 | MMMLU 76.6 | 同上 | 同上。止めたときは考えの欄を出さない | [S19][S7] ◎ |
| 4' | 参考: Gemma 4 E2B | 0.431 / 0.361 / 0.646 / 0.580 / 0.726 | MMMLU 67.4 | 同上 | 同上 | [S19][S7] ◎ |
| 5 | Ministral 3 8B | 表に無い | 基盤の版の多言語 MMLU 0.706(同じ表の Qwen3 8B Base 0.700)。指示の版の多言語の値は無い | 11 言語に日本語の名がある | 指示の版に考える形は無い。考える版は別の重み(Ministral 3 8B Reasoning 2512) | [S10] ◎ |
| 6 | Granite 4.2 8B | 表に無い | MMLU-ProX lite(IBM)61.06・IFBench 79.33 | 12 言語に日本語の名がある | 既定は考える。`enable_thinking=False` で止める。`low_effort` もある | [S12] ◎ |
| 7 | Granite 4.1 8B | 表に無い | MMMLU 64.84・INCLUDE 58.89・MGSM 82.32(日本語を含む言語の集計)・IFEval 87.06 | 12 言語に日本語の名がある | 札に考える形の記述なし | [S13] ◎ |
| 8 | llm-jp-4.1-8b-thinking | 表に無い(前の版 llm-jp-4-8b-thinking は 0.448 / **0.514** / **0.677** / 0.623 / 0.706) | 日本語 MT-Bench 7.58(審査は gpt-5.4・前の版 7.54)。Swallow の表の値は画像だけで、数値は読めない | 日本語と英語 | Harmony の形で `reasoning_effort`。止められるかは札に無い | [S19][S15] ◎ |
| 9 | llm-jp-4-8b-instruct | 表に無い | 自分の行は無い(考える版の低い努力で MT-Bench 7.23) | 日本語と英語 | 考えない版(SFT だけ) | [S16] ◎ |
| 10 | Qwen3-Swallow-8B-RL-v0.2 | **0.510** / 0.469 / 0.566 / 0.708 / 0.710 | 札の値は画像だけ | 日本語と英語 | **切り替えなし・常に考える**(札の文) | [S19][S18] ◎ |
| 11 | DeepSeek-R1-0528-Qwen3-8B | 表に無い | 日本語の記述なし(数学と GPQA だけ) | 記述なし | 札に止め方の記述なし(考えるのが既定と読める) | [S22] ◎ |
| 12 | Qwen3-VL-8B-Instruct | 表に無い | 読んでいない | 読んでいない | 考えない版(考える版は別のリポ) | [S1][S29] |
| 13 | Qwen3-4B-Instruct-2507 | 表に無い(元の Qwen3-4B は 0.448) | 読んでいない | 読んでいない | 名から考えない版(Thinking-2507 が別)【推測】 | [S19][S30] |
| 14 | Nemotron-Nano-9B-v2-JP | 0.503 / 0.437 / 0.637 / 0.711 / 0.689 | Nejumi 4 の総合 0.711(同じ表の Qwen3-8B 0.690。札は「元の試験の値とは比べられない」と書く) | 日本語版 | `enable_thinking`(既定は考える)。考える量の上限の口 `max_thinking_tokens` | [S19][S20] ◎ |

- Swallow v2 の頁の日付は書かれていない。行の中で最も新しいモデルの日付から、2026-03 以後の版と読める [S19]。Qwen3-8B と Qwen3.5-9B の値は R-147 §4-2 と同じだった(写しの確かめ)。
- 測る条件(考える形を入れたか)は Swallow の表に書かれていない [S19]。

### 2-3 表の外(条件の一部に当たらないもの・参考)

| 名 | 外した条件 | 値 | 出典 |
|---|---|---|---|
| gpt-oss-20b `openai/gpt-oss-20b` | 21B(動くのは 3.6B)。MXFP4 で「16 GB の中で動く」と札が書く=12 GB に入らない【見立て】 | Apache-2.0。Swallow の日本語平均 0.521。考える量は low・medium・high で、止められるかは札に無い | [S27][S19] ◎ |
| GPT-OSS-Swallow-20B-RL | 同上 | 日本語平均 0.568 | [S19] ◎ |
| Olmo 3 7B(Instruct・Think) | 日本語の札の記述を読んでいない | Swallow の Think 版の日本語平均 0.374 | [S24][S19] ◎ |
| Apertus-8B-Instruct-2509 | API の言語の印に `ja` が無い(`multilingual` だけ) | Apache-2.0・8.05B・2025-08-13 | [S28] ◎ |
| PLaMo 3 の 8B(`plamo-3-8b-fin-instruct`・`plamo-3-translate-8b`) | 金融と翻訳の用途の版。PLaMo のライセンスは R-147 §4-1 では同意の要るコミュニティのライセンス(今回は読み直していない) | 空欄 | [S23] ◎・R-147 |
| Sarashina2.2 3B instruct | Qwen3-8B より前(2025-02-26)。その後の 8B 級は無い | 日本語平均 0.260 | [S21][S19] ◎ |
| Meta の Llama | Qwen3-8B の後に小さな文のモデルは無い(Llama 4 は 17B×16 以上) | — | [S25] ◎ |
| Microsoft の Phi | 後に出たのは Phi-4-mini-flash-reasoning(3.8B)など。日本語の記述は読んでいない | — | [S26] ◎ |

### 2-4 公式の低ビットの重みと許可

| # | 名 | 読んだ範囲の公式の低ビットの重み | 取得の許可(CLAUDE.md §7 の 11-01 の項) |
|---|---|---|---|
| 0 | Qwen3-8B | AWQ(4 ビット) | 許可の内(`Qwen/`) |
| 1 | Qwen3.5-9B | **無い**(公式の FP8・GPTQ-Int4 は 27B・35B-A3B・122B・397B だけ)[S1] | `Qwen/` だが、4 ビットにするには公式でない量子化か自前の量子化が要る |
| 3・4 | Gemma 4 12B・E4B | QAT の w4a16(compressed-tensors。札は「vLLM の向け」と書く。版の指定なし)[S5][S8] | 許可の外(先に聞く) |
| 5 | Ministral 3 8B | FP8(既定の公開の形)と GGUF。札は「FP8 で 12 GB の VRAM に入る」と書く [S9][S10] | 許可の外 |
| 6 | Granite 4.2 8B | FP8・MXFP4・NVFP4(2026-08-13)[S11] | 許可の外 |
| 7 | Granite 4.1 8B | FP8 [S11] | 許可の外 |
| 8・9 | llm-jp-4 の 8B | 公式は GGUF(llama.cpp 向け。R-123 で使わないと決めた道具の形)[S14] | 許可の外 |
| 10 | Qwen3-Swallow-8B-RL | **AWQ-INT4**(GPTQ 版は「性能が大きく落ちた」ので非公開にした)[S18] | 許可の外(`Qwen/` でない) |
| 11 | DeepSeek-R1-0528-Qwen3-8B | 読んだ範囲に無い | 許可の外 |
| 12・13 | Qwen3-VL-8B・Qwen3-4B-2507 | 読んでいない | 許可の内(`Qwen/`) |
| 14 | Nemotron JP | 読んでいない | 許可の外 |

## §3 問 2 物差しの材料

### 3-1 人らしさ(人の選択の分布との合い方・Centaur 型の評価)

**測り方の先例(引くだけ)**: 保持した参加者の負の対数尤度(Centaur・Oh & Gobet=R-150 §2・§5-2)/人の答えの分布との全変動距離を一様の場合で割った点数(SimBench=R-149 §5-2 [S18])/2 週間後の本人の答え直しで割った正規化の一致(Park ほか 2024=記録 2-53・R-150)/省略と「いいえ」の偏りを人の代表標本と比べる形(Cheung ほか 2025=R-149 §4-3)/人の評価者が似ていると判定した勝率(HumanLM=R-150 §5-1)。

**候補ごとの値**

| 名 | 値 | 出典 |
|---|---|---|
| Qwen3-8B | 人の評価で「似ている」の勝率: Qwen3-8B-think 30.6%(Reddit の返信で学ばせた HumanLM は 41.4%) | R-150 §5-1(R-150 の S19) |
| Qwen3-8B-Base ほか Qwen3 の土台 | Psych-101 で学ばせた LoRA の値はある(学ばせていない Qwen3-14B は Psych-201 で 0.869) | R-150 §0 の 2 |
| ほかの候補 | **見つからなかった**(SimBench は Qwen3 以後を試していない=R-149 §5-2。検索 1 回で Qwen3.5・Gemma 4 の値なし) | §8 の U8 |

- 【見立て】公開の値はどれも英語の課題で、日本語の日々の判断(行き先・待つか)で測った値は無い(R-150 §0 の 5 と同じ空欄)。

### 3-2 上下を守る力(指示の階層・文の中に埋め込まれた命令への強さ)

**測り方の先例**

| 先例 | 何を測るか | 主な値 | 等級 |
|---|---|---|---|
| Wallace ほか 2024(指示の階層)[S34] | 運用者の前置き>利用者>道具の出力、の順を守るか。食い違う例を作って学ばせる | 要旨は「見たことのない攻撃の型にも大きく強くなり、ふつうの能力の落ちは小さい」(GPT-3.5)。数値は要旨に無い | ○ |
| IHEval(NAACL 2025)[S35] | 9 課題・3,538 例。前置き・利用者・履歴・道具の出力の順で、合う場合と食い違う場合 | 「どのモデルも食い違うと大きく落ちる」「公開のモデルの最良でも食い違いの解決は 48%」 | ○ |
| HIPO(arXiv 2603.16152・未査読)[S36] | SystemCheck の 2,000 組(食い違う組と合う組が半々・試験は 200)。DeepSeek-V3.2 が審査し、前置きを守った度合いと利用者への有用さを 0〜1 で別々に付ける | 表 1 の素の値(食い違う組/合う組): **Qwen3-8B 0.60/0.27・0.67/0.37**、Qwen3-4B 0.64/0.32・0.68/0.39、Llama-3.2-3B 0.61/0.35・0.67/0.39、Phi-3-3.8B 0.58/0.28・0.64/0.43。学ばせた後の Qwen3-8B は 0.70/0.72・0.77/0.81 | ◎(表 7 の 95% 区間は読めず) |
| How Language Models Choose Sides(ICML 2026 の工房)[S37] | 41 組の食い違う縛り(決まった検査器)。8 モデル。前置きの重みの差(System Authority Delta) | Llama-3.1-8B は食い違う試行で前置きに従ったのが 0.10 だけ。内部の活性からは結果を 0.97 で読み出せ、操舵で前置きに従う率が 0.132 → 0.530 に上がった | ○ |
| Dong ほか(arXiv 2608.02657・未査読)[S38] | AgentDojo の 4 組(slack・workspace・banking・travel)× 6 種の攻撃。道具の出力に紛れた命令の攻撃の成功率(ASR)と課題の達成率 | 表 3 の「手当てなし」の行(banking と travel の保持した組の最も難しい 8 点・3,408 試行): **Qwen3-8B ASR 47.2・達成 65.6、Qwen3.5-9B 43.2・93.8**、Qwen3.5-2B 7.7・50.7、Qwen3.5-27B 34.6・92.4、gpt-oss-20B 44.0・70.6、Gemma-4-31B 6.9・91.4 | ◎(全体の組の表 11 は読めず) |
| SEP(Zverev ほか・ICLR 2025)[S39] | 指示とデータを分けられるかの量 | 抜粋: 「分ける点数は Phi-3 の 13.3% から Gemma-2B の 73.2%」 | △ |

**候補ごとの値**: §2 の候補で値があるのは Qwen3-8B(HIPO・Dong ほか)と Qwen3.5-9B(Dong ほか)だけだった。Gemma 4 は 31B だけ(Dong ほか)。

- 【見立て】Dong ほかの ASR は、道具の出力に紛れた「人の言葉の命令」(記録 2-62 の「呼びかけ」に近い形)に従った率である。住民では、看板や頼みに人と同じくらい従うのが目標(2-62)なので、ASR が低いほど良いとは限らない。一方で区切りの記号の取り違え(人には起きない)は低いほど良い。この 2 つを分けて測った公開の値は見つけていない。
- 【見立て】HIPO の値は審査の LLM の採点で、別の審査では値が動く(付録の表 4 で Qwen3-1.7B の素の値は審査ごとに違う)。フロア(同じ条件の繰り返しの幅)は表 7 にあるが読めていない。

### 3-3 迎合と断りの率

**測り方の先例**: Sharma ほか 2023 の迎合(記録 2-62・R-149 の追補の問 9 の範囲)/人物の協調性と迎合の相関(Shah ほか・ACL 2026。0.6B〜20B の公開の 13 モデル・275 の人物・4,950 問で、13 のうち 9 モデルで協調性と迎合が有意に正の相関・最大 r=0.87・d=2.33=要旨 [S40] ○)/害の無い頼みを断る率(XSTest 250 問・OR-Bench=抜粋 [S42] △)。

**候補ごとの値**

| 名 | 迎合 | 断りすぎ | 出典 |
|---|---|---|---|
| Qwen3-8B | 抜粋に「迎合の率 16.5%(手当ての後 12.9%)」とあるが、論文の名と条件を確かめていない | 空欄 | [S41] △ |
| 前の世代の 8B 級(参考) | — | 害の無い頼みを断った率の平均: Llama-3.1-8B 28.53・Qwen2.5-7B 21.70・Ministral-8B(2410)18.44・Gemma-2-9B 13.46(RedBench の抜粋) | [S42] △ |
| ほかの候補 | 空欄(コミュニティの迎合の試験の頁は 404 で読めず=§8 の U1) | 空欄 | — |

- 【見立て】Shah ほかの結果は、人物の文(協調的な人物)が迎合を強めることを示す。住民の人物の書き方と迎合の率は一緒に測る必要がある。13 モデルの名は要旨に無く、候補の行には使えない。
- 安全と好みの学習が住民をどれだけ縛るか(断る向きを消す・Base と混ぜる)は R-149 の追補の問 8 の範囲で、本書では扱わない。

### 3-4 皆が同じになる癖(均質化)

**測り方の先例(引くだけ+足したもの)**: 人の答えのばらつきと指示調整の損の関係(SimBench・r=−0.942=R-149 §5-2)/AWQ の 4 ビットで Qwen3-8B の同じ答えの率が +5.1 ポイント(R-149 §5-2 [S19])/同じ住民に同じ場面を何度か出したときの一致を、人の答え直しの一致と比べる(記録 2-52)/1 つの問いに対して別々の質のよい答えをいくつ出せるか(NoveltyBench・20 モデル・人の書き手より少ない・同じ系統では大きいモデルほど少ないことが多い=要旨 [S43] ○)/モデルどうしの誤りの重なり(350 以上の LLM で、両方が誤ったときに同じ答えが 60%。作り手や構造が同じだと重なりが増え、大きく正確なモデルほど作り手が違っても重なる=要旨 [S44] ○)。

**候補ごとの値**: Qwen3-8B の AWQ の +5.1 ポイント(R-149)のほかは空欄。

### 3-5 毎回同じ答えを出せるか

**今の状態(2026-11-16 に読んだ)**

| 項目 | 状態 | 出典 |
|---|---|---|
| vLLM のバッチ不変の試験済みの一覧(latest・2026-11-04 の版・beta) | Qwen3 の密(0.6B・1.7B・4B・8B・4B-AWQ・8B-AWQ)・Qwen3-VL の 2B と 4B・gpt-oss-20b と 120b・Llama 3.1 と 3.2・Mistral-7B-v0.3・glm-4-9b-chat・Phi-3.5-mini・phi-4・Granite 3.1・EXAONE 4.0・OLMo 2 1B・ERNIE 4.5 0.3B・SmolLM2・Gemma 2 2B・PLaMo3 2B・Granite の SWA 2 本・LFM2-8B-A1B ほか。**Mamba・GDN・推測デコード・接頭辞のキャッシュには触れていない**。NVIDIA は compute capability 8.0 以上 | [S33] ◎ |
| Issue #42960(GDN でバッチ不変の設定が起動時に止まる) | **open**。11-02 に `batch-invariance` の印。11-04 の参照は文書の整理のコミットで直しではない。直ったと確かめられた版は無い(0.21.0・5 月の nightly・0.28.0 で失敗の報告) | [S31] ◎ |
| PR #45819(GDN のバッチ不変) | **open・未合流**。印は `batch-invariance`・`needs-rebase`・`v1`。11-06 に衝突。11-05 に作者が「デコードだけの束の速い道が 1 件ずつの道とビット単位で一致しない」原因を見つけて外し、Qwen3.5-0.8B の bs1 と bsN の一致の試験が通ったと書く。**11-12 の別の人の報告**: 0.33.0 に当てて Qwen3.8-27B(BF16・H200)で bs1 と bs16 はビット一致、ただし同じトークンをデコードで出した場合と前読みで採点した場合で 592 中 352 がずれた(0 層目の GDN の出力)。対象は Qwen の GDN(Qwen3-Next・Qwen3.5・Qwen3.6)だけで、Kimi・OLMo などは対象外。推測デコードは初期化で断る | [S32] ◎ |
| Mamba 混成(Nemotron JP など) | バッチ不変の文書に記述なし(R-147 §8 の U6 のまま)。Nemotron JP の札は `--mamba_ssm_cache_dtype float32` を付けるよう書く | [S33][S20] ◎ |

**候補ごとの見込み**

| # | 名 | 一覧に名があるか | 【見立て】構造から見た見込み |
|---|---|---|---|
| 0 | Qwen3-8B(AWQ) | ある | — |
| 10・11・13 | Qwen3-Swallow-8B・DeepSeek-R1-0528-Qwen3-8B・Qwen3-4B-2507 | 無い | Qwen3ForCausalLM で、一覧の Qwen3 と同じ構造。量子化の形(Swallow の AWQ)も一覧の Qwen3-8B-AWQ と同じ種類 |
| 1・2 | Qwen3.5-9B・4B | 無い | GDN なので、今の版では起動時に止まる(#42960)。PR #45819 が入っても、デコードと前読みのずれが 11-12 に報告されている |
| 3・4 | Gemma 4 | 無い(Gemma 2 2B だけ) | 窓つきの注意の混成。試験の記録なし |
| 5 | Ministral 3 8B | 無い(Mistral-7B-v0.3 だけ) | 試験の記録なし |
| 6・7 | Granite 4.1・4.2 8B | 無い(Granite 3.1 の密の 2B・8B はある) | 密の Transformer で 3.1 と同じ類と読めるが、構造の名が同じかは確かめていない |
| 8・9 | llm-jp-4 の 8B | 無い | llama 型で、一覧の Llama 3 系と同じ類と読める |
| 12 | Qwen3-VL-8B | 無い(2B と 4B はある) | 同じ系統の 2B・4B が一覧にある |
| 14 | Nemotron JP | 無い | Mamba-2 の混成で、文書に記述なし |

- 「何本余計に要るか」(記録 2-51 の統計の道の費用)を候補ごとに測った値は無い。dm_eval の `determinism_check` の `seeds_needed` は式が未定(dm-eval-11-01 README §6)。

### 3-6 速さと VRAM

5070 で測った値は、どの候補にも無い(5070 の用意はユーザーの UAC と再起動を待っている=返事その 8 §8)。下は札の大きさからの算術で、測定ではない。基準は R-123 の Qwen3-8B AWQ の重み 5,816 MiB(8.19B)=1B あたり約 710 MiB。

| # | 名 | 重みの見込み【見立て・算術】(約 10 GB の使える量の中に入るか) | KV/トークン(fp16) | 出典 |
|---|---|---|---|---|
| 0 | Qwen3-8B AWQ | 5,816 MiB(R-123 の値) | 147,456 B | R-123・R-142 |
| 1 | Qwen3.5-9B(文だけ・4 ビットなら) | 約 6,390 MiB。ただし公式の 4 ビットは無い | 32,768 B+1 本の列ごとに状態 約 50.3 MB(1,364 トークンの列で Qwen3-8B 201.1 MB に対し 95.0 MB) | R-147 §4-1・§6 |
| 3 | Gemma 4 12B(QAT w4a16) | 約 8,490 MiB。KV に残るのは 1.5 GB 前後【推測】 | 空欄(構成を読んでいない) | [S6][S8] |
| 4 | Gemma 4 E4B(QAT w4a16) | 実効 4.5B なら約 3,200 MiB・埋め込み込み 8B なら約 5,680 MiB(層ごとの埋め込みの置き方で変わる)【推測】 | 空欄 | [S7] |
| 5 | Ministral 3 8B(FP8) | 8.8B × 1 B で約 8,390 MiB。札は「FP8 で 12 GB に入る」 | 空欄 | [S10] |
| 6・7 | Granite 4.x 8B(FP8 / NVFP4) | FP8 で約 8.2〜8.6 GB・NVFP4 で約 4.8 GB【推測】。5070(sm_120)で vLLM が NVFP4・MXFP4 を動かすかは確かめていない | 163,840 B(40 層 × KV 8 × 頭の次元 128。頭の次元は 4.1 の札の 4,096÷32 から) | [S12][S13] |
| 8・9 | llm-jp-4 の 8B | BF16 で 16.0 GiB(入らない)。4 ビットにするなら約 6,100 MiB | 空欄(KV の頭の数が札に無い) | [S15][S16] |
| 10 | Qwen3-Swallow-8B AWQ | Qwen3-8B AWQ と同じ程度 | 147,456 B(同じ構造) | [S18] |
| 11 | DeepSeek-R1-0528-Qwen3-8B | BF16 で 15.3 GiB(入らない)。公式の 4 ビットなし | 147,456 B(同じ構造) | [S22] |
| 13 | Qwen3-4B-2507 | BF16 のままで約 7,670 MiB(入る)。4 ビットなら約 2,860 MiB | 空欄(構成を読んでいない) | [S30] |
| 14 | Nemotron JP | BF16 で約 16.8 GB(入らない)。公式の量子化は読んでいない | 空欄 | [S20] |

- 【見立て】考える形は 1 判断あたりの出力のトークンを増やすので、速さの比べは「考えない形」と「考える形」を別の行にする必要がある。Qwen3-Swallow は考えない形を持たない(§2-2)。
- 接頭辞のキャッシュ(共通の前置きの使い回し)は、GDN と Mamba では境目にだけ状態が置かれる実験の段の機能である(R-147 §4-3)。共通の B0 を使い回す今の形の速さが、全注意の模型と同じに出るとは限らない【見立て】。

### 3-7 物差しの軸のまとめ

| 軸 | 測り方の先例 | フロア(同じ条件の繰り返し・人どうしの幅) | 候補の公開の値 |
|---|---|---|---|
| 人らしさ | 負の対数尤度(Centaur)・SimBench の点・Park の正規化の一致・Cheung の偏り・人の評価の勝率 | Park は本人の答え直し(約 85%)。SimBench は人どうしのフロアを報告しない(R-149) | Qwen3-8B の HumanLM の 30.6% だけ |
| 上下を守る | 指示の階層の試験(IHEval・HIPO・Choose Sides)・道具の出力の注入(AgentDojo) | HIPO の表 7 は読めず。Dong ほかは試行数だけ | Qwen3-8B(2 本)・Qwen3.5-9B(1 本) |
| 迎合・断り | 迎合の試験・人物の協調性との相関・XSTest・OR-Bench | 空欄 | ほぼ空欄(Qwen3-8B の △ だけ) |
| 均質化 | SimBench のエントロピーとの関係・同じ答えの率・NoveltyBench・誤りの重なり・答え直しの一致(2-52) | AWQ の論文は作り直しの +4.4 ポイント(R-149) | Qwen3-8B の AWQ の +5.1 ポイントだけ |
| 毎回同じ答え | vLLM の試験済みの一覧・32 回の一致(dm_eval)・A/A の下限(2-51) | — | 一覧に Qwen3-8B と AWQ |
| 速さ・VRAM | 1 判断の秒・1 シム日あたりの GPU 時間(dm_eval の式) | — | 5070 の測定なし。算術の見込みだけ |
| 日本語 | Swallow v2・開発元の表・dm_eval の破綻率 | Swallow の繰り返しの幅は頁に無い | §2-2 |

## §4 問 3 判断モデルの第 1 世代(MD-22)の順の変わり方

### 4-1 今の物差しと今の値

- dm_eval の表の列(dm61 の 25 列+11-01 の 9 列)は、8B の logprob との一致(JSD・1 位の一致)・広がり(エントロピー)・位置の偏り(巡回・PBS)・決定論(32 回)・日本語の破綻率・VRAM・1 判断の秒である。「人のデータとの照合」は欄だけあり、「検証側のまま(値を入れない)」とされている([dm-eval-11-01 README](../bench/analysis/dm-eval-11-01/README.md) §4・§6、[dm61 README](../bench/analysis/wallbounce-1012/dm61/README.md) §決めたこと 1)。
- 候補のモデル(Clef-flash・Clef・Kev-9B・即断・(G))の行は、すべて「GPU の後で埋める」の空欄である。消費の場面について README は「直すまで (G) との一致を判断モデルの選定の根拠にしない」と書く(dm-eval-11-01 README の冒頭の注)。
- **つまり、今の物差しによる候補の順は、まだ 1 つも測られていない**。本節の「順の変わり方」は、学びの出どころと公開の値からの【見立て】である。

### 4-2 人の物差しを足すと順が動きうる理由(出典つき)

| # | 理由 | 根拠 | 等級 |
|---|---|---|---|
| a | 同じ系統の教師から学んだモデルは、Qwen3-8B と誤りがそろいやすい。「Qwen3-8B との一致」は、人に近いかとは別の理由で、Qwen の系統の教師の候補を押し上げうる【見立て】 | 作り手と構造が同じだと誤りの重なりが増える(350 以上の LLM)[S44] | ○ |
| b | 人の票の分布との一致では、候補の間で 4 倍を超える開きが出た例がある | ChaosNLI(1 問 100 人)での JSD: OpenDecider-small 0.040・large-td 0.030・本家 Jev 0.148・Laya 0.174(作者の測定・英語・人どうしのフロアは空欄) | R-94 §0 の 2 |
| c | 公開の点数の順と、見たことのない課題での順は入れ替わる | S1MB で bekko-400m は全体の 2 位、汎化の 6 ベンチでは 12 位(学びと評価で 77 の部分集合の名が重なる) | R-94 §0 の 3 |
| d | 「迷いが Qwen3-8B と合う」を良しとすると、Qwen3-8B の分布の狭さを受け継ぐ候補が上に来る。人の答えのばらつきが大きい場面では、指示調整したモデルの方が人から離れる【見立て】 | Qwen3-8B は考えなしで 0〜9 の 4 に 66.16%(R-149 [S2])・指示調整の損は人の答えのエントロピーと r=−0.942(R-149 [S18])・AWQ で +5.1 ポイント(R-149 [S19]) | 既存答申 |
| e | 「何もしない」の候補(MD-25 で必ず入れる)では、会話用に調整した LLM と人の間に、省略の偏りの差がある。指示調整した LLM の出力から学んだ候補はこの偏りを受け継ぎうる。人のラベルで学んだ候補は受け継がないかもしれない【見立て】 | 差は LLM 45%・人 5%。事前学習だけの Llama と Centaur には偏りが無かった(Cheung ほか 2025=R-149 §4-3) | 既存答申 |
| f | 命令文あり・なしの列(記録 2-61)は人の値と比べられる。判断モデルは選ぶだけなので記号の取り違えはほぼ起きないが、呼びかけへの反応のずれは測っていない | 人は理由つきの頼みに 93〜94%、理由なしで 60% 従った(Langer ほか 1978=記録 2-54) | 記録 |

### 4-3 候補ごとの学びの出どころと、動きうる向き【見立て】

学びの出どころは R-125 §3-1 の表のまま。右の 2 列は筆者の見立てで、測った値ではない。

| 候補 | 学びの出どころ(R-125・R-94) | 「Qwen3-8B との一致」での向き【見立て】 | 「人の判断との合い方」での向き【見立て】 |
|---|---|---|---|
| 即断 sokudan-ja-310m | 合成だけ。生成者は qwen3:30b-a3b-instruct-2507。日本語 | Qwen の系統の教師なので一致が高く出うる(理由 a) | 教師の指示調整の偏りを受け継ぎうる(理由 d・e)。日本語の人のデータでは未測定 |
| saihai-v1-310m | bekko v0 の 84 万判断+日本語 13 万判断(LLM-jp の生成 1.44 万を含む)・日本語 7 データの train | 教師の系統が混ざるので読めない | 日本語のデータの train を含むので、同じデータの試験で測ると汚れる(R-150 の重なりの注) |
| decider-0.8b | 教師 Qwen3.5-27B の書いたデータ+公開データ。英語だけ | 一致が高く出うる(理由 a) | 英語だけなので、日本語の場面では破綻率が先に効く |
| JevK5 4B / 2B | 教師 Qwen3.6-27B と GPT-6 Luna+人のラベル 30,052 件 | 一部は一致が高く出うる | 人のラベルの分だけ人に寄りうる |
| OpenJev(Alex)4B / 2B / 0.8B | 公開データを NLI に直したもの(人のラベル)。MMLU などの試験の分割も学びに入れた | 読めない | 人のラベルの元のデータと同じ試験で測ると汚れる |
| minojev | 既存のラベル(banking77・CLINC150・Amazon Polarity・GSM8K)8,000 件 | 読めない | 意図の分類の人のラベルで、日々の判断の分布とは種類が違う |
| JevForge-0.8B | Open-Jev 由来 14,842・一般 15,347・Mind2Web 5,811(人の Web の操作の記録) | 読めない | Mind2Web の分だけ人の操作に寄りうる |
| kev 4B / 0.8B | 公開データの元のラベル+合成+名の無い教師 2 本の一致した行 | 読めない | 読めない |
| laya 系 | 学びの資料の名なし | 読めない | R-94 で段階の第 1 水準を選ばない(0/300) |
| 参考: OpenDecider(R-94) | 温度で較正した LLM の教師 2 本の平均 | 読めない | ChaosNLI の人の票との JSD 0.030〜0.040(理由 b) |

- 【見立て】上の向きが当たるとすると、今の物差しでは「Qwen の系統の教師で学んだ候補」が上に来やすく、人の物差しでは「人のラベルか較正した教師の平均で学んだ候補」が上に来うる。どちらに転ぶかは測るまで分からない。

### 4-4 人の物差しに使えるデータ

| データ | 中身 | 言語 | 注 |
|---|---|---|---|
| ChaosNLI [S52] | SNLI・MNLI・αNLI の 4,645 問に 1 問 100 人の票(合計 464,500) | 英語 | 要旨は「人の意見が割れる問いで、最先端のモデルは偶然とほとんど変わらない」と書く。人どうしのフロアは要旨に無い |
| Psych-101 / Psych-201 | 心理の実験の人の試行ごとの選択 | 英語(推定) | R-150 §2-1。渋谷の物差しの錨と同じ実験が入っていれば、錨は独立でなくなる(R-150 §0 の 4) |
| SimBench | 20 のデータの人の答えの分布 | 多言語を一部含む | R-149 §5-2。枠は CC BY-NC-SA 4.0(R-149 §10) |
| Cheung ほか 2025 の場面 | 道徳の場面の「する/しない」の枠の入れ替え | 英語 | R-149 §4-3 |
| 頼みと看板の場面(Langer ほか 1978・Keizer ほか 2008) | 頼みに従う率・周りの様子で禁止の表示の効き目が変わる | 英語・オランダ | 記録 2-61 の dm_eval の新しい列の材料(返事その 8 §6-2) |
| 日本語で 1 問に多数の人の票があるデータ | — | — | 検索 1 回で見つからなかった(§8 の U9) |

- 【見立て】人のデータで判断モデルを「選ぶ」ことは、学ばせなくても較正の一種になりうる。主張の文は「人の行動データによる較正なし」で(R-150 §1)、選ぶのに使ったデータは答え合わせに使えない(2-26・2-44 の 2 つの組の台帳)。どのデータを選ぶ側に置くかは、ユーザーの決める題(§7 の T7)。

## §5 問 4 「1 つにする・ランごとに並べる・住民ごとに混ぜる」の先例

### 5-1 先例の表

| 先例 | 形 | 何をしたか | 結果 | 限界 | 等級 |
|---|---|---|---|---|---|
| Schoenegger・Tuminauskaite・Park・Tetlock「Wisdom of the Silicon Crowd」Sci. Adv. 10(45) eadp1528(2024)[S46] | 並べて平均する | 12 個の LLM の予測をまとめ、予測の大会の 925 人と 31 の二択の問いで比べた | 事前登録の分析で人の集団と統計的に差が無く、中くらいの効果の幅で同等。LLM の平均は 50% より有意に高く出た(「はい」の偏り)。人の中央値を見せると GPT-4 と Claude 2 は 17〜28% 良くなったが、人と機械の単純な平均に負けた | 予測の値の集約で、住民の集団の振る舞いではない | ○(要旨・書誌は Crossref で確かめた) |
| Bommasani・Creel・Kumar・Jurafsky・Liang「Picking on the Same Person」NeurIPS 2022 [S45] | 部品の共有 | 公平さの試験で、学びのデータや土台のモデルを共有したとき、同じ人が全部の判断者から不利を受けるか(結果の均質化) | 学びのデータの共有は均質化を確実に強めた(人の単位の方が群の単位より大きい)。土台のモデルの共有は結果がまちまちで、調整の仕方で大きく変わった | 判断の結果の均質化で、住民の多様さとは定義が違う | ○ |
| Kim・Garg・Peng・Garg「Correlated Errors in Large Language Models」ICML 2025 [S44] | モデルを替える効き目 | 350 以上の LLM の誤りの重なり | 両方が誤ったときに同じ答えが 60%。作り手と構造の共有で重なりが増え、大きく正確なモデルほど作り手が違っても重なる | 正解のある課題の誤り | ○ |
| Savcisens・Dies・Maynard・Eliassi-Rad(arXiv 2607.27512 v2・未査読)[S48] | 住民ごとに混ぜる/人物の役 | Llama-3 の 8B を 15 体(一般 1・専門の微調整 14)。48 体の網(2 つの形 × 16)・医療の 20 の文・10 回の更新・2,560 ラン | 人物の役(I→II)は、本人の考えの改め方を変えたが、全体の合意の変化はほぼ変えなかった(−0.01 → 0.03/0.04・d=0.41・p=.066)。専門のモデルを混ぜる(II→III)と合意の変化が 0.19/0.17・d=1.41 と大きく動いた。混ぜた集団にだけ、外への影響の持続した偏り(体ごとの ICC 5.75%・2.95%)が出た。同じモデル+同じ前置きでは最初の考えが全員同じ。著者は人物の名札を「同じ考えの源の名を替えるだけ」と書く | 全員が Llama-3 の 8B の派生。英語の医療の文。I の全部と II の 65% は最初から合意が最大(表 A13) | ◎(§4〜§6・前の 10 万字) |
| Bück-Kaeffer ほか「The Silicon Society Cookbook」(arXiv 2605.00197・COLM 2026 審査中)[S49] | 土台の選び方・LoRA の混ぜ方 | 土台 4 つ(Minitaur-8B・Llama-3.1-8B・Qwen2.5-7B-Instruct・gemma-3-4b-pt)に人物の群ごとの LoRA 25 個。設計の変数の分散分析 | **土台の LLM が結果に最も効く変数**(η²=0.266〔BERT の正解率〕・0.090〔合意の変化〕)。LoRA 25 個を SimBench の人の分布に合わせて重みづけで混ぜると 17.08(平均の答えに合わせると 17.05)で、単独の最良 14.60 を上回った | 混ぜたのは同じ土台の LoRA で、土台の違うモデルではない。重みを合わせたのと同じ試験で測った(保持の分割の記述なし)。著者は SimBench の点と意見の動きの量の相関は見えないと書く | ◎(§3.2・§4・§5.5) |
| Tebaldi & Knutti「The use of the multi-model ensemble in probabilistic climate projections」Phil. Trans. R. Soc. A 365(2007)[S50] | ランごとに並べる(気候) | 多くの気候モデルを同じ実験で回した束 | 束は初期値・パラメータ・構造の不確かさを含む。モデルどうしが独立でないこと・偏りと調整・「手近なモデルの束」の解釈の難しさを論じる | 抜粋だけ | △ |
| Prompts to Proxies(arXiv 2509.11311)[S51] | 少数の代理の束 | L1 で絞った代理の束の重みづけで、調査の答えの分布に合わせる | (抜粋のみ) | 抜粋だけ | △ |
| Hawkins & Sutton 2009 | ランごとに並べる(気候) | — | 記録 2-56・2-64 が引くが、原文は読めていない(記録 2-56 の注) | 未読 | — |

### 5-2 3 つの形への写し方【見立て】

| 形 | 先例が支える点 | 先例が示す危うさ | 本書で埋められなかった点 |
|---|---|---|---|
| 1 つにする | 再現が単純(厳密モードの条件をそろえやすい=2-51) | 土台の LLM が結果に最も効く変数だった [S49]。1 つだと、その土台の偏りを「モデルの源の揺れ」として測れない | — |
| (B) ランごとに並べる | 気候の束(△)。LLM の予測の束の平均が人の集団に並んだ [S46] | 作り手や構造が同じモデルは誤りがそろう [S44] ので、並べたモデルの幅は構造の不確かさを小さく見せうる。本数がモデルの数だけ増える(2-57) | 住民の集団の振る舞いで、土台の違うモデルを並べた先例は見つけていない |
| (A) 住民ごとに混ぜる | 混ぜると最初の考えのばらつきが出て、全体の動きが大きく変わった [S48]。LoRA を人の分布に合わせて混ぜると SimBench の点が上がった [S49] | 混ぜた集団では「どのモデルか」が外への影響の差として残った [S48](2-64 の「人の性質でないものが住民の違いに混ざる」心配と同じ向き)。学びのデータの共有は均質化を強める [S45] ので、同じデータの派生を混ぜても幅は広がりにくい | 土台の違う公開モデルを住民ごとに混ぜた社会シミュの値は見つけていない。5070 の 12 GB で 8B 級の 4 ビットを 2 つ同時に載せると、重みだけで約 11,600 MiB(Qwen3-8B AWQ の 5,816 MiB の 2 倍)になり、使える約 10 GB を超える【見立て・算術】 |

## §6 比較の表(住民の LLM の候補 × 軸)

値は §2・§3 から写した。「—」は値なし、「空」は調べたが見つからない。推薦の順ではなく、§2-1 の番号の順。

| # | 名 | 条件(公式・ライセンス・大きさ・日本語) | 日本語平均(Swallow) | 考える形 | 公式の低ビット | バッチ不変の一覧 | 上下を守る(HIPO の食い違う組) | 注入の ASR(Dong ほか表 3) | 人らしさ | 迎合・断り | 均質化 | 重みの見込み | 取得の許可 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | Qwen3-8B | 全部に入る | 0.491 | 切替+文ごと | AWQ | ある | 0.60 / 0.27 | 47.2 | HumanLM 30.6% | △ 16.5% | AWQ +5.1 pt | 5.8 GB | 内 |
| 1 | Qwen3.5-9B | 入る(日本語の名は札に無い) | 0.534 | 切替 | 無い | 無い(GDN で止まる) | — | 43.2 | 空 | 空 | 空 | 約 6.4 GB(4 ビットにすれば) | 内(量子化は別) |
| 3 | Gemma 4 12B | 境目の大きさ・日本語の名なし | 表に無い | 切替 | QAT w4a16 | 無い | — | —(31B は 6.9) | 空 | 空 | 空 | 約 8.5 GB | 外 |
| 4 | Gemma 4 E4B | 入る・日本語の名なし | 0.484 | 切替 | QAT w4a16 | 無い | — | — | 空 | 空 | 空 | 約 3.2〜5.7 GB | 外 |
| 5 | Ministral 3 8B | 入る | 表に無い | 別の重み | FP8 | 無い | — | — | 空 | 空 | 空 | 約 8.4 GB(FP8) | 外 |
| 6 | Granite 4.2 8B | 入る | 表に無い | 切替 | FP8・NVFP4・MXFP4 | 無い(3.1 はある) | — | — | 空 | 空 | 空 | 約 4.8〜8.6 GB | 外 |
| 7 | Granite 4.1 8B | 入る | 表に無い | 記述なし | FP8 | 無い(3.1 はある) | — | — | 空 | 空 | 空 | 約 8.2〜8.6 GB | 外 |
| 8 | llm-jp-4.1-8b-thinking | 入る | 表に無い(4 は 0.448) | 努力の段だけ | GGUF だけ | 無い | — | — | 空 | 空 | 空 | 4 ビットなら約 6.1 GB | 外 |
| 9 | llm-jp-4-8b-instruct | 入る | 表に無い | 考えない版 | GGUF は第三者 | 無い | — | — | 空 | 空 | 空 | 同上 | 外 |
| 10 | Qwen3-Swallow-8B-RL | 入る(Qwen3 の派生) | 0.510 | 常に考える | AWQ-INT4 | 無い(同じ構造はある) | — | — | 空 | 空 | 空 | 約 5.8 GB | 外 |
| 11 | DeepSeek-R1-0528-Qwen3-8B | 入る(MIT・日本語の記述なし) | 表に無い | 記述なし | 無い | 無い(同じ構造はある) | — | — | 空 | 空 | 空 | BF16 15.3 GB | 外 |
| 12 | Qwen3-VL-8B-Instruct | 入る(日本語は読んでいない) | 表に無い | 別の重み | 読んでいない | 無い(2B・4B はある) | — | — | 空 | 空 | 空 | BF16 16.3 GB | 内 |
| 13 | Qwen3-4B-Instruct-2507 | 4B | 表に無い | 別の重み【推測】 | 読んでいない | 無い(Qwen3-4B はある) | — | — | 空 | 空 | 空 | BF16 7.5 GB | 内 |
| 14 | Nemotron JP 9B | ライセンスは要判断 | 0.503 | 切替 | 読んでいない | 無い(Mamba) | — | — | 空 | 空 | 空 | BF16 16.8 GB | 外 |

- HIPO と Dong ほかの値は英語の課題で、審査の LLM や攻撃の組の選び方で動く。人らしさ以下の空欄は、5070 と dm_eval で測るまで埋まらない見込み【見立て】。

## §7 壁打ちで決める題(推薦は書かない)

| # | 題 | 選択肢の例 | 材料 |
|---|---|---|---|
| T1 | 候補の幅 | `Qwen/` の公式だけ/他の発行元も(取得の許可の追加が要る)/日本語で微調整した派生(Swallow・llm-jp)も | §1-2・§2-4 |
| T2 | 「Apache-2.0 と同等」の線 | MIT まで/NVIDIA などの独自のライセンスも個別に読む | §1-3・§2-1 #14 |
| T3 | 考える形の扱い | 考えない形で比べる/考える形も別の行で/常に考えるモデル(Swallow)は外すか | §2-2・§3-6 |
| T4 | 量子化の扱い | 公式の低ビットがあるものだけ/自前で量子化(重みの加工に当たるかの確認)/FP8 も | §2-4・R-149 の AWQ の縮み |
| T5 | 毎回同じ答えが出せないモデル | 統計の道で本数を記録(2-51)/PR #45819 の合流を待つ/GDN と Mamba は外す | §3-5 |
| T6 | 上下を守る力の物差し | 公開の試験(IHEval・HIPO の形)を日本語に直す/住民の場面で「区切りの記号」と「人の言葉の呼びかけ」を分けて測る | §3-2 の見立て |
| T7 | 判断モデルの選定に人のデータを使うか | 使わない(今のまま)/英語の公開データで参考に並べる/選ぶ側の組と答え合わせの組を台帳で分けて使う | §4-4 |
| T8 | 判断モデルの「迷いの合い方」の基準 | Qwen3-8B に合わせる/人の分布に合わせる/両方の列を並べる | §4-2 の d |
| T9 | 1 つにするか・並べるか・混ぜるか | 1 つ/(B) ランごと/(A) 住民ごと(腕)。並べるならモデルの選び方(作り手や構造の違うものを入れるか) | §5 |
| T10 | 5070 で測る順 | 日本語の破綻率 → 決定論 → 速さと VRAM → 上下 → 人らしさ、など | §3-7 |

## §8 読めなかったもの

| # | 何が | 理由 | 本書への影響 |
|---|---|---|---|
| U1 | コミュニティの迎合と作り話の試験(HalBench)の紹介の頁 | 404。断られたのではない。Reddit や Space などの別の経路では取りに行っていない | 候補の迎合の値は空欄。抜粋の値も使っていない |
| U2 | Dong ほか(arXiv 2608.02657)の HTML の 10 万字より後(付録 D の表 11=組ごとの全体の ASR) | 2 回目の読み込みが道具の側の内容の検査で止まった。サイトの拒否ではない。取り直していない | 全体の ASR(抜粋の「Qwen3-8B 24.1%」)は本文に使わず、表 3 の難しい組の値だけを使った |
| U3 | HIPO の 10 万字より後(表 7 の 95% 区間) | 道具が 1 回 10 万字まで | フロアは空欄 |
| U4 | 2607.27512 の 10 万字より後(付録の一部) | 同上 | 本文の §4〜§6 の値だけを使った |
| U5 | Qwen3-Swallow と llm-jp-4.1 の札の Swallow の値 | 札では画像だけ | 4.1 の第三者の値は空欄 |
| U6 | Nejumi の順位表 4 | 読んでいない(動的な頁と【推測】) | Nemotron の札が引く値だけ |
| U7 | Gemma 4 12B・Ministral 3・Granite 4.x・llm-jp-4.1・DeepSeek-R1-0528-Qwen3-8B・Qwen3-VL-8B・Apertus の第三者の日本語の値 | Swallow v2 の表に無い | §2-2 の空欄 |
| U8 | 候補ごとの人らしさ・迎合・断り・均質化の値 | 検索 3 回で見つからなかった | §6 の空欄 |
| U9 | 日本語で 1 問に多数の人の票があるデータ | 検索 1 回で見つからなかった | §4-4 の空欄 |
| U10 | ChaosNLI の人どうしのフロア | 要旨に無い。本文は読んでいない | R-94 の空欄 5 のまま |
| U11 | Hawkins & Sutton 2009 の原文 | 読んでいない(記録 2-56 の注のまま) | §5-1 の行は空 |
| U12 | Tebaldi & Knutti・Prompts to Proxies・SEP・RedBench の本文 | 時間の都合で抜粋で止めた | 該当の行は △ |
| U13 | Nemotron JP・Qwen3-4B-2507・Qwen3-VL-8B の公式の量子化・Qwen3.5-4B と Qwen3.8-27B のライセンスの欄 | 読んでいない | §2-4 の空欄 |
| U14 | Gemma 4・Ministral 3・Granite 4.x・llm-jp-4 の vLLM での動作とバッチ不変 | 試験済みの一覧に無い。構造の名の一致は確かめていない | §3-5 の見込みは【見立て】 |
| U15 | 5070 での速さ・VRAM の実測 | 5070 の用意の前 | §3-6 は算術だけ |
| U16 | 調べていない発行元(openbmb・tencent・XiaomiMiMo・kakaocorp・LGAI-EXAONE・zai-org・baidu・CohereLabs・LiquidAI・rakuten・cyberagent・elyza・stockmark ほか) | 時間の都合。LiquidAI・tencent・LGAI-EXAONE・CohereLabs の小さなモデルは既存答申で独自か非商用のライセンスと記録されているものがある(R-94・R-147)が、今回は読み直していない | §2-1 の漏れがありうる |
| U17 | Shah ほか(ACL 2026)の 13 モデルの名と率 | 要旨の頁だけ読んだ | §3-3 の候補の行に使えない |

Web の道具は上限に当たらなかった。403・robots・規約で断られた頁は無かった。

## §9 出典の表

| # | 出典 | URL | 読んだ範囲 | 等級 |
|---|---|---|---|---|
| S1 | Hugging Face API: Qwen の組織のモデル(作成日の新しい順に 100 件) | https://huggingface.co/api/models?author=Qwen&sort=createdAt&direction=-1&limit=100 | id と createdAt の全件 | ◎ |
| S2 | `Qwen/Qwen3.5-9B` の札 | https://huggingface.co/Qwen/Qwen3.5-9B | ライセンス・構造・言語・考える形・vLLM・多言語と指示の値 | ◎ |
| S3 | `Qwen/Qwen3.8-Flash-Next` の札 | https://huggingface.co/Qwen/Qwen3.8-Flash-Next | 大きさ・構造・ライセンス・考える形 | ◎ |
| S4 | `Qwen/Qwen3-8B` の札と API | https://huggingface.co/Qwen/Qwen3-8B | ライセンス・大きさ・言語・切り替え・createdAt | ◎ |
| S5 | Hugging Face API: google の gemma(60 件) | https://huggingface.co/api/models?author=google&search=gemma&sort=createdAt&direction=-1&limit=60 | id と createdAt | ◎ |
| S6 | `google/gemma-4-12B-it` の札 | https://huggingface.co/google/gemma-4-12B-it | ライセンス・大きさ・構造・言語・考える形・MMMLU・IFBench | ◎ |
| S7 | `google/gemma-4-E4B-it` の札 | https://huggingface.co/google/gemma-4-E4B-it | ライセンス・大きさ・構造・考える形・MMMLU | ◎ |
| S8 | `google/gemma-4-12B-it-qat-w4a16-ct` の札 | https://huggingface.co/google/gemma-4-12B-it-qat-w4a16-ct | 形式・vLLM 向けの記述・ライセンス | ◎ |
| S9 | Hugging Face API: mistralai(50 件) | https://huggingface.co/api/models?author=mistralai&sort=createdAt&direction=-1&limit=50 | id と createdAt | ◎ |
| S10 | `mistralai/Ministral-3-8B-Instruct-2512` の札 | https://huggingface.co/mistralai/Ministral-3-8B-Instruct-2512 | ライセンス・大きさ・言語・考える版・FP8・vLLM・値 | ◎ |
| S11 | Hugging Face API: ibm-granite の granite-4(60 件) | https://huggingface.co/api/models?author=ibm-granite&search=granite-4&sort=createdAt&direction=-1&limit=60 | id と createdAt | ◎ |
| S12 | `ibm-granite/granite-4.2-8b` の札 | https://huggingface.co/ibm-granite/granite-4.2-8b | ライセンス・構造・言語・考える形・vLLM・値・発表日 | ◎ |
| S13 | `ibm-granite/granite-4.1-8b` の札 | https://huggingface.co/ibm-granite/granite-4.1-8b | ライセンス・構造・言語・値・発表日 | ◎ |
| S14 | Hugging Face API: llm-jp の llm-jp-4(50 件) | https://huggingface.co/api/models?author=llm-jp&search=llm-jp-4&sort=createdAt&direction=-1&limit=50 | id と createdAt | ◎ |
| S15 | `llm-jp/llm-jp-4.1-8b-thinking` の札 | https://huggingface.co/llm-jp/llm-jp-4.1-8b-thinking | ライセンス・大きさ・考える形・vLLM・日本語の値 | ◎ |
| S16 | `llm-jp/llm-jp-4-8b-instruct` の札 | https://huggingface.co/llm-jp/llm-jp-4-8b-instruct | ライセンス・考えない版の記述・値 | ◎ |
| S17 | Hugging Face API: tokyotech-llm(40 件) | https://huggingface.co/api/models?author=tokyotech-llm&sort=createdAt&direction=-1&limit=40 | id と createdAt | ◎ |
| S18 | `tokyotech-llm/Qwen3-Swallow-8B-RL-v0.2` の札 | https://huggingface.co/tokyotech-llm/Qwen3-Swallow-8B-RL-v0.2 | ライセンス・考える形・言語・AWQ・発表日 | ◎ |
| S19 | Swallow LLM Leaderboard v2(事後学習) | https://swallow-llm.github.io/leaderboard/index-post.ja.html | 2B〜20B 級の行 | ◎ |
| S20 | `nvidia/NVIDIA-Nemotron-Nano-9B-v2-Japanese` の札 | https://huggingface.co/nvidia/NVIDIA-Nemotron-Nano-9B-v2-Japanese | ライセンス・構造・考える形・vLLM・発表日・Nejumi の表 | ◎ |
| S21 | Hugging Face API: sbintuitions(30 件) | https://huggingface.co/api/models?author=sbintuitions&sort=createdAt&direction=-1&limit=30 | id と createdAt | ◎ |
| S22 | `deepseek-ai/DeepSeek-R1-0528-Qwen3-8B` の API と札 | https://huggingface.co/deepseek-ai/DeepSeek-R1-0528-Qwen3-8B | createdAt・ライセンス・大きさ・構造・考える形・値 | ◎ |
| S23 | Hugging Face API: pfnet(25 件) | https://huggingface.co/api/models?author=pfnet&sort=createdAt&direction=-1&limit=25 | id と createdAt | ◎ |
| S24 | Hugging Face API: allenai の Olmo-3(30 件) | https://huggingface.co/api/models?author=allenai&search=Olmo-3&sort=createdAt&direction=-1&limit=30 | id と createdAt | ◎ |
| S25 | Hugging Face API: meta-llama(25 件) | https://huggingface.co/api/models?author=meta-llama&sort=createdAt&direction=-1&limit=25 | id と createdAt | ◎ |
| S26 | Hugging Face API: microsoft の phi(25 件) | https://huggingface.co/api/models?author=microsoft&search=phi&sort=createdAt&direction=-1&limit=25 | id と createdAt | ◎ |
| S27 | `openai/gpt-oss-20b` の札 | https://huggingface.co/openai/gpt-oss-20b | ライセンス・大きさ・メモリの記述・考える量 | ◎ |
| S28 | `swiss-ai/Apertus-8B-Instruct-2509` の API | https://huggingface.co/api/models/swiss-ai/Apertus-8B-Instruct-2509 | createdAt・ライセンス・言語の印・大きさ | ◎ |
| S29 | `Qwen/Qwen3-VL-8B-Instruct` の API | https://huggingface.co/api/models/Qwen/Qwen3-VL-8B-Instruct | createdAt・ライセンス・大きさ・構造 | ◎ |
| S30 | `Qwen/Qwen3-4B-Instruct-2507` の API | https://huggingface.co/api/models/Qwen/Qwen3-4B-Instruct-2507 | createdAt・ライセンス・大きさ・構造 | ◎ |
| S31 | vLLM Issue #42960「Batch-invariant support for GDN_ATTN」 | https://github.com/vllm-project/vllm/issues/42960 | 本文・コメント・印(2026-11-16 に読んだ) | ◎ |
| S32 | vLLM PR #45819「Add batch invariance support to GDN_ATTN backend」 | https://github.com/vllm-project/vllm/pull/45819 | 状態・履歴・コメント(同上) | ◎ |
| S33 | vLLM「Batch Invariance」(latest・2026-11-04 の版) | https://docs.vllm.ai/en/latest/features/batch_invariance.html | 試験済みの一覧・条件・制限 | ◎ |
| S34 | Wallace E. ほか「The Instruction Hierarchy」arXiv 2404.13208 | https://arxiv.org/abs/2404.13208 | 要旨 | ○ |
| S35 | Zhang Z. ほか「IHEval」arXiv 2502.08745・NAACL 2025 | https://arxiv.org/abs/2502.08745 | 要旨 | ○ |
| S36 | Chen K. ほか「HIPO: Instruction Hierarchy via Constrained Reinforcement Learning」arXiv 2603.16152(審査中) | https://arxiv.org/html/2603.16152v1 | HTML の前の 10 万字(表 1・付録 E) | ◎ |
| S37 | Balp-Straffon E. ほか「How Language Models Choose Sides」ICML 2026 の工房 | https://icml.cc/virtual/2026/79477 | 要旨 | ○ |
| S38 | Dong J. ほか「Your Agentic LLMs Secretly Encode Indirect Prompt-Injection Exposure in Hidden States」arXiv 2608.02657 v2 | https://arxiv.org/html/2608.02657 | 要旨と HTML の前の 10 万字(表 3・§5.3) | ◎ |
| S39 | Zverev E. ほか「Can LLMs Separate Instructions From Data?」ICLR 2025(SEP) | https://arxiv.org/abs/2403.06833 | 検索の抜粋 | △ |
| S40 | Shah A., Mishra D., Silpasuwanchai C.「Too Nice to Tell the Truth」ACL 2026 Long: 30788–30801 | https://aclanthology.org/2026.acl-long.1421/ | 要旨 | ○ |
| S41 | Qwen3-8B の迎合の率(OPCT の行・論文の名は未確認) | (検索の結果の要約に出た表の行) | 検索の抜粋 | △ |
| S42 | RedBench(arXiv 2601.03699)・ORFuzz(arXiv 2508.11222)の断りすぎの値 | https://arxiv.org/abs/2601.03699 | 検索の抜粋 | △ |
| S43 | Zhang Y. ほか「NoveltyBench」arXiv 2504.05228 | https://arxiv.org/abs/2504.05228 | 要旨 | ○ |
| S44 | Kim E., Garg A., Peng K., Garg N.「Correlated Errors in Large Language Models」ICML 2025・arXiv 2506.07962 | https://arxiv.org/abs/2506.07962 | 要旨 | ○ |
| S45 | Bommasani R. ほか「Picking on the Same Person」NeurIPS 2022・arXiv 2211.13972 | https://arxiv.org/abs/2211.13972 | 要旨 | ○ |
| S46 | Schoenegger P., Tuminauskaite I., Park P.S., Tetlock P.E.「Wisdom of the silicon crowd」Sci. Adv. 10(45): eadp1528(2024)・arXiv 2402.19379 | https://doi.org/10.1126/sciadv.adp1528 | arXiv の要旨。書誌は Crossref の API で確かめた | ○ |
| S47 | (欠番) | — | — | — |
| S48 | Savcisens G., Dies S., Maynard C., Eliassi-Rad T.「Belief Coevolution in a Social Network of Generalist and Specialist Large Language Models」arXiv 2607.27512 v2 | https://arxiv.org/html/2607.27512v2 | 要旨と HTML の前の 10 万字(§4〜§6・図 3〜5・表 A13・A17) | ◎ |
| S49 | Bück-Kaeffer A. ほか「The Silicon Society Cookbook」arXiv 2605.00197(COLM 2026 審査中) | https://arxiv.org/html/2605.00197 | 要旨と §3.2・§4(表 1)・§5.5(表 7)・付録 A | ◎ |
| S50 | Tebaldi C., Knutti R.「The use of the multi-model ensemble in probabilistic climate projections」Phil. Trans. R. Soc. A 365(1857): 2053–2075(2007) | https://doi.org/10.1098/rsta.2007.2076 | 検索の抜粋 | △ |
| S51 | 「Prompts to Proxies: Emulating Human Preferences via a Compact LLM Ensemble」arXiv 2509.11311 | https://arxiv.org/abs/2509.11311 | 検索の抜粋 | △ |
| S52 | Nie Y., Zhou X., Bansal M.「What Can We Learn from Collective Human Opinions on Natural Language Inference Data?」EMNLP 2020・arXiv 2010.03532 | https://arxiv.org/abs/2010.03532 | 要旨 | ○ |
| S53 | 日本語の多数の票のデータの検索(結果なし) | — | 検索の抜粋 | △ |
| S54 | 候補の人らしさの値の検索(SimBench・SocioBench の抜粋だけ・候補の行なし) | — | 検索の抜粋 | (数に含めない=R-149 の S18 を引く) |
| S55 | HalBench の紹介の頁 | https://techyon.pages.dev/(個別の頁) | 404 | 読めず |

- 数: ◎ 37(S1〜S33・S36・S38・S48・S49)・○ 9(S34・S35・S37・S40・S43・S44・S45・S46・S52)・△ 6(S39・S41・S42・S50・S51・S53)。S47 は欠番、S54 は数に含めない、S55 は読めず。
- 親に確かめてほしい数値: [S19] の Qwen3.5-9B 0.534・Qwen3-Swallow-8B-RL 0.510・Nemotron JP 0.503・Gemma 4 E4B 0.484/[S36] 表 1 の Qwen3-8B 0.60/0.27/[S38] 表 3 の Qwen3-8B 47.2・Qwen3.5-9B 43.2/[S48] の d=1.41 と d=0.41(p=.066)/[S49] の η² 0.266・0.090 と 17.08・14.60/[S32] の PR の状態(open・needs-rebase)と 11-12 の 352/592。

## 親の一次確認

第347・2026-11-16・親(Fable 5.2)。

| 主張 | 確かめ方 | 結果 |
|---|---|---|
| Swallow v2 の日本語平均は Qwen3.5-9B 0.534・Qwen3-Swallow-8B-RL 0.510・Nemotron JP 0.503・Qwen3-8B 0.491・Gemma 4 E4B 0.484・llm-jp-4-8b-thinking 0.448(§0 の 2・[S19]) | 親が [S19] の頁を WebFetch で読んだ | 合う(6 つとも表の値のまま) |
| Qwen3-8B は食い違う組で前置きを守った率 0.60・利用者への有用さ 0.27(§0 の 6・[S36] 表 1) | 親が arXiv 2603.16152v1 の HTML を WebFetch で読んだ | 合う(Conflicting Split・Base の行・QW-8B の列=0.60/0.27。そろう組は 0.67/0.37) |
| AgentDojo の難しい組の攻撃の成功率は Qwen3-8B 47.2・Qwen3.5-9B 43.2・gpt-oss-20B 44.0(§0 の 6・[S38] 表 3) | 親が arXiv 2608.02657 の HTML を WebFetch で読んだ | 合う(防御なしの行)。原典の言い方は「保留しておいた banking と travel の組の、最も難しい 8 つの格子点」 |
| 人物の役は全体の合意をほとんど変えず、別のモデルを混ぜると大きく動いた(d=1.41 と d=0.41・p=.066。§0 の 8・[S48]) | 親が arXiv 2607.27512v2 の HTML を WebFetch で読んだ | 数値は合う(役の付与 I→II が d=0.41・p=.066、専門のモデルの導入 II→III が d=1.41)。§0 の「15 体の実験」は写しの誤り=15 はモデルの種類の数で、1 つの網は 48 体(§5 の表の行は合っている)。§0 の文に親の訂正を入れた |
| [S49] の η² 0.266・0.090 と 17.08・14.60 | 確かめていない | 未確認 |
| 断られた頁を別の名乗り・経路・ミラー・キャッシュで読んでいないこと | 答申の取り方の注と §8(読めなかったもの)を読んだ | 403 や robots で断られた頁は無いと書かれている。404 の頁(HalBench の紹介)と、道具の内容の検査で止まった 2 回目の読み込みは、取り直していないと書かれている。その頁の内容は本文に入っていない |
| `Qwen/` 以外の重みは今の取得の許可の外(§0 の 4) | 親が CLAUDE.md §7 の 11-01 の項を読んだ | 合う(住民の LLM は `Qwen/` の公式リポ・判断モデルは各モデルの公式リポ・safetensors のみ) |
