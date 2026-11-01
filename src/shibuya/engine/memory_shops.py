"""engine.memory_shops — 人も記憶の一つの腕の店の評価の行(第 6 期 6-5・検収 M4・腕 ``--memory-people memory``)。

正: 決定 10-12 §4-6「人も記憶の一つとして扱う」(店 32 件・出来事 128 件の固定の上限もなくす)・回答 10-12 の 6-2 の M1
(人と店と出来事を同じ器に入れ上限と保管をなくす)・元の発注の項 4(店 32 件の固定の上限を外す道=腕)。

形(**器=腕**・既定 off では今の店の評価の記憶 ``engine.store_memory.StoreMemory`` が体の表 ``agents.registry.sm_*``(体あたり
32 行=``STORE_MEMORY_N``)に書くまま)
- :class:`ShopTable`: 記憶の器の子の持ち主 ``mem_layer.memory_store.shops``(状態台帳の腕の行 ``M0S``=腕 memory-people・
  軸 1 behavior・軸 2 required)。列は体の表の ``sm_*`` と同じ 7 本・同じ型(``(体, 幅)``)。幅は ``STORE_MEMORY_N``(32)から
  始め、満杯の体が出たら全員の幅を倍にする(上限=``engine.memory_store.row_caps()["shop"]``=256・expedient)。
- :class:`UncappedStoreMemory`: ``StoreMemory`` の子。行の口(``columns``・``_evict_slots``・``_put``)だけを差し替える=書き手
  (自分の訪問・看板・伝聞)・σ・減衰・score・読み口(7c の想起・選び手・B5)は親と同じ式。満杯の体の新しい店は、幅が上限より
  小さければ幅を倍にして空いた行へ、上限なら**思い浮かぶ強さ A(手がかり無し=親の ``activation``)の一番低い行**を上書きする
  (同点は最後の時刻 ``last`` の古い順・次に行の番号=決定的。親の既定の追い出しは score=A+0.5×min(4, 精度) の最小)。
- 体の表の ``sm_*`` はこの腕では書かない(空のまま=確保は今の組み立てのまま)。

**未リサーチ(expedient)**: 店の上限 256・最初の幅 32・上限での消し方(A の最小)。つなぎの台帳 ``DOC-mr65-m1-shop-uncapped``。

逐次ループ宣言(P4): なし(幅を倍にする回=log2(256/32)=3 回まで・配列演算)。
"""

from __future__ import annotations

from typing import Any, Final

import numpy as np

from shibuya.agents.state import STORE_MEMORY_EMPTY
from shibuya.engine.memory_store import SHOP_PATH, _check_permit
from shibuya.engine.store_memory import STORE_MEMORY_ROW_BYTES_ACTUAL, StoreColumns, StoreMemory

__all__ = ["ShopTable", "UncappedStoreMemory", "SHOP_COLS"]

#: 列(名・型・空の値)=体の表の ``sm_*`` と同じ型・同じ空の値(``agents.state`` の初期化: poi −1・first −1・last −1)。
SHOP_COLS: Final[tuple[tuple[str, Any, int], ...]] = (
    ("_poi", np.int32, int(STORE_MEMORY_EMPTY)),
    ("_valence", np.float32, 0),
    ("_precision", np.float32, 0),
    ("_first", np.int32, -1),
    ("_last", np.int32, -1),
    ("_n", np.uint16, 0),
    ("_source", np.uint8, 0),
)


class ShopTable:
    """店の評価の行の表(記憶の器の子の持ち主 ``mem_layer.memory_store.shops``・状態台帳の腕の行 ``M0S``)。

    書く口は :meth:`put` と :meth:`grow`(``UncappedStoreMemory`` の行の口の中からだけ)と :meth:`note_evicted`(計数)。
    欄の付け替えは ``__setattr__`` が落とす。読み口 :meth:`columns` は読み取り専用の view。
    """

    LEDGER_ARM: str = "memory-people"
    __slots__ = ("n", "cap", "_poi", "_valence", "_precision", "_first", "_last", "_n", "_source", "_shop_stats")

    def __init__(self, n_agents: int, width: int, *, cap: int) -> None:
        if int(n_agents) < 0 or int(width) < 1 or int(cap) < int(width):
            raise ValueError("n_agents ≥ 0・width ≥ 1・cap ≥ width")
        self.n = int(n_agents)
        self.cap = int(cap)
        for name, t, fill in SHOP_COLS:
            object.__setattr__(self, name, np.full((self.n, int(width)), fill, dtype=t))
        #: 計数(行 M0X): ``grown``=幅を倍にした回・``evicted_by_a``=上限で A の一番低い行を上書きした数・``written``=書いた件数。
        self._shop_stats: dict[str, int] = {"grown": 0, "evicted_by_a": 0, "written": 0}

    def __setattr__(self, name: str, value: Any) -> None:
        if not hasattr(self, name):
            object.__setattr__(self, name, value)
            return
        raise AttributeError(f"店の行の表の欄 {name} は付け替えられない(書く口は put・grow)")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"店の行の表の欄 {name} は消せない")

    @property
    def width(self) -> int:
        """いまの幅(体あたりの行の数)。"""
        return int(self._poi.shape[1])

    def columns(self) -> StoreColumns:
        """列の読み取り専用の view(``StoreMemory`` の読み口が読む)。"""
        out = []
        for name, _t, _f in SHOP_COLS:
            v = getattr(self, name).view()
            v.flags.writeable = False
            out.append(v)
        return StoreColumns(*out)

    # ------------------------------------------------------------------ 書く口(UncappedStoreMemory の中から)
    def put(self, a: np.ndarray, slot: np.ndarray, poi: np.ndarray, valence: np.ndarray, precision: np.ndarray,
            first: np.ndarray, last: np.ndarray, n: np.ndarray, source: np.ndarray) -> None:
        """行を書く(体の表の書き手 ``resolve.write_store_memory`` と同じ型の丸め)。"""
        _check_permit(SHOP_PATH, "店の評価の行")
        a = np.asarray(a, dtype=np.int64)
        s = np.asarray(slot, dtype=np.int64)
        self._poi[a, s] = np.asarray(poi, dtype=np.int64).astype(np.int32)
        self._valence[a, s] = np.asarray(valence, dtype=np.float64).astype(np.float32)
        self._precision[a, s] = np.asarray(precision, dtype=np.float64).astype(np.float32)
        self._first[a, s] = np.asarray(first, dtype=np.int64).astype(np.int32)
        self._last[a, s] = np.asarray(last, dtype=np.int64).astype(np.int32)
        self._n[a, s] = np.asarray(n, dtype=np.int64).astype(np.uint16)
        self._source[a, s] = np.asarray(source, dtype=np.int64).astype(np.uint8)
        self._shop_stats["written"] += int(a.size)

    def grow(self) -> int:
        """全員の幅を倍にする(上限 :attr:`cap` まで)→ 前の幅。上限なら ``RuntimeError``。"""
        _check_permit(SHOP_PATH, "店の評価の行の幅")
        w = self.width
        new = min(2 * w, self.cap)
        if new <= w:
            raise RuntimeError(f"店の行の幅は上限 {self.cap}(広げられない)")
        for name, t, fill in SHOP_COLS:
            out = np.full((self.n, new), fill, dtype=t)
            out[:, :w] = getattr(self, name)
            object.__setattr__(self, name, out)
        self._shop_stats["grown"] += 1
        return w

    def note_evicted(self, k: int) -> None:
        """上限で上書きした数を足す(計数)。"""
        self._shop_stats["evicted_by_a"] += int(k)

    # ------------------------------------------------------------------ 計器
    def summary(self) -> dict[str, Any]:
        """manifest ``memory_summary.memory_store.mr65.shops``(観測)。"""
        used = self._poi != STORE_MEMORY_EMPTY
        per = used.sum(axis=1) if self.n else np.zeros(0, dtype=np.int64)
        return {"width": self.width, "cap": self.cap, "rows": int(used.sum()),
                "agents_with_rows": int(np.count_nonzero(per > 0)),
                "per_agent_max": int(per.max()) if per.size else 0,
                "row_bytes": int(STORE_MEMORY_ROW_BYTES_ACTUAL), "counts": dict(self._shop_stats)}


class UncappedStoreMemory(StoreMemory):
    """人も記憶の一つの腕の店の評価の記憶(``StoreMemory`` の子=行の口だけ差し替える・行は :class:`ShopTable`)。"""

    def __init__(self, n_agents: int, *, table: ShopTable, **kw: Any) -> None:
        if not isinstance(table, ShopTable):
            raise TypeError("table は ShopTable")
        super().__init__(n_agents, table.width, **kw)
        #: 器の店の行の表(参照=状態は器の子の持ち主 shops の側で数える)。
        self._tab = table

    def columns(self, agents: Any) -> StoreColumns:
        """店の評価の行の列(器の店の行の表=体の表の ``sm_*`` は読まない)。"""
        return self._tab.columns()

    def _evict_slots(self, agents: Any, a: np.ndarray, tick: int) -> np.ndarray:
        """満杯の体の新しい店の行: 幅が上限より小さければ全員の幅を倍にして空いた最初の行・上限なら A の一番低い行(同点は最後の
        時刻の古い順・次に行の番号)。"""
        tab = self._tab
        if tab.width < tab.cap:
            w = tab.grow()
            self.stats["rows_grown"] += 1
            return np.full(a.size, w, dtype=np.int64)
        A = self.activation(agents, a, tick)
        c1 = A == A.min(axis=1)[:, None]
        last = tab.columns().last[a].astype(np.int64)
        t = np.where(c1, last, np.iinfo(np.int64).max)
        c2 = c1 & (t == t.min(axis=1)[:, None])
        slot = np.argmax(c2, axis=1).astype(np.int64)
        tab.note_evicted(a.size)
        self.stats["evictions_by_a"] += int(a.size)
        return slot

    def _put(self, agents: Any, a: np.ndarray, slot: np.ndarray, poi: np.ndarray, v: np.ndarray, p: np.ndarray,
             first: np.ndarray, last: np.ndarray, n: np.ndarray, src: np.ndarray) -> None:
        self._tab.put(a, slot, poi, v, p, first, last, n, src)
