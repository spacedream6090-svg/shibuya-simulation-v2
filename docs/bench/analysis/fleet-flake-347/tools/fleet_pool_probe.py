"""揺れた試験の「答えが 1 件も返らなくなる」形を、時間切れを縮めて手元で再現し、詰まっている側を切り分ける(読むだけ)。
使い方(リポの根で・PYTHONPATH=src):
  python docs/bench/analysis/fleet-flake-347/tools/fleet_pool_probe.py <直すまでの秒> <e2e の秒> [<刻みの数> [<形> [<見張りの間隔の秒>]]]
  形= as_is(試験と同じ組み立て)/ x4(接続の上限を 64 に)/ unbounded(接続の上限なし)。x4 と unbounded は、src を変えずに
  transport_factory から上限だけを替える(対策の候補が効くかを見るため)。
ランの間、別のスレッドが見張りの間隔(既定 4 秒)ごとに次を出す:
  - 偽サーバーへ届いた要求の数(サーバーごと)
  - 偽サーバーへ、標準ライブラリで直に GET /v1/models を送ったときの所要(サーバーが受け付けているか)
  - 艦隊の口の、レプリカごとの httpcore の接続の置き場の表示(private な属性を読むだけ)と、実行中の数
"""
from __future__ import annotations

import sys
import threading
import time
import urllib.request

sys.path.insert(0, ".")
from tests.engine import test_fleet_wiring as T  # noqa: E402
from tests.llm.test_fleet import FakeVLLM  # noqa: E402

heal_s = float(sys.argv[1])
e2e_s = float(sys.argv[2])
n_steps = int(sys.argv[3]) if len(sys.argv) > 3 else 30
mode = sys.argv[4] if len(sys.argv) > 4 else "as_is"  # as_is / unbounded(接続の上限なし) / x4(上限 4 倍)


def say(line: str) -> None:
    sys.stdout.buffer.write((line + "\n").encode("utf-8"))
    sys.stdout.flush()


servers = [FakeVLLM(), FakeVLLM(), FakeVLLM()]
stop = threading.Event()
try:
    for s in servers:
        s.total_delay_s = 1.0
    if mode == "as_is":
        client = T.make_client(servers, e2e_timeout_s=e2e_s, ttft_timeout_s=e2e_s)
    else:
        import httpx
        from shibuya.runtime.inference.fleet import FleetClient, FleetConfig
        from shibuya.foundation.manifest.schema import Mode

        lim = httpx.Limits(max_connections=None if mode == "unbounded" else 64, max_keepalive_connections=16, keepalive_expiry=None)
        cfg = FleetConfig(endpoints=tuple(x.endpoint for x in servers), model=servers[0].model, mode=Mode.SMOKE, run_id="wiring-test",
                          run_seed=1, per_replica_in_flight=16, queue_capacity=256, ttft_timeout_s=e2e_s, e2e_timeout_s=e2e_s,
                          connect_timeout_s=5.0, stream=False, latency_samples=1000)
        client = FleetClient(cfg, transport_factory=lambda ep: httpx.AsyncHTTPTransport(limits=lim))
    t0 = time.monotonic()

    def _heal() -> None:
        time.sleep(heal_s)
        for s in servers:
            s.total_delay_s = 0.0
        say(f"[{time.monotonic() - t0:6.2f}] healed server_requests={[s.n_requests for s in servers]}")

    def _direct(s: FakeVLLM) -> str:
        t = time.monotonic()
        try:
            with urllib.request.urlopen(s.endpoint + "/v1/models", timeout=3.0) as r:
                r.read()
            return f"ok {time.monotonic() - t:.3f}s"
        except Exception as exc:  # noqa: BLE001
            return f"{type(exc).__name__} {time.monotonic() - t:.3f}s"

    def _watch() -> None:
        while not stop.wait(float(sys.argv[5]) if len(sys.argv) > 5 else 4.0):
            pools = []
            for rep in getattr(client, "_replicas", []):
                try:
                    pools.append(repr(rep.client._transport._pool))
                except Exception as exc:  # noqa: BLE001
                    pools.append(f"<{type(exc).__name__}: {exc}>")
            say(f"[{time.monotonic() - t0:6.2f}] server_requests={[s.n_requests for s in servers]} "
                f"direct={[_direct(s) for s in servers]} in_flight={client.in_flight} outstanding={client.outstanding}")
            for p in pools:
                say("         " + p)

    threading.Thread(target=_heal, daemon=True).start()
    threading.Thread(target=_watch, daemon=True).start()
    res = T.run_fleet(client, ticks=n_steps, fleet_wait_s=1.0)
    stop.set()
    # ランの後の置き場の表示。ランが艦隊の口を閉じるとレプリカの一覧は空になるので、今の呼び方では何も出ない
    # (記録の出力にも「after」の行は無い)。口を閉じない呼び方に変えたときのために残している
    time.sleep(1.5)
    for rep in getattr(client, "_replicas", []):
        try:
            say("  after " + repr(rep.client._transport._pool))
        except Exception as exc:  # noqa: BLE001
            say(f"  after <{type(exc).__name__}: {exc}>")
    c = res.bridge_counters
    keys = ("fleet_calls", "fleet_ok", "fleet_answered", "fleet_deferred_timeout", "fleet_deferred_queue_full", "fleet_error_other",
            "fleet_conn_retry_same", "fleet_conn_retry_other")
    say(f"[{time.monotonic() - t0:6.2f}] end " + " ".join(f"{k}={c.get(k)!r}" for k in keys)
        + f" server_requests={[s.n_requests for s in servers]}")
finally:
    stop.set()
    for s in servers:
        s.close()
