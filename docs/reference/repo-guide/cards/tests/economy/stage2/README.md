# tests/economy/stage2

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 14 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../tests/economy/stage2/__init__.py)

(冒頭の説明なし)

## [test_stage2_account_and_conservation.py](../../../../../../../tests/economy/stage2/test_stage2_account_and_conservation.py)

第 2 期 2-1 経済の段階 2: 口座の方法(``ops.transfer`` の ``method``)・段階 2 の組・保存則の検算(全登録)の単体の試験。

- 公開の関数とクラス
  - `test_account_method_is_refused_where_it_has_no_meaning`(関数)
  - `test_account_method_works_outside_the_household_cash_window`(関数): 世帯の現金(agents.money)が読み取り専用でも、口座の脚だけの transfer(賃金=日の締め)は書ける。
  - `test_account_payee_puts_the_money_in_the_deposit_and_leaves_cash_alone`(関数)
  - `test_account_payer_pays_from_the_deposit_with_a_settlement_row`(関数)
  - `test_account_payer_short_of_deposit_is_refused_and_counted`(関数)
  - `test_account_rows_keep_all_the_checks`(関数)
  - `test_cash_method_writes_zero_in_the_method_column`(関数)
  - `test_conservation_check_passes_and_names_the_residual`(関数)
  - `test_extra_money_words_map_to_deposit_net_and_are_in_the_vocab`(関数)
  - `test_negative_an_unregistered_flow_fails_the_check`(関数): 負の対照: 登録の無い流れ(銀行 → 世帯の利子=貨幣供給量を増やす)を足すと検算が落ちる。
  - `test_negative_dropping_a_registered_cell_fails_the_check`(関数)
  - `test_registry_kinds_follow_the_flow_kind_rule_and_are_consistent`(関数)
  - `test_stage2_pairs_are_allowed_only_on_an_attached_ledger`(関数)
  - `test_the_check_runs_without_the_arm_and_lands_in_the_day_record`(関数)
- import している内部モジュール: `shibuya.economy.accounts`・`shibuya.economy.checks`・`shibuya.economy.ledger`・`shibuya.economy.ops`・`shibuya.foundation.ports.ledger`・`shibuya.foundation.vocab.events`

## [test_stage2_atm_absent_warning.py](../../../../../../../tests/economy/stage2/test_stage2_atm_absent_warning.py)

〔第335・CI の直し〕ATM の取得物(``data/realworld/osm/…``)が無い写しの注記は ``DataAbsentWarning``(UserWarning 系)で、``RuntimeWarning`` ではない。

- 公開の関数とクラス
  - `test_absent_osm_file_warns_data_absent_not_runtime`(関数): 取得物が無い写し: ``DataAbsentWarning`` が 1 回出て、``RuntimeWarning`` を失敗に昇格しても落ちない。
  - `test_data_absent_warning_is_user_warning_not_runtime`(関数)
- import している内部モジュール: `shibuya.economy.stage2_bind`
- 決定の ID: 第 335

## [test_stage2_calls.py](../../../../../../../tests/economy/stage2/test_stage2_calls.py)

第 2 期 2-1 経済の段階 2: 呼の id の配線(検収 A1)。

- 公開の関数とクラス
  - `test_a_chosen_withdrawal_skips_the_rule_and_takes_the_call_as_cause`(関数)
  - `test_an_account_answer_without_a_deposit_falls_back_to_cash`(関数)
  - `test_decision_layer_hints_are_taken_once`(関数)
  - `test_intent_batch_carries_the_calls_and_fills_the_rest`(関数)
  - `test_noted_calls_cause_purchases_and_steer_the_payment`(関数)
  - `test_port_answers_reach_the_actions_in_a_run`(関数)
  - `test_rejected_rows_drop_their_causes`(関数)
  - `test_transfer_takes_row_causes_and_counts_the_uncaused_rows`(関数)
- import している内部モジュール: `shibuya.economy.accounts`・`shibuya.economy.ledger`・`shibuya.economy.ops`・`shibuya.economy.stage2`・`shibuya.economy.stage2_bind`・`shibuya.engine.commit`・`shibuya.engine.decision.layer`・`shibuya.engine.decision.ports`・`shibuya.foundation.journal.links`・`shibuya.foundation.journal.log`・`shibuya.foundation.ports.decision`・`shibuya.foundation.ports.ledger`・`shibuya.world.model.state`・`tests/economy/stage2/test_stage2_runs.py`

## [test_stage2_default_2_4.py](../../../../../../../tests/economy/stage2/test_stage2_default_2_4.py)

〔第 2 期 2-4 V4〕経済の段階 2 の既定 on・切替口 off・効いている腕で見る再開の検査・店の売上の写しは税抜き。

- 公開の関数とクラス
  - `test_default_arm_is_on_and_off_is_the_switch`(関数)
  - `test_resume_check_uses_the_effective_arm`(関数): 金の台帳の無いラン(台帳なしの run_day)は腕 on でも段階 2 を挿さない=見出しに書かない=off と同じに扱う。
  - `test_revenue_is_tax_exclusive_on_a_synthetic_run`(関数): 合成の世界(台帳つき)の 1 日: 店の売上の写しの合計=世帯 → 店の消費支出 − レジの税・保存則が通る。
  - `test_tax_of_and_the_last_purchase_rows`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.economy.accounts`・`shibuya.economy.stage2`・`shibuya.economy.stage2_bind`
- 決定の ID: 第 346

## [test_stage2_guards.py](../../../../../../../tests/economy/stage2/test_stage2_guards.py)

第 2 期 2-1 経済の段階 2: 実行時の守り(検収 L1)の負の対照。

- 公開の関数とクラス
  - `test_atm_table_arrays_and_sources_cannot_be_written`(関数)
  - `test_money_stage2_credit_and_ledger_flag_are_sealed`(関数)
  - `test_stage2_pairs_table_cannot_be_written`(関数)
  - `test_stage2_plan_is_sealed_except_runner_once`(関数)
- import している内部モジュール: `shibuya.economy.accounts`・`shibuya.economy.credit`・`shibuya.economy.ledger`・`shibuya.economy.stage2_bind`・`shibuya.engine.calendar`

## [test_stage2_money_rules.py](../../../../../../../tests/economy/stage2/test_stage2_money_rules.py)

第 2 期 2-1 経済の段階 2: 本人の判断の代役の規則(mock と古典=expedient)と口の単体の試験(組み立ての物は試験の代役)。

- 公開の関数とクラス
  - `test_attach_twice_is_refused_and_unknown_parts_are_refused`(関数)
  - `test_ic_fares_from_the_account_and_cash_fallback_through_the_rail_port`(関数)
  - `test_initial_deposits_and_visitor_accounts`(関数)
  - `test_negative_deposit_short_card_falls_back_to_cash`(関数): 負の対照: 預金が足りなければカードでなく現金に戻る(財布で足りる額)。
  - `test_payment_falls_back_to_the_old_result_when_neither_suffices`(関数)
  - `test_payment_method_rule_and_register_tax`(関数)
  - `test_payroll_part_off_pays_nothing`(関数)
  - `test_payroll_pays_into_the_account_with_exogenous_funding`(関数)
  - `test_withdraw_needs_a_deposit_and_the_part`(関数)
  - `test_withdraw_rule_amount_and_cause`(関数)
- import している内部モジュール: `shibuya.economy.accounts`・`shibuya.economy.anchors`・`shibuya.economy.ledger`・`shibuya.economy.stage2`・`shibuya.foundation.journal.links`・`shibuya.foundation.journal.log`・`shibuya.foundation.ports.ledger`・`shibuya.world.laws.rail`

## [test_stage2_resume.py](../../../../../../../tests/economy/stage2/test_stage2_resume.py)

第 2 期 2-1 経済の段階 2: 腕 on のランの再開(10d)=通しのランと同じ(段階 2 の中身は組み立てで作り直す・預金は帳簿の残高O57 で戻す・計器は 0 から)。

- 公開の関数とクラス
  - `test_resume_equals_straight_with_the_arm`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.economy.accounts`・`shibuya.economy.stage2_bind`

## [test_stage2_resume_arm.py](../../../../../../../tests/economy/stage2/test_stage2_resume_arm.py)

第 2 期 2-1 経済の段階 2: 腕と部品を状態のファイルの見出しに書き、再開で今の腕と違えば止める(検収 A5・2-2 の M1 と同じ形)。

- 公開の関数とクラス
  - `arm`(関数)
  - `test_arm_off_state_files_keep_the_header_and_refuse_an_on_resume`(関数)
  - `test_resume_stops_when_the_arm_or_parts_differ`(関数)
- import している内部モジュール: `shibuya.economy.stage2_bind`・`shibuya.engine.resume`・`shibuya.world.model.state`・`tests/economy/stage2/test_stage2_runs.py`
- 決定の ID: 第 346

## [test_stage2_rules_credit_atm.py](../../../../../../../tests/economy/stage2/test_stage2_rules_credit_atm.py)

第 2 期 2-1 経済の段階 2: 規則の表の読み手(最低賃金・消費税)・信用の器・ATM の表と営業時間・腕と部品・暦の給料日。

- 公開の関数とクラス
  - `test_arm_and_parts_switches`(関数)
  - `test_atm_table_from_osm_has_the_55_points`(関数)
  - `test_atm_table_open_cells_follow_the_weekday_and_minute`(関数)
  - `test_consumption_tax_rate_is_ten_percent_from_the_rules_table`(関数)
  - `test_credit_book_rows_and_auto_repayment_with_delinquency`(関数)
  - `test_minimum_wage_switches_at_the_version_date`(関数): 規則の表の最初の読み手: 版のある日は表の値(1,163 円=2024-10-01〜・1,226 円=2025-10-03〜・1,280 円=2026-10-01〜)・
  - `test_monthly_wage_amounts_default_is_unchanged_and_takes_an_hourly_rate`(関数)
  - `test_opening_hours_parser`(関数)
  - `test_origin_constants_are_copies_of_the_build_geometry`(関数)
  - `test_payday_follows_the_calendar_port`(関数)
  - `test_payroll_deductions_is_an_empty_container`(関数)
  - `test_rights_pairs_reads_employment_rows_in_row_order`(関数)
- import している内部モジュール: `shibuya.build.geo.common`・`shibuya.economy.accounts`・`shibuya.economy.anchors`・`shibuya.economy.credit`・`shibuya.economy.ledger`・`shibuya.economy.ops`・`shibuya.economy.stage2`・`shibuya.economy.stage2_bind`・`shibuya.engine.calendar`・`shibuya.world.facts.rights.ledger`・`shibuya.world.model.state`
- 決定の ID: 第 337

## [test_stage2_runs.py](../../../../../../../tests/economy/stage2/test_stage2_runs.py)

第 2 期 2-1 経済の段階 2: 合成の世界の 2 日のラン(暦の口で開始日を 2026-08-24(月)=給料日 25 日をまたぐ)。

- 公開の関数とクラス
  - `arm`(関数): 腕と部品と ATM の表を試験の中だけ切り替える(終わったら元に戻す)。
  - `on_run`(関数)
  - `test_all_parts_move_money_and_keep_the_books`(関数)
  - `test_arm_off_changes_nothing_on_the_ledger`(関数)
  - `test_atms_live_in_the_fixtures`(関数)
  - `test_negative_a_closed_atm_gives_no_withdrawal`(関数): 負の対照: どの ATM も営業時間の外(全部の曜日 off)なら、財布が小さくても引き出せない。
  - `test_off_parts_spec_without_the_arm_is_ignored`(関数)
  - `test_port_arm_shows_the_candidates_and_keeps_the_mock_actions`(関数)
  - `test_turning_one_part_off_zeroes_its_flow`(関数)
- import している内部モジュール: `shibuya.economy.accounts`・`shibuya.economy.census`・`shibuya.economy.goods`・`shibuya.economy.ledger`・`shibuya.economy.stage2`・`shibuya.economy.stage2_bind`・`shibuya.engine.decision.layer`・`shibuya.engine.run`・`shibuya.engine.systems.boxes`・`shibuya.foundation.ports.ledger`・`shibuya.world.model.state`
- 読む試験: `tests/economy/stage2/test_stage2_calls.py`・`tests/economy/stage2/test_stage2_resume_arm.py`
- 決定の ID: 第 337

## [test_stage2_world_two_day.py](../../../../../../../tests/economy/stage2/test_stage2_world_two_day.py)

第 2 期 2-1 経済の段階 2: 世界資産の 2 日のラン(5,000 体・seed 1・既定 v3・開始日 2026-08-24(月)=25 日の給料日をまたぐ)。

- 公開の関数とクラス
  - `test_world_two_days_with_the_arm`(関数)
  - `test_world_two_days_without_the_arm`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.economy.accounts`・`shibuya.economy.stage2_bind`

## [test_stage2_writers.py](../../../../../../../tests/economy/stage2/test_stage2_writers.py)

第 2 期 2-1 経済の段階 2: 新しい書き手を増やさない(1-9 の AST の検査が通る形)と、口の名の表の外の口の帳尻。

- 公開の関数とクラス
  - `test_new_modules_do_not_open_the_ledger_window_or_touch_the_balance_arrays`(関数)
  - `test_new_modules_write_no_money_column`(関数)
  - `test_rail_and_ledger_route_through_the_generic_port`(関数): 運賃の IC の口(``pay_fares_many``)と賃金・引き出し・カードは ``Ledger.transfer_many`` だけを呼ぶ(``ops.transfer`` を直に
  - `test_stage2_ports_in_resolve_are_inside_a_money_writing_closure`(関数)
- import している内部モジュール: `shibuya.engine.systems.allow`・`shibuya.engine.systems.table`・`tests/economy/cp2/money_writers.py`

## [test_wage_occupation_runs.py](../../../../../../../tests/economy/stage2/test_wage_occupation_runs.py)

賃金を職業ごとの実データから(小さな版上げ・2026-10-17): 世界資産の 2 日のラン(開始日 2026-08-24=1 日目の締めが給料日)。

- 公開の関数とクラス
  - `test_conservation_and_only_the_wage_accounts_move`(関数)
  - `test_median_matches_r107`(関数)
  - `test_resume_equals_straight`(関数)
  - `two_arms`(関数): 〔第 4 期 4-3 版上げ 3 回目の第 2 部〕旧値の腕 w17 は消した=既定(occupation)の 1 本だけ(名は前のまま)。
- import している内部モジュール: `shibuya.cli`・`shibuya.economy.accounts`・`shibuya.economy.stage2_bind`・`shibuya.economy.wages`
- 決定の ID: R-107
