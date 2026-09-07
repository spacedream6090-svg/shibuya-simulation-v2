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
