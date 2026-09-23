"""C6-a 艦隊接続の検収テスト(**プロセス内の偽 vLLM**・実サーバーへは繋がない)。

偽 vLLM は標準ライブラリ ``http.server`` の ``ThreadingHTTPServer``。
``/v1/models`` と ``/v1/chat/completions``(JSON / SSE ストリーミング)を実装し、
遅延・接続断・HTTP エラー・書式不良を**注入**できる。

検収の観点(実装計画書 §7)
- ルーティングの決定論(``xxhash(call_id) mod N``)と同一(セル,時間帯)の同一 GPU 回避。
- least-in-flight への切替。
- 接続エラーの再試行**順序**(同一レプリカ → 別レプリカ)。
- TTFT / e2e タイムアウト → ``Deferred``(**捨てない**)。
- キュー満杯 → 非ブロッキングで「入らなかった」を返す。
- 書式エラー → **温度 0 で 1 回再生成** → なお駄目なら未定義行動5段。
- 録画テープに**実応答**が入り、``engine.tape.Replay`` で完全一致リプレイできる。
- 診断カウンタ。
"""

from __future__ import annotations

import json
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from shibuya.core.hashing import sha256_cbor
from shibuya.engine.tape import Replay, TapeRow, TapeWriter
from shibuya.llm import ACTION_CODES, UndefinedActionRegistry
from shibuya.llm.fleet import (
    Deferred,
    FleetBridge,
    FleetBridgeResult,
    FleetClient,
    FleetConfig,
    LLMCall,
    Outcome,
    plan_batch,
    route_primary,
)
from shibuya.manifest.schema import Mode

GOOD = "理由: 予定の時間になったから\n行動: 移動 対象: C-0001 ひと言: なし"
BAD = "うーん、なんとも言えませんね。"


# ------------------------------------------------------------------ 偽 vLLM


_AGENT_RE = re.compile(r"\[a(\d+)\|")


def _pair_talk_text(payload: dict) -> str:
    """``StubRenderer`` の本文 ``[a<id>|c…]`` から個体 id を読み、対 (id^1) を名指す 2 行形。"""
    body = " ".join(m.get("content", "") for m in payload.get("messages", ()))
    m = _AGENT_RE.search(body)
    a = int(m.group(1)) if m else 0
    return "理由: 知人を見かけたから%s行動: 会話 対象: P-%d ひと言: こんにちは" % (chr(10), a ^ 1)


class FakeVLLM:
    """プロセス内の偽 vLLM(OpenAI 互換の最小面)。注入つまみは属性で切り替える。"""

    def __init__(self, model: str = "fake-qwen3-8b-int8") -> None:
        self.model = model
        self.lock = threading.Lock()
        self.requests: list[dict] = []
        self.fail_remaining = 0  # HTTP 5xx を返す残回数
        self.fail_status = 503
        self.hard_close_remaining = 0  # 応答せず切断(接続エラー)
        self.bad_format_remaining = 0  # 2行形でない本文を返す残回数
        self.ttft_delay_s = 0.0
        self.total_delay_s = 0.0
        #: True にすると、プロンプトの ``[a<id>…]`` から個体 id を読み、
        #: 「行動: 会話 対象: P-(id^1)」を返す(**対を組む**=承諾の対象規則を満たす形)。
        self.pair_talk = False
        self.text = GOOD
        self.bad_text = BAD
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _make_handler(self))
        self.server.daemon_threads = True
        self._thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self._thread.start()

    @property
    def endpoint(self) -> str:
        host, port = self.server.server_address[:2]
        return f"http://{host}:{port}"

    @property
    def n_requests(self) -> int:
        with self.lock:
            return len(self.requests)

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self._thread.join(timeout=5.0)


def _make_handler(fake: FakeVLLM):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *args, **kwargs) -> None:  # 静かに
            pass

        # ---- 補助 ----
        def _send_json(self, status: int, obj) -> None:
            body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _chunk(self, s: str) -> None:
            b = s.encode("utf-8")
            self.wfile.write(f"{len(b):X}\r\n".encode("ascii"))
            self.wfile.write(b)
            self.wfile.write(b"\r\n")
            self.wfile.flush()

        # ---- ルート ----
        def do_GET(self) -> None:
            if self.path.rstrip("/") == "/v1/models":
                self._send_json(200, {"object": "list", "data": [{"id": fake.model, "object": "model"}]})
            else:
                self._send_json(404, {"error": "not found"})

        def do_POST(self) -> None:
            n = int(self.headers.get("Content-Length", "0") or 0)
            raw = self.rfile.read(n) if n else b"{}"
            try:
                payload = json.loads(raw.decode("utf-8"))
            except Exception:
                payload = {}
            with fake.lock:
                fake.requests.append(payload)
                close = fake.hard_close_remaining > 0
                if close:
                    fake.hard_close_remaining -= 1
                fail = 0
                if not close and fake.fail_remaining > 0:
                    fake.fail_remaining -= 1
                    fail = fake.fail_status
                if fake.bad_format_remaining > 0:
                    fake.bad_format_remaining -= 1
                    text = fake.bad_text
                elif fake.pair_talk:
                    text = _pair_talk_text(payload)
                else:
                    text = fake.text
                ttft = fake.ttft_delay_s
                total = fake.total_delay_s
            if close:
                self.close_connection = True
                return
            if fail:
                self._send_json(fail, {"error": "injected"})
                return
            if payload.get("stream"):
                self._stream(text, ttft, total)
            else:
                if ttft or total:
                    time.sleep(max(ttft, total))
                self._send_json(
                    200,
                    {
                        "id": "x",
                        "choices": [
                            {"index": 0, "message": {"role": "assistant", "content": text},
                             "finish_reason": "stop"}
                        ],
                        "usage": {"prompt_tokens": 123, "completion_tokens": max(1, len(text) // 2)},
                    },
                )

        def _stream(self, text: str, ttft: float, total: float) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()
            self.wfile.flush()
            if ttft:
                time.sleep(ttft)
            pieces = [text[i : i + 8] for i in range(0, len(text), 8)] or [""]
            per = (total / len(pieces)) if total else 0.0
            for p in pieces:
                self._chunk(
                    "data: "
                    + json.dumps(
                        {"id": "x", "choices": [{"index": 0, "delta": {"content": p},
                                                 "finish_reason": None}]},
                        ensure_ascii=False,
                    )
                    + "\n\n"
                )
                if per:
                    time.sleep(per)
            self._chunk(
                "data: "
                + json.dumps(
                    {
                        "id": "x",
                        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                        "usage": {"prompt_tokens": 123, "completion_tokens": max(1, len(text) // 2)},
                    },
                    ensure_ascii=False,
                )
                + "\n\n"
            )
            self._chunk("data: [DONE]\n\n")
            self._chunk("")

    return Handler


# ------------------------------------------------------------------ 補助


@pytest.fixture
def fleet2():
    """2 レプリカの偽艦隊。"""
    servers = [FakeVLLM(), FakeVLLM()]
    try:
        yield servers
    finally:
        for s in servers:
            s.close()


@pytest.fixture
def fleet3():
    servers = [FakeVLLM(), FakeVLLM(), FakeVLLM()]
    try:
        yield servers
    finally:
        for s in servers:
            s.close()


def make_config(servers, **kw) -> FleetConfig:
    base = dict(
        endpoints=tuple(s.endpoint for s in servers),
        model=servers[0].model,
        mode=Mode.SMOKE,
        run_id="test-run",
        per_replica_in_flight=8,
        queue_capacity=256,
        ttft_timeout_s=5.0,
        e2e_timeout_s=10.0,
        connect_timeout_s=5.0,
        latency_samples=1000,
    )
    base.update(kw)
    return FleetConfig(**base)


def mkcall(i: int, *, cell: int = 0, bucket: int = 0, tick: int = 10, agent: int | None = None) -> LLMCall:
    a = i if agent is None else agent
    return LLMCall(
        call_id=f"{tick}:{a}:2",
        agent_id=a,
        tick=tick,
        wake_class=2,
        prompt=f"[B0 共有]\n[a{a}|c{cell}|t5{bucket}]",
        system="[B0 共有]",
        user=f"[a{a}|c{cell}|t5{bucket}]",
        blocks=(("b0", "[B0 共有]"),),
        lane="L1",
        cell=cell,
        time_bucket=bucket,
    )


# ------------------------------------------------------------------ ルーティング(純関数)


def test_route_primary_is_deterministic_mod_n():
    ids = [f"10:{i}:2" for i in range(200)]
    first = [route_primary(c, 7) for c in ids]
    second = [route_primary(c, 7) for c in ids]
    assert first == second
    assert set(first) == set(range(7))  # 7 本すべてに散る


def test_plan_batch_groups_same_cell_bucket_onto_distinct_replicas():
    calls = [mkcall(i, cell=3, bucket=4) for i in range(4)]
    plan = plan_batch(calls, 7, per_replica_cap=64)
    replicas = [r for _, r in plan]
    assert len(set(replicas)) == len(replicas)  # BN-4: 同一 GPU に寄せない
    # 発射順は (cell, time_bucket, call_id) 昇順で決定論
    assert [c.call_id for c, _ in plan] == sorted(c.call_id for c in calls)
    assert plan_batch(calls, 7, per_replica_cap=64) == plan


def test_plan_batch_without_group_spread_follows_pure_mod_n():
    calls = [mkcall(i, cell=3, bucket=4) for i in range(20)]
    plan = plan_batch(calls, 7, per_replica_cap=64, group_spread=False, imbalance_threshold=10**6)
    for call, replica in plan:
        assert replica == route_primary(call.call_id, 7)


def test_plan_batch_least_in_flight_when_saturated():
    calls = [mkcall(0, cell=1, bucket=0)]
    primary = route_primary(calls[0].call_id, 3)
    load = [5, 5, 5]
    load[primary] = 8  # 上限に達している
    least = min(i for i in range(3) if load[i] == min(load))
    plan = plan_batch(calls, 3, in_flight=load, per_replica_cap=8, imbalance_threshold=10**6)
    assert plan[0][1] == least != primary


def test_plan_batch_least_in_flight_on_imbalance():
    calls = [mkcall(0, cell=1, bucket=0)]
    primary = route_primary(calls[0].call_id, 3)
    load = [0, 0, 0]
    load[primary] = 8  # 最小との差 8 ≥ 閾値 8
    plan = plan_batch(calls, 3, in_flight=load, per_replica_cap=64, imbalance_threshold=8)
    assert plan[0][1] != primary
    assert load[plan[0][1]] == 0


# ------------------------------------------------------------------ 正常系


@pytest.mark.parametrize("stream", [True, False])
def test_smoke_all_ok(fleet2, stream):
    cfg = make_config(fleet2, stream=stream)
    with FleetClient(cfg) as client:
        rejected = client.submit([mkcall(i, cell=i % 3, bucket=0) for i in range(24)])
        assert rejected == []
        done = client.drain(timeout=20.0)
    assert len(done) == 24
    assert all(isinstance(r, type(done[0])) for r in done)
    assert all(r.outcome is Outcome.OK for r in done)
    assert all(r.text == GOOD for r in done)
    assert all(r.tokens_in == 123 for r in done)
    c = client.counters()
    assert c["fleet_calls"] == 24 and c["fleet_ok"] == 24
    assert c["fleet_calls_r0"] + c["fleet_calls_r1"] == 24
    assert c["fleet_e2e_p50"] > 0.0 and c["fleet_e2e_p99"] > 0.0


def test_model_discovery(fleet2):
    cfg = make_config(fleet2, model="")
    with FleetClient(cfg) as client:
        assert client.discover_model() == fleet2[0].model


def test_payload_carries_cache_salt_seed_and_no_structured_outputs(fleet2):
    cfg = make_config(fleet2, stream=False)
    with FleetClient(cfg) as client:
        salt = client.cache_salt
        client.submit([mkcall(0)])
        client.drain(timeout=20.0)
    payloads = [p for s in fleet2 for p in s.requests]
    assert len(payloads) == 1
    p = payloads[0]
    assert p["cache_salt"] == salt
    # 既定は温度 0.7(知覚契約書 §2.5/卒業条件表・運用設計書 §1.3)・max_tokens 96(expedient)
    assert p["temperature"] == 0.7 and p["max_tokens"] == 96
    assert p["chat_template_kwargs"] == {"enable_thinking": False}  # U19: T1 思考 0
    assert "structured_outputs" not in p  # 本線は 2 行形パーサ
    assert isinstance(p["seed"], int)
    assert [m["role"] for m in p["messages"]] == ["system", "user"]


def test_t2_lane_uses_thinking_and_infra_clip_ceiling(fleet2):
    cfg = make_config(fleet2, stream=False)
    call = LLMCall(
        call_id="10:1:0", agent_id=1, tick=10, wake_class=0, prompt="p", user="p", lane="L2"
    )
    with FleetClient(cfg) as client:
        client.submit([call])
        client.drain(timeout=20.0)
    p = [q for s in fleet2 for q in s.requests][0]
    assert p["chat_template_kwargs"] == {"enable_thinking": True}
    assert p["max_tokens"] == 3168  # ceil(1.5*2048)+96


# ------------------------------------------------------------------ 失敗の意味論


def test_connection_error_retries_same_then_other(fleet2):
    """接続エラー = 同一レプリカ 1 回 → 別レプリカ 1 回(§7)。"""
    cfg = make_config(fleet2, stream=False)
    call = mkcall(0)
    primary = route_primary(call.call_id, 2)
    other = (primary + 1) % 2
    fleet2[primary].hard_close_remaining = 2  # 初回 + 同一レプリカ再試行 を潰す
    with FleetClient(cfg) as client:
        assert client.submit([call]) == []
        done = client.drain(timeout=20.0)
    assert len(done) == 1
    res = done[0]
    assert not res.deferred
    assert res.outcome is Outcome.ERROR_RETRIED_OK
    assert res.attempts == 3
    assert res.replica == other
    assert fleet2[primary].n_requests == 2  # 同一レプリカへ 2 回
    assert fleet2[other].n_requests == 1  # 別レプリカへ 1 回
    c = client.counters()
    assert c["fleet_conn_retry_same"] == 1 and c["fleet_conn_retry_other"] == 1
    assert c["fleet_error_retried_ok"] == 1


def test_http_5xx_is_a_connection_error(fleet2):
    cfg = make_config(fleet2, stream=False)
    call = mkcall(0)
    primary = route_primary(call.call_id, 2)
    fleet2[primary].fail_remaining = 1
    with FleetClient(cfg) as client:
        client.submit([call])
        done = client.drain(timeout=20.0)
    assert done[0].outcome is Outcome.ERROR_RETRIED_OK
    assert done[0].replica == primary  # 同一レプリカの再試行で通った
    assert done[0].attempts == 2


def test_all_replicas_down_defers_and_does_not_drop(fleet2):
    cfg = make_config(fleet2, stream=False)
    for s in fleet2:
        s.hard_close_remaining = 10
    call = mkcall(0)
    with FleetClient(cfg) as client:
        client.submit([call])
        done = client.drain(timeout=20.0)
    assert len(done) == 1  # 呼は消えない
    assert isinstance(done[0], Deferred)
    assert done[0].outcome is Outcome.ERROR_OTHER
    assert done[0].call.call_id == call.call_id
    assert client.counters()["fleet_error_other"] == 1


def test_ttft_timeout_defers_not_discards(fleet2):
    """TTFT 超過 = 繰り延べ(破棄禁止・憲法1)。再試行はしない。"""
    cfg = make_config(fleet2, stream=True, ttft_timeout_s=0.2, e2e_timeout_s=8.0)
    for s in fleet2:
        s.ttft_delay_s = 1.5
    with FleetClient(cfg) as client:
        client.submit([mkcall(0)])
        done = client.drain(timeout=20.0)
    assert len(done) == 1 and isinstance(done[0], Deferred)
    assert done[0].outcome is Outcome.DEFERRED_TIMEOUT
    assert done[0].attempts == 1  # タイムアウトは再試行しない
    assert client.counters()["fleet_deferred_timeout"] == 1


def test_e2e_timeout_defers(fleet2):
    cfg = make_config(fleet2, stream=False, ttft_timeout_s=0.3, e2e_timeout_s=0.3)
    for s in fleet2:
        s.total_delay_s = 1.5
    with FleetClient(cfg) as client:
        client.submit([mkcall(0)])
        done = client.drain(timeout=20.0)
    assert isinstance(done[0], Deferred)
    assert done[0].outcome is Outcome.DEFERRED_TIMEOUT


def test_queue_full_is_non_blocking(fleet2):
    """キュー満杯 = 非ブロッキングで「入らなかった」を返す(アービタが繰り延べる)。"""
    cfg = make_config(fleet2, stream=False, queue_capacity=4, per_replica_in_flight=2)
    for s in fleet2:
        s.total_delay_s = 0.4
    calls = [mkcall(i, cell=i) for i in range(16)]
    with FleetClient(cfg) as client:
        t0 = time.perf_counter()
        rejected = client.submit(calls)
        elapsed = time.perf_counter() - t0
        assert elapsed < 0.3  # tick ループを止めない
        assert len(rejected) == 12
        assert all(r.outcome is Outcome.DEFERRED_QUEUE_FULL for r in rejected)
        done = client.drain(timeout=30.0)
    assert len(done) == 4
    ids = {r.call_id for r in rejected} | {r.call_id for r in done}
    assert ids == {c.call_id for c in calls}  # 1 呼も消えていない
    assert client.counters()["fleet_deferred_queue_full"] == 12


def test_format_error_regenerates_at_temperature_zero(fleet2):
    """書式エラー = 温度 0 で 1 回再生成(§7)。再生成で通れば format_retry_ok。"""
    cfg = make_config(fleet2, stream=False, temperature=0.7)
    call = mkcall(0)
    primary = route_primary(call.call_id, 2)
    fleet2[primary].bad_format_remaining = 1
    with FleetClient(cfg) as client:
        client.submit([call])
        done = client.drain(timeout=20.0)
    assert done[0].outcome is Outcome.FORMAT_RETRY_OK
    assert done[0].format_retried and done[0].text == GOOD
    reqs = fleet2[primary].requests
    assert len(reqs) == 2
    assert reqs[0]["temperature"] == 0.7
    assert reqs[1]["temperature"] == 0.0 and reqs[1]["top_p"] == 1.0
    c = client.counters()
    assert c["fleet_format_retry"] == 1 and c["fleet_format_retry_ok"] == 1


def test_format_error_twice_falls_to_undefined_five_stages(fleet2):
    """再生成後も語彙一致しなければ未定義行動5段(§7)へ。"""
    cfg = make_config(fleet2, stream=False)
    for s in fleet2:
        s.bad_format_remaining = 10
    reg = UndefinedActionRegistry()
    with FleetClient(cfg) as client:
        bridge = FleetBridge(client, undefined=reg)
        out = bridge.submit_and_drain([mkcall(0)], timeout=20.0)
        c = bridge.counters()
    assert len(out) == 1
    res = out[0]
    assert isinstance(res, FleetBridgeResult)
    assert res.outcome is Outcome.UNDEFINED
    assert res.undefined_stage >= 0
    assert c["fleet_format_retry"] == 1 and c["fleet_format_retry_ok"] == 0
    assert c["unknown_action"] == 1 and c["parse_errors"] == 1


# ------------------------------------------------------------------ ブリッジ・テープ


def test_bridge_parses_and_records_real_response_to_tape(fleet2, tmp_path: Path):
    cfg = make_config(fleet2, stream=True)
    calls = [mkcall(i, cell=i % 2) for i in range(6)]
    with TapeWriter(tmp_path / "tape") as tape:
        with FleetClient(cfg) as client:
            bridge = FleetBridge(client, tape=tape, tape_row_factory=TapeRow)
            out = bridge.submit_and_drain(calls, timeout=20.0)
            assert bridge.n_tape_rows == 6
    assert len(out) == 6
    for res in out:
        assert isinstance(res, FleetBridgeResult)
        assert res.format_ok and res.parse.action == "移動"
        assert res.source.startswith("fleet:")

    replay = Replay(tmp_path / "tape")
    by_id = {r.call_id: r for r in out}
    for call in calls:
        res = by_id[call.call_id]
        # テープ鍵の第4要素は engine.llm_bridge と同じ算法(= LLMRequest.prompt_hash)
        assert res.tape_prompt_hash == sha256_cbor(call.prompt)
        text = replay.lookup(call.agent_id, call.tick, call.wake_class, res.tape_prompt_hash)
        assert text == res.text == GOOD  # 実応答がテープに入り完全一致で引ける


def test_bridge_passes_deferred_through_untouched(fleet2):
    cfg = make_config(fleet2, stream=False, queue_capacity=1, per_replica_in_flight=1)
    for s in fleet2:
        s.total_delay_s = 0.3
    calls = [mkcall(i, cell=i) for i in range(6)]
    with FleetClient(cfg) as client:
        bridge = FleetBridge(client)
        out = bridge.submit_and_drain(calls, timeout=30.0)
    assert len(out) == 6
    assert sum(isinstance(r, Deferred) for r in out) == 5
    assert {r.call_id for r in out} == {c.call_id for c in calls}


def test_fleet_client_is_drop_in_for_existing_llm_bridge(fleet2, tmp_path: Path):
    """``FleetClient`` は ``llm.LLMClient`` 契約を満たす=既存 bridge にそのまま挿さる。"""
    from shibuya.engine.llm_bridge import LLMBridge, StubRenderer

    cfg = make_config(fleet2, stream=False)
    with FleetClient(cfg) as client:
        bridge = LLMBridge(client, renderer=StubRenderer(), mode="record")
        res = bridge.call(7, 3, 2, 0, cell=1)
    assert res.text == GOOD
    assert res.format_ok and res.action_code >= 0
    assert res.source.startswith("fleet:")


# ------------------------------------------------------------------ 診断


def test_counters_account_for_every_call(fleet3):
    """任意の混合注入でも ok+deferred+undefined+error の合計 = 呼数(呼を捨てない)。"""
    cfg = make_config(fleet3, stream=False, queue_capacity=8, per_replica_in_flight=4)
    fleet3[0].hard_close_remaining = 3
    fleet3[1].bad_format_remaining = 2
    fleet3[2].total_delay_s = 0.05
    calls = [mkcall(i, cell=i % 4, bucket=i % 3) for i in range(20)]
    with FleetClient(cfg) as client:
        bridge = FleetBridge(client)
        out = bridge.submit_and_drain(calls, timeout=40.0)
        c = bridge.counters()
    assert {r.call_id for r in out} == {x.call_id for x in calls}
    assert len(out) == len(calls)
    kinds = {}
    for r in out:
        kinds[r.outcome] = kinds.get(r.outcome, 0) + 1
    assert sum(kinds.values()) == 20
    assert c["fleet_calls"] == 20
    assert c["fleet_accounted"] == 20  # 帳尻: 答え + 繰り延べ + error_other = 呼数
    assert (
        c["fleet_ok"]
        + c["fleet_format_retry_ok"]
        + c["fleet_error_retried_ok"]
        + c["fleet_deferred_timeout"]
        + c["fleet_deferred_queue_full"]
        + c["fleet_error_other"]
    ) == 20
    for key in ("fleet_ttft_p50", "fleet_ttft_p99", "fleet_e2e_p50", "fleet_e2e_p99"):
        assert key in c
    for i in range(3):
        assert c[f"fleet_in_flight_r{i}"] == 0.0
        assert f"fleet_peak_in_flight_r{i}" in c


def test_in_flight_returns_to_zero_after_drain(fleet2):
    cfg = make_config(fleet2, stream=True)
    with FleetClient(cfg) as client:
        client.submit([mkcall(i, cell=i % 5) for i in range(12)])
        client.drain(timeout=20.0)
        assert client.outstanding == 0
        assert client.in_flight == (0, 0)


# ------------------------------------------------------------------ C6 二重指標(09-09)

#: ラベル言い換え(C6 スモークで実際に出た形)。実効=読める・厳密=読めない。
ALIAS = "理由: 予定の時間になったから\n行動: 移動 目的地: C-0001 ひと言: なし"
#: 語彙外の行動語(§7 段0 の辞書で「移動」へ写る)。
OOV = "理由: 様子を見たいから\n行動: 探索 対象: C-0001 ひと言: なし"


def test_label_alias_counts_strict_errors_without_regenerating(fleet2):
    """別名で読めた応答は**温度 0 の再生成をしない**(実効基準)が、厳密側には計上する。"""
    cfg = make_config(fleet2, stream=False)
    for s in fleet2:
        s.text = ALIAS
    with FleetClient(cfg) as client:
        bridge = FleetBridge(client)
        out = bridge.submit_and_drain([mkcall(i, cell=i % 2) for i in range(6)], timeout=20.0)
        c = bridge.counters()
    assert len(out) == 6 and all(r.outcome is Outcome.OK for r in out)
    assert all(r.parse.action == "移動" for r in out)  # 世界には正しく届く
    assert c["fleet_format_strict_errors"] == 6  # 厳密基準ではエラー
    assert c["parse_errors"] == 0  # 実効基準ではエラーでない
    assert c["parse_error_rate"] == 0.0 and c["parse_error_rate_strict"] == 1.0
    assert c["fleet_label_alias_used"] == 6 and c["fleet_label_alias_rate"] == 1.0
    assert c["fleet_format_retry"] == 0  # **再生成していない**
    assert sum(len(s.requests) for s in fleet2) == 6  # 1 呼 = 1 リクエスト


def test_out_of_vocabulary_action_is_counted_as_dictionary_mapped(fleet2):
    """語彙外の行動語は §7 段0 の辞書で救い、``fleet_dictionary_mapped`` に計上する。"""
    cfg = make_config(fleet2, stream=False)
    for s in fleet2:
        s.text = OOV
    with FleetClient(cfg) as client:
        bridge = FleetBridge(client)
        out = bridge.submit_and_drain([mkcall(i, cell=i % 2) for i in range(4)], timeout=20.0)
        c = bridge.counters()
    assert len(out) == 4
    assert all(r.outcome is Outcome.UNDEFINED and r.undefined_stage == 0 for r in out)
    assert all(r.action_code == ACTION_CODES["移動"] for r in out)  # 世界へは「移動」で届く
    assert c["fleet_dictionary_mapped"] == 4 and c["fleet_dictionary_mapped_rate"] == 1.0
    assert c["dictionary_mapped"] == 4  # 台帳側(undefined.counters)と一致
    assert c["undefined_mapped"] == 4 and c["unknown_action"] == 4


def test_temperature_and_max_tokens_are_configurable_and_recorded(fleet2):
    """``--temperature 0.7 --max-tokens 96`` 相当が payload と manifest 欄に載る。"""
    cfg = make_config(fleet2, stream=False, temperature=0.7, t1_max_tokens=96)
    with FleetClient(cfg) as client:
        client.submit([mkcall(0)])
        client.drain(timeout=20.0)
    p = [q for s in fleet2 for q in s.requests][0]
    assert p["temperature"] == 0.7 and p["max_tokens"] == 96 and p["top_p"] == 1.0
    f = cfg.manifest_fields()
    assert f["decoding"]["T1"] == {
        "temperature": 0.7, "top_p": 1.0, "max_tokens": 96, "seed": "xxh64(call_id, run_seed)",
    }
    assert f["decoding"]["T2"]["max_tokens"] == 3168  # T2 は U19 ③ の式(t1 に依らない)


def test_format_retry_still_fires_for_真の書式崩れ(fleet2):
    """別名でも辞書でも読めない応答は、従来どおり温度 0 で 1 回再生成する。"""
    cfg = make_config(fleet2, stream=False, temperature=0.7)
    call = mkcall(0)
    primary = route_primary(call.call_id, 2)
    fleet2[primary].bad_format_remaining = 1
    with FleetClient(cfg) as client:
        bridge = FleetBridge(client)
        out = bridge.submit_and_drain([call], timeout=20.0)
        c = bridge.counters()
    assert out[0].outcome is Outcome.FORMAT_RETRY_OK
    assert c["fleet_format_retry"] == 1 and c["fleet_format_retry_ok"] == 1
    assert fleet2[primary].requests[0]["temperature"] == 0.7
    assert fleet2[primary].requests[1]["temperature"] == 0.0  # 再生成は温度 0


# ------------------------------------------------------------------ C6 追補(サブ Q 第2弾)

#: 「対象」「ひと言」のラベルを省いて値だけ並べた形(C6 実測の失敗の主形・位置で読む)。
POSITIONAL = "理由: 予定の時間になったから\n行動: 移動 C-0001 なし"


def test_dictionary_candidate_skips_the_temperature_zero_regeneration(fleet2):
    """語彙外でも §7 段0 の辞書で救える語は**再生成しない**(無駄な 1 呼を出さない)。"""
    cfg = make_config(fleet2, stream=False)
    for s in fleet2:
        s.text = OOV  # 「探索」→ 段0 で「移動」へ
    with FleetClient(cfg) as client:
        bridge = FleetBridge(client)
        out = bridge.submit_and_drain([mkcall(i, cell=i % 2) for i in range(4)], timeout=20.0)
        c = bridge.counters()
    assert len(out) == 4
    assert c["fleet_format_retry"] == 0  # **再生成していない**
    assert c["fleet_dictionary_mapped"] == 4
    assert all(r.action_code == ACTION_CODES["移動"] for r in out)
    assert sum(len(s.requests) for s in fleet2) == 4  # 1 呼 = 1 リクエスト


def test_positional_reading_is_counted(fleet2):
    """ラベルを省いた並びを位置で読んだ応答を ``fleet_positional_used`` に数える。"""
    cfg = make_config(fleet2, stream=False)
    for s in fleet2:
        s.text = POSITIONAL
    with FleetClient(cfg) as client:
        bridge = FleetBridge(client)
        out = bridge.submit_and_drain([mkcall(i, cell=i % 2) for i in range(4)], timeout=20.0)
        c = bridge.counters()
    assert all(r.parse.positional_used for r in out)
    assert c["fleet_positional_used"] == 4 and c["fleet_positional_rate"] == 1.0
    assert c["fleet_format_retry"] == 0  # 位置で読めたので再生成しない
