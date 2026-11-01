"""第 1 期 1-9 K17 の数(輪の容量・バイト・宣言の投影・HEAD の係数 3.0 との差)を JSON に書く道具。

使い方(リポの根で・作業木の src を読む): ``python docs/bench/analysis/wallbounce-1012/cp2/tools/k17_numbers.py <出力の JSON>``

- 体数 5,000(byte-check の規模)と 390,067(C7 の規模)。保持窓 1 日。
- ``transfer_log``(輪の 7 列 24 B/行)と ``transfer_log_event_ids``(目印の列 12 B/行)・物の ``delivery_log_event_ids``。
- 宣言の投影=``GrowthDeclaration.declared_projected_bytes(30, N)``(D-R2-6・保持窓 1 日なので 1 日ぶん)と
  ``check_growth`` の ``declared_over_cap``(宣言だけで cap 超過の行)。

逐次ループ宣言: なし(道具)。
"""

from __future__ import annotations

import json
import sys

import numpy as np

from shibuya.core.growth import check_growth
from shibuya.economy import ledger as LED
from shibuya.economy.goods import GoodsLedger
from shibuya.engine.ledger_api import LedgerBundle


def numbers(n: int, rate: float) -> dict:
    old = LED.TRANSFERS_PER_AGENT_PER_DAY
    LED.TRANSFERS_PER_AGENT_PER_DAY = rate  # type: ignore[misc]
    try:
        led = LED.Ledger(n, 8)
        goods = GoodsLedger.from_pois(np.zeros(8, dtype=np.int64), np.full(8, 5), np.full(8, 300), n_agents=n)
        decls, measured = LedgerBundle(money=led, goods=goods).growth_parts()
        rep = check_growth(decls, measured, steps=1_440, minutes_per_step=1, n_entities=n)
        rows = {}
        for name in ("transfer_log", "transfer_log_event_ids", "delivery_log", "delivery_log_event_ids"):
            d = decls[name]
            rows[name] = {"cap_bytes": int(d.cap), "per_day_growth_coef": float(d.per_day_growth_coef),
                          "declared_projection_bytes": float(d.declared_projected_bytes(30, n))}
        return {"n_agents": n, "rate": rate, "raw_capacity_rows": int(led.raw_capacity),
                "ring_bytes_7_columns": int(led.raw_capacity) * LED.RAW_ROW_BYTES,
                "ring_bytes_link_columns": int(led.raw_capacity) * LED.RAW_LINK_BYTES,
                "declared_over_cap": list(rep.declared_over_cap), "growth_ok": bool(rep.ok), "rows": rows}
    finally:
        LED.TRANSFERS_PER_AGENT_PER_DAY = old  # type: ignore[misc]


def main(out: str) -> int:
    doc = {"note": "第 1 期 1-9 K17: 金の生ログの輪の係数 6.5 行/体/日(HEAD 3.0)・保持窓 1 日",
           "k17": {"measured_rows_per_agent_day": LED.MEASURED_TRANSFERS_PER_AGENT_DAY, "margin": LED.K17_MARGIN,
                   "lower_bound": LED.MEASURED_TRANSFERS_PER_AGENT_DAY * LED.K17_MARGIN,
                   "rate": LED.TRANSFERS_PER_AGENT_PER_DAY},
           "rows": [numbers(n, r) for n in (5_000, 390_067) for r in (3.0, 6.5)]}
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
    for r in doc["rows"]:
        print(r["n_agents"], r["rate"], r["raw_capacity_rows"], r["ring_bytes_7_columns"], r["ring_bytes_link_columns"],
              r["declared_over_cap"], r["growth_ok"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
