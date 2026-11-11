# tests/economy

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 18 本・その他 0 本(このディレクトリの直下)

下のディレクトリ: [cp2](cp2/README.md)・[stage2](stage2/README.md)

## [__init__.py](../../../../../../tests/economy/__init__.py)

economy 層のテスト(U11 金の台帳・U-Goods 物の台帳・検算・センサス・価格形成)。

## [test_accounts.py](../../../../../../tests/economy/test_accounts.py)

科目の列挙と faucet/sink 表のテスト(境界・経済設計書 §2.1-2.2)。

- 公開の関数とクラス
  - `test_balance_sheet_has_six_lines_and_net_worth_is_derived`(関数): §2.2: 貸借対照表6行。純資産だけは導出(実配列を持たない)。
  - `test_consumption_is_household_to_store_only`(関数)
  - `test_depreciation_is_a_self_loop`(関数): 減価償却は相手方が無い(設計書との食い違い#1)ので自己ループとして受理する。
  - `test_entry_capital_payers_are_restricted_ex_nihilo`(関数): §2.3: 参入資本は創業者預金・銀行貸出・外界からのみ。
  - `test_faucet_and_sink_classification`(関数): faucet=来街者持込・域外雇用主の賃金/sink=域外仕入・税・持ち出し(§2.2)。
  - `test_faucet_sink_table_is_one_to_one_with_the_enum`(関数): faucet/sink 表は account_code の列挙と 1 対 1(全科目に行がある)。
  - `test_flow_kind_rejects_unknown_code`(関数)
  - `test_hoard_is_a_measure_not_a_flow`(関数): 退蔵項はストックの測度。どの部門対でも transfer できない。
  - `test_sector_codes_match_engine_api`(関数): 依存逆転の境界: economy の Sector と engine.ledger_api の部門番号が一致する。
  - `test_six_sectors_match_the_design`(関数): §2.1: 世帯・店舗・雇用主・銀行・政府・外界の6部門。
  - `test_twelve_flow_accounts_plus_residual_hoard_and_deviation_cost`(関数): §2.2 の 12 科目 + 残差 + 退蔵(+ §8 H-5 の逸脱比例コスト)。
  - `test_unknown_code_is_impossible`(関数): 列挙にない科目は許可されない(=transfer 実行不能)。
  - `test_wallet_kind_matches_agent_kind`(関数): 層契約で economy から agents を import できないので**値の写し**が一致することを検査。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.economy.accounts`・`shibuya.economy.anchors`・`shibuya.foundation.ports.ledger`

## [test_anchors.py](../../../../../../tests/economy/test_anchors.py)

§2.5 の金額アンカー(公的値)と初期財布・月次賃金のテスト。

- 公開の関数とクラス
  - `test_anchor_values_match_the_design_table`(関数): §2.5 の表の値(家計調査2025・最低賃金・経済センサス2021・区ごみ)。
  - `test_every_anchor_carries_a_source_string`(関数)
  - `test_initial_wallets_are_deterministic_and_kind_dependent`(関数)
  - `test_monthly_figures_are_consistent_with_the_daily_ones`(関数): 親検算: 314,001円/月 ÷ 30.44 ≈ 10,300円/日・173,042 ÷ 30.44 ≈ 5,700円/日。
  - `test_monthly_wage_amounts_use_the_minimum_wage_floor`(関数)
  - `test_monthly_wages_move_money_from_employers_to_households`(関数)
  - `test_wages_from_outside_employers_are_a_faucet`(関数)
- import している内部モジュール: `shibuya.economy.accounts`・`shibuya.economy.anchors`・`shibuya.economy.ledger`・`shibuya.foundation.rng`
- 決定の ID: D-16

## [test_census.py](../../../../../../tests/economy/test_census.py)

日次(軽量)センサス・月次 MER・ゲートのテスト(境界・経済設計書 §2.4)。

- 公開の関数とクラス
  - `test_an_empty_sector_table_still_has_the_columns`(関数): 取引が 1 件も無い月でも列は落ちない(Parquet の追記が壊れないため)。
  - `test_daily_census_parquet_roundtrip`(関数)
  - `test_daily_census_row_has_the_fixed_columns`(関数)
  - `test_flow_rows_sum_to_the_faucet_sink_totals_per_kind`(関数): 検算: 区分ごとの ``flows`` 合計 = 科目別 faucet/sink/internal の合計。
  - `test_gate_fails_on_a_goods_stocktake_difference`(関数)
  - `test_gate_fails_on_a_large_residual`(関数)
  - `test_light_census_has_only_residual_and_money_supply`(関数): §2.4「日次(軽量): 残差・貨幣供給量のみ」。
  - `test_monthly_mer_is_a_fixed_table`(関数): §2.4 月次 = EVE 型 MER(科目別 faucet/sink・貨幣供給量・残差・退蔵残高)。
  - `test_monthly_mer_sectors_is_a_fixed_table`(関数): 部門軸の長い表(別ファイル)。列は ``SECTOR_FLOW_COLUMNS`` 固定。
  - `test_sector_net_sums_to_faucet_minus_sink`(関数): 検算: ``Σ_部門 net = faucet 合計 − sink 合計``(境界を擬似部門へ出したから成り立つ)。
  - `test_sector_net_total_equals_the_money_supply_increase`(関数): 検算: 残差 0 の台帳では ``Σ_部門 net`` = 貨幣供給量の増分。
  - `test_the_sector_axis_comes_from_the_ledgers_own_sectors`(関数): 部門は**台帳が既に持っている属性**(取引フロー行列の軸 = ``accounts.Sector``)。
  - `test_the_sector_axis_does_not_move_the_fixed_table`(関数): §2.4 の固定表は 1 つも変わらない(キー・値・parquet の列と行順)。
- import している内部モジュール: `shibuya.economy.accounts`・`shibuya.economy.census`・`shibuya.economy.checks`・`shibuya.economy.goods`・`shibuya.economy.ledger`・`shibuya.foundation.ports.ledger`
- 決定の ID: D-76・D-85・第 204・第 305

## [test_entry_capital.py](../../../../../../tests/economy/test_entry_capital.py)

D-13 店舗参入資本の按分(economy.entry_capital)のテスト。

- 公開の関数とクラス
  - `test_apportionment_differentiates_categories`(関数): 一律ではない: 卸売・小売(shop)は宿泊飲食(food)より大きい。
  - `test_bounds_are_multiples_of_the_rounding_step`(関数)
  - `test_capital_is_monotone_in_k_and_in_the_population_scale`(関数): k・母集団比を上げると参入資本は**下がらない**(丸めと上限の範囲で単調)。
  - `test_capital_is_non_negative_and_within_the_declared_bounds`(関数)
  - `test_census_values_are_the_raw_156_2021_figures`(関数): センサス 156-2021(万円)× 10,000。**親が JSON で一次確認した生値**。
  - `test_cost_ratio_comes_from_the_goods_category_k`(関数): 原価率は ``goods.CATEGORY_K`` の逆数(新しい定数を置いていない)。
  - `test_empty_world_gives_an_empty_array`(関数)
  - `test_endowment_is_a_transfer_from_the_row_not_ex_nihilo`(関数): 按分版でも注入は外界 → 店舗の transfer(§2.3 ex nihilo 禁止)。
  - `test_every_mapped_industry_has_published_sales`(関数): 写像先が「調査していないもの(･･･)/秘匿(X)」の大分類になっていない。
  - `test_full_scale_agents_matches_the_l4_budget_denominator`(関数): 母集団比の分母は L4 予算の按分分母と同じ 400,000(engine 側が正典)。
  - `test_is_deterministic_no_rng`(関数)
  - `test_mapping_covers_every_poi_category`(関数): 実資産 13 値 + 合成 3 値のすべてに大分類がつく(既定へ落ちない)。
  - `test_neither_bound_binds_at_the_operating_scales`(関数): 下限・上限は運用スケール(5,000〜400,000 体)で**発動しない**(按分がそのまま出る)。
  - `test_population_scale_is_one_at_full_scale`(関数)
  - `test_price_band_matches_world_assets_hash_free_cat_code`(関数): 層契約で複製した ``price_band`` が world 側の正典と一致する(等価テスト)。
  - `test_report_carries_the_money_supply_share`(関数)
  - `test_share_of_money_supply_from_the_ledger`(関数)
  - `test_the_floor_binds_only_below_about_1900_agents`(関数): 最小カテゴリ(M 宿泊飲食)が下限に当たるのは約 1,883 体未満(境界を固定する)。
  - `test_total_equals_the_sum_of_the_parts`(関数)
  - `test_unknown_category_falls_back_to_the_declared_default`(関数)
- import している内部モジュール: `shibuya.economy.accounts`・`shibuya.economy.anchors`・`shibuya.economy.entry_capital`・`shibuya.economy.goods`・`shibuya.economy.ledger`・`shibuya.engine.arbiter`・`shibuya.world.assets`
- 決定の ID: D-13・D-16

## [test_goods.py](../../../../../../tests/economy/test_goods.py)

物の保存則(U-Goods)のテスト = 世界過程設計書 §7.1。

- 公開の関数とクラス
  - `test_deliver_is_an_alias_of_restock`(関数)
  - `test_delivery_capacity_is_proportional_to_n`(関数): D-53: 納品ログの容量も **N(個体数)比例**。物の台帳は POI 側の器だが、
  - `test_delivery_log_is_bounded_and_declared`(関数): §7.2「O(t)ログは状態成長宣言を型レベルで強制」。
  - `test_goods_faucet_sink_table_is_one_to_one_with_the_enum`(関数): §7.1 の faucet/sink 列挙と 1 対 1(列挙にない科目の move_goods は実行不能)。
  - `test_hoard_counts_unsold_shelf_stock`(関数): 退蔵項 = 売れ残り在庫(滞留日数で判定)。
  - `test_inventory_value_feeds_the_money_ledger_and_check_two_still_holds`(関数)
  - `test_move_goods_rejects_disallowed_pairs_and_shortages`(関数)
  - `test_per_sku_balance_holds_across_sale_restock_waste_and_consume`(関数): 検算①: 期首 + 流入 − 流出 + 残差 = 期末(全 SKU・日次)。
  - `test_restock_pays_the_money_ledger_as_an_import_purchase`(関数): 補充は**金の台帳**へ域外仕入(店舗→外界 sink)を立てる。払えない店は補充されない。
  - `test_sale_moves_units_from_shelf_to_households`(関数)
  - `test_sale_respects_shelf_depth_for_duplicate_stores`(関数)
  - `test_sell_many_dispenses_across_all_slots`(関数): 回帰: 先頭スロットの残りを超えても、他スロットに在庫があれば売れる。
  - `test_sell_many_ignores_out_of_range_rows_without_shifting_the_rank`(関数)
  - `test_sell_many_is_row_order_deterministic_across_slots`(関数)
  - `test_sell_many_still_refuses_when_the_whole_shelf_is_empty`(関数)
  - `test_shelf_arrays_are_frozen_outside_the_ledger`(関数)
  - `test_sku_registry_is_one_to_three_per_category`(関数)
  - `test_stocktake_residual_gate`(関数): 棚卸差異は残差科目。閾値(流量比 1%)超でゲート失敗。
  - `test_the_delivery_declaration_alone_never_exceeds_the_cap`(関数): D-53 の回帰: 宣言投影(32 B/体/日 × N)が cap を食い破らない。
  - `test_waste_band_against_the_w1_anchor`(関数): 検算②: 廃棄 sink の月次総量 ≈ 渋谷区ごみ 119.6 t/日 の band(±30%)。
- import している内部モジュール: `shibuya.economy.accounts`・`shibuya.economy.anchors`・`shibuya.economy.checks`・`shibuya.economy.goods`・`shibuya.economy.ledger`・`shibuya.foundation.growth`
- 決定の ID: D-53

## [test_ledger.py](../../../../../../tests/economy/test_ledger.py)

金の台帳(U11)のテスト = 境界・経済設計書 §2.3 が要求する **pytest 8本**。

- 公開の関数とクラス
  - `test_5k_mock_day_still_fits_in_the_ring`(関数): 既定でバイト不変: 5,000 体では **リングが一周しない**(実測 8,884 行 ≤ 容量)。
  - `test_attached_household_cash_is_the_same_array`(関数): 世帯の現金は写しでなく採用(agents.money と同一配列)。
  - `test_deposit_creates_a_matching_bank_liability`(関数)
  - `test_depreciation_reduces_fixed_assets_without_moving_cash`(関数)
  - `test_employers_come_from_the_world_asset_or_a_synthetic_fallback`(関数): 雇用主 = W6 の組織台帳(``w6_org.parquet``)。無ければ合成。
  - `test_entry_capital_must_come_from_allowed_payers`(関数): 5本目: 参入資本は創業者預金・銀行貸出・外界からの transfer 由来のみ(ex nihilo 禁止)。
  - `test_faucet_sink_totals_by_account`(関数): 8本目: faucet/sink の科目別集計(月次 MER の素材)。
  - `test_flow_matrix_rows_and_columns_are_balanced`(関数): 3本目: 四重記入(行和=科目ごとに 0・列和=部門ごとに Δ現金)。
  - `test_frozen_arrays_reject_writes_outside_the_ledger`(関数)
  - `test_growth_declarations_pass_the_gate`(関数): 成長宣言(5欄)が 24step→30日の外挿で cap 内。
  - `test_hoard_is_reported_for_idle_balances`(関数): 7本目: 使われず溜まる現金/預金を退蔵項として計上する(§2.2 UO 教訓の監視点)。
  - `test_insufficient_funds_is_a_return_value_not_an_exception`(関数)
  - `test_net_worth_equals_real_assets_after_purchases_and_wages`(関数): 4本目(主検算): Σ純資産 = Σ実物資産 ⟺ Σ金融純資産 = 0。
  - `test_raw_capacity_is_proportional_to_n`(関数): D-53: リング容量は **N 比例**(6.5 行/体/日 × N × 保持日数=〔1-9・K17〕前は 3.0)・下限あり。
  - `test_raw_log_is_bounded_and_daily_aggregated`(関数): D-R2-6: 生ログは保持窓 N 日+リングバッファで有界・日次で集約行へ畳む。
  - `test_residual_threshold_gate`(関数): 6本目: 残差 > 閾値でゲート失敗(§2.4)。
  - `test_row_column_check_catches_a_direct_balance_assignment`(関数): 列和検査は「残高の直接代入」(単一API迂回)を捕まえる=これが検算①の本体。
  - `test_state_hash_is_deterministic`(関数)
  - `test_the_declaration_alone_never_exceeds_the_cap`(関数): D-53 の回帰: 宣言投影(72 B/体/日 × N)が cap を食い破らない。
  - `test_transfer_conserves_cash_over_all_sectors_including_row`(関数): 1本目: transfer は**外界を含む全部門の現金合計**を変えない(faucet も sink も)。
  - `test_transfer_many_handles_duplicate_payers_in_row_order`(関数): 同一支払者の複数行は行順の前置和で判定する(残高を超えた行以降は不足)。
  - `test_transfer_many_rejects_the_whole_batch_for_a_bad_pair`(関数)
  - `test_unknown_and_forbidden_codes_are_rejected`(関数): 2本目: 列挙にない科目・表にない部門対の transfer は実行不能(§2.2)。
- import している内部モジュール: `shibuya.economy.accounts`・`shibuya.economy.checks`・`shibuya.economy.ledger`・`shibuya.foundation.growth`・`shibuya.foundation.ports.ledger`
- 決定の ID: D-53

## [test_min_wage_human_bridge.py](../../../../../../tests/economy/test_min_wage_human_bridge.py)

〔11-01 §5・段 2 の 5〕最低賃金を ``human`` へ・床は machine のつなぎ(``params.bridge``)・違反の記録の器。

- 公開の関数とクラス
  - `test_a_bad_bridge_is_refused`(関数)
  - `test_a_broken_bridge_in_a_later_version_stops_the_run_at_the_start`(関数): 給料日に効いていない後の版のつなぎが壊れていても、組み立て(ランの始め)で落ちる。
  - `test_before_the_rule_is_in_force_nothing_is_counted`(関数)
  - `test_floor_with_shortfall_is_apply_floor_byte_for_byte_under_the_bridge`(関数)
  - `test_kinds_are_the_table_kinds`(関数)
  - `test_negative_control_high_wages_count_nothing`(関数): 負の対照: 賃金が床より上の体だけ=件数 0。
  - `test_no_bridge_is_none_and_the_ledger_id_is_optional`(関数)
  - `test_positive_control_counts_the_shortfall_and_the_bridge_lifts_it`(関数): 正の対照: 床を下回る賃金を合成した体で件数が立つ・つなぎの床が上げる=起きた違反は 0・払う額は床つき(前と同じ)。
  - `test_the_box_is_empty_at_the_start_and_has_no_window_words`(関数)
  - `test_the_filing_deadline_bridge_is_read_from_params_bridge`(関数)
  - `test_the_floor_follows_the_kind_and_the_bridge`(関数)
  - `test_the_hours_times_hourly_path_counts_but_has_no_floor`(関数): 2-1 の道(賃金の表の無い写し=月の時間 × 時給): 床の式は前から無い=数えるだけ。時給が既定(最低賃金)なら 0・
  - `test_the_repo_rows_are_human_with_a_machine_bridge`(関数)
  - `test_without_the_bridge_the_wage_stays_below_and_the_violation_is_recorded`(関数): つなぎを外した表(human だけ): 床を当てず下回ったまま払う=起きた違反を記録(金は湧かない=保存則の残差 0)。
- import している内部モジュール: `shibuya.economy.accounts`・`shibuya.economy.anchors`・`shibuya.economy.ledger`・`shibuya.economy.stage2`・`shibuya.economy.taxes`・`shibuya.economy.wages`・`shibuya.engine.rules.table`・`shibuya.foundation.decl.bridging`・`tests/economy/test_wage_occupation.py`
- 決定の ID: 11-01・11-01/§5

## [test_pricing.py](../../../../../../tests/economy/test_pricing.py)

行5 価格形成のエンジン側テスト(世界過程設計書 §4 行5 A案 + §8 H-1〜H-5)。

- 公開の関数とクラス
  - `test_calvo_draw_is_deterministic_and_frequencies_match`(関数)
  - `test_calvo_monthly_probabilities_are_by_sector`(関数): H-1: 小売 20-30%・飲食 5-10%・サービス 5%(一律 20% を改める)。
  - `test_clearing_is_the_minimum_of_demand_and_supply`(関数)
  - `test_deviation_cost_is_booked_as_a_sink_to_the_government`(関数): H-5「逸脱比例コスト(sink登録)」= 店舗→政府の transfer として台帳に載る。
  - `test_deviation_cost_is_proportional_to_the_gap_below_the_floor`(関数): H-5: 逸脱比例コストはフロアを下回ったぶんに比例(sink 登録)。
  - `test_floor_k_has_the_three_values_from_h2`(関数): H-2: k≈2.9(原価率35%・高級)/ 3.3(30%・平均)/ 5.0(20%・ドル箱)。
  - `test_parse_failure_keeps_the_previous_r_and_is_counted`(関数): H-3: 出力拒否/パース失敗は**前期 r を維持**し計数する(診断行)。
  - `test_propose_price_is_the_single_entry_point_for_the_llm_scalar`(関数): LLM の r → フロア・クリップ・逸脱コストまでを決定論で確定する入口。
  - `test_r_is_clipped_to_the_declared_range`(関数): H-3: r∈[0.7, 1.5] にクリップ(構造的上限)。
- import している内部モジュール: `shibuya.economy.accounts`・`shibuya.economy.checks`・`shibuya.economy.ledger`・`shibuya.economy.pricing`・`shibuya.foundation.rng`

## [test_rules42_credit.py](../../../../../../tests/economy/test_rules42_credit.py)

第 4 期 4-2 総量規制の検査と利息の上限(信用の器・呼び手なし=結果不変・R-118 §2-7)。

- 公開の関数とクラス
  - `test_before_the_lower_bound_the_check_stops`(関数): 〔検収 L5〕総量規制の行の asof は下限の印=それより前の日は「規則なし」にせず止まる。
  - `test_card_limit_ratio_is_blank_and_nothing_calls_the_checks`(関数)
  - `test_income_document_rule_is_a_field`(関数)
  - `test_interest_cap_bands`(関数)
  - `test_total_volume_cap_is_one_third_of_the_income`(関数)
- import している内部モジュール: `shibuya.economy.credit`・`shibuya.engine.rules.table`
- 決定の ID: R-118

## [test_rules42_ledger.py](../../../../../../tests/economy/test_rules42_ledger.py)

第 4 期 4-2 給与の天引きと店の預かり消費税(Q1)の台帳の動き(合成の台帳・組み立ての物は試験の代役)。

- 公開の関数とクラス
  - `test_a_short_store_pays_later_and_the_check_holds`(関数)
  - `test_outside_employer_pays_gross_from_the_outside_and_only_the_employee_share`(関数)
  - `test_payday_deducts_the_employee_share_and_pays_the_employer_share`(関数)
  - `test_register_tax_goes_to_the_deposit_and_to_the_government_at_the_deadline`(関数)
  - `test_two_synthetic_days_conserve_with_law`(関数)
  - `test_without_law_the_old_values_are_kept`(関数)
- import している内部モジュール: `shibuya.economy.accounts`・`shibuya.economy.checks`・`shibuya.economy.ledger`・`shibuya.economy.stage2`・`shibuya.economy.taxes`・`shibuya.engine.economy_rules`・`shibuya.foundation.journal.log`
- 決定の ID: 第 346

## [test_rules42_payroll.py](../../../../../../tests/economy/test_rules42_payroll.py)

第 4 期 4-2 給与の天引き(R-118 §2-6・§7-1・PENDING 仮-40 の Q4・Q7): 1 人の月の計算を手計算と突き合わせる。

- 公開の関数とクラス
  - `test_employee_total_never_exceeds_gross`(関数)
  - `test_enrollment_by_hours_employer_size_students_roles_and_missing_basis`(関数)
  - `test_full_time_hours_are_the_same_in_engine_and_economy`(関数)
  - `test_lower_bound_rows_stop_before_the_bound`(関数): 〔検収 L5〕下限の印の行を下限より前に引くと止まる(施行の前の普通の行は None のまま)。
  - `test_one_person_month_matches_the_hand_calculation`(関数)
  - `test_outside_employer_rows_are_enrolled_as_full_time`(関数): 〔検収 M2〕材料の無い行でも外の雇用主の行は「51 人以上の事業所の正社員」とみなす。
  - `test_resident_tax_takes_the_two_deductions`(関数): 〔検収 M1〕所得割の元=額面 − 給与所得控除(別表第一)− 社会保険料(本人の分)の 12 か月分。
  - `test_rows_not_in_force_give_zero`(関数)
  - `test_social_insurance_over_the_gross_takes_nothing`(関数)
  - `test_special_formula_versus_the_monthly_table_bracket`(関数)
  - `test_the_50_sen_rule`(関数)
  - `test_the_care_rate_is_only_for_ages_40_to_64`(関数)
  - `test_without_inputs_nothing_is_enrolled_but_taxes_apply`(関数)
- import している内部モジュール: `shibuya.economy.taxes`・`shibuya.engine.economy_rules`・`shibuya.engine.rules.table`
- 決定の ID: R-118・R-118 §1-2 #9・第 346

## [test_rules42_runs.py](../../../../../../tests/economy/test_rules42_runs.py)

第 4 期 4-2 のランの形(合成の世界の 2 日=給料日 2026-08-25 をまたぐ)。

- 公開の関数とクラス
  - `law`(関数)
  - `test_conserved_fails_when_the_deposit_check_breaks`(関数): 〔検収 L4〕預かり金の検算(積んだ − 移した − 残高=0)が ``RunResult.conserved`` に入る(負の対照)。
  - `test_on_keeps_the_register_tax_in_the_deposit_and_deducts_on_payday`(関数)
  - `test_removed_rules_42_switch_env_stops`(関数): 〔第346〕消した切替口: 環境変数 SHIBUYA_RULES_42 を与えると読み込みで止まる・腕を選ぶ口は無い。
  - `test_resume_equals_straight_with_the_deposit`(関数)
  - `test_resume_from_a_state_without_the_rules_key_is_refused`(関数): 〔第346〕見出しの ``economy_stage2`` に ``rules_42``(4-2 の前のラン)か ``rules_42b``(4-2 の値のラン)の無い状態の
  - `test_resume_refuses_a_header_without_rules_42`(関数): 見出しの ``rules_42`` が無い状態のファイル(4-2 の前のラン)からは再開できない(〔第346〕切替口は消した・天引きは状態を
- import している内部モジュール: `shibuya.cli`・`shibuya.economy.accounts`・`shibuya.economy.census`・`shibuya.economy.goods`・`shibuya.economy.ledger`・`shibuya.engine.economy_rules`・`shibuya.engine.economy_stage2`・`shibuya.engine.resume`・`shibuya.engine.run`・`shibuya.foundation.ports.ledger`・`shibuya.world.state`
- 環境変数: `SHIBUYA_RULES_42`・`os.environ` をまるごと使う
- 決定の ID: 第 346

## [test_rules42b_ledger.py](../../../../../../tests/economy/test_rules42b_ledger.py)

第 4 期 4-2b 給料日の台帳の動き(合成の台帳)と、合成の世界の 2 日のラン。

- 公開の関数とクラス
  - `law`(関数)
  - `test_on_minus_off_is_the_contribution_and_the_age_caps`(関数)
  - `test_payday_moves_the_child_care_contribution_with_the_employer_share`(関数)
  - `test_payroll_inputs_are_always_4_2b_at_build_time`(関数): 〔第346〕組み立ては常に ``rules_42b`` 真(切替口は消した)。偽は直に作る部品の口だけ。
  - `test_removed_rules_42b_switch_env_stops`(関数): 〔第346〕消した切替口: 環境変数 SHIBUYA_RULES_42B を与えると読み込みで止まる・腕を選ぶ口は無い。
  - `test_resume_refuses_a_header_without_rules_42b`(関数): 〔第346〕見出しに ``rules_42b=on`` の無い状態のファイル(4-2 の値のラン)からは再開できない(切替口は消した)。
  - `test_stage_b_payday_has_no_undeclared_writes`(関数): 段 B(系の前後で変わった欄 ⊆ 宣言・``SHIBUYA_SYSTEMS_CHECK=1``): 給料日(2026-08-25 の締め)を含む合成の 2 日で宣言の外 0。
  - `test_the_unit_base_port_keeps_the_4_2_values_and_records`(関数): 部品の単体試験の基準の口(``rules_42b=False`` を直に作る=ランの口からは選べない)は 4-2 の値と記録のまま。
  - `test_two_synthetic_days`(関数): 合成の世界の 2 日(給料日をまたぐ)=4-2b の値で天引き(〔第346〕4-2 の値のランとの比べは旧値の切替口と一緒に消した=
- import している内部モジュール: `shibuya.economy.accounts`・`shibuya.economy.census`・`shibuya.economy.goods`・`shibuya.economy.ledger`・`shibuya.economy.stage2`・`shibuya.economy.taxes`・`shibuya.engine.economy_rules`・`shibuya.engine.economy_stage2`・`shibuya.engine.run`・`shibuya.foundation.journal.log`・`shibuya.foundation.ports.ledger`・`shibuya.world.state`
- 環境変数: `SHIBUYA_RULES_42B`・`SHIBUYA_SYSTEMS_CHECK`・`os.environ` をまるごと使う
- 決定の ID: 第 346

## [test_rules42b_payroll.py](../../../../../../tests/economy/test_rules42b_payroll.py)

第 4 期 4-2b 規則の表の空欄 3 件を埋めた値(R-118 §10-2=親の一次確認)の天引きを手計算と突き合わせる。

- 公開の関数とクラス
  - `test_adjustment_credit_border_and_floor`(関数)
  - `test_basic_deduction_bands_at_the_borders`(関数)
  - `test_child_care_contribution_is_not_the_child_support_levy`(関数): 子ども・子育て拠出金(0.36%・事業主だけ・厚年の標準報酬)と子ども・子育て支援金(0.23%・折半・健保の標準報酬)は別の行。
  - `test_child_care_contribution_is_the_pension_grade_times_rate_employer_only`(関数)
  - `test_child_care_row_before_its_lower_bound_stops`(関数)
  - `test_employee_total_never_exceeds_gross`(関数)
  - `test_no_hard_coded_ages_or_amounts_in_the_reader`(関数): AST: 年齢の上限・控除の額・率・限度は規則の表から(読み手の taxes.py に直書きが無い)。
  - `test_non_taxable_end_to_end_both_levies_are_zero`(関数): 合計所得 45 万円以下は均等割も所得割も 0(境の上下を月の額面で)。未成年者は 135 万円以下で 0。
  - `test_non_taxable_limits_and_minor`(関数)
  - `test_off_reproduces_the_4_2_values`(関数): 部品の単体試験の基準の口(``r42b=False``・〔第346〕ランの切替口は消した)=4-2 の値(f27377a の手計算)・雇用主の分は
  - `test_one_person_month_matches_the_hand_calculation`(関数)
  - `test_pension_stops_at_70_and_health_at_75`(関数)
  - `test_resident_tax_is_zero_before_the_fiscal_year_row`(関数)
  - `test_rows_absent_from_the_table_give_zero`(関数): 表に 4-2b の行が無い写し(行の無い項目は 0=控除なし・非課税なし・拠出金 0・年齢の上限なし)。
  - `test_the_rows_are_the_r118_10_2_values`(関数): 写し検査: 表の値は R-118 §10-2 の表の値(43/29/15 万円・2,400/2,450/2,500 万円・5%・200 万円・2,500 円・45 万円・
  - `test_unknown_age_stays_inside_the_caps`(関数)
- import している内部モジュール: `shibuya.economy.taxes`・`shibuya.engine.economy_rules`・`shibuya.engine.rules.table`
- 決定の ID: R-118・第 346

## [test_single_write_path.py](../../../../../../tests/economy/test_single_write_path.py)

**単一API の静的検査**(境界・経済設計書 §2.3 / 世界過程設計書 §7.1)。

- 公開の関数とクラス
  - `test_attached_agent_money_is_not_unfrozen_by_the_ledger`(関数): 採用した ``agents.money`` のフラグは台帳が触らない(窓の持ち主は resolve)。
  - `test_economy_never_calls_the_world_write_window`(関数): ``.writable(`` / ``.thaw(`` は engine/resolve.py と state モジュールの専有。
  - `test_engine_does_not_import_economy`(関数): 依存逆転: engine は economy を import しない(import-linter の層契約の同型検査)。
  - `test_numpy_add_at_ignores_the_readonly_flag`(関数): 発見の記録: ``np.add.at`` は読み取り専用配列に**書けてしまう**。
  - `test_only_goods_module_touches_the_stock_arrays`(関数): 在庫配列に触れるのは economy/goods.py だけ(= move_goods 単一API)。
  - `test_only_ledger_module_touches_the_balance_arrays`(関数): 残高配列に触れるのは economy/ledger.py と economy/ops.py だけ(= transfer 単一API)。
  - `test_only_the_owning_modules_open_the_write_window`(関数): ``_open``(書き込み窓)を economy の中で呼べるのは台帳自身だけ。
  - `test_runtime_guard_rejects_direct_writes`(関数): (a) 実行時の強制: 台帳の配列は既定で読み取り専用。
- import している内部モジュール: `shibuya.economy.accounts`・`shibuya.economy.goods`・`shibuya.economy.ledger`・`shibuya.engine.resolve`・`tests/_places.py`

## [test_t3_redundant_equation.py](../../../../../../tests/economy/test_t3_redundant_equation.py)

T3(SFC の冗長方程式)の毎期検算(D-85 (a)・ユーザー決定 2026-09-17)。

- 公開の関数とクラス
  - `test_a_broken_deposit_leg_is_caught_even_when_the_rows_and_columns_are_clean`(関数)
  - `test_a_direct_balance_assignment_breaks_the_column_check`(関数): 列和(部門ごとの Σ科目)= Δ現金 が破れる。行和と預金脚は無事=どこが壊れたか分かる。
  - `test_a_one_day_ledger_has_no_monthly_census`(関数)
  - `test_offsetting_direct_assignments_slip_past_check2_but_not_t3`(関数): **T3 を足した理由**: 検算②は集計の恒等式なので部門間で相殺すると通ってしまう。
  - `test_t3_goes_through_the_same_check1_function`(関数): T3 は検算①の**窓違い**——同じ窓を渡せば ``flow_matrix_balanced`` と同じ答え。
  - `test_t3_passes_on_a_ledger_that_only_used_transfer`(関数)
  - `test_the_monthly_check_only_fires_at_the_month_break`(関数)
  - `test_the_monthly_mer_carries_t3_and_its_breakdown`(関数): 月次 MER の戻りに ``t3_ok`` と内訳が出る(**固定表 parquet の列は増えない**)。
  - `test_the_open_day_is_inside_the_window`(関数): まだ畳んでいない当日の取引も窓に入る(締める前に走らせても答えが合う)。
- import している内部モジュール: `shibuya.economy.accounts`・`shibuya.economy.census`・`shibuya.economy.checks`・`shibuya.economy.ledger`・`shibuya.foundation.ports.ledger`
- 決定の ID: D-85

## [test_wage_occupation.py](../../../../../../tests/economy/test_wage_occupation.py)

賃金を職業ごとの実データから(小さな版上げ・2026-10-17・回答 10-13b §7 の 3)。

- 公開の関数とクラス
  - `test_apply_floor_and_month_hours`(関数)
  - `test_attr_fns_wage_equals_runtime_wage_values_with_the_same_draw`(関数)
  - `test_build_and_runtime_share_one_function`(関数)
  - `test_mapping_average_and_given`(関数)
  - `test_min_wage_floor_reads_only_the_rules_table`(関数)
  - `test_occupation_wages_are_pure`(関数)
  - `test_payroll_applies_the_floor_on_a_payday_with_the_rule_in_force`(関数)
  - `test_payroll_has_no_floor_before_the_rule_is_in_force`(関数)
  - `test_payroll_pays_occupation_wages_with_matching_funding`(関数)
  - `test_payroll_pays_the_outside_employer_from_the_rest_of_the_world`(関数): 〔第 4 期 4-3 段 10・検収 M3〕外の雇用主(閉じた表の外の組織の番号)の雇用の行は外界から払う(登録済みの faucet
  - `test_payroll_w17_arm_is_removed`(関数): 〔第 4 期 4-3 版上げ 3 回目の第 2 部〕旧値の腕 w17(W17 の勤務時間 × 最低賃金)は消した=渡すと止まる(再現は安定版の
  - `test_persona_words_reads_only_wanted_rows_and_skips_l4`(関数)
  - `test_reader_refuses_a_wrong_md5_and_returns_none_when_absent`(関数)
  - `test_removed_wage_switch_env_and_cli_flag_stop`(関数): 〔第 2 部〕消した切替口: 環境変数 SHIBUYA_WAGE を与えると読み込みで止まる・CLI の --wage は無い。
  - `test_runtime_reader_equals_the_build_reader`(関数)
  - `test_tables_absent_falls_back_with_a_note`(関数)
  - `test_wage_inputs_without_population_and_with_a_fake_population`(関数)
  - `test_wage_path_does_not_read_w17_hours_ast_with_a_negative_control`(関数)
  - `test_wage_path_header_and_resume_check`(関数): 賃金の道は occupation だけ(〔第 2 部〕腕 w17 と切替口は消した)。見出しは賃金の道を持ち、見出しに無い(版上げの前)・
- import している内部モジュール: `shibuya.build.pop.attr_fns`・`shibuya.build.pop.w21_money`・`shibuya.build.pop.w21_sources`・`shibuya.cli`・`shibuya.core.wage_formula`・`shibuya.economy.accounts`・`shibuya.economy.anchors`・`shibuya.economy.ledger`・`shibuya.economy.stage2`・`shibuya.economy.wages`・`shibuya.engine.economy_stage2`・`shibuya.engine.rights.initial`・`shibuya.foundation.journal.log`
- 読む試験: `tests/economy/test_min_wage_human_bridge.py`
- 環境変数: `SHIBUYA_WAGE`・`os.environ` をまるごと使う
- 決定の ID: 10-13b/§7・第 337・第 346
