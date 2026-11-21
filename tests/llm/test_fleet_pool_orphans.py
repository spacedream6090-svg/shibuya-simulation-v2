"""艦隊の口の接続の置き場(httpcore のプール)に、使われない接続が残って詰まる件の試験(第348・返事その 9 §5-2 の 1)。

記録: ``docs/bench/analysis/fleet-flake-347/README.md``。

httpcore 1.0.9 の ``AsyncConnectionPool`` は、置き場で待っていた要求に新しい接続を割り当てた後、その要求が
送り始める前に取り消されると、要求だけを外して接続を一覧に残す。残った接続は閉じられも使い回されもせず、
上限まで溜まると、健全な相手に対しても全部の要求が置き場で待ったままになる。

この試験は、本物の ``httpx``/``httpcore`` の置き場を通し、時計に頼らずに順を決めてこの形を作る。

- 置き場を満たす「持ち手」の要求は、接続を受けるだけで何も返さない相手(listen だけして accept しない
  ソケット)へ送る。持ち手は取り消すまで返らない。
- 置き場が満ちた後に「取り消される側」の要求を入れ、置き場で待たせる。
- 持ち手を 1 つ取り消すと、置き場は空いた枠で新しい接続を作り、待っていた要求に割り当てる。
  割り当ての直前に置き場が呼ぶ ``create_connection`` に印を付け、そこで待っていた要求を取り消す。
  こうすると、割り当てと取り消しの順が、時計や負荷によらず毎回同じになる。
- 待つのは、置き場の状態が変わること(イベントループを 1 周ずつ回して確かめる)だけ。回す数に保険の上限を付ける。

段 A は httpcore そのものの不具合の再現、段 B は ``FleetClient`` がその状態から回復して答えることを確かめる。
置き場の中身は httpx と httpcore の private な属性(``AsyncClient._transport._pool``・``_requests``・
``_max_connections``)を読む。この試験の中だけで読み、src からは読まない。
"""

from __future__ import annotations

import asyncio
import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable

import httpx

from shibuya.foundation.manifest.schema import Mode
from shibuya.foundation.ports.inference import LLMResult, Outcome
from shibuya.runtime.inference import fleet as F
from shibuya.runtime.inference.fleet import FleetClient, FleetConfig

from tests.llm.test_fleet import GOOD, FakeVLLM, mkcall

#: 置き場の状態が変わるのを待つときに、イベントループを回す数の保険の上限(時計ではなく回数で区切る)。
_LOOP_TURNS_CAP = 20_000
#: 持ち手が応答を待つ所まで進むのを待つときの保険の上限(秒)。普段は数ミリ秒で進む。結果には効かない。
_HOLD_READY_CAP_S = 5.0


class _NoAnswerServer:
    """接続は受けるが、何も読まず何も返さない相手(listen だけして accept しない)。

    TCP の接続は OS が受け付けるので、要求は送れる。応答は来ないので、要求は取り消すまで返らない。
    """

    def __init__(self) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(64)

    @property
    def url(self) -> str:
        host, port = self.sock.getsockname()[:2]
        return f"http://{host}:{port}/hold"

    def close(self) -> None:
        self.sock.close()


def _pool_of(client: httpx.AsyncClient) -> Any:
    """httpx の AsyncClient が持つ httpcore の置き場(private な属性を読む)。"""
    return client._transport._pool  # type: ignore[attr-defined]


def _conn_states(pool: Any) -> dict[str, int]:
    """置き場の接続を状態ごとに数える(``CONNECTING`` は張っていない接続、``NEW`` は張ったがまだ送っていない接続)。"""
    out: dict[str, int] = {}
    for conn in pool.connections:
        info = conn.info()
        parts = [p.strip() for p in info.split(",")]
        key = parts[2] if len(parts) >= 3 else info
        out[key] = out.get(key, 0) + 1
    return dict(sorted(out.items()))


def _queued(pool: Any) -> int:
    """置き場で接続を待っている要求の数。"""
    return sum(1 for r in pool._requests if r.is_queued())


async def _until(pred: Callable[[], bool], what: str) -> None:
    """``pred`` が真になるまでイベントループを 1 周ずつ回す(保険の上限つき)。"""
    for _ in range(_LOOP_TURNS_CAP):
        if pred():
            return
        await asyncio.sleep(0)
    raise AssertionError(f"置き場が {what} にならなかった(ループを {_LOOP_TURNS_CAP} 周回した)")


def _mark_waiting(ev: asyncio.Event) -> Callable[[str, Any], Any]:
    """httpcore の trace の印を受け、応答の見出しを待ち始めたら ``ev`` を立てる。"""

    async def trace(event_name: str, info: Any) -> None:
        if event_name == "http11.receive_response_headers.started":
            ev.set()

    return trace


async def _settle(task: asyncio.Future) -> str:
    """終わるのを待ち、終わり方の名を返す(取り消しは ``CancelledError``)。"""
    try:
        await task
    except BaseException as exc:  # noqa: BLE001 - 終わり方の名だけを見る
        return type(exc).__name__
    return "done"


async def _leave_orphans(
    client: httpx.AsyncClient, hold_url: str, victim_url: str, n_orphans: int
) -> list[str]:
    """``client`` の置き場に、割り当て直後に取り消された接続を ``n_orphans`` 本残す。

    1 本ごとに: 空いた枠を全部持ち手で埋める → 取り消される側を置き場で待たせる → 持ち手を 1 つ取り消す →
    置き場が新しい接続を作って割り当てる直前に、取り消される側を取り消す → 残りの持ち手を取り消す。
    返り値は、取り消される側の終わり方の名(1 本につき 1 つ)。
    """
    pool = _pool_of(client)
    box: dict[str, asyncio.Future] = {}
    real_create = pool.create_connection

    def create_and_cancel(origin: Any) -> Any:
        conn = real_create(origin)
        victim = box.pop("victim", None)
        if victim is not None:
            victim.cancel()  # 割り当ての直前に取り消す(この後、置き場はこの接続を victim に割り当てる)
        return conn

    pool.create_connection = create_and_cancel
    endings: list[str] = []
    try:
        for _ in range(n_orphans):
            free = pool._max_connections - len(pool.connections)
            waiting = [asyncio.Event() for _ in range(free)]
            # 要求ごとの時間切れは保険の上限(秒)にする。段 B では client が FleetClient の短い時間切れを持つので、
            # それを使うと、ループが止まったときに持ち手や取り消される側が先に切れ、結果が時計に左右される
            holders = [
                asyncio.ensure_future(
                    client.post(hold_url, content=b"hold", timeout=httpx.Timeout(_HOLD_READY_CAP_S),
                                extensions={"trace": _mark_waiting(ev)})
                )
                for ev in waiting
            ]
            # 持ち手が全部、接続を張り、要求を送り、応答を待つ所まで進むのを待つ(httpcore の trace の印=イベント)。
            # 接続を張っている途中で取り消すと、取り消しが効かずに読みの時間切れまで進む回があったので、避ける
            await asyncio.wait_for(asyncio.gather(*(ev.wait() for ev in waiting)), _HOLD_READY_CAP_S)
            assert len(pool.connections) == pool._max_connections, "持ち手が置き場を満たしていない"
            victim = asyncio.ensure_future(
                client.post(victim_url, content=b"victim", timeout=httpx.Timeout(_HOLD_READY_CAP_S))
            )
            await _until(lambda: _queued(pool) == 1, "要求 1 つが待つ形")
            box["victim"] = victim
            holders[0].cancel()
            endings.append(await _settle(victim))
            for h in holders[1:]:
                h.cancel()
            for h in holders:
                await _settle(h)
            assert "victim" not in box, "置き場が新しい接続を作らなかった(取り消される側に割り当てが起きていない)"
    finally:
        del pool.create_connection  # インスタンスに付けた印を外す(クラスの関数に戻る)
    return endings


# ------------------------------------------------------------------ 段 A(上流の不具合の再現)


def test_stage_a_httpcore_pool_keeps_a_connection_assigned_then_cancelled():
    """段 A: httpcore の置き場は、割り当て直後に取り消された要求の接続を残す(上流の不具合)。

    上流: encode/httpcore PR #1099「Reclaim connections orphaned by a cancelled request」(読んだ時点で未マージ)。
    この試験は、上流の不具合が今の版にあることを数で確かめる(残る接続の数・置き場が詰まること)。
    直しの入った版が出たら、依存の版を固定するロックのファイル(返事その 9 §1 の 13)で上げる。そのときこの試験は
    落ちる(残る数が 0 になり、置き場は詰まらない)。**試験は消さずに、期待を「残らない」に直す**(段 B は残す)。
    """
    hold = _NoAnswerServer()

    async def main() -> tuple[list[str], dict[str, int], int, str]:
        transport = httpx.AsyncHTTPTransport(
            limits=httpx.Limits(max_connections=2, max_keepalive_connections=2)
        )
        async with httpx.AsyncClient(transport=transport, timeout=httpx.Timeout(5.0)) as client:
            pool = _pool_of(client)
            endings = await _leave_orphans(client, hold.url, hold.url, n_orphans=2)
            states = _conn_states(pool)
            waiting = len(pool._requests)
            # 置き場が詰まっているか: 置き場で待つ時間を 0 にした要求は、空きが無ければ PoolTimeout になる。
            # (上流が直っていれば接続を得て、何も返さない相手を待って ReadTimeout になる)
            try:
                await client.post(hold.url, content=b"probe", timeout=httpx.Timeout(1.0, pool=0.0))
                probe = "answered"
            except httpx.TimeoutException as exc:
                probe = type(exc).__name__
            return endings, states, waiting, probe

    try:
        endings, states, waiting, probe = asyncio.run(main())
    finally:
        hold.close()
    diag = f"\nendings={endings}\nconn_states={states}\nrequests_left={waiting}\nprobe={probe}"
    assert endings == ["CancelledError", "CancelledError"], diag
    assert waiting == 0, diag  # 要求は置き場から外れている
    assert states == {"CONNECTING": 2}, diag  # 接続だけが、張られないまま 2 本残る(上流の不具合)
    assert probe == "PoolTimeout", diag  # 上限 2 本が埋まり、次の要求は接続を得られない


# ------------------------------------------------------------------ 段 B(艦隊の口が回復して答える)


#: 段 B の 1 試行の締め切り(秒)。詰まった置き場で待つ試行は、この秒数で時間切れになる。
#: 結果は秒数によらない(詰まった置き場は待っても空かない)。短いのは試験を 5 秒以内に終えるため。
_STAGE_B_E2E_S = 0.25
#: 呼を 1 つずつ出して回収する回数の上限。回復までに要る呼の数より十分に大きく取る。
_STAGE_B_ROUNDS = 6


def test_stage_b_fleet_client_recovers_from_a_pool_full_of_orphans():
    """段 B: レプリカの置き場が、割り当て直後に取り消された接続で満杯になっても、艦隊の口は回復して答える。

    1 レプリカ(別レプリカへの送り直しが無い形)の ``FleetClient`` の置き場を、段 A と同じ順で満杯にしてから、
    健全な偽 vLLM へ呼を 1 つずつ出す。直す前の口は、置き場が空かないので 1 件も答えない(赤)。
    """
    fake = FakeVLLM()
    hold = _NoAnswerServer()
    cfg = FleetConfig(
        endpoints=(fake.endpoint,),
        model=fake.model,
        mode=Mode.SMOKE,
        run_id="pool-orphans",
        per_replica_in_flight=1,
        queue_capacity=16,
        ttft_timeout_s=_STAGE_B_E2E_S,
        e2e_timeout_s=_STAGE_B_E2E_S,
        connect_timeout_s=5.0,
        stream=False,
        latency_samples=100,
    )
    client = FleetClient(cfg)
    rounds: list[str] = []
    try:
        client.start()
        rep = client._replicas[0]
        pool = _pool_of(rep.client)
        n_max = int(pool._max_connections)
        n_keep = int(pool._max_keepalive_connections)
        endings = asyncio.run_coroutine_threadsafe(
            _leave_orphans(rep.client, hold.url, fake.endpoint + "/v1/chat/completions", n_max),
            client._loop,  # type: ignore[arg-type]
        ).result(10.0)
        poisoned = _conn_states(pool)
        answered = 0
        for i in range(_STAGE_B_ROUNDS):
            rejected = client.submit([mkcall(i, cell=i)])
            done = client.drain(timeout=10.0)
            outs = [r.outcome.value for r in [*rejected, *done]]
            rounds.append(f"round {i}: {outs}")
            answered += sum(
                1 for r in done
                if isinstance(r, LLMResult) and r.outcome in (Outcome.OK, Outcome.ERROR_RETRIED_OK)
            )
            if answered:
                break
        c = client.counters()
    finally:
        client.close()
        hold.close()
        fake.close()
    diag = "\n".join(
        [f"n_max={n_max}", f"endings={endings}", f"poisoned={poisoned}", *rounds]
        + [f"{k}={c[k]!r}" for k in sorted(c) if k.startswith("fleet_")]
    )
    # (e) 置き場の上限と空き接続の上限は、Semaphore × 倍率(試験の中だけで httpcore の private な属性を読む)
    assert (n_max, n_keep) == (cfg.per_replica_in_flight * F.POOL_CONNECTIONS_PER_IN_FLIGHT,) * 2, "\n" + diag
    assert poisoned == {"CONNECTING": n_max}, "\n" + diag  # 置き場が満杯になった(前提)
    assert answered > 0, "\n" + diag  # 回復して答えが返る
    assert c["fleet_accounted"] == c["fleet_calls"], "\n" + diag  # 帳尻(呼を捨てない)
    assert c["fleet_client_rebuilt"] >= 1, "\n" + diag  # 回復はクライアントの作り直しによる


# ------------------------------------------------------------------ 作り直しの条件(呼を落とさない・同じ factory・全部閉じる)


class _GatedVLLM:
    """``/v1/chat/completions`` の応答を、``gate`` が立つまで止める偽 vLLM(要求が届くと ``arrived`` が立つ)。"""

    def __init__(self) -> None:
        self.arrived = threading.Event()
        self.gate = threading.Event()
        fake = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *args: Any, **kwargs: Any) -> None:
                pass

            def do_POST(self) -> None:
                n = int(self.headers.get("Content-Length", "0") or 0)
                if n:
                    self.rfile.read(n)
                fake.arrived.set()
                fake.gate.wait(_GATE_CAP_S)
                body = json.dumps({
                    "id": "x",
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": GOOD},
                                 "finish_reason": "stop"}],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 20},
                }, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self._thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self._thread.start()

    @property
    def endpoint(self) -> str:
        host, port = self.server.server_address[:2]
        return f"http://{host}:{port}"

    def close(self) -> None:
        self.gate.set()
        self.server.shutdown()
        self.server.server_close()
        self._thread.join(timeout=5.0)


#: 偽 vLLM が応答を止めておく保険の上限(秒)。試験は gate を立てて進めるので、普段はここまで待たない。
_GATE_CAP_S = 10.0


def test_rebuild_keeps_the_call_in_progress_and_closes_every_client():
    """作り直しても、古いクライアントで進行中の試行は壊さずに答えを返し、終わってから古いものを閉じる。

    作り直しでも同じ ``transport_factory`` を通す。``close()`` は、作り直した後のクライアントも、進行中の試行が
    残っていて退いたままのクライアントも、全部閉じる。時計に頼らないよう、作り直しは置き場の時間切れを
    数える口(``_note_pool_wait``)を直に呼んで起こす。
    """
    from shibuya.runtime.inference import fleet as F

    srv = _GatedVLLM()
    made: list[str] = []

    def factory(endpoint: str) -> httpx.AsyncBaseTransport:
        made.append(endpoint)
        return httpx.AsyncHTTPTransport(limits=httpx.Limits(max_connections=4, max_keepalive_connections=2))

    cfg = FleetConfig(
        endpoints=(srv.endpoint,), model="fake", mode=Mode.SMOKE, run_id="rebuild", per_replica_in_flight=2,
        queue_capacity=16, ttft_timeout_s=8.0, e2e_timeout_s=8.0, connect_timeout_s=5.0, stream=False,
        latency_samples=100,
    )
    client = FleetClient(cfg, transport_factory=factory)
    rep = None

    def rebuild_now() -> None:
        async def go() -> None:
            for _ in range(F.POOL_WAIT_TIMEOUTS_BEFORE_REBUILD):
                client._note_pool_wait(rep, rep.client)

        client._call_soon_sync(go())

    def wait_closing() -> None:
        async def go() -> None:
            await asyncio.gather(*list(client._closing), return_exceptions=True)

        client._call_soon_sync(go())

    try:
        client.start()
        rep = client._replicas[0]
        first = rep.client
        assert client.submit([mkcall(0)]) == []
        assert srv.arrived.wait(_GATE_CAP_S), "偽 vLLM に要求が届かない"
        rebuild_now()  # 進行中の試行が first に 1 つある間に作り直す
        second = rep.client
        held_while_rebuilt = (second is not first, first.is_closed, len(rep.retired))
        srv.gate.set()
        done = client.drain(timeout=_GATE_CAP_S)
        wait_closing()
        first_closed_after = first.is_closed
        # 新しいクライアントで次の呼も答える
        assert client.submit([mkcall(1)]) == []
        done2 = client.drain(timeout=_GATE_CAP_S)
        # 進行中の試行があるうちに、もう一度作り直してから close() する
        srv.gate.clear()
        srv.arrived.clear()
        assert client.submit([mkcall(2)]) == []
        assert srv.arrived.wait(_GATE_CAP_S), "偽 vLLM に要求が届かない(3 つ目)"
        rebuild_now()
        third = rep.client
        retired_at_close = list(rep.retired)
        c = client.counters()
    finally:
        client.close()
        srv.close()
    diag = (f"\nheld_while_rebuilt={held_while_rebuilt}\ndone={[(r.outcome.value, r.text) for r in done]}"
            f"\nfirst_closed_after={first_closed_after}\ndone2={[r.outcome.value for r in done2]}"
            f"\nmade={made}\nretired_at_close={len(retired_at_close)}\ncounters_rebuilt={c['fleet_client_rebuilt']}")
    assert held_while_rebuilt == (True, False, 1), diag  # 作り直した・古いものは閉じていない・退いた側に 1 つ
    assert [(r.outcome, r.text) for r in done] == [(Outcome.OK, GOOD)], diag  # 進行中の呼は答えを返した
    assert first_closed_after, diag  # 最後の試行が終わってから閉じた
    assert [r.outcome for r in done2] == [Outcome.OK], diag
    assert made == [srv.endpoint] * 3, diag  # 最初の 1 回と、作り直し 2 回で、同じ factory を通した
    assert c["fleet_client_rebuilt"] == 2.0, diag
    assert c["fleet_accounted"] == c["fleet_calls"] - c["fleet_outstanding"], diag
    assert retired_at_close == [second], diag
    assert first.is_closed and second.is_closed and third.is_closed, diag  # close() が全部閉じた


def test_success_resets_the_streak_and_late_timeouts_on_the_old_client_do_not_chain():
    """続いた数は、今のクライアントでの成功で 0 に戻る。作り直した後、古いクライアントで切れた試行は数えない。

    時計に頼らないよう、置き場の時間切れは数える口(``_note_pool_wait``)を直に呼んで起こし、成功は
    健全な偽 vLLM への本物の呼で起こす(``_run_call`` の成功の道を通す)。
    """
    n = F.POOL_WAIT_TIMEOUTS_BEFORE_REBUILD
    fake = FakeVLLM()
    cfg = FleetConfig(
        endpoints=(fake.endpoint,), model=fake.model, mode=Mode.SMOKE, run_id="streak", per_replica_in_flight=2,
        queue_capacity=16, ttft_timeout_s=8.0, e2e_timeout_s=8.0, connect_timeout_s=5.0, stream=False,
        latency_samples=100,
    )
    client = FleetClient(cfg)
    seen: list[str] = []

    def note(times: int, on: Any) -> None:
        async def go() -> None:
            for _ in range(times):
                client._note_pool_wait(rep, on)

        client._call_soon_sync(go())

    def look(label: str) -> None:
        seen.append(f"{label}: streak={rep.pool_wait_streak} rebuilt={client.counters()['fleet_client_rebuilt']}")

    try:
        client.start()
        rep = client._replicas[0]
        note(n - 1, rep.client)  # あと 1 回で作り直す所まで
        look("before_success")
        assert client.submit([mkcall(0)]) == []
        done = client.drain(timeout=_GATE_CAP_S)
        look("after_success")
        note(n - 1, rep.client)  # 成功で 0 に戻っていれば、まだ作り直さない
        look("after_more")
        old = rep.client
        note(1, rep.client)  # ここで作り直す
        look("after_rebuild")
        note(n, old)  # 古いクライアントで待っていた試行が一斉に切れた形(数えない)
        look("after_late_old")
        assert client.submit([mkcall(1)]) == []
        done2 = client.drain(timeout=_GATE_CAP_S)
        c = client.counters()
    finally:
        client.close()
        fake.close()
    diag = "\n" + "\n".join(seen) + f"\ndone={[r.outcome.value for r in done]}\ndone2={[r.outcome.value for r in done2]}"
    assert [r.outcome for r in done] == [Outcome.OK], diag
    assert seen == [
        f"before_success: streak={n - 1} rebuilt=0.0",
        "after_success: streak=0 rebuilt=0.0",  # 成功で 0 に戻った
        f"after_more: streak={n - 1} rebuilt=0.0",
        "after_rebuild: streak=0 rebuilt=1.0",
        "after_late_old: streak=0 rebuilt=1.0",  # 古いクライアントの時間切れでは作り直さない(連鎖しない)
    ], diag
    assert [r.outcome for r in done2] == [Outcome.OK], diag
    assert c["fleet_client_rebuilt"] == 1.0 and c["fleet_accounted"] == c["fleet_calls"], diag
