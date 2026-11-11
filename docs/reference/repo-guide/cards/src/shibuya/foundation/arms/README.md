# src/shibuya/foundation/arms

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 5 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/foundation/arms/__init__.py)

(冒頭の説明なし)

## [calendar2.py](../../../../../../../../src/shibuya/foundation/arms/calendar2.py)

engine.calendar2.arm — カレンダー 2 の腕(第 6 期 6-2・CA2 (c)(d)・CA3・CA4・CA6・CA7・CA8)。

- 公開の関数とクラス
  - `arm`(関数): いまの腕(``off``=既定・``arm``)。組み立てのときに読む。
  - `config`(関数): 設定の指紋と manifest の設定の子に出す腕の組(腕 off は ``None``=指紋に何も足さない)。
  - `is_on`(関数)
  - `set_arm`(関数): 腕を選ぶ(CLI ``--calendar-2``・試験の切替口)。
- 呼び手: `shibuya.cli`・`shibuya.engine.calendar2.layer`・`shibuya.mind.plan.promise_book`・`shibuya.runtime.systems.assemble`
- 読む試験: `tests/engine/calendar2/_ca2.py`・`tests/engine/calendar2/test_ca2_runs.py`・`tests/engine/calendar3/_ca3.py`
- 環境変数: `SHIBUYA_CALENDAR_2`

## [calendar3.py](../../../../../../../../src/shibuya/foundation/arms/calendar3.py)

engine.calendar3.arm — カレンダー 3 の腕(第 6 期 6-2・雇い主・祝日=C3 職場の連絡と束ねる・CA1・CA9・CA10・CA11)。

- 公開の関数とクラス
  - `arm`(関数): いまの腕(``off``=既定・``arm``)。組み立てのときに読む。
  - `config`(関数): 設定の指紋と manifest の設定の子に出す腕の組(腕 off は ``None``=指紋に何も足さない)。
  - `is_on`(関数)
  - `set_arm`(関数): 腕を選ぶ(CLI ``--calendar-3``・試験の切替口)。
  - `set_trial`(関数)
  - `trial`(関数): 試験用の印の下の腕(``off``・``on``)。
  - `trial_on`(関数): 試験用の印が効くか(腕 arm で下の腕 on のときだけ)。
- 呼び手: `shibuya.cli`・`shibuya.engine.calendar3.layer`・`shibuya.runtime.systems.assemble`・`shibuya.runtime.systems.conductor`
- 読む試験: `tests/engine/calendar3/_ca3.py`・`tests/engine/calendar3/test_ca3_runs.py`・`tests/engine/calendar3/test_ca3_units.py`
- 環境変数: `SHIBUYA_CALENDAR_3`・`SHIBUYA_CALENDAR_3_TRIAL`・名前を読めない所 1 か所
- 決定の ID: 10-12/§4-1

## [contact.py](../../../../../../../../src/shibuya/foundation/arms/contact.py)

engine.contact.arm — 連絡の道具 C1 の腕(第 6 期 6-4)。

- 公開の関数とクラス
  - `arm`(関数): いまの腕(``off``=既定・``c1``)。組み立てのときに読む。
  - `config`(関数): 設定の指紋と manifest の設定の子に出す腕の組(腕 off は ``None``=指紋に何も足さない)。〔C2〕習慣の腕は on のときだけ
  - `habit`(関数): CT4 の習慣の腕(``off``・``on``)。
  - `habit_on`(関数)
  - `is_on`(関数)
  - `send`(関数): 送る文の腕(``b``・``c``)。
  - `set_arm`(関数): 腕を選ぶ(CLI ``--contact``・試験の切替口)。
  - `set_habit`(関数)
  - `set_send`(関数)
  - `set_unnoticed`(関数)
  - `unnoticed`(関数): 割り込めなかった出来事の載せ方の腕(``i``・``ii``・``iii``)。
- 呼び手: `shibuya.cli`・`shibuya.engine.contact.book`・`shibuya.engine.contact.calls`・`shibuya.engine.contact.chat_state`・`shibuya.engine.contact.deliver`・`shibuya.engine.contact.layer`・`shibuya.mind.plan.contact_attention`・`shibuya.mind.plan.contact_habit`・`shibuya.runtime.systems.assemble`・`shibuya.runtime.systems.conductor`・`shibuya.world.things.device`
- 読む試験: `tests/engine/calendar2/_ca2.py`・`tests/engine/calendar3/_ca3.py`・`tests/engine/contact/_c1.py`・`tests/engine/contact/_c2.py`・`tests/engine/contact/test_c1_runs.py`・`tests/engine/contact/test_c1_units.py`・`tests/engine/contact/test_c2_habit.py`
- 環境変数: `SHIBUYA_CONTACT`・`SHIBUYA_CONTACT_HABIT`・`SHIBUYA_CONTACT_SEND`・`SHIBUYA_CONTACT_UNNOTICED`・名前を読めない所 1 か所
- 決定の ID: 10-12/§4-4

## [duties.py](../../../../../../../../src/shibuya/foundation/arms/duties.py)

engine.duties.arm — 店の仕事の腕(第 6 期 6-6 ② 第 1 部=開閉店・補充・廃棄を担当の体の判断に)。

- 公開の関数とクラス
  - `arm`(関数): いまの腕(``off``=既定・``arm``)。組み立てのときに読む。
  - `config`(関数): 設定の指紋と manifest の設定の子に出す腕の組(腕 off は ``None``=指紋に何も足さない)。
  - `is_on`(関数)
  - `set_arm`(関数): 腕を選ぶ(CLI ``--duties``・試験の切替口)。
- 呼び手: `shibuya.cli`・`shibuya.engine.duties.layer`・`shibuya.runtime.systems.assemble`
- 読む試験: `tests/engine/duties/_du.py`・`tests/engine/duties/test_du_runs.py`・`tests/engine/duties/test_du_units.py`
- 環境変数: `SHIBUYA_DUTIES`・名前を読めない所 1 か所
