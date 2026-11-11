# src/shibuya/foundation/vocab

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 4 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/foundation/vocab/__init__.py)

(冒頭の説明なし)

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
- 呼び手: `shibuya.act.activity`・`shibuya.act.intake.parser`・`shibuya.act.intent`・`shibuya.engine.commit`・`shibuya.engine.llm_bridge`・`shibuya.engine.norm_meter`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.engine.speech.layer`・`shibuya.engine.speech_clock`・`shibuya.engine.systems.build`・`shibuya.foundation.vocab.events`・`shibuya.llm.fleet`・`shibuya.llm.mock`・`shibuya.llm.undefined`・`shibuya.mind.judge.classical`・`shibuya.mind.judge.decision.ports`・`shibuya.mind.plan.duties_port`・`shibuya.world.facts.rights.record`・`tools/c6/c6lib.py`・`tools/fig/fig_ab7_actions.py`・`tools/instruments/dm_eval/judge.py`・`tools/instruments/dm_eval/situations.py`・`tools/vocab/adjudicate.py`
- 読む試験: `tests/c6/test_c6lib_aggregate.py`・`tests/c8/test_ablations_ab7.py`・`tests/engine/decision/_j0.py`・`tests/engine/decision/test_j0_mock_equivalence.py`・`tests/engine/decision/test_j0_port_schema.py`・`tests/engine/decision/test_j0_shuffle_invariance.py`・`tests/engine/duties/test_du_runs.py`・`tests/engine/events/test_e_vocab_is_closed.py`・`tests/engine/rights/test_rights_events.py`・`tests/engine/speech/test_speech_choice_utterance.py`・`tests/engine/speech/test_speech_default_off_invariance.py`・`tests/engine/speech/test_speech_on_reaches_addressee.py`・`tests/engine/speech/test_speech_port_schema.py`・`tests/engine/speech/test_wom_from_utterance_roundtrip.py`・`tests/engine/tape_analysis.py`・`tests/engine/test_c9b_targets_attention.py`・`tests/engine/test_classical_policy.py`・`tests/engine/test_conversation.py`・`tests/engine/test_intent_chooser.py`・`tests/engine/test_intent_hold.py`・`tests/engine/test_intent_mode_open.py`・`tests/engine/test_llm_mock.py`・`tests/engine/test_move_destination.py`・`tests/engine/test_parser_contract.py`・`tests/engine/test_presence_exit_walk.py`・`tests/engine/test_stage3_small_fixes.py`・`tests/engine/test_state_format_10f.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/test_undefined_action.py`・`tests/engine/test_vocab_v2_eat.py`・`tests/engine/tools/test_c0_affordance_from_registry.py`・`tests/llm/test_contract.py`・`tests/llm/test_fleet.py`・`tests/llm/test_mock_v3.py`・`tests/llm/test_parser.py`・`tests/llm/test_undefined.py`・`tests/llm/test_vocab_v2.py`・`tests/perception/test_b6_invite.py`・`tests/perception/test_templates.py`・`tests/perception/test_vocab_v2_templates.py`・`tests/test_cli_vocab_version.py`・`tests/tools/test_dm_eval.py`
- 決定の ID: D-71・D-89・D-92・D-116・第 223・第 271・第 274・第 275

## [contact_flags.py](../../../../../../../../src/shibuya/foundation/vocab/contact_flags.py)

engine.tools.contacts — 個人の連絡先の手段ごとの印(第 1 期 1-7 C0・CT5)。

- 公開の関数とクラス
  - `flags_from_kinds`(関数): 辺の種別 → 初めの印(``uint8``・形は ``kind`` と同じ)。``partner`` を渡すと空の辺(-1)は 0。
  - `tally`(関数): manifest の ``tools.contact_flags``: 印を持つ辺の数・手段ごとの辺の数・種別ごとの印を持つ辺の数・バイト。
- 呼び手: `shibuya.engine.contact.book`・`shibuya.engine.contact.layer`・`shibuya.engine.relations`・`shibuya.mind.relations.people`
- 読む試験: `tests/engine/contact/test_c1_units.py`・`tests/engine/contact/test_c2_exchange.py`・`tests/engine/tools/test_c0_contacts_in_relations.py`
- 決定の ID: 10-12/§4-4・R-85

## [events.py](../../../../../../../../src/shibuya/foundation/vocab/events.py)

engine.events.vocab — 出来事の記録の語彙表(第 1 期 1-3・CP12・5W1H の ``what``)。**閉じた表**。

- 公開の関数とクラス
  - `code_of`(関数): 表の語 → コード。表の外なら ``ValueError``(閉じた表)。
  - `family_of`(関数): 表の語の族(``"金:賃金"`` → ``"金"``)。
  - `word`(関数): 族と語 → 表の語(``"過程:rail"``)。表の外なら ``ValueError``。
- import している内部モジュール: `shibuya.foundation.vocab.actions`
- 呼び手: `shibuya.engine.calendar2.layer`・`shibuya.engine.calendar3.layer`・`shibuya.engine.calendar_self`・`shibuya.engine.contact.layer`・`shibuya.engine.duties.layer`・`shibuya.engine.events.body`・`shibuya.engine.experiment.form`・`shibuya.engine.speech.port`・`shibuya.engine.systems.state_io`・`shibuya.engine.tools.record`・`shibuya.foundation.journal.links`・`shibuya.foundation.journal.log`・`shibuya.foundation.ports.experiment_gate`・`shibuya.mind.judge.decision.layer`・`shibuya.mind.memory.memory_store`
- 読む試験: `tests/economy/cp2/test_cp2_event_links.py`・`tests/economy/stage2/test_stage2_account_and_conservation.py`・`tests/engine/contact/test_c2_video.py`・`tests/engine/decision/test_j0_cause_columns.py`・`tests/engine/duties/test_du_runs.py`・`tests/engine/events/test_e_log_schema.py`・`tests/engine/events/test_e_vocab_is_closed.py`・`tests/engine/experiment/test_x33_apply.py`・`tests/engine/multiday/test_md23_body_events.py`・`tests/engine/rights/test_rights_events.py`・`tests/engine/speech/test_speech_port_schema.py`・`tests/engine/tools/test_c0_signboard_mark_invariance.py`・`tests/engine/tools/test_c0_tool_registry.py`
- 決定の ID: 10-12/§1-4・10-12/§1-5・10-12/§4-1・10-12/§4-4・10-12/§4-5・10-13b/§0-3・10-13b/§3
