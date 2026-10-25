# R-74 答申: ビューアの作り直しの調査(v1 の作りと弱点・v2 の出力・計器盤・層・架空名の段・観測の不変性・技術の比較)

<!-- hdr:v1 -->
- **分野**: ゲームエンジン工学・CG #30 / 情報可視化 / データ工学 | **重要度**: P1(指示書 [v2-wallbounce-decisions-2026-10-03](../design/v2-wallbounce-decisions-2026-10-03.md) §10-3・§6 ⑭・§6 6-6・§9-1。保留の議題 H2 の材料)
- **一次確認**: **B**(サブ実読。Web の原典 29・コード実読は §0-2・空欄は §9)・既存答申の 2 段照合を一部実施(§7-1 の deck.gl の性能値)・親検収 済(第317・2026-10-03: 地図の不具合の候補 4 つの行(`v1:viz/make_viewer.py:2782-2806,2936-2938`・`make_viewer3d.py:2216-2226`)を親が実読=64 枚の打ち切り・4 秒の再要求・3D は再試行なし を確認。親の追記: 配信元が tile.openstreetmap.org 直接なので配信元の利用方針(大量取得の制限)も外側の原因の候補。等級 A−)
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 作成 2026-10-03・リサーチ役サブ(Opus 5.5)。子サブ未起動・Web は読むだけ(ファイルの取得なし。npm の版は registry の dist-tags を読んだだけ)・コミットなし・台帳/設計書/src 未編集。v1 リポは読むだけ。
> 既存答申との関係: [v2-game-frontend-research](v2-game-frontend-research.md)(等級 D・R15 の根拠)の deck.gl の性能値は本書 §7-1 で原典に届いた。同答申の「Cesium ion Japan 3D Buildings」「UE5 City Sample」などの他の値は本書では再照合していない(循環参照に注意)。出来事の記録の欄は [R-72](v2-r72-event-log-formats.md) §7 を正とし、本書はそれをビューアの側から読む形だけを書く。

## 結論(5 行)

1. **地図が消える原因は、v1 のコードで 4 つまで絞れた**。いちばん疑わしいのは 2D の `drawBasemap` で、画面にタイルが 64 枚を超えると地図を丸ごと描きません(`v1:viz/make_viewer.py:2795`)。ズームの段を丸めるので、拡大縮小のたびに枚数が増減し、表示倍率 125% 以上の画面では段ごとに地図が出たり消えたりします [再計算]。ほかに、シミュ内の夜(19〜4 時)に地図の見え方が約 16% まで下がること、4 秒より遅いタイルの読み込み結果が捨てられること、3D では失敗したタイルを読み直さないことがあります。
2. **人が浮く原因は v1 自身が記録していた**。階が建物の階数を超えても切り詰めず、2 階建ての建物に floor=42 が来て +138 m の高さに描かれていました(描画の 5.4% が屋根より上)。表示側は直りましたが、シミュ側は直していません(`v1:docs/plans/highfidelity-3d-physics-plan.md:28`)。屋内の人を「入った時点の座標」に階の高さを足して描く作りも残っています。この座標が建物の外なら、歩道の上の空中に描かれます(推測)。
3. **v1 が見にくかったのは、作りの方針から来ている**。ダッシュボードはタブが 10+最大 9 枚あり、ビューアは 6 種類が別々の経路で作られていました。改善は「既定 OFF=バイト一致」の旗の裏に置かれ、既定の出力は古い見た目のままでした。v1 の Chronicle 計画も、既存の 2D ビューアを「125.7MB・L1全件展開・無間引き」の失敗と書いています。
4. **今の v2 の出力では、計器盤の一部しか作れない**。読めるのは在圏 journal(セル×種別の人数)・経済センサス・checkpoint のハッシュ・テープの応答です。テープには B5・B6 の本文がありません。個体の位置の時系列、関係、出来事はファイルに出ていないので読めません。強い行のうち今の出力で判定に届くのは D1′ だけで、A1・C1・D4′ は ① の記録と C5 の位置の記録が前提です。
5. **技術は deck.gl+MapLibre(2D)から始める案が、規模・ライセンス・PLATEAU との相性で筋がよい**(親の案)。deck.gl の公式文書は ScatterplotLayer で約 100 万点まで 60 FPS(2015 年の MacBook Pro)としています。PLATEAU の 3D Tiles は CesiumJS か 3DTilesRendererJS で読めます。背景地図は OSM の配信タイルでなく、自前の PMTiles か地理院タイルにすれば、v1 の読み込みの不具合と配信元の規約の問題をまとめて避けられます。架空名の段と観測の不変性は、試験の形まで §5・§6 に書きました。

## §0 出典の表

等級: **◎** 原典本文で数値・逐語まで確認 / **○** 一部推測を含む / **△** 抄録・検索要約・二次 / **×** 未読(空欄)

### 0-1 Web の原典(2026-10-03 に読んだ)

| # | 出典 | URL | 等級 | 読んだ範囲 |
|---|---|---|---|---|
| 1 | deck.gl「Performance Optimization」 | https://deck.gl/docs/developer-guide/performance | ◎ | 1M 点で 60 FPS・10M 点で 10-20 FPS・picking 16M/層・属性の再生成が律速・バイナリ属性 |
| 2 | deck.gl「TripsLayer」 | https://deck.gl/docs/api-reference/geo-layers/trips-layer | ◎ | currentTime・trailLength・getTimestamps・32 bit 浮動小数の注意 |
| 3 | deck.gl「Using with MapLibre」 | https://deck.gl/docs/developer-guide/base-maps/using-with-maplibre | ◎ | MapLibreOverlay・interleaved(WebGL2 が要る) |
| 4 | deck.gl GitHub | https://github.com/visgl/deck.gl | ◎ | MIT・WebGL2/WebGPU |
| 5 | MapLibre GL JS GitHub | https://github.com/maplibre/maplibre-gl-js | ◎ | BSD-3-Clause・GPU のベクトルタイル描画 |
| 6 | kepler.gl GitHub | https://github.com/keplergl/kepler.gl | ◎ | MIT・「Built on top of MapLibre GL and deck.gl」・数百万点 |
| 7 | CesiumJS 参照「Cesium3DTileset」(1.146) | https://cesium.com/learn/cesiumjs/ref-doc/Cesium3DTileset.html | ◎ | 3D Tiles 0.0/1.0/1.1 を読む・ストリーミング |
| 8 | CesiumJS GitHub | https://github.com/CesiumGS/cesium | ◎ | Apache 2.0 |
| 9 | 3DTilesRendererJS GitHub | https://github.com/NASA-AMMOS/3DTilesRendererJS | ◎ | three.js と Babylon.js で 3D Tiles・PLATEAU の外部提供元・Apache-2.0・キャッシュ上限は固定 |
| 10 | three.js GitHub | https://github.com/mrdoob/three.js | ◎ | MIT |
| 11 | Babylon.js GitHub | https://github.com/BabylonJS/Babylon.js | ◎ | Apache-2.0 |
| 12 | Rerun GitHub | https://github.com/rerun-io/rerun | ◎ | MIT/Apache-2.0 の二重・WASM の Web ビューア・.rrd・Python SDK・「Expect breaking changes!」 |
| 13 | Rerun「What is Rerun」 | https://rerun.io/docs/getting-started/what-is-rerun | ○ | 概要のみ。時刻のスクラブの説明はこのページに無い |
| 14 | DuckDB-Wasm 概要 | https://duckdb.org/docs/current/clients/wasm/overview.html | ◎ | Parquet の必要な部分だけ読む・HTTP の範囲読み(経路で全取得になる注意)・4 GB の上限 |
| 15 | parquet-wasm GitHub | https://github.com/kylebarron/parquet-wasm | ◎ | Parquet⇔Arrow・MIT/Apache-2.0・1.2 MB(全機能)/456 KB(読みのみ)brotli |
| 16 | Observable Plot GitHub | https://github.com/observablehq/plot | ◎ | ISC・表形式データの探索 |
| 17 | Vega-Lite GitHub | https://github.com/vega/vega-lite | ◎ | BSD-3-Clause |
| 18 | npm registry の dist-tags(各パッケージ) | https://registry.npmjs.org/-/package/deck.gl/dist-tags ほか | ◎ | 2026-10-03 時点の最新版(§7-1 の表) |
| 19 | Epic「Overview of Pixel Streaming」 | https://dev.epicgames.com/documentation/en-us/unreal-engine/overview-of-pixel-streaming-in-unreal-engine | ◎ | UE のアプリを遠隔で回し、描いた結果を映像の流れにする |
| 20 | UE の HTML5 書き出しの撤去(4.24 で外部の拡張へ) | https://github.com/UnrealEngineHTML5/Documentation | △ | 検索の要約のみ(Epic の一次文書は未読) |
| 21 | Unity 6.2 マニュアル「WebGPU (Experimental)」「Web」 | https://docs.unity3d.com/6000.2/Documentation/Manual/WebGPU.html | ◎ | WebGPU は実験的・既定は WebGL2 |
| 22 | OSMF「Tile Usage Policy」 | https://operations.osmfoundation.org/policies/tiles/ | ◎ | Referer の要求・オフライン利用の禁止・予告なしの遮断 |
| 23 | OSM「Copyright and License」 | https://www.openstreetmap.org/copyright | ◎ | ODbL・出典の表示 |
| 24 | 国土地理院「地理院タイル一覧」 | https://maps.gsi.go.jp/development/ichiran.html | ◎ | 出典の明示で申請不要(基本測量成果は申請が要る場合あり)・URL の形 |
| 25 | Protomaps「PMTiles」 | https://docs.protomaps.com/pmtiles/ | ◎ | 1 ファイルのタイル集・HTTP の範囲読み・MapLibre 推奨 |
| 26 | PLATEAU 配信サービス「概要」 | https://docs.plateauview.mlit.go.jp/intro/ | ◎ | 3D Tiles/MVT・Terrain・Ortho を無償・試験的運用 |
| 27 | PLATEAU 配信チュートリアル(GitHub) | https://github.com/Project-PLATEAU/plateau-streaming-tutorial | △ | 検索の要約のみ(「3D Tiles 1.0及びMVT」・2024-06 にデータカタログ API) |
| 28 | Microsoft Presidio GitHub | https://github.com/microsoft/presidio | ◎ | MIT・「there is no guarantee that Presidio will find all sensitive information」 |
| 29 | Presidio「Anonymizer」 | https://presidio.dataprivacystack.org/anonymizer/ | ◎ | replace/redact/hash/mask/encrypt/custom/keep・decrypt で戻せるのは encrypt だけ |
| 30 | ENISA 2019「Pseudonymisation techniques and best practices」 | https://www.enisa.europa.eu/publications/pseudonymisation-techniques-and-best-practices | △ | 紹介ページのみ(本文未読) |
| 31 | Tao ほか 2020「Kyrix-S」arXiv 2007.15904 | https://arxiv.org/abs/2007.15904 | ◎ | 抄録(数十億点を 500 ms 未満) |
| 32 | Tao ほか 2019「Kyrix」CGF 38(3) | https://diglib.eg.org/handle/10.1111/cgf13708 | △ | 検索の要約のみ(1 億点で平均 100 ms 以下) |
| 33 | Orwig 2017「Replay Technology in 'Overwatch'」GDC | https://www.gdcvault.com/play/1024053/Replay-Technology-in-Overwatch-Kill | ◎ | 講演の紹介文(再生は不具合の再現にも使う・ネットワークの作りと並行して作る) |
| 34 | MDN「Referer」 | https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Referer | × | 現行版に「file: から送らない」の記載が無く、確認できず(空欄) |
| 35 | Khronos「HandlingContextLost」 | https://wikis.khronos.org/webgl/HandlingContextLost | × | 403(空欄) |

本数: ◎ 28・○ 1・△ 4・× 2。

### 0-2 リポの中で読んだもの(コード・記録)

| 対象 | 読んだ範囲 |
|---|---|
| `v1:viz/make_viewer.py` | 冒頭の旗(1〜30 行)・`build_data`(716〜840)・昼夜テーマ(1809〜1868)・地図タイル(2775〜2817)・`draw`(2931〜2960)・タブ(3982〜3991・4815〜4847) |
| `v1:viz/make_viewer3d.py` | 冒頭の旗(1〜45)・地形の注入(547〜590)・地面と OSM(2074〜2226)・建物(2236〜2252)・高さの関数(2415〜2446)・人の形(2374〜2392)・配置(2504〜2535) |
| `v1:viz/make_hub.py`・`v1:viz/notable_events.py`・`v1:viz/unreal/*.md` | 冒頭の説明 |
| `v1:scripts/build_chronicle.py`(1〜90・4406〜4430)・`v1:scripts/export_3d.py`(1200〜1222・1427〜1437) | 作り・地図の扱い・屋内の座標 |
| `v1:docs/plans/highfidelity-3d-physics-plan.md`(1〜60)・`v1:docs/plans/viewer-chronicle-plan.md`(1〜70) | v1 自身の不具合の記録・Chronicle の原則 |
| `v1:tests/test_gt_logger.py:438-441` | 観測の不変性の試験 |
| v2 `src/shibuya/engine/tape.py`・`llm_bridge.py:146-149`・`engine/run.py`(Checkpoint・在圏 journal・診断の列)・`cli.py`(出力の旗)・`world/processes/actual_log.py`・`economy/census.py` | 出力の口 |
| v2 `tools/c8/dashboard.py`・`tools/c8/ensemble.py:263`・`tools/c7/c7_accept.py` | 計器盤の既存の道具 |
| v2 `tests/engine/test_census_out.py:122-128`・`tests/vocab/test_undefined_out.py:43-56` | 観測の不変性の既存の試験 |
| v2 `docs/design/v2-dashboard-verification-orchestration.md`(R14)・`v2-pattern-ledger.md`・`v2-redesign.md:505`(R15)・`v2-world-data-build-spec.md:110-111` | 決定の文言 |

## §1 v1 のビューアの作りと弱点

### 1-1 構成の一覧

行数は [v1-check](../bench/analysis/wallbounce-1003/v1-check.md) §3 を正とする。

| 部品(v1 リポ相対) | 何を作るか | データの形 | 描画の技術 | 前もって集計して必要な分だけ読むか |
|---|---|---|---|---|
| `viz/make_viewer.py` | `viewer.html`(地図)と `dashboard.html`(10 タブ+最大 9 タブ) | L1 の全件を読み、step×体の位置の密な配列(`positions[step][agent]=[x,y,w]`・`w` は 0=路上/-1=範囲外/-2=睡眠/1000+建物×100+階)を JSON で HTML に埋め込む(`:716`〜`:832`・`:1001`) | Canvas 2D の手描き・OSM のラスタタイル | **しない**(全部を 1 枚に埋め込む)。`--daily-rollup` だけは位置を読まない軽量版(`:1446`) |
| `viz/make_viewer3d.py` | `viewer3d.html`(自己完結) | `scene3d/{scene.json,tracks.json}`。`--tracks-binary` で int16 量子化のチャンクを `<script src>` で遅延読み込み(冒頭 `:26`〜`:31`。1 万体×1 日で 90.4MB→約 26MB と記録) | three.js r128 を同梱(`viz/vendor/three.min.js`)・InstancedMesh・OSM のラスタを 1 枚のテクスチャに合成して地形に貼る | 一部(軌跡のチャンク) |
| `viz/make_hub.py` | `hub.html` | 各ビューアを iframe で並べるだけ | 自前 CSS | 該当なし |
| `viz/notable_events.py`・`viz/feed_rank.py` | 顕著な出来事の一覧・フィード | `l1_events.parquet` から決定論で抜く。種類の登録表を 1 つにまとめた(第137) | なし | する |
| `viz/unreal/*`・`scripts/export_ue.py` | UE5+PLATEAU SDK で再生する手順書と設計 | `sim_ue.json` | UE5(**実機で未検証**と本文に明記) | する |
| `scripts/build_chronicle.py` → `viz/chronicle/chronicle.html` | 俯瞰・関係の伝記・語の一生・物語のピン・A/B | ビルド時に事前集計(200 m 格子×1 時間の hexbin・指標の時系列・抜き出した物語)を JSON にし、HTML に全部埋め込む(10.6 MB) | Canvas 2D・OSM のラスタタイル(2D と同じ流儀) | **する**(Kyrix 式と本文に明記) |
| `scripts/live_viewer.py` | 走行中のティッカー | 本書では読んでいない | 本書では読んでいない | 本書では読んでいない |

### 1-2 不満 (i) 見た目が美しくない

コードから読める原因(評価の言葉はユーザーのもの。ここでは作りの事実だけを並べる)。

1. **2D は Canvas 2D の手描き**。道路は線の太さを種類ごとに変えた折れ線(`v1:viz/make_viewer.py:2928` の `ROAD` 表と `:2931` の `draw`)。背景は OSM の標準タイルを不透明度 0.9 で重ねるだけで、道路の線と OSM の道路が二重に描かれる。
2. **止まっている人を正弦波で揺らしている**(`microXY`・`:2732`〜`:2737`「静止エージェントの微動」)。シミュに無い動きを描いており、R15 の GlassBox 規律(見えるもの=シムの 1:1)と逆。
3. **建物の中は推定の間取りを手続き生成**(`:1870`・`:1902`)。v2 の方針「建物の階や間取りを推定で決めない」(指示書 §8)とも合わない。
4. **3D は three.js r128 を同梱して固定**。影なし(`v1:viz/make_viewer3d.py:2110` `shadowMap.enabled = false`)・建物は無彩色の Lambert(`:2117`)・人はカプセルを既定 2 倍で描く(`:2381`〜`:2383`)・地面は OSM のラスタを 1 枚に合成して貼る(`:2196`〜`:2205`)。斜めから見るとラスタはぼやける(推測)。
5. **「1 ファイルで完結」と「80MB のゲート」が質を下げていた**。テクスチャ付きの PLATEAU は埋め込み版に入れない(`:36`)、道路 LOD3 は既定 OFF(冒頭 `:16`〜`:20`)。
6. **改善は既定 OFF**。`--lateral-offset`・`--event-feed`・`--indoor-v2` はどれも「未指定なら生成 HTML は従来とバイト同一」(`v1:viz/make_viewer.py:4`〜`:14`)。良くした見た目が既定の出力に出ない作りだった。

### 1-3 不満 (ii) 地面の地図が定期的に表示されなくなる

**原因の候補(コードで特定。どれが当たりかはユーザーの環境の確認が要る)**

| # | 場所 | 中身 | 「定期的」に見える理由 |
|---|---|---|---|
| A | `v1:viz/make_viewer.py:2785`〜`:2795` | ズームの段 `z` を `Math.round(log2(...))` で丸め、13〜19 に切り詰める。画面に入るタイルが **64 枚を超えると `return` して地図を 1 枚も描かない** | 段を丸めるので、同じ段の中でも拡大率によってタイルの見かけの大きさが 181〜362 px の間で変わり、枚数が増減する。下の再計算のとおり、表示倍率 125% 以上の画面では拡大縮小の 1 段ごとに出たり消えたりする |
| B | `:2784` と `:2938` | 地図の不透明度に `(1 − 0.55×夜の度合い)` を掛け、さらに夜の色 `rgba(4,7,13,0.6)` を全面に重ねる(`_NIGHT.night`・`:1835`) | シミュ内の 19〜4 時は、タイルの寄与が 0.9×0.45×0.4 ≒ 0.16 まで下がる [再計算]。暗い背景の上で地図がほぼ見えなくなり、毎晩くり返す |
| C | `:2799`〜`:2803` | 読み込み中のタイルも 4 秒たつと作り直し、新しい要求を出す。古い要求の `onload` は捨てた方の入れ物に書くので、**4 秒より遅いタイルは永久に表示されない**。表示中は毎フレームこれをくり返す | 配信元が遅い・絞られているときに、穴が出たり消えたりする。要求がくり返されるので、OSMF の規約(#22「We may block access, without notice, if your usage degrades the service.」)に当たるおそれがある(推測) |
| D | `v1:viz/make_viewer3d.py:2190`・`:2218`〜`:2224` | 3D はタイルが 96 枚を超えると地図を作らない。読み込みは 1 回だけで、失敗(`onerror = ()=>{}`)は読み直さない | 失敗したタイルは、ページを開き直すまで穴のまま |

同じ `drawBasemap` の写しが Chronicle にもある(`v1:scripts/build_chronicle.py:4422` に 64 枚の打ち切り)。

**WebGL の扱い**: 3D は同梱の three.js r128 が `webglcontextlost` で既定動作を止め、`webglcontextrestored` で作り直す処理を持つ(`viz/vendor/three.min.js` の中に `preventDefault(),console.log("THREE.WebGLRenderer: Context Lost.")` を確認)。アプリ側には独自の処理が無い(`grep webglcontext` は 0 件)。地図が消える主因としては A〜D より弱い(推測)。Khronos の解説は 403 で読めなかった(空欄)。

**A の再計算**(画面の canvas の大きさを仮定した計算。ズームの 1 段=1.15 倍・地図の右と下の余りの端を含む最悪の枚数。スクリプトは scratch に置いた)

| 画面(canvas の画素) | 24 段のうち、常に 64 枚以下 | 常に 64 枚超(地図が消える) | 位置で変わる |
|---|---|---|---|
| 1280×720 | 24 | 0 | 0 |
| 1920×1080(表示倍率 100%) | 20 | 0 | 4 |
| 2400×1350(1080p で 125%) | 12 | 8 | 4 |
| 2880×1620(1080p で 150%) | 7 | 12 | 5 |
| 3840×2160(4K の 100%・1080p で 200%) | 1 | 22 | 1 |

canvas は地図の枠の大きさで、画面全体より小さい(横の操作盤の分)。実際の枚数はこれより少し少ない(推測)。

**再現の手順(案)**: Windows の表示倍率を 125% か 150% にし、`viewer.html` を全画面で開く。地図の層を ON にし、ホイールで 1 段ずつ拡大する。段によって地図がまるごと消え、次の段で戻る(A)。再生を 19 時以降まで進めると地図がほぼ見えなくなる(B)。開発者ツールでネットワークを「Slow 3G」に絞ると、タイルの要求が 4 秒ごとにくり返され、穴が埋まらない(C)。

**ユーザーに確かめたい点**: どのビューア(2D・3D・Chronicle)で、どの画面で、どの時刻に消えたか(空欄)。file:// で開いたページからの要求に Referer が付かず OSMF の規約(#22「From web pages, ensure a valid HTTP Referer header is sent.」)で遮断された可能性も考えたが、file:// の Referer の扱いは MDN の現行版で確認できなかった(空欄)。

### 1-4 不満 (iii) 人が空中に浮いている

v1 自身の記録(`v1:docs/plans/highfidelity-3d-physics-plan.md:28`)の逐語:

> エージェントの筒が浮く | ①**sim の floor が建物階数を超えてもクランプされない**(2階建てに floor=42 → +138m。描画フレームの 5.4% が屋根超え) ②高さ関数が建物基準面(base/gz)を無視 ③カプセルが全高 10.2m・中心配置で足元 4m がめり込む

同じ文書の 30〜32 行は、表示側だけ直してシミュ側(`scheduler.py` の階の切り詰め)は見送ったと書く。記録の行番号(`scheduler.py:2719`)は今の v1 のコードとずれている(今の 2719 行は別の関数)。

今の v1 の 3D の高さの決め方(`v1:viz/make_viewer3d.py:2430`〜`:2446`):

```js
function upOf(w){
  if(w >= 1000){ ... return (b.gz||0) + Math.max(floor-1, 0) * floorHOf(b); }
  return 0; // 路上 = 地表(呼び出し側が groundAt を使う)
}
function footY(x, y, w){ return (w >= 1000) ? upOf(w) : groundAt(x, y); }
```

残っている問題(コードから。実画面では未確認):

1. **屋内の人の xy は「建物に入った時点の座標」**(`v1:scripts/export_3d.py:1208`〜`:1211` が `enter_building` の `e["x"], e["y"]` を使う)。高さは階の床なのに、xy が建物の足跡の外(入口のノードなど)なら、歩道の上の空中に描かれる(推測。この座標が何かは未確認=空欄)。
2. **路上の人の高さは地形 `groundAt` だけ**。デッキ(歩道橋)や地下通路を歩く人も地表に置かれる。線路は `r.z` を足して描く(`:2336`)ので、人と通路の高さが合わない。
3. **建物の基準 `gz` は足跡の下の地形の最小値**(`v1:scripts/export_3d.py:1436`)。斜面の建物では、人の床と見えている地面がずれる(推測)。

v2 で防ぐ形(親の案・未リサーチ): 位置は (x, y, 階) なので、表示の高さは「その (x, y, 階) が載っている面の高さ」だけから決める。路上=地形(PLATEAU DEM。v2 は `src/shibuya/build/geo/common.py:58` に地盤高の基準を持つ)、デッキ・地下=その通路の面の高さ、建物の中=その建物のその階の床の高さ(PLATEAU の実測高÷階数、無ければ宣言した既定値)。受入の試験は「描くすべての体について、表示の高さと面の高さの差が ε 以内」「建物の中の体の xy がその建物の足跡の中」の 2 本。階が建物の階数を超える体はシミュ側の誤りなので、表示で切り詰めずに数えて計器盤の面 3 に出す。

### 1-5 不満 (iv) データが整理されておらず見にくい

1. **画面が多く、入口がばらばら**。2D の `viewer.html`・`dashboard.html`(タブ: 出来事・SNS・メッセージ・検索ログ・分析・関係・語彙・施設・住民・シナリオ=`v1:viz/make_viewer.py:3982`〜`:3991`。さらに価値・欲望・信用・逸脱・社会構造・資産・承諾・会社・在館の最大 9 タブ=`:4815`〜`:4847`)・3D の `viewer3d.html`・`points_viewer.html`・`chronicle.html`・`hub.html`(iframe で束ねるだけ)。データを作る経路も別々。
2. **登録表が二重だった時期がある**。3D の顕著パネルとライブのティッカーで集合も性質も違っていた(`v1:viz/notable_events.py` 冒頭。第137 で 1 表に統合)。
3. **何を見せるかの順位が無い**。全部のタブが同じ重さで並び、見出しの数字(合否・一致度)が無い。v1 の Chronicle 計画は「多すぎて俯瞰しか見えない」をユーザーの要望として書く(`v1:docs/plans/viewer-chronicle-plan.md:3`)。
4. **全部を埋め込む作り**。Chronicle 計画は既存 2D を「単一HTML全埋込は捨てる: 既存2Dビューワーの失敗(125.7MB・L1全件展開・無間引き)」と書く(同 `:9`〜`:10`)。3D の runB の HTML は 53,976,177 B、軌跡は約 285 MB(v1-check §3)。

### 1-6 v1 から考え方だけ引き継げるもの(コードは移植しない)

| 考え方 | v1 の場所 | v2 での扱い(親の案) |
|---|---|---|
| ビルド時に集計し、ビューアは描くだけ(Kyrix 式) | Chronicle 計画 §0-5 | 引き継ぐ。Kyrix-S(#31)は数十億点を 500 ms 未満で閲覧と報告 |
| 量子化+チャンクの遅延読み込み | `make_viewer3d.py --tracks-binary` | 引き継ぐ。形式は Arrow/Parquet にそろえる(§7) |
| 出来事の種類を 1 つの登録表で持つ | `notable_events.py` の KIND_REGISTRY | 引き継ぐ。R-72 §7-1 の `kind` の登録表と同じ表にする |
| A/B の同じ人の対比・関係の伝記・語の一生・物語のピン | Chronicle 計画 §1 の画面 1〜4 | 物語の層(§4)の候補 |
| 「観測はランを動かさない」試験 | `v1:tests/test_gt_logger.py:438-441` | 引き継ぐ(§6) |
| 改善を既定 OFF の旗の裏に置く | `make_viewer.py` の旗 | **引き継がない**。ビューアはランの外の別の道具なので、バイト一致はビューアの出力でなくランの出力に対して求める(§6) |

## §2 今の v2 の出力で見られるもの・足りないもの

### 2-1 出力の口の一覧(コードの事実)

| 口(旗) | 書くもの | 場所 |
|---|---|---|
| `--tape <dir>` | `calls.parquet`(1 呼=1 行・版 3: call_id・agent_id・tick・wake_class・prompt_hash・block_ids・params_hash・**response**・tokens・deferred・observed_tick・recalled_rows)と `blocks.parquet`(共有ブロックの本文) | `engine/tape.py:10`〜`:40` |
| 共有ブロックの範囲 | B0〜B4 だけ。**B5・B6(本人の部分)は本文を残さない** | `engine/llm_bridge.py:146`〜`:149` |
| `--census-out <dir>` | `daily_census.parquet`・`monthly_mer.parquet`・`monthly_mer_sectors.parquet`(経済) | `cli.py:299`〜`:303`・`economy/census.py` |
| `--occupancy-every N --occupancy-out x.npz` | N tick ごとの セル×人数・種別×セル・種別×(在圏/乗車中/域外) | `engine/run.py:3592`〜`:3603`・`:4044`〜`:4053` |
| `--checkpoints-out` | checkpoint の**ハッシュだけ**(agents/world/population/schedule/activity)と manifest の同定欄 | `cli.py:470`〜`:493`・`engine/run.py:465`〜`:487` |
| `--undefined-out` | 未定義行動の台帳(語ごとの集計・標本) | `cli.py:496`〜 |
| 標準出力の要約 | 診断の列(呼数・会話数・購入数など)の合計と ActualLog の行数・遵守率 | `engine/run.py:254`〜`:278`・`:1209`〜`:1266` |
| ActualLog | **ファイルに出ない**(メモリの中だけ。保持窓を過ぎた日は集約行へ畳む) | `world/processes/actual_log.py` |

### 2-2 見たいものごとの可否

| 見たいもの | 今読めるか | 根拠 | ① の記録と C5 の位置の記録ができたら |
|---|---|---|---|
| 個体の位置の時系列 | **読めない**。在圏 journal はセルごとの人数で、個体を区別しない | 2-1 | R-72 §7-1 の `place`(量子化した位置)を持つ出来事の行から、体ごとの軌跡を組み立てられる。範囲外の体は行が無い(C5) |
| 個体のプロンプトと応答 | **一部**。応答の全文と B0〜B4 は読める。B5・B6 が無いので、本人に何を見せたかは再生でしか分からない。`call_id` は日を含まない(R-72 §7-1 の注意) | 2-1 | テープ版 4(指示書 §3-4)で B5・B6 を残せば、その時点のプロンプトの全文を出せる。出来事の `cause_ref` から呼に戻れる |
| 集計 | **一部**。経済の日次・月次、セル×種別の人数、要約の合計、checkpoint の同定欄 | 2-1 | 6 時間ごとのスナップショット(① )から、任意の欄の時点の集計を作れる |
| 関係 | **読めない**。関係辺は状態の中だけで、checkpoint はハッシュだけ | `engine/run.py:465`〜`:487` | スナップショットの関係辺と、`write_relations` の出来事(R-72 §7-4)で、関係の伝記を組み立てられる |
| 出来事 | **読めない**。行動の出来事の記録が無い。診断の列は tick ごとの件数で、要約に合計だけ出る | 2-1・指示書 §6 ① | R-72 §7-1 の行(`day・tick・seq・kind・subject・object・place・cause_kind・cause_ref・parent_seq・delta`)がそのまま「出来事」の一覧になる。発話は §7-2 の届け先の行、記憶の出どころは §7-3 |

### 2-3 R-72 §7 の欄からビューアが読む形(親の案・未リサーチ)

| ビューアの画面 | 読む欄 | 作り方 |
|---|---|---|
| 地図の点 | `kind ∈ 位置の種類`・`subject`・`day/tick`・`place` | 位置の出来事を体ごとに並べ、前の位置を次の位置の時刻まで持ち続ける(起きたときだけの記録なので、間は「動いていない」か「移動の経路」として扱う)。経路を描くなら、移動の開始の行に経路の id か節点の列が要る(**今の R-72 案には無い**) |
| 位置の量子化 | `place` | (x, y, 階) の連続値に移ったら(指示書 §8 3-1)、x・y を原点からの整数(量子化の幅は未定)、階を int8、仮想空間の印を 1 bit にする案。R-72 の「辺 id+辺上の距離」の案と、どちらにするかは空間の設計ラウンドで決める |
| 個体の詳細 | `cause_ref`(=call_id)→ テープ版 4 の行 | 出来事を押すと、その原因の呼のプロンプト全文と応答を出す。`parent_seq` をたどって、前後の出来事を並べる |
| 関係の伝記 | 関係辺の出来事+発話の届け先の行(§7-2)+スナップショットの関係辺 | 2 人の id で絞り、時刻順に並べる |
| 語の一生 | 発話の行+記憶の出どころ(§7-3) | 語(または主張)の抽出はラン後に行う(指示書 §10-2)。抽出の版を画面に出す |
| 時刻のスクラブ | スナップショット(6 時間ごと)+出来事 | スナップショットを I フレーム、出来事を差分として使う(既存答申 game-frontend の「checkpoint=Iフレーム+行動イベント=Pフレーム」と同じ形。この答申は等級 D) |

## §3 最初の画面=忠実度の計器盤

### 3-1 決まっていること

- 指示書 §6 6-6 (a): 計器盤をビューアの最初の画面にする。パターン台帳の判定関数の結果を、ランの記録から読んで表示する。
- 指示書 §6 ⑫ (a): `I_i = |シミュの平均 − 観測値| ÷ √(シミュのばらつき² + 観測の誤差² + モデルの不一致²)`。3 以下で合格。`I_M` を見出しにする。強い行は全部合格が必須、弱い行は重みづけの点数。アンサンブルが前提で、1 本のランでは計算できない。モデルの不一致は最初は 0 と宣言する。
- R14 G-1(`docs/design/v2-dashboard-verification-orchestration.md:9`〜`:14`): 面 1 較正面(報告のみ)・面 2 holdout 面(ゲートはここだけ・アンサンブル単位)・面 3 運用面(赤は症状のみ)。G-8 の後段(`:83`): 結果は不確実性の区間と分散の分解で出し、選んだ 1 本の軌跡で出さない。
- 既に道具がある: `tools/c8/dashboard.py`(3 面を Markdown+JSON にまとめる。面 2 の `I_M` は「未計算」のまま=`:308`)・`tools/c8/ensemble.py:263` の `implausibility()`・`tools/c7/c7_accept.py`(C7 の受入表)。

### 3-2 画面の形(親の案・未リサーチ)

1. **見出し**: `I_M`(とその行の id)・強い行の合否(5 本のうち何本が判定できたか、何本が合格か)・弱い行の点数・アンサンブルの本数(seed 数)・判定関数の版のハッシュ・「落ちたら不合格・通っても合格とは言わない」の一文(R14 G-1)。
2. **行の表**: 台帳の行ごとに `I_i`・判定型(band/ordinal/existence/shape)・split(holdout/較正)・状態(判定済み/前提待ち/当分は測れない)・学習データの混入の疑い(運用規則 9)。
3. **1 本だけのランのとき**: 面 2 の値を出さず「アンサンブルが要る」と出す(R14 §2 の「単一ランで合否を出したら失敗」)。面 1 と面 3 は出す。
4. **行を押すと**: シミュの分布(seed ごとの値)と観測値と誤差の帯を 1 枚に描き、その行の入力ファイルと判定関数のハッシュを出す。

### 3-3 必要な入力(ファイルと欄)

| 入力 | 欄 | 今あるか |
|---|---|---|
| アンサンブルの各ラン(EnsembleSpec・R14 G-4) | ラン manifest の同定欄・seed・`final_hash` | 一部(`--checkpoints-out` の JSON。完了済みラン表は未作成) |
| 判定関数の出力(行ごと・ランごと) | `row_id`・`y_i`(そのランの値)・判定関数の版のハッシュ | **無い**(判定関数は未実装。指示書 §6 6-2 で作れるものから作る) |
| 観測値 | `z_i`・`Var_obs`(台帳の出典から。不明なら宣言値) | 台帳の本文にある。機械で読める形は無い |
| モデルの不一致 | `Var_disc`(初回 0 と宣言) | 決まっている |
| 強い行と弱い行の別・重み | 台帳の「強」の列・弱い行の重み | 強の列はある。弱い行の重みは未定(空欄) |
| holdout の開封の記録 | `docs/bench/c7/holdout_open_record.json` | ある |

**強い行の入力**(台帳 §5 の強 5 本):

| 行 | 要る記録 | 今の出力で届くか |
|---|---|---|
| D1′ 滞在人口カーブ | 在圏 journal(`cell_counts`・`kind_cell_counts`)と KDDI の holdout(`tools/c7/presence_yardstick.py` が既に読む) | **届く** |
| A1 会話グループの大きさ | 会話のセッションと参加者の出来事 | 届かない(① の後。指示書 §6 6-2 は「会話の修正の直後」) |
| C1 カスケード | 発話の届け先・記憶の出どころ・採用の出来事 | 届かない(指示書 §6 6-2 は「① の記録の直後」) |
| D4′ 3 街路の日内プロファイル | 位置の記録(C5) | 届かない(指示書 §6 6-2 が名指し) |
| E2 企業の成長率 | 長いラン | 当分は測れない(指示書 §6 6-2) |

## §4 層の分け方(親の案・未リサーチ)

| 層 | 中身 | 読むもの | 先行・参考 |
|---|---|---|---|
| 0 計器盤 | §3 | 判定関数の出力・アンサンブル | R14 |
| 1 地図の俯瞰 | 密度(セル・hexbin)→ 拡大すると個体の点。種類で色分け。再生 | 事前集計の格子(ズームごと)+位置の出来事 | Kyrix の段ごとの事前計算(#31・#32)・deck.gl の ScatterplotLayer/TripsLayer(#1・#2) |
| 2 個体の詳細 | その時点のプロンプト全文と応答・前後の出来事・関係辺・記憶の行(出どころつき)・体の値 | テープ版 4・出来事・スナップショット | 既存答申 game-frontend の「個体インスペクト」(等級 D)・Generative Agents の再生(同答申・未確認) |
| 3 タイムライン | 再生・一時停止・速度・任意の時刻へ飛ぶ・出来事の一覧から飛ぶ | スナップショット+出来事・時刻の索引 | Overwatch の再生は不具合の再現にも使う(#33)・Rerun の時系列の同期(#12) |
| 4 物語 | 関係の伝記・語の一生・A/B(同じ人の対比)・反実仮想の対比・物語のピン | 出来事の事後の抽出(指示書 §10-2) | v1 Chronicle の画面 1〜4(考え方だけ) |

層の約束(親の案):

- 層 0 の数字は層 1〜4 のどこからも 1 回で戻れる(見出しを常に出す)。
- どの層も「ランの記録にあるものだけを描く」。補間・演出(v1 の微動のようなもの)は描かない。移動の途中の位置のように記録から計算したものは、計算したと分かる印を付ける(R15 の GlassBox 規律の v2 側の宣言)。
- A/B と反実仮想は、共通乱数の対(指示書 §6 ⑮)の 2 本を同じ時刻で並べる。改変した時点まで記録が一致することの確認結果を画面に出す。

## §5 実名を架空名に置き換える出力の段(§9-1)

### 5-1 先行例

- **Presidio**(#28・#29): 検出と置き換えを分けた作り。置き換えの操作は replace・redact・hash・mask・encrypt・custom・keep。元に戻せるのは encrypt(decrypt)だけ。README は自動検出について「there is no guarantee that Presidio will find all sensitive information」と書き、別の防御を併用するよう勧める。
- **ENISA 2019**(#30): 擬似化の技術と運用の報告。本文は未読(空欄)。
- 都市シミュレーションで店名を置き換えた先行は見つからなかった(空欄)。

### 5-2 v2 での形(親の案・未リサーチ)

対象は店名(指示書 §9-1)。会社名の扱いは `v2-world-data-build-spec.md:111` が「未整理(報告済み)」と書いているので、本書では同じ段に載せられる形にだけしておく。

1. **対応表**: 実名 → 架空名の表を世界データの構築で 1 回作り、版のハッシュを manifest に入れる。同じ実名にはいつも同じ架空名(決定論)。表は gitignore の下に置き、公表物には入れない。
2. **段の場所**: ランの外の書き出しの道具の、最後の 1 段にする。ビューアのデータ・報告・Discord・データの書き出しは、全部この段を通った出力の置き場(例: `public/`)からしか読まない。ランの出力(`runs/`)には実名が残る。
3. **自由文の置き換え**: 住民の発話・応答の本文は、対応表の実名の全部(表記ゆれ・かな・略称の辞書を足す)で文字列を探して置き換える。辞書に無い言い方は残るので、Presidio の注意と同じく「見つけ残しがある」前提で、次の検査と組にする。
4. **通さないと出せない作り**: 書き出しの道具は、対応表の版が manifest と一致しないと止まる。出力の全ファイルを実名の辞書で走査し、1 件でも見つかれば出力を消して止まる。CLAUDE.md §7 の秘密スキャンと同じ「見つかったら止める」形にする。
5. **混入の疑いとの関係**: 比較の腕(プロンプトの店名だけを架空にした腕)は §9-1 の手当ての 1 つ目で、この段とは別のもの。腕の差は計器盤の面 1 か面 2 の行として出す。

## §6 観測の不変性の試験の形(親の案・未リサーチ)

既存の型: v1 `tests/test_gt_logger.py:438-441`(サイドカーの ON/OFF で L1 がバイト一致)・v2 `tests/engine/test_census_out.py:122-128`(センサスの書き出しの有無で `final_hash` と checkpoint 列が一致)・v2 `tests/vocab/test_undefined_out.py:43-56`。

| 試験 | 中身 |
|---|---|
| T-V1 ランの中の口 | ① の記録・C5 の位置・テープ版 4・ビューア用の書き出しの各口を 1 本ずつ ON と OFF にして同じ seed で回し、`final_hash`・checkpoint の全点・総呼数・テープの `calls.parquet` の内容(書き出しの口自身の列は除く)が一致することを確かめる。mock の 5,000 体×数十 tick |
| T-V2 ランの外の道具 | ビューアのデータを作る道具は別のプロセスで、ランが終わった後に読む。道具を回す前と後で、ランの出力の全ファイルのハッシュが一致することを確かめる |
| T-V3 静的な検査 | ビューアと書き出しの道具のパッケージが、エンジンの書き込み口(`engine/resolve.py` など)を import しないことを検査する |
| T-V4 走行中に見る場合 | 走行中のランを読むなら、読むのは書き終わったファイル(閉じた part)だけにする(v1 の `l1_stream.py` の「完結 part のみ」と同じ考え)。走行中の読みの有無で `final_hash` が一致することを確かめる |
| T-V5 架空名の段 | 実名の辞書で公表用の出力を走査して 0 件。対応表を消すと道具が止まる。同じ入力で 2 回回すと同じ出力 |

## §7 Web の地図・可視化の技術の比較

### 7-1 比較の表(版は npm registry の dist-tags・2026-10-03)

| 技術 | 版 | ライセンス | 10〜39 万点 | 時系列の再生 | 3D の建物と地形 | タイル地図 | PLATEAU の 3D Tiles | 学習の費用(推測) |
|---|---|---|---|---|---|---|---|---|
| deck.gl | 9.4.0 | MIT(#4) | 公式「up to about 1M (one million) data items」で 60 FPS(2015 年の MacBook Pro)・10M で 10-20 FPS・picking は 1 層 16M まで(#1)。律速は属性の再生成で、型付き配列を直接渡せば CPU を飛ばせる(#1) | TripsLayer の `currentTime`(#2)。時刻は 32 bit 浮動小数なので、生の Unix 時刻は使えない(#2) | 本書では未確認(空欄) | MapLibre と同じカメラで重ねられる(#3) | 本書では未確認(空欄) | 中 |
| MapLibre GL JS | 6.11.2 | BSD-3-Clause(#5) | 点の大量描画は deck.gl と組む | なし | 本書では未確認 | ベクトルタイル・PMTiles を推奨の読み手として挙げる(#25) | MVT なら読める(PLATEAU は MVT も配信・#26) | 中 |
| kepler.gl | 3.3.0-alpha.15(latest の印) | MIT(#6) | 「can render millions of points」(#6) | 時刻の範囲の絞り込み(#6 の例)。再生は本書で未確認 | 本書では未確認 | MapLibre+deck.gl の上に作る(#6) | 本書では未確認 | 低(完成品の道具)。作り込みはしにくい(推測) |
| CesiumJS | 1.146.0 | Apache 2.0(#8) | 本書では未確認(空欄) | 時計の部品は本書で未確認 | 地球儀・地形・3D Tiles | 画像タイル | 3D Tiles 0.0/1.0/1.1 を読む(#7)。PLATEAU VIEW 自体が Cesium を使う(#26) | 中〜高 |
| three.js | 0.186.1 | MIT(#10) | InstancedMesh(v1 で使用)。上限の公称は確認できず(公式ページが 404・空欄) | 自前 | 自前 | 自前 | 3DTilesRendererJS で読める・PLATEAU を外部提供元に挙げる(#9) | 中(全部自前) |
| Babylon.js | 9.29.0 | Apache-2.0(#11) | 本書では未確認 | 自前 | エンジンとして持つ | 自前 | 3DTilesRendererJS が Babylon.js にも対応(#9) | 中 |
| Unreal Engine | 対象外 | Epic の規約(本書で未読) | 本書では未確認 | Sequencer 等(v1 `viz/unreal/SimReplayActor_DESIGN.md`) | 強い | PLATEAU SDK(v1 の手順書) | SDK で読む | 高。Web へはピクセル配信(#19)で、GPU のサーバーが要る。HTML5 書き出しは 4.24 で外部の拡張に移った(#20・△) |
| Unity | 対象外 | Unity の規約(本書で未読) | 本書では未確認 | 自前 | 強い | PLATEAU SDK | SDK で読む | 高。Web 書き出しは WebGL2 が既定、WebGPU は実験的(#21) |
| Rerun | web-viewer 0.38.1 | MIT/Apache-2.0(#12) | 公称なし(空欄) | 時系列の記録と再生が本業(.rrd・#12) | 点・メッシュ | なし(地図の背景は本書で未確認) | なし(本書で未確認) | 低(Python から `rr.log`)。「Expect breaking changes!」(#12) |
| Observable Plot / Vega-Lite | 0.6.17 / 6.4.3 | ISC / BSD-3-Clause(#16・#17) | 計器盤のグラフ向け(大量点向けではない・推測) | なし | なし | なし | なし | 低 |
| DuckDB-Wasm | 1.33.1-dev57.0 | 本書で未確認(空欄) | 表の問い合わせ。Parquet の必要な部分だけ読む・4 GB の上限(#14) | 時刻での絞り込みを SQL で | なし | なし | なし | 低(SQL) |
| parquet-wasm+apache-arrow | 0.9.0 / 21.2.0 | MIT/Apache-2.0(#15) | Parquet を Arrow にして型付き配列のまま deck.gl へ(#1 のバイナリ属性と組む・推測) | なし | なし | なし | なし | 低 |

**背景地図の出どころ**

| 出どころ | 条件 | v1 の不具合との関係 |
|---|---|---|
| OSM の配信タイル(v1 が使用) | Referer の送信が要る・オフライン利用は不可・予告なしの遮断あり(#22) | v1 の 4 秒ごとの再要求は規約に触れるおそれ(推測) |
| 自前の PMTiles(OSM のデータから作る) | ODbL・出典の表示(#23)。1 ファイルを範囲読み(#25) | 配信元の遅延・遮断が無くなる |
| 地理院タイル | 出典の明示で申請不要(基本測量成果は申請が要る場合あり・#24) | 配信元に依存は残る |
| PLATEAU の MVT・3D Tiles | 無償・試験的運用で期間とサービスの水準は保証なし(#26) | 配信元に依存は残る。手元に PLATEAU のデータを持つなら自前で配れる(推測) |

### 7-2 ゲーム・可視化産業から輸入できるもの

| 知見 | 出典 | v2 での形(親の案) |
|---|---|---|
| 同じ形を 1 回の描画命令でまとめて描く(インスタンス描画) | deck.gl のバイナリ属性(#1)・v1 の InstancedMesh | 39 万体を 1 層で描く。位置は Arrow の型付き配列のまま渡す |
| 段ごとの事前計算(LOD) | Kyrix・Kyrix-S(#31・#32) | 引いた画では格子の密度、寄ると点、さらに寄ると人の形。格子はビルド時に段ごとに作る |
| 3D Tiles の階層の LOD とストリーミング | CesiumJS(#7)・3DTilesRendererJS(#9) | 建物は PLATEAU の 3D Tiles を読むだけにする |
| 再生を不具合の再現に使う・ネットワークの作りと並行して作る | Overwatch(#33) | ビューアを検証の道具として最初から作る(計器盤から入る) |
| 時刻のスクラブ=I フレーム+差分 | 既存答申 game-frontend(等級 D)・R-72 §7-6 | スナップショット 6 時間ごと+出来事 |
| 走行を止めない観測 | 既存答申 game-frontend の computational steering(等級 D) | ビューアは書き終わったファイルだけを読む(§6 T-V4) |

## §8 提案(親の案・未リサーチ)

### 8-1 段階

| 段 | 作るもの | 前提 | 今の出力で作れるか |
|---|---|---|---|
| 1 | 計器盤(面 1〜3)。グラフは Observable Plot か Vega-Lite。データは JSON+Parquet を DuckDB-Wasm で読む | 判定関数の出力の形・アンサンブルの完了済みラン表 | 面 3 と D1′ は作れる。面 2 の `I_M` はアンサンブルが要る |
| 2a | 2D 俯瞰(deck.gl+MapLibre・背景は自前 PMTiles)。セルの密度の再生 | 在圏 journal | 作れる(セルの粒度まで) |
| 2b | 個体の点・個体の詳細・タイムライン | ① の記録・C5 の位置・テープ版 4 | ① の後 |
| 3 | 物語の層(関係の伝記・A/B・反実仮想・語の一生) | ① の記録・共通乱数の対・事後の抽出 | ① の後 |
| 4 | 3D(CesiumJS か three.js+3DTilesRendererJS で PLATEAU の 3D Tiles)。表示の高さは §1-4 の規則 | 空間の設計ラウンド((x, y, 階)・通路の面の高さ) | 空間の作り直しの後 |

### 8-2 データの流れ

```
ラン(エンジン)── runs/<id>/ : テープ・出来事・スナップショット・在圏 journal・センサス・manifest
        │   (ランの中ではビューア用に何も書かない=§6 T-V1 で確認)
        ▼
ビルドの道具(別プロセス・読むだけ)── view/<id>/ :
        manifest.json(入力のハッシュ・道具の版)/ judge/*.json(判定関数の出力)/
        grid/z{段}.parquet(段ごとの密度)/ tracks/day{d}_h{h}.arrow(体ごとの位置・量子化)/
        events/*.parquet(出来事の索引)/ calls_index.parquet(call_id → テープの行)
        ▼
架空名の段(最後の 1 段・§5)── public/<id>/ : ここだけが外に出る
        ▼
ビューア(静的な HTML+JS・DuckDB-Wasm と deck.gl で読む)
```

ビューアは手元では `view/` を、公表では `public/` を読む。どちらも 1 つの静的なページで、サーバーの処理は持たない案。

### 8-3 H2 の壁打ちで 1 問ずつ出す選択肢(案)

1. **誰が何のために見るか**: (a) ユーザーが挙動を確かめる道具に絞る (b) (a)+共同研究者への共有 (c) (b)+顧客(商業施設)へのデモ。架空名の段の厳しさと、見た目にかける手間がこれで決まる。
2. **最初の画面**: (a) 計器盤の 3 面をそのまま (b) 見出し(`I_M`・強い行の合否)だけを最初に出し、面は下に (c) 1 本のランしかない間は面 3 を最初に出す。
3. **2D の土台**: (a) deck.gl+MapLibre (b) kepler.gl をそのまま使う (c) 開発中は Rerun で見て、ビューアは後で作る。
4. **背景地図**: (a) 自前の PMTiles(OSM のデータ) (b) 地理院タイル (c) PLATEAU の MVT (d) OSM の配信タイル(v1 と同じ)。
5. **データの置き方**: (a) 静的なファイル+DuckDB-Wasm(サーバーなし) (b) 手元の小さなサーバー (c) v1 のような 1 ファイルの HTML。
6. **個体の詳細に出すもの**: プロンプトの全文(テープ版 4 が前提)・応答・前後の出来事・記憶の出どころ・体の値のうち、どこまでを最初に作るか。
7. **物語の層の順番**: 関係の伝記・A/B と反実仮想の対比・語の一生・物語のピンのどれから作るか。
8. **見た目の基準**: (a) 記録にあるものだけを描く(補間には印を付ける) (b) (a)に加えて昼夜の明るさを時刻に合わせる (c) 見やすさのための演出を許す。人の形(点・記号・人型)と、明暗のテーマ(固定か時刻連動か)も合わせて決める。

## §9 空欄の一覧

1. ユーザーが地図の消失を見た条件(どのビューア・画面・表示倍率・時刻)。§1-3 の候補 A〜D のどれが当たりかはこれで決まる。
2. file:// で開いたページからのタイル要求に Referer が付くか(MDN の現行版に記載が無い・#34)。OSMF に遮断されたかは未確認。
3. WebGL の文脈の喪失の扱いの原典(Khronos が 403・#35)。
4. v1 の `enter_building` の x, y が何の座標か(入口のノードか、足跡の中か)。§1-4 の 1 は推測のまま。
5. Kyrix(2019)の本文の 1 億点・100 ms の値(検索の要約のみ・#32)。
6. ENISA 2019 の本文(#30)。
7. UE の HTML5 書き出しの撤去の Epic の一次文書(#20)。
8. PLATEAU の配信の 3D Tiles の版(1.0)の公式ページ(検索の要約のみ・#27)。
9. deck.gl で 39 万体を時系列で再生したときの実測(公称は 2015 年の MacBook Pro で 100 万点の静止の pan/zoom)。
10. deck.gl・MapLibre の地形と 3D Tiles の対応(本書で読んでいない)。
11. Rerun・CesiumJS・Unity・UE の点数の公称。
12. DuckDB-Wasm のライセンス(文書のページに記載なし)。
13. 都市シミュレーションで店名を架空名に置き換えた先行例。
14. ビューア用の書き出しの容量(R-72 §7-5 の 5,000 体の測定と同時に測る)。

空欄 14 件。

## §10 写し検査の材料(親向け)

| 本書の値 | 原典の逐語(#) |
|---|---|
| 約 100 万点で 60 FPS | 「up to about 1M (one million) data items」(#1) |
| 10M で 10-20 FPS | 「framerates dropping into low double digits (10-20FPS) when the data sets approach 10M items」(#1) |
| picking 16M/層 | 「The picking system can only distinguish between 16M items per layer.」(#1) |
| PMTiles の範囲読み | 「PMTiles readers use HTTP Range Requests to fetch only the relevant tile or metadata inside a PMTiles archive on-demand.」(#25) |
| OSMF の遮断 | 「We may block access, without notice, if your usage degrades the service.」(#22) |
| Presidio の注意 | 「there is no guarantee that Presidio will find all sensitive information」(#28) |
| Kyrix-S | 「Kyrix-S enables interactive browsing of SSVs of billions of objects, with response times under 500ms」(#31) |
| DuckDB-Wasm の上限 | 「WebAssembly limits the amount of available memory to 4 GB」(#14) |
| parquet-wasm の大きさ | 「the brotli-compressed WASM bundle is 1.2 MB」(#15) |
| 夜の地図の見え方 0.16 | `0.9`(既定の不透明度・`v1:viz/make_viewer.py:2672`)×`(1−0.55)`(`:2784`)×`(1−0.6)`(`_NIGHT.night` の α・`:1835`)[再計算] |
| 人が +138 m | `v1:docs/plans/highfidelity-3d-physics-plan.md:28` の逐語(§1-4) |
| 125.7MB | `v1:docs/plans/viewer-chronicle-plan.md:9`〜`:10` の逐語(§1-5) |
