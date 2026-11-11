# tests/economy/cp2

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 12 本・その他 1 本(このディレクトリの直下)

その他のファイル: `money_writers_frozen.json`

## [__init__.py](../../../../../../../tests/economy/cp2/__init__.py)

(冒頭の説明なし)

## [head_copies.py](../../../../../../../tests/economy/cp2/head_copies.py)

第 1 期 1-9: 載せ替えの前(HEAD ``136fdbb``)の ``economy/ledger.py`` と ``economy/goods.py`` の写しを読む道具(試験の補助)。

- 公開の関数とクラス
  - `diff`(関数): 2 つの状態の食い違う鍵(配列は形・型・中身)。
  - `goods_state`(関数): 物の台帳の状態(在庫の配列・納品ログの中身と位置・計数・締め)。
  - `head_goods_module`(関数)
  - `head_ledger_module`(関数)
  - `money_state`(関数): 金の台帳の状態(残高・流れ・締め・生ログの中身と位置・計数)。HEAD と今で同じ鍵。
  - `pin_problems`(関数): 写し ``name`` と読み込んだ ``mod`` が固定と違う所(字面・文の順・意味)。
  - `shims`(関数): (HEAD の Ledger の子・HEAD の GoodsLedger の子・HEAD の財布の差し替えの子)。``cause`` を捨てるだけ。
- import している内部モジュール: `tests/_head_copy_pin.py`
- 読む試験: `tests/economy/cp2/test_cp2_nine_ops_equivalence.py`

## [head_goods_136fdbb.py](../../../../../../../tests/economy/cp2/head_goods_136fdbb.py)

economy.goods — 物の保存則(U-Goods)。``move_goods`` **単一API**と SKU 別収支。

- 公開の関数とクラス
  - `GoodsCode`(クラス): 物の科目(§7.1 の faucet/sink 列挙 + 内部移動 + 残差)。
  - `GoodsLedger`(クラス): SKU 別の棚在庫・廃棄ビン・世帯合計・外界(bbox 外)を持つ物の台帳。
  - `GoodsRef`(クラス): 物の参照 = (置き場, 索引)。索引の意味: 店舗=poi_id・世帯/外界/収集=0。
  - `NodeKind`(クラス): 物の置き場(``move_goods`` の from / to)。
  - `SkuRegistry`(クラス): SKU 登録簿(全世界で 1 つ)。
  - `WasteBand`(クラス): 廃棄 sink の band 判定(検算②・台帳行 W1)。
  - `delivery_capacity_for`(関数): 納品ログのリングバッファ容量[行]を **N から**決める(D-53・2026-09-10)。
  - `goods_flow_kind`(関数): faucet / sink / internal の判定(§7.1 の列挙をそのまま規則化)。
  - `goods_is_allowed`(関数): (科目, 置き場, 置き場)が物の faucet/sink 表にあるか。
  - `growth_declarations`(関数): 物の台帳の状態成長宣言(D-R2-6 の 5 欄)。
- import している内部モジュール: `shibuya.economy.accounts`・`shibuya.economy.anchors`・`shibuya.economy.pricing`・`shibuya.foundation.growth`
- 決定の ID: D-52・D-53・第 304・第 305

## [head_ledger_136fdbb.py](../../../../../../../tests/economy/cp2/head_ledger_136fdbb.py)

economy.ledger — 金の台帳(U11)。``transfer`` **単一API**と取引フロー行列。

- 公開の関数とクラス
  - `DayClose`(クラス): ``on_day_end`` の戻り(その日の畳み込み結果)。
  - `EmployerTable`(クラス): 雇用主(組織)の最小表 = 世界データ W6 の ``w6_org.parquet`` から読む。
  - `Ledger`(クラス): 6部門の貸借対照表 SoA + 取引フロー行列 + 生ログ。
  - `growth_declarations`(関数): 金の台帳の状態成長宣言(D-R2-6 の 5 欄)。
  - `load_employers`(関数): 雇用主の表を読む(無ければ合成)。
  - `raw_capacity_for`(関数): 生ログのリングバッファ容量[行]を **N から**決める(D-53・2026-09-10)。
- import している内部モジュール: `shibuya.economy.accounts`・`shibuya.foundation.growth`・`shibuya.foundation.hashing`・`shibuya.foundation.ports.ledger`・`shibuya.foundation.time_consts`
- 決定の ID: D-53・D-85

## [money_writers.py](../../../../../../../tests/economy/cp2/money_writers.py)

第 1 期 1-9(CP2 の段階 1): お金の列(C 金)の書き手を AST で集める道具(試験の補助・src は読むだけ)。

- 公開の関数とクラス
  - `Write`(クラス): お金の列への書き 1 つ。
  - `is_money_attr`(関数)
  - `iter_sources`(関数)
  - `scan_source`(関数): 1 つのファイルの中身からお金の列への書きを集める。
  - `scan_tree`(関数)
  - `violations`(関数): 基本操作の外で、宣言の表(置き場, 関数)→ 列の名 に無い書き。
- import している内部モジュール: `shibuya.economy.ops`
- 読む試験: `tests/economy/cp2/test_cp2_transfer_only_writer.py`・`tests/economy/cp2/test_cp2_write_window.py`・`tests/economy/stage2/test_stage2_writers.py`

## [test_cp2_event_links.py](../../../../../../../tests/economy/cp2/test_cp2_event_links.py)

第 1 期 1-9: 金の生ログの行と出来事が 1 対 1(目印の列 ``_raw_event_t_ns``・``_raw_event_seq``)。物の台帳の行の目印。

- 公開の関数とクラス
  - `test_each_caused_row_has_exactly_one_event`(関数)
  - `test_economy_and_the_ledger_api_do_not_import_engine_events`(関数): 層の契約 forbidden「economy → llm」: economy と engine.ledger_api(economy が読む)は engine.events を読まない
  - `test_economy_constants_match_the_events_vocabulary`(関数): economy は engine.events を import しない(層の契約)=金の語・原因の種類の名を写しで持つ。写しが 1-3 と同じ。
  - `test_no_cause_or_log_off_leaves_the_column_empty`(関数)
  - `test_overwritten_slots_do_not_keep_stale_ids`(関数): 輪の使い回し: 原因つきの行を原因なしの行で上書きすると目印も空に戻る(古い id を残さない)。
  - `test_restock_goods_row_shares_the_payment_event`(関数): 補充: 物の行の目印=代金の行(店舗 → 外界・域外仕入)の出来事。払えない行は物の行も代金の行も無い。
  - `test_run_rows_and_events_are_one_to_one`(関数): ラン(世界資産 200 体・既定 v3・1 日): 金の生ログの目印のある行と出来事の記録の金の行が 1 対 1。
  - `test_step_width_sets_the_event_time`(関数)
  - `test_store_side_has_a_poi_where_and_llm_call_cause`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.economy.accounts`・`shibuya.economy.goods`・`shibuya.economy.ledger`・`shibuya.economy.ops`・`shibuya.engine.economy_stage2`・`shibuya.engine.rate_rules`・`shibuya.foundation.journal.links`・`shibuya.foundation.journal.log`・`shibuya.foundation.ports.ledger`・`shibuya.foundation.time_consts`・`shibuya.foundation.vocab.events`・`shibuya.llm`・`tests/_places.py`
- 決定の ID: 11-01

## [test_cp2_flow_sum.py](../../../../../../../tests/economy/cp2/test_cp2_flow_sum.py)

第 1 期 1-9: 1 日の締めの検算(新しい 1 本)=その日の transfer の額の和 = 流れの表 ``_flow`` の和。

- 公開の関数とクラス
  - `test_a_flow_write_outside_transfer_is_caught_at_the_close`(関数): 負の対照: transfer を通さず流れの表を書くと締めの検算が落ちる(計器だけ・締めは止めない)。
  - `test_a_resumed_ledger_sets_the_base_at_the_first_transfer`(関数): 日の途中から再開した台帳: 流れの表が戻った後の最初の transfer で起点を決める(戻した分は起点に入る)。
  - `test_runs_keep_the_check_and_match_the_raw_log`(関数)
  - `test_transfer_sum_equals_the_flow_sum_each_day`(関数)
- import している内部モジュール: `shibuya.economy.accounts`・`shibuya.economy.census`・`shibuya.economy.checks`・`shibuya.economy.goods`・`shibuya.economy.ledger`・`shibuya.engine.run`・`shibuya.foundation.ports.ledger`・`shibuya.world.state`

## [test_cp2_k17_capacity_and_overflow.py](../../../../../../../tests/economy/cp2/test_cp2_k17_capacity_and_overflow.py)

第 1 期 1-9 K17(回答 10-13b §3): 金の生ログの輪の容量を実測 4.07 行/体/日の 1.5 倍以上に広げて宣言し、溢れた件数をmanifest と計器に出す。試験は溢れ 0 件が条件・溢れたら記録して続ける(止めない)。

- 公開の関数とクラス
  - `small_and_default`(関数)
  - `test_5k_default_day_does_not_overflow`(関数): 5,000 体の既定 v3 の 1 日: 実測の行/体/日は 6.5 未満=溢れ 0 件(HEAD の 3.0 では 3,978 行が落ちていた)。
  - `test_capacity_formula`(関数)
  - `test_declarations_fit_their_caps`(関数)
  - `test_default_capacity_does_not_overflow`(関数): 既定の容量(⌈6.5 × N⌉・下限 16,384)では溢れ 0 件。manifest の economy の欄の中身と日次の記録の和。
  - `test_manifest_economy_is_empty_without_a_ledger`(関数)
  - `test_nineteen_configs_stay_under_the_coefficient`(関数): byte-check の 19 構成(世界資産・**5,000 体**・1 日)ごとに、行/体/日 < 6.5(K17 の係数)と溢れ 0 件。
  - `test_overflow_in_a_run_is_recorded_and_the_run_finishes`(関数): 小さな輪(64 行)で意図的に溢れさせる: manifest と日次の記録に溢れの数・ランは最後まで・final は同じ。
  - `test_overflow_is_counted_and_the_ledger_goes_on`(関数): 輪(8 行)を溢れさせる: 古い行を上書きして続け、溢れた行の数を数える。残高と流れの表は全部の行を含む。
  - `test_the_coefficient_is_at_least_one_and_a_half_times_the_measurement`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.economy.accounts`・`shibuya.economy.census`・`shibuya.economy.goods`・`shibuya.economy.ledger`・`shibuya.economy.stage2`・`shibuya.engine.economy_stage2`・`shibuya.engine.run`・`shibuya.foundation.growth`・`shibuya.foundation.ports.ledger`・`shibuya.world.state`
- 決定の ID: 10-13b/§3

## [test_cp2_nine_ops_equivalence.py](../../../../../../../tests/economy/cp2/test_cp2_nine_ops_equivalence.py)

第 1 期 1-9(CP2 の段階 1): 帳簿の 9 口を基本操作 ``transfer`` に載せ替えても、同じ残高・同じ台帳の行(結果不変 ◎)。

- 公開の関数とクラス
  - `test_5k_mock_day_matches_head`(関数)
  - `test_events_on_do_not_change_the_ledgers`(関数): 出来事の記録を挿して原因を渡しても、金と物の状態は HEAD と同じ(記録は状態を変えない)。
  - `test_m1_depreciation_between_two_stores_is_a_forbidden_row`(関数): 形 1(店 0 → 店 1): HEAD は現金を 100 円移した(900/1,100・取引 +1)。1-9 は FORBIDDEN_PAIR で何も動かさない。
  - `test_m1_depreciation_on_one_store_via_the_vector_port`(関数): 形 2(店 2 → 店 2・transfer_many): HEAD は現金が差し引き 0 で取引 +1・流れ +100。1-9 は FORBIDDEN_PAIR(固定資産も動かない)。
  - `test_m1_depreciation_via_the_scalar_port_and_the_one_entrance`(関数): 形 3(店 0 → 店 0・1 件の transfer): HEAD は OK(現金 ±0・取引 +1)。1-9 は FORBIDDEN_PAIR。
  - `test_overflowing_ring_is_identical_and_counted`(関数): 小さな輪で溢れさせても HEAD と同じ行が残り、溢れた行の数は計器にも出る(K17: 記録して続ける)。
  - `test_random_port_sequences_match_head`(関数)
  - `test_the_copies_are_the_head_blobs`(関数): 写しが HEAD 136fdbb のバイトのまま(``tests/_head_copy_pin.py`` の字面・文の順・意味=段 4 で移す道具が import の文の
- import している内部モジュール: `shibuya.cli`・`shibuya.economy.accounts`・`shibuya.economy.goods`・`shibuya.economy.ledger`・`shibuya.engine.economy_stage2`・`shibuya.foundation.journal.links`・`shibuya.foundation.journal.log`・`shibuya.foundation.ports.ledger`・`tests/economy/cp2/head_copies.py`

## [test_cp2_transfer_only_writer.py](../../../../../../../tests/economy/cp2/test_cp2_transfer_only_writer.py)

第 1 期 1-9(CP2 の段階 1): お金の列の書き手は基本操作 ``economy.ops.transfer`` の中だけ(AST・負の対照つき)。

- 公開の関数とクラス
  - `test_money_columns_are_written_only_inside_transfer`(関数): 基本操作の外の書きは凍結の表(組み立て・締め・評価替え・段階 2)にあるものだけ。
  - `test_negative_alias`(関数): 負の対照 1(別名): 台帳の残高の行を局所の名に取ってから書く。
  - `test_negative_attribute_chain`(関数): 負の対照 3(属性の鎖): 箱から台帳をたどって生ログと売上の写しを書く。
  - `test_negative_other_forms`(関数): out=・field("money")・fill・np.copyto・差し替え。
  - `test_negative_outside_transfer_in_ops_and_in_the_real_ledger`(関数): ops.py の transfer の外・実物の ledger.py の口に足した書きも落ちる(置き場でなく関数で見る)。
  - `test_negative_ufunc_at`(関数): 負の対照 2(np.add.at): writeable=False を無視して書ける形(numpy 2.5 実測)。
  - `test_only_the_ledger_ports_call_the_primitive`(関数): ``ops.transfer`` を呼ぶのは帳簿の口(economy/ledger.py の Ledger のメソッド)だけ。
  - `test_the_apply_cash_alias_rows_are_gone`(関数): ``_apply_cash`` の別名の 4 行は消え、帳簿の口の呼び出しから AST で引く(閉包は前と同じ)。
  - `test_the_frozen_table_has_no_stale_rows`(関数): 表の行は実際の書きと同じ(書きが消えたら表の行も消す=表は減るだけ)。
  - `test_the_household_ports_exist_and_move_household_cash`(関数): 口の名の表(engine 側)は economy の口と突き合う: 世帯を払い手か受け手にする Ledger の口と運賃の口。
  - `test_the_money_paths_are_declared_once`(関数)
  - `test_the_primitive_writes_every_money_column_of_the_ledger`(関数): 正の対照: transfer は帳簿の残高・流れの表・最後に動いた日・生ログの全部の列を書く(道具が書きを見ている)。
  - `writes`(関数)
- import している内部モジュール: `shibuya.economy.ledger`・`shibuya.economy.ops`・`shibuya.engine.processes.rail`・`shibuya.engine.systems.allow`・`tests/economy/cp2/money_writers.py`

## [test_cp2_write_window.py](../../../../../../../tests/economy/cp2/test_cp2_write_window.py)

第 1 期 1-9(独立検収 M2): 台帳の配列を書ける窓を開けるのは基本操作 ``economy.ops.transfer`` だけ。

- 公開の関数とクラス
  - `test_negative_setattr_and_named_writes`(関数): 負の対照 2: 名前の文字列でお金の列を書く形は書き手の AST が数える(凍結の表の外=落ちる)。
  - `test_negative_window_and_balance_write`(関数): 負の対照 1: 窓を開けて ``balance`` の配列に書く(新旧の名・別名・属性の鎖・getattr の文字列・_open を外から)。
  - `test_only_the_primitive_opens_the_ledger_window`(関数)
  - `test_the_old_route_wrote_balances_and_the_new_one_cannot_be_reached_from_src`(関数): 記録: 窓を開ければ(試験が意図して開ける)残高は書ける=守りは「窓を開けるのは transfer だけ」の静的な検査。
  - `test_the_public_window_is_gone`(関数)
  - `window_refs`(関数)
- import している内部モジュール: `shibuya.economy.accounts`・`shibuya.economy.ledger`・`shibuya.foundation.ports.ledger`・`tests/economy/cp2/money_writers.py`

## [test_cp2_writes_declared.py](../../../../../../../tests/economy/cp2/test_cp2_writes_declared.py)

第 1 期 1-9: 金の移動の目印の列と計器(状態台帳の行 ``A``=CP1 の A 湧かないもの)を書く系は ``writes.paths`` に ``A:ledger.*`` を宣言し、原因を渡す移動(運賃=過程 rail)を書く phase_c は ``E:events.*`` も宣言する。宣言の外の書きは落ちる(1-0 の段 B・段 C と1-3 の実行時の検査)。

- 公開の関数とクラス
  - `test_declared_writes_cover_the_money_meter_changes`(関数)
  - `test_declaring_systems`(関数)
  - `test_phase_c_without_the_events_declaration_fails_at_the_first_fare`(関数)
  - `test_undeclared_money_meter_write_shows_in_stage_b`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.economy.census`・`shibuya.economy.goods`・`shibuya.economy.ledger`・`shibuya.engine.run`・`shibuya.engine.state_ledger`・`shibuya.engine.systems.conductor`・`shibuya.engine.systems.overrides`・`shibuya.engine.systems.probe`・`shibuya.engine.systems.table`・`shibuya.foundation.ports.ledger`・`shibuya.foundation.write_permit`・`shibuya.world.state`
