"""第 2 期 2-1 経済の段階 2: 世界資産の 2 日のラン(5,000 体・seed 1・既定 v3・暦の口で開始日 2026-08-24(月)=25 日の
給料日をまたぐ)で腕 off/on(部品)の動いた量を測る道具。

``one`` は 1 本回して 1 行の JSON を出す(final・呼数・帳簿の行の数と溢れ・行/体/日・日ごとの保存則の検算・段階 2 の計器・
財布と預金の分位と平均・日ごとの財布の 1 体あたりの増減=v1 の「1 日 1 体 536 円ずつ減る」の見張り・RunResult.conserved)。
``side`` は腕 off・on(全部)・部品を 1 つずつ止めた 5 本を別のプロセスで回して 1 つの JSON にまとめる。
``--with-port`` で腕 on(全部)× 候補の口の腕 port(mock の口)の 1 本を足す(〔検収 A1〕呼の id の配線で運ばれる判断の数)。

    python $D/stage2_two_day.py side --out $W/two_day_ec21.json            # 作業木の src(PYTHONPATH=src)
    python $D/stage2_two_day.py summary --src $W/two_day_ec21.json         # 記録の表の行

絶対パスは JSON に書かない。逐次ループ宣言: なし(道具)。
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
REPO = HERE.parents[6]
PARTS = ("wages", "withdraw", "payment", "tax", "visitors")


def cmd_one(args: argparse.Namespace) -> int:
    import numpy as np

    from shibuya import cli
    from shibuya.engine import economy_stage2 as ES2

    from shibuya.engine.decision import layer as DL

    ES2.set_arm(args.arm)
    ES2.set_parts(args.parts or None)
    DL.set_arm(args.decision_port)
    t0 = time.perf_counter()
    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, sim_days=2, vocab_version="v3",
                  start_sim_datetime=args.start)
    man = res.run_manifest_fields()
    led = res.ledger.money
    eco = dict(man["economy"])
    s2 = eco.pop("stage2", None)
    n = int(args.agents)
    daily = []
    prev = {"households": int(res.money_start)}
    for d in man["daily"]:
        e = d["economy"]
        hh, ms = int(d["money"]["households"]), int(d["money"].get("money_supply", 0))
        rec: dict[str, Any] = {"day": d["day"], "households_cash_end": hh, "money_supply_end": ms,
                               "cash_per_agent_change": round((hh - int(prev["households"])) / n, 3),
                               "money_supply_per_agent_change": (round((ms - int(prev["money_supply"])) / n, 3)
                                                                 if "money_supply" in prev else None),
                               "rows": e.get("rows"), "rows_per_agent": round(int(e.get("rows", 0)) / n, 3),
                               "overflow": e.get("overflow"), "flow_sum_ok": e.get("flow_sum_ok"),
                               "conservation": e.get("conservation"), "census_flow_ok": d.get("census_row", {}).get("flow_ok")}
        prev = {"households": hh, "money_supply": ms}
        if "stage2" in e:
            rec["stage2"] = e["stage2"]
        daily.append(rec)
    dep = np.asarray(led.balance(1, 0), dtype=np.int64)
    out = {
        "arm": args.arm, "parts": list(ES2.parts()) if args.arm == "on" else [],
        "decision_port": args.decision_port, "decision_port_stage2": (man.get("decision_port") or {}).get("stage2"),
        "agents": n, "seed": args.seed, "start": args.start, "final": res.final_hash[:16], "calls": int(res.llm_calls),
        "conserved": bool(res.conserved), "money_start": int(res.money_start), "money_end": int(res.money_end),
        "money_stage2_in": int(getattr(res, "money_stage2_in", 0)), "deposit_total_end": int(dep.sum()),
        "economy": eco, "stage2": s2, "daily": daily, "wall_seconds": round(time.perf_counter() - t0, 1),
    }
    print(json.dumps(out, ensure_ascii=False))
    return 0


def cmd_side(args: argparse.Namespace) -> int:
    runs = [("off", "", "legacy"), ("on", "", "legacy")] + [
        ("on", ",".join(p for p in PARTS if p != x), "legacy") for x in PARTS]
    if args.with_port:
        runs.append(("on", "", "port"))
    if args.only:
        runs = [r for r in runs if f"{r[0]}:{r[1]}" + ("" if r[2] == "legacy" else f":{r[2]}")
                in args.only.split(";")]
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"

    def one(r: tuple[str, str, str]) -> dict[str, Any]:
        cmd = [sys.executable, str(HERE), "one", "--arm", r[0], "--parts", r[1], "--world", args.world,
               "--agents", str(args.agents), "--seed", str(args.seed), "--start", args.start,
               "--decision-port", r[2]]
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(REPO))
        if p.returncode != 0:
            return {"arm": r[0], "parts": r[1], "decision_port": r[2], "error": p.stderr[-3000:]}
        return json.loads(p.stdout.strip().splitlines()[-1])

    got = []
    with cf.ThreadPoolExecutor(max_workers=int(args.jobs)) as ex:
        for row in ex.map(one, runs):
            got.append(row)
            print(row.get("arm"), row.get("parts"), row.get("final"), row.get("calls"), (row.get("error") or "")[-300:],
                  flush=True)
    doc = {"tool": "ec21/tools/stage2_two_day.py", "agents": args.agents, "seed": args.seed, "start": args.start,
           "runs": got}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    """``side`` の JSON → 記録の表の行(Markdown)。"""
    doc = json.loads(Path(args.src).read_text(encoding="utf-8"))
    print("| 腕・部品 | final | 呼数 | 行/体/日(0・1 日目) | 溢れ | 保存則 残差 | 賃金(人・円) | 引き出し(回・円) | "
          "口座の購入・食事(行・円) | IC(行) | 税(円) | 来街者の口座(体) | 世帯の現金の 1 体の増減(0・1 日目) | conserved |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in doc["runs"]:
        if "error" in r:
            print(f"| {r['arm']} {r['parts']} | 失敗 | | | | | | | | | | | | |")
            continue
        s2 = r.get("stage2") or {}
        w, wd, pm, tx, en = (s2.get(k, {}) for k in ("wages", "withdraw", "payment", "tax", "endow"))
        label = r["arm"] if r["arm"] == "off" else ("on(全部)" if len(r["parts"]) == len(PARTS) else
                                                    "on − " + ",".join(p for p in PARTS if p not in r["parts"]))
        if r.get("decision_port", "legacy") != "legacy":
            label += f"・口 {r['decision_port']}"
        rows = "・".join(str(d["rows_per_agent"]) for d in r["daily"])
        over = sum(int(d.get("overflow") or 0) for d in r["daily"])
        res = "・".join(str((d.get("conservation") or {}).get("residual")) for d in r["daily"])
        cash = "・".join(str(d["cash_per_agent_change"]) for d in r["daily"])
        print(f"| {label} | {r['final']} | {r['calls']:,} | {rows} | {over} | {res} | "
              f"{w.get('paid', 0):,}・{w.get('amount', 0):,} | {wd.get('count', 0):,}・{wd.get('amount', 0):,} | "
              f"{pm.get('account_rows', 0):,}・{pm.get('account_amount', 0):,} | {pm.get('fare_ic_rows', 0):,} | "
              f"{tx.get('amount', 0):,} | {en.get('visitor_rows', 0):,} | {cash} | {r['conserved']} |")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp0 = sub.add_parser("summary")
    sp0.add_argument("--src", required=True)
    for name in ("one", "side"):
        sp = sub.add_parser(name)
        sp.add_argument("--world", default="data/world/v2")
        sp.add_argument("--agents", type=int, default=5_000)
        sp.add_argument("--seed", type=int, default=1)
        sp.add_argument("--start", default="2026-08-24")
        if name == "one":
            sp.add_argument("--arm", default="on")
            sp.add_argument("--parts", default="")
            sp.add_argument("--decision-port", default="legacy")
        else:
            sp.add_argument("--out", required=True)
            sp.add_argument("--jobs", type=int, default=4)
            sp.add_argument("--only", default="")
            sp.add_argument("--with-port", action="store_true")
    args = ap.parse_args(argv)
    return {"one": cmd_one, "side": cmd_side, "summary": cmd_summary}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
