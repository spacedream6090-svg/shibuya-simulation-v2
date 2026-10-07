"""第 2 波 §2B: 食事の束 3 項(就寝中の既定の食事・自宅の食事行・B5 の空腹の語)の計測(判定しない)。

使い方(リポのルートで・``$D`` = この置き場):

    python $D/meal_bundle_measure.py all --scratch <作業用> --out $D/item2b_meal_bundle.json

構成: 3 方策 × 5 腕 = 15 ラン(5,000 体・seed 1・語彙 v3・energy(CLI 既定)・1 シミュ日・月曜)。
- 方策: ``mock``(既定)/ ``classical_rel``(classical・記憶 on・関係 on(関係は記憶 on が要る)・門 per_wake=既定)/
  ``classical_rel_hour``(同・門 per_hour)。
- 腕: ``base``(3 切替口とも旧)/ ``defer``(``meal_sleep_defer=on``)/ ``home``(``home_meal=plan``)/
  ``words``(``hunger_words=all``)/ ``all_on``(3 つとも)。

量: final・呼数・朝食の欠食率(全体・年齢階級・20 代・自宅が範囲内・範囲外・通勤者)・1 日の食事の回数の
分布・食事の時刻(朝/昼/夕の窓・時別)・エネルギー収支(中央値と p5〜p95・3 食の体)・範囲外の食事の内訳
(既定の時刻/W17 の食事行/起床時に遅らせた)・自宅の食事の要約・B5 の空腹の語(tok の増分・語ごとの回数=
テープのある mock の base/words)・不変条件の実データ検査(項 1 が置いた食事の時刻に W17 で就寝中の体の数=0 の
はず・W17 の食事行の時刻に W17 で就寝中の数=W17 の行の重なり)。参考に第10表(国民健康・栄養調査 令和6年)。

欠食の定義は energy-classical §5a 4 と同じ(朝の窓 5:00〜10:59 に食事が 1 回も無い体・軽食だけは欠食)。
**自宅の食事(予定の実行)は欠食の分子から外れる**(食事に数える)。壁時計は JSON に入れない。絶対パスは書かない。
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
WORLD = "data/world/v2"
N = 5_000

POLICIES: dict[str, dict[str, Any]] = {
    "mock": {"vocab_version": "v3"},
    "classical_rel": {"vocab_version": "v3", "policy": "classical", "chooser": "classical", "memory": "on",
                      "relations": "on"},
    "classical_rel_hour": {"vocab_version": "v3", "policy": "classical", "chooser": "classical", "memory": "on",
                           "relations": "on", "meal_gate": "per_hour"},
}
ARMS: dict[str, dict[str, str]] = {
    "base": {},
    "defer": {"meal_sleep_defer": "on"},
    "home": {"home_meal": "plan"},
    "words": {"hunger_words": "all"},
    "all_on": {"meal_sleep_defer": "on", "home_meal": "plan", "hunger_words": "all"},
}
AGE_CLASSES = [("1-6", 1, 6), ("7-14", 7, 14), ("15-19", 15, 19), ("20-29", 20, 29), ("30-39", 30, 39),
               ("40-49", 40, 49), ("50-59", 50, 59), ("60-69", 60, 69), ("70+", 70, 200)]
TAPE_RUNS = {("mock", "base"), ("mock", "words")}


def _skip(has_b: np.ndarray, mask: np.ndarray) -> dict[str, Any]:
    k = int(np.count_nonzero(mask))
    if k == 0:
        return {"n": 0}
    return {"n": k, "skip_pct": round(100.0 * float(np.count_nonzero(mask & ~has_b)) / k, 1)}


def _q(x: np.ndarray) -> dict[str, float]:
    if x.size == 0:
        return {"n": 0}
    p = np.percentile(x, [5, 25, 50, 75, 95])
    return {"n": int(x.size), "mean": round(float(x.mean()), 1), "p5": round(float(p[0]), 1),
            "p25": round(float(p[1]), 1), "p50": round(float(p[2]), 1), "p75": round(float(p[3]), 1),
            "p95": round(float(p[4]), 1)}


def _windows(q15: list[int]) -> dict[str, int]:
    a = np.asarray(q15, dtype=np.int64)
    out = {}
    for key, (lo, hi) in (("breakfast", (300, 660)), ("lunch", (660, 960)), ("dinner", (1020, 1440))):
        out[key] = int(a[lo // 15:hi // 15].sum())
    out["other"] = int(a.sum()) - sum(out.values())
    return out


def _hourly(q15: list[int]) -> list[int]:
    return np.asarray(q15, dtype=np.int64).reshape(24, 4).sum(axis=1).tolist()


def cmd_one(args: argparse.Namespace) -> int:
    from shibuya import cli
    from shibuya.agents.state import AgentKind
    from shibuya.agents.weekly import load_weekly
    from shibuya.engine import energy as E
    from shibuya.engine import resolve as R
    from shibuya.engine.run import _resolve_population

    pol, arm = args.policy, args.arm
    kw = {**POLICIES[pol], **ARMS[arm]}
    stash: dict[str, Any] = {}
    orig_summary = E.EnergyLayer.summary

    def summary(self, agents):  # 体ごとの配列を横取りする(計測の道具・挙動に効かない)
        stash["meal_bits"] = np.asarray(self.meal_bits).copy()
        stash["n_meals"] = np.asarray(self.n_meals).copy()
        stash["balance"] = np.asarray(agents.registry.energy_balance, dtype=np.float64).copy()
        stash["eer"] = np.asarray(agents.registry.eer_kcal, dtype=np.float64).copy()
        stash["age"] = np.asarray(agents.registry.age, dtype=np.int64).copy()
        stash["sex"] = np.asarray(agents.registry.sex, dtype=np.int64).copy()
        stash["kind"] = np.asarray(agents.registry.field("kind"), dtype=np.int64).copy()
        return orig_summary(self, agents)

    E.EnergyLayer.summary = summary
    placed: list[tuple[np.ndarray, int]] = []
    rows_meals: list[tuple[np.ndarray, int]] = []
    orig_out = R.energy_out_of_area_meal

    def spy(agents, energy, agent_id, slots, from_row, tick, deferred=None):
        fr = np.asarray(from_row, dtype=bool)
        placed.append((np.asarray(agent_id)[~fr].copy(), int(tick)))
        rows_meals.append((np.asarray(agent_id)[fr].copy(), int(tick)))
        return orig_out(agents, energy, agent_id, slots, from_row, tick, deferred=deferred)

    R.energy_out_of_area_meal = spy
    # 描画の計数(B5 の tok・個体の群の tok・空腹の語ごとの回数)=テープの対象のランだけ。
    # テープの blocks は共有ブロック(B0〜B4b)だけを持つので B5 は描画の側で数える(計測の道具)。
    rstat: dict[str, Any] = {"b5": [], "individual": [], "words": {}, "none": 0}
    if (pol, arm) in TAPE_RUNS:
        from shibuya.perception import renderer as RD
        from shibuya.perception import templates as T

        orig_render = RD.Renderer.render

        def render(self, *a, **k):
            out = orig_render(self, *a, **k)
            rstat["b5"].append(int(out.tokens_est.get("B5", 0)))
            rstat["individual"].append(int(out.group_tokens.get("individual", 0)))
            txt = out.blocks["B5"].decode("utf-8")
            hit = [w for w in T.HUNGER_WORDS if f"いま{w}です" in txt]
            if hit:
                rstat["words"][hit[0]] = rstat["words"].get(hit[0], 0) + 1
            else:
                rstat["none"] += 1
            return out

        RD.Renderer.render = render
    tape = str(Path(args.scratch) / f"{pol}_{arm}") if (pol, arm) in TAPE_RUNS else None
    res = cli.run(n_agents=N, seed=1, world_dir=WORLD, tape_path=tape, **kw)
    e = dict(res.energy)
    m = res.run_manifest_fields()

    pop = _resolve_population(None, WORLD, N, 1, 10**9)
    home_in = np.zeros(N, dtype=bool)
    home_in[: pop.n] = np.asarray(pop.home_cell, dtype=np.int64)[:N] >= 0
    has_b = (stash["meal_bits"] & 1) != 0
    age, sex, kind = stash["age"], stash["sex"], stash["kind"]
    tw = (age >= 20) & (age <= 29)
    skip = {
        "all": _skip(has_b, np.ones(N, dtype=bool)),
        "age1plus": _skip(has_b, age >= 1),
        "age20_29": _skip(has_b, tw),
        "age20_29_male": _skip(has_b, tw & (sex == 0)),
        "age20_29_female": _skip(has_b, tw & (sex == 1)),
        "home_in_area": _skip(has_b, home_in),
        "home_out_of_area": _skip(has_b, ~home_in),
        "commuter": _skip(has_b, kind == int(AgentKind.COMMUTER)),
        "by_age_class": {name: _skip(has_b, (age >= lo) & (age <= hi)) for name, lo, hi in AGE_CLASSES},
    }
    nm = stash["n_meals"].astype(np.int64)
    bal = stash["balance"]
    # 不変条件(実データ): 項 1 が置いた食事(既定の時刻・遅らせた)の時刻に W17 で就寝中の体
    w = load_weekly(WORLD).restrict_to(pop.source_agent_id)

    def asleep_count(pairs: list[tuple[np.ndarray, int]]) -> int:
        if not pairs:
            return 0
        a = np.concatenate([x for x, _ in pairs])
        t = np.concatenate([np.full(x.size, tk) for x, tk in pairs])
        return int(np.count_nonzero(E.w17_wake_minute(w, N, 0, a, t) >= 0)) if a.size else 0

    counts = e.get("counts", {})
    doc: dict[str, Any] = {
        "policy": pol, "arm": arm, "switches": kw,
        "final": res.final_hash[:16], "calls": int(res.llm_calls),
        "manifest_switches": {k: m.get(k) for k in ("meal_sleep_defer", "home_meal", "hunger_words")},
        "breakfast_skip": skip,
        "meals_per_agent": {str(k): int(np.count_nonzero(nm == k)) for k in range(4)}
        | {"4+": int(np.count_nonzero(nm >= 4))},
        "meal_windows": {
            "in_area": _windows(e["meal_start_in_15min"]),
            "out_of_area": _windows(e["meal_start_out_15min"]),
            "home_plan": _windows(e.get("home_meal", {}).get("meal_start_home_15min", [0] * 96)),
        },
        "meal_hourly": {
            "in_area": _hourly(e["meal_start_in_15min"]),
            "out_of_area": _hourly(e["meal_start_out_15min"]),
            "home_plan": _hourly(e.get("home_meal", {}).get("meal_start_home_15min", [0] * 96)),
        },
        "balance_kcal": _q(bal),
        "balance_kcal_three_meals": _q(bal[(stash["meal_bits"] & 7) == 7]),
        "balance_over_eer_by_meals": {str(k): _q(bal[nm == k] / stash["eer"][nm == k]) for k in range(4)},
        "census_per_agent": e.get("census_per_agent"),
        "counts": {
            "meals_in_area": int(counts.get("meals_in_area", 0)),
            "meals_out_of_area": int(counts.get("meals_out_of_area", 0)),
            "meals_out_from_row": int(counts.get("meals_out_from_row", 0)),
            "meals_out_default_at_default_time": int(counts.get("meals_out_default", 0))
            - int(counts.get("meals_out_deferred", 0)),
            "meals_out_deferred": int(counts.get("meals_out_deferred", 0)),
            "meals_home_plan": int(counts.get("meals_home_plan", 0)),
            "snacks": int(counts.get("snacks", 0)),
        },
        "out_of_area_schedule": e.get("out_of_area_schedule"),
        "home_meal": {k: v for k, v in e.get("home_meal", {}).items() if k != "meal_start_home_15min"},
        "stage_time_share": e.get("stage_time_share"),
        "invariant_item1_placed_meals_while_w17_asleep": asleep_count(placed),
        "w17_row_meals_while_w17_asleep": asleep_count(rows_meals),
        "w17_row_meals": int(sum(x.size for x, _ in rows_meals)),
    }
    if m.get("classical"):
        c = m["classical"].get("counts", {})
        doc["classical_meal_gate"] = {"mode": m["classical"].get("meal_gate", {}).get("mode"),
                                      "rule": m["classical"].get("meal_gate", {}).get("per_hour_rule"),
                                      "passed": int(c.get("meal", 0)),
                                      "passed_by_stage": {k.split(":")[1]: int(v) for k, v in sorted(c.items())
                                                          if k.startswith("meal_stage:")}}
    if tape is not None:
        import pyarrow.parquet as pq

        ti = np.asarray(pq.read_table(Path(tape) / "calls.parquet", columns=["tokens_in"])
                        .column("tokens_in").to_pylist(), dtype=np.float64)
        b5 = np.asarray(rstat["b5"], dtype=np.float64)
        ind = np.asarray(rstat["individual"], dtype=np.float64)
        doc["render"] = {
            "renders": int(b5.size), "b5_tokens": _q(b5), "b5_tokens_max": int(b5.max()) if b5.size else 0,
            "individual_group_tokens": _q(ind), "individual_group_max": int(ind.max()) if ind.size else 0,
            "word_draws": dict(rstat["words"]), "no_word": int(rstat["none"]),
            "tape_calls": int(ti.size), "tape_tokens_in": _q(ti),
            "tape_tokens_in_sum": int(ti.sum()),
        }
    print(json.dumps(doc, ensure_ascii=False))
    return 0


def cmd_all(args: argparse.Namespace) -> int:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    jobs = [(p, a) for p in POLICIES for a in ARMS]
    if args.only:
        want = set(args.only.split(","))
        jobs = [j for j in jobs if f"{j[0]}:{j[1]}" in want]

    def one(job: tuple[str, str]) -> dict[str, Any]:
        cmd = [sys.executable, str(Path(__file__)), "one", "--policy", job[0], "--arm", job[1],
               "--scratch", args.scratch]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(REPO))
        if r.returncode != 0:
            return {"policy": job[0], "arm": job[1], "error": r.stderr[-2000:]}
        return json.loads(r.stdout.strip().splitlines()[-1])

    rows = []
    with cf.ThreadPoolExecutor(max_workers=int(args.jobs)) as ex:
        for row in ex.map(one, jobs):
            rows.append(row)
            print(row.get("policy"), row.get("arm"), row.get("final"), row.get("calls"),
                  (row.get("breakfast_skip") or {}).get("all"), (row.get("error") or "")[-400:], flush=True)
    anc = json.loads((REPO / "docs/bench/anchors/hunger_energy_anchors_v0.json").read_text(encoding="utf-8"))
    t10 = anc["nhns_t10_breakfast_skip"]
    doc = {
        "schema": "shibuya.bench/wave2-2026-09-30/meal-bundle-2b/1",
        "how": "5,000 体・seed 1・語彙 v3・energy・1 シミュ日(月曜)。3 方策 × 5 腕。判定しない",
        "skip_definition": "朝の窓 5:00〜10:59 に食事(範囲内・範囲外・自宅の予定の実行)が 1 回も無い体(軽食だけは欠食)",
        "anchor_t10_breakfast_skip_pct": {"age_classes": t10["age_classes"], "pct": t10["pct"],
                                          "source": "国民健康・栄養調査 令和6年 第10表(錨 hunger_energy_anchors_v0)"},
        "rows": rows,
    }
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1, default=str) + "\n",
                              encoding="utf-8", newline="\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("one")
    sp.add_argument("--policy", required=True, choices=tuple(POLICIES))
    sp.add_argument("--arm", required=True, choices=tuple(ARMS))
    sp.add_argument("--scratch", required=True)
    sp = sub.add_parser("all")
    sp.add_argument("--scratch", required=True)
    sp.add_argument("--out", required=True)
    sp.add_argument("--jobs", type=int, default=4)
    sp.add_argument("--only", default="")
    args = ap.parse_args(argv)
    return {"one": cmd_one, "all": cmd_all}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
