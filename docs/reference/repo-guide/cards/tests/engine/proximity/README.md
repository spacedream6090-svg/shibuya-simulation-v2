# tests/engine/proximity

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 6 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../tests/engine/proximity/__init__.py)

(冒頭の説明なし)

## [test_index.py](../../../../../../../tests/engine/proximity/test_index.py)

第 2 期 2-2 段 11a: 近傍の索引 ``engine.spatial_index.SpatialIndex``(アジェンダ §2-1「近傍の列挙は総当たりと一致」)。

- 公開の関数とクラス
  - `test_index_is_read_only_after_build`(関数): 検収 L3: 索引の配列は読み取り専用・欄の付け替えと消すのは断る。
  - `test_keys_out_of_range_are_refused`(関数)
  - `test_pairs_match_bruteforce_600_points`(関数)
  - `test_pairs_never_cross_bands`(関数)
  - `test_subset_ids_and_point_queries`(関数)
  - `test_unit_members_and_counts`(関数)
  - `test_unit_members_many_matches_single`(関数)
  - `test_within_and_query_many_match_bruteforce`(関数)
- import している内部モジュール: `shibuya.world.model.spatial_index`

## [test_philox_array.py](../../../../../../../tests/engine/proximity/test_philox_array.py)

第 2 期 2-2(親の判断 10-14 の 1): 配列で回す Philox ``core.rng.philox_array`` が numpy の ``np.random.Philox`` と同じ出力。

- 公開の関数とクラス
  - `test_philox_array_equals_numpy_philox_on_10000_rows`(関数)
  - `test_philox_array_input_checks`(関数)
  - `test_unit_float_equals_generator_random_and_k19_layout`(関数)
- import している内部モジュール: `shibuya.foundation.rng`

## [test_rule.py](../../../../../../../tests/engine/proximity/test_rule.py)

第 2 期 2-2 段 11a: 判定の規則 ``ProximityRule``・切替口・気づく確率 p(d)(合成の体)。

- 公開の関数とクラス
  - `agents`(関数)
  - `test_d_default_is_the_talk_open_constant`(関数)
  - `test_d_switch_is_checked_and_the_cell_switch_is_removed`(関数): ``--proximity-d`` は感度の腕として残す。〔第346〕``--proximity cell`` の切替口(腕を選ぶ口・環境変数)は消した。
  - `test_edge_view_reach_equals_reach`(関数): 検収 M2: 同席と知人出現が共有する辺の見え方の「届く」は ``reach`` と同じ答え(単位は打ち切りの外でも届く)。
  - `test_layer_meter_counts_unit_occupancy`(関数)
  - `test_manifest_fields_cell_and_distance`(関数)
  - `test_notice_curve_passes_r62_two_points`(関数)
  - `test_notice_draws_are_counter_streams_stateless_and_uniform`(関数): 検収・親の判断 A1: 気づく抽選は 10c の counter の流れ(用途名 proximity.notice・k19 の並べ方=時刻の鍵・体・相手)。
  - `test_notice_range_prefilter_equals_the_full_definition`(関数): ``notice_range`` は float32 の距離で先に落とす(上位集合)=全部を ``_parts`` で見たときと同じ答え。
  - `test_notice_streams_pass_the_k19_overlap_check`(関数): K19 の重なりの検査の控え(StreamRecorder)に載り、重なりも作り直しも無い。
  - `test_noticed_needs_same_band_stage_and_cutoff`(関数)
  - `test_off_stage_cannot_talk_and_boundary_is_inclusive`(関数)
  - `test_other_band_1m_cannot_talk`(関数)
  - `test_other_cell_1m_can_talk_only_in_distance`(関数)
  - `test_resume_arm_check`(関数): 検収 M1: 再開の腕の検査(見出しの proximity が無ければ cell=〔第346〕cell の切替口は消した=再開できない)。
  - `test_rule_from_requires_poi_cell`(関数)
  - `test_rule_none_and_cell_mode_keep_the_current_judgement`(関数)
  - `test_same_cell_3m_cannot_talk_in_distance`(関数)
  - `test_same_unit_talks_without_distance_b5`(関数)
  - `test_sensitivity_arms`(関数)
  - `test_unit_needs_the_store_cell`(関数): 在席の印があっても、その店のセルの外に居る体(店を出て歩いている体)は単位に数えない。
- import している内部モジュール: `shibuya.engine.resolve`・`shibuya.engine.rng_audit`・`shibuya.foundation.rng`・`shibuya.world.model.proximity`
- 環境変数: `SHIBUYA_PROXIMITY`・`os.environ` をまるごと使う
- 決定の ID: R-62・R-79・第 346

## [test_runs.py](../../../../../../../tests/engine/proximity/test_runs.py)

第 2 期 2-2 段 11a: ランの単位の検査(アジェンダ §2-1 の不変条件のうちランが要るもの)。

- 公開の関数とクラス
  - `arm`(関数): 近接の腕(〔第346〕ランは常に distance=d だけを選ぶ)。
  - `distance_day`(関数)
  - `test_b5_near_rows_are_within_radius_or_unit`(関数)
  - `test_cli_proximity_d_arm`(関数)
  - `test_cli_runs_distance_and_the_removed_cell_switch_stops`(関数): 〔第346〕CLI の既定は distance・``--proximity`` の旗は引数の誤り・環境変数 SHIBUYA_PROXIMITY は読み込みで止まる。
  - `test_every_opened_conversation_is_within_reach`(関数)
  - `test_guards_hold_on_the_distance_arm`(関数)
  - `test_notice_streams_in_a_run_pass_k19`(関数)
  - `test_resume_equals_straight_on_the_distance_arm`(関数)
  - `test_resume_with_another_proximity_arm_is_refused`(関数)
  - `test_resume_without_the_proximity_header_is_refused`(関数): 〔第346〕見出しに ``proximity`` の無い状態のファイル(cell のラン)は再開で止まる: 保存の間だけ見出しを書かない形にし、
  - `test_same_input_same_result`(関数)
  - `test_sensitivity_arms_keep_every_conversation_within_their_d`(関数)
  - `test_world_resume_equals_straight_and_the_marks_matter`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.relations`・`shibuya.engine.resolve`・`shibuya.engine.resume`・`shibuya.engine.rng_audit`・`shibuya.engine.run`・`shibuya.engine.systems.conductor`・`shibuya.engine.systems.probe`・`shibuya.engine.systems.table`・`shibuya.foundation.write_permit`・`shibuya.perception.renderer`・`shibuya.world.model.proximity`
- 環境変数: `SHIBUYA_PROXIMITY_D`・`os.environ` をまるごと使う
- 決定の ID: 11-01・11-03/§3・第 346

## [test_switch_sites.py](../../../../../../../tests/engine/proximity/test_switch_sites.py)

第 2 期 2-2 段 11a: 判定を切り替えた所(合成の体)。

- 公開の関数とクラス
  - `layer`(関数)
  - `place`(関数)
  - `table`(関数)
  - `talk`(関数)
  - `test_acquaintance_appears_when_coming_into_range_and_respects_refractory`(関数)
  - `test_acquaintance_far_or_other_band_is_rarely_or_never_noticed`(関数)
  - `test_acquaintance_first_step_marks_only_and_appearance_needs_a_new_notice`(関数)
  - `test_aware_of_reads_the_marks`(関数): 検収 L1: 描画の知人は関係の層の印を読む(``aware_of``)=気づいた相手は範囲の中に居る間は真・辺に居ない相手は偽。
  - `test_batch_partners_match_bruteforce`(関数)
  - `test_chance_picks_reachable_acquaintance_across_cells`(関数)
  - `test_commit_talk_partner_named_only_when_reachable`(関数)
  - `test_copresent_counts_reachable_edges_not_same_cell`(関数)
  - `test_leave_uses_the_rule_with_hysteresis_and_ignores_cells`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.commit`・`shibuya.engine.conversation`・`shibuya.engine.memory`・`shibuya.world.model.proximity`
