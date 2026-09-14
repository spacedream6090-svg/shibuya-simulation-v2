# レーンM答申: run manifest形式(U8)と並行実行の意味論(U9)

<!-- hdr:v1 -->
- **分野**: ソフトウェア工学 #29 / 計算機科学(並列・決定論) #28 | **重要度**: P1(親判断・2026-09-15 第191)
- **一次確認**: **B** = 出典あり・空欄を明示(残務台帳へ写し済みまたは要写し) — 出典痕跡 102 件。空欄節あり
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **分野地図**: [v2-discipline-map.md](v2-discipline-map.md)

> **親検収(Fable・2026-09-07)**: 出典を親が一次確認した。✔=親が実読して一致。
> - ✔ vLLM公式docs(実読): features/batch_invariance「NVIDIA GPUs with compute capability 8.0 or higher」・有効化=`VLLM_BATCH_INVARIANT=1`・「disables custom all-reduce operations in tensor parallel mode」。configuration/env_vars「Requires NVIDIA GPU with compute capability >= 9.0」。**答申の「公式内で8.0+と9.0の矛盾」は事実**(借用サーバーのA5000=8.6は境界=自検証テストT6が必要)。
> - ✔ Thinking Machines「Defeating Nondeterminism in LLM Inference」(実読): Qwen3-8B・1GPU・1,000系列(出力90-110tok)で既定26秒/決定的55秒/改良注意カーネル42秒。「the primary reason nearly all LLM inference endpoints are nondeterministic is that the load (and thus batch-size) nondeterministically varies」・forward passはatomic addを要する演算を含まない。**リポのベンチ「BATCH_INVARIANT=1のコスト−2%以下」との乖離は版差か負荷形状差(v2はprefill律速)=要説明(答申の指摘は妥当)**。
> - 既決「R16検証ランはTP1」は公式のcustom all-reduce無効化記述と整合(TP4の4.1%非再現の機構と一致)。
> - ACM DL/Elsevier/IEEE 1516の13件は403/有料で未読=答申の申告どおり書誌のみ(主張の根拠に使っていない)。FLAME GPU 2・Wilensky & Rand 2007・JASSSは答申が実読と申告(親は未再読)。
> - 正典化: docs/research/v2-run-manifest-concurrency-research.md(U8/U9の根拠)。

> 作成: 2026-09-07 / リサーチサブ(Opus 5) / 親=Fable検収・決定=ユーザー
> 規律遵守: 子サブ未起動。出典は正規ドメインのみ・**実読ページからの引用のみ**を「引用」として提示。
> 読めなかったもの(403/paywall/PDF不可)は各節に **空欄(未確認)** と明示。推測は【推測】。

---

## 要約(10行)

1. **U8の骨格は既存標準の合流でよい**: 記述=ODD 2020の7要素(JASSS 23(2)7・実読)、実行=reana.yaml型の4問(入力/コード/環境/手順・実読)、来歴=Workflow Run RO-Crate(PROV整合)、実験メタ=MLflow型(params/metrics/artifacts/source version)。v2固有の追加はLLM艦隊欄・忠実度プロファイル欄・封印欄の3つ。
2. **再現性の主張水準は「分布同値(distributional equivalence)」が正解**。Wilensky & Rand 2007(JASSS 10(4)2・実読)の3水準——numerical identity / distributional equivalence / relational alignment——のうち、v2は**エンジン層=numerical identity(seed固定・同一機・同一版)/LLM層=distributional equivalence**の二層宣言を推奨。
3. **vLLM公式は「既定では再現性を保証しない」と明言**(実読)。ただし V1 では `seed` 既定=0 で「temperature > 0 でも各vLLMランで結果は一貫」と書かれている。保証の前提は**同一ハードウェア・同一vLLM版**。
4. **BATCH_INVARIANT=1 は「バッチサイズ・バッチ内の順序に依らず決定的」を与える**(実読)。ただし**公式ドキュメント2ページで要求計算能力の記述が食い違う**(features頁=8.0以上/env_vars頁=9.0以上)。A5000=8.6のため**親の一次確認必須**(自前ベンチでは動いている=実測が正)。
5. **TP/量子化が非決定性の主因**: batch invariantは「テンソル並列のcustom all-reduce等、非決定性を持ち込む最適化を無効化する」(実読)。量子化側は `VLLM_MARLIN_USE_ATOMIC_ADD` が**既定0**で、PR #14138に「fp16 atomicAddで#6795の問題が再発しないか確信がない」との実読引用あり=**atomicAdd系リダクションは非決定の既知の穴**。リポの自前実測(32B AWQ TP4が温度0で4.1%非再現)と機構的に整合。
6. **U9の標準は「同期 vs 非同期 × 順序付け」**: NetLogo=`ask`はエージェント集合を**常にランダム順**で読み、4.0以降は逐次(実読)。Mesa=sequential/random(`shuffle_do`)/simultaneous(step→advance)/staged の4型で「**行動順序はモデル結果を大きく左右しうる**」と明記(実読)。Agents.jl=スケジューラは「ABMを受けてエージェントID列のイテレータを返す関数」(実読)。
7. **スケジューリングは結果を動かす=expedientでなくmechanism扱いが必要**: Weimer et al. 2019(JASSS 22(4)5・実読)は「同期性を変えると収束時の意見分散と収束パラメータの関係が変わった」「**どのスケジュールも順序バイアスの効果を完全には除去しなかった**」と報告。
8. **同一tick内競合の推奨形は「二相(bid→resolve→commit)+決定論的優先度キー」**。先例=FLAME GPU 2(実読PDF): 逐次実装は「公平性のためエージェント順をランダム化」、並列実装は**bidding**で「最高優先度のエージェントだけが移動を許される・優先度はランダム付与で公平性を担保」。さらに「**アトミック演算の順序は非決定的でGPUの実行モデルが決める**」ため、優先度が意味を持つ場合はsub-model(bidding)で解くべき、と明記。
9. **非同期LLM応答は「次tick先頭で決定論的順序に整列して適用」で十分**。世界の書き込み口はエンジンのresolve一本(既決)なので、PDESの楽観同期(Time Warp・ロールバック)は**要らない**。要るのはPDESの**lookahead概念**だけで、v2ではδ_perc+δ_think(=最短適用時刻)がそのままlookaheadになる。
10. **タイブレークの正典はDEVSの`select`型=固定規則**。v2推奨は `key = BLAKE3(run_salt ‖ tick ‖ event_class ‖ resource_id ‖ agent_id)` の昇順——「乱数だが順序は再現する」を1式で満たし、id順バイアス(v1 C-8)を根治する。

---

## 問い1. 再現性の記録(U8): 何を manifest に書くか

### 1.1 先行標準の実読要点

**(a) ODD 2020(モデル記述の正典・JASSS 23(2)7・実読)**
7要素は「1. Purpose and patterns / 2. Entities, state variables and scales / 3. Process overview and scheduling / 4. Design concepts / 5. Initialization / 6. Input data / 7. Submodels」。
引用: 「Incomplete descriptions violate the central requirement of science that materials and methods must be specified in sufficient detail to allow replication of results.」
引用(要素5): 「detail sufficient for readers to fully understand the model and its rationale and, in principle, completely re-implement it.」
→ **含意**: ODDは「モデルの記述」、manifestは「1回の実行の記述」。**両者を分離し、manifestはODD文書の版ハッシュを1欄で参照する**のが正しい接続(ODDを毎ラン複製しない)。

**(b) ODD+D(人の意思決定を扱うABMの拡張・Müller et al. 2013・Environmental Modelling & Software 48, 37-48・doi:10.1016/j.envsoft.2013.06.003)**
検索結果より: 「ODD+D は 'Theoretical and Empirical Background' の節を導入し、理論により密接に結びついたモデル設計と仮定を促す」。
→ **注記: 本文未読(検索結果の要約のみ)=一次確認は親へ**。v2との関係は明白で、**LLMが意思決定器である以上「理論的・経験的背景」の欄がmanifestでなくODD側に必要**(=知覚契約書・行動契約書がその実体)。

**(c) reana.yaml(実行の記述・docs.reana.io・実読)**
top-level = `version` / `inputs`(files, directories, parameters, options)/ `workflow`(type, file, specification, resources)/ `outputs`(files, directories)/ `workspace`(retention_days)。
引用(`workflow.type`): 「Specifies workflow language type. Can be `cwl`, `serial`, `yadage`, `snakemake`」
引用(`version`): 「Specifies REANA version to which the analysis was written for. For example, '0.6.0'.」
→ **含意**: REANAが「入力はどこ/コードはどこ/どの計算環境/どの手順」の4問に答える形。**v2 manifestもこの4問+「どの世界か(データ資産のハッシュ)」+「どのLLM艦隊か」の6問**に整理できる。`workspace.retention_days` は v2 の S1/S2(恒久記録・checkpoint)保持窓の先例。

**(d) Workflow Run RO-Crate(来歴の記述・researchobject.org・検索結果)**
「Workflow Run RO-Crate is an extension of RO-Crate and Schema.org to capture the provenance of the execution of computational workflows at different levels of granularity and bundle together all their associated objects (inputs, outputs, code, etc.)」「The model is aligned to standards such as W3C PROV」。3プロファイル階層: Process Run Crate ⊂ Workflow Run Crate ⊂ Provenance Run Crate。
→ **注記: プロファイル本文は未読(検索結果の要約)**。論文は PLOS ONE(doi:10.1371/journal.pone.0309210)/arXiv:2312.07852。
→ **含意**: v2で採るべきは**Process Run Crate相当の粒度**(1ラン=1エンティティ、入力/出力/実行環境を束ねる)。**Provenance Run Crate(全ステップの内部来歴)は過剰**——v2は400万呼/日で、呼ごとのPROVは容量破綻。

**(e) MLflow Tracking(実験メタの記述・mlflow.org・検索結果)**
「an API and UI for logging parameters, code versions, metrics, and output files」「Each run records metadata (…metrics, parameters, start and end times) and artifacts」「If you record runs in an MLflow Project, MLflow remembers the project URI and source version.」
→ **注記: 公式頁の本文は検索結果の引用のみ・直接読解は未実施**。
→ **含意**: params/metrics/artifacts/source-version の4分類は v2 にそのまま移せる。ただし**v2でのparamsは「忠実度プロファイル」1個に畳む**(§1.3)。

**(f) ACM Artifact Review and Badging(Repeatability/Reproducibility/Replicabilityの定義)**
→ **空欄(未確認)**: acm.org の当該ページは HTTP 403 で読めず。定義を引用できないため、本答申では ACM の語彙を使わず、**Wilensky & Rand の3水準(§2.4)を用語の正典とする**。

### 1.2 v2 manifest に載せるべき項目(親の設問リストへの逐条回答)

| 欄 | 載せる | 形 | 根拠/理由 |
|---|---|---|---|
| コード版 | ✔ 必須 | git commit SHA + dirty flag + `git describe` | MLflow「code versions / source version」。**dirty(未コミット変更あり)ランは較正・holdout照合に使わない**を規則化 |
| 設定ハッシュ | ✔ 必須 | 正規化YAMLの BLAKE3 | reana.yamlの`inputs.parameters`相当。**正規化規約が要る**(キー順・数値表記・改行)=知覚契約書§2.4のバイト一致規約を流用 |
| データハッシュ(OSM/PLATEAU/ペルソナ/KDDI) | ✔ 必須 | 資産ごとに {資産ID, 版, ライセンス台帳行, BLAKE3, バイト数, 件数} | reana `inputs.files/directories`。**件数も入れる**(v1の552ファイル照合の教訓) |
| シード | ✔ 必須 | **単一のmaster_seed + 派生規則の版**(§3.5) | 「乱数・個体・LLM」を別々に持つと合わせ忘れが起きる。**派生規則をコード側に置き、manifestにはmaster_seedと派生規則版だけ** |
| モデルID/量子化 | ✔ 必須 | HuggingFace repo id + revision(commit SHA)+ 量子化方式(W8A8-INT8等)+ 重みファイルのハッシュ | vLLM公式「vLLM only provides reproducibility when it runs on the same hardware and the same vLLM version」(実読)を満たす最低条件 |
| エンジン版 | ✔ 必須 | vLLM version + torch + CUDA driver + attention backend名 | 同上。**backendは明示**(batch invarianceはXPUでTRITON_ATTN必須、と公式に記載=実読) |
| デコード設定 | ✔ 必須 | temperature/top_p/top_k/max_tokens/stop/seed の**T1・T2別** | v2はT1=0.7個体シード、T2別 |
| 艦隊構成 | ✔ 必須 | {GPU枚数, TP, DP, PP, max_num_seqs, max_model_len, gpu_memory_utilization, in-flight上限(L6=64), 各レプリカのGPU index, NUMA束縛} | 第3-5段ベンチが示す通り**構成が結果とスループット両方を変える** |
| BATCH_INVARIANT | ✔ 必須 | 0/1 + 実効の検証結果(§2.5テスト) | ベンチ実測でコスト-2%以下=検証ランで常用可 |
| 時刻 | ✔ 必須 | 開始・終了のUTC ISO8601 + TZ + 経過壁時計 | MLflow「start and end times」 |
| ハードウェア | ✔ 必須 | プロファイル名(borrowed-2026-09等)+ GPU型番/driver/VRAM + CPU + RAM + トポロジ(NVLink有無・PCIe世代) | 予算宣言表§6と同じ粒度。**プロファイル名だけでなく実体も焼く**(借用機は9/10に消滅=名前だけでは復元不能) |
| 忠実度プロファイル | ✔ 必須 | プロファイル名 + そのハッシュ | 決定済み規律「比較するラン同士は同一プロファイル必須」を**機械検査可能にする**唯一の方法 |
| 予算値 | ✔ 必須 | W1/P1-P7/M1-M12/L1-L6/S1-S4 の**宣言値スナップショット** | 予算宣言表はdelta改版=**ラン時点の値を焼かないと事後に判定できない** |
| holdout封印ハッシュ | ✔ 必須 | 封印3層(D/S/P)ごとの {対象集合ハッシュ, 封印日時, 開封記録の有無} | 較正がholdoutに触れないことの**会計的証明**(方法論Phase 3ゲート) |
| 診断行 | ✔ 必須(**ラン成果物側**) | 繰り延べ量・昇格数・縮退実行数・抑止数(起床クラス別/シミュ日)+ 保存則残差・純資産=実物資産 | 予算宣言表 運用規則5。**manifestには「診断行が存在すること」のフラグとファイルハッシュ**を置く |
| **追加提案①** 実行モード | ✔ | `smoke|calibration|holdout|ablation|production` | L3(勘定分離)を機械化。**holdoutモードはholdout封印が開いていないと起動しない**をコードで強制 |
| **追加提案②** 仮説と事前登録 | ✔ | 仮説1文 + 判定指標 + 閾値 + ablation ID | OPEN-10b「HARKing防止」の実体。**事後に足せない**よう封印ハッシュ対象へ |
| **追加提案③** 親ラン参照 | ✔ | resume元のcheckpoint ID + そのハッシュ | S3退避・resume堅牢性(可搬性最優先) |
| **追加提案④** manifest自身のハッシュ | ✔ | 自己ハッシュ(自己欄を除く正規化本文のBLAKE3)= **run_id** | ラン同定子を内容から導出=同じmanifest→同じrun_id→衝突検出が無料 |
| **追加提案⑤** LLM入出力アーカイブの参照 | ✔ | ①恒久記録(全LLM入出力)のパス+ハッシュ+圧縮方式 | DECIDED-10c。**リプレイでなく直接記録**が正典なので、manifestは記録の在処を指す |
| 載せない | ✘ | 接続情報・ホスト名・IP・APIキー | CLAUDE.md §7 |

### 1.3 「予算値」と「忠実度プロファイル」の関係(親向けの設計注意)
予算宣言表はdelta方式で改版される。manifestに**予算行を丸ごとコピー**すると肥大するので、**(i)予算宣言表ファイルのcommit SHA+ハッシュ、(ii)そのランに効いた行だけの抜粋**の二段にするのが実務的。**【推測】**この二段化の先例は見つけられなかった=v2独自(expedient)。

---

## 問い2. LLMの再現性——どこまで主張できるか

### 2.1 vLLM公式が言っていること(docs.vllm.ai/en/latest/usage/reproducibility/ ・**実読**)
- 「vLLM does not guarantee the reproducibility of the results by default, for the sake of performance.」
- 「The `seed` parameter in vLLM is used to control the random states for various random number generators.」— 指定時は `random`・`np.random`・`torch.manual_seed` の状態を設定。
- 「In V1, the `seed` parameter defaults to `0` which sets the random state for each worker, so the results will remain consistent for each vLLM run even if `temperature > 0`.」
- 「Even with the above settings, vLLM only provides reproducibility when it runs on the same hardware and the same vLLM version.」
- オフラインはマルチプロセス無効化 or batch invariance、**オンライン(=v2が使うOpenAI互換サーバー)は batch invariance のみ**。
- `VLLM_ENABLE_V1_MULTIPROCESSING=0` は決定的スケジューリングを与えるが「will change the random state of user code」。

→ **v2への含意(重要)**: 「温度0.7+seed固定」で得られるのは**「1つのvLLMプロセスの寿命の中での一貫性」であって「別プロセス・別バッチ状況での同一性」ではない**。v2は艦隊(DP7)+バッチ非同期なので、**素のままでは同一manifestでもbit再現しない**。

### 2.2 バッチ不変性(docs.vllm.ai/en/latest/features/batch_invariance/ ・**実読**)
- 「the output of a model is deterministic and independent of the batch size or the order of requests in a batch」
- 有効化: `export VLLM_BATCH_INVARIANT=1`(server も同様)。
- 「Enabling batch invariance may impact performance compared to the default non-deterministic mode.」(具体数値はこの頁になし)
- 「(disables) certain optimizations that may introduce non-determinism (such as **custom all-reduce operations in tensor parallel mode**)」
- 対応: NVIDIA GPU(compute capability 8.0+)、Intel XPU(Triton・`--attention-config.backend TRITON_ATTN` 必須)。

**矛盾の検出(親の一次確認事項)**: 同じ公式サイトの環境変数一覧(docs.vllm.ai/en/latest/configuration/env_vars/ ・**実読**)は
- `VLLM_BATCH_INVARIANT`: 「Enable batch-invariant mode: deterministic results regardless of batch composition. **Requires NVIDIA GPU with compute capability >= 9.0.**」既定 `0`
と書いており、**features頁の 8.0+ と食い違う**。borrowed-2026-09 は A5000(Ampere・CC 8.6)。**リポのベンチ台帳は BATCH_INVARIANT=1 のコストを「-2%以下」と実測している=A5000で走った証拠**なので、実務上は8.6で動くと見てよい。ただし**「動く=数式上の不変性が成立している」ではない**ので、§2.5のテストで自分で確かめる必要がある。

### 2.3 非決定性の機構(thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/ ・**実読**)
vLLMのbatch invariance実装の元になった一次解説。
- 原因は浮動小数の非結合性そのものではなく**サーバー負荷**: 「When you make a query to an inference endpoint, the amount of load the server is under is effectively 'nondeterministic' from the user's perspective. The load determines the batch size that the kernels are run under, and thus changes the eventual result of each individual request!」
- 実験: Qwen3-235B・temperature=0・同一プロンプト1000回で **「80 unique completions」**、しかも「the completions are identical for the first 102 tokens」その後分岐。batch-invariantカーネル導入後は全て同一。
- コスト: 決定的推論は 1000リクエストで 55秒 vs baseline 26秒(**約2倍**)。
- 対象3演算: RMSNorm・matmul・attention。

→ **v2への含意**: 「温度0でも艦隊負荷が揺れれば出力が変わる」は**測定済みの事実**であり、v2の艦隊(DP7・in-flight 64・繰り延べアービタ)は**負荷が本質的に揺れる設計**。したがって**bit再現をランの既定要求にすることは設計と両立しない**(既決の「速度>決定論」と整合)。
→ ただし **thinking machines の2倍という数字と、リポのベンチの「-2%以下」は大きく食い違う**。実装が進んだ・負荷形状が違う(v2はprefill律速)・測定条件が違う、のいずれか。**親の一次確認候補**。

### 2.4 TP/DPで結果が変わる条件・量子化カーネル
- **TP**: batch invarianceが「custom all-reduce を無効化する」と明記(実読)= **TPのall-reduceは既定で非決定の源**。リポの自前実測「32B AWQ TP4は温度0でも4.1%非再現」(docs/bench/README.md)はこれと機構的に整合し、**R16検証ランをTP1・DP7艦隊にした判断は公式記述で裏づけられる**。
- **DP**: DPはレプリカ間で重みを共有せず独立に走るので、**「どのレプリカがどのリクエストを取るか」が結果を変える**。ルーティングが非決定なら出力も非決定。→ manifestに**ルーティング規則**(セルアフィニティ不採用・round robin等)を書く必要がある。BN-4の結論(アフィニティ不採用)はここに接続する。
- **量子化**: 公式env_vars(実読)に `VLLM_MARLIN_USE_ATOMIC_ADD`: 「Whether to use atomicAdd reduce in gptq/awq marlin kernel.」**既定 `0`**。GitHub PR #14138(実読)に開発者の言:
  - 「This PR add an argument `use_atomic_add` to marlin kernel, so that we don't require `barrier_acquire` and `barrier_release` anymore.」
  - 「So I disable the `atomicAdd` by default, and use the env variable `VLLM_MARLIN_USE_ATOMIC_ADD` to control the behavior.」
  - 「However, this `atomicAdd` use fp16, I don't sure if the issue fixed by #6795 would be introduced again (need more test).」
  → **atomicAddによるリダクションは順序非決定=既知の穴**。v2は AWQ/INT8 を使うので **manifestに `VLLM_MARLIN_USE_ATOMIC_ADD` の値を必ず記録**すべき(既定0のままにする=推奨)。
  - **空欄(未確認)**: 「W8A8-INT8(compressed-tensors)カーネルが決定的か」は公式文書に記述を見つけられず。**実測で確かめるしかない**。

### 2.5 主張できる水準(bit vs 統計)——先行の言明
**Wilensky & Rand 2007(JASSS 10(4)2・実読)** が3水準を与える(Axtell et al. 1996に基づく):
- **numerical identity**: 「showing that the original and replicated model produce the exact same numerical results」——同論文は「同じ機械で同じパラメータで同一プログラムを走らせても同一出力は保証されない」ため**この水準は確立が難しい**と述べる。
- **distributional equivalence**: 「the two implemented models are sufficiently statistically similar to each other」——実務は「statistical indistinguishability(現データでは分布が異なるという証拠がない)」を示す。
- **relational alignment**: 「the results of the two implemented models show qualitatively similar relationships between input and output variables」。
著者らは事例で**distributional equivalence を採用**。

**Paulsen, Rasmussen & Nielsen 2018(Procedia Computer Science 130, 850-857・doi:10.1016/j.procs.2018.04.078)**: MATSim(Santiago de Chile)で**100種の乱数シード**によるリンク交通量の出力ばらつきを測定。検索結果の記載では「relative errors of up to 10% do occur even for links with large volumes」。→ **注記: 本文・要旨とも未読(Elsevier 403)。数値は検索結果の要約=親の一次確認必須**。
→ **含意**: 「乱数シードだけで10%動く」なら、**シード1本のランを結論の根拠にしてはならない**=v2のアンサンブル第一主義に定量的な裏づけを与える(ただし要確認)。

### 2.6 40万体×温度0.7で何を主張できるか(答申の結論)
**二層宣言を推奨する。**

| 層 | 主張水準 | 条件 | テスト |
|---|---|---|---|
| **エンジン層**(物理・経済・スケジューリング・繰り延べ・保存則) | **numerical identity(bit再現)** | 同一manifest・同一機・LLM応答を録画リプレイ(§4.4)・CPU/単GPU・順序固定 | 同一manifest2回で**全checkpointのハッシュ一致** |
| **LLM層**(発話・行動選択) | **distributional equivalence** | 同一manifest・同一機・同一vLLM版 | 2ラン間で行動分布のJSD ≤ 帰無95%点(§8の指標B流用) |
| **世界全体**(結合系) | **relational alignment + distributional equivalence** | アンサンブルN本 | パターン台帳の照合指標がN本の分布として一致 |

- **bit再現を主張できるのは、LLM応答を固定した「録画リプレイ」の場合だけ**(=デバッグ・検死用途。既決の「決定論はタダで拾える所でだけ拾う」と一致)。
- **BATCH_INVARIANT=1 + TP1 + DP7 + 固定ルーティング + 温度0** を全部揃えれば LLM層もbit再現しうる。これは**検証ラン(論文級)専用の構成**として manifest の `mode: holdout` に紐づけるのがよい。温度0.7の本番ランでは**主張しない**。

---

## 問い3. 並行実行の意味論(U9)

### 3.1 ABM実装系の標準(実読)

**NetLogo(docs.netlogo.org/dict/ask.html・実読)**
- 「The specified agent or agentset runs the given commands.」
- **「Because agentset members are always read in a random order, when ask is used with an agentset each agent will take its turn in a random order.」**
- 「Only the agents that are in the agentset at the time the ask begins run the commands.」
- `ask-concurrent`(検索結果): 「this information is included only for backwards compatibility. We don't recommend using the ask-concurrent primitive at all in new models」「Since NetLogo 4.0 (2007), ask is serial」。
→ **教訓: 世界最普及のABM環境は「同期更新の擬似並行」を捨てて「ランダム順の逐次」に振った**。順序バイアスは**ランダム化**で潰すのが標準解。

**Mesa(mesa.readthedocs.io/stable/tutorials/2_agent_activation.html・実読)**
- Sequential: 「Agents act in a fixed order. The simplest pattern, but can introduce systematic bias.」
- Random: 「Agents act in a new random order each step. The most common default.」
- Simultaneous: 「All agents first compute their next state, then all advance at once. This prevents early-acting agents from influencing later ones within the same step.」
- Staged: 「Agents perform multiple actions per step, in a defined sequence of stages.」
- **「the order in which agents act can significantly affect model outcomes」**(Boltzmann wealth模型でGini係数が変わる、と実例つき)
- 推奨: 「Use `shuffle_do` unless your model specifically requires a fixed activation order. Random activation avoids systematic biases where early-acting agents have an inherent advantage.」
- なお Mesa は Time モジュール(旧スケジューラ群)を**廃止**し AgentSet 操作に統合(検索結果)。

**Agents.jl(GitHub docs/src/api.md・実読)**
- スケジューラ一覧: `Schedulers.fastest` / `ByID` / `Randomly` / `Partially` / `ByProperty` / `ByType`。
- インターフェース: **ABMを入力に取りエージェントIDのイテレータを返す関数(様)オブジェクト**。「You can use Function-like objects to make your scheduling possible of arbitrary events」。
→ **v2への直輸入価値が最も高い**: **「スケジューラ=IDのイテレータを返す関数」という抽象**は、v2のtickループにそのまま置ける。**manifestに「どのスケジューラ関数の版か」を1欄で書ける**ようになる。

**MATSim(matsim.org doxygen GlobalConfigGroup・実読)**
- `randomSeed` は `long randomSeed = 4711L`(既定値)としてグローバル設定に存在。
- `numberOfThreads`: 「'global' number of threads. This number is used, e.g., for replanning, but **NOT in QSim**.」
- **空欄(未確認)**: 「乱数を使うが結果は再現可能」という趣旨の記述は**検索結果には出たがdoxygenページ本文では確認できず**。MATSim本(doi:10.5334/baw)の該当章は未読。→ 親の一次確認候補(優先度は低)。
→ **含意**: MATSimは**再計画(replanning)は並列だがmobsim(QSim)は別扱い**という分離をしている。**v2も同型に分けられる**: 「LLM推論=並列でよい」「世界の適用=単一スレッド順序固定」。

### 3.2 スケジューリングは結果を動かす(=規約は mechanism 扱いが必要)

**Weimer et al. 2019「Agent Scheduling in Opinion Dynamics」JASSS 22(4)5・doi:10.18564/jasss.4065(実読)**
- SAS分類(Synchrony, Actor type, Scale)。同期性の定義: 「A model in which all agent updates occur in parallel would be called synchronous. A model in which some or all agent updates occur in series would be called asynchronous.」
- 「Varying synchrony in all cases altered the relationship between the convergence parameter and the variance in opinions observed at convergence.」
- 「Asynchronous schedules ... more likely to generate clusters toward the poles of the opinion spectrum」
- **「No schedule completely eliminated the effect of biased ordering, but ... target actors were most affected by this ordering regardless of synchrony and parameters.」**

**Caron-Lormier et al. 2008「Asynchronous and synchronous updating in individual-based models」Ecological Modelling 212(3-4), 522-527, doi:10.1016/j.ecolmodel.2007.10.049**
→ **空欄(未確認)**: 本文・要旨とも Elsevier 403 で未読。書誌情報のみ検索結果から。**主張には使わない**(親が必要なら一次確認)。

**Scheduler Dependencies in Agent-Based Models: A Case-Study Using a Contagion Model**(Springer, link.springer.com/chapter/10.1007/978-3-030-96188-6_5)
→ **空欄(未確認)**: 未読。存在のみ記録。

→ **答申の規範**: v2において**並行実行の意味論は「便宜的な実装事情」ではなく世界の法則である**。したがって
1. 意味論の全項は **`mechanism|expedient` タグ必須**(方法論の規律)。
2. 「ランダム順」を選ぶなら、それは**公平性という機構の宣言**であって単なる実装都合ではない、と台帳に書く。
3. **同期/非同期の選択そのものを ablation 対象に登録する**(Weimer et al. 2019 が「同期性を変えると結果が変わる」と示した以上、感度試験なしに固定してはいけない)。

### 3.3 同一tick内の競合の解決(席・最後の1個・会話招待)

**先例: FLAME GPU 2(Richmond et al., Software: Practice and Experience 2023, doi:10.1002/spe.3207 / White Rose eprint 199416・PDF実読)**
- 逐次実装の公平性: 「movement of agents to areas which are favourable in terms of resource, is determined through a serial process in which **agent order is randomised for fairness**」
- 並列での衝突: 「Within a parallel implementation of this model conflict naturally occurs as numerous agents compete to try to move to desirable locations.」
- 解法=bidding: 「In parallel, conflict can be resolved through a process of bidding, in which agents simultaneously 'bid' for their desired location with **only the highest priority agent allowed to perform the movement**. **Priorities can be randomly assigned to agents and stored as an agent variable to achieve fairness, as in the serial case.**」
- 3段の取引: 「(1) propose a movement to a new cell location, (2) for a cell location to rank competing agents by the agent's assigned priority and for the cell to communicate a confirmation of its preferred choice of agent, (3) perform movement of the agent whose preference is (confirmed)」+ 反復(sub-model)で「every agent has an opportunity to move」を保証(固定回数だと最悪9回必要)。
- **アトミック演算の警告**: 「The order of the atomic operations is **non deterministic and determined by the GPU's execution model**, as such, if agent priority plays an important role in manipulating the environment then this 'conflict' between agents (in obtaining a resource) is best resolved using the sub-model approach」

**Evaluation of Conflict Resolution Methods for Agent-Based Simulations on the GPU**(SIGSIM-PADS 2018, doi:10.1145/3200921.3200940)
→ **空欄(未確認)**: ACM DL 403 で本文・要旨とも未読。**タイトルとDOIのみ**。比較された手法名・結論は記憶で埋めない。

**DEVSの`select`関数(タイブレークの形式的正典)**
→ **注記: Zeigler本(Theory of Modeling and Simulation)本文は未読**。検索結果の要約では「coupled DEVS は simultaneous events のタイブレークのために select 関数を明示的に持ち、imminent な submodel 集合から**固定の優先規則で1つを選ぶ**」「並列DEVS(Parallel DEVS)はこのselectによるタイブレークの必要をなくす」。
→ **含意**: 「同時刻イベントには**モデル側が宣言した固定規則**でタイブレークする」というのが離散事象系の正典的作法。**乱数でなく規則**。v2は「規則=ハッシュ順」で両立させる(§3.4)。

### 3.4 v2への推奨: 二相(reserve→arbitrate→commit)+ハッシュ優先度

```
tick t:
  Phase A (read-only, 並列可):  全個体が現在状態を読み、意図(intent)を出す
      → LLM由来の意図は「前tickまでに届いた応答」から取る(§4)
  Phase B (arbitrate, 決定論):  資源ごとに intent を集め、優先度キーの昇順で確定
      優先度キー  pk = H(run_salt ‖ tick ‖ resource_id ‖ agent_id)   ← 128bit
      同点は agent_id の昇順(ハッシュ衝突時のみ・確率的に無視できる)
  Phase C (commit, 単一書き手): エンジンの resolve が確定分だけ世界に適用
      落選者には「失敗の意味論」を返す(行動契約書§2.1の失敗欄・§6の直前の結果)
```

**この形が満たすもの**
| 要求 | どう満たすか |
|---|---|
| 公平(id順バイアスの根治=v1 C-8) | 優先度が `agent_id` の単調関数でない(ハッシュで撹拌)。**tickごとに順序が変わる**ので特定個体が常に勝つことがない |
| 決定論 | `run_salt` は manifest の master_seed から導出。同一manifest→同一キー→同一順序。**乱数生成器の状態に依存しない**(ストリーム分離が不要になる) |
| 並列化可能 | Phase A/Bは資源ごとに独立=セグメント化ソート/セグメント化reduceでGPUに乗る。**逐次ループの新設なし**(予算宣言 P4) |
| FLAME GPU 2との整合 | 「優先度をランダム付与して公平性」の思想そのもの。ただし**優先度を状態として持たずハッシュで導出する**分、メモリ0・再現性は上(FLAME GPU 2はagent variableに格納) |
| 反復の必要性 | 「最後の1個」型は1回で決着(勝者1・他は失敗)。**移動/席取りのように「落選者が次善に回れる」場合だけ**FLAME GPU 2のsub-model同様に反復が要る。**v2の推奨: 反復は1回だけ(第2希望まで)、以降は次tickに回す**=P4の逐次ループ新設を避ける |

**競合クラス別の規則(具体)**
| 競合 | 規則 | タグ |
|---|---|---|
| 同じ席(座席・待機スペース) | 二相+pk昇順。落選=「満席」を失敗として返す | mechanism |
| 在庫最後の1個 | 二相+pk昇順。**在庫デクリメントは Phase C の単一書き手のみ**。落選=「在庫切れ」+ 行動契約書の失敗意味論 | mechanism(保存則対象) |
| 同じ相手への会話招待 | 二相+pk昇順で**招待を1件だけ通す**。他は「相手が会話中」。応答判定(較正目標≈0.8)は**招待が通った後**に引く(=乱数消費が競合数に依らない) | mechanism |
| 乗車(定員) | 二相+pk昇順。**定員超過分は次の列車へ繰り越し**(=繰り延べ) | mechanism |
| 資源を消費しない相互作用(注視・傍受) | 競合なし=Phase Aのみ | mechanism |
| 価格改定・計画改訂(権限持ち) | 権限者は原則1人=競合が起きない。起きたら pk 昇順 | mechanism |

**確率/優先度を混ぜるか**: 混ぜない。**「先着=決定論的順序」を pk で実現し、必要な確率性は pk 自体の撹拌に押し込む**のが最小構成。「重要度で優先」を入れると台帳に説明責任が生じ、感度試験が要る=expedientが増える。**【推測】**この「ハッシュを優先度に使う」形の直接の先行文献は本調査では見つけられなかった(FLAME GPU 2は変数に格納・DEVSは固定規則)。**v2独自=expedient として登録し、「一様ランダム優先度」との感度試験を1本用意する**のが正しい扱い。

### 3.5 乱数ストリームの分離(決定論の土台)
**推奨: カウンタベースRNG(Philox/Threefry型)+ 用途別ドメイン分離。**
```
u = PRF( master_seed, domain_id, tick, entity_id, draw_index )   # 状態を持たない
domain_id ∈ {physics, arbitration, conversation_accept, persona_init, jitter, ...}
```
- **利点**: (i)並列順序に依存しない(v1の逐次の罠が原理的に消える) (ii)**エージェント数が変わっても他個体の乱数が変わらない**=ablation比較が壊れない (iii)manifestに書くのは master_seed 1つだけ。
- **manifestに書く**: `master_seed` + `rng_scheme`(例 `philox4x32-10`)+ `domain_table_version`。
- **【推測】**カウンタベースRNGのABMへの適用を明示した査読文献は本調査では確認できず(Random123系の一次文献は未確認=**空欄**)。ただし「シード派生を manifest 1欄に畳む」という manifest 設計上の利点は独立に成立する。

---

## 問い4. 非同期LLM応答の取り込み順

### 4.1 前提の整理
- 世界の書き込み口は **resolve一本**(既決・AI Town同型)。**書き手はエンジン1つ**。
- LLMは**外部オラクル**であって、世界状態を持たない。
- 応答の**到着順は非決定**(艦隊・バッチ・繰り延べ)。

### 4.2 推奨規則(U9の中核)
1. **応答は到着した瞬間には適用しない。** 到着した応答は `pending_apply` バッファに入る。
2. **適用は tick の先頭**(Phase A の直前)に**まとめて**行う。
3. **適用順は決定論的キーの昇順**: `apply_key = (t_apply, event_class, H(run_salt ‖ t_apply ‖ agent_id))`。
   - `t_apply` = 起床時刻 + δ_perc + δ_think(= max(δ_min, α×出力token)。既決DECIDED-10a)を**分tickに切り上げ**た時刻。
   - `event_class` は繰り延べアービタの4クラス(会話ターン > 計画境界 > 個体変化 > セル変化)と同じ順序を使う=**規則を2つ持たない**。
4. **締切超過**(`t_apply` が既に過去):**破棄しない**。繰り延べアービタへ渡し、次tick先頭で最新状態を読み直して適用(状態トリガは最新値で回復・会話ターンは冪等でないため最優先クラス)。既決§6の運用規定①と完全に一致。
5. **未着のまま `t_apply` に到達した場合**: 既決の工学ノート(「応答未着でシミュ時刻がt+δに達する場合は適用イベントが待つ」)の通り**待つ**。ただし**待つのは当該個体だけ**であって世界全体ではない(=個体は「考え中」状態のまま既定行動=待機/継続を行う。行動契約書の「待機は失敗しない」が安全弁)。
6. **manifestに記録**: `apply_order_rule` の版・`pending_apply` の最大滞留・締切超過件数(診断行)。

### 4.3 PDESの知見のうち v2 に要るもの・要らないもの
**Fujimoto 1990「Parallel discrete event simulation」CACM 33(10), 30-53, doi:10.1145/84537.84545**
→ **空欄(未確認)**: ACM DL は 403 で本文未読。書誌情報とDOIのみ。保守的/楽観的の二分法は分野の常識だが、**引用文は出せない**。

**Jefferson 1985「Virtual Time」ACM TOPLAS 7(3), 404-425, doi:10.1145/3916.3988**
→ **空欄(未確認)**: ACM DL 403。要旨未読。Time Warp(lookahead-rollback + antimessage)という枠組みの存在のみ記録。

**HLA / IEEE 1516 の時間管理(TAR/TARA・保守的/楽観的)**
→ **空欄(未確認)**: IEEE標準本文は有料で未読。二次資料のみ検索で見えた。**採用判断の根拠にしない**。

**答申(引用に依らない設計判断)**
| PDESの概念 | v2に要るか | 理由 |
|---|---|---|
| 楽観同期・ロールバック(Time Warp) | **要らない** | 世界の書き手が1つ(resolve)で、LLMは状態を持たない。因果違反が起こる構造がない。ロールバック機構は状態の二重保持=M8予算の敵 |
| 保守的同期(受信して締切まで保留) | **要る**(§4.2がそれ) | 「届いた順に適用しない・確定時刻まで保留する」=保守的同期そのもの |
| lookahead | **要る・既に持っている** | δ_perc + δ_think が「この応答が最も早く効き得る時刻」の下界=lookahead。**これがあるからエンジンは先に進める** |
| LBTS/GVT(全体最小時刻) | **要らない**(単一エンジン) | 論理プロセスが1つなので大域最小時刻の合意が不要 |
| アンチメッセージ | 要らない | 同上 |
| **反変の注意点** | — | 「LLMが遅いほど世界が待つ」ので、**壁時計ペースは艦隊スループットが規定する**(既決の工学ノート)。lookaheadを長く取る(=δ_thinkを長めに見積もる)ほどエンジンは先行できるが、**世界の反応が鈍くなる**というトレードオフ。**δ_thinkの上限はU19で未決**のまま |

### 4.4 デバッグ用「録画リプレイ」(bit再現の唯一の入口)
- ①恒久記録(全LLM入出力・DECIDED-10c)を**そのまま応答テープとして再生**すれば、LLM層の非決定性が消え、**エンジン層は numerical identity で再現する**。
- 必要条件: 応答テープのキーが `(agent_id, t_apply, call_index)` で一意であること = **§4.2の適用キーと同じキーで記録する**。
- manifestに `replay_of: <run_id>` + `tape_hash` を書けば、リプレイランも1級のランとして台帳に載る。
- これが既決「リプレイは決定論が無料で成立した範囲のおまけ」の**実装可能な形**。

---

## 問い5. 時計の整合と同時刻イベントのタイブレーク

### 5.1 三層時計の役割(既決 DECIDED-10a の再掲と接続)
| 時計 | 刻み | 役割 | manifest欄 |
|---|---|---|---|
| 物理 | 連続時間・小刻み(密度LOD) | 位置・運動 | `physics_dt`(忠実度プロファイル内) |
| 認知 | **イベント駆動** | 起床・LLM呼・繰り延べ | `wake_rules_version`, `arbiter_version` |
| 制度 | 時間帯・日次 | 営業時間・ダイヤ・給与 | `institution_calendar_hash` |
| (基準) | **1分tick** | 上記3層の同期点・commit境界 | `tick_seconds: 60` |

### 5.2 同時刻イベントの順序(タイブレーク規則・答申)
DEVSの`select`(=モデル側が宣言した固定規則で1つを選ぶ)の思想を採り、**乱数生成器の呼び出し順に依存しない形**で実装する。

**全順序キー(1本に統一する)**
```
order_key = ( t_sim_ns ,          # ナノ秒精度のシミュ時刻(δ_perc の秒未満を保持)
              class_rank ,        # 4クラス: 会話ターン0 > 計画境界1 > 個体変化2 > セル変化3
              H(run_salt ‖ t_sim_ns ‖ event_type ‖ subject_id) ,  # 撹拌
              subject_id )        # 完全な決定性のための最終手段
```
- **class_rank は繰り延べアービタの固定優先と同一**(§4.2と同じ理由: 規則を2つ持たない)。
- **同一体の複数イベントが同時刻に明けたら「1呼に合流」**(既決§6運用規定②)を、このキーの前に適用する(合流はキー計算より先)。

### 5.3 δ_perc の秒オフセットと 1分tick の関係(**ここが設計上いちばん危ない所**)
- δ_perc = 0.213s × k × m_att、対数正規 σ_ln=0.20(既決)。**値の幅は 0.2〜1.5秒級**。
- 1分tick(60秒)に対して δ_perc は **1/300〜1/40**。つまり **δ_perc は tick 内では常にゼロに丸められる**。
- **選択肢**
  | 案 | 内容 | 評価 |
  |---|---|---|
  | (A) 丸め捨て | δ_perc を tick に丸めると全部0=**δ_percの導入が無意味になる** | **不可**(§8のablation「p_notice/δ」も測れなくなる) |
  | (B) **サブtick順序として使う**(推奨) | δ_perc は**世界時刻を進めない**が、**同一tick内のイベント順序(order_keyの第1要素 t_sim_ns)**を決める。ナノ秒フィールドに `tick_start + δ_perc` を入れる | **推奨**。追加コスト=時刻を int64 ns で持つだけ。「早く気づいた人が先に反応する」という現実の順序が**同一tick内で保存される** |
  | (C) tick を細かくする | 1分→1秒 | 予算破壊(60倍)。**不可** |
  | (D) δ_perc を確率的に次tickへ繰り上げ | δ_perc/60 の確率で1tick遅らせる | 【推測】統計的には等価だが、**同一tick内の順序情報が失われる**(誰が先に気づいたかが消える)。(B)より劣る |
- **(B)を採ると自然に効くもの**: 会話の割り込み(既決「次の移行点での優先権奪取に離散化」)は「δ_percが小さい方が先に移行点を取る」で自然に決まる。同じ在庫の最後の1個も「先に気づいた方が先に予約する」になり、§3.4の pk 撹拌より**現実的な機構**で決まる。
  → **答申の具体案: Phase B の優先度キーを `pk` 単独でなく `(ceil_ns(t_notice), pk)` の辞書式にする**。δ_percが同値のときだけ pk が効く。**これで「先着=決定論的順序」と「知覚遅延の機構」が1つの規則に統合される**。
- **注意(expedient登録)**: δ_perc の分布(σ_ln=0.20)は文献由来だが、**「δ_percが競合の勝敗を決める」という使い方は文献にない**=**expedient**。感度試験: δ_perc を全員同値に潰したランと比較して、競合の勝敗分布・在庫枯渇時刻・会話成立率が動くかを見る。

### 5.4 制度時計との整合
- 制度イベント(開店・発車・給与)は**tick境界にスナップ**する(秒未満の意味がない)。
- 制度イベントと個体イベントが同時刻の場合: **制度が先**(class_rank に `-1` を割り当てる)。理由=「営業時間外で購入」のような矛盾を起こさないため。**mechanism**(世界過程設計書の PlanSpec→ActualLog の向きと一致)。
- 日跨ぎ・時間帯跨ぎは**必ず tick 境界**に置く(=1440 tick/日の整数境界)。

---

## 問い6. 推奨

### (a) run manifest スキーマ(YAML・案)

```yaml
# ---- 同定 ----
schema_version: "1.0"
run_id:            # = 自己ハッシュ(本欄を除く正規化本文の BLAKE3-128・16進32桁)
label: "R5-ablation-01-fixed-slots-vs-single-ranking"
mode: smoke | calibration | holdout | ablation | production   # L3の勘定分離を機械化
created_utc: "2026-09-07T04:12:33Z"
tz: "Asia/Tokyo"

# ---- 事前登録(HARKing防止・封印対象) ----
preregistration:
  hypothesis: "固定枠は単一ランキングより制約違反率を下げない"   # 1文
  metrics: [violation_rate_delta, action_jsd]
  thresholds: {violation_rate_delta_ci_upper: 0.05, action_jsd: "<= null_p95"}
  ablation_id: "AB-01"
  sealed_at: "2026-09-07T04:12:33Z"

# ---- コード ----
code:
  repo: "shibuya-simulation-v2"
  commit: "<40hex>"
  describe: "v2-phase2-rc3"
  dirty: false          # true のランは calibration/holdout に使えない(CIで拒否)
  odd_doc:  {path: "docs/design/v2-odd.md", blake3: "<hex>"}   # ODD 2020 の7要素文書
  contracts:
    perception: {path: "docs/design/v2-perception-contract.md", blake3: "<hex>"}
    action:     {path: "docs/design/v2-action-contract.md",     blake3: "<hex>"}

# ---- 設定 ----
config:
  fidelity_profile: {name: "standard-40man", blake3: "<hex>"}   # 比較ランは同一必須
  normalized_blake3: "<hex>"          # 正規化YAML全体のハッシュ
  tick_seconds: 60
  n_agents: 400000
  sim_days: 1
  start_sim_datetime: "2026-05-14T04:00:00+09:00"

# ---- 乱数 ----
rng:
  master_seed: 20260907
  scheme: "philox4x32-10"             # カウンタベース=並列順序非依存
  domain_table_version: "rngdom-3"    # physics/arbitration/conversation_accept/persona_init/jitter...
  # 個体シード・LLMシードは master_seed から決定論導出(別欄に持たない)

# ---- データ資産(世界の出自) ----
data:
  - {id: osm_shibuya,  version: "2026-04-snapshot", blake3: "<hex>", bytes: 1234567, records: 88123, license_row: "DL-014"}
  - {id: plateau_lod2, version: "2024",             blake3: "<hex>", bytes: ...,      records: ...,   license_row: "DL-003"}
  - {id: persona_pool_v2, version: "v2.1",          blake3: "<hex>", bytes: ...,      records: 400000, license_row: "DL-021"}
  - {id: kddi_flow,    version: "2025Q4",           blake3: "<hex>", bytes: ...,      records: ...,   license_row: "DL-031"}
  - {id: visibility_table, version: "geom-2026-09-03", blake3: "<hex>", bytes: ...,   note: "M10・mmap共有"}

# ---- holdout 封印 ----
holdout:
  seal_scheme: "D/S/P-3layer"
  layers:
    - {name: D, member_hash: "<hex>", sealed_utc: "...", opened: false}
    - {name: S, member_hash: "<hex>", sealed_utc: "...", opened: false}
    - {name: P, member_hash: "<hex>", sealed_utc: "...", opened: false}
  # mode: holdout 以外で opened:true があれば起動を拒否

# ---- LLM 艦隊 ----
llm:
  engine: {name: vllm, version: "0.28.0", torch: "2.x.y", cuda_driver: "595.84", attention_backend: "FLASH_ATTN"}
  env:
    VLLM_BATCH_INVARIANT: "1"
    VLLM_MARLIN_USE_ATOMIC_ADD: "0"      # 既定0。atomicAdd は非決定の既知の穴
    VLLM_ENABLE_V1_MULTIPROCESSING: "1"
  replicas:
    - {tier: T1, model: "Qwen/Qwen3-8B", revision: "<hf commit sha>", quant: "W8A8-INT8",
       weights_blake3: "<hex>", tp: 1, dp: 1, gpus: [0], max_num_seqs: 128, max_model_len: 4096,
       gpu_memory_utilization: 0.90, in_flight_cap: 64}
    # ... ×7
  routing: {rule: "round_robin", cell_affinity: false, version: "route-2"}   # BN-4=不採用
  decoding:
    T1: {temperature: 0.7, top_p: 1.0, top_k: -1, max_tokens: 64, seed: "derived(master_seed, agent_id)"}
    T2: {temperature: 0.7, top_p: 1.0, max_tokens: 512, seed: "derived(master_seed, agent_id, day)"}
  prompt_contract: {version: "R3-8-v1", static_tok: 750, cell_tok: 250, individual_tok: 300}

# ---- 並行実行の意味論(U9) ----
concurrency:
  scheduler: {name: "two_phase_hash_priority", version: "cc-1"}
  phases: [read_intent, arbitrate, commit]
  priority_key: "lexicographic(ceil_ns(t_notice), blake3(run_salt||tick||resource_id||agent_id))"
  tiebreak_key: "(t_sim_ns, class_rank, blake3(...), subject_id)"
  class_rank: {institution: -1, conversation_turn: 0, plan_boundary: 1, individual_change: 2, cell_change: 3}
  llm_apply: {policy: "next_tick_head", order: "apply_key asc", overdue: "defer_to_arbiter", missing: "agent_waits"}
  retry_rounds: 1                    # 落選者の第2希望まで。以降は次tick
  arbiter: {rule: "4class_fixed_priority", promotion_T_max_min: 30, degrade_enabled: true}

# ---- 予算(ラン時点のスナップショット) ----
budget:
  source: {path: "docs/design/v2-budget-declaration.md", commit: "<40hex>", blake3: "<hex>"}
  effective: {W1_hours_per_simday: 24, L4_calls_per_day: 4000000, L6_inflight_per_gpu: 64,
              M8_rss_gb: 24, M11_input_tok: 1300, M11_output_tok: 64, P6_ms_per_tick: 2}

# ---- ハードウェア ----
hardware:
  profile: "borrowed-2026-09"
  gpus: [{model: "RTX A5000", count: 7, vram_gb: 24, driver: "595.84", nvlink: false, pcie: "Gen3 x16"}]
  cpu: {model: "Intel Xeon Gold 6226R", sockets: 2, cores: 32, threads: 64, numa_nodes: 2}
  ram_gb: 251
  os: "Ubuntu 22.04.5 LTS (kernel 5.15)"

# ---- 出力・来歴 ----
outputs:
  journal:    {path: "runs/<run_id>/journal/",     blake3_manifest: "<hex>", retention_days: 365}
  checkpoints:{path: "runs/<run_id>/ckpt/",        every_sim_hours: 6, blake3_manifest: "<hex>"}
  llm_tape:   {path: "runs/<run_id>/llm/",         blake3_manifest: "<hex>"}   # 録画リプレイの原本
  diagnostics:{path: "runs/<run_id>/diag.parquet", blake3: "<hex>",
               columns: [deferred, promoted, degraded, suppressed, residual, net_worth_vs_real_assets]}
  s3_uri: "s3://.../<run_id>/"        # 接続情報は書かない(バケット名も伏せる運用なら省略)

# ---- 系譜 ----
lineage:
  parent_run: null            # resume 元
  replay_of: null             # 録画リプレイなら元 run_id
  tape_hash: null
  ensemble_group: "ENS-2026-09-07-A"     # アンサンブルN本の束ね
  ensemble_index: 3
  ensemble_size: 16
```

**封印対象**(改竄検出): `preregistration` / `holdout` / `config.normalized_blake3` / `data[*].blake3` の4ブロックを1つの署名で固める。**ラン開始後に変えたら run_id が変わる**=事後改変が構造的に不可能。

### (b) 並行意味論の規則集(U9・条文形式)

> **C1. 同期方式**: 1分tickを commit 境界とする**二相同期**(read→arbitrate→commit)。同一tick内でエージェントが互いの当tickの結果を見ることはない(Mesaの simultaneous 相当)。ただし**arbitrate相では資源の競合だけが解決される**(=NetLogo/Mesaの「ランダム順の逐次」が持つ公平性を、順序でなく優先度キーで得る)。 **タグ: mechanism**(Weimer et al. 2019 が「同期性は結果を変える」と示す以上、選択は世界の法則の宣言)
>
> **C2. 競合解決**: 資源ごとに `intent` を集め、優先度キー `pk = ( ceil_ns(t_notice) , BLAKE3(run_salt ‖ tick ‖ resource_id ‖ agent_id) )` の**辞書式昇順**で確定。定員/在庫のある資源は上位から充足、落選者には行動契約書の失敗意味論を返す。**再試行は同一tick内で1回**(第2希望)、以降は次tick。 **タグ: mechanism**(δ_perc部)+**expedient**(ハッシュ撹拌部・感度試験=一様ランダム優先度との比較)
>
> **C3. 書き手の単一性**: 世界状態への書き込みは commit 相のエンジン resolve のみ。arbitrate 相は読み取りと予約表への追記だけを行う。**atomic演算による直接更新を禁止**(FLAME GPU 2の警告「アトミック演算の順序は非決定的」を根拠)。 **タグ: mechanism**
>
> **C4. LLM応答の適用**: 応答は到着順に適用しない。`t_apply = 起床時刻 + δ_perc + δ_think` を分tickに切り上げ、**その tick の先頭**で `apply_key = (t_apply, class_rank, H(run_salt ‖ t_apply ‖ agent_id))` の昇順に適用する。締切超過分は破棄せず繰り延べアービタへ。未着個体は「考え中」のまま既定行動(待機/継続)。 **タグ: mechanism**
>
> **C5. 乱数ストリーム**: カウンタベースRNG `u = PRF(master_seed, domain_id, tick, entity_id, draw_index)`。**用途ごとにdomain_idを分離**し、他用途の消費が影響しないことをテストで保証。逐次的な状態を持つ乱数生成器を新設するには宣言が要る(P4と同格の規律)。 **タグ: mechanism**
>
> **C6. タイブレーク**: 同一シミュ時刻のイベントは `(t_sim_ns, class_rank, H(...), subject_id)` の昇順。`class_rank` は 制度 −1 < 会話ターン 0 < 計画境界 1 < 個体変化 2 < セル変化 3(**繰り延べアービタと同一の順序を再利用**)。同一体の同時刻イベントは**キー計算の前に1呼へ合流**。 **タグ: mechanism**(DEVSのselect=固定規則の作法)
>
> **C7. サブtick時刻**: シミュ時刻は int64 ナノ秒で保持し、δ_perc は世界時刻を進めないが `t_notice` としてサブtick順序を与える。制度イベントは tick 境界にスナップ。 **タグ: mechanism**(δ_percの値)+**expedient**(δ_percを競合の勝敗に使うこと)
>
> **C8. 決定論の範囲**: エンジン層は同一manifestで bit 再現する(numerical identity)。LLM層は分布同値のみ主張する。両者を分ける境界は「resolve の入力」であり、**resolve の入力を録画すればエンジン層は完全に再現する**。 **タグ: mechanism**
>
> **C9. 順序バイアスの監査**: 診断行に「勝率 vs agent_id」「勝率 vs 到着順」の相関を毎シミュ日記録する。**|相関| > 0.05 でゲート失敗**(v1 C-8のid順バイアスの再発検出器)。 **タグ: mechanism**(Weimer et al. 2019「どのスケジュールも順序バイアスを完全には除去しない」への対応)
>
> **C10. 意味論の版**: C1-C9 の実装には `concurrency.scheduler.version` を持たせ、変更したら perf 回帰(P5)と**パターン保存の再確認**を要求する。

### (c) 再現性の主張水準とテスト

| # | テスト名 | 構成 | 合格条件 | ゲート |
|---|---|---|---|---|
| T1 | **manifest自己整合** | 任意 | run_id = 正規化本文のBLAKE3、封印4ブロックの署名一致 | CI・常時 |
| T2 | **エンジンbit再現** | mock LLM(またはテープリプレイ)・CPU・単プロセス・同一manifest×2回 | **全checkpointのハッシュが一致**。不一致なら差分の最初のtickとフィールドを出す | Phase 2完了条件 |
| T3 | **並列不変性** | 同一manifest・スレッド数 1 / 8 / 32 | T2と同じ結果(=二相+ハッシュ優先度が効いている証明) | Phase 2完了条件 |
| T4 | **規模不変性(乱数分離)** | n=5,000 と n=5,001(1体追加) | 既存5,000体の**乱数列が変わらない**(carry-over一致率 1.000) | Phase 2 |
| T5 | **順序バイアス検出** | 実LLM 24step スモーク | C9の相関 |r| ≤ 0.05 | 毎スモーク |
| T6 | **LLM層bit再現(検証ラン構成)** | BATCH_INVARIANT=1・TP1・温度0・固定ルーティング・同一manifest×2 | 全応答が**バイト一致**。一致しなければ「この機・この版では bit 再現は主張しない」と manifest に記録 | R16相当の検証ラン前 |
| T7 | **LLM層分布同値(本番構成)** | 温度0.7・DP7・同一manifest×2 | 行動分布のJSD ≤ 帰無95%点(§8指標Bの装置を流用)・制約違反率の差の95%CI上限 ≤ 0.05 | Phase 4 |
| T8 | **アンサンブル安定性** | 同一manifest・master_seedのみ変えたN本 | 台帳の照合指標のN本分布が、パターン合格基準を**分布として**満たす | Phase 4-5 |
| T9 | **予算・診断行の存在** | 全ラン | 診断行4列(繰り延べ/昇格/縮退/抑止)+保存則2検算が揃う | 全ラン(欠けたら較正・holdoutに使わない) |

**主張の文面(答申・そのまま設計書に置ける形)**
> v2は **bit再現を要求しない**。要求するのは (i) エンジン層の numerical identity(同一manifest・同一機・LLM応答固定)、(ii) LLM層の distributional equivalence(同一manifest・同一機・同一版)、(iii) 結合系の relational alignment。**未来予測の主張はアンサンブルN本の分布に対してのみ行う**。
> **根拠**: Wilensky & Rand 2007 が numerical identity を「確立が難しい」とし distributional equivalence を実務標準として採る(実読)。vLLM公式が「既定では再現性を保証しない」「同一ハードウェア・同一版でのみ再現性を与える」と明記(実読)。

### (d) expedient として登録すべき項(根拠のない部分の明示)
| 項 | なぜexpedientか | 感度試験 |
|---|---|---|
| 優先度キーへのハッシュ撹拌 | 直接の先行文献を見つけられず(FLAME GPU 2は変数格納・DEVSは固定規則) | 一様ランダム優先度・純id順・純ハッシュ順の3条件比較 |
| δ_perc を競合の勝敗に使う(C2の第1キー) | δ_perc の分布は文献由来だが「競合を決める」用法は文献にない | δ_perc を全員同値に潰した対照 |
| 再試行1回(第2希望まで) | 予算由来(P4の逐次ループ回避)。FLAME GPU 2は「動的回数」を推奨=**v2は劣化版** | 再試行 0 / 1 / 3 回で在庫枯渇時刻・移動完了率を比較 |
| class_rank に制度=−1 | 「営業時間外購入を防ぐ」という実装都合 | 制度を0(会話と同格)にした対照 |
| カウンタベースRNGの採用 | 利点は工学的に明らかだがABM適用の査読文献を確認できず(**空欄**) | (試験不要・T3/T4が実質の検証) |
| `retention_days` 型の保持窓 | reana.yaml の先例はあるが v2 の窓長は予算由来 | S1/S2 の実測で改訂 |

---

## 問い7. 親の一次確認リスト(最重要5件)

| # | 主張 | URL | 確認すべき引用文/数値 |
|---|---|---|---|
| 1 | **vLLMは既定で再現性を保証しない。V1のseed既定=0により temperature>0 でも1ラン内は一貫。保証は同一ハード・同一版に限る** | https://docs.vllm.ai/en/latest/usage/reproducibility/ | 「vLLM does not guarantee the reproducibility of the results by default, for the sake of performance.」/「In V1, the `seed` parameter defaults to `0` … so the results will remain consistent for each vLLM run even if `temperature > 0`.」/「vLLM only provides reproducibility when it runs on the same hardware and the same vLLM version.」 |
| 2 | **BATCH_INVARIANTの要求計算能力が公式2ページで食い違う(8.0 vs 9.0)。A5000=8.6** | features: https://docs.vllm.ai/en/latest/features/batch_invariance/ ・env: https://docs.vllm.ai/en/latest/configuration/env_vars/ | features頁「NVIDIA GPUs (compute capability 8.0+)」/ env_vars頁「Requires NVIDIA GPU with compute capability >= 9.0.」 → **どちらが現行か。A5000での「-2%以下」実測が数式上の不変性を伴っているかを T6 で自検証** |
| 3 | **温度0でもサーバー負荷で出力が変わる(実測: Qwen3-235B・1000完了で80種類・最初の102トークンは一致)。決定的化のコストは約2倍(26s→55s)** | https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/ | 「The load determines the batch size that the kernels are run under, and thus changes the eventual result of each individual request!」/「80 unique completions」/「identical for the first 102 tokens」/ 55秒 vs 26秒 → **リポのベンチ「BATCH_INVARIANTのコストは-2%以下」との乖離の説明が要る**(版差か負荷形状差か) |
| 4 | **再現性の主張水準の正典3分類。numerical identity は「確立が難しい」・実務標準は distributional equivalence** | https://www.jasss.org/10/4/2.html (Wilensky & Rand 2007, JASSS 10(4)2) | 「showing that the original and replicated model produce the exact same numerical results」/「the two implemented models are sufficiently statistically similar to each other」/「the results of the two implemented models show qualitatively similar relationships between input and output variables」(いずれも §2.15) |
| 5 | **並列ABMの競合解決の正典形=bidding+ランダム優先度。アトミック演算の順序は非決定** | https://doi.org/10.1002/spe.3207 (FLAME GPU 2, Richmond et al. 2023, Softw Pract Exper) / OA全文 https://eprints.whiterose.ac.uk/id/eprint/199416/ | 「agent order is randomised for fairness」/「only the highest priority agent allowed to perform the movement. Priorities can be randomly assigned to agents … to achieve fairness, as in the serial case.」/「The order of the atomic operations is non deterministic and determined by the GPU's execution model」 |

**補助確認(優先度中)**
- ODD 2020 の7要素と「Incomplete descriptions violate the central requirement of science…」の一文: https://www.jasss.org/23/2/7.html
- Mesa「the order in which agents act can significantly affect model outcomes」: https://mesa.readthedocs.io/stable/tutorials/2_agent_activation.html
- `VLLM_MARLIN_USE_ATOMIC_ADD` 既定0と fp16 atomicAdd への懸念: https://github.com/vllm-project/vllm/pull/14138

---

## 未確認・空欄の一覧(記憶で埋めていない項目)

| 項目 | 状態 | 理由 |
|---|---|---|
| ACM Artifact Review and Badging の定義(Repeatability/Reproducibility/Replicability) | **空欄** | acm.org が HTTP 403 |
| Fujimoto 1990 CACM 33(10) 30-53(doi:10.1145/84537.84545)の本文・要旨 | **空欄** | ACM DL 403。書誌情報のみ |
| Jefferson 1985 TOPLAS 7(3) 404-425(doi:10.1145/3916.3988)の要旨 | **空欄** | ACM DL 403 |
| SIGSIM-PADS 2018 "Evaluation of Conflict Resolution Methods for ABM on the GPU"(doi:10.1145/3200921.3200940) | **空欄** | ACM DL 403。比較手法名・結論は記載しない |
| Caron-Lormier et al. 2008(doi:10.1016/j.ecolmodel.2007.10.049)本文・要旨 | **空欄** | Elsevier 403。書誌情報のみ |
| Paulsen et al. 2018(doi:10.1016/j.procs.2018.04.078)本文・要旨 | **空欄** | Elsevier 403。「最大10%」は検索結果の要約=**未検証** |
| IEEE 1516(HLA)時間管理の条文 | **空欄** | 有料標準。TAR/TARA等の詳細は使用しない |
| MATSim「乱数を使うが結果は再現可能」の一次記述 | **空欄** | doxygen頁に該当記述を確認できず。MATSim本(doi:10.5334/baw)未読 |
| ODD+D 本文(doi:10.1016/j.envsoft.2013.06.003) | **空欄** | 未読。書誌と概要のみ |
| Workflow Run RO-Crate プロファイル本文 | **空欄** | 未読。概要のみ(論文: doi:10.1371/journal.pone.0309210 / arXiv:2312.07852) |
| MLflow公式頁の直接読解 | **空欄** | 検索結果の引用のみ |
| Zeigler本(DEVS `select`)の原文 | **空欄** | 未読。二次的な要約のみ |
| カウンタベースRNG(Random123)のABM適用の査読文献 | **空欄** | 見つけられず。採用理由は工学的推論=**expedient** |
| W8A8-INT8(compressed-tensors)カーネルの決定性 | **空欄** | 公式記述を見つけられず。実測で確認するほかない |

---

## 参照一覧

**実読(引用に使用)**
1. Grimm, V. et al. (2020) "The ODD Protocol for Describing Agent-Based and Other Simulation Models: A Second Update to Improve Clarity, Replication, and Structural Realism." *JASSS* 23(2)7. https://www.jasss.org/23/2/7.html
2. Wilensky, U. & Rand, W. (2007) "Making Models Match: Replicating an Agent-Based Model." *JASSS* 10(4)2. https://www.jasss.org/10/4/2.html
3. Weimer, C., Miller, J.O., Hill, R. & Hodson, D. (2019) "Agent Scheduling in Opinion Dynamics: A Taxonomy and Comparison Using Generalized Models." *JASSS* 22(4)5. doi:10.18564/jasss.4065. https://jasss.soc.surrey.ac.uk/22/4/5.html
4. vLLM 公式 "Reproducibility". https://docs.vllm.ai/en/latest/usage/reproducibility/
5. vLLM 公式 "Batch Invariance". https://docs.vllm.ai/en/latest/features/batch_invariance/
6. vLLM 公式 "Environment Variables". https://docs.vllm.ai/en/latest/configuration/env_vars/
7. Thinking Machines Lab, "Defeating Nondeterminism in LLM Inference". https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/
8. vLLM PR #14138 "[Kernel] optimize performance of gptq marlin kernel when n is small". https://github.com/vllm-project/vllm/pull/14138
9. NetLogo Dictionary: `ask`. https://docs.netlogo.org/dict/ask.html
10. Mesa Tutorial "Agent Activation". https://mesa.readthedocs.io/stable/tutorials/2_agent_activation.html
11. Agents.jl API(Schedulers). https://github.com/JuliaDynamics/Agents.jl/blob/main/docs/src/api.md
12. REANA "reana.yaml" reference. https://docs.reana.io/reference/reana-yaml/
13. Richmond, P. et al. (2023) "FLAME GPU 2: A framework for flexible and performant agent based simulation on GPUs." *Software: Practice and Experience*. doi:10.1002/spe.3207 / OA全文 https://eprints.whiterose.ac.uk/id/eprint/199416/
14. MATSim doxygen: `GlobalConfigGroup`. https://www.matsim.org/doxygen/classorg_1_1matsim_1_1core_1_1config_1_1groups_1_1_global_config_group.html

**書誌のみ(未読・主張の根拠に使っていない)**
15. Müller, B. et al. (2013) "Describing human decisions in agent-based models – ODD+D." *Environmental Modelling & Software* 48, 37-48. doi:10.1016/j.envsoft.2013.06.003
16. Fujimoto, R.M. (1990) "Parallel discrete event simulation." *CACM* 33(10), 30-53. doi:10.1145/84537.84545
17. Jefferson, D.R. (1985) "Virtual Time." *ACM TOPLAS* 7(3), 404-425. doi:10.1145/3916.3988
18. (著者未確認) (2018) "Evaluation of Conflict Resolution Methods for Agent-Based Simulations on the GPU." *SIGSIM-PADS 2018*. doi:10.1145/3200921.3200940
19. Caron-Lormier, G. et al. (2008) "Asynchronous and synchronous updating in individual-based models." *Ecological Modelling* 212(3-4), 522-527. doi:10.1016/j.ecolmodel.2007.10.049
20. Paulsen, M., Rasmussen, T.K. & Nielsen, O.A. (2018) "Output variability caused by random seeds in a multi-agent transport simulation model." *Procedia Computer Science* 130, 850-857. doi:10.1016/j.procs.2018.04.078
21. Leo, S. et al. (2024) "Recording provenance of workflow runs with RO-Crate." *PLOS ONE*. doi:10.1371/journal.pone.0309210 / arXiv:2312.07852
22. Horni, A., Nagel, K. & Axhausen, K.W. (eds., 2016) *The Multi-Agent Transport Simulation MATSim*. Ubiquity Press. doi:10.5334/baw
23. MLflow Tracking 公式ドキュメント. https://mlflow.org/docs/latest/ml/tracking/
24. Workflow Run RO-Crate プロファイル. https://www.researchobject.org/workflow-run-crate/

**リポ内(読み取りのみ)**
- `docs/design/v2-methodology.md` / `v2-budget-declaration.md` / `v2-perception-contract.md` §5-§6 / `v2-action-contract.md` / `v2-boundary-economy-design.md` §2.3 / `v2-redesign.md`(§3 決定論ポリシー・§4 並列モデル・DECIDED-10a 三層時計・DECIDED-10c 観測3階建て・OPEN-10e)/ `docs/bench/README.md` / `CLAUDE.md`
