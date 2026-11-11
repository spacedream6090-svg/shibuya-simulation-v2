# tests/engine/tools

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 9 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../tests/engine/tools/__init__.py)

(冒頭の説明なし)

## [contacts_writers.py](../../../../../../../tests/engine/tools/contacts_writers.py)

第 1 期 1-7 CT5: 連絡先の印の欄を書く所を AST で集める道具(試験の補助・src は読むだけ)。

- 公開の関数とクラス
  - `is_col`(関数)
  - `scan_source`(関数)
  - `scan_tree`(関数): src の全部: (関係の置き場の書きの全部, 許す所の外の書き)。
  - `violations`(関数): ``rel``(``src/shibuya`` からの道筋)の中の、許す所の外の書き。
- import している内部モジュール: `tests/engine/ast_writers.py`
- 読む試験: `tests/engine/tools/test_c0_contacts_in_relations.py`

## [test_c0_affordance_from_registry.py](../../../../../../../tests/engine/tools/test_c0_affordance_from_registry.py)

第 1 期 1-7 の 1-8 への結線: 候補の源「周りが示すできること」を道具の台帳から読む。

- 公開の関数とクラス
  - `test_build_passes_the_fixture_registry_and_the_run_is_unchanged`(関数): 組み立ては ``Fixtures.tools`` と同じ台帳を層に渡す。表が空なので、台帳を渡さない層(結線の前)と候補の番号列・
  - `test_empty_table_gives_the_same_words_and_candidates_as_before`(関数): 表が空なら、道具の台帳を渡した層と渡さない層(結線の前=HEAD の形)で語も候補の列も同じ。
  - `test_one_word_in_the_table_adds_a_candidate`(関数): 負の対照: 表に 1 語を仮に入れると、その語が「周りが示すできること」の候補になる(源 vocab → affordance)。
  - `test_registered_only_tools_are_not_offered`(関数): 登録だけの段(``stage`` が 6-4)の道具は、表に語があっても出ない(電話・乗換案内・地図ほか)。
  - `test_the_table_is_empty_and_frozen`(関数)
  - `test_unknown_agents_get_nothing`(関数)
  - `test_unmet_requirements_hide_the_tool`(関数)
- import している内部モジュール: `shibuya.engine.decision.layer`・`shibuya.engine.decision.sources`・`shibuya.engine.llm_bridge`・`shibuya.engine.run`・`shibuya.engine.tools.record`・`shibuya.engine.tools.registry`・`shibuya.foundation.vocab.actions`・`tests/engine/decision/_j0.py`

## [test_c0_contacts_in_relations.py](../../../../../../../tests/engine/tools/test_c0_contacts_in_relations.py)

第 1 期 1-7 道具の台帳 C0(CT5): 個人の連絡先は関係の記憶に手段ごとの印(家族と職場は初めから)。

- 公開の関数とクラス
  - `test_copies_of_the_relation_kinds`(関数)
  - `test_evicted_family_edge_loses_its_flag`(関数)
  - `test_flags_are_not_read_by_the_run`(関数): 印を書く口を止めても、印を乱しても final と呼数と rel_* が同じ(合成の世界・記憶+関係+同席+店)。
  - `test_flags_from_kinds`(関数)
  - `test_initial_edges_get_flags_for_family_and_work_only`(関数)
  - `test_memory_declares_the_contact_writes_in_stage_b`(関数)
  - `test_negative_controls_are_found`(関数): 23 形(中身の書き 17・差し替え 4・名の分からない差し替え 1・書く口の呼び出し 1)と、写しへの書き(数えない)。
  - `test_new_partner_has_no_flag_and_the_same_partner_keeps_it`(関数)
  - `test_only_the_writer_writes_the_flags`(関数)
  - `test_rebuild_contacts_equals_the_map_of_kinds`(関数)
  - `test_resume_rebuilds_the_same_flags`(関数)
  - `test_runtime_guard_stops_writes_outside_the_writer`(関数): 検収 L1: 公開の欄は読み取り専用の view・付け替えと消去は止まる・書く口だけが書ける(負の対照)。
  - `test_state_ledger_row_and_declaration`(関数)
  - `test_world_run_family_and_work_flags_and_rel_columns_unchanged`(関数)
  - `test_writing_contacts_does_not_change_the_existing_rel_columns`(関数): 初めの辺・新しい相手・押し出しの全部で、印を書く口を止めた層と ``rel_*`` が値まで同じ。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.cli`・`shibuya.engine.memory`・`shibuya.engine.relations`・`shibuya.engine.run`・`shibuya.engine.state_ledger`・`shibuya.engine.systems.conductor`・`shibuya.engine.systems.overrides`・`shibuya.engine.systems.probe`・`shibuya.engine.systems.table`・`shibuya.foundation.vocab.contact_flags`・`shibuya.foundation.write_permit`・`tests/engine/tools/contacts_writers.py`

## [test_c0_groups_from_w16.py](../../../../../../../tests/engine/tools/test_c0_groups_from_w16.py)

第 1 期 1-7 道具の台帳 C0(CT10・CT5): グループの一覧=家族(W16 の世帯)+職場(W16 の事業所=W6 の組織)。

- 公開の関数とクラス
  - `full`(関数)
  - `test_csr_rows_and_members_on_a_small_population`(関数)
  - `test_empty_and_one_sided`(関数)
  - `test_group_list_is_read_only`(関数)
  - `test_rows_equal_households_plus_establishments_on_the_full_population`(関数)
  - `test_rows_on_the_5000_sample`(関数)
- import している内部モジュール: `shibuya.engine.tools.groups`・`shibuya.world.facts.population_reader`

## [test_c0_init_recall.py](../../../../../../../tests/engine/tools/test_c0_init_recall.py)

第 1 期 1-7 道具の台帳 C0(検収 L2): 作った後の物に ``__init__`` を呼び直して中身を入れ替えられない。

- 公開の関数とクラス
  - `test_init_cannot_be_called_again`(関数)
- import している内部モジュール: `shibuya.engine.tools.groups`・`shibuya.engine.tools.places`・`shibuya.engine.tools.registry`

## [test_c0_phone_table_empty_and_declared.py](../../../../../../../tests/engine/tools/test_c0_phone_table_empty_and_declared.py)

第 1 期 1-7 道具の台帳 C0(CT5): 店の番号の場所の表は空の表で用意し、空欄をつなぎの台帳に宣言する。

- 公開の関数とクラス
  - `test_manifest_reports_the_empty_table`(関数)
  - `test_osm_phone_rule`(関数)
  - `test_the_blank_is_declared_in_the_bridging_ledger`(関数)
  - `test_the_recorded_count_is_reproduced_with_the_same_rule`(関数)
  - `test_the_table_is_empty_and_answers_none`(関数)
  - `test_the_table_is_read_only_after_construction`(関数)
- import している内部モジュール: `shibuya.engine.run`・`shibuya.engine.tools.places`・`shibuya.engine.tools.registry`・`shibuya.foundation.decl.bridging`・`shibuya.foundation.decl.ledger_paths`・`tests/_places.py`
- 決定の ID: 10-13b/§3・11-01・11-02r/§1・11-02r/§1 #7・11-03/§3・第 334

## [test_c0_signboard_mark_invariance.py](../../../../../../../tests/engine/tools/test_c0_signboard_mark_invariance.py)

第 1 期 1-7 道具の台帳 C0(CT0・CT9): 看板の文の「作り物」の印は記録にだけ(描画のバイトは変えない)。

- 公開の関数とクラス
  - `test_arm_reads_the_environment_value`(関数)
  - `test_default_run_writes_nothing_and_has_no_link`(関数)
  - `test_link_writes_one_marked_row_per_visible_signboard`(関数)
  - `test_no_link_when_the_event_log_is_off`(関数)
  - `test_synthetic_run_arm_on_and_off_render_the_same_bytes`(関数)
  - `test_the_mark_is_tied_to_the_ledger_and_the_vocab`(関数)
  - `test_undeclared_write_from_decide_fails_at_run_time`(関数)
  - `test_world_run_arm_on_and_off_render_the_same_bytes`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.run`・`shibuya.engine.systems.overrides`・`shibuya.engine.tools.record`・`shibuya.engine.tools.registry`・`shibuya.foundation.decl.bridging`・`shibuya.foundation.journal.log`・`shibuya.foundation.ports.percept`・`shibuya.foundation.vocab.events`・`shibuya.foundation.write_permit`・`shibuya.perception.renderer`
- 環境変数: `SHIBUYA_TOOL_EVENTS`

## [test_c0_tool_registry.py](../../../../../../../tests/engine/tools/test_c0_tool_registry.py)

第 1 期 1-7 道具の台帳 C0(CT0): 欄・凍結・書き換え不可・最初の中身・つなぎの台帳との結び・書く口は register だけ。

- 公開の関数とクラス
  - `test_affects_becomes_read_only`(関数)
  - `test_bridges_of_the_tools_are_active_rows_of_the_ledger`(関数)
  - `test_default_registry_contents`(関数)
  - `test_fields_are_the_contract_six_then_the_extra_four`(関数)
  - `test_invalid_rows_are_rejected`(関数)
  - `test_known_by_kinds`(関数)
  - `test_known_reads_the_row`(関数)
  - `test_negative_control_second_writer_is_found`(関数)
  - `test_no_one_outside_touches_the_registry_slot`(関数)
  - `test_only_init_and_register_rebind_the_rows`(関数)
  - `test_register_adds_only`(関数)
  - `test_registry_cannot_be_rewritten`(関数)
  - `test_tool_is_frozen_with_slots`(関数)
  - `test_tool_words_are_names_of_the_registry_and_appended_at_the_end`(関数)
- import している内部モジュール: `shibuya.engine.tools.registry`・`shibuya.foundation.decl.bridging`・`shibuya.foundation.vocab.events`
- 決定の ID: 10-12/§4-4・10-13b/§1
