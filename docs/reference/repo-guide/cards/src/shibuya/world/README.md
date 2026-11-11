# src/shibuya/world

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 6 本・その他 0 本(このディレクトリの直下)

下のディレクトリ: [processes](processes/README.md)

## [__init__.py](../../../../../../../src/shibuya/world/__init__.py)

world: セル/POI/歩行グラフ/可視性(mmap)/騒音場。core に依存。

- import している内部モジュール: `shibuya.world.assets`・`shibuya.world.graph`・`shibuya.world.state`
- 読む試験(道筋で): `tests/test_places_guard.py`・`tests/tools/test_pkgmove.py`

## [assets.py](../../../../../../../src/shibuya/world/assets.py)

world.assets — 世界データ資産(W1/W2/W3/W6)の読み込みと、CI 用の合成小世界。

- 公開の関数とクラス
  - `ProcessAssets`(クラス): 世界過程(C4 第1陣)が読む静的資産。**全欄が空でも動く**(合成世界)。
  - `WorldAssets`(クラス): 実行時 NumPy に落とした世界資産(不変)。
  - `array_sha256`(関数): 配列の並び(dtype・形・中身)の sha256。10e(B0): 騒音の集約後のセル別の段の補助の指紋。
  - `assets_available`(関数): 資産ディレクトリに必要な 6 ファイルが揃っているか。
  - `check_area_source`(関数): 歩行可能面積の出所の検査(``run_day`` が**資産を読む前**に呼ぶ=manifest が嘘をつかない)。
  - `file_sha256`(関数): ファイルの中身の sha256(16 進・1 MiB ずつ読む)。10e(B0): manifest の ``frozen_sources`` に書く値。
  - `hash_free_cat_code`(関数): カテゴリ名 → 0..2 の価格帯コード(**決定論・ハッシュを使わない**)。
  - `load_assets`(関数): ``data/world/v2`` の資産を読む(W1/W2/W3/W6・騒音は W10)。
  - `load_poi_own_cell_visibility`(関数): W8 → POI ごとの「**自分のセルの視点から見える数**」(``(n_poi,)`` int32・無ければ 0)。
  - `load_process_assets`(関数): ``data/world/v2`` から世界過程(C4 第1陣)の資産を読む。
  - `load_process_assets_or_synthetic`(関数): 資産があれば読み、無ければ空の ``ProcessAssets``(全過程が休む)。
  - `load_visible_pois_by_cell`(関数): W8 → セルごとの「そのセルの視点から見えている POI」(CSR)。
  - `load_walkable_area_m2`(関数): ``c9c_walkable_area.parquet`` → ``place_ids`` の順に並べた歩行可能面積[m²]。
  - `synthetic_assets`(関数): CI 用の合成小世界(1 セル=1 ノードの 4 近傍格子)。
- import している内部モジュール: `shibuya.core.rng`・`shibuya.core.time_consts`
- 呼び手: `shibuya.cli`・`shibuya.engine.change_detect`・`shibuya.engine.geometry`・`shibuya.engine.poi_target`・`shibuya.engine.processes.civic`・`shibuya.engine.processes.environment`・`shibuya.engine.processes.logistics`・`shibuya.engine.processes.opening`・`shibuya.engine.processes.rail`・`shibuya.engine.processes.runner`・`shibuya.engine.processes.traffic`・`shibuya.engine.run`・`shibuya.engine.systems.build`・`shibuya.perception.renderer`・`shibuya.world`・`shibuya.world.graph`・`shibuya.world.state`
- 読む試験: `tests/_data_ids.py`・`tests/economy/test_entry_capital.py`・`tests/engine/duties/_du.py`・`tests/engine/experiment/test_x33_branch.py`・`tests/engine/processes/conftest.py`・`tests/engine/processes/test_absent_processes_1102.py`・`tests/engine/processes/test_civic.py`・`tests/engine/processes/test_environment.py`・`tests/engine/processes/test_goods_flow.py`・`tests/engine/processes/test_logistics.py`・`tests/engine/processes/test_opening.py`・`tests/engine/processes/test_rail.py`・`tests/engine/processes/test_traffic.py`・`tests/engine/rights/test_staff_of_poi_equivalence.py`・`tests/engine/test_activation_2_4.py`・`tests/engine/test_area_source_c9c.py`・`tests/engine/test_assets_10e_b0_b1.py`・`tests/engine/test_calendar_10e_e3.py`・`tests/engine/test_calendar_sites.py`・`tests/engine/test_geometry_c9.py`・`tests/engine/test_intent_chooser.py`・`tests/engine/test_presence_executor.py`・`tests/engine/test_processes_run.py`・`tests/engine/test_waste_sink_report.py`・`tests/engine/test_weather_calendar_10e.py`・`tests/perception/facts/head_renderer_136fdbb.py`・`tests/world/test_world.py`
- 読む試験(道筋で): `tests/engine/test_state_ledger_10b.py`・`tests/engine/test_two_phase.py`・`tests/test_places_guard.py`
- 決定の ID: 11-03・11-03/§2・D-66・D-84・D-96・D-112・D-114・第 330

## [graph.py](../../../../../../../src/shibuya/world/graph.py)

world.graph — 歩行グラフと next-hop 経路(ベクトル化)。

- 公開の関数とクラス
  - `WalkGraph`(クラス): 歩行グラフ(不変)。``WorldAssets`` の薄いビュー。
- import している内部モジュール: `shibuya.world.assets`
- 呼び手: `shibuya.world`・`shibuya.world.state`
- 読む試験(道筋で): `tests/engine/test_two_phase.py`

## [navmesh.py](../../../../../../../src/shibuya/world/navmesh.py)

world.navmesh — 段 1 のナビメッシュ(多層の歩ける面)の資産と、その上の問い合わせ(numba・SR13=自前)。

- 公開の関数とクラス
  - `NavMesh`(クラス): 段 1 のナビメッシュ(不変)。配列は numba にそのまま渡す。
  - `area_by_cell`(関数): セルごとの歩ける面積[m²]\(ランを 100 m の列の境で切って足す=重ならない)。
  - `astar_strips`(関数): 帯の A*(入った点から次の門の中点までの距離+``climb_w``×上り)。
  - `cell_lookup_table`(関数): W2 のセル → 引き表 ``lut[iy-cy0, ix-cx0, band+1]``(セルの番号・無ければ -1)と原点 ``(cx0, cy0)``。
  - `cell_of`(関数): (x, y, 層) → セルの番号。その層のセルが無ければ地上のセル・それも無ければ -1(11c の ``cell_band`` の向きの逆)。
  - `corridor_portals`(関数): 同じ階の帯の列(``strip_seq[0..n_seq)``)→ 門の左右の点の列(帯の中の行ごとの門+帯と帯の間の門)。
  - `dem_z`(関数): DEM の格子から双線形で標高[m]\(格子の外は端の値)。
  - `funnel_points`(関数): simple stupid funnel(R-59 ``measure_navmesh.funnel`` の核を門の配列で受ける形に移した)。
  - `load_navmesh`(関数): ``nav1_*`` を読む。``verify`` なら ``nav1_meta.json`` の sha256 と照らす(違えば ``ValueError``)。
  - `locate_run`(関数): (階の添字, x, y) → ラン(無ければ -1)。行の中は二分探索。
  - `navmesh_available`(関数): 置き場にナビメッシュの資産が全部あるか。
  - `nearest_point`(関数): 階の中で (x, y) に最も近い歩ける点(ランの長方形を目の幅の 1/1000 だけ内へ寄せた中)。
  - `w1_turn_dijkstra`(関数): W1 の向きつきの辺(状態)の Dijkstra(重み=長さ+``climb_w``×上り+曲がる 1 回 ``turn_w``)。
- 呼び手: `shibuya.build.space.navmesh1`・`shibuya.engine.space.nav1`・`shibuya.world.navmesh_route`
- 読む試験: `tests/build_space/test_navmesh1_units.py`・`tests/engine/space/test_nav1_density.py`・`tests/engine/space/test_nav1_units.py`・`tests/engine/space/test_nav1_world.py`
- 読む試験(道筋で): `tests/engine/test_state_ledger_10b.py`
- 決定の ID: R-59・R-61

## [navmesh_route.py](../../../../../../../src/shibuya/world/navmesh_route.py)

world.navmesh_route — ナビメッシュの上の経路の形を引く道具(W1 の通り道 → 帯の A* → funnel)。

- 公開の関数とクラス
  - `NavPlanner`(クラス): 経路の形を引く道具(作業の配列を持つ=1 つのランで 1 つ・決定論=同点は番号の小さい方)。
  - `RouteGeom`(クラス): 1 本の経路の形(``engine.space.nav1`` が時間を載せる)。
- import している内部モジュール: `shibuya.world.navmesh`
- 呼び手: `shibuya.engine.space.nav1`
- 読む試験: `tests/build_space/test_navmesh1_units.py`
- 決定の ID: R-59・R-61

## [state.py](../../../../../../../src/shibuya/world/state.py)

world.state — セル/POI の状態レジストリ(SoA)と世界オブジェクト ``World``。

- 公開の関数とクラス
  - `World`(クラス): 世界状態(セル・POI)+不変資産(グラフ)。
  - `check_eatery_mode`(関数): ``eatery`` の値を検査して返す(``EATERY_MODES`` のどれか)。
- import している内部モジュール: `shibuya.core.hashing`・`shibuya.core.soa`・`shibuya.core.time_consts`・`shibuya.core.write_permit`・`shibuya.world.assets`・`shibuya.world.graph`
- 呼び手: `shibuya.cli`・`shibuya.engine.change_detect`・`shibuya.engine.geometry`・`shibuya.engine.poi_target`・`shibuya.engine.presence`・`shibuya.engine.processes.civic`・`shibuya.engine.processes.crowd`・`shibuya.engine.processes.environment`・`shibuya.engine.processes.goods_flow`・`shibuya.engine.processes.logistics`・`shibuya.engine.processes.opening`・`shibuya.engine.processes.rail`・`shibuya.engine.processes.runner`・`shibuya.engine.processes.salient`・`shibuya.engine.processes.traffic`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.engine.space.nav1`・`shibuya.engine.systems.build`・`shibuya.perception.renderer`・`shibuya.world`・`tools/c6/ablation1_fixed_vs_ranking.py`・`tools/c6/run_hash.py`・`tools/c7/occupancy_series.py`
- 読む試験: `tests/build_lang/test_wiring.py`・`tests/build_pop/test_pop_pipeline.py`・`tests/c6/test_t5_order_bias.py`・`tests/c6/test_t9_diagnostics.py`・`tests/economy/cp2/test_cp2_flow_sum.py`・`tests/economy/cp2/test_cp2_k17_capacity_and_overflow.py`・`tests/economy/cp2/test_cp2_writes_declared.py`・`tests/economy/stage2/test_stage2_calls.py`・`tests/economy/stage2/test_stage2_resume_arm.py`・`tests/economy/stage2/test_stage2_rules_credit_atm.py`・`tests/economy/stage2/test_stage2_runs.py`・`tests/economy/test_rules42_runs.py`・`tests/economy/test_rules42b_ledger.py`・`tests/engine/body/test_system1_placeholders.py`・`tests/engine/calendar2/_ca2.py`・`tests/engine/clock/test_tm3_step_scope.py`・`tests/engine/clock/test_tm4_regional_clock.py`・`tests/engine/contact/_c1.py`・`tests/engine/contact/_c2.py`・`tests/engine/duties/_du.py`・`tests/engine/experiment/test_x33_branch.py`・`tests/engine/memory/test_m0_store_schema.py`・`tests/engine/processes/conftest.py`・`tests/engine/processes/test_logistics.py`・`tests/engine/processes/test_rail.py`・`tests/engine/rights/test_staff_of_poi_equivalence.py`・`tests/engine/space/test_nav1_density.py`・`tests/engine/speech/test_speech_on_reaches_addressee.py`・`tests/engine/systems/test_stage_a_guard.py`・`tests/engine/test_10a_review_fixes.py`・`tests/engine/test_ablation23_switches.py`・`tests/engine/test_add_at_guard.py`・`tests/engine/test_area_source_c9c.py`・`tests/engine/test_c9b_targets_attention.py`・`tests/engine/test_calendar_sites.py`・`tests/engine/test_change_detect_p6.py`・`tests/engine/test_classical_policy.py`・`tests/engine/test_classical_social.py`・`tests/engine/test_conversation_invite.py`・`tests/engine/test_defect_fixes_1103.py`・`tests/engine/test_determinism_t1_t2_t4.py`・`tests/engine/test_eatery_place_food.py`・`tests/engine/test_energy_balance.py`・`tests/engine/test_familiarity.py`・`tests/engine/test_fleet_wiring.py`・`tests/engine/test_geometry_c9.py`・`tests/engine/test_intent_chooser.py`・`tests/engine/test_l4_budget.py`・`tests/engine/test_ledger_wiring.py`・`tests/engine/test_meal_bundle_2b.py`・`tests/engine/test_meal_gate_per_hour.py`・`tests/engine/test_memory_recall.py`・`tests/engine/test_move_destination.py`・`tests/engine/test_norm_meter.py`・`tests/engine/test_plan_sleep_d62.py`・`tests/engine/test_presence_executor.py`・`tests/engine/test_presence_exit_walk.py`・`tests/engine/test_processes_run.py`・`tests/engine/test_relations.py`・`tests/engine/test_renderer_wiring.py`・`tests/engine/test_resolve.py`・`tests/engine/test_response_delay.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_seat_release_2_4.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_sleep_suppression_d56.py`・`tests/engine/test_state_ledger_10b.py`・`tests/engine/test_store_choice.py`・`tests/engine/test_t3_manifest.py`・`tests/engine/test_tape_deferred.py`・`tests/engine/test_tape_wiring.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/test_two_phase.py`・`tests/engine/test_version_bump_10e.py`・`tests/engine/test_vocab_v2_eat.py`・`tests/engine/test_waste_sink_report.py`・`tests/engine/test_weather_calendar_10e.py`・`tests/engine/test_wom.py`・`tests/llm/test_fleet_contract.py`・`tests/perception/facts/head_renderer_136fdbb.py`・`tests/perception/facts/scenes.py`・`tests/perception/facts/test_percept_is_scratch.py`・`tests/perception/test_ablation1.py`・`tests/perception/test_ablation6_signage.py`・`tests/perception/test_b4_detector_gap.py`・`tests/perception/test_b4b_queue_feed.py`・`tests/perception/test_b6_invite.py`・`tests/perception/test_intent_mode_open.py`・`tests/perception/test_near_tiebreak.py`・`tests/perception/test_nearby_vectorized.py`・`tests/perception/test_p_see_activity.py`・`tests/perception/test_renderer_golden.py`・`tests/perception/test_signage_p_see_gate.py`・`tests/perception/test_templates.py`・`tests/perception/test_vocab_v2_templates.py`・`tests/test_cli.py`・`tests/world/test_world.py`
- 読む試験(道筋で): `tests/engine/systems/test_fix_guards.py`
- 状態台帳の行
  - SoA の列 `cells`
    - `cells.b4_hash` b4_hash(挙動 no・復元 derivable) 書ける系: detect
    - `cells.density` density(挙動 behavior・復元 derivable) 書ける系: build・phase_c
    - `cells.density_stage` density_stage(挙動 behavior・復元 derivable) 書ける系: build・phase_c
    - `cells.noise_stage` noise_stage(挙動 behavior・復元 derivable) 書ける系: (宣言なし)
    - `cells.open_count` open_count(挙動 no・復元 derivable) 書ける系: build・phase_c
  - SoA の列 `pois`
    - `pois.capacity` capacity(挙動 behavior・復元 derivable) 書ける系: (宣言なし)
    - `pois.cell` cell(挙動 behavior・復元 derivable) 書ける系: (宣言なし)
    - `pois.node` node(挙動 behavior・復元 derivable) 書ける系: (宣言なし)
    - `pois.open_from` open_from(挙動 behavior・復元 derivable) 書ける系: (宣言なし)
    - `pois.open_now` open_now(挙動 behavior・復元 required) 書ける系: duties・world
    - `pois.open_to` open_to(挙動 behavior・復元 derivable) 書ける系: (宣言なし)
    - `pois.price` price(挙動 behavior・復元 derivable) 書ける系: (宣言なし)
    - `pois.revenue` revenue(挙動 diag・復元 required) 書ける系: phase_c
    - `pois.stock` stock(挙動 behavior・復元 required) 書ける系: duties・phase_c・world
- 決定の ID: D-96
