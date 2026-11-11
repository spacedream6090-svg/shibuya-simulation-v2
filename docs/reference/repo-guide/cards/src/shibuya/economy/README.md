# src/shibuya/economy

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 15 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../src/shibuya/economy/__init__.py)

economy: 台帳/transfer/検算/センサス入力。engine の transfer 単一API経由のみ。

- import している内部モジュール: `shibuya.economy.accounts`・`shibuya.economy.checks`・`shibuya.economy.entry_capital`・`shibuya.economy.goods`・`shibuya.economy.ledger`
- 呼び手: `shibuya.cli`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 決定の ID: D-13

## [accounts.py](../../../../../../../src/shibuya/economy/accounts.py)

economy.accounts — 部門・貸借対照表の行・**取引科目の列挙と faucet/sink 表**(U11 §2.1-2.2)。

- 公開の関数とクラス
  - `AccountCode`(クラス): 取引科目(§2.2 の 12 科目 + 残差 + 退蔵 + 逸脱比例コスト)。
  - `AccountSpec`(クラス): 1科目の仕様(許可された部門対 + タグ + 由来)。
  - `BalanceLine`(クラス): 貸借対照表6行(§2.2)。``NET_WORTH`` だけは**導出量**(配列を持たない)。
  - `FlowKind`(クラス): faucet/sink 表の区分(§2.2)。
  - `RegisteredFlow`(クラス): 名前のある流れ 1 つ(口の約束 1-9 の約束 (3)「faucet/sink の全登録」を 2-1 で直した形)。
  - `Sector`(クラス): 部門(§2.1 の6部門)。値は ``engine.ledger_api.SECTOR_*`` と 1 対 1。
  - `faucet_sink_table`(関数): faucet/sink 表を人が読む形で返す(科目・支払・受取・区分・タグ)。
  - `flow_kind`(関数): faucet / sink / internal の判定(**規則で導く**=表の二重管理を作らない)。
  - `flow_registry_table`(関数): 名前のある流れの全登録を人が読む形で(名前・科目・支払・受取・区分・段)。
  - `is_allowed`(関数): (科目, 支払部門, 受取部門)が faucet/sink 表にあるか。
  - `registered_cells`(関数): 登録の (科目, 支払, 受取) → 区分(同じ組の名前が 2 つ以上あっても区分は 1 つ=登録の試験が見る)。
- import している内部モジュール: `shibuya.foundation.ports.ledger`
- 呼び手: `shibuya.cli`・`shibuya.economy`・`shibuya.economy.anchors`・`shibuya.economy.census`・`shibuya.economy.checks`・`shibuya.economy.credit`・`shibuya.economy.entry_capital`・`shibuya.economy.goods`・`shibuya.economy.ledger`・`shibuya.economy.ops`・`shibuya.economy.pricing`・`shibuya.economy.stage2`・`shibuya.economy.tax_deposit`・`tools/vocab/adjudicate.py`
- 読む試験: `tests/economy/cp2/head_goods_136fdbb.py`・`tests/economy/cp2/head_ledger_136fdbb.py`・`tests/economy/cp2/test_cp2_event_links.py`・`tests/economy/cp2/test_cp2_flow_sum.py`・`tests/economy/cp2/test_cp2_k17_capacity_and_overflow.py`・`tests/economy/cp2/test_cp2_nine_ops_equivalence.py`・`tests/economy/cp2/test_cp2_write_window.py`・`tests/economy/stage2/test_stage2_account_and_conservation.py`・`tests/economy/stage2/test_stage2_calls.py`・`tests/economy/stage2/test_stage2_default_2_4.py`・`tests/economy/stage2/test_stage2_guards.py`・`tests/economy/stage2/test_stage2_money_rules.py`・`tests/economy/stage2/test_stage2_resume.py`・`tests/economy/stage2/test_stage2_rules_credit_atm.py`・`tests/economy/stage2/test_stage2_runs.py`・`tests/economy/stage2/test_stage2_world_two_day.py`・`tests/economy/stage2/test_wage_occupation_runs.py`・`tests/economy/test_accounts.py`・`tests/economy/test_anchors.py`・`tests/economy/test_census.py`・`tests/economy/test_entry_capital.py`・`tests/economy/test_goods.py`・`tests/economy/test_ledger.py`・`tests/economy/test_min_wage_human_bridge.py`・`tests/economy/test_pricing.py`・`tests/economy/test_rules42_ledger.py`・`tests/economy/test_rules42_runs.py`・`tests/economy/test_rules42b_ledger.py`・`tests/economy/test_single_write_path.py`・`tests/economy/test_t3_redundant_equation.py`・`tests/economy/test_wage_occupation.py`・`tests/engine/events/test_e_vocab_is_closed.py`・`tests/engine/processes/test_goods_flow.py`・`tests/engine/processes/test_rail.py`・`tests/engine/test_ledger_wiring.py`・`tests/engine/test_processes_run.py`・`tests/test_cli.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 決定の ID: 第 346

## [anchors.py](../../../../../../../src/shibuya/economy/anchors.py)

economy.anchors — §2.5 の**金額アンカー**(公的値・mechanism)と初期財布/月次賃金。

- 公開の関数とクラス
  - `Anchor`(クラス): 1つの現実整合アンカー(値+単位+出典文字列+等級)。
  - `MinWageTerms`(クラス): 〔11-01 §5〕``asof`` の日の東京都の最低賃金の行の読み(値・出どころ・行の kind・つなぎ)。
  - `WalletKind`(クラス): 財布の初期化に使う個体種別(``agents.state.AgentKind`` と**同じ値**・写し)。
  - `check_rule_bridges`(関数): 〔検収 L1〕表の全部の行(全部の版)の ``params.bridge`` を検査する(壊れていれば ``ValueError``=ランの始めに落とす)。
  - `consumption_tax_rate`(関数): 〔2-1〕``asof`` の日に効いている消費税の国+地方の合計の率(分数)と出どころ。
  - `daily_spending`(関数): 種別配列 → 1日あたり消費支出[円]。
  - `initial_wallets`(関数): 初期財布[円]を対数正規で引く(expedient・§2.6「財布の現金初期分布」)。
  - `min_wage_floor`(関数): 〔賃金の小さな版上げ・検収 M1〕最低賃金法の床(4 条 2 項)の値[円/時]と出どころ=規則の表の ``minimum_wage.tokyo``
  - `min_wage_hourly`(関数): 〔2-1〕``asof`` の日に効いている東京都の最低賃金[円/時]と出どころ(規則の表の最初の読み手)。
  - `min_wage_terms`(関数): 〔11-01 §5〕``asof`` の日に効いている ``minimum_wage.tokyo`` の版の読み(**直書きの値に戻さない**)。
  - `monthly_wage_amounts`(関数): 月次賃金[円] = 労働時間 × 時給 × 割増係数(外生・§2.7 第1陣)。
  - `monthly_wages`(関数): 雇用主(または域外雇用主)→ 世帯の月次賃金を**一括** transfer する。
  - `rule_bridge`(関数): 〔11-01 §5〕規則の表の行の ``params.bridge`` を検査して返す(無い行は ``None``)。
- import している内部モジュール: `shibuya.economy.accounts`・`shibuya.engine.rules.table`
- 呼び手: `shibuya.cli`・`shibuya.economy.goods`・`shibuya.economy.stage2`・`shibuya.economy.taxes`・`shibuya.economy.wages`
- 読む試験: `tests/economy/cp2/head_goods_136fdbb.py`・`tests/economy/stage2/test_stage2_money_rules.py`・`tests/economy/stage2/test_stage2_rules_credit_atm.py`・`tests/economy/test_accounts.py`・`tests/economy/test_anchors.py`・`tests/economy/test_entry_capital.py`・`tests/economy/test_goods.py`・`tests/economy/test_min_wage_human_bridge.py`・`tests/economy/test_wage_occupation.py`・`tests/engine/rules/test_rules42_table.py`・`tests/engine/test_waste_sink_report.py`・`tests/test_cli.py`
- 読む試験(道筋で): `tests/engine/bridging/test_bridging_ledger.py`・`tests/engine/rules/test_rules_table_schema.py`・`tests/test_places_guard.py`
- 決定の ID: 11-01/§5・D-16

## [census.py](../../../../../../../src/shibuya/economy/census.py)

economy.census — 日次(軽量)センサスと月次 MER・ゲート判定(§2.4)。

- 公開の関数とクラス
  - `CensusGate`(クラス): ゲート判定(§2.4「ゲート失敗=較正・holdout照合に使わない」)。
  - `census_gate`(関数): ゲート判定(残差超・検算②不成立・棚卸差異超で失敗)。
  - `daily_census`(関数): 日次(軽量)センサスの1行。
  - `flow_row_kind`(関数): 部門軸の 1 行 → ``FlowKind`` の小文字名(``faucet`` / ``sink`` / ``internal`` …)。
  - `is_month_end`(関数): 畳んだ日数が 1 か月ぶんの区切りに達したか(0 日=まだ月次センサスは走らない)。
  - `monthly_census_t3`(関数): **月次センサスが立つ日だけ** T3 を走らせる(engine への注入口・D-85 (a))。
  - `monthly_mer`(関数): 月次 MER(EVE Online 型の**固定表**)。
  - `monthly_t3`(関数): T3(冗長方程式)の検算を走らせて**記録できる形**で返す(D-85 (a))。
  - `write_daily_census`(関数): 日次センサスを Parquet(zstd)で書く。列は ``DAILY_COLUMNS`` 固定。
  - `write_monthly_mer`(関数): 月次 MER を Parquet(zstd)で書く(科目別の縦持ち + 総量列)。
  - `write_monthly_mer_sectors`(関数): 月次 MER の**部門軸**(``flows`` の長い表)を Parquet(zstd)で書く(D-76 (a))。
- import している内部モジュール: `shibuya.economy.accounts`・`shibuya.economy.checks`
- 呼び手: `shibuya.cli`
- 読む試験: `tests/economy/cp2/test_cp2_flow_sum.py`・`tests/economy/cp2/test_cp2_k17_capacity_and_overflow.py`・`tests/economy/cp2/test_cp2_writes_declared.py`・`tests/economy/stage2/test_stage2_runs.py`・`tests/economy/test_census.py`・`tests/economy/test_rules42_runs.py`・`tests/economy/test_rules42b_ledger.py`・`tests/economy/test_t3_redundant_equation.py`・`tests/engine/test_census_out.py`・`tests/engine/test_ledger_wiring.py`・`tests/engine/test_processes_run.py`・`tests/engine/test_t3_manifest.py`・`tests/engine/test_waste_sink_report.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 決定の ID: 11-01・11-01/§2・D-76・D-85・第 204・第 305

## [checks.py](../../../../../../../src/shibuya/economy/checks.py)

economy.checks — **検算2本**(Caiani 2016)・残差ゲート・退蔵計上・ex nihilo 検査。

- 公開の関数とクラス
  - `CheckReport`(クラス): 日次ゲートに使うまとめ。
  - `FlowCheck`(クラス): 検算①(四重記入)の結果。
  - `HoardReport`(クラス): 退蔵項(§2.2「使われず溜まる現金/預金=UO教訓の監視点」)。
  - `NetWorthCheck`(クラス): 検算②(純資産合計 = 実物資産)の結果。
  - `T3Check`(クラス): T3(SFC の冗長方程式)= 検算①の3検査を**実データ**に対して走らせた結果。
  - `check_all`(関数): 日次ゲートに使う全検査(§2.4)。
  - `conservation_check`(関数): 〔第 2 期 2-1・口の約束 1-9 の約束 (3)〕締めの日の保存則の検算(faucet/sink の全登録)。
  - `ex_nihilo_ok`(関数): 参入資本が許された出所のみから来ているか(§2.3 ex nihilo 禁止)。
  - `faucet_sink_totals`(関数): faucet/sink の**科目別**集計(§2.3 pytest 8本目・§2.4 月次 MER の素材)。
  - `flow_matrix_balanced`(関数): 検算①: 四重記入(逐次ループ宣言: 部門×科目=90)。
  - `hoard_report`(関数): 退蔵項の計上: ``days`` 日以上 現金/預金が動いていない主体の残高。
  - `net_worth_equals_real_assets`(関数): 検算②(主検算・O(N)総和)。``goods`` を渡すと在庫評価額を U-Goods 側から取る。
  - `residual_gate`(関数): 残差科目のゲート(§2.4「残差>閾値はゲート失敗」)。
  - `t3_check`(関数): T3: 検算①の3検査を**実データ**で走らせる(D-85 (a)・月次センサスの時点)。
  - `tax_deposit_check`(関数): 〔第 4 期 4-2・Q1〕店の預かり消費税の検算(保存則の科目「店の預かり消費税」)。
- import している内部モジュール: `shibuya.economy.accounts`
- 呼び手: `shibuya.economy`・`shibuya.economy.census`・`shibuya.economy.ledger`・`shibuya.economy.stage2`
- 読む試験: `tests/economy/cp2/test_cp2_flow_sum.py`・`tests/economy/stage2/test_stage2_account_and_conservation.py`・`tests/economy/test_census.py`・`tests/economy/test_goods.py`・`tests/economy/test_ledger.py`・`tests/economy/test_pricing.py`・`tests/economy/test_rules42_ledger.py`・`tests/economy/test_t3_redundant_equation.py`・`tests/engine/test_ledger_wiring.py`・`tests/engine/test_processes_run.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 決定の ID: D-85

## [credit.py](../../../../../../../src/shibuya/economy/credit.py)

economy.credit — 信用の器(第 2 期 2-1・決定 10-12 §4-11 の信用 C1〜C3・**器だけ=動かない**)。

- 公開の関数とクラス
  - `CreditBook`(クラス): 貸付の行の器(列ごとの配列)。2-1 では行を足す呼び手が無い(``capacity=0`` の空の器)。
  - `interest_cap_rate`(関数): 〔第 4 期 4-2〕利息制限法 1 条の年率の上限(元本の帯ごと・分母 10,000 の整数=万分率)と出どころ(**呼び手なし**=器)。
  - `repay_due`(関数): C3: 返済日の行の返済を口座から自動で払い、足りない行は延滞を記録する(**呼び手なし**=試験だけ)。
  - `total_volume_check`(関数): 〔第 4 期 4-2〕総量規制の検査(貸す側の機械の検査・**呼び手なし**=器)。
- import している内部モジュール: `shibuya.economy.accounts`・`shibuya.economy.ops`・`shibuya.economy.taxes`
- 呼び手: `shibuya.economy.ledger`
- 読む試験: `tests/economy/stage2/test_stage2_guards.py`・`tests/economy/stage2/test_stage2_rules_credit_atm.py`・`tests/economy/test_rules42_credit.py`
- 読む試験(道筋で): `tests/economy/stage2/test_stage2_writers.py`・`tests/test_places_guard.py`
- 決定の ID: 10-12/§4-11・R-106・R-118

## [entry_capital.py](../../../../../../../src/shibuya/economy/entry_capital.py)

economy.entry_capital — 店舗の**参入資本を経済センサスから按分**する(D-13・C5)。

- 公開の関数とクラス
  - `EntryCapitalReport`(クラス): 参入資本の検算(合計・大分類別・貨幣供給に対する比率)。
  - `annual_sales`(関数): POI ごとの 1事業所当たり年商[円/年]\(``(n_poi,)`` int64)。
  - `entry_capital_report`(関数): 参入資本の検算行を作る(合計 = 個別和・大分類別内訳・貨幣供給比)。
  - `industry_of`(関数): POI カテゴリ → 産業大分類コード(未知は ``DEFAULT_INDUSTRY``)。
  - `ledger_entry_capital_share`(関数): 台帳から直に測る (店舗の現金+預金[円], 貨幣供給 M[円], 比率)。
  - `population_scale`(関数): 母集団比 ρ = n / 400,000(``None`` なら 1.0=実スケール)。
  - `price_band`(関数): カテゴリ名 → 価格帯 0..2。
  - `store_entry_capital`(関数): 店舗ごとの参入資本[円]\(``(n_poi,)`` int64・**決定論**・乱数なし)。
- import している内部モジュール: `shibuya.economy.accounts`・`shibuya.economy.goods`
- 呼び手: `shibuya.cli`・`shibuya.economy`
- 読む試験: `tests/economy/test_entry_capital.py`・`tests/test_cli.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 決定の ID: D-13・D-16

## [goods.py](../../../../../../../src/shibuya/economy/goods.py)

economy.goods — 物の保存則(U-Goods)。``move_goods`` **単一API**と SKU 別収支。

- 公開の関数とクラス
  - `GoodsCode`(クラス): 物の科目(§7.1 の faucet/sink 列挙 + 内部移動 + 残差)。
  - `GoodsLedger`(クラス): SKU 別の棚在庫・廃棄ビン・世帯合計・外界(bbox 外)を持つ物の台帳。
  - `GoodsRef`(クラス): 物の参照 = (置き場, 索引)。索引の意味: 店舗=poi_id・世帯/外界/収集=0。
  - `NodeKind`(クラス): 物の置き場(``move_goods`` の from / to)。
  - `SkuRegistry`(クラス): SKU 登録簿(全世界で 1 つ)。
  - `WasteBand`(クラス): 廃棄 sink の band 判定(検算②・台帳行 W1)。
  - `delivery_capacity_for`(関数): 納品ログのリングバッファ容量[行]を **N から**決める(D-53・2026-09-10)。
  - `delivery_event_ids_declaration`(関数): 〔1-9〕納品ログの行の目印の列(出来事の id=12 B/行)の成長宣言(1-3 の L8)。輪と同じ容量・保持窓。
  - `goods_flow_kind`(関数): faucet / sink / internal の判定(§7.1 の列挙をそのまま規則化)。
  - `goods_is_allowed`(関数): (科目, 置き場, 置き場)が物の faucet/sink 表にあるか。
  - `growth_declarations`(関数): 物の台帳の状態成長宣言(D-R2-6 の 5 欄)。
- import している内部モジュール: `shibuya.economy.accounts`・`shibuya.economy.anchors`・`shibuya.economy.pricing`・`shibuya.foundation.growth`
- 呼び手: `shibuya.economy`・`shibuya.economy.entry_capital`
- 読む試験: `tests/economy/cp2/test_cp2_event_links.py`・`tests/economy/cp2/test_cp2_flow_sum.py`・`tests/economy/cp2/test_cp2_k17_capacity_and_overflow.py`・`tests/economy/cp2/test_cp2_nine_ops_equivalence.py`・`tests/economy/cp2/test_cp2_writes_declared.py`・`tests/economy/stage2/test_stage2_runs.py`・`tests/economy/test_census.py`・`tests/economy/test_entry_capital.py`・`tests/economy/test_goods.py`・`tests/economy/test_rules42_runs.py`・`tests/economy/test_rules42b_ledger.py`・`tests/economy/test_single_write_path.py`・`tests/engine/events/test_e_vocab_is_closed.py`・`tests/engine/processes/test_goods_flow.py`・`tests/engine/test_ledger_wiring.py`・`tests/engine/test_processes_run.py`・`tests/engine/test_waste_sink_report.py`
- 読む試験(道筋で): `tests/economy/cp2/test_cp2_transfer_only_writer.py`・`tests/engine/processes/test_rate_rules_1101.py`・`tests/engine/systems/test_stage_a_guard.py`・`tests/test_places_guard.py`
- 状態台帳の行
  - 持ち主 `ledger.goods`(`GoodsLedger`)
    - `A` 金と物の台帳の行の目印の列・transfer の計器(第 1 期 1-9)(挙動 diag・復元 discardable) 道筋 `ledger.goods._dl_event_seq`・`ledger.goods._dl_event_t_ns` 書ける系: close_final・day_close・duties・phase_c・world
    - `O59` GoodsLedger _shelf・_bin・_sold_today・_day(挙動 behavior・復元 required) 道筋 `ledger.goods._bin`・`ledger.goods._day`・`ledger.goods._shelf`・`ledger.goods._sold_today` 書ける系: close_final・day_close・duties・phase_c・world
    - `O60` GoodsLedger 配達ログのリング(挙動 no・復元 discardable) 道筋 `ledger.goods._dl_code`・`ledger.goods._dl_poi`・`ledger.goods._dl_qty`・`ledger.goods._dl_slot`・`ledger.goods._dl_tick` 書ける系: close_final・day_close・duties・phase_c・world
    - `O79` GoodsLedger _shelf_age・_household_sku(挙動 behavior・復元 required) 道筋 `ledger.goods._household_sku`・`ledger.goods._shelf_age` 書ける系: close_final・day_close・duties・phase_c・world
    - `O80` GoodsLedger の保存則の項(_row_sku・_waste_sku・_inflow・_outflow・_residual・_open_stock・廃棄の g)(挙動 diag・復元 required) 道筋 `ledger.goods._day_waste_g`・`ledger.goods._inflow`・`ledger.goods._last_close`・`ledger.goods._open_stock`・`ledger.goods._outflow`・`ledger.goods._residual`・`ledger.goods._row_sku`・`ledger.goods._waste_g_daily`・`ledger.goods._waste_sku`・`ledger.goods.store_waste_g_total` 書ける系: close_final・day_close・duties・phase_c・world
    - `O81` GoodsLedger n_moves・rejections(挙動 diag・復元 discardable) 道筋 `ledger.goods.n_moves`・`ledger.goods.rejections` 書ける系: close_final・day_close・duties・phase_c・world
    - `O93` GoodsLedger 配達ログの位置(_dl_pos・_dl_head・_dl_marks・n_delivery_dropped)(挙動 diag・復元 required) 道筋 `ledger.goods._dl_head`・`ledger.goods._dl_marks`・`ledger.goods._dl_pos`・`ledger.goods.n_delivery_dropped` 書ける系: close_final・day_close・duties・phase_c・world
- 決定の ID: D-52・D-53・第 304・第 305

## [ledger.py](../../../../../../../src/shibuya/economy/ledger.py)

economy.ledger — 金の台帳(U11)。``transfer`` **単一API**と取引フロー行列。

- 公開の関数とクラス
  - `DayClose`(クラス): ``on_day_end`` の戻り(その日の畳み込み結果)。
  - `EmployerTable`(クラス): 雇用主(組織)の最小表 = 世界データ W6 の ``w6_org.parquet`` から読む。
  - `Ledger`(クラス): 6部門の貸借対照表 SoA + 取引フロー行列 + 生ログ。
  - `event_ids_declaration`(関数): 〔1-9〕生ログの行の目印の列(出来事の id=t_ns 8 B+seq 4 B=12 B/行)の成長宣言(1-3 の L8)。
  - `growth_declarations`(関数): 金の台帳の状態成長宣言(D-R2-6 の 5 欄)。
  - `load_employers`(関数): 雇用主の表を読む(無ければ合成)。
  - `raw_capacity_for`(関数): 生ログのリングバッファ容量[行]を **N から**決める(D-53・2026-09-10)。
- import している内部モジュール: `shibuya.economy.accounts`・`shibuya.economy.checks`・`shibuya.economy.credit`・`shibuya.economy.ops`・`shibuya.economy.stage2`・`shibuya.foundation.growth`・`shibuya.foundation.hashing`・`shibuya.foundation.ports.ledger`・`shibuya.foundation.time_consts`
- 呼び手: `shibuya.cli`・`shibuya.economy`・`shibuya.economy.ops`
- 読む試験: `tests/economy/cp2/test_cp2_event_links.py`・`tests/economy/cp2/test_cp2_flow_sum.py`・`tests/economy/cp2/test_cp2_k17_capacity_and_overflow.py`・`tests/economy/cp2/test_cp2_nine_ops_equivalence.py`・`tests/economy/cp2/test_cp2_transfer_only_writer.py`・`tests/economy/cp2/test_cp2_write_window.py`・`tests/economy/cp2/test_cp2_writes_declared.py`・`tests/economy/stage2/test_stage2_account_and_conservation.py`・`tests/economy/stage2/test_stage2_calls.py`・`tests/economy/stage2/test_stage2_guards.py`・`tests/economy/stage2/test_stage2_money_rules.py`・`tests/economy/stage2/test_stage2_rules_credit_atm.py`・`tests/economy/stage2/test_stage2_runs.py`・`tests/economy/test_anchors.py`・`tests/economy/test_census.py`・`tests/economy/test_entry_capital.py`・`tests/economy/test_goods.py`・`tests/economy/test_ledger.py`・`tests/economy/test_min_wage_human_bridge.py`・`tests/economy/test_pricing.py`・`tests/economy/test_rules42_ledger.py`・`tests/economy/test_rules42_runs.py`・`tests/economy/test_rules42b_ledger.py`・`tests/economy/test_single_write_path.py`・`tests/economy/test_t3_redundant_equation.py`・`tests/economy/test_wage_occupation.py`・`tests/engine/memory/test_m0_store_schema.py`・`tests/engine/processes/test_goods_flow.py`・`tests/engine/processes/test_runner.py`・`tests/engine/test_add_at_guard.py`・`tests/engine/test_ledger_wiring.py`・`tests/engine/test_processes_run.py`・`tests/engine/test_resume_10d.py`・`tests/llm/test_fleet_contract.py`
- 読む試験(道筋で): `tests/engine/speech/test_speech_writers_ast.py`・`tests/engine/systems/test_stage_a_guard.py`・`tests/test_places_guard.py`
- 状態台帳の行
  - 持ち主 `ledger.money`(`Ledger`)
    - `A` 金と物の台帳の行の目印の列・transfer の計器(第 1 期 1-9)(挙動 diag・復元 discardable) 道筋 `ledger.money._raw_event_seq`・`ledger.money._raw_event_t_ns`・`ledger.money.meter` 書ける系: close_final・day_close・duties・phase_c・world
    - `ATM` ATM の表(Fixtures.atms と同じ物・第 2 期 2-1)(挙動 behavior・復元 derivable) 道筋 `ledger.money.stage2.atms` 書ける系: (宣言なし)
    - `CR` 信用の器(CreditBook・第 2 期 2-1・器だけ=行は 0)(挙動 diag・復元 derivable) 道筋 `ledger.money.credit` 書ける系: (宣言なし)
    - `EC` 経済の段階 2 の中身(MoneyStage2=部品・体の種別・1 日の消費・労働時間・組み立ての物・計器)(挙動 behavior・復元 derivable) 道筋 `ledger.money.stage2` 書ける系: close_final・day_close・phase_c
    - `EM` 金の生ログの支払いの方法の列(_raw_method・第 2 期 2-1)(挙動 diag・復元 discardable) 道筋 `ledger.money._raw_method` 書ける系: close_final・day_close・duties・phase_c・world
    - `O57` MoneyLedger _lines・_day(挙動 behavior・復元 required) 道筋 `ledger.money._day`・`ledger.money._lines` 書ける系: close_final・day_close・duties・phase_c・world
    - `O58` MoneyLedger 生ログのリング(中身)(挙動 no・復元 discardable) 道筋 `ledger.money._raw_amt`・`ledger.money._raw_code`・`ledger.money._raw_pi`・`ledger.money._raw_ps`・`ledger.money._raw_qi`・`ledger.money._raw_qs`・`ledger.money._raw_tick` 書ける系: close_final・day_close・duties・phase_c・world
    - `O77` MoneyLedger _flow・_last_change_day・_snap0・_last_close(センサスと保存則の項)(挙動 diag・復元 required) 道筋 `ledger.money._flow`・`ledger.money._last_change_day`・`ledger.money._last_close`・`ledger.money._snap0` 書ける系: close_final・day_close・duties・phase_c・world
    - `O78` MoneyLedger rejections(挙動 diag・復元 discardable) 道筋 `ledger.money.rejections` 書ける系: close_final・day_close・duties・phase_c・world
    - `O92` MoneyLedger 締めの基準と生ログの位置(_snap・_flow_daily・_raw_pos・_raw_head・_day_marks・n_raw_dropped・n_transfers)(挙動 diag・復元 required) 道筋 `ledger.money._day_marks`・`ledger.money._flow_daily`・`ledger.money._raw_head`・`ledger.money._raw_pos`・`ledger.money._snap`・`ledger.money.n_raw_dropped`・`ledger.money.n_transfers` 書ける系: close_final・day_close・duties・phase_c・world
- 決定の ID: 10-13b/§3・D-53・D-85

## [ops.py](../../../../../../../src/shibuya/economy/ops.py)

economy.ops — お金の基本操作「移す」(第 1 期 1-9・CP2 の段階 1・A 湧かないもの)。

- 公開の関数とクラス
  - `TransferId`(クラス): ``transfer`` の戻り=生ログの通し番号の範囲 ``[first, first + n)``(1 行=1 つの transfer の記録)。
  - `TransferMeter`(クラス): ``transfer`` の計器(状態台帳の行 ``A``=軸 1 diag・軸 2 discardable=再開のランは 0 から数える)。
  - `account_name`(関数): 出来事の ``who``/``whom`` に書く口の名(世帯=体の id・ほかは ``"部門:索引"``・未リサーチ(expedient))。
  - `code_of_what`(関数): 金の語 → 科目(科目の名の語と ``MONEY_EXTRA_WHAT`` の語。表の外は ``None``)。
  - `transfer`(関数): **基本操作「移す」**(お金・A 湧かないもの)。``src`` から ``dst`` へ ``amount`` 円を移し、生ログに記録する。
  - `what_of`(関数): 科目 → 金の語(``"金:消費支出"``)。
- import している内部モジュール: `shibuya.economy.accounts`・`shibuya.economy.ledger`
- 呼び手: `shibuya.economy.credit`・`shibuya.economy.ledger`・`shibuya.economy.stage2`
- 読む試験: `tests/economy/cp2/money_writers.py`・`tests/economy/cp2/test_cp2_event_links.py`・`tests/economy/cp2/test_cp2_transfer_only_writer.py`・`tests/economy/stage2/test_stage2_account_and_conservation.py`・`tests/economy/stage2/test_stage2_calls.py`・`tests/economy/stage2/test_stage2_rules_credit_atm.py`
- 読む試験(道筋で): `tests/economy/cp2/test_cp2_write_window.py`・`tests/economy/test_single_write_path.py`・`tests/engine/speech/test_speech_writers_ast.py`・`tests/engine/test_two_phase.py`・`tests/test_places_guard.py`
- 決定の ID: 10-12/§4-5・10-13b/§3・R-113

## [pricing.py](../../../../../../../src/shibuya/economy/pricing.py)

economy.pricing — 行5 価格形成のエンジン側(内生フロア・クリアリング・Calvo・逸脱比例コスト)。

- 公開の関数とクラス
  - `PriceProposal`(クラス): ``propose_price`` の結果(1 店舗ぶん)。
  - `PriceSector`(クラス): Calvo 改定確率の業種(H-1)。
  - `StoreKind`(クラス): 店舗の業態(k の 3 値と 1 対 1)。
  - `apply_r`(関数): LLM の相対倍率 r を価格へ適用する(H-3)。
  - `book_deviation_cost`(関数): 逸脱比例コストを **sink として台帳に登録**する(店舗→政府・§8 H-5)。
  - `calvo_daily_probability`(関数): 月次改定確率 → 日次改定確率 ``1 − (1−p)^(1/30.44)``(expedient な薄め方)。
  - `calvo_draw`(関数): Calvo 型の改定抽選(H-1)。``per='month'`` なら月次確率・``'day'`` なら日次確率。
  - `clearing`(関数): クリアリング(最小形): 成立数量 = min(需要, 供給)。
  - `deviation_cost`(関数): 逸脱比例コスト(H-5)= β × max(0, フロア − 価格) × 数量 1 個あたり。
  - `floor_price`(関数): 内生フロア = 原価 × k(H-2)。円未満は切り上げ(フロアを割らない)。
  - `propose_price`(関数): 店主の r(LLM 出力)を受け取り、フロア・クリップ・逸脱コストまでを確定する入口。
- import している内部モジュール: `shibuya.economy.accounts`
- 呼び手: `shibuya.economy.goods`
- 読む試験: `tests/economy/cp2/head_goods_136fdbb.py`・`tests/economy/test_pricing.py`
- 読む試験(道筋で): `tests/engine/processes/test_rate_rules_1101.py`・`tests/test_places_guard.py`

## [stage2.py](../../../../../../../src/shibuya/economy/stage2.py)

economy.stage2 — 経済の段階 2(第 2 期 2-1・CP2 の段階 2・腕 ``--economy-stage2``・既定 off)。

- 公開の関数とクラス
  - `MoneyStage2`(クラス): 経済の段階 2 の中身(``Ledger.attach_stage2`` が作る=状態台帳の行 EC・計器 ``s2_meter`` は行 EM)。
  - `payroll_deductions`(関数): 給与の天引き(本人の分の合計[円]と内訳)。
  - `tax_of`(関数): 税込の額の中の消費税[円]\(``額 × 率 / (1 + 率)`` の切り捨て=レジの端数=未リサーチ(expedient)・4-2 で表に)。
- import している内部モジュール: `shibuya.economy.accounts`・`shibuya.economy.anchors`・`shibuya.economy.checks`・`shibuya.economy.ops`・`shibuya.economy.tax_deposit`・`shibuya.economy.taxes`・`shibuya.economy.wages`・`shibuya.foundation.growth`・`shibuya.foundation.ports.ledger`
- 呼び手: `shibuya.cli`・`shibuya.economy.ledger`
- 読む試験: `tests/economy/cp2/test_cp2_k17_capacity_and_overflow.py`・`tests/economy/stage2/test_stage2_calls.py`・`tests/economy/stage2/test_stage2_default_2_4.py`・`tests/economy/stage2/test_stage2_money_rules.py`・`tests/economy/stage2/test_stage2_rules_credit_atm.py`・`tests/economy/stage2/test_stage2_runs.py`・`tests/economy/test_min_wage_human_bridge.py`・`tests/economy/test_rules42_ledger.py`・`tests/economy/test_rules42b_ledger.py`・`tests/economy/test_wage_occupation.py`
- 読む試験(道筋で): `tests/economy/stage2/test_stage2_writers.py`・`tests/test_places_guard.py`
- 決定の ID: 10-12・10-12/§4-11・10-13b/§0-3・10-13b/§7・11-01/§5・R-107・第 346

## [tax_deposit.py](../../../../../../../src/shibuya/economy/tax_deposit.py)

economy.tax_deposit — 店の預かり消費税(第 4 期 4-2・Q1=PENDING 仮-40・R-118 §5 ①)。

- 公開の関数とクラス
  - `TaxDeposit`(クラス): 店ごとの預かり消費税(課税期間の年ごと)。書くのは :meth:`collect` と :meth:`remit_due` だけ。
- import している内部モジュール: `shibuya.economy.accounts`・`shibuya.economy.taxes`・`shibuya.foundation.ports.ledger`
- 呼び手: `shibuya.economy.stage2`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 状態台帳の行
  - 持ち主 `ledger.money.stage2.tax_deposit`(`TaxDeposit`)
    - `TXD` TaxDeposit(店の預かり消費税=課税期間の年 → 店ごとの預かり額・累計・第 4 期 4-2)(挙動 behavior・復元 required・腕 rules-42) 道筋 `ledger.money.stage2.tax_deposit.held`・`ledger.money.stage2.tax_deposit.totals` 書ける系: close_final・day_close・phase_c
- 決定の ID: R-106・R-118・第 346

## [taxes.py](../../../../../../../src/shibuya/economy/taxes.py)

economy.taxes — 第 4 期 4-2 の規則の表の machine の行の読み手(税・社会保険・消費税の端数と期限・信用の上限・割増)。

- 公開の関数とクラス
  - `Deductions`(クラス): 1 回の給料日の天引き(行ごとの円)。``employee``/``employer`` は項目 → 配列。
  - `Enrollment`(クラス): 体(行)ごとの加入(社会保険=健保・介護・支援金・厚年/雇用保険/源泉と住民税)と判定の材料の有無。
  - `PayrollTables`(クラス): 給料日 ``asof`` に効いている天引きの表(行が無い項目は ``None``=その項目は 0)。
  - `deductions`(関数): 給料日の天引き(本人の分 6 項目と雇用主の分 4 項目・〔4-2b〕5 項目=子ども・子育て拠出金)。
  - `enrollment`(関数): 加入の判定(R-118 §2-3・§2-6・規則の表の行の値): 週の時間の目安が通常の労働者の 4 分の 3 以上=社会保険/
  - `filing_deadline`(関数): 課税期間 ``period_year``(暦年)の消費税の申告と納付の期限と出どころ(課税期間の末日に効いている版)。
  - `income_tax_withholding`(関数): 源泉所得税(月額表の甲欄の電算機計算の特例=平成 24 年財務省告示第 116 号・令和 8 年分)。
  - `interest_cap`(関数): 利息制限法 1 条の上限(``bands``=元本の帯 (下限, 上限(含まない)・None=なし, 年率) の並び・``source``)。無ければ ``None``。
  - `invoice_rounding`(関数): レジの税の端数の決まり(1 枚の適格請求書につき税率ごとに 1 回・方法は任意・商品ごとは不可=問 57)。
  - `overtime_premium`(関数): 時間外の割増の率の範囲(労基法 37 条 1 項=2 割 5 分以上 5 割以下の範囲で政令の率以上・月 60 時間超は 5 割以上)。
  - `payroll_tables`(関数): ``asof`` の日に効いている天引きの 6 行(リポの表なら日ごとに 1 回だけ作る)。
  - `reduced_rate`(関数): 軽減税率(国 6.24%+地方 22/78=8%)の率と出どころ(器=呼び手なし。品目の段と店内か持ち帰りかの申告の後に使う)。
  - `resident_non_taxable`(関数): 〔4-2b〕住民税の非課税(扶養 0・23 区): 合計所得が限度以下、または未成年者(今の年齢が ``minor_age_below`` 未満・
  - `resident_tax_monthly`(関数): 住民税の特別徴収の月の額=(所得割+均等割 1,000+3,000+森林環境税 1,000)÷ 12 の 1 円未満の切り捨て。
  - `share_50sen`(関数): 額 ``num / den`` 円を「50 銭以下は切り捨て・50 銭を超えれば切り上げ」で円に(R-118 §2-6・額表の注)。
  - `standard_monthly`(関数): 報酬月額 → 標準報酬月額(等級表の下限で引く・健保法 40 条・厚年法 20 条)。
  - `total_volume_cap`(関数): 総量規制(貸金業法 13 条の 2 第 2 項・13 条 3 項)の値: 年収の割合・収入の書類が要る額(1 社・全体)。無ければ ``None``。
- import している内部モジュール: `shibuya.economy.anchors`・`shibuya.engine.rules.table`
- 呼び手: `shibuya.economy.credit`・`shibuya.economy.stage2`・`shibuya.economy.tax_deposit`
- 読む試験: `tests/economy/test_min_wage_human_bridge.py`・`tests/economy/test_rules42_ledger.py`・`tests/economy/test_rules42_payroll.py`・`tests/economy/test_rules42b_ledger.py`・`tests/economy/test_rules42b_payroll.py`・`tests/engine/rules/test_rules42_table.py`
- 読む試験(道筋で): `tests/engine/rules/test_rules_table_schema.py`・`tests/test_places_guard.py`
- 決定の ID: 10-12/§4-11・R-118・第 346

## [wages.py](../../../../../../../src/shibuya/economy/wages.py)

economy.wages — 職業 × 性 × 年齢 × 雇用形態の賃金(賃金構造基本統計調査 令和 7 年=R-107・EC2 の最初の資産)。

- 公開の関数とクラス
  - `WageTablesAbsentWarning`(クラス): 賃金の表の写しが無い写し(data の無い CI)の注記。``engine.economy_stage2.DataAbsentWarning`` と同じ UserWarning の系
  - `floor_with_shortfall`(関数): 〔11-01 §5・段 2 の 5〕床を当てる直前に「床を下回る額」を数え、床を機械が当てる行(machine かつなぎ)だけ床を当てる。
  - `load_wage_tables`(関数): 構築側の写し 4 本(:data:`DERIVED_FILES`)を md5 を照らして読む。無い写しは ``None``(md5 が違えば止める)。
  - `min_wage_floor`(関数): 〔検収 M1〕``asof`` の日に効いている最低賃金の床[円/時]と出どころ(規則の表の ``minimum_wage.tokyo``)。
  - `min_wage_terms`(関数): 〔11-01 §5〕``asof`` の日の最低賃金の行の読み(``economy.anchors.MinWageTerms``=値・出どころ・kind・つなぎ)。
- import している内部モジュール: `shibuya.core.wage_formula`・`shibuya.economy.anchors`・`shibuya.foundation.paths`
- 呼び手: `shibuya.economy.stage2`
- 読む試験: `tests/economy/stage2/test_wage_occupation_runs.py`・`tests/economy/test_min_wage_human_bridge.py`・`tests/economy/test_wage_occupation.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 決定の ID: 10-12/§4-11・10-13b/§7・11-01/§5・R-107
