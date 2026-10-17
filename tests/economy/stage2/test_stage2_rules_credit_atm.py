"""第 2 期 2-1 経済の段階 2: 規則の表の読み手(最低賃金・消費税)・信用の器・ATM の表と営業時間・腕と部品・暦の給料日。"""

from __future__ import annotations

import datetime as dt
import types
from fractions import Fraction

import numpy as np
import pytest

from shibuya.economy import anchors as AN
from shibuya.economy import credit as CR
from shibuya.economy import ops as OPS
from shibuya.economy import stage2 as S2
from shibuya.economy.accounts import AccountCode, BalanceLine, Sector
from shibuya.economy.ledger import Ledger
from shibuya.engine import economy_stage2 as ES2

H, S, E, B, G, W = (int(s) for s in Sector)


# ================================================================= 規則の表の読み手
def test_minimum_wage_switches_at_the_version_date():
    """規則の表の最初の読み手: 版のある日は表の値(1,163 円=2024-10-01〜・1,226 円=2025-10-03〜・1,280 円=2026-10-01〜)・
    版の無い日(2024-10-01 より前)は直書き 1,226 円(つなぎ)。〔第337〕前の 2 版を表に足した。"""
    assert AN.min_wage_hourly("2026-09-30") == (1_226, "rules:minimum_wage.tokyo@2025-10-03")
    assert AN.min_wage_hourly("2025-10-02") == (1_163, "rules:minimum_wage.tokyo@2024-10-01")
    assert AN.min_wage_hourly("2024-09-30") == (1_226, "anchors.MIN_WAGE_HOURLY")
    assert AN.min_wage_hourly(dt.date(2026, 10, 1)) == (1_280, "rules:minimum_wage.tokyo@2026-10-01")
    assert AN.min_wage_hourly("2027-03-31")[0] == 1_280
    assert AN.MIN_WAGE_HOURLY == 1_226  # 直書きは残す(つなぎの台帳 BR-MIN-WAGE-HOURLY-1226・外す段 4-2)


def test_consumption_tax_rate_is_ten_percent_from_the_rules_table():
    rate, src = AN.consumption_tax_rate("2026-08-25")
    assert rate == Fraction(1, 10) and src == "rules:consumption_tax.standard_rate@2019-10-01"
    assert AN.consumption_tax_rate("2019-09-30") == (Fraction(0), "none")  # 版の前は税なし(表の外)
    assert list(S2.tax_of(np.array([1_100, 330, 10, 0]), rate)) == [100, 30, 0, 0]


def test_monthly_wage_amounts_default_is_unchanged_and_takes_an_hourly_rate():
    assert list(AN.monthly_wage_amounts(np.array([160, 80]))) == [160 * 1_226, 80 * 1_226]
    assert list(AN.monthly_wage_amounts(np.array([10.0, 20.0]), hourly=1_280)) == [12_800, 25_600]
    assert list(AN.monthly_wage_amounts(np.array([10.0, 10.0]), hourly=np.array([1_000, 2_000]))) == [10_000, 20_000]


def test_payroll_deductions_is_an_empty_container():
    ded, table = S2.payroll_deductions(np.array([200_000, 0]), "2026-08-25")
    assert list(ded) == [0, 0] and table is None


# ================================================================= 信用の器(呼び手なし)
def test_credit_book_rows_and_auto_repayment_with_delinquency():
    book = CR.CreditBook(capacity=0)
    assert len(book) == 0 and book.record() == {"rows": 0, "balance": 0, "delinquent_count": 0, "delinquent_amount": 0}
    a = book.add(kind=CR.CARD, borrower_sector=H, borrower=0, limit=100_000, balance=30_000, due_day=1,
                 installment=10_000)
    b = book.add(kind=CR.CONSUMER, borrower_sector=H, borrower=1, limit=50_000, balance=50_000, due_day=1,
                 installment=20_000)
    c = book.add(kind=CR.MORTGAGE, borrower_sector=H, borrower=2, limit=1, balance=1, due_day=9, installment=1)
    assert (a, b, c) == (0, 1, 2) and CR.KIND_WORDS == ("カード", "住宅ローン", "消費者ローン", "店の借入")
    with pytest.raises(ValueError):
        book.add(kind=9, borrower_sector=H, borrower=0, limit=1, balance=1, due_day=0, installment=1)
    led = Ledger(3, 1)
    led.transfer_many(W, np.zeros(1, np.int64), H, np.array([0]), np.array([15_000]), int(AccountCode.CARRY_IN), 0,
                      method=OPS.METHOD_ACCOUNT)
    got = CR.repay_due(book, led, day=1, step=0)
    assert got == {"due": 2, "paid": 1, "paid_amount": 10_000, "delinquent": 1, "delinquent_amount": 20_000}
    assert list(book.view("balance")) == [20_000, 50_000, 1]
    assert list(book.view("delinquent_count")) == [0, 1, 0]
    assert int(np.asarray(led.balance(BalanceLine.DEPOSIT, H))[0]) == 5_000
    # 返済の流れ(世帯 → 銀行の利子)は登録の外=呼び手を作る段で登録する(今呼ぶと検算が落ちる=宣言どおり)
    led.on_day_end(0)
    assert led.meter.last_day["conservation"]["ok"] is False


# ================================================================= 腕と部品
def test_arm_and_parts_switches(monkeypatch):
    monkeypatch.setattr(ES2, "_ARM", ES2.ARM_OFF)
    monkeypatch.setattr(ES2, "_PARTS", ES2.PARTS)
    assert ES2.arm() == "off" and ES2.active_parts() == frozenset()
    ES2.set_arm("on")
    assert ES2.active_parts() == frozenset(ES2.PARTS)
    ES2.set_parts("tax,wages")
    assert ES2.parts() == ("wages", "tax")
    assert ES2.parse_parts("") == ES2.PARTS and ES2.parse_parts("all") == ES2.PARTS and ES2.parse_parts("none") == ()
    with pytest.raises(ValueError):
        ES2.set_arm("maybe")
    with pytest.raises(ValueError):
        ES2.set_parts("wages,bonus")
    assert ES2.PARTS == S2.PARTS
    assert ES2.CAUSE_NAMES == ("payroll", "atm", "register")
    assert ES2.PAYDAY_DAY_OF_MONTH == S2.PAYDAY_DAY_OF_MONTH == 25


def test_origin_constants_are_copies_of_the_build_geometry():
    from shibuya.build.geo import common as G

    assert ES2.ORIGIN_LATLON == G.ORIGIN_LATLON and ES2.M_PER_DEG_LAT == G.M_PER_DEG_LAT
    assert ES2.M_PER_DEG_LON == G.M_PER_DEG_LON and ES2.CELL_M == G.CELL_M
    x, y = G.latlon_to_local(35.6595 + 0.001, 139.70062 + 0.002)
    assert abs(x - 0.002 * ES2.M_PER_DEG_LON) < 1e-6 and abs(y - 0.001 * ES2.M_PER_DEG_LAT) < 1e-6


# ================================================================= 営業時間
def test_opening_hours_parser():
    full = ES2.parse_opening_hours("24/7")
    assert full.shape == (7, 2, 2) and (full[:, 0] == [0, 1440]).all() and (full[:, 1] == -1).all()
    wk = ES2.parse_opening_hours("Mo-Fr 09:00-15:00")
    assert (wk[:5, 0] == [540, 900]).all() and (wk[5:, :, 0] == -1).all()
    night = ES2.parse_opening_hours("Sa 22:00-02:00")
    assert list(night[5, 0]) == [1320, 1440] and list(night[6, 0]) == [0, 120]
    over = ES2.parse_opening_hours("Mo-Su 08:00-20:00; Su off")
    assert list(over[0, 0]) == [480, 1200] and (over[6, :, 0] == -1).all()
    assert ES2.parse_opening_hours("sunrise-sunset") is None and ES2.parse_opening_hours(None) is None


def test_atm_table_open_cells_follow_the_weekday_and_minute():
    hours = np.stack([ES2.parse_opening_hours("24/7"), ES2.parse_opening_hours("Mo-Fr 09:00-15:00")])
    t = ES2.AtmTable(cell=np.array([3, 5]), kind=np.array([1, 2], np.int8), hours=hours,
                     hours_from=np.array([0, 0], np.int8), n_cells=8)
    assert list(np.flatnonzero(t.open_cells(0, 10 * 60))) == [3, 5]   # 月曜 10:00
    assert list(np.flatnonzero(t.open_cells(0, 15 * 60))) == [3]      # 月曜 15:00(終わりは含まない)
    assert list(np.flatnonzero(t.open_cells(6, 10 * 60))) == [3]      # 日曜
    rec = t.record()
    assert rec["n"] == 2 and rec["kind"] == {"atm": 0, "shop": 1, "bank": 1}


@pytest.mark.requires_data("world_v2", "osm:poi_tags_overpass_20260928.json", "osm:poi_opening_hours_overpass_20260907.json")
def test_atm_table_from_osm_has_the_55_points():
    from shibuya.world.state import World

    world = World.load("data/world/v2")
    t = ES2.build_atm_table(world)
    assert t.n + t.dropped == 55  # 〔検収 L3〕ATM 7・店の中 25・銀行の支店 23(atm の印に関わらず全部)
    assert t.n >= 40 and (t.cell >= 0).all() and (t.cell < world.n_cells).all()
    rec = t.record()
    assert rec["kind"] == {"atm": 7, "shop": 25, "bank": 23} and sum(rec["kind"].values()) == t.n
    assert rec["hours_from"]["bank_default"] == 20  # 営業時間の無い支店は平日 9:00-15:00・土日は閉(宣言)
    assert (t.hours_from[t.kind == 2] != 2).all()  # 銀行の支店は 24 時間にしない
    assert set(rec["sources"]) == {"poi_tags_overpass_20260928.json", "poi_opening_hours_overpass_20260907.json"}
    # 銀行の Mo-Fr 09:00-15:00 は日曜に閉まる=日曜の営業中の ATM は平日の昼より少ない
    assert int(t.open_at(6, 600).sum()) < int(t.open_at(0, 600).sum())


# ================================================================= 暦の給料日(暦の口)と雇用の行
def test_payday_follows_the_calendar_port():
    from shibuya.engine.calendar import SimCalendar

    cal = SimCalendar(dt.datetime(2026, 8, 24))
    plan = ES2.Stage2Plan(parts=ES2.PARTS, kinds=np.zeros(1), monthly_hours=None, hours_source="default", atms=None,
                          calendar=cal, tick_seconds=60, n_agents=1, population_scale=None, causes={})
    assert [plan.is_payday(d) for d in range(3)] == [False, True, False]  # 8/25(火)
    cal2 = SimCalendar(dt.datetime(2026, 7, 20))  # 7/25 は土曜 → 前の営業日 7/24(金)
    plan2 = ES2.Stage2Plan(parts=ES2.PARTS, kinds=np.zeros(1), monthly_hours=None, hours_source="default", atms=None,
                           calendar=cal2, tick_seconds=60, n_agents=1, population_scale=None, causes={})
    assert [d for d in range(10) if plan2.is_payday(d)] == [4]
    assert plan.close_step(1) == 2 * 1440 - 1 and plan.weekday_minute(1440 + 600) == (1, 600)
    assert cal.payday_day_of_month is None  # ランの暦は変えない(給料日の規則は段階 2 の写しの暦だけ)


def test_rights_pairs_reads_employment_rows_in_row_order():
    from shibuya.engine.rights.ledger import AGENT, EMPLOY, ORG, STORE, Right, Rights

    r = Rights(capacity=4)
    r.grant(Right(holder=(AGENT, 5), object=(ORG, 9), kind=EMPLOY, source="t"))
    r.grant(Right(holder=(AGENT, 2), object=(STORE, 1), kind=EMPLOY, source="t"))
    r.grant(Right(holder=(AGENT, 5), object=(STORE, 0), kind=EMPLOY, source="t"))
    h, o = r.pairs(EMPLOY, AGENT, ORG, 0)
    assert list(h) == [5] and list(o) == [9]
    h, o = r.pairs(EMPLOY, AGENT, STORE, 0)
    assert list(h) == [2, 5] and list(o) == [1, 0]
    from shibuya.engine.calendar import SimCalendar  # Stage2Plan.employment は組織の行を先に・体ごとに最初の 1 行

    p = ES2.Stage2Plan(parts=ES2.PARTS, kinds=np.zeros(8), monthly_hours=None, hours_source="default", atms=None,
                       calendar=SimCalendar(dt.datetime(2026, 8, 24)), tick_seconds=60, n_agents=8,
                       population_scale=None, causes={})
    p.runner = types.SimpleNamespace(rights=r)
    who, sec, idx = p.employment(0)
    assert list(who) == [5, 2] and list(sec) == [E, S] and list(idx) == [9, 1]
