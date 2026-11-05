# 包みの分類の案(Claude Code の独立の案)ファイルの表 2026-11-05

> [本文](package-map-claude-code-2026-11-05.md)の付属の表です。読むだけで作りました(枝 `build/spatial-d102-prep`・HEAD `15b6bbd`)。ファイルは 1 本も動かしていません。
> 割りの行数はトップレベルの関数・クラス・定数の行の和(docstring と import の行を含まない)で、見出しの総行数より少し小さくなります。
> 新しい置き場は `src/shibuya/` からの相対です。

## 1. 数

- src の追跡ファイル 324 本(`.py` 323 本と JSON 1 本)。build は置き場を変えない 79 本。割るもの 23 本。包みの頭 25 本。それ以外の移すだけのもの 196 本。JSON 1 本。
- 表の行は機械で作り、理由の文の一部に[技術マップ](tech-map-2026-11-03.md)の一言を使いました。技術マップの後に足された `engine/defect_fixes_1103.py` は手で理由を書きました。

## 2. src(1 ファイル 1 行)

| 今の path | 新しい包みと置き場(割るものは行数つき) | 理由 | 割るか |
|---|---|---|---|
| `__init__.py` | `__init__.py`(そのまま) | パッケージの頭。中身は版だけ | いいえ |
| `agents/__init__.py` | `mind/__init__.py`(空にする) | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | いいえ |
| `agents/population.py` | `world/facts/population_reader.py` | 母集団の読み口=構築した事実の読み手 | いいえ |
| `agents/schedule.py` | `world/facts/mock_schedule.py` | mock の週次日課(構築資産の代わりの合成) | いいえ |
| `agents/state.py` | `world/model/agent_table.py` 447・`foundation/vocab/agent_codes.py` 234 | 語彙(列挙)と 35 万体の表が 1 つ。語彙は全層が読み、表は組み立てが渡す | 割る |
| `agents/weekly.py` | `world/facts/weekly_reader.py` | W17 週次表の読み口=構築した事実の読み手 | いいえ |
| `build/__init__.py` | `build/__init__.py`(置き場を変えない) | 構築の段(ランで読まれない)。オフラインの世界データ構築 W0〜W21 の包み(実行時に import されない) | いいえ |
| `build/audit/__init__.py` | `build/audit/__init__.py`(置き場を変えない) | 構築の段(ランで読まれない)。W18/W19/W20(被覆指標・凍結・検収パック)の段の一覧 | いいえ |
| `build/audit/run.py` | `build/audit/run.py`(置き場を変えない) | 構築の段(ランで読まれない)。被覆指標・凍結・検収パックを W 番号順に回す CLI | いいえ |
| `build/audit/w18_coverage.py` | `build/audit/w18_coverage.py`(置き場を変えない) | 構築の段(ランで読まれない)。W18 カタログ写像・世界被覆指標 | いいえ |
| `build/audit/w19_freeze.py` | `build/audit/w19_freeze.py`(置き場を変えない) | 構築の段(ランで読まれない)。W19 manifest の凍結と holdout の封印 | いいえ |
| `build/audit/w20_acceptance_pack.py` | `build/audit/w20_acceptance_pack.py`(置き場を変えない) | 構築の段(ランで読まれない)。W20 検収パック | いいえ |
| `build/catalog_freeze.py` | `build/catalog_freeze.py`(置き場を変えない) | 構築の段(ランで読まれない)。世界カタログ(docs の md)を JSON に凍結する | いいえ |
| `build/field/__init__.py` | `build/field/__init__.py`(置き場を変えない) | 構築の段(ランで読まれない)。W7/W10/W12/W13(場・境界レーン)の段の一覧 | いいえ |
| `build/field/common.py` | `build/field/common.py`(置き場を変えない) | 構築の段(ランで読まれない)。場・境界レーンの共有ヘルパ | いいえ |
| `build/field/road_names.py` | `build/field/road_names.py`(置き場を変えない) | 構築の段(ランで読まれない)。W10 の道路名の突合 | いいえ |
| `build/field/run.py` | `build/field/run.py`(置き場を変えない) | 構築の段(ランで読まれない)。場・境界レーンを W 番号順に回す CLI | いいえ |
| `build/field/street_grid.py` | `build/field/street_grid.py`(置き場を変えない) | 構築の段(ランで読まれない)。街路面 2.5 m 格子 | いいえ |
| `build/field/w10_noise.py` | `build/field/w10_noise.py`(置き場を変えない) | 構築の段(ランで読まれない)。W10 静的騒音場 | いいえ |
| `build/field/w10_ruler.py` | `build/field/w10_ruler.py`(置き場を変えない) | 構築の段(ランで読まれない)。W10 の物差し(較正点に町丁目の代表点を付ける) | いいえ |
| `build/field/w12_external_nodes.py` | `build/field/w12_external_nodes.py`(置き場を変えない) | 構築の段(ランで読まれない)。W12 外界ノード(鉄道の流入出) | いいえ |
| `build/field/w12_rail_events.py` | `build/field/w12_rail_events.py`(置き場を変えない) | 構築の段(ランで読まれない)。W12 の渋谷の発着の表 | いいえ |
| `build/field/w12_real_timetables.py` | `build/field/w12_real_timetables.py`(置き場を変えない) | 構築の段(ランで読まれない)。W12 の実ダイヤの読み口 | いいえ |
| `build/field/w13_weather.py` | `build/field/w13_weather.py`(置き場を変えない) | 構築の段(ランで読まれない)。W13 気象日の再生の表 | いいえ |
| `build/field/w7_planspec.py` | `build/field/w7_planspec.py`(置き場を変えない) | 構築の段(ランで読まれない)。W7 営業時間・価格帯 PlanSpec | いいえ |
| `build/geo/__init__.py` | `build/geo/__init__.py`(置き場を変えない) | 構築の段(ランで読まれない)。W0〜W6/W11(地理レーン)の段の一覧 | いいえ |
| `build/geo/common.py` | `build/geo/common.py`(置き場を変えない) | 構築の段(ランで読まれない)。地理レーンの共有ヘルパ(ハッシュ・座標・格子) | いいえ |
| `build/geo/poi_class.py` | `build/geo/poi_class.py`(置き場を変えない) | 構築の段(ランで読まれない)。W6 POI の種別とサブカテゴリの分類 | いいえ |
| `build/geo/run.py` | `build/geo/run.py`(置き場を変えない) | 構築の段(ランで読まれない)。地理レーンを回し build_manifest.json を書く CLI | いいえ |
| `build/geo/w0_crs.py` | `build/geo/w0_crs.py`(置き場を変えない) | 構築の段(ランで読まれない)。W0 原点・座標系の凍結 | いいえ |
| `build/geo/w11_station_exits.py` | `build/geo/w11_station_exits.py`(置き場を変えない) | 構築の段(ランで読まれない)。W11 駅・出口 | いいえ |
| `build/geo/w1_walk_graph.py` | `build/geo/w1_walk_graph.py`(置き場を変えない) | 構築の段(ランで読まれない)。W1 歩行グラフ | いいえ |
| `build/geo/w2_cells.py` | `build/geo/w2_cells.py`(置き場を変えない) | 構築の段(ランで読まれない)。W2 セル生成 | いいえ |
| `build/geo/w3_distances.py` | `build/geo/w3_distances.py`(置き場を変えない) | 構築の段(ランで読まれない)。W3 全点対距離 | いいえ |
| `build/geo/w4_heights.py` | `build/geo/w4_heights.py`(置き場を変えない) | 構築の段(ランで読まれない)。W4 建物・高さ | いいえ |
| `build/geo/w5_entrances.py` | `build/geo/w5_entrances.py`(置き場を変えない) | 構築の段(ランで読まれない)。W5 入口点 | いいえ |
| `build/geo/w6_poi_org.py` | `build/geo/w6_poi_org.py`(置き場を変えない) | 構築の段(ランで読まれない)。W6 POI・組織の束縛 | いいえ |
| `build/lang/__init__.py` | `build/lang/__init__.py`(置き場を変えない) | 構築の段(ランで読まれない)。W14/W15(静的言語化レーン)の段の一覧 | いいえ |
| `build/lang/common.py` | `build/lang/common.py`(置き場を変えない) | 構築の段(ランで読まれない)。W14/W15 の共有ヘルパ(プロンプトと応答の読み書き) | いいえ |
| `build/lang/run.py` | `build/lang/run.py`(置き場を変えない) | 構築の段(ランで読まれない)。静的言語化レーンを回す CLI | いいえ |
| `build/lang/w14_signage.py` | `build/lang/w14_signage.py`(置き場を変えない) | 構築の段(ランで読まれない)。W14 看板の文面 | いいえ |
| `build/lang/w15_cell_static.py` | `build/lang/w15_cell_static.py`(置き場を変えない) | 構築の段(ランで読まれない)。W15 B2 セル静的文 | いいえ |
| `build/pop/__init__.py` | `build/pop/__init__.py`(置き場を変えない) | 構築の段(ランで読まれない)。W16(母集団合成)の段の一覧 | いいえ |
| `build/pop/attr_fns.py` | `build/pop/attr_fns.py`(置き場を変えない) | 構築の段(ランで読まれない)。W21 の「属性から作る関数」の置き場 | いいえ |
| `build/pop/fitting.py` | `build/pop/fitting.py`(置き場を変えない) | 構築の段(ランで読まれない)。IPF・整数配分・適合度指標 | いいえ |
| `build/pop/pool.py` | `build/pop/pool.py`(置き場を変えない) | 構築の段(ランで読まれない)。v1 ペルソナプールの読み取りと列化 | いいえ |
| `build/pop/run.py` | `build/pop/run.py`(置き場を変えない) | 構築の段(ランで読まれない)。母集団レーンを回す CLI | いいえ |
| `build/pop/shapefile.py` | `build/pop/shapefile.py`(置き場を変えない) | 構築の段(ランで読まれない)。ESRI Shapefile の最小パーサと点包含 | いいえ |
| `build/pop/w16_population.py` | `build/pop/w16_population.py`(置き場を変えない) | 構築の段(ランで読まれない)。W16 母集団合成 | いいえ |
| `build/pop/w21_apply.py` | `build/pop/w21_apply.py`(置き場を変えない) | 構築の段(ランで読まれない)。W21 段 10「差し替え」の組み立て | いいえ |
| `build/pop/w21_attrs.py` | `build/pop/w21_attrs.py`(置き場を変えない) | 構築の段(ランで読まれない)。W21 段 3「属性」 | いいえ |
| `build/pop/w21_build.py` | `build/pop/w21_build.py`(置き場を変えない) | 構築の段(ランで読まれない)。W21 段 1〜3(人数の枠・世帯と人・属性)の組み立て | いいえ |
| `build/pop/w21_build_b.py` | `build/pop/w21_build_b.py`(置き場を変えない) | 構築の段(ランで読まれない)。W21 段 4〜7(組織と関係・お金・開始前の経験・外の人)の組み立て | いいえ |
| `build/pop/w21_build_c.py` | `build/pop/w21_build_c.py`(置き場を変えない) | 構築の段(ランで読まれない)。W21 段 8〜9 と段 10 の材料の組み立て | いいえ |
| `build/pop/w21_check.py` | `build/pop/w21_check.py`(置き場を変えない) | 構築の段(ランで読まれない)。W21 段 8「点検」 | いいえ |
| `build/pop/w21_checks.py` | `build/pop/w21_checks.py`(置き場を変えない) | 構築の段(ランで読まれない)。W21 の計器(合否なし) | いいえ |
| `build/pop/w21_frame.py` | `build/pop/w21_frame.py`(置き場を変えない) | 構築の段(ランで読まれない)。W21 段 1「人数の枠」 | いいえ |
| `build/pop/w21_households.py` | `build/pop/w21_households.py`(置き場を変えない) | 構築の段(ランで読まれない)。W21 段 2「世帯と人」(焼きなましの詰め) | いいえ |
| `build/pop/w21_money.py` | `build/pop/w21_money.py`(置き場を変えない) | 構築の段(ランで読まれない)。W21 段 5「お金」 | いいえ |
| `build/pop/w21_org.py` | `build/pop/w21_org.py`(置き場を変えない) | 構築の段(ランで読まれない)。W21 段 4「組織と関係」 | いいえ |
| `build/pop/w21_outside.py` | `build/pop/w21_outside.py`(置き場を変えない) | 構築の段(ランで読まれない)。W21 段 7「外の人」 | いいえ |
| `build/pop/w21_persona.py` | `build/pop/w21_persona.py`(置き場を変えない) | 構築の段(ランで読まれない)。W21 段 9「見せ方」=事実から人物の説明文を組む | いいえ |
| `build/pop/w21_port10.py` | `build/pop/w21_port10.py`(置き場を変えない) | 構築の段(ランで読まれない)。W21 段 10 の材料 | いいえ |
| `build/pop/w21_prior.py` | `build/pop/w21_prior.py`(置き場を変えない) | 構築の段(ランで読まれない)。W21 段 6「開始前の経験」 | いいえ |
| `build/pop/w21_sources.py` | `build/pop/w21_sources.py`(置き場を変えない) | 構築の段(ランで読まれない)。W21 の材料の台帳と読み口の守り read_guard | いいえ |
| `build/pop/w21_tables.py` | `build/pop/w21_tables.py`(置き場を変えない) | 構築の段(ランで読まれない)。W21 の表の組み立て(区の雛形と町丁目への配分) | いいえ |
| `build/run.py` | `build/run.py`(置き場を変えない) | 構築の段(ランで読まれない)。世界データ構築の通し実行 | いいえ |
| `build/sched/__init__.py` | `build/sched/__init__.py`(置き場を変えない) | 構築の段(ランで読まれない)。W17(週次スケジュール生成)の段の一覧 | いいえ |
| `build/sched/pool_facts.py` | `build/sched/pool_facts.py`(置き場を変えない) | 構築の段(ランで読まれない)。ペルソナプールの「生活の素材」欄だけを引く | いいえ |
| `build/sched/run.py` | `build/sched/run.py`(置き場を変えない) | 構築の段(ランで読まれない)。スケジュール生成レーンを回す CLI | いいえ |
| `build/sched/trial.py` | `build/sched/trial.py`(置き場を変えない) | 構築の段(ランで読まれない)。D-68 下見(2,000 体・多腕)の別経路 | いいえ |
| `build/sched/vocab.py` | `build/sched/vocab.py`(置き場を変えない) | 構築の段(ランで読まれない)。W17 週次活動表の凍結語彙と行書式 | いいえ |
| `build/sched/w17_schedule.py` | `build/sched/w17_schedule.py`(置き場を変えない) | 構築の段(ランで読まれない)。W17 スケジュール生成(LLM のプロンプトと取り込み) | いいえ |
| `build/sched/w20_calendar_1a.py` | `build/sched/w20_calendar_1a.py`(置き場を変えない) | 構築の段(ランで読まれない)。W20 暦 1a(勤務と授業の約束の週の表) | いいえ |
| `build/sched/w20_w21_port.py` | `build/sched/w20_w21_port.py`(置き場を変えない) | 構築の段(ランで読まれない)。W21 の人の表から W20 の属性を作る口 | いいえ |
| `build/space/__init__.py` | `build/space/__init__.py`(置き場を変えない) | 構築の段(ランで読まれない)。空間の段の構築側の包み | いいえ |
| `build/space/mesh.py` | `build/space/mesh.py`(置き場を変えない) | 構築の段(ランで読まれない)。塗った格子からラン・門・帯を作る | いいえ |
| `build/space/navmesh1.py` | `build/space/navmesh1.py`(置き場を変えない) | 構築の段(ランで読まれない)。多層の歩ける面のナビメッシュを組む | いいえ |
| `build/space/raster.py` | `build/space/raster.py`(置き場を変えない) | 構築の段(ランで読まれない)。歩ける面の格子に多角形・帯・三角形を塗る | いいえ |
| `build/space/sources.py` | `build/space/sources.py`(置き場を変えない) | 構築の段(ランで読まれない)。ナビメッシュの材料を手元のファイルから読む | いいえ |
| `build/vis/__init__.py` | `build/vis/__init__.py`(置き場を変えない) | 構築の段(ランで読まれない)。W8/W9(可視性・影レーン)の段の一覧 | いいえ |
| `build/vis/png.py` | `build/vis/png.py`(置き場を変えない) | 構築の段(ランで読まれない)。最小の PNG 書き出し | いいえ |
| `build/vis/run.py` | `build/vis/run.py`(置き場を変えない) | 構築の段(ランで読まれない)。可視性・影レーンを回す CLI | いいえ |
| `build/vis/w8_visibility.py` | `build/vis/w8_visibility.py`(置き場を変えない) | 構築の段(ランで読まれない)。W8 可視性テーブル | いいえ |
| `build/vis/w9_shadow.py` | `build/vis/w9_shadow.py`(置き場を変えない) | 構築の段(ランで読まれない)。W9 影グリッド | いいえ |
| `census/__init__.py` | 消す候補(中身が無い) | 4 行の頭だけ。呼び手が無い | いいえ |
| `cli.py` | `interfaces/cli/main.py` 1568・`interfaces/cli/wire_economy.py` 134 | CLI の入口。引数と組み立てを割る | 割る |
| `core/__init__.py` | `foundation/__init__.py`(空にする) | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | いいえ |
| `core/budget.py` | `foundation/budget.py` | 予算宣言表の読み口。shibuya の中を読まない | いいえ |
| `core/growth.py` | `foundation/growth.py` | 状態成長の宣言と検査の型 | いいえ |
| `core/hashing.py` | `foundation/hashing.py` | 決定論ハッシュ。決定論ハッシュ(blake3・xxh64・sha256_cbor)と優先度キー | いいえ |
| `core/rng.py` | `foundation/rng.py` | カウンタベース乱数。カウンタベース乱数(Philox)のドメイン分離 | いいえ |
| `core/serialize.py` | `foundation/serialize.py` | SoA の保存の道具(呼び手は試験だけ) | いいえ |
| `core/soa.py` | `foundation/soa.py` | SoA レジストリ。SoA レジストリとバイト予算宣言 M9 | いいえ |
| `core/time_consts.py` | `foundation/time_consts.py` | 時間の定数。時間の定数と秒⇔刻みの換算 | いいえ |
| `core/types.py` | `foundation/types.py` | 時刻・ID の型。時刻・ID・イベントクラスの固定 dtype | いいえ |
| `core/wage_formula.py` | `economy/wage_formula.py` | 中身は経済(core の下に置く理由が無い) | いいえ |
| `core/write_permit.py` | `foundation/write_permit.py` | 書きの許可の入れ物。系ごとの「書いてよい SoA の列」の実行時の守り | いいえ |
| `economy/__init__.py` | `economy/__init__.py`(空にする) | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | いいえ |
| `economy/accounts.py` | `economy/accounts.py` | 経済の中身。部門・貸借の行・取引科目の列挙と faucet/sink 表 | いいえ |
| `economy/anchors.py` | `economy/anchors.py` | 経済の中身。金額アンカー(公的値)と初期財布・月次賃金 | いいえ |
| `economy/census.py` | `economy/census.py` | 経済の中身。日次センサスと月次 MER・ゲート判定 | いいえ |
| `economy/checks.py` | `economy/checks.py` | 経済の中身。検算 2 本(Caiani 2016)・残差ゲート・退蔵・ex nihilo の検査 | いいえ |
| `economy/credit.py` | `economy/credit.py` | 経済の中身。信用の器 C1〜C3(`CreditBook`・`repay_due`)。呼び手なし | いいえ |
| `economy/entry_capital.py` | `economy/entry_capital.py` | 経済の中身。店の参入資本を経済センサスから按分する | いいえ |
| `economy/goods.py` | `economy/goods.py` | 経済の中身。物の保存則。`move_goods` 単一 API と SKU 別収支 | いいえ |
| `economy/ledger.py` | `economy/ledger.py` | 経済の中身。金の台帳 U11。`transfer` 単一 API と取引フロー行列 | いいえ |
| `economy/ops.py` | `economy/ops.py` | 経済の中身。お金の基本操作「移す」=残高を書く唯一の関数 | いいえ |
| `economy/pricing.py` | `economy/pricing.py` | 経済の中身。価格形成(内生フロア・Calvo・逸脱比例コスト) | いいえ |
| `economy/stage2.py` | `economy/stage2.py` | 経済の中身。経済の段階 2(賃金・引き出し・支払い・レジの税・来街者の口座) | いいえ |
| `economy/tax_deposit.py` | `economy/tax_deposit.py` | 経済の中身。店の預かり消費税 | いいえ |
| `economy/taxes.py` | `economy/taxes.py` | 経済の中身。規則の表の税・社会保険・消費税・信用の上限の読み手 | いいえ |
| `economy/wages.py` | `economy/wages.py` | 経済の中身。賃金構造基本統計の賃金と最低賃金の床 | いいえ |
| `engine/__init__.py` | `runtime/__init__.py`(空にする) | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | いいえ |
| `engine/absent_processes.py` | `world/laws/switch_absent.py` | 「無い」過程の切替口(3-2 で消す候補) | いいえ |
| `engine/activity.py` | `act/activity.py` | 持続する活動の実行。行為と活動の二層の活動層 | いいえ |
| `engine/arbiter.py` | `runtime/arbiter.py` 457・`mind/system1/wake.py` 63 | 呼数の裁定。9-4 で消える。型だけ割る | 割る |
| `engine/batching.py` | `foundation/queues/batching.py` | 計算のまとめの窓。連絡の配達と runtime が読む | いいえ |
| `engine/body/__init__.py` | `world/body/__init__.py`(空にする) | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | いいえ |
| `engine/body/model.py` | `world/body/model.py` | 本人の体の層。本人の体の層 | いいえ |
| `engine/body/rules.py` | `world/body/rules.py` | 体の規則の値と純関数=9-1 の外 | いいえ |
| `engine/body/schedule.py` | `world/body/schedule.py` | 体の段の境目の予約。段の境目を越える時刻の予約 TM5 | いいえ |
| `engine/body/system1.py` | `world/body/reactions.py` | 体の側の意図しない反応の器(9-3c で意味の表は持たない) | いいえ |
| `engine/bridging/__init__.py` | `foundation/decl/__init__.py`(空にする) | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | いいえ |
| `engine/bridging/ledger.py` | `foundation/decl/bridging.py` | つなぎの台帳の読み口。世界・社会の腕・runtime が読み、ほかを読まない | いいえ |
| `engine/bridging/scan.py` | `validation/static/bridging_scan.py` | expedient の宣言の検査(試験と道具だけ) | いいえ |
| `engine/calendar.py` | `world/facts/calendar.py` 386・`foundation/types.py` 9 | 暦。刻みの換算だけ割る | 割る |
| `engine/calendar2/__init__.py` | `society/arms/calendar2/__init__.py`(空にする) | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | いいえ |
| `engine/calendar2/arm.py` | `foundation/arms/calendar2.py` | 腕の切替口。何も読まない。CLI・心・社会の腕が読む | いいえ |
| `engine/calendar2/book.py` | `mind/plan/promise_book.py` | 本人の理解としての予定(CA3) | いいえ |
| `engine/calendar2/layer.py` | `society/arms/calendar2/layer.py` | 腕の持ち主と系(心・器・体の実行の束ね=v3 で割る) | いいえ |
| `engine/calendar2/port.py` | `mind/plan/calendar2_port.py` | カレンダー 2 の本人の判断 | いいえ |
| `engine/calendar2/recall.py` | `mind/plan/head_recall.py` | 頭の中の予定の思い出し。頭の中の予定の思い出し | いいえ |
| `engine/calendar3/__init__.py` | `society/arms/calendar3/__init__.py`(空にする) | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | いいえ |
| `engine/calendar3/arm.py` | `foundation/arms/calendar3.py` | 腕の切替口。何も読まない。CLI・心・社会の腕が読む | いいえ |
| `engine/calendar3/knowledge.py` | `society/arms/calendar3/knowledge.py` | 常識と店の決まりの問い合わせの口 | いいえ |
| `engine/calendar3/layer.py` | `society/arms/calendar3/layer.py` | 腕の持ち主と系(心・器・体の実行の束ね=v3 で割る) | いいえ |
| `engine/calendar3/port.py` | `mind/plan/calendar3_port.py` | カレンダー 3 の本人の判断 | いいえ |
| `engine/calendar3/roster.py` | `society/arms/calendar3/roster.py` | 雇い主の口のつなぎ。雇い主の口のつなぎ | いいえ |
| `engine/calendar_self.py` | `society/arms/calendar_self.py` | 腕。本人の判断と体の実行の束ね(v3 で割る) | いいえ |
| `engine/calendar_shadow.py` | `society/vessels/calendar_shadow.py` | 暦 1a の影=計器。暦 1a の影=計器だけ | いいえ |
| `engine/change_detect.py` | `mind/system1/change_detect.py` 290・`world/model/scene_hash.py` 63・`foundation/vocab/agent_codes.py` 6 | System 1 と B4 の指紋が 1 つ。割る | 割る |
| `engine/chooser.py` | `mind/judge/chooser.py` 153・`foundation/ports/choice.py` 69 | 選び手の口と実装。口だけ割る | 割る |
| `engine/classical.py` | `mind/judge/classical.py` | 古典の方策。System 1.5 の古典的選択モデル | いいえ |
| `engine/clock.py` | `runtime/clock.py` | 時計。シミュレーション時計 | いいえ |
| `engine/commit.py` | `act/intake/from_words.py` 542・`act/commit.py` 300・`foundation/vocab/act_codes.py` 34 | 取り合いの裁定と言葉の読みが 1 つ。割る | 割る |
| `engine/contact/__init__.py` | `society/arms/contact/__init__.py`(空にする) | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | いいえ |
| `engine/contact/arm.py` | `foundation/arms/contact.py` | 腕の切替口。何も読まない。CLI・心・社会の腕が読む | いいえ |
| `engine/contact/attention.py` | `mind/plan/contact_attention.py` | 目と心の向き。目と心の向き | いいえ |
| `engine/contact/book.py` | `society/arms/contact/book.py` | 宛先の持ち主。宛先(連絡先とグループ)の持ち主 | いいえ |
| `engine/contact/calls.py` | `society/arms/contact/calls.py` | 電話の会話。電話の会話 | いいえ |
| `engine/contact/chat_state.py` | `society/arms/contact/chat_state.py` | チャットの会話の状態。チャットの会話の状態 | いいえ |
| `engine/contact/deliver.py` | `society/arms/contact/deliver.py` | メッセージを届ける器。メッセージ・電話・既読を届ける | いいえ |
| `engine/contact/device.py` | `society/arms/contact/device.py` | 道具の状態。道具の状態と通知の刺激 | いいえ |
| `engine/contact/habit.py` | `mind/plan/contact_habit.py` | 連絡の習慣。CT4 の連絡の習慣 | いいえ |
| `engine/contact/layer.py` | `society/arms/contact/layer.py` | 腕の持ち主と系(心・器・体の実行の束ね=v3 で割る) | いいえ |
| `engine/contact/port.py` | `mind/plan/contact_port.py` | 連絡の本人の判断。連絡の本人の判断(J0 の形の仮のモデル) | いいえ |
| `engine/contact/tools.py` | `society/arms/contact/tools.py` | 道具の台帳へ足す。連絡の道具を道具の台帳へ足す | いいえ |
| `engine/conversation.py` | `society/vessels/conversation.py` | 会話のセッションの器。会話プロトコルのセッション状態機械 | いいえ |
| `engine/decision/__init__.py` | `mind/judge/decision/__init__.py`(空にする) | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | いいえ |
| `engine/decision/layer.py` | `mind/judge/decision/layer.py` | 候補の口の腕と層。候補の口 J0 の腕と層 | いいえ |
| `engine/decision/persona.py` | `mind/judge/decision/persona.py` | 人物の欄(器)。人物の欄(短い版・長い版)と差し替えの口 | いいえ |
| `engine/decision/port.py` | `foundation/ports/decision.py` | 候補の口の型。心も社会の腕も読む | いいえ |
| `engine/decision/ports.py` | `mind/judge/decision/ports.py` | 候補の口の 3 実装。候補の口の 3 実装 | いいえ |
| `engine/decision/sources.py` | `mind/judge/decision/sources.py` | 候補を作る。候補を 5 つの源から作る | いいえ |
| `engine/defect_fixes_1103.py` | `world/laws/switch_defects.py` | 欠陥 4 件の切替口(3-2 で消す候補) | いいえ |
| `engine/duties/__init__.py` | `society/arms/duties/__init__.py`(空にする) | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | いいえ |
| `engine/duties/arm.py` | `foundation/arms/duties.py` | 腕の切替口。何も読まない。CLI・心・社会の腕が読む | いいえ |
| `engine/duties/knowledge.py` | `society/arms/duties/knowledge.py` | 常識と店の決まりの問い合わせの口 | いいえ |
| `engine/duties/layer.py` | `society/arms/duties/layer.py` | 腕の持ち主と系(心・器・体の実行の束ね=v3 で割る) | いいえ |
| `engine/duties/port.py` | `mind/plan/duties_port.py` | 店の仕事の本人の判断。店の仕事の本人の判断(J0 の形の仮のモデル) | いいえ |
| `engine/economy_rules.py` | `economy/rules_bind.py` | 規則の表を経済の段階 2 に挿す口 | いいえ |
| `engine/economy_stage2.py` | `economy/stage2_bind.py` | 経済の段階 2 の切替口と組み立て | いいえ |
| `engine/energy.py` | `world/body/energy.py` | 体のエネルギー収支。体のエネルギー収支 | いいえ |
| `engine/events/__init__.py` | 消す(頭だけ) | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | いいえ |
| `engine/events/body.py` | `society/vessels/tools/body_events.py` 130・`foundation/vocab/events.py` 25 | 体の出来事を記録に書く口。語の変換だけ割る | 割る |
| `engine/events/links.py` | `world/model/journal_links.py` | 既存の記録の行に出来事の目印を付ける口 | いいえ |
| `engine/events/log.py` | `foundation/journal.py` | 出来事の記録 5W1H。語彙と書きの許可だけを読み、全層が書く(本文は割らない) | いいえ |
| `engine/events/vocab.py` | `foundation/vocab/events.py` | 出来事の閉じた語彙。行動の語彙だけを読む | いいえ |
| `engine/experiment/__init__.py` | `experiments/__init__.py`(空にする) | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | いいえ |
| `engine/experiment/apply.py` | `experiments/port/apply.py` | 申込書と世界に入る口(runtime が読む)。申込書の改変を世界に入れる口 | いいえ |
| `engine/experiment/branch.py` | `experiments/drive/branch.py` | 分岐の駆動(runtime の上) | いいえ |
| `engine/experiment/checks.py` | `experiments/port/checks.py` | 申込書と世界に入る口(runtime が読む)。申込書の点検 | いいえ |
| `engine/experiment/ensemble.py` | `experiments/port/ensemble.py` | 申込書と世界に入る口(runtime が読む)。アンサンブルの封印・事前登録・技量スコアの器 | いいえ |
| `engine/experiment/form.py` | `experiments/port/form.py` | 申込書と世界に入る口(runtime が読む)。反実仮想の申込書 | いいえ |
| `engine/experiment/gate.py` | `foundation/ports/experiment_gate.py` | 実験が世界に入る唯一の口。出来事の型が検査のために読むので下に置く | いいえ |
| `engine/experiment/layer.py` | `experiments/port/layer.py` | 申込書と世界に入る口(runtime が読む)。申込書をランに置く口と系 experiment | いいえ |
| `engine/experiment/switch.py` | `experiments/drive/switch.py` | 切り替えの駆動(runtime の上) | いいえ |
| `engine/experiment/warmup.py` | `experiments/port/warmup.py` | 申込書と世界に入る口(runtime が読む)。慣らしの判定の規則の事前登録 | いいえ |
| `engine/familiarity.py` | `mind/memory/familiarity.py` | 親しみ。親しみの表=訪問と露出のカウンタ | いいえ |
| `engine/geometry.py` | `world/model/geometry.py` | 位置の幾何と歩く速さ。位置幾何の切替口と希望歩行速度 | いいえ |
| `engine/growth_decl.py` | `runtime/state/growth_decl.py` | 状態成長の宣言。エンジン側の状態成長宣言 | いいえ |
| `engine/intent.py` | `act/intent.py` | 行為の実行中の状態の保持 | いいえ |
| `engine/ledger_api.py` | `foundation/ports/ledger.py` | 台帳の依存逆転の口(Protocol)。経済の中身を読まない | いいえ |
| `engine/llm_bridge.py` | `runtime/inference/bridge.py` 825・`foundation/ports/inference.py` 53 | 推論の口と描画の橋。割る | 割る |
| `engine/manifest_sections.py` | `runtime/state/manifest_sections.py` | manifest の欄の分け方 | いいえ |
| `engine/memory.py` | `mind/memory/memory.py` | 記憶の記録と想起。記憶 第 1 段の記録と想起 | いいえ |
| `engine/memory_embed.py` | `mind/memory/memory_embed.py` | 埋め込みの口。記憶 MR2 の埋め込みの口 | いいえ |
| `engine/memory_impression.py` | `mind/memory/memory_impression.py` | 印象の器。記憶 M3 の印象の履歴と寝たときの書き直しの器 | いいえ |
| `engine/memory_m1.py` | `mind/memory/memory_m1.py` | 記憶の強さの式。記憶 MR の強さの式・個人差・腕の切替口 | いいえ |
| `engine/memory_shops.py` | `mind/memory/memory_shops.py` | 店の評価の行。人も記憶の腕の店の評価の行 | いいえ |
| `engine/memory_store.py` | `mind/memory/memory_store.py` | 記憶の器。記憶の器 M0 | いいえ |
| `engine/memory_trace.py` | `mind/memory/memory_trace.py` | 浅い痕跡の器。注意を向けずに見ていた人の浅い痕跡の器 | いいえ |
| `engine/norm_meter.py` | `society/vessels/norm_meter.py` | 群と規範の計器=読むだけ | いいえ |
| `engine/owner_guard.py` | `runtime/clocks/owner_guard.py` | 外の状態の持ち主の守り。外の状態の持ち主の実行時の守り | いいえ |
| `engine/poi_target.py` | `act/target.py` 617・`foundation/vocab/place_words.py` 74 | 穴の値を決める。語彙の定数だけ割る | 割る |
| `engine/presence.py` | `world/laws/presence.py` 1511・`world/laws/presence_plan.py` 402 | 在圏の出入りの法則と計画の読み。割る | 割る |
| `engine/processes/__init__.py` | `world/laws/__init__.py`(空にする) | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | いいえ |
| `engine/processes/civic.py` | `world/laws/civic.py` | 公共サービスほかの世界過程 | いいえ |
| `engine/processes/crowd.py` | `world/laws/crowd.py` | 混雑の集約。混雑場・流れ・屋内占有・待ち行列 | いいえ |
| `engine/processes/environment.py` | `world/laws/environment.py` | 天気と体感温度。昼夜・天候・体感温度 | いいえ |
| `engine/processes/goods_flow.py` | `world/laws/goods_flow.py` | 補充・入荷ほかのつなぎの過程 | いいえ |
| `engine/processes/logistics.py` | `world/laws/logistics.py` | 宅配ほかの過程。宅配・バス/タクシー・道路工事 | いいえ |
| `engine/processes/opening.py` | `world/laws/opening.py` | 開閉店のつなぎの過程。営業時間と役割行動「開閉店」 | いいえ |
| `engine/processes/rail.py` | `world/laws/rail.py` | 鉄道の運行。鉄道運行(ODPT 静的ダイヤ) | いいえ |
| `engine/processes/rail_events.py` | `world/laws/rail_events.py` | 発着の表の読み口(器)。渋谷の発着の表(W12 1.3.0)を読む口の器 | いいえ |
| `engine/processes/runner.py` | `world/laws/runner.py` | 世界過程の実行器。世界過程の実行器=台帳→実装の唯一の橋 | いいえ |
| `engine/processes/salient.py` | `world/laws/salient.py` | 顕著な出来事の過程。顕著行為と p_notice の結線 | いいえ |
| `engine/processes/traffic.py` | `world/laws/traffic.py` | 自動車交通。断面自動車交通 | いいえ |
| `engine/proximity.py` | `world/model/proximity.py` | 距離で決まる届く範囲=物理 | いいえ |
| `engine/rate_rules.py` | `world/laws/switch_rate.py` | 率の規則の切替口(3-2 で消す候補) | いいえ |
| `engine/regional_clock.py` | `runtime/clocks/regional.py` | 場所ごとの時計の腕。場所ごとの時計 T4 | いいえ |
| `engine/relations.py` | `mind/relations/layer.py` 746・`world/facts/initial_ties.py` 326・`foundation/vocab/relations.py` 42 | 客観の初期の辺と主観の辺が 1 つ。割る | 割る |
| `engine/relations_people.py` | `mind/relations/people.py` | 人も記憶の腕の関係の読み口=本人の理解 | いいえ |
| `engine/resolve.py` | `act/apply.py` 454・`act/ops/shop.py` 454・`act/ops/rail.py` 379・`act/ops/move.py` 322・`act/ops/plan_writes.py` 309・`mind/ops.py` 218・`act/ops/law_writes.py` 197・`act/ops/body_writes.py` 158・`act/gate.py` 154・`act/ops/talk.py` 154・`runtime/state/restore.py` 136・`act/ops/intent_writes.py` 115・`act/ops/focus.py` 94・`act/ops/init_writes.py` 82・`foundation/write_guard.py` 33・`foundation/vocab/act_codes.py` 3・`foundation/vocab/agent_codes.py` 2 | 書き手の全部。割る | 割る |
| `engine/resume.py` | `runtime/state/resume.py` | 再開と設定の指紋。日境界の再開と通しランの状態の書き出し・読み込み・設定の指紋 | いいえ |
| `engine/rights/__init__.py` | `world/facts/rights/__init__.py`(空にする) | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | いいえ |
| `engine/rights/initial.py` | `world/facts/rights/initial.py` | 権利台帳の最初の中身。権利台帳の最初の中身 | いいえ |
| `engine/rights/ledger.py` | `world/facts/rights/ledger.py` | 誰が権利を持つかの客観の事実(9-1 の外) | いいえ |
| `engine/rights/record.py` | `world/facts/rights/record.py` | 許可のない行動の記録。許可のない行動の記録と役割語の権利の確かめ | いいえ |
| `engine/rng_audit.py` | `validation/static/rng_audit.py` | 乱数の検査(試験だけ)。K19 の検査=乱数の流れのブロックの重なり | いいえ |
| `engine/rules/__init__.py` | `world/facts/rules/__init__.py`(空にする) | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | いいえ |
| `engine/rules/table.py` | `world/facts/rules/table.py` | 現実の法と制度の値=事実。経済も読む | いいえ |
| `engine/run.py` | `runtime/result.py` 1227・`runtime/run.py` 987・`interfaces/cli/run_args.py` 193 | ランの結果と入口と CLI の補助。割る | 割る |
| `engine/run_kind.py` | `experiments/port/run_kind.py` | ランの種類の決まり。ランの種類(再現・反実仮想・腕・試験)を決めて manifest へ | いいえ |
| `engine/scheduler.py` | `foundation/queues/scheduler.py` | 汎用の予約の列。体の層と runtime が読む | いいえ |
| `engine/seat_release.py` | `world/laws/switch_seat.py` | 在席の解き方の切替口。在席の印を歩き出しで解く切替口(既定 walk) | いいえ |
| `engine/solar.py` | `world/model/solar.py` | 太陽の位置と WBGT。太陽の位置と WBGT の推定 | いいえ |
| `engine/space/__init__.py` | `world/model/space/__init__.py`(空にする) | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | いいえ |
| `engine/space/nav1.py` | `world/model/space/nav1.py` | ナビメッシュの移動の問い合わせ(書くのは act) | いいえ |
| `engine/spatial_index.py` | `world/model/spatial_index.py` | 近傍の索引。近傍の索引 | いいえ |
| `engine/speech/__init__.py` | `society/vessels/speech/__init__.py`(空にする) | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | いいえ |
| `engine/speech/layer.py` | `society/vessels/speech/layer.py` | 会話の番から発話を作る糸 | いいえ |
| `engine/speech/port.py` | `society/vessels/speech/port.py` | 発話の口と未読の列。発話の口 | いいえ |
| `engine/speech_clock.py` | `runtime/clocks/speech.py` | 会話の時計の腕。会話の時計 T2 | いいえ |
| `engine/state_codec.py` | `runtime/state/codec.py` | 状態のファイル。状態のファイルの直列化 npz+json | いいえ |
| `engine/state_hashes.py` | `runtime/state/hashes.py` | 2 つのハッシュ。behavior-hash と full-hash | いいえ |
| `engine/state_ledger.py` | `runtime/state/ledger.py` | 状態台帳。状態台帳の宣言(挙動と復元の 2 軸) | いいえ |
| `engine/state_ledger_ast.py` | `runtime/state/ledger_ast.py` | 列の読み手の AST の検査。起動時に allow が読む | いいえ |
| `engine/step_scope.py` | `runtime/clocks/step_scope.py` | 何かあった体だけ進める腕 | いいえ |
| `engine/store_choice.py` | `mind/judge/store_choice.py` | 想起優先の候補。想起優先の候補合成と決め手の記録 | いいえ |
| `engine/store_memory.py` | `mind/memory/store_memory.py` | 店の評価の記憶。店の評価の記憶 | いいえ |
| `engine/systems/__init__.py` | `runtime/systems/__init__.py`(空にする) | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | いいえ |
| `engine/systems/act.py` | `runtime/systems/act.py` | 系の配線。行為の解決の系 | いいえ |
| `engine/systems/allow.py` | `runtime/systems/allow.py` | 系の配線。系の書いてよい SoA の列を resolve の静的な閉包から作る | いいえ |
| `engine/systems/body.py` | `runtime/systems/body.py` | 系の配線。体の系 | いいえ |
| `engine/systems/boxes.py` | `runtime/systems/boxes.py` | 系の配線。run_day の状態の箱 | いいえ |
| `engine/systems/build.py` | `runtime/systems/assemble.py` | 全部の口を組み立てる場所 | いいえ |
| `engine/systems/conductor.py` | `runtime/systems/conductor.py` | 系の配線。系を呼ぶ進行役 | いいえ |
| `engine/systems/day.py` | `runtime/systems/day.py` | 系の配線。日の境目の系 | いいえ |
| `engine/systems/decide.py` | `runtime/systems/decide.py` | 系の配線。判断の系=LLM の呼と会話の番の発話 | いいえ |
| `engine/systems/guard.py` | `foundation/write_guard.py` | 系の書きの許可(出来事の記録も心の器も読む)。runtime に置くと下の層が上を読む | いいえ |
| `engine/systems/judge.py` | `runtime/systems/judge.py` | 系の配線。応答の適用・起床の源と絞り込み・アービタの系 | いいえ |
| `engine/systems/llm_io.py` | `runtime/systems/llm_io.py` | 系の配線。LLM の往復の口と系 llm_receive | いいえ |
| `engine/systems/observe.py` | `runtime/systems/observe.py` | 系の配線。計器の系 observe と checkpoint | いいえ |
| `engine/systems/overrides.py` | `validation/static/system_overrides.py` | 負の対照の差し替え(試験だけ) | いいえ |
| `engine/systems/perceive.py` | `runtime/systems/perceive.py` | 系の配線。知覚の系 | いいえ |
| `engine/systems/probe.py` | `runtime/systems/probe.py` | 系の配線。系ごとの全欄の差と指紋 | いいえ |
| `engine/systems/remember.py` | `runtime/systems/remember.py` | 系の配線。記憶の系 | いいえ |
| `engine/systems/report.py` | `runtime/systems/report.py` | 系の配線。ランの結果の組み立て R3 | いいえ |
| `engine/systems/run_end.py` | `runtime/systems/run_end.py` | 系の配線。ランの終わりの系 | いいえ |
| `engine/systems/spec.py` | `runtime/systems/spec.py` | 系の配線。系の宣言の口 | いいえ |
| `engine/systems/state_io.py` | `runtime/systems/state_io.py` | 系の配線。箱から状態台帳の持ち主・知覚 SoA・ハッシュの材料を組む | いいえ |
| `engine/systems/static_check.py` | `validation/static/system_static_check.py` | 宣言とコードの突き合わせ(試験だけ) | いいえ |
| `engine/systems/table.py` | `runtime/systems/table.py` | 系の配線。系の宣言の表 SYSTEMS(呼ぶ順の 1 つの表) | いいえ |
| `engine/systems/talk.py` | `runtime/systems/talk.py` | 系の配線。会話の系 | いいえ |
| `engine/systems/world.py` | `runtime/systems/world.py` | 系の配線。世界の系=世界過程 18 本を runner.step で回す | いいえ |
| `engine/tape.py` | `runtime/inference/tape.py` | 録画と再生。LLM 録画テープ(1 呼 1 行 Parquet)と完全一致の再生 | いいえ |
| `engine/tools/__init__.py` | `society/vessels/tools/__init__.py`(空にする) | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | いいえ |
| `engine/tools/contacts.py` | `foundation/vocab/contact_flags.py` | 連絡先の手段の印の語彙。何も読まない | いいえ |
| `engine/tools/groups.py` | `society/vessels/tools/groups.py` | グループの一覧(客観の事実の器) | いいえ |
| `engine/tools/places.py` | `society/vessels/tools/places.py` | 店の番号の表。店の番号の場所の表 | いいえ |
| `engine/tools/record.py` | `society/vessels/tools/record.py` 88・`foundation/vocab/events.py` 3 | 道具の記録。語の定数だけ割る | 割る |
| `engine/tools/registry.py` | `society/vessels/tools/registry.py` 271・`foundation/vocab/events.py` 1 | 道具の台帳。語の定数だけ割る | 割る |
| `engine/wom.py` | `mind/memory/wom.py` | 口コミの聞き取り。会話からの店の抽出=口コミの書き手 | いいえ |
| `llm/__init__.py` | `foundation/ports/inference.py` 116 | 型は口へ。再輸出は消す | 割る |
| `llm/contract.py` | `foundation/vocab/actions.py` | 行動の語彙の表。心・差分の器・出来事の全部が読む語彙で、ほかを読まない | いいえ |
| `llm/fleet.py` | `runtime/inference/fleet.py` 1473・`foundation/ports/inference.py` 215 | 型と艦隊のクライアント。型だけ割る | 割る |
| `llm/mock.py` | `runtime/inference/mock.py` 263・`foundation/vocab/actions.py` 1 | mock のクライアント。定数だけ割る | 割る |
| `llm/parser.py` | `act/intake/parser.py` | 本人の言葉を行為の型へ読む(器の入口) | いいえ |
| `llm/undefined.py` | `act/intake/undefined.py` 636・`foundation/vocab/act_codes.py` 3 | 語彙の外の行為の受け口。語の表だけ割る | 割る |
| `manifest/__init__.py` | `foundation/manifest/__init__.py`(空にする) | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | いいえ |
| `manifest/canonical.py` | `foundation/manifest/canonical.py` | manifest の正規化 | いいえ |
| `manifest/schema.py` | `foundation/manifest/schema.py` | manifest の型。U8 run manifest の 13 節の型 | いいえ |
| `manifest/world_catalog.py` | `world/ledger/world_catalog.py` | 世界カタログの読み口。世界側台帳だけが読む | いいえ |
| `perception/__init__.py` | `mind/percept/__init__.py`(空にする) | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | いいえ |
| `perception/attention.py` | `foundation/text/salience.py` 182・`mind/percept/attention.py` 45 | 気づきのゲートと文の道具が 1 つ。割る | 割る |
| `perception/channels.py` | `foundation/text/channels.py` | 文の予算とトークンの見積り=状態を持たない道具。build も読む | いいえ |
| `perception/contact_view.py` | `foundation/ports/percept_contact.py` | 連絡の知覚の事実の型(描き方の関数を含む)。何も読まない | いいえ |
| `perception/facts.py` | `foundation/ports/percept.py` | 知覚の口の型=世界と心の境目。標準ライブラリだけ | いいえ |
| `perception/hashes.py` | `foundation/text/hashes.py` | 文と欄のハッシュ=状態を持たない道具 | いいえ |
| `perception/normalize.py` | `foundation/text/normalize.py` | 文の正規化=状態を持たない文字列の道具。build と act も読む | いいえ |
| `perception/p_notice.py` | `world/model/notice_reach.py` | 顕著な行為が届いたか=世界の物理の側(9-3c で作り直す) | いいえ |
| `perception/renderer.py` | `mind/percept/draw.py` 1400・`world/model/percept_scene.py` 1137・`foundation/text/percept_words.py` 93・`mind/percept/notice.py` 74・`runtime/inference/bridge.py` 39・`foundation/time_consts.py` 1・`foundation/vocab/agent_codes.py` 1 | 世界の段と心の段が 1 つ。割る | 割る |
| `perception/state.py` | `world/model/percept_state.py` | 向きなどの派生の列。読み手は顕著な出来事の過程 | いいえ |
| `perception/templates.py` | `foundation/text/templates.py` | 凍結の文の雛形=何も読まない定数。心と runtime が読む | いいえ |
| `world/__init__.py` | `world/__init__.py`(空にする) | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | いいえ |
| `world/assets.py` | `world/model/assets.py` 1286・`foundation/vocab/place_words.py` 1 | 世界の資産の読み。語彙の定数だけ割る | 割る |
| `world/graph.py` | `world/model/graph.py` | 世界の客観の状態と資産。歩行グラフと next-hop 経路 | いいえ |
| `world/navmesh.py` | `world/model/navmesh.py` | 世界の客観の状態と資産。ナビメッシュの資産と問い合わせ | いいえ |
| `world/navmesh_route.py` | `world/model/navmesh_route.py` | 世界の客観の状態と資産。ナビメッシュの上の経路(W1 の通り道→帯の A*→funnel) | いいえ |
| `world/processes/__init__.py` | `world/ledger/__init__.py`(空にする) | 包みの頭。再輸出は消す(呼び手は新しい置き場を直に読む) | いいえ |
| `world/processes/absent.py` | `world/ledger/absent.py` | 世界過程の宣言と記録の台帳。「無いと宣言」する過程と判断の一覧 | いいえ |
| `world/processes/actual_log.py` | `world/ledger/actual_log.py` | 世界過程の宣言と記録の台帳。追記専用 ActualLog | いいえ |
| `world/processes/circularity.py` | `validation/static/circularity.py` | 循環の検査(試験だけ)。循環(同じ値の系で動かして採点する)の機械検査 | いいえ |
| `world/processes/constitution.py` | `world/ledger/constitution.py` | 憲法 5 の定数と検査。台帳の組み立てが読むので world に残す | いいえ |
| `world/processes/deletion_candidates.py` | `validation/static/deletion_candidates.py` | 削除候補の追記(試験だけ) | いいえ |
| `world/processes/first_batch.py` | `world/ledger/first_batch.py` | 世界過程の宣言と記録の台帳。第 1 陣の世界過程の宣言(データだけ) | いいえ |
| `world/processes/inputs.py` | `world/ledger/inputs.py` | 世界過程の宣言と記録の台帳。世界過程の入力の宣言の一覧 | いいえ |
| `world/processes/records.py` | `world/ledger/records.py` | 世界過程の宣言と記録の台帳。世界側台帳のレコード型 3 つ | いいえ |
| `world/processes/registry.py` | `world/ledger/registry.py` | 世界過程の宣言と記録の台帳。世界側台帳(名前空間・ID は 1 つ) | いいえ |
| `world/processes/relations.py` | `world/ledger/relations.py` | 世界過程の宣言と記録の台帳。世界側台帳の関係 4 本 | いいえ |
| `world/state.py` | `world/model/state.py` | 世界の客観の状態と資産。セルと POI の状態 SoA と世界オブジェクト | いいえ |
| `manifest/frozen/world_catalog_v0_2.json` | `world/ledger/frozen/world_catalog_v0_2.json` | 世界カタログの凍結。読み口と一緒に動かす(pyproject の package-data も直す) | いいえ |

## 3. tests

第 1 段では tests を動かしません。動かすと `parents[N]` の 133 行と `conftest.py` の `REPO_ROOT` が全部ずれるので、src の移動と別の段にします。第 1 段で直すのは import と path の文字列だけです(本文 §6)。下の表は最後に置く場所です。

| 今のディレクトリ | ファイル数 | 目標の置き場 | 理由・外れるファイル |
|---|---:|---|---|
| tests/agents | 3 | `tests/foundation/`(語彙)・`tests/world/model/`(表) | `test_state.py` は表と語彙の両方。`test_schedule.py` は `tests/world/facts/` |
| tests/bench | 2 | `tests/validation/bench/` | 計測の道具の試験 |
| tests/bridging | 3 | `tests/validation/bridging/` | つなぎと世界過程の宣言の検査 |
| tests/build_audit・build_field・build_geo・build_lang・build_pop・build_rail・build_sched・build_space・build_vis | 53 | `tests/build/<audit・field ほか>/` | build の木に合わせる |
| tests/c6・c7・c8 | 35 | `tests/validation/<c6・c7・c8>/` | 受入と感度の計器の試験 |
| tests/core | 5 | `tests/foundation/` | core の移り先に合わせる |
| tests/economy | 45 | `tests/economy/`(そのまま) | economy は名が変わらない。`engine.ledger_api`・`engine.economy_stage2` の import だけ直す |
| tests/engine/batching | 3 | `tests/foundation/queues/` | 計算のまとめの窓 |
| tests/engine/body | 9 | `tests/world/body/` | 体の層 |
| tests/engine/bridging | 3 | `tests/validation/bridging/` | つなぎの台帳と宣言の検査 |
| tests/engine/calendar | 4 | `tests/society/arms/calendar_self/` | カレンダー 1b と暦 1a の影 |
| tests/engine/calendar2・calendar3・contact・duties | 29 | `tests/society/arms/<同じ名>/` | 腕の試験 |
| tests/engine/clock | 4 | `tests/runtime/clocks/` | 時計の腕 |
| tests/engine/decision | 9 | `tests/mind/judge/decision/` | 候補の口 |
| tests/engine/events | 10 | `tests/foundation/journal/` | 出来事の記録 |
| tests/engine/experiment | 10 | `tests/experiments/` | 申込書・分岐 |
| tests/engine/memory | 17 | `tests/mind/memory/` | 記憶 |
| tests/engine/multiday | 6 | `tests/runtime/multiday/` | 複数日のラン |
| tests/engine/processes | 17 | `tests/world/laws/` | 世界過程 |
| tests/engine/proximity | 6 | `tests/world/model/proximity/` | 届く範囲 |
| tests/engine/rights・rules | 12 | `tests/world/facts/<同じ名>/` | 権利と規則の表 |
| tests/engine/space | 4 | `tests/world/model/space/` | ナビメッシュの移動 |
| tests/engine/speech・tools | 23 | `tests/society/vessels/<同じ名>/` | 発話の口と道具の台帳 |
| tests/engine/systems | 7 | `tests/runtime/systems/` | 系の宣言と書きの許可 |
| tests/engine/time | 11 | `tests/foundation/time/` | 時間の定数と刻みの語の検査 |
| tests/fig | 2 | `tests/interfaces/fig/` | 図の道具の試験 |
| tests/fixtures | 3 | `tests/fixtures/`(そのまま) | 試験のデータ。CI が md5 を見る |
| tests/llm | 9 | `tests/runtime/inference/`(fleet・mock)・`tests/foundation/vocab/`(contract・vocab_v2)・`tests/act/intake/`(parser・undefined) | llm の割り方に合わせる |
| tests/perception | 19 | `tests/mind/percept/` | 描画と注意 |
| tests/perception/facts | 7 | `tests/foundation/ports/percept/` | 知覚の事実の型 |
| tests/tools | 18 | `tests/tools/`(そのまま) | tools を動かさないので合わせる |
| tests/vocab | 5 | `tests/foundation/vocab/` | 語彙の裁定の道具 |
| tests/w17 | 3 | `tests/build/sched/` | W17 の物差し |
| tests/world | 12 | `tests/world/ledger/`(processes)・`tests/world/model/`(`test_world.py`) | 世界側台帳 |

外れるファイル(ディレクトリの直下にあって行き先が割れるもの)。

| ファイル | 目標の置き場 | 理由 |
|---|---|---|
| tests/__init__.py・conftest.py・_data_ids.py・_time_gates.py・golden_env.py | そのまま | 試験の共通の部品 |
| tests/test_budget_table.py・test_rng_properties.py・test_manifest_roundtrip.py・test_manifest_rules_extra.py | `tests/foundation/` | foundation の試験 |
| tests/test_build_run_keep_stage.py | `tests/build/` | build の通し |
| tests/test_child_imports_this_tree.py | そのまま | 取り出した木の import の検査 |
| tests/test_cli.py・test_cli_help.py・test_cli_intent_mode.py・test_cli_l4_scale.py・test_cli_vocab_version.py | `tests/interfaces/` | CLI の試験 |
| tests/test_fixture_holiday_csv.py | `tests/world/facts/` | 祝日の表 |
| tests/test_world_catalog_sha.py | `tests/world/ledger/` | 世界カタログの凍結 |
| tests/engine 直下: test_resume_10d.py・test_state_checks_10f.py・test_state_format_10f.py・test_state_ledger_10b.py・test_version_bump_10e.py・test_env_and_sections_10f.py・test_t3_manifest.py | `tests/runtime/state/` | 読む部品の移り先に合わせる |
| tests/engine 直下: test_tape.py・test_tape_deferred.py・test_tape_wiring.py・tape_analysis.py・test_fleet_wiring.py・test_llm_mock.py・test_response_delay.py | `tests/runtime/inference/` | 読む部品の移り先に合わせる |
| tests/engine 直下: test_determinism_t1_t2_t4.py・test_mock_day_w2.py・test_10a_review_fixes.py・test_ablation23_switches.py・test_activation_10e.py・test_activation_2_4.py・test_salt_seed_split_10f.py・test_stage3_small_fixes.py・test_arbiter.py・test_l4_budget.py・test_clock.py・test_census_out.py・test_ledger_wiring.py・test_pop_w21_world.py | `tests/runtime/` | 読む部品の移り先に合わせる |
| tests/engine 直下: test_resolve.py・test_two_phase.py・test_add_at_guard.py・ast_writers.py・test_intent_chooser.py・test_intent_hold.py・test_intent_mode_open.py・test_two_layer_activity.py・test_move_destination.py・test_parser_contract.py・test_undefined_action.py・test_c9b_targets_attention.py・test_vocab_v2_eat.py・test_eatery_place_food.py | `tests/act/` | 読む部品の移り先に合わせる |
| tests/engine 直下: test_energy_balance.py・test_meal_bundle_2b.py・test_meal_gate_per_hour.py・test_sleep_suppression_d56.py | `tests/world/body/` | 読む部品の移り先に合わせる |
| tests/engine 直下: test_presence_derive_v2.py・test_presence_executor.py・test_presence_exit_walk.py・test_plan_sleep_d62.py・test_processes_run.py・test_seat_release_2_4.py・test_waste_sink_report.py・discard_probe.py・test_defect_fixes_1103.py | `tests/world/laws/` | 読む部品の移り先に合わせる |
| tests/engine 直下: test_calendar.py・test_calendar_10e_e3.py・test_calendar_sites.py・test_weather_calendar_10e.py | `tests/world/facts/` | 読む部品の移り先に合わせる |
| tests/engine 直下: test_geometry_c9.py・test_assets_10e_b0_b1.py・test_area_source_c9c.py | `tests/world/model/` | 読む部品の移り先に合わせる |
| tests/engine 直下: test_change_detect_p6.py・test_classical_policy.py・test_classical_social.py・test_familiarity.py・test_memory_recall.py・test_memory_record.py・test_relations.py・test_relations_8b.py・test_relations_tenure.py・test_renderer_wiring.py・test_store_choice.py・test_store_memory.py・test_wom.py | `tests/mind/` | 読む部品の移り先に合わせる |
| tests/engine 直下: test_conversation.py・test_conversation_invite.py・test_norm_meter.py | `tests/society/` | 読む部品の移り先に合わせる |
| tests/engine 直下: test_scheduler.py・test_scheduler_p3.py・test_sim_time_T.py | `tests/foundation/` | 読む部品の移り先に合わせる |

`tests/` の頭の試験と AST の検査は path を文字列で持つものが多いので、本文 §6 の表で個別に数えました。

## 4. tools

tools は Python のパッケージの外にあるので、import の契約が効きません。置き場は変えず、役割だけを決めます。封印の層を読む部品だけを `src/shibuya/validation/sealed/` へ移す候補にします(本文 §7 の迷い 12)。

| ディレクトリ | 置き場 | 理由 | 割るか |
|---|---|---|---|
| tools/commit_check.py・decision_index.py・scan_secrets.py | そのまま(リポの道具) | シミュレーションの包みに入らない | いいえ |
| tools/bench・bench_spikes | そのまま・役割は validation の計測 | 性能の計測 | いいえ |
| tools/build_geo・world_data・spatial・hunger・gen・w17・vocab・ledger | そのまま・役割は build | 構築とラン外の下ごしらえ | いいえ |
| tools/realworld_fetch | そのまま・役割は build の取得 | 取得の道具。封印の層を書く側なので validation の sealed と同じ検査の対象にする | いいえ |
| tools/c6・c8 | そのまま・役割は validation | 受入と感度の計器 | いいえ |
| tools/c7 | そのまま・役割は validation | 受入の計器。下の 3 本だけ封印を読む候補 | いいえ |
| tools/instruments | そのまま・役割は validation | 計器。`read_guard.py` が読み口の守り | いいえ |
| tools/fig | そのまま・役割は interfaces | 図を出す道具 | いいえ |
| tools/night5070 | そのまま・役割は interfaces | 夜間のラン。`experiments.json` が `-m shibuya.cli` を文字列で持つ | いいえ |
| tools/quality_probe_v0 | そのまま・役割は validation | LLM の品質の計測 | いいえ |

外れるファイル。

| ファイル | 置き場 | 理由 |
|---|---|---|
| tools/c7/holdout_compare.py | `validation/sealed/holdout_compare.py` の候補 | 封印の層の語が 43 か所。読むかは本文を確かめていない【見立て】 |
| tools/c7/c7_accept.py | `validation/sealed/c7_accept.py` の候補 | 同じ語が 17 か所【見立て】 |
| tools/c7/c7lib.py | `validation/sealed/c7lib.py` の候補 | 同じ語が 8 か所【見立て】 |
| tools/instruments/read_guard.py | `validation/sealed/read_guard.py` の候補 | 封印の読み口の守り。ランの側は読まない。計器は読む |
