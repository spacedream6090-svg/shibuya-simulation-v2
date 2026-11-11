# src/shibuya/world/things

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 2 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/world/things/__init__.py)

(冒頭の説明なし)

## [device.py](../../../../../../../../src/shibuya/world/things/device.py)

engine.contact.device — 道具の状態と通知の刺激の形(第 6 期 6-4 C1・C2・決定 10-12 §4-4 CT0 の共通の決まり 2・3)。

- 公開の関数とクラス
  - `Devices`(クラス): 体ごとの道具の状態(状態台帳の腕の行 ``CT1D``・持ち主の道筋 ``contact.dev``)。
  - `channel_words`(関数): チャネルのビット → 語の組(音・振動・画面の順)。
  - `noise_db_of_stage`(関数): 騒音の段 → 代表の dB(段の外は端に寄せる)。
  - `power_sum_db`(関数): 2 つの音の電力の和[dB]\(``10 lg(10^(a/10) + 10^(b/10))``)。
  - `signal_ok`(関数): 電波が届くか(本段は全域で届く=つなぎ ``DOC-ct-c1-device-signal``)。
- import している内部モジュール: `shibuya.foundation.arms.contact`・`shibuya.foundation.rng`・`shibuya.foundation.text.templates`・`shibuya.foundation.time_consts`
- 呼び手: `shibuya.engine.contact.layer`
- 読む試験: `tests/engine/contact/_c2.py`・`tests/engine/contact/test_c1_fixes.py`・`tests/engine/contact/test_c1_flow.py`・`tests/engine/contact/test_c1_units.py`・`tests/engine/contact/test_c2_charge.py`・`tests/engine/contact/test_c2_video.py`
- 状態台帳の行
  - 持ち主 `contact.dev`(`Devices`)
    - `CT1D` Devices(道具の状態=電源・電池・マナーモード・置き場・イヤホン・第 6 期 6-4 C1)(挙動 behavior・復元 required・腕 contact-c1) 道筋 `contact.dev._battery`・`contact.dev._ear`・`contact.dev._home`・`contact.dev._home_prev`・`contact.dev._low_known`・`contact.dev._manner`・`contact.dev._on`・`contact.dev._place`・`contact.dev._plugged` 書ける系: calendar_3・contact
- 決定の ID: 10-12/§4-4・R-78
