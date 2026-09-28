"""engine.store_choice — **想起優先の候補合成**と**決め手の記録**(D-120 7c・N6 (a)・N7 (a)・N8 (a)・第298)。

正典: ``docs/design/v2-store-memory-implementation-agenda.md`` §3(段 7c の 1〜6)。上位=
``docs/design/v2-memory-wom-internet-draft.md`` §1-2 の 5・6・8・1-5 N6〜N8。M17 の潜在的な親しみ
(α/β・Q53)とネット(D-121)は含めない。

想起優先(N6 (a)・``--store-memory on`` かつ選び手 ``classical`` のときだけ・``engine.poi_target`` が呼ぶ)
    店を選ぶ場面(購入/食事/並ぶ・対象が**名指しでない**=カテゴリ語か「なし」。名指しは LLM の選択=
    そのまま)で、体の店の評価の行(≤ 32 行)から**想起できた店**を拾う:
    ``A ≥ τ``(記憶と共有の τ)∧ 向き ≥ 0(看板だけの店も入る=第296 Q76)∧ 意図に合う(食事=飲食店・購入/並ぶ=
    ``BUYABLE_CATS``・カテゴリ語ならその語の店)∧ 営業中(W7)∧ 購入/並ぶは在庫あり(2a/2c と同じ・飲食店は
    在庫を見ない)∧ **到達可能(N7)**。そのうち**願望水準**(``ClassicalChooser`` の段の規則: 食事でとても空腹は
    条件なし・それ以外は予算内=価格 ≤ 所持金)を満たすものがあれば、**精度に比例した分布**(``probs ∝ precision``)
    から 1 件を決定論で引く(``chooser.draw_index``)→ 現在セルの店ならその場で・セル外なら**名指しの意図**
    (段 2c・``IntentKind.POI_NAMED``=歩く)。満たすものが無ければ従来どおり(可視順の満足化+揺らぎ)。
    二段型(P_new で戻る/探す)は採らない。

到達可能性(N7 (a)・上限つきの制約=距離減衰ではない)
    ``cell_dist[現在セル, 店のセル] / 歩速[m/tick] ≤ min(次の予定までの tick, 意図の上限 INTENT_MAX_TICKS)``。
    歩速=エンジンの移動の物差し: 既定の node 幾何は **1 tick=1 ノード=W1 の辺長の平均**(実資産 ≒37.8 m/tick
    ≒2.3 km/h)・edge 幾何は体の希望速度 × tick 秒(Kladek 減速は掛けない=宣言)。次の予定=計画境界の表
    (``run.py`` の ``b_agent``/``b_tick``=``ActivityLayer``・``ClassicalPolicy`` と同じ表)。魅力度 × 距離^−β の
    形は持たない(禁止線)。

決め手(N8 (a)・SOFAI 形式・時間帯別)
    選んだ店ごとに 1 つ: ``named``(LLM の名指し)/ ``visible``(可視順の満足化)/ ``nearby``(2b の近傍探索)/
    ``habit``(習慣 p_h の候補を引いた)/ 想起優先=行の出どころのうち 1 件の精度が最大のもの(σ が最小=
    ``self`` 自分の記憶・``wom`` 伝聞・``signage`` 看板・``net`` ネット)。訪問(購入/食事の成立)の時に、その体の
    最後の決め手の店と同じなら決め手を引き継いで**初回率**(訪問のうち店の評価の行が無かった店・自分の訪問の
    ビットが無かった店)と**店頭の割合**(初回の訪問の決め手が ``visible``/``signage``)を数える(照合量=較正に
    使わない)。

逐次ループ宣言(P4): なし(1 回の想起優先は 1 体の ≤ 32 行の配列演算)。要約はランの終わりに 1 回。
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Final

import numpy as np

from shibuya.agents.state import STORE_MEMORY_EMPTY
from shibuya.engine.chooser import draw_index, hunger_stage_of
from shibuya.engine.store_memory import STORE_SOURCE_BIT, STORE_SOURCES

__all__ = [
    "CHOICE_REASONS",
    "STOREFRONT_REASONS",
    "StoreChoice",
    "walk_m_per_tick",
]

#: 決め手(SOFAI 形式の内訳)。
CHOICE_REASONS: Final[tuple[str, ...]] = (
    "named", "visible", "nearby", "habit", "self", "wom", "signage", "net",
)
#: 「店頭で決めた」とみなす決め手(照合: 初回の 22.2%=リクルート 2024「店構えや店先のメニューなど」)。
STOREFRONT_REASONS: Final[tuple[str, ...]] = ("visible", "signage")
_REASON_CODE: Final[dict[str, int]] = {r: i for i, r in enumerate(CHOICE_REASONS)}


def walk_m_per_tick(world: Any, n_agents: int, *, geometry: str = "node", geom: Any = None,
                    tick_seconds: int = 60) -> np.ndarray:
    """体ごとの歩速[m/tick](エンジンの移動の物差し)。node=W1 の辺長の平均・edge=希望速度 × tick 秒。"""
    if geometry == "edge" and geom is not None and getattr(geom, "v_desired", None) is not None:
        v = np.asarray(geom.v_desired, dtype=np.float64)[: int(n_agents)] * float(tick_seconds)
        return np.maximum(v, 1e-6)
    el = np.asarray(getattr(world.assets, "edge_len_m", np.zeros(0)), dtype=np.float64)
    m = float(el.mean()) if el.size else 1.0
    return np.full(int(n_agents), max(m, 1e-6), dtype=np.float64)


class StoreChoice:
    """想起優先の候補合成と決め手の記録(1 ランに 1 つ・``TargetResolver`` が持つ)。"""

    def __init__(self, memory: Any, world: Any, n_agents: int, *, seed: int | str,
                 boundary_agent: np.ndarray | None = None, boundary_tick: np.ndarray | None = None,
                 walk_m_per_tick: np.ndarray | None = None, intent_max_ticks: int = 60,
                 minutes_per_tick: float = 1.0, recall_first: bool = True) -> None:
        self.memory = memory                 # MemoryLayer(τ を共有・店の表 ``memory.store``)
        self.store = memory.store
        self.world = world
        self.n = int(n_agents)
        self.seed = seed
        self.minutes_per_tick = float(minutes_per_tick)
        self.ticks_per_hour = max(1, int(round(60.0 / self.minutes_per_tick)))
        self.intent_max_ticks = int(intent_max_ticks)
        self.recall_first = bool(recall_first)
        self.poi_cell = np.asarray(world.pois.cell, dtype=np.int64)
        self.price = np.asarray(world.pois.price, dtype=np.int64)
        self.walk = (np.asarray(walk_m_per_tick, dtype=np.float64) if walk_m_per_tick is not None
                     else np.full(self.n, 1.0))
        ba = np.asarray(boundary_agent if boundary_agent is not None else [], dtype=np.int64)
        bt = np.asarray(boundary_tick if boundary_tick is not None else [], dtype=np.int64)
        order = np.lexsort((bt, ba)) if ba.size else np.zeros(0, dtype=np.int64)
        self._b_tick = bt[order]
        counts = np.bincount(ba[order], minlength=self.n)[: self.n] if ba.size else np.zeros(self.n, np.int64)
        self._b_off = np.zeros(self.n + 1, dtype=np.int64)
        np.cumsum(counts, out=self._b_off[1:])
        # 出どころ → ビット・σ(1 件の精度が大きい順=σ が小さい順に並べた決め手の優先)
        sig = dict(self.store.sigma)
        self._src_order = sorted(STORE_SOURCES, key=lambda s: (float(sig[s]), STORE_SOURCES.index(s)))
        #: 体ごとの最後の決め手(訪問の引き継ぎ用・SoA の外=checkpoint に混ざらない)。
        self.choice_poi = np.full(self.n, -1, dtype=np.int64)
        self.choice_reason = np.full(self.n, -1, dtype=np.int64)
        self.stats: Counter = Counter()
        self.by_hour = np.zeros((24, len(CHOICE_REASONS)), dtype=np.int64)
        self.first_by_reason = np.zeros((2, len(CHOICE_REASONS) + 1), dtype=np.int64)  # (行なし/自分なし, 決め手+不明)
        self.visits_by_reason = np.zeros(len(CHOICE_REASONS) + 1, dtype=np.int64)
        self.store.visit_hook = self.on_visit

    # ------------------------------------------------------------------ 到達可能性(N7)
    def ticks_to_next_plan(self, aid: int, tick: int) -> int:
        lo, hi = int(self._b_off[aid]), int(self._b_off[aid + 1])
        if hi <= lo:
            return 1 << 30
        k = lo + int(np.searchsorted(self._b_tick[lo:hi], int(tick), side="right"))
        return int(self._b_tick[k]) - int(tick) if k < hi else 1 << 30

    def reachable(self, aid: int, tick: int, cell: int, pois: np.ndarray) -> np.ndarray:
        """``pois`` のうち次の予定までに歩いて届くもの(上限つきの制約・距離減衰ではない)。"""
        pois = np.asarray(pois, dtype=np.int64)
        if cell < 0:
            return np.zeros(pois.size, dtype=bool)
        pc = self.poi_cell[pois]
        cd = self.world.assets.cell_dist
        ok_c = (pc >= 0) & (pc < cd.shape[0])
        d = np.full(pois.size, np.inf)
        d[ok_c] = np.asarray(cd[cell, pc[ok_c]], dtype=np.float64)
        budget = min(self.ticks_to_next_plan(aid, tick), self.intent_max_ticks)
        return (d / float(self.walk[aid])) <= float(budget)

    # ------------------------------------------------------------------ 想起優先(N6)
    def recall(self, agents: Any, aid: int, tick: int, cell: int, fit: np.ndarray, open_now: np.ndarray,
               stock_ok: np.ndarray, eatery: np.ndarray, eat: bool) -> tuple[int, str]:
        """想起できた店から 1 件(``(POI, 決め手)``)。無ければ ``(-1, "")``(従来の経路へ)。"""
        self.stats["recall:attempts"] += 1
        r = agents.registry
        i = int(aid)
        used = np.flatnonzero(r.sm_poi[i] != STORE_MEMORY_EMPTY)
        if used.size == 0:
            self.stats["recall:no_rows"] += 1
            return -1, ""
        A = self.store.activation(agents, np.asarray([i]), tick)[0][used]
        v = self.store.valence_now(agents, np.asarray([i]), tick)[0][used]
        pois = r.sm_poi[i][used].astype(np.int64)
        prec = r.sm_precision[i][used].astype(np.float64)
        src = r.sm_source[i][used].astype(np.int64)
        inside = (pois >= 0) & (pois < fit.size)
        safe = np.where(inside, pois, 0)
        ok = inside & (A >= float(self.memory.tau)) & (np.sign(v) >= 0)
        self.stats["recall:rows_recallable"] += int(np.count_nonzero(inside & (A >= float(self.memory.tau))))
        ok &= fit[safe] & open_now[safe]
        if not eat:
            ok &= stock_ok[safe] | eatery[safe]
        self.stats["recall:rows_fit_open"] += int(np.count_nonzero(ok))
        if not bool(ok.any()):
            self.stats["recall:none_fit"] += 1
            return -1, ""
        reach = np.zeros(ok.size, dtype=bool)
        reach[ok] = self.reachable(i, tick, int(cell), pois[ok])
        self.stats["recall:rows_unreachable"] += int(np.count_nonzero(ok & ~reach))
        ok &= reach
        if not bool(ok.any()):
            self.stats["recall:none_reachable"] += 1
            return -1, ""
        # 願望水準(ClassicalChooser の段の規則): 食事でとても空腹=条件なし・それ以外は予算内
        money = int(r.money[i])
        if not (eat and hunger_stage_of(int(r.hunger[i])) >= 3):
            ok &= self.price[safe] <= money
        if not bool(ok.any()):
            self.stats["recall:none_aspiration"] += 1
            return -1, ""
        cand = np.flatnonzero(ok)
        p = prec[cand] / prec[cand].sum()
        j = int(cand[draw_index(p, self.seed, int(tick), i)])
        reason = next(s for s in self._src_order if int(src[j]) & STORE_SOURCE_BIT[s])
        self.stats["recall:chosen"] += 1
        self.stats[f"recall:candidates:{min(int(cand.size), 5)}"] += 1
        return int(pois[j]), reason

    # ------------------------------------------------------------------ 決め手(N8)
    def note(self, aid: int, poi: int, reason: str, tick: int) -> None:
        """選んだ店とその決め手(時間帯別に数え、訪問の引き継ぎ用に体ごとに 1 件だけ持つ)。"""
        code = _REASON_CODE[reason]
        self.choice_poi[int(aid)] = int(poi)
        self.choice_reason[int(aid)] = code
        hour = (int(tick) // self.ticks_per_hour) % 24
        self.by_hour[hour, code] += 1
        self.stats[f"choice:{reason}"] += 1

    def on_visit(self, a: np.ndarray, poi: np.ndarray, had_row: np.ndarray, had_self: np.ndarray) -> None:
        """訪問(購入/食事の成立)=決め手を引き継いで初回率・店頭の割合を数える(配列演算)。"""
        a = np.asarray(a, dtype=np.int64)
        poi = np.asarray(poi, dtype=np.int64)
        same = self.choice_poi[a] == poi
        code = np.where(same & (self.choice_reason[a] >= 0), self.choice_reason[a], len(CHOICE_REASONS))
        np.add.at(self.visits_by_reason, code, 1)
        np.add.at(self.first_by_reason[0], code[~np.asarray(had_row, dtype=bool)], 1)
        np.add.at(self.first_by_reason[1], code[~np.asarray(had_self, dtype=bool)], 1)

    def summary(self) -> dict[str, Any]:
        """manifest ``store_choice``: 決め手の内訳(時間帯別)・想起優先の計数・初回率・店頭の割合。"""
        names = list(CHOICE_REASONS) + ["unknown"]
        visits = int(self.visits_by_reason.sum())
        first_row = self.first_by_reason[0]
        first_self = self.first_by_reason[1]
        sf = [names.index(x) for x in STOREFRONT_REASONS]
        known = len(CHOICE_REASONS)

        def share(num: int, den: int) -> float:
            return round(num / den, 4) if den else 0.0

        return {
            "reasons": list(CHOICE_REASONS),
            "storefront_reasons": list(STOREFRONT_REASONS),
            "recall_first": bool(self.recall_first),
            "counts": {k: int(v) for k, v in sorted(self.stats.items())},
            "choices_by_reason": {r: int(self.by_hour[:, c].sum()) for r, c in _REASON_CODE.items()},
            "choices_by_hour": [
                {r: int(self.by_hour[h, c]) for r, c in _REASON_CODE.items()} for h in range(24)
            ],
            "visits": visits,
            "visits_by_reason": {names[c]: int(self.visits_by_reason[c]) for c in range(len(names))},
            "first_visit_no_row": int(first_row.sum()),
            "first_visit_no_row_share": share(int(first_row.sum()), visits),
            "first_visit_no_self": int(first_self.sum()),
            "first_visit_no_self_share": share(int(first_self.sum()), visits),
            "first_visit_no_self_by_reason": {names[c]: int(first_self[c]) for c in range(len(names))},
            "storefront_share_of_first_no_self": share(
                int(first_self[sf].sum()), int(first_self[:known].sum())),
            "storefront_share_of_first_no_row": share(
                int(first_row[sf].sum()), int(first_row[:known].sum())),
            "reference": {"first_visit_share": 0.225, "storefront_share_of_first": 0.222,
                          "note": "照合量(較正に使わない)"},
            "walk_m_per_tick_mean": round(float(np.mean(self.walk)) if self.walk.size else 0.0, 3),
            "intent_max_ticks": int(self.intent_max_ticks),
        }
