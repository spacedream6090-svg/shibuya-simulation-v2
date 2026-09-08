"""engine.change_detect — 起床条件 (i)(ii) の検出器(予算行 **P6**)。

正典
- 知覚契約書 §6 起床条件: 「(i) 所属セルの **B4 ハッシュ変化**(密度段階の跨ぎ・騒音段階・
  構造物・顕著行為の到達) (ii) **B5 変化**(内受容閾値・知人出現・近接上位kの入替・被注視・
  傍受ヒット)」。**push 禁止・pull-on-wake**——本モジュールは「起床候補」を作るだけで、
  誰を実際に呼ぶかは ``engine.arbiter`` が決める。
- 実装計画書 §3: 「変化検出: セル B2/B4 のバイト列を **xxhash で 453 回**(宣言済みの小ループ)、
  個体 B5 は**配列比較**」。
- 知覚契約書 §6 不応期表「(ii)内受容閾値 45 分・**閾値ヒステリシスで置換を試す**」
  → 本モジュールは段の上げ下げに 1 段ぶんのヒステリシス帯を入れる。
- 予算宣言表 **P6**「≤2 ms/tick@40万体・139セル(ベクトル化・**逐次ループなし**)」。
  ``tests/engine/test_change_detect_p6.py`` が 40万体×453セルで実測して報告する
  (セル数の食い違い=139/453/520 は ``world.assets`` の docstring に記録)。
- 知覚契約書 §2「B2/B4 のバイト列ハッシュ=prefixキャッシュキー=変化検出器=dormant再送抑止」
  (三役・追加コストなし)。本モジュールが作る ``b4_hash`` がその1本。

**書き込みはしない**: 検出器は世界にも個体にも書かない(運用設計書 §2.2 Phase C=
``engine.resolve`` が唯一の書き手)。新しい ``b4_hash`` と内受容段は結果に載せて返し、
``resolve.apply_detection`` が書き込む。

逐次ループ宣言(P4)
1. ``b4_block_hashes``: **変化したセル数**ぶんの xxh64 ループ(上限=セル数 453/520。
   実装計画書が明示的に許した小ループ)。
2. ``ChangeDetector.detect``: 内受容 **3 変数**ぶんのループ(個体数には比例しない)。
3. ``_cell_wake_numba``: **個体数ぶんの numba nogil ループ1本**(実装計画書 §4
   「計算は numba nogil/Warp」)。NumPy 版(``np.take``+``flatnonzero``)は int32 添字の
   内部変換で 1.43 ms/tick@40万体かかり P6 を単独で食う。numba 版は 0.25 ms。
   numba が無い環境では NumPy 版へ自動で落ちる(結果は**バイト一致**・テストで検査)。

expedient(本モジュール分)
- B4 に載せる欄は C2 では **密度段階・騒音段階・営業中POI数** の 3 つだけ(構造物・顕著行為は
  C3/C4)。欄が増えるとハッシュが変わる=**B4 の版**は C3 のレンダラで凍結する。
- 内受容の段の刻み ``INTERO_UP_EDGES``(4/7/9)とヒステリシス幅 1。契約書は「閾値」としか
  言わず値を与えていない。
- (ii) のうち **知人出現・近接入替・被注視・傍受** は C2 では検出しない(関係辺 M5・
  近接上位k・注視は C3 の知覚レンダラに依存)。内受容だけを第1陣として実装した。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import numpy as np

from shibuya.agents.state import WAKE_CONDITION_CLASS, AgentState, WakeCondition
from shibuya.core.hashing import xxh64
from shibuya.world.state import World

__all__ = [
    "INTERO_UP_EDGES",
    "INTERO_HYSTERESIS",
    "INTERO_VARS",
    "B5Crossing",
    "DetectResult",
    "b4_block_raw",
    "b4_block_hashes",
    "ChangeDetector",
]

#: 内受容 3 変数の段の上げ側閾値(0-10 スケール・expedient)。
INTERO_UP_EDGES: Final[tuple[int, ...]] = (4, 7, 9)
#: ヒステリシス幅(下げ側の閾値 = 上げ側 − この値・expedient)。
INTERO_HYSTERESIS: Final[int] = 1
#: 内受容 3 変数の (値フィールド名, 段フィールド名)。
INTERO_VARS: Final[tuple[tuple[str, str], ...]] = (
    ("hunger", "hunger_stage"),
    ("fatigue", "fatigue_stage"),
    ("thermal", "thermal_stage"),
)

_B4_COLS: Final[int] = 3  # 密度段階・騒音段階・営業中POI数
_B4_ROW_BYTES: Final[int] = _B4_COLS * 4  # int32 × 3


def _cell_wake_numpy(cell: np.ndarray, cell_mask: np.ndarray, out: np.ndarray) -> int:
    """変化セルに居る個体の索引を ``out`` に詰め、件数を返す(NumPy 版・参照実装)。"""
    hit = np.take(cell_mask, cell, mode="clip") & (cell >= 0)
    idx = np.flatnonzero(hit)
    out[: idx.size] = idx
    return int(idx.size)


def _make_cell_wake():
    """numba があれば nogil カーネル、無ければ NumPy 版を返す。"""
    try:  # pragma: no cover - 環境依存
        from numba import njit
    except Exception:  # pragma: no cover - numba 無し環境
        return _cell_wake_numpy, False

    @njit(cache=True, nogil=True, boundscheck=False)
    def _kernel(cell, cell_mask, out):  # pragma: no cover - numba がコンパイルする
        k = 0
        for i in range(cell.shape[0]):
            c = cell[i]
            if c >= 0 and cell_mask[c]:
                out[k] = i
                k += 1
        return k

    return _kernel, True


_CELL_WAKE, CELL_WAKE_USES_NUMBA = _make_cell_wake()


def b4_block_raw(world: World, tick: int) -> np.ndarray:
    """セル動的ブロック B4 の生欄 ``(n_cells, 3)`` int32(密度段・騒音段・営業中POI数)。"""
    raw = np.empty((world.n_cells, _B4_COLS), dtype=np.int32)
    raw[:, 0] = world.density_stage()
    raw[:, 1] = world.cells.noise_stage
    raw[:, 2] = world.open_count_per_cell(tick)
    return raw


def b4_block_hashes(raw: np.ndarray, rows: np.ndarray | None = None) -> np.ndarray:
    """B4 生欄の行ごとの xxh64。

    Args:
        raw: ``(n_cells, 3)`` int32(C 連続)。
        rows: 計算する行の索引(None なら全行)。

    Returns:
        ``rows`` と同じ長さの uint64 配列。

    Note:
        逐次ループ宣言1: **行数ぶんの xxh64 ループ**(上限=セル数)。実装計画書 §3 が
        「xxhash で 453 回(宣言済みの小ループ)」と明示的に許した形。
    """
    flat = memoryview(np.ascontiguousarray(raw).reshape(-1).view(np.uint8))
    idx = np.arange(raw.shape[0]) if rows is None else np.asarray(rows, dtype=np.int64)
    if idx.size == 0:
        return np.empty(0, dtype=np.uint64)
    return np.fromiter(
        (xxh64(flat[int(i) * _B4_ROW_BYTES : (int(i) + 1) * _B4_ROW_BYTES]) for i in idx),
        dtype=np.uint64,
        count=int(idx.size),
    )


@dataclass(frozen=True)
class B5Crossing:
    """1 変数ぶんの閾値跨ぎ(``resolve`` が段を書き戻すための最小情報)。"""

    var: int  # 0=hunger / 1=fatigue / 2=thermal
    stage_field: str
    agent_id: np.ndarray  # int64・昇順
    new_stage: np.ndarray  # uint8


@dataclass(frozen=True)
class DetectResult:
    """1 tick 分の検出結果(**世界には書かない**)。"""

    tick: int
    #: 変化したセルの索引(昇順)。
    changed_cells: np.ndarray
    #: 変化したセルの新しい B4 ハッシュ(``changed_cells`` と同じ並び)。
    changed_b4_hash: np.ndarray
    #: 起床条件 (i) の対象個体(昇順)。
    cell_wake_agents: np.ndarray
    #: 起床条件 (ii) 内受容の跨ぎ(変数ごと)。
    crossings: tuple[B5Crossing, ...]

    @property
    def b5_wake_agents(self) -> np.ndarray:
        """内受容で起きる個体(3 変数の和集合・昇順)。"""
        parts = [c.agent_id for c in self.crossings if c.agent_id.size]
        if not parts:
            return np.empty(0, dtype=np.int64)
        return np.unique(np.concatenate(parts))

    def candidates(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """起床候補 ``(agent_id, condition, class_rank)``。

        並びは **条件番号の昇順 → 個体 id の昇順**(挿入順に依存しない=T3 の前提)。
        同一個体が複数条件で出ることがある(合流はアービタの仕事=§6 運用規定②)。
        """
        blocks: list[tuple[np.ndarray, WakeCondition]] = []
        b5 = self.b5_wake_agents
        if b5.size:
            blocks.append((b5, WakeCondition.INTEROCEPTION))
        if self.cell_wake_agents.size:
            blocks.append((self.cell_wake_agents, WakeCondition.CELL_BLOCK))
        if not blocks:
            e = np.empty(0, dtype=np.int64)
            return e, np.empty(0, dtype=np.int8), np.empty(0, dtype=np.int64)
        agent = np.concatenate([b[0] for b in blocks])
        cond = np.concatenate(
            [np.full(b[0].size, int(b[1]), dtype=np.int8) for b in blocks]
        )
        cls = np.concatenate(
            [
                np.full(b[0].size, int(WAKE_CONDITION_CLASS[int(b[1])]), dtype=np.int64)
                for b in blocks
            ]
        )
        return agent, cond, cls


class ChangeDetector:
    """B4 ハッシュと B5 閾値の変化検出器(scratch を持ち回して確保を避ける)。

    Example:
        >>> from shibuya.world.state import World
        >>> from shibuya.agents.state import AgentState
        >>> w = World.synthetic(n_cells=9, seed=0); a = AgentState(4)
        >>> det = ChangeDetector(a.n, w.n_cells)
        >>> res = det.detect(w, a, tick=0)
        >>> res.tick
        0
    """

    def __init__(self, n_agents: int, n_cells: int) -> None:
        self.n_agents = int(n_agents)
        self.n_cells = int(n_cells)
        self._prev_raw: np.ndarray | None = None
        # scratch(1 tick ごとの確保を避ける=Windows のページフォルトが P6 を食う)
        self._b1 = np.empty(self.n_agents, dtype=bool)
        self._b2 = np.empty(self.n_agents, dtype=bool)
        self._b3 = np.empty(self.n_agents, dtype=bool)
        self._up = [np.empty(self.n_agents, dtype=bool) for _ in INTERO_VARS]
        self._dn = [np.empty(self.n_agents, dtype=bool) for _ in INTERO_VARS]
        self._hit = [np.empty(self.n_agents, dtype=bool) for _ in INTERO_VARS]
        self._any = np.empty(self.n_agents, dtype=bool)
        self._cell_mask = np.zeros(self.n_cells, dtype=np.bool_)
        self._wake_buf = np.empty(self.n_agents, dtype=np.int64)

    # ---- (i) セル ----
    def _cell_changes(self, world: World, tick: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        raw = b4_block_raw(world, tick)
        if self._prev_raw is None or self._prev_raw.shape != raw.shape:
            rows = np.arange(raw.shape[0], dtype=np.int64)
        else:
            rows = np.flatnonzero(np.any(raw != self._prev_raw, axis=1)).astype(np.int64)
        hashes = b4_block_hashes(raw, rows)
        self._prev_raw = raw
        return raw, rows, hashes

    # ---- (ii) 内受容 ----
    def _interoception(self, agents: AgentState) -> tuple[B5Crossing, ...]:
        edges = INTERO_UP_EDGES
        stages = [agents.registry.field(sf).view(np.uint8) for _, sf in INTERO_VARS]
        # 逐次ループ宣言2: 内受容 3 変数ぶん(個体数には比例しない)
        for var, (value_field, _stage_field) in enumerate(INTERO_VARS):
            v = agents.registry.field(value_field)
            p = stages[var]
            up, dn, hit = self._up[var], self._dn[var], self._hit[var]
            up[:] = False
            dn[:] = False
            for k, e in enumerate(edges):
                # 上げ: 段 k にいて上げ閾値 e[k] に達した
                np.equal(p, k, out=self._b1)
                np.greater_equal(v, e, out=self._b2)
                np.logical_and(self._b1, self._b2, out=self._b3)
                np.logical_or(up, self._b3, out=up)
                # 下げ: 段 k+1 にいて下げ閾値 e[k]-h を割った(ヒステリシス)
                np.equal(p, k + 1, out=self._b1)
                np.less(v, e - INTERO_HYSTERESIS, out=self._b2)
                np.logical_and(self._b1, self._b2, out=self._b3)
                np.logical_or(dn, self._b3, out=dn)
            np.logical_or(up, dn, out=hit)
        # 3 変数ぶんの走査を 1 回にまとめる(``flatnonzero`` は 40万体で 0.3 ms/回)
        np.logical_or(self._hit[0], self._hit[1], out=self._any)
        np.logical_or(self._any, self._hit[2], out=self._any)
        if not self._any.any():
            return tuple(
                B5Crossing(var, sf, np.empty(0, dtype=np.int64), np.empty(0, dtype=np.uint8))
                for var, (_, sf) in enumerate(INTERO_VARS)
            )
        idx_all = np.flatnonzero(self._any).astype(np.int64)
        out: list[B5Crossing] = []
        for var, (_, stage_field) in enumerate(INTERO_VARS):
            sub = self._hit[var][idx_all]
            idx = idx_all[sub]
            p = stages[var]
            new = (
                p[idx].astype(np.int16)
                + self._up[var][idx].astype(np.int16)
                - self._dn[var][idx].astype(np.int16)
            ).astype(np.uint8)
            out.append(B5Crossing(var, stage_field, idx, new))
        return tuple(out)

    # ---- 本体 ----
    def detect(self, world: World, agents: AgentState, tick: int) -> DetectResult:
        """1 tick 分の変化検出(**書き込みなし**)。

        Args:
            world: セル状態(``density`` は前 tick の Phase C で更新済み)。
            agents: 個体状態。
            tick: 現在 tick。

        Returns:
            ``DetectResult``。
        """
        _, changed_cells, changed_hash = self._cell_changes(world, tick)
        if changed_cells.size:
            self._cell_mask[:] = False
            self._cell_mask[changed_cells] = True
            # 逐次ループ宣言3: 個体数ぶんの numba nogil ループ(cell<0 は場外=対象外)
            k = _CELL_WAKE(agents.registry.cell, self._cell_mask, self._wake_buf)
            cell_agents = self._wake_buf[:k].copy()
        else:
            cell_agents = np.empty(0, dtype=np.int64)
        crossings = self._interoception(agents)
        return DetectResult(
            tick=int(tick),
            changed_cells=changed_cells,
            changed_b4_hash=changed_hash,
            cell_wake_agents=cell_agents,
            crossings=crossings,
        )
