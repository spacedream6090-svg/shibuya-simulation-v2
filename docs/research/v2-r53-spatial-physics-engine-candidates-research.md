# R-53 答申: 物理エンジン粒度の空間層 — 候補比較のための事実集め(汎用物理エンジン・群集モデル・ナビメッシュ/視線/占有・規模・2 時間軸・失敗の返し方)
<!-- hdr:v1 -->
- **分野**: 歩行者動力学 #18 / ゲーム・VR 技術の輸入(常設レーン) / 計算科学(決定論・並列) | **重要度**: P0(サブ判断・親が確定)
- **一次確認**: **B** = サブ実読(出典 38 件=◎ 33〔公式文書・原論文本文・公式リポのソース行〕・○ 5〔作者の Issue コメント 1・抄録 2・GitHub API のメタ情報 2〕・二次 0・取得失敗 3 = §8)・**親検収 済(第282・下の欄)**
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **先行答申**: [R7 群衆物理](v2-crowd-physics-research.md)(親検収済)

> 用途: 設計者「エンジンが手書きで行っている『実現可能か』の判定のうち空間系(到達・混雑・満席・視線・遮蔽・距離)を物理(空間・衝突・視線・経路)に任せたい。粒度は物理エンジン程度」に対し、候補を比べる**材料(事実)**だけを並べる。**推奨は書かない**。前提=第280 の決定論の方針(salt とテープが同じなら同じ結果・同じ環境/設定の範囲で。マシン間・スレッド数間・GPU 間のビット一致は求めない。決定論にできない外部の道具は出力をテープに記録して再生)。
> 規律: 子サブ未起動・Web は読むだけ(HTML/PDF は curl → 標準出力 → テキスト化・保存なし・clone なし)・コミットなし・台帳未編集・本書の新規作成のみ。**決定論の主張は公式文書の逐語だけを根拠にした**(作者の Issue コメントは ○ と明記)。

---

> **親検収(第282・2026-09-28・親=Fable 5.1)**
> - 一次照合した引用(親が同じ URL を curl → 標準出力 → 文字列照合・保存なし): ✓ PhysX 5.8.0 docs「The simulation behavior is not influenced by the number of worker threads that are used.」/ PhysX ヘッダ `PxSceneDesc.h` の「not currently supported on GPU」= ✓(raw main ヘッダ) / ✓ Jolt Architecture.md「Broadphase queries (BroadPhaseQuery) are NOT deterministic」「approximately 8% slower」/ ✓ Box2D「Box2D is designed to be determinism across thread counts and platforms.」「Determinism is on by default and there is no explicit option to disable it.」/ ✓ Rapier「Rapier is locally deterministic」「the results of the parallel solver are identical to the results of the sequential one」/ ✓ ORCA 2011「For 5,000 agents on eight cores, it takes 8 ms」/ ✓ Charlton 2019「(33ms per frame) for up to 5 × 10^5 agents」「GTX 970」。
> - 訂正: なし。§4 の外挿は [サブ計算]・線形・世代混在の注記を保って設計書へ写す。
> - 写し検査・訂正の伝播検査・循環参照検査・フロア併記検査: 設計書への写し先=[空間層の草案](../design/v2-spatial-physics-layer-draft.md) §3。G13/U15 の引用は C9 アジェンダ・群衆物理設計書の原文と一致(親が両文書を実読)。循環参照=R7 の親検収済み行(FLAME GPU 2・SUMO–JuPedSim)を引く=可。
> - 規律上の判定(取得経路など): 子サブなし・保存なし・clone なし=規律内。

## 要約

1. **汎用物理エンジン 5 種は、Bullet を除き「同じ環境・同じ投入順・固定刻み」での再現を公式文書で約束している**。差は条件の細部: PhysX は「同じシーン(同じ順で挿入)・同じ刻み方・同じリリース・同じプラットフォーム」で一致し「worker スレッド数に影響されない」、ただし島の独立性を足す `eENABLE_ENHANCED_DETERMINISM` は「**not currently supported on GPU**」。Box2D v3 は「スレッド数とプラットフォームをまたいで決定論」(生成順が根拠・既定で有効)。Jolt は「同じ API 呼び出し順+同じバイナリ」で決定論、ただし**ブロードフェーズ問い合わせは NOT deterministic**・コールバック順も非決定。Rapier は「同じ機械・同じ版・同じコンパイラで locally deterministic」、並列ソルバの結果は逐次と同一。Bullet は公式文書に決定論の保証文が無く、pybullet の文書の断片と作者の Issue コメント(○)だけ。
2. **2D か 3D か**: Box2D=2D のみ・PhysX/Bullet/Jolt=3D(PhysX は軸ロックで 2D 化の記述あり)・Rapier=2D/3D 両版(**Python は 3D の `rapier3d` だけ**)。
3. **Python から**: 公式の Python 経路があるのは pybullet・Rapier(`rapier3d`)・PhysX(`ovphysx`=**pre-release**・Warp 配列で出力)・JuPedSim(`pip install jupedsim`)。Box2D v3・Jolt・RVO2・Recast/Detour は**第三者**のバインディング(pyb2d3/box2d-python・Culverin・Python-RVO2・PyRecastDetour=Windows のみ)。
4. **刻み**: 汎用エンジンの既定/推奨は 1/60 s(Box2D・Jolt・Rapier・Bullet の C++)、pybullet は 1/240 s。群集モデルは JuPedSim 0.01 s(「既定のままを推奨」)、Menge の図 4 は SF 0.01 s/ORCA 0.1 s/予測型 0.002 s、RVO2 の例は 0.25 s。**60 秒 tick に対し 240〜30,000 ステップ/tick**。SUMO・MATSim の既定は 1 s(60 ステップ/tick)。
5. **規模の一次実績**: ORCA(CPU 8 コア・2011)**5,000 体で 8 ms/ステップ(円)・15.6 ms(オフィス避難)**。GPU の ORCA(GTX 970・2019)**10 万体超を 60 fps・50 万体で約 33 ms/フレーム**。Box2D v3 の積み木 5,050 体 0.90 ms(4 スレッド・AVX2=接触の多い剛体の山で群集ではない)。Menge は 32,000 体の例を「interactive simulation rates」。Vadere は 2019 時点で「thousands of agents in real-time … is not yet possible」(OSM)。汎用剛体エンジンの **1 万〜40 万体の歩行者/キャラクタ実績は公式文書に見つからない**(空欄)。
6. **単純外挿([サブ計算])**: 390,067 体を ORCA CPU で線形に伸ばすと 0.62〜1.22 s/ステップ → 0.1 s 刻みで **150〜292 h/シミュ日**。GPU ORCA 相当なら約 26 ms/ステップ → 0.1 s 刻みで **約 6.2 h/日**・0.01 s 刻みで約 62 h/日。リポ内の実測 engine_spike(numba・社会力型・40 万体 28 ms)も同じ桁。既存予算 P2 ≤300 ms/tick は 0.1 s 刻み(600 ステップ)なら 1 ステップ 0.5 ms に相当。
7. **テープ記録([サブ計算])**: 位置 float32×2=8 B/体を **tick ごと**に記録すると 390,067 体で 3.12 MB/tick=**4.49 GB/日**(S1 恒久記録 ≤5 GB/日のほぼ全量)。**物理刻みごと**(0.1 s)なら 2.7 TB/日。5,000 体は tick ごと 57.6 MB/日。
8. **2 時間軸の先行はある**: 歩行者の 3 層(strategic=活動選択/tactical=活動日程・場所と経路/operational=歩行。Vadere 論文が Hoogendoorn & Bovy 2004 を引いて記述)、Menge の「目標選択→計画→計画の適応→空間問い合わせ」分解と行動 FSM、SUMO の action-step-length(判断の間隔≠シミュ刻み)、Unity ML-Agents の DecisionPeriod(物理の固定更新 N 回に 1 回判断・既定 5)。
9. **失敗の返し方の先行**: MATSim `stuckAndAbort`(`reason` 属性つき・stuckTime 既定 10)、SUMO 歩行者の `jammed`(300 s 動けないと 1/4 速度で障害物を無視して進む)、Detour の `DT_PARTIAL_RESULT`(「best guess」を返す)と群集の `DT_CROWDAGENT_TARGET_FAILED`、Unity の `PathPartial`/`PathInvalid`。v2 には既に `UNREACHABLE`/`TARGET_GONE`/`LOST_ARBITRATION` 等 20 の失敗型がある。
10. **既存決定との関係(事実)**: C9 アジェンダの **G13(ユーザー案 09-17)=「物理は事前計算で再現し tick 内では物理エンジンを回さない」**、U15(群衆物理・仮決定 09-08)=CFSM 第 1 候補・Warp HashGrid・dt 掃引。本件の要望は G13 と向きが違う箇所がある(§7-4)。

## §0 等級と調べ方・出典表

- 等級: **◎** = 原典(公式文書・原論文本文・公式リポのソース)を生テキストで文字列照合 / **○** = 原典だが作者の Issue コメント・抄録・GitHub API のメタ情報 / **△** = 二次・検索要約 / **×** = 未確認。[コード読み] = GitHub raw のソース行。[サブ計算] = 本書での算術。
- 既存答申で親確認済みのもの(再確認せず参照): FLAME GPU 2「1M agents in ∼0.003 s per time step」(circles ベンチ)・SUMO–JuPedSim「typically 0.01 seconds」・ORCA の角のデッドロック(Game AI Pro 3)・Jülich データ CC BY 4.0([R7](v2-crowd-physics-research.md) 親検収欄)。リポ内実測 engine_spike([README](../bench/engine_spike/README.md))。D-50 の軽リサーチ([PENDING 凍結版](../log/pending-archive-2026-09-28.md) D-50 行)。

| # | 出典 | URL | 等級 | 取れた範囲 |
|---|---|---|---|---|
| 1 | PhysX 5.8.0 docs「Simulation」§Enhanced Determinism | https://nvidia-omniverse.github.io/PhysX/physx/5.8.0/docs/Simulation.html | ◎ | 決定論の節全文(5.6.1 版では RigidBodyDynamics.html に同文) |
| 2 | PhysX `PxSceneDesc.h`(main) | https://raw.githubusercontent.com/NVIDIA-Omniverse/PhysX/main/physx/include/PxSceneDesc.h | ◎ | `eENABLE_ENHANCED_DETERMINISM` のコメント(GPU 非対応) |
| 3 | PhysX `physx/README.md`・`physx/LICENSE.md`・ルート `LICENSE.md` | https://github.com/NVIDIA-Omniverse/PhysX | ◎ | SDK=Apache 2.0/ルート=BSD 3-Clause の表記・GPU バイナリは packman 取得 |
| 4 | ovphysx README | https://raw.githubusercontent.com/NVIDIA-Omniverse/PhysX/main/ovphysx/README.md | ◎ | Python 経路・pre-release・CPU/GPU |
| 5 | PhysX docs「Best Practices」「Character Controllers」 | https://nvidia-omniverse.github.io/PhysX/physx/5.8.0/docs/BestPractices.html ・ https://nvidia-omniverse.github.io/PhysX/physx/5.8.0/docs/CharacterControllers.html | ◎ | 刻みを揺らすと非決定・CCT は kinematic |
| 6 | PyBullet Quickstart Guide(PDF) | https://raw.githubusercontent.com/bulletphysics/bullet3/master/docs/pybullet_quickstartguide.pdf | ◎ | 1/240 s 既定・`deterministicOverlappingPairs`・saveState |
| 7 | Bullet User Manual(PDF)・LICENSE.txt | https://raw.githubusercontent.com/bulletphysics/bullet3/master/docs/Bullet_User_Manual.pdf | ◎ | 内部固定刻み 60 Hz・「determinis」の語は 0 件・zlib |
| 8 | bullet3 Issue #2394(作者 erwincoumans 2019-09-03) | https://github.com/bulletphysics/bullet3/issues/2394 | ○ | 「PyBullet is fully deterministic, as long as you send the same commands.」 |
| 9 | Box2D v3 docs「Simulation」§Determinism | https://box2d.org/documentation/md_simulation.html | ◎ | 決定論の節全文・刻み 1/60・sub-step 4 |
| 10 | Box2D ブログ「Determinism」(2024-08) | https://box2d.org/posts/2024/08/determinism/ | ◎ | FMA 無効・自前三角関数・x64/ARM・MSVC/GCC/Clang で試験 |
| 11 | Box2D ブログ「SIMD Matters」(2024-08) | https://box2d.org/posts/2024/08/simd-matters/ | ◎ | 積み木 5,050 体 0.90 ms |
| 12 | Box2D README・LICENSE・Releases | https://github.com/erincatto/box2d | ◎ | MIT・v3.1.1(2025-06-04)・公式外バインディング一覧に Python なし |
| 13 | pyb2d3 / box2d-python README | https://github.com/DerThorsten/pyb2d3 ・ https://github.com/giorgosg/box2d-py | ◎ | 第三者・MIT・「Early development preview」 |
| 14 | Jolt `Docs/Architecture.md` §Deterministic Simulation | https://raw.githubusercontent.com/jrouwe/JoltPhysics/master/Docs/Architecture.md | ◎ | 条件・CROSS_PLATFORM_DETERMINISTIC(約 8% 遅い)・ブロードフェーズ問い合わせは非決定 |
| 15 | Jolt README・HelloWorld.cpp・PerformanceTest.md | https://github.com/jrouwe/JoltPhysics | ◎ | MIT・Python=Culverin(第三者)・60 Hz・3,680 体の性能シーン |
| 16 | Rapier「Determinism」(Rust 版/Python 版) | https://rapier.rs/docs/user_guides/rust/determinism ・ https://rapier.rs/docs/user_guides/python/determinism | ◎ | locally deterministic・`enhanced-determinism`・並列=逐次と同一 |
| 17 | Rapier README・`bindings/python/README.md`・`integration_parameters.rs` | https://github.com/dimforge/rapier | ◎ | Apache-2.0・`pip install rapier3d`(3D・f32)・dt 既定 1/60 |
| 18 | ORCA 論文 van den Berg ら 2011(ISRR) | https://gamma.cs.unc.edu/ORCA/publications/ORCA.pdf | ◎ | 5,000 体 8 ms/15.6 ms・8 コア Xeon |
| 19 | RVO2 README・`RVOSimulator.cc`・`examples/Circle.cc` | https://github.com/snape/RVO2 | ◎[コード読み] | Apache-2.0・OpenMP・2 相の更新・例 0.25 s |
| 20 | Python-RVO2 README | https://github.com/sybrenstuvel/Python-RVO2 | ◎ | Cython・「Only tested with Python 2.7, 3.4, and 3.6」 |
| 21 | Curtis, Best & Manocha 2016「Menge」Collective Dynamics 1:A1 | https://collective-dynamics.eu/index.php/cod/article/view/A1 | ◎ | 部分問題の分解・図 4 の Δt・32,000 体の例 |
| 22 | Menge GitHub(ライセンスは API のメタ情報) | https://github.com/MengeCrowdSim/Menge | ○ | Apache-2.0 |
| 23 | JuPedSim `simulation.py`・LICENSE・README・モデル一覧 | https://github.com/PedestrianDynamics/jupedsim ・ https://www.jupedsim.org/stable/pedestrian_models/index.html | ◎ | LGPL-3.0・dt=0.01 既定・組込みモデル 7 種+自作口 |
| 24 | Kleinmeier ら 2019「Vadere」arXiv 1907.09520(Collective Dynamics 4:A21) | https://arxiv.org/abs/1907.09520 | ◎ | LGPL・Java・3 層の記述(H&B 2004 を引用)・実時間は未達 |
| 25 | Hoogendoorn & Bovy 2004, TR-B 38(2):169–190 抄録 | https://econpapers.repec.org/RePEc:eee:transb:v:38:y:2004:i:2:p:169-190 | ○ | 抄録のみ(本文の 3 層の逐語は未読) |
| 26 | PySocialForce README・`default.toml`・`stateutils.py` | https://github.com/yuxiang-gao/PySocialForce | ◎[コード読み] | MIT・numpy・全対差分(n×n) |
| 27 | MomenTUM `Licence.txt` | https://github.com/tumcms/MomenTUM | ◎ | 非商用の研究・教育のみ |
| 28 | Charlton ら 2019「Fast Simulation of Crowd Collision Avoidance」arXiv 1908.10107 | https://arxiv.org/abs/1908.10107 | ◎ | GPU ORCA 10 万体 60 fps・50 万体 33 ms |
| 29 | Recast/Detour `DetourStatus.h`・`DetourCrowd.h`・README | https://github.com/recastnavigation/recastnavigation | ◎[コード読み] | zlib・`DT_PARTIAL_RESULT`・`DT_CROWDAGENT_TARGET_FAILED` |
| 30 | PyRecastDetour README / recastlib | https://github.com/Tugcga/PyRecastDetour ・ https://github.com/layzerar/recastlib | ◎ | Windows のみ・Python 3.6–3.10 / 2018 年以降更新なし |
| 31 | VisiLibity1・PyVisiLibity・scikit-geometry | https://github.com/karlobermeyer/VisiLibity1 | ○ | いずれも LGPL-3.0(API メタ)・平面可視多角形 |
| 32 | Amanatides & Woo 1987(EG 技術論文)抄録 | https://doi.org/10.2312/egtp.19871000 | ○ | 格子走査 1 歩=比較 2 回+加算 1 回 |
| 33 | NVIDIA Warp CHANGELOG 1.15.0(2026-07-07) | https://raw.githubusercontent.com/NVIDIA/warp/main/CHANGELOG.md | ◎ | 原子操作の決定論モード RUN_TO_RUN/GPU_TO_GPU |
| 34 | SUMO「Basic Definition」「Pedestrians」「Why Vehicles are teleporting」 | https://sumo.dlr.de/docs/Simulation/Basic_Definition.html | ◎ | step-length 既定 1 s・action-step-length・jamtime 300 s |
| 35 | MATSim `QSimConfigGroup.java`・`PersonStuckEvent.java` | https://github.com/matsim-org/matsim-libs | ◎[コード読み] | timeStepSize 1.0・stuckTime 10・`stuckAndAbort`+`reason` |
| 36 | Unity ML-Agents `DecisionRequester.cs`・`Academy.cs` | https://github.com/Unity-Technologies/ml-agents | ◎[コード読み] | DecisionPeriod=5・Academy は FixedUpdate で進む |
| 37 | Unity `AI.NavMeshPathStatus` | https://docs.unity3d.com/ScriptReference/AI.NavMeshPathStatus.html | ◎ | PathComplete/PathPartial/PathInvalid |
| 38 | numba「Automatic parallelization」 | https://numba.readthedocs.io/en/stable/user/parallel.html | ◎ | prange の配列要素への縮約は競合状態になりうる(決定論の保証文は無い) |

## §1 汎用物理エンジン

- **PhysX 5**(3D・CPU/GPU): 逐語「PhysX provides limited deterministic simulation. Specifically, the results of the simulation will be identical between runs if simulating the exact same scene (same actors inserted in the same order) using the same time-stepping scheme and same PhysX release running on the same platform. The simulation behavior is not influenced by the number of worker threads that are used.」「the results of the simulation can change if actors are inserted in a different order. In addition, the overall behavior of the simulation can change if additional actors are added or if some actors are removed from the scene.」(#1)。フラグ: 「PxSceneFlag::eENABLE_ENHANCED_DETERMINISM … provided the application inserts the actors in a deterministic order, with this flag raised, the simulation of an island will be identical regardless of any other islands in the scene. However, this mode sacrifices some performance」(#1)・ヘッダ「Note that this feature is not currently supported on GPU.」(#2)。**GPU での既定の決定論の記述は GPURigidBodies ページに無い**(語「determinis」0 件)。刻み: 公式の固定推奨値は無く、Best Practices に「instead of simulating at 1/60th, consider simulating a range between 1/50th and 1/60th). This can introduce non-determinism」(#5)。ライセンス: `physx/README.md`「PhysX is licensed under the Apache License 2.0」・`physx/LICENSE.md`=Apache 2.0、**ルートの LICENSE.md は BSD 3-Clause 表記**(同じリポ内で 2 表記・#3)。GPU 部は「downloads binary content, such as the PhysX GPU binaries」(#3)。Python: `ovphysx`「pip install ovphysx」「Pre-release notice: ovphysx is a pre-release software and not yet mature」・USD シーンを読み Warp 配列で返す・CPU/GPU(#4)。キャラクタ: CCT は「a kinematic controller」(#5)。1 万〜40 万体の実績: 公式文書で**未確認**。
- **Bullet 3**(3D・CPU・zlib #7): 公式文書に決定論の保証文は無い(User Manual に「determinis」0 件)。pybullet の文書「By default, the physics server will not step the simulation, unless you explicitly send a 'stepSimulation' command. This way you can maintain control determinism of the simulation.」「When you need deterministic simulation after restoring to a previously saved state, all important state information, including contact points, need to be stored.」「deterministicOverlappingPairs … Set to 1 to enable and 0 to disable sorting of overlapping pairs (backward compatibility setting).」(#6)。作者の Issue コメント(○)「PyBullet is fully deterministic, as long as you send the same commands. If you step the simulation a different amount of times before applying a command, the world is in a different state」(#8)。刻み: pybullet「The default timestep is 1/240 second」「it is best to leave the timeStep to default, which is 240Hz. Several parameters are tuned with this value in mind」(#6)/C++「Bullet works best with a fixed internal timestep of at least 60 hertz (1/60 second)」(#7)。スレッド数・プラットフォーム間は公式記述**なし**(フォーラムの作者発言は取得失敗=§8)。
- **Box2D v3**(2D・CPU・MIT・v3.1.1): 逐語「Box2D is designed to be determinism across thread counts and platforms.」「Multithreaded determinism is achieved by basing simulation order on creation order. This includes bodies, shapes, and joint creation order. Determinism includes results reported to users (events). These events must be in deterministic order.」「Cross-platform determinism is achieved on 64-bit platforms by using compiler flags and by avoiding non-deterministic library functions.」「Determinism is on by default and there is no explicit option to disable it. However, you can break determinism by choosing different compiler flags.」「I maintain a unit test for determinism that is run for every pull request.」「Caution : Box2D determinism does not mean your application will be deterministic.」(#9)。ブログ: 「I test Box2D on x64 and ARM CPUs. I also test on MSVC, GCC, and Clang compilers.」「FMA must be disabled for cross-platform determinism」、同一機での再現は「This usually requires the world to be recreated」(#10)。刻み: 「you should use a fixed time step … A time step of 1/60 seconds (60Hz) will usually deliver a high quality simulation.」「The recommended sub-step count is 4.」(#9)。問い合わせ: README の機能に「Ray casts, shape casts, and overlap queries」「Sensor system」(#12)。Python: 公式の外部バインディング一覧(Beef/C++/WASM)に Python は無い。第三者 pyb2d3(MIT・「This may not work on windows!」はソースビルドの注記)・box2d-python(CFFI・「Early development preview - API subject to change」・Box2D main 追従)(#13)。規模: 積み木 5,050 体(接触対 14,950)で AVX2・4 workers **0.90 ms/ステップ**(AMD 7950X・#11)。
- **Jolt Physics**(3D・CPU・MIT): 逐語「The physics simulation is deterministic provided that: The APIs that modify the simulation are called in exactly the same order … The same binary code is used to run the simulation. For example, when you run the simulation on Windows it doesn't matter if you have an AMD or Intel processor.」「If you want cross platform determinism then please turn on the CROSS_PLATFORM_DETERMINISTIC option in CMake. This will make the library approximately 8% slower」。**注意書き**:「Broadphase queries (BroadPhaseQuery) are NOT deterministic because the broad phase can be modified from multiple threads.」「Narrowphase queries (NarrowPhaseQuery) will return consistent results, but the order in which the results are received can change.」「Various listener classes … are called from multiple threads. This means the order in which you receive callbacks is not deterministic.」「PhysicsSystem::GetActiveBodies will return the list of active bodies in a non-deterministic order」(#14)。刻み: HelloWorld「60 Hz is a good rate to update the physics system.」・大きい刻みでは「Do 1 collision step per 1 / 60th of a second (round up).」(#15)。キャラクタ: 「Rigid body character」「Virtual character … Updated outside of the physics update」(#15)。Python: README の一覧に Culverin(第三者・MIT・2026-01 作成)(#15)。規模: 性能試験シーンは 3,680 体(ラグドール)・4,410 箱など(時間の値は文書に無い)(#15)。
- **Rapier**(2D/3D・CPU・Apache-2.0): 逐語「By default, Rapier is locally deterministic, meaning that running the exact same simulation (with the same initial conditions) twice with the same machine, using the same version of Rapier, and the same version of the Rust compiler, will result in the exact same simulation results. However, doing this on two different computers may result in completely different results.」「the results of the parallel solver are identical to the results of the sequential one, and don't depend on the number of threads」「the enhanced-determinism feature cannot be enabled at the same time as the simd8 feature」(#16 Rust)。Python 版の逐語「with the same machine, using the same build of the bindings」「Note that this includes the timestep length: the simulation must be advanced by the same sequence of timesteps on every machine」、機械間には「The bindings are built with the determinism feature, e.g., with maturin develop --release -F determinism」、**NumPy の注意**「its vectorized functions (e.g. numpy.sin) may even give different results on two processors of the same platform, depending on the SIMD instructions they support」(#16 Python)。Python=`pip install rapier3d`(**3D・f32 のみ**)(#17)。dt 既定「default: `1.0 / 60.0`」(#17)。1 万体以上の実績: **未確認**。

## §2 群集モデルの実装

| 実装 | ライセンス | 言語/Python | 時間刻み(一次) | 60 s tick の歩数 | 決定論の記述 | 規模の一次 |
|---|---|---|---|---|---|---|
| RVO2(ORCA) | Apache-2.0 | C++98・OpenMP / Python-RVO2(第三者 Cython・「Only tested with Python 2.7, 3.4, and 3.6」) | コンストラクタ既定 0(利用者が設定)・Circle 例 0.25 s | 240 | **記述なし**。[コード読み] `doStep` は KD 木を作り→全員の新速度を計算→別ループで全員を更新(2 相・OpenMP の parallel for) | 5,000 体・8 コア・**8 ms**(円)/**15.6 ms**(オフィス避難)(#18)・動画 25,000 体(Hajj) |
| Menge | Apache-2.0(○) | C++ / Python は未確認 | 図 4: SF Δt=0.01 s・ORCA Δt=0.1 s・予測型 Δt=0.002 s | 6,000 / 600 / 30,000 | **未確認** | 「32,000 agents … at interactive simulation rates」(図 7 の数値は未抽出) |
| JuPedSim | LGPL-3.0 | C++ コア+公式 Python(`pip install jupedsim`) | `dt: float = 0.01`「It is recommended to leave this at its default value.」 | 6,000 | **記述なし**(文書で見つかったのは V3 の「tiny deterministic reverse-speed floor」だけ) | 公式の体数ベンチは**未確認**(SUMO 文書「runtime-limiting factor」=R7) |
| Vadere | LGPL | Java | 本書では**未確認** | — | 論文は乱数生成器と seed の違いが再現性に効くと指摘(自前の seed 機構は未確認) | 「simulating thousands of agents in real-time using the OSM with Vadere is not yet possible」(2019) |
| PySocialForce | MIT | numpy(numba 利用の記述は未確認) | `default.toml` `step_width = 1.0`(単位の記述なし) | 60(秒なら) | **記述なし** | [コード読み] `each_diff` が n×n の差分を作る=全対 |
| MomenTUM v2 | **非商用の研究・教育のみ**(「for non-commercial research and education purposes」) | Java | 未確認 | — | 未確認 | 未確認 |
| GPU ORCA(Charlton ら 2019) | 論文 | CUDA(FLAME GPU のメッセージ分割) | 未確認 | — | 未確認 | 「over 100,000 people to be simulated in real time (60 frames per second)」「close to 30 frames a second (33ms per frame) for up to 5 × 10^5 agents」「crossover occurring at approximately 2 × 10^3 agents」(GTX 970) |
| FLAME GPU 2(R7 親確認) | — | CUDA/Python | — | — | — | circles 1M 体 ∼0.003 s/ステップ(**歩行者モデルではない**) |

- JuPedSim の現行モデル(`Simulation(model=…)` の型注釈): CollisionFreeSpeedModel・V2・V3・GeneralizedCentrifugalForceModel・SocialForceModel・AnticipationVelocityModel・WarpDriverModel+CustomOperationalModel(自作口)(#23)。R7 時点の「CFSM のみ extensively tested」(SUMO 文書)以降にモデルが増えている。WarpDriver は「probabilistic collision fields」で `num_samples` 等のパラメータを持つ(#23)。
- 幾何の入力: JuPedSim は shapely の Polygon/MultiPolygon/WKT、または OBJ の歩行面(「floors may be stacked」)(#23)。Menge はナビメッシュ・高さ場(#21)。

## §3 ナビメッシュ・視線・占有

- **Recast/Detour**(C++・zlib): Detour の状態値「DT_PARTIAL_RESULT … Query did not reach the end location, returning best guess.」「DT_OUT_OF_NODES … Query ran out of nodes during search.」(#29)。DetourCrowd(README「Agent movement, collision avoidance, and crowd simulation」)の目標状態 `DT_CROWDAGENT_TARGET_FAILED`・`init(maxAgents, …)`(#29)。決定論の公式記述: **無い**(README・ヘッダで未発見)。Python: PyRecastDetour「Works in 64-bit Python 3.6 - 3.10 and Python 2.7 on Windows only」・ライセンス表示なし(API)・最終更新 2022-10、recastlib(zlib)最終更新 2018-07(#30)。
- **2D 可視多角形**: VisiLibity1(C++・LGPL-3.0)・PyVisiLibity(LGPL-3.0・最終更新 2020-08)・scikit-geometry(CGAL の Python 化・LGPL-3.0)(#31・ライセンスは API のメタ)。CGAL の 2D Visibility は**取得失敗**。shapely に可視多角形の関数が無いかは文書を開いていない=**未確認**。
- **格子上のレイ走査(自前実装の標準)**: Amanatides & Woo 1987「Going from one voxel to its neighbour requires only two floating point comparisons and one floating point addition.」(#32)=占有格子(例: 知覚契約の可視性格子 2.5 m)に numba で書ける形。
- **汎用エンジンの問い合わせ**: Box2D「Ray casts, shape casts, and overlap queries」(#12)・Jolt は BroadPhaseQuery が非決定・NarrowPhaseQuery は結果一致だが順序が変わる(#14)。
- **占有・近傍の numpy/numba 実装(リポ内実測)**: engine_spike(社会力型・2 m 一様格子・numba 並列・40 万体 **0.028 s/ステップ**、うち格子構築 0.021 s が単スレッドで支配)(README・R7 で親受理)。numba の並列ループは「a race condition would occur」の例を文書が挙げる(#38)=**決定論の保証文は無い**。
- **GPU(Warp)**: 「Add a deterministic execution mode for supported atomic operations, removing the run-to-run variation that floating-point atomics normally introduce. … `wp.DeterministicMode.RUN_TO_RUN` for bit-exact repeatable results on the same GPU, or `wp.DeterministicMode.GPU_TO_GPU` to also target consistency across GPU architectures.」(1.15.0・2026-07-07・#33)。**既定では浮動小数の原子加算が run-to-run で揺れる**ことを同文が前提にしている。

## §4 規模の見積り(報告のみ・[サブ計算]・線形外挿)

刻みと歩数: 0.01 s=6,000 歩/tick=864 万歩/日・1/60 s=3,600=518 万・0.1 s=600=86.4 万・0.25 s=240=34.6 万・0.5 s=120=17.3 万・1.0 s=60=8.64 万(1 日=1,440 tick)。

| 出発値(一次) | 390,067 体に線形換算(1 歩) | 0.01 s | 1/60 s | 0.1 s | 0.5 s |
|---|---|---|---|---|---|
| ORCA CPU 円 5,000 体 8 ms(#18) | 624 ms | 1,498 h/日 | 899 h | **150 h** | 30.0 h |
| ORCA CPU オフィス 5,000 体 15.6 ms(#18) | 1,217 ms | 2,921 h | 1,752 h | **292 h** | 58.4 h |
| GPU ORCA 50 万体 33 ms(#28) | 25.7 ms | 61.8 h | 37.1 h | **6.18 h** | 1.24 h |
| engine_spike 40 万体 28 ms(リポ実測) | 27.3 ms | 65.5 h | 39.3 h | **6.55 h** | 1.31 h |
| Box2D 積み木 5,050 体 0.90 ms(#11・剛体の山) | 69.5 ms | 167 h | 100 h | **16.7 h** | 3.34 h |

- 5,000 体(CPU 系はそのまま): ORCA 円 8 ms → 0.1 s 刻みで 1.92 h/日・0.5 s で 0.38 h/日。**GPU 系を 5,000 体へ縮める線形換算は無効**(原典が「crossover … 2 × 10^3 agents」付近より少ないと CPU が速いと報告)。
- 線形外挿の限界: 近傍探索の密度依存・LOD(engine_spike の 12% で 0.62 h/日 @0.5 s)・スレッド数・世代の違う CPU/GPU を補正していない。汎用剛体エンジンの歩行者規模の一次値は無い(§8)。
- 既存予算との比: P2 ≤300 ms/tick@40 万体(C9 G9)は 0.1 s 刻みなら 1 歩 **0.5 ms**・0.5 s 刻みなら 2.5 ms。W1 ≤24 h/シミュ日(C7 実測 9.167 h)。U15 §2 の P1=物理 ≤10% の壁時計。
- **テープ記録量**: 位置 float32×2=8 B/体(int16 量子化なら 4 B/体・渋谷の範囲 約 4 km を 0.1 m で表すと 40,000 段 < 65,536)。

| 体数 | tick ごと記録 | 1 日(8 B) | 1 日(4 B) | 0.5 s 刻みごと(8 B) | 0.1 s 刻みごと(8 B) |
|---|---|---|---|---|---|
| 5,000 | 40 KB/tick | 57.6 MB | 28.8 MB | 6.9 GB/日 | 34.6 GB/日 |
| 390,067 | 3.12 MB/tick | **4.49 GB** | 2.25 GB | 539 GB/日 | 2.70 TB/日 |

  比較: S1 恒久記録 ≤5 GB/シミュ日・C7 実測 0.175 GB/日([C9 ブリーフ](../design/v2-c9-geometry-brief.md) の予算表)。zstd 圧縮率は本書では測っていない(空欄)。記録を「失敗・到着・視認の変化」のイベントに限る形は件数の分布が要り、見積らない。

## §5 LLM 判断と物理刻みの 2 時間軸の先行

- **歩行者の 3 層**: Vadere 論文の逐語「Microscopic models are often conceptually divided into three levels: (1) the strategic level: activity choice, (2) the tactical level: activity schedule, area and route choice to reach the area and (3) the operational level: walking behavior. A description can be found in [37].」[37]=Hoogendoorn & Bovy 2004(#24)。同論文「Vadere … solely covers the operational level」(#24)。H&B 2004 の抄録は「route choice, activity area choice, and activity scheduling are simultaneously optimized using dynamic programming」で、**3 層の語は抄録に無い**(本文は有料=未読・#25)。
- **Menge**: 「a decomposition of the problem into related subproblems: goal selection, plan computation, plan adaptation, and spatial queries」「the Goal Selection and Plan Computation problems are solved by elements which belong to the BFSM. The Plan Adaptation domain belongs to the pedestrian models element.」・図 1 に「Visibility Query」「Proximity Query」・「At each time step, the system updates event state and task state. Then the BFSM is updated for each agent. Next, the preferred velocity for each agent is computed. The pedestrian model is used to compute a feasible velocity.」・歩行者モデルの契約は「the function mapping preferred velocity to feasible velocity」(#21)。
- **SUMO**: 「--default.action-step-length <TIME> implies that vehicles perform calculations for the adaption of accelerations or lane-change maneuvers only at intervals of the given length and not within every simulations step」「a value larger than the assumed reaction time tau may induce collisions」・step-length は既定 1 s・範囲 [0.001, 1.0](#34)。JuPedSim 連成時は歩行者だけ 0.01 s で「independent of SUMO's simulation cycle」(R7 親確認)。
- **Unity ML-Agents**: 「A DecisionPeriod of 5 means that the Agent will request a decision every 5 Academy steps.」`DecisionPeriod = 5`・`TakeActionsBetweenDecisions = true`(判断の間の Academy ステップでも行動を取る)・Academy は「step the Academy during FixedUpdate phase」(#36)。
- **MATSim**: QSim `timeStepSize = 1.0`(秒)(#35)。
- v2 の現状: 1 tick=60 s・C9a で辺上の連続位置と 1 tick 内のホップ反復(`MAX_HOPS_PER_TICK=32`・Kladek 減速・力学積分なし・IMPLEMENTED #27)。U15-3 は dt 掃引で「1 分 tick 内のサブステップ数」を宣言する形を仮決定([群衆物理設計書](../design/v2-crowd-physics.md))。

## §6 失敗の返し方の先行

- **MATSim**: `PersonStuckEvent` の `EVENT_TYPE = "stuckAndAbort"`・属性 `link`/`legMode`/`person`/`reason`。`stuckTime` 既定 10 =「time in seconds. Time after which the frontmost vehicle on a link is called `stuck' if it does not move.」・`removeStuckVehicles`「`true': stuck vehicles are removed, aborting the plan; `false': stuck vehicles are forced into the next link. `false' is probably the better choice.」(#35)。
- **SUMO 歩行者**: 「if a pedestrian was unable to move for 300s (configurable with option --pedestrian.striping.jamtime) he goes into a 'jammed' state … the person starts moving regardless of obstacles at 1/4 of its maximum speed.」横断歩道上は 10 s(#34)。車両は `--time-to-teleport` で理由つき(「wrong lane」等)にテレポート(#34)。
- **Detour/Unity**: `DT_PARTIAL_RESULT`=到達できず最善推定を返す・群集の目標状態 `DT_CROWDAGENT_TARGET_FAILED`(#29)。Unity「PathPartial The path cannot reach the destination. PathInvalid The path is not valid.」(#37)。
- **D-50 の軽リサーチ**(出典は未一次確認のまま・凍結版 D-50 行): MATSim `stuckAndAbort`・DRT `RequestRejected`・BDI-ABM(行動失敗は計画失敗と別扱い)・Voyager の failed_tasks 等。本書で MATSim の 2 ファイルを一次確認した(上)。
- v2 の現状の失敗型(`agents/state.py` `ResultCode`): 到達不能 1・途中打ち切り(混雑・閉鎖)2・満員 3・…・先に取られた 15・対象が去った 20 の計 20 型(0=成功)。意思決定層へは「直前の結果」50 tok 欄(`RESULT_TEXT` の短句)で返る(同ファイル)。

## §7 v2 への写し方(事実の整理・推奨ではない)

### 7-1 現行の手書き判定の所在(コード・文書の事実)

| 空間系 | いま(既定) | 所在 |
|---|---|---|
| 到達 | W3 全点対 next-hop 表(3,499×3,499・48.97 MB)+失敗 `UNREACHABLE` | [C9 ブリーフ](../design/v2-c9-geometry-brief.md) §1・`engine/resolve.py`(`_fail(..., UNREACHABLE)`) |
| 混雑 | セル密度 `bincount`・Fruin 段階・edge 版は Kladek 式で減速(ρ≥5.4 で停止) | `engine/geometry.py`・IMPLEMENTED #27/#32 |
| 満席 | 床面積÷席面積の席数・行列(`seats_total`/`seats_used`/`queue_len`)・満員(列車) | `engine/processes/crowd.py`・`engine/processes/rail.py` |
| 視線・遮蔽 | 同セル代理+p_see(既定 1.0)。遮蔽表 C9c-2 は C10 の被注視/傍受に束ねて未実装(第228) | C9 アジェンダ §4・G7 |
| 距離 | node 版は同ノード=距離 0。edge 版は `xy` 補間(G7 (b) 会話 2 m は edge 前提) | C9 アジェンダ G1/G7 |

### 7-2 候補 × 軸(公式記述の範囲)

| 候補 | 2D/3D | 決定論(同じ環境) | スレッド数 | 既定/推奨刻み | 規模の一次 | 較正の錨 | ライセンス | Python |
|---|---|---|---|---|---|---|---|---|
| PhysX 5 | 3D(軸ロックで 2D) | ◎ 同シーン・同順・同刻み・同版・同プラットフォーム(GPU は強化決定論なし) | ◎ 影響なし | 公式固定値なし(1/60 は例) | 未確認 | 歩行者の錨の記述なし | Apache 2.0(SDK)/ルート BSD-3 表記 | ovphysx(pre-release) |
| Bullet 3 | 3D | ○ pybullet は同コマンドで一致(作者) | 記述なし | 1/240(py)・60 Hz(C++) | 未確認 | 同上 | zlib | pybullet(公式) |
| Box2D v3 | 2D | ◎ 既定で有効・生成順 | ◎ スレッド数をまたぐ | 1/60+sub-step 4 | 5,050 体 0.90 ms(剛体) | 同上 | MIT | 第三者のみ |
| Jolt | 3D | ◎ 同順+同バイナリ(問い合わせ・コールバック順は非決定) | 非決定の列挙はマルチスレッド由来 | 60 Hz | 未確認 | 同上 | MIT | 第三者(Culverin) |
| Rapier | 2D/3D | ◎ 同機械・同版・同コンパイラ | ◎ 並列=逐次 | 1/60 | 未確認 | 同上 | Apache-2.0 | `rapier3d`(3D のみ) |
| RVO2/ORCA | 2D | 記述なし([コード] 2 相更新) | 記述なし | 例 0.25 s | 5,000 体 8〜15.6 ms | R7: 角で詰まる(Game AI Pro) | Apache-2.0 | 第三者(古い) |
| JuPedSim | 2D(OBJ 面で階層可) | 記述なし | 記述なし | 0.01 s | 未確認 | Jülich 実験の系譜(R7・U15-5) | LGPL-3.0 | 公式 |
| Menge | 2D+高さ場 | 未確認 | 未確認 | 0.002〜0.1 s | 32,000 体の例 | 未確認 | Apache-2.0(○) | 未確認(本体 C++) |
| Vadere | 2D | 未確認 | 未確認 | 未確認 | 実時間は未達(2019) | 未確認 | LGPL | 未確認(本体 Java) |
| Recast/Detour | 3D ナビメッシュ | 記述なし | — | — | 未確認 | — | zlib | 第三者(Windows のみ等) |
| 自前 numba(格子+Amanatides-Woo) | 2D | 実装次第(numba の保証文なし) | 並列縮約は競合の注意 | 自由 | engine_spike 40 万体 28 ms | U15 の錨をそのまま使う | 自前 | 既存依存のみ |
| Warp(GPU) | — | ◎ 1.15 の決定論モード(opt-in) | — | 自由 | R7: GPU 換算は推測扱い | 同上 | 本書では未確認 | 公式 |

### 7-3 「一部だけ先に置き換える」段階案の材料(独立性の事実)

- **視線・遮蔽(静的な建物だけ)**: 入力は PLATEAU の足跡など**動かない幾何だけ**で、体の位置の表現(node/edge)にも移動モデルにも依存しない。事前計算の表(G13 (iii))にも、tick 内のレイ走査(Amanatides-Woo・Box2D/Jolt の ray cast)にもできる。**人による遮蔽**を入れると連続位置と同じ刻みの位置が要る(=混雑と同じ層に依存)。
- **到達(経路)**: 入力は静的な歩行網/歩行面。W3 表の置き換え先の候補は Detour(`DT_PARTIAL_RESULT`/`DT_FAILURE` は既存 `UNREACHABLE` に対応づけうる)。混雑を経路コストに入れない限り他と独立。
- **混雑(速度と局所密度)**: 群集モデル(CFSM 等)は連続位置+サブステップが前提で、C9a の辺上位置(IMPLEMENTED #27)の上に載る。距離(会話 2 m・傍受)と人による遮蔽は同じ位置を読む=**混雑を置き換えると距離も同時に変わる**。
- **満席**: 調べた物理エンジン・群集実装に「席・収容数」の意味論は無い(問い合わせは overlap/センサー・Box2D)。席を物理にするには席の位置と形の資産が要る(本書では資産の有無を調べていない)。
- **決定論の切り分け**: 静的幾何の表(視線・到達)は事前計算=ラン内の非決定を持ち込まない。tick 内で外部エンジンを回す場合、公式に「同じ環境で一致」を言うのは PhysX(CPU)・Box2D・Jolt(問い合わせとコールバック順を除く)・Rapier。第280 の「記録して再生」の対象になりうるのは、公式の保証文が無い/保証外のもの=GPU の PhysX(強化決定論が GPU 非対応)・Warp の既定モード・numba の並列縮約・決定論の記述が無い群集実装。

### 7-4 既存決定との関係(事実のみ)

- C9 アジェンダ **G13(ユーザー案 09-17)**: 「物理エンジンで実測(計算)をシミュレーションを回す**前**に済ませ、ランの中ではそのモデル(表・解析式)で擬似的に再現する」・「物理エンジンは『表を作る側』だけに使い、tick 内では回さない」([C9 アジェンダ](../design/v2-c9-geometry-agenda.md) §4・`engine/geometry.py` の docstring にも同旨)。本件の「空間系を物理に任せる」は、G13 の「表を作る側」の範囲に収まる部分(静的な視線・到達・ボトルネック容量)と、tick 内で回す部分(混雑・人による遮蔽・距離)に分かれる。
- **U15(仮決定 09-08)**: 方式 CFSM 第 1 候補/AVM 第 2/SFM 対照/ORCA・連続体は不採用・Warp HashGrid・dt 掃引・LOD・Jülich 較正([群衆物理設計書](../design/v2-crowd-physics.md) §1)。本書の汎用剛体エンジン 5 種は U15 の候補表に入っていない。
- C9 G10: 群衆物理(CFSM)は「C9 の後」。pyproject は GPU(warp-lang/cupy)を「C0 では入れない」。

## §8 未確認・空欄

- Bullet フォーラムの作者発言(viewtopic t=1630・t=12755)=接続タイムアウト 2 回。CGAL の 2D Visibility とライセンス頁=取得失敗。Unreal の経路追従結果の型=ソース非公開で未取得。
- PhysX GPU の決定論(既定)・PhysX/Jolt/Rapier/Bullet の 1 万〜40 万体の歩行者/キャラクタ実績・Menge 図 7 の数値・JuPedSim の公式ベンチ・Vadere の刻みと seed 機構・PySocialForce の刻みの単位・MomenTUM の規模・Menge/Vadere/JuPedSim/RVO2 の決定論の公式記述(無いのか未発見かを区別できていない)。
- Hoogendoorn & Bovy 2004 本文の 3 層の逐語(Vadere 経由のみ)。shapely に可視多角形の関数が無いこと(文書未確認)。Warp のライセンス。テープの zstd 圧縮率。Unity の `fixedDeltaTime` 既定値(ページに値の記述なし)。

## §9 サブの注記(推奨ではない)

- 決定論の「同じ環境」の範囲は候補ごとに語が違う(PhysX=同じリリース+同じプラットフォーム/Jolt=同じバイナリ/Rapier=同じ機械+同じ版+同じコンパイラ/Box2D=プラットフォームをまたぐ)。第280 の方針への当てはめは親の判断。
- §4 の外挿は刻み・体数とも線形の粗い見積りで、出発値のハードウェアが 2011 年 CPU・2019 年 GPU・2024 年 CPU・リポ実測機(2026)と混在する。
