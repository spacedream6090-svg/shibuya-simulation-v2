# tests/engine

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 83 本・その他 0 本(このディレクトリの直下)

下のディレクトリ: [batching](batching/README.md)・[body](body/README.md)・[bridging](bridging/README.md)・[calendar](calendar/README.md)・[calendar2](calendar2/README.md)・[calendar3](calendar3/README.md)・[clock](clock/README.md)・[contact](contact/README.md)・[decision](decision/README.md)・[duties](duties/README.md)・[events](events/README.md)・[experiment](experiment/README.md)・[memory](memory/README.md)・[multiday](multiday/README.md)・[processes](processes/README.md)・[proximity](proximity/README.md)・[rights](rights/README.md)・[rules](rules/README.md)・[space](space/README.md)・[speech](speech/README.md)・[state](state/README.md)・[systems](systems/README.md)・[time](time/README.md)・[tools](tools/README.md)

## [__init__.py](../../../../../../tests/engine/__init__.py)

engine 層のテスト(llm.mock の結線テストを含む)。

## [ast_writers.py](../../../../../../tests/engine/ast_writers.py)

書く口の AST の道具の共通の置き場(第 1 期 1-7 検収 M1)。試験の補助・src は読むだけ。

- 公開の関数とクラス
  - `Write`(クラス)
  - `WriterScanner`(クラス): 列(``is_col`` が真の属性の名)の中身の書き・差し替え・書く口の呼び出しを集める。
  - `scan_writes`(関数): ``source`` の中の書き(列の中身・差し替え・書く口の呼び出し)。
- 読む試験: `tests/engine/body/test_body_guard.py`・`tests/engine/speech/test_speech_writers_ast.py`・`tests/engine/tools/contacts_writers.py`

## [discard_probe.py](../../../../../../tests/engine/discard_probe.py)

10f(K24 (a)): 軸 2 の実行時の検査「捨てて同じか」の道具(試験だけが使う・src は変えない)。

- 公開の関数とクラス
  - `DiscardReport`(クラス)
  - `calls`(関数)
  - `daily`(関数)
  - `diag`(関数)
  - `differences`(関数): T から後の食い違い(空なら同じ)。最初に食い違った checkpoint の tick と、どのハッシュかを出す。
  - `discardable_paths`(関数): 台帳の外の状態の行のうち軸 2 が ``discardable`` の属性の道筋(``run_day`` の局所の行と持ち主の丸ごとを除く)。
  - `hashes`(関数)
  - `install`(関数): ``monkeypatch`` で計器を入れる(戻すのは ``monkeypatch`` の後始末)。返す報告はランの後に読む。
- import している内部モジュール: `shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.engine.state_hashes`・`shibuya.engine.state_ledger`・`shibuya.engine.systems.state_io`
- 読む試験: `tests/engine/test_state_checks_10f.py`

## [tape_analysis.py](../../../../../../tests/engine/tape_analysis.py)

録画テープの行動分布・対象・会話成立性を数える診断スクリプト(C6・09-09)。

- 公開の関数とクラス
  - `analyze`(関数): テープ 1 本を読んで診断 dict を返す(読み取り専用)。
  - `format_report`(関数)
  - `main`(関数)
- import している内部モジュール: `shibuya.engine.tape`・`shibuya.foundation.vocab.actions`・`shibuya.llm.parser`
- 読む試験: `tests/engine/test_fleet_wiring.py`
- CLI の引数
  - `--json`: 診断 dict を JSON で書き出す先
  - `--top`
  - `tape`: 録画テープのディレクトリ(calls.parquet を含む)
- 決定の ID: D-58

## [test_10a_review_fixes.py](../../../../../../tests/engine/test_10a_review_fixes.py)

10a の検収後の直し(`docs/bench/analysis/wallbounce-1003/review-10a.md`)の既知の答え。

- 公開の関数とクラス
  - `table`(関数)
  - `test_august_is_summer`(関数)
  - `test_datetime_uses_tick_seconds`(関数)
  - `test_home_meals_are_read_by_tick_of_day`(関数)
  - `test_payday_moved_back_across_the_month_boundary`(関数)
  - `test_plus2_path_is_gone`(関数): 〔第 2 部〕+2(旧)の道(受け取りの位置 B)は消した=``run_day(response_delay=2)`` は止まる(前は HEAD の final
  - `test_real_day_key_is_the_day_number`(関数)
  - `test_real_mode_rest_day_reaches_the_mock_schedule`(関数): real の土・日・祝日(8/11 山の日)の mock ランで、mock 日課へ暦の土休が渡る(平日の月曜は渡らない)。
  - `test_relative_holiday_csv_is_resolved_from_the_repo_root`(関数)
  - `test_start_check_runs_on_the_calendar_after_the_weather_date`(関数): 開始日の検査は manifest の開始日(暦)と同じ日を見る。
  - `test_start_must_be_midnight`(関数)
  - `test_tape_meta_does_not_touch_the_parquet`(関数)
  - `test_the_tape_carries_the_response_delay_and_old_tapes_stop`(関数): テープの脇の meta に応答の遅れ(1)を書く・〔第 4 期 4-3 版上げ 3 回目の第 2 部〕+2(旧)の切替口は消した=値 2 の
  - `test_unreadable_csv_stops_real_and_nulls_the_manifest_in_day_index`(関数): 〔改訂(第330・RET)〕前は「day_index では止めず manifest の md5・範囲を null」も見た(day_index を消した)。暦は real
- import している内部モジュール: `shibuya.engine.calendar`・`shibuya.engine.run`・`shibuya.engine.systems.build`・`shibuya.engine.tape`・`shibuya.foundation.paths`・`shibuya.world.body.energy`・`shibuya.world.facts.mock_schedule`・`shibuya.world.facts.weekly_reader`・`shibuya.world.model.state`・`tests/engine/test_calendar.py`・`tests/engine/test_tape_deferred.py`・`tests/engine/test_tape_wiring.py`・`tests/llm/test_fleet.py`
- 決定の ID: 第 330

## [test_ablation23_switches.py](../../../../../../tests/engine/test_ablation23_switches.py)

ablation ②「p_notice の d50 を 0.5×/2×」・③「近接入替の不応期 15 分 ±50%」の切替口。

- 公開の関数とクラス
  - `spread_scene`(関数): 1 セルに個体を **0-79 m の直線上に並べた**場面(距離が効く唯一の合成場面)。
  - `test_a0_is_a_constant_and_ignores_d50`(関数): A0(定数 0.54)は距離を見ない=d50 を振っても到達は動かない(§3.1)。
  - `test_ablation_name_normalizes_every_form`(関数)
  - `test_bad_d50_scale_is_refused`(関数)
  - `test_bad_scale_is_refused`(関数)
  - `test_cli_main_flags`(関数)
  - `test_cli_main_rejects_bad_arms`(関数): 使い方の誤りは traceback ではなく usage(exit 2)で返す。
  - `test_cli_parse_refractory_scale`(関数)
  - `test_cli_run_passes_both_arms_through_kwargs`(関数)
  - `test_d50_default_is_the_section31_table`(関数)
  - `test_d50_scale_multiplies_both_the_default_and_the_per_kind_table`(関数): §3.1 の既定 40 m と ``D50_BY_KIND``(事象クラス別)を**同じ倍率**で振る。
  - `test_d50_scale_reaches_the_salient_process_through_run_day`(関数)
  - `test_default_table_is_the_section6_table_object`(関数): 既定は §6 の表**そのもの**(新しい配列すら作らない=バイト不変の担保)。
  - `test_defaults_are_byte_identical`(関数): 既定値を明示的に渡しても checkpoint・呼数・診断行が 1 ビットも動かない。
  - `test_key_forms_and_zero_factor`(関数)
  - `test_manifest_carries_the_first_wave_arms`(関数)
  - `test_normalized_scale_is_the_manifest_form`(関数)
  - `test_proximity_swap_arm_is_a_no_op_until_the_second_wave`(関数): ③ の腕(近接入替 ±50%)は**起床候補を出す側がまだ無い**ので現状 no-op。
  - `test_reach_grows_with_d50_at_every_ablation_step`(関数): 0.5× < 1.0× < 2.0×(=情報到達半径。§8 ② の指標)。同じ事象・同じ候補で比べる。
  - `test_refractory_scale_moves_the_run`(関数): **起床規則はエンジン側**なので mock でも動く(§8 ③ が mock で測れる根拠)。
  - `test_run_day_checks_the_arm_even_without_processes`(関数): 過程を切ったランでも腕の値を検査する(manifest が嘘の値を持たない)。
  - `test_scaled_table_rounds_half_up`(関数): 15 分 ×0.5 = 7.5 → **8 分**・×1.5 = 22.5 → **23 分**(自前規約・§8 に丸めの規定なし)。
  - `test_set_refractory_refuses_a_wrong_shaped_table`(関数)
  - `test_set_refractory_uses_the_run_table`(関数): ``set_refractory`` は渡された実効表でタイマーを張る(既定は §6 の表)。
  - `test_wake_candidates_follow_the_reach`(関数): 起床候補 (i) は ``noticed_agents`` そのもの=腕は起床数に出る。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.cli`・`shibuya.engine.arbiter`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.world.facts.mock_schedule`・`shibuya.world.laws.salient`・`shibuya.world.laws.switch_rate`・`shibuya.world.model.notice_reach`・`shibuya.world.model.state`
- 決定の ID: 11-01・D-49・D-56

## [test_activation_10e.py](../../../../../../tests/engine/test_activation_10e.py)

第330 ACT(10e 版上げ 1 回目の活性化): テープの脇の meta の暦の規則(親の決定 (5))。

- 公開の関数とクラス
  - `test_act_the_tape_carries_the_calendar_rules_and_the_replay_matches`(関数)
  - `test_act_weather_manifest_declares_the_two_expedients`(関数): 親の決定 (3): 層を広げる順と「同じ近さの影は前の日」は expedient として manifest に載る。
  - `test_ret_a_tape_from_before_the_activation_is_not_replayed`(関数): 〔改訂(第330・RET)〕暦の規則の記録が無いテープ(活性化より前の録画)と旧い値(day_index・legacy)のテープは止める。
  - `test_ret_check_replay_tape_does_nothing_outside_replay`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.run`・`shibuya.engine.tape`・`shibuya.world.laws.environment`・`tests/engine/test_tape_wiring.py`
- 決定の ID: 第 330

## [test_activation_2_4.py](../../../../../../tests/engine/test_activation_2_4.py)

〔第 2 期 2-4 V1〕版上げ 2 回目の世界資産の活性化(2-3b の W12 1.2.0 実ダイヤ+2-3 の W9 の影 7 日の窓)。

- 公開の関数とクラス
  - `activated`(関数): 合成の「前」の資産 → 組んだ資産 → plan → apply まで回した置き場(本体の v2 の代わり=``live``)。
  - `test_m1_materialize_builds_the_previous_asset`(関数): 退避(置き換えた 3 本)+本体の変わっていないファイル → 前の資産。足したファイルは除く。verify --want before が通る。
  - `test_m1_materialize_refuses_a_non_empty_out_and_a_wrong_live`(関数): 負の対照: 置き場が空でない・本体が plan の前とも後とも違う → 止める(終了コード 2)。
  - `test_m1_materialize_stops_on_a_missing_backup_file`(関数): 負の対照: 退避のファイルが欠けていたら組まずに止める(終了コード 2・置き場は作らない)。
  - `test_v1_build_hash_is_the_activated_one`(関数)
  - `test_v1_w12_is_the_real_timetable_version_and_w9_has_the_window`(関数)
  - `test_v1_window_days_read_their_own_shadow`(関数): 窓の 7 日(2026-07-13〜07-19)は暦の日付の影を読む(近い日の影=つなぎ BR-SHADOW-NEAREST-DAY は窓の外の日だけ)。
- import している内部モジュール: `shibuya.build.vis.w9_shadow`・`shibuya.world.assets`・`shibuya.world.laws.environment`

## [test_add_at_guard.py](../../../../../../tests/engine/test_add_at_guard.py)

書き込みガードの**穴**(``numpy`` の ``ufunc.at`` は ``writeable=False`` を見ない)を塞ぐ検査。

- 公開の関数とクラス
  - `test_arbiter_diagnostic_counters_are_not_flagged`(関数): 診断カウンタ(局所配列)への ``np.add.at`` は世界状態ではない=対象外。
  - `test_box_rooted_and_aliased_ufunc_at_outside_resolve_is_found`(関数): 負の対照(1-0 段 FIX・検収 L1): 系の箱の形・その別名・組の代入の別名の ``np.<ufunc>.at`` が見つかる。
  - `test_every_ufunc_at_in_resolve_is_preceded_by_the_frozen_check`(関数): resolve の中でも、状態への ``ufunc.at`` の**直前**に ``_require_thawed`` がある。
  - `test_frozen_flag_is_recorded_by_freeze_and_checked_by_resolve`(関数)
  - `test_numpy_ufunc_at_really_ignores_the_writeable_flag`(関数): **穴の実在**を記録する(この振る舞いが変わったら静的検査を緩めてよい)。
  - `test_resolve_actually_uses_ufunc_at_on_state`(関数): 検査が空振り(=検出ロジックの故障)でないことの陽性対照。
  - `test_set_refractory_is_blocked_when_someone_forgets_the_window`(関数): ``set_refractory`` は ``np.maximum.at`` を撃つ前に ``frozen`` を見る。
  - `test_systems_modules_have_no_state_ufunc_at`(関数): 系のモジュール(engine/systems)にも世界状態への ``ufunc.at`` は無い(書きは resolve の口だけ)。
  - `test_ufunc_at_on_world_or_agent_arrays_lives_only_in_resolve`(関数): ``np.add.at``(等)で世界状態を書けるのは resolve.py だけ。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.build`・`shibuya.economy.ledger`・`shibuya.engine.resolve`・`shibuya.engine.systems.table`・`shibuya.world.model.state`・`tests/_places.py`

## [test_arbiter.py](../../../../../../tests/engine/test_arbiter.py)

engine.arbiter のテスト: 4クラス固定優先・合流・昇格(starvation-free)・縮退・不応期。

- 公開の関数とクラス
  - `test_arbitrate_is_a_pure_function`(関数)
  - `test_conversation_has_no_refractory_floor`(関数)
  - `test_counters_shape_matches_deferral_queue`(関数)
  - `test_deferred_items_come_back_next_tick`(関数)
  - `test_degrade_applies_only_to_the_lower_two_classes_and_only_when_over_budget`(関数)
  - `test_empty_input_is_handled`(関数)
  - `test_fixed_class_priority_beats_arrival_order`(関数): 会話 > 計画境界 > 個体変化 > セル変化(到着順ではない)。
  - `test_l4_budget_arithmetic`(関数): 4,000,000 呼/日 ÷ 1,440 tick × n/400,000。5,000 体で 34.72 呼/tick=10 呼/体/日。
  - `test_no_starvation_under_sustained_overload`(関数): 過負荷でも、どの保留も ``T_max``+予算で決まる上界の内に必ず呼ばれる。
  - `test_permuting_candidates_does_not_change_the_outcome`(関数)
  - `test_promotion_after_t_max`(関数)
  - `test_promotion_is_counted_as_an_event_not_as_a_state`(関数)
  - `test_refractory_shape_is_validated`(関数)
  - `test_refractory_suppresses_but_does_not_drop_the_state_trigger`(関数)
  - `test_same_agent_multiple_conditions_merge_into_one_call`(関数)
  - `test_upper_two_classes_are_never_degraded`(関数)
  - `test_within_class_waiting_time_descending`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.arbiter`・`shibuya.foundation.queues.scheduler`・`shibuya.foundation.types`

## [test_area_source_c9c.py](../../../../../../tests/engine/test_area_source_c9c.py)

C9c-1 ``--area-source {legacy,plateau}`` と席面積の感度腕の検収。

- 公開の関数とクラス
  - `test_area_sources_and_default`(関数)
  - `test_crowd_process_keeps_the_current_table_by_default`(関数)
  - `test_default_is_byte_identical_to_explicit_legacy`(関数)
  - `test_legal_constants_match_the_primary_sources`(関数): 消防法施行規則 1 条の 3(飲食 3 m² / 物販 4 m²)・建告1441(飲食室 0.7 人/m² =
  - `test_load_walkable_area_matches_the_parquet_order`(関数)
  - `test_load_walkable_area_refuses_unknown_cells`(関数)
  - `test_manifest_carries_the_area_source_field`(関数)
  - `test_plateau_is_refused_for_injected_renderers`(関数)
  - `test_plateau_without_the_asset_fails_loudly`(関数)
  - `test_run_day_rejects_a_non_positive_seat_area`(関数)
  - `test_run_day_rejects_an_unknown_area_source`(関数)
  - `test_seat_area_arm_reaches_the_manifest`(関数)
  - `test_seat_area_override_changes_the_seat_count_only_when_given`(関数)
  - `test_the_same_denominator_reaches_detector_and_geometry`(関数): ``walkable_area_m2`` を替えると LOS 段(起床条件 (i))と Kladek 減速が**同時に**動く。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.change_detect`・`shibuya.engine.run`・`shibuya.perception.renderer`・`shibuya.world.assets`・`shibuya.world.laws.crowd`・`shibuya.world.model.geometry`・`shibuya.world.model.state`
- 決定の ID: D-84

## [test_assets_10e_b0_b1.py](../../../../../../tests/engine/test_assets_10e_b0_b1.py)

10e(版上げ 1 回目)B0 資産の指紋・B1 旧資産の切替口(第330)。

- 公開の関数とクラス
  - `test_b0_hashes_stay_out_of_the_final`(関数)
  - `test_b0_manifest_lists_what_the_run_read_and_the_two_noise_readers_agree`(関数)
  - `test_b0_world_reader_records_the_file_and_cell_hashes`(関数)
  - `test_b1_switch_is_gone`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.run`・`shibuya.perception.renderer`・`shibuya.world.assets`・`shibuya.world.laws.environment`
- 決定の ID: 第 330

## [test_c9b_targets_attention.py](../../../../../../tests/engine/test_c9b_targets_attention.py)

C9b 対象と注意(G3/G4/G5/G6/G7)の検収。

- 公開の関数とクラス
  - `BoomLLM`(クラス): 再生モードで**呼ばれたら落ちる** LLM(テープ外 0 の陽性対照)。
  - `test_apply_talk_rejects_a_partner_beyond_the_open_distance`(関数)
  - `test_approach_hint_targets_the_cell_of_the_person_or_landmark`(関数)
  - `test_approach_reports_target_gone_when_nobody_is_there_on_arrival`(関数): 最後に見た位置へ着いても対象が居なければ ``TARGET_GONE``(§4 改訂 G11)。
  - `test_approach_to_a_landmark_poi_uses_the_poi_node`(関数)
  - `test_approach_to_an_unreachable_target_fails_with_unreachable`(関数): 対象のセル/ノードが取れない(場外の相手)= ``UNREACHABLE``。
  - `test_approach_walks_to_the_node_nearest_the_target_and_arrives`(関数): 「近づく」= 移動の対象が人。目的ノードは**対象に最も近いノード**。
  - `test_attention_arm_is_deterministic_and_differs_from_the_edge_arm`(関数)
  - `test_attention_arm_needs_both_edge_and_v2`(関数): 腕は ``geometry="edge"`` **かつ** ``vocab_version="v2"`` の積でだけ立つ。
  - `test_attention_arm_tape_replays_bit_for_bit`(関数): edge + 語彙 v2 で録ったテープの再生が checkpoint 列まで一致・テープ外 0。
  - `test_attention_columns_cost_five_bytes_per_agent`(関数): ``focus_target`` int32 + ``focus_ttl`` uint8 = **5 B/体**(宣言どおり)。
  - `test_conversation_closes_only_past_the_leave_distance`(関数)
  - `test_default_arms_have_no_attention_columns_and_no_new_counters`(関数): 既定の 3 腕(node/v1・node/v2・edge/v1)は C9b の欄も診断も持たない。
  - `test_dictionary_v4_maps_word_and_hint`(関数)
  - `test_dictionary_v4_only_applies_to_vocab_v2`(関数): 語彙 v1 では写像先もヒントも現行のまま(「近づく」「見る」は未定義のまま)。
  - `test_engine_resolves_home_work_school_hints_to_the_w16_cells`(関数): 「帰宅」「通勤」「通学」の行き先を**エンジンが**拠点セルに解決する(G5)。
  - `test_focus_codes_only_fire_for_approach_and_look`(関数)
  - `test_focus_expires_after_its_max_age`(関数): 寿命(UE ``Max Age`` 型)で焦点が消える。
  - `test_focus_is_lost_beyond_the_lose_radius_which_is_wider_than_acquire`(関数): 喪失距離 > 取得距離(Sight / Lose Sight 型のヒステリシス)。
  - `test_focus_upkeep_stays_inside_the_p2_budget`(関数): 焦点の寿命・喪失距離の毎 tick 更新が P2(≤5 ms/フレーム@5 千体)を食わない。
  - `test_hint_words_and_engine_codes_are_one_to_one`(関数): ヒントの語(llm)と索引(engine)が 1 対 1(二重定義の機械検査)。
  - `test_landmark_cats_are_shared_between_world_and_renderer`(関数): 目印の集合は**世界側と知覚側で同じ 1 本**(二重定義を作らない)。
  - `test_landmark_mask_and_name_table`(関数)
  - `test_landmark_resolution_order_prefers_the_tightest_name`(関数)
  - `test_longest_match_still_wins_over_the_new_two_character_row`(関数): 新しい 2 字の行(``見る``)が既存の長い表層を食わない(最長一致)。
  - `test_look_beyond_the_acquire_radius_does_not_set_a_focus_but_still_succeeds`(関数)
  - `test_look_sets_the_focus_when_the_target_is_within_the_acquire_radius`(関数)
  - `test_no_hint_means_the_current_destination_rule`(関数): ヒントを渡さなければ**1 バイトも変わらない**(職場/自宅の現行規則)。
  - `test_parse_target_resolves_a_proper_name_to_a_poi`(関数)
  - `test_real_assets_have_the_68_landmarks_and_resolve_hachiko`(関数): 実資産(W6): landmark 56 + attraction 12 = 68 件・「ハチ公像」→ 忠犬ハチ公像。
  - `test_renderer_puts_the_focus_person_first_in_b5`(関数): B5(個体ブロック)は焦点の人物を先頭に置く。**B2 は共有ブロックなので触らない**。
  - `test_talk_open_and_leave_distances_form_a_hysteresis`(関数)
  - `test_talk_within_reach_needs_same_cell_and_two_meters`(関数)
  - `test_v1_dictionary_and_version_are_untouched`(関数): 語彙 v1 の段0 辞書・版・対象ヒント表は**同一オブジェクト**のまま。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.commit`・`shibuya.engine.conversation`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.foundation.vocab.actions`・`shibuya.llm.undefined`・`shibuya.perception.renderer`・`shibuya.world.model.geometry`・`shibuya.world.model.state`・`tests/engine/time/__init__.py`
- 決定の ID: 第 346

## [test_calendar.py](../../../../../../tests/engine/test_calendar.py)

10a(指示書 10-03 §3-1 A1・A1-1・A1-2・A1-3): 暦の口 ``engine.calendar`` の既知の答え。

- 公開の関数とクラス
  - `table`(関数)
  - `test_T_and_datetime`(関数)
  - `test_bad_files_stop`(関数)
  - `test_day_index_mode_ignores_holidays_and_keeps_the_old_values`(関数): 〔改訂(第330・RET)〕前は day_index の暦が旧い式と同じ値(曜日 = (day_index + 日) % 7・土休 = 曜日 >= 5・祝日は
  - `test_day_index_mode_only_warns_but_still_stops_out_of_range`(関数): 〔改訂(第330・RET)〕前は「day_index では規則の違反は警告だけ・範囲外は止める」を見た(day_index を消した)。
  - `test_holiday_rows_named_kyujitsu_are_holidays`(関数)
  - `test_legacy_calendar_equals_day_index_mode`(関数): 〔改訂(第330・RET)〕旧い口 ``SimCalendar.legacy``(day_index の暦)は ``SimCalendar.default``(2026-07-13 + day_index 日・
  - `test_manifest_fields`(関数)
  - `test_md5_is_of_the_file_bytes`(関数)
  - `test_missing_csv_gives_an_empty_table_and_warns_once`(関数)
  - `test_parse_school_holidays_forms`(関数)
  - `test_parse_start_forms`(関数)
  - `test_payday_is_off_by_default_and_moves_to_the_previous_business_day`(関数)
  - `test_real_mode_without_a_holiday_table_stops`(関数)
  - `test_real_weekday_and_holidays`(関数)
  - `test_season_follows_the_jma_months`(関数)
  - `test_start_check_known_dates`(関数)
  - `test_the_real_cabinet_office_csv`(関数)
  - `write_csv`(関数)
- import している内部モジュール: `shibuya.engine.calendar`・`shibuya.engine.classical`
- 読む試験: `tests/engine/test_10a_review_fixes.py`・`tests/engine/test_calendar_sites.py`・`tests/engine/test_sim_time_T.py`
- 決定の ID: 10-03/§3-1・第 330

## [test_calendar_10e_e3.py](../../../../../../tests/engine/test_calendar_10e_e3.py)

10e E3(第330): 暦の一本化。

- 公開の関数とクラス
  - `test_act_holiday_opening_hours_come_from_holiday_content_or_the_sunday_row`(関数)
  - `test_act_w7_reader_takes_the_holiday_content_column_as_ph`(関数)
  - `test_e3_defaults_come_from_one_constant`(関数)
  - `test_e3_opening_row_takes_holidays_from_the_cabinet_office_csv`(関数)
  - `test_e3_ph_row_uses_the_ph_spans_or_the_sunday_row`(関数)
  - `test_e3_run_day_and_cli_defaults_are_unchanged`(関数)
  - `test_e3_two_days_advance_on_the_calendar_and_the_weekday_rows_come_from_it`(関数): 〔改訂(第330・RET)〕前は legacy(day_index)の 2 日のランと曜日の行を比べた(legacy を消した)。今は暦の値だけを見る。
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.calendar`・`shibuya.engine.presence`・`shibuya.engine.run`・`shibuya.world.assets`・`shibuya.world.laws.opening`
- 決定の ID: 第 330・第 333

## [test_calendar_sites.py](../../../../../../tests/engine/test_calendar_sites.py)

10a: 暦を引いていた箇所を暦の口(``engine.calendar.SimCalendar``)へ付け替えた結果の既知の答え。

- 公開の関数とクラス
  - `table`(関数)
  - `test_cli_main_accepts_the_switches`(関数)
  - `test_cli_switches_and_defaults`(関数)
  - `test_mock_schedule_takes_the_rest_day_from_the_calendar`(関数)
  - `test_named_closed_next_day_comes_from_the_calendar`(関数)
  - `test_rail_timetable_kind_comes_from_the_calendar`(関数)
  - `test_runner_keeps_the_old_values_in_day_index_mode`(関数): 暦を渡さない実行器は ``SimCalendar.default(day_index)``(2026-07-13 + day_index 日・祝日の表なし)。曜日の行と土休は
  - `test_runner_reads_the_real_calendar`(関数)
  - `test_the_attendance_draw_was_removed`(関数): 〔11-01 段 2 の 4〕出勤率のくじ(E6)は道ごと消した=全員出勤の宣言(``engine.rate_rules`` の attendance)。
  - `test_weather_day_key_is_unchanged_on_day0_and_moves_from_day1`(関数): 〔改訂(第330・RET)〕前は legacy の実日の選び方 ``select_day``(0 日目の鍵=層名だけ・1 日目から日番号を足す)を見た
- import している内部モジュール: `shibuya.agents.state`・`shibuya.cli`・`shibuya.engine.calendar`・`shibuya.engine.presence`・`shibuya.engine.run`・`shibuya.world.assets`・`shibuya.world.facts.mock_schedule`・`shibuya.world.laws.environment`・`shibuya.world.laws.opening`・`shibuya.world.laws.rail`・`shibuya.world.laws.runner`・`shibuya.world.model.state`・`tests/_data_ids.py`・`tests/engine/test_calendar.py`
- 決定の ID: 11-01・第 330

## [test_census_out.py](../../../../../../tests/engine/test_census_out.py)

``--census-out`` — 日次センサス/月次 MER の出力口(境界・経済設計書 §2.4)。

- 公開の関数とクラス
  - `test_census_out_creates_missing_parents`(関数)
  - `test_census_out_writes_the_three_files`(関数)
  - `test_default_writes_nothing`(関数)
  - `test_explicit_none_is_the_same_as_the_default`(関数)
  - `test_run_day_without_a_ledger_writes_nothing`(関数)
  - `test_the_checkpoint_does_not_move`(関数): 観測(センサスの書き出し)は世界を変えない=checkpoint 列が 1 ビットも動かない。
- import している内部モジュール: `shibuya.cli`・`shibuya.economy.census`・`shibuya.engine.run`
- 決定の ID: D-76・第 204

## [test_change_detect_p6.py](../../../../../../tests/engine/test_change_detect_p6.py)

engine.change_detect のテスト+**予算行 P6 の実測**(≤2 ms/tick@40万体)。

- 公開の関数とクラス
  - `test_agents_outside_the_world_are_never_woken_by_cells`(関数)
  - `test_b4_hash_matches_full_recompute`(関数): 差分だけ再ハッシュしても、全行を計算し直した値と一致する。
  - `test_candidates_have_condition_and_class`(関数)
  - `test_cell_wake_agents_are_exactly_those_in_changed_cells`(関数)
  - `test_detector_does_not_write_to_state`(関数): 検出器は**書かない**(resolve が唯一の書き手)。
  - `test_interoception_hysteresis_has_no_oscillation`(関数): 閾値ちょうどを往復しても、ヒステリシス帯の内側では段が動かない。
  - `test_interoception_up_crossing`(関数)
  - `test_numba_kernel_matches_numpy_reference`(関数)
  - `test_p6_change_detection_under_2ms_at_400k_agents`(関数): 予算行 P6: 40万体×453セル・100 tick の平均 ≤2 ms/tick。
  - `test_p6_scaled_down_runs_in_ci`(関数): CI 用の縮小版(4万体×453セル)。絶対値ゲートは slow 側。
  - `test_unchanged_cells_are_not_reported`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.change_detect`・`shibuya.foundation.types`・`shibuya.world.model.state`・`tests/_time_gates.py`・`tests/engine/time/__init__.py`

## [test_classical_policy.py](../../../../../../tests/engine/test_classical_policy.py)

5 段目 5b: System 1.5=古典的選択モデル(D-119 L1〜L8・第292)のテスト。

- 公開の関数とクラス
  - `test_activity_map_v0_location_rules`(関数)
  - `test_aspiration_moves_with_the_hunger_word`(関数)
  - `test_cli_exposes_the_5b_flags`(関数)
  - `test_conversation_turn_replies_to_the_inviter`(関数)
  - `test_day_kind_follows_the_day_index`(関数)
  - `test_default_run_does_not_touch_the_rich_context`(関数): 既定の選び手 nearest では価格・訪問回数を組まない(既定 checkpoint 不変の構造上の担保)。
  - `test_hunger_stage_reads_both_models`(関数)
  - `test_ipf_constants_return_the_population_marginal_to_the_prior`(関数)
  - `test_make_chooser_knows_classical`(関数)
  - `test_meal_gate_combines_word_calendar_and_surroundings`(関数)
  - `test_per_call_paths_have_no_python_loops_over_agents`(関数)
  - `test_prior_anchor_is_numbers_and_codes_only`(関数)
  - `test_prior_row_is_a_distribution_with_declared_fallbacks`(関数)
  - `test_rank_jitter_tau_and_habit`(関数)
  - `test_responses_parse_as_v3_and_are_deterministic`(関数)
  - `test_run_day_classical_arm_and_layers`(関数)
  - `test_zero_sample_stratum_falls_back_to_the_age_total_row`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.cli`・`shibuya.engine.chooser`・`shibuya.engine.classical`・`shibuya.engine.poi_target`・`shibuya.engine.run`・`shibuya.foundation.vocab.actions`・`shibuya.llm`・`shibuya.llm.parser`・`shibuya.world.model.state`
- 決定の ID: D-119・第 292

## [test_classical_social.py](../../../../../../tests/engine/test_classical_social.py)

第2波 §2A 項 3-1: 古典の腕の**交際・付き合い(符号 18)の相手=知人**(Q42 (b)・指示書 §0-3・§4)のテスト。

- 公開の関数とクラス
  - `test_busy_or_asleep_or_out_of_reach_acquaintances_are_skipped`(関数): 検収後: 会話中・就寝中の知人(resolve._UNADDRESSABLE)と、会話の届かない知人(別のセル・edge 幾何なら 2 m 超)
  - `test_near_first_reproduces_the_old_rule`(関数)
  - `test_run_golden_and_arms`(関数)
  - `test_talks_to_the_nearby_acquaintance_with_the_largest_activation`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.cli`・`shibuya.engine.classical`・`shibuya.engine.run`・`shibuya.world.model.state`・`tests/golden_env.py`
- 読む試験: `tests/engine/test_env_and_sections_10f.py`
- 決定の ID: 11-01・第 330

## [test_clock.py](../../../../../../tests/engine/test_clock.py)

engine.clock のテスト(壁時計非依存・tick↔日時・δ_perc のナノ秒欄)。

- 公開の関数とクラス
  - `test_ceil_tick_matches_t_apply_rule`(関数): §2.4: t_apply=起床+δ_perc+δ_think を分tickへ**切り上げ**。
  - `test_clock_is_hashable_and_frozen`(関数)
  - `test_rejects_bad_arguments`(関数)
  - `test_t_sim_ns_uses_delta_perc_seconds`(関数): δ_perc(0.2〜1.5秒)は世界時刻を進めず、tick 内ナノ秒欄になる(運用設計書 §2.3)。
  - `test_tick_datetime_roundtrip`(関数)
  - `test_ticks_per_sim_day`(関数)
  - `test_timezone_mismatch_is_rejected`(関数)
- import している内部モジュール: `shibuya.engine.clock`・`shibuya.foundation.types`

## [test_conversation.py](../../../../../../tests/engine/test_conversation.py)

engine.conversation のテスト(行動契約書 §3 会話プロトコル)。

- 公開の関数とクラス
  - `test_backchannels_are_engine_generated_and_deterministic`(関数)
  - `test_closing_emits_the_fixed_closing_utterance_then_terminal`(関数)
  - `test_counters_report_openings_and_reasons`(関数)
  - `test_d_talk_is_declared_even_though_the_proxy_is_same_cell`(関数): C3 は「距離≦d_talk」を同一セルで代理する(定数は宣言だけ残す)。
  - `test_gate_passes_when_all_five_conditions_hold`(関数)
  - `test_gate_rejects_each_missing_condition`(関数)
  - `test_gate_rejects_self_invitation`(関数)
  - `test_hard_stop_at_max_turns_three_calls_per_agent`(関数)
  - `test_interrupt_is_discretised_to_the_next_transition_point`(関数)
  - `test_invalid_configuration_is_rejected`(関数)
  - `test_join_respects_the_participant_cap`(関数)
  - `test_leaving_is_never_decided_by_the_llm_but_退去_closes_the_session`(関数)
  - `test_non_response_is_an_ignored_event_and_costs_no_call`(関数)
  - `test_one_conversation_per_agent`(関数)
  - `test_purge_terminal_frees_the_table`(関数)
  - `test_refusal_memory_blocks_the_pair_for_a_while`(関数)
  - `test_run_day_leaves_no_conversing_agent_without_a_session`(関数): 層2指摘(C3): 不応答/却下の招待側が CONVERSING に取り残されない。
  - `test_run_day_opens_conversation_sessions_when_resolve_creates_them`(関数): resolve が会話を成立させたら ``ConversationManager`` が受け取り、話者を起こす。
  - `test_session_starts_participating_with_the_inviter_as_first_speaker`(関数)
  - `test_session_timeout_is_a_bounded_cleanup`(関数)
  - `test_soft_stop_on_silence`(関数)
  - `test_soft_stop_when_a_participant_leaves_the_cell`(関数)
  - `test_soft_stop_when_the_topic_stack_is_empty`(関数)
  - `test_speakers_alternate_starting_with_the_inviter`(関数)
  - `test_the_dead_accept_lottery_is_removed`(関数): 〔第346 死んだ道の削除〕応答率 0.8 の抽選(``answered=None`` のときだけ引いた)は消した=返事は必ず渡す。
  - `test_the_dead_important_extra_calls_are_removed`(関数): 〔第346 死んだ道の削除〕重要度上位の +2 呼(組み立ては対象を渡さなかった)は消した=全員 ``max_turns``。
  - `test_wake_candidates_are_conversation_turns_with_zero_refractory`(関数)
  - `test_walking_over_state_can_be_enabled`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.conversation`・`shibuya.engine.run`・`shibuya.foundation.types`・`shibuya.foundation.vocab.actions`・`shibuya.llm`
- 決定の ID: 第 346

## [test_conversation_invite.py](../../../../../../tests/engine/test_conversation_invite.py)

C6 会話招待の設計準拠(09-09): 「対象」欄で名指し → 被招待が**自分の呼**で答える。

- 公開の関数とクラス
  - `NamingLLM`(クラス): 個体 a が「会話 対象: P-(a^1)」と答える台本(**対を組む**)。
  - `make_manager`(関数)
  - `run_named`(関数)
  - `test_acceptance_from_another_cell_is_a_refusal`(関数)
  - `test_acceptance_is_consumed_before_phase_c_so_no_false_partner_busy`(関数): 層2 中-1: 承諾「会話 対象: P-A」は Phase C へ流さない=B に偽の失敗が載らない。
  - `test_acceptance_without_a_target_is_also_accepted`(関数)
  - `test_alone_in_the_cell_yields_no_partner_and_source_absent`(関数)
  - `test_answering_another_action_is_a_refusal`(関数)
  - `test_declining_invitees_do_not_open_sessions_and_the_inviter_is_reverted`(関数): B が 待機 と答えたら不成立=招待側は CONVERSING に取り残されない。
  - `test_intents_from_responses_fills_the_stats`(関数)
  - `test_intents_from_responses_uses_the_run_salt_for_the_fallback_order`(関数): 軽-4: フォールバックのセル内順序が **blake3 撹拌**で、塩を変えると並びが変わる。
  - `test_mock_llm_never_names_a_partner_so_the_fallback_path_is_unchanged`(関数): MockLLM は「対象: なし」しか書かない=名指し 0・フォールバックのみ(T2 の由来)。
  - `test_named_person_in_another_cell_falls_back_and_is_counted`(関数)
  - `test_named_person_in_the_same_cell_wins_over_the_batch_fallback`(関数)
  - `test_named_target_drives_invites_end_to_end`(関数): A が「会話 対象: P-B」→ B が次 tick に被招待で起床 → B の返事で成否が決まる。
  - `test_naming_a_third_party_is_a_refusal_and_stays_an_intent`(関数): 層2 中-2: 第三者 C を名指した 会話 は A への**拒否**(承諾ではない)。
  - `test_naming_yourself_or_out_of_range_falls_back`(関数)
  - `test_pair_and_speaker_refractory_block_repeat_invites`(関数)
  - `test_pending_invite_expires_and_returns_the_inviter`(関数)
  - `test_pending_invite_is_accepted_when_the_invitee_answers_talk`(関数)
  - `test_pending_invite_is_declined_when_the_invitee_answers_something_else`(関数)
  - `test_register_pending_rejects_other_cell_self_and_busy`(関数)
  - `test_set_conversing_marks_both_sides`(関数)
  - `test_settle_is_a_no_op_without_pending_invites`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.commit`・`shibuya.engine.conversation`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.llm`・`shibuya.world.facts.mock_schedule`・`shibuya.world.model.state`
- 決定の ID: 11-03・D-56・第 330

## [test_defect_fixes_1103.py](../../../../../../tests/engine/test_defect_fixes_1103.py)

〔11-03 §3〕棚卸し B の欠陥 4 件(M10・M11・M28・M16)の直しと切替口 ``engine.defect_fixes_1103`` の試験。

- 公開の関数とクラス
  - `test_a_body_choosing_a_talk_without_a_target_keeps_its_activity`(関数): 〔中-2〕対象の決まらない会話(resolve が失敗させた体=活動は変わっていない)。旧道は寝ている体を IDLE にして起こしていた
  - `test_a_body_that_joined_a_session_in_the_same_call_is_not_released`(関数): 〔低-2〕A が B に断られて戻す候補に積まれ、同じ呼び出しの後の行で C の招待を承諾してセッションに入った。直した道は
  - `test_a_queued_body_that_is_moved_elsewhere_is_dropped_before_serving`(関数): 移動・乗車の外で動いた体(ここでは域の外からの到着の口で別のセルへ置いた)は、捌く前に列から外す(直した道だけ)。
  - `test_a_queued_body_that_walks_away_leaves_the_queue`(関数)
  - `test_a_queued_body_that_walks_to_the_platform_leaves_the_queue`(関数)
  - `test_a_refusal_keeps_the_inviters_new_activity`(関数): 返事の解決(``_settle_pending_invites``)の末尾の戻し: 断られた招待側が SHOPPING なら既定では残す(旧道は IDLE)。
  - `test_an_expired_invite_keeps_the_inviters_new_activity`(関数): 返事待ちの間に歩き出した招待側(MOVING)は、期限切れの戻しで MOVING のまま(〔第346〕系の旧道=IDLE は消した)。
  - `test_an_expired_invite_still_releases_a_waiting_conversing_inviter`(関数): 返事を待って CONVERSING のままの招待側は IDLE に戻る(戻しの意図そのもの)。
  - `test_an_invitee_that_moved_away_then_accepts_keeps_the_invite_ledger_balanced`(関数): 〔中-1〕招待の後に被招待が別のセルへ動いてから承諾した。既定は不成立(``conv_pending_unreachable``=腕 on のランだけ
  - `test_an_unreachable_acceptance_is_not_a_refusal`(関数)
  - `test_drop_pending_counts_the_origin`(関数)
  - `test_end_conversation_keeps_the_activity_of_bodies_that_are_not_conversing`(関数)
  - `test_other_replies_are_still_refusals`(関数): 届かなくても「会話」でない返事は今のまま断り(直すのは承諾の返事だけ)。
  - `test_removed_defect_fixes_switch_env_and_cli_flag_stop`(関数): 〔第346〕消した切替口: 環境変数 SHIBUYA_DEFECT_FIXES_1103 を与えると読み込みで止まる・CLI の旗は引数の誤り・系は
  - `test_resume_without_the_header_is_refused`(関数): 腕は設定の指紋に入れない=状態のファイルの見出しの ``defect_fixes_1103``(常に on)を見る。〔第346〕見出しに無い状態の
  - `test_revert_conversation_is_the_legacy_release`(関数)
  - `test_run_manifest_section`(関数)
  - `test_state_header_and_resume_check`(関数)
  - `test_the_arm_is_not_a_run_day_argument`(関数): 腕は組み立てで 1 回読む(``run_day`` の引数にしない=設定の指紋に入れない)。
  - `test_the_conversation_system_releases_only_conversing_bodies`(関数): 会話の番で「移動」を選んで歩き出した体(MOVING)は、セッションの終わりで止まらない(〔第346〕系の旧道=全員を IDLE は
  - `test_the_default_arm_is_on_and_names_are_checked`(関数)
  - `test_the_queue_checks_payment_like_a_new_purchase`(関数)
  - `test_the_unreachable_origin_key_is_there_from_the_start_only_when_counted`(関数): 〔低-4〕起点の計数の鍵は最初から全部ある作り=腕 on のランは unreachable も最初から 0 で置く(旧道は鍵を足さない)。
  - `tiny_runs`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.cli`・`shibuya.engine.commit`・`shibuya.engine.conversation`・`shibuya.engine.defect_fixes_1103`・`shibuya.engine.resolve`・`shibuya.engine.resume`・`shibuya.engine.run`・`shibuya.engine.systems.boxes`・`shibuya.engine.systems.talk`・`shibuya.world.laws.crowd`・`shibuya.world.laws.rail`・`shibuya.world.model.state`・`tests/engine/processes/conftest.py`
- 環境変数: `SHIBUYA_DEFECT_FIXES_1103`・`os.environ` をまるごと使う
- 決定の ID: 11-03・11-03/§3・第 346

## [test_determinism_t1_t2_t4.py](../../../../../../tests/engine/test_determinism_t1_t2_t4.py)

決定論のテスト: T1/T2(同一 seed で checkpoint ハッシュ一致)・T4(規模不変)・M7(膨張率)。

- 公開の関数とクラス
  - `test_checkpoint_hash_survives_a_reload`(関数)
  - `test_checkpoints_are_taken_at_the_declared_interval`(関数)
  - `test_degenerate_sizes_do_not_crash`(関数)
  - `test_different_seed_gives_different_hashes`(関数)
  - `test_m7_checkpoint_roundtrip_of_agents_and_world`(関数)
  - `test_run_is_reproducible_from_a_prebuilt_world`(関数)
  - `test_run_salt_is_a_deterministic_16_byte_digest`(関数)
  - `test_same_seed_gives_identical_checkpoint_hashes`(関数)
  - `test_t4_holds_for_the_run_initialisation`(関数): 個体数を 1 体増やしても、既存個体の初期状態は変わらない。
  - `test_t4_scale_invariance_of_the_rng_stream`(関数): n=5,000 と 5,001 で、先頭 5,000 体の抽選が**バイト一致**。
- import している内部モジュール: `shibuya.engine.run`・`shibuya.foundation.serialize`・`shibuya.world.facts.mock_schedule`・`shibuya.world.model.state`

## [test_eatery_place_food.py](../../../../../../tests/engine/test_eatery_place_food.py)

段 1b(D-96 nightlife (b)): 飲食店の切替口 ``eatery={food, place_food}``。

- 公開の関数とクラス
  - `test_eatery_modes_and_default`(関数)
  - `test_place_food_adds_nightlife_except_the_four_amusement_subcats`(関数)
  - `test_place_food_equals_food_on_the_synthetic_world`(関数): 合成世界(nightlife なし・subcat なし)では 2 つの腕は同じ集合=final も同じ。
  - `test_place_food_is_exactly_the_w17_place_word_food_set`(関数): 実資産: place_food の集合 = W17 の場所語「飲食店」へ写る POI(1,042 件)。food は 823 件。
  - `test_place_food_refuses_a_world_without_subcat_when_nightlife_exists`(関数)
  - `test_run_day_rejects_an_unknown_eatery_before_running`(関数)
  - `test_run_day_resets_the_eatery_of_a_reused_world`(関数): 同じ World を使い回しても前のランの切替口は残らない(run_day が毎ラン書く)。
  - `test_the_excluded_subcats_match_the_w17_place_word_table`(関数): 二重定義の一致: nightlife の subcat のうち W17 で「飲食店」以外へ写るもの。
- import している内部モジュール: `shibuya.build.geo.poi_class`・`shibuya.build.sched.vocab`・`shibuya.build.sched.w17_schedule`・`shibuya.engine.run`・`shibuya.world.model.state`
- 決定の ID: D-96

## [test_energy_balance.py](../../../../../../tests/engine/test_energy_balance.py)

5 段目 5a: 体のエネルギー収支(D-118 K1〜K9・第291)のテスト。

- 公開の関数とクラス
  - `energy_agents`(関数)
  - `layer`(関数)
  - `model`(関数)
  - `test_advance_body_without_energy_is_the_old_rule`(関数)
  - `test_anchor_file_holds_numbers_and_codes_only`(関数): 表の文言(活動名の和文など)は入れない=和文は出典表記の 4 行だけ。
  - `test_anchor_values_are_pinned`(関数): アジェンダ §1-9 の固定値: 23.7/63.0・1.75・199/164・31.1/37.3/26.5・77.2/7:12・3.5/4.3/3.0/1.0/1.3。
  - `test_b5_draws_hunger_as_words_only_from_hungry`(関数)
  - `test_b5_of_a_v1_run_keeps_the_old_numbers`(関数)
  - `test_bmr_arm_gives_bmr_times_mean_mets`(関数): K1 (a) の感度腕: 基準日=BMR 1,575 × 平均 METs 1.379 ≈ 2,172(草案 §1-2b (1))。
  - `test_bmr_arm_runs_and_is_recorded`(関数)
  - `test_body_draw_is_per_agent_and_deterministic`(関数)
  - `test_cli_default_hunger_model_is_energy`(関数)
  - `test_eer_floor_is_the_basal_metabolism`(関数)
  - `test_eer_of_the_reference_body_is_2756`(関数): 草案 §1-2b: 男 30〜49 歳・参照体重 70.0 kg → BMR 1,575・EER 2,756。
  - `test_energy_run_stops_the_plus_one_and_keeps_fatigue`(関数)
  - `test_hunger_words_live_in_the_templates`(関数)
  - `test_initialize_energy_places_the_copy_without_a_false_crossing`(関数)
  - `test_meal_share_depends_on_time_sex_and_age`(関数)
  - `test_meal_shares_are_normalized_to_three_meals`(関数)
  - `test_mets_follow_the_activity`(関数)
  - `test_out_of_area_meal_resets_since_meal_and_adds_the_share`(関数)
  - `test_out_of_area_schedule_uses_meal_rows_then_default_times`(関数)
  - `test_out_of_area_schedule_without_weekly_is_three_default_times`(関数)
  - `test_per_tick_paths_have_no_python_loops`(関数): P4: 毎 tick 通る関数に for/while を書かない(体数ぶんの逐次ループを新設しない)。
  - `test_poi_intake_kind_is_food_or_convenience_for_snacks`(関数)
  - `test_reference_day_expenditure_equals_eer_within_0_1_percent`(関数): (g) 基準日の構成で 1,440 tick の消費の和は EER に 0.1% 以内で一致する(AVG_METS=1.379)。
  - `test_run_day_default_is_v1_and_energy_is_an_arm`(関数)
  - `test_snack_and_drink_subtract_from_since_meal`(関数)
  - `test_stage_edges_and_hunger_copy`(関数)
  - `test_unknown_sex_uses_the_mean_of_the_two_tables`(関数)
  - `test_weight_is_clipped_to_three_sd_and_age_zero_uses_the_age_one_row`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.cli`・`shibuya.engine.change_detect`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.foundation.text.templates`・`shibuya.perception.renderer`・`shibuya.world.body.energy`・`shibuya.world.facts.weekly_reader`・`shibuya.world.model.state`
- 決定の ID: D-118・第 291

## [test_env_and_sections_10f.py](../../../../../../tests/engine/test_env_and_sections_10f.py)

10f 第 1 段: 環境の欄(K26 (a)+(1))・manifest の設定と観測の分離(K22 (a))・O75 の見直し・検収の直し(N1〜N9)。

- 公開の関数とクラス
  - `test_config_paths_are_frozen`(関数): 検収 N3 の 3: 設定の節の道筋の一覧を golden で固定(設定 → 観測の黙った付け替えを捕まえる)。
  - `test_env_id_is_the_same_in_the_three_places`(関数): manifest・状態のファイルの見出し・テープの run_meta.json の 3 か所が同じ env_id(同じプロセス)。
  - `test_environment_fields_shape_and_ids`(関数)
  - `test_every_top_level_manifest_field_has_a_section`(関数)
  - `test_git_commands_take_no_optional_locks_and_ignore_untracked`(関数): 検収 N6・N7: すべての git の呼び出しに --no-optional-locks・status は追跡ファイルだけ。
  - `test_git_values_only_when_the_toplevel_is_the_package_root`(関数): 検収 N7: 写しが別のリポの中にあるとき外の commit を拾わない(toplevel が根と違えば空)。
  - `test_golden_tables_are_keyed_by_platform_and_values_unchanged`(関数)
  - `test_missing_git_gives_empty_values_and_keeps_the_fields`(関数)
  - `test_mixed_dict_leaves_are_all_listed_synthetic`(関数): 検収 N3: 混ざった辞書の下の葉はどれも表の子の道筋に当たる(合成世界・全腕・2 日)。
  - `test_mixed_dict_leaves_are_all_listed_world`(関数)
  - `test_o75_split_flow_dir8_and_coherence_are_diag`(関数): O75 の flow_dir8・coherence は src に読み手が無い → O95(diag)。描画が読む flow は O75(behavior)に残る。
  - `test_platform_id_ignores_commit_threads_and_dependency_versions`(関数): golden の行の鍵(platform_id)は commit・dirty・スレッド数・依存の一覧で動かない。env_id は動く(検収 N2)。
  - `test_relations_init_is_observed_with_constant_leaves_as_config`(関数): 検収 N1: 関係の初期化は観測(群の数・候補の対・壁時計は seed で動く)。定数の葉だけ設定。
  - `test_relations_on_5000_seeds_are_exchangeable_and_config_leaves_do_not_move`(関数): 検収 N1・N3 の 2: 関係の初期化が実際に走る構成(mock 5,000 体・記憶+関係)の seed 1/2。
  - `test_removing_a_bit_relevant_field_makes_the_golden_check_loud`(関数): 検収役の再現 a1(platform から cpu を抜く): platform_id が変わり、golden の行の取り出しが警告を出す。
  - `test_replay_of_a_tape_from_another_environment_warns_once`(関数)
  - `test_resume_from_another_environment_warns_once_and_keeps_going`(関数)
  - `test_seed_exchangeability_passes_for_v3_seeds_and_fails_on_a_config_change`(関数): 既定 v3 の seed 1 と 2 は交換可能(観測の欄の差は数えるだけ)。設定の欄を変えると落ちる。
  - `test_seed_exchangeability_sections_mode_on_synthetic_runs`(関数): 合成世界: 観測の欄だけ違う manifest は PASS・設定の欄を変えると FAIL・環境の欄の差は警告だけ。
  - `test_t1_two_processes_write_the_same_env_id_and_final_to_the_files`(関数): T1(検収 N9): 別々のプロセスで 2 回回し、書かれたファイルを読んで比べる。
  - `test_unregistered_environment_warns_and_falls_back_to_aa`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.resume`・`shibuya.engine.run`・`shibuya.engine.state_ledger`・`shibuya.engine.tape`・`shibuya.foundation.hashing`・`shibuya.foundation.manifest.sections`・`shibuya.world.laws.crowd`・`tests/engine/processes/test_rng_scheme_10c.py`・`tests/engine/test_classical_social.py`・`tests/engine/test_presence_derive_v2.py`・`tests/engine/test_presence_executor.py`・`tests/engine/test_relations_tenure.py`・`tests/golden_env.py`・`tests/perception/test_near_tiebreak.py`・`tools/c7/seed_exchangeability.py`
- 決定の ID: 11-01・11-02r/§1・11-02r/§1 #7・11-03/§3・第 330・第 333・第 334・第 346

## [test_familiarity.py](../../../../../../tests/engine/test_familiarity.py)

4 段目(記憶の先行部品=M13 訪問カウンタ+M17 露出カウンタ・親しみの表・第290)。

- 公開の関数とクラス
  - `test_a_full_table_evicts_the_row_with_the_smallest_activation`(関数)
  - `test_activation_reads_the_approximation_and_absent_things`(関数)
  - `test_cli_passes_the_familiarity_flags`(関数)
  - `test_entering_a_cell_counts_once_and_again_after_leaving`(関数)
  - `test_entering_a_cell_exposes_its_signage_once_per_entry`(関数)
  - `test_off_by_default_allocates_nothing_and_writes_nothing`(関数)
  - `test_on_counts_contacts_and_does_not_change_behaviour_on_the_real_world`(関数)
  - `test_resolve_notes_only_the_successful_visits`(関数)
  - `test_the_approximation_versus_the_exact_base_level`(関数)
  - `test_the_entry_gate_draws_the_same_stream_as_the_renderer`(関数)
  - `test_the_render_and_the_entry_of_the_same_signage_count_once_per_tick`(関数)
  - `test_the_renderer_notes_signage_only_when_asked_and_seen`(関数)
  - `test_the_renderer_publishes_the_same_signage_set_it_draws`(関数)
  - `test_the_table_is_k_rows_of_16_bytes_with_empty_rows`(関数)
  - `test_visit_signage_and_place_entries_merge_into_one_row_per_thing`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.cli`・`shibuya.engine.familiarity`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.perception.attention`・`shibuya.perception.renderer`・`shibuya.world.model.state`・`tests/engine/test_intent_hold.py`・`tests/engine/test_move_destination.py`・`tests/engine/test_stage3_small_fixes.py`・`tests/golden_env.py`
- 決定の ID: 第 290・第 330

## [test_fleet_wiring.py](../../../../../../tests/engine/test_fleet_wiring.py)

C6-a 結線の検収テスト(``run_day(fleet=…)``・**プロセス内の偽 vLLM**)。

- 公開の関数とクラス
  - `assert_no_call_is_dropped`(関数): エンジン側の「呼を捨てない」恒等式(憲法1 の監査点)。
  - `fleet_servers`(関数)
  - `make_client`(関数)
  - `make_world`(関数)
  - `run_fleet`(関数): ``fleet_wait_s`` を入れる理由: このテストのエンジンは 1 tick を 1 ms 未満で回すので、
  - `run_mock`(関数)
  - `test_add_fleet_args_defaults_follow_the_canon`(関数): 既定は温度 0.7(知覚契約書 §2.5/運用設計書 §1.3)・max_tokens 96(expedient)。
  - `test_cli_flags_put_temperature_and_max_tokens_on_the_wire`(関数): ``--temperature 0.7 --max-tokens 96`` が payload と run manifest 欄に載る。
  - `test_conversations_need_awake_partners_so_night_only_runs_barely_open_any`(関数): **切り分けの根**: 全員が「会話」と答えても、真夜中(全員 SLEEPING)はほとんど開かない。
  - `test_deferred_calls_are_not_suppressed_by_the_refractory`(関数): 不応期免除が効いていること: 繰り延べ件数がそのまま再投入件数になる。
  - `test_fleet_and_mock_runs_use_the_same_prompts`(関数): 同 seed の艦隊ランと mock ランで**プロンプト(=テープ鍵)が一致**する。
  - `test_fleet_bridge_is_built_with_the_run_vocab_version`(関数): 第214 欠陥修正: ``run_day(vocab_version="v2", fleet=…)`` は**艦隊側の parser にも v2 を渡す**。
  - `test_fleet_conversation_opens_a_session_like_the_mock_path`(関数): (c) の除外: 艦隊経路の「会話」応答も mock 経路と**同じ招待機構**へ入る。
  - `test_fleet_debug_dir_is_off_by_default`(関数)
  - `test_fleet_debug_dir_records_the_first_response_of_failed_parses`(関数): (1) 初回パースが落ちた呼の**初回の生応答**が jsonl に残る(テープ形式は不変)。
  - `test_fleet_from_args_passes_queue_capacity_through`(関数): CLI の ``--fleet-queue-capacity`` が FleetConfig.queue_capacity に届く。0/未指定は既定(×4)。
  - `test_fleet_run_conserves_money_and_accounts_every_call`(関数)
  - `test_fleet_run_pushes_cache_salt_into_the_run_manifest`(関数)
  - `test_fleet_run_records_the_real_responses_to_the_tape`(関数)
  - `test_mock_path_is_deterministic_and_carries_no_fleet_state`(関数): ``fleet=None``(既定)は従来経路: **同 seed の 2 回**で checkpoint ハッシュ列が一致し、
  - `test_mock_path_opens_conversations_in_the_same_world`(関数): 対照: 同じ世界・同じ台本を mock 経路(scripted client)で流しても同じ機構に入る。
  - `test_movement_cpu_time_is_recorded_alongside_wall_time`(関数): (3) movement 区間の**スレッド CPU 時間**が壁時計と並んで出る(GIL 待ちの切り分け)。
  - `test_phase_breakdown_separates_fleet_wait`(関数): (3) 要約に位相別 ms/tick が出る。``fleet_wait`` は ``llm`` と別勘定。
  - `test_queue_full_defers_and_is_reinjected`(関数): キュー満杯(非ブロッキング却下)も繰り延べ → 再投入され、呼は消えない。
  - `test_run_reports_dictionary_mapped_rate`(関数): 語彙外の行動語は段0 の辞書で救い、要約行の辞書写像率に出る。
  - `test_run_reports_effective_and_strict_format_error_rates`(関数): ラベル別名は**実効 0 / 厳密 >0**。要約行に両方が出る。
  - `test_tape_analysis_reads_a_fleet_tape`(関数): (2) テープ解析スクリプトが艦隊テープを読めて、会話の切り分け欄を出す。
  - `test_timeout_defers_then_reinjects_and_is_finally_answered`(関数): タイムアウト注入 → 繰り延べ → 次 tick 再投入(不応期免除)→ 最終的に処理される。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.engine.systems.build`・`shibuya.engine.tape`・`shibuya.foundation.hashing`・`shibuya.foundation.manifest.schema`・`shibuya.foundation.time_consts`・`shibuya.llm`・`shibuya.llm.fleet`・`shibuya.world.model.state`・`tests/engine/tape_analysis.py`・`tests/engine/time/__init__.py`・`tests/llm/test_fleet.py`
- 読む試験: `tests/engine/test_response_delay.py`・`tests/engine/test_resume_10d.py`・`tests/engine/time/test_v30a_key_sites.py`
- CLI の引数
  - `--seed`
- 決定の ID: 11-03・11-03/§3・D-56・D-58・第 214

## [test_geometry_c9.py](../../../../../../tests/engine/test_geometry_c9.py)

C9 位置幾何(``engine.geometry``)の検収。

- 公開の関数とクラス
  - `BoomLLM`(クラス): 再生モードで**呼ばれたら落ちる** LLM(テープ外 0 の陽性対照)。
  - `edge_run`(関数)
  - `synthetic_world`(関数)
  - `test_arrival_is_detected_when_s_reaches_the_target_node`(関数)
  - `test_bad_geometry_is_rejected_before_anything_is_built`(関数)
  - `test_density_stage_edges_are_the_fruin_los_boundaries`(関数): edge 幾何の段は **Fruin LOS**(人/m²)。``perception`` 側の表と 1 対 1(二重定義の検査)。
  - `test_density_stage_uses_people_per_square_metre_in_edge_mode`(関数): edge では段が Fruin LOS(人/m²)。node の段(人/セル)とは別物。
  - `test_desired_speeds_are_deterministic_and_scale_invariant`(関数): T4: 体数を増やしても既存個体の値が動かない(``core.rng`` の列を引かない)。
  - `test_desired_speeds_are_inside_the_bosina_weidmann_band`(関数)
  - `test_edge_mode_changes_the_run_and_records_the_arm`(関数)
  - `test_edge_mode_is_deterministic_across_two_runs`(関数)
  - `test_edge_tape_replays_bit_for_bit`(関数): T2-c: edge モードで録ったテープの再生が checkpoint 列まで一致・テープ外 0。
  - `test_engine_step_writes_unreachable_end_to_end_in_edge_mode`(関数): ``resolve.apply`` まで通して ``ResultCode.UNREACHABLE`` が立つ(next_hop を塞ぐ)。
  - `test_explicit_node_geometry_is_byte_identical_to_the_default`(関数)
  - `test_geometry_modes_and_default`(関数)
  - `test_kladek_constants_match_the_lit_note`(関数): Kretz 2015 §2 式 (7)(8)(9) の 3 値。
  - `test_kladek_curve_reproduces_the_recomputed_values`(関数): lit メモ **[再計算]** の v(ρ)(v0=1.34 m/s)を 3 桁で再現する。
  - `test_mix64_matches_the_presence_definition`(関数): ``geometry._mix64`` は ``presence``/``build.sched`` と**同じ式**(三重定義の機械検査)。
  - `test_node_mode_declares_no_extra_columns`(関数): 既定(node)は ``edge_id``/``edge_s`` を確保しない=``state_hash`` が動かない。
  - `test_one_tick_distance_at_fruin_los_f_is_about_one_fifth`(関数): ρ=3.33 人/m²(C7 実測の最混雑)→ 係数 0.198 ≒ **0.2 v**(lit メモの再計算)。
  - `test_one_tick_distance_at_zero_density_is_v_times_60`(関数): 密度 0 → 1 tick の移動距離 = ``v_desired × 60 s``(減速なし)。
  - `test_p2_declaration_has_the_400k_row`(関数): 予算宣言表 P2 に **40 万体の行**(G9 ≤300 ms/tick)が書かれている。
  - `test_p2_edge_geometry_under_300ms_at_400k_agents`(関数): 予算行 P2(G9 delta 2026-09-17): **40 万体で ≤300 ms/tick**。
  - `test_p2_scaled_down_runs_in_ci`(関数): CI 用の縮小版(4 万体・合成 453 セル)。絶対値ゲート(40 万体)は slow 側。
  - `test_position_columns_still_fit_the_m2_budget`(関数): M2(位置・運動・身体)≤128 B/体 に辺上の 2 欄を足しても収まる。
  - `test_positions_interpolate_between_the_two_end_nodes`(関数)
  - `test_result_codes_for_c9_exist_and_are_appended_at_the_end`(関数): G11: ``UNREACHABLE``(既存)と ``TARGET_GONE``(新設・末尾追加)。
  - `test_target_gone_is_written_and_rendered_like_any_other_failure`(関数): ``_fail`` に載る=描画まで通る(**発生させる側は C9b の領分**=ここでは口だけ検査)。
  - `test_unreachable_is_raised_when_the_next_hop_table_has_no_path`(関数): 次ホップが引けない体は ``stuck``(``resolve`` が ``UNREACHABLE`` を書く)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.commit`・`shibuya.engine.presence`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.foundation.budget`・`shibuya.foundation.text.templates`・`shibuya.perception.renderer`・`shibuya.world.assets`・`shibuya.world.model.geometry`・`shibuya.world.model.state`・`tests/_time_gates.py`・`tests/engine/time/__init__.py`
- 決定の ID: 第 288

## [test_intent_chooser.py](../../../../../../tests/engine/test_intent_chooser.py)

段 2a(D-114 (a)): 選択器の口 ``Chooser.probs``・候補の絞り込み・落選の理由・manifest。

- 公開の関数とクラス
  - `test_buyable_cats_are_the_shop_like_cats_q12`(関数): 親決定 Q12: 購入/並ぶの候補=店舗系 cat だけ(学校・事務所・教会などでの購入を消す)。
  - `test_category_filters_by_w6_cat_and_bad_target_when_nothing_matches`(関数)
  - `test_category_table_uses_known_w6_values_only`(関数)
  - `test_classify_order_category_word_before_names`(関数)
  - `test_draw_is_deterministic_and_follows_the_distribution`(関数)
  - `test_eat_candidates_are_eateries_and_other_reasons_are_split`(関数)
  - `test_entropy_and_names`(関数)
  - `test_generic_words_read_as_none_q11`(関数): 対応表 v0(Q11): 「店」「店舗」「ショップ」「お店」は なし(「〇〇ショップ」の名指しにしない)。
  - `test_named_in_cell_is_the_only_candidate_and_out_of_cell_fails`(関数)
  - `test_nearest_chooser_is_a_chooser_and_returns_a_one_hot_distribution`(関数)
  - `test_nearest_order_is_distance_then_visibility_then_poi_index`(関数)
  - `test_none_skips_the_closed_lowest_id_and_picks_the_most_visible_open_poi`(関数)
  - `test_poi_target_switch_is_removed_q13`(関数): 〔第 4 期 4-3 版上げ 3 回目の第 2 部〕親決定 Q13 の切替口 ``--poi-target legacy``(段 2a 前の現在セルの最小 id=旧
  - `test_poi_visibility_is_read_from_w8_on_the_real_world`(関数)
  - `test_run_day_records_chooser_and_target_resolution_in_the_manifest`(関数)
  - `test_the_representative_targets_produce_the_split_result_codes`(関数): 候補 0 の代表(閉店/在庫切れ)と -1 が、resolve の既存の判定で理由どおりの結果コードになる。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.build.geo.poi_class`・`shibuya.cli`・`shibuya.engine.chooser`・`shibuya.engine.poi_target`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.foundation.vocab.actions`・`shibuya.world.assets`・`shibuya.world.model.state`
- 決定の ID: D-114・D-119・第 288

## [test_intent_hold.py](../../../../../../tests/engine/test_intent_hold.py)

段 2c(意図の保持・D-112 ①・D-114 案 A・第288): 欄・立つ条件・着いたら実行・失敗と TOO_FAR・計画で捨てる・CELL_BLOCK の抑止・B5 の 1 行・manifest・mock の口・Q18(人 → その人のセル)・親決定 Q20(なし/待機/同じ行き先の移動は意図と歩みを保つ)・Q21(名指しの店の営業中を立てる時点で見る)・Q22(計画就寝の意図と排他)。

- 公開の関数とクラス
  - `test_a_move_to_the_same_destination_keeps_and_a_different_one_supersedes_q20`(関数)
  - `test_a_none_response_of_an_arrived_agent_is_dropped_and_the_intent_executes_q20`(関数)
  - `test_a_world_touching_response_supersedes_the_intent`(関数)
  - `test_b5_intent_line_only_for_holders_within_15_tokens`(関数)
  - `test_bed_intent_is_exclusive_with_the_planned_sleep_q22`(関数)
  - `test_buyers_beyond_the_shelf_fail_before_paying_so_money_is_conserved`(関数): 満席の列の捌きが棚 1 個の店へ同じ tick に 2 人を入れると、2 人目は支払いだけ済んで品が出ず
  - `test_commit_turns_out_of_cell_targets_into_moves_and_proposes_the_intent`(関数)
  - `test_failure_on_arrival_writes_the_code_and_the_fail_immediate_rule_holds`(関数)
  - `test_intent_actions_and_the_renderer_words_match_the_contract`(関数)
  - `test_intent_fields_are_allocated_by_default_with_none_values_and_ten_bytes`(関数)
  - `test_intent_is_set_walks_arrives_and_executes_without_an_llm_call`(関数)
  - `test_manifest_intent_and_the_layer_is_off_outside_v3_activity_candidates`(関数)
  - `test_mock_arm_sets_arrives_and_executes_intents_on_the_real_world`(関数)
  - `test_mock_out_of_cell_knob_is_off_by_default_and_prefers_names_in_brackets`(関数)
  - `test_move_to_a_person_goes_to_that_persons_cell_q18`(関数)
  - `test_named_visible_but_closed_returns_closed_now_without_walking_q21`(関数): 親決定 Q21: 立てる時点で営業中・在庫を見る。閉店なら歩かずに CLOSED を即時に。
  - `test_no_route_at_set_time_is_unreachable_with_the_intended_action_as_subject`(関数)
  - `test_none_and_wait_keep_the_intent_and_the_walk_q20`(関数): 親決定 Q20: なし(と 待機)は「新しい行為が無い」=意図を上書きせず歩みも止めない。
  - `test_plan_boundary_depart_and_sleep_drop_the_intent`(関数)
  - `test_resolver_category_without_an_open_candidate_in_the_cell_searches_nearby`(関数)
  - `test_resolver_named_out_of_cell_becomes_an_intent_only_when_visible_and_fit`(関数)
  - `test_resolver_without_intent_out_is_unchanged`(関数)
  - `test_suppress_wakes_drops_cell_block_and_expiry_only_for_holders`(関数)
  - `test_too_far_is_a_new_code_with_text_and_options`(関数)
  - `test_too_far_stops_the_walk_and_writes_the_new_code`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.cli`・`shibuya.engine.activity`・`shibuya.engine.chooser`・`shibuya.engine.commit`・`shibuya.engine.intent`・`shibuya.engine.poi_target`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.foundation.vocab.actions`・`shibuya.llm`・`shibuya.llm.mock`・`shibuya.perception.renderer`・`shibuya.world.facts.mock_schedule`・`tests/engine/test_move_destination.py`
- 読む試験: `tests/engine/test_familiarity.py`・`tests/engine/test_stage3_small_fixes.py`
- 決定の ID: D-112・D-114・第 288

## [test_intent_mode_open.py](../../../../../../tests/engine/test_intent_mode_open.py)

AB7 自由意図の腕の切替口 — エンジン側(``docs/design/v2-open-intent-arm-spec.md`` §4 (c))。

- 公開の関数とクラス
  - `WordLLM`(クラス): 常に同じ行動語(表層形)を返す台本 mock(``test_undefined_action.WordLLM`` と同じ)。
  - `test_default_is_vocab_and_the_mock_actions_do_not_move`(関数): 既定は vocab。mock は本文を読まないので open/hint 腕でも checkpoint・呼数は同じ。
  - `test_intent_mode_round_trips_into_the_run_manifest`(関数)
  - `test_role_words_default_on_and_round_trips_into_the_run_manifest`(関数): ランの既定は役割語あり(契約書 §2.2)。off は第268 以前の B0(prompt_hash が違う)。
  - `test_stage0_dictionary_works_in_both_intent_modes`(関数): 語彙を見せない腕でも、語彙外の表層は段0 辞書でエンジンの行動コードになる。
  - `test_stage1_records_the_word_in_both_intent_modes`(関数): 段0 で写せない語は、どちらの腕でも段1(記録+待機)に落ちる。
  - `test_unknown_intent_mode_is_refused`(関数)
- import している内部モジュール: `shibuya.engine.run`・`shibuya.foundation.text.templates`・`shibuya.foundation.vocab.actions`・`shibuya.llm`・`shibuya.llm.undefined`
- 決定の ID: D-56・D-113・第 268・第 269

## [test_l4_budget.py](../../../../../../tests/engine/test_l4_budget.py)

予算行 **L4**(上限 400 万呼/日 = 憲法1の監査点)の硬い上限。

- 公開の関数とクラス
  - `test_a_tick_never_exceeds_the_floor_of_the_budget`(関数)
  - `test_conversation_keeps_priority_inside_the_hard_cap`(関数): 会話ターンは固定優先の先頭=上限が効いても最優先で通る(設計どおり呼の 45%)。
  - `test_degraded_calls_no_longer_double_the_budget`(関数)
  - `test_real_world_run_stays_within_the_l4_cap`(関数)
  - `test_synthetic_run_stays_within_the_l4_cap`(関数)
  - `test_the_daily_sum_never_exceeds_the_budget_times_ticks`(関数): 端数を繰り越しても Σ呼 ≤ Σ予算(繰越の在庫は 2 tick ぶんで頭打ち)。
- import している内部モジュール: `shibuya.engine.arbiter`・`shibuya.engine.run`・`shibuya.foundation.types`・`shibuya.world.model.state`

## [test_ledger_wiring.py](../../../../../../tests/engine/test_ledger_wiring.py)

台帳(U11 金・U-Goods 物)を resolve/run へ結線したときのテスト。

- 公開の関数とクラス
  - `test_census_gate_passes_for_a_wired_day`(関数): 日次センサスは**締めた日**(day 0)を評価する。
  - `test_check_two_holds_after_the_run`(関数)
  - `test_check_two_holds_at_every_checkpoint`(関数): 検算②(主検算)は**毎期**成立する(§2.3)——手回しの tick ループで確認する。
  - `test_collect_waste_through_resolve`(関数)
  - `test_conservation_over_all_sectors_including_row`(関数): 外界を含む全部門の現金合計は 0 のまま(初期財布も transfer で入れるため)。
  - `test_consume_moves_holdings_into_the_sink`(関数): 消費は世帯の所持を減らし SKU 別 sink に落ちる(検算①は閉じたまま)。
  - `test_goods_processes_change_the_world`(関数): 逆向き: 物の過程を入れると棚が動く(=台帳の有無が世界を変える・C4 後半)。
  - `test_o_t_logs_of_both_ledgers_are_measured`(関数): D-R2-6: 台帳の O(t) ログ(取引ログ・納品ログ)が成長ゲートの実測に載る。
  - `test_purchases_are_booked_as_consumption`(関数)
  - `test_restock_requires_a_goods_ledger`(関数)
  - `test_restock_through_resolve_pays_and_updates_the_mirror`(関数): 補充は resolve 経由で ``world.pois.stock``(写し)を更新し、域外仕入を計上する。
  - `test_run_result_census_row_is_the_closed_day`(関数): ``RunResult.census_row`` = 締めた日の行(faucet/sink/廃棄が実数)。
  - `test_the_bundle_declaration_survives_the_c7_scale`(関数): D-53: **本番規模(390,067 体)でも宣言だけで cap を超えない**(ランは要らない)。
  - `test_two_wired_runs_are_identical`(関数)
  - `test_w2_five_thousand_agents_with_the_ledger_wired`(関数): W2: 台帳を結線しても 1 シミュ日の壁時計が予算内(報告値つき)。
  - `test_wiring_does_not_change_the_state_hashes_when_goods_processes_are_off`(関数): 物の過程を切れば、台帳を注入しても checkpoint ハッシュは同じ(帳簿を足すだけ)。
  - `test_world_stock_is_a_mirror_of_the_shelf`(関数): ``world.pois.stock`` は棚(SKU 別)の写し。真値は物の台帳にある。
  - `wired`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.economy.accounts`・`shibuya.economy.census`・`shibuya.economy.checks`・`shibuya.economy.goods`・`shibuya.economy.ledger`・`shibuya.engine.commit`・`shibuya.engine.economy_stage2`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.foundation.growth`・`shibuya.foundation.ports.ledger`・`shibuya.world.facts.mock_schedule`・`shibuya.world.model.state`・`tests/_time_gates.py`・`tests/engine/time/__init__.py`・`tests/golden_env.py`
- 決定の ID: 11-01・D-53・D-56・第 330

## [test_llm_mock.py](../../../../../../tests/engine/test_llm_mock.py)

llm.mock のテスト(2行形・決定論・テープ再生)。

- 公開の関数とクラス
  - `test_mock_counts_calls_and_estimates_tokens`(関数)
  - `test_mock_is_deterministic_and_scale_invariant`(関数): 同じ (seed, tick, agent, class) は常に同じ応答=カウンタベース(T4)。
  - `test_mock_needs_no_network`(関数): mock は socket を一切触らない(W2「呼び出しコストゼロ級」の担保)。
  - `test_mock_output_is_two_line_form`(関数)
  - `test_mock_uses_targets_when_given`(関数)
  - `test_property_always_two_line_and_in_vocab`(関数)
  - `test_request_hashes_are_deterministic_and_field_sensitive`(関数)
  - `test_tape_llm_does_not_fall_back_to_mock`(関数): テープ外は必ず失敗する(黙って実LLM/mock へ落とさない=運用設計書 §2.5)。
  - `test_tape_llm_rejects_non_lookup_object`(関数)
  - `test_tape_llm_replays_recorded_mock_answers`(関数): mock で録って TapeLLM で再生 → 完全一致(bit 再現の最小単位)。
  - `test_vocab_is_the_12_words_of_the_action_contract`(関数)
- import している内部モジュール: `shibuya.engine.tape`・`shibuya.foundation.vocab.actions`・`shibuya.llm`

## [test_meal_bundle_2b.py](../../../../../../tests/engine/test_meal_bundle_2b.py)

第2波 §2B: 食事の束の 3 項(切替口つき・既定は旧のまま=指示書 §8-2)。

- 公開の関数とクラス
  - `model`(関数)
  - `run_out_of_area`(関数): 全 tick で ``due_with_deferred`` を引き、食べた ``(体, tick, 時間帯, 行由来, 遅らせた)`` を返す。
  - `test_all_draws_the_four_words_and_hungry_is_the_old_rule`(関数)
  - `test_all_keeps_the_individual_blocks_within_budget`(関数): all で 1,000 描画: 個体の群(B5+B6)が 300 tok 以内・各ブロックも予算内(B0 は既知の超過)。
  - `test_breakfast_window_edge_is_fixed`(関数): 窓は [5:00, 11:00): 10:59 に起床 → 10:59 に朝食・11:00 に起床 → 朝食なし。
  - `test_cli_has_the_three_switches_with_old_defaults`(関数)
  - `test_consecutive_sleep_rows_are_read_as_one_sleep`(関数): 就寝 0:00〜7:40 と 7:40〜8:20 の 2 本: 既定の朝食の時刻 は 1 本目の中 → 連鎖して 8:20 に起床(つながないと 7:40)。
  - `test_home_meal_eats_only_at_home_and_awake_once_per_row`(関数)
  - `test_home_meal_itself_adds_no_interoception_wake`(関数): 自宅の食事は hunger_stage も合わせる=内受容の下げ跨ぎ(起床)を作らない。店の食事の口は作る(対照)。
  - `test_home_meal_moves_no_money_or_goods_only_the_four_energy_fields`(関数): 予定の実行は金と物を動かさない=書き換える欄は since_meal・収支・hunger・hunger_stage の 4 本だけ。
  - `test_home_meal_needs_a_valid_mode`(関数)
  - `test_home_meal_rows_are_only_meal_at_home_with_home_in_area`(関数)
  - `test_hungry_keeps_the_reference_scene_prompt_hash_and_all_moves_only_below_hungry`(関数)
  - `test_invariants_awake_inside_window_and_once_per_slot`(関数): on のとき: 食事はどれも W17 で起きている時刻・遅らせた食事は窓の中・同じ時間帯に 2 回食べない。
  - `test_only_bodies_out_of_area_at_the_default_time_are_deferred`(関数): 遅らせるのは既定の時刻に域外に居た体だけ(旧で食事が置かれた体)・起床時に範囲内なら食べない。
  - `test_run_wiring_defaults_are_old_and_switches_reach_the_run`(関数)
  - `test_sleep_defer_off_is_the_old_schedule`(関数)
  - `test_sleep_defer_on_moves_the_breakfast_to_the_wake_time_inside_the_window`(関数)
  - `test_template_fingerprint_follows_the_drawn_hunger_stage`(関数): all の腕は描画に使った段の下限 0 で文面の指紋を計算する。既定(hungry)と v1 のランは凍結値のまま。
  - `test_three_meal_day_still_closes_to_zero_with_deferred_breakfast`(関数): 範囲外の体は METs=基準日の平均 → 1 日の消費=EER。3 食(比の和 1.0)なら収支 0。遅らせても同じ。
  - `test_w17_wake_minute_reads_the_sleep_row_and_chains_consecutive_rows`(関数)
  - `weekly`(関数): ``(体, 開始分, 終了分, 活動, 場所)`` の行 → 月曜(day 0)だけの週次表。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.cli`・`shibuya.engine.change_detect`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.foundation.text.templates`・`shibuya.perception.renderer`・`shibuya.world.body.energy`・`shibuya.world.facts.weekly_reader`・`shibuya.world.model.state`

## [test_meal_gate_per_hour.py](../../../../../../tests/engine/test_meal_gate_per_hour.py)

第2波 §2A 項 4: 古典の腕の**食事の門を時間あたりに**(Q48 (a)・指示書 §0-2・§8-2)のテスト。

- 公開の関数とクラス
  - `test_a_meal_resets_the_hazard_but_a_snack_does_not`(関数): (a) 空腹で 60 分積んだ後に自宅の食事(予定の実行)→ H=0(次の門は 0 から)。飲食店・範囲外の食事も同じ
  - `test_b_a_full_body_at_the_gate_gets_zero_and_the_hazard_is_cleared`(関数): (b) 空腹で 60 分積んだ後、評価の時点で満腹 → p=0・H=0。
  - `test_default_is_per_wake_and_the_switch_is_on_the_cli`(関数)
  - `test_doubling_the_wake_frequency_keeps_the_expected_meals`(関数): 起床 20 分ごと → 10 分ごと。per_hour: 1 日の食事の回数の期待値の差 < 3%(残りは門を引く時刻の離散化=
  - `test_e_no_gate_pass_while_full_in_a_real_per_hour_run`(関数): (e) 実資産の classical per_hour のラン(1,500 体)で満腹の段で門を通った回数が 0(5,000 体は記録の計測)。
  - `test_hazard_rule_keeps_expected_meals_when_waking_twice_as_often`(関数): (vi) 起床 20 分ごと → 10 分ごと: 1 日の食事の回数の期待値の差 < 3%(20,000 体)。
  - `test_one_minute_sixty_times_equals_one_hour_once`(関数)
  - `test_policy_hazard_accrual_by_the_word_stage_of_each_minute`(関数): 第2波 §2B の親の決定(ハザードの積算): H += −ln(1 − p_h(その tick の段)) × 分/60・門で 1 − exp(−H)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.cli`・`shibuya.engine.classical`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.world.body.energy`・`shibuya.world.model.state`

## [test_memory_recall.py](../../../../../../tests/engine/test_memory_recall.py)

記憶 第 1 段 6b: **想起**(記憶アジェンダ v1 M4・M5・M6・M11・M15・M16・修正 2・修正 4・第295)のテスト。

- 公開の関数とクラス
  - `build`(関数)
  - `fmt`(関数)
  - `item`(関数)
  - `put`(関数)
  - `runs`(関数)
  - `table`(関数)
  - `test_a_v2_tape_reads_recalled_rows_as_empty`(関数)
  - `test_abbreviation_words_fall_back_to_the_cell_id_and_drop_the_gist`(関数): ⑥ 省略記法: POI 名に禁止語 → その行のセルの ID・要旨に禁止語 → 要旨を載せない(宣言)。
  - `test_id_match_comes_first_and_the_rest_is_filled_by_score`(関数)
  - `test_item_templates`(関数)
  - `test_k2_and_k5_instruments_are_in_the_manifest`(関数)
  - `test_k5_counts_revisits_after_a_failure_and_k2_counts_repeats`(関数)
  - `test_k_is_three_for_conversation_and_two_otherwise`(関数)
  - `test_memory_line_is_the_last_line_of_b5`(関数)
  - `test_memory_tau_is_passed_and_checked`(関数)
  - `test_off_and_zero_recall_render_exactly_as_before`(関数)
  - `test_one_item_is_capped_at_20_tokens`(関数)
  - `test_partner_object_place_and_last_result_are_query_keys`(関数)
  - `test_recall_has_no_loop_over_rows`(関数): P4: 想起は行の走査を配列演算で行う(for は想起した ≤k 件だけ)。
  - `test_recall_items_carry_the_gist`(関数)
  - `test_run_on_puts_memory_lines_and_mock_behavior_is_unchanged`(関数)
  - `test_tape_v3_writes_recalled_rows_and_keeps_the_v2_columns_in_place`(関数)
  - `test_tau_cuts_old_rows`(関数)
  - `test_the_channel_keeps_the_whole_line_within_60_tokens`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.commit`・`shibuya.engine.familiarity`・`shibuya.engine.memory`・`shibuya.engine.run`・`shibuya.engine.tape`・`shibuya.foundation.text.channels`・`shibuya.foundation.text.normalize`・`shibuya.foundation.text.templates`・`shibuya.perception.renderer`・`shibuya.world.model.state`・`tests/golden_env.py`
- 決定の ID: 第 295・第 330

## [test_memory_record.py](../../../../../../tests/engine/test_memory_record.py)

6 段目 6a: 記憶 第 1 段の**記録**(D-95・記憶アジェンダ v1 M1〜M4・修正 1・第294)のテスト。

- 公開の関数とクラス
  - `one`(関数)
  - `table`(関数)
  - `test_action_outcomes_use_last_action_and_the_applied_targets`(関数)
  - `test_activation_and_scores_and_top`(関数)
  - `test_arrivals_conversations_noticed_and_signage`(関数)
  - `test_cli_flags`(関数)
  - `test_full_table_evicts_the_lowest_score_row_and_its_gist`(関数)
  - `test_gist_falls_back_to_the_reason_field_in_vocab_v3`(関数): 第294 Q57(親の暫定): ひと言が空/「なし」なら理由欄の先頭 40 字を要旨にする。
  - `test_gists_are_capped_per_agent`(関数)
  - `test_importance_table`(関数)
  - `test_memory_columns_only_in_the_arm_and_declare_32_bytes_per_row`(関数)
  - `test_merged_rows_return_importance_to_base`(関数): 第294 Q56: 同じ鍵の反復(統合)は「初回 +1」を外して base に戻す。新しい行だけ +1。
  - `test_row_writers_are_array_ops`(関数): P4: 1 回の書き込み(統合/新規/追い出し)と読み口に for/while を書かない。
  - `test_run_default_is_off_and_memory_on_keeps_mock_behavior`(関数)
  - `test_same_key_merges_and_keeps_the_first_tick`(関数)
  - `test_several_events_for_one_agent_in_one_tick_get_distinct_rows`(関数)
  - `test_signage_first_sight_is_judged_by_the_memory_table_even_with_familiarity`(関数): 第294 Q58: 初見は記憶の表で判定(描画による露出=意識的な初見)。親しみの表の「入った回」は使わない。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.commit`・`shibuya.engine.familiarity`・`shibuya.engine.memory`・`shibuya.engine.run`・`tests/golden_env.py`
- 決定の ID: D-95・第 294・第 330

## [test_mock_day_w2.py](../../../../../../tests/engine/test_mock_day_w2.py)

1 シミュ日 mock ランのテスト: **W2**(≤10分)・**P2**(≤5ms/frame)・保存則・診断行・成長宣言。

- 公開の関数とクラス
  - `small_run`(関数)
  - `test_agents_end_in_valid_states`(関数)
  - `test_cli_can_emit_the_growth_yaml`(関数)
  - `test_cli_runs_and_falls_back_to_a_synthetic_world`(関数)
  - `test_conservation_of_money_and_revenue`(関数): 保存則: Σ所持金 + Σ売上 が 1 日を通して不変・在庫は非負。
  - `test_diagnostics_table_has_the_four_required_columns`(関数): T9: 診断行4列(繰り延べ/昇格/縮退/抑止)が全ランに存在する。
  - `test_engine_actually_moves_and_wakes`(関数)
  - `test_no_undefined_actions_from_the_mock`(関数): MockLLM は必ず 2 行形を返す(B11 実測=書式順守 1.000 の再現)。
  - `test_o_t_logs_are_measured_not_just_the_engine_buffers`(関数): 層2レビュー指摘: D-R2-6 が名指しした O(t) ログ本体を実測に載せる。
  - `test_p2_movement_and_density_under_5ms_at_5000_agents`(関数)
  - `test_state_growth_declaration_passes`(関数): D-R2-6: 24step→1日/30日 外挿が予算 M 行の内側。
  - `test_state_stays_frozen_outside_resolve`(関数)
  - `test_w2_five_thousand_agents_one_sim_day_under_ten_minutes`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.growth_decl`・`shibuya.engine.run`・`shibuya.foundation.queues.scheduler`・`tests/_time_gates.py`

## [test_move_destination.py](../../../../../../tests/engine/test_move_destination.py)

段 2b(行き先を対象欄から・D-112 ②): 移動の対象欄の解決順・近傍探索の上限・落選の分け・manifest。

- 公開の関数とクラス
  - `test_bad_target_and_unreachable_are_counted_separately`(関数)
  - `test_category_order_in_cell_then_visible_then_nearby_within_the_radius`(関数)
  - `test_cell_id_including_the_cell_prefix_and_unknown_cells`(関数)
  - `test_commit_uses_the_target_field_but_keeps_explicit_hints_and_wander`(関数)
  - `test_mock_move_target_knob_is_off_by_default_and_uses_words_or_visible_names`(関数)
  - `test_named_prefers_the_instance_in_the_current_cell_else_the_nearest`(関数)
  - `test_none_and_explanations_keep_the_default_and_offmap_agents_are_untouched`(関数)
  - `test_run_day_records_move_resolution_in_the_manifest`(関数)
  - `test_the_nearby_search_stops_at_the_radius_and_fails_as_bad_target`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.chooser`・`shibuya.engine.commit`・`shibuya.engine.poi_target`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.foundation.vocab.actions`・`shibuya.llm`・`shibuya.llm.mock`・`shibuya.world.model.state`
- 読む試験: `tests/engine/test_familiarity.py`・`tests/engine/test_intent_hold.py`・`tests/engine/test_stage3_small_fixes.py`
- 決定の ID: D-112・第 288

## [test_norm_meter.py](../../../../../../tests/engine/test_norm_meter.py)

第308 D-107 (a): 群・規範の計器(``engine.norm_meter``)。**読むだけ**=ランの状態を変えない。

- 公開の関数とクラス
  - `meter`(関数)
  - `test_context_entropy_counts_actions_by_place_and_hour`(関数)
  - `test_cowalk_needs_same_cell_same_target_within_2m_for_5_minutes`(関数)
  - `test_cowalk_run_resets_when_the_pair_breaks`(関数)
  - `test_entropy_bits_matches_the_d68_formula`(関数)
  - `test_group_norms_switch_off_is_byte_identical`(関数): 第309 Q150: ``group_norms="off"`` は計器の口を通さない=final・呼数が既定(on)と同じ・manifest は enabled=False。
  - `test_instant_group_walk_counts_neighbours_across_grid_cells_and_ignores_standing_agents`(関数)
  - `test_instant_group_walk_needs_2m_same_direction_and_both_walking`(関数)
  - `test_role_words_count_results_and_no_permission`(関数)
  - `test_summary_declares_convention_not_norm_and_does_not_judge`(関数)
  - `test_the_meter_only_reads_the_run_state`(関数): 計器を空にしたランと final・呼数が一致する=**読むだけ**(状態・乱数・テープに触れない)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.cli`・`shibuya.engine.norm_meter`・`shibuya.engine.run`・`shibuya.world.model.state`
- 決定の ID: D-107・第 308・第 309

## [test_parser_contract.py](../../../../../../tests/engine/test_parser_contract.py)

行動契約表とエンジンの**突合**(層をまたぐ検査)。

- 公開の関数とクラス
  - `test_contract_tags_are_declared_for_every_row`(関数)
  - `test_engine_action_codes_come_from_the_contract`(関数)
  - `test_failure_codes_exist_in_result_code`(関数): 契約表の失敗コード名は ``ResultCode`` に**実在**する(層をまたぐ文字列参照の検査)。
  - `test_parse_action_delegates_to_the_canonical_parser`(関数): C2 の最小写像では読めなかった形(行内分割・箇条書き)も読める=委譲の証拠。
  - `test_parse_action_returns_undefined_for_non_contract_output`(関数)
  - `test_parse_action_round_trips_every_contract_word`(関数)
  - `test_resolve_has_one_branch_per_contract_word`(関数): 12 語 + エンジン継続 = 13 分岐(``engine.resolve._APPLY``)。
  - `test_result_code_covers_the_never_fails_rule`(関数): §2 共通必須事項③「失敗しない行動が常に1つ以上(待機)」。
  - `test_role_words_are_parsed_but_are_not_engine_intents_yet`(関数): 役割語はパーサが読む(全員に見せる)が、``_APPLY`` に分岐が無いので未定義扱いに落とす。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.commit`・`shibuya.engine.resolve`・`shibuya.foundation.vocab.actions`・`shibuya.llm.parser`

## [test_plan_sleep_d62.py](../../../../../../tests/engine/test_plan_sleep_d62.py)

D-62「就寝は計画の実行」(ユーザー決定 (a)+(b)・2026-09-10)のテスト。

- 公開の関数とクラス
  - `test_activity_to_state_covers_the_vocabulary`(関数)
  - `test_boundary_events_full_agrees_with_boundary_events`(関数): ``boundary_events`` は ``boundary_events_full`` の薄い包み(並びが一致)。
  - `test_choosing_another_action_drops_the_sleep_intent`(関数): 就寝地へ歩いている途中で別の行動を選んだら意図は落ちる(幽霊を残さない)。
  - `test_initial_activity_reflects_the_plan_at_midnight`(関数): 0:00 の活動が ``Activity`` に写る(就寝 / 勤務 / 移動 の 3 例)。
  - `test_salient_wake_is_still_exempt_while_asleep`(関数): D-56 の例外(顕著行為は寝ていても起こす)は D-62 の後も生きている。
  - `test_same_seed_gives_the_same_run`(関数)
  - `test_set_initial_activity_keeps_the_rail_preassignment`(関数): 域外滞在・乗車中(``transit_state != 0``)は書き換えない(rail の事前割当が正)。
  - `test_sleep_boundary_makes_no_call_and_wake_boundary_does`(関数): 1 日ラン: 就寝境界の tick では呼が出ず、起床境界の tick では出る(mock 日課)。
  - `test_sleep_boundary_puts_the_agent_to_bed_without_an_llm_call`(関数): 就寝地に居る個体は境界でそのまま ``SLEEPING``(呼は要らない)。
  - `test_sleep_boundary_skips_riding_conversing_and_already_sleeping`(関数): 乗車中・域外滞在・会話中・就寝済は触らない(理由が計数に出る)。
  - `test_sleep_boundary_walks_home_and_sleeps_on_arrival`(関数): 就寝地に居ない個体は歩き出し(``sleep_pending``)、着いた tick に寝る。
  - `test_synthetic_world_still_starts_with_everyone_asleep`(関数): 週次表の無いランは tick 0 で全員 ``SLEEPING``(D-62 前と同じ=帰無の担保)。
  - `test_wake_from_plan_wakes_only_sleepers`(関数): 非就寝の計画境界は ``SLEEPING`` を ``IDLE`` に戻し、就寝の意図も落とす。
  - `test_wake_rate_by_hour_is_a_fraction_and_prints`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.arbiter`・`shibuya.engine.commit`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.world.facts.mock_schedule`・`shibuya.world.facts.weekly_reader`・`shibuya.world.model.state`・`tests/engine/test_sleep_suppression_d56.py`
- 決定の ID: D-51・D-56・D-62

## [test_pop_w21_world.py](../../../../../../tests/engine/test_pop_w21_world.py)

第 4 期 4-3 段 10「差し替え」の engine の読み口の試験(合成の小さな母集団+組んだ資産があれば実データ)。

- 公開の関数とクラス
  - `test_load_persona_maps_run_rows_and_w16_rows_are_blank`(関数)
  - `test_missing_columns_and_unknown_words_stop`(関数)
  - `test_persona_blocks_sit_before_b6_and_b5`(関数)
  - `test_persona_file_names_are_the_w21c_outputs`(関数)
  - `test_persona_override_keeps_the_original_and_stops_on_bad_input`(関数)
  - `test_real_short_run_has_dwellings_w21_store_staff_and_outside_employers`(関数)
  - `test_stores_without_table_staff_keep_the_round_robin_and_bad_stores_stop`(関数): 〔検収の直し・親の判断〕表の担当のいない店は今の丸振り(出どころの語を分ける)・表の店の番号が POI の外なら止まる・
  - `test_swapped_population_is_read_and_kept_through_take_and_sampling`(関数)
  - `test_swapped_population_without_the_table_stops`(関数)
  - `test_table_rows_give_store_staff_and_dwellings`(関数)
  - `test_w16_shaped_population_has_no_swap_columns`(関数)
  - `test_wage_inputs_take_w21_words_and_given_wages`(関数)
  - `test_without_the_table_the_rows_are_the_same_as_before`(関数)
- import している内部モジュール: `shibuya.build.pop.w21_build_c`・`shibuya.cli`・`shibuya.engine.decision.persona`・`shibuya.engine.economy_stage2`・`shibuya.engine.systems.build`・`shibuya.foundation.ports.decision`・`shibuya.world.facts.population_reader`・`shibuya.world.facts.rights.initial`・`shibuya.world.facts.rights.ledger`

## [test_presence_derive_v2.py](../../../../../../tests/engine/test_presence_derive_v2.py)

在圏ブロックの読み口 v2(``engine.presence.PlanBlocks.from_weekly(derive_rule="v2")``)。

- 公開の関数とクラス
  - `both`(関数)
  - `make_weekly`(関数): ``rows`` = ``[(agent_row, start, end, activity, place_kind, target_cell), …]``。
  - `spans`(関数)
  - `test_a_lodging_row_is_an_anchor_so_a_tourist_sleeps_in_the_stage`(関数)
  - `test_a_mid_day_outside_row_still_splits_the_anchored_day_into_two_blocks`(関数): ⑦(既存)の並び: 勤務*→休憩 域外→勤務* は v1 と同じく 2 本(錨は常に在圏)。
  - `test_a_return_ride_only_day_keeps_the_anchored_run_before_it`(関数): 行きの乗車を書かず帰りだけ書いた通勤者: 錨のラン(区間 0)が在圏側・乗車後の店は域外。
  - `test_a_visitor_who_wrote_only_the_return_ride_is_rescued`(関数): 奇数側(乗車の後)に滞在ランが無く偶数側にある → 偶数側が在圏(救済)。
  - `test_a_visitor_with_two_rides_is_in_the_stage_between_them`(関数)
  - `test_a_whole_day_outside_has_no_block_even_with_a_station_row`(関数): 本番 v2 で新たに 0 本になった体の形(0807-2340 用事 域外): 移動 駅 だけでは在圏にしない。
  - `test_default_rule_is_v2_and_bad_rules_are_rejected`(関数)
  - `test_home_side_station_and_after_ride_dinner_are_not_in_the_stage`(関数): 本番 v2 第 1 回の典型: 移動 駅(自宅側)→乗車→勤務*→移動 駅→乗車→食事 飲食店(自宅近く)。
  - `test_in_area_residents_read_exactly_as_v1`(関数)
  - `test_v21_a_move_only_anchored_run_without_rides_vanishes`(関数): 移動だけのラン(錨=cell≥0)で乗車に隣接しない: v2 は錨で残す・v2.1 は行程として落とす。
  - `test_v21_a_move_only_run_next_to_a_ride_on_one_side_only_also_vanishes`(関数): 層2 指摘 B(第176): 移動/支度だけのランは**両側とも**乗車行に隣接しない限り消える。
  - `test_v21_does_not_touch_mid_run_moves_or_in_area_residents`(関数)
  - `test_v21_drops_the_journey_rows_of_a_commuter_who_wrote_no_rides`(関数): 乗車を書かない域外居住者(本番 v2 表の 55.7%): 移動 駅→勤務*→移動 商業 は v2 で 1 本
  - `test_v21_keeps_the_walk_from_and_to_the_station_when_rides_are_written`(関数): 乗車→移動 駅→勤務*→移動 駅→乗車: 駅からの歩きは舞台の中=v2 と同じ 1 本。
  - `test_v21_trims_only_the_side_that_is_not_next_to_a_ride`(関数): 行きは乗車を書き、帰りは書かない: 先頭は残し末尾の移動だけ落とす。支度も落とす。
  - `test_v2_rule_on_the_real_w17_matches_the_parent_verified_counts`(関数): 親検証値(2026-09-12・全 390,067 体・day0)。表ごとに golden を持つ(``REAL_GOLDEN``・第170):
  - `test_without_rides_and_anchors_only_transit_only_runs_are_dropped`(関数): 乗車も錨も無い体: 滞在のあるランは全部在圏(v1 と同じ)・移動だけのランは落とす。
  - `three`(関数)
- import している内部モジュール: `shibuya.engine.presence`・`shibuya.world.facts.population_reader`・`shibuya.world.facts.weekly_reader`・`tests/golden_env.py`
- 読む試験: `tests/engine/test_env_and_sections_10f.py`
- 決定の ID: 第 170・第 173・第 176

## [test_presence_executor.py](../../../../../../tests/engine/test_presence_executor.py)

D-66 計画実行層(``engine.presence``・第1段)のテスト。

- 公開の関数とクラス
  - `census`(関数)
  - `fake_assets`(関数): 1 駅・平日のみの最小時刻表 + 方面→線の表 + 駅出口セル。
  - `make_layer`(関数)
  - `make_weekly`(関数): ``rows`` = ``[(agent_row, start, end, activity, place_kind, target_cell), …]``。
  - `make_world_agents`(関数): ``resolve.initialize`` と**同じ置き方**(``home_cell < 0`` の体は ``cell = node = -1``)。
  - `test_a_conversation_that_never_ends_is_forced_out_after_the_limit`(関数): ⑩-b(§4): 繰り延べ上限 30 tick で**強制退出**(幽霊を残さない)。
  - `test_a_resident_stays_in_the_stage_when_the_next_row_is_not_outside`(関数): ③-b(§10-7 (a)): **域内居住者は「次が域外」のときだけ退出**(隙間では出ない)。
  - `test_a_resident_who_boards_in_the_last_block_comes_back`(関数): E12(第3段): **次のブロックが無い**体が LLM 乗車で出たら、``t+60`` 以降の便で戻る。
  - `test_a_visitor_without_a_block_stays_outside_all_day`(関数): ⑧(§6 E7): その日 在圏ブロックが 0 本の体は**終日域外**(起床率の分母から外れる)。
  - `test_an_outside_resident_enters_and_leaves_two_or_three_times_a_day`(関数): ⑦(§7): 域外居住者は 1 日に 2〜3 回だけ出入りする(常駐しない)。
  - `test_an_outside_resident_never_sleeps_inside_the_stage`(関数): ⑨(§5 I6): ``home_cell < 0`` の体は就寝境界で**寝ない**(職場で寝る穴が塞がる)。
  - `test_arrival_is_never_later_than_the_block_start`(関数): ⑥(§3 E1): 到着 tick ≤ ブロック開始(間に合う最も遅い便。始発前は始発)。
  - `test_arrival_spread_never_exceeds_capacity_times_the_cap`(関数): ⑬(§3 E8): 容量ベース backward fill で 1 便が ``定員 × 混雑率上限`` を超えない。
  - `test_arrival_spread_stays_inside_the_eight_train_window`(関数): ⑬-b(§3 E8・第3段): **|到着便 − E1 便| ≤ 8** がどの体でも破れない。
  - `test_being_in_the_stage_implies_having_a_cell_on_every_tick`(関数): ④-b(§5 I6・層2 指摘 2026-09-11): **在圏(``transit_state==0``)⇒ セルとノードがある**。
  - `test_blocks_are_scale_invariant`(関数): ③(§7): n 体と n+1 体で、既存の体のブロックが 1 本も動かない。
  - `test_derive_folding_matches_the_parent_verified_counts`(関数): ⑭(§7): 実 W17(day0)の畳み方が親検証値と合う。
  - `test_everyone_attends_after_the_attendance_lottery_was_removed`(関数): 〔11-01 段 2 の 4〕出勤率のくじ(E6)は消した=全員出勤(日を変えても誰も休まない・ブロックは全員分)。
  - `test_exit_is_deferred_while_conversing_and_interrupts_shopping`(関数): ⑩(§4): 退出 tick に**会話中は繰り延べ**(≤30 tick)・**買物中/待ち行列は中断**。
  - `test_hunger_model_v1_reproduces_the_stage_3_checkpoints`(関数): 5 段目 5a(D-118 K5 (a)): 空腹の旧規則 ``hunger_model="v1"``。
  - `test_l4_scale_1_reproduces_the_stage_2c_checkpoints`(関数): 3 段目(D-99 (a′)・D-110): 上限スイッチ ``l4_scale=1.0`` で旧挙動(L4 按分・持ち越し 2 tick)。
  - `test_leave_effect_switch_is_removed`(関数): 〔第 4 期 4-3 版上げ 3 回目の第 2 部〕退去の効果の切替口 ``leave_effect=False``(第301 以前=9a の前)は消した=渡すと
  - `test_llm_boarding_is_re_armed_for_the_next_block`(関数): ④(§4): LLM が乗車で域外へ出たら、残り DEPART を落として**次のブロックの開始**へ張り直す。
  - `test_mix64_matches_the_build_side_definition`(関数): ``_mix64`` は W17 側(``build.sched``)と**同じ式**(二重定義の機械検査)。
  - `test_native_mode_and_other_exit_modes_are_reserved`(関数): §10-1/3: ``mode='native'`` と ``--exit-mode board_intent`` は**予約**(NotImplemented)。
  - `test_no_double_arrival_and_no_double_departure`(関数): ⑪(§5 I2/I3): ARRIVE は域外の体だけ・DEPART は在圏の体だけに適用される。
  - `test_null_arm_reproduces_the_recorded_checkpoint`(関数): ②(§7・**退化検査の要**): ``plan_executor=False`` は D-62 時点の golden と一致。
  - `test_overflow_on_the_last_train_stays_on_its_own_e1_train`(関数): ⑬-c(§3 E8・層2 最終確認): **E1 便が最終便**の体は③(E1 便が受け切り)へ直送する。
  - `test_plan_flags_are_written_through_resolve`(関数): §2: ``plan_flags`` の bit0(域外居住)/bit1(当日在圏予定)が立つ。
  - `test_pulled_in_agents_do_not_fire_a_stale_arrival`(関数): ⑫(§5 I4): 引き込み後に古い ARRIVE が発火しない・押し出しは**翌 tick に戻さない**。
  - `test_rider_conservation_holds_on_every_tick`(関数): ④(§5 I1): 在圏 + 乗車中 + 域外 = 体数 を**全 tick で**満たす。
  - `test_same_seed_gives_the_same_run_with_the_layer`(関数): ⑤(§7・T2): 既定腕で同 seed 2 ランが全 checkpoint 一致。
  - `test_summary_line_is_invisible_to_the_c7_parser`(関数): §5: 要約 1 行が ``c7lib.parse_run_summary`` の既存正規表現に当たらない。
  - `test_the_layer_draws_no_random_numbers`(関数): ①(§7): 層は ``core.rng`` を 1 語も引かない(T4 規模不変・帰無腕とのバイト一致)。
  - `test_the_real_civic_path_pulls_and_pushes_through_the_layer`(関数): ⑫-b(§5 I4): **civic の実経路**(``LargeEventProcess._arrive/_leave``)が層を通る。
  - `test_the_synthetic_world_keeps_the_layer_asleep`(関数): §6: 合成世界(母集団・週次表なし)では層が立たない=既存テストが無改造で通る。
  - `test_v3_default_reproduces_the_recorded_checkpoint`(関数): 第277(二層の段 3): 語彙 v3 の既定(CLI の既定・活動層 on・mock v3 形)の golden。
  - `w17_digest`(関数): 実 W17(``w17_schedule.parquet``)の md5 先頭 12 桁。golden は表ごとに持つ(第170・層2 指摘)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.build.sched.w17_schedule`・`shibuya.cli`・`shibuya.engine.presence`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.world.assets`・`shibuya.world.facts.population_reader`・`shibuya.world.facts.weekly_reader`・`shibuya.world.laws.civic`・`shibuya.world.laws.rail`・`shibuya.world.model.state`・`tests/golden_env.py`
- 読む試験: `tests/engine/processes/test_rate_rules_1101.py`・`tests/engine/test_env_and_sections_10f.py`・`tests/engine/test_presence_exit_walk.py`
- 決定の ID: 11-01・11-03/§3・D-1・D-62・D-66・D-99・D-110・D-112・D-113・D-114・D-118・第 145・第 168・第 170・第 267・第 277・第 288・第 289・第 291・第 301・第 302・第 330

## [test_presence_exit_walk.py](../../../../../../tests/engine/test_presence_exit_walk.py)

9a: 退出を歩かせる(D-115 ①・``--exit-mode walk_to_platform``)+退去の効果(D-112 ④)。

- 公開の関数とクラス
  - `test_cli_has_the_9a_flags`(関数)
  - `test_conversing_depart_is_deferred_then_walks`(関数)
  - `test_depart_walks_to_the_line_platform_instead_of_vanishing`(関数)
  - `test_leave_releases_store_queue_and_marks_conversation`(関数)
  - `test_leave_with_no_activity_expires_next_tick`(関数)
  - `test_plan_exit_riders_do_not_pay_the_fare`(関数): 第302 Q119 (b): 計画の退出で歩いて乗る体は運賃を払わない・LLM の乗車は払う(分けて数える)。
  - `test_rewalk_once_after_an_llm_action_then_immediate`(関数): 第302 Q117 (b): LLM の別の行為で意図が落ちたら、その行為の後に 1 回だけ歩き直す・2 回目は即時。
  - `test_run_walk_mode_accounts_for_every_exit_and_the_leave_switch_is_gone`(関数)
  - `test_too_far_and_lost_intent_fall_back_to_immediate`(関数)
  - `test_wait_keeps_a_plan_exit_walker_moving`(関数)
  - `test_walk_mode_is_accepted_and_board_intent_stays_reserved`(関数)
  - `test_walker_boarding_then_train_departure_is_a_plan_exit_not_llm`(関数)
  - `test_walker_wakes_are_suppressed_but_surprises_are_not`(関数)
  - `walk_layer`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.cli`・`shibuya.engine.activity`・`shibuya.engine.commit`・`shibuya.engine.presence`・`shibuya.engine.resolve`・`shibuya.foundation.vocab.actions`・`shibuya.world.laws.rail`・`shibuya.world.model.state`・`tests/engine/test_presence_executor.py`
- 決定の ID: D-51・D-112・D-115・第 301・第 302・第 330

## [test_processes_run.py](../../../../../../tests/engine/test_processes_run.py)

C4 結線(世界過程 → run)の受入テスト。

- 公開の関数とクラス
  - `small`(関数)
  - `test_all_declared_process_ids_have_an_implementation`(関数): 台帳 ⇄ 実装の双方向: 第1陣+前倒しの過程 id は全て実行器が名乗る。
  - `test_c4_second_half_is_bit_identical_for_the_same_seed`(関数): T2: 物・顕著行為・前倒しを入れても同一 seed で checkpoint ハッシュが一致する。
  - `test_c4_second_half_on_the_real_world`(関数): 受入: 実資産 5,000 体 × 1 日で C4 後半の全過程が回り、保存則・ゲートが立つ。
  - `test_conservation_holds_with_fares_in_the_equation`(関数)
  - `test_deletion_candidates_stay_empty`(関数): 憲法5(D-R2-4): 届き先が消えた細部は 1 件も無い。
  - `test_flow_reaches_the_b4_field`(関数): 混雑場が作った流れが B4 描画欄に載る(人物①「密度・流れ」)。
  - `test_new_processes_are_ablatable_by_id`(関数)
  - `test_p_notice_ablation_can_be_selected`(関数)
  - `test_processes_can_be_switched_off`(関数)
  - `test_real_world_runs_are_bit_identical_for_the_same_seed`(関数): T2: 実資産でも同一 seed で checkpoint ハッシュが一致する。
  - `test_run_day_on_the_real_world_with_all_first_batch_processes`(関数)
  - `test_run_result_carries_the_world_process_fields`(関数)
  - `test_two_runs_with_the_same_seed_are_identical`(関数): T2: エンジン層 bit 再現(世界過程を入れても崩れない)。
- import している内部モジュール: `shibuya.economy.accounts`・`shibuya.economy.census`・`shibuya.economy.checks`・`shibuya.economy.goods`・`shibuya.economy.ledger`・`shibuya.engine.arbiter`・`shibuya.engine.run`・`shibuya.foundation.ports.ledger`・`shibuya.world.assets`・`shibuya.world.ledger.first_batch`・`shibuya.world.model.notice_reach`・`shibuya.world.model.state`・`tests/_time_gates.py`
- 決定の ID: 11-01・11-02r/§1・11-02r/§1 #7・D-62・D-66・第 137

## [test_relations.py](../../../../../../tests/engine/test_relations.py)

C10 8a: **関係辺の表と導出**(R1 (a)・M12 (a)・D-93 (a)(b)(c)(d)・R6・第299)のテスト。

- 公開の関数とクラス
  - `build_renderer`(関数)
  - `ep`(関数)
  - `layer`(関数): 単体の仕組みの検査は 8a の τ(−1.1=会話 1 回の辺が 35 分生きる)で回す(期待値を τ の較正から切り離す)。
  - `pop`(関数)
  - `table`(関数)
  - `test_acquaintance_marks_in_the_near_line_and_off_is_unchanged`(関数)
  - `test_arm_checks_and_cli_flags`(関数)
  - `test_copresence_minutes_and_blocks`(関数)
  - `test_full_table_evicts_the_lowest_activation`(関数)
  - `test_initial_edges_hash_tiebreak_spreads_in_degree`(関数): 同じ日課の大組織(40 人・全員同点)で、id の順は行番号の小さい 15 人に入次数が集まる/hash は散る。
  - `test_initial_edges_household_work_school_and_cap`(関数)
  - `test_initial_edges_tau_and_density_arms`(関数)
  - `test_join_in_the_tick_the_session_opened_is_written_once`(関数): 3 人目が開いた同じ tick に加わっても、会話の行は参加者の組ごとに 1 本(二重に書かない)。
  - `test_last_copresence_many_matches_scalar`(関数): 性能修正(挙動不変): 直近の共在の配列版は 1 辺ずつの版と同じ値(代表日・週の両方・共在なしの辺も)。
  - `test_readers_and_writer_rounds_are_array_ops`(関数): P4: 読み口と 1 回の書き込みに for/while を書かない(体数比例の逐次ループなし)。
  - `test_readers_live_edges_strength_same_cell_and_invite_weights`(関数)
  - `test_relation_columns_only_in_the_arm_16_bytes_per_edge`(関数)
  - `test_run_default_is_off_and_relations_on_keeps_behavior`(関数)
  - `test_sessions_write_both_sides_and_utterances_do_not_add_n`(関数)
  - `test_tau_is_the_median_of_the_kth_edge`(関数)
  - `test_tenure_spreads_activation_and_arm_26_weeks`(関数): 第299 Q89/Q90: 在職期間を散らすと A が階段でなくなる(同じ共在でも A が組ごとに違う)・上限 26 週の腕。
  - `test_three_person_join_and_counters`(関数)
  - `test_writer_signs_from_result_codes_and_merges`(関数)
  - `weekly`(関数): 体ごとの (開始分, 終了分, セル) の行(全部 曜日 0=実資産と同じ 1 日ぶんの表)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.cli`・`shibuya.engine.conversation`・`shibuya.engine.memory`・`shibuya.engine.relations`・`shibuya.engine.run`・`shibuya.foundation.text.templates`・`shibuya.perception.renderer`・`shibuya.world.facts.weekly_reader`・`shibuya.world.model.state`・`tests/golden_env.py`
- 決定の ID: D-93・第 299・第 300・第 330・第 333

## [test_relations_8b.py](../../../../../../tests/engine/test_relations_8b.py)

C10 8b(会話の起点と相手選択+8a の直し)の検査。

- 公開の関数とクラス
  - `layer`(関数)
  - `table`(関数)
  - `talk`(関数)
  - `test_8b_per_tick_paths_are_array_ops`(関数): P4: 毎 tick の検出・同席・抽選に体数比例の for/while を書かない(宣言した小さな反復だけ)。
  - `test_acquaintance_appearance_wakes_once_per_pair_hour`(関数)
  - `test_acquaintance_ignores_edges_below_tau`(関数)
  - `test_chance_puts_acquaintances_within_2m_first_and_origin_labels`(関数)
  - `test_choose_partners_follows_dunbar_layers_and_is_deterministic`(関数)
  - `test_classical_near_strangers_and_rest_pick_is_hashed`(関数)
  - `test_cli_has_the_8b_flags`(関数)
  - `test_conversation_origin_counts_and_default_counters_unchanged`(関数)
  - `test_copresence_days_counts_weekdays_with_any_shared_slot`(関数)
  - `test_copresent_writes_once_per_pair_day_after_5_minutes_within_2m`(関数)
  - `test_default_tau_is_the_rederived_value_and_a_single_talk_lives_hours`(関数): 第300 訂正(8b′): n=共在の日数で再逆算した τ=−2.346(旧=在職期間ハッシュ v1)。第2波 §2A 項 2: 在職期間の
  - `test_invite_off_only_labels_origins`(関数)
  - `test_layer_weights_renormalize_over_present_layers`(関数)
  - `test_named_rows_keep_partner_and_no_edges_in_cell_keeps_fallback`(関数)
  - `test_newcomer_is_dropped_when_the_table_is_all_stronger`(関数)
  - `test_run_8b_on_is_deterministic_and_reports_origins_and_l4_share`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.cli`・`shibuya.engine.classical`・`shibuya.engine.conversation`・`shibuya.engine.memory`・`shibuya.engine.relations`・`shibuya.world.facts.weekly_reader`
- 決定の ID: D-31・第 299・第 300・第 333

## [test_relations_tenure.py](../../../../../../tests/engine/test_relations_tenure.py)

第2波 §2A 項 2: **初期辺の在職期間のハッシュの修正**(Q111 の解析で見つかった欠陥)のテスト。

- 公開の関数とクラス
  - `test_all_tied_organisation_bias_is_gone_with_v2`(関数): 200 人・同じ日課(全員同点)・k 15: v1 は同点の順=在職の短い順に選ぶ(元 id_u < 元 id_v の辺で 2 週未満が
  - `test_full_population_initial_net_is_uniform_in_every_kind_and_direction`(関数): 全母集団(W16+W17・〔段 10〕差し替えの世界は 345,858 体)。v2: 種別(世帯/職場/学校)× 向き(元 id の大小)のどれでも在職 2 週未満が
  - `test_relations_on_arm_golden_old_and_new`(関数)
  - `test_run_switch_is_removed_and_the_default_tau_is_v2`(関数): 〔第 4 期 4-3 版上げ 3 回目の第 2 部〕ランの口の切替口 --rel-tenure-hash(v1=旧)は消した=渡すと止まる(関係の部品の
  - `test_tenure_u_is_rank_independent_of_the_tie_hash`(関数)
  - `test_v1_is_the_old_formula_and_v2_is_symmetric`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.relations`・`shibuya.engine.run`・`shibuya.world.facts.population_reader`・`shibuya.world.facts.weekly_reader`・`tests/_data_ids.py`・`tests/golden_env.py`
- 読む試験: `tests/engine/test_env_and_sections_10f.py`
- 決定の ID: 11-01・11-03/§3・第 330

## [test_removed_switches_346.py](../../../../../../tests/engine/test_removed_switches_346.py)

第346 旧道の切替口の削除: 消した切替口はランの入口で止まる(検収 H1・L1)。

- 公開の関数とクラス
  - `test_a_removed_cli_flag_stops_even_when_abbreviated`(関数): 〔検収 L1〕``--proximity 1.0`` が略記で ``--proximity-d`` の感度の腕として通らない。
  - `test_a_run_with_a_removed_switch_env_stops_before_the_ticks`(関数): 値によらず(既定の値でも)止まる。止まるのは組み立ての最初か、切替口を持っていたモジュールの読み込み=刻みの前。
  - `test_the_hidden_flags_are_not_in_the_help`(関数)
  - `test_the_list_and_the_message_are_in_one_place`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.removed_switches`
- 環境変数: `SHIBUYA_DEFECT_FIXES_1103`・`SHIBUYA_PROXIMITY`・`SHIBUYA_RULES_42`・`SHIBUYA_RULES_42B`・`SHIBUYA_SEAT_RELEASE`・`os.environ` をまるごと使う
- 決定の ID: 第 346

## [test_renderer_wiring.py](../../../../../../tests/engine/test_renderer_wiring.py)

C3 結線(レンダラ → bridge → run)の受入テスト。

- 公開の関数とクラス
  - `RecordingAdapter`(クラス): 描画のたびに ``(tick, agent, cell, kind, B0-B4b のバイト列)`` を残すアダプタ。
  - `recording`(関数): ``run_day`` が作るアダプタを記録つきに差し替える。
  - `test_b6_names_the_attempted_action_in_a_real_run`(関数): B6「直前の結果」の主語が ``last_action`` の語になっている(結線の突き合わせ)。
  - `test_dynamic_noise_overrides_the_static_field`(関数): ``cells.noise_stage`` に値が入っていれば静的場より優先(C4 の世界過程用の口)。
  - `test_engine_continuation_does_not_overwrite_the_attempted_action`(関数): エンジン継続(``ENGINE_STEP``)は「新しく試みた行動」ではないので上書きしない。
  - `test_group_token_budgets_hold_across_a_whole_run`(関数): §2.2 グループ予算(750/250/300)は全描画で満たされる(超過は描画側が例外にする)。
  - `test_losers_also_get_their_attempted_action`(関数): Phase B の落選者(``LOST_ARBITRATION``)も「試みた行動」を残す。
  - `test_noise_stage_switches_between_day_and_night`(関数): 環境基準の昼 6-22 時 / 夜 22-6 時で読む配列が入れ替わる。
  - `test_open_count_no_longer_wakes_anybody`(関数): 営業中POI数は描画に出ない → B4 欄から外した(過検出の除去)。
  - `test_resolve_records_the_attempted_action_not_the_resulting_state`(関数): 失敗した行動も ``last_action`` に残る(``activity`` では復元できない)。
  - `test_rule8_holds_in_situ_on_a_synthetic_world`(関数): 走行中のランから拾った実際の起床対で B0-B4b がバイト一致する。
  - `test_rule8_holds_in_situ_on_the_real_world`(関数): 実資産(520 セル・2,337 POI)でも同じ。
  - `test_synthetic_world_has_no_static_noise_field`(関数)
  - `test_the_detector_hashes_exactly_the_rows_the_renderer_renders`(関数): 起床条件 (i) の欄=レンダラの ``b4_field_rows``(engine 側からの同一性検査)。
  - `test_world_and_perception_agree_on_the_w10_noise_stage`(関数): world 側(``assets.noise_stage_*``)と知覚側(``PerceptionAssets``)の集約が一致する。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.change_detect`・`shibuya.engine.commit`・`shibuya.engine.llm_bridge`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.foundation.text.templates`・`shibuya.perception.renderer`・`shibuya.world.model.state`
- 決定の ID: D-56

## [test_resolve.py](../../../../../../tests/engine/test_resolve.py)

engine.resolve のテスト: 行動契約書 §2.1 の 12 語(前提・効果・失敗の意味論)と保存則。

- 公開の関数とクラス
  - `test_actions_that_never_fail`(関数)
  - `test_advance_body_only_moves_on_its_period`(関数)
  - `test_all_twelve_words_parse`(関数)
  - `test_apply_detection_writes_hashes_and_stages`(関数)
  - `test_boarding_and_alighting_fail_per_contract`(関数): 行動契約書 §2.1: 乗車の失敗=列車なし・降車の失敗=その駅には止まらない。
  - `test_buy_moves_money_to_revenue_and_decrements_stock`(関数)
  - `test_buy_outside_opening_hours_fails_closed`(関数)
  - `test_buy_without_a_target_fails_bad_target`(関数)
  - `test_buy_without_money_fails`(関数)
  - `test_buy_without_stock_fails_and_stock_never_goes_negative`(関数)
  - `test_density_is_recomputed_每tick`(関数)
  - `test_engine_step_arrival_returns_to_idle_and_updates_cell`(関数)
  - `test_help_always_fails_in_c2`(関数)
  - `test_initialize_places_agents_at_home`(関数)
  - `test_move_sets_target_and_engine_step_advances`(関数)
  - `test_move_to_an_invalid_cell_fails_unreachable`(関数)
  - `test_move_to_the_current_cell_is_immediate`(関数)
  - `test_refuse_is_unaffected_by_the_report_precondition`(関数)
  - `test_report_and_refuse_are_recorded_without_failing`(関数): 顕著行為の過程が無い(C2 互換)なら通報も断るも従来どおり記録のみ。
  - `test_report_precondition_switch_off_restores_always_ok`(関数)
  - `test_report_requires_a_perceived_event_d113_2`(関数): 契約書 §2.1 通報の前提「当該事象を知覚済み」= 直近 5 tick に自分のセルの B4 に事象の行。
  - `test_report_window_boundary_is_inclusive`(関数)
  - `test_rest_recovers_fatigue`(関数)
  - `test_set_refractory_uses_the_section6_table`(関数)
  - `test_sleep_at_home_sets_sleeping_and_records_a_reflection`(関数)
  - `test_sleep_away_from_home_fails_no_bed`(関数)
  - `test_talk_creates_a_session_when_partner_is_idle_in_the_same_cell`(関数)
  - `test_talk_to_a_busy_partner_fails`(関数)
  - `test_talk_to_someone_in_another_cell_fails`(関数)
  - `test_talk_without_a_partner_fails_bad_target`(関数)
  - `test_two_buyers_of_the_same_poi_both_decrement`(関数)
  - `test_undefined_action_falls_back_to_wait`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.change_detect`・`shibuya.engine.commit`・`shibuya.engine.resolve`・`shibuya.world.model.state`
- 決定の ID: D-113・第 267・第 330

## [test_response_delay.py](../../../../../../tests/engine/test_response_delay.py)

10a(指示書 10-03 §3-5 A9): 応答の遅れ「発射 +1 tick」(〔第 4 期 4-3 版上げ 3 回目の第 2 部〕旧の +2 の切替口``response_delay`` は消した)。

- 公開の関数とクラス
  - `applied`(関数): ①で行動に変えた (tick, 体) を控える(``intents_from_responses`` を読むだけで包む)。
  - `fleet_servers`(関数)
  - `test_fleet_call_fired_at_T_is_applied_at_T_plus_delay`(関数)
  - `test_mock_is_already_plus_one_and_the_switch_is_gone`(関数): mock は発射 +1 tick で反映(既に +1)。〔第 4 期 4-3 版上げ 3 回目の第 2 部〕切替口 response_delay(2=旧)は消した=
  - `test_record_and_replay_match_under_each_delay`(関数)
  - `test_replay_of_a_plus2_tape_stops`(関数): 〔第 2 部〕+2(旧)で録ったテープ(meta の値 2)と値の無いテープ(10a より前)は再生しない=止まる(旧値の再現は安定版の
  - `test_utterances_are_recorded_at_the_receiving_tick`(関数): 会話ターンの発話は受け取った tick(発射 +1)で記録される=+1 でも +2 でも tick は動かない。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.commit`・`shibuya.engine.conversation`・`shibuya.engine.run`・`shibuya.engine.tape`・`shibuya.llm.fleet`・`shibuya.world.model.state`・`tests/engine/test_fleet_wiring.py`・`tests/engine/test_tape_deferred.py`・`tests/engine/test_tape_wiring.py`・`tests/llm/test_fleet.py`
- 決定の ID: 10-03/§3-5

## [test_resume_10d.py](../../../../../../tests/engine/test_resume_10d.py)

10d(D-102 Q3・Q5・指示書 10-03 §3-6 A10・§3-7 A11): 日境界の再開と複数日の通しラン。

- 公開の関数とクラス
  - `syn_straight`(関数)
  - `test_b3_weather_and_the_environment_read_the_same_day_on_day_two`(関数): 検収 D1・T2: 2 日目の 12 時の B3 の天候の語と、環境の過程の暑さの段が、同じ再生の実日の W13 の行から来る。
  - `test_b3_weather_follows_the_replay_date_of_each_day`(関数): 再確認 N1: 再生の実日が日ごとに変わるとき、2 日目の B3 の天候は 2 日目の実日の W13 の行(描画の単体)。
  - `test_cli_switches_for_sim_days_and_resume`(関数): 親の答え 7: ``--sim-days``・``--resume-from``(と書き出し先 ``--state-out``)を engine.run と cli で同じ綴りで。
  - `test_counter_rng_resume_draws_once`(関数)
  - `test_daily_close_runs_once_per_day`(関数)
  - `test_daily_tables_are_relaid_from_the_calendar_day`(関数): 親の答え 5: 2 日目の頭で W7 の曜日の行と世界過程の日ごとの乱数の表を暦の口の日で引き直す。
  - `test_day_boundary_resume_keeps_the_census_after_the_ledger_fix`(関数): 10d で直した行(O92 の金の台帳の ``_snap``・生ログの位置)が無いと、日の境目で再開した日のセンサスが落ちた。
  - `test_fingerprint_and_header_have_no_paths_and_run_ids_are_unique`(関数): 検収 L3・L6: 指紋はパスの文字列でなく中身で同定する・見出しに絶対パスが入らない・ラン ID は実行ごとに違う。
  - `test_fleet_inflight_calls_are_reissued_with_the_same_call_id`(関数)
  - `test_fleet_inflight_calls_at_the_day_boundary`(関数): 検収 T5: 日の境目(T=1440)で艦隊の未着の呼がある形の再開(夜の街の分)。
  - `test_ipf_cache_key_has_the_day`(関数): 親の答え 4: classical の c_t の覚え書きの鍵に日がある(2 日目は 2 日目の状態から作る)。
  - `test_ledger_rows_moved_by_10d`(関数): 親の答え 1: 14 項目を台帳の行に吸収した(軸の判定)。
  - `test_memory_mid_day_resume_keeps_calls_after_the_ledger_fix`(関数): 10d で直した行(O91 の ``conv.n_opened``=記憶の層が読む)が無いと、日中の再開で呼数が食い違った。
  - `test_named_closed_memo_survives_a_resume`(関数): 検収 L2・T4(再確認 N2 で直した): 名指しの即時閉店の控えを入れてから止めて戻すと、控えが戻り、再開の後の
  - `test_no_money_is_added_at_the_head_of_day_two_or_on_resume`(関数)
  - `test_read_state_refuses_broken_or_mismatched_files`(関数): 10f: npz+json は外から来たファイルでもコードを動かさない。それでも壊れた・取り違えたファイルは読まない
  - `test_resume_in_a_fresh_process_with_empty_caches`(関数)
  - `test_resume_rebuilds_the_staff_table_shared_with_restocking`(関数): 検収 L4・T3: 再開の後の開閉の担当従業者の表(補充の過程と同じ配列)が通しと同じ。
  - `test_resume_refuses_a_ledger_that_was_already_endowed`(関数)
  - `test_resume_refuses_finished_mismatched_and_wrong_stops`(関数)
  - `test_state_file_is_one_atomic_bundle`(関数)
  - `test_synthetic_all_arms_resume_equals_straight_at_every_tick`(関数)
  - `test_two_day_world_run_closes_money_goods_and_bodies_each_day`(関数)
  - `test_world_arms_resume_equals_straight`(関数)
  - `test_world_resume_equals_straight_at_every_tick`(関数)
  - `world_straight`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.cli`・`shibuya.economy.ledger`・`shibuya.engine.classical`・`shibuya.engine.poi_target`・`shibuya.engine.presence`・`shibuya.engine.resolve`・`shibuya.engine.resume`・`shibuya.engine.run`・`shibuya.engine.state_ledger`・`shibuya.engine.tape`・`shibuya.foundation.ports.ledger`・`shibuya.foundation.rng`・`shibuya.foundation.text.normalize`・`shibuya.foundation.text.templates`・`shibuya.perception.renderer`・`shibuya.world.facts.mock_schedule`・`shibuya.world.laws.goods_flow`・`shibuya.world.laws.runner`・`shibuya.world.laws.switch_absent`・`shibuya.world.laws.switch_rate`・`shibuya.world.model.state`・`tests/engine/test_fleet_wiring.py`・`tests/engine/test_sim_time_T.py`・`tests/llm/test_fleet.py`
- 環境変数: `os.environ` をまるごと使う
- 決定の ID: 10-03/§3-6・11-01・11-02r/§1・11-02r/§1 #7・D-102・第 330

## [test_salt_seed_split_10f.py](../../../../../../tests/engine/test_salt_seed_split_10f.py)

10f 第 2 段: 母集団の seed と動きの seed の分離(K21 (a))と、salt の道具の回す役(T3 の CRN の健全性)。

- 公開の関数とクラス
  - `test_bad_sub_seeds_are_refused`(関数)
  - `test_dynamic_domains_match_the_defaults`(関数): 検収 S3-1 の 4: ``self.domain`` の手書きの対応を、実物の既定の値と突き合わせる。
  - `test_environment_seed_only_changes_weather_events_and_works`(関数): S1: 環境の seed だけ変えると、大きな催しの会場と工事の辺が変わり、体の属性と動きの流れの鍵は同じ。
  - `test_every_rng_domain_in_src_is_classified`(関数)
  - `test_fingerprint_unchanged_by_default_and_carries_different_sub_seeds`(関数)
  - `test_motion_seed_only_keeps_the_population_and_environment`(関数)
  - `test_omitted_population_and_environment_seed_is_the_same_run`(関数)
  - `test_population_and_motion_streams_use_their_own_seed_synthetic`(関数)
  - `test_population_and_motion_streams_use_their_own_seed_world`(関数)
  - `test_road_works_day_key_with_nonzero_day_index`(関数): 再検収 T1: ``day_index`` が 0 でないランで、0 日目の工事の辺はその日の鍵と環境の seed で引く。
  - `test_runner_environment_modes`(関数): S1: 回す役の ``--environment-mode``。fixed は環境の seed が全部同じ(省略=母集団の seed)・salt は salt と同じ。
  - `test_runner_refuses_seed_args_in_arms`(関数): 再検収 T5: 腕の引数に seed の 3 つを書くと、理由を出して止める。
  - `test_seeded_hash_sites_are_classified`(関数)
  - `test_static_scan_catches_aliases_and_keyword_domains`(関数): 検収 S3-1 の 1・2: 別名の import と名前つきの ``domain=`` を拾う(わざと書いた断片で)。
  - `test_t3_runner_first_diff_matches_first_diff_py_and_crn_checks`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.conversation`・`shibuya.engine.resume`・`shibuya.engine.run`・`shibuya.foundation.rng`・`shibuya.llm.mock`・`shibuya.world.laws.civic`・`shibuya.world.laws.environment`・`shibuya.world.laws.logistics`・`shibuya.world.laws.switch_rate`・`shibuya.world.model.geometry`・`tools/c7/salt_compare.py`
- 読む試験: `tests/engine/memory/test_m1_runs.py`
- 環境変数: `SHIBUYA_RATE_RULES`・`os.environ` をまるごと使う
- 決定の ID: 11-01・第 330・第 346

## [test_scheduler.py](../../../../../../tests/engine/test_scheduler.py)

engine.scheduler のテスト: 順序規約(§2.5)・純関数性・繰り延べ待ち行列の診断列。

- 公開の関数とクラス
  - `test_cancel_and_reschedule`(関数)
  - `test_coalesce_keeps_first_occurrence`(関数)
  - `test_deferral_queue_counts_all_four_diagnostics`(関数)
  - `test_deferral_queue_interns_reasons`(関数)
  - `test_deferral_queue_rejects_institution_class`(関数): 制度(−1)はエンジン側イベントで繰り延べ対象外(知覚契約書 §6 の4クラス)。
  - `test_deferral_queue_waiting_ticks_and_pop`(関数)
  - `test_diag_columns_match_manifest_schema`(関数): 診断行4列は manifest 側の定義そのもの(engine は再輸出するだけ=定義を増やさない)。
  - `test_due_coalesces_multiple_wakes_of_one_agent`(関数): §6 運用規定②: 同一体の複数条件が同時に明けたら 1 呼に合流。
  - `test_due_events_columns`(関数)
  - `test_empty_tick`(関数)
  - `test_far_future_goes_to_heap_then_ring`(関数)
  - `test_offset_then_class_rank_ordering`(関数): (offset_ns, class_rank, blake3, agent_id) の昇順。
  - `test_order_indices_is_a_permutation`(関数)
  - `test_property_order_is_independent_of_insertion_order`(関数): T3 相当: 挿入順を並べ替えても出力(agent_id 列)は変わらない。
  - `test_pure_function_same_input_same_output`(関数)
  - `test_rejects_past_tick_and_bad_offset`(関数)
  - `test_ring_reuse_after_a_full_lap`(関数)
  - `test_schedule_due_consume_cycle`(関数)
  - `test_scheduler_matches_pure_function_on_same_state`(関数)
  - `test_tick_state_validates_shape_and_dtype`(関数)
  - `test_tiebreak_is_not_agent_id_order`(関数): 同一 (offset, class) では blake3 撹拌が効き、ID 昇順にはならない(v1 C-8 の根治)。
- import している内部モジュール: `shibuya.foundation.manifest.schema`・`shibuya.foundation.queues.scheduler`・`shibuya.foundation.types`

## [test_scheduler_p3.py](../../../../../../tests/engine/test_scheduler_p3.py)

P3 ゲート: イベント処理スループット **≥10万イベント/秒**(予算宣言表 P3)。

- 公開の関数とクラス
  - `test_p3_event_throughput`(関数)
- import している内部モジュール: `shibuya.foundation.budget`・`shibuya.foundation.queues.scheduler`・`tests/_time_gates.py`・`tests/engine/time/__init__.py`

## [test_seat_release_2_4.py](../../../../../../tests/engine/test_seat_release_2_4.py)

〔第 2 期 2-4 V3〕在席の印を歩き出しで解く(``engine.seat_release``・``resolve._apply_move``)。

- 公開の関数とクラス
  - `test_default_header_and_resume_check`(関数)
  - `test_removed_seat_release_switch_env_and_cli_flag_stop`(関数): 〔第346〕消した切替口: 環境変数 SHIBUYA_SEAT_RELEASE を与えると読み込みで止まる・CLI の --seat-release は無い。
  - `test_resume_without_the_seat_header_is_refused`(関数): 腕は設定の指紋に入れない=状態のファイルの見出しの ``seat_release`` を見る。〔第346〕見出しに無い状態のファイル
  - `test_run_manifest_reports_the_arm_and_the_count`(関数): 合成の世界のランの manifest の ``leave_effects`` に腕(walk に固定)と解いた数が出る・見出しにも walk。
  - `test_unseated_walkers_are_not_counted`(関数)
  - `test_walkers_release_the_seat_only_with_the_walk_arm`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.cli`・`shibuya.engine.commit`・`shibuya.engine.resolve`・`shibuya.engine.resume`・`shibuya.engine.run`・`shibuya.world.laws.switch_seat`・`shibuya.world.model.state`
- 環境変数: `SHIBUYA_SEAT_RELEASE`・`os.environ` をまるごと使う
- 決定の ID: 第 346

## [test_sim_time_T.py](../../../../../../tests/engine/test_sim_time_T.py)

10a(指示書 10-03 §3-1 A1): 通しの時刻 T(T = 日 × 1 日の tick 数 + 日の中の tick)の既知の答え。

- 公開の関数とクラス
  - `test_classical_and_store_choice_read_the_next_plan_by_tick_of_day`(関数)
  - `test_conversation_edge_age_is_120_minutes_across_midnight`(関数)
  - `test_day0_of_a_two_day_run_is_the_one_day_run`(関数)
  - `test_day2_draws_differ_from_day1_for_the_same_tick_and_agent`(関数)
  - `test_manifest_records_tick_seconds_and_start`(関数)
  - `test_multi_day_mouth_refuses_what_needs_the_day_head`(関数)
  - `test_next_boundary_tables_are_read_by_tick_of_day`(関数)
  - `test_no_negative_elapsed_time_in_any_tick_column_every_tick`(関数)
  - `test_out_of_area_meals_repeat_by_tick_of_day`(関数)
  - `test_real_calendar_run_needs_a_valid_start`(関数)
  - `test_refractory_set_at_2350_expires_at_0010_next_day`(関数)
  - `test_school_holiday_in_day_index_mode_only_warns`(関数): 〔改訂(第330・RET)〕前は day_index の暦で「学校の長期休みは警告だけ」を見た(day_index を消した)。いまは止める。
  - `test_start_date_moves_the_prompt_clock`(関数): 開始日を渡すとプロンプトの日付(世界内日時)がその日になる。渡さないランは今の日付のまま。
  - `test_tape_and_call_keys_use_T`(関数)
  - `test_tick_columns_can_hold_30_days_of_T`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.activity`・`shibuya.engine.arbiter`・`shibuya.engine.calendar`・`shibuya.engine.chooser`・`shibuya.engine.classical`・`shibuya.engine.relations`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.engine.store_choice`・`shibuya.engine.systems.build`・`shibuya.engine.tape`・`shibuya.foundation.hashing`・`shibuya.foundation.types`・`shibuya.llm`・`shibuya.llm.mock`・`shibuya.perception.renderer`・`shibuya.world.body.energy`・`shibuya.world.facts.mock_schedule`・`shibuya.world.laws.runner`・`shibuya.world.model.state`・`tests/engine/test_calendar.py`
- 読む試験: `tests/engine/test_resume_10d.py`・`tests/engine/test_state_checks_10f.py`
- 決定の ID: 10-03/§3-1・第 330

## [test_sleep_suppression_d56.py](../../../../../../tests/engine/test_sleep_suppression_d56.py)

D-56 就寝抑止(ユーザー決定 (a)・2026-09-10)のテスト。

- 公開の関数とクラス
  - `test_a_midnight_window_makes_no_calls_and_the_null_arm_shows_the_bug`(関数): tick 0 = 世界内 00:00(``resolve.initialize`` が全員 ``SLEEPING``)。
  - `test_a_sleeping_agent_is_woken_by_the_boundary_but_not_by_the_body`(関数): 同じ体・同じ tick に境界と内受容が立ったら、**境界だけ**が残って 1 呼になる。
  - `test_arbitrate_stays_a_pure_function_under_the_sleep_rule`(関数): 並び順に依存しない(T3 の前提)。抑止を入れても選抜集合・計数は同じ。
  - `test_calls_by_hour_sums_to_llm_calls`(関数): ``calls_by_hour``(24 要素)の合計 = ``llm_calls``(C7 受入で a(h) と照合する欄)。
  - `test_calls_come_back_once_the_first_plan_boundary_is_crossed`(関数): 合成日課の最初の境界(起床・tick 300-480)を跨ぐ窓では呼が立つ。
  - `test_conversation_turns_pass_through_even_while_asleep`(関数): 会話ターンは ``resolve._UNADDRESSABLE`` で就寝中には来ないが、来たら通す。
  - `test_interoception_and_cell_change_do_not_wake_a_sleeping_agent`(関数): 内受容閾値・セル動的ブロックの候補は、就寝中の個体では呼にならない。
  - `test_pending_candidates_are_dropped_when_the_agent_falls_asleep`(関数): 繰り延べで保留に積まれた候補も、就寝に入った体の分は同じ規則で落ちる。
  - `test_plan_boundaries_still_wake_a_sleeping_agent`(関数): **眠りから覚める境界**を含む計画境界 4 条件は就寝中でも通る(例外 (i))。
  - `test_refractory_and_sleep_are_counted_in_separate_columns`(関数): ``suppressed``(不応期)と ``sleep_suppressed``(就寝)は排他=二重計上しない。
  - `test_salient_events_reach_a_sleeping_agent`(関数): 顕著行為(火事・急病)は就寝中でも起こす(例外 (ii))。
  - `test_the_activity_that_drives_the_rule_is_the_sleeping_one`(関数): 規則が読むのは ``Activity.SLEEPING`` ただ 1 つ(tick 0 の種の確認込み)。
  - `test_the_other_individual_conditions_are_suppressed_too`(関数): 知人出現・近接入替・被注視・傍受(第2陣)も同じ扱い=源が変化検出なら落とす。
  - `test_the_sleeping_population_shrinks_the_night_share_of_the_calls`(関数): 1 シミュ日: 深夜 0〜5 時の呼の割合が帰無腕より小さくなる(a(h) の向き)。
  - `test_two_runs_with_the_same_seed_are_bit_identical`(関数): 決定論(T2)。抑止を入れても同 seed 2 回で checkpoint・診断が一致する。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.arbiter`・`shibuya.engine.run`・`shibuya.foundation.types`・`shibuya.world.model.state`
- 読む試験: `tests/engine/test_plan_sleep_d62.py`
- 決定の ID: D-56

## [test_stage3_small_fixes.py](../../../../../../tests/engine/test_stage3_small_fixes.py)

3 段目と同じ回の小修正 3 件(第289): ① 購入の件数は台帳が通した行だけ ② Q24 着いた後の活動は最新の応答の活動 ③ Q25 名指しの即時閉店の B6 に店名・閉店中・W7 の開店時刻。

- 公開の関数とクラス
  - `test_a_kept_response_without_an_activity_keeps_the_one_from_setting_q24`(関数)
  - `test_b6_names_the_closed_shop_and_the_opening_time_only_for_that_agent_q25`(関数)
  - `test_n_purchases_counts_only_the_rows_the_ledger_passed`(関数)
  - `test_the_engine_lookup_reads_the_w7_opening_matrix_q25`(関数)
  - `test_the_latest_kept_response_activity_is_restored_after_arrival_q24`(関数)
  - `test_the_resolver_records_the_immediate_named_closure_q25`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.chooser`・`shibuya.engine.commit`・`shibuya.engine.poi_target`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.foundation.text.channels`・`shibuya.foundation.vocab.actions`・`shibuya.perception.renderer`・`tests/engine/test_intent_hold.py`・`tests/engine/test_move_destination.py`
- 読む試験: `tests/engine/test_familiarity.py`
- 決定の ID: 第 289

## [test_state_checks_10f.py](../../../../../../tests/engine/test_state_checks_10f.py)

10f 第 3 段: AST と実行時の検査(K24 (a))・K19 の検査(K25 (a))。

- 公開の関数とクラス
  - `ext_scan`(関数)
  - `k19_runs`(関数): 合成世界・率 ×1000・2 日(counter)。〔改訂(第330・RET)〕前は stateful(旧値の再現の切替口)とも比べた(消した)。
  - `syn_straight`(関数)
  - `test_axis1_stale_allow_and_collision_entries_fail`(関数)
  - `test_axis2_discardable_reset_keeps_the_run_synthetic`(関数)
  - `test_axis2_discardable_reset_keeps_the_run_world`(関数)
  - `test_external_axis1_ast_passes_on_src`(関数)
  - `test_external_axis1_tables_have_reasons`(関数)
  - `test_k19_empty_allow_list_reports_every_overlap`(関数): 〔改訂(第330・RET)〕前は stateful のランの重なりを空の許可の表で見て全部落ちることを見た(stateful を消した)。
  - `test_k19_runtime_default_v3_5000_known_counts`(関数): 既定 v3・5,000 体・seed 1・1 日。10e(E4): counter では実際の重なり 0。final は包まないランと同じ。
  - `test_k19_runtime_overlaps_only_in_the_allow_list`(関数): 10e(E4): counter では実際の重なりが 0(許可の表に ``overlap`` は無い)。〔改訂(第330・RET)〕扱い ``stateful`` の
  - `test_k19_runtime_world_two_days`(関数): 世界資産 300 体・2 日(既定 v3)。10e(E4・U2): counter では日の鍵の流れ(配送・工事)も重ならない。
  - `test_k19_static_sites_are_frozen`(関数)
  - `test_t4_axis1_collision_needs_the_owner_receiver`(関数): 名前の衝突は受け手が持ち主を指さないときだけ許す(持ち主の名前で読めば落ちる)。
  - `test_t4_axis1_reading_a_no_attribute_in_a_behavior_place_fails`(関数): T4 軸 1: 実物の src に「挙動の場所で no/diag の属性を読む」断片を 1 つ足すと落ちる。
  - `test_t4_axis2_ledger_snap_made_discardable_fails_world`(関数): T4 軸 2 の 2 例目(世界資産・金の台帳): O92 の ``ledger.money._snap``(日の締めの基準)を 2 日目の途中で捨てると、
  - `test_t4_axis2_required_made_discardable_fails`(関数): T4 軸 2: O91 の ``conv.n_opened``(10d で再開の試験が見つけた 14 項目の 1 つ・記憶の層が読む)を、わざと
  - `test_t5_runtime_fifth_word_caller_fails`(関数): T5: 体ごとの流れ(1 語目=体)から 5 語引く呼び手を足すと、隣の体の流れと重なって落ちる。
  - `test_t5_static_fifth_word_caller_fails`(関数)
  - `test_u5_allow_entries_have_a_fixed_hit_count`(関数): U5: 場所ごとの許可は当たる数を固定する。数を変えた宣言と、許可した行を挙動の場所に写した src で落ちる。
  - `test_u7_ipf_cache_with_a_multiplier_is_caught`(関数): U7: O90 ``classical._ipf_cache`` は乗数が全部 1 の classical では使われない(10d の記録・検収で捕まらなかった)。
  - `test_u7_pulled_in_today_is_outside_this_check`(関数): U7: O37 ``presence._pulled_in_today``(軸 1 diag)は、わざと discardable にして日の境目の直後(T=1441)に捨てても
  - `test_v3_allow_entries_pin_the_function_of_the_line`(関数): 10e(E2・10f 第 3 段の検収 V3): 許可した行を別の関数へ**移す**(数は同じ)と、関数の名前で落ちる。
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.classical`・`shibuya.engine.resolve`・`shibuya.engine.rng_audit`・`shibuya.engine.run`・`shibuya.engine.state_ledger`・`shibuya.engine.state_ledger_ast`・`shibuya.foundation.rng`・`shibuya.world.laws.opening`・`shibuya.world.laws.switch_rate`・`tests/engine/discard_probe.py`・`tests/engine/test_sim_time_T.py`
- 決定の ID: 11-01・11-03/§3・第 330・第 337・第 346

## [test_state_format_10f.py](../../../../../../tests/engine/test_state_format_10f.py)

10f 第 3 段: 保存の形式 npz+json(K23 (a))。

- 公開の関数とクラス
  - `mid_state`(関数)
  - `test_allowed_class_table_is_importable_and_has_no_custom_pickling`(関数)
  - `test_broken_meta_and_nan_constants_are_refused`(関数)
  - `test_bundle_is_checked_against_the_ledger`(関数)
  - `test_check_item_kinds_ignores_none_and_numbers`(関数)
  - `test_generator_state_continues_the_same_draws`(関数)
  - `test_item_kinds_are_checked_before_restoring`(関数): 戻す前に今の値の型と突き合わせる(辞書が list に化けた・配列の dtype が違う)。辞書の鍵の型は、今の値に鍵が
  - `test_legacy_pickle_is_no_longer_read`(関数): 10e(E2): 10d の pickle の読み口を消した。自分が書いた形の ``.pkl`` でも開かずに止まる(pickle を開かない)。
  - `test_marks_roundtrip_types_order_and_values`(関数)
  - `test_object_arrays_in_the_npz_are_refused`(関数)
  - `test_reader_uses_allow_pickle_false_and_never_unpickles`(関数)
  - `test_real_state_keeps_shared_identity_and_roundtrips`(関数)
  - `test_shared_objects_keep_their_identity`(関数): 同じオブジェクトを 2 か所から指す値(凍結した Target・配列・list)は 1 つのまま戻る(pickle と同じ)。
  - `test_size_and_time_5000`(関数): 既定 v3・5,000 体・seed 1・テープつき・2 日のランを T=1440 で止めた状態: 1.1 MB 以下。pickle と比べる。
  - `test_state_file_is_npz_and_resume_equals_straight`(関数)
  - `test_u1_cli_flag_for_the_legacy_pickle_is_gone`(関数): 10e(E2): CLI の ``--resume-legacy-pickle`` を消した(``engine.run`` と ``shibuya.cli`` で同じ口)。
  - `test_u1_pickle_is_never_opened`(関数)
  - `test_u1_resume_from_a_pkl_written_by_the_pickle_commit`(関数): ``129da80``(第 3 段の前の HEAD)の写しの src で書いた本物の ``.pkl`` は、10e(E2)で読み口を消したので
  - `test_u3_value_class_fields_match_the_class`(関数): U3: dataclass でない値のクラスの欄の一覧が、クラスの属性(AST の ``self.x = …``)と同じ。
  - `test_u4_member_checks_and_size_cap`(関数)
  - `test_unknown_classes_and_marks_are_refused`(関数)
  - `test_unwritable_values_are_refused_with_the_place`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.class_ids`・`shibuya.engine.conversation`・`shibuya.engine.resume`・`shibuya.engine.run`・`shibuya.engine.state_codec`・`shibuya.engine.state_hashes`・`shibuya.engine.state_ledger`・`shibuya.engine.state_ledger_ast`・`shibuya.foundation.rng`・`shibuya.foundation.vocab.actions`・`tests/_time_gates.py`・`tests/engine/time/__init__.py`
- 環境変数: `os.environ` をまるごと使う
- 決定の ID: 第 337

## [test_state_ledger_10b.py](../../../../../../tests/engine/test_state_ledger_10b.py)

10b: 状態台帳の宣言・追加 C の AST の検査・behavior-hash と full-hash・揺らし試験・保留の組の call_id。

- 公開の関数とクラス
  - `all_arms_capture`(関数)
  - `runtime_owners`(関数): 小さなラン(合成の全腕・古典、実資産 200 体の v3 既定と全腕+古典)の最後の checkpoint の owners。
  - `scanned`(関数)
  - `test_ast_check_catches_a_new_reader_of_a_no_column`(関数)
  - `test_ast_check_detects_a_new_declared_column`(関数)
  - `test_ast_check_fails_on_a_stale_allow`(関数)
  - `test_ast_check_fails_on_an_unresolved_dynamic_read`(関数)
  - `test_ast_check_fails_through_a_name_table`(関数): ``fatigue`` の読みは名前の表 INTERO_VARS / INTEROCEPTION_FIELDS 経由だけ(属性の読みは 0)。
  - `test_ast_check_fails_when_a_behavior_column_has_no_reader`(関数)
  - `test_ast_check_fails_when_hunger_is_declared_no`(関数)
  - `test_ast_check_passes_on_the_current_source`(関数)
  - `test_ast_false_positives_band_and_b4_hash_are_explicit`(関数): 材料 §2-4 の誤検出 2 列は、読みの場所と根拠つきで許す(黙って外さない)。
  - `test_behavior_hash_includes_the_behavior_rows_of_the_external_state`(関数): 親の答え 3: behavior-hash に外の状態の軸 1 が behavior の行が入る(no/diag の行は入らない)。
  - `test_checkpoint_combined_is_the_behavior_hash`(関数): 10e(E1): final は behavior-hash。〔改訂(第330・RET)〕旧い組み立て(``hash_scheme="full"``・``legacy_combined``)を
  - `test_coverage_fails_when_a_new_state_is_not_declared`(関数)
  - `test_e1_dead_columns_are_gone_from_the_soa`(関数): 10e(E1・Q9・A4): 死蔵の 5 列は SoA から消え、宣言のバイトが減った(agents −5 B/体・知覚 −16 B/体)。
  - `test_e1_r1_fleet_deferred_is_hashed_as_a_multiset`(関数): 10e(E1・検収 R1 の続き): 艦隊の繰り延べの list は並びに依らず、中身(多重集合)が変われば動く。
  - `test_e1_r1_replay_inbox_is_out_of_the_behavior_hash`(関数): 10e(E1・検収 R1): 再生の到着待ち(``run_day.replay_inbox``)は軸 1 no・軸 2 required(O96)。behavior-hash の項に
  - `test_e1_retire_and_the_retired_hash_are_gone`(関数): 〔改訂(第330・RET)〕10e(E1)の「消した死蔵の 3 列を旧い final の再現のためにハッシュの中で元の位置に並べ直す」口
  - `test_every_attribute_of_the_owner_classes_is_declared`(関数): 親の答え 1: 外の状態の持ち主のクラスの属性は、台帳の行か明示の除外の一覧のどちらかに必ず載る。
  - `test_full_hash_marks_absent_owners`(関数): 腕が立っていない持ち主は「無い」の印だけ(エラーにしない)。根の鍵が無いのは配線の誤り。
  - `test_hashes_are_deterministic_across_runs`(関数)
  - `test_hunger_restore_depends_on_the_configuration`(関数): 親の答え 6: hunger は構成で軸 2 が変わる(既定=要る・energy のとき=導出できる)。full には入れる。
  - `test_int_table_fast_path_is_canonical`(関数): 会話の管理の辞書(鍵が整数の組・値が整数)の速い道: 挿入順に依らず、型が混ざれば普通の道に回る。
  - `test_ledger_declarations_from_the_decisions`(関数)
  - `test_ledger_has_187_rows_in_two_axes`(関数): 材料の 163 行(SoA 98+外の状態 65)+10b-2 の棚卸しで足した外の状態 24 行(O66〜O89)+10d の 5 行(O90〜O94)
  - `test_ledger_matches_the_actual_soa_columns_and_types`(関数): 表と実際の SoA の列名と型が一致する(列が増えたら表に無い→失敗)。
  - `test_memo_does_not_change_the_hashes`(関数)
  - `test_p1_full_hash_sees_the_order_of_ordered_rows`(関数)
  - `test_p1_ordered_rows_keep_the_insertion_order`(関数): 検収 2-1: 順序が挙動を決める行(O8 要旨の並び・O39 会話の管理)は辞書の挿入順を保つ。
  - `test_p2_end_of_day_differs_after_the_ledger_close`(関数)
  - `test_p2_end_of_day_hashes_are_reported_separately`(関数): 検収 2-2: 日の締めの後の 2 本を manifest の ``state_hashes_end_of_day`` に別に出す(台帳の無いランは
  - `test_p4_numpy_integers_take_the_same_bytes_as_python_ints`(関数): 検収 2-4: 速い道は Python の int と numpy の整数を同じに扱う。
  - `test_p5_ast_blind_spots_are_caught`(関数): 検収 2-5 の表の 5 つの書き方をそのまま: どれも捕まる(読みとして数える/解決できない読み)。
  - `test_p5_true_self_updates_are_still_not_reads`(関数)
  - `test_p6_runtime_check_catches_an_undeclared_attribute`(関数)
  - `test_p6_runtime_owner_instances_are_fully_declared`(関数): 検収 2-6: 実行時のインスタンスの ``vars()`` を台帳+除外の一覧に突き合わせる(子クラス・入れ替わるクラスも)。
  - `test_pending_tuple_carries_fire_tick_and_call_id`(関数)
  - `test_t1_deleting_the_dead_columns_changes_nothing`(関数): T1(10e・E1): 死蔵 5 列を消した後の既定の final は behavior-hash そのもの。
  - `test_t2_behavior_hash_equals_the_final_after_deleting_the_non_behavior_columns`(関数): 10e で behavior でない列を消して final を ``state_hash()`` で計算すると、10b の behavior-hash と一致する。
  - `test_t2_call_id_on_the_fleet_and_replay_paths`(関数): 検収 4-2: 艦隊の到着・艦隊の終端の drain・再生の到着・再生の終端の 4 つの道でも、保留の組は 13 要素・
  - `test_t2_exclude_equals_deleting_the_columns`(関数): ``state_hash(exclude=S)`` == 「S を宣言から消した ``state_hash()``」(10e の手順の前提・材料 §2-3)。
  - `test_t4_full_hash_detects_one_element_of_required_external_state`(関数)
  - `test_t4_soa_rows_move_the_hashes_by_their_axes`(関数)
  - `test_t5_and_t1_on_real_assets`(関数): 実資産(W16+W17・計画実行層・エネルギー)300 体 1 日。〔改訂(第330・RET)〕前は plan_activity(K15)も揺らした
  - `test_t5_perturbing_no_columns_changes_nothing`(関数)
  - `test_t5_weight_kg_is_read_only_at_initialization`(関数): ``weight_kg`` は behavior(A2 b)だが読むのは初期化だけ=途中で揺らすと behavior-hash だけが動き、
  - `test_t6_behavior_columns_do_not_depend_on_the_configuration`(関数): 構成を変えても behavior の列の集合は表から決まる(A2 (b))。age・sex は v1 の構成でも behavior。
  - `test_t7_gate_is_the_share_of_the_whole_wall_clock`(関数): T7 の門の形の単体: 割合の門は宣言値を超える checkpoint でも、全体に占める割合が小さければ通す。
  - `test_t7_hash_cost_within_the_declared_cap`(関数): T7(10e で門の形を確定・ユーザー決定 10-12=10f のアジェンダ §6-2): **門は checkpoint のハッシュの壁時計が
  - `test_to_state_is_canonical_and_strict`(関数)
  - `test_two_day_run_reports_both_hashes_every_day`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.cli`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.engine.state_hashes`・`shibuya.engine.state_ledger`・`shibuya.engine.state_ledger_ast`・`shibuya.engine.systems.decide`・`shibuya.engine.systems.llm_io`・`shibuya.engine.systems.run_end`・`shibuya.engine.systems.state_io`・`shibuya.foundation.hashing`・`shibuya.foundation.soa`・`shibuya.world.model.percept_state`・`shibuya.world.model.state`・`tests/_places.py`・`tests/engine/test_tape_deferred.py`・`tests/golden_env.py`・`tests/llm/test_fleet.py`
- 読む試験: `tests/engine/memory/test_mr65_guards.py`
- 決定の ID: 10-06/§6・10-12・11-01・11-03/§3・第 321・第 330・第 346

## [test_store_choice.py](../../../../../../tests/engine/test_store_choice.py)

D-120 7c: **想起優先の候補合成**(N6 (a))・**到達可能性**(N7 (a))・**決め手**(N8 (a))・B5 の店の項(v1.3)のテスト(第298)。

- 公開の関数とクラス
  - `item`(関数)
  - `masks`(関数)
  - `put`(関数)
  - `resolver`(関数)
  - `setup`(関数)
  - `test_arm_switches_are_checked`(関数)
  - `test_reachability_is_a_capped_constraint_not_a_distance_decay`(関数)
  - `test_reasons_by_hour_and_first_visits_and_storefront_share`(関数)
  - `test_recall_first_is_array_ops`(関数): P4: 想起優先と到達可能性は 1 体の ≤ 32 行の配列演算(for/while を書かない)。
  - `test_recall_picks_recallable_fitting_reachable_stores_by_precision`(関数)
  - `test_recall_respects_fit_open_and_aspiration`(関数)
  - `test_resolver_uses_recall_first_only_with_classical_and_unnamed_targets`(関数)
  - `test_run_default_is_unchanged_and_store_choice_is_reported`(関数)
  - `test_store_item_templates_and_cap`(関数)
  - `test_store_rows_compete_with_episodes_in_recall_and_dedupe_by_store`(関数)
  - `world`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.cli`・`shibuya.engine.chooser`・`shibuya.engine.commit`・`shibuya.engine.memory`・`shibuya.engine.poi_target`・`shibuya.engine.run`・`shibuya.engine.store_choice`・`shibuya.engine.store_memory`・`shibuya.foundation.text.channels`・`shibuya.foundation.text.templates`・`shibuya.perception.renderer`・`shibuya.world.model.state`
- 決定の ID: D-120・第 298・第 333

## [test_store_memory.py](../../../../../../tests/engine/test_store_memory.py)

D-120 7a: **店の評価の記憶**(N1 (a)・N2 (i)(iii)・N4 (a)・N5 (a)・第296)のテスト。

- 公開の関数とクラス
  - `ep`(関数)
  - `layer`(関数)
  - `row_of`(関数)
  - `runs`(関数)
  - `table`(関数)
  - `test_decay_modes`(関数)
  - `test_default_has_no_store_table_and_store_on_keeps_behavior`(関数)
  - `test_full_table_evicts_the_lowest_store_score`(関数)
  - `test_non_poi_objects_and_other_kinds_are_not_store_rows`(関数)
  - `test_own_visits_write_valence_from_the_result_and_merge_by_poi`(関数)
  - `test_reading_needs_the_arm`(関数)
  - `test_several_store_events_for_one_agent_in_one_tick_merge`(関数)
  - `test_sigma_table_and_weights`(関数)
  - `test_signage_rows_come_only_from_the_first_sight_episode`(関数)
  - `test_store_columns_only_in_the_arm_and_declare_24_bytes_per_row`(関数)
  - `test_store_memory_needs_memory_and_checks_its_knobs`(関数)
  - `test_store_readers_and_writer_rounds_are_array_ops`(関数): P4: 読み口と 1 回の書き込みに for/while を書かない(体数比例の逐次ループなし)。
  - `test_store_rows_and_known_stores`(関数)
  - `test_store_summary_in_the_manifest`(関数)
  - `test_valence_of_result`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.familiarity`・`shibuya.engine.memory`・`shibuya.engine.run`・`shibuya.engine.store_memory`・`tests/golden_env.py`
- 決定の ID: D-120・第 296・第 330

## [test_t3_manifest.py](../../../../../../tests/engine/test_t3_manifest.py)

T3(冗長方程式の毎期検算)が run manifest に載る(D-85 (a)・ユーザー決定 2026-09-17)。

- 公開の関数とクラス
  - `test_a_one_day_run_reports_t3_as_not_run`(関数)
  - `test_a_run_without_a_ledger_has_no_t3`(関数)
  - `test_the_census_out_does_not_move_the_manifest_or_the_checkpoint`(関数): ``--census-out`` を渡しても manifest は 1 欄も動かない(t3_ok も None のまま)。
  - `test_the_month_break_run_puts_t3_in_the_manifest`(関数)
  - `test_the_month_break_run_puts_t3_in_the_monthly_mer`(関数): 月次 MER の戻りにも同じ答えが出る。**固定表 parquet の列は増えない**(§2.4)。
- import している内部モジュール: `shibuya.cli`・`shibuya.economy.census`・`shibuya.engine.run`・`shibuya.world.model.state`
- 決定の ID: D-85

## [test_tape.py](../../../../../../tests/engine/test_tape.py)

engine.tape のテスト: 1呼=1行 Parquet(zstd)・ブロック intern・完全一致リプレイ。

- 公開の関数とクラス
  - `test_block_id_is_content_addressed`(関数)
  - `test_duplicate_keys_are_counted`(関数)
  - `test_empty_tape_is_readable`(関数)
  - `test_missing_tape_raises`(関数)
  - `test_parquet_is_zstd_and_schema_is_fixed`(関数)
  - `test_replay_hit_and_miss`(関数)
  - `test_replay_key_is_all_four_fields`(関数)
  - `test_write_read_roundtrip`(関数)
- import している内部モジュール: `shibuya.engine.tape`

## [test_tape_deferred.py](../../../../../../tests/engine/test_tape_deferred.py)

D-58 テープ繰り延べ行: 録画→再生が**繰り延べごと**一致する(C7 受入の停止句)。

- 公開の関数とクラス
  - `assert_same_run`(関数)
  - `common`(関数)
  - `fleet_servers`(関数)
  - `make_client`(関数)
  - `record_and_replay`(関数): 同じ設定で 艦隊ラン(録画)→ テープ再生 を回して両方の結果を返す。
  - `test_a_run_without_deferrals_writes_the_same_rows_as_before`(関数): mock ラン(繰り延べ 0)は行数=呼数・全行 deferred 0・observed_tick −1。
  - `test_a_v1_tape_is_still_readable`(関数): 版1 のテープ(3 列なし)は全行 ``deferred=0``/``observed_tick=-1`` として読める。
  - `test_a_v1_tape_replays_a_whole_run`(関数): 版1 テープでの ``run_day(mode='replay')`` が版2 と同じ結果になる(後方互換)。
  - `test_lookup_raises_on_a_deferred_row_and_lookup_row_returns_it`(関数): ``lookup``(文字列契約)は繰り延べを例外に、``lookup_row`` は値で返す。
  - `test_queue_full_run_replays_bit_for_bit`(関数): キュー満杯を強制した艦隊ランを録画→再生: 繰り延べも含めて完全一致。
  - `test_replay_of_a_deferred_tape_makes_no_intent_for_that_call`(関数): 繰り延べ行はパースも未定義行動5段も通らない(=待機 intent を作らない)。
  - `test_t2_fleet_record_equals_replay_on_the_default_final`(関数): 10e(E1・検収 R1・T2): 艦隊で録ったランとその再生が、既定の final(behavior-hash)で全 checkpoint 一致する。
  - `test_timeout_run_replays_bit_for_bit`(関数): タイムアウト(=発射より**後の tick** で観測)も同じ tick で再現される。
  - `test_writer_counts_deferred_rows`(関数)
- import している内部モジュール: `shibuya.engine.run`・`shibuya.engine.state_ledger`・`shibuya.engine.tape`・`shibuya.foundation.manifest.schema`・`shibuya.llm.fleet`・`shibuya.world.model.state`・`tests/engine/test_tape_wiring.py`・`tests/golden_env.py`・`tests/llm/test_fleet.py`
- 読む試験: `tests/engine/test_10a_review_fixes.py`・`tests/engine/test_response_delay.py`・`tests/engine/test_state_ledger_10b.py`・`tests/engine/test_version_bump_10e.py`・`tests/perception/facts/test_percept_is_scratch.py`
- 決定の ID: D-56・D-58・第 330

## [test_tape_wiring.py](../../../../../../tests/engine/test_tape_wiring.py)

engine.llm_bridge の結線テスト(録画テープ・δ_think レーン・record/replay の同一性)。

- 公開の関数とクラス
  - `BoomLLM`(クラス): 呼ばれたら落ちるクライアント(**リプレイで実LLMへ落ちない**ことの証拠)。
  - `recorded`(関数)
  - `test_bridge_writes_every_call_to_the_tape`(関数)
  - `test_delta_think_lanes_match_the_cognition_design`(関数)
  - `test_parse_error_rate_is_zero_with_the_mock`(関数): B11 実測「2行形の書式順守=1.000」の再現(MockLLM は必ず2行形)。
  - `test_real_renderer_record_replay_is_bit_for_bit_on_a_synthetic_world`(関数): 合成世界+**本物のレンダラ**でも録画→再生が完全一致・テープ外 0。
  - `test_record_and_replay_at_five_thousand_agents`(関数): C3 受け入れ: 5,000 体の 1 シミュ日を録画→リプレイで**同一ハッシュ・テープ外0**。
  - `test_record_mode_produces_a_tape_with_one_row_per_call`(関数)
  - `test_replay_hits_the_tape_and_never_calls_a_live_model`(関数)
  - `test_replay_mode_requires_a_tape`(関数)
  - `test_replay_reproduces_the_run_bit_for_bit_with_zero_misses`(関数)
  - `test_replay_with_a_different_seed_misses_the_tape`(関数)
  - `test_stub_renderer_hash_is_stable_within_a_five_minute_bucket`(関数)
  - `test_stub_renderer_path_still_records_and_replays`(関数): ``renderer="stub"`` の安い経路も同じ性質を保つ(テストの逃げ道が生きている)。
  - `test_t_apply_uses_the_lane`(関数)
  - `test_tape_miss_is_counted_and_does_not_fall_back`(関数)
  - `test_the_default_renderer_is_the_real_one`(関数): ``run_day`` の既定は本物の ``perception.renderer.Renderer``(C3 結線)。
  - `test_the_five_diagnostic_rows_exist`(関数)
  - `test_the_two_prompt_hashes_are_both_deterministic_and_different`(関数): ``BridgeResult.prompt_hash``(レンダラ blake3)と ``tape_prompt_hash``(テープ鍵)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.llm_bridge`・`shibuya.engine.run`・`shibuya.engine.tape`・`shibuya.llm`・`shibuya.llm.mock`・`shibuya.perception.renderer`・`shibuya.world.model.state`
- 読む試験: `tests/engine/processes/test_rng_scheme_10c.py`・`tests/engine/test_10a_review_fixes.py`・`tests/engine/test_activation_10e.py`・`tests/engine/test_response_delay.py`・`tests/engine/test_tape_deferred.py`・`tests/engine/test_version_bump_10e.py`・`tests/perception/facts/test_percept_is_scratch.py`
- 決定の ID: D-56

## [test_two_layer_activity.py](../../../../../../tests/engine/test_two_layer_activity.py)

行為と活動の二層 — 段 2(エンジンの活動層・D-116・第276)。

- 公開の関数とクラス
  - `V3LLM`(クラス): 語彙 v3 の 5 ラベル形を返す台本 mock(行動・対象・活動・まで を固定)。
  - `test_activity_kind_mapping`(関数)
  - `test_activity_line_budget_and_filters`(関数)
  - `test_activity_off_is_the_current_behaviour`(関数)
  - `test_arrival_and_failure_settle_the_activity`(関数)
  - `test_b4b_activity_line_is_byte_identical_in_a_cell`(関数)
  - `test_bridge_role_words_fall_back_to_none_and_hints_carry_in_v3`(関数)
  - `test_cell_block_wakes_are_suppressed_during_an_activity`(関数)
  - `test_cell_rows_count_everyone_in_the_cell_top_two`(関数)
  - `test_checkpoint_includes_the_activity_text`(関数)
  - `test_expiry_candidate_at_the_until_tick`(関数)
  - `test_expiry_condition_is_outside_the_refractory_table`(関数)
  - `test_expiry_wakes_agents_in_a_v3_run`(関数)
  - `test_next_schedule_uses_the_plan_boundary_table`(関数)
  - `test_queue_delegates_to_eat_or_buy`(関数)
  - `test_queue_without_a_poi_is_bad_target`(関数)
  - `test_renderer_v3_expiry_reason_and_failure_options`(関数)
  - `test_resting_bodies_recover_fatigue_every_ten_ticks`(関数)
  - `test_undefined_falls_back_to_none_in_v3`(関数)
  - `test_until_resolution_rules`(関数)
  - `test_v1_ignores_the_activity_switch`(関数)
  - `test_v3_option_and_word_tables_are_the_compat_reading`(関数)
  - `test_v3_run_checkpoints_carry_the_activity_hash_and_are_deterministic`(関数)
  - `test_wander_bad_target_fails_as_bad_target`(関数)
  - `test_wander_destinations_are_within_the_radius_and_deterministic`(関数)
  - `test_wander_run_walks_near_and_keeps_walking`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.activity`・`shibuya.engine.arbiter`・`shibuya.engine.commit`・`shibuya.engine.llm_bridge`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.foundation.hashing`・`shibuya.foundation.text.channels`・`shibuya.foundation.text.templates`・`shibuya.foundation.types`・`shibuya.foundation.vocab.actions`・`shibuya.llm`・`shibuya.perception.renderer`・`shibuya.world.facts.mock_schedule`・`shibuya.world.facts.weekly_reader`・`shibuya.world.model.state`・`tests/golden_env.py`
- 決定の ID: D-116・第 275・第 276・第 330

## [test_two_phase.py](../../../../../../tests/engine/test_two_phase.py)

二相コミットのテスト: Phase B の資源裁定・順序不変(T3)・**書き込み口が1本であることの静的検査**。

- 公開の関数とクラス
  - `test_arbitration_is_permutation_invariant`(関数)
  - `test_capacity_limits_the_winners`(関数)
  - `test_conversation_partner_capacity_is_one`(関数)
  - `test_earlier_t_notice_wins_before_the_hash`(関数): pk の第1要素=気づいた時刻(δ_perc)。先に気づいた人が先に取る(§2.3)。
  - `test_every_hot_path_declares_its_sequential_loops`(関数): P4「逐次ループの新設は宣言必須」= モジュール docstring に『逐次ループ宣言』がある。
  - `test_free_intents_never_contend`(関数)
  - `test_frozen_state_rejects_direct_updates`(関数): resolve の外からの直接更新は例外(運用設計書 §2.2「atomic 演算による直接更新は禁止」)。
  - `test_losers_get_the_failure_code`(関数)
  - `test_no_python_loop_over_agents_in_engine_hot_paths`(関数): P4: エンジンのホットパスに**個体数ぶんの逐次ループ**を書かない。
  - `test_one_per_agent_keeps_the_llm_intent_over_the_engine_step`(関数)
  - `test_only_resolve_writes_to_the_world`(関数): ``.writable(`` を**呼ぶ**のは engine/resolve.py だけ(=世界への書き込み口は1本)。
  - `test_phase_c_outcome_is_independent_of_intent_order`(関数): T3 相当: Phase A の intent の並び順を変えても Phase C の結果は同一。
  - `test_stock_zero_means_nobody_wins`(関数)
  - `test_thaw_is_never_called_outside_the_state_modules`(関数): ``.thaw(`` は書き込みガードの解除口。呼び出しは agents/state.py・world/state.py の内部だけ
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.commit`・`shibuya.engine.resolve`・`shibuya.engine.systems.table`・`shibuya.world.model.state`・`tests/_places.py`
- 決定の ID: 第 330

## [test_undefined_action.py](../../../../../../tests/engine/test_undefined_action.py)

未定義行動5段のエンジン側結線(行動契約書 §7)+ 書式エラー率の診断行。

- 公開の関数とクラス
  - `GarbledLLM`(クラス): **わざと書式を壊した** mock(書式エラー率 > 0 の対照)。
  - `WordLLM`(クラス): 常に同じ行動語(表層形)を返す台本 mock。
  - `test_dictionary_mapping_keeps_the_engine_running_on_surface_forms`(関数): 全員が「買う」と言っても、段0 の写像で購入 intent になる(未定義行動は増えない)。
  - `test_garbled_output_is_still_recorded_verbatim_on_the_tape`(関数)
  - `test_parse_error_rate_is_zero_with_the_mock_and_positive_when_garbled`(関数)
  - `test_role_actions_are_parsed_but_land_on_the_safety_valve`(関数): §2.2 の役割語は読めるが効果先が C4。当面は待機へ(権限検査は engine の宿題)。
  - `test_stage0_maps_surface_forms_to_engine_action_codes`(関数)
  - `test_stage1_records_and_falls_back_to_waiting`(関数)
  - `test_stage2_needs_n_distinct_agents_through_the_bridge`(関数)
  - `test_tape_writer_can_be_shared_by_a_bridge_and_closed_once`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.commit`・`shibuya.engine.llm_bridge`・`shibuya.engine.run`・`shibuya.engine.tape`・`shibuya.foundation.vocab.actions`・`shibuya.llm`・`shibuya.llm.undefined`
- 決定の ID: D-56

## [test_version_bump_10e.py](../../../../../../tests/engine/test_version_bump_10e.py)

10e(版上げ 1 回目)の試験: E2 の期限つきの辞書の掃除・O64 の分類の確かめ(E1 の試験は状態台帳の試験の中)。

- 公開の関数とクラス
  - `purge_runs`(関数): 合成世界 300 体・語彙 v3・2 日。掃除あり(既定)と、掃除を止めた(``purge_expired`` を何もしない)ラン。
  - `test_e2_dicts_stay_bounded_over_days`(関数): 掃除ありの辞書の大きさは日をまたいでも増え続けない(止めたランは日数に比例して増える)。
  - `test_e2_o64_signage_exposures_are_empty_at_every_checkpoint`(関数): O64 の ``renderer.signage_exposures`` は tick の中だけの口=checkpoint の時点では常に空(no のままでよい根拠)。
  - `test_e2_purge_does_not_change_behavior`(関数): 掃除を止めたランと、呼数・行動の件数・起床の内訳・各呼の prompt_hash が同じ(期限切れは「無い」と同じ)。
  - `test_e2_purge_expired_drops_only_expired_entries_and_reads_stay_the_same`(関数): 期限 ``<= tick`` の項だけを落とす。落とした後も、その tick から先の読み(拒否・相手別と話者別の不応期)は同じ。
  - `test_e4_default_rng_scheme_is_counter_and_stateful_is_the_old_switch`(関数): 〔改訂(第330・RET)〕方式は counter だけ。``stateful``・``--rng-scheme``・``k19_counters`` の方式の引数を消した
  - `test_e4_l1_tape_meta_carries_the_rng_layout_and_old_counter_tapes_stop`(関数): L1: テープの脇の meta に鍵の配置の印(``rng_layout``)。10c〜10f の counter で録ったテープ(印が無い)は再生で
  - `test_e4_l2_load_population_and_three_argument_samplers_follow_the_engine`(関数): L2: ``load_population(n=…)`` は engine と同じ鍵の並べ方(counter)。3 引数の抽出の差し替え(凍結した測りの道具)も
  - `test_e4_l3_checkpoints_payload_is_version_2`(関数): L3: CLI の checkpoints の JSON は版 2(``combined`` は既定で behavior-hash)。
  - `test_e4_recorder_groups_by_seed_u8`(関数): U8: 束ねる鍵に master seed を入れた=seed の違う同じ用途名・同じカウンタの流れを重なりと数えない。
  - `test_e4_u2_next_key_is_no_longer_a_shifted_copy`(関数): U2(既知の答え): 旧の並び(鍵を 0 語目に置く)では「鍵 d+1 の流れ」が「鍵 d の流れを 1 ブロック(4 語)ずらした写し」に
  - `test_e4_u2_two_day_run_has_independent_day_streams`(関数): U2: 2 日のラン(合成世界・counter)で、日の鍵の流れ(配送・工事)はどれも重ならない=日ごとの差を主張に使える。
  - `test_e5_a_version_3_tape_reads_as_day_0_and_replays`(関数): 旧版(版 3)のテープは「日=0」として読める: 新しい 7 列は空で埋まり、鍵(tick=日の中の tick=T)で再生できる。
  - `test_e5_b5_b6_texts_rebuild_the_prompt_hash`(関数): B5 は列に直接・B6 は intern(K1): 共有ブロック 6 本+B5+B6 の本文から ``prompt_hash`` を作り直せる(再描画の検算)。
  - `test_e5_key_has_the_day_through_T`(関数): 鍵に日(A8 の 1): 2 日のランのテープの tick は通しの T(1 日目は 1,440 以上)・鍵は日をまたいで衝突しない。
  - `test_e5_recalled_memory_identity_and_acquaintances`(関数): 引いた記憶の同定(A8 の 2)と「(知人)」の相手の id・出どころの予約(A8 の 3)。
  - `test_e5_schema_is_version_4_and_appends_seven_columns`(関数)
  - `test_e5_t1_fleet_rows_carry_b5_b6_and_rebuild_the_prompt_hash`(関数): T1: 艦隊の経路(``FleetBridge``)の応答の行と繰り延べの行にも B5・B6 が入り、``prompt_hash`` を本文から作り直せる。
  - `test_e5_t3_recalled_identity_matches_the_memory_table`(関数): T3: 引いた記憶の同定 3 列を、想起した時点の記憶の表(``mem_tick``・``mem_kind``・``mem_object``・店の行は
  - `v4_tape`(関数): 世界資産 300 体・1 日・語彙 v3・記憶 on・関係 on(初期の関係辺がある=知人の印が出る)。
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.conversation`・`shibuya.engine.memory`・`shibuya.engine.rng_audit`・`shibuya.engine.run`・`shibuya.engine.state_ledger`・`shibuya.engine.systems.state_io`・`shibuya.engine.tape`・`shibuya.foundation.hashing`・`shibuya.foundation.rng`・`shibuya.world.facts.population_reader`・`shibuya.world.laws.switch_rate`・`shibuya.world.model.state`・`tests/_data_ids.py`・`tests/engine/test_tape_deferred.py`・`tests/engine/test_tape_wiring.py`・`tests/llm/test_fleet.py`
- 決定の ID: 11-01・第 330

## [test_vocab_v2_eat.py](../../../../../../tests/engine/test_vocab_v2_eat.py)

語彙 v2「食事」のエンジン側 — D-71 §3 E(飲食店オブジェクトの affordance)。

- 公開の関数とクラス
  - `WordLLM`(クラス): 常に同じ行動語(表層形)を返す台本 mock(``test_intent_mode_open.WordLLM`` と同じ)。
  - `test_a_full_run_records_meals_and_closes_the_books`(関数)
  - `test_action_usage_of_the_default_run_carries_the_v1_version`(関数)
  - `test_action_usage_reaches_the_run_manifest`(関数)
  - `test_closed`(関数): 開店前(既定 10:00-22:00)は ``CLOSED``。
  - `test_eating_moves_money_to_the_shop_and_conserves`(関数)
  - `test_eating_relieves_hunger_and_keeps_the_agent_in_the_shop`(関数)
  - `test_money_short`(関数): 所持金 < 価格 は ``MONEY_SHORT``(店の 1 tick 受け入れ数で落選した分は別コード)。
  - `test_not_in_eatery`(関数): 飲食店が無いセルに居る体は ``NOT_IN_EATERY``(``BAD_TARGET`` ではない)。
  - `test_stage0_dictionary_v3_grounds_eating_into_the_new_word`(関数): 「食べる」は v1 では 購入、v2 では **食事** に着地する(段0 辞書 v3)。
  - `test_the_declared_dwell_is_expedient_and_reuses_the_existing_seat_machinery`(関数): 所要時間 20 分は**契約行の宣言値**(専用タイマーは未実装=在席の回転率に従う)。
  - `test_the_default_run_is_byte_identical`(関数): 既定(v1)の checkpoint・呼数・行動分布は、語彙 v2 を足しても 1 ビットも動かない。
  - `test_the_eat_resource_is_the_shop_like_a_purchase`(関数): 食事は購入と**同じ資源**(店の 1 tick 受け入れ数)を奪い合う=満員は落選になる。
  - `test_the_eat_target_is_an_eatery_poi_in_the_same_cell`(関数)
  - `test_the_v1_apply_table_is_untouched`(関数)
  - `test_unknown_vocab_version_is_refused`(関数)
  - `test_v2_is_a_different_run_but_still_conserves`(関数): v2 は**別の値**(mock の抽選語彙も 13 語になる)。保存則と在庫は破れない。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.commit`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.foundation.vocab.actions`・`shibuya.llm`・`shibuya.world.facts.mock_schedule`・`shibuya.world.model.state`
- 決定の ID: D-71・第 274

## [test_waste_sink_report.py](../../../../../../tests/engine/test_waste_sink_report.py)

第304 Q135 (a)(小さいもの 第 2 批④): ラン要約の廃棄帯=**店だけの静的な帯**+内訳 3 つ(報告だけ)。

- 公開の関数とクラス
  - `test_monthly_census_uses_the_store_band_and_the_store_collected_mass`(関数): 第305 Q137: 月次センサスの帯も店だけの帯(判定=店の回収量 t/日)・帯の意味を明記(報告だけ)。
  - `test_real_world_store_band_is_0_911_t_per_day_for_any_agent_count`(関数): 実世界(2,337 POI・初期在庫 64): 0.911 t/日 ±30% = 0.64〜1.18(体数に依らない)。
  - `test_run_summary_uses_the_store_band_and_lists_three_sources`(関数): 〔11-01 段 2 の 4・検収 M1〕腕 off(既定)では店の帯は外した売れ残りの廃棄率の期待=判定は非該当(None)・値は残す。
  - `test_static_store_waste_is_floor_of_stock_times_rate_times_mass`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.economy.anchors`・`shibuya.economy.census`・`shibuya.economy.goods`・`shibuya.world.assets`・`shibuya.world.laws.switch_rate`・`shibuya.world.model.state`・`tools/c7/c7lib.py`
- 決定の ID: 11-01・第 304・第 305

## [test_weather_calendar_10e.py](../../../../../../tests/engine/test_weather_calendar_10e.py)

10e B6(第330): 天気=再生日・太陽と影=暦の日付の規則(``calendar``)。

- 公開の関数とクラス
  - `test_b6_b3_words_body_heat_and_sun_follow_one_rule`(関数): README §E6-1 B6 のための注 (1)〜(3): 描画の天気(B3)・体感温度・日の出と日の入りの語が同じ規則
  - `test_b6_days_advance_and_only_the_environment_seed_moves_the_draws`(関数)
  - `test_b6_heat_uses_the_replay_weather_and_the_calendar_sun`(関数)
  - `test_b6_inside_the_window_replays_the_actual_day_and_takes_the_sun_from_the_calendar`(関数)
  - `test_b6_known_answer_calendar_on_the_replay_day_equals_legacy_but_the_label`(関数): 暦の日付が窓の中のランは、その日の実際の天気と影(代用なし)で回る・同じ設定の 2 回は全 checkpoint が同じ。
  - `test_b6_legacy_default_is_untouched`(関数): 〔改訂(第330・RET)〕前は「legacy は今のまま(影のある日に絞る・日の出は再生日の行)」を見た(legacy を消した)。
  - `test_b6_outside_the_window_samples_and_an_empty_stratum_widens_with_a_warning`(関数)
  - `test_b6_perturbed_draws_follow_the_day_counts_of_season_kind_and_type`(関数)
  - `test_b6_recomputed_heat_and_sun_equal_w13_when_the_dates_match`(関数): 実資産の 35 日すべて: 暦の日付=再生日なら、計算し直した WBGT・暑さ段・日の出・日の入りが W13 の値と同じ。
  - `test_b6_shadow_comes_from_the_calendar_date_or_the_nearest_with_a_warning`(関数)
  - `test_b6_solar_formulas_equal_the_build_stage`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.build.field.w13_weather`・`shibuya.build.geo.common`・`shibuya.cli`・`shibuya.engine.calendar`・`shibuya.foundation.text.normalize`・`shibuya.perception.renderer`・`shibuya.world.assets`・`shibuya.world.facts.mock_schedule`・`shibuya.world.laws.environment`・`shibuya.world.laws.runner`・`shibuya.world.model.solar`・`shibuya.world.model.state`
- 決定の ID: 第 330

## [test_wom.py](../../../../../../tests/engine/test_wom.py)

D-120 7b: **会話からの店の抽出**(N3 (a)・口コミ=伝聞の書き手・第297)のテスト。

- 公開の関数とクラス
  - `ex`(関数)
  - `table`(関数)
  - `test_a_reason_writing_llm_leaks_nothing_by_default`(関数): 第2波 §2A 項 1 (i): 理由欄に店名と評価語を書く LLM でも、既定(utterance)は抽出 0・伝聞の行 0。
  - `test_a_talking_llm_writes_word_of_mouth_rows_for_listeners_only`(関数): 旧の源(``wom_source="reason-target"``)で第297 の挙動を再現する(第2波 §2A 項 1 (ii))。
  - `test_chain_names_pick_the_store_nearest_to_the_speaker`(関数)
  - `test_default_has_no_wom_and_mock_extracts_nothing`(関数)
  - `test_extraction_is_per_call_string_work`(関数): P4: 抽出は呼ごとの文字列処理(体数に比例するループを書かない)=宣言が本文にある。
  - `test_hear_writes_only_the_listener_row_as_word_of_mouth`(関数)
  - `test_normalize_and_boundaries_and_store_like_words`(関数)
  - `test_person_refs_and_digit_only_names_do_not_match`(関数)
  - `test_queue_success_is_valence_zero_q77`(関数)
  - `test_reason_only_store_name_does_not_leak_to_listener_by_default`(関数): 第2波 §2A 項 1 (i)(ii): 理由欄(内心)にだけ店名がある v3 の応答 → 既定では聞き手の店の行が増えない・
  - `test_synthetic_tape_matches_20_of_20_and_unrelated_0`(関数)
  - `test_valence_needs_a_store_and_mixed_words_cancel`(関数)
  - `test_wom_source_switch_is_checked_and_on_the_cli`(関数): 第2波 §2A 項 1: ``--wom-source {utterance,reason-target}``(既定 utterance)・誤りは ValueError。
  - `test_words_inside_a_store_name_are_not_valence_words`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.cli`・`shibuya.engine.memory`・`shibuya.engine.run`・`shibuya.engine.store_memory`・`shibuya.engine.wom`・`shibuya.world.model.state`・`tests/golden_env.py`
- 決定の ID: D-120・第 297・第 298・第 330・第 333
