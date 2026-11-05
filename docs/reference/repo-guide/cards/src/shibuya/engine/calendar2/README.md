# src/shibuya/engine/calendar2

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 6 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/engine/calendar2/__init__.py)

engine.calendar2 — カレンダー 2「会話とメッセージから生まれる予定」(第 6 期 6-2・腕 ``--calendar-2 arm``・既定 off)。

## [arm.py](../../../../../../../../src/shibuya/engine/calendar2/arm.py)

engine.calendar2.arm — カレンダー 2 の腕(第 6 期 6-2・CA2 (c)(d)・CA3・CA4・CA6・CA7・CA8)。

- 公開の関数とクラス
  - `arm`(関数): いまの腕(``off``=既定・``arm``)。組み立てのときに読む。
  - `config`(関数): 設定の指紋と manifest の設定の子に出す腕の組(腕 off は ``None``=指紋に何も足さない)。
  - `is_on`(関数)
  - `set_arm`(関数): 腕を選ぶ(CLI ``--calendar-2``・試験の切替口)。
- 呼び手: `shibuya.cli`・`shibuya.engine.calendar2.book`・`shibuya.engine.calendar2.layer`・`shibuya.engine.systems.build`
- 読む試験: `tests/engine/calendar2/_ca2.py`・`tests/engine/calendar2/test_ca2_runs.py`・`tests/engine/calendar3/_ca3.py`
- 環境変数: `SHIBUYA_CALENDAR_2`

## [book.py](../../../../../../../../src/shibuya/engine/calendar2/book.py)

engine.calendar2.book — 本人の予定の器(第 6 期 6-2 カレンダー 2・CA3・CA4・CA6・CA7)。

- 公開の関数とクラス
  - `PromiseBook`(クラス): 本人の予定の器(状態台帳の腕の行 ``CA2B``)。行は持ち主ごと=二人の約束も各自が自分の行を持つ。
  - `broken`(関数): 壊れた予定(CA4 (d))なら理由・そうでなければ ``None``。
- import している内部モジュール: `shibuya.engine.calendar2.arm`
- 呼び手: `shibuya.engine.calendar2.layer`・`shibuya.engine.calendar3.layer`
- 読む試験: `tests/engine/calendar2/test_ca2_units.py`・`tests/engine/calendar3/test_ca3_runs.py`・`tests/engine/calendar3/test_ca3_units.py`
- 状態台帳の行
  - 持ち主 `calendar2.book`(`PromiseBook`)
    - `CA2B` PromiseBook(本人の予定の器=各自が自分の理解の行・第 6 期 6-2 カレンダー 2)(挙動 behavior・復元 required・腕 calendar-2) 道筋 `calendar2.book.by_owner`・`calendar2.book.next_id`・`calendar2.book.rows` 書ける系: calendar_2・calendar_3
- 決定の ID: 10-12/§4-1

## [layer.py](../../../../../../../../src/shibuya/engine/calendar2/layer.py)

engine.calendar2.layer — カレンダー 2「会話とメッセージから生まれる予定」の持ち主と系 ``calendar_2``(第 6 期 6-2・腕``--calendar-2 arm``・既定 off)。

- 公開の関数とクラス
  - `Calendar2Layer`(クラス): カレンダー 2 の持ち主(状態台帳の腕の行 ``CA2*``)。
  - `audit_causes`(関数): 負の対照の監査: 族 ``約束`` の出来事のうち、本人の判断の語の原因が判断の呼び(LlmCall・源と番号つき・この層の形の
  - `issued_key`(関数)
  - `manifest_fields`(関数): manifest の ``calendar_2``(腕 arm のランだけ・ほかは空=欄を出さない)。
  - `sys_calendar_2`(関数): 系 calendar_2(刻みの中・腕 arm のランだけ立つ)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.core.rng`・`shibuya.core.time_consts`・`shibuya.engine.calendar2.arm`・`shibuya.engine.calendar2.book`・`shibuya.engine.calendar2.port`・`shibuya.engine.calendar2.recall`・`shibuya.engine.calendar_self`・`shibuya.engine.contact.attention`・`shibuya.engine.decision.port`・`shibuya.engine.events.log`・`shibuya.engine.events.vocab`・`shibuya.engine.processes.opening`・`shibuya.engine.resolve`・`shibuya.llm.mock`
- 呼び手: `shibuya.engine.run`・`shibuya.engine.systems.build`・`shibuya.engine.systems.table`
- 読む試験: `tests/engine/calendar2/_ca2.py`・`tests/engine/calendar2/test_ca2_runs.py`・`tests/engine/calendar2/test_ca2_units.py`・`tests/engine/calendar2/test_ca2_world.py`・`tests/engine/time/test_v30a_key_sites.py`
- 読む試験(道筋で): `tests/engine/space/test_nav1_units.py`・`tests/engine/time/test_t0_rng_key.py`
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

## [port.py](../../../../../../../../src/shibuya/engine/calendar2/port.py)

engine.calendar2.port — カレンダー 2 の本人の判断(候補の口 J0 の形)の仮のモデルと候補の作り方(第 6 期 6-2)。

- 公開の関数とクラス
  - `Calendar2Port`(クラス): カレンダー 2 の判断の仮のモデル(mock・判断モデルの代わり)。乱数の鍵はその刻みのその体の判断の通し番号。
  - `call_id_of`(関数): 判断の呼びの id(テープの形 ``<刻み>:<体>:<−通し番号>``)。
  - `cand`(関数): 候補 1 つ(源は語から・見せ方の文は省略で語そのもの・id は省略で語)。
  - `parse_call_id`(関数): カレンダー 2 の判断の呼びの id → ``(刻み, 体, 通し番号)``(この形でなければ ``None``)。
  - `purpose_of_serial`(関数)
  - `serial_of`(関数): 判断の通し番号(``SERIAL_BASE``+その刻みのその体の k 回目 × 16+判断の種類)。上限を超えたら ``ValueError``。
- import している内部モジュール: `shibuya.core.rng`・`shibuya.engine.decision.port`
- 呼び手: `shibuya.engine.calendar2.layer`・`shibuya.engine.calendar3.layer`
- 読む試験: `tests/engine/calendar2/_ca2.py`・`tests/engine/calendar2/test_ca2_units.py`・`tests/engine/calendar3/test_ca3_units.py`・`tests/engine/time/test_v30a_key_sites.py`
- 読む試験(道筋で): `tests/engine/time/test_t0_rng_key.py`
- 決定の ID: 10-12/§4-1

## [recall.py](../../../../../../../../src/shibuya/engine/calendar2/recall.py)

engine.calendar2.recall — 頭の中の予定の思い出し(第 6 期 6-2 カレンダー 2・CA3「頭の中だけの予定もエンジンは保管し、本人には記憶で思い出せたときだけ見せる」・AT1「頭の中=記憶で思い出せたとき」)。

- 公開の関数とクラス
  - `HeadRecall`(クラス): 頭の中の予定の思い出しの口(参照=状態を持たない。痕跡は行の ``trace`` に置く)。
- import している内部モジュール: `shibuya.engine.memory`・`shibuya.engine.memory_m1`
- 呼び手: `shibuya.engine.calendar2.layer`
- 決定の ID: 10-12/§4-6
