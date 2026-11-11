# src/shibuya/engine/calendar3

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 4 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/engine/calendar3/__init__.py)

engine.calendar3 — カレンダー 3「雇い主・祝日」(第 6 期 6-2・C3 職場の連絡と束ねる・腕 ``--calendar-3 arm``・既定 off)。

## [knowledge.py](../../../../../../../../src/shibuya/engine/calendar3/knowledge.py)

engine.calendar3.knowledge — 暦の常識(祝日の問い合わせの口と常識の文)と店の決まりの口(第 6 期 6-2 カレンダー 3)。

- 公開の関数とクラス
  - `CommonCalendar`(クラス): 暦の常識の問い合わせの口(全員が知る=CA11)。暦の口を読むだけ。
  - `StoreRules`(クラス): 店の決まりの口(組織の口が知らせる)。本段は**枠だけ**=休業日の知らせは空(つなぎ ``DOC-ca3-store-closed-days-frame``)。
  - `common_line`(関数): 常識の文の 1 行(判断の入力に足す形)。
- 呼び手: `shibuya.engine.calendar3.layer`・`shibuya.engine.duties.knowledge`
- 読む試験: `tests/engine/calendar3/test_ca3_units.py`
- 決定の ID: 10-12/§4-1

## [layer.py](../../../../../../../../src/shibuya/engine/calendar3/layer.py)

engine.calendar3.layer — カレンダー 3「雇い主・祝日」の持ち主と系 ``calendar_3``(第 6 期 6-2・C3 職場の連絡と束ねる・腕``--calendar-3 arm``・既定 off)。

- 公開の関数とクラス
  - `Calendar3Layer`(クラス): カレンダー 3 の持ち主(状態台帳の腕の行 ``CA3*``)。
  - `audit_causes`(関数): 負の対照の監査: 族 ``勤務`` の出来事のうち、本人の判断の語の原因が判断の呼び(LlmCall・源と番号つき・この層の形の
  - `issued_key`(関数)
  - `labor_params`(関数): 規則の表の労働時間の行(human=人が取り締まる側=止めない)を読む。表が無い写し・施行の前は空(記録だけの形)。
  - `manifest_fields`(関数): manifest の ``calendar_3``(腕 arm のランだけ・ほかは空=欄を出さない)。
  - `sys_calendar_3`(関数): 系 calendar_3(刻みの中・腕 arm のランだけ立つ)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.calendar3.knowledge`・`shibuya.engine.calendar_self`・`shibuya.foundation.arms.calendar3`・`shibuya.foundation.journal.log`・`shibuya.foundation.ports.decision`・`shibuya.foundation.rng`・`shibuya.foundation.time_consts`・`shibuya.foundation.vocab.events`・`shibuya.mind.plan.calendar2_port`・`shibuya.mind.plan.calendar3_port`・`shibuya.mind.plan.promise_book`・`shibuya.world.facts.rules.table`・`shibuya.world.laws.opening`
- 呼び手: `shibuya.engine.duties.layer`・`shibuya.engine.run`・`shibuya.runtime.systems.assemble`・`shibuya.runtime.systems.table`
- 読む試験: `tests/engine/calendar3/test_ca3_runs.py`・`tests/engine/calendar3/test_ca3_units.py`・`tests/engine/calendar3/test_ca3_world.py`・`tests/engine/time/test_v30a_key_sites.py`
- 読む試験(道筋で): `tests/engine/rules/test_rules_table_schema.py`・`tests/engine/time/test_t0_rng_key.py`
- 状態台帳の行
  - 持ち主 `calendar3`(`Calendar3Layer`)
    - `CA3G` Calendar3Layer が系の間と刻みの間に渡す値(読んだ C3 の連絡の控え・仲裁で回した考えた体・第 6 期 6-2)(挙動 behavior・復元 required・腕 calendar-3) 道筋 `calendar3._reads`・`calendar3._think` 書ける系: calendar_3・contact
    - `CA3M` カレンダー 3 の計器(計数・分布・休みの申し出の出来事の id・第 6 期 6-2)(挙動 diag・復元 required・腕 calendar-3) 道筋 `calendar3._c3_event_of`・`calendar3._c3_hist`・`calendar3._c3_meter` 書ける系: calendar_3
    - `CA3P` Calendar3Layer の C3 の連絡の控え・帳面・勤務の行の表・知らせの印・通し番号(第 6 期 6-2 カレンダー 3)(挙動 behavior・復元 required・腕 calendar-3) 道筋 `calendar3._agenda`・`calendar3._calls`・`calendar3._days`・`calendar3._msg`・`calendar3._next`・`calendar3._noticed`・`calendar3._out`・`calendar3._wait`・`calendar3._work_rows` 書ける系: calendar_3
    - `CA3Q` 発行したカレンダー 3 の判断の呼びの控えと呼び数(監査の突き合わせ・第 6 期 6-2)(挙動 diag・復元 required・腕 calendar-3) 道筋 `calendar3._c3_issued`・`calendar3._c3_issued_n` 書ける系: calendar_3
    - `CA3S` Calendar3Layer の雇い主の記録(組んだ週・組んだシフト・第 6 期 6-2 カレンダー 3)(挙動 behavior・復元 required・腕 calendar-3) 道筋 `calendar3._compose_due`・`calendar3._composed`・`calendar3._plan` 書ける系: calendar_3
- 書きの許可
  - 系 `calendar_3`(群 暦・時 `tick`・立つ条件 `calendar3`・関数 `sys_calendar_3`)
    - 書いてよい外の道筋: `BW:batching.*`・`CA2B:calendar2.book.*`・`CA2G:calendar2._turns`・`CA3*:calendar3.*`・`CT1*:contact.*`・`E:events.*`
- 決定の ID: 10-12/§4-1

## [roster.py](../../../../../../../../src/shibuya/engine/calendar3/roster.py)

engine.calendar3.roster — 雇い主の口のつなぎの形(第 6 期 6-2 カレンダー 3・CA1「雇い主がエージェントになるまでのつなぎ」)。

- 公開の関数とクラス
  - `Roster`(クラス): 雇い主の口の表(組み立てで 1 回作る導出・読むだけ)。
  - `build_roster`(関数): 権利台帳の雇用の行・W20 の表・母集団の役割の語から雇い主の口の表を作る(読むだけ)。
  - `empty_roster`(関数)
  - `roster_for_run`(関数): ランの雇い主の口の表(〔検収 H1〕最初の刻みの頭に呼ぶ=再開では状態を戻して権利台帳を作り直した後)。W20 の表が無い
  - `w20_table_for_run`(関数): 組み立ての口: ランの W20 の週の表(世界の資産=状態でない・母集団の無いラン=合成の世界は ``None``)。
- import している内部モジュール: `shibuya.engine.calendar_shadow`・`shibuya.world.facts.rights.initial`・`shibuya.world.facts.rights.ledger`
- 呼び手: `shibuya.runtime.systems.assemble`
- 読む試験: `tests/engine/calendar3/_ca3.py`・`tests/engine/calendar3/test_ca3_runs.py`・`tests/engine/calendar3/test_ca3_units.py`
- 決定の ID: 10-12/§4-1
