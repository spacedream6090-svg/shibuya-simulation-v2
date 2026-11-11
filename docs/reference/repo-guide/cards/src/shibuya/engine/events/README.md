# src/shibuya/engine/events

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 5 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/engine/events/__init__.py)

engine.events — 出来事の記録(第 1 期 1-3・CP12・CT9・5W1H)。

## [body.py](../../../../../../../../src/shibuya/engine/events/body.py)

engine.events.body — 体の出来事を出来事の記録(1-3)に書く口(第 2 期 2-3・腕 ``--memory-store events`` のランだけ)。

- 公開の関数とクラス
  - `BodyEventLink`(クラス): 体の出来事の口(記憶の器が持つ=``MemoryStore.body_events``・組み立てが腕のランだけ作る)。
  - `kind_of_what`(関数): 出来事の語のコード → 記憶の種類(記憶の器の中身の写像の検査=``MemoryStore.remember``)。表の外は ``0``。
- import している内部モジュール: `shibuya.engine.events.log`・`shibuya.engine.events.vocab`・`shibuya.engine.tools.record`
- 呼び手: `shibuya.engine.memory_store`・`shibuya.engine.systems.build`
- 読む試験: `tests/engine/multiday/test_md23_body_events.py`
- 読む試験(道筋で): `tests/test_places_guard.py`

## [links.py](../../../../../../../../src/shibuya/engine/events/links.py)

engine.events.links — 既存の記録の行に出来事の id の目印を付ける口(第 1 期 1-3・口の約束 1-3 の約束 (2))。

- 公開の関数とクラス
  - `ActualLogLink`(クラス): ActualLog の ``event_sink``(過程の id → 出来事を ``n`` 行書いて id の 2 列を返す)。
  - `MoneyEventLink`(クラス): 〔第 1 期 1-9〕金の生ログ(``economy.ledger``)の口: 原因を渡した transfer の行ごとに出来事を 1 行書き、id の 2 列を返す。
- import している内部モジュール: `shibuya.engine.events.log`・`shibuya.engine.events.vocab`
- 呼び手: `shibuya.engine.processes.runner`・`shibuya.engine.systems.build`
- 読む試験: `tests/economy/cp2/test_cp2_event_links.py`・`tests/economy/cp2/test_cp2_nine_ops_equivalence.py`・`tests/economy/stage2/test_stage2_calls.py`・`tests/economy/stage2/test_stage2_money_rules.py`・`tests/engine/events/test_e_log_links_actual.py`・`tests/engine/rights/test_rights_events.py`

## [log.py](../../../../../../../../src/shibuya/engine/events/log.py)

engine.events.log — 出来事の記録(第 1 期 1-3・CP12・CT9・5W1H)。

- 公開の関数とクラス
  - `Event`(クラス): 出来事 1 行(5W1H+誰に+どれだけ+原因)。書き手は ``id`` を付けない(``EventLog.append`` が付ける)。
  - `EventLog`(クラス): 出来事の記録(書く口は ``append`` の 1 つ)。
  - `Experiment`(クラス): 原因=実験の条件(``cond_id``)。**作れるのは ``engine/experiment/gate.py`` の ``admit`` だけ**(CP12)。
  - `LlmCall`(クラス): 原因=LLM の呼び出し(``call_id``=テープの ``call_id`` 列と同じ値・``input_event_ids``=入力に入っていた出来事の id)。
  - `Process`(クラス): 原因=過程(世界過程の名か区切りの名=``vocab.PROCESS_NAMES``・〔1-5〕検査の名=``vocab.CHECK_PROCESSES``)。
  - `enabled`(関数): 出来事を記録するか(切替口 ``SHIBUYA_EVENTS``・``set_enabled``)。
  - `set_enabled`(関数): 記録を入れる/外す(腕・試験の切替口)。組み立ての時に読む(ランの途中で変えても、そのランの記録は変わらない)。
- import している内部モジュール: `shibuya.core.growth`・`shibuya.core.time_consts`・`shibuya.core.types`・`shibuya.engine.events.vocab`・`shibuya.engine.experiment.gate`・`shibuya.engine.systems.guard`
- 呼び手: `shibuya.cli`・`shibuya.engine.calendar2.layer`・`shibuya.engine.calendar3.layer`・`shibuya.engine.calendar_self`・`shibuya.engine.contact.layer`・`shibuya.engine.decision.layer`・`shibuya.engine.duties.layer`・`shibuya.engine.economy_stage2`・`shibuya.engine.events.body`・`shibuya.engine.events.links`・`shibuya.engine.experiment.gate`・`shibuya.engine.memory_impression`・`shibuya.engine.memory_store`・`shibuya.engine.processes.goods_flow`・`shibuya.engine.processes.rail`・`shibuya.engine.rights.record`・`shibuya.engine.speech.port`・`shibuya.engine.systems.build`・`shibuya.engine.systems.state_io`・`shibuya.engine.tools.record`
- 読む試験: `tests/economy/cp2/test_cp2_event_links.py`・`tests/economy/cp2/test_cp2_nine_ops_equivalence.py`・`tests/economy/stage2/test_stage2_calls.py`・`tests/economy/stage2/test_stage2_money_rules.py`・`tests/economy/test_rules42_ledger.py`・`tests/economy/test_rules42b_ledger.py`・`tests/economy/test_wage_occupation.py`・`tests/engine/calendar2/_ca2.py`・`tests/engine/calendar2/test_ca2_runs.py`・`tests/engine/calendar2/test_ca2_units.py`・`tests/engine/calendar3/test_ca3_runs.py`・`tests/engine/calendar3/test_ca3_units.py`・`tests/engine/contact/_c1.py`・`tests/engine/contact/_c2.py`・`tests/engine/contact/test_c1_event_log_onoff.py`・`tests/engine/contact/test_c1_fixes.py`・`tests/engine/contact/test_c1_flow.py`・`tests/engine/contact/test_c1_units.py`・`tests/engine/contact/test_c2_runs.py`・`tests/engine/decision/test_j0_cause_columns.py`・`tests/engine/duties/test_du_runs.py`・`tests/engine/events/test_e_cause_three_kinds.py`・`tests/engine/events/test_e_log_invariance.py`・`tests/engine/events/test_e_log_links_actual.py`・`tests/engine/events/test_e_log_schema.py`・`tests/engine/events/test_e_manifest_events.py`・`tests/engine/events/test_e_vocab_is_closed.py`・`tests/engine/experiment/_x33.py`・`tests/engine/experiment/test_x33_apply.py`・`tests/engine/memory/test_m3_impression_and_trace.py`・`tests/engine/multiday/test_md23_body_events.py`・`tests/engine/rights/test_rights_events.py`・`tests/engine/speech/test_s8_event_log_onoff.py`・`tests/engine/speech/test_speech_empty_text_errors.py`・`tests/engine/speech/test_speech_modality_field_empty.py`・`tests/engine/speech/test_speech_on_reaches_addressee.py`・`tests/engine/speech/test_speech_port_schema.py`・`tests/engine/speech/test_wom_from_utterance_roundtrip.py`・`tests/engine/state/test_class_ids.py`・`tests/engine/tools/test_c0_signboard_mark_invariance.py`・`tests/perception/facts/test_percept_schema.py`
- 状態台帳の行
  - 持ち主 `events`(`EventLog`)
    - `E` EventLog(出来事の記録・第 1 期 1-3)(挙動 diag・復元 discardable) 道筋 `events._ci_n`・`events._ci_seq`・`events._ci_t`・`events._cz_call_agent`・`events._cz_call_cls`・`events._cz_call_t`・`events._cz_exp_rows`・`events._cz_experiments`・`events._cz_in_len`・`events._cz_in_start`・`events._cz_kind`・`events._cz_last_llm`・`events._cz_n`・`events._cz_num`・`events._cz_proc_rows`・`events._cz_ref`・`events._cz_src`・`events._cz_texts`・`events._ev_cause`・`events._ev_day_mark`・`events._ev_how_much`・`events._ev_n`・`events._ev_n_appended`・`events._ev_n_evicted`・`events._ev_name_codes`・`events._ev_names`・`events._ev_now_ns`・`events._ev_origin`・`events._ev_read_ns`・`events._ev_received_ns`・`events._ev_seq`・`events._ev_seq_next`・`events._ev_t_ns`・`events._ev_via`・`events._ev_what`・`events._ev_where_id`・`events._ev_where_kind`・`events._ev_who`・`events._ev_whom` 書ける系: calendar_2・calendar_3・checkpoint・close_final・contact・conversation・day_close・decide・duties・experiment・llm_receive・memory・phase_c・presence・world
- 環境変数: `SHIBUYA_EVENTS`
- 決定の ID: R-113

## [vocab.py](../../../../../../../../src/shibuya/engine/events/vocab.py)

engine.events.vocab — 出来事の記録の語彙表(第 1 期 1-3・CP12・5W1H の ``what``)。**閉じた表**。

- 公開の関数とクラス
  - `code_of`(関数): 表の語 → コード。表の外なら ``ValueError``(閉じた表)。
  - `family_of`(関数): 表の語の族(``"金:賃金"`` → ``"金"``)。
  - `word`(関数): 族と語 → 表の語(``"過程:rail"``)。表の外なら ``ValueError``。
- import している内部モジュール: `shibuya.llm.contract`
- 呼び手: `shibuya.engine.calendar2.layer`・`shibuya.engine.calendar3.layer`・`shibuya.engine.calendar_self`・`shibuya.engine.contact.layer`・`shibuya.engine.decision.layer`・`shibuya.engine.duties.layer`・`shibuya.engine.events.body`・`shibuya.engine.events.links`・`shibuya.engine.events.log`・`shibuya.engine.experiment.form`・`shibuya.engine.experiment.gate`・`shibuya.engine.memory_store`・`shibuya.engine.speech.port`・`shibuya.engine.systems.state_io`・`shibuya.engine.tools.record`
- 読む試験: `tests/economy/cp2/test_cp2_event_links.py`・`tests/economy/stage2/test_stage2_account_and_conservation.py`・`tests/engine/contact/test_c2_video.py`・`tests/engine/decision/test_j0_cause_columns.py`・`tests/engine/duties/test_du_runs.py`・`tests/engine/events/test_e_log_schema.py`・`tests/engine/events/test_e_vocab_is_closed.py`・`tests/engine/experiment/test_x33_apply.py`・`tests/engine/multiday/test_md23_body_events.py`・`tests/engine/rights/test_rights_events.py`・`tests/engine/speech/test_speech_port_schema.py`・`tests/engine/tools/test_c0_signboard_mark_invariance.py`・`tests/engine/tools/test_c0_tool_registry.py`
- 決定の ID: 10-12/§1-4・10-12/§1-5・10-12/§4-1・10-12/§4-4・10-12/§4-5・10-13b/§0-3・10-13b/§3
