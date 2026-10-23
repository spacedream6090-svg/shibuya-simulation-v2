"""第 1 期 1-5: 権利台帳を作る時間と大きさ(5,000 体の抽出と全母集団・POI 2,337)と、開閉の口の権利の問い合わせの時間。

使い方(リポの根で・src を ``PYTHONPATH`` に): ``python <この置き場>/time_rights_r15.py``。壁時計は目安(記録に書く)。
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

from shibuya.agents.population import load_population
from shibuya.engine.rights import initial as RI
from shibuya.engine.systems.build import _org_of_agent

WORLD = Path("data/world/v2")


def main() -> int:
    n_poi = pq.read_metadata(WORLD / "w6_poi.parquet").num_rows
    out = {}
    for label, n in (("5000", 5_000), ("full", None)):
        pop = load_population(WORLD, n, 1)
        org = _org_of_agent(pop, pop.n)
        t0 = time.perf_counter()
        led = RI.build_initial(pop.kind, n_poi, org)
        build_s = time.perf_counter() - t0
        t0 = time.perf_counter()
        staff = RI.staff_of_poi(led, n_poi, 0)
        read_s = time.perf_counter() - t0
        stores = np.arange(n_poi)[:20]
        t0 = time.perf_counter()
        for _ in range(288):  # 開閉の評価は 5 分ごと=1 日 288 回(1 回 20 行)
            led.holds_each(staff[stores], stores, kind="employ", holder_kind="agent", object_kind="store", t_ns=0)
        ask_s = time.perf_counter() - t0
        c = led.counts()
        out[label] = {"agents": int(pop.n), "rows": c["rows"], "bytes": c["bytes"], "by_kind": c["by_kind"],
                      "build_s": round(build_s, 3), "staff_read_s": round(read_s, 4),
                      "holds_each_288_s": round(ask_s, 3)}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
