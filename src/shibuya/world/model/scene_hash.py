"""world.model.scene_hash — 割る段で ``engine/change_detect.py`` を割った割り先(全ファイルの表 §4・名の表は
``tools/pkgmove/map.toml`` の割る行)。

中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の
方針は、主な割り先 ``mind/system1/change_detect.py`` に残した元の docstring を読むこと。
"""

from __future__ import annotations

from typing import Final
import numpy as np
from shibuya.foundation.text import hashes as PH
from shibuya.foundation.text import normalize as PN
from shibuya.foundation.text import templates as PT
from shibuya.world.model.percept_scene import WALKABLE_FRACTION_SYNTHETIC
from shibuya.world.model.assets import CELL_SIZE_M
from shibuya.world.model.state import World

__all__ = [
    "DEFAULT_WALKABLE_AREA_M2", "b4_block_raw", "b4_block_hashes",
]


#: 歩行可能面積が与えられないときの分母[m²](``perception.renderer`` の合成世界と同値)。
DEFAULT_WALKABLE_AREA_M2: Final[float] = CELL_SIZE_M * CELL_SIZE_M * WALKABLE_FRACTION_SYNTHETIC


def b4_block_raw(
    world: World,
    tick: int,
    *,
    walkable_area_m2: np.ndarray | float | None = None,
    noise_stage: np.ndarray | None = None,
    flow: np.ndarray | None = None,
    salient_digest: np.ndarray | None = None,
    los_stage: np.ndarray | None = None,
) -> np.ndarray:
    """セル動的ブロック B4 の**描画欄** ``(n_cells, 4)`` int32(``B4_FIELD_COLUMNS`` の順)。

    知覚契約書 §2.2/§5 の三役は「**描画バイト列**のハッシュ」を要求する。C2 は安い代理として
    「密度段8値・騒音段・営業中POI数」を使っていたが、これは描画の欄と**別物**で、
    描画バイト変化の 48% を取りこぼしていた(``docs/ops/build-report-C3.md`` §2)。
    C3 の結線でこの関数を ``perception.hashes.b4_field_row``(描画がそれ**だけ**に依存する欄)
    へ切り替えた。欄ハッシュはこれで描画バイトの refinement になる。

    Args:
        world: セル状態。
        tick: 現在 tick(騒音の昼夜切替に使う)。
        walkable_area_m2: 密度→人/m² の分母。None なら ``DEFAULT_WALKABLE_AREA_M2``。
        noise_stage: 騒音段(None なら ``world.noise_stage_for_tick(tick)``)。
        flow: 流れ 0-2(None なら 0)。
        salient_digest: 顕著行為ダイジェスト(None なら 0)。
        los_stage: 〔段 5-1b〕密度の段(Fruin の LOS)を外から渡す(nav1 のラン=``world.cells.density_stage``=
            ``NavSpace.per_m2`` の推定と同じ値)。None(legacy)なら ``density ÷ walkable_area_m2`` から。

    Note:
        **営業中POI数は欄から外した**。店が開いても B4 の描画バイトは変わらない
        (営業時間は B2 の看板=セル固定)ので、起床条件 (i)「B4 ハッシュ変化」に載せると
        過検出になる。知覚契約書 §6 (i) の列挙(密度段階の跨ぎ・騒音段階・構造物・
        顕著行為の到達)にも営業中POI数は無い。
    """
    n = world.n_cells
    if los_stage is not None:
        los = np.asarray(los_stage, dtype=np.uint8)
    else:
        area = DEFAULT_WALKABLE_AREA_M2 if walkable_area_m2 is None else walkable_area_m2
        per_m2 = np.asarray(world.cells.density, dtype=np.float64) / np.maximum(
            np.asarray(area, dtype=np.float64), 1.0
        )
        los = PN.peg_stage_array(per_m2, PT.DENSITY_LOS_EDGES_PER_M2)
    ns = world.noise_stage_for_tick(tick) if noise_stage is None else np.asarray(noise_stage)
    fl = np.zeros(n, dtype=np.uint8) if flow is None else np.asarray(flow)
    sal = np.zeros(n, dtype=np.int32) if salient_digest is None else np.asarray(salient_digest)
    return PH.b4_field_row(los, ns, fl, sal)


def b4_block_hashes(raw: np.ndarray, rows: np.ndarray | None = None) -> np.ndarray:
    """B4 描画欄の行ごとの xxh64(``perception.hashes.field_row_hashes`` に委譲)。

    Args:
        raw: ``(n_cells, len(B4_FIELD_COLUMNS))`` int32(C 連続)。
        rows: 計算する行の索引(None なら全行)。

    Returns:
        ``rows`` と同じ長さの uint64 配列。

    Note:
        逐次ループ宣言1: **行数ぶんの xxh64 ループ**(上限=セル数 453/520。
        実装計画書が明示的に許した形)。実体は知覚側にある=**ハッシュの定義は 1 か所**。
    """
    return PH.field_row_hashes(raw, rows)
