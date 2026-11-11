# tests/engine/memory

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 17 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../tests/engine/memory/__init__.py)

(冒頭の説明なし)

## [_m0.py](../../../../../../../tests/engine/memory/_m0.py)

第 1 期 1-6 M0 の試験の共通(腕の切替・合成の世界の小さなランの設定・記憶の表と器の行の突き合わせ)。

- 公開の関数とクラス
  - `arm`(関数): 腕を一時的に選ぶ(組み立てが読む)。
  - `run_with_arm`(関数)
  - `table_vs_store`(関数): 記憶の表(``mem_*``・要旨)と器の行の食い違い(空なら同じ)。M0 の器は表の写し=全部の体・全部の行で同じはず。
- import している内部モジュール: `shibuya.mind.memory.memory_store`
- 読む試験: `tests/engine/memory/test_m0_recall_equivalence.py`・`tests/engine/memory/test_m0_render_bytes.py`・`tests/engine/memory/test_m0_shown_recorded.py`・`tests/engine/memory/test_m0_store_schema.py`・`tests/engine/memory/test_m0_writes_declared.py`

## [_mr65.py](../../../../../../../tests/engine/memory/_mr65.py)

第 6 期 6-5 記憶 MR の試験の共通(腕の切替・合成の世界の小さなラン)。

- 公開の関数とクラス
  - `arms`(関数): 器の腕と 6-5 の腕を一時的に選ぶ(組み立てが読む)。``kw`` は ``model``・``cue``・``people``・``embed_model``・``grain``。
  - `mr65`(関数): ランの manifest の ``memory_summary.memory_store.mr65``(腕の計器)。
- import している内部モジュール: `shibuya.mind.memory.memory_m1`・`shibuya.mind.memory.memory_store`
- 読む試験: `tests/engine/memory/test_m1_runs.py`・`tests/engine/memory/test_m2_cue.py`・`tests/engine/memory/test_m4_m5_people.py`・`tests/engine/memory/test_mr65_grain_and_cli.py`・`tests/engine/memory/test_mr65_guards.py`・`tests/engine/memory/test_mr65_review_fixes.py`

## [test_m0_cli.py](../../../../../../../tests/engine/memory/test_m0_cli.py)

第 1 期 1-6 記憶の器 M0: CLI ``--memory-store`` は指定したとき環境変数 ``SHIBUYA_MEMORY_STORE`` より強い(検収 L9)。

- 公開の関数とクラス
  - `test_cli_memory_store_beats_the_environment`(関数)
- import している内部モジュール: `shibuya.runtime.inference.tape`
- 環境変数: `os.environ` をまるごと使う

## [test_m0_recall_equivalence.py](../../../../../../../tests/engine/memory/test_m0_recall_equivalence.py)

第 1 期 1-6 記憶の器 M0: 腕 on で、今の記憶の表の想起と器の想起が同じ候補を返す(口の約束 1-6 の約束 (2))。

- 公開の関数とクラス
  - `Probe`(クラス)
  - `probe`(関数): ``MemoryLayer.recall`` を包み、抜き取った刻みで今の表の道と器の道を両方引いて比べる(返すのは器の道)。
  - `test_manifest_differs_only_by_the_store_instrument`(関数): 腕 on/off の manifest: 既存の葉は全部同じ。足したのは ``memory_summary.memory_store`` の下の葉だけ。
  - `test_synthetic_every_recall_is_the_same`(関数): ``memory_n`` を小さくした 2 本は追い出しが何百回も起きる(検収 L10: 追い出しの同値をランで確かめる)。
  - `test_synthetic_two_days_resume_rebuilds_the_store`(関数): 腕 on の 2 日のラン: 日中(12:30)で止めて再開=器は戻した表から作り直す。再開の後は通しのランと同じ。
  - `test_world_5000_sampled_recalls_are_the_same`(関数): 世界資産 5,000 体・mock・1 日(byte-check の記憶の構成)で、刻みの 1/7 の全部の想起を突き合わせる。
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.run`・`shibuya.mind.memory.memory`・`shibuya.runtime.inference.tape`・`tests/engine/memory/_m0.py`

## [test_m0_render_bytes.py](../../../../../../../tests/engine/memory/test_m0_render_bytes.py)

第 1 期 1-6 記憶の器 M0: 描き方の口 ``render_memories`` が今の描き方とバイトで同じ(``test_m0_render_bytes``)。

- 公開の関数とクラス
  - `test_b5_text_is_the_same_with_and_without_the_store`(関数)
  - `test_render_memories_edges`(関数)
  - `test_render_memories_equals_the_b5_memory_line`(関数)
- import している内部モジュール: `shibuya.engine.llm_bridge`・`shibuya.engine.run`・`shibuya.foundation.time_consts`・`shibuya.mind.memory.memory_store`・`tests/engine/memory/_m0.py`

## [test_m0_shown_recorded.py](../../../../../../../tests/engine/memory/test_m0_shown_recorded.py)

第 1 期 1-6 記憶の器 M0: 録画(MR16)=見せた記憶の行の記録(口の約束 1-6 の約束 (3)・``test_m0_shown_recorded``)。

- 公開の関数とクラス
  - `runs`(関数)
  - `test_arm_on_adds_one_column_inside_version_4`(関数)
  - `test_event_ids_follow_the_recalled_rows`(関数)
  - `test_last_shown_time_matches_the_tape`(関数): 器の「最後に見せた時刻」=テープでその行(同じ目印)を見せた最後の呼び出しの時刻。
  - `test_tape_writer_arm_columns_are_a_closed_table`(関数)
- import している内部モジュール: `shibuya.engine.run`・`shibuya.foundation.time_consts`・`shibuya.mind.memory.memory`・`shibuya.runtime.inference.tape`・`tests/engine/memory/_m0.py`

## [test_m0_store_schema.py](../../../../../../../tests/engine/memory/test_m0_store_schema.py)

第 1 期 1-6 記憶の器 M0: 器の形(口の約束 1-6 の口・受入の試験 ``test_m0_store_schema``)。

- 公開の関数とクラス
  - `guard_on`(関数)
  - `test_annotations_follow_the_gist_rules`(関数): 注釈=今の要旨と同じ規則(体あたり 16 件・古い順に落とす・追い出した行の注釈は落とす・同じ行に置き直すと最後へ)。
  - `test_arm_switch`(関数)
  - `test_closed_tables_cannot_be_changed`(関数): 検収 L2: 閉じた表(器の列の表・テープの腕の列の表)は書き換えられない。
  - `test_delattr_is_closed`(関数): 検収 L1: 欄を消してから付け替える抜け道を閉じる(負の対照)。
  - `test_ledger_rows_are_out_of_both_hashes_and_the_state_file`(関数)
  - `test_mark_shown_records_the_time_and_returns_the_pointer_text`(関数)
  - `test_rebuild_from_the_table_gives_the_same_rows`(関数)
  - `test_rebuild_only_outside_systems`(関数): 検収 L3: 作り直しは再開の組み立て(系の外)だけ。系の中(M0* を宣言した系でも)では落ちる。
  - `test_remember_evicts_the_lowest_score_row_like_the_table`(関数): 満杯=score 最小の行(同点は番号の小さい方)を追い出す。今の ``MemoryLayer._write`` と行が同じ。
  - `test_remember_new_merge_and_pointer_to_the_last_occurrence`(関数)
  - `test_remember_rejects_what_m0_cannot_hold`(関数)
  - `test_row_columns_bytes_and_ranges`(関数)
  - `test_runtime_owner_coverage_with_the_store`(関数)
  - `test_setattr_guard_and_slots`(関数)
  - `test_store_imports_only_allowed_layers`(関数): 器は engine の層の契約(engine > perception|llm > world|agents > core)を守る(import-linter と同じ向き)。
  - `test_store_is_one_module_beside_the_memory_table`(関数)
  - `test_strength_is_capped_like_the_fixed_table`(関数)
  - `test_systems_declare_the_store_paths`(関数)
  - `test_value_drift_from_the_table_is_caught_at_write`(関数): 検収 M1: 行の番号が同じでも、器の値(ここでは重要度)が表とずれたら書いた所で落ちる(負の対照)。
  - `test_view_has_words_and_content_but_no_strength_number`(関数)
  - `test_writes_outside_the_declaration_fail`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.build`・`shibuya.economy.ledger`・`shibuya.engine.resolve`・`shibuya.foundation.time_consts`・`shibuya.foundation.write_guard`・`shibuya.foundation.write_permit`・`shibuya.llm`・`shibuya.mind.memory.memory`・`shibuya.mind.memory.memory_store`・`shibuya.perception.renderer`・`shibuya.runtime.inference.tape`・`shibuya.runtime.state.ledger`・`shibuya.runtime.state.ledger_ast`・`shibuya.runtime.systems.table`・`shibuya.world.model.state`・`tests/_places.py`・`tests/engine/memory/_m0.py`

## [test_m0_writes_declared.py](../../../../../../../tests/engine/memory/test_m0_writes_declared.py)

第 1 期 1-6 記憶の器 M0: 器を書く系の宣言(口の約束の共通の約束「SYSTEMS の宣言に書き手を足す=段 B で宣言の外 0」)。

- 公開の関数とクラス
  - `test_declared_writes_cover_the_store_changes`(関数)
  - `test_dropping_the_store_path_fails_where_it_is_written`(関数)
- import している内部モジュール: `shibuya.engine.run`・`shibuya.foundation.write_permit`・`shibuya.runtime.systems.conductor`・`shibuya.runtime.systems.probe`・`shibuya.runtime.systems.table`・`shibuya.validation.static.system_overrides`・`tests/engine/memory/_m0.py`

## [test_m1_runs.py](../../../../../../../tests/engine/memory/test_m1_runs.py)

第 6 期 6-5 記憶 M1 の腕(``--memory-model m1``)のラン・器・守りの試験(合成の世界・data 無し)。

- 公開の関数とクラス
  - `test_arms_without_the_store_are_refused`(関数)
  - `test_default_arms_create_nothing_and_add_no_manifest_leaves`(関数)
  - `test_enable_arms_once_and_outside_the_systems`(関数)
  - `test_m1_needs_the_population_seed_at_assembly`(関数): 〔検収 M1〕器に腕 m1 を置くときに母集団の seed が無ければ止める(既定の 0 で黙って引かない)。
  - `test_m1_rate_seed_is_the_population_seed`(関数): 〔検収 M1〕腕 m1 の人ごとの忘れる速さ(用途名 memory.forgetting_rate=母集団の側)は、そのランの母集団の seed から引く
  - `test_m1_recall_differs_from_m0_top_k`(関数)
  - `test_m1_two_days_resume_is_the_straight_run`(関数)
  - `test_memory_off_with_memory_arms_is_refused`(関数): 〔検収 L6〕記憶 off のランで 6-5 の腕を立てたら止める(check_arms と同じ形・ランの種類が「腕」になる抜け道を塞ぐ)。
  - `test_render_words_port_marks_vague_items`(関数)
  - `test_store_unit_touch_times_strength_and_words`(関数)
  - `test_write_needs_the_declared_m0m_path`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.run`・`shibuya.foundation.time_consts`・`shibuya.foundation.write_guard`・`shibuya.mind.memory.memory`・`shibuya.mind.memory.memory_m1`・`shibuya.mind.memory.memory_store`・`shibuya.runtime.inference.tape`・`tests/engine/memory/_mr65.py`・`tests/engine/test_salt_seed_split_10f.py`

## [test_m1_strength.py](../../../../../../../tests/engine/memory/test_m1_strength.py)

第 6 期 6-5 記憶 M1: 強さの式(ACT-R の折衷形・秒の時刻・+1 なし・d=0.5)と人ごとのばらつき 15%(Sense 2018)の単体。

- 公開の関数とクラス
  - `test_arm_switches_and_checks`(関数)
  - `test_forgetting_scale_is_deterministic_and_about_15_percent`(関数)
  - `test_hybrid_equals_exact_when_n_le_k_and_is_close_for_even_spacing`(関数)
  - `test_known_values_without_plus_one`(関数)
  - `test_m1_state_guards`(関数)
  - `test_minimum_encoding_time_avoids_infinity`(関数)
  - `test_recall_recognize_forget_and_words`(関数)
  - `test_tau_from_m0_matches_the_m0_crossing_time`(関数)
  - `test_touch_times_shifts_newest_first`(関数)
  - `test_units_shift_all_strengths_by_the_same_amount`(関数): MR1: 単位を c 倍にすると全部の強さが −d·ln c だけ同じにずれる(+1 の無い式)=τ に吸収される。
- import している内部モジュール: `shibuya.foundation.time_consts`・`shibuya.mind.memory.memory`・`shibuya.mind.memory.memory_m1`

## [test_m2_cue.py](../../../../../../../tests/engine/memory/test_m2_cue.py)

第 6 期 6-5 記憶 M2: 手がかり(既定=その場の手がかり=ID の一致・腕 ``--memory-cue embed``=意味の手がかり)。

- 公開の関数とクラス
  - `test_close_gist_ranks_first_with_the_semantic_cue`(関数)
  - `test_cue_text_choice_in_and_out_of_conversation`(関数)
  - `test_default_cue_computes_no_embedding`(関数)
  - `test_dropping_a_note_drops_its_vector`(関数)
  - `test_embed_arm_run_is_deterministic`(関数)
  - `test_ngram_embedder_is_deterministic_and_normalized`(関数)
  - `test_ruri_close_sentence_ranks_first`(関数)
  - `test_ruri_pins_and_missing_weights`(関数)
- import している内部モジュール: `shibuya.engine.run`・`shibuya.foundation.time_consts`・`shibuya.mind.memory.memory_embed`・`shibuya.mind.memory.memory_store`・`shibuya.runtime.inference.tape`・`tests/engine/memory/_mr65.py`

## [test_m3_impression_and_trace.py](../../../../../../../tests/engine/memory/test_m3_impression_and_trace.py)

第 6 期 6-5 記憶 M3 の器(印象の履歴と寝たときの書き直し)と、注意を向けずに見ていた人の浅い痕跡の口(mock で試験)。

- 公開の関数とクラス
  - `test_hidden_referent_field_is_empty_and_versioned`(関数)
  - `test_impressions_are_appended_and_rewritten_on_sleep`(関数)
  - `test_impressions_need_an_llm_call_cause`(関数)
  - `test_played_along_share_gauge`(関数)
  - `test_shallow_trace_from_the_shared_log`(関数)
- import している内部モジュール: `shibuya.foundation.journal.log`・`shibuya.foundation.ports.percept`・`shibuya.foundation.time_consts`・`shibuya.mind.memory.memory_impression`・`shibuya.mind.memory.memory_trace`

## [test_m4_m5_people.py](../../../../../../../tests/engine/memory/test_m4_m5_people.py)

第 6 期 6-5 思い浮かぶ/見覚え(MR4)と人も記憶の一つ(器=腕 ``--memory-people memory``)。

- 公開の関数とクラス
  - `test_cap_eviction_ties_go_to_the_lower_row`(関数)
  - `test_full_agent_doubles_the_width_when_nothing_is_forgotten`(関数)
  - `test_people_arm_refuses_to_resume`(関数)
  - `test_people_arm_run_keeps_shops_in_the_store_table`(関数)
  - `test_people_arm_run_never_writes_the_relation_table`(関数)
  - `test_people_layer_does_not_touch_the_relation_table`(関数)
  - `test_person_rows_key_importance_and_kind_kept`(関数)
  - `test_recall_and_recognition_and_forgetting`(関数)
  - `test_row_caps_bound_the_width_and_evict_the_lowest_a_row`(関数)
  - `test_rows0_over_the_width_cap_is_refused`(関数)
  - `test_seed_people_from_the_initial_edges`(関数)
  - `test_seed_people_over_the_person_cap_is_refused`(関数)
  - `test_shop_table_grows_to_the_cap_then_overwrites_the_lowest_a`(関数)
  - `test_shop_table_ties_and_bounds`(関数)
  - `test_world_5000_one_day_uncapped_grows_and_reads_people`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.cli`・`shibuya.engine.relations`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.foundation.time_consts`・`shibuya.mind.memory.memory`・`shibuya.mind.memory.memory_m1`・`shibuya.mind.memory.memory_shops`・`shibuya.mind.memory.memory_store`・`shibuya.mind.relations.people`・`tests/engine/memory/_mr65.py`

## [test_mr65_grain_and_cli.py](../../../../../../../tests/engine/memory/test_mr65_grain_and_cli.py)

第 6 期 6-5: 体の出来事の粒度の腕(``--memory-grain day``=2-3 の 14.6 行/体/日を減らす案)と CLI の腕。

- 公開の関数とクラス
  - `test_cli_memory_arms_beat_the_environment`(関数)
  - `test_cli_run_kind_counts_the_memory_arms`(関数)
  - `test_grain_day_refuses_to_resume`(関数)
  - `test_grain_day_writes_fewer_rows_and_keeps_the_recall`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.run`・`shibuya.experiments.port.run_kind`・`shibuya.foundation.time_consts`・`shibuya.runtime.inference.tape`・`tests/engine/memory/_mr65.py`・`tests/engine/multiday/_md.py`
- 環境変数: `SHIBUYA_MEMORY_GRAIN`・`SHIBUYA_MEMORY_MODEL`・`SHIBUYA_MEMORY_PEOPLE`・`os.environ` をまるごと使う

## [test_mr65_guards.py](../../../../../../../tests/engine/memory/test_mr65_guards.py)

第 6 期 6-5 の守り(書く口は器の中だけ・付け替えの守り・層の契約・宣言の表)。

- 公開の関数とクラス
  - `test_child_columns_are_assigned_only_inside_their_classes`(関数)
  - `test_child_owner_ports_are_called_only_from_the_store`(関数)
  - `test_ledger_rows_and_axes`(関数)
  - `test_negative_control_finds_an_outside_call`(関数)
  - `test_new_modules_respect_the_layer_contract`(関数)
  - `test_runtime_owners_of_the_arm_runs_are_fully_declared`(関数)
  - `test_shop_table_ports_are_called_only_from_the_uncapped_store`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.run`・`shibuya.llm`・`shibuya.mind.memory.memory_embed`・`shibuya.mind.memory.memory_impression`・`shibuya.mind.memory.memory_m1`・`shibuya.mind.memory.memory_shops`・`shibuya.mind.memory.memory_trace`・`shibuya.mind.relations.people`・`shibuya.perception.renderer`・`shibuya.runtime.state.ledger`・`shibuya.runtime.state.ledger_ast`・`tests/_places.py`・`tests/engine/memory/_mr65.py`・`tests/engine/test_state_ledger_10b.py`

## [test_mr65_review_fixes.py](../../../../../../../tests/engine/memory/test_mr65_review_fixes.py)

第 6 期 6-5 の独立検収(mr65/review.md)の直しの試験(L1・L3・L4・M3・L7・CueState の守り)。

- 公開の関数とクラス
  - `test_arms_enter_the_config_section_and_the_fingerprint`(関数)
  - `test_bridge_ids_use_the_stage_names_of_answer_6_2`(関数)
  - `test_cue_state_guards`(関数)
  - `test_ledger_m0_note_declares_the_arm_runs_and_keeps_the_axes`(関数)
  - `test_params_tables_are_read_only_and_the_summary_is_a_plain_copy`(関数)
  - `test_people_readers_compute_each_strength_once`(関数)
  - `test_resume_refuses_another_embed_model_or_another_arm`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.run`・`shibuya.foundation.decl.ledger_paths`・`shibuya.foundation.manifest.sections`・`shibuya.foundation.time_consts`・`shibuya.mind.memory.memory_embed`・`shibuya.mind.memory.memory_m1`・`shibuya.mind.memory.memory_store`・`shibuya.mind.relations.people`・`shibuya.runtime.state.ledger`・`shibuya.runtime.systems.assemble`・`tests/_places.py`・`tests/engine/memory/_mr65.py`
- 決定の ID: 10-12
