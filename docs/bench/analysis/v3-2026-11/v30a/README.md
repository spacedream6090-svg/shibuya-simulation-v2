# v3-0a 乱数の鍵・ハッシュ・呼びの id の材料を世界の時刻から作る書き方へ — 段 1 の棚卸しと見積り(段 1 で止めた)

> **注(11-04)**: 指示書 11-04 §2-1(`docs/design/prompt-2026-11-04-reply4.md`)の**案 A**(§1-1 の「届く」18 か所だけ・
> 署名の変更 0〜1 本・1 バイト不変・切替口なし)で、段 2(書き換え)と段 3(試験・byte-check・性能)を行った。土台は
> HEAD 2160272。結果は §2〜§6。§1 は段 1 の棚卸しのまま(行番号は HEAD 33193c3 の値。2160272 でも 18 か所は同じ行だった)。
> §1-2(約 27 か所)と §1-3 は触っていない(v3-0b で行う)。

- 根拠: 指示書 11-03 §5(`docs/design/prompt-2026-11-03-reply3.md`)・独立の読み §2-2・§2-3・§3-2・§3-3
  (`docs/reference/v3-core-independent-review-2026-11-02.md`)。
- 作業木 `stage/v30a`(HEAD 33193c3)。**src/・tests/ は変えていない**(この README だけ新しく足した)。
- 結論: **範囲が目安(書き換え 30 か所以下・公開の関数の署名の変更 10 本以下)を超えた**ので、指示どおり書き換えに入らず
  §1 の表と見積りだけを残して止めた。書き換えの候補は**約 45 か所**、署名の変更は**約 20〜25 本**(数え方は §1-4)。
- 段 2・段 3(試験・byte-check・性能)は行っていない。§2〜§5 は空欄。

## §1 棚卸し

grep の型: `run_tick_key`・`wake_tiebreak`・`apply_key`・`priority_key`・`wander_key`・`relation_invite_key`・`stream(`・
`philox(`・`philox_array(`・`blake3`・`xxh64`・`step_key`・`call_id`・`f"{tick}`・`f"{step}`・`f"{int(step)}`・
`gate_stage1(`・`draw_index(`・`TIME_BUCKET_TICKS`。行番号はすべて HEAD 33193c3。独立の読みが挙げた所はすべて HEAD で
同じ行にあった(`llm/mock.py:172` は実際の `stream(` が `:179`・`:194` の 2 本。独立の読みが挙げていない `:227`・`:243` の
2 本もある)。

「届き方」の列:
- **届く**=その関数の中で `t_ns`(`ctx.t_ns`・`DecisionCtx.t_ns`・引数 `t_ns`)と刻みの幅が両方使える。署名を変えずに書き換えられる。
- **通す N**=`t_ns` が届いていない。最も近い `TickCtx`/`t_ns` からその所まで、N 本の関数(か dataclass の欄)の署名に
  引数を足す必要がある。
- **蓄えた値**=材料が「今の刻み」ではなく、状態やテープに蓄えた刻みの番号(`t_apply`・`res.tick`・テープの `tick` 列)。
  `t_ns` から作り直す相手が無い。値をナノ秒で蓄える段(v3-0b=結果が動く)まで書き換えられない。
- **読む側**=呼びの id を文字列から読み戻すだけ(材料を作らない)。宣言つきの例外の候補。

### 1-1 届く(署名を変えずに書き換えられる)= 18 か所

| # | 所 | 材料 | 届き方 |
|---:|---|---|---|
| 1 | `engine/systems/decide.py:181` | 呼びの id `f"{tick}:{a}:{cls}"`(艦隊の道) | `ctx.t_ns`・`b.cfg.tick_seconds` |
| 2 | `engine/systems/decide.py:185` | 時間帯 `tick // TIME_BUCKET_TICKS` | 同上 |
| 3 | `engine/decision/port.py:313`(`:317` が使う) | `step_key(ctx.step)` → `run_tick_key` | `DecisionCtx.t_ns`(`:211`)・`self.step_seconds`。`core/rng.py:130` の `time_key_from_t_ns` がそのまま使える |
| 4 | `engine/decision/layer.py:308` | 呼びの id `f"{int(step)}:{agent}:{cls}"` | `decide_one` は `t_ns` を受ける(`decide.py:122`) |
| 5〜6 | `engine/contact/port.py:225`・`:235` | `step_key(ctx.step)` | `DecisionCtx.t_ns`・`ContactPort` は `DecisionPort` を継ぐ |
| 7〜8 | `engine/calendar2/port.py:185`・`:195` | 同上 | 同上(腕だけ) |
| 9〜10 | `engine/calendar3/port.py:154`・`:164` | 同上 | 同上(腕だけ) |
| 11〜12 | `engine/duties/port.py:147`・`:157` | 同上 | 同上(腕だけ) |
| 13 | `engine/contact/layer.py:506` | `habit_recheck_u(seed, port.step_key(T), …)` | `_habit_or_decide(T, t_ns, …)` の引数 |
| 14 | `engine/contact/layer.py:446` | `call_id_of(T, a, serial)` | `_decide(T, t_ns, …)` の引数・`self.step_seconds` |
| 15 | `engine/contact/layer.py:517` | 同上 | `_habit_or_decide` の引数 |
| 16 | `engine/calendar2/layer.py:270` | 同上 | `_decide(T, t_ns, …)`。幅の持ち方は【未確認】 |
| 17 | `engine/calendar3/layer.py:280` | 同上 | 同上 |
| 18 | `engine/duties/layer.py:289` | 同上 | 同上 |

### 1-2 通す(t_ns が届いていない)= 約 27 か所

| # | 所 | 材料 | 通す道(足す署名) |
|---:|---|---|---|
| 19 | `engine/llm_bridge.py:792` | 呼びの id `f"{int(step)}:{agent}:{cls}"`(mock・再生の道) | `LLMBridge.call`・`LLMBridge.begin`・`CallStart` の欄・`_after_render`(公開 2 本+dataclass 1+内 1) |
| 20 | `engine/llm_bridge.py:808-809` | 再生の鍵 `lookup_row(agent, step, cls, prompt_hash)` | 19 と同じ道。ただしテープの `tick` 列と対で読むので **蓄えた値**の側面もある |
| 21 | `engine/arbiter.py:439` | 起床の同順 `wake_tiebreak_array(run_salt, tick, …)`(**既定のランの同順**) | `arbitrate(…, tick, …)` ← `Arbiter.step`(`:575`)← 系(公開 2 本) |
| 22 | `engine/commit.py:447` | 資源の優先 `priority_key_array(run_salt, tick, …)` | `arbitrate_resources(…, tick, …)` ← `engine/systems/act.py:74`(公開 1 本) |
| 23 | `engine/commit.py:887` | 被招待の起床の同順 `wake_tiebreak_array(run_salt, tick, …)` | `intents_from_responses(…, tick, …)` ← `engine/systems/judge.py:168`(公開 1 本) |
| 24 | `engine/classical.py:630` | `stream(seed, "policy.classical", tick, aid, cond)` | `request.tick`(`LLMRequest`)。`LLMRequest` に `t_ns` の欄+古典の方策に幅(dataclass 1+構築 1) |
| 25〜28 | `llm/mock.py:179`・`:194`・`:227`・`:243` | `stream(master_seed, 領域, request.tick, agent, 級)` | 24 と同じ `LLMRequest` の欄+`MockLLM` に幅(層契約: llm 層が刻みの幅を持つ) |
| 29 | `engine/chooser.py:269` | `stream(seed, "engine.chooser", tick, agent)` | `draw_index(p, seed, tick, agent)`(公開 1 本)← 30〜32 |
| 30〜31 | `engine/poi_target.py:518`・`:647` | `draw_index(…, tick, …)` | `PoiTarget.resolve`(`:373`)・`_pick`(`:631`)(公開 1 本+内 1) |
| 32 | `engine/store_choice.py:182` | `draw_index(…, tick, …)` | `recall(agents, aid, tick, …)`(公開 1 本) |
| 33 | `engine/conversation.py:386` | `stream(master_seed, "conversation.invite", tick, inviter)` | `_accepts` ← `invite`(`:390`)(公開 1 本+内 1) |
| 34 | `perception/p_notice.py:477` | `stream(seed, "perception.p_notice", *k19_counters(event_id, tick))` | `notice_event(*, …, tick)` ← `engine/processes/salient.py:256`(公開 1 本) |
| 35 | `engine/processes/salient.py:335` | `run_tick_key(day_index, tick, 幅)` | `_collapse_events(tick)` ← `step(self, tick)`=**世界過程の共通の口**(`engine/processes` に `def step(self, tick: int)` が 19 本) |
| 36 | `engine/processes/civic.py:194` | `run_tick_key(day_index, tick, 幅)` | `_counter_stream(tick, cell)` ← `step(self, tick)`(civic だけで 5 本。35 と同じ共通の口) |
| 37 | `engine/proximity.py:262`(`:345` が使う) | `time_key(T)` → `run_tick_key` | `time_key` ← `notice_u(T, …)` ← `noticed(…, T, …)`・`engine/relations.py:1175`(公開 2〜3 本) |
| 38 | `engine/activity.py:419` | `wander_key_array(salt, tick, …)` | `wander_destinations(…, tick)` ← `wander_intents`(`:430`)・`engine/systems/judge.py:141`(公開 2 本) |
| 39 | `engine/relations.py:946` | `relation_invite_key_array(salt, tick, …)` | `choose_talk_partners(agents, tick, …)` ← `engine/commit.py:911`・`engine/systems/build.py:1237`(公開 1 本) |
| 40 | `engine/relations.py:983` | 同上 | `pick_rest(tick, …)` ← `engine/systems/build.py:1236`(公開 1 本) |
| 41 | `engine/familiarity.py:305` | `gate_stage1(…, domain_counters=(t, 体, POI))` | `_signage_on_entry(t, …)` ← `after_tick(agents, tick, …)`(`:224`)(公開 1 本+内 1) |
| 42 | `perception/renderer.py:1972` | `gate_stage1(…, domain_counters=(tick, 体, POI))` | `_signage_seen(…, tick)` ← `perceive_call(step)`(`:1479`)・`render(tick=…)`(公開 2 本。描画の口は試験とスタブの描き手も実装する) |
| 43 | `engine/calendar_self.py:902` | 呼びの id `f"{_DECIDE_STEP_KEY}-set:{T0}:{a}"` | `_set_reminders(ids, T0)`(`:878`)(内 1。呼び手の届き方は【未確認】) |
| 44 | `engine/calendar_self.py:1414` | 呼びの id `f"{_DECIDE_STEP_KEY}:{T}:{a}:{trip}"` | `_opportunities(T, started)`(`:1366`)(内 1。同上) |
| 45 | `llm/undefined.py:789` | 呼びの id `f"adjudicate:{word}:{tick}"` | `adjudicate(word, tick)`(`:771`)(公開 1 本) |
| 46 | `engine/scheduler.py:133` | `wake_tiebreak_array(state.run_salt, state.tick, …)` | `TickState` に `t_ns` が無い(dataclass 1)。**既定のランでは呼ばれない**(独立の読み §1-2) |

### 1-3 蓄えた値・読む側(書き換えの外=宣言つきの例外の候補)

| 所 | 材料 | 区分 | 理由 |
|---|---|---|---|
| `engine/systems/judge.py:102` | 返事の適用の順 `apply_key_array(salt, t_apply, ag)` | 蓄えた値 | `t_apply` は保留の組(状態)に蓄えた刻みの番号。`ctx.t_ns` から作る相手ではない。ナノ秒で蓄えるのは v3-0b(独立の読み §3-2 の「返事の適用の順の鍵をナノ秒にする=動く」) |
| `engine/run.py:1971` | `_call_ref(res)` が `res.tick` から呼びの id を作り直す | 蓄えた値 | `res.tick` は発射の刻み(結果の欄・再生の到着待ちに入る)。`res` が `call_id` を運べば読むだけになるが、`BridgeResult`・艦隊の結果・再生の行の欄を足す(+dataclass 2〜3) |
| `engine/tape.py:148`・`:159`・`:312-314`・`:602`・`:643` | テープの列 `tick`・`observed_tick`・再生の鍵 | 蓄えた値 | 指示で「テープの列名と値は変えない」 |
| `engine/events/log.py:309`・`:332-341`・`:506-509` | 原因の列が呼びの id を `"{T}:{体}:{級}"` と読み戻す | 読む側 | 材料を作らない |
| `engine/contact/port.py:182`・`:196`・`calendar2/port.py:157`・`calendar3/port.py:126`・`duties/port.py:119` | `parse_call_id`・`step_of_call_id` | 読む側 | 同上 |
| `engine/contact/port.py:175`・`calendar2/port.py:150`・`calendar3/port.py:119`・`duties/port.py:112` | `call_id_of(step, agent, serial)` | 形の定義 | 呼び手(#14〜18)が渡す整数を替えれば足りる。関数は変えない |
| `llm/fleet.py:267-280` | 復号の seed・振り分け `xxh64(call_id, …)` | 読む側 | 呼びの id を経由するだけ(#1 が替われば一緒に替わる) |
| `engine/speech_clock.py:236` | `k19_counters(speaker, t_ns, session+1)` | 既に t_ns | 参考(書き換え不要) |

### 1-4 見積り

| 区分 | か所 | 公開の関数・dataclass の署名の変更 |
|---|---:|---:|
| 1-1 届く | 18 | 0(`DecisionPort` に `t_ns` 版の鍵のメソッドを 1 本足す案=新規 1) |
| 1-2 通す | 約 27 | 約 20〜25(下の内訳) |
| 1-3 例外 | 13 前後 | 0 |
| 計(書き換え) | **約 45** | **約 20〜25** |

1-2 の署名の内訳(重なりを除いた概数): `LLMBridge.call`・`LLMBridge.begin`・`CallStart`・`LLMRequest`(t_ns の欄)・`MockLLM`/古典の方策の幅・
`arbitrate`・`Arbiter.step`・`arbitrate_resources`・`intents_from_responses`・`draw_index`・`PoiTarget.resolve`・`StoreChoice.recall`・
`Conversation.invite`・`notice_event`・世界過程の `step(self, tick)`(共通の口=19 本の実装)・`Proximity.noticed`/`notice_u`・
`wander_destinations`/`wander_intents`・`choose_talk_partners`・`pick_rest`・`Familiarity.after_tick`・描画の `render`/`perceive_call`・
`UndefinedAction.adjudicate`・`TickState`。どれも既定値つきの引数で後方互換にはできるが、目安の 10 本を倍以上超える。

目安を超えた主な原因【推測】:
1. 乱数を引く所の多くが、系の関数(`TickCtx` を受ける)から 2〜3 段下の層の関数・メソッドで、刻みの番号の整数だけを受けている
   (`T0` で `TickCtx` に `t_ns` を足したが、系より下へはまだ通していない=`boxes.py:76`「T0 では系はまだ読まない」)。
2. 世界過程の口 `step(self, tick)` が 19 本の実装の共通の形で、1 本を替えると全部の口の形が揃わなくなる。
3. mock と古典の方策は `LLMRequest.tick`(テープの列と同じ値)を乱数の鍵に使う。`t_ns` を運ぶには llm 層の契約の dataclass に
   欄を足し、llm 層が刻みの幅を知る必要がある(層契約に触る)。

### 1-5 範囲を狭める案(親の判断用・どれも未着手)

- **案 A(1-1 の 18 か所だけ)**: 署名の変更 0〜1 本。既定のランで効くのは #1・#2(艦隊の道の呼びの id と時間帯=mock の byte-check では
  艦隊の道を通らない【推測】)と #3(判断の口 port の腕)。腕の判断の口(contact・calendar2・calendar3・duties)は 19 構成に入っているかを
  byte-check の構成表(`docs/bench/analysis/wave2-2026-09-30/wave2_bytecheck.py:54-64`・`w6_regen_measure.py` の `ARMS`)で
  確かめる必要がある。
- **案 B(案 A+系の直下 1 段)**: #21〜23(アービタの同順・資源の優先・被招待の同順=どれも系から 1 段)と #19(橋の呼びの id)を足す。
  署名の変更は 5〜6 本。既定のランの同順の鍵(独立の読み §2-2 の要所)が入る。
- **案 C(全部)**: 約 45 か所・約 20〜25 本。世界過程の口を `step(self, ctx)` に揃える段を先に別に立てる【推測: その段だけで 19 本+系の
  呼び手の書き換え】。

## §2 足した関数と書き換えの一覧

### 2-1 足した関数(既存の署名の変更 0 本・公開の口を 2 本足した=`core.rng.key_time_from_t_ns` と `DecisionPort.time_key_at`)

| 関数 | 所 | 中身 |
|---|---|---|
| `key_time_from_t_ns(t_ns, step_seconds)` | `core/rng.py` | `t_ns // (幅 × 1e9)`(床)。刻みの頭の時刻を渡せば今までの刻みの番号と同じ整数。幅が正でなければ `ValueError`。v3-0b で材料の単位を替えるときはこの 1 本を替える |
| `DecisionPort.time_key_at(t_ns)` | `engine/decision/port.py` | `time_key_from_t_ns(day_key0, t_ns, step_seconds)`=刻みの頭の時刻なら `step_key(T)` と同じ値。**足した署名はこの 1 本** |
| `time_key_from_t_ns`(既存) | `core/rng.py` | 中で `key_time_from_t_ns` を通す形に直した(値と例外は前と同じ)。呼び手は `time_key_at` の 1 か所 |

`DecisionPort.step_key(step)` は残した(src からの呼び手は 0 本になった=試験が旧の値と比べるのに使う。消すかは v3-0b で判断)。

### 2-2 書き換えた 18 か所(行番号は作業木の今の行)

| # | 所 | 旧の材料 | 新の書き方 |
|---:|---|---|---|
| 1 | `engine/systems/decide.py:184`(艦隊の道) | 呼びの id `f"{tick}:{a}:{cls}"` | `key_t = key_time_from_t_ns(int(ctx.t_ns), tick_seconds)`(`:162`・刻みに 1 回)→ `f"{key_t}:{a}:{cls}"` |
| 2 | `engine/systems/decide.py:188` | 時間帯 `tick // TIME_BUCKET_TICKS` | `key_t // TIME_BUCKET_TICKS` |
| 3 | `engine/decision/port.py:322`(`choose`) | `present_rng(…, self.step_key(ctx.step), …)` | `self.time_key_at(ctx.t_ns)` |
| 4 | `engine/decision/layer.py:310` | 呼びの id `f"{int(step)}:…"` | `f"{key_time_from_t_ns(t_ns, self.port.step_seconds)}:…"` |
| 5〜6 | `engine/contact/port.py:225`・`:235` | `self.step_key(ctx.step)` | `self.time_key_at(ctx.t_ns)` |
| 7〜8 | `engine/calendar2/port.py:185`・`:195` | 同上 | 同上 |
| 9〜10 | `engine/calendar3/port.py:154`・`:164` | 同上 | 同上 |
| 11〜12 | `engine/duties/port.py:147`・`:157` | 同上 | 同上 |
| 13 | `engine/contact/layer.py:507` | `habit_recheck_u(seed, self.port.step_key(T), …)` | `self.port.time_key_at(t_ns)` |
| 14 | `engine/contact/layer.py:447` | `call_id_of(T, a, serial)` | `call_id_of(key_time_from_t_ns(t_ns, self.step_seconds), a, serial)` |
| 15 | `engine/contact/layer.py:518` | 同上 | 同上 |
| 16 | `engine/calendar2/layer.py:271` | 同上 | 同上 |
| 17 | `engine/calendar3/layer.py:281` | 同上 | 同上 |
| 18 | `engine/duties/layer.py:290` | 同上 | 同上 |

- 新しい識別子は `key_time_from_t_ns`・`time_key_at`・`key_t`(`open`・`tick` を含まない。`tick_seconds`・`TIME_BUCKET_TICKS` は既存の名)。
- `DecisionContext.step`・`LLMCall.tick`(テープの列)・`_issue(T, …)`(監査の控え)など、18 か所の外の刻みの番号は変えていない。
- 切替口なし。§1-2・§1-3 は触っていない。

### 2-3 前提の確かめ(段 1 で【未確認】だった点)

- **#16・#17 の幅の持ち方**: カレンダー 2・3 の層(と連絡・店の仕事の層)は組み立てから `step_seconds=int(tick_seconds)` を受けて
  `self.step_seconds`・`self.step_ns` に持つ(`engine/systems/build.py` の各層の組み立て)。判断の口も同じ幅(`_pkw`)。
- **`T` と `t_ns // 幅` が常に一致するか**: 系が受ける時刻は、進行役 `engine/systems/conductor.py` の `on_step` が
  `T = t_ns // step_ns` から `TickCtx.of(T, tpd, step_s)`(`t_ns = T × 幅 × 1e9`)で作る 1 か所だけ(`TickCtx.of` の呼び手は src に 1 つ)。
  T は通しの番号(日の鍵は `day_key0` の側)なので、日をまたいでも再開(`t_begin` から始める)でも同じ式。腕の層の `_decide`・
  `_habit_or_decide` は `run_step(ctx.T, ctx.t_ns, …)` から `T`・`t_ns` を書き換えずに受け渡す(ずらして渡す所は grep で 0。窓の境目の
  事象 `_on_due` は判断を呼ばない)。カレンダー 1b(`calendar_self.py`=18 か所の外だが #3 の `choose` を通る)は
  `t_ns = T × step_seconds × 1e9` を自分で作り、口と同じ幅。一致しない道は見つからなかった。§3 のランの試験で、日をまたいで止め・
  再開した後まで全部の入口で一致を確かめた。

## §3 試験

| 試験 | 中身 |
|---|---|
| `tests/engine/time/test_t0_rng_key.py::test_callers_are_the_plan_a_sites` | `test_no_caller_yet` を書き直した(親の確認済み)。`key_time_from_t_ns`・`time_key_from_t_ns`・`time_key_at` の src の呼び手が 18 か所の表と一致・`step_key` の src の呼び手は 0(足しても消しても落ちる) |
| `…::test_key_time_is_the_step_number` | 全刻み 2 日ぶん・幅 1/7/30/120/300 秒の境(日の頭・2 日目・3 日目)・刻みの中は床・負の時刻は床・幅 0 と負は `ValueError` |
| `tests/engine/time/test_v30a_key_sites.py`(新) | #3・#5〜#12: 判断の口の基底と腕の口 4 種の並べ替え・選びの乱数を、鍵を `step_key(ctx.step)` に戻した写しと比べて同じ(12 の刻み=0・1・日の頭の前後・TPD+300・2 日目の末・7 日目 × 体 × 通し番号 × 幅 60/30・日の鍵 0/20,000)。#1・#2・#4・#14〜#18: 呼びの id と時間帯が旧の形と同じ。#13・#15: 連絡の層の合成の台で、習慣の戻しの鍵が `step_key(T)`・習慣で答えた呼びの id が旧の形(習慣で答えた道を通ったことも確かめる)。ラン: (a) 連絡(習慣 on)+カレンダー 2・3+判断の口 port の合成のラン(日曜 → 月曜)と (b) 店の仕事の合成のランを、TPD+300 で止めて再開し、口と層のすべての入口で「t_ns から作った整数 == 刻みの番号」(違反 0)。(c) 偽の艦隊のラン(12 刻み)で、発射した呼びの id が `f"{T}:{体}:{級}"`・時間帯が `T // 5` |
| `tests/engine/duties/test_du_units.py::test_mock_port_is_uniform_deterministic_and_closed` | 直した: 文脈を `step=k, t_ns=0` で作っていた(エンジンが渡さない形=刻みの番号だけを変えて鍵を変えていた)。`t_ns=k × 60e9` に直した(試験の意図=刻みごとに選びが一様、は同じ) |

ラン (a)・(b) の入口ごとの確かめの数(違反 0):

| 入口 | (a) | (b) |
|---|---:|---:|
| `TickCtx.of`(止めたランと再開のランで 2 日の全刻み) | 2,880 | 2,880 |
| `DecisionLayer.decide_one`(#4)・`DecisionPort.choose`(#3) | 2,798・2,798 | — |
| `ContactLayer._decide`(#14)・`ContactPort.choose`(#5〜6) | 911・911 | — |
| `ContactLayer._habit_or_decide`(#13・#15) | 286 | — |
| `Calendar2Layer._decide`(#16)・`Calendar2Port.choose`(#7〜8) | 943・943 | — |
| `Calendar3Layer._decide`(#17)・`Calendar3Port.choose`(#9〜10) | 327・327 | — |
| `DutiesLayer._decide`(#18)・`DutiesPort.choose`(#11〜12) | — | 11・11 |

回した試験(作業木・`PYTHONPATH` は作業木の src):
- `tests/engine/time tests/engine/decision tests/engine/contact -n 6`: 249 件すべて通った(失敗 0)。
- 書き換えたファイルに関わる試験 `tests/engine/calendar2 tests/engine/calendar3 tests/engine/duties tests/engine/calendar tests/engine/test_fleet_wiring.py tests/llm/test_fleet.py -n 6`: 225 件のうち失敗 1(上の `test_du_units` の文脈)→ 直した後、そのファイルは全部通った。
- 全体試験は回していない(親が回す)。

## §4 byte-check

道具 `docs/bench/analysis/wallbounce-1012/10e/byte_check_10e.py`(5,000 体・seed 1・1 日・mock・テープつき・`--jobs 2`)。土台=本体の src
(HEAD 2160272・回す前と後に `git diff --quiet 2160272 -- src` で変わっていないことを確かめた・label `base_2160272`)、作業木=`--src`
に作業木の src(label `v30a`)。

**19 構成すべて 25 欄が同じ**(compare の `moved` が全構成で空):

| 構成 | 25 欄 | final | 呼数 |
|---|---|---|---:|
| w6_v3_default | 同じ | `c8d68704b7b0760d` | 60,939 |
| w6_v3_activity_off | 同じ | `ba35651c9a16bc7b` | 44,209 |
| w6_v1_default | 同じ | `7bed32bd4af97c2a` | 45,735 |
| w6_v1_derive_v2_1 | 同じ | `f46687d5aae54d30` | 40,325 |
| w6_v2 | 同じ | `6531a266225061cb` | 47,629 |
| w6_v1_edge | 同じ | `0e4b194512b22c9b` | 45,735 |
| w6_v2_edge | 同じ | `8cb2e2713ff7c1e5` | 47,629 |
| w6_v1_edge_plateau | 同じ | `0e4b194512b22c9b` | 45,735 |
| w6_old_v1_default | 同じ | `0a9bf5f060dcad48` | 45,735 |
| w6_old_v1_derive_v2_1 | 同じ | `b3236da240ced8d0` | 40,325 |
| w6_old_v2 | 同じ | `d328cbfde2e62a9a` | 47,629 |
| w6_old_v1_edge | 同じ | `b88739d611d970f2` | 45,735 |
| w6_old_v2_edge | 同じ | `722d68383f9ee63f` | 47,629 |
| w6_old_v1_edge_plateau | 同じ | `b88739d611d970f2` | 45,735 |
| w6_golden_null_arm | 同じ | `2875768fc19e02e8` | 95,645 |
| v3_mem_store | 同じ | `2df5703f853f18d4` | 60,939 |
| v3_mem_rel | 同じ | `477e22fcaed2590a` | 63,519 |
| v3_classical | 同じ | `5be0188ea16db82c` | 89,941 |
| v3_classical_mem_rel | 同じ | `ea3047ab705ac9e2` | 100,942 |

腕の判断の口が 19 構成のどれで通るか:

| 口(18 か所の #) | 19 構成で通るか | 理由 | 同値を示したもの |
|---|---|---|---|
| 艦隊の道(#1・#2) | どれも通らない | 19 構成は mock(艦隊を渡さない) | §3 ラン (c)・単位の試験 |
| 判断の口 port(#3・#4) | どれも通らない | 腕 `SHIBUYA_DECISION_PORT` の既定は `legacy`(19 構成は渡さない) | §3 の口の単位・ラン (a)・下の腕 on の byte-check |
| 連絡 c1(#5・#6・#13〜#15) | どれも通らない | 腕 `SHIBUYA_CONTACT` の既定は `off` | 同上 |
| カレンダー 2(#7・#8・#16) | どれも通らない | 腕 `SHIBUYA_CALENDAR_2` の既定は `off` | 同上 |
| カレンダー 3(#9・#10・#17) | どれも通らない | 腕 `SHIBUYA_CALENDAR_3` の既定は `off` | 同上 |
| 店の仕事(#11・#12・#18) | どれも通らない | 腕 `SHIBUYA_DUTIES` の既定は `off` | §3 の口の単位・ラン (b)・下の腕 on の byte-check |

=19 構成の一致は「18 か所を通らない道が 1 バイトも動かない」ことの確かめで、18 か所そのものの同値は §3 の試験と下の追加の
byte-check で示した。

追加の確かめ(腕 on・2 構成): 両側とも環境変数で `SHIBUYA_DECISION_PORT=port`・`SHIBUYA_CONTACT=c1`・`SHIBUYA_CONTACT_HABIT=on`・
`SHIBUYA_CALENDAR=1b`・`SHIBUYA_CALENDAR_2=arm`・`SHIBUYA_CALENDAR_3=arm`・`SHIBUYA_DUTIES=arm` を置いて `--only w6_v3_default,v3_classical`
(label `base_2160272_arms`・`v30a_arms`。7 変数は side の `env` 欄に出ている)。
〔検収の訂正〕本物の世界のランで通るのは 11 か所: w6_v3_default で `DecisionPort.choose` 84,514・`decide_one` 69,032・calendar2 11,923・contact の `_decide` 390・duties 79(v3_classical では contact 0)。**calendar3(#9・#10・#17)と習慣の道(#13・#15)は両構成とも 0 回**で、これらの同値は合成のランと単位の試験(§3)だけで示している。通った入口の新旧の不一致は 0(検収役のスパイ)。

| 構成(腕 on) | 25 欄 | final | 呼数 |
|---|---|---|---:|
| w6_v3_default | 同じ | `a1ef8fe8d4f5a257` | 69,032 |
| v3_classical | 同じ | `4f3ead084a92da21` | 87,393 |

- final と呼数が既定の構成(`c8d68704b7b0760d` / 60,939・`5be0188ea16db82c` / 89,941)と違う=腕が効いたランであることの確かめ。
  腕ごとの判断の数はこのランでは数えていない(数えたのは §3 の合成のラン)。

置き場: [bytecheck/](bytecheck/)(side 4 本・compare 2 本。絶対パスが無いことを grep で確かめた)。

## §5 性能(10-13b §0-7)

5,000 体 × 1 日・mock・seed 1・`w6_v3_default` と同じ引数(`cli.run(vocab_version="v3", activity=True)`・テープなし)。1 本ずつ単独で、
土台 → 作業木を 2 巡(ほかの重いランは止めた後)。壁時計=`cli.run` の前後・刻みあたり=壁時計 ÷ 1,440・最大メモリ=Windows の最大の
作業集合(`PeakWorkingSetSize`・10^6 B を MB)。判断モデルの呼数は 0(mock)。道具は作業用の置き場の使い捨ての写し(リポには入れていない)。

| 版 | 壁時計[秒] 1 巡/2 巡 | 刻みあたり[ms] | 最大メモリ[MB] | 呼数(LLM) | final |
|---|---|---|---|---:|---|
| 土台(`2160272`) | 60.3 / 56.2 | 41.9 / 39.0 | 533.8 / 528.6 | 60,939 | `c8d68704b7b0760d` |
| 作業木(v3-0a 案 A) | 60.3 / 55.1 | 41.9 / 38.2 | 528.3 / 531.3 | 60,939 | `c8d68704b7b0760d` |

- 同じ巡の土台と比べ壁時計 0.0 / −1.1 秒・最大メモリ −5.5 / +2.7 MB=揺れの中。悪化は見えない。
- この測りの前の 1 回(最大メモリの読み取りの不具合で 0 と出た回)の壁時計は土台 56.5/56.7 秒・作業木 55.4/60.9 秒(巡の間の揺れが
  ±3 秒ある)。
- 既定のランは 18 か所のどれも通らない(艦隊の道も腕の口も通らない)ので、仕事の量は変わらない。

## §6 できなかったこと・【推測】

- 艦隊の道(#1・#2)の日をまたぐ境・再開の後は、偽の艦隊のランで回していない(偽の艦隊のランは 12 刻み)。代わりに、系が受ける
  `ctx` がすべて `TickCtx.of` の 1 か所から来ることと、ラン (a)・(b) で止めて再開した後まで `TickCtx.of` の全刻み(2,880)で一致する
  ことを確かめた(#1・#2 は `ctx.T` と `ctx.t_ns` だけを読む)。
- `DecisionPort.step_key` は src の呼び手が 0 になったが残した(消すと公開の署名の削除=v3-0b で判断)。
- カレンダー 1b(`calendar_self.py`)の呼びの id(§1-2 の #43・#44)は触っていない。#3 の `choose` を通るので、腕 on の byte-check
  (1b を含む)で結果が同じことを確かめた。
- 段 1 の §6 の残り(#20 の区分・「既定のランで効く所」)は v3-0b の段の話で、本段では扱っていない。
- 〔検収で見つかった棚卸しの漏れ〕`engine/decision/ports.py:92` の `MockPort.pick` は `self.mock.action_draw(ctx.agent_id, ctx.step, …)` で刻みの番号を乱数の材料にしている。描画の道(`llm/mock.py`=#25〜28)と揃える必要があるので案 A の外に置き、v3-0b の表に足す。

## §7 検収と親の確かめ(第344)

- 別の検収役(Opus 5.5・実装を見ていない): **条件つき受入**=コードの欠陥なし。中 1(§4 の「16 か所」→ 11 か所)・低 4(`SWITCH_ENV` の注の誤り・署名の数え方・`MockPort.pick` の棚卸しの漏れ・同義反復に近い試験 1 本)。中 1 と低 2 件は本書と compare の `note` を親が直した。`MockPort.pick` は v3-0b へ。試験 1 本は害なしとして残す。検収役の試験 474 passed・0 failed。
- 親の byte-check(本体の src vs 作業木の src・5,000 体・seed 1・1 日・mock): 4 構成(w6_v3_default・v3_mem_store・v3_classical・v3_classical_mem_rel)は 25/25 同じ(final `c8d68704b7b0760d`・`2df5703f853f18d4`・`5be0188ea16db82c`・`ea3047ab705ac9e2`)。腕 on(上の 7 変数)の w6_v3_default も 25/25 同じ(final `a1ef8fe8d4f5a257`・呼数 69,032)。
