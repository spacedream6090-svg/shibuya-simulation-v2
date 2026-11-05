# src/shibuya/engine/body

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 5 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/engine/body/__init__.py)

engine.body — 本人の体と System 1 の層(第 3 期 3-5・③ 群=意図しない体と System 1 の反応)。

- import している内部モジュール: `shibuya.engine.body.model`・`shibuya.engine.body.schedule`
- 呼び手: `shibuya.cli`・`shibuya.engine.systems.build`
- 読む試験: `tests/engine/body/test_body_guard.py`・`tests/engine/body/test_body_manifest.py`・`tests/engine/body/test_body_reserve.py`・`tests/engine/body/test_body_same_values.py`
- 決定の ID: 10-12・10-12/§1-5

## [model.py](../../../../../../../../src/shibuya/engine/body/model.py)

engine.body.model — 本人の体の層 ``BodyModel``(状態台帳の外の状態の持ち主 ``body``=行 ``BD``・第 3 期 3-5)。

- 公開の関数とクラス
  - `BodyModel`(クラス): 本人の体の層(持ち主 ``body``)。``arm``=TM5 の腕(``sweep``/``reserve``)・``n``=体の数・``gauge``=段の境目の計器を
  - `gauge_on`(関数): 段の境目の計器を数えるか(環境変数 ``SHIBUYA_BODY_BOUNDARY_GAUGE`` が ``1``)。組み立てのときに読む。
  - `manifest_fields`(関数): manifest の ``body``(持ち主・腕・規則の出典の表・器だけの 3 件=設定/予約と段の境目の計器=観測)。
- import している内部モジュール: `shibuya.core.time_consts`・`shibuya.engine.body.rules`・`shibuya.engine.body.schedule`・`shibuya.engine.body.system1`
- 呼び手: `shibuya.engine.body`・`shibuya.engine.processes.environment`・`shibuya.engine.processes.salient`・`shibuya.engine.run`
- 読む試験: `tests/engine/body/test_body_manifest.py`・`tests/engine/body/test_body_reserve.py`
- 読む試験(道筋で): `tests/engine/body/test_body_guard.py`
- 状態台帳の行
  - 持ち主 `body`(`BodyModel`)
    - `BD` BodyModel(本人の体の層の段の境目の計器と TM5 の予約の列・第 3 期 3-5)(挙動 diag・復元 discardable) 道筋 `body._body_meter`・`body._reservations` 書ける系: body・world
- 環境変数: `SHIBUYA_BODY_BOUNDARY_GAUGE`

## [rules.py](../../../../../../../../src/shibuya/engine/body/rules.py)

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
- import している内部モジュール: `shibuya.agents.state`・`shibuya.core.time_consts`・`shibuya.engine.change_detect`・`shibuya.engine.energy`
- 呼び手: `shibuya.engine.body.model`・`shibuya.engine.body.schedule`・`shibuya.engine.processes.environment`・`shibuya.engine.processes.salient`・`shibuya.engine.resolve`
- 読む試験: `tests/engine/body/test_body_rules_sources.py`・`tests/engine/body/test_body_same_values.py`・`tests/engine/body/test_meal_default_w17.py`
- 決定の ID: 10-12・10-12/§1-5・10-13b/§7・11-01・D-118・第 275

## [schedule.py](../../../../../../../../src/shibuya/engine/body/schedule.py)

engine.body.schedule — TM5「次に段階の境目を越える時刻を予約」の口(第 3 期 3-5・腕 ``--body-schedule``)。

- 公開の関数とクラス
  - `BodySchedule`(クラス): 体の層の予約の列(状態台帳の行 ``BD`` の中身)。
  - `arm`(関数): いまの腕(``sweep``=既定・``reserve``=TM5 の予約)。組み立てのときに読む。
  - `chain_digest`(関数): 段の境目の列の鎖のハッシュ(``sha256(前 ‖ 刻み ‖ 種類 ‖ 体 ‖ 前の値 ‖ 後の値)``・体は昇順)。
  - `next_felt_frames`(関数): 窓 ``frame`` の次に、列 ``cols`` の体感温度が変わる窓(``int64``・その日の中に無ければ :data:`NEVER`)。
  - `next_intero_steps`(関数): 規則に通した直後(刻み ``now``)の値から、次に空腹か疲れが変わりうる最初の刻み(``int64``・無ければ :data:`NEVER`)。
  - `set_arm`(関数): 腕を選ぶ(CLI ``--body-schedule``・試験の切替口)。組み立ての時に読む(ランの途中で変えても、そのランは変わらない)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.body.rules`・`shibuya.engine.energy`・`shibuya.engine.scheduler`
- 呼び手: `shibuya.engine.body`・`shibuya.engine.body.model`
- 読む試験: `tests/engine/body/test_body_reserve.py`・`tests/engine/body/test_body_rules_sources.py`
- 読む試験(道筋で): `tests/engine/body/test_body_guard.py`・`tests/engine/systems/test_stage_a_guard.py`
- 環境変数: `SHIBUYA_BODY_SCHEDULE`
- 決定の ID: 10-12・10-12/§4-2

## [system1.py](../../../../../../../../src/shibuya/engine/body/system1.py)

engine.body.system1 — 意図しない System 1 の反応の**器だけ**の 3 件(第 3 期 3-5・値は空)。

- 公開の関数とクラス
  - `System1Slot`(クラス): 器 1 つ(id・中身・口・欄・値が入る段・つなぎの台帳の行)。
  - `crowd_gait`(関数): 混雑の中の歩き方と避け方の口。**値は空**(None=空間の段 1 の物理で入る)。
  - `loud_sound_notice`(関数): 大きな音に注意が向く口(知覚の事実 ``Percept.nearby_change`` の種類 ``loud_sound``)。**値は空**(None)。
  - `manifest_rows`(関数): manifest の ``body.system1``(器の一覧・設定)。
  - `noise_stage_at`(関数): W10 の騒音の段の読みの口(``World.noise_stage_for_tick`` の値をセルで引く・読むだけ)。舞台の外の体は 0。
  - `speech_loudness`(関数): ロンバード効果の口: 周りの騒音の段 → 話す大きさ。**値は空**(None=仕組みがまだ無い・空間の段 3)。
- import している内部モジュール: `shibuya.perception.facts`
- 呼び手: `shibuya.engine.body.model`・`shibuya.engine.contact.layer`
- 読む試験: `tests/engine/body/test_body_rules_sources.py`・`tests/engine/body/test_system1_placeholders.py`
- 決定の ID: 10-12・10-12/§1-5
