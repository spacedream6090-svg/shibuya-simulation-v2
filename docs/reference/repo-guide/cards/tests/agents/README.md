# tests/agents

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 3 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../tests/agents/__init__.py)

agents 層のテスト。

## [test_schedule.py](../../../../../../tests/agents/test_schedule.py)

agents.schedule のテスト: T4(規模不変性)とカウンタベース抽選の同値性。

- 公開の関数とクラス
  - `test_boundaries_are_strictly_increasing_and_in_day`(関数)
  - `test_bulk_and_per_agent_draws_are_identical`(関数): 一括生成(既定)と個体別 Philox(T4 の定義)が**バイト一致**すること。
  - `test_cells_are_in_range`(関数)
  - `test_different_seed_changes_the_schedule`(関数)
  - `test_empty_schedule`(関数)
  - `test_events_of_day_is_tick_sorted_and_complete`(関数)
  - `test_t4_scale_invariance_5000_vs_5001`(関数): 運用設計書 §1.4 T4: n=5,000 と 5,001 で**既存個体の乱数列が不変**。
  - `test_weekend_pattern_differs_and_day_index_wraps`(関数)
- import している内部モジュール: `shibuya.agents.schedule`

## [test_state.py](../../../../../../tests/agents/test_state.py)

agents.state のテスト: M9 バイト予算・§6 不応期表・書き込みガード。

- 公開の関数とクラス
  - `test_core_fields_fit_m2_position_body_budget`(関数): M2(位置・運動・身体)≤128B/体 に、起床機構(refractory)を除いた欄が収まる。
  - `test_defaults_use_minus_one_sentinels`(関数)
  - `test_freeze_blocks_writes_and_writable_restores`(関数)
  - `test_kind_field_is_not_shadowed_by_registry_kind`(関数): ``Registry.kind`` は文字列 ``"agent"``。同名フィールドが**配列で**引けること(回帰)。
  - `test_m9_every_field_declared_and_within_m1`(関数)
  - `test_refractory_array_shape`(関数)
  - `test_refractory_table_matches_perception_contract_section6`(関数): 知覚契約書 §6 の不応期表(11 行)と 1 対 1。
  - `test_result_codes_cover_action_contract_failures`(関数)
  - `test_state_hash_changes_with_state`(関数)
  - `test_unknown_field_raises`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.foundation.types`
- 決定の ID: 第 276
