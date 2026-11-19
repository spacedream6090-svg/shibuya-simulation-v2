# src/shibuya/mind/percept

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 4 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/mind/percept/__init__.py)

(冒頭の説明なし)

## [attention.py](../../../../../../../../src/shibuya/mind/percept/attention.py)

mind.percept.attention — 割る段で ``perception/attention.py`` を割った割り先(全ファイルの表 §4・名の表は``tools/pkgmove/map.toml`` の割る行)。

- 公開の関数とクラス
  - `gate_stage1`(関数): 段1 の一発ベルヌーイ(決定論・``core.rng.stream`` のドメイン分離)。
  - `p_see`(関数): 媒体 → 視認確率(§4 段1)。
- import している内部モジュール: `shibuya.foundation.rng`
- 呼び手: `shibuya.mind.memory.familiarity`・`shibuya.mind.percept.notice`
- 読む試験: `tests/engine/test_familiarity.py`・`tests/perception/facts/head_renderer_136fdbb.py`・`tests/perception/facts/test_coef_removed_or_armed.py`・`tests/perception/test_attention.py`・`tests/perception/test_p_see_activity.py`・`tests/perception/test_signage_p_see_gate.py`
- 決定の ID: 11-03

## [draw.py](../../../../../../../../src/shibuya/mind/percept/draw.py)

mind.percept.draw — 割る段で ``perception/renderer.py`` を割った割り先(全ファイルの表 §4・名の表は``tools/pkgmove/map.toml`` の割る行)。

- 公開の関数とクラス
  - `Rendered`(クラス): 1 起床ぶんの描画結果。
  - `Renderer`(クラス): 観測レンダラ(1 起床=1 呼び出し)。
  - `acquaintance_ids_in`(関数): 10e(E5・A8): B5 の本文に「(知人)」の印つきで出た相手の体 id(出た順・重複なし)=テープ版 4 の列。
  - `check_hunger_words`(関数)
  - `compose_memory_line`(関数): 項(順位の高い順)→ B5「記憶」の 1 行と載せた項の数(6b・M4)。0 件なら ``("", 0)``。
  - `memory_item_text`(関数): 想起した 1 行(``engine.memory.RecallItem`` と同じ欄を持つもの)→ B5「記憶」の項 1 件(6b・v1.2)。
  - `strip_speech_imperatives`(関数): 発話の本文 → 看板と同じ表(``strip_imperatives``)で落とした後、発話だけの型(``SPEECH_IMPERATIVE_PATTERNS``)の文も落とす。
- import している内部モジュール: `shibuya.foundation.hashing`・`shibuya.foundation.ports.percept`・`shibuya.foundation.ports.percept_contact`・`shibuya.foundation.text.channels`・`shibuya.foundation.text.hashes`・`shibuya.foundation.text.normalize`・`shibuya.foundation.text.percept_words`・`shibuya.foundation.text.salience`・`shibuya.foundation.text.templates`・`shibuya.foundation.vocab.agent_codes`・`shibuya.mind.percept.notice`・`shibuya.world.model.agent_table`・`shibuya.world.model.percept_scene`・`shibuya.world.model.state`
- 呼び手: `shibuya.interfaces.cli.main`・`shibuya.mind.memory.memory_store`・`shibuya.runtime.result`・`shibuya.runtime.run`・`shibuya.runtime.systems.assemble`・`shibuya.runtime.systems.report`・`tools/c6/ablation1_fixed_vs_ranking.py`
- 読む試験: `tests/build_lang/test_wiring.py`・`tests/engine/proximity/test_runs.py`・`tests/engine/speech/test_speech_on_reaches_addressee.py`・`tests/engine/speech/test_speech_port_schema.py`・`tests/engine/test_c9b_targets_attention.py`・`tests/engine/test_energy_balance.py`・`tests/engine/test_familiarity.py`・`tests/engine/test_intent_hold.py`・`tests/engine/test_meal_bundle_2b.py`・`tests/engine/test_memory_recall.py`・`tests/engine/test_relations.py`・`tests/engine/test_renderer_wiring.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_stage3_small_fixes.py`・`tests/engine/test_store_choice.py`・`tests/engine/test_tape_wiring.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/test_weather_calendar_10e.py`・`tests/engine/tools/test_c0_signboard_mark_invariance.py`・`tests/perception/facts/test_coef_removed_or_armed.py`・`tests/perception/facts/test_perceive_order.py`・`tests/perception/facts/test_percept_is_scratch.py`・`tests/perception/facts/test_percept_schema.py`・`tests/perception/facts/test_render_from_percept_bytes.py`・`tests/perception/test_ablation1.py`・`tests/perception/test_ablation6_signage.py`・`tests/perception/test_b4_detector_gap.py`・`tests/perception/test_b4b_queue_feed.py`・`tests/perception/test_b6_invite.py`・`tests/perception/test_intent_mode_open.py`・`tests/perception/test_near_tiebreak.py`・`tests/perception/test_nearby_vectorized.py`・`tests/perception/test_p_see_activity.py`・`tests/perception/test_renderer_golden.py`・`tests/perception/test_signage_p_see_gate.py`・`tests/perception/test_templates.py`・`tests/perception/test_vocab_v2_templates.py`・`tests/perception/test_weather_a48.py`
- 読む試験(道筋で): `tests/tools/test_pkgmove.py`
- 状態台帳の行
  - 持ち主 `renderer`(`Renderer`)
    - `O63` PerceptionRenderer のキャッシュ _b1_cache〜_b4_cache・_rank_cell_cache・_acq_cache・_tickc(挙動 no・復元 derivable) 道筋 `renderer._acq_cache`・`renderer._b1_cache`・`renderer._b2_cache`・`renderer._b3_cache`・`renderer._b4_cache`・`renderer._rank_cell_cache`・`renderer._tickc` 書ける系: decide・perceive_prepare・world
    - `O64` PerceptionRenderer の口 acquaintance_fn・memory_recall・session_partner_fn・named_closed_lookup・signage_exposures(挙動 no・復元 discardable) 道筋 `renderer.acquaintance_fn`・`renderer.memory_recall`・`renderer.named_closed_lookup`・`renderer.session_partner_fn`・`renderer.signage_exposures` 書ける系: decide・memory
    - `O84` PerceptionRenderer の計数(挙動 diag・復元 discardable) 道筋 `renderer.cache_hits`・`renderer.cache_misses`・`renderer.contact_lines`・`renderer.contact_lines_over_budget`・`renderer.contact_unnoticed_renders`・`renderer.intent_lines`・`renderer.intent_lines_over_budget`・`renderer.memory_items`・`renderer.memory_items_dropped_for_budget`・`renderer.memory_items_dropped_for_channel`・`renderer.memory_line_tokens`・`renderer.memory_lines`・`renderer.memory_lines_over_budget`・`renderer.named_closed_notes`・`renderer.near_order_ties`・`renderer.near_tie_breaks`・`renderer.near_tie_candidates`・`renderer.renders`・`renderer.signage_gate_draws`・`renderer.signage_gate_shown`・`renderer.speech_lines`・`renderer.speech_lines_over_budget`・`renderer.truncation_count` 書ける系: decide・perceive_prepare
- 決定の ID: 10-12/§1-6・11-03・D-59・D-60・D-71・D-111・D-113・D-117・D-118・第 269・第 300・第 304

## [notice.py](../../../../../../../../src/shibuya/mind/percept/notice.py)

mind.percept.notice — 割る段で ``perception/renderer.py`` を割った割り先(全ファイルの表 §4・名の表は``tools/pkgmove/map.toml`` の割る行)。

- 公開の関数とクラス
  - `SignageNotice`(クラス): 看板に気づく側(注視の抽選と看板の文)。
  - `check_signage_p_see`(関数): 看板の注視確率を検査して返す(0.0〜1.0 の外は ``ValueError``)。
- import している内部モジュール: `shibuya.foundation.text.salience`・`shibuya.foundation.time_consts`・`shibuya.mind.percept.attention`
- 呼び手: `shibuya.mind.percept.draw`・`shibuya.runtime.systems.assemble`
- 読む試験: `tests/perception/test_signage_p_see_gate.py`
- 読む試験(道筋で): `tests/tools/test_pkgmove.py`
- 状態台帳の行
  - 持ち主 `renderer` の別のクラス `SignageNotice`(行は `shibuya.mind.percept.draw` のカードを見る)
- 決定の ID: 10-12/§1-6・D-59
