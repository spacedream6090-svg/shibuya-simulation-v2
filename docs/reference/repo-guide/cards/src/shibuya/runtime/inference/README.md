# src/shibuya/runtime/inference

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 5 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/runtime/inference/__init__.py)

(冒頭の説明なし)

## [bridge.py](../../../../../../../../src/shibuya/runtime/inference/bridge.py)

engine.llm_bridge — エンジンと LLM クライアントの**唯一の接点**(録画/リプレイ・δ_think・解釈)。

- 公開の関数とクラス
  - `BridgeResult`(クラス): 1呼の結果(エンジンが intent を組むのに必要なものだけ)。
  - `CallStart`(クラス): 〔第 1 期 1-8 J0〕1 呼の前半(知覚の事実まで)。``LLMBridge.begin`` が作り ``finish`` が残りを行う。
  - `LLMBridge`(クラス): エンジン ↔ LLM の一本道。``mode="record"`` は実クライアント/mock、``"replay"`` はテープ。
  - `PerceptionRendererAdapter`(クラス): ``perception.renderer.Renderer`` を bridge の ``Renderer`` 契約へ橋渡しする。
  - `StubRenderer`(クラス): 決定論の最小プロンプト(``prompt_hash`` が (agent, cell, tick//5, wake_class) で決まる)。
  - `delta_think_ticks`(関数): レーン → δ_think[tick]\(**分tickへ切り上げ**・運用設計書 §2.4)。
- import している内部モジュール: `shibuya.act.intake.parser`・`shibuya.act.intake.undefined`・`shibuya.foundation.ports.inference`・`shibuya.foundation.text.templates`・`shibuya.foundation.vocab.actions`・`shibuya.runtime.inference.mock`・`shibuya.runtime.inference.tape`
- 呼び手: `shibuya.runtime.result`・`shibuya.runtime.run`・`shibuya.runtime.systems.assemble`・`shibuya.runtime.systems.llm_io`・`shibuya.runtime.systems.run_end`
- 読む試験: `tests/engine/clock/test_tm2_talk_clock.py`・`tests/engine/decision/_j0.py`・`tests/engine/decision/test_j0_mock_equivalence.py`・`tests/engine/decision/test_j0_port_schema.py`・`tests/engine/duties/test_du_runs.py`・`tests/engine/memory/test_m0_render_bytes.py`・`tests/engine/rights/test_no_permission_count.py`・`tests/engine/rights/test_rights_events.py`・`tests/engine/test_renderer_wiring.py`・`tests/engine/test_tape_wiring.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/test_undefined_action.py`・`tests/engine/tools/test_c0_affordance_from_registry.py`・`tests/llm/test_fleet.py`・`tests/llm/test_fleet_contract.py`・`tests/perception/facts/test_percept_is_scratch.py`・`tests/perception/test_weather_a48.py`
- 状態台帳の行
  - 持ち主 `bridge`(`LLMBridge`)
    - `O85` LLMBridge _interned(テープへ書いた共有ブロック)(挙動 no・復元 required) 道筋 `bridge._interned` 書ける系: close_final・decide
    - `O86` LLMBridge の計数(挙動 diag・復元 discardable) 道筋 `bridge.n_calls`・`bridge.n_deferred`・`bridge.n_dictionary_mapped`・`bridge.n_label_alias`・`bridge.n_parse_errors`・`bridge.n_parse_errors_strict`・`bridge.n_positional`・`bridge.n_role_actions`・`bridge.n_role_unauthorized`・`bridge.n_role_unjudged`・`bridge.n_tape_misses`・`bridge.n_tape_rows`・`bridge.n_undefined_mapped`・`bridge.n_unknown_action` 書ける系: close_final・decide
- 決定の ID: D-58・D-59・D-71

## [fleet.py](../../../../../../../../src/shibuya/runtime/inference/fleet.py)

llm.fleet — 実 vLLM 艦隊クライアント(httpx 非同期 × N レプリカ)と艦隊ブリッジ。

- 公開の関数とクラス
  - `FleetBridge`(クラス): ``engine.llm_bridge`` の ``source="fleet"`` 実装(層契約のため llm 側に置く)。
  - `FleetBridgeResult`(クラス): 1 呼の解釈済み結果(engine が intent を組むのに必要なものだけ)。
  - `FleetClient`(クラス): 実 vLLM 艦隊への非同期クライアント(engine の同期ループから使う)。
  - `FleetConfig`(クラス): 艦隊設定(manifest ``llm_fleet`` 節のうちクライアントが要る分)。
  - `FleetTapeRow`(クラス): ``engine.tape.TapeRow`` と**同じ欄名**の既定行(テープ実体を注入しないときの器)。
  - `TapeSink`(クラス): 録画テープの書き出し口(``engine.tape.TapeWriter`` がこの形を満たす)。
  - `call_from_request`(関数): ``llm.LLMRequest`` → ``LLMCall``(同期経路と既存テストのための橋)。
  - `fleet_auth_headers`(関数): ``SHIBUYA_FLEET_API_KEY`` が空でなければ ``Authorization: Bearer <値>``。無ければ None。
  - `l4_calls_per_day`(関数): 予算行 L4「上限 400 万呼/日(o64)」を読む(憲法1 の監査点)。
  - `l6_in_flight_per_gpu`(関数): 予算行 L6「**64 in-flight/GPU**(bounded)」を読む(数値をコード側に複製しない)。
  - `plan_batch`(関数): 1 バッチの発射順とレプリカ割当を決める**純関数**(実装計画書 §7 順序制御)。
- import している内部モジュール: `shibuya.act.intake.parser`・`shibuya.act.intake.undefined`・`shibuya.foundation.budget`・`shibuya.foundation.hashing`・`shibuya.foundation.manifest.schema`・`shibuya.foundation.ports.inference`・`shibuya.foundation.vocab.actions`
- 呼び手: `shibuya.interfaces.cli.run_args`・`shibuya.runtime.run`・`shibuya.runtime.systems.assemble`・`tools/c6/c6lib.py`・`tools/vocab/adjudicate.py`
- 読む試験: `tests/c6/test_l4_l6_budget.py`・`tests/engine/test_fleet_wiring.py`・`tests/engine/test_response_delay.py`・`tests/engine/test_state_checks_10f.py`・`tests/engine/test_tape_deferred.py`・`tests/engine/time/test_v30a_key_sites.py`・`tests/llm/test_fleet.py`・`tests/llm/test_fleet_auth.py`・`tests/llm/test_fleet_contract.py`・`tests/perception/facts/test_percept_is_scratch.py`・`tests/test_cli_l4_scale.py`
- 状態台帳の行
  - 持ち主 `fleet_bridge`(`FleetBridge`)
    - `O88` FleetBridge _interned(挙動 no・復元 required) 道筋 `fleet_bridge._interned` 書ける系: decide・drain・llm_receive
    - `O89` FleetBridge の計数(挙動 diag・復元 discardable) 道筋 `fleet_bridge.n_calls`・`fleet_bridge.n_debug_rows`・`fleet_bridge.n_debug_skipped`・`fleet_bridge.n_deferred`・`fleet_bridge.n_deferred_rows`・`fleet_bridge.n_dictionary_mapped`・`fleet_bridge.n_label_alias`・`fleet_bridge.n_parse_errors`・`fleet_bridge.n_parse_errors_strict`・`fleet_bridge.n_positional`・`fleet_bridge.n_role_actions`・`fleet_bridge.n_tape_rows`・`fleet_bridge.n_undefined_mapped`・`fleet_bridge.n_unknown_action` 書ける系: decide・drain・llm_receive
- 環境変数: `SHIBUYA_FLEET_API_KEY`
- 決定の ID: D-55・D-58・D-71

## [mock.py](../../../../../../../../src/shibuya/runtime/inference/mock.py)

llm.mock — ネットワーク不要の決定論クライアント(MockLLM)とテープ再生クライアント(TapeLLM)。

- 公開の関数とクラス
  - `MockLLM`(クラス): 決定論の 2 行形を返す mock クライアント(ネットワーク・GPU 不要)。
  - `TapeLLM`(クラス): 録画テープから答えるクライアント。**テープ外は例外**(黙って実LLMへ落とさない)。
- import している内部モジュール: `shibuya.foundation.ports.inference`・`shibuya.foundation.rng`・`shibuya.foundation.types`・`shibuya.foundation.vocab.actions`
- 呼び手: `shibuya.experiments.drive.switch`・`shibuya.runtime.inference.bridge`・`shibuya.runtime.run`・`shibuya.runtime.systems.assemble`・`tools/c6/metric_b_rerun.py`
- 読む試験: `tests/c6/test_t5_order_bias.py`・`tests/engine/decision/test_j0_mock_equivalence.py`・`tests/engine/decision/test_j0_port_schema.py`・`tests/engine/decision/test_j0_shuffle_invariance.py`・`tests/engine/experiment/test_cf33b_switch.py`・`tests/engine/speech/test_speech_choice_utterance.py`・`tests/engine/speech/test_speech_default_off_invariance.py`・`tests/engine/test_intent_hold.py`・`tests/engine/test_llm_mock.py`・`tests/engine/test_move_destination.py`・`tests/engine/test_salt_seed_split_10f.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_tape_wiring.py`・`tests/engine/test_undefined_action.py`・`tests/llm/test_fleet_contract.py`・`tests/llm/test_mock_v3.py`・`tests/llm/test_undefined.py`
- 読む試験(道筋で): `tests/engine/bridging/test_bridging_ledger.py`
- 決定の ID: D-116・D-119・第 277

## [tape.py](../../../../../../../../src/shibuya/runtime/inference/tape.py)

engine.tape — LLM 録画テープ(1呼=1行 Parquet/zstd)と完全一致リプレイ。

- 公開の関数とクラス
  - `Replay`(クラス): テープからの完全一致リプレイ。**テープ外は必ず失敗**(実LLMへ落とさない)。
  - `Tape`(クラス): テープの読み出し(``calls.parquet`` + ``blocks.parquet``)。
  - `TapeDeferred`(クラス): 引いた行が**繰り延べ行**だった(=この呼に応答は無い・D-58)。
  - `TapeHit`(クラス): ``Replay.lookup_row`` の戻り(1行ぶんの再生に要る欄だけ)。
  - `TapeMiss`(クラス): テープに無い呼び出しを引いた(=リプレイ失敗。実LLMへは落とさない)。
  - `TapeRow`(クラス): 1呼=1行(``deferred=1`` なら「答えの返らなかった 1 呼」=D-58)。
  - `TapeWriter`(クラス): テープ書き出し(Parquet/zstd)。``with`` で使うか ``close()`` を呼ぶこと。
  - `block_id_for`(関数): 共有プロンプトブロックの内容アドレス ``blake3(text)[:16]`` の16進32桁。
  - `read_run_meta`(関数): テープの脇の meta を読む(無ければ空 dict=10a より前の録画)。
  - `tape_v4_fields`(関数): テープ版 4(10e・E5)の 7 列の値を、描画の出力(``RenderedPrompt``)か艦隊の呼(``LLMCall``)から作る。
- import している内部モジュール: `shibuya.foundation.hashing`・`shibuya.foundation.text.channels`
- 呼び手: `shibuya.experiments.drive.branch`・`shibuya.runtime.inference.bridge`・`shibuya.runtime.run`・`shibuya.runtime.systems.assemble`・`tools/c6/ablation1_fixed_vs_ranking.py`・`tools/c6/c6lib.py`・`tools/c6/format_role_rates.py`・`tools/c6/t6_bit_reproduce.py`・`tools/c6/t7_distribution.py`・`tools/c8/ablation_runner.py`・`tools/fig/fig_ab7_actions.py`・`tools/fig/fig_ab7c_vocab.py`・`tools/fig/fig_d91_ride_chain.py`・`tools/vocab/registry_from_tape.py`
- 読む試験: `tests/c6/test_c6lib_scenes.py`・`tests/engine/experiment/test_cf33b_switch.py`・`tests/engine/memory/test_m0_cli.py`・`tests/engine/memory/test_m0_recall_equivalence.py`・`tests/engine/memory/test_m0_shown_recorded.py`・`tests/engine/memory/test_m0_store_schema.py`・`tests/engine/memory/test_m1_runs.py`・`tests/engine/memory/test_m2_cue.py`・`tests/engine/memory/test_mr65_grain_and_cli.py`・`tests/engine/multiday/test_md23_body_events.py`・`tests/engine/multiday/test_md23_resume.py`・`tests/engine/processes/test_rng_scheme_10c.py`・`tests/engine/tape_analysis.py`・`tests/engine/test_10a_review_fixes.py`・`tests/engine/test_activation_10e.py`・`tests/engine/test_env_and_sections_10f.py`・`tests/engine/test_fleet_wiring.py`・`tests/engine/test_llm_mock.py`・`tests/engine/test_memory_recall.py`・`tests/engine/test_response_delay.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_tape.py`・`tests/engine/test_tape_deferred.py`・`tests/engine/test_tape_wiring.py`・`tests/engine/test_undefined_action.py`・`tests/engine/test_version_bump_10e.py`・`tests/llm/test_fleet.py`
- 状態台帳の行
  - 持ち主 `bridge.tape`(`TapeWriter`)
    - `O87` TapeWriter の書き出し待ちの行と計数(挙動 no・復元 discardable) 道筋 `bridge.tape._arm_values`・`bridge.tape._blocks`・`bridge.tape._n_deferred`・`bridge.tape._n_written`・`bridge.tape._rows` 書ける系: close_final・decide・drain・llm_receive
- 決定の ID: 10-13b/§3・D-58・第 295
