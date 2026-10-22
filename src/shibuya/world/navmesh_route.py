"""world.navmesh_route — ナビメッシュの上の経路の形を引く道具(W1 の通り道 → 帯の A* → funnel)。

正: 空間の設計の下書き §4 段 1・SR12 (a)(曲がる 1 回 ≈ 50 m・上り 1 m ≈ 3.8 m を段 1 に入れる)・SR13 (a)。

**二段の探索**(HPA* と同じ考え=R-59 §2-1): 通りの単位の選び(曲がる回数と上り)は W1 の向きつきの辺の Dijkstra
(曲がる=向きが 45° 以上変わる=R-61 SF の定義)で引き、その通り道の近くの帯(資産 ``nav1_corridor``=辺から 20 m)に
絞って帯の A*(距離+上りの重み)を引き、funnel で面の上の線にする。通り道の中で引けなければ全体に広げて引き直す
(``RouteGeom.mode`` 1=数える)。経路の選びは本人の判断(段 3/判断モデルの後)=今は既定の重み(つなぎ)で、
3 つの性格の違う候補を出す口 :meth:`NavPlanner.candidates` だけを置く(呼び手なし=J0 の形)。

逐次ループ宣言(P4): 経路を 1 本引くごとに、W1 の通り道の節の数ぶんと区間の数ぶんの Python のループ(探索の本体は
numba)。体ごとのループではない(呼び手=``engine.space.nav1`` が新しく経路の要る体だけを回す)。
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Final

import numpy as np

from shibuya.world.navmesh import (
    NavMesh,
    astar_strips,
    corridor_portals,
    funnel_points,
    w1_turn_dijkstra,
)

__all__ = ["RouteGeom", "NavPlanner", "TURN_ANGLE_DEG", "MODE_CORRIDOR", "MODE_WIDE"]

#: 「曲がる」の角(R-61 §3-1 SF「at least a 45-degree change in direction」)。
TURN_ANGLE_DEG: Final[float] = 45.0
#: 経路の引き方: 通り道の中で引けた / 全体に広げて引いた。
MODE_CORRIDOR: Final[int] = 0
MODE_WIDE: Final[int] = 1


@dataclass
class RouteGeom:
    """1 本の経路の形(``engine.space.nav1`` が時間を載せる)。

    ``pts`` (k, 2) の点・``fi`` (k,) 点の階の添字・``seg_link`` (k-1,) 区間が接続口ならその番号(歩く区間は -1)・
    ``seg_dir`` (k-1,) 接続口の向き(0=a→b)・``ck_vertex``/``ck_node`` W1 の節を通った点の添字と節の番号(昇順)・
    ``w1_path`` 通り道の節の列・``mode`` 引き方・``expanded`` A* の展開数。
    """

    pts: np.ndarray
    fi: np.ndarray
    seg_link: np.ndarray
    seg_dir: np.ndarray
    ck_vertex: np.ndarray
    ck_node: np.ndarray
    w1_path: np.ndarray
    mode: int
    expanded: int

    @property
    def length_m(self) -> float:
        d = np.hypot(*np.diff(self.pts, axis=0).T) if self.pts.shape[0] > 1 else np.zeros(0)
        return float(d[self.seg_link < 0].sum())


class NavPlanner:
    """経路の形を引く道具(作業の配列を持つ=1 つのランで 1 つ・決定論=同点は番号の小さい方)。

    ``link_cost_ab``/``link_cost_ba`` は接続口の重み[m](基準の速さで歩いたときの時間の距離=呼び手が渡す)。
    """

    def __init__(self, mesh: NavMesh, node_xy: np.ndarray, edge_u: np.ndarray, edge_v: np.ndarray,
                 edge_len_m: np.ndarray, edge_geom: tuple[np.ndarray, np.ndarray] | None,
                 link_cost_ab: np.ndarray, link_cost_ba: np.ndarray) -> None:
        self.mesh = m = mesh
        n_s = m.n_strips
        self.g = np.zeros(n_s)
        self.parent = np.zeros(n_s, dtype=np.int64)
        self.via_kind = np.zeros(n_s, dtype=np.int8)
        self.via_ref = np.zeros(n_s, dtype=np.int32)
        self.via_dir = np.zeros(n_s, dtype=np.int8)
        self.ex = np.zeros(n_s)
        self.ey = np.zeros(n_s)
        self.closed = np.zeros(n_s, dtype=np.int64)
        self.cstamp = 0
        self.allow = np.zeros(n_s, dtype=np.int64)
        self.astamp = 0
        hcap = max(64, 4 * int(m.adj_to.size) + 16)
        self.hf = np.zeros(hcap)
        self.hi = np.zeros(hcap, dtype=np.int64)
        self.link_cost_ab = np.ascontiguousarray(link_cost_ab, dtype=np.float64)
        self.link_cost_ba = np.ascontiguousarray(link_cost_ba, dtype=np.float64)
        # ---- W1 の向きつきの辺(2E 個: 0..E-1 = u→v・E..2E-1 = v→u)
        u = np.asarray(edge_u, dtype=np.int64)
        v = np.asarray(edge_v, dtype=np.int64)
        E = int(u.size)
        self.n_edges = E
        self.n_nodes = int(np.asarray(node_xy).shape[0])
        nxy = np.asarray(node_xy, dtype=np.float64)
        du = np.concatenate([u, v])
        dv = np.concatenate([v, u])
        self.dir_edge = np.concatenate([np.arange(E), np.arange(E)]).astype(np.int64)
        head_out = np.zeros((2 * E, 2))
        head_in = np.zeros((2 * E, 2))
        for k in range(E):
            xy = None
            if edge_geom is not None:
                coords, off = edge_geom
                g = np.asarray(coords[int(off[k]):int(off[k + 1])], dtype=np.float64)
                if g.shape[0] >= 2:
                    xy = g if np.hypot(*(g[0] - nxy[u[k]])) <= np.hypot(*(g[-1] - nxy[u[k]])) else g[::-1]
            if xy is None:
                xy = np.stack([nxy[u[k]], nxy[v[k]]])
            a0 = xy[1] - xy[0]
            a1 = xy[-1] - xy[-2]
            for d, ho, hin in ((k, a0, a1), (k + E, -a1, -a0)):
                no = math.hypot(ho[0], ho[1]) or 1.0
                ni = math.hypot(hin[0], hin[1]) or 1.0
                head_out[d] = ho / no
                head_in[d] = hin / ni
        z_node = np.zeros(self.n_nodes)
        for i in range(self.n_nodes):
            f = int(m.anchor_fi[i])
            if f >= 0:
                z = m.z_at(f, float(m.anchor_x[i]), float(m.anchor_y[i]))
                z_node[i] = 0.0 if math.isnan(z) else z
        self.dir_rise = (z_node[dv] - z_node[du]).astype(np.float64)
        self.dir_len = np.concatenate([edge_len_m, edge_len_m]).astype(np.float64)
        self.dir_end = dv
        self.head_out = np.ascontiguousarray(head_out)
        self.head_in = np.ascontiguousarray(head_in)
        order = np.argsort(du, kind="stable")
        self.out_to = order.astype(np.int64)
        self.out_ptr = np.concatenate([[0], np.cumsum(np.bincount(du, minlength=self.n_nodes))]).astype(np.int64)
        self.dist = np.zeros(2 * E)
        self.dparent = np.zeros(2 * E, dtype=np.int64)
        self.done = np.zeros(2 * E, dtype=np.int64)
        self.dstamp = 0
        self.dhf = np.zeros(8 * E + 16)
        self.dhi = np.zeros(8 * E + 16, dtype=np.int64)
        self._alloc(1 << 14)
        self.anchor_fi = np.asarray(m.anchor_fi, dtype=np.int64)
        self.anchor_xy = np.stack([m.anchor_x, m.anchor_y], axis=1)
        self.cos_turn = math.cos(math.radians(TURN_ANGLE_DEG))

    def _alloc(self, sz: int) -> None:
        self.lx = np.zeros(sz)
        self.ly = np.zeros(sz)
        self.rx = np.zeros(sz)
        self.ry = np.zeros(sz)
        self.out_buf = np.zeros((sz + 4, 2))

    # ------------------------------------------------------------------ W1 の通り道
    def nearest_node(self, x: float, y: float, fi: int) -> int:
        """同じ階の節の点で最も近い節(同じ階に無ければ全部から)。同点は番号の小さい方。"""
        d = np.hypot(self.anchor_xy[:, 0] - x, self.anchor_xy[:, 1] - y)
        same = self.anchor_fi == int(fi)
        if same.any():
            d = np.where(same, d, np.inf)
        return int(np.argmin(d))

    def w1_path(self, s: int, t: int, turn_w: float, climb_w: float) -> np.ndarray:
        """W1 の節 s → t の向きつきの辺の列(無ければ空)。"""
        if s == t or s < 0 or t < 0:
            return np.zeros(0, dtype=np.int64)
        self.dstamp += 1
        lo, hi = int(self.out_ptr[s]), int(self.out_ptr[s + 1])
        last = w1_turn_dijkstra(self.dir_len.size, self.out_ptr, self.out_to, self.dir_len, self.dir_rise,
                                self.head_out, self.head_in, self.dir_end, lo, hi, self.out_to, int(t),
                                float(turn_w), float(climb_w), float(self.cos_turn), self.dist, self.dparent,
                                self.done, self.dstamp, self.dhf, self.dhi)
        if last < 0:
            return np.zeros(0, dtype=np.int64)
        seq = [int(last)]
        while self.dparent[seq[-1]] >= 0:
            seq.append(int(self.dparent[seq[-1]]))
        return np.asarray(seq[::-1], dtype=np.int64)

    # ------------------------------------------------------------------ 帯の A*
    def _astar(self, s0, sx, sy, s1, gx, gy, climb_w, use_allow):
        m = self.mesh
        self.cstamp += 1
        return astar_strips(m.adj_ptr, m.adj_to, m.adj_kind, m.adj_ref, m.adj_dir, m.portal_y, m.portal_x0,
                            m.portal_x1, m.link_ax, m.link_ay, m.link_bx, m.link_by, self.link_cost_ab,
                            self.link_cost_ba, m.strip_floor, m.floor_code, m.strip_z, m.dem_z, m.dem_ox, m.dem_oy,
                            m.dem_res, int(s0), float(sx), float(sy), int(s1), float(gx), float(gy), float(climb_w),
                            self.allow, self.astamp, bool(use_allow), self.g, self.parent, self.via_kind,
                            self.via_ref, self.via_dir, self.ex, self.ey, self.closed, self.cstamp, self.hf, self.hi)

    def plan(self, ox: float, oy: float, ofi: int, target_node: int, *, turn_w: float, climb_w: float,
             use_corridor: bool = True) -> RouteGeom | None:
        """(ox, oy, 階の添字 ofi) → 節 ``target_node`` の点までの経路の形(引けなければ None)。"""
        m = self.mesh
        if target_node < 0 or target_node >= self.n_nodes:
            return None
        gfi = int(m.anchor_fi[target_node])
        if gfi < 0:
            return None
        gx, gy = float(m.anchor_x[target_node]), float(m.anchor_y[target_node])
        r0 = m.locate(ofi, ox, oy)
        if r0 < 0:
            r0, ox, oy, _d = m.nearest(ofi, ox, oy, 5.0)
            if r0 < 0:
                return None
        r1 = int(m.anchor_run[target_node])
        s0 = int(m.run_strip[r0])
        s1 = int(m.run_strip[r1])
        sn = self.nearest_node(ox, oy, ofi)
        path = self.w1_path(sn, int(target_node), turn_w, climb_w) if use_corridor else np.zeros(0, np.int64)
        self.astamp += 1
        st = self.astamp
        self.allow[s0] = st
        self.allow[s1] = st
        for d in path:
            e = int(self.dir_edge[d])
            self.allow[m.corr_strips[m.corr_ptr[e]:m.corr_ptr[e + 1]]] = st
        mode = MODE_CORRIDOR
        n_exp = 0
        ok = False
        if path.size or s0 == s1:
            ok, n_exp = self._astar(s0, ox, oy, s1, gx, gy, climb_w, True)
        if not ok:
            mode = MODE_WIDE
            ok, n2 = self._astar(s0, ox, oy, s1, gx, gy, climb_w, False)
            n_exp += int(n2)
        if not ok:
            return None
        seq = [s1]
        while self.parent[seq[-1]] >= 0:
            seq.append(int(self.parent[seq[-1]]))
        seq = seq[::-1]
        nodes = [int(self.dir_end[d]) for d in path]
        return self._shape(seq, r0, ox, oy, r1, gx, gy, nodes, mode, int(n_exp))

    def candidates(self, ox: float, oy: float, ofi: int, target_node: int, *, turn_w: float, climb_w: float
                   ) -> dict[str, RouteGeom | None]:
        """性格の違う 3 つの候補(最短/曲がりが少ない/坂が少ない)。**呼び手なし**=段 3/判断モデルの回で本人が選ぶ口。

        - ``shortest``: 曲がると上りの重み 0(距離だけ)。
        - ``fewer_turns``: 曲がる重みを 4 倍(既定の重みの 4 倍=未リサーチ・候補の性格を出すための値)。
        - ``less_climb``: 上りの重みを 4 倍(同上)。
        """
        return {
            "shortest": self.plan(ox, oy, ofi, target_node, turn_w=0.0, climb_w=0.0),
            "fewer_turns": self.plan(ox, oy, ofi, target_node, turn_w=4.0 * turn_w, climb_w=climb_w),
            "less_climb": self.plan(ox, oy, ofi, target_node, turn_w=turn_w, climb_w=4.0 * climb_w),
        }

    # ------------------------------------------------------------------ 形
    def _shape(self, seq, r0, ox, oy, r1, gx, gy, nodes, mode, n_exp) -> RouteGeom:
        m = self.mesh
        pts: list[np.ndarray] = []
        fis: list[int] = []
        links: list[int] = []
        dirs: list[int] = []
        seg_strips = [seq[0]]
        entry_run = [r0]
        exit_run: list[int] = []
        inter: list[tuple[float, float, float]] = []
        cur_start = (ox, oy)
        cur_fi = int(m.run_floor[r0])
        for k in range(1, len(seq)):
            v = seq[k]
            kind = int(self.via_kind[v])
            ref = int(self.via_ref[v])
            if kind == 0:
                lo, hi = int(m.portal_lo_run[ref]), int(m.portal_hi_run[ref])
                ent = lo if int(m.run_strip[lo]) == v else hi
                ext = hi if ent == lo else lo
                exit_run.append(ext)
                entry_run.append(ent)
                inter.append((float(m.portal_y[ref]), float(m.portal_x0[ref]), float(m.portal_x1[ref])))
                seg_strips.append(v)
            else:
                d = int(self.via_dir[v])
                if d == 0:
                    ax, ay, bx, by, bfi = m.link_ax[ref], m.link_ay[ref], m.link_bx[ref], m.link_by[ref], int(
                        m.link_bfi[ref])
                    afi = int(m.link_afi[ref])
                else:
                    ax, ay, bx, by, bfi = m.link_bx[ref], m.link_by[ref], m.link_ax[ref], m.link_ay[ref], int(
                        m.link_afi[ref])
                    afi = int(m.link_bfi[ref])
                exit_run.append(m.locate(afi, float(ax), float(ay)))
                p = self._funnel(seg_strips, entry_run, exit_run, inter, cur_start, (float(ax), float(ay)))
                pts.append(p)
                fis.append(cur_fi)
                links.append(ref)
                dirs.append(d)
                cur_start = (float(bx), float(by))
                cur_fi = bfi
                seg_strips = [v]
                entry_run = [m.locate(bfi, float(bx), float(by))]
                exit_run = []
                inter = []
        exit_run.append(r1)
        p = self._funnel(seg_strips, entry_run, exit_run, inter, cur_start, (gx, gy))
        pts.append(p)
        fis.append(cur_fi)
        all_p, all_f, seg_link, seg_dir = [], [], [], []
        for k in range(len(pts)):
            if k > 0:
                seg_link.append(np.asarray([links[k - 1]], np.int32))
                seg_dir.append(np.asarray([dirs[k - 1]], np.int8))
            all_p.append(pts[k])
            all_f.append(np.full(pts[k].shape[0], fis[k], np.int8))
            seg_link.append(np.full(pts[k].shape[0] - 1, -1, np.int32))
            seg_dir.append(np.zeros(pts[k].shape[0] - 1, np.int8))
        P = np.concatenate(all_p)
        F = np.concatenate(all_f)
        SL = np.concatenate(seg_link) if seg_link else np.zeros(0, np.int32)
        SD = np.concatenate(seg_dir) if seg_dir else np.zeros(0, np.int8)
        ckv, ckn = [], []
        j = 0
        for nd in nodes:
            ax_, ay_ = self.anchor_xy[nd]
            dd = np.hypot(P[j:, 0] - ax_, P[j:, 1] - ay_)
            q = j + int(np.argmin(dd))
            ckv.append(q)
            ckn.append(nd)
            j = q
        return RouteGeom(pts=P, fi=F, seg_link=SL, seg_dir=SD, ck_vertex=np.asarray(ckv, np.int64),
                         ck_node=np.asarray(ckn, np.int64), w1_path=np.asarray(nodes, np.int64), mode=int(mode),
                         expanded=int(n_exp))

    def _funnel(self, seg_strips, entry_run, exit_run, inter, start, goal) -> np.ndarray:
        m = self.mesh
        n = len(seg_strips)
        iy = np.asarray([t[0] for t in inter] + [0.0], dtype=np.float64)
        ix0 = np.asarray([t[1] for t in inter] + [0.0], dtype=np.float64)
        ix1 = np.asarray([t[2] for t in inter] + [0.0], dtype=np.float64)
        need = 8 + n + int(sum(int(m.strip_run_ptr[s + 1] - m.strip_run_ptr[s]) for s in seg_strips))
        if need > self.lx.size:
            self._alloc(1 << int(math.ceil(math.log2(need))))
        k = corridor_portals(np.asarray(seg_strips, np.int64), np.asarray(entry_run, np.int64),
                             np.asarray(exit_run, np.int64), n, m.strip_run_ptr, m.strip_runs, m.run_row, m.run_x0,
                             m.run_x1, m.run_floor, m.floor_ox, m.floor_oy, m.res, iy, ix0, ix1, self.lx, self.ly,
                             self.rx, self.ry)
        c = funnel_points(self.lx, self.ly, self.rx, self.ry, int(k), float(start[0]), float(start[1]),
                          float(goal[0]), float(goal[1]), self.out_buf)
        return self.out_buf[:c].copy()
