"""foundation.vocab.relations — 割る段で ``engine/relations.py`` を割った割り先(全ファイルの表 §4・名の表は
``tools/pkgmove/map.toml`` の割る行)。

中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の
方針は、主な割り先 ``mind/relations/layer.py`` に残した元の docstring を読むこと。
"""

from __future__ import annotations

from typing import Final, NamedTuple
import numpy as np

__all__ = [
    "REL_K", "REL_MODES", "REL_KINDS", "REL_KIND_NAMES", "REL_D", "REL_TAU", "REL_TAU_V1", "REL_TAU_BY_TENURE_HASH",
    "DEFAULT_REL_TENURE_HASH", "REL_S", "REL_TENURE_WEEKS", "REL_ROW_BYTES_ACTUAL", "REL_ROW_BYTES_DECLARED",
    "REL_INIT_DENSITIES", "REL_ORIGINS", "RelationEdges", "InitialEdges",
]


#: 体あたりの辺の数(R1 (a)・Dunbar の 15 層・感度 5/50)。
REL_K: Final[int] = 15
REL_MODES: Final[tuple[str, ...]] = ("off", "on")
#: 辺の種別(R1 (a))。
REL_KINDS: Final[dict[str, int]] = {"household": 1, "work": 2, "school": 3, "regular": 4, "acquaintance": 5}
REL_KIND_NAMES: Final[dict[int, str]] = {v: k for k, v in REL_KINDS.items()}
#: 減衰(記憶と同じ既決値・感度 0.25/0.75)。
REL_D: Final[float] = 0.5
#: 辺として残る A の閾値 τ_rel(**較正対象**・第300 訂正=8b′ で再逆算): 在職期間 T_uv を散らし、n を「共在の
#: あった日数」で数えた機械的初期化(``initial_edges``・上限 13 週)を W16+W17 の全母集団(390,067 体)にかけたときの
#: 「体ごとの 15 番目の辺の A」の中央値=**−2.3454**(ラン開始時・15 本の体 54.5%・1 日の終わり −2.4075)を小数 3 桁で
#: 切り下げて **−2.346**(=ラン開始時に中央 15 本が残る値・感度 ±0.5)。8a の −1.1(A が 13 段の階段)・8b の 0.704
#: (n を 15 分枠で数えた=会話 1 回の辺と単位が違った)は置き換え。過程と τ の曲線は記録
#: ``docs/bench/analysis/c10-relations-2026-09-28/`` §8b′。
REL_TAU_V1: Final[float] = -2.346
#: 第2波 §2A 項 2(Q111 の解析で見つかった欠陥の修正): 在職期間の U を同点の順のハッシュと独立にした(``v2``)
#: うえで、8b′ と同じ手順(全母集団・``initial_edges(tau=None)``・ラン開始時の「体ごとの 15 番目の辺の A」の
#: 中央値を小数 3 桁で切り下げ)で再逆算した値。値と手順は記録 ``docs/bench/analysis/wave2-2026-09-30/`` §2A-2。
REL_TAU_V2: Final[float] = -2.322
#: 在職期間のハッシュの版 → 既定の τ_rel(``v1``=旧=−2.346 のまま・``v2``=修正後の再逆算)。
REL_TAU_BY_TENURE_HASH: Final[dict[str, float]] = {"v2": REL_TAU_V2, "v1": REL_TAU_V1}
#: 既定の τ_rel(既定の在職期間ハッシュ ``v2`` の値)。
REL_TAU: Final[float] = REL_TAU_V2
#: 強さ P のロジスティックの幅(M17 の宣言と同じ)。
REL_S: Final[float] = 0.25
#: 初期辺の**在職期間 T_uv の上限**[週](第299 Q89/Q90): 辺ごとに組の hash で 1〜13 週に一様に散らす
#: (expedient・感度腕 26 週)。n=共在のあった日数/週 × T_uv(第300 訂正=1 日 1 本)・first=−T_uv。
REL_TENURE_WEEKS: Final[float] = 13.0
DEFAULT_REL_TENURE_HASH: Final[str] = "v2"
#: 1 辺の実バイト(4+1+1+4+4+2)と宣言バイト(同じ)。
REL_ROW_BYTES_ACTUAL: Final[int] = 16
REL_ROW_BYTES_DECLARED: Final[int] = 16
#: 初期網の密度の腕(×0.5=共在が中央値より長い組だけ・×1=共在 > 0・×2=共在 0 の組織/学校の組も入れる)。
REL_INIT_DENSITIES: Final[tuple[float, ...]] = (0.5, 1.0, 2.0)
#: 会話の起点の種別(8b 診断行): 招待=自分で会話を選んだ・偶然=相手が 2 m 内の知人・知人出現=その起床の呼。
REL_ORIGINS: Final[tuple[str, ...]] = ("invite", "chance", "acquaintance")


class RelationEdges(NamedTuple):
    """1 体の生きている辺(A ≥ τ_rel・A の降順)。"""

    partner: np.ndarray
    kind: np.ndarray
    sign: np.ndarray
    A: np.ndarray
    P: np.ndarray       # 強さ 0..255(uint8)
    row: np.ndarray


class InitialEdges(NamedTuple):
    """機械的初期化の辺(体の行番号の組・有向)と監査の材料。"""

    u: np.ndarray
    v: np.ndarray
    kind: np.ndarray
    n: np.ndarray
    first: np.ndarray
    last: np.ndarray
    minutes: np.ndarray
    audit: dict


def _activation(n: np.ndarray, first: np.ndarray, tick: int, minutes_per_tick: float, d: float) -> np.ndarray:
    nn = np.asarray(n, dtype=np.float64)
    L = np.maximum(0.0, (int(tick) - np.asarray(first, dtype=np.float64)) * float(minutes_per_tick))
    with np.errstate(divide="ignore"):
        return np.log(nn / (1.0 - float(d))) - float(d) * np.log(L + 1.0)


#: 初期辺の同点(共在の分が同じ相手)の決め方。``hash``=体の元 id の組の混ぜ合わせ(既定・決定論・seed に依らない)・
#: ``id``=相手の行番号の小さい方(8a の初版=大組織で行番号の小さい体に入次数が集まる=390,067 体で最大 1,090)。
REL_TIEBREAKS: Final[tuple[str, ...]] = ("hash", "id")
