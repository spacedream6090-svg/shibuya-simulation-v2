# src/shibuya/engine/systems

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 24 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/engine/systems/__init__.py)

engine.systems — ``run_day`` を「状態の箱・系(読む欄と書く欄の宣言)・短い進行役」に分けた形(第 1 期 1-0)。

## [act.py](../../../../../../../../src/shibuya/engine/systems/act.py)

engine.systems.act — 行為の解決の系(phase_a・phase_b・phase_c)(第 1 期 1-0)。

- 公開の関数とクラス
  - `sys_phase_a`(関数): phase_a(HEAD run.py の同じ区間・文は変えない)。
  - `sys_phase_b`(関数): phase_b(HEAD run.py の同じ区間・文は変えない)。
  - `sys_phase_c`(関数): phase_c(HEAD run.py の同じ区間・文は変えない)。
- import している内部モジュール: `shibuya.engine.commit`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.foundation.time_consts`
- 呼び手: `shibuya.engine.systems.table`
- 読む試験(道筋で): `tests/economy/cp2/test_cp2_transfer_only_writer.py`
- 書きの許可
  - 系 `phase_a`(群 行為の解決・時 `tick`・関数 `sys_phase_a`)
    - 呼んでよい resolve の口: `intent_kept_by`
    - 書いてよい外の道筋: `O66:act_layer.*`・`O[4-6]:intent_layer.*`
    - 書く scratch: `intents`・`llm_intents`
    - 書く計数: `layer_counts`・`peak_intents`・`phase`
  - 系 `phase_b`(群 行為の解決・時 `tick`・関数 `sys_phase_b`)
    - 書く scratch: `plan`
    - 書く計数: `phase`
  - 系 `phase_c`(群 行為の解決・時 `tick`・関数 `sys_phase_c`)
    - 呼んでよい resolve の口: `apply`
    - 書いてよい SoA の列(閉包): `agents.activity`・`agents.band`・`agents.board_line`・`agents.board_since`・`agents.cell`・`agents.edge_id`・`agents.edge_s`・`agents.energy_balance`・`agents.fatigue`・`agents.focus_target`・`agents.focus_ttl`・`agents.holdings`・`agents.hunger`・`agents.intent_action`・`agents.intent_kind`・`agents.intent_since`・`agents.intent_target`・`agents.last_action`・`agents.last_result`・`agents.last_result_tick`・`agents.money`・`agents.nav_fi`・`agents.nav_node`・`agents.nav_of`・`agents.nav_ox`・`agents.nav_oy`・`agents.nav_t`・`agents.nav_tgt`・`agents.nav_wait`・`agents.node`・`agents.path_next_node`・`agents.poi_ref`・`agents.poi_since`・`agents.queue_poi`・`agents.queue_since`・`agents.since_meal_kcal`・`agents.sleep_pending`・`agents.talk_partner`・`agents.target_node`・`agents.transit_ref`・`agents.transit_state`・`agents.xy`・`cells.density`・`cells.density_stage`・`cells.open_count`・`pois.revenue`・`pois.stock`
    - 書いてよい外の道筋: `A:ledger.*`・`E:events.*`・`EC:ledger.*`・`EM:ledger.*`・`O21:classical._gate_hazard`・`O26:poi_resolver.*`・`O2[7-9]:energy.*`・`O34:norm_meter.*`・`O46:runner.*`・`O47:runner.*`・`O48:runner.*`・`O5[0-1]:runner.*`・`O5[7-9]:ledger.*`・`O60:ledger.*`・`O66:act_layer.*`・`O7[2-5]:runner.*`・`O7[7-9]:ledger.*`・`O8[01]:ledger.*`・`O94:poi_resolver.*`・`O9[23]:ledger.*`・`O[4-6]:intent_layer.*`・`TXD:ledger.*`
    - 書く scratch: `outcome`
    - 書く計数: `geometry_hops`・`geometry_jammed`・`leave_counts`・`per_action_total`・`phase`・`result`
- 決定の ID: 11-03・D-71・D-107・第 308・第 346

## [allow.py](../../../../../../../../src/shibuya/engine/systems/allow.py)

engine.systems.allow — 系の「書いてよい SoA の列」を resolve の口の静的な閉包から作る(第 1 期 1-0・段 A)。

- 公開の関数とクラス
  - `ResolveIndex`(クラス): resolve.py の関数ごとの直接の書きと辺(静的)。
  - `closure`(関数): resolve の口の集合から、resolve.py の中でたどれる関数の全部(口そのものを含む)。
  - `index`(関数): ``RESOLVE_FILES`` を読んで関数ごとの書きと辺を作る(``root`` は ``src/shibuya``・既定はこのパッケージ)。
  - `place_of`(関数): 書きの式の手前の文字列から置き場を決める(``pois``・``cells``・``perception``・ほかは ``agents``)。
  - `src_root`(関数): ``src/shibuya`` の場所(〔移す段 2-2〕包みの根は ``core.paths`` の 1 か所)。
  - `writes_for_ops`(関数): resolve の口の集合の静的な書き集合の閉包(``"agents.cell"`` の形)。=系の ``writes.soa``。
- import している内部モジュール: `shibuya.engine.state_ledger_ast`・`shibuya.foundation.paths`
- 呼び手: `shibuya.engine.systems.spec`・`shibuya.engine.systems.static_check`
- 読む試験: `tests/economy/cp2/test_cp2_transfer_only_writer.py`・`tests/economy/stage2/test_stage2_writers.py`・`tests/engine/body/test_body_guard.py`・`tests/engine/state/test_move_prep_stage2.py`・`tests/engine/systems/test_fix_guards.py`・`tests/engine/systems/test_stage_a_guard.py`・`tests/engine/systems/test_systems_table.py`・`tests/tools/test_repo_guide.py`
- 決定の ID: 第 330

## [body.py](../../../../../../../../src/shibuya/engine/systems/body.py)

engine.systems.body — 体の系(body・presence・plan_boundary・home_meal・activity_intent・energy_after)(第 1 期 1-0)。

- 公開の関数とクラス
  - `sys_activity_intent`(関数): activity_intent(HEAD run.py の同じ区間・文は変えない)。
  - `sys_body`(関数): body(HEAD run.py の同じ区間・文は変えない)。
  - `sys_energy_after`(関数): energy_after(HEAD run.py の同じ区間・文は変えない)。
  - `sys_home_meal`(関数): home_meal(HEAD run.py の同じ区間・文は変えない)。
  - `sys_plan_boundary`(関数): plan_boundary(HEAD run.py の同じ区間・文は変えない)。
  - `sys_presence`(関数): presence(HEAD run.py の同じ区間・文は変えない)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.foundation.time_consts`・`shibuya.world.body.energy`
- 呼び手: `shibuya.engine.systems.table`
- 読む試験(道筋で): `tests/engine/body/test_body_guard.py`・`tests/engine/test_state_checks_10f.py`
- 書きの許可
  - 系 `activity_intent`(群 体・時 `tick`・立つ条件 `act_layer`・関数 `sys_activity_intent`)
    - 呼んでよい resolve の口: `clear_intent`・`fail_intent`・`relabel_intent_failure`・`set_activity`・`set_activity_until`・`set_intent`
    - 書いてよい SoA の列(閉包): `agents.activity`・`agents.activity_kind`・`agents.activity_until`・`agents.intent_action`・`agents.intent_kind`・`agents.intent_since`・`agents.intent_target`・`agents.last_action`・`agents.last_result`・`agents.last_result_tick`・`agents.target_node`
    - 書いてよい外の道筋: `O66:act_layer.*`・`O[1-3]:act_layer.*`・`O[4-6]:intent_layer.*`
  - 系 `body`(群 体・時 `tick`・関数 `sys_body`)
    - 呼んでよい resolve の口: `advance_body`・`energy_out_of_area_meal`
    - 書いてよい SoA の列(閉包): `agents.energy_balance`・`agents.fatigue`・`agents.hunger`・`agents.since_meal_kcal`
    - 書いてよい外の道筋: `BD:body.*`・`O21:classical.*`・`O2[7-9]:energy.*`・`O3[0-3]:energy.*`
  - 系 `energy_after`(群 体・時 `tick`・立つ条件 `energy`・関数 `sys_energy_after`)
    - 書いてよい外の道筋: `O28:energy.*`・`O33:energy.*`
  - 系 `home_meal`(群 体・時 `tick`・立つ条件 `home_meals`・関数 `sys_home_meal`)
    - 呼んでよい resolve の口: `energy_home_meal`
    - 書いてよい SoA の列(閉包): `agents.energy_balance`・`agents.hunger`・`agents.hunger_stage`・`agents.since_meal_kcal`
    - 書いてよい外の道筋: `O21:classical._gate_hazard`・`O2[7-9]:energy.*`・`O3[0-3]:energy.*`
  - 系 `plan_boundary`(群 体・時 `tick`・関数 `sys_plan_boundary`)
    - 呼んでよい resolve の口: `balk_queue`・`begin_exit_walk`・`begin_planned_sleep`・`rail_arrive`・`rail_depart`・`release_indoor`・`set_plan_state`・`wake_from_plan`
    - 書いてよい SoA の列(閉包): `agents.activity`・`agents.band`・`agents.board_line`・`agents.board_since`・`agents.cell`・`agents.last_result`・`agents.last_result_tick`・`agents.node`・`agents.plan_flags`・`agents.poi_ref`・`agents.poi_since`・`agents.queue_poi`・`agents.queue_since`・`agents.sleep_pending`・`agents.target_node`・`agents.transit_ref`・`agents.transit_state`・`agents.xy`
    - 書いてよい外の道筋: `O3[5-8]:presence.*`・`O5[01]:runner.*`・`O70:presence.*`・`O73:runner.*`・`O75:runner.*`
    - 書く scratch: `p_agent`・`p_class`・`p_cond`
    - 書く計数: `layer_counts`・`phase`・`sleep_counts`
  - 系 `presence`(群 体・時 `tick`・立つ条件 `presence`・関数 `sys_presence`)
    - 呼んでよい resolve の口: `balk_queue`・`begin_exit_walk`・`begin_planned_sleep`・`begin_walk_to`・`clear_board_intent`・`rail_arrive`・`rail_depart`・`release_indoor`・`set_activity`・`set_plan_state`・`wake_from_plan`
    - 書いてよい SoA の列(閉包): `agents.activity`・`agents.activity_kind`・`agents.activity_until`・`agents.band`・`agents.board_line`・`agents.board_since`・`agents.cell`・`agents.last_result`・`agents.last_result_tick`・`agents.node`・`agents.plan_flags`・`agents.poi_ref`・`agents.poi_since`・`agents.queue_poi`・`agents.queue_since`・`agents.sleep_pending`・`agents.target_node`・`agents.transit_ref`・`agents.transit_state`・`agents.xy`
    - 書いてよい外の道筋: `C1B*:calendar_self.*`・`E:events.*`・`O1:act_layer.*`・`O2:act_layer.*`・`O3[5-8]:presence.*`・`O5[01]:runner.*`・`O66:act_layer.*`・`O70:presence.*`・`O73:runner.*`・`O75:runner.*`
    - 書く計数: `layer_counts`・`phase`
- 決定の ID: D-62・D-66

## [boxes.py](../../../../../../../../src/shibuya/engine/systems/boxes.py)

engine.systems.boxes — ``run_day`` の状態の箱(第 1 期 1-0・草案 §2-3)。

- 公開の関数とクラス
  - `Box`(クラス): 状態の箱の全部(系は ``(ctx, box)`` を受け取る)。
  - `Buffers`(クラス): 使い回すバッファ(物は 1 回だけ作る・刻みの頭で空にしない=草案 R1)。
  - `DayTables`(クラス): 計画境界の表(日の頭で張り直す・HEAD の ``_relay_tables`` の nonlocal 5 つ)と W17 の曜日の代用の記録。
  - `Fixtures`(クラス): 組み立てで作り、ランの間は読むだけの物。
  - `Layers`(クラス): 状態台帳の外の状態の持ち主(名は ``hash_owners`` の鍵と同じ)。``undefined``・``run_day`` は導く。
  - `LlmIo`(クラス): LLM の往復の状態(状態台帳 O43・O44・O96・持ち主の名 ``run_day``)。``pending`` は束縛し直す(①)。
  - `RunConfig`(クラス): 検査済みの腕と値(組み立ての S0〜S1 の結果)と、ランの範囲(凍結)。
  - `RunStats`(クラス): 診断の積算・ランの結果・記録(試験のときだけ指紋に入れる=草案 §2-7)。
  - `SoAState`(クラス)
  - `TickCtx`(クラス): 系が受け取る時刻。ランの単位の系は ``T=None``(ほかの欄も ``None``)。
  - `TickScratch`(クラス): 刻みの中の受け渡し(刻みの頭で空にする)。
  - `TickScratchStrict`(クラス): 試験の番兵つき(T4): 刻みの頭で ``UNSET`` を置き、その刻みに書かれる前に読むと落ちる。
- import している内部モジュール: `shibuya.foundation.time_consts`・`shibuya.foundation.write_guard`
- 呼び手: `shibuya.engine.systems.build`・`shibuya.engine.systems.conductor`
- 読む試験: `tests/economy/stage2/test_stage2_runs.py`・`tests/engine/systems/test_boxes.py`・`tests/engine/systems/test_fix_guards.py`・`tests/engine/systems/test_systems_table.py`・`tests/engine/test_defect_fixes_1103.py`・`tests/engine/time/test_t0_rng_key.py`・`tests/engine/time/test_t0_tickctx_equivalence.py`・`tests/engine/time/test_v30a_key_sites.py`・`tests/perception/facts/test_percept_is_scratch.py`
- 決定の ID: 11-01・11-02r/§1・11-02r/§1 #7・第 346

## [build.py](../../../../../../../../src/shibuya/engine/systems/build.py)

engine.systems.build — 組み立て(R1・S0〜S8 と再開の復元)(第 1 期 1-0・段 F)。

- 公開の関数とクラス
  - `build`(関数): 組み立て(R1): 腕の検査・世界と SoA と層の組み立て・状態の箱・再開の復元。返り値=``Box``。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.economy.stage2_bind`・`shibuya.engine.activity`・`shibuya.engine.arbiter`・`shibuya.engine.calendar`・`shibuya.engine.calendar2.layer`・`shibuya.engine.calendar3.layer`・`shibuya.engine.calendar3.roster`・`shibuya.engine.calendar_self`・`shibuya.engine.calendar_shadow`・`shibuya.engine.change_detect`・`shibuya.engine.chooser`・`shibuya.engine.classical`・`shibuya.engine.commit`・`shibuya.engine.contact.layer`・`shibuya.engine.contact.tools`・`shibuya.engine.conversation`・`shibuya.engine.decision.layer`・`shibuya.engine.decision.ports`・`shibuya.engine.defect_fixes_1103`・`shibuya.engine.duties.layer`・`shibuya.engine.events.body`・`shibuya.engine.experiment.layer`・`shibuya.engine.familiarity`・`shibuya.engine.intent`・`shibuya.engine.llm_bridge`・`shibuya.engine.memory`・`shibuya.engine.memory_m1`・`shibuya.engine.memory_store`・`shibuya.engine.norm_meter`・`shibuya.engine.poi_target`・`shibuya.engine.presence`・`shibuya.engine.regional_clock`・`shibuya.engine.relations`・`shibuya.engine.removed_switches`・`shibuya.engine.resolve`・`shibuya.engine.resume`・`shibuya.engine.run`・`shibuya.engine.speech.layer`・`shibuya.engine.speech_clock`・`shibuya.engine.step_scope`・`shibuya.engine.store_choice`・`shibuya.engine.store_memory`・`shibuya.engine.systems.boxes`・`shibuya.engine.systems.state_io`・`shibuya.engine.tape`・`shibuya.engine.tools.record`・`shibuya.engine.wom`・`shibuya.foundation.arms.calendar2`・`shibuya.foundation.arms.calendar3`・`shibuya.foundation.arms.contact`・`shibuya.foundation.arms.duties`・`shibuya.foundation.decl.bridging`・`shibuya.foundation.journal.links`・`shibuya.foundation.journal.log`・`shibuya.foundation.queues.batching`・`shibuya.foundation.rng`・`shibuya.foundation.text.channels`・`shibuya.foundation.text.templates`・`shibuya.foundation.time_consts`・`shibuya.foundation.vocab.actions`・`shibuya.llm.fleet`・`shibuya.llm.mock`・`shibuya.perception.renderer`・`shibuya.world.assets`・`shibuya.world.body.energy`・`shibuya.world.body.model`・`shibuya.world.facts.mock_schedule`・`shibuya.world.facts.rights.initial`・`shibuya.world.facts.rules.table`・`shibuya.world.facts.weekly_reader`・`shibuya.world.laws.crowd`・`shibuya.world.laws.runner`・`shibuya.world.laws.salient`・`shibuya.world.laws.switch_absent`・`shibuya.world.laws.switch_rate`・`shibuya.world.laws.switch_seat`・`shibuya.world.model.geometry`・`shibuya.world.model.proximity`・`shibuya.world.model.space.nav1`・`shibuya.world.model.state`
- 呼び手: `shibuya.engine.systems.conductor`
- 読む試験: `tests/engine/bridging/test_bridging_ledger.py`・`tests/engine/clock/test_tm4_regional_clock.py`・`tests/engine/duties/_du.py`・`tests/engine/memory/test_mr65_review_fixes.py`・`tests/engine/rights/test_rights_from_w16.py`・`tests/engine/rights/test_staff_of_poi_equivalence.py`・`tests/engine/test_10a_review_fixes.py`・`tests/engine/test_fleet_wiring.py`・`tests/engine/test_pop_w21_world.py`・`tests/engine/test_sim_time_T.py`
- 読む試験(道筋で): `tests/engine/body/test_body_guard.py`・`tests/engine/calendar3/test_ca3_runs.py`・`tests/engine/rules/test_rules_table_schema.py`・`tests/engine/systems/test_boxes.py`
- 決定の ID: 10-12・10-12/§1-6・10-13b/§7・11-01・11-02r/§1・11-02r/§1 #7・11-03・11-03/§3・D-31・D-58・D-59・D-62・D-66・D-71・D-107・D-112・D-120・第 214・第 308・第 309・第 330・第 346

## [conductor.py](../../../../../../../../src/shibuya/engine/systems/conductor.py)

engine.systems.conductor — 系を呼ぶ進行役(第 1 期 1-0・草案 §2-4)。

- 公開の関数とクラス
  - `conduct`(関数): ``run_day`` の本体: 組み立て(R1)→ 窓のループ(窓の中の事象を時刻順に=刻みの事象は日の頭 D1・刻みの系・日の終わり D2)
  - `declared_check`(関数): 段 B(試験のとき): 系の前後で変わった欄 ⊆ 宣言の書く欄、を見る関数(``probe.Probe.check`` に渡す)。
  - `run_system`(関数): 系 ``spec`` を 1 回呼ぶ(``ctx`` はその刻みの ``TickCtx``・ランの単位の系は ``None``)。
  - `tick_plan`(関数): 刻みの中で呼ぶ系の並び(表の順・立たない系を外す=草案 §2-2)。〔第 2 部〕``llm_receive`` の位置 B(応答の遅れ 2=旧)の
- import している内部モジュール: `shibuya.engine.regional_clock`・`shibuya.engine.speech_clock`・`shibuya.engine.systems.boxes`・`shibuya.engine.systems.build`・`shibuya.engine.systems.day`・`shibuya.engine.systems.probe`・`shibuya.engine.systems.spec`・`shibuya.engine.systems.table`・`shibuya.foundation.arms.calendar3`・`shibuya.foundation.arms.contact`・`shibuya.foundation.queues.batching`・`shibuya.foundation.time_consts`・`shibuya.foundation.write_guard`
- 呼び手: `shibuya.engine.run`
- 読む試験: `tests/economy/cp2/test_cp2_writes_declared.py`・`tests/engine/batching/test_conductor_windows.py`・`tests/engine/body/test_system1_placeholders.py`・`tests/engine/calendar3/test_ca3_runs.py`・`tests/engine/clock/test_tm3_step_scope.py`・`tests/engine/clock/test_tm4_regional_clock.py`・`tests/engine/contact/test_c1_runs.py`・`tests/engine/decision/test_j0_writes_declared.py`・`tests/engine/events/test_e_writes_declared.py`・`tests/engine/experiment/test_x33_run.py`・`tests/engine/memory/test_m0_writes_declared.py`・`tests/engine/proximity/test_runs.py`・`tests/engine/speech/test_speech_writes_declared.py`・`tests/engine/systems/test_guard_runs.py`・`tests/engine/tools/test_c0_contacts_in_relations.py`・`tests/perception/facts/test_percept_is_scratch.py`
- 読む試験(道筋で): `tests/engine/systems/test_fix_guards.py`
- 環境変数: `SHIBUYA_SYSTEMS_CHECK`
- 決定の ID: 10-12/§4-2

## [day.py](../../../../../../../../src/shibuya/engine/systems/day.py)

engine.systems.day — 日の境目の系 day_head(D1)と day_close(D2)(第 1 期 1-0・段 F)。

- 公開の関数とクラス
  - `day_close_due`(関数): 10d: 複数日のランの途中の日の締め(1 日 1 回)。HEAD の ``if td == tpd - 1 and tick != total_ticks - 1``。
  - `day_head_due`(関数): 10d: 日の頭(1 日目から)=表の張り直しと今日の計画の写し(初期化はしない)。HEAD の ``if td == 0 and tick > 0``。
  - `sys_day_close`(関数): D2(HEAD run.py:4497-4500): 途中の日の締め(鉄道の最後の便は流さない)と、その後の状態の書き出し。
  - `sys_day_head`(関数): D1(HEAD run.py:3607-3609): 表の張り直し(``relay_tables``)と今日の計画の写し(``start_day``)。
- import している内部モジュール: `shibuya.engine.systems.state_io`
- 呼び手: `shibuya.engine.systems.conductor`・`shibuya.engine.systems.table`
- 読む試験: `tests/engine/batching/test_conductor_windows.py`
- 書きの許可
  - 系 `day_close`(群 暦・時 `day_end`・関数 `sys_day_close`)
    - 呼んでよい resolve の口: `rail_arrive`・`rail_depart`・`set_plan_state`・`sync_transit_activity`
    - 書いてよい SoA の列(閉包): `agents.activity`・`agents.band`・`agents.cell`・`agents.node`・`agents.plan_flags`・`agents.target_node`・`agents.transit_ref`・`agents.transit_state`・`agents.xy`
    - 書いてよい外の道筋: `A:ledger.*`・`C1B:calendar_self.cal_store`・`E:events.*`・`EC:ledger.*`・`EM:ledger.*`・`O2:act_layer._digest_cache`・`O3[5-8]:presence.*`・`O5[0-6]:runner.*`・`O5[7-9]:ledger.*`・`O60:ledger.*`・`O61:runner.*`・`O70:presence.*`・`O7[2-6]:runner.*`・`O7[7-9]:ledger.*`・`O8[01]:ledger.*`・`O95:runner.*`・`O9[23]:ledger.*`・`TXD:ledger.*`
    - 書く計数: `daily_records`・`result`・`state_files`
  - 系 `day_head`(群 暦・時 `day_head`・関数 `sys_day_head`)
    - 呼んでよい resolve の口: `set_plan_state`
    - 書いてよい SoA の列(閉包): `agents.plan_flags`
    - 書いてよい外の道筋: `C1B*:calendar_self.*`・`CAL:calendar_shadow.*`・`O3[5-8]:presence.*`・`O4[6-9]:runner.*`・`O5[0-6]:runner.*`・`O61:runner.*`・`O70:presence.*`・`O7[3-6]:runner.*`・`O95:runner.*`
    - 書く計数: `day_heads`

## [decide.py](../../../../../../../../src/shibuya/engine/systems/decide.py)

engine.systems.decide — 判断の系 decide(④ LLM の呼・会話ターンの発話)(第 1 期 1-0)。

- 公開の関数とクラス
  - `sys_decide`(関数): decide(HEAD run.py の同じ区間・文は変えない)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.engine.systems.llm_io`・`shibuya.foundation.rng`・`shibuya.foundation.time_consts`・`shibuya.llm.fleet`
- 呼び手: `shibuya.engine.systems.table`
- 読む試験: `tests/engine/test_state_ledger_10b.py`・`tests/perception/facts/test_percept_is_scratch.py`
- 読む試験(道筋で): `tests/engine/time/test_t0_rng_key.py`
- 書きの許可
  - 系 `decide`(群 判断・時 `tick`・LLM `send`・関数 `sys_decide`)
    - 呼んでよい resolve の口: `set_refractory`・`talk_within_reach`・`write_memory`・`write_store_memory`
    - 書いてよい SoA の列(閉包): `agents.mem_cell`・`agents.mem_importance`・`agents.mem_kind`・`agents.mem_last`・`agents.mem_n`・`agents.mem_object`・`agents.mem_partner`・`agents.mem_result`・`agents.mem_tick`・`agents.refractory_until`・`agents.sm_first`・`agents.sm_last`・`agents.sm_n`・`agents.sm_poi`・`agents.sm_precision`・`agents.sm_source`・`agents.sm_valence`
    - 書いてよい外の道筋: `BW:batching.*`・`CA2G:calendar2._turns`・`CT1G:contact._face_turns`・`CT1G:contact._look_main`・`CT1M:contact._meter`・`DUG:duties._role_asks`・`E:events.*`・`J0:decision.*`・`M0*:mem_layer.memory_store.*`・`O12:mem_layer.*`・`O15:wom.*`・`O17:rel_layer.*`・`O19:rel_layer.*`・`O1[01]:mem_layer.*`・`O2[0-4]:classical.*`・`O35:presence.*`・`O39:conv.*`・`O40:conv.*`・`O41:conv.*`・`O43:run_day.*`・`O44:run_day.*`・`O62:undefined.*`・`O69:classical.*`・`O6[34]:renderer.*`・`O70:presence.*`・`O84:renderer.*`・`O85:bridge.*`・`O86:bridge.*`・`O87:bridge.*`・`O8:mem_layer.*`・`O8[23]:undefined.*`・`O8[89]:fleet_bridge.*`・`O90:classical.*`・`O91:conv.*`・`O96:run_day.*`・`O9:mem_layer.*`・`S8:speech.*`・`S8E:speech.*`・`S8M:speech.*`・`T4W:clock.*`・`TCC:talk_clock.*`・`TCR:talk_clock.*`
    - 書く scratch: `parse_errors`・`percepts`
    - 書く計数: `calls_by_cond`・`layer_counts`・`n_fleet_resent`・`n_outside_calls`・`peak_backlog`・`peak_pending`・`phase`・`result`
- 決定の ID: D-56・D-58・D-66

## [judge.py](../../../../../../../../src/shibuya/engine/systems/judge.py)

engine.systems.judge — 判断の系(apply_responses・wake_sources・wake_filter・wake_assemble・arbiter)(第 1 期 1-0)。

- 公開の関数とクラス
  - `sys_apply_responses`(関数): apply_responses(HEAD run.py の同じ区間・文は変えない)。
  - `sys_arbiter`(関数): arbiter(HEAD run.py の同じ区間・文は変えない)。
  - `sys_wake_assemble`(関数): wake_assemble(HEAD run.py の同じ区間・文は変えない)。
  - `sys_wake_filter`(関数): wake_filter(HEAD run.py の同じ区間・文は変えない)。
  - `sys_wake_sources`(関数): wake_sources(HEAD run.py の同じ区間・文は変えない)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.arbiter`・`shibuya.engine.commit`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.foundation.hashing`・`shibuya.foundation.time_consts`
- 呼び手: `shibuya.engine.systems.table`
- 書きの許可
  - 系 `apply_responses`(群 判断・時 `tick`・関数 `sys_apply_responses`)
    - 呼んでよい resolve の口: `end_conversation`・`set_conversing`・`talk_within_reach`
    - 書いてよい SoA の列(閉包): `agents.activity`・`agents.talk_partner`
    - 書いてよい外の道筋: `O13:poi_resolver.*`・`O19:rel_layer.*`・`O2[56]:poi_resolver.*`・`O34:norm_meter.*`・`O39:conv.*`・`O40:conv.*`・`O41:conv.*`・`O43:run_day.*`・`O66:act_layer.*`・`O68:poi_resolver.*`・`O91:conv.*`・`O94:poi_resolver.*`・`O[4-6]:intent_layer.*`
    - 書く scratch: `applied_activity`・`applied_now`・`llm_intents`・`n_undefined`
    - 書く buffers: `focus_request`
    - 書く計数: `n_undefined_total`・`phase`・`talk_stats`
  - 系 `arbiter`(群 判断・時 `tick`・関数 `sys_arbiter`)
    - 書いてよい外の道筋: `O42:arbiter.*`・`O71:arbiter.*`
    - 書く scratch: `decision`・`outside_now`
    - 書く計数: `awake_sum`・`awake_ticks`・`phase`
  - 系 `wake_assemble`(群 判断・時 `tick`・関数 `sys_wake_assemble`)
    - 書く scratch: `cands`
  - 系 `wake_filter`(群 判断・時 `tick`・関数 `sys_wake_filter`)
    - 呼んでよい resolve の口: `clear_refractory`
    - 書いてよい SoA の列(閉包): `agents.refractory_until`
    - 書いてよい外の道筋: `O44:run_day.*`・`O70:presence.*`
    - 書く scratch: `det_agent`・`det_class`・`det_cond`・`e_agent`・`e_class`・`e_cond`・`f_agent`・`f_class`・`f_cond`・`f_exempt`・`f_since`・`p_agent`・`p_class`・`p_cond`
    - 書く計数: `n_fleet_reinjected`
  - 系 `wake_sources`(群 判断・時 `tick`・関数 `sys_wake_sources`)
    - 書いてよい外の道筋: `O39:conv.*`・`O41:conv.*`・`O46:runner.*`・`O72:runner.*`
    - 書く scratch: `c_agent`・`c_class`・`c_cond`・`s_agent`・`s_class`・`s_cond`
- 決定の ID: 11-03・D-56・D-62・D-66・D-107・第 308・第 346

## [llm_io.py](../../../../../../../../src/shibuya/engine/systems/llm_io.py)

engine.systems.llm_io — LLM の往復の口(会話ターンの発話・艦隊/再生の到着の受け取り)と系 llm_receive(第 1 期 1-0)。

- 公開の関数とクラス
  - `receive_arrivals`(関数): ④′ 艦隊(と再生の代役)の到着を受け取る(10a・A9)。返り値=書式エラーの件数。
  - `sys_llm_receive`(関数): 系 llm_receive(L5・L11 前半): 艦隊/再生の到着を受け取り、書式エラーの件数を scratch に置く。
  - `utter`(関数): 会話ターンの発話 1 回(``conv.utterance``)。6a: 記憶の会話の行と要旨(on のときだけ)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.llm_bridge`・`shibuya.engine.run`・`shibuya.engine.speech.layer`・`shibuya.engine.wom`・`shibuya.llm.fleet`
- 呼び手: `shibuya.engine.systems.decide`・`shibuya.engine.systems.table`
- 読む試験: `tests/engine/speech/test_wom_from_utterance_roundtrip.py`・`tests/engine/test_state_ledger_10b.py`
- 書きの許可
  - 系 `llm_receive`(群 判断・時 `tick`・LLM `receive`・関数 `sys_llm_receive`)
    - 呼んでよい resolve の口: `write_memory`・`write_store_memory`
    - 書いてよい SoA の列(閉包): `agents.mem_cell`・`agents.mem_importance`・`agents.mem_kind`・`agents.mem_last`・`agents.mem_n`・`agents.mem_object`・`agents.mem_partner`・`agents.mem_result`・`agents.mem_tick`・`agents.sm_first`・`agents.sm_last`・`agents.sm_n`・`agents.sm_poi`・`agents.sm_precision`・`agents.sm_source`・`agents.sm_valence`
    - 書いてよい外の道筋: `BW:batching.*`・`CA2G:calendar2._turns`・`CT1G:contact._face_turns`・`DUG:duties._role_asks`・`E:events.*`・`M0*:mem_layer.memory_store.*`・`O12:mem_layer.*`・`O15:wom.*`・`O1[01]:mem_layer.*`・`O39:conv.*`・`O40:conv.*`・`O41:conv.*`・`O43:run_day.*`・`O44:run_day.*`・`O62:undefined.*`・`O87:bridge.*`・`O8:mem_layer.*`・`O8[23]:undefined.*`・`O8[89]:fleet_bridge.*`・`O91:conv.*`・`O96:run_day.*`・`O9:mem_layer.*`・`S8:speech.*`・`S8E:speech.*`・`S8M:speech.*`・`T4W:clock.*`・`TCC:talk_clock.*`・`TCR:talk_clock.*`
    - 書く scratch: `n_parse_errors_fleet`
    - 書く計数: `phase`
- 決定の ID: D-58・D-120・第 294

## [observe.py](../../../../../../../../src/shibuya/engine/systems/observe.py)

engine.systems.observe — 計器の系 observe(L21+L22)と checkpoint(L23)(第 1 期 1-0・段 B)。

- 公開の関数とクラス
  - `checkpoint`(関数): L23: checkpoint の 3 本のハッシュ(HEAD run.py:4452-4495)。
  - `observe`(関数): L21+L22: 診断の行・在圏の標本・規範の計器・在圏 journal(HEAD run.py:4403-4451)。
- import している内部モジュール: `shibuya.engine.run`・`shibuya.engine.systems.state_io`・`shibuya.foundation.hashing`・`shibuya.foundation.queues.scheduler`
- 呼び手: `shibuya.engine.systems.table`
- 書きの許可
  - 系 `checkpoint`(群 計器・時 `tick`・関数 `checkpoint`)
    - 書いてよい外の道筋: `E:events.*`・`O2:act_layer._digest_cache`
    - 書く計数: `phase`・`result`
  - 系 `observe`(群 計器・時 `tick`・関数 `observe`)
    - 書いてよい外の道筋: `O34:norm_meter.*`・`O70:presence.*`
    - 書く計数: `diag_rows`・`occ_counts`・`occ_kind`・`occ_ticks`・`occ_transit`・`prev_sessions`・`prev_tape_misses`・`sleep_counts`
- 決定の ID: D-56・D-62・D-66・D-107・第 308

## [overrides.py](../../../../../../../../src/shibuya/engine/systems/overrides.py)

engine.systems.overrides — 試験の負の対照のための宣言の差し替え(第 1 期 1-0・草案 §3-1 の T1〜T3)。**試験のときだけ**。

- 公開の関数とクラス
  - `drop_path`(関数)
  - `drop_scratch`(関数)
  - `drop_soa`(関数)
  - `replace_spec`(関数): 系 ``name`` の ``writes`` の欄を差し替えた宣言で回す(``SYSTEMS`` と ``SPECS`` の両方)。
  - `wrap_fn`(関数): 系 ``name`` の関数を包み、T 以後の最初の 1 回だけ ``inject(ctx, b)`` を前か後に呼ぶ(段 FIX の負の対照)。
- import している内部モジュール: `shibuya.engine.systems.table`
- 読む試験: `tests/economy/cp2/test_cp2_writes_declared.py`・`tests/engine/decision/test_j0_writes_declared.py`・`tests/engine/events/test_e_writes_declared.py`・`tests/engine/experiment/test_x33_run.py`・`tests/engine/memory/test_m0_writes_declared.py`・`tests/engine/speech/test_speech_writes_declared.py`・`tests/engine/systems/test_guard_runs.py`・`tests/engine/tools/test_c0_contacts_in_relations.py`・`tests/engine/tools/test_c0_signboard_mark_invariance.py`

## [perceive.py](../../../../../../../../src/shibuya/engine/systems/perceive.py)

engine.systems.perceive — 知覚の系(perceive_prepare・detect)(第 1 期 1-0)。

- 公開の関数とクラス
  - `sys_detect`(関数): detect(HEAD run.py の同じ区間・文は変えない)。
  - `sys_perceive_prepare`(関数): perceive_prepare(HEAD run.py の同じ区間・文は変えない)。
- import している内部モジュール: `shibuya.engine.resolve`・`shibuya.engine.run`
- 呼び手: `shibuya.engine.systems.table`
- 書きの許可
  - 系 `detect`(群 知覚・時 `tick`・関数 `sys_detect`)
    - 呼んでよい resolve の口: `apply_detection`
    - 書いてよい SoA の列(閉包): `agents.fatigue_stage`・`agents.hunger_stage`・`agents.thermal_stage`・`cells.b4_hash`
    - 書いてよい外の道筋: `O45:detector.*`・`O66:act_layer.*`・`O6:intent_layer.*`・`T3M:step_scope.*`
    - 書く scratch: `det_agent`・`det_class`・`det_cond`・`e_agent`・`e_class`・`e_cond`
    - 書く計数: `intero_cross`・`phase`
  - 系 `perceive_prepare`(群 知覚・時 `tick`・関数 `sys_perceive_prepare`)
    - 書いてよい外の道筋: `O63:renderer.*`・`O84:renderer.*`・`PX:proximity.*`
    - 書く scratch: `field_rows`・`near_index`

## [probe.py](../../../../../../../../src/shibuya/engine/systems/probe.py)

engine.systems.probe — 系ごとの全欄の差(段 B)と系ごとの指紋(草案 §2-6 の B・§2-7)。**試験のときだけ**。

- 公開の関数とクラス
  - `Probe`(クラス): 系の境目ごとに snapshot を取り、差を直前の系へ帰属させる(段 B・指紋)。
  - `View`(クラス): snapshot の材料(HEAD の局所からでも箱からでも同じ形に組む)。
  - `at`(関数): 系 ``name`` の始まりの境目(試験のときだけ snapshot を取る・既定のランでは何もしない)。
  - `first_diff`(関数): 2 本の ``Probe.to_json()`` の entries を並べて、最初に食い違った (T, 系, 欄) を返す(同じなら ``None``)。
  - `plain`(関数): 比べるための素の値(配列は digest・辞書は鍵の repr の順・dataclass は欄・知らない物は型の名だけ)。
  - `save`(関数)
  - `snapshot`(関数): 全欄の digest(読むだけ・乱数を引かない・状態を書かない)。
  - `view_of`(関数): 箱から snapshot の材料を組む(HEAD の局所から組む ``probe_run._head_view`` と同じ形)。
- import している内部モジュール: `shibuya.engine.class_ids`・`shibuya.engine.state_hashes`・`shibuya.engine.state_ledger`・`shibuya.engine.systems.state_io`
- 呼び手: `shibuya.engine.experiment.branch`・`shibuya.engine.systems.conductor`
- 読む試験: `tests/economy/cp2/test_cp2_writes_declared.py`・`tests/engine/batching/test_conductor_windows.py`・`tests/engine/clock/test_tm3_step_scope.py`・`tests/engine/clock/test_tm4_regional_clock.py`・`tests/engine/decision/test_j0_writes_declared.py`・`tests/engine/events/test_e_writes_declared.py`・`tests/engine/experiment/test_x33_run.py`・`tests/engine/memory/test_m0_writes_declared.py`・`tests/engine/proximity/test_runs.py`・`tests/engine/speech/test_speech_writes_declared.py`・`tests/engine/state/test_class_ids.py`・`tests/engine/systems/test_guard_runs.py`・`tests/engine/tools/test_c0_contacts_in_relations.py`

## [remember.py](../../../../../../../../src/shibuya/engine/systems/remember.py)

engine.systems.remember — 記憶の系(memory・familiarity)(第 1 期 1-0)。

- 公開の関数とクラス
  - `sys_familiarity`(関数): familiarity(HEAD run.py の同じ区間・文は変えない)。
  - `sys_memory`(関数): memory(HEAD run.py の同じ区間・文は変えない)。
- 呼び手: `shibuya.engine.systems.table`
- 書きの許可
  - 系 `familiarity`(群 記憶・時 `tick`・立つ条件 `fam_layer`・関数 `sys_familiarity`)
    - 呼んでよい resolve の口: `write_familiarity`
    - 書いてよい SoA の列(閉包): `agents.fam_exposures`・`agents.fam_first`・`agents.fam_last`・`agents.fam_thing`・`agents.fam_visits`
    - 書いてよい外の道筋: `O67:fam_layer.*`・`O7:fam_layer.*`
  - 系 `memory`(群 記憶・時 `tick`・関数 `sys_memory`)
    - 呼んでよい resolve の口: `write_memory`・`write_relations`・`write_store_memory`
    - 書いてよい SoA の列(閉包): `agents.mem_cell`・`agents.mem_importance`・`agents.mem_kind`・`agents.mem_last`・`agents.mem_n`・`agents.mem_object`・`agents.mem_partner`・`agents.mem_result`・`agents.mem_tick`・`agents.rel_first`・`agents.rel_kind`・`agents.rel_last`・`agents.rel_n`・`agents.rel_partner`・`agents.rel_sign`・`agents.sm_first`・`agents.sm_last`・`agents.sm_n`・`agents.sm_poi`・`agents.sm_precision`・`agents.sm_source`・`agents.sm_valence`
    - 書いてよい外の道筋: `CT5:rel_layer._contact_flags`・`E:events.*`・`M0*:mem_layer.memory_store.*`・`O15:wom.*`・`O1[0-2]:mem_layer.*`・`O1[34]:poi_resolver.*`・`O1[6-9]:rel_layer.*`・`O64:renderer.*`・`O68:poi_resolver.*`・`O[89]:mem_layer.*`
    - 書く scratch: `exposures`

## [report.py](../../../../../../../../src/shibuya/engine/systems/report.py)

engine.systems.report — ランの結果の組み立て(R3・E2〜E4)(第 1 期 1-0・段 B)。

- 公開の関数とクラス
  - `report`(関数): R3: ``RunResult`` の組み立て・成長の検査・在圏 journal の書き出し(HEAD run.py:4593-4965)。返り値=``RunResult``。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.calendar`・`shibuya.engine.defect_fixes_1103`・`shibuya.engine.growth_decl`・`shibuya.engine.poi_target`・`shibuya.engine.run`・`shibuya.engine.tools.record`・`shibuya.foundation.growth`・`shibuya.foundation.rng`・`shibuya.foundation.text.channels`・`shibuya.foundation.time_consts`・`shibuya.perception.renderer`・`shibuya.world.laws.salient`・`shibuya.world.laws.switch_absent`・`shibuya.world.laws.switch_rate`
- 呼び手: `shibuya.engine.systems.table`
- 書きの許可
  - 系 `report`(群 計器・時 `run_end`・関数 `report`)
    - 書く計数: `frozen_sources_map`・`result`・`sleep_counts`
- 決定の ID: 11-01・11-02r/§1・11-02r/§1 #7・11-03/§3・D-58・D-59・D-99・D-107・第 308・第 309・第 330・第 346

## [run_end.py](../../../../../../../../src/shibuya/engine/systems/run_end.py)

engine.systems.run_end — ランの終わりの系(drain・close_final)(第 1 期 1-0)。

- 公開の関数とクラス
  - `sys_close_final`(関数): close_final(E1・HEAD run.py:4551-4592): テープを閉じる・世界過程の最後の日の締め(鉄道の最後の便を流す)・
  - `sys_drain`(関数): drain(HEAD run.py の同じ区間・文は変えない)。
- import している内部モジュール: `shibuya.engine.llm_bridge`・`shibuya.engine.run`・`shibuya.engine.systems.state_io`・`shibuya.llm.fleet`
- 呼び手: `shibuya.engine.systems.table`
- 読む試験: `tests/engine/test_state_ledger_10b.py`
- 書きの許可
  - 系 `close_final`(群 暦・時 `run_end`・関数 `sys_close_final`)
    - 呼んでよい resolve の口: `rail_arrive`・`rail_depart`・`set_plan_state`・`sync_transit_activity`
    - 書いてよい SoA の列(閉包): `agents.activity`・`agents.band`・`agents.cell`・`agents.node`・`agents.plan_flags`・`agents.target_node`・`agents.transit_ref`・`agents.transit_state`・`agents.xy`
    - 書いてよい外の道筋: `A:ledger.*`・`C1B:calendar_self.cal_store`・`E:events.*`・`EC:ledger.*`・`EM:ledger.*`・`O2:act_layer._digest_cache`・`O3[5-8]:presence.*`・`O5[0-6]:runner.*`・`O5[7-9]:ledger.*`・`O60:ledger.*`・`O61:runner.*`・`O70:presence.*`・`O7[2-6]:runner.*`・`O7[7-9]:ledger.*`・`O8[01]:ledger.*`・`O8[5-7]:bridge.*`・`O95:runner.*`・`O9[23]:ledger.*`・`TXD:ledger.*`
    - 書く計数: `daily_records`・`ledger_growth`・`result`・`state_files`
  - 系 `drain`(群 判断・時 `run_end`・LLM `drain`・関数 `sys_drain`)
    - 書いてよい外の道筋: `M0R:mem_layer.memory_store.*`・`O43:run_day.*`・`O44:run_day.*`・`O87:bridge.*`・`O8[89]:fleet_bridge.*`・`O96:run_day.*`
    - 書く計数: `result`・`state_files`
- 決定の ID: D-58・第 304

## [spec.py](../../../../../../../../src/shibuya/engine/systems/spec.py)

engine.systems.spec — 系の宣言の口(第 1 期 1-0・草案 §2-5)。未リサーチ(expedient)の名と形。

- 公開の関数とクラス
  - `Access`(クラス)
  - `SystemSpec`(クラス)
  - `make`(関数): 宣言を 1 つ作る(``writes.soa`` は ``resolve_ops`` の閉包)。文字列は空白で区切った名の並び。
  - `path_allowed`(関数): 外の状態の鍵 ``"O39:conv.sessions"`` が宣言の道筋(前方一致の ``*`` を含む)に入るか。
  - `with_fn`(関数)
- import している内部モジュール: `shibuya.engine.systems.allow`
- 呼び手: `shibuya.engine.systems.conductor`・`shibuya.engine.systems.table`
- 読む試験: `tests/engine/clock/test_tm4_regional_clock.py`・`tests/engine/systems/test_systems_table.py`・`tests/tools/test_repo_guide.py`

## [state_io.py](../../../../../../../../src/shibuya/engine/systems/state_io.py)

engine.systems.state_io — 箱から状態台帳の持ち主・知覚 SoA・ハッシュの材料を組む口(第 1 期 1-0)。

- 公開の関数とクラス
  - `act_hash_now`(関数): 活動層(と意図の層)の Python 側の状態のハッシュ(HEAD の ``_act_hash_now``)。
  - `bodies_now`(関数): HEAD の ``_bodies_now``。
  - `close_day_midrun`(関数): 10d: 複数日のランの途中の日の締め(1 日 1 回・最後の刻みの後・次の日の刻み 0 の前)。HEAD の ``_close_day_midrun``。
  - `day_record`(関数): HEAD の ``_day_record``。
  - `eod_hashes`(関数): 日の締めの**後**の behavior-hash・full-hash(10b 検収後 P2・10d の再開の判定はこちら)。読むだけ。HEAD の ``_eod_hashes``。
  - `hash_owners`(関数): 10b: 状態台帳の外の状態の持ち主(``items`` の根の鍵)。HEAD の ``_hash_owners`` と同じ鍵・同じ順・同じ物。
  - `ledger_close`(関数): 金と物の台帳の日の締め・日次センサス・月次 T3・センサスの書き出し(1 日のランは今のまま)。HEAD の ``_ledger_close``。
  - `mark_boundary`(関数): 1-3: E(診断)の区切りの行(``day_close``・``checkpoint``)を記録の時計の時刻で 1 行書く(記録しないときは何もしない)。
  - `money_now`(関数): HEAD の ``_money_now``。
  - `pst_now`(関数): 知覚 SoA(顕著行為の過程が持つ・世界過程が無ければ ``None``)。HEAD の ``_pst_now``。
  - `rebuild_derived`(関数): 10d(親の答え 2): 起動時に**SoA の値から**作る表を、戻した SoA から決定的に作り直す(再開だけ)。HEAD の ``_rebuild_derived``。
  - `relay_tables`(関数): 10d: ``d`` 日目の日の頭の**表の張り直し**(資産・暦・日番号だけから決まる=再開でも同じ表)。HEAD の ``_relay_tables``。
  - `save_state`(関数): 10d: 状態のまとまりを 1 ファイルに書く(SoA の列・外の状態・進捗の印・艦隊の未着の呼)。HEAD の ``_save_state``。
  - `start_day`(関数): 10d: ``d`` 日目の日の頭の体の側の書き換え(通しのランだけ・再開では保存した値を読む)。HEAD の ``_start_day``。
  - `w17_weekday`(関数): その日に引く W17 の曜日の行(0 日目は暦のまま=今と同じ)。HEAD の ``_w17_weekday``。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.economy.stage2_bind`・`shibuya.engine.defect_fixes_1103`・`shibuya.engine.experiment.layer`・`shibuya.engine.regional_clock`・`shibuya.engine.resume`・`shibuya.engine.run`・`shibuya.engine.state_hashes`・`shibuya.engine.state_ledger`・`shibuya.foundation.decl.bridging`・`shibuya.foundation.hashing`・`shibuya.foundation.journal.log`・`shibuya.foundation.time_consts`・`shibuya.foundation.vocab.events`・`shibuya.world.facts.rules.table`・`shibuya.world.laws.switch_absent`・`shibuya.world.laws.switch_rate`・`shibuya.world.laws.switch_seat`・`shibuya.world.model.proximity`
- 呼び手: `shibuya.engine.systems.build`・`shibuya.engine.systems.day`・`shibuya.engine.systems.observe`・`shibuya.engine.systems.probe`・`shibuya.engine.systems.run_end`
- 読む試験: `tests/engine/discard_probe.py`・`tests/engine/processes/test_rng_scheme_10c.py`・`tests/engine/systems/test_boxes.py`・`tests/engine/test_state_ledger_10b.py`・`tests/engine/test_version_bump_10e.py`・`tests/engine/time/test_t0_tm9_fields.py`
- 読む試験(道筋で): `tests/engine/rules/test_rules_table_schema.py`
- 決定の ID: 11-01・11-02r/§1・11-02r/§1 #7・11-03/§3・D-85・第 346

## [static_check.py](../../../../../../../../src/shibuya/engine/systems/static_check.py)

engine.systems.static_check — 系の宣言と系のコードを AST で突き合わせる(第 1 期 1-0・草案 §2-6 の D ①②③)。

- 公開の関数とクラス
  - `SystemCode`(クラス)
  - `analyze`(関数): 系の関数(か箱を受け取る補助)の本体を推移的に読む。
  - `analyze_spec`(関数)
  - `source_root`(関数): このモジュールのあるディレクトリ(〔移す段 2-2〕``core.paths.module_dir``)。
- import している内部モジュール: `shibuya.engine.resolve`・`shibuya.engine.systems.allow`・`shibuya.foundation.paths`
- 読む試験: `tests/engine/state/test_move_prep_stage2.py`・`tests/engine/systems/test_fix_guards.py`・`tests/engine/systems/test_systems_table.py`

## [table.py](../../../../../../../../src/shibuya/engine/systems/table.py)

engine.systems.table — 系の宣言の表 ``SYSTEMS``(呼ぶ順の 1 つの表)(第 1 期 1-0・草案 §2-2・§2-5)。

- import している内部モジュール: `shibuya.engine.calendar2.layer`・`shibuya.engine.calendar3.layer`・`shibuya.engine.contact.layer`・`shibuya.engine.duties.layer`・`shibuya.engine.experiment.layer`・`shibuya.engine.systems.act`・`shibuya.engine.systems.body`・`shibuya.engine.systems.day`・`shibuya.engine.systems.decide`・`shibuya.engine.systems.judge`・`shibuya.engine.systems.llm_io`・`shibuya.engine.systems.observe`・`shibuya.engine.systems.perceive`・`shibuya.engine.systems.remember`・`shibuya.engine.systems.report`・`shibuya.engine.systems.run_end`・`shibuya.engine.systems.spec`・`shibuya.engine.systems.talk`・`shibuya.engine.systems.world`
- 呼び手: `shibuya.engine.systems.conductor`・`shibuya.engine.systems.overrides`
- 読む試験: `tests/build_rail/test_w12_arrivals_2_3c.py`・`tests/economy/cp2/test_cp2_writes_declared.py`・`tests/economy/stage2/test_stage2_writers.py`・`tests/engine/batching/test_conductor_windows.py`・`tests/engine/calendar/test_ca1b_unit.py`・`tests/engine/calendar/test_calendar_shadow.py`・`tests/engine/calendar2/test_ca2_runs.py`・`tests/engine/calendar3/test_ca3_runs.py`・`tests/engine/clock/test_tm3_step_scope.py`・`tests/engine/clock/test_tm4_regional_clock.py`・`tests/engine/contact/test_c1_fixes.py`・`tests/engine/contact/test_c1_runs.py`・`tests/engine/decision/test_j0_writes_declared.py`・`tests/engine/duties/test_du_runs.py`・`tests/engine/events/test_e_writes_declared.py`・`tests/engine/experiment/test_x33_run.py`・`tests/engine/memory/test_m0_store_schema.py`・`tests/engine/memory/test_m0_writes_declared.py`・`tests/engine/proximity/test_runs.py`・`tests/engine/speech/test_speech_writes_declared.py`・`tests/engine/systems/test_fix_guards.py`・`tests/engine/systems/test_guard_runs.py`・`tests/engine/systems/test_systems_table.py`・`tests/engine/test_add_at_guard.py`・`tests/engine/test_two_phase.py`・`tests/engine/time/test_t0_no_tick_word.py`・`tests/engine/tools/test_c0_contacts_in_relations.py`・`tests/perception/facts/test_percept_is_scratch.py`・`tests/tools/test_repo_guide.py`
- 書きの許可
  - 系 `build`(群 組み立て・時 `run_head`・関数 `_build_fn`)
    - 呼んでよい resolve の口: `initialize`・`initialize_energy`・`place_at_external`・`rail_arrive`・`restore_items`・`restore_soa`・`set_initial_activity`・`set_plan_state`・`write_relations`
    - 書いてよい SoA の列(閉包): `agents.activity`・`agents.age`・`agents.band`・`agents.board_line`・`agents.board_since`・`agents.cell`・`agents.eer_kcal`・`agents.energy_balance`・`agents.fatigue`・`agents.hunger`・`agents.hunger_stage`・`agents.kind`・`agents.money`・`agents.node`・`agents.plan_flags`・`agents.rel_first`・`agents.rel_kind`・`agents.rel_last`・`agents.rel_n`・`agents.rel_partner`・`agents.rel_sign`・`agents.sex`・`agents.since_meal_kcal`・`agents.target_node`・`agents.thermal`・`agents.transit_ref`・`agents.transit_state`・`agents.weight_kg`・`agents.xy`・`cells.density`・`cells.density_stage`・`cells.open_count`
- 決定の ID: 第 346

## [talk.py](../../../../../../../../src/shibuya/engine/systems/talk.py)

engine.systems.talk — 会話の系(relations_wake・conversation)(第 1 期 1-0)。

- 公開の関数とクラス
  - `sys_conversation`(関数): conversation(HEAD run.py の同じ区間・文は変えない)。
  - `sys_relations_wake`(関数): relations_wake(HEAD run.py の同じ区間・文は変えない)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.commit`・`shibuya.engine.resolve`
- 呼び手: `shibuya.engine.systems.table`
- 読む試験: `tests/engine/test_defect_fixes_1103.py`
- 書きの許可
  - 系 `conversation`(群 会話・時 `tick`・立つ条件 `conv`・関数 `sys_conversation`)
    - 呼んでよい resolve の口: `end_conversation`・`join_conversation`・`set_conversing`・`talk_within_reach`
    - 書いてよい SoA の列(閉包): `agents.activity`・`agents.last_result`・`agents.last_result_tick`・`agents.talk_partner`
    - 書いてよい外の道筋: `E:events.*`・`O19:rel_layer.*`・`O39:conv.*`・`O40:conv.*`・`O41:conv.*`・`O91:conv.*`・`TCC:talk_clock.*`
    - 書く計数: `leave_closed`
  - 系 `relations_wake`(群 会話・時 `tick`・立つ条件 `rel_layer`・関数 `sys_relations_wake`)
    - 呼んでよい resolve の口: `write_relations`
    - 書いてよい SoA の列(閉包): `agents.rel_first`・`agents.rel_kind`・`agents.rel_last`・`agents.rel_n`・`agents.rel_partner`・`agents.rel_sign`
    - 書いてよい外の道筋: `O1[6-9]:rel_layer.*`
    - 書く scratch: `e_agent`・`e_class`・`e_cond`
- 決定の ID: 11-03・D-93・D-112・第 346

## [world.py](../../../../../../../../src/shibuya/engine/systems/world.py)

engine.systems.world — 世界の系(world=世界過程 18 本の下位の系を ``runner.step`` で回す)(第 1 期 1-0)。

- 公開の関数とクラス
  - `sys_world`(関数): world(HEAD run.py の同じ区間・文は変えない)。
- 呼び手: `shibuya.engine.systems.table`
- 書きの許可
  - 系 `world`(群 世界・時 `tick`・関数 `sys_world`)
    - 呼んでよい resolve の口: `balk_queue`・`collect_waste`・`consume`・`discard_to_bin`・`rail_arrive`・`rail_depart`・`release_indoor`・`request_open_close`・`restock`・`set_notice_state`・`set_open_flags`・`set_plan_state`・`set_thermal`・`sync_transit_activity`
    - 書いてよい SoA の列(閉包): `agents.activity`・`agents.band`・`agents.cell`・`agents.holdings`・`agents.last_result`・`agents.last_result_tick`・`agents.node`・`agents.plan_flags`・`agents.poi_ref`・`agents.poi_since`・`agents.queue_poi`・`agents.queue_since`・`agents.target_node`・`agents.thermal`・`agents.transit_ref`・`agents.transit_state`・`agents.xy`・`perception.heading`・`perception.task_flag`・`pois.open_now`・`pois.stock`
    - 書いてよい外の道筋: `A:ledger.*`・`BD:body.*`・`C1B:calendar_self.cal_store`・`DUM:duties._du_meter`・`E:events.*`・`EM:ledger.*`・`O3[5-7]:presence.*`・`O4[6-9]:runner.*`・`O5[0-6]:runner.*`・`O5[7-9]:ledger.*`・`O60:ledger.*`・`O61:runner.*`・`O63:renderer._tickc`・`O70:presence.*`・`O7[2-6]:runner.*`・`O7[7-9]:ledger.*`・`O8[01]:ledger.*`・`O95:runner.*`・`O9[23]:ledger.*`
