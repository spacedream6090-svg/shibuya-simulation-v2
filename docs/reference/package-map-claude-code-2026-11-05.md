# 包みの分類の案(Claude Code の独立の案)2026-11-05

> 11-05/§4 の発注に答える案です。読むだけで作りました(枝 `build/spatial-d102-prep`・HEAD `15b6bbd`)。ファイルは 1 本も動かしていません。推薦してよいのは本書だけで、決めるのはユーザーです。
> 付属の表は [package-map-claude-code-2026-11-05-files.md](package-map-claude-code-2026-11-05-files.md) です。
> 印の約束は次のとおりです。印の無い数は実測(AST と grep)です。「模擬」は割り当ての表から辺を計算した結果で、ファイルは動かしていません。自分の組み立てには【見立て】、測っていない数には【推測】を付けました。数えたスクリプトはスクラッチに置き、リポには入れていません。

## 要旨

1. 11 の包みに全 324 ファイルを割り当てました。build の 79 本は動かさず、23 本を関数の単位で割り、残りは移すだけです。
2. 世界と心を分ける鍵は 2 つです。`perception/renderer.py` を「何があるか」(world)と「文に描く」(mind)に割ること、語彙と知覚の型を foundation へ下ろすことです。
3. 割った後を模擬すると、包みをまたぐ辺は 796 本です(頭の import 609・関数の中 146・注釈だけ 41)。案の契約 8 本は、模擬の木に本物の lint-imports をかけて、例外 8 本を認めれば全部通りました。
4. 原則に反する辺は 35 本です。例外 8 本、腕の束ね 20 本、注釈だけ 7 本です。
5. 包みの単位の循環は 2 組残ります(world・act・economy と runtime・experiments)。副包みの単位では、例外 8 本を除けば循環は 0 です。
6. 「心は世界を読まない」は import の検査だけでは守れません。列の持ち主の欄・AST の検査・読み取り専用の口・揺らし試験の 4 段で守り、表を物理的に割るのは v3 にします。
7. 世界の列の書きは全部 act の関数を通します。法則(world.laws)はその呼び手です。心の欄の書き手は mind、金と物の書き手の実体は economy です。
8. 関係と約束は 3 か所に分けます。事実は world、運ぶ器は society、本人の理解は mind です。約束そのものは本人の理解で、器は約束を持ちません。
9. 移動の前に塞ぐ穴が 1 つあります。クラスの「モジュール名.クラス名」が final のハッシュに入っていて、名前を変えると値が変わりました(実測)。固定の表を先に入れないと、1 バイト不変の移動はできません。
10. 迷いは 16 件、原則への異論は 6 件です(§7・§8)。

## 1. 包みと層の形

### 1-1 層(上が下を読む・`|` は互いに読まない)

```text
interfaces
validation.static
experiments.drive
runtime
society.arms
world.laws
mind | act | society.vessels
world.body
world.model | economy
world.facts | world.ledger | experiments.port
foundation

build は横に置く。ランの側からは読まれない。build は foundation・economy・world の一部・experiments.port を読む。
```

原則の 11 の包みはそのままです。`world`・`society`・`experiments`・`validation` は中を副包みに分けました。分けないと `world` と `act` が包みの単位で循環し、契約に書けないためです(§8 の異論 1)。

### 1-2 大きさ(模擬・割りの残りの docstring と import を含む)

| 包み | 行数 | 新モジュール | 中身(副包みの行数はおよその値) |
|---|---:|---:|---|
| foundation | 11,579 | 44 | 時間・乱数・ハッシュ・SoA・manifest・語彙 `vocab` 約 2,160・口の型 `ports` 約 1,690・文の道具 `text` 約 1,880・予約の列 `queues` 約 1,050・出来事の記録 `journal` 820・腕の切替口 `arms` |
| world | 26,201 | 63 | `model` 8,002・`laws` 7,999・`ledger` 4,347・`facts` 3,069・`body` 2,486 |
| mind | 12,595 | 36 | `memory` 5,197・`judge` 2,038・`percept` 1,738・`plan` 1,411・`relations` 1,068・`system1` 397・`ops` 218 |
| act | 7,815 | 19 | `ops` 2,264・`intake` 2,106・`target` 680・`intent` 524・`activity` 519・`apply` 454・`commit` 300・`gate` 154 |
| economy | 8,993 | 18 | 今の `economy/` と `core/wage_formula.py`・`engine/economy_rules.py`・`engine/economy_stage2.py` |
| society | 10,848 | 30 | `arms` 7,490(腕の束ね)・`vessels` 3,241(会話・発話・道具の台帳・計器) |
| runtime | 20,411 | 43 | `systems` 6,599・`state` 5,469・`inference` 3,471・`clocks` 1,319・`result` 1,227・`run` 987・`arbiter` 457 |
| experiments | 2,828 | 10 | `port` 1,877(runtime が読む)・`drive` 933(runtime の上) |
| validation | 1,646 | 7 | `static` 1,642(試験だけが呼ぶ検査)。`sealed` は今は空(迷い 12) |
| interfaces | 2,069 | 3 | `cli` |
| build | 36,101 | 79 | 今の `build/` のまま |

今の `src/shibuya` は `.py` 323 本・141,092 行です。[技術マップ](tech-map-2026-11-03.md)の後に `engine/defect_fixes_1103.py` が足されたので 1 本増えています。

## 2. 中心の部品の割り方

行数は全部 AST で数えました。割り先の行数は関数・クラス・定数の行の和で、docstring と import を含みません。定数は参照元が 1 つの割り先だけならそこへ付けました。

### 2-1 `agents/state.py`(854 行)

| 割り先 | 行数 | 中身 |
|---|---:|---|
| `world/model/agent_table.py` | 447 | `AgentState`(列の宣言 362 行を含む)・`LAST_ACTION_NONE` |
| `foundation/vocab/agent_codes.py` | 324 | `AgentKind`・`Activity`・`ResultCode`・`WakeCondition`・`ActivityKind`・`IntentKind`・`focus_code_*`・`*_FIELDS`・`REFRACTORY_MINUTES`・`WAKE_CONDITION_CLASS` ほか |

- 今 54 本が import しますが、ほとんどは語彙だけです。`AgentState` の名を使うのは 16 本で、mind と society からの辺は全部型の注釈だけでした(§4-5 の 7 本)。
- 表の実体は組み立てが作って渡します。mind は表を import しません。
- 列を持ち主で割るのは v3 です(§5-1)。

### 2-2 `engine/resolve.py`(3,699 行)

| 割り先 | 行数 | 関数 | 書く相手 |
|---|---:|---|---|
| `act/apply.py` | 454 | `apply`・`_apply_sleep`・`_apply_report`・`_apply_rest`・`_apply_record_only`・`_apply_help`・表 `_APPLY*` | 判断の結果の入口 |
| `act/gate.py` | 154 | `ResolveOutcome`・`_ok`・`_fail` | 結果の型 |
| `act/ops/shop.py` | 454 | `_apply_buy`・`_complete_buy`・`_apply_eat`・`_complete_eat`・`_apply_queue`・`_apply_wait`・`_serve_poi_queue`・`balk_queue`・`release_indoor`・`_stage2_*`・`_payable`・`_purchase_tax` | 買う・食べる・並ぶ |
| `act/ops/rail.py` | 379 | `_apply_board`・`_serve_board_queue`・`_board_riders`・`_enter_board_queue`・`_apply_alight`・`rail_arrive`・`rail_depart`・`place_at_external`・`sync_transit_activity` ほか | 乗る・降りる。鉄道の法則の呼び口を含む |
| `act/ops/move.py` | 322 | `_apply_engine_step`・`_apply_move`・`_nav_*`・`nav_place`・`_settle_approach`・`_approach_dest_node`・`_cell_of_node` | 歩く |
| `act/ops/plan_writes.py` | 309 | `set_plan_state`・`begin_planned_sleep`・`wake_from_plan`・`begin_exit_walk`・`begin_walk_to`・`clear_board_intent` | 計画実行層の呼び口 |
| `act/ops/law_writes.py` | 197 | `restock`・`discard_to_bin`・`consume`・`collect_waste`・`set_thermal`・`set_notice_state`・`set_open_flags`・`request_open_close` | 世界過程の呼び口 |
| `act/ops/body_writes.py` | 158 | `advance_body`・`initialize_energy`・`energy_home_meal`・`energy_out_of_area_meal`・`_energy_meal`・`_energy_snack` | 体の法則の呼び口 |
| `act/ops/talk.py` | 154 | `_apply_talk`・`_apply_leave`・`talk_within_reach`・`join_conversation`・`end_conversation`・`set_conversing`・`revert_conversation` | 話す |
| `act/ops/intent_writes.py` | 115 | `set_intent`・`clear_intent`・`fail_intent`・`relabel_intent_failure`・`intent_kept_by`・`set_activity`・`set_activity_until` | 実行中の行為 |
| `act/ops/focus.py` | 94 | `_set_focus`・`_clear_focus`・`_advance_focus`・`_focus_xy` | 注意の焦点(列は mind の持ち物・迷い 6) |
| `act/ops/init_writes.py` | 82 | `initialize`・`set_initial_activity` | 組み立ての初期値 |
| `mind/ops.py` | 218 | `write_memory`・`write_familiarity`・`write_store_memory`・`write_relations`・`set_refractory`・`clear_refractory`・`apply_detection`・`refractory_ticks`・`wake_condition_index`・`normalized_refractory_scale` | 心の欄 |
| `runtime/state/restore.py` | 136 | `restore_soa`・`restore_items`・`_restore_value`・`_restore_array_into` | 再開の復元(全部の列) |
| `foundation/write_guard.py` | 33 | `_require_thawed` | 書きの検査(act と mind の両方が使う) |
| `foundation/vocab/act_codes.py` ほか | 5 | `TALK_OPEN_METERS`・`TALK_LEAVE_METERS`・`EXIT_WALK_FLAG`・`_REFRACTORY_TICKS` | 定数 |

- 今の SoA の書きは AST で見える分が 395 か所で、355 か所が resolve、残りの 40 か所は `AgentState` と `World` の組み立ての初期値です。`writable()` を呼ぶのも resolve の 50 か所だけです。「書き手は 1 本」は今でも成り立っています。割っても同じ形を保ちます。
- `systems/allow.py` は `engine/resolve.py` の 1 本を AST で読んで許可を作ります。割るときはファイルの一覧を読む形に直します(§6)。

### 2-3 `engine/commit.py`(1,008 行)

| 割り先 | 行数 | 関数 |
|---|---:|---|
| `act/intake/from_words.py` | 542 | `intents_from_responses`(342 行)・`parse_action`・`talk_partners`・`pair_partners`・`_talk_partners_reach`・`_poi_in_cell`・`engine_continuations`・`focus_codes`・`undefined_fallback_code`・`target_hint_code` |
| `act/commit.py` | 300 | `IntentBatch`・`ResourceSpace`・`CommitPlan`・`arbitrate_resources`・`_rank_within_resource`・`delta_perc_ns`・`tick_start_ns` |
| `foundation/vocab/act_codes.py` | 34 | `ACT_*`・`ACTION_WORDS`・`ACTION_CODES`・`ENGINE_STEP`・`WANDER_BAD_TARGET`・`S2_*` ほか |

`ACT_*` を下ろすと mind の `memory.py`・`decision/layer.py` から act への辺が消えます。

### 2-4 `perception/renderer.py`(3,112 行)

| 割り先 | 行数 | 中身 |
|---|---:|---|
| `mind/percept/draw.py` | 1,400 | `Rendered`・`Renderer.__init__`・`_render_percept`・`render_percept`・`draw`・`_b1`〜`_b6`・`_draw_b3`・`_draw_b4`・`_b5_ranked`・`_cell_blocks_ranked`・`_with_intent_line`・`_with_memory_line`・`_with_speech_lines`・`_contact_blocks`・`_lines_for`・`_pool_render`・`_rank_items`・`memory_item_text`・`compose_memory_line` ほか |
| `world/model/percept_scene.py` | 1,137 | `PerceptionAssets`・`_TickCache`・`Renderer.prepare_tick`・`perceive`・`_scene`・`_wake_view`・`_intent_view`・`_time_view`・`_nearby_people`・`_nearby_people_distance`・`_near_sort`・`_near_take`・`_acquaintances_of`・`_signage_poi`・`activity_class_of`・`_cheapest_price`・`_next_open_hour`・`_named_closed_text`・`_b4b_raw`・`_b4b_lines`・`_merge_activity_lines`・`near_tie_*` ほか |
| `foundation/text/percept_words.py` | 93 | `activity_line`・`named_closed_note`・`intent_line`・`person_word`・`near_person_text`・`_hunger_word`・`_activity_word` |
| `mind/percept/notice.py` | 74 | `Renderer._signage_seen`・`_signage_body`・`check_signage_p_see` |
| `runtime/inference/bridge.py` | 39 | `Renderer.render`(`perceive` の後に `render_percept` を呼ぶだけ) |

- 第 1 期 1-2 で「状態 → `Percept` → 文」の 2 段に分かれているので、切る線はもう引けています。9-1 の「何があるか(世界)」が `perceive` まで、「何に気づくか(心)」が `_signage_seen` です。
- `draw` の側に、状態を読む列は 0 でした(AST で見える分)。残る直接読みは B4b の文とキャッシュです(例外 T1)。
- クラス 1 つを 2 つの包みへ割る作業は移動ではありません。`prepare_tick` と `__init__` を分ける手当てが要ります。やる時期は迷い 16 です。

### 2-5 `engine/events/log.py`(820 行)

割りません。`foundation/journal.py` へ丸ごと移します。読むのは語彙と書きの許可(`systems/guard.py` も foundation へ下ろす)だけで、全層が書きます。出来事の型と記録の本体を別々の層に置くと辺が増えるだけでした。注意点は全知の覗き見です(迷い 8)。

### 2-6 `engine/arbiter.py`(640 行)

| 割り先 | 行数 | 中身 |
|---|---:|---|
| `runtime/arbiter.py` | 457 | `arbitrate`・`Arbiter`・`ArbiterDecision`・`call_budget_per_tick`・`_class_slot`。11-04b の 9-4 で消える部品 |
| `mind/system1/wake.py` | 63 | `WakeCandidates`(起きる候補の型) |

### 2-7 `engine/change_detect.py`(444 行)

| 割り先 | 行数 | 中身 |
|---|---:|---|
| `mind/system1/change_detect.py` | 290 | `ChangeDetector`・`DetectResult`・`B5Crossing`・`_make_cell_wake`・`_cell_wake_numpy` |
| `world/model/scene_hash.py` | 63 | `b4_block_raw`・`b4_block_hashes`(セルの見え方の指紋) |
| `foundation/vocab/agent_codes.py` | 6 | `INTERO_UP_EDGES`・`INTERO_VARS` |

`ChangeDetector` が指紋を呼ぶ辺は例外 T3 です。9-3c の形にすると、世界が「変わったセル」の配列を出し、心はそれを受けるだけになります【見立て】。

### 2-8 `engine/presence.py`(2,089 行)

| 割り先 | 行数 | 中身 |
|---|---:|---|
| `world/laws/presence.py` | 1,511 | `PlanExecutor`(1,459 行)・`EventType`・`_HomeShim` |
| `world/laws/presence_plan.py` | 402 | `PlanBlocks`・`_apply_derive_v2`・`_trim_nonstay_edges`・`_day_rows`・`_mix64` |

v3 ではさらに 3 つに割る案です【見立て】。予定(`PlanBlocks`)は mind、到着と退出の時刻の割り付け(`_spread_arrivals`・`_build_events`)は人口の出入りとして world.laws、体を動かす手順(`_do_arrive`・`_do_depart`・`_begin_walk`・`_flush_walkers`)は act です。今は指示書が presence を世界に入れた形([技術マップ](tech-map-2026-11-03.md)の注)のまま world に置きます(迷い 4)。

### 2-9 `engine/conversation.py`(979 行)

割りません。`society/vessels/conversation.py` へ移します。`ConversationManager` はセッションの状態機械で、器の形です。`_accepts` の応答率 0.8 の抽選は 11-05/§3-2 の 2 で消す死んだ道です。`wake_candidates` は心へ起床を渡す口なので、v3 で口の型に替えます【見立て】。

### 2-10 `engine/llm_bridge.py`(1,041 行)

| 割り先 | 行数 | 中身 |
|---|---:|---|
| `runtime/inference/bridge.py` | 825 | `LLMBridge`(487 行)・`PerceptionRendererAdapter`・`BridgeResult`・`StubRenderer`・`CallStart`・`delta_think_ticks`・`_kept_target` |
| `foundation/ports/inference.py` | 53 | `RenderedPrompt`・`Renderer`(Protocol) |

`llm/__init__.py`(型)と `llm/fleet.py` の型(`LLMCall`・`LLMResult`・`Deferred`・`Outcome`・`split_system_user` ほか 215 行)も `foundation/ports/inference.py` へ下ろします。`FleetClient`・`FleetBridge`(1,473 行)と `MockLLM`・`TapeLLM`(297 行)は `runtime/inference/` です(迷い 11)。

### 2-11 `cli.py`(1,876 行)

| 割り先 | 行数 | 中身 |
|---|---:|---|
| `interfaces/cli/main.py` | 1,568 | `main`(1,034 行)・`run`(174 行)・`undefined_registry_payload`・`checkpoints_payload`・`parse_refractory_scale`・`apply_fleet_queue_default`・`write_census_files`・`arm_baseline`・`run_arms` ほか |
| `interfaces/cli/wire_economy.py` | 134 | `build_ledger_bundle`・`household_wallets`・`_HouseholdWalletLedger`・`store_capital_array`・`store_capital_report` |

`python -m shibuya.cli` は `tools/night5070/experiments.json` などが文字列で持つので、`shibuya/cli.py` を 1 行の入口として残します(古い道の口ではなく外との約束です)。

### 2-12 `engine/run.py`(2,691 行)

| 割り先 | 行数 | 中身 |
|---|---:|---|
| `runtime/result.py` | 1,227 | `RunResult`(1,083 行)・`Checkpoint`・`decision_layers_summary`・`_calls_by_model`・`_action_usage`・`_tm234_sections`・`_calendar*_field` ほか |
| `runtime/run.py` | 987 | `run_day`(455 行)・`_settle_pending_invites`・`_schedule_with_population`・`_named_closed_lookup`・`_resolve_population`・`_default_mock`・`check_replay_tape` ほか |
| `interfaces/cli/run_args.py` | 193 | `main`・`add_fleet_args`・`fleet_from_args`・`add_calendar_args`・`calendar_kwargs_from_args` |

`python -m shibuya.engine.run` の入口は `interfaces/cli` へ移すか消します。

### 2-13 `engine/systems/*`(25 本)

置き場は `runtime/systems/` のままです。原則は「中身に触らない」なので、中身のある系は v3 で持ち主の包みへ寄せます。「列の読み」は AST で見える `agents.*` などの読みの数です。

| 今のファイル | 行数 | 新しい置き場 | 主な関数(行数) | 中身の持ち主 | 列の読み |
|---|---:|---|---|---|---:|
| `act.py` | 169 | `runtime/systems/` | `sys_phase_a` 42・`sys_phase_b` 14・`sys_phase_c` 89 | act | 2 |
| `allow.py` | 189 | 同じ | `index` 68(起動時に resolve を AST で読む) | runtime | 0 |
| `body.py` | 185 | 同じ | `sys_plan_boundary` 62・`sys_presence` 28・`sys_body` 26 | world.body・world.laws | 2 |
| `boxes.py` | 505 | 同じ | 箱の型 | runtime | 0 |
| `build.py` | 1,701 | `runtime/systems/assemble.py` | `build` 1,547 | runtime(全部を組み立てる場所) | 5 |
| `conductor.py` | 247 | 同じ | `conduct` 95 | runtime | 0 |
| `day.py` | 41 | 同じ | `sys_day_head`・`sys_day_close` | runtime | 0 |
| `decide.py` | 234 | 同じ | `sys_decide` 194 | mind と推論の口 | 4 |
| `guard.py` | 62 | `foundation/write_guard.py` | `system_scope`・`events_write_allowed` | foundation | 0 |
| `judge.py` | 401 | 同じ | `sys_apply_responses` 156・`sys_wake_filter` 63・`sys_wake_assemble` 51・`sys_arbiter` 35 | act(応答の適用)・mind(起床) | 4 |
| `llm_io.py` | 159 | 同じ | `receive_arrivals` 71・`utter` 53 | runtime(推論の口) | 2 |
| `observe.py` | 148 | 同じ | `observe` 61・`checkpoint` 58 | runtime(計器) | 3 |
| `overrides.py` | 90 | `validation/static/system_overrides.py` | 試験の差し替え | validation | 0 |
| `perceive.py` | 107 | 同じ | `sys_detect` 51・`sys_perceive_prepare` 34 | mind・world.model | 1 |
| `probe.py` | 315 | 同じ | `snapshot` 47・`plain` 44 | runtime(試験のときだけ) | 0 |
| `remember.py` | 77 | 同じ | `sys_memory` 38 | mind | 0 |
| `report.py` | 538 | 同じ | `report` 507 | runtime | 4 |
| `run_end.py` | 174 | 同じ | `sys_close_final` 87・`sys_drain` 63 | runtime | 0 |
| `spec.py` | 82 | 同じ | `make` 12 | runtime | 0 |
| `state_io.py` | 467 | 同じ | `hash_owners` 51・`relay_tables` 52・`day_record` 56 | runtime | 2 |
| `static_check.py` | 225 | `validation/static/system_static_check.py` | `analyze` 115 | validation | 0 |
| `table.py` | 578 | 同じ | 表 `SYSTEMS` | runtime | 0 |
| `talk.py` | 245 | 同じ | `sys_conversation` 176・`sys_relations_wake` 39 | society.vessels・act | 8 |
| `world.py` | 21 | 同じ | `sys_world` 6 | world.laws | 0 |
| `__init__.py` | 16 | 同じ | 頭 | runtime | 0 |

## 3. import の決まりの案

import-linter 2.15 の形です。`exclude_type_checking_imports` を立てます。空の殻のモジュール 352 本に模擬の辺を import で書いた木を作り、本物の `lint-imports` をかけました。結果は 8 本の契約が全部 KEPT で、1,310 の依存を解析し、`ignore_imports` は層の契約 8・mind の契約 6・器の契約 1 です(§4-5 の T1〜T8 と同じ 8 組)。実物を動かしてかけたものではありません。

```toml
[tool.importlinter]
root_package = "shibuya"
include_external_packages = false
exclude_type_checking_imports = true

# ---- 1. 全体の層(上から下へだけ読む・| は互いに読まない)
[[tool.importlinter.contracts]]
name = "layers: interfaces > validation.static > experiments.drive > runtime > society.arms > world.laws > (mind | act | society.vessels) > world.body > (world.model | economy) > (world.facts | world.ledger | experiments.port) > foundation"
type = "layers"
layers = [
  "shibuya.interfaces",
  "shibuya.validation.static",
  "shibuya.experiments.drive",
  "shibuya.runtime",
  "shibuya.society.arms",
  "shibuya.world.laws",
  "shibuya.mind | shibuya.act | shibuya.society.vessels",
  "shibuya.world.body",
  "shibuya.world.model | shibuya.economy",
  "shibuya.world.facts | shibuya.world.ledger | shibuya.experiments.port",
  "shibuya.foundation",
]
ignore_imports = [
  # 切符 L: 下から上・兄弟の間の辺。v3 の割りで消す(本文 §4-3 の表の番号)
  "shibuya.mind.relations.layer -> shibuya.world.model.proximity",      # T5
  "shibuya.world.model.percept_scene -> shibuya.mind.percept.notice",   # T6
  "shibuya.mind.judge.decision.layer -> shibuya.society.vessels.tools.registry",  # T7
  "shibuya.society.vessels.speech.layer -> shibuya.mind.memory.wom",    # T8
  "shibuya.mind.percept.draw -> shibuya.world.model.percept_scene",     # T1
  "shibuya.mind.percept.notice -> shibuya.world.model.percept_scene",   # T2
  "shibuya.mind.system1.change_detect -> shibuya.world.model.scene_hash",  # T3
  "shibuya.mind.judge.decision.layer -> shibuya.economy.stage2_bind",   # T4
]

# ---- 2. foundation は何も読まない
[[tool.importlinter.contracts]]
name = "foundation は何も読まない"
type = "forbidden"
source_modules = ["shibuya.foundation"]
forbidden_modules = [
  "shibuya.world", "shibuya.mind", "shibuya.act", "shibuya.economy", "shibuya.society",
  "shibuya.runtime", "shibuya.experiments", "shibuya.validation", "shibuya.interfaces", "shibuya.build",
]

# ---- 3. mind は foundation の口の型だけを読む
[[tool.importlinter.contracts]]
name = "mind は world・act・economy・society・runtime を読まない(知覚の口の型は foundation.ports)"
type = "forbidden"
source_modules = ["shibuya.mind"]
forbidden_modules = [
  "shibuya.world", "shibuya.act", "shibuya.economy", "shibuya.society",
  "shibuya.runtime", "shibuya.experiments", "shibuya.validation", "shibuya.interfaces", "shibuya.build",
]
allow_indirect_imports = true
ignore_imports = [
  "shibuya.mind.percept.draw -> shibuya.world.model.percept_scene",     # T1
  "shibuya.mind.percept.notice -> shibuya.world.model.percept_scene",   # T2
  "shibuya.mind.system1.change_detect -> shibuya.world.model.scene_hash",  # T3
  "shibuya.mind.judge.decision.layer -> shibuya.economy.stage2_bind",   # T4
  "shibuya.mind.relations.layer -> shibuya.world.model.proximity",      # T5
  "shibuya.mind.judge.decision.layer -> shibuya.society.vessels.tools.registry",  # T7
]

# ---- 4. 世界の列を書く関数は決まった呼び手だけ
[[tool.importlinter.contracts]]
name = "act.ops と act.apply を呼べるのは act・world.laws・society.arms・runtime・interfaces だけ"
type = "protected"
protected_modules = ["shibuya.act.ops", "shibuya.act.apply"]
allowed_importers = ["shibuya.act", "shibuya.world.laws", "shibuya.society.arms", "shibuya.runtime", "shibuya.interfaces"]
as_packages = true

# ---- 5. お金と物の書き手
[[tool.importlinter.contracts]]
name = "economy.ops と economy.goods を読めるのは economy・interfaces だけ(台帳は foundation.ports.ledger の型で渡す)"
type = "protected"
protected_modules = ["shibuya.economy.ops", "shibuya.economy.goods", "shibuya.economy.ledger"]
allowed_importers = ["shibuya.economy", "shibuya.interfaces"]
as_packages = true

# ---- 6. 経済が読める先
[[tool.importlinter.contracts]]
name = "economy は world.facts と foundation だけを読む"
type = "forbidden"
source_modules = ["shibuya.economy"]
forbidden_modules = [
  "shibuya.world.model", "shibuya.world.body", "shibuya.world.laws", "shibuya.world.ledger",
  "shibuya.mind", "shibuya.act", "shibuya.society", "shibuya.runtime",
]
allow_indirect_imports = true

# ---- 7. 器は判断と書きを持たない
[[tool.importlinter.contracts]]
name = "society.vessels は act・mind・runtime・world.laws を読まない"
type = "forbidden"
source_modules = ["shibuya.society.vessels"]
forbidden_modules = ["shibuya.act", "shibuya.mind", "shibuya.runtime", "shibuya.world.laws"]
allow_indirect_imports = true
ignore_imports = [
  "shibuya.society.vessels.speech.layer -> shibuya.mind.memory.wom",    # T8
]

# ---- 8. ランの側は build を読まない
[[tool.importlinter.contracts]]
name = "build はランで読まれない"
type = "forbidden"
source_modules = [
  "shibuya.foundation", "shibuya.world", "shibuya.mind", "shibuya.act", "shibuya.economy", "shibuya.society",
  "shibuya.runtime", "shibuya.experiments", "shibuya.validation.static", "shibuya.interfaces",
]
forbidden_modules = ["shibuya.build"]

# ---- 9. ランの側は封印を読む部品を読まない(validation.sealed を作ったら効く)
#      いまは src に validation.sealed が無いので、作るまで次の行を入れない。
#[[tool.importlinter.contracts]]
#name = "validation.sealed はランの側から読めない"
#type = "protected"
#protected_modules = ["shibuya.validation.sealed"]
#allowed_importers = ["shibuya.validation.sealed"]
#as_packages = true
```

import の契約で書けないことは試験に書きます。列の持ち主の検査(§5-1)・書きの閉包(`systems/allow.py`)・封印の語の検査(§8 の異論 6)です。

## 4. 辺の数

### 4-1 今の木

| 数え方 | 計 | 頭の import | 関数の中の遅延 import | TYPE_CHECKING |
|---|---:|---:|---:|---:|
| import の文 | 2,523 | 2,152 | 370 | 1 |
| モジュールの対(重複なし) | 1,251 | 1,032 | 218 | 1 |
| 使う名前を追う数え方(下の表と同じ) | 1,196 | 943 | 221 | 注釈だけ 32 |

`lint-imports` の HEAD の結果は 5 契約すべて KEPT・1,250 の依存です。対の数は AST の 1,251 と 1 本違います(どれかは確かめていません)。本物の TYPE_CHECKING は `economy/ops.py` の 1 文だけです。

### 4-2 割った後(模擬)

新モジュール 352 本、モジュールの対 1,387 本(頭の import 1,081・関数の中 229・注釈だけ 77)です。そのうち包みをまたぐ辺は 796 本(頭の import 609・関数の中 146・注釈だけ 41)です。

- 「注釈だけ」は、名前が型の注釈にしか出てこない辺です。`from __future__ import annotations` のファイルなら `if TYPE_CHECKING:` へ移せます。本物の TYPE_CHECKING でまたぐ辺は 0 本です。
- 使う名前を追って数えたので、再輸出の頭(10 本・281 の import)は空にする前提で数えていません。

表の中は「頭の import / 関数の中 / 注釈だけ」です。

| 元 \ 先 | foundation | world | mind | act | economy | society | runtime | experiments | validation | interfaces | build | 計 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| foundation |  |  |  |  |  |  |  |  |  |  |  | 0 |
| world | 93/1/1 |  | 1/0/0 | 11/0/0 |  |  |  |  |  |  |  | 107 |
| mind | 73/7/1 | 3/1/6 |  |  | 1/0/0 | 0/1/0 |  |  |  |  |  | 93 |
| act | 47/3/4 | 5/1/20 |  |  | 0/1/0 |  |  |  |  |  |  | 81 |
| economy | 10/4/0 | 0/6/0 |  |  |  |  |  |  |  |  |  | 20 |
| society | 66/6/1 | 4/9/1 | 11/3/0 | 5/0/0 |  |  |  |  |  |  |  | 106 |
| runtime | 81/18/1 | 34/18/4 | 32/4/0 | 25/1/0 | 1/1/0 | 9/18/0 |  | 2/3/0 |  |  |  | 252 |
| experiments | 6/1/0 | 0/1/0 | 0/2/0 |  |  |  | 1/3/0 |  |  |  |  | 14 |
| validation | 0/1/0 | 4/2/0 |  |  |  |  | 1/0/0 |  |  |  |  | 8 |
| interfaces | 6/9/0 | 13/6/1 | 7/3/0 | 2/1/0 | 12/0/0 | 0/3/0 | 5/3/1 | 1/3/0 |  |  |  | 76 |
| build | 33/1/0 | 2/0/0 |  |  | 2/0/0 |  |  | 0/1/0 |  |  |  | 39 |
| 計 |  |  |  |  |  |  |  |  |  |  |  | 796 |

### 4-3 副包みの単位(foundation への辺を除く)

| 元 | 先 | 頭の import | 関数の中 | 注釈だけ |
|---|---|---:|---:|---:|
| act | world.model | 2 | 1 | 20 |
| act | world.body | 3 | 0 | 0 |
| act | economy | 0 | 1 | 0 |
| build | economy | 2 | 0 | 0 |
| build | world.ledger | 1 | 0 | 0 |
| build | experiments.port | 0 | 1 | 0 |
| build | world.model | 1 | 0 | 0 |
| economy | world.facts | 0 | 6 | 0 |
| experiments.drive | runtime | 1 | 3 | 0 |
| experiments.drive | mind | 0 | 2 | 0 |
| experiments.drive | experiments.port | 0 | 1 | 1 |
| experiments.drive | world.ledger | 0 | 1 | 0 |
| interfaces | economy | 12 | 0 | 0 |
| interfaces | world.model | 9 | 1 | 1 |
| interfaces | mind | 7 | 3 | 0 |
| interfaces | runtime | 5 | 3 | 1 |
| interfaces | world.laws | 1 | 4 | 0 |
| interfaces | experiments.port | 1 | 2 | 0 |
| interfaces | act | 2 | 1 | 0 |
| interfaces | world.body | 1 | 1 | 0 |
| interfaces | world.facts | 2 | 0 | 0 |
| interfaces | society.vessels | 0 | 2 | 0 |
| interfaces | society.arms | 0 | 1 | 0 |
| interfaces | experiments.drive | 0 | 1 | 0 |
| mind | world.model | 3 | 1 | 6 |
| mind | society.vessels | 0 | 1 | 0 |
| mind | economy | 1 | 0 | 0 |
| runtime | mind | 32 | 4 | 0 |
| runtime | act | 25 | 1 | 0 |
| runtime | world.model | 14 | 2 | 4 |
| runtime | world.laws | 6 | 11 | 0 |
| runtime | society.arms | 5 | 11 | 0 |
| runtime | world.facts | 8 | 5 | 0 |
| runtime | society.vessels | 4 | 7 | 0 |
| runtime | world.body | 6 | 0 | 0 |
| runtime | experiments.port | 2 | 3 | 0 |
| runtime | economy | 1 | 1 | 0 |
| society.arms | mind | 11 | 2 | 0 |
| society.arms | society.vessels | 8 | 2 | 0 |
| society.arms | world.laws | 1 | 4 | 0 |
| society.arms | act | 5 | 0 | 0 |
| society.arms | world.facts | 0 | 5 | 0 |
| society.arms | world.body | 1 | 0 | 0 |
| society.arms | world.ledger | 1 | 0 | 0 |
| society.vessels | world.facts | 1 | 0 | 0 |
| society.vessels | world.model | 0 | 0 | 1 |
| society.vessels | mind | 0 | 1 | 0 |
| validation.static | world.ledger | 4 | 2 | 0 |
| validation.static | runtime | 1 | 0 | 0 |
| world.body | world.facts | 0 | 1 | 0 |
| world.laws | world.model | 5 | 1 | 25 |
| world.laws | world.facts | 9 | 2 | 0 |
| world.laws | act | 11 | 0 | 0 |
| world.laws | world.ledger | 7 | 0 | 0 |
| world.laws | world.body | 3 | 0 | 0 |
| world.model | mind | 1 | 0 | 0 |

### 4-4 循環

| 単位 | 頭の import だけ | 関数の中を含む |
|---|---|---|
| 今の木のモジュール | 1 組(`llm`・`llm.fleet`・`llm.mock`) | 9 組(最大 16 本) |
| 割った後のモジュール | 7 組(各 2 本) | 14 組(最大 17 本) |
| 割った後の包み | 2 組(act・world・mind と runtime・experiments) | 2 組(society・act・world・economy・mind と runtime・experiments) |
| 割った後の副包み | 1 組(world.model・mind) | 1 組(society.vessels・world.model・mind) |
| 例外 T1〜T8 を除いた副包み | 0 | 0 |
| 例外 T1〜T8 を除いた包み | なし | 2 組(economy・act・world と runtime・experiments) |

- 例外を除いて包みの単位に残る 2 組は、原因が 1 か所ずつです。`world.laws → act → world.model` と `act → economy → world.facts` で 1 組、`experiments.drive → runtime → experiments.port` で 1 組です。副包みなら一方向です。
- 割った後のモジュールの 7 組は、割り方の定数の置き場から出ます。全部同じ包みの中です。割るときに定数を下ろして解きます。

| 組 | 原因の名前 |
|---|---|
| `foundation/journal`・`foundation/vocab/events` | `SIGNBOARD_CAUSE` が `Process` を読む。定数の組を `tools/record` に戻すか、型を先に置く |
| `act/ops/move`・`act/ops/rail` | `_apply_engine_step` が `_enter_board_queue` を呼ぶ |
| `act/apply`・`act/ops/talk` | 表 `_APPLY` と `_UNADDRESSABLE` |
| `world/laws/presence`・`world/laws/presence_plan` | `DERIVE_RULES` を下へ |
| `runtime/run`・`runtime/result` | `RunResult` と `DIAG_RUN_COLUMNS` |
| `interfaces/cli/main`・`interfaces/cli/wire_economy` | 互いの補助 |
| `mind/percept/notice`・`world/model/percept_scene` | 例外 T2・T6 |

### 4-5 原則に反する辺は 35 本

**例外 T1〜T8(`ignore_imports` に載せる 8 本・頭の import 5・関数の中 3)**

| 番号 | 辺 | 読む名前 | 消し方 |
|---|---|---|---|
| T1 | `mind.percept.draw → world.model.percept_scene` | `PerceptionAssets`・`_TickCache`・`_scene`・`_time_view` | 静的資産の型を `foundation.ports` へ。描く側は `Percept` と資産だけを受ける |
| T2 | `mind.percept.notice → world.model.percept_scene` | `_signage_poi` | 看板の POI を引数で受ける |
| T3 | `mind.system1.change_detect → world.model.scene_hash` | `b4_block_raw`・`b4_block_hashes` | 世界が「変わったセル」を口へ出す |
| T4 | `mind.judge.decision.layer → economy.stage2_bind` | `PAYMENT_NOTE`・`WITHDRAW_WORD`・`atm_open_cells` | ATM の場所を知覚へ。語を語彙へ |
| T5 | `mind.relations.layer → world.model.proximity` | `notice_p` | 口で受ける |
| T6 | `world.model.percept_scene → mind.percept.notice` | `_signage_seen` | 注入で受ける(`memory_recall`・`heard_fn` と同じ形)か、9-1 の 2 段で心の側が絞る |
| T7 | `mind.judge.decision.layer → society.vessels.tools.registry` | `affordance_words` | 周りが示すできることを知覚の事実へ(R-134 §4) |
| T8 | `society.vessels.speech.layer → mind.memory.wom` | `hear` | 組み立てで渡す |

**腕の束ね 20 本(契約は通るが「society は器と計器だけ」に反する)**

| 辺 | 本数 | 中身 |
|---|---:|---|
| `society.arms → mind` | 13 | `calendar2.layer`・`calendar3.layer`・`calendar_self`・`contact.layer`・`contact.book`・`duties.layer` が本人の判断(`*_port`)・予定の帳面・注意・習慣を読む |
| `society.arms → world.laws` | 5 | `rows_of_day`・`FLAG_ARRIVED`・`PlanBlocks`・`RESTOCK_STEP_MINUTES` ほか |
| `society.arms → world.body` | 1 | `loud_sound_notice`・`noise_stage_at` |
| `society.arms → world.ledger` | 1 | `DeviationVocab` |

**注釈だけ 7 本(`if TYPE_CHECKING:` へ移せば消える)**

`mind.ops → world.model.agent_table`・`mind.ops → world.model.state`・`mind.percept.draw → world.model.agent_table`・`mind.percept.draw → world.model.state`・`mind.system1.change_detect → world.model.agent_table`・`mind.system1.change_detect → world.model.state`・`society.vessels.norm_meter → world.model.agent_table`

原則の「foundation は何も読まない」「build はランで読まれない」「validation の封印はランの側から読めない」に反する辺は 0 本です(封印の部品は今 src にありません)。

### 4-6 import に出ない違反

import の辺には出ないものを、列の読み書きで数えました。読み手の包みは割った後の置き場で数えています。

| 読み手 \ 列の持ち主 | world(35 列+cells・pois・知覚の列) | act(12 列) | economy(2 列) | mind(33 列) |
|---|---:|---:|---:|---:|
| world | 164 | 20 | 3 | 0 |
| mind | 50 | 3 | 1 | 124 |
| act | 226 | 55 | 9 | 8 |
| economy | 2 | 0 | 0 | 0 |
| society | 75 | 7 | 0 | 0 |
| runtime | 33 | 2 | 5 | 2 |
| experiments | 1 | 0 | 0 | 0 |
| validation | 1 | 0 | 0 | 0 |
| interfaces | 2 | 0 | 0 | 0 |

| 書き手 \ 列の持ち主 | world | act | economy | mind |
|---|---:|---:|---:|---:|
| world | 24 | 8 | 0 | 8 |
| mind | 1 | 0 | 0 | 28 |
| act | 236 | 73 | 6 | 11 |
| economy・society・runtime ほか | 0 | 0 | 0 | 0 |

- `mind` が自分の外の列を読むのは 54 か所です(§5-1)。
- 表に無い foundation の 1 か所は `Registry.kind`(文字列)で、列ではありませんでした。
- `runtime` は 13 本で 42 か所を読み、書きは 0 か所です。
- `act` の economy の列への書きは 6 か所です。`money` の 3 か所は台帳の無いランの `else` の枝(購入・食事・運賃)で、金の基本操作を通っていません。2 か所は初期値で、1 か所は `holdings`(所持品の個数)です。
- `act` が mind の列を書くのは 11 か所で、焦点の列 9 か所と `hunger_stage` 2 か所です。`mind.ops` が world を書くのは `apply_detection` の `cells.b4_hash` の 1 か所です。
- `world` の 40 か所は全部 `AgentState`・`World` の組み立ての初期値です。

### 4-7 割らずに移すだけなら

割る 23 本を既定の割り先へ丸ごと置いた場合の模擬です(`agents/state.py` は foundation の語彙の側に丸ごと置いた形)。新モジュール 322 本、包みをまたぐ辺 662 本(頭 507・関数の中 145・注釈だけ 10)、原則に反する辺 47 本(頭 32・関数の中 14・注釈だけ 1)です。内訳は `mind → act` 7・`mind → world.model` 5・`society.arms → mind` 13・`act → runtime` 3・`mind → runtime` 2 ほかです。割ると `mind → act` は 0、`act → runtime` は 0 になります。

## 5. 3 点の答え

### 5-1 35 万体の状態を 1 つの表で全層に渡している今、「mind は world の中身を直接読まない」をどう守るか

答えは、import の検査のほかに 3 段を重ね、表を物理的に割るのは v3 の時にする案です。

今の実測です。`agents` の 82 列を持ち主で分けると、world 35・act 12・economy 2・mind 33 です。mind の包みに入るファイルが自分の外の列を読むのは 54 か所・19 列・11 本です。

| ファイル | か所 | 読む列 |
|---|---:|---|
| `mind/judge/classical.py` | 22 | `cell` 6・`activity` 4・`poi_ref` 3・`hunger` 3・`transit_state` 2・`sex` 2・`age` 2 |
| `mind/memory/memory.py` | 11 | `poi_ref` 4・`cell` 3・`last_result_tick`・`last_action`・`last_result`・`queue_poi` |
| `mind/relations/layer.py` | 7 | `cell` 5・`xy` 2(相手の位置) |
| `mind/judge/store_choice.py` | 4 | `cell`・`pois.price`・`money`・`hunger` |
| `mind/system1/change_detect.py` | 2 | `cell`・`cells.density_stage` |
| `mind/memory/memory_store.py` | 2 | `kind`・`cell` |
| `mind/percept/notice.py` | 2 | `pois.open_from`・`pois.open_to` |
| `familiarity`・`relations/people`・`wom`・`decision/layer` | 各 1 | `cell` |

守り方は次の 4 段です。

| 段 | 何で守るか | 何が分かるか | 時期 |
|---|---|---|---|
| ① import の契約 | §3 の契約 3。mind は foundation だけを読む。表のクラスは注釈だけ | 他の包みのコードに触れない | 移動と同時 |
| ② 列の持ち主の検査 | 状態台帳の SoA の行に `owner` の欄を足す。`state_ledger_ast` の読み手の表を使い「mind の読む列=mind の列+口の列の一覧」を試験で固定する。今の 54 か所を一覧に載せ、減らす方向にだけ動かす | どの列を読んだか | 移動の後すぐ(結果は動かない) |
| ③ 読み取り専用の口 | 組み立てで `AgentState` を丸ごと渡さず、列の部分集合だけを持つ口の物を渡す。`.registry` も `arrays` も持たせない。列は読み取り専用の配列のまま(複製なし) | 実行時に一覧の外の列を読めば `AttributeError` | 移動の後 |
| ④ 揺らし試験 | 口の外の世界の列、または見えないはずの他人の行を揺らし、判断と final が動かないことを確かめる(`tests/engine/test_state_ledger_10b.py` の揺らし試験と同じ形) | 他人の行を読んだか | v3 の段の検収 |

口は 2 つの形にします【見立て】。

- `Percept`(今の `perception/facts.py`)は 1 人・1 起床ぶんの事実です。LLM と判断モデルへ渡します。
- 新しい `SenseBatch`(読み取り専用の配列の束)は System 1 が配列のまま見張るための口です。35 万体に比例するのは配列の中身だけで、物の数は 1 つです。作るのは起動時に 1 回で、刻みごとの費用は増えません【推測・未計測】。

④ が要る理由は、配列は全員分なので、他人の行を添字で読むことを型では止められないからです。②③ で分かるのは列の名までで、行は分かりません。これが今の形の限界です。

v3 の核で、表を持ち主ごとの 4 つの `Registry`(world・act・economy・mind)に割ります。同じ番号の体を指す形です。ハッシュの順を変えないために、並びは状態台帳の表から作ります【見立て】。

19 列の行き先は次の案です【見立て】。

| 読みの種類 | 列 | 行き先 |
|---|---|---|
| 本人の体と居場所 | `cell`・`hunger`・`activity`・`poi_ref`・`queue_poi`・`transit_state`・`money` | 口の列(本人の行だけ読む約束) |
| 本人の行為の結果 | `last_action`・`last_result`・`last_result_tick` | `Percept.wake`(今もある) |
| 本人の属性 | `age`・`sex`・`kind` | 9-1 の追加 1 のとおり本人の自己理解として心の側へ写す。世界に残すのは見た目の欄 |
| 他人の位置 | `cell`・`xy` | `Percept.seen_people` |
| 店と街 | `pois.price`・`pois.open_from`・`pois.open_to`・`cells.density_stage` | 知覚か本人の知識から。店の値段を全員が読める今の形は覗き見 |

### 5-2 世界の過程・心の欄・経済の書きを誰が行うか(「世界を書けるのは act だけ」の範囲)

答えは「世界の列を書く関数を持つのは act だけ。呼ぶのは act の外でもよい」です。

| 書くもの | 書き手(関数の置き場) | 呼び手 | 原因の印 | 今の書き | 動かす量 |
|---|---|---|---|---|---|
| 判断の結果 | `act.apply`・`act.ops.*` | runtime の系 | `LlmCall` | `apply` | 割るだけ |
| 世界の法則(鉄道・体の時間・天気・混雑・補充のつなぎ・開閉のつなぎ) | `act.ops.law_writes`・`rail`・`body_writes`・`shop`・`plan_writes` | `world.laws`(11 辺)・`society.arms`(5 辺)・系 `sys_body` | `Process`(法則)か宣言つきのつなぎ | `R.restock` など 19 口 | 移すだけ。呼び方は今のまま |
| 世界の法則が持つ自分の状態(列車・待ち行列の予約ほか) | 各法則のオブジェクト | 各法則 | 状態台帳の外の状態の行 | runner 18 行・presence 5 行ほか | 変えない |
| 心の欄(記憶・親しみ・店の評価・関係・不応期) | `mind.ops` | mind | 本人だけ(CP1 の D) | `write_memory` など 10 口 | resolve から出す |
| 実行中の行為の欄(意図・活動・直前の結果) | `act.ops.intent_writes`・`act.apply` | act | 行為の鎖の一部 | `set_intent` など | 割るだけ |
| 金 | `economy.ops.transfer` 1 か所 | `Ledger` の口を通して act と economy | `Process`・`LlmCall` | 台帳のあるランは 1 か所(試験あり)。台帳の無いランの枝に直接の書きが 3 か所 | 世帯の現金の配列の持ち主を economy にし、枝を消す |
| 物 | `economy.goods.move_goods` | 同じ | 同じ | 今も 1 か所 | 変えない |
| 権利 | `world.facts.rights` の `grant`・`revoke` | 組み立てだけ(今)。将来は act | CP1 の C | 今も 2 口 | 置き場だけ |
| 組み立てと再開 | `act.ops.init_writes`・`runtime.state.restore` | runtime | 初期状態 | `initialize`・`restore_soa` | 再開だけは全部の列を書く例外として宣言 |

理由は 4 つです。

1. R-134 の差分の器は、行為を基本操作の列にし、原因を持たせて当てます。法則の書きも同じ口を通せば、「過程が原因の差分は旗のある欄を書けない」(R-134 §5-5)を検査できます。
2. 今でも `writable()` の呼び手は resolve だけです。形を保つのが一番動かす量が少なくすみます。
3. CLAUDE.md §3 の「まだ人の行動で作れない変化はエンジン規則でつなぐ」のカバー率を、呼び手の数として測れます。
4. 逆に法則に自分で書かせると、書きの門が 2 つになり `systems/allow.py` の閉包と AST の検査を 2 重に持つことになります。

代わりに包みの単位で `world ⇄ act` の循環ができます。`world.laws > act > world.model` の層で解きます(§8 の異論 1)。v3 で「店の欄の差分」の型が入ったら、法則は差分を返す形に寄せ、`world.laws → act` の 11 辺を減らせます【見立て】。

経済は「世界」に含めるかの線引きになります。9-1 では金は心の外なので世界の側です。書き手の実体は保存則のために economy の 1 関数のまま置き、呼ぶ道を act の基本操作(R-134 §1-2 の `money.transfer`)とします。給料のような日の締めの書きは economy の過程が呼びます。これは act を通らない例外です(§8 の異論 2)。

### 5-3 関係と約束を、客観の事実(world)・器(society)・本人の理解(mind)のどこに置くか

3 か所は重複ではなく別の物です。判定の問いは次の 3 つです【見立て】。

1. 本人が忘れても残り、ほかの人が確かめられるか。はいなら world です。
2. 人と人の間で受け渡す形や手順の入れ物で、中身の判断を持たないか。はいなら society です。
3. 本人が忘れると無くなり、人ごとに食い違ってよいか。はいなら mind です。

| もの | 今の置き場 | 案 | 理由 |
|---|---|---|---|
| 世帯・職場・学校の所属 | `relations.initial_edges` の材料(W16・W17) | `world.facts.initial_ties` | 構築した事実 |
| 雇用・所有・賃借・許可 | `rights/ledger.py` | `world.facts.rights` | 9-1 の外。A2 の旗も同じ「誰が権利を持つかの事実」 |
| 「A が B に 18 時と言った」という発話 | `events/log.py` | `foundation.journal`(置き場)・世界の客観の記録(意味) | 起きたことの記録。本人は見聞きした分しか読めない(迷い 8) |
| 今の会話のセッション | `conversation.py` | `society.vessels.conversation` | 受け渡しの器 |
| メッセージの配達・電話・未読 | `contact/deliver.py`・`calls.py`・`chat_state.py` | `society.arms.contact`(v3 で vessels) | 運ぶ器。中身の判断を持たない |
| グループの一覧 | `tools/groups.py` | `society.vessels.tools.groups` | 成員の事実と入れ物 |
| 手元の連絡帳 | `contact/book.py` | `society.arms.contact.book`(v3 で world の持ち物) | 本人が忘れても端末に残る物。今の表は関係の層から作る仮の形 |
| 雇い主のシフトの知らせ | `calendar3/roster.py` | `society.arms.calendar3.roster` | 雇い主の口のつなぎ |
| 関係の記憶(`rel_*`・人の行) | `relations.py`・`relations_people.py` | `mind.relations` | 本人の経験の和。人ごとに非対称 |
| 個人への印象・内面の推測・一般化した印象(9-1 の追加 3) | 未実装(`memory_impression.py` は器) | `mind.relations` | 主観 |
| 約束 | `calendar2/book.py`(CA3 が「各自が自分の理解を持つ・共有の 1 行にしない」と決めている) | `mind.plan.promise_book` | 本人の理解。相手の行と食い違ってよい |
| 頭の中の予定の思い出し | `calendar2/recall.py` | `mind.plan.head_recall` | 記憶と同じ式 |
| 破られたかの判定 | 層の計器 | 本人の判定は mind。計器は `foundation.journal` を読む `society` か `validation` | 破られたと思うかは本人の理解 |

決まりは 3 つです。

- **器は約束を持ちません。** 持つのは運んだ言葉の出来事と届いた事実だけです。
- **world から mind への写しは始めの 1 回だけです。** 世帯と職場の辺は組み立てで記憶の初期値へ入れます。その後 mind は world を読まず、知覚からだけ更新します。今の `rel_kind` は客観の種別の写しで、始めは一致します。
- **`rel_*` の列を読む側は mind の口を通します。** `initial_edges` の入力の型と `REL_*` の定数は `foundation.vocab.relations` へ下ろします(42 行)。

## 6. path の文字列と直し方

### 6-1 先に塞ぐ穴(型の名がハッシュに入っている)

`engine/state_hashes.py` の `_qual` は `型.__module__ + "." + 型.__qualname__` をハッシュのバイトへ流します(enum・dataclass・値のクラス)。300 体・120 刻みの mock で確かめました。

| 条件 | final |
|---|---|
| そのまま | `ca1c761a…` |
| `_qual` の返す名に接頭辞を足す(移動と同じ変化) | `9d7fd317…` |
| 接頭辞を足し、許可の表 `VALUE_CLASSES` を足さない | ランが `TypeError: O42 arbiter.queue: to_state: 直列化の書き手が無い型 …` で止まる |

このランで流れた型は `core.types.EventClass`・`engine.arbiter.WakeCandidates`・`engine.scheduler.DeferralQueue`・`perception.p_notice.EventBudget`・`perception.p_notice.Counters` の 5 つです(腕を立てたランでは増えます【推測】)。

つまり、ファイルを動かすと final が動きます。同じ名前を持つ場所はほかにもあります。

- `engine/state_codec.py` の `qualname` と `ALLOWED_CLASSES` 17 行・`CLASS_FIELDS` 2 行。状態のファイルの中身です。`importlib.import_module` で組み立て直すので、古い状態のファイルが読めなくなります。
- `engine/resume.py` の `_canon` の `<module.qualname>`。設定の指紋に入ります。
- `engine/state_hashes.py` の `VALUE_CLASSES` 4 行。
- `tests` の dotted の文字列(`shibuya.engine.conversation.PendingInvite` など)。

**直し方**: 移動の前の段で、`runtime/state/class_ids.py` のような固定の表(クラス → 今の名前の文字列)を入れ、`_qual`・`qualname`・`_canon` がその表を引く形にします。名前は今の文字列のまま凍結します。古い状態のファイルの読み込みも表で解きます。この段だけで byte-check 19 構成を通してから、ファイルを動かします。

### 6-2 変えてはいけない文字列

見た目はモジュールの名ですが、中身は ID です。置換でまとめて直すと結果が動きます。

| 種類 | 数 | 例 | 扱い |
|---|---:|---|---|
| 乱数の領域の名 | 8 | `engine.processes.rail`・`engine.processes.environment`・`engine.chooser`・`perception.attention.p_see`・`perception.p_notice`・`llm.mock`・`llm.mock.move_target`・`llm.mock.out_of_cell_target`(`world.*`・`economy.*` の領域も同じ扱い) | 変えない。変えると乱数の列が変わる |
| 版の ID | 70 か所・46 本 | `shibuya.engine.batching/1`・`shibuya.perception/percept/2`・`shibuya.engine.resume/state/v2` | 変えない。manifest と状態のファイルに出る |
| ハッシュの見出し | 1 | `b"shibuya.engine.state_hashes/full/v1"` | 変えない |

機械の置換はこれらの一覧を除外にします。試験で文字列を凍結します(`tests/engine/time/manifest_keys_frozen.json` と同じ形)。

### 6-3 path を文字列で持つ場所の数

コードの文字列定数だけを数えました(docstring とコメントは別)。

| 場所 | 数 | 働き | 直し方 |
|---|---:|---|---|
| `engine/state_ledger.py` の `OWNER_CLASSES` 76・`OWNER_ALT_CLASSES` 6・`_ALLOW_*` 9 | 91 | 機能する(クラスの属性の網羅・読み手の許可) | 対応表で機械で直す。割るファイルは `contains` の文字列を含む新しいファイルを AST で探す |
| 同じファイルの `basis`(`_SOA` 105・`_EXT` 174) | 279 | 文(`a08109a` の時点の `path:line` の記録)。試験は空でないことだけを見る | 直さない。当時の記録の印を見出しに書く |
| `engine/state_ledger_ast.py` の `DECL_FILES` 3・`UNRESOLVED_ALLOW` 7・`RESULT_FILES` 3・`GENERIC_FILES` 5・`DIAG_EXITS` 14・`EXT_AST_ALLOW` 18・関数の中 1 | 51 | 機能する | 対応表で機械で直す。検査 4 が「当たらない許可」を落とすので漏れは試験で分かる |
| `engine/rng_audit.py` の表 | 43 | 機能する(path・関数・領域) | path だけ直す。領域の名は変えない |
| `engine/systems/allow.py` の `base / "engine" / "resolve.py"`・`static_check.py` の `RESOLVE_MODULE`・接頭辞 `shibuya.engine.systems.` | 5 | 機能する(起動時に AST で読む) | ファイルの一覧を読む形へ書き直す(`RESOLVE_FILES`)。関数の名が衝突しないことを試験で見る |
| `engine/state_codec.py`・`state_hashes.py` の dotted | 23 | §6-1 | 固定の表 |
| `world/processes/absent.py` 14・`inputs.py` 11・`body/rules.py` 2・`bridging/scan.py` 1・`events/log.py` 1・`defect_fixes_1103.py` 1・`cli.py` 1 | 31 | 宣言の文・根拠の文【見立て・試験は確かめていない】 | 機械で直すか、当時の記録と書く |
| `Path(__file__).resolve().parents[N]` | src 14 行(ほかに `here = Path(__file__)` 4 行) | 機能する(`docs/`・`data/` への道) | `foundation/paths.py` の `repo_root()` 1 本に集める。深さが変わるので全部直す |
| `tests/` の path の文字列 | 205(50 本) | AST の検査・読み手の表 | 対応表で直す |
| `tests/` の `src/shibuya` の文字列 | 25(25 本) | 同じ | 変えない(ディレクトリは同じ) |
| `tests/` の `/ "engine" / "x.py"` の形 | 98(32 本) | 同じ | 対応表で直す |
| `tests/` の dotted の文字列 | 130(39 本) | 同じ | 対応表で直す。ID は除く |
| `tests/` の import の文 | 2,556(394 本) | import | 機械で書き換える |
| `tools/` の path・結合・dotted | 6・4・6 | 同じ | 対応表で直す |
| `tools/` の import の文 | 97(33 本) | import | 機械で書き換える |
| `tools/` の非 Python(`night5070/experiments.json` の `-m shibuya.cli` など) | path 59・dotted 17(3 本) | 文字列の引数 | `shibuya/cli.py` の入口を残せば多くは不要 |
| `pyproject.toml` | 34 | 契約と `package-data` の `shibuya.manifest` | §3 の契約へ差し替える |
| `.github/workflows/ci.yml` | 0 | `lint-imports` を呼ぶだけ | 不要 |
| `docs/` | 273 本が `engine/resolve.py` か `src/shibuya/` に触れる | 記録 | 直さない(当時の記録)。索引に旧と新の対応表を 1 枚置く |
| 系の表の `O39:conv.sessions` などの道筋 | なし | 属性の道筋でファイルに依らない | 変えない |

### 6-4 順【見立て】

1. 固定の表を入れる(§6-1)。byte-check 19 構成。
2. `repo_root()` へ集める。allow の一覧の形にする。byte-check。
3. 旧と新の対応表(TOML 1 本)を作り、`tools/` に移動の道具を置く。道具は AST で import を書き換え、path の表を直す。ID の一覧は除外する。
4. ファイルを動かす(割らない 221 本。build の 79 本は動かない)。古い場所の口は残さない(10-13b §0-6)。`shibuya/cli.py` だけ外との約束として残す。byte-check。
5. 語彙と型を下ろす割りをする(agents/state・commit の定数・attention・fleet の型など)。byte-check。
6. resolve を割る。byte-check。
7. renderer を割る(迷い 16)。byte-check。
8. tests の置き場を変える。

## 7. 迷いの一覧

| # | 触れる原則 | 迷い | 候補と帰結 | 案 |
|---:|---|---|---|---|
| 1 | 世界を書けるのは act だけ | 法則の書き | (a) act の関数を法則が呼ぶ=書きの門 1 つ・包みの循環 1 組・11 辺 (b) 法則が自分で書く=循環なし・門が 2 つ・AST の検査が 2 重 (c) 法則は差分を返す=きれいだが全 19 口の書き直しで v3 の範囲 | (a) で移し v3 で (c) へ寄せる |
| 2 | mind は world を読まない | `AgentState` の置き場 | (a) `world/model` =注釈だけ 3 本 (b) `runtime` =act・world.laws から上向きの辺 18 本(注釈を含む) (c) foundation =契約では読めてしまい検査が効かない | (a) |
| 3 | society は器と計器だけ | 腕の束ね 7,490 行 | (a) `society.arms` と名を分けて v3 まで置く=違反 20 本を宣言 (b) 12 番目の包み `arms` =原則の文は守れる・包みが増える (c) 今割る=仕様の決まっていない腕の設計を先に決めることになる | (a) か (b)。ユーザーの判断 |
| 4 | 世界 / 心 | `presence` | (a) world.laws(11-03 の指示書のまま) (b) 予定だけ mind へ今割る=`PlanBlocks` が状態のファイルの許可の表に載る (c) v3 で 3 つに割る | (a) のあと (c) |
| 5 | 9-1 の外 / society は器 | 権利・規則の表・暦 | (a) `world.facts`=economy が読むのを許す契約が要る (b) society =economy → society の辺 6 本・act の検査の段 6 が society を読む (c) 規則の表だけ foundation | (a) |
| 6 | 9-1 の内と外 | 意図・活動・焦点の列 | 意図と活動(12 列のうち 6): act の実行の状態か、mind の目標か。焦点は 9-1 の注意 | 意図と活動は act・`Percept.intent` で心へ見せる。焦点は mind の持ち物で、今は act が 9 か所書く(v3 で直す) |
| 7 | 行為の鎖・9-2 | 言葉を読む部品(`parser`・`undefined`・`intents_from_responses`) | (a) act.intake=器の入口(R-134 段 0〜1)・行為の鎖を 1 か所で持てる (b) mind =本人の言葉の解釈。mind が world を読むことになる(`_poi_in_cell` など) (c) runtime | (a)。9-2 で再検討 |
| 8 | mind は world を読まない | 出来事の記録の置き場 | (a) foundation=全層が書ける・mind が記録全体を読めてしまう (b) world =mind が書けなくなる(`memory_store` が id を使う) (c) 書きの口と読みの口を分ける | (a) に「mind は `find`・`positions` を呼ばない」AST の検査を足す。今の mind の使い方は `EventId` と定数だけ |
| 9 | foundation は何も読まない | 語彙と文の雛形 | (a) foundation=原則の文は守る・11,579 行に太る (b) `mind.percept.templates`=world と act と build が mind を読むことになる (c) 語彙の 12 番目の包み | (a)。§8 の異論 4 |
| 10 | 9-3c | `p_notice`・`attention`・B4 の指紋 | `p_notice` は world.model(届いたか)。`p_see` は mind(気づくか)。今の式は 9-3c で作り直す前の物 | この案で移し、9-3c の段で割り直す |
| 11 | runtime / interfaces | 推論のクライアント | (a) `runtime/inference`=9-1「推論は runtime の口が束ねる」・辺が素直 (b) `interfaces`=外への口の章に合う・runtime → interfaces の上向きの辺が 3 本 | (a) |
| 12 | 封印 | 封印を読む部品の置き場 | (a) tools に置いたまま=import の契約の外・今でも shibuya からは import できない (b) `validation/sealed`=契約で守れる・tools からの import が増える | (a) で AST の検査を足し、本物の読み手を確かめてから (b) |
| 13 | validation | 経済の計器(`census`・`checks`) | (a) economy=保存則のゲートはランの中で動く (b) validation =economy → validation の上向き | (a) |
| 14 | runtime は中身に触らない | 系の中身 | (a) `runtime/systems` に置いて v3 で細らせる=列の読み 42 か所を宣言 (b) 持ち主へ今移す=`Box` の型を下へ下ろす大きな手術 | (a) |
| 15 | なし | 試験の置き場 | (a) src の後=`parents[N]` 133 行を別の段で直す (b) 同時=差分が読めなくなる | (a) |
| 16 | 1 バイト不変 | 割る時期 | (a) 移すだけの段と割る段を分ける=途中は違反 47 本 (b) 同時=一度に差分が大きい。`Renderer` のクラスを割るのは移動より危ない | (a)。`Renderer` は最後 |

## 8. 原則への異論

1. **`world` を 1 つの包みとして書くと循環します。** 「世界を書けるのは act だけ」と「世界の過程は world」を同時に守ると `world.laws → act → world.model` になり、包みの単位で循環します。副包みで解けますが、原則の文には現れません。文を「世界の状態(`world`)」「世界の法則(`laws`)」に分けるか、副包みの層を原則に書くのがよいと考えます。
2. **「世界を書けるのは act だけ」は文を直したほうが正確です。** 実際の形は「世界の列を書く関数は act にしかない。呼ぶのは法則でもよい」です。さらに、金と物の書き手の実体は保存則のために economy にあり、給料日の書きは act を通りません。提案の文は「世界の列を書く関数は act だけが持ち、金と物は economy の基本操作だけが書く」です。
3. **「society は器と計器だけ」に腕 7,490 行の行き場がありません。** カレンダー 2・3・1b・連絡・店の仕事の層は、本人の判断と体の実行を束ねています。器でも心でも act でもありません。v3 で割るまでの置き場として、原則に一時の例外を書くか、12 番目の包みを足すのがよいと考えます。
4. **「foundation は何も読まない」は import の話に限って成り立ちます。** 模擬で foundation から外への辺は 0 本でした。ただ、語彙・口の型・文の雛形・出来事の記録が入り、意味のある物が半分を超えます【見立て】。また `core/budget.py` は `docs/` の表を、`bridging/ledger.py` は JSON を読みます。`foundation`(意味なし)と `contracts`(語彙と口の型)に割る案は検討に値します。
5. **「runtime は中身に触らない」は全部には言えません。** 組み立ては中身を全部 import します。模擬で runtime の 43 本のうち 18 本が中身の包みを読み、147 辺です。多いのは `systems/assemble` 60・`result` 24・`run` 22 です。残りの 25 本は 0 辺です。そこで「中核(時計・進行役・系の宣言)は中身を読まない。組み立てと結果は読む」と 2 つに分ければ、契約に書けます。
6. **「validation の封印はランの側から読めない」は import では守れません。** ファイルは path で開けます。実例として、ランの側の `engine/energy.py` は `ANCHORS_VALIDATION_PATH` の定数を持ちます(今は読まず、試験が確かめています)。守りは `tools/instruments/read_guard.py` の形です。ランの包みのコードに封印の語(`data/jinryu`・`_validation_anchors`・`odpt_rt`)の文字列を置かない AST の検査と、ランを `sealed_only` で包む試験を足すのがよいと考えます。今の該当は `energy.py` の 2 か所(docstring と定数)と `world/processes/inputs.py` の宣言の文 1 か所です。

## 9. 既存の実装の比較

Web は使わず、リポの答申に載っている範囲だけです。答申の等級は各答申のとおりで、本書では読み直していません。

| 先例 | 分け方 | 書きの口 | 読みの宣言 | この案との対応 | 出典 |
|---|---|---|---|---|---|
| Bevy | 系の引数の型で読み書きを宣言する | `Commands` で構造の変化を溜めて同期点で当てる | 同じ部品への読みと書きを並べると実行時にエラー(B0001) | 系の宣言 `reads`・`writes`(今もある)・`writable` の窓 | R-113 §10・§11、R-134 §1-1 |
| Unity Entities 1.3 | 系を群に入れ順を宣言。既定の群は初期化・シミュレーション・表示の 3 つ | なし | — | 系の表 `SYSTEMS`。包みの分け方の資料は無い | R-113 §11 |
| UE Mass | 表現・シミュレーション・複製の LOD を別に持つ。Actor との写しの向きを型で宣言 | 特性ごとに写しの向き | 断片の要求を宣言 | world と心の間の「写しの向き」(§5-3 の始めの 1 回の写し) | R-140 §4、R-113 |
| UE Smart Objects | 物は実行の論理を持たない。活動の集まりと予約だけ | 体の側が実行 | tag と範囲で探す | 器は判断を持たない(society.vessels) | R-134 §4 |
| SpatialOS | 1 つの entity の component に authority を持つ worker は 1 つ | 持ち主だけが書く | interest は問い合わせで書く | 列の持ち主の欄(§5-1) | R-138 §4 |
| EVE Online | Proxy・SOL・DB の 3 層。星系ごとのノード | SOL | なし | 規模の話で、コードの層は別 | R-138 §2 |
| ACT-R | モジュールとバッファ。手続きはバッファの塊にだけ触れる | 要求を出す | バッファ経由 | mind は口の型だけを読む | R-135 §b-1 |
| PIANO(Project Sid) | 状態を持たない関数のモジュールが共有の Agent State を読み書きする | 各モジュール | 書かれていない | 今の 1 つの表に近い。口の無い形 | R-135 §c-3(R-41 §4-2) |
| Concordia | GM の `EventResolution` が試みの出来事を解く | GM | 観察者に配る | act の差分の器(GM の役)。Concordia は LLM、案はコード | R-134 §9・R-124 |
| TigerBeetle | 残高は transfer でしか変わらない | transfer | なし | `economy.ops.transfer` | R-113 §10 |
| Datomic | 純関数の取引関数を事前に入れる | 取引の直列の pipeline | なし | 判例の雛形(ランの中で育たない) | R-134 §1-1 |
| AI Town | 記憶の行は本人の視点の文 | なし | — | mind の本人の理解(§5-3) | R-113 |

似た大きさのシミュレーションの**パッケージの分け方そのもの**は答申に載っていません。MATSim・SUMO・Repast・MASON・Mesa・AgentSociety・OASIS は時間と同期や検証の話で引かれているだけです(R-133・R-117)。この節の対応づけと 11 の包みへの当てはめは未リサーチ(expedient)です。

## 10. 読めなかったこと・限界

- `data/` は開いていません。封印の層の値も開いていません。封印の語は `src`・`tools` の `.py` の文字列を数えただけです。
- 関数の本体を全部は読んでいません。割り先は関数の名・docstring・使う名前の AST で決め、中心の部品の一部だけ本文を読みました。
- 模擬の辺は名前の使用を追ったものです。引数で渡された物の属性の読み(ダックタイピング)は辺に出ません。
- メソッド単位で割ったのは `Renderer` だけです。`PlanExecutor`・`LLMBridge`・`RunResult` などはクラスのまま数えました。
- 列の読み書きの数は `state_ledger_ast` の strict に近い AST です。配列を渡した先の読み・局所の別名・`field("x")` の形は入っていません。実際はもっと多いです【推測】。
- 実物のファイルを動かして試験を回していません。ハッシュの実測は mock の 1 構成(300 体・120 刻み)で、byte-check 19 構成は回していません。
- `tools/c7` などの封印の候補は語の数だけで、本当に開くかは読んでいません。
- 同じ時間に増えている未追跡のファイル(`docs/design/spec/`・`docs/research/` の新しい答申)は読んでいません。
