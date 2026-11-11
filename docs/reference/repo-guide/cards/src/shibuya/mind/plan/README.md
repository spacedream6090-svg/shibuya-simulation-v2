# src/shibuya/mind/plan

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 9 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/mind/plan/__init__.py)

(冒頭の説明なし)

## [calendar2_port.py](../../../../../../../../src/shibuya/mind/plan/calendar2_port.py)

engine.calendar2.port — カレンダー 2 の本人の判断(候補の口 J0 の形)の仮のモデルと候補の作り方(第 6 期 6-2)。

- 公開の関数とクラス
  - `Calendar2Port`(クラス): カレンダー 2 の判断の仮のモデル(mock・判断モデルの代わり)。乱数の鍵はその刻みのその体の判断の通し番号。
  - `call_id_of`(関数): 判断の呼びの id(テープの形 ``<刻み>:<体>:<−通し番号>``)。
  - `cand`(関数): 候補 1 つ(源は語から・見せ方の文は省略で語そのもの・id は省略で語)。
  - `parse_call_id`(関数): カレンダー 2 の判断の呼びの id → ``(刻み, 体, 通し番号)``(この形でなければ ``None``)。
  - `purpose_of_serial`(関数)
  - `serial_of`(関数): 判断の通し番号(``SERIAL_BASE``+その刻みのその体の k 回目 × 16+判断の種類)。上限を超えたら ``ValueError``。
- import している内部モジュール: `shibuya.foundation.ports.decision`・`shibuya.foundation.rng`
- 呼び手: `shibuya.engine.calendar2.layer`・`shibuya.engine.calendar3.layer`
- 読む試験: `tests/engine/calendar2/_ca2.py`・`tests/engine/calendar2/test_ca2_units.py`・`tests/engine/calendar3/test_ca3_units.py`・`tests/engine/time/test_v30a_key_sites.py`
- 読む試験(道筋で): `tests/engine/time/test_t0_rng_key.py`
- 決定の ID: 10-12/§4-1

## [calendar3_port.py](../../../../../../../../src/shibuya/mind/plan/calendar3_port.py)

engine.calendar3.port — カレンダー 3 の本人の判断(候補の口 J0 の形)の仮のモデルと候補の語(第 6 期 6-2・雇い主・C3)。

- 公開の関数とクラス
  - `Calendar3Port`(クラス): カレンダー 3 の判断の仮のモデル(mock・判断モデルの代わり)。乱数の鍵はその刻みのその体の判断の通し番号。
  - `call_id_of`(関数): 判断の呼びの id(テープの形 ``<刻み>:<体>:<−通し番号>``)。
  - `cand`(関数): 候補 1 つ(源は語から・見せ方の文は省略で語そのもの・id は省略で語)。
  - `parse_call_id`(関数): カレンダー 3 の判断の呼びの id → ``(刻み, 体, 通し番号)``(この形でなければ ``None``)。
  - `purpose_of_serial`(関数)
  - `serial_of`(関数): 判断の通し番号(``SERIAL_BASE``+その刻みのその体の k 回目 × 16+判断の種類)。上限を超えたら ``ValueError``。
- import している内部モジュール: `shibuya.foundation.ports.decision`・`shibuya.foundation.rng`
- 呼び手: `shibuya.engine.calendar3.layer`
- 読む試験: `tests/engine/calendar3/_ca3.py`・`tests/engine/calendar3/test_ca3_runs.py`・`tests/engine/calendar3/test_ca3_units.py`・`tests/engine/duties/test_du_units.py`・`tests/engine/time/test_v30a_key_sites.py`
- 読む試験(道筋で): `tests/engine/time/test_t0_rng_key.py`
- 決定の ID: 10-12/§4-1

## [contact_attention.py](../../../../../../../../src/shibuya/mind/plan/contact_attention.py)

engine.contact.attention — 目と心の向き(第 6 期 6-4 C1・決定 10-12 §4-4 CT0「使っている間の気づきにくさ」=係数を掛けない)。

- 公開の関数とクラス
  - `Attention`(クラス): 体ごとの目と心の向き(状態台帳の腕の行 ``CT1A``・持ち主の道筋 ``contact.attn``)。
  - `coarsen`(関数): 知覚の事実 ``p`` を目と心の向きの形にした写し(``mind_dir``=:class:`AttentionView`・``tool_state``=道具の状態)。
  - `gate_salient`(関数): その刻みの顕著行為ごとの「気づいた体」から、関心の的が周りでなく割り込めなかった体を外した写しを返す(〔検収 M1〕
  - `interrupted_of`(関数): 起きた理由が驚き駆動の入口(セルの B4 の変化)か。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.foundation.arms.contact`・`shibuya.foundation.ports.percept_contact`・`shibuya.foundation.time_consts`
- 呼び手: `shibuya.engine.calendar2.layer`・`shibuya.engine.contact.layer`
- 読む試験: `tests/engine/contact/test_c1_fixes.py`・`tests/engine/contact/test_c1_flow.py`・`tests/engine/contact/test_c1_units.py`・`tests/engine/contact/test_c2_video.py`
- 状態台帳の行
  - 持ち主 `contact.attn`(`Attention`)
    - `CT1A` Attention(目と心の向き=視線の先・関心の的・前の刻みの活動・最後に気づいた通知・第 6 期 6-4 C1)(挙動 behavior・復元 required・腕 contact-c1) 道筋 `contact.attn._focus`・`contact.attn._gaze`・`contact.attn._notice`・`contact.attn._prev_act` 書ける系: calendar_3・contact
    - `CT1AS` Attention._gaze_since(今の視線になった時刻=画面を見ていた長さの計器の素・第 6 期 6-4 C1)(挙動 diag・復元 required・腕 contact-c1) 道筋 `contact.attn._gaze_since` 書ける系: calendar_3・contact
- 決定の ID: 10-12/§4-4・D-121

## [contact_habit.py](../../../../../../../../src/shibuya/mind/plan/contact_habit.py)

engine.contact.habit — CT4 の習慣(本人の過去の連絡の判断から作る・第 6 期 6-4 C2・腕 ``SHIBUYA_CONTACT_HABIT``)。

- 公開の関数とクラス
  - `HabitBook`(クラス): 体ごとの連絡の選びの回数(状態台帳の腕の行 ``CT1H``・持ち主の道筋 ``contact.habit``)。
  - `states_of`(関数): 体ごとの状態(勤務中・家・移動中・ほか)。``work_cell`` が ``None`` なら勤務中は無い。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.foundation.arms.contact`
- 呼び手: `shibuya.engine.contact.layer`
- 読む試験: `tests/engine/contact/test_c2_habit.py`・`tests/engine/contact/test_c2_runs.py`・`tests/engine/time/test_v30a_key_sites.py`
- 状態台帳の行
  - 持ち主 `contact.habit`(`HabitBook`)
    - `CT1H` HabitBook(CT4 の習慣=体ごとの状態 × 判断 × 語の選びの回数・第 6 期 6-4 C2)(挙動 behavior・復元 required・腕 contact-c1) 道筋 `contact.habit._counts` 書ける系: calendar_3・contact
- 決定の ID: 10-03/§7-3・10-12/§4-4

## [contact_port.py](../../../../../../../../src/shibuya/mind/plan/contact_port.py)

engine.contact.port — 連絡の本人の判断(候補の口 J0 の形)の仮のモデル・文の口・習慣の口(第 6 期 6-4 C1)。

- 公開の関数とクラス
  - `ContactPort`(クラス): 連絡の判断の仮のモデル(mock・判断モデルの代わり)。乱数の鍵はその刻みのその体の判断の通し番号(``ctx.call_id`` から読む・
  - `MockTextPort`(クラス): 文の口の仮のモデル(LLM の口の代わり=定型の文 1 つ)。
  - `call_id_of`(関数): 判断の呼びの id(テープの形 ``<刻み>:<体>:<−通し番号>``=主の判断の起床の級 ≥ 0 と分ける)。
  - `cand`(関数): 候補 1 つ(源は語から・見せ方の文は省略で語そのもの・id は省略で語)。
  - `cap_text`(関数): 長さの上限(安全装置): 超えたら切って ``True``。
  - `habit_recheck_u`(関数): 〔C2〕習慣で答えられるときに判断の口へ戻すかの一様乱数(用途名 ``contact.habit``・0 語目を空け 1〜3 語目に刻みの鍵・体・
  - `parse_call_id`(関数): 連絡の判断の呼びの id → ``(刻み, 体, 通し番号)``(連絡の形でなければ ``None``)。
  - `purpose_of_serial`(関数)
  - `serial_of`(関数): 判断の通し番号(その刻みのその体の k 回目 × 16+判断の種類)。上限を超えたら ``ValueError``(番号がぶつからない)。
  - `step_of_call_id`(関数): 判断の呼びの id → 刻み(連絡の形でなければ ``None``)。負の対照の試験と監査が読む。
- import している内部モジュール: `shibuya.foundation.ports.decision`・`shibuya.foundation.rng`・`shibuya.llm.mock`
- 呼び手: `shibuya.engine.contact.layer`
- 読む試験: `tests/engine/calendar2/test_ca2_units.py`・`tests/engine/calendar3/test_ca3_runs.py`・`tests/engine/calendar3/test_ca3_units.py`・`tests/engine/contact/_c1.py`・`tests/engine/contact/test_c1_event_log_onoff.py`・`tests/engine/contact/test_c1_fixes.py`・`tests/engine/contact/test_c1_flow.py`・`tests/engine/contact/test_c1_units.py`・`tests/engine/contact/test_c2_charge.py`・`tests/engine/contact/test_c2_exchange.py`・`tests/engine/contact/test_c2_habit.py`・`tests/engine/contact/test_c2_runs.py`・`tests/engine/contact/test_c2_video.py`・`tests/engine/time/test_v30a_key_sites.py`
- 読む試験(道筋で): `tests/engine/time/test_t0_rng_key.py`
- 決定の ID: 10-12/§4-4

## [duties_port.py](../../../../../../../../src/shibuya/mind/plan/duties_port.py)

engine.duties.port — 店の仕事の本人の判断(候補の口 J0 の形)の仮のモデルと候補の語(第 6 期 6-6 ② 第 1 部)。

- 公開の関数とクラス
  - `DutiesPort`(クラス): 店の仕事の判断の仮のモデル(mock・判断モデルの代わり)。乱数の鍵はその刻みのその体の判断の通し番号。
  - `call_id_of`(関数): 判断の呼びの id(テープの形 ``<刻み>:<体>:<−通し番号>``)。
  - `cand`(関数): 候補 1 つ(源は語から・id は省略で語)。語が閉じた表の外なら ``KeyError``。
  - `parse_call_id`(関数): 店の仕事の判断の呼びの id → ``(刻み, 体, 通し番号)``(この形でなければ ``None``)。
  - `purpose_of_serial`(関数)
  - `serial_of`(関数): 判断の通し番号(``SERIAL_BASE``+その刻みのその体の k 回目 × 16+判断の種類)。上限を超えたら ``ValueError``。
- import している内部モジュール: `shibuya.foundation.ports.decision`・`shibuya.foundation.rng`・`shibuya.foundation.vocab.actions`
- 呼び手: `shibuya.engine.duties.layer`
- 読む試験: `tests/engine/duties/_du.py`・`tests/engine/duties/test_du_runs.py`・`tests/engine/duties/test_du_units.py`・`tests/engine/time/test_v30a_key_sites.py`
- 読む試験(道筋で): `tests/engine/time/test_t0_rng_key.py`
- 決定の ID: 10-12/§1-5

## [head_recall.py](../../../../../../../../src/shibuya/mind/plan/head_recall.py)

engine.calendar2.recall — 頭の中の予定の思い出し(第 6 期 6-2 カレンダー 2・CA3「頭の中だけの予定もエンジンは保管し、本人には記憶で思い出せたときだけ見せる」・AT1「頭の中=記憶で思い出せたとき」)。

- 公開の関数とクラス
  - `HeadRecall`(クラス): 頭の中の予定の思い出しの口(参照=状態を持たない。痕跡は行の ``trace`` に置く)。
- import している内部モジュール: `shibuya.mind.memory.memory`・`shibuya.mind.memory.memory_m1`
- 呼び手: `shibuya.engine.calendar2.layer`
- 決定の ID: 10-12/§4-6

## [promise_book.py](../../../../../../../../src/shibuya/mind/plan/promise_book.py)

engine.calendar2.book — 本人の予定の器(第 6 期 6-2 カレンダー 2・CA3・CA4・CA6・CA7)。

- 公開の関数とクラス
  - `PromiseBook`(クラス): 本人の予定の器(状態台帳の腕の行 ``CA2B``)。行は持ち主ごと=二人の約束も各自が自分の行を持つ。
  - `broken`(関数): 壊れた予定(CA4 (d))なら理由・そうでなければ ``None``。
- import している内部モジュール: `shibuya.foundation.arms.calendar2`
- 呼び手: `shibuya.engine.calendar2.layer`・`shibuya.engine.calendar3.layer`
- 読む試験: `tests/engine/calendar2/test_ca2_units.py`・`tests/engine/calendar3/test_ca3_runs.py`・`tests/engine/calendar3/test_ca3_units.py`
- 状態台帳の行
  - 持ち主 `calendar2.book`(`PromiseBook`)
    - `CA2B` PromiseBook(本人の予定の器=各自が自分の理解の行・第 6 期 6-2 カレンダー 2)(挙動 behavior・復元 required・腕 calendar-2) 道筋 `calendar2.book.by_owner`・`calendar2.book.next_id`・`calendar2.book.rows` 書ける系: calendar_2・calendar_3
- 決定の ID: 10-12/§4-1
