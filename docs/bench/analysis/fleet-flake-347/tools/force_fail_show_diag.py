"""試験の関数をそのまま呼び、時間切れだけを 0.05 秒に差し替えて落とし、失敗したときの表示(assert の文)を見る(手元の確かめ・読むだけ)。
使い方(リポの根で・PYTHONPATH=src): python docs/bench/analysis/fleet-flake-347/tools/force_fail_show_diag.py
試験のファイルは書き換えない(このプロセスの中で、艦隊の口を作る関数だけを差し替える)。約 45 秒かかる。
"""
from __future__ import annotations

import sys
import time

sys.path.insert(0, ".")
from tests.engine import test_fleet_wiring as T  # noqa: E402
from tests.llm.test_fleet import FakeVLLM  # noqa: E402

servers = [FakeVLLM(), FakeVLLM(), FakeVLLM()]
orig = T.make_client
T.make_client = lambda srv, **kw: orig(srv, **{**kw, "e2e_timeout_s": 0.05, "ttft_timeout_s": 0.05})
t0 = time.monotonic()
try:
    T.test_timeout_defers_then_reinjects_and_is_finally_answered(servers)
    out = "passed (no failure)"
except AssertionError as exc:
    out = "AssertionError:\n" + str(exc)
finally:
    for s in servers:
        s.close()
sys.stdout.buffer.write((out + f"\nwall={time.monotonic() - t0:.1f}s\n").encode("utf-8"))
