"""mind.percept.attention — 割る段で ``perception/attention.py`` を割った割り先(全ファイルの表 §4・名の表は
``tools/pkgmove/map.toml`` の割る行)。

中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の
方針は、主な割り先 ``foundation/text/salience.py`` に残した元の docstring を読むこと。
"""

from __future__ import annotations

from typing import Final, Sequence
import numpy as np
from shibuya.foundation.rng import stream

__all__ = [
    "P_SEE_LARGE_VISION", "P_SEE_LARGE_VISION_AUDIO", "P_SEE_LARGE_VISION_SILENT", "P_SEE_MEDIUM_RANGE",
    "P_SEE_MEDIUM_DEFAULT", "p_see", "gate_stage1",
]


# ---------------------------------------------------------------- 段1 到達確率(p_see)
# 〔11-03 棚卸し A §4-1〕棚卸し 10-31 の #34 は錨を「実測帯 0.14〜0.79・日本 0.70」と書くが、実装は帯が 2 つ
# (中小媒体 0.14〜0.40・大型ビジョン 0.63〜0.78・既定 0.70)で 0.79 は無い。棚卸しの写しの側の食い違い(値は変えない)。
#: 大型ビジョンの視認確率(既定・音声条件を指定しないとき)。
P_SEE_LARGE_VISION: Final[float] = 0.70
#: 音声あり。
P_SEE_LARGE_VISION_AUDIO: Final[float] = 0.78
#: 無音。
P_SEE_LARGE_VISION_SILENT: Final[float] = 0.63
#: 中小媒体の帯(英仏流用=expedient・日本の業界標準指標は接触機会 OTS で視認率ではない)。
P_SEE_MEDIUM_RANGE: Final[tuple[float, float]] = (0.14, 0.40)
#: 中小媒体の代表値(帯の中点・expedient)。
P_SEE_MEDIUM_DEFAULT: Final[float] = 0.27


# ---------------------------------------------------------------- 段1
def p_see(
    medium: str = "large_vision",
    *,
    audio: bool | None = None,
) -> float:
    """媒体 → 視認確率(§4 段1)。

    Args:
        medium: ``"large_vision"``(大型ビジョン)または ``"medium_small"``(中小媒体)。
        audio: 大型ビジョンのみ。True=音声有0.78 / False=無音0.63 / None=既定0.70。
    """
    if medium == "large_vision":
        if audio is None:
            return P_SEE_LARGE_VISION
        return P_SEE_LARGE_VISION_AUDIO if audio else P_SEE_LARGE_VISION_SILENT
    if medium == "medium_small":
        return P_SEE_MEDIUM_DEFAULT
    raise ValueError(f"未知の媒体: {medium!r}(large_vision / medium_small)")


def gate_stage1(
    n: int,
    probability: float | np.ndarray,
    *,
    seed: int | str,
    domain_counters: Sequence[int],
) -> np.ndarray:
    """段1 の一発ベルヌーイ(決定論・``core.rng.stream`` のドメイン分離)。

    Args:
        n: 判定件数。
        probability: 到達確率(スカラーまたは ``(n,)``)。
        seed: マスターシード。
        domain_counters: カウンタ(例 ``(agent_id, tick)``)。

    Returns:
        ``(n,)`` bool。通過=True。
    """
    if n <= 0:
        return np.zeros(0, dtype=bool)
    g = stream(seed, "perception.attention.p_see", *[int(c) for c in domain_counters])
    return g.random(n) < np.broadcast_to(np.asarray(probability, dtype=np.float64), (n,))
