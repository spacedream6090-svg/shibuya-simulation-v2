# src/shibuya/act/ops

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 12 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/act/ops/__init__.py)

(冒頭の説明なし)

## [body_writes.py](../../../../../../../../src/shibuya/act/ops/body_writes.py)

act.ops.body_writes — 割る段で ``engine/resolve.py`` を割った割り先(全ファイルの表 §4・名の表は``tools/pkgmove/map.toml`` の割る行)。

- 公開の関数とクラス
  - `advance_body`(関数): 内受容 3 変数の自然変動(**C4 の世界過程が入るまでの駆動源**・expedient)。
  - `energy_home_meal`(関数): **第2波 §2B 項 2(Q35 (a))** 範囲内の自宅の食事行=予定の実行(``engine.energy.HomeMeals.due``)。
  - `energy_out_of_area_meal`(関数): 範囲外の食事(K9 (a)): 域外に居る体の予定の食事=時間帯の比 × EER・``since_meal=0``。
  - `initialize_energy`(関数): 体の定数(体重・EER)を抽選し、食後の消費・収支・``hunger`` の写しと段を置く(ラン開始時 1 回)。
- import している内部モジュール: `shibuya.foundation.time_consts`・`shibuya.foundation.vocab.agent_codes`・`shibuya.world.body.energy`・`shibuya.world.body.rules`・`shibuya.world.model.agent_table`
- 呼び手: `shibuya.act.ops.shop`・`shibuya.runtime.systems.assemble`・`shibuya.runtime.systems.body`
- 読む試験: `tests/engine/discard_probe.py`・`tests/engine/test_energy_balance.py`・`tests/engine/test_meal_bundle_2b.py`・`tests/engine/test_meal_gate_per_hour.py`・`tests/engine/test_resolve.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_state_checks_10f.py`・`tests/engine/test_state_ledger_10b.py`・`tests/engine/test_two_layer_activity.py`
- 書きの許可
  - `_energy_meal`: 直接の書き `agents.energy_balance`・`agents.hunger`・`agents.since_meal_kcal`
  - `_energy_snack`: 直接の書き `agents.energy_balance`・`agents.hunger`・`agents.since_meal_kcal`
  - `advance_body`: 直接の書き `agents.energy_balance`・`agents.fatigue`・`agents.hunger`・`agents.since_meal_kcal` 口として持つ系: body
  - `energy_home_meal`: 直接の書き `agents.hunger_stage` 口として持つ系: home_meal
  - `energy_out_of_area_meal`: 直接の書き (なし) 口として持つ系: body
  - `initialize_energy`: 直接の書き `agents.eer_kcal`・`agents.energy_balance`・`agents.hunger`・`agents.hunger_stage`・`agents.since_meal_kcal`・`agents.weight_kg` 口として持つ系: build
- 決定の ID: D-118・第 275

## [detect_writes.py](../../../../../../../../src/shibuya/act/ops/detect_writes.py)

act.ops.detect_writes — 割る段で ``engine/resolve.py`` を割った割り先(全ファイルの表 §4・名の表は``tools/pkgmove/map.toml`` の割る行)。

- 公開の関数とクラス
  - `write_b4_hash`(関数): ``change_detect`` が返した新しい B4 ハッシュを書き込む(世界の欄 ``cells.b4_hash``)。
- import している内部モジュール: `shibuya.mind.system1.change_detect`・`shibuya.world.model.state`
- 呼び手: `shibuya.runtime.systems.perceive`
- 読む試験: `tests/engine/clock/test_tm3_step_scope.py`・`tests/engine/test_detection_writes_split.py`・`tests/engine/test_resolve.py`
- 読む試験(道筋で): `tests/tools/test_pkgmove.py`
- 書きの許可
  - `write_b4_hash`: 直接の書き `cells.b4_hash` 口として持つ系: detect

## [focus.py](../../../../../../../../src/shibuya/act/ops/focus.py)

act.ops.focus — 割る段で ``engine/resolve.py`` を割った割り先(全ファイルの表 §4・名の表は``tools/pkgmove/map.toml`` の割る行)。

- import している内部モジュール: `shibuya.foundation.vocab.agent_codes`
- 呼び手: `shibuya.act.apply`・`shibuya.act.ops.move`・`shibuya.act.ops.shop`
- 読む試験: `tests/engine/test_c9b_targets_attention.py`
- 書きの許可
  - `_advance_focus`: 直接の書き `agents.focus_target`・`agents.focus_ttl`
  - `_clear_focus`: 直接の書き `agents.focus_target`・`agents.focus_ttl`
  - `_set_focus`: 直接の書き `agents.focus_target`・`agents.focus_ttl`

## [init_writes.py](../../../../../../../../src/shibuya/act/ops/init_writes.py)

act.ops.init_writes — 割る段で ``engine/resolve.py`` を割った割り先(全ファイルの表 §4・名の表は``tools/pkgmove/map.toml`` の割る行)。

- 公開の関数とクラス
  - `initialize`(関数): 個体を自宅セルに置き、所持金・種別・内受容の初期段を設定する(**ランの最初に1回**)。
  - `set_initial_activity`(関数): tick 0 の ``activity`` を**計画(W17)の 0:00 時点の活動**から立てる(D-62 (b))。
- import している内部モジュール: `shibuya.foundation.ports.ledger`・`shibuya.foundation.vocab.agent_codes`・`shibuya.world.body.rules`・`shibuya.world.model.agent_table`・`shibuya.world.model.state`
- 呼び手: `shibuya.runtime.systems.assemble`・`tools/c6/ablation1_fixed_vs_ranking.py`
- 読む試験: `tests/engine/processes/conftest.py`・`tests/engine/rights/test_staff_of_poi_equivalence.py`・`tests/engine/test_ablation23_switches.py`・`tests/engine/test_conversation_invite.py`・`tests/engine/test_intent_hold.py`・`tests/engine/test_ledger_wiring.py`・`tests/engine/test_plan_sleep_d62.py`・`tests/engine/test_resolve.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/test_vocab_v2_eat.py`
- 書きの許可
  - `initialize`: 直接の書き `agents.activity`・`agents.age`・`agents.band`・`agents.cell`・`agents.fatigue`・`agents.hunger`・`agents.kind`・`agents.money`・`agents.node`・`agents.sex`・`agents.thermal`・`agents.xy`・`cells.density`・`cells.density_stage`・`cells.open_count` 口として持つ系: build
  - `set_initial_activity`: 直接の書き `agents.activity` 口として持つ系: build
- 決定の ID: D-62・D-66

## [intent_writes.py](../../../../../../../../src/shibuya/act/ops/intent_writes.py)

act.ops.intent_writes — 割る段で ``engine/resolve.py`` を割った割り先(全ファイルの表 §4・名の表は``tools/pkgmove/map.toml`` の割る行)。

- 公開の関数とクラス
  - `clear_intent`(関数): 意図を消す(計画境界・割り込み・経路の行き止まり=段 2c)。結果コードは書かない。
  - `fail_intent`(関数): 意図を**失敗で終える**(段 2c の満了=``TOO_FAR``)。
  - `intent_kept_by`(関数): 意図を持つ体に適用する行為が意図を**保つ**か(段 2c・親決定 Q20・**読むだけ**)。
  - `relabel_intent_failure`(関数): 既に書かれた失敗(移動の ``UNREACHABLE``)の**主語を意図の行為に**して意図を消す(段 2c)。
  - `set_activity`(関数): **活動の持続と種別**を書く(二層の段 2・``engine.activity`` が値を決める・書き手は本関数)。
  - `set_activity_until`(関数): ``activity_until`` だけを書き換える(到着・会話成立の満了=二層の段 2)。
  - `set_intent`(関数): **意図を立てる**(段 2c・値は ``engine.intent`` が決める)。
- import している内部モジュール: `shibuya.foundation.vocab.act_codes`・`shibuya.foundation.vocab.agent_codes`・`shibuya.foundation.write_guard`・`shibuya.world.model.agent_table`・`shibuya.world.model.state`
- 呼び手: `shibuya.act.activity`・`shibuya.act.apply`・`shibuya.act.intent`
- 読む試験: `tests/engine/test_intent_hold.py`
- 書きの許可
  - `_clear_intent_fields`: 直接の書き `agents.intent_action`・`agents.intent_kind`・`agents.intent_since`・`agents.intent_target`
  - `clear_intent`: 直接の書き (なし) 口として持つ系: activity_intent
  - `fail_intent`: 直接の書き `agents.activity`・`agents.last_action`・`agents.last_result`・`agents.last_result_tick`・`agents.target_node` 口として持つ系: activity_intent
  - `intent_kept_by`: 直接の書き (なし) 口として持つ系: phase_a
  - `relabel_intent_failure`: 直接の書き `agents.last_action` 口として持つ系: activity_intent
  - `set_activity`: 直接の書き `agents.activity_kind`・`agents.activity_until` 口として持つ系: activity_intent・presence
  - `set_activity_until`: 直接の書き `agents.activity_until` 口として持つ系: activity_intent
  - `set_intent`: 直接の書き `agents.intent_action`・`agents.intent_kind`・`agents.intent_since`・`agents.intent_target` 口として持つ系: activity_intent

## [law_writes.py](../../../../../../../../src/shibuya/act/ops/law_writes.py)

act.ops.law_writes — 割る段で ``engine/resolve.py`` を割った割り先(全ファイルの表 §4・名の表は``tools/pkgmove/map.toml`` の割る行)。

- 公開の関数とクラス
  - `collect_waste`(関数): 廃棄物収集(店舗の廃棄ビン→bbox 外)。搬出質量[g]を返す(棚は動かない)。
  - `consume`(関数): 消費(世帯の所持 → sink)。個体側は ``holdings``(個数)、SKU 別は台帳側の合計。
  - `discard_to_bin`(関数): 売れ残りを廃棄ビンへ(棚→ビン)。**棚が減るので写しの書き戻しが要る**。
  - `request_open_close`(関数): 役割行動「開閉店」(行動契約書 §2.2)。権利=当該 POI の担当従業者(権利台帳の ``employ`` の行)。
  - `restock`(関数): 店舗補充・納品(外界→棚)。代金は域外仕入(店舗→外界)で払う。
  - `set_notice_state`(関数): 知覚側 SoA(M12: 向き量子化+課題従事フラグ)を書く(**書き込み口は resolve 一本**)。
  - `set_open_flags`(関数): POI の営業フラグ上書き欄を書く(-1=上書きなし / 0=閉 / 1=開)。
  - `set_thermal`(関数): 体感温度(内受容3変数の1本)を一括代入する(知覚契約書 §3 内受容・日陰係数0.86)。
- import している内部モジュール: `shibuya.foundation.ports.ledger`・`shibuya.foundation.vocab.agent_codes`・`shibuya.foundation.write_guard`・`shibuya.world.model.agent_table`・`shibuya.world.model.state`
- 呼び手: `shibuya.interim_bundles.duties.layer`・`shibuya.world.laws.environment`・`shibuya.world.laws.goods_flow`・`shibuya.world.laws.opening`・`shibuya.world.laws.salient`
- 読む試験: `tests/engine/duties/test_du_runs.py`・`tests/engine/processes/test_absent_processes_1102.py`・`tests/engine/processes/test_goods_flow.py`・`tests/engine/processes/test_opening.py`・`tests/engine/rights/test_no_permission_count.py`・`tests/engine/rights/test_rights_events.py`・`tests/engine/test_ledger_wiring.py`
- 書きの許可
  - `collect_waste`: 直接の書き (なし) 口として持つ系: world
  - `consume`: 直接の書き `agents.holdings` 口として持つ系: world
  - `discard_to_bin`: 直接の書き `pois.stock` 口として持つ系: duties・world
  - `request_open_close`: 直接の書き `agents.last_result`・`agents.last_result_tick`・`pois.open_now` 口として持つ系: duties・world
  - `restock`: 直接の書き `pois.stock` 口として持つ系: duties・world
  - `set_notice_state`: 直接の書き `perception.heading`・`perception.task_flag` 口として持つ系: world
  - `set_open_flags`: 直接の書き `pois.open_now` 口として持つ系: world
  - `set_thermal`: 直接の書き `agents.thermal` 口として持つ系: world
- 決定の ID: 10-12/§1-4

## [move.py](../../../../../../../../src/shibuya/act/ops/move.py)

act.ops.move — 割る段で ``engine/resolve.py`` を割った割り先(全ファイルの表 §4・名の表は``tools/pkgmove/map.toml`` の割る行)。

- 公開の関数とクラス
  - `nav_place`(関数): ランの頭(nav1): 体を節の点へ置き、セルと層を面から導く(初期化と域外の配置の後に 1 回・再開では呼ばない)。
- import している内部モジュール: `shibuya.act.gate`・`shibuya.act.ops.focus`・`shibuya.act.ops.rail`・`shibuya.foundation.vocab.act_codes`・`shibuya.foundation.vocab.agent_codes`・`shibuya.world.model.agent_table`・`shibuya.world.model.state`
- 呼び手: `shibuya.act.apply`・`shibuya.runtime.systems.assemble`
- 読む試験: `tests/engine/test_move_destination.py`・`tests/engine/test_two_layer_activity.py`
- 書きの許可
  - `_apply_engine_step`: 直接の書き `agents.activity`・`agents.board_line`・`agents.board_since`・`agents.edge_id`・`agents.edge_s`・`agents.node`・`agents.path_next_node`・`agents.sleep_pending`・`agents.target_node`
  - `_apply_move`: 直接の書き `agents.activity`・`agents.poi_ref`・`agents.poi_since`・`agents.queue_poi`・`agents.queue_since`・`agents.target_node`
  - `_nav_positions`: 直接の書き `agents.band`・`agents.cell`・`agents.nav_fi`・`agents.nav_node`・`agents.nav_t`・`agents.nav_tgt`・`agents.nav_wait`・`agents.xy`
  - `_nav_step`: 直接の書き `agents.nav_fi`・`agents.nav_node`・`agents.nav_of`・`agents.nav_ox`・`agents.nav_oy`・`agents.nav_t`・`agents.nav_tgt`・`agents.nav_wait`・`agents.node`・`agents.xy`
  - `_nav_stop`: 直接の書き `agents.nav_node`・`agents.nav_t`・`agents.nav_tgt`・`agents.nav_wait`・`agents.node`・`agents.xy`
  - `_settle_approach`: 直接の書き `agents.focus_target`・`agents.focus_ttl`
  - `nav_place`: 直接の書き `cells.density`・`cells.density_stage`
- 決定の ID: 11-03・D-51・D-62

## [plan_writes.py](../../../../../../../../src/shibuya/act/ops/plan_writes.py)

act.ops.plan_writes — 割る段で ``engine/resolve.py`` を割った割り先(全ファイルの表 §4・名の表は``tools/pkgmove/map.toml`` の割る行)。

- 公開の関数とクラス
  - `begin_exit_walk`(関数): **9a 退出を歩かせる**(D-115 ①): 計画の退出の体に**その体の路線のホーム**への乗車の意図を立てる。
  - `begin_planned_sleep`(関数): **就寝境界に達した体を寝かせる**(D-62 (a)「就寝は計画の実行」・2026-09-10 決定)。
  - `begin_walk_to`(関数): 〔第 6 期 6-2 カレンダー 1b〕本人が決めた行き先のセルへ歩き出す(体の基本動作「歩く」=決定 10-12 §1-4 D1)。
  - `clear_board_intent`(関数): 乗車の意図(``board_line``/``board_since``)を落とす(9a: 計画の退出を即時に切り替えた体)。
  - `set_plan_state`(関数): ``plan_flags``(D-66 計画実行層の欄)への**唯一の書き込み口**(〔第330・RET〕K15 で ``plan_activity`` を消した)。
  - `wake_from_plan`(関数): **非就寝の計画境界に達した体を起こす**(D-62 (a) の対称形)。
- import している内部モジュール: `shibuya.act.ops.rail`・`shibuya.foundation.vocab.agent_codes`・`shibuya.world.model.agent_table`・`shibuya.world.model.state`
- 呼び手: `shibuya.interim_bundles.calendar2.layer`・`shibuya.interim_bundles.calendar_self`・`shibuya.runtime.systems.body`・`shibuya.world.laws.presence`
- 読む試験: `tests/engine/test_plan_sleep_d62.py`
- 書きの許可
  - `begin_exit_walk`: 直接の書き `agents.activity`・`agents.board_line`・`agents.board_since`・`agents.target_node` 口として持つ系: plan_boundary・presence
  - `begin_planned_sleep`: 直接の書き `agents.activity`・`agents.board_line`・`agents.board_since`・`agents.sleep_pending`・`agents.target_node` 口として持つ系: plan_boundary・presence
  - `begin_walk_to`: 直接の書き `agents.activity`・`agents.board_line`・`agents.board_since`・`agents.sleep_pending`・`agents.target_node` 口として持つ系: calendar_2・presence
  - `clear_board_intent`: 直接の書き `agents.board_line`・`agents.board_since` 口として持つ系: presence
  - `set_plan_state`: 直接の書き `agents.plan_flags` 口として持つ系: build・close_final・day_close・day_head・plan_boundary・presence・world
  - `wake_from_plan`: 直接の書き `agents.activity`・`agents.sleep_pending` 口として持つ系: plan_boundary・presence
- 決定の ID: 10-12/§1-4・D-51・D-56・D-62・D-66・D-115・第 330

## [rail.py](../../../../../../../../src/shibuya/act/ops/rail.py)

act.ops.rail — 割る段で ``engine/resolve.py`` を割った割り先(全ファイルの表 §4・名の表は``tools/pkgmove/map.toml`` の割る行)。

- 公開の関数とクラス
  - `place_at_external`(関数): 域外ノードに個体を置く(U10 §1.1「域外は方面別の外界ノード」・ランの最初)。
  - `rail_arrive`(関数): 列車の到着で域外ノードの個体をホームのセルへ降ろす(域外→bbox)。
  - `rail_depart`(関数): 列車の発車で乗客を域外ノードへ運び出す(bbox→域外)。
  - `sync_transit_activity`(関数): ``transit_state`` を正として ``activity`` を整える(乗車中=``RIDING``)。
- import している内部モジュール: `shibuya.act.gate`・`shibuya.foundation.vocab.act_codes`・`shibuya.foundation.vocab.agent_codes`・`shibuya.world.model.agent_table`・`shibuya.world.model.state`
- 呼び手: `shibuya.act.apply`・`shibuya.act.ops.move`・`shibuya.act.ops.plan_writes`・`shibuya.interim_bundles.calendar_self`・`shibuya.world.laws.civic`・`shibuya.world.laws.presence`・`shibuya.world.laws.rail`・`shibuya.world.laws.runner`
- 読む試験: `tests/engine/calendar/test_ca1b_runs.py`・`tests/engine/processes/test_civic.py`・`tests/engine/processes/test_crowd.py`・`tests/engine/processes/test_opening.py`・`tests/engine/processes/test_rail.py`・`tests/engine/processes/test_rail_board_intent.py`・`tests/engine/processes/test_rail_return.py`・`tests/engine/processes/test_rate_rules_1101.py`・`tests/engine/rights/test_rights_events.py`・`tests/engine/rights/test_staff_of_poi_equivalence.py`・`tests/engine/test_defect_fixes_1103.py`・`tests/engine/test_intent_hold.py`・`tests/engine/test_presence_executor.py`・`tests/engine/test_presence_exit_walk.py`
- 書きの許可
  - `_apply_alight`: 直接の書き `agents.activity`・`agents.node`・`agents.target_node`・`agents.transit_ref`・`agents.transit_state`
  - `_apply_board`: 直接の書き `agents.activity`・`agents.board_line`・`agents.board_since`・`agents.queue_poi`・`agents.queue_since`・`agents.target_node`
  - `_board_riders`: 直接の書き `agents.activity`・`agents.board_line`・`agents.board_since`・`agents.money`・`agents.node`・`agents.poi_ref`・`agents.queue_poi`・`agents.target_node`・`agents.transit_ref`・`agents.transit_state`
  - `_enter_board_queue`: 直接の書き `agents.activity`・`agents.board_line`・`agents.board_since`・`agents.target_node`
  - `_serve_board_queue`: 直接の書き `agents.activity`・`agents.board_line`・`agents.board_since`
  - `place_at_external`: 直接の書き `agents.activity`・`agents.board_line`・`agents.board_since`・`agents.cell`・`agents.node`・`agents.target_node`・`agents.transit_ref`・`agents.transit_state` 口として持つ系: build
  - `rail_arrive`: 直接の書き `agents.activity`・`agents.band`・`agents.cell`・`agents.node`・`agents.target_node`・`agents.transit_ref`・`agents.transit_state`・`agents.xy` 口として持つ系: build・close_final・day_close・plan_boundary・presence・world
  - `rail_depart`: 直接の書き `agents.activity`・`agents.cell`・`agents.node`・`agents.target_node`・`agents.transit_ref`・`agents.transit_state` 口として持つ系: close_final・day_close・plan_boundary・presence・world
  - `sync_transit_activity`: 直接の書き `agents.activity` 口として持つ系: close_final・day_close・world
- 決定の ID: 11-03・D-51・第 302

## [shop.py](../../../../../../../../src/shibuya/act/ops/shop.py)

act.ops.shop — 割る段で ``engine/resolve.py`` を割った割り先(全ファイルの表 §4・名の表は``tools/pkgmove/map.toml`` の割る行)。

- 公開の関数とクラス
  - `balk_queue`(関数): 待ち行列からの離脱(離脱閾値・``INTERRUPTED``=「途中打ち切り(混雑・閉鎖)」)。
  - `release_indoor`(関数): 在席の解除(回転率=滞在上限・16行表 行2 の expedient)。
- import している内部モジュール: `shibuya.act.commit`・`shibuya.act.gate`・`shibuya.act.ops.body_writes`・`shibuya.act.ops.focus`・`shibuya.economy.stage2_bind`・`shibuya.foundation.vocab.act_codes`・`shibuya.foundation.vocab.agent_codes`・`shibuya.foundation.write_guard`・`shibuya.world.model.agent_table`
- 呼び手: `shibuya.act.apply`・`shibuya.act.ops.talk`・`shibuya.interim_bundles.calendar_self`・`shibuya.world.laws.crowd`・`shibuya.world.laws.presence`
- 読む試験: `tests/engine/body/test_body_same_values.py`・`tests/engine/processes/test_crowd.py`・`tests/engine/test_defect_fixes_1103.py`・`tests/engine/test_familiarity.py`・`tests/engine/test_intent_chooser.py`・`tests/engine/test_intent_hold.py`・`tests/engine/test_presence_exit_walk.py`・`tests/engine/test_stage3_small_fixes.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/test_vocab_v2_eat.py`
- 読む試験(道筋で): `tests/tools/test_pkgmove.py`
- 書きの許可
  - `_apply_buy`: 直接の書き `agents.activity`・`agents.queue_poi`・`agents.queue_since`
  - `_apply_eat`: 直接の書き `agents.activity`・`agents.queue_poi`・`agents.queue_since`
  - `_apply_wait`: 直接の書き `agents.activity`
  - `_complete_buy`: 直接の書き `agents.activity`・`agents.holdings`・`agents.hunger`・`agents.money`・`agents.poi_ref`・`agents.poi_since`・`agents.queue_poi`・`pois.revenue`・`pois.stock`
  - `_complete_eat`: 直接の書き `agents.activity`・`agents.hunger`・`agents.money`・`agents.poi_ref`・`agents.poi_since`・`agents.queue_poi`・`pois.revenue`
  - `_serve_poi_queue`: 直接の書き `agents.activity`・`agents.queue_poi`・`agents.queue_since`
  - `_stage2_withdraw`: 直接の書き `agents.money`
  - `balk_queue`: 直接の書き `agents.activity`・`agents.last_result`・`agents.last_result_tick`・`agents.queue_poi`・`agents.queue_since` 口として持つ系: plan_boundary・presence・world
  - `release_indoor`: 直接の書き `agents.activity`・`agents.poi_ref`・`agents.poi_since` 口として持つ系: plan_boundary・presence・world
- 決定の ID: 11-03・11-09・D-71・D-113・第 267・第 268・第 275・第 288・第 288 #54

## [talk.py](../../../../../../../../src/shibuya/act/ops/talk.py)

act.ops.talk — 割る段で ``engine/resolve.py`` を割った割り先(全ファイルの表 §4・名の表は``tools/pkgmove/map.toml`` の割る行)。

- 公開の関数とクラス
  - `end_conversation`(関数): 〔11-03 M10〕終わったセッションの参加者を解放する(行動契約書 §3「終了はエンジン」)。
  - `join_conversation`(関数): **3 人目の参加**(C10 8a・D-93 (d)・``--conv-max-participants 3`` のランだけ)。
  - `revert_conversation`(関数): 招待が不応答/ゲート却下だったとき、resolve が CONVERSING にした招待側を IDLE へ戻す。
  - `set_conversing`(関数): 会話成立時に**両側**を CONVERSING にする(C6・09-09)。
  - `talk_within_reach`(関数): 会話が届くか(**C9b G7**)。``by_distance=False`` は現行の「同一セル代理」。
- import している内部モジュール: `shibuya.act.gate`・`shibuya.act.ops.shop`・`shibuya.foundation.vocab.act_codes`・`shibuya.foundation.vocab.agent_codes`・`shibuya.foundation.write_guard`・`shibuya.world.model.agent_table`
- 呼び手: `shibuya.act.apply`・`shibuya.runtime.run`・`shibuya.runtime.systems.judge`・`shibuya.runtime.systems.talk`
- 読む試験: `tests/engine/processes/test_rail_board_intent.py`・`tests/engine/proximity/test_rule.py`・`tests/engine/proximity/test_runs.py`・`tests/engine/test_c9b_targets_attention.py`・`tests/engine/test_conversation_invite.py`・`tests/engine/test_defect_fixes_1103.py`・`tests/engine/test_presence_exit_walk.py`
- 書きの許可
  - `_apply_leave`: 直接の書き `agents.activity`・`agents.talk_partner`
  - `_apply_talk`: 直接の書き `agents.activity`・`agents.talk_partner`
  - `end_conversation`: 直接の書き `agents.activity`・`agents.talk_partner` 口として持つ系: apply_responses・conversation
  - `join_conversation`: 直接の書き `agents.activity`・`agents.last_result`・`agents.last_result_tick`・`agents.talk_partner` 口として持つ系: conversation
  - `revert_conversation`: 直接の書き `agents.activity`・`agents.talk_partner`
  - `set_conversing`: 直接の書き `agents.activity`・`agents.talk_partner` 口として持つ系: apply_responses・conversation
  - `talk_within_reach`: 直接の書き (なし) 口として持つ系: apply_responses・conversation・decide
- 決定の ID: 11-03・D-93・D-112・第 263
