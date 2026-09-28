"""5 段目 5a(体のエネルギー収支・D-118 K1〜K9)の計測。

使い方(リポジトリの根から)::

    # 15 腕を energy(CLI の既定)と v1(旧規則)で回す(v1 は 3 段目の記録と一致するはず)
    python docs/bench/analysis/energy-classical-2026-09-28/energy_measure.py arms15 --model energy \\
        --world data/world/v2 --out docs/bench/analysis/energy-classical-2026-09-28/arms15_energy.json
    python docs/bench/analysis/energy-classical-2026-09-28/energy_measure.py arms15 --model v1 \\
        --world data/world/v2 --out docs/bench/analysis/energy-classical-2026-09-28/arms15_v1.json
    # 壁時計と RSS(v3 既定・1 構成=1 プロセス: v1 / energy eer / energy bmr)
    python docs/bench/analysis/energy-classical-2026-09-28/energy_measure.py perf \\
        --world data/world/v2 --out docs/bench/analysis/energy-classical-2026-09-28/perf.json
    # 照合(食事開始の 15 分分布 × 錨 3 本・欠食率・語の段の時間・収支の分布・D-111 の予想表)
    python docs/bench/analysis/energy-classical-2026-09-28/energy_measure.py report \\
        --out docs/bench/analysis/energy-classical-2026-09-28/report.json

- ``arms15``: [W6 再生成の計測](../w6-regen-2026-09-28/w6_regen_measure.py) の 15 腕(``ARMS``)を
  ``cli.run(..., hunger_model=<model>)`` で回し、[3 段目の記録](../l4-unlimited-2026-09-28/l4_arms15.json)
  の ``unlimited`` の final と並べる。v3 既定の腕は energy の要約を全部控える(report が読む)。
- ``perf``: 子プロセスで 1 構成ずつ回し、壁時計と**ピークの作業セット**(Windows
  ``K32GetProcessMemoryInfo``)と ``AgentState.bytes_total()`` を取る。**決定論でない**(同じ PC の 1 回)。
- ``report``: 錨(``docs/bench/anchors/hunger_energy_anchors_v0.json``)だけを読む(data/ は読まない)。
  食事開始の分布は**範囲内の食事だけ**(K6 (i) の付帯)。照合であって較正ではない。

絶対パスは書かない。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
W6 = HERE.parent / "w6-regen-2026-09-28" / "w6_regen_measure.py"
L4 = HERE.parent / "l4-unlimited-2026-09-28" / "l4_arms15.json"
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


def _w6() -> Any:
    spec = importlib.util.spec_from_file_location("w6_regen_measure", W6)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _peak_working_set_bytes() -> int:
    """Windows のピーク作業セット(RSS 相当)。取れなければ -1。"""
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
    except Exception:  # noqa: BLE001 - Windows 以外
        return -1


def _summ(res: Any, full_energy: bool) -> dict[str, Any]:
    cbc = dict(res.calls_by_condition)
    calls = int(res.column("calls").sum()) if res.diagnostics.size else 0
    purchases_tick = res.column("purchases") if res.diagnostics.size else []
    by_hour = [0] * 24
    for t, v in enumerate(purchases_tick):
        by_hour[(t // 60) % 24] += int(v)
    au = dict(res.action_usage)
    llm_actions = {k: v for k, v in au.items() if k != ENGINE_CONTINUE}
    e = dict(res.energy)
    keep = ("counts", "census_per_agent", "stage_time_share", "breakfast_skip", "meals_per_agent",
            "balance_kcal", "rate")
    return {
        "final_hash": res.final_hash,
        "llm_calls": calls,
        "llm_calls_per_agent_day": round(calls / max(1, res.n_agents), 4),
        "calls_by_entrance": {k: int(sum(cbc.get(c, 0) for c in v)) for k, v in ENTRANCES.items()},
        "calls_by_condition": cbc,
        "action_usage_llm": llm_actions,
        "purchases": int(sum(by_hour)),
        "purchases_by_hour": by_hour,
        "meals_in_area": int(res.meals),
        "intero_crossings": dict(res.intero_crossings),
        "hunger_model": str(res.hunger_model),
        "energy": e if full_energy else {k: e[k] for k in keep if k in e},
        "conserved": bool(res.conserved),
    }


# ------------------------------------------------------------------ arms15
def cmd_arms15(args: argparse.Namespace) -> int:
    from shibuya import cli

    w6 = _w6()
    before = {r["arm"]: r["unlimited"]["final_hash"]
              for r in json.loads(L4.read_text(encoding="utf-8"))["arms"]}
    rows = []
    for name, kw in w6.ARMS.items():
        t0 = time.perf_counter()
        res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world,
                      hunger_model=args.model, **kw)
        row = {"arm": name, "args": dict(kw), "final_stage3": before.get(name, ""),
               **_summ(res, full_energy=(name == "v3_default"))}
        row["equals_stage3"] = row["final_hash"] == row["final_stage3"]
        rows.append(row)
        print(f"{name}: {row['final_stage3'][:8]} → {row['final_hash'][:8]} "
              f"{'=' if row['equals_stage3'] else '≠'} calls {row['llm_calls']:,} "
              f"({time.perf_counter() - t0:.1f}s)", flush=True)
    doc = {"schema": "shibuya.bench/energy-2026-09-28/arms15/1", "n_agents": args.agents,
           "seed": args.seed, "hunger_model": args.model, "arms": rows}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n",
                              encoding="utf-8")
    return 0


# ------------------------------------------------------------------ perf(1 構成=1 プロセス)
def cmd_one(args: argparse.Namespace) -> int:
    from shibuya import cli

    t0 = time.perf_counter()
    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, vocab_version="v3",
                  hunger_model=args.model, energy_rate=args.rate)
    wall = time.perf_counter() - t0
    out = {
        "hunger_model": args.model, "energy_rate": args.rate if args.model == "energy" else "",
        "final_hash": res.final_hash, "llm_calls": int(res.llm_calls),
        "agents_bytes_total": int(res.agents.bytes_total()),  # type: ignore[attr-defined]
        "agents_declared_bytes_per_agent": int(res.agents.declared_bytes_per_agent),  # type: ignore[attr-defined]
        "wall_seconds_nondeterministic": round(wall, 2),
        "peak_working_set_bytes_nondeterministic": _peak_working_set_bytes(),
        "census_per_agent": dict(res.energy.get("census_per_agent", {})),
    }
    print(json.dumps(out, ensure_ascii=False))
    return 0


def cmd_perf(args: argparse.Namespace) -> int:
    rows = []
    for model, rate in (("v1", "eer"), ("energy", "eer"), ("energy", "bmr")):
        cmd = [sys.executable, str(Path(__file__)), "one", "--model", model, "--rate", rate,
               "--world", args.world, "--agents", str(args.agents), "--seed", str(args.seed)]
        got = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True)
        row = json.loads(got.stdout.strip().splitlines()[-1])
        rows.append(row)
        print(f"{model}/{rate}: final {row['final_hash'][:8]} wall {row['wall_seconds_nondeterministic']}s "
              f"peak WS {row['peak_working_set_bytes_nondeterministic'] / 2**20:.1f} MiB "
              f"agents {row['agents_bytes_total']:,} B", flush=True)
    Path(args.out).write_text(json.dumps({"schema": "shibuya.bench/energy-2026-09-28/perf/1",
                                          "rows": rows}, ensure_ascii=False, indent=1) + "\n",
                              encoding="utf-8")
    return 0


# ------------------------------------------------------------------ report
def _norm(xs: list[float | None]) -> list[float]:
    v = [0.0 if x is None else float(x) for x in xs]
    s = sum(v)
    return [x / s for x in v] if s > 0 else v


def _tvd(p: list[float], q: list[float]) -> float:
    return 0.5 * sum(abs(a - b) for a, b in zip(p, q))


def _jsd(p: list[float], q: list[float]) -> float:
    out = 0.0
    for a, b in zip(p, q):
        m = 0.5 * (a + b)
        if a > 0:
            out += 0.5 * a * math.log2(a / m)
        if b > 0:
            out += 0.5 * b * math.log2(b / m)
    return out


def _peak_slots(p: list[float], k: int = 3) -> list[str]:
    order = sorted(range(len(p)), key=lambda i: (-p[i], i))[:k]
    return [f"{i * 15 // 60:02d}:{i * 15 % 60:02d}" for i in order]


def _by_hour(xs: list[float]) -> list[float]:
    return [sum(xs[h * 4:(h + 1) * 4]) for h in range(24)]


def _window_peaks(p: list[float]) -> dict[str, str]:
    """朝(5-10 時台)・昼(11-15 時台)・夕(17-23 時台)それぞれの最大区分の開始。"""
    out = {}
    for name, lo, hi in (("breakfast", 20, 44), ("lunch", 44, 64), ("dinner", 68, 96)):
        i = max(range(lo, hi), key=lambda j: (p[j], -j))
        out[name] = f"{i * 15 // 60:02d}:{i * 15 % 60:02d}"
    return out


def cmd_report(args: argparse.Namespace) -> int:
    anc = json.loads(ANCHORS.read_text(encoding="utf-8"))
    en = json.loads((HERE / "arms15_energy.json").read_text(encoding="utf-8"))
    v1 = json.loads((HERE / "arms15_v1.json").read_text(encoding="utf-8"))
    ea = {r["arm"]: r for r in en["arms"]}
    va = {r["arm"]: r for r in v1["arms"]}
    e3 = ea["v3_default"]
    v3 = va["v3_default"]
    energy = e3["energy"]
    n = int(en["n_agents"])

    # ---- (b) 食事開始の 15 分分布(範囲内)× 錨 3 本 ----
    sim = _norm(energy["meal_start_in_15min"])
    series = anc["ssb2021_meal_rate_15min"]["series"]
    ref = {k: _norm(v["rate_pct"]) for k, v in series.items()}
    compare = {
        k: {"tvd": round(_tvd(sim, r), 4), "jsd_bits": round(_jsd(sim, r), 4),
            "peak_slots": _peak_slots(r), "window_peaks": _window_peaks(r),
            "share_by_hour": [round(x, 4) for x in _by_hour(r)]}
        for k, r in ref.items()
    }
    floor = {
        "national_vs_tokyo": {"tvd": round(_tvd(ref["t8_1_weekday_national_total"],
                                                ref["t7_1_weekday_tokyo_total"]), 4),
                              "jsd_bits": round(_jsd(ref["t8_1_weekday_national_total"],
                                                     ref["t7_1_weekday_tokyo_total"]), 4)},
        "national_vs_kanto": {"tvd": round(_tvd(ref["t8_1_weekday_national_total"],
                                                ref["t8_1_weekday_kanto_total"]), 4),
                              "jsd_bits": round(_jsd(ref["t8_1_weekday_national_total"],
                                                     ref["t8_1_weekday_kanto_total"]), 4)},
        "kanto_vs_tokyo": {"tvd": round(_tvd(ref["t8_1_weekday_kanto_total"],
                                             ref["t7_1_weekday_tokyo_total"]), 4),
                           "jsd_bits": round(_jsd(ref["t8_1_weekday_kanto_total"],
                                                  ref["t7_1_weekday_tokyo_total"]), 4)},
    }
    meal_in = {
        "n_meals_in_area": int(sum(energy["meal_start_in_15min"])),
        "peak_slots": _peak_slots(sim),
        "window_peaks": _window_peaks(sim),
        "share_by_hour": [round(x, 4) for x in _by_hour(sim)],
        "compare": compare,
        "floor_between_anchors": floor,
        "note": "照合(K6 (i)・較正に使っていない)。錨は行動者率(その 15 分に食事をした人の割合)、"
                "シミュレーションは食事の成立(開始)の件数=形だけを比べる(正規化して総和 1)。",
    }
    meal_out = {"n_meals_out_of_area": int(sum(energy["meal_start_out_15min"])),
                "peak_slots": _peak_slots(_norm(energy["meal_start_out_15min"])),
                "note": "予定由来(W17 の食事行・既定の時刻)=照合の分子・分母から外す"}

    # ---- (a) D-111 の予想表(mock で取れる行だけ) ----
    def entr_share(r: dict[str, Any]) -> float:
        ent = r["calls_by_entrance"]
        tot = sum(ent.values())
        return round(ent["体"] / tot, 4) if tot else 0.0

    def night(r: dict[str, Any]) -> dict[str, Any]:
        h = r["purchases_by_hour"]
        tot = sum(h)
        return {"purchases_0_5h": int(sum(h[0:5])), "purchases": int(tot),
                "share_0_5h": round(sum(h[0:5]) / tot, 4) if tot else 0.0}

    def act_share(r: dict[str, Any]) -> dict[str, Any]:
        au = r["action_usage_llm"]
        tot = sum(au.values())
        mv = au.get("移動", 0) + au.get("購入", 0)
        return {"move_plus_buy": round(mv / tot, 4) if tot else 0.0, "llm_actions": int(tot)}

    ex = energy["counts"]
    d111 = {
        "b5_hunger_line_share_awake_in_area": {
            "v1_hunger_ge_4_note": "v1 の B5 は hunger≥4 で「閾値超え」を描く(時間割合は未計測=段 0〜3 の時間は v1 には無い)",
            "energy_hungry_or_very_hungry": round(
                energy["stage_time_share"]["awake_in_area"]["hungry"]
                + energy["stage_time_share"]["awake_in_area"]["very_hungry"], 4),
            "predicted": "0.11",
        },
        "wake_entrance_body_share": {"v1": entr_share(v3), "energy": entr_share(e3),
                                     "predicted": "0.05-0.08"},
        "intero_crossings_awake_in_area": {"v1": v3["intero_crossings"], "energy": e3["intero_crossings"]},
        "late_night_purchases": {"v1": night(v3), "energy": night(e3), "predicted": "≈0"},
        "realized_per_agent_day": {
            "v1": {"purchases": round(v3["purchases"] / n, 3), "meals_in_area": round(v3["meals_in_area"] / n, 3)},
            "energy": {"purchases": round(e3["purchases"] / n, 3),
                       "meals_in_area": round(e3["meals_in_area"] / n, 3),
                       "meals_out_of_area": round(ex["meals_out_of_area"] / n, 3),
                       "snacks": round(ex["snacks"] / n, 3)},
            "predicted": "2-3",
        },
        "action_distribution": {"v1": act_share(v3), "energy": act_share(e3), "predicted": "0.6-0.7"},
        "reason_column": "mock では取れない(理由は定型)",
    }

    # ---- (c) 朝食の欠食率(20 代) ----
    t10 = anc["nhns_t10_breakfast_skip"]
    i20 = t10["age_classes"].index("20-29")
    skip = {
        "sim": energy["breakfast_skip"],
        "anchor_pct_20_29": {"total": t10["pct"]["total"][i20], "male": t10["pct"]["male"][i20],
                             "female": t10["pct"]["female"][i20]},
        "definition_note": "sim=その日に朝の窓(5:00〜10:59)で食事(範囲内/範囲外)が 1 回も無い体の割合。"
                           "軽食だけの体は欠食に数える(第10表の欠食=菓子・果物などのみ+錠剤などのみ+何も食べない)",
    }
    doc = {
        "schema": "shibuya.bench/energy-2026-09-28/report/1",
        "day_of_week": "day_index=0=月曜=平日(run_day の既定)→ 第8-1表(平日)・第7-1表 平日・第18-1表(平日)",
        "d111_prediction_table": d111,
        "meal_start_in_area": meal_in,
        "meal_start_out_of_area": meal_out,
        "breakfast_skip": skip,
        "stage_time_share": energy["stage_time_share"],
        "balance": {k: energy[k] for k in ("census", "census_per_agent", "balance_kcal",
                                            "balance_kcal_by_meals", "balance_over_eer_by_meals",
                                            "meals_per_agent", "agents_with_three_meals")},
        "counts": energy["counts"],
        "intake_kcal": energy["intake_kcal"],
        "weight_kg": energy["weight_kg"],
        "eer_kcal": energy["eer_kcal"],
        "arms15": [
            {"arm": a, "v1_final": va[a]["final_hash"], "v1_equals_stage3": va[a]["equals_stage3"],
             "energy_final": ea[a]["final_hash"], "v1_calls": va[a]["llm_calls"],
             "energy_calls": ea[a]["llm_calls"],
             "v1_body_entrance": va[a]["calls_by_entrance"]["体"],
             "energy_body_entrance": ea[a]["calls_by_entrance"]["体"],
             "energy_meals_in_area": ea[a]["meals_in_area"],
             "energy_meals_out_of_area": ea[a]["energy"]["counts"]["meals_out_of_area"],
             "energy_awake_in_area_hungry_plus": round(
                 ea[a]["energy"]["stage_time_share"]["awake_in_area"]["hungry"]
                 + ea[a]["energy"]["stage_time_share"]["awake_in_area"]["very_hungry"], 4)}
            for a in ea
        ],
    }
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: doc[k] for k in ("d111_prediction_table", "breakfast_skip")},
                     ensure_ascii=False, indent=1))
    print(json.dumps({k: meal_in[k] for k in ("peak_slots", "window_peaks", "floor_between_anchors")},
                     ensure_ascii=False))
    print(json.dumps({k: v["tvd"] for k, v in compare.items()}, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="5 段目 5a の計測")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("arms15", "one", "perf"):
        sp = sub.add_parser(name)
        sp.add_argument("--world", default="data/world/v2")
        sp.add_argument("--agents", type=int, default=5_000)
        sp.add_argument("--seed", type=int, default=1)
        if name != "one":
            sp.add_argument("--out", required=True)
        if name in ("arms15", "one"):
            sp.add_argument("--model", choices=("v1", "energy"), default="energy")
        if name == "one":
            sp.add_argument("--rate", choices=("eer", "bmr"), default="eer")
    sp = sub.add_parser("report")
    sp.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    return {"arms15": cmd_arms15, "one": cmd_one, "perf": cmd_perf, "report": cmd_report}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
