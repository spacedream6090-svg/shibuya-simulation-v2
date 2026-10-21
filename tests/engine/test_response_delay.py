"""10a(指示書 10-03 §3-5 A9): 応答の遅れ「発射 +1 tick」(〔第 4 期 4-3 版上げ 3 回目の第 2 部〕旧の +2 の切替口
``response_delay`` は消した)。

固定する性質(偽 vLLM ``tests.llm.test_fleet.FakeVLLM``・実サーバーへは繋がない)
- 艦隊: tick T に発射した呼は、既定(``response_delay=1``)では T+1 の①(反映)で行動になる。
  ``response_delay=2`` では旧のとおり T+2。どちらも受け取り(``observed_tick``)は T+1。
- mock(``fleet=None``)は既に +1 で、切替口の値に依らず結果が 1 バイトも変わらない。
- 録画 → 再生(``replay_inbox`` の経路)は、録画と同じ切替口の値で完全に一致する(+1 と +2 の両方)。
- 会話の発話の記録の tick は動かない(受け取った tick のまま)。動くのは「同じ tick の中の順」だけで、
  旧(+2)では発話を受け取る前に起床候補を作るので、まだ発話していない話者がもう一度起こされうる。

①への反映の tick は ``commit.intents_from_responses`` に渡る (tick, 体) で観測する(読むだけの包み)。
"""

from __future__ import annotations

from collections import Counter

import numpy as np
import pytest

from shibuya.engine import commit as C
from shibuya.engine import run as RUN
from shibuya.engine.run import run_day
from shibuya.engine.tape import Tape
from shibuya.llm.fleet import FleetBridge  # 1-0: run.py は FleetBridge を import しない(組み立ては engine.systems.build)

from tests.engine.test_fleet_wiring import (
    CONV_AGENTS,
    CONV_TICKS,
    _conv_world,
    make_client,
    run_mock,
)
from tests.engine.test_tape_deferred import common, record_and_replay
from tests.engine.test_tape_deferred import make_client as make_client_d58
from tests.llm.test_fleet import FakeVLLM

TICKS = 24


@pytest.fixture
def fleet_servers():
    servers = [FakeVLLM(), FakeVLLM(), FakeVLLM()]
    try:
        yield servers
    finally:
        for s in servers:
            s.close()


@pytest.fixture
def applied(monkeypatch):
    """①で行動に変えた (tick, 体) を控える(``intents_from_responses`` を読むだけで包む)。"""
    got: list[tuple[int, int]] = []
    orig = C.intents_from_responses

    def wrap(agents, world, space, tick, agent_ids, *a, **k):
        got.extend((int(tick), int(x)) for x in np.asarray(agent_ids).tolist())
        return orig(agents, world, space, tick, agent_ids, *a, **k)

    monkeypatch.setattr(C, "intents_from_responses", wrap)
    return got


def _fleet_run(servers, tmp_path, delay: int, **kw):
    from shibuya.world.state import World

    client = make_client(servers)
    return run_day(
        n_agents=200, seed=1, world=World.synthetic(n_cells=24, seed=1), ticks=TICKS, fleet=client,
        fleet_wait_s=10.0, renderer="stub", processes=False, population=False, world_dir=None,
        sleep_suppression=False, tape_path=tmp_path / f"tape_{delay}", **kw,
    )


@pytest.mark.parametrize("delay", [1])  # 〔第 2 部〕2(旧)は消した
def test_fleet_call_fired_at_T_is_applied_at_T_plus_delay(fleet_servers, tmp_path, applied, delay):
    res = _fleet_run(fleet_servers, tmp_path, delay)
    rows = [r for r in Tape(tmp_path / f"tape_{delay}").rows() if not r.is_deferred]
    assert rows and res.llm_calls == len(rows)
    assert all(r.observed_tick == r.tick + 1 for r in rows if r.observed_tick < TICKS)  # 受け取りは T+1
    want = Counter((r.tick + delay, r.agent_id) for r in rows if r.tick + delay < TICKS)
    got = Counter(applied)
    assert got == want, f"+{delay} で反映されていない"
    assert res.run_manifest_fields()["response_delay"] == delay


def test_mock_is_already_plus_one_and_the_switch_is_gone(tmp_path, applied):
    """mock は発射 +1 tick で反映(既に +1)。〔第 4 期 4-3 版上げ 3 回目の第 2 部〕切替口 response_delay(2=旧)は消した=
    渡すと止まる。"""
    run_mock(tape_path=tmp_path / "m1")
    first = list(applied)
    rows = list(Tape(tmp_path / "m1").rows())
    want = Counter((r.tick + 1, r.agent_id) for r in rows if r.tick + 1 < 24)
    assert Counter(first) == want
    with pytest.raises(TypeError):
        run_mock(tape_path=tmp_path / "m2", response_delay=2)


@pytest.mark.parametrize("delay", [1])  # 〔第 2 部〕2(旧)は消した
def test_record_and_replay_match_under_each_delay(tmp_path, delay):
    servers = [FakeVLLM(), FakeVLLM()]
    try:
        for srv in servers:
            srv.total_delay_s = 0.02
        client = make_client_d58(servers, per_replica_in_flight=4, queue_capacity=8)
        rec, rep = record_and_replay(client, tmp_path / f"t{delay}", ticks=20, budget=30.0, fleet_wait_s=2.0)
    finally:
        for s in servers:
            s.close()
    assert rec.bridge_counters["fleet_deferred_queue_full"] > 0
    assert [c.combined for c in rep.checkpoints] == [c.combined for c in rec.checkpoints]
    assert rep.final_hash == rec.final_hash and rep.tape_miss_count == 0
    assert rep.bridge_counters["fleet_reinjected"] == rec.bridge_counters["fleet_reinjected"]


def test_replay_of_a_plus2_tape_stops(tmp_path):
    """〔第 2 部〕+2(旧)で録ったテープ(meta の値 2)と値の無いテープ(10a より前)は再生しない=止まる(旧値の再現は安定版の
    タグ)。前は +2 で録って +2 で再生できた。"""
    import json

    from shibuya.engine.tape import RUN_META_FILENAME
    from tests.engine.test_tape_wiring import BoomLLM

    servers = [FakeVLLM(), FakeVLLM()]
    try:
        for srv in servers:
            srv.total_delay_s = 0.02
        client = make_client_d58(servers, per_replica_in_flight=4, queue_capacity=8)
        rec = run_day(fleet=client, tape_path=tmp_path / "t", fleet_wait_s=2.0, budget=30.0, **common(20))
    finally:
        for s in servers:
            s.close()
    rep1 = run_day(mode="replay", replay=tmp_path / "t", llm=BoomLLM(), budget=30.0, **common(20))
    assert rep1.final_hash == rec.final_hash
    mp = tmp_path / "t" / RUN_META_FILENAME
    d = json.loads(mp.read_text(encoding="utf-8"))
    mp.write_text(json.dumps({**d, "response_delay": 2}) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="response_delay=2"):
        run_day(mode="replay", replay=tmp_path / "t", llm=BoomLLM(), budget=30.0, **common(20))
    d.pop("response_delay")
    mp.write_text(json.dumps(d) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="response_delay=None"):
        run_day(mode="replay", replay=tmp_path / "t", llm=BoomLLM(), budget=30.0, **common(20))


@pytest.mark.parametrize("delay", [1])  # 〔第 2 部〕2(旧)は消した
def test_utterances_are_recorded_at_the_receiving_tick(fleet_servers, monkeypatch, delay):
    """会話ターンの発話は受け取った tick(発射 +1)で記録される=+1 でも +2 でも tick は動かない。"""
    from shibuya.agents.state import WakeCondition
    from shibuya.engine.conversation import ConversationManager

    for s in fleet_servers:
        s.pair_talk = True
    utt: list[tuple[int, int]] = []
    orig = ConversationManager.utterance

    def spy(self, agent_id, tick, **k):
        utt.append((int(agent_id), int(tick)))
        return orig(self, agent_id, tick, **k)

    monkeypatch.setattr(ConversationManager, "utterance", spy)
    turn = int(WakeCondition.CONVERSATION_TURN)
    fired: list[tuple[int, int]] = []
    orig_submit = FleetBridge.submit

    def submit(self, batch, now_tick):
        fired.extend((int(c.agent_id), int(c.tick)) for c in batch if int(c.condition) == turn)
        return orig_submit(self, batch, now_tick=now_tick)

    monkeypatch.setattr(FleetBridge, "submit", submit)
    client = make_client(fleet_servers)
    res = run_day(n_agents=CONV_AGENTS, seed=1, world=_conv_world(), ticks=CONV_TICKS, fleet=client,
                  fleet_wait_s=10.0, renderer="stub", processes=False, population=False, world_dir=None)
    assert res.conversation_sessions > 0 and fired
    want = Counter((a, t + 1) for a, t in fired if t + 1 < CONV_TICKS)
    assert Counter(utt) == want
