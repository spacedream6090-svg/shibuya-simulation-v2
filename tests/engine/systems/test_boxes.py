"""1-0 段 C: 状態の箱・局所の割り当ての表(漏れ 0)・scratch の番兵(T4)と書きの宣言(段 C)・持ち主の名と順。"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from shibuya.core import write_permit as WP
from shibuya.engine.systems import boxes as BX
from shibuya.engine.systems import guard as G

TABLE = Path("docs/bench/analysis/wallbounce-1012/run-day-decomp/local-assignment.json")
BOX_CLASSES = {
    "cfg": BX.RunConfig, "soa": BX.SoAState, "layers": BX.Layers, "llm": BX.LlmIo, "day": BX.DayTables,
    "buffers": BX.Buffers, "scratch": BX.TickScratch, "stats": BX.RunStats, "fx": BX.Fixtures,
}
#: 表の箱の名 → ``Box`` の属性の名(``stats`` は名の衝突を避けて ``runstats``)。
BOX_ATTR = {"stats": "runstats"}
#: 表の欄の名 → 箱の欄の名(名の衝突を避けて変えたもの)。
FIELD_RENAMES = {("stats", "sleep_counts"): "sleep_tally"}


def _fields(cls) -> set[str]:
    if cls is BX.TickScratch:
        return set(BX.SCRATCH_FIELDS)
    names = {f.name for f in dataclasses.fields(cls)}
    names |= {n for n, v in vars(cls).items() if isinstance(v, property)}
    return names


def test_every_local_of_run_day_is_assigned():
    """段 C の門(草案 §2-3〔改訂 K8〕): HEAD の run_day の局所 450 個に割り当て無しが 0。"""
    doc = json.loads(TABLE.read_text(encoding="utf-8"))
    assert doc["n_locals"] == 450 and doc["unassigned"] == []
    assert all(r["to"] for r in doc["locals"].values())


def test_box_targets_exist():
    doc = json.loads(TABLE.read_text(encoding="utf-8"))
    missing = []
    for name, r in doc["locals"].items():
        to = r["to"]
        if not to.startswith("box:"):
            continue
        box, fld = to[4:].split(".", 1)
        fld = fld.split("(")[0]
        fld = FIELD_RENAMES.get((box, fld), fld)
        if fld not in _fields(BOX_CLASSES[box]):
            missing.append(f"{name} → {to}")
    assert not missing, missing
    assert {f.name for f in dataclasses.fields(BX.Box)} == {BOX_ATTR.get(k, k) for k in BOX_CLASSES}


def test_scratch_fields_cover_the_table():
    doc = json.loads(TABLE.read_text(encoding="utf-8"))
    sc = {r["to"][len("box:scratch."):] for r in doc["locals"].values() if r["to"].startswith("box:scratch.")}
    assert sc == set(BX.SCRATCH_FIELDS)


def test_owner_names_match_the_hash_owners():
    from shibuya.engine.systems import state_io as SIO

    layers = BX.Layers(**{f.name: None for f in dataclasses.fields(BX.Layers)})
    layers.bridge = type("B", (), {"undefined": "U"})()
    io = BX.LlmIo(pending=[], fleet_deferred=[], fleet_waiting=set(), fleet_inflight={}, replay_inbox={})

    class _B:
        pass

    b = _B()
    b.layers, b.llm = layers, io
    owners = SIO.hash_owners(b)
    assert tuple(owners) == BX.OWNER_NAMES
    assert owners["undefined"] == "U"
    assert type(owners["run_day"]).__module__ == "shibuya.engine.run"  # 持ち主のクラスの置き場を変えない
    assert type(owners["run_day"]).__qualname__ == "_RunDayLocals"


# ================================================================= TickScratch(番兵 T4・書きの宣言 段 C)
def test_strict_scratch_raises_on_read_before_write():
    sc = BX.TickScratchStrict()
    sc.reset(BX.UNSET)
    with pytest.raises(AttributeError):
        _ = sc.decision
    sc.decision = 3
    assert sc.decision == 3


def test_scratch_write_outside_the_declaration_fails():
    sc = BX.TickScratch()
    prev = WP.enabled()
    WP.set_enabled(True)
    try:
        with G.system_scope("phase_b", frozenset(), frozenset({"plan"})):
            sc.plan = 1
            with pytest.raises(AttributeError):
                sc.outcome = 2  # 負の対照(T2・段 C): 宣言の外の欄
        sc.outcome = 2  # 系の外は制限なし
        WP.set_enabled(False)
        with G.system_scope("phase_b", frozenset(), frozenset({"plan"})):
            sc.outcome = 3  # 切替口で外すと検査しない
    finally:
        WP.set_enabled(prev)


def test_scratch_reset_keeps_buffers():
    """R1: ``focus_request`` は scratch でなく ``Buffers``(tick の頭で空にしない)。"""
    assert "focus_request" not in BX.SCRATCH_FIELDS
    assert "focus_request" in {f.name for f in dataclasses.fields(BX.Buffers)}


def test_tick_ctx():
    c = BX.TickCtx.of(1441, 1440)
    assert (c.T, c.td, c.day) == (1441, 1, 1)


def test_run_day_signature_is_unchanged_and_build_unpacks_every_argument():
    """草案 §3-3 の 3: 設定の指紋 ``_call_args = dict(locals())`` は run_day の頭のまま。組み立ては引数を全部結ぶ。"""
    import ast
    import inspect

    from shibuya.engine import run as RUN

    params = list(inspect.signature(RUN.run_day).parameters)
    assert len(params) == 113
    src = inspect.getsource(RUN.run_day)
    body = ast.parse(src).body[0].body
    first = body[1] if isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) else body[0]
    assert ast.unparse(first) == "_call_args = dict(locals())"
    bsrc = Path("src/shibuya/engine/systems/build.py").read_text(encoding="utf-8")
    import re

    got = re.findall(r"^    (\w+) = _call_args\['(\w+)'\]$", bsrc, flags=re.M)
    assert [a for a, _ in got] == [b for _, b in got] == params
