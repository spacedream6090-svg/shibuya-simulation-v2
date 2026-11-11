# tests/engine/multiday

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 6 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../tests/engine/multiday/__init__.py)

(冒頭の説明なし)

## [_md.py](../../../../../../../tests/engine/multiday/_md.py)

第 2 期 2-3 の試験の共通(合成の世界の小さなランの設定・腕の切替・ランの記録と器を控える・道具の読み込み)。

- 公開の関数とクラス
  - `Capture`(クラス): 器に口を置く所を包み、ランの器と記録を控える(戻り値は変えない)。
  - `arms`(関数): 腕を一時的に選ぶ(組み立てが読む)。〔第346〕近接は常に distance(切替口 cell は消した)。
  - `tool`(関数): 記録の道具(``md23/tools/multiday_md23.py``)を読み込む。
- import している内部モジュール: `shibuya.economy.stage2_bind`・`shibuya.mind.memory.memory_store`
- 読む試験: `tests/engine/memory/test_mr65_grain_and_cli.py`・`tests/engine/multiday/test_md23_body_events.py`・`tests/engine/multiday/test_md23_resume.py`・`tests/engine/multiday/test_md23_tool.py`・`tests/engine/multiday/test_md23_w9_window.py`
- 決定の ID: 第 346

## [test_md23_body_events.py](../../../../../../../tests/engine/multiday/test_md23_body_events.py)

第 2 期 2-3: 体の出来事を出来事の記録(1-3)に載せる(腕 ``--memory-store events`` のときだけ)。

- 公開の関数とクラス
  - `runs`(関数)
  - `test_arm_on_writes_the_body_events`(関数)
  - `test_body_link_fields_cannot_be_rebound`(関数): 〔検収 L4〕口の欄(記録・看板の印)は組み立ての 1 回だけ=付け替えと消去は落ちる(負の対照)。
  - `test_causes_are_the_call_or_a_body_process`(関数)
  - `test_conversation_end_rows_per_participant`(関数)
  - `test_default_run_has_no_body_events_and_no_store`(関数)
  - `test_legacy_path_with_the_log_off_is_the_1_6_form`(関数): 〔検収 L1〕腕 events+記録 off(器だけの道)=1-6 と同じ legacy の行(目印 −1−番地)・final とテープの既存の列も同じ。
  - `test_m0l_is_an_arm_row_present_only_with_the_store`(関数)
  - `test_notice_and_signage_are_perception_events`(関数)
  - `test_pointer_beyond_the_retention_window_recalls_only_the_summary`(関数): 〔親の判断 M3〕目印の先が記録の保持窓(7 日)の外に出た行=要旨(注釈と強さ)だけで想起に使う・本文は無い。
  - `test_rebuild_keeps_the_log_pointer_from_the_saved_seq`(関数): 再開: 作り直しは行 M0L(記録の seq)から目印と出どころを戻す(記録の行は再開のランに無くても目印は残る)。
  - `test_recall_candidates_are_the_same_as_the_legacy_form`(関数)
  - `test_remember_takes_only_ids_in_the_log`(関数)
  - `test_signboard_rows_of_the_1_7_arm_are_reused`(関数)
  - `test_store_pointers_are_log_events`(関数)
  - `test_word_tables_agree_with_the_memory_and_the_vocab`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.events.body`・`shibuya.engine.run`・`shibuya.engine.tools.record`・`shibuya.foundation.journal.log`・`shibuya.foundation.time_consts`・`shibuya.foundation.vocab.events`・`shibuya.mind.memory.memory`・`shibuya.mind.memory.memory_store`・`shibuya.runtime.inference.tape`・`shibuya.runtime.state.ledger`・`tests/engine/multiday/_md.py`

## [test_md23_resume.py](../../../../../../../tests/engine/multiday/test_md23_resume.py)

第 2 期 2-3: 複数日のランの日の境目で保存 → 翌日を再開=通しと同じ(10d の再開を複数日の腕の組で)。

- 公開の関数とクラス
  - `test_synthetic_two_days_resume_at_the_day_boundary`(関数)
  - `test_world_two_days_resume_default_and_arm_d`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.run`・`shibuya.foundation.time_consts`・`shibuya.runtime.inference.tape`・`tests/engine/multiday/_md.py`

## [test_md23_tool.py](../../../../../../../tests/engine/multiday/test_md23_tool.py)

第 2 期 2-3: 複数日の計器の道具(``md23/tools/multiday_md23.py``)の単体と、実データの 5 日(``slow``・1 本=既定・seed 1)。

- 公開の関数とクラス
  - `test_day_rows_from_a_synthetic_three_day_record`(関数)
  - `test_days_to_full`(関数)
  - `test_the_tool_collects_three_synthetic_days`(関数)
  - `test_world_five_days_default`(関数): 実データの 5 日(月〜金・5,000 体・seed 1・既定の腕=土台 v3_mem_rel・開始日の検査 A1-3 は外さない=親の判断 M1)。
- import している内部モジュール: `shibuya.foundation.time_consts`・`tests/engine/multiday/_md.py`

## [test_md23_w9_window.py](../../../../../../../tests/engine/multiday/test_md23_w9_window.py)

第 2 期 2-3: 影の日付(W9)を 7 日の窓(2026-07-13 月〜07-19 日)に広げた(構築側・活性化は 2-4)。

- 公開の関数とクラス
  - `test_bridging_rows_after_2_3`(関数)
  - `test_shadow_dates_cover_the_seven_day_window`(関数)
  - `test_stage_asset_has_the_window_and_the_fallback_is_used_only_outside`(関数)
- import している内部モジュール: `shibuya.build.vis.w9_shadow`・`shibuya.foundation.decl.bridging`・`shibuya.world.laws.environment`・`tests/engine/multiday/_md.py`
- 環境変数: `SHIBUYA_SPACE`
- 決定の ID: 第 334
