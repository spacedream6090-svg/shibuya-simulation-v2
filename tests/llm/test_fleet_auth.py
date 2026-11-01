"""艦隊の API key(環境変数 ``SHIBUYA_FLEET_API_KEY``)のヘッダ(tools/night5070 の安全の規則 1)。

- 変数が空でなければ、全レプリカの要求に ``Authorization: Bearer <値>`` を付ける。
- 変数が無い・空なら付けない(既定=これまでと同じ要求)。
HTTP サーバーは立てない(``httpx.MockTransport``)。
"""

from __future__ import annotations

import json

import httpx
import pytest

from shibuya.llm.fleet import FLEET_API_KEY_ENV, FleetClient, FleetConfig, LLMCall, Outcome, fleet_auth_headers

GOOD = "理由: 予定の時間になったから\n行動: 移動 対象: C-0001 ひと言: なし"


def _run_one(seen: list[str]) -> Outcome:
    def factory(endpoint: str) -> httpx.MockTransport:
        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request.headers.get("Authorization", ""))
            json.loads(request.content.decode("utf-8"))
            return httpx.Response(200, json={
                "id": "x",
                "choices": [{"index": 0, "message": {"role": "assistant", "content": GOOD},
                             "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 20}})

        return httpx.MockTransport(handler)

    cfg = FleetConfig(endpoints=("http://a", "http://b"), model="fake", per_replica_in_flight=2, queue_capacity=8,
                      stream=False, e2e_timeout_s=2.0, ttft_timeout_s=2.0)
    client = FleetClient(cfg, transport_factory=factory)
    try:
        client.submit([LLMCall(call_id=f"1:{a}:2", agent_id=a, tick=1, wake_class=2, prompt="p", user="p")
                       for a in range(4)])
        out = client.drain(timeout=10.0)
    finally:
        client.close()
    assert len(out) == 4
    return out[0].outcome


def test_bearer_header_when_env_set(monkeypatch):
    monkeypatch.setenv(FLEET_API_KEY_ENV, "k-test-123")
    seen: list[str] = []
    assert _run_one(seen) is Outcome.OK
    assert len(seen) == 4 and all(h == "Bearer k-test-123" for h in seen)
    assert fleet_auth_headers() == {"Authorization": "Bearer k-test-123"}


@pytest.mark.parametrize("value", [None, "", "   "])
def test_no_header_without_env(monkeypatch, value):
    if value is None:
        monkeypatch.delenv(FLEET_API_KEY_ENV, raising=False)
    else:
        monkeypatch.setenv(FLEET_API_KEY_ENV, value)
    seen: list[str] = []
    assert _run_one(seen) is Outcome.OK
    assert seen and all(h == "" for h in seen)
    assert fleet_auth_headers() is None
