# src/shibuya/world/facts

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 4 本・その他 0 本(このディレクトリの直下)

下のディレクトリ: [rights](rights/README.md)・[rules](rules/README.md)

## [__init__.py](../../../../../../../../src/shibuya/world/facts/__init__.py)

(冒頭の説明なし)

## [mock_schedule.py](../../../../../../../../src/shibuya/world/facts/mock_schedule.py)

agents.schedule — **mock 専用**の合成 T0 週次スケジュール(計画境界の生成器)。

- 公開の関数とクラス
  - `MockWeeklySchedule`(クラス): 合成日課(mock)。全て個体ごとの配列で持つ(個体オブジェクトを作らない)。
  - `draw_words`(関数): 個体 ``start_agent..start_agent+n_agents-1`` の生語を一括生成する(ループなし)。
  - `draw_words_per_agent`(関数): **参照実装**(T4 の定義そのまま): 個体ごとに独立の Philox から引く。
  - `synthesize`(関数): 合成日課を作る(**mock 専用**)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.foundation.rng`・`shibuya.foundation.time_consts`
- 呼び手: `shibuya.engine.systems.build`・`tools/c6/ablation1_fixed_vs_ranking.py`
- 読む試験: `tests/agents/test_schedule.py`・`tests/build_sched/test_weekly_loader.py`・`tests/engine/processes/conftest.py`・`tests/engine/processes/test_rail_return.py`・`tests/engine/rights/test_staff_of_poi_equivalence.py`・`tests/engine/test_10a_review_fixes.py`・`tests/engine/test_ablation23_switches.py`・`tests/engine/test_calendar_sites.py`・`tests/engine/test_conversation_invite.py`・`tests/engine/test_determinism_t1_t2_t4.py`・`tests/engine/test_intent_hold.py`・`tests/engine/test_ledger_wiring.py`・`tests/engine/test_plan_sleep_d62.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/test_vocab_v2_eat.py`・`tests/engine/test_weather_calendar_10e.py`
- 読む試験(道筋で): `tests/engine/test_two_phase.py`

## [population_reader.py](../../../../../../../../src/shibuya/world/facts/population_reader.py)

agents.population — W16 母集団(``w16_population.parquet``)の読み込みと二層抽出。

- 公開の関数とクラス
  - `Population`(クラス): W16 母集団の列(行順=``agent_id`` の昇順)。
  - `PopulationSchemaError`(クラス): 母集団の列が欠けている・知らない語や番号がある(黙って埋めない)。
  - `load_population`(関数): W16 母集団を読む。資産が無ければ ``None``。
  - `population_available`(関数): ``<world_dir>/w16_population.parquet`` があるか。
  - `sample_population`(関数): 二層抽出(定員先取り層+統計層)。同 seed 同結果。
- import している内部モジュール: `shibuya.foundation.hashing`・`shibuya.foundation.rng`
- 呼び手: `shibuya.cli`・`shibuya.economy.stage2_bind`・`shibuya.engine.run`・`tools/c7/attr_arms.py`・`tools/w17/diversity_yardstick.py`
- 読む試験: `tests/build_pop/test_pop_pipeline.py`・`tests/build_pop/test_pop_units.py`・`tests/build_pop/test_w21_stage10_swap.py`・`tests/c6/test_t5_order_bias.py`・`tests/engine/rights/test_rights_from_w16.py`・`tests/engine/rights/test_staff_of_poi_equivalence.py`・`tests/engine/test_pop_w21_world.py`・`tests/engine/test_presence_derive_v2.py`・`tests/engine/test_presence_executor.py`・`tests/engine/test_relations_tenure.py`・`tests/engine/test_version_bump_10e.py`・`tests/engine/tools/test_c0_groups_from_w16.py`
- 読む試験(道筋で): `tests/engine/bridging/test_bridging_ledger.py`

## [weekly_reader.py](../../../../../../../../src/shibuya/world/facts/weekly_reader.py)

agents.weekly — W17 週次活動表(``w17_schedule.parquet``)の読み込みと計画境界の取り出し。

- 公開の関数とクラス
  - `InboundStarts`(クラス): その日の**域内活動**(``place_kind != 域外``)の開始分を体行ごとに束ねた索引(D-61)。
  - `WeeklySchedule`(クラス): 週次活動表(行順=``(agent_id, day, seq)`` 昇順)。
  - `activity_to_action`(関数): 語彙版 → 活動語 → 行動語の表(v1/v2 は ``ACTIVITY_TO_ACTION`` そのもの)。
  - `apply_to_mock_schedule`(関数): 合成日課(``MockWeeklySchedule``)の拠点セルを W17 の当日の行き先で上書きする。
  - `load_weekly`(関数): W17 週次表を読む(``<world_dir>/w17_schedule.parquet``)。資産が無ければ ``None``。
  - `load_weekly_file`(関数): **ファイル名を問わず**1 つの parquet から週次表を組む。
  - `weekly_available`(関数): ``<world_dir>/w17_schedule.parquet`` があるか。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.foundation.hashing`・`shibuya.foundation.time_consts`
- 呼び手: `shibuya.engine.calendar_shadow`・`shibuya.engine.presence`・`shibuya.engine.systems.build`・`shibuya.world.body.energy`・`tools/instruments/anchor_gauge.py`・`tools/w17/diversity_yardstick.py`
- 読む試験: `tests/build_pop/test_w21_stage10_swap.py`・`tests/build_sched/test_trial.py`・`tests/build_sched/test_weekly_loader.py`・`tests/engine/body/test_meal_default_w17.py`・`tests/engine/processes/test_rail_return.py`・`tests/engine/test_10a_review_fixes.py`・`tests/engine/test_energy_balance.py`・`tests/engine/test_meal_bundle_2b.py`・`tests/engine/test_plan_sleep_d62.py`・`tests/engine/test_presence_derive_v2.py`・`tests/engine/test_presence_executor.py`・`tests/engine/test_relations.py`・`tests/engine/test_relations_8b.py`・`tests/engine/test_relations_tenure.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/time/test_t0_time_consts.py`・`tests/w17/test_diversity_yardstick.py`
- 決定の ID: D-61・D-62・D-68
