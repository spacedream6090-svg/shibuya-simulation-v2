"""**L4 / L6 予算の読み取り**(C6 受入「L4/L6予算」)。

- 予算行 **L4**「上限 400 万呼/日(o64)/ 平均 **10 呼/体/日**が繰り延べアービタの制御目標」。
- 予算行 **L6**「**64 in-flight/GPU**(bounded)」。

数値はコードに複製せず、**予算表から読む**(``llm.fleet.l4_calls_per_day`` /
``l6_in_flight_per_gpu``)。艦隊の実挙動そのものは ``tests/llm/test_fleet.py``(偽 vLLM)が
見るので、ここでは「ランが上限を破らないこと」と「診断行の in-flight が L6×N を超えないこと」
だけを固定する。
"""

from __future__ import annotations

import pytest

from shibuya import cli
from shibuya.engine.arbiter import call_budget_per_tick
from shibuya.engine.run import run_day
from shibuya.llm.fleet import FleetConfig, l4_calls_per_day, l6_in_flight_per_gpu

from .conftest import WORLD_DIR, real_data


def test_l4_and_l6_are_read_from_the_budget_table():
    assert l4_calls_per_day() == 4_000_000
    assert l6_in_flight_per_gpu() == 64


def test_l4_cap_holds_for_a_5000_agent_day_on_the_synthetic_world(capsys):
    n, ticks = 5_000, 1_440
    res = run_day(n_agents=n, seed=1, ticks=ticks, checkpoint_every=720, n_cells=139)
    cap = int(call_budget_per_tick(n) * ticks)
    with capsys.disabled():
        print(
            f"\n[L4] {res.llm_calls:,} 呼 = {res.llm_calls / n:.2f} 呼/体/日 "
            f"(按分上限 {cap:,} / 絶対上限 {l4_calls_per_day():,})"
        )
    assert res.llm_calls <= cap
    assert res.llm_calls <= l4_calls_per_day()
    assert res.llm_calls / n <= 10.0  # L4 の制御目標


@real_data
@pytest.mark.slow
def test_l4_cap_holds_on_the_real_world(capsys):
    n, ticks = 5_000, 1_440
    res = cli.run(n_agents=n, seed=1, world_dir=WORLD_DIR, ticks=ticks, checkpoint_every=720)
    with capsys.disabled():
        print(f"\n[L4 実データ] {res.llm_calls:,} 呼 = {res.llm_calls / n:.2f} 呼/体/日")
    assert res.llm_calls <= int(call_budget_per_tick(n) * ticks)
    assert res.llm_calls / n <= 10.0


# ---------------------------------------------------------------- L6(in-flight)
def test_l6_caps_are_derived_from_the_table_not_hard_coded():
    cfg = FleetConfig(endpoints=("http://a:1", "http://b:2", "http://c:3"))
    assert cfg.resolved_per_replica() == l6_in_flight_per_gpu()
    assert cfg.resolved_max_in_flight() == l6_in_flight_per_gpu() * 3
    assert cfg.resolved_queue_capacity() == cfg.resolved_max_in_flight() * 4
    fields = cfg.manifest_fields()
    assert fields["in_flight_cap_per_replica"] == l6_in_flight_per_gpu()
    assert fields["in_flight_cap_total"] == l6_in_flight_per_gpu() * 3


def test_in_flight_report_flags_a_breach(c6lib):
    cap = l6_in_flight_per_gpu()
    ok = c6lib.in_flight_report(
        {"fleet_peak_in_flight_r0": cap, "fleet_peak_in_flight_r1": cap - 1}, 2, cap
    )
    assert ok["ok"] and ok["max_peak"] == cap and ok["cap_total"] == cap * 2
    bad = c6lib.in_flight_report({"fleet_peak_in_flight_r0": cap + 1}, 1, cap)
    assert not bad["ok"]


def test_a_run_without_a_fleet_reports_no_in_flight_counters(c6lib):
    """mock ランに ``fleet_*`` は立たない(=艦隊ランでだけ検査が効く)。"""
    res = run_day(n_agents=300, seed=1, ticks=24, checkpoint_every=24, n_cells=25)
    fleet_keys = [k for k in res.bridge_counters if k.startswith("fleet_")]
    assert fleet_keys == []
    rep = c6lib.in_flight_report(res.bridge_counters, 7, l6_in_flight_per_gpu())
    assert rep["peaks"] == {} and rep["ok"]


def test_fleet_smoke_keeps_in_flight_within_l6(c6lib, tmp_path, capsys):
    """**偽 vLLM 2 本**に対する 24step スモークで in-flight が L6 を破らない。

    実サーバーには繋がない(``tests/c6/_fake_vllm.py`` はプロセス内の最小 OpenAI 互換面)。
    艦隊そのものの挙動(SSE・再試行・タイムアウト)は ``tests/llm/test_fleet.py`` が見る。
    """
    from ._fake_vllm import FakeVLLM

    cap = l6_in_flight_per_gpu()
    fakes = [FakeVLLM(), FakeVLLM()]
    try:
        client = c6lib.build_fleet_client(
            [f.endpoint for f in fakes], mode="smoke", run_seed=1, stream=False
        )
        try:
            res, route = c6lib.run_smoke(
                n_agents=300, seed=1, ticks=24, world_dir=None,
                tape_path=tmp_path / "tape", fleet=client,
                # D-56 の帰無腕: tick 0 = 世界内 00:00 で全員 ``SLEEPING``。24 tick の
                # 艦隊スモークは既定のままだと呼が 0 になり L6(同時発射上限)を測れない。
                extra={"sleep_suppression": False},
            )
        finally:
            client.close()
        rep = c6lib.in_flight_report(res.bridge_counters, len(fakes), cap)
        with capsys.disabled():
            print(
                f"\n[L6] 経路={route} 呼={int(res.bridge_counters.get('fleet_calls', 0))} "
                f"peak={rep['peaks']} (上限 {cap}/GPU) 実測同時={[f.peak_concurrency for f in fakes]}"
            )
        assert route.startswith("cli.run(fleet=")
        assert rep["peaks"], "fleet_peak_in_flight_r* が診断行に無い"
        assert rep["ok"], rep
        for f in fakes:
            assert 0 < f.peak_concurrency <= cap, f.peak_concurrency
        assert res.run_manifest_fields()["fleet"]["in_flight_cap_per_replica"] == cap
    finally:
        for f in fakes:
            f.close()


@pytest.mark.slow
def test_a_recorded_fleet_run_can_be_checked_offline(c6lib):
    """親がサーバーで回した診断行を ``SHIBUYA_C6_FLEET_COUNTERS``(JSON)で渡して検査する。"""
    import json
    import os

    path = os.environ.get("SHIBUYA_C6_FLEET_COUNTERS", "")
    if not path or not os.path.exists(path):
        pytest.skip("艦隊ランの診断行が無い(SHIBUYA_C6_FLEET_COUNTERS 未設定)")
    counters = json.loads(open(path, encoding="utf-8").read())
    n_replicas = int(counters.get("n_replicas", 7))
    rep = c6lib.in_flight_report(counters, n_replicas, l6_in_flight_per_gpu())
    assert rep["ok"], rep
