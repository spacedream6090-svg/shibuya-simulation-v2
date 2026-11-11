# tests/engine/clock

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 4 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../tests/engine/clock/__init__.py)

(冒頭の説明なし)

## [test_tm2_talk_clock.py](../../../../../../../tests/engine/clock/test_tm2_talk_clock.py)

第 6 期 6-3 時計の段 T2: 会話の時計(``engine.speech_clock``・腕 ``--talk-clock mora``)の試験。

- 公開の関数とクラス
  - `talk`(関数)
  - `test_a_bad_environment_arm_fails_at_import`(関数)
  - `test_anchor_values_are_the_r111_copies`(関数): 写し検査の形: 錨の値と出典(R-111 §3-2 の表・R-73 §4-2)。
  - `test_arm_plumbing`(関数)
  - `test_c1_chat_port_shape_is_blank`(関数)
  - `test_cap_is_a_safety_and_leaves_a_record`(関数)
  - `test_d2_constant_is_the_expected_range_of_18_normals`(関数)
  - `test_different_conversations_are_batched_in_one_dispatch`(関数)
  - `test_in_window_turns_run_in_time_order_and_carry_to_the_next_window`(関数)
  - `test_language_of_other_and_none`(関数)
  - `test_late_turns_are_carried_with_the_lag`(関数)
  - `test_m2_talk_clock_refuses_writes_from_outside`(関数): 〔検収 M2〕負の対照: 外から欄を書く・消す・中身を書くと止まる。``ANCHORS`` の値は書けない(組)。
  - `test_m3_two_turns_of_a_conversation_that_is_not_late_are_refused`(関数): 〔検収 M3〕遅れていない会話(始まりの刻み)で同じ刻みに 2 番を植えても止まる(持ち越しの有無によらない検査)。
  - `test_manifest_keys_match_the_sections_table`(関数)
  - `test_mora_5000_one_day_gives_the_conversation_length_distribution`(関数): 発注: 腕 mora で 5,000 体 1 日が回り、会話の長さの分布が出る(既定の表との差は記録 tm234/README.md §T2)。
  - `test_mora_does_not_change_the_world_and_counts_conversations`(関数)
  - `test_mora_rule_known_counts`(関数): 本当のモーラ数(読みで数えた数)と規則の出力が合う例。
  - `test_mora_rule_known_misses_of_the_kanji_two_mora_approximation`(関数): 〔検収 L3〕漢字 1 字 2 拍の近似(1-8b の読みの規則=仮採用 1)が外れる例: 規則の出力と本当の数を分けて固定する
  - `test_negative_control_adding_the_think_time_is_caught`(関数): 〔検収 L2〕負の対照: 間に TM2 の考える時間(今の表の会話応答 L4 0.2 秒)を足す欠陥を植えると、間の検査が落ちる。
  - `test_negative_control_batching_inside_one_conversation_is_refused`(関数): 同じ会話の 2 つの番を 1 回で作る(=1 回の LLM に会話をまとめて書かせる形)と止まる(会話が遅れているとき)。
  - `test_no_router_is_an_error`(関数)
  - `test_partner_term_familiar_vs_stranger`(関数)
  - `test_partner_term_reads_the_relation_layer_live_edges`(関数)
  - `test_person_rate_distribution_mean_range_and_determinism`(関数)
  - `test_silent_other_language_and_no_session_are_counted`(関数)
  - `test_the_dispatch_check_also_refuses_one_conversation_in_one_batch`(関数): 束の検査(規則 7)も残る: 同じ会話の発言を同じ時刻の束に入れると処理で止まる(持ち主の中を白箱で植える)。
  - `test_think_time_is_not_added_to_the_gap`(関数)
  - `test_two_days_and_resume_with_mora_match_the_straight_default`(関数): 〔検収 L4〕会話の番のある構成(合成の世界・語彙 v1・150 体)で 2 日と日の境目・2 日目の途中からの再開=通し。
  - `test_within_speaker_jitter_has_mean_one_and_cv_042_and_is_keyed_by_the_event`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.llm_bridge`・`shibuya.engine.resume`・`shibuya.engine.speech.port`・`shibuya.engine.speech_clock`・`shibuya.foundation.manifest.sections`・`shibuya.foundation.queues.batching`・`shibuya.foundation.time_consts`
- 環境変数: `os.environ` をまるごと使う
- 決定の ID: R-73・R-111

## [test_tm3_step_scope.py](../../../../../../../tests/engine/clock/test_tm3_step_scope.py)

第 6 期 6-3 時計の段 T3: 何かあった体だけ(``engine.step_scope``・腕 ``--step-scope changed``)の試験。

- 公開の関数とクラス
  - `scope`(関数)
  - `test_arm_plumbing`(関数)
  - `test_changed_run_matches_all_on_the_synthetic_world`(関数)
  - `test_changed_run_matches_all_on_world_assets`(関数)
  - `test_cli_step_scope_beats_the_environment_and_is_an_arm`(関数)
  - `test_m2_step_scope_refuses_writes_from_outside`(関数): 〔検収 M2〕負の対照: 外から欄を書く・消す・写しの配列と計器の中身を書くと止まる。
  - `test_marks_are_exactly_the_changed_columns_and_the_crossed`(関数)
  - `test_marks_follow_value_changes_and_keep_crossed_agents`(関数)
  - `test_scoped_interoception_equals_the_full_one_on_a_superset`(関数)
  - `test_stage_b_declared_writes_with_changed`(関数)
  - `test_two_days_and_resume_with_changed_match_the_straight_default`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.cli`・`shibuya.engine.change_detect`・`shibuya.engine.resolve`・`shibuya.engine.resume`・`shibuya.engine.run`・`shibuya.engine.step_scope`・`shibuya.engine.systems.conductor`・`shibuya.engine.systems.probe`・`shibuya.engine.systems.table`・`shibuya.foundation.manifest.sections`・`shibuya.foundation.time_consts`・`shibuya.world.state`
- 環境変数: `os.environ` をまるごと使う

## [test_tm4_regional_clock.py](../../../../../../../tests/engine/clock/test_tm4_regional_clock.py)

第 6 期 6-3 時計の段 T4: 場所ごとの時計(``engine.regional_clock``・腕 ``--clock regional``)の試験。

- 公開の関数とクラス
  - `arms`(関数)
  - `test_an_event_for_a_region_already_run_in_the_window_goes_to_the_boundary`(関数)
  - `test_boundary_moves_are_counted_with_zero_delay`(関数)
  - `test_cli_clock_regional`(関数)
  - `test_gauge_lateness_reads_the_clock_section`(関数)
  - `test_hearing_across_regions_is_delivered_at_the_window_end`(関数)
  - `test_lateness_from_the_plan_tables`(関数)
  - `test_m2_regional_clock_refuses_writes_from_outside`(関数): 〔検収 M2〕負の対照: 外から欄を書く・消す・配列と表の中身を書くと止まる。
  - `test_m2_the_region_handler_runs_with_the_clock_closed`(関数): 区域の事象の処理の関数(外のコード)を呼ぶ間は時計の欄を書けない(予約の口は書ける=自分で開く)。
  - `test_mixed_is_a_port_only`(関数)
  - `test_negative_control_stage_b_catches_the_missing_declaration`(関数): 負の対照: decide の宣言から行 BW を外すと、発言のある構成の段 B が宣言の外の書きを捕まえる。
  - `test_past_schedule_is_refused`(関数)
  - `test_region_events_run_per_region_in_time_order`(関数)
  - `test_regional_run_matches_global_on_the_synthetic_world`(関数)
  - `test_regional_with_talk_clock_matches_global_on_world_assets`(関数)
  - `test_regions_from_cell_centroids`(関数)
  - `test_stage_b_declared_writes_with_utterances`(関数): 〔検収 M1・L4〕段 B を会話の発言のある構成(合成の世界・語彙 v1・150 体・600 刻み)で腕 mora(全体の時計と区域ごとの時計)
  - `test_two_days_and_resume_with_regional_match_the_straight_global`(関数)
  - `test_window_mark_passes_the_new_rows`(関数)
  - `test_world_assets_have_29_regions`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.regional_clock`・`shibuya.engine.resume`・`shibuya.engine.run`・`shibuya.engine.speech_clock`・`shibuya.engine.systems.build`・`shibuya.engine.systems.conductor`・`shibuya.engine.systems.probe`・`shibuya.engine.systems.spec`・`shibuya.engine.systems.table`・`shibuya.foundation.manifest.sections`・`shibuya.foundation.time_consts`・`shibuya.world.state`
- 環境変数: `os.environ` をまるごと使う
