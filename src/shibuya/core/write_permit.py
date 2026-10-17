"""core.write_permit — 系ごとの「書いてよい SoA の列」(第 1 期 1-0・段 A)。

``AgentState``・``World``・``PerceptionState`` の解除口(``writable()`` の中の解除)は、ここに置いた**いまの許可**を見て、
許可の列だけを書き込み可能にする(ほかの列は読み取り専用のまま)。許可は進行役(``engine.systems.conductor.run_system``)が
系を呼ぶ間だけ置く。許可が無い(``None``)とき=組み立て・系の外・切替口で外したときは、今までどおり全部の列を解く。

- 鍵は状態台帳の SoA の鍵と同じ語彙(``"agents.cell"``・``"cells.b4_hash"``・``"pois.stock"``・``"perception.heading"``)。
- 切替口: 環境変数 ``SHIBUYA_WRITE_GUARD=off`` か ``set_enabled(False)``(既定は入れる=草案 §0-2 の親の決め)。外すと
  許可を置かない=今までと同じ全部の解除。結果(final・テープ)はどちらでも同じ(書きの検査は書く値を変えない)。
- ``numpy`` の ``ufunc.at`` は書き込みの旗を見ないので、resolve の ``_require_thawed`` が書く配列ごとに旗を見る(同じ段 A)。

層: ``core`` は何にも依存しない(agents・world・perception がここを読む)。
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

__all__ = ["allows", "current", "enabled", "scope", "set_enabled"]

#: いまの許可(``None``=制限なし)。進行役が系を呼ぶ間だけ置く。
_PERMIT: frozenset[str] | None = None
#: 切替口(既定は入れる)。
_ENABLED: bool = os.environ.get("SHIBUYA_WRITE_GUARD", "on").strip().lower() not in ("off", "0", "false", "no")


def enabled() -> bool:
    """書きの検査(段 A の ①)が入っているか。"""
    return _ENABLED


def set_enabled(flag: bool) -> None:
    """書きの検査を入れる/外す(試験と重さの測り用の切替口)。"""
    global _ENABLED
    _ENABLED = bool(flag)


def current() -> frozenset[str] | None:
    """いまの許可(``None``=制限なし)。"""
    return _PERMIT


def allows(place: str, name: str) -> bool:
    """置き場 ``place`` の列 ``name`` を解いてよいか(許可が無ければ常に真)。"""
    p = _PERMIT
    return p is None or f"{place}.{name}" in p


@contextmanager
def scope(keys: frozenset[str] | None) -> Iterator[None]:
    """``with scope(許可):`` の間だけ許可を置く(切替口で外していれば置かない)。入れ子は内側が勝ち、出るときに戻す。"""
    global _PERMIT
    prev = _PERMIT
    if _ENABLED:
        _PERMIT = None if keys is None else frozenset(keys)
    try:
        yield
    finally:
        _PERMIT = prev
