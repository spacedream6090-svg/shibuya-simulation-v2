# src/shibuya/society/contact

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 5 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/society/contact/__init__.py)

(冒頭の説明なし)

- 読む試験(道筋で): `tests/tools/test_pkgmove.py`

## [calls.py](../../../../../../../../src/shibuya/society/contact/calls.py)

engine.contact.calls — 電話の会話(第 6 期 6-4 C1・決定 10-12 §4-4 CT1「TM3 の会話の仕組みがそのまま使える」・§4-2 TM1・TM3)。

- 公開の関数とクラス
  - `CallManager`(クラス): 電話の会話(対面の会話の仕組みそのまま・場所が違うだけ)。
  - `CallSpeechPort`(クラス): 通話の発話の口(発話の口そのまま・道具=通話)。
- import している内部モジュール: `shibuya.foundation.arms.contact`・`shibuya.foundation.ports.percept_contact`・`shibuya.society.conversation`・`shibuya.society.speech.port`
- 呼び手: `shibuya.interim_bundles.contact.layer`
- 読む試験: `tests/engine/contact/test_c1_event_log_onoff.py`・`tests/engine/contact/test_c1_fixes.py`・`tests/engine/contact/test_c2_video.py`
- 状態台帳の行
  - 持ち主 `contact.calls` の別のクラス `CallManager`(行は `shibuya.society.conversation` のカードを見る)
  - 持ち主 `contact.speech` の別のクラス `CallSpeechPort`(行は `shibuya.society.speech.port` のカードを見る)
- 決定の ID: 10-12/§4-4

## [chat_state.py](../../../../../../../../src/shibuya/society/contact/chat_state.py)

engine.contact.chat_state — チャットの会話の状態(第 6 期 6-4 C1・決定 10-12 §4-2 TM1)。

- 公開の関数とクラス
  - `ChatBook`(クラス): 続いているチャットの状態(会話の器の子・``Session`` の表)。書く口は :meth:`on_message` と :meth:`step` だけ。
  - `group_key`(関数): グループのチャットの鍵(グループの一覧の行の番号)。
  - `pair_key`(関数): 1 対 1 のチャットの鍵(順に依らない)。
- import している内部モジュール: `shibuya.foundation.arms.contact`・`shibuya.society.conversation`
- 呼び手: `shibuya.interim_bundles.contact.layer`
- 読む試験: `tests/engine/contact/test_c1_fixes.py`・`tests/engine/contact/test_c1_units.py`
- 状態台帳の行
  - 持ち主 `contact.chats` の別のクラス `ChatBook`(行は `shibuya.society.conversation` のカードを見る)
- 決定の ID: 10-12/§4-2

## [deliver.py](../../../../../../../../src/shibuya/society/contact/deliver.py)

engine.contact.deliver — 届く(エンジン)=メッセージ・電話・既読(第 6 期 6-4 C1・決定 10-12 §4-4 CT3・CT9・§4-2 TM1)。

- 公開の関数とクラス
  - `Mailbox`(クラス): 届いた・送った・予約のメッセージと着信(書く口はこのクラスのメソッドだけ)。
  - `senders_of`(関数): 読んだ行 → 会話ごとの束 ``(鍵の種類 p/g, 相手かグループ, 最後の行の番号)``(出た順・重ねない)。
- import している内部モジュール: `shibuya.foundation.arms.contact`・`shibuya.foundation.ports.percept_contact`・`shibuya.foundation.queues.batching`・`shibuya.foundation.time_consts`
- 呼び手: `shibuya.interim_bundles.contact.layer`
- 読む試験: `tests/engine/contact/test_c1_fixes.py`・`tests/engine/contact/test_c1_flow.py`・`tests/engine/contact/test_c1_units.py`・`tests/engine/contact/test_c2_charge.py`・`tests/engine/contact/test_c2_video.py`
- 状態台帳の行
  - 持ち主 `contact.mail`(`Mailbox`)
    - `CT1I` Mailbox(届いた箱・新しく届いた数・網が預かる分・窓の境目の予約・着信と呼び出し・番号・第 6 期 6-4 C1)(挙動 behavior・復元 required・腕 contact-c1) 道筋 `contact.mail._calling`・`contact.mail._held`・`contact.mail._inbox`・`contact.mail._next`・`contact.mail._pending`・`contact.mail._ringing`・`contact.mail._unseen` 書ける系: calendar_3・contact
    - `CT1IS` Mailbox._sent(送ったメッセージの既読の数=道具の性質・第 6 期 6-4 C1)(挙動 behavior・復元 required・腕 contact-c1) 道筋 `contact.mail._by_sender`・`contact.mail._sent` 書ける系: calendar_3・contact
- 決定の ID: 10-12/§4-4

## [tools.py](../../../../../../../../src/shibuya/society/contact/tools.py)

engine.contact.tools — 連絡の道具の台帳の行(第 6 期 6-4 C1 の限界・C2・C6=口の約束 1-7・決定 10-12 §4-4 CT0)。

- 公開の関数とクラス
  - `register_into`(関数): ランの道具の台帳に足す(腕 c1 の組み立てだけが呼ぶ)。もうある名は足さない(差し替えない)。足した行の数。
- import している内部モジュール: `shibuya.society.tools.registry`
- 呼び手: `shibuya.interim_bundles.contact.layer`・`shibuya.runtime.systems.assemble`
- 読む試験: `tests/engine/contact/test_c2_habit.py`・`tests/engine/contact/test_c2_runs.py`
- 決定の ID: 10-12/§4-4
