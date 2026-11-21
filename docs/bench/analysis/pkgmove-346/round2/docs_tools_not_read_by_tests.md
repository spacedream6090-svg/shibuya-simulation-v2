# 段 4 の後に動かなくなる docs の記録の道具(tests が読まないもの・親の決定 7)

道具は書き換えない(docs の下の記録)。段 4 の全段(保留を除く)で移すモジュールか、空にする頭を import する docs の `.py`。tests が道で読む 11 本は (a) の範囲に入れた(`tools/pkgmove/allow.py` の `RECORD_TOOLS`)ので、この一覧に入らない。数え方: AST の `import shibuya…`・`from shibuya… import`(関数の中を含む)。

全部で 131 本。

| 道具 | 読むモジュール(頭の 4 つ) |
|---|---|
| `docs/bench/analysis/c10-relations-2026-09-28/rel_measure.py` | shibuya.agents, shibuya.agents.population, shibuya.agents.weekly, shibuya.core.hashing ほか |
| `docs/bench/analysis/d113-defects-2026-09-26/d113_1_parse_snapshot.py` | shibuya.llm.parser |
| `docs/bench/analysis/energy-classical-2026-09-28/classical_measure.py` | shibuya.engine, shibuya.engine.energy, shibuya.world.state |
| `docs/bench/analysis/energy-classical-2026-09-28/energy_measure.py` | shibuya.engine, shibuya.engine.energy |
| `docs/bench/analysis/familiarity-2026-09-28/familiarity_measure.py` | shibuya.agents, shibuya.core.hashing, shibuya.engine, shibuya.engine.familiarity ほか |
| `docs/bench/analysis/intent-chooser-2026-09-28/intent_hold_measure.py` | shibuya.agents, shibuya.core.hashing, shibuya.engine |
| `docs/bench/analysis/intent-chooser-2026-09-28/intent_measure.py` | shibuya.engine |
| `docs/bench/analysis/intent-chooser-2026-09-28/move_measure.py` | shibuya.engine |
| `docs/bench/analysis/intent-chooser-2026-09-28/replay_intents.py` | shibuya.engine, shibuya.engine.processes.opening, shibuya.llm.parser, shibuya.world ほか |
| `docs/bench/analysis/intent-chooser-2026-09-28/replay_moves.py` | shibuya.engine, shibuya.engine.processes.opening, shibuya.llm.parser, shibuya.world ほか |
| `docs/bench/analysis/intent-chooser-2026-09-28/replay_tapes.py` | shibuya.engine, shibuya.engine.processes.opening, shibuya.llm.parser, shibuya.world ほか |
| `docs/bench/analysis/l4-unlimited-2026-09-28/l4_measure.py` | shibuya.engine, shibuya.engine.intent |
| `docs/bench/analysis/memory-stage1-2026-09-28/memory_measure.py` | shibuya.agents, shibuya.core.hashing, shibuya.llm.parser, shibuya.world.state |
| `docs/bench/analysis/memory-stage1-2026-09-28/recall_measure.py` | shibuya.agents, shibuya.core.hashing, shibuya.core.types, shibuya.engine ほか |
| `docs/bench/analysis/proximity-edge-2026-09-30/proximity_measure.py` | shibuya.engine, shibuya.engine.norm_meter, shibuya.perception |
| `docs/bench/analysis/q111-capacity-2026-09-30/q111_measure.py` | shibuya.agents.population, shibuya.agents.weekly, shibuya.engine |
| `docs/bench/analysis/s2-rules-1101/tools/measure_shortfall.py` | shibuya.engine, shibuya.engine.economy_stage2, shibuya.engine.rules, shibuya.engine.rules.table |
| `docs/bench/analysis/s2e-1102/tools/run_s2e.py` | shibuya.core.time_consts |
| `docs/bench/analysis/small-fixes-2026-09-29/q148_colocation_diag.py` | shibuya.engine, shibuya.engine.norm_meter |
| `docs/bench/analysis/small-fixes-2026-09-29/small_fixes_measure.py` | shibuya.engine.processes.goods_flow, shibuya.manifest.schema, shibuya.perception, shibuya.world.state |
| `docs/bench/analysis/spatial-2026-10/sp1/tools/accept_345.py` | shibuya.engine |
| `docs/bench/analysis/spatial-2026-10/sp1/tools/checks_sp1.py` | shibuya.engine.systems, shibuya.engine.systems.table |
| `docs/bench/analysis/spatial-2026-10/sp1/tools/diag_density_sp1.py` | shibuya.engine |
| `docs/bench/analysis/spatial-2026-10/sp1/tools/runs_sp1.py` | shibuya.engine |
| `docs/bench/analysis/spatial-2026-10/sp1b/tools/sp1b_2day.py` | shibuya.engine, shibuya.engine.space, shibuya.engine.space.nav1 |
| `docs/bench/analysis/spatial-2026-10/sp1b/tools/sp1b_events.py` | shibuya.engine, shibuya.engine.processes, shibuya.engine.processes.salient, shibuya.perception |
| `docs/bench/analysis/spatial-2026-10/sp1b/tools/sp1b_measure.py` | shibuya.engine, shibuya.engine.geometry, shibuya.engine.space, shibuya.engine.space.nav1 ほか |
| `docs/bench/analysis/store-memory-2026-09-28/choice_measure.py` | shibuya.agents, shibuya.core.hashing, shibuya.engine, shibuya.engine.memory ほか |
| `docs/bench/analysis/store-memory-2026-09-28/store_measure.py` | shibuya.agents, shibuya.core.hashing, shibuya.engine, shibuya.engine.store_memory ほか |
| `docs/bench/analysis/store-memory-2026-09-28/wom_measure.py` | shibuya.agents, shibuya.core.hashing, shibuya.core.types, shibuya.engine.wom ほか |
| `docs/bench/analysis/v3-2026-11/a/tools/measure_core.py` | shibuya.engine, shibuya.engine.systems, shibuya.engine.systems.conductor |
| `docs/bench/analysis/vocab-v3-candidates-2026-09-26/v3_extract.py` | shibuya.llm.contract, shibuya.llm.parser |
| `docs/bench/analysis/w6-regen-2026-09-28/eatery_measure.py` | shibuya.engine, shibuya.engine.processes.opening, shibuya.world, shibuya.world.state |
| `docs/bench/analysis/wallbounce-1003/10a/b56_measure.py` | shibuya.engine |
| `docs/bench/analysis/wallbounce-1003/10a/response_delay_measure.py` | shibuya.engine, shibuya.engine.conversation, shibuya.manifest.schema, shibuya.world.state |
| `docs/bench/analysis/wallbounce-1003/10b/hash_cost.py` | shibuya.engine, shibuya.engine.state_hashes, shibuya.engine.state_ledger |
| `docs/bench/analysis/wallbounce-1003/10b/hash_order_check.py` | shibuya.core.soa |
| `docs/bench/analysis/wallbounce-1003/10b/ledger_record.py` | shibuya.engine, shibuya.engine.state_ledger, shibuya.engine.state_ledger_ast |
| `docs/bench/analysis/wallbounce-1003/10c/count_dist_x1000.py` | shibuya.engine.processes.civic, shibuya.engine.processes.salient |
| `docs/bench/analysis/wallbounce-1003/10d/resume_check_10d.py` | shibuya.engine.state_ledger |
| `docs/bench/analysis/wallbounce-1003/r66/r66_measure.py` | shibuya.core.hashing, shibuya.engine, shibuya.perception |
| `docs/bench/analysis/wallbounce-1003/wage/measure_day.py` | shibuya.engine |
| `docs/bench/analysis/wallbounce-1003/wage/payroll_scale.py` | shibuya.agents.population |
| `docs/bench/analysis/wallbounce-1006/scripts/10f/ext_readers_ast.py` | shibuya.engine, shibuya.engine.state_ledger |
| `docs/bench/analysis/wallbounce-1006/scripts/10f/ext_state_writes_ast.py` | shibuya.engine, shibuya.engine.state_ledger |
| `docs/bench/analysis/wallbounce-1006/scripts/10f/state_format_probe.py` | shibuya.engine, shibuya.engine.resume, shibuya.engine.state_ledger |
| `docs/bench/analysis/wallbounce-1006/scripts/10f/stream_overlap_runtime.py` | shibuya.agents.schedule, shibuya.core.rng, shibuya.engine.processes.rail |
| `docs/bench/analysis/wallbounce-1006/scripts/count_agentless.py` | shibuya.engine, shibuya.engine.activity, shibuya.engine.conversation |
| `docs/bench/analysis/wallbounce-1012/10e/budget_10e.py` | shibuya.engine, shibuya.engine.resume, shibuya.engine.state_codec |
| `docs/bench/analysis/wallbounce-1012/10e/population_swap_check.py` | shibuya.agents.population |
| `docs/bench/analysis/wallbounce-1012/10e/w10_cell_stage_diff.py` | shibuya.world |
| `docs/bench/analysis/wallbounce-1012/bd35/tools/byte_check_bd35.py` | shibuya.engine, shibuya.engine.body, shibuya.engine.body.schedule |
| `docs/bench/analysis/wallbounce-1012/bd35/tools/perf_bd35.py` | shibuya.core.time_consts, shibuya.engine.body, shibuya.engine.body.rules, shibuya.engine.energy |
| `docs/bench/analysis/wallbounce-1012/bd35/tools/probe_bd35.py` | shibuya.engine, shibuya.engine.body |
| `docs/bench/analysis/wallbounce-1012/bd35/tools/two_day_bd35.py` | shibuya.engine, shibuya.engine.body |
| `docs/bench/analysis/wallbounce-1012/c0/tools/add_bridges_c0.py` | shibuya.engine.bridging, shibuya.engine.bridging.scan |
| `docs/bench/analysis/wallbounce-1012/c0/tools/count_osm_phone.py` | shibuya.engine.tools.places |
| `docs/bench/analysis/wallbounce-1012/c0/tools/port_pair_c0.py` | shibuya.engine.decision, shibuya.engine.decision.layer, shibuya.engine.decision.port |
| `docs/bench/analysis/wallbounce-1012/c0/tools/probe_c0.py` | shibuya.engine.bridging, shibuya.engine.bridging.ledger, shibuya.engine.systems, shibuya.engine.systems.probe ほか |
| `docs/bench/analysis/wallbounce-1012/c0/tools/signboard_volume_c0.py` | shibuya.engine.tools |
| `docs/bench/analysis/wallbounce-1012/c0/tools/wire_bridges_c0.py` | shibuya.engine.bridging, shibuya.engine.bridging.scan |
| `docs/bench/analysis/wallbounce-1012/ca1b/tools/run_ca1b.py` | shibuya.engine, shibuya.engine.calendar_self |
| `docs/bench/analysis/wallbounce-1012/ca2/tools/run_ca2.py` | shibuya.engine, shibuya.engine.calendar2, shibuya.engine.calendar2.arm, shibuya.engine.calendar2.layer ほか |
| `docs/bench/analysis/wallbounce-1012/ca3/tools/run_ca3.py` | shibuya.engine.calendar2, shibuya.engine.calendar2.arm, shibuya.engine.calendar2.layer, shibuya.engine.calendar3 ほか |
| `docs/bench/analysis/wallbounce-1012/ca31/tools/count_w17_bridges_ca31.py` | shibuya.agents.weekly, shibuya.engine |
| `docs/bench/analysis/wallbounce-1012/ca31/tools/ledger_rows_ca31.py` | shibuya.engine.bridging, shibuya.engine.bridging.scan |
| `docs/bench/analysis/wallbounce-1012/ca31/tools/shadow_run_ca31.py` | shibuya.engine |
| `docs/bench/analysis/wallbounce-1012/cf33/tools/branch_example.py` | shibuya.core.time_consts, shibuya.engine.experiment, shibuya.engine.experiment.branch, shibuya.engine.experiment.form ほか |
| `docs/bench/analysis/wallbounce-1012/cf33b/tools/switch_example.py` | shibuya.core.time_consts, shibuya.engine.experiment, shibuya.engine.experiment.branch, shibuya.engine.experiment.form ほか |
| `docs/bench/analysis/wallbounce-1012/cp2/tools/byte_check_cp2.py` | shibuya.economy |
| `docs/bench/analysis/wallbounce-1012/cp2/tools/k17_numbers.py` | shibuya.core.growth, shibuya.economy, shibuya.engine.ledger_api |
| `docs/bench/analysis/wallbounce-1012/ct_c1/tools/run_c1_onoff.py` | shibuya.engine.contact, shibuya.engine.contact.arm, shibuya.engine.contact.layer, shibuya.engine.events ほか |
| `docs/bench/analysis/wallbounce-1012/ct_c2/tools/run_c2.py` | shibuya.engine.contact, shibuya.engine.contact.arm, shibuya.engine.contact.layer, shibuya.engine.events ほか |
| `docs/bench/analysis/wallbounce-1012/duties1/tools/run_du1.py` | shibuya.engine.duties, shibuya.engine.duties.arm, shibuya.engine.duties.layer, shibuya.engine.events ほか |
| `docs/bench/analysis/wallbounce-1012/e13/tools/day_rows_e13.py` | shibuya.engine.events, shibuya.engine.events.log |
| `docs/bench/analysis/wallbounce-1012/e13/tools/probe_e13.py` | shibuya.engine.events, shibuya.engine.events.log, shibuya.engine.systems, shibuya.engine.systems.probe |
| `docs/bench/analysis/wallbounce-1012/ec21/tools/probe_ec21.py` | shibuya.engine.systems, shibuya.engine.systems.probe |
| `docs/bench/analysis/wallbounce-1012/ec21/tools/split_l2_l3.py` | shibuya.engine, shibuya.engine.economy_stage2, shibuya.world.state |
| `docs/bench/analysis/wallbounce-1012/ec21/tools/stage2_two_day.py` | shibuya.engine, shibuya.engine.decision, shibuya.engine.decision.layer, shibuya.engine.economy_stage2 |
| `docs/bench/analysis/wallbounce-1012/evalset-1-10/tools/select_situations.py` | shibuya.core.rng |
| `docs/bench/analysis/wallbounce-1012/j0/tools/arm_pair.py` | shibuya.engine.decision, shibuya.engine.decision.layer |
| `docs/bench/analysis/wallbounce-1012/j0/tools/cause_bytes.py` | shibuya.core.time_consts, shibuya.engine.events, shibuya.engine.events.log |
| `docs/bench/analysis/wallbounce-1012/m0/tools/recall_equivalence_m0.py` | shibuya.engine, shibuya.engine.memory, shibuya.engine.memory_store |
| `docs/bench/analysis/wallbounce-1012/mr65/tools/arms_mr65.py` | shibuya.core.time_consts, shibuya.engine.events.log, shibuya.engine.memory_store |
| `docs/bench/analysis/wallbounce-1012/mr65/tools/capacity_mr65.py` | shibuya.core.time_consts, shibuya.engine, shibuya.engine.events.log, shibuya.engine.memory_m1 ほか |
| `docs/bench/analysis/wallbounce-1012/p12/tools/probe_p12.py` | shibuya.engine.systems, shibuya.engine.systems.probe, shibuya.perception, shibuya.perception.facts |
| `docs/bench/analysis/wallbounce-1012/p12/tools/render_cost.py` | shibuya.perception |
| `docs/bench/analysis/wallbounce-1012/pop41/tools/ledger_w21.py` | shibuya.engine.bridging, shibuya.engine.bridging.scan |
| `docs/bench/analysis/wallbounce-1012/pop41b/tools/ledger_w21b.py` | shibuya.engine.bridging, shibuya.engine.bridging.scan |
| `docs/bench/analysis/wallbounce-1012/pop41c/tools/ledger_w21c.py` | shibuya.engine.bridging, shibuya.engine.bridging.scan |
| `docs/bench/analysis/wallbounce-1012/pop43/tools/ledger_pop43.py` | shibuya.engine.bridging, shibuya.engine.bridging.scan |
| `docs/bench/analysis/wallbounce-1012/pop43/tools/ledger_pop43_part2.py` | shibuya.engine.bridging, shibuya.engine.bridging.scan |
| `docs/bench/analysis/wallbounce-1012/pop43/tools/runs_pop43.py` | shibuya.agents.population |
| `docs/bench/analysis/wallbounce-1012/prox22/tools/index_cost.py` | shibuya.core.rng, shibuya.engine, shibuya.engine.proximity |
| `docs/bench/analysis/wallbounce-1012/prox22/tools/notice_cost.py` | shibuya.core.rng, shibuya.engine, shibuya.engine.proximity |
| `docs/bench/analysis/wallbounce-1012/prox22/tools/probe_poi_ref.py` | shibuya.engine, shibuya.engine.processes, shibuya.engine.processes.crowd, shibuya.engine.proximity |
| `docs/bench/analysis/wallbounce-1012/prox22/tools/reread_11c.py` | shibuya.engine, shibuya.engine.norm_meter, shibuya.engine.proximity, shibuya.engine.systems ほか |
| `docs/bench/analysis/wallbounce-1012/prox22/tools/resume_check.py` | shibuya.engine, shibuya.engine.proximity |
| `docs/bench/analysis/wallbounce-1012/r14/tools/build_ledger.py` | shibuya.engine.bridging, shibuya.engine.bridging.ledger, shibuya.engine.bridging.scan, shibuya.world.processes ほか |
| `docs/bench/analysis/wallbounce-1012/r14/tools/probe_r14.py` | shibuya.engine.bridging, shibuya.engine.bridging.ledger, shibuya.engine.systems, shibuya.engine.systems.probe |
| `docs/bench/analysis/wallbounce-1012/r14/tools/scan_expedients.py` | shibuya.engine.bridging, shibuya.engine.bridging.scan |
| `docs/bench/analysis/wallbounce-1012/r15/tools/add_bridges_r15.py` | shibuya.engine.bridging, shibuya.engine.bridging.scan |
| `docs/bench/analysis/wallbounce-1012/r15/tools/count_no_permission.py` | shibuya.engine, shibuya.engine.events, shibuya.engine.events.vocab |
| `docs/bench/analysis/wallbounce-1012/r15/tools/time_rights_r15.py` | shibuya.agents.population, shibuya.engine.rights, shibuya.engine.rights.initial, shibuya.engine.systems.build |
| `docs/bench/analysis/wallbounce-1012/rules42b/tools/runs_rules42b.py` | shibuya.economy |
| `docs/bench/analysis/wallbounce-1012/run-day-decomp/build_allow.py` | shibuya.engine, shibuya.engine.state_ledger_ast |
| `docs/bench/analysis/wallbounce-1012/run-day-decomp/dyn_process.py` | shibuya.engine, shibuya.engine.processes, shibuya.engine.processes.runner, shibuya.engine.state_hashes ほか |
| `docs/bench/analysis/wallbounce-1012/run-day-decomp/dyn_writers.py` | shibuya.engine, shibuya.engine.state_hashes, shibuya.engine.state_ledger |
| `docs/bench/analysis/wallbounce-1012/run-day-decomp/ext_coarse.py` | shibuya.engine.systems, shibuya.engine.systems.conductor, shibuya.engine.systems.probe, shibuya.engine.systems.table |
| `docs/bench/analysis/wallbounce-1012/run-day-decomp/guard_poc.py` | shibuya.engine, shibuya.perception.state, shibuya.world.state |
| `docs/bench/analysis/wallbounce-1012/run-day-decomp/guard_runs.py` | shibuya.core, shibuya.core.write_permit, shibuya.engine.systems, shibuya.engine.systems.overrides |
| `docs/bench/analysis/wallbounce-1012/run-day-decomp/ledger_writers.py` | shibuya.engine, shibuya.engine.state_ledger |
| `docs/bench/analysis/wallbounce-1012/run-day-decomp/multi_writers.py` | shibuya.engine, shibuya.engine.state_ledger, shibuya.engine.systems.table |
| `docs/bench/analysis/wallbounce-1012/run-day-decomp/probe_run.py` | shibuya.engine.systems, shibuya.engine.systems.conductor, shibuya.engine.systems.probe, shibuya.engine.systems.table |
| `docs/bench/analysis/wallbounce-1012/run-day-decomp/resolve_callers.py` | shibuya.engine, shibuya.engine.state_ledger_ast |
| `docs/bench/analysis/wallbounce-1012/run-day-decomp/resolve_calls_by_seg.py` | shibuya.engine |
| `docs/bench/analysis/wallbounce-1012/run-day-decomp/soa_writers_ast.py` | shibuya.engine, shibuya.engine.state_ledger, shibuya.engine.state_ledger_ast |
| `docs/bench/analysis/wallbounce-1012/s8b/tools/arm_meters.py` | shibuya.engine.speech, shibuya.engine.speech.layer, shibuya.engine.speech.port |
| `docs/bench/analysis/wallbounce-1012/s8b/tools/run_s8_onoff.py` | shibuya.engine.events, shibuya.engine.events.log, shibuya.engine.speech, shibuya.engine.speech.layer ほか |
| `docs/bench/analysis/wallbounce-1012/s8b/tools/two_day_resume.py` | shibuya.engine, shibuya.engine.resume, shibuya.engine.speech, shibuya.engine.speech.layer |
| `docs/bench/analysis/wallbounce-1012/tm32/tools/perf_tm32.py` | shibuya.core.time_consts, shibuya.engine, shibuya.engine.batching |
| `docs/bench/analysis/wallbounce-1012/tm32/tools/probe_tm32.py` | shibuya.engine.systems, shibuya.engine.systems.probe |
| `docs/bench/analysis/wallbounce-1012/tm32/tools/two_day_resume_tm32.py` | shibuya.core.time_consts |
| `docs/bench/analysis/wallbounce-1012/vb24/tools/resume_vb24.py` | shibuya.core.time_consts, shibuya.engine, shibuya.engine.economy_stage2, shibuya.engine.proximity ほか |
| `docs/bench/analysis/wallbounce-1012/vb24/tools/seat_probe_vb24.py` | shibuya.engine, shibuya.engine.processes, shibuya.engine.processes.crowd, shibuya.engine.proximity ほか |
| `docs/bench/analysis/wave2-2026-09-30/meal_bundle_measure.py` | shibuya.agents.weekly, shibuya.engine, shibuya.engine.energy, shibuya.perception ほか |
| `docs/bench/analysis/wave2-2026-09-30/noise_floor_measure.py` | shibuya.engine |
| `docs/bench/analysis/wave2-2026-09-30/social_measure.py` | shibuya.engine, shibuya.engine.classical |
| `docs/bench/analysis/wave2-2026-09-30/tenure_measure.py` | shibuya.agents.population, shibuya.agents.weekly, shibuya.engine |
| `docs/research/r60/r60_inventory.py` | shibuya.engine.wom |
| `docs/research/r60/r60_tape_targets.py` | shibuya.engine.wom, shibuya.llm.contract, shibuya.llm.parser |
