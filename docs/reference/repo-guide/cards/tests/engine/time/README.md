# tests/engine/time

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 8 本・その他 3 本(このディレクトリの直下)

その他のファイル: `manifest_keys_frozen.json`・`tick_word_allow.json`・`time_literal_allow.json`

## [__init__.py](../../../../../../../tests/engine/time/__init__.py)

(冒頭の説明なし)

- 読む試験: `tests/engine/test_c9b_targets_attention.py`・`tests/engine/test_change_detect_p6.py`・`tests/engine/test_fleet_wiring.py`・`tests/engine/test_geometry_c9.py`・`tests/engine/test_ledger_wiring.py`・`tests/engine/test_scheduler_p3.py`・`tests/engine/test_state_format_10f.py`

## [test_t0_literal_count.py](../../../../../../../tests/engine/time/test_t0_literal_count.py)

第 1 期 1-1 時計 T0: ``src/shibuya`` に時間の直書きが残っていない(AST で数える・残すものは allow の表に理由つき)。

- 公開の関数とクラス
  - `scan_source`(関数): ``(行, 種類)`` の一覧。種類は ``lit 1440`` や ``// 60`` の形。
  - `scan_tree`(関数): ``{"相対パス:行": [種類, …]}``(``base`` からの相対パス)。
  - `test_allow_table_has_reasons_and_no_stale_rows`(関数)
  - `test_negative_control_detects_every_form`(関数): 負の対照: 仮のファイルに直書きを置くと、形ごとに見つかる(数え方が空回りしていない)。
  - `test_no_time_literals_outside_the_allow_table`(関数)
  - `test_time_consts_module_itself_has_no_hits`(関数)

## [test_t0_no_tick_word.py](../../../../../../../tests/engine/time/test_t0_no_tick_word.py)

第 1 期 1-1 時計 T0: 「tick」の語(用語集 :165・:208-209=使わない。「刻み」「計算のまとめ」)。

- 公開の関数とクラス
  - `bare_word_lines`(関数): 注釈と docstring の行のうち、引用(バッククォート)の外に「tick」がある行。
  - `identifiers`(関数): 識別子(名・属性・関数とクラスの名・引数・キーワード引数・import の名・global/nonlocal)のうち「tick」を含むもの。
  - `test_allow_table_has_reasons_and_no_stale_names`(関数)
  - `test_kept_names_include_the_hash_and_interface_names`(関数): 変えない名(1-0 の規則)が理由つきで載っている(例: 状態台帳の道筋・manifest の欄・CLI の引数・テープの列)。
  - `test_negative_control_identifiers`(関数)
  - `test_negative_control_words`(関数)
  - `test_no_bare_word_in_comments_and_docstrings_of_core_and_systems`(関数)
  - `test_no_new_identifier_with_the_word`(関数)
  - `tree_identifiers`(関数)
- import している内部モジュール: `shibuya.engine.systems.table`・`shibuya.foundation.time_consts`・`tests/_places.py`

## [test_t0_rng_key.py](../../../../../../../tests/engine/time/test_t0_rng_key.py)

第 1 期 1-1 時計 T0(TM7 (d) の準備): ``rng.time_key_from_t_ns`` は ``run_tick_key`` と同じ鍵の値(全刻み・2 日ぶん)。〔v3-0a 案 A(指示書 11-04 §2-1)〕呼び手は棚卸し §1-1 の 18 か所だけ(``test_callers_are_the_plan_a_sites``)。``rng.key_time_from_t_ns`` は今まで材料に入れていた刻みの番号と同じ整数(各か所の同値は ``test_v30a_key_sites.py``)。

- 公開の関数とクラス
  - `test_bad_width`(関数)
  - `test_callers_are_the_plan_a_sites`(関数): 〔v3-0a 案 A〕呼び手は棚卸し §1-1 の 18 か所だけ(足すと落ちる・消しても落ちる)。
  - `test_inside_a_step_maps_to_the_step_that_contains_it`(関数)
  - `test_key_time_is_the_step_number`(関数): 〔v3-0a 案 A〕``key_time_from_t_ns`` は刻みの頭の時刻から今の刻みの番号を返す(全刻み・2 日ぶん・ほかの幅・刻みの中は床)。
  - `test_other_widths`(関数)
  - `test_same_key_for_every_step_of_two_days`(関数)
- import している内部モジュール: `shibuya.engine.systems.boxes`・`shibuya.foundation.rng`・`shibuya.foundation.time_consts`
- 決定の ID: 11-04/§2-1

## [test_t0_tickctx_equivalence.py](../../../../../../../tests/engine/time/test_t0_tickctx_equivalence.py)

第 1 期 1-1 時計 T0: ``TickCtx`` の ``t_ns``・``tod_s`` と 1-0 の ``T``・``td``・``day`` の同値(全刻み・2 日ぶん)と、進行役がランの設定の幅を渡していること。

- 公開の関数とクラス
  - `test_all_steps_of_two_days`(関数)
  - `test_default_width_and_the_old_call_form`(関数): 1-0 の呼び口 ``TickCtx.of(T, tpd)`` は残る(幅の既定は 60 秒=``STEP_SECONDS``)。1-0 の欄の値は前と同じ。
  - `test_other_widths_keep_the_relations`(関数)
  - `test_the_conductor_passes_the_run_width`(関数): 進行役(``conductor``)は ``RunConfig.tick_seconds`` を幅として渡す(合成の世界・20 体・30 刻み)。
- import している内部モジュール: `shibuya.engine.run`・`shibuya.engine.systems.boxes`・`shibuya.foundation.time_consts`・`shibuya.foundation.types`

## [test_t0_time_consts.py](../../../../../../../tests/engine/time/test_t0_time_consts.py)

第 1 期 1-1 時計 T0: 時間の定数の値と関係・換算の関数・旧い名との同値(``core.time_consts``)。

- 公開の関数とクラス
  - `test_conversions_reject_bad_width`(関数)
  - `test_conversions_reject_non_integers`(関数)
  - `test_doctests`(関数)
  - `test_module_level_aliases_elsewhere_are_the_same_value`(関数): 置き換えで再輸出にした各モジュールの ``MINUTES_PER_DAY`` ほか(読み手が名で引く)は同じ値。
  - `test_old_names_are_the_same_values`(関数): ``core.types`` の旧い名は残し、値は新しい定数と同じ(再輸出か同じ値の別名)。
  - `test_relations`(関数)
  - `test_seconds_to_steps_rounding_rule`(関数): 丸めの規則=床(その秒を含む刻み)。整数だけを受ける。
  - `test_time_consts_imports_only_the_standard_library`(関数): 層契約: 標準ライブラリだけ(core の最下層=誰からでも import できる)。
  - `test_values`(関数)
- import している内部モジュール: `shibuya.act.activity`・`shibuya.engine.growth_decl`・`shibuya.foundation.growth`・`shibuya.foundation.queues.scheduler`・`shibuya.foundation.time_consts`・`shibuya.foundation.types`・`shibuya.world.facts.weekly_reader`・`shibuya.world.laws.civic`・`shibuya.world.laws.goods_flow`・`shibuya.world.laws.logistics`・`shibuya.world.laws.opening`・`shibuya.world.ledger.actual_log`

## [test_t0_tm9_fields.py](../../../../../../../tests/engine/time/test_t0_tm9_fields.py)

第 1 期 1-1 時計 T0(TM9・GPU 無しの欄・10f と一体): manifest と日次の記録に「判断モデルと LLM を分けた呼び出し数」「時計の種類と幅」「つなぎの台帳の数」を足した。欄が増えるだけ(既存の欄の名・順・値は変えない)。

- 公開の関数とクラス
  - `test_daily_llm_calls_match_the_per_step_diagnostics`(関数): 日次の LLM の数=診断の行の ``calls`` の日ごとの和(別の数え方と突き合わせる)。
  - `test_daily_records_have_tm9_and_the_days_add_up`(関数)
  - `test_manifest_keys_match_the_frozen_list`(関数)
  - `test_manifest_tm9_values`(関数)
  - `test_resume_mid_day_counts_only_this_run`(関数): 再開したランの日次の LLM は再開した時刻からの分。止めたランの残り+再開したランの分=通しの 2 日目。
  - `test_sections_of_tm9_fields`(関数)
  - `test_tm9_fields_do_not_feed_the_final_hash`(関数): 欄の値(時計の種類)を変えても final と呼数は同じ(TM9 の欄は記録だけ)。
  - `two_days`(関数)
- import している内部モジュール: `shibuya.engine.run`・`shibuya.engine.systems.state_io`・`shibuya.foundation.decl.bridging`・`shibuya.foundation.manifest.sections`・`shibuya.foundation.time_consts`
- 決定の ID: 11-01・11-02r/§1・11-02r/§1 #7・11-03/§3

## [test_v30a_key_sites.py](../../../../../../../tests/engine/time/test_v30a_key_sites.py)

〔v3-0a 案 A(指示書 11-04 §2-1)〕棚卸し §1-1 の 18 か所の同値: 世界の時刻 ``t_ns`` から作った整数(乱数の鍵・呼びのid・時間帯)が、書き換えの前に材料に入れていた刻みの番号から作った値と同じ(日をまたぐ境・2 日目・再開の後)。

- 公開の関数とクラス
  - `spy`(関数)
  - `test_arm_port_presents_and_draws_as_before`(関数): #5〜#12: 腕の口の並べ替え(``choose``)と選びの乱数(``_draw``)の鍵。
  - `test_base_port_presents_and_chooses_as_before`(関数): #3: 判断の口の基底の並べ替え(``present_rng``)の鍵。
  - `test_call_ids_and_time_bucket_from_time_are_the_old_ones`(関数)
  - `test_contact_calendars_and_port_runs_across_the_day_and_resume`(関数): 連絡(習慣 on)・カレンダー 2・3・判断の口 port の腕のラン(日 → 月・TPD+300 で止めて再開)。
  - `test_contact_habit_key_and_call_id_are_the_old_ones`(関数)
  - `test_duties_run_across_the_day_and_resume`(関数): 店の仕事の腕のラン(TPD+300 で止めて再開)。
  - `test_fleet_call_ids_and_time_bucket_are_the_old_ones`(関数): #1・#2: 艦隊の道で発射した呼び(偽の艦隊・合成の世界)の id と時間帯が旧の形(``f"{T}:{体}:{級}"``・``T // 5``)。
  - `test_old_copy_only_swaps_the_key`(関数): (この試験の道具の検査)旧の写しは鍵の口だけを差し替える(元の口は変えない)。
  - `test_port_key_from_time_is_the_old_key`(関数)
- import している内部モジュール: `shibuya.engine.calendar2.layer`・`shibuya.engine.calendar3.layer`・`shibuya.engine.contact.layer`・`shibuya.engine.duties.layer`・`shibuya.engine.run`・`shibuya.engine.systems.boxes`・`shibuya.foundation.ports.decision`・`shibuya.foundation.rng`・`shibuya.foundation.time_consts`・`shibuya.llm.fleet`・`shibuya.mind.judge.decision.layer`・`shibuya.mind.plan.calendar2_port`・`shibuya.mind.plan.calendar3_port`・`shibuya.mind.plan.contact_habit`・`shibuya.mind.plan.contact_port`・`shibuya.mind.plan.duties_port`・`tests/engine/calendar3/_ca3.py`・`tests/engine/contact/_c2.py`・`tests/engine/decision/_j0.py`・`tests/engine/duties/_du.py`・`tests/engine/test_fleet_wiring.py`・`tests/llm/test_fleet.py`
- 決定の ID: 11-04/§2-1
