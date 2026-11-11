# tests/build_rail

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 3 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../tests/build_rail/__init__.py)

(冒頭の説明なし)

## [test_activate_tt23c.py](../../../../../../tests/build_rail/test_activate_tt23c.py)

2-3c の活性化の道具(``docs/bench/analysis/wallbounce-1012/tt23c/tools/activate_tt23c.py``)を合成の置き場で回す。

- 公開の関数とクラス
  - `test_apply_stops_when_the_stage_differs_from_the_plan`(関数)
  - `test_plan_apply_verify_materialize_revert`(関数)

## [test_w12_arrivals_2_3c.py](../../../../../../tests/build_rail/test_w12_arrivals_2_3c.py)

W12 1.3.0 の渋谷の発着の表(第 2 期 2-3c・``build/field/w12_rail_events.py``)。

- 公開の関数とクラス
  - `synth`(関数)
  - `test_each_gate_component_has_a_negative_control`(関数): 〔検収 L1・L2〕ゲート ``rail_events_suspicious_pairs`` の残りの成分 1 つずつ: 成田エクスプレスの外れ・列車時刻表との
  - `test_engine_reader_is_not_called_from_any_process`(関数): 〔検収 L3〕読む口の器はどの過程・系からも呼ばれない(既定は読まない=結果不変の静的な番人)。
  - `test_engine_reader_is_off_by_default`(関数)
  - `test_inputs_follow_the_challenge_switch`(関数)
  - `test_metro_arrivals_upstream_departures_match_the_user_tables`(関数): 地下鉄の渋谷着の列車の手前の駅(表参道・明治神宮前)の発車は、ユーザーの表の読み取りと時刻の多重集合で一致
  - `test_negative_controls_leave_suspicious_pairs`(関数): まとめない組: 上りの行き先が違う/当駅始発の印が無い/発車−到着が上限の外 → 疑わしい組が残る(黙って結ばない)。
  - `test_origin_marks_match_the_challenge_isorigin`(関数): 当駅始発の印(ユーザーの PDF の読み取り)=チャレンジ枠の東急 渋谷の駅の時刻表の isOrigin(照合だけ)。
  - `test_readings_agree_read1_read2_and_hour_cells`(関数): 読み取りの検査(2-3b と同じ形): 読み 1 と読み 2 が (時, 分) と種別・行き先で一致・時ごとの本数が一致。
  - `test_real_run_matches_the_record_golden`(関数)
  - `test_same_minute_two_trains_are_counted_on_the_raw_rows`(関数): 〔検収 M1〕相鉄線直通の便と大崎方面の便が同じ分=表の生の行では 2 便・発車の表では 1 行(2-3b の重複の除去)。
  - `test_synthetic_arrivals_and_through_merge`(関数)
  - `test_unknown_station_or_type_stops`(関数)
  - `test_version_table_names_rules_and_declarations`(関数)
- import している内部モジュール: `shibuya.build.audit.w19_freeze`・`shibuya.build.field.common`・`shibuya.build.field.w12_external_nodes`・`shibuya.build.field.w12_rail_events`・`shibuya.build.field.w12_real_timetables`・`shibuya.engine.processes.opening`・`shibuya.engine.processes.rail_events`・`shibuya.engine.systems.table`・`tests/_data_ids.py`
