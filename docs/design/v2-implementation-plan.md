# v2実装計画書(v1: 言語・部品・コンポーネント・プロセス・データ層・テスト/CI)

> **状態: v1・決定(仮・2026-09-07・ユーザー「Aで行こう・1〜7も採用」)。全項は仮=変更可。構築は「全て決めてから」の方針下で、残ラウンド(世界過程拡張・ペルソナ動態・U8/U9・世界データ仕様)の決定後に開始。**
> 根拠: [v2-implementation-stack-research.md](../research/v2-implementation-stack-research.md)(親一次確認済み: NVIDIA numba-cuda保守モード宣言・AMBER 1118×・FLAME GPU 2 bidding/1M体0.003s・vLLM sha256_cbor/cache_salt・httpx既定20)+[docs/bench/engine_spike/README.md](../bench/engine_spike/README.md)(エンジン実測: 1tick処理≈1.6分/シミュ日・群衆物理dt0.5でCPU1.3h/GPU換算6分)+LLM側実測14.8h/日(第5段)。

## §1 言語・ランタイム(決定A)
- **Python 3.12 + NumPy/Numba(CPU) + NVIDIA Warp(GPU第一・同一カーネルをCPU/CUDAへJIT・Apache-2.0)・CuPy(GPU第二)**。`numba.cuda`は採らない(NVIDIA公式: 保守モード)。
- 律速はLLM(14.8h/日・極限試算0.5-1.5h)であり、エンジン(1-10分/日・群衆物理込みで+0.1-1.3h)の言語速度は総時間を動かさない。v1の遅さは逐次ループとRAM膨張(データ配置)であって言語ではない(AMBER: 列指向Pythonは Agents.jl 同等域)。
- **移行条件(事前宣言)**: 次のいずれかがPhase 2/3の実測で起きた**関数のみ**Rust(PyO3)またはC++へ: ①numbaベクトル化後もP2(≤5ms@5千体)/P3(≥10万イベント/秒)を2倍以上超過 ②P6(変化検出≤2ms/tick)不達 ③GIL干渉が実測されプロセス分離でも解けない。移行時はNumPy参照実装を残し数値一致テストをCIに置く。
- 重い連続物理(群衆・車両追従)はどの言語でもGPUカーネル(Warp)に書く=言語選択と独立。
- **v2の「アーキテクチャからの刷新」**は言語ではなく、配列指向(SoA)・単一書き込み口(engine.resolve)・二相コミット・予算とテストによる強制、で実現する。

## §2 部品表
| 用途 | 部品 | 版方針 | ライセンス | 備考 |
|---|---|---|---|---|
| 配列 | NumPy(≥2.1) | 下限固定 | BSD-3 | Philox同梱 |
| CPU JIT | Numba(0.61系以降) | 固定 | BSD-2 | CUDAターゲット不使用 |
| GPU | warp-lang(第一)/cupy-cuda12x(第二) | 固定 | Apache-2.0/MIT | RTX 5070(sm_120)のwheel対応は**未確認**(ローカル機での可否) |
| 暗号ハッシュ | blake3 | 固定 | 要確認 | manifest・資産・封印・優先度キー |
| 高速ハッシュ | xxhash | 固定 | 要確認 | 変化検出・prefixキー・ルーティング |
| HTTP非同期 | httpx | 固定 | BSD-3 | レプリカごとにAsyncClient+Limits(64,64,None)+Semaphore(64) |
| LLMサーバ | vLLM 0.28.0 | **完全固定** | Apache-2.0 | 検証ラン=`--prefix-caching-hash-algo sha256_cbor`・モード別`cache_salt` |
| 埋め込み | sentence-transformers+onnxruntime(CPU) | 固定 | Apache-2.0 | Ruri-v3-30m・`intra_op_num_threads`明示+コア割当 |
| 列指向I/O | pyarrow | 固定 | Apache-2.0 | Parquet |
| 集計 | duckdb | 固定 | MIT | 診断・センサス・検算SQL(ファイル直読) |
| 圧縮 | zstandard | 固定 | BSD | テープ・checkpoint |
| テスト | pytest/pytest-benchmark/hypothesis | 固定 | MIT | §6 |
| 性能履歴 | asv | 固定 | BSD-3 | セルフホスト機のみ |
| 構造保全 | import-linter | 固定 | BSD-2 | §3の層契約 |
| 設定 | pydantic(またはdataclass+自作検証) | 固定 | MIT | manifest正規化 |
| RNG | numpy.random.Philox | NumPyに従う | BSD-3 | カウンタベース(鍵=ドメイン・カウンタ=tick/個体/抽選番号)。manifest欄は`numpy-philox4x64` |

## §3 コンポーネントと依存規則(上→下のimportのみ・循環禁止=import-linterでCI強制)
```
manifest(誰にも依存しない・全員が読む)
build(オフライン・成果物=不変資産・実行時にimportされない)
core: SoAレジストリ・dtype/バイト予算宣言・Philox・ハッシュ・時刻/ID型(何にも依存しない)
world: セル/POI/グラフ/可視性(mmap)/騒音場      agents: 状態SoA/T0習慣/記憶/関係
perception: レンダラ/ハッシュ三役/注意ゲート/p_notice → 出力=Observation DTO(bytes+メタ)
llm: 艦隊クライアント/パーサ/テープ(world/agentsをimportしない=mock LLMが成立)
engine: 時計/スケジューラ/繰り延べアービタ/resolve/二相コミット=**世界状態への唯一の書き込み口**
economy: 台帳/transfer/検算/センサス(engineのtransfer単一API経由のみ)   census/diag: 読み取り専用
```
- SoA: 1フィールド=1本のNumPy配列+dtypeレジストリ(M9)。個体オブジェクトを作らない。セル(100m・453)を第一のチャンク。
- スケジューラ: 1分tickのバケット配列+tick内は秒オフセット(δ_perc)でnp.argsort整列。heapqは遠未来予約のみ。`scheduler(state)->ndarray[int64]`の純関数。
- 二相コミット: reserve→arbitrate→commit(FLAME GPU 2のpropose→rank→moveと1対1=mechanism)。優先度キー=(気づいた時刻, blake3(salt‖tick‖資源ID‖個体ID))。未解決者数を診断行へ。
- 変化検出: セルB2/B4のバイト列をxxhashで453回(宣言済みの小ループ)、個体B5は配列比較。
- 録画テープ: 1呼=1行Parquet(zstd)、共有ブロックはblock_idでintern。リプレイは完全一致・テープ外は失敗。

## §4 プロセス/スレッド構成
- Proc A engine(単一プロセス・asyncio×1・計算はnumba nogil/Warp)。理由: M8(RSS≤24GB)・GILは逐次禁止下で問題化しない・決定論の証明が単純。
- Proc B×7 vLLM OpenAIサーバ(外部起動・ランより長生き)。Proc C 埋め込みworker(CPU・スレッド数明示)。Proc D writer(Parquet/journal/checkpoint・SPSCキュー)。Proc E 計器盤(読むだけ)。
- 実測項目(Phase 2): httpxイベントループとnumba計算の干渉。出たらLLMクライアントを別プロセスへ(条件宣言済み)。

## §5 データ層
- 世界データ台帳=Parquet(不変・ハッシュ)→実行時NumPy。可視性=生バイナリ+numpy.memmap(ラン間共有)。LLMテープ・診断行・transfer=Parquet(zstd・日次)。センサス=Parquet+CSV。checkpoint=.npz+zstd(M7≤2.0xを機械検査)。集計=DuckDB直読。
- 40万体×1日: テープ1.2-1.6GB(圧縮後)+診断/取引/行動ログ数百MB=1.5-2.0GB(S1≤5GB内)。**個体×tickの全記録は禁止**(セル別集計へ)。
- **要決定(Phase 2)**: checkpointがS2(≤17GB/日)と6時間毎×膨張率≤2.0xで緊張(生24GB/日)→圧縮前提/増分/頻度。

## §6 テスト・CI・性能ゲート
- 層: 単体(pytest)/性質(hypothesis: 保存則・正規化9項のバイト一致・RNGドメイン分離)/バイト一致golden(同セル2体でB0-B4差分ゼロ・改版は宣言)/状態成長宣言(5欄・24step→30日外挿でM行超は失敗)/直列化(M7)/録画リプレイ回帰(状態ハッシュ一致)/契約テスト(12語+種別固有・2行形・未定義行動5段)/実LLMは24stepスモークまで。
- CI(GitHub Actions・GPUなし)=上記ほぼ全て+5,000体縮小ラン。GPU必須(`@pytest.mark.gpu`・セルフホスト)=P1・GPU/CPU数値一致・vLLM実接続とBATCH_INVARIANT自検証(A5000=CC8.6の境界問題)・40万体RSS。正典化前に手動gpuテストの記録をmanifestへ。
- P5(+10%で失敗)は共有ランナーでは**相対ゲート**(同一ジョブでbaseline/candidate交互測定・比1.10)、絶対値(W2/P2/P3/P6)はセルフホストのasvのみ。P4(逐次ループ宣言)はAST検査を試行(expedient)。

## §7 U8/U9追補(艦隊接続)
- 検証ラン=`--prefix-caching-hash-algo sha256_cbor`+実行モード(smoke/calibration/holdout/ablation/production)別`cache_salt`をmanifestに記録。
- 順序制御: ブロック順序固定・同一(セル,時間帯)の呼を同一時刻にまとめて発射(同一GPUに寄せない=BN-4)・レプリカ配分=xxhash(call_id) mod 7(不均衡時はleast-in-flight)。
- 失敗の意味論: 接続エラー=同一レプリカ1回→別レプリカ1回/タイムアウト(TTFT 60s・e2e 300s=expedient)=**繰り延べ**(破棄禁止・憲法1)/書式エラー=温度0で1回再生成→未定義行動5段/キュー満杯=非ブロッキングで「入らなかった」を返しアービタが繰り延べ。全て診断行に計数。

## §8 expedient登録簿(本書分)
engine単一プロセス(GIL干渉未実測)/P6のxxhash×453で≤2ms(未実測)/CI相対ゲート比1.10/P4のAST機械化/LLMタイムアウト既定/ルーティングmod 7/経済transfer 20取引/体/日の見積り/checkpoint増分案/Warp第一(大規模ABMの公開事例未確認)/sm_120対応未確認/Ruriスループット未計測。

**C0(骨格・2026-09-08)で導入した自前規約(追記のみ・決定項は変更していない)**:
- `core.rng` 鍵導出=blake3(UTF-8 `"i:<seed>"`または`"s:<run_id>"` ‖ 0x1F ‖ domain) の16バイト→Philox4x64鍵(k0,k1)・カウンタ=最大4語(個体ID/tick/抽選番号)。ドメイン表は manifest.rng.domain_table_version で版管理(本モジュールは表を持たない)。
- `manifest.canonical`: run_id は正規化本文から **キーごと除去**して blake3(with_run_id は冪等)・辞書キーは再帰ソート・**リスト順序は保持**(replicas/phases/data_assets/diagnostics.columns の順序は本文の一部)・datetime 欄は datetime 型(YAMLの暗黙時刻と引用文字列を同一正規形へ)。
- `manifest.schema`: 診断列名 `DIAG_COLUMNS=("deferred","promoted","degraded","suppressed")`・保存則検算名 `CONSERVATION_CHECKS=("conservation_transfer_residual","conservation_stock_residual")`(命名は未リサーチ・C4で確定)・規則(d)のIPv4判定は4成分の版番号も弾く安全側・`output.s3_uri` 欄は持たない(extra=forbid)・`decoding.T1/T2` の下位欄=(temperature, top_p, max_tokens, seed)。
- `core.budget`: 予算表の行ID正規表現は `^[WPMLSI]\d+$`(I1 初期化予算を含む=34行・W/P/M/L/S の33行は別テストで固定)・`parse_limit` は比較子(≤≥<>)付きの太字を優先する best-effort(L4/L6/S3/S4/I1 は None)。
- 世界カタログ分母: 凍結規則=「見出し行 `| # | 型 |` から最初の空行までを UTF-8 で SHA-256 し先頭16桁」(第92の凍結スクリプトから復元・34f9fa9d316587be を再現)・成果物は `src/shibuya/manifest/frozen/world_catalog_v0_2.json`(ディレクトリ名 `frozen/` は .gitignore の `data/` と衝突しないための命名)。
- pre-commit 秘密スキャン=`.githooks/pre-commit`+`git config core.hooksPath .githooks`(ローカル設定・pre-commit フレームワーク不使用)。CI は ubuntu の GPU なし段のみ(自己ホスト段は C2 以降)。
- (層2レビュー指摘で追記・09-08) 正規化本文の符号化=`json.dumps(sort_keys=True, ensure_ascii=False, separators=(",",":"))` の UTF-8(run_id の値を決める規約)・`normalized_yaml` は `width=4096`・`Identity.run_id` は押印前 None 許容・規則(d)は IPv4 に加え `http` 始まり文字列(大小無視)も拒否・規則(c)に `VLLM_MARLIN_USE_ATOMIC_ADD=0` を追加・`Concurrency.phases` は `(read_intent, arbitrate, commit)` 固定。`core.budget`: 環境変数 `SHIBUYA_BUDGET_MD` で表の場所を上書き可・`## 6.` 以降は読まない・見出しセルは固定タプル。凍結 JSON の書式(indent=1・ensure_ascii=False・末尾 LF・追加キー source/rule)は byte 一致テストの対象=書式自体が凍結。pyproject: `filterwarnings=error::DeprecationWarning:shibuya.*`・`addopts="-q -p no:cacheprovider"`。改行コードは `.gitattributes`(`* text=auto eol=lf`)で LF 固定(凍結 SHA が LF バイト列に依存するため)。


**C2 第1弾(core/engine・2026-09-08)で導入した自前規約(追記のみ)**:
- `core.types`: ID幅 int32・`INVALID_*`=−1番兵・t_sim_ns は int64(60秒tickで|tick|≤153,722,867)・EventClass=class_rank(制度−1/会話0/計画境界1/個体2/セル3)。**RNGカウンタとして使うときは class_rank+1**(core.rng は非負のみ)。
- `core.hashing`: priority_key/apply_key/wake_key のバイト配置=`run_salt ‖ 3バイト用途タグ(pk/ak/wk) ‖ int64-LE 欄`・既知解固定・配列版は要素ごとの blake3 逐次ループ(≈2.0M件/s・P4宣言)。`sha256_cbor` は vLLM と算法名を揃えただけでバイト一致は主張しない。
- `core.soa`: 個体バイト上限=予算行 M1(≤30KB/体=30,000 B・KBは10進)・セルの上限行なし(None)・属性アクセスは自前規約(正典は `reg.arrays`)。
- `core.growth`: 正典=D-R2-6 の5欄(per_agent_bytes/per_cell_bytes/per_day_growth/retention/worst_case_ops_per_tick)。外挿は線形(24step→1日/30日)・retention があるとき実効期間=min(地平, retention)。
- `core.serialize`: 形式=zstd(非圧縮 npz)+`__meta__` JSON・level 3。**M7 の分母=非圧縮直列化長**(RAM/ファイル比も併記)。
- `engine.scheduler`: 地平 HORIZON_TICKS=1,440(設計書はHを与えない)・整列鍵から挿入順 seq を除外(T3)・取り消しは tombstone+全走査 O(地平)。DeferralQueue は入れる/数える/出すのみ(裁定規則は第2弾)。
- `engine.tape`: ディレクトリ2ファイル(行+共有ブロック)・block_id=blake3先頭16B・テープ外は `TapeMiss` 例外(黙って実LLMへ落とさない)。
- `llm`: `LLMClient`/`TapeLookup` Protocol(依存性逆転で engine.tape を import しない)・prompt_hash/params_hash=sha256_cbor・トークン見積り=文字数÷2・**12語定数の置き場所は当面 llm(C3 で行動パーサ側に一本化)**・MockLLM の語句表と一様抽選は意図的に無根拠(mockを暗黙のモデルにしない)。

**C2 第2弾(agents/world/engine 二相コミット・アービタ・resolve・変化検出・mock 1日・2026-09-08)で導入した自前規約(追記のみ)**:
- 合成小世界(CI 用)=1セル1ノードの4近傍格子・1 tick=1ノード(100 m/分)。実資産では1 tick=1ノードは歩行より遅い(ノード間隔<100 m)=実速度は U15(群衆物理)で置換。ノード→セルは格子式 floor(x/100)(W1 に place_id 欄なし)。
- 合成 POI(1セル2件・3カテゴリ・300/800/1,500円・在庫32-96・受入4件/tick)・営業時間一律10-22時(W7 未結線)・noise_stage 0(W10 未結線)。B4 欄=密度段・騒音段・営業中POI数の3つ(構造物・顕著行為は C3)。
- 内受容: 段の刻み(4/7/9)・ヒステリシス幅1・自然変動(30 tick ごと+1/休憩−3/購入−4/睡眠−2)=C4 の世界過程までの駆動源。
- アービタ: T_MAX(会話3/計画境界10/個体30/セル60 tick)・昇格=待ち時間からの純関数(累積・starvation-free)・DEGRADE_COST_FACTOR 0.5・δ_perc は予期クラス別の定数(σ_ln 0.20 と m_att は C3)・δ_think=0→t_apply=tick+1(認知設計書 L1)。**`DeferralQueue.promote()`(list.index の逐次)は設計規模で使えず未使用**=昇格は待ち時間の純関数で再定義。診断計数の読み: deferred=新規繰り延べ件数・promoted=昇格事象数。
- 資源ID名前空間=POI→会話相手→就寝スロット(容量200/セル)の連番。会話相手=同一セルの起床者の最小id(招待の資源競合を起こすため)。「対象」はエンジンが文脈から導く(対象パーサは C3)。
- 書き込みガード `freeze()/thaw()/writable()` を agents/state.py と world/state.py に二重配置(world|agents は相互 import 禁止)・静的検査は AST(`writable` 呼び出しが engine/resolve.py 以外に無い)。
- 変化検出 P6: 変化セル→在席個体の圧縮に numba カーネル1本(NumPy 参照実装と byte 一致テスト)。ベンチは 453 セル(予算行 P6 の「139セル」より厳しい側)。
- 成長宣言の cap(16/16/32/64 MB・5 GB)は S1/M8 から親が按分した見積り(予算表に個別行なし)。テープ 400 B/呼(実装計画書の上端)。mock 日課=1日5境界・平日/休日2パターン。
- **C2 未実装(C3/C4 へ)**: 会話の継続・終了(max_turns)・記憶転写・関係辺/通報・断るは記録のみ/手伝いは BAD_TARGET/B5 は内受容のみ(知人・近接・被注視・傍受は C3)/相手別不応期(同一相手60分・同一話者30分=関係辺依存)/録画テープの実書き出し(見積りのみ)/Phase B 第2ラウンドは空回り(第2希望なし)/40万体フルランは未実測(4万体 18.2 s・arbiter 支配)。
- (層2レビュー指摘で追記・09-08) 密度段の境界 `DENSITY_STAGE_EDGES=(1,5,20,60,150,400,1000)`(人/セル・expedient)・初期内受容 hunger 2/fatigue 2/thermal 5・行バイト見積り pending_apply 128/arbiter 32/intent 32/diag 128 B・起床条件→予期クラス写像 `_CONDITION_EXPECTATION`(commit.py)・**縮退の適用範囲=予算超過 tick では下位2クラスの選抜全件を縮退**(予算内に収まる分も)・クラス内順序=待ち tick 降順(許容遅延比ではない)・LLM へ渡す wake_class=昇格後の実効クラス(テープ鍵の第3要素も実効クラス=C3 で確定)・`one_per_agent` の優先=LLM由来>エンジン継続・checkpoint_every=360・`DIAG_RUN_COLUMNS` 運用列・AgentKind 5値・ResultCode 追加(LOST_ARBITRATION/UNDEFINED_ACTION/BAD_TARGET)・n_conflicts=初回裁定の落選数(再試行で二重計上しない・修正済み)・書き込みガードは構築直後は非凍結で run.py が freeze する規律(AST 検査は writable と thaw の呼び出し元を固定)。

**C3 契約側(llm/contract・parser・undefined・engine/conversation・llm_bridge・2026-09-08)で導入した自前規約(追記のみ)**:
- `llm.contract`=行動語彙の唯一の正典(12語+種別固有12語=24語・§2.2 の 指示/並ぶ/撮影を含む・発車/停車 と 並ぶ/撮影 は1行2語を分割)。種別固有語の target_kind は推定(§2.2 に対象列なし・`target_declared=False`)・前提条件IDは自前識別子(日本語逐語は `precondition_text`)・対象の表層形(C-0117 / g<ix>_<iy>_<GL|UG|DECK> / P-204 / 整数 / …駅)。
- `llm.parser`: ラベル別名表・行動ラベル完全欠落時のみ自由文フォールバック・`<think>` 除去・値は次ラベルか改行まで・`format_ok`(書式)と `action`(語彙一致)を別指標。
- `llm.undefined`: 同義語表 v0(版付き)・最長部分文字列フォールバック・N=10・ログ上限 4,096・段3 キーワード(保存則/在庫/所持金/性能/予算/売上/faucet/sink)・裁定プロンプト文面。
- `engine.conversation`: d_talk≈1 m は同一セルで代替(セル内座標なし)・受諾 0.8・招待者先行の交互発話・話題数=max_turns・沈黙 5 tick・セッション TTL 60 tick・拒否記憶 60 tick(無順序対)・定型の相槌/締め文・招待の RNG カウンタ=(tick, inviter)(§2.5 順・親修正)・resolve が招待側のみ CONVERSING にするため被招待側の離脱はセルで検出(C4 で両側更新)。
- `engine.llm_bridge`: StubRenderer(prompt_hash=agent/cell/tick//5/wake_class)・call_id="<tick>:<agent>:<class>"・δ_think=ceil(レーン秒/60)=L0 0/L1 1/L2 2/L3 5 tick(認知設計書 §1)・種別固有語は当面 待機 に写像+計数・TapeMiss→空応答→未定義→待機(実LLMへ落とさない)。
- `engine.run`: 診断の日次行 8(deferred/promoted/degraded/suppressed/parse_errors/undefined_actions/tape_misses/conversations_opened・率は RunResult 属性)・会話招待は resolve の 会話 成功を入口とし `partner_idle=True` を前提(resolve が適用時に検査済み)。
- 手伝いの失敗「能力不足」= `ResultCode.INSUFFICIENT_ABILITY`(親追加)。

**C3 知覚側(perception templates/normalize/channels/p_notice/attention/hashes/state/renderer・2026-09-08)で導入した自前規約(追記のみ)**:
- テンプレ v1=品質プローブ v0 の文面を 2 行形と v2 ID 形式へ適応(template_sha256=161fe181bc325f00…固定)。B1 から 年代・性別 を外す(個体依存語=規約⑧・C5 で B5 自己状態へ)。LOS 文面は v0 流用(境界のみ Fruin)。空要素の定型句・[B6 問い]・対象欄の説明文は自前。
- **規約⑧の読み**=「B0-B4 に個体を同定する語を入れない」・バイト一致検査は (セル, 5分帯, 種別) 単位(B1=種別ブロックのため種別が違えば B1 は異なる=文面どおりの⑧は構造的に不成立)。
- B0 は v0 文面(条例適用規則を含む)で 603 tok=行予算 300 の 2 倍・共有静的の群予算 644/750 内(実効ゲートは群予算 750/250/300=BN-5 の実測単位)=PENDING(ユーザー判断)。§3.2 のチャネル上限は**内容**に適用し、ラベル+素性タグの固定オーバーヘッド(≈24 tok)はブロック総量側で数える。
- normalize: 略語ブラックリスト・個体依存語の正規表現・5 分丸めは floor・規約⑥は列挙行にのみ適用。channels: トークン=chars//2・切り詰めは行単位で末尾から・単一ランキング腕は呼び出し側の順序を受けるスタブ(ablation ①)。
- p_notice: 一発ベルヌーイを段1・段2の独立 2 抽選で実装(合成確率は同値・N は段1後に依存)・社会項の近傍数は 4e6 対を超えると 3×3 バケット近似(計数)・向きは 16 セクタ量子化(E2=6.22° より粗い=保守側)。attention: 中小媒体 p_see=0.27(0.14-0.40 の中点)・顕著性の重み 1.0/1.0/0.5/0.5・床 0.05・命令文除去の正規表現(文単位・保守的・除去件数を報告)・既定注視 0.48 s(Fotios 中央値)。
- hashes: prefix_key のバイト配置(tag‖block ids‖u64 LE→xxh64)・b4_field_row の 4 欄(LOS 6 段/騒音段/流れ/顕著行為ダイジェスト)=**エンジンの変化検出(density 8 段/人・セル)との不一致で描画バイト変化の約 48% を取りこぼす→C3 結線で engine.change_detect を知覚側の行に切替**。
- state(M12): 向き 1 B+課題 1 B+再送ハッシュ 8+8 B=18 B/体(自前上限 24 B/体・予算表に知覚行なし)。renderer: 密度の分母=歩行可能面積(実資産=W10 街路点×6.25 m²・合成=セル面積×0.15)・k=3/2/1 は LOS A-B/C-D/E-F・B4b は定型空文・流れ 0・W13 欠日はその時刻の最頻値・看板=最も可視な POI の営業時間・[B2 路面]は層と街路点の有無のみ。内受容閾値 (4,7,9)・騒音段語彙・行動語彙は層契約のため複製(等価テストで保護)。

**C4 経済側(economy accounts/ledger/goods/checks/census/pricing/anchors・engine/ledger_api・2026-09-08)で導入した自前規約(追記のみ)**:
- 依存性逆転: engine は `engine.ledger_api` の Protocol(MoneyLedger/GoodsLedger/LedgerBundle)だけを知り、economy が実装(engine→economy の import なし・AST 検査)。世帯現金=`agents.money` を参照で採用(写しなし)・`world.pois.stock` は SKU 別棚の写し(resolve のみが書く)。台帳結線は状態ハッシュ中立(結線前後で同 seed 同ハッシュ)。
- accounts: 減価償却=自己ループ transfer(payer==payee・現金不動・固定資産と純資産が減る)/退蔵項=enum に置くが transfer 不能の測度(checks.hoard_report)/**逸脱比例コスト=15 番目の科目(店舗→政府・sink)**/外界・銀行・政府は負残高可(faucet の相手勘定)/税は第1陣「税 sink のみ」。**初期財布は外界から `CARRY_IN`(来街者持込)で注入=住民には誤ラベル→PENDING(初期保有の科目)**。
- ledger: 同一支払者の重複行は前置和で判定・生ログ 24 B×262,144 行(**→ D-53(2026-09-10)で N 比例 = `max(16,384, 3.0×N×保持日数)` 行へ**・本節末の D-53 項)・保持窓 1 日→日次集約(D-R2-6)・貨幣供給量 M=世帯+店舗+雇用主の現金+預金・成長宣言係数 3 transfer/体/日・cap(6.29/16/512 MB)は親按分=要 delta。検算①=行和 0・**列和=Δ現金**(Caiani の Δ行を陽に持たない形)+Δ預金−Δ借入=0。
- goods: SKU=カテゴリあたり 1-3 品目(質量 g・廃棄率)・払い出しは最初の非空スロット・在庫評価=標準原価(価格÷k)・初期在庫は均等割・棚卸差異閾値=流量の 1%・棚の退蔵=14 日・廃棄 band ±30%・カテゴリ→k(コンビニ 5.0/飲食 3.3/物販 2.9)・世帯は SKU 別合計のみ(M1 非搭載)。内部移動の科目 SALE/TO_BIN/STOCKTAKE を追加(§7.1 は faucet/sink のみ列挙)。
- pricing: 種別→k・β=0.5(E7 アンカー未取得)・月次 Calvo→日次 1−(1−p)^(1/30.44)・clearing=min。anchors: 種別→日消費・財布=対数正規(中央値=日消費×3 日・σ0.6・1,000〜2,000,000 円)・来街者 7.1 万円÷5・月次賃金=時間×最低賃金×割増 1.0。checks: 残差閾値=M×1e-6・退蔵=30 日不動。census: 日次行に検算②成否・廃棄質量を追加(設計より広い)・Parquet zstd。
- **書き込みガードの穴**: numpy の `np.add.at` は writeable=False を無視(numpy 2.5.3 実証)→台帳は明示フラグで防御・engine 側は C3 結線で静的検査(add.at の第1引数が world./agents. なら resolve.py のみ)を追加。

**C3 結線(レンダラ→bridge・直前行動・W10 騒音段・変化検出の切替・書き込みガード・2026-09-08)で導入した自前規約(追記のみ)**:
- **prompt_hash は 2 種で役割が違う**: テープの完全一致鍵=`LLMRequest.prompt_hash`=sha256_cbor(プロンプト本文)(vLLM と算法名を揃える)/prefix キー=`Rendered.prompt_hash`=blake3(ブロック連結)(BridgeResult.prompt_hash)。両方を記録し役割で使い分ける(統一しない)。
- `last_action`(int8・+1 B/体)は resolve のみが書く(12 語と落選時・ENGINE_STEP は書かない=移動の継続)。`last_result` はレンダラが SoA から読む(bridge は渡さない=「未実行」分岐を壊さないため)。
- W10 騒音段=街路点の**最頻値**でセル集約(perception._street_aggregate とバイト一致・world/assets.py に複製)・昼夜 2 配列を World に持ち `noise_stage_for_tick`・`cells.noise_stage` は動的上書き枠(0=静的場)。合成世界は 0。
- 変化検出(起床条件(i)・dormant 抑止)の B4 行=知覚側 `b4_field_row`(LOS 6 段/m²・騒音段・流れ・顕著行為ダイジェスト)に切替→描画バイト変化の取りこぼし 1,387/2,878→0・過検出 42→0。**開閉店(open_count)は B4 行から外す**(描画バイトを変えず・知覚契約 §6(i) に無い)=開閉店は起床源でない(pin テスト)。P6 は 0.80/1.03/1.36 ms/tick(≤2 ms)。
- run_day の世界時計=DEFAULT_START_DATETIME+日+分(start_sim_datetime 欄は C6 で manifest から)・salient_events=空・flow=0(世界過程は C4)。テープ共有ブロックの intern は xxh64 で去重。
- 書き込みガード: numpy ufunc.at は writeable=False を無視→`_require_thawed` を resolve の一括更新前に置き、`np.*.at` の第 1 引数が world./agents. の呼び出しは resolve.py のみ(AST 検査・別名は module レベルの単純解決)。

**C4 世界側台帳(world/processes records/relations/registry/constitution/first_batch/actual_log/deletion_candidates・2026-09-08)で導入した自前規約(追記のみ)**:
- ProcessKind に AGENT_FALLBACK(conf 宣言つきフォールバックを型で可視化)・DeviationVocab に DELAY(delay_minutes≠0⇔DELAY)・軸2(可変性・改訂権者)は自由文・conf は executor=engine_rule 行のみ・保留チャネル(嗅覚)と封印行(S1-S3)の参照は違反・破棄行(D2/D3)は不存在扱い・`registry_hash` は to_json 書式依存・coverage_report のフォールバック比率=行数割合・WorldProcess 自身にも executor(fallback 台帳を1本で引く)。
- ActualLog: 1 行 31 B(23+索引 8)・1 対象 1 日 4 件の見積り・cap 512 MB/16 MB は S1 からの按分(予算表に行なし=delta 要)・`per_day_growth=O(N)`(日次増分の位数・累積が O(t)=D-R2-6 の趣旨)・保持窓 7 日→日次集約・compliance_rate=SCHEDULED の割合。
- 第1陣の宣言 21 過程(llm_agent 9/none 7/engine_rule 5=フォールバック台帳 5 行: rail 0.6・store_opening 0.5・vehicle_cross_section 0.4・hotel 0.4・large_event 0.3)+PlanSpec 2+細部 3+関係 13・各行に感度試験 id(AB-*)と返済期限・カタログ被覆(宣言)23/57・憲法5 検査 OK(実 doc の id 集合: 知覚チャネル 15 行・パターン台帳 48 行・観測出力 cog_* 5)・削除候補 0。B3 の届き先は PROPOSED(PENDING)。
- (C3 層2レビュー指摘で追記・09-08) 近接チャネルの件数上限は解除(max_items=len(near)・100 tok 上限は維持)・prefix_key は共有 B0-B4b のみで合成(修正)・B2 可視物の順序=可視視点数降順→ID 昇順(規約②の読み)・セルあたり可視 POI 上限 8・地物 4・未知 kind→来街者・未知 wake_reason→一般活動文・規約⑥は B4/B4b/B5 に描画経路で検査(B2 の OSM 固有名詞「…等」は対象外)・run の既定デコード temperature 0.0(Phase 2 は 0.7 で再測=事前登録)・裁定呼 temperature 0/max_tokens 256・役割語の失敗コード写像(接客/放送/遅延報告/並ぶ/撮影→BAD_TARGET・発車/停車→INTERRUPTED・指示→UNREACHABLE=親の推定)・walk_over_ticks=0 既定・不応答/却下の招待側は resolve.revert_conversation で IDLE へ戻す(修正)・`fail_streak` の 4 回打ち切り(行動契約 §6)は未消費・起床(ii)は内受容のみ(知人/近接入替/被注視/傍受は部品のみ)・注意ゲート段1-3/p_notice/dormant 抑止/PerceptionState は部品完成(結線は C4 の世界過程と同時)。

**C4 世界過程の挙動 前半(engine/processes runner/environment/rail/opening/crowd/traffic・2026-09-08)で導入した自前規約(追記のみ)**:
- runner は tick 先頭(⓪ prepare_tick の前=混雑場の流れを描画が消費するため)・憲法5 検査は起動時に fail-fast・registry_hash を RunResult へ・過程は id または AB-* で切替。
- 環境: WBGT 段→体感 (2,4,6,8,10)・日陰係数 0.86 を素の体感に乗算・セルの日陰=重心最近傍の街路点 1 点・再生日は W9 の影がある日に限定(prefer_shadow_days・現状 2026-07-28 のみ)・engine 側 select_day は build を import できないため再実装(RNG ドメイン `engine.processes.environment`=構築段と別の日を引きうる)・合成世界は固定の穏やかな日(体感 5)。
- 鉄道: DWELL 2 tick・運賃 180 円一律(IC/切符の区別なし)・容量=§2.6 の輸送力÷本数(東横 1,200/半蔵門 1,494/銀座 640 は車両数推定)・山手線の上限 139%(内/外回りは方向列から同定不能)・§2.6 の受容率は tick ごとの申込者への割当(連続率の量子化)・**§2.6 の「実効容量」2 種(定員×混雑率上限 vs 定員×2.0)→2.0 を乗り残しの硬い上限、線別上限は D10′ 照合の目標**・外界起点の個体 12%(EXTERNAL_HOME_PERMILLE 120)・到着列車=外出境界以後の最初の便(乗換/所要時間なし)・混雑率はシム内乗客のみ→5,000 体では受容が効かない・発車の移動は dep_tick の次 tick・line_capacity_12.json は src から読まない(_meta.usage_note)。**降車は in situ で 0**(LLM 往復≥1 tick+停車 2 tick=判断が発車後に落ちる・到着は engine の rail_arrive 573/日)。
- 営業時間: 5 分格子で評価・日跨ぎ区間は同日に折り返し・従業者の店舗割当=kind=従業者 の round-robin・フォールバック(conf 0.5)が 99.7%(mock は役割語を出さない=C6 の実 LLM で再測)・REPLACEMENT を「代替実行者による実現」に転用。
- 混雑・屋内: 席数=床面積÷2 m²(飲食/夜間)÷4 m²(他)・DWELL_MAX 30 tick・WAIT_MAX 15 tick・離脱=INTERRUPTED・座席割当は resolve 呼内の行順(Phase B 資源でない)・M/M/c 待ち時間は観測列のみ・流れは 3 値(一定/滞留気味/一方向=テンプレの FLOW_WORDS・8 方位は算出のみ)・B4b の行列は素材のみ(結線は後半)。
- 断面交通: 通過交通比 0.55(出典なし)・時間配分=Q12 を 7-18 時一様/残りを他時間一様・辺のセル=始点ノード・W10 の既定表を engine に転記(build を import 不可・ヘッダとの等価テスト)。
- core.types.max_tick=全オフセットで int64 に収まる上限(153,722,866)へ境界修正(hypothesis 検出)。

**C4 世界過程の挙動 後半(engine/processes goods_flow/logistics/civic/salient・L4 上限・センサス結線・shibuya.cli・2026-09-08)で導入した自前規約(追記のみ)**:
- **L4 上限の修正**: アービタは縮退呼を 0.5 と数えて累積コストで切っていたため呼数が上限の最大 2 倍まで通っていた→呼数(件数)で切る(`n_sel=min(コスト基準, floor(予算), 件数)`)+端数繰越の在庫上限 2 tick。実測 56,488→50,000 呼/日(10.00/体・上限=憲法1 の監査点)。
- 補充点=棚容量の 95%(0.80 だと実データ 1 日で補充 0=感度大)・補充ロット=満杯までの差・評価 5 分・engine_rule フォールバック 10:00(conf 0.5=台帳に行なし→**§1 末尾のフォールバック台帳へ行追加が要る**)・バックヤード=「未陳列の納品枠」(物の台帳に在庫置場の節点なし)・納品窓 05-08 時・1 店 1 便・遅延 15% 幾何分布(平均 6 分・上限 30 分)・**納品の支払いは棚入れ時**(MoneyLedger に店舗→外界の単独口がない)。
- 廃棄: 売れ残り→ビン 05:00・世帯消費 19:00 に 1 個・収集はセル順(06-10 時)・街路ごみ 0.05 g/人/tick(SKU なし=質量のみ別欄)・清掃 05-07/13-15 時 8 セル/tick。廃棄 band は 5,000 体で 1.30 t/日(≈1% 人口=規模の帰結・×100 で band 内)。
- 宅配 27,000 個/日×bbox 面積比 0.344・世帯数比配分・08-21 時 14 段・再配達なし/バス=127 停留所(座標なし→幹線の長いセルへ決定論配置)・10 分等間隔 06-23 時・乗降なし/出動=対数正規(中央値 8 分・σ0.5・上限 60 分)/報道 07・12・18 時・在席セル全部・B4 素性タグ〔放送〕/ホテル 120 室・IN 21 時 OUT 9 時/インフラ原単位 電力 0.35 kWh/人/時・水 0.012 m³/人/時/大規模イベント 18-21 時・外界から 200 人上限・3 セル/道路工事 夜間 6 辺(記録のみ・迂回なし)。
- 顕著行為: 倒れる 3.0 件/1 万体/日・座標=個体・d50 倒れる 40 m/警察 45 m・80 m 近傍=同セル+4 近傍・EventBudget 200/tick・気づいた個体=起床候補(アービタ経由)・**文面は B4(セル共有・到達分)のみ**(B5「気づいたこと」行はテンプレ v1 凍結のため未実装=改版判断)・A0-A4 は run_day(p_notice_ablation)/AB-PNOTICE-A<k>。
- B4b(行列)のダイジェストは b4_field_row の第4欄へ畳む(§6(i) が B4b に触れないため=取りこぼし回避・列を増やすと凍結形が動く)。
- 台帳の有無は世界を変える(物の過程は台帳がないと動かない)→「台帳注入でハッシュ不変」は物の過程を切った場合に限定(テスト)。
- `shibuya.cli`=層外の組立入口(engine と economy を束ねる・店舗参入資本 200,000 円/店=expedient)。`python -m shibuya.engine.run` は台帳なしの mock のまま。
- core.types.max_tick 境界修正(hypothesis)。
- (C4 層2レビュー指摘で追記・09-08) crowd: 想定床面積表 FLOOR_AREA_M2_BY_CAT(既定 80 m²)・流れ 3 値の閾値 STILL_SHARE 0.20/COHERENT 0.50。goods: SKU の質量/廃棄率(弁当 350 g・5%/飲料 500 g・1%/日用品 200 g・0%/定食 400 g・8%/ドリンク 300 g・2%/衣料 300 g・0%)・納品ログ 16 B×131,072 行(**→ D-53(2026-09-10)で N 比例 = `max(16,384, 2.0×N×保持日数)` 行へ**)・**sell_many は累積スロット払い出し**(旧「最初の非空スロット」を訂正)。goods_flow: DELIVERY_LOT_FACTOR 2。rail: 表に無い線の既定容量 1,200 人/混雑率上限 139%・§2.6(ii)(混雑率→内受容・停車時間)は未実装・(iii)乗り残し率は診断行へ追加(C4-fix)。salient: SALIENCY_BY_KIND 4 組・セル代表距離 25 m・密度 3 値の境界 2/4・d50 放送 60 m。civic: PRESS_BODY 文面・同セル複数ホテルの先頭寄せ。resolve: _SELL_SLOT_RETRIES 8(保険)。logistics: バス位相 stop_cell % headway・宅配端数の小数部降順配分。**日次センサスは閉じた日の DayClose で評価**(修正前は畳んだ後の空行列を見ていた=C4-fix)・D-R2-6 のラン終端ゲートに O(t) ログ(ActualLog/transfer_log/納品ログ)の実測を追加(C4-fix)。B4b の行列は renderer.prepare_tick(queues=) で結線済み(crowd.py の旧注記を訂正)。

**C5 経済側(economy/entry_capital・cli の既定を按分へ・2026-09-09)で導入した自前規約(追記のみ)**:
- **D-13 の置換**。参入資本[円/店] = 1事業所当たり年商(産業大分類)÷365 × 運転資金日数 k × 原価率 × 母集団比 ρ。年商は経済センサス2021活動調査・渋谷区13113・表章項目 `156-2021`「1事業所当たり売上(収入)金額」[万円]・経営組織=総数(親取得 09-07 の e-Stat JSON から**モジュールへ転記**= `data/` は gitignore 下で CI から読めないため `anchors` と同じ扱い)。注入は従来どおり `Ledger.endow_stores`(外界 → 店舗・科目 ENTRY_CAPITAL)= **ex nihilo 禁止**は不変。
- **k = 30 日**(出典なし=expedient)。**原価率**は `goods.CATEGORY_K` の逆数(コンビニ 0.20/飲食 0.303/物販 0.345)を再利用=新しい定数を置かない(域外仕入は標準原価で払うので必要額は年商ではなく仕入額)。`pricing.K_BY_KIND` は**業態順**(高級/平均/ドル箱)で並びが違うので使わない。
- **母集団比 ρ = n/400,000**(`engine.arbiter.L4_REFERENCE_AGENTS` と同分母・等価テストで固定)。ρ を入れずに実スケールの運転資金を入れると 5,000 体のランで店舗現金が貨幣供給の 99.9% を占める。ρ は線形なので**貨幣供給比はスケール不変**。
- **写像表**(POI カテゴリ 16 値 → 産業大分類・expedient): food/nightlife/hotel→M(宿泊業，飲食サービス業)・shop→I(卸売業，小売業)・office→L(学術研究，専門・技術サービス業)・service→R2・school/education→O2・landmark/leisure/hall/attraction/cinema→N・合成世界の コンビニ/物販→I・飲食→M。未知カテゴリ→N。
- **丸め=1,000 円単位で切り捨て・下限 10,000 円・上限 50,000,000 円**。運用スケール(5,000〜400,000 体)ではどちらの端も**発動しない**(下限が効くのは約 1,883 体未満)。
- **従業者数による店規模補正はしない**(POI に従業者欄が無く、`w6_org` との結合鍵 `place_id` は 100 m 格子=店舗単位でない。センサスの「1事業所当たり従業者数」は大分類ごとの定数で年商と同じ情報しか持たない)。**1 店あたり年商の分布形も置かない**(決定論優先・点=大分類の平均。設計書 §2.6 の expedient 欄は空欄のまま)。
- **実測**(実資産 2,337 店・n=5,000・seed=1・1 シミュ日): 合計参入資本 **286,293,000 円**(tick 0)。貨幣供給比 **93.02% → 89.09%**(tick 0)・**93.26% → 89.46%**(日末)。ρ=1(40 万体)なら合計 22,984,829,000 円。保存則・センサスゲートはどちらの経路でも PASS。
- `cli`: `--store-capital` は**既定 None=按分**・値を渡したときだけ一律(C4 の 200,000 円/店は `STORE_ENTRY_CAPITAL_YEN` に既定値として残す)。ラン末尾に「[参入資本] 店舗の現金+預金 / 貨幣供給 = %」の検算行を印字。
- **親判断待ち(本節では解決しない)**: ①`anchors.SALES_PER_ESTABLISHMENT` と設計書 §2.5 の I(卸売・小売)・N(生活関連・娯楽)は**末尾 1 桁落ちの転記**(生値 131,523 万円・22,527 万円 → 表記「1億3,152万円」「2,253万円」。M 宿泊・飲食 8,532 万円は 4 桁なので一致)。②区レベルの**中分類が無い**= shop に卸売業の年商が混ざる。③**町丁目別が無い**(区計 1 行)=立地差が按分に入らない。④売上が公表されない大分類(D/F/G/G1/H/J/O/O1/Q/Q1/R/R1 = `･･･` 調査していないもの、Q2 = `X` 秘匿)→ office を G 情報通信へ寄せられない。

**C5 W14/W15(build/lang・2026-09-09)で導入した自前規約(追記のみ)**:
- **層契約の例外**: `build.lang` は `shibuya.perception` の `normalize`/`channels`/`attention` を import する(他の build 段階は「manifest と core だけ」)。理由=W14/W15 は**知覚ブロックの文面そのもの**をバイト凍結するので、正規化規約を二重定義すると凍結バイト列と描画バイト列が静かにずれる(文面凍結宣言が壊れる)。`lint-imports` の 5 契約は KEPT(build → perception は層契約にも「build は実行時に import されない」契約にも触れない)。語彙定数の二重定義(騒音段語彙・行動 12 語)とは危険度が違うので**この 3 モジュールだけ**例外にした。
- **段階=2 相の純関数**: `run` は ①プロンプト jsonl を書く ②応答 jsonl が在れば入力資産として `input_hash` に含めて検証・凍結する。LLM 呼び出しは段階の外(`tools/gen/fleet_gen.py`)。応答が無くても段階は落ちない。プロンプト形式は fleet_gen の入力欄(`id/system/user/max_tokens/temperature/seed/repeat`+`thinking`)に合わせ、jsonl は `canonical_json_bytes` で書く(キー整列・LF 固定=再構築でバイト一致)。
- **`build.lang.__init__`** は他レーンと同じく `STAGES`(タプル)を持ち、段階名→関数は `run.STAGE_FUNCS`(`__init__.stage_funcs()` が遅延取得)。`build/run.py` への登録は親が行う。
- **検査器**(自前): 固有名詞 N1-N7・禁止語 E1-E3・個体語 I1-I2・省略記法 A1。詳細と語リストは世界データ構築仕様書 §4 の同名節。
- **凍結文のレンダラ結線**: `PerceptionAssets.poi_signage`/`cell_static`/`frozen_sources`。切替は world_dir のファイル有無のみ・行が無ければ従来の合成文・**テンプレ本体と `template_sha256=161fe181…` は不変**。W15 の枠 45 tok は「B2 予算 150 − 実資産での他行最大」から導出(§3.2 の `B2.visible` 60 をそのまま使うと最悪セルで B2=165 tok)。
- **テスト**: `tests/build_lang/`(33+22+15 本)。最小の合成 world_dir(セル 3・POI 4)で段階を回し、実資産テストは skipif。hypothesis 2 本=①入力が生成文を含むなら違反ゼロ(偽陽性で世界を壊さない側の保証)②入力に無いカタカナ語は必ず捕まる。

**C6-a 艦隊接続(llm/fleet・engine/run 結線・2026-09-09)で導入した自前規約(追記のみ)**:
- **in-flight の分母(親決定 09-09)**: 予算行 L6 の文面どおり **per-replica 64**(=64 in-flight/GPU)。**合計 = 64 × レプリカ数**(既定艦隊 7 本なら 448)。実装計画書 §2 部品表「レプリカごとに AsyncClient+Limits(64,64,None)+Semaphore(64)」と整合。値は `core.budget` で**表から読む**(コード側に複製しない)。`FleetConfig(max_in_flight=…)` で合計を明示上書きできる。
- **L4 の呼数=発射数(親決定 09-09)**: 「上限 400 万呼/日」は**発射した呼の数**で数える(繰り延べからの再送も 1 呼)。`RunResult.llm_calls` は選抜数=発射数のまま。再送の実数は診断行 `fleet_resent` に**別計上**する(呼数上限の分母を膨らませない)。
- **繰り延べ呼の不応期は免除(親決定 (a)・09-09)**: 繰り延べは「答えが来なかった」であって起床の抑止対象ではない(憲法1 破棄禁止の帰結)。`engine.resolve.clear_refractory`(**単一書き込み口**に置いた)で `refractory_until[個体, 条件] = 0` に戻してから起床候補へ再投入する。戻し方は expedient=同じ (個体, 条件) に別の呼が張った不応期も一緒に消える(実運用では最後の呼=いま繰り延べた呼なので実害なし・**一般には過剰に戻す**)。再投入は `since_tick` を保つ(昇格が巻き戻らない)。診断行 `fleet_reinjected`。
- **呼を捨てないの恒等式**(engine 側の監査点): `fleet_deferred_timeout + fleet_deferred_queue_full + fleet_error_other == fleet_reinjected + RunResult.fleet_unanswered_at_end`。クライアント側は `fleet_accounted == fleet_calls`。**(層2 軽-2 で訂正・09-09)** `fleet_unanswered_at_end` は**ラン終端で答えが返らなかった呼の計数**であって、次ランへ引き継ぐ仕組みはまだ無い(ラン内の状態なので**捨てられる**)。同様に終端 `drain` で拾えた応答(`fleet_drained_at_end`)は**テープには入るが世界には適用されない**(tick ループが終わっているため `pending` に積んだまま)。どちらも「1 日ランの末尾に取り残しがどれだけあるか」を測る診断で、0 を目標にする(`--fleet-wait-s` と TTL の調整点)。
- タイムアウト値 60 s/300 s は §7 の expedient をそのまま。**TTFT の定義**=「最初の `data:` 行が届くまで」→ 実測のため既定 `stream=True`(親決定 09-09: 維持。T3 は既定経路で測り、外れたら非ストリーミングでも測る)。非ストリーミングでは TTFT は e2e に潰れる。
- 接続エラーの類別: 送受信例外(`httpx.NetworkError`/`ConnectTimeout`/`PoolTimeout`/`RemoteProtocolError`)+ HTTP 5xx + 429。4xx(429 以外)と本文不正は再試行せず `error_other`(=繰り延べ)。§7 は「接続エラー」としか書いていない。
- **別レプリカ = `(primary + 1) mod N`**(`tools/gen/fleet_gen.py` の先例)。N=1 では退化=`fleet_no_alternate_replica` に計数。
- least-in-flight の発動条件 = 「割当先が per-replica 上限に達している」または「最小との差 ≥ 8」。閾値 8 は出所なし。判定に使う in-flight は**予約(発射済み+未完了)**であって実並行数ではない。
- グループ化の粒度 = `(cell, 5分帯)`(`TIME_BUCKET_TICKS=5`・知覚契約書 §2.4 ⑨)。同一 GPU 回避は `xxhash(call_id) mod N` を第一とし、**衝突した後続だけ**を次の空きレプリカへずらす最小補正(§7 の配分規則を壊さない)。グループ員数 > N なら使用集合を畳んで再開。`group_spread=False` で純 mod N に戻せる(ablation)。
- seed 導出 = `xxh64(call_id, seed=run_seed) & 0x7fffffff`(呼び出し順非依存)。
- **`cache_salt` 導出**(親決定 09-09: ランが導出して押す)= `blake3("shibuya.cache_salt" ‖ 0x1F ‖ mode ‖ 0x1F ‖ run_id)` の先頭 16 B(32 桁)。`FleetConfig.manifest_fields()` を `RunResult.fleet_fields` へ入れ、`run_manifest_fields()["fleet"]` に出す。`manifest.schema` 側の欄追加はしない(dict のまま)。mock/tape ランでは空 dict(欄は常にある)。
- 待ち行列容量 = 合計 in-flight 上限 × 4(既定)。レイテンシ標本は直近 50,000 件のリング(p50/p99)。
- **再生成のテープ表現**(親決定 09-09): 書式エラーの温度 0 再生成は**最終応答 1 行だけ**がテープに残る。再生成の事実は診断カウンタ(`fleet_format_retry` / `fleet_format_retry_ok`)にしかない=**リプレイでは 1 回生成に見える**。
- 診断行(艦隊分・21+3N 列+engine 側 2 列): `fleet_calls / ok / format_retry(_ok,_rate) / answered / deferred_timeout / deferred_queue_full / deferred_rate / error_retried_ok / error_other / conn_retry_same / conn_retry_other / no_alternate_replica / infra_clip / tokens_in / tokens_out / ttft_p50 / ttft_p99 / e2e_p50 / e2e_p99 / outstanding / accounted` + レプリカ別 `in_flight_r{i} / peak_in_flight_r{i} / calls_r{i}` + engine 側 `fleet_reinjected / fleet_resent`。終端計数は**排他**(接続再試行と書式再生成が重なった呼は FORMAT_RETRY_OK 側に数え、接続再試行の事実は `conn_retry_*` に残す)。
- 層契約の回避策(`llm` は engine/perception/world/agents を import 不可): 入口は自前 `LLMCall`(engine 側が `RenderedPrompt` から詰める)・テープは `TapeSink` プロトコル + `tape_row_factory`(engine が `engine.tape.TapeRow` を渡す=`llm.TapeLookup` と同じ依存性逆転)・`ResultCode` 写像と `t_apply` の tick 換算は engine に残す・`LANE_THINK_TOKENS` は複製し**等価テストで固定**(`tests/llm/test_fleet_contract.py`)。`llm.fleet` は `manifest.schema.Mode` を import する(層順で下向き=契約に触れない)。
- `system`/`user` の割り方 = 描画本文の先頭が B0 ブロックで始まればそこで切る、始まらなければ `("", 本文全体)`(**推測で切らない**)。テープ鍵は割る前の連結本文の `sha256_cbor`(mock ランと同鍵=艦隊ランのテープが既存 `Replay`/`TapeLLM` でそのまま再生できる)。
- 結果の返る順は**非決定**(レプリカの速さで前後)。決定性は `apply_key=(t_apply, event_class, blake3(…))` 昇順の適用(運用設計書 §2.4)が担保する。到着が遅れた応答は `max(t_apply, tick+1)` で**破棄せず**適用へ回す(締切超過=繰り延べの趣旨)。
- **`run_day(fleet_wait_s=0.0)`**(expedient): ④′ で未応答が残っているとき最大この秒数だけ待つ。既定 0=純非ブロッキング。本番(予算行 W1: 1 シミュ日 ≤24 h ⇒ 1 tick ≈ 37 秒の壁時計)では LLM の往復が 1 tick に収まるので 0 でよい。**スモーク/テストのようにエンジンが LLM より桁違いに速いラン**では、0 のままだと応答が全部ラン終端に届き δ_think の契約が観測できないので艦隊に歩調を合わせる。**本番経路は変えない**。
- 同期 1 呼経路(`FleetClient.complete`・`LLMClient` 契約)の繰り延べは `FleetDeferredError` で送出。空応答を返すと `engine.llm_bridge` が未定義→待機に落として**呼が消える**(憲法1 違反)ため。この経路はスモーク/デバッグ専用で、本番は `submit`/`poll`/`drain`。
- 役割語は `engine.llm_bridge` と同じく当面 待機 に写像+計数。
- **退化検査**(09-09 実測): mock 経路は 1 バイトも変わらない=`python -m shibuya.cli --agents 5000 --seed 1 --ticks 1440`(実資産・母集団・世界過程・台帳あり)で最終 checkpoint `combined=fbad9b8119fcc2870bc726ce2098444f4d9a5b34792cbdba9d36e76a1b3871d4`・呼数 50,000(10.00 呼/体=L4 の制御目標)・保存則 OK。
- **(C6 初回スモークを受けた追補・09-09)二重指標**: C6 スモーク(5,000 体×24 tick・実艦隊 7 本・温度 0)で書式エラー率 **0.176**(受入 ≤0.10)が出た。原因はラベル言い換え(「目的地:」「目的:」)と語彙外の行動語(探索・観察・調査)で、**応答の中身は正しかった**。`llm.parser` の別名許容(サブ Q)を受けて、指標を 2 本立てにする:
    - **実効**(主・`parse_error_rate` / `fleet_*` の `parse_errors`): C6 別名を許容した後=**世界に実際に届いた intent の書式健全性**。**温度 0 の再生成の判定もこちら**(別名で読めたら再生成しない=無駄な 1 呼を出さない)。
    - **厳密**(併記・`parse_error_rate_strict` / `fleet_format_strict_errors`): C6 以前の別名表だけで見た判定=**B11 実測 1.000 と同じ物差し**。知覚契約書 §2 卒業条件表の「書式エラー率 ≤0.10」はこの物差しで定義されたので、**受入をどちらで読むかは親判断=D-28(PENDING へ載せる)**。本節は「実効を主・厳密を併記」で実装し、判定は保留する。
    - 併せて `label_alias_used`/`label_alias_rate`(別名で読めた割合)・`dictionary_mapped`(件数は `undefined.counters()` が正典)/`dictionary_mapped_rate`(§7 段0 の辞書で救えた割合)を診断行へ。艦隊側は `fleet_label_alias_used`/`fleet_label_alias_rate`/`fleet_dictionary_mapped`/`fleet_dictionary_mapped_rate`。要約行=`書式エラー率 実効 x / 厳密 y (受入 ≤0.10) ・別名 z ・辞書写像 w`、`[艦隊書式]` 行に同じ内訳+温度 0 再生成の回数。
    - **`ParseResult.with_dictionary_mapping` は bridge から呼ばない**(親判断待ち): 段0 で救えた語を `parse.action` に載せると ①`BridgeResult.parse` は「生の応答の記述」という既存の契約テスト(`tests/engine/test_undefined_action.py`)が壊れる ②`engine.run` が会話ターンで `conv.utterance(action=res.parse.action)` を呼ぶので**発話ブロックの中身が変わる**(mock 経路不変の約束に触れる)。救えた事実は `action_code`・`undefined_stage=0`・診断行に残る。
- **(同・追補)デコード設定のフラグ化**: `--temperature`(既定 **0.7**)・`--max-tokens`(既定 **96**)を `add_fleet_args` に追加し、`FleetConfig` の既定も `DEFAULT_TEMPERATURE`/`DEFAULT_T1_MAX_TOKENS` に一本化、`fleet` dict の `decoding{T1,T2}`(運用設計書 §1.2 と同じ欄形・下位欄 temperature/top_p/max_tokens/seed)へ記録する。
    - **温度 0.7 の出所**: 運用設計書 §1.2 の設定節は `decoding{T1,T2}` の**欄形しか定めておらず数値を持たない**。数値の根拠は 知覚契約書 §2.5「温度0.7・実データ場面での再測は Phase 2=事前登録」/同 §2 卒業条件表「Phase 2 実データ・温度0.7 で再確認|≤0.10」/運用設計書 §1.3「本番(温度0.7)」の 3 か所(いずれも 0.7)。C3 の `engine.run` 既定 0.0 は **mock ランの決定論**のための値で実艦隊には適用しない。
    - **max_tokens 96 は expedient**: 2 行形の最大= 理由 40 字 + 行動語 + 対象 + ひと言 20 字 + ラベル ≒ 70 tok。認知設計書 §1 の「出力 64 tok」は**思考 0 の帯**であって出力上限の下限ではなく、64 では長い対象(`g<ix>_<iy>_<GL|UG|DECK>`)で切れ得る。切れたら `finish_reason=="length"`=`fleet_infra_clip` に出る。T2 側は U19 ③ の式(`ceil(1.5*B_world)+96`)のままで `t1_max_tokens` に依らない。
    - seed は既存どおり `xxh64(call_id, run_seed)`(呼び出し順非依存)。**mock 経路は不変**(T2 ハッシュ `fbad9b81…` を `cli --agents 5000 --ticks 1440` で再確認・09-09)。
    - `FleetBridge` の `params`(=テープ列 `params_hash`)は**艦隊の実デコード設定**から作る(mock の `{max_tokens:64, temperature:0.0}` を引きずらない)。
- **(同・追補)`run_day(fleet_wait_s=)`** は `add_fleet_args` の `--fleet-wait-s` から渡す(既定 0=純非ブロッキング)。
- **(C6 1 日ラン追調査・09-09)書式デバッグ jsonl**: `--fleet-debug-dir <dir>`(既定 off・診断のみ)。**初回パースが実効または厳密で落ちた呼だけ**を `format_debug.jsonl` へ 1 行 1 呼で落とす(`call_id`/`agent_id`/`tick`/`replica`/`system`/`user`/`first_raw`/`retry_raw`/`first_effective_ok`/`first_strict_ok`/`final_*`/`errors`/`alias_surfaces`/`raw_action`/`labels_found`/`reason`)。**テープ形式は一切変えない**(テープは最終応答 1 行のまま=運用設計書 §2.5)ので、温度 0 再生成の**初回の生応答**はここからしか採れない=`LLMResult.first_text` に保持する。行数上限 `DEFAULT_DEBUG_MAX_ROWS=5,000`(超過は `fleet_debug_skipped`)。`reason` の分類(`no_labels`/`unknown_action_word`/`missing_label:…`/`label_alias:…`/`no_action_field`/`other`)は**expedient**。
- **(同)会話ゼロの切り分け**: 読み取り専用の検死道具 `tests/engine/tape_analysis.py`(`python tests/engine/tape_analysis.py <tape_dir>`)。行動分布・対象の型・別名/語彙外の内訳・**会話を選んだ呼が「同 tick・同共有ブロック(≒同セル・同 5 分帯)」に他の呼を持っていたか**を数える。`tools/` 直下でも `tools/c6/` でもない場所に置いたのは、前者が運搬役(`fleet_gen`)の場所・後者がサブ P の作業域だから。
    - **グループの近似**: テープにセル欄が無いので、共有ブロック集合の一致を「同(セル, 5 分帯, 種別)」の代理にする(規約⑧=知覚レンダラは同一(セル,5分帯,種別)で同じ共有ブロックを引く)。近似であることを出力に明記する。
    - **判明した土台**(結線テストで確認): `engine.commit.pair_partners` は**同じ適用バッチの同セル最小 id** を相手にする=LLM が書いた `対象` 欄は **会話 では使われない**。相手が同じ tick の同じセルの呼に居なければ `target=-1` で不成立。さらに **tick 0 は真夜中で全員 SLEEPING** なので、短いランは全員が「会話」と答えても 1 件も開かないことがある。`tests/engine/test_fleet_wiring.py` の 3 本(艦隊/mock 対照/夜間対照)で **(c) 艦隊経路の結線ずれは除外**した(艦隊経路でも `sessions_opened>0`・`utterance_blocks>0`)。
- **(同・サブ Q 第2弾の結線 09-09)** `ParseResult.dictionary_candidate` があれば**温度 0 の再生成をしない**(語彙外でも §7 段0 の辞書で確実に救えるため・C6 実測で初回失敗の 30% が語彙外=無駄な 1 呼を出さない)。`fleet_dictionary_mapped` に計上し `fleet_format_retry` からは外す。`positional_used`(ラベルを省いた並びを位置で読んだ)を `fleet_positional_used`/`fleet_positional_rate`・engine 側 `positional_used`/`positional_rate` と要約行へ。
- **(同)P2(movement)の切り分け**: `phase_seconds` に `fleet_wait`(`--fleet-wait-s` の待ち・`llm` から分離)と **`movement_cpu`**(movement 区間の `time.thread_time`=**スレッド CPU 時間**)を追加し、要約に「内訳[ms/tick]」行と「movement 壁 x / CPU y ・待ち割合 z」行を出す。壁時計と CPU の差=**仕事が増えたのではなく待たされた**の証拠(実装計画書 §4「httpx イベントループと計算の干渉。出たら LLM クライアントを別プロセスへ」の判定材料)。`time.thread_time` は Windows では解像度 ≈15.6 ms で小さいランでは 0 になる=**実測は Linux サーバー側**。
    - **ローカル実測(5,000 体×24 tick・139 セル・stub レンダラ・偽艦隊 7 本)**: 素の numpy 0.020 / mock 0.081 / mock+アイドル艦隊スレッド 0.126 / 艦隊 wait=0 0.294 / 艦隊 wait=1 0.498 ms/tick。**同じ numpy 仕事で 3〜6 倍**に膨らむ=`movement` に新しい仕事は入っていない。
- テスト: `tests/llm/test_fleet.py`(27)・`tests/llm/test_fleet_contract.py`(16・hypothesis 2)・`tests/engine/test_fleet_wiring.py`(20)。偽 vLLM は**プロセス内**(`http.server.ThreadingHTTPServer`+`httpx.MockTransport`)で、実サーバー(SSH)へは繋がない。
- **退化検査ハッシュの履歴(親・09-09)**: 艦隊結線単独では mock 実資産ランの checkpoint は fbad9b8119fcc287…(C5-b と同一)。その後の「C6 会話招待の設計準拠」(両側 CONVERSING・0.8 抽選廃止・フォールバックの blake3 撹拌)で **eb7e07ccab05ec72…/sessions 67** へ変化(HEAD 版で旧値を再現済み・層2 中-3)。以後の変更で再度変わる場合は同じ書式で追記する。

**C6 会話招待の設計準拠(engine/commit・conversation・resolve・run・2026-09-09)**:
- **対象スロットを使う**(行動契約書 §1-2)。`engine.commit.talk_partners` を新設: ①LLM が書いた `対象: P-<id>` が範囲内・自分でない・**同一セル**(知覚契約書 §3.7 の雑談可聴 1-2.5 m を C3 と同じくセルで代理)なら**その個体**を相手にする ②さもなければ `pair_partners`(同じ適用バッチの同セル最小 id)へフォールバック(**expedient のまま**・計数) ③どちらも無ければ相手なし。C3 の「対象はエンジンが文脈から導く」は expedient で、**LLM の対象欄を無視していた**=設計との差だった。
- **承諾は Phase C の前に消費する**(層2 中-1・09-09)。被招待 B の承諾「会話 対象: P-A」を intent のまま Phase C へ流すと、A は招待して CONVERSING なので `resolve._apply_talk` が `PARTNER_BUSY` を書き、**B の「直前の結果」(B6)に偽の失敗**が載る(層2 再現: 200 体 1 セル 700 tick で 51 セッション中 45 件)。`engine.run._settle_pending_invites` を Phase A の直後(`intents_from_responses` の**前**)に置き、承諾した行を intent から外す(承諾は新しい招待ではない)。第三者名指しは**外さない**(C への新規招待として通す)。
- **二相の招待**(知覚契約書 §6 起床(ii) の被招待)。相手がその tick の適用バッチに居ない=**まだ招待を見ていない**ので、その tick の相手の応答は招待への返事ではない。よって `ConversationManager.register_pending` に積み、**次 tick に `WakeCondition.CONVERSATION_TURN` で起床**させて本人の呼で答えさせる。返事が 会話 なら `resolve_pending(accepted=True)` で成立、それ以外は不成立→招待側は `revert_conversation`。**相互指名**(お互いが相手を名指し)はその場で成立させる。
- **応答確率 0.8 の抽選をやめた**。`ConversationManager.invite(answered=…)` を足し、答えが分かる場面では抽選を引かない(`ACCEPT_PROBABILITY` は**較正の目標値であって機構ではない**)。抽選が残るのは `answered=None` の直接呼び出し(単体テスト・旧経路)だけ。
- **両側 CONVERSING**。`resolve.set_conversing` を新設し、成立時に招待側と被招待側の `activity`/`talk_partner` を同時に書く(C4 の既知の穴「resolve が招待側のみ CONVERSING」を閉じた)。解放は従来どおり `conv.step` の終了時に `revert_conversation` が両側へ。**すでに別セッションに入っている個体は戻さない**(相互招待 A→B・B→C で B が引き剥がされる穴を塞いだ)。
- **相手別不応期**(**expedient**・層2 中-5①)。`agents.state.refractory_until` は体×条件で**相手別を持てない**(C2 で未実装として登録済み)ので、対の表は `ConversationManager` が持つ: `PAIR_INVITE_REFRACTORY_TICKS=60`・`SPEAKER_INVITE_REFRACTORY_TICKS=30`。**値は知覚契約書 §6 不応期表の「知人出現 60 分」「傍受 30 分」からの転用**で、同表に「被招待」の行は無い=**根拠のある値ではない**(ablation 対象)。招待は成否によらず刻む(`stamp_invite_refractory`)。**相互指名の経路も検査・刻印する**(層2 軽-5・09-09 追加)。
- **承諾の対象規則**(**expedient**・層2 中-5②): 返事が 会話 かつ 対象が**招待者**または**名指しなし**なら承諾。第三者を名指した 会話 は招待者への**拒否**として扱い、その返事は intent に残して**第三者への新規招待**として通す。行動契約書 §3 に承諾の対象規則は無い(「1 呼 1 発話ブロック」までしか定めていない)ので、対象スロット(§1-2)の素直な読みを採った。
- **`_apply_talk` の「相手 idle」を緩めた**(**expedient**): C3 は相手が `Activity.IDLE` であることを要求していたため、移動中・待機中・買い物中の相手に声をかけられず、**C6 の 1 日ランで会話が 1 件も成立しなかった**。声をかけられない相手を `_UNADDRESSABLE=(CONVERSING, SLEEPING)` に限る(会話中=§2.1 の `PARTNER_BUSY`・就寝中=応答できない)。「話しかけられる状態」の正典は無い=ablation 対象。
- `PENDING_INVITE_TTL_TICKS=3`(expedient・δ_think L1 1 tick + 繰り延べ 1 tick の余裕)。期限切れは「無視された」= 呼を消費しない(§3)。
- 診断行: `conv_invites` / `conv_accepted` / `conv_declined` / `conv_pending_expired` / `conv_pending_open` / `conv_invite_refractory_blocked` と、相手の由来 `conv_target_named` / `conv_fallback_same_batch` / `conv_target_absent`。
- **mock の T2 ハッシュは変わる**。理由は ①両側 CONVERSING(被招待側の `activity` が動く) ②0.8 抽選の廃止(MockLLM は文脈を読まないので被招待として 会話 と答えるのは 1/12)。**MockLLM は「対象: なし」しか書かない**ので `conv_target_named=0`=名指し経路は mock では通らない(実測で確認)。stub レンダラ・5,000 体×1,440 tick の対照: **`8b18eec7…`(C6 前・呼 43,612・sessions 195)→ `8428cc73…`(現在・呼 43,845・sessions 43・invites 572/accepted 43/declined 244/expired 262)**。**セッション数の減少は結線の不具合ではなく「相手が自分で決める」ようにした帰結**(親判断: mock day を下限対照として使うなら抽選を戻す口が要る)。
- **ID 順バイアスの是正**(T5・サブ P のテストが検出): フォールバックの「セル内**最小 id**」は ID 順の規則で、被招待も起床するようになった C6 では **`wake_count` の ID 相関 |r|≈0.10**(受入 ≤0.05)を作った(v1 C-8 の再来)。`pair_partners(order_key=)` を足し、`intents_from_responses(run_salt=)` から `core.hashing.wake_tiebreak_array`(blake3 撹拌)を渡す形へ。**修正後 |r|=0.0017**(T5 8 本 合格)。`order_key=None`(=ID 順)は単体テストと後方互換のためだけに残す。
- テスト: `tests/engine/test_conversation_invite.py`(15・純関数/返事待ち/不応期/両側 CONVERSING/通し 2 本)。

**C5-a(build/pop・W16 母集団合成・agents/population・2026-09-09)で導入した自前規約(追記のみ)**:
- `build.pop.shapefile`: ESRI Shapefile の**最小パーサ**(部品表に geopandas/pyshp/shapely が無い)。対応は shapeType **0/5 のみ**・.dbf は dBASE III の C/N 型・**cp932 固定**・削除行は落とす。範囲外の shapeType は黙って読まず `ValueError`。点包含=レイキャスティングの**全パート交差数の偶奇**(穴つきでも正しい)。逐次ループは「リングの辺数」「ポリゴン数」「レコード数」で、点数・体数には比例しない(P4 宣言)。
- `build.pop.fitting`: SRMSE の定義を `sqrt(K·Σ(p_sim−p_obs)²)`(割合ベース・答申の出典と同型。性別 K=2 では片側 0.5 ポイントで 0.01 = 決定台帳のラインちょうど)。IPF は 2 次元・反復上限 200・収束 tol 1e-9(周辺の最大絶対残差/総和)。**種が全 0 の行/列は一様種で埋める**(構造的ゼロと標本ゼロを区別できないため)。整数配分は最大剰余法・同点は添字の小さい方(決定論)。
- `build.pop.pool`: ペルソナプール(100 万行 JSONL)から**必要な欄だけ**列化(6 秒級)。`gender` の「男/女」→ 0/1、欠測 −1。
- `build.pop.w16_population`: 親シード **MASTER_SEED=20260909**(`core.rng` の master_seed・param_hash に載る)。ドメインは `w16.*`(draw/chome/direction/school/seat/sample/dispatcher)。出力は `w16_population/households/duty_roster/chome.parquet` + `w16_gates.json` + `w16_cohorts.json`。カタログ写像=#13/#14/#15。
- `agents.state.AgentKind` を **5 値 → 9 値**へ拡張(0-4 は不変・5 STUDENT/6 REGULAR_VISITOR/7 FOREIGN_VISITOR/8 CREW)。`economy.anchors.WalletKind` と `DAILY_SPENDING_BY_KIND` も同じ並びで拡張(新種別の日消費は既存行の写し=expedient)。**`perception.templates.KIND_WORDS` は広げていない**(v1 の凍結テンプレ SHA に入っているため=改版は親判断待ち。表に無い種別は renderer が「来街者」へ落ちる)。
- `agents.schedule`: mock の種別抽選を `len(AgentKind)-1` から定数 **`MOCK_KIND_COUNT=4`** へ置換(種別を足しても既存 mock の乱数列が動かないように釘付け)。`MockWeeklySchedule` に **省略可能欄** `age`/`sex`/`direction_node`/`population_hash` を追加(mock 単独では `None`/`""`)。
- `agents.state`: `age`(uint8)・`sex`(int8・−1=不明)を SoA へ追加(M6 プロフィール枠)。宣言合計 119→**121 B/体**(M1 30,000 B の内数)。書き込みは `engine.resolve.initialize` のみ。
- `agents.population`: `Population` は W16 の列そのまま。`start_cell()`=自宅→勤務→通学→fallback(**W17 が入るまでの繋ぎ**・域外常住の体を街に置く規約)。`population_hash()`=blake3(列名・dtype・生バイト)。二層抽出の**定員先取り層**= `pool_layer==5`(プール L5=乗務・駅務・警察/消防・議員)∪ `kind==DISPATCHER`、**統計層**=(種別×年齢階級×性別)の最大剰余法(層の在庫を超えたら余っている層へ押し戻す)。`n` が定員先取り層より小さいときは定員層だけを取る。
- `engine.run`: `run_day(population=...)`。`None`(既定)は `world_dir` に `w16_population.parquet` があれば**自動で読む**が、**世界のセル数と合わないときは黙って合成個体へ落ちる**(`world_dir` を知覚資産の置き場としてだけ渡す既存の使い方を壊さないため)。明示的に `Population` を渡した場合だけ食い違いを例外にする。`False` で下限対照。`Checkpoint` に `population_hash` 欄を足し、`combined`(T1/T2 の一致判定)に混ぜた。
- CLI: `python -m shibuya.engine.run --no-population` を追加。`shibuya.cli` は `world_dir` 経由で自動的に母集団を使う(切る口は未追加)。
- テスト: `tests/build_pop/`(単体 17 本=Shapefile 往復・点包含・穴・最大剰余の性質2本(hypothesis)・IPF 4 本・SRMSE/JSD・二層抽出 5 本、実データ 11 本=ゲート全合格・80 町丁目一致・再構築バイト一致・ローダ・1 日ラン)。5,000 体×1 日は `@pytest.mark.slow`(実測 17.4 s)。
- 実測(親検収用): W16 単体 **9.2 s / ピーク RSS 720 MB / 390,188 体**、`w16_population.parquet` 4.61 MB(11.8 B/体)。全段階通し 25 s・`build_hash` = `0100706bcaf01078…`。

**C5-a 仕上げ(定員先取り層を機能定員へ・世帯財布を anchors へ結線・写し定数の等価テスト・2026-09-09 夕)——追記のみ・決定項は不変**:
- **定員先取り層の再定義(層2 中-1)**。旧: `pool_layer == 5`(プール L5 の**全件**)∪ `kind == DISPATCHER` = **1,316 体**= 5,000 体ランの **26.3%**。新: **役割名の表** `agents.population.RESERVED_ROLES` = 駅員・電車運転士・車掌・バス運転士・指令・警察官・消防士・救急隊員・議員 の 9 語。答申 §Q6-b「乗務員・指令・議員・警察/消防など**機能に必要な最小定員**」の読み= 公共交通の運行(鉄道乗務・駅務・バス)+ 運行/警備の指令 + 治安・救急 + 制度側。**タクシー運転手 350・路上生活者 80・ティッシュ配り 30・配信者 16・ストリートミュージシャン 15・清掃作業員 12・納品ドライバー 10・夜間清掃員 10・募金スタッフ 6・キッチンカー営業者 6・街頭演説者 4・路上占い師 4・路上支援員 4(計 547)は統計層**=縮尺の対象へ移した。
- **実測**: 定員先取り層 **769 体**(駅員 300・警察官 140・バス運転士 120・電車運転士 60・消防士 45・車掌 40・議員 34・指令 24・救急隊員 6)= 5,000 体ランの **15.4%**(1,316 体・26.3% から低下)。統計層に残った職務者は n=5,000 で 4 体(タクシー 2・路上生活者 1・配信者 1)。統計層の種別構成比は 40 万体版と一致(全種別で差 <0.01・テストで機械検査)。
- **expedient(残る)**: 役割ごとの**実定員は公表値が無く**、v1 プール L5 の在庫体数をそのまま「最小定員」とみなしている。**答申の目安「概算 300-400 体」に対して実測 769 体**= 駅員 300 が支配的(渋谷区内の駅 16・24 時間 3 交代を仮定すると桁は合うが、根拠は在庫であって公的値ではない)。**親判断待ち**: (a)駅員を統計層へ移す/定員を減らす、(b)769 のまま「機能定員」として登録する、のどちらか。
- **`agents.population` の変更**: `Population` に `duty_role`(省略可能・旧資産では `None`)・`counts_by_duty_role()` を追加。`reserved_mask` = `duty_role ∈ RESERVED_ROLES` ∪ `kind ∈ RESERVED_KINDS`(指令の保険)。`RESERVED_POOL_LAYER` は **`DUTY_POOL_LAYER` へ改名**(名簿の出所を示すだけで判定には使わない)。ローダは parquet のスキーマを見て `duty_role` が無ければ `None` で読む(旧資産で落ちない)。`AGE_EDGES` は 15 → **16 階級**(W16 と同時)。
- **層をまたいだ写し定数の等価テスト(層2 中-3)**: `tests/build_pop/test_pop_units.py` に 4 本。①`build.pop.w16_population.KIND_*` == `agents.state.AgentKind` の 9 値かつ `len(KIND_NAMES) == len(AgentKind)`、②`W16.AGE_EDGES == agents.population.AGE_EDGES` かつ 16 階級かつ `CENSUS_AGE_CATS`(総数/男/女)の長さ一致、③`RESERVED_KINDS == (AgentKind.DISPATCHER,)`・`DUTY_POOL_LAYER == 5`・`RESERVED_ROLES` が非空、④役割名の**綴り**が構築側の語彙(`RAIL_CREW_ROLES` ∪ 指令)と一致。加えて実データ側で `RESERVED_ROLES` の全語が名簿に実在することを確認(綴り違いで定員層が空になる事故の検出)。
- **世帯の初期財布を `economy.anchors` へ結線**(サブ K 親判断待ち 5 の解消)。`agents.schedule.synthesize` の一様 2,000〜10,001 円は **mock 専用**のまま残し、W16 母集団を載せたランでは `anchors.initial_wallets`(対数正規・中央値 = 種別ごとの日消費 × 3 日・σ 0.6・clip 1,000〜2,000,000 円)を使う。層契約(`agents` は `economy` を import できない/`engine` も `economy` を import できない)を守るため、**層外の `shibuya.cli`** が母集団の `kind` 配列を読んで金額を作り、`Ledger` の派生 `_HouseholdWalletLedger` が `endow_households` の**入口で金額だけ差し替える**。経路(外界 → 世帯・科目 CARRY_IN)は不変 = **ex nihilo 禁止・保存則・センサスは不変**。乱数は `core.rng` の Philox・ドメイン **`wallet.initial`**(manifest のドメイン表に 1 行増える)。母集団の体数を超える行(縮小ラン)と `--no-population` は mock のまま。
- **実測(n=5,000・seed=1・1 シミュ日・実資産)**: 貨幣供給 **321,304,562 → 425,825,162 円**。`[参入資本]` 店舗の現金+預金 287,398,694 円 = **67.49%**(C4 一律 200,000 円 93.02% → C5 按分のみ 89.46% → **C5 按分+世帯財布 67.49%**。サブ K の見立て「約 70%」と一致)。`[世帯財布]` 138,426,468 円 = 32.51%(mock 経路は 33,867,103 円 = 10.54%)。保存則 OK・日次センサス PASS(残差 0)・2 回のランで最終 checkpoint ハッシュ一致(`37c11b91e0ebf8a5…`)。
- **登録簿の日末比率の訂正(軽)**: 「93.26% → 89.46%(日末)」の **89.46% は `--no-population`(mock 財布)の日末値**として再現(09-09 実測)。母集団あり・mock 財布 = 89.43%(親の C5-a 実測)、母集団あり・anchors 財布(**現在の既定**)= **67.49%**。3 つは経路が違うので併記する。
- **`shibuya.cli --no-population`**(軽-5): `engine.run --no-population` と同じ意味(母集団を読まず合成個体・世帯財布も mock)。`cli.run(use_population=False)` が入口。ラン末尾に `[世帯財布] … (mock 一様|anchors 対数正規・母集団あり|--no-population)` の検算行を印字。
- **親判断待ち(本節では解決しない)**: ①定員先取り層 769 体 vs 答申の目安 300-400(上記)。②境界・経済設計書 §2.6「財布の現金初期分布」の expedient 欄は**分布形が無い**まま(対数正規 σ0.6・3 日ぶんは自前)——実データの家計金融資産分布に当てるかは未決。③`--no-population` のランで `最小在庫 46`・母集団ありで `0`(mock 個体と実個体で購買が違う=想定内だが在庫下限の意味が経路で変わる)。④状態成長宣言の `actual_log_raw` 超過は**本仕上げ以前から出る**(母集団の有無に関わらず同じ)= D-R2-6 の delta 改訂待ち。

**C5-b W17(build/sched・agents/weekly・2026-09-09)で導入した自前規約(追記のみ)**:
- **層契約は素のまま**: `build.sched` は `manifest`/`core`(+ 同じ build 内の `geo.common`・`pop.w16_population` の種別定数)だけを import する。**W14/W15 と違い `perception` は import しない**——あの例外は「凍結バイト=描画バイト」を守るためで、W17 の出力は知覚ブロックの文面ではなく構造化された表なので、例外を作る理由がない。トークン推定 `estimate_tokens`(UTF-8 文字数 ÷ 2)は `perception.channels`/`llm` と**同一規約の三重定義**になる。`lint-imports` の 5 契約は KEPT。
- **語彙の二重定義を機械検査する**: `build.sched.vocab`(構築側)と `agents.weekly`(ラン側)が活動語 12・場所語 12・行動語への写像・起床条件への写像を**それぞれ**持つ(`agents` は `build` を import できない)。`tests/build_sched/test_weekly_loader.py::test_vocabulary_double_definition_agrees` が一致を、`test_wake_conditions_match_perception_contract` が `agents.state.WakeCondition` との一致を検査する。`agents.population` の `AGE_EDGES`/最大剰余法と同じ扱い。
- **段階=2 相の純関数**(build.lang と同型): ①プロンプト jsonl を**ストリーミングで**書く(39 万行をメモリに載せない・`--shard i/n` で分割)②応答 jsonl が在れば入力資産として `input_hash` に含め、行パーサ → 整合修復 → raking → parquet。応答が無くても段階は落ちない。プロンプト行は fleet_gen の入力欄(`id/system/user/max_tokens/temperature/seed/repeat/thinking`)に合わせるが、**`build.lang.common.Prompt` は使えない**(あちらは温度 0・seed 固定・repeat 2 をクラス定数で焼いており、W17 の温度 0.7・seed=hash(agent)・repeat 1 を表現できない。かつ import すると perception まで引き込む)= `build.sched.w17_schedule.SchedPrompt` を別に置いた。
- **`build.sched.pool_facts`**: ペルソナプールから W17 が要る欄(`occupation`/`shift_pattern`/`work_days`/`visit_cadence`/`duty_pattern`/`bedtime_min`/`sleep_steps`/`school_stage`/`residence_line`)だけを引く読み取り器。`build.pop.pool` は W16 が要る欄しか列化せず(`shift_pattern`/`duty_pattern` は dict なので未対応)、**`build.pop` は本工程の編集対象外**なので W17 側に口を置いた。行順は `pool_index` と同じ(part ファイル名順)。**必要な行だけ `json.loads`**(残りは行数を数えて飛ばす)= 100 万行のプールから 39 万行を 5.6 s で引く。
- **メモリ設計(RSS ≤2 GB)**: 取り込みの中間表は `array.array`(agent 4 B + day 1 + start 2 + end 2 + activity 1 + place 1 + modified 1 = **12 B/活動**)。numpy へ移した後も **int32/int8 のまま**扱う(int64 に広げると 1,600 万行で +0.5 GB)。raking の並べ替えキーは候補行ぶんだけ作る。実測ピーク RSS = **734 MB**(39 万体・656 万活動)/骸格フォールバックが 95% の最悪ケースでも **1,002 MB**(1,157 万活動)。
- **逐次ループ宣言(P4)**: `build_facts`(体数ぶん・勤務窓と来訪日)/`iter_prompts`(体数ぶん)/`ingest` の本体(体数ぶん・パースと修復)/`pool_facts.read_facts`(プール行数ぶん)。いずれも**構築時 1 回**(I1 の外・ランのループではない)。`rake` は「目的数 × 24 時間」のループだけで活動数に比例しない。`agents.weekly` はループ**ゼロ**(CSR + `np.repeat`/`np.searchsorted`)。
- **テスト**: `tests/build_sched/`(**90 本**= プロンプト 20 + パーサ 20 + 修復/raking 28 + 取り込み 11 + ローダ 11。うち 1 本が `slow`=実データ)。最小の合成 world_dir(体 10・POI 4・プール 5 層)で段階を回し、実データは skipif+`slow`。hypothesis 2 本=①`format_line` → `parse_line` の往復(全語彙×全時刻)②seed の範囲と決定論。1,000 体のモック応答でストリーミング取り込みを回す規模テストつき。
- **実測(親検収用)**: プロンプト生成 11.3 s / RSS 283 MB / 呼数 390,067(=体数・repeat 1)/ 入力 tok 平均 339.9・最大 350 / `w17_prompts.jsonl` 683 MB。取り込み 40.6 s / RSS 734 MB / `w17_schedule.parquet` 6.53 MB(16.7 B/体)/ ローダ 266 B/体(M3 12,800 B/体 の 2.1%・週 42 活動なら 576 B/体)。
- **結線は入れていない**(編集禁止ファイル): `agents/schedule.py` の合成表を W17 表で置き換える箇所・`engine/run.py` の計画境界スライス・`build/run.py` の `RUN_ORDER` への W17 追記は**差分案として報告**し、親が入れる。

**C5 W14/W15 第2回改訂(build/lang・2026-09-09・第1回生成の全件分析が根拠)**:
- **第1回の実測**(親が ingest): rep 間バイト一致率 **1.000**(温度 0 の決定性は成立)。不合格率は W14 **0.131**(307/2,337・閾値 0.10)/W15 **0.283**(147/520・閾値 0.05)で **FAIL**。内訳 W14 = N7 漢字 113・N4 数字 78・too_long 72・N1 英字 47・N2 カタカナ 11・N3 4・その他 3 / W15 = A1「など」106・N4 数字 50・too_long 7・I1 一人称 5・N2 4・N3 2・N1 1。**原因は検査器の偽陽性(W14 側の N1/N7/N2 計 171 件)とプロンプトの欠陥(数字を含まない入力表現・曜日別内訳の書き写し・「など」)の 2 つ**で、モデルの捏造そのものは W14 で 6 件(0.26%)だけだった。
- **検査器の修正**: ① N1 は**ラテン語単位**(空白・数字で割る・アクセントと空白を畳んで大小無視で照合)=「Skechers 11」「Curry Shop C & C → C&C」「Créa → Creá」を通す。② N7 は**3 文字以上**に限定し、一般漢語表を 60 語超へ拡張(開館/開校/参拝/診療/利用/軽食/紹介/用品/料理/専門店/休館 ほか)。**曜日の略記(「月金」「火曜金曜」)は N7 でなく A1 の新規則 `A1_weekday_abbr` が見る**(入力にそのまま在る表現は略記としない)。③ N2 の一般カタカナ語表を約 100 語へ拡張(スイーツ/パチンコ/クリニック/イタリアン/デザート/サンドイッチ/グッズ/カレー/ハウス/アイス/クリーム/ヘア/ファストフード/ブランド/トラック ほか)。④ N3 も文字単位の残差方式にし、残りが 1 文字でも**接尾辞そのもの**(駅・坂・寺・橋)なら不合格にする(「渋谷駅」を足す形は捕まえ、「KOMEHYO (コメ兵) 買取センター渋谷 → KOMEHYO買取センター」は通す)。⑤ `_residual` の入力照合を**語単位から文字単位**(長い部分文字列から貪欲に除去・候補長 24 まで)へ。⑥ **N4(数字)は変更しない**——「毎日終日」に対し 10-22 時と書いた 74 件は真陽性。ただし**比較の前に入力側を NFKC 正規化**する(全角数字の POI 名で偽陽性が出るため)。⑦ `_strip_known`(規約⑥ の前処理)は**省略記法の語そのものを除去しない**(プロンプトに「「など」を使わない」と書くと、その「など」が入力語として拾われ⑥が素通りする)。
- **W14 プロンプトの改訂**: ① `[0,1440]` の表記を「終日」→**「24時間」**、全曜日 24 時間は**「24時間営業(毎日)」**(数字 24 を入力に含めることで、コンビニ等が数字つきで書ける)。② 営業時間を**多くて 2 帯に圧縮**して渡す(全曜日同一→「毎日<帯>」/平日群・土日群でそれぞれ一定→「平日は<A>、土日は<B>」/それ以外→**代表日**(営業分数最大・同点は曜日番号の小さい方)の**最初の区間**+「(曜日で異なる)」。1 日に複数区間あれば最初の区間だけ+「(時間帯で異なる)」。2 帯でも `MAX_HOURS_CHARS`=**24 字**を超えたら代表日 1 帯へ落とす)。群の一部だけ営業なら「平日」と書かず曜日を出す。**実測: 営業時間表現は平均 10.7 字・最大 26 字**(第1回は曜日別の全内訳)。③ system に「営業時間は与えられた表現をそのまま使う・曜日ごとの内訳を作らない・曜日を略さない」「**45 字以内の 1 文**・収まらないときは価格帯→業種の順に省き、店名と営業時間は残す」を追加。
- **W15 プロンプトの改訂**: system に ①**「など」「等」「ほか」「その他」の禁止**(全部書けないときは名前を省いて種別だけ書く) ②**個数を数字で書かない**(入力にある数字はそのまま使ってよい) ③一人称(私・僕・我々)の禁止 ④**区画IDと広さを書かない**(全区画で同じ=憲法5) ⑤「「見えるもの:」に続けて読まれる文として書く」を追加し、user 末尾にも短い念押しを置いた。禁止語を例示に使わないよう、他の規則の「〜など」は「〜のような」に置き換えた。
- **版**(旧→新): W14 `prompts_sha256` b2ac72b4ebd11e16… → **5923438d63ffd351…**・`system_sha256` 85c0dc6f76f2c9c7… → **247a39b391a9eca0…**。W15 `prompts_sha256` cebe004ade8f8f76… → **75c75ce2d59e89a1…**・`system_sha256` ed83619d26a824ec… → **963309344037aab3…**。seed 20260909・temperature 0・repeat 2・thinking false は**据え置き**。W14 入力 306.3 tok 平均(旧 243.5)・W15 433.8 tok 平均(旧 317.2)。
- **修正の効き(第1回の応答 × 新検査器で再判定・旧プロンプトの allowed を復元して測定)**: W14 0.131 → **0.085**(N1 47→1・N7 113→3・N2 11→2・N3 4→0)。残りは N4 74・too_long 72・`A1_weekday_abbr` 50 で、いずれも**プロンプト改訂で狙った的**。残存する真陽性は 6 件のみ(歌広場→「歌庯場」×3・ホみや→「ホミヤ」・TAKEZAWA→「TAKESAWA」・Harry's→「ハリス」= すべて名称の改変)。W15 は 0.283 → 0.275(W15 の不合格はすべてプロンプト起因なので検査器修正では動かない=改訂の効果は再生成後に測る)。
- **第1回の生成物の扱い**: `w14_responses.jsonl`/`w15_responses.jsonl` は `*.round1.jsonl` へ改名、凍結済みだった `w14_signage.parquet`/`w15_cell_static.parquet`/`*_gates.json` は `round1_` 接頭辞へ退避した(ゲート不合格の凍結文をレンダラが拾わないようにするため。削除はしていない)。

**C5-b W17 第1回パイロット後の改版(`stage_version` 1.1.0・2026-09-09 夜)**:
- **決定論の修正(親指摘)**: `W17.header.json` の `notes.wall_clock_s` に壁時計が入っており、2 回の構築でヘッダのバイトが変わって W18 の `input_hash` → `build_hash` が毎回変わっていた(`tests/build_field/test_field_pipeline.py::test_rebuild_is_byte_identical` が FAIL)。**ヘッダ(=ハッシュ対象)から時間計測を全部外し**(`import time` ごと削除)、壁時計は CLI の標準出力だけに残した(W16 と同じ扱い)。`tests/build_sched/test_w17_ingest.py` に ①2 つの世界ディレクトリで構築して `W17.header.json` がバイト一致 ②ヘッダ JSON 全体に時刻・壁時計・絶対パスが現れない、の 2 本を足した。**教訓: ヘッダに入れてよいのは入力から決まる値だけ。計測はゲート/標準出力へ。**
- **パーサの戻り値**: `vocab.parse_line` は `(活動, 理由)` → **`(活動, 理由, 直した印)`** の 3 要素へ。同義語表で寄せた行は `fix_activity`/`fix_place` として数え、`FAILURE_REASONS`(捨てた行)と分けた=`parse_fail_rate` の分子が「本当に捨てた行」だけになる。
- **`repair_day` の規則 8**(`_fill_day`): 1 日の活動が `MIN_ACTS_PER_DAY=4` に満たない日を `skeleton_day` から**隙間に入る分だけ**補う。`skeleton` は `skeleton_day` の 7 日連結へ分解。
- **`--pilot N` / `--pilot-ingest`**: 種別ごとに N 体を抜いた `w17_pilot_prompts.jsonl` を書く/`w17_pilot_responses.jsonl` を取り込んで**報告だけ**する(parquet もヘッダも書かない)。本番の応答 glob と当たらない名前にしてある。
- 詳細(パイロットの実測値・facts 規則・同義語表・プロンプト改版履歴 v1 `6927a1d7…` → v2 `8b6102c0…`)は世界データ構築仕様書 §4 の同名節。
- **テスト**: `tests/build_sched/` は 90 → **123 本**(パーサ +21・修復 +3・取り込み/パイロット/決定論 +7・プロンプト +3・既存の書き換え)。

**C5 W14/W15 第3回改訂(build/lang・2026-09-09・第2回生成の結果が根拠)**:
- **第2回の実測**(親が ingest): rep 間バイト一致 1.000。**W14 は合格**(不合格率 **0.040**・凍結 2,243/2,337)。**W15 は不合格**(**0.362**・too_long **181/188**=不合格の 96%・I1 一人称 8・N4 3・A1 1)——「など」を禁じて名前を列挙させた結果、45 tok(90 字)の枠を大幅に超えた。W14 の残り理由は `A1_weekday_abbr` **56**(「土曜日曜」「土曜日曜日」= 入力の「土日は…」をモデルが曜日名へ展開したもの)。
- **A1 曜日判定の修正(W14 の凍結率を上げる・再生成なしの再 ingest)**: 略記の定義を「**完全な曜日名(`[月火水木金土日]曜日?`)を落としたあとに残る、曜日字の 2 文字以上の連なり**」に変えた。「月金」「土日」は略記(入力にその表現が在れば通す)、「土曜日曜」「土曜日曜日」「火曜金曜」「月曜から金曜」は**略記でない**。N7 の残差前処理も同じ規則に合わせた。**効果(第2回の応答をそのまま再 ingest)**: 不合格率 0.040 → **0.0180**・凍結 2,243 → **2,295 行(+52)**。残り 42 件の内訳は too_long 30・I1 7・E1 2・N1/N2/N7 各 1(いずれも真陽性)。**W14 のプロンプトは 1 バイトも変えていない**(`prompts_sha256` 5923438d… のまま)。
- **W15 を「枠に収まる設計」へ変更**(親指示):
  - **プロンプトに載せる可視物を上位 2 件・目印を上位 2 件に前処理**(`MAX_VISIBLE_POI`/`MAX_VISIBLE_LANDMARK` 8/4 → **2/2**)。選び方は決定論で `renderer.PerceptionAssets.load` と**同じ順序**(可視視点数の降順 → target_id 昇順)の先頭から。レンダラ側の合成フォールバックは 8/4 のまま(件数だけがプロンプト固有)。
  - **セル内 POI の構成を「最も多い種別 1 語」に圧縮**(件数つきの「飲食店8、サービス店3…」を廃止)。同数は業種語の昇順、POI が無ければ「なし」。実測分布: なし 205・飲食店 96・物販店 77・事務所 26・学校 22 ほか。
  - **街区は数でなく「あり/なし」**。これで**プロンプトに残る数字は place_id と「一辺100メートル」だけ**になり、個数記述(N4)の誘因が消える。
  - system を全面改稿: 冒頭で**三人称の客観描写**を宣言し一人称を名指しで禁止(第2回でも 8 件)/「45 字以内の**1文**・長さが最優先」/「まず区画の性格(層・街区の有無・多い店の種別 1 語)」→「そのあと**名前は最大 2 つまで**」/「書ききれないものは**数えず、触れない**」(「など」の代替行動を明示)/数を書かない/区画IDと広さを書かない。user 末尾にも同じ念押しを置く。
  - **長さの構造的保証**: プロンプト行に `"regex": "[^
]{10,88}"` を付ける(`fleet_gen` が vLLM `structured_outputs`(xgrammar)へ渡す・W17 で導入済み)。**88 字 = `estimate_tokens` で 44 tok ≤ `TOKEN_CAP` 45** なので、枠超えの文が物理的に出てこない。指示値 `CHAR_LIMIT`=45 は「そこを狙わせる」ための値で、88 は硬い天井。禁止語(「など」等)は正規表現に書けないので指示+検査器で見る。**文字数の数え方は xgrammar の Unicode 文字単位を前提=パイロット 3 件で要確認**(想定と違えば親へ報告)。
  - `Prompt.regex` は**空なら jsonl の行に出さない**。生成済みの W14 の行の形(=SHA)を動かさないため。
- **版**(第2回→第3回): W15 `prompts_sha256` 75c75ce2d59e89a1… → **dfd70b355ae730f1…**・`system_sha256` 963309344037aab3… → **ce31171b0675b3c2…**。W14 は**据え置き**(`prompts_sha256` 5923438d63ffd351…・`system_sha256` 247a39b391a9eca0…)。seed 20260909・temperature 0・repeat 2・thinking false も不変。W15 入力 431.8 tok 平均(第2回 433.8)。
- **履歴(全 3 回の SHA)**: W14 prompts b2ac72b4→5923438d(第2回で確定)/system 85c0dc6f→247a39b3。W15 prompts cebe004a→75c75ce2→**dfd70b35**/system ed83619d→96330934→**ce31171b**。
- **生成物の退避**: 第2回の W15 応答は `w15_responses.round2.jsonl`、凍結物は `round2_w15_*` へ改名(第1回は `round1_*`/`*.round1.jsonl`)。W14 は第2回の応答をそのまま使い、再 ingest 前の凍結物を `round2_w14_*` に控えてから上書きした。

**C5-b W17 第2回パイロット後の改版=構造化出力(`stage_version` 1.2.0・2026-09-09 深夜)**:
- **出力は日見出し形**(`d0` の見出し行 + `HHMM-HHMM <活動語> <場所語>` の 3 列)。行から曜日欄を外して 1 行あたりのトークンを削った(v2 は 1 行 ≈19 tok で 318/344 が `max_tokens` で切れた)。`max_tokens` 560 → **600**。
- **プロンプト行ごとに `regex` を持つ**(vLLM `structured_outputs.regex`・`fleet_gen` が送る)。`SchedPrompt.regex` は `to_json()` に `"regex"` として出る。**体ごとに違う**: 場所語の集合を `place_set(f, i)` が事実から決め(域外/職場/学校の有無)、来街種別は来訪日だけ活動行を許す。**事実にない場所語は文法で出せない**=D-W18 の捏造検査に相当する構造検査。母集団全体で相異なる regex は **35 本**・種別ごとの代表 SHA は世界データ構築仕様書 §4 の表。
- **パーサ**: `vocab.parse_line(line, day=None)` が日見出し形(3 列)と旧形式(4 列)の両方を読む。`parse_text` が見出し行で曜日を切り替える。`format_schedule` は日見出し形、旧形式は `format_schedule_flat`。
- **`w17_prompts.jsonl` は 1.49 GB**(regex を各行に持つ)。`fleet_gen` は全行を list に読むので **`--shard 0/8` … `7/8` に分けて流すことを推奨**(1 本 ≈190 MB)。
- **テスト**: `tests/build_sched/` は 123 → **183 本**(プロンプト/regex 73・パーサ 50・修復 31・取り込み 18・ローダ 11。うち 1 本が `slow`=実データ)。

**C5 W15 第3回 追補(build/lang・2026-09-09・親のパイロット結果)**:
- **xgrammar の regex は文字単位**と確定(親プローブ: 32 文字/92 バイトの出力が `[^
]{10,88}` を通過・`finish_reason=stop`)。`REGEX_MAX_CHARS`=88 は**そのまま**でよい(前節の「要確認」は解消)。
- **先頭の見出し語を正規化で落とす**: パイロット 3 件中 2 件が system の指示文「「見えるもの:」に続けて読まれる文として書く」の見出しを本文へ書き写した(「見えるもの: 地上に街区があり…」)。レンダラのテンプレ `B2.visible` が既に「見えるもの: 」を持つので、そのまま凍結すると**見出しが二重になる**。`normalize_generated` の手順に **5.** を挿入(引用符外しの後・句読点空白の前):
  - 除去対象 `_LEADING_HEADINGS`(自前・expedient)= 見えるもの/見える物/説明/区画の説明/静的な説明/区画の静的な説明/本文/出力/回答/答え/記述/描写/店頭表示/表示。**先頭にある場合だけ**・直後にコロン(全角/半角)・後続空白も落とす。
  - **無くなるまで繰り返す**(「見えるもの: 説明: …」を 1 回だけ落とすと 2 度目の正規化が動き `normalize_mismatch` で不合格になる)=**冪等**。`verify_one` が冪等性を検査する。
  - 文中の見出し語(「…、見えるもの: は書かない」)やコロンの無い「見えるものは特にない」は**触らない**。見出しだけの応答は `empty` で不合格。
  - **プロンプトは変えない**(第3回の本生成中のため)。凍結文はこの正規化後のバイト列なので、生成物はそのまま使える。
- **W14 への影響なし**を確認: 第2回の応答 2,337 件を新旧の正規化で再 ingest しても凍結 2,295 行・**差分 0 行**(見出しで始まる応答が 1 件も無い)。`fail_rate` 0.017972 も不変。

**C5 W14/W15 ゲートの母集団(build/lang・2026-09-09・親決定)**:
- **ゲートの母集団は「凍結した行」**。不合格になった応答の欠陥は `fail_rate_within_threshold` が一括で見るので、**個別の欠陥ゲートで二重に数えない**。根拠: 第3回の W15 は fail_rate **0.0154**(閾値 0.05)で合格しながら、`rep_byte_match_rate` 0.996154(rep 不一致 2 件)と `individual_word_violations` 3 だけで段階が落ちていた。**どの行も凍結されておらず**(不合格→レンダラは合成文へフォールバック)、凍結物の品質は保たれている。
- **ゲート名の変更**(`common.gate_rows`・W14/W15 共通): `rep_byte_match_rate`(期待 1.0)→ **`frozen_rep_byte_match_rate`**(期待 1.0・**合否**)+ `rep_byte_match_rate_all` / `rep_mismatch_count`(**報告のみ**)。W15 の `individual_word_violations`(期待 0)→ **`frozen_individual_word_violations`**(期待 0・合否)+ `individual_word_violations_all`(報告のみ)。W14 も同じ定義に揃えた(実測 1.0 / 0 なので結果は不変)。`w1x_gates.json` にも `rep_mismatch_count`・`rep_mismatch_ids`・`frozen_rep_byte_match_rate`・`individual_word_violations_all/frozen` を出す。
- **この 2 ゲートは pin(構造的な不変条件の釘付け)であって実測ではない**と明示する: `verify_one` が rep 不一致を `rep_mismatch` で、個体語を `I1/I2` で不合格にする以上、凍結行の一致率は必ず 1.0・個体語は必ず 0 になる。将来 `verify_one` を緩めたらここで落ちる、という保険。**実測の情報は `rep_byte_match_rate_all` / `rep_mismatch_count` / `individual_word_violations_all`** の側にある(CLAUDE.md の「同語反復ゲート」指摘への対応として、pin であることをコード docstring にも書いた)。
- **第3回 W15 の ingest 実測**: fail_rate **0.015385**(8/520)・凍結 **512**・tokens max 35 / mean 13.9 / chars max 70・`rep_byte_match_rate_all` 0.996154(不一致 2)。不合格 8 の理由 = rep_mismatch 2・I1_individual 3・A1_abbreviation 1・E3_imperative 1・N2+N5 1。**温度 0 + 構造化出力でも 2 セルが揺れた**(下記)。
- **rep 不一致の実体(親の記録用)**: `g-4_4_GL` rep0「見えるもの: 地上に街区があり、夜間営業の飲食店belami、Zarigzu cafeが並ぶ。」/ rep1「見えるもの: 地上に街区があり事務所が多い。夜間営業の飲食店belami、Zarigzu cafeが見える。」、`g-7_-4_GL` rep0「見えるもの: 地上に飲食店が集まり、学校と物販店が見られる。」/ rep1「見えるもの: 地上に飲食店が集まる街区、学校(8号館)、物販店(マルエツプチ)が見える。」。文の構造ごと違うので丸め誤差ではなく**バッチ非決定性**(温度 0 でも並行度・KV の状態で分岐する既知の現象)。

**C5 W14/W15 I1 偽陽性の修正(build/lang・2026-09-09・親承認)**: `check_individual_words` の I1(一人称・二人称の語)を **`allowed` に現れる語を除いた残り**に掛ける(`check_abbreviation` と同じ扱い)。POI 名の「**私**立青山学院中等部」「陳家**私**菜」で「私」が当たる偽陽性が第3回で 10 件(W14 7・W15 3・**すべて入力由来**)出たため。I2(`assert_no_agent_dependent_words`: 人ID・所持金・内受容)は**本文そのもの**に掛けたまま(入力で免罪しない)。併せて `INDIVIDUAL_WORDS` に W15 の system が名指しで禁じている「僕/ぼく/俺/おれ/我々/われわれ/私たち」を追加(入力由来の語は先に除くので「俺のフレンチ」型の店名は落ちない)。**再 ingest のみ・再生成なし・プロンプト不変**。効果: **W14 凍結 2,295 → 2,302(+7)**・fail_rate 0.017972 → **0.014976**、**W15 凍結 512 → 514(+2)**・fail_rate 0.015385 → **0.011538**。残る不合格は W14 35(too_long 30・E1 2・N1/N2/N7 各 1)・W15 6(rep_mismatch 2・A1 1・E3 1・I1 1・N2+N5 1)でいずれも真陽性。**未修正で親 PENDING へ**: W15 の `E3_imperative` 1 件(「見渡せる」が `perception/attention.py` の `IMPERATIVE_PATTERNS` の「渡せ」に語境界なしで一致)。知覚契約側の管轄なので触っていない。**現状の拒否は正しい挙動**(描画時に `strip_imperatives` がその文を落として本文が空になるため、凍結すると文面凍結が壊れる)。

**C6-b 検証ハーネス(`tests/c6`・`tools/c6`・2026-09-09)**:
- **部品**: `tools/c6/c6lib.py`(純関数=統計・場面抽出・採点・出力・記録クライアント)+ 実行器 6 本
  (`run_hash.py`=T3 の子プロセス / `t6_bit_reproduce.py` / `t7_distribution.py` /
  `metric_b_rerun.py` / `ablation1_fixed_vs_ranking.py` / `format_role_rates.py`)。
  全実行器が `--endpoints --world --agents --ticks --out`(+`--seed --model`)を受け、
  `<out>/<名前>.json` と `.md` を書く。新依存なし(numpy/httpx/pyarrow は既存)。
  `tools/c6` はパッケージにせず、各スクリプトが自分のディレクトリと `src` を `sys.path` へ足す
  (サーバーで `python tools/c6/xxx.py` と直接叩けるように)。`tests/c6/conftest.py` が同じ道を通す。
- **T3 の測り方(自前)**: 設計書は「スレッド 1/8/32 で同一結果」だが、**ラン時のエンジンに並列度の口は無い**
  (`prange`/`parallel=True` は `build.geo`/`build.vis` だけ・`engine.change_detect` の numba は
  nogil の逐次カーネル)。よって T3 = `NUMBA_NUM_THREADS`/`OMP_NUM_THREADS`/`MKL_NUM_THREADS` を
  **1 と 8** にした 2 プロセスで `run_hash.py` を回し checkpoint ハッシュを突き合わせる形にした
  (32 は同じ仕掛けで増やせるが CI 時間のため既定は 1/8=expedient)。
  「engine に `prange` が無いこと」自体をテストで釘付け(増えたら測り方を見直す合図)。
- **T5 は実データでは「種別層内」で判定する(親確認・09-09 追補/層2 再確認で格付け直し)**:
  W16 の `agent_id` は種別ごとに**まとまって**並ぶ(実測): 0-43,582 は**住民と従業者が交互**
  (住民 36,506・従業者 7,077)/43,583-43,587 住民/43,588-259,359 通勤(連続 215,772)/
  259,360-292,744 通学(連続 33,385)/292,745-312,744 定期来街(連続 20,000)/
  312,745-330,606 来街(連続 17,862)/330,607-388,750 は**来街と訪日が交互**
  (来街 40,740・訪日 17,404)/388,751-390,008 乗務(連続 1,258)/390,009-390,042 住民/
  390,043-390,066 指令(連続 24)。連続でない種別(住民・従業者・来街・訪日)も
  **その区間の中でしか出ない**ので、ID は種別の強い説明変数になる。層は `pop.kind` で取るので
  交互かどうかは扱いに影響しない。
  種別で起床の出方が違う(来街者はほぼ呼ばれない・通勤者は計画境界で呼ばれる)ため、
  **ID と起床回数の生の相関は種別構成の差**を拾う。W17 週次表が載った 09-09 以降、
  生の ρ は −0.13 まで動く(それ以前は −0.018)。T5(v1 の C-8)の検査対象は**処理順のバイアス**
  なので、実データは `c6lib.stratified_order_bias_report` で**種別を層に固定**し、層内で
  ID 順位との Spearman を取る。二層抽出(5,000 体)も種別順を保つので同じ扱い。
  合成個体は行が i.i.d. なので従来どおり生の相関(`order_bias_report`)でよい。
  - **主判定(3 量すべて)**: ①**呼数**で重み付けした層内 |ρ| の平均 ≤0.05
    (体数で重み付けると呼がほぼ 0 の来街者層が平均を薄める。重みは指標ごとに
    「その指標へ情報を寄せた呼数」= `selected_count`/`wake_count` は呼数、`mean_wake_tick` は
    値を持つ体数) ②**最大の層(通勤)単独** ≤0.05 ③**kind を統制した部分相関** |r| ≤0.05
    (層内で中心化した残差どうしの Pearson。層をまたいで同じ向きに乗るバイアスを 1 本で見る)。
  - **副判定**: 母集団反転の**符号反転** `|ρ_順 + ρ_逆| ≤ 0.05`(`c6lib.reversal_symmetry`)。
    処理順のバイアスは反転しても同じ向きに乗るので、符号が返れば構成の効果と言える。
  - **傍証(判定に使わない)**: 反転との KS/JSD。個体別呼数の**多重集合**の比較なので、
    **全個体に同じ向きで乗る処理順バイアスには構造的に無反応**(並べ替えても多重集合は同じ)。
  - **報告値**: 生の相関(種別構成を含む)。
  **層内の検出力**: 層内 ρ の SE ≈ 1/√(層内で呼ばれた体数)。最大層(通勤 2,346 体)でも
  24 tick で呼ばれるのは約 520 体=SE≈0.044 で閾値と同じ桁になり、`mean_wake_tick` の層内 ρ は
  seed ごとに −0.059/+0.049/+0.059 と**符号が飛ぶ**(実測)。そこで**母集団を固定して run seed を
  3 本回し、Fisher z 平均**(`c6lib.average_stratified_reports`)に閾値を当てる(expedient)。
  **実測(実データ 5,000 体×24 tick・3 seed 平均)**: ①呼数加重平均 |ρ| =
  mean_wake_tick 0.0438(w=830)/ selected_count 0.0179(w=833)/ wake_count 0.0176(w=5,454)、
  ②最大層 COMMUTER(n=2,346)= +0.0162 / +0.0015 / +0.0259、③部分相関 = +0.0284 / +0.0057 /
  +0.0272 → **主判定 合格**。副判定=反転の符号残差 selected_count 0.0004・
  mean_wake_tick 0.0235 → 合格。傍証=KS D=0.0004・p=1.000・JSD=0.00010 bits。
  報告値の生 ρ は selected_count −0.1311・wake_count −0.1303(反転で +0.1314 へ符号が返る)。
  なお指令(n=24・呼 4)のような小さい層は層内 ρ が ±0.25 まで振れるが、呼数重みなので
  加重平均への寄与は 0.001 級(層別の値は表に出して読めるようにしてある)。
- **T5 の 3 量と検出力(自前)**: 閾値 **|r| ≤ 0.05 は設計書 §1.4 の逐語**。測る量は
  ①アービタで選ばれた回数 ②呼ばれた tick の平均(いずれも `RecordingLLM` が控える)
  ③起床(候補)回数=**`budget` を外したラン**の呼数で代用(expedient)。
  Pearson と Spearman の両方を出す。**検出力**: |r| の SE ≈ 1/√呼数なので、
  2,000 体×24 tick(呼 333)では seed 次第で ±0.16 まで揺れて判定にならない。
  標準ケースは **5,000 体 × 24 tick × 3 seed**(呼 833・SE≈0.035)とし、呼 <400 なら判定しない。
  ID 写像の反転対照は W16 母集団の行を逆順にした `Population` で回す(判定は上記の格付けどおり
  =層内 3 条件が主・符号反転が副・KS/JSD は傍証)。
- **場面抽出の規則(自前・指標B)**: 「答えが決まる場面」= **駆動因が 1 つ以上ある場面**
  (①B5 内受容が空文言でない=閾値割れが描かれている ②B6 起床理由が計画境界
  ③B6 に「…で失敗しました」がある)。品質プローブv0 の mid 層(閉店間際・段階・条例=
  駆動因を必ず 1 つ入れた場面)の実データ版で、文献根拠は無い。
  制約種は `agents.state.RESULT_TEXT` の失敗語 18 種を全部分類したうえで、
  **事前登録の 5 種= 営業時間外/所持金不足/満員/移動不能(到達不能)/会話拒否(断られた)**。
  契約書 §8 は「5 種」としか書かないので**どの 5 種かは本ハーネスの選択**(`--kinds` で差し替え可)。
  抽出は `sha256(agent_id,tick,wake_class,prompt_hash)` 昇順の決定論、制約枠と「決まる場面」枠は
  重複させない。違反判定は**制約種→禁じ手 1 語**の固定表(営業時間外/所持金不足/在庫切れ→購入、
  満員/運賃不足/列車なし→乗車、止まらない→降車、到達不能→移動、断られた/会話中/去った→会話、
  寝る場所なし→就寝)。表に無い種(対象を特定できない等)は違反にしない。
- **帰無参照の定義(自前)**: 契約書 §8「同分布 2 標本のブートストラップ」を、
  **2 標本を混ぜた分布から同じ標本数を多項分布で 2 本引いた JSD の分位点**(既定 2,000 反復)
  として実装した。指標B ではこれに加えて **同モデル seed 違いの 1 パス**も実測の帰無として出す
  (親指示)。Δ違反率の CI は場面を復元抽出する対応ありブートストラップ(4,000 反復)。
  JSD の単位は bits(品質プローブv0 と同じ)。χ² は自前の不完全ガンマ(scipy 非依存)。
- **親判断待ち(C6-b で判明したもの)**:
  1. **T7 の合格線が無い(D-25)**。§1.3 の「JSD ≤ 帰無95th」は**指標B(v0 vs v1)**の閾値であり、
     「seed 違い 2 ラン」の合否線は設計書に無い(2 ランは定義上同分布=帰無そのものが期待値)。
     `t7_distribution.py` は JSD・帰無 p50/p95・χ² p・呼数比を**報告値**として出し、合否を付けない。
  2. **ablation ① の切替口が実装されていない**。`perception.channels.BudgetMode.SINGLE_RANKING` は
     Enum の枠だけで、`Renderer` は `self.budget_mode` を保持するのみ(どこでも読んでいない)。
     `ablation1_fixed_vs_ranking.py --probe-only` の実測 = **24 場面すべてバイト同一(差 0)**。
     `run_day`/CLI にもモードのフラグは無く、レンダラは `run_day` 内部で `AgentState` を作ってから
     組むので外から差し替える口も無い。**単一ランキングの実装と run_day/CLI のフラグ**が要る。
  3. **録画テープから場面を再呼できない**。テープの共有ブロックは
     `engine.llm_bridge.SHARED_BLOCK_IDS` = B0-B4b で、**B5/B6(個体固有)は intern されない**。
     指標B は `RecordingLLM`(`llm=` を包む)が出す `scenes.jsonl`(プロンプト全文)を使う形にした。
     テープ列に個体ブロックを足すかは親判断。なお **`fleet=` を渡したランは `llm=` を通らない**ので、
     実 LLM 走行中の全文採取の口は現状ない(収集は mock ランで行う)。
  4. **会話相手の選び方に ID 順バイアスがある**。`engine.commit.pair_partners` は docstring どおり
     「セル内の**最小 id** を相手にする」(C3 の expedient)。240 tick・予算無制限の診断ランで
     **会話ターン起床(class 0)だけ r ≈ −0.14**(class 2 は +0.006・class 3 は −0.027)。
     24 step のスモークでは会話成立が数件しか出ないため T5 の閾値には掛からず**合格する**が、
     v1 の C-8(ID 順バイアス)と同種の穴。修正するかは親判断
     (`test_t5_conversation_partner_rule_is_the_known_min_id_expedient` が現状の規則を釘付け)。
  5. **指標B の在庫が足りない**(mock 収集・実データ 5,000 体×1 日 = 50,000 呼の実測):
     営業時間外 1,375・到達不能 126 は足りるが、**所持金不足 0・満員 0・断られた 0**。
     実際に多いのは 対象を特定できない 6,862(mock が「対象」を出さないため)・
     その駅には止まらない 3,708・列車なし 3,604・相手が会話中 762・寝る場所がない 696。
     事前登録の 5 種を維持するなら**呼を実 LLM にする/ラン長を伸ばす**、
     維持しないなら 5 種の差し替えが要る(`--kinds`)。在庫表は全 18 種を出す。
- **L6 の検査**: `tests/c6/_fake_vllm.py`(プロセス内の最小 OpenAI 互換面・非ストリーミング)へ
  24step スモークを流し、`fleet_peak_in_flight_r*` と**サーバー側で数えた同時実行数**の両方が
  L6(64/GPU)以下であることを見る(実サーバーには繋がない)。艦隊そのものの挙動
  (SSE・再試行・タイムアウト)は `tests/llm/test_fleet.py` に任せて重複させない。
  親がサーバーで回した診断行は `SHIBUYA_C6_FLEET_COUNTERS`(JSON パス)で渡すと同じ検査が走る。
- **書式エラー率の判定**: 率 ≤0.10 **かつ n ≥ 59**(B11 の標本数)を満たしたときだけ「合格」と書く。
  n<59 は「標本不足」。サブ Q のラベル別名許容(`llm.parser`)が入ったので、**実効を主・厳密を併記**
  (親判断 **D-28**): 実効=C6 別名を許した `ParseResult.format_ok`(再生成の要否と同じ基準)、
  厳密=C6 以前の別名表だけで見た `strict_format_ok`(B11 n=59 と地続き)。
  `alias_used` の率と表層の内訳も出す。**未定義行動率は段0 辞書
  (`llm.undefined.map_synonym`)で救えなかった分だけ**を数え、救えた分は
  `dictionary_mapped_rate` に分けて行動分布では**写像先の契約語**として数える
  (エンジンの `UndefinedActionRegistry.observe` と同じ扱い)。
  役割語率は `llm.contract.is_role_action` で数え、受入表には
  §9.1 が名指しする 5 語(補充・開閉店・発車・停車・指示)を個別行で出す。
- **テスト**: `tests/c6` は **96 本**(T3 4・T5 8・T9 5・L4/L6 8・c6lib と各ツールの純関数 71)。
  実データ/長地平は `@pytest.mark.slow`、実資産が無い環境は skipif。
  ツール 3 本(T6/T7/書式・役割語)は偽艦隊 2 本に対する端から端までの実行も確認済み
  (`route=cli.run(fleet=…)`・`fleet_accounted=fleet_calls`)。

**C6 パーサ許容(`llm/parser`・`llm/undefined`・2026-09-09)**: 初回実 LLM スモーク(5,000 体×24 tick・Qwen3-8B INT8・温度 0・呼 833)の **書式エラー率 0.176**(受入 ≤0.10)・書式再生成 154/833・未定義行動 43 が根拠。親がテープで確認した中身=モデルは 2 行形をほぼ守るが **①ラベルを言い換える**(「対象:」の代わりに「目的地:」「目的:」)**②語彙外の行動語**(探索・観察・調査・探す・調べる)が混じる。**設計書の決定項は書き換えていない**(行動契約書 §1 の 2 行形・§2 の 12 語+役割語は不変)。①は**パーサ側の許容**、②は §7 段 0「辞書写像」の**枠内での表の拡張**として受ける。

- **ラベル別名表(C6 追加分・`parser.LABEL_ALIASES_C6`・expedient)**

| 追加した表層 | 正準ラベル | 根拠 |
|---|---|---|
| 目的地 / 目的 | 対象 | スモークのテープに実在(最多) |
| 場所 / 対象物 | 対象 | 同系の言い換え(予防・未実測) |
| コメント / セリフ / 台詞 | ひと言 | 同上(`一言`/`ひとこと`/`発話` は C6 以前から) |
| 根拠 / わけ | 理由 | 同上 |
| アクション / 行為 | 行動 | 同上 |

  C6 以前の別名は `parser.LABEL_ALIASES_V0` として**凍結**(理由/reason・行動/action・対象/行き先/行先/相手/target/destination・ひと言/一言/ひとこと/発話/utterance/comment)。`LABEL_ALIASES = V0 ∪ C6`。
  吸収する表記ゆれ: 全角/半角コロン・ラベル前後の空白(全角空白を含む)・`**`/`[]`/`【】` の飾り・**行末の空白**・**行末の literal `\n`**(本文に実改行が無いときだけ改行として読み、値の末尾に残ったものは落とす=テープに `…ため  \n行動:` の形で出た)。

- **二重指標(受入の分母を動かさないための措置)**: `ParseResult.format_ok` は C6 別名を含む**寛容**判定(=**書式再生成の要否**はこちらで決まる)/`ParseResult.strict_format_ok` は `LABEL_ALIASES_V0` だけで走査した**従来定義**(=**受入の「書式エラー率」はこちらで数え続ける**)。C6 別名を 1 つも使っていない応答では両者は必ず一致する(その場合は 2 回目の走査をしない短絡実装)。辞書写像・役割語の扱いは従来どおり両指標の外(語彙の問題であって書式の問題ではない)。

- **段 0 辞書写像の追加(`undefined.SYNONYMS_C6`)**: `SYNONYM_TABLE_VERSION` を `undefined-synonyms-v0` → **`undefined-synonyms-v1`**。方針は既存表のアンカー(「様子を見る」→待機)に合わせ、**移動を伴う探索 → 移動**・**その場の観察/確認 → 待機**(待機=行動契約書 §2 共通必須事項③「失敗しない行動」)。**対象は付けない**(`TARGET_HINTS` を足さない=対象の決定はエンジンの仕事)。

| 追加した表層 | 写像先 | 備考 |
|---|---|---|
| 探す / 探し / 探索 / 探る | 移動 | `探し` は「探して/探した/探しに行く」の部分一致の受け皿 |
| 見回る / 歩き回る / うろつく / 散策 | 移動 | 同方針の近縁語(予防・未実測) |
| 観察 / 眺める / 見物 / 見学 | 待機 | スモークで実在=観察 |
| 確認 / 調べる / 調べ / 調査 / チェック | 待機 | スモークで実在=調査・調べる |

- **診断フィールド(実装済み・エンジン側への結線は親)**

| 置き場 | 名前 | 意味 |
|---|---|---|
| `llm.parser.ParseResult` | `strict_format_ok` | 従来定義の書式順守(**受入表はこれで数える**) |
| 同 | `alias_used`(別名プロパティ `label_alias_used`) | 正準以外のラベル表層を使ったか |
| 同 | `alias_surfaces` | 使った表層(検出順・重複なし)=どの言い換えが多いかの内訳 |
| 同 | `dictionary_mapped` | 段 0 の写像を載せたか(`ParseResult.with_dictionary_mapping(word)` を通したときだけ真) |
| `llm.undefined.UndefinedOutcome` | `action_from_dictionary` | 段 0 の辞書写像で契約語彙が入ったか(段 4 の判例参照は含めない) |
| `llm.undefined.UndefinedActionRegistry` | `n_dictionary_mapped` / `counters()["dictionary_mapped"]` | 段 0 で救えた件数 |

  現状 `engine/run.py` の `parse_error_rate` と `llm/fleet.py` の `n_parse_errors` は `format_ok` を数えている(=別名を許した後の値)。**受入表の「書式エラー率」を従来定義で出すには `strict_format_ok` を集計する結線が要る**(engine/fleet は別サブ作業中のため本作業では触っていない)。

- **昇格条件 / ablation**: 別名表・辞書追加はともに **expedient**。昇格条件=**テンプレ v1.1 で「対象:」固定を強調**して同じスモークを再測し、(a) `alias_used` 率が十分下がる(ラベル言い換えがテンプレで消える)なら別名表は**保険**として残し受入は `strict_format_ok` のみで判定、(b) 下がらないなら別名は**モデルの安定した挙動**として扱い、受入指標の定義そのものを親が再決定する。`alias_surfaces` と `dictionary_mapped` の内訳を再測の比較量にする。

**C6 パーサ許容 第2弾(位置引数・辞書 v2・2026-09-09 夕)**: 根拠=`--fleet-debug-dir`(60 tick・2,083 呼・失敗 531)の内訳 **`missing_label:対象` 226 / `対象+ひと言` 78 / `ひと言` 6**(=ラベルを省いて**値だけを契約の順序で並べる**「行動: 移動 なし なし」型)・**`unknown_action_word` 96**(探索 50・通勤 16・観察 9・調査 ほか)・**ラベル別名 125**(目的/目的地)。第1弾と同じく決定項は不変。

- **位置引数の許容(`parser._fill_positional`・expedient)**: 行動契約書 §1 で 2 行目の**欄順は固定**(行動→対象→ひと言)なので、欠けたラベルの値を「**直前に在る欄の余りトークン**」として拾う。

| 入力の形 | 読み | 備考 |
|---|---|---|
| `行動: <語> <v1> <v2…>` | 対象=v1・ひと言=v2 以降 | ひと言は残り全部を連結(自由文) |
| `行動: <語> <v1> ひと言: …` | 対象=v1 | 対象だけ欠落の混在形 |
| `行動: <語> 対象: <t1> <t2…>` | ひと言=t2 以降 | ひと言が対象の値に押し込まれた形 |
| `行動: <語> <v1>`(v2 なし) | ひと言=**なし**(§1 の既定値) | `errors` に `comment_defaulted` |

  安全弁: **行動ラベルが在り、行動語が先頭トークンにある**ときだけ働く(「行動: すぐに 移動 なし」型は触らない)。余りトークンが 1 つも無ければ何もしない(=欄落ちは欄落ちのまま)。値は自由文なので中身では落とさない(切り詰めは従来どおり)。`raw_action` は**語彙語だけ**に詰め直す(「移動 なし」→「移動」=§7 段 0 が正しく引ける)。判定は `format_ok=True` / `strict_format_ok=False` / `positional_used=True`、`alias_surfaces` に `"positional"`、`errors` に生の欠落(`missing_label:*`)と回収(`positional:*`)の**両方**を残す。`alias_used` はラベル表層の話なので**位置引数では立てない**。

- **実効/厳密の定義(新旧)**

| 指標 | C6 以前 | 現在 | 使い道 |
|---|---|---|---|
| `format_ok`(実効) | 4 ラベル(v0 別名可)が揃い行動欄から語彙語が取れた | 左に **C6 別名**と**位置引数**の回収を加えた | **書式再生成の要否**・エンジンが intent にできるか |
| `strict_format_ok`(厳密) | (無し。当時の `format_ok` がこれ) | v0 別名のみで走査・**位置引数は使わない** | **受入の「書式エラー率」**(0.176 と同じ定義で比較) |
| 語彙外(`unknown_action_word`) | `format_ok=False` | **`format_ok=False` のまま**(親決定 09-09) | 段 0 で救えるかは `dictionary_candidate` で別に見る |

- **段 0 辞書 v2**(`SYNONYM_TABLE_VERSION` を `undefined-synonyms-v1` → **`v2`**): 通勤 / 通学 / 出勤 / 退勤 / 出社 / 登校 / 進入 → **移動**。`TARGET_HINTS` は足さない(職場・学校セルの印は未定義=**親判断待ち**。`home` に相当する仕組みは要るか)。**`通報`・`退去`・`購入` は §2.1 の 12 語そのもの**なので辞書には入れない(語彙一致で通る)——テストで「辞書のキーが語彙語と衝突しない」を釘付け。

- **追加の診断フィールド**: `ParseResult.positional_used`(位置で読んだか)/ `ParseResult.dictionary_candidate`(語彙外のとき §7 段 0 の辞書で**救える語**=写像先・救えなければ `None`)。後者は**初回判定でも数えられる**ので、`llm/fleet.py` の書式再生成の判定を「語彙外でも `dictionary_candidate` があるなら再生成しない」に変えられる(結線は親/サブ O)。写像そのもの(呼数・計数・段 1〜4・段 4 判例)は従来どおり `UndefinedActionRegistry` の仕事で、パーサは**表を引くだけ**(段 4 判例は見ない)。

- **未処理(親判断)**: 「`行動: 待機 対象: なし`(ひと言が丸ごと無く余りトークンも無い)」は**書式エラーのまま**(実測 6 件)。位置の証拠が無い欄落ちまで既定値で埋めると 4 欄要求が実質 3 欄になるため保守側に倒した。

- **テスト**: `tests/llm/test_parser.py` **68 本**(24→52→68)・`tests/llm/test_undefined.py` **48 本**(18→38→48)=`tests/llm` 124→**202 本**。スモークの実例 3 本・位置引数の 4 形+併用(別名×位置)・陰性(ラベル欠落・3 行+散文・語彙外かつ辞書外・行動語が先頭トークンに無い・余りトークン無し)・v0 別名は `strict_format_ok` 真のまま・全角コロン/空白/行末 literal `\n`・`dictionary_candidate` の陽性/陰性・性質テスト 1 本(**ラベルの順序入替と表層の選び方を変えても読み取りが変わらない**・300 例)。

**C6 ablation①(`perception/renderer`・`perception/channels`・`engine/run`・`cli`・2026-09-09)で導入した自前規約(追記のみ・決定項は変更していない)**:
知覚契約書 §3.2 は「固定枠 vs **同一総トークンの単一ランキング(最近性×重要度×関連性)**」の ablation を**義務**と書き、§8 第1陣①・§9 完了条件・§10.3 卒業条件(=単一ランキングと行動分布・違反率が同等)がこれを指す。C6-b の実測では `BudgetMode.SINGLE_RANKING` が Enum の枠だけで **24 場面すべてバイト同一(no-op)**=測定不成立だった。本作業はその**切替の実装**であり、契約書の決定項(上限表・ブロック順・テンプレ)は 1 行も書き換えていない(`template_sha256=161fe181bc325f00` 不変)。

- **切替口**: `Renderer(..., budget_mode=BudgetMode.FIXED_SLOTS|SINGLE_RANKING)`(`"fixed"`/`"ranking"` の語も `BudgetMode.parse` で受ける)→ `run_day(budget_mode=…)` → `python -m shibuya.cli --budget-mode {fixed,ranking}`(既定 `fixed`=現行の描画と 1 バイトも変わらない)。腕は `RunResult.budget_mode` と **run manifest 欄 `budget_mode`** に出る(`fixed_slots`/`single_ranking`)。`renderer=` を明示注入したランではフラグは効かない(注入側が持つ)。
- **単一ランキングの定義(自前・4 点)**:
  1. **池の単位**=§2.2 の予算グループ。セル依存(B2+B4+B4b)と個体(B5)の 2 本。共有静的(B0/B1/B3)は**両腕で同一バイト**(prefix キャッシュを壊さない)。
  2. **池の総額**=そのブロック群の**チャネル上限の総和**(セル 150+60+40=**250**・個体 100+40+65+15=**220**)。§3.2 の「同一総トークン」をこの値と読んだ。偶然ではなくグループ予算と一致する(セル 250・個体 300−B6 80=220)。
  3. **順位**=`attention.rank_by_saliency` そのもの(§4 のフロア付き対数加算 `Σ wᵢ·ln(floor+xᵢ)`・視角=サイズ/距離)。契約書の語への写像は **重要度←視角×局所コントラスト・最近性←動き・関連性←逸脱度**(**expedient**。契約書は 3 語を並べるだけで式も重みも与えない。§4 の顕著性式を再利用したのは、知覚側に別の順位式を 2 本持たせないため)。
  4. **採り方**=順位順に、行の途中で切らずに、入らなければ**そこで打ち切る**(`channels.take_within_pool`=固定枠 `truncate_lines` と同じ規約)。**チャネル別の上限 tok も件数上限(`max_items`)も使わない**のが腕の差。
- **チャネル既定素性 `channels.RANKING_PRIORS`(全て expedient)**: (size_m, distance_m, contrast, motion, deviance) = B2.ground(4,2,.5,0,0)/B2.visible(6,20,.5,.1,0)/B2.signage(2,12,.8,.2,0)/B2.landmark(25,100,.4,0,0)/B4.density(20,15,.3,.6,0)/B4.noise(20,15,.2,.2,0)/B4.salient(1.7,12,.5,.9,1.0)/B4b.near(2,6,.5,.3,.2)/B5.near_person(1.7,**実測距離**,.5,.7,0)/B5.intero(1,1,.6,0,**閾値超過度**)/B5.self(1,1,.4,.1,0)/B5.watched(1.7,5,.5,.5,.5)。**非視覚チャネル(内受容・自己状態)は「視角=1.0」を内的信号の既定に置いた**(§4 の顕著性は視覚の式で、非視覚の合成規則は契約書にない)。実測がある 2 項目だけ上書きする(近接人物=同一セル在席者の実距離[m]・内受容=`(値−4)/(10−4)`)。既定素性のスコア表は `renderer.RANKING_PRIOR_SCORES`(起動時 1 回)。
- **同点処理**: `rank_by_saliency` の `np.lexsort((ids, -score))`= スコア降順→**`item_id` 昇順**(§2.4 ②)。`item_id` は `"<channel_id>#<3桁の入力内順位>"` なので、同スコアではチャネル id 昇順→チャネル内の元の順(可視視点数の降順など資産側で確定済みの順)になる。乱数は 1 つも引かない。
- **行の並び**: ブロック内は**チャネルの最上位項目のスコア降順**(同点は channel_id 昇順)。1 チャネル=1 行(`B5.self` だけ 2 行)なので、これが「単一ランキングの順序」そのもの。**採った項目が無いチャネル**(空文言を出す行)は既定素性のスコアで並べる。チャネルでない構造行(`B2.place`=現在地)は**常に先頭**。§2.2 の**ブロック順(B0→B6)は両腕で不変**(池はブロックをまたぐが、行はブロックの中に留まる=prefix・ハッシュ三役・グループ会計を壊さないための自前の線引き。**ブロックの壁も外す腕は作っていない=親判断待ち**)。
- **凍結文(W14/W15)の扱い**: 固定枠と同じ。W15 のセル静的文は `B2.visible` の**1 項目**として(在れば合成の可視物リストを置換して)池に入り、W14 の看板本文は `B2.signage` の**1 項目**として入る。どちらも命令文除去は先に掛かる(憲法6・多重防御)。凍結文が池から落ちればその行は空文言になる(文面の書き換えはしない)。
- **群予算の担保**: 池の会計はチャネル**内容**のトークンだけを見る(固定枠と同じ)ので、ブロックラベル等の固定オーバーヘッドが乗った描画バイトが §2.2 のグループ予算を超えることがありうる。超えていたら**順位の最下位から 1 件ずつ落として組み直す**(`_pool_render` の収束ループ・候補件数が上限)。これで `strict_group_budget` の例外は構造的に起きない。逐次ループ宣言(P4)は候補件数ぶん(1 セル/1 個体で十数件)で**個体数・セル数に比例しない**。
- **ablation の対象外(両腕で同じもの)**: 近接 k の密度逓減 3/2/1 と知人常掲(§3 人物④=別 ablation)・注意ゲート段0-3(§4)・p_notice(§3.1)・正規化規約9項・テンプレ本体と `template_sha256`・B0/B1/B3・ブロック順・§2.4 ⑧(**両腕で機械検査**)。
- **副作用(腕を測るときの注意)**: 単一ランキングでは B4 の内容が B2 の採否を動かすので、セル依存ブロックのキャッシュ鍵が固定枠の `(セル)` から **`(セル, B4 欄ハッシュ)`** になる(=prefix 再利用率が下がる方向)。診断行の `cache_hit_rate` は腕どうしで直接比べない。`truncation_count` も同様(固定枠はキャッシュ**ミス時だけ**切り詰め記録を積むのに対し、単一ランキングは**描画のたびに**チャネル別の記録を返す=分母が違う)。`prefix_key` も腕をまたぐと一致しない(**同じ腕の中では同セル同 tick で一致**)。
- **感度試験としての位置づけ**: §10.3 の卒業条件は「単一ランキングと**行動分布・違反率が同等**」。同等なら固定枠(E 等級 約130 tok)は「結果を駆動していない」証明が立ち expedient のまま残せる。差が出たら固定枠は**結果を駆動する設計判断**なので、上限表の根拠づけか単一ランキングへの乗り換えを親が決める。測定は `tools/c6/ablation1_fixed_vs_ranking.py`(①切替口の実在確認=レンダラ単体・②24step スモーク 2 構成の行動分布 JSD)。**mock ランでは腕の差は出ない**(`MockLLM` はプロンプト本文を読まないので、300 体×30 tick の 2 腕で `final_hash` も呼数も一致した=実測)。ablation ① の②は**実 LLM(艦隊)でしか測れない**。
- **テスト**: `tests/perception/test_ablation1.py` **25 本**(既定=固定枠の golden 指紋釘付け・切替が no-op でないこと・両腕で群予算・多セル多個体でも予算・固定枠が切る場面で差(件数枠 B4.salient 2→12・トークン枠 B5.near_person 27→39)・近接人物が距離順・§2.4 ⑧ が両腕で成立・共有静的は両腕同一・決定論 2 回・キャッシュ・池の総額=固定枠の総和・`BudgetMode.parse`・全チャネルに既定素性・`run_day`/`cli.run`/`--budget-mode` と manifest 欄・偽 vLLM 2 本に対するツールの端から端まで)。`tests/c6/test_c6lib_aggregate.py` の no-op 期待は**反転**した(C6-b が「実装が入ったら落ちる=更新の合図」と書いていた 1 本)。
- **親判断待ち**: (1) 順位式を契約書の語(最近性×重要度×関連性)どおりに**別式**として実装するか(最近性は描画側に信号が無い=エンジンからの受け渡しが要る)。上記の写像は §4 の顕著性の再利用であって、契約書の 3 語の逐語実装ではない。(2) **ブロックの壁も外す腕**(1 本の平坦なランキングとして B2/B4/B4b を混ぜて出す)を作るか。(3) `tools/c6/ablation1_fixed_vs_ranking.py` の②(24step スモーク 2 構成)は**腕にモードを渡していない**(`run_arm` が `c6lib.run_smoke(..., extra={"budget_mode": tag})` を渡せば通る=1 行)。本作業は編集範囲外なので触っていない。現状 ② は 2 本とも `fixed` を回す。

**C5-b W17 本番第1回後の改版=raking 予算の適応化(2026-09-10)**:
- 本番 390,067 呼の ingest で **修正率 0.2117 > 0.20 = FAIL**(修復だけで 9.58% + 固定 12% の raking)。**設計ゲートは動かさず** raking の行数予算を適応にした。
- `rake(..., budget_rows=…)` を追加し、`ingest()` が **`max(0, ADAPTIVE_MODIFIED_TARGET(0.19) × n_considered − 修復ぶんの修正)`** を渡す。予算は**集計値だけから決まる純関数**なので決定論は維持。予算 0 なら raking は 1 行も動かさない(JSD は前後同値で報告)。`RAKE_MAX_FRAC=0.12` は固定予算の ablation 用として残す。
- 再 ingest(103 s)で**全ゲート PASS**: modified_rate **0.187104**(旧 0.2117)・jsd_max_after 0.421132(旧 0.401=固定 12% 時)・raking n_moved 1,188,863(予算 1,188,877)。**JSD +0.020 と引き換えにゲートを通す**のが感度試験の結果。数表は世界データ構築仕様書 §4 の同名節。
- **修正率の分母**の文言を実装に合わせて訂正(層2 軽-3・実装は不変): 分母は「応答が使えた体=パースできた活動数/使えなかった体=骸格の活動数」で、**修復が足した活動は分母に入らない**(分子だけ)。
- **テスト**: `tests/build_sched/` は 183 → **192 本**(適応予算 9 本: 明示予算の上限・予算 0 で raking なし・負の予算は 0 に丸める・修復率を 6 通り振って不変条件・固定予算との ablation)。

**C6 被招待の提示(`perception/renderer`・`engine/llm_bridge`・`engine/run`・2026-09-09)で導入した自前規約(追記のみ・決定項は変更していない)**:
知覚契約書 §6 は起床条件に**(ii) 被招待**を挙げるが、B6(起床理由・直前の結果)に被招待の行が無く、**被招待は「誰に誘われたか」をプロンプト上で知らされていなかった**。承諾は行動契約書 §1-2 の対象スロットで「行動: 会話 **対象: 招待者**」と名指す規則(`engine.run._settle_pending_invites`)なので、名前が届かなければ承諾しようがない(サブ O 実測: mock 1 日で招待 1,114・承諾 57・拒否 582・期限切れ 471)。**可否の答えは(1)=既存スロットで表せた**: `B6.wake` は `[B6 起床] {reason}` で、レンダラは前から `wake_reason: int | str` を受ける(文言そのものを渡せる)。よって**テンプレ本体(`TEMPLATES`/`WAKE_REASON_TEXT`)には 1 行も足していない**=`template_sha256=161fe181bc325f00` 不変。v1.1 delta は不要。

- **文面(`renderer.INVITE_REASON`・expedient)**: 「`{person}`があなたに話しかけました。応じるなら 行動: 会話 対象: `{person}`、応じないなら別の行動を選びます。」定数は **`renderer.py` 側**に置く(`RESULT_OPTIONS`「いま可能3語」・`RESULT_TEXT` と同じ扱い=凍結 SHA の payload の外)。契約書は起床条件(ii)を列挙するだけで文面を与えないので**文面は自前**。承諾側だけを書くと誘導になるため、**応じない側の句を必ず併記**する(中立化。ablation 候補)。
- **人 ID の表層 `renderer.person_word`**= `P-<id>`。`B5.near_person` の `P-<id>(未知/知人)` と**同じ表層**で、`llm.contract._PERSON_RE` がそのまま読む(テストでパーサに通して招待者 id に戻ることを固定)。
- **起床条件では絞らない(自前・実測が根拠)**: `_settle_pending_invites` は**その tick に答えた全員**から返事待ちを拾うので、被招待が会話ターン以外(一般活動など)で起きた呼も承諾/拒否として消費される。`WakeCondition.CONVERSATION_TURN` に限ると招待文が載る呼が **262 招待中 4 件**しか出なかった(200 体・600 tick 実測)。よって `engine.run._inviter_of` は**返事待ちがあるかだけ**で判定する(話者は返事待ちを持たないので `pending_inviter_of` が -1 を返し、自然に切り分かる)。文面は「話しかけました」という**事実**の提示で、「〜のため起床しました」とは書かない(起床理由の詐称にならない書き方)。
- **結線(最小差分)**: `Renderer.render(..., inviter: int | None = None)` → `_b6` の起床行のみ差し替え。`engine.llm_bridge` の `Renderer` Protocol・`StubRenderer`・`PerceptionRendererAdapter`・`LLMBridge.call` に `inviter: int = -1` を足す(**-1 は描画 1 バイト不変**。`StubRenderer` は受け取るだけで使わない=テープ鍵を動かさない)。`engine.run` は同期経路と艦隊経路の 2 か所で `_inviter_of(conv, a, cond)` を渡す。
- **規約⑧・prefix**: B6 は**個体ブロック**なので B0-B4b は 1 バイトも動かない(`prefix_key` も同値)。B5 も動かない。両 `budget_mode`(固定枠/単一ランキング)で成立をテストで固定。
- **トークン増分**: B6 は **36 → 53 tok(+17)**(合成の標準場面)。最悪ケース実測(6 桁 id・同セル 80 人が全員知人・所持金不足の失敗理由つき)で **B6 79/80 tok**・個体群は固定枠 262 / 単一ランキング 294(上限 300)。単一ランキングは B5 の池が B6 の実測ぶんを差し引くので**構造的に 300 を超えない**が、固定枠は上限表の総和(220)+ラベルが積み上がるため**余裕が薄い**(親判断待ち)。
- **効果の測り方(重要)**: **mock ランでは測れない**。`MockLLM.render` は `(master_seed, tick, agent_id, wake_class)` の抽選と `request.targets` しか見ず、**プロンプト本文を読まない**(知覚アダプタは `targets` を出さないので mock の対象は常に「なし」=`conv_target_named` 0)。実測: `cli --agents 5000 --seed 1 --world data/world/v2` は本修正の前後で **`final_hash` まで完全一致**(`d5d793375a9d322e…`)、会話も 招待 1,149 / 承諾 48 / 拒否 604 / 期限切れ 490 で不変。**プロンプトを読む LLM でだけ効く**ので、A/B は「同じ LLM・同じ世界・描画だけ実レンダラ vs `renderer="stub"`」で測る: **招待 101 → 承諾 87 / 拒否 1**(招待文が載った呼 100)対 **招待 147 → 承諾 0 / 拒否 147**(`tests/perception/test_b6_invite.py` が毎回この行を出す)。
- **engine 側に残る目詰まり(perception の管轄外・親判断)**: 既定の L4 按分予算では、200 体 600 tick で **招待 262 中 248 が期限切れ**(被招待が呼ばれる前に TTL が切れる)。上の A/B は `budget=n_agents` で呼の枯渇を外して測っている。5,000 体の実ランでも期限切れ 490/1,149(43%)。招待 TTL とアービタの優先度(`EventClass.CONVERSATION` は最優先クラスだが不応期・按分に負ける)は**会話の成立率を直接決める**ので、実 LLM スモークの前に engine 側で見直す価値がある。
- **テスト**: `tests/perception/test_b6_invite.py` **11 本**(招待者が出る/招待なしはバイト不変/テンプレ SHA と `TEMPLATES` に足していないこと/規約⑧ と B5 と `prefix_key` 不変(両モード)/予算(両モード)/決定論とパーサ往復/`wake_reason` より優先/`_inviter_of` の切り分け 4 ケース/端から端まで A/B)。
- **親判断待ち**: (1) 承諾の書き方(「行動: 会話 対象: P-x」)を B6 に出すこと自体が**誘導**でないか(中立句で緩和したが、ablation 第2陣に「承諾の書き方あり/なし」を足すのが素直)。(2) 固定枠での個体群予算の余裕(B6 が 79/80 まで伸びうる)。(3) 招待 TTL・アービタ(上記)。

**C7 受入計器(`tools/c7`・`tests/c7`・2026-09-09)で導入した自前規約(追記のみ・決定項は変更していない)**:

> 対象=§9.1 **C7** 行の受入(壁時計≤24h・M8≤24GB・S1≤5GB・診断行・決定論 T2・被覆指標 WC-6・**holdout 照合は事後1回のみ**(KDDI 形状5指標))を機械で回すための計器。新規は `tools/c7/{c7lib,occupancy_series,holdout_compare,c7_accept}.py` + `tools/c7/area_axes_v0.json` と `tests/c7/`(**58 本**)。`engine/**` は 1 行も触っていない(必要なフックは下記「親が入れる差分案」)。数値ユーティリティ(JSD・相関・表)は `tools/c6/c6lib` を再利用(新規依存なし)。

- **E-C7-1 形状5指標の操作定義と合格線=事前登録「案」(親判断待ち)**。境界・経済設計書 §1.4 は 5 つの**名前**(相関・ピーク時刻・平日休日比・エリア構成・属性構成)しか与えていないので、計算式と合格線は本ツールの提案(`c7lib.PREREG_V0`)。**H3「平日休日比」は測定不能**——KDDI の 6 レイヤは全て曜日軸を持たない(d1_reacquisition 結論3・④未発見1「平日/休日軸を持つ渋谷駅周辺の時間帯別滞在人口の open データは存在しない」)。代替として D1′ の**深夜残存率(1-4時平均÷終日平均)の値と順序**を置き、結果 JSON に `substituted: true` と理由を必ず出す。**5 指標のうち実測できるのは 4**。

  | # | §1.4 の名 | 操作定義(ラン側 ↔ holdout 側) | 合格線(案) | 根拠 |
  |---|---|---|---|---|
  | H1 | 相関 | エリア別 24 時間シェア(5×24)の **JSD**(エリアごと・平均/最大)+ 平坦化 120 点の **Pearson r** | JSD 平均 **≤0.0122**・r **≥0.80** | JSD 上限=**v1 テンプレ(破棄済みの旧 D1 基盤)と KDDI 2024 の JSD 0.01225**=「捨てた基盤より良いこと」の**下限対照**。r は自前(根拠なし) |
  | H2 | ピーク時刻 | 各エリアのシェア最大時刻(24 時周期の差)+ 5 エリアの**ピーク順序**(Kendall τ-b) | 全 5 エリアで **±1h**・τ **≥0.60** | D1′「ピーク時刻の順序関係」。±1h と 0.60 は自前 |
  | H3 | 平日休日比 | **測定不能** → 代替=**深夜残存率**の値と順序 | Δ絶対値 **≤0.05**・τ **≥0.60** | D1′「深夜残存率の順序関係」。閾値は自前 |
  | H4 | エリア構成 | 1 日合計のエリア別シェア(5) の JSD と最大差 | JSD **≤0.0122**・Δ **≤0.05** | H1 と同じ下限対照。Δ は自前 |
  | H5 | 属性構成 | エリア×属性(勤務者/居住者/来街者)シェア(5×3)の JSD 平均と最大差 | JSD 平均 **≤0.02**・Δ **≤0.10** | 全て自前(根拠なし) |

  - **参考(合格線ではない到達目標)**: `jsd_target=0.0012` = KDDI 実測の**年次変動 JSD の上端**(D1′ の「閾値根拠 0.0001-0.0012」)。データ側のノイズ床なので初回ランの合格線にはしない。
  - **親の確認事項**: D1′ の 0.0001-0.0012 が**どの底の JSD か**が答申に書かれていない。本ツールは `c6lib.jsd` の既定 **base=2(bits)** で計算する。自然対数で算出されていたなら閾値は ×ln2 になる。
  - **絶対水準は使わない**(D1′「値は形状と比のみ」)。読み取り直後にシェアへ正規化し、実数は JSON にも報告にも載せない(`tests/c7/test_holdout_compare.py::test_report_does_not_leak_absolute_levels` が機械で固定・水準を 987 倍しても判定が動かないことも固定)。

- **E-C7-2 セル→5エリア写像(`area_axes_v0.json`)= expedient**。5 エリアの**公的なポリゴンは存在しない**(KDDI 6 レイヤに geometry なし・SCJ API もジオメトリを返さない・確実な入手は区への照会=redesign D1′ 行 09-03)。台帳 D1′ は **(b) 採用決定(09-03)=expedient 境界**なので、その座標化を本ツールで行う。
  - 形=**外縁楕円 1 + 中心矩形 1 + 折れ線 3**(JR 線=南北軸/玉川通り=駅西の東西軸/六本木通り=駅東の東西軸。指針2010 p.18 と地図読み取り答申に一致)。判定は「外縁の外→圏外/中心矩形→central/それ以外は JR の西東 × 該当 EW 軸の北南」。代表点=**格子中心** `(ix+0.5)×100m`(`centroid_x/y` はノード配置でセル内に偏るため)。
  - 外縁は 139ha に**面積を合わせた楕円**(読み取り 4 端の矩形は 182ha=1.3 倍の過大)。**外縁 4 端と六本木通りの終点は、出典が明記する読み取り誤差 ±100-200m の範囲内で、5 エリアの面積が地図読み取りの面積目安帯に入るように当てた**(`fit_adjustments` に差分を明記)。したがって `area_ha_bands` の検査は**当てはめ残差であって独立検定ではない**。
  - 実資産 520 セルでの結果: central 9 / northwest 57 / northeast 27 / southeast 14 / southwest 31 ha(**合計 138 ha**・目安帯 全合格)・**圏外 329 セル**(bbox は 139ha 区域の約 2.7 倍なので当然)。
  - **感度**(地図読み取り答申④の要求「境界を ±50m 膨張/収縮して D1′ 判定が動かないこと」): `--sensitivity` で測る。実測 **−50m で 5.6% / +50m で 8.3% のセルが移動**。+50m では中心エリアが 9→20ha になり面積帯を外れる(中心矩形が小さいので膨張に最も弱い)。**D1′ 判定が動かないことの確認は、実ラン後に ±50m の写像で 5 指標を測り直して行う**(親)。
  - **昇格条件**: ① OSM 線形(ODbL・ライセンス台帳記帳)から JR 線・国道246号・六本木通り・139ha 区域線を取り、3 分割線+外周を実線形で構成する ② **SCJ 施設 214 件(5 エリア属性つき)を多角形に落として属性一致率 ≥90%**(地図読み取り答申の手順 3・SCJ データがリポに無いため未実施) ③ 区への境界照会。
- **E-C7-3 在圏時系列の取り口**。エンジンは `world.cells.density`(セル別在席数)を毎 tick 計算するが**保存していない**。当面は `tools/c7/occupancy_series.py` の `OccupancyRecorder` が **`engine.resolve.apply` をモジュール属性で包んで**毎正時に標本化する(**ソースは非改変**・読み取りだけ・呼び出し順と回数は素通し=`tests/c7` で固定)。C7 本ランでは**エンジン側フック**(下記差分案)が出す `c7_occupancy.npz` を `--journal` で読む経路を正とする。journal 形式 = `ticks (T,) int64` / `cell_counts (T,C) int32` / `kind_cell_counts (T,K,C) int32`(任意)/ `meta` JSON。既定の標本間隔=**60 tick(毎正時)**、5 分刻みも可(288×9×520×4B=5.4MB)。
- **E-C7-3b 種別→KDDI 属性の写像(`c7lib.KIND_TO_ATTR`)= expedient**。KDDI は自宅/勤務地の推定で 3 分類する。COMMUTER/DISPATCHER/CREW→**勤務者**、WORKER(舞台に常住し舞台内に勤める)/RESIDENT→**居住者**、VISITOR/REGULAR_VISITOR/FOREIGN_VISITOR/**STUDENT**→**来街者**。W16 母集団(390,067 体)の人数シェアは worker 55.6% / resident 11.2% / visitor 33.2% で、KDDI 2024 の 5 エリア平均(勤務者 ≈36% / 居住者 ≈11% / 来街者 ≈53%)と**方向がずれている**——ただし KDDI は**在圏**の構成でこちらは**人数**の構成なので直接は比べられない。H5 が落ちたときは写像を差し替えて感度を測る(親判断)。
- **E-C7-4 T2 の代替(3 脚)**。運用設計書 §1.4 T2 は「同一 manifest×2 で全 checkpoint ハッシュ一致」だが、**40 万体を 2 回回すと壁時計 48h で W1 を割る**。C7 では次を「T2 相当」とし、受入表に**T2 そのものではない**と明記する。
  - **T2-a** 5,000 体×1 シミュ日の**完全再ラン一致**(checkpoint 全点+final_hash)。
  - **T2-b** 40 万体 本ランの**先頭 K tick(既定 120)の部分再ラン一致**(=規模での決定論)。本ランと部分再ランは**同じ `--checkpoint-every`** で回すこと(前方一致で判定)。壁時計は本ランの約 1/12。
  - **T2-c** 40 万体 本ランの **checkpoint 自己整合**(tick 昇順・欠けなし・空の combined なし・`population_hash`/`schedule_hash` が全点同一)。
  - 3 脚とも合格で「T2 相当」。**T2-b の K と、これで T2 の代替として足りるかは親判断**。
- **E-C7-5 開封規律の実装形**。`holdout_compare.py` は ① `--open-seal` を**明示**しないと 1 バイトも読まない ② W19 の封印(`w19_freeze.json` の `holdout_seal`)を先に読み、メンバーの **sha256 が封印時と一致**することを確認(不一致なら停止) ③ **開封記録**(既定 `docs/bench/c7/holdout_open_record.json`: 層名・opened_utc・run_id・ファイル sha256・結果)を書く ④ **記録が既にあれば `--force` なしでは拒否**(=「事後1回のみ」の機械的担保)。manifest への書き込みは `--manifest ... --write-manifest` を付けたときだけ(既定は断片を印字するだけ=設計書・build_manifest を勝手に書き換えない)。
- **E-C7-6 生データの欄名は best-effort**。`la_raw_powerbi_2024.json` の実欄名は holdout なので**確認していない**。答申の実測構造表(`taizai_seibetu` 20,112 行=5エリア×年×月×時間帯×性別 / `taizai_zokuseibetu` 1,257 行=5エリア×年×月×属性)と表記(名称・年・月・時間帯・性別・属性・人数_の合計)から**別名表**で解決し、**解決できなければ例外で止める**(推測で埋めない)。`--field-map` で明示指定できる。時間帯は **5〜28 時の 24 区分**なので `hour % 24` で世界内の時に写す(24時台→0時・28時台→4時)。年は既定で**最新年を自動選択**。
- **その他の細部**: 深夜帯=1〜4 時台(D1b の定義)/`kendall_tau` は τ-b の自前実装(SciPy なし・O(n²)・n=5)。**全エリアが同順位だと τ-b の分母が 0 になる**(=順序で分化していない)ので、判定は FAIL のまま `tau_undefined: true` を結果に残す(「不一致」と「順序が定義できない」を取り違えないため)/受入表で読めなかった欄は `None`(「—」)のまま残す(推測で埋めない)/**P2 行は 40 万体では「参考」**(予算表 P2 の宣言は 5 千体の行で、40 万体の物理行が予算表に無い=**親判断待ち**)/L4 の 400 万呼は予算表の文面から機械で取れないので受入表側に定数で置いた(**要 delta か読み取り改良**)。
- **親が入れる engine 側フック差分案(本作業では入れていない)**: `engine/run.py` の `run_day` に `occupancy_every: int = 0` / `occupancy_path: str | Path | None = None` を足し、tick ループ末尾(`checkpoint` ブロックの直前)で `occupancy_every>0 and tick % occupancy_every == 0` のとき `world.cells.density` と `(kind, cell)` の bincount を list に積み、ラン終端で `np.savez_compressed` する。バイト予算=`24×520×4B=50KB`(毎正時)〜`288×9×520×4B=5.4MB`(5分刻み・種別つき)で **S1(≤5GB/シミュ日)の 0.1% 未満**。CLI に `--occupancy-every` / `--occupancy-out` を足す。既定 0 = **1 バイトも変わらない**(状態ハッシュ・診断行・テープに影響なし)。同じ場所で `checkpoints_json()` 相当(tick つき checkpoint JSON)も落とすと T2-b/T2-c がそのまま回る。
- **テスト**(`tests/c7`・**58 本**・実 KDDI は開かない): 折れ線の左右判定/合成幾何の 4 象限+中心+圏外/±dilate/写像 JSON 往復/境界定義が expedient と当てはめ経緯を宣言していること/実資産 520 セルで 5 エリア非空+面積帯+感度(`data/world/v2` が無ければ skip)/エリア集計と時刻平均/形状の量(シェア・ピーク・深夜残存・構成)/τ の既知値/種別→属性/journal 往復/**記録器が世界を書かない・呼び出しを素通しする・detach で戻る**/**封印ガード 3 種**(未指定・二度目・force)/sha256 不一致の検出/欄名解決と失敗時の例外/時間帯 5-28 の変換/**合成 holdout に対する 5 指標**(一致=合格・ピークずらし=不合格・**水準不変**・エリア構成のずれを検出・未供給は「測定不能」)/**報告に絶対水準が漏れない**/事前登録が「案」であること/ラン要約と `/usr/bin/time -v` の読み取り/決定論(完全一致・食い違い位置・前方一致・run_hash 形式)/自己整合/受入表(全合格・予算超過・欠けは未判定・診断行の欠け)/CLI 端から端まで。
- **親判断待ち(まとめ)**: (1) 形状5指標の**事前登録の確定**(特に H1/H4 の下限対照 0.0122 と、H3 を深夜残存率で代替してよいか) (2) JSD の**底**の確認 (3) セル→エリア写像を OSM 線形へ昇格させるか、expedient のまま C7 を回すか (4) T2-b の K と「3 脚で T2 相当」の可否 (5) P2 の 40 万体行を予算表に足すか (6) `KIND_TO_ATTR` の写像 (7) 開封の実行タイミング(受入表の他の行が全部通ってから 1 回)。

**C7 renderer 近接候補のベクトル化(性能・挙動不変・`perception/renderer`・2026-09-09)**:
C7(390,067 体)の実測で **llm 位相 46,079 ms/tick**(呼 2,709/tick)になり、cProfile(mock・3 tick・8,126 呼)が `perception/renderer.py` の `_nearby_items` を名指しした。原因は **1 呼あたりセル在席者ぶんの Python 反復**(距離の辞書内包 101.3 s・`set(peers)` の genexpr 17.9 s=**111,027,686 回**=1 呼 13,663 反復)と、**float32 SoA の全体コピー**(`np.asarray(agents.xy, dtype=float64)`=390,067×2 で **1.6 ms/呼**)。5,000 体では 0.27 ms/呼で見えなかった(セル人口が 2 桁違う)。**設計・規則は 1 行も変えていない**(§3 人物④の上位 k 密度逓減 3/2/1・知人常掲・同点処理・並び・距離の値)。

- **変えた 6 点**: ① 自分の座標は**2 スカラーだけ**読む(全体コピーを廃止)。② 座標は `prepare_tick` が作る**セル順の連続配列** `cell_x`/`cell_y` から取る(1 呼あたりの gather を廃止)。③ 自分の行は**逆置換** `cell_pos` で O(1) に外す(`peers[peers != i]` の全走査を `np.delete` 1 本へ)。④ 知人の同セル判定は `cell_pos` の範囲比較=**知人数ぶん**(旧: `set(peers)` の全走査)。⑤ `sqrt` は**採った数件だけ**(旧: セル在席者ぶんの辞書)。⑥ 知人集合/配列は `_acq_cache` に**個体ごと 1 度だけ**作る(知人表は Renderer 構築時に固定)。
- **バイト不変の作り方(ここが肝)**: `np.argpartition` に渡す `d2` の**並びと値を旧実装と完全に一致**させた。連続配列で `dx*dx + dy*dy` を作り(`((xy[peers]-xy[i])**2).sum(1)` と加算順まで同じ)、自分の行だけ `np.delete` で抜く(= `peers[peers != i]` と同じ順序)。距離は同じ `d2` の要素の `sqrt` を採るのでビット一致。float32→float64 の変換も旧実装と同じ経路(`asarray(xy, float64)` を tick 1 回に移しただけ)。**同点の解け方が変わる余地を残していない**(ties は `argpartition` に同じ配列を渡す限り同じ)。
- **キャッシュの鍵と無効化**: `_TickCache` は `prepare_tick(tick)` で**丸ごと作り直す**=鍵は **tick**(`render()` は `self._tickc.tick != tick` なら自動で `prepare_tick` を呼ぶ)。よって無効化は tick 境界のみで、tick 内でセルや座標が動かない前提に**依存しない**(動いた個体は `cell_pos` の範囲外に落ち、旧実装と同じ「素通り」経路へ行く=テストで固定)。`_acq_cache` の鍵は**個体 id**・無効化なし(知人表は不変)。
- **予算との関係**: 追加の per-tick 演算は `argsort` の後に **逆置換 1 本 + float64 変換 1 本 + 連続化 2 本**=390,067 体で **約 7.7 ms/tick**(`argsort` 17.7 ms は元からある)。診断の `detect` 位相は 38 → 42 ms/tick。**逐次ループは 1 本も増やしていない**(P4 宣言は `prepare_tick`=セル数ぶんの xxh64 のまま)。**P7**(p_notice のイベント演算 0.26 MOPS/イベント)には触れない(別経路)。**P6**(変化検出 ≤2 ms/tick)にも触れないが、同じ per-tick 前計算の枠なので実測は本節の値を使う。メモリは **+24 byte/体**(`cell_x`/`cell_y` 各 8・`cell_pos` 8)= 390,067 体で **9.4 MB**。M12(p_notice の 2+2 byte/体)と同じ「個体ぶんの補助配列」枠だが**予算表に行が無い**ので、M 行の追記が要るかは**親判断待ち**。
- **実測(実資産・mock・`--agents 390067 --ticks 3`・同一 PC・同一プロセスで新旧を差し替えて A/B)**:

| | llm[ms/tick] | 1 呼[ms] | 壁時計(3 tick) | final_hash |
|---|---|---|---|---|
| 修正前 | 16,908 | 6.242 | 54.5 s | `8f8d3467d2416685` |
| 修正後 | **690** | **0.255** | **6.1 s** | `8f8d3467d2416685` |

  呼数は両者 8,126(2,709/tick)。**final_hash が一致**=40 万体規模でも出力が 1 ビットも動いていない。**24.5 倍**・目標(llm ≤1,500 ms/tick・≤0.5 ms/呼)を満たす。親のサーバー実測 46,079 ms/tick は同じコードの別ハードなので、比は同じでも絶対値は環境で変わる。cProfile(修正後)では `_nearby` は 0.763 s/8,126 呼(**0.094 ms/呼**)まで下がり、上位は `arbiter.arbitrate`・`core.hashing._hash_rows_u64`(起床タイブレーク)・`llm_bridge.call` に移った(=次に効く場所はレンダラの外)。
- **不変の確認**: 実資産 5,000 体 mock 1 日の checkpoint `d5d793375a9d322e…` 不変・テンプレ SHA `161fe181` 不変・固定枠 golden `prompt_hash bb23f7c6…` 不変・規約⑧ 不変(既存 golden と `tests/perception` 全体)。
- **テスト**: `tests/perception/test_nearby_vectorized.py` **7 本**(**修正前の実装を逐語で持ち**、混雑世界の全個体で新旧の語と距離の**ビット一致**を照合(知人あり/なし)・tick 索引から外れた個体の素通り・空セル/範囲外セル・`cell_pos`/`cell_x`/`cell_y` の不変条件・**両モードの描画 prompt_hash 一致**)。

**C8 ablation/感度/計器盤の基盤(`tools/c8`・`tests/c8`・2026-09-09)で導入した自前規約(追記のみ・決定項は変更していない)**:
- **構成**: `tools/c8/c8lib.py`(純関数・設計書の走査・帰無参照)/`ablation_runner.py`+`ablations_v1.json`(第1陣 6 本の腕定義表と実行器)/`sensitivity.py`+`sensitivity_v1.json`(expedient 感度試験の台帳と構築段階の対照)/`dashboard.py`(忠実度計器盤 R14 G-1 の3面)/`ensemble.py`(アンサンブル運用 R14 G-4/G-5/G-8 の**設計だけ**)。`tools/c6/c6lib`(JSD・スコア・`run_smoke`・出力)と `tools/c7/c7lib`(受入表)を**再利用**(新規依存なし)。`src/shibuya/**` は 1 行も触っていない。
- **「結果を駆動していない」の判定形(自前・片側の論法)**: 構築段階の対照(入力側)の差が**帰無参照**(同じ分布から 2 回引いた 2 標本の JSD の 95% 点・多項リサンプリング 2,000 回)以内なら、入力が動かないのだから **その expedient はランの結果を駆動しえない**(`not_driving`)。超えたときは「駆動する**かもしれない**」までしか言えず、**ラン側の対照が要る**(`needs_run`)。**構築段階だけで「駆動している」とは結論しない**。方法論は「振って結果非依存を示す」としか書いておらず**合格線は設計書に無い**=帰無参照を仮の物差しに置いたのは expedient(親判断待ち)。
- **感度台帳の分母(漏れ検出)**: 世界データ構築仕様書 §2 の `### D-W\d+` 見出しの中で宣言された「感度: …」を正規表現で全部拾う(`c8lib.scan_build_spec_sensitivities`)。**行頭が「感度:」の行だけでなく `- expedient: …。感度: …` の行途中の宣言も拾う**(D-W2/W3/W5/W7/W9/W10/W15/W17 はこの形)。実測 **14 行**(D-W2・W3・W5・W6・W7・**W8(必須)**・W9・W10・W11・W13・W14・W15・W16・W17)。世界過程の感度試験 id は**コードが正典**として `src/shibuya/engine/processes/*.py` の `ablation_id` から拾う(**21 本**)。`tests/c8` がこの 2 集合と台帳を突き合わせ、**設計書にあって台帳に無い行があれば落ちる**。実装計画書 §8 の走査(`scan_plan_sensitivities`)は自由文なので**報告用**(分母には使わない)。
- **穴の記録**: `data/world/v2/build_manifest.json` の各段階 `expedients` 欄には **122 行**あるのに、設計書が感度試験を宣言しているのは **14 行**。差の 108 行は構築仕様書 §0-7「感度試験なしの expedient は出荷不可」に照らすと**未宣言の穴**=親判断待ち(台帳の `open_questions` に記録)。
- **腕定義表の安全弁**: `runs[].kwargs` は `ALLOWED_KWARGS`(`budget_mode`/`p_notice_ablation`/`processes_enabled|disabled`/`salient_rate_per_10k`/`use_population` の実装済み 6 個+差分案の 3 個)に限る。**未実装の口を使う腕は `pending: true`** を持ち、実行器は回さずに差分案を印字して exit 2。腕定義表(データ)から任意のキーワード引数が `cli.run` へ流れない。
- **GPU 時間の換算**: 受入報告 C6 §2b の実測(5,000 体×1,440 tick=呼 50,000 を 7×A5000 で約 29 分)から `CALLS_PER_SECOND = 28.7 呼/s` を置き、呼数 → 壁時計へ外挿する(**実測 1 点の外挿=expedient**)。**L2 の分母(総 GPU 時間)は絶対値で宣言されていない**ので、本表は「本番 1 シミュ日=W1 上限 24 h」を分母に置いた 20%=**4.8 h** を枠の目安にした(expedient・親判断待ち)。
- **計器盤の読み取り規約**: 入力(build_manifest/wc_index/w16・w17 gates/`docs/bench/c6*`/`tools/c7/c7_accept` の出力/受入報告 C0-C7/PENDING)は**あるものだけ読み、無い欄は「—」で残す**(推測で埋めない)。T1-T9 の「根拠」は受入報告の該当行を**自前の並べ替え規則**で選ぶ(箇条書き +3・数値あり +1.5・「実装中/予定/サブ」−2・新しい工程を優先)=**報告の補助であって判定ではない**。受入表の `HOLD`/`SEAL` 行は**面2だけに出す**(同じ行を 2 面に出さない=R14 G-1「ゲートは面2のみ」)。面2(holdout)の実行不能度 `I_M` は **Var_ens が要る=アンサンブルが無い間は計算しない**(R14 G-1「判定はラン単位でなくアンサンブル単位」の実装上の帰結)。
- **Markdown 表のセル**: `c8lib.markdown_table` は `c6lib.markdown_table` を包んで**セル内の `|` を必ず逃がす**(T5 の「|r| ≤ 0.05」・`budget_mode='fixed'|'ranking'` で実際に表が崩れた)。
- **アンサンブル(設計のみ)**: seed 写像は R14 G-5 の `blake3(manifest_sha256 ‖ 0x1F ‖ run_index)` の**下位 63 bit**(切り出し幅とマスクは自前)。完了済みラン表の列名も自前(G-7 が「自前ラン表のスキーマ」を expedient と明記)。CRPS はアンサンブル標本推定量 `mean|x−y| − ½·mean|x−x'|`(reliability/resolution 分解は未実装)、spread-skill は `sqrt(mean Var_ens)/RMSE(ens_mean, obs)`。

**C8 の実測(親検収の対象・2026-09-09)**:
- **ablation 第1陣 6 本の切替口**: 実装済みは **①のみ**(`--budget-mode {fixed,ranking}`=C6 で入った)。②p_notice d50・③近接入替の不応期・⑥広告ゼロ=**小さな差分案で足せる**(下記)。④聴覚 ΔSNR・⑤日次内省=**前提機能が §9 第2陣で未実装**(聴覚の物理軸はコードに無く同一セル代理・日次内省は就寝で「発火を記録するだけ」)。**親が入れる差分案**: (a) `run_day(p_notice_d50_scale=1.0)` → `WorldProcessRunner` → `SalientProcess` → `PNoticeParams(d50_m=D50_DEFAULT_M*scale)`。(b) `run_day(refractory_scale={WakeCondition.PROXIMITY_SWAP: 0.5})`=`engine/resolve.py` の `_REFRACTORY_TICKS` と `engine/arbiter.py` の `REFRACTORY_TICKS`(いま module 定数)を「ランが持つ表」に変える。(c) `run_day(signage=True)` → `Renderer(signage_enabled=…)` → `_signage` が False のとき `B2.signage_empty` を返す(テンプレ SHA 不変)。いずれも既定でバイト不変。
- **罠の記録**: `--ablate AB-PNOTICE-A0` は **`salient` 過程ごと止まる**(`runner._names_of` が A0-A4 を salient の別名として扱うため)。A0-A4 の腕を選ぶのは `cli.run(p_notice_ablation="A0")`(CLI フラグは無い)。
- **構築段階の対照(親のローカルで実行済み・5 本)**:

| 台帳 id | 設計 | 宣言 → 対照 | JSD[bits] | 帰無95% | 判定 |
|---|---|---|---|---|---|
| S-W16-FLOOR | D-W16 | 建物床面積按分 → **面積按分** | **0.1239** | 0.0035 | ラン対照が要る(TVD 0.297=住民の 3 割が別セルへ) |
| S-W14-HOURUNIFORM | D-W14 | time_dist_12 の時刻重み → **一様** | **0.3007** | 0.0057 | ラン対照が要る(8 時 28.6% → 4.2%) |
| S-W15-TEMP | D-W15 | 実測気温 → **+1.5 ℃** | **0.0616** | 0.0042 | ラン対照が要る(体感段階が **43.7%** の時間で変わる) |
| S-W14-JRPHASE | D-W14 | 等間隔ダイヤ → **位相を半運転間隔ずらす** | 0.000024(時別)/0.0019(10 分) | 0.0011/0.0054 | **駆動していない**(時別・10 分別とも帰無内。ただし時間あたり本数の最大差は 12 本=1 分刻みの乗車判断への影響は別問題) |
| S-W17-RAKE | §8 RAKE_MAX_FRAC | 適応予算 → **固定 12%** | Δ=0.0203 | —(両側とも決定論) | 固定 12% で jsd_max_after **0.40085**・修正率 **0.21168**(登録簿の 0.401/0.2117 を**再現**)=適応は JSD +0.020 と引き換えに修正率ゲートを通す |

  再 ingest(応答 jsonl 約 400 MB・`rake_budget_rows = 0.12 × 12,565,687 = 1,507,882`)の所要は **90 s**(サーバー実測 103 s と同オーダー)。
- **計器盤の初回実行(C7 本番ラン進行中・`--accept` なし)**: 構築ゲート **200 本中 不合格 3**(W9 `shadow_bytes_per_day_le_10mb`=D-2/W10 `calibration_max_abs_residual_db`・`primary_secondary_sections_matched`=D-1)。被覆 **C 0.425 / C_q 0.237 / Q 0.204 / D 0.327 / V 0.000 / R —**・X 0.0041・孤児 0(WC-6 PASS)。書式エラー率 実効 **0.0077**/厳密 **0.3791**(D-28)・役割語率 **0.0**(D-38)。指標 B Δ違反率 −0.12(CI 上限 0.154 > 0.05)・JSD 0.2909(帰無 0.0156)=**両方不合格**(D-37)。「歪む場所」の宣言候補は PENDING から **8 件**(D-2/D-7/D-14/**D-33**/D-35/**D-37**/**D-38**/D-40)。
- **アンサンブルの見積り(設計のみ)**: 390,067 体×1,440 tick=呼 **3,900,670**/ラン → **37.7 h/ラン**(C6 実測からの外挿)=**W1 24 h を単体で超える**。8 本なら 302 h。体数・シミュ日・本数のどれを削るかは**親判断**(`ensemble_v1.json` の `open_questions` に自動で出る)。k\* の凍結ファイル(R14 G-2)は**未作成**。
- **テスト**: `tests/c8` **105 本**(c8lib 19: 表のエスケープ・帰無参照の性質と決定論・片側判定・GPU 換算が C6 実測を再現・予算表は Markdown が正典・設計書走査(行途中の感度・必須は D-W8 だけ・第1陣 6 本・AB-* 21 本)/腕定義表 22: 6 本と rank・設計書逐語との対応・未実装なら差分案必須・kwargs allowlist・L2 枠内・実装済みは①だけ・mock で差の出ない腕は①⑥・引き当て・表の整形・破壊検出・`run_metrics`/`compare_runs` の純関数・実行器が未実装の腕を回さない・**GPU 時間が換算式と一致**・合計欄が腕の積み上げと一致/感度台帳 22: 突合(1 行落とすと「漏れ」で落ちる)・過程 id はコードが正典・done 行は result 必須・小データの構築対照(Δ=0 は no-op・既に一様なら差なし・実ダイヤは動かさない・10 分間隔を 5 分ずらすとどのビンでも測れないことの記録)・実資産(あるときだけ)/計器盤 22: 収集の純関数・入力欠けで「未測定」・被覆は加重和にしない・面1に judge を作らない・赤は症状のみ・T1-T9 の根拠が無ければ空欄・表の整形/アンサンブル 20: seed 写像の決定論と衝突なし・core.rng に通る・master_seed のみ変える・W1 超過の自動検出・CRPS/spread-skill/実行不能度)。doctest 5 本。


**C8 ablation 切替口 ②③⑥(`engine`・`perception`・`cli`・2026-09-09)で導入した自前規約(追記のみ・決定項は変更していない)**:
> 知覚契約書 **§8**「ablation の優先順位規則…第1陣 6 本」は義務(方法論「ablation マトリクスは完了条件」)。ここで足したのは**腕を選ぶ口**だけで、係数も表もテンプレも 1 つも書き換えていない。**既定値で 1 バイトも動かない**ことをテストと退化検査で押さえる。

- **② p_notice の d50(`AB2-PNOTICE-D50`)**: `run_day(p_notice_d50_scale: float = 1.0)` → `WorldProcessRunner(p_notice_d50_scale=…)` → `SalientProcess(d50_scale=…)`。CLI は `--pnotice-d50-scale FACTOR`(別名 `--p-notice-d50-scale`)。倍率は `PNoticeParams(d50_m=D50_DEFAULT_M×scale)` と **`salient.D50_BY_KIND`(事象クラス別 40/45/60 m)の両方**に掛かる(片方だけだと `notice_event(d50_m=…)` が per-kind 値で上書きするので腕が効かない)。**打ち切り `cutoff_m`(80 m)は動かさない**=§3.1 の別の expedient なので同じ腕で 2 つを振らない。その結果 **2.0× は d50=打ち切りと同値**になる(報告に明記)。倍率は正の有限値のみ(0・負・NaN・inf は `ValueError`)。§3.1 の **A0-A4 と併用できる**(A0 は定数 0.54 なので d50 を無視する=テストで固定)。診断は `salient.d50_scale`、manifest 欄は `p_notice_d50_scale`。
- **③ 不応期表(`AB3-REFRACTORY-PROX`)**: `run_day(refractory_scale: Mapping[…, float] | None = None)`。CLI は `--refractory-scale COND=FACTOR`(繰り返し可・条件名は `WakeCondition` の 11 行・大小文字と `-`/`_` を吸収)。`engine.resolve.refractory_ticks(scale)` が**ランの実効表**を 1 本組み、`set_refractory(..., table=…)` がそれを読む。`scale` が `None`/空なら**モジュール定数の配列オブジェクトをそのまま返す**(新しい配列すら作らない=既定でバイト不変の担保)。**丸めは自前規約**(§8 に規定なし): 表は分の整数なので `floor(x+0.5)`(half-up)=15 分 ×0.5 → **8 分**・×1.5 → **23 分**。倍率 0 は「床なし」として許す。manifest 欄 `refractory_scale` は `{条件名: 倍率}` を**名前昇順**で持つ。
  - **見つけた事実 1**: `engine/arbiter.py:109` の `REFRACTORY_TICKS` は **論理に使われていない写し**だった(アービタは `refractory_until`(体×条件の「次に起床してよい tick」)しか読まず、タイマーを張るのは `resolve.set_refractory` だけ)。よって実効表を渡す先は resolve **1 箇所**。写しは残し、コメントで「参照用・ablation ③ が振るのは `resolve.refractory_ticks`」と明記した(2 つの正典を作らないため、既定で両者が一致することをテストで釘付け)。
  - **見つけた事実 2(親判断待ち)**: **`PROXIMITY_SWAP` を起床候補に出すコードが無い**。`change_detect` が出すのは `INTEROCEPTION` と `CELL_BLOCK` の 2 条件だけで、近接入替・知人出現・被注視・傍受の 4 行は §9 **第2陣**。したがって ③ の腕(近接入替 15 分 ±50%)は**切替口はあっても現状 no-op**。切替口が壊れていないことは `CELL_BLOCK` を 0.5 倍して checkpoint が動くことで示し、第2陣が入った日に落ちるテストを置いた。
- **⑥ 広告ゼロ(`AB6-AD-ZERO`)**: `run_day(signage: bool = True)` → `Renderer(signage_enabled=…)`。CLI は `--no-signage`。`_signage_body()` の先頭で `None` を返すだけ=**固定枠と単一ランキングの両方**が同じ材料を使っているので 1 箇所で腕が効く(固定枠 → `B2.signage_empty`・ランキング → 候補が空列)。W14 凍結文も合成文も等しく落ちる。**テンプレ本体に 1 文字も足していない**(`B2.signage_empty` は「表示が無いセル」用に元からある)=`template_sha256=161fe181…` 不変・固定枠 golden `prompt_hash bb23f7c6…` 不変・規約⑧ 不変。効果は**セル群トークンが減る側にしか動かない**。
- **manifest 欄**: `run_manifest_fields()` に `p_notice_ablation`(`A0`-`A4` へ正規化)・`p_notice_d50_scale`・`refractory_scale`・`signage` の 4 欄を追加(既定値のランでも欄は常に出る=腕が「既定だった」ことが後から言える)。`RunResult` 側は**実際に走った側**を書く(⑥ はレンダラの `signage_enabled`、② は `runner.salient.d50_scale`)。注入レンダラのランでは注入側の値が正=①と同じ作法。
- **測れる範囲(親への報告事項)**:
  - **② は合成世界では測れない**。個体は街路ノードに座り、`World.synthetic` はセルあたりノード 1 個なので事象までの距離が **0 m か 100 m**(打ち切り 80 m の外)しか無い。実資産(`data/world/v2`)2,000 体×90 tick の下見では、A4 既定で 0.5×/1.0×/2.0× の到達が 10,736/10,736/10,737(候補 12,899)= **天井に張り付く**(共在で距離 0 → `p1=1`、加えて社会伝播)。A1(距離のみ)なら 10,749/10,799/10,910 と動く。**腕の指標(情報到達半径)を実 LLM で測る前に、何を測る腕なのかの再確認が要る**=親判断。テストは 0-79 m に個体を並べた場面で A1/A2/A3/A4 の**全段で単調**であることを釘付けする。
  - **③ は `CELL_BLOCK` なら mock で動く**(checkpoint が変わる)。`PROXIMITY_SWAP` は上記のとおり第2陣待ち。
  - **⑥ は mock では描画バイトと入力トークンだけが動く**(MockLLM は本文を読まない=C6 実測)。`final_hash`・呼数は不変。行動差は実 LLM でしか出ない。
- **不変の確認(退化検査)**: 実資産 5,000 体 mock 1 日(`python -m shibuya.cli --agents 5000 --seed 1 --world data/world/v2`)の checkpoint **`d5d793375a9d322edd36c7b11b98e3be17072f8ea8a84f33ea9e9065c8725803`** 不変(呼 49,847・会話 48・保存則 OK)・テンプレ SHA `161fe181bc325f00…` 不変・固定枠 golden `prompt_hash bb23f7c6…` 不変・manifest の腕は既定 `fixed_slots`/`A4`/`1.0`/`{}`/`True`。
- **腕定義表の更新**: `tools/c8/ablations_v1.json` の ②③⑥ を `status: ready`・`switch.implemented: true`・`how`/`verified` を実装に合わせた(**それ以外の欄・コードは触っていない**)。**残る 1 手**: `runs[].pending: true` と `ablation_runner.PENDING_KWARGS` が tools/c8 側にあるため、実行器は依然この 3 腕を飛ばす(`executed: false`)。回すには tools/c8 の 2 箇所(`PENDING_KWARGS` から 3 キーを外す・各 `runs` の `pending` を落とす)が要る=**親判断**(`open_questions` に記録済み)。同じく tools/c8 側の `ablation_runner._manifest_fields` は manifest 欄を 5 個に絞っているので、新しい 4 欄(`p_notice_ablation`/`p_notice_d50_scale`/`refractory_scale`/`signage`)は腕の結果 JSON に載らない=腕の同定が結果ファイルだけでは付かない(3 箇所目の親判断)。
- **テスト**: `tests/engine/test_ablation23_switches.py` **39 本**(② 表の既定・per-kind の倍率・A1-A4 全段で到達が単調・A0 は無視・起床候補=到達・不正倍率 4 通り・`ablation_name` の正規化/③ 既定は同じ配列オブジェクト・half-up 丸め・鍵 4 形・倍率 0・不正 4 通り・manifest 形の名前昇順・`set_refractory` がランの表を使う・形の違う表を拒む/run_day: 既定明示でバイト不変・`CELL_BLOCK` で checkpoint が動く・`PROXIMITY_SWAP` は第2陣まで no-op(入った日に落ちる)・manifest 4 欄・過程を切ったランでも腕の値を検査・`cli.run`/`cli.main` のフラグ往復 5 通り・使い方の誤りは usage で exit 2)・`tests/perception/test_ablation6_signage.py` **15 本**(golden `bb23f7c6…` 釘付け・両モードで空文言・全セル・材料が 1 本・テンプレ SHA 不変・規約⑧・群予算は減る側のみ・run_day で checkpoint 不変かつセル群トークンが減る・`--no-signage` 往復)。`tests/c8` は 105 → **105 本**(実装状況の事実を書いた 3 本を更新: 実装済みは①だけ → **①②③⑥**・未実装の腕の例を ⑥ → ④)。

**D-58 テープ繰り延べ行(`engine.tape` 版2・`engine.llm_bridge`・`llm.fleet`・`engine.run`・2026-09-10)**:
> 運用設計書 §2.5「録画リプレイ=LLMテープ(**1呼=1行**・共有ブロックはID化・`params_hash`)から **(agent_id, tick, wake_class, prompt_hash) 完全一致**で引く。テープ外は失敗」は**決定項=変更していない**。ここで足したのは「1呼」の中に**答えの返らなかった呼**を含める拡張(繰り延べも 1 行・応答空・`deferred` 印)。鍵の4要素・テープ外=失敗・テープ外率の診断行はそのまま。

- **なぜ要るか(PENDING D-58)**: 艦隊経路は queue full / タイムアウトの呼を**翌 tick の起床候補へ再投入**する(憲法1=破棄禁止・`run.py` の `fleet_deferred`)。版1 のテープは応答の返った呼しか行を持たないので、再生には繰り延べが存在せず tick 0 から状態が分岐した(本番 c7-day-2 = 390,067 体・繰り延べ 1,320,190 呼 → `tape_miss` 3,569,355/3,618,159 = **98.7%**)。
- **スキーマ版**: `shibuya.tape/2`。Parquet の**スキーマ metadata** `shibuya.tape.schema` に入れる(`Tape.schema_version`)。版1 の 10 列は**順序ごと不変**、末尾に 3 列を足すだけ。
  - `deferred` (int8): 0=応答が返った / 1=繰り延べ。繰り延べ行は `response=""`・`tokens_in=tokens_out=0`。
  - `deferred_reason` (string): `llm.fleet.Outcome` の値=`deferred_queue_full` / `deferred_timeout` / `error_other` の**閉じた語彙**。応答行は `""`。自由文の `Deferred.reason`(例外型名・HTTP ステータス)は**テープへ入れない**(列を非決定にしない・診断行と `debug_dir` に残る)。
  - `observed_tick` (int64): エンジンがその呼の帰結を**観測した** tick。−1 = 同 tick 同期(mock/スタブ経路=版1 と同義)。
    - **親の指示との差分(黙って解決しない)**: 指示は新列 2 本(`deferred`・`deferred_reason`)。3 本目 `observed_tick` を足したのは、**繰り延べだけ記録しても再生が一致しない**ため。① タイムアウトの繰り延べは発射 tick `T` ではなく観測 tick `T+k` で再投入される(`run.py` の ④′ poll → 同 tick の再投入枠)ので、`T+1` に戻すと本番と別の tick で起床する。② 応答の返った呼も艦隊では `T` より後に届き、`t_apply = max(tick+δ_think, 到着tick+1)`(運用設計書 §2.4 + `run.py`)が到着 tick に依存する。どちらも「エンジンが帰結を観測した tick」1 本で表せるので、列は 1 本にした。
- **後方互換**: 3 列が無い版1 テープは `deferred=0` / `deferred_reason=""` / `observed_tick=-1` として読む(`Tape._column`)。`Tape.schema_version` は metadata が無く新列も無ければ `shibuya.tape/1` を返す。`Replay` は**既定でない行だけ**を副索引 `_meta` に入れるので、版1・mock テープでは索引の RAM も走査も版1 と同じ(空 dict)。
- **記録側**:
  - `llm.fleet.FleetBridge`: `submit`/`poll`/`drain`/`submit_and_drain` に `now_tick` を足した(既定 −1=tick を持たない経路)。`Deferred` を返す/受けるたびに `_record_deferred` が 1 行書く。応答行にも `observed_tick=now_tick` が入る。`engine.run` は `poll(now_tick=tick)` / `submit(calls, now_tick=tick)` / 終端の `drain(now_tick=ticks)` を渡す(`ticks` = 最後の tick の 1 つ先=「ループ中には届かなかった」の印)。
  - 繰り延べ行の `prompt_hash` は応答行と同じ算法(`sha256_cbor(call.prompt)`)= 再生は**発射 tick の鍵**でこの行を引き当てる。
  - 再送で最終的に答えが返った呼は従来どおり**別の行**(別 `call_id`・別 `tick`)。
- **再生側の意味論**(`engine.llm_bridge.LLMBridge.call` + `engine.run`):
  - `Replay.lookup_row` が版2 の欄を値で返す(`TapeHit`)。文字列契約の `Replay.lookup`(= `llm.TapeLookup` / `TapeLLM` が使う口)は繰り延べ行に当たると **`TapeDeferred`** を投げる(「応答が無い」は文字列で表せない・`llm.fleet.FleetDeferredError` と同じ手口)。`TapeDeferred` は `TapeMiss` の**兄弟であって部分型ではない**=`except TapeMiss` で握ってもテープ外率に混じらない。
  - `mode="replay"` の `LLMBridge.call` は `Replay.lookup_row` を 1 回引く(`LLMClient` 契約は応答文字列しか運べないので、版2 の欄を取るためにここだけ `Replay` を直に読む。`TapeLLM` は llm 層の口として従来どおり使える)。繰り延べ行なら `BridgeResult(deferred=True, deferred_reason, observed_tick)` を返し、**パースも未定義行動5段も通さない**(本番の `FleetBridge._interpret` が `Deferred` を素通しするのと同じ)。
  - `engine.run` は再生モードで**艦隊の代役**(`replay_inbox: observed_tick → 届く項目`)を回す。発射(④)で `observed_tick > tick` なら受信箱へ入れ、④′(艦隊 poll と**同じ位置**)で取り出す。繰り延べは `fleet_deferred` へ積んで既存の再投入ブロック(不応期の `clear_refractory` つき)に通す=**本番と同じ 1 本の道**。queue full(`observed_tick == 発射 tick`)は本番と同じく翌 tick の再投入枠へ、タイムアウト(`observed_tick > 発射 tick`)は観測 tick の ④′ で再投入。ラン終端に残った分は本番の `drain` と同じ位置で処理し、`fleet_drained_at_end` / `fleet_unanswered_at_end` に出る。
  - 呼数 L4 は**発射数**のまま(繰り延べも 1 呼)。再生の要約に `fleet_reinjected` / `fleet_resent` が出るのは**繰り延べを再現したときだけ**(mock ランは従来どおり `fleet_*` 欄を持たない)。
- **既定でバイト不変**: mock ラン(繰り延べ 0)は全行 `deferred=0`・`observed_tick=-1`・`replay_inbox` は空のまま=`run_day` の分岐に 1 度も入らない。退化検査 = 実資産 5,000 体 mock 1 日(`--agents 5000 --seed 1 --world data/world/v2`)の checkpoint **`d5d793375a9d322e…`** 不変・会話 48 不変。テープのバイト列自体はスキーマ変更で変わる(列が 3 本増える)が、これは**版2 の定義**であって挙動ではない。
- **残る非決定(宣言)**: ① 本番の**到着順は非決定**(`llm.fleet` の docstring・運用設計書 §2.4 は「到着順に適用しない=適用順は `apply_key` 昇順」)。再生は 1 tick 内を**発射順**で配るので、`pending` の適用順(`apply_key` 昇順で並べ替える)は一致するが、同 tick に同一セッションの 2 人が発話した場合の `conv.utterance` の順は本番と一致しない場合がある。② `UndefinedActionRegistry.observe` の呼び順が本番(到着順)と再生(発射順)で違う=段2/段3 の裁定閾値に達する tick がずれうる(現状 段1 も段2 も `action_code` は `UNDEFINED_ACTION` で同じなので行動には出ない)。どちらも**版2 で解決していない**=本番テープの再生で最初に疑う場所。
- **テスト**: `tests/engine/test_tape_deferred.py` **8 本**(queue full を強制した艦隊ランの録画→再生が全 checkpoint・`final_hash` 一致/タイムアウト(発射より後の tick で観測)も同じ tick で再現/繰り延べ行が待機 intent を作らない(版1 の「空応答→未定義行動」に落ちていない)/版1 テープが読める・版1 テープでの 1 日再生が一致/繰り延べ 0 のランは行数=呼数・全行既定値・`Replay._meta` が空/`lookup` は `TapeDeferred`・`lookup_row` は値/`TapeWriter.n_deferred_rows`)。`tests/llm/test_fleet_contract.py` の欄突合は `deferred`/`deferred_reason`/`observed_tick` を**再生側の欄**として除外(本番の艦隊は繰り延べを別の型 `Deferred` で返す)。

**D-53 リング容量の N 比例(`economy.ledger`・`economy.goods`・`shibuya.cli`・2026-09-10)**:
> D-R2-6(状態成長宣言)は**決定項=変更していない**。5欄も cap の意味(予算表 M 行の値)もそのまま。ここで直したのは**実装が宣言に追いついていなかった**点=リングバッファの容量が N に比例せず、cap(= 容量 × 行バイト)が宣言投影(O(N))を下回っていたこと。

- **症状(PENDING D-53)**: C7 本番 390,067 体で `core.growth.check_growth` が `declared_over_cap = ['transfer_log', 'delivery_log']`(**実測を待たずに宣言だけで cap 超過=設計が破綻している**)。`transfer_log` の実測 6,291,456 B は cap ちょうど=**リングが 1 日で一周**していた(生ログを捨てていた)。
- **原因**: 宣言は `per_day_growth="O(N)"` × 72 B/体/日(3.0 取引 × 24 B)・保持窓 1 日なので投影 = 72 × N。一方 cap は固定容量 `DEFAULT_RAW_CAPACITY=262,144` 行 × 24 B = 6.29 MB で **N に比例しない**。390,067 体では投影 28.1 MB > cap。`delivery_log` も同型(2.0 移動 × 16 B = 32 B/体/日・固定 131,072 行 = 2.10 MB < 12.5 MB)。
- **直し**: 容量を N から決める。`economy.ledger.raw_capacity_for(n_households, retention_days) = max(16,384, ceil(3.0 × N × 保持日数))`・`economy.goods.delivery_capacity_for(n_agents, retention_days) = max(16,384, ceil(2.0 × N × 保持日数))`。`Ledger(raw_capacity=None)` / `GoodsLedger(delivery_capacity=None)` が既定でこれを使い、**cap = 容量 × 行バイト = 宣言投影**(下限より上の N では等号)になる。明示した容量は従来どおりそのまま(既存テストの `raw_capacity=16` などは不変)。
- **物の台帳に `n_agents` を渡す理由**: 在庫は POI 側(設計書 §7.1「個体 M1 には載せない」)なので `GoodsLedger` は個体数を持たなかったが、`check_growth` の N は**個体数**(`engine.run` が `n_entities=n_agents` を渡す)。宣言 O(N) の N と容量の N を一致させるため、`cli.build_ledger_bundle` が `GoodsLedger.from_pois(..., n_agents=n_agents)` で渡す(省略時は下限のみ)。
- **下限 16,384 行(expedient)**: 取引・移動の行は個体だけでなく**店舗**からも出る(参入資本 `endow_stores` = POI 数ぶん・域外仕入の代金 = 納品数ぶん・廃棄収集 = POI 数ぶん)ので、小さな N では 3.0×N / 2.0×N を下回る容量になってリングが一周する。下限は 0.39 MB / 0.26 MB = 据え置き既定(6.29 MB / 2.10 MB)より**小さい**=小規模ランは RAM が減る側にしか動かない。
- **バイト(予算書 §3 の実測・delta 節へ記載)**: 390,067 体で transfer 28.1 MB + delivery 12.5 MB = **≈40.6 MB**(M8 の 0.17%)。旧実装比 +32.2 MB(会計値。実配列は 23 B/行・14 B/行なので実 RSS 増は ≈+30 MB)。5,000 体は下限のまま。
- **既定でバイト不変(退化検査)**: 実資産 5,000 体 mock 1 日(`--agents 5000 --seed 1 --world data/world/v2`)の checkpoint **`d5d793375a9d322e…`** 不変・呼 49,847・会話 48・保存則 OK・成長行の**実測値も不変**(`transfer_log` 213,216 B / `delivery_log` 71,296 B)。動いたのは cap の表示だけ(6,291,456 → 393,216・2,097,152 → 262,144)=5,000 体では 8,884 行 / 4,456 行しか使わず**リングは一周しない**。
- **テスト**: `tests/economy/test_ledger.py` 4 本(N 比例・下限・保持窓倍・明示容量は不変/5,000 体で一周しない/宣言だけで cap 超過しない = 5,000 体と 390,067 体)・`tests/economy/test_goods.py` 3 本(同上)・`tests/engine/test_ledger_wiring.py` 1 本(`LedgerBundle.growth_parts()` を 390,067 体で `check_growth` に通し `declared_over_cap` が空・cap = 28,084,824 / 12,482,144・同ファイルの 500 体 1 日ランは `n_raw_dropped == 0` = 生ログを捨てていない)。

**D-51 乗車の意図保持(`engine.resolve`・`engine.processes.rail`・`agents.state`・`engine.run`・2026-09-10・ユーザー決定 (c))**:
> **行動契約書・世界過程設計書・運用設計書の決定項は変更していない**。ここに登録するのは、行動契約書 §2.1「乗車」の前提条件「**同一セルに停車中**」の**読み**を「満たすまで世界が運ぶ」へ広げたこと(**判断は 1 回・実行は世界**=MATSim の計画実行と同じ形)と、その実装で導入した自前規約・定数。設計書本文は書き換えていない。

- **症状(PENDING D-51)**: C7 本番 390,067 体で「乗車」が **64,784 回**選ばれて実乗車 **75 回(0.12%)**。答申(`docs/research/v2-c7-fix-research.md` §3-1・親一次確認)の診断=「停車時分は既に現実の 2 倍長く、在線条件では説明できない。実世界では『乗車を決める』と『ホームに立つ』の間に **3〜7 分**ある(渋谷の乗換え移動 ピーク 3.3 分/オフピーク 5.5 分・東急は地上2階→地下5階・最長 579.3 m)。エンジンにこの過程が無いので、乗車を選んだ体はホーム以外のセルに居たまま前提を満たせず消えていた」。実務の標準(MATSim/DTA)でも denied boarding は**定員到達時にのみ**起きる。
- **(a) ホームで待つ状態**: 個体 SoA に **`board_line`(int8・-1=意図なし)/ `board_since`(int32・-1=まだ立っていない)** を足した(**5 B/体**・M1 上限 30,000 B/体の 0.017%・390,067 体で **1.95 MB**)。ホームのセルに居て「乗車」を選ぶと `activity=WAITING`・`board_line`・`board_since=tick` になり、**失敗を返さない**(従来は列車が居なければ `NO_TRAIN`)。**`transit_state` は 0(在圏)のまま**=乗客の保存則の分母である 3 値を増やしていない。
- **(b) 意図の保持**: ホーム以外で「乗車」を選ぶと、世界が**最寄りの(行ける)ホーム**へ `target_node` を張って `activity=MOVING` にする。移動は**既存の next-hop 機構そのまま**(新しい経路探索を作っていない)。到着は既存の `_apply_engine_step` の到着分岐が拾い、そのまま待ち行列へ入る。「最寄り」は**ホーム代表ノードへの直線距離の昇順**(経路長ではない=expedient)、同距離は**路線索引の昇順**(決定論)。近い順に「経路があるか」を見て最初に通ったものを採る(逐次ループは**便のある路線ぶん**≤8)。
- **(c) 停車時分と混雑率**: `DWELL_TICKS` を線別表にした。**通過型ホーム 1 tick(60 秒)**=mechanism(実停車時分 30〜60 秒 = 乗降 10〜45 秒 + 確認 8.7〜20.5 秒・東京メトロ自社設定 ラッシュ 20〜60 秒・京王 15〜25 秒基本・東急 5 秒単位 急行30/特急40 秒。**60 秒は実値の上界**)、**終端(渋谷で折り返す 銀座線・京王井の頭線)2 tick**=expedient(終着 最低 45 秒 + 折返し時分は**未取得**)。「1 分 tick では 20〜60 秒を表せない」ことも expedient として宣言。混雑率上限 `LINE_CONGESTION_CAP_PCT` は**令和7年度(2025)実績**へ 5 行更新(田園都市線 133→**138**・東横線 122→**124**・半蔵門線 103→**111**・副都心線 117(据置)・井の頭線 123→**125**)。**山手線 139・埼京線 163・銀座線 147 は 2025 値が親未確認**のため令和6年度のまま据え置き、行コメントで明示(答申は 135/136・167・153 を挙げるが**推測で埋めない**)。
- **(d) 待ちの打ち切り `BOARD_WAIT_LIMIT_TICKS = 30`(expedient)**: 渋谷の運転間隔は全線 2.2〜5.0 分・待ち時間=間隔の半分なので、**最大 5 分の 6 倍**を上限に採った。メトロ 3 線は **1〜4 時台の運行が 0 本**=「待っても来ない時間帯」が実在するので打ち切りが要る(無いと始発まで動かない体が出る)。打ち切りは `board_line` を落として **`NO_TRAIN`** を返す(個体は次の起床で判断し直す)。
- **失敗の意味論に新語を足していない**: 行けるホームが 1 つも無い/乗車中・域外滞在で乗ろうとした場合も **`NO_TRAIN`**(契約書 §2.1 の 3 語=満員・運賃不足・列車なし のまま)。内訳は `rail.counters()` の `board_unreachable` に出す。
- **待ち行列の捌き(`_serve_board_queue`)**: Phase C の**行動語の適用の後・位置確定の前**に 1 本走る(同じ tick にホームへ着いた体と、同じ tick に乗車を選んだ体を同じ列車に乗せるため)。順序は **`board_since` 昇順 → `agent_id` 昇順の FIFO**(決定論)。受容は従来どおり `rail.accept_quota`(§2.6 の混雑率→受容率)。**乗れなかった体は待ち続ける**(`TRAIN_FULL` を「直前の結果」に書くだけ・意図は落とさない)。**運賃を払えない体は意図を落とす**(待っても払えない=`FARE_SHORT`)。
- **待ち行列の突合は「線」ではなく「セル」**(expedient): 渋谷は 8 線のうち 7 線が同じホームセル(291)に載る(半蔵門線だけ 239)。`board_line` は「どのホームへ行くか」を決める欄で、実際に乗れるのは**そのセルに停まった便すべて**。行き先(方面)を持たないので線を選び分ける意味が無い=行き先を持たせるのは第2陣。
- **意図の落ち方(不変条件)**: 意図を持つ体は「ホームへ歩いている(`MOVING`)」か「ホームで待っている(`board_since≥0`)」のどちらか。①**乗車・待機・エンジン継続以外**の行動を確定したら落とす(Phase C の冒頭 1 本)。②到達不能(`UNREACHABLE`)で歩みが止まったら落とす。③会話に引き込まれる等**自分の行動以外**で止まった体は毎 tick の掃除で落とす(`rail.board_dropped`・失敗は返さない)。④域外へ出す `place_at_external` でも落とす。
- **逐次ループ宣言(P4)**: `_apply_board` = 便のある路線ぶん(≤8)×2 本・`_serve_board_queue` = **この tick に停車中の列車数**ぶん 1 本(路線 8 × 方向 2 = 高々 16 級)。どちらも個体数に比例しない。**個体数に比例するのは `board_line ≥ 0` の全走査 1 本**(390,067 体で **0.42 ms/tick** の実測・以降は意図を持つ体だけの小さい添字で回す)。5,000 体の実測で phase_c 0.45 → **0.63 ms/tick**、movement(P2)は 0.092 → 0.100 ms/tick で上限 5 ms に対し不変。
- **診断行**: `RunResult` に `n_board_waiting` / `n_board_timeout`(要約の「乗車待ち W(打ち切り T)」)。`rail.counters()` に `board_intent` / `board_walking` / `board_waiting` / `boarded_from_queue` / `board_timeout` / `board_unreachable` / `board_dropped` / `board_success_rate`。
- **退化検査(挙動が変わる修正=checkpoint は変わって当然)**: 実資産 5,000 体 mock 1 日(`--agents 5000 --seed 1 --world data/world/v2`)。checkpoint **`d5d793375a9d322e…` → `602f3bfb2b1aeefb…`**。**乗車 167 → 2,356(14.1×)**・乗車意図 4,088 → **成立率 57.6%**・乗車待ち 3,031・打ち切り 655・ホームなし 0・掃除 28・**降車 0(不変)**・呼 49,847 → 49,687・会話 48 → 35・保存則 OK(Σ運賃 30,060 → 424,080 = 2,356 × 180 円)・センサス残差 0/ゲート PASS・乗客保存則 在圏 2,661 + 乗車中 **0** + 域外 2,339 = 5,000(**RIDING の取り残し 0**)。
- **変わった golden(既存テスト)**: `tests/engine/processes/test_rail.py` の 4 本 —(1)`test_congestion_caps_are_the_official_values`(2025 値へ・据置 3 行も明示)、(2)`test_boarding_without_a_train_returns_no_train` → **`…waits_on_the_platform`**(列車が居なくても失敗にせず待つ)、(3)`test_boarding_in_another_cell_returns_no_train` → **`…walks_to_the_nearest_platform`**(ホーム外は移動が組まれる)、(4)`test_alight_succeeds_only_while_the_train_is_at_the_platform`(通過型 dwell が 1 tick になったので**終端の井の頭線**の便で検査する形に変更)。新規 `tests/engine/processes/test_rail_board_intent.py` **11 本**(tick 列の固定・FIFO と quota・次の便で残りが乗る・打ち切り・保存則と RIDING 取り残し 0・意図の落ち方 4 本・決定論)+ `test_rail.py` に線別 dwell 1 本。
- **申し送り(親判断)**: ①**降車 0 は D-51 では直らない**——舞台の駅は渋谷 1 つなので「乗って降りる」が同一 tick でしか成立しない(乗ったら次 tick に域外へ出る)。方面・降車駅を持たせるのは第2陣。②mock ランは MockLLM が 12 語を一様に引くので乗車意図が呼の 8.2% になる(C7 本番の実 LLM は 64,784/3.9M = **1.7%**)。域外へ出た体は戻らないので、mock の 5,000 体ランでは 47% が域外に溜まる=**mock の数字を実 LLM の予測に使わないこと**。

**D-56 就寝中の起床抑止(`engine.arbiter`・`engine.run`・`shibuya.cli`・2026-09-10・ユーザー決定 (a))**:
> **知覚契約書・認知設計書の決定項は変更していない**(§6 の 4 クラス固定優先・不応期表・11 の起床条件はそのまま)。ここに登録するのは、繰り延べアービタの**入口に 1 段**「就寝中は起こさない」を足したことと、その実装で導入した自前規約・診断列・観測欄。設計書本文は書き換えていない。

- **症状(PENDING D-56)**: C7 本番 390,067 体で深夜 0〜5 時の LLM 呼が昼と同数(**毎時 107,520 = 按分上限そのもの**)。テープの「就寝」選択は 1 日 **229 回**だけ=**寝ている住民に移動/購入を選ばせていた**(営業時間外違反・購入偏重の一因)。候補の供給(内受容閾値・セル動的ブロック)は昼夜で変わらず、アービタは「起きているか」を見ていなかった。
- **根拠(答申 `docs/research/v2-c7-fix-research.md` §2・親一次確認済)**: 東京都 平日の起床率 a(h) = 0 時 20.5% / 1 時 11.1 / 2 時 5.7 / 3 時 3.5 / 4 時 5.3 / 5 時 15.3 / 6 時 40.7 / 7 時 72.2 / 12〜19 時 97.8〜98.9 / 22 時 74.9 / 23 時 46.2(平均 68.4%・令和 3 年社会生活基本調査 第 4-1 表)。交替制勤務 12.9%・若年層は夜型なので **a(h) を一律に掛けない**。就寝判定は**個体の状態**(`registry.activity == Activity.SLEEPING`)で行い、**a(h) は検証(深夜の呼数の照合)にだけ使う**。
- **規則**: `Arbiter.step(..., asleep=)` に個体別の bool を渡し、`arbitrate` の**①不応期より前**(⓪)で `asleep[agent] & ~sleep_exempt` の候補を落とす。落とした分は**破棄ではない**(§6 運用規定①と同じ=状態トリガは次回起床時に最新値を読む)。新規候補と**保留(pending)の両方**に効く=就寝に入った体の分は保留からも消える(`arbitrate` が合併後の配列に掛けるので掃除は自動・アービタに別口を足していない)。
- **例外は「条件」ではなく「源」で決める**(`WakeCandidates.sleep_exempt`・bool 1 本): 顕著行為由来の候補と変化検出由来の候補は**どちらも `CELL_BLOCK`** なので条件では区別できない。`engine.run` が候補を連結する場所で印を立てる — 計画境界 `p`(`PLAN_*` の 4 条件=**眠りから覚める境界を含む**)= 通す/変化検出 `d` = 落とす/会話ターン `c` = 通す(`resolve._UNADDRESSABLE` で就寝中には来ないが、来たら通す=片側だけ `CONVERSING` が残る事故を作らない)/顕著行為 `s` = 通す(火事・急病は寝ていても起こす)。
- **艦隊の再投入 `f` は条件で判定する(過剰抑止の宣言)**: 繰り延べになった呼は源を持ち帰れないので `condition <= PLAN_TRANSIT`(会話ターン 0 と `PLAN_*` 1-4)だけ通す。**顕著行為由来の再投入は `CELL_BLOCK` なので、その体が就寝に入っていれば落ちる**。実害は「答えの返らなかった呼を寝ている間は蒸し返さない」だけだが、**過剰抑止であることを明記する**。
- **診断列**: 不応期の `suppressed` とは**別列** `sleep_suppressed`(`DIAG_RUN_COLUMNS` の 23 列目・要約に `診断 sleep_suppressed: N`)。就寝抑止を**①不応期より前**に置いたので 2 列は**排他**(同じ候補が両方に計上されない)。`DIAG_COLUMNS`(予算宣言表 §7-5 の 4 列)と `RunResult.arbiter_counters` の形は**変えていない**。
- **観測欄 `calls_by_hour`(24 要素)**: 世界内時刻の時別の**発射数**(Σ = `llm_calls`)。時 = `(tick // 60) % 24`(開始 00:00 = テープ meta の `start_hour` と同じ約束)。要約に 1 行 `呼/時 00:… 23:…`。C7 受入はこの行から深夜 0〜5 時 / 昼 12〜19 時の合計を取り a(h) と並べる。`tools/c7/c7lib.parse_run_summary` は無改造で読める(`診断 \w+:` 行が 1 本増えるだけ・`呼/時` 行はどのパターンにも当たらない)。
- **腕(ablation)`sleep_suppression`(既定 True)**: `run_day(sleep_suppression=)`・`shibuya.cli --no-sleep-suppression`・`python -m shibuya.engine.run --no-sleep-suppression`。`False` = **D-56 前の挙動**(帰無腕)。`run_manifest_fields()` に欄を 1 つ足した(既定 `True`)。**理由**: ①効果の測定に帰無腕が要る、②`resolve.initialize` は tick 0(世界内 00:00)で**全員を `SLEEPING` に置く**ので、深夜だけを回す短いラン(艦隊・テープ・パーサの配管テスト = 8〜180 tick)は既定のままだと呼が 0 になる。
- **退化検査(挙動が変わる修正=checkpoint は変わって当然)**: 実資産 5,000 体 mock 1 日。**台帳つきの標準入口** `python -m shibuya.cli --agents 5000 --seed 1 --world data/world/v2` は checkpoint **`602f3bfb2b1aeefb…`(第133)→ `2cc12d4351738c44…`**・呼 49,687 → **41,742**・乗車 2,356 → 1,665・会話セッション 35 → 52・センサス 残差 0 / ゲート PASS 不変(sink 432,726 → 305,994)・`sleep_suppressed` 0 → **78,800**。以下の時間帯別は `python -m shibuya.engine.run`(台帳なし)の同条件ラン: checkpoint **`3ea0612e2e3a13df…` → `3b70d81deb3b0c5b…`**。呼 49,637 → **41,535**(−16.3%)・**深夜 0〜5 時 12,500 → 11,263(比 0.90)**・昼 12〜19 時 16,417 → 11,758(比 0.72)・就寝の選択 2,603 → 2,091・購入 1,200 → 918・移動 133,998 → 91,151・会話 1,147 → 1,066(セッション 41 → 54)・乗車 2,350 → 1,678・運賃 423,000 → 302,040・保存則 OK(Σ 35,064,083 不変)・センサス 残差 0 / ゲート PASS 不変・遵守率 0.6116 → 0.6115・`sleep_suppressed` 0 → **77,391**・`suppressed` 33,341 → 20,037・壁時計 14.2 → 11.7 s。
- **所見(a(h) との照合・親判断が要る)**: **深夜の呼は 10% しか減っていない**(0〜2 時は按分上限 2,083/時 に張り付いたまま)。実測した「起きている割合」は 00 時末 29.2% → 01〜05 時末 **42〜44%**(a(h) は 3.5〜15.3%)・12〜19 時末 **63〜66%**(a(h) は 97.8〜98.9%)。**原因は抑止の側ではなく「誰が寝ているか」の側**: `registry.activity` を `SLEEPING` にする口は ①`resolve.initialize` の一括代入(tick 0)と ②**LLM が「就寝」と答えたとき**(`resolve._apply_sleep`)の 2 つだけで、**W17 週次表は `activity` を書かない**。だから計画境界で起こされた体は答え次第でそのまま起きっぱなしになる(mock は 12 語を一様に引くので 11/12 で起き続ける。C7 本番の実 LLM は「就寝」を 1 日 229 回しか選んでいないので**同じ穴が本番でも開く**)。D-56 (a) は仕様どおり入ったが、**深夜の呼数を a(h) に寄せるには「就寝は世界が持つ状態」にする追加判断が要る**(候補: 就寝境界で `activity` をエンジンが `SLEEPING` にする / `activity` の初期値を W17 の 0 時時点の活動から作る)。
- **テスト**: 新規 `tests/engine/test_sleep_suppression_d56.py` **18 本**(内受容・セル変化は就寝中に呼ばない/第2陣の 4 条件も同じ/`PLAN_*` 4 条件は通る(parametrize)/同 tick に境界と内受容が立ったら境界だけ残る/**同じ `CELL_BLOCK` でも顕著行為の印があれば通る**/会話ターンは通る/保留が就寝開始で消える/`suppressed` と `sleep_suppressed` は排他/並び順不変(純関数)/真夜中の窓は呼 0・帰無腕は呼が立つ/最初の計画境界を跨ぐと呼が戻る/`calls_by_hour` の合計 = `llm_calls`/同 seed 2 回一致/深夜の呼の割合が帰無腕より小さい/tick 0 の種は全員 `SLEEPING`)。
- **変わった golden・既存テスト(全て「深夜だけを回していた」ことが原因)**:
  - **窓を延ばした**(最初の計画境界 = 合成日課の起床 tick 300-480 を跨ぐ長さにした): `tests/engine/test_ablation23_switches.py` `_run` 180→**540** tick・`tests/engine/test_undefined_action.py` `SMALL` 120→**540**・`tests/engine/test_tape_wiring.py` `SMALL` 180→**540**・`tests/engine/test_renderer_wiring.py` 2 本(240→540・300→540)・`tests/engine/test_conversation_invite.py` 1 本(200→540)。
  - **帰無腕で回した**(8〜90 tick で艦隊/テープの配管だけを見るので窓を延ばせない): `tests/engine/test_fleet_wiring.py`(`run_mock`/`run_fleet` に `NO_SLEEP_ARM`)・`tests/engine/test_tape_deferred.py`(`common()` と v1 テープ 2 本)。
  - **`tests/engine/test_ablation23_switches.py::test_refractory_scale_moves_the_run`**: 振る条件を `CELL_BLOCK` → **`INTEROCEPTION`**。寝ている体は動かないのでセル動的ブロックがほとんど変化せず、この fixture(800 体・25 セル・過程なし)では `CELL` クラスの候補が 0 件になり `CELL_BLOCK` の不応期を振っても 1 ビットも動かない(**D-49「③ は第2陣まで no-op」に `CELL_BLOCK` も並んだ**=親へ報告)。`INTEROCEPTION` / `PLAN_GENERAL` / `PLAN_TRANSIT` は動く。
  - **`tests/engine/test_fleet_wiring.py::test_conversations_need_awake_partners_so_night_only_runs_barely_open_any`**: 元の「成立率の比較」は帰無腕で残し、既定では**真夜中の窓は呼そのものが 0**という上位互換の主張を足した。
  - **`tests/engine/test_ledger_wiring.py::test_conservation_over_all_sectors_including_row`**: 「店舗の現金 = 売上(第1陣は店舗が支出しない)」が崩れた。**D-56 で軌道が変わり、この fixture(500 体・1 日)で初めて補充が 1 件成立した**ため。等式を科目で閉じる形へ = **店舗の現金 = 売上 − 域外仕入**(515 円)。第1陣で店舗が現金を出す口は域外仕入だけ(科目一覧が証拠)。
- **バイト**: `WakeCandidates` に bool 1 本(`sleep_exempt`)= 保留 1 行 25 → **26 B**(`ARBITER_PENDING_ROW_BYTES = 32` の宣言内・実測 `arbiter_backlog` は 158,720 → 116,128 B と**減った**)。個体 SoA(M1)には 1 バイトも足していない。

### D-61 域内居住者の帰りの便(2026-09-10・ユーザー決定 (a))

> 発端: D-51 で乗車が成立するようになった結果、**渋谷に家がある個体**(域内居住者)が乗車で域外へ出ると再入場の経路が無く、日末まで域外に溜まった(到着の事前割当は `_build_external_home` が**域外居住者だけ**に張るので、域内居住者には帰りの便が 1 本も無かった)。

- **規則**(`engine.processes.rail.RailProcess._assign_return`): 発車ブロックで `rail_depart` した乗客のうち `external_line < 0`(=起動時に域外居住でない)の体について、W17 週次表からその体の「**現在 tick より後**の最初の**域内活動**」の開始分 `want` を引き、**ホームへ入る時刻 `dep_tick - dwell + 1` が `want` 以上で最も早い便**に到着を割り当てる。到着は事前割当と**同じ経路**(`resolve.rail_arrive`・`n_arrivals`)を通る。
- **「域内活動」の定義 = `place_kind` ≠ 域外**(**追補・2026-09-10・親判断**・**expedient**)。当初の決定 (a) の逐語は「`target_cell >= 0`(行き先セルが解決している活動)」だったが、W17 は**「自宅」活動の 84% を `target_cell = -1` のまま**出す(day0 全 1,805,177 活動のうち解決済みは 26.9%=職場 300,006・自宅 139,702・学校 45,569 だけ。自宅 739,203・駅 354,805・飲食店 79,491 は未解決)。そのため逐語定義では 10:00 以降に「次の域内活動」を持つ体が 15% しか居らず(05:00 68% → 22:00 8%)、決定の趣旨(住民は戻る)が果たせなかった(実測: 帰りの便が付いたのは域内居住者の発車の 27.8%)。セルが未解決でも**渋谷の中の活動**(自宅・駅・飲食店・公園…)なら「その時刻に渋谷に居なければならない」ことは決まっているので、**場所種別だけで判定**する。到着後の位置はホームのセル(既存どおり)。**W17 側で自宅セルが解決されれば `target_cell >= 0` の条件へ戻せる**(判定は `agents.weekly.WeeklySchedule.inbound_starts` の 1 行)。
- **鉄道を迂回する過程の穴を塞ぐ**(**追補・同上**): `engine.processes.civic.LargeEventProcess` は 18:00 に域外の体 200 人を会場セルへ引き込み(`_arrive`)、21:00 に `resolve.rail_depart` を**直接呼んで**外へ出す(`_leave`)。本モジュールの発車ブロックを通らないので帰りの便が付かず、また引き込みが**帰りの便待ちの体を横取り**していた(旧測定で割当 409 に対し到着 396)。rail に公開口を 2 本足し、civic の当該 2 箇所からだけ呼ぶ: `assign_return_trains(ids, tick)`(退場者に帰りの便)・`drop_from_return_queue(ids)`(引き込んだ体の予約を落とす=`arrival_train` を `-1` に。**域外居住者の事前割当は触らない**)。到着側は待ち行列の行と `arrival_train` を**突き合わせて**から降ろすので、落とした予約・付け替えられた古い予約は発火しない(二重到着なし・保存則不変)。
- **線を選ばない理由**: 渋谷は**1 駅**で、どの線で戻っても降りるのは同じホームのセル群。乗換・所要時間を持たない第1陣では線を選び分ける意味がない(D-51 §8 の「到着便の割り当て=自分の外出時刻以降で最初の便」と同じ宣言)。同着の便は**便索引の昇順**で決める=決定論。
- **戻らない条件**(その日は域外滞在のまま=**乗客の保存則の分母**に残る): ① その日にもう域内活動が無い ② `want` 以降にホームへ入る便が無い(終電後)③ 週次表の無いラン(合成世界・`--no-population`)。①②は `no_return`、②だけを `return_no_train` にも数える。
- **域外居住者は対象外**: 事前割当(`_arr_order`/`_arr_start`)は静的なまま触らない。帰りの便は**便索引 → 待ち行列**の dict(動的)に積み、`entering` の便で `pop` して合流させる。`arrival_train` は割当時に書く(降車セルの引き先)。
- **結線**(`run.py` を変えずに週次表を鉄道へ届ける): `RailProcess` は `WorldProcessRunner` 経由で **mock 日課の実体**を握っているので、`agents.weekly.apply_to_mock_schedule`(tick ループの前に 1 回呼ばれる)が `object.__setattr__(mock, "weekly", weekly)` で週次表を**添付**する。データクラスのフィールドではないので `schedule_hash`・バイト予算・`dataclasses.replace` の等価性には効かない。テストは `RailProcess(..., weekly=)` / `attach_weekly()` で直に挿す。
- **索引**(`agents.weekly.InboundStarts`): その日の**域内活動**の開始分を体行ごとの CSR にして、`key = 体行*(1441)+開始分` を 1 回組む(`target_cell_at` と同じ手)。引きは `searchsorted` 1 本 = **個体数に比例する逐次ループなし**。
- **逐次ループ宣言(P4)**: 新設は 2 本とも**便数**ぶん(個体数に比例しない)。① 割当: 発車した乗客を割当先の便で `argsort` → 切れ目ごとに待ち行列へ積む(異なり数 ≤ 便数)。② 到着: その tick にホームへ入る便ぶん(実測 1〜3 本)。5,000 体 1 日で rail 過程の壁時計は **0.119 → 0.149 s**(1,440 tick 合計)。
- **バイト**: 個体 SoA(M1)に 1 バイトも足していない。増えるのは列車 SoA の `enter_tick`(便数 × 8 B・4,089 便 = 33 KB)と、**同時に域外に居る域内居住者ぶんの待ち行列**(int64 の断片。日末 実測 1,280 体 ≒ 10 KB)。
- **診断**(`counters()` / `summary()` の鉄道行。`run.py` は触っていない): `return_scheduled`(割当)・`return_arrived`(実際に降りた)・`no_return`(戻らない)・`return_no_train`(うち終電後)。
- **テスト**: 新規 `tests/engine/processes/test_rail_return.py` **15 本**(次の活動 250 分 → `enter_tick>=250` の最初の便で降りてホームのセルに居る・開始ちょうどの便を飛ばさない・**(vi) `target_cell<0` でも `place_kind`≠域外なら呼び戻す**/`place_kind`=域外の活動では呼び戻さない・次の域内活動が無い/終電後は戻らない・週次表なしは D-61 前の挙動・域外居住者の事前割当が壊れない・域外居住者に帰りの便を割り当てない(`arrival_train` を上書きしない)・**全 tick で保存則**(在圏+乗車中+域外=個体数)・同条件 2 回一致(census 列・counters・`arrival_train`)・**(vii) イベント退場者(21:00)に帰りの便が付いてホームへ戻る**/**イベント入場(18:00)で予約が落ち、古い割当が発火しない**(二重到着なし・全 tick で保存則)・`inbound_starts` は域外の行だけ落とす・`apply_to_mock_schedule` の添付)。既存の rail/board_intent/agents/civic のテストは無改造で PASS(**変わった golden は無い**)。
- **退化検査**(実資産 5,000 体 mock 1 日 `cli --agents 5000 --seed 1 --world data/world/v2`。**並行サブ AB が resolve/run を編集中**だったので、`_inbound_index` を `None` 固定にした腕を「前」として**同一プロセスで**測った=第134 の checkpoint とは別の基線):

| 欄 | D-61 off | 逐語 (a) `target_cell>=0` | **拡張 `place_kind`≠域外(採用)** |
|---|---:|---:|---:|
| 発車 便 | 4,089 | 4,089 | 4,089 |
| 乗車・域外へ出た乗客 | 1,617 | 1,682 | 1,876 |
| 到着降車 `arrivals` | 573 | 1,082 | **2,091** |
| 帰りの便 割当 / 到着 | 0 / 0 | 522 / 509 | **1,560 / 1,518** |
| 戻らない(うち終電後) | 1,580 (0) | 1,131 (0) | **276 (0)** |
| 日末の域外滞留 | **1,597(31.9%)** | 1,274(25.5%) | **482(9.6%)** |
| checkpoint 最終 | `e3aedc7631c7964e…` | `f13349bd652bb24e…` | `c96baf821c9a046f…` |
| 保存則 Σmoney | OK 139,575,428 | OK | OK |
| センサス | 残差 0 / PASS | 残差 0 / PASS | 残差 0 / PASS |
| 大規模イベント 入場/退場 | 200 / 200 | 200 / 200 | 200 / 200 |
| rail 過程 壁時計[s/日] | 0.119 | 0.150 | 0.172 |

- **所見(親への申し送り)**: 拡張定義でも **276 体はその日戻らない**(週次表のその日の残りが全て「域外」の活動=**設計どおり**)。終電後(`return_no_train`)は 0。**W17 が自宅セルを解決すれば逐語定義に戻せる**ので、上の 3 列は「どちらの定義でも保存則・センサスは動かない」ことの記録でもある。この修正は**鉄道と大規模イベントの経路だけ**を塞いだ——他に `resolve.rail_depart` / `resolve.place_at_external` を直接呼ぶ過程が増えたら、同じ 2 本の公開口を呼ぶ必要がある(現状の呼び手は grep で `civic.py` と `runner.py`(起動時の域外配置)のみ)。

### D-62 就寝は計画の実行(2026-09-10・ユーザー決定 (a)+(b))

> **知覚契約書・認知設計書・行動契約書の決定項は変更していない**(§6 の 11 起床条件・4 クラス固定優先・不応期表・§2.1 の 12 行動語はそのまま)。ここに登録するのは、**計画境界のうち就寝境界だけをエンジンの実行に回した**ことと、`activity` の初期値を週次表から立てたこと、およびその実装で入れた自前規約・観測欄・帰無腕。設計書本文は書き換えていない。

- **症状(PENDING D-62・D-56 の所見が起案)**: D-56(就寝抑止)を入れても深夜 0〜5 時の呼は 0.90 倍にしか減らなかった。原因は抑止の側ではなく「**誰が寝ているか**」の側で、`registry.activity` を `SLEEPING` にする口が ①`resolve.initialize` の tick 0 一括代入 ②LLM が「就寝」と答えたとき(`resolve._apply_sleep`)の 2 つしか無く、**W17 週次表の就寝境界は起床候補(`PLAN_SLEEPING`)を出すだけで `activity` を書かなかった**。mock は 12 語を一様に引くので 11/12 が起き続け、C7 本番でも 8B が「就寝」を選んだのは 1 日 229 回だけ。
- **根拠(答申 `docs/research/v2-c7-fix-research.md` §2・親一次確認済)**: 東京都 平日の起床率 a(h) = 0 時 20.5% / 3 時 3.5 / 5 時 15.3 / 12〜19 時 97.8〜98.9(令和 3 年社会生活基本調査 第 4-1 表)。**一律に掛けない**(交替制勤務 12.9%)=検証にだけ使う。
- **決定 (a) 就寝は計画の実行**: 週次表の**就寝境界に達した個体はエンジンが `activity = SLEEPING` にする**(`resolve.begin_planned_sleep`)。その境界では**LLM を呼ばない**(`engine.run` が起床候補から外す)。判断そのものは週次表=その個体が LLM で作った計画なので、**判断 1 回・実行は世界**(D-51 乗車の意図保持と同じ形)。**起床も対称**にした: 非就寝の計画境界(`PLAN_WORKING`/`PLAN_GENERAL`/`PLAN_TRANSIT`)に達した `SLEEPING` の体は `resolve.wake_from_plan` が `IDLE` に戻してから呼ぶ——**呼が繰り延べ・予算切れで落ちても起きる**(現実の起床は呼ばれ方に依存しない)。顕著行為で起こす道は D-56 の例外のまま(変更なし)。
- **決定 (b) tick 0 の初期化**: 週次表があるランは tick 0 の `activity` を**その日 0:00 時点の活動**から立てる(`weekly.initial_activity` → `resolve.set_initial_activity`)。写像 `weekly.ACTIVITY_TO_STATE` = 就寝→`SLEEPING` / 移動・乗車→`MOVING` / 休憩→`RESTING` / それ以外→`IDLE`。**週次表の無い合成世界・mock 日課は従来どおり全員 `SLEEPING`**(`resolve.initialize` の一括代入は残す)。`transit_state != 0`(域外滞在・乗車中)の体は**触らない**=`place_at_external` が立てた `WAITING` と rail の事前割当の整合を保つ。
- **意図の保持(`sleep_pending`・1 B/体・M1 の 0.003%)**: 就寝地(その活動の `target_cell`。未解決 `-1` なら `schedule.home_cell`)に居ない体は、その場で寝かせず**就寝地へ `target_node` を張って歩かせ** `sleep_pending = 1` を立てる。着いた tick に `resolve._apply_engine_step` が `SLEEPING` にする(乗車の意図保持と**同じ分岐の隣**)。別の行動を選べば意図は落ちる(`_SLEEP_KEEP_ACTIONS = (就寝, エンジン継続)`)・行き止まりでも落ちる。`board_line` とは排他(就寝を始めた体は乗車の意図を落とす)。
- **expedient(自前規約・この節が登録)**:
  1. **触らない体**: 就寝境界に来ても ①乗車中・域外滞在(`transit_state != 0`)②会話中(`CONVERSING`)③既に就寝中 は書き換えない。①は `transit_state` が乗客の保存則の分母だから(車内で寝る状態を作らない=第2陣)、②は片側だけ `CONVERSING` が残る事故を作らないため(D-56 の例外③と同じ理由)。**その日の就寝境界は 1 人 1〜2 回しか来ないので、触らなかった体はその日ずっと起きたままになる**(実測 5,000 体で 域外 1,378 件=下の所見)。
  2. **`ACTIVITY_TO_STATE` の写像**: 「勤務」「通学」に対応する `Activity` が無い(在席語は店頭滞在の `SHOPPING` だけ)ので `IDLE` に落とす。「乗車」は tick 0 では列車に乗っていないので `MOVING`(`target_node` は張らない=`engine_continuations` は拾わない)。
  3. **0:00 を覆う活動が無い体の既定 = `SLEEPING`**(`initial_activity(fallback=)`)。D-62 前の挙動(全員 `SLEEPING`)を「週次表が黙っている所」にだけ残す形。実資産では day0 の 0:00 に活動があるのは 390,067 体中 276,517 体(70.9%)。
  4. **歩いている間は起きている**(`MOVING`)。現実の「帰って寝る」は移動が先なので境界ちょうどに寝ないのは正しいが、経路が長いと就寝が遅れる(実測: 歩き出した 757 件のうちその日のうちに着いて寝たのは 201 件)。
- **観測欄 `wake_rate_by_hour`(24 要素)**: 各 tick の `activity != SLEEPING` の割合を時ごとに平均した「**起床率/時**」。測る場所は**アービタの直前**。域外滞在・乗車中は「起きている」に数える。要約に 1 行 `起床率/時 00:… 23:…` を `呼/時` の隣に足した。加えて `D-62 計画就寝 …` の 1 行(その場/着いて/歩行中/計画起床/寝かせなかった理由の内訳)。`tools/c7/c7lib.parse_run_summary` は**無改造で読める**(`診断 \w+:` にも他のどのパターンにも当たらない)。**診断表 `DIAG_RUN_COLUMNS` は 1 列も増やしていない**。
- **腕(ablation)`plan_sleep`(既定 True)**: `run_day(plan_sleep=)`・`shibuya.cli --no-plan-sleep`・`python -m shibuya.engine.run --no-plan-sleep`。`False` = **D-62 前の挙動**(就寝境界も LLM に判断させ、tick 0 は全員 `SLEEPING`)。`run_manifest_fields()` に欄を 1 つ足した(既定 `True`)。**理由**: 効果の測定に帰無腕が要る(下の退化検査はこの腕で測った)。
- **退化検査**(実資産 5,000 体 mock 1 日 `cli --agents 5000 --seed 1 --world data/world/v2`。**並行サブ AA が `rail.py`/`weekly.py` を編集中**で第134 の基線(呼 41,742・checkpoint `2cc12d43…`)は動いてしまうので、`--no-plan-sleep` の腕を「前」として**同一プロセス・同一ツリー**で測った=D-61 の効果は両腕に等しく入っている):

| 欄 | 前(D-62 off) | 後(D-62 on) | a(h) |
|---|---:|---:|---:|
| 呼 | 42,190 | **37,111**(−12.0%) | |
| 呼 0〜5 時 | 11,266 | **6,260**(比 0.56) | |
| 呼 12〜19 時 | 12,278 | 12,693(比 1.03) | |
| 起床率 00 時 | 0.201 | **0.185** | 0.205 |
| 起床率 03 時 | 0.435 | **0.250** | 0.035 |
| 起床率 12 時 | 0.661 | **0.743** | 0.978 |
| 起床率 18 時 | 0.665 | **0.713** | 0.989 |
| 就寝の選択(`reflections`) | 2,076 | 1,779 | |
| 計画就寝 その場/着いて(歩行中) | 0 | 1,193 / 602(1,516) | |
| 計画起床 | 0 | 4,674 | |
| 寝かせなかった 域外/乗車中/会話中/就寝済 | – | 636 / 0 / 0 / 3,580 | |
| 乗車 | 1,956 | 1,876 | |
| 会話セッション | 68 | 54 | |
| 移動(`moved`)/ 購入 | 96,959 / 947 | 119,676 / 1,096 | |
| `sleep_suppressed` / `suppressed` | 79,475 / 21,984 | 76,975 / 29,308 | |
| 保存則 Σ | 139,575,428 OK | 139,575,428 OK | |
| センサス | 残差 0 / ゲート PASS | 残差 0 / ゲート PASS | |
| 壁時計 | 19.4 s | 18.0 s | |
| checkpoint 最終 | `79a374b36c24be68…` | `c96baf821c9a046f…` | |

- **所見(親判断が要る)**: 深夜の呼は **0.90 倍(D-56)→ 0.56 倍**まで下がり、昼の起床率は 0.66 → 0.74 に上がった=方向は決定どおり。ただし **a(h) には届かない。届かない分は engine ではなく W17 週次表の側にある**(この 5,000 体サンプルで週次表そのものが言う起床率を測った値):
  - 当日(day0)に活動を 1 本も持たない体が **839/5,000(16.8%)**。この体は境界が 1 本も無いので**終日 `SLEEPING`**(D-62 前も同じ=呼ばれもしない)。昼の起床率の**上限が 0.83** になる。
  - 週次表が言う起床率(隙間を就寝と数える): 00 時 **0.055** / 03 時 **0.178** / 12 時 **0.663** / 18 時 **0.341**。**03 時は a(h)(0.035)の 5 倍・18 時は a(h)(0.989)の 1/3**。18 時に活動で覆われている体は 5,000 中 **1,887** しか無く(07 時 3,913 → 19 時 811 → 20 時 615)、**夕方から夜にかけて計画が抜けている**(1 体あたりの当日活動は平均 4.76 本)。
  - つまり engine 側(0.250 / 0.744)は「週次表 + 隙間で起きたまま」の合成で、**a(h) に寄せるには W17 の再生成か、隙間の扱い(次の活動まで寝かせる/前の活動を延長する)の決定が要る**。**これは D-62 の範囲外**なので、選択肢を PENDING へ起案する(親判断)。
- **テスト**: 新規 `tests/engine/test_plan_sleep_d62.py` **14 本**(就寝地に居れば境界で `SLEEPING`・居なければ歩いて着いた tick に寝る・乗車中/域外/会話中/就寝済は触らない(内訳の計数)・別の行動で意図が落ちる・`wake_from_plan` は寝ている体だけ起こし意図を落とす・1 日ランで就寝境界の呼が帰無腕より減り起床境界では呼が出る・顕著行為の例外は D-62 後も生きている(D-56 のテストと同じ道具)・0:00 の活動が 4 種の `Activity` に写る/隙間は fallback・`ACTIVITY_TO_STATE` の語彙一致・`set_initial_activity` は `transit_state != 0` を触らない/長さ不一致は例外・`boundary_events` は `boundary_events_full` の薄い包み・合成世界は tick 0 全員就寝・`起床率/時` の書式と manifest 欄・同 seed 2 回一致)。**変わった golden は無い**(既存テストは無改造で PASS)。
- **変わった golden・既存テスト(3 本・すべて「起きている体が増えた」ことが原因)**:
  - **`tests/c6/test_t5_order_bias.py`**(実データ 2 本): `_run` に **`plan_sleep=False`** を足した(`sleep_suppression=False` と同じ理由)。既定だと tick 0 の `activity` が W17 の 0:00 の活動から立つので、「24 tick の窓で誰が起こされるか」に**週次表という体ごとの共変量**が入り、層内 |ρ| の `mean_wake_tick` が **0.0784 > 0.05**(`selected_count` 0.0210・`wake_count` 0.0219 は閾値内)。これは `arbitrate` の並び順のバイアスではなく**構成のバイアス**で、種別(kind)の層別では落ちない。**T5 の判定を W17 込みにするかは親判断**(合成世界の T5 3 本は既定のまま PASS)。
  - **`tests/perception/test_b6_invite.py::test_end_to_end_only_the_real_renderer_lets_the_invitee_accept`**: 「招待文を読めない stub 側は承諾 0」が 358 招待中 **2 件(0.6%)**になった。原因は D-62 ではなく**既存の相手決定**——名指した相手が同一セルに居ないと `commit.pair_partners` が同席者へ差し替える(`conv_fallback_same_batch` 535 件)ので、同じセルで 2 人が同時に「会話」を選ぶと相互指名になる。起きている体が増えて初めて引いた。判定を**率**(承諾 ≤ 招待の 1%・発話ブロックは実レンダラの 5% 未満)へ変えた(実レンダラ 262 承諾/1,572 発話 vs stub 2/12)。
  - **`tests/engine/test_processes_run.py::test_c4_second_half_on_the_real_world`**: 9 過程の ActualLog「1 行以上」の輪から **`hotel_room_inventory` を外した**。ホテルのチェックインはこの fixture(5,000 体×1 日)で **0〜1 件の事象**で、D-62 で「就寝」の選択が 2,076 → 1,779 に減った結果 1 件 → 0 件になった。過程は変えていないので、代わりに**過程が有効で客室在庫が立っていること**(`runner.hotel.rooms_total.sum() > 0`・`counters()["checkin"] == res.hotel_checkins`)を見る。
- **バイト**: 個体 SoA に `sleep_pending` **1 B/体**(M1 30 KB/体 の 0.003%)。週次表側は増えない(`boundary_events_full` は既存列を返すだけ・`activity_at`/`initial_activity` は都度計算)。`RunResult` に 24 個の float(ラン全体で 1 本)。

## §9 構築工程(決定(仮)・2026-09-08・ユーザー「承認・完成まで漕ぎ着けて」・実行形=工程ごとに/goal+自動モード・出口でユーザー判断)

> 前提: CLAUDE.md §2-2「全て決めてから構築」。着手ゲート=世界データ構築仕様書(D-W1〜D-W22)+本§9の承認。**所要日数は親の推測**(サブ実装+親検収込み・並列度2)。GPU: サーバー返却(9/10)後はローカル1GPUのみ→C5後半以降(艦隊必須)は再借用/クラウドが前提。

- **(2026-09-09 追補・親)`cli --checkpoints-out PATH` / `--replay TAPE_DIR`**: 受入表 T2-a/b/c の入力。checkpoint 列(tick・agents/world/population/schedule ハッシュ・combined)と final_hash(全桁)を JSON へ。`--replay` は本番テープ(calls.parquet)を `mode=replay` で再生し(LLM 呼なし)、40 万体本ランの checkpoint 列を復元する=T2-c(自己整合)と「再生 final_hash = 本番 summary の 16 桁」の照合。既定=書かない・回さない(バイト不変)。tests/test_cli.py 3 本(c7_accept.selfconsistency が読める形・同 seed 2 ラン一致・既定で書かない)。パターン照合: T2 決定論(運用設計書 §1.4)の代替 3 本(E-C7-4)。

### 9.1 工程表(C0〜C8)

| 工程 | 内容 | 担当 | 検収(親・機械) | 依存 | 推測日数 | GPU |
|---|---|---|---|---|---|---|
| **C0 骨格** | リポ構造(manifest/build/core/world/agents/perception/llm/engine/economy/census)・import-linter層契約・pytest/hypothesis骨格・CI(GitHub Actions)・秘密スキャンpre-commit・予算宣言の機械読取(P/M/S/L行)・世界カタログ分母ファイル(SHA 34f9fa9d)・manifest正規化(pydantic) | 親+サブ1 | CI緑・層契約違反0・manifest往復一致 | — | 1-2 | 不要 |
| **C1 世界データ構築** | W0-W13(呼ゼロ)+W18被覆指標+W19 manifest凍結+W20検収パック。**サブA(地理)**=W0-W6/W8/W9/W11、**サブB(場・境界)**=W7/W10/W12/W13 | サブA・B | 段階ゲート表全合格・再構築でbuild_hash一致・目視検収パック(セル地図・出口45・騒音場画像) | C0・取得レーン(§3) | 5-8 | W8のみ(可視性・ローカル可) |
| **C2 エンジン核** | core(SoAレジストリ・dtype/バイト予算・Philox・ハッシュ)+world/agents SoA+engine(1分tick時計・スケジューラ・4クラス繰り延べアービタ・resolve単一書き込み口・二相コミット・録画テープ)+**mock LLM**+状態成長宣言(5欄) | サブC(core/engine)・サブD(agents/成長宣言) | 5,000体×1日 mock ≤10分(W2)・P2/P3/P6・M7≤2.0x・同seed同状態ハッシュ(T1/T2)・hypothesis性質テスト | C0(C1と並列可) | 5-8 | 不要 |
| **C3 知覚・LLM接続層** | レンダラB0-B6+チャネル上限+正規化規約9項+ハッシュ三役+変化検出+注意ゲート0-2+p_notice(2段ヒル)+パーサ(2行形)+未定義行動5段+行動契約12語+会話1呼1発話ブロック+診断行 | サブE(perception)・サブF(llm/契約) | goldenバイト一致(同セル2体B0-B4差分0)・契約テスト・チャネル上限テスト・mock 5,000体で診断行5本が出る | C1・C2 | 4-6 | 不要 |
| **C4 世界過程第1陣+経済+物** | 16行の第1陣(移動・占有/待ち行列・営業時間PlanSpec・鉄道静的ダイヤ+乗車§2.6・混雑場・騒音・天候・昼夜)+U-Goods骨格(補充・納品・廃棄物収集・屋内占有・断面交通)+**前倒し分(予算内で: 宅配・バス/タクシー・公共サービス出動・街路清掃・インフラ日負荷・ホテル客室・工事占用・報道・大規模イベント)**+U11 SFC(transfer単一API・検算2本・pytest 8本・faucet/sink列挙・月次センサス)+憲法5機械検査 | サブG(世界過程)・サブH(経済/物)・サブI(前倒し分) | 保存則テスト全合格・センサス残差閾値内・reaches/contributes検査・5,000体mockで16行の診断行 | C2・C3 | 8-12 | 不要 |
| **C5 母集団・生成** | W16母集団合成(40万体・CPU)→W14/W15静的言語化(T2・2,900呼)→W17スケジュール生成(T1・40万呼)→W18再算出 | サブJ(合成)・親(LLM生成の実行) | SRMSE/JSD/空セル0%・修正率<20%・文面凍結SHA・被覆指標WC-5 | C1・C4(PlanSpec) | 3-5(+艦隊12h) | W14/15=ローカル1GPU可・**W17=艦隊必須** |
| **C6 実LLMスモーク+運用テスト** | 艦隊接続(httpx×7・cache_salt・sha256_cbor)・24stepスモーク(5,000体・実LLM)・T3-T9(バッチ不変性・リプレイ・封印・dirty禁止)・指標B事前登録再測・ablation①(固定枠 vs 単一ランキング) | サブK(接続)・親(スモーク実行・検収) | 指標B・ablation①・L4/L6予算・T3-T9全合格 | C5 | 3-5 | **艦隊必須**(縮小は1GPU) |
| **C7 40万体×1日 本番相当** | サーバーで1日ラン(週7日表・第1陣全部)・壁時計≤24h・M8≤24GB・S1≤5GB・診断行・**holdout照合は事後1回のみ**(KDDI形状5指標) | 親 | 予算全行・決定論(同seed再ラン=T2)・被覆指標WC-6 | C6 | 2-3(+ラン24h) | **艦隊必須** |
| **C8 ablation・感度・計器盤** | ablation第1陣6本(20%予約枠)・expedient登録簿の感度試験・忠実度計器盤・アンサンブル運用(Phase 5) | 親+サブ | 各expedientの「結果を駆動していない」証明 | C7 | 継続 | 艦隊 |

**合計(推測)**: C0-C4≈**3.5-5週**(GPU不要=返却後もローカルで進む)、C5-C7≈**1.5-2週+艦隊時間**。C1∥C2で1週短縮。

**実績と改訂見込み(09-08夜・delta)**: C0 50分・C1∥C2 2.5h・C3 2h・C4 3h=**C0〜C4 合計≈8h**(推測 3.5-5 週に対し /goal 無人運転+サブ2並列で約 1/20)。C5〜C8 のコード側見込み(外部前提を除く): C5-a W16≈3-4h(前提=町丁目境界データ)・C5-b W14/W15≈1h+W17≈12h(艦隊)・C6≈4-6h+スモーク(艦隊)・C7=準備 2-3h+ラン ≤24h(艦隊・返却延長が前提)・C8=ablation 6本×ラン(継続)。**律速は外部前提(境界データ・GPU 艦隊・実 LLM 時間)であってコード工数ではない**。工程地図と前提の対応は PENDING.md §5。

### 9.2 サブ配分の規律(CLAUDE.md §5の工程への適用)
- 1サブ=1コンポーネント(層契約の1層)・同時起動≤2・**コミット禁止**・子サブ禁止。
- 親検収=ディスク実在+親自身のpytest+**実データ規模退化検査**(5,000体で通っても40万体SoAでRSS/秒を測る)。
- サブの完了報告は「テスト名と結果表」を要求(自己申告の「完了」は不採用)。
- 各工程の出口で PENDING→IMPLEMENTED 移動・devlog・予算書の実測欄更新・expedient登録簿の追記。

### 9.3 順序依存と並列
C0 → {C1 ∥ C2} → C3 → C4 → C5 → C6 → C7 → C8。C5のW16(合成)はC1直後に前倒し可(CPUのみ)。W17はC4のPlanSpec完成後。

### 9.4 GPU計画(返却後)
- ローカル1GPU: W8可視性・W14/W15(8B/32B INT8・2,900呼)・縮小スモーク(500体×24step)。
- 艦隊必須: W17(40万呼≈12h)・C6フル(5,000体×24step)・C7(40万体×1日)。**再借用/クラウドの決定はC5着手前**(C0-C4の3.5-5週の間に判断)。

### 9.5 /goal運用の細目(決定(仮)・09-08・ユーザー「§9.5でいく」=(a)〜(h)採用)

> 出典=Claude Code公式ドキュメント「Claudeをゴールに向かって動作させ続ける」(code.claude.com/docs/ja/goal)と「モデル設定」(同/model-config)。親が09-08に実読。

**(a) /goalの仕様(原典の要点)**: セッションスコープの**プロンプト型Stop hookのラッパー**。作業モデルがターンを終えるたびに、条件文と会話全体が「小さく高速なモデル」(既定Haiku)へ送られ、yes/noと短い理由が返る。noなら理由を次ターンの指針として作業が続く。評価器は**ツールを呼ばず、トランスクリプトに表示されたものだけ**を判定する(ファイルもコマンドも独立には見ない)。条件は最大4,000文字・`or stop after N turns`で上限を切れる・`/goal`で経過ターン/トークン/最新理由を確認・`/goal clear`で解除・`--resume`で復元(カウンタはリセット)。権限は変えないので**自動モードと併用**が前提。

**(b) 評価器モデルの差し替え**: 評価器=「バックグラウンド機能に使用するモデル」で、環境変数 `ANTHROPIC_DEFAULT_HAIKU_MODEL` が「`haiku`に使用するモデル、またはバックグラウンド機能に使用するモデル」を制御する(model-config 環境変数表)。したがって**Fable 5.1のモデルIDを指定すれば評価器もFableになる**と読めるが、**未検証**(①/goalが同変数を参照するかは文書上の推論 ②アローリスト外へのリダイレクトは不可 ③背景機能全体が同モデルになりコストが上がる ④Fableの安全分類器フォールバック)。**C0着手前に自明なゴール(例: `pytest -q`が通る)で1回だけ試験し、評価器の理由文のモデル痕跡と`/goal`のトークン支出で確認**する。

**(c) 検証の主体**: 評価器は「達成の証拠がトランスクリプトに出ているか」の門番にすぎない。**検証そのもの=親(Fable)のpytest実行・ディスク実在確認・実データ規模退化検査**(CLAUDE.md §5)を作業側が毎ターン行い、その出力を会話に残す。サブ(Opus)の完了報告は証拠にしない。評価器が弱いモデルでも、条件文が「証明コマンドと期待出力」を要求していれば騙されにくい。

**(d) 条件文の型**: 終了状態1つ(測定可能)+証明手順(コマンドと期待する出力)+不変制約(触らないもの)+停止句(ユーザー判断が必要な分岐に出会ったらPENDINGに書いて停止/Nターン)。

**(e) 自律中の判断規則(CLAUDE.md §2-3「拡張は先に聞く」との両立)**: 設計書が沈黙する細部(変数名・ファイル分割・テスト件数・expedientの初期値)は**設計書のexpedient登録簿に追記して続行**。**パターン台帳の行・予算宣言(P/M/S/L)・ライセンス台帳・憲法6原則・設計書の決定項に触れる変更**は実装せずPENDINGに分岐を書いて**ターンを終える(=停止句に該当・ゴール達成扱い)**。

**(f) コミット規律**(**09-08改定・ユーザー「お願いする」**): 作業はブランチ(`build/c0-c4`)で行い、**工程出口で§9.6層2(別Fableの独立検収)に合格したら親がブランチへコミットする(ユーザー確認不要)**。**mainへのマージのみユーザー**。中間はワーキングツリーに置く。秘密スキャンは新規/変更ファイル全部に対して実行してからコミット。旧規則(出口でユーザー確認後に1回)は無人運転のため廃止。

**(g) 記録**: 工程内はマイルストーンごとにdevlogへ1行、出口で1エントリ(TRACE要素の更新も1行=G-3)。PENDING→IMPLEMENTEDの移動は出口で。

**(h) C0条件文の草案(約1,500字・4,000字以内)**:

```text
/goal 工程C0(骨格)を docs/design/v2-implementation-plan.md §3・§6・§9.1 のとおり完成させる。完了の定義(すべて満たし、証拠をこの会話に出力で示すこと):
1. src/ 配下に manifest/build/core/world/agents/perception/llm/engine/economy/census の各パッケージが存在し、import-linter の層契約(§3の上→下のみ・循環禁止)が設定され、`lint-imports` が違反0で終了した出力が表示されている。
2. `pytest -q` が exit 0 で終了し、passed件数を含む出力が表示されている。テストには少なくとも: manifestの正規化→シリアライズ→再読込の往復一致、予算宣言表(P/M/S/L行)の機械読取、世界カタログ分母ファイルのSHA-256が 34f9fa9d で始まること、hypothesisの性質テスト1本以上、が含まれる。
3. .github/workflows にCI定義があり、ローカルで同じコマンド列(lint-imports・pytest・秘密スキャン)が通っている。
4. `python tools/scan_secrets.py` を新規・変更ファイル全部に対して実行し CLEAN が表示されている。
5. docs/log/devlog.md に工程出口のエントリ、PENDING.md/IMPLEMENTED.md の更新が行われている。
制約: docs/design/ 配下の設計書の決定項を書き換えない。data/ を git に追加しない。git commit はしない(親がユーザー確認後に行う)。サブエージェントの完了報告は証拠にせず、親自身が pytest を実行した出力のみを証拠とする。
停止句: 設計書に無い決定でパターン台帳・予算宣言・ライセンス・憲法に触れる分岐に出会ったら、その分岐を PENDING.md に書いて停止する(この停止もゴール達成として扱う)。または 40 ターン経過で停止する。
```

### 9.6 無人運転(制限中断からの自動再開)と二重監視の構成(**一部決定・09-08**: (d)コミット規律=採用/層3 OpenAI=現時点では使わない/使用量クレジット=説明後にユーザー判断・保留/CLI更新=親が実施 2.1.179→2.1.263・VS Code拡張は2.1.263で同梱バイナリ/**09-08夜追記(ユーザー回答)**: 使用量クレジット=**使わない**(「止まったら仕方ない」=制限時は開いたセッションで待ち自動再開・週次制限のみ手動)・PC=画面オフのみ(スリープ無効)・サーバー疎通=09-08 18:48 OK(7×A5000 空き)・R16=仮決定(決定台帳・推奨どおり)・実装再開=ユーザー合図待ち)

> 出典=Claude Code公式ドキュメント(英語版 .md を親が09-08に実読): interactive-mode「Wait for a usage limit to reset」・goal「Errors you have to fix clear the goal」「Background work defers evaluation」「Evaluation model and cost」・hooks「prompt and agent hook fields」・costs「Add usage credits」・scheduled-tasks「Limitations」・settings-reference `autoContinueAtUsageLimit`。リサーチサブ(claude-code-guide)の報告は親が原典で再確認し、「/goalは制限解除後に自動再開する」という推論部分を原典の文言に差し替えた。

**(a) 制限中断からの自動再開=公式機能(要バージョン更新)**
- 事実: 「claude.aiの使用量制限がタスク途中でClaudeを止めたとき、Claude Codeは開いたセッション内で待ち、制限がリセットされた後にタスクを自分で続ける。自動継続はclaude.aiサブスクリプションでサインインした対話セッションで既定ON。**v2.1.234以降が必要**」。リセット時は「固定プロンプトで止まった所からタスクを拾う(最後のメッセージは再送しない)」。連続ヒットは「最大2回まで自動で再武装、その後停止し `/rate-limit-options` を促す」。
- 条件: セッションを開いたままにする(閉じると待ちは復元されない)。PCが**約30分超スリープ**すると `press enter to continue` になる=手動。権限プロンプトが出ると止まる→**自動モード必須**。`-p`/バックグラウンドセッションには提供されない。**週次制限(リセットが24時間超先)は自動で待たない**=手動再開が1回要る。設定 `autoContinueAtUsageLimit`(User or managed・既定ON)。
- 現状: ローカルCLIは 2.1.179 だった→**09-08 親が `claude update` を実行し 2.1.263 へ**。VS Code拡張(anthropic.claude-code)は既に **2.1.263** で自前の同梱バイナリ(resources/native-binary/claude.exe)を使う=自動継続(2.1.234+)・/goal復元(2.1.239+)・待機中チェックイン(2.1.236+)の要件をすべて満たす。
- /goalとの関係(原典): 「レート制限や過負荷などの一時的エラーの後、Claude Codeはゴールを有効のまま残す」。ゴールをクリアするのは認証失敗(VS Code拡張などホスト管理下では残す)・クレジット枯渇・auto-compactで解けないコンテキスト溢れ・モデル利用不可の4種のみ。再開時は「全経路でゴールを復元(v2.1.239+)・ターン数/タイマー/トークン基準はリセット」。サブや背景シェルが動いている間は評価をスキップし、**30分→1時間→2時間の間隔で待機中チェックインを自発ターンで最大3回**(v2.1.236+・`CLAUDE_CODE_GOAL_CHECKIN_MINUTES`で変更)。
- 使用量クレジット(`/usage-credits`・Pro/Max): 制限を超えて継続できる(有料)。待ち中に追加すれば即時再開。**採否=ユーザー**(コスト)。

**(b) 監視の層(二重構造の推奨形)**
| 層 | 何が見るか | 実体 | 強さ | 備考 |
|---|---|---|---|---|
| 0 決定論ゲート | テスト・層契約・秘密・予算 | CI(GitHub Actions)+ローカル pytest/import-linter/scan_secrets/予算テスト | **最強** | モデル非依存・騙せない |
| 1 ターン門番 | 「達成の証拠が会話に出ているか」 | /goal評価器 or 自前のprompt型Stop hook | 中 | 評価器はツール不可=文面判定のみ |
| 2 工程出口の独立検収 | 設計適合・テストの実在・登録簿・台帳不変 | **別インスタンスのFable**(Agentツール model:"fable")が固定チェックリストで敵対的レビュー・pytestを自分で再実行 | 強 | 合格までコミットしない。任意で /code-review ultra(ユーザー起動・課金) |
| 3 他ベンダー(任意) | 工程報告+差分要約への第三意見 | command/http型hookまたは出口スクリプトからOpenAI APIを呼ぶ | 弱〜中 | 文面のみ・助言扱い(ログ)。要OPENAI_API_KEY(環境変数のみ)・工程粒度でコスト小。誤りの相関が低いのが利点 |
- 層1の評価器モデル: 原典「別のモデルで評価するには `ANTHROPIC_DEFAULT_HAIKU_MODEL` を設定」+警告「小型高速モデルを使う全所(haikuエイリアス・会話要約などの背景機能)に効く」。**代替=自前のprompt型Stop hookに `model` フィールド**(hooks原典: 「評価に使うモデル。既定は高速モデル」)でFableを指定すれば、背景機能を巻き込まずに「もう一つのFable」が毎ターン採点できる。agent型hook(実験的・Read/Grep/Globを使って検証・既定タイムアウト60秒)はファイルを自分で見られる=層1と層2の中間。
- 親の見立て: 自律構築で最も起きやすい事故は「証拠なき完了申告」と「テストを弱めて通す」。これを止めるのはツールを持つ層0・層2であり、文面だけを見る層1・層3ではない。同一モデルの監視は盲点が相関するが、層0が非モデルなので致命ではない。**推奨=層0+層1(Fable Stop hook)+層2**。層3はOpenAIキーがあれば工程出口に追加(未決)。
- 監視は制限中断を防がない(別問題)。制限は(a)で、監視は(b)で扱う。

**(c) 「最後まで作る」の到達点と、ユーザーが避けられない判断**
- C0〜C4(骨格・世界データ・エンジン核・知覚/LLM接続・世界過程/経済/物)はGPU不要=無人で到達可能。
- C5後半(W17スケジュール生成40万呼)〜C7(40万体×1日)は**艦隊GPUが必須**。サーバー返却(9/10)後の再借用/クラウド/縮小(ローカル1GPU)の選択=R16と一体で、**C5着手前にユーザー判断が1回必要**(C0〜C4の間に選択肢と費用を用意して提示)。
- 週次制限に当たった場合の手動再開(1回/週)と、PCを起こしておくこと(スリープ無効)はユーザー側の前提。

**(d) §9.5の改定案(無人前提)**: (f)コミット=「工程出口で親が1回・ユーザー確認後」→**「層2合格後に親がブランチへコミット(確認不要)・mainへのマージのみユーザー」**。(g)報告=工程出口ごとに `docs/ops/build-report-Cn.md` を書き、ユーザーは後から読む。停止句は維持(台帳・予算・ライセンス・憲法に触れる分岐)。

**(e) 開始手順(ユーザー側・一度だけ)**: ① `claude update`+VS Code拡張更新(2.1.234+を確認) ② PCのスリープ無効・セッションを開いたまま ③ 自動モード ④ (任意)`/usage-credits` ⑤ /goal投入(C0〜C4通し条件文=親が用意) ⑥ (任意)OpenAIキーを環境変数で。
