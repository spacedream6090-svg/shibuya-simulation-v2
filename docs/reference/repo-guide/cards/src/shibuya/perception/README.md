# src/shibuya/perception

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 3 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../src/shibuya/perception/__init__.py)

(冒頭の説明なし)

- 読む試験(道筋で): `tests/tools/test_pkgmove.py`

## [attention.py](../../../../../../../src/shibuya/perception/attention.py)

perception.attention — 注意ゲート 段0-段3(知覚契約書 §4)。「届く」→「気づく」。

- 公開の関数とクラス
  - `SalientItem`(クラス): 顕著性順位づけの入力(1件)。
  - `StripReport`(クラス): 命令文除去の記録(黙って消さない=診断行へ)。
  - `apply_budget`(関数): 段2 の件数上限(既定は**非注入**=枠に入らなければ載せない)。
  - `content_cap_chars`(関数): 注視秒 → 日本語字数の上限 ``round(7.5×秒)``(下限4・上限30)。
  - `feature_tag`(関数): 素性タグの固定文言(§1 条6)。
  - `gate_stage1`(関数): 段1 の一発ベルヌーイ(決定論・``core.rng.stream`` のドメイン分離)。
  - `p_see`(関数): 媒体 → 視認確率(§4 段1)。
  - `rank_by_saliency`(関数): 顕著性=**視角×局所コントラスト(+動き・逸脱度)**の降順に並べ替える。
  - `strip_imperatives`(関数): 世界内テキストから**命令文を文単位で除去**する(§1 条6・§4 段3)。
  - `tag_world_text`(関数): 世界内テキスト → (素性タグ+命令文除去+内容キャップ済みの本文, 除去記録)。
- import している内部モジュール: `shibuya.foundation.rng`
- 呼び手: `shibuya.build.lang.common`・`shibuya.mind.memory.familiarity`・`shibuya.perception.renderer`・`shibuya.world.laws.civic`・`shibuya.world.laws.salient`
- 読む試験: `tests/build_lang/test_w14_signage.py`・`tests/engine/processes/test_salient.py`・`tests/engine/speech/test_speech_on_reaches_addressee.py`・`tests/engine/test_familiarity.py`・`tests/perception/facts/head_renderer_136fdbb.py`・`tests/perception/facts/test_coef_removed_or_armed.py`・`tests/perception/test_attention.py`・`tests/perception/test_p_see_activity.py`・`tests/perception/test_signage_p_see_gate.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 決定の ID: 11-03

## [renderer.py](../../../../../../../src/shibuya/perception/renderer.py)

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
  - `check_signage_p_see`(関数): 看板の注視確率を検査して返す(0.0〜1.0 の外は ``ValueError``)。
  - `compose_memory_line`(関数): 項(順位の高い順)→ B5「記憶」の 1 行と載せた項の数(6b・M4)。0 件なら ``("", 0)``。
  - `intent_line`(関数): 意図の 1 行(``INTENT_LINE_MAX_TOKENS`` に収まるよう対象の名を末尾から切り詰める)。
  - `memory_item_text`(関数): 想起した 1 行(``engine.memory.RecallItem`` と同じ欄を持つもの)→ B5「記憶」の項 1 件(6b・v1.2)。
  - `named_closed_note`(関数): Q25 の補足の 1 句(店名 + 閉店中 + あれば「HH:MM に開く」・≤ 15 tok)。
  - `near_person_text`(関数): 見えた人(``facts.SeenPerson``)→ B5 近接行の項(``P-<id>(未知/知人)``・1-2 の前と同じ表層)。
  - `near_tie_keys`(関数): 観る体 ``observer`` から見た相手 ``ids`` の撹拌鍵(u64・splitmix64 の仕上げ・配列演算)。
  - `near_tie_salt64`(関数): ``blake3(run_salt ‖ b"nt\x00")`` の先頭 8 バイト(u64)。1 ランに 1 回だけ作る。
  - `person_word`(関数): 個体 id → 観測に出る人 ID の表層(``P-17``)。
  - `strip_speech_imperatives`(関数): 発話の本文 → 看板と同じ表(``strip_imperatives``)で落とした後、発話だけの型(``SPEECH_IMPERATIVE_PATTERNS``)の文も落とす。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.foundation.hashing`・`shibuya.foundation.ports.percept`・`shibuya.foundation.ports.percept_contact`・`shibuya.foundation.text.channels`・`shibuya.foundation.text.hashes`・`shibuya.foundation.text.normalize`・`shibuya.foundation.text.templates`・`shibuya.foundation.time_consts`・`shibuya.perception.attention`・`shibuya.world.assets`・`shibuya.world.model.state`
- 呼び手: `shibuya.cli`・`shibuya.engine.change_detect`・`shibuya.engine.run`・`shibuya.mind.memory.memory_store`・`shibuya.runtime.systems.assemble`・`shibuya.runtime.systems.report`・`tools/c6/ablation1_fixed_vs_ranking.py`
- 読む試験: `tests/build_lang/test_wiring.py`・`tests/engine/memory/test_m0_store_schema.py`・`tests/engine/memory/test_mr65_guards.py`・`tests/engine/proximity/test_runs.py`・`tests/engine/speech/test_speech_on_reaches_addressee.py`・`tests/engine/speech/test_speech_port_schema.py`・`tests/engine/test_area_source_c9c.py`・`tests/engine/test_assets_10e_b0_b1.py`・`tests/engine/test_c9b_targets_attention.py`・`tests/engine/test_energy_balance.py`・`tests/engine/test_familiarity.py`・`tests/engine/test_geometry_c9.py`・`tests/engine/test_intent_hold.py`・`tests/engine/test_meal_bundle_2b.py`・`tests/engine/test_memory_recall.py`・`tests/engine/test_relations.py`・`tests/engine/test_renderer_wiring.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_stage3_small_fixes.py`・`tests/engine/test_store_choice.py`・`tests/engine/test_tape_wiring.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/test_weather_calendar_10e.py`・`tests/engine/tools/test_c0_signboard_mark_invariance.py`・`tests/llm/test_fleet_contract.py`・`tests/perception/facts/test_coef_removed_or_armed.py`・`tests/perception/facts/test_percept_is_scratch.py`・`tests/perception/facts/test_percept_schema.py`・`tests/perception/facts/test_render_from_percept_bytes.py`・`tests/perception/test_ablation1.py`・`tests/perception/test_ablation6_signage.py`・`tests/perception/test_b4_detector_gap.py`・`tests/perception/test_b4b_queue_feed.py`・`tests/perception/test_b6_invite.py`・`tests/perception/test_intent_mode_open.py`・`tests/perception/test_near_tiebreak.py`・`tests/perception/test_nearby_vectorized.py`・`tests/perception/test_p_see_activity.py`・`tests/perception/test_renderer_golden.py`・`tests/perception/test_signage_p_see_gate.py`・`tests/perception/test_templates.py`・`tests/perception/test_vocab_v2_templates.py`
- 読む試験(道筋で): `tests/engine/test_salt_seed_split_10f.py`・`tests/test_places_guard.py`
- 状態台帳の行
  - 持ち主 `renderer`(`Renderer`)
    - `O63` PerceptionRenderer のキャッシュ _b1_cache〜_b4_cache・_rank_cell_cache・_acq_cache・_tickc(挙動 no・復元 derivable) 道筋 `renderer._acq_cache`・`renderer._b1_cache`・`renderer._b2_cache`・`renderer._b3_cache`・`renderer._b4_cache`・`renderer._rank_cell_cache`・`renderer._tickc` 書ける系: decide・perceive_prepare・world
    - `O64` PerceptionRenderer の口 acquaintance_fn・memory_recall・session_partner_fn・named_closed_lookup・signage_exposures(挙動 no・復元 discardable) 道筋 `renderer.acquaintance_fn`・`renderer.memory_recall`・`renderer.named_closed_lookup`・`renderer.session_partner_fn`・`renderer.signage_exposures` 書ける系: decide・memory
    - `O84` PerceptionRenderer の計数(挙動 diag・復元 discardable) 道筋 `renderer.cache_hits`・`renderer.cache_misses`・`renderer.contact_lines`・`renderer.contact_lines_over_budget`・`renderer.contact_unnoticed_renders`・`renderer.intent_lines`・`renderer.intent_lines_over_budget`・`renderer.memory_items`・`renderer.memory_items_dropped_for_budget`・`renderer.memory_items_dropped_for_channel`・`renderer.memory_line_tokens`・`renderer.memory_lines`・`renderer.memory_lines_over_budget`・`renderer.named_closed_notes`・`renderer.near_order_ties`・`renderer.near_tie_breaks`・`renderer.near_tie_candidates`・`renderer.renders`・`renderer.signage_gate_draws`・`renderer.signage_gate_shown`・`renderer.speech_lines`・`renderer.speech_lines_over_budget`・`renderer.truncation_count` 書ける系: decide・perceive_prepare
- 決定の ID: 10-12/§1-6・10-12/§1-13・11-03・D-59・D-60・D-71・D-111・D-113・D-117・D-118・第 269・第 300・第 304
