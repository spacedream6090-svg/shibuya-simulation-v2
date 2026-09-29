"""engine.relations — **関係辺の表と導出**(C10 8a・第299)+**会話の起点と相手選択**(C10 8b)。

正典: ``docs/design/v2-c10-relations-implementation-agenda.md`` §1(段 8a の 1〜8・第299 印=Q89〜Q99)・§2(段 8b の
1〜6)・§4。上位=``docs/design/v2-c10-relations-agenda.md`` §4(R1〜R14+R9′)・§5 と追記(D-93 (a)〜(d))・
``docs/research/v2-c10-initial-relations-research.md`` §6-1・記憶アジェンダ M12。入れ物は記憶 第 1 段と同じ
(``engine.memory.MemoryLayer`` が持つ・腕でだけ確保・書き手は resolve・A の近似)。8c(語彙 v3.1)・8d(約束)・
ウォームアップの強制ペアは含めない。

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
    新しい相手も辺として比べる: 表の最弱の A が新しい辺(n=1・L=0)の A 以上なら新しい方を落とす(8b・宣言)。
    同席(COPRESENT・8b の腕 ``--rel-copresent on``・既定 off=第299 Q91): 同セル・2 m 内・連続 5 分で 1 本・
    相手ごと 1 日 1 本・**表に居る相手だけ**(知らない同席者は辺を作らない=宣言)・符号 +0。

機械的初期化(R2 (a)・D-93 (c)・「初期関係が下地」・:func:`initial_edges`)
    ラン開始時に W16(世帯・組織・学校セル)と W17(週次表)から: (i) 世帯=同一世帯の全ペア(種別 1)
    (ii) 職場/学校=同一組織/学校セルの体のうち、W17 で**同じセル・同じ時間帯**に居る時間(共在・15 分の枠)が
    長い順に、世帯を除いた残り枠(≤ k − 世帯)へ(種別 2/3・共在の分が同じ相手の順は体の元 id の組の混ぜ合わせ=
    行番号の順にしない=大組織の入次数の偏りを避ける・:data:`REL_TIEBREAKS`)(iii) 常連(4)は作らない。
    **第299 Q89/Q90**: 辺ごとの在職期間 T_uv を組の hash で 1〜13 週に一様に散らす(``tenure_weeks``・感度 26)・
    first=−T_uv・last=直近の共在(ランの日の前へ遡る)。**第300 訂正(8b′)**: n=**共在のあった日数/週** × T_uv
    (1 日 1 本=ラン中の会話 1 セッション・同席 1 日 1 本と同じ単位・代表日の係数 世帯 7・職場/学校 5)。15 分枠の
    共在時間は上位 k の順位付け(と密度の腕)にだけ使う。世帯で共在が取れない(域外の自宅=セル未解決)ペアは
    毎日=7 日/週と置く(宣言)。A ≥ τ_rel の辺だけ書く。

会話の起点と相手選択(8b・R5・R7 (a)・R12・R13・:meth:`RelationLayer.choose_talk_partners`)
    名指しの無い会話の相手=同セルの生きている辺の相手に Dunbar 2020 の重み(内側 5 人 40%・次の 10 人 20%・
    残り 40%=辺の無い同席者・居る層で再正規化=Q99)+seed つき乱択(``core.hashing.relation_invite_key_array``)。
    2 m 内の知人が居ればその中から(偶然=第一候補)。同セルに辺が無ければ従来の同席者のハッシュ順。起点=招待/
    偶然/知人出現(:data:`REL_ORIGINS`)。知人出現の起床(``WakeCondition.ACQUAINTANCE``)=生きている辺の相手が
    同セルに現れた tick(前 tick は同セルでなかった)・同一相手 60 分(:meth:`acquaintance_candidates`)。

逐次ループ宣言(P4)
    1. :func:`initial_edges`: 組(世帯・組織・学校セル)の数ぶん(ラン開始時に 1 回・組の中は行列積)。
       1b. 直近の共在: 書く辺の塊(4,096 辺)の数ぶん(ラン開始時に 1 回・塊の中は配列演算)。
    2. :meth:`RelationLayer.on_episodes`: 体あたりの相互作用の件数の最大ぶん(同じ体の 2 件目を次の回へ)。
    3. 読み口 :meth:`RelationLayer.edges` / :meth:`partners_in_cell` / :meth:`weights_for_invite` は配列演算。
    4. 8b の毎 tick: 同セルの辺の集め(体 × k の int32 1 回=``_same_cell_hits``)を同席と知人出現が共有・
       その当たりだけの配列演算。抽選は会話の行 × k の配列演算(起点の控えは会話の行の数ぶん)。
    SoA の外(腕だけ): 同席=欄ごとの始まりの tick int32+日 int16(体あたり 90 B)・知人出現=同一相手の不応期
    int32(体あたり 60 B)・前 tick のセル int32(4 B)・相手に選ばれた回数 int64(8 B)。
"""

from __future__ import annotations

import math
from collections import Counter
from types import SimpleNamespace
from typing import Any, Final, NamedTuple

import numpy as np

from shibuya.agents.state import REL_EMPTY, WAKE_CONDITION_CLASS, ResultCode, WakeCondition
from shibuya.core.hashing import relation_invite_key_array
from shibuya.engine import resolve as R

__all__ = [
    "REL_K",
    "REL_MODES",
    "REL_KINDS",
    "REL_KIND_NAMES",
    "REL_D",
    "REL_TAU",
    "REL_TAU_V1",
    "REL_TAU_BY_TENURE_HASH",
    "REL_TENURE_HASHES",
    "DEFAULT_REL_TENURE_HASH",
    "check_rel_tenure_hash",
    "REL_S",
    "REL_TENURE_WEEKS",
    "REL_SLOT_MIN",
    "REL_ROW_BYTES_ACTUAL",
    "REL_ROW_BYTES_DECLARED",
    "REL_INIT_DENSITIES",
    "REL_INVITE_LAYERS",
    "HOUSEHOLD_MIN_DAYS_PER_WEEK",
    "copresence_days",
    "REL_COPRESENT_MINUTES",
    "REL_COPRESENT_METERS",
    "REL_ACQ_PAIR_REFRACTORY_MIN",
    "REL_ORIGINS",
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
#: 在職期間 T_uv のハッシュの版(第2波 §2A 項 2)。``v2``(既定)=同点の順のハッシュ ``_pair_mix(元 id_u, 元 id_v)``
#: と独立な混ぜ合わせ(向きのない組の ``_pair_mix`` にもう 1 段 splitmix64 を塩つきでかける)/ ``v1``=旧
#: (``_pair_mix(min, max)``=元 id_u < 元 id_v の辺で同点の順と同じ値=同点の多い組で在職の短い相手ほど選ばれる欠陥・
#: 旧 golden の再現用)。
REL_TENURE_HASHES: Final[tuple[str, ...]] = ("v2", "v1")
DEFAULT_REL_TENURE_HASH: Final[str] = "v2"
#: v2 の塩(未リサーチ=expedient・値そのものに意味はない=黄金比の 64 bit 表現と異なる定数なら何でもよい)。
_TENURE_SALT_V2: Final[int] = 0xD1B54A32D192ED03
#: 共在を数える時間の枠[分](週 7 日 × 96 枠)。
REL_SLOT_MIN: Final[int] = 15
#: 1 辺の実バイト(4+1+1+4+4+2)と宣言バイト(同じ)。
REL_ROW_BYTES_ACTUAL: Final[int] = 16
REL_ROW_BYTES_DECLARED: Final[int] = 16
#: 初期網の密度の腕(×0.5=共在が中央値より長い組だけ・×1=共在 > 0・×2=共在 0 の組織/学校の組も入れる)。
REL_INIT_DENSITIES: Final[tuple[float, ...]] = (0.5, 1.0, 2.0)
#: 招待の重み(Dunbar 2020: 内側 5 人に 40%・次の 10 人に 20%・残り 40%=辺の無い同席者=8b が読む)。
REL_INVITE_LAYERS: Final[tuple[tuple[int, float], ...]] = ((5, 0.40), (10, 0.20))
#: 世帯で共在が取れない(自宅が域外)ペアの「共在のあった日数/週」(毎日=7・宣言=第299 Q92 の床 7 回/週)。
HOUSEHOLD_MIN_DAYS_PER_WEEK: Final[int] = 7
#: 同席(COPRESENT・第299 Q91・R-36 §6-1 の初期案=expedient): 同セル・距離 2 m 内・連続 5 分で 1 本・
#: 相手ごと 1 日 1 本まで。**表に居る相手(辺)だけ**を強める(知らない同席者は辺を作らない=宣言)。
REL_COPRESENT_MINUTES: Final[int] = 5
REL_COPRESENT_METERS: Final[float] = 2.0
#: 知人出現の起床(R7 (a))の同一相手の不応期[分](知覚契約 §6「同一相手 60 分」)。
REL_ACQ_PAIR_REFRACTORY_MIN: Final[int] = 60
#: 会話の起点の種別(8b 診断行): 招待=自分で会話を選んだ・偶然=相手が 2 m 内の知人・知人出現=その起床の呼。
REL_ORIGINS: Final[tuple[str, ...]] = ("invite", "chance", "acquaintance")
_ACQ: Final[int] = int(WakeCondition.ACQUAINTANCE)
#: W17 が **1 日ぶんしか無い**(全体が曜日 0 だけ=実資産の事実)とき、その日を「代表日」として「共在のあった
#: 日数/週」に直す日数(世帯 7・職場 5・学校 5=宣言・expedient)。複数の曜日がある表では共在のあった曜日の数。
REL_DAYS_PER_WEEK: Final[dict[int, int]] = {1: 7, 2: 5, 3: 5}
_SLOTS_PER_DAY: Final[int] = 1440 // REL_SLOT_MIN
_SLOTS: Final[int] = 7 * _SLOTS_PER_DAY
_TALK: Final[int] = 7
#: 招待の層の外(k=50 の腕の 16 番目以降の辺)は「残り」の層に入れる(宣言)。
_REST_SHARE: Final[float] = 1.0 - sum(s for _, s in REL_INVITE_LAYERS)
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


def check_rel_tenure_hash(version: str) -> str:
    """``--rel-tenure-hash`` の値を検める。"""
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
    first = -np.round(tw * 7.0 * 1440.0 / float(minutes_per_tick)).astype(np.int64)
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


def _rank_live(A: np.ndarray, tau: float) -> np.ndarray:
    """``(m, k)`` の A → 生きている辺(A ≥ τ)の強さの順位(0=最強・同点は欄の小さい方)・それ以外 −1。"""
    m, k = A.shape
    live = A >= float(tau)
    key = np.where(live, -A, np.inf)
    order = np.argsort(key, axis=1, kind="stable")
    rank = np.empty((m, k), dtype=np.int64)
    rank[np.arange(m)[:, None], order] = np.arange(k)[None, :]
    return np.where(live, rank, -1)


def _layer_weights(rank: np.ndarray, cand: np.ndarray, rest_present: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """招待の重み(Dunbar 2020・第299 Q99=**居る層で再正規化**)。

    ``rank``=生きている辺の順位(``_rank_live``)・``cand``=候補の辺・``rest_present``=辺の無い同席者が居るか。
    内側 5 人 40%・次の 10 人 20%・残り 40%(辺の無い同席者+16 番目以降の辺=宣言)。層の中は等分。
    Returns: ``(辺の重み (m, k), 残りの人の重み (m,))``(行の合計 1・候補が無い行は 0)。
    """
    rest_present = np.asarray(rest_present, dtype=bool)
    w = np.zeros(rank.shape, dtype=np.float64)
    total = np.zeros(rank.shape[0], dtype=np.float64)
    lo = 0
    for size, share in REL_INVITE_LAYERS:  # 層の数ぶん(2)
        mem = cand & (rank >= lo) & (rank < lo + size)
        cnt = mem.sum(axis=1)
        s = np.where(cnt > 0, share, 0.0)
        w += np.where(mem, (s / np.maximum(cnt, 1))[:, None], 0.0)
        total += s
        lo += size
    beyond = cand & (rank >= lo)
    n_rest = beyond.sum(axis=1) + rest_present.astype(np.int64)
    s_rest = np.where(n_rest > 0, _REST_SHARE, 0.0)
    per = s_rest / np.maximum(n_rest, 1)
    w += np.where(beyond, per[:, None], 0.0)
    w_rest = np.where(rest_present, per, 0.0)
    total += s_rest
    ok = total > 0
    w = np.where(ok[:, None], w / np.where(ok, total, 1.0)[:, None], 0.0)
    w_rest = np.where(ok, w_rest / np.where(ok, total, 1.0), 0.0)
    return w, w_rest


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
        # ---- 8b(会話の起点): 招待の重みの抽選の塩・起点の控え・相手に選ばれた回数(T5 の材料) ----
        self._invite_salt: bytes | None = None
        self.origin_of: dict[int, int] = {}
        self.chosen_count: np.ndarray | None = None
        # ---- 8b(Q91 同席): 2 m 内が続いている始まりの tick・最後に書いた日(平らな体 × k・SoA の外=腕だけ) ----
        self._co_since: np.ndarray | None = None
        self._co_day: np.ndarray | None = None
        self._co_active = np.zeros(0, dtype=np.int64)
        # ---- 8b: 同セルの辺の集め(同じ tick の同席と知人出現で共有) ----
        self._hits: tuple[np.ndarray, np.ndarray, np.ndarray] | None = None
        self._hits_tick = -1
        self._co_minutes = float(REL_COPRESENT_MINUTES)
        self._co_meters = float(REL_COPRESENT_METERS)
        # ---- 8b(R7 (a) 知人出現): 同一相手の不応期(体 × k)・前 tick のセル・この tick の候補 ----
        self._acq_until: np.ndarray | None = None
        self._acq_pair_ticks = 0
        self._prev_cell: np.ndarray | None = None
        self._acq_pending: tuple[np.ndarray, np.ndarray] = (np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int64))
        #: 壁時計(決定論でない・manifest の ``wall_seconds_nondeterministic``)。
        self.wall: Counter = Counter()

    @property
    def copresent_on(self) -> bool:
        return self._co_since is not None

    @property
    def acq_wake_on(self) -> bool:
        return self._acq_until is not None

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
            # 8b(宣言): 新しい相手も「辺」として比べる=新しい辺(n=1・L=0 の A)が表の最弱以下なら新しい方を落とす
            a_new = math.log(1.0 / (1.0 - self.d))
            lose = np.zeros(a.size, dtype=bool)
            lose[np.flatnonzero(evict)] = A.min(axis=1) >= a_new
            if bool(lose.any()):
                self.stats["newcomer_dropped"] += int(np.count_nonzero(lose))
                keep_ = ~lose
                a, partner, sign, found, slot, new, evict = (a[keep_], partner[keep_], sign[keep_], found[keep_],
                                                             slot[keep_], new[keep_], evict[keep_])
                if a.size == 0:
                    return
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
        if bool(new.any()):
            self._reset_slots(a[new], slot[new])

    def _reset_slots(self, a: np.ndarray, slot: np.ndarray) -> None:
        """欄の相手が替わった(新しい辺)→ 同席の連続・同一相手の不応期をその欄だけ空に戻す。"""
        if self._co_since is not None:
            f = np.asarray(a, dtype=np.int64) * self.k + np.asarray(slot, dtype=np.int64)
            self._co_since[f] = -1
            self._co_day[f] = -1
            self._co_active = self._co_active[~np.isin(self._co_active, f)]
        if self._acq_until is not None:
            self._acq_until[a, slot] = -1

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

    def weights_for_invite(self, agents: Any, agent_id: int, tick: int, *,
                           rest_present: bool = True) -> tuple[np.ndarray, np.ndarray, float]:
        """招待の重み(Dunbar 2020): 強さの上位 5 人で 40%・次の 10 人で 20%・残り 40%=辺の無い同席者。

        第299 Q99: **居る層で再正規化**(層の中は等分・居ない層の割合は居る層へ比例配分)。セルでは絞らない
        (8b の抽選は :meth:`choose_talk_partners` が同セルの辺だけで同じ規則を使う)。
        Returns: ``(相手=A の降順, 重み, 残りの人の重み)``。
        """
        e = self.edges(agents, agent_id, tick)
        if e.partner.size == 0:
            return e.partner, np.zeros(0, dtype=np.float64), (1.0 if rest_present else 0.0)
        rank = np.arange(e.partner.size, dtype=np.int64)[None, :]
        w, w_rest = _layer_weights(rank, np.ones_like(rank, dtype=bool), np.asarray([bool(rest_present)]))
        return e.partner, w[0], round(float(w_rest[0]), 6)

    # ------------------------------------------------------------------ 8b: 会話の相手と起点
    def enable_invite(self, run_salt: bytes) -> None:
        """招待の相手の抽選(seed つき決定論)を開く。"""
        self._invite_salt = bytes(run_salt)
        self.chosen_count = np.zeros(self.n, dtype=np.int64)

    def choose_talk_partners(self, agents: Any, tick: int, a: np.ndarray, fallback: np.ndarray,
                             named_ok: np.ndarray, condition: np.ndarray, *,
                             record_origin: bool = True) -> tuple[np.ndarray, np.ndarray]:
        """会話の相手(R5・R12・D-31 (b))と起点(招待/偶然/知人出現)。配列演算(体 × k)。

        - 名指し(``named_ok``)の行は相手を変えない(起点だけ付ける)。
        - 名指しの無い行: 同セルの**生きている辺**の相手を、**2 m 内の知人が居ればその中から**(偶然=第一候補・
          残りの層は付けない)、居なければ同セルの辺+残り(``fallback``=従来の同席者のハッシュ順・辺の相手でない
          とき)から、:func:`_layer_weights` の重みで seed つきに引く。同セルに辺が無ければ ``fallback`` のまま
          (従来どおり=D-31 (a))。
        - 起点: 起床が知人出現 → ``acquaintance``・相手が 2 m 内の知人 → ``chance``・それ以外 → ``invite``。

        Returns: ``(相手, 起点の索引)``。起点は :attr:`origin_of` にも控える(run が招待の計数に使う・
        ``record_origin=False``=classical 方策の呼の時点の選び=控えない)。
        """
        a = np.asarray(a, dtype=np.int64)
        fb = np.asarray(fallback, dtype=np.int64)
        named_ok = np.asarray(named_ok, dtype=bool)
        cond = np.asarray(condition, dtype=np.int64)
        if a.size == 0:
            return fb.copy(), np.zeros(0, dtype=np.int64)
        r = agents.registry
        p = r.rel_partner[a].astype(np.int64)
        A = self.activation(agents, a, tick)
        rank = _rank_live(A, self.tau)
        live = rank >= 0
        cell = np.asarray(r.cell, dtype=np.int64)
        ca = cell[a]
        pp = np.where(live, p, 0)
        in_cell = live & (cell[pp] == ca[:, None]) & (ca[:, None] >= 0)
        xy = np.asarray(r.xy, dtype=np.float64)
        d2 = ((xy[pp] - xy[a][:, None, :]) ** 2).sum(axis=-1)
        near = in_cell & (d2 <= float(R.TALK_OPEN_METERS) ** 2)
        has_near = near.any(axis=1)
        cand = np.where(has_near[:, None], near, in_cell)
        fb_is_edge = ((p == fb[:, None]) & in_cell).any(axis=1)
        rest_present = ~has_near & (fb >= 0) & ~fb_is_edge
        w, w_rest = _layer_weights(rank, cand, rest_present)
        total = w.sum(axis=1) + w_rest
        pick = ~named_ok & (total > 0) & cand.any(axis=1)
        out = fb.copy()
        if bool(pick.any()) and self._invite_salt is not None:
            key = relation_invite_key_array(self._invite_salt, int(tick), a[pick])
            u = (key >> np.uint64(11)).astype(np.float64) / float(1 << 53)
            cum = np.cumsum(np.concatenate([w[pick], w_rest[pick][:, None]], axis=1), axis=1)
            idx = (cum < (u * cum[:, -1])[:, None]).sum(axis=1)
            idx = np.minimum(idx, self.k)
            rows = np.flatnonzero(pick)
            got_edge = idx < self.k
            out[rows[got_edge]] = p[rows[got_edge], idx[got_edge]]
            r_edge = rank[rows[got_edge], idx[got_edge]]
            for name, sel in (("inner", r_edge < 5), ("next", (r_edge >= 5) & (r_edge < 15)),
                              ("beyond", r_edge >= 15)):  # 層の数ぶん(3)
                self.stats[f"invite_pick:{name}"] += int(np.count_nonzero(sel))
            self.stats["invite_pick:rest"] += int(np.count_nonzero(~got_edge))
            self.stats["invite_pick:near_first"] += int(np.count_nonzero(has_near[rows]))
            if self.chosen_count is not None:
                ch = out[rows]
                ch = ch[ch >= 0]
                np.add.at(self.chosen_count, ch, 1)
        self.stats["invite_named"] += int(np.count_nonzero(named_ok))
        self.stats["invite_fallback_only"] += int(np.count_nonzero(~named_ok & ~pick))
        # 起点(名指しの行も同じ規則)
        chosen_near = ((p == out[:, None]) & near).any(axis=1)
        origin = np.where(cond == _ACQ, 2, np.where(chosen_near & (out >= 0), 1, 0)).astype(np.int64)
        if record_origin:
            for ag, o in zip(a.tolist(), origin.tolist()):  # 逐次: 会話の行の数ぶん(≤ 1 tick の呼数)
                self.origin_of[int(ag)] = int(o)
        return out, origin

    def pick_rest(self, tick: int, agent_id: int, candidates: Any) -> int:
        """「残り」の層の 1 人(辺の無い同席者の候補から seed つきハッシュ順=id の順にしない・D-31 (a))。

        classical 方策の呼の時点の選び(近接行の「未知」の人)に使う。候補が無ければ −1。
        """
        c = np.unique(np.asarray(list(candidates), dtype=np.int64))
        c = c[(c >= 0) & (c != int(agent_id))]
        if c.size == 0 or self._invite_salt is None:
            return int(c[0]) if c.size else -1
        key = relation_invite_key_array(self._invite_salt + b"|rest", int(tick), np.asarray([int(agent_id)]))
        return int(c[int(key[0] % np.uint64(c.size))])

    def pop_origin(self, agent_id: int) -> int:
        """招待を出した体の起点(無ければ 0=招待)。1 回読むと消える。"""
        return int(self.origin_of.pop(int(agent_id), 0))

    # ------------------------------------------------------------------ 8b: 同セルの辺(毎 tick 1 回の集め)
    def _same_cell_hits(self, agents: Any, tick: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """いま**同じセル**に居る辺 ``(体, 欄, 相手)``(体 × k の 1 回の集め・同じ tick の 2 回目は控えを返す)。

        同席の書き手と知人出現の検出が共有する(P4 宣言: 毎 tick ``n × k`` の int32 の集め 1 回)。
        """
        if self._hits_tick == int(tick) and self._hits is not None:
            return self._hits
        r = agents.registry
        cell = np.asarray(r.cell)
        p = np.asarray(r.rel_partner)
        same = cell[p] == cell[:, None]            # 空の欄(−1)は下の p ≥ 0 で落とす
        same &= p != REL_EMPTY
        same &= (cell >= 0)[:, None]
        a, j = np.nonzero(same)
        self._hits = (a.astype(np.int64), j.astype(np.int64), p[a, j].astype(np.int64))
        self._hits_tick = int(tick)
        return self._hits

    # ------------------------------------------------------------------ 8b: 同席(Q91)
    def enable_copresent(self, *, minutes: float = REL_COPRESENT_MINUTES,
                         meters: float = REL_COPRESENT_METERS) -> None:
        """同席の書き手を開く(``--rel-copresent on``)。欄ごとの「2 m 内が続いている始まりの tick」(int32)と
        「最後に書いた日」(int16)を平らな配列で持つ(SoA の外・腕だけ)。"""
        self._co_since = np.full(self.n * self.k, -1, dtype=np.int32)
        self._co_day = np.full(self.n * self.k, -1, dtype=np.int16)
        self._co_active = np.zeros(0, dtype=np.int64)
        self._co_minutes = float(minutes)
        self._co_meters = float(meters)

    def copresent_step(self, agents: Any, tick: int) -> None:
        """同じセル・2 m 内に辺の相手が居る欄を数え、連続 5 分で 1 本(相手ごと 1 日 1 本)を辺に書く。

        書く=``n``+1・``last``=tick・符号は +0(同席のみ=0・R-36 §2-5 C)。表に居ない同席者は書かない。
        逐次ループ宣言: なし(同セルの辺の集め 1 回+その当たりだけの配列演算・毎 tick)。
        """
        if self._co_since is None:
            return
        r = agents.registry
        a, j, v = self._same_cell_hits(agents, tick)
        if a.size:
            xy = np.asarray(r.xy, dtype=np.float64)
            dd = xy[v] - xy[a]
            near = (dd * dd).sum(axis=1) <= self._co_meters ** 2
            a, j = a[near], j[near]
        flat = a * self.k + j                       # 体の昇順 → 欄の昇順(nonzero の並び)=整列済み
        old = self._co_active
        gone = old[~np.isin(old, flat, assume_unique=True)]
        self._co_since[gone] = -1
        fresh = flat[~np.isin(flat, old, assume_unique=True)]
        self._co_since[fresh] = int(tick)
        self._co_active = flat
        if flat.size == 0:
            return
        day = int(int(tick) * self.minutes_per_tick // 1440)
        run = (int(tick) - self._co_since[flat].astype(np.int64) + 1) * self.minutes_per_tick
        fire = (run >= self._co_minutes) & (self._co_day[flat] != day)
        if not bool(fire.any()):
            return
        a, j, f = a[fire], j[fire], flat[fire]
        self._co_day[f] = day
        n = np.minimum(r.rel_n[a, j].astype(np.int64) + 1, 65_535)
        R.write_relations(agents, a, j, r.rel_partner[a, j].astype(np.int64), r.rel_kind[a, j].astype(np.int64),
                          r.rel_sign[a, j].astype(np.int64), r.rel_first[a, j].astype(np.int64),
                          np.full(a.size, int(tick)), n)
        self.stats["copresent_events"] += int(a.size)
        for kd, c in Counter(r.rel_kind[a, j].astype(np.int64).tolist()).items():  # 種別の数ぶん(≤ 5)
            self.stats[f"copresent_events:{REL_KIND_NAMES.get(int(kd), kd)}"] += int(c)

    # ------------------------------------------------------------------ 8b: 知人出現の起床(R7 (a))
    def enable_acquaintance_wake(self, *, pair_refractory_min: float = REL_ACQ_PAIR_REFRACTORY_MIN) -> None:
        """知人出現の起床を開く。同一相手の不応期(体 × k・int32)を持つ。"""
        self._acq_until = np.full((self.n, self.k), -1, dtype=np.int32)
        self._acq_pair_ticks = int(round(float(pair_refractory_min) / self.minutes_per_tick))

    def acquaintance_candidates(self, agents: Any, tick: int,
                                eligible: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """知人(A ≥ τ)が同セルに**現れた** tick(前 tick は同セルでなかった)の起床候補(1 体 1 件・最強の相手)。

        ``eligible``=候補にしてよい体(起きていて舞台に居る=アービタが落とさない体)。前 tick のセルは全体で持つ。
        同一相手の不応期 60 分で落とす。1 tick 目は「前 tick」が無いので出さない(宣言)。
        逐次ループ宣言: なし(同セルの辺の集め 1 回+その当たりだけの配列演算・毎 tick)。
        """
        empty = (np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int8), np.zeros(0, dtype=np.int64))
        self._acq_pending = (np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int64))
        if self._acq_until is None:
            return empty
        r = agents.registry
        prev = self._prev_cell
        self._prev_cell = np.array(r.cell, copy=True)
        if prev is None:
            return empty
        a, j, v = self._same_cell_hits(agents, tick)
        if a.size == 0:
            return empty
        pa = prev[a]
        appear = (prev[v] != pa) | (pa < 0)        # 前 tick は同じセルでなかった
        if eligible is not None:
            appear &= np.asarray(eligible, dtype=bool)[a]
        a, j = a[appear], j[appear]
        self.stats["acq_appear"] += int(a.size)
        if a.size == 0:
            return empty
        ok = self._acq_until[a, j] <= int(tick)
        self.stats["acq_pair_refractory"] += int(np.count_nonzero(~ok))
        a, j = a[ok], j[ok]
        A = _activation(r.rel_n[a, j], r.rel_first[a, j], tick, self.minutes_per_tick, self.d)
        live = A >= self.tau
        self.stats["acq_not_live"] += int(np.count_nonzero(~live))
        a, j, A = a[live], j[live], A[live]
        if a.size == 0:
            return empty
        order = np.lexsort((j, -A, a))
        a, j = a[order], j[order]
        first = np.concatenate(([True], a[1:] != a[:-1]))
        a, j = a[first], j[first]
        self._acq_pending = (a, j)
        self.stats["acq_candidates"] += int(a.size)
        return (a, np.full(a.size, _ACQ, dtype=np.int8),
                np.full(a.size, int(WAKE_CONDITION_CLASS[_ACQ]), dtype=np.int64))

    def stamp_acquaintance(self, selected: np.ndarray, tick: int) -> None:
        """アービタが選んだ知人出現の呼 → その相手の欄に同一相手の不応期(60 分)を張る。"""
        a_c, j_c = self._acq_pending
        sel = np.asarray(selected, dtype=np.int64)
        if self._acq_until is None or sel.size == 0 or a_c.size == 0:
            return
        pos = np.searchsorted(a_c, sel)
        pos = np.minimum(pos, a_c.size - 1)
        hit = a_c[pos] == sel
        a, j = a_c[pos[hit]], j_c[pos[hit]]
        self._acq_until[a, j] = int(tick) + self._acq_pair_ticks
        self.stats["acq_woken"] += int(a.size)

    def lifetime_days(self, agents: Any, tick: int) -> dict[str, Any]:
        """生きている辺が相互作用なしで τ を下回るまでの残り日数(種別の初期辺/知人の辺)。"""
        r = agents.registry
        used = r.rel_partner != REL_EMPTY
        n = r.rel_n.astype(np.float64)
        L = np.maximum(0.0, (int(tick) - r.rel_first.astype(np.float64)) * self.minutes_per_tick)
        with np.errstate(divide="ignore", over="ignore"):
            A = np.log(n / (1.0 - self.d)) - self.d * np.log(L + 1.0)
            Lstar = np.exp((np.log(n / (1.0 - self.d)) - self.tau) / self.d) - 1.0
        live = used & (A >= self.tau)
        rem = (Lstar - L) / 1440.0
        out: dict[str, Any] = {}
        kind = r.rel_kind.astype(np.int64)
        for name, sel in (("initial", live & (kind != REL_KINDS["acquaintance"])),
                          ("acquaintance", live & (kind == REL_KINDS["acquaintance"]))):  # 2 通り
            x = rem[sel]
            out[name] = ({q: round(float(np.percentile(x, float(q[1:]))), 3)
                          for q in ("p0", "p10", "p50", "p90", "p100")} | {"n": int(x.size)}) if x.size else {"n": 0}
        return out

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
            # ---- 8b ----
            "lifetime_days": self.lifetime_days(agents, tick),
            "copresent": self._co_since is not None,
            "acquaintance_wake": self._acq_until is not None,
            "invite_weights": self._invite_salt is not None,
            "wall_seconds_nondeterministic": {k_: round(float(v), 3) for k_, v in sorted(self.wall.items())},
        }
