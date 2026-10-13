"""第 1 期 1-9: 金の生ログの行と出来事が 1 対 1(目印の列 ``_raw_event_t_ns``・``_raw_event_seq``)。物の台帳の行の目印。

口の約束 1-3 の約束 (2)(既存の記録は消さず ``Event.id`` への目印で結ぶ)を金と物の生ログで(1-3 の仮採用 10 の続き)。
基本操作 ``ops.transfer`` は原因(``cause``)を渡された行ごとに ``EventLog.append(Event(what=金:<科目>, how_much=額,
who=払い手, whom=受け手, cause))`` を書き、id を生ログの行に入れる。原因の無い行・記録 off の行は目印が空(-1)。

- 単体: 1 対 1・欄の中身・刻みの幅・原因の無い行・記録 off・溢れた輪・補充の物の行と代金の行が同じ id。
- ラン(data・世界資産 200 体・既定 v3): 運賃(原因=過程 rail)と補充の代金(原因=過程 shelf)の行が出来事と 1 対 1・
  計器の数(出来事の行・原因の無い行)と記録の分布(``金:持ち出し``・``金:域外仕入``)が合う・物の補充の行の目印=代金の行。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.core.time_consts import NS_PER_SECOND
from shibuya.economy import ops as OPS
from shibuya.economy.accounts import AccountCode, Sector
from shibuya.economy.goods import GoodsLedger
from shibuya.economy.ledger import Ledger
from shibuya.engine.events import vocab as V
from shibuya.engine.events.links import MoneyEventLink
from shibuya.engine.events.log import EventLog, LlmCall, Process

H, S, W = int(Sector.HOUSEHOLD), int(Sector.STORE), int(Sector.ROW)
RAIL, SHELF = Process("rail"), Process("shelf")


def _ledger(cap=None, *, enabled=True, step_seconds=60):
    led = Ledger(5, 3, raw_capacity=cap)
    log = EventLog(enabled=enabled)
    led.attach_events(MoneyEventLink(log), step_seconds=step_seconds)
    led.endow_households(np.full(5, 50_000), 0)  # 原因なし
    return led, log


def _links(led, log):
    """生ログの行ごとの (行, 出来事 or None)。"""
    rows = led.raw_rows()
    t, s = led.raw_event_ids()
    out = []
    for i in range(rows.shape[0]):
        out.append((rows[i], None if s[i] < 0 else log.get((int(t[i]), int(s[i])))))
    return out


def test_each_caused_row_has_exactly_one_event():
    led, log = _ledger()
    log.begin_step(7 * 60 * NS_PER_SECOND)
    st = led.transfer_many(H, np.array([0, 1, 2]), W, np.zeros(3, np.int64), np.array([170, 170, 210]),
                           int(AccountCode.CARRY_OUT), 7, cause=RAIL)
    assert (st == 0).all()
    links = _links(led, log)
    caused = [(r, e) for r, e in links if e is not None]
    assert len(links) == 8 and len(caused) == 3  # 財布 5 行(原因なし)+運賃 3 行
    ids = [e.id for _r, e in caused]
    assert len(set(ids)) == 3 and len(log) == 3  # 1 対 1(別々の id・記録の行は 3 つだけ)
    for r, e in caused:
        assert e.what == "金:持ち出し" == OPS.what_of(int(r[6]))
        assert e.how_much == int(r[5]) and e.who == int(r[2]) and e.whom == "外界:0"
        assert e.cause == RAIL and e.t_ns == 7 * 60 * NS_PER_SECOND == int(r[0]) * 60 * NS_PER_SECOND
        assert V.family_of(e.what) == V.FAMILY_MONEY and e.where is None
    assert led.meter.events == 3 and led.meter.uncaused == 5 and led.meter.rows == 8


def test_store_side_has_a_poi_where_and_llm_call_cause():
    led, log = _ledger()
    cause = LlmCall("12:3:1")
    led.purchase_many(np.array([3]), np.array([2]), np.array([800]), 0, cause=cause)
    (_r, e), = [(r, e) for r, e in _links(led, log) if e is not None]
    assert (e.who, e.whom, e.where, e.what, e.cause) == (3, "店舗:2", ("poi", 2), "金:消費支出", cause)


def test_step_width_sets_the_event_time():
    led, log = _ledger(step_seconds=300)
    log.begin_step(4 * 300 * NS_PER_SECOND)
    led.transfer_many(H, np.array([0]), W, np.zeros(1, np.int64), np.array([10]), int(AccountCode.CARRY_OUT), 4,
                      cause=RAIL)
    (r, e), = [(r, e) for r, e in _links(led, log) if e is not None]
    assert int(r[0]) == 4 and e.t_ns == 4 * 300 * NS_PER_SECOND


def test_no_cause_or_log_off_leaves_the_column_empty():
    led, log = _ledger(enabled=False)
    led.transfer_many(H, np.array([0, 1]), W, np.zeros(2, np.int64), np.array([5, 5]), int(AccountCode.CARRY_OUT), 0,
                      cause=RAIL)
    t, s = led.raw_event_ids()
    assert (s == OPS.NO_EVENT).all() and (t == OPS.NO_EVENT).all() and len(log) == 0
    assert led.meter.events == 0 and led.meter.uncaused == 5  # 記録 off は「原因なし」に数えない
    led2 = Ledger(2, 1)  # 記録を挿していない台帳
    led2.endow_households(np.array([10, 20]), 0, cause=RAIL)
    assert (led2.raw_event_ids()[1] == OPS.NO_EVENT).all()


def test_overwritten_slots_do_not_keep_stale_ids():
    """輪の使い回し: 原因つきの行を原因なしの行で上書きすると目印も空に戻る(古い id を残さない)。"""
    led, log = _ledger(cap=6)
    led.transfer_many(H, np.arange(5), W, np.zeros(5, np.int64), np.full(5, 3), int(AccountCode.CARRY_OUT), 0,
                      cause=RAIL)
    assert led.meter.overflow == 4  # 財布 5 行+運賃 5 行 → 6 行の輪
    links = _links(led, log)
    assert [e is not None for _r, e in links] == [False] + [True] * 5
    led.transfer_many(H, np.arange(4), W, np.zeros(4, np.int64), np.full(4, 3), int(AccountCode.CARRY_OUT), 0)
    links = _links(led, log)
    assert [e is not None for _r, e in links] == [True, True, False, False, False, False]
    assert all(e.how_much == int(r[5]) for r, e in links if e is not None)


def test_restock_goods_row_shares_the_payment_event():
    """補充: 物の行の目印=代金の行(店舗 → 外界・域外仕入)の出来事。払えない行は物の行も代金の行も無い。"""
    led, log = _ledger()
    led.endow_stores(np.array([5_000, 0, 5_000]), 0)
    g = GoodsLedger.from_pois(np.array([0, 1, 2]), np.array([4, 4, 4]), np.array([300, 300, 300]))
    ok = g.restock_many(np.array([0, 1, 2]), np.array([2, 2, 2]), 0, money=led, cause=SHELF)
    assert ok.tolist() == [True, False, True]  # 店 1 は現金 0
    gt, gs = g.delivery_event_ids()
    rows = g.delivery_rows()
    assert rows.shape[0] == 2 and (gs >= 0).all()
    for i in range(2):
        e = log.get((int(gt[i]), int(gs[i])))
        assert e.what == "金:域外仕入" and e.who == f"店舗:{int(rows[i, 1])}" and e.cause == SHELF
    # 販売・廃棄の行は空
    g.sell_many(np.array([0]), 1)
    assert int(g.delivery_event_ids()[1][-1]) == OPS.NO_EVENT


@pytest.mark.requires_data("world_v2:w17_schedule.parquet")
def test_run_rows_and_events_are_one_to_one():
    """ラン(世界資産 200 体・既定 v3・1 日): 金の生ログの目印のある行と出来事の記録の金の行が 1 対 1。"""
    from shibuya import cli

    res = cli.run(n_agents=200, seed=1, world_dir="data/world/v2", vocab_version="v3")
    led, g, log = res.ledger.money, res.ledger.goods, res.event_log
    rows = led.raw_rows()
    t, s = led.raw_event_ids()
    have = s >= 0
    assert led.meter.overflow == 0 and rows.shape[0] == led.meter.rows  # 輪は 1 日ぶんを全部持つ
    assert int(have.sum()) == led.meter.events > 0
    assert int((~have).sum()) == led.meter.uncaused
    money_events = [e for e in log.events() if V.family_of(e.what) == V.FAMILY_MONEY]
    assert len(money_events) == led.meter.events  # 記録の金の行=目印のある行(1 対 1)
    ids = set(zip(t[have].tolist(), s[have].tolist()))
    assert len(ids) == int(have.sum()) and ids == {e.id for e in money_events}
    for i in np.flatnonzero(have):
        e = log.get((int(t[i]), int(s[i])))
        assert e.what == OPS.what_of(int(rows[i, 6])) and e.how_much == int(rows[i, 5])
        assert e.cause in (RAIL, SHELF)
        assert (e.cause == RAIL) == (int(rows[i, 6]) == int(AccountCode.CARRY_OUT))
    daily = res.run_manifest_fields()["daily"][0]
    by = daily["events"]["by_what"]
    assert by.get("金:持ち出し", 0) + by.get("金:域外仕入", 0) == led.meter.events
    assert daily["economy"]["event_rows"] == led.meter.events
    # 物の補充の行の目印=代金の行の出来事(同じ id)
    gt, gs = g.delivery_event_ids()
    restock = g.delivery_rows()[:, 4] == 0
    assert restock.any() and (gs[restock] >= 0).all() and (gs[~restock] < 0).all()
    assert set(zip(gt[restock].tolist(), gs[restock].tolist())) <= ids


def test_economy_constants_match_the_events_vocabulary():
    """economy は engine.events を import しない(層の契約)=金の語・原因の種類の名を写しで持つ。写しが 1-3 と同じ。"""
    from shibuya.engine.events import log as EV

    assert OPS.MONEY_FAMILY == V.FAMILY_MONEY
    assert OPS.CAUSE_KINDS == EV.CAUSE_KINDS
    assert set(OPS.MONEY_WHAT) == {f"{V.FAMILY_MONEY}:{w}" for w in V.MONEY_WORDS}
    assert all(w in V.VOCAB_CODES for w in OPS.MONEY_WHAT)
    assert [int(c) for c in OPS.MONEY_WHAT.values()] == list(range(len(V.MONEY_WORDS)))


def test_economy_and_the_ledger_api_do_not_import_engine_events():
    """層の契約 forbidden「economy → llm」: economy と engine.ledger_api(economy が読む)は engine.events を読まない
    (読むと語彙表 → llm.contract の鎖で破れる)。出来事の口 MoneyEventLink は build が作って挿す。"""
    import ast
    from pathlib import Path

    src = Path(__file__).resolve().parents[3] / "src" / "shibuya"
    files = sorted((src / "economy").glob("*.py")) + [src / "engine" / "ledger_api.py"]
    bad = []
    for f in files:
        for n in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            mods = ([n.module or ""] if isinstance(n, ast.ImportFrom)
                    else [a.name for a in n.names] if isinstance(n, ast.Import) else [])
            bad += [f"{f.name}:{m}" for m in mods if m.startswith(("shibuya.engine.events", "shibuya.llm"))]
    assert bad == [], bad
