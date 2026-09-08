"""world: セル/POI/歩行グラフ/可視性(mmap)/騒音場。core に依存。

層契約: docs/design/v2-implementation-plan.md §3(import-linter で強制)。
C2 第2弾で入るのは**資産読み込み+合成小世界**(assets)・**歩行グラフ**(graph)・
**セル/POI 状態レジストリ**(state)。可視性(W8)と騒音場(W10)は C3 以降。
"""

from shibuya.world.assets import (
    BAND_CODES,
    CELL_SIZE_M,
    WorldAssets,
    assets_available,
    load_assets,
    synthetic_assets,
)
from shibuya.world.graph import WalkGraph
from shibuya.world.state import DENSITY_STAGE_EDGES, World

__all__ = [
    "World",
    "WorldAssets",
    "WalkGraph",
    "load_assets",
    "synthetic_assets",
    "assets_available",
    "BAND_CODES",
    "CELL_SIZE_M",
    "DENSITY_STAGE_EDGES",
]
