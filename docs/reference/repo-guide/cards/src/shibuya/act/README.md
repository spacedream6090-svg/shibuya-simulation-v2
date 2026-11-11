# src/shibuya/act

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 3 本・その他 0 本(このディレクトリの直下)

下のディレクトリ: [intake](intake/README.md)

## [__init__.py](../../../../../../../src/shibuya/act/__init__.py)

(冒頭の説明なし)

## [activity.py](../../../../../../../src/shibuya/act/activity.py)

engine.activity — 行為と活動の二層の**活動層**(二層の実装 段 2・D-116・第276)。

- 公開の関数とクラス
  - `ActivityLayer`(クラス): 活動層(``engine.run`` が ``vocab_version="v3"`` かつ ``activity=True`` のときだけ作る)。
  - `ActivityPayload`(クラス): 1 応答ぶんの活動(パーサ v3 の欄を運ぶだけ)。
  - `activity_kind_of`(関数): 行動コード(と「あたり」の印)→ ``ActivityKind``(expedient・モジュール注記)。
  - `displayable_activity`(関数): B4b に出せる活動文か(なし・空・§2.4 ⑧ の個体依存語・⑥ の省略記法を含む文は出さない)。
  - `payload_of`(関数): ``BridgeResult``/艦隊の ``Outcome`` → 活動(語彙 v3 の応答だけ・それ以外は ``None``)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.calendar`・`shibuya.engine.commit`・`shibuya.engine.resolve`・`shibuya.foundation.hashing`・`shibuya.foundation.text.normalize`・`shibuya.foundation.time_consts`・`shibuya.foundation.vocab.actions`
- 呼び手: `shibuya.act.intent`・`shibuya.engine.run`・`shibuya.engine.systems.build`
- 読む試験: `tests/engine/space/test_nav1_units.py`・`tests/engine/test_intent_hold.py`・`tests/engine/test_presence_exit_walk.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/time/test_t0_time_consts.py`
- 状態台帳の行
  - 持ち主 `act_layer`(`ActivityLayer`)
    - `O1` ActivityLayer text・until_kind(挙動 behavior・復元 required) 道筋 `act_layer.text`・`act_layer.until_kind` 書ける系: activity_intent・presence
    - `O2` ActivityLayer text_id・_texts・_text_ids・_digest_cache(挙動 no・復元 derivable) 道筋 `act_layer._digest_cache`・`act_layer._text_ids`・`act_layer._texts`・`act_layer.text_id` 書ける系: activity_intent・checkpoint・close_final・day_close・presence
    - `O3` ActivityLayer _bt_agent・_bt_tick・_bt_start(挙動 no・復元 derivable) 道筋 `act_layer._bt_agent`・`act_layer._bt_start`・`act_layer._bt_tick` 書ける系: activity_intent
    - `O66` ActivityLayer の計数(挙動 diag・復元 discardable) 道筋 `act_layer.kind_counts`・`act_layer.n_arrival_expired`・`act_layer.n_cell_suppressed`・`act_layer.n_expiry_candidates`・`act_layer.n_fail_immediate`・`act_layer.n_intent_moves`・`act_layer.n_leave_expired`・`act_layer.n_partner_expired`・`act_layer.n_set`・`act_layer.n_wander_bad`・`act_layer.n_wander_steps` 書ける系: activity_intent・apply_responses・detect・phase_a・phase_c・presence
- 決定の ID: D-62・D-112・D-116・第 275・第 276

## [intent.py](../../../../../../../src/shibuya/act/intent.py)

engine.intent — **意図の保持**(段 2c・D-112 ①・D-114 案 A・第288)。

- 公開の関数とクラス
  - `IntentLayer`(クラス): 意図の保持(``engine.run`` が活動層と一緒に作る=語彙 v3・``--activity on``・``candidates``)。
  - `intent_summary`(関数): 計数 → manifest ``intent`` の形(アジェンダ §3-6)。
- import している内部モジュール: `shibuya.act.activity`・`shibuya.agents.state`・`shibuya.engine.commit`・`shibuya.engine.resolve`・`shibuya.foundation.vocab.actions`
- 呼び手: `shibuya.cli`・`shibuya.engine.run`・`shibuya.engine.systems.build`
- 読む試験: `tests/engine/space/test_nav1_units.py`・`tests/engine/test_intent_hold.py`
- 読む試験(道筋で): `tests/engine/systems/test_fix_guards.py`・`tests/engine/systems/test_stage_a_guard.py`
- 状態台帳の行
  - 持ち主 `intent_layer`(`IntentLayer`)
    - `O4` IntentLayer _payload(挙動 behavior・復元 required) 道筋 `intent_layer._payload` 書ける系: activity_intent・apply_responses・phase_a・phase_c
    - `O5` IntentLayer _proposals・_executing・_kept_walk(挙動 no・復元 discardable) 道筋 `intent_layer._executing`・`intent_layer._kept_walk`・`intent_layer._proposals` 書ける系: activity_intent・apply_responses・phase_a・phase_c
    - `O6` IntentLayer stats・ticks_sum・ticks_n(挙動 diag・復元 discardable) 道筋 `intent_layer.stats`・`intent_layer.ticks_n`・`intent_layer.ticks_sum` 書ける系: activity_intent・apply_responses・detect・phase_a・phase_c
- 決定の ID: D-51・D-62・D-112・D-114・D-122・第 288
