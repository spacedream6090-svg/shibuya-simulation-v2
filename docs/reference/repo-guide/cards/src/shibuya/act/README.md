# src/shibuya/act

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 7 本・その他 0 本(このディレクトリの直下)

下のディレクトリ: [intake](intake/README.md)・[ops](ops/README.md)

## [__init__.py](../../../../../../../src/shibuya/act/__init__.py)

(冒頭の説明なし)

## [activity.py](../../../../../../../src/shibuya/act/activity.py)

engine.activity — 行為と活動の二層の**活動層**(二層の実装 段 2・D-116・第276)。

- 公開の関数とクラス
  - `ActivityLayer`(クラス): 活動層(``engine.run`` が ``vocab_version="v3"`` かつ ``activity=True`` のときだけ作る)。
  - `ActivityPayload`(クラス): 1 応答ぶんの活動(パーサ v3 の欄を運ぶだけ)。
  - `activity_kind_of`(関数): 行動コード(と「あたり」の印)→ ``ActivityKind``(expedient・モジュール注記)。
  - `displayable_activity`(関数): B4b に出せる活動文か(なし・空・§2.4 ⑧ の個体依存語・⑥ の省略記法を含む文は出さない)。
  - `payload_of`(関数): ``BridgeResult``/艦隊の ``Outcome`` → 活動(語彙 v3 の応答だけ・それ以外は ``None``)。
- import している内部モジュール: `shibuya.act.commit`・`shibuya.act.ops.intent_writes`・`shibuya.foundation.hashing`・`shibuya.foundation.text.normalize`・`shibuya.foundation.time_consts`・`shibuya.foundation.types`・`shibuya.foundation.vocab.act_codes`・`shibuya.foundation.vocab.actions`・`shibuya.foundation.vocab.agent_codes`
- 呼び手: `shibuya.act.intent`・`shibuya.runtime.run`・`shibuya.runtime.systems.assemble`
- 読む試験: `tests/engine/space/test_nav1_units.py`・`tests/engine/test_intent_hold.py`・`tests/engine/test_presence_exit_walk.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/time/test_t0_time_consts.py`
- 状態台帳の行
  - 持ち主 `act_layer`(`ActivityLayer`)
    - `O1` ActivityLayer text・until_kind(挙動 behavior・復元 required) 道筋 `act_layer.text`・`act_layer.until_kind` 書ける系: activity_intent・presence
    - `O2` ActivityLayer text_id・_texts・_text_ids・_digest_cache(挙動 no・復元 derivable) 道筋 `act_layer._digest_cache`・`act_layer._text_ids`・`act_layer._texts`・`act_layer.text_id` 書ける系: activity_intent・checkpoint・close_final・day_close・presence
    - `O3` ActivityLayer _bt_agent・_bt_tick・_bt_start(挙動 no・復元 derivable) 道筋 `act_layer._bt_agent`・`act_layer._bt_start`・`act_layer._bt_tick` 書ける系: activity_intent
    - `O66` ActivityLayer の計数(挙動 diag・復元 discardable) 道筋 `act_layer.kind_counts`・`act_layer.n_arrival_expired`・`act_layer.n_cell_suppressed`・`act_layer.n_expiry_candidates`・`act_layer.n_fail_immediate`・`act_layer.n_intent_moves`・`act_layer.n_leave_expired`・`act_layer.n_partner_expired`・`act_layer.n_set`・`act_layer.n_wander_bad`・`act_layer.n_wander_steps` 書ける系: activity_intent・apply_responses・detect・phase_a・phase_c・presence
- 決定の ID: D-62・D-112・D-116・第 275・第 276

## [apply.py](../../../../../../../src/shibuya/act/apply.py)

engine.resolve — **世界状態への唯一の書き込み口**(二相コミットの Phase C)。

- 公開の関数とクラス
  - `apply`(関数): Phase C: 確定した intent だけを世界へ適用する(**唯一の書き手**)。
- import している内部モジュール: `shibuya.act.commit`・`shibuya.act.gate`・`shibuya.act.ops.focus`・`shibuya.act.ops.intent_writes`・`shibuya.act.ops.move`・`shibuya.act.ops.rail`・`shibuya.act.ops.shop`・`shibuya.act.ops.talk`・`shibuya.foundation.ports.ledger`・`shibuya.foundation.vocab.act_codes`・`shibuya.foundation.vocab.actions`・`shibuya.foundation.vocab.agent_codes`・`shibuya.world.model.agent_table`・`shibuya.world.model.geometry`・`shibuya.world.model.state`
- 呼び手: `shibuya.runtime.result`・`shibuya.runtime.systems.act`・`tools/c7/attr_arms.py`・`tools/c7/occupancy_series.py`
- 読む試験: `tests/c7/test_attr_arms.py`・`tests/engine/body/test_body_same_values.py`・`tests/engine/processes/test_civic.py`・`tests/engine/processes/test_crowd.py`・`tests/engine/processes/test_rail.py`・`tests/engine/processes/test_rail_board_intent.py`・`tests/engine/processes/test_rail_return.py`・`tests/engine/test_c9b_targets_attention.py`・`tests/engine/test_defect_fixes_1103.py`・`tests/engine/test_geometry_c9.py`・`tests/engine/test_intent_chooser.py`・`tests/engine/test_intent_hold.py`・`tests/engine/test_ledger_wiring.py`・`tests/engine/test_parser_contract.py`・`tests/engine/test_plan_sleep_d62.py`・`tests/engine/test_renderer_wiring.py`・`tests/engine/test_resolve.py`・`tests/engine/test_seat_release_2_4.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/test_two_phase.py`・`tests/engine/test_vocab_v2_eat.py`
- 書きの許可
  - `_apply_rest`: 直接の書き `agents.activity`・`agents.fatigue`
  - `_apply_sleep`: 直接の書き `agents.activity`・`agents.target_node`
  - `apply`: 直接の書き `agents.band`・`agents.board_line`・`agents.board_since`・`agents.cell`・`agents.edge_id`・`agents.edge_s`・`agents.last_action`・`agents.last_result`・`agents.last_result_tick`・`agents.node`・`agents.path_next_node`・`agents.sleep_pending`・`agents.xy`・`cells.density`・`cells.density_stage`・`cells.open_count` 口として持つ系: phase_c
- 決定の ID: 11-03・11-03/§2・11-03/§3・D-51・D-62・D-71・D-113・D-116・第 266・第 267・第 268・第 346

## [commit.py](../../../../../../../src/shibuya/act/commit.py)

engine.commit — 二相コミットの Phase A(intent 収集)と Phase B(資源ごとの裁定)。

- 公開の関数とクラス
  - `CommitPlan`(クラス): Phase B の出力。
  - `IntentBatch`(クラス): Phase A の出力(SoA)。1 個体につき 1 件までに畳んである。
  - `ResourceSpace`(クラス): 資源 ID の名前空間(POI / 会話相手 / 就寝スロット)。
  - `arbitrate_resources`(関数): Phase B: 資源ごとに pk 昇順で確定する(**世界は書き換えない**)。
  - `delta_perc_ns`(関数): 起床条件 → δ_perc[ns]\(予期クラス別の定数・expedient)。
  - `tick_start_ns`(関数): tick 開始のナノ秒(δ_perc を足す基準)。
- import している内部モジュール: `shibuya.foundation.hashing`・`shibuya.foundation.types`・`shibuya.foundation.vocab.act_codes`・`shibuya.foundation.vocab.agent_codes`
- 呼び手: `shibuya.act.activity`・`shibuya.act.apply`・`shibuya.act.intake.from_words`・`shibuya.act.intent`・`shibuya.act.ops.shop`・`shibuya.runtime.systems.act`・`shibuya.runtime.systems.assemble`・`shibuya.runtime.systems.judge`
- 読む試験: `tests/economy/stage2/test_stage2_calls.py`・`tests/engine/processes/test_civic.py`・`tests/engine/processes/test_crowd.py`・`tests/engine/processes/test_rail.py`・`tests/engine/processes/test_rail_board_intent.py`・`tests/engine/processes/test_rail_return.py`・`tests/engine/test_c9b_targets_attention.py`・`tests/engine/test_conversation_invite.py`・`tests/engine/test_defect_fixes_1103.py`・`tests/engine/test_geometry_c9.py`・`tests/engine/test_intent_hold.py`・`tests/engine/test_ledger_wiring.py`・`tests/engine/test_move_destination.py`・`tests/engine/test_plan_sleep_d62.py`・`tests/engine/test_renderer_wiring.py`・`tests/engine/test_resolve.py`・`tests/engine/test_seat_release_2_4.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/test_two_phase.py`・`tests/engine/test_vocab_v2_eat.py`
- 読む試験(道筋で): `tests/tools/test_pkgmove.py`

## [gate.py](../../../../../../../src/shibuya/act/gate.py)

act.gate — 割る段で ``engine/resolve.py`` を割った割り先(全ファイルの表 §4・名の表は``tools/pkgmove/map.toml`` の割る行)。

- 公開の関数とクラス
  - `ResolveOutcome`(クラス): Phase C の結果(診断行の素材)。
- import している内部モジュール: `shibuya.foundation.ports.ledger`・`shibuya.foundation.vocab.agent_codes`・`shibuya.world.model.agent_table`・`shibuya.world.model.geometry`
- 呼び手: `shibuya.act.apply`・`shibuya.act.ops.move`・`shibuya.act.ops.rail`・`shibuya.act.ops.shop`・`shibuya.act.ops.talk`
- 読む試験: `tests/engine/test_c9b_targets_attention.py`・`tests/engine/test_familiarity.py`・`tests/engine/test_geometry_c9.py`・`tests/engine/test_intent_chooser.py`・`tests/engine/test_intent_hold.py`・`tests/engine/test_move_destination.py`・`tests/engine/test_presence_exit_walk.py`・`tests/engine/test_stage3_small_fixes.py`・`tests/engine/test_two_layer_activity.py`
- 書きの許可
  - `_fail`: 直接の書き `agents.last_result`・`agents.last_result_tick`
  - `_ok`: 直接の書き `agents.last_result`・`agents.last_result_tick`
- 決定の ID: 11-03・11-03/§3・D-51・D-62・D-112・D-113・D-118・第 266・第 267・第 275・第 275 #2・第 288・第 346

## [intent.py](../../../../../../../src/shibuya/act/intent.py)

engine.intent — **意図の保持**(段 2c・D-112 ①・D-114 案 A・第288)。

- 公開の関数とクラス
  - `IntentLayer`(クラス): 意図の保持(``engine.run`` が活動層と一緒に作る=語彙 v3・``--activity on``・``candidates``)。
  - `intent_summary`(関数): 計数 → manifest ``intent`` の形(アジェンダ §3-6)。
- import している内部モジュール: `shibuya.act.activity`・`shibuya.act.commit`・`shibuya.act.ops.intent_writes`・`shibuya.foundation.vocab.act_codes`・`shibuya.foundation.vocab.actions`・`shibuya.foundation.vocab.agent_codes`
- 呼び手: `shibuya.interfaces.cli.main`・`shibuya.runtime.result`・`shibuya.runtime.run`・`shibuya.runtime.systems.assemble`
- 読む試験: `tests/c6/test_t3_parallel_invariance.py`・`tests/economy/test_single_write_path.py`・`tests/engine/memory/test_m0_store_schema.py`・`tests/engine/space/test_nav1_units.py`・`tests/engine/state/test_move_prep_stage2.py`・`tests/engine/test_intent_hold.py`・`tests/engine/test_state_ledger_10b.py`・`tests/llm/test_fleet_contract.py`
- 読む試験(道筋で): `tests/engine/systems/test_fix_guards.py`・`tests/engine/systems/test_stage_a_guard.py`
- 状態台帳の行
  - 持ち主 `intent_layer`(`IntentLayer`)
    - `O4` IntentLayer _payload(挙動 behavior・復元 required) 道筋 `intent_layer._payload` 書ける系: activity_intent・apply_responses・phase_a・phase_c
    - `O5` IntentLayer _proposals・_executing・_kept_walk(挙動 no・復元 discardable) 道筋 `intent_layer._executing`・`intent_layer._kept_walk`・`intent_layer._proposals` 書ける系: activity_intent・apply_responses・phase_a・phase_c
    - `O6` IntentLayer stats・ticks_sum・ticks_n(挙動 diag・復元 discardable) 道筋 `intent_layer.stats`・`intent_layer.ticks_n`・`intent_layer.ticks_sum` 書ける系: activity_intent・apply_responses・detect・phase_a・phase_c
- 決定の ID: D-51・D-62・D-112・D-114・D-122・第 288

## [target.py](../../../../../../../src/shibuya/act/target.py)

engine.poi_target — 購入/食事/並ぶの対象を**候補 → 選び手**で決める(段 2a・D-114 (a))。

- 公開の関数とクラス
  - `TargetResolver`(クラス): 対象欄の読み・候補の絞り込み・選び手の抽選(1 ランに 1 つ・世界は読むだけ)。
  - `move_resolution_summary`(関数): 段 2b の計数 → manifest ``move_resolution`` の形。
  - `resolution_summary`(関数): 計数 → manifest ``target_resolution`` の形((i)〜(iv)+エントロピーの平均)。
- import している内部モジュール: `shibuya.foundation.ports.choice`・`shibuya.foundation.vocab.act_codes`・`shibuya.foundation.vocab.agent_codes`・`shibuya.foundation.vocab.place_words`・`shibuya.world.model.assets`・`shibuya.world.model.state`
- 呼び手: `shibuya.interfaces.cli.main`・`shibuya.runtime.result`・`shibuya.runtime.run`・`shibuya.runtime.systems.assemble`・`shibuya.runtime.systems.report`
- 読む試験: `tests/engine/test_classical_policy.py`・`tests/engine/test_intent_chooser.py`・`tests/engine/test_intent_hold.py`・`tests/engine/test_move_destination.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_stage3_small_fixes.py`・`tests/engine/test_store_choice.py`
- 状態台帳の行
  - 持ち主 `poi_resolver`(`TargetResolver`)
    - `O26` TargetResolver _cat_mask_cache・stats・entropy_sum・named_closed・move_stats(挙動 diag・復元 discardable) 道筋 `poi_resolver._cat_mask_cache`・`poi_resolver.entropy_sum`・`poi_resolver.move_stats`・`poi_resolver.stats` 書ける系: apply_responses・phase_c
    - `O94` TargetResolver named_closed(名指しの店の即時閉店の控え)(挙動 behavior・復元 required) 道筋 `poi_resolver.named_closed` 書ける系: apply_responses・phase_c
- 決定の ID: D-112・D-114・D-120・第 270・第 286
