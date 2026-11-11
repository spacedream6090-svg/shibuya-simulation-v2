# tests/engine/body

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 9 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../tests/engine/body/__init__.py)

(冒頭の説明なし)

## [body_fixtures.py](../../../../../../../tests/engine/body/body_fixtures.py)

第 3 期 3-5 の試験の共通の道具: 3-5 より前の式の写し(移しただけ=同じ値の物差し)・作り物の体の表・作り物のエネルギー。

- 公開の関数とクラス
  - `StubModel`(クラス): ``EnergyModel`` の 4 つの口だけ(METs と消費の式は energy.py と同じ形・METs の値は改訂版メッツ表の 4 値)。
  - `apply_update`(関数): ``resolve.advance_body`` の書き方の写し(作り物の表へ)。
  - `copy_registry`(関数)
  - `fake_registry`(関数)
  - `head_advance_body`(関数): HEAD の ``resolve.advance_body`` の本体(``with agents.writable()`` の中の文=配列へそのまま)。
  - `head_collapse`(関数): HEAD の ``SalientProcess._collapse_events`` の乱数の引き方(倒れる体の id の列)。
  - `head_felt`(関数): HEAD の ``EnvironmentProcess.step`` の体感温度(``R.set_thermal`` の丸めまで)。
  - `head_stage`(関数)
  - `stub_energy`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.change_detect`・`shibuya.foundation.time_consts`・`shibuya.world.body.energy`
- 読む試験: `tests/engine/body/test_body_reserve.py`・`tests/engine/body/test_body_same_values.py`

## [test_body_guard.py](../../../../../../../tests/engine/body/test_body_guard.py)

第 3 期 3-5: 体の層の守り(書く口は ``step``・``initial`` だけ・新しい書き手を作らない・持ち主の欄の守り)。

- 公開の関数とクラス
  - `test_callers_of_the_body_write_ports_are_not_more_than_head`(関数)
  - `test_negative_planted_writes_and_calls_are_found`(関数): 負の対照: 体の層の外から中身を書く・予約の列の書く口を呼ぶ・step を呼ぶ行を植えると見つかる。
  - `test_no_new_writer_of_the_body_columns`(関数)
  - `test_only_the_ports_write_the_body_layer`(関数)
  - `test_sweep_allocates_no_per_agent_arrays_and_reserve_does`(関数): 〔3-5 検収 M1〕腕 sweep(既定)は体ごとの予約の配列を作らない(状態台帳の行 BD の「腕 sweep: 計器だけ」)。
  - `test_the_body_layer_holds_copies_not_soa_views`(関数): 写し(引き直しの検出)は SoA の配列のビューを持たない(D ⑥ と同じ約束)。
  - `test_the_owner_refuses_rebinding_and_deleting`(関数)
  - `test_the_schedule_refuses_writes_outside_its_ports`(関数): 〔3-5 検収 L7〕予約の列の欄は書く口の外で付け替え・消去・配列の書きを断る(負の対照=書く口の中は書ける)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.systems.allow`・`shibuya.world.body.model`・`shibuya.world.body.schedule`・`tests/engine/ast_writers.py`

## [test_body_manifest.py](../../../../../../../tests/engine/body/test_body_manifest.py)

第 3 期 3-5: manifest の ``body``(持ち主・腕・予約の数・境目の数・一致の計器)と CLI の腕 ``--body-schedule``。

- 公開の関数とクラス
  - `test_arm_switch_reads_env_and_cli`(関数)
  - `test_manifest_body_keys_and_sections`(関数)
  - `test_manifest_fields_without_a_layer_are_null`(関数)
  - `test_the_arm_is_not_in_the_fingerprint_and_marks_the_run_kind`(関数)
  - `test_world_assets_reserve_equals_sweep_with_thermal_boundaries`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.run`・`shibuya.engine.run_kind`・`shibuya.foundation.manifest.sections`・`shibuya.world.body.model`・`shibuya.world.body.schedule`
- 決定の ID: 11-01・11-02r/§1・11-02r/§1 #7・11-03/§3

## [test_body_reserve.py](../../../../../../../tests/engine/body/test_body_reserve.py)

第 3 期 3-5 TM5 の予約の腕(``--body-schedule reserve``)=「全員を毎回見る版」(sweep)と一致すること(受入の条件)。

- 公開の関数とクラス
  - `test_activity_change_replans_the_reservation`(関数): 就寝で疲れ 0・空腹がいちばん上の段の体は予約なし → 起きると次の体の刻みに予約(活動の変更で引き直す)。
  - `test_felt_guard_refuses_a_table_that_disagrees_with_the_window`(関数): 守り: その日の表がいまの窓の値と違えば止める(予約の前提が崩れた)。
  - `test_felt_negative_control`(関数)
  - `test_felt_reserve_equals_sweep`(関数)
  - `test_negative_control_shifting_the_reservation`(関数): 負の対照: 予約の式を 1 刻み遅らせると値と境目の列が食い違う。早めても同じ(下界の予約=空振りして引き直す)。
  - `test_reserve_equals_sweep_with_outside_writers`(関数)
  - `test_resume_with_the_reserve_arm_equals_the_straight_run`(関数): 腕 sweep で日の途中と日の境目に保存した状態から腕 reserve で再開=通し(sweep)と同じ(予約の列は状態から引き直す)。
  - `test_run_day_reserve_equals_sweep`(関数)
- import している内部モジュール: `shibuya.engine.run`・`shibuya.world.body.energy`・`shibuya.world.body.model`・`shibuya.world.body.schedule`・`tests/engine/body/body_fixtures.py`

## [test_body_rules_sources.py](../../../../../../../tests/engine/body/test_body_rules_sources.py)

第 3 期 3-5: 体の規則の出典の欄(③ の 3 件に conf と出典・倒れる率は出典なし=expedient)とつなぎの台帳の行の結び。

- 公開の関数とクラス
  - `ledger`(関数)
  - `test_declaration_tables_are_one_to_one_with_ledger_rows`(関数)
  - `test_moved_items_left_the_old_headings`(関数)
  - `test_rules_cover_the_inventory_rows_with_conf_and_source`(関数)
  - `test_system1_rows_remove_at_the_spatial_stages`(関数)
- import している内部モジュール: `shibuya.engine.bridging.scan`・`shibuya.foundation.decl.bridging`・`shibuya.world.body.reactions`・`shibuya.world.body.rules`・`shibuya.world.body.schedule`

## [test_body_same_values.py](../../../../../../../tests/engine/body/test_body_same_values.py)

第 3 期 3-5: ③ の 3 件(D8 空腹と疲れ・A2 体感温度・D9 倒れる)と D18 を体の層へ移しただけ=同じ値(HEAD の式の写しと比べる)。

- 公開の関数とクラス
  - `test_collapse_draw_equals_head_on_the_same_stream`(関数)
  - `test_felt_temperature_equals_head`(関数)
  - `test_initial_values_equal_head`(関数)
  - `test_interoception_equals_head_over_a_day`(関数)
  - `test_moved_names_point_to_the_same_values`(関数): 前の場所の名(``resolve``・``environment``・``salient``)は体の層の値を写して出す(読み手の import は変えない)。
  - `test_negative_a_changed_rule_is_seen_by_the_ruler`(関数): 負の対照: 体の規則の値を 1 つ変えると HEAD の写しと食い違う(物差しが空回りしていない)。
  - `test_the_sweep_model_writes_the_same_as_the_pure_rule`(関数): ``BodyModel(arm="sweep").step`` は純関数の値をそのまま返す(計器を数えるだけ)。
- import している内部モジュール: `shibuya.engine.resolve`・`shibuya.foundation.rng`・`shibuya.world.body.model`・`shibuya.world.body.rules`・`shibuya.world.laws.environment`・`shibuya.world.laws.salient`・`tests/engine/body/body_fixtures.py`

## [test_meal_default_w17.py](../../../../../../../tests/engine/body/test_meal_default_w17.py)

〔小さな版上げ・回答 10-13b §7 の 2〕範囲外の人の既定の食事時刻と初期の空腹を W17 v2 の日課の分布(構築側)から。

- 公開の関数とクラス
  - `test_default_engine_never_opens_the_validation_anchor_files`(関数)
  - `test_draw_from_the_world_w17_matches_its_meal_rows_jsd`(関数)
  - `test_draw_is_deterministic_and_keyed_by_the_body`(関数)
  - `test_energy_source_names_no_validation_file`(関数): コードの読み口: 開く道筋に検証側の名が無い(錨の名は構築側だけ)。〔第 2 部〕旧値の腕は消した=渡すと止まる。
  - `test_from_weekly_uses_the_day_rows_then_all_days_then_frozen`(関数)
  - `test_frozen_draw_matches_the_frozen_histogram`(関数)
  - `test_frozen_table_is_pinned_and_read_only`(関数)
  - `test_initial_hunger_comes_from_the_previous_dinner_and_stays_in_range`(関数)
  - `test_manifest_has_the_source_and_the_share_gauge`(関数)
  - `test_negative_control_a_planted_read_is_caught`(関数)
  - `test_out_of_area_defaults_are_drawn_per_body_and_rows_are_kept`(関数)
  - `test_removed_switch_env_and_cli_flag_stop`(関数): 〔第 2 部〕消した切替口: 環境変数 SHIBUYA_MEAL_DEFAULT を与えると読み込みで止まる・CLI の --meal-default は無い。
  - `test_two_day_run_resume_equals_straight`(関数)
  - `test_w17_default_times_move_with_the_seed`(関数): 〔検収 L3〕既定の時刻は seed で変わる(体ごとの引き)。〔第 2 部〕seed に依らない 1 つの値の旧値の腕は消した。
  - `test_world_two_day_resume_equals_straight`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.run`・`shibuya.world.body.energy`・`shibuya.world.body.rules`・`shibuya.world.facts.weekly_reader`
- 環境変数: `SHIBUYA_MEAL_DEFAULT`・`os.environ` をまるごと使う
- 決定の ID: 10-13b/§7

## [test_system1_placeholders.py](../../../../../../../tests/engine/body/test_system1_placeholders.py)

第 3 期 3-5: 器だけの 3 件(ロンバード効果・混雑の中の歩き方と避け方・大きな音に注意が向く)=欄と口だけ・値は空。

- 公開の関数とクラス
  - `test_loud_sound_is_a_nearby_change_kind_and_the_percept_shape_is_unchanged`(関数)
  - `test_noise_reading_port_reads_w10_only`(関数)
  - `test_percepts_of_a_run_keep_the_fields_empty`(関数): 合成の世界のランで描いた知覚の事実(系 decide が ``TickScratch.percepts`` に書く)の器の欄は None のまま。
  - `test_ports_return_empty_values`(関数)
- import している内部モジュール: `shibuya.engine.run`・`shibuya.engine.systems.conductor`・`shibuya.foundation.ports.percept`・`shibuya.world.body.reactions`・`shibuya.world.model.state`
