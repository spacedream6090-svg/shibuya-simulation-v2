# src/shibuya/foundation/vocab

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 8 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/foundation/vocab/__init__.py)

(冒頭の説明なし)

## [act_codes.py](../../../../../../../../src/shibuya/foundation/vocab/act_codes.py)

foundation.vocab.act_codes — 割る段で ``llm/undefined.py`` を割った割り先(全ファイルの表 §4・名の表は``tools/pkgmove/map.toml`` の割る行)。

- import している内部モジュール: `shibuya.foundation.vocab.actions`
- 呼び手: `shibuya.act.activity`・`shibuya.act.commit`・`shibuya.act.intake.from_words`・`shibuya.act.intake.undefined`・`shibuya.act.intent`・`shibuya.act.target`・`shibuya.engine.resolve`・`shibuya.mind.judge.decision.layer`・`shibuya.mind.memory.memory`・`shibuya.runtime.run`・`shibuya.runtime.systems.judge`・`shibuya.runtime.systems.talk`
- 読む試験: `tests/economy/stage2/test_stage2_calls.py`・`tests/engine/processes/test_civic.py`・`tests/engine/processes/test_crowd.py`・`tests/engine/processes/test_rail.py`・`tests/engine/processes/test_rail_board_intent.py`・`tests/engine/processes/test_rail_return.py`・`tests/engine/test_c9b_targets_attention.py`・`tests/engine/test_conversation_invite.py`・`tests/engine/test_defect_fixes_1103.py`・`tests/engine/test_geometry_c9.py`・`tests/engine/test_intent_hold.py`・`tests/engine/test_ledger_wiring.py`・`tests/engine/test_memory_recall.py`・`tests/engine/test_memory_record.py`・`tests/engine/test_move_destination.py`・`tests/engine/test_parser_contract.py`・`tests/engine/test_plan_sleep_d62.py`・`tests/engine/test_presence_exit_walk.py`・`tests/engine/test_renderer_wiring.py`・`tests/engine/test_resolve.py`・`tests/engine/test_seat_release_2_4.py`・`tests/engine/test_stage3_small_fixes.py`・`tests/engine/test_store_choice.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/test_two_phase.py`・`tests/engine/test_undefined_action.py`
- 決定の ID: D-71・D-116

## [actions.py](../../../../../../../../src/shibuya/foundation/vocab/actions.py)

llm.contract — 行動契約書(R4・v1)の**唯一の正典置き場**(語彙・契約表・対象の型)。

- 公開の関数とクラス
  - `ActionSpec`(クラス): 行動契約表の**1行**(§2.1 の12語 / §2.2 の役割語)。
  - `Target`(クラス): 「対象」欄の解釈結果。``raw`` は**常に逐語**(文面凍結のため加工しない)。
  - `TargetKind`(クラス): 「対象」欄の型(行動契約書 §1 の ``<セルID|物カテゴリ|人ID|なし>`` の一般化)。
  - `Until`(クラス): 「まで」欄の解釈結果。
  - `UntilKind`(クラス): 「まで」欄の型(アジェンダ §1-2 の 6 型)。
  - `action_code_of`(関数): 行動語 → コード。12語は 0..11・役割語は 12..・未知は ``UNDEFINED_ACTION``。
  - `action_words`(関数): その版でパーサが受理する行動語(v1=24 語・v2=25 語・v3=23 語)。
  - `append_comment`(関数): 〔1-8b〕応答の 2 行目の最後に ``ひと言:`` の欄を足す(mock と古典の方策の発話=発話の口の入口)。
  - `check_vocab_version`(関数): ``vocab_version`` を検査して正規化する(不正値は ``ValueError``)。
  - `compat_word`(関数): ある版の語を別の版の語彙で読む(``VOCAB_COMPAT``・F)。対応が無い語はそのまま返す。
  - `cross_action_words`(関数): その版の**種別横断語**(v1=12 語・v2=13 語・v3=11 語+なし)。B0 の出力規約に出す並び。
  - `engine_action_codes`(関数): その版で**エンジンに適用分岐がある**語 → コード(役割語は含まない)。
  - `format_two_line`(関数): 行動契約書 §1 の固定2行形に整形する(字数は呼び出し側が守る)。
  - `format_two_line_v3`(関数): v3 の固定 2 行形に整形する(字数は呼び出し側が守る)。``until`` の既定は語の 1 つ。
  - `is_role_action`(関数): §2.2 の役割語か(``"v3"`` では 並ぶ は横断語=役割語ではない)。
  - `parse_target`(関数): 「対象」欄の文字列 → ``Target``。**例外を投げない**。
  - `parse_until`(関数): 「まで」欄の文字列 → ``Until``。**例外を投げない**。
  - `resolve_landmark`(関数): 固有名 → POI 索引(``None``=解決できない)。
  - `role_action_words`(関数): その版の**役割語**(v1/v2=12 語=``ROLE_ACTION_WORDS`` そのもの・v3=11 語)。
  - `safe_action_word`(関数): その版の安全弁の語(**失敗しない**・未定義行動の落ち先)。v1/v2=待機・v3=なし。
  - `spec_of`(関数): 行動語 → 契約行(未知は None)。``"v2"`` で「食事」・``"v3"`` で v3 の 23 行を引く。
- import している内部モジュール: `shibuya.foundation.time_consts`
- 呼び手: `shibuya.act.activity`・`shibuya.act.intake.from_words`・`shibuya.act.intake.parser`・`shibuya.act.intake.undefined`・`shibuya.act.intent`・`shibuya.engine.resolve`・`shibuya.foundation.vocab.act_codes`・`shibuya.foundation.vocab.events`・`shibuya.interim_bundles.calendar2.layer`・`shibuya.mind.judge.classical`・`shibuya.mind.judge.decision.ports`・`shibuya.mind.plan.contact_port`・`shibuya.mind.plan.duties_port`・`shibuya.runtime.clocks.speech`・`shibuya.runtime.inference.bridge`・`shibuya.runtime.inference.fleet`・`shibuya.runtime.inference.mock`・`shibuya.runtime.run`・`shibuya.runtime.systems.assemble`・`shibuya.society.norm_meter`・`shibuya.society.speech.layer`・`shibuya.world.facts.rights.record`・`tools/c6/c6lib.py`・`tools/fig/fig_ab7_actions.py`・`tools/instruments/dm_eval/judge.py`・`tools/instruments/dm_eval/situations.py`・`tools/vocab/adjudicate.py`
- 読む試験: `tests/c6/test_c6lib_aggregate.py`・`tests/c8/test_ablations_ab7.py`・`tests/engine/decision/_j0.py`・`tests/engine/decision/test_j0_mock_equivalence.py`・`tests/engine/decision/test_j0_port_schema.py`・`tests/engine/decision/test_j0_shuffle_invariance.py`・`tests/engine/duties/test_du_runs.py`・`tests/engine/events/test_e_vocab_is_closed.py`・`tests/engine/rights/test_rights_events.py`・`tests/engine/speech/test_speech_choice_utterance.py`・`tests/engine/speech/test_speech_default_off_invariance.py`・`tests/engine/speech/test_speech_on_reaches_addressee.py`・`tests/engine/speech/test_speech_port_schema.py`・`tests/engine/speech/test_wom_from_utterance_roundtrip.py`・`tests/engine/tape_analysis.py`・`tests/engine/test_c9b_targets_attention.py`・`tests/engine/test_classical_policy.py`・`tests/engine/test_conversation.py`・`tests/engine/test_intent_chooser.py`・`tests/engine/test_intent_hold.py`・`tests/engine/test_intent_mode_open.py`・`tests/engine/test_llm_mock.py`・`tests/engine/test_move_destination.py`・`tests/engine/test_parser_contract.py`・`tests/engine/test_presence_exit_walk.py`・`tests/engine/test_stage3_small_fixes.py`・`tests/engine/test_state_format_10f.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/test_undefined_action.py`・`tests/engine/test_vocab_v2_eat.py`・`tests/engine/tools/test_c0_affordance_from_registry.py`・`tests/llm/test_contract.py`・`tests/llm/test_fleet.py`・`tests/llm/test_mock_v3.py`・`tests/llm/test_parser.py`・`tests/llm/test_undefined.py`・`tests/llm/test_vocab_v2.py`・`tests/perception/test_b6_invite.py`・`tests/perception/test_templates.py`・`tests/perception/test_vocab_v2_templates.py`・`tests/test_cli_vocab_version.py`・`tests/tools/test_dm_eval.py`
- 決定の ID: D-71・D-89・D-92・D-116・第 223・第 271・第 274・第 275

## [agent_codes.py](../../../../../../../../src/shibuya/foundation/vocab/agent_codes.py)

foundation.vocab.agent_codes — 割る段で ``agents/state.py`` を割った割り先(全ファイルの表 §4・名の表は``tools/pkgmove/map.toml`` の割る行)。

- 公開の関数とクラス
  - `Activity`(クラス): 現在の行動状態(行動契約書 §2.1 の効果が落ちる先)。
  - `ActivityKind`(クラス): 活動の種別(``activity_kind``・二層の実装アジェンダ §2 の表)。
  - `AgentKind`(クラス): 個体の種別。
  - `IntentKind`(クラス): 意図の対象の種類(``intent_kind``・段 2c)。``intent_target`` の意味を決める。
  - `ResultCode`(クラス): 「直前の結果」コード(行動契約書 §2.1 失敗の意味論 / §6 の 50 tok 欄の素材)。
  - `WakeCondition`(クラス): 起床条件(知覚契約書 §6 不応期表の**11 行と 1 対 1**)+ **活動の満了**(二層・段 2)。
  - `focus_code_for_person`(関数): 個体 id → ``focus_target`` の符号化(そのまま=非負)。
  - `focus_code_for_poi`(関数): POI 索引 → ``focus_target`` の符号化(``-2 - poi_id`` ≤ -2)。
  - `focus_is_person`(関数): ``focus_target`` が個体を指しているか。
  - `focus_is_poi`(関数): ``focus_target`` が POI を指しているか。
  - `focus_poi_of`(関数): ``focus_target`` → POI 索引(POI でない要素は ``-1``)。
- import している内部モジュール: `shibuya.foundation.types`
- 呼び手: `shibuya.act.activity`・`shibuya.act.commit`・`shibuya.act.intake.from_words`・`shibuya.act.intent`・`shibuya.act.target`・`shibuya.economy.rules_bind`・`shibuya.engine.resolve`・`shibuya.interfaces.cli.main`・`shibuya.interim_bundles.calendar2.layer`・`shibuya.interim_bundles.calendar3.layer`・`shibuya.interim_bundles.calendar_self`・`shibuya.interim_bundles.contact.layer`・`shibuya.interim_bundles.duties.layer`・`shibuya.mind.judge.classical`・`shibuya.mind.judge.decision.ports`・`shibuya.mind.judge.store_choice`・`shibuya.mind.memory.familiarity`・`shibuya.mind.memory.memory`・`shibuya.mind.memory.memory_shops`・`shibuya.mind.memory.memory_store`・`shibuya.mind.memory.store_memory`・`shibuya.mind.plan.contact_attention`・`shibuya.mind.plan.contact_habit`・`shibuya.mind.relations.layer`・`shibuya.mind.system1.change_detect`・`shibuya.perception.renderer`・`shibuya.runtime.arbiter`・`shibuya.runtime.clocks.step_scope`・`shibuya.runtime.run`・`shibuya.runtime.systems.assemble`・`shibuya.runtime.systems.body`・`shibuya.runtime.systems.decide`・`shibuya.runtime.systems.judge`・`shibuya.runtime.systems.llm_io`・`shibuya.runtime.systems.report`・`shibuya.runtime.systems.state_io`・`shibuya.runtime.systems.talk`・`shibuya.society.conversation`・`shibuya.society.norm_meter`・`shibuya.world.body.energy`・`shibuya.world.body.rules`・`shibuya.world.body.schedule`・`shibuya.world.facts.mock_schedule`・`shibuya.world.facts.rights.initial`・`shibuya.world.facts.weekly_reader`・`shibuya.world.laws.civic`・`shibuya.world.laws.crowd`・`shibuya.world.laws.goods_flow`・`shibuya.world.laws.opening`・`shibuya.world.laws.presence`・`shibuya.world.laws.salient`・`shibuya.world.model.agent_table`・`shibuya.world.model.space.nav1`・`tools/c6/t7_distribution.py`・`tools/vocab/adjudicate.py`
- 読む試験: `tests/agents/test_state.py`・`tests/bench/test_refr20b_tool.py`・`tests/build_lang/test_wiring.py`・`tests/build_pop/test_pop_units.py`・`tests/build_sched/test_w17_prompts.py`・`tests/build_sched/test_weekly_loader.py`・`tests/c6/test_c6lib_scenes.py`・`tests/c6/test_t5_order_bias.py`・`tests/economy/test_accounts.py`・`tests/engine/body/body_fixtures.py`・`tests/engine/bridging/test_bridging_ledger.py`・`tests/engine/calendar2/test_ca2_units.py`・`tests/engine/clock/test_tm3_step_scope.py`・`tests/engine/contact/test_c1_fixes.py`・`tests/engine/contact/test_c1_units.py`・`tests/engine/contact/test_c2_habit.py`・`tests/engine/memory/test_m4_m5_people.py`・`tests/engine/multiday/test_md23_body_events.py`・`tests/engine/processes/test_civic.py`・`tests/engine/processes/test_crowd.py`・`tests/engine/processes/test_goods_flow.py`・`tests/engine/processes/test_opening.py`・`tests/engine/processes/test_rail.py`・`tests/engine/processes/test_rail_board_intent.py`・`tests/engine/processes/test_salient.py`・`tests/engine/proximity/test_switch_sites.py`・`tests/engine/rights/test_rights_events.py`・`tests/engine/rights/test_staff_of_poi_equivalence.py`・`tests/engine/space/test_nav1_units.py`・`tests/engine/speech/test_speech_choice_utterance.py`・`tests/engine/speech/test_speech_on_reaches_addressee.py`・`tests/engine/test_ablation23_switches.py`・`tests/engine/test_arbiter.py`・`tests/engine/test_c9b_targets_attention.py`・`tests/engine/test_change_detect_p6.py`・`tests/engine/test_classical_policy.py`・`tests/engine/test_classical_social.py`・`tests/engine/test_conversation.py`・`tests/engine/test_conversation_invite.py`・`tests/engine/test_defect_fixes_1103.py`・`tests/engine/test_detection_writes_split.py`・`tests/engine/test_energy_balance.py`・`tests/engine/test_familiarity.py`・`tests/engine/test_fleet_wiring.py`・`tests/engine/test_geometry_c9.py`・`tests/engine/test_intent_chooser.py`・`tests/engine/test_intent_hold.py`・`tests/engine/test_meal_bundle_2b.py`・`tests/engine/test_meal_gate_per_hour.py`・`tests/engine/test_memory_recall.py`・`tests/engine/test_memory_record.py`・`tests/engine/test_mock_day_w2.py`・`tests/engine/test_move_destination.py`・`tests/engine/test_norm_meter.py`・`tests/engine/test_parser_contract.py`・`tests/engine/test_plan_sleep_d62.py`・`tests/engine/test_presence_executor.py`・`tests/engine/test_presence_exit_walk.py`・`tests/engine/test_relations.py`・`tests/engine/test_relations_8b.py`・`tests/engine/test_renderer_wiring.py`・`tests/engine/test_resolve.py`・`tests/engine/test_response_delay.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_seat_release_2_4.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_sleep_suppression_d56.py`・`tests/engine/test_stage3_small_fixes.py`・`tests/engine/test_store_choice.py`・`tests/engine/test_store_memory.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/test_two_phase.py`・`tests/engine/test_undefined_action.py`・`tests/engine/test_vocab_v2_eat.py`・`tests/engine/test_wom.py`・`tests/engine/tools/test_c0_contacts_in_relations.py`・`tests/llm/test_contract.py`・`tests/llm/test_vocab_v2.py`・`tests/perception/facts/head_renderer_136fdbb.py`・`tests/perception/facts/scenes.py`・`tests/perception/facts/test_percept_schema.py`・`tests/perception/facts/test_render_from_percept_bytes.py`・`tests/perception/test_ablation1.py`・`tests/perception/test_ablation6_signage.py`・`tests/perception/test_b4b_queue_feed.py`・`tests/perception/test_b6_invite.py`・`tests/perception/test_intent_mode_open.py`・`tests/perception/test_near_tiebreak.py`・`tests/perception/test_nearby_vectorized.py`・`tests/perception/test_p_see_activity.py`・`tests/perception/test_renderer_golden.py`・`tests/perception/test_signage_p_see_gate.py`・`tests/perception/test_templates.py`・`tests/perception/test_vocab_v2_templates.py`
- 決定の ID: 11-03・D-71・D-116・D-120・第 334

## [contact_flags.py](../../../../../../../../src/shibuya/foundation/vocab/contact_flags.py)

engine.tools.contacts — 個人の連絡先の手段ごとの印(第 1 期 1-7 C0・CT5)。

- 公開の関数とクラス
  - `flags_from_kinds`(関数): 辺の種別 → 初めの印(``uint8``・形は ``kind`` と同じ)。``partner`` を渡すと空の辺(-1)は 0。
  - `tally`(関数): manifest の ``tools.contact_flags``: 印を持つ辺の数・手段ごとの辺の数・種別ごとの印を持つ辺の数・バイト。
- 呼び手: `shibuya.interim_bundles.contact.book`・`shibuya.interim_bundles.contact.layer`・`shibuya.mind.relations.layer`・`shibuya.mind.relations.people`
- 読む試験: `tests/engine/contact/test_c1_units.py`・`tests/engine/contact/test_c2_exchange.py`・`tests/engine/tools/test_c0_contacts_in_relations.py`
- 決定の ID: 10-12/§4-4・R-85

## [events.py](../../../../../../../../src/shibuya/foundation/vocab/events.py)

engine.events.vocab — 出来事の記録の語彙表(第 1 期 1-3・CP12・5W1H の ``what``)。**閉じた表**。

- 公開の関数とクラス
  - `code_of`(関数): 表の語 → コード。表の外なら ``ValueError``(閉じた表)。
  - `family_of`(関数): 表の語の族(``"金:賃金"`` → ``"金"``)。
  - `kind_of_what`(関数): 出来事の語のコード → 記憶の種類(記憶の器の中身の写像の検査=``MemoryStore.remember``)。表の外は ``0``。
  - `word`(関数): 族と語 → 表の語(``"過程:rail"``)。表の外なら ``ValueError``。
- import している内部モジュール: `shibuya.foundation.vocab.actions`
- 呼び手: `shibuya.experiments.port.form`・`shibuya.foundation.journal.links`・`shibuya.foundation.journal.log`・`shibuya.foundation.ports.experiment_gate`・`shibuya.interim_bundles.calendar2.layer`・`shibuya.interim_bundles.calendar3.layer`・`shibuya.interim_bundles.calendar_self`・`shibuya.interim_bundles.contact.layer`・`shibuya.interim_bundles.duties.layer`・`shibuya.mind.judge.decision.layer`・`shibuya.mind.memory.body_events`・`shibuya.mind.memory.memory_store`・`shibuya.runtime.systems.state_io`・`shibuya.society.speech.port`・`shibuya.society.tools.record`・`shibuya.society.tools.registry`
- 読む試験: `tests/economy/cp2/test_cp2_event_links.py`・`tests/economy/stage2/test_stage2_account_and_conservation.py`・`tests/engine/contact/test_c2_video.py`・`tests/engine/decision/test_j0_cause_columns.py`・`tests/engine/duties/test_du_runs.py`・`tests/engine/events/test_e_log_schema.py`・`tests/engine/events/test_e_vocab_is_closed.py`・`tests/engine/experiment/test_x33_apply.py`・`tests/engine/multiday/test_md23_body_events.py`・`tests/engine/rights/test_rights_events.py`・`tests/engine/speech/test_speech_port_schema.py`・`tests/engine/tools/test_c0_affordance_from_registry.py`・`tests/engine/tools/test_c0_signboard_mark_invariance.py`・`tests/engine/tools/test_c0_tool_registry.py`
- 読む試験(道筋で): `tests/tools/test_pkgmove.py`
- 決定の ID: 10-12/§1-4・10-12/§1-5・10-12/§4-1・10-12/§4-4・10-12/§4-5・10-13b/§0-3・10-13b/§3

## [place_words.py](../../../../../../../../src/shibuya/foundation/vocab/place_words.py)

foundation.vocab.place_words — 割る段で ``world/assets.py`` を割った割り先(全ファイルの表 §4・名の表は``tools/pkgmove/map.toml`` の割る行)。

- 呼び手: `shibuya.act.target`・`shibuya.mind.memory.wom`・`shibuya.world.model.assets`
- 読む試験: `tests/engine/test_intent_chooser.py`
- 決定の ID: D-114・第 286

## [relations.py](../../../../../../../../src/shibuya/foundation/vocab/relations.py)

foundation.vocab.relations — 割る段で ``engine/relations.py`` を割った割り先(全ファイルの表 §4・名の表は``tools/pkgmove/map.toml`` の割る行)。

- 公開の関数とクラス
  - `InitialEdges`(クラス): 機械的初期化の辺(体の行番号の組・有向)と監査の材料。
  - `RelationEdges`(クラス): 1 体の生きている辺(A ≥ τ_rel・A の降順)。
- 呼び手: `shibuya.mind.memory.memory`・`shibuya.mind.relations.layer`・`shibuya.mind.relations.people`・`shibuya.runtime.run`・`shibuya.runtime.systems.assemble`・`shibuya.world.facts.initial_ties`
- 読む試験: `tests/engine/test_relations.py`・`tests/engine/test_relations_8b.py`・`tests/engine/test_relations_tenure.py`・`tests/engine/tools/test_c0_contacts_in_relations.py`
- 決定の ID: 第 299・第 300
