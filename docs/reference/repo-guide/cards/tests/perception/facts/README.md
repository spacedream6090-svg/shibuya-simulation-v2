# tests/perception/facts

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 7 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../tests/perception/facts/__init__.py)

(冒頭の説明なし)

## [head_renderer_136fdbb.py](../../../../../../../tests/perception/facts/head_renderer_136fdbb.py)

perception.renderer — 観測レコード → B0-B6 の決定論描画(知覚契約書 §2)。

- 公開の関数とクラス
  - `PerceptionAssets`(クラス): 描画に要る静的資産(セル代表点からの可視物・名称・歩行可能面積・天候表)。
  - `Rendered`(クラス): 1 起床ぶんの描画結果。
  - `Renderer`(クラス): 観測レンダラ(1 起床=1 呼び出し)。
  - `acquaintance_ids_in`(関数): 10e(E5・A8): B5 の本文に「(知人)」の印つきで出た相手の体 id(出た順・重複なし)=テープ版 4 の列。
  - `activity_line`(関数): 活動の (文, 人数) の列(人数降順→文字列順・上位 2)→ B4b の 1 行(無ければ ``""``)。
  - `check_hunger_words`(関数)
  - `check_near_order`(関数)
  - `check_near_tiebreak`(関数)
  - `check_p_see_activity`(関数): 活動の種別の乗数表を検査して、全部の鍵を持つ辞書で返す(欠けた鍵は 1.0)。
  - `check_signage_p_see`(関数): 看板の注視確率を検査して返す(0.0〜1.0 の外は ``ValueError``)。
  - `compose_memory_line`(関数): 項(順位の高い順)→ B5「記憶」の 1 行と載せた項の数(6b・M4)。0 件なら ``("", 0)``。
  - `intent_line`(関数): 意図の 1 行(``INTENT_LINE_MAX_TOKENS`` に収まるよう対象の名を末尾から切り詰める)。
  - `memory_item_text`(関数): 想起した 1 行(``engine.memory.RecallItem`` と同じ欄を持つもの)→ B5「記憶」の項 1 件(6b・v1.2)。
  - `named_closed_note`(関数): Q25 の補足の 1 句(店名 + 閉店中 + あれば「HH:MM に開く」・≤ 15 tok)。
  - `near_tie_keys`(関数): 観る体 ``observer`` から見た相手 ``ids`` の撹拌鍵(u64・splitmix64 の仕上げ・配列演算)。
  - `near_tie_salt64`(関数): ``blake3(run_salt ‖ b"nt\x00")`` の先頭 8 バイト(u64)。1 ランに 1 回だけ作る。
  - `person_word`(関数): 個体 id → 観測に出る人 ID の表層(``P-17``)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.foundation.hashing`・`shibuya.foundation.text.channels`・`shibuya.foundation.text.hashes`・`shibuya.foundation.text.normalize`・`shibuya.foundation.text.templates`・`shibuya.foundation.time_consts`・`shibuya.perception.attention`・`shibuya.world.assets`・`shibuya.world.state`
- 読む試験(道筋で): `tests/perception/facts/scenes.py`
- 決定の ID: D-59・D-60・D-71・D-111・D-113・D-117・D-118・D-121・第 269・第 300・第 304

## [scenes.py](../../../../../../../tests/perception/facts/scenes.py)

第 1 期 1-2 の試験の道具(試験ではない): HEAD の描画の写しの読み込み・合成の場面・HEAD の双子の描画。

- 公開の関数とクラス
  - `build`(関数): 合成世界+個体(同じセルに複数体・内受容と所持金と行為と直前の結果がばらける)。
  - `head_module`(関数)
  - `twin`(関数): 1-2 の描画 ``r`` の HEAD の双子(同じ物を指す・設定と口を写す)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.world.state`・`tests/_head_copy_pin.py`
- 読む試験: `tests/engine/speech/test_speech_on_reaches_addressee.py`・`tests/perception/facts/test_coef_removed_or_armed.py`・`tests/perception/facts/test_percept_schema.py`・`tests/perception/facts/test_render_from_percept_bytes.py`

## [test_coef_removed_or_armed.py](../../../../../../../tests/perception/facts/test_coef_removed_or_armed.py)

第 1 期 1-2 知覚の分離: 係数は消した(口の約束 1-2 の〔決定〕・決定 10-12 §1-6「係数で持たない」)。

- 公開の関数とクラス
  - `test_manifest_fields`(関数)
  - `test_names_are_gone`(関数)
  - `test_phone_flag_does_not_change_the_primary_detection`(関数)
  - `test_removed_values_are_not_in_src`(関数)
  - `test_signage_gate_is_one_p_for_every_activity`(関数)
- import している内部モジュール: `shibuya.engine.run`・`shibuya.foundation.ports.percept`・`shibuya.perception.attention`・`shibuya.perception.p_notice`・`shibuya.perception.renderer`・`tests/perception/facts/scenes.py`
- 環境変数: `SHIBUYA_PERCEPT_COEFS`
- 決定の ID: 10-12/§1-6

## [test_percept_is_scratch.py](../../../../../../../tests/perception/facts/test_percept_is_scratch.py)

第 1 期 1-2 知覚の分離: ``Percept`` は刻みの中の一時(口の約束 1-2 の約束 (3)・段 C の守り)。

- 公開の関数とクラス
  - `recorded_tape`(関数): 偽 vLLM で録ったテープ(作業木の src)。
  - `test_ledger_row_p_is_out_of_both_hashes`(関数)
  - `test_percepts_are_not_in_the_final_or_the_state_files`(関数): Percept の有無は状態に入らない: 描いた Percept を捨てても(scratch に書かない形)final は同じ。
  - `test_percepts_live_only_inside_their_step`(関数)
  - `test_replay_full_hash_does_not_see_percepts`(関数): Percept を作る形と作らない形で、再生の全部の checkpoint の full-hash が同じ(Percept は状態に入らない)。
  - `test_replay_full_hash_matches_the_head_copy`(関数): 検収 M1 の再現の形: 同じテープを HEAD の写し(1-2 の前の src)と作業木の src で再生し、全部の checkpoint の
  - `test_replay_inbox_never_holds_a_percept`(関数)
  - `test_reset_empties_the_field`(関数)
  - `test_runs_under_the_stage_b_and_sentinel_checks`(関数)
  - `test_scratch_field_and_its_single_writer`(関数)
  - `test_stage_c_stops_a_write_from_another_system`(関数)
  - `test_stub_renderer_writes_an_empty_mapping`(関数)
- import している内部モジュール: `shibuya.engine.llm_bridge`・`shibuya.engine.resume`・`shibuya.engine.run`・`shibuya.engine.state_hashes`・`shibuya.engine.state_ledger`・`shibuya.engine.systems.boxes`・`shibuya.engine.systems.conductor`・`shibuya.engine.systems.decide`・`shibuya.engine.systems.table`・`shibuya.foundation.ports.percept`・`shibuya.foundation.write_guard`・`shibuya.llm.fleet`・`shibuya.perception.renderer`・`shibuya.world.state`・`tests/_head_copy_pin.py`・`tests/_places.py`・`tests/engine/test_tape_deferred.py`・`tests/engine/test_tape_wiring.py`・`tests/llm/test_fleet.py`
- 環境変数: `SHIBUYA_SYSTEMS_CHECK`・`os.environ` をまるごと使う
- 決定の ID: D-58・第 337

## [test_percept_schema.py](../../../../../../../tests/perception/facts/test_percept_schema.py)

第 1 期 1-2 知覚の分離: ``perception.facts.Percept`` の形(口の約束 1-2・回答 10-13b §4-2)。

- 公開の関数とクラス
  - `test_brief_fields_carry_the_named_parts`(関数): 発注の欄: 見えた物(id・種類・距離・向き)・見えた人(id・向き・行為)・音(段)・時刻の見方(日の中の秒・暦の日の種類)・
  - `test_day_kind_comes_from_the_calendar_hook_and_does_not_touch_bytes`(関数)
  - `test_decision_input_shape_and_drawing_port`(関数)
  - `test_empty_fields_default_to_none`(関数)
  - `test_event_ref_has_the_shape_of_the_event_id`(関数)
  - `test_facts_match_the_state`(関数)
  - `test_fields_and_order_are_frozen`(関数)
  - `test_intent_wake_and_memories_are_carried`(関数)
  - `test_manifest_instrument`(関数)
  - `test_percept_cannot_be_written`(関数)
  - `test_records_are_frozen_with_slots`(関数)
  - `test_rendered_percepts_have_the_empty_fields_empty`(関数)
  - `test_run_manifest_has_the_percept_section`(関数)
  - `test_seen_people_are_the_near_line_in_order`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.run`・`shibuya.foundation.journal.log`・`shibuya.foundation.ports.percept`・`shibuya.foundation.text.normalize`・`shibuya.foundation.text.templates`・`shibuya.perception.renderer`・`tests/perception/facts/scenes.py`
- 決定の ID: 10-13b/§4-2・11-01・11-02r/§1・11-02r/§1 #7・11-03/§3・第 340

## [test_render_from_percept_bytes.py](../../../../../../../tests/perception/facts/test_render_from_percept_bytes.py)

第 1 期 1-2 知覚の分離: 「状態 → Percept → 文」の描画が 1-2 の前の描画とバイト一致(口の約束 1-2 の約束 (1))。

- 公開の関数とクラス
  - `recall_for`(関数): 双子の想起の口=1-2 の側が引いた行をそのまま返す(想起の計数を 2 回にしない)。
  - `same_rendered`(関数): 2 つの描画の結果で違う欄の名(空なら同じ)。
  - `test_19_configs_render_the_same_bytes_as_head`(関数)
  - `test_a_percept_from_another_step_is_refused`(関数): 刻みの外で残らない(1-2 の約束 (3)): 前の刻みの Percept は描かない。
  - `test_counters_match_head`(関数): 描画の計数(診断の行 O84)も 1-2 の前と同じ(draw を呼ばずに比べる)。
  - `test_negative_control_one_byte_change_is_caught`(関数): 負の対照: 描き方を 1 文字だけ変えると双子との比べで落ちる(比べが恒真でない)。
  - `test_render_without_prepare_and_out_of_area_cells`(関数): ``prepare_tick`` を呼ばずに描く道(``render`` が自分で前計算する)と、セルの外の体も同じ。
  - `test_synthetic_scenes_render_the_same_bytes_as_head`(関数)
  - `test_the_19_configs_are_the_byte_check_set`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.cli`・`shibuya.engine.memory`・`shibuya.engine.proximity`・`shibuya.foundation.text.hashes`・`shibuya.perception.renderer`・`tests/perception/facts/scenes.py`
- 決定の ID: 第 346
