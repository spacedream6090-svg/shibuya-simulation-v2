# R-123 RTX 5070 で Qwen3-8B(4 ビット)を vLLM で回し、5,000 体 × 1 日を動かす手順書

> 発注: [回答 10-25](../design/v2-answers-2026-10-25.md) §0 の 1・§5 R-C・§6-0〜§6-2。作成: リサーチ役(Opus 5.5)・2026-10-25。
> 位置づけ: 答申(研究の題)。**何も入れていない・何も取得していない**。コマンドは書いただけで、1 つも実行していない(機械の読み取りだけは §1 のとおり実行した)。
> 出典の番号 [S*] は §7 の表、[R*] はリポの中の記録。読んだ日はすべて 2026-10-25。確かめられなかったものは「未確認」、自前の置き方は「expedient」と書く。

---

## §0 要旨

1. この PC には **WSL が入っていない**(`wsl --status` が「インストールされていません」と返す)。`.venv` に torch と vLLM は無い(httpx 0.28.1 はある)。GPU は RTX 5070・12,227 MiB・ドライバ 617.42(CUDA UMD 13.4)。机上の常駐アプリがすでに 2,081 MiB を使っている。
2. **推奨は (A) WSL2(Ubuntu)+ vLLM 0.28.0(PyPI の既定=CUDA 13.0・torch 2.13.0)+ 公式の `Qwen/Qwen3-8B-AWQ`(Apache-2.0・6.10 GB)を `--quantization awq_marlin --dtype float16` で 1 本立てる構成**。0.28.0 は、サーバーで B14(バッチ不変)を通した版と同じ。sm_120 で起動しなければ、0.32.0(2026-10-18 公開)へ上げる。
3. vLLM の公式文書は、バッチ不変の対象を「compute capability 8.0 以上」とし、試験済みの一覧に **Qwen/Qwen3-8B-AWQ を載せている**[S1]。ただし環境変数の頁は「9.0 以上」と書いていて食い違う[S2]。どの GPU で試したかも書いていない。**sm_120(5070)で効くかは一次資料では確かめられない**。そこで手元で B14 と同じ形の試験(32/32 一致)を通すことを、合格の条件にする。
4. VRAM の見込み: 重み 5,816 MiB。KV は 1 トークン 144 KiB(fp16)。`--gpu-memory-utilization 0.78` なら KV は約 2.2〜2.7 GiB で、1,364 トークンの列が**共有なしで 11〜14 本、静的 750 トークンを共有すれば 24〜30 本**入る。`--max-num-seqs 32` が上限の目安。
5. E1(5,000 体 × 1 日・62,176 呼)の壁時計は **最短 約 2.1 h/中央 約 3.2 h/最長 約 8.5 h**(§5)。1:00 に始めれば、3 時台〜9 時台に終わる。7 GPU の実測(30〜37 分)を単純に 7 倍すると 3.5〜4.3 h で、上の幅に入る。
6. (B) llama.cpp と (C) Ollama は、API の形がおおむね合うものの、バッチ不変が無い[S24]。Ollama は `chat_template_kwargs` を受けるかが書かれていない[S26]。どちらも「温度 0 の再現性だけ」を見る控えにとどめる。
7. E1 は 2-7(再送の穴)を直す前なので、「動くかどうかの確認」に限る(回答 10-25 §6-0)。1 日を通すランは、CLAUDE.md §4 により**ユーザーが明示してから**回す。その前は 24 刻みのスモークまで。

### 親とユーザーの判断が要る点(許可待ちの一覧)

| # | 何 | 誰が | 取得先・中身 | 根拠 |
|---|---|---|---|---|
| P1 | **WSL と Ubuntu の導入**(管理者の `wsl --install -d <配布物>`・再起動あり) | ユーザー | Microsoft の配布物(Store 経由)。取得のドメインは許可の一覧の外 | [S21] |
| P2 | **WSL 側の pip**: `vllm==0.28.0` とその依存(torch 2.13.0 ほか・約 300 MB の wheel+CUDA の部品) | ユーザーの許可 | PyPI(許可の一覧にある・版の固定が条件)。依存が `download.pytorch.org` を要るかは未確認=要るなら一覧の外 | CLAUDE.md §7・[S6][S8] |
| P3 | **重み** `Qwen/Qwen3-8B-AWQ` の revision `4da05a8edb55c6046cce958586c33b61da07bb79`(6,098,581,864 B) | ユーザーの許可 | huggingface.co(一覧にあるのは「判断モデルの候補と Ruri-v3」だけ=**本件が入るかは親の判断**) | CLAUDE.md §7・[S15] |
| P4 | 控え (B) の場合: llama.cpp の Windows 版の実行ファイル(zip)と GGUF `Qwen3-8B-Q4_K_M.gguf`(5,027,783,488 B) | ユーザーの許可 | github.com の release(実行ファイル・zip=一覧の外)/huggingface.co | CLAUDE.md §7・[S18] |
| P5 | 控え (C) の場合: Ollama のインストーラ(実行ファイル)とモデル | ユーザーの許可 | ollama.com(一覧の外) | — |
| P6 | `--generation-config` を既定(auto=モデルの `top_k 20` が入る)のままにするか、`vllm`(要求の値だけ)にするか | 親 | 9 月のサーバーは既定のままだった(起動の台本に指定なし)[R8]。前と同じ条件にするなら既定のまま | [S10][S17] |
| P7 | 夜間に机上アプリ(ブラウザ・Discord ほか)を閉じる/スリープを止める設定 | ユーザー | — | §1・回答 10-25 §0 の 9(電池の設定) |

---

## §1 機械の確認(読み取りだけ・2026-10-25 21:30)

| 項目 | 読んだ値 | 読み方 |
|---|---|---|
| GPU | NVIDIA GeForce RTX 5070・12,227 MiB・WDDM・使用中 2,081 MiB(机上のアプリ約 30 本=Chrome・Edge・Slack・Discord・ChatGPT・claude・VS Code ほか) | `nvidia-smi` |
| ドライバ | 617.42(KMD 617.42・CUDA UMD Version 13.4)。10-06 のメモの 591.86 から上がっている | 同上 |
| WSL | **入っていない**。`wsl -l -v` と `wsl --status` はどちらも「Linux 用 Windows サブシステムがインストールされていません。'wsl.exe --install' を実行してインストールできます。」の旨を返す(UTF-16 の文字化けを読み直した)。`wsl.exe` 自体は 10.0.26100.9549 | `wsl -l -v`・`wsl --status`・`Get-Command wsl` |
| Windows | Windows 11 Home(レジストリの ProductName は「Windows 10 Home」と出るが、build 26200 なので Windows 11)・25H2・build 26200.9711 | `HKLM:\...\CurrentVersion` |
| CPU・主記憶・ディスク | Intel Core Ultra 7 265K(20 コア)・31.2 GB・C: の空き 353.4 GB | `Get-CimInstance` |
| 本体の `.venv` | Python 3.12.10。torch=無し・vllm=無し・httpx 0.28.1・xxhash 4.0.1・pyarrow 25.0.1・numpy 2.5.3・aiohttp=無し | `pip list` |

含意: 艦隊のクライアント(`fleet.py`=httpx)は、今の `.venv` のままで動く。Windows 側に新しい依存は要らない。GPU 側は WSL を入れるところから始める。WSL の主記憶は既定で「Windows の 50%」=約 15.6 GB[S23]。重み 6 GB の読み込みには足りる。

---

## §2 構成の案(比較)

艦隊のクライアントが期待する API の形(`src/shibuya/llm/fleet.py` を読んだ)は次のとおり:
- `GET /v1/models` の先頭の id を使う(`--model` が空のとき)。
- `POST /v1/chat/completions`。中身は `messages`(system+user)・`max_tokens`(T1=96)・`temperature`(既定 0.7)・`top_p`・**呼ごとの `seed`**(`xxh64(call_id, run_seed)`)・**`chat_template_kwargs: {"enable_thinking": <T2 なら true>}`**・`cache_salt`・`stream: true`+`stream_options.include_usage`。
- TTFT のタイムアウトは 60 s、全体は 300 s。並列の上限は予算行 L6 の 64/レプリカで、CLI からは変えられない(`--fleet-queue-capacity` だけ変えられる)。
- `cache_salt` と `chat_template_kwargs` は vLLM の拡張で、他のサーバーは無視するか拒む。

| | (A) WSL2 + vLLM | (B) Windows ネイティブ llama.cpp(`llama-server`・GGUF Q4_K_M) | (C) Ollama(Windows 版) |
|---|---|---|---|
| 版の案 | vLLM **0.28.0**(2026-08-26・PyPI 既定 CUDA 13.0・`torch==2.13.0`)[S5][S6][S8]。控えに 0.32.0(2026-10-18・同じ torch 2.13.0)[S4][S7]。CUDA 13 には R580 以上のドライバが要る[S3]=617.42 で足りる | release の版は未選定(未確認) | 未選定(未確認) |
| sm_120 で動く確度 | **中〜高**。PyTorch は 2.7(cu128)から Blackwell に対応(prototype)[S29]。vLLM の Blackwell の最低は CUDA 12.8[S3]。RTX 5090(sm_120)+ WSL2 で `Qwen3-14B-AWQ` を `awq_marlin`・`--dtype float16` で動かした報告がある(vLLM 0.17.1)[S11]。量子化の対応表は Hopper までしか載せていない[S9]=公式の保証は無い。RTX 5060 Ti の「`awq` は bf16 に固定されて落ち、`awq_marlin`+`TRITON_ATTN` で動く」という報告は、検索の要約しか読めなかった(本文は 404=**未確認**)[S13] | 高(5070 の llama-bench の記録あり)[S25] | 高と見込む(未確認) |
| バッチ不変 | `VLLM_BATCH_INVARIANT=1`。CC 8.0 以上・`Qwen/Qwen3-8B-AWQ` が試験済みの一覧にある[S1]。環境変数の頁は CC 9.0 以上[S2](sm_120=12.0 はどちらも満たす)。実装の注は「Hopper(SM90)と Blackwell(SM100)」としか書いておらず、SM120 の記述は無い[S30]。A5000(8.6)では 32/32 を確かめた[R7]。**5070 では未確認 → §4 の 7 で自検証** | **無い**。「`cache_prompt` を使うと、バッチの大きさが違えば logits はビット単位で同じにならない」と明記[S24] | 無い(llama.cpp 系・未確認) |
| 処理量の見込み | 連続バッチ+prefix キャッシュ。A5000 で同じ重み(Qwen3-8B-AWQ・vLLM 0.28.0)を測った記録がある=2.78 呼/s(入力 1,500・出力 128・c32)[R1] | 連続バッチは既定 on・`-np` で枠の数[S24]。vLLM と同じ負荷で比べた記録は無い(未計測) | `OLLAMA_NUM_PARALLEL` の既定 1・待ち 512 を超えると 503[S27]。多数の並列には向かない |
| `fleet.py` との相性 | **そのまま**(9 月の艦隊と同じ API) | `/v1/chat/completions` はある。`enable_thinking` はサーバー全体の `--chat-template-kwargs` で切れる[S24]。要求ごとに受けるか(T2 の帯)は未確認。`cache_salt` は無視されると見込む(未確認) | `seed`・`stream_options.include_usage`・`temperature`・`top_p`・`max_tokens` は受ける[S26]。思考の切り替えは `reasoning_effort: "none"`[S26]。`chat_template_kwargs` は文書に無い=**思考が既定で on のまま流れる恐れ**。直すには src の変更が要る(今は止めている) |
| 決定論 | 不変 on+呼ごとの seed で、バッチの組み方によらず同じ出力(A5000 で実測)[R7] | 温度 0 でも並列の組み方で変わり得る[S24] | 同左 |
| 総合 | **推奨** | 控え(動作の確認と、温度 0 の再現性だけ) | 採らない(思考の切り替えが合わない) |

### (A) の起動の値の案と根拠

| 引数 | 案 | 根拠 |
|---|---|---|
| `--quantization` | `awq_marlin` | 5090 + WSL2 で動いた構成[S11]。素の `awq` は sm_120 で落ちるという報告(未確認)[S13] |
| `--dtype` | `float16` | 重みの `torch_dtype` は float16[S16]。engine args の頁は「half は AWQ に推奨」[S10]。5090 で動いた構成も float16[S11] |
| `--max-model-len` | 4096 | 9 月の艦隊と同じ値[R8]。T1 は入力 ≤1,300+出力 96 で 2,048 に収まる。T2(`max_tokens = ceil(1.5*B_world)+96`)の余裕を見て 4096(expedient) |
| `--gpu-memory-utilization` | **0.78**(起動の直前に `nvidia-smi` の空きを見て 0.70〜0.80 で決める) | 既定は 0.92[S10]。机上ですでに 2,081 MiB を使っている=空きは最大 (12,227−2,081)/12,227 ≈ 0.83。WSL2 + Blackwell で VRAM の見えない使用分が出た報告(GitHub #41619)は検索の要約だけ=未確認。0.78 は expedient |
| `--max-num-seqs` | 32 | KV に入る本数(共有ありで 24〜30・§3)と、A5000 の膝 c32〜c64[R1] から。クライアントは 64 本まで送るので、残りは vLLM の待ち行列に入る(TTFT 60 s の内側に収まる見込み=§6) |
| `--max-num-batched-tokens` | 4096(足りなければ 8192) | 9 月は 8192[R8]。12 GB では活性の領域を小さくする(expedient) |
| `--enable-prefix-caching` | 明示する | 9 月の台本と同じ[R8]。共有の静的ブロック(≤750 tok・予算 M11)が効く |
| `--kv-cache-dtype` | `auto`(fp16) | fp8 にすると列の数は倍になるが、9 月(fp16)と出力が変わる。不変性も未確認 → まず auto |
| 環境変数 | `VLLM_BATCH_INVARIANT=1`・`VLLM_USE_FLASHINFER_SAMPLER=0`・`VLLM_WORKER_MULTIPROC_METHOD=spawn`・`PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` | 前 2 つは 9 月のサーバーと同じ(README・メモ server-vllm-ops)。後 2 つは 5090 + WSL2 の報告[S11] |
| 注意の層 | まず既定(自動)。落ちたら `--attention-backend TRITON_ATTN` | 引数は engine args にある[S10]。5060 Ti の報告(未確認)[S13] |

---

## §3 重みの候補

| 候補 | モデルカード | ライセンス | 大きさ | 版(固定に使う) | 備考 |
|---|---|---|---|---|---|
| **Qwen/Qwen3-8B-AWQ(公式)** | https://huggingface.co/Qwen/Qwen3-8B-AWQ | apache-2.0・gated=false | safetensors 2 本=4,853,922,024+1,244,659,840=**6,098,581,864 B(5,816 MiB)** | sha `4da05a8edb55c6046cce958586c33b61da07bb79`(lastModified 2025-05-21) | AWQ 4 ビット・group 128・gemm・zero_point=true・torch_dtype float16[S16]。カードは `vllm>=0.8.5`、非思考の推奨 Temperature=0.7・TopP=0.8・TopK=20・MinP=0、量子化モデルには presence_penalty 1.5 を強く勧める[S14]。**艦隊は 0.7/top_p は送るが presence_penalty は送らない=9 月と同じ**(変えるなら腕) |
| Qwen/Qwen3-8B-GGUF(公式・控え B) | https://huggingface.co/Qwen/Qwen3-8B-GGUF | apache-2.0・gated=false | `Qwen3-8B-Q4_K_M.gguf` 5,027,783,488 B(4,795 MiB) | sha `7c41481f57cb95916b40956ab2f0b139b296d974` | llama.cpp 用[S18] |
| Qwen/Qwen3-8B-FP8(公式・参考) | https://huggingface.co/Qwen/Qwen3-8B-FP8 | 未確認(公式の系列) | 9,436,628,784 B(9,000 MiB) | — | 12 GB では KV の場所がほぼ残らない=**不採用**[S19]。5090 + WSL2 では FP8 が AWQ の 1/3 の速さという報告もある[S11] |
| 第三者の AWQ/GPTQ | 探していない | — | — | — | 公式の AWQ があるので不要 |

9 月の本番は `nytopop/Qwen3-8B.w8a8`(INT8)だった。今回は量子化が変わる(INT8 → AWQ 4 ビット)ので、**9 月の結果とは「別のモデル」として比べる**。A5000 の記録では、同じ形の負荷で AWQ の処理量は INT8 の 0.757 倍だった[R1]。品質の差(品質プローブ)は未計測。

### VRAM の見積り(式)

- KV の 1 トークン = 2(K と V)× 層 36 × KV ヘッド 8 × head_dim 128 × 2 B(fp16)= **147,456 B = 144 KiB**[S16]。1 列 1,364 トークン(入力 1,300+出力 64・予算 M11)= 191.8 MiB。
- 使える量 = 12,227 MiB × util − 重み 5,816 MiB − その他(活性・CUDA グラフ・torch の文脈。**1,000〜1,500 MiB と置く=expedient**)。
- util 0.78 → 9,537 − 5,816 − (1,000〜1,500) = **KV 2,221〜2,721 MiB = 15,794〜19,349 トークン**。
  - 共有なし: ÷1,364 = **11.6〜14.2 列**。
  - 静的 750 トークンを全列で共有(prefix キャッシュ): (トークン − 750) ÷ 614 = **24.5〜30.3 列**。
  - fp8 KV(参考): それぞれ約 2 倍(23〜28 列/50〜62 列)。
- 実際の値は、起動ログの KV の行(GPU KV cache size)で確かめる。§4 の 6 で記録する。

---

## §4 手順(コマンドは書いただけ・未実行)

役割の分け: **WSL 側=vLLM のサーバーだけ**(GPU を持つ)。**Windows 側=本体の `.venv` でエンジンと艦隊のクライアント**(世界データ `data/` も Windows 側のまま)。両者は `http://127.0.0.1:8000` でつなぐ。WSL の既定(NAT)では、WSL の中のサーバーに Windows から `localhost` で届く[S22][S23]。

1. **WSL2 の準備(ユーザー・P1)**。管理者の PowerShell で:
   ```powershell
   wsl --install -d Ubuntu-24.04     # 配布物の名前は wsl --list --online で確かめる(Ubuntu-24.04 があるかは未確認)
   # 再起動 → Ubuntu の利用者名とパスワードを作る
   wsl -l -v                          # VERSION 2 を確かめる
   ```
   `%UserProfile%\.wslconfig` の案(expedient):
   ```ini
   [wsl2]
   memory=20GB        # 既定は主記憶の 50%=約 15.6 GB。重みの読み込みと pip の展開に余裕
   swap=8GB
   [general]
   instanceIdleTimeout=-1   # 既定 15000 ms で止まる。夜間の常駐のため(-1=自動で止めない)[S23]
   ```
2. **CUDA の確認(WSL の中)**。Linux 用の NVIDIA ドライバは**入れない**(Windows のドライバが `libcuda.so` として渡される)[S20]。
   ```bash
   /usr/lib/wsl/lib/nvidia-smi        # RTX 5070 と 617.42 が見えること
   python3 --version                  # vLLM 0.28.0 は >=3.10,<3.15 [S8]
   ```
   CUDA Toolkit は原則として入れない(torch の wheel が CUDA の実行部品を持つ)。flashinfer の JIT が nvcc を要るときは、9 月と同じく `CUDA_HOME=<venv>/lib/python3.X/site-packages/nvidia/cu13` を渡す(メモ server-vllm-ops)。どうしても Toolkit を入れるなら、`cuda-toolkit-12-x` か WSL 用の deb だけを使う(`cuda`・`cuda-drivers` のメタパッケージは禁止)[S20]。
3. **venv と版固定の pip(許可の後・P2)**。requirements の案(まだ入れない):
   ```text
   # requirements-5070-wsl.txt(案)=WSL 側の vLLM サーバー専用。本体の pyproject には入れない
   vllm==0.28.0
   torch==2.13.0          # vllm 0.28.0 の requires_dist と同じ [S8]
   torchvision==0.28.0
   torchaudio==2.11.0
   ```
   ```bash
   python3 -m venv ~/venvs/vllm-0280 && source ~/venvs/vllm-0280/bin/activate
   pip install -r requirements-5070-wsl.txt
   pip freeze > ~/venvs/vllm-0280.freeze.txt     # 実際に入った版を記録(ライセンス台帳と性能の記録へ)
   python -c "import torch;print(torch.__version__, torch.version.cuda, torch.cuda.get_device_capability())"   # (12, 0) を期待
   ```
   注: 0.28.0 の `requirements/cuda.txt` は `flashinfer-cubin` を `flashinfer.ai` の索引から取るが、PyPI の wheel の依存には入らない[S6]。flashinfer.ai は許可の一覧の外なので**足さない**(JIT で代える)。
4. **重みの取得(許可の後・P3)**。WSL の Linux 側のディスクに置く(`/mnt/c` 越しは遅いと見込む=未確認):
   ```bash
   hf download Qwen/Qwen3-8B-AWQ --revision 4da05a8edb55c6046cce958586c33b61da07bb79 \
       --local-dir ~/models/Qwen3-8B-AWQ     # CLI の名前(hf/huggingface-cli)は入る版によって違う=未確認
   sha256sum ~/models/Qwen3-8B-AWQ/*.safetensors > ~/models/Qwen3-8B-AWQ.sha256   # ライセンス台帳に行を足す
   ```
5. **起動前の VRAM の確認(Windows 側)**: `nvidia-smi` の使用量を見て、util を「(12,227 − 使用中 − 300) ÷ 12,227」以下に決める(300 MiB は expedient の余白)。
6. **`vllm serve` の起動(WSL 側)**。1 本の bash の行に環境変数を並べる(9 月の tmux の教訓=export に頼らない):
   ```bash
   VLLM_BATCH_INVARIANT=1 VLLM_USE_FLASHINFER_SAMPLER=0 VLLM_WORKER_MULTIPROC_METHOD=spawn \
   PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
   ~/venvs/vllm-0280/bin/vllm serve ~/models/Qwen3-8B-AWQ \
     --served-model-name qwen3-8b-awq --host 127.0.0.1 --port 8000 \
     --quantization awq_marlin --dtype float16 \
     --max-model-len 4096 --gpu-memory-utilization 0.78 \
     --max-num-seqs 32 --max-num-batched-tokens 4096 --enable-prefix-caching \
     --seed 0 2>&1 | tee ~/logs/vllm-5070-$(date +%Y%m%d-%H%M).log
   ```
   起動ログから KV の容量(トークン数)・注意の層の名前・CUDA グラフの捕捉の成否・バッチ不変の有効を写して残す。`--host 127.0.0.1` で Windows の `localhost` から届くかは、localhostForwarding の既定(true)[S23] に頼る。届かなければ `--host 0.0.0.0` に変える(LAN に開くので Windows のファイアウォールの確認が要る)[S22]。
7. **健全性の 1 呼(Windows 側)**:
   ```powershell
   curl.exe -s http://127.0.0.1:8000/v1/models
   curl.exe -s http://127.0.0.1:8000/v1/chat/completions -H "Content-Type: application/json" -d '{\"model\":\"qwen3-8b-awq\",\"messages\":[{\"role\":\"user\",\"content\":\"一言で返事を\"}],\"max_tokens\":16,\"temperature\":0,\"seed\":1,\"chat_template_kwargs\":{\"enable_thinking\":false}}'
   ```
   合格: 200 が返る・本文に `<think>` の中身が無い・`usage` がある。
8. **バッチ不変の確認(B14 の形・WSL 側)**: `tools/bench_spikes/batch_invariance_check.py` を WSL 側の venv で動かす(aiohttp を使う。vLLM の依存に入っているかは未確認。本体の `.venv` には無い)。
   ```bash
   python /mnt/c/<リポ>/tools/bench_spikes/batch_invariance_check.py --url http://127.0.0.1:8000 \
     --model qwen3-8b-awq --probes /mnt/c/<リポ>/tools/quality_probe_v0/probes.jsonl \
     --out ~/b14_5070_inv1.json --label 5070-awq-inv1
   ```
   合格の線は A5000 と同じ=**T6a 32/32・logprobs 32/32・T6b 32/32**[R7]。比較のため、`VLLM_BATCH_INVARIANT=0` でも 1 回回す(A5000 では 3/32)。注: この道具は `enable_thinking` を送らないので、Qwen3 は思考の形で答える(不変性の判定には足りるが、本番の形とは違う)。本番の形で測る道具に直すかは親の判断。
9. **艦隊クライアントの接続(Windows 側)**: 先に 24 刻みのスモーク(CLAUDE.md §4)。
   ```powershell
   .venv\Scripts\python.exe -m shibuya.cli --agents 5000 --seed 1 --world data/world/v2 --ticks 24 `
     --llm fleet --endpoints http://127.0.0.1:8000 --model qwen3-8b-awq `
     --mode smoke --run-id e1-5070-smoke24 --fleet-wait-s 120 `
     --tape <新しい空のディレクトリ> --checkpoints-out <新しい名前>.json
   ```
   見るもの: 書式エラー・`fleet_infra_clip`(length で切れた数)・繰り延べ・TTFT。レプリカ 1 本なので、route は `mod 1`=全部 1 本に行く(`plan_batch` の n_replicas=1)。
10. **E1 の起動(ユーザーの明示の後・Windows 側)**: 9 から `--ticks 24` を外し(既定 1,440)、`--run-id e1-5070-s1` とする。`--fleet-wait-s 120` は必須(0 にすると応答が終わりに集まる=lessons §3)。出力先が在れば止める(lessons §8)。終わったら vLLM を止め(WSL の端末で Ctrl+C/`wsl --terminate <配布物>`)、ログのパスをマスクする(lessons §7 の 10)。§6-0 の起動の台本は、この 5〜10 を 1 本にまとめる(親の作業)。

---

## §5 所要時間の見積り(E1〜E8)

### 前提

| 量 | 値 | 出どころ |
|---|---|---|
| 呼数(5,000 体・v3 既定・1 日) | **62,176**(mock の数。実 LLM では変わり得る) | [R5] sp1b |
| 入力/呼 | 宣言 ≤1,300。実測は 914(5,000 体・9 月)〜1,419〜1,427(39 万体・9 月) | 予算 M11・[R3][R2] |
| 出力/呼 | 宣言 o64。実測の平均 37.1〜37.2(上限 96) | [R2] |
| A5000 の AWQ と INT8 の比 | 0.757(同じ形=入力 1,500・出力 128・c32・`tok_s_total` 4,525.66 ÷ 5,980.58) | [R1] |
| A5000 の INT8・o64 の呼/s | キャッシュなし 4.39(400 呼/91.1 s)・階層の prefix(当たり 58〜68%)8.07〜9.36 | [R1] |
| 5070 と A5000 の比(llama.cpp・Llama 2 7B Q4_0) | prefill(pp512)1.27〜1.29・decode(tg128)0.94〜0.98 | [S25] 5070: 5,184.75/5,783.44 と 127.54/128.21、A5000: 4,028.16/4,552.15 と 130.07/135.83 |
| WSL の係数 | 0.7〜1.0(5090 の単発の decode で「WSL2 はネイティブの約 70%」。バッチの多いときの値は無い) | [S11] |
| エンジンだけの時間(mock・5,000 体・1 日) | 63.4 s(2 日のランは 105.6 s) | [R5] |

### 式

- 5070 の呼/s: r = (A5000 INT8 の呼/s) × 0.757 × (5070/A5000 の比) × (WSL の係数)。
  - 最小: 4.39 × 0.757 × 0.94 × 0.7 = **2.2 呼/s**(キャッシュが効かず、decode 律速の比を使い、WSL が 70%)。
  - 中央: 8.7 × 0.757 × 1.1 × 0.85 = **6.2 呼/s**(expedient の中間)。
  - 最大: 9.36 × 0.757 × 1.29 × 1.0 = **9.1 呼/s**。
  - 補正: 本番の入力(914〜1,427)と出力(37)は、試験の入力 1,500・出力 64 より軽い。上の幅は保守側に寄る。KV に入る列が 24〜30 本で、A5000 の c32 よりやや少ないぶんは下に寄る(未計測)。
- 壁時計 T ≈ N ÷ r + (呼の少ない刻みの下限:約 480 刻み × 1〜3 s。TTFT+37〜96 トークンの decode=expedient) + エンジン(1〜5 分。艦隊があると P2 の壁時計が GIL で延びる=メモ)+ 起動(モデルの読み込み・CUDA グラフ・JIT で 5〜15 分。Blackwell は JIT が数分延びる[S3])。

### 結果

| # | 実験 | 呼数の前提 | 最短 | 中央 | 最長 | 注 |
|---|---|---|---|---|---|---|
| **E1** | 既定 × 1 日 × 実 LLM | 62,176 | **約 2.1 h**(1.9 h+8 分+起動) | **約 3.2 h**(2.8 h+16 分+起動) | **約 8.5 h**(7.9 h+24 分+起動) | 1:00 開始なら 3:10〜9:30 に終わる。7 GPU の実測 30〜37 分(lessons §10)を単純に 7 倍すると 3.5〜4.3 h。ただし 7 GPU のランは刻みの往復(1.23 s/刻み)で決まっていて、GPU は飽和していなかった(5,000 体では呼数 2.09 倍で壁時計 1.24 倍=lessons §3)。単純な 7 倍は上側の目安 |
| E2 | 腕を全部 on × 1 日 | mock で v3_mem_rel 64,500 [R5]。会話の発話と T2(思考あり)の呼は**未計測** | E1 × 1.0 | E1 × 1.3〜2 | E1 × 2 以上 | T2 の帯は `enable_thinking=true` で出力が長い=decode が増える。E1 で測った r と、E2 の mock の呼数から引き直す |
| E3 | mock・古典で 30 日 | GPU なし | 約 26 分(52.8 s/日 × 30) | 約 32 分(63.4 s/日 × 30) | 1 h 以上(状態の育ち方は未計測) | **今は `--sim-days` の開始日検査(5 日まで)で止まる**=回答 10-25 §6-1 の 3 の後 |
| E4 | 30 日 × 実 LLM | 62,176 × 30 | 約 63 h | 約 96 h | 約 255 h | 1 晩では終わらない=数晩に分けて再開する。実 LLM での resume==straight は未証明(lessons §11-1) |
| E5 | ペルソナ 3 構成 × 1 日 + 生い立ち 5,000 体 | 3 × 62,176 + 5,000 呼(出力 約 600 トークン) | 3 × E1 + 約 1 h | 3 × E1 + 約 1.5 h | 3 × E1 + 約 2.5 h | 生い立ちの生成は W17 の実測(A5000 INT8 で 2.25〜2.3 呼/s・出力の平均 587 トークン)[R4] × 出力比 0.757 [R1] × tg 比 0.94〜0.98 × WSL 0.7〜1.0 ≒ 1.1〜1.7 呼/s。長い出力で KV に入る列が減るぶんは未計測 |
| E6 | 店舗選択 4 腕 × 1 日 | 4 × 62,176 | 4 × E1 = 8.4 h | 12.8 h | 34 h | R-K の後 |
| E7 | 揺らし × 古典と LLM | 腕の数は未定 | LLM 1 腕 = E1・古典 1 腕 = 1〜2 分 | — | — | 計器ができてから |
| E8 | 即断(ModernBERT-ja 3.1 億)と Ruri | vLLM ではない | 未計測 | 未計測 | 未計測 | torch が要る(新しい依存=許可待ち)。WSL 側の venv の torch を使えば、追加は transformers と重みだけ(未確認) |

結論: **夜に 1 本回せるのは E1・E2・E3・E5 の 1 構成まで**。E4 と E6 は数晩かかる。E1 の実測の r(呼/s)が出たら、この表を実測で置き換える(§6-7 の計測の分離の一覧に「GPU ごとの処理量」の欄がある)。

---

## §6 失敗の型と対処

| 型 | 兆し | 対処 |
|---|---|---|
| VRAM 不足 | 起動時に「KV の場所が足りない/free memory が util より少ない」の類で止まる。走行中は preemption の警告が増える | util を 0.05 ずつ下げる/机上アプリを閉じる(使用中 2,081 MiB)/`--max-num-batched-tokens 2048`/`--max-model-len 2048`(T2 の切れが増えるので記録)/最後の手で `--kv-cache-dtype fp8`(出力が変わる=別の腕として記録)。WSL2 + Blackwell で約 16 GiB の見えない使用分が出た報告(Mamba 系のモデル・GitHub #41619)は検索の要約だけで**未確認** |
| sm_120 のカーネルが無い | `no kernel image is available`・`cutlass ... capability 120` の類 | torch が cu128 以上か確かめる[S29]。`awq_marlin`+`--dtype float16` を明示[S11]。注意の層を `TRITON_ATTN` に[S10][S13]。それでも駄目なら vLLM 0.32.0(SM12x の項が入っている)[S4] |
| `awq` が落ちる | `--quantization awq` で dtype の検証エラー(報告=未確認)[S13] | `awq_marlin` を使う |
| CUDA グラフの捕捉で落ちる | 捕捉の途中で `cudaErrorUnknown` | WSL を新しくする(5090 では WSL 2.7.0 で直った報告)[S11]。最後の手で `--enforce-eager`(5090 では 8 分の 1 の速さ=E1 が 1 晩に入らない)[S11] |
| WSL のネットワーク | Windows から `curl http://127.0.0.1:8000` が届かない | localhostForwarding(既定 true)を確かめる[S23]。`--host 0.0.0.0` に変える/`.wslconfig` で `networkingMode=mirrored`(Windows 11 22H2 以上)[S22]。VPN 系の常駐が CUDA の初期化を邪魔した報告(Tailscale)[S11] |
| WSL が勝手に止まる | 夜中にサーバーが消える | `instanceIdleTimeout=-1`[S23]。サーバーは前景のプロセスとして持ち続ける(起動の台本の作り方=親) |
| ドライバの版 | CUDA 13 の wheel で初期化に失敗 | CUDA 13 は R580 以上[S3](今は 617.42=足りる)。Windows Update でドライバが変わったら、ログに版を残す。WSL の中に Linux のドライバを入れていないか確かめる[S20] |
| 思考が出る | 応答に `<think>` の中身が入り、2 行形のパーサが落ちる | `chat_template_kwargs` が届いているか(vLLM なら届く)。(C) Ollama ではここで落ちる[S26] |
| TTFT のタイムアウト(60 s) | 繰り延べ(`DEFERRED_TIMEOUT`)が出る | クライアントは 64 本まで送り、vLLM は 32 本だけ実行する。混む刻みで 64 本が待つと、6 呼/s で約 11 s=60 s の内側に収まる見込み。r が 2 呼/s まで落ちると 32 s 前後。繰り延べが出たら、2-7(背圧)の前の E1 は「動くかどうか」の結論にとどめる |
| **バッチ不変が成り立たない** | §4 の 8 で T6a/T6b が 32/32 にならない | 代わりに「**温度 0 の再現性だけ**」を確かめる=同じ 32 本を、並列 1 本ずつで 2 回送って一致するか(逐次なら組み方の影響が出ない)。本番(温度 0.7)の再ランの一致は主張しない=「分布同値の宣言」のまま(B14 の結論 4 と同じ扱い)。manifest に「5070 では不変性の自検証が不合格」と書く |
| 9 月との比較の取り違え | 行動の分布が 9 月とずれる | モデルが INT8 → AWQ に変わっている(§3)。`--generation-config` の扱い(P6)・presence_penalty を送っていないことも記録する |

---

## §7 出典の表(読んだ日はすべて 2026-10-25)

| # | URL | 確かめたこと |
|---|---|---|
| S1 | https://docs.vllm.ai/en/latest/features/batch_invariance.html | beta・CC 8.0 以上・試験済みの一覧に `Qwen/Qwen3-8B-AWQ`・SM120/コンシューマ GPU の記述なし・`VLLM_BATCH_INVARIANT=1`・性能に影響し得る(頁の日付 2026-10-19・latest の版) |
| S2 | https://docs.vllm.ai/en/latest/configuration/env_vars.html | `VLLM_BATCH_INVARIANT` の注「compute capability >= 9.0」・`VLLM_USE_FLASHINFER_SAMPLER`・`VLLM_WORKER_MULTIPROC_METHOD`(既定 fork) |
| S3 | https://docs.vllm.ai/en/latest/getting_started/installation/gpu.html | OS は Linux・Windows は WSL・Python 3.11〜3.14(latest の頁)・CC 7.5 以上・Blackwell は CUDA 12.8 以上・CUDA 13 は R580 以上・JIT は Blackwell で数分延びる |
| S4 | https://github.com/vllm-project/vllm/releases | v0.32.0=Latest・18 Oct・PyPI 既定 CUDA 13.0・SM12x の項(NVFP4 KV・XQA) |
| S5 | https://github.com/vllm-project/vllm/releases/tag/v0.28.0 | 26 Aug 公開・PyPI 既定 CUDA 13.0・「FlashInfer XQA decode support on SM12x」 |
| S6 | https://raw.githubusercontent.com/vllm-project/vllm/v0.28.0/requirements/cuda.txt | `torch==2.13.0`・`torchaudio==2.11.0`・`torchvision==0.28.0`・flashinfer 0.6.16.post3(flashinfer-cubin は PyPI の依存から外れる) |
| S7 | https://raw.githubusercontent.com/vllm-project/vllm/v0.32.0/requirements/cuda.txt | 同じ torch 2.13.0・flashinfer-python 0.7.0.post1 |
| S8 | https://pypi.org/pypi/vllm/0.28.0/json | requires_python `>=3.10,<3.15`・Apache-2.0・x86_64 の wheel 314,500,103 B・2026-08-26 掲載・requires_dist の torch 3 本 |
| S9 | https://docs.vllm.ai/en/latest/features/quantization/index.html | 対応表の列は Hopper まで=Blackwell の列なし |
| S10 | https://docs.vllm.ai/en/latest/configuration/engine_args.html | `--gpu-memory-utilization` 既定 0.92・`--dtype half` は AWQ に推奨・`--generation-config` 既定 auto(モデルの値を読む)・`--kv-cache-dtype` の選択肢・`--attention-backend` |
| S11 | https://github.com/vllm-project/vllm/issues/37242 | RTX 5090(sm_120)・WSL2 2.7.0・ドライバ 581.80・vLLM 0.17.1・Qwen3-14B-AWQ を `awq_marlin --dtype float16` で約 140 tok/s(単発)・WSL2 はネイティブの約 70%・eager は約 17 tok/s・FP8 は 3 分の 1・環境変数 2 本・Tailscale の干渉 |
| S12 | https://discuss.vllm.ai/t/running-nvfp4-nemotron-model-on-win11-wsl-rtx-5080-5070-ti/2310 | 5080+5070 Ti・WSL 2.5.9・ドライバ 591.86。公式の image は NVFP4 で SM120 のカーネル不足で落ち、NVIDIA の container で動いた(AWQ ではない) |
| S13 | https://discuss.vllm.ai/t/field-report-awq-on-rtx-5060-ti-sm-120-blackwell-awq-marlin-triton-attn-working/2463 | **本文は 404 で読めず=未確認**。検索の要約に「`awq` は bf16 固定で落ちる・`awq_marlin`+`TRITON_ATTN` で動く・vLLM 0.17.2rc1・torch 2.10.0+cu130」とあるだけ |
| S14 | https://huggingface.co/Qwen/Qwen3-8B-AWQ | apache-2.0・AWQ 4-bit・`vllm>=0.8.5`・思考の既定 on・非思考の推奨サンプリング・presence_penalty 1.5 の推奨・文脈長 32,768 |
| S15 | https://huggingface.co/api/models/Qwen/Qwen3-8B-AWQ と同 `/tree/main` | sha `4da05a8e…`・gated=false・safetensors 2 本の大きさ(合計 6,098,581,864 B) |
| S16 | https://huggingface.co/Qwen/Qwen3-8B-AWQ/raw/main/config.json | 層 36・KV ヘッド 8・head_dim 128・torch_dtype float16・bits 4・group_size 128・version gemm |
| S17 | https://huggingface.co/Qwen/Qwen3-8B-AWQ/raw/main/generation_config.json | temperature 0.6・top_k 20・top_p 0.95 |
| S18 | https://huggingface.co/api/models/Qwen/Qwen3-8B-GGUF と同 `/tree/main` | apache-2.0・sha `7c41481f…`・Q4_K_M 5,027,783,488 B |
| S19 | https://huggingface.co/api/models/Qwen/Qwen3-8B-FP8/tree/main | safetensors 合計 9,436,628,784 B |
| S20 | https://docs.nvidia.com/cuda/wsl-user-guide/index.html | v13.4・2026-10-12 更新・Linux のドライバを入れない・`cuda-toolkit-12-x` だけ・pinned memory は限られる・nvidia-smi は `/usr/lib/wsl/lib` |
| S21 | https://learn.microsoft.com/en-us/windows/wsl/install | 管理者で `wsl --install`→再起動・`-d` で配布物・`--list --online`(一覧の外のドメインだが読むだけ) |
| S22 | https://learn.microsoft.com/en-us/windows/wsl/networking | NAT の既定で Windows から `localhost` で届く・mirrored は 22H2 以上・LAN からは 0.0.0.0 とファイアウォール |
| S23 | https://learn.microsoft.com/en-us/windows/wsl/wsl-config | memory の既定 50%・swap 25%・localhostForwarding の既定 true・instanceIdleTimeout の既定 15000 ms(-1 で無効)・vmIdleTimeout 60000 |
| S24 | https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md | `-np`・連続バッチの既定 on・`--chat-template-kwargs`・`cache_prompt` で「バッチの大きさが違えば logits はビット単位で同じでない」。`/v1/chat/completions` の欄(要求ごとの `chat_template_kwargs`)は頁の取得範囲に入らず**未確認** |
| S25 | https://github.com/ggml-org/llama.cpp/discussions/15013 | 表の RTX 5070 と RTX A5000 の pp512・tg128(§5 の前提の表) |
| S26 | https://docs.ollama.com/api/openai-compatibility | 受ける欄(seed・stream_options.include_usage・reasoning_effort ほか)・`"none"` で思考を切る・`chat_template_kwargs` の記載なし |
| S27 | https://docs.ollama.com/faq | `OLLAMA_NUM_PARALLEL` の既定 1・`OLLAMA_MAX_QUEUE` 512・超えると 503・文脈の既定 4096 |
| S28 | https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5070-family/ | 6,144 CUDA コア・12 GB GDDR7・192 bit・988 AI TOPS・250 W。**帯域の値は頁に無い=未確認** |
| S29 | https://pytorch.org/blog/pytorch-2-7/ | 2.7 で Blackwell 対応(prototype)・CUDA 12.8 の wheel |
| S30 | https://raw.githubusercontent.com/vllm-project/vllm/v0.28.0/vllm/model_executor/layers/batch_invariant.py | SM80 だけ別の道・注は「Hopper(SM90)と Blackwell(SM100)」・設定する環境変数(CUBLAS_WORKSPACE_CONFIG ほか)・SM120 の記述なし |

リポの中の記録:

| # | 場所 | 使ったこと |
|---|---|---|
| R1 | `docs/bench/bench_ledger.csv` の `p18-Qwen3-8B-w4a16-awq-mnbt8192-c32`・`p18-Qwen3-8B-w8a8-int8-mnbt8192-c32`・`m2-8b-int8-olenNC-c32-o64`・`m3-h-d3-*-o64` | A5000 の AWQ と INT8 の比・o64 の呼/s |
| R2 | `docs/ops/build-report-C7.md` の 64・114 行 | 入力の平均 1,419/1,427・出力の平均 37.2/37.1 |
| R3 | `docs/ops/build-report-C8.md` の 42 行 | 5,000 体・実 LLM・1 腕 35 分・入力 914 tok |
| R4 | `docs/ops/build-report-C5.md` の 87・89 行 | W17 の生成 2.25〜2.3 呼/s/GPU・出力の平均 587 |
| R5 | `docs/bench/analysis/spatial-2026-10/sp1b/README.md` の 180・378・448 行 | 62,176 呼・63.4 s/日・2 日 105.6 s |
| R6 | `docs/design/v2-budget-declaration.md` の M11・L6 | 入力 ≤1,300・出力 o64・64 in-flight/GPU |
| R7 | `docs/bench/b14_batch_invariance/README.md` | A5000 で T6a・T6b 32/32・不変 off で 3/32 |
| R8 | `tools/quality_probe_v0/run_b10_b11.sh` の 9 行 | 9 月の `vllm serve` の引数(max-model-len 4096・batched 8192・seqs 32・prefix on・generation-config の指定なし) |

---

## §8 親の一次確認の欄(空欄)

| # | 確かめること | 結果 | 確かめた日 |
|---|---|---|---|
| C1 | S1 の試験済みの一覧に `Qwen/Qwen3-8B-AWQ` があるか・CC の記述(S2 との食い違い) | | |
| C2 | S6/S8 の `torch==2.13.0`・vLLM 0.28.0 の PyPI 既定が CUDA 13.0 か | | |
| C3 | S15/S16 の sha・大きさ・層/KV ヘッド/head_dim(144 KiB/トークンの再計算) | | |
| C4 | S11 の構成(`awq_marlin`・`--dtype float16`・WSL2 の版) | | |
| C5 | S25 の 5070 と A5000 の数値・R1 の 4 行の再計算(0.757・4.39・8.07〜9.36) | | |
| C6 | §5 の E1 の式の再計算(2.2/6.2/9.1 呼/s → 1.9/2.8/7.9 h) | | |
| C7 | S13(本文が読めなかった報告)の扱い | | |
| C8 | 許可の一覧(P1〜P7)を PENDING §1 に載せるか | | |

## 親の一次確認(第339・2026-10-25・Fable 5.1)

- 機械: 親も `wsl --status` を実行=「インストールされていません」の旨(UTF-16)。`nvidia-smi`=NVIDIA GeForce RTX 5070・ドライバ 617.42・12,227 MiB・使用中 2,207 MiB(親の時点)=本文 §1 と一致。
- 重み: `huggingface.co/Qwen/Qwen3-8B-AWQ` のカード(親が 2026-10-25 に実読)=License apache-2.0・AWQ 4-bit・8.2B(非埋め込み 6.95B)・`sglang>=0.4.6.post1 or vllm>=0.8.5`・`enable_thinking=True` が既定・non-thinking の推奨 Temperature 0.7/TopP 0.8/TopK 20/MinP 0・量子化モデルは presence_penalty 1.5 を強く推奨=本文 §3 と一致。合計の容量はカードに記載なし(本文の 6,098,581,864 B は revision のファイル一覧から=親は未確認)。
- vLLM 0.28.0: PyPI の JSON(親が実読)=`requires_python <3.15,>=3.10`・`torch==2.13.0`・`torchvision==0.28.0`・`torchaudio==2.11.0`・`flashinfer-python==0.6.16.post3`・公開 2026-08-26=本文 §2・P2 と一致。PyPI は OSV の脆弱性の注記を多数付ける(0.29.0/0.30.0 で修正)=**手元の 127.0.0.1:8000 だけで使い、外に開けない**(親の注)。
- 未確認のまま(本文どおり): `VLLM_BATCH_INVARIANT=1` が sm_120 で効くか(B14 を 32/32 で通してから使う)・5070 の帯域・WSL の係数。所要時間の表(§5)は expedient の式=E1 の実測で置き換える。
- 許可待ち P1〜P7 は第 N の報告でユーザーへ。P6(`--generation-config`)は親案=既定のまま(9 月のサーバーと同じ条件)。
