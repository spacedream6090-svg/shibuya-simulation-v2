# 10a の検収(通しの時刻 T・暦の口・応答の遅れ +1)

> 検収役(Opus 5.5・実装役とは別の人)の記録。2026-10-03。何も直していない。
> 基準: `git archive HEAD`(HEAD=3342b65)を OS の一時ディレクトリに展開した写し。比べる相手: 作業木(10a の実装入り)。
> 壊して捕まるかの試験は、作業木の src・tests を一時ディレクトリに写した上で行い、1 件ごとに元に戻した(最後に作業木と差が無いことを確認)。
> 検算のスクリプト(byte-check・鍵の計数・+1 の照合・暦の境界)は一時ディレクトリに置いた。リポには残していない。

## 0. まとめ

| 種類 | 件数 |
|---|---|
| 結果を動かす欠陥 | 0 |
| 潜在の欠陥 | 5 |
| 記録の誤り | 3 |
| テストの欠け | 6 |
| 問い | 4 |

- **byte-check は一致**。自分のスクリプトで 7 構成(既定 v3・帰無・関係 on・15 腕から 3 本・古典+記憶+関係)を HEAD の写しと作業木で回し、final・呼数・checkpoint の全点・テープの全列(blocks 3 列・calls 14 列)が 7/7 で一致した。実装役の `10a/byte_check.json` の値とも一致。classical 1,500 体の golden(`4f78f3c0`/25,808)も既存のテストで一致。
- 艦隊(偽 vLLM)でも、作業木の `response_delay=2` は HEAD と final が一致する(会話あり・なしの 2 本・録画と再生の両方)。
- 壊して捕まるか: 発注文の 8 件は全部捕まった。自分で足した 24 件のうち 6 件が捕まらなかった(§4)。

## 1. byte-check の数え直し

手順: 実装役の `wave2_bytecheck.py` は使わず、自分のスクリプトで `shibuya.cli.run(n_agents=5000, seed=1, world_dir="data/world/v2", tape_path=…)` を構成ごとに別プロセスで回した。HEAD 側は `PYTHONPATH` を写しの src に向け、読んだ `shibuya` の場所を出力に入れて写しを読んだことを確かめた。比べた値: final・呼数・checkpoint の (tick, combined) 全点の sha・`blocks.parquet` と `calls.parquet` の行数と全列の sha。

| 構成 | HEAD final / 呼数 | 作業木 final / 呼数 | 全列 | 実装役の記録 |
|---|---|---|---|---|
| 既定 v3(golden) | 993276d5e5bb5cbe / 69,978 | 同じ | 一致 | 一致 |
| 帰無(golden_null_arm) | 72cb9cd52982da74 / 100,439 | 同じ | 一致 | 一致 |
| 関係 on(v3_mem_rel) | 40409ebed834126b / 72,930 | 同じ | 一致 | 一致 |
| v3_activity_off | f746406eb78b024a / 58,570 | 同じ | 一致 | 一致 |
| old_v2_edge | cf01958883d07209 / 54,170 | 同じ | 一致 | 一致 |
| v1_edge_plateau | e32d69e91ff45e66 / 55,173 | 同じ | 一致 | 一致 |
| v3_classical_mem_rel | 28ea80375e7ee646 / 110,395 | 同じ | 一致 | 一致 |

- classical 1,500 体: `tests/engine/test_classical_social.py -k "golden or 1500"` が作業木で通る(`4f78f3c0…`/25,808)。
- 艦隊の +2 と HEAD(偽 vLLM・`fleet_wait_s=10`・合成世界 30 tick と会話の世界): HEAD `8e00aeb3bf157073`・`141c408c6a4dc3ff` / 作業木 +2 同じ / 作業木 +1 `2a24815a364887f4`・`29aebf0b1b1d2056`。録画 → 再生はどれも録画と一致。

## 2. 指摘

### 2-1 結果を動かす欠陥

なし(既定のランは上の通り 1 バイトも動いていない)。

### 2-2 潜在の欠陥

**P1 開始日の検査が、再生実日に置き換える前の日付で走る**
- 根拠: `src/shibuya/engine/run.py:2068-2083` で暦を `DEFAULT_START_DATETIME + day_index 日` で作って `check_start` を走らせ、その後 `run.py:2417-2426` で開始日を気象の再生実日に置き換える(`with_start`)。manifest の `start_sim_datetime`・`calendar.days[].date` は置き換えた後の日、`calendar.start_check` の文言は置き換える前の日を書く。
- 再現(`run_day(n_agents=50, seed=1, world_dir="data/world/v2", ticks=5, day_index=d)`):

| day_index | 再生実日(manifest の日付) | 検査が見た日 |
|---|---|---|
| 0 | 2026-07-28 | 2026-07-28 |
| 1 | 2026-07-28 | 2026-07-29 |
| 4 | 2026-07-28 | 2026-08-01 |
| 5 | 2026-08-08 | 2026-08-02 |

- 影響: day_index モードは警告だけなので結果は動かない。ただし同じ manifest の中で日付が 2 つになり、再生実日が祝日(W13 の窓の 8/11 山の日)に当たっても「0 日目が祝日」の警告は出ない。real モードは開始日を必須にしているので食い違わない。

**P2 0:00 でない開始時刻を黙って受ける**
- 根拠: `calendar.py:188-203` の `parse_start` は ISO の日時(時刻つき)を受け、`SimCalendar.__post_init__`(`calendar.py:253-259`)は時刻を検査しない。`run_day(start_sim_datetime=…)` は `datetime` も文字列も受ける。
- 再現: `SimCalendar(datetime(2026, 8, 3, 9, 0))` で `datetime_of(0)=09:00`・`tick_of_day(0)=0`・`day_of(900)=0` なのに `datetime_of(900)=2026-08-04 00:00`。
- 影響: 日の中の表(計画境界・食事・営業時間の `T % 1 日の tick 数`)は T=0 を 0:00 として引き、プロンプトの時計と天候(`renderer.py:620-628` の `when.hour`)は 9:00 から数える。9 時間ずれた世界が警告なしに回る。0:00 以外を止めるか、日の頭のずれを T に足す決めが要る。

**P3 応答の遅れの値がテープに残らず、違う値で再生しても止まらない**
- 根拠: テープは版 3 のまま(`src/shibuya/engine/tape.py:90-127`)で、遅れの値を持たない。`observed_tick` は +1 と +2 で同じ(受け取りは T+1)。
- 再現(偽 vLLM・合成世界 150 体・30 tick): +1 で録ったテープを +2 で再生、+2 で録ったテープを +1 で再生すると、どちらも反映の列と final が録画と違うのに `tape_miss_count=0`(落ちず・警告も無い)。
- 影響: 既定が 1 になったので、10a より前に艦隊で録ったテープを既定のまま再生すると黙ってずれる。実装役の記録 §5-3 の通り今の旧テープは 100% テープ外で落ちるので、いまは表に出ない。

**P4 祝日 CSV が無いと、day_index モードの範囲外の検査が黙って抜ける**
- 根拠: `calendar.py:384-391` は表が読めたときだけ範囲を見る。警告は `load_holidays` の 1 回だけで(`calendar.py:139-164`・プロセスの中で同じパスは 2 回目から無言)、`check_start` は何も言わない。既定の場所は作業ディレクトリからの相対(`calendar.py:70`)。
- 再現: `SimCalendar(datetime(2030, 1, 7), holidays=load_holidays("no/such.csv")).check_start(1)` は `[]`(止まらない)。同じ日付で CSV ありなら止まる。
- 影響: 既定の暦は祝日を使わないので結果は動かない。ただし作業ディレクトリが違うだけで manifest の `holiday_csv_md5`・`holiday_csv_range` が空になり、範囲外の開始日も素通りする。`tools/c7/seed_exchangeability.py` は manifest の差を数えるので、同じ構成のランが「説明の無い差」になりうる。

**P5 給料日を前の営業日へ寄せると、月をまたぐ分が落ちる**
- 根拠: `calendar.py:337-350` は「その日の月」の給料日だけを求めて比べる。翌月 1 日が土休で前月末へ寄るとき、前月末の日はその月の給料日(前月 1 日)と比べるので一致しない。
- 再現: `SimCalendar(datetime(2026, 7, 1), weekday_mode="real", holidays=…, payday_day_of_month=1)` で 2026-07〜10 月の給料日は `07-01・09-01・10-01` の 3 日。8/1(土)の分(7/31 になるはず)が無い。
- 影響: 既定は給料日なしで、今は誰も読まない。賃金の段でつなぐ前に直す必要がある。

### 2-3 記録の誤り

**R1 HEAD の commit を `a08109a` と書いている**: README §0-1・§6、`byte_check.json` の `"head"`。今の HEAD は 3342b65。`git diff --stat a08109a 3342b65 -- src tests` は空なので、数値はそのまま有効。

**R2 付け替えた箇所の数が 3 通りある**: README §0-3 と §3 は「21 か所を付け替え・残り 3 か所」。§3 の列挙(#1・#2・#3・#7・#8・#10〜#21・#22)は 18 か所で、付け替えていないのは #4・#5・#6・#9・#23・#24 の 6 か所。`run.py` の `run_day` の docstring(`calendar_weekday` の説明)は「曜日・土休・祝日を引く 22 か所は暦の口を通す」。表の中身(どこを付け替え、どこを残したか)は grep の結果と合っている(§3)。

**R3 書かれていない挙動の変更が 1 つある**: `tick_seconds` が 1 日(86,400 秒)を割り切らないと、`run_day` が起動時に止まるようになった(`calendar.py:103-111`。`run_day` が暦を作るとき)。前は回っていた。既存の呼び手に当たるものは無かった(grep)が、README §1・§7-7 に書かれていない。

### 2-4 テストの欠け

壊して捕まるかの全表は §4。捕まらなかったものと、見ていない筋:

**T1 +2 の経路を HEAD の値に固定するテストが無い**
- 再現: 旧の位置の受け取りの下限を `tick + 1` から `tick` に変える(`run.py:3203`)。新しいテスト 55 件はすべて通る。ところが偽 vLLM の会話の世界では final が HEAD と違う(HEAD・作業木 +2 = `141c408c6a4dc3ff`、変えたもの = `c4cfa4dd09f32e87`)。下限は反映の tick を変えないが、適用順の鍵(`apply_key_array` の t_apply)を変える。
- 今のテスト(`test_record_and_replay_match_under_each_delay`・`test_replay_with_the_other_delay_diverges`)は同じコードの録画と再生を比べるだけ。旧テープの再生を守る経路なので、HEAD の final を既知の答えとして固定する試験が要る。

**T2 `tick_seconds` が 60 でないときの世界内日時が固定されていない**: `datetime_of` を `start + T 分` に戻しても捕まらない(§7-7 の変更)。`test_T_and_datetime` は 60 の値だけを見て、30 では `ticks_per_day` しか見ていない。60 のランの日時が 1 分もずれないことは、byte-check の prompt_hash 一致で確かめた。

**T3 real モードの日の鍵(`day_key`)**: real でも `day_index + 日` を返すように変えても捕まらない(`calendar.py:356-364`)。

**T4 mock 日課への `rest_day` の結線**: `run.py` で `events_of_day` に `rest_day` を渡すのをやめても捕まらない。テストは `MockWeeklySchedule` の単体だけで、real モードの土日・祝日の日の mock ランを見ていない。

**T5 自宅の食事(`HomeMeals.due`)の `T % 1 日の tick 数`**: 外しても捕まらない(`energy.py:772`)。範囲外の食事だけが検査されている。

**T6 季節の 8 月**: 8 月を秋に変えても捕まらない(テストは 2・3・5・6・9・12 月)。軽い。

### 2-5 問い

**Q1 鉄道の時刻表と計画実行層を 0 日目の座標のままにした件(README §7-1・§7-2)**: 既定の 1 日のランで不変なことは byte-check で確かめた。`sim_days=2` は合成世界に限られ、そこでは時刻表も計画実行層も動かないので、2 日目の破綻は「起きない」のではなく「通らない」。守りは複数日の口の制限だけで、これはテスト(`test_multi_day_mouth_refuses_what_needs_the_day_head`)で固定されている(制限を外すと捕まる)。10g まではこの形でよいか。

**Q2 P3 の扱い**: 遅れの値をテープ版 4(K1)の欄に入れるか、再生のときに manifest と突き合わせて違えば止めるか。

**Q3 合成世界では確かめられない鍵が 4 件ある**: 2 日のランで鍵に入る値を数えた(§3-2)。会話の招待・注意の p_see・p_notice・艦隊の seed は合成世界の 2 日のランでは 1 回も呼ばれない。どれもループの `tick`(=T)をそのまま渡しているのはコードで確かめた。世界資産での 2 日のランは 10g の後で確かめるのでよいか。

**Q4 manifest に足した欄**: 既定のランの final とテープには混ざっていない(byte-check)。`run_manifest_fields` の値をハッシュする箇所は src に無い(G-5 の `manifest_sha256` は文書の上だけ)。ただし `tools/c7/seed_exchangeability.py` は manifest の差を数えるので、10a より前のランと後のランを比べると新しい欄が「説明の無い差」として出る。同じコードどうしの比べ方だけに使うなら問題は無い。等価の指定(`parse_equivalents`)を足すか。

## 3. 確かめたこと(指摘なし)

### 3-1 24 か所の付け替えの網羅(grep)

- `src/shibuya`(build を除く)で `day_index`・`% 7`・`weekday()` を grep した。残っている `% 7` は、暦の口が渡した曜日を表の中で引く箇所だけ(`opening.py:82`・`relations.py:306,328`・`energy.py:220,574`・`classical.py:233` の `day_kind_of` は run から呼ばれなくなりテストだけが使う・`schedule.py:142` は `rest_day` が無いときの旧い口)。
- 世界過程の日ごとの乱数(顕著行為・出動・催し・入荷・工事・配達)は `runner.py` から `day_key` を受ける。W7 は `table_weekday(0)`。鉄道は `is_rest_day(0)` と `table_weekday(0)`。どれも README §3 の表と合う。
- 付け替えていない 6 か所(#4・#5・#6・#9・#23・#24)は README の理由の通り。`resolve.initialize(day_index=…)` は本文で使っていない。

### 3-2 日番号の無い鍵が T で変わるか(2 日の合成世界ラン)

`run_day(n_agents=100, n_cells=16, ticks=1440, sim_days=2, budget=100)` を全腕(語彙 v3・記憶・関係・店の記憶・親しみ・エネルギー・同席)と古典+全腕で回し、乱数と salt の関数を包んで、鍵に入った tick の値を数えた。

| 鍵 | 全腕: 呼ばれた回数 / 2 日目(T ≥ 1,440)の回数 / 最大の T | 古典 |
|---|---|---|
| llm.mock(棚卸し #1〜3) | 2,424 / 1,202 / 2,877 | なし |
| policy.classical(#4) | なし | 4,089 / 2,166 / 2,871 |
| engine.chooser(#5) | 311 / 152 / 2,740 | なし |
| salt pk(#9) | 627 / 305 / 2,871 | 205 / 100 / 2,868 |
| salt ak(#10) | 1,417 / 732 / 2,878 | 1,878 / 996 / 2,872 |
| salt wk(#11) | 1,591 / 828 / 2,877 | 1,878 / 996 / 2,871 |
| salt wd(#12) | 747 / 429 / 2,860 | 610 / 393 / 2,877 |
| salt ri・ri\|rest(#13・#14) | 3 / 3 / 2,044 | なし |
| call_id・テープの鍵(#15・#16) | 2 日目の行 1,202・call_id の頭が T・鍵の衝突なし | 2 日目の行 2,166 |

- 2 日目に T(≥ 1,440)が入っていることを 12 件で確かめた。確かめられないもの 4 件(会話の招待 #6・p_see #7・p_notice #8・艦隊の seed #17)は Q3。
- ◐ の 2 件(天気の実日・出勤率)は 0 日目は旧い鍵のまま・1 日目から変わることをテストが固定している(壊すと捕まる・§4 の X1・X2)。

### 3-3 既定が不変か

- `--calendar-weekday` の既定は `day_index`(`run.py` の `add_calendar_args`)、`run_day` の既定も `day_index`。`--response-delay` の既定は 1。
- mock: `_receive_arrivals` は `fleet_bridge is None` かつ `replay_inbox` が空なら何もしない。byte-check で確かめた。
- 既定のランの manifest(v2 世界・300 体): `start_sim_datetime=2026-07-28T00:00:00`・`tick_seconds=60`・`sim_days=1`・`response_delay=1`・`holiday_csv_md5=733fabb6b488794a0cd3d94df4b1f24a`・`start_check=[]`・暦の警告なし。
- `sim_days` の口: 既定 1 では `total_ticks = ticks`。新たに `ticks > 1 日` で止める(README §1 の通り)。`ticks` が 1,440 を超える呼び手は src・tools・tests・scripts に無かった。

### 3-4 +1 の正しさ(自分のモックで別の角度から)

艦隊の `poll` を包んで受け取った応答ごとに (受け取った tick, 体, 発射の tick, レーン) を控え、①の反映(`intents_from_responses`)と「反映の tick = max(発射 + δ_think(レーン), 受け取り + (遅れ − 1))」を照合した(偽 vLLM・合成世界 150 体・30 tick・seed 3)。

| | +1 | +2 |
|---|---|---|
| 受け取り − 発射 | 1(150 件すべて) | 1(150 件すべて) |
| 反映の列と式 | 一致 | 一致 |
| 同じ値で再生 | 反映の列・final とも一致 | 一致 |
| 逆の値で再生 | 違う(tape_miss 0)| 違う(tape_miss 0)|
| 会話: 発話の件数・セッション | 51・6 | 57・7 |
| 会話: 発話の tick − 発射の tick | 1(51 件) | 1(57 件) |

- 発話の記録の tick は受け取った tick で、+1 と +2 で動かない。実装役の記録(51/57 件・6/7 セッション)と同じ数になった。
- このランのレーンはすべて L1 だった(δ_think が 2 以上のレーンは通っていない。式は max を取るので L2・L3 でも反映が早まることは無い)。

### 3-5 実装役の止めた問い(README §7)の読み

- 1・2(0 日目の座標): Q1。
- 5(expedient): 祝日を日曜の行にする・`real` の日の鍵は、どちらも `weekday_mode == "real"` のときだけ効く(`calendar.py:313-327,356-364`)。既定で効いていないことは byte-check で確かめた。
- 7(`tick_seconds ≠ 60`): 60 では `start + T × 60 秒 = start + T 分` で同じ値(prompt_hash 一致)。60 以外はテストで固定されていない(T2)。

### 3-6 境界

- 日の切り替わり(T=1,439 → 1,440): `td` は 0 に戻り、不応期・会話の辺の経過時間は実装役のテスト (i)(ii) で固定されている。
- T の型: SoA の 15 列は int32、`_co_day` は int16(`relations.py:939`)。30 日で足りる(テストあり)。
- tz つきの開始日(`+09:00`): `datetime_of(1440)` は翌日 0:00+09:00、曜日と検査は日付から引き、問題は出なかった。
- 祝日が月曜の週: 2026-09-21(敬老の日)を real の 2 日ランの開始にすると「0 日目が祝日」「連続する平日に収まらない」の 2 つで止まる。
- CSV の範囲外: CSV があれば day_index でも止まる。CSV が無いと抜ける(P4)。

## 4. 壊して捕まるか(新しいテスト 4 本・55 件)

1 か所ずつ書き換えて新しいテスト 4 本を回し、元に戻した。「捕まえたテスト」はファイル名を省いた関数名。

| # | 壊し方 | 結果 | 捕まえたテスト |
|---|---|---|---|
| M1a | ループの T から日を落とす(`tick = tick % 1 日`) | 捕まった | test_day0_of_a_two_day_run_is_the_one_day_run ×3・test_tape_and_call_keys_use_T・test_no_negative_elapsed_time_in_any_tick_column_every_tick |
| M1b | `day_of(T)` を常に 0 | 捕まった | test_T_and_datetime・test_named_closed_next_day_comes_from_the_calendar |
| M1c | 活動層の次の境界で日の頭を足さない | 捕まった | test_next_boundary_tables_are_read_by_tick_of_day |
| M2 | 祝日の読み込みを常に空 | 捕まった | 14 件(test_holiday_rows_named_kyujitsu_are_holidays ほか) |
| M3 | `--calendar-weekday` の既定を real | 捕まった | test_cli_switches_and_defaults |
| M4 | 下限を `tick + 1` に戻す | 捕まった | test_fleet_call_fired_at_T_is_applied_at_T_plus_delay[1]・test_replay_with_the_other_delay_diverges |
| M5 | 受け取りを①の前から外す(+1 では受け取らない) | 捕まった | test_fleet_call_fired_at_T_is_applied_at_T_plus_delay[1]・test_utterances_are_recorded_at_the_receiving_tick[1] |
| M5b | 受け取りを旧の位置へ戻し、下限は `tick` のまま | 捕まった | test_fleet_call_fired_at_T_is_applied_at_T_plus_delay[1]・test_replay_with_the_other_delay_diverges |
| M6 | 範囲外の開始日の検査を外す | 捕まった | test_start_check_known_dates・test_day_index_mode_only_warns_but_still_stops_out_of_range |
| M7 | `td = tick` | 捕まった | M1a と同じ 5 件 |
| M8 | 開始日の「月曜」を「火曜」に | 捕まった | test_start_check_known_dates・test_day_index_mode_only_warns_but_still_stops_out_of_range・test_manifest_records_tick_seconds_and_start・test_real_calendar_run_needs_a_valid_start |
| X1 | 天気の実日の鍵に日を足さない | 捕まった | test_weather_day_key_is_unchanged_on_day0_and_moves_from_day1 |
| X2 | 出勤率の抽選に日を足さない | 捕まった | test_attendance_draw_keeps_day0_and_moves_from_day1 |
| X3 | 閉店中の店の翌日を失敗の日から数えない | 捕まった | test_named_closed_next_day_comes_from_the_calendar |
| X4 | real の土休に祝日を入れない | 捕まった | test_real_weekday_and_holidays ほか 2 件 |
| X5 | real の祝日を日曜の行にしない | 捕まった | test_real_weekday_and_holidays ほか 2 件 |
| X6 | real の日の鍵を `day_index + 日` に | **捕まらない** | なし(T3) |
| X7 | CSV が無い警告を毎回出す | 捕まった | test_missing_csv_gives_an_empty_table_and_warns_once |
| X8 | 世界内日時を `start + T 分` に戻す | **捕まらない** | なし(T2) |
| X9 | 旧の位置の下限を `tick` に(+2 の経路) | **捕まらない** | なし(T1。HEAD と final が違う) |
| X10 | 再生の下限を常に `tick + 1` | 捕まった | test_record_and_replay_match_under_each_delay[1]・test_replay_with_the_other_delay_diverges |
| X11 | 範囲外の食事の `% 1 日` を外す | 捕まった | test_out_of_area_meals_repeat_by_tick_of_day |
| X12 | 自宅の食事の `% 1 日` を外す | **捕まらない** | なし(T5) |
| X13 | 古典の次の予定で `td` を使わない | 捕まった | test_classical_and_store_choice_read_the_next_plan_by_tick_of_day |
| X14 | 想起優先の次の予定で `td` を使わない | 捕まった | 同上 |
| X15 | real の規則違反を警告だけに | 捕まった | test_start_check_known_dates・test_real_calendar_run_needs_a_valid_start |
| X16 | mock 日課に `rest_day` を渡さない | **捕まらない** | なし(T4) |
| X17 | 世界過程の日の鍵を曜日に | 捕まった | test_runner_keeps_the_old_values_in_day_index_mode[9]・test_runner_reads_the_real_calendar |
| X18 | 鉄道のダイヤを `day_index % 7` の直読みに戻す | 捕まった | test_rail_timetable_kind_comes_from_the_calendar |
| X19 | 複数日の口の制限(世界資産・台帳・艦隊・再生)を外す | 捕まった | test_multi_day_mouth_refuses_what_needs_the_day_head |
| X20 | 1 日を超える `ticks` を許す | 捕まった | 同上 |
| X21 | 給料日を前の営業日へ寄せない | 捕まった | test_payday_is_off_by_default_and_moves_to_the_previous_business_day |
| X22 | 8 月を秋に | **捕まらない** | なし(T6) |
| X23 | CSV の日付の昇順の検査を外す | 捕まった | test_bad_files_stop |

## 5. 再検収(実装役の直しの後・2026-10-03)

> 見たのは直しの差分だけ(`calendar.py`・`tape.py`・`run.py`・新しいテスト `tests/engine/test_10a_review_fixes.py` 17 件・`test_response_delay.py` と `test_calendar_sites.py` の書き換え・README §10)。差分は、最初の検収の時に一時ディレクトリへ写した作業木と今の作業木を比べて取った。何も直していない。

### 5-1 結論

- 14 件の直しはどれも実装どおりで、正しい。既定の結果は動いていない。
- 残った指摘は、潜在の欠陥 1(直しで新しく入った軽いもの)と問い 2。結果を動かす欠陥・記録の誤り・テストの欠けは 0。

| 種類 | 件数 |
|---|---|
| 結果を動かす欠陥 | 0 |
| 潜在の欠陥 | 1(N1) |
| 記録の誤り | 0 |
| テストの欠け | 0 |
| 問い | 2(N2・N3) |

### 5-2 壊して捕まるか(新しいテスト 5 本・72 件)

- 前回の 33 件(発注文の 8 件+自分の 24 件。M5b を除く)を今の木で回し直した。**33 件すべて捕まる**。前回捕まらなかった 6 件は、次のテストが捕まえた。
  - X6: test_real_day_key_is_the_day_number
  - X8: test_datetime_uses_tick_seconds
  - X9: test_plus2_path_reproduces_the_head_final
  - X12: test_home_meals_are_read_by_tick_of_day
  - X16: test_real_mode_rest_day_reaches_the_mock_schedule の 3 通り以上
  - X22: test_august_is_summer
- 直しそのものを壊す 9 件を足した。**9 件すべて捕まる**。

| 壊し方 | 捕まえたテスト |
|---|---|
| P1 開始日の検査を、置き換える前の暦でも 1 回走らせる | test_start_check_runs_on_the_calendar_after_the_weather_date |
| P1 検査を既定の開始日 + day_index の暦で走らせる | 同上・test_real_calendar_run_needs_a_valid_start |
| P2 0:00 の検査を外す | test_start_must_be_midnight |
| P3 テープの値との突き合わせを外す | test_replay_with_the_other_delay_stops・test_the_tape_carries_the_response_delay_and_mismatches_stop ほか |
| P3 値の無いテープを 2 とみなさない | test_a_tape_without_the_value_is_replayed_as_2_with_one_warning |
| P3 `run_meta.json` を書かない | test_record_and_replay_match_under_each_delay[1] ほか |
| P4 相対パスを作業ディレクトリから解決する | test_relative_holiday_csv_is_resolved_from_the_repo_root |
| P4 読めないときの md5 を空文字に戻す | test_unreadable_csv_stops_real_and_nulls_the_manifest_in_day_index |
| P5 当月の寄せ先だけを見る | test_payday_moved_back_across_the_month_boundary |

- 前回 M4(下限を `tick + 1` に戻す)を捕まえたテストのうち、test_replay_with_the_other_delay_diverges は「止まる」テストへ置き換わった。今は test_fleet_call_fired_at_T_is_applied_at_T_plus_delay[1] だけが捕まえる(1 件で足りている)。
- 書き換えのあと、写しが作業木と同じ中身に戻ったことを `diff -r` で確かめた。

### 5-3 検算の場面が実装どおりか

- **T1 の既知の答え**: HEAD の写しで自分で回した。偽 vLLM・`pair_talk`・会話の世界 200 体 × 600 tick・`fleet_wait_s=10` の final は `79821d778ea4addf`(セッション 7)。作業木の +2 も同じ値で、テストの定数と一致した。
- **P1**: `check_start` は `with_start(world_start)` の後(`run.py` の知覚レンダラの直前)に移った。テストは合成世界に再生実日を差し込む形で、置き換えた後の日を見ていることを固定している。
- **P2**: `(時, 分, 秒, マイクロ秒) == 0` を見る。tz つきの 0:00(`+09:00`・UTC・`-05:00`)は 3 本とも `run_day` が通り、manifest の開始日は渡したままの値になった。誤って止めることは無い。
- **P3 の 3 つの場面**: 自分のスクリプトで確かめた。テープは HEAD の写しで録った、meta の無いもの(合成世界・20 tick)。

| 場面 | 結果 |
|---|---|
| 値の無い mock テープを既定で再生 | 2 で回る・final `84d56f8542b10aeb`=HEAD の録画と同じ・テープ外 0・警告 1 回 |
| 同じテープを 2 で再生 | 同じ final・警告なし(2 回目なので) |
| 同じテープを 1 で再生 | 止まる(「テープは response_delay=2・今の設定は 1」) |
| 値の無い艦隊テープを既定で再生 | final `462e964893156333`=HEAD の録画と同じ・テープ外 0 |
| 同じテープを `Replay` オブジェクトで渡す | 同じ final(パスでもオブジェクトでも meta を読む) |
| 再生しながら録り直す(`tape_path` つき) | 新しいテープの `run_meta.json` は `{"response_delay": 2}`(使った値) |

- **P4 の CSV の解決先**: `REPO_ROOT = Path(calendar.py).parents[3]`=リポの根。作業ディレクトリをリポの外にして既定のランを回しても、md5 `733fabb6…`・範囲 1955-01-01〜2027-11-23 が読めた。読めないときは md5 と範囲が `null` になる。
- **P5**: 規則は「当月か翌月の給料日の寄せ先」。2026-07〜10 の 5 日(10-30 は 11/1(日)の寄せ)は規則どおり。前回の自分の検算は 10/28 までしか見ていなかったので、10-30 を数えていない。

### 5-4 既定が動いていないか

- byte-check を自分のスクリプトで 2 本回した(作業木の今と、前回取った HEAD の写しの結果を比べた)。final・呼数・checkpoint の全点・テープの全列が一致した。
  - 既定 v3: `993276d5e5bb5cbe`/69,978
  - 帰無: `72cb9cd52982da74`/100,439
- テープの置き場には `run_meta.json`(`{"response_delay": 1}`)が増える。parquet の 2 本は変わらない。
- `tape_miss_count` の数え方には手が入っていない(`tape.py` と `run.py` の差分は meta の読み書きと突き合わせだけ)。上の再生はどれもテープ外 0。

### 5-5 指摘

**N1(潜在の欠陥・軽い)開始日の検査が、世界を読んだ後・テープの置き場を作った後になった**
- 根拠: P1 で `check_start` を `with_start` の後へ移した。そのため、世界資産の読み込み、`TapeWriter` の生成(`tape.py:266-268` で置き場を `mkdir`)、層の初期化の後に走る。直す前は世界を触る前だった。
- 再現: `run_day(n_agents=10, n_cells=9, ticks=5, calendar_weekday="real", start_sim_datetime="2026-08-04", tape_path=<新しい場所>)` は「0 日目が月曜でない」で止まり、空のテープの置き場が残る。
- 影響: 結果は動かない。39 万体のランでは、開始日の誤りが世界を読み終えるまで分からない。real モードは開始日が渡された時点で日付が決まるので、再生実日に依らない検査(real の規則・範囲)は前で走らせ、再生実日で決まる day_index の警告だけを後に置く手もある。

**N2(問い)値の無い旧テープを 1 で再生すると、mock のテープでも止まる**
- mock で録ったテープは `replay_inbox` を通らないので、遅れの値は結果に効かない(上の表の通り)。それでも `--response-delay 1` を付けると止まる。安全側の扱いで害は無い。旧い mock テープを 1 で回したい場面があるかどうかだけ確認したい。

**N3(問い)day_index モードで CSV が読めないとき、範囲外の検査は今も抜ける**
- `start_problems` は直していない(読めないときに止めるのは real だけ)。読めない場合は manifest の md5・範囲が `null` になり、警告も 1 回出るので、前回の P4 の「黙って」は解消した。day_index は祝日を使わないので、この扱いで足りるという読みでよいか。

### 5-6 README §10 の記述

直しの表・問いへの答え・byte-check の記述は、上の検算と食い違わない。§10 の T1 の「検収役の構成は記録から再現できなかった」は、前回の私の記録が構成を細かく書いていなかったため。今回の 5-3 に構成を書いた。
