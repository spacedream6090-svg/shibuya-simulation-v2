"""第 2 期 2-1 経済の段階 2: 実行時の守り(検収 L1)の負の対照。

組み立ての物と表はランの中で書き換えられない: ATM の表の配列(読み取り専用)・段階 2 の組の表(``MappingProxyType``)・
``Stage2Plan``(組み立ての後は ``runner`` を 1 回置く外は書けない)・``MoneyStage2``・``CreditBook``(行の数 ``n`` の外)・
``Ledger._stage2_pairs``(腕を挿したかから導く=書けない)。
"""

from __future__ import annotations

import datetime as dt
import types

import numpy as np
import pytest

from shibuya.economy import credit as CR
from shibuya.economy.accounts import STAGE2_PAIRS, AccountCode, Sector, is_allowed
from shibuya.economy.ledger import Ledger
from shibuya.engine import economy_stage2 as ES2


def _table() -> ES2.AtmTable:
    full = ES2.parse_opening_hours("24/7")
    return ES2.AtmTable(cell=np.array([3, 5]), kind=np.array([0, 2], dtype=np.int8), hours=np.stack([full, full]),
                        hours_from=np.array([0, 4], dtype=np.int8), n_cells=8, sources={"x.json": "0"})


def test_atm_table_arrays_and_sources_cannot_be_written():
    t = _table()
    for name in ("cell", "kind", "hours", "hours_from"):
        with pytest.raises(ValueError):
            getattr(t, name)[0] = 1
    with pytest.raises(TypeError):
        t.sources["y"] = "1"  # type: ignore[index]
    with pytest.raises(AttributeError):  # 凍結の dataclass
        t.n_cells = 9  # type: ignore[misc]
    src = np.array([1, 2])
    t2 = ES2.AtmTable(cell=src, kind=np.array([0, 0], dtype=np.int8), hours=np.stack([_table().hours[0]] * 2),
                      hours_from=np.zeros(2, np.int8), n_cells=4)
    src[0] = 3  # 渡した配列は写しになる=表は変わらない
    assert list(t2.cell) == [1, 2]


def test_stage2_pairs_table_cannot_be_written():
    with pytest.raises(TypeError):
        STAGE2_PAIRS[AccountCode.RENT] = ((Sector.ROW, Sector.EMPLOYER),)  # type: ignore[index]
    assert is_allowed(AccountCode.RENT, Sector.ROW, Sector.EMPLOYER, stage2=True) is False


def test_stage2_plan_is_sealed_except_runner_once():
    from shibuya.engine.calendar import SimCalendar

    p = ES2.Stage2Plan(parts=ES2.PARTS, kinds=np.zeros(4), monthly_hours=np.ones(4), hours_source="default", atms=None,
                       calendar=SimCalendar(dt.datetime(2026, 8, 24)), tick_seconds=60, n_agents=4,
                       population_scale=None, causes={"payroll": "c"})
    for name, value in (("parts", ("wages",)), ("kinds", np.ones(4)), ("atms", _table()), ("hourly", 1_500)):
        with pytest.raises(AttributeError):
            setattr(p, name, value)
    with pytest.raises(ValueError):
        p.kinds[0] = 7
    with pytest.raises(ValueError):
        p.monthly_hours[0] = 500.0
    with pytest.raises(TypeError):
        p.causes["atm"] = "x"  # type: ignore[index]
    with pytest.raises(AttributeError):
        del p.parts
    p.runner = types.SimpleNamespace(rights=None)  # 組み立てが実行器を作った後に 1 回だけ
    with pytest.raises(AttributeError):
        p.runner = types.SimpleNamespace(rights=None)


def test_money_stage2_credit_and_ledger_flag_are_sealed():
    led = Ledger(4, 2, 2)
    with pytest.raises(AttributeError):
        led._stage2_pairs = True  # type: ignore[misc]
    assert led._stage2_pairs is False
    led.attach_stage2(types.SimpleNamespace(parts=("wages", "payment"), kinds=np.array([0, 1, 3, 7])))
    assert led._stage2_pairs is True
    m = led.stage2
    for name, value in (("parts", frozenset({"tax"})), ("handles_purchase", False), ("atms", None), ("n", 9)):
        with pytest.raises(AttributeError):
            setattr(m, name, value)
    for a in (m.kinds, m.daily, m.visitor, m.monthly_hours):
        with pytest.raises(ValueError):
            a[0] = a[0]
    with pytest.raises(AttributeError):
        del m.plan
    book = led.credit
    with pytest.raises(AttributeError):
        book.cols = {}
    with pytest.raises(AttributeError):
        book.capacity = 5
    i = CR.CreditBook(capacity=1).add(kind=CR.CARD, borrower_sector=0, borrower=0, limit=10, balance=5, due_day=0,
                                      installment=1)
    assert i == 0  # add だけが行の数を進める
