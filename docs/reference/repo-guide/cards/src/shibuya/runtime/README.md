# src/shibuya/runtime

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 6 本・その他 0 本(このディレクトリの直下)

下のディレクトリ: [clocks](clocks/README.md)・[inference](inference/README.md)・[state](state/README.md)・[systems](systems/README.md)

## [__init__.py](../../../../../../../src/shibuya/runtime/__init__.py)

(冒頭の説明なし)

## [arbiter.py](../../../../../../../src/shibuya/runtime/arbiter.py)

engine.arbiter — 繰り延べアービタ(知覚契約書 §6 の裁定規則)。

- 公開の関数とクラス
  - `Arbiter`(クラス): 毎tick の裁定+保留の持ち越し+診断計数の積み上げ(1 シミュ日ぶん)。
  - `ArbiterDecision`(クラス): 1 tick 分の裁定結果(純関数 ``arbitrate`` の出力)。
  - `arbitrate`(関数): 繰り延べアービタの**純関数**本体(入力の並び順に依存しない)。
  - `call_budget_per_tick`(関数): 予算行 L4 を tick あたり・当該規模へ按分した呼数。
- import している内部モジュール: `shibuya.foundation.hashing`・`shibuya.foundation.queues.scheduler`・`shibuya.foundation.time_consts`・`shibuya.foundation.types`・`shibuya.foundation.vocab.agent_codes`・`shibuya.mind.system1.wake`
- 呼び手: `shibuya.runtime.result`・`shibuya.runtime.run`・`shibuya.runtime.systems.assemble`
- 読む試験: `tests/bench/test_refr20b_tool.py`・`tests/c6/test_l4_l6_budget.py`・`tests/c8/test_ablations_ab8.py`・`tests/c8/test_ablations_l4_pin.py`・`tests/economy/test_entry_capital.py`・`tests/engine/test_ablation23_switches.py`・`tests/engine/test_arbiter.py`・`tests/engine/test_l4_budget.py`・`tests/engine/test_plan_sleep_d62.py`・`tests/engine/test_processes_run.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_sleep_suppression_d56.py`・`tests/engine/test_two_layer_activity.py`・`tests/test_cli_l4_scale.py`
- 読む試験(道筋で): `tests/engine/test_add_at_guard.py`・`tests/engine/test_two_phase.py`
- 状態台帳の行
  - 持ち主 `arbiter`(`Arbiter`)
    - `O42` Arbiter _pending・_pool・queue・_last_tick(挙動 behavior・復元 required) 道筋 `arbiter._last_tick`・`arbiter._pending`・`arbiter._pool`・`arbiter.queue` 書ける系: arbiter
    - `O71` Arbiter の計数(挙動 diag・復元 discardable) 道筋 `arbiter._diag_total`・`arbiter._merged_total`・`arbiter._outside_total`・`arbiter._sleep_total`・`arbiter.budget_unused`・`arbiter.n_calls_total` 書ける系: arbiter
- 決定の ID: 09-25・D-56・D-66・D-99・D-110

## [clock.py](../../../../../../../src/shibuya/runtime/clock.py)

engine.clock — シミュレーション時計(壁時計に一切依存しない)。

- 公開の関数とクラス
  - `SimClock`(クラス): 開始時刻と tick 長だけを持つ不変の時計。
- import している内部モジュール: `shibuya.foundation.time_consts`・`shibuya.foundation.types`
- 読む試験: `tests/engine/test_clock.py`
- 読む試験(道筋で): `tests/engine/test_state_checks_10f.py`・`tests/tools/test_pkgmove.py`

## [result.py](../../../../../../../src/shibuya/runtime/result.py)

runtime.result — 割る段で ``engine/run.py`` を割った割り先(全ファイルの表 §4・名の表は``tools/pkgmove/map.toml`` の割る行)。

- 公開の関数とクラス
  - `Checkpoint`(クラス): checkpoint 1 点の状態ハッシュ(T1/T2 の一致判定)。
  - `RunResult`(クラス): 1 ランの結果。
  - `decision_layers_summary`(関数): 5b(L4 (a)): 時 × 層 × 起床入口 の判断数 → manifest の形(割合つき)。
- import している内部モジュール: `shibuya.act.apply`・`shibuya.act.intake.undefined`・`shibuya.act.intent`・`shibuya.act.target`・`shibuya.experiments.port.layer`・`shibuya.experiments.port.run_kind`・`shibuya.foundation.decl.bridging`・`shibuya.foundation.growth`・`shibuya.foundation.manifest.sections`・`shibuya.foundation.ports.percept`・`shibuya.foundation.queues.batching`・`shibuya.foundation.queues.scheduler`・`shibuya.foundation.rng`・`shibuya.foundation.text.channels`・`shibuya.foundation.text.templates`・`shibuya.foundation.time_consts`・`shibuya.foundation.types`・`shibuya.interim_bundles.calendar2.layer`・`shibuya.interim_bundles.calendar3.layer`・`shibuya.interim_bundles.calendar_self`・`shibuya.interim_bundles.contact.layer`・`shibuya.interim_bundles.duties.layer`・`shibuya.mind.judge.chooser`・`shibuya.mind.judge.classical`・`shibuya.mind.judge.decision.layer`・`shibuya.mind.memory.familiarity`・`shibuya.mind.memory.memory`・`shibuya.mind.percept.draw`・`shibuya.runtime.arbiter`・`shibuya.runtime.clocks.regional`・`shibuya.runtime.clocks.speech`・`shibuya.runtime.clocks.step_scope`・`shibuya.runtime.inference.bridge`・`shibuya.runtime.state.hashes`・`shibuya.runtime.state.ledger`・`shibuya.society.calendar_shadow`・`shibuya.society.speech.layer`・`shibuya.world.body.energy`・`shibuya.world.body.model`・`shibuya.world.facts.rights.record`・`shibuya.world.facts.rules.table`・`shibuya.world.model.assets`・`shibuya.world.model.geometry`・`shibuya.world.model.proximity`・`shibuya.world.model.space.nav1`
- 呼び手: `shibuya.interfaces.cli.main`・`shibuya.runtime.run`・`shibuya.runtime.systems.assemble`・`shibuya.runtime.systems.observe`・`shibuya.runtime.systems.report`・`shibuya.runtime.systems.state_io`
- 読む試験: `tests/c6/test_t9_diagnostics.py`・`tests/engine/test_calendar_sites.py`・`tests/engine/test_mock_day_w2.py`・`tests/engine/test_sleep_suppression_d56.py`・`tests/engine/test_state_ledger_10b.py`・`tests/engine/test_tape_wiring.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/time/test_t0_tm9_fields.py`・`tests/test_cli_vocab_version.py`
- 読む試験(道筋で): `tests/tools/test_pkgmove.py`
- 決定の ID: 11-01・11-02r・11-02r/§1・11-02r/§1 #7・11-03・11-03/§3・D-28・D-51・D-55・D-56・D-58・D-59・D-62・D-66・D-71・D-84・D-85・D-96・D-99・D-107・D-110・D-112・D-113・D-114・D-115・D-116・D-117・D-118・D-119・D-120・第 268・第 269・第 300・第 304・第 308・第 330

## [run.py](../../../../../../../src/shibuya/runtime/run.py)

engine.run — 1 シミュ日の mock ラン(予算行 **W2**)と CLI。

- 公開の関数とクラス
  - `check_replay_tape`(関数): 〔第330・RET〕再生するテープが今の版で録られたかを確かめる(違えば止める=警告ではなく例外)。
  - `classical_acq_addressable`(関数): 第2波 §2A 項 3-1(検収後): 古典の交際の候補の A から、話しかけられない相手(会話中・就寝中=
  - `l4_budget`(関数): 〔Q13〕呼数の倍率 → 1 刻みの呼数上限(``budget`` を渡さない ``run_day`` と ``cli.run`` が使う 1 つの式)。
  - `resolve_environment_seed`(関数): 10f 第 2 段の直し(S1): 環境の seed(``resolve_sub_seed`` と同じ)。
  - `resolve_l4_scale`(関数): 〔Q13 (a′)〕渡さなかった倍率(``None``)の決め方=``run_day`` と ``cli.run`` の 1 つの規則。
  - `resolve_population_seed`(関数): 10f(K21 (a)): 母集団の seed(``resolve_sub_seed`` と同じ)。
  - `resolve_sub_seed`(関数): 10f: 母集団・環境の seed(``None`` なら ``seed`` と同じ値=今と同じ)。
  - `run_day`(関数): 1 シミュ日(既定 1,440 tick)の mock ランを回す。
  - `run_salt_for`(関数): ``blake3(master_seed ‖ 0x1f ‖ "engine")`` の先頭 16 バイト(親の指定)。
- import している内部モジュール: `shibuya.act.activity`・`shibuya.act.intake.from_words`・`shibuya.act.intent`・`shibuya.act.ops.talk`・`shibuya.act.target`・`shibuya.foundation.ports.ledger`・`shibuya.foundation.queues.scheduler`・`shibuya.foundation.rng`・`shibuya.foundation.text.channels`・`shibuya.foundation.text.templates`・`shibuya.foundation.time_consts`・`shibuya.foundation.types`・`shibuya.foundation.vocab.act_codes`・`shibuya.foundation.vocab.actions`・`shibuya.foundation.vocab.agent_codes`・`shibuya.foundation.vocab.relations`・`shibuya.mind.judge.chooser`・`shibuya.mind.judge.classical`・`shibuya.mind.memory.familiarity`・`shibuya.mind.memory.memory`・`shibuya.mind.memory.store_memory`・`shibuya.mind.memory.wom`・`shibuya.mind.percept.draw`・`shibuya.runtime.arbiter`・`shibuya.runtime.inference.bridge`・`shibuya.runtime.inference.fleet`・`shibuya.runtime.inference.mock`・`shibuya.runtime.inference.tape`・`shibuya.runtime.result`・`shibuya.runtime.systems.conductor`・`shibuya.world.body.energy`・`shibuya.world.facts.calendar`・`shibuya.world.facts.population_reader`・`shibuya.world.laws.opening`・`shibuya.world.model.agent_table`・`shibuya.world.model.assets`・`shibuya.world.model.geometry`・`shibuya.world.model.state`
- 呼び手: `shibuya.interfaces.cli.main`・`shibuya.interfaces.cli.run_args`・`shibuya.runtime.systems.act`・`shibuya.runtime.systems.assemble`・`shibuya.runtime.systems.body`・`shibuya.runtime.systems.decide`・`shibuya.runtime.systems.judge`・`shibuya.runtime.systems.llm_io`・`shibuya.runtime.systems.perceive`・`shibuya.runtime.systems.run_end`・`shibuya.runtime.systems.state_io`・`tools/c6/run_hash.py`・`tools/c7/occupancy_series.py`・`tools/instruments/anchor_gauge.py`
- 読む試験: `tests/build_pop/test_pop_pipeline.py`・`tests/c6/test_l4_l6_budget.py`・`tests/c6/test_t5_order_bias.py`・`tests/c6/test_t9_diagnostics.py`・`tests/economy/cp2/test_cp2_flow_sum.py`・`tests/economy/cp2/test_cp2_k17_capacity_and_overflow.py`・`tests/economy/cp2/test_cp2_writes_declared.py`・`tests/economy/stage2/test_stage2_runs.py`・`tests/economy/test_rules42_runs.py`・`tests/economy/test_rules42b_ledger.py`・`tests/engine/batching/test_conductor_windows.py`・`tests/engine/body/test_body_manifest.py`・`tests/engine/body/test_body_reserve.py`・`tests/engine/body/test_meal_default_w17.py`・`tests/engine/body/test_system1_placeholders.py`・`tests/engine/bridging/test_bridging_ledger.py`・`tests/engine/bridging/test_manifest_rules_bridges.py`・`tests/engine/calendar/test_ca1b_runs.py`・`tests/engine/calendar/test_calendar_shadow.py`・`tests/engine/calendar2/test_ca2_runs.py`・`tests/engine/calendar3/test_ca3_runs.py`・`tests/engine/clock/test_tm3_step_scope.py`・`tests/engine/clock/test_tm4_regional_clock.py`・`tests/engine/contact/test_c1_event_log_onoff.py`・`tests/engine/contact/test_c1_fixes.py`・`tests/engine/contact/test_c1_runs.py`・`tests/engine/contact/test_c2_runs.py`・`tests/engine/decision/test_j0_cause_columns.py`・`tests/engine/decision/test_j0_mock_equivalence.py`・`tests/engine/decision/test_j0_other_ratio_field.py`・`tests/engine/decision/test_j0_shuffle_invariance.py`・`tests/engine/decision/test_j0_writes_declared.py`・`tests/engine/duties/test_du_runs.py`・`tests/engine/events/test_e_log_invariance.py`・`tests/engine/events/test_e_log_links_actual.py`・`tests/engine/events/test_e_log_schema.py`・`tests/engine/events/test_e_manifest_events.py`・`tests/engine/events/test_e_writes_declared.py`・`tests/engine/experiment/test_x33_run.py`・`tests/engine/memory/test_m0_recall_equivalence.py`・`tests/engine/memory/test_m0_render_bytes.py`・`tests/engine/memory/test_m0_shown_recorded.py`・`tests/engine/memory/test_m0_writes_declared.py`・`tests/engine/memory/test_m1_runs.py`・`tests/engine/memory/test_m2_cue.py`・`tests/engine/memory/test_m4_m5_people.py`・`tests/engine/memory/test_mr65_grain_and_cli.py`・`tests/engine/memory/test_mr65_guards.py`・`tests/engine/memory/test_mr65_review_fixes.py`・`tests/engine/multiday/test_md23_body_events.py`・`tests/engine/multiday/test_md23_resume.py`・`tests/engine/processes/test_absent_processes_1102.py`・`tests/engine/processes/test_rate_rules_1101.py`・`tests/engine/processes/test_rng_scheme_10c.py`・`tests/engine/proximity/test_runs.py`・`tests/engine/rights/test_rights_events.py`・`tests/engine/rights/test_rights_manifest.py`・`tests/engine/speech/_s8b.py`・`tests/engine/speech/test_speech_writes_declared.py`・`tests/engine/state/shaped_names.py`・`tests/engine/state/test_class_ids.py`・`tests/engine/systems/test_boxes.py`・`tests/engine/systems/test_guard_runs.py`・`tests/engine/test_10a_review_fixes.py`・`tests/engine/test_ablation23_switches.py`・`tests/engine/test_activation_10e.py`・`tests/engine/test_area_source_c9c.py`・`tests/engine/test_assets_10e_b0_b1.py`・`tests/engine/test_c9b_targets_attention.py`・`tests/engine/test_calendar_10e_e3.py`・`tests/engine/test_calendar_sites.py`・`tests/engine/test_census_out.py`・`tests/engine/test_classical_policy.py`・`tests/engine/test_classical_social.py`・`tests/engine/test_conversation.py`・`tests/engine/test_conversation_invite.py`・`tests/engine/test_defect_fixes_1103.py`・`tests/engine/test_determinism_t1_t2_t4.py`・`tests/engine/test_eatery_place_food.py`・`tests/engine/test_energy_balance.py`・`tests/engine/test_env_and_sections_10f.py`・`tests/engine/test_familiarity.py`・`tests/engine/test_fleet_wiring.py`・`tests/engine/test_geometry_c9.py`・`tests/engine/test_intent_chooser.py`・`tests/engine/test_intent_hold.py`・`tests/engine/test_intent_mode_open.py`・`tests/engine/test_l4_budget.py`・`tests/engine/test_ledger_wiring.py`・`tests/engine/test_meal_bundle_2b.py`・`tests/engine/test_meal_gate_per_hour.py`・`tests/engine/test_memory_recall.py`・`tests/engine/test_memory_record.py`・`tests/engine/test_mock_day_w2.py`・`tests/engine/test_move_destination.py`・`tests/engine/test_plan_sleep_d62.py`・`tests/engine/test_presence_executor.py`・`tests/engine/test_processes_run.py`・`tests/engine/test_relations.py`・`tests/engine/test_relations_tenure.py`・`tests/engine/test_renderer_wiring.py`・`tests/engine/test_response_delay.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_salt_seed_split_10f.py`・`tests/engine/test_seat_release_2_4.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_sleep_suppression_d56.py`・`tests/engine/test_stage3_small_fixes.py`・`tests/engine/test_state_checks_10f.py`・`tests/engine/test_state_format_10f.py`・`tests/engine/test_state_ledger_10b.py`・`tests/engine/test_store_choice.py`・`tests/engine/test_store_memory.py`・`tests/engine/test_t3_manifest.py`・`tests/engine/test_tape_deferred.py`・`tests/engine/test_tape_wiring.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/test_undefined_action.py`・`tests/engine/test_version_bump_10e.py`・`tests/engine/test_vocab_v2_eat.py`・`tests/engine/test_wom.py`・`tests/engine/time/test_t0_tickctx_equivalence.py`・`tests/engine/time/test_t0_tm9_fields.py`・`tests/engine/time/test_v30a_key_sites.py`・`tests/engine/tools/test_c0_affordance_from_registry.py`・`tests/engine/tools/test_c0_contacts_in_relations.py`・`tests/engine/tools/test_c0_phone_table_empty_and_declared.py`・`tests/engine/tools/test_c0_signboard_mark_invariance.py`・`tests/llm/test_mock_v3.py`・`tests/perception/facts/test_coef_removed_or_armed.py`・`tests/perception/facts/test_percept_is_scratch.py`・`tests/perception/facts/test_percept_schema.py`・`tests/perception/test_ablation1.py`・`tests/perception/test_ablation6_signage.py`・`tests/perception/test_b6_invite.py`・`tests/perception/test_near_tiebreak.py`・`tests/perception/test_p_see_activity.py`・`tests/perception/test_signage_p_see_gate.py`・`tests/perception/test_weather_a48.py`・`tests/test_cli_l4_scale.py`・`tests/test_cli_vocab_version.py`
- 読む試験(道筋で): `tests/tools/test_commit_check.py`・`tests/tools/test_pkgmove.py`
- 決定の ID: 10-12/§1-6・11-03・R-8・D-56・D-59・D-61・D-62・D-66・D-71・D-84・D-93・D-96・D-99・D-107・D-110・D-112・D-113・D-114・D-115・D-116・D-117・D-118・D-119・D-120・第 266・第 267・第 268・第 269・第 299・第 308・第 309・第 330・第 346・第 347

## [switch_defects.py](../../../../../../../src/shibuya/runtime/switch_defects.py)

engine.defect_fixes_1103 — 棚卸し B で見つけた欠陥 4 件の直しの宣言・計器・見出し(指示書 11-03 §3・小さな版上げ 1 回分)。

- 公開の関数とクラス
  - `check_resume`(関数): 再開のときに、保存したランの見出しの ``defect_fixes_1103``(無ければ legacy=版上げの前のラン)が on かを確かめる(違えば止める)。
  - `empty_counts`(関数): 計器の空の形(活動の名ごとの dict 2 本と整数 5 本)。
  - `header_fields`(関数): 状態のファイルの見出しの ``defect_fixes_1103``(ランは常に ``{"mode": "on"}``・on の外の名は None)。
  - `is_legacy`(関数): ``mode``(省略=ランの腕 on)が旧道(版上げの前の挙動=部品の口だけ)か。
  - `is_on`(関数): ``mode``(省略=ランの腕 on)が直した道か。
  - `manifest_fields`(関数): manifest の ``defect_fixes_1103``(設定=形の版・腕・4 件の宣言・直した印/観測=計器)。
  - `resolve`(関数): 引数の腕(``None``=ランの腕 ``on``)を名に直す(名の誤りは止める)。
- import している内部モジュール: `shibuya.foundation.arms.removed`
- 呼び手: `shibuya.runtime.systems.assemble`・`shibuya.runtime.systems.report`・`shibuya.runtime.systems.state_io`
- 読む試験: `tests/engine/test_defect_fixes_1103.py`
- 環境変数: `SHIBUYA_DEFECT_FIXES_1103`
- 決定の ID: 10-13b/§0-6・11-02r/§2-2・11-03・11-03/§3・第 346
