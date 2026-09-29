"""第2波 §2A 項 3-1: 古典の腕の**交際・付き合い(符号 18)の相手=知人**(Q42 (b)・指示書 §0-3・§4)のテスト。

旧(``near_first``)は B5 近接行の最初の人(=見知らぬ人)に話しかけ、C10 の関係と記憶を汚していた。既定
(``acquaintance``)は近接行に載っている知人(生きている関係辺の相手)のうち活性 A が最大の人・居なければ「なし・待つ」。
見るもの: (a) A 最大・未知の人は選ばない・同点は近接行の順・居なければ待つ・招待者への返事は不変 (b) 旧の再現
(c) ラン: 関係 off では classical から会話を始めない・関係 on では知人と話す・golden の新旧・切替口。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from shibuya.agents.state import Activity, AgentKind, AgentState
from shibuya.engine import classical as CL
from shibuya.world.state import World

DOC, MD5 = CL.load_activity_prior()
SRC = Path("src/shibuya")
WORLD = "data/world/v2"
PROMPT = "[B5 近接] 近くの人物: P-3(未知)、P-7(知人)、P-5(知人)、P-9(未知)。"

#: classical 1,500 体・seed 1・v3 の既定(acquaintance・関係 off)の final と呼数(旧は
#: ``tests/perception/test_near_tiebreak.CLASSICAL_1500_GOLDEN["hash"]`` を ``classical_social="near_first"`` で再現)。
CLASSICAL_1500_GOLDEN_ACQ = ("4f78f3c0ce95d8e205c700952d756cd2e443da86bd54c60c073f39cafd5ec00a", 25_808)


def _bound(n: int = 12, social: str = "acquaintance") -> CL.ClassicalPolicy:
    w = World.synthetic(n_cells=9, seed=1)
    a = AgentState(n)
    with a.writable():
        a.cell[:] = 0
        a.hunger[:] = 8
        a.age[:] = 30
        a.kind[:] = AgentKind.VISITOR
        a.activity[:] = int(Activity.IDLE)
    pol = CL.ClassicalPolicy(seed=1, prior=CL.ActivityPrior(DOC, "weekday", "kanto"), prior_md5=MD5, social=social)
    pol.bind(agents=a, world=w, home_cell=np.full(n, 1), work_cell=np.full(n, 2), school_cell=np.full(n, -1),
             has_work=np.zeros(n, dtype=bool), boundary_agent=np.zeros(0, dtype=np.int64),
             boundary_tick=np.zeros(0, dtype=np.int64))
    return pol


def _acq(table: dict[int, float]):
    seen: list[tuple[int, int, list[int]]] = []

    def fn(aid: int, tick: int, ids: list[int]) -> np.ndarray:
        seen.append((aid, tick, list(ids)))
        return np.asarray([table.get(i, -np.inf) for i in ids], dtype=np.float64)

    return fn, seen


# ================================================================= (a) 選び方
def test_talks_to_the_nearby_acquaintance_with_the_largest_activation():
    pol = _bound()
    pol.acq_fn, seen = _acq({7: 0.5, 5: 1.25, 3: -np.inf})
    pol._tick = 40
    assert pol._respond("18", 0, 0, PROMPT, -1) == (CL.REASON_ACTIVITY, "会話", "P-5", "話す", "30分")
    assert seen == [(0, 40, [3, 7, 5, 9])]                          # 近接行の人(自分を除く・行の順)
    pol.acq_fn, _ = _acq({7: 1.0, 5: 1.0})
    assert pol._respond("18", 0, 0, PROMPT, -1)[2] == "P-7"         # 同点は近接行の順(距離の順)
    pol.acq_fn, _ = _acq({})                                         # 近接行に知人が居ない(未知の人だけ)
    assert pol._respond("18", 0, 0, PROMPT, -1)[1:4] == ("なし", "なし", "待つ")
    assert pol._respond("18", 0, 0, "", -1)[1:4] == ("なし", "なし", "待つ")   # 誰も見えない
    pol.acq_fn = None                                                # 関係の腕が off=知人は居ない
    assert pol._respond("18", 0, 0, PROMPT, -1)[1:4] == ("なし", "なし", "待つ")
    assert pol._respond("18", 0, 0, PROMPT, 9)[1:3] == ("会話", "P-9")   # 招待者への返事は不変
    assert pol.counts["talk_acquaintance"] == 3 and pol.counts["talk_no_acquaintance"] == 3
    pol.acq_fn, _ = _acq({3: 2.0})
    assert pol._respond("18", 3, 0, PROMPT, -1)[1] == "なし"         # 自分(P-3)は相手にしない


def test_near_first_reproduces_the_old_rule():
    pol = _bound(social="near_first")
    pol.acq_fn, seen = _acq({5: 9.0})
    assert pol._respond("18", 0, 0, PROMPT, -1)[1:3] == ("会話", "P-3")   # 最初の人(未知でも)
    assert seen == []                                                     # 知人の表は引かない
    assert pol._respond("18", 3, 0, PROMPT, -1)[1:3] == ("会話", "P-7")
    with pytest.raises(ValueError):
        _bound(social="friends")
    assert CL.CLASSICAL_SOCIAL_MODES == ("acquaintance", "near_first") and CL.DEFAULT_CLASSICAL_SOCIAL == "acquaintance"


def test_busy_or_asleep_or_out_of_reach_acquaintances_are_skipped():
    """検収後: 会話中・就寝中の知人(resolve._UNADDRESSABLE)と、会話の届かない知人(別のセル・edge 幾何なら 2 m 超)
    は候補から外す。会話中の知人(A が大きい)と空いている知人が居れば、空いている方を選ぶ。"""
    from shibuya.engine.run import classical_acq_addressable

    pol = _bound()
    a = pol.agents
    r = a.registry
    with a.writable():
        r.cell[:] = 0
        r.activity[7] = int(Activity.CONVERSING)   # A 最大の知人は会話中
        r.activity[5] = int(Activity.IDLE)         # 空いている知人
        r.activity[9] = int(Activity.SLEEPING)
    table = {7: 2.0, 5: 1.0, 9: 3.0}

    def fn(aid, tick, ids):
        A = np.asarray([table.get(i, -np.inf) for i in ids], dtype=np.float64)
        return classical_acq_addressable(a, aid, ids, A, by_distance=False)

    pol.acq_fn = fn
    assert pol._respond("18", 0, 0, PROMPT, -1)[2] == "P-5"                   # 空いている方
    got = classical_acq_addressable(a, 0, [3, 7, 5, 9], np.array([0.0, 2.0, 1.0, 3.0]), by_distance=False)
    assert got.tolist() == [0.0, -np.inf, 1.0, -np.inf]
    with a.writable():
        r.cell[5] = 1                                                         # 別のセル=届かない
    assert pol._respond("18", 0, 0, PROMPT, -1)[1:4] == ("なし", "なし", "待つ")
    with a.writable():
        r.cell[5] = 0
        r.xy[0] = (0.0, 0.0)
        r.xy[5] = (5.0, 0.0)                                                  # 同じセルでも 5 m
    assert classical_acq_addressable(a, 0, [5], np.array([1.0]), by_distance=False).tolist() == [1.0]
    assert classical_acq_addressable(a, 0, [5], np.array([1.0]), by_distance=True).tolist() == [-np.inf]
    assert classical_acq_addressable(a, 0, [0, -1], np.array([1.0, 1.0]), by_distance=False).tolist() == [-np.inf, -np.inf]


# ================================================================= (c) ラン
def test_run_golden_and_arms():
    from shibuya.world.assets import assets_available

    if not assets_available(WORLD):
        pytest.skip("W 資産(data/world/v2)が無い")
    from shibuya import cli
    from shibuya.engine.run import run_day

    with pytest.raises(ValueError):
        run_day(n_agents=10, ticks=2, vocab_version="v3", policy="classical", classical_social="all")
    src = (SRC / "cli.py").read_text(encoding="utf-8")
    assert '"--classical-social"' in src and "classical_social=str(args.classical_social)" in src
    kw = dict(n_agents=1500, seed=1, world_dir=WORLD, vocab_version="v3", policy="classical", chooser="classical")
    r = cli.run(**kw)
    assert (r.final_hash, int(r.llm_calls)) == CLASSICAL_1500_GOLDEN_ACQ
    m = r.run_manifest_fields()["classical"]
    assert m["social"] == "acquaintance"
    c = m["counts"]
    assert c.get("talk_acquaintance", 0) == 0 and c["talk_no_acquaintance"] == c["activity:18"] > 0  # 関係 off
    # 関係 on(記憶 on)では近接行の知人と話す
    on = cli.run(n_agents=3000, seed=1, world_dir=WORLD, vocab_version="v3", policy="classical",
                 chooser="classical", memory="on", relations="on", ticks=720)  # 知人が同じセルに来る規模
    c_on = on.run_manifest_fields()["classical"]["counts"]
    assert c_on.get("talk_acquaintance", 0) > 0
    assert c_on.get("talk_acquaintance", 0) + c_on.get("talk_no_acquaintance", 0) == c_on["activity:18"]
