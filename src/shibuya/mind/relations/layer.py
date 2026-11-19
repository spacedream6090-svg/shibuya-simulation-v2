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
    〔第 1 期 1-7 CT5〕個人の連絡先の手段ごとの印 ``contact_flags``(体 × k の uint8=体あたり k B・``--relations on`` の
    ランだけ)。

〔第 1 期 1-7 CT5〕個人の連絡先の手段ごとの印(決定 10-12 §4-4 CT5 (c)・``engine.tools.contacts``)
    ``contact_flags``(体 × k・欄の位置は ``rel_*`` の列と同じ)。既存の ``rel_*`` の列と書き方は変えない。中身は
    ``_contact_flags`` に置き、``contact_flags`` は読み取り専用の view を返す property(口の外から書けない・付け替えられない=
    検収 L1。``_contact_flags`` の付け替えと消去も ``__setattr__``/``__delattr__`` で止める)。書くのは
    :meth:`RelationLayer._write_contacts` の 1 つだけ(呼ぶのは初めの辺=:meth:`seed_initial`・欄の相手が替わった=
    :meth:`_reset_slots`・再開の作り直し=:meth:`rebuild_contacts`=試験の AST)。家族(世帯の辺)と職場(職場の辺)は
    初めから印あり。C0 では誰も読まない(C1 で使う)=印は辺の種別の写像そのもの(状態台帳の行 ``CT5``=軸 1 diag・
    軸 2 derivable・中身は hash_skip)。
"""

from __future__ import annotations

import math
from collections import Counter
from typing import Any, Final
import numpy as np
from shibuya.foundation.vocab.agent_codes import REL_EMPTY, WAKE_CONDITION_CLASS, ResultCode, WakeCondition
from shibuya.foundation.hashing import relation_invite_key_array
# 〔割る段 6 の S6-G1〕別名 R を割り先ごとに分けた(R_ACT_CODES=foundation.vocab.act_codes・R_MIND=mind.ops の名。割る前は全部 resolve)
from shibuya.engine import resolve as R_ACT_CODES
from shibuya.engine import resolve as R_MIND
from shibuya.foundation.vocab import contact_flags as _CT
from shibuya.foundation.time_consts import MINUTES_PER_DAY
from shibuya.foundation.vocab.relations import (
    InitialEdges,
    REL_D,
    REL_K,
    REL_KINDS,
    REL_KIND_NAMES,
    REL_ROW_BYTES_ACTUAL,
    REL_ROW_BYTES_DECLARED,
    REL_S,
    REL_TAU,
    RelationEdges,
    _activation,
)

__all__ = [
    "REL_INVITE_LAYERS", "REL_COPRESENT_MINUTES", "REL_COPRESENT_METERS", "REL_ACQ_PAIR_REFRACTORY_MIN",
    "RelationLayer",
]


#: 招待の重み(Dunbar 2020: 内側 5 人に 40%・次の 10 人に 20%・残り 40%=辺の無い同席者=8b が読む)。
REL_INVITE_LAYERS: Final[tuple[tuple[int, float], ...]] = ((5, 0.40), (10, 0.20))
#: 同席(COPRESENT・第299 Q91・R-36 §6-1 の初期案=expedient): 同セル・距離 2 m 内・連続 5 分で 1 本・
#: 相手ごと 1 日 1 本まで。**表に居る相手(辺)だけ**を強める(知らない同席者は辺を作らない=宣言)。
REL_COPRESENT_MINUTES: Final[int] = 5
REL_COPRESENT_METERS: Final[float] = 2.0
#: 知人出現の起床(R7 (a))の同一相手の不応期[分](知覚契約 §6「同一相手 60 分」)。
REL_ACQ_PAIR_REFRACTORY_MIN: Final[int] = 60
_ACQ: Final[int] = int(WakeCondition.ACQUAINTANCE)
_TALK: Final[int] = 7
#: 招待の層の外(k=50 の腕の 16 番目以降の辺)は「残り」の層に入れる(宣言)。
_REST_SHARE: Final[float] = 1.0 - sum(s for _, s in REL_INVITE_LAYERS)
_HELP: Final[int] = 9
_SIGN_LABEL: Final[dict[int, str]] = {1: "+1", 0: "0", -1: "-1"}
#: 〔1-7 CT5・検収 L1〕付け替えと消去を止める属性(連絡先の印の中身)。
_CONTACT_GUARDED: Final[frozenset[str]] = frozenset({"_contact_flags"})
_SIGN_OF_RESULT: Final[dict[int, int]] = {
    int(ResultCode.OK): 1, int(ResultCode.REFUSED): -1, int(ResultCode.PARTNER_BUSY): 0,
    int(ResultCode.PARTNER_GONE): 0,
}


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
        # ---- 第 2 期 2-2(腕 --proximity distance): 体 × k の辺の見え方(同じ刻みの同席と知人出現で共有=検収 M2) ----
        self._ev: tuple[np.ndarray, ...] | None = None
        self._ev_step = -1
        self._co_minutes = float(REL_COPRESENT_MINUTES)
        self._co_meters = float(REL_COPRESENT_METERS)
        # ---- 8b(R7 (a) 知人出現): 同一相手の不応期(体 × k)・前 tick のセル・この tick の候補 ----
        self._acq_until: np.ndarray | None = None
        self._acq_pair_ticks = 0
        self._prev_cell: np.ndarray | None = None
        self._acq_pending: tuple[np.ndarray, np.ndarray] = (np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int64))
        #: 壁時計(決定論でない・manifest の ``wall_seconds_nondeterministic``)。
        self.wall: Counter = Counter()
        #: 〔第 1 期 1-7 CT5〕個人の連絡先の手段ごとの印の中身(体 × k・``engine.tools.contacts.MEANS`` のビット)。書くのは
        #: ``_write_contacts`` だけ・読むのは ``contact_flags``(読み取り専用の view)。C0 では誰も読まない(状態台帳の行 CT5)。
        self._contact_flags = np.zeros((self.n, self.k), dtype=_CT.FLAG_DTYPE)

    # ------------------------------------------------------------------ 1-7 CT5(検収 L1): 実行時の守り
    def __setattr__(self, name: str, value: Any) -> None:
        if name in _CONTACT_GUARDED and name in self.__dict__:
            raise AttributeError(f"RelationLayer の {name} は付け替えられない(連絡先の印を書く口は _write_contacts だけ)")
        object.__setattr__(self, name, value)

    def __delattr__(self, name: str) -> None:
        if name in _CONTACT_GUARDED:
            raise AttributeError(f"RelationLayer の {name} は消せない(連絡先の印を書く口は _write_contacts だけ)")
        object.__delattr__(self, name)

    @property
    def contact_flags(self) -> np.ndarray:
        """連絡先の印(体 × k の読み取り専用の view=口の外から書けない。書く口は ``_write_contacts``)。"""
        v = self._contact_flags.view()
        v.flags.writeable = False
        return v

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
        R_MIND.write_relations(agents, u[ok], slot[ok], init.v[ok], init.kind[ok], np.zeros(int(ok.sum())),
                          init.first[ok], init.last[ok], init.n[ok])
        # 1-7 CT5: 家族(世帯の辺)と職場(職場の辺)は初めから連絡先の印あり(ほかの種別は 0)
        self._write_contacts(u[ok], slot[ok], _CT.flags_from_kinds(init.kind[ok]))
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
        R_MIND.write_relations(agents, a, slot, partner, kind, sg, first, np.full(a.size, int(tick)), n)
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
        # 1-7 CT5: 新しい相手の連絡先は知らない(交換は本人の行動=C1)
        self._write_contacts(a, slot, 0)

    # ------------------------------------------------------------------ 1-7 CT5: 連絡先の印(書く口は 1 つ)
    def _write_contacts(self, a: np.ndarray, slot: np.ndarray, flags: Any) -> None:
        """連絡先の印の欄 ``(a, slot)`` に ``flags`` を書く。**印を書く口はこれ 1 つ**(呼ぶのは ``seed_initial``・
        ``_reset_slots``・``rebuild_contacts`` だけ=試験の AST)。"""
        self._contact_flags[np.asarray(a, dtype=np.int64), np.asarray(slot, dtype=np.int64)] = flags

    def contact_tally(self, agents: Any) -> dict[str, Any]:
        """manifest の ``tools.contact_flags``(印を持つ辺の数・手段ごと・種別ごと=``engine.tools.contacts.tally``)。読むだけ。"""
        r = agents.registry
        return {**_CT.tally(self._contact_flags, r.rel_kind, r.rel_partner), "means": list(_CT.MEANS)}

    def rebuild_contacts(self, agents: Any) -> None:
        """再開: 戻した辺の種別から連絡先の印を作り直す(C0 では印は種別の写像そのもの=通しのランと同じ値)。"""
        r = agents.registry
        kind = np.asarray(r.rel_kind)
        rows, cols = np.indices(kind.shape)
        self._write_contacts(rows.reshape(-1), cols.reshape(-1),
                             _CT.flags_from_kinds(kind, np.asarray(r.rel_partner)).reshape(-1))

    # ------------------------------------------------------------------ 読み口
    def _partner_rows(self, agents: Any, agent_ids: np.ndarray) -> np.ndarray:
        """〔第 6 期 6-5〕体の配列 → ``(体, 幅)`` の辺の相手(空は −1)。既定=``rel_partner`` の写し(幅=k)。人も記憶の一つの腕
        (``engine.relations_people``)は器の人の行(幅=器の行の幅)。"""
        return agents.registry.rel_partner[np.asarray(agent_ids, dtype=np.int64)].astype(np.int64)

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
                             record_origin: bool = True, proximity: Any = None) -> tuple[np.ndarray, np.ndarray]:
        """会話の相手(R5・R12・D-31 (b))と起点(招待/偶然/知人出現)。配列演算(体 × k)。

        - 名指し(``named_ok``)の行は相手を変えない(起点だけ付ける)。
        - 名指しの無い行: 同セルの**生きている辺**の相手を、**2 m 内の知人が居ればその中から**(偶然=第一候補・
          残りの層は付けない)、居なければ同セルの辺+残り(``fallback``=従来の同席者のハッシュ順・辺の相手でない
          とき)から、:func:`_layer_weights` の重みで seed つきに引く。同セルに辺が無ければ ``fallback`` のまま
          (従来どおり=D-31 (a))。
        - 起点: 起床が知人出現 → ``acquaintance``・相手が 2 m 内の知人 → ``chance``・それ以外 → ``invite``。

        〔第 2 期 2-2 段 11a〕``proximity``(腕 ``--proximity distance`` の ``engine.proximity.ProximityRule``)を渡すと、
        「同セルの辺」と「2 m 内の知人」をどちらも「届く辺の相手」(同じ層・距離 ≤ d、または同じ B5 の単位)に替える
        (届く知人が居ればその中から=偶然)。``None``(既定)は今のまま。

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
        p = self._partner_rows(agents, a)  # 〔6-5〕読み口(既定は rel_partner の写し=人も記憶の腕は器の人の行)
        width = int(p.shape[1])
        A = self.activation(agents, a, tick)
        rank = _rank_live(A, self.tau)
        live = rank >= 0
        pp = np.where(live, p, 0)
        if proximity is not None and proximity.is_distance:  # 第 2 期 2-2: 届く辺の相手(同セルと 2 m を 1 つに)
            in_cell = live & proximity.reach(agents, a[:, None], pp)
            near = in_cell
        else:
            cell = np.asarray(r.cell, dtype=np.int64)
            ca = cell[a]
            in_cell = live & (cell[pp] == ca[:, None]) & (ca[:, None] >= 0)
            xy = np.asarray(r.xy, dtype=np.float64)
            d2 = ((xy[pp] - xy[a][:, None, :]) ** 2).sum(axis=-1)
            near = in_cell & (d2 <= float(R_ACT_CODES.TALK_OPEN_METERS) ** 2)
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
            idx = np.minimum(idx, width)
            rows = np.flatnonzero(pick)
            got_edge = idx < width
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

    @staticmethod
    def _edges(agents: Any) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """空でない辺の欄 ``(体, 欄, 相手)``(体の昇順 → 欄の昇順)。第 2 期 2-2(腕 distance)の材料。"""
        p = np.asarray(agents.registry.rel_partner)
        a, j = np.nonzero(p != REL_EMPTY)
        return a.astype(np.int64), j.astype(np.int64), p[a, j].astype(np.int64)

    def _edge_view(self, agents: Any, tick: int, proximity: Any) -> tuple[np.ndarray, ...]:
        """〔第 2 期 2-2 段 11a・検収 M2〕いまの辺の見え方 ``(体, 欄, 相手, 気づく範囲, 距離, 届く)``(舞台の中の辺だけ)。

        体 × k の辺を刻みに 1 回だけなめる(``ProximityRule.edge_view``)。同じ刻みの 2 回目(同席の後の知人出現)は控えを
        返す(今の道の ``_same_cell_hits`` と同じ形=同じ刻みの中で位置が動かない系の中でだけ呼ぶ)。
        逐次ループ宣言: なし(体 × k の 1 回の集めと、打ち切りの中の辺だけの距離の配列演算・毎刻み)。
        """
        if self._ev_step == int(tick) and self._ev is not None:
            return self._ev
        a, j, v = self._edges(agents)
        cell = np.asarray(agents.registry.cell)
        on = (cell[a] >= 0) & (cell[v] >= 0)            # 舞台の外の体の辺は範囲の外で届かない(先に落とす=答えは同じ)
        a, j, v = a[on], j[on], v[on]
        inr, dist, reach = proximity.edge_view(agents, a, v)
        self._ev = (a, j, v, inr, dist, reach)
        self._ev_step = int(tick)
        return self._ev

    def aware_of(self, agents: Any, agent_id: int, ids: Any, tick: int) -> np.ndarray:
        """〔第 2 期 2-2・検収 L1〕体 ``agent_id`` が相手 ``ids`` に気づいている(気づいた印か起床の後の不応期が切れていない)か。

        読むだけ(描画の B5 の近接行の知人が読む=描画ごとに引き直さない)。辺に居ない相手・知人出現の起床が無いランは偽。
        逐次ループ宣言: なし(相手の数 × k の配列演算)。
        """
        ids = np.atleast_1d(np.asarray(ids, dtype=np.int64))
        if self._acq_until is None or ids.size == 0:
            return np.zeros(ids.size, dtype=bool)
        i = int(agent_id)
        p = np.asarray(agents.registry.rel_partner)[i].astype(np.int64)
        on = (p[None, :] == ids[:, None]) & (p[None, :] != REL_EMPTY)
        return (on & (self._acq_until[i].astype(np.int64)[None, :] > int(tick))).any(axis=1)

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

    def copresent_step(self, agents: Any, tick: int, *, proximity: Any = None) -> None:
        """同じセル・2 m 内に辺の相手が居る欄を数え、連続 5 分で 1 本(相手ごと 1 日 1 本)を辺に書く。

        書く=``n``+1・``last``=tick・符号は +0(同席のみ=0・R-36 §2-5 C)。表に居ない同席者は書かない。
        〔第 2 期 2-2 段 11a〕``proximity``(腕 ``--proximity distance``)を渡すと「同じセル・2 m 内」を「届く」(同じ層・
        距離 ≤ d、または同じ B5 の単位)に替える(辺の見え方は知人出現と共有=:meth:`_edge_view`)。``None``(既定)は今のまま。
        逐次ループ宣言: なし(同セルの辺の集め 1 回+その当たりだけの配列演算・毎 tick)。
        """
        if self._co_since is None:
            return
        r = agents.registry
        if proximity is not None and proximity.is_distance:
            ea, ej, _ev, _inr, _d, reach = self._edge_view(agents, tick, proximity)
            a, j = ea[reach], ej[reach]
        else:
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
        day = int(int(tick) * self.minutes_per_tick // MINUTES_PER_DAY)
        run = (int(tick) - self._co_since[flat].astype(np.int64) + 1) * self.minutes_per_tick
        fire = (run >= self._co_minutes) & (self._co_day[flat] != day)
        if not bool(fire.any()):
            return
        a, j, f = a[fire], j[fire], flat[fire]
        self._co_day[f] = day
        n = np.minimum(r.rel_n[a, j].astype(np.int64) + 1, 65_535)
        R_MIND.write_relations(agents, a, j, r.rel_partner[a, j].astype(np.int64), r.rel_kind[a, j].astype(np.int64),
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
                                eligible: np.ndarray | None = None, *,
                                proximity: Any = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """知人(A ≥ τ)が同セルに**現れた** tick(前 tick は同セルでなかった)の起床候補(1 体 1 件・最強の相手)。

        ``eligible``=候補にしてよい体(起きていて舞台に居る=アービタが落とさない体)。前 tick のセルは全体で持つ。
        同一相手の不応期 60 分で落とす。1 tick 目は「前 tick」が無いので出さない(宣言)。
        〔第 2 期 2-2 段 11a〕``proximity``(腕 ``--proximity distance``)を渡すと「同セルに現れた」を「新しく気づいた」に
        替える(:meth:`_acq_notice`)。``None``(既定)は今のまま。
        逐次ループ宣言: なし(同セルの辺の集め 1 回+その当たりだけの配列演算・毎 tick)。
        """
        empty = (np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int8), np.zeros(0, dtype=np.int64))
        self._acq_pending = (np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int64))
        if self._acq_until is None:
            return empty
        r = agents.registry
        prev = self._prev_cell
        self._prev_cell = np.array(r.cell, copy=True)
        if proximity is not None and proximity.is_distance:
            a_n, j_n = self._acq_notice(agents, tick, proximity, first=prev is None, eligible=eligible)
            return self._acq_finish(agents, tick, a_n, j_n)
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
        return self._acq_finish(agents, tick, a, j)

    def _acq_notice(self, agents: Any, tick: int, proximity: Any, *, first: bool,
                    eligible: np.ndarray | None) -> tuple[np.ndarray, np.ndarray]:
        """〔第 2 期 2-2 段 11a〕知人に**新しく気づいた**辺 ``(体, 欄)``(腕 ``--proximity distance``・B4)。

        気づく範囲(舞台の中・同じ層・距離 ≤ 100 m)の辺のうち、まだ気づいていない欄だけ p(d)(R-62 の 2 点の
        ロジスティック)で引く(10c の counter の流れ=用途名 ``proximity.notice``・鍵=時刻の鍵・体・相手)。辺の見え方は
        同席と共有する(:meth:`_edge_view`)。気づいた欄は「次の刻みまで気づいている」印を同一相手の不応期の
        配列 ``_acq_until`` に置く(``max(今の値, T+2)``)=範囲の中に居る間は毎刻み印が延びる=引き直さない。範囲の外に
        出た欄は印が切れ、次に範囲に入ったら引き直す。不応期(起床の後 60 分)の欄も「気づいている」と同じに扱う
        (起床の後 60 分は同じ相手で起きない=今と同じ)。1 刻み目は印だけ置いて出さない(今と同じ宣言)。
        逐次ループ宣言: 抽選は引く組の数ぶん(``ProximityRule.notice_u``=範囲の中で、まだ気づいていない辺の数)。ほかは
        配列演算(毎刻み)。
        """
        from shibuya.world.model.proximity import notice_p

        z = np.zeros(0, dtype=np.int64)
        ea, ej, ev, inr, dist, _reach = self._edge_view(agents, tick, proximity)
        a, j, v, dist = ea[inr], ej[inr], ev[inr], dist[inr]
        if a.size == 0:
            return z, z
        T = int(tick)
        until = self._acq_until[a, j].astype(np.int64)
        aware = until > T
        hit = np.zeros(a.size, dtype=bool)
        fresh = np.flatnonzero(~aware)
        if fresh.size:
            hit[fresh] = proximity.notice_u(T, a[fresh], v[fresh]) < notice_p(dist[fresh])
        self.stats["acq_notice_draws"] += int(fresh.size)
        self.stats["acq_noticed"] += int(np.count_nonzero(hit))
        seen = aware | hit
        self._acq_until[a[seen], j[seen]] = np.maximum(until[seen], T + 2).astype(self._acq_until.dtype)
        if first:
            return z, z
        if eligible is not None:
            hit &= np.asarray(eligible, dtype=bool)[a]
        a, j = a[hit], j[hit]
        self.stats["acq_appear"] += int(a.size)
        return a, j

    def _acq_finish(self, agents: Any, tick: int, a: np.ndarray,
                    j: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """知人出現の候補の仕上げ(生きている辺だけ・1 体 1 件=最強の相手・控え)。今の道と第 2 期 2-2 の腕が共有する。"""
        empty = (np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int8), np.zeros(0, dtype=np.int64))
        r = agents.registry
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
        rem = (Lstar - L) / MINUTES_PER_DAY
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
