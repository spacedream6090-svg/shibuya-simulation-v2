# src/shibuya/engine/processes

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 12 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/engine/processes/__init__.py)

engine.processes — **世界過程 第1陣の振る舞い**(D-R2-5・§7.2 初回実装の前半)。

- import している内部モジュール: `shibuya.engine.processes.crowd`・`shibuya.engine.processes.environment`・`shibuya.engine.processes.opening`・`shibuya.engine.processes.rail`・`shibuya.engine.processes.runner`・`shibuya.engine.processes.traffic`

## [civic.py](../../../../../../../../src/shibuya/engine/processes/civic.py)

engine.processes.civic — 公共サービス出動・報道/公式発信・大規模イベント・ホテル・インフラ。

- 公開の関数とクラス
  - `HotelProcess`(クラス): ホテル客室在庫(来街者のチェックイン・アウト)。
  - `InfraLoadProcess`(クラス): インフラ日負荷(電力・水)の集約。**報告のみ**(網は持たない)。
  - `LargeEventProcess`(クラス): 大規模イベント(会場の開催・旧道は外界からの来街増分を窓の間だけ入れる)。
  - `PressProcess`(クラス): 報道・公式発信(固定時刻の放送)。1 行を作る。届けるのは在席者のいるセルだけ(``salient._broadcast_events``)。
  - `PublicServiceDispatchProcess`(クラス): 公共サービス出動(救急・警察)。「倒れる」事象を受けて出動し、到着で解消する。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.core.rng`・`shibuya.core.time_consts`・`shibuya.engine.absent_processes`・`shibuya.engine.rate_rules`・`shibuya.engine.resolve`・`shibuya.perception.attention`・`shibuya.world.assets`・`shibuya.world.processes.records`・`shibuya.world.state`
- 呼び手: `shibuya.engine.processes.runner`
- 読む試験: `tests/engine/processes/test_absent_processes_1102.py`・`tests/engine/processes/test_civic.py`・`tests/engine/processes/test_rail_return.py`・`tests/engine/processes/test_rate_rules_1101.py`・`tests/engine/processes/test_rng_scheme_10c.py`・`tests/engine/processes/test_salient.py`・`tests/engine/test_presence_executor.py`・`tests/engine/test_salt_seed_split_10f.py`・`tests/engine/time/test_t0_time_consts.py`
- 読む試験(道筋で): `tests/engine/systems/test_fix_guards.py`
- 状態台帳の行
  - 持ち主 `runner.dispatch`(`PublicServiceDispatchProcess`)
    - `O47` PublicServiceDispatchProcess rng・pending(挙動 behavior・復元 required) 道筋 `runner.dispatch.pending`・`runner.dispatch.rng` 書ける系: day_head・phase_c・world
    - `O73` 世界の過程と実行器の計数(挙動 diag・復元 discardable) 道筋 `runner.dispatch.delay_minutes_total`・`runner.dispatch.n_arrived`・`runner.dispatch.n_dispatched` 書ける系: close_final・day_close・day_head・duties・phase_c・plan_boundary・presence・world
  - 持ち主 `runner.hotel`(`HotelProcess`)
    - `O48` HotelProcess rooms_occupied・bed_cell(挙動 behavior・復元 required) 道筋 `runner.hotel.bed_cell`・`runner.hotel.rooms_occupied` 書ける系: day_head・phase_c・world
    - `O73` 世界の過程と実行器の計数(挙動 diag・復元 discardable) 道筋 `runner.hotel.n_checkin`・`runner.hotel.n_checkout`・`runner.hotel.n_no_bed` 書ける系: close_final・day_close・day_head・duties・phase_c・plan_boundary・presence・world
  - 持ち主 `runner.infra`(`InfraLoadProcess`)
    - `O55` LastMile delivered・_cum/BusTaxi・Traffic(cell_hourly・cell_vehicles)・Infra(power_kwh)・Press・Opening・DeliveryInbound の計数(挙動 no・復元 derivable) 道筋 `runner.infra.power_kwh` 書ける系: close_final・day_close・day_head・world
    - `O73` 世界の過程と実行器の計数(挙動 diag・復元 discardable) 道筋 `runner.infra.water_m3` 書ける系: close_final・day_close・day_head・duties・phase_c・plan_boundary・presence・world
  - 持ち主 `runner.large_event`(`LargeEventProcess`)
    - `O49` LargeEventProcess _inside(挙動 behavior・復元 required) 道筋 `runner.large_event._inside` 書ける系: day_head・world
    - `O73` 世界の過程と実行器の計数(挙動 diag・復元 discardable) 道筋 `runner.large_event.n_in`・`runner.large_event.n_out` 書ける系: close_final・day_close・day_head・duties・phase_c・plan_boundary・presence・world
  - 持ち主 `runner.press`(`PressProcess`)
    - `O73` 世界の過程と実行器の計数(挙動 diag・復元 discardable) 道筋 `runner.press.n_releases` 書ける系: close_final・day_close・day_head・duties・phase_c・plan_boundary・presence・world
- 決定の ID: 10-12/§1-3・11-01・11-01/§2・11-02r/§1・11-02r/§1 #7・D-61・D-66・第 330

## [crowd.py](../../../../../../../../src/shibuya/engine/processes/crowd.py)

engine.processes.crowd — 混雑場・流れ・屋内占有・待ち行列(D-R2-5 第1陣 + §7.2 初回実装)。

- 公開の関数とクラス
  - `CrowdProcess`(クラス): 密度・流れ(人物①)と屋内占有・待ち行列(人物②)の集約。
  - `seats_for_categories`(関数): POI カテゴリ列 → 席数(容量 c)。**全部 expedient**(16行表 行2)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.resolve`・`shibuya.world.state`
- 呼び手: `shibuya.engine.processes`・`shibuya.engine.processes.runner`・`shibuya.engine.systems.build`
- 読む試験: `tests/engine/processes/test_crowd.py`・`tests/engine/test_area_source_c9c.py`・`tests/engine/test_defect_fixes_1103.py`・`tests/engine/test_env_and_sections_10f.py`
- 状態台帳の行
  - 持ち主 `runner.crowd`(`CrowdProcess`)
    - `O51` CrowdProcess queue_action(挙動 behavior・復元 required) 道筋 `runner.crowd.queue_action` 書ける系: close_final・day_close・day_head・phase_c・plan_boundary・presence・world
    - `O73` 世界の過程と実行器の計数(挙動 diag・復元 discardable) 道筋 `runner.crowd.n_balked`・`runner.crowd.n_released`・`runner.crowd.peak_occupancy`・`runner.crowd.peak_queue` 書ける系: close_final・day_close・day_head・duties・phase_c・plan_boundary・presence・world
    - `O75` CrowdProcess occupancy・queue_len・flow(挙動 behavior・復元 unknown) 道筋 `runner.crowd.flow`・`runner.crowd.occupancy`・`runner.crowd.queue_len` 書ける系: close_final・day_close・day_head・phase_c・plan_boundary・presence・world
    - `O95` CrowdProcess flow_dir8・coherence(8 方位と向きのそろい)(挙動 diag・復元 unknown) 道筋 `runner.crowd.coherence`・`runner.crowd.flow_dir8` 書ける系: close_final・day_close・day_head・world
- 決定の ID: R-8・D-113・第 263・第 268

## [environment.py](../../../../../../../../src/shibuya/engine/processes/environment.py)

engine.processes.environment — 昼夜・天候・体感温度(D-R2-5 第1陣の 1-2 行目)。

- 公開の関数とクラス
  - `EnvironmentProcess`(クラス): 昼夜(``daynight_solar``)+ 天候・体感温度(``weather``)。
  - `WeatherWarning`(クラス): 10e(B6): 天気の規則の警告(層を広げた・暦の日付の影が無く近い日の影を読んだ)。
  - `calendar_candidates`(関数): 10e(B6): 季節 × 平日/土休 の W13 の行(昇順の索引)と、広げた段(``""``=広げていない)。
  - `nearest_shadow_date`(関数): 10e(B6): ``target`` にいちばん近い影の日(同じ近さなら前の日)。影が無ければ ``None``。
  - `sample_calendar_day`(関数): 10e(B6): 季節 × 平日/土休 × 天候型の層から、窓の中で実際に起きた日数の割合で再生日を引く。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.core.hashing`・`shibuya.core.rng`・`shibuya.core.time_consts`・`shibuya.engine.body.model`・`shibuya.engine.body.rules`・`shibuya.engine.calendar`・`shibuya.engine.resolve`・`shibuya.engine.solar`・`shibuya.world.assets`・`shibuya.world.state`
- 呼び手: `shibuya.engine.processes`・`shibuya.engine.processes.runner`
- 読む試験: `tests/engine/body/test_body_same_values.py`・`tests/engine/experiment/_x33.py`・`tests/engine/experiment/test_x33_apply.py`・`tests/engine/multiday/test_md23_w9_window.py`・`tests/engine/processes/test_environment.py`・`tests/engine/test_activation_10e.py`・`tests/engine/test_activation_2_4.py`・`tests/engine/test_assets_10e_b0_b1.py`・`tests/engine/test_calendar_sites.py`・`tests/engine/test_salt_seed_split_10f.py`・`tests/engine/test_weather_calendar_10e.py`
- 読む試験(道筋で): `tests/engine/body/test_body_guard.py`
- 状態台帳の行
  - 持ち主 `runner.environment`(`EnvironmentProcess`)
    - `O56` EnvironmentProcess replay_date・stratum・_row・_shade(挙動 behavior・復元 derivable) 道筋 `runner.environment._row`・`runner.environment._shade`・`runner.environment.replay_date`・`runner.environment.stratum` 書ける系: close_final・day_close・day_head・experiment・world
    - `O73` 世界の過程と実行器の計数(挙動 diag・復元 discardable) 道筋 `runner.environment.n_updates`・`runner.environment.shadow_missing` 書ける系: close_final・day_close・day_head・duties・phase_c・plan_boundary・presence・world
    - `O76` EnvironmentProcess daylight・heat_stage・wbgt(挙動 behavior・復元 derivable) 道筋 `runner.environment.daylight`・`runner.environment.heat_stage`・`runner.environment.wbgt` 書ける系: close_final・day_close・day_head・world
- 決定の ID: 第 330

## [goods_flow.py](../../../../../../../../src/shibuya/engine/processes/goods_flow.py)

engine.processes.goods_flow — 物の流れ(§7.2 初回実装の後半 + 前倒し 1 本)。

- 公開の関数とクラス
  - `DeliveryInboundProcess`(クラス): 納品(早朝帯・**納品ドライバー行動**)。未陳列の納品枠(バックヤード)を積む。
  - `ShelfRestockProcess`(クラス): 店舗補充・棚在庫(**店員 T0 行動** + conf 宣言つき engine_rule フォールバック)。
  - `StreetCleaningProcess`(クラス): 街路清掃(セル別のごみストックが密度で増え、シフトで掃かれる)。
  - `WasteCollectionProcess`(クラス): 廃棄物収集(店舗ビン → bbox 外)+ C 類排出(売れ残り・世帯消費)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.core.rng`・`shibuya.core.time_consts`・`shibuya.engine.absent_processes`・`shibuya.engine.events.log`・`shibuya.engine.rate_rules`・`shibuya.engine.resolve`・`shibuya.world.processes.records`・`shibuya.world.state`
- 呼び手: `shibuya.engine.duties.layer`・`shibuya.engine.processes.runner`
- 読む試験: `tests/engine/duties/test_du_runs.py`・`tests/engine/processes/test_absent_processes_1102.py`・`tests/engine/processes/test_goods_flow.py`・`tests/engine/processes/test_rate_rules_1101.py`・`tests/engine/test_resume_10d.py`・`tests/engine/time/test_t0_time_consts.py`
- 状態台帳の行
  - 持ち主 `runner.delivery_inbound`(`DeliveryInboundProcess`)
    - `O55` LastMile delivered・_cum/BusTaxi・Traffic(cell_hourly・cell_vehicles)・Infra(power_kwh)・Press・Opening・DeliveryInbound の計数(挙動 no・復元 derivable) 道筋 `runner.delivery_inbound.delay_minute` 書ける系: close_final・day_close・day_head・world
    - `O73` 世界の過程と実行器の計数(挙動 diag・復元 discardable) 道筋 `runner.delivery_inbound.n_delayed`・`runner.delivery_inbound.n_runs`・`runner.delivery_inbound.units_delivered` 書ける系: close_final・day_close・day_head・duties・phase_c・plan_boundary・presence・world
  - 持ち主 `runner.shelf`(`ShelfRestockProcess`)
    - `O52` ShelfRestockProcess backroom・_acted_today(挙動 behavior・復元 required) 道筋 `runner.shelf._acted_today`・`runner.shelf.backroom` 書ける系: close_final・day_close・day_head・duties・world
    - `O73` 世界の過程と実行器の計数(挙動 diag・復元 discardable) 道筋 `runner.shelf.n_fallback`・`runner.shelf.n_no_backroom`・`runner.shelf.n_rejected`・`runner.shelf.n_role_actions`・`runner.shelf.units_restocked`・`runner.shelf.yen_paid` 書ける系: close_final・day_close・day_head・duties・phase_c・plan_boundary・presence・world
  - 持ち主 `runner.street_cleaning`(`StreetCleaningProcess`)
    - `O53` WasteCollection _cursor・waste_g_collected/StreetCleaning litter_g・swept_g(挙動 no・復元 required) 道筋 `runner.street_cleaning._cursor`・`runner.street_cleaning.litter_g`・`runner.street_cleaning.swept_g` 書ける系: close_final・day_close・day_head・duties・world
    - `O73` 世界の過程と実行器の計数(挙動 diag・復元 discardable) 道筋 `runner.street_cleaning.litter_generated_g`・`runner.street_cleaning.n_swept_cells` 書ける系: close_final・day_close・day_head・duties・phase_c・plan_boundary・presence・world
  - 持ち主 `runner.waste`(`WasteCollectionProcess`)
    - `O53` WasteCollection _cursor・waste_g_collected/StreetCleaning litter_g・swept_g(挙動 no・復元 required) 道筋 `runner.waste._cursor`・`runner.waste.waste_g_collected` 書ける系: close_final・day_close・day_head・duties・world
    - `O73` 世界の過程と実行器の計数(挙動 diag・復元 discardable) 道筋 `runner.waste.consumed_g`・`runner.waste.n_bin_rows`・`runner.waste.n_consumed`・`runner.waste.n_stops` 書ける系: close_final・day_close・day_head・duties・phase_c・plan_boundary・presence・world
- 決定の ID: 11-01・11-02r/§1・11-02r/§1 #7・第 304

## [logistics.py](../../../../../../../../src/shibuya/engine/processes/logistics.py)

engine.processes.logistics — 宅配ラストマイル・バス/タクシー・道路工事(§7.2 前倒し)。

- 公開の関数とクラス
  - `BusTaxiProcess`(クラス): バス・タクシー運行(等間隔 PlanSpec + 停留所への到着イベント)。
  - `LastMileProcess`(クラス): 宅配ラストマイル(世帯数按分 × 時間帯カーブ)。
  - `RoadWorksProcess`(クラス): 道路工事・占用(夜間の PlanSpec)。
- import している内部モジュール: `shibuya.core.rng`・`shibuya.core.time_consts`・`shibuya.engine.absent_processes`・`shibuya.engine.rate_rules`・`shibuya.world.assets`・`shibuya.world.processes.records`・`shibuya.world.state`
- 呼び手: `shibuya.engine.processes.runner`
- 読む試験: `tests/engine/processes/test_absent_processes_1102.py`・`tests/engine/processes/test_logistics.py`・`tests/engine/processes/test_rate_rules_1101.py`・`tests/engine/test_salt_seed_split_10f.py`・`tests/engine/time/test_t0_time_consts.py`
- 読む試験(道筋で): `tests/engine/bridging/test_bridging_ledger.py`
- 状態台帳の行
  - 持ち主 `runner.bus_taxi`(`BusTaxiProcess`)
    - `O73` 世界の過程と実行器の計数(挙動 diag・復元 discardable) 道筋 `runner.bus_taxi.n_arrivals` 書ける系: close_final・day_close・day_head・duties・phase_c・plan_boundary・presence・world
  - 持ち主 `runner.last_mile`(`LastMileProcess`)
    - `O55` LastMile delivered・_cum/BusTaxi・Traffic(cell_hourly・cell_vehicles)・Infra(power_kwh)・Press・Opening・DeliveryInbound の計数(挙動 no・復元 derivable) 道筋 `runner.last_mile._cum`・`runner.last_mile.delivered` 書ける系: close_final・day_close・day_head・world
    - `O73` 世界の過程と実行器の計数(挙動 diag・復元 discardable) 道筋 `runner.last_mile.n_batches` 書ける系: close_final・day_close・day_head・duties・phase_c・plan_boundary・presence・world
  - 持ち主 `runner.road_works`(`RoadWorksProcess`)
    - `O54` RoadWorks blocked_cells・occupied_edges(挙動 no・復元 required) 道筋 `runner.road_works.blocked_cells`・`runner.road_works.occupied_edges` 書ける系: close_final・day_close・day_head・world
    - `O73` 世界の過程と実行器の計数(挙動 diag・復元 discardable) 道筋 `runner.road_works.n_finished`・`runner.road_works.n_started` 書ける系: close_final・day_close・day_head・duties・phase_c・plan_boundary・presence・world
- 環境変数: `SHIBUYA_WARD_AREA_M2`
- 決定の ID: 11-01・11-01/§2・11-02r/§1・11-02r/§1 #7

## [opening.py](../../../../../../../../src/shibuya/engine/processes/opening.py)

engine.processes.opening — 営業時間 PlanSpec と役割行動「開閉店」(D-R2-5 第1陣の 6 行目)。

- 公開の関数とクラス
  - `OpeningProcess`(クラス): 営業時間 PlanSpec の実績確定(役割行動 + conf 宣言つきフォールバック)。
  - `build_open_matrix`(関数): W7 の区間 → ``(n_poi, 1440)`` の開閉行列(日跨ぎは同じ日へ巻き戻す)。
  - `rows_of_day`(関数): その日の行(曜日 0〜6・祝日 ``PH_ROW``)に当たる W7 の区間の真偽の列。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.core.time_consts`・`shibuya.core.types`・`shibuya.engine.calendar`・`shibuya.engine.resolve`・`shibuya.engine.rights.initial`・`shibuya.engine.rights.ledger`・`shibuya.engine.rights.record`・`shibuya.world.assets`・`shibuya.world.processes.records`・`shibuya.world.state`
- 呼び手: `shibuya.engine.calendar2.layer`・`shibuya.engine.calendar3.layer`・`shibuya.engine.processes`・`shibuya.engine.processes.runner`・`shibuya.engine.run`
- 読む試験: `tests/build_rail/test_w12_arrivals_2_3c.py`・`tests/engine/experiment/_x33.py`・`tests/engine/experiment/test_x33_apply.py`・`tests/engine/experiment/test_x33_branch.py`・`tests/engine/processes/test_goods_flow.py`・`tests/engine/processes/test_opening.py`・`tests/engine/rights/test_rights_events.py`・`tests/engine/rights/test_rights_manifest.py`・`tests/engine/rights/test_staff_of_poi_equivalence.py`・`tests/engine/test_calendar_10e_e3.py`・`tests/engine/test_calendar_sites.py`・`tests/engine/test_state_checks_10f.py`・`tests/engine/time/test_t0_time_consts.py`
- 状態台帳の行
  - 持ち主 `runner.opening`(`OpeningProcess`)
    - `O73` 世界の過程と実行器の計数(挙動 diag・復元 discardable) 道筋 `runner.opening.n_events`・`runner.opening.n_fallback`・`runner.opening.n_role_actions`・`runner.opening.n_unauthorized` 書ける系: close_final・day_close・day_head・duties・phase_c・plan_boundary・presence・world
- 決定の ID: 10-12/§1-1・第 330

## [rail.py](../../../../../../../../src/shibuya/engine/processes/rail.py)

engine.processes.rail — 鉄道運行(ODPT 静的ダイヤ・D-R2-5 第1陣の 3 行目)。

- 公開の関数とクラス
  - `RailProcess`(クラス): 静的ダイヤで列車を進め、乗車・降車の前提条件と混雑率受容を持つ世界過程。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.core.rng`・`shibuya.engine.calendar`・`shibuya.engine.events.log`・`shibuya.engine.ledger_api`・`shibuya.engine.rate_rules`・`shibuya.engine.resolve`・`shibuya.world.assets`・`shibuya.world.processes.records`・`shibuya.world.state`
- 呼び手: `shibuya.engine.processes`・`shibuya.engine.processes.runner`
- 読む試験: `tests/economy/cp2/test_cp2_transfer_only_writer.py`・`tests/economy/stage2/test_stage2_money_rules.py`・`tests/engine/processes/test_rail.py`・`tests/engine/processes/test_rail_board_intent.py`・`tests/engine/processes/test_rail_return.py`・`tests/engine/processes/test_rate_rules_1101.py`・`tests/engine/test_calendar_sites.py`・`tests/engine/test_defect_fixes_1103.py`・`tests/engine/test_presence_executor.py`・`tests/engine/test_presence_exit_walk.py`
- 読む試験(道筋で): `tests/tools/test_pkgmove.py`
- 状態台帳の行
  - 持ち主 `runner.rail`(`RailProcess`)
    - `O50` RailProcess occupancy・peak_ratio・_return_queue・_inbound・_inbound_ready(挙動 behavior・復元 required) 道筋 `runner.rail._inbound`・`runner.rail._inbound_ready`・`runner.rail._return_queue`・`runner.rail.occupancy`・`runner.rail.peak_ratio` 書ける系: close_final・day_close・day_head・phase_c・plan_boundary・presence・world
    - `O73` 世界の過程と実行器の計数(挙動 diag・復元 discardable) 道筋 `runner.rail.n_arrivals`・`runner.rail.n_board_applicants`・`runner.rail.n_board_dropped`・`runner.rail.n_board_intent`・`runner.rail.n_board_timeout`・`runner.rail.n_board_unreachable`・`runner.rail.n_board_waiting`・`runner.rail.n_board_waiting_plan_exit`・`runner.rail.n_board_walking`・`runner.rail.n_boarded_from_queue`・`runner.rail.n_boarded_plan_exit`・`runner.rail.n_departed_riders`・`runner.rail.n_departures`・`runner.rail.n_fare_rejected`・`runner.rail.n_left_behind`・`runner.rail.n_left_behind_by_rate`・`runner.rail.n_no_return`・`runner.rail.n_return_arrived`・`runner.rail.n_return_no_train`・`runner.rail.n_return_scheduled` 書ける系: close_final・day_close・day_head・duties・phase_c・plan_boundary・presence・world
    - `O74` RailProcess arrival_train・external_line(帰りの便の予約印・域外居住者の路線)(挙動 behavior・復元 required) 道筋 `runner.rail.arrival_train`・`runner.rail.external_line` 書ける系: close_final・day_close・day_head・phase_c・world
- 決定の ID: 11-01・11-01/§2・D-51・D-61・D-66・D-115・第 302

## [rail_events.py](../../../../../../../../src/shibuya/engine/processes/rail_events.py)

engine.processes.rail_events — 渋谷の発着の表(W12 1.3.0)を読む口の器(第 2 期 2-3c・**既定は読まない**)。

- 公開の関数とクラス
  - `RailEventsAsset`(クラス): 発着の表の SoA(行の順は資産のまま)。``lines`` は線の名(昇順)・``line_idx`` はその索引。
  - `load_rail_events`(関数): 資産の置き場から発着の表を読む。``enabled`` を省くと :data:`READ_RAIL_EVENTS`(既定 False=読まずに ``None``)。
- import している内部モジュール: `shibuya.core.time_consts`
- 読む試験: `tests/build_rail/test_w12_arrivals_2_3c.py`

## [runner.py](../../../../../../../../src/shibuya/engine/processes/runner.py)

engine.processes.runner — 世界過程の実行器(台帳 → 実装の唯一の橋)。

- 公開の関数とクラス
  - `WorldProcessRunner`(クラス): 世界過程 第1陣(前半)の実行器。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.core.time_consts`・`shibuya.engine.absent_processes`・`shibuya.engine.calendar`・`shibuya.engine.events.links`・`shibuya.engine.processes.civic`・`shibuya.engine.processes.crowd`・`shibuya.engine.processes.environment`・`shibuya.engine.processes.goods_flow`・`shibuya.engine.processes.logistics`・`shibuya.engine.processes.opening`・`shibuya.engine.processes.rail`・`shibuya.engine.processes.salient`・`shibuya.engine.processes.traffic`・`shibuya.engine.rate_rules`・`shibuya.engine.resolve`・`shibuya.engine.rights.initial`・`shibuya.engine.rights.record`・`shibuya.world.assets`・`shibuya.world.processes.actual_log`・`shibuya.world.processes.first_batch`・`shibuya.world.state`
- 呼び手: `shibuya.engine.processes`・`shibuya.engine.systems.build`
- 読む試験: `tests/engine/events/test_e_log_links_actual.py`・`tests/engine/events/test_e_vocab_is_closed.py`・`tests/engine/processes/test_absent_processes_1102.py`・`tests/engine/processes/test_runner.py`・`tests/engine/test_calendar_sites.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_weather_calendar_10e.py`
- 状態台帳の行
  - 持ち主 `runner`(`WorldProcessRunner`)
    - `O73` 世界の過程と実行器の計数(挙動 diag・復元 discardable) 道筋 `runner.n_steps`・`runner.phase_seconds` 書ける系: close_final・day_close・day_head・duties・phase_c・plan_boundary・presence・world
- 決定の ID: 11-01・11-02r/§1・11-02r/§1 #7・D-52・D-61・D-66・第 304・第 305・第 330

## [salient.py](../../../../../../../../src/shibuya/engine/processes/salient.py)

engine.processes.salient — 顕著行為(人物③)と ``p_notice`` の結線。

- 公開の関数とクラス
  - `SalientEvent`(クラス): 1 件の顕著行為。
  - `SalientProcess`(クラス): 顕著行為の生成・``p_notice`` による到達判定・B4 行の組み立て。
  - `ablation_name`(関数): ``p_notice`` の ablation → ``"A0"``…``"A4"``(manifest の同定欄・§3.1)。
  - `build_salient_feed`(関数): ``SalientEvent`` の列 → ``Renderer.prepare_tick(salient_events=…)`` の形。
  - `check_d50_scale`(関数): ``d50_scale`` の検査(ablation ②)。正の有限値だけ許す。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.core.rng`・`shibuya.core.time_consts`・`shibuya.engine.body.model`・`shibuya.engine.body.rules`・`shibuya.engine.rate_rules`・`shibuya.engine.resolve`・`shibuya.perception.attention`・`shibuya.perception.p_notice`・`shibuya.perception.state`・`shibuya.world.state`
- 呼び手: `shibuya.engine.processes.runner`・`shibuya.engine.systems.build`・`shibuya.engine.systems.report`
- 読む試験: `tests/engine/body/test_body_same_values.py`・`tests/engine/processes/test_absent_processes_1102.py`・`tests/engine/processes/test_rate_rules_1101.py`・`tests/engine/processes/test_rng_scheme_10c.py`・`tests/engine/processes/test_salient.py`・`tests/engine/test_ablation23_switches.py`
- 状態台帳の行
  - 持ち主 `runner.salient`(`SalientProcess`)
    - `O46` SalientProcess rng・event_seen_tick・budget(挙動 behavior・復元 required) 道筋 `runner.salient.budget`・`runner.salient.event_seen_tick`・`runner.salient.rng` 書ける系: day_head・phase_c・wake_sources・world
    - `O72` SalientProcess の計数(挙動 diag・復元 discardable) 道筋 `runner.salient.n_broadcast_lines`・`runner.salient.n_collapse`・`runner.salient.n_events`・`runner.salient.n_noticed`・`runner.salient.n_over_cap` 書ける系: close_final・day_close・phase_c・wake_sources・world
- 決定の ID: 11-01・11-01/§2・D-113・第 267・第 330

## [traffic.py](../../../../../../../../src/shibuya/engine/processes/traffic.py)

engine.processes.traffic — 断面自動車交通(C 類 + B 類域外発生・§7.2 初回実装)。

- 公開の関数とクラス
  - `TrafficProcess`(クラス): 断面自動車交通(時間帯別)。世界状態は書かず、場を持つだけ。
- import している内部モジュール: `shibuya.core.time_consts`・`shibuya.world.assets`・`shibuya.world.state`
- 呼び手: `shibuya.engine.processes`・`shibuya.engine.processes.runner`
- 読む試験: `tests/engine/processes/test_traffic.py`
- 状態台帳の行
  - 持ち主 `runner.traffic`(`TrafficProcess`)
    - `O55` LastMile delivered・_cum/BusTaxi・Traffic(cell_hourly・cell_vehicles)・Infra(power_kwh)・Press・Opening・DeliveryInbound の計数(挙動 no・復元 derivable) 道筋 `runner.traffic.cell_hourly`・`runner.traffic.cell_vehicles` 書ける系: close_final・day_close・day_head・world
    - `O73` 世界の過程と実行器の計数(挙動 diag・復元 discardable) 道筋 `runner.traffic.daily_vehicle_km` 書ける系: close_final・day_close・day_head・duties・phase_c・plan_boundary・presence・world
