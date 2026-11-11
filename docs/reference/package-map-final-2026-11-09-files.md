# コードの区分の最終の表(全ファイル)2026-11-09

> [本文](package-map-final-2026-11-09.md)の付属の表です。設計役(Opus 5.5)が作りました。作業木の HEAD は `14b151a`(src は案 K が読んだ `15b6bbd` と同じと `git diff` で確かめました)。ファイルは 1 本も動かしていません。
> 土台は[照らし合わせ](package-map-reconcile-2026-11-05.md) §7 の合わせた案です。そこに[返事その 7](../design/prompt-2026-11-09-reply7.md) §4-1 の決着を当てました。案 K の行は[案 K の付属の表](package-map-claude-code-2026-11-05-files.md)をそのまま引き、置き場の名だけを直した所は「理由」に書きました。
> 新しい置き場は `src/shibuya/` からの相対です。割るファイルの行数は案 K の数え方(最上位の関数・クラス・定数の行の和。docstring と import を含まない)で、案 K の数をそのまま使いました。`engine/calendar_shadow.py` と `act/ops/detect_writes.py` だけはこの役の数えです。

## 1. 列の意味

- **元**: K=案 K の置き場のまま(両案が同じ 265 本を含む)。F=照らし合わせが案 F に寄せたもの。照らし合わせ=照らし合わせが両案と違う形にしたもの(消す 2 本)。11-09=返事その 7 の決着で置き場が変わったもの。
- **照らし合わせ**: 照らし合わせ §1-2 の区分。同じ=両案が同じ包み。(i)=事実の読み違い。(ii)=当てはめの違い。(iii)=原則の迷い(問いの番号)。
- **割るか**: 割るものは §4 の番号で、割り先ごとの関数・クラス・定数を載せました。
- **包み**: 割るファイルは主な割り先(いちばん大きい割り先)の包みです。

## 2. 数

- 行は 324 本(`.py` 323 本と JSON 1 本)。割るもの 24 本。消すもの 2 本。build は置き場を変えない 79 本。
- 〔移す段 1・段 2 で足した〕第346 で足された `engine/removed_switches.py` の行 224a と、移す段で足したファイル `engine/class_ids.py`(143a)・`core/paths.py`(91a)の行を足した(行は 327 本)。上と本文 §2 の数には入れていない。
- 〔移す段 3 の続きで足した〕つなぎの台帳の道の対応の表 `engine/bridging/ledger_paths.py`(125a)の行を足した(行は 328 本)。上と本文 §2 の数には入れていない。
- 元の内訳: K 298 本・11-09 18 本・F 6 本・照らし合わせ 2 本。
- 照らし合わせの区分の内訳: 同じ 265 本・(ii) 41 本・(iii) 16 本・(i) 2 本。
- 包みごとの数は本文 §2 にあります。

## 3. src(1 ファイル 1 行)

| # | 今の道筋 | 包み | 新しい置き場(割るものは行数つき) | 割るか | 理由 | 元 | 照らし合わせ |
|---:|---|---|---|---|---|---|---|
| 1 | `__init__.py` | 根 | `__init__.py`(そのまま) | いいえ | パッケージの頭。中身は版だけ | K | 同じ |
| 2 | `agents/__init__.py` | 消す | 消す | いいえ | 呼び手 0 の再輸出の頭(両案とも再輸出を消す)。古い頭は、古い包みに割るファイルが残る間は空のまま残し、最後の割りの段で消す | 照らし合わせ | (ii) 頭 |
| 3 | `agents/population.py` | world | `world/facts/population_reader.py` | いいえ | 母集団の読み口=構築した事実の読み手 | K | 同じ |
| 4 | `agents/schedule.py` | world | `world/facts/mock_schedule.py` | いいえ | mock の週次日課(構築資産の代わりの合成) | K | 同じ |
| 5 | `agents/state.py` | world | `world/model/agent_table.py` 447・`foundation/vocab/agent_codes.py` 234 | 割る(§4-1) | 語彙(列挙)と 35 万体の表が 1 つ。語彙は全層が読み、表は組み立てが渡す。問い 1 の決着=A(移すときに import の決まりと「心が読んでよい欄」の一覧)。到達点は心に渡すのは知覚だけ | K | (iii) 問い 1 |
| 6 | `agents/weekly.py` | world | `world/facts/weekly_reader.py` | いいえ | W17 週次表の読み口=構築した事実の読み手 | K | 同じ |
| 7 | `build/__init__.py` | build | `build/__init__.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。オフラインの世界データ構築 W0〜W21 の包み(実行時に import されない) | K | 同じ |
| 8 | `build/audit/__init__.py` | build | `build/audit/__init__.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W18/W19/W20(被覆指標・凍結・検収パック)の段の一覧 | K | 同じ |
| 9 | `build/audit/run.py` | build | `build/audit/run.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。被覆指標・凍結・検収パックを W 番号順に回す CLI | K | 同じ |
| 10 | `build/audit/w18_coverage.py` | build | `build/audit/w18_coverage.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W18 カタログ写像・世界被覆指標 | K | 同じ |
| 11 | `build/audit/w19_freeze.py` | build | `build/audit/w19_freeze.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W19 manifest の凍結と holdout の封印 | K | 同じ |
| 12 | `build/audit/w20_acceptance_pack.py` | build | `build/audit/w20_acceptance_pack.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W20 検収パック | K | 同じ |
| 13 | `build/catalog_freeze.py` | build | `build/catalog_freeze.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。世界カタログ(docs の md)を JSON に凍結する | K | 同じ |
| 14 | `build/field/__init__.py` | build | `build/field/__init__.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W7/W10/W12/W13(場・境界レーン)の段の一覧 | K | 同じ |
| 15 | `build/field/common.py` | build | `build/field/common.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。場・境界レーンの共有ヘルパ | K | 同じ |
| 16 | `build/field/road_names.py` | build | `build/field/road_names.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W10 の道路名の突合 | K | 同じ |
| 17 | `build/field/run.py` | build | `build/field/run.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。場・境界レーンを W 番号順に回す CLI | K | 同じ |
| 18 | `build/field/street_grid.py` | build | `build/field/street_grid.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。街路面 2.5 m 格子 | K | 同じ |
| 19 | `build/field/w10_noise.py` | build | `build/field/w10_noise.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W10 静的騒音場 | K | 同じ |
| 20 | `build/field/w10_ruler.py` | build | `build/field/w10_ruler.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W10 の物差し(較正点に町丁目の代表点を付ける) | K | 同じ |
| 21 | `build/field/w12_external_nodes.py` | build | `build/field/w12_external_nodes.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W12 外界ノード(鉄道の流入出) | K | 同じ |
| 22 | `build/field/w12_rail_events.py` | build | `build/field/w12_rail_events.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W12 の渋谷の発着の表 | K | 同じ |
| 23 | `build/field/w12_real_timetables.py` | build | `build/field/w12_real_timetables.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W12 の実ダイヤの読み口 | K | 同じ |
| 24 | `build/field/w13_weather.py` | build | `build/field/w13_weather.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W13 気象日の再生の表 | K | 同じ |
| 25 | `build/field/w7_planspec.py` | build | `build/field/w7_planspec.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W7 営業時間・価格帯 PlanSpec | K | 同じ |
| 26 | `build/geo/__init__.py` | build | `build/geo/__init__.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W0〜W6/W11(地理レーン)の段の一覧 | K | 同じ |
| 27 | `build/geo/common.py` | build | `build/geo/common.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。地理レーンの共有ヘルパ(ハッシュ・座標・格子) | K | 同じ |
| 28 | `build/geo/poi_class.py` | build | `build/geo/poi_class.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W6 POI の種別とサブカテゴリの分類 | K | 同じ |
| 29 | `build/geo/run.py` | build | `build/geo/run.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。地理レーンを回し build_manifest.json を書く CLI | K | 同じ |
| 30 | `build/geo/w0_crs.py` | build | `build/geo/w0_crs.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W0 原点・座標系の凍結 | K | 同じ |
| 31 | `build/geo/w11_station_exits.py` | build | `build/geo/w11_station_exits.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W11 駅・出口 | K | 同じ |
| 32 | `build/geo/w1_walk_graph.py` | build | `build/geo/w1_walk_graph.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W1 歩行グラフ | K | 同じ |
| 33 | `build/geo/w2_cells.py` | build | `build/geo/w2_cells.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W2 セル生成 | K | 同じ |
| 34 | `build/geo/w3_distances.py` | build | `build/geo/w3_distances.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W3 全点対距離 | K | 同じ |
| 35 | `build/geo/w4_heights.py` | build | `build/geo/w4_heights.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W4 建物・高さ | K | 同じ |
| 36 | `build/geo/w5_entrances.py` | build | `build/geo/w5_entrances.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W5 入口点 | K | 同じ |
| 37 | `build/geo/w6_poi_org.py` | build | `build/geo/w6_poi_org.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W6 POI・組織の束縛 | K | 同じ |
| 38 | `build/lang/__init__.py` | build | `build/lang/__init__.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W14/W15(静的言語化レーン)の段の一覧 | K | 同じ |
| 39 | `build/lang/common.py` | build | `build/lang/common.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W14/W15 の共有ヘルパ(プロンプトと応答の読み書き) | K | 同じ |
| 40 | `build/lang/run.py` | build | `build/lang/run.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。静的言語化レーンを回す CLI | K | 同じ |
| 41 | `build/lang/w14_signage.py` | build | `build/lang/w14_signage.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W14 看板の文面 | K | 同じ |
| 42 | `build/lang/w15_cell_static.py` | build | `build/lang/w15_cell_static.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W15 B2 セル静的文 | K | 同じ |
| 43 | `build/pop/__init__.py` | build | `build/pop/__init__.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W16(母集団合成)の段の一覧 | K | 同じ |
| 44 | `build/pop/attr_fns.py` | build | `build/pop/attr_fns.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W21 の「属性から作る関数」の置き場 | K | 同じ |
| 45 | `build/pop/fitting.py` | build | `build/pop/fitting.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。IPF・整数配分・適合度指標 | K | 同じ |
| 46 | `build/pop/pool.py` | build | `build/pop/pool.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。v1 ペルソナプールの読み取りと列化 | K | 同じ |
| 47 | `build/pop/run.py` | build | `build/pop/run.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。母集団レーンを回す CLI | K | 同じ |
| 48 | `build/pop/shapefile.py` | build | `build/pop/shapefile.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。ESRI Shapefile の最小パーサと点包含 | K | 同じ |
| 49 | `build/pop/w16_population.py` | build | `build/pop/w16_population.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W16 母集団合成 | K | 同じ |
| 50 | `build/pop/w21_apply.py` | build | `build/pop/w21_apply.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W21 段 10「差し替え」の組み立て | K | 同じ |
| 51 | `build/pop/w21_attrs.py` | build | `build/pop/w21_attrs.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W21 段 3「属性」 | K | 同じ |
| 52 | `build/pop/w21_build.py` | build | `build/pop/w21_build.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W21 段 1〜3(人数の枠・世帯と人・属性)の組み立て | K | 同じ |
| 53 | `build/pop/w21_build_b.py` | build | `build/pop/w21_build_b.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W21 段 4〜7(組織と関係・お金・開始前の経験・外の人)の組み立て | K | 同じ |
| 54 | `build/pop/w21_build_c.py` | build | `build/pop/w21_build_c.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W21 段 8〜9 と段 10 の材料の組み立て | K | 同じ |
| 55 | `build/pop/w21_check.py` | build | `build/pop/w21_check.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W21 段 8「点検」 | K | 同じ |
| 56 | `build/pop/w21_checks.py` | build | `build/pop/w21_checks.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W21 の計器(合否なし) | K | 同じ |
| 57 | `build/pop/w21_frame.py` | build | `build/pop/w21_frame.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W21 段 1「人数の枠」 | K | 同じ |
| 58 | `build/pop/w21_households.py` | build | `build/pop/w21_households.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W21 段 2「世帯と人」(焼きなましの詰め) | K | 同じ |
| 59 | `build/pop/w21_money.py` | build | `build/pop/w21_money.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W21 段 5「お金」 | K | 同じ |
| 60 | `build/pop/w21_org.py` | build | `build/pop/w21_org.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W21 段 4「組織と関係」 | K | 同じ |
| 61 | `build/pop/w21_outside.py` | build | `build/pop/w21_outside.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W21 段 7「外の人」 | K | 同じ |
| 62 | `build/pop/w21_persona.py` | build | `build/pop/w21_persona.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W21 段 9「見せ方」=事実から人物の説明文を組む | K | 同じ |
| 63 | `build/pop/w21_port10.py` | build | `build/pop/w21_port10.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W21 段 10 の材料 | K | 同じ |
| 64 | `build/pop/w21_prior.py` | build | `build/pop/w21_prior.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W21 段 6「開始前の経験」 | K | 同じ |
| 65 | `build/pop/w21_sources.py` | build | `build/pop/w21_sources.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W21 の材料の台帳と読み口の守り read_guard | K | 同じ |
| 66 | `build/pop/w21_tables.py` | build | `build/pop/w21_tables.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W21 の表の組み立て(区の雛形と町丁目への配分) | K | 同じ |
| 67 | `build/run.py` | build | `build/run.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。世界データ構築の通し実行 | K | 同じ |
| 68 | `build/sched/__init__.py` | build | `build/sched/__init__.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W17(週次スケジュール生成)の段の一覧 | K | 同じ |
| 69 | `build/sched/pool_facts.py` | build | `build/sched/pool_facts.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。ペルソナプールの「生活の素材」欄だけを引く | K | 同じ |
| 70 | `build/sched/run.py` | build | `build/sched/run.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。スケジュール生成レーンを回す CLI | K | 同じ |
| 71 | `build/sched/trial.py` | build | `build/sched/trial.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。D-68 下見(2,000 体・多腕)の別経路 | K | 同じ |
| 72 | `build/sched/vocab.py` | build | `build/sched/vocab.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W17 週次活動表の凍結語彙と行書式 | K | 同じ |
| 73 | `build/sched/w17_schedule.py` | build | `build/sched/w17_schedule.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W17 スケジュール生成(LLM のプロンプトと取り込み) | K | 同じ |
| 74 | `build/sched/w20_calendar_1a.py` | build | `build/sched/w20_calendar_1a.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W20 暦 1a(勤務と授業の約束の週の表) | K | 同じ |
| 75 | `build/sched/w20_w21_port.py` | build | `build/sched/w20_w21_port.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W21 の人の表から W20 の属性を作る口 | K | 同じ |
| 76 | `build/space/__init__.py` | build | `build/space/__init__.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。空間の段の構築側の包み | K | 同じ |
| 77 | `build/space/mesh.py` | build | `build/space/mesh.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。塗った格子からラン・門・帯を作る | K | 同じ |
| 78 | `build/space/navmesh1.py` | build | `build/space/navmesh1.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。多層の歩ける面のナビメッシュを組む | K | 同じ |
| 79 | `build/space/raster.py` | build | `build/space/raster.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。歩ける面の格子に多角形・帯・三角形を塗る | K | 同じ |
| 80 | `build/space/sources.py` | build | `build/space/sources.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。ナビメッシュの材料を手元のファイルから読む | K | 同じ |
| 81 | `build/vis/__init__.py` | build | `build/vis/__init__.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W8/W9(可視性・影レーン)の段の一覧 | K | 同じ |
| 82 | `build/vis/png.py` | build | `build/vis/png.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。最小の PNG 書き出し | K | 同じ |
| 83 | `build/vis/run.py` | build | `build/vis/run.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。可視性・影レーンを回す CLI | K | 同じ |
| 84 | `build/vis/w8_visibility.py` | build | `build/vis/w8_visibility.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W8 可視性テーブル | K | 同じ |
| 85 | `build/vis/w9_shadow.py` | build | `build/vis/w9_shadow.py`(置き場を変えない) | いいえ | 構築の段(ランで読まれない)。W9 影グリッド | K | 同じ |
| 86 | `census/__init__.py` | 消す | 消す | いいえ | 4 行の頭だけで呼び手 0(両案とも中身なし) | 照らし合わせ | (ii) 頭 |
| 87 | `cli.py` | interfaces | `interfaces/cli/main.py` 1568・`interfaces/cli/wire_economy.py` 134 | 割る(§4-2) | CLI の入口。引数と組み立てを割る。`shibuya/cli.py` は `python -m shibuya.cli` の入口として 1 行だけ残す(外との約束・案 K §2-11) | K | 同じ |
| 88 | `core/__init__.py` | foundation | `foundation/__init__.py`(空にする) | いいえ | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | K | 同じ |
| 89 | `core/budget.py` | foundation | `foundation/budget.py` | いいえ | 予算宣言表の読み口。shibuya の中を読まない | K | 同じ |
| 90 | `core/growth.py` | foundation | `foundation/growth.py` | いいえ | 状態成長の宣言と検査の型 | K | 同じ |
| 91 | `core/hashing.py` | foundation | `foundation/hashing.py` | いいえ | 決定論ハッシュ。決定論ハッシュ(blake3・xxh64・sha256_cbor)と優先度キー | K | 同じ |
| 91a | `core/paths.py` | foundation | `foundation/paths.py` | いいえ | リポの根と包みの根(移す段 2-2 で足した。置き場は本文 §7-3 のとおり)。標準ライブラリだけを読む | 移す段 2 | — |
| 92 | `core/rng.py` | foundation | `foundation/rng.py` | いいえ | カウンタベース乱数。カウンタベース乱数(Philox)のドメイン分離 | K | 同じ |
| 93 | `core/serialize.py` | foundation | `foundation/serialize.py` | いいえ | SoA の保存の道具(呼び手は試験だけ) | K | 同じ |
| 94 | `core/soa.py` | foundation | `foundation/soa.py` | いいえ | SoA レジストリ。SoA レジストリとバイト予算宣言 M9 | K | 同じ |
| 95 | `core/time_consts.py` | foundation | `foundation/time_consts.py` | いいえ | 時間の定数。時間の定数と秒⇔刻みの換算 | K | 同じ |
| 96 | `core/types.py` | foundation | `foundation/types.py` | いいえ | 時刻・ID の型。時刻・ID・イベントクラスの固定 dtype | K | 同じ |
| 97 | `core/wage_formula.py` | economy | `economy/wage_formula.py` | いいえ | 中身は経済(core の下に置く理由が無い) | K | 同じ |
| 98 | `core/write_permit.py` | foundation | `foundation/write_permit.py` | いいえ | 書きの許可の入れ物。系ごとの「書いてよい SoA の列」の実行時の守り | K | 同じ |
| 99 | `economy/__init__.py` | economy | `economy/__init__.py`(空にする) | いいえ | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | K | 同じ |
| 100 | `economy/accounts.py` | economy | `economy/accounts.py` | いいえ | 経済の中身。部門・貸借の行・取引科目の列挙と faucet/sink 表 | K | 同じ |
| 101 | `economy/anchors.py` | economy | `economy/anchors.py` | いいえ | 経済の中身。金額アンカー(公的値)と初期財布・月次賃金 | K | 同じ |
| 102 | `economy/census.py` | economy | `economy/census.py` | いいえ | 経済の中身。日次センサスと月次 MER・ゲート判定 | K | 同じ |
| 103 | `economy/checks.py` | economy | `economy/checks.py` | いいえ | 経済の中身。検算 2 本(Caiani 2016)・残差ゲート・退蔵・ex nihilo の検査 | K | 同じ |
| 104 | `economy/credit.py` | economy | `economy/credit.py` | いいえ | 経済の中身。信用の器 C1〜C3(`CreditBook`・`repay_due`)。呼び手なし | K | 同じ |
| 105 | `economy/entry_capital.py` | economy | `economy/entry_capital.py` | いいえ | 経済の中身。店の参入資本を経済センサスから按分する | K | 同じ |
| 106 | `economy/goods.py` | economy | `economy/goods.py` | いいえ | 経済の中身。物の保存則。`move_goods` 単一 API と SKU 別収支 | K | 同じ |
| 107 | `economy/ledger.py` | economy | `economy/ledger.py` | いいえ | 経済の中身。金の台帳 U11。`transfer` 単一 API と取引フロー行列 | K | 同じ |
| 108 | `economy/ops.py` | economy | `economy/ops.py` | いいえ | 経済の中身。お金の基本操作「移す」=残高を書く唯一の関数 | K | 同じ |
| 109 | `economy/pricing.py` | economy | `economy/pricing.py` | いいえ | 経済の中身。価格形成(内生フロア・Calvo・逸脱比例コスト) | K | 同じ |
| 110 | `economy/stage2.py` | economy | `economy/stage2.py` | いいえ | 経済の中身。経済の段階 2(賃金・引き出し・支払い・レジの税・来街者の口座) | K | 同じ |
| 111 | `economy/tax_deposit.py` | economy | `economy/tax_deposit.py` | いいえ | 経済の中身。店の預かり消費税 | K | 同じ |
| 112 | `economy/taxes.py` | economy | `economy/taxes.py` | いいえ | 経済の中身。規則の表の税・社会保険・消費税・信用の上限の読み手 | K | 同じ |
| 113 | `economy/wages.py` | economy | `economy/wages.py` | いいえ | 経済の中身。賃金構造基本統計の賃金と最低賃金の床 | K | 同じ |
| 114 | `engine/__init__.py` | runtime | `runtime/__init__.py`(空にする) | いいえ | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む)。古い頭は、古い包みに割るファイルが残る間は空のまま残し、最後の割りの段で消す | K | 同じ |
| 115 | `engine/absent_processes.py` | world | `world/laws/switch_absent.py` | いいえ | 「無い」過程の切替口(3-2 で消す候補)。11-05 §3-2 の削除の対象(消えれば行も消す) | K | 同じ |
| 116 | `engine/activity.py` | act | `act/activity.py` | いいえ | 持続する活動の実行。行為と活動の二層の活動層。問い 5 の決着=A(今は act・本人には知覚の欄で見せる)。到達点は意図と予定は心・実行の仕組みは act(9-2・9-5 で割る) | K | (iii) 問い 5 |
| 117 | `engine/arbiter.py` | runtime | `runtime/arbiter.py` 457・`mind/system1/wake.py` 63 | 割る(§4-3) | 呼数の裁定。9-4 で消える。型だけ割る | K | 同じ |
| 118 | `engine/batching.py` | foundation | `foundation/queues/batching.py` | いいえ | 計算のまとめの窓。連絡の配達と runtime が読む | K | (ii) |
| 119 | `engine/body/__init__.py` | world | `world/body/__init__.py`(空にする) | いいえ | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | K | 同じ |
| 120 | `engine/body/model.py` | world | `world/body/model.py` | いいえ | 本人の体の層 | K | 同じ |
| 121 | `engine/body/rules.py` | world | `world/body/rules.py` | いいえ | 体の規則の値と純関数=9-1 の外 | K | 同じ |
| 122 | `engine/body/schedule.py` | world | `world/body/schedule.py` | いいえ | 体の段の境目の予約。段の境目を越える時刻の予約 TM5 | K | 同じ |
| 123 | `engine/body/system1.py` | world | `world/body/reactions.py` | いいえ | 体の側の意図しない反応の器(9-3c で意味の表は持たない) | K | 同じ |
| 124 | `engine/bridging/__init__.py` | foundation | `foundation/decl/__init__.py`(空にする) | いいえ | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | K | (ii) 頭 |
| 125 | `engine/bridging/ledger.py` | foundation | `foundation/decl/bridging.py` | いいえ | つなぎの台帳の読み口。世界・社会の腕・runtime が読み、ほかを読まない | K | 同じ |
| 125a | `engine/bridging/ledger_paths.py` | foundation | `foundation/decl/ledger_paths.py` | いいえ | 今の道 → つなぎの台帳に書いてある道の対応の表(移す段 3 の続きで足した・親の決定 1=案 (b)。移す道具が段ごとに書き足す)。何も読まない。読み手は宣言の走査と試験だけ。台帳の読み口と同じ `foundation/decl/` に置く | 移す段 3 | — |
| 126 | `engine/bridging/scan.py` | validation | `validation/static/bridging_scan.py` | いいえ | expedient の宣言の検査(試験と道具だけ) | K | 同じ |
| 127 | `engine/calendar.py` | world | `world/facts/calendar.py` 386・`foundation/types.py` 9 | 割る(§4-4) | 暦。刻みの換算だけ割る。`REPO_ROOT`・`resolve_repo_path` は移す段 2 で `core/paths.py`(移した後は `foundation/paths.py`)へ出す案(本文 §7-3) | K | (ii) |
| 128 | `engine/calendar2/__init__.py` | interim_bundles | `interim_bundles/calendar2/__init__.py`(空にする) | いいえ | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む)。問い 4 の決着=12 番目の一時の区分 interim_bundles(社会の区分には入れない) | 11-09 | (iii) 問い 4 |
| 129 | `engine/calendar2/arm.py` | foundation | `foundation/arms/calendar2.py` | いいえ | 腕の切替口。何も読まない。CLI・心・社会の腕が読む | K | (ii) |
| 130 | `engine/calendar2/book.py` | mind | `mind/plan/promise_book.py` | いいえ | 本人の理解としての予定(CA3) | K | 同じ |
| 131 | `engine/calendar2/layer.py` | interim_bundles | `interim_bundles/calendar2/layer.py` | いいえ | 腕の持ち主と系(心・器・体の実行の束ね=v3 で割る)。問い 4 の決着=12 番目の一時の区分 interim_bundles(社会の区分には入れない) | 11-09 | (iii) 問い 4 |
| 132 | `engine/calendar2/port.py` | mind | `mind/plan/calendar2_port.py` | いいえ | カレンダー 2 の本人の判断 | K | 同じ |
| 133 | `engine/calendar2/recall.py` | mind | `mind/plan/head_recall.py` | いいえ | 頭の中の予定の思い出し | K | 同じ |
| 134 | `engine/calendar3/__init__.py` | interim_bundles | `interim_bundles/calendar3/__init__.py`(空にする) | いいえ | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む)。問い 4 の決着=12 番目の一時の区分 interim_bundles(社会の区分には入れない) | 11-09 | 同じ |
| 135 | `engine/calendar3/arm.py` | foundation | `foundation/arms/calendar3.py` | いいえ | 腕の切替口。何も読まない。CLI・心・社会の腕が読む | K | (ii) |
| 136 | `engine/calendar3/knowledge.py` | interim_bundles | `interim_bundles/calendar3/knowledge.py` | いいえ | 常識と店の決まりの問い合わせの口 | 11-09 | (ii) |
| 137 | `engine/calendar3/layer.py` | interim_bundles | `interim_bundles/calendar3/layer.py` | いいえ | 腕の持ち主と系(心・器・体の実行の束ね=v3 で割る)。問い 4 の決着=12 番目の一時の区分 interim_bundles(社会の区分には入れない) | 11-09 | 同じ |
| 138 | `engine/calendar3/port.py` | mind | `mind/plan/calendar3_port.py` | いいえ | カレンダー 3 の本人の判断 | K | 同じ |
| 139 | `engine/calendar3/roster.py` | interim_bundles | `interim_bundles/calendar3/roster.py` | いいえ | 雇い主の口のつなぎ。問い 4 の決着=12 番目の一時の区分 interim_bundles(社会の区分には入れない) | 11-09 | 同じ |
| 140 | `engine/calendar_self.py` | interim_bundles | `interim_bundles/calendar_self.py` | いいえ | 腕。本人の判断と体の実行の束ね(v3 で割る)。問い 4 の決着=12 番目の一時の区分 interim_bundles(社会の区分には入れない) | 11-09 | (iii) 問い 4 |
| 141 | `engine/calendar_shadow.py` | society | `society/calendar_shadow.py` 197・`world/facts/w20_calendar_reader.py` 115 | 割る(§4-5) | W20 の勤務と授業の週の表の読み口(束ねが出勤・通学に使う=世界の事実)と、暦 1a の影の計器が 1 つ。割る | 11-09 | (i) |
| 142 | `engine/change_detect.py` | mind | `mind/system1/change_detect.py` 290・`world/model/scene_hash.py` 63・`foundation/vocab/agent_codes.py` 6 | 割る(§4-6) | System 1 と B4 の指紋が 1 つ。割る | K | 同じ |
| 143 | `engine/chooser.py` | mind | `mind/judge/chooser.py` 153・`foundation/ports/choice.py` 69 | 割る(§4-7) | 選び手の口と実装。口だけ割る | K | 同じ |
| 143a | `engine/class_ids.py` | runtime | `runtime/state/class_ids.py` | いいえ | クラスの名の固定の表(移す段 1 で足した。置き場は本文 §7-1 のとおり)。何も読まない。読み手は状態のハッシュ・状態のファイル・再開・系ごとの指紋 | 移す段 1 | — |
| 144 | `engine/classical.py` | mind | `mind/judge/classical.py` | いいえ | 古典の方策。System 1.5 の古典的選択モデル | K | 同じ |
| 145 | `engine/clock.py` | runtime | `runtime/clock.py` | いいえ | 時計。シミュレーション時計 | K | 同じ |
| 146 | `engine/commit.py` | act | `act/intake/from_words.py` 542・`act/commit.py` 300・`foundation/vocab/act_codes.py` 34 | 割る(§4-8) | 取り合いの裁定と言葉の読みが 1 つ。割る | K | 同じ |
| 147 | `engine/contact/__init__.py` | interim_bundles | `interim_bundles/contact/__init__.py`(空にする) | いいえ | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む)。問い 4 の決着=12 番目の一時の区分 interim_bundles(社会の区分には入れない) | 11-09 | 同じ |
| 148 | `engine/contact/arm.py` | foundation | `foundation/arms/contact.py` | いいえ | 腕の切替口。何も読まない。CLI・心・社会の腕が読む | K | (ii) |
| 149 | `engine/contact/attention.py` | mind | `mind/plan/contact_attention.py` | いいえ | 目と心の向き | K | 同じ |
| 150 | `engine/contact/book.py` | interim_bundles | `interim_bundles/contact/book.py` | いいえ | 宛先の持ち主。宛先(連絡先とグループ)の持ち主。問い 4 の決着=12 番目の一時の区分 interim_bundles(社会の区分には入れない)。連絡帳は持ち物=到達点は world/things(今は心の関係の層を読むので、world に置くと world から mind への辺になる) | 11-09 | 同じ |
| 151 | `engine/contact/calls.py` | interim_bundles | `interim_bundles/contact/calls.py` | いいえ | 電話の会話。問い 4 の決着=12 番目の一時の区分 interim_bundles(社会の区分には入れない)。運ぶ器(問い 3)。import は foundation と society だけ=今 society に置くかは本文 §8 の聞きたいこと 1 | 11-09 | 同じ |
| 152 | `engine/contact/chat_state.py` | interim_bundles | `interim_bundles/contact/chat_state.py` | いいえ | チャットの会話の状態。問い 4 の決着=12 番目の一時の区分 interim_bundles(社会の区分には入れない)。運ぶ器(問い 3)。import は foundation と society だけ=今 society に置くかは本文 §8 の聞きたいこと 1 | 11-09 | 同じ |
| 153 | `engine/contact/deliver.py` | interim_bundles | `interim_bundles/contact/deliver.py` | いいえ | メッセージを届ける器。メッセージ・電話・既読を届ける。問い 4 の決着=12 番目の一時の区分 interim_bundles(社会の区分には入れない)。運ぶ器(問い 3)。import は foundation と society だけ=今 society に置くかは本文 §8 の聞きたいこと 1 | 11-09 | 同じ |
| 154 | `engine/contact/device.py` | world | `world/things/device.py` | いいえ | 持ち物(電池・電源・マナーモード・かばん)=世界の状態(CT0) | F | (ii) |
| 155 | `engine/contact/habit.py` | mind | `mind/plan/contact_habit.py` | いいえ | 連絡の習慣。CT4 の連絡の習慣 | K | 同じ |
| 156 | `engine/contact/layer.py` | interim_bundles | `interim_bundles/contact/layer.py` | いいえ | 腕の持ち主と系(心・器・体の実行の束ね=v3 で割る)。問い 4 の決着=12 番目の一時の区分 interim_bundles(社会の区分には入れない) | 11-09 | 同じ |
| 157 | `engine/contact/port.py` | mind | `mind/plan/contact_port.py` | いいえ | 連絡の本人の判断。連絡の本人の判断(J0 の形の仮のモデル) | K | 同じ |
| 158 | `engine/contact/tools.py` | interim_bundles | `interim_bundles/contact/tools.py` | いいえ | 道具の台帳へ足す。連絡の道具を道具の台帳へ足す。問い 4 の決着=12 番目の一時の区分 interim_bundles(社会の区分には入れない)。運ぶ器(問い 3)。import は foundation と society だけ=今 society に置くかは本文 §8 の聞きたいこと 1 | 11-09 | 同じ |
| 159 | `engine/conversation.py` | society | `society/conversation.py` | いいえ | 会話のセッションの器。会話プロトコルのセッション状態機械 | K | 同じ |
| 160 | `engine/decision/__init__.py` | mind | `mind/judge/decision/__init__.py`(空にする) | いいえ | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | K | (ii) |
| 161 | `engine/decision/layer.py` | mind | `mind/judge/decision/layer.py` | いいえ | 候補の口の腕と層。候補の口 J0 の腕と層 | K | (ii) |
| 162 | `engine/decision/persona.py` | mind | `mind/judge/decision/persona.py` | いいえ | 人物の欄(器)。人物の欄(短い版・長い版)と差し替えの口 | K | 同じ |
| 163 | `engine/decision/port.py` | foundation | `foundation/ports/decision.py` | いいえ | 候補の口の型。心も社会の腕も読む | K | 同じ |
| 164 | `engine/decision/ports.py` | mind | `mind/judge/decision/ports.py` | いいえ | 候補の口の 3 実装 | K | (ii) |
| 165 | `engine/decision/sources.py` | mind | `mind/judge/decision/sources.py` | いいえ | 候補を作る。候補を 5 つの源から作る | K | 同じ |
| 166 | `engine/defect_fixes_1103.py` | runtime | `runtime/switch_defects.py` | いいえ | 欠陥 4 件(会話の終わり・列の印・列での支払い・返事待ち)の切替口。読み手は組み立て・結果・状態の書き出し・CLI だけ。11-05 §3-2 の削除の対象(消えれば行も消す) | F | (ii) |
| 167 | `engine/duties/__init__.py` | interim_bundles | `interim_bundles/duties/__init__.py`(空にする) | いいえ | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む)。問い 4 の決着=12 番目の一時の区分 interim_bundles(社会の区分には入れない) | 11-09 | (iii) 問い 4 |
| 168 | `engine/duties/arm.py` | foundation | `foundation/arms/duties.py` | いいえ | 腕の切替口。何も読まない。CLI・心・社会の腕が読む | K | (ii) |
| 169 | `engine/duties/knowledge.py` | interim_bundles | `interim_bundles/duties/knowledge.py` | いいえ | 常識と店の決まりの問い合わせの口 | 11-09 | (ii) |
| 170 | `engine/duties/layer.py` | interim_bundles | `interim_bundles/duties/layer.py` | いいえ | 腕の持ち主と系(心・器・体の実行の束ね=v3 で割る)。問い 4 の決着=12 番目の一時の区分 interim_bundles(社会の区分には入れない) | 11-09 | (iii) 問い 4 |
| 171 | `engine/duties/port.py` | mind | `mind/plan/duties_port.py` | いいえ | 店の仕事の本人の判断。店の仕事の本人の判断(J0 の形の仮のモデル) | K | 同じ |
| 172 | `engine/economy_rules.py` | economy | `economy/rules_bind.py` | いいえ | 規則の表を経済の段階 2 に挿す口 | K | 同じ |
| 173 | `engine/economy_stage2.py` | economy | `economy/stage2_bind.py` | いいえ | 経済の段階 2 の切替口と組み立て | K | 同じ |
| 174 | `engine/energy.py` | world | `world/body/energy.py` | いいえ | 体のエネルギー収支 | K | 同じ |
| 175 | `engine/events/__init__.py` | foundation | `foundation/journal/__init__.py`(空にする) | いいえ | 出来事の記録の小包みの頭。古い頭は、古い包みに割るファイルが残る間は空のまま残し、最後の割りの段で消す | F | (ii) 頭 |
| 176 | `engine/events/body.py` | mind | `mind/memory/body_events.py` 130・`foundation/vocab/events.py` 25 | 割る(§4-9) | BodyEventLink は記憶の器 memory_store の body_events として持たれる。語の変換は語彙へ | F | (ii) |
| 177 | `engine/events/links.py` | foundation | `foundation/journal/links.py` | いいえ | 記録の行に出来事の目印を付ける口。読むのは出来事の記録と語彙だけ | F | (ii) |
| 178 | `engine/events/log.py` | foundation | `foundation/journal/log.py` | いいえ | 出来事の記録 5W1H。語彙と書きの許可だけを読み、全層が書く(本文は割らない)。置き場の名は小包み foundation/journal の中へ(案 K は foundation/journal.py) | K | 同じ |
| 179 | `engine/events/vocab.py` | foundation | `foundation/vocab/events.py` | いいえ | 出来事の閉じた語彙。行動の語彙だけを読む | K | 同じ |
| 180 | `engine/experiment/__init__.py` | experiments | `experiments/__init__.py`(空にする) | いいえ | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | K | 同じ |
| 181 | `engine/experiment/apply.py` | experiments | `experiments/port/apply.py` | いいえ | 申込書と世界に入る口(runtime が読む)。申込書の改変を世界に入れる口 | K | 同じ |
| 182 | `engine/experiment/branch.py` | experiments | `experiments/drive/branch.py` | いいえ | 分岐の駆動(runtime の上) | K | 同じ |
| 183 | `engine/experiment/checks.py` | experiments | `experiments/port/checks.py` | いいえ | 申込書と世界に入る口(runtime が読む)。申込書の点検 | K | 同じ |
| 184 | `engine/experiment/ensemble.py` | experiments | `experiments/port/ensemble.py` | いいえ | 申込書と世界に入る口(runtime が読む)。アンサンブルの封印・事前登録・技量スコアの器 | K | 同じ |
| 185 | `engine/experiment/form.py` | experiments | `experiments/port/form.py` | いいえ | 申込書と世界に入る口(runtime が読む)。反実仮想の申込書 | K | 同じ |
| 186 | `engine/experiment/gate.py` | foundation | `foundation/ports/experiment_gate.py` | いいえ | 実験が世界に入る唯一の口。出来事の型が検査のために読むので下に置く | K | (ii) |
| 187 | `engine/experiment/layer.py` | experiments | `experiments/port/layer.py` | いいえ | 申込書と世界に入る口(runtime が読む)。申込書をランに置く口と系 experiment | K | 同じ |
| 188 | `engine/experiment/switch.py` | experiments | `experiments/drive/switch.py` | いいえ | 切り替えの駆動(runtime の上) | K | 同じ |
| 189 | `engine/experiment/warmup.py` | experiments | `experiments/port/warmup.py` | いいえ | 申込書と世界に入る口(runtime が読む)。慣らしの判定の規則の事前登録 | K | 同じ |
| 190 | `engine/familiarity.py` | mind | `mind/memory/familiarity.py` | いいえ | 親しみ。親しみの表=訪問と露出のカウンタ | K | 同じ |
| 191 | `engine/geometry.py` | world | `world/model/geometry.py` | いいえ | 位置の幾何と歩く速さ。位置幾何の切替口と希望歩行速度 | K | 同じ |
| 192 | `engine/growth_decl.py` | runtime | `runtime/state/growth_decl.py` | いいえ | 状態成長の宣言。エンジン側の状態成長宣言 | K | (ii) |
| 193 | `engine/intent.py` | act | `act/intent.py` | いいえ | 行為の実行中の状態の保持。問い 5 の決着=A(今は act・本人には知覚の欄で見せる)。到達点は意図と予定は心・実行の仕組みは act(9-2・9-5 で割る) | K | (iii) 問い 5 |
| 194 | `engine/ledger_api.py` | foundation | `foundation/ports/ledger.py` | いいえ | 台帳の依存逆転の口(Protocol)。経済の中身を読まない | K | (ii) |
| 195 | `engine/llm_bridge.py` | runtime | `runtime/inference/bridge.py` 825・`foundation/ports/inference.py` 53 | 割る(§4-10) | 推論の口と描画の橋。割る | K | 同じ |
| 196 | `engine/manifest_sections.py` | foundation | `foundation/manifest/sections.py` | いいえ | manifest の欄の分け方=manifest の型と同じ種類の表(実験の分岐も読む) | F | (ii) |
| 197 | `engine/memory.py` | mind | `mind/memory/memory.py` | いいえ | 記憶の記録と想起。記憶 第 1 段の記録と想起 | K | 同じ |
| 198 | `engine/memory_embed.py` | mind | `mind/memory/memory_embed.py` | いいえ | 埋め込みの口。記憶 MR2 の埋め込みの口 | K | 同じ |
| 199 | `engine/memory_impression.py` | mind | `mind/memory/memory_impression.py` | いいえ | 印象の器。記憶 M3 の印象の履歴と寝たときの書き直しの器 | K | 同じ |
| 200 | `engine/memory_m1.py` | mind | `mind/memory/memory_m1.py` | いいえ | 記憶の強さの式。記憶 MR の強さの式・個人差・腕の切替口 | K | 同じ |
| 201 | `engine/memory_shops.py` | mind | `mind/memory/memory_shops.py` | いいえ | 店の評価の行。人も記憶の腕の店の評価の行 | K | 同じ |
| 202 | `engine/memory_store.py` | mind | `mind/memory/memory_store.py` | いいえ | 記憶の器。記憶の器 M0 | K | 同じ |
| 203 | `engine/memory_trace.py` | mind | `mind/memory/memory_trace.py` | いいえ | 浅い痕跡の器。注意を向けずに見ていた人の浅い痕跡の器 | K | 同じ |
| 204 | `engine/norm_meter.py` | society | `society/norm_meter.py` | いいえ | 群と規範の計器=読むだけ | K | (ii) |
| 205 | `engine/owner_guard.py` | runtime | `runtime/clocks/owner_guard.py` | いいえ | 外の状態の持ち主の守り。外の状態の持ち主の実行時の守り | K | (ii) |
| 206 | `engine/poi_target.py` | act | `act/target.py` 617・`foundation/vocab/place_words.py` 74 | 割る(§4-11) | 穴の値を決める。語彙の定数だけ割る | K | 同じ |
| 207 | `engine/presence.py` | world | `world/laws/presence.py` 1511・`world/laws/presence_plan.py` 402 | 割る(§4-12) | 在圏の出入りの法則と計画の読み。割る | K | 同じ |
| 208 | `engine/processes/__init__.py` | world | `world/laws/__init__.py`(空にする) | いいえ | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | K | 同じ |
| 209 | `engine/processes/civic.py` | world | `world/laws/civic.py` | いいえ | 公共サービスほかの世界過程 | K | 同じ |
| 210 | `engine/processes/crowd.py` | world | `world/laws/crowd.py` | いいえ | 混雑の集約。混雑場・流れ・屋内占有・待ち行列 | K | 同じ |
| 211 | `engine/processes/environment.py` | world | `world/laws/environment.py` | いいえ | 天気と体感温度。昼夜・天候・体感温度 | K | 同じ |
| 212 | `engine/processes/goods_flow.py` | world | `world/laws/goods_flow.py` | いいえ | 補充・入荷ほかのつなぎの過程 | K | 同じ |
| 213 | `engine/processes/logistics.py` | world | `world/laws/logistics.py` | いいえ | 宅配ほかの過程。宅配・バス/タクシー・道路工事 | K | 同じ |
| 214 | `engine/processes/opening.py` | world | `world/laws/opening.py` | いいえ | 開閉店のつなぎの過程。営業時間と役割行動「開閉店」 | K | 同じ |
| 215 | `engine/processes/rail.py` | world | `world/laws/rail.py` | いいえ | 鉄道の運行。鉄道運行(ODPT 静的ダイヤ) | K | 同じ |
| 216 | `engine/processes/rail_events.py` | world | `world/laws/rail_events.py` | いいえ | 発着の表の読み口(器)。渋谷の発着の表(W12 1.3.0)を読む口の器 | K | 同じ |
| 217 | `engine/processes/runner.py` | world | `world/laws/runner.py` | いいえ | 世界過程の実行器。世界過程の実行器=台帳→実装の唯一の橋 | K | 同じ |
| 218 | `engine/processes/salient.py` | world | `world/laws/salient.py` | いいえ | 顕著な出来事の過程。顕著行為と p_notice の結線 | K | 同じ |
| 219 | `engine/processes/traffic.py` | world | `world/laws/traffic.py` | いいえ | 自動車交通。断面自動車交通 | K | 同じ |
| 220 | `engine/proximity.py` | world | `world/model/proximity.py` | いいえ | 距離で決まる届く範囲=物理 | K | 同じ |
| 221 | `engine/rate_rules.py` | world | `world/laws/switch_rate.py` | いいえ | 率の規則の切替口(3-2 で消す候補)。11-05 §3-2 の削除の対象(消えれば行も消す) | K | 同じ |
| 222 | `engine/regional_clock.py` | runtime | `runtime/clocks/regional.py` | いいえ | 場所ごとの時計の腕。場所ごとの時計 T4 | K | 同じ |
| 223 | `engine/relations.py` | mind | `mind/relations/layer.py` 746・`world/facts/initial_ties.py` 326・`foundation/vocab/relations.py` 42 | 割る(§4-13) | 客観の初期の辺と主観の辺が 1 つ。割る。問い 3 の決着=A(世界の事実・運ぶ器・本人の理解の 3 か所。世界の事実から本人の理解への写しは始めの 1 回) | K | (iii) 問い 3 |
| 224 | `engine/relations_people.py` | mind | `mind/relations/people.py` | いいえ | 人も記憶の腕の関係の読み口=本人の理解 | K | 同じ |
| 224a | `engine/removed_switches.py` | foundation | `foundation/arms/removed.py` | いいえ | 消した切替口の一覧と、渡されたら止める口(第346 で足した)。標準ライブラリだけを読む。読み手は世界の法則(`seat_release`・`proximity`)・経済の規則の口(`economy_rules`)・runtime(組み立て・欠陥の切替口)・CLI で、全部より下の foundation に置き、切替口 4 本と同じ `foundation/arms/` に並べる案(移す段 1 で足した行。置き場は段 4 の前に親が確かめる) | 移す段 1 | — |
| 225 | `engine/resolve.py` | act | `act/apply.py` 454・`act/ops/shop.py` 454・`act/ops/rail.py` 379・`act/ops/move.py` 322・`act/ops/plan_writes.py` 309・`mind/ops.py` 208・`act/ops/law_writes.py` 197・`act/ops/body_writes.py` 158・`act/gate.py` 154・`act/ops/talk.py` 154・`runtime/state/restore.py` 136・`act/ops/intent_writes.py` 115・`act/ops/focus.py` 94・`act/ops/init_writes.py` 82・`foundation/write_guard.py` 33・`act/ops/detect_writes.py` 10・`foundation/vocab/act_codes.py` 3・`foundation/vocab/agent_codes.py` 2 | 割る(§4-14) | 書き手の全部。割る。`apply_detection` だけは世界の欄 `cells.b4_hash` を書くので、11-09 の書きの文(世界の欄を書く関数は act だけ)に合わせて `act/ops/detect_writes.py` へ(案 K は `mind/ops.py`) | K | 同じ |
| 226 | `engine/resume.py` | runtime | `runtime/state/resume.py` | いいえ | 再開と設定の指紋。日境界の再開と通しランの状態の書き出し・読み込み・設定の指紋 | K | 同じ |
| 227 | `engine/rights/__init__.py` | world | `world/facts/rights/__init__.py`(空にする) | いいえ | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む)。問い 7 の決着=world の事実の側 | K | (iii) 問い 7 |
| 228 | `engine/rights/initial.py` | world | `world/facts/rights/initial.py` | いいえ | 権利台帳の最初の中身。問い 7 の決着=world の事実の側 | K | (iii) 問い 7 |
| 229 | `engine/rights/ledger.py` | world | `world/facts/rights/ledger.py` | いいえ | 誰が権利を持つかの客観の事実(9-1 の外)。問い 7 の決着=world の事実の側 | K | (iii) 問い 7 |
| 230 | `engine/rights/record.py` | world | `world/facts/rights/record.py` | いいえ | 許可のない行動の記録。許可のない行動の記録と役割語の権利の確かめ。問い 7 の決着=world の事実の側 | K | (iii) 問い 7 |
| 231 | `engine/rng_audit.py` | validation | `validation/static/rng_audit.py` | いいえ | 乱数の検査(試験だけ)。K19 の検査=乱数の流れのブロックの重なり | K | 同じ |
| 232 | `engine/rules/__init__.py` | world | `world/facts/rules/__init__.py`(空にする) | いいえ | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む)。問い 7 の決着=world の事実の側 | K | (iii) 問い 7 |
| 233 | `engine/rules/table.py` | world | `world/facts/rules/table.py` | いいえ | 現実の法と制度の値=事実。経済も読む。問い 7 の決着=world の事実の側 | K | (iii) 問い 7 |
| 234 | `engine/run.py` | runtime | `runtime/result.py` 1227・`runtime/run.py` 987・`interfaces/cli/run_args.py` 193 | 割る(§4-15) | ランの結果と入口と CLI の補助。割る | K | 同じ |
| 235 | `engine/run_kind.py` | experiments | `experiments/port/run_kind.py` | いいえ | ランの種類の決まり。ランの種類(再現・反実仮想・腕・試験)を決めて manifest へ | K | 同じ |
| 236 | `engine/scheduler.py` | foundation | `foundation/queues/scheduler.py` | いいえ | 汎用の予約の列。体の層と runtime が読む | K | (ii) |
| 237 | `engine/seat_release.py` | world | `world/laws/switch_seat.py` | いいえ | 在席の解き方の切替口。在席の印を歩き出しで解く切替口(既定 walk) | K | 同じ |
| 238 | `engine/solar.py` | world | `world/model/solar.py` | いいえ | 太陽の位置と WBGT。太陽の位置と WBGT の推定 | K | 同じ |
| 239 | `engine/space/__init__.py` | world | `world/model/space/__init__.py`(空にする) | いいえ | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | K | 同じ |
| 240 | `engine/space/nav1.py` | world | `world/model/space/nav1.py` | いいえ | ナビメッシュの移動の問い合わせ(書くのは act) | K | 同じ |
| 241 | `engine/spatial_index.py` | world | `world/model/spatial_index.py` | いいえ | 近傍の索引 | K | 同じ |
| 242 | `engine/speech/__init__.py` | society | `society/speech/__init__.py`(空にする) | いいえ | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | K | 同じ |
| 243 | `engine/speech/layer.py` | society | `society/speech/layer.py` | いいえ | 会話の番から発話を作る糸 | K | 同じ |
| 244 | `engine/speech/port.py` | society | `society/speech/port.py` | いいえ | 発話の口と未読の列。発話の口 | K | 同じ |
| 245 | `engine/speech_clock.py` | runtime | `runtime/clocks/speech.py` | いいえ | 会話の時計の腕。会話の時計 T2 | K | 同じ |
| 246 | `engine/state_codec.py` | runtime | `runtime/state/codec.py` | いいえ | 状態のファイル。状態のファイルの直列化 npz+json | K | 同じ |
| 247 | `engine/state_hashes.py` | runtime | `runtime/state/hashes.py` | いいえ | 2 つのハッシュ。behavior-hash と full-hash | K | (ii) |
| 248 | `engine/state_ledger.py` | runtime | `runtime/state/ledger.py` | いいえ | 状態台帳。状態台帳の宣言(挙動と復元の 2 軸) | K | (ii) |
| 249 | `engine/state_ledger_ast.py` | runtime | `runtime/state/ledger_ast.py` | いいえ | 列の読み手の AST の検査。起動時に allow が読む | K | (ii) |
| 250 | `engine/step_scope.py` | runtime | `runtime/clocks/step_scope.py` | いいえ | 何かあった体だけ進める腕 | K | 同じ |
| 251 | `engine/store_choice.py` | mind | `mind/judge/store_choice.py` | いいえ | 想起優先の候補。想起優先の候補合成と決め手の記録 | K | 同じ |
| 252 | `engine/store_memory.py` | mind | `mind/memory/store_memory.py` | いいえ | 店の評価の記憶 | K | 同じ |
| 253 | `engine/systems/__init__.py` | runtime | `runtime/systems/__init__.py`(空にする) | いいえ | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | K | 同じ |
| 254 | `engine/systems/act.py` | runtime | `runtime/systems/act.py` | いいえ | 系の配線。行為の解決の系 | K | 同じ |
| 255 | `engine/systems/allow.py` | runtime | `runtime/systems/allow.py` | いいえ | 系の配線。系の書いてよい SoA の列を resolve の静的な閉包から作る | K | 同じ |
| 256 | `engine/systems/body.py` | runtime | `runtime/systems/body.py` | いいえ | 系の配線。体の系 | K | 同じ |
| 257 | `engine/systems/boxes.py` | runtime | `runtime/systems/boxes.py` | いいえ | 系の配線。run_day の状態の箱 | K | 同じ |
| 258 | `engine/systems/build.py` | runtime | `runtime/systems/assemble.py` | いいえ | 全部の口を組み立てる場所 | K | 同じ |
| 259 | `engine/systems/conductor.py` | runtime | `runtime/systems/conductor.py` | いいえ | 系の配線。系を呼ぶ進行役 | K | 同じ |
| 260 | `engine/systems/day.py` | runtime | `runtime/systems/day.py` | いいえ | 系の配線。日の境目の系 | K | 同じ |
| 261 | `engine/systems/decide.py` | runtime | `runtime/systems/decide.py` | いいえ | 系の配線。判断の系=LLM の呼と会話の番の発話 | K | 同じ |
| 262 | `engine/systems/guard.py` | foundation | `foundation/write_guard.py` | いいえ | 系の書きの許可(出来事の記録も心の器も読む)。runtime に置くと下の層が上を読む | K | 同じ |
| 263 | `engine/systems/judge.py` | runtime | `runtime/systems/judge.py` | いいえ | 系の配線。応答の適用・起床の源と絞り込み・アービタの系 | K | 同じ |
| 264 | `engine/systems/llm_io.py` | runtime | `runtime/systems/llm_io.py` | いいえ | 系の配線。LLM の往復の口と系 llm_receive | K | 同じ |
| 265 | `engine/systems/observe.py` | runtime | `runtime/systems/observe.py` | いいえ | 系の配線。計器の系 observe と checkpoint | K | 同じ |
| 266 | `engine/systems/overrides.py` | validation | `validation/static/system_overrides.py` | いいえ | 負の対照の差し替え(試験だけ) | K | (ii) |
| 267 | `engine/systems/perceive.py` | runtime | `runtime/systems/perceive.py` | いいえ | 系の配線。知覚の系 | K | 同じ |
| 268 | `engine/systems/probe.py` | runtime | `runtime/systems/probe.py` | いいえ | 系の配線。系ごとの全欄の差と指紋 | K | 同じ |
| 269 | `engine/systems/remember.py` | runtime | `runtime/systems/remember.py` | いいえ | 系の配線。記憶の系 | K | 同じ |
| 270 | `engine/systems/report.py` | runtime | `runtime/systems/report.py` | いいえ | 系の配線。ランの結果の組み立て R3 | K | 同じ |
| 271 | `engine/systems/run_end.py` | runtime | `runtime/systems/run_end.py` | いいえ | 系の配線。ランの終わりの系 | K | 同じ |
| 272 | `engine/systems/spec.py` | runtime | `runtime/systems/spec.py` | いいえ | 系の配線。系の宣言の口 | K | 同じ |
| 273 | `engine/systems/state_io.py` | runtime | `runtime/systems/state_io.py` | いいえ | 系の配線。箱から状態台帳の持ち主・知覚 SoA・ハッシュの材料を組む | K | 同じ |
| 274 | `engine/systems/static_check.py` | validation | `validation/static/system_static_check.py` | いいえ | 宣言とコードの突き合わせ(試験だけ) | K | 同じ |
| 275 | `engine/systems/table.py` | runtime | `runtime/systems/table.py` | いいえ | 系の配線。系の宣言の表 SYSTEMS(呼ぶ順の 1 つの表) | K | 同じ |
| 276 | `engine/systems/talk.py` | runtime | `runtime/systems/talk.py` | いいえ | 系の配線。会話の系 | K | 同じ |
| 277 | `engine/systems/world.py` | runtime | `runtime/systems/world.py` | いいえ | 系の配線。世界の系=世界過程 18 本を runner.step で回す | K | 同じ |
| 278 | `engine/tape.py` | runtime | `runtime/inference/tape.py` | いいえ | 録画と再生。LLM 録画テープ(1 呼 1 行 Parquet)と完全一致の再生 | K | 同じ |
| 279 | `engine/tools/__init__.py` | society | `society/tools/__init__.py`(空にする) | いいえ | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む)。古い頭は、古い包みに割るファイルが残る間は空のまま残し、最後の割りの段で消す | K | 同じ |
| 280 | `engine/tools/contacts.py` | foundation | `foundation/vocab/contact_flags.py` | いいえ | 連絡先の手段の印の語彙。何も読まない | K | (ii) |
| 281 | `engine/tools/groups.py` | society | `society/tools/groups.py` | いいえ | グループの一覧(客観の事実の器) | K | 同じ |
| 282 | `engine/tools/places.py` | society | `society/tools/places.py` | いいえ | 店の番号の表。店の番号の場所の表 | K | 同じ |
| 283 | `engine/tools/record.py` | society | `society/tools/record.py` 88・`foundation/vocab/events.py` 3 | 割る(§4-16) | 道具の記録。語の定数だけ割る | K | 同じ |
| 284 | `engine/tools/registry.py` | society | `society/tools/registry.py` 271・`foundation/vocab/events.py` 1 | 割る(§4-17) | 道具の台帳。語の定数だけ割る | K | 同じ |
| 285 | `engine/wom.py` | mind | `mind/memory/wom.py` | いいえ | 口コミの聞き取り。会話からの店の抽出=口コミの書き手 | K | 同じ |
| 286 | `llm/__init__.py` | foundation | `foundation/ports/inference.py` 116 | 割る(§4-18) | 型は口へ。再輸出は消す | K | (ii) |
| 287 | `llm/contract.py` | foundation | `foundation/vocab/actions.py` | いいえ | 行動の語彙の表。心・差分の器・出来事の全部が読む語彙で、ほかを読まない | K | 同じ |
| 288 | `llm/fleet.py` | runtime | `runtime/inference/fleet.py` 1473・`foundation/ports/inference.py` 215 | 割る(§4-19) | 型と艦隊のクライアント。型だけ割る | K | 同じ |
| 289 | `llm/mock.py` | runtime | `runtime/inference/mock.py` 263・`foundation/vocab/actions.py` 1 | 割る(§4-20) | mock のクライアント。定数だけ割る | K | 同じ |
| 290 | `llm/parser.py` | act | `act/intake/parser.py` | いいえ | 本人の言葉を行為の型へ読む(器の入口) | K | (ii) |
| 291 | `llm/undefined.py` | act | `act/intake/undefined.py` 636・`foundation/vocab/act_codes.py` 3 | 割る(§4-21) | 語彙の外の行為の受け口。語の表だけ割る | K | 同じ |
| 292 | `manifest/__init__.py` | foundation | `foundation/manifest/__init__.py`(空にする) | いいえ | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | K | 同じ |
| 293 | `manifest/canonical.py` | foundation | `foundation/manifest/canonical.py` | いいえ | manifest の正規化 | K | 同じ |
| 294 | `manifest/frozen/world_catalog_v0_2.json` | world | `world/ledger/frozen/world_catalog_v0_2.json` | いいえ | 世界カタログの凍結。読み口と一緒に動かす(pyproject の package-data も直す) | K | 同じ |
| 295 | `manifest/schema.py` | foundation | `foundation/manifest/schema.py` | いいえ | manifest の型。U8 run manifest の 13 節の型 | K | 同じ |
| 296 | `manifest/world_catalog.py` | world | `world/ledger/world_catalog.py` | いいえ | 世界カタログの読み口。世界側台帳だけが読む。`importlib.resources` の包みの名 `shibuya.manifest` を JSON と一緒に直す | K | 同じ |
| 297 | `perception/__init__.py` | mind | `mind/percept/__init__.py`(空にする) | いいえ | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む)。古い頭は、古い包みに割るファイルが残る間は空のまま残し、最後の割りの段で消す | K | 同じ |
| 298 | `perception/attention.py` | foundation | `foundation/text/salience.py` 182・`mind/percept/attention.py` 45 | 割る(§4-22) | 気づきのゲートと文の道具が 1 つ。割る | K | (i) |
| 299 | `perception/channels.py` | foundation | `foundation/text/channels.py` | いいえ | 文の予算とトークンの見積り=状態を持たない道具。build も読む | K | (ii) |
| 300 | `perception/contact_view.py` | foundation | `foundation/ports/percept_contact.py` | いいえ | 連絡の知覚の事実の型(描き方の関数を含む)。何も読まない | K | (ii) |
| 301 | `perception/facts.py` | foundation | `foundation/ports/percept.py` | いいえ | 知覚の口の型=世界と心の境目。標準ライブラリだけ | K | 同じ |
| 302 | `perception/hashes.py` | foundation | `foundation/text/hashes.py` | いいえ | 文と欄のハッシュ=状態を持たない道具 | K | (ii) |
| 303 | `perception/normalize.py` | foundation | `foundation/text/normalize.py` | いいえ | 文の正規化=状態を持たない文字列の道具。build と act も読む | K | (ii) |
| 304 | `perception/p_notice.py` | world | `world/model/notice_reach.py` | いいえ | 顕著な行為が届いたか=世界の物理の側(9-3c で作り直す)。問い 6 の決着=移す段は案 K の置き場。9-3c の式を作り直すときに、届いたかは世界・振り分けは心に割る | K | (iii) 問い 6 |
| 305 | `perception/renderer.py` | mind | `mind/percept/draw.py` 1400・`world/model/percept_scene.py` 1137・`foundation/text/percept_words.py` 93・`mind/percept/notice.py` 74・`runtime/inference/bridge.py` 39・`foundation/time_consts.py` 1・`foundation/vocab/agent_codes.py` 1 | 割る(§4-23) | 世界の段と心の段が 1 つ。割る | K | 同じ |
| 306 | `perception/state.py` | world | `world/model/percept_state.py` | いいえ | 向きなどの派生の列。読み手は顕著な出来事の過程 | K | (ii) |
| 307 | `perception/templates.py` | foundation | `foundation/text/templates.py` | いいえ | 凍結の文の雛形=何も読まない定数。心と runtime が読む | K | (ii) |
| 308 | `world/__init__.py` | world | `world/__init__.py`(空にする) | いいえ | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | K | 同じ |
| 309 | `world/assets.py` | world | `world/model/assets.py` 1286・`foundation/vocab/place_words.py` 1 | 割る(§4-24) | 世界の資産の読み。語彙の定数だけ割る | K | 同じ |
| 310 | `world/graph.py` | world | `world/model/graph.py` | いいえ | 世界の客観の状態と資産。歩行グラフと next-hop 経路 | K | 同じ |
| 311 | `world/navmesh.py` | world | `world/model/navmesh.py` | いいえ | 世界の客観の状態と資産。ナビメッシュの資産と問い合わせ | K | 同じ |
| 312 | `world/navmesh_route.py` | world | `world/model/navmesh_route.py` | いいえ | 世界の客観の状態と資産。ナビメッシュの上の経路(W1 の通り道→帯の A*→funnel) | K | 同じ |
| 313 | `world/processes/__init__.py` | world | `world/ledger/__init__.py`(空にする) | いいえ | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | K | 同じ |
| 314 | `world/processes/absent.py` | world | `world/ledger/absent.py` | いいえ | 世界過程の宣言と記録の台帳。「無いと宣言」する過程と判断の一覧 | K | 同じ |
| 315 | `world/processes/actual_log.py` | world | `world/ledger/actual_log.py` | いいえ | 世界過程の宣言と記録の台帳。追記専用 ActualLog | K | 同じ |
| 316 | `world/processes/circularity.py` | validation | `validation/static/circularity.py` | いいえ | 循環の検査(試験だけ)。循環(同じ値の系で動かして採点する)の機械検査 | K | 同じ |
| 317 | `world/processes/constitution.py` | world | `world/ledger/constitution.py` | いいえ | 憲法 5 の定数と検査。台帳の組み立てが読むので world に残す | K | (ii) |
| 318 | `world/processes/deletion_candidates.py` | validation | `validation/static/deletion_candidates.py` | いいえ | 削除候補の追記(試験だけ) | K | (ii) |
| 319 | `world/processes/first_batch.py` | world | `world/ledger/first_batch.py` | いいえ | 世界過程の宣言と記録の台帳。第 1 陣の世界過程の宣言(データだけ) | K | 同じ |
| 320 | `world/processes/inputs.py` | world | `world/ledger/inputs.py` | いいえ | 世界過程の宣言と記録の台帳。世界過程の入力の宣言の一覧 | K | 同じ |
| 321 | `world/processes/records.py` | world | `world/ledger/records.py` | いいえ | 世界過程の宣言と記録の台帳。世界側台帳のレコード型 3 つ | K | 同じ |
| 322 | `world/processes/registry.py` | world | `world/ledger/registry.py` | いいえ | 世界過程の宣言と記録の台帳。世界側台帳(名前空間・ID は 1 つ) | K | 同じ |
| 323 | `world/processes/relations.py` | world | `world/ledger/relations.py` | いいえ | 世界過程の宣言と記録の台帳。世界側台帳の関係 4 本 | K | 同じ |
| 324 | `world/state.py` | world | `world/model/state.py` | いいえ | 世界の客観の状態と資産。セルと POI の状態 SoA と世界オブジェクト | K | 同じ |

## 4. 割るファイルの割り先(関数の単位)

- 記号の割り先は案 K の作業の表(関数・クラス・定数ごと)を引き、置き場の名を最終の表に合わせて直しました。`engine/calendar_shadow.py` の割りと `apply_detection` の行き先だけはこの役が決めました。
- モジュールの頭の文(import・`__all__`・最上位の `if` など)は、各ファイルの最初の割り先へ行きます。
- 辺の数・循環・原則に反する辺のうち、この割り先が要るものは割る段で数えます(本文 §6)。

### 4-1 `agents/state.py`

| 割り先 | 行数 | クラス | 関数・メソッド | 定数 |
|---|---:|---|---|---|
| `world/model/agent_table.py` | 447 | `AgentState` | `AgentState.__init__`、`AgentState.__getattr__`、`AgentState.__len__`、`AgentState.frozen`、`AgentState.freeze`、`AgentState.thaw`、`AgentState.writable`、`AgentState.state_hash`、`AgentState.bytes_total`、`AgentState.budget_report`、`AgentState.declared_bytes_per_agent` | `LAST_ACTION_NONE` |
| `foundation/vocab/agent_codes.py` | 234 | `AgentKind`、`Activity`、`ResultCode`、`WakeCondition`、`ActivityKind`、`IntentKind` | `focus_code_for_person`、`focus_code_for_poi`、`focus_is_person`、`focus_is_poi`、`focus_poi_of` | `FOCUS_NONE`、`MOCK_KIND_COUNT`、`RESULT_TEXT`、`N_WAKE_CONDITIONS`、`N_WAKE_CONDITIONS_ALL`、`REFRACTORY_MINUTES`、`WAKE_CONDITION_CLASS`、`ACTIVITY_UNTIL_NONE`、`INTENT_NONE`、`FAMILIARITY_FIELDS`、`FAMILIARITY_EMPTY`、`MEMORY_FIELDS` ほか 7 個 |

### 4-2 `cli.py`

| 割り先 | 行数 | クラス | 関数・メソッド | 定数 |
|---|---:|---|---|---|
| `interfaces/cli/main.py` | 1568 | なし | `parse_refractory_scale`、`write_census_files`、`fleet_queue_note`、`apply_fleet_queue_default`、`run`、`_batch_widths`、`_experiment_form`、`checkpoints_payload`、`undefined_registry_payload`、`_engine_run_day`、`arm_baseline`、`_arm_norm`、`run_arms`、`main` | `CLI_DEFAULT_VOCAB_VERSION`、`CLI_DEFAULT_L4_SCALE`、`CLI_DEFAULT_HUNGER_MODEL`、`STORE_ENTRY_CAPITAL_YEN`、`DAILY_CENSUS_FILENAME`、`MONTHLY_MER_FILENAME`、`MONTHLY_MER_SECTORS_FILENAME`、`UNDEFINED_PAYLOAD_SCHEMA`、`NON_ARM_RUN_KWARGS` |
| `interfaces/cli/wire_economy.py` | 134 | `_HouseholdWalletLedger` | `store_capital_array`、`store_capital_report`、`household_wallets`、`build_ledger_bundle`、`_HouseholdWalletLedger.__init__`、`_HouseholdWalletLedger.endow_households` | `WALLET_DOMAIN` |

### 4-3 `engine/arbiter.py`

| 割り先 | 行数 | クラス | 関数・メソッド | 定数 |
|---|---:|---|---|---|
| `runtime/arbiter.py` | 457 | `ArbiterDecision`、`Arbiter` | `call_budget_per_tick`、`_class_slot`、`arbitrate`、`ArbiterDecision.__post_init__`、`ArbiterDecision.n_calls`、`ArbiterDecision.n_sleep_suppressed`、`ArbiterDecision.n_outside_suppressed`、`ArbiterDecision.counters`、`Arbiter.__init__`、`Arbiter.pending`、`Arbiter.n_pending`、`Arbiter._store`、`Arbiter.step`、`Arbiter.counters`、`Arbiter.totals`、`Arbiter.merged_total`、`Arbiter.sleep_suppressed_total`、`Arbiter.sleep_suppressed_counters`、`Arbiter.outside_suppressed_total`、`Arbiter.outside_suppressed_counters` | `T_MAX_TICKS`、`DEGRADE_COST_FACTOR`、`DEGRADE_CLASSES`、`POOL_CAP_TICKS`、`L4_CALLS_PER_DAY`、`L4_REFERENCE_AGENTS`、`L4_LINE_PER_AGENT_DAY`、`_TICKS_PER_DAY`、`REFRACTORY_TICKS` |
| `mind/system1/wake.py` | 63 | `WakeCandidates` | `WakeCandidates.__post_init__`、`WakeCandidates.__len__`、`WakeCandidates.empty`、`WakeCandidates.concat`、`WakeCandidates.take` | なし |

### 4-4 `engine/calendar.py`

| 割り先 | 行数 | クラス | 関数・メソッド | 定数 |
|---|---:|---|---|---|
| `world/facts/calendar.py` | 386 | `CalendarWarning`、`HolidayTable`、`SimCalendar` | `_parse_ymd`、`resolve_repo_path`、`load_holidays`、`parse_start`、`parse_school_holidays`、`holidays_between`、`HolidayTable.covers`、`SimCalendar.__post_init__`、`SimCalendar.default`、`SimCalendar.with_start`、`SimCalendar.ticks_per_day`、`SimCalendar.day_of`、`SimCalendar.tick_of_day`、`SimCalendar.to_T`、`SimCalendar.datetime_of`、`SimCalendar.date_of_day`、`SimCalendar.weekday`、`SimCalendar.is_holiday`、`SimCalendar.holiday_name`、`SimCalendar.set_holiday`、`SimCalendar.is_rest_day`、`SimCalendar.table_weekday`、`SimCalendar.opening_row`、`SimCalendar.day_kind`、`SimCalendar.season`、`SimCalendar.is_business_day`、`SimCalendar.is_payday`、`SimCalendar._payday_target`、`SimCalendar.day_index_of`、`SimCalendar.day_key`、`SimCalendar.in_school_holiday`、`SimCalendar.start_problems`、`SimCalendar.check_start`、`SimCalendar.manifest_fields` | `DEFAULT_HOLIDAY_CSV`、`HOLIDAY_CSV_COLUMNS`、`DEFAULT_WORLD_START`、`WEEKDAY_MODE`、`WEATHER_SCHEME`、`OPENING_ROW_PH`、`SEASON_OF_MONTH`、`_DAY_KIND_OF_WEEKDAY`、`HOLIDAY_TABLE_WEEKDAY`、`_WARNED_MISSING`、`REPO_ROOT` |
| `foundation/types.py` | 9 | なし | `ticks_per_day` | なし |

### 4-5 `engine/calendar_shadow.py`

| 割り先 | 行数 | クラス | 関数・メソッド | 定数 |
|---|---:|---|---|---|
| `society/calendar_shadow.py` | 197 | `CalendarShadow` | `arm`、`set_arm`、`is_on`、`_hist15`、`_stats`、`_active15`、`_w17_work_span`、`manifest_fields`、`build`、`CalendarShadow.__init__`、`CalendarShadow.__setattr__`、`CalendarShadow.__delattr__`、`CalendarShadow.relay_day`、`CalendarShadow.manifest` | `MODE_W17`、`MODE_1A`、`MODES`、`DEFAULT_MODE`、`SCHEMA`、`SLOT_MIN`、`N_SLOTS`、`W17_WORK_CODE`、`MANIFEST_CONFIG`、`MANIFEST_OBSERVED`、`_ARM` |
| `world/facts/w20_calendar_reader.py` | 115 | `CalendarTable` | `resolve_path`、`_readonly`、`_freeze`、`_thaw`、`_sha256`、`load_table`、`CalendarTable.__post_init__` | `FILE_NAME`、`STAGE_DIR`、`HEADER_NAME`、`WEEK0_MONDAY`、`N_DAYS`、`COMMIT_WORK`、`COMMIT_SCHOOL`、`_COLS` |

### 4-6 `engine/change_detect.py`

| 割り先 | 行数 | クラス | 関数・メソッド | 定数 |
|---|---:|---|---|---|
| `mind/system1/change_detect.py` | 290 | `B5Crossing`、`DetectResult`、`ChangeDetector` | `_cell_wake_numpy`、`_make_cell_wake`、`DetectResult.b5_wake_agents`、`DetectResult.candidates`、`ChangeDetector.__init__`、`ChangeDetector._cell_changes`、`ChangeDetector._interoception`、`ChangeDetector._interoception_scoped`、`ChangeDetector.detect` | `INTERO_HYSTERESIS`、`B4_FIELD_COLUMNS`、`_CELL_WAKE` |
| `world/model/scene_hash.py` | 63 | なし | `b4_block_raw`、`b4_block_hashes` | `DEFAULT_WALKABLE_AREA_M2` |
| `foundation/vocab/agent_codes.py` | 6 | なし | なし | `INTERO_UP_EDGES`、`INTERO_VARS` |

### 4-7 `engine/chooser.py`

| 割り先 | 行数 | クラス | 関数・メソッド | 定数 |
|---|---:|---|---|---|
| `mind/judge/chooser.py` | 153 | `NearestChooser`、`ClassicalChooser` | `hunger_stage_of`、`check_chooser`、`make_chooser`、`NearestChooser.probs`、`ClassicalChooser.__init__`、`ClassicalChooser._count`、`ClassicalChooser.probs` | `CHOOSER_NAMES`、`HABIT_P`、`RANK_TAU`、`_INTERO_UP_EDGES`、`DEFAULT_CHOOSER` |
| `foundation/ports/choice.py` | 69 | `ChoiceContext`、`Chooser` | `draw_index`、`entropy_bits`、`Chooser.probs` | `CHOOSER_RNG_DOMAIN` |

### 4-8 `engine/commit.py`

| 割り先 | 行数 | クラス | 関数・メソッド | 定数 |
|---|---:|---|---|---|
| `act/intake/from_words.py` | 542 | なし | `undefined_fallback_code`、`target_hint_code`、`focus_codes`、`parse_action`、`talk_partners`、`_reach_rows`、`_talk_partners_reach`、`pair_partners`、`engine_continuations`、`_poi_in_cell`、`intents_from_responses` | なし |
| `act/commit.py` | 300 | `IntentBatch`、`ResourceSpace`、`CommitPlan` | `delta_perc_ns`、`_concat_s2`、`_rank_within_resource`、`arbitrate_resources`、`tick_start_ns`、`IntentBatch.__post_init__`、`IntentBatch.__len__`、`IntentBatch.empty`、`IntentBatch.concat`、`IntentBatch.take`、`IntentBatch.one_per_agent`、`ResourceSpace.partner_offset`、`ResourceSpace.sleep_offset`、`ResourceSpace.size`、`ResourceSpace.poi`、`ResourceSpace.partner`、`ResourceSpace.sleep`、`ResourceSpace.capacity`、`CommitPlan.n_unresolved` | `_CONDITION_EXPECTATION` |
| `foundation/vocab/act_codes.py` | 34 | なし | なし | `ACTION_WORDS`、`ACTION_CODES`、`ACT_MOVE`、`ACT_BOARD`、`ACT_ALIGHT`、`ACT_BUY`、`ACT_WAIT`、`ACT_TALK`、`ACT_LEAVE`、`ACT_REPORT`、`ACT_HELP`、`ACT_REFUSE` ほか 22 個 |

### 4-9 `engine/events/body.py`

| 割り先 | 行数 | クラス | 関数・メソッド | 定数 |
|---|---:|---|---|---|
| `mind/memory/body_events.py` | 130 | `BodyEventLink` | `BodyEventLink.__init__`、`BodyEventLink.__setattr__`、`BodyEventLink.__delattr__`、`BodyEventLink.enabled`、`BodyEventLink._event`、`BodyEventLink._what`、`BodyEventLink._cause`、`BodyEventLink.write`、`BodyEventLink.conversation_end` | `SRC_ACT`、`SRC_ARRIVE`、`SRC_TALK_OPEN`、`SRC_TURN`、`SRC_NOTICE`、`SRC_SIGNAGE`、`SOURCES`、`ACT_FAMILY_WORDS`、`_TALK_WORDS`、`_P_RESOLVE`、`_P_CONV`、`_VIA_FACE` |
| `foundation/vocab/events.py` | 25 | なし | `kind_of_what` | `KIND_ACT_WORD`、`_KIND_NOTICE`、`_KIND_SIGNAGE`、`_KIND_TALK`、`WHAT_TALK_OPEN`、`WHAT_TALK_END`、`WHAT_NOTICE`、`WHAT_SIGNAGE`、`_WHAT_OF_KIND` |

### 4-10 `engine/llm_bridge.py`

| 割り先 | 行数 | クラス | 関数・メソッド | 定数 |
|---|---:|---|---|---|
| `runtime/inference/bridge.py` | 825 | `StubRenderer`、`PerceptionRendererAdapter`、`BridgeResult`、`CallStart`、`LLMBridge` | `delta_think_ticks`、`_kept_target`、`StubRenderer.__init__`、`StubRenderer.render`、`StubRenderer.prepare_tick`、`PerceptionRendererAdapter.__init__`、`PerceptionRendererAdapter.prepare_tick`、`PerceptionRendererAdapter.b4_field_rows`、`PerceptionRendererAdapter.assets`、`PerceptionRendererAdapter.render`、`PerceptionRendererAdapter.perceive_call`、`PerceptionRendererAdapter.render_call`、`PerceptionRendererAdapter._wrap`、`PerceptionRendererAdapter.counters`、`BridgeResult.format_ok`、`LLMBridge.__init__`、`LLMBridge.attach_role_rights`、`LLMBridge.prepare_tick`、`LLMBridge.call`、`LLMBridge.begin`、`LLMBridge.finish`、`LLMBridge.code_of_word`、`LLMBridge._after_render`、`LLMBridge._append_tape`、`LLMBridge.parse_error_rate`、`LLMBridge.parse_error_rate_strict`、`LLMBridge.tape_miss_rate`、`LLMBridge.counters`、`LLMBridge.close` | `ACTION_WORD_BY_CODE`、`SHARED_BLOCK_IDS`、`ALPHA_THINK_SECONDS_PER_TOKEN`、`LANE_SECONDS`、`LANE_THINK_TOKENS`、`DEFAULT_LANE`、`STUB_SHARED_BLOCK` |
| `foundation/ports/inference.py` | 53 | `RenderedPrompt`、`Renderer` | `RenderedPrompt.block_ids`、`Renderer.render` | なし |

### 4-11 `engine/poi_target.py`

| 割り先 | 行数 | クラス | 関数・メソッド | 定数 |
|---|---:|---|---|---|
| `act/target.py` | 617 | `TargetResolver` | `_norm`、`move_resolution_summary`、`resolution_summary`、`TargetResolver.__post_init__`、`TargetResolver._rich_fields`、`TargetResolver._category_mask`、`TargetResolver._match_name`、`TargetResolver.classify`、`TargetResolver._no_candidate`、`TargetResolver.pois_in_cell`、`TargetResolver._order`、`TargetResolver.resolve`、`TargetResolver._named_elsewhere`、`TargetResolver._category_elsewhere`、`TargetResolver._nearby_pick`、`TargetResolver.cell_of_target`、`TargetResolver._pick`、`TargetResolver.resolve_move`、`TargetResolver._record_dist` | `KIND_NAMED`、`KIND_CATEGORY`、`KIND_NONE`、`NO_CANDIDATE_REASONS`、`MOVE_SEARCH_RADIUS_CELLS`、`MOVE_BAD_TARGET`、`MOVE_DIST_BINS_M`、`_ID_FORM`、`NAME_MIN_CHARS`、`_SUFFIXES` |
| `foundation/vocab/place_words.py` | 74 | なし | なし | `CATEGORY_WORDS`、`GENERIC_WORDS`、`BUYABLE_CATS`、`SYNTHETIC_BUYABLE_CATS` |

### 4-12 `engine/presence.py`

| 割り先 | 行数 | クラス | 関数・メソッド | 定数 |
|---|---:|---|---|---|
| `world/laws/presence.py` | 1511 | `EventType`、`_HomeShim`、`PlanExecutor` | `_HomeShim.__init__`、`PlanExecutor.__init__`、`PlanExecutor._lines_of_direction`、`PlanExecutor.absent_on`、`PlanExecutor._train_mask`、`PlanExecutor.relay_day`、`PlanExecutor.start_day`、`PlanExecutor.initialize_caches`、`PlanExecutor._exit_cells`、`PlanExecutor._assign_trains`、`PlanExecutor._spread_arrivals`、`PlanExecutor._build_events`、`PlanExecutor.initialize`、`PlanExecutor.step`、`PlanExecutor.step_plan_boundaries`、`PlanExecutor._run_tick`、`PlanExecutor._run_type`、`PlanExecutor._do_arrive`、`PlanExecutor._do_depart`、`PlanExecutor._defer`、`PlanExecutor._release_affiliations`、`PlanExecutor._depart_now`、`PlanExecutor._begin_walk`、`PlanExecutor._flush_rewalks`、`PlanExecutor._flush_walkers`、`PlanExecutor.plan_exit_mask`、`PlanExecutor.notify_departed_by_plan`、`PlanExecutor.suppress_walker_wakes`、`PlanExecutor.note_calls`、`PlanExecutor._flush_deferred_exits`、`PlanExecutor.candidates_for_pull`、`PlanExecutor.notify_pulled_in`、`PlanExecutor.notify_pushed_out`、`PlanExecutor.notify_departed_by_llm`、`PlanExecutor._rearm_after_leaving`、`PlanExecutor._earliest_enter_tick`、`PlanExecutor.sample`、`PlanExecutor.plan_stranded_eod`、`PlanExecutor.plan_match_in`、`PlanExecutor.plan_match_out`、`PlanExecutor.day_night_ratio`、`PlanExecutor.counters`、`PlanExecutor.exit_summary`、`PlanExecutor.summary` | `ARRIVAL_SPREAD_MAX_TRAINS`、`EXIT_DEFER_LIMIT`、`RETURN_MIN_AWAY_MIN`、`EXIT_MODES`、`EXIT_WALK_MAX_TICKS`、`SLEEP_ACTIVITY_CODE`、`PLACE_KIND_LODGING`、`DERIVE_RULES`、`DERIVE_RULE_DEFAULT`、`_TYPE_ORDER`、`FLAG_HOME_OUT`、`FLAG_HAS_PLAN` ほか 2 個 |
| `world/laws/presence_plan.py` | 402 | `PlanBlocks` | `_mix64`、`_day_rows`、`_apply_derive_v2`、`_trim_nonstay_edges`、`PlanBlocks.n_blocks`、`PlanBlocks.agent_of_block`、`PlanBlocks.blocks_per_agent`、`PlanBlocks.all_day_outside`、`PlanBlocks.in_area_at`、`PlanBlocks.from_weekly` | `RIDE_ACTIVITY_CODE`、`PLACE_KIND_HOME`、`MOVE_ACTIVITY_CODE`、`PREP_ACTIVITY_CODE`、`ANCHOR_PLACE_KINDS`、`NON_STAY_ACTIVITY_CODES`、`EDGE_TRIM_ACTIVITY_CODES`、`_MAX_RIDE_RUN` |

### 4-13 `engine/relations.py`

| 割り先 | 行数 | クラス | 関数・メソッド | 定数 |
|---|---:|---|---|---|
| `mind/relations/layer.py` | 746 | `RelationLayer` | `_rank_live`、`_layer_weights`、`RelationLayer.__init__`、`RelationLayer.__setattr__`、`RelationLayer.__delattr__`、`RelationLayer.contact_flags`、`RelationLayer.copresent_on`、`RelationLayer.acq_wake_on`、`RelationLayer.seed_initial`、`RelationLayer.on_episodes`、`RelationLayer._write_round`、`RelationLayer._reset_slots`、`RelationLayer._write_contacts`、`RelationLayer.contact_tally`、`RelationLayer.rebuild_contacts`、`RelationLayer._partner_rows`、`RelationLayer.activation`、`RelationLayer.strength`、`RelationLayer.edges`、`RelationLayer.acquaintances`、`RelationLayer.partners_in_cell`、`RelationLayer.weights_for_invite`、`RelationLayer.enable_invite`、`RelationLayer.choose_talk_partners`、`RelationLayer.pick_rest`、`RelationLayer.pop_origin`、`RelationLayer._same_cell_hits`、`RelationLayer._edges`、`RelationLayer._edge_view`、`RelationLayer.aware_of`、`RelationLayer.enable_copresent`、`RelationLayer.copresent_step`、`RelationLayer.enable_acquaintance_wake`、`RelationLayer.acquaintance_candidates`、`RelationLayer._acq_notice`、`RelationLayer._acq_finish`、`RelationLayer.stamp_acquaintance`、`RelationLayer.lifetime_days`、`RelationLayer.summary` | `REL_INVITE_LAYERS`、`REL_COPRESENT_MINUTES`、`REL_COPRESENT_METERS`、`REL_ACQ_PAIR_REFRACTORY_MIN`、`_ACQ`、`_TALK`、`_REST_SHARE`、`_HELP`、`_SIGN_LABEL`、`_CONTACT_GUARDED`、`_SIGN_OF_RESULT` |
| `world/facts/initial_ties.py` | 326 | なし | `slot_cells`、`copresence`、`copresence_days`、`_last_copresence`、`_last_copresence_many`、`_pair_mix`、`_weekly64`、`check_rel_tenure_hash`、`_splitmix64`、`_tenure_unit`、`_tenure_weeks`、`initial_edges`、`tau_from_edges` | `REL_TENURE_HASHES`、`_TENURE_SALT_V2`、`REL_SLOT_MIN`、`HOUSEHOLD_MIN_DAYS_PER_WEEK`、`REL_DAYS_PER_WEEK`、`_SLOTS_PER_DAY`、`_SLOTS`、`_LAST_CHUNK` |
| `foundation/vocab/relations.py` | 42 | `RelationEdges`、`InitialEdges` | `_activation` | `REL_K`、`REL_MODES`、`REL_KINDS`、`REL_KIND_NAMES`、`REL_D`、`REL_TAU_V1`、`REL_TAU_V2`、`REL_TAU_BY_TENURE_HASH`、`REL_TAU`、`REL_S`、`REL_TENURE_WEEKS`、`DEFAULT_REL_TENURE_HASH` ほか 5 個 |

### 4-14 `engine/resolve.py`

| 割り先 | 行数 | クラス | 関数・メソッド | 定数 |
|---|---:|---|---|---|
| `act/apply.py` | 454 | なし | `apply`、`_apply_record_only`、`_apply_report`、`_apply_help`、`_apply_rest`、`_apply_sleep` | `REST_FATIGUE_RELIEF`、`EAT_DWELL_MINUTES`、`REPORT_WINDOW_TICKS`、`_BOARD_KEEP_ACTIONS`、`_SLEEP_KEEP_ACTIONS`、`_UNADDRESSABLE`、`_APPLY`、`_APPLY_V2`、`_APPLY_V3`、`_APPLY_BY_VOCAB`、`_ACTION_ORDER_V1`、`_ACTION_ORDER_V3` ほか 1 個 |
| `act/ops/shop.py` | 454 | なし | `_stage2_money`、`_payable`、`_stage2_note_calls`、`_stage2_withdraw`、`_apply_buy`、`_complete_buy`、`_apply_eat`、`_purchase_tax`、`_complete_eat`、`_apply_queue`、`_apply_wait`、`release_indoor`、`_remember_queue_action`、`_serve_poi_queue`、`balk_queue` | `BUY_HUNGER_RELIEF`、`EAT_HUNGER_RELIEF`、`_SELL_SLOT_RETRIES`、`_QUEUE_FOR_BUY`、`_QUEUE_FOR_EAT` |
| `act/ops/rail.py` | 379 | なし | `_platform_table`、`_enter_board_queue`、`_apply_board`、`_serve_board_queue`、`_plan_exit_mask`、`_board_riders`、`_apply_alight`、`place_at_external`、`rail_arrive`、`rail_depart`、`sync_transit_activity` | `BOARD_WAIT_LIMIT_TICKS` |
| `act/ops/move.py` | 322 | なし | `_is_nav`、`_nav_stop`、`_nav_step`、`_nav_positions`、`nav_place`、`_apply_engine_step`、`_settle_approach`、`_apply_move`、`_approach_dest_node`、`_cell_of_node` | `APPROACH_DONE_M` |
| `act/ops/plan_writes.py` | 309 | なし | `set_plan_state`、`begin_planned_sleep`、`wake_from_plan`、`begin_exit_walk`、`begin_walk_to`、`clear_board_intent` | なし |
| `mind/ops.py` | 208 | なし | `wake_condition_index`、`refractory_ticks`、`normalized_refractory_scale`、`set_refractory`、`clear_refractory`、`write_familiarity`、`write_memory`、`write_store_memory`、`write_relations` | なし |
| `act/ops/law_writes.py` | 197 | なし | `restock`、`discard_to_bin`、`consume`、`collect_waste`、`set_thermal`、`set_notice_state`、`set_open_flags`、`request_open_close` | なし |
| `act/ops/body_writes.py` | 158 | なし | `advance_body`、`initialize_energy`、`_tick_minute`、`_energy_meal`、`_energy_snack`、`energy_out_of_area_meal`、`energy_home_meal` | なし |
| `act/gate.py` | 154 | `ResolveOutcome` | `_ok`、`_fail`、`ResolveOutcome.add_result` | なし |
| `act/ops/talk.py` | 154 | なし | `join_conversation`、`revert_conversation`、`end_conversation`、`set_conversing`、`talk_within_reach`、`_apply_talk`、`_apply_leave` | なし |
| `runtime/state/restore.py` | 136 | なし | `restore_soa`、`_restore_array_into`、`_restore_value`、`restore_items` | なし |
| `act/ops/intent_writes.py` | 115 | なし | `set_activity`、`set_activity_until`、`_clear_intent_fields`、`intent_kept_by`、`set_intent`、`clear_intent`、`fail_intent`、`relabel_intent_failure` | `INTENT_KEEP_ACTIONS` |
| `act/ops/focus.py` | 94 | なし | `_focus_xy`、`_clear_focus`、`_set_focus`、`_advance_focus` | `FOCUS_TTL_TICKS`、`FOCUS_ACQUIRE_M`、`FOCUS_LOSE_M` |
| `act/ops/init_writes.py` | 82 | なし | `initialize`、`set_initial_activity` | なし |
| `foundation/write_guard.py` | 33 | なし | `_require_thawed` | なし |
| `act/ops/detect_writes.py` | 10 | なし | `apply_detection` | なし |
| `foundation/vocab/act_codes.py` | 3 | なし | なし | `TALK_OPEN_METERS`、`TALK_LEAVE_METERS`、`EXIT_WALK_FLAG` |
| `foundation/vocab/agent_codes.py` | 2 | なし | なし | `_REFRACTORY_TICKS`、`_REFRACTORY_TICKS` |

### 4-15 `engine/run.py`

| 割り先 | 行数 | クラス | 関数・メソッド | 定数 |
|---|---:|---|---|---|
| `runtime/result.py` | 1227 | `Checkpoint`、`RunResult` | `decision_layers_summary`、`_action_usage`、`_calls_by_model`、`_calendar2_field`、`_calendar3_field`、`_duties_field`、`_contact_c1_field`、`_tm234_sections`、`Checkpoint.combined`、`RunResult.column`、`RunResult.parse_error_rate`、`RunResult.parse_error_rate_strict`、`RunResult.label_alias_rate`、`RunResult.positional_rate`、`RunResult.dictionary_mapped_rate`、`RunResult.tape_miss_count`、`RunResult.undefined_action_count`、`RunResult.conversation_sessions`、`RunResult.sleep_suppressed_count`、`RunResult.outside_suppressed_count`、`RunResult.calls_by_hour_text`、`RunResult.wake_rate_in_area_by_hour_text`、`RunResult.wake_rate_by_hour_text`、`RunResult.diagnostics_day`、`RunResult.final_hash`、`RunResult._waste_breakdown_text`、`RunResult._waste_band_note`、`RunResult.waste_band_ok`、`RunResult.state_hashes_fields`、`RunResult.run_manifest_fields`、`RunResult.economy_fields`、`RunResult.l4_audit_fields`、`RunResult.conserved`、`RunResult.phase_breakdown`、`RunResult.movement_ms_per_tick`、`RunResult.movement_cpu_ms_per_tick`、`RunResult.movement_gil_wait_ratio`、`RunResult.summary` | `ENGINE_STEP_LABEL`、`DECISION_LAYERS`、`L4_CONVERSATION_SHARE_LINE` |
| `runtime/run.py` | 987 | `_RunDayLocals` | `_resolve_response_delay`、`_replay_tape_dir`、`check_replay_tape`、`_count_intero_crossings`、`_named_closed_lookup`、`_default_mock`、`_synonym_table_version`、`resolve_sub_seed`、`resolve_population_seed`、`resolve_environment_seed`、`_same_seed`、`run_salt_for`、`_resolve_population`、`_population_fits`、`_check_population_fits`、`_schedule_with_population`、`_settle_pending_invites`、`_inviter_of`、`_target_person`、`_target_poi`、`_pending_extra`、`_call_ref`、`_split_due`、`classical_acq_addressable`、`run_day` | `DELTA_THINK_TICKS`、`TIME_BUCKET_TICKS`、`DIAG_RUN_COLUMNS`、`DIAG_DAY_ROWS`、`_ENTRANCES`、`_ENTRANCE_PLAN`、`_ENTRANCE_EXPIRY`、`_ENTRANCE_OF_CONDITION`、`RESPONSE_DELAYS`、`DEFAULT_RESPONSE_DELAY`、`RNG_LAYOUT`、`POPULATION_RNG_DOMAINS` ほか 3 個 |
| `interfaces/cli/run_args.py` | 193 | なし | `add_fleet_args`、`add_calendar_args`、`calendar_kwargs_from_args`、`fleet_from_args`、`main` | なし |

### 4-16 `engine/tools/record.py`

| 割り先 | 行数 | クラス | 関数・メソッド | 定数 |
|---|---:|---|---|---|
| `society/tools/record.py` | 88 | `SignboardReadLink`、`ToolsFixture` | `arm_from_env`、`enabled`、`set_enabled`、`build_fixture`、`_signboard_reads`、`manifest_fields`、`SignboardReadLink.__init__`、`SignboardReadLink.__call__` | `MANIFEST_SCHEMA`、`ARM_ENV`、`_ENABLED` |
| `foundation/vocab/events.py` | 3 | なし | なし | `SIGNBOARD_ORIGIN`、`SIGNBOARD_WHAT`、`SIGNBOARD_CAUSE` |

### 4-17 `engine/tools/registry.py`

| 割り先 | 行数 | クラス | 関数・メソッド | 定数 |
|---|---:|---|---|---|
| `society/tools/registry.py` | 271 | `KnownBy`、`Tool`、`ToolRegistry` | `_is_int`、`_closed`、`affordance_words`、`default_registry`、`KnownBy.__post_init__`、`KnownBy.of`、`KnownBy.knows`、`KnownBy.describe`、`Tool.__post_init__`、`Tool.as_dict`、`ToolRegistry.__init__`、`ToolRegistry.__setattr__`、`ToolRegistry.__delattr__`、`ToolRegistry.register`、`ToolRegistry.get`、`ToolRegistry.known`、`ToolRegistry.rows`、`ToolRegistry.names`、`ToolRegistry.__len__`、`ToolRegistry.__iter__`、`ToolRegistry.__contains__`、`ToolRegistry.in_use`、`ToolRegistry.registered_only`、`ToolRegistry.usable` | `NOTICE`、`PHONE`、`CONTACTS`、`GROUP`、`TRANSIT`、`MAP`、`CLOCK`、`FORECAST`、`TOOL_NAMES`、`REQUIRE_KINDS`、`OWNERS`、`CONTENT_WRITERS` ほか 14 個 |
| `foundation/vocab/events.py` | 1 | なし | なし | `SIGNBOARD` |

### 4-18 `llm/__init__.py`

| 割り先 | 行数 | クラス | 関数・メソッド | 定数 |
|---|---:|---|---|---|
| `foundation/ports/inference.py` | 116 | `LLMRequest`、`LLMResponse`、`LLMClient`、`TapeLookup` | `estimate_tokens`、`LLMRequest.prompt_hash`、`LLMRequest.params_hash`、`LLMClient.complete`、`TapeLookup.lookup` | なし |

### 4-19 `llm/fleet.py`

| 割り先 | 行数 | クラス | 関数・メソッド | 定数 |
|---|---:|---|---|---|
| `runtime/inference/fleet.py` | 1473 | `FleetConfig`、`TapeSink`、`FleetTapeRow`、`_Latency`、`_RetryableHTTP`、`_FatalHTTP`、`_Replica`、`FleetClient`、`FleetBridgeResult`、`FleetBridge` | `l6_in_flight_per_gpu`、`l4_calls_per_day`、`plan_batch`、`fleet_auth_headers`、`_classify`、`_debug_reason`、`_format_ok`、`_raise_for_status`、`_next_data`、`_read_chunk`、`call_from_request`、`FleetConfig.__post_init__`、`FleetConfig.n_replicas`、`FleetConfig.resolved_cache_salt`、`FleetConfig.resolved_per_replica`、`FleetConfig.resolved_max_in_flight`、`FleetConfig.resolved_queue_capacity`、`FleetConfig.manifest_fields`、`TapeSink.intern_block`、`TapeSink.append`、`_Latency.__init__`、`_Latency.add`、`_Latency.quantile`、`_Latency.__len__`、`_Replica.__init__`、`FleetClient.__init__`、`FleetClient.start`、`FleetClient._call_soon_sync`、`FleetClient._setup_clients`、`FleetClient.close`、`FleetClient._close_clients`、`FleetClient.__enter__`、`FleetClient.__exit__`、`FleetClient.discover_model`、`FleetClient._discover_model`、`FleetClient.submit`、`FleetClient.poll`、`FleetClient.drain`、`FleetClient.wait_idle`、`FleetClient.outstanding`、`FleetClient.in_flight`、`FleetClient._finish`、`FleetClient._move_replica`、`FleetClient._payload`、`FleetClient._run_call`、`FleetClient._attempt`、`FleetClient._attempt_once`、`FleetClient._attempt_stream`、`FleetClient.complete`、`FleetClient.counters`、`FleetBridgeResult.format_ok`、`FleetBridgeResult.deferred`、`FleetBridge.__init__`、`FleetBridge.submit`、`FleetBridge.poll`、`FleetBridge.drain`、`FleetBridge.submit_and_drain`、`FleetBridge._interpret`、`FleetBridge._record_debug`、`FleetBridge._intern_blocks`、`FleetBridge._record_tape`、`FleetBridge._tape_v4`、`FleetBridge._record_deferred`、`FleetBridge.parse_error_rate`、`FleetBridge.parse_error_rate_strict`、`FleetBridge.counters`、`FleetBridge.close` | `LANE_TIER`、`DEFAULT_TTFT_TIMEOUT_S`、`DEFAULT_E2E_TIMEOUT_S`、`DEFAULT_IMBALANCE_THRESHOLD`、`DEBUG_FILENAME`、`DEFAULT_DEBUG_MAX_ROWS`、`_L6_RE`、`_L4_RE`、`_MULT`、`DEFERRED_OUTCOMES`、`FLEET_API_KEY_ENV`、`_RETRYABLE_EXC` |
| `foundation/ports/inference.py` | 215 | `Outcome`、`LLMCall`、`LLMResult`、`Deferred`、`FleetDeferredError` | `max_tokens_for`、`cache_salt_for`、`seed_for`、`route_primary`、`split_system_user`、`LLMCall.block_ids`、`LLMCall.user_text`、`LLMCall.group_key`、`LLMCall.wake_since`、`LLMResult.call_id`、`LLMResult.source`、`LLMResult.deferred`、`Deferred.call_id`、`Deferred.deferred`、`FleetDeferredError.__init__` | `LANE_THINK_TOKENS`、`INFRA_CLIP_FACTOR`、`INFRA_CLIP_SLACK`、`DEFAULT_TEMPERATURE`、`DEFAULT_T1_MAX_TOKENS`、`CACHE_SALT_DOMAIN`、`_SEP` |

### 4-20 `llm/mock.py`

| 割り先 | 行数 | クラス | 関数・メソッド | 定数 |
|---|---:|---|---|---|
| `runtime/inference/mock.py` | 263 | `MockLLM`、`TapeLLM` | `MockLLM.__init__`、`MockLLM._stream`、`MockLLM._draws`、`MockLLM._render_v3`、`MockLLM._move_target`、`MockLLM._shop_target`、`MockLLM.render`、`MockLLM.action_draw`、`MockLLM.complete`、`MockLLM.acomplete`、`TapeLLM.__init__`、`TapeLLM.complete`、`TapeLLM.acomplete`、`TapeLLM.__getattr__` | `MOCK_RNG_DOMAIN`、`MOCK_REASONS`、`MOCK_COMMENTS`、`MOCK_FORMS`、`MOCK_ACTIVITIES_V3`、`MOCK_UNTILS_V3`、`MOCK_UNTILS_V3_MOVE`、`MOCK_WANDER_ONE_IN`、`_MOVE_WORD`、`MOCK_MOVE_TARGET_WORDS`、`_MOVE_TARGET_DOMAIN_SUFFIX`、`_VISIBLE_PREFIX` ほか 3 個 |
| `foundation/vocab/actions.py` | 1 | なし | なし | `MOCK_UTTERANCE` |

### 4-21 `llm/undefined.py`

| 割り先 | 行数 | クラス | 関数・メソッド | 定数 |
|---|---:|---|---|---|
| `act/intake/undefined.py` | 636 | `ProposalStatus`、`UndefinedActionRecord`、`Proposal`、`UndefinedOutcome`、`UndefinedActionRegistry` | `synonym_table`、`synonym_table_version`、`target_hints`、`target_surface_hint`、`fallback_actions`、`undefined_feedback`、`map_synonym`、`Proposal.needs_parent_review`、`UndefinedOutcome.mapped`、`UndefinedOutcome.action_from_dictionary`、`UndefinedActionRegistry.__init__`、`UndefinedActionRegistry.observe`、`UndefinedActionRegistry.distinct_agents`、`UndefinedActionRegistry._maybe_adjudicate`、`UndefinedActionRegistry.adjudicate`、`UndefinedActionRegistry.adopt`、`UndefinedActionRegistry.reject`、`UndefinedActionRegistry.counters`、`UndefinedActionRegistry.top_words` | `SYNONYM_TABLE_VERSION`、`_SYNONYMS_V0`、`SYNONYMS_C6`、`SYNONYMS`、`SYNONYMS_V3_DIFF`、`SYNONYMS_V3`、`SYNONYM_TABLE_VERSION_V3`、`SYNONYMS_V4_DIFF`、`SYNONYMS_V4`、`SYNONYM_TABLE_VERSION_V4`、`SYNONYMS_V5_DIFF`、`SYNONYMS_V5` ほか 14 個 |
| `foundation/vocab/act_codes.py` | 3 | なし | なし | `TARGET_HINT_WORDS` |

### 4-22 `perception/attention.py`

| 割り先 | 行数 | クラス | 関数・メソッド | 定数 |
|---|---:|---|---|---|
| `foundation/text/salience.py` | 182 | `SalientItem`、`StripReport` | `rank_by_saliency`、`apply_budget`、`content_cap_chars`、`strip_imperatives`、`feature_tag`、`tag_world_text`、`StripReport.n_removed` | `BUDGET_ADS`、`BUDGET_SALIENT`、`BUDGET_OVERHEARD`、`SALIENCY_WEIGHTS`、`SALIENCY_FLOOR`、`CONTENT_CAP_CHARS_PER_SEC`、`CONTENT_CAP_MIN_CHARS`、`CONTENT_CAP_MAX_CHARS`、`GAZE_SECONDS_DEFAULT`、`EFFECT_CAP_PER_EXPOSURE`、`MEMORY_CAP_RECOGNITION`、`MEMORY_CAP_RECALL` ほか 3 個 |
| `mind/percept/attention.py` | 45 | なし | `p_see`、`gate_stage1` | `P_SEE_LARGE_VISION`、`P_SEE_LARGE_VISION_AUDIO`、`P_SEE_LARGE_VISION_SILENT`、`P_SEE_MEDIUM_RANGE`、`P_SEE_MEDIUM_DEFAULT` |

### 4-23 `perception/renderer.py`

| 割り先 | 行数 | クラス | 関数・メソッド | 定数 |
|---|---:|---|---|---|
| `mind/percept/draw.py` | 1400 | `Rendered`、`Renderer(枠)` | `memory_item_text`、`_store_item_text`、`compose_memory_line`、`check_hunger_words`、`strip_speech_imperatives`、`_to_v3`、`acquaintance_ids_in`、`Rendered.tokens_total`、`Rendered.within_group_budgets`、`Rendered.shared_static_bytes`、`Renderer.__init__`、`Renderer.render_percept`、`Renderer.draw`、`Renderer._render_percept`、`Renderer._b1`、`Renderer._b2`、`Renderer._signage`、`Renderer._visible_static`、`Renderer._visible_names`、`Renderer._b3`、`Renderer._draw_b3`、`Renderer._b4`、`Renderer._scene_is_shared`、`Renderer._draw_b4`、`Renderer._b2_peripheral`、`Renderer._contact_blocks`、`Renderer._b5`、`Renderer._intent_text`、`Renderer._with_intent_line`、`Renderer._with_memory_line`、`Renderer.memory_summary`、`Renderer._rank_items`、`Renderer._pool_render`、`Renderer._channel_order`、`Renderer._lines_for`、`Renderer._cell_candidates`、`Renderer._cell_blocks_ranked`、`Renderer._b5_ranked`、`Renderer._b6`、`Renderer._speech_parts`、`Renderer._with_speech_lines`、`Renderer._b6_lines`、`Renderer._observation`、`Renderer.cache_hit_rate`、`Renderer._hunger_sha_min_stage`、`Renderer.report` | `SIGNAGE_P_SEE_DEFAULT`、`SIGNAGE_P_SEE_DOMAIN`、`P_SEE_ACTIVITY_KINDS`、`_STORE_ITEM_KIND`、`_STORE_SELF_BIT`、`HUNGER_WORDS_MODES`、`DEFAULT_HUNGER_WORDS`、`INVITE_REASON`、`SPEECH_HEARD_LINE`、`SPEECH_FIELD_LINE`、`SPEECH_IMPERATIVE_PATTERNS`、`_SPEECH_SENTENCE_SPLIT` ほか 10 個 |
| `world/model/percept_scene.py` | 1137 | `PerceptionAssets`、`_TickCache` | `_prior_scores`、`_load_frozen_text`、`_street_aggregate`、`near_tie_salt64`、`near_tie_keys`、`check_near_order`、`check_near_tiebreak`、`_noise_stage`、`_cell_index`、`PerceptionAssets.n_cells`、`PerceptionAssets.uses_frozen_signage`、`PerceptionAssets.uses_frozen_cell_static`、`PerceptionAssets.noise_stage_for_tick`、`PerceptionAssets.weather`、`PerceptionAssets.synthetic`、`PerceptionAssets.available`、`PerceptionAssets.load_or_synthetic`、`PerceptionAssets.load`、`Renderer.prepare_tick`、`Renderer.b4_field_rows`、`Renderer.perceive`、`Renderer._scene`、`Renderer._wake_view`、`Renderer._intent_view`、`Renderer._time_view`、`Renderer._signage_poi`、`Renderer.signage_poi_by_cell`、`Renderer.activity_class_of`、`Renderer.activity_classes`、`Renderer._b4b_raw`、`Renderer._b4b_lines`、`Renderer._merge_activity_lines`、`Renderer._nearby`、`Renderer._nearby_items`、`Renderer._nearby_people`、`Renderer._nearby_people_distance`、`Renderer._near_sort`、`Renderer._near_take`、`Renderer._acquaintances_of`、`Renderer._named_closed_text`、`Renderer._cheapest_price`、`Renderer._next_open_hour` | `_ONE_MICROSECOND`、`_NS_PER_MICROSECOND`、`WALKABLE_FRACTION_SYNTHETIC`、`STREET_POINT_AREA_M2`、`NEAR_TIEBREAKS`、`_NEAR_TIE_TAG`、`_U64_MASK`、`NEAR_ORDERS` |
| `foundation/text/percept_words.py` | 93 | なし | `_hunger_word`、`intent_line`、`named_closed_note`、`activity_line`、`person_word`、`near_person_text`、`_activity_word` | `ACTIVITY_WORDS`、`ACTIVITY_WORDS_V3`、`ACTIVITY_LINE`、`ACTIVITY_LINE_MAX_TOKENS`、`ACTIVITY_ITEM_SEPARATOR`、`INTENT_LINE`、`INTENT_LINE_MAX_TOKENS`、`INTENT_FALLBACK_TARGET`、`NAMED_CLOSED_NOTE`、`NAMED_CLOSED_OPENS`、`NAMED_CLOSED_NOTE_MAX_TOKENS`、`NAMED_CLOSED_FALLBACK_NAME` |
| `mind/percept/notice.py` | 74 | なし | `check_signage_p_see`、`Renderer._signage_body`、`Renderer._signage_seen` | なし |
| `runtime/inference/bridge.py` | 39 | なし | `Renderer.render` | なし |
| `foundation/time_consts.py` | 1 | なし | なし | `DEFAULT_START_DATETIME` |
| `foundation/vocab/agent_codes.py` | 1 | なし | なし | `INTERO_UP_EDGES` |

### 4-24 `world/assets.py`

| 割り先 | 行数 | クラス | 関数・メソッド | 定数 |
|---|---:|---|---|---|
| `world/model/assets.py` | 1286 | `WorldAssets`、`ProcessAssets` | `file_sha256`、`array_sha256`、`check_area_source`、`load_walkable_area_m2`、`assets_available`、`_cell_key`、`load_assets`、`load_poi_own_cell_visibility`、`load_visible_pois_by_cell`、`_noise_stage_per_cell`、`hash_free_cat_code`、`_nearest_node_in_cell`、`_grid_next_hop`、`synthetic_assets`、`_hhmm_to_min`、`_nearest_street_point_per_cell`、`_street_features_path`、`_bus_stop_cells`、`load_process_assets`、`load_process_assets_or_synthetic`、`WorldAssets.has_noise_field`、`WorldAssets.noise_stage_for_hour`、`WorldAssets.poi_position`、`WorldAssets.n_nodes`、`WorldAssets.n_cells`、`WorldAssets.n_poi`、`WorldAssets.summary`、`ProcessAssets.has_weather`、`ProcessAssets.has_shadow`、`ProcessAssets.has_timetable`、`ProcessAssets.has_plan_spec`、`ProcessAssets.has_road`、`ProcessAssets.has_bus_stops`、`ProcessAssets.day_index_of`、`ProcessAssets.shadow_path`、`ProcessAssets.shadow_planes`、`ProcessAssets.synthetic` | `BAND_CODES`、`CELL_SIZE_M`、`GRID_ORIGIN_XY`、`_REQUIRED_FILES`、`SYNTHETIC_POI_PRICES`、`SYNTHETIC_POI_CAPACITY`、`DEFAULT_OPEN_FROM_TICK`、`DEFAULT_OPEN_TO_TICK`、`NOISE_DAY_HOURS`、`N_NOISE_STAGES`、`SHADOW_GLOB`、`AREA_SOURCES` ほか 15 個 |
| `foundation/vocab/place_words.py` | 1 | なし | なし | `SYNTHETIC_POI_CATS` |

