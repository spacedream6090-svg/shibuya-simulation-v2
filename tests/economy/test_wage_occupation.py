"""賃金を職業ごとの実データから(小さな版上げ・2026-10-17・回答 10-13b §7 の 3)。

- 共有: 実行時の ``economy.wages`` の式は 4-1 段 5 の ``build.pop.attr_fns`` の賃金の関数と同じ物(移した=同じ値)・分位の
  乱数は ``AttrKey.uniform`` と同じ引き方・実データの写しの読み解きは構築の読み口と同じ表(data が要る)。
- 純粋: 同じ鍵で同じ値・``open`` 0 回・入力を書き換えない。W17 の勤務時間を読まない(AST+負の対照)。
- 写像: ペルソナの職業の語 → 職種・雇用の語 → 雇用形態・写せない体は雇用形態と年齢(と性)だけの平均・与えた値が先。
- 給料日: 賃金の腕 occupation は体ごとの月の賃金を払う(原資=外界の売上=同じ額・保存則の残差 0)・w17 は今までの額・
  表の写しが無い写しは注記して 160 時間 × 最低賃金。
- 切替口: ``--wage``・見出しと再開の検査。
"""

from __future__ import annotations

import ast
import datetime as dt
import inspect
import sys
import textwrap
import types
from pathlib import Path

import numpy as np
import pytest

from shibuya.build.pop import attr_fns as A
from shibuya.economy import stage2 as S2
from shibuya.economy import wages as WG
from shibuya.economy.accounts import AccountCode, BalanceLine, Sector
from shibuya.economy.ledger import Ledger
from shibuya.engine import economy_stage2 as ES2
from shibuya.engine.events import log as EV

H, S, E, B, G, W = (int(s) for s in Sector)
O_ = len(WG.WAGE_OCCUPATIONS)
K_ = 5


def _tables() -> WG.WageTables:
    """合成の賃金の表(職種ごとに水準を変える・階級 5)。"""
    occ_scale = 1.0 + 0.1 * np.arange(O_)
    level = np.empty((O_, 2, 2))
    level[:, :, 0] = 300_000.0 * occ_scale[:, None]
    level[:, :, 1] = 220_000.0 * occ_scale[:, None]
    freq = np.tile(np.array([1.0, 3.0, 5.0, 3.0, 1.0]), (O_, 2, 1)) * occ_scale[:, None, None]
    return WG.WageTables(
        wage_level=level, wage_bonus=np.full((O_, 2, 2), 500_000.0), wage_hours=np.full((O_, 2, 2), 160.0),
        wage_all=280_000.0 * np.tile(occ_scale[:, None], (1, 2)),
        wage_age_ratio=np.tile(np.linspace(0.7, 1.3, WG.WAGE_AGE_EDGES.size), (O_, 2, 1)),
        bonus_age_ratio=np.ones((O_, 2, WG.WAGE_AGE_EDGES.size)),
        wage_cls_lo=np.array([100_000.0, 200_000.0, 300_000.0, 400_000.0, 500_000.0]),
        wage_cls_hi=np.array([200_000.0, 300_000.0, 400_000.0, 500_000.0, 600_000.0]),
        wage_cls_freq=freq, wage_median=np.full((O_, 2), 350_000.0), pt_hourly=np.full((O_, 2), 1_300.0),
        pt_bonus=np.full((O_, 2), 30_000.0), pt_hours_day=np.full((O_, 2), 5.0), pt_days=np.full((O_, 2), 15.0),
        md5={"synthetic": "0"})


def _status(words) -> np.ndarray:
    lut = {w: i for i, w in enumerate(A.EMP_STATUS)}
    return np.array([lut.get(w, -1) for w in words], dtype=np.int64)


# ================================================================ 共有(二重に作らない)
def test_build_and_runtime_share_one_function():
    assert A.WAGE_OCCUPATIONS is WG.WAGE_OCCUPATIONS and A.WAGE_AGE_EDGES is WG.WAGE_AGE_EDGES
    assert A._wage_quantile is WG.wage_quantile
    from shibuya.core import wage_formula as WF

    assert WG.wage_values is WF.wage_values and WG.occupation_wages is WF.occupation_wages
    # 式の置き場は numpy と core.rng だけを読む(build が読んでも engine と llm が読まれない)
    imports = {n.module for n in ast.walk(ast.parse(Path(WF.__file__).read_text(encoding="utf-8")))
               if isinstance(n, ast.ImportFrom) and n.module}
    assert {m for m in imports if m.startswith("shibuya")} == {"shibuya.core.rng"}
    from shibuya.build.pop import w21_money as M

    assert M.WAGE_CLASS_FLOOR_YEN == WG.WAGE_CLASS_FLOOR_YEN and M.WAGE_TOP_FACTOR == WG.WAGE_TOP_FACTOR
    src = inspect.getsource(M.load_wage_tables)
    assert "parse_wage_tables" in src and "searchsorted" not in src  # 読み解きは 1 か所
    assert "wage_values" in inspect.getsource(A._wage) and "wage_cls_freq" not in inspect.getsource(A._wage)


def test_attr_fns_wage_equals_runtime_wage_values_with_the_same_draw():
    tb = _tables()
    n = 3_000
    rng = np.random.default_rng(5)
    st = _status(rng.choice(["regular", "dispatched", "part_time", "executive", "self_employed", ""], n))
    attrs = {"emp_status": st, "occupation_major": rng.integers(0, 12, n), "sex": rng.integers(0, 2, n),
             "age": rng.integers(15, 80, n)}
    counters = np.stack([np.arange(n), np.zeros(n, np.int64), np.zeros(n, np.int64)], axis=1)
    key = A.AttrKey(20260909, WG.WAGE_DOMAIN, counters)
    m_build = A.call("wage_monthly", attrs, tb, key)
    occ, sex, form, ok = A._occ_sex_form(attrs)
    u = WG.wage_uniform(20260909, np.arange(n))
    assert np.array_equal(u, key.uniform()[:, 0])  # 分位の乱数は AttrKey と同じ引き方
    m_rt, h_rt, a_rt = WG.wage_values(tb, occ, sex, form, ok, attrs["age"], u)
    assert np.array_equal(m_build, m_rt)
    assert np.array_equal(A.call("wage_hourly", attrs, tb, key), h_rt)
    assert np.array_equal(A.call("wage_annual", attrs, tb, key), a_rt)
    assert (m_rt[ok] > 0).all() and (m_rt[~ok] == -1).all()


@pytest.mark.requires_data("world_v2")
def test_runtime_reader_equals_the_build_reader(tmp_path):
    rt = WG.load_wage_tables()
    if rt is None:
        pytest.skip("requires_data: 賃金の表の写し(research_cache/pop41b/derived)が無い")
    from shibuya.build.pop import w21_money as M
    from shibuya.build.pop import w21_sources as SRC

    for sid, (name, md5, src_md5) in WG.DERIVED_FILES.items():  # 写しの台帳と同じ md5(build は実行時に読めない=写し)
        s = SRC.source(sid)
        assert s.derived[-1] == name and s.derived_md5 == md5 and s.md5 == src_md5
        assert "/".join(s.derived[:-1]) == WG.DERIVED_RELDIR.removeprefix("data/")
    data = Path(__file__).resolve().parents[2] / "data"
    if not all(data.joinpath(*SRC.source(sid).path).exists() for sid in WG.DERIVED_FILES):
        pytest.skip("requires_data: 賃金構造の元の xlsx が無い")
    g = SRC.W21Guard.for_build(data, out=tmp_path / "out")
    with g.active():
        bt = M.load_wage_tables(g)
    for f in WG.WAGE_TABLE_FIELDS:
        assert np.array_equal(np.asarray(getattr(rt, f)), np.asarray(bt[f])), f
    assert set(rt.md5) == {v[0] for v in WG.DERIVED_FILES.values()}


def test_reader_refuses_a_wrong_md5_and_returns_none_when_absent(tmp_path):
    assert WG.load_wage_tables(tmp_path) is None
    for name, _md5, _src in WG.DERIVED_FILES.values():
        (tmp_path / name).write_text('{"dims":[],"items":[],"rows":[]}', encoding="utf-8")
    with pytest.raises(ValueError, match="md5"):
        WG.load_wage_tables(tmp_path)


# ================================================================ 純粋・W17 を読まない
def _inputs(n: int, *, occ_words=None, emp_words=None, sex=None, age=None):
    occ_words = occ_words if occ_words is not None else ["事務従事者"] * n
    emp_words = emp_words if emp_words is not None else ["正規"] * n
    occ, ov = ES2._vocab(np.array(occ_words, dtype=object))
    emp, ev = ES2._vocab(np.array(emp_words, dtype=object))
    return ES2.WageInputs(occ_code=occ, occ_vocab=ov, emp_code=emp, emp_vocab=ev,
                          sex=np.zeros(n, np.int8) if sex is None else np.asarray(sex, np.int8),
                          age=np.full(n, 40, np.int16) if age is None else np.asarray(age, np.int16),
                          counters=np.arange(n, dtype=np.int64), seed=7, source="test")


def _ow(tb, inp, given=None):
    return WG.occupation_wages(tb, occ_code=inp.occ_code, occ_vocab=inp.occ_vocab, emp_code=inp.emp_code,
                               emp_vocab=inp.emp_vocab, sex=inp.sex, age=inp.age, seed=inp.seed,
                               counters=inp.counters, given=given)


def test_occupation_wages_are_pure():
    tb = _tables()
    rng = np.random.default_rng(1)
    n = 2_000
    inp = _inputs(n, occ_words=list(rng.choice([*WG.WAGE_OCCUPATIONS, "非就業", "通学", ""], n)),
                  emp_words=list(rng.choice(["正規", "非正規", "役員", "自営業主", "非就業", ""], n)),
                  sex=rng.integers(-1, 2, n), age=rng.integers(-1, 80, n))
    before = {k: np.array(getattr(inp, k), copy=True) for k in ("occ_code", "emp_code", "sex", "age", "counters")}
    _ow(tb, inp)  # 遅れて読まれる import を先に済ませる
    seen: list[str] = []
    on = [True]

    def hook(ev, args):
        if on[0] and ev == "open":
            seen.append(str(args[0]))

    sys.addaudithook(hook)
    w1, b1 = _ow(tb, inp)
    w2, b2 = _ow(tb, inp)
    on[0] = False
    assert seen == []  # open 0 回
    assert np.array_equal(w1, w2) and np.array_equal(b1, b2)
    for k, v in before.items():
        assert np.array_equal(getattr(inp, k), v), k
    assert (w1 > 0).all()  # 雇用の行のある体に払う額は全部の体にある


#: W17 の勤務時間に当たる名(識別子・属性・引数・import)。賃金の道に 1 つも出ない。
_W17_NAMES = ("monthly_hours", "weekly_work_hours", "weekly", "WEEKS_PER_MONTH", "ACTIVITY_WORDS", "hours_source",
              "DEFAULT_MONTHLY_HOURS", "w17_schedule", "start_min", "end_min")


def _w17_hits(tree: ast.AST) -> list[str]:
    hits = []
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Name):
            names = [node.id]
        elif isinstance(node, ast.Attribute):
            names = [node.attr]
        elif isinstance(node, ast.arg):
            names = [node.arg]
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name for a in node.names] + ([node.module] if getattr(node, "module", None) else [])
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in _W17_NAMES:
            names = [node.value]  # getattr(plan, "monthly_hours") の形
        for nm in names:
            if any(nm == w or nm.endswith("." + w) or ".weekly" in str(nm) for w in _W17_NAMES):
                hits.append(nm)
    return hits


def test_wage_path_does_not_read_w17_hours_ast_with_a_negative_control():
    from shibuya.core import wage_formula as WF

    for f in (WG.__file__, WF.__file__):
        assert _w17_hits(ast.parse(Path(f).read_text(encoding="utf-8"))) == [], f
    for fn in (ES2.wage_inputs, ES2.persona_words, S2.MoneyStage2._occupation_wages):
        assert _w17_hits(ast.parse(textwrap.dedent(inspect.getsource(fn)))) == [], fn.__name__
    # 負の対照: W17 の時間を読む関数は見つかる
    bad = "def f(plan, weekly):\n    h = plan.monthly_hours\n    return getattr(plan, 'monthly_hours', None)\n"
    assert set(_w17_hits(ast.parse(bad))) == {"monthly_hours", "weekly"}


# ================================================================ 写像・平均・与えた値
def test_mapping_average_and_given():
    tb = _tables()
    occ_words = ["事務従事者", "販売従事者", "非就業", "通学", "", "販売従事者", "事務従事者"]
    emp_words = ["正規", "非正規", "正規", "", "", "役員", "正規"]
    sex = [0, 1, 0, -1, 1, 0, -1]
    age = [40, 30, 40, 50, -1, 45, 40]
    inp = _inputs(7, occ_words=occ_words, emp_words=emp_words, sex=sex, age=age)
    w, b = _ow(tb, inp)
    assert list(b) == [WG.BASIS_OCCUPATION, WG.BASIS_OCCUPATION, WG.BASIS_AVERAGE, WG.BASIS_AVERAGE,
                       WG.BASIS_AVERAGE, WG.BASIS_OCCUPATION, WG.BASIS_AVERAGE]
    assert (w > 0).all()
    # 写せない体の平均は、同じ u・雇用形態・年齢での職種ごとの値の間に入る
    u = WG.wage_uniform(7, np.arange(7))
    for i in (2, 3, 4):
        s_list = [sex[i]] if sex[i] >= 0 else [0, 1]
        vals = [WG.wage_values(tb, np.array([o]), np.array([s]), np.array([0]), np.array([True]),
                               np.array([age[i]]), u[i:i + 1], unknown_age_ratio_one=True)[0][0]
                for o in range(O_) for s in s_list]
        assert min(vals) <= w[i] <= max(vals), i
    # 性が分からない「事務」の体は事務の男女の平均(職種は写す)
    vals6 = [WG.wage_values(tb, np.array([2]), np.array([s]), np.array([0]), np.array([True]), np.array([40]),
                            u[6:7])[0][0] for s in (0, 1)]
    assert min(vals6) <= w[6] <= max(vals6)
    # 役員は正社員・正職員の表(雇用形態の比=正社員)・非正規は正社員以外の表
    reg = WG.wage_values(tb, np.array([3]), np.array([0]), np.array([0]), np.array([True]), np.array([45]), u[5:6])
    assert w[5] == reg[0][0]
    nonreg = WG.wage_values(tb, np.array([3]), np.array([1]), np.array([1]), np.array([True]), np.array([30]),
                            u[1:2])
    assert w[1] == nonreg[0][0]
    # 与えた値(W21 の wage_monthly)が先
    given = np.array([-1, 123_456, -1, -1, -1, -1, -1])
    w2, b2 = _ow(tb, inp, given=given)
    assert w2[1] == 123_456 and b2[1] == WG.BASIS_GIVEN and np.array_equal(np.delete(w2, 1), np.delete(w, 1))


def test_persona_words_reads_only_wanted_rows_and_skips_l4(tmp_path):
    import json

    for layer, rows in (("L2", [{"occupation_major": "事務従事者", "employment": "正規"},
                                {"occupation_major": "販売従事者", "employment": "非正規"},
                                {"occupation_major": "サービス職業従事者", "employment": None}]),
                        ("L4", [{"occupation_major": "販売従事者", "employment": "正規"}])):
        d = tmp_path / layer
        d.mkdir()
        lines = [json.dumps(r, ensure_ascii=False) for r in rows]
        (d / "part-0000.jsonl").write_text(lines[0] + "\n\n", encoding="utf-8")  # 空の行は数えない
        (d / "part-0001.jsonl").write_text("\n".join(lines[1:]) + "\n", encoding="utf-8")
    got, read = ES2.persona_words(tmp_path, np.array([2, 2, 4, 2, 0, 2]), np.array([1, 2, 0, 1, -1, 0]))
    assert list(got["occupation_major"]) == ["販売従事者", "サービス職業従事者", "", "販売従事者", "", "事務従事者"]
    assert list(got["employment"]) == ["非正規", "", "", "非正規", "", "正規"]
    assert read == 3  # 同じ行を指す 2 体は 1 回だけ読む・L4 は読まない


def test_wage_inputs_without_population_and_with_a_fake_population(tmp_path):
    sched = types.SimpleNamespace(master_seed=11)
    w = ES2.wage_inputs(sched, None, 3)
    assert w.source == "no_population" and w.occ_vocab == () and (w.sex == -1).all() and (w.age == -1).all()
    assert w.seed == 11 and list(w.counters) == [0, 1, 2]
    pop = types.SimpleNamespace(n=2, sex=np.array([1, 0]), age=np.array([33, 44]), source_agent_id=np.array([900, 77]),
                                pool_layer=np.array([2, 2]), pool_index=np.array([0, 0]))
    with pytest.warns(ES2.DataAbsentWarning):
        w2 = ES2.wage_inputs(sched, pop, 3, pool_root=tmp_path / "none")
    assert w2.source == "pool_absent" and list(w2.counters) == [900, 77, 2] and list(w2.age) == [33, 44, -1]
    with pytest.raises(ValueError):
        w2.sex[0] = 0  # 読み取り専用


# ================================================================ 給料日(帳簿)
#: 合成の帳簿の試験の日=規則の表に最低賃金の版が無い日(2024-10-01 より前=床なし・〔第337〕前の 2 版を足した)。
NO_FLOOR_DAY = dt.date(2024, 8, 26)


def _plan(wage_model="occupation", n=4, inputs=None, day=NO_FLOOR_DAY):
    cal_day = day
    return types.SimpleNamespace(
        parts=S2.PARTS, kinds=np.array([0, 0, 3, 2])[:n], monthly_hours=None, hours_source="none(wage=occupation)",
        atms=None, cause=lambda name: EV.Process(name), date_of_step=lambda step: cal_day,
        date_of=lambda day: cal_day, is_payday=lambda day: day == 1, close_step=lambda day: 1439,
        employment=lambda day: (np.array([0, 2, 3]), np.array([E, E, S]), np.array([2, 2, 1])),
        record=lambda: {}, wage_model=wage_model,
        wage_inputs=inputs if inputs is not None else _inputs(n, occ_words=["事務従事者", "販売従事者", "", "非就業"],
                                                              emp_words=["正規", "非正規", "", "正規"],
                                                              sex=[0, 1, -1, 1], age=[40, 30, -1, 50]))


def test_payroll_pays_occupation_wages_with_matching_funding(monkeypatch):
    tb = _tables()
    monkeypatch.setattr(WG, "load_wage_tables", lambda root=None: tb)
    led = Ledger(4, 2, 3)
    led.attach_stage2(_plan())
    st2 = led.stage2
    want = st2.monthly_wage.copy()
    assert st2.wage_source == "occupation" and (want > 0).all()
    led.endow_households(np.full(4, 1_000), 0)
    dep0 = np.asarray(led.balance(BalanceLine.DEPOSIT, H), dtype=np.int64).copy()
    led.on_day_end(0)
    led.on_day_end(1)
    dep1 = np.asarray(led.balance(BalanceLine.DEPOSIT, H), dtype=np.int64)
    assert list(dep1 - dep0) == [want[0], 0, want[2], want[3]]
    day = led.meter.last_day
    assert day["conservation"]["ok"] is True and day["conservation"]["residual"] == 0
    wages = int(led.flow_daily[-1][:, :, int(AccountCode.WAGE)].sum())
    assert wages == int(want[[0, 2, 3]].sum()) == day["stage2"]["wages"]["amount"] == day["stage2"]["wages"]["funding"]
    # 原資=外界 → 雇用主・店(消費支出=払う賃金と同じ額)=雇用主の手元は 0 のまま
    assert int(np.asarray(led.balance(BalanceLine.CASH, E))[2]) == 0
    m = st2.s2_meter["rules"]["wage_model"]
    assert m["employed"] == 3 and m["paid_by_basis"] == {"occupation": 1, "average": 2, "given": 0}
    rec = st2.manifest_record(led)
    assert rec["plan"]["wage_path"] == "occupation"
    assert rec["rules"]["wage_build"]["path"] == "occupation" and rec["rules"]["wage_build"]["bodies"] == 4
    g = st2.growth_declaration(employers=3)
    assert g.per_agent_bytes == S2.BYTES_PER_AGENT + S2.WAGE_BYTES_PER_AGENT
    with pytest.raises(ValueError):
        st2.monthly_wage[0] = 1  # 読み取り専用


def test_payroll_w17_arm_keeps_the_old_amount(monkeypatch):
    monkeypatch.setattr(WG, "load_wage_tables", lambda root=None: pytest.fail("w17 は賃金の表を読まない"))
    led = Ledger(4, 2, 3)
    led.attach_stage2(_plan(wage_model="w17"))
    assert led.stage2.monthly_wage is None and led.stage2.wage_source == "w17"
    led.endow_households(np.full(4, 1_000), 0)
    dep0 = np.asarray(led.balance(BalanceLine.DEPOSIT, H), dtype=np.int64).copy()
    led.on_day_end(0)
    led.on_day_end(1)
    pay = int(round(S2.DEFAULT_MONTHLY_HOURS * 1_226))
    assert list(np.asarray(led.balance(BalanceLine.DEPOSIT, H), dtype=np.int64) - dep0) == [pay, 0, pay, pay]
    assert "wage_model" not in led.stage2.s2_meter["rules"]
    rec = led.stage2.manifest_record(led)
    assert "wage_path" not in rec["plan"] and "wage_build" not in rec["rules"]
    assert led.stage2.growth_declaration(employers=3).per_agent_bytes == S2.BYTES_PER_AGENT


def test_tables_absent_falls_back_with_a_note(monkeypatch):
    monkeypatch.setattr(WG, "load_wage_tables", lambda root=None: None)
    led = Ledger(4, 2, 3)
    with pytest.warns(WG.WageTablesAbsentWarning, match="賃金の表"):
        led.attach_stage2(_plan())
    assert led.stage2.monthly_wage is None and led.stage2.wage_source == "tables_absent"
    assert issubclass(WG.WageTablesAbsentWarning, UserWarning) and not issubclass(WG.WageTablesAbsentWarning, RuntimeWarning)
    led.endow_households(np.full(4, 1_000), 0)
    led.on_day_end(1)
    pay = int(round(S2.DEFAULT_MONTHLY_HOURS * 1_226))
    assert led.meter.last_day["stage2"]["wages"]["amount"] == 3 * pay


# ================================================================ 切替口・見出し・再開
def test_arm_switch_header_and_resume_check(monkeypatch):
    assert ES2.DEFAULT_WAGE == "occupation" and ES2.WAGE_ARMS == ("occupation", "w17")
    with pytest.raises(ValueError):
        ES2.set_wage_arm("hours")
    monkeypatch.setattr(ES2, "_ARM", ES2.ARM_ON)
    monkeypatch.setattr(ES2, "_PARTS", ES2.PARTS)
    plan_occ = types.SimpleNamespace(parts=ES2.PARTS, wage_model="occupation")
    plan_w17 = types.SimpleNamespace(parts=ES2.PARTS, wage_model="w17")
    assert ES2.header_fields(plan_occ) == {"arm": "on", "parts": list(ES2.PARTS), "wage": "occupation"}
    assert ES2.header_fields(plan_w17) == {"arm": "on", "parts": list(ES2.PARTS)}  # w17 の見出しは今のまま
    monkeypatch.setattr(ES2, "_WAGE", "occupation")
    ES2.check_resume({"arm": "on", "parts": list(ES2.PARTS), "wage": "occupation"})
    with pytest.raises(ValueError, match="賃金の腕"):
        ES2.check_resume({"arm": "on", "parts": list(ES2.PARTS)})  # 見出しに無い=w17(版上げの前の状態)
    monkeypatch.setattr(ES2, "_WAGE", "w17")
    ES2.check_resume({"arm": "on", "parts": list(ES2.PARTS)})
    ES2.check_resume({"arm": "off"}, effective=False)


def test_cli_wage_switch(monkeypatch):
    from shibuya import cli

    seen = []
    monkeypatch.setattr(ES2, "set_wage_arm", lambda name: seen.append(name))
    monkeypatch.setattr(cli, "run", lambda **kw: types.SimpleNamespace())
    src = inspect.getsource(cli)
    assert '"--wage"' in src and "set_wage_arm(str(args.wage))" in src
    assert "_ES2.wage_arm() != _ES2.DEFAULT_WAGE" in src  # 既定と違えば腕のラン
    with pytest.raises(SystemExit):
        cli.main(["--wage", "hours"])


# ================================================================ 〔検収 M1〕最低賃金法の床
def test_min_wage_floor_reads_only_the_rules_table():
    assert WG.min_wage_floor("2024-09-30") == (None, "none")  # 表に版の無い日=床なし(直書きに戻さない)
    assert WG.min_wage_floor("2024-10-01") == (1_163, "rules:minimum_wage.tokyo@2024-10-01")
    assert WG.min_wage_floor("2026-08-25") == (1_226, "rules:minimum_wage.tokyo@2025-10-03")  # 世界の時点の給料日
    assert WG.min_wage_floor("2026-10-01") == (1_280, "rules:minimum_wage.tokyo@2026-10-01")
    from shibuya.economy import anchors as AN

    src = inspect.getsource(AN.min_wage_floor)
    assert "MIN_WAGE_HOURLY" not in src and "1226" not in src and "1_226" not in src


def test_apply_floor_and_month_hours():
    m, raised = WG.apply_floor(np.array([100_000, 300_000, -1, 150_000]), np.array([160.0, 160.0, 160.0, np.nan]),
                               1_280)
    assert list(m) == [204_800, 300_000, -1, 150_000] and list(raised) == [True, False, False, False]
    same, none = WG.apply_floor(np.array([1, 2]), np.array([160.0, 160.0]), None)
    assert list(same) == [1, 2] and not none.any()
    tb = _tables()
    inp = _inputs(4, occ_words=["事務従事者", "事務従事者", "非就業", ""], emp_words=["正規", "非正規", "正規", "正規"],
                  sex=[0, 1, 0, -1])
    h = WG.month_hours(tb, occ_code=inp.occ_code, occ_vocab=inp.occ_vocab, emp_code=inp.emp_code,
                       emp_vocab=inp.emp_vocab, sex=inp.sex)
    assert np.allclose(h, 160.0)  # 合成の表は全部 160 時間(写せない体は平均)


def _low_tables():
    tb = _tables()
    return WG.WageTables(**{f: getattr(tb, f) for f in WG.WAGE_TABLE_FIELDS
                            if f not in ("wage_cls_lo", "wage_cls_hi")},
                         wage_cls_lo=np.array([60_000.0, 100_000.0, 150_000.0, 200_000.0, 300_000.0]),
                         wage_cls_hi=np.array([100_000.0, 150_000.0, 200_000.0, 300_000.0, 400_000.0]), md5={"low": "0"})


def test_payroll_applies_the_floor_on_a_payday_with_the_rule_in_force(monkeypatch):
    tb = _low_tables()
    monkeypatch.setattr(WG, "load_wage_tables", lambda root=None: tb)
    n = 40
    plan = _plan(n=4)
    inp = _inputs(n, occ_words=["事務従事者"] * n, emp_words=["正規"] * n, sex=[0] * n, age=[50] * n)
    day = dt.date(2026, 10, 23)
    plan = types.SimpleNamespace(**{**vars(plan), "kinds": np.zeros(n, np.int64), "wage_inputs": inp,
                                    "date_of": lambda d: day, "date_of_step": lambda st: day,
                                    "employment": lambda d: (np.arange(n), np.full(n, E), np.full(n, 2))})
    led = Ledger(n, 2, 3)
    led.attach_stage2(plan)
    st2 = led.stage2
    floor_amt = int(round(1_280 * 160.0))
    below = st2.monthly_wage < floor_amt
    assert below.any() and (~below).any()
    assert st2.s2_meter["rules"]["wage_build"]["floor_at_start"]["raised"] == int(below.sum())
    led.endow_households(np.full(n, 1_000), 0)
    dep0 = np.asarray(led.balance(BalanceLine.DEPOSIT, H), dtype=np.int64).copy()
    led.on_day_end(1)
    got = np.asarray(led.balance(BalanceLine.DEPOSIT, H), dtype=np.int64) - dep0
    want = np.where(below, floor_amt, st2.monthly_wage)
    assert np.array_equal(got, want)
    f = st2.s2_meter["rules"]["wage_model"]["floor"]
    assert f["yen_per_hour"] == 1_280 and f["raised"] == int(below.sum())
    assert f["raised_amount"] == int((floor_amt - st2.monthly_wage)[below].sum())
    day_rec = led.meter.last_day
    assert day_rec["conservation"]["ok"] is True and day_rec["stage2"]["wages"]["funding"] == int(want.sum())


def test_payroll_has_no_floor_before_the_rule_is_in_force(monkeypatch):
    tb = _low_tables()
    monkeypatch.setattr(WG, "load_wage_tables", lambda root=None: tb)
    led = Ledger(4, 2, 3)
    led.attach_stage2(_plan())  # 2024-08-26=表に版が無い
    want = led.stage2.monthly_wage.copy()
    led.endow_households(np.full(4, 1_000), 0)
    led.on_day_end(1)
    f = led.stage2.s2_meter["rules"]["wage_model"]["floor"]
    assert f == {"yen_per_hour": None, "source": "none", "raised": 0, "raised_share": 0.0, "raised_amount": 0}
    assert led.meter.last_day["stage2"]["wages"]["amount"] == int(want[[0, 2, 3]].sum())
