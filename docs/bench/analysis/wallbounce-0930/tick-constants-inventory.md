# tick 単位の定数と毎 tick の起床の棚卸し(指示書 §0-2・§1-10 (b) の下調べ)

- 日付: 2026-09-30 / 実行役サブ(Opus 5.5)/ 親の検収前
- 対象: src/shibuya/(build/ を除く=世界データの構築は tick を持たない)。コードを読んだだけ(ランは回していない・無変更)。
- 目的: 指示書 [v2-wallbounce-decisions-2026-09-30.md](../../../design/v2-wallbounce-decisions-2026-09-30.md) §0-2「時間に関わる確率・長さは秒あたり/時間あたりで書く」と §1-10 (b)「10〜15 秒の tick を腕として試す」の前に、書き直しの手間を測る。

## 0. 前提: 1 tick = 60 秒(確認)

- `DEFAULT_TICK_SECONDS: Final[int] = 60  # 運用設計書 §1.2 設定節 tick_seconds`(src/shibuya/core/types.py:93)。
- `run_day(..., tick_seconds: int = DEFAULT_TICK_SECONDS, ...)`(src/shibuya/engine/run.py:1531)。**CLI に `--tick-seconds` は無い**(src/shibuya/cli.py と run.py の `add_argument` を grep・該当なし)。本番・ablation は全部 60 秒。
- 60 以外の値を使うテストは `tests/engine/test_clock.py:26`(`SimClock(START, tick_seconds=30)`)だけ見つかった(tests/ を `tick_seconds=(15|30|10|120)` で grep)。`SimClock`(src/shibuya/engine/clock.py)は秒に対応しているが、**`run_day` は使っていない**(src/shibuya を grep・`engine/__init__.py` の再輸出だけ)。

## 1. tick 数で書かれた時間の定数・確率

列「15 s で」= tick を 15 秒にしたときの挙動。**変わる**=実時間の長さ(または頻度)が 1/4(または 4 倍)になる。**変わらない**=秒/分から tick へ換算している。**不明**=コードだけでは決められない。

### 1-1 起床・不応期・アービタ

| # | ファイル:行 | 名前 | 値 | 意味 | 秒(60 s tick) | 15 s で |
|---|---|---|---|---|---|---|
| 1 | agents/state.py:305-317(使う所 engine/resolve.py:254・:792-) | `REFRACTORY_MINUTES` | 0/360/150/60/15/45/10/15/5/5/30 | 起床条件 11 種の不応期。**名前は分だが tick として使う**(arbiter.py:128「tick_seconds=60 なので 1 分 = 1 tick」・resolve.py:293 同旨) | 0/21,600/9,000/3,600/900/2,700/600/900/300/300/1,800 | **変わる**(不応期が 1/4=起床の上限頻度 4 倍) |
| 2 | engine/resolve.py:281-(`refractory_ticks(scale)`) | 実効不応期表 | 上の表 × 倍率(half-up 丸め) | ablation ③ の口 | 同上 | **変わる**(丸めも分の整数前提) |
| 3 | engine/arbiter.py:106-111 | `T_MAX_TICKS` | 会話 3/計画境界 10/個体 30/セル 60 | 繰り延べの昇格までの待ち | 180/600/1,800/3,600 | **変わる** |
| 4 | engine/arbiter.py:117 | `POOL_CAP_TICKS` | 2.0 | 端数繰越の上限(tick 何個ぶんの予算か) | 120 s ぶん | **変わる**(L4 の腕のときだけ効く) |
| 5 | engine/arbiter.py:126・:136-150 | `_TICKS_PER_DAY`(`call_budget_per_tick` の既定) | 1,440 | L4 の日量を tick へ按分 | 1 日 | **変わる**(L4 の腕では日量が 4 倍になる。既定の無制限=予算 n_agents/tick(cli.py:430)では按分に使わない) |

### 1-2 会話

| # | ファイル:行 | 名前 | 値 | 意味 | 秒 | 15 s で |
|---|---|---|---|---|---|---|
| 6 | engine/conversation.py:90 | `REFUSAL_MEMORY_TICKS` | 60 | 拒否/無視の記憶 | 3,600 | **変わる** |
| 7 | engine/conversation.py:92 | `SILENCE_TICKS` | 5 | 沈黙のソフト終了(:758 `tick - last_utterance_tick > silence_ticks`) | 300 | **変わる** |
| 8 | engine/conversation.py:94 | `MAX_SESSION_TICKS` | 60 | セッション寿命の上限 | 3,600 | **変わる** |
| 9 | engine/conversation.py:102 | `PENDING_INVITE_TTL_TICKS` | 3 | 被招待の返事の待ち。根拠のコメントが「δ_think L1=1 tick + アービタの繰り延べ 1 tick 分の余裕」=**tick の構造から導いた値** | 180 | **変わる**(ただし根拠が tick 数なので 3 tick のままが正しい可能性=要判断) |
| 10 | engine/conversation.py:107 | `PAIR_INVITE_REFRACTORY_TICKS` | 60 | 同一相手への招待の間隔(知覚契約 §6「同一相手 60 分」) | 3,600 | **変わる** |
| 11 | engine/conversation.py:110 | `SPEAKER_INVITE_REFRACTORY_TICKS` | 30 | 同一話者の招待の間隔(「同一話者 30 分」) | 1,800 | **変わる** |
| 12 | engine/conversation.py:84-86 | `MAX_TURNS`/`IMPORTANT_EXTRA_TURNS` | 3 / +2 | 1 体の LLM 呼の上限(時間ではない)。ただし**会話は 1 ターン = 1 tick**(会話ターン起床・不応期 0) | 1 ターン 60 s | 回数は**変わらない**・会話の実時間は **1/4** |

### 1-3 行動の持続・意図・移動

| # | ファイル:行 | 名前 | 値 | 意味 | 秒 | 15 s で |
|---|---|---|---|---|---|---|
| 13 | engine/processes/crowd.py:96(使う所 :231) | `DWELL_MAX_TICKS` | 30 | 在席の上限=回転率。食事 20 分の宣言(resolve.py:222 `EAT_DWELL_MINUTES`)も専用タイマーを持たずこれに従う | 1,800 | **変わる** |
| 14 | engine/processes/crowd.py:98(使う所 :242・:306) | `WAIT_MAX_TICKS` | 15 | 列の離脱(`INTERRUPTED`)・観測欄の平均待ち近似 | 900 | **変わる** |
| 15 | engine/intent.py:99(CLI engine/run.py:1839・cli.py:859 `--intent-max-ticks`) | `INTENT_MAX_TICKS` | 60(腕 30/120) | 歩いてこれを超えたら `TOO_FAR` | 3,600 | **変わる**。store_choice.py:19 の到達可能性も `歩速[m/tick] ≤ min(次の予定までの tick, INTENT_MAX_TICKS)` で tick の上限を使う |
| 16 | engine/presence.py:88・:607 | `EXIT_WALK_MAX_TICKS` | 60 | 歩いて乗る退出の上限(9a) | 3,600 | **変わる** |
| 17 | engine/presence.py:82(使う所 :1637・:1640) | `RETURN_MIN_AWAY_MIN` | 60 | 在圏ブロックへ戻る最短の外出。**名前は分だが tick に足している**(`self._earliest_enter_tick(t + RETURN_MIN_AWAY_MIN)`) | 3,600 | **変わる** |
| 18 | engine/resolve.py:201(使う所 :1750・:1774) | `FOCUS_TTL_TICKS` | 10 | 注意の焦点の寿命(毎 tick −1) | 600 | **変わる** |
| 19 | engine/resolve.py:236(使う所 :2544) | `REPORT_WINDOW_TICKS` | 5 | 通報の前提「知覚済み」の窓。コメントが「最長レーン L3(300 s)= 5 tick」=**秒からの導出値を tick で固定** | 300 | **変わる**(秒から導けば 20 tick) |
| 20 | engine/resolve.py:237(使う所 :2009) | `BOARD_WAIT_LIMIT_TICKS` | 30 | 乗車待ちの打ち切り | 1,800 | **変わる** |
| 21 | engine/processes/rail.py:118・:123・:129 | `DWELL_TICKS`/`DWELL_TICKS_TERMINAL`/`DWELL_TICKS_BY_LINE` | 1 / 2 | 停車時間(通過型/終端) | 60 / 120 | **変わる**(15/30 s。コメント rail.py:113-117 は実値 30〜60 s を「1 分 tick では表せない」と宣言=**実値に近づく方向**) |
| 22 | world/graph.py:12(使う所 engine/resolve.py:1519 `step_once`) | 1 tick = 1 ノード前進(既定の `--geometry node`=geometry.py:84) | 1 ノード/tick | node 幾何の歩行 | — | **変わる**(実時間の歩行速度が 4 倍) |
| 23 | engine/geometry.py:99(使う所 :328) | `MAX_HOPS_PER_TICK` | 32 | edge 幾何の 1 tick の辺跨ぎの上限(距離は `v × f(ρ) × tick_seconds`=:277) | — | **変わらない**(距離は秒で換算・上限に当たりにくくなるだけ) |
| 24 | engine/activity.py:78・llm/contract.py:1163・:1165(換算 activity.py:211) | `PARTNER_MAX_MINUTES`/`UNTIL_DEFAULT_MINUTES`/`UNTIL_MAX_MINUTES` | 60 / 60 / 480 分 | 「まで」の既定と上限 | 3,600 / 3,600 / 28,800 | **変わらない**(`np.ceil(m / minutes_per_tick)`) |

### 1-4 体(内受容)

| # | ファイル:行 | 名前 | 値 | 意味 | 秒 | 15 s で |
|---|---|---|---|---|---|---|
| 25 | engine/resolve.py:176(使う所 :1115 `int(tick) % BODY_TICK_PERIOD == 0`) | `BODY_TICK_PERIOD` | 30 | 疲労 +1(energy でないときは空腹も +1)・就寝中の疲労 −2 の周期 | 1,800 | **変わる**(疲労の進みが 4 倍=既定の energy 腕でも疲労はこの規則) |
| 26 | engine/resolve.py:184(使う所 :1117) | `ACTIVITY_REST_PERIOD_TICKS` | 10 | 休んでいる体の疲労 −1 の周期(`--activity on`=既定 cli.py:798) | 600 | **変わる** |
| 27 | engine/energy.py:261・:334 | energy の消費(`EER/1440 × 分/tick × METs`) | — | 既定の空腹(`DEFAULT_HUNGER_MODEL = "energy"`=energy.py:105) | — | **変わらない**(`minutes_per_tick` で換算) |
| 28 | engine/change_detect.py:73・:75 | `INTERO_UP_EDGES`/`INTERO_HYSTERESIS` | 4/7/9・1 | 内受容の段の閾値(値の閾値で時間ではない) | — | 定数は**変わらない**。ただし #25 で値の進みが 4 倍なので**跨ぎの回数は変わる** |

### 1-5 記憶・関係・なじみ(Δt の単位)

| # | ファイル:行 | 名前 | 値 | 意味 | 15 s で |
|---|---|---|---|---|---|
| 29 | engine/memory.py:113・:220-226 | `MEMORY_D` と `activation_rows` | d=0.5・L=(tick−first)×分/tick | 記憶の活性。**Δt の単位は分**。importance は固定表(memory.py:181・時間で減衰しない) | **変わらない** |
| 30 | engine/familiarity.py:91・:187 | `FAMILIARITY_D`・L | d=0.5・分 | なじみの活性。場所は「入った回」だけ数える(tick ごとではない・docstring :37-38) | **変わらない** |
| 31 | engine/store_memory.py:100・:101・:310・:329-347 | `GA_RECENCY_PER_HOUR` 0.995/時・`CITYSIM_LAMBDA_PER_DAY` 0.03/日・actr の L | 時・日・分で換算 | 店の評価の減衰 | **変わらない** |
| 32 | engine/relations.py:112・:127・:139・:142(換算 :914・:932) | `REL_D`・`REL_SLOT_MIN` 15・`REL_COPRESENT_MINUTES` 5・`REL_ACQ_PAIR_REFRACTORY_MIN` 60 | 分 | 関係の活性・共在の枠・同席 5 分・知人出現の同一相手 60 分 | **変わらない**(`minutes_per_tick` で換算)。ただし知人出現の**体の**不応期は #1 の表(10 tick)で変わる |
| 33 | engine/classical.py:93(換算 :334) | `MEAL_CALENDAR_MIN` | 30 分 | 古典の腕の食事ゲート | **変わらない** |

### 1-6 世界過程・計器・その他

| # | ファイル:行 | 名前 | 値 | 意味 | 秒 | 15 s で |
|---|---|---|---|---|---|---|
| 34 | perception/p_notice.py:113 | `MAX_EVENTS_PER_TICK` | 200 | 顕著イベントの tick あたり上限 | 200/60 s | **変わる**(上限が秒あたり 4 倍。上限に当たっていなければ影響なし=不明) |
| 35 | engine/processes/salient.py:305-306 | 崩れの発生率 | 日あたり率 × tick_seconds/86,400 | ポアソンの tick あたり期待値 | — | **変わらない** |
| 36 | engine/processes/goods_flow.py:115(使う所 :578) | `LITTER_G_PER_PERSON_TICK` | 0.05 g/人/tick | 街路ごみの発生 | 0.05 g/人/分 | **変わる**(1 日のごみが 4 倍) |
| 37 | engine/processes/goods_flow.py:119(使う所 :584-585) | `CELLS_PER_SWEEP_TICK` | 8 | 清掃の進み | 8 セル/分 | **変わる** |
| 38 | engine/processes/opening.py:50・:177-178/goods_flow.py:85・:223/environment.py:73・:246 | `STEP_MINUTES` 5・`RESTOCK_STEP_MINUTES` 5・`THERMAL_STEP_MINUTES`(=5) | 5 分 | 分を秒から出し `minute % 5` で間引く | — | **不明**: 該当の分に 4 tick 続けて走る。開閉(状態の比較)・暑さ(同じ値の上書き)は冪等に見えるが、補充(在庫が発注点未満なら発注)は 4 回走ると量が変わりうる【推測】 |
| 39 | engine/processes/civic.py:90・:137/logistics.py:74/traffic.py:145/environment.py:214/salient.py:423 | 時刻の換算 | `tick * tick_seconds // 60` | 世界過程の時刻 | — | **変わらない** |
| 40 | engine/run.py:239(使う所 :3124・llm/fleet.py:354・:622) | `TIME_BUCKET_TICKS` | 5 | 艦隊の順序制御の「5 分帯」(知覚契約 §2.4 ⑨) | 300 | **変わる**(75 秒帯になる) |
| 41 | engine/llm_bridge.py:155-161・:176-192 | `LANE_SECONDS`・`delta_think_ticks` | L1 2.6 s ほか | δ_think(秒 → `ceil(秒/tick秒)`) | — | **変わらない**(L1 は 15 s でも 1 tick)。run.py:231 `DELTA_THINK_TICKS` は 60 秒固定で計算した定数だが src 内で参照しているのは docstring だけ(grep) |
| 42 | engine/run.py:2914-2917 | 艦隊の応答の適用 `max(t_apply, tick+1)` | — | 本番(障壁あり)では常に発射 + 2 tick で適用([tick-llm-overlap.md](tick-llm-overlap.md) §1-4) | 120 | **変わる**(30 s) |
| 43 | engine/norm_meter.py:57(使う所 :341・:346) | `COWALK_MINUTES` | 5 | 群れ歩きの連続時間。**連続 tick 数と比べている** | 300 | **変わる**(計器のみ・世界は動かない) |
| 44 | engine/energy.py:583-588 | `stage_ticks` | — | 空腹の段の延べ(tick 数で数える計器) | — | **変わる**(計器の単位のみ) |
| 45 | engine/scheduler.py:79 | `HORIZON_TICKS` | 1,440 | 遠未来予約を heapq へ回す地平 | 1 日 | 挙動は**変わらない**見込み(性能の構造)【推測】 |

## 2. 毎 tick 評価される起床の種類と、tick を 10〜15 s にしたとき

起床候補は run.py:2779-3012 で 6 本の配列に集めてアービタへ渡す(`WakeCandidates(np.concatenate([p_agent, d_agent, c_agent, s_agent, f_agent, e_agent]), ...)` run.py:2986-2987)。

| 源 | 何を見ているか(場所) | 毎 tick の評価 | 10〜15 s で回数 | 理由 |
|---|---|---|---|---|
| p 計画境界 | W17 の境界(`weekly.boundary_events_full`・agents/weekly.py:327 `tick = self.start_min[idx]`)を tick で切り出す(run.py:2808) | 境界の tick だけ | **増えない**(事象) | ただし境界の tick が**分をそのまま使っている**ので、tick を変えると時刻がずれる(§3)。直さないと 15 s tick では 1 日の境界が最初の 6 時間に詰まる |
| d-(i) セル B4 の変化(CELL_BLOCK) | 自分のセルの B4 描画欄(LOS 6 段・騒音段・流れ・顕著行為ダイジェスト)の行が前 tick と違う(change_detect.py:286-299・:370-378) | 全セル×毎 tick | **増える** | 密度の段の境目でのちらつきを細かく拾う【推測】。不応期 30 tick(#1)が 7.5 分になり 1 体の上限頻度が 4 倍 |
| d-(ii) 内受容の段の跨ぎ(INTEROCEPTION) | hunger/fatigue/thermal の段(change_detect.py:302-341) | 全個体×毎 tick | **増える**(いまのままなら) | 疲労の進みが tick 周期(#25・#26)なので 4 倍速。秒へ直せば事象の数は**増えない** |
| c 会話ターン | `conv.wake_candidates(tick)`(run.py:2854-2855)・不応期 0 | 会話中の体×毎 tick | **増えない**(1 会話の呼数は MAX_TURNS で上限)/**会話の数は増える**見込み | 1 ターン=1 tick。招待の間隔(#10・#11)・拒否の記憶(#6)が 1/4 になり 1 時間あたりの招待が増える【推測】 |
| s 顕著行為の到達 | `runner.salient_wake_candidates(tick)`(run.py:2863-2864)・発生は日あたり率(#35) | 事象のある tick | **増えない**(上限 #34 に当たらない限り) | |
| f 艦隊の繰り延べの再投入 | 前 tick に答えが返らなかった呼(run.py:2928-2945) | 毎 tick | 不明 | タイムアウト・キュー満杯次第(tick の長さでは決まらない) |
| e-1 活動の満了(ACTIVITY_EXPIRY) | `act_layer.expiry_candidates`(run.py:2795)・`activity_until` は分から換算(#24) | 毎 tick | **増えない** | |
| e-2 知人出現(ACQUAINTANCE) | 知人が同じセルに**現れた** tick(relations.py:934-974・前 tick とセルが違う=縁で発火)・同一相手 60 分は分で換算 | 毎 tick | **増えない**(縁で発火)/体の不応期 10 tick は 1/4 | 連続位置(D 層)でセルの境をまたぐちらつきが増えれば増える【推測】 |
| (参考)同席の書き手 | `rel_layer.copresent_step`(run.py:2967)=起床ではなく関係の書き込み | 毎 tick | — | 5 分は分で換算(#32) |
| (未実装)近接入替・被注視・傍受 | change_detect.py:40-41「C2 では検出しない」 | — | — | 候補を作るコードが無い |

- 毎 tick の**評価の費用**(回数)はすべて tick 数に比例して 4〜6 倍になる(P6 の変化検出・知人の同セル走査など)。これは起床の回数とは別【計算: 1,440 → 5,760〜8,640 tick/日】。

## 3. 1 tick = 60 秒を前提にしているコード(時刻の換算・1,440 tick/日)

「分 = tick」として分の値を tick に入れている所(tick を変えると時刻がずれる):

| ファイル:行 | 中身 |
|---|---|
| core/types.py:93-94 | `DEFAULT_TICK_SECONDS = 60`・`MINUTES_PER_SIM_DAY = 1_440` |
| cli.py:621(・:385) | `--ticks` の既定 = `MINUTES_PER_SIM_DAY`(1 日 = 1,440 tick) |
| engine/run.py:2229 | 知覚の時計 `clock_fn=lambda t: start + timedelta(minutes=int(t))` |
| perception/renderer.py:1054 | 既定の `clock_fn` も `timedelta(minutes=int(t))` |
| engine/run.py:3019 | 起床率/時 `_h = (tick // 60) % 24` |
| engine/run.py:3140 | 呼/時 `calls_by_hour[(tick // 60) % 24]` |
| engine/run.py:490 | 同(docstring「時 = `(tick // 60) % 24`」) |
| engine/run.py:3903 | 状態成長宣言 `minutes_per_step=max(1, tick_seconds // 60)`(15 s では 0.25 でなく 1 になる) |
| agents/weekly.py:327 | 計画境界の tick = `start_min`(分) |
| engine/presence.py:412-413・:485-488・:1070・:1620-1621 | 在圏ブロックの開始/終了[分]を tick と同じ軸で比べる |
| engine/presence.py:602 | `ticks: int = MINUTES_PER_DAY` |
| engine/presence.py:1695・:1706 | `(tick // 60) % 24` |
| engine/presence.py:1697・:1731 | `in_area_at(tick % MINUTES_PER_DAY)` |
| engine/presence.py:1637 | `t + RETURN_MIN_AWAY_MIN`(#17) |
| engine/processes/rail.py:320-326 | 発車 tick = 時刻表の `tt_departure_min`(分) |
| engine/arbiter.py:126・:141 | `_TICKS_PER_DAY = 1_440`(L4 の按分) |
| engine/arbiter.py:128/engine/resolve.py:293 | 「tick_seconds=60 なので分=tick」(不応期) |
| engine/growth_decl.py:54・:67・:114・:123 | `TICKS_PER_DAY = 1_440`(状態成長宣言の日あたり量) |
| engine/scheduler.py:79 | `HORIZON_TICKS = 1_440` |
| economy/ledger.py:108 | `_TICKS_PER_DAY = 1_440`(定義のみ・同ファイル内で参照なし=grep) |
| cli.py:581 | `int(row["tick"]) // 60`(時の集計) |
| engine/processes/rail.py:33・:57・:113-117 | 「1 tick=60 秒」を前提にした説明(停車時間) |
| world/graph.py:12 | 「1 tick=1 ノード前進 … 6 km/h の歩行に一致」(合成世界の説明) |

秒に対応済み(tick_seconds か minutes_per_tick で換算している)の主なもの: engine/geometry.py:189-277(edge の歩行距離)・engine/activity.py:171-241・engine/energy.py:217-479・engine/classical.py:271-334・engine/relations.py(minutes_per_tick)・engine/memory.py・engine/familiarity.py・engine/store_memory.py・engine/store_choice.py:64-87・engine/norm_meter.py:83-153(時の集計のみ)・engine/processes/{civic,environment,goods_flow,logistics,opening,salient,traffic,crowd(時刻のみ)}・engine/llm_bridge.py:176-192・engine/clock.py(未使用)。

## 4. 書き直しの手間の見積もり(【推測】)

- tick 数の定数は **約 30 個**(§1 の「変わる」)。ほとんどは「秒の定数 + `ceil(秒 / tick_seconds)` の換算 1 行」で済む。既定の checkpoint は 60 s のまま動かないように書ける(換算結果が同じ整数になる)。
- 手間が大きいのは §3 の「分 = tick」の箇所: **presence(在圏ブロックの軸)・W17 の境界・鉄道の時刻表・知覚の時計**。軸を tick に直すか、分へ変換する層を 1 つ挟むかの設計判断が要る。
- 意味の判断が要るもの: #9(招待の待ち 3 tick は tick の構造から導いた値)・#12(会話 1 ターン = 1 tick を秒で固定するか)・#21(停車時間は実値へ近づく)・#22(node 幾何は 1 tick 1 ノード=秒にできない)・#38(5 分間引きが 4 回走る)・#42(艦隊の +2 tick)。

## 5. 探した範囲と漏れの可能性

- grep した型: 大文字定数の名前に TICK/TTL/REFRACT/WINDOW/MIN/MINUTES/PERIOD/WAIT/DWELL/STEPS などを含むもの・`tick //`・`tick %`・`// 60`・`1440`/`1_440`・`* 60`・`tick_seconds`・`minutes_per_tick`・乱数の抽選(`.random(`)。
- 乱数の抽選はすべて「呼ごと・事象ごと」で、tick あたりのハザード確率(毎 tick 一定の確率で起きる)は見つからなかった(chooser.py:269・classical.py:465・conversation.py:385・goods_flow.py:341・attention.py:226・p_notice.py:479 を確認)。
- 名前に単位を含まない数字直書き(例: `+ 1` を毎 tick 足す類)は網羅していない。§1 の #25・#26 のように周期で書かれたものは拾ったが、他に直書きがある可能性は残る。
