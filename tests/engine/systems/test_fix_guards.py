"""1-0 段 FIX(検収 review-impl-1-0.md §1 の 1〜10): 「宣言の外を書いたら落ちる」の穴を塞いだ検査と負の対照。

- 3: 書きの許可を外す口(``write_permit.scope``・``set_enabled``・``guard.system_scope``・許可の大域の書き換え)は決まった
  置き場からしか呼べない(静的・負の対照つき)。
- 5: D⑥ の別名の形を広げた(``registry.arrays["x"]``・``getattr``・``field(変数)``・局所の別名・組・辞書)。
- 10: D② を本物の検査にした(凍結した書く列の表と、いまの閉包が食い違えば落ちる)。
- 1・2・4・6・7・8 の負の対照は ``test_add_at_guard.py``・``test_guard_runs.py``・``test_systems_table.py`` と下。
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

from shibuya.engine import state_ledger_ast as A
from shibuya.engine.systems import allow as AL
from shibuya.engine.systems import static_check as SC
from shibuya.engine.systems.table import SPECS, SYSTEMS

SRC = Path("src/shibuya")
HERE = Path(__file__).resolve().parent

# ================================================================= 3: 書きの許可を外す口
STATE_MODULES = {"agents/state.py", "world/state.py", "perception/state.py"}
#: write_permit の関数 → 呼んでよい置き場(試験と記録の道具は src の外=ここに出ない)。
WP_CALLS = {"allows": STATE_MODULES, "scope": {"engine/systems/guard.py"}, "enabled": {"engine/systems/guard.py"},
            "set_enabled": set(), "current": set()}
WP_IMPORTERS = STATE_MODULES | {"engine/systems/guard.py", "core/write_permit.py"}
#: guard の口 → 呼んでよい置き場。
GUARD_CALLS = {"system_scope": {"engine/systems/conductor.py"}}
#: 書き換えてはいけない許可の大域(その置き場の外で代入しない)。
PERMIT_GLOBALS = {"_PERMIT": "core/write_permit.py", "_ENABLED": "core/write_permit.py",
                  "SCRATCH_PERMIT": "engine/systems/guard.py", "BUFFERS_PERMIT": "engine/systems/guard.py",
                  "CURRENT": "engine/systems/guard.py"}


def permit_offenders(rel: str, tree: ast.AST) -> list[str]:
    out: list[str] = []
    wp_alias, wp_direct, g_alias, g_direct = set(), {}, set(), {}
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom):
            for a in n.names:
                if n.module == "shibuya.core" and a.name == "write_permit":
                    wp_alias.add(a.asname or a.name)
                elif n.module == "shibuya.core.write_permit":
                    wp_direct[a.asname or a.name] = a.name
                elif n.module == "shibuya.engine.systems" and a.name == "guard":
                    g_alias.add(a.asname or a.name)
                elif n.module == "shibuya.engine.systems.guard":
                    g_direct[a.asname or a.name] = a.name
        elif isinstance(n, ast.Import):
            for a in n.names:
                if a.name == "shibuya.core.write_permit":
                    wp_alias.add(a.asname or a.name)
                if a.name == "shibuya.engine.systems.guard":
                    g_alias.add(a.asname or a.name)
    if (wp_alias or wp_direct) and rel not in WP_IMPORTERS:
        out.append(f"{rel}: write_permit を import してよい置き場の外")
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            fname = None
            if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id in wp_alias:
                fname = ("wp", f.attr)
            elif isinstance(f, ast.Name) and f.id in wp_direct:
                fname = ("wp", wp_direct[f.id])
            elif isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id in g_alias:
                fname = ("g", f.attr)
            elif isinstance(f, ast.Name) and f.id in g_direct:
                fname = ("g", g_direct[f.id])
            if fname is not None:
                table = WP_CALLS if fname[0] == "wp" else GUARD_CALLS
                if fname[1] in table and rel not in table[fname[1]]:
                    out.append(f"{rel}:{n.lineno}: {fname[1]} を呼んでよい置き場の外")
        tgts = (n.targets if isinstance(n, ast.Assign) else [n.target] if isinstance(n, (ast.AugAssign, ast.AnnAssign))
                else [])
        for t in tgts:
            for x in ast.walk(t):
                name = x.attr if isinstance(x, ast.Attribute) else None
                if name in PERMIT_GLOBALS and PERMIT_GLOBALS[name] != rel:
                    out.append(f"{rel}:{n.lineno}: 許可の大域 {name} を書き換える")
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "setattr" and len(n.args) >= 2 \
                and isinstance(n.args[1], ast.Constant) and n.args[1].value in PERMIT_GLOBALS \
                and PERMIT_GLOBALS[n.args[1].value] != rel:
            out.append(f"{rel}:{n.lineno}: 許可の大域 {n.args[1].value} を setattr で書き換える")
    return out


def test_permit_switches_are_called_only_from_known_places():
    offenders = []
    for fp in A.source_files(SRC):
        rel = fp.relative_to(SRC).as_posix()
        offenders += permit_offenders(rel, ast.parse(fp.read_text(encoding="utf-8")))
    assert not offenders, offenders


def test_permit_check_catches_planted_switches():
    """負の対照(検収 L2・L11): 系と層から許可を外す口を呼ぶ・大域を書き換えると見つかる。"""
    planted = ast.parse(
        "from shibuya.core import write_permit as WP\n"
        "from shibuya.core.write_permit import set_enabled\n"
        "from shibuya.engine.systems import guard as G\n"
        "def sys_x(ctx, b):\n"
        "    with WP.scope(None):\n        pass\n"
        "    set_enabled(False)\n"
        "    with G.system_scope('x', None, None):\n        pass\n"
        "    G.SCRATCH_PERMIT = None\n"
        "    WP._PERMIT = None\n")
    got = permit_offenders("engine/systems/fake.py", planted)
    assert any("import してよい" in x for x in got)
    for word in ("scope", "set_enabled", "system_scope", "SCRATCH_PERMIT", "_PERMIT"):
        assert any(word in x for x in got), (word, got)


# ================================================================= 5: D⑥ の別名の形を広げる
_SOA_TAILS = {"registry", "agents", "cells", "pois", "pstate"}
_EXEMPT_D6 = {"agents/state.py", "world/state.py", "perception/state.py", "engine/resolve.py", "core/soa.py"}
D6_ALLOW = {
    ("engine/intent.py", "self._poi_cell"): "POI のセル(静的な列)を int64 の写しで持つ(dtype が違う=写し・凍結の後)",
    ("engine/store_choice.py", "self.poi_cell"): "同上",
    ("engine/store_choice.py", "self.price"): "POI の値段(静的な列)の int64 の写し",
    ("engine/processes/civic.py", "self.bed_cell[got]"):
        "層の ndarray の要素への代入(値の写し=別名にならない。AST では的が配列か辞書か分からないので見つける側)",
}
_UNWRAP_CALLS = {"asarray", "asanyarray", "ascontiguousarray"}
_UNWRAP_METHODS = {"view", "reshape", "ravel"}


def _tail(expr: ast.AST) -> str:
    if isinstance(expr, ast.Attribute):
        return expr.attr
    if isinstance(expr, ast.Name):
        return expr.id
    return ""


def _root(expr: ast.AST) -> str:
    while isinstance(expr, (ast.Attribute, ast.Subscript, ast.Call)):
        expr = expr.func if isinstance(expr, ast.Call) else expr.value
    return expr.id if isinstance(expr, ast.Name) else ""


def soa_ish(v: ast.AST, names: set[str], aliases: set[str]) -> bool:
    """式が SoA の配列・ビュー・登録表を指すか(別名 ``aliases`` は局所の名)。"""
    if isinstance(v, (ast.Tuple, ast.List, ast.Set)):
        return any(soa_ish(e, names, aliases) for e in v.elts)
    if isinstance(v, ast.Dict):
        return any(soa_ish(e, names, aliases) for e in v.values if e is not None)
    while True:
        if isinstance(v, ast.Subscript):
            if isinstance(v.value, ast.Attribute) and v.value.attr == "arrays":  # registry.arrays["x"]
                return True
            v = v.value
            continue
        if isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute):
            if v.func.attr in _UNWRAP_CALLS and v.args:
                v = v.args[0]
                continue
            if v.func.attr in _UNWRAP_METHODS:
                v = v.func.value
                continue
            if v.func.attr == "field":  # registry.field(…)(定数でも変数でも)
                return True
        break
    if isinstance(v, ast.Call) and isinstance(v.func, ast.Name) and v.func.id == "getattr" and v.args:
        b = v.args[0]
        return _tail(b) in _SOA_TAILS or _root(b) in aliases
    if isinstance(v, ast.Attribute) and v.attr in names:
        return _tail(v.value) in _SOA_TAILS or _root(v.value) in aliases
    if isinstance(v, ast.Attribute) and v.attr in ("registry", "arrays") :
        return _tail(v.value) in _SOA_TAILS or _root(v.value) in aliases
    if isinstance(v, ast.Name):
        return v.id in aliases
    return False


def _local_aliases(fn: ast.AST, names: set[str]) -> set[str]:
    aliases: set[str] = set()
    changed = True
    while changed:
        changed = False
        for n in ast.walk(fn):
            if not isinstance(n, ast.Assign):
                continue
            for t in n.targets:
                pairs = (list(zip(t.elts, n.value.elts)) if isinstance(t, (ast.Tuple, ast.List))
                         and isinstance(n.value, (ast.Tuple, ast.List)) and len(t.elts) == len(n.value.elts)
                         else [(t, n.value)])
                for tt, vv in pairs:
                    if isinstance(tt, ast.Name) and tt.id not in aliases and (
                            soa_ish(vv, names, aliases)
                            or (isinstance(vv, ast.Attribute) and vv.attr == "registry")):
                        aliases.add(tt.id)
                        changed = True
    return aliases


def d6_hits(tree: ast.AST, names: set[str]) -> list[tuple[int, str, str]]:
    """層の属性(``X.attr = …``・組の代入の要素)に SoA の配列・ビュー・別名を入れる行。"""
    hits = []
    scopes = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))] or [tree]
    for fn in scopes:
        aliases = _local_aliases(fn, names)
        for n in ast.walk(fn):
            if not isinstance(n, (ast.Assign, ast.AnnAssign)) or n.value is None:
                continue
            tgts = n.targets if isinstance(n, ast.Assign) else [n.target]
            for t in tgts:
                pairs = (list(zip(t.elts, n.value.elts)) if isinstance(t, (ast.Tuple, ast.List))
                         and isinstance(n.value, (ast.Tuple, ast.List)) and len(t.elts) == len(n.value.elts)
                         else [(t, n.value)])
                for tt, vv in pairs:
                    if isinstance(tt, (ast.Attribute, ast.Subscript)) and soa_ish(vv, names, aliases):
                        hits.append((n.lineno, ast.unparse(tt), ast.unparse(n)[:90]))
    return sorted(set(hits))


def _names() -> set[str]:
    decl = A.declared_columns(SRC)
    return {c for v in decl.values() for c in v}


def test_d6_no_layer_holds_a_soa_array_view_or_alias():
    names = _names()
    offenders, used = [], set()
    for fp in A.source_files(SRC):
        rel = fp.relative_to(SRC).as_posix()
        if rel in _EXEMPT_D6:
            continue
        for ln, tgt, text in d6_hits(ast.parse(fp.read_text(encoding="utf-8")), names):
            if (rel, tgt) in D6_ALLOW:
                used.add((rel, tgt))
                continue
            offenders.append(f"{rel}:{ln} {text}")
    assert not offenders, offenders
    assert used == set(D6_ALLOW), set(D6_ALLOW) - used


def test_d6_finds_the_alias_forms():
    """負の対照(検収 §1 の 5): 9 つの形のうち AST で追える 8 つが見つかる(np.asarray の写しは dtype で写しかビューか
    決まらないので見つける側に倒す)。"""
    names = _names()
    src = (
        "def bind(self, agents, b, name):\n"
        "    r = agents.registry\n"
        "    self.a = agents.registry.cell[:]\n"
        "    self.b = b.soa.agents.registry.hunger\n"
        "    self.c = r.arrays['hunger']\n"
        "    self.d = getattr(r, 'hunger')\n"
        "    self.e = r.field(name)\n"
        "    self.f = r.hunger\n"
        "    self.g = np.asarray(r.hunger)\n"
        "    self.h, self.i = r.hunger, 3\n"
        "    self.j = {'h': r.hunger}\n"
        "    h = r.hunger\n"
        "    self.k = h\n"
        "    self.ok = 3\n")
    hits = {tgt for _ln, tgt, _t in d6_hits(ast.parse(src), names)}
    assert hits == {f"self.{c}" for c in "abcdefghjk"}, hits


# ================================================================= 10: D② を本物の検査に
FROZEN = HERE / "writes_soa_frozen.json"


def d2_mismatches(systems, frozen: dict[str, list[str]]) -> list[str]:
    """凍結の表と食い違う系の名(閉包を ``resolve_ops`` から計算し直したもの・系が持つ ``writes.soa`` の両方を見る)。"""
    out = []
    for s in systems:
        want = frozen.get(s.name)
        if want is None or sorted(AL.writes_for_ops(s.resolve_ops)) != want or sorted(s.writes.soa) != want:
            out.append(s.name)
    return out + sorted(set(frozen) - {s.name for s in systems})


def test_d2_writes_soa_matches_the_frozen_table():
    """D②: 系の書く SoA の列(resolve の口の閉包)が、凍結して確かめた表と同じ。resolve.py の書きが変わったり
    ``resolve_ops`` を変えたりして許可が広がる・狭まると落ちる(表を作り直して差を確かめてから更新する)。"""
    frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
    assert d2_mismatches(SYSTEMS, frozen) == []


def test_d2_detects_a_widened_or_narrowed_permit():
    """負の対照(D②・検収 §1 の 10): 系の ``resolve_ops`` に口を 1 つ足す(許可が広がる)・1 つ外す(狭まる)と、
    凍結の表と食い違って見つかる。"""
    from dataclasses import replace

    frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
    pp, pc = SPECS["perceive_prepare"], SPECS["phase_c"]
    assert "agents.refractory_until" not in AL.writes_for_ops(pp.resolve_ops)
    wider = [replace(s, resolve_ops=s.resolve_ops | {"set_refractory"}) if s is pp else s for s in SYSTEMS]
    assert d2_mismatches(wider, frozen) == ["perceive_prepare"]
    op = sorted(pc.resolve_ops)[0]
    narrower = [replace(s, resolve_ops=s.resolve_ops - {op}) if s is pc else s for s in SYSTEMS]
    assert AL.writes_for_ops(pc.resolve_ops - {op}) != AL.writes_for_ops(pc.resolve_ops), op  # 外すと狭まる口
    assert d2_mismatches(narrower, frozen) == ["phase_c"]


# ================================================================= 6: D① の別名
def test_d1_sees_plain_imports_and_other_aliases(tmp_path):
    """負の対照(検収 L9): resolve の口を素の import・別の別名で呼んでも ``resolve_calls`` に出る。"""
    import importlib.util
    import sys

    p = tmp_path / "fake_d1.py"
    p.write_text(
        "from shibuya.engine.resolve import revert_conversation\n"
        "import shibuya.engine.resolve as RV\n"
        "from shibuya.engine import resolve as R2\n"
        "def sys_fake(ctx, b):\n"
        "    revert_conversation(b.soa.agents, [0])\n"
        "    RV.set_activity(b.soa.agents, [0], [0])\n"
        "    R2.clear_intent(b.soa.agents, [0])\n"
        "    from shibuya.engine.resolve import set_intent as si\n"
        "    si(b.soa.agents, [0])\n", encoding="utf-8")
    spec = importlib.util.spec_from_file_location("fake_d1", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["fake_d1"] = mod
    spec.loader.exec_module(mod)
    c = SC.analyze(mod.sys_fake)
    assert c.resolve_calls == {"revert_conversation", "set_activity", "clear_intent", "set_intent"}, c.resolve_calls


def test_d3_tally_writes_through_tuple_aliases_are_seen():
    """検収 §1 の 7: 組の代入の別名(``a, b = rs.x, rs.y``)と ``rs.<欄>`` の別名を通した書きも積算の書きに数える。"""
    c = SC.analyze(SPECS["observe"].fn)
    assert {"diag_rows", "sleep_counts", "occ_ticks", "occ_counts", "occ_kind", "occ_transit",
            "prev_tape_misses", "prev_sessions"} <= c.tally_stores, c.tally_stores


# ================================================================= 2 の補い(検収 L4b): 箱の段 C を素通りする書き
def bypass_setattr_sites(rel: str, tree: ast.AST) -> list[str]:
    """``object.__setattr__(…)``(箱の ``__setattr__`` の段 C を素通りする)を系のモジュールで使う行。"""
    out = []
    for n in ast.walk(tree):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "__setattr__"
                and isinstance(n.func.value, ast.Name) and n.func.value.id == "object"):
            out.append(f"{rel}:{n.lineno}")
    return out


def test_systems_modules_do_not_bypass_the_box_setattr():
    """系のモジュール(箱の定義 ``boxes.py`` の外)は ``object.__setattr__`` を使わない(段 C を素通りしない)。"""
    root = SRC / "engine" / "systems"
    hits = []
    for fp in sorted(root.glob("*.py")):
        if fp.name == "boxes.py":
            continue
        hits += bypass_setattr_sites(fp.name, ast.parse(fp.read_text(encoding="utf-8")))
    assert not hits, hits


def test_bypass_setattr_check_catches_a_planted_line():
    """負の対照(検収 L4b): ``object.__setattr__(b.scratch, "outcome", …)`` が見つかる。"""
    planted = ast.parse("def sys_x(ctx, b):\n    object.__setattr__(b.scratch, 'outcome', None)\n")
    assert bypass_setattr_sites("fake.py", planted) == ["fake.py:2"]
