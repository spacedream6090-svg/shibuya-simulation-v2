# src/shibuya/runtime/clocks

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 5 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/runtime/clocks/__init__.py)

(冒頭の説明なし)

## [owner_guard.py](../../../../../../../../src/shibuya/runtime/clocks/owner_guard.py)

engine.owner_guard — 外の状態の持ち主の実行時の守り(第 6 期 6-3 検収 M2・3-2 の ``WindowQueue`` と同じ形を共通の口に)。

- 公開の関数とクラス
  - `closed`(関数): ``obj`` の欄を書けない間(書く口の中から外のコード=処理の関数を呼ぶ間)。
  - `frozen_array`(関数): 配列に書けない印を付けて返す(持ち主が新しい配列で置き換える)。
  - `guarded_delattr`(関数)
  - `guarded_setattr`(関数)
  - `hidden`(関数): 持ち主の中身を書く辞書(無ければ作る)。持ち主の書く口の中だけで使う。
  - `writing`(関数): ``obj`` の欄を書ける間(入れ子可)。
- 呼び手: `shibuya.runtime.clocks.regional`・`shibuya.runtime.clocks.speech`・`shibuya.runtime.clocks.step_scope`

## [regional.py](../../../../../../../../src/shibuya/runtime/clocks/regional.py)

engine.regional_clock — 場所ごとの時計(第 6 期 6-3 時計の段 T4・TM1・腕 ``--clock regional``)。

- 公開の関数とクラス
  - `RegionalClock`(クラス): 場所ごとの時計(状態台帳の腕の行 ``T4W``・持ち主の名 ``clock``)。腕 regional のランだけ進行役が作る。
  - `arm`(関数): いまの腕(``global``=既定・``regional``・``mixed``=口だけ)。進行役と組み立てが読む。
  - `clock_kind`(関数): TM9 の欄 ``clock_kind``(区域ごとの時計の持ち主があれば ``regional``・無ければ今の ``steps``)。
  - `is_default`(関数)
  - `make`(関数): 進行役の口: 腕 regional のときだけ区域ごとの時計を作る(既定 global は None・mixed は止める=口だけ)。
  - `manifest_fields`(関数): manifest の ``clock``(腕 regional のランだけ・既定の腕は None=節を出さない)。
  - `region_of_cells`(関数): セル → 区域の番号(int64・0 から)と作り方の名。重心を 500 m の格子で塊にする(格子の (x, y) の昇順に番号)。
  - `set_arm`(関数): 腕を選ぶ(CLI ``--clock``・試験の切替口)。ランの始めに読む。
- import している内部モジュール: `shibuya.foundation.time_consts`・`shibuya.runtime.clocks.owner_guard`
- 呼び手: `shibuya.cli`・`shibuya.engine.run`・`shibuya.runtime.systems.assemble`・`shibuya.runtime.systems.conductor`・`shibuya.runtime.systems.state_io`
- 読む試験: `tests/engine/clock/test_tm4_regional_clock.py`
- 状態台帳の行
  - 持ち主 `clock`(`RegionalClock`)
    - `T4W` RegionalClock の区域ごとの窓・区域の事象・体の区域の写し・遅刻の日の表・計器(第 6 期 6-3 T4)(挙動 diag・復元 discardable・腕 clock-regional) 道筋 `clock._rc_events`・`clock._rc_head`・`clock._rc_late`・`clock._rc_meter`・`clock._rc_seq`・`clock._rc_snap` 書ける系: decide・llm_receive
- 環境変数: `SHIBUYA_CLOCK`
- 決定の ID: 10-12/§4-2・R-73

## [speech.py](../../../../../../../../src/shibuya/runtime/clocks/speech.py)

engine.speech_clock — 会話の時計(第 6 期 6-3 時計の段 T2・TM3・腕 ``--talk-clock mora``)。

- 公開の関数とクラス
  - `ChatTiming`(クラス): 打つ道具(``チャット``)の時間=C1(チャットの会話の状態)が刺す口。値は空欄(None)=C1 で入れる。
  - `QueueRouter`(クラス): 全体で 1 つの時計(``engine.batching.WindowQueue``)に発言の事象を置く口(区域ごとの時計は
  - `SpeechTiming`(クラス): 話す道具(``対面``)の時間: 発言の長さ = モーラ数 × モーラの長さ × 揺れ × 相手の項・間 = 日本語の平均。
  - `TalkClock`(クラス): 会話の時計(状態台帳の腕の行 ``TCR``・``TCC``・持ち主の名 ``talk_clock``)。腕 ``mora`` のランだけ組み立てが作る。
  - `arm`(関数): いまの腕(``table``=既定・``mora``)。組み立てのときに読む。
  - `is_default`(関数)
  - `language_of`(関数): 本文の言語(仮名か漢字がある=``ja``・英数字だけ=``other``・どちらも無い=``none``)。
  - `make`(関数): 組み立ての口: 腕 mora のときだけ会話の時計を作る(既定 table は None=今の道)。
  - `manifest_fields`(関数): manifest の ``talk_clock``(腕 mora のランだけ・既定の腕は None=節を出さない)。
  - `person_mora_len_s`(関数): 体 ``agent`` のモーラの長さ[秒]\(規則 2=切った対数正規・母集団の seed と体の番号の Philox・状態を持たない)。
  - `set_arm`(関数): 腕を選ぶ(CLI ``--talk-clock``・試験の切替口)。組み立ての時に読む(ランの途中で変えてもそのランは変わらない)。
  - `utterance_jitter`(関数): 発言ごとの揺れ(規則 3=平均 1 の対数正規・CV 0.42)。鍵=話し手・発言を作った時刻[ns]・会話の番号(TM7 (d))。
- import している内部モジュール: `shibuya.foundation.rng`・`shibuya.foundation.time_consts`・`shibuya.foundation.vocab.actions`・`shibuya.runtime.clocks.owner_guard`・`shibuya.society.speech.port`
- 呼び手: `shibuya.cli`・`shibuya.engine.run`・`shibuya.runtime.systems.assemble`・`shibuya.runtime.systems.conductor`
- 読む試験: `tests/engine/clock/test_tm2_talk_clock.py`・`tests/engine/clock/test_tm4_regional_clock.py`
- 状態台帳の行
  - 持ち主 `talk_clock`(`TalkClock`)
    - `TCC` TalkClock の会話の時計・予約した発言・計器(第 6 期 6-3 T2)(挙動 diag・復元 discardable・腕 talk-clock) 道筋 `talk_clock._tc_line`・`talk_clock._tc_meter`・`talk_clock._tc_pending` 書ける系: conversation・decide・llm_receive
    - `TCR` TalkClock の話す速さの控え(体 → モーラの長さ・第 6 期 6-3 T2)(挙動 diag・復元 discardable・腕 talk-clock) 道筋 `talk_clock._tc_rate` 書ける系: decide・llm_receive
- 環境変数: `SHIBUYA_TALK_CLOCK`
- 決定の ID: 10-12/§4-2・R-73・R-73 #30・R-73 #32・R-111・R-111 #38・R-111 #42・R-111 #44

## [step_scope.py](../../../../../../../../src/shibuya/runtime/clocks/step_scope.py)

engine.step_scope — 何かあった体だけ(第 6 期 6-3 時計の段 T3・腕 ``--step-scope changed``)。

- 公開の関数とクラス
  - `StepScope`(クラス): 何かあった体の印(状態台帳の腕の行 ``T3M``・持ち主の名 ``step_scope``)。腕 changed のランだけ組み立てが作る。
  - `arm`(関数): いまの腕(``all``=既定・``changed``)。組み立てのときに読む。
  - `is_default`(関数)
  - `make`(関数): 組み立ての口: 腕 changed のときだけ印の持ち主を作る(既定 all は None=今の道)。
  - `manifest_fields`(関数): manifest の ``step_scope``(腕 changed のランだけ・既定の腕は None=節を出さない)。
  - `set_arm`(関数): 腕を選ぶ(CLI ``--step-scope``・試験の切替口)。組み立ての時に読む。
- import している内部モジュール: `shibuya.engine.change_detect`・`shibuya.runtime.clocks.owner_guard`
- 呼び手: `shibuya.cli`・`shibuya.engine.run`・`shibuya.runtime.systems.assemble`
- 読む試験: `tests/engine/clock/test_tm3_step_scope.py`
- 状態台帳の行
  - 持ち主 `step_scope`(`StepScope`)
    - `T3M` StepScope の変化の印(内受容の値と段の写し・前に跨いだ体・計器・第 6 期 6-3 T3)(挙動 diag・復元 discardable・腕 step-scope) 道筋 `step_scope._ss_copy`・`step_scope._ss_crossed`・`step_scope._ss_meter` 書ける系: detect
- 環境変数: `SHIBUYA_STEP_SCOPE`
- 決定の ID: 10-12/§4-2
