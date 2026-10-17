"""第 1 期 1-3 出来事の記録: 原因は 3 種類だけ・実験の条件の口は 1 か所(CP12)。口の約束 1-3 の受入の試験
``test_e_cause_three_kinds``。

- 第 4 の原因の型は作れない(根の子・3 つの型の子・偽の型を ``Event`` と ``append`` に渡す)。
- 実験の条件の型 ``Experiment`` を ``engine/experiment/gate.py`` の外から作ると落ちる:
  (a) 静的=``src/shibuya`` の全ファイルの AST(呼び出し・import・別名・``getattr``・``vars``・``__dict__``・文字列の名・
  ``*`` の import)。型の定義の置き場(``engine/events/log.py``)と口(``gate.py``)だけが許される。負の対照は別名 12 形。
  (b) 実行時=``Experiment.__init__`` が呼び手のフレームを見る(負の対照: 直接・別名・getattr・replace・__init__ の
  呼び直し・型から作る・pickle)。書きの検査の切替口(``SHIBUYA_WRITE_GUARD=off``)でも外れない。正の対照=``gate.admit``。

限界(記録 e13/README.md): 静的な検査は実行時に組み立てた名(``"Exp" + "eriment"``)を記録の置き場の別名に
``getattr`` する形は「動的な getattr」として落とすが、別名を介さない形(引数で受け取ったモジュール)は見えない=実行時の
検査が受け持つ。``object.__new__`` で ``__init__`` を飛ばす形は型の名を書くので静的な検査が落とす。
"""

from __future__ import annotations

import ast
import copy
import dataclasses
import pickle
from pathlib import Path

import pytest

from shibuya.core import write_permit as WP
from shibuya.engine.events import log as EV
from shibuya.engine.experiment import gate as GATE

SRC = Path(__file__).resolve().parents[3] / "src" / "shibuya"
TYPE = "Experiment"
LOG_MODULE = "shibuya.engine.events.log"
#: 型の名を書いてよい置き場(``src/shibuya`` からの相対パス)。
ALLOWED = {"engine/events/log.py", "engine/experiment/gate.py"}


# ================================================================= 3 種類だけ
def test_three_kinds_only():
    assert EV.CAUSE_TYPES == (EV.LlmCall, EV.Process, EV.Experiment)
    assert EV.CAUSE_KINDS == ("llm_call", "process", "experiment")


@pytest.mark.parametrize("base_name", ["_Cause", "LlmCall", "Process", "Experiment"])
def test_a_fourth_cause_type_cannot_be_defined(base_name):
    base = getattr(EV, base_name)
    with pytest.raises(TypeError, match="3 種類"):
        type("Fourth", (base,), {})
    with pytest.raises(TypeError, match="3 種類"):
        type("Process", (base,), {"__module__": EV.__name__})  # 名と置き場を真似ても封じた後は作れない


def test_a_fake_cause_is_rejected_by_the_event_and_the_log():
    @dataclasses.dataclass(frozen=True)
    class Intervention:  # 心を直接書く・任意の関数(AgentSociety v1 の型)に当たる第 4 の種類の偽物
        name: str = "UPDATE_STATE_INTERVENE"

    with pytest.raises(TypeError):
        EV.Event(t_ns=0, who="engine", what="過程:rail", cause=Intervention())
    e = EV.Event(t_ns=0, who="engine", what="過程:rail", cause=EV.Process("rail"))
    object.__setattr__(e, "cause", Intervention())  # 凍結を破って差し替えても書く口が落とす
    with pytest.raises(TypeError, match="3 種類"):
        EV.EventLog().append(e)


# ================================================================= CP12 (a) 静的
def _log_aliases(tree: ast.AST) -> set[str]:
    out: set[str] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module == "shibuya.engine.events":
            out |= {a.asname or a.name for a in n.names if a.name == "log"}
        elif isinstance(n, ast.Import):
            out |= {a.asname for a in n.names if a.name == LOG_MODULE and a.asname}
    return out


def _is_log_ref(expr: ast.AST, aliases: set[str]) -> bool:
    if isinstance(expr, ast.Name):
        return expr.id in aliases
    try:
        return ast.unparse(expr) == LOG_MODULE
    except Exception:  # noqa: BLE001
        return False


def offenders(rel: str, tree: ast.AST) -> list[str]:
    """``rel`` で型 ``Experiment`` を作れる形(参照・import・文字列の名・記録の置き場の動的な取り出し)。"""
    if rel in ALLOWED:
        return []
    out: list[str] = []
    aliases = _log_aliases(tree)
    for n in ast.walk(tree):
        ln = getattr(n, "lineno", 0)
        if isinstance(n, ast.ImportFrom):
            for a in n.names:
                if a.name == TYPE:
                    out.append(f"{rel}:{ln}: 型の名を import する")
                if a.name == "*" and (n.module or "").startswith("shibuya.engine.events"):
                    out.append(f"{rel}:{ln}: 記録の置き場から * を import する")
        elif isinstance(n, ast.Name) and n.id == TYPE:
            out.append(f"{rel}:{ln}: 型の名 {TYPE} を参照する")
        elif isinstance(n, ast.Attribute) and n.attr == TYPE:
            out.append(f"{rel}:{ln}: 属性 .{TYPE} を参照する")
        elif isinstance(n, ast.Attribute) and n.attr == "__dict__" and _is_log_ref(n.value, aliases):
            out.append(f"{rel}:{ln}: 記録の置き場の __dict__ を読む")
        elif isinstance(n, ast.Constant) and isinstance(n.value, str) and (
                n.value == TYPE or n.value.endswith("." + TYPE)):
            out.append(f"{rel}:{ln}: 文字列の名 {n.value!r}(getattr・vars・import の材料)")
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.args:
            if n.func.id == "getattr" and len(n.args) >= 2 and not isinstance(n.args[1], ast.Constant) \
                    and _is_log_ref(n.args[0], aliases):
                out.append(f"{rel}:{ln}: 記録の置き場から動的な名で getattr する")
            if n.func.id == "vars" and _is_log_ref(n.args[0], aliases):
                out.append(f"{rel}:{ln}: 記録の置き場の vars を読む")
    return out


def test_no_module_outside_the_gate_names_the_experiment_type():
    found = []
    files = sorted(SRC.rglob("*.py"))
    assert len(files) > 100
    for fp in files:
        rel = fp.relative_to(SRC).as_posix()
        found += offenders(rel, ast.parse(fp.read_text(encoding="utf-8")))
    assert found == [], found


def test_the_allowed_places_do_name_the_type():
    """正の対照(静的): 許した 2 か所は実際に型の名を書いている(許しの表が空回りしていない)。"""
    for rel in sorted(ALLOWED):
        tree = ast.parse((SRC / rel).read_text(encoding="utf-8"))
        assert offenders("engine/fake_" + rel.replace("/", "_"), tree), rel


#: 負の対照(別名 12 形)。発注の 3 本=直接・別名・getattr は先頭の 3 つ。
PLANTED = {
    "direct": f"from {LOG_MODULE} import Experiment\nExperiment('c')\n",
    "alias": f"from {LOG_MODULE} import Experiment as X\nX('c')\n",
    "getattr": "from shibuya.engine.events import log as L\ngetattr(L, 'Experiment')('c')\n",
    "module_attr": f"import {LOG_MODULE} as L\nL.Experiment('c')\n",
    "package_attr": "from shibuya.engine.events import log\nlog.Experiment('c')\n",
    "dotted": f"import {LOG_MODULE}\n{LOG_MODULE}.Experiment('c')\n",
    "getattr_dynamic": "from shibuya.engine.events import log as L\nn = 'Exp' + 'eriment'\ngetattr(L, n)('c')\n",
    "vars": "from shibuya.engine.events import log as L\nvars(L)['Exp' + 'eriment']('c')\n",
    "module_dict": "from shibuya.engine.events import log as L\nk = 'x'\nL.__dict__[k]('c')\n",
    "star": "from shibuya.engine.events.log import *\nExperiment('c')\n",
    "importlib": f"import importlib\nm = importlib.import_module('{LOG_MODULE}')\nm.Experiment('c')\n",
    "new_without_init": "from shibuya.engine.events import log as L\nobject.__new__(L.Experiment)\n",
}


@pytest.mark.parametrize("form", list(PLANTED))
def test_static_check_catches_every_planted_form(form):
    got = offenders("engine/systems/fake.py", ast.parse(PLANTED[form]))
    assert got, (form, PLANTED[form])


# ================================================================= CP12 (b) 実行時
def _admitted():
    log = EV.EventLog()
    eid = GATE.admit(log, "cond-A", what="過程:opening", who="engine", origin="実験")
    return log, log.get(eid).cause


def test_gate_is_the_one_way_in():
    """正の対照: 口を通せば実験の条件の原因で 1 行書ける。"""
    log, cause = _admitted()
    assert type(cause) is EV.Experiment and cause.cond_id == "cond-A" and cause.kind == "experiment"
    assert len(log) == 1 and log.event(0).origin == "実験"
    assert EV.EventLog(enabled=False) is not None
    assert GATE.admit(EV.EventLog(enabled=False), "cond-B", what="過程:opening", who="engine") is None
    with pytest.raises(ValueError):
        GATE.admit(EV.EventLog(), "cond-C", what="過程:決定", who="engine")  # 語彙表の外は口でも落ちる


def test_runtime_direct():
    with pytest.raises(PermissionError, match="CP12"):
        EV.Experiment("x")


def test_runtime_alias():
    alias = EV.Experiment
    with pytest.raises(PermissionError, match="CP12"):
        alias("x")


def test_runtime_getattr():
    with pytest.raises(PermissionError, match="CP12"):
        getattr(EV, "Exp" + "eriment")("x")


def test_runtime_other_ways():
    _log, e = _admitted()
    with pytest.raises(PermissionError):
        dataclasses.replace(e, cond_id="y")
    with pytest.raises(PermissionError):
        type(e)("z")
    with pytest.raises(PermissionError):
        EV.Experiment.__init__(e, "w")  # 呼び直しでも中身は書き換わらない
    assert e.cond_id == "cond-A"
    with pytest.raises(TypeError):
        pickle.dumps(e)
    assert copy.copy(e) is e and copy.deepcopy(e) is e


def test_runtime_check_stays_on_when_the_write_guard_is_off():
    prev = WP.enabled()
    WP.set_enabled(False)
    try:
        with pytest.raises(PermissionError, match="CP12"):
            EV.Experiment("x")
        _log, e = _admitted()
        assert e.cond_id == "cond-A"
    finally:
        WP.set_enabled(prev)


# ---------------------------------------------------------------- 検収 M1(第334): 書くときにも門を確かめる
def _event_with(cause):
    return EV.Event(t_ns=0, who="engine", what="過程:opening", cause=cause)


def test_append_checks_the_gate_for_experiment_causes_reuse():
    """読み戻した実験の原因を、口の外で別の出来事に付けて書くと落ちる(使い回し)。"""
    log, cause = _admitted()
    with pytest.raises(PermissionError, match="CP12"):
        log.append(_event_with(cause))
    assert len(log) == 1


def test_append_rejects_a_forged_experiment_made_without_init():
    """``object.__new__`` と ``type(e).__new__`` で ``__init__`` を飛ばした偽物も、書くときに落ちる。"""
    log, e = _admitted()
    forged = object.__new__(EV.Experiment)
    object.__setattr__(forged, "cond_id", "forged")
    with pytest.raises(PermissionError, match="CP12"):
        log.append(_event_with(forged))
    forged2 = type(e).__new__(type(e))
    object.__setattr__(forged2, "cond_id", "forged2")
    with pytest.raises(PermissionError, match="CP12"):
        log.append(_event_with(forged2))
    assert len(log) == 1


def test_append_gate_check_stays_on_when_the_write_guard_is_off():
    prev = WP.enabled()
    WP.set_enabled(False)
    try:
        log, cause = _admitted()
        with pytest.raises(PermissionError, match="CP12"):
            log.append(_event_with(cause))
    finally:
        WP.set_enabled(prev)
