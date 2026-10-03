# 10a の実装(K1・K7〜K9 に左右されない部分): 通しの時刻 T・暦の口・応答の遅れ +1(2026-10-03)

> 実行役(Opus 5.5)の記録。親の検収前。commit していない。指示: [壁打ちの決定 10-03](../../../../design/v2-wallbounce-decisions-2026-10-03.md) §3-1・§3-5・§3-8、着手の形: [10a のアジェンダ](../../../../design/v2-d102-10a-agenda.md) §2・§4、材料: [10a の材料](../10a-prep.md)。
> **やっていないこと(次の便)**: テープ版 4(K1 待ち)/ 暦の既定の切り替え(K8 待ち=既定は今の `day_index` の曜日のまま)/ 学校の長期休みの表の中身(K7 待ち=表は空で口だけ)/ 日の頭の初期化と日ごとの表の作り直し(10g・A11)。

## 0. 結論

1. **既定の結果は動いていない**。HEAD(`3342b65`。byte-check の写しは `a08109a` から取ったが、`git diff a08109a 3342b65 -- src tests` は空=src と tests に差は無い)の `git archive` の写しと作業木で 19 構成(W6 再生成の 15 腕+店の記憶・関係・古典・古典+記憶+関係)を mock/classical 5,000 体・1 シミュ日・テープつきで回し、final・呼数・blocks・calls の 14 列(prompt_hash を含む)が **19/19 一致**([byte_check.json](byte_check.json))。golden v3 `993276d5e5bb5cbe`/69,978・帰無 `72cb9cd52982da74`/100,439・関係 on `40409ebed834126b`/72,930 はこの中。classical 1,500 体の golden `4f78f3c0`/25,808 は既存のテスト(`tests/engine/test_classical_social.py`)で一致。
2. **通しの時刻 T** を入れた。ループの変数は T(1 日のランでは T = tick)。複数日を回す最小の口 `run_day(sim_days=N)`(mock 用・合成世界だけ)で 2 日を回し、0 日目が 1 日のランと checkpoint まで一致、2 日目に不応期・会話の辺・乱数の鍵・経過時間が正しく続くことを既知の答えで固定した。**型を上げた列は無い**(15 列とも int32=最大 21 億 tick)。
3. **暦の口** `src/shibuya/engine/calendar.py` を作り、暦を引いていた 24 か所のうち 18 か所を付け替えた(#4・#5・#6・#9・#23・#24 の 6 か所は残した=付け替え不要か K7 か資産の再構築が要る=§3)。切替口 `--calendar-weekday {day_index,real}`(既定 `day_index`)。内閣府の祝日 CSV を読み md5 を manifest に書く。開始日の検査(real は止める・day_index は警告)。
4. **応答の遅れ +1**: 艦隊/再生の受け取りを①の直前へ移し、下限を `max(t_apply, tick)` にした。切替口 `--response-delay {1,2}`(既定 1)。偽 vLLM で「T に発射 → T+1 の①で反映」「2 なら T+2」を固定。mock は動かない。
5. **止めた問い 7 件**(§7)。主なもの: 鉄道の時刻表と計画実行層のイベントは指示の「T % 1 日の tick 数で引く」ではなく **0 日目の座標(通しの T)のまま**にした(剰余で引くとラン終端の処理で 0 日目の便が再び着き、既定の結果が動くため)。旧い実 LLM テープは今のプロンプトと 100% テープ外になり、+2 の再生経路を通らない(§5-3)。

## 1. 入れたもの(切替口と既定)

| 入れたもの | 切替口 | 既定 | 旧の挙動を出す値 |
|---|---|---|---|
| 通しの時刻 T(ループの変数・鍵・テープの tick 欄・状態の値は T、日の中の表は `T % 1 日の tick 数`) | `run_day(sim_days=N)`(CLI なし・mock 用) | 1 | 1(1 日のランでは T = tick) |
| 暦の口(曜日・祝日・季節・給料日・営業日・日の鍵) | `--calendar-weekday {day_index,real}` | `day_index` | `day_index` |
| 開始日の欄 | `--start-date YYYY-MM-DD`(`run_day(start_sim_datetime=…)`) | なし=今の導き方(既定の開始日 + day_index、気象の再生実日があればその日) | なし |
| 祝日 CSV の場所 | `--holiday-csv` | `data/calendar/syukujitsu.csv` | —(既定の暦は祝日を見ない) |
| 学校の長期休みの区間 | `--school-holidays YYYY-MM-DD:YYYY-MM-DD,…` | 空 | 空 |
| 応答の遅れ | `--response-delay {1,2}` | 1 | 2 |

- 切替口は `engine.run.add_calendar_args`・`add_fleet_args`(`--response-delay`)で `python -m shibuya.engine.run` と `python -m shibuya.cli` の両方に同じ綴りで入れた。
- `sim_days > 1` は**合成世界(`world_dir=None`)・台帳なし・艦隊なし・再生でない**ランだけ。`ticks` は 1 日の tick 数でなければ止める。1 日のランで `ticks` が 1 日を超えるのも止める(前は黙って回っていた=複数日の扱いが不定だった)。理由: 日の頭の初期化(A11)と日ごとの表の作り直し(10g)が無いので、2 日目からは 0 日目の表を繰り返すだけ。時刻表と計画実行層は 0 日目の座標のまま(§2-3)。これは 10d(再開)の先取りではない(状態を保存せず、同じプロセスで続けるだけ)。
- `fleet_wait_s` の docstring の「本番は 0 でよい」を「本番の運用は 120」に直した(コメントと help だけ)。
- **挙動の変更(検収で指摘・初版に書いていなかった)**: `tick_seconds` が 1 日(86,400 秒)を割り切らないと、`run_day` が暦を作るとき(起動時)に止まる。前は回っていた。既存の呼び手に当たるものは無い(検収役の grep)。

## 2. 通しの時刻 T(A1)

### 2-1 鍵と状態

- `run_day` のループは `for tick in range(total_ticks)`(`tick` が T)。`td = tick % 1 日の tick 数`。1 日のランでは `td == tick`。
- **T で自動的に変わる 17 件**(材料 §2-3 の ●): 呼ごとの乱数 8・salt のハッシュ 6・call_id・テープの鍵・艦隊の seed は、ループの変数がそのまま T になったので**コードの変更なしで T を使う**。テストで確かめたもの: mock の応答の乱数・選び手 `draw_index`・適用順 `apply_key_array` が 2 日目の同じ tick・同じ体で 1 日目と違う / 2 日のテープで (体, T, 級) と call_id が衝突しない・call_id の頭が T。
- **日番号を足した 2 件**(◐): 天気の実日の鍵(`environment.select_day(…, day=)`・型の乱択 `stream(seed, 領域, 日)`)と出勤率の抽選(`presence.attendance_draw(agent, day=, seed=)`)。**0 日目は今の鍵のまま**、1 日目から日番号(と出勤率は seed)を足す。今のランは起動時に 0 日目だけを引く(日ごとの引き直しは 10g)。mock 日課(20)は暦の平日/休日を通した(`rest_day`)。
- tick を値に持つ SoA の 15 列+外の 7 行: ループの T がそのまま書かれる。不応期・「まで」・最後の結果・意図・在席・待ち・乗車待ち・記憶・親しみ・店の記憶・関係辺・顕著行為を見た tick・同席・知人出現・会話の不応期とセッション・アービタの保留が、2 日のランの**毎 tick** で「〜から ≤ T」「〜まで ≤ T + 上限」を満たす(テスト iv)。同席の「相手ごと 1 日 1 本」(`relations.copresent_step` の `day = T × 分 // 1440`)は T で 2 日目に日番号 1 になり、2 日目も辺が書かれる(棚卸し表 4-b の「2 日目以降は同席の辺が 1 本も書かれない」穴が消えた)。

### 2-2 日の中の時刻で引く表(`T % 1 日の tick 数`)

| 表 | 場所 | 変更 |
|---|---|---|
| 計画境界(mock 日課・W17) | `run.py` の `b_start[td]` | T → td |
| 次の予定(活動層・古典・想起優先) | `activity.py` `_next_boundary`・`classical.py` `_next_plan_minutes`・`store_choice.py` `ticks_to_next_plan` | td で引き、活動層はその日の頭を足して T に戻す |
| 範囲外の食事・自宅の食事の予定 | `energy.py` `OutOfAreaMeals.due_with_deferred`・`HomeMeals.due` | td で引く |
| 時別の計数 `(tick // 60) % 24` | `run.py`(起床率・時別の呼数) | td から(値は同じ) |
| 営業時間・食事の窓・語の段・昼夜・天候・補充・清掃・配達・工事・ホテル・催し・騒音・既定の営業時間 | `opening.py`・`energy.py`・`environment.py`・`goods_flow.py`・`logistics.py`・`civic.py`・`world/state.py` など | 変更なし(もとから `% 1440` か `% 24` を取っている=T でも回る) |
| 在圏の計数・計画一致率・規範の計器・想起優先の時別 | `presence.sample`・`norm_meter`・`store_choice` | 変更なし(`% 24`・`% 1440` を取っている) |

### 2-3 T の座標のまま(0 日目の座標)にしたもの(§7 の問い 1・2)

- **鉄道の時刻表**(`rail.py`): `dep_tick`・`enter_tick` は 0 日目の座標のまま、T と直接比べる。0 日目は今と同じ。1 日目からの便は日の頭で張り直す(10g)。それまでは 1 日目以降に新しい便は出ない。
- **計画実行層のイベント**(`presence.py`): 同じ。`0 <= T < ticks` の範囲だけ。
- 理由は §7 の問い 1。どちらも合成世界では動かない(時刻表・W17 が無い)ので、`sim_days > 1` の口(合成世界だけ)では通らない。

### 2-4 型(30 日ぶんの T = 43,200)

| 列 | 型 | 最大 | 判定 |
|---|---|---|---|
| SoA 15 列(`refractory_until`・`activity_until`・`last_result_tick`・`intent_since`・`poi_since`・`queue_since`・`board_since`・`mem_tick`・`mem_last`・`fam_first`・`fam_last`・`sm_first`・`sm_last`・`rel_first`・`rel_last`) | int32 | 2,147,483,647 | 足りる(負の過去 tick=初期辺も表せる) |
| 外: 顕著行為を見た tick・同席の始まり・知人出現の不応期・退出の歩行の始まり・退出を落とす tick | int32 | 同上 | 足りる |
| 外: 同席の最後に書いた日 `_co_day` | int16 | 32,767 日 | 足りる(日番号) |
| 外: 会話・アービタ・出動の保留・退出の締切 | Python の int / int64 | — | 足りる |

**型を上げた列は無い。増えたバイトは 0**。テスト `test_tick_columns_can_hold_30_days_of_T` で固定した(30 日+10 日先・負の値)。

### 2-5 manifest に足した欄(列の追加だけ)

`run_manifest_fields()` に次を足した(ランが書く欄。`cli.checkpoints_payload` の `manifest` にも載る)。

| 欄 | 中身 |
|---|---|
| `tick_seconds` | 1 tick の秒数(既定 60) |
| `start_sim_datetime` | T=0 の世界内日時(ISO。既定のランは気象の再生実日、合成世界は 2026-07-28T00:00:00) |
| `sim_days` | 回した日数 |
| `response_delay` | 応答の遅れの切替口(1/2) |
| `calendar` | `start_sim_datetime`・`tick_seconds`・`ticks_per_day`・`sim_days`・`calendar_weekday`・`day_index`・`holiday_csv`(渡された相対パス)・`holiday_csv_md5`・`holiday_csv_range`・`school_holidays`・`payday_day_of_month`・`days`(日ごとの日付・曜日・祝日名・土休・季節)・`start_check`(day_index での警告の文言) |

## 3. 暦の口と付け替えた 24 か所

`engine.calendar.SimCalendar(start_sim_datetime, tick_seconds, weekday_mode, day_index, holidays, school_holidays, payday_day_of_month)`。主な口: `day_of(T)`・`tick_of_day(T)`・`datetime_of(T)`・`date_of_day(日)`・`weekday(日)`・`is_holiday(日)`・`holiday_name(日)`・`is_rest_day(日)`・`table_weekday(日)`・`day_kind(日)`・`season(日)`・`is_business_day(日)`・`is_payday(日)`・`day_key(日)`・`in_school_holiday(日)`・`check_start(日数)`・`manifest_fields(日数)`。

- `day_index`(既定): 曜日 = `(day_index + 日) % 7`・土休 = 曜日 ≥ 5・**祝日は効かせない**・日の鍵 = `day_index + 日`。付け替えの前の式と同じ値(テストで 15 × 9 通りを照合)。
- `real`: 曜日は開始日の実の曜日、祝日は土休、曜日 7 日の表では祝日を**日曜の行**(親案「祝日は土休扱い」に沿った expedient)、日の鍵 = 日番号。`--start-date` が要る。
- 季節は気象庁の区分(春 3〜5・夏 6〜8・秋 9〜11・冬 12〜2 月)。給料日は既定なし(規則は賃金の段 §6 ⑧)。日を渡したときだけ「毎月その日・土休なら前の営業日へ」(expedient・未リサーチ・今は誰も読まない)。営業日 = 土休でない日(年末年始などの慣行の休みは入れていない=未リサーチ)。

| # | 何を引くか | 前 | 後 |
|---|---|---|---|
| 1 | 世界内日時(プロンプト・記憶の時刻) | `start + timedelta(minutes=t)`(`start` = 再生実日 か 既定の開始日 + day_index) | `calendar.datetime_of(T)` = `start + T × tick_seconds`(開始日の決め方は同じ・`--start-date` を渡せばその日) |
| 2 | 天気の層(平日/土休) | `day_index % 7 >= 5` | `calendar.is_rest_day(日)` |
| 3 | 天気の型と実日の乱択の鍵 | (seed, 0)・(seed, 層名) | (seed, 日)・(seed, 層名[+日])=0 日目は同じ |
| 4 | 日の出・WBGT・暑さ段 | 再生実日の W13 の行 | 変更なし(借りた実日で引く) |
| 5 | プロンプトの天候(B3) | `clock_fn` の日付+時 | 変更なし(§7 の問い 3=K7) |
| 6 | 日陰の格子 | 再生実日 | 変更なし(借りた実日) |
| 7 | 店の営業時間の行列(W7) | `day_index % 7` | `calendar.table_weekday(0)`(runner が渡す) |
| 8 | 閉店中の店の翌日(描画) | `(day_index + 1) % 7` | `calendar.table_weekday(失敗の T の日 + 1)` |
| 9 | 営業時間が無い店の既定 | `tick % 1440` | 変更なし(暦ではない) |
| 10 | 鉄道の平日/土休ダイヤ | `day_index % 7 >= 5` | `calendar.is_rest_day(0)` |
| 11 | 鉄道の域外居住の出発・帰りの便の曜日の行 | `boundary_ticks(day_index)`・`inbound_starts(day_index)` | `boundary_ticks(table_weekday, rest_day=is_rest_day)`・`inbound_starts(table_weekday(0))` |
| 12 | mock 日課の平日/休日 | `day_index % 7 >= 5` | `events_of_day(…, rest_day=calendar.is_rest_day(0))`(agents 層は engine を import できないので値で渡す) |
| 13 | W17 の曜日の行(計画境界) | `boundary_events_full(day_index)` | `calendar.table_weekday(0)` |
| 14 | W17 の初期の活動・拠点セル | `day_index` | `calendar.table_weekday(0)` |
| 15 | 食事・起床の W17 の行 | `day_index` | `calendar.table_weekday(0)` |
| 16 | 計画実行層の W17 の行 | `day_index` | `calendar.table_weekday(0)` |
| 17 | 出勤率の欠席 | `_mix64(agent_id)` | `attendance_draw(agent, day, seed)`(0 日目は同じ) |
| 18 | 古典の事前分布(平日/土曜/日曜) | `day_kind_of(day_index)` | `calendar.day_kind(0)` |
| 19 | 初期の関係辺の「最後の共在」 | `day_index % 7` | `calendar.table_weekday(0)` |
| 20 | 世界過程の日ごとの乱数(顕著行為・出動・催し・入荷・工事・配達) | `day_index` | `calendar.day_key(0)`(day_index モードでは同じ値) |
| 21 | 日次の締め・日次センサス・月次 T3 | `day_index` | `calendar.day_key(最後の日)`(台帳は 1 日のランだけ。月 30 日固定は変えていない) |
| 22 | 給料日 | ランにつながっていない | `calendar.is_payday(日)` の口だけ(既定なし) |
| 23 | (構築)W13 の祝日 | 手書き 2 行 | **変えていない**(§7 の問い 4) |
| 24 | (構築)W7 の祝日 `PH` | 捨てる | **変えていない**(資産が動く)。実行時は `real` の祝日を日曜の行で引く |

付け替えたのは #1・#2・#3・#7・#8・#10〜#21・#22(口)=18 か所(検収で数え直した。初版の「21」は誤り)。残した 6 か所は #4・#5・#6・#9・#23・#24。#4・#6・#9 は暦ではない/借りた実日で引くので付け替え不要、#5 は K7、#23・#24 は構築側(資産の再構築)で次の便。`resolve.initialize(day_index=…)` は引数を受けるが本文で使っていない(材料のとおり)ので触っていない。

## 4. 開始日の検査(A1-1・A1-3)

`SimCalendar.check_start(sim_days)`(`run_day` の起動時・世界を読む前):

| 検査 | real | day_index |
|---|---|---|
| 祝日の表の範囲外の日を含む(1955/1/1〜2027/11/23 の外) | 止める | 止める |
| 祝日の表が読めていない | 止める | 警告(CSV が無い警告 1 回) |
| 0 日目が月曜でない | 止める | 警告 |
| 0 日目が祝日 | 止める | 警告 |
| 複数日が連続する平日に収まらない(土日・祝日を含む) | 止める | 警告 |
| どれかの日が学校の長期休みの区間 | 止める | 警告 |

既定のラン(`day_index=0`・2026-07-28)は警告も出ない(曜日は day_index の約束で月曜・祝日でない・学校の休みの表は空)。

## 5. 応答の遅れ +1(A9)

### 5-1 変えたところ

- 受け取り(④′: 艦隊の `wait_idle`+`poll`・再生の `replay_inbox`)を `_receive_arrivals(tick, floor)` にまとめた。`response_delay=1` は **⓪(知覚の前計算)の後・①(反映)の直前**で `floor = tick`、`2` は旧の位置(会話ターン起床・顕著行為の起床の後・③の前)で `floor = tick + 1`。
- 待ちの位置を⓪の後にしたので、LLM と重ねられる区間は「発射(④)→ 次の tick の 0・⓪a・⓪a-2・⓪」。失うのは ①・②・起床候補の分だけ(材料 §3 の 4)。全体の遅れは実 LLM で測る(推測のまま)。
- mock(`fleet_bridge is None`・`replay_inbox` が空)は `_receive_arrivals` の中で何もしない。byte-check で 19/19 一致(§6)。

### 5-2 偽 vLLM での確かめ([response_delay.json](response_delay.json)・`response_delay_measure.py`)

| | +1(既定) | +2(旧) |
|---|---|---|
| 反映の tick(テスト) | 発射 T → T+1 の① | 発射 T → T+2 の① |
| 受け取り `observed_tick` | T+1 | T+1 |
| 会話ターンの発話の記録の tick − 発射の tick | 1(51 件すべて) | 1(57 件すべて) |
| 会話ターンの呼 / 全呼 | 52 / 414 | 57 / 414 |
| 開いたセッション / 招待 | 6 / 131 | 7 / 138 |
| 未応答の体への再発射(`fleet_resent`) | 0 | 0 |

- **発話の記録の tick は動かない**(受け取った tick=発射 +1 のまま)。動くのは同じ tick の中の順で、+1 では発話の記録が①・②・会話ターン起床より前に来る。会話の数の差(6 と 7)は、反映が 1 tick 早いので軌跡が変わったため(判定しない)。旧の順で心配した「まだ発話していない話者がもう一度起こされる」再発射は、どちらも 0 だった。
- 録画 → 再生は、録画と同じ切替口の値で完全一致(+1・+2 とも・繰り延べつき)。初版では +2 で録ったテープを +1 で再生すると黙って結果が変わった。検収後はテープの脇の meta と突き合わせて止める(§10 P3)。

### 5-3 旧い実 LLM テープ([old_tape_replay_c9b_smoke_s1.json](old_tape_replay_c9b_smoke_s1.json)・`old_tape_replay_check.py`)

- 手元の版 2(`observed_tick` つき)の実テープで小さいもの `c9b-smoke-s1`(5,000 体・35,856 行)を、録ったときの構成(`geometry=edge`・`vocab_version=v2`)で HEAD・作業木 +2・作業木 +1 で再生した。**3 本とも一致**(final `18bea2ea332d1c65`・42,233 呼)。ただし**テープ外が 100%**(42,233 / 42,233)=録った後にプロンプトが変わっていて、`replay_inbox` の経路を 1 回も通らない。+1 でも結果が同じなのはそのため。
- したがって「+2 で旧テープ 17 本の再生が HEAD と一致する」は、今の HEAD では検査にならない(どちらもテープ外で落ちる)。§7 の問い 6。代わりに偽 vLLM の録画 → 再生で +2 の経路を固定した。

## 6. byte-check

- 手順: [wave2 の README](../../wave2-2026-09-30/README.md) と同じ([wave2_bytecheck.py](../../wave2-2026-09-30/wave2_bytecheck.py) の `side`・`compare`)。HEAD `a08109a`(今の HEAD `3342b65` と src・tests は同じ)を `git archive HEAD src docs/bench/anchors docs/design/v2-budget-declaration.md docs/bench/analysis/w6-regen-2026-09-28` で OS の一時ディレクトリへ展開した写しと作業木で、19 構成を mock/classical 5,000 体・seed 1・1 シミュ日・テープつきで回した。旧の切替口を付けた側(`work_old`)は無い(今回の切替口はどれも既定が旧と同じ値か、mock では通らない)。
- 結果: **19/19 一致**(final・呼数・blocks・calls の 14 列)・`src_checks` ok(HEAD 側は写しを読み、作業木側は作業木を読んだ)。[byte_check.json](byte_check.json)。

| 構成 | final | 呼数 |
|---|---|---|
| w6_v3_default(golden v3) | 993276d5e5bb5cbe | 69,978 |
| w6_golden_null_arm(帰無) | 72cb9cd52982da74 | 100,439 |
| v3_mem_rel(関係 on) | 40409ebed834126b | 72,930 |
| v3_classical | 3390e3ec02d392a9 | 97,563 |
| ほか 15 構成 | [byte_check.json](byte_check.json) | |

- classical 1,500 体の golden(`4f78f3c0`・25,808)は既存のテスト `tests/engine/test_classical_social.py` で一致。

```
D=docs/bench/analysis/wave2-2026-09-30
python $D/wave2_bytecheck.py side --src <git archive HEAD の src> --label head --scratch <作業用> --out <作業用>/head.json
python $D/wave2_bytecheck.py side --label work --scratch <作業用> --out <作業用>/work.json
python $D/wave2_bytecheck.py compare --head <作業用>/head.json --work <作業用>/work.json --head-label a08109a --out docs/bench/analysis/wallbounce-1003/10a/byte_check.json
```

## 7. 見つけた問い(止めたもの・親の判断待ち)

1. **鉄道の時刻表を `T % 1 日の tick 数` で引かず、0 日目の座標のまま T と比べた**(指示との食い違い)。剰余で引くと (a) ラン終端の `runner.end_of_day` が最後の発車を流すために `rail.step(T+1)` を呼ぶので、1 日ちょうどのランでは `T+1 = 1,440 → 0` に巻き戻り、ホームへ入る時刻が 0 の便の到着がラン終端でもう一度起きる(既定の結果が動く)(b) 便の同定(乗車中の体の `transit_ref`・混雑・帰りの便の待ち行列)が便の索引なので、日をまたいで同じ索引を繰り返すと前日の便と混ざる。0 日目の座標のままなら 0 日目は今と同じで、日付を越える便も T で続けて走る。1 日目からの便は日の頭で張り直す形(10g)を提案する。時刻表は発車 1〜1,439 分(0 時台の発車が 136 本)・1,440 分以上の行は無い(資産で確認)。
2. **計画実行層のイベント**も同じ理由で 0 日目の座標のまま(`0 <= T < ticks`)。1 日目以降の在圏の出入りは 10g で張り直す。
3. **プロンプトの天候(#5)**: B3 は世界内日時の「日付+時」で W13 を引き、無ければ時だけの表へ黙って落ちる。`--start-date` で W13 の窓の外の日を選ぶと、天気は再生実日のものではなく時だけの表になる(K7 の (a)〜(c) で決める)。今回は直していない。
4. **構築側の #23(W13 の手書きの祝日 2 行)・#24(W7 の `PH`)は変えていない**。#23 は値が CSV と一致する(材料 §2-5)が、変えると次の再構築で資産の注記が変わる。#24 は資産が動く。どちらも版上げ 1 回目(または K7 (b) の W13 の年間化)で付け替えるのがよい。
5. **expedient として入れたもの**(親の確認がほしい): `real` の祝日を曜日 7 日の表で日曜の行にする(W7・古典・W17・関係辺の初期化)/ 給料日の規則「土休なら前の営業日へ」(既定なし)/ 営業日に年末年始を入れない / `day_index` モードの日の鍵を `day_index + 日`(今の値)、`real` を日番号にした(モードを替えると `day_index ≠ 0` のランでは 0 日目の顕著行為・出動などの乱数が変わる)。
6. **旧テープ 17 本の再生の検査**: 今の HEAD ではプロンプトが変わっていてテープ外 100%(§5-3)。「+2 で旧テープの再生が録ったときと一致する」を見るなら、録ったときの commit を `git archive` した写しと作業木 +2 を比べる必要がある(ただし作業木はその後の変更を全部含むので、+2 だけでは一致しない見込み)。どの形で確かめるかの判断がほしい。
7. **tick_seconds が 60 でないラン**: 世界内日時を `start + T 分` から `start + T × tick_seconds` に直した(T と日付の対応を合わせるため)。既定(60)の値は同じ。また `tick_seconds` が 86,400 を割り切らないと起動時に止まるようになった(前は回っていた)。60 でないランは今まで日付と時刻がずれていた(テスト・腕には 60 以外のランは無い)。ほかにも tick = 分の前提の箇所(`(tick // 60) % 24` など)が残っている(棚卸し `tick-constants-inventory.md`)。

## 8. テスト

新しいテスト 4 ファイル・**55 件**(すべて通る)。

| ファイル | 件数 | 中身 |
|---|---|---|
| `tests/engine/test_calendar.py` | 17 | 祝日 CSV(「休日」の行 2026/5/6・9/22・md5・範囲・形の違うファイルで止める・無いとき警告 1 回・本物の CSV の md5 と 2026 年の 18 行)/ 2026-07-28 は火曜 / day_index モードが旧い式と同じ値(15 × 9 通り)/ T と日時 / 季節 / 給料日 / 開始日の検査(月曜・祝日の月曜・日曜・土曜を含む 6 日・9/21〜22 を含む・範囲外 2 通り・学校の休み)/ day_index は警告だけ・範囲外は止める / 学校の休みと開始日の書式 / manifest の欄 |
| `tests/engine/test_sim_time_T.py` | 17 | 2 日のランの 0 日目が 1 日のランと一致(既定・全腕・古典)・2 日目の朝にも呼 / テープと call_id が T / (i) 23:50 の 20 分の不応期が 2 日目 0:10 に切れる(0:09 は抑止)/ (ii) 23:00 の会話の辺が 2 日目 1:00 に 120 分 / (iii) 2 日目の乱数が違う / (iv) 全腕の 2 日ランの毎 tick で経過時間が負にならない(SoA 15 列+外の行・2 日目にも書かれている・同席が 2 日目にも書かれる)/ 型(30 日の T)/ 日の中の表(活動層・古典・想起優先・範囲外の食事)/ 複数日の口の制限 / manifest の欄 / real の開始日 / 開始日でプロンプトの日付が動く / 学校の休みは day_index で警告 |
| `tests/engine/test_response_delay.py` | 8 | 艦隊 +1 / +2 の反映の tick / mock は切替口に依らず同じで既に +1 / 録画 → 再生が +1・+2 それぞれで一致 / +2 のテープを +1 で再生すると変わる / 会話の発話の記録は受け取った tick(+1・+2) |
| `tests/engine/test_calendar_sites.py` | 13 | 天気の実日の鍵(0 日目は旧い式と同じ・1 日目から変わる)/ 世界過程(day_index 0・4・5・6・9 で旧い値・real の祝日)/ mock 日課の rest_day / 閉店中の店の翌日(day_index・2 日目・土曜・real の祝日)/ 出勤率の抽選 / CLI の切替口 / `shibuya.cli.main` が切替口を受ける / 鉄道の平日/土休ダイヤ(実の資産があるときだけ) |

関係する既存のテスト(`tests/engine`・`tests/agents`・`tests/world`・`tests/perception`・`tests/test_cli.py`・`tests/test_manifest_roundtrip.py`)も回した。落ちたのは 1 件(`test_stage3_small_fixes.py::test_the_engine_lookup_reads_the_w7_opening_matrix_q25`=`_named_closed_lookup` に旧い口の整数 `day_index` を渡す)で、テストは変えずに関数側で整数を `SimCalendar.legacy` に包む形にして通した。全体のテストは親が回す。

## 9. 変えたファイル

- 新規: `src/shibuya/engine/calendar.py` / tests 4 本(§8)/ 記録 `docs/bench/analysis/wallbounce-1003/10a/`(本書・`byte_check.json`・`response_delay.json`・`response_delay_measure.py`・`old_tape_replay_c9b_smoke_s1.json`・`old_tape_replay_check.py`)。
- 変更: `src/shibuya/engine/run.py`(T のループ・暦の口・開始日・manifest・受け取りの関数・切替口と CLI)/ `src/shibuya/cli.py`(切替口)/ `src/shibuya/engine/processes/runner.py`・`environment.py`・`rail.py`(暦の口)/ `src/shibuya/engine/presence.py`(出勤率の鍵・暦の曜日)/ `src/shibuya/engine/energy.py`・`activity.py`・`classical.py`・`store_choice.py`(日の中の tick で引く)/ `src/shibuya/agents/schedule.py`(`rest_day`)。

## 10. 検収後の直し(`../review-10a.md`・2026-10-03)

検収(別のサブ): 結果を動かす欠陥 0・byte-check 7/7 一致。潜在の欠陥 5・記録の誤り 3・テストの欠け 6 を直した。

| # | 指摘 | 直し | テスト(`tests/engine/test_10a_review_fixes.py` ほか) |
|---|---|---|---|
| P1 | 開始日の検査が、気象の再生実日へ置き換える前の暦(既定の開始日 + day_index)を見ていた | `check_start` を `calendar.with_start(world_start)` の後へ移した。manifest の `calendar.start_check` と `start_sim_datetime` が同じ日を見る | 再生実日を差し込んだ合成世界のランで、検査が置き換えた後の日(2026-07-22)を見る・置き換える前の日では警告しない |
| P2 | 0:00 でない開始時刻を受けていた | `SimCalendar.__post_init__` で 0:00 ちょうどでなければ `ValueError`(tz の有無は問わない) | 09:00・0:00:01 は止まる・0:00 と tz つきの 0:00 は通る・`run_day` でも止まる |
| P3 | 応答の遅れの値を再生で突き合わせていなかった(逆の値で再生しても黙って回り、テープ外 0 のまま結果が違った) | テープの脇の meta `run_meta.json`(`TapeWriter(run_meta=…)`・`Tape.run_meta`・`read_run_meta`)に `response_delay` を書く。**テープの版と calls.parquet の列は変えない**。再生ではテープの値と設定が違えば `ValueError`(文言に両方の値)。値の無いテープ(10a より前の録画)は 2 とみなし `ResponseDelayWarning` を 1 回出す。`run_day(response_delay=None)`・`--response-delay` の既定を「未指定」にし、未指定なら録画・mock は 1、値の無いテープの再生は 2 | +1 で録って +2 で再生 → 止まる / +2 で録って +1 で再生 → 止まる / 値の無いテープを既定で再生 → 2 で回り final が録画と一致・警告 1 回(2 回目は出ない)/ 値の無いテープを 1 で再生 → 止まる / meta は parquet に触らない |
| P4 | 祝日 CSV の相対パスが作業ディレクトリから解決されていた。読めないとき manifest は `""`・`[]` | 相対パスはリポの根から(`calendar.resolve_repo_path`・manifest には渡された文字列)。読めないとき `holiday_csv_md5`・`holiday_csv_range` を `null`。real は「祝日の表が読めていない」で止める(前から) | 作業ディレクトリをリポの外にしても読める / 無いパス+real → 止まる / 無いパス+day_index → 警告と null / 範囲外の開始日も読めない時点で real は止まる |
| P5 | 給料日の前営業日への寄せが月をまたぐ分を落としていた | その日が「当月の給料日の寄せ先」か「翌月の給料日の寄せ先」なら給料日 | `payday_day_of_month=1`・real・2026-07〜10: 07-01・07-31・09-01・10-01 **と 10-30**(下の問い) |
| R1 | HEAD の表記 | `3342b65`(src・tests は `a08109a` と同じ)と書いた | — |
| R2 | 付け替えの数 | 18 か所(残した 6 か所を列挙)・`run_day` の docstring の「22 か所」も 18 に | — |
| R3 | `tick_seconds` が 1 日を割り切らないと止まる変更が未記載 | §1 と §7-7 に書いた | — |
| T1 | +2 の経路を HEAD の値に固定するテストが無い | HEAD の写しで取った final を定数にした。構成: 偽 vLLM(`pair_talk`)・合成世界 2 セル・200 体 × 600 tick・`fleet_wait_s=10`・stub・過程なし(検収役の構成は記録から再現できなかったので、指示どおり自分の構成で HEAD の写しから取った)。HEAD `79821d778ea4addf`=作業木 +2(+1 は `066ada7a8421b620`)。旧の位置の下限を `tick + 1` → `tick` に壊すと `04d46ddbac3d6e76` になり落ちることを確かめた | `test_plus2_path_reproduces_the_head_final` |
| T2 | `tick_seconds=30` の世界内日時 | — | `datetime_of(90) = start + 45 分` |
| T3 | real の `day_key` | — | real は日番号・day_index は `day_index + 日` |
| T4 | real の土日・祝日の mock ランで `rest_day` が mock 日課へ渡るか | — | 8/8(土)・8/9(日)・8/11(山の日)は `rest_day=True`、8/10(月)は False(real の開始日の検査は検査だけを空にして回す) |
| T5 | `HomeMeals.due` の `T % 1 日の tick 数` | — | 最小の W17(1 体・自宅の食事 1 行)で 2 日目の同じ時刻に同じ行が出る |
| T6 | 季節の 8 月 | — | 8 月は夏・9/1 は秋 |

**問いへの親の答えの反映**: Q1(鉄道と計画実行層は 0 日目の座標のまま・10g で張り直す)= §7 の 1・2 のまま。Q2 = 上の P3。Q3 会話の招待・p_see・p_notice・艦隊の seed の 4 件が 2 日目に T を鍵にしているかは、10g の世界資産の 2 日ランで確かめる(今の 2 日の口は合成世界・艦隊なしなので、少なくとも艦隊の seed は通らない。残り 3 件がどれだけ通るかは数えていない)。Q4 `tools/c7/seed_exchangeability.py` の「seed が違えば違って当然の欄」(`ALLOWED_DIFF`)には足していない。新しい欄のうち `tick_seconds`・`sim_days`・`response_delay`・`calendar` の構成の欄は seed 間で同じでなければならない(違えば構成が違う=「未説明」で正しい)。seed で変わりうるのは `start_sim_datetime`・`calendar.start_sim_datetime`・`calendar.days`(気象の再生実日から決まる)だけで、元の `replay_date` も一覧に無い(再生実日が seed 間で違えば今も「未説明」になる)。この扱いは `replay_date` と揃えて親が決めるのがよい(注意として書くだけにした・`tools/` は触っていない)。

**新しく出た問い(1 件)**: P5 の検算は「2026-07〜10 の給料日は 4 日」だったが、規則どおりだと 11/1(日)の給料日が前の営業日 10/30(金)へ寄るので、10 月の中に 5 日目(10-30)が入る。規則(当月か翌月の寄せ先)は指示のとおりにしてあり、テストは 5 日で固定した。検算の範囲を 10/1 までと読むなら 4 日で一致する。どちらの読みか確認がほしい。→ **親の答え(10-03)**: 規則どおりの 5 日(10-30 を含む)で正しい(検算の 4 日は 11/1 の寄せの見落とし)。Q4 の `ALLOWED_DIFF` は足さないまま・`replay_date` と揃える扱いは 10f で決める。

**§5-3 の旧テープの再生(`old_tape_replay_check.py`)への影響**: `c9b-smoke-s1` には meta が無いので、検収後は「2 とみなす」になり、`--delay 1` で回すと止まる(P3 の想定どおり)。§5-3 の数字は直しの前に取ったもの。

**byte-check(直しの後)**: 既定 v3・帰無・関係 on の 3 本を HEAD の写しと比べて **3/3 一致**(final・呼数・blocks・calls の 14 列・`src_checks` ok)。[byte_check_after_review.json](byte_check_after_review.json)。

**変えたファイル(直しの分)**: `src/shibuya/engine/calendar.py`(P2・P4・P5)/ `src/shibuya/engine/tape.py`(テープの脇の meta)/ `src/shibuya/engine/run.py`(P1・P3・CLI の既定・docstring)/ tests: `test_10a_review_fixes.py`(新規)・`test_response_delay.py`(逆の値の再生は止まる)・`test_calendar_sites.py`(CLI の既定は未指定)/ 記録: 本節・`byte_check_after_review.json`。
