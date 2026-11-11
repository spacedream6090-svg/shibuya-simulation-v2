# src/shibuya/core

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 12 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../src/shibuya/core/__init__.py)

core: SoAレジストリ・dtype/バイト予算宣言・Philox RNG・ハッシュ・時刻/ID型。何にも依存しない。

- 読む試験(道筋で): `tests/tools/test_pkgmove.py`

## [budget.py](../../../../../../../src/shibuya/core/budget.py)

予算宣言表(docs/design/v2-budget-declaration.md)の読み取り器。

- 公開の関数とクラス
  - `BudgetRow`(クラス): 予算宣言表の1行。セルは Markdown の生文字列のまま(前後空白のみ除去)。
  - `budget_by_id`(関数): ``id`` → 行 の索引を作る。
  - `load_budget_table`(関数): 宣言表 §1〜§5 の全行を、Markdown 上の出現順で返す。
  - `parse_limit`(関数): 宣言値セルから数値上限を **best-effort** で1つ取り出す。
- import している内部モジュール: `shibuya.core.paths`
- 呼び手: `shibuya.core.soa`・`shibuya.llm.fleet`・`tools/c7/c7lib.py`・`tools/c8/c8lib.py`
- 読む試験: `tests/core/test_soa.py`・`tests/engine/state/test_move_prep_stage2.py`・`tests/engine/test_geometry_c9.py`・`tests/engine/test_scheduler_p3.py`・`tests/llm/test_fleet_contract.py`・`tests/test_budget_table.py`
- 環境変数: `SHIBUYA_BUDGET_MD`

## [growth.py](../../../../../../../src/shibuya/core/growth.py)

core.growth — 状態成長宣言(**正典 = D-R2-6**)と 24step→1日/30日 外挿の検査器。

- 公開の関数とクラス
  - `GrowthDeclaration`(クラス): 1つの成長する構造体の宣言(**D-R2-6 の 5 欄が必須**)。
  - `GrowthReport`(クラス): ``check_growth`` の報告(CI ゲート用)。
  - `GrowthRow`(クラス): ``check_growth`` の 1 構造体分の結果。
  - `Retention`(クラス): D-R2-6 の ``retention`` 欄 = **生ログ保持日数と圧縮先**。
  - `check_growth`(関数): 24step スモークの実測バイトを 1 日・``horizon_days`` 日へ外挿し cap と突き合わせる。
- import している内部モジュール: `shibuya.core.time_consts`
- 呼び手: `shibuya.economy.goods`・`shibuya.economy.ledger`・`shibuya.economy.stage2`・`shibuya.engine.events.log`・`shibuya.engine.growth_decl`・`shibuya.engine.run`・`shibuya.engine.systems.report`・`shibuya.world.processes.actual_log`・`shibuya.world.processes.first_batch`・`shibuya.world.processes.records`
- 読む試験: `tests/core/test_growth.py`・`tests/economy/cp2/head_goods_136fdbb.py`・`tests/economy/cp2/head_ledger_136fdbb.py`・`tests/economy/cp2/test_cp2_k17_capacity_and_overflow.py`・`tests/economy/test_goods.py`・`tests/economy/test_ledger.py`・`tests/engine/test_ledger_wiring.py`・`tests/engine/time/test_t0_time_consts.py`・`tests/world/processes/conftest.py`・`tests/world/processes/test_actual_log.py`

## [hashing.py](../../../../../../../src/shibuya/core/hashing.py)

core.hashing — 決定論ハッシュ(blake3/xxh64/sha256_cbor)と優先度キー。

- 公開の関数とクラス
  - `apply_key`(関数): LLM 応答の適用順キー第3要素(運用設計書 §2.4)。
  - `apply_key_array`(関数): ``apply_key`` のベクトル版(pending_apply の一括適用順づけ)。
  - `blake3_hex`(関数): blake3 の16進ダイジェスト(既定32バイト=64桁)。
  - `blake3_u64`(関数): blake3 の先頭8バイトを little-endian の unsigned int64 として読む。
  - `cbor_canonical`(関数): CBOR 正準符号化(``cbor2.dumps(obj, canonical=True)``)。
  - `priority_key`(関数): 資源競合の優先度キー第2要素(運用設計書 §2.2)。
  - `priority_key_array`(関数): ``priority_key`` のベクトル版(同じ刻みの全 intent 分)。
  - `relation_invite_key_array`(関数): 招待の相手を関係辺の重みで引く u64(``blake3(run_salt ‖ b"ri\x00" ‖ i64le(tick) ‖ i64le(agent_id))``)。
  - `sha256_cbor`(関数): CBOR 正準符号化 → SHA-256 の16進(vLLM の ``--prefix-caching-hash-algo sha256_cbor`` と同名算法)。
  - `wake_tiebreak`(関数): 同時刻起床イベントのタイブレーク第3要素(運用設計書 §2.5)。
  - `wake_tiebreak_array`(関数): ``wake_tiebreak`` のベクトル版(1 刻み分の起床イベント)。
  - `wander_key_array`(関数): 「あたり」歩行の行き先を選ぶ u64(``blake3(run_salt ‖ b"wd\x00" ‖ i64le(tick) ‖ i64le(agent_id))``)。
  - `xxh64`(関数): xxh64(変化検出・prefix キー・ルーティング用の高速ハッシュ)。
  - `xxh64_array`(関数): バイト列の列 → uint64 配列(セルB2/B4の変化検出用・要素ごとの逐次ループ=宣言済み)。
- 呼び手: `shibuya.agents.population`・`shibuya.agents.weekly`・`shibuya.build.sched.trial`・`shibuya.build.sched.w17_schedule`・`shibuya.economy.ledger`・`shibuya.engine.activity`・`shibuya.engine.arbiter`・`shibuya.engine.calendar_self`・`shibuya.engine.commit`・`shibuya.engine.processes.environment`・`shibuya.engine.relations`・`shibuya.engine.resume`・`shibuya.engine.scheduler`・`shibuya.engine.state_hashes`・`shibuya.engine.systems.judge`・`shibuya.engine.systems.observe`・`shibuya.engine.systems.state_io`・`shibuya.engine.tape`・`shibuya.llm`・`shibuya.llm.fleet`・`shibuya.perception.hashes`・`shibuya.perception.renderer`・`shibuya.perception.templates`・`shibuya.world.processes.registry`・`shibuya.world.state`
- 読む試験: `tests/core/test_types_hashing.py`・`tests/economy/cp2/head_ledger_136fdbb.py`・`tests/engine/test_env_and_sections_10f.py`・`tests/engine/test_fleet_wiring.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_state_ledger_10b.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/test_version_bump_10e.py`・`tests/golden_env.py`・`tests/llm/test_fleet.py`・`tests/perception/facts/head_renderer_136fdbb.py`・`tests/perception/test_hashes_state.py`・`tests/perception/test_renderer_golden.py`
- 読む試験(道筋で): `tests/engine/test_salt_seed_split_10f.py`
- 決定の ID: D-31・D-116

## [paths.py](../../../../../../../src/shibuya/core/paths.py)

core.paths — リポの根と包みの根を 1 か所で求める(移す段 2-2・計画 docs/reference/package-map-final-2026-11-09.md §7-3)。

- 公開の関数とクラス
  - `find_upward`(関数): ``start`` から上へ辿り、``relpath`` のファイルを含む最初のディレクトリ(無ければ ``FileNotFoundError``)。
  - `module_dir`(関数): モジュールの名(``__name__``)→ そのファイルのあるディレクトリ(包みの根から名の部品をたどる)。
  - `resolve_repo_path`(関数): 相対パスはリポの根から、絶対パスはそのまま(検収後 P4: 作業ディレクトリに依らない)。
- 呼び手: `shibuya.core.budget`・`shibuya.economy.wages`・`shibuya.engine.bridging.ledger`・`shibuya.engine.bridging.scan`・`shibuya.engine.calendar`・`shibuya.engine.classical`・`shibuya.engine.economy_stage2`・`shibuya.engine.energy`・`shibuya.engine.resume`・`shibuya.engine.rules.table`・`shibuya.engine.systems.allow`・`shibuya.engine.systems.static_check`・`shibuya.world.processes.constitution`
- 読む試験: `tests/engine/state/test_move_prep_stage2.py`・`tests/engine/test_10a_review_fixes.py`・`tests/tools/test_bytecheck.py`

## [rng.py](../../../../../../../src/shibuya/core/rng.py)

core.rng — カウンタベース乱数(numpy Philox4x64)のドメイン分離。

- 公開の関数とクラス
  - `derive_key`(関数): (master_seed, domain) → Philox4x64 の 128bit 鍵 (k0, k1)。
  - `k19_counter_array`(関数): :func:`k19_counters` の配列の版(0 語目を 0 に空け、鍵の列を 1〜3 語目に置く=(n, 1 + 列の数) の uint64)。
  - `k19_counters`(関数): 10e(E4・K19)の鍵の並べ方。0 語目を 0 に空け、鍵の語を 1〜3 語目に置く。
  - `key_time_from_t_ns`(関数): 〔v3-0a 案 A(指示書 11-04 §2-1)〕乱数の鍵・呼びの id・時間帯の材料に入れる時刻の整数を、通しの時刻 ``t_ns``
  - `philox`(関数): 鍵=derive_key・カウンタ=(counters を 4 語に詰めた 256bit) の Philox ビット生成器。
  - `philox_array`(関数): ``philox(master_seed, domain, *counters[i]).random_raw(words)`` を全行まとめて引く((n, words) の uint64)。
  - `run_tick_key`(関数): counter の乱数の鍵に入れる時刻 = ``day_key0 × 1 日の刻みの数 + T``。
  - `stream`(関数): 用途別の Generator。例: ``stream(seed, "agent.habit", agent_id, tick)``。
  - `time_key_from_t_ns`(関数): 〔第 1 期 1-1 T0・TM7 (d) の準備〕``run_tick_key`` と同じ鍵の値を、刻みの番号でなく通しの時刻 ``t_ns``
  - `unit_float`(関数): uint64 → [0, 1) の float64(numpy の ``Generator.random()`` と同じ写し方=上の 53 bit × 2^-53)。
- import している内部モジュール: `shibuya.core.time_consts`
- 呼び手: `shibuya.agents.population`・`shibuya.agents.schedule`・`shibuya.build.field.w13_weather`・`shibuya.build.geo.w3_distances`・`shibuya.build.pop.attr_fns`・`shibuya.build.pop.w16_population`・`shibuya.build.pop.w21_apply`・`shibuya.build.pop.w21_build`・`shibuya.build.pop.w21_build_b`・`shibuya.build.pop.w21_checks`・`shibuya.build.pop.w21_households`・`shibuya.build.pop.w21_port10`・`shibuya.build.pop.w21_prior`・`shibuya.build.sched.w20_calendar_1a`・`shibuya.cli`・`shibuya.core.wage_formula`・`shibuya.engine.calendar2.layer`・`shibuya.engine.calendar2.port`・`shibuya.engine.calendar3.layer`・`shibuya.engine.calendar3.port`・`shibuya.engine.chooser`・`shibuya.engine.classical`・`shibuya.engine.contact.device`・`shibuya.engine.contact.layer`・`shibuya.engine.contact.port`・`shibuya.engine.decision.layer`・`shibuya.engine.decision.port`・`shibuya.engine.duties.layer`・`shibuya.engine.duties.port`・`shibuya.engine.energy`・`shibuya.engine.geometry`・`shibuya.engine.memory_m1`・`shibuya.engine.processes.civic`・`shibuya.engine.processes.environment`・`shibuya.engine.processes.goods_flow`・`shibuya.engine.processes.logistics`・`shibuya.engine.processes.rail`・`shibuya.engine.processes.salient`・`shibuya.engine.proximity`・`shibuya.engine.rng_audit`・`shibuya.engine.run`・`shibuya.engine.space.nav1`・`shibuya.engine.speech_clock`・`shibuya.engine.systems.build`・`shibuya.engine.systems.decide`・`shibuya.engine.systems.report`・`shibuya.llm.mock`・`shibuya.perception.attention`・`shibuya.perception.p_notice`・`shibuya.world.assets`・`tools/instruments/dm_eval/bias.py`・`tools/instruments/dm_eval/judge.py`・`tools/instruments/dm_eval/situations.py`
- 読む試験: `tests/c8/test_ensemble.py`・`tests/economy/test_anchors.py`・`tests/economy/test_pricing.py`・`tests/engine/body/test_body_same_values.py`・`tests/engine/processes/test_rng_scheme_10c.py`・`tests/engine/proximity/test_philox_array.py`・`tests/engine/proximity/test_rule.py`・`tests/engine/state/test_move_prep_stage2.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_salt_seed_split_10f.py`・`tests/engine/test_state_checks_10f.py`・`tests/engine/test_state_format_10f.py`・`tests/engine/test_version_bump_10e.py`・`tests/engine/time/test_t0_rng_key.py`・`tests/engine/time/test_v30a_key_sites.py`・`tests/test_rng_properties.py`
- 決定の ID: 11-04/§2-1・第 330

## [serialize.py](../../../../../../../src/shibuya/core/serialize.py)

core.serialize — SoA レジストリの checkpoint(.npz + zstd)と膨張率 M7 の測定。

- 公開の関数とクラス
  - `BloatMeasurement`(クラス): M7(直列化↔in-RAM 膨張率)の測定値。
  - `SaveResult`(クラス): ``save_registry`` の結果。
  - `load_registry`(関数): ``save_registry`` で書いたファイルを読み、``state_hash`` の一致を検査して返す。
  - `measure_bloat`(関数): checkpoint を読み直して M7(膨張率)を測る。
  - `save_registry`(関数): レジストリを ``.npz``(非圧縮)→ zstd で1ファイルに保存する。
- import している内部モジュール: `shibuya.core.soa`
- 読む試験: `tests/core/test_serialize.py`・`tests/engine/test_determinism_t1_t2_t4.py`
- 決定の ID: 第 141

## [soa.py](../../../../../../../src/shibuya/core/soa.py)

core.soa — SoA(構造体の配列でなく配列の構造体)レジストリとバイト予算宣言(M9)。

- 公開の関数とクラス
  - `BudgetReport`(クラス): レジストリ全体の予算報告。
  - `FieldDecl`(クラス): 1フィールドの宣言(M9)。
  - `FieldReport`(クラス): ``budget_report`` の1行。
  - `Registry`(クラス): SoA 状態のレジストリ(個体オブジェクトを作らない)。
  - `default_per_entity_byte_cap`(関数): 種別(``"agent"``/``"cell"``)ごとの既定バイト上限を予算宣言表から読む。
- import している内部モジュール: `shibuya.core.budget`
- 呼び手: `shibuya.agents.state`・`shibuya.core.serialize`・`shibuya.perception.state`・`shibuya.world.state`
- 読む試験: `tests/core/test_serialize.py`・`tests/core/test_soa.py`・`tests/engine/test_state_ledger_10b.py`
- 読む試験(道筋で): `tests/engine/systems/test_fix_guards.py`・`tests/engine/systems/test_stage_a_guard.py`
- 決定の ID: 第 330

## [time_consts.py](../../../../../../../src/shibuya/core/time_consts.py)

core.time_consts — 時間の定数と、秒と刻みの換算(第 1 期 1-1 時計 T0・TM7・TM8)。

- 公開の関数とクラス
  - `seconds_to_steps`(関数): 秒 → 刻みの数(整数)。
  - `steps_to_seconds`(関数): 刻みの数 → 秒(整数・丸め無し=``steps × 幅``)。``seconds_to_steps`` の右逆(``seconds_to_steps(steps_to_seconds(n)) == n``)。
- 呼び手: `shibuya.agents.schedule`・`shibuya.agents.weekly`・`shibuya.build.audit.w20_acceptance_pack`・`shibuya.build.field.common`・`shibuya.build.field.w10_noise`・`shibuya.build.field.w12_external_nodes`・`shibuya.build.field.w12_real_timetables`・`shibuya.build.field.w13_weather`・`shibuya.build.field.w7_planspec`・`shibuya.build.lang.w14_signage`・`shibuya.build.pop.w21_persona`・`shibuya.build.sched.pool_facts`・`shibuya.build.sched.trial`・`shibuya.build.sched.vocab`・`shibuya.build.sched.w17_schedule`・`shibuya.build.sched.w20_calendar_1a`・`shibuya.build.sched.w20_w21_port`・`shibuya.build.space.navmesh1`・`shibuya.build.vis.w9_shadow`・`shibuya.cli`・`shibuya.core.growth`・`shibuya.core.rng`・`shibuya.core.types`・`shibuya.economy.ledger`・`shibuya.engine.activity`・`shibuya.engine.arbiter`・`shibuya.engine.batching`・`shibuya.engine.body.model`・`shibuya.engine.body.rules`・`shibuya.engine.calendar`・`shibuya.engine.calendar2.layer`・`shibuya.engine.calendar3.layer`・`shibuya.engine.calendar_self`・`shibuya.engine.calendar_shadow`・`shibuya.engine.classical`・`shibuya.engine.clock`・`shibuya.engine.contact.attention`・`shibuya.engine.contact.deliver`・`shibuya.engine.contact.device`・`shibuya.engine.contact.layer`・`shibuya.engine.duties.knowledge`・`shibuya.engine.duties.layer`・`shibuya.engine.economy_stage2`・`shibuya.engine.energy`・`shibuya.engine.events.log`・`shibuya.engine.experiment.apply`・`shibuya.engine.experiment.branch`・`shibuya.engine.experiment.form`・`shibuya.engine.experiment.layer`・`shibuya.engine.growth_decl`・`shibuya.engine.memory_m1`・`shibuya.engine.memory_store`・`shibuya.engine.memory_trace`・`shibuya.engine.norm_meter`・`shibuya.engine.presence`・`shibuya.engine.processes.civic`・`shibuya.engine.processes.environment`・`shibuya.engine.processes.goods_flow`・`shibuya.engine.processes.logistics`・`shibuya.engine.processes.opening`・`shibuya.engine.processes.rail_events`・`shibuya.engine.processes.runner`・`shibuya.engine.processes.salient`・`shibuya.engine.processes.traffic`・`shibuya.engine.regional_clock`・`shibuya.engine.relations`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.engine.scheduler`・`shibuya.engine.solar`・`shibuya.engine.space.nav1`・`shibuya.engine.speech.layer`・`shibuya.engine.speech.port`・`shibuya.engine.speech_clock`・`shibuya.engine.store_choice`・`shibuya.engine.store_memory`・`shibuya.engine.systems.act`・`shibuya.engine.systems.body`・`shibuya.engine.systems.boxes`・`shibuya.engine.systems.build`・`shibuya.engine.systems.conductor`・`shibuya.engine.systems.decide`・`shibuya.engine.systems.judge`・`shibuya.engine.systems.report`・`shibuya.engine.systems.state_io`・`shibuya.llm.contract`・`shibuya.perception.normalize`・`shibuya.perception.renderer`・`shibuya.world.assets`・`shibuya.world.processes.actual_log`・`shibuya.world.state`・`tools/instruments/anchor_gauge.py`・`tools/instruments/batch_width_gauge.py`・`tools/instruments/dm_eval/judge.py`・`tools/instruments/dm_eval/situations.py`
- 読む試験: `tests/build_field/test_w12_real_timetables.py`・`tests/economy/cp2/head_ledger_136fdbb.py`・`tests/economy/cp2/test_cp2_event_links.py`・`tests/engine/batching/test_conductor_windows.py`・`tests/engine/batching/test_window_queue.py`・`tests/engine/body/body_fixtures.py`・`tests/engine/bridging/test_manifest_rules_bridges.py`・`tests/engine/calendar2/_ca2.py`・`tests/engine/calendar2/test_ca2_units.py`・`tests/engine/calendar3/_ca3.py`・`tests/engine/clock/test_tm2_talk_clock.py`・`tests/engine/clock/test_tm3_step_scope.py`・`tests/engine/clock/test_tm4_regional_clock.py`・`tests/engine/contact/_c1.py`・`tests/engine/contact/_c2.py`・`tests/engine/contact/test_c1_runs.py`・`tests/engine/contact/test_c2_charge.py`・`tests/engine/contact/test_c2_runs.py`・`tests/engine/decision/test_j0_cause_columns.py`・`tests/engine/duties/_du.py`・`tests/engine/events/test_e_log_invariance.py`・`tests/engine/events/test_e_log_links_actual.py`・`tests/engine/events/test_e_log_schema.py`・`tests/engine/events/test_e_manifest_events.py`・`tests/engine/experiment/_x33.py`・`tests/engine/experiment/test_cf33b_switch.py`・`tests/engine/experiment/test_x33_branch.py`・`tests/engine/memory/test_m0_render_bytes.py`・`tests/engine/memory/test_m0_shown_recorded.py`・`tests/engine/memory/test_m0_store_schema.py`・`tests/engine/memory/test_m1_runs.py`・`tests/engine/memory/test_m1_strength.py`・`tests/engine/memory/test_m2_cue.py`・`tests/engine/memory/test_m3_impression_and_trace.py`・`tests/engine/memory/test_m4_m5_people.py`・`tests/engine/memory/test_mr65_grain_and_cli.py`・`tests/engine/memory/test_mr65_review_fixes.py`・`tests/engine/multiday/test_md23_body_events.py`・`tests/engine/multiday/test_md23_resume.py`・`tests/engine/multiday/test_md23_tool.py`・`tests/engine/processes/test_absent_processes_1102.py`・`tests/engine/rights/test_rights_manifest.py`・`tests/engine/speech/test_speech_default_off_invariance.py`・`tests/engine/test_fleet_wiring.py`・`tests/engine/time/test_t0_no_tick_word.py`・`tests/engine/time/test_t0_rng_key.py`・`tests/engine/time/test_t0_tickctx_equivalence.py`・`tests/engine/time/test_t0_time_consts.py`・`tests/engine/time/test_t0_tm9_fields.py`・`tests/engine/time/test_v30a_key_sites.py`・`tests/perception/facts/head_renderer_136fdbb.py`・`tests/tools/test_dm_eval.py`・`tests/tools/test_repo_guide.py`
- 読む試験(道筋で): `tests/engine/time/test_t0_literal_count.py`

## [types.py](../../../../../../../src/shibuya/core/types.py)

core.types — 時刻・ID・イベントクラスの固定 dtype 定義。

- 公開の関数とクラス
  - `EventClass`(クラス): イベントクラスと class_rank(運用設計書 §2.5・昇順が優先)。
  - `as_agent_id`(関数): 範囲検査つきの AgentId 変換。
  - `as_cell_id`(関数): 範囲検査つきの CellId 変換。
  - `as_resource_id`(関数): 範囲検査つきの ResourceId 変換。
  - `max_tick`(関数): t_sim_ns が **刻みの中のどのオフセットでも** int64 に収まる刻みの番号の絶対値上限。
  - `split_t_sim_ns`(関数): t_sim_ns → (刻みの番号 ``tick``, offset_ns)。``t_sim_ns`` の逆写像(floor 除算=負時刻でも整合)。
  - `t_sim_ns`(関数): (刻みの番号 ``tick``, 刻みの中のオフセット[ns]) → t_sim_ns(int64 ナノ秒=``SimTime``)。
- import している内部モジュール: `shibuya.core.time_consts`
- 呼び手: `shibuya.agents.state`・`shibuya.engine.arbiter`・`shibuya.engine.calendar`・`shibuya.engine.clock`・`shibuya.engine.commit`・`shibuya.engine.conversation`・`shibuya.engine.events.log`・`shibuya.engine.memory`・`shibuya.engine.processes.opening`・`shibuya.engine.rights.ledger`・`shibuya.engine.rights.record`・`shibuya.engine.run`・`shibuya.engine.scheduler`・`shibuya.engine.speech.port`・`shibuya.llm.mock`・`tools/fig/fig_calls_by_hour.py`
- 読む試験: `tests/agents/test_state.py`・`tests/core/test_types_hashing.py`・`tests/engine/processes/test_salient.py`・`tests/engine/state/test_class_ids.py`・`tests/engine/test_arbiter.py`・`tests/engine/test_change_detect_p6.py`・`tests/engine/test_clock.py`・`tests/engine/test_conversation.py`・`tests/engine/test_l4_budget.py`・`tests/engine/test_scheduler.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_sleep_suppression_d56.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/time/test_t0_tickctx_equivalence.py`・`tests/engine/time/test_t0_time_consts.py`・`tests/fig/test_fig_smoke.py`

## [wage_formula.py](../../../../../../../src/shibuya/core/wage_formula.py)

core.wage_formula — 職業 × 性 × 年齢 × 雇用形態の賃金の式と表の読み解き(賃金構造基本統計調査 令和 7 年=R-107)。

- 公開の関数とクラス
  - `WageTables`(クラス): 実行時の賃金の表(配列は書き込み禁止)。欄の名と形は ``build.pop.attr_fns.AttrTablesB`` の賃金の欄と同じ。
  - `apply_floor`(関数): 〔検収 M1〕最低賃金法の床(4 条 2 項=足りない部分は最低賃金と同じ定めとみなす)。時給(月 ÷ 月の時間の目安)が床を
  - `median_check`(関数): 計器(構築側の点検=合否なし): 職種 × 性ごとの月の賃金の中央値と、第18表の中位数(一般労働者)との差。
  - `month_hours`(関数): 〔検収 M1〕体ごとの月の所定内の時間の目安[時]\(最低賃金の床=時給 × この時間)。
  - `occupation_wages`(関数): 体ごとの月の賃金[円]\(所定内給与)と出どころ(:data:`BASIS_NAMES` の番号)。純粋(表と入力を読むだけ)。
  - `parse_wage_tables`(関数): 賃金構造 令和 7 年(第9・6・18 表と短時間 第2表の写しの行)→ 賃金の欄(企業規模計・円と時間)。
  - `wage_quantile`(関数): 第18表の所定内給与額の階級の度数(職種 × 男女)から分位 u の値[円/月]\(階級の中は一様=宣言)。
  - `wage_uniform`(関数): 体ごとの分位 u(用途名 :data:`WAGE_DOMAIN`・``counters`` は (n, ≤3) の鍵の語・1 語だけ引く)。
  - `wage_values`(関数): (所定内給与[円/月], 時間あたり[円], 年の賃金[円])。対象外(``ok`` が偽)は −1。
- import している内部モジュール: `shibuya.core.rng`
- 呼び手: `shibuya.build.pop.attr_fns`・`shibuya.build.pop.w21_money`・`shibuya.economy.wages`
- 読む試験: `tests/economy/test_wage_occupation.py`
- 読む試験(道筋で): `tests/tools/test_pkgmove.py`
- 決定の ID: 10-12/§4-11・10-13b/§7・R-107

## [write_permit.py](../../../../../../../src/shibuya/core/write_permit.py)

core.write_permit — 系ごとの「書いてよい SoA の列」(第 1 期 1-0・段 A)。

- 公開の関数とクラス
  - `allows`(関数): 置き場 ``place`` の列 ``name`` を解いてよいか(許可が無ければ常に真)。
  - `current`(関数): いまの許可(``None``=制限なし)。
  - `enabled`(関数): 書きの検査(段 A の ①)が入っているか。
  - `scope`(関数): ``with scope(許可):`` の間だけ許可を置く(切替口で外していれば置かない)。入れ子は内側が勝ち、出るときに戻す。
  - `set_enabled`(関数): 書きの検査を入れる/外す(試験と重さの測り用の切替口)。
- 呼び手: `shibuya.agents.state`・`shibuya.engine.systems.guard`・`shibuya.perception.state`・`shibuya.world.state`
- 読む試験: `tests/economy/cp2/test_cp2_writes_declared.py`・`tests/engine/decision/test_j0_writes_declared.py`・`tests/engine/events/test_e_cause_three_kinds.py`・`tests/engine/events/test_e_writes_declared.py`・`tests/engine/experiment/test_x33_run.py`・`tests/engine/memory/test_m0_store_schema.py`・`tests/engine/memory/test_m0_writes_declared.py`・`tests/engine/proximity/test_runs.py`・`tests/engine/speech/test_speech_writes_declared.py`・`tests/engine/systems/test_boxes.py`・`tests/engine/systems/test_fix_guards.py`・`tests/engine/systems/test_guard_runs.py`・`tests/engine/systems/test_stage_a_guard.py`・`tests/engine/tools/test_c0_contacts_in_relations.py`・`tests/engine/tools/test_c0_signboard_mark_invariance.py`
- 環境変数: `SHIBUYA_WRITE_GUARD`
