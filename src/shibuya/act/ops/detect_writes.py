"""act.ops.detect_writes — 割る段で ``engine/resolve.py`` を割った割り先(全ファイルの表 §4・名の表は
``tools/pkgmove/map.toml`` の割る行)。

中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の
方針は、主な割り先 ``act/apply.py`` に残した元の docstring を読むこと。
"""

from __future__ import annotations

from shibuya.mind.system1.change_detect import DetectResult
from shibuya.world.model.state import World

__all__ = [
    "write_b4_hash",
]


# ---------------------------------------------------------------- 変化検出の書き戻し
def write_b4_hash(world: World, result: DetectResult) -> None:
    """``change_detect`` が返した新しい B4 ハッシュを書き込む(世界の欄 ``cells.b4_hash``)。"""
    with world.writable():
        if result.changed_cells.size:
            world.cells.b4_hash[result.changed_cells] = result.changed_b4_hash
