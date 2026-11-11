# -*- coding: utf-8 -*-
"""tools/pkgmove(移す段 3 の道具・返事その 7 §4-2・計画 package-map-final §7-4 の段 3)の試験。data は要らない。

**今の木の状態に依らない**(親の裁定 tests1 の 1): 段 4 では、各段を当てた後の木でもこの試験が通らないといけない。だから、本物の
木を写した試験の木で「次に当てる段」(まだ当たっていない最初の段=``pending``)を選び、期待は対応表の行と計画から作る。全段が当たった
木では、当てる段の要る試験は理由つきで飛ばし、作った小さな木の試験と、守りを直に呼ぶ試験と、冪等の試験が残る。

- 一時のコピーの木(src/shibuya・tests・tools と凍結の JSON・つなぎの台帳・tests が読む docs の記録の道具)で回す。リポの木には
  書かない。
- 当てた木では、import の文と許可の一覧の道の文字列の行のほかは 1 バイトも変わらない(移したファイルは古い道と新しい道で比べる)。
  許可の一覧の外の文字列とバイト列の定数は 1 つも変わらない(AST で全部の定数を前後で突き合わせる=道具の守りとは別の実装)。
- 凍結の値が残る(道具の守りが「同じ」)。負の対照は、どの守りが止めたかを文まで確かめる。
- 書かない実行は木に何も書かない。保留の行の名指しは断る。本体の作業木への ``--apply`` は断る(断る側に倒す)。冪等。
- 対応表 TOML が作り直しと同じ。許可の一覧 TOML は、まだどの段も当たっていない木でだけ作り直しと比べる(段を当てた木では
  作り直しが要る=取り込みと段ごとに親が作り直す)。
"""
from __future__ import annotations

import ast
import dataclasses
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_TOOLS = ROOT / "tools"
if str(_TOOLS) not in sys.path:  # 末尾に足す(tools の下の名が入れた包みを隠さないように)
    sys.path.append(str(_TOOLS))

from pkgmove import allow as AL  # noqa: E402
from pkgmove import classids as CI  # noqa: E402
from pkgmove import cli as CLI  # noqa: E402
from pkgmove import guard as G  # noqa: E402
from pkgmove import ledgerpaths as LPT  # noqa: E402
from pkgmove import move as MV  # noqa: E402
from pkgmove import strings as ST  # noqa: E402
from pkgmove.model import SRC_PREFIX, Ctx, Index, Tree, apply_edits, docstring_ids, mod_of, symbol_map  # noqa: E402
from pkgmove.table import HELD, MAP_REL, STAGES, build_map_text, load_map, parse_table  # noqa: E402

CLI_PY = ROOT / "tools" / "pkgmove" / "cli.py"
FROZEN_FILES = ("tests/engine/state/names_frozen.json", "tests/engine/state/class_ids_frozen.json",
                "docs/design/bridging-ledger.json")
MAPDOC = load_map(ROOT / MAP_REL)


def _ignore(_d: str, names: list[str]) -> set[str]:
    return {n for n in names if n in ("__pycache__", ".pytest_cache")}


def make_copy(dst: Path) -> Path:
    """一時のコピーの木(src/shibuya・tests・tools・凍結の JSON とつなぎの台帳・tests が読む docs の記録の道具)。"""
    for top in ("src/shibuya", "tests", "tools"):
        shutil.copytree(ROOT / top, dst / top, ignore=_ignore)
    for f in (*FROZEN_FILES, *AL.RECORD_TOOLS):
        if (ROOT / f).is_file():
            (dst / f).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / f, dst / f)
    return dst


def digest(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in sorted(root.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts:
            out[p.relative_to(root).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def run_cli(*args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run([sys.executable, str(CLI_PY), *args], capture_output=True, text=True, encoding="utf-8",
                          errors="replace", env=env, cwd=str(ROOT))


def frozen_of(root: Path) -> G.Frozen:
    return G.Frozen.load(lambda rel: (root / rel).read_text(encoding="utf-8"))


def plan_for(root: Path, stages, **kw) -> MV.Plan:
    return MV.make_plan(Tree.load(root, extra=AL.RECORD_TOOLS), MAPDOC, stages, allow_tt=AL.load_tests_tools(ROOT),
                        frozen=frozen_of(root), ledger_text=(root / MV.LEDGER_REL).read_text(encoding="utf-8"), **kw)


def apply_rows(tree: Tree, stage: str) -> list[Row]:
    """木の今の形で、段のうち当てる行(まだ当たっていない行)。"""
    rows, _held = MV.select_rows(MAPDOC, (stage,))
    return [r for r in rows if MV._row_state(tree, r) == "apply"]


@lru_cache(maxsize=1)
def _root_tree() -> Tree:
    return Tree.load(ROOT, extra=AL.RECORD_TOOLS)


@lru_cache(maxsize=1)
def pending() -> tuple[str, ...]:
    """リポの今の木で、まだ当てる行のある段(段 4 の順)。"""
    t = _root_tree()
    return tuple(s for s in STAGES if apply_rows(t, s))


def pristine() -> bool:
    """どの段の行も当たっていない木か(全部の段に当てる行が残っている=段 3 の時点の木)。"""
    t = _root_tree()
    rows, _ = MV.select_rows(MAPDOC, STAGES)
    return all(MV._row_state(t, r) == "apply" for r in rows)


def where(rel: str) -> str:
    """今の道(``src/shibuya`` からの相対)のファイルの、リポの今の木の中の道筋(移した後なら新しい道)。"""
    return MV.locate(_root_tree(), MAPDOC, rel)


def need_pending(n: int = 1) -> tuple[str, ...]:
    p = pending()
    if len(p) < n:
        pytest.skip(f"当てる段が {n} つ無い木(当たっていない段 {list(p)})=段 4 の段を当てた後の木")
    return p


@pytest.fixture(scope="module")
def base_copy(tmp_path_factory) -> Path:
    return make_copy(tmp_path_factory.mktemp("pkgmove_base"))


@pytest.fixture(scope="module")
def staged(base_copy) -> MV.Plan:
    """次に当てる段(まだ当たっていない最初の段)の計画。全段が当たった木では飛ばす。"""
    return plan_for(base_copy, (need_pending()[0],))


@pytest.fixture(scope="module")
def applied(tmp_path_factory, staged) -> Path:
    root = make_copy(tmp_path_factory.mktemp("pkgmove_applied"))
    MV.apply(staged, root)
    return root


def _first_stage_is(stage: str) -> bool:
    return bool(pending()) and pending()[0] == stage


# ------------------------------------------------------------------ 対応表と許可の一覧
def test_map_toml_is_made_from_the_table_and_is_current():
    rows = parse_table((ROOT / "docs/reference/package-map-final-2026-11-09-files.md").read_text(encoding="utf-8"))
    assert len(rows) == 328
    kinds = Counter(r.kind for r in rows)
    assert kinds == {"move": 206, "keep": 94, "split": 24, "delete": 2, "empty": 2}
    assert {r.old: r.held for r in rows if r.held} == HELD
    # 保留の一覧: 問い 1 の 4 本・問い 2(resolve)・問い 6(run)・行 224a
    assert set(HELD) == {"engine/contact/deliver.py", "engine/contact/calls.py", "engine/contact/chat_state.py",
                         "engine/contact/tools.py", "engine/resolve.py", "engine/run.py", "engine/removed_switches.py"}
    by = {r.old: r for r in rows}
    assert by["engine/resolve.py"].kind == "split" and "act/ops/detect_writes.py" in by["engine/resolve.py"].split_to
    assert by["core/__init__.py"].empty_head and by["core/__init__.py"].new == "foundation/__init__.py"
    assert by["world/__init__.py"].kind == "empty" and by["agents/__init__.py"].kind == "delete"
    assert (ROOT / MAP_REL).read_text(encoding="utf-8") == build_map_text(ROOT)
    assert run_cli("map", "--check").returncode == 0


def test_allow_toml_is_current_and_src_tables_exist():
    """許可の一覧 TOML は、どの段も当たっていない木でだけ作り直しと比べる。(b-src) の表は今の置き場に全部ある。"""
    if pristine():
        assert run_cli("allow", "--check").returncode == 0
    for f, sym, _why in AL.SRC_TABLES:
        t = ast.parse((ROOT / where(f)).read_text(encoding="utf-8"))
        assert sym in set(symbol_map(t).values()), (f, sym)
    sl = ast.parse((ROOT / where("engine/state_ledger.py")).read_text(encoding="utf-8"))
    allows = {n.targets[0].id for n in sl.body if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
              and n.targets[0].id.startswith("_ALLOW_")}
    assert allows == {s for f, s, _ in AL.SRC_TABLES if f == "engine/state_ledger.py" and s.startswith("_ALLOW_")}


# ------------------------------------------------------------------ 書かない実行・保留・本体の作業木
def test_dry_run_writes_nothing(tmp_path):
    root = make_copy(tmp_path / "t")
    before = digest(root)
    stage = pending()[0] if pending() else "foundation"
    r = run_cli("move", "--stage", stage, "--tree", str(root))
    assert r.returncode == 0, r.stderr[-2000:]
    assert "書いていない" in r.stdout
    assert digest(root) == before


def test_held_rows_are_refused(base_copy):
    for old in HELD:
        with pytest.raises(MV.Refused):
            MV.select_rows(MAPDOC, (), only=[old])
    r = run_cli("move", "--stage", "interim_bundles", "--only", "engine/contact/deliver.py", "--tree", str(base_copy))
    assert r.returncode == 2 and "保留" in r.stderr
    rows, held = MV.select_rows(MAPDOC, ("interim_bundles",))
    assert {r.old for r in held} == {"engine/contact/deliver.py", "engine/contact/calls.py",
                                     "engine/contact/chat_state.py", "engine/contact/tools.py"}
    assert not ({r.old for r in rows} & set(HELD))
    rows, held = MV.select_rows(MAPDOC, ("foundation",))
    assert [r.old for r in held] == ["engine/removed_switches.py"]


def test_staged_plan_refuses_the_held_rows_and_leaves_them(staged):
    _rows, held = MV.select_rows(MAPDOC, staged.stages)
    assert [r.old for r in staged.refused] == [r.old for r in held]
    for r in held:
        p = SRC_PREFIX + r.old
        assert (p in staged.before.files) == (p in staged.after.files)
        if r.new:
            assert (SRC_PREFIX + r.new in staged.after.files) == (SRC_PREFIX + r.new in staged.before.files)


def _git(cwd: Path, *a: str) -> None:
    subprocess.run(["git", *a], cwd=str(cwd), check=True, capture_output=True)


def test_apply_refuses_a_main_worktree_and_allows_others(tmp_path):
    main = tmp_path / "main"
    main.mkdir()
    _git(main, "init", "-q")
    (main / "x.txt").write_text("x", encoding="utf-8")
    _git(main, "add", "x.txt")
    _git(main, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "x")
    linked = tmp_path / "linked"
    _git(main, "worktree", "add", "-q", str(linked))
    plain = tmp_path / "plain"
    plain.mkdir()
    assert CLI.is_main_worktree(main) and CLI.is_main_worktree(main / ".git" / "..")
    sub = main / "sub"
    sub.mkdir()
    assert CLI.is_main_worktree(sub)
    assert not CLI.is_main_worktree(linked)
    assert not CLI.is_main_worktree(plain)
    # 本体の作業木へ --apply は断る(木の中身があっても何も書かない)
    make_copy(main)
    before = digest(main)
    r = run_cli("move", "--stage", "foundation", "--apply", "--tree", str(main))
    assert r.returncode == 2 and "本体の作業木" in r.stderr
    assert digest(main) == before
    # --apply には --tree が要る
    assert run_cli("move", "--stage", "foundation", "--apply").returncode == 2
    # このリポが git の中なら、その本体の作業木も本体と見分ける(書かずに関数だけ)
    r = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--path-format=absolute", "--git-common-dir"],
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode == 0 and r.stdout.strip():
        assert CLI.is_main_worktree(Path(r.stdout.strip()).parent)


# ------------------------------------------------------------------ 当てた木: import の文と許可の一覧の行のほかは同じ
def _import_lines(tree: ast.Module) -> set[int]:
    out: set[int] = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            out |= set(range(n.lineno, n.end_lineno + 1))
    return out


def _allowed_lines(tree: ast.Module, path: str, allowed: set[tuple[str, str]]) -> set[int]:
    syms = symbol_map(tree)
    out: set[int] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and (path, syms.get(id(n), "")) in allowed:
            out |= set(range(n.lineno, n.end_lineno + 1))
    return out


def _sites(plan: MV.Plan) -> set[tuple[str, str]]:
    tree = plan.before
    s = {(x.path, x.symbol) for x in AL.src_sites(lambda f: MV.locate(tree, MAPDOC, f))}
    s |= {(x.path, x.symbol) for x in AL.load_tests_tools(ROOT)}
    s.add((MV.locate(tree, MAPDOC, AL.CLASS_IDS_TABLE[0]), AL.CLASS_IDS_TABLE[1]))
    s.add((MV.locate(tree, MAPDOC, AL.LEDGER_PATHS_TABLE[0]), AL.LEDGER_PATHS_TABLE[1]))
    s |= {(h, "__all__") for h in plan.dropped_all}  # (e) 頭の __all__(除いた名だけ=別の試験で確かめる)
    return s


def _py_files(root: Path) -> set[str]:
    out = {p.relative_to(root).as_posix() for top in ("src", "tests", "tools")
           for p in (root / top).rglob("*.py") if "__pycache__" not in p.parts}
    return out | {f for f in AL.RECORD_TOOLS if (root / f).is_file()}


def test_only_import_statements_and_allowlisted_string_lines_change(base_copy, applied, staged):
    allowed = _sites(staged)
    moves = {o: n for o, n in staged.file_moves.items() if o.endswith(".py")}
    inv = {v: k for k, v in moves.items()}
    heads = set(staged.emptied_heads) | set(staged.created_heads) | set(staged.deleted)
    after_files, before_files = _py_files(applied), _py_files(base_copy)
    assert after_files - before_files == set(moves.values()) | (set(staged.created_heads) - before_files)
    assert before_files - after_files == set(moves) | set(staged.deleted)
    changed = 0
    for q in sorted(after_files):
        p = inv.get(q, q)
        if q in heads or p in heads:
            assert (applied / q).read_bytes() == b"", q  # 頭は空(新しい頭・空にした古い頭)
            continue
        old = (base_copy / p).read_bytes()
        new = (applied / q).read_bytes()
        if old == new:
            continue
        changed += 1
        to, tn = ast.parse(old.decode("utf-8")), ast.parse(new.decode("utf-8"))
        lo = old.decode("utf-8").split("\n")
        ln = new.decode("utf-8").split("\n")
        skip_o = _import_lines(to) | _allowed_lines(to, p, allowed)
        skip_n = _import_lines(tn) | _allowed_lines(tn, p, allowed)
        keep_o = [x for i, x in enumerate(lo, 1) if i not in skip_o]
        keep_n = [x for i, x in enumerate(ln, 1) if i not in skip_n]
        assert keep_o == keep_n, f"{p} → {q}: import の文と許可の一覧の行のほかが変わった"
    assert changed == len([p for p in staged.changed if p.endswith(".py") and p not in heads])


def _const_multiset(text: str, path: str, allowed: set[tuple[str, str]]) -> Counter:
    t = ast.parse(text)
    syms = symbol_map(t)
    return Counter((syms.get(id(n), ""), n.value) for n in ast.walk(t)
                   if isinstance(n, ast.Constant) and isinstance(n.value, (str, bytes))
                   and (path, syms.get(id(n), "")) not in allowed)


def test_string_constants_outside_the_allowlist_do_not_change(base_copy, applied, staged):
    allowed = _sites(staged)
    heads = set(staged.emptied_heads) | set(staged.deleted)
    n = 0
    for p in sorted(staged.before.files):
        if p in heads or p.startswith("tools/pkgmove/") or p == "tests/tools/test_pkgmove.py":
            continue
        q = staged.file_moves.get(p, p)
        a = _const_multiset((base_copy / p).read_text(encoding="utf-8"), p, allowed)
        b = _const_multiset((applied / q).read_text(encoding="utf-8"), p, allowed)
        assert a == b, p
        n += 1
    assert n > 900


def _consts(text: str) -> list[str]:
    t = ast.parse(text)
    ds = docstring_ids(t)
    return [n.value for n in ast.walk(t) if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in ds]


def test_mora_rule_and_other_untouched_path_shaped_strings_stay_in_the_rest_plan(base_copy):
    """残る段を全部まとめた計画(全段が当たった木では行 0 の計画)でも: 腕 mora の manifest に出る文は書き換えない・つなぎの
    台帳は書き換えない(398 行)・守りが全部同じ・保留の行を断る。"""
    stages = pending() or STAGES
    plan = plan_for(base_copy, stages)
    p = MV.locate(plan.before, MAPDOC, "engine/speech_clock.py")
    q = plan.file_moves.get(p, p)
    want = [c for c in _consts(plan.before.files[p]) if "engine.speech.port.mora_count" in c]
    assert want and all(c in _consts(plan.after.files[q]) for c in want)
    rows = [r for r in plan.rows_applied if r.kind == "move"]
    if any(r.old == "engine/speech/port.py" for r in rows):
        assert any(u["file"] == p and u["token"].startswith("engine.speech.port") for u in plan.untouched)
    assert plan.ledger["rows_src"] == 398
    assert MV.LEDGER_REL not in plan.after.files
    assert set(plan.guards) == {"names_frozen", "class_ids", "shaped_74", "outside_allowlist", "ledger_paths",
                                "import_names", "head_all"}
    assert all(v.startswith("同じ") for v in plan.guards.values()), plan.guards
    _rows, held = MV.select_rows(MAPDOC, stages)
    assert {r.old for r in plan.refused} == {r.old for r in held}


# ------------------------------------------------------------------ 凍結の値と負の対照
def test_frozen_values_are_kept_by_the_staged_plan(staged, applied):
    assert all(v.startswith("同じ") for v in staged.guards.values()), staged.guards
    cp = MV.locate(staged.before, MAPDOC, AL.CLASS_IDS_TABLE[0])
    before = CI.table_of(staged.before.files[cp])
    after = CI.table_of((applied / staged.file_moves.get(cp, cp)).read_text(encoding="utf-8"))
    assert sorted(before.values()) == sorted(after.values())
    assert list(after) == sorted(after)
    # CP12 の宣言はそのまま(書き換えない)
    decl = 'CLASS_ID: ClassVar[str] = "shibuya.engine.events.log.Experiment"'
    lp = next(f for f, t in staged.before.files.items() if f.startswith(SRC_PREFIX) and decl in t)
    assert decl in (applied / staged.file_moves.get(lp, lp)).read_text(encoding="utf-8")
    # 乱数の用途名は表の中でも書き換えない
    ra = MV.locate(staged.before, MAPDOC, "engine/rng_audit.py")
    assert '"engine.processes.rail"' in (applied / staged.file_moves.get(ra, ra)).read_text(encoding="utf-8")
    if staged.stages == ("foundation",):  # 段 3 の時点の木で foundation を当てたとき(同じ __qualname__ の組)
        assert after["shibuya.foundation.types.EventClass"] == "shibuya.core.types.EventClass"
        assert after["shibuya.foundation.manifest.schema.Arbiter"] == "shibuya.manifest.schema.Arbiter"
        assert after["shibuya.engine.arbiter.Arbiter"] == "shibuya.engine.arbiter.Arbiter"
        text = (applied / "src/shibuya/engine/rng_audit.py").read_text(encoding="utf-8")
        assert '("foundation/ports/decision.py", "present_rng", "decision.present")' in text
        assert 'rel == "foundation/rng.py"' in text


def _naive(old_new: dict[str, str]):
    """素朴な書き換え(字面を全部置き換える=凍結の値も書き換える)。負の対照のための差し替え。"""
    def rv(ctx, rules, value):
        new = value
        reps = []
        for o, n in old_new.items():
            for m in re.finditer(re.escape(o), value):
                reps.append((m.start(), m.end(), n, "naive"))
            new = new.replace(o, n)
        return new, sorted(reps), []
    return rv


def _any_stages() -> tuple[str, ...]:
    """当てる段があればその最初の段、無ければ全段(行 0 の計画=書き換えの道と守りは回る)。"""
    return (pending()[0],) if pending() else STAGES


def test_negative_naive_rewrite_of_rng_domain_names_is_stopped(base_copy, monkeypatch):
    monkeypatch.setattr(ST, "rewrite_value", _naive({"engine.processes.rail": "world.laws.rail"}))
    extra = [AL.Site(MV.locate(Tree.load(base_copy), MAPDOC, "engine/rng_audit.py"), "SAFE_SITES", "paths")]
    with pytest.raises(MV.Stopped) as e:
        plan_for(base_copy, _any_stages(), extra_sites=extra)
    msg = "\n".join(e.value.errors)
    assert "names_frozen の rng_domains_path_shaped" in msg
    assert "凍結の値の字面が変わった" in msg


def test_negative_naive_rewrite_of_a_class_name_in_a_test_is_stopped(tmp_path, monkeypatch):
    root = make_copy(tmp_path / "t")
    rel = "tests/zz_frozen_case.py"
    (root / rel).write_text('def f():\n    return "shibuya.core.types.EventClass"\n', encoding="utf-8", newline="")
    monkeypatch.setattr(ST, "rewrite_value", _naive({"shibuya.core.types.EventClass": "shibuya.foundation.types.EventClass"}))
    with pytest.raises(MV.Stopped) as e:
        plan_for(root, _any_stages(), extra_sites=[AL.Site(rel, "f", "paths")])
    assert any("凍結の値の字面が変わった: " + rel in x for x in e.value.errors), e.value.errors[:3]


def test_negative_key_guard_catches_a_swapped_pair_and_changed_values():
    """〔再検収 L-a〕鍵の守り(直に呼ぶ): 同じ ``__qualname__`` の組の値の入れ替え・値の書き換え・1 対 1 でない対応表を止める。"""
    old = {"shibuya.a.Arbiter": "shibuya.a.Arbiter", "shibuya.b.Arbiter": "shibuya.b.Arbiter"}
    fq = {"shibuya.a.Arbiter": "Arbiter", "shibuya.b.Arbiter": "Arbiter"}
    modmap = {"shibuya.a": "shibuya.c"}
    good = CI.new_table(old, modmap, fq)
    CI.check_keys(old, good, modmap, fq)
    swapped = {"shibuya.c.Arbiter": "shibuya.b.Arbiter", "shibuya.b.Arbiter": "shibuya.a.Arbiter"}
    with pytest.raises(CI.ClassIdError, match="鍵の取り違え"):
        CI.check_keys(old, swapped, modmap, fq)
    with pytest.raises(CI.ClassIdError, match=re.escape("値(凍結の名)が変わった")):
        CI.check_keys(old, {"shibuya.c.Arbiter": "shibuya.c.Arbiter", "shibuya.b.Arbiter": "shibuya.b.Arbiter"},
                      modmap, {**fq, "shibuya.c.Arbiter": "Arbiter"})
    with pytest.raises(CI.ClassIdError, match="1 対 1 でない"):
        CI.check_keys({"shibuya.a.X": "shibuya.a.X"}, {"shibuya.c.X": "shibuya.a.X"},
                      {"shibuya.a": "shibuya.c", "shibuya.b": "shibuya.c"}, {"shibuya.a.X": "X"})


def test_negative_swapping_a_same_qualname_pair_is_stopped_in_a_plan(base_copy):
    """計画の中でも鍵の守りが止める(組の片方が動く foundation の段がまだ当たっていない木だけ)。"""
    if "foundation" not in pending():
        pytest.skip("foundation の段が当たった木=組の片方が動く段が無い(鍵の守りは直に呼ぶ試験で確かめる)")

    def swapped(old, modmap, fq):
        new = CI.new_table(old, modmap, fq)
        a, b = "shibuya.foundation.manifest.schema.Arbiter", "shibuya.engine.arbiter.Arbiter"
        new[a], new[b] = new[b], new[a]
        return new
    with pytest.raises(MV.Stopped) as e:
        plan_for(base_copy, ("foundation",), keyfn=swapped)
    assert "鍵の取り違え" in "\n".join(e.value.errors)

    def values_too(old, modmap, fq):
        new = CI.new_table(old, modmap, fq)
        return {k: (k if "foundation" in k else v) for k, v in new.items()}
    with pytest.raises(MV.Stopped) as e:
        plan_for(base_copy, ("foundation",), keyfn=values_too)
    assert "値(凍結の名)が変わった" in "\n".join(e.value.errors)


def test_negative_a_map_sending_two_modules_to_one_is_refused(base_copy):
    """〔突然変異 m19〕2 つの行を同じ行き先へ送る対応表は、行き先の守りが断る(どの守りが止めたかまで見る)。"""
    stage = need_pending()[0]
    tree = Tree.load(base_copy)
    cand = [r for r in apply_rows(tree, stage) if r.kind == "move" and not r.is_head and r.old.endswith(".py")]
    if len(cand) < 2:
        pytest.skip("当てる段に動かすファイルが 2 本無い")
    rows = list(MAPDOC.rows)
    i = next(k for k, r in enumerate(rows) if r.old == cand[1].old)
    rows[i] = dataclasses.replace(rows[i], new=cand[0].new)
    with pytest.raises(MV.Refused, match="対応表の行き先が重なる"):
        MV.make_plan(tree, MV.MapDoc(rows=rows), (stage,), allow_tt=AL.load_tests_tools(ROOT),
                     frozen=frozen_of(base_copy))


def test_frozen_guard_stops_when_a_frozen_value_is_already_different(tmp_path):
    root = make_copy(tmp_path / "t")
    f = root / MV.locate(Tree.load(root), MAPDOC, "engine/processes/rail.py")
    f.write_text(f.read_text(encoding="utf-8").replace('"engine.processes.rail"', '"engine.processes.rail2"', 1),
                 encoding="utf-8", newline="")
    with pytest.raises(MV.Stopped) as e:
        plan_for(root, _any_stages())
    assert "移す前の木が凍結と既に違う" in e.value.errors[0]


# ------------------------------------------------------------------ 冪等・当てた木の形
def _normalized(text: str) -> tuple[list[tuple[str, str, str]], list[str]]:
    """(import の文で読む (モジュール, 名, 別名) を並べ直した一覧, import の文の外の行)。段を分けて当てると、行き先で
    分けた import の文の並びと分け方が変わることがある(読む名は同じ)。"""
    t = ast.parse(text)
    imp = sorted((getattr(n, "module", "") or "", a.name, a.asname or "") for n in ast.walk(t)
                 if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names)
    lines = _import_lines(t)
    return imp, [x for i, x in enumerate(text.split("\n"), 1) if i not in lines]


def test_stages_in_order_give_the_same_tree_as_together(base_copy):
    """残る最初の 2 段を順に当てた木と、2 つをまとめて当てた木が同じ(違ってよいのは import の文の並びと分け方だけ・前の段で
    空にした古い頭は、最後のファイルが出た段で消す)。守りは各段で同じ。"""
    s1, s2 = need_pending(2)[:2]
    fz = frozen_of(base_copy)
    led = (base_copy / MV.LEDGER_REL).read_text(encoding="utf-8")
    first = plan_for(base_copy, (s1,))
    second = MV.make_plan(first.after, MAPDOC, (s2,), allow_tt=AL.load_tests_tools(ROOT), frozen=fz, ledger_text=led)
    both = plan_for(base_copy, (s1, s2))
    assert all(v.startswith("同じ") for v in second.guards.values())
    if (s1, s2) == ("foundation", "world"):
        assert SRC_PREFIX + "manifest/__init__.py" in second.deleted
    a, b = second.after, both.after
    assert set(a.files) == set(b.files) and a.blobs == b.blobs
    for q in sorted(p for p in a.files if a.files[p] != b.files[p]):
        assert _normalized(a.files[q]) == _normalized(b.files[q]), q


def test_apply_twice_is_the_same(tmp_path):
    root = make_copy(tmp_path / "t")
    stage = pending()[0] if pending() else "foundation"
    r = run_cli("move", "--stage", stage, "--apply", "--tree", str(root))
    assert r.returncode == 0, r.stderr[-2000:]
    once = digest(root)
    r2 = run_cli("move", "--stage", stage, "--apply", "--tree", str(root))
    assert r2.returncode == 0, r2.stderr[-2000:]
    assert '"rows_applied": 0' in r2.stdout and '"changed_files": 0' in r2.stdout
    assert digest(root) == once


def test_applied_tree_has_the_new_places_and_empty_heads(applied, staged):
    rows = apply_rows(staged.before, staged.stages[0])
    assert len(staged.rows_applied) == len(rows)
    moves = [r for r in rows if r.kind == "move" and not r.is_head]
    assert len(staged.file_moves) == len(moves)
    for r in moves:
        assert (applied / SRC_PREFIX / r.new).is_file() and not (applied / SRC_PREFIX / r.old).exists()
    for h in staged.created_heads + staged.emptied_heads:
        assert (applied / h).read_bytes() == b"", h
    for h in staged.deleted:
        assert not (applied / h).exists()
    if staged.stages == ("foundation",):
        assert len(rows) == 40  # 計画の 38 本+core/paths.py(91a)+つなぎの台帳の道の表(125a)
        assert (applied / "src/shibuya/core/wage_formula.py").is_file()
        text = (applied / "src/shibuya/engine/run.py").read_text(encoding="utf-8")
        assert "from shibuya.manifest import" not in text


# ------------------------------------------------------------------ round2(全段の予行で見つけた直しと、親の決定 1・2・7・12)
def test_head_reexports_of_modules_leaving_the_package_are_dropped(staged):
    """この段で空にしない頭の再輸出のうち、出どころが包みの外へ移るものの import の文を除く(循環の import を作らない)。
    除いた名を、その頭から読む import の文はどのファイルにも残らない。頭の中で使う名は除かない。"""
    dr = staged.dropped_reexports
    for head, names in dr.items():
        pkg = mod_of(head[len(SRC_PREFIX):])
        t = ast.parse(staged.after.files[head])
        bound = {a.asname or a.name for n in t.body if isinstance(n, ast.ImportFrom) for a in n.names}
        assert not (bound & set(names)), head
        for path, text in staged.after.files.items():
            if path.startswith("tools/pkgmove/") or path == "tests/tools/test_pkgmove.py":
                continue
            for n in ast.walk(ast.parse(text)):
                if isinstance(n, ast.ImportFrom) and n.level == 0 and n.module == pkg:
                    assert not ({a.name for a in n.names} & set(names)), (path, n.lineno)
    if staged.stages == ("foundation",):
        assert set(dr) == {SRC_PREFIX + "engine/__init__.py", SRC_PREFIX + "llm/__init__.py",
                           SRC_PREFIX + "perception/__init__.py"}
        assert "DeferralQueue" in dr[SRC_PREFIX + "engine/__init__.py"] and "Target" in dr[SRC_PREFIX + "llm/__init__.py"]
        assert "sha256_cbor" not in dr[SRC_PREFIX + "llm/__init__.py"]  # 頭の中で使う=除かない


def test_ledger_paths_table_follows_the_moves_and_the_ledger_is_kept(staged, base_copy):
    """(d) 移したファイルごとに「今の道 → 台帳の道」を表に足す(台帳は書き換えない)。台帳のコードの行の道は全部、表を通して
    今のファイルに届く。負の対照: 台帳の道に届かない行があれば止める。"""
    lp = MV.locate(staged.before, MAPDOC, AL.LEDGER_PATHS_TABLE[0])
    moves = {SRC_PREFIX + r.old: SRC_PREFIX + r.new for r in staged.rows_applied if r.kind == "move" and not r.is_head
             and r.old.endswith(".py")}
    want = LPT.updated(LPT.table_of(staged.before.files[lp]), moves)
    assert LPT.table_of(staged.after.files[staged.file_moves.get(lp, lp)]) == want
    assert staged.ledger_paths_added == len(moves)
    assert staged.guards["ledger_paths"].startswith("同じ")
    assert MV.LEDGER_REL not in staged.after.files
    led = (base_copy / MV.LEDGER_REL).read_text(encoding="utf-8")
    m = re.search(r'"declared_in": "(src/shibuya/[\w/]+)\.py#', led)
    assert m
    bad = led.replace(f'"declared_in": "{m.group(1)}.py#', f'"declared_in": "{m.group(1)}_gone.py#', 1)
    with pytest.raises(MV.Stopped) as e:
        MV.make_plan(Tree.load(base_copy, extra=AL.RECORD_TOOLS), MAPDOC, staged.stages,
                     allow_tt=AL.load_tests_tools(ROOT), frozen=frozen_of(base_copy), ledger_text=bad)
    assert any("台帳の道が今のファイルに届かない" in x for x in e.value.errors)


def test_catalog_json_relpath_moves_with_the_json(base_copy):
    """(b-src) 〔親の決定 2〕構築の側が凍結の JSON を書く先は、JSON と一緒に動く(JSON がまだ動いていない木では動かす段まで
    当て、動いた木では今の木の値が在る JSON を指す)。"""
    row = next(r for r in MAPDOC.rows if r.old == "manifest/frozen/world_catalog_v0_2.json")
    cat = MV.locate(Tree.load(base_copy), MAPDOC, "build/catalog_freeze.py")
    if row.stage in pending():
        stages = pending()[: pending().index(row.stage) + 1]
        plan = plan_for(base_copy, stages)
        assert f'CATALOG_JSON_RELPATH = "src/shibuya/{row.new}"' in plan.after.files[plan.file_moves.get(cat, cat)]
        assert SRC_PREFIX + row.new in plan.after.blobs
    else:
        text = (base_copy / cat).read_text(encoding="utf-8")
        m = re.search(r'CATALOG_JSON_RELPATH = "([^"]+)"', text)
        assert m and (base_copy / m.group(1)).is_file()


def test_record_tools_list_matches_the_scan_of_tests():
    """(a) の範囲に足す docs の記録の道具の一覧は、tests が道で読む docs の ``.py`` の走査と同じ。"""
    tree = _root_tree()
    got = AL.scan_record_tools({p: t for p, t in tree.files.items() if p.startswith("tests/")},
                               lambda rel: (ROOT / rel).is_file())
    assert tuple(got) == AL.RECORD_TOOLS


def test_record_tools_get_only_their_import_statements_rewritten(staged):
    # 本数は前提にしない(記録の道具の一覧は tests の字面の走査で決まる=試験の役が字面を減らせば減る)
    changed = [p for p in AL.RECORD_TOOLS if staged.after.files.get(p) != staged.before.files.get(p)]
    assert all(p in staged.changed for p in changed)
    assert all(e.kind == "import" for p in changed for e in staged.changed[p])


def test_skipping_interim_bundles_then_applying_it_keeps_the_guards(base_copy):
    """〔親の決定 12〕interim_bundles を飛ばして後の段を当て、最後に interim_bundles を当てても守りが通り、残る段をまとめて
    当てた木と同じ(違ってよいのは import の文の並びと分け方だけ)。全段が当たった木では、どちらも行 0。"""
    rest = tuple(s for s in (pending() or STAGES) if s != "interim_bundles")
    first = plan_for(base_copy, rest)
    last = MV.make_plan(first.after, MAPDOC, ("interim_bundles",), allow_tt=AL.load_tests_tools(ROOT),
                        frozen=frozen_of(base_copy), ledger_text=(base_copy / MV.LEDGER_REL).read_text(encoding="utf-8"))
    for pl in (first, last):
        assert all(v.startswith("同じ") for v in pl.guards.values()), pl.guards
    assert {r.old for r in last.refused} == {"engine/contact/deliver.py", "engine/contact/calls.py",
                                             "engine/contact/chat_state.py", "engine/contact/tools.py"}
    whole = plan_for(base_copy, pending() or STAGES)
    a, b = last.after, whole.after
    assert set(a.files) == set(b.files) and a.blobs == b.blobs
    for q in sorted(p for p in a.files if a.files[p] != b.files[p]):
        assert _normalized(a.files[q]) == _normalized(b.files[q]), q


# ------------------------------------------------------------------ 検収の指摘(M-1・M-2・M-3・突然変異・L-5・L-7・L-9)
def _tiny_tree(root: Path, files: dict[str, str]) -> Path:
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8")
    return root


def test_import_check_catches_a_cycle_and_passes_a_clean_tree(tmp_path):
    """〔M-1〕全モジュールを 1 本ずつ最初から import する確かめ。わざと循環を作った小さな木で落ち、直した木で通る。読んだ
    ``shibuya`` は木の src。"""
    from pkgmove import importcheck as IC

    bad = _tiny_tree(tmp_path / "bad", {
        "src/shibuya/__init__.py": "",
        "src/shibuya/pkg/__init__.py": "from shibuya.moved import THING\n",
        "src/shibuya/pkg/sib.py": "X = 1\n",
        "src/shibuya/moved.py": "from shibuya.pkg import sib\nTHING = sib.X\n",
    })
    doc = IC.check(bad, jobs=2)
    assert "shibuya.moved" in doc["bad"] and "ImportError" in doc["bad"]["shibuya.moved"] and not IC.ok(doc)
    assert doc["cli_help_exit"] is None
    assert Path(doc["shibuya_file"]).resolve() == (bad / "src/shibuya/__init__.py").resolve()
    assert run_cli("importcheck", "--tree", str(bad)).returncode == 3
    good = _tiny_tree(tmp_path / "good", {
        "src/shibuya/__init__.py": "",
        "src/shibuya/pkg/__init__.py": "",
        "src/shibuya/pkg/sib.py": "X = 1\n",
        "src/shibuya/moved.py": "from shibuya.pkg import sib\nTHING = sib.X\n",
    })
    assert IC.ok(IC.check(good, jobs=2))
    assert run_cli("importcheck", "--tree", str(good)).returncode == 0


def test_main_worktree_check_fails_closed(tmp_path, monkeypatch):
    """〔M-2〕git が失敗したら断る側・呼び手の GIT_DIR に左右されない・.git が 1 つも無いときだけ git の外。報告の置き場が本体の
    作業木の中でも断る(L-6)。"""
    main = tmp_path / "main"
    main.mkdir()
    _git(main, "init", "-q")
    (main / "x.txt").write_text("x", encoding="utf-8")
    _git(main, "add", "x.txt")
    _git(main, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "x")
    linked = tmp_path / "linked"
    _git(main, "worktree", "add", "-q", str(linked))
    broken = tmp_path / "broken"
    broken.mkdir()
    (broken / ".git").write_text("gitdir: " + str(tmp_path / "nowhere") + "\n", encoding="utf-8")
    plain = tmp_path / "plain"
    plain.mkdir()
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "nowhere"))
    assert CLI.is_main_worktree(main) and CLI.is_main_worktree(main / "sub" / "not_yet")
    monkeypatch.setenv("GIT_DIR", str(main / ".git" / "worktrees" / "linked"))
    assert CLI.is_main_worktree(main)
    # 〔検収 n11〕.git がファイルの作業木(linked)では git を呼ぶ。呼び手の GIT_DIR が本体の .git を指していても、外して聞く
    # (外さなければ git は本体の .git を答え、linked を本体と取り違える)
    monkeypatch.setenv("GIT_DIR", str(main / ".git"))
    assert not CLI.is_main_worktree(linked)
    monkeypatch.delenv("GIT_DIR")
    assert CLI.is_main_worktree(broken)  # git が失敗=断る
    assert not CLI.is_main_worktree(linked) and not CLI.is_main_worktree(plain)
    tree = _tiny_tree(tmp_path / "tree", {"src/shibuya/__init__.py": ""})
    r = run_cli("move", "--stage", "foundation", "--tree", str(tree), "--out-dir", str(main / "reports"))
    assert r.returncode == 2 and "報告の置き場" in r.stderr and not (main / "reports").exists()
    # 〔検収 L-g〕importcheck の結果の置き場も、本体の作業木の中なら断る(何も書かない)
    r = run_cli("importcheck", "--tree", str(tree), "--out", str(main / "ic.json"))
    assert r.returncode == 2 and "結果の置き場" in r.stderr and not (main / "ic.json").exists()


def test_bound_names_guard_catches_a_changed_binding():
    """〔突然変異 m14〕import の文が結ぶ名(別名を含む)が前後で違えば止める(直に呼ぶ・作った木)。頭から除いた再輸出の名だけは
    減ってよい。"""
    assert G.bound_names("from a import b as c\nimport x.y\nimport p.q as r\n") == Counter({"c": 1, "x": 1, "r": 1})
    before = Tree(files={"tests/t.py": "from shibuya.llm import contract\n", "src/shibuya/h/__init__.py":
                         "from shibuya.h.m import N\n"})
    good = Tree(files={"tests/t.py": "from shibuya.foundation.vocab import actions as contract\n",
                       "src/shibuya/h/__init__.py": ""})
    bad = Tree(files={"tests/t.py": "from shibuya.foundation.vocab import actions\n", "src/shibuya/h/__init__.py": ""})
    drop = {"src/shibuya/h/__init__.py": ["N"]}
    assert G.check_bound_names(before, good, {}, set(), drop) == []
    errs = G.check_bound_names(before, bad, {}, set(), drop)
    assert errs and errs[0].startswith("import の文が結ぶ名が変わった: tests/t.py")
    assert G.check_bound_names(before, good, {}, set(), {}) != []  # 除いた名と言わなければ頭の名の減りも止める


def test_negative_changing_the_names_bound_by_imports_is_stopped_in_a_plan(tmp_path, monkeypatch):
    """計画の中でも、別名を落とす書き手を差し込むと結ぶ名の守りが止める。次に当てる段で動くモジュールを別名で読む試験の
    ファイルを作った木で。"""
    stage = need_pending()[0]
    root = make_copy(tmp_path / "t")
    row = next(r for r in apply_rows(Tree.load(root), stage)
               if r.kind == "move" and not r.is_head and r.old.endswith(".py"))
    rel = "tests/zz_alias_case.py"
    (root / rel).write_text(f"import {mod_of(row.old)} as zz_alias\n", encoding="utf-8", newline="")
    plan = plan_for(root, (stage,))
    assert plan.after.files[rel] == f"import {mod_of(row.new)} as zz_alias\n"
    from pkgmove import imports as IM

    monkeypatch.setattr(IM, "_alias_text", lambda name, asname: name)
    with pytest.raises(MV.Stopped) as e:
        plan_for(root, (stage,))
    assert any(x.startswith("import の文が結ぶ名が変わった: " + rel) for x in e.value.errors), e.value.errors[:3]


def test_negative_class_ids_guard_catches_values_and_coverage(base_copy):
    """〔突然変異 m03・m20〕固定の表の値が凍結の写像と違う・表の鍵が src のクラスと合わない、を守りが見つける(直に呼ぶ)。"""
    fz = frozen_of(base_copy)
    t = Tree.load(base_copy)
    path = MV.locate(t, MAPDOC, AL.CLASS_IDS_TABLE[0])
    assert G.check_class_ids(t, fz, path) == []
    v = t.files[path]
    line = next(x for x in v.split("\n") if re.match(r'^    "shibuya\.[\w.]+": "shibuya\.[\w.]+",$', x))
    val = line.split(": ", 1)[1].rstrip(",").strip('"')
    t.files[path] = v.replace(line, line.replace(f': "{val}"', f': "{val}Klass"'), 1)
    assert any("凍結の写像と違う" in x for x in G.check_class_ids(t, fz, path))
    t.files[path] = "\n".join(x for x in v.split("\n") if x != line)
    assert any("src のクラスと合わない" in x for x in G.check_class_ids(t, fz, path))


def test_negative_names_guard_catches_version_ids_headers_and_rng_tables(base_copy):
    """〔突然変異 m21〕版の ID・ハッシュの見出し・乱数の領域の名の表の鍵が凍結と違えば、欄の名つきで見つける(直に呼ぶ)。"""
    fz = frozen_of(base_copy)
    base = Tree.load(base_copy)
    assert G.check_names(base, fz) == []
    vid = next(v for k, v in fz.names["version_ids"] if k == "s")
    head = fz.names["hash_headers"][0]
    dom = fz.names["rng_domains"]["POPULATION_RNG_DOMAINS"][0]
    for old, new, field in ((f'"{vid}"', f'"{vid}x"', "version_ids"), (f'b"{head}"', f'b"{head}x"', "hash_headers"),
                            (f'"{dom}":', f'"{dom}x":', "rng_domains")):
        t = base.copy()
        hit = [p for p, s in t.files.items() if p.startswith(SRC_PREFIX) and old in s]
        if field == "rng_domains":
            hit = [MV.locate(t, MAPDOC, "engine/run.py")]  # 表の定義の置き場(鍵の字面 ``"<名>":``)
        assert hit, old
        t.files[hit[0]] = t.files[hit[0]].replace(old, new, 1)
        errs = G.check_names(t, fz)
        assert any(field in x for x in errs), (field, errs)


def test_negative_shaped_74_guard_alone_catches_a_manifest_text(base_copy, monkeypatch):
    """〔突然変異 m04〕manifest に出る文の中の道の形(``engine/energy.py`` の見出しの項)を書き換える書き手を、その表の記号に
    差し込むと、74 種の守りだけが止める(斜線の道は凍結の字面の守りの外)。"""
    monkeypatch.setattr(ST, "rewrite_value", _naive({"engine/energy.py": "world/body/energy.py"}))
    extra = [AL.Site(MV.locate(Tree.load(base_copy), MAPDOC, "engine/body/rules.py"), "BODY_RULES", "paths")]
    with pytest.raises(MV.Stopped) as e:
        plan_for(base_copy, _any_stages(), extra_sites=extra)
    assert any(x.startswith("道の形の名(74 種)の出てくる数が変わった") for x in e.value.errors), e.value.errors
    assert not any("names_frozen" in x or "許可の一覧の外" in x for x in e.value.errors)


def test_negative_an_emptied_head_with_a_definition_is_stopped(tmp_path):
    """〔突然変異 m18・検収 L-f〕空にする頭に定義(関数・クラス)があれば止める。import・docstring・``__all__`` のほかの文
    (代入など)があっても止める(空にすると消える)。"""
    root = make_copy(tmp_path / "t")
    tree = Tree.load(root)
    heads = [(s, r) for s in pending() for r in apply_rows(tree, s) if r.is_head and r.kind in ("move", "empty", "delete")]
    if not heads:
        pytest.skip("空にする頭の行が残っていない木")
    stage, row = heads[0]
    h = root / SRC_PREFIX / row.old
    h.write_text(h.read_text(encoding="utf-8") + "\n\ndef helper():\n    return 1\n\n\nLIMIT = 3\n",
                 encoding="utf-8", newline="")
    with pytest.raises(MV.Stopped) as e:
        plan_for(root, (stage,))
    assert any("空にする頭に定義がある" in x and "helper" in x for x in e.value.errors)
    assert any("空にする頭に import・docstring・__all__ のほかの文がある" in x and "Assign@" in x for x in e.value.errors)


def test_imports_through_an_emptied_head_are_sent_to_the_defining_modules(staged):
    """〔突然変異 m12〕空にする頭を通る import は、定義したモジュールへ向く(頭から読んでよいのは子のモジュールだけ)。"""
    heads = {mod_of(h[len(SRC_PREFIX):]) for h in [*staged.emptied_heads, *staged.deleted]}
    ix = Index(staged.after)
    for path, t in staged.after.files.items():
        if path.startswith("tools/pkgmove/") or path == "tests/tools/test_pkgmove.py":
            continue
        for n in ast.walk(ast.parse(t)):
            if isinstance(n, ast.ImportFrom) and n.level == 0 and n.module in heads:
                assert all(ix.exists(f"{n.module}.{a.name}") for a in n.names), (path, n.lineno)


def test_imports_through_an_emptied_head_are_sent_to_the_defining_modules_in_a_sample():
    """〔突然変異 m12〕作った見本の木で(本物の tests の字面に寄りかからない): 空にする頭 ``shibuya.pk`` の再輸出を通る import は
    定義したモジュールへ向き、子のモジュールを読む import は子の新しい置き場へ向く。"""
    from pkgmove import imports as IM

    tree = Tree(files={"src/shibuya/__init__.py": "", "src/shibuya/pk/__init__.py": "from shibuya.pk.a import X\n",
                       "src/shibuya/pk/a.py": "X = 1\n", "src/shibuya/pk/b.py": "Y = 2\n"})
    ctx = Ctx(index=Index(tree), modmap={"shibuya.pk.a": "shibuya.qq.a", "shibuya.pk.b": "shibuya.qq.b"},
              heads_changed={"shibuya.pk"})
    code = "from shibuya.pk import X\nfrom shibuya.pk import b as BB\n\n\ndef f():\n    from shibuya.pk import X as Z\n    return Z\n"
    st = IM.ImportStats()
    out = apply_edits(code, IM.rewrite_file(ctx, "tests/x.py", code, ast.parse(code), {}, st))
    assert "from shibuya.pk import" not in out, out
    assert "from shibuya.qq.a import X\n" in out and "from shibuya.qq import b as BB\n" in out
    assert "    from shibuya.qq.a import X as Z\n" in out
    assert st.via_head >= 2


def test_every_rewritten_path_chain_points_to_a_file_in_the_applied_tree(staged):
    """〔突然変異 m28〕``/`` の結合を書き換えた所は、全部、当てた木で在るファイルを指す(書き換えなければ古い道=当てた木に無い
    ファイルを指す)。"""
    # 本数と特定のファイルは前提にしない(本物の木で結合が 0 本でも通る。書き換えの力は見本の木の試験=下で持つ)
    chains = [(p, e) for p, edits in staged.changed.items() for e in edits
              if e.kind == "path" and e.note.startswith("chain ")]
    for p, e in chains:
        rel = "/".join(x.strip().strip("\"'") for x in e.new.split("/"))
        assert (SRC_PREFIX + rel) in staged.after.files or (SRC_PREFIX + rel) in staged.after.blobs, (p, rel)
        old = e.note[len("chain "):]
        old_rel = old[len("src/shibuya/"):] if old.startswith("src/shibuya/") else old
        assert (SRC_PREFIX + old_rel) not in staged.after.files, (p, old)


def test_path_chains_over_several_constants_are_rewritten_in_a_sample():
    """〔突然変異 m28〕作った見本の木で: 2 つ以上の定数にまたがる ``/`` の結合を、道具の入口(許可の記号の中の文字列の書き換え)で
    新しい道の部品に書き換える。形は 2 つ=変数の後に道の部品だけが続く形と、変数の後に ``src``・``shibuya`` から始まる部品が
    続く形(道の頭が定数の途中から始まる)。古い道の部品は残らない。許可の一覧の外の記号の結合は書き換えない。"""
    ctx = Ctx(index=Index(Tree(files={"src/shibuya/__init__.py": ""})), modmap={}, heads_changed=set())
    rules = ST.PathRules(relmap={"engine/ledger_api.py": "foundation/ports/ledger.py"})
    code = ("def f(src, root):\n"
            "    a = src / \"engine\" / \"ledger_api.py\"\n"
            "    b = root / 'src' / 'shibuya' / 'engine' / 'ledger_api.py'\n"
            "    return a, b\n\n\n"
            "def g(src):\n"
            "    return src / \"engine\" / \"ledger_api.py\"\n")
    t = ast.parse(code)
    stats = ST.StrStats()
    edits = ST.rewrite_file_strings(ctx, rules, "tests/x.py", code, t, symbol_map(t), {"f": "paths"}, stats)
    out = apply_edits(code, edits)
    f_part, g_part = out.split("def g", 1)
    assert 'a = src / "foundation" / "ports" / "ledger.py"' in f_part
    assert "b = root / 'src' / 'shibuya' / 'foundation' / 'ports' / 'ledger.py'" in f_part
    assert "engine" not in f_part and "ledger_api" not in f_part
    assert 'return src / "engine" / "ledger_api.py"' in g_part  # 許可の一覧の外=そのまま
    assert len([e for e in edits if e.note.startswith("chain ")]) == 2
    ast.parse(out)


def test_split_import_keeps_the_comments_of_its_names():
    """〔突然変異 m13・L-9〕行き先が 2 つに分かれる文を作り直すとき、名の行の注・名の前の注だけの行・頭の行の注を残す。"""
    from pkgmove import imports as IM

    tree = Tree(files={"src/shibuya/__init__.py": "", "src/shibuya/pk/__init__.py":
                       "from shibuya.pk.a import X\nfrom shibuya.pk.b import Y\n",
                       "src/shibuya/pk/a.py": "X = 1\n", "src/shibuya/pk/b.py": "Y = 2\n"})
    ctx = Ctx(index=Index(tree), modmap={"shibuya.pk.a": "shibuya.qq.a"}, heads_changed={"shibuya.pk"})
    code = ("def f():\n    from shibuya.pk import (  # 頭の注\n        X,  # X の注\n        # Y の前の注\n        Y,\n"
            "    )  # 後ろ\n    return X\n")
    st = IM.ImportStats()
    out = apply_edits(code, IM.rewrite_file(ctx, "tests/x.py", code, ast.parse(code), {}, st))
    assert st.split == 1 and st.via_head == 1
    for c in ("# 頭の注", "# X の注", "# Y の前の注", "# 後ろ"):
        assert c in out, c
    assert "from shibuya.qq.a import (" in out and "from shibuya.pk.b import (" in out
    ast.parse(out)


def test_package_names_alone_are_not_rewritten_and_relative_imports_are_noted():
    """〔L-7〕包み(ディレクトリ)の名だけの点の文字列は、行き先が 1 つに決まらないので書き換えずに注意に出す(モジュールの名は
    書き換える)。〔L-5〕相対の import が移すファイルにかかれば注意に出す。作った木で。"""
    from pkgmove import imports as IM

    tree = Tree(files={"src/shibuya/__init__.py": "", "src/shibuya/pk/__init__.py": "", "src/shibuya/pk/a.py": "X = 1\n",
                       "src/shibuya/pk/b.py": "from .a import X\n"})
    ctx = Ctx(index=Index(tree), modmap={"shibuya.pk.a": "shibuya.qq.a", "shibuya.pk": "shibuya.qq",
                                         "shibuya.pk.b": "shibuya.qq.b"}, heads_changed={"shibuya.pk"})
    rules = ST.PathRules(relmap={"pk/a.py": "qq/a.py"})
    new, reps, skipped = ST.rewrite_value(ctx, rules, "shibuya.pk")
    assert new == "shibuya.pk" and reps == [] and skipped[0][0] == "dotted_package"
    new, _r, _s = ST.rewrite_value(ctx, rules, "shibuya.pk.a")
    assert new == "shibuya.qq.a"
    c2 = Ctx(index=Index(tree), modmap={"shibuya.pk.b": "shibuya.qq.b"}, heads_changed=set())
    st = IM.ImportStats()
    text = tree.files["src/shibuya/pk/b.py"]
    assert IM.rewrite_file(c2, "src/shibuya/pk/b.py", text, ast.parse(text), {}, st) == []
    assert any("相対の import" in w for w in st.warnings)


def test_negative_rewriting_a_docstring_in_an_allowlisted_symbol_is_stopped(tmp_path, monkeypatch):
    """〔突然変異 m29・L-9〕許可の一覧の記号の中でも docstring は書き換えない。作った試験のファイルの許可の記号(docstring と
    道の文字列を持つ)で: 道の文字列だけが書き換わり docstring は残る。docstring も書き換える書き手(docstring の見分けを外す)を
    差し込むと、許可の一覧の外の守り(docstring を比べる)が止める。"""
    root = make_copy(tmp_path / "t")
    tree = Tree.load(root)
    cand = [(s, r) for s in pending() for r in apply_rows(tree, s)
            if r.kind == "move" and not r.is_head and r.old.endswith(".py") and "/" in r.old]
    if not cand:
        pytest.skip("動かすファイルが残っていない木")
    stage, row = cand[0]
    rel = "tests/zz_docstring_case.py"
    old_path = f"src/shibuya/{row.old}"
    body = f'def f():\n    """see {old_path}"""\n    return "{old_path}"\n'
    (root / rel).write_text(body, encoding="utf-8", newline="")
    extra = [AL.Site(rel, "f", "paths")]
    plan = plan_for(root, (stage,), extra_sites=extra)
    assert plan.after.files[rel] == body.replace(f'return "{old_path}"', f'return "src/shibuya/{row.new}"')
    monkeypatch.setattr(ST, "docstrings_of", lambda text: frozenset())
    with pytest.raises(MV.Stopped) as e:
        plan_for(root, (stage,), extra_sites=extra)
    assert any(x.startswith("許可の一覧の外の定数が変わった: " + rel) for x in e.value.errors), e.value.errors[:3]


def test_outside_guard_compares_docstrings_inside_allowlisted_symbols():
    """〔L-9〕作った木で: 許可の記号の中の docstring が変われば止め、docstring でない文字列が変わるのは通す。"""
    before = Tree(files={"tests/t.py": 'def f():\n    """engine/clock.py の説明。"""\n    return "engine/clock.py"\n'})
    ok_after = Tree(files={"tests/t.py": 'def f():\n    """engine/clock.py の説明。"""\n    return "runtime/clock.py"\n'})
    bad_after = Tree(files={"tests/t.py": 'def f():\n    """runtime/clock.py の説明。"""\n    return "runtime/clock.py"\n'})
    allowed = {("tests/t.py", "f")}
    assert G.check_outside(before, ok_after, {}, allowed, set(), set(), set()) == []
    errs = G.check_outside(before, bad_after, {}, allowed, set(), set(), set())
    assert errs and errs[0].startswith("許可の一覧の外の定数が変わった")


# ------------------------------------------------------------------ 再検収の指摘(review3: L-a・頭の __all__・n05・n06・n07・n11・L-f・L-g)
def test_import_check_reimports_every_module_from_scratch(tmp_path):
    """〔検収 n05〕読む順でだけ循環が出る小さな木: ``a_pkg`` を先に読めば ``z_moved`` も読めるが、``z_moved`` を最初に読むと
    循環で落ちる。確かめは 1 つ読むたびに ``shibuya`` を ``sys.modules`` から外すので、``z_moved`` を落とす(同じ子のプロセスで
    順に読む ``jobs=1``)。"""
    from pkgmove import importcheck as IC

    root = _tiny_tree(tmp_path / "order", {
        "src/shibuya/__init__.py": "",
        "src/shibuya/a_pkg/__init__.py": "from shibuya.z_moved import THING\n",
        "src/shibuya/a_pkg/sib.py": "X = 1\n",
        "src/shibuya/z_moved.py": "from shibuya.a_pkg import sib\nTHING = sib.X\n",
    })
    assert IC.modules(root / "src") == ["shibuya", "shibuya.a_pkg", "shibuya.a_pkg.sib", "shibuya.z_moved"]
    doc = IC.check(root, jobs=1)
    assert set(doc["bad"]) == {"shibuya.z_moved"} and "ImportError" in doc["bad"]["shibuya.z_moved"]


def test_import_check_fails_when_it_reads_a_shibuya_outside_the_tree(tmp_path):
    """〔検収 n06〕木の ``src/shibuya`` に頭(``__init__.py``)が無いと、子は別の場所の ``shibuya``(editable の本体・無ければ
    名前空間の包み)を読む。確かめはそれを落ちたと数える。"""
    from pkgmove import importcheck as IC

    root = _tiny_tree(tmp_path / "other", {"src/shibuya/notes.txt": "no head"})
    doc = IC.check(root, jobs=1)
    assert "<shibuya>" in doc["bad"] and "木の src でない shibuya を読んだ" in doc["bad"]["<shibuya>"] and not IC.ok(doc)


def test_cache_only_dirs_are_pruned_and_namespace_leftovers_are_caught(tmp_path):
    """〔検収 L-a〕``__pycache__`` だけを持つ古い包みのディレクトリは名前空間の包みとして import できる=import の確かめが落とす。
    消す道具(``prune_cache_only_dirs``)は、それだけを消す(中身のあるディレクトリ・データのディレクトリは残す)。"""
    from pkgmove import importcheck as IC

    root = _tiny_tree(tmp_path / "ns", {
        "src/shibuya/__init__.py": "",
        "src/shibuya/old/__pycache__/gone.cpython-312.pyc": "x",
        "src/shibuya/old/deeper/__pycache__/gone2.cpython-312.pyc": "x",
        "src/shibuya/live/__init__.py": "",
        "src/shibuya/live/__pycache__/__init__.cpython-312.pyc": "x",
        "src/shibuya/data_dir/table.json": "{}",
    })
    doc = IC.check(root, jobs=1, gone=["shibuya.old", "shibuya.never_was"])
    assert set(doc["bad"]) == {"<名前空間> shibuya.old"} and doc["gone"] == 2
    removed = MV.prune_cache_only_dirs(root)
    assert removed == ["src/shibuya/old/deeper", "src/shibuya/old"]
    assert (root / "src/shibuya/live/__pycache__").is_dir() and (root / "src/shibuya/data_dir/table.json").is_file()
    assert IC.ok(IC.check(root, jobs=1, gone=["shibuya.old"]))
    assert MV.prune_cache_only_dirs(root) == []


def _find_spec_in(root: Path, names: list[str]) -> dict[str, bool]:
    code = ("import importlib.util, json, sys\nout = {}\nfor m in json.loads(sys.argv[1]):\n    try:\n"
            "        out[m] = importlib.util.find_spec(m) is not None\n    except (ImportError, ValueError):\n"
            "        out[m] = False\nprint(json.dumps(out))\n")
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env["PYTHONPATH"] = str(root / "src")
    r = subprocess.run([sys.executable, "-c", code, json.dumps(names)], capture_output=True, text=True, encoding="utf-8",
                       env=env, cwd=str(root))
    assert r.returncode == 0, r.stderr[-1000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_stacked_apply_prunes_old_package_dirs_and_returns_3_when_imports_fail(tmp_path):
    """〔検収 L-a・n07〕同じ木に段を重ねて当てる形: 前の import が作った ``__pycache__`` を全部のディレクトリに置いた木へ、次の
    段(残る最初の 2 段)を ``--apply`` する。① 移して無くなった包みのディレクトリは ``__pycache__`` ごと消え、古い包みの名は
    ``find_spec`` で ``None``。② 読めないモジュールを 1 本足しておくと、書いた後の import の確かめが落ちて終了コード 3
    (落ちたのはそのモジュールだけ=名前空間の残りは無い)。当てる段が無い木では ② だけ(行 0 の段)。"""
    root = make_copy(tmp_path / "t")
    base = root / "src" / "shibuya"
    for d in [base, *[p for p in base.rglob("*") if p.is_dir() and p.name != "__pycache__"]]:
        (d / "__pycache__").mkdir(exist_ok=True)
        (d / "__pycache__" / "zz_stale.cpython-312.pyc").write_bytes(b"stale")
    (base / "zz_broken.py").write_text("import shibuya.zz_does_not_exist\n", encoding="utf-8", newline="")
    stages = ",".join(pending()[:2]) or "foundation"
    out = tmp_path / "out"
    r = run_cli("move", "--stage", stages, "--apply", "--tree", str(root), "--out-dir", str(out), "--import-jobs", "4")
    assert r.returncode == 3, (r.stdout[-1500:], r.stderr[-1500:])
    assert "書いた後の import の確かめが落ちた" in r.stderr and "shibuya.zz_broken" in r.stderr
    tag = stages.replace(",", "_")
    doc = json.loads((out / f"pkgmove_{tag}_imports.json").read_text(encoding="utf-8"))
    assert set(doc["bad"]) == {"shibuya.zz_broken"}, doc["bad"]
    assert "消した古いディレクトリ" in r.stdout
    left = [p for p in base.rglob("*") if p.is_dir() and p.name != "__pycache__" and MV._cache_only(p)]
    assert left == [], left
    gone = MV.gone_packages(MAPDOC, root)
    assert doc["gone"] == len(gone)
    if pending()[:2] and gone:
        assert all(not v for v in _find_spec_in(root, gone).values())
        assert [g for g in gone if (root / "src" / g.replace(".", "/")).is_dir()] == []


def _bound_in_head(text: str) -> set[str]:
    t = ast.parse(text)
    out: set[str] = set()
    for n in ast.walk(t):
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n in t.body:
            out.add(n.name)
        elif isinstance(n, ast.ImportFrom):
            out |= {a.asname or a.name for a in n.names}
        elif isinstance(n, ast.Import):
            out |= {a.asname or a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.Assign):
            out |= {x.id for tg in n.targets for x in ast.walk(tg) if isinstance(x, ast.Name)}
    return out


def _all_of(text: str) -> list[str]:
    for n in ast.parse(text).body:
        if isinstance(n, ast.Assign) and any(isinstance(x, ast.Name) and x.id == "__all__" for x in n.targets):
            return [e.value for e in n.value.elts]
    return []


def test_head_all_drops_only_the_dropped_reexport_names(staged):
    """〔親の裁定 review3 の 2〕頭から除いた再輸出の名は、その頭の ``__all__`` からも除く。残る ``__all__`` は前の
    ``__all__`` から除いた名を抜いたもの(並びも同じ)で、名は全部その頭で結ばれている(別の実装で確かめる)。"""
    assert set(staged.dropped_all) <= set(staged.dropped_reexports)
    for h, names in staged.dropped_reexports.items():
        before, after = _all_of(staged.before.files[h]), _all_of(staged.after.files[h])
        assert after == [x for x in before if x not in set(names)], h
        assert staged.dropped_all.get(h, []) == [x for x in before if x in set(names)], h
        d = h[: -len("__init__.py")]
        unbound = [x for x in after if x not in _bound_in_head(staged.after.files[h])
                   and d + x + ".py" not in staged.after.files and d + x + "/__init__.py" not in staged.after.files]
        assert unbound == [], (h, unbound)
    assert staged.guards["head_all"].startswith("同じ")
    if staged.stages == ("foundation",):
        assert {k: len(v) for k, v in staged.dropped_all.items()} == {
            SRC_PREFIX + "engine/__init__.py": 9, SRC_PREFIX + "llm/__init__.py": 22, SRC_PREFIX + "perception/__init__.py": 30}
        text = staged.after.files[SRC_PREFIX + "llm/__init__.py"]
        assert '"ParseResult"' in text and '"ACTION_VOCAB_12"' not in text
        assert "# 行動契約(llm.contract の再輸出)" in text  # 注の行は残す(import の文と許可の行のほかは変えない)


def test_all_drops_keeps_comments_and_refuses_other_forms():
    """1 行 1 要素の行だけを除く(行の終わりの注は注の行として残す)。1 行に 2 つ以上の要素は除かずに注意(守りが止める)。"""
    from pkgmove import imports as IM
    from pkgmove.model import apply_edits

    text = '__all__ = [\n    # 注\n    "A",\n    "B",  # B の注\n    "C",\n]\n'
    edits, removed, warns = IM.all_drops("src/shibuya/h/__init__.py", text, ast.parse(text), ["B", "C"])
    assert removed == ["B", "C"] and warns == []
    assert apply_edits(text, edits) == '__all__ = [\n    # 注\n    "A",\n    # B の注\n]\n'
    inline = '__all__ = ["A", "B"]\n'
    edits, removed, warns = IM.all_drops("src/shibuya/h/__init__.py", inline, ast.parse(inline), ["B"])
    assert edits == [] and removed == [] and "1 行 1 要素の形でない" in warns[0]
    t = Tree(files={"src/shibuya/h/__init__.py": "from shibuya.h.m import A\n" + inline, "src/shibuya/h/m.py": "A = 1\n"})
    assert any("頭の __all__ に頭で結ばれない名がある: src/shibuya/h/__init__.py" in x for x in G.check_head_all(t))
    t.files["src/shibuya/h/__init__.py"] = "from shibuya.h.m import A\n__all__ = [\"A\", \"m\"]\n"
    assert G.check_head_all(t) == []  # 子のモジュールの名は結ばれていると見る


def test_negative_head_all_guards_stop_a_writer_that_keeps_or_overdrops_names(base_copy, staged, monkeypatch):
    """負の対照: ``__all__`` から除かない書き手を差し込むと「結ばれない名」で止まる。除いた名のほかの名まで除く書き手を
    差し込むと「除いた再輸出の名のほかで変わった」で止まる。"""
    if not staged.dropped_all:
        pytest.skip("次に当てる段に頭の再輸出を除く頭が無い")
    from pkgmove import imports as IM

    orig = IM.all_drops
    monkeypatch.setattr(IM, "all_drops", lambda path, text, tree, names: ([], [], []))
    with pytest.raises(MV.Stopped) as e:
        plan_for(base_copy, staged.stages)
    assert any(x.startswith("頭の __all__ に頭で結ばれない名がある") for x in e.value.errors), e.value.errors[:3]

    def overdrop(path, text, tree, names):
        extra = [x for x in (G.head_all_names(text) or []) if x not in set(names)][:1]
        return orig(path, text, tree, [*names, *extra])
    monkeypatch.setattr(IM, "all_drops", overdrop)
    with pytest.raises(MV.Stopped) as e:
        plan_for(base_copy, staged.stages)
    assert any(x.startswith("頭の __all__ が除いた再輸出の名のほかで変わった") for x in e.value.errors), e.value.errors[:3]
