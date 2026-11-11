# src/shibuya/engine/calendar2

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 2 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/engine/calendar2/__init__.py)

engine.calendar2 — カレンダー 2「会話とメッセージから生まれる予定」(第 6 期 6-2・腕 ``--calendar-2 arm``・既定 off)。

## [layer.py](../../../../../../../../src/shibuya/engine/calendar2/layer.py)

engine.calendar2.layer — カレンダー 2「会話とメッセージから生まれる予定」の持ち主と系 ``calendar_2``(第 6 期 6-2・腕``--calendar-2 arm``・既定 off)。

- 公開の関数とクラス
  - `Calendar2Layer`(クラス): カレンダー 2 の持ち主(状態台帳の腕の行 ``CA2*``)。
  - `audit_causes`(関数): 負の対照の監査: 族 ``約束`` の出来事のうち、本人の判断の語の原因が判断の呼び(LlmCall・源と番号つき・この層の形の
  - `issued_key`(関数)
  - `manifest_fields`(関数): manifest の ``calendar_2``(腕 arm のランだけ・ほかは空=欄を出さない)。
  - `sys_calendar_2`(関数): 系 calendar_2(刻みの中・腕 arm のランだけ立つ)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.calendar_self`・`shibuya.engine.resolve`・`shibuya.foundation.arms.calendar2`・`shibuya.foundation.journal.log`・`shibuya.foundation.ports.decision`・`shibuya.foundation.rng`・`shibuya.foundation.time_consts`・`shibuya.foundation.vocab.events`・`shibuya.llm.mock`・`shibuya.mind.plan.calendar2_port`・`shibuya.mind.plan.contact_attention`・`shibuya.mind.plan.head_recall`・`shibuya.mind.plan.promise_book`・`shibuya.world.laws.opening`
- 呼び手: `shibuya.engine.run`・`shibuya.runtime.systems.assemble`・`shibuya.runtime.systems.table`
- 読む試験: `tests/engine/calendar2/_ca2.py`・`tests/engine/calendar2/test_ca2_runs.py`・`tests/engine/calendar2/test_ca2_units.py`・`tests/engine/calendar2/test_ca2_world.py`・`tests/engine/space/test_nav1_units.py`・`tests/engine/time/test_v30a_key_sites.py`
- 読む試験(道筋で): `tests/engine/time/test_t0_rng_key.py`
- 状態台帳の行
  - 持ち主 `calendar2`(`Calendar2Layer`)
    - `CA2G` Calendar2Layer が系の間と刻みの間に渡す値(会話の番の控え・仲裁で回した考えた体・第 6 期 6-2 カレンダー 2)(挙動 behavior・復元 required・腕 calendar-2) 道筋 `calendar2._think`・`calendar2._turns` 書ける系: calendar_2・calendar_3・contact・decide・llm_receive
    - `CA2M` カレンダー 2 の計器(計数・分布・体ごとの約束の数・第 6 期 6-2)(挙動 diag・復元 required・腕 calendar-2) 道筋 `calendar2._c2_event_of`・`calendar2._c2_hist`・`calendar2._c2_meter`・`calendar2._c2_offer_event`・`calendar2._c2_per_agent` 書ける系: calendar_2
    - `CA2O` Calendar2Layer の誘い・帳面・歩いている行・知らせ・手帳・範囲の外の印(第 6 期 6-2 カレンダー 2)(挙動 behavior・復元 required・腕 calendar-2) 道筋 `calendar2._agenda`・`calendar2._days`・`calendar2._noticed`・`calendar2._offer_next`・`calendar2._offers`・`calendar2._out_row`・`calendar2._planner_day`・`calendar2._was_out`・`calendar2._watch` 書ける系: calendar_2
    - `CA2Q` 発行したカレンダー 2 の判断の呼びの控えと呼び数(監査の突き合わせ・第 6 期 6-2)(挙動 diag・復元 required・腕 calendar-2) 道筋 `calendar2._c2_issued`・`calendar2._c2_issued_n` 書ける系: calendar_2
- 書きの許可
  - 系 `calendar_2`(群 暦・時 `tick`・立つ条件 `calendar2`・関数 `sys_calendar_2`)
    - 呼んでよい resolve の口: `begin_walk_to`
    - 書いてよい SoA の列(閉包): `agents.activity`・`agents.board_line`・`agents.board_since`・`agents.sleep_pending`・`agents.target_node`
    - 書いてよい外の道筋: `CA2*:calendar2.*`・`E:events.*`
- 決定の ID: 10-12/§4-1・10-12/§4-4
