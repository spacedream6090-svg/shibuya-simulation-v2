"""第 1 期 1-5(CP3・決定 10-12 §1-4): 権利で止めていた分を止めずに記録に替えた。

- 開閉店(``resolve.request_open_close``): 権利の無い行も効果(開閉の旗)は確定し、結果は ``OK``(行動は起きた=検収 L2)。
  呼び手の過程が ``行為:許可のない行動``(原因 ``Process("rights")``・``where``=店の POI)を 1-3 の出来事の記録へ 1 行ずつ書き、
  自分の持ち物(``n_unauthorized``=状態台帳の O73)で数える。記録の口は ActualLog の ``event_sink`` から引く。
- 開閉の過程の端から端まで: 担当の雇用の行を ``revoke`` で終えると、現場に居る担当の開閉は止まらず記録される。
- 判断の応答の役割語(``LLMBridge``): 行動は起きない(待機/なしに落ちる)ので**出来事は書かず**、数え(許可なし・判定
  しない)を判断の口の持ち物(``n_role_unauthorized``・``n_role_unjudged``=O86)に持つ(検収 L4・L10)。
- 判断の系(decide)の中で回す(検収 L3): 台本の LLM が役割語を答え続けても、出来事は書かれず、数えは manifest に出て、
  final は確かめの口を外したランと同じ。
- 語彙と原因: 1-3 の 55 語のコードは動かない(足した語は末尾)・``過程:rights`` の語は無い・``Process("rights")`` は作れる。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.agents.state import ResultCode
from shibuya.engine import resolve as R
from shibuya.engine.events import log as EV
from shibuya.engine.events import vocab as V
from shibuya.engine.events.links import ActualLogLink
from shibuya.engine.llm_bridge import LLMBridge
from shibuya.engine.processes.opening import OpeningProcess
from shibuya.engine.rights import ledger as L
from shibuya.engine.rights import record as RR
from shibuya.llm import LLMResponse, format_two_line
from shibuya.llm.contract import ACTION_CODES
from shibuya.world.processes.actual_log import ActualLog

from tests.engine.processes.conftest import fake_plan_assets, make_agents, make_world

WHAT = "行為:許可のない行動"


def _unauthorized(log: EV.EventLog) -> list[EV.Event]:
    return [e for e in log.events() if e.what == WHAT]


# ================================================================= 語彙と原因
def test_the_word_and_the_cause_name():
    # 1-7 で末尾に「道具:看板」を足した(1-5 の語のコード 55 は動かない)
    assert RR.WHAT_UNAUTHORIZED == WHAT and V.VOCAB[55] == WHAT and V.code_of(WHAT) == 55
    first55 = (tuple(f"行為:{w}" for w in V.ACT_WORDS) + tuple(f"過程:{w}" for w in V.PROCESS_NAMES)
               + tuple(f"金:{w}" for w in V.MONEY_WORDS) + tuple(f"物:{w}" for w in V.GOODS_WORDS))
    assert V.VOCAB[:55] == first55 and len(first55) == 55   # 1-3 の語のコードは動かない
    assert "過程:rights" not in V.VOCAB_CODES and V.CHECK_PROCESSES == ("rights",)
    assert EV.Process("rights").name == "rights" and "rights" in V.CAUSE_PROCESS_NAMES
    assert V.family_of(WHAT) == "行為" and WHAT not in {f"行為:{w}" for w in V.ACT_WORDS}


# ================================================================= 開閉店(resolve の口と記録の口)
def test_open_close_without_the_right_is_not_stopped_and_is_ok():
    world = make_world(4)
    agents, _ = make_agents(world, 12)
    log = EV.EventLog()
    log.begin_step(5_000)
    got = []

    def on_unauthorized(a, p):  # noqa: ANN001
        got.append(RR.record_unauthorized(log, a, p))

    code = R.request_open_close(
        agents, world, np.array([3, 4]), np.array([0, 1]), np.array([True, False]), 10,
        permitted=np.array([True, False]), on_unauthorized=on_unauthorized)
    assert code.tolist() == [int(ResultCode.OK), int(ResultCode.OK)]          # 行動は起きた(検収 L2)
    assert int(agents.last_result[4]) == int(ResultCode.OK)
    assert int(world.pois.open_now[0]) == 1 and int(world.pois.open_now[1]) == 0  # 止めない(旗は確定)
    rows = _unauthorized(log)
    assert got == [1] and len(rows) == 1
    e = rows[0]
    assert (e.who, e.where, e.t_ns, e.cause) == (4, ("poi", 1), 5_000, EV.Process("rights"))


def test_record_without_a_log_counts_only_and_checks_lengths():
    assert RR.record_unauthorized(None, [1, 2], [0, 0]) == 2
    log = EV.EventLog(enabled=False)
    assert RR.record_unauthorized(log, [1], [0]) == 1 and len(log) == 0
    with pytest.raises(ValueError):
        RR.record_unauthorized(None, [1], [0, 1])
    assert RR.events_of(None) is None


def _linked_actual_log(events: EV.EventLog) -> ActualLog:
    al = ActualLog("actual_log")
    al.event_sink = ActualLogLink(events, {"store_opening": "opening"})
    return al


def test_the_opening_process_records_a_revoked_staff_and_still_opens():
    world = make_world(4)
    agents, _ = make_agents(world, 40)
    log = EV.EventLog()
    proc = OpeningProcess(world, agents, fake_plan_assets([(0, 0, 600, 1_320)]), day_index=0,
                          actual_log=_linked_actual_log(log))
    assert RR.events_of(proc.log) is log
    staff = int(proc.staff_of_poi[0])
    rid = next(i for i, r in enumerate(proc.rights)
               if r.kind == L.EMPLOY and r.object == (L.STORE, 0) and r.holder == (L.AGENT, staff))
    proc.rights.revoke(rid, 1, None)                       # 担当の雇用を終える(書く口の 2 つ目)
    R.rail_arrive(agents, world, np.array([staff]), np.array([int(world.pois.cell[0])]))
    log.begin_step(0)
    proc.step(600)
    assert bool(world.open_mask(600)[0]) is True           # 止めない
    assert int(agents.last_result[staff]) == int(ResultCode.OK)
    assert [(e.who, e.where) for e in _unauthorized(log)] == [(staff, ("poi", 0))]
    assert proc.n_unauthorized == 1 and proc.unauthorized_tally() == {"open_close": 1}


# ================================================================= 判断の応答の役割語(LLMBridge)
class WordLLM:
    def __init__(self, word: str) -> None:
        self.word = word

    def complete(self, request):
        return LLMResponse(text=format_two_line("台本の理由", self.word, "なし", "なし"), source="scripted")


class _Owner:
    """権利台帳の持ち主(開閉の過程の代わり)。"""

    def __init__(self, rights: L.Rights) -> None:
        self.rights = rights
        self.tick_seconds = 60


def _rights_with_employee(agent: int) -> L.Rights:
    led = L.Rights()
    led.grant(L.Right(holder=(L.AGENT, agent), object=(L.ORG, 0), kind=L.EMPLOY, source="試験"))
    return led


@pytest.mark.parametrize("word", ["開閉店", "補充", "接客", "価格改定"])
def test_an_employee_word_without_employment_is_counted_not_written(word):
    owner = _Owner(_rights_with_employee(1))
    check = RR.RoleActCheck(owner)
    assert check(2, 1, word) is False and check(1, 1, word) is True
    bridge = LLMBridge(WordLLM(word))
    bridge.attach_role_rights(check)
    res = bridge.call(agent_id=2, tick=1, wake_class=1, cell=0)       # 体 2 は雇用の行を持たない
    assert res.role_action and res.action_code == ACTION_CODES["待機"]   # 落とし方は今までどおり
    bridge.call(agent_id=1, tick=1, wake_class=1, cell=0)             # 体 1 は持つ=数えない
    c = bridge.counters()
    assert (bridge.n_role_unauthorized, bridge.n_role_unjudged) == (1, 0)
    assert c["role_unauthorized"] == 1 and c["role_unjudged"] == 0 and c["role_actions"] == 2


@pytest.mark.parametrize("word, verdict", [("発車", None), ("放送", None), ("計画改訂", None), ("撮影", True)])
def test_duty_words_are_not_judged_and_everyone_words_are_allowed(word, verdict):
    owner = _Owner(L.Rights())
    bridge = LLMBridge(WordLLM(word))
    bridge.attach_role_rights(RR.RoleActCheck(owner))
    assert RR.RoleActCheck(owner)(2, 1, word) is verdict
    res = bridge.call(agent_id=2, tick=1, wake_class=1, cell=0)
    assert res.role_action
    assert (bridge.n_role_unauthorized, bridge.n_role_unjudged) == (0, 1 if verdict is None else 0)


def test_without_the_check_nothing_is_counted_and_the_code_is_the_same():
    bridge = LLMBridge(WordLLM("開閉店"))
    res = bridge.call(agent_id=2, tick=1, wake_class=1, cell=0)
    assert bridge.role_rights is None and res.role_action and res.action_code == ACTION_CODES["待機"]
    assert (bridge.n_role_unauthorized, bridge.n_role_unjudged) == (0, 0)


# ================================================================= 判断の系(decide)の中(検収 L3)
KW = dict(n_agents=60, seed=3, n_cells=9, ticks=720, budget=60.0, checkpoint_every=120, vocab_version="v1")


@pytest.mark.parametrize("word", ["開閉店", "発車"])
def test_role_words_inside_the_decide_system(word, monkeypatch):
    from shibuya.engine.run import run_day

    res = run_day(llm=WordLLM(word), **KW)
    m = res.run_manifest_fields()["rights"]["unauthorized"]
    calls = int(res.bridge_counters["role_actions"])
    assert calls > 0 and res.event_log.what_counts().get(WHAT, 0) == 0   # 行動は起きない=出来事は書かない
    if word == "開閉店":
        assert 0 < m["role_action_unauthorized"] <= calls and m["role_action_unjudged"] == 0
    else:
        assert m["role_action_unjudged"] == calls and m["role_action_unauthorized"] == 0
    assert m["open_close"] == 0
    # 確かめの口を外しても final と呼数は同じ(数えは計器だけ)
    monkeypatch.setattr(RR.RoleActCheck, "__call__", lambda self, a, s, w: True)
    other = run_day(llm=WordLLM(word), **KW)
    assert other.final_hash == res.final_hash and other.llm_calls == res.llm_calls
    assert other.run_manifest_fields()["rights"]["unauthorized"]["role_action_unauthorized"] == 0


# ================================================================= 既定のランでは 0
def test_a_default_run_records_nothing():
    from shibuya.engine.run import run_day

    res = run_day(n_agents=60, seed=3, n_cells=9, ticks=240, budget=60.0, vocab_version="v3", checkpoint_every=120)
    assert res.event_log.what_counts().get(WHAT, 0) == 0
    m = res.run_manifest_fields()["rights"]
    assert m["unauthorized"] == {"open_close": 0, "role_action_unauthorized": 0, "role_action_unjudged": 0}
    assert res.runner.opening.n_unauthorized == 0
