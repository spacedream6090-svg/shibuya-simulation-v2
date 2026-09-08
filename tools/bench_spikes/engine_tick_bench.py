# -*- coding: utf-8 -*-
"""engine_tick_bench.py — v2エンジンの1tick処理を40万体規模で模した計測(設計判断用スパイク・シム本体ではない)。
設計(知覚契約書/行動契約書/認知設計書/実装スタック答申)に沿った代表段階を、Python+NumPy(+numba任意)で実装し、
段階ごとの実時間を計測して1シミュ日(1,440tick)へ外挿する。LLM呼び出しはしない(観測レンダリングと出力パースのみ再現)。
"""
import argparse, time, os, sys, hashlib, re, json
import numpy as np
try:
    if os.environ.get("NO_NUMBA"): raise ImportError("disabled")
    import numba
    from numba import njit, prange
    HAVE_NUMBA = True
except Exception:
    HAVE_NUMBA = False
try:
    import xxhash
    def h64(b): return xxhash.xxh3_64_intdigest(b)
except Exception:
    def h64(b): return int.from_bytes(hashlib.blake2b(b, digest_size=8).digest(), "little")

ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, default=400_000)
ap.add_argument("--cells", type=int, default=453)
ap.add_argument("--ticks", type=int, default=60)
ap.add_argument("--calls-per-day", type=int, default=4_000_000)
ap.add_argument("--events-per-tick", type=int, default=200)
ap.add_argument("--seed", type=int, default=20260907)
a = ap.parse_args()
rng = np.random.default_rng(a.seed)
N, C, T = a.n, a.cells, a.ticks
wake_rate = a.calls_per_day / 1440 / N  # 期待起床率/体/tick

# ---- SoA 状態 ----
cell = rng.integers(0, C, N).astype(np.int32)
hunger = rng.random(N, dtype=np.float32) * 6
stamina = rng.random(N, dtype=np.float32) * 10
temp = rng.random(N, dtype=np.float32) * 10
money = (rng.random(N, dtype=np.float32) * 20000 + 1000).astype(np.float32)
in_transit = np.zeros(N, dtype=np.bool_)
remain_min = np.zeros(N, dtype=np.int16)
dest = cell.copy()
plan_end_tick = rng.integers(0, 1440, N).astype(np.int32)
last_cell_hash_seen = np.zeros(N, dtype=np.uint64)
persona_age = rng.integers(15, 80, N).astype(np.int16)
persona_sex = rng.integers(0, 2, N).astype(np.int8)
kind = rng.integers(0, 6, N).astype(np.int8)
shop_balance = np.zeros(C * 5, dtype=np.float64)  # 店舗(セル×5)の売上残高
total0 = float(money.astype(np.float64).sum() + shop_balance.sum())
cell_xy = rng.random((C, 2), dtype=np.float32) * 2000
KIND = ["住民", "通勤者", "来街者", "従業者", "乗務員", "指令"]
DENS = ["段階A", "段階B", "段階C", "段階D", "段階E", "段階F"]
ACTIONS = ["移動", "購入", "待機", "会話", "退去", "通報", "手伝い", "断る", "休憩", "就寝"]

if HAVE_NUMBA:
    @njit(parallel=True, cache=True)
    def k_needs(hunger, stamina, temp, in_transit):
        for i in prange(hunger.shape[0]):
            hunger[i] = min(hunger[i] + 0.004, 10.0)
            if in_transit[i]:
                stamina[i] = max(stamina[i] - 0.01, 0.0)
            else:
                stamina[i] = min(stamina[i] + 0.002, 10.0)
    @njit(parallel=True, cache=True)
    def k_move(in_transit, remain_min, cell, dest):
        for i in prange(cell.shape[0]):
            if in_transit[i]:
                remain_min[i] -= 1
                if remain_min[i] <= 0:
                    cell[i] = dest[i]; in_transit[i] = False

def needs_np():
    np.minimum(hunger + np.float32(0.004), 10, out=hunger)
    st = np.where(in_transit, stamina - np.float32(0.01), stamina + np.float32(0.002))
    np.clip(st, 0, 10, out=stamina)

def move_np():
    m = in_transit
    remain_min[m] -= 1
    arr = m & (remain_min <= 0)
    cell[arr] = dest[arr]; in_transit[arr] = False

# 出力パース(2行形・ラベル基準)
LAB = re.compile(r"(?:^|\s)(理由|行動|対象|ひと言)\s*[:：]\s*")
def parse2(text):
    parts = LAB.split(text)
    f = {}
    for i in range(1, len(parts) - 1, 2): f[parts[i]] = parts[i + 1].strip()
    act = f.get("行動", "")
    for j, v in enumerate(ACTIONS):
        if act.startswith(v): return j, f.get("対象", "なし")
    return 2, "なし"

SAMPLE_OUT = ["理由: 空腹なので食事をとりたい。\n行動: 購入 対象: 定食店A ひと言: 定食ください",
              "理由: 予定の時刻が近い。\n行動: 移動 対象: C-0117 ひと言: なし",
              "理由: 少し疲れた。\n行動: 休憩 対象: なし ひと言: なし"]

def render_individual(i, dens_stage, noise_stage, wake_reason):
    # B5/B6 個体部(契約書v1・正規化規約: 段階語彙・固定順序)
    return ("[B1 種別] あなたは%sです。年代は%d代、性別は%sです。\n"
            "[B4 密度] 歩行者密度は%sです。\n[B4 騒音] 環境騒音は%sです。\n"
            "[B5 内受容] 空腹は%dです。体力は%dです。体感温度は%dです。\n"
            "[B5 所持] 所持金は%s円です。手はふさがっていません。\n"
            "[B5 近接] 近くの人物: P-%d(未知)、P-%d(未知)、P-%d(未知)。\n"
            "[B6 起床] %s\n[B6 直前の結果] 直前の行動は成功しました。いま可能: 移動 購入 待機\n"
            "[B6 問い] 今から何をしますか。") % (
        KIND[kind[i]], (persona_age[i] // 10) * 10, "男性" if persona_sex[i] == 0 else "女性",
        DENS[dens_stage], noise_stage, int(hunger[i]), int(stamina[i]), int(temp[i]),
        f"{int(money[i]):,}", (i * 7) % 900 + 100, (i * 11) % 900 + 100, (i * 13) % 900 + 100, wake_reason)

stages = {k: 0.0 for k in ["needs", "move", "density", "cell_hash", "wake", "arbiter", "render", "parse", "resolve", "conserve", "p_notice"]}
n_wakes = 0; n_render = 0; n_events = 0
prev_hash = np.zeros(C, dtype=np.uint64)
t_all = time.perf_counter()
for t in range(T):
    t0 = time.perf_counter()
    if HAVE_NUMBA: k_needs(hunger, stamina, temp, in_transit)
    else: needs_np()
    t1 = time.perf_counter(); stages["needs"] += t1 - t0
    if HAVE_NUMBA: k_move(in_transit, remain_min, cell, dest)
    else: move_np()
    t2 = time.perf_counter(); stages["move"] += t2 - t1
    dens = np.bincount(cell, minlength=C)
    dens_stage = np.minimum(dens // 400, 5).astype(np.int8)  # LOS段階(仮)
    t3 = time.perf_counter(); stages["density"] += t3 - t2
    # セル動的ブロックのハッシュ(139-453回のPythonループ=宣言済み)
    cur_hash = np.empty(C, dtype=np.uint64)
    for c in range(C):
        cur_hash[c] = h64(b"%d|%d|%d" % (c, dens_stage[c], (t // 60) % 4))
    changed_cell = cur_hash != prev_hash; prev_hash = cur_hash
    t4 = time.perf_counter(); stages["cell_hash"] += t4 - t3
    # 起床判定: 計画境界 | 内受容閾値 | セル変化(不応期は簡略)
    wake = (plan_end_tick == (t % 1440)) | (hunger > 8.0) | changed_cell[cell]
    # 期待起床率に合わせる(ハッシュ変化の暴発を不応期で抑えた状態を模す)
    rnd = rng.random(N) < wake_rate
    wake = rnd | (plan_end_tick == (t % 1440))
    idx = np.flatnonzero(wake)
    t5 = time.perf_counter(); stages["wake"] += t5 - t4
    # アービタ: 4クラス固定優先+ハッシュ優先度でソート(上限=in-flight 448×tick内処理は全件)
    cls = (idx % 4).astype(np.int8)
    pk = (idx.astype(np.uint64) * np.uint64(0x9E3779B97F4A7C15)) ^ np.uint64(t)
    order = np.lexsort((pk, cls)); idx = idx[order]
    t6 = time.perf_counter(); stages["arbiter"] += t6 - t5
    # 観測レンダリング(個体部)+prefixキー
    keys = []
    for i in idx:
        s = render_individual(int(i), int(dens_stage[cell[i]]), "60デシベル帯", "直前の行動(移動)が終わったため、次の行動を決める必要があります。")
        keys.append(h64(s.encode("utf-8")))
    n_render += len(idx)
    t7 = time.perf_counter(); stages["render"] += t7 - t6
    # 出力パース
    acts = np.empty(len(idx), dtype=np.int8)
    for k, i in enumerate(idx):
        acts[k], _ = parse2(SAMPLE_OUT[int(i) % 3])
    t8 = time.perf_counter(); stages["parse"] += t8 - t7
    # resolve(二相の commit 相当): 購入=transfer(保存則)・移動=transit開始・休憩=体力回復
    buy = idx[acts == 1]; price = (rng.random(len(buy)) * 1500 + 300).astype(np.float32)
    ok = money[buy] >= price; buy = buy[ok]; price = price[ok]
    money[buy] -= price
    np.add.at(shop_balance, (cell[buy] * 5 + (buy % 5)), price.astype(np.float64))
    hunger[buy] = np.maximum(hunger[buy] - 5, 0)
    mv = idx[acts == 0]; dest[mv] = rng.integers(0, C, len(mv)); in_transit[mv] = True
    remain_min[mv] = rng.integers(3, 25, len(mv)).astype(np.int16)
    rest = idx[acts == 8]; stamina[rest] = np.minimum(stamina[rest] + 2, 10)
    plan_end_tick[idx] = (t + rng.integers(15, 240, len(idx))) % 1440
    t9 = time.perf_counter(); stages["resolve"] += t9 - t8
    # 保存則検査(純資産合計=不変)
    total = float(money.astype(np.float64).sum() + shop_balance.sum())
    assert abs(total - total0) < 1.0, (total, total0)
    t10 = time.perf_counter(); stages["conserve"] += t10 - t9
    # p_notice: 200イベント/tick × 近傍(±1リング≈9セル・約2.6万体)へ距離→LUT→ベルヌーイ
    # セル索引(tickごとに1回: 個体をセル順に整列=空間チャンク化の代替)
    order_c = np.argsort(cell, kind="stable"); cell_sorted = cell[order_c]
    starts = np.searchsorted(cell_sorted, np.arange(C + 1))
    ev_cells = rng.integers(0, C, a.events_per_tick)
    with np.errstate(over="ignore", invalid="ignore"):
        for ec in ev_cells:
            lo, hi = starts[max(ec - 4, 0)], starts[min(ec + 5, C)]   # ±4セル分の連続区間(≈9セル近傍)
            nb = order_c[lo:hi]
            d = np.abs(cell_xy[cell[nb], 0] - cell_xy[ec, 0]) + np.abs(cell_xy[cell[nb], 1] - cell_xy[ec, 1]) + 1.0
            s = np.minimum(40.0 / d, 8.0); P = s ** (2.7 + 0.7 * s); P = P / (1 + P)
            hit = rng.random(len(nb)) < P
            n_events += 1
    t11 = time.perf_counter(); stages["p_notice"] += t11 - t10
    n_wakes += len(idx)
elapsed = time.perf_counter() - t_all
per_tick = elapsed / T
print(json.dumps({"numba": HAVE_NUMBA, "N": N, "cells": C, "ticks": T, "wakes_total": n_wakes, "wakes_per_tick": n_wakes / T,
                  "elapsed_s": round(elapsed, 3), "s_per_tick": round(per_tick, 4), "extrap_min_per_simday": round(per_tick * 1440 / 60, 1),
                  "stage_s_per_tick": {k: round(v / T, 5) for k, v in stages.items()},
                  "stage_share": {k: round(v / elapsed, 3) for k, v in stages.items()}}, ensure_ascii=False, indent=1))
