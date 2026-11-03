# v3-0a 乱数の鍵・ハッシュ・呼びの id の材料を世界の時刻から作る書き方へ — 段 1 の棚卸しと見積り(段 1 で止めた)

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

空欄(段 1 で止めた)。

## §3 試験

空欄。既存の試験も回していない(src を変えていないため)。

## §4 byte-check

空欄。

## §5 性能

空欄。

## §6 できなかったこと・【推測】

- 段 2・段 3 は行っていない(範囲が目安を超えたため=指示書 11-03 §5・発注の段 1-3)。
- #16・#17 の calendar2・calendar3 の層の刻みの幅の持ち方、#43・#44 の呼び手の `t_ns` の届き方は確かめていない(【未確認】)。
- #20 の再生の鍵を「通す」に入れるか「蓄えた値」に入れるかは親の判断(テープの列は変えない規則と、再生の鍵が今の刻みと
  テープの列の対で引く形の両方に掛かる)。
- 既存の試験 `tests/engine/time/test_t0_rng_key.py::test_no_caller_yet` は「`time_key_from_t_ns` の呼び手が無い」ことを検査する。
  書き換えに入るときは、この試験を「呼び手の一覧」の試験に書き直す必要がある(試験の意図の変更=親の確認が要る)。
- 「既定のランで効く所」の判定は読みだけ(実行で確かめていない)。
