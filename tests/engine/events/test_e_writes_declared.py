"""第 1 期 1-3 出来事の記録: 書き口は系の宣言 ``writes.paths`` の ``E:events.*`` に載り、宣言の外の書きは落ちる
(口の約束 1-3 の約束 (4))。

- 宣言の凍結: ``E:events.*`` を宣言した系の集合は ``writes_paths_events.json`` と同じ(world・checkpoint・day_close・
  close_final)。状態台帳の行 ``E`` の道筋に当たる(1-0 の D⑧)。SoA の書く列の凍結(``writes_soa_frozen.json``)は
  変えていない(記録は SoA を書かない)。
- 段 C と同じ実行時の検査(既定で入る): 系の宣言から ``E:events.*`` を外すと、その系が記録を書いた所で
  ``PermissionError``。書きの検査の切替口で外せる。
- 段 B(試験のときの全欄の差): 実行時の検査を外して宣言を外すと、系ごとの差の測りが ``E:`` の道筋の変化を宣言の外として
  その系に出す。宣言どおりなら宣言の外 0(記録の道筋の変化は world・checkpoint の宣言の中)。
- ``guard.PATHS_PERMIT`` を書き換えてよいのは ``guard.py`` だけ(AST)。
"""

from __future__ import annotations

import ast
import fnmatch
import json
from pathlib import Path

import pytest

from shibuya.core import write_permit as WP
from shibuya.engine import state_ledger as SL
from shibuya.engine.run import run_day
from shibuya.engine.systems import conductor as CD
from shibuya.engine.systems import guard as G
from shibuya.engine.systems import overrides as OV
from shibuya.engine.systems import probe as PR
from shibuya.engine.systems.table import SPECS, SYSTEMS

HERE = Path(__file__).resolve().parent
SRC = HERE.parents[2] / "src" / "shibuya"
FROZEN = json.loads((HERE / "writes_paths_events.json").read_text(encoding="utf-8"))
KW = dict(n_agents=80, seed=1, n_cells=9, ticks=720, budget=80.0, sleep_suppression=False, vocab_version="v3",
          memory="on", relations="on", rel_copresent="on", store_memory="on", checkpoint_every=60)
#: 差を測る刻み: 7 刻みごと+checkpoint の刻みとその次(最後の系 checkpoint の差は次の刻みの頭で帰属する)。
TICKS = frozenset(range(0, 720, 7)) | frozenset(t for c in range(59, 720, 60) for t in (c, c + 1))


@pytest.fixture(autouse=True)
def _guard_on():
    prev = WP.enabled()
    WP.set_enabled(True)
    yield
    WP.set_enabled(prev)


def test_declaring_systems_match_the_frozen_list():
    pat = FROZEN["pattern"]
    got = [s.name for s in SYSTEMS if pat in s.writes.paths]
    assert got == FROZEN["systems"]
    items = [f"{r.key}:{it}" for r in SL.external_rows() for it in r.items]
    e_items = [k for k in items if fnmatch.fnmatchcase(k, pat)]
    assert e_items and all(k.startswith("E:events.") for k in e_items)
    assert G.EVENTS_PATH in e_items
    # 宣言の外のどの系も E の道筋に当たる型を持たない
    for s in SYSTEMS:
        if s.name not in FROZEN["systems"]:
            assert not any(fnmatch.fnmatchcase(G.EVENTS_PATH, p) for p in s.writes.paths), s.name


def test_events_write_allowed_reads_the_paths_permit():
    with G.system_scope("x", None, None, None, frozenset({"O39:conv.*"})):
        assert not G.events_write_allowed()
    with G.system_scope("x", None, None, None, frozenset({"E:events.*"})):
        assert G.events_write_allowed()
    assert G.events_write_allowed()  # 系の外は制限なし
    WP.set_enabled(False)
    with G.system_scope("x", None, None, None, frozenset({"O39:conv.*"})):
        assert G.events_write_allowed()  # 切替口で外せる(段 C と同じ)


@pytest.mark.parametrize("system", ["checkpoint", "world"])
def test_undeclared_write_fails_at_run_time(system):
    with OV.drop_path(system, "E:events.*"):
        with pytest.raises(PermissionError, match=f"系 {system} は出来事の記録"):
            run_day(**KW)


def test_undeclared_write_shows_in_stage_b():
    WP.set_enabled(False)  # 実行時の検査を外して、段 B だけで見る
    pr = PR.Probe(check=None, ticks=TICKS)
    PR.ACTIVE = pr
    try:
        with OV.drop_path("checkpoint", "E:events.*"):
            pr.check = CD.declared_check(SPECS)
            run_day(**KW)
    finally:
        PR.ACTIVE = None
    bad = [(t, s, k) for t, s, k in pr.violations if k.startswith("E:")]
    assert bad and all(s == "checkpoint" for _t, s, _k in bad), pr.violations[:5]


def test_declared_writes_cover_the_event_changes():
    pr = PR.Probe(check=CD.declared_check(SPECS), ticks=TICKS)
    PR.ACTIVE = pr
    try:
        run_day(**KW)
    finally:
        PR.ACTIVE = None
    assert pr.n_snap > 0 and not pr.violations, pr.violations[:10]
    writers = {s for _t, s, _d, keys in pr.entries if any(k.startswith("E:") for k in keys)}
    assert {"checkpoint"} <= writers <= set(FROZEN["systems"]) | {CD.TICK_HEAD, "close_final", "report", "END"}


def test_paths_permit_is_assigned_only_in_the_guard():
    bad = []
    for fp in sorted(SRC.rglob("*.py")):
        rel = fp.relative_to(SRC).as_posix()
        if rel == "engine/systems/guard.py":
            continue
        for n in ast.walk(ast.parse(fp.read_text(encoding="utf-8"))):
            tgts = n.targets if isinstance(n, ast.Assign) else [n.target] if isinstance(n, (ast.AugAssign,
                                                                                            ast.AnnAssign)) else []
            for t in tgts:
                for x in ast.walk(t):
                    if (isinstance(x, ast.Attribute) and x.attr == "PATHS_PERMIT") or (
                            isinstance(x, ast.Name) and x.id == "PATHS_PERMIT"):
                        bad.append(f"{rel}:{n.lineno}")
    assert bad == [], bad
