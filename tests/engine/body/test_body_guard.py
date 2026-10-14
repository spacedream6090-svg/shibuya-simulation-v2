"""第 3 期 3-5: 体の層の守り(書く口は ``step``・``initial`` だけ・新しい書き手を作らない・持ち主の欄の守り)。

- 持ち主 ``BodyModel`` の欄は組み立ての 1 回だけ置ける(``__setattr__``・``__delattr__`` が断る)。
- 体の層の中身(``_reservations``=``BodySchedule`` の欄・``_body_meter``)を書くのは ``BodyModel`` の口(``__init__``・``initial``・``step``
  と下請け)と ``BodySchedule`` の書く口だけ。``BodySchedule`` の書く口を呼ぶのは ``BodyModel`` の口だけ(AST・負の対照つき)。
- ``body.step(...)``・``body.initial(...)`` を呼ぶのは ``engine/resolve.py``(``advance_body``・``initialize``・
  ``initialize_energy``)と ``engine/processes/environment.py``(``EnvironmentProcess.step``)だけ。
- SoA の体の欄(空腹・疲れ・暑さ・段・食後の消費・収支)を書く resolve の関数の集合と、その口の呼び手の数は HEAD と同じ
  (新しい書き手を作らない・呼び手は減るか同じ)。
"""

from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pytest

from shibuya.engine.body import BodyModel
from shibuya.engine.systems import allow as AL

from tests.engine.ast_writers import UNKNOWN, scan_writes

SRC = Path(__file__).resolve().parents[3] / "src" / "shibuya"
MODEL, SCHED = "engine/body/model.py", "engine/body/schedule.py"
#: 体の層の中身の欄(持ち主の 2 つ+予約の列の欄)。
COLS = frozenset({"_reservations", "_body_meter", "intero", "intero_seq", "intero_at", "intero_snap", "intero_primed", "felt",
                  "felt_seq", "felt_at", "felt_col", "felt_table", "felt_next", "felt_serial"})
#: 中身を書いてよい関数(持ち主の口と下請け・予約の列の書く口)。
ALLOWED = frozenset({
    f"{MODEL}:BodyModel.{m}" for m in ("__init__", "initial", "step", "_step_intero", "_reserve_intero", "_step_felt",
                                        "_note", "__setattr__", "__delattr__")} | {
    f"{SCHED}:BodySchedule.{m}" for m in ("reset", "intero_due", "intero_plan", "intero_snapshot", "felt_due",
                                           "felt_new_table", "felt_plan", "__setattr__", "__post_init__")})
#: 予約の列の書く口(呼んでよいのは持ち主の口だけ)。
SCHED_PORTS = frozenset({"reset", "intero_due", "intero_plan", "intero_snapshot", "felt_due", "felt_new_table",
                         "felt_plan"})
PORT_CALLERS = frozenset({f"{MODEL}:BodyModel.{m}" for m in ("__init__", "initial", "_reserve_intero", "_step_felt")})
#: 同じ名の欄を持つ別の持ち主(体の層の対象の外): 予約の列の道具そのもの。持ち主の欄の名 ``_reservations``・``_body_meter``
#: はほかの持ち主と重ならない名にした(10f の外の状態の軸 1 の AST の検査の名の衝突を避ける)。
OTHER_OWNERS = frozenset({"engine/scheduler.py"})
MUTATORS = frozenset({"setdefault", "append", "pop", "popitem", "clear", "update", "extend", "insert", "remove"})


def _rel(p: Path) -> str:
    return p.relative_to(SRC).as_posix()


def _writes(rel: str, text: str) -> list[str]:
    if rel in OTHER_OWNERS:
        return []
    bad = []
    for w in scan_writes(text, lambda n: n in COLS):
        if w.name == UNKNOWN and not rel.startswith("engine/body/"):
            continue
        if f"{rel}:{w.func}" not in ALLOWED:
            bad.append(f"{rel}:{w.line} [{w.func}] {w.kind} {w.name} ({w.form})")
    return bad


class _Calls(ast.NodeVisitor):
    def __init__(self) -> None:
        self.stack: list[str] = []
        self.out: list[tuple[str, str, str, int]] = []  # (関数, 口, 受け手の式, 行)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]

    def visit_Call(self, node: ast.Call) -> None:
        f = node.func
        if isinstance(f, ast.Attribute):
            self.out.append((".".join(self.stack[:2]) or "<module>", f.attr, ast.unparse(f.value), node.lineno))
        self.generic_visit(node)


def _calls(text: str) -> list[tuple[str, str, str, int]]:
    v = _Calls()
    v.visit(ast.parse(text))
    return v.out


def _scan_ports(files: dict[str, str]) -> tuple[list[str], list[str], list[str]]:
    """(予約の列の書く口の外の呼び手, 体の層の step/initial の呼び手, 中身の外の書き・変えるメソッド)。"""
    sched_bad, body_calls, writes = [], [], []
    for rel, text in files.items():
        writes += _writes(rel, text)
        for func, port, recv, line in _calls(text):
            if port in SCHED_PORTS and ("_reservations" in recv or "plan" == recv) and f"{rel}:{func}" not in PORT_CALLERS:
                sched_bad.append(f"{rel}:{line} [{func}] {recv}.{port}")
            if port in ("step", "initial") and "body" in recv.lower():
                body_calls.append(f"{rel}:{func}:{port}")
            if port in MUTATORS and recv.split(".")[-1] in COLS and not rel.startswith("engine/body/"):
                writes.append(f"{rel}:{line} [{func}] method {recv}.{port}")
    return sched_bad, body_calls, writes


def _src_files() -> dict[str, str]:
    return {_rel(p): p.read_text(encoding="utf-8") for p in sorted(SRC.rglob("*.py"))}


def test_only_the_ports_write_the_body_layer():
    sched_bad, body_calls, writes = _scan_ports(_src_files())
    assert writes == [], writes
    assert sched_bad == [], sched_bad
    assert sorted(set(body_calls)) == sorted({
        "engine/resolve.py:advance_body:step", "engine/resolve.py:initialize:initial",
        "engine/resolve.py:initialize_energy:initial", "engine/processes/environment.py:EnvironmentProcess.step:step",
    }), body_calls


def test_negative_planted_writes_and_calls_are_found():
    """負の対照: 体の層の外から中身を書く・予約の列の書く口を呼ぶ・step を呼ぶ行を植えると見つかる。"""
    planted = {
        "engine/presence.py": (
            "def f(body, layers):\n"
            "    body._body_meter['steps'] = 0\n"
            "    layers.body._reservations.intero_plan(0, [], [])\n"
            "    layers.body.step('interoception', None, 0)\n"
            "    body._reservations.intero_snap.clear()\n"
        ),
        MODEL: "class BodyModel:\n    def observed(self):\n        self._body_meter['x'] = 1\n",
    }
    sched_bad, body_calls, writes = _scan_ports(planted)
    assert any("presence.py:2" in w for w in writes) and any("model.py:3" in w for w in writes)
    assert any("method body._reservations.intero_snap.clear" in w for w in writes)
    assert any("intero_plan" in s for s in sched_bad)
    assert "engine/presence.py:f:step" in body_calls


def test_the_owner_refuses_rebinding_and_deleting():
    bm = BodyModel(3)
    for name in ("arm", "n", "_reservations", "_body_meter", "step_seconds", "gauge"):
        with pytest.raises(AttributeError, match="付け替えられない"):
            setattr(bm, name, None)
        with pytest.raises(AttributeError, match="消せない"):
            delattr(bm, name)
    with pytest.raises(AttributeError):
        bm.new_field = 1  # __slots__ の外
    view = bm.meter_view
    with pytest.raises(TypeError):
        view["steps"] = 1  # type: ignore[index]
    with pytest.raises(ValueError):
        BodyModel(3, arm="lazy")
    with pytest.raises(ValueError):
        bm.step("thermal", None, 0)


#: HEAD(3-5 より前)の resolve の体の欄の書き手(``allow.index`` の直接の書き・記録 bd35/README.md §6)。
HEAD_WRITERS = {
    "_apply_rest": ["agents.fatigue"],
    "_complete_buy": ["agents.hunger"],
    "_complete_eat": ["agents.hunger"],
    "_energy_meal": ["agents.energy_balance", "agents.hunger", "agents.since_meal_kcal"],
    "_energy_snack": ["agents.energy_balance", "agents.hunger", "agents.since_meal_kcal"],
    "advance_body": ["agents.energy_balance", "agents.fatigue", "agents.hunger", "agents.since_meal_kcal"],
    "apply_detection": ["agents.fatigue_stage", "agents.hunger_stage", "agents.thermal_stage"],
    "energy_home_meal": ["agents.hunger_stage"],
    "initialize": ["agents.fatigue", "agents.hunger", "agents.thermal"],
    "initialize_energy": ["agents.energy_balance", "agents.hunger", "agents.hunger_stage", "agents.since_meal_kcal"],
    "set_thermal": ["agents.thermal"],
}
BODY_COLS = frozenset(c for v in HEAD_WRITERS.values() for c in v) | {"agents.fatigue_stage", "agents.thermal_stage"}


def test_no_new_writer_of_the_body_columns():
    ix = AL.index()
    got = {f: sorted(v & BODY_COLS) for f, v in ix.direct.items() if v & BODY_COLS}
    assert got == HEAD_WRITERS


#: HEAD の口の呼び手(src の中・``R.<口>(...)``)。
HEAD_CALLERS = sorted([
    ("engine/processes/environment.py", "set_thermal"), ("engine/processes/environment.py", "set_thermal"),
    ("engine/systems/body.py", "advance_body"), ("engine/systems/build.py", "initialize"),
    ("engine/systems/build.py", "initialize_energy"),
])


def test_callers_of_the_body_write_ports_are_not_more_than_head():
    got = []
    for rel, text in _src_files().items():
        for _func, port, recv, _line in _calls(text):
            if port in ("advance_body", "set_thermal", "initialize", "initialize_energy") and recv in ("R", "resolve"):
                got.append((rel, port))
    assert sorted(got) == HEAD_CALLERS  # 呼び手は減るか同じ(3-5 は同じ数)


def test_the_body_layer_holds_copies_not_soa_views():
    """写し(引き直しの検出)は SoA の配列のビューを持たない(D ⑥ と同じ約束)。"""
    from shibuya.agents.state import AgentState

    a = AgentState(6)
    bm = BodyModel(6, arm="reserve")
    r = a.registry
    bm.step("interoception", r, 0)
    snap = bm._reservations.intero_snap  # noqa: SLF001 - 試験だけ読む
    assert set(snap) == {"act", "f", "h"}
    for k, col in (("act", "activity"), ("f", "fatigue"), ("h", "hunger")):
        assert not np.shares_memory(snap[k], getattr(r, col)), k


def test_sweep_allocates_no_per_agent_arrays_and_reserve_does():
    """〔3-5 検収 M1〕腕 sweep(既定)は体ごとの予約の配列を作らない(状態台帳の行 BD の「腕 sweep: 計器だけ」)。"""
    sw, rs = BodyModel(1_000, arm="sweep"), BodyModel(1_000, arm="reserve")
    for bm, size in ((sw, 0), (rs, 1_000)):
        plan = bm._reservations  # noqa: SLF001 - 試験だけ読む
        for name in ("intero_seq", "intero_at", "felt_seq", "felt_at", "felt_col"):
            assert getattr(plan, name).size == size, (bm.arm, name)
        bm.initial(1_000)  # 刻み 0 で空に戻しても同じ
        assert plan.intero_seq.size == size and plan.felt_col.size == size
    assert sw.reserved_steps().size == 0 and sw.observed()["pending"] == {"interoception": 0, "felt": 0}


def test_the_schedule_refuses_writes_outside_its_ports():
    """〔3-5 検収 L7〕予約の列の欄は書く口の外で付け替え・消去・配列の書きを断る(負の対照=書く口の中は書ける)。"""
    from shibuya.agents.state import AgentState

    bm = BodyModel(5, arm="reserve")
    plan = bm._reservations  # noqa: SLF001 - 試験だけ読む
    with pytest.raises(AttributeError, match="付け替えられない"):
        plan.felt_serial = 3
    with pytest.raises(AttributeError, match="消せない"):
        del plan.intero
    with pytest.raises(ValueError):
        plan.intero_seq[0] = 7  # 読み取り専用
    with pytest.raises(ValueError):
        plan.felt_col[:] = 1
    # 書く口の中は書ける(口を通した後は閉じる)
    assert plan.intero_plan(0, np.array([1, 2]), np.array([30, 40])) == 2
    assert list(bm.reserved_steps()) == [-1, 30, 40, -1, -1]
    assert not plan.intero_seq.flags.writeable and plan.__dict__["_port_active"] is False
    r = AgentState(5).registry
    bm.step("interoception", r, 0)
    assert all(not a.flags.writeable for a in plan.intero_snap.values())
    with pytest.raises(ValueError):
        plan.intero_snap["f"][0] = 1
