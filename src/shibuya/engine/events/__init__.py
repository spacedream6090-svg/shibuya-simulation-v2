"""engine.events — 出来事の記録(第 1 期 1-3・CP12・CT9・5W1H)。

- ``log``: ``Event``・原因の 3 型(``LlmCall``・``Process``・実験の条件)・``EventLog``(書く口は ``append`` の 1 つ)。
- ``vocab``: ``what`` の語彙表(閉じた表)・``via``(CT9)・``where`` の種類。
- ``links``: 既存の記録(ActualLog)の行に出来事の id の目印を付ける口。

実験の条件の原因は ``engine/experiment/gate.py`` の ``admit`` だけが作る(CP12)。ここからは再輸出しない。

逐次ループ宣言: なし。
"""
