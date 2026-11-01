"""engine.tools — 道具の台帳 C0(第 1 期 1-7・CT0・CT5・CT9・CT10)。

- ``registry``: 道具の台帳(``Tool``・``ToolRegistry``・最初の中身 ``DEFAULT_TOOLS``)。
- ``contacts``: 個人の連絡先の手段ごとの印(関係の記憶の ``RelationLayer.contact_flags`` の値の作り方と数え方)。
- ``groups``: グループの一覧(家族=W16 の世帯・職場=W16 の事業所=W6 の組織)。
- ``places``: 店の番号の場所の表(C0 は空の表・読み口 ``phone_of``)。
- ``record``: 記録の欄(CT9)の口=看板を読んだ出来事に「作り物」の印(腕・既定 off)と manifest の ``tools``。

C0 は器だけ(既定の final・behavior-hash・テープ・描画は動かない)。中身を使う段は第 6 期の C1〜(計画 6-4)。
ここでは下のモジュールを import しない(``engine.relations`` が ``contacts`` を読むので、循環を作らない)。
"""
