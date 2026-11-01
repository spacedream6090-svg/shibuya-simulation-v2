# R-59 答申: ナビメッシュの実装候補・経路探索の費用・物理とのつなぎ・歩ける面の材料(D-122 / 指示書 09-30 §1-4・§1-7)
<!-- hdr:v1 -->
- **分野**: ゲーム・VR 技術の輸入(常設レーン) / 歩行者動力学 #18 / 計算幾何 | **重要度**: P0(空間の設計ラウンドの材料)
- **一次確認**: **B** = サブ実読(出典 25 件=◎ 22〔公式リポのソース行・LICENSE 本文・公式文書・原論文本文を curl → 標準出力で読んだもの〕・○ 2〔PyPI の JSON メタ情報〕・△ 1〔検索要約〕)+手元計測 1 本(スクリプトと JSON を同梱)。**親の一次確認前**。
- **索引**: [INDEX.md](INDEX.md) ・ **先行答申**: [R-53 エンジン比較](v2-r53-spatial-physics-engine-candidates-research.md)(親検収済)・[空間層の草案](../design/v2-spatial-physics-layer-draft.md)
- 規律: 子サブ未起動・Web は読むだけ(保存なし・clone なし・pip install なし)・コミットなし・台帳/設計書/src 未編集。書いたのは本書と `docs/research/r59/`(.py 1 本・.json 1 本)だけ。**推奨は §6 に「未リサーチ(expedient)を含む案」として分けて書く**。

## 結論 5 行

1. **手元の PLATEAU 道路 LOD3 は既に三角形に分かれている**(`tran_lod3.npz`・重複を畳んで歩道部 18,794 枚/道路面全体 48,566 枚)。三角分割の道具を新たに入れなくても、これを溶接すればナビメッシュの材料になる。ただし**歩道部(2000)だけでは 343 個の島に切れる**(最大の塊が全体の 1.8%)。交差部(1020)・島(3000)を足しても最大の塊は 69%。車道部(1000)まで足すと 99.8% がつながる。**横断歩道は PLATEAU のコード表に無い**(§5)ので、歩道の無い細い道の車道と、横断歩道の帯を足す規則が要る。
2. **1 回の探索の費用(実測・numba・単スレッド)**: 道路面全体(45,978 枚)で三角形の双対グラフの A* と funnel を合わせて **p50 0.81 ms・p95 2.87 ms**、200 m 四方の中なら p50 0.03 ms。1 日 102 万〜400 万回(§2-3)なら **0.23〜3.2 CPU 時間/シミュ日**。目的地 1 つから全三角形への距離場は **5.4 ms・368 KB**。固定の目的地 9,643 個(入口・POI・駅出口)を全部前計算しても **約 52 秒・3.5 GB**。
3. **「全組の next-hop 表は作れない」はこの規模では厳密には成り立たない**: 46k 枚なら int32 で 8.5 GB、隣の番号(3 通り=2 bit)にすれば 0.53 GB。**作れない本当の理由は費用が人ごとに違うこと**(§1-4 の経路コスト=混雑・信号・慣れ・屋根・急ぎ)。静的な表は「全員同じ費用」でしか使えない。三角形が 10 万〜20 万枚に増えれば(階・デッキ・地下街)2 bit でも 2.5〜10 GB になる。
4. **ライセンス**: Recast/Detour=zlib(商用可)。ただし Linux で使える保守中の Python 版は見つからなかった。CGAL の三角分割・最短路・可視性は **GPL**(商用ライセンスは別売)。**JuPedSim(LGPL-3)は CGAL の GPL 部分(CDT・Surface_mesh_shortest_path)をソースに同梱してビルドしている**(どういう条件で使えるかの公開の記述は見つからない=未確認)。triangle/meshpy(Shewchuk)は「**商用システムの一部として配布するには作者との直接の取り決めが要る**」。shapely 2.1 の `constrained_delaunay_triangles` は BSD-3 で、中の GEOS は LGPL-2.1(動的ライブラリ)。
5. **推奨(expedient)**: PLATEAU の三角形をそのまま土台にし、溶接・接続・A*・funnel・距離場を **numba で自前実装**する(依存を足さない・Windows/Linux 同じ・決定論を自分で保証できる・検算済み)。退路は shapely 2.1(横断歩道の帯や穴の後処理・pip の許可が要る)と Recast/Detour の自前ビルド。JuPedSim は照合用の参照実装にとどめる。v1.4.2 は**毎刻み・全員について経路を一から引き直す**作りで、39 万体の本番には向かない(§3)。

---

## §0 等級・出典表

- 等級: **◎** = 原典(公式リポのソース行・LICENSE 本文・公式文書・原論文本文)を curl → 標準出力 → 文字列で読んだもの / **○** = PyPI の JSON API のメタ情報(版・日付・依存・wheel の種類) / **△** = 検索の要約だけ / 空欄 = 未確認。
- R-53 で確認済みの事実(再確認せず引く): PyRecastDetour「Windows only」・recastlib の更新停止(R-53 #30)、Detour の `DT_PARTIAL_RESULT`(#29)、JuPedSim の `dt=0.01` 既定と「floors may be stacked」(#23)、Menge の分解(#21)、Vadere の 3 層の記述(#24)。

| # | 出典 | URL | 等級 | 取れた範囲 |
|---|---|---|---|---|
| N1 | JuPedSim `docs/source/concepts/routing.rst`(master) | https://github.com/PedestrianDynamics/jupedsim/blob/master/docs/source/concepts/routing.rst | ◎ | Way finding の節 |
| N2 | JuPedSim v1.4.2 `libsimulator/src/RoutingEngine.hpp`・`RoutingEngine.cpp`・`TacticalDecisionSystem.hpp`・`Simulation.cpp` | https://github.com/PedestrianDynamics/jupedsim/tree/v1.4.2/libsimulator/src | ◎[コード読み] | CDT・TA* の g/h・funnel・呼ばれる頻度 |
| N3 | JuPedSim master `SurfaceMeshShortestPathRoutingEngine.hpp`・`RoutingEngine.hpp`・`CfgCgal.hpp`・`third-party/CMakeLists.txt` | https://github.com/PedestrianDynamics/jupedsim/tree/master/libsimulator/src | ◎[コード読み] | 3D の経路エンジン(未リリース)・CGAL 6.1.2 を同梱 |
| N4 | JuPedSim v1.4.2 `python_modules/jupedsim/jupedsim/routing.py` | https://github.com/PedestrianDynamics/jupedsim/blob/v1.4.2/python_modules/jupedsim/jupedsim/routing.py | ◎ | Python の `RoutingEngine.compute_waypoints` |
| N5 | JuPedSim v1.4.2 `CollisionFreeSpeedModel.cpp`・`CollisionGeometry.hpp` | 同上 | ◎[コード読み] | 望む向き=次の経由点・壁=線分・4 m 格子 |
| N6 | JuPedSim `LICENSE` と PyPI | https://github.com/PedestrianDynamics/jupedsim/blob/v1.4.2/LICENSE ・ https://pypi.org/pypi/jupedsim/json | ◎/○ | LGPL-3+・1.4.2(2026-05-21)・依存 |
| N7 | CGAL `Installation/LICENSE`・各パッケージの `package_info/*/license.txt` | https://github.com/CGAL/cgal/blob/master/Installation/LICENSE | ◎ | パッケージごとの GPL/LGPL(cgal.org/license.html は 403 で読めず) |
| N8 | cgal-swig-bindings(PyPI `cgal`) | https://pypi.org/pypi/cgal/json | ○ | 6.0.1(2024-10-25)・GPLv3+ の分類子 |
| N9 | Recast/Detour `License.txt`・`README.md`・`Docs/_1_Introduction.md`・`DetourNavMeshQuery.h`・`DetourNavMesh.h`・releases API | https://github.com/recastnavigation/recastnavigation | ◎ | zlib・ボクセル化・off-mesh 接続・問い合わせ API・v1.6.0(2023-05-21)・最終コミット 2026-02-27 |
| N10 | Path-Finder(PyPI `pynavmesh`)README | https://github.com/Tugcga/Path-Finder | ◎/○ | MIT・「最適を保証しない」・1.2.5(2023-12-15)・push 2024-09-24 |
| N11 | triangle(drufat)`LICENSE`・同梱の Triangle `README`・`triangle.c` の冒頭 | https://github.com/drufat/triangle ・ https://github.com/drufat/triangle-c | ◎ | 包み=LGPL-3・中身=Shewchuk の条件 |
| N12 | meshpy `LICENSE` | https://github.com/inducer/meshpy/blob/main/LICENSE | ◎ | Triangle License をそのまま含む |
| N13 | shapely `docs/release/2.x.rst`・`README.rst`・GEOS `COPYING` | https://github.com/shapely/shapely ・ https://github.com/libgeos/geos | ◎ | 2.1.0 で `constrained_delaunay_triangles` 追加(GEOS ≥3.10)・BSD-3・GEOS=LGPL-2.1 |
| N14 | mapbox_earcut(Python)`LICENSE.md`・earcut.hpp `README.md`・`LICENSE` | https://github.com/skogler/mapbox_earcut_python ・ https://github.com/mapbox/earcut.hpp | ◎ | ISC・品質より速さ・穴に対応・bit 一致の記述 |
| N15 | Menge `VelCompNavMesh.h`・`PrefVelocity.h`・`VelCompVF.h`・`ElevationNavMesh.h`・commits API | https://github.com/MengeCrowdSim/Menge | ◎[コード読み] | 望む速度の型・経路からのずれで引き直す・最終コミット 2019-08-24 |
| N16 | Kleinmeier ら 2019「Vadere」 | https://arxiv.org/abs/1907.09520 | ◎(PDF 本文) | eikonal の床場・EikMesh |
| N17 | Cui, Harabor, Grastien 2017「Compromise-free Pathfinding on a Navigation Mesh」(Polyanya) | https://www.ijcai.org/proceedings/2017/0070.pdf | ◎ | 抄録 |
| N18 | Demyen & Buro 2006「Efficient Triangulation-Based Pathfinding」(TA*) | https://cdn.aaai.org/AAAI/2006/AAAI06-148.pdf | ◎ | 抄録 |
| N19 | Botea, Müller, Schaeffer 2004「Near Optimal Hierarchical Path-Finding」(HPA*) | http://webdocs.cs.ualberta.ca/~mmueller/ps/2004/hpastar.pdf | ◎ | 抄録 |
| N20 | Treuille, Cooper, Popović 2006「Continuum Crowds」 | https://grail.cs.washington.edu/projects/crowd-flows/78-treuille.pdf | ◎ | 抄録・序論 |
| N21 | SUMO `docs/web/docs/Simulation/Pedestrians.md` | https://github.com/eclipse-sumo/sumo/blob/main/docs/web/docs/Simulation/Pedestrians.md | ◎ | crossing・walkingarea・`--crossings.guess` |
| N22 | OSM Wiki `Key:area:highway`・`Tag:footway=crossing` | https://wiki.openstreetmap.org/wiki/Key:area:highway ・ https://wiki.openstreetmap.org/wiki/Tag:footway%3Dcrossing | ◎(`action=raw`) | 道路の面の描き方・横断歩道の線 |
| N23 | PLATEAU コードリスト `TrafficArea_function.xml`・`AuxiliaryTrafficArea_function.xml`(i-UR 3.1) | https://www.geospatial.jp/iur/codelists/3.1/TrafficArea_function.xml | ◎ | 機能コードの一覧 |
| N24 | PyPI JSON(shapely・scipy・triangle・mapbox-earcut・trimesh・pyvista・pathfinding・networkx・rustworkx・meshpy・pymeshlab) | https://pypi.org/pypi/<name>/json | ○ | 版・日付・ライセンス分類子・wheel の OS |
| N25 | 検索要約「wow-navmesh」(Detour だけの Python 包み・Windows のみ) | https://github.com/srounet/wow-navmesh | △ | 要約だけ(本文未読) |

---

## §1 候補の一覧と比較(作業 1)

### 1-1 事実(公式の文書・ソース)

- **JuPedSim の経路(N1〜N5)**
  - 文書(N1): 「To determine the route, *JuPedSim* triangulates the geometry and computes the distance between two points through the triangulation. Here, it will compute the distance between the centers of two neighboring triangles. When multiple paths lead to the target, the shortest one will be preferred.」
  - v1.4.2 の実装(N2): CGAL の `Constrained_Delaunay_triangulation_2` に外周と穴を制約として入れ、`mark_domain_in_triangulation` で内側を印付け。探索は TA*(コメントに Demyen の定理番号「Theorem 4.2.12」)。h=目的点から共有辺までの距離、g=3 つの下界の最大。目的の三角形に着いた候補は**全部 funnel にかけて最短を採る**(「Unlike in A* this is only a first candidate solution」)。funnel は「This is the actual simple stupid funnel algorithm」。開いたリストの探索は「TODO(kkratz): replace this find on unsorted vector with something with a better runtime」。
  - **呼ばれる頻度(N2)**: `TacticalDecisionSystem.hpp:22` `agent.destination = routingEngine.ComputeWaypoint(agent.pos, dest);` が全エージェントについて回り、`Simulation.cpp:55` の `Iterate()` から**毎イテレーション**呼ばれる。`ComputeWaypoint` は `ComputeAllWaypoints(...)[1]`=**毎回、経路全体を一から探索**している。
  - master(未リリース・N3): 3D の `SurfaceMeshShortestPathRoutingEngine`(CGAL `Surface_mesh_shortest_path`)。「The sequence tree for @p target: built on first use, then kept.」=**目的地ごとに木を作って保持**する形。壁からの離れ `wallClearance = 0.2`(既定)。
  - 同梱物(N3): `third-party/cgal` を `find_package(CGAL 6.1.2 ... PATHS ${CMAKE_CURRENT_SOURCE_DIR}/cgal)` で使う。
  - Python(N4): `jupedsim.RoutingEngine(geometry).compute_waypoints(frm, to)`。1 回に 1 組で、配列で一括の口は無い。geometry は shapely の Polygon/MultiPolygon/WKT。
  - ライセンス・版(N6): LGPL-3.0-or-later。PyPI 1.4.2(2026-05-21)・Python 3.10〜3.14・wheel は win_amd64・manylinux x86_64・macOS。**依存 = numpy・shapely・pyside6・vtk・deprecated**。
- **CGAL(N7・N8)**: 「It is specified in each file of the CGAL library which license applies to it. This is either the GNU General Public License or the GNU Lesser General Public License」「It is also possible to obtain commercial licenses from GeometryFactory」。パッケージごとの `license.txt`: **Triangulation_2・Mesh_2・Surface_mesh_shortest_path・Surface_mesh・AABB_tree・Visibility_2 = GPL (v3 or later)** / Polygon・Kernel_23 = LGPL。Python の公式束縛 `cgal`(PyPI)6.0.1 は 2024-10-25・GPLv3+ の分類子・win/linux の wheel あり。
- **Recast/Detour(N9)**: zlib「Permission is granted to anyone to use this software for any purpose, including commercial applications」。作り方=「First Recast rasterizes the input triangle meshes into voxels.」(=**ボクセルの細かさ `cs` で形が丸まる**)。「Robustly handles large amounts of overlapping geometry」(高さ方向のスパンで重なった床を扱う)。層の間は **off-mesh 接続**「An off-mesh connection is a user defined traversable connection made up to two vertices.」(双方向のフラグあり)。問い合わせ=`findPath`・`findStraightPath`・`raycast`・`findDistanceToWall`・`moveAlongSurface`・`initSlicedFindPath`(分割探索)。タイル化と「heirarchical path-planning」(README の綴りのまま)。最終リリース v1.6.0(2023-05-21)・最終コミット 2026-02-27。Python は R-53 のとおり(PyRecastDetour=Windows のみ)に加え、検索で Detour だけの `wow-navmesh`(Windows のみ・WoW 形式専用)を見た(△・N25)。**Linux で保守中の汎用 Python 束縛は見つからない**。決定論の記述は無い(R-53)。
- **Path-Finder / pynavmesh(N10)**: MIT。「find closest path between centers of polygons by using A* algorithm in dual graph」「the path finding algorithm does not guaranteer the optimality of the generated path」。Recast の 1 手法を Python に移植して焼く機能あり。pure Python(`any` の wheel)・1.2.5(2023-12-15)。
- **triangle / meshpy(N11・N12)**: Python の包みは LGPL-3 だが、中の Triangle(Shewchuk)は「Private, research, and institutional use is free.」「**Distribution of this code as part of a commercial system is permissible ONLY BY DIRECT ARRANGEMENT WITH THE AUTHOR.**」。meshpy の LICENSE も同じ Triangle License を含む。制約つき Delaunay・品質メッシュ(最小角)が作れる。triangle 20250106(2025-01-07)・win/linux の wheel あり。
- **shapely(N13)**: 2.1.0(2025-04-03)の新関数に「`constrained_delaunay_triangles` (#1685) (requires GEOS >= 3.10)」。「Shapely is licensed under BSD 3-Clause license. GEOS is available under the terms of GNU Lesser General Public License (LGPL) 2.1」。GIL を外して GEOS を回す(README)。最新 2.1.2(2025-09-24)。**.venv に無い**。
- **mapbox_earcut(N14)**: 包み=ISC・中身の earcut.hpp=ISC。「Earcut favors raw speed and simplicity over triangulation quality」「extended to handle holes … in a way that doesn't _guarantee_ correctness of triangulation」。オプションの `refine` について「unlike `earcut` it does not promise bit-identical output across compilers」。2.1.0(2026-09-08)。
- **その他(N24)**: `pathfinding`(MIT)は格子の A* の道具(ナビメッシュではない・本文未読で README の範囲は未確認)。trimesh(MIT)・pyvista(MIT)はメッシュの入出力と可視化で、制約つき 2D 三角分割の関数は本書では確認していない(空欄)。scipy は `scipy.spatial.Delaunay`(qhull)が制約なし(文書は未読=空欄)。scipy・shapely・networkx は **.venv に無い**(`pip list` で確認)。

### 1-2 比較表

| 候補 | 役割 | ライセンス(商用の扱い) | Windows/Linux | 最終リリース・保守 | 多層(階・縦の接続) | 穴・細い通路 | 決定論の記述 | Python から(一括) | 依存 |
|---|---|---|---|---|---|---|---|---|---|
| **自前 numba**(本書の計測) | 溶接・隣接・A*・funnel・距離場 | 自前 | 同じコード | — | 三角形が z を持つ+off-mesh 型の辺を足せば可(未実装) | PLATEAU の面の形のまま(ボクセル化の丸めなし) | **自分で保証**(同点規則・整数の溶接・逐次)=§4 で 200 組を 2 回一致 | ◎ 配列で持つ | numpy・numba(既存) |
| JuPedSim 1.4.2 | CDT+TA*+funnel/物理 | LGPL-3+。**中に CGAL の GPL 部分**(条件は未確認) | ✓/✓ | 2026-05-21・活発(master 2026-09-29) | 1.4.2 は 2D。master に 3D の面(未リリース) | 穴=制約辺。`wallClearance` 0.2 m(master) | 記述なし(R-53) | 1 組ずつ | shapely・pyside6・vtk |
| Recast/Detour | ボクセル→ナビメッシュ・探索・群集 | zlib(**商用可**) | C++ は両方。Python 版は Windows のみ | v1.6.0(2023-05)・コミット 2026-02 | ◎ 重なった床(スパン)+ off-mesh 接続 | ボクセルの細かさ `cs` と歩行半径で縁が削られる | 記述なし(R-53) | 汎用の束縛なし(自前ビルドが要る) | C++98 のみ |
| CGAL(公式束縛 `cgal`) | CDT・メッシュ・測地線・可視性 | **GPL**(商用ライセンスは別売) | ✓/✓ | 束縛 2024-10 | Surface_mesh_shortest_path で 3D の面 | 制約辺で厳密 | 厳密述語(Exact_predicates)。順序の記述は未確認 | 束縛の API は未読 | numpy |
| triangle / meshpy | CDT・品質メッシュ | 包み LGPL-3/**中身は商用配布に作者の許可が要る** | ✓/✓ | 2025-01 / 2026-09 | なし(2D) | 制約辺・最小角・最大面積 | README「exact Delaunay」(順序の記述なし) | 配列で渡す | numpy |
| shapely ≥2.1 | CDT(GEOS)・多角形演算 | BSD-3/GEOS=LGPL-2.1(同梱の動的ライブラリ) | ✓/✓ | 2.1.2(2025-09) | なし(2D) | 穴つき Polygon | 未確認 | ベクトル化の ufunc | numpy |
| mapbox_earcut | 耳切り(穴あり) | ISC | ✓/✓ | 2.1.0(2026-09) | なし | 穴に対応・品質は保証しない | earcut 本体は bit 一致を含意(N14 の対比文)・refine は非保証 | 配列で渡す | numpy |
| Path-Finder(pynavmesh) | 焼く+重心 A* | MIT | pure Python | 2023-12 | 未確認 | Recast の手法の移植 | 記述なし | Python のループ | なし |
| Menge | 望む速度の部品(ナビメッシュ・道路図・ベクトル場) | Apache-2.0(R-53) | C++ | 最終コミット 2019-08 | 高さ場(`ElevationNavMesh`) | ナビメッシュの障害物 | 未確認 | 未確認 | — |
| Vadere | eikonal の床場+自前メッシュ(EikMesh) | LGPL(R-53) | Java | 未確認 | 未確認 | 床場の格子/メッシュの細かさ | 未確認 | Java | — |

---

## §2 経路の探索の方法と費用(作業 2)

### 2-1 方法(原典の逐語)

- **TA*(N18)**: 「abstracting an environment represented using constrained Delaunay triangulations … almost all paths are found much faster using TA*, and more so using TRA*」。JuPedSim 1.4.2 の実装がこれ(N2)。
- **Polyanya(N17)**: 「When the mesh is static, shortest path problems can be solved exactly and very fast but only after a costly preprocessing step. When the mesh is dynamic, practitioners turn to online methods which typically compute only approximately shortest paths. … Polyanya … is simultaneously fast, online and optimal.」(実装のライセンスは未確認=空欄)
- **重心 A*+funnel(N10・本書の計測)**: 最適は保証されない。本書の検算で広い面では **+1.7〜2.3%**(§4-1)。
- **HPA*(N19)**: 「At the local level, the optimal distances for crossing each cluster are pre-computed and cached. At the global level, clusters are traversed in a single big step.」「up to 10 times faster, while finding paths that are within 1% of optimal」(格子の地図で)。
- **流れ場/目的地ごとの距離場**: Vadere の床場「the eikonal equation is a widely used approach to obtain the geodesic distance between a destination and each position in the topography」(N16)。Continuum Crowds「Our formulation is designed for large groups with common goals, not for scenarios where each person's intention is distinctly different.」(N20)。JuPedSim master の「目的地ごとに木を作って保持」(N3)も同じ考え。

### 2-2 費用の実測(§4 の数字を再掲)

| 面 | 三角形数 | 1 回の探索 p50/p95/最大 | 展開数 p50/p95 | 距離場 1 本 | 距離場のメモリ/本 |
|---|---|---|---|---|---|
| 道路面全体(1000+1020+2000+3000) | 45,978 | **0.81/2.87/9.5 ms** | 6,018/18,779 | **5.37 ms** | 368 KB(float32 距離+int32 次の三角形) |
| 同・200 m 四方の中の 2 点 | 同上 | 0.030/0.088 ms | 225/742 | — | — |
| 歩道部+交差部+島 | 28,269(最大の塊 19,411) | 0.33/0.96 ms | 3,536/10,023 | 1.44 ms | 226 KB |

### 2-3 1 日の回数の見積り([サブ計算]・リポの記録から)

- 下限: PT のトリップ原単位 **2.61/人日**([パターン台帳 D6](../design/v2-pattern-ledger.md))× 390,067 = **約 102 万回/日**。
- 中: LLM の応答 **6.90 呼/体/日 = 2,691,795 呼/日**(c7-day-4 実測・[詳細の概観](../design/v2-architecture-overview-detailed.md) §L4)を「起床 1 回で探索 1 回」の上界とみなすと **約 269 万回/日**。
- 上限: L4 の上限 **400 万呼/日**。指示書 §1-6 の「起床時の知覚の描画 1 日 300〜500 万回」も同じ桁。
- 費用 = 回数 × 1 回(p50 0.81 / 平均 1.08 / p95 2.87 ms): **102 万回 → 0.23〜0.81 h・269 万回 → 0.61〜2.14 h・400 万回 → 0.90〜3.19 h(1 スレッド)**。探索は人ごとに独立なので、体の番号で書き分ければ並列にしても結果は変わらない(§6-3)。
- 対比: JuPedSim 1.4.2 の作り(毎刻み・全員が引き直す)をそのまま 39 万体に当てると、0.5 s 刻みで 390,067 × 120 × 1,440 = **6.7×10¹⁰ 回/日**(1 ms/回なら 1.9 万 h)。**経路は起床時に 1 回引いて持ち、ずれたときだけ引き直す**(Menge の `setHeadingDeviation`「Sets the angular deviation which triggers replanning.」・N15)形でなければ桁が合わない。

### 2-4 全組の next-hop 表のメモリ([サブ計算])

| 三角形数 N | int32 の表(N²×4 B) | 隣の番号 2 bit(N²/4 B) | 全部を Dijkstra で作る時間(N×1 本) |
|---|---|---|---|
| 28,269(歩道+交差部+島) | 3.2 GB | 0.20 GB | 約 41 s |
| 45,978(道路面全体・実測) | **8.5 GB** | **0.53 GB** | 約 247 s |
| 100,000(階・デッキ・地下街を足した想定・expedient) | 40 GB | 2.5 GB | — |
| 200,000(同) | 160 GB | 10 GB | — |

- 読み: いまの面の広さなら**メモリでも時間でも作れてしまう**。作れない(使えない)理由は別にある: (i) 経路コストが人ごと・時刻ごとに違う(指示書 §1-4 = 混雑・坂・信号・縦の接続の待ち+曲がる回数・慣れた道・雨天の屋根・急ぎ)。静的な表は「全員同じ費用」のときだけ正しい。(ii) 三角形の next-hop は重心の道で、最短の幾何の道ではない(+2% 前後・§4-1)。(iii) 階・デッキ・地下街・建物の上階を足すと N が増え、N² で膨らむ。
- **固定の目的地の距離場は安い**: 入口 7,261+POI 2,337+駅出口 45 = 9,643 本 × 5.37 ms ≈ **52 s**、× 368 KB ≈ **3.5 GB**(float32+int32)。「距離の見積り」(到達の時間予算=TOO_FAR)と「全員同じ費用で足りる用途」はこれで引ける。人ごとの重みが入る経路は起床時に A* を 1 回引く。

---

## §3 群集の物理とのつなぎ(作業 3・R-53 と重ならない範囲)

- **JuPedSim(N5)**: 物理(CFSM)の「望む向き」は **次の経由点へ向かう単位ベクトル** `const auto desired_direction = (ped.destination - ped.pos).Normalized();`(v1.4.2 `CollisionFreeSpeedModel.cpp:85`)。`ped.destination` は §2 の `ComputeWaypoint`(funnel の 2 点目)。**壁は線分**で、`CollisionGeometry` が 4 m 格子(`const int CELL_EXTEND = 4;`)に線分を入れ、`LineSegmentsInApproxDistanceTo(ped.pos)` で近くの壁を引く。さらに隣人との間に壁の線分があれば、その隣人を相手にしない(同 51〜61 行)。
- **Menge(N15)**: 望む速度は「span」(左端・右端・好みの向き・速さ・目標点)。`PrefVelocity::getTarget()` を持つ。ナビメッシュの部品は「Graph searches through the mesh are performed to find paths through arbitrarily complex environments.」、**経路からのずれが角度の閾値を超えたら引き直す**。他に道路図(`VelCompRoadMap`)・一様格子のベクトル場(`VelCompVF`「uniformly discretized 2D grid」)の部品がある。高さは `ElevationNavMesh`「If an agent (or a point) cannot be located on the mesh, its elevation is zero.」。
- **Vadere(N16)**: 望む向きは床場(eikonal の解 u)の勾配。「For all positions inside obstacles, f is zero, that is, the wave stops.」。床場の計算のために自前のメッシュ生成(EikMesh)を持つ。
- **Recast/Detour(N9)**: 「you should not use the navmesh or paths generated by the navmesh as collision geometry or animation splines」(`Docs/_1_Introduction.md` の前半)。**ナビメッシュは経路の構造で、壁との衝突は物理側で持つ**という切り分け。
- **v2 への写し(未リサーチ=expedient)**: 起床時に経路(三角形の列+funnel の経由点)を 1 回引いて体ごとに持つ → 物理の各刻みでは「次の経由点への単位ベクトル × 希望速度」を望む速度として渡す(JuPedSim と同じ形)→ 経由点に近づいたら次へ進める → 体が経路の三角形の列から外れたら(押し出された等)その体だけ引き直す(Menge の形)。壁はナビメッシュの境界辺(実測では境界辺 11,451 本・道路面全体)を線分として近傍の格子に登録する(JuPedSim の形)。固定の目的地へ向かう大勢(駅の出口へ向かう流れ等)は距離場の勾配でも与えられる(Vadere の形)。

---

## §4 手元での計測(作業 4)

- スクリプト: [`docs/research/r59/measure_navmesh.py`](r59/measure_navmesh.py)(numpy 2.5.3・numba 0.67.0・新しい依存なし)。結果: [`docs/research/r59/measure_navmesh.json`](r59/measure_navmesh.json)。CPU 20 論理コア(Intel Family 6 Model 198)・**単スレッド**。1 回の探索の時間は Python から numba を呼ぶ往復と、経路を Python のリストでたどる時間を含む。
- 材料: `data/plateau/tran_lod3.npz`(PLATEAU 渋谷区 2025 の道路 LOD3・clip 2.882 km²・`quant_scale` 0.05 m)。**全部が三角形**で、同じ三角形が 2〜6 回入っている(`tools/build_geo/walkable_area.py` の docstring の確定事実)=完全一致を畳んだ。`walkable_area.py` の出力(`c9c_walkable_area.parquet`)はセルごとの面積で形を持たないため、ナビメッシュの材料にはならない。
- .venv に scipy・shapely が無いので、三角分割は作らず **PLATEAU の三角形を使った**。200 m 四方の窓は原点(渋谷駅付近)中心の [-100,100]²。

### 4-1 検算(答えの分かる場面・第 0-1 規律)

| 場面 | funnel の長さ | 解析解 | 判定 |
|---|---|---|---|
| 幅 1 の直線の帯 | 9.013878189 | 9.013878189 | 一致 |
| 幅 1 の L 字(角を 1 つ回る) | 17.029386366 | 17.029386366 | 一致 |
| 幅 1 の U 字(角を 2 つ回る) | 25.029386366 | 25.029386366 | 一致 |
| 広い正方形(通路が一意でない) | 12.2228 | 11.9474 | **+2.31%**(重心 A* の通路が最短でない) |
| 幅 2 の L 字 | 14.1421 | 14.1421 | 一致 |
| 広い U 字 | 16.6562 | 16.3693 | **+1.75%** |

→ funnel は正しい。**重心 A* が選ぶ通路は最短とは限らない**(Path-Finder の README の記述と整合)。直すには、TA*(JuPedSim 1.4.2 のように着いた候補を全部 funnel にかける)か Polyanya。

### 4-2 面の連結(溶接の許容差ごと)

| 面(PLATEAU の機能コード) | 一意の三角形 | 溶接 0.05 m: 塊の数/最大の塊の割合 | 0.10 m | 0.20 m | 0.50 m |
|---|---|---|---|---|---|
| 歩道部 2000 | 18,794(103,103 m²) | 343 / **1.8%** | 293 / 2.2% | 252 / 2.1% | 237 / 2.1% |
| 歩道部+車道交差部 1020+島 3000 | 29,835 | 342 / 54.0% | 300 / **68.7%** | 273 / 66.2% | 269 / 80.5% |
| +車道部 1000(道路面全体) | 48,566 | 22 / 99.1% | 11 / **99.8%** | 5 / 99.8% | 4 / 99.97% |

- 溶接 0.10 m で三角形は 18,794 → 17,801(潰れた細い三角形が落ちる・面積は 103,103 → 103,094.6 m²)。三角形の面積 p5/p50/p95 = 0.05/1.48/25.7 m²(歩道部)・辺の長さ p50 3.1 m。
- **3 枚以上で共有する辺**が 7〜59 本ある(溶接で重なった面)。**境界辺**は道路面全体で 11,451 本(内部辺 63,139 本)。
- 読み: 歩道部は**車道と交差部で切れた短冊の集まり**で、単独ではナビメッシュにならない。塊が溶接の許容差で減ることから、隣り合う地物が頂点を共有しない所(T 字の継ぎ目)がある**と推測**(T 字の継ぎ目の本数は数えていない=§7 未確認)。

### 4-3 探索の時間(2,000 組・seed 59)

- §2-2 の表のとおり。道路面全体の経路長 p50 800 m・p95 1,471 m、**直線距離に対する比 p50 1.21・p95 1.66**、経由点(funnel の角)p50 35・p95 71。歩道+交差部+島では比 p50 1.41・p95 2.41(車道を渡れない分の遠回り=横断歩道が足りない分を含む)。
- **決定論**: 同じ 200 組を 2 回引いて経由点の列がバイト一致(3 面とも `true`)。

---

## §5 歩ける面の材料(作業 5)

### 5-1 手元に在るもの(事実)

| 材料 | 中身 | ナビメッシュでの役 |
|---|---|---|
| PLATEAU 道路 LOD3(`udx/tran`・npz は clip 2.882 km²) | 三角形・z つき。機能コード=1000 車道部・1020 車道交差部・2000 歩道部・3000 島(npz に在るのはこの 4 つ) | 地上の面の本体。z で坂も取れる(poly_z は -3.2〜29.7 m) |
| PLATEAU コード表(N23) | TrafficArea: 1000〜1130(車道系)・2000 歩道部・2010 自転車歩行者道・2020 歩道・2030 自転車道・6000/7000 駐車場・8000 番台 軌道。Auxiliary: 3000 島・3010 交通島・5000 番台 植栽 など | **横断歩道のコードは無い** |
| PLATEAU 地下街 `udx/ubld`(1 ファイル・33 MB) | `bldg:FloorSurface` 145・`bldg:Door` 188・`InteriorWallSurface` 1,934・名前「渋谷駅周辺エリア」「Storey_B1～B3」(要素を数えただけ) | 地下の階の面(床)と出入口。**本書は形を読んでいない** |
| OSM 横断歩道点(`crossings_shibuya.json`) | 192 点(信号あり 80・スクランブル 7・半径 45 m の宣言)・周期 140 s | 横断歩道の帯を置く位置 |
| 建物(`w4_buildings` 7,210)・街区(`w2_blocks` 1,227・`w2_block_rings.npz`) | 足跡・街区の環 | 穴(建物)・私有地の範囲 |
| 入口 `w5_entrances` 7,261・POI `w6_poi` 2,337・駅出口 `w11_station_exits` 45・構内の接続 `w11_station_graph_*` | 点 | 目的地・縦の接続口(off-mesh 型の辺) |

### 5-2 足りない面をどう埋めるか(先行)

- **横断歩道・交差点の歩行域**: SUMO は横断歩道(crossing)と、歩道と横断歩道をつなぐ面(walkingarea)を別の種類として持ち、`netconvert --crossings.guess` で「adds crossings wherever sidewalks with similar angle are separated by lanes which forbid pedestrians」と自動で作る。walkingarea が在る網では「pedestrians may only cross a street whenever there is a pedestrian crossing」(N21)。OSM は横断歩道を `highway=footway`+`footway=crossing` の**線**で描き、道路の**面**は `area:highway`(「describes the shape … of a highway」・`area:highway=footway/pedestrian/steps`・`traffic_island`)で描く(N22)。→ PLATEAU の交差部(1020)の中に、OSM の横断歩道点(192)から道の向きに直交する帯(幅は宣言)を切り出して歩ける面に足す、が先行に沿う形(帯の幅と長さの決め方は未リサーチ=expedient)。
- **歩道の無い細い道**: 手元の `walkable_area.py` が既に「歩道率 < 0.15 のセルは道路構造令 5 条 5 項(歩車共存=車道全幅が歩行空間)に従って OSM 側へ倒す」を持つ(expedient・第219)。ナビメッシュでも同じ規則で**歩道の無い道の車道部(1000)を歩ける面に入れる**のが、実測(歩道だけでは 343 塊)と整合する。
- **広場・私有地の通り抜け・デッキ・地下街**: 広場は OSM の `area:highway=pedestrian`/`highway=pedestrian`+`area=yes` が候補(手元の OSM 抽出にこの面が入っているかは未確認)。デッキは PLATEAU 橋梁 LOD2.1(指示書 §1-7)=本書では未読。地下街は ubld の FloorSurface を階ごとの面にして、Door と駅構内の接続 22 本(指示書 §1-7 E)を off-mesh 型の辺でつなぐ。私有地の通り抜け(公開空地など)の公的な面のデータは本書では見つけていない(空欄)。

---

## §6 まとめの表と推奨(**親への案・未リサーチ(expedient)を含む**)

### 6-1 第一候補と退路

| 順 | 案 | 理由(事実) | 残る不確かさ |
|---|---|---|---|
| **第一** | **自前 numba**: PLATEAU の三角形(歩道部+交差部+島+歩道の無い道の車道部)を整数の格子で溶接 → 横断歩道の帯・地下街の床・デッキを足す → 双対グラフ(CSR)→ A*(同点は三角形番号)+ funnel → 必要なら TA* 型の候補の選び直し。固定の目的地は距離場を前計算。階の間は Detour の off-mesh 接続と同じ「2 点をつなぐ辺」に所要時間・容量・向きを持たせる | 依存を足さない(実装計画書=Python 3.12+NumPy/Numba)・Windows/Linux で同じコード・決定論を自分で保証でき、検算も済み・1 回 0.81 ms(p50)・材料が既に三角形 | T 字の継ぎ目の直し方(辺の分割)・横断歩道の帯の規則・重心 A* の +2% を直すか |
| 退路 1 | shapely ≥2.1(`constrained_delaunay_triangles`・多角形の和/差)を**前処理だけ**に使う(帯の切り出し・穴の差し引き・継ぎ目の修復)。実行時の探索は自前のまま | BSD-3+GEOS LGPL-2.1(動的)・win/linux の wheel | **pip install の許可が要る**。GEOS の決定論の記述は未確認 |
| 退路 2 | Recast/Detour を自前の pybind11 でビルドして、ボクセルから多層のナビメッシュを焼く | zlib・重なった床と off-mesh 接続が組み込み | C++ のビルド環境と pybind11 の取得=**許可が要る**。ボクセルの `cs` で細い歩道が削られる。決定論の記述なし |
| 参照 | JuPedSim(照合用に同じ形で数体を走らせて比べる) | Jülich の系譜・CDT+TA*+funnel・Python で使える | LGPL+中の CGAL は GPL=条件を確認するまで製品に入れない。毎刻み全員引き直す作りは本番の規模に合わない。依存に pyside6・vtk |
| 避ける | triangle/meshpy(商用配布は作者の許可)・CGAL 直(GPL) | N11・N7 | 研究の内部利用は可(条文どおり)だが、収益化(ユーザーの長期構想)と相性が悪い |

### 6-2 インストールの許可が要るもの(いまの .venv に無い)

| パッケージ | 版(PyPI の最新) | ライセンス | 配布元 | 用途 |
|---|---|---|---|---|
| shapely | 2.1.2(2025-09-24) | BSD-3(GEOS = LGPL-2.1 を同梱) | https://pypi.org/project/shapely/ | 前処理(退路 1) |
| jupedsim | 1.4.2(2026-05-21) | LGPL-3+(中に CGAL の GPL 部分) | https://pypi.org/project/jupedsim/ | 照合の参照。依存 pyside6・vtk・shapely・deprecated も入る |
| mapbox-earcut | 2.1.0(2026-09-08) | ISC | https://pypi.org/project/mapbox-earcut/ | 小さな多角形(帯・床)の耳切り |
| scipy | 1.18.1(2026-08-21) | BSD-3 | https://pypi.org/project/scipy/ | csgraph の比較用(必須ではない) |
| cgal | 6.0.1(2024-10-25) | GPLv3+ | https://pypi.org/project/cgal/ | 使わない案(記録のみ) |
| triangle | 20250106 | LGPL-3(中身は Shewchuk の条件) | https://pypi.org/project/triangle/ | 使わない案(記録のみ) |
| Recast/Detour(自前ビルド) | v1.6.0 | zlib | https://github.com/recastnavigation/recastnavigation | 退路 2(C++ コンパイラと pybind11 が要る) |

### 6-3 決定論を保つための注意(自前実装の場合・expedient)

1. **溶接は整数で**: 量子化した整数(0.05 m 刻み)を格子に丸めて `np.unique`(並べ替え済み)で番号を振る。浮動小数の距離比較で溶接しない。
2. **並べ替えの鍵を全部固定**: 辺は (小さい頂点, 大きい頂点, 三角形番号) で `lexsort`、隣接の CSR は (元, 先) で整列。Python の set や、ポインタのハッシュの順(JuPedSim は `std::hash<decltype(&*fh)>` で面のポインタを鍵にしている=N2)に依らない。
3. **優先度つきキューの同点**: (f, 三角形番号) の辞書順で比べる。
4. **浮動小数**: float64・numba の `fastmath` は使わない。同じバイナリ・同じ環境で同一(D-102 の方針)。機種の間の一致は求めない(`math.hypot` などの libm の差)。
5. **並列**: 探索は体ごとに独立なので、`prange` で体の番号の配列に書き分ける(縮約をしない)。起床の順に依らず同じ結果。
6. **版の記録**: メッシュ(頂点・面・接続)のハッシュを manifest に入れる。溶接の許容差・横断歩道の帯の規則は checkpoint の版に入れる。

---

## §7 未確認の一覧(空欄)

- JuPedSim が CGAL の GPL パッケージ(Triangulation_2・Surface_mesh_shortest_path)を LGPL の配布物に含めていることの条件(商用ライセンスの有無・公開の記述)=見つからない。JuPedSim の issue を「license」で検索した 12 件に CGAL の話は無かった。
- cgal.org/license.html は 403 で読めない(GitHub の LICENSE とパッケージごとの license.txt で代用)。
- Recast/Detour・CGAL・GEOS・Polyanya の決定論(同じ入力で同じ出力)の公式の記述。Polyanya の実装のライセンス。
- trimesh・pyvista・scipy の制約つき 2D 三角分割の有無(文書を開いていない)。`pathfinding`(brean)の README 本文。
- PLATEAU 道路 LOD3 の T 字の継ぎ目の本数(塊が溶接の許容差で減ることからの推測だけ)。
- 地下街 ubld の FloorSurface の形・階ごとの面積・Door の位置(要素を数えただけ)。デッキ(PLATEAU 橋梁)の形。
- 手元の OSM 抽出に広場の面(`area:highway`・`highway=pedestrian`+`area=yes`)が入っているか。
- 私有地の通り抜け(公開空地など)の面のデータの公的な出典。
- JuPedSim の実測(.venv に無いので測っていない)。Recast の渋谷規模での焼き時間。
- 舞台 約 1.4 km² と計測範囲(PLATEAU の clip 2.882 km²)の違いによる三角形数の換算(本書は clip のまま報告)。
- 重心 A* の実データでの最適からのずれ(合成の場面での +1.7〜2.3% だけ)。

## §8 INDEX に足す行の案

| 09-30 | [r59-navmesh-implementations](v2-r59-navmesh-implementations.md) | 250 | **B**(サブ実読 ◎22・○2・△1+手元計測・親の一次確認前) | ゲーム・VR 技術の輸入 / 歩行者動力学 #18 / 計算幾何 | R-59 ナビメッシュの実装候補と経路探索の費用(指示書 09-30 §1-4・§1-7): PLATEAU 道路 LOD3 は既に三角形(歩道部 18,794・道路面 48,566)=三角分割の道具は要らないが、歩道部だけでは 343 塊(最大 1.8%)・車道まで含めて 99.8% 連結・横断歩道のコードは無い。自前 numba の A*+funnel(検算済み)で 1 回 p50 0.81/p95 2.87 ms(45,978 枚)・距離場 1 本 5.4 ms/368 KB・1 日 102〜400 万回で 0.2〜3.2 CPU h。全組の表は 46k 枚なら 8.5 GB(2 bit で 0.53 GB)=作れないのではなく費用が人ごとに違うので使えない。ライセンス: Recast zlib(Linux の Python 版なし)・CGAL の三角分割/最短路は GPL・JuPedSim(LGPL)は CGAL の GPL 部分を同梱・Triangle は商用配布に作者の許可。JuPedSim 1.4.2 は毎刻み全員の経路を引き直す。推奨(expedient)=自前 numba+退路 shapely 2.1/Recast 自前ビルド |
