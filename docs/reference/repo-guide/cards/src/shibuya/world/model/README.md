# src/shibuya/world/model

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 11 本・その他 0 本(このディレクトリの直下)

下のディレクトリ: [space](space/README.md)

## [__init__.py](../../../../../../../../src/shibuya/world/model/__init__.py)

(冒頭の説明なし)

- 読む試験(道筋で): `tests/tools/test_pkgmove.py`

## [geometry.py](../../../../../../../../src/shibuya/world/model/geometry.py)

engine.geometry — C9 位置幾何(辺上の連続位置・歩行速度)の**切替口**。

- 公開の関数とクラス
  - `EdgeGeometry`(クラス): 辺上の連続位置(G1 (b))と歩行速度(G2 (b))の**前計算した表**+解析式。
  - `check_geometry`(関数): 幾何モードの検査(``run_day`` が**世界を作る前**に呼ぶ=manifest が嘘をつかない)。
  - `desired_speeds`(関数): 個体の希望歩行速度[m/s]\(**seed と agent_id だけの決定論**・float32)。
  - `kladek_speed_factor`(関数): 密度 → 自由速度に対する比 ``v/v0``(Kladek/Weidmann・**解析式 1 本**)。
- import している内部モジュール: `shibuya.engine.change_detect`・`shibuya.foundation.rng`・`shibuya.world.assets`・`shibuya.world.model.state`
- 呼び手: `shibuya.cli`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.engine.systems.build`・`shibuya.world.model.space.nav1`
- 読む試験: `tests/build_pop/test_w21_stage8_9.py`・`tests/engine/space/test_nav1_density.py`・`tests/engine/space/test_nav1_units.py`・`tests/engine/test_area_source_c9c.py`・`tests/engine/test_c9b_targets_attention.py`・`tests/engine/test_geometry_c9.py`・`tests/engine/test_salt_seed_split_10f.py`

## [graph.py](../../../../../../../../src/shibuya/world/model/graph.py)

world.graph — 歩行グラフと next-hop 経路(ベクトル化)。

- 公開の関数とクラス
  - `WalkGraph`(クラス): 歩行グラフ(不変)。``WorldAssets`` の薄いビュー。
- import している内部モジュール: `shibuya.world.assets`
- 呼び手: `shibuya.world.model.state`
- 読む試験(道筋で): `tests/engine/test_two_phase.py`

## [navmesh.py](../../../../../../../../src/shibuya/world/model/navmesh.py)

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
- 呼び手: `shibuya.build.space.navmesh1`・`shibuya.world.model.navmesh_route`・`shibuya.world.model.space.nav1`
- 読む試験: `tests/build_space/test_navmesh1_units.py`・`tests/engine/space/test_nav1_density.py`・`tests/engine/space/test_nav1_units.py`・`tests/engine/space/test_nav1_world.py`
- 読む試験(道筋で): `tests/engine/test_state_ledger_10b.py`
- 決定の ID: R-59・R-61

## [navmesh_route.py](../../../../../../../../src/shibuya/world/model/navmesh_route.py)

world.navmesh_route — ナビメッシュの上の経路の形を引く道具(W1 の通り道 → 帯の A* → funnel)。

- 公開の関数とクラス
  - `NavPlanner`(クラス): 経路の形を引く道具(作業の配列を持つ=1 つのランで 1 つ・決定論=同点は番号の小さい方)。
  - `RouteGeom`(クラス): 1 本の経路の形(``engine.space.nav1`` が時間を載せる)。
- import している内部モジュール: `shibuya.world.model.navmesh`
- 呼び手: `shibuya.world.model.space.nav1`
- 読む試験: `tests/build_space/test_navmesh1_units.py`
- 決定の ID: R-59・R-61

## [notice_reach.py](../../../../../../../../src/shibuya/world/model/notice_reach.py)

perception.p_notice — 人物③「顕著な行為」への確率的到達(知覚契約書 §3.1・案B 2段ヒル型)。

- 公開の関数とクラス
  - `Ablation`(クラス): §3.1 の ablation A0-A4(A4=完成形)。
  - `Counters`(クラス): 診断行に出す計数(§6 運用規定「診断行に常設」)。
  - `DensityClass`(クラス): 密度クラス(``m_density`` の索引)。
  - `EventBudget`(クラス): 顕著イベントの 1 tick 上限(§3.1「顕著イベント上限200/tick(宣言値)」)。
  - `NoticeResult`(クラス): 1イベント×候補群の結果。
  - `PNoticeParams`(クラス): §3.1 の係数一式(ablation で振るのはこの dataclass を差し替える)。
  - `TaskLoad`(クラス): 課題従事フラグ(M12 の 1 byte)。〔第 1 期 1-2〕負荷の係数は消した=値は事実として残す(心の向きの仕組みの入力の候補)。
  - `combine`(関数): ``p = 1 − (1−P1')(1−P2)``。
  - `eccentricity_deg`(関数): 事象方向と視線方向の角度差 ``|E_ang|``[度・0..180]。
  - `heading_to_degrees`(関数): 量子化された向き(0..sectors-1 の uint8)→ 度[0,360)。セクタ0 = +x 方向。
  - `notice_event`(関数): 1つの顕著イベントについて、候補群の「気づいた/気づかない」を引く(§3.1)。
  - `p1_primary`(関数): TTPF 一次検出 ``P1``。``d50_eff=0``(背後)は 0 を返す(〔1-2〕負荷の係数 ``m_load`` は消した)。
  - `p2_social`(関数): 社会伝播 ``P2 = a·N^b/(n50^b + N^b)``(N=0 なら 0)。
  - `social_counts`(関数): 各点の半径 ``radius_m`` 内にある「既に気づいた点」の数(自分自身は数えない)。
- import している内部モジュール: `shibuya.foundation.rng`
- 呼び手: `shibuya.world.laws.salient`・`shibuya.world.model.percept_state`
- 読む試験: `tests/engine/processes/test_salient.py`・`tests/engine/space/test_nav1_units.py`・`tests/engine/test_ablation23_switches.py`・`tests/engine/test_processes_run.py`・`tests/perception/facts/test_coef_removed_or_armed.py`・`tests/perception/test_p_notice.py`
- 決定の ID: 10-12/§1-6

## [percept_state.py](../../../../../../../../src/shibuya/world/model/percept_state.py)

perception.state — 知覚側が持つ個体 SoA(予算行 **M12** と prefix 抑止の前回ハッシュ)。

- 公開の関数とクラス
  - `PerceptionState`(クラス): 知覚側の個体 SoA。
  - `heading_from_vector`(関数): 進行方向ベクトル → 量子化された向き(0..sectors-1 の uint8)。
- import している内部モジュール: `shibuya.foundation.soa`・`shibuya.foundation.write_permit`・`shibuya.world.model.notice_reach`
- 呼び手: `shibuya.world.laws.salient`
- 読む試験: `tests/engine/systems/test_stage_a_guard.py`・`tests/engine/test_state_ledger_10b.py`・`tests/perception/test_hashes_state.py`
- 読む試験(道筋で): `tests/engine/systems/test_fix_guards.py`
- 状態台帳の行
  - SoA の列 `perception`
    - `perception.heading` heading(挙動 no・復元 derivable) 書ける系: world
    - `perception.invocation_distance` invocation_distance(挙動 no・復元 discardable・死蔵) 書ける系: (宣言なし)
    - `perception.task_flag` task_flag(挙動 no・復元 derivable) 書ける系: world
- 決定の ID: D-102

## [proximity.py](../../../../../../../../src/shibuya/world/model/proximity.py)

engine.proximity — 会話と近接を実距離で判定する(第 2 期 2-2・段 11a)。

- 公開の関数とクラス
  - `NearView`(クラス): 描画の前計算に渡す物(規則・この刻みの索引・気づいた印の読み口)。
  - `ProximityLayer`(クラス): 腕 ``distance`` の層(判定の規則・計器・気づいた印の読み口)。組み立てが作る(既定の distance で作る・旧道の cell では作らない=None)。
  - `ProximityRule`(クラス): 腕 ``distance`` の判定の規則(組み立てで 1 回作る・ランの間は変えない)。``seed``=動きの側の seed。
  - `batch_partners`(関数): 適用の束 ``batch`` の中で、``rows``(束の中の位置)の体に届く束の体のうち並びの鍵が最小の体(届く体が無ければ −1)。
  - `check_resume`(関数): 再開のときに、保存したランの腕(見出しの ``proximity``・無ければ cell=2-2 までのラン)と今の腕が同じかを確かめる
  - `d`(関数): いまの会話の距離 d[m]\(ランの近接の規則=``distance`` の距離)。
  - `header_fields`(関数): 状態のファイルの見出しの ``proximity``(層の無い物は書かない=None・ランは常に層を持つ)。
  - `manifest_fields`(関数): manifest の ``proximity``(層の無い物は観測の子が null・ランは常に層を持つ=mode は distance)。
  - `marks_for`(関数): 「暫定」の印(B6・B8)。B6 は位置の出どころ(node と edge の幾何は立っている体は node・nav1 は面の上の点)・B8 は
  - `notice_p`(関数): R-62 の 2 点を通るロジスティック p(d)(距離[m] → 気づく確率)。
  - `rule_from`(関数): 組み立ての口(``seed``=動きの側の seed=気づく抽選の counter の流れの鍵・``poi_cell``=``world.pois.cell``・
  - `set_d`(関数): 会話の距離 d の感度の腕を選ぶ(CLI ``--proximity-d``・試験の切替口)。
- import している内部モジュール: `shibuya.engine.removed_switches`・`shibuya.foundation.rng`・`shibuya.world.model.spatial_index`
- 呼び手: `shibuya.cli`・`shibuya.engine.commit`・`shibuya.engine.relations`・`shibuya.engine.run`・`shibuya.engine.systems.build`・`shibuya.engine.systems.state_io`
- 読む試験: `tests/engine/proximity/test_rule.py`・`tests/engine/proximity/test_runs.py`・`tests/engine/proximity/test_switch_sites.py`・`tests/engine/space/test_nav1_units.py`・`tests/perception/facts/test_render_from_percept_bytes.py`
- 読む試験(道筋で): `tests/engine/test_state_ledger_10b.py`
- 状態台帳の行
  - 持ち主 `proximity`(`ProximityLayer`)
    - `PX` ProximityLayer(近接の層の計器・第 2 期 2-2 段 11a)(挙動 diag・復元 discardable) 道筋 `proximity._meter` 書ける系: perceive_prepare
- 環境変数: `SHIBUYA_PROXIMITY`・`SHIBUYA_PROXIMITY_D`
- 決定の ID: 10-03/§4・10-13b/§0-3・R-62・R-79・第 346

## [solar.py](../../../../../../../../src/shibuya/world/model/solar.py)

engine.solar — 太陽の位置(日の出・日の入り・太陽高度)と WBGT の推定(10e B6・第330)。

- 公開の関数とクラス
  - `daylight_phase`(関数): 日照の 3 値(構築段の ``daylight_phase`` と同じ規則)。
  - `heat_stage`(関数): WBGT → 暑さ段(0〜4)。
  - `hourly_wbgt`(関数): ``date`` の太陽高度(時の中ほど)と、その時の気象(再生日の行)から WBGT の推定値(丸めない)。
  - `solar_elevation_deg`(関数): 地方時 ``local_min``(0 時からの分)の太陽高度 [deg]。
  - `sun_minutes`(関数): 日の出・日の入りを**分に丸めた値**(W13 の ``sunrise``/``sunset`` 列の ``HH:MM`` と同じ丸め=``round``)。
  - `sun_times`(関数): 日の出・日の入り(地方時の 0 時からの分)。極夜・白夜は ``(None, None)``。
  - `wbgt_estimate`(関数): WBGT の推定式(屋外・実況が無いときの代わり=expedient)。
- import している内部モジュール: `shibuya.foundation.time_consts`
- 呼び手: `shibuya.world.laws.environment`
- 読む試験: `tests/engine/test_weather_calendar_10e.py`
- 決定の ID: 第 330

## [spatial_index.py](../../../../../../../../src/shibuya/world/model/spatial_index.py)

engine.spatial_index — 近傍の索引(第 2 期 2-2 段 11a・セル廃止の役割 ①「近傍の索引」の最初の部品)。

- 公開の関数とクラス
  - `SpatialIndex`(クラス): 近傍の索引(層ごとの ``cell_m`` の格子・刻みごとに作って捨てる・組み立ての後は読むだけ)。
  - `expand_ranges`(関数): 範囲 ``[lo, hi)`` の並び → (範囲の番号, 位置)(``np.repeat`` の形・ループなし)。
- 呼び手: `shibuya.world.model.proximity`
- 読む試験: `tests/engine/proximity/test_index.py`

## [state.py](../../../../../../../../src/shibuya/world/model/state.py)

world.state — セル/POI の状態レジストリ(SoA)と世界オブジェクト ``World``。

- 公開の関数とクラス
  - `World`(クラス): 世界状態(セル・POI)+不変資産(グラフ)。
  - `check_eatery_mode`(関数): ``eatery`` の値を検査して返す(``EATERY_MODES`` のどれか)。
- import している内部モジュール: `shibuya.foundation.hashing`・`shibuya.foundation.soa`・`shibuya.foundation.time_consts`・`shibuya.foundation.write_permit`・`shibuya.world.assets`・`shibuya.world.model.graph`
- 呼び手: `shibuya.cli`・`shibuya.engine.change_detect`・`shibuya.engine.poi_target`・`shibuya.engine.presence`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.engine.systems.build`・`shibuya.perception.renderer`・`shibuya.world.laws.civic`・`shibuya.world.laws.crowd`・`shibuya.world.laws.environment`・`shibuya.world.laws.goods_flow`・`shibuya.world.laws.logistics`・`shibuya.world.laws.opening`・`shibuya.world.laws.rail`・`shibuya.world.laws.runner`・`shibuya.world.laws.salient`・`shibuya.world.laws.traffic`・`shibuya.world.model.geometry`・`shibuya.world.model.space.nav1`・`tools/c6/ablation1_fixed_vs_ranking.py`・`tools/c6/run_hash.py`・`tools/c7/occupancy_series.py`
- 読む試験: `tests/build_lang/test_wiring.py`・`tests/build_pop/test_pop_pipeline.py`・`tests/c6/test_t5_order_bias.py`・`tests/c6/test_t9_diagnostics.py`・`tests/economy/cp2/test_cp2_flow_sum.py`・`tests/economy/cp2/test_cp2_k17_capacity_and_overflow.py`・`tests/economy/cp2/test_cp2_writes_declared.py`・`tests/economy/stage2/test_stage2_calls.py`・`tests/economy/stage2/test_stage2_resume_arm.py`・`tests/economy/stage2/test_stage2_rules_credit_atm.py`・`tests/economy/stage2/test_stage2_runs.py`・`tests/economy/test_rules42_runs.py`・`tests/economy/test_rules42b_ledger.py`・`tests/engine/body/test_system1_placeholders.py`・`tests/engine/calendar2/_ca2.py`・`tests/engine/clock/test_tm3_step_scope.py`・`tests/engine/clock/test_tm4_regional_clock.py`・`tests/engine/contact/_c1.py`・`tests/engine/contact/_c2.py`・`tests/engine/duties/_du.py`・`tests/engine/experiment/test_x33_branch.py`・`tests/engine/memory/test_m0_store_schema.py`・`tests/engine/processes/conftest.py`・`tests/engine/processes/test_logistics.py`・`tests/engine/processes/test_rail.py`・`tests/engine/rights/test_staff_of_poi_equivalence.py`・`tests/engine/space/test_nav1_density.py`・`tests/engine/speech/test_speech_on_reaches_addressee.py`・`tests/engine/systems/test_stage_a_guard.py`・`tests/engine/test_10a_review_fixes.py`・`tests/engine/test_ablation23_switches.py`・`tests/engine/test_add_at_guard.py`・`tests/engine/test_area_source_c9c.py`・`tests/engine/test_c9b_targets_attention.py`・`tests/engine/test_calendar_sites.py`・`tests/engine/test_change_detect_p6.py`・`tests/engine/test_classical_policy.py`・`tests/engine/test_classical_social.py`・`tests/engine/test_conversation_invite.py`・`tests/engine/test_defect_fixes_1103.py`・`tests/engine/test_determinism_t1_t2_t4.py`・`tests/engine/test_eatery_place_food.py`・`tests/engine/test_energy_balance.py`・`tests/engine/test_familiarity.py`・`tests/engine/test_fleet_wiring.py`・`tests/engine/test_geometry_c9.py`・`tests/engine/test_intent_chooser.py`・`tests/engine/test_l4_budget.py`・`tests/engine/test_ledger_wiring.py`・`tests/engine/test_meal_bundle_2b.py`・`tests/engine/test_meal_gate_per_hour.py`・`tests/engine/test_memory_recall.py`・`tests/engine/test_move_destination.py`・`tests/engine/test_norm_meter.py`・`tests/engine/test_plan_sleep_d62.py`・`tests/engine/test_presence_executor.py`・`tests/engine/test_presence_exit_walk.py`・`tests/engine/test_processes_run.py`・`tests/engine/test_relations.py`・`tests/engine/test_renderer_wiring.py`・`tests/engine/test_resolve.py`・`tests/engine/test_response_delay.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_seat_release_2_4.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_sleep_suppression_d56.py`・`tests/engine/test_state_ledger_10b.py`・`tests/engine/test_store_choice.py`・`tests/engine/test_t3_manifest.py`・`tests/engine/test_tape_deferred.py`・`tests/engine/test_tape_wiring.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/test_two_phase.py`・`tests/engine/test_version_bump_10e.py`・`tests/engine/test_vocab_v2_eat.py`・`tests/engine/test_waste_sink_report.py`・`tests/engine/test_weather_calendar_10e.py`・`tests/engine/test_wom.py`・`tests/llm/test_fleet_contract.py`・`tests/perception/facts/head_renderer_136fdbb.py`・`tests/perception/facts/scenes.py`・`tests/perception/facts/test_percept_is_scratch.py`・`tests/perception/test_ablation1.py`・`tests/perception/test_ablation6_signage.py`・`tests/perception/test_b4_detector_gap.py`・`tests/perception/test_b4b_queue_feed.py`・`tests/perception/test_b6_invite.py`・`tests/perception/test_intent_mode_open.py`・`tests/perception/test_near_tiebreak.py`・`tests/perception/test_nearby_vectorized.py`・`tests/perception/test_p_see_activity.py`・`tests/perception/test_renderer_golden.py`・`tests/perception/test_signage_p_see_gate.py`・`tests/perception/test_templates.py`・`tests/perception/test_vocab_v2_templates.py`・`tests/test_cli.py`・`tests/world/test_world.py`
- 読む試験(道筋で): `tests/engine/systems/test_fix_guards.py`・`tests/tools/test_pkgmove.py`
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
