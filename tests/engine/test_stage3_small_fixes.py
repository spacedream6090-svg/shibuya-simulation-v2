"""3 段目と同じ回の小修正 3 件(第289): ① 購入の件数は台帳が通した行だけ ② Q24 着いた後の活動は
最新の応答の活動 ③ Q25 名指しの即時閉店の B6 に店名・閉店中・W7 の開店時刻。
"""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np

from shibuya.agents.state import AgentState, IntentKind, ResultCode
from shibuya.engine import commit as C
from shibuya.engine import resolve as R
from shibuya.engine.chooser import NearestChooser
from shibuya.engine.poi_target import TargetResolver
from shibuya.engine.run import _named_closed_lookup
from shibuya.llm.contract import UntilKind, parse_target
from shibuya.perception import channels as ch
from shibuya.perception import renderer as PR
from shibuya.perception.renderer import Renderer

from tests.engine.test_intent_hold import (
    _FakeGoods,
    _agents0,
    _payload,
    _row,
    _tick,
    _walk_to_cell3,
)
from tests.engine.test_move_destination import NOON, _world


# ------------------------------------------------------------------ ① 購入の件数
class _PickyMoney:
    """``refuse`` の体の支払いを却下する偽の金の台帳(却下の行は所持金を動かさない)。"""

    def __init__(self, agents, refuse):
        self.agents = agents
        self.refuse = set(refuse)

    def purchase_many(self, buyers, stores, amounts, tick):
        r = self.agents.registry
        status = np.zeros(np.asarray(buyers).size, dtype=np.int64)
        for k, b in enumerate(np.asarray(buyers).tolist()):
            if b in self.refuse:
                status[k] = 1
            else:
                r.money[b] = np.int32(int(r.money[b]) - int(amounts[k]))
        return status


def test_n_purchases_counts_only_the_rows_the_ledger_passed():
    w = _world()
    ag = AgentState(3)
    with ag.writable(), w.writable():
        ag.registry.money[:] = 10_000
        w.pois.stock[7] = 5
        led = SimpleNamespace(money=_PickyMoney(ag, refuse={1}), goods=_FakeGoods(w.pois.stock))
        out = R.ResolveOutcome(tick=NOON, ledger=led)
        R._complete_buy(ag, w, np.array([0, 1, 2]), np.array([7, 7, 7]),
                        np.array([800, 800, 800]), NOON, out)
    assert out.n_purchases == 2                 # 却下された体 1 は数えない(以前は 3)
    assert out.revenue_delta == 1_600
    assert int(ag.registry.last_result[1]) == int(ResultCode.MONEY_SHORT)


# ------------------------------------------------------------------ ② Q24
def test_the_latest_kept_response_activity_is_restored_after_arrival_q24():
    t = NOON
    w, ag, act, il, space, res = _walk_to_cell3(t)
    # 歩いている途中の なし(意図を保つ)に活動「散歩・45 分」
    _tick(w, ag, act, il, space, t + 1, _row(t + 1, C.ACT_NONE),
          ([0], [C.ACT_NONE], [_payload(text="散歩", value=45)]))
    r = ag.registry
    k = 2
    while int(r.intent_action[0]) != -1 and k < 10:
        _tick(w, ag, act, il, space, t + k)
        k += 1
    done = t + k - 1
    assert int(r.last_action[0]) == C.ACT_EAT and int(r.last_result[0]) == int(ResultCode.OK)
    assert act.text[0] == "散歩" and int(r.activity_until[0]) == done + 45
    assert il.counters()["latest_activity_used"] == 1


def test_a_kept_response_without_an_activity_keeps_the_one_from_setting_q24():
    t = NOON
    w, ag, act, il, space, res = _walk_to_cell3(t)
    _tick(w, ag, act, il, space, t + 1, _row(t + 1, C.ACT_NONE),
          ([0], [C.ACT_NONE], [_payload(text="なし", kind=UntilKind.MINUTES, value=5)]))
    r = ag.registry
    k = 2
    while int(r.intent_action[0]) != -1 and k < 10:
        _tick(w, ag, act, il, space, t + k)
        k += 1
    done = t + k - 1
    assert act.text[0] == "食事" and int(r.activity_until[0]) == done + 30  # 立てたときの活動
    assert il.counters()["latest_activity_used"] == 0


# ------------------------------------------------------------------ ③ Q25
def test_the_resolver_records_the_immediate_named_closure_q25():
    w = _world(visible={0: [(4, 30)]})
    with w.writable():
        w.pois.open_now[:] = 1
        w.pois.open_now[4] = 0
    res = TargetResolver(world=w, chooser=NearestChooser(), seed=1)
    io: dict[int, tuple[int, int]] = {}
    ag = _agents0(w, 7)
    res.resolve(ag, NOON, np.array([5, 6]), np.array([C.ACT_EAT, C.ACT_EAT]),
                [parse_target("カフェ・ベローチェ"), None], is_eat=np.array([True, True]),
                is_buy_like=np.array([False, False]), intent_out=io)
    assert res.named_closed == {5: (4, NOON)}   # 名指しの即時閉店の体だけ


def _renderer_with(lookup):
    w = _world()
    a = AgentState(2)
    with a.writable():
        a.cell[:] = 0
        a.money[:] = 1_000
        a.last_action[:] = C.ACT_EAT
        a.last_result[:] = int(ResultCode.CLOSED)
        a.last_result_tick[:] = NOON
    w.cells.density[:] = w.compute_density(a.cell)
    r = Renderer(w, a, seed=3, vocab_version="v3")
    r.prepare_tick(NOON + 1)
    r.named_closed_lookup = lookup
    return r


def test_b6_names_the_closed_shop_and_the_opening_time_only_for_that_agent_q25():
    base = _renderer_with(None)
    before = [base.render(i, tick=NOON + 1, wake_reason=3) for i in (0, 1)]
    note = {0: (4, NOON, 7 * 60 + 30)}
    r = _renderer_with(lambda aid: note.get(aid))
    after = [r.render(i, tick=NOON + 1, wake_reason=3) for i in (0, 1)]
    b6 = after[0].blocks["B6"].decode("utf-8")
    name = str(r.assets.poi_name[4])
    phrase = PR.named_closed_note(name, 7 * 60 + 30)
    assert phrase in b6 and "閉店中・07:30に開く" in phrase
    assert "営業時間外" in b6                                  # RESULT_TEXT の短句は変えない
    assert ch.estimate_tokens(phrase) <= PR.NAMED_CLOSED_NOTE_MAX_TOKENS
    assert after[1].prompt_hash == before[1].prompt_hash    # 該当しない体は 1 バイトも変わらない
    assert after[0].prompt_hash != before[0].prompt_hash
    assert r.named_closed_notes == 1
    # 失敗の tick が違う(=その後に別の失敗/成功をした)なら載せない
    stale = _renderer_with(lambda aid: (4, NOON - 5, 450) if aid == 0 else None)
    assert stale.render(0, tick=NOON + 1, wake_reason=3).prompt_hash == before[0].prompt_hash
    # 開店時刻が無い(W7 に区間が無い)なら「閉店中」だけ
    assert PR.named_closed_note("おむすび権米衛", -1) == "(おむすび権米衛は閉店中)"
    long = PR.named_closed_note("とても長い名前のお店の本店ビルディング渋谷", 600)
    assert ch.estimate_tokens(long) <= 15 and long.endswith("は閉店中・10:00に開く)")


def test_the_engine_lookup_reads_the_w7_opening_matrix_q25():
    om = np.zeros((3, 1440), dtype=bool)
    om[0, 600:1200] = True                     # POI 0: 10:00-20:00
    pa = SimpleNamespace(plan_poi=np.array([1, 2]), plan_day=np.array([1, 3]),
                         plan_start=np.array([420, 540]), plan_end=np.array([600, 700]))
    runner = SimpleNamespace(opening=SimpleNamespace(open_matrix=om, assets=pa))
    resolver = SimpleNamespace(named_closed={7: (0, 300), 8: (0, 1300), 9: (1, 1300), 10: (2, 100)})
    look = _named_closed_lookup(resolver, runner, 0, 60)
    assert look(7) == (0, 300, 600)            # 当日の後の最初の開店
    assert look(8) == (0, 1300, -1)            # 当日も翌日(火)も区間なし
    assert look(9) == (1, 1300, 420)           # 翌日(火)の最初の開始
    assert look(10) == (2, 100, -1)            # 翌日は水ではない
    assert look(99) is None
    assert _named_closed_lookup(resolver, None, 0, 60)(7) == (0, 300, -1)  # W7 が無い世界
