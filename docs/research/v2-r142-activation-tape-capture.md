<!-- hdr:v1 | 等級: B(第344 親の一次確認=末尾の表) | 作成: 2026-11-04 | 範囲: 指示書 11-04 §5-2 -->
# R-142 活性をテープに残す道(vLLM の隠れ状態の取り出し・HF transformers の道・Qwen3-8B の量・5070 で試す形)

- **分野**: 自然言語処理・機械学習 #27 / 計算機科学(並列・決定論) #28 / ソフトウェア工学 #29 | **重要度**: P2([返事その 4(11-04)](../design/prompt-2026-11-04-reply4.md) §4「テープの腕」・§5 の 2)
- **一次確認**: B(第344・親=末尾の表)。筆者がこの回に読んだ出典は 23 本(◎ 17・○ 6・△ 0)。既存答申からの引用は 5 本。読めなかったものは §9 に挙げた。
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 作成 2026-11-04・リサーチ役(Opus 5.5)。子サブは起動していない。コード・台帳・設計書・INDEX は 1 バイトも変えていない。封印の層(holdout・test の層)には触れていない。pip・重みの取得・clone はしていない。
> **Web の道具について**: WebFetch と WebSearch は、作業の始めから利用の上限で使えなかった。そのため、頁は curl の標準出力を文字だけにして読んだ(名乗りは curl の既定のまま変えていない。リポにも data/ にも保存していない。HTML を文字にする 9 行の補助スクリプトだけ、リポの外の作業用の場所に置いた)。**検索ができなかった**ので、出典は「公式の文書・ソース・PyPI・GitHub の API から辿れたもの」に限られる(§9 の U2)。
> **robots の件**: SGLang の文書(docs.sglang.ai)は robots.txt で `ClaudeBot` を `Disallow: /` にしている。筆者は robots を読む前に 1 頁を取得してしまった。その後で robots を読み、**内容は本書で使わない**ことにした。別の経路(GitHub のソースなど)でも取りに行っていない(§9 の U1)。
> 等級: ◎=原典か公式の文書・ソースの頁を本文まで読んだ/○=抄録・要旨・該当行の抜き出しだけ読んだ/△=検索の要約だけ。筆者の組み立ては【見立て】、根拠の無い置き方は【推測】と書く。推薦は書かない。決めるのはユーザー。

## §0 要旨

1. vLLM には**公式の取り出しの機能**がある。名前は「Hidden State Extraction」(推測デコードの擬似の方式 `extract_hidden_states`+KV コネクタ `ExampleHiddenStatesConnector`)。PR #33736 で 2026-03-02 に入り、リリースノートでは v0.17.0、blog では「v0.18.0 以降」と書かれている [S4][S5][S6][S7]。
2. 生成と同時に取れる。層は `eagle_aux_hidden_state_layer_ids` で選ぶ。番号 k は「k 層を通った後の残差」で、0 は埋め込み、36 は最終の正規化の前にあたる [S12]。1 要求ごとに `[トークン数, 層数, 4096]` の safetensors をサーバーの側のディスクに書き、応答の `kv_transfer_params.hidden_states_path` でその場所を返す [S4][S8][S13]。
3. 制約: 書くのは**プロンプトの全トークン**で、「最後の 1 トークンだけ」の口は無い。生成したトークンは `include_output_tokens` で足せる(v0.28.0 に有り・v0.18.0 に無し)が、最後の 1 トークンは入らない [S8][S14]。量子化した KV は使えない [S10]。chunked prefill は、文書が「両立しない・切ること」と書き、blog は「使える」と書いていて食い違ったまま [S4][S5](R-126 の空欄 7 は未解消)。
4. 速さとバッチ不変との関係について、vLLM の資料に**数値も記述も無い**。この機能は推測デコードの道を通る(下書きは標本そのまま)[S9]。だから `VLLM_BATCH_INVARIANT=1` の下で、取り出しを on にした艦隊と off の艦隊の出力が同じになるかは、資料からは言えない(B14 と同じ形の試験が要る)【見立て】。
5. ほかの道: pooling の口(`--runner pooling`・LAST)は最後のトークンを 1 本返す。ただし最終層だけで、既定で L2 正規化がかかり、生成と同じ口では使えない [S15]。vllm-lens 1.3.0(MIT・プラグイン)は任意の層を生成と同時に取れるが、`vllm==0.30.0` に固定され、全要求で CUDA グラフを切る [S19]。観測プラグインの RFC #36998 はまだ open [S18]。
6. 速さの先例値として読めたのは vllm-lens の表だけ。Llama-3.3-70B・TP4・vLLM 0.17.0・eager どうしの比較で、1 層の取り出しは壁時計 +12.0%、全 80 層は +317.0% [S20]。CUDA グラフを切ること自体の損は、この表には入っていない。HF transformers の道の速さの先例値は見つけられなかった(空欄)。
7. Qwen3-8B の config.json(HF・`Qwen/Qwen3-8B`): 層 36・隠れ次元 4,096・注意の頭 32・KV の頭 8・頭の次元 128・語彙 151,936・中間 12,288・`bfloat16`・埋め込みと出力は別 [S1]。この値から数えたパラメータ数 8,190,735,360(埋め込みを除く層の部分 6,946,071,552)は、モデルカードの 8.2B・6.95B と合う [S2]。
8. 量: 1 呼・1 層・最後のトークン・16 bit で **8,192 B**。5,000 体の既定のラン(60,939 呼/日)で **約 0.50 GB/日**、35 万体を比(×70)で見積もると **約 34.9 GB/日**。全 36 層を残すと 18.0 GB/日と 1.26 TB/日になる。KV は 1 トークン 147,456 B(144 KiB)で、1 呼(1,364 トークン)では 191.8 MiB になる(§4)。
9. vLLM の取り出しは全トークンを書いてから切るので、一時の書き出しは 1 呼あたり約 7.5〜11.7 MB、5,000 体 1 日で約 681 GB になる。保存する量の約 1,364 倍にあたる(§4-3)。ロックに `fcntl` を使うので、読み手は WSL の側に置くことになる【見立て】(§6)。
10. 本プロジェクトとの接点【見立て】: `fleet.py` の `params_extra` を使えば、要求に `kv_transfer_params` を通す道はすでにある。ただし応答の `kv_transfer_params` は今は読んでいない。ストリーミングの応答型にはその欄が無い。`params_hash` は要求ごとの追加を含まない。テープの側は `ARM_COLUMNS` の腕の列か別のファイルに置ける。**11-04 §4 の「残す列」と、R-126 §5-3 の親案「保存せず、入力から計算し直す」がぶつかる**ので、題 T1 に挙げた(§8)。

## §1 問い

返事その 4 §5 の 2: vLLM の生成の途中の隠れ状態を外へ出す方法はあるか。無ければ、HF transformers の別の道の速さはどうか。Qwen3-8B の設定を config.json で確かめ、1 呼あたり・1 日あたりの量を出す。5070 で試せる最小の形を出す。

分けて問う:
- (1) vLLM の公式の機能・pooling の口・hook・プラグイン(§2)。
- (2) HF transformers の道(§3)。
- (3) Qwen3-8B の設定と量(§4)。
- (4) 5070 で試す最小の形の案(§5)。
- (5) 本プロジェクトのテープと艦隊との接点(§6)。

既存答申との関係(重ねない): 第 2 世代の判断モデルの形・活性を教師にする手順・テープに足す欄・容量の初めの見積り(E1 は 64,528 呼で 0.53 GB/日)は [R-126](v2-r126-second-gen-decision-model-activations-heads.md) §5(**B**)を正とする。本書はその空欄 7(chunked prefill・AWQ・速さ)を埋めにいき、量を 11-03 の呼数で出し直す。5070 の vLLM の版・起動の値・KV の見積り(144 KiB/トークン)は [R-123](v2-r123-rtx5070-qwen3-8b-runbook.md)(**B**)を正とする。バッチ不変の B14(32/32)は [R-38](v2-r38-closed-output-judges-research.md)(**B**)と R-123 による。テープの容量の錨(69.4 B/呼)は [R-72](v2-r72-event-log-formats.md)(**A−**)による。persona vectors と接頭辞の KV の衝突は [性格の答申](v2-personality-traits-research.md)(**B**)と R-126 §3-3 に書かれている。操舵と多数の LoRA は 11-04 §5 の 1(別の答申)の題なので、本書は取り出しに限る。

## §2 vLLM で隠れ状態を外へ出す道

### 2-1 公式の機能「Hidden State Extraction」

| 項 | 中身 | 出典 |
|---|---|---|
| 入った時期 | PR #33736「[Spec Decode] Add hidden states extraction system」、2026-03-02 に merge。リリースノートは v0.17.0 の項に「Hidden states extraction system (#33736)」と書く。blog は「included in vllm>=v0.18.0」と書く。v0.17.0 のタグにコネクタのファイルがあることは確かめた | [S6][S7][S5][S14] ◎○ |
| その後 | v0.29.0 で Model Runner V2 の既定化に合わせ、`extract_hidden_states` が MRV2 に入った(#49811)。生成したトークンの分を足す `include_output_tokens` は v0.28.0 のコネクタにあり、v0.18.0 のコネクタには無い | [S7][S14] ○ |
| 仕組み | 推測デコードの「下書きのモデル」の席に、注意を計算しない擬似のモデルを置く。本体の補助の隠れ状態(EAGLE-3 用の配管)をその擬似の層の KV の場所に書き込み、KV コネクタがそれをディスクへ出す。blog の説明では、paged の KV と同じ仕組みで管理するので、prefix キャッシュ・chunked prefill・バッチ化が使えるという | [S5][S6] ◎ |
| 下書き | 「推測はしない。標本のトークンをそのまま下書きとして返し、必ず検証を通す」(提案器の docstring)。`num_speculative_tokens` は 1 に固定(assert) | [S9] ◎ |
| 起動 | `--speculative_config '{"method":"extract_hidden_states","num_speculative_tokens":1,"draft_model_config":{"hf_config":{"eagle_aux_hidden_state_layer_ids":[…]}}}'` と `--kv_transfer_config '{"kv_connector":"ExampleHiddenStatesConnector","kv_role":"kv_producer","kv_connector_extra_config":{"shared_storage_path":…}}'` の 2 つを一緒に指定する | [S4][S5] ◎ |
| 層の番号 | Qwen2/Qwen3 の forward は、番号 k が補助の層の一覧にあれば「k 層を通った後の hidden+residual」を積む(k=0 は最初の層の前=埋め込み)。文書の注は「`num_hidden_layers` を番号に渡すと最終層の出力が取れる。出力の正規化はかかっていない」 | [S12][S4] ◎ |
| 書く物 | 1 要求 1 ファイル `<shared_storage_path>/<request_id>.safetensors`。中身は `hidden_states [num_tokens, 層数, hidden_size]` と `token_ids [num_tokens]`。既定はプロンプトのトークンだけ。`include_output_tokens: true` なら生成したトークンも入るが、**最後のトークンは除く**(前向きの計算の入力になっていないので KV に無い) | [S4][S8] ◎ |
| 書き方(v0.32.0) | 要求が終わったら KV の場所から切り出し、別の CUDA ストリームで固定のホストのメモリへ非同期にコピーし、スレッドのプール(既定 8 本)で safetensors を書く。`.lock` を `fcntl.flock` で握り、読み手 `load_hidden_states()` は共有のロックで待つ。safetensors が 0.8.0 未満なら GIL を握るので遅いという警告がある | [S8] ◎ |
| 返し方 | 応答の `kv_transfer_params.hidden_states_path` に場所が入る。要求ごとの `hidden_states_path` の指定は `allow_custom_save_path` が on のときだけ効く(文書は「信頼できるクライアントだけで」と書く)。チャットの要求型 `ChatCompletionRequest` と応答型 `ChatCompletionResponse` には `kv_transfer_params` の欄がある。**ストリーミングの応答型 `ChatCompletionStreamResponse` には無い**(v0.32.0 の protocol.py) | [S4][S13] ◎○ |
| 推奨 | 文書は「オンラインでは /dev/shm のような RAM の上のファイルシステムを使い、クライアントがすぐ消す」ことを勧める。blog は「プロンプトのトークンだけを保存するので、v1/completions に max_tokens=1 で呼ぶ」ことを勧める(include_output_tokens ができる前の記述) | [S4][S5] ◎ |
| 型の制約 | 擬似の注意の層が受けるのは fp16・bf16・fp32。KV の型は `auto` か `bfloat16` だけで、量子化した KV では NotImplementedError になる | [S10] ○ |
| 並列 | blog: 1 台の中の `--tensor-parallel-size`・`--data-parallel-size` で動く。コネクタは TP の rank 0 だけが書く | [S5][S8] ◎ |
| chunked prefill | 文書(latest・2026-06-11、v0.32.0 のタグの md も同じ文)は「Chunked prefill is not compatible with this feature and must be disabled.」と書く。blog は「chunked prefill … を使える」と書く。設定のファイル 4 本(vllm.py・scheduler.py・arg_utils.py・scheduler の本体)を grep したが、この機能で chunked prefill を拒む検査は見つからなかった | [S4][S5][S11] ◎○ |
| 速さ | 数値は無い。blog は「最初のコネクタは最適化されておらず、書き込みがブロッキング。非同期化は作業中」と書く(2026-03 の時点)。v0.32.0 のコネクタは上のとおり非同期になっている | [S5][S8] ◎ |
| バッチ不変 | バッチ不変の文書(latest・2026-11-03)は試験済みの一覧に `Qwen/Qwen3-8B` と `Qwen/Qwen3-8B-AWQ` を載せる。推測デコードやこの機能と一緒に使ったときの記述は無い | [S17] ◎ |

### 2-2 ほかの道

| 道 | 中身 | 出典 |
|---|---|---|
| pooling の口 | `--runner pooling`(必要なら `--convert embed`)で、因果モデルは既定で LAST(最後のトークンの last_hidden_states)を返す。変換したモデルの embed は既定で L2 正規化がかかり、`{"use_activation": false}` で外せる。取れるのは**最終層だけ**で、生成の runner とは別に立てる。文書の冒頭に「HF Transformers や Sentence Transformers より速いとは限らない」とある | [S15] ◎ |
| 公式のプラグインの仕組み | `vllm.general_plugins` の entry point で、木の外のモデルを `ModelRegistry.register_model` で登録できる。どのプロセスでも読み込まれる。Qwen3 の実装を写して取り出しを足したモデルを登録する道は、この仕組みで作れる【見立て】 | [S16] ◎ |
| vllm-lens 1.3.0 | MIT・2026-10-02。依存は `vllm==0.30.0`(固定)。general_plugins として自動で読み込まれ、**`enforce_eager=True` を強制**する(全要求で CUDA グラフと torch.compile が切れる)。要求ごとに `extra_args`(HTTP では `vllm_xargs`)の `output_residual_stream: [層]` で残差を `(層, 位置, hidden)` の形で返す。既定は JSON の中に base64+zstd、大きいときは `activations_transport="binary"` で別の取り出し口(サーバーの側のバッファ 既定 8 GiB・TTL 300 s)。任意の Python の hook(`ctx.saved`)も渡せるが、HTTP では cloudpickle なので「任意コードの実行」になると README が書く | [S19] ◎ |
| hotwire-vllm 0.1.2 | MIT。**操舵だけ**で、取り出しは無い。README は「インストールだけで使える vLLM の操舵の道具(vllm-lens・EasySteer・IBM の vLLM Hook)はどれも `enforce_eager=True` を強制する。PyTorch の forward hook は CUDA グラフの捕捉を越えて生き残らないからだ」と書き、自分は Triton の演算子をグラフの中に入れて CUDA グラフを保つと書く | [S21] ◎ |
| RFC #36998 | 「Observation Plugin for Intercepting & Routing on Activations」(2026-03-13・open)。forward hook で層の出力を取り、要求ごとに切って plugin に渡す提案。案の中で観測は **prefill の間だけ**に限っている。まだ入っていない | [S18] ○ |
| SGLang | 文書の robots が ClaudeBot を断っているので読まない(§9 の U1)。空欄 | — |

### 2-3 vllm-lens の速さの表(読めた先例値はこれだけ)

`examples/benchmark.ipynb` の出力 [S20]。条件: Llama-3.3-70B-Instruct・TP 4・vLLM 0.17.0・`enforce_eager=True`(基準の側もプラグインを読み込んでいるので eager)・alpaca の 50 問・`max_model_len` 1,024。

| 腕 | 壁時計 | 出力 tok/s | 基準との差(壁時計) |
|---|---|---|---|
| 基準(取り出しなし) | 82.15 s | 413.6 | — |
| 1 層(第 5 層) | 92.02 s | 351.4 | +12.0% |
| 全 80 層 | 342.59 s | 93.9 | +317.0% |
| 要求ごとに層を変える(0〜10) | 91.78 s | 366.1 | +11.7% |
| 操舵ベクトル(第 5 層) | 96.92 s | 374.0 | +18.0% |
| LoRA を交互に | 166.26 s | 203.6 | +102.4% |

- 注: 基準も eager なので、CUDA グラフを切ること自体の損はこの表に入っていない。8B を 1 枚で回す場合の値でもない。全 80 層の腕について、ノートは「1 要求あたり約 195 MB を CPU に置く」と書く。

## §3 HF transformers の道

| 項 | 中身 | 出典 |
|---|---|---|
| `output_hidden_states=True` | 前向きの計算で、埋め込みの出力と各層の出力のタプル(層数+1 本・各 `(batch, seq, hidden)`)を返す。文書の注: `hidden_states[-1]` が `last_hidden_state` と一致するとは限らない(最後に正規化をかけるモデルがある) | [S22] ◎ |
| `generate(..., output_hidden_states=True, return_dict_in_generate=True)` | 生成の各段について、層ごとの隠れ状態のタプルのタプルを返す。生成と同時に取れる | [S23] ◎ |
| forward hook | `register_forward_hook` で 1 層の出力だけを取る道は、PyTorch の一般の仕組み。transformers の文書の該当頁はこの回に読んでいない【推測】 | — |
| 速さの先例値 | **見つけられなかった**(検索の道具が使えなかった・§9 の U3)。vLLM の blog は、transformers で隠れ状態を作る道の欠点として「vLLM の性能の工夫(大きなモデル・分散)を失う」「transformers と vLLM の隠れ状態の小さな食い違いが不具合の種になる」の 2 つを挙げる。数値は無い | [S5] ◎ |
| 量の注 | `output_hidden_states=True` は全層を GPU の上に持つ。1,364 トークン × 37 本 × 4,096 × 2 B ≈ 413 MB/列(再計算)。1 層だけなら hook のほうが軽い【見立て】 | 計算 |

- 【見立て】 HF の道は、走行中の艦隊の代わりにはならない。今の艦隊は vLLM の OpenAI 互換の口(`/v1/chat/completions`)を叩く形で、決定論は vLLM のバッチ不変(B14)に頼っている(R-38・R-123)。HF の道が向くのは「走行の後に、テープの入力から計算し直す」形(R-126 §5-3 の案)か、小さなモデルで道を試す形(§5)である。ただし、計算し直した活性が本番の活性とどこまで一致するかは、別の道(transformers と vLLM)では保証されない(blog の 2 つ目の欠点)。

## §4 Qwen3-8B の設定と量

### 4-1 config.json(https://huggingface.co/Qwen/Qwen3-8B/raw/main/config.json・2026-11-04 に頁を読んだ・ダウンロードはしていない)

| 欄 | 値 |
|---|---|
| `architectures` | `Qwen3ForCausalLM` |
| `num_hidden_layers`(層の数) | **36** |
| `hidden_size`(隠れ次元) | **4096** |
| `num_attention_heads`(注意の頭) | **32** |
| `num_key_value_heads`(KV の頭) | **8** |
| `head_dim`(頭の次元) | **128** |
| `vocab_size`(語彙) | **151936** |
| `intermediate_size` | 12288 |
| `max_position_embeddings` | 40960 |
| `torch_dtype` | `bfloat16` |
| `tie_word_embeddings` | false |
| `rope_theta` | 1000000 |
| `sliding_window` / `use_sliding_window` | null / false |

- 同じ系列の値(各 config.json を読んだ)[S3]: Qwen3-0.6B=隠れ 1,024・28 層/Qwen3-1.7B=2,048・28 層/Qwen3-4B=2,560・36 層(いずれも KV の頭 8・頭の次元 128・語彙 151,936・bf16・埋め込みと出力を共有)/**Qwen3-8B-AWQ=隠れ 4,096・36 層・`float16`・AWQ 4 bit・group 128**(R-123 の S16 と同じ)。
- パラメータ数の検算(再計算): 1 層 = Q 4,096×4,096+K と V 各 4,096×1,024+O 4,096×4,096+MLP 3×4,096×12,288+正規化 = 192,946,432。36 層で 6,946,071,552。埋め込みと出力が各 622,329,856。合計 8,190,735,360。モデルカードの「8.2B・埋め込みを除く 6.95B」と合う [S2](R-126 の空欄 9 はこれで埋まる)。
- 注: 8B の元の重みは bf16、AWQ 版は fp16 で回る。テープの腕の「fp16 で約 8 KB」は、bf16 でも同じ 2 B/値なので量は変わらない。ただ、AWQ 版の活性と bf16 版の活性は同じ値にならない【見立て】。

### 4-2 1 呼あたり・1 日あたりの量(再計算)

1 呼・1 層・最後のトークン・16 bit = 4,096 × 2 B = **8,192 B**。これは今のテープの 1 呼(69.4 B・R-72)の約 118 倍にあたる。

| 規模 | 呼/日 | 1 層・最後・16 bit | 全 36 層・最後・16 bit | 1 層・int8 | 1 層・256 次元に縮めた 16 bit |
|---|---|---|---|---|---|
| 5,000 体(既定のラン・11-03 の値) | 60,939(fix4-1103 の README・mock・seed 1) | **0.499 GB**(0.465 GiB) | 17.97 GB | 0.250 GB | 31.2 MB |
| 35 万体(5,000 体の比 ×70 で概算=【推測】) | 4,265,730 | **34.94 GB**(32.54 GiB) | 1,258 GB | 17.47 GB | 2.18 GB |
| 参考: 39 万体の実測の呼数(C7・9 月の版) | 2,706,593(R-72) | 22.17 GB | 798 GB | 11.09 GB | 1.39 GB |

- 埋め込みの段まで含めて 37 本残すと、全層の欄は ×37/36 になる(5,000 体で 18.47 GB/日)。
- R-126 §5-3 は E1 を 64,528 呼で 0.53 GB/日とした。11-03 の既定のランは 60,939 呼で、量は 0.50 GB/日になる。
- 縮め方(int8・PCA)は R-126 §5-3 の列を同じ式で出し直したもので、縮めてよいかは決めていない。

### 4-3 KV キャッシュと、取り出しの一時の量(参考)

| 量 | 値 | 式 |
|---|---|---|
| KV/トークン(16 bit) | 147,456 B = 144 KiB | 2(K と V)× 36 × 8 × 128 × 2 B(R-123 と同じ) |
| KV/呼 | 128.5〜200.7 MiB | 入力 914〜1,427 トークン(R-123 の実測の幅)。1,364 トークン(入力 1,300+出力 64)で 191.8 MiB |
| vLLM の取り出しの擬似の KV(1 層) | 8 KiB/トークン=本物の KV の 5.6% | 擬似の層は「頭の数=取り出す層の数、頭の次元=hidden_size」で場所を取る [S6]。同じ VRAM の上限の中では、入る列が約 5.3%(8/152)減る【見立て】 |
| 同(36 層) | 288 KiB/トークン=本物の KV の 2 倍 | 同上 |
| 提案器のバッファ | (max_num_batched_tokens+max_num_seqs)× 層数 × 4,096 × 2 B。例: (2,048+32) × 1 × 8 KiB ≈ 16.3 MiB | [S9] のバッファの形 |
| 一時の書き出し(1 層・全プロンプト) | 7.5〜11.7 MB/呼 | 914〜1,427 トークン × 8,192 B |
| 同・5,000 体 1 日 | 約 681 GB(1,364 トークンで計算) | 60,939 × 1,364 × 8,192 B。保存する量(0.499 GB)の約 1,364 倍 |
| 同・書き出しの速さ | 約 22〜90 MB/s(中央 59 MB/s) | 681 GB を R-123 の E1 の所要 8.5/3.2/2.1 h で割った【見立て】 |
| 同・35 万体(×70) | 約 47.7 TB/日 | 【推測】 |

## §5 5070(12 GB)で試せる最小の形の案(試していない・形だけ)

前提: R-123 のとおり、5070 は 12,227 MiB で、机上のアプリがすでに約 2,081 MiB を使う。WSL と vLLM はユーザーの UAC の後(11-04 §6)。どの形も pip や重みの取得が要る。許可の範囲は CLAUDE.md §7(11-01 の追加)で決まる。

| 案 | モデル | 道 | 試せること | 要るもの・未確認の点 |
|---|---|---|---|---|
| M1 | `Qwen/Qwen3-8B-AWQ`(fp16・6.10 GB・R-123) | vLLM の `extract_hidden_states`(1 層)+`ExampleHiddenStatesConnector`。`shared_storage_path` は WSL の /dev/shm。読み手(WSL の側)が最後のトークンだけ残して元を消す | 本番と同じ道で、生成と同時に 1 層が取れるか。取り出しの on と off で出力が同じか(B14 の形で 32/32)。KV に入る列の数(起動のログ)。壁時計の差 | vLLM 0.28.0(R-123 の版)に機能と `include_output_tokens` があることはソースで確かめた。AWQ・sm_120・バッチ不変と一緒に動くかは未確認。chunked prefill を切る必要があるかは食い違い(§2-1) |
| M2 | 同上 | 走行の後に、テープの入力から計算し直す(vLLM の取り出しで `max_tokens=1`) | R-126 §5-3 の案。走行中の速さに触れない | 走行中の活性と一致するかは、同じ版・同じ重み・バッチ不変の下で確かめる |
| M3 | `Qwen/Qwen3-0.6B`/`1.7B`/`4B`(bf16) | HF transformers の forward hook か `output_hidden_states` | 道(層の番号・最後のトークンの位置・テープへの書き出し)の配線の確かめ。重みは 8B より小さい【推測】 | transformers の pip(許可の範囲は確かめる)。活性は 8B と別物で、教師には使えない。1 呼の量は 2,048/4,096/5,120 B(再計算) |
| M4 | `Qwen/Qwen3-8B-AWQ` | HF transformers+AWQ の読み込み | vLLM の活性との食い違いの大きさ | AWQ の核の pip が要る(名前と版は未確認)。8B の bf16 版(約 16.4 GB=8.19B × 2 B)は 12 GB に入らない(再計算) |
| M5 | `Qwen/Qwen3-8B-AWQ` | vllm-lens 1.3.0 | 任意の層・hook で最後のトークンだけ返す | `vllm==0.30.0` 固定(R-123 の 0.28.0 と違う)・eager の強制・pip の許可(R-126 の問い 6 は「今は入れない」)。HTTP の hook は任意コードの実行 |

## §6 本プロジェクトのテープと艦隊との接点【見立て】

src を読んだ事実(HEAD 2160272):
- `src/shibuya/llm/fleet.py` の `_payload` は `/v1/chat/completions` に `model・messages・max_tokens・temperature・top_p・seed・chat_template_kwargs`(と `cache_salt`)を送る。`call.params_extra` があれば、payload にそのまま足す。
- `_attempt_once` は応答の `choices[0]` と `usage` だけを読む。応答の `kv_transfer_params` は読んでいない。
- `params_hash` は艦隊の橋の初めに `self.params` から 1 回だけ作る。要求ごとの `params_extra` は入らない。
- `src/shibuya/engine/tape.py` は版 4(21 列)で、腕を立てたランだけ末尾に足す列 `ARM_COLUMNS` の仕組みがある(今は `recalled_event_ids` の 1 本だけ)。繰り延べの行(D-58)も 1 行を持つ。

接点の見立て:
1. **要求の側**: `params_extra={"kv_transfer_params": {...}}` で、コードを変えずに要求ごとの指定は届く。ただし、取り出しの on/off はサーバーの起動の設定(推測デコードの席)で決まる。テープの鍵の `params_hash` には入らないので、run_meta(R-126 §5-2 の `vllm_version`・`quant`・`batch_invariant` の並び)に「取り出しの設定」を足す形が考えられる。
2. **応答の側**: 非ストリーミングなら `d["kv_transfer_params"]["hidden_states_path"]` で場所が取れる。ストリーミング(`cfg.stream`)の応答型にはこの欄が無い。既定の名前 `<request_id>.safetensors` の request_id が応答の `id` と同じかは確かめていない(§9 の U9)。
3. **読み手の場所**: コネクタは `fcntl` のロックを使うので、`load_hidden_states()` は Windows の側では動かない【推測】。艦隊のクライアントは Windows の側にある(R-123)。そのため、WSL の側に「読んで最後のトークンを切り、元を消す」小さな係を置き、結果を返す形になる。一時の量は §4-3 のとおり 1 日 681 GB(5,000 体)。
4. **どのトークンか**: 「最後のトークン」には 2 通りある。(a) プロンプトの最後(最初の生成の直前・prefill の活性=R-126 の第 2 世代の入力と同じ位置)。(b) 生成の最後(`include_output_tokens` でも最後の 1 個は入らないので、その 1 つ前)。T2 の思考あり(`enable_thinking`)の呼では、(b) は思考の後の答えの側になる。
5. **テープの置き場所**: (i) `ARM_COLUMNS` に `act_l{k}`(長さ 4,096 の 16 bit の固定長、または 8,192 B の binary)を足す。腕を立てたランだけ列が増え、既定のランは 21 列のまま。(ii) 別のファイル(例: `acts.parquet`、`call_id` を鍵)にすれば `calls.parquet` は腕の on でも変わらない。Parquet と pyarrow で 16 bit の浮動小数を扱えるかは確かめていない(§9 の U12)。
6. **繰り延べ・作り直し**: 繰り延べの行(答えが返らなかった呼)には活性が無い。書式の失敗で温度 0 の作り直しをした呼では、テープに残る応答の試行の活性を採るか決める必要がある。プロンプトの最後の活性は同じプロンプトなら同じはずだが、それはバッチ不変が効いているときに限る【見立て】。
7. **決定論**: 活性の値はバッチの組み方に左右される。バッチ不変の下なら同じ入力で同じ値になる見込みだが、取り出しを on にした艦隊は推測デコードの道を通るので、**on の艦隊でも B14 を通すこと**が前提になる【見立て】。on と off で応答が同じかの試験も同じ形で作れる。
8. **記憶との関係**: 11-04 §4 の決定どおり、記憶には使わない。テープの再生(TapeMiss の鍵)も活性を見ない。だから、活性の欠けや違いは再生の一致に効かない【見立て】。

## §7 比較の表(推薦は書かない)

| 道 | 版・状態 | 生成と同時 | 層を選べるか | 取れる位置 | 最後のトークンだけ | CUDA グラフ | バッチ不変との関係 | 速さの資料 | 足す導入 | 等級 |
|---|---|---|---|---|---|---|---|---|---|---|
| A. vLLM `extract_hidden_states`(走行中) | v0.17.0〜(blog は 0.18.0〜)・`include_output_tokens` は 0.28.0 に有り | 可 | 可(任意の複数・0〜36) | プロンプトの全部(+出力から最後を除いた分) | 無い(後で切る) | 提案器が CUDA グラフの振り分けを持つ(使われるかは未確認) | 記述なし・推測デコードの道を通る | 数値なし | なし(vLLM の本体) | [S4]〜[S14] ◎○ |
| B. A を走行の後に(テープの入力から計算し直す) | 同上 | — (別の時に prefill だけ) | 可 | 同上 | 無い | 同上 | 本番の活性との一致は同じ版・重み・不変の下で試す | 数値なし | なし | 同上+R-126 §5-3 |
| C. vLLM pooling(LAST) | 現行の文書 | 不可(別の runner) | 不可(最終層だけ) | 最後のトークン | 有る | 記述なし | 記述なし | 「HF より速いとは限らない」 | なし(別のインスタンスの VRAM) | [S15] ◎ |
| D. vllm-lens 1.3.0 | `vllm==0.30.0` 固定 | 可 | 可 | 全位置(hook で絞れる【見立て】) | hook 次第 | **切る**(全要求) | 記述なし | 1 層 +12.0%・全層 +317%(70B・TP4・eager どうし) | pip(MIT) | [S19][S20] ◎ |
| E. 自前のプラグイン(general_plugins+モデルの登録) | 公式の仕組み | 可【見立て】 | 可【見立て】 | 実装次第 | 実装次第 | forward hook なら切れる(hotwire の主張)・演算子にすれば保てる【見立て】 | 実装と試験次第 | なし | 自前のコード(保守の負担=blog) | [S16][S21] ◎ |
| F. RFC #36998 | open・未実装 | prefill だけの案 | 可(案) | 案では prefill | 案次第 | hook の案 | 記述なし | なし | — | [S18] ○ |
| G. HF transformers(`output_hidden_states`・hook) | 現行の文書 | 可(generate) | 全層か hook で 1 層 | 全位置/各段 | hook で絞れる | 使わない(eager の PyTorch)【推測】 | vLLM のバッチ不変の外・vLLM との値の食い違いの危険(blog) | 先例値は見つからず | pip(transformers・AWQ なら核も) | [S22][S23][S5] ◎ |

## §8 決めるべき題(選択肢と根拠・推薦は書かない)

| # | 題 | 選択肢 | 根拠 |
|---|---|---|---|
| T1 | **残すか、計算し直すか**(矛盾の確認) | (a) 11-04 §4 のとおり走行中に残す列 / (b) R-126 §5-3 の親案(第340 で親が賛成)のとおり、保存せずにテープの入力から計算し直す / (c) 両方(既定は b・腕で a) | 11-04 §4 は「1 呼につき 1 本の活性を残す列」。R-126 §5-3 と §親の一次確認は「活性は保存せず入力から計算し直す=親案 賛成」。どちらを正にするかの記録は見つからなかった |
| T2 | 道 | A・B・D・E・G(§7) | 速さの数値は D だけ。A は本体の機能だが、バッチ不変との関係に記述が無い |
| T3 | どのトークン | (a) プロンプトの最後(prefill)/(b) 生成の最後の 1 つ前/(c) 両方 | §6 の 4。第 2 世代の入力(R-126)は (a) の位置。読み出し(感情・崩れ)にどちらが合うかは別の答申の題 |
| T4 | どの層 | 1 層の番号(vLLM の数え方で 0〜36)/複数の層 | 層の選び方は 11-04 §5 の 1(操舵の答申)の題と重なる |
| T5 | 型と縮め方 | 16 bit(fp16/bf16)/int8/PCA | §4-2。AWQ の艦隊の活性は fp16 で出る |
| T6 | 置き場所 | `ARM_COLUMNS` の腕の列/別のファイル(`call_id` を鍵) | §6 の 5。別のファイルなら `calls.parquet` は on でも変わらない |
| T7 | 決定論の扱い | on の艦隊でも B14 を合格の条件にする/on と off の応答の一致を試す/`params_hash` か run_meta に取り出しの設定を入れる | §6 の 1・7 |
| T8 | 繰り延べ・作り直しの行 | 活性なし(空)/最後の試行のもの | §6 の 6 |
| T9 | 5070 で試す形 | M1〜M5(§5) | pip・重みの許可の範囲(CLAUDE.md §7) |
| T10 | 35 万体の量の扱い | 1 層 16 bit で 34.9 GB/日(比の概算)を全部残す/標本を取る/縮める | §4-2。分割(holdout)は R-126 §5-4 の規則に従う |

## §9 読めなかったもの・確かめていないもの

| # | 対象 | 理由 | 影響 |
|---|---|---|---|
| U1 | SGLang の文書(`return_hidden_states` ほか) | robots.txt が `User-agent: ClaudeBot` に `Disallow: /`。筆者は robots を読む前に sampling params の頁を 1 回取得した(道具の出力はリポの外の道具の結果の置き場に自動で残った)。robots を読んだ後は内容を使っていない。GitHub など別の経路でも取りに行っていない | SGLang の行は比較の表に無い |
| U2 | Web の検索全般 | WebFetch・WebSearch が利用の上限で使えなかった。curl で公式の頁・ソース・PyPI・GitHub の API だけを読んだ | EasySteer(arXiv 2509.25175)・IBM の vLLM Hook・nnsight・TensorRT-LLM などの先例を探せていない |
| U3 | HF transformers の道の速さの先例値 | 検索できず、文書に数値なし | §3 の速さは空欄 |
| U4 | 推測デコードの道(取り出し)とバッチ不変を一緒に使った記録 | バッチ不変の文書・リリースノートの該当行に記述なし | §6 の 7 は試験が前提 |
| U5 | chunked prefill の食い違い | 文書は「切ること」、blog は「使える」。4 ファイルの grep で拒む検査は見つからなかった。それ以外の場所は読んでいない | R-126 の空欄 7 は半分だけ埋まった |
| U6 | AWQ のモデルで取り出しが動くか | 資料に記録なし(擬似の層は fp16 を受ける=[S10]) | M1 の未確認の点 |
| U7 | 取り出しの速さ(壁時計の差) | 文書・blog に数値なし | §7 の A の速さは空欄 |
| U8 | 取り出しを on にしたとき、生成されるトークンが off と同じか | 提案器の docstring は「必ず検証を通す」とだけ書く。検証の段の計算の形は読んでいない | T7 |
| U9 | ストリーミングの応答の `id` と、保存の名前の `request_id` が同じか | 読んでいない | §6 の 2 |
| U10 | vllm-lens の `docs/compatibility.md` と、バッチ不変との関係 | 読んでいない | D の行のバッチ不変は空欄 |
| U11 | Qwen3-0.6B/1.7B/4B の重みの大きさ | モデルカードを読んでいない | §5 の M3 の大きさは【推測】 |
| U12 | Parquet と pyarrow の 16 bit 浮動小数の扱い | 読んでいない | T6 の (i) の型 |
| U13 | RTX 5070 の演算の速さと帯域 | 読んでいない | 計算し直す(B)の所要は出していない |
| U14 | RFC #36998 の本文の後半と議論 | 本文の前半 5,000 字だけ読んだ | F の行は ○ |

## §10 出典(読んだ日はすべて 2026-11-04)

| # | 出典 | URL | 読んだ範囲 | 等級 | ライセンス |
|---|---|---|---|---|---|
| S1 | `Qwen/Qwen3-8B` の config.json | https://huggingface.co/Qwen/Qwen3-8B/raw/main/config.json | 全文 | ◎ | Apache-2.0(モデルカードの表記) |
| S2 | `Qwen/Qwen3-8B` のモデルカード(README.md) | https://huggingface.co/Qwen/Qwen3-8B/raw/main/README.md | 冒頭の仕様(パラメータ数・層・頭・文脈長)とライセンスの行 | ◎ | Apache-2.0 |
| S3 | `Qwen/Qwen3-0.6B`・`Qwen3-1.7B`・`Qwen3-4B`・`Qwen3-8B-AWQ` の config.json | https://huggingface.co/Qwen/Qwen3-4B/raw/main/config.json ほか同じ形 | 全文 | ◎ | — |
| S4 | vLLM 文書「Hidden State Extraction」(latest・2026-06-11 の表記) | https://docs.vllm.ai/en/latest/features/speculative_decoding/extract_hidden_states/ | 全文 | ◎ | — |
| S5 | vLLM blog「Extracting hidden states from vLLM」(2026-03-30) | https://vllm.ai/blog/2026-03-30-extract-hidden-states | 全文 | ◎ | — |
| S6 | vLLM PR #33736 の本文 | https://github.com/vllm-project/vllm/pull/33736(GitHub の API で本文を読んだ) | 本文・題・merge の日 | ◎ | Apache-2.0(リポ) |
| S7 | vLLM のリリースノート v0.10.0〜v0.33.0rc3 | https://github.com/vllm-project/vllm/releases(GitHub の API) | 各版の本文から hidden state・batch invariance の行を抜き出した | ○ | — |
| S8 | `vllm/distributed/kv_transfer/kv_connector/v1/example_hidden_states_connector.py`(v0.32.0) | https://raw.githubusercontent.com/vllm-project/vllm/v0.32.0/vllm/distributed/kv_transfer/kv_connector/v1/example_hidden_states_connector.py | 全文 | ◎ | Apache-2.0(読むだけ) |
| S9 | `vllm/v1/spec_decode/extract_hidden_states.py`(v0.32.0) | https://raw.githubusercontent.com/vllm-project/vllm/v0.32.0/vllm/v1/spec_decode/extract_hidden_states.py | 初めの 200 行(提案器の本体) | ◎ | Apache-2.0 |
| S10 | `vllm/model_executor/models/extract_hidden_states.py`(v0.32.0) | https://raw.githubusercontent.com/vllm-project/vllm/v0.32.0/vllm/model_executor/models/extract_hidden_states.py | 型の制約の行と量子化 KV の検査の行 | ○ | Apache-2.0 |
| S11 | `vllm/config/speculative.py` ほか設定 4 ファイル(v0.32.0) | https://raw.githubusercontent.com/vllm-project/vllm/v0.32.0/vllm/config/speculative.py | `extract_hidden_states` の grep の前後 | ○ | Apache-2.0 |
| S12 | `vllm/model_executor/models/qwen2.py` の forward と `interfaces.py` の `_maybe_add_hidden_state`(v0.32.0) | https://raw.githubusercontent.com/vllm-project/vllm/v0.32.0/vllm/model_executor/models/qwen2.py | 該当の関数の全体 | ◎ | Apache-2.0 |
| S13 | `vllm/entrypoints/openai/chat_completion/protocol.py`(v0.32.0) | https://raw.githubusercontent.com/vllm-project/vllm/v0.32.0/vllm/entrypoints/openai/chat_completion/protocol.py | `kv_transfer_params` の欄と応答型の grep | ○ | Apache-2.0 |
| S14 | 同コネクタのファイルの有無と `include_output_tokens` の有無(v0.17.0・v0.18.0・v0.28.0・v0.29.0) | https://raw.githubusercontent.com/vllm-project/vllm/v0.28.0/vllm/distributed/kv_transfer/kv_connector/v1/example_hidden_states_connector.py ほか | HTTP の状態と語の数 | ○ | Apache-2.0 |
| S15 | vLLM 文書「Pooling Models」(latest) | https://docs.vllm.ai/en/latest/models/pooling_models/ | 前半(課題・pooling の型・変換・既定の正規化) | ◎ | — |
| S16 | vLLM 文書「Plugin System」(latest) | https://docs.vllm.ai/en/latest/design/plugin_system/ | 前半(仕組み・種類) | ◎ | — |
| S17 | vLLM 文書「Batch Invariance」(latest・2026-11-03 の表記) | https://docs.vllm.ai/en/latest/features/batch_invariance/ | 全文 | ◎ | — |
| S18 | vLLM RFC #36998「Observation Plugin for Intercepting & Routing on Activations」 | https://github.com/vllm-project/vllm/issues/36998(GitHub の API) | 本文の前半 5,000 字・状態(open) | ○ | — |
| S19 | vllm-lens 1.3.0(PyPI) | https://pypi.org/project/vllm-lens/(JSON の API) | 説明の前半 18,000 字・依存・版の日付 | ◎ | MIT |
| S20 | vllm-lens `examples/benchmark.ipynb` | https://raw.githubusercontent.com/UKGovernmentBEIS/vllm-lens/main/examples/benchmark.ipynb | セルと出力の全部 | ◎ | MIT |
| S21 | hotwire-vllm 0.1.2(PyPI) | https://pypi.org/project/hotwire-vllm/(JSON の API) | 説明の前半 5,000 字 | ◎ | MIT |
| S22 | HF transformers 文書「Model outputs」 | https://huggingface.co/docs/transformers/main_classes/output | `hidden_states` の節 | ◎ | — |
| S23 | HF transformers 文書「Utilities for Generation」 | https://huggingface.co/docs/transformers/internal/generation_utils | `GenerateDecoderOnlyOutput` の節 | ◎ | — |

robots の確認: docs.vllm.ai(全部許可)・vllm.ai(`/api/`・`/_next/`・`/static/` 以外は許可)・huggingface.co(全部許可)・pypi.org(`/simple/`・`/packages/` ほかは不許可。JSON の API の `/pypi/` は不許可の一覧に無い)・raw.githubusercontent.com(robots.txt は 404)。docs.sglang.ai は ClaudeBot を不許可(U1)。

既存答申(等級は INDEX.md の値):
- ※既存答申 R-126(**B**)— 第 2 世代の判断モデル・テープを教師にする手順・容量の初めの見積り・空欄 7 と 9
- ※既存答申 R-123(**B**)— 5070 の vLLM 0.28.0・AWQ・KV 144 KiB/トークン・入力 914〜1,427・E1 の所要
- ※既存答申 R-72(**A−**)— テープ 69.4 B/呼・C7 の 2,706,593 呼
- ※既存答申 R-38(**B**)— バッチ不変での logprobs の一致(B14)
- ※既存答申 性格の答申(**B**)— persona vectors と接頭辞の KV の衝突
- 設計の原文: [返事その 4(11-04)](../design/prompt-2026-11-04-reply4.md) §4・§5、`docs/bench/analysis/fix4-1103/README.md`(既定のラン 60,939 呼)、`src/shibuya/engine/tape.py`・`src/shibuya/llm/fleet.py`(HEAD 2160272 で読んだ)

## 空欄

1. HF transformers の道の速さの先例値(U3)。
2. vLLM の取り出しの速さの数値と、バッチ不変と一緒に使った記録(U4・U7)。
3. chunked prefill の食い違いの決着(U5)。
4. AWQ と sm_120 での取り出しの動作(U6)。
5. 取り出しの on と off で生成が同じか(U8)。
6. ストリーミングの応答の id と保存の名前の関係(U9)。
7. SGLang の `return_hidden_states`(U1・robots で読まない)。
8. 検索で見つけるはずだった他の先例(EasySteer・IBM の vLLM Hook・nnsight など・U2)。

## 親の一次確認(第344・2026-11-04・親)

| 主張 | 確かめ方 | 結果 |
|---|---|---|
| Qwen3-8B の config.json(層 36・隠れ 4,096・頭 32・KV の頭 8・頭の次元 128・語彙 151,936・中間 12,288・bfloat16・tie なし) | huggingface.co の raw の config.json を読んだ | **9 項目とも一致** |
| vLLM の隠れ状態の取り出しは PR #33736・merge 2026-03-02 | GitHub の API で PR を読んだ | **一致**(題「[Spec Decode] Add hidden states extraction system」) |
| 量 8,192 B × 60,939 呼 = 0.499 GB/日・KV 2×36×8×128×2 = 147,456 B/トークン | 再計算 | **一致**(499,212,288 B・147,456 B) |
| SGLang の robots | docs.sglang.ai/robots.txt を読んだ(robots の頁だけ) | 筆者の記述どおり ClaudeBot を断る旨の行がある。読む前に 1 頁を取得した件は §9 U1 に記録あり・本文と出典の表に SGLang の頁の内容は無い(grep) |
