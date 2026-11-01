"""engine.speech — 発話の口(第 1 期 1-8b・Q57 (d)・10-03 §6 ⑤・10-13b §1 1-5)。

- ``port``: ``Utterance``(発話 1 つ)・``SpeechContext``(その発話の呼び出し)・``SpeechPort.say``(書く口 1 つ=出来事ログに
  1 回・相手の次の入力に載せる・口コミの抽出に渡す)・``mora_count``(本文のモーラ数=TM3 の入力)。
- ``layer``: 腕 ``--speech-port {off,on}``(既定 off)・会話の番の答えから発話を作って口に通す糸(``speak_turn``)・manifest の
  ``speech_port``。

逐次ループ宣言: なし。
"""
