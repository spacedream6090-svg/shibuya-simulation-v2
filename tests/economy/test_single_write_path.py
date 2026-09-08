"""**単一API の静的検査**(境界・経済設計書 §2.3 / 世界過程設計書 §7.1)。

    「``transfer(payer, payee, amount, account_code)`` 単一API・残高の直接代入は**静的に禁止**」
    「``move_goods(from, to, qty, sku, account_code)`` 単一API・在庫の直接代入は**静的禁止**」

強制は二重: (a) 台帳の配列は既定で ``writeable=False``(実行時)
           (b) 本ファイルの AST 検査 = 台帳の内部配列に触れてよいモジュールを1本に限る(静的)
"""

from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pytest

from shibuya.economy.accounts import BalanceLine, Sector
from shibuya.economy.goods import GoodsLedger
from shibuya.economy.ledger import Ledger

SRC = Path("src/shibuya")
LEDGER = "src/shibuya/economy/ledger.py"
GOODS = "src/shibuya/economy/goods.py"

#: 金の台帳の残高配列(触れてよいのは ledger.py だけ)。
MONEY_PRIVATE = ("_lines", "_flow", "_last_change_day")
#: 物の台帳の在庫配列(触れてよいのは goods.py だけ)。
GOODS_PRIVATE = ("_shelf", "_bin", "_household_sku", "_row_sku", "_waste_sku")


def _modules_touching(attrs: tuple[str, ...]) -> list[str]:
    """``<何か>.<attr>`` に**触れる**モジュール(読み書きどちらでも)を列挙する。"""
    out: list[str] = []
    for path in sorted(SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in attrs:
                out.append(str(path).replace("\\", "/"))
                break
    return out


def _modules_calling(name: str) -> list[str]:
    out: list[str] = []
    for path in sorted(SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == name:
                    out.append(str(path).replace("\\", "/"))
                    break
    return out


def test_only_ledger_module_touches_the_balance_arrays():
    """残高配列に触れるのは economy/ledger.py だけ(= transfer 単一API)。"""
    assert _modules_touching(MONEY_PRIVATE) == [LEDGER]


def test_only_goods_module_touches_the_stock_arrays():
    """在庫配列に触れるのは economy/goods.py だけ(= move_goods 単一API)。"""
    assert _modules_touching(GOODS_PRIVATE) == [GOODS]


def test_only_the_owning_modules_open_the_write_window():
    """``_open``(書き込み窓)を economy の中で呼べるのは台帳自身だけ。"""
    callers = [p for p in _modules_calling("_open") if "/economy/" in p]
    assert callers == [GOODS, LEDGER]


def test_economy_never_calls_the_world_write_window():
    """``.writable(`` / ``.thaw(`` は engine/resolve.py と state モジュールの専有。

    economy がこれを呼べてしまうと「書き込み口は resolve 1本」が崩れる
    (``tests/engine/test_two_phase.py`` の同型検査を economy 側からも張る)。
    """
    for name in ("writable", "thaw"):
        callers = [p for p in _modules_calling(name) if "/economy/" in p]
        assert callers == [], (name, callers)


def test_engine_does_not_import_economy():
    """依存逆転: engine は economy を import しない(import-linter の層契約の同型検査)。"""
    offenders: list[str] = []
    for path in sorted((SRC / "engine").rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith(
                "shibuya.economy"
            ):
                offenders.append(str(path))
            if isinstance(node, ast.Import):
                for a in node.names:
                    if a.name.startswith("shibuya.economy"):
                        offenders.append(str(path))
    assert offenders == []


def test_runtime_guard_rejects_direct_writes():
    """(a) 実行時の強制: 台帳の配列は既定で読み取り専用。"""
    led = Ledger(3, 2)
    goods = GoodsLedger.from_pois(np.zeros(2, dtype=np.int64), np.full(2, 4), np.full(2, 300))
    assert led.frozen and goods.frozen
    with pytest.raises(ValueError):
        led.balance(BalanceLine.CASH, Sector.STORE)[0] = 10
    with pytest.raises(ValueError):
        goods.shelf[0, 0] = 10
    with pytest.raises(ValueError):
        goods.bins[0, 0] = 10


def test_attached_agent_money_is_not_unfrozen_by_the_ledger():
    """採用した ``agents.money`` のフラグは台帳が触らない(窓の持ち主は resolve)。

    numpy の ``np.add.at`` は ``writeable=False`` を**無視して書ける**(2.5.3 実測)ので、
    台帳は自前でフラグを検査する。この検査が無いと「書き込み口は resolve 1本」が
    静かに破れる(親へ報告した発見)。
    """
    money = np.zeros(4, dtype=np.int32)
    led = Ledger(4, 1)
    led.attach_household_cash(money)
    money.flags.writeable = False
    with led.unlocked():
        assert not money.flags.writeable  # 台帳は外部配列のフラグを立てない
    with pytest.raises(ValueError, match="読み取り専用"):
        led.endow_households(np.full(4, 100, dtype=np.int64), tick=0)
    assert int(money.sum()) == 0
    money.flags.writeable = True
    led.endow_households(np.full(4, 100, dtype=np.int64), tick=0)
    assert int(money.sum()) == 400


def test_numpy_add_at_ignores_the_readonly_flag():
    """発見の記録: ``np.add.at`` は読み取り専用配列に**書けてしまう**。

    既存の ``AgentState.freeze`` / ``World.freeze`` の守りも ``np.add.at`` 経路には
    効かない(直接代入だけが弾かれる)。台帳側は自前検査で塞いだが、engine 側の
    ``np.add.at(world.pois.stock, …)`` 等は同じ穴が空いたままである(親へ報告)。
    """
    a = np.zeros(3, dtype=np.int32)
    a.flags.writeable = False
    with pytest.raises(ValueError):
        a[0] = 1
    np.add.at(a, np.array([0]), np.array([5], dtype=np.int32))
    assert int(a[0]) == 5  # ← フラグが効いていない
