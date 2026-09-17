"""engine.geometry — C9 位置幾何(辺上の連続位置・歩行速度)の**切替口**。

正典
- C9 決定アジェンダ ``docs/design/v2-c9-geometry-agenda.md`` §1 + **§4 改訂**
  (2026-09-17 ユーザー決定): **G1 (b) 辺上の連続位置** / **G2 (b) 希望速度を
  1.00〜1.60 m/s の個体分布から引き、Kladek 式で密度減速** / **G9 P2 ≤300 ms/tick@40 万体** /
  **G11 失敗コード ``UNREACHABLE``・``TARGET_GONE``(猶予つき)**。
- 材料 ``docs/design/v2-c9-geometry-brief.md`` §1.2/§1.3(``xy`` は ``resolve`` が毎 tick
  ノード座標で上書き=位置がノード 3,499 個に量子化されている)・§1.4(歩行可能面積)。
- 速度式: ``docs/research/lit/crowd__kretz2015_kladek-formula.md``
  **v = v0·[1 − exp(−1.913·(1/ρ − 1/5.4))]**(Kretz 2015 §2 式 (1)(7)(8)(9)。
  Weidmann による Kladek 式のパラメータ化)。
- 希望速度の幅: ``docs/research/lit/crowd__bosina-weidmann2018_fd-generic-model.md``
  Table 2「Desired walking speed vd 1.00–1.60 m/s」。**年齢係数ではない**(§4 の訂正)。

ユーザー方針(2026-09-17)
    「物理は**事前計算した表・解析式**で再現し、tick ごとに物理エンジンは回さない」。
    → 辺長は W1 の表引き(``edge_len_m``)・速度減速は解析式(Kladek)1 本。力学積分は無い。

モード
    ``"node"``(既定)= 現行の 1 tick=1 ノード。**本モジュールは一切呼ばれない**
    = checkpoint は 1 バイトも動かない。
    ``"edge"`` = 体は「辺 ``edge_id`` の上・始点 ``node`` から ``edge_s`` [m]・
    向き ``node``→``path_next_node``」に居る。``xy`` は両端ノードの線形補間。

逐次ループ宣言(P4)
- ``EdgeGeometry.advance``: **ホップ数ぶん**のループ(上限 ``MAX_HOPS_PER_TICK``)。
  各反復は「まだ進める体」だけの配列演算で、反復のたびに対象が縮む。**個体数に比例する
  Python ループは無い**。走査対象は ``activity==MOVING and target_node>=0`` の体のみ
  (``engine.commit.engine_continuations`` が選ぶ集合)。
- ``EdgeGeometry.positions``: ループなし(配列演算のみ・全個体 1 本)。

expedient(本モジュール分)
- 希望速度の母集団合成を **一様分布 Uniform(1.00, 1.60)** にした。Bosina & Weidmann 2018
  §3.3.1 が挙げる 4 通り(minimum / maximum / average / **uniform**)の 1 つで、
  帯の中身(何本の研究の何パーセンタイルか)は原典が有料で**空欄**。平均・中央は
  **1.30 m/s** であって Weidmann の自由速度 1.34 m/s(``SPEED_REFERENCE_MS``)ではない。
- ``MAX_HOPS_PER_TICK``(1 tick に跨げる辺の上限)は自前。W1 の最短辺 1.0 m・
  最大予算 1.60 m/s × 60 s = 96 m なので理論上は 96 ホップありうるが、実測の中央辺長
  21.75 m では 32 で足りる。**超過分の距離は次 tick へ繰り越さず捨てる**(体は辺上に残る)。
- 辺上の距離 ``edge_s`` は W1 の **街路長 ``length_m``** で測り、``xy`` は両端ノードの
  **直線補間**で描く(実測比 p50 1.0007・p90 1.071 = 街路長は直線距離より長い)。
  つまり「到着時刻は街路長・見た目の座標は直線」の近似。
- セル/層は**近い方の端点**(``edge_s / 辺長 ≥ 0.5`` なら先のノード)から取る。
  ``node``(経路の基点)とは別概念。
- 密度 ρ は**前 tick 末の ``world.cells.density``**(``apply`` の末尾で貼り直される値)を
  使う=陽的スキーム。同 tick 内の順序依存を作らないための選択。
- ρ ≥ 5.4 人/m²(Kladek の詰め込み密度)では係数が 0 = **体は動かない**。
  式どおりの振る舞いで、床は置かない(置くと設計者の指紋になる)。件数は
  ``ResolveOutcome.n_jammed`` に出して見えるようにする。
"""

from __future__ import annotations

from typing import Final

import numpy as np

from shibuya.core.rng import derive_key
from shibuya.engine.change_detect import DEFAULT_WALKABLE_AREA_M2
from shibuya.world.assets import WorldAssets
from shibuya.world.state import DENSITY_STAGE_EDGES_PER_M2

__all__ = [
    "GEOMETRY_MODES",
    "DEFAULT_GEOMETRY",
    "check_geometry",
    "KLADEK_GAMMA",
    "KLADEK_RHO_MAX_PER_M2",
    "SPEED_REFERENCE_MS",
    "DESIRED_SPEED_MIN_MS",
    "DESIRED_SPEED_MAX_MS",
    "DESIRED_SPEED_DOMAIN",
    "MAX_HOPS_PER_TICK",
    "ARRIVE_EPSILON_M",
    "kladek_speed_factor",
    "desired_speeds",
    "EdgeGeometry",
]

#: 幾何モードの集合(``run_day(geometry=...)`` / ``--geometry``)。
GEOMETRY_MODES: Final[tuple[str, ...]] = ("node", "edge")
#: 既定=現行の 1 tick=1 ノード(**バイト不変**)。
DEFAULT_GEOMETRY: Final[str] = GEOMETRY_MODES[0]

#: Kladek 式の γ[1/m²](Kretz 2015 式 (8))。
KLADEK_GAMMA: Final[float] = 1.913
#: Kladek 式の ρ_max[人/m²](同 式 (9))。ここで速度 0。
KLADEK_RHO_MAX_PER_M2: Final[float] = 5.4
#: Weidmann の自由速度[m/s](同 式 (7))。**参照値**=個体の希望速度はこの値を使わない。
SPEED_REFERENCE_MS: Final[float] = 1.34
#: 希望歩行速度の帯[m/s](Bosina & Weidmann 2018 Table 2)。
DESIRED_SPEED_MIN_MS: Final[float] = 1.00
DESIRED_SPEED_MAX_MS: Final[float] = 1.60
#: 希望速度を引く決定論ドメイン(``core.rng.derive_key`` の鍵材料)。
DESIRED_SPEED_DOMAIN: Final[str] = "geometry.desired_speed"

#: 1 tick に跨げる辺の上限(expedient・逐次ループの反復上限)。
MAX_HOPS_PER_TICK: Final[int] = 32
#: 「ノードに達した」とみなす残距離[m]。
ARRIVE_EPSILON_M: Final[float] = 1e-6


def check_geometry(value: str) -> str:
    """幾何モードの検査(``run_day`` が**世界を作る前**に呼ぶ=manifest が嘘をつかない)。"""
    text = str(value)
    if text not in GEOMETRY_MODES:
        raise ValueError(f"geometry は {GEOMETRY_MODES} のどれか(いま {value!r})")
    return text


def _mix64(x: np.ndarray) -> np.ndarray:
    """splitmix64 の最終混合(決定論・ベクトル化・**乱数ではない**)。

    ``engine.presence._mix64`` / ``build.sched.w17_schedule._mix64`` と**同じ式**
    (層をまたぐ共有モジュールを作れないための三重定義・テストが一致を機械検査)。
    ランの乱数列を 1 語も消費しないので T4(規模不変)が保たれる。
    """
    v = np.asarray(x, dtype=np.uint64).copy()
    with np.errstate(over="ignore"):
        v ^= v >> np.uint64(33)
        v *= np.uint64(0xFF51AFD7ED558CCD)
        v ^= v >> np.uint64(33)
        v *= np.uint64(0xC4CEB9FE1A85EC53)
        v ^= v >> np.uint64(33)
    return v


def kladek_speed_factor(rho_per_m2) -> np.ndarray:
    """密度 → 自由速度に対する比 ``v/v0``(Kladek/Weidmann・**解析式 1 本**)。

    ``v/v0 = 1 − exp(−γ·(1/ρ − 1/ρ_max))``(Kretz 2015 §2 式 (1)+(8)(9))。
    ρ→0 で 1・ρ ≥ ρ_max(5.4 人/m²)で 0。負にならないよう ``[0, 1]`` に clip する
    (lit メモの「実装では clip が要る」)。

    Example:
        >>> float(kladek_speed_factor(0.0))
        1.0
        >>> round(float(kladek_speed_factor(3.33)) * 1.34, 3)
        0.265
    """
    rho = np.asarray(rho_per_m2, dtype=np.float64)
    inv = np.divide(1.0, rho, out=np.full(rho.shape, np.inf), where=rho > 0.0)
    f = 1.0 - np.exp(-KLADEK_GAMMA * (inv - 1.0 / KLADEK_RHO_MAX_PER_M2))
    return np.clip(np.nan_to_num(f, nan=0.0, posinf=1.0, neginf=0.0), 0.0, 1.0)


def desired_speeds(seed: int | str, agent_ids) -> np.ndarray:
    """個体の希望歩行速度[m/s](**seed と agent_id だけの決定論**・float32)。

    ``Uniform(1.00, 1.60)``(Bosina & Weidmann 2018 Table 2 の帯・母集団合成は
    同 §3.3.1 の ``uniform`` 腕)。``core.rng`` の Philox 列は**引かない**
    (ランの乱数列を消費すると T4 規模不変と帰無腕のバイト一致が壊れる)ので、
    鍵だけ ``derive_key`` から取り splitmix64 で個体ごとに混ぜる。
    """
    k0, _ = derive_key(seed, DESIRED_SPEED_DOMAIN)
    ids = np.asarray(agent_ids, dtype=np.int64)
    bits = _mix64(ids.astype(np.uint64) ^ np.uint64(k0 & ((1 << 64) - 1)))
    u = (bits >> np.uint64(11)).astype(np.float64) / float(1 << 53)  # [0, 1)
    return (DESIRED_SPEED_MIN_MS + (DESIRED_SPEED_MAX_MS - DESIRED_SPEED_MIN_MS) * u).astype(
        np.float32
    )


class EdgeGeometry:
    """辺上の連続位置(G1 (b))と歩行速度(G2 (b))の**前計算した表**+解析式。

    ``resolve.apply(..., geometry=EdgeGeometry(...))`` で edge モードになる。
    渡さなければ ``resolve`` は現行の 1 tick=1 ノードの経路をそのまま通る。

    Attributes:
        v_desired: 個体ごとの希望速度[m/s](``(n_agents,)`` float32・前計算)。
        walkable_area_m2: セル別歩行可能面積[m²](密度の分母・既存値を再利用)。

    Example:
        >>> from shibuya.world.state import World
        >>> g = EdgeGeometry(World.synthetic(n_cells=9, seed=1).assets, seed=1, n_agents=4)
        >>> bool((g.v_desired >= 1.0).all() and (g.v_desired <= 1.6).all())
        True
    """

    def __init__(
        self,
        assets: WorldAssets,
        *,
        seed: int | str,
        n_agents: int,
        walkable_area_m2=None,
        tick_seconds: int = 60,
    ) -> None:
        self.assets = assets
        self.seed = seed
        self.n_agents = int(n_agents)
        self.tick_seconds = int(tick_seconds)
        self.v_desired = desired_speeds(seed, np.arange(self.n_agents, dtype=np.int64))

        n_cells = int(assets.n_cells)
        if walkable_area_m2 is None:
            area = np.full(n_cells, DEFAULT_WALKABLE_AREA_M2, dtype=np.float64)
        else:
            area = np.asarray(walkable_area_m2, dtype=np.float64).ravel()
            if area.size != n_cells:
                raise ValueError(
                    f"walkable_area_m2 の長さが {area.size}(セル数 {n_cells})"
                )
        self.walkable_area_m2 = np.maximum(area, 1.0)

        # ---- 前計算した表 ①: (u, v) → 辺索引(両向き・searchsorted 用に整列) ----
        n_nodes = int(assets.n_nodes)
        self._n_nodes = n_nodes
        u = np.asarray(assets.edge_u, dtype=np.int64)
        v = np.asarray(assets.edge_v, dtype=np.int64)
        eid = np.arange(u.size, dtype=np.int64)
        key = np.concatenate([u * n_nodes + v, v * n_nodes + u])
        val = np.concatenate([eid, eid])
        order = np.argsort(key, kind="stable")
        self._pair_key = key[order]
        self._pair_edge = val[order].astype(np.int32)
        # ---- 前計算した表 ②: 辺 → 街路長[m](W1 の実測値) ----
        self._edge_len = np.asarray(assets.edge_len_m, dtype=np.float64)
        self._node_xy = np.asarray(assets.node_xy, dtype=np.float64)

    # ------------------------------------------------------------------ 表引き
    def lookup_edge(self, u, v) -> tuple[np.ndarray, np.ndarray]:
        """``(u, v)`` → ``(辺索引, 辺長[m])``。表に無い対は ``(-1, 直線距離)``。

        逐次ループ宣言(P4): なし(``searchsorted`` 1 回)。
        """
        uu = np.asarray(u, dtype=np.int64).ravel()
        vv = np.asarray(v, dtype=np.int64).ravel()
        out_e = np.full(uu.shape, -1, dtype=np.int64)
        out_l = np.zeros(uu.shape, dtype=np.float64)
        ok = (uu >= 0) & (vv >= 0)
        if not np.any(ok) or self._pair_key.size == 0:
            return out_e, out_l
        k = uu[ok] * self._n_nodes + vv[ok]
        pos = np.clip(np.searchsorted(self._pair_key, k), 0, self._pair_key.size - 1)
        hit = self._pair_key[pos] == k
        e = np.where(hit, self._pair_edge[pos].astype(np.int64), -1)
        straight = np.linalg.norm(
            self._node_xy[vv[ok]] - self._node_xy[uu[ok]], axis=1
        )
        length = np.where(hit, self._edge_len[np.maximum(e, 0)], straight)
        out_e[ok] = e
        out_l[ok] = length
        return out_e, out_l

    def edge_length(self, edge_id, u, v) -> np.ndarray:
        """辺索引(無ければ両端ノード)から辺長[m]を引く。"""
        e = np.asarray(edge_id, dtype=np.int64).ravel()
        uu = np.asarray(u, dtype=np.int64).ravel()
        vv = np.asarray(v, dtype=np.int64).ravel()
        known = (e >= 0) & (e < self._edge_len.size)
        out = np.where(known, self._edge_len[np.maximum(e, 0)], 0.0)
        rest = (~known) & (uu >= 0) & (vv >= 0)
        if np.any(rest):
            out[rest] = np.linalg.norm(
                self._node_xy[vv[rest]] - self._node_xy[uu[rest]], axis=1
            )
        return out

    # ------------------------------------------------------------------ 速度
    def speed_factor_per_cell(self, density) -> np.ndarray:
        """セル別の減速係数 ``v/v0``(Kladek・``(n_cells,)`` float64)。"""
        d = np.asarray(density, dtype=np.float64).ravel()
        return kladek_speed_factor(d / self.walkable_area_m2)

    def tick_budget_m(self, agent_id, cell, density) -> np.ndarray:
        """その tick に歩ける距離[m] = ``v_desired × f(ρ) × tick_seconds``。"""
        aid = np.asarray(agent_id, dtype=np.int64).ravel()
        c = np.asarray(cell, dtype=np.int64).ravel()
        factor_cell = self.speed_factor_per_cell(density)
        f = np.where(
            (c >= 0) & (c < factor_cell.size), factor_cell[np.clip(c, 0, max(factor_cell.size - 1, 0))], 1.0
        )
        v = self.v_desired[np.clip(aid, 0, max(self.v_desired.size - 1, 0))].astype(np.float64)
        return v * f * float(self.tick_seconds)

    def density_stage(self, density) -> np.ndarray:
        """人/m² の Fruin LOS 段(``world.state.DENSITY_STAGE_EDGES_PER_M2``)。"""
        d = np.asarray(density, dtype=np.float64).ravel()
        per_m2 = d / self.walkable_area_m2
        return np.searchsorted(
            np.asarray(DENSITY_STAGE_EDGES_PER_M2), per_m2, side="right"
        ).astype(np.uint8)

    # ------------------------------------------------------------------ 前進
    def advance(self, *, node, next_node, edge_s, edge_id, target, budget_m, route):
        """辺上を ``budget_m`` だけ進める(**純関数**・新しい配列を返す)。

        Args:
            node: 直前に通過したノード(``(k,)`` int)。
            next_node: 向かっている先のノード(``-1``=辺に乗っていない)。
            edge_s: ``node`` からの距離[m]。
            edge_id: いま乗っている辺(``-1``=乗っていない)。
            target: 目的ノード。
            budget_m: この tick に歩ける距離[m]。
            route: ``(node, target) -> 次ホップ`` の呼び出し可能(``WalkGraph.route_next_node``)。

        Returns:
            ``(node, next_node, edge_s, edge_id, arrived, stuck, n_hops)``。
            ``arrived``=目的ノードに達した・``stuck``=次ホップが引けない(``UNREACHABLE``)。

        逐次ループ宣言(P4): ホップ数ぶん(≤``MAX_HOPS_PER_TICK``)。
        """
        nd = np.asarray(node, dtype=np.int64).copy()
        nx = np.asarray(next_node, dtype=np.int64).copy()
        s = np.asarray(edge_s, dtype=np.float64).copy()
        eid = np.asarray(edge_id, dtype=np.int64).copy()
        tgt = np.asarray(target, dtype=np.int64).ravel()
        budget = np.asarray(budget_m, dtype=np.float64).copy()
        k = nd.size
        arrived = np.zeros(k, dtype=bool)
        stuck = np.zeros(k, dtype=bool)
        if k == 0:
            return nd, nx, s.astype(np.float32), eid, arrived, stuck, 0

        seglen = self.edge_length(eid, nd, nx)
        # 目的ノードに既に居る体(通常は前 tick で到着済み)
        arrived |= (nd == tgt) & (tgt >= 0)
        # 場外(``node`` < 0)・目的なし(``target`` < 0)は node 幾何の ``step_once`` と同じく
        # 「前に進めない」= ``UNREACHABLE``。**詰まり(予算 0)は stuck ではない**(遅いだけ)。
        stuck |= (~arrived) & ((nd < 0) | (tgt < 0))
        idx = np.flatnonzero(
            (~arrived) & (~stuck) & (budget > ARRIVE_EPSILON_M)
        )
        n_hops = 0
        for _ in range(MAX_HOPS_PER_TICK):
            if idx.size == 0:
                break
            # (a) 辺に乗っていない体に次のホップを引く(next-hop 表=ファンシー添字1回)
            need = idx[nx[idx] < 0]
            if need.size:
                nh = np.asarray(route(nd[need], tgt[need]), dtype=np.int64)
                ok = (nh >= 0) & (nh != nd[need])
                stuck[need[~ok]] = True
                nx[need] = np.where(ok, nh, -1)
                e, ln = self.lookup_edge(nd[need], np.where(ok, nh, -1))
                eid[need] = np.where(ok, e, -1)
                seglen[need] = np.where(ok, ln, 0.0)
                s[need] = 0.0
            idx = idx[nx[idx] >= 0]
            if idx.size == 0:
                break
            # (b) 進む(辺の残りと予算の小さい方)
            rem = np.maximum(seglen[idx] - s[idx], 0.0)
            step = np.minimum(budget[idx], rem)
            s[idx] += step
            budget[idx] -= step
            # (c) ノードに達した体は次の辺へ(目的ノードなら到着)
            reached = idx[s[idx] >= seglen[idx] - ARRIVE_EPSILON_M]
            if reached.size:
                nd[reached] = nx[reached]
                nx[reached] = -1
                eid[reached] = -1
                s[reached] = 0.0
                seglen[reached] = 0.0
                arrived[reached[nd[reached] == tgt[reached]]] = True
            n_hops += 1
            idx = idx[(budget[idx] > ARRIVE_EPSILON_M) & ~arrived[idx] & ~stuck[idx]]
        # 到着・到達不能の体は辺から降ろす(辺上に居てよいのは移動中の体だけ)
        off = arrived | stuck
        nx[off] = -1
        eid[off] = -1
        s[off] = 0.0
        return nd, nx, s.astype(np.float32), eid, arrived, stuck, n_hops

    # ------------------------------------------------------------------ 位置
    def positions(self, node, next_node, edge_s, edge_id):
        """辺上の連続位置 → ``(cell, band, xy)``(**純関数**・全個体 1 本の配列演算)。

        - ``xy`` = 両端ノードの**線形補間**(``edge_s / 辺長`` の比・float32)。
        - ``cell`` / ``band`` = **近い方の端点**のセル/層(比 ≥ 0.5 で先のノード)。
        - 辺に乗っていない体(``next_node < 0``)は従来どおりノード座標そのもの。
        """
        nd = np.asarray(node, dtype=np.int64).ravel()
        nx = np.asarray(next_node, dtype=np.int64).ravel()
        s = np.asarray(edge_s, dtype=np.float64).ravel()
        eid = np.asarray(edge_id, dtype=np.int64).ravel()
        on_edge = (nx >= 0) & (nd >= 0)
        seglen = self.edge_length(eid, nd, nx)
        frac = np.zeros(nd.shape, dtype=np.float64)
        np.divide(s, seglen, out=frac, where=(seglen > 0.0) & on_edge)
        frac = np.clip(frac, 0.0, 1.0)

        safe_nd = np.maximum(nd, 0)
        safe_nx = np.where(on_edge, np.maximum(nx, 0), safe_nd)
        a = self._node_xy[safe_nd]
        b = self._node_xy[safe_nx]
        # ``nd < 0``(場外)は ``frac=0`` で ``node_xy[0]`` になる= node 幾何の
        # ``r.xy[:] = node_xy[max(node, 0)]`` と**同じ値**(腕の差を余計に作らない)。
        xy = (a + frac[:, None] * (b - a)).astype(np.float32)

        near = np.where(on_edge & (frac >= 0.5), safe_nx, safe_nd)
        valid = nd >= 0
        cell = np.where(valid, self.assets.node_cell[near], -1).astype(np.int32)
        band = np.where(valid, self.assets.node_band[near], 0).astype(np.int8)
        return cell, band, xy

    def snap_to_nearest_node(self, node, next_node, edge_s, edge_id):
        """辺上の体を**近い方の端点**へ吸着する(**純関数**)。

        新しい行動(移動・購入・待機…)を選んだ体は、その時点でノードに立っていることに
        する。``node`` を基点に経路を引き直すための前処理で、ずれは高々「辺長の半分」。
        """
        nd = np.asarray(node, dtype=np.int64).copy()
        nx = np.asarray(next_node, dtype=np.int64).ravel()
        s = np.asarray(edge_s, dtype=np.float64).ravel()
        eid = np.asarray(edge_id, dtype=np.int64).ravel()
        on_edge = (nx >= 0) & (nd >= 0)
        seglen = self.edge_length(eid, nd, nx)
        frac = np.zeros(nd.shape, dtype=np.float64)
        np.divide(s, seglen, out=frac, where=(seglen > 0.0) & on_edge)
        nd = np.where(on_edge & (frac >= 0.5), nx, nd)
        zero_i = np.full(nd.shape, -1, dtype=np.int64)
        return nd, zero_i, np.zeros(nd.shape, dtype=np.float32), zero_i.copy()
