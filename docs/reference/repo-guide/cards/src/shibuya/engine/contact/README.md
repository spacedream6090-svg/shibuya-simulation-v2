# src/shibuya/engine/contact

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 7 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/engine/contact/__init__.py)

engine.contact — 連絡の道具 C1(第 6 期 6-4・決定 10-12 §4-4 CT0〜CT5・CT9・§4-2 TM1・TM3・回答 2-1=GPU の前に腕で)。

- 決定の ID: 10-12/§4-4・R-78

## [book.py](../../../../../../../../src/shibuya/engine/contact/book.py)

engine.contact.book — 宛先(連絡先とグループ)の持ち主(第 6 期 6-4 C1・C2・決定 10-12 §4-4 CT5・口の約束 1-7 の器)。

- 公開の関数とクラス
  - `ContactBook`(クラス): 宛先の持ち主(関係の層・グループの一覧を読む+〔C2〕本人が交換した連絡先・作ったグループ・招待・調べた店の番号)。
- import している内部モジュール: `shibuya.engine.tools.groups`・`shibuya.foundation.arms.contact`・`shibuya.foundation.vocab.contact_flags`・`shibuya.mind.relations.people`
- 呼び手: `shibuya.engine.contact.layer`
- 読む試験: `tests/engine/contact/test_c1_fixes.py`・`tests/engine/contact/test_c1_units.py`・`tests/engine/contact/test_c2_exchange.py`・`tests/engine/contact/test_c2_habit.py`
- 状態台帳の行
  - 持ち主 `contact.book`(`ContactBook`)
    - `CT1B` ContactBook の本人の行動で動く帳(交換した連絡先・作ったグループ・招待・調べた店の番号・第 6 期 6-4 C2)(挙動 behavior・復元 required・腕 contact-c1) 道筋 `contact.book._exchanged`・`contact.book._invites`・`contact.book._made`・`contact.book._made_next`・`contact.book._member_of`・`contact.book._places` 書ける系: calendar_3・contact
    - `CT1M` 連絡の道具の計器(層・チャット・通話・通話の発話の口の計数と分布・通話の切った判断の控え・第 6 期 6-4 C1)(挙動 diag・復元 discardable・腕 contact-c1) 道筋 `contact.book.bodiless_dropped` 書ける系: calendar_3・contact
- 決定の ID: 10-12/§4-4

## [calls.py](../../../../../../../../src/shibuya/engine/contact/calls.py)

engine.contact.calls — 電話の会話(第 6 期 6-4 C1・決定 10-12 §4-4 CT1「TM3 の会話の仕組みがそのまま使える」・§4-2 TM1・TM3)。

- 公開の関数とクラス
  - `CallManager`(クラス): 電話の会話(対面の会話の仕組みそのまま・場所が違うだけ)。
  - `CallSpeechPort`(クラス): 通話の発話の口(発話の口そのまま・道具=通話)。
- import している内部モジュール: `shibuya.engine.conversation`・`shibuya.engine.speech.port`・`shibuya.foundation.arms.contact`・`shibuya.foundation.ports.percept_contact`
- 呼び手: `shibuya.engine.contact.layer`
- 読む試験: `tests/engine/contact/test_c1_event_log_onoff.py`・`tests/engine/contact/test_c1_fixes.py`・`tests/engine/contact/test_c2_video.py`
- 読む試験(道筋で): `tests/tools/test_pkgmove.py`
- 状態台帳の行
  - 持ち主 `contact.calls` の別のクラス `CallManager`(行は `shibuya.engine.conversation` のカードを見る)
  - 持ち主 `contact.speech` の別のクラス `CallSpeechPort`(行は `shibuya.engine.speech.port` のカードを見る)
- 決定の ID: 10-12/§4-4

## [chat_state.py](../../../../../../../../src/shibuya/engine/contact/chat_state.py)

engine.contact.chat_state — チャットの会話の状態(第 6 期 6-4 C1・決定 10-12 §4-2 TM1)。

- 公開の関数とクラス
  - `ChatBook`(クラス): 続いているチャットの状態(会話の器の子・``Session`` の表)。書く口は :meth:`on_message` と :meth:`step` だけ。
  - `group_key`(関数): グループのチャットの鍵(グループの一覧の行の番号)。
  - `pair_key`(関数): 1 対 1 のチャットの鍵(順に依らない)。
- import している内部モジュール: `shibuya.engine.conversation`・`shibuya.foundation.arms.contact`
- 呼び手: `shibuya.engine.contact.layer`
- 読む試験: `tests/engine/contact/test_c1_fixes.py`・`tests/engine/contact/test_c1_units.py`
- 読む試験(道筋で): `tests/tools/test_pkgmove.py`
- 状態台帳の行
  - 持ち主 `contact.chats` の別のクラス `ChatBook`(行は `shibuya.engine.conversation` のカードを見る)
- 決定の ID: 10-12/§4-2

## [deliver.py](../../../../../../../../src/shibuya/engine/contact/deliver.py)

engine.contact.deliver — 届く(エンジン)=メッセージ・電話・既読(第 6 期 6-4 C1・決定 10-12 §4-4 CT3・CT9・§4-2 TM1)。

- 公開の関数とクラス
  - `Mailbox`(クラス): 届いた・送った・予約のメッセージと着信(書く口はこのクラスのメソッドだけ)。
  - `senders_of`(関数): 読んだ行 → 会話ごとの束 ``(鍵の種類 p/g, 相手かグループ, 最後の行の番号)``(出た順・重ねない)。
- import している内部モジュール: `shibuya.foundation.arms.contact`・`shibuya.foundation.ports.percept_contact`・`shibuya.foundation.queues.batching`・`shibuya.foundation.time_consts`
- 呼び手: `shibuya.engine.contact.layer`
- 読む試験: `tests/engine/contact/test_c1_fixes.py`・`tests/engine/contact/test_c1_flow.py`・`tests/engine/contact/test_c1_units.py`・`tests/engine/contact/test_c2_charge.py`・`tests/engine/contact/test_c2_video.py`
- 読む試験(道筋で): `tests/tools/test_pkgmove.py`
- 状態台帳の行
  - 持ち主 `contact.mail`(`Mailbox`)
    - `CT1I` Mailbox(届いた箱・新しく届いた数・網が預かる分・窓の境目の予約・着信と呼び出し・番号・第 6 期 6-4 C1)(挙動 behavior・復元 required・腕 contact-c1) 道筋 `contact.mail._calling`・`contact.mail._held`・`contact.mail._inbox`・`contact.mail._next`・`contact.mail._pending`・`contact.mail._ringing`・`contact.mail._unseen` 書ける系: calendar_3・contact
    - `CT1IS` Mailbox._sent(送ったメッセージの既読の数=道具の性質・第 6 期 6-4 C1)(挙動 behavior・復元 required・腕 contact-c1) 道筋 `contact.mail._by_sender`・`contact.mail._sent` 書ける系: calendar_3・contact
- 決定の ID: 10-12/§4-4

## [layer.py](../../../../../../../../src/shibuya/engine/contact/layer.py)

engine.contact.layer — 連絡の道具 C1 の持ち主と系 ``contact`` の本体(第 6 期 6-4・腕 ``--contact c1``・既定 off)。

- 公開の関数とクラス
  - `ContactLayer`(クラス): 連絡の道具 C1 の持ち主(状態台帳の腕の行 ``CT1*``)。
  - `GatedSalient`(クラス): 門を通した顕著行為の読み口の写し(記憶の系の (c) 気づきが読む ``cell``・``noticed`` だけ)。
  - `audit_causes`(関数): 負の対照の監査: 族 ``連絡`` の出来事のうち、本人の判断の語の原因が判断の呼び(LlmCall・源と番号つき)で、その時刻が
  - `issued_key`(関数)
  - `manifest_fields`(関数): manifest の ``contact_c1``(腕 c1 のランだけ・ほかは ``None``=欄を出さない)。
  - `sys_contact`(関数): 系 contact(刻みの中・腕 c1 のランだけ立つ)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.contact.book`・`shibuya.engine.contact.calls`・`shibuya.engine.contact.chat_state`・`shibuya.engine.contact.deliver`・`shibuya.engine.contact.tools`・`shibuya.engine.conversation`・`shibuya.engine.speech.port`・`shibuya.engine.tools.groups`・`shibuya.foundation.arms.contact`・`shibuya.foundation.journal.log`・`shibuya.foundation.ports.decision`・`shibuya.foundation.ports.percept_contact`・`shibuya.foundation.queues.batching`・`shibuya.foundation.rng`・`shibuya.foundation.time_consts`・`shibuya.foundation.vocab.contact_flags`・`shibuya.foundation.vocab.events`・`shibuya.mind.plan.contact_attention`・`shibuya.mind.plan.contact_habit`・`shibuya.mind.plan.contact_port`・`shibuya.world.body.reactions`・`shibuya.world.things.device`
- 呼び手: `shibuya.engine.run`・`shibuya.engine.systems.build`・`shibuya.engine.systems.table`
- 読む試験: `tests/engine/calendar3/test_ca3_runs.py`・`tests/engine/calendar3/test_ca3_world.py`・`tests/engine/contact/_c1.py`・`tests/engine/contact/_c2.py`・`tests/engine/contact/test_c1_event_log_onoff.py`・`tests/engine/contact/test_c1_fixes.py`・`tests/engine/contact/test_c1_flow.py`・`tests/engine/contact/test_c1_runs.py`・`tests/engine/contact/test_c1_units.py`・`tests/engine/contact/test_c1_world.py`・`tests/engine/contact/test_c2_charge.py`・`tests/engine/contact/test_c2_exchange.py`・`tests/engine/contact/test_c2_habit.py`・`tests/engine/contact/test_c2_runs.py`・`tests/engine/contact/test_c2_video.py`・`tests/engine/time/test_v30a_key_sites.py`
- 読む試験(道筋で): `tests/engine/time/test_t0_rng_key.py`
- 状態台帳の行
  - 持ち主 `contact`(`ContactLayer`)
    - `CT1G` 連絡の層が系の間に渡す値(顕著行為の門を通った気づいた体・仲裁で回した判断・主の判断が選んだ「スマホを見る」・第 6 期 6-4 C1 検収 M1・M5)(挙動 behavior・復元 required・腕 contact-c1) 道筋 `contact._defer`・`contact._defer_charge`・`contact._defer_exchange`・`contact._face_turns`・`contact._look_main`・`contact._sal_noticed`・`contact._sal_step` 書ける系: calendar_3・contact・decide・llm_receive
    - `CT1M` 連絡の道具の計器(層・チャット・通話・通話の発話の口の計数と分布・通話の切った判断の控え・第 6 期 6-4 C1)(挙動 diag・復元 discardable・腕 contact-c1) 道筋 `contact._ct_hist`・`contact._exposed_prev`・`contact._hangup`・`contact._meter` 書ける系: calendar_3・contact・decide
    - `CT1Q` 発行した連絡の判断の呼びの控えと呼び数・出来事の id の診断の表(監査の突き合わせ・calls_by_model・原因の入力・第 6 期 6-4 C1 検収 M2・M5・1-3 の (1) の直し)(挙動 diag・復元 required・腕 contact-c1) 道筋 `contact._ct_event_of`・`contact._issued`・`contact._issued_n` 書ける系: calendar_3・contact
- 書きの許可
  - 系 `contact`(群 連絡・時 `tick`・立つ条件 `contact`・関数 `sys_contact`)
    - 書いてよい外の道筋: `BW:batching.*`・`CA2G:calendar2._turns`・`CA3G:calendar3._reads`・`CT1*:contact.*`・`E:events.*`
- 決定の ID: 10-12/§4-4

## [tools.py](../../../../../../../../src/shibuya/engine/contact/tools.py)

engine.contact.tools — 連絡の道具の台帳の行(第 6 期 6-4 C1 の限界・C2・C6=口の約束 1-7・決定 10-12 §4-4 CT0)。

- 公開の関数とクラス
  - `register_into`(関数): ランの道具の台帳に足す(腕 c1 の組み立てだけが呼ぶ)。もうある名は足さない(差し替えない)。足した行の数。
- import している内部モジュール: `shibuya.engine.tools.registry`
- 呼び手: `shibuya.engine.contact.layer`・`shibuya.engine.systems.build`
- 読む試験: `tests/engine/contact/test_c2_habit.py`・`tests/engine/contact/test_c2_runs.py`
- 読む試験(道筋で): `tests/tools/test_pkgmove.py`
- 決定の ID: 10-12/§4-4
