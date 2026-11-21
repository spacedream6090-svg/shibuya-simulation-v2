"""〔11-01 §5・段 2 の 5〕最低賃金を ``human`` へ・床は machine のつなぎ(``params.bridge``)・違反の記録の器。

正: 回答 11-01 §5(判定は「現実でその場で物理的に止まるか」・最低賃金と法定労働時間は human・検知と反応の口ができるまで
machine をつなぎとして残す)・指示書 11-01 段 2 の 5(違反が起きたら記録する器だけ先に)。記録
``docs/bench/analysis/s2-rules-1101/README.md``。

- 規則の表: ``minimum_wage.tokyo`` の 3 版は ``kind: human``・``params.bridge`` は machine のつなぎ(欄の検査つき)。
- 床: 行が machine か、human/norm でつなぎが machine のときだけ当てる(表の値を直書きしない)。つなぎのある既定では払う額が
  :func:`economy.wages.apply_floor` と 1 バイト同じ。
- 器 ``rules.minimum_wage_shortfall``: 床を当てる直前に床を下回った体と額(正の対照=低い賃金の合成・負の対照=高い賃金)・
  つなぎを外した表では下回ったまま払い ``violation_*`` に立つ。
"""

from __future__ import annotations

import datetime as dt
import types

import numpy as np
import pytest

from shibuya.economy import anchors as AN
from shibuya.economy import stage2 as S2
from shibuya.economy import wages as WG
from shibuya.economy.accounts import BalanceLine
from shibuya.economy.ledger import Ledger
from shibuya.world.facts.rules import table as RT
from tests.economy.test_wage_occupation import E, H, NO_FLOOR_DAY, _inputs, _low_tables, _plan, _tables

FLOOR_DAY = dt.date(2026, 10, 23)
BRIDGE = {"kind": "machine", "conf": "expedient", "remove_at": "7",
          "remove_note": "検知と反応の口(気づいた人・本人・監督)ができる段",
          "declared_in": "11-01 §5", "ledger_id": "DOC-s2rules-min-wage-floor-bridge"}


def _row(kind: str, bridge=None, yen: int = 1_280, asof: str = "2026-10-01") -> RT.Rule:
    params = {"yen_per_hour": yen, "area": "東京都"}
    if bridge is not None:
        params["bridge"] = bridge
    return RT.Rule(id="minimum_wage.tokyo", kind=kind, asof=asof, params=params,
                   source=(RT.Source(law="最低賃金法", article="4 条", version="2025-06-01", url="https://example.invalid/x"),))


# ================================================================= 規則の表
def test_the_repo_rows_are_human_with_a_machine_bridge():
    rules = RT.default_rules()
    vs = rules.versions("minimum_wage.tokyo")
    assert [(r.asof, r.params["yen_per_hour"]) for r in vs] == [("2024-10-01", 1163), ("2025-10-03", 1226),
                                                                 ("2026-10-01", 1280)]
    for r in vs:
        assert r.kind == "human"
        b = AN.rule_bridge(r)
        assert dict(b) == BRIDGE
        assert "11-01 §5" in r.note and "params.bridge" in r.note
    # 〔検収 M1〕つなぎのある行の一覧(書き方は params.bridge の 1 つ)=最低賃金の 3 版と消費税の申告の期限
    assert AN.check_rule_bridges() == ("consumption_tax.filing_deadline@2026-10-01", "minimum_wage.tokyo@2024-10-01",
                                       "minimum_wage.tokyo@2025-10-03", "minimum_wage.tokyo@2026-10-01")
    assert {r.id for r in rules if AN.rule_bridge(r) is not None} == {"minimum_wage.tokyo",
                                                                       "consumption_tax.filing_deadline"}
    assert all(AN.rule_bridge(r)["kind"] == "machine" and r.kind == "human" for r in rules if "bridge" in r.params)
    # remove_at は計画の段の語(つなぎの台帳の PLAN_STAGES)で統一(説明の文は remove_note)
    from shibuya.foundation.decl import bridging as BL

    assert {AN.rule_bridge(r)["remove_at"] for r in rules if "bridge" in r.params} <= BL.PLAN_STAGES
    # 法定労働時間の行は前から human(床の機械の側が無い=つなぎを足さない)
    hours = rules.get("labor.statutory_hours", "2026-07-13")
    assert hours.kind == "human" and "bridge" not in hours.params


def test_kinds_are_the_table_kinds():
    assert AN._RULE_KINDS == RT.KINDS


@pytest.mark.parametrize("bad", [
    "machine",                                                     # 辞書でない
    {k: v for k, v in BRIDGE.items() if k != "conf"},              # 欄が無い
    {**BRIDGE, "extra": "x"},                                      # 知らない欄
    {**BRIDGE, "kind": "robot"},                                   # kind の外
    {**BRIDGE, "kind": "human"},                                   # 行と同じ kind=つなぎにならない
    {**BRIDGE, "conf": "0.5"},                                     # conf の外
    {**BRIDGE, "remove_at": " "},                                  # 空
])
def test_a_bad_bridge_is_refused(bad):
    with pytest.raises(ValueError):
        AN.rule_bridge(_row("human", bad))


def test_no_bridge_is_none_and_the_ledger_id_is_optional():
    assert AN.rule_bridge(_row("machine")) is None
    b = {k: v for k, v in BRIDGE.items() if k not in ("ledger_id", "remove_note")}
    assert dict(AN.rule_bridge(_row("human", b))) == b


# ================================================================= 床は kind とつなぎで決まる
def test_the_floor_follows_the_kind_and_the_bridge():
    src = "rules:minimum_wage.tokyo@2026-10-01"
    assert AN.min_wage_floor(FLOOR_DAY, RT.Rules([_row("machine")])) == (1_280, src)
    assert AN.min_wage_floor(FLOOR_DAY, RT.Rules([_row("human", BRIDGE)])) == (1_280, src)
    assert AN.min_wage_floor(FLOOR_DAY, RT.Rules([_row("human")])) == (None, f"human:{src}")
    assert AN.min_wage_floor(FLOOR_DAY, RT.Rules([_row("norm")])) == (None, f"norm:{src}")
    assert AN.min_wage_floor("2026-09-30", RT.Rules([_row("human", BRIDGE)])) == (None, "none")
    t = AN.min_wage_terms(FLOOR_DAY, RT.Rules([_row("human", BRIDGE)]))
    assert (t.kind, t.enforced_by, t.floor_by_machine) == ("human", AN.ENFORCED_BRIDGE, True)
    t = AN.min_wage_terms(FLOOR_DAY, RT.Rules([_row("human")]))
    assert (t.enforced_by, t.floor_by_machine, t.yen_per_hour) == (AN.ENFORCED_NONE, False, 1_280)
    # リポの表(既定)=つなぎの床
    assert WG.min_wage_terms("2026-08-25").enforced_by == AN.ENFORCED_BRIDGE
    assert WG.min_wage_floor("2026-08-25") == (1_226, "rules:minimum_wage.tokyo@2025-10-03")


def test_floor_with_shortfall_is_apply_floor_byte_for_byte_under_the_bridge():
    rng = np.random.default_rng(11)
    m = rng.integers(-5, 400_000, 2_000).astype(np.int64)
    h = rng.uniform(0, 200, 2_000)
    h[::17] = np.nan
    terms = AN.min_wage_terms(FLOOR_DAY, RT.Rules([_row("human", BRIDGE)]))
    want, raised = WG.apply_floor(m, h, 1_280)
    paid, lifted, below, short = WG.floor_with_shortfall(m, h, terms)
    assert paid.dtype == want.dtype and paid.tobytes() == want.tobytes()
    assert lifted.tobytes() == raised.tobytes() and below.tobytes() == raised.tobytes() and raised.any()
    assert short == int((want - m)[raised].sum()) > 0
    # つなぎの無い human: 払う額はそのまま・下回った体と額は同じ
    t2 = AN.min_wage_terms(FLOOR_DAY, RT.Rules([_row("human")]))
    paid2, lifted2, below2, short2 = WG.floor_with_shortfall(m, h, t2)
    assert paid2.tobytes() == m.tobytes() and not lifted2.any()
    assert below2.tobytes() == raised.tobytes() and short2 == short
    # 版の無い日=床も下回りも無い
    t3 = AN.min_wage_terms("2024-09-30")
    paid3, lifted3, below3, short3 = WG.floor_with_shortfall(m, h, t3)
    assert paid3.tobytes() == m.tobytes() and not lifted3.any() and not below3.any() and short3 == 0


# ================================================================= 給料日の器
def _low_ledger(monkeypatch, n: int = 40, tables=None):
    tb = _low_tables() if tables is None else tables
    monkeypatch.setattr(WG, "load_wage_tables", lambda root=None: tb)
    plan = _plan(n=4)
    inp = _inputs(n, occ_words=["事務従事者"] * n, emp_words=["正規"] * n, sex=[0] * n, age=[50] * n)
    plan = types.SimpleNamespace(**{**vars(plan), "kinds": np.zeros(n, np.int64), "wage_inputs": inp,
                                    "date_of": lambda d: FLOOR_DAY, "date_of_step": lambda st: FLOOR_DAY,
                                    "employment": lambda d: (np.arange(n), np.full(n, E), np.full(n, 2))})
    led = Ledger(n, 2, 3)
    led.attach_stage2(plan)
    led.endow_households(np.full(n, 1_000), 0)
    return led


def _high_tables():
    tb = _tables()
    return WG.WageTables(**{f: getattr(tb, f) for f in WG.WAGE_TABLE_FIELDS
                            if f not in ("wage_cls_lo", "wage_cls_hi")},
                         wage_cls_lo=np.array([400_000.0, 450_000.0, 500_000.0, 550_000.0, 600_000.0]),
                         wage_cls_hi=np.array([450_000.0, 500_000.0, 550_000.0, 600_000.0, 650_000.0]), md5={"high": "0"})


def _pay(led) -> np.ndarray:
    dep0 = np.asarray(led.balance(BalanceLine.DEPOSIT, H), dtype=np.int64).copy()
    led.on_day_end(1)
    return np.asarray(led.balance(BalanceLine.DEPOSIT, H), dtype=np.int64) - dep0


def test_the_box_is_empty_at_the_start_and_has_no_window_words(monkeypatch):
    led = _low_ledger(monkeypatch)
    box = led.stage2.s2_meter["rules"][S2.SHORTFALL_KEY]
    st2 = led.stage2
    below0 = int((st2.monthly_wage < int(round(1_280 * 160.0))).sum())
    assert below0 > 0
    assert box == {"rule": "minimum_wage.tokyo", "scope": "run", **{k: 0 for k in S2.SHORTFALL_COUNTS},
                   "below_at_start": below0, "last": None}
    for k in (S2.SHORTFALL_KEY, *S2.SHORTFALL_COUNTS, "scope", "below_at_start", "last", "bridge_ledger_id",
              "enforced_by", "wage_path"):
        assert "open" not in k and "tick" not in k, k


def test_positive_control_counts_the_shortfall_and_the_bridge_lifts_it(monkeypatch):
    """正の対照: 床を下回る賃金を合成した体で件数が立つ・つなぎの床が上げる=起きた違反は 0・払う額は床つき(前と同じ)。"""
    led = _low_ledger(monkeypatch)
    st2 = led.stage2
    floor_amt = int(round(1_280 * 160.0))
    below = st2.monthly_wage < floor_amt
    assert below.any() and (~below).any()
    got = _pay(led)
    assert np.array_equal(got, np.where(below, floor_amt, st2.monthly_wage))
    short = int((floor_amt - st2.monthly_wage)[below].sum())
    box = st2.s2_meter["rules"][S2.SHORTFALL_KEY]
    assert (box["paydays"], box["checked"]) == (1, 40)
    assert (box["below_rows"], box["below_amount"]) == (int(below.sum()), short)
    assert (box["lifted_rows"], box["lifted_amount"]) == (int(below.sum()), short)
    assert (box["violation_rows"], box["violation_amount"]) == (0, 0)
    assert box["last"] == {"asof": "2026-10-23", "yen_per_hour": 1_280, "source": "rules:minimum_wage.tokyo@2026-10-01",
                           "kind": "human", "enforced_by": "bridge",
                           "bridge_ledger_id": "DOC-s2rules-min-wage-floor-bridge", "wage_path": "occupation"}
    f = st2.s2_meter["rules"]["wage_model"]["floor"]  # 前からの給料日の計器と同じ数
    assert (f["raised"], f["raised_amount"]) == (box["lifted_rows"], box["lifted_amount"])
    rec = st2.manifest_record(led)
    assert rec["rules"][S2.SHORTFALL_KEY] == box
    assert led.meter.last_day["conservation"]["ok"] is True


def test_without_the_bridge_the_wage_stays_below_and_the_violation_is_recorded(monkeypatch):
    """つなぎを外した表(human だけ): 床を当てず下回ったまま払う=起きた違反を記録(金は湧かない=保存則の残差 0)。"""
    monkeypatch.setattr(RT, "default_rules", lambda: RT.Rules([_row("human")]))
    led = _low_ledger(monkeypatch)
    st2 = led.stage2
    floor_amt = int(round(1_280 * 160.0))
    below = st2.monthly_wage < floor_amt
    got = _pay(led)
    assert np.array_equal(got, st2.monthly_wage)
    box = st2.s2_meter["rules"][S2.SHORTFALL_KEY]
    short = int((floor_amt - st2.monthly_wage)[below].sum())
    assert (box["below_rows"], box["below_amount"]) == (int(below.sum()), short)
    assert (box["lifted_rows"], box["lifted_amount"]) == (0, 0)
    assert (box["violation_rows"], box["violation_amount"]) == (int(below.sum()), short) and short > 0
    assert box["last"]["enforced_by"] == "none" and box["last"]["bridge_ledger_id"] is None
    # 〔検収 L4〕つなぎの無い表でも、組み立ての日に下回る体の数は器に残る(前からの floor_at_start は床なし=0)
    assert box["below_at_start"] == int(below.sum()) > 0
    assert st2.s2_meter["rules"]["wage_build"]["floor_at_start"]["raised"] == 0
    assert st2.s2_meter["rules"]["wage_model"]["floor"]["source"] == "human:rules:minimum_wage.tokyo@2026-10-01"
    assert led.meter.last_day["conservation"]["ok"] is True and led.meter.last_day["conservation"]["residual"] == 0


def test_negative_control_high_wages_count_nothing(monkeypatch):
    """負の対照: 賃金が床より上の体だけ=件数 0。"""
    led = _low_ledger(monkeypatch, tables=_high_tables())
    st2 = led.stage2
    assert (st2.monthly_wage >= int(round(1_280 * 160.0))).all()
    _pay(led)
    box = st2.s2_meter["rules"][S2.SHORTFALL_KEY]
    assert box["paydays"] == 1 and box["checked"] == 40
    assert all(box[k] == 0 for k in S2.SHORTFALL_COUNTS if k not in ("paydays", "checked"))


def test_before_the_rule_is_in_force_nothing_is_counted(monkeypatch):
    monkeypatch.setattr(WG, "load_wage_tables", lambda root=None: _low_tables())
    led = Ledger(4, 2, 3)
    led.attach_stage2(_plan(day=NO_FLOOR_DAY))
    led.endow_households(np.full(4, 1_000), 0)
    led.on_day_end(1)
    box = led.stage2.s2_meter["rules"][S2.SHORTFALL_KEY]
    assert (box["paydays"], box["checked"], box["below_rows"], box["violation_rows"]) == (1, 3, 0, 0)
    assert box["last"]["enforced_by"] == "none" and box["last"]["yen_per_hour"] is None


def test_the_hours_times_hourly_path_counts_but_has_no_floor(monkeypatch):
    """2-1 の道(賃金の表の無い写し=月の時間 × 時給): 床の式は前から無い=数えるだけ。時給が既定(最低賃金)なら 0・
    合成の低い時給なら下回ったまま払った体が violation に立つ(金の流れは前と同じ)。"""
    monkeypatch.setattr(WG, "load_wage_tables", lambda root=None: None)
    with pytest.warns(WG.WageTablesAbsentWarning):
        led = Ledger(4, 2, 3)
        led.attach_stage2(_plan(day=FLOOR_DAY))
    led.endow_households(np.full(4, 1_000), 0)
    led.on_day_end(1)
    box = led.stage2.s2_meter["rules"][S2.SHORTFALL_KEY]
    assert (box["checked"], box["below_rows"], box["violation_rows"]) == (3, 0, 0)
    assert box["last"]["wage_path"] == "tables_absent"
    assert box["last"]["enforced_by"] == "none"  # 〔検収 L2〕2-1 の道は床を当てない
    assert box["below_at_start"] is None  # 賃金の表の無い写し=組み立ての月の賃金が無い
    with pytest.warns(WG.WageTablesAbsentWarning):
        led2 = Ledger(4, 2, 3)
        led2.attach_stage2(types.SimpleNamespace(**{**vars(_plan(day=FLOOR_DAY)), "hourly": np.full(4, 1_000.0)}))
    led2.endow_households(np.full(4, 1_000), 0)
    led2.on_day_end(1)
    pay = int(round(S2.DEFAULT_MONTHLY_HOURS * 1_000))
    assert led2.meter.last_day["stage2"]["wages"]["amount"] == 3 * pay  # 床なし(前と同じ)
    box2 = led2.stage2.s2_meter["rules"][S2.SHORTFALL_KEY]
    short = 3 * (int(round(S2.DEFAULT_MONTHLY_HOURS * 1_280)) - pay)
    assert (box2["below_rows"], box2["below_amount"], box2["lifted_rows"]) == (3, short, 0)
    assert (box2["violation_rows"], box2["violation_amount"]) == (3, short)


# ================================================================= 〔検収 L1・M1〕ランの始めの検査・申告の期限のつなぎ
def test_a_broken_bridge_in_a_later_version_stops_the_run_at_the_start(monkeypatch):
    """給料日に効いていない後の版のつなぎが壊れていても、組み立て(ランの始め)で落ちる。"""
    bad = {**BRIDGE, "conf": "0.5"}
    monkeypatch.setattr(RT, "default_rules", lambda: RT.Rules([_row("human", BRIDGE, yen=1_226, asof="2025-10-03"),
                                                              _row("human", bad)]))
    with pytest.raises(ValueError, match="conf"):
        _low_ledger(monkeypatch)
    assert AN.check_rule_bridges(RT.Rules([_row("machine")])) == ()


def test_the_filing_deadline_bridge_is_read_from_params_bridge():
    from shibuya.economy import taxes as TX

    row = RT.default_rules().get(TX.DEADLINE_RULE_ID, "2026-12-31")
    b = AN.rule_bridge(row)
    assert b["kind"] == "machine" and b["ledger_id"] == "DOC-rules42-tax-remit-machine" and b["remove_at"] == "6-6"
    assert TX.filing_deadline(2026) == (dt.date(2027, 3, 31), "rules:consumption_tax.filing_deadline@2026-10-01")
    # つなぎの無い human の行は、つなぎの読み口が止める
    d = row.as_dict()
    d["params"] = {k: v for k, v in d["params"].items() if k != "bridge"}
    with pytest.raises(ValueError, match="params.bridge"):
        TX._bridge_row(TX.DEADLINE_RULE_ID, "2026-12-31", RT.Rules([RT.Rule.from_dict(d)]))
