"""第 2 期 2-1 経済の段階 2: 呼の id の配線(検収 A1)。

- 基本操作 ``ops.transfer`` は行ごとの原因(``list``)を受ける: None の行は出来事を書かない(生ログの目印は -1・計器
  ``uncaused`` に数える)。長さの違い・型の違いは落ちる。
- ``IntentBatch`` の任意の 2 列(``call_id``・``s2_flags``)は連結・抜き出し・1 体 1 件の畳みで運ばれ、持たない部分は空の値で
  埋まる(どこも持たなければ ``None``=今のまま)。
- 台帳: 金に触れる行為の呼の id を控えると、購入・食事の行の原因が ``LlmCall(call_id)`` になる・支払いの方法の答え
  (カード=口座)に先に従う・引き出しは口が選んだ行(``wanted``)が規則を通らず原因は呼。
- 判断の口の層: 口の答え(お金を下ろす・支払いの方法)を印にして控え、判断の系が 1 回だけ取り出す。
- 合成の世界の 1 日(腕 on・腕 port・mock の口の答えを試験の中だけ差し替え): 口の答えが行為の解決へ運ばれる(引き出し・
  口座の支払い)・購入と食事の行の原因が呼になる・保存則の残差 0。
"""

from __future__ import annotations

import datetime as dt
import types

import numpy as np
import pytest

from shibuya.economy import ops as OPS
from shibuya.economy import stage2 as S2
from shibuya.economy.accounts import AccountCode, BalanceLine, Sector
from shibuya.economy.ledger import Ledger
from shibuya.engine import commit as C
from shibuya.engine import economy_stage2 as ES2
from shibuya.engine.events import log as EV
from shibuya.engine.events.links import MoneyEventLink
from shibuya.engine.ledger_api import TransferStatus

H, S, E, B, G, W = (int(s) for s in Sector)
KINDS = np.array([0, 1, 3, 7])


def _plan(parts=S2.PARTS):
    cal_day = dt.date(2026, 8, 24)
    return types.SimpleNamespace(
        parts=tuple(parts), kinds=KINDS, monthly_hours=None, hours_source="default", atms=None,
        cause=lambda name: EV.Process(name), llm_cause=lambda cid: EV.LlmCall(str(cid)),
        date_of_step=lambda step: cal_day, date_of=lambda day: cal_day, is_payday=lambda day: False,
        close_step=lambda day: 1439, employment=lambda day: (np.zeros(0),) * 3, record=lambda: {},
    )


def _led(parts=S2.PARTS, wallets=(20_000, 20_000, 20_000, 20_000)) -> tuple[Ledger, EV.EventLog]:
    led = Ledger(len(wallets), 2, 2)
    led.attach_stage2(_plan(parts))
    led.endow_households(np.asarray(wallets), 0)
    led.endow_stores(np.full(2, 10_000), 0)
    log = EV.EventLog()
    led.attach_events(MoneyEventLink(log), step_seconds=60)
    return led, log


def _llm_rows(log: EV.EventLog, what: str) -> list[str]:
    out = []
    for i in range(len(log)):
        ev = log.event(i)
        if ev.what == what and isinstance(ev.cause, EV.LlmCall):
            out.append(ev.cause.call_id)
    return out


# ================================================================= 基本操作の行ごとの原因
def test_transfer_takes_row_causes_and_counts_the_uncaused_rows():
    led, log = _led(parts=("wages",))
    m0 = led.meter.uncaused
    first = led.raw_position()
    st = led.transfer_many(H, np.array([0, 1, 2]), S, np.array([0, 1, 0]), np.array([100, 200, 300]),
                           int(AccountCode.CONSUMPTION), 3, cause=[EV.LlmCall("3:0:2"), None, EV.Process("atm")])
    assert list(st) == [0, 0, 0]
    assert led.meter.uncaused - m0 == 1  # None の行だけ
    t, s = led.raw_event_ids()
    tail = s[first:]
    assert list(tail >= 0) == [True, False, True]  # None の行の目印は空
    assert _llm_rows(log, "金:消費支出") == ["3:0:2"]
    with pytest.raises(ValueError, match="行数"):
        led.transfer_many(H, np.array([0, 1]), S, np.array([0, 0]), np.array([1, 1]), int(AccountCode.CONSUMPTION), 3,
                          cause=[None])
    with pytest.raises(TypeError):
        OPS.transfer(led, (H, np.array([0])), (S, np.array([0])), np.array([1]), OPS.what_of(AccountCode.CONSUMPTION),
                     ["x"], 0)
    # 全部 None の並び=原因なし(1 つの None と同じ)
    m1 = led.meter.uncaused
    led.transfer_many(H, np.array([0, 1]), S, np.array([0, 0]), np.array([1, 1]), int(AccountCode.CONSUMPTION), 4,
                      cause=[None, None])
    assert led.meter.uncaused - m1 == 2


def test_rejected_rows_drop_their_causes():
    led, log = _led(parts=("wages",), wallets=(20_000, 10, 20_000, 20_000))
    st = led.transfer_many(H, np.array([0, 1, 2]), S, np.array([0, 0, 0]), np.array([100, 5_000, 100]),
                           int(AccountCode.CONSUMPTION), 3,
                           cause=[EV.LlmCall("3:0:2"), EV.LlmCall("3:1:2"), EV.LlmCall("3:2:2")])
    assert list(st) == [0, int(TransferStatus.INSUFFICIENT_FUNDS), 0]
    assert _llm_rows(log, "金:消費支出") == ["3:0:2", "3:2:2"]  # 却下の行の原因は書かない


# ================================================================= IntentBatch の任意の 2 列
def _batch(ids, with_calls: bool) -> C.IntentBatch:
    n = len(ids)
    b = C.IntentBatch(np.asarray(ids, dtype=np.int64), np.zeros(n, np.int8), np.full(n, -1, np.int32),
                      np.full(n, -1, np.int32), np.zeros(n, np.int64))
    if with_calls:
        import dataclasses

        b = dataclasses.replace(b, call_id=np.array([f"1:{i}:2" for i in ids], dtype=object),
                                s2_flags=np.full(n, C.S2_MONEY_ACT, dtype=np.int8))
    return b


def test_intent_batch_carries_the_calls_and_fills_the_rest():
    plain = C.IntentBatch.concat([_batch([5, 6], False), _batch([7], False)])
    assert plain.call_id is None and plain.s2_flags is None  # どこも持たない=今のまま
    mixed = C.IntentBatch.concat([_batch([5, 6], True), _batch([7], False)])
    assert list(mixed.call_id) == ["1:5:2", "1:6:2", None]
    assert list(mixed.s2_flags) == [C.S2_MONEY_ACT, C.S2_MONEY_ACT, 0]
    t = mixed.take([2, 0])
    assert list(t.call_id) == [None, "1:5:2"] and list(t.s2_flags) == [0, C.S2_MONEY_ACT]
    one = C.IntentBatch.concat([_batch([5], True), _batch([5, 6], False)]).one_per_agent()
    assert len(one) == 2 and one.call_id is not None
    with pytest.raises(ValueError):
        import dataclasses

        dataclasses.replace(_batch([1, 2], False), call_id=np.array(["x"], dtype=object))


# ================================================================= 台帳: 購入・食事・引き出しの原因と支払いの答え
def test_noted_calls_cause_purchases_and_steer_the_payment():
    led, log = _led()
    dep0, cash0 = (np.asarray(led.balance(x, H), dtype=np.int64).copy() for x in (BalanceLine.DEPOSIT, BalanceLine.CASH))
    led.note_calls_many(np.array([0, 2]), np.array(["5:0:2", "5:2:1"], dtype=object), np.array([-1, 1]))
    st = led.purchase_many(np.array([0, 1, 2]), np.array([0, 1, 1]), np.array([1_100, 1_100, 1_100]), 6)
    assert list(st) == [0, 0, 0]
    # 体 2 は財布で足りるが答え「カード」=口座・体 0 は答えなし=財布で足りる=現金・体 1 は控えなし=原因なし
    cash = np.asarray(led.balance(BalanceLine.CASH, H), dtype=np.int64)
    dep = np.asarray(led.balance(BalanceLine.DEPOSIT, H), dtype=np.int64)
    assert list(cash0 - cash)[:3] == [1_100, 1_100, 0] and list(dep0 - dep)[:3] == [0, 0, 1_100]
    assert sorted(_llm_rows(log, "金:消費支出")) == ["5:0:2", "5:2:1"]
    assert _llm_rows(log, "金:カード") == ["5:2:1"]  # 口座の決済の行も同じ呼
    calls = led.stage2.s2_meter["run"]["calls"]
    assert calls["noted"] == 2 and calls["pay_answers"] == 1 and calls["pay_answer_rows"] == 1
    assert calls["purchase_caused"] == 2 and calls["purchase_uncaused"] == 1
    led.on_day_end(0)
    assert led.meter.last_day["conservation"]["ok"] is True


def test_an_account_answer_without_a_deposit_falls_back_to_cash():
    led, _log = _led(parts=("payment",))  # 預金の無い来街者 1(visitors を止めた)
    led.note_calls_many(np.array([1]), np.array(["5:1:2"], dtype=object), np.array([1]))
    cash0 = int(np.asarray(led.balance(BalanceLine.CASH, H))[1])
    assert list(led.purchase_many(np.array([1]), np.array([0]), np.array([500]), 6)) == [0]
    assert cash0 - int(np.asarray(led.balance(BalanceLine.CASH, H))[1]) == 500


def test_a_chosen_withdrawal_skips_the_rule_and_takes_the_call_as_cause():
    led, log = _led(wallets=(200_000, 200_000, 200_000, 200_000))  # 財布は 1 日の消費より大きい=規則では下ろさない
    got = led.withdraw_many(np.array([0, 2]), 7, cause=EV.Process("atm"), wanted=np.array([True, False]),
                            call_ids=np.array(["7:0:2", "7:2:2"], dtype=object))
    assert int(got[0]) > 0 and int(got[1]) == 0
    assert _llm_rows(log, "金:引き出し") == ["7:0:2"]
    calls = led.stage2.s2_meter["run"]["calls"]
    assert calls["withdraw_chosen"] == 1 and calls["withdraw_caused"] == 1
    led2, log2 = _led(wallets=(10, 10, 10, 10))  # 規則で下ろす行・呼の無い行は Process("atm")
    got2 = led2.withdraw_many(np.array([0, 2]), 7, cause=EV.Process("atm"), call_ids=np.array([None, "7:2:2"],
                                                                                             dtype=object))
    assert (got2 > 0).all()
    assert _llm_rows(log2, "金:引き出し") == ["7:2:2"] and log2.cause_counts().get("process", 0) >= 1


# ================================================================= 判断の口の層の印
def test_decision_layer_hints_are_taken_once():
    from shibuya.engine.decision import layer as DL
    from shibuya.engine.decision.port import Choice

    lay = DL.DecisionLayer.__new__(DL.DecisionLayer)
    lay.meter = DL._empty_meter()
    lay._s2_hints = {}
    lay._note_stage2(5, Choice(candidate_id=f"affordance:{ES2.WITHDRAW_WORD}", number=2, kind=ES2.WITHDRAW_WORD))
    lay._note_stage2(6, Choice(candidate_id="vocab:購入", number=1, kind="購入", payment="カード"))
    lay._note_stage2(7, Choice(candidate_id="vocab:食事", number=1, kind="食事", payment="現金"))
    lay._note_stage2(8, Choice(candidate_id="vocab:移動", number=1, kind="移動", payment="カード"))  # 購入・食事でない
    assert lay.take_stage2_hint(5) == (C.S2_WITHDRAW,) and lay.take_stage2_hint(5) == ()
    assert lay.take_stage2_hint(6) == (C.S2_PAY_ACCOUNT,) and lay.take_stage2_hint(7) == (C.S2_PAY_CASH,)
    assert lay.take_stage2_hint(8) == ()
    st = lay.meter["stage2"]
    assert st["withdraw_chosen"] == 1 and st["payment_answered"] == 2


# ================================================================= 合成の世界の 1 日
def test_port_answers_reach_the_actions_in_a_run(monkeypatch):
    from tests.economy.stage2 import test_stage2_runs as TR
    from shibuya.engine.decision import layer as DL
    from shibuya.engine.decision import ports as PT
    from shibuya.world.state import World

    monkeypatch.setattr(ES2, "_ARM", ES2.ARM_OFF)
    monkeypatch.setattr(ES2, "_PARTS", ES2.PARTS)
    monkeypatch.setattr(ES2, "_ATM_OVERRIDE", None)
    ES2.set_arm("on")
    ES2.set_parts(ES2.PARTS)
    ES2.set_atm_table(TR._atm_everywhere(World.synthetic(n_cells=64, seed=2).n_cells))
    base, base_led = TR._run(sim_days=1)  # 腕 legacy: 呼の id だけが運ばれる(口の答えは無い)
    bc = base_led.stage2.s2_meter["run"]["calls"]
    assert bc["purchase_caused"] > 0 and bc["withdraw_chosen"] == 0 and bc["pay_answers"] == 0
    assert bc["purchase_uncaused"] <= bc["purchase_caused"] // 10  # ほとんどの購入・食事が呼を原因に持つ

    orig = PT.MockPort._answer

    def answer(self, ctx, presented):  # noqa: ANN001 — 試験の中だけ: 下ろせる所では下ろす・購入と食事はカード
        cid, extra = orig(self, ctx, presented)
        w = next((c for c in presented if c.kind == ES2.WITHDRAW_WORD), None)
        if w is not None:
            return w.id, extra
        kind = next((c.kind for c in presented if c.id == cid), None)
        if kind in ("購入", "食事"):
            return cid, {**extra, "payment": "カード"}
        return cid, extra

    monkeypatch.setattr(PT.MockPort, "_answer", answer)
    monkeypatch.setattr(DL, "_ARM", DL.ARM_PORT)
    res, led = TR._run(sim_days=1)
    calls = led.stage2.s2_meter["run"]["calls"]
    dp = res.run_manifest_fields()["decision_port"]["stage2"]
    assert dp["withdraw_chosen"] > 0 and dp["payment_answered"] > 0
    assert calls["withdraw_chosen"] > 0 and calls["withdraw_caused"] >= calls["withdraw_chosen"]
    assert calls["pay_answers"] > 0 and calls["pay_answer_rows"] > 0 and calls["purchase_caused"] > 0
    assert led.stage2.s2_meter["run"]["withdraw"]["count"] >= calls["withdraw_chosen"] > 0
    m = res.run_manifest_fields()
    assert all(d["economy"]["conservation"]["ok"] for d in m["daily"])
