<!-- hdr:v1 | 等級: B(第346 親の一次確認=末尾の表) | 作成: 2026-11-09 | 範囲: 返事その 7(11-09)§6-2 の R-141 の追補・記録 2-32 -->
# R-141 の追補: Qwen3-8B 用の公開の特徴の辞書(スパースオートエンコーダ・SAE)と、性格の向き(persona vectors)の取り出し方の手順

- **分野**: 自然言語処理・機械学習 #27 / 人格心理学 #13 / ソフトウェア工学 #29 | **重要度**: 発注文に記載なし([返事その 7(11-09)](../design/prompt-2026-11-09-reply7.md) §6-2。記録 [2-32](../reference/wallbounce-record-2026-11-02_05.md) の「特徴の辞書(Qwen3-8B 用があるかは要確認)」)
- **一次確認**: B(第346・親=末尾の表)。筆者がこの回に読んだ出典は 17 本(◎ 11・○ 2・△ 4)。既存答申からの引用は 5 本(R-141・R-142・R-126・R-123・R-148)。読めなかったものは §7 に挙げた。
- **索引**: [INDEX.md](INDEX.md)(索引の行の追加は親が行う) ・ **元の答申**: [R-141](v2-r141-persistent-state-vectors-and-steering.md)(本書は元の答申を 1 バイトも変えていない)

> 作成 2026-11-09・リサーチ役(Opus 5.5)。子サブは起動していない。Web は WebFetch と WebSearch で読むだけで、**上限には当たっていない**。curl は使っていない。**重みは 1 つも取得していない**(Hugging Face はモデルカード・API の JSON・設定と評価の小さな JSON・LICENSE の文だけを読んだ)。pip・clone はしていない。リポにも data/ にも何も保存していない。封印の層には触れていない。コード・台帳・設計書・INDEX・元の答申は変えていない。commit も git add もしていない。発注文が開かないと定めた文書(IMPLEMENTED.md・build-report-C7*/C8*・G1 のバックテストの計画・パターン台帳・data/ の下)は開いていない。
> **取り方の注**: arxiv.org と huggingface.co は robots.txt を先に読んだ(arXiv は `/abs`・`/html` を許し、Hugging Face は全体を許す)。GitHub は robots.txt を読まずに WebFetch でリポの頁だけ読んだ。WebFetch は頁を小さなモデルが要約して返す道具なので、◎ の数値と引用は「返ってきた文」である。長い HTML は 10 万字ごとに区切って読み、末尾を読み残したものは §7 に書いた。断られた頁は無い。
> 等級: ◎=原典か公式の文書・ソース・カードの本文を読んだ/○=要旨だけ/△=検索の抜粋だけ。筆者の組み立ては【見立て】、根拠の無い置き方は【推測】と書く。**推薦は書かない**。決めるのはユーザー。

## §0 要旨

1. Qwen3-8B 用の公開の特徴の辞書はある。公式は Qwen の Qwen-Scope で、Qwen3-8B 用は `Qwen/SAE-Res-Qwen3-8B-Base-W64K-L0_50` と `..._L0_100` の 2 本である。どちらも **Base のモデル**で学び、全 36 層の残差(各層の出力)・幅 65,536(16 倍)・TopK(k=50 か 100)である [S1][S2][S3]。リポの作成は 2026-04-27、論文(arXiv 2605.11887)は 2026-05-12 [S1][S5]。
2. L0_50 の版は commit `9b7d647…`(2026-05-13)で、1 層 2,147,764,593〜603 B の `.pt` が 36 本、計 約 77.3 GB である(safetensors ではない)。メタデータのライセンスは `other`(名 qwen)だが、LICENSE のファイルの中身は Apache License 2.0 である。カードには別に、科学研究の外の目的での使用などを禁じる注意書きがある [S3]。
3. 学習データは「社内の事前学習データ」とだけ書かれ、トークン数と言語の記載は無い。カードの言語の札は `en` だけである。再構成の指標(説明できた分散・損失の差)は、論文の読めた範囲に無い。大きなノルムの活性(特に最初のトークン)は除いて学んだ [S1][S3]。
4. Base で学んだ辞書を後の学習のモデルに使うことを、カードは「多くの場合に妥当」と書く [S3]。後の学習ありの Qwen3-8B や AWQ の量子化版で測った値は、読んだ範囲に無い。
5. ほかに Karvonen の `adamkarvonen/qwen3-8b-saes`(MIT・2025-11-24)がある。**Qwen/Qwen3-8B** の層 9・18・27 の残差に、幅 16k と 65k・L0 80 と 160 の 4 本ずつで、学習データは FineWeb 90%・LMSYS-Chat 10%・5 億トークンである。層 18・幅 65k・k=80 の評価は、説明できた分散 0.706・L0 84.7・生きている特徴 99.2%(200 入力・長さ 2,048)[S6]。指示調整版の組(Qwen3-Instruct SAE・層 0〜8・幅 65K)は論文だけで、重みは「数か月のうちに公開」とある [S4]。
6. 日本語は、どの辞書も学習データに入っているかを書いていない。Qwen-Scope の論文は有害さの分類の 13 言語に日本語を入れたが、日本語の値は図だけで本文に無い [S1]。
7. 性格の向きの取り出しの手順(Chen ほか 2025・コードは Apache-2.0)は次のとおりである。特性の名と短い説明から、強いモデル(Claude 3.7 Sonnet)が対の系の指示 5 組・問い 40(取り出し 20・評価 20)・採点の指示を作る。正と負の指示で取り出しの問いごとに 10 回ずつ答えさせ、判定役(GPT-4.1-mini・0〜100)の点が 50 より上/下のものだけを残す。各層の残差を**答えのトークンで平均**し、正と負の平均の差を向きにする [S7][S8]。
8. 層は、同じ係数で層ごとに操舵して特性の点が最も高い層を選ぶ(Qwen2.5-7B は 20 層・作り話は 16 層、Llama-3.1-8B は 16 層)。確かめ方は、操舵で特性が動くか、一貫性の点(75 以上を保つ)、最後のプロンプトのトークンの射影と特性の点の相関(r=0.75〜0.83)、人の判定との一致(300 対で 94.7%)である [S7]。Qwen3-8B では 53 特性の監査があり、層は 20 が最も多く次いで 25、係数は 0〜2.5、判定役は手元の gpt-oss-20b だった(Big Five の特性ごとの値は読めた範囲に無い)[S9]。
9. 印象(温かさ・有能さ)を活性から読んだ先例に Deas ほか 2025 がある。モデル自身に特性を指定して書かせた文を札にし、MLP の活性の線形の読み取り器で、温かさ F1 75〜90・有能さ 75〜85 だった(英語・Llama-3.1-8B ほか 3 モデル)[S12]。札が「本人のモデルに作らせた条件」である点は、記録 2-32 の「札は本人のモデルの写しに尋ねた答え」と形が近い【見立て】。公開のリポは中身が空で、ライセンスの記載も無い [S13]。
10. 記録 2-32 の「計器としてだけ」に関わる注意は 3 つある【見立て】。辞書の学習データは、Qwen-Scope は言語の記載が無く(札は `en`)、Karvonen は 9 割が英語の FineWeb で、日本語の住民の印象を読む物差しとしては確かめられていない。persona vectors の手順は生成役と判定役に外の強いモデルを使う。読んだ 2 組の辞書の重みはどちらも `.pt` で、CLAUDE.md §7 の 11-01 の取得の許可(住民の LLM と判断モデル・safetensors のみ)の外にあたる(§6)。

## §1 問いと前提

### 1-1 問い(返事その 7 §6-2)

- (1) Qwen3-8B 用の公開の特徴の辞書(SAE)があるか。公開元・層・幅・ライセンス・版。
- (2) 性格の向き(persona vectors)の取り出し方の手順。論文と公開コード、対の文の作り方・層の選び方・確かめ方。
- 背景は記録 2-32: 温かさ・有能さ・親しさの数は計器としてだけ取り出し、本人の判断には戻さない。取り出し方はランの外で本人のモデルの写しに尋ねるか、T1 の再計算で活性を読む。読めたものが本人の印象とは限らない(対照の課題・尋ねた答え・行動と突き合わせる)。費用はその日の入力をもう一度通すのと同じなので、抽選した一部で行う。

### 1-2 前提(読んだもの)

| 前提 | 中身 | 場所 |
|---|---|---|
| 持続する性格の向きの基本 | persona vectors・CAA・RepE の形、層の選び方の先例(Qwen2.5-7B は 28 層中 20 層目)、Qwen3-8B の 36 層・隠れ次元 4,096 | [R-141](v2-r141-persistent-state-vectors-and-steering.md) §2-1・§4-1(B)。R-141 §10-2 の空欄 9 が「persona vectors の付録の残り」 |
| 活性の番号 | vLLM の取り出しの番号 k は「k 層を通った後の残差」で、0 は埋め込み、36 は最終の正規化の前 | [R-142](v2-r142-activation-tape-capture.md) §0 の 2(B) |
| 読み出しの対照 | 状況の文の感情・同じノルムの無作為の向き・対照課題で学んだ読み取り器・P0/P1 の床・amnesic の確かめ | R-126 §7(B) |
| 5070 の構成 | vLLM 0.28.0・`Qwen/Qwen3-8B-AWQ` | R-123(B) |
| 社会の見方の軸の疑い | 2 軸が成り立つのは約 35%・平均を比べてよい水準は約 11%(記録 2-32 が R-148 から引く) | 記録 2-32 |

## §2 Qwen3-8B 用の SAE

### 2-1 一覧(Hugging Face の API の検索 3 回・2026-11-09)

| リポ | 対象のモデル | 層 | 幅・疎さ | 中身を読んだか | 出典 |
|---|---|---|---|---|---|
| `Qwen/SAE-Res-Qwen3-8B-Base-W64K-L0_50` | Qwen3-8B-Base | 0〜35(全 36) | 65,536・k=50 | カード・API・LICENSE | [S3] ◎ |
| `Qwen/SAE-Res-Qwen3-8B-Base-W64K-L0_100` | Qwen3-8B-Base | 0〜35 | 65,536・k=100 | 一覧の行だけ(作成 2026-04-27・ダウンロード 713) | [S2][S5] ◎ |
| `adamkarvonen/qwen3-8b-saes` | Qwen/Qwen3-8B | 9・18・27 | 16k/65k × L0 80/160 | API・README・層 18 の 1 本の設定と評価 | [S6] ◎ |
| Qwen3-Instruct SAE(He ほか 2026) | Qwen3 の指示調整版 | 0〜8 | 65K・L0 160(目標) | 論文だけ(重みは未公開) | [S4] ◎ |
| `sammyliu/qwen3-8b-sae-l20-topk64`・`...-l36-topk64`・`lmxxf/qwen3-8b-sae-layer9`・`...layer22`・`...layer27`・`elrashid/sae-qwen3-8b-topk-l18`・`asher577/sae_qwen3_8b_L24_d65k_k50`・`..._k80`・`ExplosionNuclear/Qwen3-8B-hook_resid_pre-SAE`・`Yusser/MULTI21-SAES-Qwen3-8B_512_2100000000`・`Silen/cosine-scored-saes-qwen3-8b` ほか | 名前からは Qwen3-8B | 名前のとおり | 名前のとおり | 読んでいない(どれもダウンロード 0〜7) | [S5] ◎(一覧だけ) |

- 同じ検索に `ByteDance-Seed/Qwen3-30B-A3B-MoE-SAE`(2026-11-05)など別のモデルの組も出た。本書の範囲は 8B だけ。

### 2-2 Qwen-Scope(公式)

| 項目 | 中身 | 出典 |
|---|---|---|
| 組 | 7 つのモデル(Qwen3 と Qwen3.5・密と MoE)に 14 組。Qwen3.5-27B だけが指示調整版で学んだ | [S1] ◎ |
| 層と位置 | 「1–36 (all)」と論文の表、ファイルは `layer0.sae.pt`〜`layer35.sae.pt`。カードのコードは `model.model.layers[LAYER]` の出力に forward hook を掛ける(層の後の残差) | [S1][S3] ◎ |
| 形 | TopK の SAE。`W_enc`(65536, 4096)・`W_dec`(4096, 65536)・`b_enc`・`b_dec`。死んだ特徴の補助の損失(重み 1/32)。「almost all released SAEs have a negligible number of dead features」 | [S1][S3] ◎ |
| 学習データ | 「in-house pretraining data」。トークン数・言語は記載なし | [S1] ◎ |
| 外れ値 | 大きなノルムの活性を除いた。外れ値は Qwen3-1.7B と Qwen3-8B に最も多く、特に各入力の最初のトークン | [S1] ◎ |
| 量 | 層 0〜9 は 2,147,764,593 B、層 10〜35 は 2,147,764,603 B。重みの計 77,319,525,608 B(約 77.3 GB)。小さなファイル 105,067 B。検索の抜粋は「1 層 float32 で約 2.1 GB、bf16 の本体 16 GB と合わせ約 18 GB で 24 GB の GPU 1 枚に載る」と要約する(論文の該当の文は本書で確かめていない) | [S3] ◎・[S17] △ |
| 読み込み | 独自のコード(sae_lens ではない)。transformers で float32 の本体を読み、`torch.load` で `.pt` を読む。デモは `--model Qwen/Qwen3-8B-Base` | [S3] ◎ |
| Base 以外への適用 | 「using SAEs trained on base models to explore the internal process of post-training checkpoints is also reasonable」(多くの場合)。デモに `--model-name-analyzing-now qwen3-8b` の例 | [S3] ◎ |
| 用途の例 | 推論時の操舵(言語・概念・好み)・評価の重複の分析・多言語の有害さの分類(英語で特徴 1 つの F1 0.90 超)・後の学習(コードの切り替わりを減らす)。Qwen3-8B-Base の SASFT はコードの切り替わりの率を中国語 0.96→0.66%・ロシア語 0.16→0.07%・韓国語 0.43→0.07%(21 万例の設定)に下げた。能力の確かめ(中国語・11 万例の設定)では MMLU 52.15→50.09・HellaSwag 42.48→39.60 | [S1] ◎ |
| ライセンス | API のメタデータは `license: other`・`license_name: qwen`・`license_link` は同じリポの LICENSE。LICENSE の中身は「Apache License Version 2.0, January 2004」と「Copyright 2026 Alibaba Cloud」で、利用者数の閾値や研究だけの限定は無い。カードの注意書きは、科学研究の外の目的でモデルの能力に手を加えることと、有害な内容(列挙の中に「社会主義の核心的価値観」に反するものを含む)を作り広めることを禁じ、違反者は許可を自動で失い、最終の解釈は持ち主にある、と書く。論文 §9.3 にも同じ趣旨の文がある | [S1][S3] ◎ |
| 版 | L0_50: sha `9b7d647127c303dd371e5dbd992236bd9799b171`・最終の更新 2026-05-13・作成 2026-04-27・ゲートなし。公開の告知の日 2026-04-30 は検索の抜粋だけ | [S3] ◎・[S17] △ |

### 2-3 Karvonen の組

| 項目 | 中身 | 出典 |
|---|---|---|
| 対象 | `lm_name: "Qwen/Qwen3-8B"`・`submodule_name: "resid_post_layer_18"`(設定の JSON) | [S6] ◎ |
| 層 | 9・18・27(README は「layers 25%, 50%, and 75%」)。番号の数え方(0 から/1 から)は本書で確かめていない | [S6] ◎ |
| 4 本の対応 | trainer 0: L0 80・16k/trainer 1: L0 160・16k/trainer 2: L0 80・65k/trainer 3: L0 160・65k | [S6] ◎ |
| 形 | BatchTopK(`dictionary_learning` で学習)。1 つの固定の閾値を持つので、推論では JumpReLU として使え、バッチに依る活性を避けられると README が書く | [S6] ◎ |
| 学習 | 9 割 FineWeb・1 割 LMSYS-Chat・5 億トークン。層 18・trainer 2: 学習率 5e-05・244,140 歩・k=80・文脈の長さ 2,048 | [S6] ◎ |
| 評価(層 18・trainer 2) | `frac_variance_explained` 0.7056・`l0` 84.73・`cossim` 0.9024・`frac_alive` 0.9923・`n_inputs` 200・`context_length` 2048 | [S6] ◎ |
| 外れ値の注意 | Qwen は数百トークン先にも不定の注意の吸い込みがあり、約 0.1% のトークンでノルムが中央値の 100〜1,000 倍になる。中央値の 10 倍を超える活性を学習でも使用でも除いた(MSE が 3% よくなった)。使う側も同じ処理が要る、と README が書く | [S6] ◎ |
| 量・版・ライセンス | ae.pt は 536,954,902 B(16k)と 2,147,764,246 B(65k)、計 約 16.1 GB。sha `460a11d556a0c58ffd65909555f38b33e9d71aea`・最終の更新 2025-11-24。MIT | [S6] ◎ |

### 2-4 Qwen3-Instruct SAE(He ほか 2026)

- 題は「Discovering Millions of Interpretable Features with Sparse Autoencoders」(arXiv 2606.26620・2026-06-25)。Qwen3-1.7B・4B・8B の指示調整版。8B は残差の層 0〜8(「layer 0 refers to the first transformer block after the embedding layer」)・JumpReLU・幅 65K・L0 の目標 160・FineWeb-Edu 9B トークン。8B の再構成の評価は「not yet」[S4] ◎。
- 公開: 「We will release the code and model weights in the coming months.」。ライセンスの記載なし [S4] ◎。

### 2-5 使うときの技術の注【見立て】

- 番号の対応: Qwen-Scope の `layerL` は `layers[L]` の出力なので、R-142 の vLLM の番号では k=L+1 にあたる【算術】。Chen ほかの層は「1 から数え、各層の出力」[S7]。He ほかは 0 から数える [S4]。同じ「20 層」でも指す位置が 1 つずれうる。
- 量子化: 住民は `Qwen/Qwen3-8B-AWQ`(R-123)で、辞書は Base(Qwen-Scope)か Qwen3-8B(Karvonen)の浮動小数で学んでいる。T1 の再計算をどの重みで行うか(AWQ のままか、量子化の前か)で、辞書との合い方が変わる。量子化版で辞書を当てた記録は見つからなかった。
- 外れ値: 2 つの組はどちらも大きなノルムの活性を除いて学んでいる [S1][S6]。T1 の再計算の側で同じ除き方をしないと、特徴の値が別物になる恐れ【推測】。
- 費用【算術】: 1 層・1 トークンの符号化は 65,536 × 4,096 = 約 2.68 億の積和(約 0.54 GFLOP)。Qwen3-8B の前向きはパラメータ数 8,190,735,360(R-142)から約 16.4 GFLOP/トークンなので、1 層の符号化は約 3% にあたる(注意の計算を除いた粗い比)。辞書 1 層は float32 で約 2.15 GB(ファイルの大きさ)。
- 思考の切り替え: Qwen3-8B は思考あり/なしを持つが、辞書の学習と評価がどちらの出力で行われたかは、Karvonen の組では LMSYS-Chat を 1 割混ぜたことだけが書かれ、Qwen-Scope では書かれていない。

## §3 性格の向き(persona vectors)の取り出し方

### 3-1 Chen ほか 2025 の手順

| 段 | 中身(条件つき) | 出典 |
|---|---|---|
| 1 入力 | 特性の名と短い説明 | [S7] ◎ |
| 2 材料を作る | 共通の雛形 1 つで、強いモデル(Claude 3.7 Sonnet。README は思考あり・予算 5,000・max_tokens 16,000)が作る。(a) 対の系の指示 5 組: 正は「特性を出せ」、負は「特性を避け、反対の振る舞いを出せ」。(b) 問い 40: 「問いの中で特性を出せと頼まない」。取り出し 20・評価 20 に分ける。(c) 採点の指示 1 つ。出力は JSON | [S7][S8] ◎ |
| 3 答えを作る | 取り出しの問いごとに、正と負の系の指示で各 10 回。標本の設定(温度など)は書かれていない | [S7] ◎ |
| 4 ふるい | 判定役 GPT-4.1-mini(`gpt-4.1-mini-2025-04-14`)が 0〜100 で採点(上位 20 の logit の加重和・拒否は REFUSAL)。正は 50 より上、負は 50 より下だけを残す | [S7][S8] ◎ |
| 5 向き | 各層の残差を答えのトークンで平均し、正の平均 − 負の平均。コードは `response_avg_diff.pt`(論文で使用)・`prompt_avg_diff.pt`・`prompt_last_diff.pt` を `[層 × 隠れ次元]` で出す | [S7][S8] ◎ |
| 6 位置の比べ | 付録 A.3: 答えの平均・プロンプトの平均・プロンプトの最後を同じノルムで操舵して比べ、答えの平均が最も強く効いた | [S7] ◎ |
| 7 層 | 付録 B.4: 層ごとに同じ係数で操舵し、特性の点が最も高い層。Qwen2.5-7B-Instruct は悪と追従 20・作り話 16、Llama-3.1-8B-Instruct は 3 つとも 16。層の掃引の係数の値は書かれていない(本文の例に 0.5・1.0・1.5・2.5 ほか) | [S7] ◎ |
| 8 操舵 | 各デコードの歩で h ← h + α·v。引けば抑える | [S7] ◎ |
| 9 確かめ | 一貫性の点(GPT-4.1-mini・0〜100)は後からの操舵で 75 超・予防の操舵で 80 超。MMLU。人の判定: 著者 2 人が特性ごとに 50 対(LLM の点 >80 と <20)を見て計 284/300(94.7%)。監視: 系の指示 8 種(Claude 4.0 Sonnet が作成)と多数例 0・5・10・15・20 で、最後のプロンプトのトークンの射影と特性の点が r=0.75〜0.83(同じ型の指示の中では弱い)。微調整によるずれと特性の発現は r=0.76〜0.97(他の特性を基準にすると 0.34〜0.86) | [S7] ◎ |
| 10 限界(著者) | 特性を前もって指定する必要がある・曖昧な説明は意図しない向きを生む・平均の差は粗い・系の指示で引き出せる特性に限る・判定役は完全でない・評価の問いは 20 で単発の会話・試したのは中くらいの 2 モデル | [S7] ◎ |
| 11 言語 | 英語以外への適用は書かれていない | [S7] ◎ |

### 3-2 Qwen3-8B での先例(Zeng・Emami・Choi 2026)

| 項目 | 中身 | 出典 |
|---|---|---|
| 規模 | 4 つの領域の 53 特性。Qwen3-8B と gpt-oss-20b | [S9] ◎ |
| 手順の違い | Chen ほかの差の平均(答えのトークン)を使う。特性ごとに引き出しの問い 40。判定役は API ではなく手元の gpt-oss-20b(GPT-4.1-mini と 3 特性で照合)。向きは毎回の前向きで残差に足す | [S9] ◎ |
| 層と係数 | 層 {5, 10, 15, 20, 25}(途中から 30・35 を追加)× 係数 {0, 0.5, 1.0, 1.5, 2.0, 2.5}。Qwen3-8B は 20 層が最も多く、次いで 25。「There is no universal best layer.」 | [S9] ◎ |
| 区分 | natural: 基準の点 ≥70 かつ伸び ≤10/steerable: <70 かつ ≥10/intractable: それ以外か信号なし。閾値を 65〜75・5〜15 で動かした感度も報告 | [S9] ◎ |
| Qwen3-8B の結果 | 一般の領域で 19 特性中 16 が steerable。伸びの大きい特性は hyperbolic 42.28・impolite 40.78 ほか。Big Five の 5 つは一般の領域に入っているが、特性ごとの値は読めた範囲に無い(neurotic は伸びの大きい特性の 1 つと図 7 の記述にある) | [S9] ◎ |
| 生成の設定 | 複数の標本は温度 1.0・1 つなら 0.0・top_p 1・最大 1,000 トークン。思考の切り替えは書かれていない | [S9] ◎ |
| 費用 | H100 で 9.6 時間、入力 5,383・出力 186,926 トークン(1 特性あたりか全体かは本書で確かめていない) | [S9] ◎ |
| 限界(著者) | 特異性の対照(無作為の向き・混ぜた向き・負の係数の掃引)が無い | [S9] ◎ |
| コード | 頁に URL なし。出力の CSV などを出すと書く | [S9] ◎ |

### 3-3 Big Five を SAE の特徴で操舵した先例

- Zhang・Wang・Su「Mechanistic Knobs in LLMs」arXiv 2601.02978 は Big Five を例に、対の意味で特徴を引き出し、CAA より安定と要旨で書いていたが、v3(2026-10-13)で**取り下げ**られ、2607.26853 に作り直された [S10] ○。
- 作り直しの「From Representations to Behaviors: Exploring the Person-Situation-Behavior Triad in LLMs」(2607.26853・v2 2026-11-04)は、同じ状況に置いた対の振る舞いから SAE で性格の両極の特徴を取り出し、別の状況で両向きに動かし、社会的な課題で人の性格研究と合う得失を見た、と要旨で書く。モデル・辞書・層・数値は要旨に無い [S11] ○。
- DPN-LE(arXiv 2604.27929)は MLP の活性を高い/低い特性の標本で比べ、効果量 d で神経を選ぶ(LLaMA-3-8B-Instruct・Qwen2.5-7B-Instruct・抜粋)[S15] △。

### 3-4 印象(温かさ・有能さ)を活性から読んだ先例

| 研究 | 札の作り方 | 読む所 | 結果 | 出典 |
|---|---|---|---|---|
| Deas ほか 2025(EMNLP 2025)「Artificial Impressions」 | 各モデルに「friendly and meticulous」のような特性を指定して利用者の文を書かせ、指定した特性を札にする(Nicolas ほか 2021 の辞書で温かさ 131 語・有能さ 104 語・高低の 2 値)。1 モデルあたり 274,830 文(各指定 10 標本・温度 0.9)。人の検証は 4 人・各 81 対・Krippendorff の α .71(2 値で .78) | 各層の MLP の活性(残差でも同じ傾き)。トークンの位置は読めた範囲に無い | 温かさ F1 75〜90・有能さ 75〜85(5 分割の交差検証)。層の中ほどの前で最大、その後ゆっくり下がる。語の袋の基準を多くの深さで上回る | [S12] ◎ |
| 同(対象) | Llama-3.2-1B・Llama-3.1-8B・OLMo-2-7B。英語だけ | — | — | [S12] ◎ |
| SCoUT(AAAI 2026) | — | 注意の頭 | 温かさ ρ 最大 0.83・有能さ 0.90(抜粋) | [S14] △ |

- 【見立て】Deas ほかの量は「モデルが文の書き手に持つ印象」で、記録 2-32 の「本人が相手に持つ印象」に近い。persona vectors は「モデル自身が出す特性」で、構成概念が違う。

## §4 記録 2-32 との接点【見立て・推薦なし】

| 2-32 の注意 | 読んだ先例の形 | ぶつかる所 |
|---|---|---|
| 計器としてだけ・判断に戻さない | 読むだけの形は 2 つ: SAE の特徴の値を読む [S1][S6]、向きへの射影を読む(Chen ほかの監視)[S7]。どちらも操舵は要らない | 射影の監視は「最後のプロンプトのトークン」で相関が出た [S7]。T1 の再計算でどのトークンの活性を残すかは R-142 §0 の 3(全トークンを書く)と関わる |
| 札は本人のモデルの写しに尋ねた答えや対の文から | Chen ほかは外の強いモデルが対の指示を作り、外の判定役が採点する [S7]。Zeng ほかは判定役を手元のモデルに替えた [S9]。Deas ほかは札をモデル自身の生成の条件にした [S12] | 外のモデルを使う形は、費用・取得の許可・データを外へ送るかの題になる。手元の判定役なら許可の一覧(11-01)の範囲を確かめる必要がある |
| 読めたものが印象とは限らない | Chen ほかは同じ型の指示の中では相関が弱いと書く [S7]。Zeng ほかは特異性の対照が無いと書く [S9]。Deas ほかは語の袋を基準にした [S12] | R-126 §7 の対照(同じノルムの無作為の向きほか)と、2-32 の「尋ねた答え・行動と突き合わせる」が要る |
| 言語 | 読んだ先例はどれも英語。Qwen-Scope のカードの言語の札は `en` | 日本語の対の文で作った向き・日本語で確かめた辞書の先例は見つからなかった(R-141 §10-2 の空欄 1 と同じ) |
| 社会の見方の軸の疑い | Deas ほかと SCoUT は SCM の 2 軸を前提にする | R-148 の疑い(2-32 の注)が読み取り器の札にもそのまま当たる |
| 費用 | 辞書 1 層の符号化は前向きの約 3%【算術】。persona vectors の作成は 1 特性あたり少なくとも 400 回の生成と採点(正負 2 × 20 問 × 10 回)【算術】。対の指示 5 組をすべてで回すなら 2,000 回になる(5 組の使い方は本書で確かめていない) | 2-32 の「抽選した一部で」の量は本書では置いていない |

## §5 既存の実装・公開コードの比較表(推薦なし)

| 公開物 | 対象 | 層 | 幅・疎さ | 学習データ | 形式・量 | ライセンス | 版 | 出典 |
|---|---|---|---|---|---|---|---|---|
| Qwen-Scope `SAE-Res-Qwen3-8B-Base-W64K-L0_50` | Qwen3-8B-Base | 0〜35 | 65,536・TopK k=50 | 社内の事前学習データ(量・言語の記載なし) | `.pt`(pickle)・1 層 2.15 GB・計 77.3 GB | メタは other/qwen・LICENSE は Apache-2.0・別に注意書き | `9b7d647`(2026-05-13) | [S1][S3] ◎ |
| Qwen-Scope `..._L0_100` | 同 | 同 | 65,536・k=100 | 同 | 同(本書で確かめていない) | 本書で確かめていない | 本書で確かめていない | [S2] ◎ |
| `adamkarvonen/qwen3-8b-saes` | Qwen/Qwen3-8B | 9・18・27 | 16k/65k・BatchTopK・L0 80/160 | FineWeb 90%・LMSYS-Chat 10%・5 億 | `.pt`・計 16.1 GB | MIT | `460a11d`(2025-11-24) | [S6] ◎ |
| Qwen3-Instruct SAE | Qwen3 の指示調整版 8B | 0〜8 | 65K・JumpReLU・L0 160 | FineWeb-Edu 9B | 未公開 | 記載なし | — | [S4] ◎ |
| 個人の公開 十数本 | 名前からは Qwen3-8B | 名前のとおり | 名前のとおり | 読んでいない | 読んでいない | 読んでいない | — | [S5] ◎(一覧だけ) |
| `safety-research/persona_vectors` | 例は Qwen/Qwen2.5-7B-Instruct(任意のモデルを指定できる) | `--layer` で指定 | — | 材料は `dataset.zip`(中身は本書で確かめていない) | 向きは `[層 × 隠れ次元]` の `.pt` | Apache-2.0 | 10 commits(日付は頁に無い) | [S8] ◎ |
| `saprmarks/dictionary_learning` | (Karvonen の組の学習に使用) | — | — | — | — | 本書で確かめていない | — | [S6](README の言及) |
| `NickDeas/ArtificialImpressions` | — | — | — | — | README だけ(「Code upload in progress」) | 記載なし(LICENSE のファイルなし) | 3 commits | [S13] ◎ |
| vllm-lens・EasySteer・hotwire-vllm(実行中に活性を取る・足す道具) | — | — | — | — | — | MIT・Apache-2.0・MIT | R-141 §5-2 の版 | ※R-141 §5-2 |

## §6 決めるべき題(選択肢と根拠・推薦は書かない)

| # | 題 | 選択肢 | 根拠 |
|---|---|---|---|
| D1 | 辞書を使うか | Qwen-Scope(Base・全層)/Karvonen(Qwen3-8B・3 層)/指示調整版の公開を待つ/自前で学ぶ/使わない | §2・§5 |
| D2 | 取得の許可 | 先に聞く。CLAUDE.md §7 の 11-01 の Hugging Face の許可は「住民の LLM は `Qwen/` の公式リポ・判断モデルは各モデルの公式リポ・safetensors のみ」で、SAE はそのどちらでもなく、形式も `.pt`(pickle)である | §2-2・§2-3 |
| D3 | ライセンスと注意書き | Qwen-Scope のメタ(other/qwen)と LICENSE(Apache-2.0)の食い違いをどう読むか。注意書きの「科学研究の外の目的」の範囲と、商用の前の確認 | §2-2 |
| D4 | 層と位置の対応 | R-142 の番号 k と辞書の番号 L(k=L+1)の対応を固定するか。T1 の再計算で残す層とトークン | §2-5・§4 |
| D5 | 外れ値の除き方 | 辞書の側と同じ処理(中央値の 10 倍・大きなノルム)を T1 の側でも行うか | §2-5 |
| D6 | 量子化と思考の切り替え | T1 の再計算を AWQ で行うか量子化の前の重みで行うか。思考あり/なしのどちらの出力を読むか | §2-5 |
| D7 | 性格の向きの材料と判定役 | 外の強いモデル(Chen ほか)/手元のモデル(Zeng ほか)/本人のモデルの写しに尋ねる(2-32)。日本語の対の文を作るか | §3・§4 |
| D8 | 確かめ方の線 | 一貫性の点・人の判定との一致・特異性の対照(無作為・混ぜた向き・負の係数)・R-126 §7 の対照のどれを置くか | §3-1・§3-2・§4 |
| D9 | 印象を相手ごとに読む形 | 書き手の印象(Deas ほか)の形/自分の特性(persona vectors)の形/読む位置(相手について書いたトークンなど) | §3-4 |
| D10 | 抽選の量と費用 | 抽選する住民と呼びの割合。辞書の符号化は前向きの約 3%【算術】 | §4 |

## §7 読めなかったもの・確かめていないもの

| # | 対象 | 理由 | 影響 |
|---|---|---|---|
| U1 | Qwen-Scope の再構成の指標(説明できた分散・損失の差)と学習のトークン数・言語 | 論文の読めた範囲とカードに無い。カードが指す技術報告の PDF は読んでいない | 辞書の質は Karvonen の 1 本の評価だけが数値 |
| U2 | `..._L0_100` のカード・API・LICENSE | 一覧の行だけ | §5 の空欄 |
| U3 | 個人の公開の十数本の中身 | 読んでいない | §2-1 の最後の行 |
| U4 | Qwen-Scope の Space(`Qwen/QwenScope`) | 開いていない | — |
| U5 | Karvonen の組の層 9・27 と他の trainer の評価 | 層 18 の trainer 2 だけ読んだ | — |
| U6 | `dictionary_learning` のライセンス・層の番号の数え方 | 確かめていない | §2-3・§5 |
| U7 | Chen ほかの HTML の末尾 21,704 字・一貫性の採点の指示の文 | 読んでいない | — |
| U8 | Zeng ほかの表 2(Big Five ほか特性ごとの値)・リポ | 読めた範囲に無い・URL が無い | §3-2 |
| U9 | Deas ほかの HTML の末尾 約 42,000 字(読み取り器の種類・トークンの位置) | 読んでいない | §3-4 |
| U10 | SCoUT・DPN-LE・Qwen3 の persona vectors のブログ | 検索の抜粋だけ | △ |
| U11 | 2607.26853 の本文 | 要旨だけ | §3-3 |
| U12 | Anthropic の persona vectors の解説の頁・Neuronpedia の Qwen3 の扱い | 探していない | — |
| U13 | 量子化版(AWQ)に辞書を当てた記録・日本語で確かめた辞書や向き | 見つからなかった(検索 2 回と HF の API の検索 3 回) | §2-5・§4 |

断られた頁は無い。Web の道具の上限には当たらなかった。

## §8 出典(読んだ日はすべて 2026-11-09)

| # | 出典 | URL | 読んだ範囲 | 等級 |
|---|---|---|---|---|
| S1 | Deng ほか(18 名)2026「Qwen-Scope: Turning Sparse Features into Development Tools for Large Language Models」arXiv 2605.11887v1 | https://arxiv.org/abs/2605.11887 | 要旨と HTML の全体(2 回に分けて) | ◎ |
| S2 | Hugging Face のコレクション `Qwen/qwen-scope` | https://huggingface.co/collections/Qwen/qwen-scope | 一覧の全体 | ◎ |
| S3 | `Qwen/SAE-Res-Qwen3-8B-Base-W64K-L0_50` のカード・API(`?blobs=true`)・LICENSE | https://huggingface.co/Qwen/SAE-Res-Qwen3-8B-Base-W64K-L0_50 | カードの全体・API の JSON・LICENSE の全文 | ◎ |
| S4 | He ほか 2026「Discovering Millions of Interpretable Features with Sparse Autoencoders」(Qwen3-Instruct SAE)arXiv 2606.26620v1 | https://arxiv.org/abs/2606.26620 | 要旨と HTML | ◎ |
| S5 | Hugging Face の API の検索(`search=qwen3-8b&filter=sae`・`search=qwen3-8b-sae`・`search=sae-qwen3`) | https://huggingface.co/api/models | 結果の一覧(3・19・100 件) | ◎ |
| S6 | `adamkarvonen/qwen3-8b-saes`(MIT)の API・README・層 18 trainer 2 の `config.json` と `eval_results.json` | https://huggingface.co/adamkarvonen/qwen3-8b-saes | 該当のファイルの全文 | ◎ |
| S7 | Chen ほか 2025「Persona Vectors」arXiv 2507.21509v3 | https://arxiv.org/html/2507.21509v3 | HTML の前半 20 万字(付録 A.3・B.4・I を含む) | ◎ |
| S8 | `safety-research/persona_vectors`(Apache-2.0)の README | https://github.com/safety-research/persona_vectors | README とライセンスの欄 | ◎ |
| S9 | Zeng・Emami・Choi 2026「What Models Express, Suppress, and Resist: Auditing Open-Weight LLMs with Persona Vectors」arXiv 2607.13162v3 | https://arxiv.org/abs/2607.13162 | 要旨と HTML の全体(2 回に分けて) | ◎ |
| S10 | Zhang・Wang・Su「Mechanistic Knobs in LLMs」arXiv 2601.02978(v3 で取り下げ) | https://arxiv.org/abs/2601.02978 | 要旨と版の履歴 | ○ |
| S11 | Zhang・Wang・Su「From Representations to Behaviors: Exploring the Person-Situation-Behavior Triad in LLMs」arXiv 2607.26853v2 | https://arxiv.org/abs/2607.26853 | 要旨 | ○ |
| S12 | Deas ほか 2025「Artificial Impressions」arXiv 2510.08915v1(EMNLP 2025) | https://arxiv.org/html/2510.08915v1 | HTML の前半 10 万字 | ◎ |
| S13 | `NickDeas/ArtificialImpressions` | https://github.com/NickDeas/ArtificialImpressions | リポの頁(README だけ) | ◎ |
| S14 | SCoUT(AAAI 2026) | https://ojs.aaai.org/index.php/AAAI/article/view/39905 | 検索の抜粋 | △ |
| S15 | DPN-LE arXiv 2604.27929 | https://arxiv.org/abs/2604.27929 | 検索の抜粋 | △ |
| S16 | ブログ「Persona Vector Distillation in LLM Weights」(Qwen3 の 0.6B〜8B に persona vectors を当てた記録) | https://darshanmakwana412.github.io/2025/12/persona-vector-distillation | 検索の抜粋 | △ |
| S17 | Qwen-Scope の公開の告知の日(2026-04-30)を書く紹介の頁 | 検索の結果(lilting.ch ほか) | 検索の抜粋 | △ |

既存答申: ※R-141(B)§2-1・§4・§5-2・§10-2・※R-142(B)§0・§4・※R-126(B)§3-3・§7・※R-123(B)。リポの記録: [壁打ちの記録](../reference/wallbounce-record-2026-11-02_05.md) 2-32(R-148 の値の引用を含む)。D 等級の答申は根拠に使っていない。

### 親が一次確認すべき数値と主張

1. Qwen-Scope の Qwen3-8B 用 2 本が Base で学んだこと・層 0〜35・幅 65,536・k=50/100・`.pt` の 36 本・計 77,319,525,608 B・sha `9b7d647…` [S1][S3]。
2. 同じリポのメタ(`license: other`・`license_name: qwen`)と LICENSE の中身(Apache-2.0)の食い違い、カードの注意書き [S3]。
3. Karvonen の組の層 9・18・27・4 本の対応・FineWeb 90%/LMSYS-Chat 10%・5 億トークン・評価の 0.7056/84.73/0.9923・MIT [S6]。
4. Chen ほかの手順の数(5 組・40 問・10 回・50 の閾値・答えのトークンの平均・284/300・r=0.75〜0.83)[S7]。
5. Zeng ほかの Qwen3-8B の層(20 が最多・次いで 25)と係数 0〜2.5 [S9]。

## 親の一次確認(第346・2026-11-09・親)

| 主張 | 確かめ方 | 結果 |
|---|---|---|
| Qwen/SAE-Res-Qwen3-8B-Base-W64K-L0_50 のカード: Qwen3-8B-Base で学習・36 層・幅 65,536・Top-K 50・`.pt` | huggingface.co のカード(WebFetch) | **一致**。ライセンスはカードの欄で「qwen」(答申の「LICENSE の中身は Apache-2.0」は親未確認) |
| SAE の重みは `.pt`(pickle) | カード | 11-01 の許可(safetensors のみ)の外。取らない。取るなら先に聞く(第346 の報告) |
| 親未確認: persona vectors の手順の値・Karvonen の 0.706・層 20 の監査 | — | 未確認 |
