# src/shibuya/build/field

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 12 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/build/field/__init__.py)

build.field — 世界データ構築 W7/W10/W12/W13(場・境界レーン)。

- 呼び手: `shibuya.build.field.run`・`shibuya.build.run`

## [common.py](../../../../../../../../src/shibuya/build/field/common.py)

build.field.common — 場・境界レーンの共有ヘルパ。

- 公開の関数とクラス
  - `clamp`(関数)
  - `db_from_power`(関数): 相対エネルギー → dB(0 以下は ``-300`` を返す=無音の番兵)。
  - `db_sum`(関数): dB のエネルギー和(パワー和)。空なら ``-300``。
  - `hhmm_to_min`(関数): ``HH:MM`` → 0時からの分。``24:00`` は 1440。
  - `json_text`(関数): Parquet の文字列列へ入れる canonical JSON(バイト決定論のため)。
  - `median`(関数): 偶数個は下側中央値(決定論・浮動小数の平均を避ける)。
  - `min_to_hhmm`(関数): 0時からの分 → ``HH:MM``(24時以降は 25:10 のように繰り上げ表記)。
  - `normalize_jp`(関数): 路線名などの日本語キーを突合可能な形へ正規化する。
  - `power_from_db`(関数): dB → 相対エネルギー。
  - `read_holidays_csv`(関数): 内閣府の祝日 CSV → {``YYYY-MM-DD``: 名称}(全行・日付順)。
- import している内部モジュール: `shibuya.build.geo.common`・`shibuya.core.time_consts`
- 呼び手: `shibuya.build.field.road_names`・`shibuya.build.field.run`・`shibuya.build.field.w10_noise`・`shibuya.build.field.w10_ruler`・`shibuya.build.field.w12_external_nodes`・`shibuya.build.field.w13_weather`・`shibuya.build.field.w7_planspec`
- 読む試験: `tests/build_field/test_field_units.py`・`tests/build_field/test_w10_road_names.py`・`tests/build_field/test_w10_ruler.py`・`tests/build_field/test_w12_keio_switch_2_4.py`・`tests/build_field/test_w12_pm_peak_switch.py`・`tests/build_field/test_w12_real_timetables.py`・`tests/build_rail/test_w12_arrivals_2_3c.py`
- 決定の ID: 第 330

## [road_names.py](../../../../../../../../src/shibuya/build/field/road_names.py)

W10 の道路名の突合(段 1c・D-1 (a)・2026-09-28)。

- 公開の関数とクラス
  - `EdgeWayMatch`(クラス): 辺 → way → センサス路線 の突合の結果(辺の並び=``w1_edges`` の行順)。
  - `census_key`(関数): way のタグ → ``(種別, 路線番号の候補)``。種別は :data:`KEY_KINDS` のどれか。
  - `edge_midpoints`(関数): 辺の折れ線の**弧長の中点** ``(n, 2)``(世界ローカル m)。
  - `match_edges_to_ways`(関数): 辺の中点 → 最も近い way(≤ ``buffer_m``)→ センサス路線。
  - `match_report`(関数): klass 別の写像率・名寄せ率・路線ごとの辺数(W10 の notes 用・決定論)。
  - `nearest_way`(関数): 各点に最も近い way の索引と距離[m]\(同距離は線分の並びが先の way=決定論)。
  - `sections_for_key`(関数): 種別+路線番号 → センサス区間(``wards`` の順に最初に区間がある区のもの・無ければ全区間)。
  - `way_band`(関数): 段 1c′ Q9: way の層 → ``UG``/``GL``/``DECK``(W1 の辺の ``band`` と同じ語)。
  - `way_segments`(関数): Overpass の way(``geometry`` = ``[{lat, lon}, …]``)→ 線分の配列 ``(ax, ay, bx, by, owner)``。
- import している内部モジュール: `shibuya.build.field.common`・`shibuya.build.geo.common`
- 呼び手: `shibuya.build.field.w10_noise`
- 読む試験: `tests/build_field/test_w10_road_names.py`・`tests/build_field/test_w10_ruler.py`
- 決定の ID: D-1

## [run.py](../../../../../../../../src/shibuya/build/field/run.py)

build.field.run — 場・境界レーンの段階を W 番号順に実行する CLI。

- 公開の関数とクラス
  - `main`(関数)
  - `run_stages`(関数): 段階を順に実行してヘッダを書く(geo.run.run_stages と同形・段階表だけが違う)。
- import している内部モジュール: `shibuya.build.field`・`shibuya.build.field.common`・`shibuya.build.field.w10_noise`・`shibuya.build.field.w12_external_nodes`・`shibuya.build.field.w13_weather`・`shibuya.build.field.w7_planspec`・`shibuya.build.geo.run`
- 呼び手: `shibuya.build.run`
- CLI の引数
  - `--data`: 入力データ根(既定 data)
  - `--out`: 出力ディレクトリ(例 data/world/v2)
  - `--quiet`
  - `--stage`: 実行する段階(繰り返し可・既定=全段階)

## [street_grid.py](../../../../../../../../src/shibuya/build/field/street_grid.py)

街路面 2.5m 格子(D-W9「道路8mバッファ・2.5m格子」・W8/W9/W10 の共有台)。

- 公開の関数とクラス
  - `StreetPoints`(クラス): 街路格子。SoA(列ごとの numpy 配列)。
  - `segment_arrays`(関数): エッジ折線 → 線分配列 (ax, ay, bx, by, owner_edge_idx)。
  - `street_points`(関数): 歩行グラフ → 街路面格子点(層バンド別)。
- 呼び手: `shibuya.build.field.w10_noise`・`shibuya.build.field.w10_ruler`
- 読む試験: `tests/build_field/test_field_units.py`

## [w10_noise.py](../../../../../../../../src/shibuya/build/field/w10_noise.py)

W10 静的騒音場(§1 W10・D-W11)。

- 公開の関数とクラス
  - `calibrate`(関数): 較正点ごとにモデル値と実測の残差を出す。座標を必要としない(路線名で突合)。
  - `energy_coeffs`(関数): 区間諸元 → (昼 A, 夜 A)。A は時間平均したエネルギー係数(``LAeq=10 lg(A·Σ1/r)``)。
  - `geometry_factor`(関数): 車線別線音源の幾何係数 ``Σ_i 1/r_i``(d=車道中心線からの距離)。
  - `hourly_flows`(関数): 時刻 → (小型車 台/h, 大型車 台/h)。昼間12h=7-18時・残りを 19-6時へ一様配分。
  - `l_a_max`(関数): 伝搬 ``L_A = L_WA − 8 − 20·lg r + ΔL``(点音源・反射面上)。
  - `l_wa`(関数): ASJ RTN-Model 2018 の音響パワーレベル ``L_WA = a + b·lg V`` [dB]。
  - `laeq_at`(関数): 区間諸元+車道中心線からの距離 → (昼 LAeq, 夜 LAeq) [dB]。
  - `lane_energy_coeff`(関数): 1車線・1時間・単位距離あたりのエネルギー係数 A(``LAeq = 10·lg(A/r)``)。
  - `lane_offsets`(関数): 車道中心線から見た各車線中心の符号つき横位置(近い側が正・降順)。
  - `median_section`(関数): 区間群 → 列ごとの中央値(決定論のため下側中央値)。
  - `noise_stage`(関数): LAeq → B4 騒音段階の番号(0=静か .. 3=うるさい)。
  - `read_kasyo`(関数): 箇所別基本表 → 区間辞書のリスト(必要列のみ・ヘッダ名で探す)。
  - `read_r5_points`(関数): 常時監視測定地点 CSV → 渋谷区5点+隣接2点(D-W11 の較正点)。
  - `route_match`(関数): 路線名(+市区町村)でセンサス区間を引く。正規化一致→末尾「線」を落とした前方一致。
  - `run`(関数)
- import している内部モジュール: `shibuya.build.field.common`・`shibuya.build.field.road_names`・`shibuya.build.field.street_grid`・`shibuya.core.time_consts`
- 呼び手: `shibuya.build.audit.w19_freeze`・`shibuya.build.field.run`・`shibuya.build.field.w10_ruler`
- 読む試験: `tests/build_field/test_field_units.py`・`tests/build_field/test_w10_road_names.py`・`tests/build_field/test_w10_ruler.py`
- 読む試験(道筋で): `tests/engine/bridging/test_bridging_ledger.py`
- 決定の ID: 09-30・10-03/§9-4・R-67・D-1・第 330

## [w10_ruler.py](../../../../../../../../src/shibuya/build/field/w10_ruler.py)

W10 の物差し(W10 の Q6・2026-09-30): 較正点に町丁目の代表点の座標を付け、「点の近くの騒音場の値 − 実測」を測る。

- 公開の関数とクラス
  - `Chome`(クラス): 小地域 1 つ(世界ローカル m)。
  - `chome_name_from_address`(関数): (互換)R5 の所在地 → (区, 小地域名)。読めなければ :class:`ValueError`(行の処理は
  - `load_chome`(関数): 小地域境界 → ``{S_NAME: Chome}``(同名が複数あれば例外=曖昧な代表点を作らない)。
  - `measure_near`(関数): 点 (cx, cy) から半径 ``radius_m`` の中の格子点の代表値(``max``・``road``)。
  - `measured_klasses`(関数): R5 の道路種別 → 測った道路の階級(:data:`MEASURED_ROAD_KLASSES`・表に無ければ音源全部)。
  - `parse_address`(関数): R5 の所在地 → ``{"ward", "name", "code"}``。**例外を投げない**。
  - `points_to_segments_min_dist`(関数): 各点から線分群までの最短距離 [m]\(線分が無ければ inf)。
  - `polygon_centroid`(関数): 面積重心(全リングの符号つき面積で重み付け=穴は引かれる)。
  - `road_facing_point`(関数): 町丁目の中で最寄りの辺が測った階級の GL 格子点のうち、``estat`` 点に最も近いもの。
  - `ruler_error`(関数): 物差しの誤差の見積り(町丁目の大きさ・代表点のずれ・町丁目の中の値の散らばり)。
  - `ruler_from_world`(関数): 世界ディレクトリ(W10 の出力と W1 の辺)+ 入力データ根 → :func:`ruler_rows` の行。
  - `ruler_rows`(関数): R5 の点ごとに物差しを測る(計測の道具とテストが同じ関数を通る)。
  - `summarize_diffs`(関数): 点ごとの差(``[昼, 夜]`` or None)→ 平均・平均絶対値(評価できた点だけ)。
- import している内部モジュール: `shibuya.build.field.common`・`shibuya.build.field.street_grid`・`shibuya.build.field.w10_noise`・`shibuya.build.geo.common`・`shibuya.build.pop.shapefile`
- 読む試験: `tests/build_field/test_w10_ruler.py`

## [w12_external_nodes.py](../../../../../../../../src/shibuya/build/field/w12_external_nodes.py)

W12 外界ノード(§1 W12・D-W14・境界経済設計書 §1 U10)。

- 公開の関数とクラス
  - `equal_interval_departures`(関数): 等間隔ダイヤ(expedient)。朝ピーク=``peak_tph``・夕ピーク=``peak_tph_pm``・他は比を掛ける。
  - `hour_shares`(関数): time_dist_12 → 目的 → 24 時間の構成比(合計 1)。
  - `metro_timetables_in_use`(関数): W12 が実際に読む ODPT の駅の時刻表(線, ファイル名)=半蔵門線・副都心線だけ(銀座線は実ダイヤの読み口)。
  - `offpeak_ratio_from`(関数): メトロ実ダイヤの発時刻行 → (オフピーク比, 朝ピーク本数, 昼平均本数)。
  - `parse_metro_timetable`(関数): ODPT StationTimetable JSON → 発時刻行。
  - `pm_peak_for_line`(関数): 線ごとに :func:`equal_interval_departures` へ渡す ``peak_tph_pm``。
  - `rail_flows`(関数): 駅別発着表+乗換行列 → 路線別の (乗車/降車, 乗換流出, 乗換流入)。
  - `run`(関数)
  - `timetable_versions_doc`(関数): 〔2-3b〕``w12_timetable_versions.json``: 線ごとの版の宣言(世界の時点との前後)と入力の md5。
- import している内部モジュール: `shibuya.build.field.common`・`shibuya.build.field.w12_rail_events`・`shibuya.build.field.w12_real_timetables`・`shibuya.core.time_consts`
- 呼び手: `shibuya.build.audit.w19_freeze`・`shibuya.build.field.run`・`shibuya.build.field.w12_rail_events`
- 読む試験: `tests/build_field/test_field_units.py`・`tests/build_field/test_w12_keio_switch_2_4.py`・`tests/build_field/test_w12_pm_peak_switch.py`・`tests/build_field/test_w12_real_timetables.py`・`tests/build_rail/test_w12_arrivals_2_3c.py`
- 決定の ID: 10-12b・10-13・10-13b/§2・第 330

## [w12_rail_events.py](../../../../../../../../src/shibuya/build/field/w12_rail_events.py)

W12 の渋谷の発着の表(第 2 期 2-3c・計画 2-3c の行=2-3b の検収 3)。

- 公開の関数とクラス
  - `MetroLine`(クラス)
  - `RailEvents`(クラス)
  - `build_rail_events`(関数): 発車の表(``w12_timetables.parquet`` の列・行の順)+入力 → 発着の表と要約(時刻は要約に入れない)。
  - `keio_arrivals`(関数): 京王 井の頭線の渋谷着(チャレンジ枠の列車時刻表から作った CSV)。切替口 ``USE_ODPT_CHALLENGE`` が False なら空。
  - `metro_station_rows`(関数): ODPT の駅の時刻表(今の 7 月の取得・半蔵門線/副都心線)→ 発車の行の属性(列車の id・行き先・種別・始発の印)。
  - `metro_trains`(関数): ODPT オープン枠の列車時刻表 → (渋谷発の列車, 渋谷着の列車)=銀座線・半蔵門線・副都心線。
  - `nex_rows`(関数): 成田エクスプレスの表(読まない=湘南新宿ラインの表に含まれることの確かめだけ)。
  - `station_name`(関数): ODPT の駅 id → 名(知らない id は ValueError=黙って通さない)。
  - `suspicious_total`(関数): 残った疑わしい組の数(ゲートの値): 結べない東急の上り・下りの対の数の食い違い・上限の外・成田エクスプレスの外れ・
  - `tokyu_origin_marks`(関数): ``東急_印.final.csv``(東急 渋谷の下りの 2 表の当駅始発の印)→ (表, 暦, HH:MM) → 印。
  - `type_name`(関数)
  - `user_table_rows`(関数): 読む表(:func:`RT.tables_in_use`)の行 → 発車の行の属性(表・種別・行き先)。畳んだ後の線で返す。
- import している内部モジュール: `shibuya.build.field.w12_external_nodes`・`shibuya.build.field.w12_real_timetables`
- 呼び手: `shibuya.build.field.w12_external_nodes`
- 読む試験: `tests/build_rail/test_w12_arrivals_2_3c.py`
- 決定の ID: 第 330

## [w12_real_timetables.py](../../../../../../../../src/shibuya/build/field/w12_real_timetables.py)

W12 の実ダイヤの読み口(第 2 期 2-3b・回答 10-13 の 7・回答 10-13b §2)。

- 公開の関数とクラス
  - `OdptTrainSpec`(クラス): ODPT の列車時刻表から「起点の駅の発車」を取る線。
  - `RealTimetables`(クラス): 実ダイヤの読みの結果(行は畳んだ後・重複を除いた後・臨時を外した後)。
  - `TableSpec`(クラス): 渋谷の発車の表 1 つ(平日と土休の 2 ファイル)→ W12 の線と向き。
  - `all_input_rel_paths`(関数)
  - `dedup`(関数): 同じ (line, direction, calendar, departure) を 1 本に(先に来た行を残す)。返り値=(行, 除いた件数の表)。
  - `fold`(関数): 線を畳む(``fold_lines`` の鍵の線 → 値の線)。行の他の欄は変えない。
  - `hhmm`(関数): CSV の (時, 分) → ``HH:MM``(0 時台は 00:MM=翌日の 0 時)。範囲の外は ValueError。
  - `input_rel_paths`(関数): 入力の層 → 読むファイル(data 根からの相対・読む順)。W19 の資産表と ``input_hash`` に使う。
  - `jr_marks`(関数): ``JR_注記.final.csv`` → (表, 平日土休, 時, 分) → 印の文字列。
  - `load_odpt_static`(関数): ``*.json.gz``(ODPT の静的データの取得の形=``{"_meta":…, "data": [...]}``)を読む。
  - `load_real_timetables`(関数): data 根から実ダイヤを読む(白い一覧の表+ODPT の銀座線)。ファイルが無ければ FileNotFoundError。
  - `md5_file`(関数)
  - `metro_station_versions`(関数): ODPT の駅の時刻表(今の 7 月の取得)→ 暦ごとの dct:issued・dc:date と取得の時刻。
  - `parse_train_timetable_departures`(関数): ODPT ``odpt:TrainTimetable`` → 起点の駅(``spec.origin_station``)の発車の行と点検の表。
  - `read_csv_rows`(関数): 読み取りの CSV(UTF-8 BOM 付き)→ 行の辞書。
  - `rows_from_table`(関数): 表 1 ファイルの行 → W12 の行(畳む前の line)。CSV の会社・路線・駅・方面・平日土休が一覧と違えば止まる。
  - `spec_rows`(関数): 方面の写像の表(params と記録に書く形)。
  - `split_temporary`(関数): (残す行, 外す行)。外す行に ◆ が付いていなければ ValueError(黙って外さない)。
  - `table_rel_paths`(関数): 表 1 つの 2 ファイル(平日・土休)の data 根からの相対パス。
  - `tables_in_use`(関数): 〔2-4〕読む表=:data:`USER_TABLES` から、切替口 :data:`USE_ODPT_CHALLENGE` が False ならチャレンジ枠の表を除く。
- import している内部モジュール: `shibuya.core.time_consts`
- 呼び手: `shibuya.build.audit.w19_freeze`・`shibuya.build.field.w12_external_nodes`・`shibuya.build.field.w12_rail_events`
- 読む試験: `tests/build_audit/test_audit_units.py`・`tests/build_field/test_w12_keio_switch_2_4.py`・`tests/build_field/test_w12_pm_peak_switch.py`・`tests/build_field/test_w12_real_timetables.py`・`tests/build_rail/test_w12_arrivals_2_3c.py`
- 決定の ID: 10-13・10-13b/§2・第 330

## [w13_weather.py](../../../../../../../../src/shibuya/build/field/w13_weather.py)

W13 気象日再生(§1 W13・D-W15・知覚契約書 §3 B3 語彙)。

- 公開の関数とクラス
  - `day_weather_type`(関数): 日単位の天候型(猛暑 > 雨 > 晴/曇)。
  - `daylight_phase`(関数): B3 日照語彙。
  - `heat_stage`(関数)
  - `hour_weather`(関数): B3 天候語彙(時別)。夜間(日照が定義されない時間)は日単位の型へ落とす。
  - `read_amedas_day`(関数): アメダス日ファイル → (日付, 時 → 集約値)。10分値を時単位へ畳む。
  - `read_etrn_10min_csv`(関数): etrn 10 分値 CSV → ((日付, 時 0..23) → 時の集約値, 窓の外へ出た行の数)。
  - `read_etrn_csv`(関数): etrn 時別値 CSV → (日付, 時 0..23) → 集約値(アメダス畳み込みと同じキー)。
  - `run`(関数)
  - `season_of`(関数): 気象庁の季節の区分(春 3〜5・夏 6〜8・秋 9〜11・冬 12〜2)。列には入れない(notes の表だけ)。
  - `select_day`(関数): 層 → 実日(決定論)。``core.rng.stream(seed, "build.w13", ...)`` から引く。
  - `solar_elevation_deg`(関数): 地方時 ``local_min``(0時からの分)の太陽高度 [deg]。
  - `sun_times`(関数): 日の出・日の入(地方時の 0時からの分)。極夜・白夜は ``(None, None)``。
  - `wbgt_estimate`(関数): WBGT 推定式(屋外・実況未取得時の代替=expedient)。
  - `weekday_kind`(関数): 平日 / 土休(土日+国民の祝日=内閣府の CSV)。
  - `window_dates`(関数)
- import している内部モジュール: `shibuya.build.field.common`・`shibuya.core.rng`・`shibuya.core.time_consts`
- 呼び手: `shibuya.build.audit.w19_freeze`・`shibuya.build.field.run`・`shibuya.build.vis.w9_shadow`・`tools/c8/sensitivity.py`
- 読む試験: `tests/build_audit/test_audit_units.py`・`tests/build_field/test_field_units.py`・`tests/build_vis/test_vis_units.py`・`tests/engine/test_weather_calendar_10e.py`
- 決定の ID: 10-12b・第 330

## [w7_planspec.py](../../../../../../../../src/shibuya/build/field/w7_planspec.py)

W7 営業時間・価格帯(PlanSpec)(§1 W7・D-W8)。

- 公開の関数とクラス
  - `LawCapEffect`(クラス): 法規上限の適用で何が起きたか(区間数)。
  - `OpeningHoursParseError`(クラス): OSM ``opening_hours`` の対応部分集合の外。
  - `apply_law_cap`(関数): 営業不可窓(D-W8)で各区間を切る。**開店側も閉店側も**切る。
  - `default_week`(関数): カテゴリ既定表 → 7×区間リスト。表に無い組は KeyError(ゲートで検出)。
  - `intervals_in_prohibited_window`(関数): 営業不可窓と重なる区間の数(適用前後の不変条件の計測に使う)。
  - `law_key_for`(関数): POI → 法規上限表のキー(OSM タグの明示があればそちらを優先)。
  - `parse_holiday_hours`(関数): 〔改訂(第330 B6)〕OSM ``opening_hours`` の ``PH``(祝日)の規則 → 祝日の 1 日ぶんの区間。
  - `parse_opening_hours`(関数): OSM ``opening_hours`` の**共通部分集合**を 7×区間リストへ。
  - `prohibited_intervals`(関数): 毎日繰り返す営業不可窓を絶対軸 ``[0, span_min)`` へ展開する。
  - `run`(関数)
  - `weekly_open_minutes`(関数)
- import している内部モジュール: `shibuya.build.field.common`・`shibuya.core.time_consts`
- 呼び手: `shibuya.build.audit.w19_freeze`・`shibuya.build.field.run`
- 読む試験: `tests/build_field/test_field_units.py`
- 決定の ID: 10-12b・D-72・第 330
