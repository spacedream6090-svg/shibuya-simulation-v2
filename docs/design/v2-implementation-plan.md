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

**(f) コミット規律**: 作業はブランチ(例 `c0-skeleton`)で行い、**コミットは工程の出口で親が1回・ユーザー確認後**(既存の§6運用のまま)。中間はワーキングツリーに置く。秘密スキャンは新規/変更ファイル全部に対して実行してからコミット。

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
