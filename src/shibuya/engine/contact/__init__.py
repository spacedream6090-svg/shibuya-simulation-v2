"""engine.contact — 連絡の道具 C1(第 6 期 6-4・決定 10-12 §4-4 CT0〜CT5・CT9・§4-2 TM1・TM3・回答 2-1=GPU の前に腕で)。

腕 ``--contact c1``(環境変数 ``SHIBUYA_CONTACT``・既定 ``off``=今のまま=層を作らない)。中身は 1 対 1 のメッセージ・グループの
メッセージ・電話・チャットの会話の状態・目と心の向き(記録 ``docs/bench/analysis/wallbounce-1012/ct_c1/README.md``)。

- ``arm``: 腕と下の腕(割り込めなかった出来事の載せ方 (i)(ii)(iii)・送る文の腕 (b)(c))。
- ``device``: 道具の状態(電池・電波・マナーモード・かばんの中・イヤホン)と通知の刺激の形(R-78 の SNR の形)。
- ``attention``: 目の向き(視線の先)と心の向き(関心の的)・周辺視の粗い気配(Percept の形を変える)・割り込みの門。
- ``port``: 本人の判断(候補の口 J0 の形=今読む/後で/無視・スマホを見る・宛先・返す・出る/出ない・切る)の仮のモデル(mock)と
  文の口(mock は定型の文)・習慣の口(本段は判断の口に戻すだけ)。
- ``deliver``: 届く(エンジン)=メッセージは送った時刻に・電話と打ち終わりの送信は窓の境目(3-2)に・既読は道具の性質。
- ``chat_state``: チャットの会話の状態(``engine.conversation`` の ``Session``・``ConvState`` と同じ形)。
- ``calls``: 電話の会話(``engine.conversation.ConversationManager`` をそのまま使う子クラス)と通話の発話の口
  (``engine.speech.port.SpeechPort`` の子クラス)。
- ``book``: 宛先(連絡先=関係の記憶の手段ごとの印・グループの一覧=1-7 の器)。
- ``layer``: 持ち主 ``ContactLayer``(状態台帳の腕の行 ``CT1*``)・系 ``contact`` の本体・計器・manifest の ``contact_c1``。

ここでは下のモジュールを import しない(読み込みを軽く保つ=組み立てが要るときだけ読む)。
"""
