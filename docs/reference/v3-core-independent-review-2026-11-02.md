# v3 の核の独立の読み(R-130・R-133 の突き合わせ)

- 作成 2026-11-02・リサーチ役(Opus 5.5)。土台: `<読み手の複製の場所(親が伏せた=リポに絶対パスを書かない規則)>` の HEAD `90258ef`(origin/build/spatial-d102-prep)。
- 読んだだけ。コード・文書・data は変えていない(`git status` は空)。pytest は回していない。Web は使っていない。子エージェントは起動していない。
- 場所は `path:行`(`src/shibuya/` は省いて `engine/…` と書く)。推測は【推測】、筆者の組み立ては【見立て】と書く。
- 数値の出どころは、R-130 が残した生データ `docs/bench/analysis/v3-2026-11/a/raw/n5000_t60_h0.json`・`n5000_ts1_h0.json`・`n5000_ts1_h0.summary.txt`(以下 raw)。`data/` の中は開いていない。
- 手順: 先にコードを読んで §1〜§4 の骨子を書き、その後で R-130・R-133・棚卸し(09-30)を読んで §5 を書いた。

## §0 要旨

1. 今の核は「60 秒ごとの刻みの事象が自分で次の刻みを予約する」形で、器は事象の列でも、中身は時間駆動のまま。既定のランで列に入る事象は刻みの事象 1 種だけ(§1)。
2. R-133 §0-1 の「すでに事象の列で動いている」は器についてだけ正しい。起床・返事の適用・在圏・鉄道はどれも刻みごとの走査で、`engine/scheduler.py` の起床の列は既定のランでは使われていない(§1・§5)。
3. 刻みの番号への依存は 4 群とも広い。乱数の鍵は `run_tick_key` のほかに、刻みの番号をそのまま入れる口が 10 か所以上ある。呼びの id・テープの鍵・状態のファイルの見出しも刻みの番号で持つ(§2)。
4. M1 は「器だけ」なら byte-check を 1 バイトも動かさずに始められる見込み。ただし R-133 の v3-0 が束ねている「呼びの id と乱数の鍵を世界の時刻に」「列を状態に入れる」は、そのままでは byte-check の比べる値を動かす【見立て】(§3)。
5. 1 秒刻みで事象が膨らんだ第 1 の原因は、W17 の在圏ブロックと鉄道の時刻表が「分」のまま刻みの番号として使われていること。世界の 0〜1 時を 1 秒刻みで回したランは、1 日ぶんの計画と時刻表を最初の 1,440 秒に詰めて実行していた(§4)。
6. 第 2 は、歩く体を刻みごとに 1 歩ずつ進める作り(意図と歩く体の数が刻みの数に比例する)。第 3 は、不応期などの刻みの数の定数。L4 の予算は、このランでは上限に当たっていないので原因ではない(§4)。
7. R-130 の「夜の 1 時間でも呼が 551 倍」は読み違いで、比べた 2 本のランは中身の違う仕事を回している(§5)。

## §1 進行役と列の実態

### 1-1 事象駆動になっている所

| 所 | 事実 |
|---|---|
| `engine/systems/conductor.py:169` | 窓の待ち行列 `WindowQueue` を作る(幅は腕 `_BA.arm()`・既定 60 秒) |
| `engine/systems/conductor.py:191-195` | 刻みの事象の処理の関数 `on_step` は、まず次の刻みの事象を `t_ns + step_ns` に予約する(自分で次を張る形) |
| `engine/systems/conductor.py:208`・`:212` | 種類 `KIND_STEP` を置き、最初の刻みの事象を `t_begin × step_ns` に予約する |
| `engine/systems/conductor.py:214-221` | ループは「窓の頭が終わりに届くまで `run_window`」。窓の数ぶん回る |
| `engine/batching.py:356-411` | 窓の中は時刻 → 体 → 種類の順位 → 予約の番号で並べ(`:344`)、処理の中の予約は同じ窓で続けて回す(`:401-405`) |
| `engine/batching.py:211-212` | 待ち行列の中身は `Scheduler`(バケットの輪+heapq)を流用。地平は 2 刻みぶん(`:83`) |
| `engine/events/log.py:395-452` | 出来事の記録の id は `(t_ns, seq)`。時刻はすでにナノ秒 |
| 腕だけ | 会話の時計(`conductor.py:182-189`)・連絡の道具 c1(`:209-210`)・区域ごとの時計(`:179-181`・`:219-221`)は、刻みの外の時刻の事象を同じ列に置く。既定のランでは立たない |

### 1-2 刻み駆動のままの所

| 所 | 事実 |
|---|---|
| `engine/systems/conductor.py:196-206` | 刻みの事象 1 つの中身は、表の系(刻みの中 25+腕)を全部、決まった順に呼ぶ。`TickCtx.of(T, tpd, step_s)` が刻みの番号 T から時刻を作る(`engine/systems/boxes.py:87-91`) |
| `engine/systems/conductor.py:126-129` | 呼ぶ系は `timing == "tick"` の全部(表 `engine/systems/table.py:107-466`) |
| `engine/batching.py:64`・`:192-193` | 窓の幅は定数 `STEP_SECONDS`(60)の約数だけで、刻みの幅がその倍数でないと `ValueError`。刻みの幅を 1 秒にすると既定の幅 60 では作れない |
| `engine/presence.py:1278-1280`・`:1376-1394` | 計画実行層の到着・退出・就寝・起床は、日の頭に配列で組み、`_ev_start = searchsorted(…, arange(ticks+1))` で刻みごとに切り出す。列ではなく「刻みの番号で引く表」 |
| `engine/presence.py:1123-1137`・`:1240` | その表の時刻は W17 の分(`start_min`)と便の `enter_tick`。docstring も「層のイベント列は日の中の分」と書く(`:654`) |
| `engine/processes/rail.py:351`・`:392`・`:770`・`:807` | 発車の時刻は時刻表の分 `tt_departure_min` をそのまま `dep_tick` に入れ、毎刻み `enter_tick == t`・`dep_tick == t - 1` を全便で比べる |
| `engine/processes/runner.py:460-466` | 世界過程は毎刻み全部の `step(tick)` を呼ぶ |
| `engine/systems/llm_io.py:140-145` | 艦隊の返事の適用時刻 `t_apply = res.tick + delta_think_ticks(lane, tick_seconds)`=刻みの番号。下限は `floor = tick`(`:157-159`) |
| `engine/llm_bridge.py:181-197` | `delta_think_ticks` は秒を刻みへ切り上げる(L1 の 2.6 秒も 1 刻み) |
| `engine/run.py:1974-1976`・`engine/systems/judge.py:95-96` | 保留の返事は Python の list で、毎刻み全件を `p[0] <= tick` で分ける |
| `engine/systems/judge.py:372-398`・`:56-59` | 起床候補は毎刻み 6 つの源から作り直し、毎刻みアービタにかける |
| `engine/arbiter.py:394-405` | 不応期は体 × 条件の「次に起きてよい刻み」と毎刻み比べる |
| `engine/systems/perceive.py:73` | 変化の検出は毎刻み全員とセルを見る |
| `engine/scheduler.py:434-451` | 起床の列の `due`・`order_indices` は、src の中に呼び手が無い(grep の結果。`.due(` の呼び手は energy・press・civic の別の物)。`Scheduler` の実際の使い手は窓の待ち行列(`engine/batching.py:211`)と体の層の腕 reserve(`engine/body/schedule.py:279`・既定は sweep=`:64`)だけ |

### 1-3 判定

- 器は事象の列で、時刻も窓もナノ秒で持つ。窓の幅を 1 秒にしても既定の結果は同じだった(raw の `n5000_t60_h0_bw1.json` は呼 69・診断の列も `n5000_t60_h0.json` と同じ。R-130 §3 の final 一致の記載とも合う)。
- 中身は時間駆動。列にあるのは刻みの事象 1 つで、その処理が全系・全員を刻みごとに回す。在圏・鉄道・返事の適用・起床・不応期は、どれも「刻みの番号で引く表か、毎刻みの全件比べ」。
- R-133 §0-1 は「器はある」という意味なら正確。「動いている」と読むと言い過ぎになる。列を「世界の時刻の事象で埋めていく」前に、在圏と鉄道の表の単位(分)をそろえる仕事がある(§4)。

## §2 刻みの番号への依存の棚卸し

grep の型: `tick`・`STEP_SECONDS`・`STEPS_PER_`・`NS_PER_STEP`・`_TICKS`・`per_tick`・`run_tick_key`・`MINUTES_PER_DAY`・`minutes_per_tick`。src の件数(行): `tick_seconds` 312・`MINUTES_PER_DAY` 219・`per_tick` 133・`_TICKS\b` 116・`STEP_SECONDS` 28・`NS_PER_STEP` 26・`STEPS_PER_` 30・`run_tick_key` 19。

### 2-1 (a) 定数

| 群 | 名前と値 | 所 | 1 秒刻みで |
|---|---|---|---|
| 不応期 | `REFRACTORY_MINUTES` 0/360/150/60/15/45/10/15/5/5/30。名前は分だが刻みとして使う | `agents/state.py:306-318`・`engine/resolve.py:262`・`:827`・`engine/systems/build.py:616` | 60 分の 1 |
| 起床の昇格 | `T_MAX_TICKS` 3/10/30/60 | `engine/arbiter.py:107-112`・`:425-429` | 60 分の 1 |
| L4 | `_TICKS_PER_DAY = STEPS_PER_DAY`・`call_budget_per_tick`・`POOL_CAP_TICKS` 2.0 | `engine/arbiter.py:118`・`:127`・`:137-151`・`engine/systems/build.py:1026` | 1 日の量が 60 倍(ただし CLI の既定は上限なし=`cli.py:110`・`:526-527`) |
| 会話 | `REFUSAL_MEMORY_TICKS` 60・`SILENCE_TICKS` 5・`MAX_SESSION_TICKS` 60・`PENDING_INVITE_TTL_TICKS` 3・`PAIR_INVITE_REFRACTORY_TICKS` 60・`SPEAKER_INVITE_REFRACTORY_TICKS` 30。1 番=1 刻み | `engine/conversation.py:90-110`・`:608-637` | 60 分の 1 |
| 在席・列 | `DWELL_MAX_TICKS` 30・`WAIT_MAX_TICKS` 15 | `engine/processes/crowd.py:96`・`:98` | 60 分の 1 |
| 意図・歩き | `INTENT_MAX_TICKS` 60・`EXIT_WALK_MAX_TICKS` 60・`RETURN_MIN_AWAY_MIN` 60(刻みに足す) | `engine/intent.py:99`・`engine/presence.py:135`・`:142`・`:1861` | 60 分の 1 |
| 注意・通報・乗車 | `FOCUS_TTL_TICKS` 10・`REPORT_WINDOW_TICKS` 5・`BOARD_WAIT_LIMIT_TICKS` 30 | `engine/resolve.py:209`・`:244-245` | 60 分の 1 |
| 鉄道 | `DWELL_TICKS` 1・`DWELL_TICKS_TERMINAL` 2・発車=時刻表の分 | `engine/processes/rail.py:130`・`:135`・`:351`・`:392` | 停車は 60 分の 1・発車の時刻は 60 倍早まる |
| 体 | `BODY_TICK_PERIOD` 30・`ACTIVITY_REST_PERIOD_TICKS` 10 | `engine/body/rules.py:53`・`:58`・`:177` | 疲れの進みが 60 倍 |
| 世界過程 | `LITTER_G_PER_PERSON_TICK` 0.05・`CELLS_PER_SWEEP_TICK` 8・`MAX_EVENTS_PER_TICK` 200 | `engine/processes/goods_flow.py:124`・`:128`・`perception/p_notice.py:112` | 60 倍 |
| 時と日の換算 | `STEPS_PER_HOUR` で時を出す・`% STEPS_PER_DAY` で日の中の分 | `engine/systems/decide.py:213`・`engine/systems/judge.py:47`・`engine/presence.py:1919-1935`・`world/state.py:394` | 時の札がずれる |
| 窓・輪 | `DEFAULT_WIDTH_S`・`WIDTHS_S`・`HORIZON_STEPS` 2・`HORIZON_TICKS = STEPS_PER_DAY` | `engine/batching.py:62-64`・`:83`・`engine/scheduler.py:80` | 窓は作れない(§1-2) |
| 既定 60 の引数 | `tick_start_ns(tick, tick_seconds=60)` を幅を渡さずに呼ぶ | `engine/commit.py:467-469`・`:637` | 歩く体の意図の時刻が 60 倍になる |
| 秒・分に直してある所(参考) | 活動の「まで」・energy・古典・記憶・関係・店の記憶・歩速(nav1)・環境の過程の時刻 | `engine/activity.py:177`・`:213`・`engine/classical.py:346`・`engine/store_choice.py:64-72` ほか | 変わらない |

### 2-2 (b) 乱数の鍵

| 鍵 | 所 | 刻みの番号の入り方 |
|---|---|---|
| `run_tick_key(day_key0, T, 幅)` | `core/rng.py:116-127`。呼び手 `engine/processes/salient.py:335`・`civic.py:194`・`engine/decision/port.py:313`・`engine/proximity.py:262` | 刻みの番号 T。`time_key_from_t_ns` が同じ値を `t_ns` から作れる(`core/rng.py:130-144`)が、呼び手は無い |
| `step_key(ctx.step)` | `engine/contact/port.py:225`・`:235`・`:262`・`engine/calendar2/port.py:195`・`engine/calendar3/port.py:164`・`engine/duties/port.py:157` | 腕だけ。刻みの番号 |
| 生の tick を counter に | `engine/classical.py:630`・`engine/chooser.py:269`・`engine/conversation.py:386`・`llm/mock.py:8`・`:172`・`perception/p_notice.py:477` | `stream(seed, 領域, tick, …)` |
| blake3 の割り | `core/hashing.py:119`・`:128`・`:137`・`:181-207`。使う所 `engine/arbiter.py:439`(起床の同順)・`engine/systems/judge.py:102`(返事の適用の順)・`engine/commit.py:887` | `tick` と `t_apply`(刻み)をハッシュの材料に入れる |
| 艦隊の復号の seed | `llm/fleet.py:267-273` | `xxh64(call_id, run_seed)`=呼びの id 経由で刻みの番号 |

### 2-3 (c) 呼びの id・テープの鍵・出来事の記録

| 物 | 所 | 形 |
|---|---|---|
| 呼びの id(艦隊の道) | `engine/systems/decide.py:181` | `f"{tick}:{a}:{cls}"` |
| 呼びの id(mock・再生の道) | `engine/llm_bridge.py:792` | `f"{step}:{agent}:{class}"` |
| 時間帯 | `engine/systems/decide.py:185`・`engine/run.py:175` | `tick // TIME_BUCKET_TICKS`(5 刻み) |
| テープの列と鍵 | `engine/tape.py:148`・`:159`・`:312-314`・`:602`・`:643` | 列 `tick`・`observed_tick`(刻み)。再生の鍵 `(agent_id, tick, wake_class, prompt_hash)` |
| 出来事の記録 | `engine/events/log.py:309`・`:332-341`・`:506-509` | id は `(t_ns, seq)`。原因の列は呼びの id を `"{T}:{体}:{級}"` と読んで T を持つ(形が違えば文字列の表) |
| 記録の時計 | `engine/systems/conductor.py:199-200`・`engine/events/log.py:395-400` | 刻みの頭で `begin_step(t_ns)` |
| 状態のファイル | `engine/resume.py:432`・`:575` | ファイル名と見出し `progress.next_T` は刻みの番号 |

### 2-4 (d) 試験

数え方: tests/ の 405 ファイル・`def test_` 5,213 本を grep した。1 つのファイルが複数の型に当たるので、行は重なる。

| 型 | ファイル | そのファイルの中の試験の本数 |
|---|---:|---:|
| 1 日=1,440(`1440`・`1_440`・`MINUTES_PER_DAY`・`STEPS_PER_DAY`) | 128 | 1,748 |
| 60 秒の幅(`STEP_SECONDS`・`NS_PER_STEP`・`STEPS_PER_HOUR`・`tick_seconds`) | 49 | 519 |
| 乱数の鍵(`run_tick_key`・`wake_tiebreak`・`apply_key`) | 7 | 87 |
| 呼びの id・テープの鍵(`call_id`・`"tick"`・`observed_tick`) | 91 | 1,211 |
| 刻みの定数(不応期・会話・意図・在席・T_MAX・L4) | 34 | 585 |
| 結果の指紋(final・behavior/full-hash) | 113 | 1,517 |
| どれか 1 つ(上の型と `ticks=`) | 232 | 2,908 |

- `tick_seconds=` に 60 以外を渡す試験は 30 が 8 か所・7 が 2 か所だけ(grep)。1 秒を渡す試験は無い。
- 時間の直書きは `tests/engine/time/test_t0_literal_count.py` が AST で数える(`core/time_consts.py:3-5`)。
- 【見立て】器だけの段なら、結果の指紋の試験(113 ファイル)が「不変」の門になる。鍵を時刻に替える段では、呼びの id・テープの鍵の試験(91 ファイル)の多くが書き直しの対象になる。

### 2-5 既存の棚卸し(`docs/bench/analysis/wallbounce-0930/tick-constants-inventory.md`・09-30)との差

| 区分 | 項目 | 所 |
|---|---|---|
| 増えた | 時間の名前の表 `STEP_SECONDS`・`STEPS_PER_*`・`NS_PER_STEP`(T0) | `core/time_consts.py:58-65` |
| 増えた | 窓の幅は 60 の約数だけ・輪の地平 2 刻み | `engine/batching.py:62-64`・`:83` |
| 増えた | `NS_PER_STEP` を既定にする所 | `engine/memory_trace.py:36`・`engine/memory_store.py:1409`・`economy/ledger.py:308`(ledger は `attach_events` で幅を受ける=`engine/systems/build.py:1378`) |
| 増えた | `run_tick_key` の呼び手(判断の口・近接) | `engine/decision/port.py:313`・`engine/proximity.py:262` |
| 増えた | 腕の判断の口の `step_key` と `MAX_DECISIONS_PER_STEP`(回数の上限・時間ではない) | `engine/contact/port.py:110`・`engine/calendar2/port.py:75` ほか |
| 増えた | 歩く体の意図の時刻が既定の 60 秒で作られる | `engine/commit.py:637` |
| 増えた | 出来事の記録の原因の列が呼びの id の T を持つ | `engine/events/log.py:309` |
| 動いた | 時の札 `(tick // 60) % 24` は `td // STEPS_PER_HOUR` へ(意味は同じ) | `engine/systems/decide.py:213`・`engine/systems/judge.py:47` |
| 動いた | 体の周期は `engine/resolve.py` から `engine/body/rules.py:53`・`:58` へ | — |
| 動いた | 知覚の時計は `calendar.datetime_of` を渡す形に直った。描画の既定の時計だけ分のまま | `engine/systems/build.py:911`・`perception/renderer.py:1167` |
| 消えた | 棚卸し #42「艦隊の適用 `max(t_apply, tick+1)`」=位置 B は消え、下限は `tick` | `engine/systems/llm_io.py:9`・`:157-159` |
| 残った | 棚卸し §3 が挙げた「分=刻み」の所(在圏ブロック・W17 の境目・鉄道の時刻表)は、今もそのまま | `engine/presence.py:1123-1137`・`engine/processes/rail.py:351`・`:392` |

## §3 移行 M1 の実現性

### 3-1 前提の事実

- byte-check の比べる値は final・呼数・テープの全列の sha(`call_id`・`tick`・`observed_tick` を含む)・behavior/full-hash ほか(`docs/bench/analysis/wave2-2026-09-30/wave2_bytecheck.py:84-93`・`docs/bench/analysis/wallbounce-1012/10e/byte_check_10e.py:130`・`:265`)。19 構成は `cli.run` の引数の組(`wave2_bytecheck.py:54-64`)。
- 状態台帳の行 `BW` は軸 1 diag・軸 2 discardable で、どちらのハッシュにも状態のファイルにも入らない(`engine/state_ledger.py:971-986`)。
- `run_tick_key` と `time_key_from_t_ns` は、刻みの頭の時刻なら同じ値(`core/rng.py:130-144`・`tests/engine/time/test_t0_rng_key.py`)。

### 3-2 v3-0 で変えるものごとの判定

| 変えるもの | 結果 | 根拠 |
|---|---|---|
| 新しい核の器に、今の系の並びを 60 秒の刻みの事象 1 つで載せる | 動かない | T1 と同じ形(`engine/systems/conductor.py:7-10`)。窓 1 秒でも同じ値(raw `n5000_t60_h0_bw1.json`) |
| 窓の中の順の鍵を 1 本にする | 既定は動かない・腕は動きうる | 既定の窓には刻みの事象が 1 つだけ。会話の時計・c1・区域の時計の腕は同じ時刻に複数の事象を置く(`engine/systems/conductor.py:182-189`・`:209-210`) |
| 起床の同順の鍵を変える | 動く | 今の同順は `engine/arbiter.py:439-457`(`wake_tiebreak_array(run_salt, tick, …)`)。`engine/scheduler.py:121-135` の順は既定のランで使われていない(§1-2) |
| 乱数の鍵を `t_ns` から作る | 値が刻みの番号と同じなら動かない・単位を秒やナノ秒にすると動く | `core/rng.py:130-144`。生の tick を入れる口(§2-2)は、`t_ns // NS_PER_STEP` で同じ整数に戻せば不変 |
| 返事の適用の順の鍵 `apply_key_array(salt, t_apply, ag)` をナノ秒にする | 動く | `engine/systems/judge.py:102`・`core/hashing.py:181` |
| 呼びの id を世界の時刻の形にする | 動く | テープの `call_id` 列の sha が変わる(`wave2_bytecheck.py:91`)。艦隊では復号の seed も変わる(`llm/fleet.py:267-273`)。出来事の記録の原因の列は文字列の表へ落ちる(`engine/events/log.py:506-509`・diag) |
| テープの鍵 `tick` をナノ秒にする | 動く・古いテープの再生も壊れる | `engine/tape.py:312-314`・`:602`・`:643` |
| 列を状態に入れる(`BW` を required に) | 動く | full-hash と状態のファイルに行が加わる(`engine/state_ledger.py:975-986`)。再開の照合(2 日のラン・再開)も変わる |
| 状態のファイルの見出し `next_T` をナノ秒にする | 動く | `engine/resume.py:432`・`:575` |
| `refractory_until` などの刻みの欄をナノ秒にする | 動く(int32 では桁も足りない) | `agents/state.py:706`・`engine/resolve.py:827` |
| 刻みの幅そのものを 1 秒にする | 動く(§4) | §2-1 の定数の全部 |

### 3-3 見立て

- 【見立て】M1 は始められる。v3-0 を「器だけ」(新しい核・60 秒の刻みの事象・鍵の値は刻みの番号のまま・`BW` は discardable のまま・計器を足す)に限れば、19 構成の byte-check を 1 バイトも動かさずに通せる見込み。
- 【見立て】R-133 §8-3 の v3-0 は「鍵の 1 本化」「列を状態に入れる」「呼びの id と乱数の鍵を世界の時刻に」を同じ段に入れている。表のとおり、後ろ 2 つは byte-check の比べる値を動かす。v3-0a(器・不変)と v3-0b(鍵と id の形を替える版上げか、比べる列を宣言して外す段)に割る必要がある。
- 【見立て】刻みの事象が 60 秒の格子に乗っている間は、`t_ns // NS_PER_STEP` で今の整数を作り直せる。だから鍵の材料を「時刻から作る」書き方への置き換えは不変で進められる。単位を秒に替えた時点で結果が動く。
- 障害の一覧: 乱数の鍵(§2-2 の生の tick の 10 か所余り)・呼びの id(2 か所の f 文字列)・テープの再生の鍵・状態のファイルの見出し・`BW` の discardable 軸・アービタの同順のハッシュ・返事の適用の順のハッシュ・`refractory_until` の int32。

## §4 1 秒刻みで事象が膨らむ原因(上位 3 つ)

raw の比べ(5,000 体・seed 1・mock・世界の 0:00〜1:00。60 秒刻みは 60 刻み・1 秒刻みは 3,600 刻み+窓 1 秒):

| 欄 | 60 秒 | 1 秒 |
|---|---:|---:|
| 呼 | 69 | 38,001 |
| 意図 | 128 | 929,989 |
| 歩く体の刻み(moved) | 59 | 891,876 |
| 起床候補 | 6,376 | 97,936 |
| 不応期で抑えた数(suppressed) | 38 | 9,251 |
| 計画実行の到着 / 退出 | 45 / 0 | 5,743 / 5,659 |
| LLM の乗車で出た体 | 3 | 327 |
| 繰り延べ・縮退(deferred・degraded) | 0・0 | 0・0 |
| 呼/時(`calls_by_hour`) | 0 時に 69 だけ | 0〜23 の全部の札に 116〜4,380(朝 7〜9 と夕 17〜19 に山) |

### 第 1: 分の表を刻みの番号として使う(在圏ブロックと鉄道)

- 根拠: 在圏の事象の時刻は W17 の分(`engine/presence.py:1123-1137`・`:1240`・docstring `:654`)。`self.ticks` はランの刻みの数で、1 秒刻みでは 3,600(`engine/systems/build.py:851`)。表は刻みの番号で引く(`engine/presence.py:1278-1280`・`:1377-1380`)。鉄道の発車も時刻表の分(`engine/processes/rail.py:351`・`:392`・`:770`)。
- 1 秒刻みでは、分 m の出来事が m 秒目に起きる。1 日の到着・退出・就寝・起床と全部の便が、最初の 1,440 秒(世界の 0:00〜0:24)に詰まって実行される。
- raw の値はこの読みと合う。到着 45 → 5,743・退出 0 → 5,659 は 1 日ぶんの数。summary の「計画起床 743」「計画一致率(在圏) 0.550」も同じ。呼/時の札は `td // STEPS_PER_HOUR`(`engine/systems/decide.py:213`)で、1 秒刻みでは「分の札」を 60 で割った値になり、計画の 1 日の形(朝と夕の山)がそのまま出ている。
- 【推測】呼 69 → 38,001 の大部分はこれで説明がつく。60 秒刻みの 0〜1 時は、ほぼ全員が寝ているか域外に居る時間帯だった(sleep_suppressed 973・outside_suppressed 5,290)。1 秒刻みは、ほぼ 1 日ぶんの起きている人の判断を回した。

### 第 2: 歩く体を刻みごとに 1 歩進める

- 根拠: 歩いている体は毎刻み 1 件の「エンジンの継続」の意図を出す(`engine/commit.py:621-638`・`engine/systems/act.py:53-58`)。nav1 の 1 刻みの歩みは希望速度 × 刻みの秒(`engine/store_choice.py:64-69` と同じ考え)なので、同じ道のりに 60 倍の刻みがかかる。
- raw: 意図 929,989 のうち歩く体の刻みが 891,876(96%)。刻みあたり約 248 体が歩いていた計算(891,876 ÷ 3,600)。
- 歩く体の数そのものも第 1 で増えている。事象駆動の核では、この分は「歩き出し」と「着く」の 2 事象に置き換わる【見立て】。
- 付記: 歩く体の意図の時刻 `t_notice_ns` は幅を渡さずに作るので、1 秒刻みでは 60 倍の時刻になる(`engine/commit.py:637`・`:467-469`)。数は増やさないが、時刻の意味は壊れる。

### 第 3: 刻みの数で書いた不応期・昇格・会話の定数

- 根拠: 不応期の表は分の値を刻みとして足す(`agents/state.py:306-318`・`engine/resolve.py:262`・`:827`)。比べは刻みの番号(`engine/arbiter.py:402`)。セル変化の不応期 30 は 30 秒・近接入替 15 は 15 秒になる。昇格の待ち `T_MAX_TICKS`(`engine/arbiter.py:107-112`)、会話の招待の間隔と寿命(`engine/conversation.py:90-110`)、体の周期(`engine/body/rules.py:53`・`:58`)も同じく 60 分の 1。
- 変化の検出と起床候補は毎刻み作り直す(`engine/systems/perceive.py:73`・`engine/systems/judge.py:372-398`)。1 体が同じ条件で起きてよい頻度の上限が 60 倍になる。
- raw: 起床候補 15 倍・不応期で抑えた数 243 倍。【推測】第 1 と分けて測っていないので、呼の増え方への寄与は量れない。

### 原因でないもの

- L4 の予算は刻みあたり(`engine/arbiter.py:127`・`:137-151`)で、1 秒刻みでは 1 日の量が 60 倍に緩む。ただし CLI の既定は上限なし(`l4_scale=0` → 予算=体数/刻み=`cli.py:110`・`:526-527`)。raw でも deferred・degraded は両方のランで 0。このランの膨らみの原因ではない(上限を入れたランでは効く)。

## §5 答申 R-130・R-133 との食い違い

| # | 答申の所 | 答申の記述 | 本書の読み | 根拠 |
|---|---|---|---|---|
| 1 | R-130 §0-8・§3 末尾・§5-1 の 3 | 膨らむ理由は「不応期・起床の検査・L4 の予算が刻みの数で書かれている」(推測) | 第 1 の原因は、在圏の表と鉄道の時刻表が分のまま刻みの番号に使われていること。L4 はこのランでは当たっていない | §4。`engine/presence.py:1123-1137`・`engine/processes/rail.py:351`・`cli.py:526-527`・raw の deferred 0 |
| 2 | R-130 §3・§5-1 の 3 | 「夜の 1 時間でも呼が 551 倍」「いちばん静かな 1 時間で使った」 | 1 秒刻みのランは 1 日ぶんの計画を最初の 24 分に詰めて回しており、夜の 1 時間ではない。比べた 2 本は仕事の中身が違う | raw の到着 5,743・退出 5,659・呼/時の 24 札 |
| 3 | R-130 §3 の表と「124 倍」・§0-9 | 1 秒刻みの 1 時間の壁時計を、刻み比例の費用の材料に使う | 1 秒刻みの 43.7 秒には 1 日ぶん近い事象の費用が入る。刻みの固定費の見積りには「事象の無い刻みの床」(2.0 ms)だけが使える【見立て】 | #2 と同じ |
| 4 | R-130 §4 の「圏の出入り(エンジン)」 | 「エンジンは 1 人が何度も出入りするのを数える(推測・確かめていない)」 | 未確認のまま。本書も確かめていない | — |
| 5 | R-133 §0-1・§1-1 の読み | 今の進行役はすでに事象の列で動いている | 器は列だが、中身は 60 秒の刻みの事象が全系を回す時間駆動。列にある世界の事象は既定で 1 種 | §1。`engine/systems/conductor.py:191-212` |
| 6 | R-133 §0-2・§1-1 の 3 行目 | 同時刻の鍵の 1 通りは「起床のスケジューラ」の「時刻 → 級 → blake3 → 体」 | `engine/scheduler.py` の順(`order_indices`)は既定のランで呼ばれない。実際の起床の同順はアービタの `lexsort((agent, pk, -waited, eff_class))`(待ちの長さも入る)で、ハッシュに刻みの番号が入る | `engine/arbiter.py:439-457`・§1-2 の最後の行 |
| 7 | R-133 §1-1 の presence の行・§8-3 の v3-1 | 計画実行層の事象を「既に事象の形」として列へ移す(時刻が 60 秒の格子なら一致) | その表の時刻の単位は分で、刻みの幅とは結び付いていない。列へ移す前に、表の時刻を秒(か t_ns)に直す段が要る。60 秒刻みのままなら一致する | `engine/presence.py:654`・`:1278-1280` |
| 8 | R-133 §8-2 (M1)・§8-3 v3-0 | v3-0 で鍵の 1 本化・列を状態に・呼びの id と乱数の鍵を世界の時刻に、のうえで 19 構成が一致 | 後ろ 2 つは byte-check の比べる値(テープの `call_id` 列・full-hash・状態のファイル)を動かす。器だけの段と分ける必要がある【見立て】 | §3-2 |
| 9 | R-133 §2-2 の決定論の注意 | 今の `run_tick_key` は刻みの番号を使う | `run_tick_key` のほかに、生の tick を counter やハッシュに入れる口が 10 か所余りある(mock の返事・古典・選び・会話の招待・気づき・起床の同順・適用の順) | §2-2 |
| 10 | R-133 §1-1 の batching の行 | 幅 W は 60 秒の約数だけ | 正確。加えて、刻みの幅が 60 でないと既定の幅のままでは核が組めない(`engine/batching.py:192-193`)。R-130 §3 も同じことを書いている | — |
| 11 | R-130 §6 の 12 番・R-133 §1-1 | `run_day` の `tick_seconds` は `run.py:2001`、runner の step は `runner.py:453` | HEAD `90258ef` ではそれぞれ `engine/run.py:2006`・`engine/processes/runner.py:460`。土台の commit の差で、中身の食い違いではない | — |

- 09-30 の棚卸し §2 の p 行と §3 は「計画境界の tick が分のまま」「直さないと 15 秒刻みでは 1 日の境界が最初の 6 時間に詰まる」と書いていた。R-130 はこれを引いていない。

## §6 読めなかった所・確かめられなかった所

- ランは回していない。§4 の 3 つの原因の寄与の割合は、raw の数からの推測。分けて測るには、在圏と鉄道の時刻を秒に換算した腕と、不応期を秒で書いた腕の 2 本を足して回す必要がある(どちらもコードの変更が要る=本書の範囲の外)。
- byte-check の 19 構成の中身(`docs/bench/analysis/w6-regen-2026-09-28` の `ARMS`)は開いていない。時計の腕(mora・regional・c1)を含むかは確かめていない。§3-2 の「腕は動きうる」はその前提つき。
- `engine/run.py` の `run_day`(約 4,000 行)は `_split_due` の周りしか読んでいない。`tick_seconds` を受けて換算している所の網羅は §2-1 の grep の範囲まで。
- 体の層の reserve の腕(`engine/body/schedule.py`)と区域ごとの時計(`engine/regional_clock.py`)・会話の時計(`engine/speech_clock.py`)の中は読んでいない。
- 試験の本数(§2-4)は grep の当たりの上限で、刻みの番号を本当に前提にしているかは 1 本ずつ見ていない。
- R-133 の §11 の出典(Web)は確かめていない(Web 不使用)。
- `data/`・`data/jinryu/`・holdout は開いていない。

## 読んだファイル

- src: `engine/systems/conductor.py`(全)・`engine/batching.py`(全)・`engine/scheduler.py`(全)・`engine/clock.py`(全)・`core/time_consts.py`(全)・`engine/systems/table.py`(全)・`engine/systems/llm_io.py`(全)・`engine/systems/decide.py`(全)・`engine/presence.py`(1-215・440-500・650-700・1105-1404 と grep)・`engine/processes/runner.py`(grep・460-468)・`engine/llm_bridge.py`(30-204 と grep)・`engine/arbiter.py`(90-219・290-610)・`engine/resolve.py`(200-324・800-834)・`agents/state.py`(300-337)・`engine/systems/judge.py`(1-120・240-399)・`engine/systems/act.py`(20-69)・`engine/systems/perceive.py`(50-107)・`engine/commit.py`(467-470・621-638)・`engine/conversation.py`(60-129・600-659)・`engine/change_detect.py`(grep)・`core/rng.py`(116-144 と grep)・`core/hashing.py`(grep)・`engine/tape.py`(grep)・`engine/events/log.py`(grep)・`engine/state_ledger.py`(960-990)・`engine/resume.py`(grep)・`engine/systems/build.py`(150-378・830-869 と grep)・`engine/systems/boxes.py`(87-91)・`engine/systems/day.py`(19-27)・`engine/processes/rail.py`(120-135・340-392・420-437・765-772)・`engine/body/schedule.py`(265-345 と grep)・`engine/store_choice.py`(60-80)・`world/state.py`(388-400)・`economy/ledger.py`(300-315)・`llm/fleet.py`(grep)・`cli.py`(425-445・515-530 と grep)・`engine/run.py`(1974-1977 と grep)
- docs: `docs/research/v2-r130-core-timing-and-event-counts.md`(全)・`docs/research/v2-r133-event-driven-core-design-options.md`(全)・`docs/bench/analysis/wallbounce-0930/tick-constants-inventory.md`(全)・`docs/bench/analysis/v3-2026-11/a/raw/n5000_ts1_h0.summary.txt`・`n5000_t60_h0.json`・`n5000_ts1_h0.json`・`n5000_t60_h0_bw1.json`(欄の抜き出し)・`docs/bench/analysis/s2e-1102/bytecheck/cmp_head1c137c6_vs_merged4566492_default.json`(鍵の一覧)・`docs/bench/analysis/wave2-2026-09-30/wave2_bytecheck.py`(54-99)・`docs/bench/analysis/wallbounce-1012/10e/byte_check_10e.py`(grep)・`docs/design/v2-implementation-plan-2026-10-12.md`(grep)・`CLAUDE.md`
- tests: grep だけ(§2-4)
