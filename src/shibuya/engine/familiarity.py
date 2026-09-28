"""engine.familiarity — **親しみの表**(4 段目・記憶の先行部品=M13 訪問カウンタ+M17 露出カウンタ・第290)。

正典: ``docs/design/v2-familiarity-counters-implementation-agenda.md`` §1〜§3。記憶アジェンダ M13
(訪問カウンタの前倒し=D-119 の習慣 p_h の入力)・M17(潜在的な親しみ=体×もの の基底活性 A)。

本段は**カウンタと A の保持と計測だけ**(誰も読まない)。店選びへの接続(M17 の形 α/β)は記憶
アジェンダ M17 のユーザーの答えの後・LLM への文章化(B5 の記憶行)は記憶 第 1 段 M4 で。

表(``AgentState(familiarity_columns=True)`` のランだけ確保・``--familiarity on``)
    体ごとに K 行(:data:`FAMILIARITY_K`=64・宣言・感度 32/128)。1 行 = ``fam_thing`` int32・
    ``fam_first`` int32・``fam_last`` int32・``fam_visits`` uint16・``fam_exposures`` uint16=16 B。
    ``fam_thing`` の符号化: POI 索引(≥0)/ 場所=**``−(cell+2)``**(:func:`place_thing`・アジェンダ §1-1 の
    ``−(cell+1)`` はセル 0 が空行の印 −1 と重なるので 1 ずらした=宣言・問い)/ 人=``1<<30 | id``
    (本段では書かない)/ 空行 −1。

A の読み口(ACT-R の**最適化学習の近似**・宣言)::

    A = ln( n / (1 − d) ) − d · ln(L + 1)

    n = visits + exposures(接触の種類の重みは同じ=宣言・M17 の感度腕は後)
    L = (tick − first_tick) × 分/tick(寿命=最初の接触からの分)
    d = 0.5(既決・認知設計 §4)

  厳密式(認知設計 §4)``A = ln Σ_j (Δt_j + 1)^(−d)`` は全接触の時刻が要る(体×もの×接触の履歴=
  バイトが接触数に比例)。近似は n と L だけで済む(16 B/行)。等間隔の接触で厳密式に近く、最近に
  偏った接触では低め・古い接触に偏れば高めに出る(差の例は記録の README §4)。

書き手 3 つ(``after_tick``・tick の Phase C の後・on のときだけ)
    1. **訪問**: 購入/食事の成立した行(``resolve._complete_buy/_complete_eat`` の成功行・並ぶは委譲先で
       数える)の POI に visits+1(``ResolveOutcome.visit_agents/visit_pois``)。
    2. **看板の露出**(親決定 (f)): 2 つの経路を合わせて数える(同じ tick の同じ (体, POI) は 1 回)。
       (i) **描画による露出**=呼ばれた体の描画で看板の注視ゲート(p_see)を通り B2 に看板行が載った
       POI(``Renderer.signage_exposures`` の控え)。(ii) **入った回による露出**=セルに入った回 ×
       そのセルで B2 に載る看板の POI(``Renderer.signage_poi_by_cell``=描画と同じ 1 件)× p_see の
       決定論ベルヌーイ(``attention.gate_stage1``=描画と同じ流れ ``core.rng.stream(seed,
       "perception.attention.p_see", tick, agent_id, poi_id)``・既定 1.0 は全部)。LLM を呼ばれなかった
       体が看板の前を通った接触を拾う。描画は変えない。**エピソードには入れない**(二本立て・D-95 修正 1)。
    3. **場所**: 体のセルが前の tick と違って ≥0 なら、そのセルに exposures+1(**入った回**だけ・
       tick ごとではない=宣言)。ラン開始時の居場所は tick 0 の入場として数える。
    人(B4b の同席)と道は**本段では書かない**。

統合と追い出し
    同じもの は 1 行に統合(first は保つ・last を更新)。新しいもので表が満杯なら **A が最小の行**を
    落とす(同点は行番号の小さい方・件数 ``evictions``)。

逐次ループ宣言(P4)
    1. :meth:`FamiliarityLayer.after_tick`: 体あたりの接触の**種類数ぶん**(≤ 4 回=訪問・描画の看板・場所・入った回の看板)の配列演算。体数・
       接触数に比例する Python ループは無い(例外: p_see < 1 のときだけ、看板のあるセルに入った体の
       数ぶんの抽選=描画と同じカウンタ (tick, agent_id, poi_id)。既定 p_see=1.0 は抽選しない)。
    2. :meth:`FamiliarityLayer.top_k`: 1 体の K 行(読み口・本段では計測だけが呼ぶ)。

expedient(宣言)
    ``FAMILIARITY_K=64``(感度 32/128・1 日では追い出しがほぼ効かない=親決定 (c))・接触の重み
    (訪問=露出=親決定 (a)・A はほぼ露出で決まる)・場所は入った回(親決定 (b))・場所の符号化
    ``−(cell+2)``(親決定 (e))・看板の露出=描画による露出+入った回 × そのセルの看板 × p_see
    (親決定 (f))・A の近似式(一様に散った接触の仮定・最近に偏った接触で過小=親決定 (d))・
    同点の追い出しは行番号・カウンタの上限 65,535(uint16 で飽和)。
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Final, Sequence

import numpy as np

from shibuya.agents.state import FAMILIARITY_EMPTY
from shibuya.engine import resolve as R
from shibuya.perception.attention import gate_stage1

__all__ = [
    "FAMILIARITY_K",
    "FAMILIARITY_K_ARMS",
    "FAMILIARITY_D",
    "FAMILIARITY_MODES",
    "PERSON_BIT",
    "ACTIVATION_ABSENT",
    "COUNT_MAX",
    "place_thing",
    "person_thing",
    "thing_kind",
    "activation_approx",
    "activation_exact",
    "FamiliarityLayer",
]

#: 体あたりの行数(記憶アジェンダ M17 の親推奨・宣言・感度腕 32/128)。
FAMILIARITY_K: Final[int] = 64
FAMILIARITY_K_ARMS: Final[tuple[int, ...]] = (32, 64, 128)
#: 減衰 d(既決・認知設計 §4)。
FAMILIARITY_D: Final[float] = 0.5
#: 切替口(``--familiarity``)。既定 off=表を確保しない=既定 checkpoint 不変。
FAMILIARITY_MODES: Final[tuple[str, ...]] = ("off", "on")
#: 人の ``thing_id`` の印(本段では書かない)。
PERSON_BIT: Final[int] = 1 << 30
#: 表に無いものの A(−inf 相当の有限の定数=JSON と比較で扱える)。
ACTIVATION_ABSENT: Final[float] = -1.0e9
#: カウンタの上限(uint16 で飽和)。
COUNT_MAX: Final[int] = 65_535

_KIND_VISIT: Final[int] = 0
_KIND_SIGNAGE: Final[int] = 1
_KIND_PLACE: Final[int] = 2
_KIND_SIGNAGE_ENTRY: Final[int] = 3


def place_thing(cell) -> np.ndarray:
    """セル → 場所の ``thing_id``(``−(cell+2)``=空行 −1 と衝突しない・cell ≥ 0)。

    アジェンダ §1-1 は ``−(cell+1)`` と書いたが、cell 0 が空行の印 −1 と重なるので 1 ずらした(宣言)。
    """
    return -(np.asarray(cell, dtype=np.int64) + 2)


def person_thing(agent_id) -> np.ndarray:
    """体 → 人の ``thing_id``(``1<<30 | id``・本段では書かない)。"""
    return np.asarray(agent_id, dtype=np.int64) | PERSON_BIT


def thing_kind(thing) -> np.ndarray:
    """``thing_id`` → 種類(``"empty"`` / ``"poi"`` / ``"place"`` / ``"person"``)の文字列配列。"""
    t = np.asarray(thing, dtype=np.int64)
    out = np.full(t.shape, "poi", dtype=object)
    out[t == FAMILIARITY_EMPTY] = "empty"
    out[t <= -2] = "place"
    out[(t >= 0) & ((t & PERSON_BIT) != 0)] = "person"
    return out


def activation_approx(n, lifetime_min, d: float = FAMILIARITY_D) -> np.ndarray:
    """最適化学習の近似 ``A = ln(n/(1−d)) − d·ln(L+1)``(n ≤ 0 は :data:`ACTIVATION_ABSENT`)。"""
    n_ = np.asarray(n, dtype=np.float64)
    L = np.maximum(np.asarray(lifetime_min, dtype=np.float64), 0.0)
    out = np.full(np.broadcast(n_, L).shape, ACTIVATION_ABSENT, dtype=np.float64)
    ok = n_ > 0
    out[ok] = np.log(n_[ok] / (1.0 - d)) - d * np.log(np.broadcast_to(L, out.shape)[ok] + 1.0)
    return out


def activation_exact(ages_min: Sequence[float], d: float = FAMILIARITY_D) -> float:
    """厳密式 ``ln Σ_j (Δt_j + 1)^(−d)``(Δt_j=各接触からの経過分・比較と記録のためだけ)。"""
    a = np.asarray(ages_min, dtype=np.float64)
    if a.size == 0:
        return ACTIVATION_ABSENT
    return float(np.log(np.sum((np.maximum(a, 0.0) + 1.0) ** (-d))))


class FamiliarityLayer:
    """親しみの表の値を決める層(書き手は ``resolve.write_familiarity``)。

    Args:
        n_agents: 体数。
        k: 体あたりの行数(``AgentState.familiarity_k`` と同じ)。
        minutes_per_tick: 1 tick の分(寿命 L の換算)。
        d: 減衰(既決 0.5)。
    """

    def __init__(self, n_agents: int, k: int = FAMILIARITY_K, *, minutes_per_tick: float = 1.0,
                 d: float = FAMILIARITY_D, signage_poi_by_cell: np.ndarray | None = None,
                 p_see: float = 1.0, seed: int | str = 0) -> None:
        self.n = int(n_agents)
        self.k = int(k)
        self.minutes_per_tick = float(minutes_per_tick)
        self.d = float(d)
        #: 前の tick のセル(場所の「入った回」の判定)。−1=まだ見ていない/域外。
        self.prev_cell = np.full(self.n, -1, dtype=np.int64)
        #: 親決定 (f): セル → そのセルで B2 に載る看板の POI(−1=なし)。``None``=入った回の露出なし。
        self.signage_poi_by_cell = (
            None if signage_poi_by_cell is None
            else np.asarray(signage_poi_by_cell, dtype=np.int64)
        )
        self.p_see = float(p_see)
        self.seed = seed
        self.stats: Counter = Counter()

    # ------------------------------------------------------------------ 読み口
    def _activation_rows(self, agents: Any, ids: np.ndarray, tick: int) -> np.ndarray:
        r = agents.registry
        n = r.fam_visits[ids].astype(np.int64) + r.fam_exposures[ids].astype(np.int64)
        L = (int(tick) - r.fam_first[ids].astype(np.int64)) * self.minutes_per_tick
        a = activation_approx(n, L, self.d)
        a[r.fam_thing[ids] == FAMILIARITY_EMPTY] = ACTIVATION_ABSENT
        return a

    def activation(self, agents: Any, agent_ids, thing_ids, tick: int) -> np.ndarray:
        """体×もの → A(float32・表に無ければ :data:`ACTIVATION_ABSENT`)。**本段では誰も読まない**。"""
        a = np.asarray(agent_ids, dtype=np.int64)
        t = np.asarray(thing_ids, dtype=np.int64)
        out = np.full(a.size, ACTIVATION_ABSENT, dtype=np.float32)
        if a.size == 0:
            return out
        rows = agents.registry.fam_thing[a].astype(np.int64)
        hit = rows == t[:, None]
        found = hit.any(axis=1)
        if bool(found.any()):
            slot = np.argmax(hit, axis=1)
            acts = self._activation_rows(agents, a, tick)
            out[found] = acts[np.arange(a.size), slot][found].astype(np.float32)
        return out

    def top_k(self, agents: Any, agent_id: int, tick: int, k: int = 3) -> list[dict[str, Any]]:
        """1 体の A の上位 k 行(もの・種類・A・訪問・露出)。**本段では計測だけが呼ぶ**。"""
        i = np.asarray([int(agent_id)], dtype=np.int64)
        acts = self._activation_rows(agents, i, tick)[0]
        r = agents.registry
        order = [j for j in np.argsort(-acts, kind="stable").tolist()
                 if int(r.fam_thing[i[0], j]) != FAMILIARITY_EMPTY][: int(k)]
        return [
            {
                "thing": int(r.fam_thing[i[0], j]),
                "kind": str(thing_kind(r.fam_thing[i[0], j])),
                "A": float(acts[j]),
                "visits": int(r.fam_visits[i[0], j]),
                "exposures": int(r.fam_exposures[i[0], j]),
            }
            for j in order
        ]

    # ------------------------------------------------------------------ 書き手
    def after_tick(self, agents: Any, tick: int, visits: tuple[Sequence[np.ndarray],
                   Sequence[np.ndarray]] | None = None,
                   signage: Sequence[tuple[int, int]] | None = None) -> None:
        """この tick の接触(訪問・看板の露出・セルに入った)を表へ書く。Phase C の後に 1 回。"""
        t = int(tick)
        parts_a: list[np.ndarray] = []
        parts_t: list[np.ndarray] = []
        parts_k: list[np.ndarray] = []
        if visits is not None and len(visits[0]):
            va = np.concatenate([np.asarray(x, dtype=np.int64) for x in visits[0]])
            vp = np.concatenate([np.asarray(x, dtype=np.int64) for x in visits[1]])
            parts_a.append(va)
            parts_t.append(vp)
            parts_k.append(np.full(va.size, _KIND_VISIT, dtype=np.int64))
            self.stats["visits"] += int(va.size)
        seen_pairs: set[tuple[int, int]] = set()
        if signage:
            sa = np.fromiter((int(x[0]) for x in signage), dtype=np.int64, count=len(signage))
            sp = np.fromiter((int(x[1]) for x in signage), dtype=np.int64, count=len(signage))
            parts_a.append(sa)
            parts_t.append(sp)
            parts_k.append(np.full(sa.size, _KIND_SIGNAGE, dtype=np.int64))
            self.stats["exposures_signage_render"] += int(sa.size)
            seen_pairs = set(zip(sa.tolist(), sp.tolist()))
        cell = np.asarray(agents.registry.cell, dtype=np.int64)
        entered = np.flatnonzero((cell >= 0) & (cell != self.prev_cell))
        self.prev_cell = cell.copy()
        if entered.size:
            parts_a.append(entered)
            parts_t.append(place_thing(cell[entered]))
            parts_k.append(np.full(entered.size, _KIND_PLACE, dtype=np.int64))
            self.stats["exposures_place"] += int(entered.size)
            ea, ep = self._signage_on_entry(t, entered, cell[entered], seen_pairs)
            if ea.size:
                parts_a.append(ea)
                parts_t.append(ep)
                parts_k.append(np.full(ea.size, _KIND_SIGNAGE_ENTRY, dtype=np.int64))
                self.stats["exposures_signage_entry"] += int(ea.size)
        if not parts_a:
            return
        a = np.concatenate(parts_a)
        th = np.concatenate(parts_t)
        kd = np.concatenate(parts_k)
        # 体ごとに 1 件ずつの「回」に分ける(同じ体の接触は同じ tick で高々種類数ぶん)
        order = np.lexsort((kd, a))
        a, th, kd = a[order], th[order], kd[order]
        starts = np.flatnonzero(np.concatenate(([True], a[1:] != a[:-1])))
        rank = np.arange(a.size) - np.repeat(starts, np.diff(np.append(starts, a.size)))
        # 逐次ループ宣言1: 体あたりの接触の件数の最大ぶん(≤ 4)
        for rnd in range(int(rank.max()) + 1):
            sel = rank == rnd
            self._touch(agents, t, a[sel], th[sel], kd[sel] == _KIND_VISIT)

    def _signage_on_entry(
        self, t: int, agents_in: np.ndarray, cells: np.ndarray, seen_pairs: set[tuple[int, int]]
    ) -> tuple[np.ndarray, np.ndarray]:
        """親決定 (f): セルに入った体 × そのセルの看板 × p_see(描画と同じ流れ)→ (体, POI)。

        同じ tick に描画で同じ (体, POI) の露出があれば数えない(二重に数えない)。
        逐次ループ宣言: p_see < 1 のときだけ、看板のあるセルに入った体の数ぶん(1 件 1 抽選・描画と
        同じカウンタ (tick, agent_id, poi_id))。既定 p_see=1.0 は抽選しない(全部通る)。
        """
        empty = (np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int64))
        sp_tab = self.signage_poi_by_cell
        if sp_tab is None or agents_in.size == 0 or self.p_see <= 0.0:
            return empty
        ok_cell = (cells >= 0) & (cells < sp_tab.size)
        poi = np.full(agents_in.size, -1, dtype=np.int64)
        poi[ok_cell] = sp_tab[cells[ok_cell]]
        sel = np.flatnonzero(poi >= 0)
        if sel.size == 0:
            return empty
        a, p = agents_in[sel], poi[sel]
        if self.p_see < 1.0:
            keep = np.fromiter(
                (bool(gate_stage1(1, self.p_see, seed=self.seed,
                                  domain_counters=(int(t), int(x), int(y)))[0])
                 for x, y in zip(a.tolist(), p.tolist())),
                dtype=bool, count=a.size,
            )
            a, p = a[keep], p[keep]
        if seen_pairs and a.size:
            dup = np.fromiter(((int(x), int(y)) in seen_pairs for x, y in zip(a.tolist(), p.tolist())),
                              dtype=bool, count=a.size)
            self.stats["exposures_signage_entry_dedup"] += int(np.count_nonzero(dup))
            a, p = a[~dup], p[~dup]
        return a, p

    def _touch(self, agents: Any, t: int, a: np.ndarray, th: np.ndarray, is_visit: np.ndarray) -> None:
        """1 体 1 件の接触を統合/新規/追い出しで 1 行に書く(配列演算)。"""
        r = agents.registry
        rows = r.fam_thing[a].astype(np.int64)
        hit = rows == th[:, None]
        found = hit.any(axis=1)
        slot = np.where(found, np.argmax(hit, axis=1), -1)
        empty = rows == FAMILIARITY_EMPTY
        new = ~found
        has_empty = empty.any(axis=1)
        use_empty = new & has_empty
        slot = np.where(use_empty, np.argmax(empty, axis=1), slot)
        evict = new & ~has_empty
        if bool(evict.any()):
            acts = self._activation_rows(agents, a[evict], t)
            slot[evict] = np.argmin(acts, axis=1)  # 同点は行番号の小さい方
            self.stats["evictions"] += int(np.count_nonzero(evict))
        old_v = r.fam_visits[a, slot].astype(np.int64)
        old_e = r.fam_exposures[a, slot].astype(np.int64)
        old_f = r.fam_first[a, slot].astype(np.int64)
        v = np.where(found, old_v, 0) + is_visit.astype(np.int64)
        e = np.where(found, old_e, 0) + (~is_visit).astype(np.int64)
        f = np.where(found, old_f, t)
        R.write_familiarity(
            agents, a, slot, th, f, np.full(a.size, t, dtype=np.int64),
            np.minimum(v, COUNT_MAX), np.minimum(e, COUNT_MAX),
        )
        self.stats["merged"] += int(np.count_nonzero(found))
        self.stats["new_rows"] += int(np.count_nonzero(new))

    # ------------------------------------------------------------------ 監査
    def summary(self, agents: Any, tick: int) -> dict[str, Any]:
        """manifest ``familiarity``: 件数・K の使用率・訪問/露出/A の分布の要約・上位 3 件の種類。"""
        r = agents.registry
        used = (r.fam_thing != FAMILIARITY_EMPTY)
        rows_per = used.sum(axis=1)
        vis = r.fam_visits.astype(np.int64)
        exp = r.fam_exposures.astype(np.int64)
        acts = self._activation_rows(agents, np.arange(self.n), tick)
        a_used = acts[used]

        def q(x: np.ndarray) -> dict[str, float]:
            if x.size == 0:
                return {}
            return {p: round(float(np.percentile(x, float(p[1:]))), 4)
                    for p in ("p0", "p10", "p50", "p90", "p100")} | {"mean": round(float(x.mean()), 4)}

        only_v = used & (vis > 0) & (exp == 0)
        only_e = used & (vis == 0) & (exp > 0)
        both = used & (vis > 0) & (exp > 0)
        # 上位 3 件の種類(A の降順・空行を除く)
        top_idx = np.argsort(-acts, axis=1, kind="stable")[:, :3]
        top_things = np.take_along_axis(r.fam_thing.astype(np.int64), top_idx, axis=1)
        top_used = np.take_along_axis(used, top_idx, axis=1)
        kinds = Counter(thing_kind(top_things[top_used]).tolist())
        return {
            "k": int(self.k),
            "d": float(self.d),
            "counts": {k: int(v) for k, v in sorted(self.stats.items())},
            "rows_used_per_agent": q(rows_per.astype(np.float64)),
            "full_agents": int(np.count_nonzero(rows_per == self.k)),
            "visits_per_agent": q(vis.sum(axis=1).astype(np.float64)),
            "exposures_per_agent": q(exp.sum(axis=1).astype(np.float64)),
            "rows_by_kind": dict(Counter(thing_kind(r.fam_thing[used]).tolist())),
            "rows_visit_only": int(np.count_nonzero(only_v)),
            "rows_exposure_only": int(np.count_nonzero(only_e)),
            "rows_both": int(np.count_nonzero(both)),
            "A": q(a_used),
            "A_visit_only": q(acts[only_v]),
            "A_exposure_only": q(acts[only_e]),
            "A_both": q(acts[both]),
            "top3_kinds": dict(kinds),
        }
