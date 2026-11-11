# src/shibuya/foundation/ports

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 6 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/foundation/ports/__init__.py)

(冒頭の説明なし)

## [decision.py](../../../../../../../../src/shibuya/foundation/ports/decision.py)

engine.decision.port — 候補の口 J0 の型と、提示(順のシャッフルと番号)の仕組み(第 1 期 1-8・DM-0・DM4・DM5・DM13・C-2)。

- 公開の関数とクラス
  - `Candidate`(クラス): 候補 1 つ(``number`` は提示のときに振る=作る側は ``None``)。
  - `Choice`(クラス): 口の答え(``choose`` が返す)。驚き・迷い・連続値・ひと言は空(None)で始める(〔決定〕と 1-8b)。
  - `DecisionContext`(クラス): 判断の入力(``perception.facts.PerceptCarrier`` の形)。口は値を解釈しない。
  - `DecisionPort`(クラス): 候補の口(判断モデルと LLM で 1 つ)。実装は ``_answer`` だけを書く。
  - `Hesitation`(クラス): 迷い(DM5): 1 位と 2 位の確率の差(``margin``)と分布のエントロピー(``entropy``・自然対数)。
  - `compose`(関数): 判断の入力の文(DM4: 短い版と長い版を 1 つの仕組みで・共通部分を前に)。J0 では使わない(プロンプトは今のまま)。
  - `options_text`(関数): 提示の文(候補は「頭に浮かんだこと」として・番号つき・最後に「その他」)。C-2 の 3・4。
  - `present`(関数): 候補を並べ替え、提示の番号(1〜n)を**最後に**振った写しを返す(C-2 の 1・Concordia の形)。
  - `present_rng`(関数): 並べ替えの乱数(10c の counter の鍵=``core.rng.k19_counters``(刻みの鍵・体・候補の数))。
- import している内部モジュール: `shibuya.foundation.rng`
- 呼び手: `shibuya.engine.calendar2.layer`・`shibuya.engine.calendar2.port`・`shibuya.engine.calendar3.layer`・`shibuya.engine.calendar3.port`・`shibuya.engine.calendar_self`・`shibuya.engine.contact.layer`・`shibuya.engine.contact.port`・`shibuya.engine.decision.layer`・`shibuya.engine.decision.ports`・`shibuya.engine.decision.sources`・`shibuya.engine.duties.layer`・`shibuya.engine.duties.port`・`tools/instruments/dm_eval/backends/base.py`・`tools/instruments/dm_eval/bias.py`・`tools/instruments/dm_eval/cli.py`・`tools/instruments/dm_eval/judge.py`・`tools/instruments/dm_eval/situations.py`
- 読む試験: `tests/build_pop/test_w21_stage8_9.py`・`tests/economy/stage2/test_stage2_calls.py`・`tests/engine/calendar/test_ca1b_unit.py`・`tests/engine/calendar3/test_ca3_units.py`・`tests/engine/contact/test_c1_fixes.py`・`tests/engine/contact/test_c1_units.py`・`tests/engine/decision/_j0.py`・`tests/engine/decision/test_j0_cause_columns.py`・`tests/engine/decision/test_j0_mock_equivalence.py`・`tests/engine/decision/test_j0_other_ratio_field.py`・`tests/engine/decision/test_j0_port_schema.py`・`tests/engine/decision/test_j0_shuffle_invariance.py`・`tests/engine/duties/test_du_units.py`・`tests/engine/test_pop_w21_world.py`・`tests/engine/time/test_v30a_key_sites.py`・`tests/tools/test_dm_eval.py`
- 読む試験(道筋で): `tests/engine/time/test_t0_rng_key.py`
- 決定の ID: 10-12/§4-7・10-13b/§4-2・R-108・R-113

## [experiment_gate.py](../../../../../../../../src/shibuya/foundation/ports/experiment_gate.py)

engine.experiment.gate — 実験が世界に入る口(第 1 期 1-3・CP12)。**この 1 関数 ``admit`` だけ**。

- 公開の関数とクラス
  - `admit`(関数): 実験の条件 ``cond_id`` を原因とする出来事を記録の時計の時刻で 1 行書き、id を返す(CP12 の唯一の口)。
- import している内部モジュール: `shibuya.foundation.journal.log`・`shibuya.foundation.vocab.events`
- 呼び手: `shibuya.engine.experiment.apply`・`shibuya.foundation.journal.log`
- 読む試験: `tests/engine/decision/test_j0_cause_columns.py`・`tests/engine/events/test_e_cause_three_kinds.py`・`tests/engine/experiment/test_x33_apply.py`・`tests/engine/experiment/test_x33_form.py`・`tests/engine/state/test_class_ids.py`
- 決定の ID: 10-12/§4-5・R-113

## [ledger.py](../../../../../../../../src/shibuya/foundation/ports/ledger.py)

engine.ledger_api — 台帳の**依存逆転インターフェース**(Protocol と語彙だけ・実装は economy)。

- 公開の関数とクラス
  - `DayCloses`(クラス): ``LedgerBundle.end_of_day`` の戻り(その日の締め)。
  - `EntityRef`(クラス): 台帳の主体参照 = (部門, 部門内の索引)。
  - `GoodsLedger`(クラス): 物の台帳(U-Goods・世界過程設計書 §7.1)。実装は ``shibuya.economy.goods.GoodsLedger``。
  - `LedgerBundle`(クラス): resolve / run へ注入する台帳の束(金・物)。どちらも ``None`` 可(C2 互換経路)。
  - `MoneyLedger`(クラス): 金の台帳(U11)。実装は ``shibuya.economy.ledger.Ledger``。
  - `TransferStatus`(クラス): ``transfer`` の結果コード(**業務上の失敗は例外にしない**=行動契約書 §2.1 と同思想)。
- 呼び手: `shibuya.cli`・`shibuya.economy.accounts`・`shibuya.economy.ledger`・`shibuya.economy.stage2`・`shibuya.economy.tax_deposit`・`shibuya.engine.economy_stage2`・`shibuya.engine.processes.rail`・`shibuya.engine.resolve`・`shibuya.engine.run`
- 読む試験: `tests/economy/cp2/head_ledger_136fdbb.py`・`tests/economy/cp2/test_cp2_event_links.py`・`tests/economy/cp2/test_cp2_flow_sum.py`・`tests/economy/cp2/test_cp2_k17_capacity_and_overflow.py`・`tests/economy/cp2/test_cp2_nine_ops_equivalence.py`・`tests/economy/cp2/test_cp2_write_window.py`・`tests/economy/cp2/test_cp2_writes_declared.py`・`tests/economy/stage2/test_stage2_account_and_conservation.py`・`tests/economy/stage2/test_stage2_calls.py`・`tests/economy/stage2/test_stage2_money_rules.py`・`tests/economy/stage2/test_stage2_runs.py`・`tests/economy/test_accounts.py`・`tests/economy/test_census.py`・`tests/economy/test_ledger.py`・`tests/economy/test_rules42_runs.py`・`tests/economy/test_rules42b_ledger.py`・`tests/economy/test_t3_redundant_equation.py`・`tests/engine/processes/test_goods_flow.py`・`tests/engine/test_ledger_wiring.py`・`tests/engine/test_processes_run.py`・`tests/engine/test_resume_10d.py`
- 読む試験(道筋で): `tests/tools/test_pkgmove.py`
- 決定の ID: D-85

## [percept.py](../../../../../../../../src/shibuya/foundation/ports/percept.py)

perception.facts — 知覚の事実 ``Percept``(第 1 期 1-2 知覚の分離)。

- 公開の関数とクラス
  - `BodyView`(クラス): 体の段(空腹・疲れ・暑さ)。``hunger``・``fatigue``・``thermal`` は内受容の値(0〜10)、``*_stage`` は閾値
  - `IntentView`(クラス): いまの意図(行為のコード・対象の種類=``agents.state.IntentKind``・対象の番号)。
  - `Percept`(クラス): 1 体・1 刻みの知覚の事実(構造のある事実。文は ``Renderer.render_percept`` が描く)。
  - `PerceptCarrier`(クラス): 1-8 の ``DecisionPort.choose(ctx, candidates)`` の ``ctx`` が満たす形(知覚の事実を持つ)。
  - `PerceptDrawing`(クラス): 知覚の事実の描き方(文章はその 1 つ=``perception.renderer.Renderer``)。
  - `SceneView`(クラス): その場(セルと刻みで決まる事実=同じセルの全員で同じ・刻みごとに 1 回作る)。
  - `SeenObject`(クラス): 見えた物 1 つ(id・種類・距離・向き)。今はセルの代表点から見える物=距離と向きは空間の段で入る(None)。
  - `SeenPerson`(クラス): 見えた人 1 人(id・向き・行為)。並びは描画の近接行と同じ(焦点が先頭・ほかは距離の順か id の順)。
  - `SelfView`(クラス): 自分の状態(種別・所持金・手がふさがっているか・今の行為)。持ち物の中身は ``Percept.belongings``(空=1-7)。
  - `Sound`(クラス): 聞こえる音 1 つ(段)。
  - `TimeView`(クラス): 時刻の見方(同じ刻みの全員で同じ)。
  - `WakeView`(クラス): 起きた理由と直前の結果(B6 の材料)。
  - `percept_fields`(関数): ``Percept`` の欄の名(宣言順)。
  - `percept_manifest`(関数): manifest の ``percept``(計器): 形の版・欄の数と名・空の欄の一覧。
  - `with_prediction`(関数): 本人の予想を並べた ``Percept`` の写し(1-8 の口が使う)。
- 呼び手: `shibuya.engine.body.system1`・`shibuya.engine.run`・`shibuya.perception.renderer`
- 読む試験: `tests/engine/body/test_system1_placeholders.py`・`tests/engine/contact/test_c1_units.py`・`tests/engine/contact/test_c2_video.py`・`tests/engine/decision/test_j0_port_schema.py`・`tests/engine/memory/test_m3_impression_and_trace.py`・`tests/engine/tools/test_c0_signboard_mark_invariance.py`・`tests/perception/facts/test_coef_removed_or_armed.py`・`tests/perception/facts/test_percept_is_scratch.py`・`tests/perception/facts/test_percept_schema.py`・`tests/perception/test_nearby_vectorized.py`
- 決定の ID: 10-03/§7・10-12/§1-6・10-12/§1-13・10-12/§4-4・10-13b/§4-2・R-113

## [percept_contact.py](../../../../../../../../src/shibuya/foundation/ports/percept_contact.py)

perception.contact_view — 連絡の道具 C1 の知覚の事実の値(目と心の向き・道具の状態)と描き方の行(第 6 期 6-4・腕 c1 だけ)。

- 公開の関数とクラス
  - `AttentionView`(クラス): 目と心の向き(``Percept.mind_dir`` の値=腕 c1 のランだけ)。
  - `DeviceView`(クラス): 道具の状態と通知(``Percept.tool_state`` の値=腕 c1 のランだけ)。返すのは現実の道具が知り得ることだけ(CT0 の 4)。
  - `contact_lines`(関数): B6 の末尾に足す行(通話 → 着信 → 通知 → 未読 → 割り込めなかった出来事の順)。
  - `people_hint_word`(関数): 人の気配の数 → 粗い語(周辺視=数えない)。
- 呼び手: `shibuya.engine.contact.attention`・`shibuya.engine.contact.calls`・`shibuya.engine.contact.deliver`・`shibuya.engine.contact.layer`・`shibuya.perception.renderer`
- 読む試験: `tests/engine/contact/test_c1_units.py`・`tests/engine/contact/test_c1_world.py`・`tests/engine/contact/test_c2_video.py`
- 決定の ID: 10-12/§4-4
