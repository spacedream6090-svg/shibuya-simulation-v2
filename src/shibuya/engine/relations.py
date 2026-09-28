"""engine.relations — **関係辺の表と導出**(C10 8a・R1 (a)・M12 (a)・D-93 (a)(b)(c)・第299)。

正典: ``docs/design/v2-c10-relations-implementation-agenda.md`` §1(段 8a の 1〜8)・§4。上位=
``docs/design/v2-c10-relations-agenda.md`` §4(R1〜R14+R9′)・§5 と追記(D-93 (a)〜(d))・
``docs/research/v2-c10-initial-relations-research.md`` §6-1・記憶アジェンダ M12。入れ物は記憶 第 1 段と同じ
(``engine.memory.MemoryLayer`` が持つ・腕でだけ確保・書き手は resolve・A の近似)。8b(会話の起点)・8c(語彙
v3.1)・8d(約束)・同席 COPRESENT・ウォームアップの強制ペアは含めない。

表(``AgentState(relation_columns=True)`` のランだけ・``--relations on``・``--memory on`` が前提)
    体ごとに k 辺(:data:`REL_K`=15・感度 5/50)。1 辺=``rel_partner`` i32(−1=空)・``rel_kind`` u8
    (:data:`REL_KINDS`=世帯 1/職場 2/学校 3/常連 4/知人 5)・``rel_sign`` i8(Σ 符号=精度加重の和・w=1・
    ±127 で止める・読むときは sign)・``rel_first`` i32(A の起点・初期辺は過去の負の tick)・``rel_last`` i32・
    ``rel_n`` u16(相互作用の回数=A の n)=**実 16 B**(4+1+1+4+4+2・アジェンダの「15 B」は数え違い)
    =宣言 16 B/辺 → 240 B/体。

A と強さ(M12 (a)・D-93 (a))::

    A = ln(n/(1−d)) − d·ln(L+1)      L=(tick − rel_first)×分/tick・d=0.5(#56/#60 と同じ近似)
    辺として残る条件: A ≥ τ_rel(:data:`REL_TAU`・較正対象=機械的初期化の後の「15 番目の辺の A」の中央値から
    逆算して宣言・感度 ±0.5)
    読むときの強さ P = 1/(1+exp(−(A−τ_rel)/s))(s=0.25)を 0..255 に量子化(Zhao 2012)

    Δ と半減期は持たない。τ を下回った辺は表に残る(相互作用が戻れば A が上がる)が、読み口は返さない。

書き手(:meth:`RelationLayer.on_episodes`=``MemoryLayer.record`` が相互作用のエピソードを書いた直後)
    記憶のエピソードのうち partner ≥ 0(自分でない体): 会話(kind=talk)・手伝い(kind=help)。会話は
    **1 セッション 1 本**(発話ごとの ``mem_n``+1 は辺に写さない=``note_utterance`` の記録は通さない)。
    符号(D-93 (b)・LLM は書かない)=``OK`` の会話/手伝い +1・``REFUSED`` −1・``PARTNER_BUSY``/``PARTNER_GONE``
    0(相手の都合)・それ以外の結果(対象不正・能力不足 …)は辺にしない。同じ相手は 1 辺に統合(n+1・last 更新)。
    新しい相手=種別 知人(5)。満杯で新しい相手 → A 最小の辺を落とす(層満杯の押し出し・行動契約 §5)。
    同席(COPRESENT)は書かない(口 ``--rel-copresent`` は後の段=本段では無い)。

機械的初期化(R2 (a)・D-93 (c)・「初期関係が下地」・:func:`initial_edges`)
    ラン開始時に W16(世帯・組織・学校セル)と W17(週次表)から: (i) 世帯=同一世帯の全ペア(種別 1)
    (ii) 職場/学校=同一組織/学校セルの体のうち、W17 で**同じセル・同じ時間帯**に居る時間(共在・15 分の枠)が
    長い順に、世帯を除いた残り枠(≤ k − 世帯)へ(種別 2/3・共在の分が同じ相手の順は体の元 id の組の混ぜ合わせ=
    行番号の順にしない=大組織の入次数の偏りを避ける・:data:`REL_TIEBREAKS`)(iii) 常連(4)は作らない。n=共在のブロック数/週
    × 13(過去 13 週の反復)・first=−13 週・last=直近の共在(ランの日の前へ遡る)。世帯で共在が取れない
    (域外の自宅=セル未解決)ペアは毎日 1 回=7 ブロック/週と置く(宣言)。A ≥ τ_rel の辺だけ書く。

逐次ループ宣言(P4)
    1. :func:`initial_edges`: 組(世帯・組織・学校セル)の数ぶん(ラン開始時に 1 回・組の中は行列積)。
       1b. 直近の共在: 書く辺の塊(4,096 辺)の数ぶん(ラン開始時に 1 回・塊の中は配列演算)。
    2. :meth:`RelationLayer.on_episodes`: 体あたりの相互作用の件数の最大ぶん(同じ体の 2 件目を次の回へ)。
    3. 読み口 :meth:`RelationLayer.edges` / :meth:`partners_in_cell` / :meth:`weights_for_invite` は配列演算。
"""

from __future__ import annotations

import math
from collections import Counter
from types import SimpleNamespace
from typing import Any, Final, NamedTuple

import numpy as np

from shibuya.agents.state import REL_EMPTY, ResultCode
from shibuya.engine import resolve as R

__all__ = [
    "REL_K",
    "REL_MODES",
    "REL_KINDS",
    "REL_KIND_NAMES",
    "REL_D",
    "REL_TAU",
    "REL_S",
    "REL_INIT_WEEKS",
    "REL_SLOT_MIN",
    "REL_ROW_BYTES_ACTUAL",
    "REL_ROW_BYTES_DECLARED",
    "REL_INIT_DENSITIES",
    "REL_INVITE_LAYERS",
    "HOUSEHOLD_MIN_BLOCKS_PER_WEEK",
    "RelationEdges",
    "InitialEdges",
    "slot_cells",
    "copresence",
    "initial_edges",
    "tau_from_edges",
    "RelationLayer",
]

#: 体あたりの辺の数(R1 (a)・Dunbar の 15 層・感度 5/50)。
REL_K: Final[int] = 15
REL_MODES: Final[tuple[str, ...]] = ("off", "on")
#: 辺の種別(R1 (a))。
REL_KINDS: Final[dict[str, int]] = {"household": 1, "work": 2, "school": 3, "regular": 4, "acquaintance": 5}
REL_KIND_NAMES: Final[dict[int, str]] = {v: k for k, v in REL_KINDS.items()}
#: 減衰(記憶と同じ既決値・感度 0.25/0.75)。
REL_D: Final[float] = 0.5
#: 辺として残る A の閾値 τ_rel(**較正対象**): W16+W17 の全母集団(390,067 体)で機械的初期化をしたときの
#: 「体ごとの 15 番目の辺の A」の中央値=**−1.0241**(ラン開始時・15 本の体が 54.5%)・1 日の終わりには −1.0253
#: (A は L とともに下がる)。1 日のランの間に初期辺が全部落ちないよう **0.075 の余裕を置いて −1.1**(=相互作用が
#: 無いまま約 15 日もつ・宣言・感度 ±0.5)。逆算の過程は記録 ``docs/bench/analysis/c10-relations-2026-09-28/`` §8a。
REL_TAU: Final[float] = -1.1
#: 強さ P のロジスティックの幅(M17 の宣言と同じ)。
REL_S: Final[float] = 0.25
#: 初期辺の「過去の反復」の週数(n=共在のブロック数/週 × 13・first=−13 週)。
REL_INIT_WEEKS: Final[int] = 13
#: 共在を数える時間の枠[分](週 7 日 × 96 枠)。
REL_SLOT_MIN: Final[int] = 15
#: 1 辺の実バイト(4+1+1+4+4+2)と宣言バイト(同じ)。
REL_ROW_BYTES_ACTUAL: Final[int] = 16
REL_ROW_BYTES_DECLARED: Final[int] = 16
#: 初期網の密度の腕(×0.5=共在が中央値より長い組だけ・×1=共在 > 0・×2=共在 0 の組織/学校の組も入れる)。
REL_INIT_DENSITIES: Final[tuple[float, ...]] = (0.5, 1.0, 2.0)
#: 招待の重み(Dunbar 2020: 内側 5 人に 40%・次の 10 人に 20%・残り 40%=辺の無い同席者=8b が読む)。
REL_INVITE_LAYERS: Final[tuple[tuple[int, float], ...]] = ((5, 0.40), (10, 0.20))
#: 世帯で共在が取れない(自宅が域外)ペアの共在ブロック数/週(毎日 1 回・宣言)。
HOUSEHOLD_MIN_BLOCKS_PER_WEEK: Final[int] = 7
#: W17 が **1 日ぶんしか無い**(全体が曜日 0 だけ=実資産の事実)とき、その日を「代表日」として週の回数に
#: 直す日数(世帯 7・職場 5・学校 5=宣言・expedient)。複数の曜日がある表では週の合計をそのまま使う。
REL_DAYS_PER_WEEK: Final[dict[int, int]] = {1: 7, 2: 5, 3: 5}
_SLOTS_PER_DAY: Final[int] = 1440 // REL_SLOT_MIN
_SLOTS: Final[int] = 7 * _SLOTS_PER_DAY
_TALK: Final[int] = 7
_HELP: Final[int] = 9
_SIGN_LABEL: Final[dict[int, str]] = {1: "+1", 0: "0", -1: "-1"}
_SIGN_OF_RESULT: Final[dict[int, int]] = {
    int(ResultCode.OK): 1, int(ResultCode.REFUSED): -1, int(ResultCode.PARTNER_BUSY): 0,
    int(ResultCode.PARTNER_GONE): 0,
}


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


def _last_copresence(su: np.ndarray, sv: np.ndarray, day_index: int, daily: bool = False) -> int:
    """2 体の枠 → ランの日の 0 時より前の最後の共在の終わり[分](負・無ければ −7 日)。

    ``daily``(W17 が 1 日ぶん=代表日)なら「前日も同じ日課」として前日の最後の共在の終わり。
    それ以外は週を遡る。
    """
    both = (su == sv) & (su >= 0)
    if not bool(both.any()):
        return -7 * 1440
    if daily:
        j = int(np.flatnonzero(both[:_SLOTS_PER_DAY])[-1]) if bool(both[:_SLOTS_PER_DAY].any()) else -1
        return (j + 1) * REL_SLOT_MIN - 1440 if j >= 0 else -7 * 1440
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
    out = np.full(both.shape[0], -7 * 1440, dtype=np.int64)
    if both.shape[0] == 0:
        return out
    if daily:
        b = both[:, :_SLOTS_PER_DAY]
        has = b.any(axis=1)
        j = _SLOTS_PER_DAY - 1 - np.argmax(b[:, ::-1], axis=1)
        return np.where(has, (j + 1) * REL_SLOT_MIN - 1440, out)
    start = (int(day_index) % 7) * _SLOTS_PER_DAY
    order = (start - 1 - np.arange(_SLOTS)) % _SLOTS
    bo = both[:, order]
    has = bo.any(axis=1)
    return np.where(has, -(np.argmax(bo, axis=1) * REL_SLOT_MIN), out)


#: 初期辺の同点(共在の分が同じ相手)の決め方。``hash``=体の元 id の組の混ぜ合わせ(既定・決定論・seed に依らない)・
#: ``id``=相手の行番号の小さい方(8a の初版=大組織で行番号の小さい体に入次数が集まる=390,067 体で最大 1,090)。
REL_TIEBREAKS: Final[tuple[str, ...]] = ("hash", "id")


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


def initial_edges(pop: Any, weekly: Any, n_agents: int, *, k: int = REL_K, day_index: int = 0,
                  density: float = 1.0, minutes_per_tick: float = 1.0, d: float = REL_D,
                  tau: float | None = REL_TAU, tiebreak: str = "hash") -> InitialEdges:
    """W16(世帯・組織・学校セル)+W17(共在)→ 初期辺(有向・体ごとに上位 k − 世帯)。

    ``tau`` が数なら A ≥ τ の辺だけ返す(``None`` なら全部=τ の逆算に使う)。逐次ループ宣言 1。
    ``tiebreak``: 共在の分が同じ相手の順(:data:`REL_TIEBREAKS`・既定 ``hash``)。
    """
    if float(density) not in REL_INIT_DENSITIES:
        raise ValueError(f"rel_init_density は {REL_INIT_DENSITIES} のどれか(いま {density})")
    if tiebreak not in REL_TIEBREAKS:
        raise ValueError(f"tiebreak は {REL_TIEBREAKS} のどれか(いま {tiebreak!r})")
    m = min(int(n_agents), int(pop.n))
    audit: dict[str, Any] = {"density": float(density), "k": int(k), "slot_minutes": REL_SLOT_MIN,
                             "tiebreak": str(tiebreak)}
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
    blks: list[np.ndarray] = []
    n_pairs = 0
    for kind, mem in groups:  # 逐次ループ宣言 1: 組の数ぶん(組の中は行列積)
        g = int(mem.size)
        n_pairs += g * (g - 1)
        slots = slot_cells(weekly, mem)
        mm, bb = copresence(slots)
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
        blks.append(bb[iu, iv])
    audit["candidate_pairs_all"] = int(n_pairs)
    if not us:
        audit["reason"] = "no_groups"
        return InitialEdges(empty, empty, empty, empty, empty, empty, empty, audit)
    u = np.concatenate(us)
    v = np.concatenate(vs)
    kind = np.concatenate(kinds)
    mn = np.concatenate(mins)
    bk = np.concatenate(blks)
    # 同じ組が複数の組に居る(世帯かつ同僚)→ 種別の小さい方(世帯 > 職場 > 学校)を残す
    key = u * (m + 1) + v
    order = np.lexsort((kind, key))
    key, u, v, kind, mn, bk = key[order], u[order], v[order], kind[order], mn[order], bk[order]
    first_of = np.concatenate(([True], key[1:] != key[:-1]))
    u, v, kind, mn, bk = u[first_of], v[first_of], kind[first_of], mn[first_of], bk[first_of]
    hh = kind == REL_KINDS["household"]
    if daily:  # 代表日 → 週の回数(世帯 7・職場/学校 5)
        lut = np.zeros(max(REL_DAYS_PER_WEEK) + 1, dtype=np.float64)
        for kd, dd in REL_DAYS_PER_WEEK.items():  # 種別の数ぶん(3)
            lut[kd] = dd
        bk = bk * lut[kind]
    bk = np.where(hh & (bk <= 0), HOUSEHOLD_MIN_BLOCKS_PER_WEEK, bk)
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
        bk = np.where(~hh & (bk <= 0), 1.0, bk)  # 共在 0 の組織/学校の組=週 1 回と置く
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
    n = np.minimum(65_535, np.round(bk * REL_INIT_WEEKS)).astype(np.int64)
    n = np.maximum(n, 1)
    week_ticks = int(round(REL_INIT_WEEKS * 7 * 1440 / float(minutes_per_tick)))
    first = np.full(u.size, -week_ticks, dtype=np.int64)
    A0 = _activation(n, first, 0, minutes_per_tick, d)
    audit["edges_before_tau"] = int(u.size)
    if tau is not None:
        live = A0 >= float(tau)
        audit["dropped_by_tau"] = int(np.count_nonzero(~live))
        u, v, kind, mn, n, first, A0 = u[live], v[live], kind[live], mn[live], n[live], first[live], A0[live]
    # 直近の共在(ランの日の前へ遡る)=書く辺だけ・辺の塊ごとの配列演算(逐次ループ宣言 1b: 塊の数ぶん=
    # 辺数/4,096・ラン開始時に 1 回)
    last = np.full(u.size, -7 * 1440, dtype=np.int64)
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


# ---------------------------------------------------------------------------- 層
class RelationLayer:
    """関係辺の書き手と読み口(``MemoryLayer`` が持つ・``--relations on`` のランだけ)。"""

    def __init__(self, n_agents: int, k: int = REL_K, *, minutes_per_tick: float = 1.0, d: float = REL_D,
                 tau: float = REL_TAU, s: float = REL_S) -> None:
        self.n = int(n_agents)
        self.k = int(k)
        if self.k < 1:
            raise ValueError(f"rel_k は 1 以上(いま {k})")
        self.minutes_per_tick = float(minutes_per_tick)
        self.d = float(d)
        if not (0.0 < self.d < 1.0):
            raise ValueError(f"rel_d は 0〜1(いま {d})")
        self.tau = float(tau)
        if not math.isfinite(self.tau):
            raise ValueError("rel_tau は有限の実数")
        self.s = float(s)
        self.stats: Counter = Counter()
        self.init_audit: dict[str, Any] = {}

    # ------------------------------------------------------------------ 初期化
    def seed_initial(self, agents: Any, init: InitialEdges) -> None:
        """機械的初期化の辺を書く(ラン開始時に 1 回・体ごとに k 本まで=``initial_edges`` が切ってある)。"""
        self.init_audit = dict(init.audit)
        u = np.asarray(init.u, dtype=np.int64)
        if u.size == 0:
            return
        order = np.lexsort((np.arange(u.size), u))
        us = u[order]
        starts = np.flatnonzero(np.concatenate(([True], us[1:] != us[:-1])))
        slot = np.empty(u.size, dtype=np.int64)
        slot[order] = np.arange(u.size) - np.repeat(starts, np.diff(np.append(starts, u.size)))
        ok = slot < self.k
        R.write_relations(agents, u[ok], slot[ok], init.v[ok], init.kind[ok], np.zeros(int(ok.sum())),
                          init.first[ok], init.last[ok], init.n[ok])
        self.stats["init_edges"] += int(ok.sum())
        for kd, c in Counter(init.kind[ok].tolist()).items():  # 種別の数ぶん(≤ 5)
            self.stats[f"init_edges:{REL_KIND_NAMES[int(kd)]}"] += int(c)

    # ------------------------------------------------------------------ 書き手
    def on_episodes(self, agents: Any, tick: int, a: np.ndarray, kind: np.ndarray, partner: np.ndarray,
                    result: np.ndarray) -> None:
        """記憶のエピソード(会話・手伝いで相手のあるもの)→ 辺(配列演算・体ごとに 1 件ずつの回)。"""
        a = np.asarray(a, dtype=np.int64)
        if a.size == 0:
            return
        kind = np.asarray(kind, dtype=np.int64)
        partner = np.asarray(partner, dtype=np.int64)
        result = np.asarray(result, dtype=np.int64)
        known = np.isin(result, list(_SIGN_OF_RESULT))
        pick = (np.isin(kind, (_TALK, _HELP)) & (partner >= 0) & (partner < self.n) & (partner != a) & known)
        if not bool(pick.any()):
            return
        a, partner, result = a[pick], partner[pick], result[pick]
        sign = np.fromiter((_SIGN_OF_RESULT[int(x)] for x in result.tolist()), dtype=np.int64,
                           count=result.size)  # 事象の数ぶん
        for sg, c in Counter(sign.tolist()).items():  # 符号の数ぶん(≤ 3)
            self.stats["events:sign" + _SIGN_LABEL[int(sg)]] += int(c)
        self.stats["events"] += int(a.size)
        order = np.lexsort((np.arange(a.size), a))
        sa = a[order]
        starts = np.flatnonzero(np.concatenate(([True], sa[1:] != sa[:-1])))
        rank = np.empty(a.size, dtype=np.int64)
        rank[order] = np.arange(a.size) - np.repeat(starts, np.diff(np.append(starts, a.size)))
        for rnd in range(int(rank.max()) + 1):  # 逐次ループ宣言 2: 体あたりの件数の最大ぶん
            sel = np.flatnonzero(rank == rnd)
            self._write_round(agents, tick, a[sel], partner[sel], sign[sel])

    def _write_round(self, agents: Any, tick: int, a: np.ndarray, partner: np.ndarray, sign: np.ndarray) -> None:
        r = agents.registry
        rows = r.rel_partner[a].astype(np.int64)
        hit = rows == partner[:, None]
        found = hit.any(axis=1)
        slot = np.where(found, np.argmax(hit, axis=1), -1)
        empty = rows == REL_EMPTY
        new = ~found
        has_empty = empty.any(axis=1)
        slot = np.where(new & has_empty, np.argmax(empty, axis=1), slot)
        evict = new & ~has_empty
        if bool(evict.any()):
            A = self.activation(agents, a[evict], tick)
            slot[evict] = np.argmin(A, axis=1)  # 同点は行番号の小さい方
            self.stats["evictions"] += int(np.count_nonzero(evict))
            for kd, c in Counter(r.rel_kind[a[evict], slot[evict]].astype(np.int64).tolist()).items():
                self.stats[f"evicted_kind:{REL_KIND_NAMES.get(int(kd), kd)}"] += int(c)
        old_kind = r.rel_kind[a, slot].astype(np.int64)
        old_sign = r.rel_sign[a, slot].astype(np.int64)
        old_first = r.rel_first[a, slot].astype(np.int64)
        old_n = r.rel_n[a, slot].astype(np.int64)
        kind = np.where(found, old_kind, REL_KINDS["acquaintance"])
        sg = np.clip(np.where(found, old_sign, 0) + sign, -127, 127)
        first = np.where(found, old_first, int(tick))
        n = np.where(found, np.minimum(old_n + 1, 65_535), 1)
        R.write_relations(agents, a, slot, partner, kind, sg, first, np.full(a.size, int(tick)), n)
        self.stats["merged"] += int(np.count_nonzero(found))
        self.stats["new_edges"] += int(np.count_nonzero(new))

    # ------------------------------------------------------------------ 読み口
    def activation(self, agents: Any, agent_ids: np.ndarray, tick: int) -> np.ndarray:
        """体の配列 → ``(体, k)`` の A(空の辺は −inf)。"""
        r = agents.registry
        a = np.asarray(agent_ids, dtype=np.int64)
        A = _activation(r.rel_n[a], r.rel_first[a], tick, self.minutes_per_tick, self.d)
        return np.where(r.rel_partner[a] == REL_EMPTY, -np.inf, A)

    def strength(self, A: np.ndarray) -> np.ndarray:
        """A → 強さ P(0..255・uint8)。"""
        with np.errstate(over="ignore"):
            p = 1.0 / (1.0 + np.exp(-(np.asarray(A, dtype=np.float64) - self.tau) / self.s))
        return np.clip(np.round(p * 255.0), 0, 255).astype(np.uint8)

    def edges(self, agents: Any, agent_id: int, tick: int) -> RelationEdges:
        """1 体の生きている辺(A ≥ τ_rel・A の降順・同点は行番号)。"""
        r = agents.registry
        i = int(agent_id)
        A = self.activation(agents, np.asarray([i]), tick)[0]
        live = np.flatnonzero(A >= self.tau)
        live = live[np.lexsort((live, -A[live]))]
        return RelationEdges(
            partner=r.rel_partner[i][live].astype(np.int64), kind=r.rel_kind[i][live].astype(np.int64),
            sign=np.sign(r.rel_sign[i][live]).astype(np.int64), A=A[live], P=self.strength(A[live]), row=live,
        )

    def acquaintances(self, agents: Any, agent_id: int, tick: int) -> np.ndarray:
        """描画の「知人」=生きている辺の相手(A ≥ τ_rel・行番号の順・≤ k・呼ごと O(k))。"""
        r = agents.registry
        i = int(agent_id)
        p = r.rel_partner[i]
        used = p != REL_EMPTY
        if not bool(used.any()):
            return np.zeros(0, dtype=np.int64)
        A = _activation(r.rel_n[i][used], r.rel_first[i][used], tick, self.minutes_per_tick, self.d)
        return p[used][A >= self.tau].astype(np.int64)

    def partners_in_cell(self, agents: Any, agent_ids: np.ndarray, tick: int) -> np.ndarray:
        """体の配列 → ``(体, k)`` の「同じセルに居る生きている辺の相手」(他は −1・体 × k の配列演算)。"""
        r = agents.registry
        a = np.asarray(agent_ids, dtype=np.int64)
        p = r.rel_partner[a].astype(np.int64)
        live = (p != REL_EMPTY) & (self.activation(agents, a, tick) >= self.tau)
        cell = np.asarray(r.cell, dtype=np.int64)
        pc = np.where(live, cell[np.where(live, p, 0)], -2)
        same = live & (pc == cell[a][:, None]) & (cell[a][:, None] >= 0)
        return np.where(same, p, -1)

    def weights_for_invite(self, agents: Any, agent_id: int, tick: int) -> tuple[np.ndarray, np.ndarray, float]:
        """招待の重み(Dunbar 2020): 強さの上位 5 人で 40%・次の 10 人で 20%・残り 40%=辺の無い同席者(8b)。

        層の人数が足りなければ、その層の割合を居る人で等分する(居ない層の割合は残りへ回す=宣言)。
        Returns: ``(相手, 重み, 残りの割合)``。
        """
        e = self.edges(agents, agent_id, tick)
        w = np.zeros(e.partner.size, dtype=np.float64)
        rest = 1.0
        lo = 0
        for size, share in REL_INVITE_LAYERS:  # 層の数ぶん(2)
            hi = min(lo + size, e.partner.size)
            if hi > lo:
                w[lo:hi] = share / (hi - lo)
                rest -= share
            lo += size
        return e.partner, w, round(rest, 6)

    # ------------------------------------------------------------------ 監査
    def summary(self, agents: Any, tick: int) -> dict[str, Any]:
        """manifest ``relations``: 辺/体・種別・符号・A/P の分布・τ で落ちた辺・押し出し・初期網の監査。"""
        r = agents.registry
        all_ids = np.arange(self.n, dtype=np.int64)
        used = r.rel_partner != REL_EMPTY
        A = self.activation(agents, all_ids, tick)
        live = used & (A >= self.tau)
        per = live.sum(axis=1)

        def q(x: np.ndarray) -> dict[str, float]:
            x = np.asarray(x, dtype=np.float64)
            if x.size == 0:
                return {}
            return {p: round(float(np.percentile(x, float(p[1:]))), 4)
                    for p in ("p0", "p10", "p50", "p90", "p99", "p100")} | {"mean": round(float(x.mean()), 4)}

        kinds = r.rel_kind[live].astype(np.int64)
        signs = np.sign(r.rel_sign[live]).astype(np.int64)
        deg = np.bincount(per, minlength=self.k + 1)
        init = dict(self.init_audit)
        return {
            "k": self.k, "tau": self.tau, "d": self.d, "s": self.s,
            "row_bytes_actual": REL_ROW_BYTES_ACTUAL, "row_bytes_declared": REL_ROW_BYTES_DECLARED,
            "counts": {k_: int(v) for k_, v in sorted(self.stats.items())},
            "edges_live_per_agent": q(per),
            "edges_live_total": int(live.sum()),
            "edges_below_tau": int((used & ~live).sum()),
            "agents_with_edges": int(np.count_nonzero(per > 0)),
            "degree_histogram": {str(i): int(c) for i, c in enumerate(deg.tolist()) if c},
            "degree_regular": bool(np.count_nonzero(deg) <= 1),
            "kinds": {REL_KIND_NAMES.get(int(k_), str(k_)): int(c) for k_, c in sorted(Counter(kinds.tolist()).items())},
            "signs": {str(int(k_)): int(c) for k_, c in sorted(Counter(signs.tolist()).items())},
            "A": q(A[live]),
            "P": q(self.strength(A[live]).astype(np.float64)),
            "n_per_edge": q(r.rel_n[live]),
            "dunbar_layers": {"agents_with_5_or_more": int(np.count_nonzero(per >= 5)),
                              "agents_with_15": int(np.count_nonzero(per >= 15))},
            "init": init,
        }
