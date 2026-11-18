# src/shibuya/world/facts

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 7 本・その他 0 本(このディレクトリの直下)

下のディレクトリ: [rights](rights/README.md)・[rules](rules/README.md)

## [__init__.py](../../../../../../../../src/shibuya/world/facts/__init__.py)

(冒頭の説明なし)

## [calendar.py](../../../../../../../../src/shibuya/world/facts/calendar.py)

engine.calendar — 暦の口(指示書 10-03 §3-1 A1・A1-1・A1-2・A1-3)。

- 公開の関数とクラス
  - `CalendarWarning`(クラス): 暦の口の警告(祝日 CSV が無い)。
  - `HolidayTable`(クラス): 祝日の表(日付 → 名称)と出どころ。
  - `SimCalendar`(クラス): ランの暦(``start_sim_datetime`` と T から日付・曜日・祝日・季節・給料日・営業日を返す)。
  - `holidays_between`(関数): ``lo``〜``hi``(両端を含む)の祝日(ISO の日付 → 名称)。
  - `load_holidays`(関数): 内閣府の祝日 CSV を読む(cp932)。無ければ空の表を返し、警告を 1 回だけ出す。
  - `parse_school_holidays`(関数): 学校の長期休みの区間の一覧(manifest の欄 ``school_holidays``)を ``(始, 終)`` の組に直す。
  - `parse_start`(関数): 開始日の欄(``--start-date``)→ ``datetime``。``None``/空は ``None``(既定の導き方)。
- import している内部モジュール: `shibuya.foundation.paths`・`shibuya.foundation.types`
- 呼び手: `shibuya.interfaces.cli.run_args`・`shibuya.runtime.run`・`shibuya.runtime.systems.assemble`・`shibuya.runtime.systems.report`・`shibuya.world.laws.environment`・`shibuya.world.laws.opening`・`shibuya.world.laws.rail`・`shibuya.world.laws.runner`
- 読む試験: `tests/build_field/test_field_units.py`・`tests/build_field/test_w12_real_timetables.py`・`tests/economy/stage2/test_stage2_guards.py`・`tests/economy/stage2/test_stage2_rules_credit_atm.py`・`tests/engine/calendar/test_calendar_shadow.py`・`tests/engine/calendar3/test_ca3_runs.py`・`tests/engine/calendar3/test_ca3_units.py`・`tests/engine/experiment/_x33.py`・`tests/engine/experiment/test_x33_branch.py`・`tests/engine/test_10a_review_fixes.py`・`tests/engine/test_calendar.py`・`tests/engine/test_calendar_10e_e3.py`・`tests/engine/test_calendar_sites.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_weather_calendar_10e.py`
- 決定の ID: 10-03/§3-1・第 330

## [initial_ties.py](../../../../../../../../src/shibuya/world/facts/initial_ties.py)

world.facts.initial_ties — 割る段で ``engine/relations.py`` を割った割り先(全ファイルの表 §4・名の表は``tools/pkgmove/map.toml`` の割る行)。

- 公開の関数とクラス
  - `check_rel_tenure_hash`(関数): 在職期間のハッシュの版を検める(関係の部品の単体の口・〔第 2 部〕ランの口の切替口 --rel-tenure-hash は消した)。
  - `copresence`(関数): ``(g, 枠)`` のセル → ``(共在の分(g×g), 共在のブロック数(g×g))``(同じセル・同じ枠・行列積)。
  - `copresence_days`(関数): ``(g, 7×96)`` のセル → ``(g, g)`` の「共在のあった曜日の数」(0〜7・同じセル・同じ枠が 1 枠でもある日)。
  - `initial_edges`(関数): W16(世帯・組織・学校セル)+W17(共在)→ 初期辺(有向・体ごとに上位 k − 世帯)。
  - `slot_cells`(関数): 体行の配列 → ``(体, 7×96)`` の「その 15 分に居るセル」(W17 の解決済みセル・無ければ −1)。
  - `tau_from_edges`(関数): τ の逆算: 体ごとの k 番目に強い辺の A(k 本に満たない体は −∞)の中央値(=半分の体が k 本残る τ)。
- import している内部モジュール: `shibuya.foundation.time_consts`・`shibuya.foundation.vocab.relations`
- 呼び手: `shibuya.runtime.systems.assemble`
- 読む試験: `tests/engine/test_relations.py`・`tests/engine/test_relations_8b.py`・`tests/engine/test_relations_tenure.py`
- 決定の ID: 第 299・第 300

## [mock_schedule.py](../../../../../../../../src/shibuya/world/facts/mock_schedule.py)

agents.schedule — **mock 専用**の合成 T0 週次スケジュール(計画境界の生成器)。

- 公開の関数とクラス
  - `MockWeeklySchedule`(クラス): 合成日課(mock)。全て個体ごとの配列で持つ(個体オブジェクトを作らない)。
  - `draw_words`(関数): 個体 ``start_agent..start_agent+n_agents-1`` の生語を一括生成する(ループなし)。
  - `draw_words_per_agent`(関数): **参照実装**(T4 の定義そのまま): 個体ごとに独立の Philox から引く。
  - `synthesize`(関数): 合成日課を作る(**mock 専用**)。
- import している内部モジュール: `shibuya.foundation.rng`・`shibuya.foundation.time_consts`・`shibuya.foundation.vocab.agent_codes`
- 呼び手: `shibuya.runtime.systems.assemble`・`tools/c6/ablation1_fixed_vs_ranking.py`
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
- 呼び手: `shibuya.economy.stage2_bind`・`shibuya.interfaces.cli.wire_economy`・`shibuya.runtime.run`・`tools/c7/attr_arms.py`・`tools/w17/diversity_yardstick.py`
- 読む試験: `tests/build_pop/test_pop_pipeline.py`・`tests/build_pop/test_pop_units.py`・`tests/build_pop/test_w21_stage10_swap.py`・`tests/c6/test_t5_order_bias.py`・`tests/engine/memory/test_m0_store_schema.py`・`tests/engine/rights/test_rights_from_w16.py`・`tests/engine/rights/test_staff_of_poi_equivalence.py`・`tests/engine/test_pop_w21_world.py`・`tests/engine/test_presence_derive_v2.py`・`tests/engine/test_presence_executor.py`・`tests/engine/test_relations_tenure.py`・`tests/engine/test_version_bump_10e.py`・`tests/engine/tools/test_c0_groups_from_w16.py`・`tests/llm/test_fleet_contract.py`
- 読む試験(道筋で): `tests/engine/bridging/test_bridging_ledger.py`

## [w20_calendar_reader.py](../../../../../../../../src/shibuya/world/facts/w20_calendar_reader.py)

world.facts.w20_calendar_reader — 割る段で ``engine/calendar_shadow.py`` を割った割り先(全ファイルの表 §4・名の表は``tools/pkgmove/map.toml`` の割る行)。

- 公開の関数とクラス
  - `CalendarTable`(クラス): ランの体の並びに引き直した W20 の週の表(配列は ``(体, 週, 曜日)``)と版の記録。
  - `load_table`(関数): W20 の週の表を読み、ランの体の並び(``agent_ids``=W16 の ``agent_id``)に引き直す。
  - `resolve_path`(関数): W20 の週の表の道筋(環境変数 ``SHIBUYA_CALENDAR_W20`` があればそれ・無ければ ``<world_dir>/w20_calendar_1a.parquet``)。
- 呼び手: `shibuya.interim_bundles.calendar3.roster`・`shibuya.interim_bundles.calendar_self`・`shibuya.society.calendar_shadow`・`tools/instruments/anchor_gauge.py`
- 読む試験: `tests/build_sched/test_w20_calendar_1a.py`・`tests/engine/calendar/test_ca1b_unit.py`・`tests/engine/calendar/test_calendar_shadow.py`
- 環境変数: `SHIBUYA_CALENDAR_W20`

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
- import している内部モジュール: `shibuya.foundation.hashing`・`shibuya.foundation.time_consts`・`shibuya.foundation.vocab.agent_codes`
- 呼び手: `shibuya.runtime.systems.assemble`・`shibuya.society.calendar_shadow`・`shibuya.world.body.energy`・`shibuya.world.laws.presence`・`shibuya.world.laws.presence_plan`・`tools/instruments/anchor_gauge.py`・`tools/w17/diversity_yardstick.py`
- 読む試験: `tests/build_pop/test_w21_stage10_swap.py`・`tests/build_sched/test_trial.py`・`tests/build_sched/test_weekly_loader.py`・`tests/engine/body/test_meal_default_w17.py`・`tests/engine/processes/test_rail_return.py`・`tests/engine/test_10a_review_fixes.py`・`tests/engine/test_energy_balance.py`・`tests/engine/test_meal_bundle_2b.py`・`tests/engine/test_plan_sleep_d62.py`・`tests/engine/test_presence_derive_v2.py`・`tests/engine/test_presence_executor.py`・`tests/engine/test_relations.py`・`tests/engine/test_relations_8b.py`・`tests/engine/test_relations_tenure.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/time/test_t0_time_consts.py`・`tests/w17/test_diversity_yardstick.py`
- 決定の ID: D-61・D-62・D-68
