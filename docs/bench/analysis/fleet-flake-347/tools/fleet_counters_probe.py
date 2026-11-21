"""揺れた試験(test_timeout_defers_then_reinjects_and_is_finally_answered)と同じ呼び方で回し、表示に足した数を手元で見る(読むだけ)。
使い方(リポの根で・PYTHONPATH=src):
  python docs/bench/analysis/fleet-flake-347/tools/fleet_counters_probe.py <直すまでの秒> [<run_day の前に待つ秒> [<e2e の秒>]]
2 つ目の引数は、偽サーバーを直す時計を先に進めておく秒(組み立てが遅い実行機のまね)。3 つ目は時間切れの秒(既定 0.2=試験と同じ。
縮めると、遅い実行機のまねになる)。
"""
from __future__ import annotations

import sys
import threading
import time

sys.path.insert(0, ".")
from tests.engine import test_fleet_wiring as T  # noqa: E402
from tests.llm.test_fleet import FakeVLLM  # noqa: E402

heal_s = float(sys.argv[1])
pre_s = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
e2e_s = float(sys.argv[3]) if len(sys.argv) > 3 else 0.2
servers = [FakeVLLM(), FakeVLLM(), FakeVLLM()]
try:
    for s in servers:
        s.total_delay_s = 1.0
    client = T.make_client(servers, e2e_timeout_s=e2e_s, ttft_timeout_s=e2e_s)
    healed: dict = {}
    t0 = time.monotonic()

    def _heal() -> None:
        time.sleep(heal_s)
        for s in servers:
            s.total_delay_s = 0.0
        healed["at_s"] = round(time.monotonic() - t0, 2)
        healed["server_requests"] = [s.n_requests for s in servers]

    th = threading.Thread(target=_heal, daemon=True)
    th.start()
    if pre_s:
        time.sleep(pre_s)
    res = T.run_fleet(client, ticks=90, fleet_wait_s=1.0)
    wall = time.monotonic() - t0
    c = res.bridge_counters
    keys = ("fleet_calls", "fleet_ok", "fleet_answered", "fleet_deferred_timeout", "fleet_deferred_queue_full", "fleet_error_other",
            "fleet_conn_retry_same", "fleet_conn_retry_other", "fleet_resent", "fleet_reinjected", "fleet_outstanding")
    out = {k: c.get(k) for k in keys}
    out.update(e2e_s=e2e_s, run_wall_s=round(wall, 2), healed_at_s=healed.get("at_s"), server_requests_at_heal=healed.get("server_requests"),
               server_requests_at_end=[s.n_requests for s in servers], unanswered_at_end=res.fleet_unanswered_at_end)
    sys.stdout.buffer.write((" ".join(f"{k}={v!r}" for k, v in out.items()) + "\n").encode("utf-8"))
finally:
    for s in servers:
        s.close()
