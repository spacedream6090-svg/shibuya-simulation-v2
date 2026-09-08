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
- (C3 結線で解消) B4 の欄は **知覚側の描画欄**(``perception.hashes.b4_field_row`` =
  LOS 6 段・騒音段・流れ・顕著行為ダイジェスト)に切り替えた。C2 の「密度段8値・騒音段・
  営業中POI数」は描画の欄と別物で、描画バイト変化の 48% を取りこぼしていた
  (``docs/ops/build-report-C3.md`` §2)。**営業中POI数は欄から外した**(描画に出ないため
  起床させるのは過検出。契約書 §6 (i) の列挙にも無い)。
- 流れ・顕著行為ダイジェストは C3 では常に 0(方向データと顕著行為の到達判定は C4)。
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
from shibuya.perception import hashes as PH
from shibuya.perception import normalize as PN
from shibuya.perception import templates as PT
from shibuya.perception.renderer import WALKABLE_FRACTION_SYNTHETIC
from shibuya.world.assets import CELL_SIZE_M
from shibuya.world.state import World

__all__ = [
    "INTERO_UP_EDGES",
    "INTERO_HYSTERESIS",
    "INTERO_VARS",
    "B4_FIELD_COLUMNS",
    "DEFAULT_WALKABLE_AREA_M2",
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

#: B4 の**描画に使う欄**の並び(``perception.hashes.b4_field_row`` と 1 対 1)。
B4_FIELD_COLUMNS: Final[tuple[str, ...]] = (
    "los_stage",  # 歩行者密度 LOS 6 段(人/m²・分母=歩行可能面積)
    "noise_stage",  # 騒音段階 4 段(W10 昼夜場 or 動的上書き)
    "flow",  # 流れ 3 値(方向データが入るまで 0)
    "salient_digest",  # 顕著行為の到達(行の xxh64 下位 31 bit・無ければ 0)
)
#: 歩行可能面積が与えられないときの分母[m²](``perception.renderer`` の合成世界と同値)。
DEFAULT_WALKABLE_AREA_M2: Final[float] = CELL_SIZE_M * CELL_SIZE_M * WALKABLE_FRACTION_SYNTHETIC


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


def b4_block_raw(
    world: World,
    tick: int,
    *,
    walkable_area_m2: np.ndarray | float | None = None,
    noise_stage: np.ndarray | None = None,
    flow: np.ndarray | None = None,
    salient_digest: np.ndarray | None = None,
) -> np.ndarray:
    """セル動的ブロック B4 の**描画欄** ``(n_cells, 4)`` int32(``B4_FIELD_COLUMNS`` の順)。

    知覚契約書 §2.2/§5 の三役は「**描画バイト列**のハッシュ」を要求する。C2 は安い代理として
    「密度段8値・騒音段・営業中POI数」を使っていたが、これは描画の欄と**別物**で、
    描画バイト変化の 48% を取りこぼしていた(``docs/ops/build-report-C3.md`` §2)。
    C3 の結線でこの関数を ``perception.hashes.b4_field_row``(描画がそれ**だけ**に依存する欄)
    へ切り替えた。欄ハッシュはこれで描画バイトの refinement になる。

    Args:
        world: セル状態。
        tick: 現在 tick(騒音の昼夜切替に使う)。
        walkable_area_m2: 密度→人/m² の分母。None なら ``DEFAULT_WALKABLE_AREA_M2``。
        noise_stage: 騒音段(None なら ``world.noise_stage_for_tick(tick)``)。
        flow: 流れ 0-2(None なら 0)。
        salient_digest: 顕著行為ダイジェスト(None なら 0)。

    Note:
        **営業中POI数は欄から外した**。店が開いても B4 の描画バイトは変わらない
        (営業時間は B2 の看板=セル固定)ので、起床条件 (i)「B4 ハッシュ変化」に載せると
        過検出になる。知覚契約書 §6 (i) の列挙(密度段階の跨ぎ・騒音段階・構造物・
        顕著行為の到達)にも営業中POI数は無い。
    """
    n = world.n_cells
    area = DEFAULT_WALKABLE_AREA_M2 if walkable_area_m2 is None else walkable_area_m2
    per_m2 = np.asarray(world.cells.density, dtype=np.float64) / np.maximum(
        np.asarray(area, dtype=np.float64), 1.0
    )
    los = PN.peg_stage_array(per_m2, PT.DENSITY_LOS_EDGES_PER_M2)
    ns = world.noise_stage_for_tick(tick) if noise_stage is None else np.asarray(noise_stage)
    fl = np.zeros(n, dtype=np.uint8) if flow is None else np.asarray(flow)
    sal = np.zeros(n, dtype=np.int32) if salient_digest is None else np.asarray(salient_digest)
    return PH.b4_field_row(los, ns, fl, sal)


def b4_block_hashes(raw: np.ndarray, rows: np.ndarray | None = None) -> np.ndarray:
    """B4 描画欄の行ごとの xxh64(``perception.hashes.field_row_hashes`` に委譲)。

    Args:
        raw: ``(n_cells, len(B4_FIELD_COLUMNS))`` int32(C 連続)。
        rows: 計算する行の索引(None なら全行)。

    Returns:
        ``rows`` と同じ長さの uint64 配列。

    Note:
        逐次ループ宣言1: **行数ぶんの xxh64 ループ**(上限=セル数 453/520。
        実装計画書が明示的に許した形)。実体は知覚側にある=**ハッシュの定義は 1 か所**。
    """
    return PH.field_row_hashes(raw, rows)


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

    def __init__(
        self,
        n_agents: int,
        n_cells: int,
        walkable_area_m2: np.ndarray | float | None = None,
    ) -> None:
        """
        Args:
            n_agents / n_cells: 規模。
            walkable_area_m2: 密度→人/m² の分母(知覚側 ``PerceptionAssets.walkable_area_m2``)。
                None なら ``DEFAULT_WALKABLE_AREA_M2``。**レンダラと同じ分母**を渡すこと
                (違う分母だと LOS 段がずれ、起床条件 (i) が描画バイトと食い違う)。
        """
        self.n_agents = int(n_agents)
        self.n_cells = int(n_cells)
        self.walkable_area_m2 = walkable_area_m2
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
    def _cell_changes(
        self, world: World, tick: int, field_rows: np.ndarray | None = None
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        if field_rows is None:
            raw = b4_block_raw(world, tick, walkable_area_m2=self.walkable_area_m2)
        else:
            raw = np.ascontiguousarray(np.asarray(field_rows, dtype=np.int32))
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
    def detect(
        self,
        world: World,
        agents: AgentState,
        tick: int,
        *,
        field_rows: np.ndarray | None = None,
    ) -> DetectResult:
        """1 tick 分の変化検出(**書き込みなし**)。

        Args:
            world: セル状態(``density`` は前 tick の Phase C で更新済み)。
            agents: 個体状態。
            tick: 現在 tick。
            field_rows: ``(n_cells, 4)`` int32 の B4 描画欄。**レンダラが既に作っていれば
                それを渡す**(``engine.run`` はそうする)= 検出器と描画が同じ 1 本の欄を見る
                =「起床条件 (i) が鳴らないのに文面が変わる」取りこぼしが構造的に 0 になる。
                None なら ``b4_block_raw`` が world から作る(単体運転・ベンチ用)。

        Returns:
            ``DetectResult``。
        """
        _, changed_cells, changed_hash = self._cell_changes(world, tick, field_rows)
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
