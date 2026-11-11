# src/shibuya/society/speech

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 3 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/society/speech/__init__.py)

(冒頭の説明なし)

## [layer.py](../../../../../../../../src/shibuya/society/speech/layer.py)

engine.speech.layer — 発話の口の腕と、会話の番の答えから発話を作って口に通す糸(第 1 期 1-8b)。

- 公開の関数とクラス
  - `arm`(関数): いまの腕(``off``=既定・``on``=発話の口)。組み立てのときに読む。
  - `make_port`(関数): 組み立ての口: 発話の口を作る。口コミの抽出の口 ``wom_fn`` は今の道(``engine.systems.llm_io.utter`` の口コミの段)と
  - `manifest_fields`(関数): manifest の ``speech_port``(腕が off のランは口が無い=観測の子は null)。
  - `set_arm`(関数): 腕を選ぶ(CLI ``--speech-port``・試験の切替口)。組み立ての時に読む(ランの途中で変えても、そのランは変わらない)。
  - `speak_turn`(関数): 会話の番の答え 1 つ → 発話(``Utterance``)→ 口。返り値=目印(発話が無ければ ``None``)。
- import している内部モジュール: `shibuya.foundation.time_consts`・`shibuya.foundation.vocab.actions`・`shibuya.llm.mock`・`shibuya.mind.memory.wom`・`shibuya.society.speech.port`
- 呼び手: `shibuya.cli`・`shibuya.engine.run`・`shibuya.engine.systems.build`・`shibuya.engine.systems.llm_io`
- 読む試験: `tests/engine/speech/_s8b.py`・`tests/engine/speech/test_speech_default_off_invariance.py`・`tests/engine/speech/test_speech_empty_text_errors.py`・`tests/engine/speech/test_speech_on_reaches_addressee.py`・`tests/engine/speech/test_speech_port_schema.py`・`tests/engine/speech/test_wom_from_utterance_roundtrip.py`
- 読む試験(道筋で): `tests/engine/speech/test_speech_writers_ast.py`
- 環境変数: `SHIBUYA_SPEECH_PORT`

## [port.py](../../../../../../../../src/shibuya/society/speech/port.py)

engine.speech.port — 発話の口(第 1 期 1-8b・Q57 (d)・10-03 §6 ⑤・10-12 §4-6 MR11・§4-2 TM3・10-13b §1 1-5)。

- 公開の関数とクラス
  - `SpeechContext`(クラス): 発話の呼び出し(``say`` の ``ctx``)。口は値を解釈しない(書く・届ける・渡すのに使うだけ)。
  - `SpeechPort`(クラス): 発話の口(書く口は ``say`` の 1 つ・読み口は ``take_heard``)。腕 ``--speech-port on`` のランだけ組み立てが作る。
  - `Utterance`(クラス): 発話 1 つ(口が出来事ログに書く前の形=``event_id`` は ``None``・口が付ける)。``mora`` は本文から数える。
  - `mora_count`(関数): 本文のモーラ数(TM3 の入力=発言の長さ=モーラ数 × 話す速さ)。
- import している内部モジュール: `shibuya.foundation.journal.log`・`shibuya.foundation.time_consts`・`shibuya.foundation.types`・`shibuya.foundation.vocab.events`・`shibuya.society.conversation`
- 呼び手: `shibuya.engine.contact.calls`・`shibuya.engine.contact.layer`・`shibuya.engine.speech_clock`・`shibuya.society.speech.layer`
- 読む試験: `tests/engine/clock/test_tm2_talk_clock.py`・`tests/engine/contact/test_c1_event_log_onoff.py`・`tests/engine/speech/test_s8_event_log_onoff.py`・`tests/engine/speech/test_speech_arm_rows_resume.py`・`tests/engine/speech/test_speech_empty_text_errors.py`・`tests/engine/speech/test_speech_modality_field_empty.py`・`tests/engine/speech/test_speech_on_reaches_addressee.py`・`tests/engine/speech/test_speech_port_schema.py`
- 読む試験(道筋で): `tests/engine/speech/test_speech_writers_ast.py`
- 状態台帳の行
  - 持ち主 `contact.speech`(`SpeechPort`)
    - `CT1M` 連絡の道具の計器(層・チャット・通話・通話の発話の口の計数と分布・通話の切った判断の控え・第 6 期 6-4 C1)(挙動 diag・復元 discardable・腕 contact-c1) 道筋 `contact.speech._heard_taken`・`contact.speech._last_input`・`contact.speech._own_last`・`contact.speech.meter` 書ける系: calendar_3・contact
    - `CT1Q` 発行した連絡の判断の呼びの控えと呼び数・出来事の id の診断の表(監査の突き合わせ・calls_by_model・原因の入力・第 6 期 6-4 C1 検収 M2・M5・1-3 の (1) の直し)(挙動 diag・復元 required・腕 contact-c1) 道筋 `contact.speech._mark_event_of` 書ける系: calendar_3・contact
    - `CT1S` CallSpeechPort.inbox(通話の相手の次の番に載る発話・第 6 期 6-4 C1)(挙動 behavior・復元 required・腕 contact-c1) 道筋 `contact.speech.inbox` 書ける系: calendar_3・contact
  - 持ち主 `speech`(`SpeechPort`)
    - `S8` SpeechPort.inbox(届け先 → 未読の発話の列・第 1 期 1-8b)(挙動 behavior・復元 required・腕 speech-port) 道筋 `speech.inbox` 書ける系: decide・llm_receive
    - `S8E` SpeechPort の口の目印 → 出来事の記録の id の診断の表(第 1 期 1-8b・1-3 の (1) の直し)(挙動 diag・復元 required・腕 speech-port) 道筋 `speech._mark_event_of` 書ける系: decide・llm_receive
    - `S8M` SpeechPort の計器・直近の入力の目印・渡した発話の記録の id の控え(第 1 期 1-8b)(挙動 diag・復元 discardable・腕 speech-port) 道筋 `speech._heard_taken`・`speech._last_input`・`speech._own_last`・`speech.meter` 書ける系: decide・llm_receive
- 決定の ID: 09-30・10-03/§6・10-12/§4-6・10-13b/§1
