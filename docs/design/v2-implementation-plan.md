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
