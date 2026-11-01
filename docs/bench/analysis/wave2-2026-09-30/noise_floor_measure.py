"""第 2 波 §2B(検収後の直し): 項 2(自宅の食事)の総呼数の差を、**揺らぎの床**と並べる(判定しない)。

使い方(リポのルートで・``$D`` = この置き場):

    python $D/noise_floor_measure.py all --scratch <作業用> --out $D/item2b_noise_floor.json

構成: 方策 2 通り(mock・classical+記憶 on+関係 on・門は既定 per_wake)× 腕 5 本(5,000 体・seed 1・語彙 v3・energy・
月曜・テープつき)。
- ``base``: 3 切替口とも旧。
- ``home``: ``home_meal=plan``。
- ``floor0``〜``floor2``: 旧のまま、tick 360(6:00)以後の範囲内の飲食店の食事のうち k 番目(k=0,1,2)の 1 回だけ、
  食べた体の食後の ``since_meal`` を +1 kcal・収支を −1 kcal(=摂取を 1 kcal 減らした食後の状態)にする。
  1 kcal は語の段の区切り(EER/3 × 0.25 ≈ 150〜200 kcal)の 1% 未満で、挙動には効かないはずの最小の違い。
  **床の測り方は実行役の案=未リサーチ(expedient)**。

量(テープの calls の ``agent_id`` と ``tick`` を base と比べる): 総呼数の差・呼数が変わった体の数・揺らぎを受けた体
(自宅で食べた体/+1 kcal の体)自身の呼数の差・ほかの体の差・呼の並びが最初に分かれた tick(tick ごとの呼数の列で比較)。
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
T_FROM = 360
POLICIES: dict[str, dict[str, Any]] = {
    "mock": {"vocab_version": "v3"},
    "classical_rel": {"vocab_version": "v3", "policy": "classical", "chooser": "classical", "memory": "on",
                      "relations": "on"},
}
ARMS = ("base", "home", "floor0", "floor1", "floor2")


def cmd_one(args: argparse.Namespace) -> int:
    from shibuya import cli
    from shibuya.engine import resolve as R

    pol, arm = args.policy, args.arm
    kw = dict(POLICIES[pol])
    touched: list[int] = []
    if arm == "home":
        kw["home_meal"] = "plan"
        orig_home = R.energy_home_meal

        def spy_home(agents, energy, agent_id, slots, tick):
            touched.extend(int(a) for a in np.asarray(agent_id).tolist())
            return orig_home(agents, energy, agent_id, slots, tick)

        R.energy_home_meal = spy_home
    elif arm.startswith("floor"):
        k = int(arm[5:])
        seen = [0]
        orig_meal = R._energy_meal

        def nudge(r, ids, tick, energy, *, kind, slots=None, from_row=None, deferred=None):
            orig_meal(r, ids, tick, energy, kind=kind, slots=slots, from_row=from_row, deferred=deferred)
            ids = np.asarray(ids, dtype=np.int64)
            if kind == "meal_in" and int(tick) >= T_FROM and ids.size and not touched:
                if seen[0] == k:
                    a = int(ids[0])
                    r.since_meal_kcal[a] += np.float32(1.0)
                    r.energy_balance[a] -= np.float32(1.0)
                    touched.append(a)
                seen[0] += 1

        R._energy_meal = nudge
    tape = Path(args.scratch) / f"nf_{pol}_{arm}"
    res = cli.run(n_agents=N, seed=1, world_dir=WORLD, tape_path=str(tape), **kw)
    print(json.dumps({"policy": pol, "arm": arm, "final": res.final_hash[:16], "calls": int(res.llm_calls),
                      "touched": sorted(set(touched)), "tape": tape.name}))
    return 0


def _calls(tape: Path) -> tuple[np.ndarray, np.ndarray]:
    import pyarrow.parquet as pq

    t = pq.read_table(tape / "calls.parquet", columns=["agent_id", "tick"])
    return (np.asarray(t.column("agent_id").to_pylist(), dtype=np.int64),
            np.asarray(t.column("tick").to_pylist(), dtype=np.int64))


def cmd_all(args: argparse.Namespace) -> int:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    jobs = [(p, a) for p in POLICIES for a in ARMS]

    def one(job: tuple[str, str]) -> dict[str, Any]:
        cmd = [sys.executable, str(Path(__file__)), "one", "--policy", job[0], "--arm", job[1],
               "--scratch", args.scratch]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(REPO))
        if r.returncode != 0:
            return {"policy": job[0], "arm": job[1], "error": r.stderr[-2000:]}
        return json.loads(r.stdout.strip().splitlines()[-1])

    with cf.ThreadPoolExecutor(max_workers=int(args.jobs)) as ex:
        runs = list(ex.map(one, jobs))
    rows = []
    for pol in POLICIES:
        base = next(r for r in runs if r["policy"] == pol and r["arm"] == "base")
        ba, bt = _calls(Path(args.scratch) / base["tape"])
        bc = np.bincount(ba, minlength=N)
        btick = np.bincount(bt, minlength=1440)
        for r in runs:
            if r["policy"] != pol or r["arm"] == "base":
                continue
            if r.get("error"):
                rows.append(r)
                continue
            a, t = _calls(Path(args.scratch) / r["tape"])
            c = np.bincount(a, minlength=N)
            tk = np.bincount(t, minlength=1440)
            diff = c - bc
            touched = np.asarray(r["touched"], dtype=np.int64)
            mask = np.zeros(N, dtype=bool)
            mask[touched] = True
            div = np.flatnonzero(tk != btick)
            rows.append({
                "policy": pol, "arm": r["arm"], "final": r["final"], "calls": r["calls"],
                "base_final": base["final"], "base_calls": base["calls"],
                "calls_diff": int(r["calls"] - base["calls"]),
                "agents_with_changed_calls": int(np.count_nonzero(diff)),
                "touched_agents": int(touched.size),
                "calls_diff_touched": int(diff[mask].sum()),
                "calls_diff_others": int(diff[~mask].sum()),
                "first_tick_calls_differ": int(div[0]) if div.size else None,
            })
            print(json.dumps(rows[-1], ensure_ascii=False), flush=True)
    doc = {"schema": "shibuya.bench/wave2-2026-09-30/noise-floor-2b/1",
           "how": "5,000 体・seed 1・v3・energy・月曜・テープの calls を base と体ごと・tick ごとに比べる。"
                  "floor=tick 360 以後の k 番目の範囲内の飲食店の食事の 1 回だけ食後の since_meal +1 kcal・収支 −1 kcal"
                  "(実行役の案=未リサーチ)。判定しない",
           "rows": rows}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("one")
    sp.add_argument("--policy", required=True, choices=tuple(POLICIES))
    sp.add_argument("--arm", required=True, choices=ARMS)
    sp.add_argument("--scratch", required=True)
    sp = sub.add_parser("all")
    sp.add_argument("--scratch", required=True)
    sp.add_argument("--out", required=True)
    sp.add_argument("--jobs", type=int, default=4)
    args = ap.parse_args(argv)
    return {"one": cmd_one, "all": cmd_all}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
