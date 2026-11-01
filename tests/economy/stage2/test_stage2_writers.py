"""第 2 期 2-1 経済の段階 2: 新しい書き手を増やさない(1-9 の AST の検査が通る形)と、口の名の表の外の口の帳尻。

- 段階 2 の新しいモジュール(``economy/stage2.py``・``economy/credit.py``・``engine/economy_stage2.py``)はお金の列
  (``ops.MONEY_PATHS``)を書かない(帳簿の汎用の口 ``Ledger.transfer_many`` を呼ぶだけ=書くのは ``ops.transfer``)。
- resolve の中で段階 2 の口を呼ぶ関数: 引き出し(``withdraw_many``=世帯の現金が増える)は口の名の表
  ``TRANSFER_PORTS_HOUSEHOLD`` に足した(〔検収 A7・親の承認〕=``_stage2_withdraw`` は ``agents.money`` を書く関数として
  AST で引かれる)。読むだけの ``can_pay_many`` は表の外。どちらも「その関数を閉包に持つ系の ``writes.soa`` が
  ``agents.money`` を持つ」を確かめる(書き込みの許可は今の宣言のまま正しい=凍結の表 ``writes_soa_frozen.json`` は
  変わらない)。
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

from shibuya.engine.systems import allow as AL
from shibuya.engine.systems.table import SYSTEMS
from tests.economy.cp2 import money_writers as MW

HERE = Path(__file__).resolve().parent
SRC = HERE.parents[2] / "src" / "shibuya"
FROZEN = json.loads((HERE.parent / "cp2" / "money_writers_frozen.json").read_text(encoding="utf-8"))
DECLARED = {(w["path"], w["func"]): set(w["attrs"]) for w in FROZEN["writers"]}
NEW_MODULES = ("economy/stage2.py", "economy/credit.py", "engine/economy_stage2.py")
STAGE2_PORTS = ("withdraw_many", "can_pay_many", "pay_fares_many")


def test_new_modules_write_no_money_column():
    for rel in NEW_MODULES:
        ws = MW.scan_source((SRC / rel).read_text(encoding="utf-8"), rel)
        assert ws == [], [(w.func, w.attr, w.form) for w in ws]
        assert MW.violations(ws, DECLARED) == []


def test_new_modules_do_not_open_the_ledger_window_or_touch_the_balance_arrays():
    for rel in NEW_MODULES:
        text = (SRC / rel).read_text(encoding="utf-8")
        for bad in ("_unlocked", "_open(", "._lines", "._flow[", "_last_change_day"):
            assert bad not in text, (rel, bad)


def _callers_in_resolve(names: tuple[str, ...]) -> set[str]:
    tree = ast.parse((SRC / "engine" / "resolve.py").read_text(encoding="utf-8"))
    out: set[str] = set()
    for fn in (n for n in tree.body if isinstance(n, ast.FunctionDef)):
        for node in ast.walk(fn):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in names:
                out.add(fn.name)
    return out


def test_stage2_ports_in_resolve_are_inside_a_money_writing_closure():
    callers = _callers_in_resolve(STAGE2_PORTS)
    assert callers == {"_payable", "_stage2_withdraw"}, callers
    # 〔検収 A7〕引き出しの口だけが表に入る(読むだけの can_pay_many・rail の中の pay_fares_many は外)
    assert set(STAGE2_PORTS) & set(AL.TRANSFER_PORTS_HOUSEHOLD) == {"withdraw_many"}
    ix0 = AL.index()
    assert {f for f, _ln, p in ix0.transfer_callers if p == "withdraw_many"} == {"_stage2_withdraw"}
    assert "agents.money" in AL.writes_for_ops({"_stage2_withdraw"})
    ix = AL.index()
    holders = []
    for spec in SYSTEMS:
        if spec.name == "build":
            continue
        clo = AL.closure(spec.resolve_ops, ix)
        if callers & clo:
            holders.append(spec.name)
            assert "agents.money" in spec.writes.soa, spec.name
    assert "phase_c" in holders


def test_rail_and_ledger_route_through_the_generic_port():
    """運賃の IC の口(``pay_fares_many``)と賃金・引き出し・カードは ``Ledger.transfer_many`` だけを呼ぶ(``ops.transfer`` を直に
    呼ばない=1-9 の「基本操作を呼ぶのは帳簿の 3 つの口だけ」の試験と同じ)。"""
    for rel in NEW_MODULES:
        text = (SRC / rel).read_text(encoding="utf-8")
        assert "_OPS.transfer(" not in text and "ops.transfer(" not in text.replace("``ops.transfer``", "")
