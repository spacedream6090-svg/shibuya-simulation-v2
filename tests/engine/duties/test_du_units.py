"""第 6 期 6-6 ② 第 1 部 店の仕事の単体の試験: 店の決まりの口(担当だけが知る・区切り・常識の文)・仮のモデル(一様・決定論・
閉じた語)・呼びの id・腕の切替口・AST の負の対照(本人の語の原因は判断の呼びだけ・候補を出す条件に時刻の直書きが無い)。"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from shibuya.engine.decision.port import DecisionContext
from shibuya.engine.duties import arm as AD
from shibuya.engine.duties import port as PD
from shibuya.engine.duties.knowledge import UNKNOWN, ShopRules, rules_line
from shibuya.engine.rights import ledger as L

SRC = Path(__file__).resolve().parents[3] / "src" / "shibuya" / "engine" / "duties"


def _rules(rule_row: tuple[int, int] = (540, 1260)) -> ShopRules:
    tab = np.zeros((2, 1440), dtype=bool)
    tab[0, rule_row[0]:rule_row[1]] = True
    tab[1, 600:1200] = True
    led = L.Rights()
    led.grant(L.Right(holder=(L.AGENT, 7), object=(L.STORE, 0), kind=L.EMPLOY, source="試験"))
    return ShopRules(SimpleNamespace(open_matrix=tab, rights=led))


def test_only_the_staff_knows_the_store_rules():
    r = _rules()
    assert r.at([7, 8, 7], [0, 0, 1], 600, 0).tolist() == [1, UNKNOWN, UNKNOWN]  # 雇用の行の無い体・店は知らない
    assert r.at([7], [0], 500, 0).tolist() == [0] and r.at([7], [0], 540 + 1440, 0).tolist() == [1]  # 日で巻き戻す
    assert r.hours(7, 0, 0) == [(540, 1260)] and r.hours(8, 0, 0) == []
    assert rules_line(r, 7, 0, 0) == "店の決まり: 営業 9:00〜21:00。(出どころ不明)" and rules_line(r, 8, 0, 0) == ""
    assert r.edge(7, 0, 530, 0, rising=True) == 540 and r.edge(7, 0, 1250, 0, rising=False) == 1260
    assert r.edge(8, 0, 530, 0, rising=True) is None
    assert r.closed_days(0, range(7)) == ()  # 休業日の枠(カレンダー 3 の店の決まりの口=親クラス)は空のまま


def test_store_rules_follow_the_table_rows():
    assert _rules((780, 1260)).hours(7, 0, 0) == [(780, 1260)]
    assert _rules((780, 1260)).at([7], [0], 700, 0).tolist() == [0]


def test_store_rules_without_a_table_know_nothing():
    r = ShopRules(SimpleNamespace(open_matrix=np.zeros((0, 0), dtype=bool), rights=L.Rights()))
    assert r.at([1], [0], 600, 0).tolist() == [UNKNOWN] and r.hours(1, 0, 0) == []


def test_mock_port_is_uniform_deterministic_and_closed():
    port = PD.DutiesPort(seed=1, day_key0=0, step_seconds=60)
    cands = [PD.cand(PD.K_SHOP, "店を開ける", id=PD.ID_UNLOCK), PD.cand(PD.K_WAIT, "まだ", id="wait")]
    picks = []
    for k in range(1, 401):
        ctx = DecisionContext(agent_id=3, step=k, t_ns=0, wake_class=-1, condition=-1, cell=0,
                              call_id=PD.call_id_of(k, 3, PD.serial_of(PD.P_SHOP, 1)))
        a = port.choose(ctx, cands)
        b = port.choose(ctx, cands)
        assert a == b
        picks.append(a.candidate_id)
    share = picks.count(PD.ID_UNLOCK) / len(picks)
    assert 0.4 < share < 0.6
    with pytest.raises(KeyError):
        PD.cand("価格改定", "値段を変える")


def test_call_ids_do_not_collide_with_other_ports():
    from shibuya.engine.calendar3 import port as P3

    s = PD.serial_of(PD.P_WASTE, PD.MAX_DECISIONS_PER_STEP - 1)
    assert PD.SERIAL_BASE > P3.SERIAL_BASE + 16 * P3.MAX_DECISIONS_PER_STEP
    assert PD.parse_call_id(PD.call_id_of(5, 2, s)) == (5, 2, s) and PD.purpose_of_serial(s) == PD.P_WASTE
    assert PD.parse_call_id(P3.call_id_of(5, 2, P3.serial_of(P3.P_FRAME, 1))) is None
    assert PD.parse_call_id("5:2:3") is None
    with pytest.raises(ValueError):
        PD.serial_of(PD.P_SHOP, PD.MAX_DECISIONS_PER_STEP)


def test_first_per_store_takes_the_first_eligible_row():
    """〔検収 M1〕雇用の行(店の順)のうち候補になれる行の、店ごとの最初の行(1 店 1 刻み 1 人)。"""
    from shibuya.engine.duties.layer import first_per_store

    stores = np.array([0, 0, 0, 2, 2, 5])
    agents = np.array([10, 11, 12, 20, 21, 50])
    p, a, rows = first_per_store(stores, agents, np.array([False, True, True, True, True, False]))
    assert p.tolist() == [0, 2] and a.tolist() == [11, 20] and rows.tolist() == [1, 3]
    p, a, rows = first_per_store(stores, agents, np.zeros(6, dtype=bool))
    assert p.size == a.size == rows.size == 0


def test_store_rules_source_mark():
    """〔検収 M3〕出どころの印(W7 の列 src)・実データには印を付けない・列が無ければ不明。"""
    r = _rules()
    assert r.source(0) == "unknown" and rules_line(r, 7, 0, 0).endswith("(出どころ不明)")
    r.shops.assets = SimpleNamespace(plan_src_names=("category_default", "osm_opening_hours"),
                                     plan_poi_src=np.array([0, 1], dtype=np.int16))
    assert r.source(0) == "category_default" and r.source(1) == "osm_opening_hours"
    assert rules_line(r, 7, 0, 0) == "店の決まり: 営業 9:00〜21:00。(出どころ category_default=作り物の印)"
    r.shops.assets.plan_poi_src[0] = 1
    assert rules_line(r, 7, 0, 0) == "店の決まり: 営業 9:00〜21:00。"


def test_arm_switch():
    prev = AD.arm()
    try:
        AD.set_arm("arm")
        assert AD.is_on() and AD.config() == {"arm": "arm"}
        AD.set_arm("off")
        assert not AD.is_on() and AD.config() is None
        with pytest.raises(ValueError):
            AD.set_arm("on")
    finally:
        AD.set_arm(prev)


# ================================================================= AST: 本人の語の原因は判断の呼びだけ
_PERSON = {"W_UNLOCK", "W_LOCK", "W_RESTOCK", "W_DISCARD"}


def _cause_problems(src: str) -> list[str]:
    """(1) ``_log`` の本人の語の原因は名前 ``cause`` だけ・(2) ``cause`` に入れてよいのは ``self._decide`` の答え(組の 2 つ目)と、
    役割語の道(``_role_word``)の ``LlmCall(…)`` だけ・(3) ``cause`` を引数で受ける関数は呼び手が (2) の ``cause`` を渡す。"""
    tree = ast.parse(src)
    bad: list[str] = []
    fns = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    for fn in fns:
        for node in ast.walk(fn):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "_log":
                what = node.args[2] if len(node.args) > 2 else None
                cause = node.args[3] if len(node.args) > 3 else None
                names = {n.id for n in ast.walk(what) if isinstance(n, ast.Name)} if what is not None else set()
                if names & _PERSON and not (isinstance(cause, ast.Name) and cause.id == "cause"):
                    bad.append(f"{fn.name}: 本人の語の原因が判断の呼びでない(行 {node.lineno})")
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    tgt = [e for e in (t.elts if isinstance(t, ast.Tuple) else [t]) if isinstance(e, ast.Name)]
                    if not any(e.id == "cause" for e in tgt):
                        continue
                    v = node.value
                    ok_decide = (isinstance(t, ast.Tuple) and isinstance(v, ast.Call)
                                 and isinstance(v.func, ast.Attribute) and v.func.attr == "_decide")
                    ok_role = (fn.name == "_role_word" and isinstance(v, ast.Call)
                               and getattr(v.func, "id", "") == "LlmCall")
                    if not (ok_decide or ok_role):
                        bad.append(f"{fn.name}: 原因を判断の呼びの外から作った(行 {node.lineno})")
    return bad


def test_ast_person_events_come_only_from_decisions():
    assert _cause_problems((SRC / "layer.py").read_text(encoding="utf-8")) == []


def test_ast_negative_control_catches_planted_causes():
    planted = '''
class X:
    def _engine_unlocks(self, T, t_ns, a, p):
        self._log(t_ns, a, W_UNLOCK, Process("opening"), poi=p)
        cause = LlmCall("1:2:-4194321")
        self._log(t_ns, a, W_RESTOCK, cause, poi=p)
        self._log(t_ns, a, W_LOCK if p else W_DISCARD, LlmCall("x"), poi=p)
'''
    assert len(_cause_problems(planted)) == 3, _cause_problems(planted)


# ================================================================= AST: 候補を出す条件に時刻の直書きが無い
_OFFER_FNS = {"_shop_offers", "run_step"}


def _time_problems(src: str) -> list[str]:
    """候補を出す条件を作る関数(``_shop_offers``・``run_step``)の比較と算術に、0・1 と名前のほかの数(時刻の直書き)が無い。
    ``_shop_offers`` は店の決まりの口(``self.rules.at``)の答えだけで条件を作る(開閉の行列を直に読まない)。"""
    tree = ast.parse(src)
    bad: list[str] = []
    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name in _OFFER_FNS]:
        for node in ast.walk(fn):
            if isinstance(node, (ast.Compare, ast.BinOp)):
                for c in ast.walk(node):
                    if isinstance(c, ast.Constant) and isinstance(c.value, (int, float)) and not isinstance(c.value, bool) \
                            and c.value not in (0, 1, -2):
                        msg = f"{fn.name}: 時刻の直書き {c.value}(行 {c.lineno})"
                        if msg not in bad:
                            bad.append(msg)
            if fn.name == "_shop_offers" and isinstance(node, ast.Attribute) and node.attr == "open_matrix":
                bad.append(f"{fn.name}: 開閉の行列を直に読んだ(行 {node.lineno})")
    return bad


def test_ast_offer_conditions_have_no_time_literals():
    assert _time_problems((SRC / "layer.py").read_text(encoding="utf-8")) == []


def test_ast_negative_control_catches_time_literals():
    planted = '''
class X:
    def _shop_offers(self, s, pois, minute, t_ns, now):
        unlock = (minute >= 540) & (now[pois] == 0)
        lock = self.opening.open_matrix[pois, minute] == 0
        return unlock, lock

    def run_step(self, T, t_ns, td, day, **kw):
        if td % 1440 == 300:
            pass
'''
    assert len(_time_problems(planted)) == 4, _time_problems(planted)
