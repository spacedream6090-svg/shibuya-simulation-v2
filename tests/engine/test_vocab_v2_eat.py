"""語彙 v2「食事」のエンジン側 — D-71 §3 E(飲食店オブジェクトの affordance)。

見るもの
(i)   **既定 v1 は 1 バイトも動かない**: ``_APPLY`` は 13 分岐のまま・同じ種の mock ランで
      checkpoint・呼数・行動分布が v1 の値と一致する/
(ii)  v2 で「食事」が発火し、**金が世帯から店舗へ移り**(科目=消費支出)保存則が閉じる/
(iii) 飲食店にいない/所持金不足/営業時間外で ``NOT_IN_EATERY``/``MONEY_SHORT``/``CLOSED``/
(iv)  効果は購入と違う: **棚在庫も所持品も動かない**(摂食≠購買)・空腹は下がる・在店になる/
(vi)  ``action_usage``(D-71 §3 J「語ごとの使用率」)が run manifest に出る。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.agents.schedule import synthesize
from shibuya.agents.state import Activity, AgentState, ResultCode
from shibuya.engine import commit as C
from shibuya.engine import resolve as R
from shibuya.engine.run import run_day
from shibuya.llm import LLMResponse, format_two_line
from shibuya.llm.contract import ACTION_WORD_EAT, EAT_ACTION_CODE
from shibuya.world.state import World


class WordLLM:
    """常に同じ行動語(表層形)を返す台本 mock(``test_intent_mode_open.WordLLM`` と同じ)。"""

    def __init__(self, word: str) -> None:
        self.word = word
        self.n_calls = 0

    def complete(self, request):
        self.n_calls += 1
        return LLMResponse(
            text=format_two_line("台本の理由", self.word, "なし", "なし"), source="scripted"
        )


#: 営業時間(既定 10:00-22:00 = tick 600-1320)に**入る**窓。短い窓だと全件 ``CLOSED`` になる。
OPEN_HOURS = dict(
    n_agents=200, seed=4, ticks=700, checkpoint_every=700, n_cells=16, conversations=False
)
#: v1/v2 の比較に使う窓(``test_intent_mode_open.SMALL`` と同じ)。
SMALL = dict(n_agents=300, seed=4, ticks=540, checkpoint_every=540, n_cells=16)


# ------------------------------------------------------------------ 単体(決定論・1 tick)
def _scene(n: int = 8, tick: int = 700, money: int = 10_000, hunger: int = 9):
    """飲食店のセルに n 体を置いた 1 tick の場面。"""
    w = World.synthetic(n_cells=16, seed=1)
    a = AgentState(n)
    R.initialize(a, w, synthesize(n, 1, w.n_cells))
    eatery = int(np.flatnonzero(w.eatery_mask)[0])
    cell = int(w.pois.cell[eatery])
    with a.writable():
        a.registry.node[:] = w.assets.cell_rep_node[cell]
        a.registry.cell[:] = cell
        a.registry.money[:] = money
        a.registry.hunger[:] = hunger
    return w, a, eatery, cell, tick


def _eat(w, a, tick, n):
    space = C.ResourceSpace(w.n_poi, a.n, w.n_cells)
    ids = np.arange(n, dtype=np.int64)
    batch = C.intents_from_responses(
        a, w, space, tick, ids, np.zeros(n, dtype=np.int64),
        np.full(n, EAT_ACTION_CODE, dtype=np.int64),
    )
    plan = C.arbitrate_resources(batch, tick, b"salt" * 4, space, w.pois.stock, w.pois.capacity)
    return batch, R.apply(plan.confirmed, plan.losers, a, w, tick, vocab_version="v2")


def test_the_eat_target_is_an_eatery_poi_in_the_same_cell():
    w, a, eatery, cell, tick = _scene()
    batch, _ = _eat(w, a, tick, 8)
    assert set(batch.target_id.tolist()) == {eatery}
    assert bool(w.eatery_mask[eatery]), "対象は飲食店(cat が飲食帯)に限られる"


# ------------------------------------------------------------------ (ii)(iv) 効果
def test_eating_moves_money_to_the_shop_and_conserves():
    w, a, eatery, cell, tick = _scene()
    price = int(w.pois.price[eatery])
    money0 = int(a.registry.money.astype(np.int64).sum())
    rev0 = int(w.pois.revenue.astype(np.int64).sum())
    stock0 = w.pois.stock.copy()
    holdings0 = a.registry.holdings.copy()
    _, out = _eat(w, a, tick, 8)
    assert out.n_meals > 0
    assert out.meal_yen == out.n_meals * price
    money1 = int(a.registry.money.astype(np.int64).sum())
    rev1 = int(w.pois.revenue.astype(np.int64).sum())
    # 保存則: 世帯の減り = 店舗の増え(科目は購入と同じ 消費支出)
    assert money0 - money1 == rev1 - rev0 == out.meal_yen
    # 摂食≠購買: 棚在庫も所持品も動かさない
    assert np.array_equal(w.pois.stock, stock0)
    assert np.array_equal(a.registry.holdings, holdings0)


def test_eating_relieves_hunger_and_keeps_the_agent_in_the_shop():
    w, a, eatery, cell, tick = _scene(hunger=9)
    _, out = _eat(w, a, tick, 8)
    ate = np.flatnonzero(a.registry.last_result == int(ResultCode.OK))
    assert ate.size == out.n_meals > 0
    assert int(a.registry.hunger[ate[0]]) == 9 - R.EAT_HUNGER_RELIEF
    assert int(a.registry.activity[ate[0]]) == int(Activity.SHOPPING), "在店=その tick は動かない"
    assert int(a.registry.last_action[ate[0]]) == EAT_ACTION_CODE


def test_the_declared_dwell_is_expedient_and_reuses_the_existing_seat_machinery():
    """所要時間 20 分は**契約行の宣言値**(専用タイマーは未実装=在席の回転率に従う)。"""
    assert R.EAT_DWELL_MINUTES == 20
    assert R.EAT_HUNGER_RELIEF == R.BUY_HUNGER_RELIEF, "新しい数を作らない(既存値の再利用)"


# ------------------------------------------------------------------ (iii) 失敗コード
def test_not_in_eatery():
    """飲食店が無いセルに居る体は ``NOT_IN_EATERY``(``BAD_TARGET`` ではない)。"""
    w, a, eatery, cell, tick = _scene()
    non_food = [
        c for c in range(w.n_cells)
        if not bool(w.eatery_mask[w.pois.cell == c].any())
    ]
    assert non_food, "合成世界に飲食店のないセルがあること"
    with a.writable():
        a.registry.node[:] = w.assets.cell_rep_node[non_food[0]]
        a.registry.cell[:] = non_food[0]
    _, out = _eat(w, a, tick, 8)
    assert out.n_meals == 0
    assert out.per_result.get(int(ResultCode.NOT_IN_EATERY)) == 8


def test_money_short():
    """所持金 < 価格 は ``MONEY_SHORT``(店の 1 tick 受け入れ数で落選した分は別コード)。"""
    w, a, eatery, cell, tick = _scene(money=1)
    _, out = _eat(w, a, tick, 8)
    assert out.n_meals == 0 and out.n_confirmed > 0
    assert out.per_result.get(int(ResultCode.MONEY_SHORT)) == out.n_confirmed


def test_closed():
    """開店前(既定 10:00-22:00)は ``CLOSED``。"""
    w, a, eatery, cell, tick = _scene(tick=300)
    _, out = _eat(w, a, tick, 8)
    assert out.n_meals == 0 and out.n_confirmed > 0
    assert out.per_result.get(int(ResultCode.CLOSED)) == out.n_confirmed


def test_the_eat_resource_is_the_shop_like_a_purchase():
    """食事は購入と**同じ資源**(店の 1 tick 受け入れ数)を奪い合う=満員は落選になる。"""
    w, a, eatery, cell, tick = _scene()
    _, out = _eat(w, a, tick, 8)
    assert out.n_losers > 0, "容量を超えた分は Phase B で落選する"
    assert out.per_result.get(int(ResultCode.LOST_ARBITRATION)) == out.n_losers


# ------------------------------------------------------------------ (i) 既定のバイト不変
def test_the_v1_apply_table_is_untouched():
    assert len(R._APPLY) == 13 and EAT_ACTION_CODE not in R._APPLY
    assert len(R._APPLY_V2) == 14 and R._APPLY_V2[EAT_ACTION_CODE] is R._apply_eat
    assert R._APPLY_BY_VOCAB["v1"] is R._APPLY
    assert R._ACTION_ORDER_BY_VOCAB["v2"][-1] == EAT_ACTION_CODE
    assert R._ACTION_ORDER_BY_VOCAB["v1"] == R._ACTION_ORDER_BY_VOCAB["v2"][:-1]


def test_the_default_run_is_byte_identical():
    """既定(v1)の checkpoint・呼数・行動分布は、語彙 v2 を足しても 1 ビットも動かない。"""
    base = run_day(**SMALL)
    explicit = run_day(vocab_version="v1", **SMALL)
    assert base.vocab_version == "v1"
    assert base.final_hash == explicit.final_hash != ""
    assert base.llm_calls == explicit.llm_calls > 0
    assert base.action_usage == explicit.action_usage
    assert base.meals == explicit.meals == 0
    assert ACTION_WORD_EAT not in base.action_usage


def test_v2_is_a_different_run_but_still_conserves():
    """v2 は**別の値**(mock の抽選語彙も 13 語になる)。保存則と在庫は破れない。"""
    v1 = run_day(**SMALL)
    v2 = run_day(vocab_version="v2", **SMALL)
    assert v2.final_hash != v1.final_hash
    assert v2.conserved and v2.min_stock >= 0
    assert ACTION_WORD_EAT in v2.action_usage


def test_unknown_vocab_version_is_refused():
    with pytest.raises(ValueError):
        run_day(vocab_version="v3", **SMALL)


# ------------------------------------------------------------------ ラン全体(段0 → 食事)
def test_stage0_dictionary_v3_grounds_eating_into_the_new_word():
    """「食べる」は v1 では 購入、v2 では **食事** に着地する(段0 辞書 v3)。"""
    v1 = run_day(llm=WordLLM("食べる"), **OPEN_HOURS)
    v2 = run_day(llm=WordLLM("食べる"), vocab_version="v2", **OPEN_HOURS)
    assert v1.action_usage.get("購入", 0) > 0 and ACTION_WORD_EAT not in v1.action_usage
    assert v2.action_usage.get(ACTION_WORD_EAT, 0) > 0 and "購入" not in v2.action_usage
    assert v1.undefined_action_count == v2.undefined_action_count == 0


def test_a_full_run_records_meals_and_closes_the_books():
    res = run_day(llm=WordLLM("食べる"), vocab_version="v2", **OPEN_HOURS)
    assert res.meals > 0 and res.meal_yen > 0
    assert res.conserved, "Σ所持金 + Σ売上 + Σ運賃 が不変"
    assert res.money_start - res.money_end == res.revenue_end + res.fares_paid
    assert res.revenue_end >= res.meal_yen


# ------------------------------------------------------------------ (vi) 語ごとの使用率
def test_action_usage_reaches_the_run_manifest():
    res = run_day(llm=WordLLM("食べる"), vocab_version="v2", **OPEN_HOURS)
    fields = res.run_manifest_fields()
    assert fields["vocab_version"] == "v2"
    # C9b(G5 対象ヒント)で段0 辞書は v4 へ(v3 + ``SYNONYMS_V4_DIFF``)
    assert fields["synonym_table_version"] == "undefined-synonyms-v4"
    assert fields["action_usage"] == res.action_usage
    assert fields["action_usage"][ACTION_WORD_EAT] > 0
    # 合計は「適用された行動の延べ数」=どの語も落ちていない
    assert sum(res.action_usage.values()) > 0


def test_action_usage_of_the_default_run_carries_the_v1_version():
    from shibuya.llm.contract import ACTION_VOCAB_12

    res = run_day(**SMALL)
    fields = res.run_manifest_fields()
    assert fields["vocab_version"] == "v1"
    assert fields["synonym_table_version"] == "undefined-synonyms-v2"
    # 既定のランに出る鍵は「12 語 + エンジン継続」だけ(役割語は待機へ落ちる・食事は無い)
    assert set(fields["action_usage"]) <= {"(エンジン継続)", *ACTION_VOCAB_12}
    assert fields["action_usage"]
