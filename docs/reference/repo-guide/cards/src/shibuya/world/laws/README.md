# src/shibuya/world/laws

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 17 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/world/laws/__init__.py)

(冒頭の説明なし)

## [civic.py](../../../../../../../../src/shibuya/world/laws/civic.py)

engine.processes.civic — 公共サービス出動・報道/公式発信・大規模イベント・ホテル・インフラ。

- 公開の関数とクラス
  - `HotelProcess`(クラス): ホテル客室在庫(来街者のチェックイン・アウト)。
  - `InfraLoadProcess`(クラス): インフラ日負荷(電力・水)の集約。**報告のみ**(網は持たない)。
  - `LargeEventProcess`(クラス): 大規模イベント(会場の開催・旧道は外界からの来街増分を窓の間だけ入れる)。
  - `PressProcess`(クラス): 報道・公式発信(固定時刻の放送)。1 行を作る。届けるのは在席者のいるセルだけ(``salient._broadcast_events``)。
  - `PublicServiceDispatchProcess`(クラス): 公共サービス出動(救急・警察)。「倒れる」事象を受けて出動し、到着で解消する。
- import している内部モジュール: `shibuya.act.ops.rail`・`shibuya.foundation.rng`・`shibuya.foundation.text.salience`・`shibuya.foundation.time_consts`・`shibuya.foundation.vocab.agent_codes`・`shibuya.world.laws.switch_absent`・`shibuya.world.laws.switch_rate`・`shibuya.world.ledger.records`・`shibuya.world.model.agent_table`・`shibuya.world.model.assets`・`shibuya.world.model.state`
- 呼び手: `shibuya.world.laws.runner`
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

## [crowd.py](../../../../../../../../src/shibuya/world/laws/crowd.py)

engine.processes.crowd — 混雑場・流れ・屋内占有・待ち行列(D-R2-5 第1陣 + §7.2 初回実装)。

- 公開の関数とクラス
  - `CrowdProcess`(クラス): 密度・流れ(人物①)と屋内占有・待ち行列(人物②)の集約。
  - `seats_for_categories`(関数): POI カテゴリ列 → 席数(容量 c)。**全部 expedient**(16行表 行2)。
- import している内部モジュール: `shibuya.act.ops.shop`・`shibuya.foundation.vocab.agent_codes`・`shibuya.world.model.agent_table`・`shibuya.world.model.state`
- 呼び手: `shibuya.runtime.systems.assemble`・`shibuya.world.laws.runner`
- 読む試験: `tests/engine/processes/test_crowd.py`・`tests/engine/test_area_source_c9c.py`・`tests/engine/test_defect_fixes_1103.py`・`tests/engine/test_env_and_sections_10f.py`
- 状態台帳の行
  - 持ち主 `runner.crowd`(`CrowdProcess`)
    - `O51` CrowdProcess queue_action(挙動 behavior・復元 required) 道筋 `runner.crowd.queue_action` 書ける系: close_final・day_close・day_head・phase_c・plan_boundary・presence・world
    - `O73` 世界の過程と実行器の計数(挙動 diag・復元 discardable) 道筋 `runner.crowd.n_balked`・`runner.crowd.n_released`・`runner.crowd.peak_occupancy`・`runner.crowd.peak_queue` 書ける系: close_final・day_close・day_head・duties・phase_c・plan_boundary・presence・world
    - `O75` CrowdProcess occupancy・queue_len・flow(挙動 behavior・復元 unknown) 道筋 `runner.crowd.flow`・`runner.crowd.occupancy`・`runner.crowd.queue_len` 書ける系: close_final・day_close・day_head・phase_c・plan_boundary・presence・world
    - `O95` CrowdProcess flow_dir8・coherence(8 方位と向きのそろい)(挙動 diag・復元 unknown) 道筋 `runner.crowd.coherence`・`runner.crowd.flow_dir8` 書ける系: close_final・day_close・day_head・world
- 決定の ID: R-8・D-113・第 263・第 268・第 347

## [environment.py](../../../../../../../../src/shibuya/world/laws/environment.py)

engine.processes.environment — 昼夜・天候・体感温度(D-R2-5 第1陣の 1-2 行目)。

- 公開の関数とクラス
  - `EnvironmentProcess`(クラス): 昼夜(``daynight_solar``)+ 天候・体感温度(``weather``)。
  - `WeatherWarning`(クラス): 10e(B6): 天気の規則の警告(層を広げた・暦の日付の影が無く近い日の影を読んだ)。
  - `calendar_candidates`(関数): 10e(B6): 季節 × 平日/土休 の W13 の行(昇順の索引)と、広げた段(``""``=広げていない)。
  - `nearest_shadow_date`(関数): 10e(B6): ``target`` にいちばん近い影の日(同じ近さなら前の日)。影が無ければ ``None``。
  - `sample_calendar_day`(関数): 10e(B6): 季節 × 平日/土休 × 天候型の層から、窓の中で実際に起きた日数の割合で再生日を引く。
- import している内部モジュール: `shibuya.act.ops.law_writes`・`shibuya.foundation.hashing`・`shibuya.foundation.rng`・`shibuya.foundation.time_consts`・`shibuya.world.body.model`・`shibuya.world.body.rules`・`shibuya.world.facts.calendar`・`shibuya.world.model.agent_table`・`shibuya.world.model.assets`・`shibuya.world.model.solar`・`shibuya.world.model.state`
- 呼び手: `shibuya.runtime.systems.assemble`・`shibuya.world.laws.runner`
- 読む試験: `tests/engine/body/test_body_same_values.py`・`tests/engine/experiment/_x33.py`・`tests/engine/experiment/test_x33_apply.py`・`tests/engine/multiday/test_md23_w9_window.py`・`tests/engine/processes/test_environment.py`・`tests/engine/test_activation_10e.py`・`tests/engine/test_activation_2_4.py`・`tests/engine/test_assets_10e_b0_b1.py`・`tests/engine/test_calendar_sites.py`・`tests/engine/test_salt_seed_split_10f.py`・`tests/engine/test_weather_calendar_10e.py`・`tests/perception/test_weather_a48.py`
- 読む試験(道筋で): `tests/engine/body/test_body_guard.py`
- 状態台帳の行
  - 持ち主 `runner.environment`(`EnvironmentProcess`)
    - `O56` EnvironmentProcess replay_date・stratum・_row・_shade(挙動 behavior・復元 derivable) 道筋 `runner.environment._row`・`runner.environment._shade`・`runner.environment.replay_date`・`runner.environment.stratum` 書ける系: close_final・day_close・day_head・experiment・world
    - `O73` 世界の過程と実行器の計数(挙動 diag・復元 discardable) 道筋 `runner.environment.n_updates`・`runner.environment.shadow_missing` 書ける系: close_final・day_close・day_head・duties・phase_c・plan_boundary・presence・world
    - `O76` EnvironmentProcess daylight・heat_stage・wbgt(挙動 behavior・復元 derivable) 道筋 `runner.environment.daylight`・`runner.environment.heat_stage`・`runner.environment.wbgt` 書ける系: close_final・day_close・day_head・world
- 決定の ID: 第 330

## [goods_flow.py](../../../../../../../../src/shibuya/world/laws/goods_flow.py)

engine.processes.goods_flow — 物の流れ(§7.2 初回実装の後半 + 前倒し 1 本)。

- 公開の関数とクラス
  - `DeliveryInboundProcess`(クラス): 納品(早朝帯・**納品ドライバー行動**)。未陳列の納品枠(バックヤード)を積む。
  - `ShelfRestockProcess`(クラス): 店舗補充・棚在庫(**店員 T0 行動** + conf 宣言つき engine_rule フォールバック)。
  - `StreetCleaningProcess`(クラス): 街路清掃(セル別のごみストックが密度で増え、シフトで掃かれる)。
  - `WasteCollectionProcess`(クラス): 廃棄物収集(店舗ビン → bbox 外)+ C 類排出(売れ残り・世帯消費)。
- import している内部モジュール: `shibuya.act.ops.law_writes`・`shibuya.foundation.journal.log`・`shibuya.foundation.rng`・`shibuya.foundation.time_consts`・`shibuya.foundation.vocab.agent_codes`・`shibuya.world.laws.switch_absent`・`shibuya.world.laws.switch_rate`・`shibuya.world.ledger.records`・`shibuya.world.model.agent_table`・`shibuya.world.model.state`
- 呼び手: `shibuya.interim_bundles.duties.layer`・`shibuya.world.laws.runner`
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

## [logistics.py](../../../../../../../../src/shibuya/world/laws/logistics.py)

engine.processes.logistics — 宅配ラストマイル・バス/タクシー・道路工事(§7.2 前倒し)。

- 公開の関数とクラス
  - `BusTaxiProcess`(クラス): バス・タクシー運行(等間隔 PlanSpec + 停留所への到着イベント)。
  - `LastMileProcess`(クラス): 宅配ラストマイル(世帯数按分 × 時間帯カーブ)。
  - `RoadWorksProcess`(クラス): 道路工事・占用(夜間の PlanSpec)。
- import している内部モジュール: `shibuya.foundation.rng`・`shibuya.foundation.time_consts`・`shibuya.world.laws.switch_absent`・`shibuya.world.laws.switch_rate`・`shibuya.world.ledger.records`・`shibuya.world.model.assets`・`shibuya.world.model.state`
- 呼び手: `shibuya.world.laws.runner`
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

## [opening.py](../../../../../../../../src/shibuya/world/laws/opening.py)

engine.processes.opening — 営業時間 PlanSpec と役割行動「開閉店」(D-R2-5 第1陣の 6 行目)。

- 公開の関数とクラス
  - `OpeningProcess`(クラス): 営業時間 PlanSpec の実績確定(役割行動 + conf 宣言つきフォールバック)。
  - `build_open_matrix`(関数): W7 の区間 → ``(n_poi, 1440)`` の開閉行列(日跨ぎは同じ日へ巻き戻す)。
  - `rows_of_day`(関数): その日の行(曜日 0〜6・祝日 ``PH_ROW``)に当たる W7 の区間の真偽の列。
- import している内部モジュール: `shibuya.act.ops.law_writes`・`shibuya.foundation.time_consts`・`shibuya.foundation.types`・`shibuya.foundation.vocab.agent_codes`・`shibuya.world.facts.calendar`・`shibuya.world.facts.rights.initial`・`shibuya.world.facts.rights.ledger`・`shibuya.world.facts.rights.record`・`shibuya.world.ledger.records`・`shibuya.world.model.agent_table`・`shibuya.world.model.assets`・`shibuya.world.model.state`
- 呼び手: `shibuya.interim_bundles.calendar2.layer`・`shibuya.interim_bundles.calendar3.layer`・`shibuya.runtime.run`・`shibuya.world.laws.runner`
- 読む試験: `tests/build_rail/test_w12_arrivals_2_3c.py`・`tests/engine/experiment/_x33.py`・`tests/engine/experiment/test_x33_apply.py`・`tests/engine/experiment/test_x33_branch.py`・`tests/engine/processes/test_goods_flow.py`・`tests/engine/processes/test_opening.py`・`tests/engine/rights/test_rights_events.py`・`tests/engine/rights/test_rights_manifest.py`・`tests/engine/rights/test_staff_of_poi_equivalence.py`・`tests/engine/test_calendar_10e_e3.py`・`tests/engine/test_calendar_sites.py`・`tests/engine/test_state_checks_10f.py`・`tests/engine/time/test_t0_time_consts.py`
- 状態台帳の行
  - 持ち主 `runner.opening`(`OpeningProcess`)
    - `O73` 世界の過程と実行器の計数(挙動 diag・復元 discardable) 道筋 `runner.opening.n_events`・`runner.opening.n_fallback`・`runner.opening.n_role_actions`・`runner.opening.n_unauthorized` 書ける系: close_final・day_close・day_head・duties・phase_c・plan_boundary・presence・world
- 決定の ID: 10-12/§1-1・第 330

## [presence.py](../../../../../../../../src/shibuya/world/laws/presence.py)

engine.presence — 計画実行層(Presence & Plan Executor・D-66 第1段)。

- 公開の関数とクラス
  - `EventType`(クラス): 日次イベントの種(設計書 §3 の表)。値は表の番号。
  - `PlanExecutor`(クラス): 計画実行層(D-66 第1段)。日次でイベント列を組み、tick ごとに resolve を叩く。
- import している内部モジュール: `shibuya.act.ops.plan_writes`・`shibuya.act.ops.rail`・`shibuya.act.ops.shop`・`shibuya.foundation.time_consts`・`shibuya.foundation.vocab.act_codes`・`shibuya.foundation.vocab.agent_codes`・`shibuya.world.facts.weekly_reader`・`shibuya.world.laws.presence_plan`・`shibuya.world.laws.switch_rate`・`shibuya.world.model.agent_table`・`shibuya.world.model.state`
- 呼び手: `shibuya.interfaces.cli.run_args`・`shibuya.interim_bundles.calendar_self`・`shibuya.runtime.systems.assemble`・`tools/instruments/anchor_gauge.py`
- 読む試験: `tests/engine/_legacy_world.py`・`tests/engine/calendar/test_ca1b_runs.py`・`tests/engine/processes/test_rate_rules_1101.py`・`tests/engine/test_calendar_10e_e3.py`・`tests/engine/test_presence_executor.py`・`tests/engine/test_presence_exit_walk.py`・`tests/engine/test_resume_10d.py`
- 読む試験(道筋で): `tests/economy/cp2/test_cp2_transfer_only_writer.py`・`tests/engine/body/test_body_guard.py`
- 状態台帳の行
  - 持ち主 `presence`(`PlanExecutor`)
    - `O35` PlanExecutor 退出の歩行 _walk_since・_walk_line・_plan_rider・_rewalked・_rewalk_*(挙動 behavior・復元 required) 道筋 `presence._plan_rider`・`presence._rewalk_deadline`・`presence._rewalk_ids`・`presence._rewalk_line`・`presence._rewalked`・`presence._walk_line`・`presence._walk_since` 書ける系: close_final・day_close・day_head・decide・plan_boundary・presence・world
    - `O36` PlanExecutor _defer_ids・_defer_deadline・_defer_line・_defer_walk・_extra・_skip_depart_at(挙動 behavior・復元 required) 道筋 `presence._defer_deadline`・`presence._defer_ids`・`presence._defer_line`・`presence._defer_walk`・`presence._extra`・`presence._skip_depart_at` 書ける系: close_final・day_close・day_head・plan_boundary・presence・world
    - `O37` PlanExecutor _pulled_in_today(挙動 diag・復元 required) 道筋 `presence._pulled_in_today` 書ける系: close_final・day_close・day_head・plan_boundary・presence・world
    - `O38` PlanExecutor ev_*・arrival_*・absent・blocks(挙動 no・復元 derivable) 道筋 `presence.absent`・`presence.arrival_cell`・`presence.arrival_tick`・`presence.arrival_train`・`presence.arrival_train_e1`・`presence.blocks`・`presence.ev_act`・`presence.ev_agent`・`presence.ev_arg`・`presence.ev_place`・`presence.ev_tick`・`presence.ev_type` 書ける系: close_final・day_close・day_head・plan_boundary・presence
    - `O70` PlanExecutor の計数と時別の控え(挙動 diag・復元 discardable) 道筋 `presence.exit_cell_by_hour`・`presence.exit_stage_max_by_hour`・`presence.fallback_minutes`・`presence.in_area_by_hour`・`presence.lost_why`・`presence.match_in_den`・`presence.match_in_num`・`presence.match_out_den`・`presence.match_out_num`・`presence.n_arrivals`・`presence.n_arrive_skipped`・`presence.n_arrive_skipped_in_area`・`presence.n_arrive_skipped_pulled`・`presence.n_depart_dropped`・`presence.n_depart_skipped`・`presence.n_departed_by_llm`・`presence.n_departures`・`presence.n_exit_deferred`・`presence.n_exit_forced`・`presence.n_exit_gate_immediate`・`presence.n_exit_lost`・`presence.n_exit_lost_deferred`・`presence.n_exit_lost_final`・`presence.n_exit_no_platform`・`presence.n_exit_rewalk_forced`・`presence.n_exit_rewalk_gone`・`presence.n_exit_rewalk_queued`・`presence.n_exit_rewalk_started`・`presence.n_exit_too_far`・`presence.n_exit_walk_boarded`・`presence.n_exit_walk_departed`・`presence.n_exit_walk_gone`・`presence.n_exit_walk_restarted`・`presence.n_exit_walk_started`・`presence.n_exit_walk_waiting_at_start`・`presence.n_gate_arrivals`・`presence.n_home_out_slept_inside`・`presence.n_placed_at_start`・`presence.n_pulled_in`・`presence.n_pushed_out`・`presence.n_queue_balked`・`presence.n_rearmed`・`presence.n_returned_to_block`・`presence.n_shopping_interrupted`・`presence.n_spread_moved`・`presence.n_spread_overflow`・`presence.n_walk_calls`・`presence.n_walk_wakes_suppressed`・`presence.platform_cell_by_hour`・`presence.sample_hours`・`presence.sample_in_area`・`presence.sleep_counts`・`presence.wake_in_area_by_hour`・`presence.walk_minutes` 書ける系: close_final・day_close・day_head・decide・observe・plan_boundary・presence・wake_filter・world
- 決定の ID: 11-01・11-01/§2・11-02・D-51・D-61・D-62・D-66・D-115・第 145・第 302・第 330

## [presence_plan.py](../../../../../../../../src/shibuya/world/laws/presence_plan.py)

world.laws.presence_plan — 割る段で ``engine/presence.py`` を割った割り先(全ファイルの表 §4・名の表は``tools/pkgmove/map.toml`` の割る行)。

- 公開の関数とクラス
  - `PlanBlocks`(クラス): **在圏ブロック**(その体がその日「舞台に居る」連続区間)の CSR。
- import している内部モジュール: `shibuya.world.facts.weekly_reader`
- 呼び手: `shibuya.interfaces.cli.run_args`・`shibuya.interim_bundles.calendar_self`・`shibuya.runtime.systems.assemble`・`shibuya.world.laws.presence`・`tools/instruments/anchor_gauge.py`
- 読む試験: `tests/engine/test_geometry_c9.py`・`tests/engine/test_presence_derive_v2.py`・`tests/engine/test_presence_executor.py`
- 決定の ID: 11-01・第 170

## [rail.py](../../../../../../../../src/shibuya/world/laws/rail.py)

engine.processes.rail — 鉄道運行(ODPT 静的ダイヤ・D-R2-5 第1陣の 3 行目)。

- 公開の関数とクラス
  - `RailProcess`(クラス): 静的ダイヤで列車を進め、乗車・降車の前提条件と混雑率受容を持つ世界過程。
- import している内部モジュール: `shibuya.act.ops.rail`・`shibuya.foundation.journal.log`・`shibuya.foundation.ports.ledger`・`shibuya.foundation.rng`・`shibuya.world.facts.calendar`・`shibuya.world.laws.switch_rate`・`shibuya.world.ledger.records`・`shibuya.world.model.agent_table`・`shibuya.world.model.assets`・`shibuya.world.model.state`
- 呼び手: `shibuya.world.laws.runner`
- 読む試験: `tests/economy/cp2/test_cp2_transfer_only_writer.py`・`tests/economy/stage2/test_stage2_money_rules.py`・`tests/engine/processes/test_rail.py`・`tests/engine/processes/test_rail_board_intent.py`・`tests/engine/processes/test_rail_return.py`・`tests/engine/processes/test_rate_rules_1101.py`・`tests/engine/test_calendar_sites.py`・`tests/engine/test_defect_fixes_1103.py`・`tests/engine/test_presence_executor.py`・`tests/engine/test_presence_exit_walk.py`
- 状態台帳の行
  - 持ち主 `runner.rail`(`RailProcess`)
    - `O50` RailProcess occupancy・peak_ratio・_return_queue・_inbound・_inbound_ready(挙動 behavior・復元 required) 道筋 `runner.rail._inbound`・`runner.rail._inbound_ready`・`runner.rail._return_queue`・`runner.rail.occupancy`・`runner.rail.peak_ratio` 書ける系: close_final・day_close・day_head・phase_c・plan_boundary・presence・world
    - `O73` 世界の過程と実行器の計数(挙動 diag・復元 discardable) 道筋 `runner.rail.n_arrivals`・`runner.rail.n_board_applicants`・`runner.rail.n_board_dropped`・`runner.rail.n_board_intent`・`runner.rail.n_board_timeout`・`runner.rail.n_board_unreachable`・`runner.rail.n_board_waiting`・`runner.rail.n_board_waiting_plan_exit`・`runner.rail.n_board_walking`・`runner.rail.n_boarded_from_queue`・`runner.rail.n_boarded_plan_exit`・`runner.rail.n_departed_riders`・`runner.rail.n_departures`・`runner.rail.n_fare_rejected`・`runner.rail.n_left_behind`・`runner.rail.n_left_behind_by_rate`・`runner.rail.n_no_return`・`runner.rail.n_return_arrived`・`runner.rail.n_return_no_train`・`runner.rail.n_return_scheduled` 書ける系: close_final・day_close・day_head・duties・phase_c・plan_boundary・presence・world
    - `O74` RailProcess arrival_train・external_line(帰りの便の予約印・域外居住者の路線)(挙動 behavior・復元 required) 道筋 `runner.rail.arrival_train`・`runner.rail.external_line` 書ける系: close_final・day_close・day_head・phase_c・world
- 決定の ID: 11-01・11-01/§2・D-51・D-61・D-66・D-115・第 302

## [rail_events.py](../../../../../../../../src/shibuya/world/laws/rail_events.py)

engine.processes.rail_events — 渋谷の発着の表(W12 1.3.0)を読む口の器(第 2 期 2-3c・**既定は読まない**)。

- 公開の関数とクラス
  - `RailEventsAsset`(クラス): 発着の表の SoA(行の順は資産のまま)。``lines`` は線の名(昇順)・``line_idx`` はその索引。
  - `load_rail_events`(関数): 資産の置き場から発着の表を読む。``enabled`` を省くと :data:`READ_RAIL_EVENTS`(既定 False=読まずに ``None``)。
- import している内部モジュール: `shibuya.foundation.time_consts`
- 読む試験: `tests/build_rail/test_w12_arrivals_2_3c.py`
- 決定の ID: 11-16/§1-3

## [runner.py](../../../../../../../../src/shibuya/world/laws/runner.py)

engine.processes.runner — 世界過程の実行器(台帳 → 実装の唯一の橋)。

- 公開の関数とクラス
  - `WorldProcessRunner`(クラス): 世界過程 第1陣(前半)の実行器。
- import している内部モジュール: `shibuya.act.ops.rail`・`shibuya.foundation.journal.links`・`shibuya.foundation.time_consts`・`shibuya.world.facts.calendar`・`shibuya.world.facts.rights.initial`・`shibuya.world.facts.rights.record`・`shibuya.world.laws.civic`・`shibuya.world.laws.crowd`・`shibuya.world.laws.environment`・`shibuya.world.laws.goods_flow`・`shibuya.world.laws.logistics`・`shibuya.world.laws.opening`・`shibuya.world.laws.rail`・`shibuya.world.laws.salient`・`shibuya.world.laws.switch_absent`・`shibuya.world.laws.switch_rate`・`shibuya.world.laws.traffic`・`shibuya.world.ledger.actual_log`・`shibuya.world.ledger.first_batch`・`shibuya.world.model.agent_table`・`shibuya.world.model.assets`・`shibuya.world.model.state`
- 呼び手: `shibuya.runtime.systems.assemble`
- 読む試験: `tests/engine/_legacy_world.py`・`tests/engine/events/test_e_log_links_actual.py`・`tests/engine/events/test_e_vocab_is_closed.py`・`tests/engine/processes/test_absent_processes_1102.py`・`tests/engine/processes/test_runner.py`・`tests/engine/test_calendar_sites.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_weather_calendar_10e.py`
- 状態台帳の行
  - 持ち主 `runner`(`WorldProcessRunner`)
    - `O73` 世界の過程と実行器の計数(挙動 diag・復元 discardable) 道筋 `runner.n_steps`・`runner.phase_seconds` 書ける系: close_final・day_close・day_head・duties・phase_c・plan_boundary・presence・world
- 決定の ID: 11-01・11-02r/§1・11-02r/§1 #7・D-52・D-61・D-66・第 304・第 305・第 330

## [salient.py](../../../../../../../../src/shibuya/world/laws/salient.py)

engine.processes.salient — 顕著行為(人物③)と ``p_notice`` の結線。

- 公開の関数とクラス
  - `SalientEvent`(クラス): 1 件の顕著行為。
  - `SalientProcess`(クラス): 顕著行為の生成・``p_notice`` による到達判定・B4 行の組み立て。
  - `ablation_name`(関数): ``p_notice`` の ablation → ``"A0"``…``"A4"``(manifest の同定欄・§3.1)。
  - `build_salient_feed`(関数): ``SalientEvent`` の列 → ``Renderer.prepare_tick(salient_events=…)`` の形。
  - `check_d50_scale`(関数): ``d50_scale`` の検査(ablation ②)。正の有限値だけ許す。
- import している内部モジュール: `shibuya.act.ops.law_writes`・`shibuya.foundation.rng`・`shibuya.foundation.text.salience`・`shibuya.foundation.time_consts`・`shibuya.foundation.vocab.agent_codes`・`shibuya.world.body.model`・`shibuya.world.body.rules`・`shibuya.world.laws.switch_rate`・`shibuya.world.model.agent_table`・`shibuya.world.model.notice_reach`・`shibuya.world.model.percept_state`・`shibuya.world.model.state`
- 呼び手: `shibuya.runtime.systems.assemble`・`shibuya.runtime.systems.report`・`shibuya.world.laws.runner`
- 読む試験: `tests/engine/body/test_body_same_values.py`・`tests/engine/processes/test_absent_processes_1102.py`・`tests/engine/processes/test_rate_rules_1101.py`・`tests/engine/processes/test_rng_scheme_10c.py`・`tests/engine/processes/test_salient.py`・`tests/engine/test_ablation23_switches.py`
- 状態台帳の行
  - 持ち主 `runner.salient`(`SalientProcess`)
    - `O46` SalientProcess rng・event_seen_tick・budget(挙動 behavior・復元 required) 道筋 `runner.salient.budget`・`runner.salient.event_seen_tick`・`runner.salient.rng` 書ける系: day_head・phase_c・wake_sources・world
    - `O72` SalientProcess の計数(挙動 diag・復元 discardable) 道筋 `runner.salient.n_broadcast_lines`・`runner.salient.n_collapse`・`runner.salient.n_events`・`runner.salient.n_noticed`・`runner.salient.n_over_cap` 書ける系: close_final・day_close・phase_c・wake_sources・world
- 決定の ID: 11-01・11-01/§2・D-113・第 267・第 330

## [switch_absent.py](../../../../../../../../src/shibuya/world/laws/switch_absent.py)

engine.absent_processes — 「無い」と宣言した世界過程 5 件を止める切替口(指示書 11-02 返事その 2 §1 #7・小さな版上げ 1 回分)。

- 公開の関数とクラス
  - `check_resume`(関数): 再開のときに、保存したランの見出しの ``absent_processes``(無ければ legacy=版上げの前のラン)が既定の stopped かを
  - `header_fields`(関数): 状態のファイルの見出しの ``absent_processes``(legacy のランは書かない=None=版上げの前の見出しのまま)。
  - `is_legacy`(関数): ``mode``(省略=既定 stopped)が旧道(5 件の過程を動かす)か。
  - `manifest_fields`(関数): manifest の ``absent_processes``(設定=形の版・腕・過程の宣言・止めた印/観測=旧道の件数)。
  - `resolve`(関数): 過程の引数の腕(``None``=既定 stopped。〔第347〕ランの切替口は消した)を名に直す(名の誤りは止める)。
  - `stopped_flags`(関数): 過程ごとの ``absent_<名>_stopped``(1=止めた・0=旧道)。腕だけで決まる印(設定)。
- import している内部モジュール: `shibuya.foundation.arms.removed`
- 呼び手: `shibuya.runtime.systems.assemble`・`shibuya.runtime.systems.report`・`shibuya.runtime.systems.state_io`・`shibuya.world.laws.civic`・`shibuya.world.laws.goods_flow`・`shibuya.world.laws.logistics`・`shibuya.world.laws.runner`
- 読む試験: `tests/bridging/test_drives_from_vs_scoring.py`・`tests/engine/processes/test_absent_processes_1102.py`
- 環境変数: `SHIBUYA_ABSENT_PROCESSES`
- 決定の ID: 10-13b/§0-6・11-01/§2・11-02・11-02r・11-02r #7・11-02r/§1・11-02r/§1 #7・11-02r/§1 #8・11-02r/§2-2・第 347

## [switch_rate.py](../../../../../../../../src/shibuya/world/laws/switch_rate.py)

engine.rate_rules — 率の形の規則を外す切替口(指示書 11-01 段 2 の 3・4・回答 11-01 §2・§3・小さな版上げ 1 回分)。

- 公開の関数とクラス
  - `check_resume`(関数): 再開のときに、保存したランの見出しの ``rate_rules``(無ければ legacy=版上げの前のラン)が既定の off かを確かめる
  - `header_fields`(関数): 状態のファイルの見出しの ``rate_rules``(legacy のランは書かない=None=版上げの前の見出しのまま)。
  - `is_legacy`(関数): ``mode``(省略=既定 off)が旧道(率の形の規則を動かす)か。
  - `manifest_fields`(関数): manifest の ``rate_rules``(設定=形の版・腕・規則の宣言・外した印/観測=旧道の件数)。
  - `removed_flags`(関数): 規則ごとの ``rate_rule_<名>_removed``(1=外した・0=旧道)。腕だけで決まる印(設定)。
  - `resolve`(関数): 過程の引数の腕(``None``=既定 off。〔第347〕ランの切替口は消した)を名に直す(名の誤りは止める)。
- import している内部モジュール: `shibuya.foundation.arms.removed`
- 呼び手: `shibuya.interfaces.cli.wire_economy`・`shibuya.runtime.systems.assemble`・`shibuya.runtime.systems.report`・`shibuya.runtime.systems.state_io`・`shibuya.world.laws.civic`・`shibuya.world.laws.goods_flow`・`shibuya.world.laws.logistics`・`shibuya.world.laws.presence`・`shibuya.world.laws.rail`・`shibuya.world.laws.runner`・`shibuya.world.laws.salient`
- 読む試験: `tests/bridging/test_drives_from_vs_scoring.py`・`tests/engine/processes/test_rate_rules_1101.py`・`tests/engine/test_waste_sink_report.py`
- 環境変数: `SHIBUYA_RATE_RULES`
- 決定の ID: 10-13b/§0-6・11-01・11-01/§2・第 347

## [switch_seat.py](../../../../../../../../src/shibuya/world/laws/switch_seat.py)

engine.seat_release — 在席の印を歩き出しで解く(第 2 期 2-4 V3・版上げ 2 回目)の見出しと再開の検査。

- 公開の関数とクラス
  - `check_resume`(関数): 再開のときに、保存したランの見出しの ``seat_release``(無ければ legacy=2-4 より前のラン)が walk かを確かめる(違えば止める)。
  - `header_fields`(関数): 状態のファイルの見出しの ``seat_release``(ランは常に ``{"mode": "walk"}``・walk の外の名は None)。
- import している内部モジュール: `shibuya.foundation.arms.removed`
- 呼び手: `shibuya.runtime.systems.assemble`・`shibuya.runtime.systems.state_io`
- 読む試験: `tests/engine/test_seat_release_2_4.py`
- 環境変数: `SHIBUYA_SEAT_RELEASE`
- 決定の ID: 第 346

## [traffic.py](../../../../../../../../src/shibuya/world/laws/traffic.py)

engine.processes.traffic — 断面自動車交通(C 類 + B 類域外発生・§7.2 初回実装)。

- 公開の関数とクラス
  - `TrafficProcess`(クラス): 断面自動車交通(時間帯別)。世界状態は書かず、場を持つだけ。
- import している内部モジュール: `shibuya.foundation.time_consts`・`shibuya.world.model.assets`・`shibuya.world.model.state`
- 呼び手: `shibuya.world.laws.runner`
- 読む試験: `tests/engine/processes/test_traffic.py`
- 状態台帳の行
  - 持ち主 `runner.traffic`(`TrafficProcess`)
    - `O55` LastMile delivered・_cum/BusTaxi・Traffic(cell_hourly・cell_vehicles)・Infra(power_kwh)・Press・Opening・DeliveryInbound の計数(挙動 no・復元 derivable) 道筋 `runner.traffic.cell_hourly`・`runner.traffic.cell_vehicles` 書ける系: close_final・day_close・day_head・world
    - `O73` 世界の過程と実行器の計数(挙動 diag・復元 discardable) 道筋 `runner.traffic.daily_vehicle_km` 書ける系: close_final・day_close・day_head・duties・phase_c・plan_boundary・presence・world
