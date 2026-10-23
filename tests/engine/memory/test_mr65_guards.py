"""第 6 期 6-5 の守り(書く口は器の中だけ・付け替えの守り・層の契約・宣言の表)。

- M1 の状態(``M1State``)の書く口(``place``・``clear``・``seed_rows``・``grow``)と意味の手がかりの状態(``CueState``)の書く口
  (``note_heard``・``note_own``・``embed_rows``・``drop_rows``・``remap``・``rebuild``)を呼ぶのは記憶の器
  (``engine/memory_store.py`` の ``MemoryStore``)だけ(src の AST)。負の対照: 外から呼ぶ行を足した写しで見つかる。
- 子の持ち主の中身の列は持ち主の中でだけ書く(``_t_ns``・``_heard`` などへの代入は src の他のファイルに無い)。
- 状態台帳: 腕の行 M0M(behavior・required・腕 memory-model)・M0C(behavior・required・腕 memory-cue・埋め込みは
  hash_skip)・計数の行 M0X(diag・discardable)。持ち主のクラスと除外の網羅(合成の世界の腕のランの実行時)。
- 6-5 のモジュールは層の契約の中(engine から perception・llm を import しない)。
- 〔検収 M4〕店の行の表(``ShopTable``)の書く口(``put``・``grow``・``note_evicted``)を呼ぶのは ``engine/memory_shops.py``
  (``UncappedStoreMemory`` の行の口)だけ・列(``_poi``・``_valence``・``_precision``・``_source``)への代入は表の中だけ。
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from shibuya.engine import state_ledger as SL
from shibuya.engine import state_ledger_ast as SA
from shibuya.engine.run import run_day

from tests.engine.memory._mr65 import KW, arms

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src" / "shibuya"
M1_PORTS = {"place", "clear", "seed_rows", "grow"}
CUE_PORTS = {"note_heard", "note_own", "embed_rows", "drop_rows", "remap"}
MODULES = ("memory_m1", "memory_embed", "memory_impression", "memory_trace", "relations_people", "memory_shops")
SHOP_PORTS = {"put", "grow", "note_evicted"}


def _port_calls(root: Path) -> list[tuple[str, str, str]]:
    """``<何か>.m1.<口>(...)``・``<何か>.cue.<口>(...)`` の呼び出し(ファイル・受け手・口)。"""
    out = []
    for p in sorted(root.rglob("*.py")):
        tree = ast.parse(p.read_text(encoding="utf-8"))
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
                recv = n.func.value
                if isinstance(recv, ast.Attribute) and recv.attr in ("m1", "cue"):
                    ports = M1_PORTS if recv.attr == "m1" else CUE_PORTS | {"rebuild"}
                    if n.func.attr in ports:
                        out.append((p.relative_to(root).as_posix(), recv.attr, n.func.attr))
    return out


def test_child_owner_ports_are_called_only_from_the_store():
    calls = _port_calls(SRC)
    assert calls and {f for f, _r, _p in calls} == {"engine/memory_store.py"}, calls


def test_negative_control_finds_an_outside_call(tmp_path):
    root = tmp_path / "shibuya"
    (root / "engine").mkdir(parents=True)
    (root / "engine" / "x.py").write_text("def f(ms):\n    ms.m1.place([0], [True], 1)\n    ms.cue.note_own(0, 'x')\n",
                                          encoding="utf-8")
    assert sorted(_port_calls(root)) == [("engine/x.py", "cue", "note_own"), ("engine/x.py", "m1", "place")]


def test_child_columns_are_assigned_only_inside_their_classes():
    targets = {"_t_ns", "_scale", "_heard", "_own", "_vec", "_qcache"}
    bad = []
    for p in sorted(SRC.rglob("*.py")):
        rel = p.relative_to(SRC).as_posix()
        if rel in ("engine/memory_m1.py", "engine/memory_embed.py"):
            continue
        for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            tgs = n.targets if isinstance(n, ast.Assign) else [n.target] if isinstance(n, (ast.AugAssign,
                                                                                            ast.AnnAssign)) else []
            for t in tgs:
                base = t.value if isinstance(t, ast.Subscript) else t
                if isinstance(base, ast.Attribute) and base.attr in targets:
                    bad.append((rel, n.lineno, base.attr))
    assert bad == []


def _shop_port_calls(root: Path) -> list[tuple[str, str, str]]:
    """店の行の表の書く口の呼び出し(受け手の名が ``_tab``・``tab``・``table``・``shops``)。"""
    out = []
    for p in sorted(root.rglob("*.py")):
        for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in SHOP_PORTS:
                recv = n.func.value
                name = recv.attr if isinstance(recv, ast.Attribute) else recv.id if isinstance(recv, ast.Name) else ""
                if name in ("_tab", "tab", "table", "shops"):
                    out.append((p.relative_to(root).as_posix(), name, n.func.attr))
    return out


def test_shop_table_ports_are_called_only_from_the_uncapped_store(tmp_path):
    calls = _shop_port_calls(SRC)
    assert calls and {f for f, _r, _p in calls} == {"engine/memory_shops.py"}, calls
    # 負の対照: 外から呼ぶ行を足した写しで見つかる
    root = tmp_path / "shibuya"
    (root / "engine").mkdir(parents=True)
    (root / "engine" / "x.py").write_text("def f(ms):\n    ms.shops.grow()\n", encoding="utf-8")
    assert _shop_port_calls(root) == [("engine/x.py", "shops", "grow")]
    bad = []
    for p in sorted(SRC.rglob("*.py")):
        rel = p.relative_to(SRC).as_posix()
        if rel == "engine/memory_shops.py":
            continue
        for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            tgs = n.targets if isinstance(n, ast.Assign) else [n.target] if isinstance(n, ast.AugAssign) else []
            for t in tgs:
                base = t.value if isinstance(t, ast.Subscript) else t
                if isinstance(base, ast.Attribute) and base.attr in ("_poi", "_valence", "_precision", "_source"):
                    bad.append((rel, n.lineno, base.attr))
    assert bad == []


def test_ledger_rows_and_axes():
    assert (SL.row("M0M").behavior, SL.row("M0M").restore, SL.row("M0M").arm) == (SL.BEHAVIOR, SL.REQUIRED,
                                                                                   "memory-model")
    assert (SL.row("M0C").behavior, SL.row("M0C").restore, SL.row("M0C").arm) == (SL.BEHAVIOR, SL.REQUIRED,
                                                                                   "memory-cue")
    assert set(SL.row("M0C").hash_skip) == {"mem_layer.memory_store.cue._vec", "mem_layer.memory_store.cue._qcache"}
    assert (SL.row("M0X").behavior, SL.row("M0X").restore, SL.row("M0X").arm) == (SL.DIAG, SL.DISCARDABLE, "")
    assert SL.OWNER_CLASSES["mem_layer.memory_store.m1"] == ("engine/memory_m1.py", "M1State")
    assert SL.OWNER_CLASSES["mem_layer.memory_store.cue"] == ("engine/memory_embed.py", "CueState")
    # 〔検収 M4〕店の行の表(腕の行 M0S=腕 memory-people)と店の記憶の子クラス
    assert (SL.row("M0S").behavior, SL.row("M0S").restore, SL.row("M0S").arm) == (SL.BEHAVIOR, SL.REQUIRED,
                                                                                   "memory-people")
    assert SL.row("M0S").arm_owner == "mem_layer.memory_store.shops"
    assert SL.OWNER_CLASSES["mem_layer.memory_store.shops"] == ("engine/memory_shops.py", "ShopTable")
    assert ("engine/memory_shops.py", "UncappedStoreMemory") in SL.OWNER_ALT_CLASSES["mem_layer.store"]
    assert "mem_layer.memory_store.shops._shop_stats" in SL.row("M0X").items


@pytest.mark.parametrize("kw", [dict(model="m1"), dict(cue="embed", embed_model="ngram-test"),
                                dict(model="m1", people="memory", rows0=8), dict(grain="day")])
def test_runtime_owners_of_the_arm_runs_are_fully_declared(monkeypatch, kw):
    from tests.engine.test_state_ledger_10b import _spy_hash_inputs

    mp = pytest.MonkeyPatch()
    try:
        with arms("events", **kw):
            with _spy_hash_inputs(mp) as seen:
                run_day(**dict(KW, ticks=240))
        owners = seen[-1]["owners"]
    finally:
        mp.undo()
    assert SA.runtime_uncovered(owners) == {}


def test_new_modules_respect_the_layer_contract():
    for m in MODULES:
        tree = ast.parse((SRC / "engine" / f"{m}.py").read_text(encoding="utf-8"))
        imported = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom) and n.module:
                imported.add(n.module)
            elif isinstance(n, ast.Import):
                imported |= {a.name for a in n.names}
        assert not any(x.startswith(("shibuya.perception", "shibuya.llm", "shibuya.cli")) for x in imported), (m, imported)
