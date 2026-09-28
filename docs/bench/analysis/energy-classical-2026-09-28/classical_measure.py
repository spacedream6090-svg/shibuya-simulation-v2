"""5 段目 5b(System 1.5=古典的選択モデル・D-119 L1〜L8)の計測。

使い方(リポジトリの根から)::

    python docs/bench/analysis/energy-classical-2026-09-28/classical_measure.py arms \\
        --world data/world/v2 --out docs/bench/analysis/energy-classical-2026-09-28/classical_arms.json

腕(mock 5,000 体・seed 1・語彙 v3・空腹 energy=CLI の既定)は :data:`ARMS`。1 腕=1 子プロセスで回し、
壁時計とピークの作業セット(Windows ``K32GetProcessMemoryInfo``)を別の JSON(``classical_perf.json``)に
分ける(決定論でない)。

計器(本スクリプトの中だけ・エンジンの挙動は変えない):
- **軌跡**: ``resolve.advance_body`` を包んで 10 tick ごとに体のセル・活動の種別・域外を控える。
- **訪問**: ``resolve.apply`` を ``track_visits=True`` で呼んで成立した購入/食事の (体, POI) を集める
  (控えるだけ=世界は変えない。親しみの表の無いランでは誰も読まない)。
- **LLMob 4 指標の簡易版**(宣言・問い): SD=連続する 2 つの在圏セルの距離(W3 ``cell_dist``)の分布・
  SI=セルが変わる間隔の分布・DARD=活動の種別 × 時の分布・STVD=セル × 時の在圏の分布。現実の軌跡が
  無いので **腕どうしの JSD**(基準=mock v3)だけを出す(LLMob は現実との JSD)。
- **店の集中**(D-120 と同じ物差し): cat ごとに POI の訪問数の Gini(訪問 0 の店を含む)・上位 10 店の
  占有率・HHI。
- 5a と同じ形: 食事開始の 15 分分布(範囲内)× 錨 3 本・朝食欠食率・語の段の時間・起床入口・跨ぎ。

絶対パスは書かない。
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
ANCHORS = HERE.parents[1] / "anchors" / "hunger_energy_anchors_v0.json"
ENGINE_CONTINUE = "(エンジン継続)"
ENTRANCES: dict[str, tuple[str, ...]] = {
    "場所": ("CELL_BLOCK",),
    "体": ("INTEROCEPTION",),
    "日課": ("PLAN_SLEEPING", "PLAN_WORKING", "PLAN_GENERAL", "PLAN_TRANSIT"),
    "会話": ("CONVERSATION_TURN",),
    "満了": ("ACTIVITY_EXPIRY",),
    "社会": ("ACQUAINTANCE", "PROXIMITY_SWAP", "BEING_WATCHED", "OVERHEARD"),
}
BASE = {"vocab_version": "v3"}
ARMS: dict[str, dict[str, Any]] = {
    "mock_v3": {},
    "mock_v3_chooser_classical": {"chooser": "classical"},
    "classical": {"policy": "classical", "chooser": "classical"},
    "classical_familiarity": {"policy": "classical", "chooser": "classical", "familiarity": "on"},
    "classical_hunger_v1": {"policy": "classical", "chooser": "classical", "hunger_model": "v1"},
    "classical_tau_0_5": {"policy": "classical", "chooser": "classical", "classical_tau": 0.5},
    "classical_tau_2_0": {"policy": "classical", "chooser": "classical", "classical_tau": 2.0},
    "classical_familiarity_ph_0_25": {"policy": "classical", "chooser": "classical",
                                      "familiarity": "on", "classical_habit_p": 0.25},
    "classical_familiarity_ph_0_75": {"policy": "classical", "chooser": "classical",
                                      "familiarity": "on", "classical_habit_p": 0.75},
    "classical_national": {"policy": "classical", "chooser": "classical",
                           "activity_region": "national"},
}
SAMPLE_EVERY = 10
CATS = ("sleep", "move", "wander", "in_shop", "in_place", "talk", "riding", "away")
SD_BINS_M = (0, 50, 100, 200, 400, 800, 1600)
SI_BINS_MIN = (10, 20, 30, 60, 120, 240, 480)


def _peak_working_set_bytes() -> int:
    try:
        import ctypes
        import ctypes.wintypes as wt

        class PMC(ctypes.Structure):
            _fields_ = [("cb", wt.DWORD), ("PageFaultCount", wt.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]

        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.GetCurrentProcess.restype = wt.HANDLE
        f = k32.K32GetProcessMemoryInfo
        f.argtypes = [wt.HANDLE, ctypes.POINTER(PMC), wt.DWORD]
        f.restype = wt.BOOL
        pmc = PMC()
        pmc.cb = ctypes.sizeof(PMC)
        if not f(k32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb):
            return -1
        return int(pmc.PeakWorkingSetSize)
    except Exception:  # noqa: BLE001
        return -1


def _gini(x: np.ndarray) -> float:
    v = np.sort(np.asarray(x, dtype=np.float64))
    n = v.size
    if n == 0 or v.sum() <= 0:
        return 0.0
    cum = np.cumsum(v)
    return float((n + 1 - 2 * (cum / cum[-1]).sum()) / n)


def _concentration(visits: np.ndarray, cats: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    carr = np.asarray(cats)
    for c in ("food", "shop", "all"):
        v = visits if c == "all" else visits[carr == c]
        tot = int(v.sum())
        top = np.sort(v)[::-1][:10]
        out[c] = {"n_poi": int(v.size), "visits": tot, "poi_visited": int(np.count_nonzero(v)),
                  "gini": round(_gini(v), 4),
                  "top10_share": round(float(top.sum()) / tot, 4) if tot else 0.0,
                  "hhi": round(float(((v / tot) ** 2).sum()), 5) if tot else 0.0}
    return out


# ------------------------------------------------------------------ 1 腕(子プロセス)
def cmd_one(args: argparse.Namespace) -> int:
    from shibuya import cli
    from shibuya.agents.state import Activity, ActivityKind
    from shibuya.engine import resolve as R

    kw = {**BASE, **ARMS[args.arm]}
    samples: list[tuple[np.ndarray, np.ndarray, np.ndarray]] = []
    visit_pois: list[np.ndarray] = []
    orig_body = R.advance_body
    orig_apply = R.apply

    def body(agents: Any, tick: int, energy: Any = None) -> None:
        if int(tick) % SAMPLE_EVERY == 0:
            r = agents.registry
            act = np.asarray(r.activity)
            ts = np.asarray(r.transit_state)
            cat = np.full(act.size, CATS.index("in_place"), dtype=np.int8)
            cat[np.asarray(r.poi_ref) >= 0] = CATS.index("in_shop")
            cat[act == int(Activity.SHOPPING)] = CATS.index("in_shop")
            cat[act == int(Activity.CONVERSING)] = CATS.index("talk")
            mv = act == int(Activity.MOVING)
            cat[mv] = CATS.index("move")
            if "activity_kind" in r.arrays:
                cat[mv & (np.asarray(r.activity_kind) == int(ActivityKind.WANDER))] = CATS.index("wander")
            cat[act == int(Activity.SLEEPING)] = CATS.index("sleep")
            cat[ts == 1] = CATS.index("riding")
            cat[ts == 2] = CATS.index("away")
            cell = np.where(ts == 0, np.asarray(r.cell), -1).astype(np.int32)
            samples.append((cell, cat, (ts == 0) & (act != int(Activity.SLEEPING))))
        orig_body(agents, tick, energy)

    def apply(*a: Any, **k: Any) -> Any:
        k["track_visits"] = True
        out = orig_apply(*a, **k)
        visit_pois.extend(np.asarray(p, dtype=np.int64) for p in out.visit_pois)
        return out

    R.advance_body = body  # type: ignore[assignment]
    R.apply = apply  # type: ignore[assignment]
    t0 = time.perf_counter()
    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, **kw)
    wall = time.perf_counter() - t0
    R.advance_body = orig_body  # type: ignore[assignment]
    R.apply = orig_apply  # type: ignore[assignment]

    from shibuya.world.state import World

    world = World.load_or_synthetic(Path(args.world), n_cells=139, seed=args.seed)
    cell_dist = np.asarray(world.assets.cell_dist, dtype=np.float64)
    cells = np.stack([s[0] for s in samples])      # (T, n)
    cats = np.stack([s[1] for s in samples])
    awake_in = np.stack([s[2] for s in samples])
    t_n, n = cells.shape
    hour = (np.arange(t_n) * SAMPLE_EVERY // 60) % 24
    # SD / SI: 在圏セルの変化(域外・乗車の間はつながない)
    sd = np.zeros(len(SD_BINS_M), dtype=np.int64)
    si = np.zeros(len(SI_BINS_MIN), dtype=np.int64)
    prev = cells[:-1]
    nxt = cells[1:]
    ch = (prev >= 0) & (nxt >= 0) & (prev != nxt)
    ti, ai = np.nonzero(ch)
    d = cell_dist[prev[ti, ai], nxt[ti, ai]]
    sd += np.bincount(np.searchsorted(SD_BINS_M, d, side="right") - 1, minlength=len(SD_BINS_M))[:len(SD_BINS_M)]
    order = np.lexsort((ti, ai))
    ai_s, ti_s = ai[order], ti[order]
    same = ai_s[1:] == ai_s[:-1]
    gap_min = (ti_s[1:] - ti_s[:-1])[same] * SAMPLE_EVERY
    si += np.bincount(np.searchsorted(SI_BINS_MIN, gap_min, side="right") - 1,
                      minlength=len(SI_BINS_MIN))[:len(SI_BINS_MIN)]
    dard = np.zeros((len(CATS), 24), dtype=np.int64)
    np.add.at(dard, (cats.ravel().astype(np.int64), np.repeat(hour, n)), 1)
    stvd = np.zeros((world.n_cells, 24), dtype=np.int64)
    ok = cells >= 0
    np.add.at(stvd, (cells[ok].astype(np.int64), np.repeat(hour, n).reshape(t_n, n)[ok]), 1)
    presence = [float(np.mean([(cells[t] >= 0).sum() for t in np.flatnonzero(hour == h)]))
                for h in range(24)]
    awake_presence = [float(np.mean([awake_in[t].sum() for t in np.flatnonzero(hour == h)]))
                      for h in range(24)]
    visits = np.bincount(np.concatenate(visit_pois) if visit_pois else np.zeros(0, dtype=np.int64),
                         minlength=world.n_poi)
    cbc = dict(res.calls_by_condition)
    au = {k: v for k, v in res.action_usage.items() if k != ENGINE_CONTINUE}
    m = res.run_manifest_fields()
    e = dict(res.energy)
    out = {
        "arm": args.arm, "args": kw, "final_hash": res.final_hash,
        "llm_calls": int(res.llm_calls),
        "calls_by_entrance": {k: int(sum(cbc.get(c, 0) for c in v)) for k, v in ENTRANCES.items()},
        "action_usage_llm": au,
        "purchases": int(res.column("purchases").sum()), "meals_in_area": int(res.meals),
        "decision_layers": {k: m["decision_layers"][k] for k in ("totals", "share", "by_entrance")},
        "decision_layers_by_hour": [
            {k: row[k] for k in ("system1", "system1_5", "system2")}
            for row in m["decision_layers"]["by_hour"]
        ],
        "classical": m["classical"], "chooser_stats": m["chooser_stats"],
        "target_resolution": m.get("target_resolution", {}),
        "conversation_counters": dict(res.conversation_counters),
        "intero_crossings": dict(res.intero_crossings),
        "energy": {k: e[k] for k in ("counts", "census_per_agent", "stage_time_share", "breakfast_skip",
                                     "meals_per_agent", "meal_start_in_15min", "meal_start_out_15min",
                                     "balance_kcal_by_meals") if k in e},
        "hunger_model": str(res.hunger_model),
        "llmob": {"sd_bins_m": list(SD_BINS_M), "sd": sd.tolist(), "si_bins_min": list(SI_BINS_MIN),
                  "si": si.tolist(), "dard_cats": list(CATS), "dard": dard.tolist(),
                  "stvd": stvd.tolist()},
        "presence_by_hour": [round(x, 1) for x in presence],
        "awake_in_area_by_hour": [round(x, 1) for x in awake_presence],
        "concentration": _concentration(visits, [str(c) for c in world.assets.poi_cat]),
        "conserved": bool(res.conserved),
        "_wall_seconds_nondeterministic": round(wall, 2),
        "_peak_working_set_bytes_nondeterministic": _peak_working_set_bytes(),
        "_agents_bytes_total": int(res.agents.bytes_total()),  # type: ignore[attr-defined]
    }
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return 0


# ------------------------------------------------------------------ 腕を束ねる
def _norm(v: Any) -> np.ndarray:
    a = np.asarray([0.0 if x is None else x for x in np.asarray(v, dtype=object).ravel()],
                   dtype=np.float64)
    s = a.sum()
    return a / s if s > 0 else a


def _jsd(p: np.ndarray, q: np.ndarray) -> float:
    out = 0.0
    for a, b in zip(p, q):
        m = 0.5 * (a + b)
        if a > 0:
            out += 0.5 * a * math.log2(a / m)
        if b > 0:
            out += 0.5 * b * math.log2(b / m)
    return out


def _tvd(p: np.ndarray, q: np.ndarray) -> float:
    return float(0.5 * np.abs(p - q).sum())


def _window_peaks(p: np.ndarray) -> dict[str, str]:
    out = {}
    for name, lo, hi in (("breakfast", 20, 44), ("lunch", 44, 64), ("dinner", 68, 96)):
        i = max(range(lo, hi), key=lambda j: (p[j], -j))
        out[name] = f"{i * 15 // 60:02d}:{i * 15 % 60:02d}"
    return out


def cmd_arms(args: argparse.Namespace) -> int:
    tmp = Path(args.tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    for arm in ARMS:
        path = tmp / f"{arm}.json"
        cmd = [sys.executable, str(Path(__file__)), "one", "--arm", arm, "--world", args.world,
               "--agents", str(args.agents), "--seed", str(args.seed), "--out", str(path)]
        subprocess.run(cmd, check=True)
        r = json.loads(path.read_text(encoding="utf-8"))
        print(f"{arm}: final {r['final_hash'][:8]} calls {r['llm_calls']:,} wall "
              f"{r['_wall_seconds_nondeterministic']}s", flush=True)
    return cmd_collect(args)


def cmd_collect(args: argparse.Namespace) -> int:
    """腕ごとの中間 JSON(``--tmp``)を束ねる(腕は回さない)。"""
    tmp = Path(args.tmp)
    rows = {arm: json.loads((tmp / f"{arm}.json").read_text(encoding="utf-8")) for arm in ARMS}
    anc = json.loads(ANCHORS.read_text(encoding="utf-8"))
    ref = {k: _norm(v["rate_pct"]) for k, v in anc["ssb2021_meal_rate_15min"]["series"].items()}
    base = rows["mock_v3"]
    summary = []
    for arm, r in rows.items():
        ll, bl = r["llmob"], base["llmob"]
        meal = _norm(r["energy"].get("meal_start_in_15min", [0] * 96))
        summary.append({
            "arm": arm, "args": r["args"], "final_hash": r["final_hash"], "llm_calls": r["llm_calls"],
            "calls_by_entrance": r["calls_by_entrance"],
            "decision_layers_share": r["decision_layers"]["share"],
            "llmob_jsd_vs_mock_v3": {
                "SD": round(_jsd(_norm(ll["sd"]), _norm(bl["sd"])), 4),
                "SI": round(_jsd(_norm(ll["si"]), _norm(bl["si"])), 4),
                "DARD": round(_jsd(_norm(ll["dard"]), _norm(bl["dard"])), 4),
                "STVD": round(_jsd(_norm(ll["stvd"]), _norm(bl["stvd"])), 4),
                "DARD_in_area": round(_jsd(_norm(np.asarray(ll["dard"])[:6]),
                                           _norm(np.asarray(bl["dard"])[:6])), 4),
            },
            "dard_share_by_cat": dict(zip(ll["dard_cats"],
                                          [round(float(x), 4) for x in _norm(np.asarray(ll["dard"]).sum(axis=1))])),
            "sd_share": [round(float(x), 4) for x in _norm(ll["sd"])],
            "si_share": [round(float(x), 4) for x in _norm(ll["si"])],
            "meal_start_in_area": {
                "n": int(sum(r["energy"].get("meal_start_in_15min", []))),
                "window_peaks": _window_peaks(meal) if meal.sum() > 0 else {},
                "tvd": {k: round(_tvd(meal, v), 4) for k, v in ref.items()} if meal.sum() > 0 else {},
                "jsd_bits": {k: round(_jsd(meal, v), 4) for k, v in ref.items()} if meal.sum() > 0 else {},
            },
            "energy": {k: r["energy"][k] for k in ("counts", "census_per_agent", "stage_time_share",
                                                   "breakfast_skip", "meals_per_agent") if k in r["energy"]},
            "purchases": r["purchases"], "meals_in_area": r["meals_in_area"],
            "action_usage_llm": r["action_usage_llm"],
            "presence_by_hour": r["presence_by_hour"],
            "awake_in_area_by_hour": r["awake_in_area_by_hour"],
            "concentration": r["concentration"],
            "chooser_stats": r["chooser_stats"],
            "chooser_entropy_mean_bits": r["target_resolution"].get("chooser_entropy_mean_bits"),
            "classical_counts": r["classical"].get("counts", {}),
            "decision_layers_by_hour": r["decision_layers_by_hour"],
            "intero_crossings": r["intero_crossings"],
            "conversations_opened": int(r["conversation_counters"].get("sessions_opened", 0)),
            "conserved": r["conserved"],
        })
    floor = {"national_vs_tokyo": round(_tvd(ref["t8_1_weekday_national_total"],
                                             ref["t7_1_weekday_tokyo_total"]), 4),
             "national_vs_kanto": round(_tvd(ref["t8_1_weekday_national_total"],
                                             ref["t8_1_weekday_kanto_total"]), 4),
             "kanto_vs_tokyo": round(_tvd(ref["t8_1_weekday_kanto_total"],
                                          ref["t7_1_weekday_tokyo_total"]), 4)}
    doc = {"schema": "shibuya.bench/classical-2026-09-28/arms/1", "n_agents": args.agents,
           "seed": args.seed, "sample_every_ticks": SAMPLE_EVERY, "meal_tvd_floor": floor,
           "arms": summary}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    perf = {"schema": "shibuya.bench/classical-2026-09-28/perf/1",
            "rows": [{"arm": a, "final_hash": r["final_hash"],
                      "wall_seconds_nondeterministic": r["_wall_seconds_nondeterministic"],
                      "peak_working_set_bytes_nondeterministic": r["_peak_working_set_bytes_nondeterministic"],
                      "agents_bytes_total": r["_agents_bytes_total"]} for a, r in rows.items()]}
    Path(args.perf_out).write_text(json.dumps(perf, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="5 段目 5b の計測")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("one")
    sp.add_argument("--arm", required=True, choices=tuple(ARMS))
    sp.add_argument("--world", default="data/world/v2")
    sp.add_argument("--agents", type=int, default=5_000)
    sp.add_argument("--seed", type=int, default=1)
    sp.add_argument("--out", required=True)
    for name in ("arms", "collect"):
        sp = sub.add_parser(name)
        sp.add_argument("--world", default="data/world/v2")
        sp.add_argument("--agents", type=int, default=5_000)
        sp.add_argument("--seed", type=int, default=1)
        sp.add_argument("--out", required=True)
        sp.add_argument("--perf-out", default=str(HERE / "classical_perf.json"))
        sp.add_argument("--tmp", required=True, help="腕ごとの中間 JSON の置き場(スクラッチ)")
    args = ap.parse_args(argv)
    return {"one": cmd_one, "arms": cmd_arms, "collect": cmd_collect}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
