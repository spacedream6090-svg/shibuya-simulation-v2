# レーンI答申: 実装スタック(言語・ランタイム・ABM基盤・エンジン構造・データ層・CI)

<!-- hdr:v1 -->
- **分野**: ソフトウェア工学 #29 / 計算機科学(並列・決定論) #28 | **重要度**: P1(親判断・2026-09-15 第191)
- **一次確認**: **B** = 出典あり・空欄を明示(残務台帳へ写し済みまたは要写し) — 出典痕跡 55 件。空欄節あり
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **分野地図**: [v2-discipline-map.md](v2-discipline-map.md)

> **親検収(Fable・2026-09-07)**: 出典を親が一次確認した。✔=親が実読して一致。
> - ✔ NVIDIA/numba-cuda README(実読): 「Numba-CUDA is in maintenance mode. Moving forward, we intend to support only security issues and critical bug fixes through the lifetime of CUDA 13.」(新機能はNumba-CUDA-MLIRへ)→A3のGPU実装手段を`numba.cuda`以外(Warp第一・CuPy第二)にする根拠は事実。
> - ✔ AMBER(arXiv 2601.16292・抄録実読): 列指向Python ABM・「speedups of up to 1118×」vs Mesa・最大の空間SIRベンチでAgents.jlを上回る(**1.2倍という数値は抄録に無い=本文値・親未再読**)。
> - ✔ FLAME GPU 2(SPE 2023・White Rose OA PDF実読): 「conflict can be resolved through a process of bidding, in which agents simultaneously 'bid' for their desired location with only the highest priority agent allowed to perform the movement」「able to simulate 1M agents in ∼0.003 s per time step」。**「atomic演算の順序は非決定」の逐語は親の抽出で見つからず**(bidding・性能値は一致)。
> - ✔ vLLM公式(design/prefix_caching・engine_args実読): sha256(pickle)は「Hashes may not be reproducible across different Python or vLLM versions」・`sha256_cbor`=「reproducible, cross-language compatible hash」・`cache_salt`=先頭ブロックのハッシュに注入され同じsaltの要求だけがKVを再利用。**R16検証ランは`--prefix-caching-hash-algo sha256_cbor`+ラン種別ごとのcache_saltを宣言**(答申の提案は妥当・U8 manifestに追加)。
> - ✔ httpx公式(実読): Limits既定=max_keepalive_connections 20・max_connections 100・keepalive_expiry 5。L6(64 in-flight/GPU×7=448)には既定値が不足=レプリカごとに`Limits(64,64,None)`。
> - S2(checkpoint≤17GB/日)とM1(12GB)×M7(≤2.0x)×4回/日=生24GB/日の算術的緊張は事実(予算書の改訂候補)。
> - 空欄(RTX 5070 sm_120のwheel対応・Ruriスループット・blake3/xxhashライセンス・Mesa 3大規模ベンチ・numba vs Rust同一ABM査読ベンチ)は答申の申告どおり。
> - 正典化: docs/research/v2-implementation-stack-research.md(実装計画ラウンドの根拠)。

> 作成: 2026-09-07 / リサーチサブ(Opus 5) / 親=Fable検収・決定=ユーザー
> 規律遵守: 子サブ未起動。出典は正規ドメインのみ。**実読ページからの引用のみ**を「引用」として提示。
> 読めなかった・見つからなかった項目は **空欄(未確認)**。推測は **【推測】**。
> リポジトリは読み取りのみ(書き込み・コミットなし)。Webからのファイル保存は行っていない(WebFetchのツール側キャッシュを除く)。

---

## 要約(10行)

1. **言語決定案 = Python 3.12 + NumPy/Numba(CPU)+ CuPy or NVIDIA Warp(GPU)。既決A3/A4を変更する理由は見つからなかった。** ただし GPU 層の部品選択には後述の重大な変更が要る。
2. **Numba の CUDA ターゲットは「保守モードのみ」に移行した**(NVIDIA公式リポの実読: "Numba-CUDA is in maintenance mode…only security issues and critical bug fixes through the lifetime of CUDA 13")。**A3の「GPU(CUDA)対応」を numba.cuda で書く前提は今すぐ見直すべき**。代替は CuPy(elementwise/RawKernel)または NVIDIA Warp(Apache-2.0・CPU/CUDA両バックエンド・Windows/Linux/macOS wheel)。
3. **「配列指向Pythonは40万体で足りる」の裏付けが2026年に出た**: AMBER(arXiv 2601.16292・Polars列指向)は 5,000体50step で Mesa 比 **最大1118.6倍**、SIR で **Agents.jl より1.2倍速い**。v1の失敗はPythonではなく**個体オブジェクト逐次ループ**だったことを外部データが裏付ける。
4. **ABM基盤は全て「使わない・参考にする」**。Mesa は Agents.jl 比 **24.9〜125.6倍遅い**(Agents.jl論文Table 2・実読)。FLAME GPU 2 は 1M体 0.003秒/step だが CUDA専用・モデルを自前DSLで書く形で LLM 非同期I/O と噛み合わない。**FLAME GPU 2 の sub-model bidding だけは思想輸入**する。
5. **二相コミットの外部先例が確定した**: FLAME GPU 2 論文(実読)は「**アトミック演算の順序は非決定的でGPUの実行モデルが決める**」ため優先度が意味を持つ競合は sub-model の **bidding**(提案→セルが優先度で順位付け→確定移動)で解けと明記。v2の reserve→arbitrate→commit と同型=**expedientでなく先例つき mechanism**。
6. **決定論の部品は既製で足りる**: `numpy.random.Philox`(カウンタベース・key/counter直接指定可・`advance`/`jumped`)+ `blake3`(PyO3製・Apache/CC0)。**vLLM 自身がプレフィクスキャッシュのブロックハッシュに sha256/sha256_cbor/xxhash を使い、`cache_salt` で名前空間を切る**(実読)=v2の「ハッシュ三役」と同じ設計思想が艦隊側にも既にある。
7. **LLM接続は「vLLM OpenAI互換サーバ + httpx.AsyncClient(bounded semaphore)」を推奨、オフライン `LLM.generate` は不可**。vLLM公式が「オフラインentrypointは同期レンダラで**逐次**処理」と明記(実読)+ 再現性ページが「オンラインは batch invariance のみ」と明記(リポ既収載)。
8. **データ層 = Parquet(ログ・診断・センサス)+ DuckDB(集計)+ npz/mmap(checkpoint)**。DuckDB は「クエリに必要な列だけ読む」「フィルタをスキャンに押し下げzonemapで読み飛ばす」(実読)。**40万体×1日の見積り: LLMテープ 4.8GB raw(zstd後 1.2-1.6GB【推測】)・診断行 160-240MB・checkpoint 24GB raw/日**。**個体×tickの全記録は 5.76億行/日=禁止**(セル別集計へ)。
9. **CI の性能ゲート(P5=+10%)は GitHub Actions 共有ランナーでは誤検出する**。相対比較(同一ジョブ内でbaselineとcandidateを交互測定)+ 絶対時間ゲートはセルフホスト機限定、の二段構えを推奨。
10. **最大のリスク3件**: (a) numba.cuda 保守モード (b) ローカル機 RTX 5070 = Blackwell sm_120 の各ライブラリ対応が**未確認** (c) 単一プロセス asyncio に GPU 計算と 400万呼/日のHTTPを同居させたときの GIL 干渉(実測が要る)。

---

## 問い1. 言語とランタイム

### 1.1 要件の再確認(リポから)

| 要件 | 出所 |
|---|---|
| 40万体・基本tick=1分・秒オフセット | A8(v2-redesign.md 行「構築前の即決8項」) |
| 配列指向・逐次禁止・CPU(numba)/GPU(CUDA)両対応・サーバー第一 | A3(同上) |
| Python 3.12・`src/shibuya/{world,agents,perception,llm,engine,census,diag}`・pytest+mock | A4(同上) |
| P1 GPU物理 ≤50ms/フレーム@40万体 / P2 CPU numba ≤5ms@5千体 / P3 ≥10万イベント/秒 | v2-budget-declaration.md §2 |
| M8 RSS ≤24GB(64GB機で2ラン並列が下限) | 同 §3 |
| L4 400万呼/日・L6 64 in-flight/GPU | 同 §4 |
| ハード: 借用7×A5000(9/10返却)→ ローカル Win11・20コア・31GB・RTX 5070 12GB + クラウド都度 | 親の背景記述 |

### 1.2 候補比較

| 候補 | 40万体の物理・集約 | LLM非同期I/O | CPU/GPU両対応 | Win/Linux | 1人+AIサブでの保守 | 判定 |
|---|---|---|---|---|---|---|
| **Python + NumPy/Numba(+CuPy/Warp)** | 配列指向なら十分(§1.3の実測) | asyncio+httpx が最も自然 | numba(CPU)/CuPy・Warp(GPU) | ○ | ◎(既決A4・v1資産・サブが書ける) | **本命** |
| Rust(PyO3)コア + Python制御 | 最速級・SoA自然 | Python側で従来通り | GPU は別途 cust/wgpu で自作=重い | ○ | △(ビルド鎖が二重・サブの生産性が落ちる) | **代替1案(部分適用)** |
| Julia(Agents.jl) | 最速級(§1.3) | HTTP.jl はあるが vLLM 生態系は薄い | CUDA.jl は良質 | ○ | ✗(既決A4を全否定・v1資産全捨て・サブの熟練度が不明) | 不採用 |
| C++ コア + pybind11 | 最速 | 同上 | CUDA直書き | ○ | ✗(1人+AI体制で最も高コスト) | 不採用 |
| Taichi | GPU/CPU両対応・SoA/AoS選択可・JIT | Python側で可 | CUDA/Vulkan/Metal/CPU | ○ | △(生態系が小さい・数値ライブラリが薄い) | 参考(GPU物理のみ候補) |
| **NVIDIA Warp** | 粒子系・空間ハッシュの primitives が揃う | Python側で可 | **CPU(x86-64/ARM)とCUDAの両方に同一カーネルをJIT** | Win/Linux/macOS wheel | ○(Pythonのまま書ける) | **GPU層の第一候補** |

### 1.3 実測ベンチ(引用)

**(a) AMBER: 列指向Python ABM(arXiv:2601.16292・HTML版を実読)**
- 条件: 「The independent variables are framework (seven implementations as listed above), population size (500, 1,000, and 5,000 agents), and simulation length (50 steps).」
- 環境: 「Experiments were conducted on an Apple Silicon laptop running Python 3.12.7 and Julia 1.12.3.」/ 版: 「AMBER 0.3.1, Mesa 3.4.1, AgentPy 0.1.5, SimPy 4.1.1, Melodie 1.0, and Polars 1.32.2.」
- 5,000体・50step の実時間: **Wealth Transfer** AMBER(vectorized) **21ms** vs Mesa **23,917ms** / **Random Walk** **6.2ms** vs **141ms** / **SIR** **687ms** vs **17,967ms**。
- 比率: Mesa 比 **1117.6×**(wealth transfer)、Melodie 比 30.9×、AgentPy 比 17.5×、**Agents.jl 比 1.2×(SIR)**。
- ライセンス: 「AMBER is released under the BSD 3-Clause licence」
- **v2への含意**: 「Pythonだから遅い」は誤り。**遅いのは個体オブジェクト逐次ループ**であり、列指向(SoA)にすれば Julia の ABM 専用フレームワークと同等域に入る。v1の RAM 13.6倍・逐次の罠は言語選択でなく**データレイアウトの罪**だった、という外部証拠。
- 注意: これは**5,000体**の測定であって40万体ではない。40万体域の外挿は本答申では**空欄(未確認)**。ただしv2のPhase 2ゲート(A1: 5,000体×1シミュ日)はまさにこの規模=**AMBERの数値がそのままPhase 2の到達目標の目安になる**。

**(b) Agents.jl 論文 Table 2(arXiv:2101.10072・PDF本文を実読)**
- 「Table 2. Benchmarks of four model types across four ABM frameworks. Run-times are normalised against the Agents.jl time, thus a value of 2x means it took twice as long to complete the benchmark in the respective framework.」
- Agents.jl 4.4 を 1 としたとき(Mesa 0.8 / NetLogo 6.2 / Mason 20.0):
  - Flocking(連続空間): Mesa **26.8×** / NetLogo **10.3×** / MASON **2.1×**
  - Wolf-Sheep-Grass(格子): Mesa **31.9×** / NetLogo **10.3×** / MASON 実装なし
  - Forest Fire(格子): Mesa **125.6×** / NetLogo **53.0×** / MASON 実装なし
  - Schelling(格子): Mesa **24.9×** / NetLogo **8.0×** / MASON **14.3×**
- **v2への含意**: **Mesa は候補から外れる**(v2規模ではオーダーが2つ足りない)。ただしこれは Mesa 0.8 の測定であり、Mesa 3(2025・AgentSet導入)は未測定=**空欄(未確認)**。

**(c) FLAME GPU 2(Softw. Pract. Exper. 53(8), doi:10.1002/spe.3207・White Rose OA版PDFを実読)**
- 「our benchmark model, which is representative of a wide range of continuous space, particle type models, is able to simulate **1M agents in ∼0.003 s per time step** using spatial partitioning and our run time compilation approach.」
- 「Our Sugarscape model demonstrating the use of sub modelling is able to simulate an environment size of **16M agents in ∼1 second per time step**.」
- 「A conservative estimate for a V100 device is that population sizes exceeding **100M** are feasible.」
- **v2への含意**: **P1(≤50ms/フレーム@40万体・GPU)は極めて安全側の予算**。連続空間・粒子型で 1M体 3ms/step(V100級)が2023年に出ている以上、40万体50msは 17倍の余裕がある。**予算の緩さ側の裏付け**として台帳に置ける。

**(d) 【推測】/ 未確認**
- 「単一スレッドで Julia は Rust より約4倍速い(ABM)」という検索結果由来の主張が出たが、**一次ページを実読していないため採用しない(空欄・未確認)**。
- numba vs Rust vs C++ の**同一ABMでの**査読ベンチは本調査では見つけられなかった=**空欄(未確認)**。近いものとして arXiv:2303.06195(Julia/Python+Numba/Kokkos on exascale nodes)があるが本文未読。

### 1.4 GPU可搬性(重要な変更点)

**Numba の CUDA ターゲットの状態が変わった**。NVIDIA/numba-cuda リポジトリ(実読):
> 「Numba-CUDA is in maintenance mode. Moving forward, we intend to support only security issues and critical bug fixes through the lifetime of CUDA 13.」
ライセンスは BSD-2-Clause。加えて Numba 本体のドキュメント(検索結果より・本文未読=**要親確認**)は 0.61 で内蔵CUDAターゲットを非推奨化、0.62 で警告、0.63 以降で削除、と段階を宣言している。

→ **A3の「GPU(CUDA)対応」の実装手段として numba.cuda を既定にするのは今からでは筋が悪い**。推奨は:
- **第一候補: NVIDIA Warp**(github.com/NVIDIA/warp・実読)。「Warp is a Python framework for GPU-accelerated simulation, robotics, and machine learning.」「PyPI wheels on PyPI for Windows (x86-64), Linux (x86-64 and AArch64), and macOS (Apple Silicon).」「Apache-2.0 license」。**同一カーネルソースが CPU と CUDA の両方にJITされる**=A3「CPU/GPU両対応」を1本のコードで満たす唯一の候補。
- **第二候補: CuPy**(NumPy互換API+`ElementwiseKernel`/`RawKernel`)。NumPy コードの移植コストが最小。ただし CPU 側は NumPy/Numba で別実装になる(コード二重化)。
- **Blackwell(RTX 5070 = sm_120)対応は未確認**。CUDA Toolkit 12.8 が sm_120 を含むことは複数の二次情報が言うが、**CuPy / Warp / Numba-CUDA の公式wheelが sm_120 を含むかは本調査で確認できず=空欄(未確認)。親の一次確認候補**(ローカル機での実行可否そのものが懸かる)。

### 1.5 Rust(PyO3)の位置づけ

PyO3公式(pyo3.rs・実読): 「Rust bindings for Python, including tools for creating native Python extension modules.」「PyO3 is licensed under the Apache-2.0 license or the MIT license, at your option.」maturin でビルド。

**推奨は「全面採用しない・ホットスポット限定の逃げ道として宣言だけしておく」**。理由:
- v2の律速は LLM(W3で宣言済み・step内訳で物理≤10%)。**言語を速くしても律速が動かない**。
- 1人+AIサブ体制では、Rust コアはビルド鎖(maturin・クロスコンパイル・Win/Linux両wheel)と検収コストを二重にする。CLAUDE.md §5「サブの完了報告は信用せず親のpytestで検収」の運用が、Rustだと親側のビルド環境依存で重くなる。
- **移行条件を先に宣言しておく**(§8(a))。

---

## 問い2. ABM基盤の採否

| 基盤 | 版/ライセンス | 判定 | 理由(引用つき) |
|---|---|---|---|
| **Mesa** | Mesa 3系・Apache-2.0 | **使わない** | Agents.jl論文Table 2で Mesa 0.8 は 24.9〜125.6× 遅い。AMBER論文で Mesa 3.4.1 に対し 1117.6× の差(5,000体)。**個体オブジェクト+スケジューラ**というv1の失敗形そのもの。Mesa 3 の AgentSet は改善だが、40万体域の測定は**空欄(未確認)** |
| **Repast4Py** | BSD-3(GitHub Repast/repast4py) | **参考にする** | MPI分散のPython ABM。「leverages Numba, NumPy, and PyTorch packages, and the Python C API」(検索結果・本文未読)。v2は**単一ノード+外部LLM艦隊**が形なので MPI 分散は不要(むしろ M8/RSS と checkpoint を複雑にする)。**参考にする点=「ghost agent(境界の複製)」の語彙**が、v2の境界=来街(U10 方面別外界ノード)の実装語彙に流用できる可能性【推測】 |
| **Agents.jl** | Julia・MIT | **参考にする** | スケジューラ設計が最も整理されている。公式(実読要点): 「The schedulers of Agents.jl … all schedulers are functions that take the ABM as input and return an iterator over agent IDs」。**「スケジューラ=ID列を返す関数」という抽象がv2にそのまま移植できる**(engine/scheduler の型シグネチャ)。既定は「コンテナ順=任意」・`Scheduler.ByID`・`Scheduler.Randomly`・`Scheduler.ByProperty` |
| **FLAME GPU 2** | v2.0.0-rc24 以降・**MIT**(論文実読: 「FLAME GPU 2 v2.0.0-rc24 is open source under a permissive MIT licence」) | **参考にする(思想輸入)** | 採用しない理由: (i) CUDA専用=A3の「CPU/GPU両対応」を満たさない (ii) モデルを FLAME GPU の agent function DSL で書く形=v2の「LLMが意思決定器」「非同期HTTP待ち」と噛み合わない (iii) 「there is a roughly one second run-time overhead on first execution of a simulation」(RTC)。**輸入するもの=並列意味論**(§3.3で詳述) |
| **MATSim** | Java・GPL | **参考にする** | 交通需要側(U10来街・PT/交通センサス較正)の語彙。エンジンとしては採用しない。**本調査では本文未読=空欄(未確認)** |
| **NetLogo** | 教育用 | **使わない** | Agents.jl比 8.0〜53.0× 遅い。40万体は非現実 |
| **AMBER** | BSD-3・arXiv:2601.16292(2026) | **参考にする(強)** | Polars列指向テーブル+ビューAPIという構成そのものが v2 の agents/SoA 層の設計図。**採用しない理由**は、v2の状態がM1-M6の細かいバイト予算つきで、可視性テーブル・記憶埋め込み・関係疎表現など Polars の列型に載らない構造を含むため。**設計を読む価値は最も高い** |
| **ABMax(JAX)** | arXiv:2508.16508 | **空欄(未確認)** | 本文未読。JAX/XLA 路線は「LLM待ちのasyncioと同居しにくい」【推測】ため優先度低 |

**結論: 既製ABM基盤は使わない。**v2の要件(外部LLM艦隊への400万呼/日の非同期I/O・二相コミット・繰り延べアービタ・バイト一致観測レンダラ・バイト予算のCIゲート)はどの基盤の中核とも競合し、基盤を使うと**基盤の意味論を回避するコードのほうが大きくなる**。

---

## 問い3. エンジン構造(部品表つき)

### 3.1 ECS/SoA

- **採る形**: 「1コンポーネント = 1本の NumPy 配列(dtypeを宣言)」。エンティティ = 行番号。**個体オブジェクトを作らない**。
- 参照実装として読む価値があるのは AMBER(Polars列テーブル+ビューAPI)。ただし v2 は **NumPy structured array ではなく「フィールドごとの独立1次元配列 + dtype レジストリ」**を推奨。理由: M9(全フィールドにバイト予算宣言+テスト強制)を**配列1本=台帳1行**で機械検査できる形にするため。
- チャンク化: **セル単位(100m格子・139セル)を第一のチャンク**にする。既決のセル格子(A7・100mセル原点固定)と揃うので、可視性テーブル(M10・mmap)・観測レンダラのB2/B4ブロック・prefixキャッシュキーが**すべて同じ境界**に乗る。
- 【推測】チャンク内の並べ替え(セル移動時のコンパクション)は「削除=tombstone + 定期コンパクション」が定石。頻度と閾値は expedient として宣言し、感度試験対象。

### 3.2 イベント駆動スケジューラ

- 骨格: **1分tick(A8)+ tick内の秒オフセットで起床順**。tick境界で「今tickに発火する事象」を配列で取り出し、tick内は δ_perc(秒) の昇順。
- 部品: 標準ライブラリ `heapq`(優先度キュー)で足りる。**ただし逐次heapqを40万体の主ループに置いてはならない**(P4宣言対象)。推奨は **「tickバケット配列 + tick内は np.argsort によるベクトル整列」**=heapqは「1分より遠い未来の予約」だけに使う二層構造。
- 抽象は Agents.jl 由来: **`scheduler(state) -> ndarray[int64]`(起床する個体IDの配列を返す純関数)**。テストで「同じ状態 → 同じID配列」を強制。

### 3.3 二相コミット(外部先例が確定した)

FLAME GPU 2 論文(実読)から、**v2の設計に直接効く3つの引用**:

> 「Atomic operations permit agents to manipulate values directly. This form of communication is well suited to agents consuming some form of resource within the environment ensuring that race conditions are not introduced. **The order of the atomic operations is non deterministic and determined by the GPU's execution model**, as such, if agent priority plays an important role in manipulating the environment then this 'conflict' between agents (in obtaining a resource) is best resolved using the sub-model approach described later in this article.」

> 「In parallel, conflict can be resolved through a process of **bidding, in which agents simultaneously 'bid' for their desired location with only the highest priority agent allowed to perform the movement. Priorities can be randomly assigned to agents and stored as an agent variable to achieve fairness, as in the serial case.**」

> 「The transactional bidding process consists of agent functions to allow agents to (1) propose a movement to a new cell location, (2) for a cell location to rank competing agents by the agent's assigned priority and for the cell to communicate a confirmation of its preferred choice of agent, (3) perform movement of the agent whose preference is confirmed.」

さらに、**反復回数が実測で理論最大より小さい**ことも報告されている:
> 「The results of the Sugarscape model in Figure 11B, demonstrate that resolution of movement as a result of competition, can be achieved in far fewer resolution steps than the theoretical maximum of 9.」

**v2への含意(重要)**:
1. v2の `reserve → arbitrate → commit` は **FLAME GPU 2 の (1)propose (2)rank (3)move と1対1対応**する。既存答申(v2-run-manifest-concurrency-research.md 要約8)が「先例=FLAME GPU 2」と書いているのは正しく、本調査でも同じ引用で確認できた。
2. **「優先度をエージェント変数として持たせて公平性を担保」**という形は、v2の `pk = (ceil_ns(t_notice), BLAKE3(run_salt‖tick‖resource_id‖agent_id))` と同型。**v2側はさらに「乱数だが再現する」を満たす**ぶん強い。
3. **反復回数を固定にせず「未解決者数のリダクションを終了条件にする」**という設計は v2 も採るべき。既決の「再試行は同一tick内で1回(第2希望)、以降は次tick」は**打ち切り側**なので、**未解決者数を診断行に必ず出す**(打ち切り禁止=憲法1の監査点)。

### 3.4 決定論(カウンタベースRNG)

**部品: `numpy.random.Philox`(NumPy同梱・BSD-3)。追加ライブラリ不要。**
NumPy公式(実読):
> 「Philox is a 64-bit PRNG that uses a counter-based design based on weaker (and faster) versions of cryptographic functions.」
> 「The Philox state vector consists of a 256-bit value encoded as a 4-element uint64 array and a 128-bit value encoded as a 2-element uint64 array. The former is a counter which is incremented by 1 for every 4 64-bit randoms produced. The second is a key which determined the sequence produced. **Using different keys produces independent sequences.**」
> 「Philox can be used in parallel applications by using a sequence of distinct keys where each instance uses different key.」
> `advance(delta)`: 「Advance the underlying RNG as-if delta draws have occurred.」

**v2への実装形**: 既存答申の `u = PRF(master_seed, domain_id, tick, entity_id, draw_index)` は、Philox を **`key = f(master_seed, domain_id)` / `counter = g(tick, entity_id, draw_index)` として直接構成できる**(`Philox(key=..., counter=...)` が公開API)。→ **「逐次的な状態を持つ乱数生成器を作らない」というv2規律が、既製ライブラリだけで満たせる**。
- manifest欄: `rng_scheme: "numpy-philox4x64"` + `domain_table_version`(既存答申の欄をNumPy実装名で埋める)。
- 注意: NumPy の Philox は **4×64bit**(Random123 の philox4x32 とは別変種)。答申案の `philox4x32-10` という文字列は**実装に合わせて訂正が要る**。
- 【推測】numba の nopython 内から Philox を直接叩くのは非対応のため、GPU/numbaカーネル内で乱数が要る場合は **カーネル内に Philox の丸め関数を自前実装**(30行程度)するか、**CPU側で乱数配列を先に生成して渡す**。後者を既定にすると「乱数消費が実行順に依存しない」ことがテストで示しやすい。

### 3.5 状態のチャンク化と変化検出ハッシュ

- **要件**: P6(変化検出 ≤2ms/tick@40万体・139セル)。B2/B4 のバイト列ハッシュが「prefixキャッシュキー・変化検出器・dormant再送抑止」の三役(知覚契約書)。
- **部品候補**:
  - `blake3`(PyPI・oconnor663/blake3-py・実読: 「Python bindings for the official Rust implementation of BLAKE3, based on PyO3」「The basic API matches that of Python's standard `hashlib` module」・`max_threads` あり、ただし「Note that this can be slower for inputs shorter than ~1 MB」)。**manifest・データ資産・封印のハッシュはこちら**(暗号学的・改竄検出が要件)。
  - `xxhash`(PyPI・xxHash bindings)。**tickごとの変化検出はこちら**(非暗号・短入力で速い)。
- **重要な整合**: vLLM 自身がプレフィクスキャッシュのブロックハッシュで同じ三択をしている。vLLM公式(docs.vllm.ai/en/stable/design/prefix_caching/ ・実読):
  > `--prefix-caching-hash-algo`: **sha256**(既定)「Uses Python's `pickle` for serialization. **Hashes may not be reproducible across different Python or vLLM versions.**」/ **sha256_cbor**「Uses `cbor2` for serialization, providing a **reproducible, cross-language compatible** hash.」/ **xxhash**「Uses Pickle serialization with xxHash (128-bit) for faster, non-cryptographic hashing.」
  > ハッシュの構成要素: 「The hash value of the parent hash block.」「A tuple of tokens in this block. The reason to include the exact tokens is to reduce potential hash value collision.」「Other values required to make this block unique, such as LoRA IDs, multi-modality input hashes …, and **cache salts to isolate caches in multi-tenant environments**.」
  > `cache_salt`: 「injected into the hash of the first block, ensuring that only requests with the same salt can reuse cached KV blocks.」
  > 追い出し: 「Pop the block from the head of the free queue. This is the LRU block to be evicted.」
- **v2への含意(3つ)**:
  1. **検証ラン(R16・BATCH_INVARIANT)では `--prefix-caching-hash-algo sha256_cbor` を宣言すべき**。既定 sha256 は「Pythonやv版をまたいで再現しない」と公式が明言しており、**manifestが「同じ入力→同じキャッシュ挙動」を主張できなくなる**。これは既存答申(U8/U9)に無い新しい発見。
  2. **`cache_salt` は v2 の艦隊運用に直接使える**: 「較正ラン」と「holdout照合ラン」で salt を変えれば、**KVキャッシュの相互汚染が構造的に不可能**になる(L3=勘定分離の実装手段)。これも既存答申に無い。
  3. LRU追い出しは、リポのベンチ第3段結論2「セル128超ではLRU追い出しの定常状態」と機構が一致=ベンチ解釈の裏取り。
- **P6の実装**: セルごとの B2/B4 バイト列を `bytes` に組んで `xxhash.xxh3_64_intdigest` を139回。139回のPythonループは許容(P4の「逐次ループ新設」に当たるが、規模が139=宣言すれば通る)。個体側B5の閾値判定は40万要素の配列比較=ベクトル化。**2ms/tick は【推測】達成可能**だが、Phase 2 で実測に差し替え(予算表の改訂条件どおり)。

### 3.6 録画リプレイ(LLM入出力テープ)

- v2は既決で「**リプレイでなく直接記録**が正典」(恒久記録=全LLM入出力)。テープは (a) 恒久記録 (b) mock再生の入力、を兼ねる。
- **形式推奨**: **1呼=1行の Parquet**(zstd)、列 = `{call_id, run_id, tick, sim_time_ns, agent_id, wake_class, model_id, prompt_block_ids[], prompt_individual_text, params_hash, output_text, prompt_tokens, completion_tokens, ttft_ms, e2e_ms, server_replica, finish_reason, deferred_from_tick}`。
  - **共有ブロック(B0-B4)は本文を書かず `block_id`(そのブロックのBLAKE3)だけ**を書き、別テーブル `blocks.parquet` に intern する。これで容量が1桁落ちる(§5の見積り)。
  - `params_hash` = temperature/top_p/max_tokens/stop の正規化ハッシュ。
- **リプレイの意味論**: `(agent_id, tick, wake_class, prompt_hash)` をキーに完全一致で引く。**一致しなければ「テープ外」として即座に失敗**(黙って実LLMへフォールバックしない)。テープ外率を診断行に出す。

### 3.7 部品表(問い3範囲)

| 用途 | 部品 | 版の指定方針 | ライセンス | 備考 |
|---|---|---|---|---|
| 配列 | NumPy | ≥2.1 を下限に固定(Python 3.12) | BSD-3 | Philox 同梱 |
| CPU JIT | Numba | 0.61系以降を固定 | BSD-2 | **CUDAターゲットは使わない** |
| GPU カーネル | **NVIDIA Warp**(第一) / **CuPy**(第二) | Warp: PyPI `warp-lang` を版固定 | Warp: **Apache-2.0** / CuPy: MIT | Warp は CPU/CUDA両バックエンド。**sm_120(RTX 5070)対応は未確認** |
| 暗号ハッシュ | `blake3` | 版固定 | 空欄(未確認・リポにLICENSEはあるが種別未読) | manifest・資産・封印用 |
| 高速ハッシュ | `xxhash` | 版固定 | 空欄(未確認) | 変化検出・prefixキー用 |
| 優先度キュー | 標準 `heapq` | — | PSF | 遠未来予約のみ |
| RNG | `numpy.random.Philox` | NumPyに従う | BSD-3 | カウンタベース |

---

## 問い4. LLM艦隊との接続

### 4.1 オフライン `LLM.generate` vs サーバー方式 → **サーバー方式一択**

vLLM公式(検索結果で得た文言・**本文の当該行は未読=親確認事項**):
> 「The OpenAI-compatible API server uses the async renderer path to parallelize tokenization, chat template rendering, and multimodal preprocessing across concurrent requests.」
> 「The offline LLM entrypoint uses the synchronous renderer path and **processes prompts (including multimodal preprocessing) serially**.」

リポ既収載の実読事実(v2-run-manifest-concurrency-research.md §2.1):
> オフラインはマルチプロセス無効化 or batch invariance、**オンライン(=v2が使うOpenAI互換サーバー)は batch invariance のみ**。

**判定: サーバー方式。**根拠4つ:
1. **DP7 = 7プロセスの独立サーバー**という既決の艦隊形はサーバー方式でしか組めない(ベンチ第3段「DP7線形性100.2-100.4%」は7サーバーへの同時発射の実測)。
2. オフラインは逐次レンダラ=**400万呼/日の前処理がそこで詰まる**。
3. エンジン(numba/CuPy・GIL・大きなSoA)と vLLM(torch・CUDAコンテキスト)を**同一プロセスに同居させるとRSS予算M8≤24GBが即死**する。**プロセス境界が予算の防波堤**。
4. 艦隊はランより長生きさせられる(サーバー起動コスト・重みロードをラン間で償却)。24stepスモークの反復が速くなる。

### 4.2 非同期バッチクライアントの形

**推奨: `httpx.AsyncClient` + `asyncio.Semaphore` の二層バウンド。**(`aiohttp` でも可だが、httpx は同期/非同期の同一API=テストで同期クライアントに差し替えやすい。)

httpx公式(実読):
> `max_keepalive_connections`: 「number of allowable keep-alive connections, or `None` to always allow. (Defaults 20)」
> `max_connections`: 「maximum number of allowable connections, or `None` for no limits. (Default 100)」
> `keepalive_expiry`: 「time limit on idle keep-alive connections in seconds, or `None` for no limits. (Default 5)」

**設定の帰結(重要)**: 既定の `max_keepalive_connections=20` は **L6=64 in-flight/GPU に足りない**。7レプリカ×64 = **448 in-flight** を張るなら、レプリカごとに別クライアントを立て、各々 `Limits(max_connections=64, max_keepalive_connections=64, keepalive_expiry=None)` にする。**既定のまま走らせると、keep-alive枯渇で毎リクエストTCP+TLSハンドシェイクが起き、TTFTが静かに悪化する**(v1の ulimit=1024 の罠と同種の「静かに壊れる」型)。

```
FleetClient
 ├ replicas: [ReplicaClient(url_i, httpx.AsyncClient(limits=Limits(64,64,None)), sem=Semaphore(64)) × 7]
 ├ submit(req) -> Future            # 呼び出し側は await するだけ
 ├ 内部: bounded queue(全体上限 = 7×64 = 448)
 └ backpressure: queue満杯なら submit が待つ = 繰り延べアービタが「入れられない」を検知して繰り延べる
```

- **バックプレッシャの意味論(v2固有)**: キューが満杯のとき、**呼を捨ててはならない(憲法1)**。繰り延べアービタへ「入らなかった」を返し、**次tickへ繰り延べ+診断行に計上**(予算表 運用規則5「繰り延べ量を起床クラス別/シミュ日で必ず記録」)。
- ベンチ根拠: 「**並行度の膝はc=64/GPU**(KV使用率0.58)。c128でKV1.00に張り付きTTFTのみ悪化→bounded queue上限=64 in-flight/GPUが実測推奨値」(リポ docs/bench/README.md 第3段結論4)。**L6=64はここから来ている**。

### 4.3 prefix cache を効かせるリクエスト順序制御

ベンチの支配変数順位(リポ実測): ①prefix共有深さ(1.6-2.0x)>②出力長>③並行度>④mnbt>>⑤NUMA(0%)・⑥投機的デコード(負)。

**実装規則(4つ)**:
1. **ブロック順序は `[全体 → 種別 → セル → 個体]` 固定**(BN-5: 種別非依存セル節はv1サイズで−4%=不採用)。
2. **同一 (セル, 時間帯) の呼をまとめて連続発射**する。vLLM の APC はブロックハッシュ連鎖なので、**同じ前置ブロックを持つ呼が時間的に近いほどヒットする**。tickごとに「セルキー昇順で整列 → その順に submit」。
   - ただし **セルアフィニティ・ルーティング(セル→特定GPU固定)は不採用**(BN-4: Zipf不均衡のコストが常に上回る)。**同一GPUに寄せるのでなく、同一時刻に寄せる**のが結論。
3. **ラウンドロビンでレプリカへ配る**(rank mod 7 は有利側バイアスの疑いがベンチ第5段の未測定欄にある)。**推奨: `xxhash(call_id) mod 7`** で内容非依存の均等分散。負荷不均衡が出たら「最短キュー選択(least-in-flight)」へ切替。
4. **`cache_salt` を実行モード(smoke/calibration/holdout/ablation/production)ごとに変える**(§3.5の含意2)。

### 4.4 タイムアウト/再試行の意味論(繰り延べアービタと接続)

| 事象 | 扱い | 診断行 |
|---|---|---|
| 接続エラー・5xx | **同一レプリカへ即時1回再試行 → 失敗なら別レプリカへ1回** | `llm_retry_n` |
| タイムアウト(既定: TTFT 60s / e2e 300s【推測・要実測】) | **その呼は破棄せず「繰り延べ」**。次tickの起床キューへ再投入。tick跨ぎの繰り延べ回数に上限を置かず、**回数分布を診断行に出す** | `llm_deferred_by_timeout` |
| 書式エラー(2行形の不順守) | 1回だけ再生成(温度0)→ なお不順守なら**「未定義行動5段」の意味論へ**(行動契約書) | `llm_format_error` |
| キュー満杯 | **submitがブロックせず即座に「入らなかった」を返す**(非ブロッキング) → アービタが繰り延べ | `llm_backpressure_defer` |

**設計上の要点**: 「タイムアウト=破棄」にすると**憲法1(打ち切り禁止)違反が静かに入る**。**タイムアウトは繰り延べの一種**として実装し、繰り延べ量を必ず記録する。これは予算表 運用規則5 の直接の適用。

### 4.5 埋め込み(Ruri-v3-30m)

Hugging Face モデルカード(cl-nagoya/ruri-v3-30m・実読):
- パラメータ: 「37M」(埋め込み除くと「10M」)
- 埋め込み次元: 「256」
- 最大長: 「Supports sequence lengths up to 8192 tokens」
- ライセンス: 「Apache License, Version 2.0」
- 入力接頭辞: 空文字 / 「トピック: 」/「検索クエリ: 」/「検索文書: 」
- JMTEB 平均: 「74.51」

→ **リポの M4(記憶 ≤6.1KB/体・Ruri-v3-30m 256次元int8・40万体で2.4GB)と一致**。

**推論スタック**:
- 部品: `onnxruntime`(CPU EP)+ `sentence-transformers`(`backend="onnx"`)。sentence-transformers 公式リリースノート(v5.1.0・実読要点): 「ONNX and OpenVINO backends offering 2-3x speedups」。CPU の量子化まで含めた比較は公式ドキュメントの図に入っており**本文からは数値を取れなかった=空欄(未確認)**(取れた文言は 「In the full backend benchmark below, fp16 with Flash Attention and input unpadding was the fastest configuration measured (3.87x over fp32, comparing each backend at its best batch size)」= これはGPU側の話)。**int8量子化で ~3.2x(onnx-qint8)/~5.3x(openvino-qint8)** という数値は検索要約経由で本文未確認=**親の一次確認候補**。
- **Ruri-v3-30m の実スループット公開値は見つからなかった=空欄(未確認)**。Phase 2 で自前測定が要る(37Mパラメータ・256次元なら CPU 20コアで数千文/秒級と**【推測】**するが、根拠なし=expedient)。
- スレッド設定(onnxruntime公式・実読):
  > `intra_op_num_threads`: 「Controls the _total_ number of INTRA threads to use to run the model. INTRA = parallelize computation _inside_ each operator」既定「INTRA Threads Total = Number of physical CPU Cores.」
  > 「Onnxruntime also allow customers to create a global intra-op thread pool to prevent overheated contentions among session thread pools.」
  > 「There are multiple sessions run in parallel, customer might prefer their intra-op thread pools run on separate cores to avoid contention.」(`session.intra_op_thread_affinities`)
- **v2への含意**: 埋め込みは既決どおり**別プロセス**(v2-cognition-design.md)。**既定の「物理コア数」設定のままだと、エンジンプロセスとコアを食い合う**。`intra_op_num_threads` を明示(例: 4)+ `intra_op_thread_affinities` でコアを分離し、**エンジンのP2/P3予算を守る**。これは「静かに壊れる」型の罠なので設定を manifest に焼く。

---

## 問い5. データ層

### 5.1 形式の割り当て

| 対象 | 形式 | 理由 |
|---|---|---|
| **世界データ台帳**(POI・グラフ・セル属性) | **Parquet**(不変・ビルド成果物)+ 実行時は NumPy 配列へ展開 | 列指向・型・圧縮・ハッシュ検証が容易 |
| **可視性テーブル**(M10 ≤512MB) | **生バイナリ + `numpy.memmap`** | ラン間 mmap 共有が既決。Parquetでは mmap 共有ができない |
| **LLMテープ**(恒久記録) | **Parquet(zstd)・日次パーティション** + `blocks.parquet`(共有ブロックのintern辞書) | §3.6 |
| **診断行** | **Parquet**(`runs/<run_id>/diag.parquet`・既存manifest案どおり) | DuckDBで直接集計 |
| **経済台帳(transfer)** | **Parquet**(append-only・日次パーティション) | 検算はDuckDBのSQLで書ける(四重記入・純資産合計=実物資産) |
| **センサス表**(月次MER/日次軽量) | **Parquet**(小さい)+ 人間向けに CSV 併出 | |
| **checkpoint** | **`.npz`(非圧縮)+ 外側 zstd**、または生バイナリ+メタJSON | M7(膨張率≤2.0x)を機械検査しやすい。Zarrは**採らない**(チャンク/圧縮メタが増え、膨張率の勘定が不透明になる) |
| **集計・照会** | **DuckDB**(ファイルを読むだけ・DBに取り込まない) | 公式(実読): 「when querying a Parquet file, only the columns required for the query are read.」「When you apply a filter to a column that is scanned from a Parquet file, the filter will be pushed down into the scan, and can even be used to skip parts of the file using the built-in zonemaps.」「If you wish to keep the data stored inside the Parquet file, but want to query the Parquet file directly, you can create a view over the `read_parquet` function.」glob(`SELECT * FROM 'test/*.parquet'`)・Hiveパーティション対応 |

### 5.2 40万体×1シミュ日のログ量見積り

前提: 400万呼/日(L4)・1,440 tick/日(1分tick)・139セル・入力1,300tok(共有1,000+個体300)・出力o64。

| 種別 | 行数/日 | 生サイズ/日 | 圧縮後(zstd-3)【推測: 3-4x】 | 予算(S1/S2) |
|---|---|---|---|---|
| **LLMテープ**(共有ブロックintern後) | 400万 | 個体プロンプト300tok≈0.9KB + 出力64tok≈0.19KB + メタ0.1KB ≈ **1.2KB/呼 → 4.8GB** | **1.2-1.6GB** | S1 ≤5GB/日 ○ |
| — 共有ブロック辞書 | 数千 | ~数MB | 数MB | |
| **診断行**(呼ごと1行・数値列中心) | 400万 | 約 60B/行 = 240MB | **60-90MB** | |
| **経済 transfer**【推測: 20取引/体/日】 | 800万 | 32B/行 = 256MB | **70-90MB** | |
| **イベント/行動ログ**(resolve結果) | 【推測】400-800万 | 48B/行 = 200-400MB | 60-120MB | |
| **セル別集計**(139セル×1,440tick×~20列) | 20万 | 数十MB | 数MB | |
| **checkpoint**(6h毎=4回/日) | — | M1=12GB in-RAM / M7≤2.0x → 直列化 **≥6GB×4 = 24GB** | **~17GB**(zstd 1.4x以上が必要) | S2 ≤17GB/日 △**要検証** |
| **合計(checkpoint除く)** | | ~5.5GB | **1.5-2.0GB** | |

**禁止事項(v1 runB の教訓の直接適用)**:
- **個体×tick の全記録は禁止**: 40万体 × 1,440 tick = **5.76億行/日**。16B/行でも **9.2GB/日(非圧縮)**、Parquet でも数GB。**位置トレースはセル別集計(20万行/日)へ落とす**。個体軌跡が要るランは**サンプル個体(例: 2,000体=0.5%)のみ**を事前登録して記録。
- **O(N·t) 以上の項は状態成長宣言(D-R2-6・YAML 5欄)が必須**。ActualLog は日次集約+保持窓。

**S2(checkpoint ≤17GB/日)の注意**: M7(膨張率≤2.0x)から直列化サイズは in-RAM 12GB の**半分以上**、つまり ≥6GB。6時間毎(4回/日)なら生 24GB。**S2を守るには圧縮を前提にするか、増分checkpoint(前回との差分)にするか、頻度を落とすかの三択**。これは予算表に**明示されていない緊張**=親への申し送り。**【推測】** 増分checkpoint(不変フィールドは初回のみ・可変フィールドのみ差分)が最も筋がよい。

### 5.3 mmap と Arrow

- 可視性テーブル(M10)は **`numpy.memmap` 一択**(ラン間共有=M8に1回分だけ算入、が既決)。
- Arrow IPC(Feather)の mmap 読みは、writerプロセスとengineプロセス間のゼロコピー受け渡しに使える【推測】が、**本調査で公式ドキュメントを実読していない=空欄(未確認)**。第1陣は `multiprocessing.Queue` + Parquet書き出しで足り、最適化は宣言つきで後回し。

---

## 問い6. テスト・CI・性能ゲート

### 6.1 テストの層

| 層 | 道具 | 内容 |
|---|---|---|
| 単体 | pytest | 各モジュール |
| 性質 | **hypothesis** | ①保存則(任意のtransfer列で四重記入が閉じる・純資産合計=実物資産) ②観測レンダラの正規化規約9項(任意の状態でバイト一致) ③RNGのドメイン分離(他ドメインの消費が結果を変えない) ④二相コミットの安全性(任意の競合集合で「定員超過が起きない」「優先度順序が守られる」) |
| バイト一致 | pytest(golden) | 同セル同時間帯の2体で B0-B4 のバイト差分ゼロ(契約書§2.4⑧)。**テンプレ改版でgoldenが変わったら「変化の宣言」を要求** |
| 状態成長宣言 | pytest + YAMLゲート | 全モジュールの5欄(per_agent_bytes/per_cell_bytes/per_day_growth/retention/worst_case_ops_per_tick)を宣言。**24stepスモークの実測を1日・30日へ外挿し、予算表M行を超えたらCI失敗**(D-R2-6) |
| 直列化 | pytest | **M7: in-RAM / 直列化 ≤ 2.0x** を実データ規模の縮小版で毎回検査(v1事故13.6倍の再発防止) |
| 録画リプレイ回帰 | pytest | 固定テープ+固定manifest → 状態ハッシュが一致。**エンジン層=numerical identity**(既存答申の二層宣言) |
| 性能 | **pytest-benchmark**(CI・相対)+ **asv**(セルフホスト機・履歴) | §6.3 |
| 契約 | pytest | 行動契約(12語+種別固有)・2行形の文法・未定義行動5段 |
| 実LLM | 手動/夜間 | **24stepスモークまで**(A4)。フルランはユーザー明示時のみ |

### 6.2 CI(GitHub Actions・GPUなし)で回せる範囲

**回せる**: 上表のほぼ全て。CPU numba パス・mock LLM・テープリプレイ・保存則・バイト一致・状態成長宣言・M7膨張率・5,000体規模の短ラン(W2 ≤10分が予算なので、CIでは 100-500 step の縮小版)。

**GPU必須(セルフホスト or 手動ゲート)**:
- P1(≤50ms/フレーム@40万体)の実測。
- GPUカーネルの**CPU参照実装との数値一致**テスト(これが GPU/CPU両対応の実質の検収)。
- vLLM 実接続・BATCH_INVARIANT の自検証(A5000=CC 8.6 の境界問題)。
- 40万体規模の RSS(M8)実測。

**運用**: GPU必須テストに `@pytest.mark.gpu` を付け、CI は `-m "not gpu"`。**リリース(=正典化)の前に手動で `-m gpu` を回した記録を manifest に残す**。

### 6.3 P5(+10%で失敗)の計測法 ― **重要な落とし穴**

- asv 公式(実読要点): 「airspeed velocity detects statistically significant decreases of performance automatically based on the available data when you run `asv publish`」「clicking the 'Regressions' tab …」。**履歴を追う道具**であって、PRごとのゲートには向かない。
- pytest-benchmark は pytest 統合でPRゲートに向くが、**GitHub Actions 共有ランナーは実行ごとに CPU 世代・ノイズが変わる**。絶対時間で +10% は**確実に誤検出する**(本答申の判断・出典なし=**expedient**)。
- **推奨の二段構え**:
  1. **CI(共有ランナー)= 相対ゲート**。同一ジョブ内で `main` の baseline と PR の candidate を**交互に**測り、その比が 1.10 を超えたら失敗。ノイズは両者に等しく乗るので比は安定する。加えて**ノイズ非依存の代理指標**(呼び出し回数・確保バイト数・イベント数)を assert する。
  2. **セルフホスト機(ローカル Win11 / クラウド借用)= 絶対ゲート**。asv で履歴を残し、W2(≤10分/シミュ日@5千体)・P2・P3・P6 の**絶対値**を判定。**予算表の値はここでだけ判定する**。
- **P4(逐次ループの新設は宣言必須)の機械化**: 【推測】AST 検査で「`for` の中で個体配列を添字アクセスしている」パターンを lint し、`# perf-declared: <台帳行ID>` コメントが無ければ失敗、という自作 lint が最も安上がり。先行事例は見つけられなかった=**expedient**。

---

## 問い7. コンポーネント分割と依存

### 7.1 依存グラフ(下が土台。**上→下の import のみ許す**)

```
                      ┌─────────────┐
                      │  manifest   │  run manifest の読み書き・封印・ハッシュ検証
                      └──────┬──────┘   (誰にも依存しない・全員が読む)
┌──────────┐                │
│  build   │ オフライン      │
│(世界構築)│ 成果物=不変資産  │
└────┬─────┘                │
     │ (実行時は import されない・成果物ファイルだけを渡す)
     ▼
┌──────────────────────────────────────────────────────────────┐
│ core   : SoAレジストリ・dtype/バイト予算宣言・Philox RNG・     │  ← 何にも依存しない
│          ハッシュ(blake3/xxhash ラッパ)・時刻型・ID型         │
└───────────────────────────┬──────────────────────────────────┘
        ┌───────────────────┴────────────────────┐
        ▼                                        ▼
┌──────────────┐                        ┌──────────────┐
│   world      │ セル/POI/グラフ/        │   agents     │ 状態SoA/T0習慣/
│              │ 可視性(mmap)/騒音場     │              │ 記憶/関係
└───────┬──────┘                        └───────┬──────┘
        └──────────────┬─────────────────────────┘
                       ▼
              ┌──────────────────┐
              │   perception     │ レンダラ/ハッシュ三役/注意ゲート/p_notice
              │                  │ → 出力は **Observation DTO(ただの bytes+メタ)**
              └────────┬─────────┘
                       ▼
              ┌──────────────────┐
              │      llm         │ 艦隊クライアント/パーサ/テープ
              │                  │ **world/agents を import しない**(DTOのみ)
              └────────┬─────────┘
                       ▼
       ┌───────────────────────────────────┐
       │            engine                 │ 時計/スケジューラ/繰り延べアービタ/
       │  ★ 世界状態への唯一の書き込み口   │ resolve/二相コミット(reserve→arbitrate→commit)
       └───────┬───────────────────┬───────┘
               ▼                   ▼
       ┌──────────────┐    ┌──────────────┐
       │   economy    │    │  census/diag │ 読み取り専用の集計・計器盤
       │ 台帳/transfer│    │              │
       │ /検算/センサス│    └──────────────┘
       └──────────────┘
         ※ economy は engine の transfer 単一APIを通してのみ状態を触る
           (SoAを直接書かない)
```

### 7.2 依存規則(循環禁止の具体形)

1. **`core` は誰も import しない**(NumPy等の外部のみ)。
2. **`llm` は `world`/`agents` を import してはならない**。入力は `perception` が作った **Observation DTO**(バイト列+メタのみ)、出力は **Action DTO**(パース済み構造体)。→ これで **mock LLM が完全に成立**し、テープリプレイが型レベルで保証される。
3. **世界状態を書き換えるのは `engine.resolve` だけ**(行動契約書の既決)。`economy` も `perception` も**読むだけ**。書き込みは `engine` が提供する `transfer()` / `commit()` を呼ぶ。
4. **`build` は実行時に import されない**。成果物(Parquet/memmap/ハッシュ)だけが `world` に渡る。**ビルド鎖の依存が実行時に漏れない**=OSM/PLATEAU/GDAL等の重い依存をランタイムから排除。
5. **`manifest` は全員が読めるが誰にも依存しない**(設定は不変オブジェクトとして注入)。
6. **循環検査を CI に入れる**: `import-linter`(または自作の AST 検査)で上の層順序を契約として宣言し、違反でCI失敗。**この1本があるかないかで、1人+AIサブ体制の構造保全がまったく違う**(サブは平気で横に import を足す)。

### 7.3 プロセス/スレッド構成

```
[Proc A] engine (単一プロセス)
   ├ asyncio イベントループ ×1        … LLM待ち・writerへの送出・埋め込みworker IPC
   ├ 計算は numba(nogil) / CuPy or Warp … GILを離す区間で走る
   ├ RSS 予算 M8 ≤24GB はこのプロセスで測る
   └ GPU: Phase 3 以降は同プロセスで CUDA ストリームを持つ
[Proc B×7] vLLM OpenAI サーバ (外部起動・ランより長生き)
   └ engine とは HTTP のみ。--prefix-caching-hash-algo sha256_cbor(検証ラン)
[Proc C] embedding worker (onnxruntime CPU・Ruri-v3-30m)
   └ intra_op_num_threads を明示・コアアフィニティで engine と分離
[Proc D] writer (Parquet/journal/checkpoint)
   └ engine から SPSC キュー。**主ループがディスクI/Oでブロックしない**ことが目的
[Proc E] (任意) 計器盤・可視化
   └ diag.parquet と checkpoint を読むだけ(書き込み権限を持たない)
```

**なぜ engine を単一プロセスにするか(3つ)**:
1. **M8(RSS≤24GB)を守る唯一の形**。SoA をプロセス間で分けると複製かshared_memoryの複雑さが要り、どちらも予算か保守性を壊す。
2. **GIL は問題にならない設計になっている**。A3(逐次禁止)を守れば Python レベルの反復は tick あたり数百回(セル139・イベントクラス数個)。重い計算は numba `nogil` / CuPy カーネル内=GILの外。**残る GIL 圧は asyncio の HTTP 処理**で、これは httpx が C 拡張側で待つ。
3. **決定論の担保が単純**。マルチプロセスにすると「どのプロセスが先に書いたか」が入り、二相コミットの証明が壊れる。

**リスク(実測が要る)**: 400万呼/日 = 平均 **46呼/秒**、ピークでその数倍。**httpx のイベントループと numba 計算が同一プロセスで干渉しないか**は Phase 2 の実測項目。干渉が出たら **LLMクライアントを Proc F に分離**(engine とは共有メモリのリングバッファ)。**この分離条件を先に宣言しておく**(P4の精神)。

---

## 問い8. 推奨

### (a) 言語・ランタイムの決定案

**本命案: Python 3.12 + NumPy/Numba(CPU)+ NVIDIA Warp(GPU)。既決A3/A4を維持し、GPU部品だけ `numba.cuda` → `Warp`(代替 CuPy)に差し替える。**

- 理由: (i)律速はLLM(W3)であり言語の絶対速度は効かない (ii)配列指向にすれば Python でも Agents.jl 同等域(AMBER) (iii)Warp は **CPU/CUDA両バックエンドに同一カーネルをJIT** = A3を1本のコードで満たす (iv)Apache-2.0・Win/Linux/macOS wheel = 借用機→ローカル機の可搬性(DECIDED-2)に合う (v)1人+AIサブ体制の保守性が最良。
- **delta(予算表・決定台帳への申し送り)**: A3 の「GPU(CUDA)」の実装手段を明示し、`numba.cuda` は**採らない**と書く(理由: NVIDIA公式が保守モードを宣言)。

**代替案: Python + Rust(PyO3/maturin)ホットスポット。**
- **移行条件(先に宣言しておく)**: 以下のいずれかが Phase 2/3 の実測で起きたときのみ、当該関数だけを Rust 化する。
  1. numba でベクトル化してもなお **P2(≤5ms/frame@5千体)または P3(≥10万イベント/秒)を2倍以上超過**する関数がある。
  2. **P6(変化検出 ≤2ms/tick)**が numba+xxhash で満たせない。
  3. GIL 干渉が実測され、かつ Proc 分離でも解けない。
- 移行時の規律: **Rust化は関数単位・CPU参照実装(NumPy)を必ず残す**・両者の数値一致テストをCIに置く。

**不採用: Julia / C++ 全面 / FLAME GPU 2 / Mesa**(§1.2・§2)。

### (b) 部品表

| 分類 | ライブラリ | 版方針 | ライセンス | 用途 |
|---|---|---|---|---|
| 言語 | CPython | **3.12**(A4) | PSF | |
| 配列 | NumPy | 下限固定・上限は緩め | BSD-3 | SoA・Philox |
| CPU JIT | Numba | 0.61系以降 | BSD-2 | 物理・集約・p_notice |
| GPU | **warp-lang**(第一) | 版固定 | **Apache-2.0** | Phase 3 物理 |
| GPU | cupy-cuda12x(第二) | 版固定 | MIT | NumPy互換の逃げ道 |
| ハッシュ(暗号) | blake3 | 版固定 | 空欄(未確認) | manifest・資産・封印・優先度キー |
| ハッシュ(高速) | xxhash | 版固定 | 空欄(未確認) | 変化検出・prefixキー・ルーティング |
| HTTP非同期 | **httpx** | 版固定 | BSD-3 | 艦隊クライアント |
| LLMサーバ | **vLLM 0.28.0**(ベンチ実績版) | 完全固定(再現性の前提) | Apache-2.0 | 艦隊 |
| 埋め込み | sentence-transformers + onnxruntime | 版固定 | Apache-2.0 | Ruri-v3-30m(Apache-2.0) |
| 列指向I/O | pyarrow | 版固定 | Apache-2.0 | Parquet読み書き |
| 集計 | duckdb | 版固定 | MIT | 診断・センサス・検算SQL |
| 圧縮 | zstandard | 版固定 | BSD | テープ・checkpoint |
| テスト | pytest / pytest-benchmark / hypothesis | 版固定 | MIT | §6 |
| 性能履歴 | asv | 版固定 | BSD-3 | セルフホスト機のみ |
| 構造保全 | import-linter | 版固定 | BSD-2 | §7.2の層契約 |
| 設定 | pydantic(または dataclass+自作検証) | 版固定 | MIT | manifest正規化 |

> ライセンス欄の「空欄(未確認)」は、**本調査でLICENSEファイルを実読していない**という意味。親の一次確認対象(データライセンス台帳へ載せる前に必須)。

### (c) コンポーネント図と依存規則 → §7.1・§7.2

### (d) プロセス/スレッド構成 → §7.3

### (e) テスト・CI計画 → §6

### (f) expedient(根拠のない選択)の明示

| # | 選択 | なぜ expedient か | 感度試験/検証の形 |
|---|---|---|---|
| E1 | engine を単一プロセス+asyncio にする | 40万体規模で GIL 干渉が出ないという公開データを見つけられなかった | Phase 2 で「計算時間 vs HTTP待ちの重なり率」を実測。悪化したら Proc F 分離(条件を先に宣言) |
| E2 | P6(変化検出 ≤2ms)を xxhash×139セル で満たす | 実測なし | Phase 2 で実測に差し替え(予算表の改訂条件どおり) |
| E3 | CI の相対ゲート(baseline/candidate 交互測定・比 1.10) | 先行事例を確認できず | 実運用で誤検出率を記録し、閾値を delta 改版 |
| E4 | P4 の機械化(AST lint で個体添字ループを検出) | 先行事例なし | 誤検出/見逃しの数を記録 |
| E5 | LLM タイムアウト既定(TTFT 60s / e2e 300s) | 根拠なし | ベンチの TTFT 分布(c=1024で170秒の実測あり)から Phase 2 で決め直す |
| E6 | ルーティング = `xxhash(call_id) mod 7` | 均等性は明らかだが、prefix共有との相互作用は未測定 | least-in-flight との A/B(BN-4の壁時計列の作法で測る) |
| E7 | 経済 transfer を 20取引/体/日 と見積り | 根拠なし(§5.2) | Phase 2 の実測で差し替え |
| E8 | checkpoint を増分方式にする案 | S2 との緊張を解く案だが先例未確認 | Phase 2 で全量 vs 増分の膨張率・復元時間を測る |
| E9 | Warp を GPU 第一候補にする | Warp を用いた大規模ABMの公開事例を確認できていない(粒子系・ロボティクスが主用途) | Phase 3 手前で CuPy 実装との A/B を1つ作る |

---

## 問い9. 親の一次確認リスト(最重要5件)

| # | 主張 | URL | 引用文 | 確認すべき数値/事実 |
|---|---|---|---|---|
| **1** | **Numba の CUDA ターゲットは保守モードに移行=A3の実装手段を変える根拠** | https://github.com/NVIDIA/numba-cuda | 「Numba-CUDA is in maintenance mode. Moving forward, we intend to support only security issues and critical bug fixes through the lifetime of CUDA 13.」 | (a)この文が README 現行版に実在するか (b)Numba 本体の非推奨スケジュール(0.61 非推奨 / 0.62 警告 / 0.63 で削除)が https://numba.readthedocs.io/en/stable/cuda/overview.html に実在するか(**本答申は検索要約経由=未読**) (c)ライセンス BSD-2-Clause |
| **2** | **vLLM のプレフィクスキャッシュ・ハッシュは既定 sha256 で「Python/vLLM版をまたいで再現しない」・`sha256_cbor` が再現可能・`cache_salt` で分離** | https://docs.vllm.ai/en/stable/design/prefix_caching/ | 「sha256 … Uses Python's `pickle` for serialization. **Hashes may not be reproducible across different Python or vLLM versions.**」/「sha256_cbor … providing a reproducible, cross-language compatible hash.」/「cache_salt … injected into the hash of the first block, ensuring that only requests with the same salt can reuse cached KV blocks.」 | (a)`--prefix-caching-hash-algo` の選択肢と既定値 (b)0.28.0 でこのフラグが存在するか(**答申は stable 版ページを読んだ・0.28.0固定版での確認が要る**) (c)cache_salt がOpenAI互換APIのリクエストに載せられるか |
| **3** | **FLAME GPU 2: アトミックの順序は非決定・優先度つき競合は bidding sub-model で解く(=v2の二相コミットの先例)** | doi:10.1002/spe.3207(OA全文 https://eprints.whiterose.ac.uk/id/eprint/199416/ ) | 「**The order of the atomic operations is non deterministic and determined by the GPU's execution model**, as such, if agent priority plays an important role in manipulating the environment then this 'conflict' between agents (in obtaining a resource) is best resolved using the sub-model approach」/「conflict can be resolved through a process of **bidding** … **only the highest priority agent allowed to perform the movement. Priorities can be randomly assigned to agents** … to achieve fairness, as in the serial case.」 | (a)引用文の実在(親は既に既存答申の検収でこの文献に触れている) (b)性能値「1M agents in ∼0.003 s per time step」「16M agents in ∼1 second per time step」 (c)ライセンス「open source under a permissive MIT licence」 |
| **4** | **配列指向Pythonは ABM 専用フレームワーク(Agents.jl)に並ぶ=言語変更の必要がないことの外部証拠** | arXiv:2601.16292(AMBER)/ arXiv:2101.10072(Agents.jl) | AMBER: 「population size (500, 1,000, and 5,000 agents), and simulation length (50 steps)」「achieves speedups of up to 1118× over Mesa」/ Agents.jl Table 2: Mesa 0.8 は Agents.jl 比 **24.9×/26.8×/31.9×/125.6×** | (a)AMBER の 5,000体の絶対時間(wealth transfer 21ms vs Mesa 23,917ms)と Agents.jl 比 1.2×(SIR) (b)**測定規模が 5,000体どまり**であること(40万体の外挿ではない)を台帳に明記する (c)Agents.jl Table 2 の数値と Mesa の版(0.8)が古いこと |
| **5** | **httpx の既定 keep-alive 上限 20 は L6(64 in-flight/GPU)に足りない=静かに壊れる型の設定** | https://www.python-httpx.org/advanced/resource-limits/ | 「max_keepalive_connections: number of allowable keep-alive connections … (Defaults 20)」「max_connections: maximum number of allowable connections … (Default 100)」「keepalive_expiry: time limit on idle keep-alive connections in seconds … (Default 5)」 | (a)既定値3つ (b)7レプリカ×64=448 in-flight を張る構成で、レプリカごとに別 AsyncClient を立てる必要があるか (c)`keepalive_expiry=None` の妥当性 |

**追加の確認候補(5件に入らないが重要)**:
- **RTX 5070(Blackwell sm_120)における CuPy / Warp / vLLM のwheel対応**=**空欄(未確認)**。ローカル機での実行可否そのものが懸かる。
- sentence-transformers の CPU 量子化速度(onnx-qint8 3.2x / openvino-qint8 5.3x)は**検索要約経由・本文未読**。
- **Ruri-v3-30m のスループット公開値は見つからなかった**(自前測定が必要)。
- **S2(checkpoint ≤17GB/日)と M7(膨張率≤2.0x)+ M1(12GB)+ 6時間毎 の算術が緊張する**(生24GB/日)。予算表の再確認が要る。

---

## 参照一覧

**実読(引用を本文に載せたもの)**
1. NVIDIA/numba-cuda — https://github.com/NVIDIA/numba-cuda (保守モード宣言・BSD-2-Clause)
2. NVIDIA/warp — https://github.com/NVIDIA/warp (Apache-2.0・Win/Linux/macOS wheel・CPU/CUDA)
3. NumPy — Philox — https://numpy.org/doc/stable/reference/random/bit_generators/philox.html
4. vLLM — Automatic Prefix Caching — https://docs.vllm.ai/en/stable/design/prefix_caching/
5. httpx — Resource Limits — https://www.python-httpx.org/advanced/resource-limits/
6. onnxruntime — Thread management — https://onnxruntime.ai/docs/performance/tune-performance/threading.html
7. PyO3 — https://pyo3.rs/
8. Hugging Face — cl-nagoya/ruri-v3-30m — https://huggingface.co/cl-nagoya/ruri-v3-30m
9. DuckDB — Parquet overview — https://duckdb.org/docs/current/data/parquet/overview.html
10. Richmond et al. 2023, FLAME GPU 2, *Softw. Pract. Exper.* 53(8) — https://doi.org/10.1002/spe.3207 (OA全文 https://eprints.whiterose.ac.uk/id/eprint/199416/ ・PDF本文を実読)
11. Pham, AMBER: A Columnar Architecture for High-Performance Agent-Based Modeling in Python — https://arxiv.org/abs/2601.16292 (HTML版 https://arxiv.org/html/2601.16292v2 を実読)
12. Datseris, Vahdati, DuBois, Agents.jl — https://arxiv.org/abs/2101.10072 (PDF本文 Table 2 を実読)
13. oconnor663/blake3-py — https://github.com/oconnor663/blake3-py
14. sentence-transformers v5.1.0 リリースノート — https://github.com/UKPLab/sentence-transformers/releases/tag/v5.1.0

**検索結果の要約のみ(本文未読=引用として使っていない)**
15. Numba CUDA overview(非推奨スケジュール) — https://numba.readthedocs.io/en/stable/cuda/overview.html
16. Repast4Py — https://github.com/Repast/repast4py ・ https://repast.github.io/repast4py.site/
17. Agents.jl スケジューラ — https://juliadynamics.github.io/Agents.jl/stable/
18. Taichi — https://github.com/taichi-dev/taichi ・ https://docs.taichi-lang.org/
19. asv — https://asv.readthedocs.io/en/stable/using.html
20. Mesa 3(JOSS) — https://doi.org/10.21105/joss.07668
21. vLLM Online Serving — https://docs.vllm.ai/en/stable/serving/online_serving/
22. sbert 効率化ドキュメント — https://www.sbert.net/docs/sentence_transformer/usage/efficiency.html

**空欄(未確認)**
- MATSim の一次資料 / ABMax(arXiv:2508.16508)/ Julia vs Rust の ABM ベンチ一次ページ / numba vs Rust vs C++ の同一ABM査読ベンチ / CuPy・Warp の sm_120 対応 / Ruri-v3-30m のスループット公開値 / blake3・xxhash の PyPI パッケージの正確なライセンス種別 / Arrow IPC の mmap ゼロコピー公式記述 / Mesa 3 の40万体級ベンチ

**リポ内参照(読み取りのみ)**
- `docs/design/v2-budget-declaration.md`(W1-W3/P1-P7/M1-M12/L1-L7/S1-S4・運用規則6)
- `docs/design/v2-redesign.md` 行「構築前の即決8項」(A3/A4/A7/A8)・行 R4/R5/D-R2-3〜6
- `docs/design/v2-perception-contract.md`(§2.4 正規化規約9項・ハッシュ三役・起床条件)
- `docs/bench/README.md`(第1-5段の結論・L6=64の実測根拠・BN-5契約書サイズ)
- `docs/research/v2-run-manifest-concurrency-research.md`(U8/U9・二相コミット・Philox・BLAKE3優先度キー)
