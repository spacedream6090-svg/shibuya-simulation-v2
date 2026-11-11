# tests/engine/batching

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 3 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../tests/engine/batching/__init__.py)

(冒頭の説明なし)

## [test_conductor_windows.py](../../../../../../../tests/engine/batching/test_conductor_windows.py)

第 3 期 3-2(時計の段 T1): 進行役の窓のループ(``engine.systems.conductor.conduct``)の試験。

- 公開の関数とクラス
  - `test_a_bad_environment_width_fails_at_import`(関数)
  - `test_a_non_default_width_is_an_arm_run`(関数)
  - `test_cli_batch_width_beats_the_environment`(関数)
  - `test_cli_rejects_a_width_that_does_not_divide_the_step`(関数)
  - `test_default_width_is_one_step_per_window_and_ctx_is_the_window_head`(関数)
  - `test_finer_widths_give_the_same_calls_order_final_and_checkpoints`(関数)
  - `test_fingerprint_has_the_width_only_for_the_arm`(関数)
  - `test_l1_stage_b_catches_a_non_bw_change_at_the_window_mark`(関数): 段 B(``SHIBUYA_SYSTEMS_CHECK``=``_conduct_checked``)が、窓の境目に帰属した行 BW の外の変化を落とす(負の対照:
  - `test_l1_window_mark_passes_only_bw_keys_and_tick_head_stays_open`(関数)
  - `test_real_assets_width_10_matches_width_60`(関数)
  - `test_the_system_order_is_the_old_step_loop`(関数): 系の並びは前の刻みのループ(``for T in range(t_begin, t_end)``)と同じ: 刻みごとに 日の頭(立つ日)→ 刻みの系の表の順 →
  - `test_two_days_and_resume_match_the_straight_run_for_the_arm`(関数)
  - `test_window_changes_are_attributed_to_the_window_mark_and_fingerprints_do_not_move`(関数)
  - `width`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.resume`・`shibuya.engine.run`・`shibuya.engine.run_kind`・`shibuya.engine.systems.conductor`・`shibuya.engine.systems.day`・`shibuya.engine.systems.probe`・`shibuya.engine.systems.table`・`shibuya.foundation.queues.batching`・`shibuya.foundation.time_consts`
- 環境変数: `SHIBUYA_SYSTEMS_CHECK`・`os.environ` をまるごと使う

## [test_window_queue.py](../../../../../../../tests/engine/batching/test_window_queue.py)

第 3 期 3-2(時計の段 T1): 計算のまとめの窓 ``engine.batching.WindowQueue`` の単体(合成の事象だけ・data 不要)。

- 公開の関数とクラス
  - `test_boundary_event_inside_the_window_goes_to_the_next_window_head`(関数)
  - `test_cap_carries_the_rest_to_the_next_window_and_counts`(関数)
  - `test_cap_must_be_positive_and_width_must_divide_the_step`(関数)
  - `test_cap_stops_a_zero_delay_loop_without_stopping_the_run`(関数): 0 の遅れで自分を予約し続ける連鎖(会話の番の暴走の形)でも、窓は上限で閉じて次へ進む(止めない・数える)。
  - `test_in_window_and_queued_events_get_distinct_seq`(関数)
  - `test_in_window_kinds_give_the_same_order_and_times_for_every_width`(関数)
  - `test_l6_manifest_fields_after_a_cap_hit`(関数)
  - `test_l6_reservations_beyond_the_ring_keep_order_and_times_for_every_width`(関数)
  - `test_l7_same_time_event_added_inside_a_group_runs_after_the_rest_of_the_group`(関数): 体 5・9 の束(同じ時刻・同じ種類=1 回の処理)の中で体 3 を同じ時刻に足すと、5 → 9 → 3 の順(体の番号順の例外=宣言)。
  - `test_m1_assignment_from_outside_fails`(関数)
  - `test_m1_register_after_the_start_and_duplicate_names_fail`(関数)
  - `test_m1_tables_are_read_only`(関数)
  - `test_manifest_fields_keys_match_the_sections_table`(関数)
  - `test_negative_control_a_boundary_event_below_60_s_changes_the_order_with_the_width`(関数): 負の対照: 窓の境目で届ける種類(TM1 の電話)を 60 秒未満の時刻(80 秒)に 1 つ。60 秒の窓では 120 秒(次の窓の頭)に
  - `test_order_inside_a_window_is_time_then_agent_then_rank_then_seq`(関数)
  - `test_reserve_seq_shares_the_numbering_with_schedule`(関数)
  - `test_same_time_same_kind_is_one_array_in_agent_order`(関数)
  - `test_scheduling_inside_the_window_runs_in_the_same_window_in_time_order`(関数)
  - `test_scheduling_into_the_past_raises`(関数)
  - `test_set_arm_and_is_default`(関数)
  - `test_unknown_kind_and_bad_shapes_raise`(関数)
  - `test_widths_are_the_divisors_of_the_step_and_the_default_is_the_step`(関数)
- import している内部モジュール: `shibuya.foundation.manifest.sections`・`shibuya.foundation.queues.batching`・`shibuya.foundation.queues.scheduler`・`shibuya.foundation.time_consts`
- 決定の ID: 10-03/§7-5
