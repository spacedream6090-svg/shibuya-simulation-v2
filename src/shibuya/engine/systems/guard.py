"""engine.systems.guard — 系を呼ぶ間だけ置く書きの許可(第 1 期 1-0・草案 §2-6 の A ①・C)。

- SoA: ``core.write_permit.scope(spec.writes.soa)``(解除口が許可の列だけを解く)。
- scratch・buffers: ``SCRATCH_PERMIT``(``TickScratch.__setattr__`` が見る=段 C)。``None`` は制限なし。
- 切替口: ``core.write_permit.set_enabled(False)``(か環境変数 ``SHIBUYA_WRITE_GUARD=off``)で SoA と scratch の両方を外す。

逐次ループ宣言: なし(系 1 回あたり定数回の代入)。
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from shibuya.core import write_permit as _WP

__all__ = ["CURRENT", "SCRATCH_PERMIT", "system_scope"]

#: いま回している系の名(記録と誤りの文の材料・``None``=系の外)。
CURRENT: str | None = None
#: いまの系が書いてよい scratch の欄(``None``=制限なし)。
SCRATCH_PERMIT: frozenset[str] | None = None


@contextmanager
def system_scope(name: str, soa: frozenset[str] | None, scratch: frozenset[str] | None) -> Iterator[None]:
    """系 ``name`` を呼ぶ間だけ SoA と scratch の許可を置く(出るときに前の値へ戻す)。"""
    global CURRENT, SCRATCH_PERMIT
    prev = (CURRENT, SCRATCH_PERMIT)
    CURRENT = name
    if _WP.enabled():
        SCRATCH_PERMIT = None if scratch is None else frozenset(scratch)
    try:
        with _WP.scope(soa):
            yield
    finally:
        CURRENT, SCRATCH_PERMIT = prev
