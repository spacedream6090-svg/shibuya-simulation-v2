"""world.facts.initial_ties — 割る段で ``engine/relations.py`` を割った割り先(全ファイルの表 §4・名の表は
``tools/pkgmove/map.toml`` の割る行)。

中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の
方針は、主な割り先 ``mind/relations/layer.py`` に残した元の docstring を読むこと。
"""

from __future__ import annotations

import math
from collections import Counter
from types import SimpleNamespace
from typing import Any, Final
import numpy as np
from shibuya.foundation.time_consts import MINUTES_PER_DAY
from shibuya.foundation.vocab.relations import (
    DEFAULT_REL_TENURE_HASH,
    InitialEdges,
    REL_D,
    REL_INIT_DENSITIES,
    REL_K,
    REL_KINDS,
    REL_KIND_NAMES,
    REL_TAU,
    REL_TENURE_WEEKS,
    REL_TIEBREAKS,
    _activation,
)

__all__ = [
    "REL_TENURE_HASHES", "check_rel_tenure_hash", "REL_SLOT_MIN", "HOUSEHOLD_MIN_DAYS_PER_WEEK", "copresence_days",
    "slot_cells", "copresence", "initial_edges", "tau_from_edges",
]


#: 在職期間 T_uv のハッシュの版(第2波 §2A 項 2)。``v2``(既定)=同点の順のハッシュ ``_pair_mix(元 id_u, 元 id_v)``
#: と独立な混ぜ合わせ(向きのない組の ``_pair_mix`` にもう 1 段 splitmix64 を塩つきでかける)/ ``v1``=旧
#: (``_pair_mix(min, max)``=元 id_u < 元 id_v の辺で同点の順と同じ値=同点の多い組で在職の短い相手ほど選ばれる欠陥・
#: 旧 golden の再現用)。
REL_TENURE_HASHES: Final[tuple[str, ...]] = ("v2", "v1")
#: v2 の塩(未リサーチ=expedient・値そのものに意味はない=黄金比の 64 bit 表現と異なる定数なら何でもよい)。
_TENURE_SALT_V2: Final[int] = 0xD1B54A32D192ED03
#: 共在を数える時間の枠[分](週 7 日 × 96 枠)。
REL_SLOT_MIN: Final[int] = 15
#: 世帯で共在が取れない(自宅が域外)ペアの「共在のあった日数/週」(毎日=7・宣言=第299 Q92 の床 7 回/週)。
HOUSEHOLD_MIN_DAYS_PER_WEEK: Final[int] = 7
#: W17 が **1 日ぶんしか無い**(全体が曜日 0 だけ=実資産の事実)とき、その日を「代表日」として「共在のあった
#: 日数/週」に直す日数(世帯 7・職場 5・学校 5=宣言・expedient)。複数の曜日がある表では共在のあった曜日の数。
REL_DAYS_PER_WEEK: Final[dict[int, int]] = {1: 7, 2: 5, 3: 5}
_SLOTS_PER_DAY: Final[int] = MINUTES_PER_DAY // REL_SLOT_MIN
_SLOTS: Final[int] = 7 * _SLOTS_PER_DAY


# ---------------------------------------------------------------------------- 共在(W17)
def slot_cells(weekly: Any, rows: np.ndarray) -> np.ndarray:
    """体行の配列 → ``(体, 7×96)`` の「その 15 分に居るセル」(W17 の解決済みセル・無ければ −1)。

    ラン開始時に 1 回(組の体だけ)。行 → 枠の展開は配列演算(逐次ループなし)。
    """
    rows = np.asarray(rows, dtype=np.int64)
    out = np.full((rows.size, _SLOTS), -1, dtype=np.int32)
    if rows.size == 0:
        return out
    lo = weekly.day_offset[rows * 7]
    hi = weekly.day_offset[rows * 7 + 7]
    counts = (hi - lo).astype(np.int64)
    idx = np.repeat(lo.astype(np.int64), counts) + (
        np.arange(int(counts.sum()), dtype=np.int64) - np.repeat(np.cumsum(counts) - counts, counts))
    who = np.repeat(np.arange(rows.size, dtype=np.int64), counts)
    cell = np.asarray(weekly.target_cell, dtype=np.int64)[idx]
    keep = cell >= 0
    idx, who, cell = idx[keep], who[keep], cell[keep]
    if idx.size == 0:
        return out
    # 曜日=体行の中の CSR 位置から(day_offset は体×7 の CSR)
    dstart = weekly.day_offset[(rows * 7)[:, None] + np.arange(7)[None, :]]  # (体, 7)
    day = (np.sum(idx[:, None] >= dstart[who], axis=1) - 1).astype(np.int64)
    s0 = day * _SLOTS_PER_DAY + np.asarray(weekly.start_min, dtype=np.int64)[idx] // REL_SLOT_MIN
    s1 = day * _SLOTS_PER_DAY + (np.asarray(weekly.end_min, dtype=np.int64)[idx] + REL_SLOT_MIN - 1) // REL_SLOT_MIN
    s1 = np.maximum(s1, s0 + 1)
    span = (s1 - s0).astype(np.int64)
    k = np.repeat(np.arange(idx.size, dtype=np.int64), span)
    slot = np.repeat(s0, span) + (np.arange(int(span.sum()), dtype=np.int64) - np.repeat(np.cumsum(span) - span, span))
    ok = slot < _SLOTS
    out[who[k[ok]], slot[ok]] = cell[k[ok]]
    return out


def copresence(slots: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """``(g, 枠)`` のセル → ``(共在の分(g×g), 共在のブロック数(g×g))``(同じセル・同じ枠・行列積)。

    ブロック=続けて共在した枠の塊(枠 t で共在 ∧ t−1 では共在でない)=Σ_c (B_c B_cᵀ − D_c D_cᵀ)
    (B_c=セル c に居る枠・D_c=t と t−1 の両方でセル c に居る枠)。週をまたぐ端は切る(宣言)。
    """
    g = int(slots.shape[0])
    mins = np.zeros((g, g), dtype=np.float64)
    blocks = np.zeros((g, g), dtype=np.float64)
    if g == 0:
        return mins, blocks
    cells = np.unique(slots[slots >= 0])
    prev = np.concatenate([np.full((g, 1), -1, dtype=slots.dtype), slots[:, :-1]], axis=1)
    for c in cells.tolist():  # 組の中のセルの数ぶん(自宅・職場・学校=数個)
        B = (slots == c).astype(np.float32)
        D = ((slots == c) & (prev == c)).astype(np.float32)
        bb = B @ B.T
        mins += bb
        blocks += bb - D @ D.T
    np.fill_diagonal(mins, 0.0)
    np.fill_diagonal(blocks, 0.0)
    return mins * REL_SLOT_MIN, blocks


def copresence_days(slots: np.ndarray) -> np.ndarray:
    """``(g, 7×96)`` のセル → ``(g, g)`` の「共在のあった曜日の数」(0〜7・同じセル・同じ枠が 1 枠でもある日)。

    第300 訂正(8b′): 初期辺の n の単位(1 日 1 本=ラン中の同席と同じ)。曜日ごと・セルごとの行列積。
    """
    g = int(slots.shape[0])
    days = np.zeros((g, g), dtype=np.int64)
    if g == 0:
        return days
    cells = np.unique(slots[slots >= 0])
    for d in range(7):  # 曜日の数ぶん(7)
        s = slots[:, d * _SLOTS_PER_DAY:(d + 1) * _SLOTS_PER_DAY]
        hit = np.zeros((g, g), dtype=np.float64)
        for c in cells.tolist():  # 組の中のセルの数ぶん(数個)
            B = (s == c).astype(np.float32)
            hit += B @ B.T
        days += hit > 0
    np.fill_diagonal(days, 0)
    return days


def _last_copresence(su: np.ndarray, sv: np.ndarray, day_index: int, daily: bool = False) -> int:
    """2 体の枠 → ランの日の 0 時より前の最後の共在の終わり[分](負・無ければ −7 日)。

    ``daily``(W17 が 1 日ぶん=代表日)なら「前日も同じ日課」として前日の最後の共在の終わり。
    それ以外は週を遡る。
    """
    both = (su == sv) & (su >= 0)
    if not bool(both.any()):
        return -7 * MINUTES_PER_DAY
    if daily:
        j = int(np.flatnonzero(both[:_SLOTS_PER_DAY])[-1]) if bool(both[:_SLOTS_PER_DAY].any()) else -1
        return (j + 1) * REL_SLOT_MIN - MINUTES_PER_DAY if j >= 0 else -7 * MINUTES_PER_DAY
    start = (int(day_index) % 7) * _SLOTS_PER_DAY
    # ランの日の 0 時から過去へ 1 週ぶん遡る並び(逐次なし=配列の回転)
    order = (start - 1 - np.arange(_SLOTS)) % _SLOTS
    hit = int(np.argmax(both[order]))
    return -(hit * REL_SLOT_MIN)  # その枠の終わり=0 時から hit 枠前


#: 直近の共在を一度に求める辺の数(``(辺, 7×96)`` の真偽の塊=約 2.7 MB × 塊/4,096 辺)。
_LAST_CHUNK: Final[int] = 4_096


def _last_copresence_many(sl_u: np.ndarray, sl_v: np.ndarray, day_index: int, daily: bool) -> np.ndarray:
    """``_last_copresence`` の配列版(辺の塊ごと・同じ値)。``sl_u``/``sl_v`` は ``(辺, 7×96)``。"""
    both = (sl_u == sl_v) & (sl_u >= 0)
    out = np.full(both.shape[0], -7 * MINUTES_PER_DAY, dtype=np.int64)
    if both.shape[0] == 0:
        return out
    if daily:
        b = both[:, :_SLOTS_PER_DAY]
        has = b.any(axis=1)
        j = _SLOTS_PER_DAY - 1 - np.argmax(b[:, ::-1], axis=1)
        return np.where(has, (j + 1) * REL_SLOT_MIN - MINUTES_PER_DAY, out)
    start = (int(day_index) % 7) * _SLOTS_PER_DAY
    order = (start - 1 - np.arange(_SLOTS)) % _SLOTS
    bo = both[:, order]
    has = bo.any(axis=1)
    return np.where(has, -(np.argmax(bo, axis=1) * REL_SLOT_MIN), out)


def _pair_mix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """体の元 id の組 → uint64(splitmix64 の仕上げ・同点の順だけに使う・向きあり)。"""
    with np.errstate(over="ignore"):
        x = (np.asarray(a, dtype=np.uint64) * np.uint64(0x9E3779B97F4A7C15)) ^ (
            np.asarray(b, dtype=np.uint64) * np.uint64(0xBF58476D1CE4E5B9))
        x ^= x >> np.uint64(31)
        x *= np.uint64(0x94D049BB133111EB)
        x ^= x >> np.uint64(29)
    return x


def _weekly64(weekly: Any) -> Any:
    """W17 の CSR の 4 列を int64 で 1 回だけ作る(``slot_cells`` の ``np.asarray`` が組ごとに全体を写さない)。"""
    return SimpleNamespace(
        day_offset=np.asarray(weekly.day_offset, dtype=np.int64),
        target_cell=np.asarray(weekly.target_cell, dtype=np.int64),
        start_min=np.asarray(weekly.start_min, dtype=np.int64),
        end_min=np.asarray(weekly.end_min, dtype=np.int64),
    )


def check_rel_tenure_hash(version: str) -> str:
    """在職期間のハッシュの版を検める(関係の部品の単体の口・〔第 2 部〕ランの口の切替口 --rel-tenure-hash は消した)。"""
    if str(version) not in REL_TENURE_HASHES:
        raise ValueError(f"rel_tenure_hash は {REL_TENURE_HASHES} のどれか(いま {version!r})")
    return str(version)


def _splitmix64(x: np.ndarray) -> np.ndarray:
    """uint64 → uint64(splitmix64 の 1 段=加算と仕上げ・全単射)。"""
    with np.errstate(over="ignore"):
        z = np.asarray(x, dtype=np.uint64) + np.uint64(0x9E3779B97F4A7C15)
        z = (z ^ (z >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
        z = (z ^ (z >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
        z ^= z >> np.uint64(31)
    return z


def _tenure_unit(src_u: np.ndarray, src_v: np.ndarray, version: str = DEFAULT_REL_TENURE_HASH) -> np.ndarray:
    """在職期間の U ∈ [0, 1)(元 id の**向きのない組**の混ぜ合わせ=u→v と v→u で同じ)。

    ``v1``(旧)= ``_pair_mix(min, max)``。元 id_u < 元 id_v の辺では同点の順(``_pair_mix(元 id_u, 元 id_v)``)と
    同じ値になる=欠陥(第2波 §2A 項 2)。``v2`` = その値に塩を排他的論理和してから splitmix64 をもう 1 段
    (全単射の非線形の混ぜ=同点の順との順位相関が消える)。
    """
    lo = np.minimum(src_u, src_v)
    hi = np.maximum(src_u, src_v)
    x = _pair_mix(lo, hi)
    if check_rel_tenure_hash(version) == "v2":
        x = _splitmix64(x ^ np.uint64(_TENURE_SALT_V2))
    return (x >> np.uint64(11)).astype(np.float64) / float(1 << 53)  # [0, 1)


def _tenure_weeks(src_u: np.ndarray, src_v: np.ndarray, tenure_weeks: float,
                  version: str = DEFAULT_REL_TENURE_HASH) -> np.ndarray:
    """辺の在職期間 T_uv[週]=1 + (上限 − 1) × U(組)。U=:func:`_tenure_unit`(u→v と v→u で同じ)。"""
    unit = _tenure_unit(src_u, src_v, version)
    return 1.0 + (float(tenure_weeks) - 1.0) * unit


def initial_edges(pop: Any, weekly: Any, n_agents: int, *, k: int = REL_K, day_index: int = 0,
                  density: float = 1.0, minutes_per_tick: float = 1.0, d: float = REL_D,
                  tau: float | None = REL_TAU, tiebreak: str = "hash",
                  tenure_weeks: float = REL_TENURE_WEEKS,
                  tenure_hash: str = DEFAULT_REL_TENURE_HASH) -> InitialEdges:
    """W16(世帯・組織・学校セル)+W17(共在)→ 初期辺(有向・体ごとに上位 k − 世帯)。

    ``tau`` が数なら A ≥ τ の辺だけ返す(``None`` なら全部=τ の逆算に使う)。逐次ループ宣言 1。
    ``tiebreak``: 共在の分が同じ相手の順(:data:`REL_TIEBREAKS`・既定 ``hash``)。
    ``tenure_weeks``: 在職期間 T_uv の上限[週](第299 Q89/Q90・既定 13・感度 26)。
    ``tenure_hash``: 在職期間のハッシュの版(:data:`REL_TENURE_HASHES`・既定 ``v2``=同点の順と独立・``v1``=旧)。
    """
    if not (math.isfinite(float(tenure_weeks)) and float(tenure_weeks) >= 1.0):
        raise ValueError(f"tenure_weeks は 1 以上(いま {tenure_weeks})")
    if float(density) not in REL_INIT_DENSITIES:
        raise ValueError(f"rel_init_density は {REL_INIT_DENSITIES} のどれか(いま {density})")
    if tiebreak not in REL_TIEBREAKS:
        raise ValueError(f"tiebreak は {REL_TIEBREAKS} のどれか(いま {tiebreak!r})")
    check_rel_tenure_hash(tenure_hash)
    m = min(int(n_agents), int(pop.n))
    audit: dict[str, Any] = {"density": float(density), "k": int(k), "slot_minutes": REL_SLOT_MIN,
                             "tiebreak": str(tiebreak), "tenure_weeks": float(tenure_weeks),
                             "tenure_hash": str(tenure_hash)}
    empty = np.zeros(0, dtype=np.int64)
    if m == 0 or weekly is None:
        audit["reason"] = "no_population_or_schedule"
        return InitialEdges(empty, empty, empty, empty, empty, empty, empty, audit)
    groups: list[tuple[int, np.ndarray]] = []
    for kind, col in ((REL_KINDS["household"], "household_id"), (REL_KINDS["work"], "org_id"),
                      (REL_KINDS["school"], "school_cell")):
        ids = np.asarray(getattr(pop, col), dtype=np.int64)[:m]
        ok = np.flatnonzero(ids >= 0)
        if ok.size == 0:
            continue
        order = ok[np.argsort(ids[ok], kind="stable")]
        sid = ids[order]
        cut = np.flatnonzero(np.diff(sid)) + 1
        for mem in np.split(order, cut):  # 組の数ぶん(1 回)
            if mem.size >= 2:
                groups.append((kind, mem))
    audit["groups"] = dict(Counter(REL_KIND_NAMES[kd] for kd, _ in groups))
    weekly = _weekly64(weekly)  # 性能(挙動不変): 組ごとの全体の写しをやめる
    src_id = np.asarray(getattr(pop, "source_agent_id", np.arange(m)), dtype=np.int64)[:m]  # 同点の順の種
    per_day = np.diff(weekly.day_offset).reshape(-1, 7)
    daily = bool(per_day[:, 1:].sum() == 0)
    audit["w17_single_day"] = daily
    us: list[np.ndarray] = []
    vs: list[np.ndarray] = []
    kinds: list[np.ndarray] = []
    mins: list[np.ndarray] = []
    dys: list[np.ndarray] = []
    n_pairs = 0
    for kind, mem in groups:  # 逐次ループ宣言 1: 組の数ぶん(組の中は行列積)
        g = int(mem.size)
        n_pairs += g * (g - 1)
        slots = slot_cells(weekly, mem)
        mm, _bb = copresence(slots)
        # 組の中で体ごとに共在の長い順の上位 k(最後に体ごとに k で切るので、組の中で先に切ってよい)
        key = np.where(np.eye(g, dtype=bool), -1.0, mm)
        take = min(int(k), g - 1)
        if tiebreak == "hash":  # 同点は体の元 id の組の混ぜ合わせの順(行番号に依らない)
            cols = np.lexsort((_pair_mix(src_id[mem][:, None], src_id[mem][None, :]), -key), axis=-1)[:, :take]
        else:  # id: 同点は相手の行番号の小さい方
            cols = np.argsort(-key, axis=1, kind="stable")[:, :take]
        iu = np.repeat(np.arange(g), take)
        iv = cols.ravel()
        us.append(mem[iu])
        vs.append(mem[iv])
        kinds.append(np.full(iu.size, kind, dtype=np.int64))
        mins.append(mm[iu, iv])
        # 第300 訂正: 共在のあった日数(W17 が 1 日ぶんなら下で代表日の係数から出す=ここでは数えない)
        dys.append(copresence_days(slots)[iu, iv] if not daily else np.zeros(iu.size, dtype=np.int64))
    audit["candidate_pairs_all"] = int(n_pairs)
    if not us:
        audit["reason"] = "no_groups"
        return InitialEdges(empty, empty, empty, empty, empty, empty, empty, audit)
    u = np.concatenate(us)
    v = np.concatenate(vs)
    kind = np.concatenate(kinds)
    mn = np.concatenate(mins)
    dy = np.concatenate(dys).astype(np.float64)
    # 同じ組が複数の組に居る(世帯かつ同僚)→ 種別の小さい方(世帯 > 職場 > 学校)を残す
    key = u * (m + 1) + v
    order = np.lexsort((kind, key))
    key, u, v, kind, mn, dy = key[order], u[order], v[order], kind[order], mn[order], dy[order]
    first_of = np.concatenate(([True], key[1:] != key[:-1]))
    u, v, kind, mn, dy = u[first_of], v[first_of], kind[first_of], mn[first_of], dy[first_of]
    hh = kind == REL_KINDS["household"]
    # 第300 訂正(8b′・Q100/Q101): n の単位=**共在のあった日数**(1 日 1 本=ラン中の会話 1 セッション・同席 1 日 1 本と
    # 同じ A の式に同じ単位)。15 分枠の共在時間(mn)は上位 k の順位付けと密度の腕にだけ使う(Granovetter の時間量)。
    if daily:  # 代表日に共在 → 週の日数(世帯 7・職場/学校 5)
        lut = np.zeros(max(REL_DAYS_PER_WEEK) + 1, dtype=np.float64)
        for kd, dd in REL_DAYS_PER_WEEK.items():  # 種別の数ぶん(3)
            lut[kd] = dd
        bk = np.where(mn > 0, lut[kind], 0.0)
    else:
        bk = dy
    bk = np.where(hh & (bk <= 0), HOUSEHOLD_MIN_DAYS_PER_WEEK, bk)
    audit["candidate_pairs"] = int(u.size)
    audit["candidate_pairs_copresent"] = int(np.count_nonzero(mn > 0))
    # 密度の腕(世帯は常に全ペア)
    if float(density) == 1.0:
        keep = hh | (mn > 0)
    elif float(density) == 0.5:
        pos = mn[~hh & (mn > 0)]
        thr = float(np.median(pos)) if pos.size else 0.0
        keep = hh | (mn > thr)
        audit["density_threshold_minutes"] = thr
    else:
        keep = np.ones(u.size, dtype=bool)
        bk = np.where(~hh & (bk <= 0), 1.0, bk)  # 共在 0 の組織/学校の組=週 1 日と置く
    u, v, kind, mn, bk = u[keep], v[keep], kind[keep], mn[keep], bk[keep]
    # 体ごとに: 世帯を先に・残りは共在の分の降順(同点は tiebreak=既定は元 id の組の混ぜ合わせ)で k 本まで
    tie = _pair_mix(src_id[u], src_id[v]) if tiebreak == "hash" else v
    order = np.lexsort((tie, -mn, (~(kind == REL_KINDS["household"])).astype(np.int64), u))
    u, v, kind, mn, bk = u[order], v[order], kind[order], mn[order], bk[order]
    starts = np.flatnonzero(np.concatenate(([True], u[1:] != u[:-1])))
    rank = np.arange(u.size) - np.repeat(starts, np.diff(np.append(starts, u.size)))
    cap = rank < int(k)
    audit["capped_out"] = int(np.count_nonzero(~cap))
    u, v, kind, mn, bk = u[cap], v[cap], kind[cap], mn[cap], bk[cap]
    # 第299 Q89/Q90+第300 訂正: 在職期間 T_uv(組の hash で 1〜上限 週)・n=共在のあった日数/週 × T_uv・first=−T_uv
    tw = _tenure_weeks(src_id[u], src_id[v], float(tenure_weeks), str(tenure_hash))
    n = np.minimum(65_535, np.round(bk * tw)).astype(np.int64)
    n = np.maximum(n, 1)
    first = -np.round(tw * 7.0 * float(MINUTES_PER_DAY) / float(minutes_per_tick)).astype(np.int64)
    A0 = _activation(n, first, 0, minutes_per_tick, d)
    audit["edges_before_tau"] = int(u.size)
    if tau is not None:
        live = A0 >= float(tau)
        audit["dropped_by_tau"] = int(np.count_nonzero(~live))
        u, v, kind, mn, n, first, A0 = u[live], v[live], kind[live], mn[live], n[live], first[live], A0[live]
    # 直近の共在(ランの日の前へ遡る)=書く辺だけ・辺の塊ごとの配列演算(逐次ループ宣言 1b: 塊の数ぶん=
    # 辺数/4,096・ラン開始時に 1 回)
    last = np.full(u.size, -7 * MINUTES_PER_DAY, dtype=np.int64)
    need = np.unique(np.concatenate([u, v])) if u.size else empty
    if need.size:
        sl = slot_cells(weekly, need)
        pu = np.searchsorted(need, u)
        pv = np.searchsorted(need, v)
        for c0 in range(0, u.size, _LAST_CHUNK):  # 逐次ループ宣言 1b: 塊の数ぶん
            c1 = min(u.size, c0 + _LAST_CHUNK)
            last[c0:c1] = _last_copresence_many(sl[pu[c0:c1]], sl[pv[c0:c1]], day_index, daily)
    last = np.round(last / float(minutes_per_tick)).astype(np.int64)
    return InitialEdges(u, v, kind, n, first, last, mn.astype(np.int64), audit)


def tau_from_edges(u: np.ndarray, A: np.ndarray, n_agents: int, k: int = REL_K) -> dict[str, Any]:
    """τ の逆算: 体ごとの k 番目に強い辺の A(k 本に満たない体は −∞)の中央値(=半分の体が k 本残る τ)。"""
    u = np.asarray(u, dtype=np.int64)
    A = np.asarray(A, dtype=np.float64)
    kth = np.full(int(n_agents), -np.inf)
    if u.size:
        order = np.lexsort((-A, u))
        us, As = u[order], A[order]
        starts = np.flatnonzero(np.concatenate(([True], us[1:] != us[:-1])))
        rank = np.arange(us.size) - np.repeat(starts, np.diff(np.append(starts, us.size)))
        hit = rank == int(k) - 1
        kth[us[hit]] = As[hit]
    med = float(np.median(kth)) if kth.size else -np.inf
    fin = kth[np.isfinite(kth)]
    return {"tau": med, "agents": int(n_agents), "agents_with_k_edges": int(fin.size),
            "share_with_k_edges": round(fin.size / max(1, int(n_agents)), 4),
            "kth_A_quantiles": ({p: round(float(np.percentile(fin, q)), 4)
                                 for p, q in (("p10", 10), ("p25", 25), ("p50", 50), ("p75", 75), ("p90", 90))}
                                if fin.size else {})}
