"""賃金の段の準備: 5,000 体 mock 1 日の所持金の減り方を測る(src は編集しない・読むだけ)。

使い方(リポジトリ直下で):
    PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe docs/bench/analysis/wallbounce-1003/wage/measure_day.py [体数] [seed]

出力: 同じフォルダの measure_day_<体数>_s<seed>.json(新規名・上書きは同じ条件の再実行だけ)。
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

import shibuya.cli as CLI
from shibuya.economy.accounts import ACCOUNT_NAMES, SECTOR_NAMES, AccountCode, BalanceLine, Sector
from shibuya.engine import resolve as R

N = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 1
OUT = Path(__file__).with_name(f"measure_day_{N}_s{SEED}.json")

captured: dict = {}
_orig_bundle = CLI.build_ledger_bundle
_orig_init = R.initialize


def _bundle(*a, **k):
    b = _orig_bundle(*a, **k)
    captured["bundle"] = b
    led = b.money
    # 参入資本(外界→店舗)は build の時点で入っている
    captured["store_cash_after_endow"] = int(led.balance(BalanceLine.CASH, Sector.STORE).sum())
    return b


def _init(agents, world, schedule, **k):
    _orig_init(agents, world, schedule, **k)
    captured["agents"] = agents
    captured["money0"] = np.asarray(agents.registry.money, dtype=np.int64).copy()
    captured["kind"] = np.asarray(agents.registry.field("kind"), dtype=np.int64).copy()


CLI.build_ledger_bundle = _bundle
R.initialize = _init

t0 = time.time()
res = CLI.run(n_agents=N, seed=SEED)
wall = time.time() - t0

led = captured["bundle"].money
money0 = captured["money0"]
money1 = np.asarray(led.balance(BalanceLine.CASH, Sector.HOUSEHOLD), dtype=np.int64)
kind = captured["kind"]
flows = led.flow_daily
flow = sum(flows) if flows else led.flow
names = {int(c): ACCOUNT_NAMES[int(c)] for c in AccountCode}
by_pair = []
for ps in range(6):
    for qs in range(6):
        for c in range(flow.shape[2]):
            v = int(flow[ps, qs, c])
            if v:
                by_pair.append({"from": SECTOR_NAMES[ps], "to": SECTOR_NAMES[qs], "account": names[c], "amount": v})

per_kind = {}
for k in np.unique(kind):
    m = kind == k
    per_kind[int(k)] = {
        "n": int(m.sum()),
        "money_start_sum": int(money0[m].sum()),
        "money_end_sum": int(money1[m].sum()),
        "money_start_median": float(np.median(money0[m])),
        "money_end_median": float(np.median(money1[m])),
        "n_end_below_1000": int((money1[m] < 1000).sum()),
        "n_end_zero": int((money1[m] <= 0).sum()),
    }

out = {
    "n_agents": N,
    "seed": SEED,
    "wall_seconds": round(wall, 1),
    "ticks": int(res.ticks),
    "household_money_start": int(money0.sum()),
    "household_money_end": int(money1.sum()),
    "household_money_delta": int(money1.sum() - money0.sum()),
    "household_money_delta_per_agent": float((money1.sum() - money0.sum()) / max(1, N)),
    "store_cash_after_endow": captured["store_cash_after_endow"],
    "sector_cash_end": {SECTOR_NAMES[s]: int(v) for s, v in enumerate(led.sector_totals(BalanceLine.CASH))},
    "sector_deposit_end": {SECTOR_NAMES[s]: int(v) for s, v in enumerate(led.sector_totals(BalanceLine.DEPOSIT))},
    "ledger_sizes": list(led.sizes),
    "flows_by_pair": by_pair,
    "account_totals": led.account_totals(flow),
    "rejections": {str(k): int(v) for k, v in led.rejections.items()},
    "n_transfers": int(led.n_transfers),
    "money_supply_end": int(led.money_supply()),
    "fares_paid": int(getattr(res, "fares_paid", 0)),
    "census_row": {k: (v if isinstance(v, (int, float, bool, str)) else str(v)) for k, v in res.census_row.items()},
    "per_kind": per_kind,
    "n_end_zero": int((money1 <= 0).sum()),
}
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print(json.dumps({k: out[k] for k in ("wall_seconds", "household_money_start", "household_money_end",
                                       "household_money_delta", "account_totals")}, ensure_ascii=False))
