# R-55 自前コードの読み取り: checkpoint の中身・乱数・Python 側の状態・再開の現状(D-102 と決定論の方針の材料)

- 日付 2026-09-28 / 読み役 Opus 5.5 / **推奨は書かない**(コードの事実だけ。解釈が混ざる箇所は「未検証」と明記)
- **親検収 済(第281)**: 主張 5 件(`run.py:2426-2436` の Checkpoint はハッシュ 5 本・`core/soa.py:382-399` は `_decls` 全列を混ぜ `mechanism` で除外しない・`salient.py:160,308`/`civic.py:116,132` の `self.rng` が状態を持つ・`change_detect.py:294-299` の `_prev_raw is None` で全セル変化扱い+`b4_hash` は `resolve.py:723` が書くだけ・`run.py:1737` `for tick in range(ticks)`+`schema.py:394-397` の `parent_run` は欄だけ)を親が同じ行を印字して一致。`save_registry` の呼び手が engine に無いことも grep で一致。設計への写し先=[再開と決定論の設計書](../design/v2-resume-determinism-draft.md) §4。
- 対象 commit `31645d87646f9dab63dd5a431c99494a2dc440a8`(branch `design/memory-net-draft`・作業木 clean)
- 読んだファイル: `engine/run.py`・`engine/activity.py`・`engine/arbiter.py`・`engine/scheduler.py`・`engine/change_detect.py`・`engine/conversation.py`・`engine/llm_bridge.py`・`engine/tape.py`・`engine/presence.py`(抜粋)・`engine/geometry.py`(抜粋)・`engine/commit.py`(抜粋)・`engine/resolve.py`(抜粋)・`engine/ledger_api.py`・`engine/processes/{runner,salient,civic,rail,crowd,environment,goods_flow,logistics}.py`(抜粋)・`core/{rng,hashing,soa,serialize}.py`・`agents/{state,population}.py`・`world/state.py`・`perception/{state,renderer,attention,p_notice}.py`(抜粋)・`economy/{ledger,goods}.py`(抜粋)・`llm/{fleet,mock,undefined}.py`(抜粋)・`manifest/schema.py`・`cli.py`(抜粋)・`tools/c7/seed_exchangeability.py`・`tools/c6/t6_bit_reproduce.py`(冒頭)・`tests/engine/test_determinism_t1_t2_t4.py`・`tests/c6/test_t3_parallel_invariance.py`・`docs/ops/v2-server-lessons.md` §5・§11・`docs/research/v2-r48-own-code-memory-range-return.md`・`docs/bench/c7/ensemble/c7-day-4_seeds1-3*.{md,json}`
- パスは `src/shibuya/` を省略(`tests/`・`tools/`・`docs/` はそのまま)。実行して確かめた箇所は [実行確認] と書く(`.venv` の Python・numpy 2.5.3・little-endian)。

---

## §1 checkpoint の中身

| 欄 | 何を混ぜているか | 根拠 |
|---|---|---|
| `Checkpoint` 全体 | `tick` と 5 本のハッシュ文字列だけ。**状態そのもの(配列)は書かない** | `engine/run.py:259-280` |
| `combined` | `blake3("\x1f".join([agents, world, population, schedule] (+ activity が空でなければ)))` | `engine/run.py:276-280` `parts = [self.agents_hash, self.world_hash, self.population_hash, self.schedule_hash]` |
| 取る時点 | tick 末(Phase C・会話・活動層・診断行のあと)。`checkpoint_every`(既定 360)ごと+最終 tick=1 日 4 点 | `engine/run.py:2426-2436`・`:1162` |
| `agents_hash` | `Registry.state_hash`: 見出し(版文字列・`kind`・個体数)+**宣言順の全列**について 名前・`dtype.str`・形・生バイト。**`mechanism` タグで除外しない**(`self._decls.values()` を全部回す) | `agents/state.py:580-582` → `core/soa.py:382-399` `for d in self._decls.values(): … h.update(flat.view(np.uint8) …)` |
| `world_hash` | `blake3(cells.state_hash ‖ 0x1f ‖ pois.state_hash)`。cells 5 列・pois 9 列(§2)。遅延キャッシュ `_eatery_mask` 等は SoA でない=入らない | `world/state.py:349-353`・`:136-143` |
| `population_hash` | W16 母集団の同定ハッシュ(ラン中は不変) | `engine/run.py:1039`・`:2431`・`agents/population.py:175-184` |
| `schedule_hash` | W17 週次表の同定ハッシュ(週次表なしは `""`・ラン中は不変) | `engine/run.py:1667` |
| `activity_hash` | 活動層がある(v3+activity on)ランだけ。体順に「活動文の sha256」を連結+`until_kind.tobytes()` を sha256。intern 表(`text_id`/`_texts`)は入らない | `engine/activity.py:447-459`・`engine/run.py:2433` |

混ざらないもの(事実): 世界過程の Python 状態(§4)・経済台帳(`MoneyLedger.state_hash` は存在するが run から呼ばれない=`economy/ledger.py:792-801`・呼び出し元 grep は tests だけ)・知覚側 SoA `PerceptionState`(`perception/state.py:171-172` に `state_hash` はあるが run から呼ばれない)・会話・アービタ・変化検出・保留中の LLM 応答。

- 配列を保存する口 `core/serialize.save_registry` / `load_registry`(zstd(npz)+meta JSON・読込時に `state_hash` 一致を検査)は存在する(`core/serialize.py:143-261`)が、**呼び出し元は tests だけ**(`tests/engine/test_determinism_t1_t2_t4.py:81,112`・`tests/core/test_serialize.py`)。`engine/` からの呼び出しは 0 件。1 本の `Registry` 単位で、Python オブジェクトは対象外。
- CLI `--checkpoints-out` が書く JSON は `shibuya.cli/checkpoints/1`: `tick`・各ハッシュ・`combined`・`final_hash`・manifest 欄(`cli.py:346-374`・`:796-800`)。配列は含まない。

## §2 SoA 全列(挙動に効くか/診断・死蔵か)

判定の基準: `src/shibuya/{engine,perception,llm,economy}` を列名で grep し、**読んで分岐・計算・描画に使う箇所**があれば「挙動」。書くだけ/宣言だけは「読み手未検出」「死蔵」。M=mechanism=True / E=expedient(mechanism=False)。腕=その腕のランだけ確保。[実行確認] 既定 36 列 127 B/体、全腕 44 列 147 B/体。

**agents(`agents/state.py:375-499`)**

| 列 | dtype | B | タグ | 判定 | 読み手の例 |
|---|---|---|---|---|---|
| cell | i4 | 4 | M | 挙動 | change_detect・commit・resolve・renderer ほか 15 ファイル |
| node | i4 | 4 | M | 挙動 | resolve(移動) |
| band | i1 | 1 | M | 読み手未検出 | 書くだけ `resolve.py:448,1026,1052,2268` |
| xy | f4×2 | 8 | M | 挙動 | geometry・crowd・salient(p_notice)・renderer |
| path_next_node / target_node | i4 | 4+4 | M | 挙動 | resolve・commit・crowd |
| edge_id / edge_s(腕 edge) | i4/f4 | 4+4 | M | 挙動 | resolve |
| focus_target(腕 attention) | i4 | 4 | M | 挙動 | commit・resolve・renderer |
| focus_ttl(腕 attention) | u1 | 1 | E | 挙動 | `resolve.py:1344-1351`(寿命で焦点を落とす) |
| kind | i1 | 1 | M | 挙動 | renderer・resolve・過程 |
| age / sex | u1/i1 | 1+1 | M | 読み手未検出 | 初期化で書くだけ `resolve.py:454-457` |
| hunger / fatigue / thermal | u1 | 3 | M | 挙動 | resolve・change_detect・bridge |
| hunger_stage / fatigue_stage / thermal_stage | i1 | 3 | **E** | **挙動**(起床条件) | `engine/change_detect.py:77-80` `("hunger", "hunger_stage")` を文字列で引く |
| money | i4 | 4 | M | 挙動 | resolve・ledger(世帯現金=この配列そのもの) |
| holdings | u1 | 1 | E | 挙動 | `resolve.py:2158-2163`(消費)・`renderer.py:1334`(手) |
| activity | i1 | 1 | M | 挙動 | 多数 |
| plan_cursor | i2 | 2 | M | **死蔵** | 宣言以外の参照 0 件(grep `src/`・`tools/`) |
| talk_partner | i4 | 4 | M | 読み手未検出 | 書くだけ `resolve.py:1913,1933,1991,2000` |
| invocation_distance | u2 | 2 | E | **死蔵** | 宣言以外の参照 0 件 |
| transit_state / transit_ref | i1/i4 | 1+4 | M | 挙動 | rail・presence・resolve `:1647` |
| board_line | i1 | 1 | M | 挙動 | resolve |
| board_since | i4 | 4 | **E** | **挙動** | `resolve.py:1403,1538,1555,1577`(FIFO と打ち切り) |
| sleep_pending | i1 | 1 | M | 挙動 | `resolve.py:712,961,1129` |
| poi_ref / poi_since / queue_poi / queue_since | i4 | 16 | **E** | **挙動** | `processes/crowd.py:231,242,250-254`・presence |
| plan_activity(腕 plan) | i1 | 1 | M | 読み手未検出 | 書くだけ `resolve.py:546-548` |
| plan_flags(腕 plan) | i1 | 1 | M | 挙動 | `presence.py:1283-1287` |
| activity_until / activity_kind(腕 activity) | i4/i1 | 4+1 | M | 挙動 | `engine/activity.py` |
| refractory_until | i4×11 | 44 | M | 挙動 | `run.py` → `arbiter.step`(不応期) |
| wake_pending_class | i1 | 1 | M | **死蔵** | 初期値 −1 を書く `agents/state.py:505` 以外 0 件 |
| last_action / last_result / last_result_tick | i1/i1/i4 | 6 | M | 挙動 | bridge・renderer・`activity.py:292-293` |
| fail_streak | u1 | 1 | E | 読み手未検出 | 増減だけ `resolve.py:1008,1069,1081,2423,2468`(閾値比較 0 件) |

**world(`world/state.py:93-125`)** cells: density(i4・M・毎 tick `agents.cell` から再計算 `resolve.py:1030,1054`)/ density_stage(u1・E・同じく再計算・salient が読む `salient.py:484`)/ noise_stage(u1・E・動的上書き欄)/ open_count(i4・M・書くだけ `resolve.py:1058`=読み手未検出)/ b4_hash(u8・M・**書くだけ** `resolve.py:723`・読み手 0 件)。pois: cell・node・stock・price・revenue(M・挙動)/ capacity・open_from・open_to(E・挙動=commit・renderer)/ open_now(M・挙動=`world.open_mask`)。

**知覚側 `PerceptionState`**(salient 過程が私有・checkpoint 外)heading・task_flag(M・事象の直前に全体を書き直してから読む `salient.py:205-214`)/ last_b2_hash・last_b4_hash(M・**宣言以外の参照 0 件**)。

**腕でだけ確保する仕組み**: `AgentState(plan_columns, edge_columns, attention_columns, activity_columns)` の旗で `declare` 自体を呼ぶかを分ける(`agents/state.py:332-399`・`:466-481`)。旗は `run_day` が決める: edge=`geometry=="edge"`、attention=`edge かつ v2`、plan=`W16+W17 あり かつ plan_executor`、activity=`v3 かつ activity`(`engine/run.py:1422,1446,1453-1460`)。列の有無で `state_hash`(全宣言列を回す)が変わるため「既定の checkpoint を動かさない」ための形、と docstring が述べる(`agents/state.py:346-366`)。

## §3 乱数

- **鍵とカウンタ**: `derive_key(seed, domain)=blake3("i:<seed>" ‖ 0x1f ‖ domain)` 先頭 16 B → Philox4x64 の鍵、カウンタは最大 4 語(`core/rng.py:45-73`)。`stream(...)` は**呼ぶたびに新しい Generator** を返す(`core/rng.py:76-78`)=カウンタ型。状態が残るのは呼び出し側が Generator を持ち続けた場合だけ。
- **状態を持ち続ける Generator(2 本)**: `SalientProcess.rng = stream(seed, "world.salient", day_index)` を毎 tick `poisson`/`choice` で消費(`processes/salient.py:160`・`:308`・`:314`)。`PublicServiceDispatchProcess.rng = stream(seed, "world.public_service_dispatch", day_index)` を出動ごとに `lognormal`(`processes/civic.py:116`・`:132`)。どちらも checkpoint に入らない。
- **起動時に一度だけ引くもの**: `world.large_event`(`civic.py:441`)・`world.delivery_inbound`(`goods_flow.py:336`)・`world.road_works`(`logistics.py:291`)・`world.delivery_last_mile`(予約・引かない `logistics.py:125`)・`engine.processes.environment`(天気種別 counter 0 と実日 counter=blake3(層名) `environment.py:101-102,194-197`)・`engine.processes.rail`(`random_raw` `rail.py:364`)・`agent.schedule`(`agents/schedule.py:75,88`)・`w16.sample.*`(`agents/population.py:315,334`)・`wallet.initial`(`cli.py:191`)・`world.synthetic`(`world/assets.py:595`)。
- **呼ごと・その場で作って捨てるもの**(状態なし): `llm.mock`(tick, agent, wake_class+1)`llm/mock.py:141-147`/`conversation.invite`(tick, inviter)`engine/conversation.py:373`/`perception.attention.p_see`(tick, agent, poi)`perception/renderer.py:1184-1188`/`perception.p_notice`(event_id, tick)`perception/p_notice.py:478`。
- **Philox を引かない決定論**: 希望歩行速度=`derive_key` の鍵+splitmix64(`engine/geometry.py:148-162`)/ 出勤率=`_mix64(agent_id)` のみ・**seed も day_index も入らない**(`engine/presence.py:148-163,739`)。
- **blake3 キー(run_salt)**: `run_salt_for(seed)=blake3("i:<seed>" ‖ 0x1f ‖ "engine")[:16]`(`engine/run.py:253-256`)。用途タグ pk/ak/wk/wd(`core/hashing.py:63-67`)で、優先度キー(`engine/commit.py:408-410`)・適用順(`engine/run.py:1786-1787`)・起床タイブレーク(`engine/arbiter.py:433`)・「あたり」(`engine/activity.py:367-386`)。入力は (salt, tick, id…) で状態なし。整数は `<i8` 固定で詰める(`core/hashing.py:155`)。
- **xxhash**: B4 変化検出・prefix 鍵(`core/hashing.py:83-90`)・艦隊のデコード seed `seed_for(call_id, run_seed)=xxh64 & 0x7fffffff`(`llm/fleet.py:266-272`)。
- **カウンタに day_index が入っていない**: 呼ごとの流れと blake3 キーは日内 tick(0..ticks-1)だけを使う(上記の各行・`run_day` のループは `for tick in range(ticks)` `engine/run.py:1737`)。call_id も `f"{tick}:{a}:{cls}"`(`engine/run.py:2172`・`engine/llm_bridge.py:605`)。日単位の過程は day_index をカウンタに使う(salient・civic・goods_flow・logistics)。
- **OS 乱数・暗黙 seed**: `src/shibuya` で `np.random.default_rng` / `import random` / 組み込み `hash()` の使用は 0 件(grep。`default_rng` は tests の性質テストだけ=例 `tests/engine/test_arbiter.py:97`)。
- [実行確認] numpy 2.5.3 の Philox は `bit_generator.state` が dict(`bit_generator`・`state{counter,key}`・`buffer`・`buffer_pos`・`has_uint32`・`uinteger`)で、途中の state を新しい Generator に代入すると以後の引きが一致した(`stream(1,"world.salient",0)` で poisson 5 回後に保存→復元→10 回が一致)。

## §4 Python 側の状態(SoA の外)

「形」= tick 境界で取り出すときの型(ndarray=配列として出せる型 / 構造体=dict・list・dataclass で直列化の書き手が要る・現状その書き手は無い)。

| 状態 | 場所 | 形 | checkpoint | 挙動に効く根拠 |
|---|---|---|---|---|
| 活動文 `text`(list[str]・体数)+`until_kind` | `engine/activity.py:178-179` | 構造体+ndarray | **混ざる**(activity_hash) | `settle_events`・`cell_rows` |
| 活動の intern `text_id`/`_texts`/`_text_ids` | `engine/activity.py:181-183,305-307` | 派生 | 混ざらない | `cell_rows` は (−人数, 文) で並べ替え=id 順に依らない `:439-442` |
| 会話 `sessions`(Session dataclass)・`_of_agent`・`_refusal_until`・`pending_invites`・`_pair_invite_until`・`_speaker_invite_until`・`_next_id` | `engine/conversation.py:276-286` | 構造体 | 混ざらない | `wake_candidates` `:566-595`・ゲート |
| アービタの繰り延べ `_pending`(WakeCandidates 5 配列)・端数繰越 `_pool`(float)・`queue`(クラス別 list) | `engine/arbiter.py:533-545,556-566,585` | ndarray+float+構造体 | 混ざらない | 次 tick の裁定入力 |
| 適用待ち `pending`(10 要素 tuple の list)・`fleet_deferred`・`fleet_waiting`(set)・`replay_inbox`(dict)| `run_day` の局所変数 `engine/run.py:1610-1619,1708` | 構造体 | 混ざらない | `t_apply` で適用 |
| 変化検出の前回欄 `_prev_raw`(セル×4 int32) | `engine/change_detect.py:274,294-299` | ndarray | 混ざらない(`b4_hash` は世界に書かれるが読み手 0) | **None のとき全セルを「変化」扱い** `:294-296` |
| 変化検出の `_up/_dn/_hit/_b1..3` | `engine/change_detect.py:276-284` | 毎 tick 上書きの作業領域 | — | 状態ではない |
| 顕著行為 `rng`・`event_seen_tick`(体数 int32)・`budget`・`pstate`・`_cell_index_tick` 等 | `processes/salient.py:153-176` | Generator+ndarray | 混ざらない | `event_seen_tick` は通報の前提 `resolve.py:2013-2019` |
| 出動 `rng`・`pending`(到着予定 list) | `processes/civic.py:116-117,152-157` | Generator+構造体 | 混ざらない | 警察事象の発生 |
| ホテル `rooms_occupied`・`bed_cell`(体数) | `processes/civic.py:271-278,297,335` | ndarray | 混ざらない | 部屋の空き判定 |
| 大規模イベント `_inside` | `processes/civic.py:449,484` | ndarray | 混ざらない | 退場の対象 |
| 鉄道 `occupancy`(便ごと)・`peak_ratio`・`_return_queue`(dict→list[ndarray])・`_inbound` | `processes/rail.py:280-295,554-556,572-582,615` | ndarray+構造体 | 混ざらない | 乗車の受容(満員)`:554-556` |
| 混雑 `queue_action`(体数 int8) | `processes/crowd.py:184`・書き手 `resolve.py:2323-2327` | ndarray | 混ざらない | 列から席へ入れたときの完了の種類 |
| 混雑 `occupancy`・`queue_len`・`flow`・`coherence` | `processes/crowd.py:250-297` | 毎 tick SoA から再計算 | — | — |
| 物の流れ `backroom`・`_acted_today`・`waste_g_collected`・`_cursor`・`litter_g`(float64) | `processes/goods_flow.py:171-182,426-430,559-562` | ndarray+数値 | 混ざらない | 挙動への効きは本答申で未確認 |
| 物流 `delivered`・`_cum`・`blocked_cells`・`occupied_edges` | `processes/logistics.py:121-124,285-288` | ndarray+数値 | 混ざらない | 未確認 |
| 環境 `replay_date`・`stratum`(起動時)・`_shade` キャッシュ | `processes/environment.py:144-157,194-232` | 値+ndarray | 混ざらない | 実日→描画の日付 `run.py:1543-1544` |
| 計画実行層 `_defer_ids/_defer_deadline/_defer_line`・`_extra`・`_skip_depart_at`・`_pulled_in_today` | `engine/presence.py:695-703,1196-1273` | ndarray+構造体 | 混ざらない | 退出の繰り延べ・予約の突き合わせ |
| ActualLog(追記専用) | `processes/runner.py:185-189` | ndarray リング | 混ざらない | 読み手は遵守率・成長宣言だけ(`runner.py:438`・`run.py:2491`) |
| 金の台帳 `_lines`(店舗以下)・`_flow`・`_flow_daily`・`_snap/_snap0`・生ログリング・`_day` | `economy/ledger.py:222-269,712-741` | ndarray+構造体 | 混ざらない(世帯現金は SoA `money`) | 残高制約 |
| 物の台帳 `_shelf/_bin/_shelf_age/_sold_today/_household_sku …`・納品リング・`_day` | `economy/goods.py:355-394` | ndarray | 混ざらない | 棚在庫 |
| 未定義行動台帳 `log`(deque)・`counts`・`precedents`・`vocabulary_extension` | `llm/undefined.py:697-704` | 構造体 | 混ざらない | `precedents` は裁定器があるときだけ増える=`run_day` は裁定器なし(`llm/undefined.py:684`・`engine/llm_bridge.py:519-523`) |
| テープ書き手 `_rows`(4,096 行ごとに flush)・`_blocks`・`_writer` | `engine/tape.py:228-331` | 構造体+ファイル | — | blocks.parquet は `close()` でだけ書く `:322-331` |
| 艦隊 in-flight・結果キュー | `llm/fleet.py:975-991` | 外部スレッド/プロセス | — | 到着 tick が壁時計に依存 |
| レンダラのキャッシュ `_b1/_b2/_b3/_b4/_acq/_rank_cell`・tick キャッシュ | `perception/renderer.py:766-803` | 構造体 | — | メモ(純関数性は個別に検証していない) |
| 世界の遅延キャッシュ `_eatery_mask` 等 | `world/state.py:136-143` | ndarray/dict | — | 資産からの純関数 |

## §5 非決定性の源とテスト

- **numba**: engine の numba は `change_detect._cell_wake_numba`(`nogil`・逐次)1 本(`engine/change_detect.py:109`)。`prange`/`parallel=True` は `build/geo/w3_distances.py:38,51`・`build/vis/w8_visibility.py:332,368,407,432`・`build/vis/w9_shadow.py:77,101` だけ=ランの外。engine に並列ループが無いことをテストが固定(`tests/c6/test_t3_parallel_invariance.py:49-60`)。
- **`np.add.at`**: engine の使用箇所(`arbiter.py:341-482`・`activity.py:309`・`presence.py:879-897`・`civic.py:339`・`crowd.py:219`・`rail.py:572,581`・`resolve.py:1758,1760,1849,2163`)は全て整数配列。浮動小数の `add.at` は見つからなかった。
- **浮動小数が入る状態**: `xy`(f4・ハッシュに入る。node 幾何は資産座標の写し `resolve.py:1029`、edge 幾何は f8 補間→f4 `geometry.py:392`)/ アービタの `_pool`(f8 の逐次加減 `arbiter.py:585-590`)と `cumsum(cost)` の比較(`+1e-9` `arbiter.py:461-466`)/ p_notice の確率(f8 の式と一様乱数の比較 `p_notice.py:470-479`)/ 路上ごみ `litter_g`(f8)。機械・BLAS/libm・SIMD 差でビットが変わるかは**未検証**。
- **並べ替え**: engine・perception・economy の `argsort` は全て `kind="stable"` か `np.lexsort`。既定(非安定)は `agents/population.py:364` の 1 か所(起動時の抽出)。アービタは入力順に依存しない純関数(`arbiter.py:28-31`・性質テスト `tests/engine/test_arbiter.py:96`)。応答の適用は `np.lexsort((ag, ak, ev_class, t_apply))`(`engine/run.py:1787`)。
- **dict/set**: dict は挿入順。`set[str]` は所属判定だけ(`engine/llm_bridge.py:551`)。過程は `PROCESS_ORDER` のタプル順で回す(`processes/runner.py:363-364`)。組み込み `hash()` 不使用(§3)=`PYTHONHASHSEED` に依る箇所は見つからなかった。
- **エンディアン**: `Registry.state_hash` は `dtype.str`(例 `<i4`)とネイティブのバイト列をそのまま混ぜる(`core/soa.py:394-397`)=ビッグエンディアン機では構造上別の値になる。`MoneyLedger.state_hash` も同形(`economy/ledger.py:797-799`)。行ハッシュは `<i8` 固定(`core/hashing.py:155`)。活動層は int8+UTF-8 で順序非依存。
- **スレッド・艦隊**: 艦隊は別スレッドの asyncio(`llm/fleet.py:981-983`)。`FleetBridge.poll` の順序は非決定と明記(`llm/fleet.py:1619-1624`)。`run_day` は到着した応答を `max(res.tick+δ, tick+1)` で積む=**到着 tick が壁時計に依存**(`engine/run.py:2004-2006`)。会話の発話は到着順に `conv.utterance` を呼ぶ(`engine/run.py:2013-2015`)。運用記録: 39 万体本番は繰り延べが時刻依存で同 seed 再ランが一致しない(D-54)・5,000 体・`fleet_wait_s 120`・繰り延べ 0 では bit 一致(`docs/ops/v2-server-lessons.md:98-101`)。
- **テープ再生で吸収される範囲**: 鍵は `(agent_id, tick, wake_class, prompt_hash)`(`engine/tape.py:438`)。版 2 は繰り延べ行と `observed_tick` を持ち(`engine/tape.py:18-33`)、再生側は `replay_inbox[observed_tick]` で「後で届く」を再現する(`engine/run.py:1965-1985,2124-2140`)。鍵に日付は入らない(tick は日内・プロンプト本文には `clock_fn` の日時が載る `perception/renderer.py:833`)。
- **決定論を検査している既存テスト**(抜粋): T1/T2 同 seed で全 checkpoint 一致 `tests/engine/test_determinism_t1_t2_t4.py:21`・別 seed で別 `:30`・T4 規模不変 `:58,69`・npz 往復でハッシュ保持 `:87,108` / T3 スレッド 1 vs 8(slow)`tests/c6/test_t3_parallel_invariance.py:64,81,89` / numba=NumPy 版の一致 `tests/engine/test_change_detect_p6.py:87` / テープ再生の bit 一致 `tests/engine/test_tape_wiring.py:145,188,213`・繰り延べテープ `tests/engine/test_tape_deferred.py:119,152,222` / 過程込み同 seed 一致 `tests/engine/test_processes_run.py:72,137,301` / 記録済み checkpoint の再現 `tests/engine/test_presence_executor.py:220,244` / 活動層込み `tests/engine/test_two_layer_activity.py:250` / 台帳込み `tests/engine/test_ledger_wiring.py:96` / CLI の checkpoints JSON 決定論 `tests/test_cli.py:174` / T6 LLM 層 bit 再現は「一致しなければ主張しない」と記録する作り `tools/c6/t6_bit_reproduce.py:1-8`・`tests/c6/test_c6lib_aggregate.py:178`。**途中再開と通しの一致(resume==straight)を検査するテストは無い**(grep `resume` のヒットは W17 生成と `tests/c8/test_ensemble.py:84` のラン表の鍵だけ)。

## §6 再開の現状

- **`run_day` は 1 日を 0 から作る**: シグネチャに前の状態を受ける引数・開始 tick の引数は無い(`engine/run.py:1151-1206`)。本体で `AgentState`(`:1454`)・`R.initialize`(`:1468`)・会話(`:1432`)・変化検出(`:1621`)・アービタ(`:1640`)・世界過程・計画実行層を毎回生成し、`for tick in range(ticks)`(`:1737`)。R-48 の既出事実「**日をまたいで状態を持ち越す経路は見つからなかった**(=翌日のランは空腹 2、所持金は初期値から始まる)」(`docs/research/v2-r48-own-code-memory-range-return.md:107`)と一致。
- **`parent_run`**: `manifest/schema.py:394-397` の `Lineage` にあるだけ。他の参照 0 件(grep `src`・`tools`・`tests`)。`docs/ops/v2-server-lessons.md:189` も「再開の口が無い」と記す。
- `engine/scheduler.Scheduler` は `start_tick` を持つ(`engine/scheduler.py:183-201`)が src 内で生成されていない(grep)。
- **ラン終端で捨てるもの**: 最終 tick 以降に `t_apply` がある `pending`、アービタの `_pending`、艦隊の未応答(`fleet_unanswered_at_end` として数えるだけ・コメントは「次ランへ持ち越すの監査点」`engine/run.py:2456-2458`)。
- **tick 内の順序**(切るならどこか、の材料): 体の時間経過 `advance_body`(`tick % 30`・`resolve.py:821-831`)→ 世界過程 → 計画実行層 → 知覚の前計算 → ① 応答の適用 → ② 変化検出 → 計画境界 → 会話・顕著行為の起床 → ④′ 艦隊の到着 → ③ アービタ → ④ 呼 → ⑤⑥⑦ → 会話の招待と終了 → 活動層 → 診断行 → 在圏 journal → checkpoint(`engine/run.py:1737-2436`)。
- **日の締め**(ループの後): 艦隊の吸い切り(`:2440-2459`)→ `bridge.close()`(テープを閉じる `:2478`)→ `runner.end_of_day(ticks-1)`=`rail.step(ticks)` と ActualLog の退避(`processes/runner.py:371-376`・`run.py:2485`)→ `ledger.end_of_day(day_index)`(`:2511`)→ 日次センサス(`:2518`)→ 月次 T3(`:2525`)→ `census_out` 書き出し(`:2532`)→ 在圏 journal を一括保存(`:2707`)。日次内省は「就寝で発火を記録するだけ」(`resolve.py:39,2049-2076`)。

**v1 の 5 型(`docs/ops/v2-server-lessons.md:194-203`)に対応する v2 の該当箇所**

| v1 の型 | v2 で該当するコード(事実) |
|---|---|
| 未保存の状態 | checkpoint はハッシュのみ(§1)。§4 の「混ざらない」行はどれもファイルに出る経路が無い |
| 再開で二重に発火 | ① 状態を持つ Generator 2 本は day_index カウンタの先頭から始まる(`salient.py:160`・`civic.py:116`)=作り直すと同じ列を先頭から引く ② 変化検出は `_prev_raw is None` の tick に全セル変化扱い(`change_detect.py:294-296`)③ `end_of_day` が `rail.step(ticks)` を撃つ(`runner.py:371-375`)④ 呼ごとの流れにも call_id にも day_index が無い(§3) |
| キャッシュ消失で結果が変わる | `_prev_raw`(挙動に効く)・アービタ `_pool`・レンダラのメモ・vLLM の prefix キャッシュ(`cache_salt` `llm/fleet.py:244-265,1062-1063`) |
| 途中 flush で未走査区間 | テープは 4,096 行ごと flush・blocks は close 時だけ(`tape.py:228,262-268,322-331`)。在圏 journal・センサスはラン終端で一括 |
| 日次締めの二重 | `MoneyLedger.on_day_end` は同じ `day` の二度呼びを拒否しない(`_flow_daily.append`・`_day = d+1` `ledger.py:712-741`)。`LedgerBundle.end_of_day`・`GoodsLedger.on_day_end` も同様に検査なし(`ledger_api.py:270-282`・`goods.py:842-`)。正常終了の印・再開拒否の印は無い(再開の口が無い) |

## §7 salt(seed)の使われ方

- **seed が入る先**(`run_day` 内): 合成世界(`World.synthetic(seed)` `run.py:1428`)・mock LLM(`:1429`)・`run_salt`(`:1430`)・会話(`:1432`)・mock 日課(`:1433`)・母集団の読み込みと二層抽出(`load_population(seed)`・`sample_population(seed)` `:959-970`)・世界過程一式(`WorldProcessRunner(seed=…)`)・レンダラ(p_see・p_notice)・edge 幾何の希望速度・CLI の初期財布(`cli.py:191`)・艦隊のデコード seed(`run_seed=args.seed` `run.py:2783`)。`cache_salt` は `(mode, run_id)` から(`llm/fleet.py:244-265`)で seed ではない。
- **seed に依らないもの**: W17 週次表(ファイル読み込み)・出勤率の欠席(`_mix64(agent_id)`)・実資産の世界(`world_dir`)。
- **seed に依るが「世界」側のもの**: 天気種別と再生実日(`environment.py:194-197`)→ 描画の日付(`run.py:1543-1544`)。
- **母集団**: `pop.n > n_agents` のときだけ `sample_population(seed)` が走る(`run.py:969-970`)。**R-31 検査の事実**: `tools/c7/seed_exchangeability.py` は `population_hash`/`schedule_hash`/`world_hash`/`agents_hash` の seed 間同一性を「報告」し、許容差分は `seed`・`run_id`・`final_hash`・`fleet.cache_salt`・`fleet.run_id`(`:1-16`・`:29-35`)。c7-day-4(390,067 体・seed 1/2/3)の結果は PASS、**母集団・日課のハッシュは 3 seed で同一、world/agents は全 checkpoint で別**(`docs/bench/c7/ensemble/c7-day-4_seeds1-3.md:4`・同 JSON `hash_identity`)。この規模では抽出が走らない条件(体数=母集団)である点は上の行のとおり。

## まとめ表

| 問い | 答え(事実) | 根拠 |
|---|---|---|
| checkpoint は状態を保存するか | しない。ハッシュ 5 本と tick だけ | `engine/run.py:259-280,2426-2436` |
| agents_hash は診断列も混ぜるか | 混ぜる(宣言順の全列・タグで除外しない)。死蔵 3 列(plan_cursor・invocation_distance・wake_pending_class)も入る | `core/soa.py:382-399`・§2 |
| world_hash の範囲 | cells 5 列+pois 9 列のみ。過程・台帳・キャッシュは外 | `world/state.py:349-353` |
| 「挙動に関わる状態」は全部 SoA にあるか | 無い。会話・アービタ・変化検出の前回欄・保留応答・鉄道の乗車数・混雑の queue_action・ホテル・計画実行層の繰り延べ・台帳が Python 側 | §4 |
| 乱数は状態を持つか | 基本はカウンタ型。例外 2 本(salient・dispatch の `self.rng`) | `core/rng.py:76-78`・`salient.py:160`・`civic.py:116` |
| Generator の状態は取り出せるか | numpy 2.5.3 で dict として取り出し・戻しでき、以後の引きが一致 | [実行確認] §3 |
| 同 seed 同結果(同機・mock/テープ)を検査しているか | T1/T2・過程込み・テープ再生で検査済み | §5 テスト一覧 |
| スレッド数依存 | engine に並列ループ無し(テストで固定)・T3 は 1 vs 8 スレッドの別プロセスで比較 | `tests/c6/test_t3_parallel_invariance.py:49-77` |
| 艦隊の非決定 | 到着 tick が壁時計依存・poll 順非決定。テープ版 2 の再生で吸収 | `run.py:2004-2006`・`fleet.py:1619-1624`・`tape.py:18-33` |
| 途中 tick から再開する入口 | 無い(`start_tick` 引数なし・`parent_run` は欄だけ) | `run.py:1151-1206,1737`・`manifest/schema.py:394-397` |
| 日次締めの二重防止 | 検査なし | `economy/ledger.py:712-741` |
| resume==straight のテスト | 無い | §5 末尾 |

## 見つからなかったもの(探した場所)

- `run_day` の外で複数日を回して状態を持ち越す経路(`cli.py`・`engine/run.py`・`tools/` の `run_day(` 呼び出し。R-48 と同じ結論)。
- checkpoint から状態を読み戻して `run_day` を続ける口(`engine/`・`cli.py` の grep `load_registry|resume|start_tick|restore`)。
- Python 側状態(§4)の直列化コード(`to_dict`/pickle/npz 書き出し。grep で engine 内 0 件)。
- `band`・`age`・`sex`・`talk_partner`・`plan_activity`・`fail_streak`・`open_count`・`b4_hash`・`last_b2_hash`・`last_b4_hash` を読んで分岐する箇所(`engine`・`perception`・`llm`・`economy` の grep。別名経由の読みは `r.`/`a.` の 1 文字別名まで確認)。
- 浮動小数の `np.add.at`・非安定ソートの engine 内使用・組み込み `hash()`・OS 乱数。
- 物の流れ・物流・街路清掃の Python 状態(`backroom`・`litter_g`・`blocked_cells` 等)が行動分岐に効く箇所は**確認していない**(未確認=見つからなかった、ではない)。
- 機械・BLAS・SIMD をまたぐ浮動小数のビット一致を調べた記録(docs・tests)。
