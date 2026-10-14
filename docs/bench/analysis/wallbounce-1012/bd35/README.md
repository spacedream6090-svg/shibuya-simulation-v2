# 第 3 期 3-5 本人の体と System 1(55 件の ③ 群)・TM5 の予約の口の記録

- 実装役 Opus 5.5。作業木の枝 `3-5/body-system1`(作った時の土台 `d35a9b6`=2-4 の版上げ 2 回目の取り込みの後 → 検収の後に本体 `60dadc4`(2-3c・3-2・4-1 の取り込みの後)へ rebase=§16-2)。commit は親。§0〜§15 の数は rebase の前の土台の上の値(rebase の後に変わった数は §16-2 の表)。
- 正: [決定 10-12](../../../../design/v2-wallbounce-decisions-2026-10-12.md) §1-5(55 件の 3 群の ③=意図しない体と System 1 の反応=本人の体と System 1 としてコードに残す・研究で「意図しない」と裏付けがあり選択を決めないものに限る/D の論点 3=体の生理と急変は本人の体・倒れる率は出典を探す)・§4-2 TM5(体の変化は次に段階の境目を越える時刻を予約する・「全員を毎回見る版」と一致することが受入の条件)・TM6 の T3・[計画](../../../../design/v2-implementation-plan-2026-10-12.md) の 3-5 の行(T3 で有効=◎ 結果不変)・[回答 10-13b](../../../../design/v2-answers-2026-10-13b.md) §0-3(新しい問いは既定 off の腕で仮採用)。洗い出し [agentless-outcomes-inventory.md](../../wallbounce-1006/agentless-outcomes-inventory.md) の A2・D8・D9・D18 と [code-vs-decisions-survey.md](../code-vs-decisions-survey.md) の ③ の 3 件。
- 測った機械: Windows 11・x86-64・論理 CPU 20(並行して別の作業木のランが動いていた)。数は実測。生の出力(テープ・side の JSON・状態のファイル)は作業木の `_bc/`(git の外・取り込みの前に消す)。本書には比べた結果と道具だけを置く。絶対パス・ホスト名・個人名は書かない。

## 0. 結論

- **作った**: 本人の体の層 `src/shibuya/engine/body/`(持ち主 `BodyModel`=状態台帳の外の状態の持ち主 `body`・行 `BD`)。③ の 3 件(D8 空腹と疲れ・A2 体感温度・D9 倒れる)と D18(刻み 0 の体の状態)の計算を、前と**同じ値**を返す口 `BodyModel.step`・`felt_temperature`・`collapse_draw`・`initial` に移した。SoA を書くのは今までどおり `engine.resolve` だけ(体の層は書く値を返す)。
- **既定は結果不変**: byte-check **19/19 構成で 25 欄とも本体 HEAD と同じ**(§7)。系ごとの指紋も 3 構成で全部の (刻み, 系, 欄) が同じ(§9)。
- **TM5 の予約の口**(腕 `--body-schedule reserve`・既定 `sweep`・T3 で有効): 体ごとに「次に段の境目(空腹の語の段・疲れの目盛・体感温度の目盛)を越える刻み」を見込んで予約の列(`engine.scheduler.Scheduler`=1 分のバケット)に置き、予約の来た体と入力の変わった体だけを規則に通す。**19/19 構成で sweep と 27 欄(25 欄+段の境目の列の鎖のハッシュと数)とも同じ**。**負の対照**: 予約を 1 刻み遅らせると final・呼数・テープ・境目の列が動く(2/2 構成)。1 刻み早めても同じ(下界の予約=空振りして引き直す)。規則に通した体の延べは 5,000 体・1 日で全員の 2.7〜6.9%。
- **2 日・再開**(5,000 体): 通しの reserve=通しの sweep。腕 sweep で日の境目と日の中で止めた状態から腕 reserve で再開しても通しと同じ(予約の列は状態から引き直す=軸 2 discardable)。2 日の final は 2-4 の記録 V4-5 の値と同じ(§8)。
- **性能**: いまの予約の腕は sweep より**遅い**(体の層の 1 刻みの時間が 5,000 体で 2.6 倍・39 万体で 1.11 倍・§10)。既定の sweep は HEAD 相当の計算より 5,000 体で +1.3%・39 万体で +0.5%(〔検収 L6〕段の境目の計器は環境変数のときだけ数える形にした後)。全員のエネルギーの積み上げと入力の比べ(どちらも体数ぶんの配列演算)を残したため。予約が速さに効くのは T3 の版上げ(閉じた式の積み上げ・活動の口からの知らせ)の後=宣言(つなぎの台帳 `BR-BODY-RESERVE-*`・外す段 T3)。
- **器だけの 3 件**(値は空): ロンバード効果・混雑の中の歩き方と避け方・大きな音に注意が向く(`Percept.nearby_change` の種類 `loud_sound`)。つなぎの台帳に 3 行(外す段 5-3・5-1・5-3)。
- **見つけたこと**: (1) byte-check の HEAD の写しの手順(10e の道具の docstring)に、2-4 の後は `docs/design/rules-table.json`(消費税の率)と `data/realworld/osm/` の 2 本(ATM の表)が要る。無いと写しの HEAD のランだけ経済の段階 2 の値が変わり、19/19 構成で final が食い違う(§7-3・本体 `82eeab0` の 10e の道具の `HEAD_TREE_FILES` で直っている)。(2) HEAD の体感温度の写像はセル番号がセルの数以上の体で添字の誤りになる書き方だった(新しい写像は舞台の外の値に写す・ランでは起きない=19/19 同じ)。
- 試験: 新しい試験 66 本(`tests/engine/body/` 6 ファイル)。範囲の試験と全体の試験の結果は §11。仮採用と限界は §13、親に確かめてほしいことは §14。

## 1. 作ったもの・変えたもの

| ファイル | 中身 |
|---|---|
| `src/shibuya/engine/body/__init__.py`(新) | 置き場の説明・`BodyModel` と腕の口の再輸出 |
| `src/shibuya/engine/body/rules.py`(新) | 体の規則の値と純関数(前の場所と同じ式・型・順)・出典の表 `BODY_RULES`(10 行)・expedient の宣言の表 `BODY_EXPEDIENTS`(7)。前の場所の値の名(`BODY_TICK_PERIOD` ほか)はここが正 |
| `src/shibuya/engine/body/model.py`(新) | 持ち主 `BodyModel`(欄は 1 回だけ置ける・書く口は `initial`・`step`)・段の境目の列の計器・manifest の `body` |
| `src/shibuya/engine/body/schedule.py`(新) | TM5 の予約の口(腕 `sweep`/`reserve`・環境変数 `SHIBUYA_BODY_SCHEDULE`)・`BodySchedule`(予約の列 2 本と引き直しの写し)・次の境目の見込み `next_intero_steps`・`next_felt_frames`・宣言の表 `RESERVE_EXPEDIENTS`(2) |
| `src/shibuya/engine/body/system1.py`(新) | 器だけの 3 件(口は None を返す・W10 の騒音の段の読みの口)・宣言の表 `SYSTEM1_EXPEDIENTS`(3) |
| `src/shibuya/engine/resolve.py` | `advance_body(…, body=None)`・`initialize(…, body=None)`・`initialize_energy(…, body=None)` は体の層の口の値を書くだけ(体の層を渡さない呼び手は同じ値の純関数)・`set_thermal(…, indices=None)`(腕 reserve は値の変わりうる体だけを書く)・体の値の名は `engine.body.rules` から写して出す・docstring の expedient の項(行為の効果の内受容に書き直した=項の数は 6 のまま) |
| `src/shibuya/engine/processes/environment.py` | 体感温度は体の層の口(`body` が無ければ全員を同じ値で書く)・`felt_day_table`(その日の窓 × セルの表=腕 reserve だけ)・`_shade_at`(キャッシュの印を触らない日陰)・写像の 3 つの値は体の層から写して出す・docstring の expedient の見出しの項 5 → 2 |
| `src/shibuya/engine/processes/salient.py` | 倒れるの引き方は `collapse_draw`(同じ乱数の流れ・同じ順)・率の名は体の層から写して出す・見出しの項 5 → 4 |
| `src/shibuya/engine/processes/runner.py` | `attach_body`(環境の過程へ体の層を挿す・実行器の属性は増やさない) |
| `src/shibuya/engine/systems/body.py` | 系 `body` が `b.layers.body` を `advance_body` に渡す |
| `src/shibuya/engine/systems/build.py` | `BodyModel` を作る(どの腕でも)・`initialize`・`initialize_energy` に渡す・`runner.attach_body`・`Layers(body=…)` |
| `src/shibuya/engine/systems/{table,boxes,state_io,run_end}.py` | §12(共有のファイル) |
| `src/shibuya/engine/state_ledger.py` | 行 `BD`・持ち主 `body`・除外 3 行(§6) |
| `src/shibuya/engine/state_hashes.py` | `VALUE_CLASSES` に `engine.scheduler.Scheduler`(行 BD の予約の列を系ごとの差の測りが読める形に・どちらのハッシュにも入らない) |
| `src/shibuya/engine/run.py`・`manifest_sections.py` | manifest の末尾に `body`(混ざった辞書=設定 8・観測 14) |
| `src/shibuya/perception/facts.py` | `NEARBY_CHANGE_KINDS = ("loud_sound",)`(`Percept` の欄・並び・形の版は変えない) |
| `src/shibuya/cli.py` | `--body-schedule {sweep,reserve}`・ランの種類(既定と違えば arm) |
| `docs/design/bridging-ledger.json` | 12 行を足した・既存の ③ の 3 行の項の数と注を直した(§5) |
| 凍結の表と数の試験 | §12 |
| `tests/engine/body/`(新) | §11 |
| `docs/bench/analysis/wallbounce-1012/bd35/tools/` | byte-check(10e の 1 本のランを包む)・系ごとの指紋(ec21 の道具を包む)・2 日と再開・性能 |

## 2. ③ の 3 件の移し方(前後の口・同じ値の根拠)

| 洗い出しの行 | 前の口 | 後の口(体の層) | 書く口(resolve・前と同じ) | 同じ値の根拠 |
|---|---|---|---|---|
| D8 空腹(v1)・疲れ・就寝と休みの回復 | `resolve.advance_body` の本体 | `BodyModel.step("interoception", …)` → `rules.interoception`(`fatigue_after`・`hunger_v1_after`) | `advance_body` | 同じ式(`int16` に上げて ±・上限 10・下限 0・`uint8`)・同じ順(体の刻み → 休みの刻み)。HEAD の本体を写した物差しと、v1/エネルギー × 二層の段 2 あり/なし × 刻み 0〜180 × 外の書き手つきで毎刻み同じ(試験 `test_body_same_values.py`) |
| D8 空腹(エネルギー収支 5a) | `advance_body` の後半 | 同上(`energy_spent`・`hunger_copy_of`=`EnergyModel` の式のまま) | `advance_body`(`since_meal_kcal[:] = 前 + 消費`・`energy_balance -= 消費`) | float32 の足し算 1 回(前の `+=` と同じ丸め)・語の段は `stage_of`・`hunger_copy` のまま。`energy.py` の錨の読み口は触っていない |
| A2 体感温度 | `EnvironmentProcess.step`(暑さ段 → 写像 × 日陰 → `rint` → `set_thermal` の丸め) | `BodyModel.felt_temperature`(`rules.felt_cells` を体のセルで引く) | `set_thermal`(既定は全員) | セルごとの値を先に丸めて体のセルで引く=要素ごとの `rint`・`clip` は添字と入れ替えてよい。暑さ段 −1〜5・日陰・舞台の外で HEAD の写しと同じ(試験) |
| D9 倒れる | `SalientProcess._collapse_events` の前半 | `BodyModel.collapse_draw(g, 率, 体数, 刻みの幅, セル)` | 書かない(顕著行為の事象と出動は salient のまま=② の出動は触らない) | 同じ流れ(`stream(seed, "world.salient.counter", 0, 時刻の鍵)`)から同じ順(ポアソン → 在圏の体から重複なし → 昇順)。1,440 刻みで HEAD の写しと同じ列(試験) |
| D18 刻み 0 の体の状態 | `resolve.initialize`(空腹 2・疲れ 2・暑さ 5・段)・`initialize_energy`(食後の消費の初期値・空腹の写しと段) | `BodyModel.initial(n)`・`initial(energy=…, eer=…)` | `initialize`・`initialize_energy` | 同じ値と段(`INTERO_UP_EDGES` を何本越えたか)。体の活動の初期値(W17 の 0 時の行)は予定の表の側(`set_initial_activity`)に残した=体の値でなく予定の値(§13 の仮採用) |

- 前の場所の名(`resolve.BODY_TICK_PERIOD`・`SLEEP_FATIGUE_RELIEF`・`ACTIVITY_REST_PERIOD_TICKS`・`ACTIVITY_REST_FATIGUE_RELIEF`・`environment.HEAT_STAGE_TO_THERMAL`・`SHADE_FACTOR`・`FALLBACK_THERMAL`・`salient.COLLAPSE_PER_10K_PER_DAY`)は体の層の値を写して出す(読み手の import は変えない・`__all__` に残した)。行為の効果(休憩 −3・購入と食事 −4)は resolve に残した(体の自然な変化ではない)。
- **書き手は増えない**(AST): SoA の体の欄(空腹・疲れ・暑さ・段・食後の消費・収支)を書く resolve の関数は HEAD と同じ 11(`_apply_rest`・`_complete_buy`・`_complete_eat`・`_energy_meal`・`_energy_snack`・`advance_body`・`apply_detection`・`energy_home_meal`・`initialize`・`initialize_energy`・`set_thermal`)で列も同じ(`allow.index` の直接の書き・HEAD の写しで同じ表)。口の呼び手(`R.advance_body`・`set_thermal`・`initialize`・`initialize_energy`)は HEAD と同じ 5(試験 `test_body_guard.py`)。系の `writes.soa`(静的な閉包)は変わらない(`writes_soa_frozen.json` は直していない)。

## 3. TM5 の予約の口

### 3-1. 段の境目(予約する変化)と見込みの式

刻み `now` に規則に通した直後の値から、次に値が変わりうる最初の刻み(下界)を見込む。`nb`=次の体の刻み(30 の倍数)・`nr`=次の休みの刻み(10 の倍数・二層の段 2 のランだけ)。

| 量 | 段 | 次の境目(予約の刻み) | 予約なし(入力が変わるまで見ない) |
|---|---|---|---|
| 疲れ | 0〜10 の目盛の 1 つ | 起きていて 10 未満・就寝中で 0 より上 → `nb`/休んでいる体(在店/その場・期限 `activity_until > nr`・移動/乗車/就寝でない)で 0 より上 → `nr`/早い方 | 起きていて 10・就寝中で 0・休みでない |
| 空腹 v1 | 0〜10 の目盛 | 10 未満 → `nb` | 10 |
| 空腹(エネルギー収支) | 語の段(満腹/ふつう/空腹/とても空腹=比 0.25・0.75・1.5) | `now + max(1, j − 余白)`。`j`=⌈(次の区切り × EER/3 − 食後の消費) ÷ 1 刻みの消費⌉・余白=2+⌈j × ulp(1.5 × EER/3) ÷ 1 刻みの消費⌉(float32 の足し算の誤差の上限=1 回で ulp の半分 × 刻みの数を 2 倍に見た) | とても空腹(上の区切りが無い) |
| 体感温度 | 0〜10 の目盛 | その日の表(5 分の窓 × セル+舞台の外)で、体のいる列の値が次に変わる窓(`_next_change_table`) | その日の中で変わらない |

- 予約の刻みに来た体は**前と同じ規則**(sweep の式)で値を作り、変わったら境目の列に足し、新しい値から見込み直す。早めの予約は境目の手前で空振りして見込み直すだけ=値は同じ(負の対照 −1 で確かめた)。遅い予約は境目を取りこぼす=値が変わる(負の対照 +1)。
- 予約の列: 内受容は刻みのバケット(`Scheduler`・地平 1 日)・体感温度は窓の通し番号のバケット(地平 288 窓)。体ごとに生きている予約の通し番号を持ち、古い予約は取り出す時に落とす(`Scheduler.cancel` は O(地平) なので使わない)。取り出しは前に取り出した刻み/窓の次から今までの全部(体の刻みを飛ばすランで早めた予約を落とさない=検収の前に自分で見つけて直した・試験の負の対照 −1)。
- 体感温度の表: 環境の過程が日の頭と天気の日付の差し替え(3-3 の L0)の後の最初の窓で作り直す(`felt_day_table`・暑さ段と日陰は窓ごとの `step` と同じ式・`_shade` のキャッシュの印は触らない=behavior-hash に入る `runner.environment._shade` は sweep と同じに進む)。表が替わったら全員を見直す。**守り**: 窓ごとに、表のその窓の行と今の窓の値が同じでなければ止める(`RuntimeError`)。

### 3-2. 引き直しの条件

- 前に規則に通した後の写しと比べて入力が違う体は、その刻みで規則に通して予約を引き直す: 活動・活動の種別と期限(二層の段 2)・1 刻みの消費(活動と乗車の状態から来る METs=float32 の値で比べる)・空腹・疲れ・食後の消費(食事・軽食・自宅の食事・範囲外の食事)。体感温度はセル(移動)。
- 活動を書く口が resolve に約 40 か所あり 1 つの口が無いため、口ごとの知らせでなく写しとの比べ(体数ぶんの配列の比べ 7 本)で見つける(仮採用・つなぎの台帳 `BR-BODY-RESERVE-DETECT`・外す段 T3)。単体の試験: 就寝で疲れ 0・とても空腹の体は予約なし → 起きると次の体の刻み(30)に予約・入力が変わらなければ引き直さない(`test_activity_change_replans_the_reservation`)。
- 予約の列の始まり: 組み立ての直後(`initial`)と再開の最初の刻みは写しが無い=全員を規則に通す。予約の列は状態台帳の行 `BD`(軸 1 diag・軸 2 discardable=再開では状態から引き直す・下界の予約なので引き直した列は通しの列と違ってよい=結果は同じ)。

### 3-3. 一致の表(19 構成・5,000 体・seed 1・1 日・テープつき)

[sweep_vs_reserve.json](sweep_vs_reserve.json)(腕 sweep=作業木の既定・腕 reserve)は 19/19 構成で 27 欄(10e の 25 欄+段の境目の列の鎖のハッシュ `boundary_digest`・種類ごとの数 `boundaries`)とも同じ。[head_vs_reserve.json](head_vs_reserve.json)(本体 HEAD と腕 reserve)も 19/19 で 25 欄とも同じ。

| 構成 | final(HEAD=sweep=reserve) | 呼数 | 段の境目 空腹/疲れ/暑さ | 規則に通した体(内受容) reserve/sweep | 体感温度 reserve/sweep | 予約 内受容/体感温度 |
|---|---|---|---|---|---|---|
| `w6_v3_default` | `b8eadcb51e8705e7` | 64,528 | 26,054 / 147,392 / 43,987 | 417,115(5.8%) | 75,282(5.2%) | 411,289 / 57,848 |
| `w6_v3_activity_off` | `c88ba9104f45f897` | 50,006 | 25,107 / 43,524 / 36,997 | 197,054(2.7%) | 55,294(3.8%) | 185,199 / 43,330 |
| `w6_v1_default` | `e1288e092ddaca86` | 51,655 | 23,348 / 55,809 / 37,367 | 200,944(2.8%) | 56,816(3.9%) | 186,091 / 44,194 |
| `w6_v1_derive_v2_1` | `cfbba0d504a27aa7` | 44,807 | 24,730 / 54,010 / 36,080 | 201,559(2.8%) | 53,956(3.7%) | 189,605 / 41,953 |
| `w6_v2` | `c186b380ae65cb86` | 51,266 | 24,430 / 54,921 / 36,678 | 204,780(2.8%) | 54,612(3.8%) | 192,963 / 42,301 |
| `w6_v1_edge` | `d1c56f85847c21db` | 46,054 | 23,252 / 54,267 / 34,470 | 198,374(2.8%) | 46,227(3.2%) | 185,435 / 35,594 |
| `w6_v2_edge` | `948b975a2ab74231` | 46,655 | 24,159 / 53,736 / 34,181 | 202,269(2.8%) | 45,065(3.1%) | 191,151 / 34,686 |
| `w6_v1_edge_plateau` | `ff8fc6b562622640` | 47,871 | 23,304 / 54,918 / 34,989 | 200,618(2.8%) | 47,003(3.3%) | 187,433 / 36,470 |
| `w6_old_v1_default` | `78b6fec6036b2438` | 51,655 | 23,348 / 55,809 / 37,367 | 200,944(2.8%) | 56,816(3.9%) | 186,091 / 44,194 |
| `w6_old_v1_derive_v2_1` | `f647f0483ef3d7ca` | 44,807 | 24,730 / 54,010 / 36,080 | 201,559(2.8%) | 53,956(3.7%) | 189,605 / 41,953 |
| `w6_old_v2` | `9d8a34ee545f484a` | 51,266 | 24,430 / 54,921 / 36,678 | 204,780(2.8%) | 54,612(3.8%) | 192,963 / 42,301 |
| `w6_old_v1_edge` | `245b2fdb8aa229ef` | 46,054 | 23,252 / 54,267 / 34,470 | 198,374(2.8%) | 46,227(3.2%) | 185,435 / 35,594 |
| `w6_old_v2_edge` | `2fb54c9ad562faca` | 46,655 | 24,159 / 53,736 / 34,181 | 202,269(2.8%) | 45,065(3.1%) | 191,151 / 34,686 |
| `w6_old_v1_edge_plateau` | `dd66261d71c4d6ae` | 47,871 | 23,304 / 54,918 / 34,989 | 200,618(2.8%) | 47,003(3.3%) | 187,433 / 36,470 |
| `w6_golden_null_arm` | `19ee17b1b1caf44c` | 96,695 | 13,399 / 89,635 / 38,544 | 210,120(2.9%) | 66,425(4.6%) | 190,598 / 50,597 |
| `v3_mem_store` | `a9f6f9f0adb3f9a4` | 64,528 | 26,054 / 147,392 / 43,987 | 417,115(5.8%) | 75,282(5.2%) | 411,289 / 57,848 |
| `v3_mem_rel` | `768b2262e3b0999e` | 67,794 | 26,075 / 148,021 / 44,043 | 421,474(5.9%) | 75,675(5.3%) | 415,822 / 58,149 |
| `v3_classical` | `ca25874a5e4acb79` | 93,017 | 31,861 / 138,173 / 48,258 | 482,344(6.7%) | 92,616(6.4%) | 477,872 / 73,032 |
| `v3_classical_mem_rel` | `9dd9d5684891b57c` | 105,363 | 32,011 / 139,393 / 49,627 | 494,551(6.9%) | 96,766(6.7%) | 490,073 / 76,657 |

- 規則に通した体の延べ(内受容)は全員を毎刻み見る 7,200,000(5,000 × 1,440)に対し 2.7〜6.9%、体感温度は 1,440,000(5,000 × 288 窓)に対し 3.1〜6.7%。予約の数は 1 日に 18.5 万〜49 万(内受容)・3.5 万〜7.7 万(体感温度)。
- 5,000 体・1 日の `w6_v3_default` の腕 reserve の計器: 予約の来た体の延べ 305,207・引き直し 110,936(1 刻みに体の 1.54%)・体感温度の予約の来た体 15,073・移動した体 56,043(1 窓に体の 3.9%)・日の表 1 回・終わりに生きている予約 4,784(内受容)。

### 3-4. 負の対照(予約の式を 1 刻みずらす・2 構成)

| ずらし | 構成 | 結果 |
|---|---|---|
| +1(遅らせる) | `w6_v3_default`・`v3_mem_rel` | 25 欄のうち 15 欄と境目の列 2 欄が動いた(final・呼数 64,528 → 54,532 と 67,794 → 57,028 と呼の列と行と起床の内訳・テープの blocks の行と sha・行動の件数と sha・食事・顕著行為に気づいた数・出動の遅れの平均・behavior/full の最後・締めの後の 2 本)。疲れの境目 147,392 → 14,563(体の刻みに当たらない予約が引き直しで体の刻みの次にずれ続ける)=[sweep_vs_shift1.json](sweep_vs_shift1.json) |
| −1(早める) | 同じ 2 構成 | 27 欄とも sweep と同じ=[sweep_vs_shift-1.json](sweep_vs_shift-1.json) |

道具 `tools/byte_check_bd35.py --shift K`(このプロセスの中だけ `next_intero_steps`・`next_felt_frames` を包む・src は変えない)。単体の試験でも内受容 2 形 × 2・体感温度で同じ向き(`test_negative_control_shifting_the_reservation`・`test_felt_negative_control`)。

## 4. 器だけの 3 件

| 器 | 口(値は None) | 欄 | 値が入る段 | つなぎの台帳 |
|---|---|---|---|---|
| ロンバード効果(周りの騒音 → 話す大きさ) | `system1.speech_loudness`・W10 の騒音の段の読みの口 `noise_stage_at`(`World.noise_stage_for_tick` をセルで引く・読み手はまだ無い) | `Percept.heard_speech`(聞こえる会話=届く範囲が話す大きさで変わる) | 5-3(音の伝わり方) | `BR-SYSTEM1-LOMBARD`(5-3) |
| 混雑の中の歩き方と避け方 | `system1.crowd_gait` | なし(空間の段 1 の物理=歩く速さと向き) | 5-1 | `BR-SYSTEM1-CROWD-GAIT`(5-1) |
| 大きな音に注意が向く | `system1.loud_sound_notice` | `Percept.nearby_change` の種類 `loud_sound`(`perception.facts.NEARBY_CHANGE_KINDS`) | 5-3 | `BR-SYSTEM1-LOUD-SOUND`(5-3) |

- どれも洗い出しに行が無い(今のコードに無い)=口と欄だけ。`Percept` の欄・並び・空の欄 9・形の版 `shibuya.perception/percept/1`・manifest の `percept` は前と同じ。合成の世界のランで描いた知覚の事実の `nearby_change`・`heard_speech` は None のまま(試験)。byte-check のテープ(プロンプトの列と blocks)は 19/19 同じ=描画のバイト不変。
- 3 件とも「研究で意図しないと裏付けがあり選択を決めない」かの確かめ(決定 §1-5 の条件)は本段ではしていない(値が入る段の答申で確かめる・§14)。

## 5. 出典の表(conf)とつなぎの台帳

`BODY_RULES`(manifest の `body.rules` にも出る):

| id | 中身 | conf | 出典 | つなぎの台帳 | 洗い出し |
|---|---|---|---|---|---|
| `body.natural_variation` | 空腹(v1)+1・疲れ +1/体の刻み・就寝中の疲れ −2 | expedient | 自前(行動契約書に無い) | `BR-BODY-NATURAL-VARIATION` | D8 |
| `body.rest_recovery` | 在店/その場で持続中の体の疲れ −1/10 刻み | expedient | 第275 親の決め #1・感度腕 5/10/20 | `BR-BODY-REST-RECOVERY` | D8 |
| `body.energy_balance` | 空腹=食後の消費/(EER/3) の語の段 | expedient | D-118 K1 (c)・K2 (a)・改訂版メッツ表 2012・AVG_METS と区切りは expedient | `HD-engine.energy-cc73b60c`(既存) | D8 |
| `body.felt_map` | 暑さ段 → 体感 2/4/6/8/10 | expedient | 知覚契約書 §3(スケールだけ)・写像は自前 | `BR-BODY-FELT-MAP` | A2 |
| `body.shade_factor` | 日陰=生値 × 0.86 | **mechanism** | 知覚契約書 §3 内受容・R3-2 の決定 | なし | A2 |
| `body.shade_target` | 係数の掛け先=生値 | expedient | 自前 | `BR-BODY-SHADE-TARGET` | A2 |
| `body.felt_fallback` | 気象の資産が無い世界の 5 | expedient | 自前(C2 の初期値) | `BR-BODY-FELT-FALLBACK` | A2 |
| `body.collapse_rate` | 倒れる=1 万体あたり 1 日 3.0 件 | expedient | **出典なし**(東京消防庁の出場件数から同じ桁の丸い値・D の論点 3=出典を探す) | `BR-BODY-COLLAPSE-RATE` | D9 |
| `body.initial` | 刻み 0 の空腹 2・疲れ 2・暑さ 5 | expedient | C2 の初期値(自前) | `BR-BODY-INITIAL` | D18 |
| `body.initial_energy` | 刻み 0 の食後の消費 | expedient | energy.py の見出しの項 | `HD-engine.energy-cc73b60c`(既存) | D18 |

つなぎの台帳(`docs/design/bridging-ledger.json`・active 337 → 349・行 348 → 360=rebase の前/〔rebase の後〕本体 `60dadc4` の active 375 → 387・行 386 → 398):

- 足した 12 行(どれも `conf` expedient・`remove_basis` inferred・since 2026-10-15・コードの宣言の表=形 `expedients` と 1 対 1・`what` は宣言の文そのまま): 体の規則 7(`BR-BODY-NATURAL-VARIATION`・`REST-RECOVERY`・`FELT-MAP`・`SHADE-TARGET`・`FELT-FALLBACK`・`COLLAPSE-RATE`・`INITIAL`=外す段 7)・予約の口 2(`BR-BODY-RESERVE-DETECT`・`RESERVE-ACCUMULATE`=外す段 T3)・器 3(`BR-SYSTEM1-LOMBARD` 5-3・`CROWD-GAIT` 5-1・`LOUD-SOUND` 5-3)。
- 既存の ③ の行の持ち主の付け替え: 宣言を体の層へ移した見出しの行の項の数と注を直した=`HD-engine.processes.environment-1af925f4`(項 5 → 2・注に移した先 3 行)・`HD-engine.processes.salient-1af925f4`(項 5 → 4・注に `BR-BODY-COLLAPSE-RATE`)・`HD-engine.resolve-1af925f4`(項 6 のまま=同じ位置の項を行為の効果に書き直した・注に `BR-BODY-NATURAL-VARIATION`)。
- 形ごとの数: expedients 143 → 155(〔rebase の後〕本体の 171 → 183)・見出し 83(項の合計 362 → 358)。

## 6. 体の層の守りと状態台帳

- 持ち主 `BodyModel` の欄(`arm`・`n`・`step_seconds`・`_reservations`・`_body_meter`)の名は、ほかの持ち主の属性と重ならない名にした(最初の `_plan` は世界過程 3 つの `_plan` と重なり、10f の外の状態の軸 1 の AST の検査 `test_state_checks_10f.py` が名の衝突で落ちた=範囲の試験で見つけて名を替えた・3-3 と同じ型の落ち)。欄は組み立ての 1 回だけ置ける(`__setattr__`・`__delattr__` が断る・`__slots__`)。計器の読み口 `meter_view` は読むだけの写し。
- 〔検収 M1〕体ごとの予約の配列(通し番号・刻み/窓・列・写し)は腕 reserve のときだけ確保する(腕 sweep は長さ 0=行 BD の大きさの宣言「腕 sweep: 計器だけ」のとおり・39 万体で 15.6 MB の確保をやめた)。〔検収 L7〕`BodySchedule` にも実行時の守り: 欄の付け替えと消去は書く口(`reset`・`intero_due`・`intero_plan`・`intero_snapshot`・`felt_due`・`felt_new_table`・`felt_plan`=印 `_writing`)の中だけ・持ち主の配列は口の外では読み取り専用(`setflags(write=False)`)。窓の通し番号の覚えも口の中(`felt_due`・`felt_new_table`)に移した。
- 書く口は `initial`(予約と写しを空に戻す)と `step`(部分 2 つ=`interoception` と `felt`=呼ぶ時刻が違う)だけ。中身(`_reservations` の欄・`_body_meter`)を書く文は持ち主の口とその下請けと `BodySchedule` の書く口の中だけ・`BodySchedule` の書く口を呼ぶのは持ち主の口だけ・`body.step`/`body.initial` を呼ぶのは `resolve.advance_body`・`initialize`・`initialize_energy` と `EnvironmentProcess.step` だけ(AST・1-7 の道具 `tests/engine/ast_writers.py`・負の対照=外から書く・口を呼ぶ行を植えると見つかる)。写し(引き直しの検出)は SoA のビューを持たない(D ⑥ の試験と `np.shares_memory` の試験)。
- 状態台帳の行 `BD`(外の状態の末尾=2-3 の `M0L` の後・外 114・全体 205/〔rebase の後〕3-2 の `BW` の後・外 115・全体 206・版は上げない=1-3〜3-3 と同じ仮採用): 道筋 `body._body_meter`・`body._reservations`・軸 1 diag(親の発注の宣言=予約は「どの体を規則に通すか」を決めるが、受入の条件が sweep と結果が同じ=結果を変えない控え)・軸 2 discardable。持ち主 `body`(`OWNER_CLASSES`・`hash_owners` の末尾)。除外: `body` の設定 3(`arm`・`n`・`step_seconds`)・`runner.environment` の参照 `body` とキャッシュ `_felt_table`。書く系は `body` と `world`(宣言 `BD:body.*`)。
- manifest の `body`(一番上の鍵の末尾=3-3 の `experiment` の後/〔rebase の後〕3-2 の `batching` の後): 設定 8(`schema`・`owner`・`arm`・`arms`・`rules`・`expedients`・`reserve_expedients`・`system1`)・観測 14(体の刻みの回数・規則に通した体の延べ・予約の来た体・引き直し・予約・体感温度の窓と延べと予約の来た体と移動した体と予約と日の表・生きている予約・段の境目の数と列の鎖のハッシュ)。「一致の計器」は `boundary_digest`(刻み・種類・体・前・後の列の sha256 の鎖=腕をまたいで比べられる)と `boundaries`。〔検収 L6・親の判断〕この 2 つは環境変数 `SHIBUYA_BODY_BOUNDARY_GAUGE=1`(か `BodyModel(gauge=True)`)のときだけ数え、既定は null(欄は残す)。腕の一致の試験と記録の比べ(§3-3・§3-4・§8)は立てて回した。設定の道筋の golden `CONFIG_PATHS_SHA256` は `417f0818…` → `46a3127d…`。

## 7. byte-check(19 構成)

### 7-1. 既定=本体 HEAD と同じ

[head_vs_sweep.json](head_vs_sweep.json): **19/19 構成で 25 欄とも同じ**(`10e/byte_check_10e.py` の欄=final・呼数・blocks・テープの全部の列の sha と列の名・行動の件数・起床の内訳・顕著行為・倒れる・出動・食事・behavior/full の最後・締めの後の 2 本・暦・frozen_sources)。head=`d35a9b6` の src の写し(`src_is_worktree` 偽・§7-3 の手順)・作業木=腕 sweep(`src_is_worktree` 真)。倒れるは 19 構成とも 5 件(=collapse の引き方を通った)。

### 7-2. 腕 reserve=sweep=HEAD

§3-3。[sweep_vs_reserve.json](sweep_vs_reserve.json)(27 欄・19/19)・[head_vs_reserve.json](head_vs_reserve.json)(25 欄・19/19)。腕 reserve の side は取り出しの `np.unique` を外した後の src で回し直した(外す前の side と final・規則に通した体の延べ・予約の数まで同じ)。

### 7-2b. 最後の src での確かめ

19 構成の side の後に、結果に効かない直し(持ち主の欄の名 `_plan`・`_meter` → `_reservations`・`_body_meter`=§6・状態台帳の行 BD の大きさの文)をした。最後の src で 2 構成(`w6_v3_default`・`v3_mem_rel`)を回し直し、HEAD と 25 欄・腕 sweep の side と腕 reserve が 27 欄とも同じ。

### 7-3. 見つけたこと: HEAD の写しの手順に要るファイル

10e の道具の docstring の手順(`git archive <HEAD> src` と錨 3 本と祝日の CSV)で作った HEAD の写しは、2-4 の後の src では 19/19 構成で final が作業木と違った(例 `w6_v3_default` の写し `d2e8fabc…` と作業木 `b8eadcb5…`・`w6_v3_activity_off` の呼数 50,040 と 50,006)。系ごとの指紋の最初の食い違いは刻み 364 の phase_c(`ledger.money._raw_code`・`_raw_ps`=支払いの方法と税の生ログ)。原因は 2-4 V4 で既定にした経済の段階 2 が src の写しの根から読む 2 つ:

- `docs/design/rules-table.json`(`economy.anchors.consumption_tax_rate`=消費税の率・無いと 0)。
- `data/realworld/osm/poi_tags_overpass_20260928.json`・`poi_opening_hours_overpass_20260907.json`(`engine.economy_stage2` の ATM の表=`calendar.resolve_repo_path` が src の写しの根から解決・無いと ATM 0 点)。

この 3 本を写しに足すと 19/19 で同じになった(§7-1 は足した後の値)。どちらも要る: 規則の表だけを足した写しは `w6_v3_default` `730f2fdf…`・`w6_v3_activity_off` の呼数 50,040(ATM 0 点)、OSM の 2 本だけを足した写しは `136d03a7…`・`a68f011e…`(呼数は同じ・税 0)で、どちらも作業木(`b8eadcb5…`・`c88ba910…`)と違った。10e の道具は本段の編集の範囲の外なので直していない(親へ・§14)。本段の写しの手順は §15 に書いた。

- **両側とも同じ data で回した**: 作業木の側は `PYTHONPATH` に作業木の src(`src_is_worktree` 真)・`data` は本体の data への junction(作業木を作ったときの物)・世界資産は `data/world/v2`(本体の v2)。HEAD の写しの側は本体の data から上の 3 本(祝日の CSV と OSM の 2 本)をバイトのまま写した(世界資産は作業木の根から同じ `data/world/v2` を読む)。比べの値はこの写しの形で取った。
- 〔検収 L3〕親の注意(2-3c の発見=写しの根に本体の data への junction を一時だけ置く)は §7-1 の比べの後に届いた。その形に合わせようとして写しの根に作った junction は指す先を誤った(存在しない場所)。外す `cmd /c rmdir` は許可の分類器に断られ、**親が .NET で外した=`_bc` の下に junction は残っていない**。
- 〔検収 L3〕10e の写しの手順は本体 `82eeab0` の 10e の道具で直っている(`HEAD_TREE_FILES`=写しの木がリポの根から読む追跡ファイル 8 本と data の 3 本・`side` は足りなければ止まる)。規則の表 `docs/design/rules-table.json` は data の外なので、junction の形でも写しに要る(その一覧に入っている)。

## 8. 2 日・再開=通し(世界資産・5,000 体・seed 1・2 日)

道具 `tools/two_day_bd35.py`([two_day_v3_mem_rel.json](two_day_v3_mem_rel.json)・[two_day_w6_v3_default.json](two_day_w6_v3_default.json))。全部の確かめが真:

| 土台 | 通しの final(呼数) | 通し reserve=通し sweep | sweep で刻み 1,440 に止める → reserve で再開 | sweep で刻み 750 に止める → reserve で再開 |
|---|---|---|---|---|
| `v3_mem_rel` | `31c9b19409e18b2f`(145,675) | final・呼数・全 checkpoint 8 点・境目の列が同じ | final と止めた後の checkpoint 4 点が同じ・呼数 67,794+77,881=145,675 | 同じ(checkpoint 6 点・29,550+116,125) |
| `w6_v3_default` | `b346bb6e3ecc60af`(138,946) | 同じ | 同じ(64,528+74,418) | 同じ(27,974+110,972) |

- 通しの final と呼数は 2-4 の記録([vb24/README.md](../vb24/README.md) §V4-5 の再開=通し)の値と同じ。
- 予約の腕の計器: 2 日の通しで規則に通した体の延べ 825,787/14,400,000(5.7%・`v3_mem_rel`)・日の表 2 回(日ごと)。再開のランは最初の刻みで全員を規則に通し、日の中で止めた再開は日の表を 2 回(再開の日と次の日)作った。
- 試験(合成の世界・2 日・150 体): 腕 sweep で刻み 750 と 1,440 に保存 → 腕 reserve で再開=通し(`test_resume_with_the_reserve_arm_equals_the_straight_run`)。

## 9. 系ごとの指紋

道具 `tools/probe_bd35.py`(ec21 の `probe_ec21.py` を包み、3-5 で足した行 `BD` と結果の後付けの属性 `body_layer` を指紋から外す)と vb24 の `probe_systems_vb24.py`。3 構成(合成の世界 80 体 720 刻み・世界資産 300 体の既定 v3・記憶+関係):

- [probe_head_vs_sweep.json](probe_head_vs_sweep.json): **動いた系 0**(全部の (刻み, 系, 変わった欄の digest) の並びと系ごとの指紋 18〜20 系が同じ・final `d5c5fde5…`・`3dfb3050…`・`5cb03e3a…`)。
- [probe_sweep_vs_reserve.json](probe_sweep_vs_reserve.json): **動いた系 0**(腕 reserve の `body`・`world` の系の書きは値の変わりうる体だけだが、系の境目の全欄の digest は sweep と同じ)。
- HEAD の写しは §7-3 の 3 本を足した写し(足す前は刻み 364 の phase_c で食い違った=原因の特定に使った)。

## 10. 性能(P4・予約の腕の 1 刻みあたりの時間・39 万体の見積り)

道具 `tools/perf_bd35.py`([perf_bd35.json](perf_bd35.json))。作り物の体の表(エネルギー収支・二層の段 2 あり・体感温度は 5 刻みに 1 回・resolve の書き戻しを含む)を 1,440 刻み。外の書き手の量は 5,000 体の世界資産のランの計器から(1 刻みに体の 1.54% が活動を変え・0.78% がセルを移る)。腕 `pure`=体の層の持ち主を通さない純関数=HEAD 相当の計算。

| 体の数 | 腕 | 体の刻み 平均/p50/p99 [µs] | 体感温度 1 窓 [µs] | 1 刻みあたりの合計 [µs] | 規則に通した体/刻み | 体感温度/窓 | 1 日(1,440 刻み)の見積り |
|---|---|---|---|---|---|---|---|
| 5,000 | pure | 88.5 / 79.0 / 145.0 | 11.5 | 90.2 | — | — | 0.13 秒 |
| 5,000 | sweep | 89.3 / 78.8 / 180.8 | 13.7 | 91.4 | 5000.0 | 5000.0 | 0.13 秒 |
| 5,000 | sweep_gauge | 100.9 / 90.1 / 241.1 | 26.8 | 105.6 | 5000.0 | 5000.0 | 0.15 秒 |
| 5,000 | reserve | 225.8 / 206.5 / 685.5 | 80.9 | 241.8 | 218.6 | 241.5 | 0.35 秒 |
| 50,000 | pure | 852.0 / 773.7 / 1,747.0 | 82.1 | 862.5 | — | — | 1.24 秒 |
| 50,000 | sweep | 924.2 / 882.4 / 1,312.1 | 97.7 | 937.3 | 50000.0 | 50000.0 | 1.35 秒 |
| 50,000 | sweep_gauge | 990.1 / 921.8 / 1,819.5 | 173.8 | 1,018.3 | 50000.0 | 50000.0 | 1.47 秒 |
| 50,000 | reserve | 1,333.5 / 1,103.2 / 7,157.4 | 424.1 | 1,412.5 | 2181.3 | 2413.3 | 2.03 秒 |
| 390,000 | pure | 11,068.9 / 10,762.0 / 15,215.1 | 2,089.7 | 11,409.7 | — | — | 16.43 秒 |
| 390,000 | sweep | 11,122.5 / 10,693.7 / 16,075.5 | 2,109.1 | 11,466.7 | 390000.0 | 390000.0 | 16.51 秒 |
| 390,000 | sweep_gauge | 11,278.1 / 10,512.3 / 18,842.6 | 2,494.9 | 11,701.3 | 390000.0 | 390000.0 | 16.85 秒 |
| 390,000 | reserve | 12,044.6 / 9,774.7 / 73,160.8 | 3,832.9 | 12,745.8 | 17035.6 | 18820.2 | 18.35 秒 |

- 〔検収 L6 の後〕既定(sweep=段の境目の計器を数えない)は HEAD 相当(pure)より 5,000 体で +1.3%(+1.2 µs/刻み)・5 万体で +8.7%(+75 µs・p50 は +109 µs=同じ機械で並行の負荷のあるときの測り)・39 万体で +0.5%(+57 µs)。計器を数える `sweep_gauge`(直す前の既定と同じ計算)は 5,000 体で +17%・39 万体で +2.6%=差の大半は計器だった。直す前の測り(既定が計器を数えた形)は 5,000 体で +19%・39 万体で +3.7%。
- **予約の腕は今は sweep より遅い**(検収の後の測り=計器なしの sweep に対して 5,000 体 2.6 倍・5 万体 1.5 倍・39 万体 1.11 倍)。中身(39 万体・300 刻みの cProfile・取り出しの `np.unique` を外す前): 全員のエネルギーの積み上げ(METs と消費)が約 3 割・取り出しの並べ直し(`np.unique`=約 15%=重なりが無いので外した=値は同じ・19/19 の byte-check を回し直した)・引き直しの見込み・入力の比べ・予約の列への積み(相異なる予約の刻みの数ぶんの Python のループ)・写し。体の刻み(30 刻みごと)に起きている体の多くの疲れが一斉に変わる=予約の積みがその刻みに集まり、p99 が 79 ms に跳ねる。
- 見積り(39 万体・1 日=1,440 刻み・体の層だけ・検収の後): pure 約 16.4 秒・sweep 約 16.5 秒・reserve 約 18.4 秒。予約が速さに効くには、(1) エネルギーの積み上げを閉じた式(整数の kcal など)にして予約の時刻だけで値を作る(既定の値が動く=T3 の版上げ)、(2) 写しの比べを活動の口からの知らせに替える、(3) 疲れの体の刻みの一斉の変化を「次に 10 に届く刻み」の 1 予約にまとめる、が要る(つなぎの台帳 `BR-BODY-RESERVE-*`・§13)。

## 11. 試験

新しい試験 66 本(`tests/engine/body/`・道具 `body_fixtures.py`=HEAD の式の写し・作り物の体の表とエネルギー・検収の後に 2 本足した):

| ファイル | 本数 | 中身 |
|---|---|---|
| `test_body_same_values.py` | 24 | ③ の 3 件と D18 が HEAD の式の写しと同じ値(体の刻み 12 形 × 刻み 0〜180・外の書き手つき/sweep の持ち主=純関数/体感温度 7 段/倒れる 1,440 刻み/刻み 0)・前の名が同じ値・負の対照(規則の値を変えると物差しが食い違う) |
| `test_body_reserve.py` | 19 | 外の書き手つきで reserve=sweep(内受容 8 形・境目の列・規則に通した体が少ない)・負の対照(+1 で食い違う・−1 で同じ)・活動の変化で引き直す・体感温度の予約(移動・表の差し替え 3 回)と負の対照・表と窓の食い違いで止める守り・合成の世界の `run_day` 3 構成で final・全 checkpoint・呼数・境目の列が同じ・腕 sweep の状態から腕 reserve で再開=通し |
| `test_body_guard.py` | 8 | 中身を書く口と予約の列の書く口と `step`/`initial` の呼び手(AST・負の対照)・持ち主の欄の守り・書き手の 11 関数と列が HEAD と同じ・口の呼び手 5 が HEAD と同じ・写しがビューでない・〔検収 M1〕腕 sweep は体ごとの配列を確保しない・〔検収 L7〕予約の列の付け替え・消去・配列の書きを口の外で断る(負の対照=口の中は書ける) |
| `test_body_rules_sources.py` | 6 | 規則の表の conf と出典とつなぎの台帳の行(倒れる率=expedient・出典なし)・宣言の表 3 本と台帳の 12 行が 1 対 1・器の外す段 5-3・5-1・5-3・既存の ③ の行の項の数と注 |
| `test_system1_placeholders.py` | 4 | 器の口は None・W10 の読みの口・`loud_sound` と `Percept` の形が前と同じ・ランの知覚の事実の器の欄が None |
| `test_body_manifest.py` | 5 | manifest の `body` の鍵と節・層の無いランは null・腕の切替(環境変数の口・`--body-schedule`)・腕は設定の指紋に入らずランの種類は arm・世界資産 300 体で reserve=sweep(体感温度の境目あり・requires_data) |

- **範囲の試験**(発注の一覧=`tests/engine/body tests/engine/systems tests/engine/events tests/engine/time tests/engine/test_energy_balance.py tests/engine/test_resume_10d.py tests/engine/test_state_ledger_10b.py tests/engine/test_state_checks_10f.py tests/engine/test_env_and_sections_10f.py tests/perception tests/engine/experiment tests/engine/bridging`・`-n 6 --dist loadfile`・slow を含む): 1 回目 1,036 passed・4 failed(15 分 14 秒)。落ちた 4 本=10f の外の状態の軸 1 の AST の検査 3 本(持ち主の欄の名 `_plan` が世界過程 3 つの `_plan` と衝突=名を `_reservations`・`_body_meter` に替えた・§6)と manifest の末尾の並び 1 本(`test_percept_schema.py`=増えた分だけ直した)。直した後の回し直し(`tests/engine/body tests/engine/systems tests/engine/test_state_checks_10f.py tests/perception/facts tests/engine/test_state_ledger_10b.py`): **379 passed・0 failed**(7 分 6 秒)。
- **全体の試験**(`--ignore=tests/c7`・`-m "not slow and not gpu"`・`-n 6 --dist loadfile`・子のプロセスにも作業木の src=`PYTHONPATH` は絶対パス): **4,968 passed・1 failed・1 xfailed**(16 分 48 秒)。落ちた 1 本は `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`(テープの置き場の junction 由来の既知の落ち=2-4 の V7・3-3 の記録と同じ)。その前の 1 回目は 5 failed で、本段の欠陥 3 本(manifest の末尾の並びの試験 2 本=増えた分だけ直した・`test_sim_time_T.py` の `advance_body` を包む関数の引数の数=体の層の引数を受けて渡す形に直した)と、`PYTHONPATH=src`(相対)で子のプロセスが本体の src を読んだ環境の落ち 1 本(絶対パスで通る)と上の既知の 1 本。
- **slow**(`-m "slow and not gpu"`・`-n 4`): 86 passed・1 failed・1 skipped(26 分 2 秒)。落ちた 1 本は `tests/engine/test_change_detect_p6.py::test_p6_change_detection_under_2ms_at_400k_agents`(4 並列の負荷で 5.55 ms > 2 ms=単独で回すと通る=1.30 秒・変化の検出=本段の外・2-4 の V7 と同じ型)。
- `lint-imports`: 5 契約とも KEPT。
- `tests/c7` は回していない(発注)。

## 12. 触った共有ファイル

進行役 `engine/systems/conductor.py` は触っていない(TM5 の予約の口は系 `body` の中=`resolve.advance_body` と、系 `world` の中の環境の過程=進行役の外)。

| 共有のファイル | 触った所 |
|---|---|
| `engine/systems/table.py` | 系 `body` の `paths` に `BD:body.*`・`reads` に `layers.body`/系 `world` の `paths` に `BD:body.*`/close_final の `reads` に `layers.body`(3-3 の `layers.experiment` の後)/見出しの段落 1 つ。系の数・順・`resolve_ops`・`writes.soa` は変えていない |
| `engine/systems/boxes.py` | `OWNER_NAMES` の末尾(`experiment` の後・〔rebase の後〕3-2 の `batching` の後)に `body`・`Layers.body`(既定 None) |
| 状態台帳 `engine/state_ledger.py` | 行 `BD`(外の状態の末尾=`M0L` の後・〔rebase の後〕`BW` の後)・`OWNER_CLASSES["body"]`(`experiment` の後・〔rebase の後〕`batching` の後)・`EXCLUDED` に 3 行(末尾)・`LEDGER_VERSION` の注(版は上げない) |
| 凍結の表 | `tests/engine/time/manifest_keys_frozen.json`(末尾に `body`・注)・`tests/engine/time/tick_word_allow.json`(使わなくなった名 `per_tick` を消した=salient の局所の名が体の層の `per_step` になった)。数の試験: `test_bridging_ledger.py`(形の数・項の合計)・`test_manifest_rules_bridges.py`(末尾の 9 つ)・`test_t0_tm9_fields.py`(末尾の並び)・`tests/perception/facts/test_percept_schema.py`(manifest の末尾の 9 つ)・`tests/engine/rights/test_rights_manifest.py`(末尾の 7 つ)・`tests/engine/tools/test_c0_phone_table_empty_and_declared.py`(末尾の 5 つ)・`test_state_ledger_10b.py`(行の数と並び)・`test_env_and_sections_10f.py`(末尾の鍵・`CONFIG_PATHS_SHA256`)・〔検収 L7〕`tests/engine/systems/test_stage_a_guard.py` の `FLAG_WRITERS`(配列の書きの旗を立てる場所=`engine/body/schedule.py` の `_open_and_call`=予約の列が自分の配列を書く口の中だけ開ける・SoA ではない)。試験の差し替えの口: `tests/engine/test_sim_time_T.py` の `advance_body` を包む関数が体の層の引数 `body` も受けて渡す形に(包む関数の引数の数だけ) |
| `cli.py` | `--body-schedule`(`--seat-release` の後)・設定の口(`economy_stage2` の前)・ランの種類の腕の条件 1 行 |
| manifest の末尾 | `engine/run.py`(`experiment` の後に `body`・〔rebase の後〕`batching` の後)・`engine/manifest_sections.py`(同じ並びで `body` の混ざった辞書) |
| つなぎの台帳 | §5 |
| ほか(発注の一覧の外で 3-2 と重なりうる所) | `engine/systems/state_io.py`(`hash_owners` の末尾)・`run_end.py`(`result.body_layer`)・`build.py`(体の層を作って渡す 4 か所)・`systems/body.py`(`advance_body` に体の層を渡す) |

## 13. 限界と仮採用(10-13b §0-3)

- **仮採用 1(引き直しの見つけ方)**: 活動の口からの知らせでなく、前に規則に通した後の写しとの比べ(体数ぶんの配列の比べ 7 本/刻み)。活動を書く口が resolve に約 40 か所あるため。T3 で口の知らせに替える候補(`BR-BODY-RESERVE-DETECT`)。
- **仮採用 2(積み上げは全員)**: エネルギーの積み上げ(食後の消費・収支=float32)は腕 reserve でも全員を毎刻み足す。足し算の順を変えると値が 1 ulp 動き、sweep と一致しない。予約するのは段の写し(空腹の語・疲れ・体感温度)の更新だけ(`BR-BODY-RESERVE-ACCUMULATE`・外す段 T3)。
- **仮採用 3(体感温度の予約も入れた)**: TM5 の文は空腹と疲れ。発注の「暑さの段」を体感温度の目盛で入れた。暑さ段と日陰は世界の側の変化(TM5 の「外の変化は驚き駆動とカレンダー 1b」)でもあるので、日の表を作るのは環境の過程・予約は体の層とした。
- **仮採用 4(状態台帳の軸)**: 行 `BD` は軸 1 diag(発注の宣言)。予約は「どの体を規則に通すか」を読む計算なので、厳密には読み手のある行。腕 reserve が sweep と同じ結果になることを byte-check と単体の試験で守る形にした。版は上げない。
- **仮採用 5(D18 の活動)**: 刻み 0 の活動(W17 の 0 時の行)は体の層に移さず予定の表の側に残した(体の値でなく予定の値)。
- **仮採用 6(書く口の数)**: `step` は部分 2 つ(内受容=系 body の刻みの頭/体感温度=系 world の 5 分の窓)。呼ぶ時刻が違うので 1 つの呼び出しにまとめていない。
- 腕 reserve は既定 off(T3 で有効)。腕は設定の指紋に入れず、状態のファイルの見出しにも書かない(結果が同じ=腕をまたいだ再開を許す=試験で確かめた)。ランの種類は既定と違えば arm。
- 予約の腕は今は sweep より遅い(§10)。
- 器だけの 3 件が「研究で意図しないと裏付けがあり選択を決めないもの」かは本段では確かめていない(値を入れる段の答申で)。倒れる率の出典は探していない(リサーチは親の段)。
- 見つけた HEAD の書き方の誤り(セル番号 ≥ セルの数の体の体感温度の添字)は新しい写像で舞台の外の値になる(ランでは起きない)。

## 14. 親に確かめてほしいこと

1. 〔検収の後〕byte-check の HEAD の写しの手順は本体 `82eeab0` の 10e の道具(`HEAD_TREE_FILES`)で直っている(§7-3)。`_bc` の下の誤った junction は親が .NET で外した。2-4 の検収の比べ(`parent_head_vs_vb24_4cfg.json`)の head の側がどう作られたかは、親の側で確かめてほしい(写しに規則の表と data が無ければ同じ食い違いが出る)。
2. 仮採用 1〜6(§13)。特に 1(写しとの比べ)と 4(行 BD の軸 1)。
3. 腕 reserve の速さ(§10): T3 の版上げで閉じた式の積み上げにするか(既定の値が動く)。
4. 器だけの 3 件と倒れる率の出典のリサーチの段取り。
5. 3-2(進行役の書き換え)との取り込み: `test_system1_placeholders.py` の 1 本は 1-2 の試験と同じく `conductor.run_system` を包んで知覚の事実を見る(3-2 で名が変われば両方を直す)。

## 15. 再現の手順(作業木の根で)

HEAD の写しは本体 `82eeab0` の 10e の道具の手順(`git archive` の写し+追跡ファイル 8 本+data への junction)。junction は回し終えたら
中を消さずに外す(`Remove-Item`・`rmdir` はドライブの根の保護で止まることがある=.NET の `Directory.Delete` で外す)。

```
D=docs/bench/analysis/wallbounce-1012/bd35
W=_bc
# HEAD の写し=src+追跡ファイル 8 本(規則の表・つなぎの台帳・予算の md・知覚契約・パターン台帳・錨 3 本)+ 構成の表
git archive d35a9b6 src docs/design/rules-table.json docs/design/bridging-ledger.json \
    docs/design/v2-budget-declaration.md docs/design/v2-perception-contract.md docs/design/v2-pattern-ledger.md \
    docs/bench/anchors/hunger_energy_build_anchors_v0.json docs/bench/anchors/hunger_energy_validation_anchors_v0.json \
    docs/bench/anchors/ssb2021_activity_prior_v0.json docs/bench/analysis/w6-regen-2026-09-28 | tar -x -C $W/head_src
cmd /c mklink /J <$W の Windows の道筋>\head_src\data <本体の data の Windows の道筋>     # data へのつなぎ(一時)
python docs/bench/analysis/wallbounce-1012/10e/byte_check_10e.py side --src $W/head_src/src --label head --scratch $W --out $W/head.json
pwsh -c "[System.IO.Directory]::Delete('<$W の Windows の道筋>\head_src\data')"      # つなぎだけを外す(中は消えない)
# 作業木の既定(段の境目の計器なし)と、2 つの腕の一致(両側とも計器あり=--gauge)と負の対照
PYTHONPATH=src python $D/tools/byte_check_bd35.py side --label wt_sweep --scratch $W --out $W/wt_sweep.json
python $D/tools/byte_check_bd35.py compare --a $W/head.json --b $W/wt_sweep.json --out $D/head_vs_sweep.json
PYTHONPATH=src python $D/tools/byte_check_bd35.py side --label wt_sweep_g --gauge --scratch $W --out $W/wt_sweep_g.json
PYTHONPATH=src python $D/tools/byte_check_bd35.py side --label wt_reserve --gauge --body-schedule reserve --scratch $W --out $W/wt_reserve.json
python $D/tools/byte_check_bd35.py compare --a $W/wt_sweep_g.json --b $W/wt_reserve.json --out $D/sweep_vs_reserve.json
PYTHONPATH=src python $D/tools/byte_check_bd35.py side --label wt_shift1 --gauge --body-schedule reserve --shift 1 \
    --only w6_v3_default,v3_mem_rel --scratch $W --out $W/wt_shift1.json      # −1 も同じ形
# 2 日と再開(計器は道具が立てる)・系ごとの指紋・性能
PYTHONPATH=src python $D/tools/two_day_bd35.py all --base v3_mem_rel --scratch $W --out $D/two_day_v3_mem_rel.json
PYTHONHASHSEED=0 PYTHONPATH=$W/head_src/src python $D/tools/probe_bd35.py side --label head --out $W/probe_head.json   # junction のある間に
PYTHONHASHSEED=0 PYTHONPATH=src python $D/tools/probe_bd35.py side --label reserve --body-schedule reserve --out $W/probe_reserve.json
python docs/bench/analysis/wallbounce-1012/vb24/tools/probe_systems_vb24.py --a $W/probe_head.json --b $W/probe_reserve.json --out …
PYTHONPATH=src python $D/tools/perf_bd35.py --sizes 5000,50000,390000 --steps 1440 --change-rate 0.0154 --move-rate 0.0078 --out $D/perf_bd35.json
```

## 16. 検収の後の直し(検収役=条件つき受入)と rebase

### 16-1. 検収の後の直し

| 項 | 直したこと | 確かめ |
|---|---|---|
| 中 M1 | 腕 sweep(既定)でも体ごとの予約の配列(int64 × 5 本=39 万体で 15.6 MB)を確保していた=行 BD の大きさの宣言「腕 sweep: 計器だけ」と食い違い → `BodySchedule.reset` は腕 reserve のときだけ体数の長さで作る(sweep は長さ 0)。宣言はそのまま | 試験 `test_sweep_allocates_no_per_agent_arrays_and_reserve_does`(sweep は 0・reserve は体数・刻み 0 で空に戻しても同じ) |
| 低 L6(親の判断) | 段の境目の計器(新旧の値の比べと鎖のハッシュ・種類ごとの数)は環境変数 `SHIBUYA_BODY_BOUNDARY_GAUGE=1`(か `BodyModel(gauge=True)`)のときだけ数える。既定は数えない=manifest の `body.boundaries`・`boundary_digest` は null(欄は残す)。持ち主の欄 `gauge`(設定・状態台帳の除外に足した)。道具: `byte_check_bd35.py --gauge`・`two_day_bd35.py` は立てて回す・`perf_bd35.py` に腕 `sweep_gauge` | 一致の試験(`test_body_reserve.py`)は立てて回す(自動の fixture)・manifest の試験で既定は null を確かめる。sweep の 1 刻みの時間は HEAD 相当より 5,000 体 +1.3%・39 万体 +0.5%(直す前 +19%・+3.7%・§10) |
| 低 L1 | `resolve.py` の docstring「30 tick ごとの」→「30 刻みごとの」 | — |
| 低 L2 | `processes/salient.py` は `BodyModel.collapse_draw` を通す(前は `rules.collapse_draw` を直に)。`processes/environment.py` の体感温度も `BodyModel.felt_temperature`・`felt_cells` を通す=`BODY_RULES` の `port` 欄と同じ口 | byte-check(下)で値は同じ |
| 低 L7 | `BodySchedule` に実行時の守り(`__setattr__`・`__delattr__`・持ち主の配列は口の外で `setflags(write=False)`・書く口の印 `_writing`)。窓の通し番号の覚えを口の中へ移した(`model.py` の直の代入をやめた) | 試験 `test_the_schedule_refuses_writes_outside_its_ports`(付け替え・消去・配列の書きを断る/負の対照=口の中は書けて出ると閉じる)・AST の試験の許す場所に `BodySchedule.__setattr__`・`__post_init__`・`test_stage_a_guard.py` の `FLAG_WRITERS` に 1 行 |
| 低 L8 | `state_hashes.py` の `VALUE_CLASSES` の `Scheduler` に注(今は行 BD の中だけを想定・ほかの行、とくに behavior・full に入る行が持つようになったら並べ方と型の検査を見直す) | — |
| 低 L3・L4 | §7-3・§14 の 1・§15(`_bc` の下に junction は残っていない=親が .NET で外した・10e の手順は本体 `82eeab0` の `HEAD_TREE_FILES` で直っている・再現の手順を「`git archive` の写し+追跡ファイル 8 本+data への junction(.NET で外す)」の形に) | — |
| 親が書く | L5(10e の `SWITCH_ENV` に `SHIBUYA_BODY_SCHEDULE`) | 触っていない |

確かめ(直した後の src):

- **byte-check 4 構成・既定(腕 sweep・計器なし)=HEAD**: `w6_v3_default`・`w6_v3_activity_off`・`w6_v1_default`・`v3_mem_rel` で 25 欄とも同じ([v2_head_vs_sweep_4cfg.json](v2_head_vs_sweep_4cfg.json)・HEAD の side は §7-1 と同じ写しの条件の物を使った・作業木は `src_is_worktree` 真・計器の欄は null)。
- **reserve=sweep 2 構成**(両側とも計器あり=`--gauge`): `w6_v3_default`・`v3_mem_rel` で 27 欄とも同じ([v2_sweep_vs_reserve_2cfg.json](v2_sweep_vs_reserve_2cfg.json))。計器ありの sweep の境目の列は直す前の 19 構成の side と同じ値。
- **性能**(§10 の表=測り直し・`perf_bd35.json`): 1 刻みの合計 5,000 体 pure 90.2・sweep 91.4・sweep_gauge 105.6・reserve 241.8 µs/39 万体 pure 11.41・sweep 11.47・sweep_gauge 11.70・reserve 12.75 ms。
- **範囲の試験**(`tests/engine/body tests/engine/systems tests/engine/time tests/engine/events tests/engine/test_resume_10d.py tests/engine/test_state_ledger_10b.py tests/engine/test_state_checks_10f.py tests/engine/test_energy_balance.py`・`-n 6`): 495 passed・1 failed(12 分 43 秒)。落ちた 1 本=`test_stage_a_guard.py::test_direct_flag_writes_live_only_in_known_places`(L7 の配列の旗を立てる場所が許す場所の表に無い)→ 表に 1 行足して回し直し `tests/engine/systems/test_stage_a_guard.py tests/engine/body` 83 passed。`lint-imports` 5 契約とも KEPT。

### 16-2. 本体 `60dadc4` への rebase(2-3c・3-2 窓の待ち行列・4-1 W21 の取り込みの後)

commit の無い枝の手順: 変えた追跡ファイル 29 本と新しい置き場(`engine/body/`・`tests/engine/body/`・記録)を控え → `git checkout` で土台 `d35a9b6` の形に戻す → `git rebase build/spatial-d102-prep`(早送り)→ 控えを 3 方向 `git merge-file`(base=`d35a9b6`・ours=控え・theirs=`60dadc4`)で合わせた。並びは「本体の分 → 3-5 の分」。

| ファイル | 衝突 | 合わせ方 |
|---|---|---|
| 13 本(`resolve.py`・`processes/{environment,runner,salient}.py`・`state_hashes.py`・`systems/{body,build,run_end,table}.py`・`perception/facts.py`・`test_stage_a_guard.py`・`test_sim_time_T.py`・`tick_word_allow.json`) | 0 | そのまま(`build.py` は本体の 5 行と自動で合わさった) |
| `systems/boxes.py` | 3 | `OWNER_NAMES`・注・`Layers` を 3-2 の `batching` の後に `body` |
| `systems/state_io.py` | 2 | `hash_owners` の注と鍵を `batching` の後に `body` |
| `run.py` | 2 | import と manifest の末尾(`batching` の後に `body`) |
| `manifest_sections.py` | 1 | `batching` の混ざった辞書の後に `body` |
| `state_ledger.py` | 4 | `LEDGER_VERSION` の注・行(`BW` の後に `BD`)・`OWNER_CLASSES`・`EXCLUDED`(どれも 3-2 の後) |
| `cli.py` | 3 | import・ランの種類の腕の条件(3-2 の `_BATCH.is_default()` の後に体の腕)・CLI の引数(`--batch-width-s` の後に `--body-schedule`) |
| `tests/engine/time/manifest_keys_frozen.json` | 2 | 本体の版の末尾に `body`・注の末尾に 3-5 の文(JSON は本体の版から作り直した) |
| 末尾を数える試験 6 本(`test_manifest_rules_bridges.py`・`test_rights_manifest.py`・`test_t0_tm9_fields.py`・`test_c0_phone_table_empty_and_declared.py`・`test_percept_schema.py`・`test_env_and_sections_10f.py`) | 各 1〜3 | 末尾の並びを `…, "experiment", "batching", "body"` に(数える長さを 1 つずつ足した)・`TM32_KEYS` の後に `BD35_KEYS` |
| `test_state_ledger_10b.py` | 2 | 行数 外 114・全体 205(本体)→ 外 115・全体 206・行の並びの末尾 `…, "M0L", "BW", "BD"` |
| `test_bridging_ledger.py` | 1 | expedients 171(本体=2-3c 144+W21 27)→ 183(+3-5 の 12)・見出しの数 83 と項の合計 358 はそのまま |
| `docs/design/bridging-ledger.json` | 13 | 本体の版(末尾=3-2 の 4 行 → 4-1 の 27 行)に、3-5 の直し(既存の ③ の 3 行の項の数と注)と 12 行を末尾に当て直した(道具=同じ直しの台本) |
| 記録の道具 `tools/probe_bd35.py` | — | 外す行に 3-2 の `BW` を足した |

数の変化(本体 `60dadc4` → 3-5 を合わせた後):

| 数 | 本体 | 合わせた後 |
|---|---|---|
| 状態台帳の行(外/全体) | 114 / 205 | 115 / 206 |
| manifest の一番上の鍵 | 末尾 `batching` | 末尾 `batching`, `body` |
| `CONFIG_PATHS_SHA256` | `564d5c72…ffbeaf57` | `8c1610ad…5209d43`(合わせた後の表で計算し直した) |
| つなぎの台帳 active(`bridges_count` の見込み)/行 | 375 / 386 | 387 / 398 |
| 形 expedients | 171 | 183 |

確かめ(rebase の後):

- **範囲の試験**(`tests/engine/body tests/engine/systems tests/engine/batching tests/engine/time tests/engine/events tests/engine/bridging tests/engine/test_resume_10d.py tests/engine/test_state_ledger_10b.py tests/engine/test_state_checks_10f.py tests/engine/test_env_and_sections_10f.py tests/engine/test_energy_balance.py tests/engine/rights tests/engine/tools tests/perception`・`-n 6`): **1,201 passed・0 failed**(12 分 24 秒)。`lint-imports` 5 契約とも KEPT。
- **byte-check 既定 4 構成**: HEAD=本体 `60dadc4` の写し(本体の 10e の道具の手順=`git archive` の src と追跡ファイル 8 本と構成の表+data の 3 本=`HEAD_TREE_FILES` が全部そろう=`tree_missing` 空)と作業木の既定(腕 sweep・計器なし・`src_is_worktree` 真)が `w6_v3_default`・`w6_v3_activity_off`・`w6_v1_default`・`v3_mem_rel` で 25 欄とも同じ([rb_head60_vs_sweep_4cfg.json](rb_head60_vs_sweep_4cfg.json))。final は rebase の前と同じ値(`b8eadcb5…`・`c88ba910…`・`e1288e09…`・`768b2262…`=3-2・4-1 は既定の結果を変えない)。
  - data は junction でなく、本体の data から 3 本(祝日の CSV・OSM の 2 本)をバイトのまま写した(道具の `HEAD_TREE_FILES` の data の 3 本と同じ物=写しの木の検査が通る)。前に junction の後片付けで外す口が断られたため、ドライブの根を指す誤りや本体の data へのつなぎを `_bc` に残さない形を選んだ。世界資産は両側とも作業木の根の `data/world/v2`(本体の v2)を読む。
- **reserve=sweep 2 構成**(両側とも計器あり): `w6_v3_default`・`v3_mem_rel` で 27 欄とも同じ([rb_sweep_vs_reserve_2cfg.json](rb_sweep_vs_reserve_2cfg.json))。計器ありの境目の列は rebase の前の 19 構成の値と同じ。

