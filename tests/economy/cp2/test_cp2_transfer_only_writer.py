"""第 1 期 1-9(CP2 の段階 1): お金の列の書き手は基本操作 ``economy.ops.transfer`` の中だけ(AST・負の対照つき)。

口の約束 1-9 の受入の試験 ``test_cp2_transfer_only_writer.py``。お金の列=``economy.ops.MONEY_PATHS``(agents.money・
pois.revenue・帳簿の残高 ``_lines``・流れの表 ``_flow``・最後に動いた日・生ログ ``_raw_*``)。

- src の全ファイルを AST で見て、お金の列への書きを集める(道具 ``money_writers.py``・別名・``np.add.at``・属性の鎖・
  ``out=``・``fill``・``field("money")`` を通す)。
- 基本操作 ``economy/ops.py`` の ``transfer`` の外の書きは、凍結の表 ``money_writers_frozen.json``(組み立て・締め・
  評価替え・段階 2=resolve の行動の適用の中)にあるものだけ。表は減るだけ(表にあって書きが無い行も落ちる)。
- 負の対照: 別名・``np.add.at``・属性の鎖(発注の 3 本)+ ``ops.py`` の transfer の外・実物の ledger.py に足した書き・
  ``out=``・``field``・``fill``。
- 1-0 の別名の表(``engine.systems.allow.ALIAS_WRITES``)から ``_apply_cash`` の行が消え、帳簿の口の呼び出しから引く
  規則 1 つになった(閉包は同じ=``writes_soa_frozen.json`` の試験が見る)。
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from shibuya.economy import ops as OPS
from shibuya.economy.ledger import Ledger
from shibuya.engine.systems import allow as AL

from tests.economy.cp2 import money_writers as MW

HERE = Path(__file__).resolve().parent
SRC = HERE.parents[2] / "src" / "shibuya"
FROZEN = json.loads((HERE / "money_writers_frozen.json").read_text(encoding="utf-8"))
DECLARED: dict[tuple[str, str], set[str]] = {(w["path"], w["func"]): set(w["attrs"]) for w in FROZEN["writers"]}
RAW_COLUMNS = {"_raw_tick", "_raw_ps", "_raw_pi", "_raw_qs", "_raw_qi", "_raw_amt", "_raw_code",
               "_raw_event_t_ns", "_raw_event_seq", "_raw_pos", "_raw_head"}


@pytest.fixture(scope="module")
def writes() -> list[MW.Write]:
    return MW.scan_tree(SRC)


def _by_owner(ws):
    out: dict[tuple[str, str], set[str]] = {}
    for w in ws:
        out.setdefault((w.path, w.func), set()).add(w.attr)
    return out


# ================================================================= 本物の src
def test_money_columns_are_written_only_inside_transfer(writes):
    """基本操作の外の書きは凍結の表(組み立て・締め・評価替え・段階 2)にあるものだけ。"""
    bad = MW.violations(writes, DECLARED)
    assert bad == [], [f"{w.path}:{w.line} {w.func} {w.attr} ({w.form})" for w in bad]


def test_the_frozen_table_has_no_stale_rows(writes):
    """表の行は実際の書きと同じ(書きが消えたら表の行も消す=表は減るだけ)。"""
    got = _by_owner(writes)
    for key, attrs in DECLARED.items():
        assert got.get(key) == attrs, (key, sorted(got.get(key, set())), sorted(attrs))
    kinds = {w["kind"] for w in FROZEN["writers"]}
    assert kinds <= {"組み立て", "締め", "評価替え", "段階 2"}


def test_the_primitive_writes_every_money_column_of_the_ledger(writes):
    """正の対照: transfer は帳簿の残高・流れの表・最後に動いた日・生ログの全部の列を書く(道具が書きを見ている)。"""
    got = _by_owner(writes)[MW.PRIMITIVE]
    assert {"_lines", "_flow", "_last_change_day"} <= got
    assert RAW_COLUMNS <= got
    forms = {w.form for w in writes if (w.path, w.func) == MW.PRIMITIVE}
    assert {"ufunc.at", "添字への代入", "添字への代入(+=)", "属性の差し替え(+=)"} <= forms


def test_the_money_paths_are_declared_once():
    assert set(OPS.MONEY_PATHS) == {"agents.money", "pois.revenue", "ledger.money._lines", "ledger.money._flow",
                                    "ledger.money._last_change_day", "ledger.money._raw_*"}
    assert OPS.MONEY_ATTRS == {"money", "revenue", "_lines", "_flow", "_last_change_day"}
    assert OPS.MONEY_ATTR_PREFIX == "_raw_"


def test_only_the_ledger_ports_call_the_primitive():
    """``ops.transfer`` を呼ぶのは帳簿の口(economy/ledger.py の Ledger のメソッド)だけ。"""
    callers: set[tuple[str, str]] = set()
    for rel, text in MW.iter_sources(SRC):
        tree = ast.parse(text)
        for cls in [n for n in tree.body if isinstance(n, ast.ClassDef)] + [None]:
            body = cls.body if cls is not None else tree.body
            for fn in [b for b in body if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef))]:
                for node in ast.walk(fn):
                    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                            and node.func.attr == "transfer" and isinstance(node.func.value, ast.Name)
                            and node.func.value.id in ("_OPS", "OPS", "ops")):
                        callers.add((rel, f"{cls.name}.{fn.name}" if cls is not None else fn.name))
    assert callers == {("economy/ledger.py", "Ledger.transfer"), ("economy/ledger.py", "Ledger.transfer_many"),
                       ("economy/ledger.py", "Ledger.depreciate")}, callers
    # 旧い書き手は消した(transfer の中に移した)
    assert not hasattr(Ledger, "_apply_cash") and not hasattr(Ledger, "_record")


# ================================================================= 1-0 の別名の表
def test_the_apply_cash_alias_rows_are_gone():
    """``_apply_cash`` の別名の 4 行は消え、帳簿の口の呼び出しから AST で引く(閉包は前と同じ)。"""
    assert not any("_apply_cash" in why for _w, why in AL.ALIAS_WRITES.values())
    assert set(AL.ALIAS_WRITES) == {"apply_detection"}
    callers = {f for f, _ln, _p in AL.index().transfer_callers}
    assert callers == {"_complete_buy", "_complete_eat", "_board_riders", "initialize"}
    assert AL.TRANSFER_WRITES == ("agents.money",)
    for fn in callers:
        assert "agents.money" in AL.writes_for_ops({fn})


def test_the_household_ports_exist_and_move_household_cash():
    """口の名の表(engine 側)は economy の口と突き合う: 世帯を払い手か受け手にする Ledger の口と運賃の口。"""
    from shibuya.engine.processes.rail import RailProcess

    assert set(AL.TRANSFER_PORTS_HOUSEHOLD) == {"purchase_many", "endow_households", "pay_fares"}
    from types import MappingProxyType

    assert isinstance(AL.TRANSFER_PORTS_HOUSEHOLD, MappingProxyType)  # 検収 L6: 実行時に書き換えられない
    assert callable(getattr(Ledger, "purchase_many")) and callable(getattr(Ledger, "endow_households"))
    assert callable(getattr(RailProcess, "pay_fares"))
    # Ledger の口のうち世帯の部門を書くのはこの 2 つ(ほかは transfer/transfer_many=汎用・endow_stores=店・depreciate)
    src = (SRC / "economy" / "ledger.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    led = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Ledger")
    hh = set()
    for fn in [b for b in led.body if isinstance(b, ast.FunctionDef)]:
        if "Sector.HOUSEHOLD" in ast.unparse(fn) and fn.name not in ("attach_household_cash", "freeze", "_unfreeze",
                                                                    "bytes_total"):
            hh.add(fn.name)
    assert hh == {"purchase_many", "endow_households"}, hh


# ================================================================= 負の対照
def _bad(code: str, path: str = "economy/goods.py") -> list[MW.Write]:
    return MW.violations(MW.scan_source(code, path), DECLARED)


def test_negative_alias():
    """負の対照 1(別名): 台帳の残高の行を局所の名に取ってから書く。"""
    bad = _bad("def leak(led):\n    c = led._lines[0][1]\n    c[3] = 5\n")
    assert [(w.func, w.attr, w.form) for w in bad] == [("leak", "_lines", "添字への代入")]
    # 別名の鎖・for の別名・+=
    bad = _bad("def leak(led):\n    a = led._lines\n    b = a[0]\n    for arr in b:\n        arr += 1\n")
    assert [(w.attr, w.form) for w in bad] == [("_lines", "別名への +=")]


def test_negative_ufunc_at():
    """負の対照 2(np.add.at): writeable=False を無視して書ける形(numpy 2.5 実測)。"""
    bad = _bad("import numpy as np\ndef leak(agents):\n    np.add.at(agents.registry.money, [0], 1)\n",
               "engine/presence.py")
    assert [(w.func, w.attr, w.form) for w in bad] == [("leak", "money", "ufunc.at")]
    bad = _bad("import numpy as np\ndef leak(world):\n    rev = world.pois.revenue\n    np.subtract.at(rev, [1], 2)\n")
    assert [(w.attr, w.form) for w in bad] == [("revenue", "ufunc.at")]


def test_negative_attribute_chain():
    """負の対照 3(属性の鎖): 箱から台帳をたどって生ログと売上の写しを書く。"""
    bad = _bad("def leak(b, world):\n    b.layers.ledger.money._raw_amt[0] = 1\n    world.pois.revenue[3] += 7\n"
               "    b.layers.ledger.money._raw_pos += 1\n", "engine/systems/act.py")
    assert [(w.attr, w.form) for w in bad] == [("_raw_amt", "添字への代入"), ("revenue", "添字への代入(+=)"),
                                              ("_raw_pos", "属性の差し替え(+=)")]


def test_negative_outside_transfer_in_ops_and_in_the_real_ledger():
    """ops.py の transfer の外・実物の ledger.py の口に足した書きも落ちる(置き場でなく関数で見る)。"""
    bad = _bad("def helper(led):\n    led._flow[0, 0, 0] = 1\n", "economy/ops.py")
    assert [(w.func, w.attr) for w in bad] == [("helper", "_flow")]
    real = (SRC / "economy" / "ledger.py").read_text(encoding="utf-8")
    planted = real.replace("    def raw_rows(self) -> np.ndarray:\n",
                           "    def _sneak(self, i):\n        cash = self._lines[0][1]\n        np.add.at(cash, i, 9)\n\n"
                           "    def raw_rows(self) -> np.ndarray:\n", 1)
    assert planted != real
    bad = _bad(planted, "economy/ledger.py")
    assert [(w.func, w.attr) for w in bad] == [("Ledger._sneak", "_lines")]
    assert _bad(real, "economy/ledger.py") == []  # 足す前は通る


def test_negative_other_forms():
    """out=・field("money")・fill・np.copyto・差し替え。"""
    code = ("import numpy as np\n"
            "def leak(led, reg, x):\n"
            "    np.maximum(x, 0, out=led._flow)\n"
            "    reg.field('money')[2] = 0\n"
            "    led._last_change_day[1].fill(0)\n"
            "    np.copyto(reg.money, x)\n"
            "    led._raw_head = 5\n")
    got = [(w.attr, w.form) for w in _bad(code)]
    assert got == [("_flow", "out="), ("money", "添字への代入"), ("_last_change_day", ".fill()"),
                   ("money", "np.copyto"), ("_raw_head", "属性の差し替え")], got
    # 読むだけ・旗だけ・台帳の束の欄の差し替えは書きではない
    ok = ("def fine(led, bundle, a):\n    s = led._flow.sum()\n    arr = led._lines[0][0]\n"
          "    arr.flags.writeable = False\n    bundle.money = None\n    return a.money[0] + s\n")
    assert _bad(ok) == []
