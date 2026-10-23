# 複数の系が書く列の一覧(1-0)

- ユーザーの条件(2026-10-13): 同じ列を複数の区間(系)が書いている所を、後で話題ごとにまとめ直すときの課題として記録する。
- 作り方: `multi_writers.py`(このフォルダ)。**宣言**=系の表 `SYSTEMS` の書く欄(SoA は resolve の口の静的な閉包=上限・外の状態は道筋の宣言を台帳の項目に当てた)。**観測**=系ごとの全欄の差(1-0 のラン・6 構成・ラン 12 本・1,000 体・seed 1・全 tick: golden_null_arm, v1_edge, v2_edge_attention, v3_classical_mem_rel, v3_default, v3_mem_rel_store)で実際に値を変えた系。段 FIX の後は段 DEF の測り(`1-0_probe`)と段 FIX の測り(`1-0_probe_fix2`=scratch の中身と digest できない外の道筋の代わりの digest つき・1 日)の和。
- 並びは呼ぶ順(表の順)。後の系が前の系の書いた値を上書きする=系の順を入れ替えると結果が動く(草案 §3-3 の 12)。
- 数: SoA の列で 2 系以上が書く=宣言 56・観測 33。外の状態の道筋で 2 系以上=宣言 456・観測 66(行の単位の観測 32)。草案 §1-5 の測り(HEAD・6 構成・窓の tick)は SoA 28 列・外の行 27。

## SoA の列(観測で 2 系以上)

| 列 | 軸 1 | 観測の書き手(順) | 宣言の書き手(閉包=上限) |
|---|---|---|---|
| `agents.activity` | behavior | world → presence → apply_responses → plan_boundary → phase_c → conversation → close_final | world → presence → apply_responses → plan_boundary → phase_c → conversation → activity_intent → day_close → close_final |
| `agents.band` | no | world → presence → phase_c | world → presence → plan_boundary → phase_c → day_close → close_final |
| `agents.board_line` | behavior | plan_boundary → phase_c | presence → plan_boundary → phase_c |
| `agents.cell` | behavior | world → presence → phase_c | world → presence → plan_boundary → phase_c → day_close → close_final |
| `agents.energy_balance` | diag | body → phase_c | body → home_meal → phase_c |
| `agents.fatigue` | behavior | body → phase_c | body → phase_c |
| `agents.holdings` | behavior | world → phase_c | world → phase_c |
| `agents.hunger` | behavior | body → phase_c | body → home_meal → phase_c |
| `agents.intent_action` | behavior | phase_c → activity_intent | phase_c → activity_intent |
| `agents.intent_kind` | behavior | phase_c → activity_intent | phase_c → activity_intent |
| `agents.intent_since` | behavior | phase_c → activity_intent | phase_c → activity_intent |
| `agents.intent_target` | behavior | phase_c → activity_intent | phase_c → activity_intent |
| `agents.last_result` | behavior | world → phase_c | world → presence → plan_boundary → phase_c → conversation → activity_intent |
| `agents.last_result_tick` | behavior | world → phase_c | world → presence → plan_boundary → phase_c → conversation → activity_intent |
| `agents.mem_importance` | behavior | decide → memory | llm_receive → decide → memory |
| `agents.mem_last` | behavior | decide → memory | llm_receive → decide → memory |
| `agents.mem_n` | behavior | decide → memory | llm_receive → decide → memory |
| `agents.node` | behavior | world → presence → phase_c | world → presence → plan_boundary → phase_c → day_close → close_final |
| `agents.plan_flags` | behavior | world → presence | day_head → world → presence → plan_boundary → day_close → close_final |
| `agents.poi_ref` | behavior | world → presence → phase_c | world → presence → plan_boundary → phase_c |
| `agents.poi_since` | behavior | world → presence → phase_c | world → presence → plan_boundary → phase_c |
| `agents.queue_poi` | behavior | world → phase_c | world → presence → plan_boundary → phase_c |
| `agents.queue_since` | behavior | world → phase_c | world → presence → plan_boundary → phase_c |
| `agents.rel_last` | no | relations_wake → memory | relations_wake → memory |
| `agents.rel_n` | behavior | relations_wake → memory | relations_wake → memory |
| `agents.since_meal_kcal` | behavior | body → phase_c | body → home_meal → phase_c |
| `agents.sleep_pending` | behavior | plan_boundary → phase_c | presence → plan_boundary → phase_c |
| `agents.talk_partner` | behavior | apply_responses → phase_c → conversation | apply_responses → phase_c → conversation |
| `agents.target_node` | behavior | world → presence → plan_boundary → phase_c | world → presence → plan_boundary → phase_c → activity_intent → day_close → close_final |
| `agents.transit_ref` | behavior | world → presence → phase_c → close_final | world → presence → plan_boundary → phase_c → day_close → close_final |
| `agents.transit_state` | behavior | world → presence → phase_c → close_final | world → presence → plan_boundary → phase_c → day_close → close_final |
| `agents.xy` | behavior | world → presence → phase_c | world → presence → plan_boundary → phase_c → day_close → close_final |
| `pois.stock` | behavior | world → phase_c | world → phase_c |

## SoA の列(宣言だけで 2 系以上・観測では 1 系以下)

| 列 | 軸 1 | 観測 | 宣言 |
|---|---|---|---|
| `agents.activity_kind` | behavior | activity_intent | presence → activity_intent |
| `agents.activity_until` | behavior | activity_intent | presence → activity_intent |
| `agents.board_since` | behavior | phase_c | presence → plan_boundary → phase_c |
| `agents.hunger_stage` | behavior | detect | detect → home_meal |
| `agents.last_action` | behavior | phase_c | phase_c → activity_intent |
| `agents.mem_cell` | behavior | memory | llm_receive → decide → memory |
| `agents.mem_kind` | behavior | memory | llm_receive → decide → memory |
| `agents.mem_object` | behavior | memory | llm_receive → decide → memory |
| `agents.mem_partner` | behavior | memory | llm_receive → decide → memory |
| `agents.mem_result` | behavior | memory | llm_receive → decide → memory |
| `agents.mem_tick` | behavior | memory | llm_receive → decide → memory |
| `agents.refractory_until` | behavior | decide | wake_filter → decide |
| `agents.rel_first` | behavior | memory | relations_wake → memory |
| `agents.rel_kind` | behavior | memory | relations_wake → memory |
| `agents.rel_partner` | behavior | memory | relations_wake → memory |
| `agents.rel_sign` | behavior | memory | relations_wake → memory |
| `agents.sm_first` | behavior | memory | llm_receive → decide → memory |
| `agents.sm_last` | behavior | memory | llm_receive → decide → memory |
| `agents.sm_n` | behavior | memory | llm_receive → decide → memory |
| `agents.sm_poi` | behavior | memory | llm_receive → decide → memory |
| `agents.sm_precision` | behavior | memory | llm_receive → decide → memory |
| `agents.sm_source` | behavior | memory | llm_receive → decide → memory |
| `agents.sm_valence` | behavior | memory | llm_receive → decide → memory |

## 外の状態(行の単位・観測で 2 系以上)

| 行 | 観測の書き手(順) |
|---|---|
| O2 | activity_intent → checkpoint |
| O5 | apply_responses → phase_a → activity_intent |
| O6 | apply_responses → detect → phase_a → activity_intent |
| O9 | decide → memory |
| O11 | decide → memory |
| O19 | apply_responses → relations_wake → decide → conversation → memory |
| O28 | body → phase_c → energy_after |
| O34 | apply_responses → observe |
| O36 | world → presence |
| O37 | day_head → world |
| O39 | apply_responses → decide → conversation |
| O41 | apply_responses → decide → conversation |
| O43 | apply_responses → decide |
| O50 | day_head → world → phase_c → close_final |
| O55 | day_head → world |
| O56 | day_head → world |
| O57 | world → phase_c → day_close → close_final |
| O58 | world → phase_c |
| O59 | world → phase_c → day_close → close_final |
| O60 | world → phase_c |
| O61 | world → close_final |
| O63 | world → perceive_prepare → decide |
| O64 | decide → memory |
| O66 | apply_responses → detect → phase_a → activity_intent |
| O70 | world → presence → plan_boundary → observe → close_final |
| O73 | world → phase_c → close_final |
| O77 | world → phase_c → day_close → close_final |
| O79 | world → phase_c → day_close → close_final |
| O80 | world → day_close → close_final |
| O81 | world → phase_c |
| O92 | world → phase_c → day_close → close_final |
| O93 | world → phase_c → day_close → close_final |

## 外の状態(道筋の単位・観測で 2 系以上)

| 道筋 | 軸 1 | 観測の書き手(順) | 宣言の書き手 |
|---|---|---|---|
| `O5:intent_layer._executing` | no | phase_a → activity_intent | apply_responses → phase_a → phase_c → activity_intent |
| `O5:intent_layer._kept_walk` | no | phase_a → activity_intent | apply_responses → phase_a → phase_c → activity_intent |
| `O5:intent_layer._proposals` | no | apply_responses → activity_intent | apply_responses → phase_a → phase_c → activity_intent |
| `O6:intent_layer.stats` | diag | apply_responses → detect → phase_a → activity_intent | apply_responses → detect → phase_a → phase_c → activity_intent |
| `O11:mem_layer.stats` | diag | decide → memory | llm_receive → decide → memory |
| `O19:rel_layer.origin_of` | diag | apply_responses → conversation | apply_responses → relations_wake → decide → conversation → memory |
| `O19:rel_layer.stats` | diag | apply_responses → relations_wake → decide → memory | apply_responses → relations_wake → decide → conversation → memory |
| `O28:energy.counts` | diag | body → phase_c | body → home_meal → phase_c → energy_after |
| `O28:energy.intake_kcal` | diag | body → phase_c | body → home_meal → phase_c → energy_after |
| `O28:energy.meal_bits` | diag | body → phase_c | body → home_meal → phase_c → energy_after |
| `O28:energy.n_meals` | diag | body → phase_c | body → home_meal → phase_c → energy_after |
| `O36:presence._extra` | behavior | world → presence | day_head → world → presence → plan_boundary → day_close → close_final |
| `O36:presence._skip_depart_at` | behavior | world → presence | day_head → world → presence → plan_boundary → day_close → close_final |
| `O37:presence._pulled_in_today` | diag | day_head → world | day_head → world → presence → plan_boundary → day_close → close_final |
| `O39:conv._of_agent` | behavior | apply_responses → conversation | llm_receive → apply_responses → wake_sources → decide → conversation |
| `O39:conv._refusal_until` | behavior | apply_responses → conversation | llm_receive → apply_responses → wake_sources → decide → conversation |
| `O39:conv.pending_invites` | behavior | apply_responses → conversation | llm_receive → apply_responses → wake_sources → decide → conversation |
| `O39:conv.sessions` | behavior | apply_responses → decide → conversation | llm_receive → apply_responses → wake_sources → decide → conversation |
| `O41:conv.closed_by_reason` | diag | decide → conversation | llm_receive → apply_responses → wake_sources → decide → conversation |
| `O41:conv.n_gate_rejected` | diag | apply_responses → conversation | llm_receive → apply_responses → wake_sources → decide → conversation |
| `O41:conv.origin_counts` | diag | apply_responses → conversation | llm_receive → apply_responses → wake_sources → decide → conversation |
| `O41:conv.size_hist` | diag | decide → conversation | llm_receive → apply_responses → wake_sources → decide → conversation |
| `O43:run_day.pending` | behavior | apply_responses → decide | llm_receive → apply_responses → decide → drain |
| `O50:runner.rail.occupancy` | behavior | day_head → world → phase_c → close_final | day_head → world → presence → plan_boundary → phase_c → day_close → close_final |
| `O50:runner.rail.peak_ratio` | behavior | day_head → phase_c | day_head → world → presence → plan_boundary → phase_c → day_close → close_final |
| `O55:runner.last_mile.delivered` | no | day_head → world | day_head → world → day_close → close_final |
| `O57:ledger.money._day` | behavior | day_close → close_final | world → phase_c → day_close → close_final |
| `O57:ledger.money._lines` | behavior | world → phase_c | world → phase_c → day_close → close_final |
| `O58:ledger.money._raw_amt` | no | world → phase_c | world → phase_c → day_close → close_final |
| `O58:ledger.money._raw_code` | no | world → phase_c | world → phase_c → day_close → close_final |
| `O58:ledger.money._raw_pi` | no | world → phase_c | world → phase_c → day_close → close_final |
| `O58:ledger.money._raw_qs` | no | world → phase_c | world → phase_c → day_close → close_final |
| `O58:ledger.money._raw_tick` | no | world → phase_c | world → phase_c → day_close → close_final |
| `O59:ledger.goods._day` | behavior | day_close → close_final | world → phase_c → day_close → close_final |
| `O59:ledger.goods._shelf` | behavior | world → phase_c | world → phase_c → day_close → close_final |
| `O59:ledger.goods._sold_today` | behavior | phase_c → day_close → close_final | world → phase_c → day_close → close_final |
| `O60:ledger.goods._dl_code` | no | world → phase_c | world → phase_c → day_close → close_final |
| `O60:ledger.goods._dl_poi` | no | world → phase_c | world → phase_c → day_close → close_final |
| `O60:ledger.goods._dl_qty` | no | world → phase_c | world → phase_c → day_close → close_final |
| `O60:ledger.goods._dl_tick` | no | world → phase_c | world → phase_c → day_close → close_final |
| `O61:runner.log` | no | world → close_final | day_head → world → day_close → close_final |
| `O63:renderer._tickc` | no | world → perceive_prepare | world → perceive_prepare → decide |
| `O64:renderer.signage_exposures` | no | decide → memory | decide → memory |
| `O70:presence.n_departed_by_llm` | diag | world → close_final | day_head → world → presence → plan_boundary → wake_filter → decide → observe → day_close → close_final |
| `O73:runner.rail.n_departed_riders` | diag | world → close_final | day_head → world → presence → plan_boundary → phase_c → day_close → close_final |
| `O73:runner.rail.n_departures` | diag | world → close_final | day_head → world → presence → plan_boundary → phase_c → day_close → close_final |
| `O73:runner.rail.n_no_return` | diag | world → close_final | day_head → world → presence → plan_boundary → phase_c → day_close → close_final |
| `O77:ledger.money._flow` | diag | world → phase_c → day_close → close_final | world → phase_c → day_close → close_final |
| `O77:ledger.money._last_change_day` | diag | world → phase_c | world → phase_c → day_close → close_final |
| `O77:ledger.money._last_close` | diag | day_close → close_final | world → phase_c → day_close → close_final |
| `O79:ledger.goods._household_sku` | behavior | world → phase_c | world → phase_c → day_close → close_final |
| `O79:ledger.goods._shelf_age` | behavior | world → day_close → close_final | world → phase_c → day_close → close_final |
| `O80:ledger.goods._day_waste_g` | diag | world → day_close → close_final | world → phase_c → day_close → close_final |
| `O80:ledger.goods._inflow` | diag | world → day_close → close_final | world → phase_c → day_close → close_final |
| `O80:ledger.goods._last_close` | diag | day_close → close_final | world → phase_c → day_close → close_final |
| `O80:ledger.goods._open_stock` | diag | day_close → close_final | world → phase_c → day_close → close_final |
| `O80:ledger.goods._outflow` | diag | world → day_close → close_final | world → phase_c → day_close → close_final |
| `O80:ledger.goods._waste_g_daily` | diag | day_close → close_final | world → phase_c → day_close → close_final |
| `O81:ledger.goods.n_moves` | diag | world → phase_c | world → phase_c → day_close → close_final |
| `O92:ledger.money._day_marks` | diag | day_close → close_final | world → phase_c → day_close → close_final |
| `O92:ledger.money._flow_daily` | diag | day_close → close_final | world → phase_c → day_close → close_final |
| `O92:ledger.money._raw_pos` | diag | world → phase_c | world → phase_c → day_close → close_final |
| `O92:ledger.money._snap` | diag | day_close → close_final | world → phase_c → day_close → close_final |
| `O92:ledger.money.n_transfers` | diag | world → phase_c | world → phase_c → day_close → close_final |
| `O93:ledger.goods._dl_marks` | diag | day_close → close_final | world → phase_c → day_close → close_final |
| `O93:ledger.goods._dl_pos` | diag | world → phase_c | world → phase_c → day_close → close_final |
