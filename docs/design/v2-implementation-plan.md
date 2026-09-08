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
- ledger: 同一支払者の重複行は前置和で判定・生ログ 24 B×262,144 行・保持窓 1 日→日次集約(D-R2-6)・貨幣供給量 M=世帯+店舗+雇用主の現金+預金・成長宣言係数 3 transfer/体/日・cap(6.29/16/512 MB)は親按分=要 delta。検算①=行和 0・**列和=Δ現金**(Caiani の Δ行を陽に持たない形)+Δ預金−Δ借入=0。
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
- (C4 層2レビュー指摘で追記・09-08) crowd: 想定床面積表 FLOOR_AREA_M2_BY_CAT(既定 80 m²)・流れ 3 値の閾値 STILL_SHARE 0.20/COHERENT 0.50。goods: SKU の質量/廃棄率(弁当 350 g・5%/飲料 500 g・1%/日用品 200 g・0%/定食 400 g・8%/ドリンク 300 g・2%/衣料 300 g・0%)・納品ログ 16 B×131,072 行・**sell_many は累積スロット払い出し**(旧「最初の非空スロット」を訂正)。goods_flow: DELIVERY_LOT_FACTOR 2。rail: 表に無い線の既定容量 1,200 人/混雑率上限 139%・§2.6(ii)(混雑率→内受容・停車時間)は未実装・(iii)乗り残し率は診断行へ追加(C4-fix)。salient: SALIENCY_BY_KIND 4 組・セル代表距離 25 m・密度 3 値の境界 2/4・d50 放送 60 m。civic: PRESS_BODY 文面・同セル複数ホテルの先頭寄せ。resolve: _SELL_SLOT_RETRIES 8(保険)。logistics: バス位相 stop_cell % headway・宅配端数の小数部降順配分。**日次センサスは閉じた日の DayClose で評価**(修正前は畳んだ後の空行列を見ていた=C4-fix)・D-R2-6 のラン終端ゲートに O(t) ログ(ActualLog/transfer_log/納品ログ)の実測を追加(C4-fix)。B4b の行列は renderer.prepare_tick(queues=) で結線済み(crowd.py の旧注記を訂正)。
## §9 構築工程(決定(仮)・2026-09-08・ユーザー「承認・完成まで漕ぎ着けて」・実行形=工程ごとに/goal+自動モード・出口でユーザー判断)

> 前提: CLAUDE.md §2-2「全て決めてから構築」。着手ゲート=世界データ構築仕様書(D-W1〜D-W22)+本§9の承認。**所要日数は親の推測**(サブ実装+親検収込み・並列度2)。GPU: サーバー返却(9/10)後はローカル1GPUのみ→C5後半以降(艦隊必須)は再借用/クラウドが前提。

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

### 9.6 無人運転(制限中断からの自動再開)と二重監視の構成(**一部決定・09-08**: (d)コミット規律=採用/層3 OpenAI=現時点では使わない/使用量クレジット=説明後にユーザー判断・保留/CLI更新=親が実施 2.1.179→2.1.263・VS Code拡張は2.1.263で同梱バイナリ)

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
