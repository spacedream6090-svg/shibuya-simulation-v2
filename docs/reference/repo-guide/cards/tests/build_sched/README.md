# tests/build_sched

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 10 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../tests/build_sched/__init__.py)

tests.build_sched — W17 スケジュール生成(build.sched)の単体テスト。

## [conftest.py](../../../../../../tests/build_sched/conftest.py)

tests.build_sched の共通フィクスチャ。

- 公開の関数とクラス
  - `data_dir`(関数): ``ctx.data`` 相当(プールだけ)。
  - `mock_week`(関数): その体の事実に**素直に従った**応答本文(= プロンプトの指示どおりの出力)。
  - `response_row`(関数): ``tools/gen/fleet_gen.py`` 形式の応答 1 行。
  - `simple_week`(関数): 検査に使う「素直な週」の応答本文(全て語彙内・重なりなし)。
  - `world_dir`(関数): W17 が読む最小の world_dir。
  - `write_pool`(関数): ``data/persona_pool_v2`` 相当を作る。
  - `write_population`(関数): ``w16_population.parquet`` 相当(W17 が読む列だけ)。
  - `write_responses`(関数)
- import している内部モジュール: `shibuya.build.sched.vocab`
- 読む試験: `tests/build_sched/test_trial.py`・`tests/build_sched/test_w17_ingest.py`・`tests/build_sched/test_w17_prompts.py`・`tests/build_sched/test_weekly_loader.py`

## [test_trial.py](../../../../../../tests/build_sched/test_trial.py)

D-68 下見(``build.sched.trial``): 層化・seed 決定論・逆関数法・文法・報告の機械検査。

- 公開の関数とクラス
  - `anchor`(関数): 本物のアンカー台帳(``docs/bench/anchors/commute_time_dist_r3.json``)。
  - `test_absent_days_follow_actor_rate`(関数): §2-5: 欠勤は第31表の行動者率で曜日ごとに引く(大標本で ±2pt)。
  - `test_block_kind_conflicts_and_derivation`(関数): ``block_kind`` と 活動語/場所語 の矛盾検出・現行形式からの派生写像。
  - `test_block_regex_allows_3_to_10_lines_and_bans_night_prep`(関数): ブロック形式 regex: 行は ``{3,10}``・**0〜3 時台の 支度/乗車 はマッチしない**。
  - `test_current_format_regex_line_bounds_per_arm`(関数): P1a は本番どおり ``{4,5}``・P1b は ``{3,10}``(文法を緩めた腕だけ活動数が動く)。
  - `test_duty_open_is_depart_plus_lead_and_length_clipped`(関数): 始業=出勤+``arrival_lead_min``(欠損は 30 分)・勤務長は [4h, 12h]。
  - `test_employment_mix_weights_sum_to_one`(関数): 決定項 2: 非正規の按分(パート/アルバイト/契約/嘱託/派遣)と自営業主 28:72 の重み和=1。
  - `test_identity_char_floor_is_80`(関数): 親判断(2026-09-11): 字数下限は**80 字**(失敗を弾く目的)・上限 420 は据置。
  - `test_identity_check_catches_the_four_bans`(関数): 段1: 字数 200〜420 と禁止 4 つ(固有名詞・数字・箇条書き・挨拶の定型)。
  - `test_inverse_cdf_is_monotone_and_uniform_within_bin`(関数): 累積は単調・ビン内は 15 分一様(端も含む)。
  - `test_mock_block_text_matches_its_own_regex`(関数): モック応答は自分の文法を満たす(= 文法が満たせる形であることの存在証明)。
  - `test_output_names_avoid_production_globs`(関数): 下見の出力名が本番 glob(``w17_responses*`` / ``w17_prompts*``)に**当たらない**。
  - `test_p0b_also_reports_a_repaired_variant`(関数): P0b だけは本番の ``repair`` を通した版も出す(= 前値と同じ土俵)。
  - `test_p1_system_changes_only_fewshot_times_and_line_rule`(関数): P1 の system は本番テンプレから**例示の時刻と行数規則だけ**が違う。
  - `test_p1_user_adds_employment_and_own_times`(関数): P1 の事実行に雇用形態と自分の出勤/帰宅 HH:MM(分単位)が載る(§1)。
  - `test_p2p_grammar_has_no_block_kind_and_uses_the_current_parser`(関数): P2′: 行は現行 W17 と同じ 3 列・区分の列は文法にも例示にも無い・パーサは ``V.parse_text``。
  - `test_p2p_max_tokens_is_1536_and_p2_stays_1024`(関数): P2′ の生成上限は 1,536(P2 の 1,024 で 65% が切断)。P2 は不変。
  - `test_p2p_states_time_fidelity_in_system_and_user`(関数): P2′ の system と user の**両方**に時刻の忠実さの指示が入る(P2 には入らない)。
  - `test_parse_blocks_finds_gap_sleep_and_kind_conflict`(関数): パーサ: 切れ目・就寝・``block_kind`` の矛盾を拾う(壊れた行はその行だけ捨てる)。
  - `test_production_prompt_does_not_read_trial_only_fields`(関数): ``pool_facts`` に足した下見専用欄を**本番 W17 の user プロンプトは読まない**。
  - `test_prompts_sha_differs_per_arm_and_reproduces`(関数): 腕ごとに ``prompts_sha256`` が違い、同じ腕は 2 回で一致する(改版の検出器)。
  - `test_real_anchor_reproduces_research_quantiles`(関数): アンカー台帳が答申 §6-3 の分位(正規 6:15/7:30/9:00)を再現する。
  - `test_report_splits_modified_rate_by_origin`(関数): 決定項 10: 修正率を **LLM 由来**(パース失敗・検査落ち)と**エンジン由来**に分ける。
  - `test_sample_and_windows_are_deterministic`(関数): seed 決定論: 2 回引いて標本も勤務窓も**バイト同値**。
  - `test_sample_is_stratified_and_identical_across_arms`(関数): 層化の体数は設計書 §4 の表どおり・**全腕で同じ体**(対応のある比較)。
  - `test_trial_parquet_has_weekly_columns_plus_block_kind`(関数): 下見 parquet は ``agents.weekly._COLUMNS`` をそのまま含み(物差しが読める)+``block_kind``/``arm``。
  - `test_v2_example_for_factless_bodies_is_scattered`(関数): 事実の無い体(非就業・来街・通学)は種別ごとの骨格+``_mix64`` の散らし・分は :00/:30 でない。
  - `test_v2_example_is_built_from_each_body_facts`(関数): 例示は **system ではなく user**・時刻は**その体の事実**(出勤/窓/帰宅)そのもの。
  - `test_v2_gate_thresholds_and_one_day_notes`(関数): v2 のゲート: parse 失敗 <0.02・被覆 ≥0.999 は合否・多様性と JSD は報告のみ。
  - `test_v2_ingest_adopts_raking_zero_and_reports_twelve`(関数): raking は 12% と 0% の両方を計算し、**採用は 0%**(エンジン由来の修正 0)。
  - `test_v2_one_day_grammar_and_max_tokens`(関数): 1 日モード: 文法・例示・指示が d0 だけ・``max_tokens`` は 320(切断 0 を保つ)。
  - `test_v2_production_writes_one_row_per_agent_with_safe_names`(関数): 本番は**層化なし・行数=体数**・名前は本番 glob に当たらない・隔離先が強制される。
  - `test_v2_promote_backs_up_the_old_assets`(関数): ``--promote``: 旧版を ``w17v1_backup/`` へ退避してからコピーする。
  - `test_v2_retry_failed_bumps_the_seed_once`(関数): ``--retry-failed`` + ``--seed-bump 1``: 落ちた体だけ・seed が +1・名前も別(最大 1 回)。
  - `test_v2_time_fact_repair_switch`(関数): ``--time-fact-repair``: 既定オフは**一致率を数えるだけ**・オンで行を動かして計数。
  - `test_windows_are_not_drawn_for_students_and_visitors`(関数): 通学者・来街者・非就業は窓を引かない(通学は本番のまま)。
  - `trial_world`(関数): 通勤者 ``N_BODIES`` 体(雇用形態が全種類)の世界+プール。
- import している内部モジュール: `shibuya.agents.weekly`・`shibuya.build.pop.w16_population`・`shibuya.build.sched.pool_facts`・`shibuya.build.sched.trial`・`shibuya.build.sched.vocab`・`shibuya.build.sched.w17_schedule`・`tests/build_sched/conftest.py`
- 決定の ID: D-68

## [test_w17_ingest.py](../../../../../../tests/build_sched/test_w17_ingest.py)

W17 取り込み: ストリーミング・最後の行を採る・ゲート・段階の 2 相・実データ。

- 公開の関数とクラス
  - `big_world`(関数): 1,000 体のモック世界(ストリーミング取り込みの規模テスト)。
  - `test_adaptive_budget_is_zero_when_repair_already_fills_the_gate`(関数): 修復だけで枠を使い切る応答(骸格になる=全件修正)では raking を止める。
  - `test_adaptive_budget_keeps_the_total_under_the_gate`(関数): 修復率を振っても **raking がゲートを割らせない**(D-W17 (iii) 修正率<20%)。
  - `test_broken_responses_only_lose_their_own_lines`(関数)
  - `test_cli_runs_and_accepts_shard`(関数)
  - `test_explicit_budget_overrides_the_adaptive_one`(関数): ablation: 固定予算(旧 12%)を渡すと適応を上書きする(JSD 差の感度試験用)。
  - `test_header_is_byte_identical_across_two_builds`(関数): ``W17.header.json`` が 2 回の構築でバイト一致する(D-W20 の再構築テスト)。
  - `test_last_row_wins_for_duplicate_ids`(関数): fleet_gen の resume で同じ id が二度書かれたら**最後の行**を採る。
  - `test_missing_responses_fall_back_to_skeleton`(関数): 応答の無い体は骸格で埋め、**修正率に全件計上される**(ゲートが落ちる)。
  - `test_notes_carry_no_non_deterministic_values`(関数): ヘッダの ``notes`` に時刻・壁時計・絶対パス・環境を入れない。
  - `test_output_columns_and_ordering`(関数)
  - `test_pilot_cli_writes_only_the_sample`(関数)
  - `test_pilot_ingest_reports_without_writing_assets`(関数)
  - `test_pilot_prompts_are_per_kind_and_deterministic`(関数)
  - `test_pilot_takes_up_to_per_kind_from_each_kind`(関数)
  - `test_real_population_prompts`(関数): 実データ: 件数=体数・平均入力トークン・プロンプト SHA を測って報告する。
  - `test_stage_freezes_when_responses_are_present`(関数): 応答があれば parquet + ゲート json を書き、``input_hash`` に応答 SHA が入る。
  - `test_stage_is_deterministic`(関数): 同じ入力で 2 回走らせて出力 SHA が一致する(D-W20 再構築テスト)。
  - `test_stage_writes_prompts_without_responses`(関数): 応答が無くても段階は落ちない(プロンプトだけ書いて「応答未取得」を報告)。
  - `test_streaming_ingest_at_scale`(関数): 1,000 体をシャード 2 本の応答から取り込む(ストリーミング・壁時計を報告)。
  - `test_write_pilot_prompts`(関数)
  - `test_write_schedule_roundtrips`(関数)
- import している内部モジュール: `shibuya.build.geo.common`・`shibuya.build.sched.run`・`shibuya.build.sched.vocab`・`shibuya.build.sched.w17_schedule`・`tests/build_sched/conftest.py`

## [test_w17_parse.py](../../../../../../tests/build_sched/test_w17_parse.py)

W17 行パーサ: 陽性/陰性・24 時越え・語彙外・壊れた行の落とし方(hypothesis 込み)。

- 公開の関数とクラス
  - `test_activity_synonyms_are_mapped`(関数)
  - `test_body_line_without_a_heading_is_dropped`(関数): 見出しの前に来た活動行は曜日が決まらないので捨てる。
  - `test_cross_midnight_in_heading_form`(関数)
  - `test_cross_midnight_is_split`(関数)
  - `test_cross_midnight_to_2400_is_not_split`(関数)
  - `test_day_heading_form_is_parsed`(関数): v3 の書式: 見出し行 ``dN`` の下の活動行に、その曜日が付く。
  - `test_empty_day_heading_yields_no_activity`(関数): 来街者の来訪日でない曜日=見出しだけ。
  - `test_format_body_has_three_columns`(関数)
  - `test_format_parse_roundtrip`(関数): ``format_line`` が書いた行は必ず読め、同じ活動に戻る(24 時越えは分割される)。
  - `test_format_schedule_emits_seven_headings`(関数)
  - `test_format_schedule_roundtrips_through_the_parser`(関数)
  - `test_mixed_forms_are_read`(関数): 見出し形と旧形式が混ざっても、旧形式は自分の曜日を優先する。
  - `test_old_flat_form_is_still_read`(関数): 旧形式(1 行に曜日)も互換で読める。
  - `test_one_line_sleep_across_midnight_is_the_new_form`(関数): 短縮形式: 日をまたぐ就寝は 1 行(2 行に割らせない)。
  - `test_parse_line_negative`(関数)
  - `test_parse_line_positive`(関数)
  - `test_parse_text_drops_only_broken_lines`(関数)
  - `test_parse_text_strips_think_block`(関数)
  - `test_parse_text_truncates_runaway_output`(関数)
  - `test_place_synonyms_are_mapped`(関数)
  - `test_synonym_fixes_are_not_counted_as_failures`(関数)
  - `test_trailing_noise_is_stripped`(関数)
  - `test_unmapped_words_are_still_dropped`(関数): 表に無い語は**寄せない**(勝手な既定語に落とさない)。1 文字の断片も落とす。
- import している内部モジュール: `shibuya.build.sched.vocab`

## [test_w17_prompts.py](../../../../../../tests/build_sched/test_w17_prompts.py)

W17 プロンプト生成: 決定論・fleet_gen 形式・seed=hash(agent)・種別別テンプレ・シャード。

- 公開の関数とクラス
  - `facts`(関数)
  - `test_activity_words_map_into_action_contract`(関数): 活動語 12 は全て行動契約書 §2.1 の「種別横断12語」へ写像できる。
  - `test_call_count_equals_agent_count`(関数): 呼数=体数(repeat 1)。
  - `test_every_prompt_carries_a_regex`(関数)
  - `test_every_prompt_has_exactly_one_plan_line`(関数): **勤務・通学・来訪のどれか 1 行が必ず入る**(第1回パイロットの退化への対処)。
  - `test_facts_windows_by_kind`(関数)
  - `test_place_set_drops_facts_the_agent_does_not_have`(関数): 事実にない場所語は regex から外す(固有名詞検査の代わりの構造検査)。
  - `test_prompt_fields_match_fleet_gen_format`(関数): ``tools/gen/fleet_gen.py`` が読む欄が揃っている(温度 0.7・repeat 1・thinking false)。
  - `test_prompt_tokens_within_budget`(関数): 入力トークン(共有 prefix 込み)の平均が目標以下(§1 予算・報告値)。
  - `test_prompts_are_deterministic`(関数): 同じ入力から 2 回作って SHA が一致する(§0-1 決定論)。
  - `test_regex_accepts_four_and_five_lines_per_day`(関数): 陽性: 各日 4-5 行 × 7 日はマッチする(末尾改行の有無どちらも)。
  - `test_regex_for_visitors_allows_only_the_visit_days`(関数): 来街者は**来訪日だけ活動行**・他の日は見出しだけ。
  - `test_regex_rejects_a_missing_day`(関数)
  - `test_regex_rejects_out_of_vocabulary_words`(関数)
  - `test_regex_rejects_places_the_agent_cannot_have`(関数): 無職の住民は「域外」を書けない(第2回パイロットで全活動が域外になった)。
  - `test_regex_rejects_trailing_space_and_old_format`(関数)
  - `test_regex_rejects_wrong_line_counts`(関数): 陰性: 1 日 3 行以下・6 行以上は通らない(第2回パイロットの 12 行/日を封じる)。
  - `test_regex_summary_is_deterministic`(関数)
  - `test_regular_visitor_school_day_cadence`(関数): ``visit_cadence == "school_day"`` の定期来街者は平日 5 日になる。
  - `test_residents_without_a_seat_get_an_outside_workplace`(関数): 勤務席の無い住民は**域外勤務**として facts に入る(パイロット id=11 の再発防止)。
  - `test_school_age_agents_always_get_a_school_line`(関数): 15 歳未満は学校セルが無くても通学として書く。
  - `test_seed_hypothesis_range`(関数)
  - `test_seed_is_deterministic_and_matches_prompt`(関数)
  - `test_seed_is_unique_over_population_scale`(関数): 39 万体規模で seed が衝突しない(2^53 剰余=衝突期待値 1e-5 件未満)。
  - `test_shard_bounds_are_checked`(関数)
  - `test_shards_partition_the_population`(関数)
  - `test_system_states_the_format_and_vocabulary`(関数): **日見出し形**の書式・例・語彙・規則が system に書かれている。
  - `test_system_templates_are_frozen_per_kind`(関数): 種別ごとに system が違い、共通部が先頭にある(prefix キャッシュが効く形)。
  - `test_user_prompt_carries_the_facts`(関数)
  - `test_wake_conditions_match_perception_contract`(関数): ``ACTIVITY_TO_WAKE`` は知覚契約書 §6 の計画境界 4 行(``WakeCondition``)と一致。
  - `test_write_prompts_streams_jsonl`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.build.sched.vocab`・`shibuya.build.sched.w17_schedule`・`tests/build_sched/conftest.py`

## [test_w17_repair.py](../../../../../../tests/build_sched/test_w17_repair.py)

W17 段2: 整合修復の 7 規則・骸格フォールバック・raking(答申 Q4-2 段2/段3)。

- 公開の関数とクラス
  - `facts`(関数)
  - `share`(関数)
  - `test_day_shift_clamps_the_first_and_last_block`(関数): 1 日の平行移動は先頭の開始を 0・末尾の終了を 1440 に切り詰める(範囲外にしない)。
  - `test_duty_is_clamped_into_the_plan_spec_window`(関数): 勤務は本人の勤務窓(PlanSpec/シフト)の中へ丸める。
  - `test_duty_on_a_non_working_day_becomes_rest_at_home`(関数)
  - `test_fill_does_not_touch_non_visit_days_of_visitors`(関数)
  - `test_fill_keeps_the_llm_activities`(関数)
  - `test_hour_curves_are_normalized`(関数)
  - `test_jensen_shannon_bounds`(関数)
  - `test_leisure_outside_opening_hours_is_moved`(関数): 閉店中(開店率 < 5%)に始まる店内活動は同じ日の最寄りの開店時間帯へ動く。
  - `test_negative_budget_is_clamped_to_zero`(関数)
  - `test_open_24h_shop_is_never_moved`(関数): 24 時間営業のコンビニがある物販店は深夜でも動かさない(閾値の陰性側)。
  - `test_open_share_is_built_from_plan_spec`(関数)
  - `test_overlap_is_resolved_by_shifting_the_later_block`(関数)
  - `test_rake_does_nothing_when_the_budget_is_zero`(関数): 修復だけでゲートの枠を使い切ったら raking しない(JSD は据え置き・報告する)。
  - `test_rake_respects_an_explicit_row_budget`(関数)
  - `test_raking_lowers_jsd_and_counts_moves`(関数): 全部 6 時始まりの勤務を、朝ピークのカーブへ寄せる。
  - `test_raking_never_creates_overlaps`(関数): 隣の活動の隙間の中でしか動かさない。
  - `test_raking_respects_the_move_budget`(関数)
  - `test_raking_rolls_back_when_it_would_make_things_worse`(関数): 全目的の JSD 最大値が下がらないときは丸ごと巻き戻す(較正の悪化を凍結しない)。
  - `test_skeleton_is_valid_after_repair`(関数): 応答全滅の埋めは、修復を通したあと**そのまま凍結できる形**になっている。
  - `test_sleep_is_inserted_for_residents`(関数)
  - `test_sleep_is_not_forced_on_agents_without_a_home_in_the_world`(関数)
  - `test_sleep_only_day_is_filled_from_the_skeleton`(関数): 第1回パイロットの退化(23/300 が 7 日とも「就寝」だけ)への対処。
  - `test_too_many_activities_are_capped`(関数)
  - `test_visitor_keeps_only_visit_days_with_entry_and_exit`(関数)
  - `test_zero_length_and_out_of_range_are_dropped`(関数)
- import している内部モジュール: `shibuya.build.sched.vocab`・`shibuya.build.sched.w17_schedule`

## [test_w20_calendar_1a.py](../../../../../../tests/build_sched/test_w20_calendar_1a.py)

第 3 期 3-1 構築側の段 W20cal(暦 1a・``build.sched.w20_calendar_1a``)の受入の試験。

- 公開の関数とクラス
  - `attrs`(関数): n 体の作り物(勤務・授業・空欄・duty_role・舞台の外・自宅を混ぜる)。
  - `build`(関数)
  - `materials`(関数)
  - `real5000`(関数)
  - `test_attributes_are_the_only_population_input`(関数): 関数の入力は属性の表だけ(W16 の版が変わっても、属性の読み口を差し替えれば同じ関数が使える)。
  - `test_blank_rules_and_school`(関数): 決まっていない予定は空欄・授業は月〜金(規則)で時間帯は空欄・土日は空欄。
  - `test_clipped_work_recomputes_the_return`(関数): 〔検収 低 1〕勤務の長さを [4h, 12h] に切った体の帰宅は終業+片道の通勤時間(終業 ≤ 帰宅)=どの勤務の行も
  - `test_day_weights_use_table_74_6_first`(関数): 曜日の重みは第74-6表の地位・勤務形態の行・職業の分かる duty_role の体だけ第74-9表の比を掛ける。
  - `test_deterministic_and_subset_invariant`(関数): 同じ属性なら同じ表・体の部分集合で作っても同じ行(体ごとの鍵=人口が変わっても作り直しにならない)。
  - `test_employment_status_from_the_persona_and_the_duty_role_redraw`(関数): 地位はペルソナの employment の 6 値を第6-2表の 6 区分へ写す(親の判断 2026-10-15 の 3)・duty_role の体だけ
  - `test_fixed_every_week_and_weekly_redraws_with_the_body_week_key`(関数): 正規(毎週固定)は週が変わっても同じ・非正規とシフトは週ごとの抽選(鍵=体・週・曜日)。
  - `test_guard_refuses_validation_tables_before_opening`(関数): 負の対照: 守りの間は検証側の名のファイル(どこにあっても)と r99 の許可の外を ``open`` の前に落とす。
  - `test_place_kinds_by_role_and_workplace`(関数): 勤務場所の種類は duty_role の表だけで決め、W16 の事業所の体は建物(W16 に職業の列が無い=親の判断 2026-10-15 の 1)。
  - `test_r99_file_lists_follow_the_parent_judgement`(関数): 構築側に開いてよいのは 4 本だけ・検証側(第14表・第15-1〜3表・第68-3表)は名で落とす(パターン台帳 §10)。
  - `test_read_guard_of_2_0_sees_no_validation_table`(関数): 2-0 の ``read_guard`` の形(監査フック)でも、材料の組み立ては検証側の名を開かない。負の対照つき。
  - `test_real_5000_rows_equal_the_stage_asset_when_present`(関数): 組んだ資産(data/world/v2_stage_3-1)があれば、同じ 5,000 体の行が一致する(段=関数を全員にかけただけ)。
  - `test_real_5000_table_shape_and_golden`(関数)
  - `test_real_materials_match_the_r99_primary_values`(関数): 材料の値が R-99 の親検収済みの値と一致(写し検査)。開いたのは構築側の 4 本だけ。
  - `test_rest_day_is_drawn_in_proportion_to_the_not_working_rate`(関数): 〔親の判断 第337 (2)〕休みの曜日=その曜日の働かない率(1 − 予定の率)に比例して 1 日(体・週の鍵・毎週固定の体は
  - `test_rows_columns_and_order`(関数)
  - `test_seat_beats_school_and_is_counted`(関数): 〔検収 中 1・親の判断 第337〕W16 の席(種別 0・2)があってペルソナが学校段階か学校のセルを持つ体は、席を優先して勤務の
  - `test_seat_but_nonworking_persona_is_blank`(関数): W16 の席(種別 0・2)があってもペルソナの employment が非就業なら勤務の約束は空欄(親の判断 第336 (3))・数える。
  - `test_times_are_the_31_36_inverse_with_the_lead_and_the_clip`(関数): 始業=出勤+片道の通勤時間・終業=帰宅−片道の通勤時間(勤務の長さは [4h, 12h] に切る)。
  - `test_w19_lists_the_build_inputs_and_families`(関数): W19 の資産表と層の元に W20cal の構築側の入力が載る(検証側の名は載らない)。
  - `test_weekday_rates_are_table_74_6_and_table_19_is_only_a_gauge`(関数): 曜日の予定の率は第74-6表の地位・勤務形態の曜日の率そのもの(実現値=予定の下限・親の判断 第336 (1))・週の日数は
  - `test_weekly_rest_day_for_employees_from_the_rules_table`(関数): 〔検収 中 2・親の判断 第337〕労働基準法 9 条の労働者(無期・有期・臨時)の体は、その週に 7 日とも勤務を引いたら 1 日を
- import している内部モジュール: `shibuya.build.audit.w19_freeze`・`shibuya.build.pop.w21_build`・`shibuya.build.sched.trial`・`shibuya.build.sched.w20_calendar_1a`・`shibuya.engine.calendar_shadow`・`tools/instruments/read_guard.py`
- 読む試験: `tests/build_sched/test_w20_w21_port.py`・`tests/engine/calendar/test_calendar_shadow.py`
- 決定の ID: R-99・第 336・第 337

## [test_w20_w21_port.py](../../../../../../tests/build_sched/test_w20_w21_port.py)

W21 → W20 の ``Attributes`` の口(``build.sched.w20_w21_port``・第 4 期 4-1 段 10 の材料)の試験。

- 公開の関数とクラス
  - `test_attributes_from_w21_has_the_19_fields_and_passes_the_calendar`(関数)
  - `test_lead_minutes`(関数)
  - `test_new_duty_words_are_keys_and_w16_default_is_unchanged`(関数)
  - `test_real_w21_people_pass_the_calendar`(関数)
  - `test_unknown_duty_role_stops`(関数)
  - `test_w20cal_param_hash_is_unchanged`(関数): 〔検収 中 1〕W20cal の ``params`` の ``duty_role_spec`` は組んだ資産(v2_stage_3-1)のヘッダと同じ=組み直しても
- import している内部モジュール: `shibuya.build.geo.common`・`shibuya.build.pop.attr_fns`・`shibuya.build.sched.w20_calendar_1a`・`shibuya.build.sched.w20_w21_port`・`tests/build_sched/test_w20_calendar_1a.py`

## [test_weekly_loader.py](../../../../../../tests/build_sched/test_weekly_loader.py)

``agents.weekly``: 語彙の二重定義一致・往復・計画境界の取り出し・バイト予算。

- 公開の関数とクラス
  - `frozen`(関数)
  - `test_apply_to_mock_schedule_overwrites_the_bases`(関数): 結線用の変換関数: 合成日課の拠点セルを W17 の当日の行き先で置き換える。
  - `test_boundary_events_replace_the_mock_five_slot_table`(関数): ``events_of_day`` の差し替え: tick 昇順・条件は活動語から決まる。
  - `test_bytes_per_agent_within_the_budget`(関数): M1(≤30KB/体)・M3(T0 習慣 ≤12.8KB/体)の内側にあることを実測して報告する。
  - `test_load_weekly_returns_none_without_asset`(関数)
  - `test_load_weekly_roundtrip`(関数)
  - `test_projected_bytes_at_full_scale`(関数): 39 万体・週 42 活動での投影値(実資産が無くても数えられる形で報告)。
  - `test_restrict_to_reorders_and_rejects_unknown_ids`(関数)
  - `test_schedule_hash_is_stable_and_sensitive`(関数)
  - `test_target_cell_at_uses_the_table_then_the_fallback`(関数)
  - `test_vocabulary_double_definition_agrees`(関数): ``build.sched.vocab`` と ``agents.weekly`` の語彙・写像が一致する。
  - `test_wake_conditions_are_plan_boundaries`(関数)
- import している内部モジュール: `shibuya.agents.schedule`・`shibuya.agents.state`・`shibuya.agents.weekly`・`shibuya.build.sched.vocab`・`shibuya.build.sched.w17_schedule`・`tests/build_sched/conftest.py`
