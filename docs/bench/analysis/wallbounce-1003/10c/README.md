# 10c 状態を持つ乱数 2 本をカウンタ型に(Q8・A5 (a′))

基準: HEAD `adc6da8`(ブランチ `build/spatial-d102-prep`)。アジェンダ [v2-d102-foundation-implementation-agenda.md](../../../../design/v2-d102-foundation-implementation-agenda.md) §3 と末尾の A5、ユーザー決定 [v2-wallbounce-decisions-2026-10-03.md](../../../../design/v2-wallbounce-decisions-2026-10-03.md) §3-2・§3-8。

## 0. 要点

1. **既定の結果は動いていない**。HEAD の `git archive` の写しと作業木(既定 `stateful`)で 19 構成(W6 の 15 腕+店の記憶・関係・古典・古典+記憶+関係。mock/classical 5,000 体・seed 1・1 シミュ日・テープつき)を回し、final・呼数・blocks・calls の 14 列が **19/19 一致**([byte_check.json](byte_check.json) の `rows`・`all_ok: true`)。golden v3 `993276d5e5bb5cbe`/69,978・帰無 `72cb9cd52982da74`/100,439・関係 on `40409ebed834126b`/72,930 はこの中。classical 1,500 体の golden `4f78f3c0`/25,808 は既存のテスト `tests/engine/test_classical_social.py` で一致。
2. **counter に切り替えると**、実世界・seed 1 で「倒れる」が 0 件 → 5 件、出動が 0 → 5 件、顕著行為の事象(倒れる+隊の到着)が 0 → 10 件になる。気づいた延べ人数が 290〜1,151 人増え、そこから起きる呼数が構成により −185〜+1,444 件動く(§4)。
3. **件数の分布は同じ桁**。率を既定の ×1000 にした合成世界で 5 seed を比べ、決めた線(平均の差 ≤ 2 × seed 間の標準偏差・分散の比 ≤ 10)をすべての量で満たした(§3)。
4. **再開で保存が要る状態は増えない**。counter では 2 本の Generator が `None` になり、full-hash に入る道筋で値を持つものは stateful の部分集合になる。差はちょうどこの 2 本(台帳の軸 2 のテスト)。
5. 報告した問い 3 件には親の答えが出た(§6)。問い 3 の後半(再生の突き合わせ)は今回入れた(§7)。別のサブの検収([review-10c.md](../review-10c.md)・結果を動かす欠陥 0)を受けた直しは §10。

## 1. 入れたもの

| 場所 | 中身 |
|---|---|
| `src/shibuya/core/rng.py` | `RNG_SCHEMES = ("stateful", "counter")`・`DEFAULT_RNG_SCHEME = "stateful"`・`check_rng_scheme`・`run_tick_key(day_key0, T, tick_seconds)` |
| `src/shibuya/engine/processes/salient.py` | 引数 `rng_scheme`。counter では `rng = None` にして、「倒れる」の乱数を毎 tick `stream(seed, "world.salient.counter", 0, 鍵の時刻)` から作る。選ばれた体は id の昇順に並べ直してから出動を呼ぶ |
| `src/shibuya/engine/processes/civic.py` | `PublicServiceDispatchProcess` に引数 `rng_scheme`。counter では `rng = None` にして、出動ごとに `stream(seed, "world.public_service_dispatch.counter", 0, 鍵の時刻, セル, k)` から遅れを引く |
| `src/shibuya/engine/processes/runner.py` | 引数 `rng_scheme` を出動と顕著行為へ渡す |
| `src/shibuya/engine/run.py` | `run_day(rng_scheme=…)`(先頭で検査。再生ではテープの脇の meta と突き合わせる=§7)・テープの脇の `run_meta.json` に `rng_scheme` を書く・`RunResult.rng_scheme`・manifest の `rng_scheme`(列を足しただけ)・`--rng-scheme` を `add_calendar_args` に入れた(`engine.run` と `shibuya.cli` が同じ関数を使うので綴りは 1 か所) |
| `src/shibuya/cli.py` | コメントだけ(口は `add_calendar_args` から入る) |
| `src/shibuya/engine/state_ledger.py` | 台帳の行 O46・O47 の注記(「rng は stateful だけ Generator・counter では None」)。除外の一覧に、新しい属性(`rng_scheme`・出動の `master_seed`・`day_index`)を定数として、k の数え(`_k_tick`・`_k_next`)をキャッシュとして理由つきで足した。行の数と軸の判定は変えていない(`LEDGER_VERSION` もそのまま) |
| `tests/engine/test_calendar_sites.py` | `calendar_kwargs_from_args` の戻り値の辞書に `rng_scheme: "stateful"` が増えたので期待値を直した |
| `tests/engine/test_10a_review_fixes.py` | `run_meta.json` の中身の期待値 3 か所に `rng_scheme: "stateful"` を足した |

stateful の道は Generator の作り方も引く順も今のまま(`g = self.rng` に置き換えただけ)。

## 2. 鍵の形と k の決め方

- **顕著行為の発生**: 用途名 `world.salient.counter`、カウンタは `(0, 鍵の時刻)`。毎 tick 作り直すので状態を持たない。
- **出動の遅れ**: 用途名 `world.public_service_dispatch.counter`、カウンタは `(0, 鍵の時刻, セル, k)`。
- **鍵の時刻** = `run_tick_key(day_key(0), T)` = `day_key(0) × 1 日の tick 数 + T`。`day_key(日) = day_key(0) + 日` なので、これは「日の鍵 × 1 日の tick 数 + 日の中の tick」と同じで、T と一対一。`--calendar-weekday real` では `day_key(0) = 0` なので **T そのもの**。既定の `day_index` モードでは `day_index × 1 日の tick 数 + T`(tick 60 秒なら × 1,440)になり、stateful が日の鍵に入れていた `day_index` の違いを残す(問い 1)。
- **k**: 同じ T・同じセルの出動を、呼ばれた順に 0 から数えた番号。呼び手(顕著行為)は、その tick に倒れた体を **id の昇順**に並べてから呼ぶ。数えは T が変わると空に戻す、tick の中だけのもの。tick の境目で再開すれば空から数え直すので同じ値になる。事象の通し番号は使わない。
- **カウンタの 1 語目を 0 にした理由**: numpy の Philox は 1 語目から 1 ずつ進む。実測で `stream(1, "x", 0, 5)` から 1 ブロック(4 語)引いた後の列は `stream(1, "x", 1, 5)` の頭と同じだった。1 語目に鍵の時刻を置くと、ある tick で 2 ブロック以上引いたときに隣の tick の列と重なる。1 語目を 0 にしておけば、2^64 ブロック引くまで重ならない(問い 2)。
- 用途名を stateful と分けたのは、同じ鍵の Philox の列が重ならないようにするため。

## 3. 試験の結果(既知の答え)

新しいテスト `tests/engine/processes/test_rng_scheme_10c.py`(21 件・すべて通過。うち 2 件は §7 の再生の突き合わせ、5 件は §10 の検収後の直し。(iii) の 5 seed 比較のテストは §10 で z 検定のテスト 2 件に置き換えた)。

| 番号 | 中身 | 結果 |
|---|---|---|
| (i) | counter の腕を 2 回回す(合成世界・60 体・1 日・率 ×1000) | final・呼数・checkpoint・顕著行為の件数・出動の件数・気づいた数がすべて一致。stateful とは final が違う |
| (ii) | `test_civic.py` の 400 件(同じ tick・16 セル × 25 件)を counter で | どのセルでも到着の tick が 2 種類以上。丸める前の引きは 400 件すべて違う。平均の遅れは既存の範囲の中 |
| (ii′) | 状態を持たない | 前の tick に 12 件出動していても、(T, セル, k) の引きは同じ。顕著行為も、前の 30 tick を回したかどうかで T=30 の事象が変わらない(stateful は変わる) |
| (ii″) | k の順 | 1 tick に複数の出動が出たとき、呼ばれた体の id が昇順 |
| (iii) | 率 ×1000 の合成世界で件数の分布を比べる | 下の表。すべて線の中 |
| (iv) | 既定の率・seed 1 | 実世界(5,000 体): stateful 0 件・counter 5 件(§4)。合成世界(2,000 体): stateful 0 件・counter 1 件 |
| (v) | `run_day(sim_days=2)` で鍵に T が入っているか | 顕著行為の鍵の時刻が T = 0〜2,879 の 1 本ずつ。1 日目と 2 日目の出動の鍵に重なりが無い。T=0 と T=1,440 の引きは違う。stateful の 2 日のランは counter の用途名を 1 本も作らない |
| (vi) | 再開をはさんでも同じ列 | 10d で確かめる。今は「保存が要る状態が増えない」ことを台帳の軸 2 で固定(下) |
| 軸 2 | full-hash に入る道筋の値を stateful と counter で比べる | 道筋の集合は同じ。Generator は stateful に 2 本(`runner.salient.rng`・`runner.dispatch.rng`)、counter では 0 本で `None`。counter で値を持つ道筋は stateful の部分集合で、差はこの 2 本だけ |

**(iii) の判定**(§10 で改めた): **主**は tick ごとの件数を既知の答え(ポアソン)と比べる z 検定(§10)。下の表の 5 seed の比較(平均の差 ≤ 2 × (2 方式の seed 間の標準偏差の大きい方)、かつ分散の比 ≤ 10)は**副**の判定として記録に残す。5 seed(1〜5)。2 つの段で測った([count_dist_x1000.json](count_dist_x1000.json)・[count_dist_x1000.py](count_dist_x1000.py))。

| 段 | 量 | stateful 平均 | counter 平均 | 差 / 線 | 分散の比 | 判定 |
|---|---|---|---|---|---|---|
| 過程だけ(25 セル・1,000 体) | 倒れる(=出動) | 296.6 | 297.2 | 0.6 / 43.2 | 3.17 | 合格 |
| 〃 | 平均の遅れ[分] | 9.02 | 9.19 | 0.18 / 0.70 | 1.14 | 合格 |
| mock の 1 日(139 セル・2,000 体) | 倒れる(=出動) | 600.8 | 592.6 | 8.2 / 59.8 | 4.36 | 合格 |
| 〃 | 顕著行為の事象 | 1,197.4 | 1,182.4 | 15.0 / 122.3 | 4.42 | 合格 |
| 〃 | 気づいた延べ | 18,208.8 | 17,976.8 | 232 / 2,248 | 2.54 | 合格 |
| 〃 | 平均の遅れ[分] | 9.02 | 9.17 | 0.15 / 0.38 | 1.14 | 合格 |
| 〃 | 呼数 | 18,335.4 | 18,101.2 | 234 / 597 | 2.72 | 合格 |

期待値: 1,000 体 × 0.3/日 = 300 件、2,000 体 × 0.3/日 = 600 件。遅れは対数正規(中央値 8 分・σ 0.5)の平均 8 × e^0.125 ≈ 9.06 分。どちらの方式も期待値のそばにある。

既定の率の合成世界(2,000 体・5 seed)では stateful 0,0,1,0,0 件・counter 1,0,0,2,0 件(期待値 0.6 件/日)。2 方式とも 0 件だった seed 2 と 5 は final も同じだった(乱数の方式は事象が出ない限り結果に効かない)。

実世界 seed 1 の counter の 5 件は、期待値 1.5 件に対して多め(ポアソンで 5 件以上は約 1.9%)なので確かめた。顕著行為の乱数だけを 300 seed 引くと、1 日の件数は counter 平均 1.55・分散 1.71、stateful 平均 1.51・分散 1.32。偏りは無く、seed 1 がたまたま多い側だった。

## 4. byte-check と counter で動く量

手順は [byte_check_10c.py](byte_check_10c.py)(10b の手順に件数の欄と `--rng-scheme` を足した)。HEAD の写しは短いパスに置いた(深いパスだと numba のキャッシュ名が Windows のパスの長さを超える)。

- 既定(stateful)の作業木と HEAD: **19/19 一致**(14 列)。HEAD 側の件数も 19 構成すべてで倒れる 0・出動 0。
- counter の腕(作業木・`--rng-scheme counter`)。stateful との差。manifest の `rng_scheme` は両方とも正しく出た:

| 構成 | 倒れる | 出動 | 顕著行為の事象 | 気づいた延べ | 呼数 stateful → counter(差) | blocks の行の差 | 平均の遅れ[分] |
|---|---|---|---|---|---|---|---|
| w6_v3_default(golden v3) | 0 → 5 | 0 → 5 | 0 → 10 | 352 | 69,978 → 69,796(−182) | −13 | 8.8 |
| w6_v3_activity_off | 0 → 5 | 0 → 5 | 0 → 10 | 290 | 58,570 → 59,231(+661) | +11 | 12.0 |
| w6_v1_default | 0 → 5 | 0 → 5 | 0 → 10 | 609 | 60,970 → 61,931(+961) | +3 | 11.8 |
| w6_v1_derive_v2_1 | 0 → 5 | 0 → 5 | 0 → 10 | 634 | 54,285 → 54,786(+501) | +11 | 4.4 |
| w6_v2 | 0 → 5 | 0 → 5 | 0 → 10 | 536 | 60,901 → 61,135(+234) | +4 | 12.0 |
| w6_v1_edge | 0 → 5 | 0 → 5 | 0 → 10 | 789 | 54,150 → 54,121(−29) | +8 | 5.0 |
| w6_v2_edge | 0 → 5 | 0 → 5 | 0 → 10 | 786 | 54,170 → 53,985(−185) | +5 | 9.8 |
| w6_v1_edge_plateau | 0 → 5 | 0 → 5 | 0 → 10 | 471 | 55,173 → 55,304(+131) | +4 | 5.8 |
| w6_old_*(6 本) | 新しい側の同名の腕と同じ値 | | | | | | |
| w6_golden_null_arm(帰無) | 0 → 5 | 0 → 5 | 0 → 10 | 1,151 | 100,439 → 100,947(+508) | +10 | 9.0 |
| v3_mem_store | 0 → 5 | 0 → 5 | 0 → 10 | 352 | 69,978 → 69,796(−182) | −13 | 8.8 |
| v3_mem_rel(関係 on) | 0 → 5 | 0 → 5 | 0 → 10 | 472 | 72,930 → 73,468(+538) | +120 | 10.0 |
| v3_classical | 0 → 5 | 0 → 5 | 0 → 10 | 432 | 97,563 → 97,903(+340) | +67 | 11.2 |
| v3_classical_mem_rel | 0 → 5 | 0 → 5 | 0 → 10 | 523 | 110,395 → 111,839(+1,444) | +76 | 8.4 |

final はすべての構成で動く(counter の各構成の final は byte_check.json の `counter_moves`)。倒れる件数はどの構成でも 5 件で同じ(発生は体の配置に依らず、ポアソンの数は鍵だけで決まる)。遅れの平均が構成で違うのは、倒れる体とセルが配置で違い、鍵の (セル, k) が変わるため。

10e で counter を既定にするときの材料: A6 の「カウンタ型の乱数への切替で動くのは、顕著行為と出動の件数だけであること」は、**件数だけでは済まない**。事象が出ると、気づいた体が起きて呼が増減し、final・呼数・blocks が動く(上の表)。動いてよい量の書き方を 10e のアジェンダで決める必要がある(問い 3)。

## 5. 確かめたテスト

- 新規 `tests/engine/processes/test_rng_scheme_10c.py` 21 件 通過。`test_tape_wiring.py`・`test_tape.py` も通過。
- 既存: `tests/engine/processes/`(全件)・`test_state_ledger_10b.py`(台帳の網羅の検査と AST の検査を含む)・`test_processes_run.py`・`test_sim_time_T.py`・`test_t3_manifest.py`・`test_calendar.py`・`test_calendar_sites.py`(期待値を直した 1 件)・`test_10a_review_fixes.py`・`test_response_delay.py`・`test_determinism_t1_t2_t4.py`・`test_classical_social.py`・`tests/c8/test_ablations_table.py`・`tests/c6/test_t9_diagnostics.py`・`tests/test_cli_*.py` 通過。全体のテストは親が回す。

## 6. 見つけた問い(止めたもの)と親の答え

親の答え(2026-10-04):
- 問い 1: 鍵は `day_key(0) × 1 日の tick 数 + T` のままでよい。理由は、`--day` が違うランが同じ乱数を引かないようにするため。10a の `day_key`(既定の `day_index` モードでは日の鍵に `day_index` を入れて今の値を保つ)と同じ考え方である。
- 問い 2: 10c では直さない。呼び手の一覧(どこで何語引くか)を下の表にした。10f で検査を足すかを決める。
- 問い 3: 10e の A6 の文言は親が直す。再生の突き合わせは今回入れた(§7)。

以下は報告したときの問いの文面。

1. **鍵の時刻に `day_key(0)` を入れたこと**(親の判断を仰ぐ)。指示の形は `(seed, 名前, T)`。T は毎ラン 0 から始まるので、T だけだと既定の `day_index` モードで `--day 0` と `--day 3` のランが同じ引きになり、stateful(日の鍵 `day_index` を入れていた)より区別が減る。そこで `day_key(0) × 1 日の tick 数 + T` にした。`real` モードでは `day_key(0) = 0` なので T そのもの。T だけにするなら `run_tick_key` の 1 行を変えるだけ(既定は動かない)。なお `real` モードでは stateful も counter も開始日の違いが鍵に入らない(どちらも日の鍵が 0 から)。
2. **ほかの `stream()` の呼び手の 1 語目**(報告だけ・直していない)。Philox は 1 語目から進むので、`stream(seed, 用途, a, b)` から 1 ブロック(4 語)より多く引くと、`stream(seed, 用途, a+1, b)` の頭と同じ列になる。1 語目に tick や体の id を置いている呼び手が多い(例 `engine.chooser`・`policy.classical`・`conversation.invite`・`llm.mock`・`perception.p_notice`(1 語目は事象の番号)・`body.weight`)。4 語以内なら重ならない。親の答えを受けて、1 回に何語引くかを下の表にした。
3. **10e の「動いてよい量」**。§4 のとおり、counter への切替では件数のほかに final・呼数・blocks も動く。A6 の文言「動くのは件数だけ」を「事象とそこから起きる起床・呼だけ」と読むかを 10e のアジェンダで決める必要がある。あわせて、再生(replay)では録画と同じ `rng_scheme` でないと結果がずれる。今は `response_delay` のようにテープの脇の meta と突き合わせる仕組みは入れていない(既存の実 LLM テープはすべて stateful なので、今のところ食い違いは起きない)。

### 6-1. 1 語目が値ごとに変わる `stream()` の呼び手と、1 回に引く語数

1 回に引く 64 bit の語の数は、numpy の Philox の状態(カウンタと buffer_pos)から実測した(200 回の最小〜最大)。4 語を超えると、1 語目を 1 つ進めた流れの頭と重なる(実測: `stream(1, "x", 0, 5)` の 5 語目以降 = `stream(1, "x", 1, 5)` の頭)。1 語目がハッシュの値(`build.w13`・`world.environment` の実日の選択)の呼び手と、1 語目が定数の呼び手は除いた。10c で入れた 2 本は 1 語目が 0。

| 用途名(場所) | 1 語目 | 1 回に引くもの | 語数 | 4 語を超えるか |
|---|---|---|---|---|
| `engine.chooser`(engine/chooser.py:269) | tick | `random()` 1 回 | 1 | 超えない |
| `policy.classical`(engine/classical.py:612) | tick | `random()` 2 回 | 2 | 超えない |
| `conversation.invite`(engine/conversation.py:384) | tick | `random()` 1 回 | 1 | 超えない |
| `llm.mock`(llm/mock.py:185) | tick | 31 bit の整数 3 個 | 2 | 超えない |
| `llm.mock` v3(llm/mock.py:197) | tick | 31 bit の整数 6 個 | 3 | 超えない |
| `llm.mock` の移動・店の対象(llm/mock.py:215・231) | tick | `random()` 1 回+31 bit の整数 1 個 | 2 | 超えない |
| `perception.attention.p_see`(attention.py:225。呼び手は renderer.py:1659・familiarity.py:311,319) | tick | `random(n)`。呼び手はどれも n=1 | 1 | 超えない |
| `perception.p_notice`(p_notice.py:478) | **事象の番号**(同じ tick の何番目か) | `random((2, 候補の数))` | 2 × 候補の数 | **候補が 3 人以上で超える**。同じ tick に事象が 2 件以上あると、事象 k の後ろの方の引きが事象 k+1 の頭と同じになる |
| `body.weight`・`body.eer`(engine/energy.py:382-383) | 体の番号 | `standard_normal()` 1 回 | ふつう 1〜3(正規乱数の棄却があると増える) | **まれに超える**。seed 1・5,000 体で `body.weight` は体 1017、`body.eer` は体 4316 が 5 語以上を引き、次の体の流れの頭と重なる(検収 R3)。200 回の試しでは見えない頻度で、効きは無視できる |
| `world.delivery_inbound`(goods_flow.py:336) | 日の鍵 | POI 数 × (整数・`random`・幾何分布) | POI 数の約 2.5 倍(500 POI で 1,258〜1,283) | **超える**。日の鍵 d の列の後ろが d+1 の列の頭と重なる(複数日のランで日をまたいで相関しうる) |
| `world.road_works`(logistics.py:291) | 日の鍵 | `choice(辺の数, 工事の数, 重複なし)` | 辺の数と工事の数による(合成の 139 から 3 個で 3) | **実世界の既定ランでは既に超えている**(2 ブロック=5 語以上・検収 R4)。日の鍵が 1 違うラン同士で `delivery_inbound` と同じ形に重なる |
| `world.large_event`(civic.py:478) | 日の鍵 | `choice(セル数, 3, 重複なし)` | 3 | 超えない |
| `world.delivery_last_mile`(logistics.py:125) | 日の鍵 | 作るだけで引かない(予約) | 0 | 超えない |
| `world.salient`・`world.public_service_dispatch`(stateful の 2 本) | 日の鍵 | 1 日ずっと同じ流れを進める | 1 日で数千 | **超える**。日の鍵 d の流れを進めると d+1 の流れの頭に入る。`sim_days=2` の今の作りでは 1 本を通しで使うので 1 ランの中では重ならないが、`--day` が 1 違うラン同士では列がずれて重なる |
| `w16.sample.stratum`(agents/population.py:334) | 層の番号 | `permutation(層の人数)` | 層の人数による(100 人で 63〜79) | **超える**。隣の番号の層の並べ替えと列が重なる |
| `w16.*`(build/pop/w16_population.py:214・223・1034・1039) | 呼び手が渡すカウンタ | `permutation(n)`・`random(n)`・`integers(…, need)` | n による | n が 4 を超えると超えうる(構築時だけ・ランの外) |

## 7. 再生の突き合わせ(親の答え 3 を受けて追加)

- 録画では、テープの脇の `run_meta.json` に `rng_scheme` を書く(10a の `response_delay` と同じ場所・テープの版と列は変えない)。
- 再生では、テープの値と今の設定が違えば `ValueError` で止める(文言は「乱数の方式がテープと違う: テープは rng_scheme=counter・今の設定は stateful(--rng-scheme を録画と同じ値にする)」)。
- 値の無いテープ(10c より前の録画)は `stateful` とみなす。既存の実 LLM テープ 17 本は既定のまま再生できる。〔検収後の直し〕値の無いテープでは警告(`RngSchemeWarning`)を 1 回出す(§10 (b))。
- 検算(テスト 2 件): counter で録って既定(stateful)で再生すると止まる / counter で再生すると final が一致し、テープの取りこぼしは 0。stateful で録って counter で再生すると止まる / 既定で再生すると一致。`run_meta.json` から `rng_scheme` を消したテープは、既定で再生すると stateful で回って final が一致し、counter で再生すると止まる。
- 既定の結果: final・呼数・blocks・calls は変わらない(meta は parquet の外)。既定 v3 と帰無の 2 本で byte-check をやり直した(§8)。

## 8. 再生の突き合わせを入れた後の byte-check

[byte_check_after_replay_check.json](byte_check_after_replay_check.json): 既定 v3 と帰無の 2 本を、HEAD の写しと作業木で 14 列を比べた。結果は **2/2 一致**(既定 v3 `993276d5e5bb5cbe`/69,978・帰無 `72cb9cd52982da74`/100,439)。作業木のテープの `run_meta.json` は `{"response_delay": 1, "rng_scheme": "stateful"}`。

## 9. 後片付け

byte-check に使った HEAD の写しとテープ(`C:/w10c`)は、検収が済んだら消してよい(親が消す)。

## 10. 検収後の直し([review-10c.md](../review-10c.md) を受けて)

検収の結果は、結果を動かす欠陥 0・byte-check 一致。親の指示で次を直した。src に触ったのは (b) の警告だけで、既定の結果は変わらない(警告は再生で値の無いテープのときだけ出る)。

**記録の誤り(R1〜R4)**
- R1: テストの件数を今の数(21 件)に直した。§0-5 の「止めた問い」は「親の答えが出た」に直した。
- R2: 鍵の式の「× 1440」を「× 1 日の tick 数」に直した(コードは前から `86,400 // tick_seconds` で正しい)。
- R3: §6-1 の `body.weight`・`body.eer` を「まれに超える(5,000 体で 1 体ずつ)・効きは無視できる」に直した。
- R4: §6-1 の `world.road_works` を「実世界の既定ランでは既に超えている」に直した。

**テストの欠け(T1〜T3)と、検収が勧めた単体の守り**
- T1 `test_run_tick_key_multiplies_by_the_ticks_per_day_not_1440`: tick 30 秒で `run_tick_key(1, 0, 30) == 2,880 == run_tick_key(0, 2,880, 30)`。定数 1,440 にすると落ちる。
- T2 `test_day_key0_enters_the_key`: 日の鍵 0 と 3 の同じ T で出動の遅れが違う。日の鍵 1 の T=100 と日の鍵 0 の T=1,540 が同じ。`test_run_day_passes_day_key0_to_the_counter_key`: `run_day(day_index=3)` の顕著行為の鍵が `(0, 3 × 1,440 + T)`。鍵から `day_key(0)` を落とすとどちらも落ちる。
- 検収 §5 の M3・M9: `test_counter_streams_have_their_own_names_and_word0_is_zero`(counter の用途名が stateful と別・カウンタの 1 語目が 0)を単体で足した(2 日のランの 1 本だけに頼らないため)。
- T3: (iii) の主の判定を z 検定に替えた(`test_per_tick_counts_match_the_known_poisson_rate`)。5 seed × 1,440 tick = 7,200 tick の「倒れる」の件数を、既知の答え(ポアソン・1 tick の期待値 λ = 率 × 体数 / 10,000 / 1 日の tick 数 = 3,000 × 1,000 / 10,000 / 1,440 = 0.2083)と比べる。
  - 合計の z = (Σx − Nλ) / √(Nλ)(期待値 1,500 件・標準誤差 38.7 件)。
  - 分散の指数の z: D = Σ(x − x̄)² / x̄ はポアソンなら自由度 N−1 の χ² に従うので、z = (D − (N−1)) / √(2(N−1))(平均と分散がそろうか=ポアソンらしさ)。
  - 線は |z| ≤ 3。根拠: 正規近似で両側 p ≈ 0.0027。1 方式に 2 つ、2 方式で 4 つの z を見るので、全部が正しくても落ちる率は約 1%(5 seed の比較の約 5% より小さい)。検出力: 率が 10% 低いと合計の z の期待値は −150 / 38.7 ≈ −3.9 で、約 8 割の確率で落ちる(5 seed の比較は約 3 割しか捕まえない=検収 T3)。既知の答えのテスト `test_poisson_z_catches_a_ten_percent_lower_rate` で、10% 低い率のポアソン列が z < −3 になることを固定した。
  - 結果([count_dist_x1000.json](count_dist_x1000.json) の `process_x1000.main_poisson_z`): stateful 合計 1,483 件(z −0.44・分散の指数の z +0.27)、counter 1,486 件(z −0.36・−1.31)。どちらも合格。mock の 1 日(2,000 体)の段は tick ごとの件数を取っていないので、1 日の合計だけを比べた(`run_day_x1000.main_poisson_z_total`): 期待 3,000 件に対し stateful 3,004 件(z +0.07)・counter 2,963 件(z −0.68)。
  - 5 seed の比較(§3 の表)は副の判定として記録に残した(`secondary_5seed`)。テストからは外した(seed を固定していても、合成世界の作りが変わると理由なく落ちる率が約 5% あるため)。

**問いへの答え**
- (a) 名前 `rng_scheme` は切替口の名前(アジェンダどおり)として残す。manifest の設計の `rng.scheme`(生成器の名前 `"numpy-philox4x64"`・`manifest/schema.py`)とは別物である。`run.py` の `run_day` の docstring と `_resolve_rng_scheme` の docstring にも 1 行書いた。
- (b) 再生で `rng_scheme` の値の無いテープは stateful とみなし、**警告(`RngSchemeWarning`)を 1 回出す**ようにした(`response_delay` と同じ形・同じテープでは 2 回目は出さない)。10e で既定を counter にしたとき、旧テープが黙って回らないことに気づけるようにするため。テスト `test_a_tape_without_the_value_is_replayed_as_stateful` で、警告が 1 回だけ出ること・2 回目は出ないことを確かめた。
- (c) 既存の重なり P1〜P3(`w16.sample.stratum`・`perception.p_notice`・`world.delivery_inbound`)は直さない(K19)。
