# tests/engine/rules

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 3 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../tests/engine/rules/__init__.py)

(冒頭の説明なし)

## [test_rules42_table.py](../../../../../../../tests/engine/rules/test_rules42_table.py)

第 4 期 4-2 規則の表の中身(R-118 §7-1 の 4-3 に束ねる分・PENDING 仮-40 の Q2・Q6): 19 行+申告の期限の 1 行。

- 公開の関数とクラス
  - `test_every_machine_row_has_a_reader`(関数): machine の行は読み手と一緒に(読み手の無い machine の行を残さない): economy.taxes が読む行と anchors の 2 行。
  - `test_existing_rows_keep_their_values`(関数)
  - `test_lower_bound_rows_are_marked`(関数)
  - `test_norm_kind_and_schema_2`(関数)
  - `test_r118_law_sources_match_the_research_table`(関数): 写し検査: R-118 の e-Gov の出典は答申 §1-1 の表の同じ行(law_id と 7-13 の版)にあり、URL は asof=2026-07-13。
  - `test_the_19_rows_are_the_draft_rows_and_in_force_on_the_world_date`(関数)
  - `test_the_filing_deadline_row_is_from_r106_and_used_at_the_period_end`(関数)
  - `test_the_grade_tables_are_the_research_copies`(関数)
  - `test_the_two_rows_now_cite_the_world_date_versions`(関数): R-118 §5 ②: 出典の版を世界の時点の版に(値は不変)。
- import している内部モジュール: `shibuya.economy.anchors`・`shibuya.economy.taxes`・`shibuya.world.facts.rules.table`
- 決定の ID: 11-01/§5・R-118

## [test_rules_table_schema.py](../../../../../../../tests/engine/rules/test_rules_table_schema.py)

第 1 期 1-4 規則の表(CP10・決定 10-12 §1-12): 出典と版が必須・asof で版を引ける・表の sha が決定的(口の約束 1-4)。

- 公開の関数とクラス
  - `test_a_source_needs_law_article_version_and_url`(関数)
  - `test_a_source_url_is_https_and_retrieved_is_a_date`(関数)
  - `test_bad_rules_are_refused`(関数)
  - `test_from_dict_refuses_unknown_and_missing_fields`(関数)
  - `test_get_returns_the_version_in_force_on_the_day`(関数)
  - `test_load_refuses_another_schema`(関数)
  - `test_only_the_manifest_and_the_daily_record_import_the_table`(関数): 約束 (1): 規則の表を読んでも挙動は変わらない=読むのは manifest(run.py)と日次の記録(state_io.py)と、ランの始めに
  - `test_rows_sources_and_params_are_frozen`(関数)
  - `test_sources_are_copied_from_the_research_tables`(関数): 写し検査: e-Gov の法令 ID と版は R-106 §0-2 の表の同じ行にある・URL は答申の本文にある(親の一次確認の出典は
  - `test_the_reader_check_sees_every_import_form`(関数): 検収 L8 の負の対照: 別名・相対の import も読み手として見つかる。
  - `test_the_repo_minimum_wage_has_the_version_on_the_world_date`(関数): 〔第337・親の一次確認で △ を解消〕世界の時点 2026-07-13 は 1,226 円(2025-10-03 の版)。2024-10-01 より前は版が無い。
  - `test_the_repo_table_has_three_real_rules`(関数)
  - `test_the_table_object_cannot_be_rewired`(関数)
  - `test_the_table_sha_is_deterministic_and_is_the_rules_version`(関数)
  - `test_the_values_are_the_r106_values`(関数)
  - `test_two_rows_with_the_same_id_and_asof_are_refused`(関数)
- import している内部モジュール: `shibuya.world.facts.rules.table`
- 決定の ID: 10-12/§1-12・11-01/§5・R-106・R-118・第 337
