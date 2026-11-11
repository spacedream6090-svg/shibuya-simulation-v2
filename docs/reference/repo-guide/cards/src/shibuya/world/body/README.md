# src/shibuya/world/body

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 6 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/world/body/__init__.py)

(冒頭の説明なし)

- 読む試験(道筋で): `tests/tools/test_pkgmove.py`

## [energy.py](../../../../../../../../src/shibuya/world/body/energy.py)

engine.energy — 体のエネルギー収支(5 段目 5a・D-118 K1〜K9・第291)。

- 公開の関数とクラス
  - `EnergyLayer`(クラス): ラン 1 本ぶんの エネルギー収支(模型+範囲外の予定+診断)。
  - `EnergyModel`(クラス): 錨から組んだ表と式(純関数)。書き込みはしない。
  - `HomeMeals`(クラス): **第2波 §2B 項 2(Q35 (a))** 範囲内の自宅の食事行=「予定の実行」(``--home-meal plan``)。
  - `MealStartDistribution`(クラス): **既定の食事時刻の分布**(腕 ``w17``・回答 10-13b §7 の 2)。時間帯(朝・昼・夕)ごとに、W17 の食事の行の開始の
  - `OutOfAreaMeals`(クラス): 範囲外の食事の予定(K9 (a))。起動時に 1 日ぶんの (tick, 体, 時間帯) を組む。
  - `anchors_paths`(関数): エンジンが読む錨のファイル=構築側の 1 本だけ(〔第 2 部〕検証側を読む旧値の腕は消した)。
  - `anchors_rel`(関数): manifest の ``energy.anchors`` の道筋。
  - `check_energy_rate`(関数)
  - `check_home_meal`(関数)
  - `check_hunger_model`(関数)
  - `check_meal_default`(関数)
  - `check_meal_sleep_defer`(関数)
  - `load_anchors`(関数): 錨の追跡ファイルを読む → ``(辞書, md5)``。
  - `meal_default`(関数): 既定の食事時刻の出どころ(``w17`` だけ=〔第 2 部〕旧値の腕と切替口は消した)。
  - `meal_start_distribution`(関数): 組み立ての口: 週次表(全員)から分布を作る(週次表が無ければ凍結の表)。
  - `minute_slot`(関数): その日の分 → 時間帯(朝 0 / 昼 1 / 夕 2 / その他 3)。
  - `w17_wake_minute`(関数): 体 ``agent`` がその日の ``minute`` に W17 の「就寝」の行の中に居れば、**起床の分**
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.calendar`・`shibuya.foundation.paths`・`shibuya.foundation.rng`・`shibuya.foundation.time_consts`・`shibuya.world.facts.weekly_reader`
- 呼び手: `shibuya.cli`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.engine.systems.body`・`shibuya.engine.systems.build`・`shibuya.world.body.rules`・`shibuya.world.body.schedule`
- 読む試験: `tests/engine/body/body_fixtures.py`・`tests/engine/body/test_body_reserve.py`・`tests/engine/body/test_meal_default_w17.py`・`tests/engine/state/test_move_prep_stage2.py`・`tests/engine/test_10a_review_fixes.py`・`tests/engine/test_energy_balance.py`・`tests/engine/test_meal_bundle_2b.py`・`tests/engine/test_meal_gate_per_hour.py`・`tests/engine/test_sim_time_T.py`
- 読む試験(道筋で): `tests/engine/state/test_names_frozen.py`・`tests/tools/test_pkgmove.py`
- 状態台帳の行
  - 持ち主 `energy.home_meals`(`HomeMeals`)
    - `O32` HomeMeals の予定 tick・agent・slot・_start・home_cell(挙動 no・復元 derivable) 道筋 `energy.home_meals._start`・`energy.home_meals.agent`・`energy.home_meals.home_cell`・`energy.home_meals.slot`・`energy.home_meals.tick` 書ける系: body・home_meal
    - `O33` HomeMeals n_not_home・n_asleep・OutOfAreaMeals の計数 n_armed ほか(挙動 diag・復元 discardable) 道筋 `energy.home_meals.n_asleep`・`energy.home_meals.n_not_home` 書ける系: body・energy_after・home_meal
  - 持ち主 `energy.out_of_area`(`OutOfAreaMeals`)
    - `O29` OutOfAreaMeals の予定 tick・agent・slot・from_row・_start(挙動 no・復元 derivable) 道筋 `energy.out_of_area._start`・`energy.out_of_area.agent`・`energy.out_of_area.from_row`・`energy.out_of_area.slot`・`energy.out_of_area.tick` 書ける系: body・home_meal・phase_c
    - `O30` OutOfAreaMeals の遅らせの表 d_agent・d_slot・d_arm_tick・d_eat_tick・d_wake_min(挙動 no・復元 derivable) 道筋 `energy.out_of_area.d_agent`・`energy.out_of_area.d_arm_tick`・`energy.out_of_area.d_eat_tick`・`energy.out_of_area.d_slot`・`energy.out_of_area.d_wake_min` 書ける系: body・home_meal
    - `O31` OutOfAreaMeals d_armed(就寝中の食事を起床時に回す印)(挙動 behavior・復元 required) 道筋 `energy.out_of_area.d_armed` 書ける系: body・home_meal
    - `O33` HomeMeals n_not_home・n_asleep・OutOfAreaMeals の計数 n_armed ほか(挙動 diag・復元 discardable) 道筋 `energy.out_of_area.n_armed`・`energy.out_of_area.n_deferred_not_out`・`energy.out_of_area.n_skipped_past_window` 書ける系: body・energy_after・home_meal
  - 持ち主 `energy`(`EnergyLayer`)
    - `O27` EnergyLayer bmr(挙動 behavior・復元 derivable) 道筋 `energy.bmr` 書ける系: body・home_meal・phase_c
    - `O28` EnergyLayer meal_bits・n_meals・n_snacks・counts・intake_kcal・meal_start_*・stage_ticks*(挙動 diag・復元 discardable) 道筋 `energy.ate_default`・`energy.counts`・`energy.intake_kcal`・`energy.meal_bits`・`energy.meal_start_home`・`energy.meal_start_in`・`energy.meal_start_out`・`energy.n_meals`・`energy.n_snacks`・`energy.snack_start`・`energy.stage_ticks`・`energy.stage_ticks_awake_by_hour` 書ける系: body・energy_after・home_meal・phase_c
- 環境変数: `SHIBUYA_MEAL_DEFAULT`
- 決定の ID: 10-03/§7-1・10-13b/§7・D-111・D-118・第 291

## [model.py](../../../../../../../../src/shibuya/world/body/model.py)

engine.body.model — 本人の体の層 ``BodyModel``(状態台帳の外の状態の持ち主 ``body``=行 ``BD``・第 3 期 3-5)。

- 公開の関数とクラス
  - `BodyModel`(クラス): 本人の体の層(持ち主 ``body``)。``arm``=TM5 の腕(``sweep``/``reserve``)・``n``=体の数・``gauge``=段の境目の計器を
  - `gauge_on`(関数): 段の境目の計器を数えるか(環境変数 ``SHIBUYA_BODY_BOUNDARY_GAUGE`` が ``1``)。組み立てのときに読む。
  - `manifest_fields`(関数): manifest の ``body``(持ち主・腕・規則の出典の表・器だけの 3 件=設定/予約と段の境目の計器=観測)。
- import している内部モジュール: `shibuya.foundation.time_consts`・`shibuya.world.body.reactions`・`shibuya.world.body.rules`・`shibuya.world.body.schedule`
- 呼び手: `shibuya.engine.run`・`shibuya.engine.systems.build`・`shibuya.world.laws.environment`・`shibuya.world.laws.salient`
- 読む試験: `tests/engine/body/test_body_guard.py`・`tests/engine/body/test_body_manifest.py`・`tests/engine/body/test_body_reserve.py`・`tests/engine/body/test_body_same_values.py`
- 状態台帳の行
  - 持ち主 `body`(`BodyModel`)
    - `BD` BodyModel(本人の体の層の段の境目の計器と TM5 の予約の列・第 3 期 3-5)(挙動 diag・復元 discardable) 道筋 `body._body_meter`・`body._reservations` 書ける系: body・world
- 環境変数: `SHIBUYA_BODY_BOUNDARY_GAUGE`

## [reactions.py](../../../../../../../../src/shibuya/world/body/reactions.py)

engine.body.system1 — 意図しない System 1 の反応の**器だけ**の 3 件(第 3 期 3-5・値は空)。

- 公開の関数とクラス
  - `System1Slot`(クラス): 器 1 つ(id・中身・口・欄・値が入る段・つなぎの台帳の行)。
  - `crowd_gait`(関数): 混雑の中の歩き方と避け方の口。**値は空**(None=空間の段 1 の物理で入る)。
  - `loud_sound_notice`(関数): 大きな音に注意が向く口(知覚の事実 ``Percept.nearby_change`` の種類 ``loud_sound``)。**値は空**(None)。
  - `manifest_rows`(関数): manifest の ``body.system1``(器の一覧・設定)。
  - `noise_stage_at`(関数): W10 の騒音の段の読みの口(``World.noise_stage_for_tick`` の値をセルで引く・読むだけ)。舞台の外の体は 0。
  - `speech_loudness`(関数): ロンバード効果の口: 周りの騒音の段 → 話す大きさ。**値は空**(None=仕組みがまだ無い・空間の段 3)。
- import している内部モジュール: `shibuya.foundation.ports.percept`
- 呼び手: `shibuya.engine.contact.layer`・`shibuya.world.body.model`
- 読む試験: `tests/engine/body/test_body_rules_sources.py`・`tests/engine/body/test_system1_placeholders.py`
- 決定の ID: 10-12・10-12/§1-5

## [rules.py](../../../../../../../../src/shibuya/world/body/rules.py)

engine.body.rules — 本人の体の規則(③ 意図しない体と System 1・第 3 期 3-5)の値と純関数。

- 公開の関数とクラス
  - `BodyInitial`(クラス): 刻み 0 の体の状態(``uint8``・``int8``・``float32`` の配列)。エネルギー収支の欄はそのランだけ(ほかは None)。
  - `BodyRule`(クラス): 本人の体の規則 1 つの出典の欄(conf=mechanism/expedient・出典・つなぎの台帳の行)。
  - `InteroUpdate`(クラス): 体の刻み 1 回の書き込み(``resolve.advance_body`` が SoA に写す)。
  - `collapse_draw`(関数): この刻みに倒れる体(id の昇順・``int64``)。3-5 より前の ``SalientProcess._collapse_events`` と同じ乱数の引き方
  - `energy_spent`(関数): 1 刻みの消費(``float32``・全員)=``EnergyModel.expenditure(eer, mets_of(活動), bmr)``(式は energy.py のまま)。
  - `fatigue_after`(関数): 疲れの規則(体の刻みの +1・就寝中の −2・休みの −1)。3-5 より前の ``advance_body`` と同じ値(``uint8``)。
  - `felt_cells`(関数): その 5 分の窓のセルごとの体感温度(``uint8``・長さ ``n_cells + 1``=末尾は舞台の外の体の値)。
  - `felt_columns`(関数): 体のセル → :func:`felt_cells` の列(舞台の中のセルはそのセル・外=−1 や範囲外は末尾の列)。
  - `felt_temperature`(関数): 全員の体感温度(``uint8``)=:func:`felt_cells` を体のセルで引いた値(全員を見る版)。
  - `hunger_copy_of`(関数): 食後の消費 → 空腹の写し(語の段 1/5/8/10・``uint8``)。
  - `hunger_v1_after`(関数): 空腹(v1)の規則(体の刻みの +1・上限 10)。
  - `initial_energy_values`(関数): エネルギー収支のランの刻み 0 の食後の消費・空腹の写しと段(3-5 より前の ``resolve.initialize_energy`` と同じ値)。
  - `initial_values`(関数): 刻み 0 の空腹・疲れ・暑さと段(3-5 より前の ``resolve.initialize`` と同じ値)。
  - `interoception`(関数): 全員を見る版(sweep)の体の刻み 1 回。3-5 より前の ``resolve.advance_body`` と同じ値。
  - `resting`(関数): 「休んでいる体」=活動の種別が 在店/その場 で持続中・移動/乗車/就寝中でない(二層の段 2)。
  - `rule`(関数): 規則の id → 行。
  - `rule_steps`(関数): ``now`` が体の刻み(空腹+1・疲れ+1・就寝の回復)か・休みの回復の刻みか。
  - `stage_values`(関数): 内受容の値 → 段(``INTERO_UP_EDGES`` を何本越えたか・``int8``)。
  - `steps_to_hunger_edge`(関数): 今の食後の消費 ``since`` から、1 刻みに ``spent`` ずつ足して次の語の段の境目を越えるまでの刻みの数の見込み
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.change_detect`・`shibuya.foundation.time_consts`・`shibuya.world.body.energy`
- 呼び手: `shibuya.engine.resolve`・`shibuya.world.body.model`・`shibuya.world.body.schedule`・`shibuya.world.laws.environment`・`shibuya.world.laws.salient`
- 読む試験: `tests/engine/body/test_body_rules_sources.py`・`tests/engine/body/test_body_same_values.py`・`tests/engine/body/test_meal_default_w17.py`
- 読む試験(道筋で): `tests/tools/test_pkgmove.py`
- 決定の ID: 10-12・10-12/§1-5・10-13b/§7・11-01・D-118・第 275

## [schedule.py](../../../../../../../../src/shibuya/world/body/schedule.py)

engine.body.schedule — TM5「次に段階の境目を越える時刻を予約」の口(第 3 期 3-5・腕 ``--body-schedule``)。

- 公開の関数とクラス
  - `BodySchedule`(クラス): 体の層の予約の列(状態台帳の行 ``BD`` の中身)。
  - `arm`(関数): いまの腕(``sweep``=既定・``reserve``=TM5 の予約)。組み立てのときに読む。
  - `chain_digest`(関数): 段の境目の列の鎖のハッシュ(``sha256(前 ‖ 刻み ‖ 種類 ‖ 体 ‖ 前の値 ‖ 後の値)``・体は昇順)。
  - `next_felt_frames`(関数): 窓 ``frame`` の次に、列 ``cols`` の体感温度が変わる窓(``int64``・その日の中に無ければ :data:`NEVER`)。
  - `next_intero_steps`(関数): 規則に通した直後(刻み ``now``)の値から、次に空腹か疲れが変わりうる最初の刻み(``int64``・無ければ :data:`NEVER`)。
  - `set_arm`(関数): 腕を選ぶ(CLI ``--body-schedule``・試験の切替口)。組み立ての時に読む(ランの途中で変えても、そのランは変わらない)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.foundation.queues.scheduler`・`shibuya.world.body.energy`・`shibuya.world.body.rules`
- 呼び手: `shibuya.cli`・`shibuya.world.body.model`
- 読む試験: `tests/engine/body/test_body_guard.py`・`tests/engine/body/test_body_manifest.py`・`tests/engine/body/test_body_reserve.py`・`tests/engine/body/test_body_rules_sources.py`
- 読む試験(道筋で): `tests/engine/systems/test_stage_a_guard.py`
- 環境変数: `SHIBUYA_BODY_SCHEDULE`
- 決定の ID: 10-12・10-12/§4-2
