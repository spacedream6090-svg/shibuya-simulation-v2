"""engine.rules — 規則の表(第 1 期 1-4・CP10・決定 10-12 §1-12)。

- ``table``: ``Rule``(出典と版つきの 1 行)・``Rules.get(id, asof)``(asof の日に効いている版)・``rules_version``
  (表の sha=manifest と日次の記録の欄)。1-4 では読み手を作らない(中身は 4-2)。

逐次ループ宣言: なし。
"""
