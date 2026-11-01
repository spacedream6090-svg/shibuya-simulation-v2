# 第 1 期 1-1 時計 T0(TM7・TM8)の実装の記録

- 実装役 Opus 5.5。作業木の枝 `1-1/t0`(HEAD `3e0ff73`)。commit は親。
- 正: [口の約束 1-1](../../../../design/v2-foundation-contracts-2026-10-13.md)(〔決定〕〔1〕〔2〕は allow 表と報告)・[計画 第 1 期 1-1](../../../../design/v2-implementation-plan-2026-10-12.md)(TM9 を含む)・[指示書 10-12](../../../../design/v2-wallbounce-decisions-2026-10-12.md) の TM7・TM8・TM9・[回答 10-13b](../../../../design/v2-answers-2026-10-13b.md) §0-3・[1-0 の記録](../run-day-decomp/impl-1-0.md)(ハッシュに入る名=台帳の鍵・道筋・持ち主は変えない)・[用語集](../../../../design/v2-glossary.md)(「tick」の語は使わない)。
- 数は実測。生の出力(テープ・side の JSON)は git の外の作業用の置き場(作業木の `_bc/`)に置いた。比べた結果だけをこのフォルダに置く: [byte_check_t0.json](byte_check_t0.json)・[manifest_check_t0.json](manifest_check_t0.json)。

## 0. 結論

- 時間の定数を `core/time_consts.py` に集め、`src/shibuya` の時間の直書きを **281 か所 → 0 か所**にした(allow の表は空)。置き換えは 1 か所ずつ同じ値の名にしただけで、式の形は変えていない。
- `TickCtx` に `t_ns`(通しのナノ秒)と `tod_s`(その日の秒)を足した。進行役はランの設定の幅(`RunConfig.tick_seconds`)を渡す。`core/types.py` に `SimTime`(ナノ秒の整数の別名)を足した。
- 乱数の鍵は 10c の counter のまま。`rng.time_key_from_t_ns` を足したが、呼び手は無い(準備だけ)。
- 注釈と docstring の「tick」は、`core/` と `engine/systems/` で 108 行 → 0 行にした。識別子は名を替えず、「tick」を含む 158 個の名を理由つきで凍結した。新しい名を足すと試験が落ちる。
- TM9 の欄(判断モデルと LLM を分けた呼び出し数・時計の種類と幅・つなぎの台帳の数)を、manifest の末尾と日次の記録に足した。
- **結果不変**: byte-check は 19 構成すべてで、25 欄とも HEAD と同じだった。2 日のラン(final `912446bd2b42b6ab`・140,913 呼・テープの sha)も HEAD と同じ。manifest は 7 本とも既存の欄が全部同じで、足したのは TM9 の欄だけ。
- 試験: 新しい試験 46 本(約 10 秒)。全体は 4,010 passed・1 failed(作業木の junction による既知の 1 件)・1 xfailed(13 分 8 秒)。

## 1. 作ったもの

| 項 | ファイル | 中身 |
|---|---|---|
| 1 時間の定数 | `src/shibuya/core/time_consts.py`(新規・標準ライブラリだけ) | `NS_PER_SECOND`・`SECONDS_PER_MINUTE`・`MINUTES_PER_HOUR`・`HOURS_PER_DAY`・`SECONDS_PER_HOUR`(3,600)・`MINUTES_PER_DAY`(1,440)・`SECONDS_PER_DAY`(86,400)・`STEP_SECONDS`(60)・`STEPS_PER_HOUR`(60)・`STEPS_PER_DAY`(1,440)・`NS_PER_STEP`・`CLOCK_KIND`(`"steps"`)・`seconds_to_steps()`/`steps_to_seconds()`。派生する値は名の積で書いた(このファイル自身にも直書きの当たりは無い)。丸めの規則は **床**(その秒を含む刻み)。整数だけを受け、`float` と `bool` は落とす |
| 1 旧い名 | `src/shibuya/core/types.py` | `NS_PER_SECOND`・`SECONDS_PER_MINUTE` は `time_consts` の再輸出。`DEFAULT_TICK_SECONDS = STEP_SECONDS`・`MINUTES_PER_SIM_DAY = MINUTES_PER_DAY` は同じ値の別名にした。名と値は 1 つも変えていない |
| 2 `SimTime` | `src/shibuya/core/types.py` | `SimTime = int`(`t_sim_ns` と同じ意味のナノ秒の整数)を足し、`__all__` に入れた |
| 3 `TickCtx` | `src/shibuya/engine/systems/boxes.py`・`conductor.py` | 欄 `t_ns = T × 幅 × 1e9` と `tod_s = td × 幅` を足した。呼び口は `TickCtx.of(T, tpd, step_seconds=STEP_SECONDS)` で、1-0 の `of(T, tpd)` もそのまま使える。進行役は `cfg.tick_seconds` を渡す(1 か所)。`T`・`td`・`day` の値と意味は変えていない。系はまだ新しい欄を読まない |
| 6 乱数の鍵 | `src/shibuya/core/rng.py` | `time_key_from_t_ns(day_key0, t_ns, step_seconds)` を足した。`t_ns // (幅 × 1e9)` の刻みの番号を求め、`run_tick_key` と同じ値を返す。呼び手は変えていない。`run_tick_key` の `86_400` は `SECONDS_PER_DAY` に置き換えた |
| 7 TM9 | `src/shibuya/engine/run.py`・`systems/state_io.py`・`manifest_sections.py`・`systems/table.py` | §4 |

## 2. 直書きの置き換え

### 2-1. 数え方と件数

AST で数えた(`tests/engine/time/test_t0_literal_count.py`)。対象は発注の `1440`・`86400`・`// 60`・`* 60`・`/ 60`・`% 1440` に、同じ置き換えをした `3600` と `% 60`・`24` の演算を足した形。

- 数値のリテラル `1440`・`86400`・`3600`(`1_440`・`1440.0` など、書き方と int/float を問わない)
- 二項演算と累算代入の `//`・`*`・`/`・`%` で、どちらかの項が `60` か `24` のもの(`60.0` を含む)

| 形 | 前 | 後 |
|---|---:|---:|
| リテラル `1440`(`% 1440` を含む) | 84 | 0 |
| `* 60` | 67 | 0 |
| `// 60` | 51 | 0 |
| `/ 60` | 19 | 0 |
| `% 60` | 18 | 0 |
| `% 24` | 16 | 0 |
| `* 24` | 10 | 0 |
| リテラル `3600` | 9 | 0 |
| リテラル `86400` | 5 | 0 |
| `/ 24` | 2 | 0 |
| **計(式の位置で重複なし)** | **281** | **0** |

ファイル別(前 → 後はどれも 0): `build/sched/trial.py` 27・`build/sched/w17_schedule.py` 27・`build/field/w7_planspec.py` 18・`engine/processes/civic.py` 15・`engine/processes/goods_flow.py` 15・`engine/energy.py` 12・`build/sched/vocab.py` 11・`engine/presence.py` 10・`engine/processes/logistics.py` 10・`engine/relations.py` 10・`engine/processes/environment.py` 8・`build/field/w12_external_nodes.py` 7・`build/field/w13_weather.py` 7・`engine/systems/build.py` 7・`engine/solar.py` 6・`perception/renderer.py` 6・`engine/classical.py` 5・`engine/processes/salient.py` 5・`engine/run.py` 5・`engine/systems/body.py` 5・`build/vis/w9_shadow.py` 4・`engine/systems/decide.py` 4・3 か所のもの 6 本・2 か所のもの 12 本・1 か所のもの 15 本(計 55 ファイル)。段ごとでは build 111・engine 145・その他 25。

置き換えた名の内訳: `MINUTES_PER_HOUR` 125・`MINUTES_PER_DAY` 70(と `float(MINUTES_PER_DAY)` 1)・`HOURS_PER_DAY` 28・`SECONDS_PER_MINUTE` 23・`SECONDS_PER_HOUR` 9・`STEPS_PER_HOUR` 7・`STEPS_PER_DAY` 6・`SECONDS_PER_DAY` 5。残りの 7 か所はモジュールごとの重複した定義 `MINUTES_PER_DAY: Final[int] = 1_440` で、定義を消して `time_consts` から import した(`agents/weekly.py`・`build/sched/vocab.py`・`engine/activity.py`・`engine/processes/` の civic・goods_flow・logistics・opening)。名は残るので、読み手が `weekly.MINUTES_PER_DAY` などで引く形も前のまま動く。

### 2-2. 名の選び方(値はどれも同じ。違いは意味だけ)

- 暦の上の時間(分 → 時の `// 60`、時刻 `HH:MM` → 分の `* 60`、1 日の分 `% 1440` など)は `MINUTES_PER_*`・`SECONDS_PER_*`・`HOURS_PER_DAY` を使った。
- **刻みの数を時・日に直す所は `STEPS_PER_*` にした**(13 か所)。日の中の刻み `td // 60` で時を出す所(`systems/decide.py`・`systems/judge.py`)、通しの刻み `tick // 60`・`tick % 60` で正時を見る所(`presence.py` 3 か所・`cli.py`)、1 日の刻みの数の定数(`economy/ledger.py`・`engine/arbiter.py` の `_TICKS_PER_DAY`、`growth_decl.py`・`world/processes/actual_log.py` の `TICKS_PER_DAY`、`scheduler.py` の `HORIZON_TICKS`)、`world/state.py` の `tick % 1440`(営業時間の分と比べる)、`actual_log.py` の `ticks_per_day // 60` がこれにあたる。どれも 1 刻み=1 分を前提にしている。刻みの幅を変える段(T1 以降)では、ランの設定の幅から計算する形に直す候補になる。`grep STEPS_PER_` で拾える。
- `tick × tick_seconds // 60` のように秒から分を出す所は `SECONDS_PER_MINUTE` にした。`tick × minutes_per_tick % 1440`(分)は `MINUTES_PER_DAY` にした。
- 発見的な既定から手で直したのは 15 か所(作業用の道具 `apply_literals.py` の `OVR`)。

### 2-3. 型を変えない工夫

- `/ 60.0` のような真の割り算の項は、int の名に置き換えた(`x / 60` と `x / 60.0` は、Python の整数・浮動小数・NumPy の配列のどれでも同じ値と型になる)。
- 浮動小数の項との掛け算 `5.0 * 60.0` も int の名に置き換えた(片方が float なので結果は float)。
- それ以外で float の値が要る 1 か所(`relations.py` の `tw * 7.0 * 1440.0`)は `float(MINUTES_PER_DAY)` にした。
- `time_consts` の定数は全部 int にした(試験で確かめる)。

### 2-4. allow の表

`tests/engine/time/time_literal_allow.json` は **空(`{}`)**。281 か所はどれも時間の意味の数だった。「時間でない 60」「文字列の中」に当たる式は無かった。文字列の中は AST の数値リテラルではないので、もともと数えていない。表の行が当たりを失ったら試験が落ちるので、古い行は残らない。

### 2-5. 置き換えの前後で同じ値か(3 通り)

1. **AST の同値**(作業用の道具 `ast_equiv.py`): HEAD と作業木の各ファイルを AST に直して比べた。docstring は落とし、`time_consts` から import した名はその値に戻す。モジュールの重複定義は値と同じに扱い、真の割り算と浮動小数の掛け算の項は int と float を同一視する。変えた src 69 本のうち、**61 本は完全に同じ**だった。違う 8 本はどれも意図して足したもので、目で確かめた: `rng.py`(関数)・`types.py`(`SimTime`。これを外すと同じ)・`manifest_sections.py`・`run.py`・`state_io.py`・`table.py`(TM9)・`boxes.py`・`conductor.py`(`TickCtx`)。
2. **build の段の検算**(作業用の道具 `build_probe.py`): 資産は作り直していない。置き換えた 16 個の純粋な関数を、同じ入力で HEAD の写しと作業木の両方から呼んだ。出力の sha は両側とも `0acdba23590a7a42` で同じだった。対象は `common.hhmm_to_min`・`min_to_hhmm`・`w7_planspec` の 4 つ・`w14_signage._fmt_hm`・`pool_facts.parse_hhmm`・`trial` の 3 つ・`vocab.format_line`・`parse_line`・`w17_schedule._hm`・`w12_external_nodes._minute`・`w13_weather.sun_times`・`w9_shadow.sun_vector`。build の段のファイルは 1. でも全部同じだった。
3. **byte-check 19 構成**(§5)。

## 3. 「tick」の語

- **(a) 注釈と docstring**: `src/shibuya/core/` と `src/shibuya/engine/systems/` の 108 行を「刻み」に書き直し、0 行にした(「刻みの中」「刻みの頭」「刻みの数」など)。ハッシュの鍵・manifest の欄・識別子を名のまま書く所は、バッククォートで引用した(`tick_seconds`・`total_ticks`・`fire_tick` など)。試験 `test_t0_no_tick_word.py` が、引用の外に「tick」が無いことを見る。実行時の文字列(エラーの文・origin の欄)は変えていない。ほかの src には注釈と docstring の 707 行が残っている(段階的に直す・§7)。
- **(b) 識別子**: 名は 1 つも替えていない。〔決定 10-13b §3〕のとおり、残す名を allow の表 `tests/engine/time/tick_word_allow.json` に理由つきで載せた。**158 個**で、HEAD と同じ集合。T0 で足したコードは刻み系の名(`step_seconds`・`t_ns`・`tod_s`・`time_key_from_t_ns`)を使った。試験は、表の外の新しい名と、使われなくなった表の名の両方で落ちる。

| 理由 | 数 | 例 |
|---|---:|---|
| 状態台帳の鍵・道筋に入る名(ハッシュに入る)=変えない | 44 | `tick_ms_max`・`tick_seconds`・`ticks`・`_tickc`・`ev_tick`・`mem_tick` |
| manifest の欄=変えない | 1 | `budget_per_tick` |
| CLI・`cli.run`・`run_day` の引数(設定の指紋に入る)=変えない | 1 | `stop_at_tick` |
| テープの列=変えない | 2 | `observed_tick`・`recalled_first_tick` |
| 1-0 の箱の名・欄・系の宣言の名=段階的 | 8 | `TickCtx`・`TickScratch`・`total_ticks`・`awake_ticks` |
| 公開の名(関数・クラス・定数・属性・引数)=段階的 | 85 | `TICK_DTYPE`・`run_tick_key`・`DEFAULT_TICK_SECONDS`・`REFRACTORY_TICKS` |
| 局所の変数・private=段階的 | 17 | `_ticks_per_day`・`sticks` |

分け方は機械で決めた(作業用の道具 `tick_idents.py`)。理由の優先順は、状態台帳の道筋の形の文字列 → manifest → CLI・`run_day` の引数 → テープ → 箱と宣言 → 局所・公開。1 つの名が複数に当たるときは最初の理由を書いた(`tick_seconds` は CLI の引数でもある)。

## 4. TM9 の欄(10f と一体)

| 欄 | manifest(末尾に追加) | 日次の記録(`daily` の各行) | 節(10f の表) |
|---|---|---|---|
| `calls_by_model` | `{"judge_model": 0, "llm": llm_calls_total と同じ}` | その日の分。`RunResult.llm_calls` のこの記録までの増え=このランの中で数えた分 | 観測 |
| `clock_kind` | `"steps"`(`time_consts.CLOCK_KIND`) | 同じ | 設定 |
| `step_seconds` | `tick_seconds` と同じ値(60) | 同じ | 設定 |
| `bridges_count` | `null`(つなぎの台帳は 1-4 で入る。口の約束 1-4 の manifest の欄と同じ名) | 同じ | 設定 |

- final と behavior-hash は manifest を読まない(状態のハッシュは状態台帳の道筋だけ)ので、欄は manifest に置いた。確かめ方は 3 つある。byte-check の final・behavior・full が同じこと。試験で `CLOCK_KIND` を書き換えても final と呼数が同じこと。manifest の比べで既存の欄が全部同じこと(§5)。
- 日次の記録は状態のファイルにも入らない(再開のランでは空から始まる)。再開したランの最初の日は、再開した時刻からの分を数える。試験で、止めたランの残りと再開したランの分の和が、通しの 2 日目と同じことを確かめた。
- 足したことで変わった既存のもの: `manifest_sections`(10f の欄の表)に TM9 の 4 行が増えた。これは欄を足せば必ず増える表なので、既存の欄の値ではないとみなした。設定の節の golden `CONFIG_PATHS_SHA256`(`tests/engine/test_env_and_sections_10f.py`)を `58bb3124…` から `d16f26e6…` に更新し、同じ試験の「末尾に足した欄」の表に `T0_KEYS` を足した(凍結の表の増えた欄だけ)。系 `day_close`・`close_final` の読みの宣言には `cfg.tick_seconds` を足した(日次の記録の幅を読むため。1-0 の試験 D③ が読みの宣言の漏れを見つけた)。
- manifest の一番上の鍵(108 個・順も)は `tests/engine/time/manifest_keys_frozen.json` に凍結した。`writes_soa_frozen.json` と同じ形の凍結。

## 5. 結果不変の確かめ

| 確かめ | 範囲 | 結果 |
|---|---|---|
| byte-check([byte_check_t0.json](byte_check_t0.json)) | `byte_check_10e.py`・19 構成・5,000 体・seed 1・1 日・テープつき。HEAD の側は本体の src(`3e0ff73`)、T0 の側は作業木の src(`src_is_worktree` 真) | **19/19 構成で 25 欄とも同じ**(final・呼数・blocks・calls の列の sha・行動の件数・起床の内訳・behavior/full の最後・締めの後の 2 本・暦・frozen_sources ほか) |
| A/A の対照 | HEAD の写し(`git archive`)と本体の src | 19/19 で 25 欄とも同じ(比べ方が空回りしていない・ランは再現する) |
| 2 日のラン | `two_day_check_act.py one`・5,000 体・seed 1・既定 v3・テープつき・HEAD と T0 | 全欄が同じ。final `912446bd2b42b6ab`・140,913 呼・calls `cb330e76b4b8a573`・blocks `7f09f3dc78d84ac4`(1-0 と 10e の記録の値と同じ) |
| manifest([manifest_check_t0.json](manifest_check_t0.json)) | 10f の `manifest_check_10f.py side` の 7 本(既定 v3 の seed 1・2・帰無腕・記憶+関係・古典+記憶+関係)。両側 `PYTHONHASHSEED=0`。平坦にした全欄を比べ、壁時計は除いた | 7/7 で final が同じ。既存の欄 1,695〜2,211 個がどれも同じ。足したのは 14 葉(一番上の TM9 5 葉・daily の行 5 葉・節の表 4 行)だけで、順は既存の後に TM9。違う環境の欄は git の commit と汚れ、env_id だけ |
| 再開 | 既存の試験 `test_resume_10d.py`(全部)と TM9 の再開の試験 | 通った(§6) |
| 系ごとの境目の宣言 | `tests/engine/systems`(書きの宣言・読みの宣言・凍結の表 `writes_soa_frozen.json` は変更なし) | 通った |

## 6. 試験

新しい試験 `tests/engine/time/`(46 本・合成の世界だけで data は要らない・約 10 秒):

- `test_t0_time_consts.py`: 定数の値と関係、旧い名との同値、再輸出の名、換算の丸めと型の検査、doctest、標準ライブラリだけを import すること。
- `test_t0_literal_count.py`: allow の外は 0、表の古い行が無いこと、負の対照(仮のファイルの 11 行を形ごとに見つけ、文字列・演算でない 60・足し算は数えない)、`time_consts` 自身に当たりが無いこと。
- `test_t0_tickctx_equivalence.py`: 2 日の全刻みで `tod_s == td*60`・`t_ns == T*60e9`・`day == T//1440`・`t_sim_ns(T) == t_ns`。ほかの幅でも関係が成り立つこと。進行役がランの幅を渡すこと(合成の世界の 30 刻み)。
- `test_t0_rng_key.py`: 2 日の全刻みと 3 つの日の鍵で `time_key_from_t_ns == run_tick_key`。刻みの中の時刻、ほかの幅、src に呼び手が無いこと。
- `test_t0_no_tick_word.py`: (a) と (b)。負の対照(識別子 6 種、注釈と docstring の引用の内外)も入れた。
- `test_t0_tm9_fields.py`: manifest の鍵の凍結、TM9 の値と節、日次の和=総数=診断の行の `calls` の日ごとの和、再開、TM9 の値が final に入らないこと。

既存の試験(1-1 に関わるもの): `tests/engine/systems`・`test_env_and_sections_10f.py`・`test_sim_time_T.py`・`test_calendar*.py`・`test_resume_10d.py`・`test_10a_review_fixes.py`・`test_clock.py`・`test_state_ledger_10b.py` と新しい試験を 4 並列でまとめて回し、383 passed・1 件は並列の子プロセスが落ちた(`test_resume_10d.py::test_world_resume_equals_straight_at_every_tick[750]`・worker crashed)。同じ試験を 1 本で回し直すと 5 passed(98 秒)。

### 6-1. 全体の試験

`-m "not gpu and not slow" -n 4 --dist loadfile`(data あり・作業木): **4,010 passed・1 failed・1 xfailed(13 分 8 秒)**。落ちた 1 件は `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report` で、テープの道筋が `data/tape/` で始まらないという内容。作業木の `data` が本体への junction であることで起きる既知の落ちで、[1-0 の記録](../run-day-decomp/impl-1-0.md) §1・§7-4 と同じ(本体では通る)。上の並列の子プロセスの落ちは、全体のランでは起きなかった。`lint-imports` は 5 契約とも守られている(183 ファイル)。秘密の走査(`tools/scan_secrets.py`・変えたファイルと新しいファイル)は CLEAN。

## 7. 限界・空欄・仮採用・親に確かめてほしい点

- **仮採用(10-13b §0-3)**。既存の決定と原文から答えが出なかったので親の推奨に近い案で進め、戻せる形にした。どれも記録の欄と名だけで、結果は動かない。
  1. TM9 の欄の名と形: `calls_by_model = {"judge_model", "llm"}`・`clock_kind = "steps"`・`step_seconds`・`bridges_count`(1-4 の口の約束と同じ名)。
  2. manifest の置き場は末尾(10f と 10e の「列追加のみ」の慣行)。そのため `test_env_and_sections_10f.py` の凍結の 2 つを更新した。編集してよい範囲の「凍結の表(増えた欄だけ)」と読んだ。
  3. 直書きの範囲に `3600`・`% 60`・`24` の演算を足した(発注は「など」)。定数の名は `MINUTES_PER_DAY`・`STEPS_PER_HOUR` を足した(発注の一覧に無い 2 つ)。
  4. 判断モデルの呼び出し数は 0 にした。古典の方策(`classical`)の決定は判断モデルの呼び出しに数えていない。
- **刻みの幅を前提にした 13 か所**(§2-2・`STEPS_PER_*`)。T0 では値を変えないので名を分けただけ。T1 で幅を設定から読む形に直す候補になる。
- 時間の直書きで、試験の対象の外に残るもの: 演算の項でない `60`(関数の既定の引数 `tick_seconds: int = 60` など。`seconds… = 60` の形で 36 行)、`range(24)`・`minlength=24`、時刻の分のリテラル(`1_410`・`900`・`540` など)。T0 の門(値の同値と定数の集約)の外として残した。
- 「tick」の語は、`core/`・`engine/systems/` の外の注釈と docstring に 707 行残る。識別子 158 個も替えていない(段階的)。
- 作業用の置き場 `_bc/`(作業木の直下)は `.gitignore` に無い。**親が消してほしい**(テープ・side の JSON・試験のログ。commit に入れない)。
- 作業用の道具(`sites.py`・`apply_literals.py`・`ast_equiv.py`・`tickscan.py`・`tick_rewrite.py`・`tick_idents.py`・`build_probe.py`・`manifest_check_t0.py`)は、このセッションの scratchpad の `333/t0/` に置いた(リポには入れていない)。

## 8. 親の検収(第334・2026-10-14)

- 親の byte-check 4 構成(本体 HEAD の src vs 作業木の src・w6_v3_default/w6_v3_activity_off/w6_v1_default/v3_mem_rel): final が同じ 4/4・動いた欄 0(parent_head_vs_t0_4cfg.json)。
- 親が作業木で tests/engine/time を実行: 46 passed(9.7 秒)。実装役の全体試験(4,010 passed・落ち 1 件は junction 由来の既知)と記録 §2-5 の同値の確かめ(AST・build の 16 関数の sha・byte-check 19/19)を読んだ。
- 独立検収(review.md)の判定は §9。L1 の直しの後、親が作業木で tests/engine/time・build_lang・build_field・build_sched を再実行: 585 passed・1 xfailed(4 並列・93 秒)・lint-imports 5 kept。

## 9. 独立検収(review.md)と親の直し(第334・2026-10-14)

- **判定: 条件つき受入**(検収役は実装を見ていない。byte-check 4 構成=25 欄とも同じ・AST の独自の比較 60/69 同一+意図した追加 9・演算子と型の不変 38 か所・build の関数の sha 一致・直書き 281 → 0・時刻の欄の同値 30 日+乱数 20,000 点・指定の試験 262 passed)。
- **M1(中・仮採用=10-13b §0-3・PENDING §1-1b)**: 約束 (3)「tick の語を識別子から消す」は口の約束の〔決定〕のとおり**段階的**にし、T0 では識別子を 1 つも改名せず 158 名を理由つきで凍結(ハッシュに入る 48 名は変えない・110 名は後の段で別名に=箱と宣言の 8 名は T1・公開の 85 名と局所の 17 名は触る段で)。注釈と docstring は `core/`・`engine/systems/` だけ直し、707 行が残る。凍結の試験は「増えたら落ちる」だけなので、既存の名が新しいファイルに広がるのは捕まえない(L5)=各段の検収で見る。
- **L1(低・親が直した)**: 数え方の外にあった時間の直書き 4 か所を置き換えた(`w14_signage.py` の `divmod(m, 60)` → `MINUTES_PER_HOUR`・`w12_external_nodes.py` の `Fraction(60)` → `MINUTES_PER_HOUR`・`pool_facts.py` の `min(1439, …)` ×2 → `MINUTES_PER_DAY - 1`・`w7_planspec.py` の `SPAN_MIN = 2880` → `2 * MINUTES_PER_DAY`)。値は同じ(build は資産を作り直さない=次の版上げで)。数え方(`test_t0_literal_count.py`)は `divmod`・`1439`・`2880` を数えない=限界として残す。
- **L2(低)**: §2-2 の「T1 は `grep STEPS_PER_` で見つかる」は言い過ぎ。刻みの幅を前提にした所は他にもある(`engine/presence.py` の `tick % MINUTES_PER_DAY` ・既定の引数 `tick_seconds: int = 60` 29 か所など)。T1 の発注で「幅を設定から読む」対象を AST で洗い出す。
- **L3(低)**: 口の約束の `TICK_SECONDS` はコードでは `STEP_SECONDS`(「tick」の語を新しい名に入れないため)。`DEFAULT_TICK_SECONDS` は同じ値の別名で残る。`SimTime` は型の別名を足しただけで注釈にはまだ使っていない(1-3 の `Event.t_ns` から使う)。
- **L4(低・親が直した)**: 同値の道具 3 本を `t0/tools/` に置いた(絶対パスなし)。
- **L6(低)**: `seconds_to_steps` が bool を受ける・`time_key_from_t_ns` が幅を `int()` で切り捨てる(どちらも呼び手なし)=T1 で型の検査を足す。
- 親の検収: §8 のとおり(byte-check 4 構成 同じ・`tests/engine/time` 46 passed)。直した後の試験は親が作業木で再実行(§8 に追記)。
