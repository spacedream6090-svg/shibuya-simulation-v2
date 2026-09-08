# -*- coding: utf-8 -*-
"""crowd_physics_bench.py — 群衆物理(社会力モデル型)の1ステップを40万体・CPU(numba並列)で計測するスパイク。
配置: 6.93km²相当の領域に、30%の個体を面積5%の「混雑地区」に集中(渋谷駅周辺のピーク相当)。
近傍探索=一様格子(2m)。各個体は半径2m内の近傍から反発力(指数)を受け、目標速度へ緩和。
計測: 1ステップの実時間 → dt=1.0/0.5/0.1秒で1シミュ日(86,400秒)へ外挿。
物理対象をLOD(混雑セルのみ)に絞った場合(対象10%)も計測。
"""
import argparse, time, json
import numpy as np
from numba import njit, prange

ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, default=400_000)
ap.add_argument("--steps", type=int, default=10)
ap.add_argument("--seed", type=int, default=7)
a = ap.parse_args()
rng = np.random.default_rng(a.seed)
N = a.n
L = 2632.0  # 6.93 km² の正方形辺長(m)
# 配置: 70%一様・30%を中心の5%面積(辺長 L*sqrt(0.05)) に集中
pos = rng.random((N, 2), dtype=np.float32) * L
n_scr = int(N * 0.02); n_mid = int(N * 0.10)
pos[:n_scr] = L / 2 - 30 + rng.random((n_scr, 2), dtype=np.float32) * 60          # スクランブル級 2.2人/m²
pos[n_scr:n_scr + n_mid] = L / 2 - 150 + rng.random((n_mid, 2), dtype=np.float32) * 300  # 駅周辺 0.44人/m²
vel = (rng.random((N, 2), dtype=np.float32) - 0.5) * 1.0
goal = (rng.random((N, 2), dtype=np.float32) - 0.5)
goal /= (np.linalg.norm(goal, axis=1, keepdims=True) + 1e-6)
CELL = 2.0
G = int(np.ceil(L / CELL)); L = CELL * G

@njit
def build_grid(pos, cell, G):
    n = pos.shape[0]
    L = cell * G
    keys = np.empty(n, np.int64)
    counts = np.zeros(G * G + 1, np.int64)
    for i in range(n):
        # 周期境界(ベンチ用・端への堆積を防ぐ)
        x = pos[i, 0] % L; y = pos[i, 1] % L
        if not (x >= 0 and x < L): x = 0.0
        if not (y >= 0 and y < L): y = 0.0
        pos[i, 0] = x; pos[i, 1] = y
        gx = int(x / cell); gy = int(y / cell)
        if gx >= G: gx = G - 1
        if gy >= G: gy = G - 1
        k = gx * G + gy
        keys[i] = k; counts[k + 1] += 1
    starts = np.cumsum(counts)
    fill = starts[:-1].copy()
    order = np.empty(n, np.int64)
    for i in range(n):
        k = keys[i]; order[fill[k]] = i; fill[k] += 1
    return order, starts

@njit(parallel=True)
def sfm_step(pos, vel, goal, order, starts, cell, G, dt, v0, tau, A, B, r):
    n = pos.shape[0]
    newv = np.empty_like(vel)
    for i in prange(n):
        fx = (v0 * goal[i, 0] - vel[i, 0]) / tau
        fy = (v0 * goal[i, 1] - vel[i, 1]) / tau
        gx = int(pos[i, 0] / cell); gy = int(pos[i, 1] / cell)
        for dx in range(-1, 2):
            cx = gx + dx
            if cx < 0 or cx >= G: continue
            for dy in range(-1, 2):
                cy = gy + dy
                if cy < 0 or cy >= G: continue
                k = cx * G + cy
                for p in range(starts[k], starts[k + 1]):
                    j = order[p]
                    if j == i: continue
                    ddx = pos[i, 0] - pos[j, 0]; ddy = pos[i, 1] - pos[j, 1]
                    d2 = ddx * ddx + ddy * ddy
                    if d2 < 4.0 and d2 > 1e-6:
                        d = np.sqrt(d2)
                        f = A * np.exp((2 * r - d) / B)
                        if f > 50.0: f = 50.0
                        fx += f * ddx / d; fy += f * ddy / d
        vx = vel[i, 0] + fx * dt; vy = vel[i, 1] + fy * dt
        sp = np.sqrt(vx * vx + vy * vy)
        if sp > 3.0:
            vx = vx * 3.0 / sp; vy = vy * 3.0 / sp
        newv[i, 0] = vx; newv[i, 1] = vy
    for i in prange(n):
        vel[i, 0] = newv[i, 0]; vel[i, 1] = newv[i, 1]
        pos[i, 0] += vel[i, 0] * dt; pos[i, 1] += vel[i, 1] * dt

def run(pos, vel, goal, steps, dt):
    # warm-up
    order, starts = build_grid(pos, CELL, G)
    sfm_step(pos, vel, goal, order, starts, CELL, G, dt, 1.34, 0.5, 2000.0, 0.08, 0.3)
    t_grid = 0.0; t_step = 0.0
    for s in range(steps):
        t0 = time.perf_counter(); order, starts = build_grid(pos, CELL, G); t1 = time.perf_counter()
        sfm_step(pos, vel, goal, order, starts, CELL, G, dt, 1.34, 0.5, 2000.0, 0.08, 0.3); t2 = time.perf_counter()
        t_grid += t1 - t0; t_step += t2 - t1
    return t_grid / steps, t_step / steps

res = {}
for label, sel in (("all_400k", slice(None)), ("lod_12pct_dense_only", slice(0, int(N * 0.12)))):
    p = pos[sel].copy(); v = vel[sel].copy(); g = goal[sel].copy()
    tg, ts = run(p, v, g, a.steps, 0.5)
    per_step = tg + ts
    # 近傍数の目安
    order, starts = build_grid(p, CELL, G)
    counts = np.diff(starts); occ = counts[counts > 0]
    res[label] = {"n": int(p.shape[0]), "s_per_step": round(per_step, 4), "grid_s": round(tg, 4), "force_s": round(ts, 4),
                  "mean_per_occupied_cell(2m)": round(float(occ.mean()), 2), "max_per_cell": int(occ.max()),
                  "hours_per_simday": {f"dt={dt}s": round(per_step * (86400 / dt) / 3600, 2) for dt in (1.0, 0.5, 0.1)}}
print(json.dumps(res, ensure_ascii=False, indent=1))
