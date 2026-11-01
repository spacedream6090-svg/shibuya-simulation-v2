"""4-2: 給料日を含む 2 日のラン(08-24 から)の動いた量と性能を 1 行の JSON に(使い捨て)。

python runs_rules42.py <out.json> [config]   (PYTHONPATH で src を選ぶ・SHIBUYA_RULES_42 で腕)
"""
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[6]
W2 = REPO / "docs/bench/analysis/wave2-2026-09-30/wave2_bytecheck.py"
sys.path.insert(0, str(REPO / "docs/bench/analysis/wallbounce-1012/pop43/tools"))
from runs_pop43 import _peak_working_set_bytes  # noqa: E402


def main() -> None:
    out = Path(sys.argv[1])
    cfg = sys.argv[2] if len(sys.argv) > 2 else "w6_v3_default"
    spec = importlib.util.spec_from_file_location("wave2_bytecheck", W2)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["wave2_bytecheck"] = mod
    spec.loader.exec_module(mod)
    kw = dict(mod.configs()[cfg])
    kw.update(sim_days=2, start_sim_datetime="2026-08-24")
    from shibuya import cli
    from shibuya.economy.accounts import AccountCode, BalanceLine, Sector

    t0 = time.perf_counter()
    res = cli.run(n_agents=5_000, seed=1, world_dir="data/world/v2", **kw)
    wall = time.perf_counter() - t0
    peak = _peak_working_set_bytes()
    led = res.ledger.money
    s2 = led.stage2
    f = sum(np.asarray(x) for x in led.flow_daily)

    def fl(code, a, b):
        return int(f[int(a), int(b), int(code)])

    H, S, E, G, W = Sector.HOUSEHOLD, Sector.STORE, Sector.EMPLOYER, Sector.GOVERNMENT, Sector.ROW
    run = s2.s2_meter["run"]
    dep = getattr(s2, "tax_deposit", None)
    m = res.run_manifest_fields()
    days = [{"day": d["day"], "conservation": d["economy"]["conservation"],
             "deposit_check": d["economy"]["stage2"]["tax"].get("deposit_check"),
             "held_balance": d["economy"]["stage2"]["tax"].get("held_balance")} for d in m["daily"]]
    calls = res.calls_by_model if hasattr(res, "calls_by_model") else None
    doc = {
        "config": cfg, "rules_42": os.environ.get("SHIBUYA_RULES_42", "(既定)"), "final": res.final_hash[:16],
        "src_is_worktree": Path(__import__("shibuya").__file__).resolve().parents[1] == (REPO / "src").resolve(),
        "llm_calls": int(res.llm_calls), "calls_by_model": calls, "wall_s": round(wall, 1), "peak_rss_bytes": peak,
        "ticks": int(m.get("ticks", 0) or 0) if isinstance(m.get("ticks"), int) else None,
        "wages": {k: int(v) for k, v in run["wages"].items()},
        "tax": {k: int(v) for k, v in run["tax"].items()},
        "flows": {"wage_E_H": fl(AccountCode.WAGE, E, H), "wage_S_H": fl(AccountCode.WAGE, S, H),
                  "wage_W_H": fl(AccountCode.WAGE, W, H), "funding_W_E": fl(AccountCode.CONSUMPTION, W, E),
                  "funding_W_S": fl(AccountCode.CONSUMPTION, W, S), "tax_H_G": fl(AccountCode.TAX, H, G),
                  "tax_E_G": fl(AccountCode.TAX, E, G), "tax_S_G": fl(AccountCode.TAX, S, G)},
        "government_cash": int(np.asarray(led.balance(BalanceLine.CASH, G))[0]),
        "household_deposit_total": int(np.asarray(led.balance(BalanceLine.DEPOSIT, H)).sum()),
        "store_cash_total": int(np.asarray(led.balance(BalanceLine.CASH, S)).sum()),
        "employer_cash_total": int(np.asarray(led.balance(BalanceLine.CASH, E)).sum()),
        "deposit": None if dep is None else dep.record(),
        "rules": {k: v for k, v in s2.s2_meter["rules"].items() if k in ("payroll_deductions", "invoice_rounding")},
        "days": days, "conserved": bool(res.conserved),
        "phase_seconds": {k: round(float(v), 2) for k, v in (res.phase_seconds or {}).items()
                          if isinstance(v, (int, float))},
    }
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    print(doc["final"], doc["wall_s"], doc["flows"])


if __name__ == "__main__":
    main()
