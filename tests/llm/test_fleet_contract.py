"""C6-a 艦隊接続の契約テスト(層契約・純関数・性質)。HTTP サーバーを立てない軽い側。

- 層契約(実装計画書 §3): ``llm.fleet`` は engine/perception/world/agents/economy/census を
  import しない(``lint-imports`` と二重化した AST 検査)。
- 層契約のための**複製**(``LANE_THINK_TOKENS``)が engine 側の正典と同値であること。
- ``cache_salt``(モード別)・seed 導出・``max_tokens``(U19 ③)・予算行の読み取り。
- hypothesis: 任意の呼集合で **ok+deferred+undefined+error の合計 = 呼数**(呼を捨てない)。
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import httpx
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from shibuya.core.budget import budget_by_id, load_budget_table
from shibuya.llm.fleet import (
    DEFAULT_E2E_TIMEOUT_S,
    DEFAULT_TTFT_TIMEOUT_S,
    LANE_THINK_TOKENS,
    LANE_TIER,
    Deferred,
    FleetBridge,
    FleetClient,
    FleetConfig,
    LLMCall,
    Outcome,
    cache_salt_for,
    l4_calls_per_day,
    l6_in_flight_per_gpu,
    max_tokens_for,
    plan_batch,
    route_primary,
    seed_for,
    split_system_user,
)
from shibuya.manifest.schema import Mode

GOOD = "理由: 予定の時間になったから\n行動: 移動 対象: C-0001 ひと言: なし"
BAD = "うーん、なんとも言えませんね。"

FLEET_PY = Path(__file__).resolve().parents[2] / "src" / "shibuya" / "llm" / "fleet.py"
FORBIDDEN_PREFIXES = (
    "shibuya.engine",
    "shibuya.perception",
    "shibuya.world",
    "shibuya.agents",
    "shibuya.economy",
    "shibuya.census",
    "shibuya.build",
)


# ------------------------------------------------------------------ 層契約


def test_fleet_module_imports_no_forbidden_layer():
    """``llm`` は engine/perception/world/agents を import しない(AST での二重化)。"""
    tree = ast.parse(FLEET_PY.read_text(encoding="utf-8"))
    seen: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            seen.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            seen.append(node.module)
    bad = [m for m in seen if m.startswith(FORBIDDEN_PREFIXES)]
    assert bad == [], f"層契約違反の import: {bad}"


def test_lane_think_tokens_matches_engine_canon():
    """``LANE_THINK_TOKENS`` は層契約のための複製=engine 側の正典と同値を機械で固定する。"""
    from shibuya.engine.llm_bridge import LANE_SECONDS, LANE_THINK_TOKENS as CANON

    assert dict(LANE_THINK_TOKENS) == dict(CANON)
    assert set(LANE_TIER) == set(LANE_SECONDS)  # レーンの集合も同じ
    # 思考トークン 0 のレーンが T1・>0 が T2(認知設計書 §1 の表と一致)
    for lane, tokens in LANE_THINK_TOKENS.items():
        assert LANE_TIER[lane] == ("T1" if tokens == 0 else "T2")


def test_bridge_result_fields_mirror_engine_bridge_result():
    """``FleetBridgeResult`` は ``engine.llm_bridge.BridgeResult`` の欄を包含する。"""
    from dataclasses import fields

    from shibuya.engine.llm_bridge import BridgeResult

    from shibuya.llm.fleet import FleetBridgeResult

    engine_fields = {f.name for f in fields(BridgeResult)}
    fleet_fields = {f.name for f in fields(FleetBridgeResult)}
    # ``t_apply``/``tape_miss`` は engine 側の責務(δ_think の tick 換算・リプレイ)。
    # ``deferred``/``deferred_reason``/``observed_tick`` は**再生側の欄**(D-58):
    # 本番の艦隊は繰り延べを別の型(``Deferred``)で返すので結果型には要らない
    # (``FleetBridgeResult.deferred`` は常に False を返す property として在る)。
    replay_only = {"t_apply", "tape_miss", "deferred", "deferred_reason", "observed_tick"}
    missing = engine_fields - fleet_fields - replay_only
    assert missing == set(), f"engine 側の欄が落ちている: {missing}"
    assert FleetBridgeResult.deferred.fget is not None  # 「繰り延べでない」は型で言う


# ------------------------------------------------------------------ 予算・定数


def test_budget_rows_are_read_not_duplicated():
    rows = budget_by_id(load_budget_table())
    assert "in-flight" in rows["L6"].declared
    assert l6_in_flight_per_gpu() == 64  # 予算行 L6(ベンチ第3段の並行度の膝 c64)
    assert l4_calls_per_day() == 4_000_000  # 予算行 L4(憲法1 の監査点)


def test_default_timeouts_follow_plan_section7():
    assert DEFAULT_TTFT_TIMEOUT_S == 60.0
    assert DEFAULT_E2E_TIMEOUT_S == 300.0


def test_max_tokens_follows_u19_infra_clip():
    assert max_tokens_for("L0", 64) == 64
    assert max_tokens_for("L1", 64) == 64
    assert max_tokens_for("L4", 64) == 64
    assert max_tokens_for("L2", 64) == 3168  # ceil(1.5*2048)+96
    assert max_tokens_for("L3", 64) == 11346  # ceil(1.5*7500)+96
    with pytest.raises(KeyError):
        max_tokens_for("L9", 64)


# ------------------------------------------------------------------ cache_salt / seed


def test_cache_salt_differs_per_mode_and_is_stable():
    salts = {m: cache_salt_for(m, "run-abc") for m in Mode}
    assert len(set(salts.values())) == len(Mode)  # モード別に必ず違う
    for m in Mode:
        assert cache_salt_for(m, "run-abc") == salts[m]  # 同 run_id 同 mode で同じ
        assert cache_salt_for(m, "run-xyz") != salts[m]  # run_id が違えば違う
        assert len(salts[m]) == 32 and int(salts[m], 16) >= 0
    assert cache_salt_for("holdout", "r") == cache_salt_for(Mode.HOLDOUT, "r")
    with pytest.raises(ValueError):
        cache_salt_for("productionn", "r")


def test_seed_is_a_function_of_call_id_and_run_seed():
    a = seed_for("10:7:2", 1)
    assert a == seed_for("10:7:2", 1)
    assert a != seed_for("10:7:2", 2)
    assert a != seed_for("10:8:2", 1)
    assert 0 <= a <= 0x7FFF_FFFF


def test_split_system_user():
    assert split_system_user("SYS\nrest", "SYS") == ("SYS", "rest")
    assert split_system_user("SYSrest", "SYS") == ("SYS", "rest")
    assert split_system_user("other", "SYS") == ("", "other")  # 推測で切らない


# ------------------------------------------------------------------ 設定の検証


def test_config_rejects_bad_input():
    with pytest.raises(ValueError):
        FleetConfig(endpoints=())
    with pytest.raises(ValueError):
        FleetConfig(endpoints=("http://a", "http://a"))
    with pytest.raises(ValueError):
        FleetConfig(endpoints=("http://a",), ttft_timeout_s=10.0, e2e_timeout_s=5.0)


def test_manifest_fields_record_verification_run_settings():
    cfg = FleetConfig(
        endpoints=tuple(f"http://r{i}" for i in range(7)),
        mode=Mode.HOLDOUT,
        run_id="deadbeef",
        per_replica_in_flight=64,
    )
    f = cfg.manifest_fields()
    assert f["prefix_caching_hash_algo"] == "sha256_cbor"
    assert f["cache_salt"] == cache_salt_for(Mode.HOLDOUT, "deadbeef")
    assert f["routing"] == {"rule": "xxhash(call_id) mod N", "cell_affinity": False}
    assert f["n_replicas"] == 7
    assert f["in_flight_cap_per_replica"] == 64 and f["in_flight_cap_total"] == 448


def test_l6_default_is_read_from_the_budget_table():
    cfg = FleetConfig(endpoints=("http://a", "http://b"))
    assert cfg.resolved_per_replica() == l6_in_flight_per_gpu()
    assert cfg.resolved_max_in_flight() == l6_in_flight_per_gpu() * 2
    assert cfg.resolved_queue_capacity() == l6_in_flight_per_gpu() * 8


# ------------------------------------------------------------------ 順序制御(性質)


@given(
    n=st.integers(min_value=1, max_value=40),
    n_rep=st.integers(min_value=1, max_value=7),
)
@settings(max_examples=50, deadline=None)
def test_plan_batch_is_a_permutation_and_deterministic(n, n_rep):
    calls = [
        LLMCall(
            call_id=f"10:{i}:2",
            agent_id=i,
            tick=10,
            wake_class=2,
            prompt="p",
            cell=i % 5,
            time_bucket=i % 3,
        )
        for i in range(n)
    ]
    plan = plan_batch(calls, n_rep, per_replica_cap=64)
    assert {c.call_id for c, _ in plan} == {c.call_id for c in calls}  # 過不足なし
    assert len(plan) == n
    assert all(0 <= r < n_rep for _, r in plan)
    assert plan == plan_batch(calls, n_rep, per_replica_cap=64)  # 決定論
    keys = [(c.cell, c.time_bucket, c.call_id) for c, _ in plan]
    assert keys == sorted(keys)  # 同一(セル,時間帯)は隣り合う=同時発射


# ------------------------------------------------------------------ 偽トランスポート


def _mock_factory(kind_of):
    """``endpoint -> httpx.MockTransport``。``kind_of(call_text) -> str`` で挙動を注入。"""

    def factory(endpoint: str) -> httpx.MockTransport:
        def handler(request: httpx.Request) -> httpx.Response:
            payload = json.loads(request.content.decode("utf-8"))
            text_in = payload["messages"][-1]["content"]
            kind = kind_of(text_in, endpoint)
            if kind == "conn":
                raise httpx.ConnectError("injected", request=request)
            if kind == "5xx":
                return httpx.Response(503, json={"error": "injected"})
            if kind == "4xx":
                return httpx.Response(400, json={"error": "injected"})
            body = BAD if kind == "bad" else GOOD
            return httpx.Response(
                200,
                json={
                    "id": "x",
                    "choices": [
                        {"index": 0, "message": {"role": "assistant", "content": body},
                         "finish_reason": "stop"}
                    ],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 20},
                },
            )

        return httpx.MockTransport(handler)

    return factory


KINDS = ("ok", "bad", "conn", "5xx", "4xx")


@given(
    kinds=st.lists(st.sampled_from(KINDS), min_size=1, max_size=25),
    n_rep=st.integers(min_value=1, max_value=4),
)
@settings(max_examples=25, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_every_call_is_accounted_for(kinds, n_rep):
    """性質: 任意の呼集合で **返る結果の数 = 呼数**・**帳尻 = 呼数**(呼を捨てない=憲法1)。"""
    calls = [
        LLMCall(
            call_id=f"10:{i}:2",
            agent_id=i,
            tick=10,
            wake_class=2,
            prompt=f"u{i}",
            user=f"u{i}",
            cell=i % 4,
            time_bucket=i % 2,
        )
        for i in range(len(kinds))
    ]
    by_text = {f"u{i}": k for i, k in enumerate(kinds)}
    cfg = FleetConfig(
        endpoints=tuple(f"http://replica{i}" for i in range(n_rep)),
        model="fake",
        mode=Mode.SMOKE,
        run_id="prop",
        per_replica_in_flight=4,
        queue_capacity=64,  # 満杯は別テスト(test_fleet.py)で見る
        stream=False,
        ttft_timeout_s=2.0,
        e2e_timeout_s=2.0,
    )
    client = FleetClient(cfg, transport_factory=_mock_factory(lambda t, e: by_text[t]))
    try:
        bridge = FleetBridge(client)
        out = bridge.submit_and_drain(calls, timeout=30.0)
        counters = bridge.counters()
    finally:
        client.close()

    assert len(out) == len(calls)
    assert {r.call_id for r in out} == {c.call_id for c in calls}
    assert counters["fleet_calls"] == len(calls)
    assert counters["fleet_accounted"] == len(calls)

    # 結果の型と outcome の対応が崩れていない
    for r in out:
        if isinstance(r, Deferred):
            assert r.outcome in (
                Outcome.DEFERRED_TIMEOUT,
                Outcome.DEFERRED_QUEUE_FULL,
                Outcome.ERROR_OTHER,
            )
        else:
            assert r.outcome in (
                Outcome.OK,
                Outcome.FORMAT_RETRY_OK,
                Outcome.ERROR_RETRIED_OK,
                Outcome.UNDEFINED,
            )
    # 注入した挙動どおりの帰結になっている
    kind_by_id = {c.call_id: by_text[c.user] for c in calls}
    for r in out:
        k = kind_by_id[r.call_id]
        if k == "ok":
            assert r.outcome is Outcome.OK
        elif k == "bad":
            assert r.outcome is Outcome.UNDEFINED  # 再生成しても bad → 未定義行動5段
        elif k == "4xx":
            assert r.outcome is Outcome.ERROR_OTHER
        else:  # conn / 5xx: 全レプリカが同じ挙動なので枯渇 → 繰り延べ
            assert r.outcome is Outcome.ERROR_OTHER


def test_single_replica_has_no_alternate_and_is_counted():
    """レプリカ 1 本では「別レプリカ 1 回」が退化する=診断行に残す。"""
    cfg = FleetConfig(
        endpoints=("http://only",),
        model="fake",
        per_replica_in_flight=2,
        queue_capacity=8,
        stream=False,
        e2e_timeout_s=2.0,
        ttft_timeout_s=2.0,
    )
    client = FleetClient(cfg, transport_factory=_mock_factory(lambda t, e: "ok"))
    try:
        client.submit([LLMCall(call_id="1:1:2", agent_id=1, tick=1, wake_class=2, prompt="p", user="p")])
        out = client.drain(timeout=10.0)
        c = client.counters()
    finally:
        client.close()
    assert len(out) == 1 and out[0].outcome is Outcome.OK
    assert c["fleet_no_alternate_replica"] == 1


def test_routing_spreads_over_seven_replicas_like_the_plan():
    """§7「レプリカ配分=xxhash(call_id) mod 7」。実艦隊規模で偏りが極端でないこと。"""
    ids = [f"{t}:{a}:2" for t in range(30) for a in range(30)]
    counts = [0] * 7
    for cid in ids:
        counts[route_primary(cid, 7)] += 1
    share = [c / len(ids) for c in counts]
    assert min(share) > 0.11 and max(share) < 0.17  # 1/7 ≒ 0.143
