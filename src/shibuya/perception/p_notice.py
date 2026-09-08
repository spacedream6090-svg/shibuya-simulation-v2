"""perception.p_notice — 人物③「顕著な行為」への確率的到達(知覚契約書 §3.1・案B 2段ヒル型)。

正典(§3.1 逐語)
- **一次検出**(目標捕捉の標準式 TTPF=Sandia SAND2015-6368 式(2)(3)):
  ``s = d50_eff/d``・``E = 2.7 + 0.7 s``・``P1 = s^E/(1+s^E)``。
  ``d50_eff = d50(事象クラス) × m_light × m_ecc × m_density``。
  ``m_light`` = 昼1.0/夜0.68(Fotios 8.9/13.0)、``m_ecc = E2/(E_ang+E2)``(E2=6.22°・
  ``|E_ang|>110°`` で 0 = 背後は一次視覚ゼロ)、``m_density`` = 疎1.0/中0.5/密0.2。
  ``P1' = P1 × m_load``(歩きスマホ0.46・会話1.0・手空き1.0)。**動く事象は d50 を1.5倍**。
- **二次検出(社会伝播)**: ``P2 = 0.92·N^1.05/(1.2^1.05+N^1.05)``(Milgram 1969 データへの
  ヒル型フィット・N=**半径15 m 内で当該 tick に既に気づいた人数**)。
- **合成**: ``p = 1−(1−P1')(1−P2)``。**発生 tick での一発ベルヌーイ**
  (毎tickハザード累積は誤り=Wood & Simons 2019)。
- **打ち切り 80 m**(±1リング=9セル)。
- 検算表(d50=40 m・前方・昼・疎・手空き): 10 m 0.9995 / 20 m 0.945 / 40 m 0.500 /
  60 m 0.217 / 80 m 0.108 / 100 m 0.061 / 200 m 0.010 → ``tests/perception/test_p_notice.py``。
- **ablation**: A0 定数0.54(Simons & Chabris)→A1+距離→A2+負荷・照明→A3+偏心・密度→
  A4+社会伝播(=完成形)。
- **性能予算(§3.1/§7 P7)**: 「イベント時のベクトル演算1回=約10 ops/体×近傍在席者
  (~26,000体)=**0.26 MOPS/イベント**」・顕著イベント**上限200/tick**・
  追加状態=向き量子化1 byte+課題従事フラグ1 byte=**2 byte/体**(M12)。

逐次ループ宣言(P4)
- **なし**(全て NumPy のベクトル演算。近傍計数も一様格子+``searchsorted``+``bincount`` で
  ループを持たない)。イベント数ぶんの呼び出しは呼び出し側(``EventBudget`` が 200/tick で切る)。

expedient(本モジュール分・§3.1 の「expedient明示」を写したもの)
- ``d50=40 m``(Fotios 注視距離を Johnson の検出:認識=1:4 で外挿)
- ``m_density``(クラッタで N50 が 0.5→2.5 になる写像)
- 打ち切り ``80 m``
- ``m_load``(Hyman は距離/密度を統制していない)
- 社会項の適用半径 ``15 m``
- **本モジュール独自の expedient**: ①「一発ベルヌーイ」を一次→二次の**2段抽選**として実装した
  (合成確率 ``1−(1−P1')(1−P2)`` と数学的に等価。N が一次検出の結果に依存するため、
  1つの一様乱数では書けない)。②社会項の近傍計数は一様格子(格子辺=15 m)+厳密距離判定だが、
  対の総数が ``max_pairs`` を超える超高密度では 3×3 バケット計数×面積比 ``πr²/(9r²)`` へ
  退避する(退避回数は counters に載る)。③向きの量子化=16 セクタ(22.5°刻み・1 byte)。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Final

import numpy as np

from shibuya.core.rng import stream

__all__ = [
    "D50_DEFAULT_M",
    "CUTOFF_M",
    "E2_DEG",
    "ECC_CUTOFF_DEG",
    "M_LIGHT_DAY",
    "M_LIGHT_NIGHT",
    "M_DENSITY",
    "M_LOAD",
    "MOVING_D50_MULTIPLIER",
    "SOCIAL_RADIUS_M",
    "SOCIAL_A",
    "SOCIAL_B",
    "SOCIAL_N50",
    "A0_CONSTANT",
    "MAX_EVENTS_PER_TICK",
    "HEADING_SECTORS",
    "TaskLoad",
    "DensityClass",
    "Ablation",
    "PNoticeParams",
    "NoticeResult",
    "Counters",
    "EventBudget",
    "heading_to_degrees",
    "eccentricity_deg",
    "p1_primary",
    "p2_social",
    "combine",
    "notice_event",
    "social_counts",
]

# ---------------------------------------------------------------- 係数(§3.1)
#: 事象クラス既定の d50[m](expedient)。
D50_DEFAULT_M: Final[float] = 40.0
#: 打ち切り距離[m](expedient・±1リング=9セル)。
CUTOFF_M: Final[float] = 80.0
#: TTPF の指数式(mechanism・Sandia SAND2015-6368 式(2)(3))。
TTPF_E_BASE: Final[float] = 2.7
TTPF_E_SLOPE: Final[float] = 0.7
#: 偏心の半減角 E2[度](mechanism・視覚の偏心スケーリング)。
E2_DEG: Final[float] = 6.22
#: 背後判定[度](|E_ang| がこれを超えると一次視覚ゼロ)。
ECC_CUTOFF_DEG: Final[float] = 110.0
#: 照明係数(Fotios 昼13.0 m/夜8.9 m → 0.68)。
M_LIGHT_DAY: Final[float] = 1.0
M_LIGHT_NIGHT: Final[float] = 0.68
#: 密度係数(疎/中/密・expedient)。
M_DENSITY: Final[tuple[float, float, float]] = (1.0, 0.5, 0.2)
#: 負荷係数(手空き/歩きスマホ/会話・expedient)。
M_LOAD: Final[tuple[float, float, float]] = (1.0, 0.46, 1.0)
#: 動く事象の d50 倍率(動標的の N50=静止の 2/3 → d50 は 1.5 倍側)。
MOVING_D50_MULTIPLIER: Final[float] = 1.5
#: 社会伝播の適用半径[m](expedient)。
SOCIAL_RADIUS_M: Final[float] = 15.0
#: 社会伝播ヒル型のパラメータ(Milgram 1969 データへのフィット)。
SOCIAL_A: Final[float] = 0.92
SOCIAL_B: Final[float] = 1.05
SOCIAL_N50: Final[float] = 1.2
#: ablation A0 の定数(Simons & Chabris の全体値)。
A0_CONSTANT: Final[float] = 0.54
#: 顕著イベントの 1 tick 上限(§3.1 宣言値・§7 P7)。
MAX_EVENTS_PER_TICK: Final[int] = 200
#: 向きの量子化セクタ数(1 byte・22.5°刻み)。
HEADING_SECTORS: Final[int] = 16


class TaskLoad(IntEnum):
    """課題従事フラグ(``m_load`` の索引・M12 の 1 byte)。"""

    FREE = 0  # 手空き
    PHONE = 1  # 歩きスマホ
    TALKING = 2  # 会話


class DensityClass(IntEnum):
    """密度クラス(``m_density`` の索引)。"""

    SPARSE = 0  # 疎
    MEDIUM = 1  # 中
    DENSE = 2  # 密


class Ablation(IntEnum):
    """§3.1 の ablation A0-A4(A4=完成形)。"""

    A0_CONSTANT = 0  # 定数 0.54
    A1_DISTANCE = 1  # +距離
    A2_LOAD_LIGHT = 2  # +負荷・照明
    A3_ECC_DENSITY = 3  # +偏心・密度
    A4_SOCIAL = 4  # +社会伝播(既定)


@dataclass(frozen=True)
class PNoticeParams:
    """§3.1 の係数一式(ablation で振るのはこの dataclass を差し替える)。"""

    d50_m: float = D50_DEFAULT_M
    cutoff_m: float = CUTOFF_M
    e2_deg: float = E2_DEG
    ecc_cutoff_deg: float = ECC_CUTOFF_DEG
    m_light_night: float = M_LIGHT_NIGHT
    m_density: tuple[float, float, float] = M_DENSITY
    m_load: tuple[float, float, float] = M_LOAD
    moving_multiplier: float = MOVING_D50_MULTIPLIER
    social_radius_m: float = SOCIAL_RADIUS_M
    social_a: float = SOCIAL_A
    social_b: float = SOCIAL_B
    social_n50: float = SOCIAL_N50
    ablation: Ablation = Ablation.A4_SOCIAL
    #: 社会項の厳密近傍計数を許す対の総数(超えたらバケット近似へ退避)。
    max_pairs: int = 4_000_000


@dataclass
class Counters:
    """診断行に出す計数(§6 運用規定「診断行に常設」)。"""

    events: int = 0
    events_over_cap: int = 0
    candidates: int = 0
    noticed_primary: int = 0
    noticed_social: int = 0
    social_approx_fallbacks: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "events": self.events,
            "events_over_cap": self.events_over_cap,
            "candidates": self.candidates,
            "noticed_primary": self.noticed_primary,
            "noticed_social": self.noticed_social,
            "social_approx_fallbacks": self.social_approx_fallbacks,
        }


@dataclass(frozen=True)
class NoticeResult:
    """1イベント×候補群の結果。

    Attributes:
        index: 打ち切り 80 m 内に残った候補の**元配列の索引**(昇順)。
        distance_m: その候補までの距離[m]。
        p1: 一次検出確率 ``P1'``。
        p2: 二次検出確率 ``P2``。
        p: 合成確率 ``1−(1−P1')(1−P2)``。
        noticed: 気づいた候補の bool。
        noticed_primary: 一次で気づいた bool(社会項の N の素)。
        social_n: 各候補の半径15 m 内の既気づき人数。
    """

    index: np.ndarray
    distance_m: np.ndarray
    p1: np.ndarray
    p2: np.ndarray
    p: np.ndarray
    noticed: np.ndarray
    noticed_primary: np.ndarray
    social_n: np.ndarray

    @property
    def n_candidates(self) -> int:
        return int(self.index.size)

    @property
    def n_noticed(self) -> int:
        return int(np.count_nonzero(self.noticed))

    def noticed_ids(self) -> np.ndarray:
        """気づいた候補の元索引。"""
        return self.index[self.noticed]


class EventBudget:
    """顕著イベントの 1 tick 上限(§3.1「顕著イベント上限200/tick(宣言値)」)。

    Example:
        >>> b = EventBudget()
        >>> b.admit(1)
        True
    """

    def __init__(self, cap: int = MAX_EVENTS_PER_TICK) -> None:
        self.cap = int(cap)
        self.tick: int | None = None
        self.used = 0
        self.counters = Counters()

    def start_tick(self, tick: int) -> None:
        """新しい tick を開始する(使用量をリセット)。"""
        self.tick = int(tick)
        self.used = 0

    def admit(self, tick: int) -> bool:
        """このイベントを処理してよいか。上限超過なら False(計数して捨てる)。"""
        if self.tick != int(tick):
            self.start_tick(tick)
        if self.used >= self.cap:
            self.counters.events_over_cap += 1
            return False
        self.used += 1
        self.counters.events += 1
        return True


# ---------------------------------------------------------------- 幾何
def heading_to_degrees(heading_u8: np.ndarray, sectors: int = HEADING_SECTORS) -> np.ndarray:
    """量子化された向き(0..sectors-1 の uint8)→ 度[0,360)。セクタ0 = +x 方向。"""
    return np.asarray(heading_u8, dtype=np.float64) * (360.0 / float(sectors))


def eccentricity_deg(
    agent_xy: np.ndarray, heading_u8: np.ndarray, event_xy: np.ndarray
) -> np.ndarray:
    """事象方向と視線方向の角度差 ``|E_ang|``[度・0..180]。"""
    d = np.asarray(event_xy, dtype=np.float64).reshape(1, 2) - np.asarray(
        agent_xy, dtype=np.float64
    )
    bearing = np.degrees(np.arctan2(d[:, 1], d[:, 0]))
    delta = bearing - heading_to_degrees(heading_u8)
    return np.abs((delta + 180.0) % 360.0 - 180.0)


# ---------------------------------------------------------------- 確率
def p1_primary(
    distance_m: np.ndarray,
    d50_eff_m: np.ndarray | float,
    m_load: np.ndarray | float = 1.0,
) -> np.ndarray:
    """TTPF 一次検出 ``P1' = P1 × m_load``。``d50_eff=0``(背後)は 0 を返す。"""
    d = np.asarray(distance_m, dtype=np.float64)
    d50 = np.broadcast_to(np.asarray(d50_eff_m, dtype=np.float64), d.shape)
    ok = (d50 > 0.0) & (d > 0.0)
    s = np.zeros_like(d)
    np.divide(d50, d, out=s, where=ok)
    e = TTPF_E_BASE + TTPF_E_SLOPE * s
    se = np.zeros_like(d)
    np.power(s, e, out=se, where=ok & (s > 0.0))
    p1 = np.where(ok, se / (1.0 + se), 0.0)
    # d=0(同一点)は確実に見える
    p1 = np.where((d == 0.0) & (d50 > 0.0), 1.0, p1)
    return p1 * np.asarray(m_load, dtype=np.float64)


def p2_social(
    n: np.ndarray | float,
    a: float = SOCIAL_A,
    b: float = SOCIAL_B,
    n50: float = SOCIAL_N50,
) -> np.ndarray:
    """社会伝播 ``P2 = a·N^b/(n50^b + N^b)``(N=0 なら 0)。"""
    nn = np.asarray(n, dtype=np.float64)
    nb = np.power(np.maximum(nn, 0.0), b)
    return np.where(nn > 0.0, a * nb / (np.power(n50, b) + nb), 0.0)


def combine(p1: np.ndarray, p2: np.ndarray) -> np.ndarray:
    """``p = 1 − (1−P1')(1−P2)``。"""
    return 1.0 - (1.0 - np.asarray(p1, dtype=np.float64)) * (
        1.0 - np.asarray(p2, dtype=np.float64)
    )


# ---------------------------------------------------------------- 近傍計数(社会項の N)
def social_counts(
    xy: np.ndarray,
    noticed: np.ndarray,
    radius_m: float = SOCIAL_RADIUS_M,
    *,
    max_pairs: int = 4_000_000,
    counters: Counters | None = None,
) -> np.ndarray:
    """各点の半径 ``radius_m`` 内にある「既に気づいた点」の数(自分自身は数えない)。

    一様格子(格子辺=半径)で 3×3 バケットに絞り、**厳密な距離判定**で数える。
    対の総数が ``max_pairs`` を超えるときはバケット計数 × 面積比 ``πr²/(9r²)`` の近似へ退避する
    (expedient・退避回数は counters に載る)。

    Note:
        逐次ループ宣言(P4): **なし**(9 方向ぶんの固定長ループのみ。点数に比例しない)。
    """
    pts = np.asarray(xy, dtype=np.float64)
    n = pts.shape[0]
    hit = np.asarray(noticed, dtype=bool)
    if n == 0 or not hit.any():
        return np.zeros(n, dtype=np.int32)
    r = float(radius_m)
    src = pts[hit]

    gx = np.floor(pts[:, 0] / r).astype(np.int64)
    gy = np.floor(pts[:, 1] / r).astype(np.int64)
    sx = np.floor(src[:, 0] / r).astype(np.int64)
    sy = np.floor(src[:, 1] / r).astype(np.int64)
    span = int(max(sx.max() - sx.min(), sy.max() - sy.min(), gx.max() - gx.min(),
                   gy.max() - gy.min())) + 3
    base_x = int(min(sx.min(), gx.min())) - 1
    base_y = int(min(sy.min(), gy.min())) - 1
    key_src = (sx - base_x) * span + (sy - base_y)
    order = np.argsort(key_src, kind="stable")
    key_sorted = key_src[order]
    src_sorted = src[order]

    total_pairs = 0
    starts_all = np.empty((9, n), dtype=np.int64)
    counts_all = np.empty((9, n), dtype=np.int64)
    k = 0
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            q = (gx + dx - base_x) * span + (gy + dy - base_y)
            lo = np.searchsorted(key_sorted, q, side="left")
            hi = np.searchsorted(key_sorted, q, side="right")
            starts_all[k] = lo
            counts_all[k] = hi - lo
            total_pairs += int((hi - lo).sum())
            k += 1

    if total_pairs > int(max_pairs):
        if counters is not None:
            counters.social_approx_fallbacks += 1
        # バケット計数 × 面積比(expedient の退避路)
        approx = counts_all.sum(axis=0).astype(np.float64) * (np.pi / 9.0)
        approx -= hit.astype(np.float64)  # 自分自身
        return np.maximum(np.rint(approx), 0.0).astype(np.int32)

    counts_flat = counts_all.ravel()
    starts_flat = starts_all.ravel()
    keep = counts_flat > 0
    counts_flat = counts_flat[keep]
    starts_flat = starts_flat[keep]
    owner = np.tile(np.arange(n, dtype=np.int64), 9)[keep]
    if counts_flat.size == 0:
        return np.zeros(n, dtype=np.int32)
    total = int(counts_flat.sum())
    ends = np.cumsum(counts_flat)
    seg_start = ends - counts_flat
    ramp = np.arange(total, dtype=np.int64) - np.repeat(seg_start, counts_flat)
    src_idx = np.repeat(starts_flat, counts_flat) + ramp
    tgt_idx = np.repeat(owner, counts_flat)
    diff = src_sorted[src_idx] - pts[tgt_idx]
    within = (diff[:, 0] ** 2 + diff[:, 1] ** 2) <= r * r
    counts = np.bincount(tgt_idx[within], minlength=n).astype(np.int32)
    counts -= hit.astype(np.int32)  # 自分自身(気づいていれば距離0で1件数えている)
    return np.maximum(counts, 0).astype(np.int32)


# ---------------------------------------------------------------- 本体
def notice_event(
    *,
    event_xy: tuple[float, float] | np.ndarray,
    agent_xy: np.ndarray,
    heading_u8: np.ndarray,
    task_flag: np.ndarray | int = TaskLoad.FREE,
    density_class: np.ndarray | int = DensityClass.SPARSE,
    night: bool = False,
    moving: bool = False,
    d50_m: float | None = None,
    seed: int | str = 0,
    event_id: int = 0,
    tick: int = 0,
    params: PNoticeParams | None = None,
    already_noticed: np.ndarray | None = None,
    counters: Counters | None = None,
) -> NoticeResult:
    """1つの顕著イベントについて、候補群の「気づいた/気づかない」を引く(§3.1)。

    Args:
        event_xy: 事象の平面座標[m]。
        agent_xy: ``(n, 2)`` 候補の平面座標[m]。
        heading_u8: ``(n,)`` 量子化された向き(0..15)。
        task_flag: ``TaskLoad``(スカラーまたは ``(n,)``)。
        density_class: ``DensityClass``(スカラーまたは ``(n,)``)。
        night: 夜間なら True(``m_light``)。
        moving: 動く事象なら True(d50 を 1.5 倍)。
        d50_m: 事象クラスの d50[m](None なら ``params.d50_m``)。
        seed / event_id / tick: 乱数のドメイン分離
            (``stream(seed, "perception.p_notice", event_id, tick)``)。
        params: 係数一式(ablation の切替を含む)。
        already_noticed: ``(n,)`` bool。**この tick に既に気づいている**候補(他イベント由来)。
            社会項の N の初期値に入る。
        counters: 診断計数(省略可)。

    Returns:
        ``NoticeResult``(打ち切り 80 m 内の候補のみ)。
    """
    prm = params or PNoticeParams()
    ev = np.asarray(event_xy, dtype=np.float64).reshape(2)
    xy = np.asarray(agent_xy, dtype=np.float64).reshape(-1, 2)
    n_all = xy.shape[0]

    d_all = np.hypot(xy[:, 0] - ev[0], xy[:, 1] - ev[1])
    idx = np.flatnonzero(d_all <= prm.cutoff_m)
    if counters is not None:
        counters.candidates += int(idx.size)
    if idx.size == 0:
        z = np.zeros(0, dtype=np.float64)
        return NoticeResult(idx, z, z, z, z, np.zeros(0, bool), np.zeros(0, bool),
                            np.zeros(0, np.int32))

    d = d_all[idx]
    pos = xy[idx]
    heads = np.asarray(heading_u8, dtype=np.uint8).reshape(-1)[idx]
    loads = np.broadcast_to(np.asarray(task_flag, dtype=np.int64).reshape(-1), (n_all,))[idx]
    dens = np.broadcast_to(np.asarray(density_class, dtype=np.int64).reshape(-1), (n_all,))[idx]

    ab = prm.ablation
    if ab == Ablation.A0_CONSTANT:
        p1 = np.full(d.shape, A0_CONSTANT, dtype=np.float64)
    else:
        d50 = float(prm.d50_m if d50_m is None else d50_m)
        if moving:
            d50 *= prm.moving_multiplier
        m_light = 1.0
        m_load = np.ones(d.shape, dtype=np.float64)
        if ab >= Ablation.A2_LOAD_LIGHT:
            m_light = prm.m_light_night if night else M_LIGHT_DAY
            m_load = np.asarray(prm.m_load, dtype=np.float64)[np.clip(loads, 0, 2)]
        m_ecc = np.ones(d.shape, dtype=np.float64)
        m_dens = np.ones(d.shape, dtype=np.float64)
        if ab >= Ablation.A3_ECC_DENSITY:
            e_ang = eccentricity_deg(pos, heads, ev)
            m_ecc = np.where(
                e_ang > prm.ecc_cutoff_deg, 0.0, prm.e2_deg / (e_ang + prm.e2_deg)
            )
            m_dens = np.asarray(prm.m_density, dtype=np.float64)[np.clip(dens, 0, 2)]
        d50_eff = d50 * m_light * m_ecc * m_dens
        p1 = p1_primary(d, d50_eff, m_load)

    g = stream(seed, "perception.p_notice", int(event_id), int(tick))
    draws = g.random((2, d.size))
    noticed_primary = draws[0] < p1

    prior = (
        np.zeros(d.size, dtype=bool)
        if already_noticed is None
        else np.asarray(already_noticed, dtype=bool).reshape(-1)[idx]
    )
    if ab >= Ablation.A4_SOCIAL:
        n_social = social_counts(
            pos,
            noticed_primary | prior,
            prm.social_radius_m,
            max_pairs=prm.max_pairs,
            counters=counters,
        )
        p2 = p2_social(n_social, prm.social_a, prm.social_b, prm.social_n50)
    else:
        n_social = np.zeros(d.size, dtype=np.int32)
        p2 = np.zeros(d.size, dtype=np.float64)

    noticed_social = (~noticed_primary) & (draws[1] < p2)
    noticed = noticed_primary | noticed_social
    if counters is not None:
        counters.noticed_primary += int(np.count_nonzero(noticed_primary))
        counters.noticed_social += int(np.count_nonzero(noticed_social))

    return NoticeResult(
        index=idx,
        distance_m=d,
        p1=p1,
        p2=p2,
        p=combine(p1, p2),
        noticed=noticed,
        noticed_primary=noticed_primary,
        social_n=n_social,
    )
