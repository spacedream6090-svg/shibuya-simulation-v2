# src/shibuya/runtime/inference

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 2 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/runtime/inference/__init__.py)

(冒頭の説明なし)

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
- 呼び手: `shibuya.engine.experiment.branch`・`shibuya.engine.llm_bridge`・`shibuya.engine.run`・`shibuya.runtime.systems.assemble`・`tools/c6/ablation1_fixed_vs_ranking.py`・`tools/c6/c6lib.py`・`tools/c6/format_role_rates.py`・`tools/c6/t6_bit_reproduce.py`・`tools/c6/t7_distribution.py`・`tools/c8/ablation_runner.py`・`tools/fig/fig_ab7_actions.py`・`tools/fig/fig_ab7c_vocab.py`・`tools/fig/fig_d91_ride_chain.py`・`tools/vocab/registry_from_tape.py`
- 読む試験: `tests/c6/test_c6lib_scenes.py`・`tests/engine/experiment/test_cf33b_switch.py`・`tests/engine/memory/test_m0_cli.py`・`tests/engine/memory/test_m0_recall_equivalence.py`・`tests/engine/memory/test_m0_shown_recorded.py`・`tests/engine/memory/test_m0_store_schema.py`・`tests/engine/memory/test_m1_runs.py`・`tests/engine/memory/test_m2_cue.py`・`tests/engine/memory/test_mr65_grain_and_cli.py`・`tests/engine/multiday/test_md23_body_events.py`・`tests/engine/multiday/test_md23_resume.py`・`tests/engine/processes/test_rng_scheme_10c.py`・`tests/engine/tape_analysis.py`・`tests/engine/test_10a_review_fixes.py`・`tests/engine/test_activation_10e.py`・`tests/engine/test_env_and_sections_10f.py`・`tests/engine/test_fleet_wiring.py`・`tests/engine/test_llm_mock.py`・`tests/engine/test_memory_recall.py`・`tests/engine/test_response_delay.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_tape.py`・`tests/engine/test_tape_deferred.py`・`tests/engine/test_tape_wiring.py`・`tests/engine/test_undefined_action.py`・`tests/engine/test_version_bump_10e.py`・`tests/llm/test_fleet.py`
- 状態台帳の行
  - 持ち主 `bridge.tape`(`TapeWriter`)
    - `O87` TapeWriter の書き出し待ちの行と計数(挙動 no・復元 discardable) 道筋 `bridge.tape._arm_values`・`bridge.tape._blocks`・`bridge.tape._n_deferred`・`bridge.tape._n_written`・`bridge.tape._rows` 書ける系: close_final・decide・drain・llm_receive
- 決定の ID: 10-13b/§3・D-58・第 295
