"""engine.relations_people — 人も記憶の一つ(第 6 期 6-5・腕 ``--memory-people memory``)の関係の読み口。

正: 決定 10-12 §4-6「人も記憶の一つとして扱う(MR5 を含む)」=人も同じ器・同じ式で扱う。関係の表(容量 50)と眠っている関係の
保管をやめる。思い浮かぶ=強さが τ を超える・見覚え=目の前にいる手がかりを足すと超える・どちらにも届かず十分下がったら忘れる
(消す)。50 人・150 人などの数は押し付けない(結果の数を Dunbar の層と照合)。最初の関係はデータから開始前の経験として入れる。
MR4: 親しさは数値で持たず、関係の種類・会った事実・印象の文を言葉で見せる。MR6: 好意の数値は持たない(符号は 0)。

形(**器=腕**・既定 off では今の関係の層 ``engine.relations.RelationLayer`` のまま)
- :class:`PeopleRelationLayer` は ``RelationLayer`` の子で、読み口(:meth:`activation`・:meth:`edges`・:meth:`acquaintances`・
  :meth:`partners_in_cell`・:meth:`_partner_rows`=会話の相手選び ``choose_talk_partners`` が使う)を**記憶の器の人の行**
  (``MemoryStore.people_rows``=種類 ``memory_m1.PERSON_KIND``・強さは M1 の式・境目は M1 の τ)から作る。**関係の表
  ``rel_*`` を読まない・書かない**(試験の AST と負の対照)。
- 書き手: 人の行に触れるのは記憶の書き手(``MemoryLayer._touch_people``=会話・手伝いの出来事・番ごと=MR6 の注意が向いた
  1 回)と注意の口(``MemoryLayer.note_attended``=口だけ)。この層の :meth:`on_episodes` は数えるだけ。
- 最初の関係: :meth:`seed_initial` が今の関係の層の機械的初期化の辺(W16 の世帯・W17 の共在=``initial_edges``)を人の行に
  入れる(4-1 段 4 の ``w21_relations_initial`` が本体に無い間のつなぎ=台帳 ``DOC-mr65-people-initial``)。辺の種類は人の行の
  対象の欄(関係の種類)に持つ。上限 15(Q111)は入れる側の ``initial_edges`` の引数のまま=器の側では切らない。
- 本段で無いもの: 同席(``--rel-copresent``=MR6 は「注意が向いたときを 1 回」で置き換える・目の向きと空間の段が先)・知人出現の
  起床(``--rel-acq-wake``・既定 on・空間の段の後)=要求は計器の数に出して作らない(``copresent_on``・``acq_wake_on`` は偽=系は
  呼ばない・呼べば止める)・連絡先の印(CT5=人の行の関係の種類から数えるだけ・印の配列は持たない)。

**未リサーチ(expedient)**: 人の行の関係の種類を対象の欄に持つ形・符号を 0 に固定(好意の数値は持たない=MR6)・強さ P の幅は
今の関係の層と同じ s=0.25(M1 の τ の上で)・関係の読み口の幅=器の行の幅(人の行だけを見る)。

逐次ループ宣言(P4): なし(体 × 器の行の幅の配列演算)。
"""

from __future__ import annotations

from collections import Counter
from typing import Any

import numpy as np

from shibuya.engine.relations import (
    REL_D,
    REL_K,
    REL_KIND_NAMES,
    REL_KINDS,
    REL_ROW_BYTES_ACTUAL,
    REL_ROW_BYTES_DECLARED,
    REL_S,
    InitialEdges,
    RelationEdges,
    RelationLayer,
)
from shibuya.engine.tools import contacts as _CT

__all__ = ["PeopleRelationLayer"]


class PeopleRelationLayer(RelationLayer):
    """人も記憶の一つの腕の関係の読み口(器の人の行・関係の表を読まない)。``store`` は ``MemoryStore``(上限なし・M1)。"""

    def __init__(self, n_agents: int, k: int = REL_K, *, store: Any, minutes_per_tick: float = 1.0,
                 d: float = REL_D, s: float = REL_S) -> None:
        if store is None or store.m1 is None or not store.uncapped:
            raise ValueError("PeopleRelationLayer は人も記憶の一つの腕の器(上限なし・M1)が前提")
        super().__init__(n_agents, k, minutes_per_tick=minutes_per_tick, d=d, tau=float(store.m1.tau), s=s)
        #: 記憶の器(参照=状態は器の側で数える)。
        self._ms = store

    # ------------------------------------------------------------------ 時刻
    def _now_ns(self, step: int) -> int:
        return int(step) * int(self._ms.ns_per_step)

    # ------------------------------------------------------------------ 初期化(最初の関係はデータから)
    def seed_initial(self, agents: Any, init: InitialEdges) -> None:
        """今の関係の層の機械的初期化の辺 → 器の人の行(開始前の経験・時刻は負の刻み → ns)。"""
        self.init_audit = dict(init.audit)
        u = np.asarray(init.u, dtype=np.int64)
        if u.size == 0:
            return
        ns = int(self._ms.ns_per_step)
        got = self._ms.seed_people(u, init.v, init.kind, init.n, np.asarray(init.first, dtype=np.int64) * ns,
                                   np.asarray(init.last, dtype=np.int64) * ns)
        self.stats["init_edges"] += int(got)
        for kd, c in Counter(np.asarray(init.kind, dtype=np.int64).tolist()).items():  # 種別の数ぶん(≤ 5)
            self.stats[f"init_edges:{REL_KIND_NAMES[int(kd)]}"] += int(c)

    # ------------------------------------------------------------------ 書き手(数えるだけ)
    def on_episodes(self, agents: Any, tick: int, a: np.ndarray, kind: np.ndarray, partner: np.ndarray,
                    result: np.ndarray) -> None:
        """人の行は記憶の書き手が触れる(``MemoryLayer._touch_people``)=ここは数えるだけ(関係の表に書かない)。"""
        self.stats["episodes_seen"] += int(np.asarray(a).size)

    # ------------------------------------------------------------------ 読み口(器の人の行)
    def _partner_rows(self, agents: Any, agent_ids: np.ndarray) -> np.ndarray:
        # 〔検収 L3〕相手だけ要る=強さを計算しない(A は直後の activation で 1 回)
        partner, _rel, _A, _Af, _row = self._ms.people_rows(agent_ids, 0, strength=False, familiar=False)
        return partner

    def activation(self, agents: Any, agent_ids: np.ndarray, tick: int) -> np.ndarray:
        """体の配列 → ``(体, 幅)`` の人の行の強さ A(M1 の式・人でない行は −inf)。"""
        return self._ms.people_rows(agent_ids, self._now_ns(tick), familiar=False)[2]

    def edges(self, agents: Any, agent_id: int, tick: int) -> RelationEdges:
        """1 体の思い浮かぶ人(A ≥ τ=M1 の τ・A の降順・同点は行の番号)。符号は 0(好意の数値は持たない=MR6)。"""
        i = int(agent_id)
        partner, rel, A, _Af, row = self._ms.people_rows(np.asarray([i]), self._now_ns(tick), familiar=False)
        partner, rel, A, row = partner[0], rel[0], A[0], row[0]
        live = np.flatnonzero(A >= self.tau)
        live = live[np.lexsort((live, -A[live]))]
        return RelationEdges(partner=partner[live], kind=rel[live], sign=np.zeros(live.size, dtype=np.int64),
                             A=A[live], P=self.strength(A[live]), row=row[live])

    def acquaintances(self, agents: Any, agent_id: int, tick: int) -> np.ndarray:
        """描画の「知人」=思い浮かぶ人(A ≥ τ・行の番号の順)。"""
        partner, _rel, A, _Af, _row = self._ms.people_rows(np.asarray([int(agent_id)]), self._now_ns(tick),
                                                           familiar=False)
        return partner[0][A[0] >= self.tau].astype(np.int64)

    def recognized(self, agents: Any, agent_id: int, ids: Any, tick: int) -> np.ndarray:
        """見覚え(MR4・MR5): 目の前の人 ``ids`` のうち、見覚えの強さに手がかりを足すと τ を超える人か(思い浮かぶ人を含む)。"""
        from shibuya.engine.memory_m1 import recognize_mask

        ids = np.atleast_1d(np.asarray(ids, dtype=np.int64))
        partner, _rel, A, A_fam, _row = self._ms.people_rows(np.asarray([int(agent_id)]), self._now_ns(tick))
        p, a_, af = partner[0], A[0], A_fam[0]
        hit = p[None, :] == ids[:, None]
        rec = recognize_mask(af, self.tau, np.ones(af.size, dtype=bool)) | (a_ >= self.tau)
        return (hit & rec[None, :]).any(axis=1)

    def partners_in_cell(self, agents: Any, agent_ids: np.ndarray, tick: int) -> np.ndarray:
        """体の配列 → ``(体, 幅)`` の「同じセルに居る思い浮かぶ人」(他は −1)。"""
        r = agents.registry
        a = np.asarray(agent_ids, dtype=np.int64)
        partner, _rel, A, _Af, _row = self._ms.people_rows(a, self._now_ns(tick), familiar=False)
        live = (partner >= 0) & (A >= self.tau)
        cell = np.asarray(r.cell, dtype=np.int64)
        pc = np.where(live, cell[np.where(live, partner, 0)], -2)
        same = live & (pc == cell[a][:, None]) & (cell[a][:, None] >= 0)
        return np.where(same, partner, -1)

    def aware_of(self, agents: Any, agent_id: int, ids: Any, tick: int) -> np.ndarray:
        """知人出現の起床が無い腕=いつも偽(今の層の ``--rel-acq-wake`` の無いランと同じ)。"""
        return np.zeros(np.atleast_1d(np.asarray(ids)).size, dtype=bool)

    # ------------------------------------------------------------------ 本段で無いもの(要求は数える・呼ぶと止める)
    def enable_copresent(self, **kw: Any) -> None:
        """同席の腕(``--rel-copresent``)は作らない(MR6=注意が向いたときを 1 回=``MemoryLayer.note_attended``・目の向きと
        空間の段が先)。要求は計器 ``counts.copresent_requested_unavailable`` に出す(``copresent_on`` は偽のまま)。"""
        self.stats["copresent_requested_unavailable"] += 1

    def enable_acquaintance_wake(self, **kw: Any) -> None:
        """知人出現の起床(``--rel-acq-wake``・既定 on)は作らない(空間の段の後)。要求は計器
        ``counts.acq_wake_requested_unavailable`` に出す(``acq_wake_on`` は偽のまま=系は起床を作らない)。"""
        self.stats["acq_wake_requested_unavailable"] += 1

    def copresent_step(self, agents: Any, tick: int, *, proximity: Any = None) -> None:
        raise RuntimeError("人も記憶の一つの腕に同席の書き手は無い")

    def acquaintance_candidates(self, agents: Any, tick: int, *args: Any, **kw: Any) -> Any:
        raise RuntimeError("人も記憶の一つの腕に知人出現の起床は無い")

    def stamp_acquaintance(self, selected: np.ndarray, tick: int) -> None:
        raise RuntimeError("人も記憶の一つの腕に知人出現の起床は無い")

    def _same_cell_hits(self, agents: Any, tick: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        raise RuntimeError("人も記憶の一つの腕は関係の表の集めを使わない")

    @staticmethod
    def _edges(agents: Any) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        raise RuntimeError("人も記憶の一つの腕は関係の表の集めを使わない")

    def _edge_view(self, agents: Any, tick: int, proximity: Any) -> tuple[np.ndarray, ...]:
        raise RuntimeError("人も記憶の一つの腕は関係の表の集めを使わない")

    def _acq_notice(self, *args: Any, **kw: Any) -> Any:
        raise RuntimeError("人も記憶の一つの腕に知人出現の起床は無い")

    def _acq_finish(self, *args: Any, **kw: Any) -> Any:
        raise RuntimeError("人も記憶の一つの腕に知人出現の起床は無い")

    def _write_round(self, *args: Any, **kw: Any) -> None:
        raise RuntimeError("人も記憶の一つの腕は関係の表に書かない(人の行は記憶の書き手が触れる)")

    def _reset_slots(self, *args: Any, **kw: Any) -> None:
        raise RuntimeError("人も記憶の一つの腕は関係の表の欄を持たない")

    # ------------------------------------------------------------------ 連絡先の印(CT5)=人の行の関係の種類から数えるだけ
    @property
    def contact_flags(self) -> np.ndarray:
        """印の配列は持たない(幅 0 の読み取り専用)。"""
        v = np.zeros((self.n, 0), dtype=_CT.FLAG_DTYPE)
        v.flags.writeable = False
        return v

    def contact_tally(self, agents: Any) -> dict[str, Any]:
        partner, rel, _A, _Af, _row = self._ms.people_rows(np.arange(self.n, dtype=np.int64), 0, strength=False,
                                                           familiar=False)
        flags = _CT.flags_from_kinds(rel, partner)
        return {**_CT.tally(flags, rel, partner), "means": list(_CT.MEANS)}

    def rebuild_contacts(self, agents: Any) -> None:
        """印の配列を持たない=何もしない(再開の腕は器の側で止める)。"""
        return None

    # ------------------------------------------------------------------ 監査(今の層と同じ鍵)
    def lifetime_days(self, agents: Any, tick: int) -> dict[str, Any]:
        """思い浮かぶ人が触れられないまま τ を下回るまでの残り日数(初期の人/知人)。M1 の式の B の傾きからの外挿は
        しない=この腕では空(``n`` だけ)=宣言。"""
        partner, rel, A, _Af, _row = self._ms.people_rows(np.arange(self.n, dtype=np.int64), self._now_ns(tick),
                                                          familiar=False)
        live = (partner >= 0) & (A >= self.tau)
        return {"initial": {"n": int(np.count_nonzero(live & (rel != REL_KINDS["acquaintance"])))},
                "acquaintance": {"n": int(np.count_nonzero(live & (rel == REL_KINDS["acquaintance"])))}}

    def summary(self, agents: Any, tick: int) -> dict[str, Any]:
        """manifest ``relations``(今の層と同じ鍵・値は器の人の行から)。"""
        partner, rel, A, _Af, _row = self._ms.people_rows(np.arange(self.n, dtype=np.int64), self._now_ns(tick),
                                                          familiar=False)
        used = partner >= 0
        live = used & (A >= self.tau)
        per = live.sum(axis=1)

        def q(x: np.ndarray) -> dict[str, float]:
            x = np.asarray(x, dtype=np.float64)
            if x.size == 0:
                return {}
            return {p: round(float(np.percentile(x, float(p[1:]))), 4)
                    for p in ("p0", "p10", "p50", "p90", "p99", "p100")} | {"mean": round(float(x.mean()), 4)}

        kinds = rel[live].astype(np.int64)
        deg = np.bincount(per, minlength=1)
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
            "signs": {"0": int(live.sum())} if int(live.sum()) else {},
            "A": q(A[live]),
            "P": q(self.strength(A[live]).astype(np.float64)),
            "n_per_edge": {},
            "dunbar_layers": {"agents_with_5_or_more": int(np.count_nonzero(per >= 5)),
                              "agents_with_15": int(np.count_nonzero(per >= 15))},
            "init": dict(self.init_audit),
            "lifetime_days": self.lifetime_days(agents, tick),
            "copresent": False,
            "acquaintance_wake": False,
            "invite_weights": self._invite_salt is not None,
            "wall_seconds_nondeterministic": {k_: round(float(v), 3) for k_, v in sorted(self.wall.items())},
        }
