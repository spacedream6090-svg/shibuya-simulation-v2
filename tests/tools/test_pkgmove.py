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
from pkgmove import split as SP  # noqa: E402
from pkgmove import strings as ST  # noqa: E402
from pkgmove.model import SRC_PREFIX, Ctx, Index, Tree, apply_edits, docstring_ids, mod_of, symbol_map  # noqa: E402
from pkgmove.table import (  # noqa: E402
    HELD, LATE_STAGES, MAP_REL, SPLIT_ENTRIES, SPLIT_FORWARDERS, STAGES, Row, build_map_text, forwarder_text, load_map,
    parse_table,
)

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
    for f in (*FROZEN_FILES, *AL.RECORD_TOOLS, "pyproject.toml"):
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
                        frozen=frozen_of(root), ledger_text=(root / MV.LEDGER_REL).read_text(encoding="utf-8"),
                        pyproject_text=_pyproject_of(root), **kw)


def _pyproject_of(root: Path) -> str | None:
    p = root / "pyproject.toml"
    return p.read_bytes().decode("utf-8") if p.is_file() else None


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
    # 〔割る段 5a の G0〕2 つ目以降の割り先 9 本と 18 本目(延ばした)の割り先 1 本の行(move の形・split_from)を足し、行 244 を
    # 割る行に替えた(18 本目は延ばしても割る行のまま=table.SPLIT_DEFERRED)。〔割る段 5b の G0〕2 つ目以降の割り先 6 本の行
    # (87a・141a・146a・207a・234a・234b)を足した(親の裁定 Q5)。〔割る段 6 の S6-G0・裁定 Q5〕2 つ目以降の新しい割り先 14 本の行
    # (225a〜225n)を足した。〔割る段 6 の M0〕延ばした 18 本目を割る段の順の 24 本目に載せた(行の数は変わらない)
    assert len(rows) == 358
    kinds = Counter(r.kind for r in rows)
    assert kinds == {"move": 235, "keep": 94, "split": 25, "delete": 2, "empty": 2}
    # 保留の一覧は 11-16 の答え(返事その 8 §1-6)で全部決着した=空
    assert {r.old: r.held for r in rows if r.held} == HELD == {}
    by = {r.old: r for r in rows}
    # 答えの後に移す行は、済んだ段と別の段: 連絡の器 4 本 → society(§1-6 の 1)・行 224a → foundation/arms/removed.py
    for f in ("calls", "chat_state", "deliver", "tools"):
        r = by[f"engine/contact/{f}.py"]
        assert (r.kind, r.package, r.new, r.stage) == ("move", "society", f"society/contact/{f}.py", "society_contact")
    r = by["engine/removed_switches.py"]
    assert (r.kind, r.package, r.new, r.stage) == ("move", "foundation", "foundation/arms/removed.py", "foundation_224a")
    assert {r.old: r.stage for r in rows if r.old in LATE_STAGES} == LATE_STAGES
    assert {r.stage for r in rows if r.stage} == set(STAGES)
    # 割る行(段 4 では動かさない)の割り先: apply_detection の (b)=act の側と mind/ops.py(§1-6 の 2)・入口=interfaces(§1-6 の 6)
    assert by["engine/resolve.py"].kind == "split"
    assert {"act/ops/detect_writes.py", "mind/ops.py"} <= set(by["engine/resolve.py"].split_to)
    # 〔割る段 6 の S6-G0・裁定 Q3〕S6-A で割った 2 つの関数を、それぞれの割り先に書き分けた(古い名 apply_detection は表に無い)
    nm = by["engine/resolve.py"].name_map
    assert (nm["write_b4_hash"], nm["write_intero_stages"]) == ("act/ops/detect_writes.py", "mind/ops.py")
    assert "apply_detection" not in nm and by["engine/resolve.py"].names_complete
    assert by["engine/run.py"].kind == "split" and "interfaces/cli/run_args.py" in by["engine/run.py"].split_to
    # 〔割る段 5b の G0・親の裁定 Q4〕run と commit の主な割り先を入れ替えた・入口の転送と入口の割り先の宣言は main の割り先
    assert by["engine/run.py"].new == "runtime/run.py" and by["engine/commit.py"].new == "act/commit.py"
    assert SPLIT_FORWARDERS == {"cli.py": by["cli.py"].new} == {"cli.py": by["cli.py"].name_map["main"]}
    assert SPLIT_ENTRIES == {"engine/run.py": by["engine/run.py"].name_map["main"]} == {"engine/run.py": "interfaces/cli/run_args.py"}
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


def test_held_rows_are_refused_in_a_sample():
    """〔11-16 の答えで table.HELD は空〕保留の仕組みは作った見本の対応表で確かめる: 名指しは断る・段を選べば保留の行を外して
    報告に出し、木の中では動かさない(保留でない行は動かす)。"""
    rows = [Row(num="1", old="pk/a.py", package="x", kind="move", new="qq/a.py", stage="foundation", held="問いの答え待ち"),
            Row(num="2", old="pk/b.py", package="x", kind="move", new="qq/b.py", stage="foundation")]
    md = MV.MapDoc(rows=rows)
    with pytest.raises(MV.Refused, match="保留の行は動かさない"):
        MV.select_rows(md, (), only=["pk/a.py"])
    cand, held = MV.select_rows(md, ("foundation",))
    assert [r.old for r in cand] == ["pk/b.py"] and [r.old for r in held] == ["pk/a.py"]
    tree = Tree(files={"src/shibuya/__init__.py": "", "src/shibuya/pk/__init__.py": "", "src/shibuya/pk/a.py": "A = 1\n",
                       "src/shibuya/pk/b.py": "from shibuya.pk.a import A\n"})
    plan = MV.make_plan(tree, md, ("foundation",))
    assert [r.old for r in plan.refused] == ["pk/a.py"] and plan.after.files["src/shibuya/pk/a.py"] == "A = 1\n"
    assert plan.after.files["src/shibuya/qq/b.py"] == "from shibuya.pk.a import A\n"
    assert "src/shibuya/pk/b.py" not in plan.after.files


def test_late_stage_rows_are_chosen_only_by_their_stage(base_copy):
    """〔段 4 の残り〕本物の対応表で: 答えの後の段は、その行だけを選ぶ(保留で外す行は 0)。済んだ段の名(society・foundation)は
    その行を選ばない(済んだ段を当て直さない)。割る行は保留が外れても名指しで動かさない(CLI は終了コード 2)。"""
    for stage in sorted(set(LATE_STAGES.values())):
        rows, held = MV.select_rows(MAPDOC, (stage,))
        assert {r.old for r in rows} == {o for o, s in LATE_STAGES.items() if s == stage} and held == []
    for stage in ("society", "foundation", "interim_bundles"):
        rows, held = MV.select_rows(MAPDOC, (stage,))
        assert not ({r.old for r in rows} & set(LATE_STAGES)) and held == []
    for old in ("engine/resolve.py", "engine/run.py"):
        with pytest.raises(MV.Refused, match="動かす行でない"):
            MV.select_rows(MAPDOC, (), only=[old])
    r = run_cli("move", "--stage", "foundation", "--only", "engine/run.py", "--tree", str(base_copy))
    assert r.returncode == 2 and "動かす行でない" in r.stderr


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
                                "import_names", "head_all", "package_data"}
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


_REC_TOOL = ('"""記録の道具の見本: src/shibuya/pk/a.py と shibuya.pk.a を読む。"""\n'
             "from shibuya.pk.a import X  # src/shibuya/pk/a.py の X\n"
             "import shibuya.pk.a as A\n\n"
             'PATH = "src/shibuya/pk/a.py"\n'
             'MOD = "shibuya.pk.a"\n'
             'CODE = "from shibuya.pk.a import X"\n\n\n'
             "def f():\n"
             '    """engine と同じ形の道 src/shibuya/pk/a.py を返す。"""\n'
             '    from shibuya.pk.a import X as Y  # 関数の中\n'
             '    return Y, "pk/a.py"\n')


def _rec_plan(**kw) -> MV.Plan:
    rel = "docs/bench/rec/tool.py"
    tree = Tree(files={"src/shibuya/__init__.py": "", "src/shibuya/pk/__init__.py": "", "src/shibuya/pk/a.py": "X = 1\n",
                       rel: _REC_TOOL})
    rows = [Row(num="1", old="pk/a.py", package="x", kind="move", new="qq/a.py", stage="foundation")]
    return MV.make_plan(tree, MV.MapDoc(rows=rows), ("foundation",), **kw)


def test_record_tools_get_only_their_import_statements_rewritten_in_a_sample():
    """〔親の決定 7・作った見本の木〕記録の道具に当たるファイル(docs の ``.py``・許可の一覧の外)では、import の文だけが書き換わり、
    同じ道を持つ文字列・注・docstring・コードの形の文字列は 1 バイトも変わらない。負の対照: その文字列の記号を許可の一覧に
    差し込むと(記録の道具の文字列も書き換える書き手)、変わったことを見つける。"""
    rel = "docs/bench/rec/tool.py"
    plan = _rec_plan()
    want = (_REC_TOOL.replace("from shibuya.pk.a import X  #", "from shibuya.qq.a import X  #")
            .replace("import shibuya.pk.a as A", "import shibuya.qq.a as A")
            .replace("    from shibuya.pk.a import X as Y", "    from shibuya.qq.a import X as Y"))
    assert plan.after.files[rel] == want
    assert {e.kind for e in plan.changed[rel]} == {"import"} and len(plan.changed[rel]) == 3
    bad = _rec_plan(extra_sites=[AL.Site(rel, "PATH", "paths"), AL.Site(rel, "f", "paths")])
    assert bad.after.files[rel] != want
    assert '"src/shibuya/qq/a.py"' in bad.after.files[rel] and "path" in {e.kind for e in bad.changed[rel]}


def test_skipping_the_next_stage_is_refused(base_copy):
    """〔検収 中-2〕本物の木で、次に当てる段を飛ばす計画は断る(書かない実行でも・CLI は終了コード 2)。次の段から順に
    まとめる計画と、済んだ段の名(行 0)は通る。当てる段が 2 つ残らない木では飛ばす(〔親の決定 12〕の「interim_bundles を飛ばして
    後で当てる」形は、段の順を当てた順に決めたので、今は断る側)。"""
    p = need_pending(2)
    with pytest.raises(MV.Refused, match="段の順が違う"):
        plan_for(base_copy, (p[1],))
    r = run_cli("move", "--stage", p[1], "--tree", str(base_copy))
    assert r.returncode == 2 and "段の順が違う" in r.stderr
    both = plan_for(base_copy, p[:2])
    assert {r.stage for r in both.rows_applied} == set(p[:2])
    done = tuple(s for s in STAGES if s not in p)
    if done:
        assert plan_for(base_copy, (done[-1],)).rows_applied == []


def test_done_stages_are_not_applied_again(base_copy):
    """〔段 4 の残り〕済んだ段(当てる行の残らない段)をまとめて当て直す計画は、行 0・書き換え 0・移動 0(済んだ段を壊さない)。
    まだどの段も当たっていない木では済んだ段が無い=飛ばす。"""
    done = tuple(s for s in STAGES if s not in pending())
    if not done:
        pytest.skip("済んだ段が無い木(段 3 の時点の木)")
    plan = plan_for(base_copy, done)
    assert plan.rows_applied == [] and plan.changed == {} and plan.file_moves == {}
    assert plan.created_heads == [] and plan.emptied_heads == [] and plan.deleted == []
    rows, _ = MV.select_rows(MAPDOC, done)
    assert len(plan.rows_already) == len(rows) > 0
    assert all(v.startswith("同じ") for v in plan.guards.values()), plan.guards


# 〔段 4 の残り〕答えの後の段の見本: 済んだ段の包み(society・foundation)へ後から移す行を別の段にした対応表
def _late_sample() -> tuple[Tree, MV.MapDoc]:
    rows = [Row(num="1", old="core/a.py", package="foundation", kind="move", new="foundation/a.py", stage="foundation"),
            Row(num="2", old="engine/clock.py", package="runtime", kind="move", new="runtime/clock.py", stage="runtime"),
            Row(num="3", old="engine/assemble.py", package="runtime", kind="move", new="runtime/systems/assemble.py",
                stage="runtime"),
            Row(num="4", old="engine/s.py", package="society", kind="move", new="society/s.py", stage="society"),
            Row(num="5", old="engine/m.py", package="mind", kind="move", new="mind/m.py", stage="mind"),
            Row(num="6", old="engine/contact/c.py", package="society", kind="move", new="society/contact/c.py",
                stage="society_contact"),
            Row(num="7", old="engine/contact/__init__.py", package="interim_bundles", kind="move",
                new="interim_bundles/contact/__init__.py", stage="interim_bundles", empty_head=True),
            Row(num="8", old="engine/contact/layer.py", package="interim_bundles", kind="move",
                new="interim_bundles/contact/layer.py", stage="interim_bundles"),
            Row(num="9", old="engine/removed.py", package="foundation", kind="move", new="foundation/arms/removed.py",
                stage="foundation_224a"),
            Row(num="10", old="census/__init__.py", package="消す", kind="delete", stage="delete"),
            Row(num="11", old="cli.py", package="interfaces", kind="split", new="interfaces/cli/main.py",
                split_to=("interfaces/cli/main.py",)),
            # 〔検収 低-6〕まだ移っていない読み手: 最終の置き場が runtime の割る行と、mind の割る行
            Row(num="12", old="engine/run.py", package="runtime", kind="split", new="runtime/result.py",
                split_to=("runtime/result.py", "interfaces/cli/run_args.py")),
            Row(num="13", old="engine/r.py", package="mind", kind="split", new="mind/r.py", split_to=("mind/r.py",))]
    files = {"src/shibuya/__init__.py": "", "src/shibuya/core/__init__.py": "", "src/shibuya/core/a.py": "A = 1\n",
             "src/shibuya/engine/__init__.py": "", "src/shibuya/engine/clock.py": "",
             "src/shibuya/engine/assemble.py": "from shibuya.engine.contact import layer\n",
             "src/shibuya/engine/s.py": "from shibuya.core.a import A\n", "src/shibuya/engine/m.py": "M = 1\n",
             "src/shibuya/engine/contact/__init__.py": "", "src/shibuya/engine/contact/c.py": "from shibuya.engine.s import A\n",
             "src/shibuya/engine/contact/layer.py": "from shibuya.engine.contact import c\nfrom shibuya.engine import removed\n",
             "src/shibuya/engine/removed.py": "R = 1\n", "src/shibuya/census/__init__.py": '"""census"""\n',
             "src/shibuya/cli.py": "from shibuya.engine.contact.layer import c\n",
             "src/shibuya/engine/run.py": "from shibuya.engine.contact import layer\n",
             "src/shibuya/engine/r.py": "from shibuya.engine.contact import layer\n"}
    return Tree(files=files), MV.MapDoc(rows=rows)


def test_late_stages_move_only_their_rows_and_the_tree_stage_follows_in_a_sample():
    """〔段 4 の残り・作った見本の木〕段を当てた順に 1 段ずつ当てると: 各段で動くのはその段の行だけ・前の段を当て直すと行 0・
    木の段(``contracts.stage_of``)はいま当てた段・import の文は新しい置き場を読む・全部をまとめて当てた木と同じ。"""
    from pkgmove import contracts as CT

    spec = CT.load_spec(ROOT / CT.CONTRACTS_REL)
    tree0, md = _late_sample()
    order = [s for s in STAGES if any(r.stage == s for r in md.rows)]
    assert order[-4:] == ["society_contact", "interim_bundles", "foundation_224a", "delete"]
    assert CT.stage_of(tree0, md, spec) == ""
    tree, done = tree0, []
    for s in order:
        plan = MV.make_plan(tree, md, (s,))
        assert sorted(r.num for r in plan.rows_applied) == sorted(r.num for r in md.rows if r.stage == s), s
        for d in done:
            assert MV.make_plan(plan.after, md, (d,)).rows_applied == [], (s, d)
        tree = plan.after
        done.append(s)
        assert CT.stage_of(tree, md, spec) == s, s
    f = tree.files
    assert f["src/shibuya/interim_bundles/contact/layer.py"] == (
        "from shibuya.society.contact import c\nfrom shibuya.foundation.arms import removed\n")
    assert f["src/shibuya/society/contact/c.py"] == "from shibuya.society.s import A\n"
    assert f["src/shibuya/runtime/systems/assemble.py"] == "from shibuya.interim_bundles.contact import layer\n"
    assert f["src/shibuya/society/contact/__init__.py"] == "" and f["src/shibuya/foundation/arms/__init__.py"] == ""
    assert "src/shibuya/engine/contact/__init__.py" not in f and "src/shibuya/census/__init__.py" not in f
    together = MV.make_plan(tree0, md, tuple(order)).after
    assert together.files == tree.files and together.blobs == tree.blobs


def test_section_6_6_rules_come_in_at_their_stages_in_a_sample():
    """〔段 4 の残り・作った見本の木〕§6-6 の決まりは入れる段から: 一時の区分の読み手の決まり(9)は interim_bundles の段から
    (読んでよい側=runtime と、まだ移っていない読み手で最終の置き場が interfaces の cli)・runtime の核の決まり(10)は delete の
    段から(直の辺だけを見る=節に allow_indirect_imports)。前の段では報告の not_expressed に段の名つきで出る。"""
    from pkgmove import contracts as CT

    spec = CT.load_spec(ROOT / CT.CONTRACTS_REL)
    tree, md = _late_sample()
    seen: dict[str, tuple[list[dict], dict]] = {}
    for s in [s for s in STAGES if any(r.stage == s for r in md.rows)]:
        tree = MV.make_plan(tree, md, (s,)).after
        seen[s] = CT.build(spec, md, tree, s)
    name9 = "〔段 4 の途中の決まり〕§6-6 の 1 "
    name10 = "〔段 4 の途中の決まり〕§6-6 の 2 "
    for s, (contracts, rep) in seen.items():
        has9 = any(c["name"].startswith(name9) for c in contracts)
        has10 = any(c["name"].startswith(name10) for c in contracts)
        after_ib = STAGES.index(s) >= STAGES.index("interim_bundles")
        assert has9 == after_ib and has10 == (s == "delete"), s
        if not after_ib and STAGES.index(s) > STAGES.index(spec.old_only_through):
            assert {"rule": 9, "name": spec.rules[8]["name"], "why": "段 interim_bundles から入れる"} in rep["not_expressed"]
    contracts, rep = seen["delete"]
    c9 = next(c for c in contracts if c["name"].startswith(name9))
    assert c9["type"] == "protected" and c9["protected_modules"] == ["shibuya.interim_bundles"]
    # 読んでよい側=runtime と、最終の置き場が runtime・interfaces のまだ移っていない読み手だけ(最終が mind の engine.r は
    # 一時の区分を読んでいても足さない=〔検収 低-6〕)
    assert c9["allowed_importers"] == ["shibuya.runtime", "shibuya.cli", "shibuya.engine.run"]
    c10 = next(c for c in contracts if c["name"].startswith(name10))
    assert c10["source_modules"] == ["shibuya.runtime.clock"] and c10["allow_indirect_imports"] is True
    assert "shibuya.interim_bundles" in c10["forbidden_modules"] and "shibuya.society" in c10["forbidden_modules"]
    text = CT.render(spec, "delete", contracts)
    assert "allow_indirect_imports = true" in text
    assert CT.section_dict(text)["contracts"][-1]["allow_indirect_imports"] is True


def test_skipped_or_reversed_stages_are_refused_in_a_sample():
    """〔検収 中-2・作った見本の木〕段を飛ばす・逆の順の計画は断る(``Refused``=CLI の終了コード 2)。次の段から順にまとめる計画と、
    済んだ段の名で当て直す計画(行 0)は通る。段を飛ばした木(段の行だけの対応表=断らない書き手で作った)は、木の段が分からない
    =``tree_stage`` も ``contracts.stage_of`` も ``None`` で、次の段も断る。"""
    from pkgmove import contracts as CT

    spec = CT.load_spec(ROOT / CT.CONTRACTS_REL)
    tree0, md = _late_sample()
    order = [s for s in STAGES if any(r.stage == s for r in md.rows)]
    with pytest.raises(MV.Refused, match="段の順が違う"):
        MV.make_plan(tree0, md, (order[1],))
    k = order.index("society_contact")
    tree = tree0
    for s in order[:k]:
        tree = MV.make_plan(tree, md, (s,)).after
    assert MV.tree_stage(tree, md) == order[k - 1] == CT.stage_of(tree, md, spec)
    with pytest.raises(MV.Refused, match="段の順が違う"):  # society_contact を飛ばす
        MV.make_plan(tree, md, ("interim_bundles",))
    with pytest.raises(MV.Refused, match="段の順が違う"):  # 2 つ先の段まで飛ばしてまとめる
        MV.make_plan(tree, md, ("society_contact", "foundation_224a"))
    ok = MV.make_plan(tree, md, ("interim_bundles", "society_contact"))  # 次の段から順の 2 段(渡す並びは問わない)
    assert MV.tree_stage(ok.after, md) == "interim_bundles" == CT.stage_of(ok.after, md, spec)
    assert MV.make_plan(ok.after, md, ("society", "society_contact")).rows_applied == []  # 済んだ段の名=行 0
    with pytest.raises(MV.Refused, match="段の順が違う"):  # foundation_224a より先に delete
        MV.make_plan(ok.after, md, ("delete",))
    only_ib = MV.MapDoc(rows=[r for r in md.rows if r.stage == "interim_bundles" or r.kind in ("split", "keep")])
    skipped = MV.make_plan(tree, only_ib, ("interim_bundles",)).after
    assert MV.tree_stage(skipped, md) is None and CT.stage_of(skipped, md, spec) is None
    with pytest.raises(MV.Refused, match="木の段が段の順と合わない"):
        MV.make_plan(skipped, md, ("society_contact",))
    with pytest.raises(CT.ContractsError, match="食い違う"):
        CT.build(spec, md, skipped, "interim_bundles")


def test_effective_ignores_count_only_the_lines_that_stop_a_violation_in_a_sample(tmp_path):
    """〔検収 中-1・作った見本の包み〕効いている例外=外すとその契約が broken になる行。何も止めていない例外(層の外のモジュール
    からの辺)は数えない。延べと重なりを除いた数・消える段ごとの数・まとめて外しても kept か。木には何も書かない。"""
    from pkgmove import contracts as CT

    files = {"src/shibuya/__init__.py": "", "src/shibuya/high.py": "H = 1\n",
             "src/shibuya/low.py": "from shibuya.high import H\n", "src/shibuya/mid.py": "from shibuya import low\n"}
    for rel, text in files.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(text, encoding="utf-8", newline="")
    before = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*"))
    contracts = [{"name": "層", "type": "layers", "layers": ["shibuya.high", "shibuya.low"],
                  "ignore_imports": ["shibuya.low -> shibuya.high", "shibuya.mid -> shibuya.low"]},
                 {"name": "low は high を読まない", "type": "forbidden", "source_modules": ["shibuya.low"],
                  "forbidden_modules": ["shibuya.high"], "ignore_imports": ["shibuya.low -> shibuya.high"]}]
    rep = {"ignores": [{"importer": "shibuya.low", "imported": "shibuya.high", "gone_at": "段 6"},
                       {"importer": "shibuya.mid", "imported": "shibuya.low", "gone_at": "段 5a"}]}
    spec = CT.load_spec(ROOT / CT.CONTRACTS_REL)
    eff = CT.effective_ignores(tmp_path, spec, contracts, rep)
    assert (eff["base_kept"], eff["lines"], eff["unique"], eff["jointly_kept"]) == (True, 2, 1, True)
    assert eff["not_effective"] == ["shibuya.mid -> shibuya.low"] and eff["gone_at"] == {"段 6": 1}
    assert CT.ignore_counts(contracts, rep)["ignore_unique"] == 2  # 載せた数は 2(効いているのは 1)
    assert sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*")) == before  # 木に何も書かない
    # 負の対照: 効いている例外を載せない契約は基準が broken
    assert CT.effective_ignores(tmp_path, spec, [dict(contracts[1], ignore_imports=[])], rep)["base_kept"] is False


def test_ignore_counts_count_lines_unique_edges_and_where_they_go():
    """例外の数(返事その 8 §1-12 の 3): 延べの行・重なりを除いた辺・重なりを除いた辺の消える段ごとの数(載せなかった行は数えない)。"""
    from pkgmove import contracts as CT

    contracts = [{"ignore_imports": ["a -> b", "c -> d"]}, {"ignore_imports": ["a -> b"]}, {"name": "x"}]
    rep = {"ignores": [{"importer": "a", "imported": "b", "gone_at": "段 6"},
                       {"importer": "x", "imported": "y", "gone_at": "段 7", "skipped": "辺が無い"}],
           "ignores_66": [{"importer": "c", "imported": "d", "gone_at": "段 5a"}], "extra_ignores": []}
    assert CT.ignore_counts(contracts, rep) == {"ignore_lines": 3, "ignore_unique": 2,
                                                 "ignore_gone_at": {"段 5a": 1, "段 6": 1}}


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
    ファイルを作った木で(当てる段のうち、動かすファイルのある最初の段=delete の段だけが残る木では飛ばす)。"""
    need_pending()
    root = make_copy(tmp_path / "t")
    tree = Tree.load(root)
    cand = [(s, r) for s in pending() for r in apply_rows(tree, s)
            if r.kind == "move" and not r.is_head and r.old.endswith(".py")]
    if not cand:
        pytest.skip("当てる段に動かすファイルが無い木(delete の段だけが残る木)")
    stage, row = cand[0]
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
        if field == "rng_domains":  # 表の定義の置き場(鍵の字面 ``"<名>":``)
            # 〔割る段 5b の G2〕割る段で表の置き場が変わる(engine/run.py → runtime/run.py)=表の名を頂上で定義するファイルを引く
            hit = [p for p, s in t.files.items() if p.startswith(SRC_PREFIX) and "POPULATION_RNG_DOMAINS" in s
                   and "POPULATION_RNG_DOMAINS" in SP.top_names(s)]
            assert len(hit) == 1, hit
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
    with pytest.raises(MV.Stopped) as e:  # 〔検収 中-2〕頭の段の前の段から順に当てる計画で(段を飛ばすと断る)
        plan_for(root, pending()[: pending().index(stage) + 1])
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


# ------------------------------------------------------------------ 段ごとの import の決まり(brief_contracts・親の決定)
def _plan_text() -> str:
    return (ROOT / "docs/reference/package-map-final-2026-11-09.md").read_text(encoding="utf-8")


def test_contracts_toml_matches_the_plan_tables():
    """元のファイルの層は計画 §1-2 の図、28 本は §6-4 の表と同じ(写しの誤りを止める)。決まりは 1〜8。"""
    from pkgmove import contracts as CT

    spec = CT.load_spec(ROOT / CT.CONTRACTS_REL)
    t = _plan_text()
    block = t.split("### 1-2", 1)[1].split("```text", 1)[1].split("```", 1)[0]
    lay = [x.split("←")[0].strip() for x in block.splitlines() if x.strip() and not x.startswith("build")]
    assert spec.layers == lay and spec.side == ["build"]
    sec = t.split("### 6-4", 1)[1].split("### 6-5", 1)[0]
    rows = re.findall(r"^\| (\d+) \| `([\w.]+)` \| `([\w.]+)` \| (頭|関数の中) \| ([\d・]+) \| .*? \| (.*?) \| .*? \|$", sec, re.M)
    want = [(int(n), a, b, f, [int(x) for x in r.split("・")], g) for n, a, b, f, r, g in rows]
    got = [(g["num"], g["importer"], g["imported"], g["form"], list(g["rules"]), g["gone_at"]) for g in spec.ignores]
    assert len(want) == 28 and got == want
    assert [r["id"] for r in spec.rules] == list(range(1, 11))  # §6-4 の 1〜8 と §6-6 の 2 つ(9・10)
    # 計画の表の外の辺は、親の仮採用(2026-11-11・判断 1=候補 A)の 1 本だけ(増やせば落ちる)
    assert [(e["importer"], e["imported"], list(e["rules"])) for e in spec.extras] == [("llm", "llm.fleet", [1, 3])]
    assert all(w in spec.extras[0]["note"] for w in ("段 5a で消える", "28 本の外", "親の仮採用"))
    # §6-6 の 2 の表(核の候補 → 読む先)は計画の表と同じ(名は最終の置き場)。決まり 10 にだけ載せる
    sec66 = t.split("### 6-6", 1)[1].split("## 7.", 1)[0]
    rows66 = re.findall(r"^\| `(runtime/[\w/]+)\.py`[^|]* \| `([\w/]+)\.py`[^|]* \| `(\w+)` \| .*? \|$", sec66, re.M)
    assert [(a.replace("/", "."), b.replace("/", ".")) for a, b, _n in rows66] == [
        (g["importer"], g["imported"]) for g in spec.ignores66] and len(rows66) == 3
    assert all(list(g["rules"]) == [10] for g in spec.ignores66)
    # 段の順は当てた順(道具の STAGES と同じ)。答えの後の 4 段は validation の後・delete が最後
    assert spec.stage_order == STAGES
    assert STAGES[-4:] == ("society_contact", "interim_bundles", "foundation_224a", "delete")


def test_pyproject_section_is_the_one_made_for_the_tree_stage():
    """木の pyproject の [tool.importlinter] の節は、木の段の作り直しと同じ(段 4 の各段の commit で作り直す)。どの段も当たって
    いない木は今の 5 つの決まり。段の境目でない木は飛ばす。"""
    from pkgmove import contracts as CT

    spec = CT.load_spec(ROOT / CT.CONTRACTS_REL)
    tree = _root_tree()
    stage = CT.stage_of(tree, MAPDOC, spec)
    # 〔検収 中-2〕本物のリポの木は、段を順に当てて commit した木だけ=段が分からない(None)のは段を飛ばすか逆の順で当てた木
    # なので落とす(前は飛ばしていた)。段の途中の木は commit しない(道具は段ごとに当てる)。見本の木の None は別の試験で見る
    assert stage is not None, "木の段が段の順と合わない(段を飛ばしたか、逆の順で当てた木)"
    assert MV.tree_stage(tree, MAPDOC) == stage
    _head, cur = CT.split_pyproject((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    if stage == "":
        contracts = CT.old_contracts(spec)
        stage_name = "(移す前)"
    else:
        contracts, _rep = CT.build(spec, MAPDOC, tree, stage)
        stage_name = stage
    assert CT.same_section(cur, CT.render(spec, stage_name, contracts)), stage_name
    names = {m for c in contracts for k in ("layers", "source_modules", "forbidden_modules", "protected_modules",
                                            "allowed_importers") for x in c.get(k, []) for m in x.split(" | ")}
    names |= {m for c in contracts for x in c.get("ignore_imports", []) for m in x.split(" -> ")}
    ix = Index(tree)
    assert sorted(n for n in names if not ix.exists(n)) == []


def _ct_sample_tree() -> tuple[Tree, MV.MapDoc]:
    rows = [Row(num="1", old="core/rng.py", package="foundation", kind="move", new="foundation/rng.py", stage="foundation"),
            Row(num="2", old="world/state.py", package="world", kind="move", new="world/model/state.py", stage="world"),
            Row(num="3", old="engine/body/rules.py", package="world", kind="move", new="world/body/rules.py",
                stage="world"),
            Row(num="4", old="engine/clock.py", package="runtime", kind="move", new="runtime/clock.py", stage="runtime"),
            Row(num="5", old="economy/wages.py", package="economy", kind="keep", new="economy/wages.py"),
            Row(num="6", old="build/x.py", package="build", kind="keep", new="build/x.py"),
            Row(num="7", old="engine/run.py", package="runtime", kind="split", new="runtime/result.py",
                split_to=("runtime/result.py", "runtime/run.py"))]
    files = {"src/shibuya/__init__.py": "", "src/shibuya/foundation/__init__.py": "", "src/shibuya/foundation/rng.py": "",
             "src/shibuya/world/__init__.py": "", "src/shibuya/world/model/__init__.py": "",
             "src/shibuya/world/model/state.py": "from shibuya.foundation import rng\n",
             "src/shibuya/world/body/__init__.py": "", "src/shibuya/world/body/rules.py": "import shibuya.engine.clock\n",
             "src/shibuya/engine/__init__.py": "", "src/shibuya/engine/clock.py": "", "src/shibuya/engine/run.py": "",
             "src/shibuya/economy/__init__.py": "", "src/shibuya/economy/wages.py": "",
             "src/shibuya/build/__init__.py": "", "src/shibuya/build/x.py": ""}
    return Tree(files=files), MV.MapDoc(rows=rows)


def test_contracts_name_only_modules_in_the_tree_and_drop_changed_old_names():
    """〔作った見本の木・world の段〕作った節に、木に無い包みの名は入らない。古い決まりは、無くなった名(core・manifest ほか)と
    意味が変わった名(engine から world/body へファイルが入った world)を外し、外した名を報告に出す。新しい決まりは最終の名に
    在る単位だけ(runtime はまだ移っていない=言わない)。木の当たっている行が段と食い違えば断る。"""
    from pkgmove import contracts as CT

    spec = CT.load_spec(ROOT / CT.CONTRACTS_REL)
    tree, md = _ct_sample_tree()
    contracts, rep = CT.build(spec, md, tree, "world")
    ix = Index(tree)
    names = {m for c in contracts for k in ("layers", "source_modules", "forbidden_modules", "protected_modules",
                                            "allowed_importers") for x in c.get(k, []) for m in x.split(" | ")}
    assert names and sorted(n for n in names if not ix.exists(n)) == []
    assert "shibuya.runtime" not in names and "shibuya.core" not in names
    new_layers = next(c for c in contracts if c["name"].startswith("〔段 4 の途中の決まり〕1 "))["layers"]
    assert new_layers == ["shibuya.world.body", "shibuya.world.model | shibuya.economy", "shibuya.foundation"]
    old_layers = next(c for c in contracts if c["type"] == "layers" and not c["name"].startswith("〔"))["layers"]
    assert old_layers == ["shibuya.economy", "shibuya.engine"]
    dropped = {(d["name"], d["why"]) for d in rep["dropped_old"]}
    assert ("world", "名の意味が変わった(ほかの置き場からファイルが入った)") in dropped and ("core", "木に無い") in dropped
    assert all(g.get("skipped") for g in rep["ignores"])  # 28 本の対はこの木に無い=載せない
    assert not any("ignore_imports" in c for c in contracts)
    with pytest.raises(CT.ContractsError, match="食い違う"):
        CT.build(spec, md, tree, "runtime")
    text = CT.render(spec, "world", contracts)
    assert CT.same_section(text, text) and CT.section_dict(text)["root_package"] == "shibuya"


def test_contracts_cli_refuses_a_main_worktree(tmp_path):
    """``contracts --apply`` も本体の作業木へは書かない(move --apply と同じ守り)。"""
    main = tmp_path / "main"
    main.mkdir()
    _git(main, "init", "-q")
    r = run_cli("contracts", "--stage", "foundation", "--tree", str(main), "--apply")
    assert r.returncode == 2 and "本体の作業木" in r.stderr


# ------------------------------------------------------------------ pyproject の package-data の鍵(親の裁定 2026-11-11・判断 2)
def test_package_data_key_moves_with_the_json(base_copy):
    """(f) 凍結の JSON が移る段で、package-data の鍵を新しい包みの名にする(glob はそのまま・ほかの行は変えない)。JSON が
    もう移った木では、今の鍵が木に在る包みで glob が当たる。"""
    from pkgmove import pkgdata as PD

    row = next(r for r in MAPDOC.rows if r.old == "manifest/frozen/world_catalog_v0_2.json")
    text = _pyproject_of(base_copy)
    if row.stage in pending():
        plan = plan_for(base_copy, pending()[: pending().index(row.stage) + 1])
        new_key = mod_of(row.new.rsplit("/", 2)[0] + "/__init__.py")
        assert PD.entries(plan.pyproject_after) == {**{k: v for k, v in PD.entries(text).items() if k != "shibuya.manifest"},
                                                    new_key: ["frozen/*.json"]}
        assert ("shibuya.manifest", new_key) in plan.package_data_keys
        assert plan.guards["package_data"].startswith("同じ")
        changed = [(a, b) for a, b in zip(text.splitlines(), plan.pyproject_after.splitlines()) if a != b]
        assert changed == [('"shibuya.manifest" = ["frozen/*.json"]', f'"{new_key}" = ["frozen/*.json"]')]
    else:
        assert PD.check(text, Tree.load(base_copy)) == []


def test_package_data_rewrite_and_guard_in_a_sample():
    """作った見本の木で: 無くなる包みの鍵だけを、ファイルが同じ形で移った 1 つの包みへ書き換える。ほかの節の行(filterwarnings)は
    変えない。守り: 木に無い包みの鍵・どれにも当たらない glob を見つける。行き先が 2 つに分かれれば書き換えない。"""
    from pkgmove import pkgdata as PD

    text = ('[tool.setuptools.package-data]\n"shibuya.old" = ["frozen/*.json"]\n"shibuya.keep" = ["*.txt"]\n\n'
            '[tool.pytest.ini_options]\nfilterwarnings = ["error::DeprecationWarning:shibuya.old.*"]\n')
    before = Tree(files={"src/shibuya/__init__.py": "", "src/shibuya/old/__init__.py": "", "src/shibuya/keep/__init__.py": ""},
                  blobs={"src/shibuya/old/frozen/a.json": b"{}", "src/shibuya/keep/n.txt": b"x"})
    after = Tree(files={"src/shibuya/__init__.py": "", "src/shibuya/new/pk/__init__.py": "", "src/shibuya/keep/__init__.py": ""},
                 blobs={"src/shibuya/new/pk/frozen/a.json": b"{}", "src/shibuya/keep/n.txt": b"x"})
    moves = {"src/shibuya/old/frozen/a.json": "src/shibuya/new/pk/frozen/a.json"}
    out, keys, warns = PD.rewrite(text, before, after, moves)
    assert keys == [("shibuya.old", "shibuya.new.pk")] and warns == []
    assert out == text.replace('"shibuya.old" = ["frozen/*.json"]', '"shibuya.new.pk" = ["frozen/*.json"]')
    assert 'filterwarnings = ["error::DeprecationWarning:shibuya.old.*"]' in out
    assert PD.check(out, after) == []
    assert PD.check(text, after) == ["package-data の鍵の包みが木に無い: shibuya.old"]
    bad_glob = out.replace('["*.txt"]', '["*.csv"]')
    assert PD.check(bad_glob, after) == ["package-data の glob がどのファイルにも当たらない: shibuya.keep ['*.csv']"]
    before2 = Tree(files=before.files, blobs={**before.blobs, "src/shibuya/old/frozen/b.json": b"{}"})
    after2 = Tree(files={**after.files, "src/shibuya/other/__init__.py": ""},
                  blobs={**after.blobs, "src/shibuya/other/frozen/b.json": b"{}"})
    out2, keys2, warns2 = PD.rewrite(text, before2, after2, {**moves, "src/shibuya/old/frozen/b.json":
                                                             "src/shibuya/other/frozen/b.json"})
    assert out2 == text and keys2 == [] and "行き先が 1 つに決まらない" in warns2[0]


def test_negative_a_plan_that_does_not_rewrite_package_data_is_stopped(base_copy, monkeypatch):
    """負の対照: package-data の鍵を書き換えない書き手を差し込むと、JSON が移る段で守りが止める。"""
    from pkgmove import pkgdata as PD

    row = next(r for r in MAPDOC.rows if r.old == "manifest/frozen/world_catalog_v0_2.json")
    if row.stage not in pending():
        pytest.skip("凍結の JSON がもう移った木")
    monkeypatch.setattr(PD, "rewrite", lambda text, before, after, moves: (text, [], []))
    with pytest.raises(MV.Stopped) as e:
        plan_for(base_copy, pending()[: pending().index(row.stage) + 1])
    assert any("package-data の鍵の包みが木に無い: shibuya.manifest" in x for x in e.value.errors), e.value.errors[:3]


# ------------------------------------------------------------------ 検収 第 3 回(M-1・M-2・L-5)
#: 計画 §6-4 の決まり 2〜8 の文から読んだ型と名の並び(この表は toml から作らない。計画の文の語と下の試験で照らす)。
_PLAN_RULES = {
    2: ("forbidden", {"source": ["foundation"], "forbidden_all_except": ["foundation"]}),
    3: ("forbidden", {"source": ["mind"], "forbidden_all_except": ["foundation", "mind"]}),
    4: ("protected", {"protected": ["act.apply", "act.ops"],
                      "allowed": ["act", "world.laws", "interim_bundles", "runtime", "interfaces"]}),
    5: ("protected", {"protected": ["economy.ops", "economy.goods", "economy.ledger"], "allowed": ["economy", "interfaces"]}),
    6: ("forbidden", {"source": ["economy"], "forbidden_all_except": ["world.facts", "foundation", "economy"]}),
    7: ("forbidden", {"source": ["society"], "forbidden": ["act", "mind", "runtime", "world.laws", "interim_bundles"]}),
    8: ("forbidden", {"source_all_except": ["build"], "forbidden": ["build"]}),
}


def test_contract_rules_are_the_plan_sentences():
    """〔検収 M-1・L-7〕決まり 1〜8 の名は計画 §6-4 の文そのまま(番号つき)。決まり 2〜8 の型と名の並びは、試験の中の表
    (計画の文から読んだもの)と同じで、表の名は全部、その決まりの計画の文に出てくる。"""
    from pkgmove import contracts as CT

    spec = CT.load_spec(ROOT / CT.CONTRACTS_REL)
    sec = _plan_text().split("### 6-4", 1)[1].split("### 6-5", 1)[0]
    lines = {int(n): t for n, t in re.findall(r"^([1-8])\. (.+)$", sec, re.M)}
    rules = {r["id"]: r for r in spec.rules}
    assert {i: rules[i]["name"] for i in range(1, 9)} == {n: f"{n} {t}" for n, t in lines.items()}
    assert spec.rules[0]["type"] == "layers" and set(spec.rules[0]) == {"id", "type", "name"}
    for i in range(2, 9):
        r = rules[i]
        typ, body = _PLAN_RULES[r["id"]]
        assert r["type"] == typ, r["id"]
        assert {k: v for k, v in r.items() if k not in ("id", "name", "type")} == body, r["id"]
        for names in body.values():
            for x in names:
                assert x in lines[r["id"]], (r["id"], x)
    # §6-6 の 2 つ(返事その 8 §1-6 の 7・3): 名は計画の太字の文・中身は計画の文の名と同じ・入れる段
    sec66 = _plan_text().split("### 6-6", 1)[1].split("## 7.", 1)[0]
    s66 = {int(n): (b, rest) for n, b, rest in re.findall(r"^([12])\. \*\*(.+?)\*\*(.+)$", sec66, re.M)}
    # 決まり 10 は直の辺だけを見る(検収 中-3)=名にそう書く
    assert rules[9]["name"] == f"§6-6 の 1 {s66[1][0]}" and rules[10]["name"] == f"§6-6 の 2 {s66[2][0]}(直の辺だけ)"
    r9 = rules[9]
    assert (r9["type"], r9["protected"], r9["allowed"], r9["from_stage"]) == (
        "protected", ["interim_bundles"], ["runtime", "interfaces"], "interim_bundles")
    assert "protected" in s66[1][1] and all(x in s66[1][0] for x in ("runtime", "interfaces"))
    r10 = rules[10]
    assert (r10["type"], r10["allow_indirect_imports"], r10["from_stage"]) == ("forbidden", True, "delete")
    core = []
    for span in re.findall(r"`(runtime/[^`]+)`", s66[2][1].split("【見立て】")[0]):
        m = re.fullmatch(r"(runtime/[\w/]+)/\{([\w,]+)\}\.py", span)
        core += [f"{m.group(1)}/{x}" for x in m.group(2).split(",")] if m else [span.removesuffix(".py").removesuffix("/*")]
    assert r10["source_names"] == [x.replace("/", ".") for x in core]
    content = re.search(r"中身の包み[((]([\w・]+)[))]", s66[2][1]).group(1).split("・")
    assert sorted({x.split(".")[0] for x in r10["forbidden"]}) == sorted(content)
    units = CT.load_spec(ROOT / CT.CONTRACTS_REL).units
    assert sorted(r10["forbidden"]) == sorted(u for u in units if u.split(".")[0] in content)


def _pd_sample(root: Path) -> tuple[Tree, MV.MapDoc, str]:
    # 消す頭は中身がある形(空の頭は「消す行が当たっている」と読む=段の順の確かめ〔検収 中-2〕で、ほかの行と食い違う木になる)
    files = {"src/shibuya/__init__.py": "", "src/shibuya/old/__init__.py": '"""old"""\n',
             "src/shibuya/old/mod.py": "X = 1\n"}
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8", newline="")
    (root / "src/shibuya/old/frozen").mkdir()
    (root / "src/shibuya/old/frozen/a.json").write_bytes(b"{}\n")
    py = ('[project]\r\nname = "x"\r\n\r\n[tool.setuptools.package-data]\r\n"shibuya.old" = ["frozen/*.json"]\r\n\r\n'
          '[tool.pytest.ini_options]\r\nfilterwarnings = ["error::DeprecationWarning:shibuya.old.*"]\r\n')
    (root / "pyproject.toml").write_bytes(py.encode("utf-8"))
    rows = [Row(num="1", old="old/mod.py", package="x", kind="move", new="new/pk/mod.py", stage="foundation"),
            Row(num="2", old="old/frozen/a.json", package="x", kind="move", new="new/pk/frozen/a.json", stage="foundation"),
            Row(num="3", old="old/__init__.py", package="x", kind="delete", stage="foundation")]
    return Tree.load(root), MV.MapDoc(rows=rows), py


def test_apply_writes_the_package_data_key_and_nothing_else_of_pyproject_in_a_sample(tmp_path):
    """〔検収 M-2・k15〕作った見本の木へ ``apply`` すると、木の pyproject の package-data の鍵だけが新しい包みの名になり、ほかの
    バイト(改行の CRLF・ほかの節の filterwarnings を含む)は 1 バイトも変わらない。2 回目は何も変えない。"""
    root = tmp_path / "t"
    tree, md, py = _pd_sample(root)
    plan = MV.make_plan(tree, md, ("foundation",), pyproject_text=py)
    assert plan.package_data_keys == [("shibuya.old", "shibuya.new.pk")]
    MV.apply(plan, root)
    got = (root / "pyproject.toml").read_bytes().decode("utf-8")
    assert got == py.replace('"shibuya.old" = ["frozen/*.json"]', '"shibuya.new.pk" = ["frozen/*.json"]')
    assert (root / "src/shibuya/new/pk/frozen/a.json").is_file() and not (root / "src/shibuya/old").exists()
    again = MV.make_plan(Tree.load(root), md, ("foundation",), pyproject_text=got)
    assert again.package_data_keys == [] and again.pyproject_after == got
    assert "b/pyproject.toml" in MV.unified_diff(plan)  # 〔L-1〕書かない実行の差分にも出る


def test_rule_5_adds_only_late_readers_whose_final_place_may_read_in_a_sample():
    """〔検収 M-2・k10・k11〕決まり 5 の読んでよい側に足すのは、まだ移っていない読み手のうち、最終の置き場が読んでよい側
    (economy・interfaces)にあるものだけ。最終の置き場が読んでよくない側(mind)の読み手は足さない。"""
    from pkgmove import contracts as CT

    spec = CT.load_spec(ROOT / CT.CONTRACTS_REL)
    rows = [Row(num="1", old="core/rng.py", package="foundation", kind="move", new="foundation/rng.py", stage="foundation"),
            Row(num="2", old="economy/ledger.py", package="economy", kind="keep", new="economy/ledger.py"),
            Row(num="3", old="cli.py", package="interfaces", kind="split", new="interfaces/cli/main.py",
                split_to=("interfaces/cli/main.py",)),
            Row(num="4", old="engine/reader.py", package="mind", kind="move", new="mind/reader.py", stage="mind")]
    files = {"src/shibuya/__init__.py": "", "src/shibuya/foundation/__init__.py": "", "src/shibuya/foundation/rng.py": "",
             "src/shibuya/economy/__init__.py": "", "src/shibuya/economy/ledger.py": "",
             "src/shibuya/cli.py": "from shibuya.economy import ledger\n",
             "src/shibuya/engine/__init__.py": "", "src/shibuya/engine/reader.py": "from shibuya.economy import ledger\n"}
    contracts, rep = CT.build(spec, MV.MapDoc(rows=rows), Tree(files=files), "world")
    c5 = next(c for c in contracts if c["name"].startswith("〔段 4 の途中の決まり〕5 "))
    assert c5["protected_modules"] == ["shibuya.economy.ledger"]
    assert c5["allowed_importers"] == ["shibuya.economy", "shibuya.cli"]
    assert rep["late_allowed"] == [{"rule": 5, "modules": ["shibuya.cli"]}]
    assert rep["uncovered"] == ["shibuya.cli"]  # engine.reader は古い層の engine で覆われる


def test_package_data_is_not_rewritten_when_the_file_changes_shape():
    """〔検収 L-5・k18〕glob に当たっていたファイルが、包みの道からの相対の形を変えて移ったら(``frozen/a.json`` →
    ``data/a.json``)、行き先の包みが決まらないので鍵を書き換えない(守りが止める)。"""
    from pkgmove import pkgdata as PD

    text = '[tool.setuptools.package-data]\n"shibuya.old" = ["frozen/*.json"]\n'
    before = Tree(files={"src/shibuya/__init__.py": "", "src/shibuya/old/__init__.py": ""},
                  blobs={"src/shibuya/old/frozen/a.json": b"{}"})
    after = Tree(files={"src/shibuya/__init__.py": "", "src/shibuya/new/pk/__init__.py": ""},
                 blobs={"src/shibuya/new/pk/data/a.json": b"{}"})
    out, keys, warns = PD.rewrite(text, before, after, {"src/shibuya/old/frozen/a.json": "src/shibuya/new/pk/data/a.json"})
    assert out == text and keys == [] and "行き先が 1 つに決まらない" in warns[0]
    assert PD.check(out, after) == ["package-data の鍵の包みが木に無い: shibuya.old"]


# ------------------------------------------------------------------ 〔割る段 5a〕割る行を当てる道具(split.py・親の裁定 Q10=案 A)
_OLD_SAMPLE = (
    '"""old — 見本の元のファイル。"""\n'
    "\n"
    "from __future__ import annotations\n"
    "\n"
    "import os\n"
    "from typing import Final\n"
    "\n"
    "from shibuya.vocab import base as V\n"
    "\n"
    '__all__ = ["A", "B", "f", "C"]\n'
    "\n"
    "#: A の注\n"
    "A: Final[int] = 1\n"
    'B: Final[str] = V.word("x")\n'
    "\n"
    "\n"
    "def f(x: int) -> int:\n"
    "    return x + A + len(os.sep)\n"
    "\n"
    "\n"
    "class C:\n"
    "    def g(self) -> str:\n"
    "        return B\n"
    "\n"
    "\n"
    "assert A == 1\n"
)
_BASE_SAMPLE = (
    '"""base — 見本の既に在る割り先。"""\n'
    "\n"
    "from __future__ import annotations\n"
    "\n"
    "from typing import Final\n"
    "\n"
    "__all__ = [\n"
    '    "word",\n'
    "]\n"
    "\n"
    "\n"
    "def word(s: str) -> str:\n"
    "    return s\n"
)
_SAMPLE_ROW = dict(num="1", old="pk/old.py", package="nw", kind="split", new="nw/main.py",
                   split_to=("nw/main.py", "vocab/base.py"),
                   names=(("A", "vocab/base.py"), ("B", "vocab/base.py"), ("f", "nw/main.py"), ("C", "nw/main.py")),
                   names_complete=True, rewrites=(("vocab/base.py", "V"),))


def _split_sample(extra: dict[str, str] | None = None, **row_kw) -> tuple[Tree, MV.MapDoc]:
    files = {
        "src/shibuya/__init__.py": "",
        "src/shibuya/pk/__init__.py": "",
        "src/shibuya/pk/old.py": _OLD_SAMPLE,
        "src/shibuya/pk/reader.py": "from shibuya.pk.old import A, f\nfrom shibuya.pk import old as OLD\n\nX = A + f(1) + OLD.A\n",
        "src/shibuya/vocab/__init__.py": "",
        "src/shibuya/vocab/base.py": _BASE_SAMPLE,
        "tests/test_x.py": "from shibuya.pk.old import C\n",
        **(extra or {}),
    }
    return Tree(files=files), MV.MapDoc(rows=[Row(**{**_SAMPLE_ROW, **row_kw})])


def _then(mutate):
    """割り先の組み立ての後に字面を変える(負の対照=道具の不具合を植える)。"""
    def compose(tree, row, src_rel, ix, plan):
        return mutate(SP.compose(tree, row, src_rel, ix, plan))
    return compose


def test_split_sample_composes_dests_and_rewrites_readers():
    """見本の木: 名を結ぶ文は表の割り先へ(元の字面と注のまま)・ほかの文(assert)は読む名の割り先へ・主な割り先は元の
    docstring・割り先が使う import だけ・兄弟の割り先からの import・__all__ は割り先ごと・既に在る割り先へは後ろへ足し、
    宣言した別名(V.x)だけ書き換える・読み手の import は名の割り先へ文を分ける・別名で読む形は割り先が 1 つなら書き換える。
    守りは全部「同じ」。"""
    tree, md = _split_sample()
    plan = SP.make_split_plan(tree, md, "pk/old.py", check_order=False)
    a = plan.after.files
    assert "src/shibuya/pk/old.py" not in a and a["src/shibuya/nw/__init__.py"] == "" and a["src/shibuya/pk/__init__.py"] == ""
    main = a["src/shibuya/nw/main.py"]
    assert main.startswith('"""old — 見本の元のファイル。"""\n\nfrom __future__ import annotations\n')
    assert "import os\n" in main and "from typing" not in main and "from shibuya.vocab.base import A, B\n" in main
    assert '__all__ = [\n    "f", "C",\n]\n' in main and "def f(x: int) -> int:" in main and "class C:" in main
    base = a["src/shibuya/vocab/base.py"]
    assert base.startswith('"""base — 見本の既に在る割り先。"""\n') and "def word(s: str) -> str:\n    return s\n" in base
    assert '    "word",\n    "A", "B",\n]\n' in base and "#: A の注\nA: Final[int] = 1\n" in base
    assert 'B: Final[str] = word("x")\n' in base and "V." not in base and "assert A == 1\n" in base
    assert a["src/shibuya/pk/reader.py"].splitlines()[:3] == [
        "from shibuya.vocab.base import A", "from shibuya.nw.main import f", "from shibuya.vocab import base as OLD"]
    assert a["tests/test_x.py"] == "from shibuya.nw.main import C\n"
    assert plan.rewrites_applied == {"vocab/base.py": 1} and plan.dests == {"nw/main.py": "new", "vocab/base.py": "existing"}
    assert plan.created_heads == ["src/shibuya/nw/__init__.py"] and plan.deleted == ["src/shibuya/pk/old.py"]
    assert set(plan.guards) >= {"stmts", "constants", "bindings", "declarations", "outside_allowlist", "import_names",
                                "head_all"} and set(plan.guards.values()) == {"同じ"}
    for p in ("src/shibuya/nw/main.py", "src/shibuya/vocab/base.py", "src/shibuya/pk/reader.py"):
        compile(a[p], p, "exec")


@pytest.mark.parametrize("mutate,word", [
    # 1 文を落とす(クラス C を写し忘れる)
    (lambda out: {**out, "nw/main.py": out["nw/main.py"].split("\n\nclass C:")[0] + "\n"}, "① 文"),
    # 1 文を 2 か所に置く(f を既に在る割り先にも写す)
    (lambda out: {**out, "vocab/base.py": out["vocab/base.py"] + "\n\ndef f(x: int) -> int:\n    return x + A\n"}, "① 文"),
    # 文字列の定数を変える(守りを通らない書き換え)
    (lambda out: {**out, "vocab/base.py": out["vocab/base.py"].replace('word("x")', 'word("y")')}, "② 定数"),
    # 要る import を落とす
    (lambda out: {**out, "nw/main.py": out["nw/main.py"].replace("import os\n", "")}, "③ 名の結び"),
])
def test_negative_split_guards_stop_a_broken_composition(mutate, word):
    tree, md = _split_sample()
    with pytest.raises(SP.SplitStopped) as ei:
        SP.make_split_plan(tree, md, "pk/old.py", check_order=False, compose_fn=_then(mutate))
    assert any(word in e for e in ei.value.errors), ei.value.errors


def test_negative_undeclared_or_unused_alias_rewrites_are_refused():
    """自分を別名で読む文は、宣言した書き換え(親の裁定 Q6)のときだけ書き換える。宣言が無ければ断り、当たらない宣言も断る。"""
    tree, md = _split_sample(rewrites=())
    with pytest.raises(SP.SplitRefused, match="宣言した書き換え"):
        SP.make_split_plan(tree, md, "pk/old.py", check_order=False)
    tree, md = _split_sample(rewrites=(("vocab/base.py", "V"), ("nw/main.py", "V")))
    with pytest.raises(SP.SplitRefused, match="当たらない"):
        SP.make_split_plan(tree, md, "pk/old.py", check_order=False)


def test_negative_a_reader_with_two_destinations_is_listed_for_hand_fixing():
    """属性で読み、割り先が 2 つ以上になる読みは書き換えずに「手で直す一覧」に出し、既定(strict)では断る。"""
    extra = {"src/shibuya/pk/r2.py": "from shibuya.pk import old as O\n\nY = O.A + O.f(1)\n"}
    tree, md = _split_sample(extra)
    with pytest.raises(SP.SplitRefused, match="手で直す"):
        SP.make_split_plan(tree, md, "pk/old.py", check_order=False)
    plan = SP.make_split_plan(tree, md, "pk/old.py", check_order=False, strict=False)
    assert len(plan.manual) == 1 and "src/shibuya/pk/r2.py" in plan.manual[0]
    assert plan.after.files["src/shibuya/pk/r2.py"] == extra["src/shibuya/pk/r2.py"]


def test_negative_a_declaration_in_a_second_destination_is_stopped():
    """2 つ目以降の新しい割り先につなぎの台帳の宣言(expedient の段落)が入ると、台帳の道の表(1 対 1)で表せないので止める。"""
    old = _OLD_SAMPLE + '\n\ndef h() -> int:\n    """仮の値を返す。\n\n    expedient: 見本の仮の値。\n    """\n    return 1\n'
    tree, md = _split_sample({"src/shibuya/pk/old.py": old}, names=(*_SAMPLE_ROW["names"], ("h", "nw/extra.py")),
                             split_to=("nw/main.py", "vocab/base.py", "nw/extra.py"))
    with pytest.raises(SP.SplitStopped) as ei:
        SP.make_split_plan(tree, md, "pk/old.py", check_order=False)
    assert any("④ 宣言" in e and "nw/extra.py" in e for e in ei.value.errors), ei.value.errors


def test_negative_split_class_key_guard_catches_a_swapped_pair():
    old = {"shibuya.pk.old.C": "shibuya.pk.old.C", "shibuya.pk.old.D": "shibuya.pk.old.D", "shibuya.x.E": "shibuya.x.E"}
    fq = {"shibuya.pk.old.C": "C", "shibuya.pk.old.D": "D", "shibuya.x.E": "E"}
    keymap = CI.split_keymap({"C": None, "D": None}, "shibuya.pk.old", {"C": "shibuya.nw.main", "D": "shibuya.vocab.base"})
    good = CI.split_table(old, keymap, fq)
    CI.check_split_keys(old, good, keymap, fq)
    assert set(good) == {"shibuya.nw.main.C", "shibuya.vocab.base.D", "shibuya.x.E"} and sorted(good.values()) == sorted(old.values())
    swapped = {"shibuya.nw.main.C": "shibuya.pk.old.D", "shibuya.vocab.base.D": "shibuya.pk.old.C", "shibuya.x.E": "shibuya.x.E"}
    with pytest.raises(CI.ClassIdError, match="取り違え"):
        CI.check_split_keys(old, swapped, keymap, fq)
    with pytest.raises(CI.ClassIdError, match="1 対 1"):
        CI.check_split_keys(old, good, {**keymap, "shibuya.x.E": "shibuya.nw.main.C"}, fq)


def test_split_in_place_keeps_the_main_file_and_moves_names_out():
    """主な割り先が元のファイルの今の置き場(段 4 で移した=延ばした 18 本目の形): 元のファイルを書き直し、出した名は割り先から読む。"""
    port = ('"""port — 見本。"""\n\nfrom __future__ import annotations\n\n_K: frozenset[str] = frozenset("ab")\n\n\n'
            "def m(s: str) -> int:\n    return sum(1 for c in s if c not in _K)\n\n\n"
            "class P:\n    def n(self) -> int:\n        return m(\"abc\")\n")
    files = {"src/shibuya/__init__.py": "", "src/shibuya/sp/__init__.py": "", "src/shibuya/sp/port.py": port,
             "src/shibuya/sp/use.py": "from shibuya.sp.port import P, m\n"}
    row = Row(num="1", old="old/port.py", package="sp", kind="split", new="sp/port.py", split_to=("sp/port.py", "txt/mora.py"),
              names=(("_K", "txt/mora.py"), ("m", "txt/mora.py"), ("P", "sp/port.py")), names_complete=True)
    md = MV.MapDoc(rows=[row])
    tree = Tree(files=files)
    assert SP.source_rel(tree, row) == "sp/port.py" and not SP.is_done(tree, row)
    plan = SP.make_split_plan(tree, md, "old/port.py", check_order=False)
    a = plan.after.files
    assert plan.in_place and "def m(" not in a["src/shibuya/sp/port.py"] and "class P:" in a["src/shibuya/sp/port.py"]
    assert "from shibuya.txt.mora import m\n" in a["src/shibuya/sp/port.py"]
    assert a["src/shibuya/txt/mora.py"].startswith('"""txt.mora — 割る段で ``old/port.py`` を割った割り先')
    assert a["src/shibuya/sp/use.py"].splitlines() == ["from shibuya.sp.port import P", "from shibuya.txt.mora import m"]
    assert set(plan.guards.values()) == {"同じ"} and SP.is_done(plan.after, row)


def test_split_rows_in_the_real_map_match_the_source_files():
    """本物の対応表: 割る段 5a の 17 本と延ばした 1 本(18 本目だった ``engine/speech/port.py``=G0 の検収の後の親の答え 1)は名が
    揃い(§4 を開いた=親の裁定 Q9)、まだ割っていない本は表の名が元のファイルの頂上の名と同じ。延ばした行は割る行のまま、順に
    載らず(split_order 0)、道具は名指しでも断る。2 つ目以降の割り先の行(split_from)は段 4 の段の行に数えず、名指しでも段 4 の
    道具は断る。〔割る段 5b の G0〕順に 5b の 5 本を足した(22 本)・2 つ目以降の割り先の行は 16 本(5a 10・5b 6)。〔割る段 6 の
    S6-G0〕順に段 6 の 1 本(23 本目=engine/resolve.py)を足した・2 つ目以降の割り先の行は 30 本(段 6 の 14 を足した)。〔割る段 6
    の M0・親の裁定 Q12・T2〕延ばした行を順の 24 本目に載せた(``SPLIT_DEFERRED`` は空)。順に無い行を名指しで断ることは、その行を
    除いた順を渡して確かめる(延ばした行と同じ形)。"""
    from pkgmove.table import SPLIT_DEFERRED, SPLIT_ORDER

    tree = _root_tree()
    by = MAPDOC.by_old()
    assert [r.old for r in MAPDOC.split_rows()] == list(SPLIT_ORDER) and len(SPLIT_ORDER) == 24
    assert SPLIT_ORDER[17:] == ("engine/commit.py", "engine/presence.py", "engine/calendar_shadow.py", "engine/run.py", "cli.py",
                                "engine/resolve.py", "engine/speech/port.py")
    assert SPLIT_DEFERRED == {} and by["engine/speech/port.py"].kind == "split"
    assert by["engine/speech/port.py"].split_order == 24 and MAPDOC.meta.get("split_deferred") == []
    with pytest.raises(SP.SplitRefused, match="割る段の順に無い行"):
        SP.make_split_plan(tree, MAPDOC, "engine/speech/port.py", order=SPLIT_ORDER[:-1])
    for old in (*SPLIT_ORDER, *SPLIT_DEFERRED):
        r = by[old]
        assert r.names_complete and r.split_order == (SPLIT_ORDER.index(old) + 1 if old in SPLIT_ORDER else 0)
        if SP.is_done(tree, r):
            continue
        src = SP.source_rel(tree, r)
        assert src is not None, old
        assert set(r.name_map) == SP.top_names(tree.files[SRC_PREFIX + src]), old
    sf = [r for r in MAPDOC.rows if r.split_from]
    assert len(sf) == 30 and all(r.kind == "move" and r.stage == "" and r.new in by[r.split_from].split_to for r in sf)
    assert len([r for r in sf if r.split_from == "engine/resolve.py"]) == 14
    rows, _held = MV.select_rows(MAPDOC, STAGES)
    assert not [r for r in rows if r.split_from]
    with pytest.raises(MV.Refused, match="割る段の割り先の行"):
        MV.select_rows(MAPDOC, (), only=[sf[0].old])
    assert by["engine/events/body.py"].rewrites == (("foundation/vocab/events.py", "V"),)
    assert by["engine/speech/port.py"].name_map["mora_count"] == "foundation/text/mora.py"


def test_split_order_is_kept_in_the_real_tree():
    """割る段の順(親の裁定 Q11): 次の本のほかは断る(段を飛ばさない)。"""
    from pkgmove.table import SPLIT_ORDER

    tree = _root_tree()
    st = SP.split_state(tree, MAPDOC)
    assert st is not None
    if len(st) >= len(SPLIT_ORDER) - 1:
        pytest.skip("割る段の終わりの木")
    nxt = SP.next_split(tree, MAPDOC)
    assert nxt == SPLIT_ORDER[len(st)]
    later = SPLIT_ORDER[len(st) + 1]
    with pytest.raises(SP.SplitRefused, match="順が違う"):
        SP.make_split_plan(tree, MAPDOC, later)


def test_split_dry_run_of_the_next_row_writes_nothing_and_keeps_every_guard(tmp_path):
    """本物の木で次の本を書かずに当てる(--through=手で直す読みは残して報告): 何も書かず、守りが全部「同じ」。割る行が残り 0 の
    木では、書かない実行の口(次の本の既定の形と ``--through all``)が何も書かないことだけを確かめる(親の裁定・5b の終わり)。"""
    tree = _root_tree()
    nxt = SP.next_split(tree, MAPDOC)
    if nxt is None:
        before = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                  for p in ("tools/pkgmove/map.toml", "pyproject.toml")}
        for name, args in (("next", ("--next",)), ("all", ("--through", "all"))):
            od = tmp_path / name
            r = run_cli("split", *args, "--out-dir", str(od))
            assert r.returncode == 0 and "割る段は全部当たっている" in r.stdout, (args, r.stdout[-2000:], r.stderr[-2000:])
            assert not od.exists() or [x for x in od.rglob("*") if x.is_file()] == [], args
        assert before == {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in before}
        return
    before = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in ("tools/pkgmove/map.toml", "pyproject.toml")}
    r = run_cli("split", "--through", nxt, "--out-dir", str(tmp_path))
    assert r.returncode == 0, r.stderr[-3000:]
    rows = json.loads((tmp_path / "split_through_summary.json").read_text(encoding="utf-8"))
    assert [x["row"] for x in rows] == [nxt] and all(v == "同じ" or v.startswith("宣言どおり") for v in rows[0]["guards"].values())
    assert "contracts" in rows[0]["guards"] and isinstance(rows[0]["unwritten"], list)  # 〔検収 高-1・低-2〕
    assert "書いていない" in r.stdout
    assert before == {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in before}


def test_ignore_split_rows_come_in_with_their_split():
    """〔親の裁定 Q3〕割る段で出る辺 4 本は別の表 [[ignore_split]](28 本と表の外の 1 本の表は変えない)。appears_with の割る行を
    当てる前の木では載せない。〔割る段 6 の S6-G0・裁定 Q6〕段 6 の 4 本(割 5〜8=型の注釈だけの辺)を足した。"""
    from pkgmove import contracts as CT
    from pkgmove.table import SPLIT_ORDER

    spec = CT.load_spec(ROOT / CT.CONTRACTS_REL)
    got = [(g["importer"], g["imported"], list(g["rules"]), g["appears_with"]) for g in spec.ignores_split]
    assert got == [("mind.percept.draw", "world.model.agent_table", [3], "agents/state.py"),
                   ("world.model.scene_hash", "world.model.percept_scene", [1], "engine/change_detect.py"),
                   ("mind.system1.change_detect", "world.model.agent_table", [3], "engine/change_detect.py"),
                   ("mind.system1.change_detect", "world.model.scene_hash", [3], "engine/change_detect.py"),
                   ("act.ops.detect_writes", "mind.system1.change_detect", [1], "engine/resolve.py"),
                   ("mind.ops", "world.model.agent_table", [3], "engine/resolve.py"),
                   ("runtime.state.restore", "world.model.agent_table", [10], "engine/resolve.py"),
                   ("runtime.state.restore", "world.model.state", [10], "engine/resolve.py")]
    assert [g["gone_at"] for g in spec.ignores_split if g["appears_with"] == "engine/resolve.py"] == ["注釈だけ"] * 4
    assert all(g["appears_with"] in SPLIT_ORDER and g["gone_at"] for g in spec.ignores_split)
    assert len(spec.ignores) == 28 and len(spec.extras) == 1
    tree = _root_tree()
    stage = CT.stage_of(tree, MAPDOC, spec)
    if not stage:
        pytest.skip("段 4 の前の木")
    _c, rep = CT.build(spec, MAPDOC, tree, stage)
    by = MAPDOC.by_old()
    for row in rep["ignores_split"]:
        if not SP.is_done(tree, by[row["appears_with"]]):
            assert row.get("skipped") == "割る行がまだ当たっていない", row


# ------------------------------------------------------------------ 〔割る段 5a・G0 の検収の直し〕止め・決まり・守りの負の対照
_TWO_SAMPLE = '"""two — 見本の 2 本目の元のファイル。"""\n\nfrom __future__ import annotations\n\nT = 1\nU = 2\n'
_TWO_ROW = dict(num="2", old="pk/two.py", package="nw", kind="split", new="nw/two.py", split_to=("nw/two.py", "vocab/base.py"),
                names=(("T", "nw/two.py"), ("U", "vocab/base.py")), names_complete=True)


def test_split_refuses_a_done_row_a_wrong_order_and_a_skipped_tree(monkeypatch):
    """〔検収 中-4〕済んだ本の当て直し・順が違う本・順を飛ばした木(split_state が None)は、どれも断る(終了コード 2 の経路)。"""
    monkeypatch.setattr(SP, "SPLIT_ORDER", ("pk/old.py", "pk/two.py"))
    tree, _md = _split_sample({"src/shibuya/pk/two.py": _TWO_SAMPLE})
    md = MV.MapDoc(rows=[Row(**_SAMPLE_ROW), Row(**_TWO_ROW)])
    assert SP.split_state(tree, md) == [] and SP.next_split(tree, md) == "pk/old.py"
    with pytest.raises(SP.SplitRefused, match="順が違う"):
        SP.make_split_plan(tree, md, "pk/two.py")
    done = SP.make_split_plan(tree, md, "pk/old.py").after
    assert SP.split_state(done, md) == ["pk/old.py"] and SP.next_split(done, md) == "pk/two.py"
    with pytest.raises(SP.SplitRefused, match="当たっている"):
        SP.make_split_plan(done, md, "pk/old.py")
    skipped = SP.make_split_plan(tree, md, "pk/two.py", check_order=False).after  # 1 本目を飛ばして 2 本目だけ当てた木
    assert SP.split_state(skipped, md) is None
    with pytest.raises(SP.SplitRefused, match="段を飛ばしたか"):
        SP.make_split_plan(skipped, md, "pk/old.py")


def test_split_apply_refuses_a_main_worktree(tmp_path):
    """〔検収 中-4〕``split --apply`` は git の本体の作業木を断り、何も書かない(木をまるごと写さない小さな見本の木)。"""
    main = tmp_path / "main"
    (main / "src" / "shibuya").mkdir(parents=True)
    (main / "src" / "shibuya" / "__init__.py").write_text("", encoding="utf-8")
    _git(main, "init", "-q")
    before = {k: v for k, v in digest(main).items() if not k.startswith(".git/")}
    r = run_cli("split", "--next", "--apply", "--tree", str(main))
    assert r.returncode == 2 and "本体の作業木" in r.stderr, r.stderr[-2000:]
    r = run_cli("split", "--next", "--apply")
    assert r.returncode == 2 and "--tree" in r.stderr
    r = run_cli("split", "--apply", "--through", "all", "--tree", str(main))
    assert r.returncode == 2 and "--through" in r.stderr
    assert {k: v for k, v in digest(main).items() if not k.startswith(".git/")} == before


def test_contract_view_puts_the_main_destination_of_a_split_head_in_the_final_names():
    """〔検収 高-1〕頭を割る行(llm/__init__.py の形): 中身が割り先へ出た後(元の頭が 0 バイト)は、主な割り先が最終の名になり、
    その単位(foundation)が言える。前は頭の行を全部飛ばし、単位と決まりが黙って言えなくなった。"""
    from pkgmove import contracts as CT

    rows = [Row(num="1", old="core/rng.py", package="foundation", kind="move", new="foundation/rng.py", stage="foundation"),
            Row(num="2", old="llm/__init__.py", package="foundation", kind="split", new="foundation/ports/inference.py",
                split_to=("foundation/ports/inference.py",)),
            Row(num="3", old="llm/fleet.py", package="runtime", kind="move", new="runtime/fleet.py", stage="runtime")]
    md = MV.MapDoc(rows=rows)
    base = {"src/shibuya/__init__.py": "", "src/shibuya/foundation/__init__.py": "", "src/shibuya/foundation/rng.py": "",
            "src/shibuya/llm/fleet.py": ""}
    before = Tree(files={**base, "src/shibuya/llm/__init__.py": "X = 1\n"})
    after = Tree(files={**base, "src/shibuya/llm/__init__.py": "", "src/shibuya/foundation/ports/__init__.py": "",
                        "src/shibuya/foundation/ports/inference.py": "X = 1\n"})
    vb, va = CT.view(before, md), CT.view(after, md)
    assert "shibuya.foundation.ports.inference" not in vb.final_of
    assert va.is_final("shibuya.foundation.ports.inference") and CT._unit_ok(va, "shibuya", "foundation") == (True, "")
    assert ("shibuya.llm", "shibuya.foundation.ports.inference") in va.moved_in


def test_negative_split_stops_when_import_rules_weaken_without_a_declaration(monkeypatch):
    """〔検収 高-1〕割る前の木で言えた単位・決まりが、割った後に言えなくなったら(宣言の外)止める。宣言
    (``[[split_weakens]]``)の分は通し、守りの値に「宣言どおり」と数を出す。"""
    from pkgmove import contracts as CT

    def fake_build(spec, mapdoc, tree, stage):
        done = "src/shibuya/nw/main.py" in tree.files
        return [], {"n_old": 2, "n_new": 9 - done, "dropped_old": [],
                    "not_expressed": [{"rule": "単位", "name": "nw", "why": "見本"}] if done else []}

    monkeypatch.setattr(CT, "stage_of", lambda tree, mapdoc, spec: "delete")
    monkeypatch.setattr(CT, "build", fake_build)
    spec = CT.Spec(root="shibuya", old_only_through="foundation", stage_order=("foundation", "delete"), layers=[], side=[],
                   rules=[], old=[], ignores=[])
    tree, md = _split_sample()
    with pytest.raises(SP.SplitStopped) as ei:
        SP.make_split_plan(tree, md, "pk/old.py", check_order=False, contracts_spec=spec)
    assert [e for e in ei.value.errors if e.startswith("決まり") and "単位|nw" in e], ei.value.errors
    spec.split_weakens = [{"split": "pk/old.py", "not_expressed": ["単位|nw"]}]
    plan = SP.make_split_plan(tree, md, "pk/old.py", check_order=False, contracts_spec=spec)
    assert plan.guards["contracts"] == "宣言どおり 1" and plan.contracts["contracts_after"] == {"old": 2, "new": 8}


def test_split_weakened_reads_the_declarations():
    """〔検収 高-1〕古い決まりから外れた名・丸ごと外れた古い決まり・言えなくなった決まりを、宣言の内と外に分ける。"""
    from pkgmove import contracts as CT

    spec = CT.Spec(root="shibuya", old_only_through="foundation", stage_order=("delete",), layers=[], side=[], rules=[],
                   old=[], ignores=[], split_weakens=[{"split": "x.py", "old_names_gone": ["llm"], "contracts_gone": ["L"],
                                                       "not_expressed": ["2|foundation は何も読まない"]}])
    b = {"n_old": 3, "n_new": 9, "not_expressed": [], "dropped_old": [{"contract": "K", "name": "agents", "why": "木に無い"}]}
    a = {"n_old": 2, "n_new": 9, "not_expressed": [{"rule": 1, "name": "層", "why": "w"}],
         "dropped_old": [*b["dropped_old"], {"contract": "K", "name": "llm", "why": "木に無い"},
                         {"contract": "L", "name": "(契約)", "why": "空"}, {"contract": "M", "name": "core", "why": "木に無い"}]}
    w = CT.weakened(spec, "x.py", b, a)
    assert w["declared"] == ["古い決まりから外れた: K の llm", "古い決まりから外れた: L の (契約)"]
    assert w["undeclared"] == ["言えなくなった: 1|層", "古い決まりから外れた: M の core"]
    assert w["unused"] == ["2|foundation は何も読まない"]
    same = CT.weakened(spec, "y.py", b, b)
    assert same["declared"] == [] == same["undeclared"] and same["unused"] == []


def test_split_weakened_sees_more_than_new_rule_names():
    """〔再検収 低-1〕前から言えない決まりで言えない名が増える・どの決まりも見ないモジュールが増える・読んでよい側に足した読み手が
    増える・載せた例外の行が増える(``[[ignore_split]]`` の外)も、宣言の外なら弱まりに数える。理由の文の言い回しが変わるだけ・
    減る向き・割る段の表の例外は数えない。``other`` の宣言は報告の文そのもので当てる。"""
    from pkgmove import contracts as CT

    spec = CT.Spec(root="shibuya", old_only_through="foundation", stage_order=("delete",), layers=[], side=[], rules=[],
                   old=[], ignores=[])
    why = "元の側の名のうち木で言えないもの: "
    b = {"n_old": 2, "n_new": 9, "dropped_old": [], "uncovered": ["shibuya.a"],
         "not_expressed": [{"rule": 10, "name": "核", "why": why + "x"}, {"rule": "単位", "name": "u", "why": "ほか 3"}],
         "late_allowed": [{"rule": 5, "modules": ["shibuya.r1"]}],
         "ignores": [{"num": 1}, {"num": 2, "skipped": "辺が無い"}], "ignores_66": [], "extra_ignores": [],
         "ignores_split": [{"num": "割 1", "skipped": "割る行がまだ当たっていない"}]}
    a = {**b, "uncovered": ["shibuya.a", "shibuya.b"],
         "not_expressed": [{"rule": 10, "name": "核", "why": why + "x, y"}, {"rule": "単位", "name": "u", "why": "ほか 2"}],
         "late_allowed": [{"rule": 5, "modules": ["shibuya.r1", "shibuya.r2"]}],
         "ignores": [{"num": 1}, {"num": 2}], "ignores_split": [{"num": "割 1"}]}
    w = CT.weakened(spec, "x.py", b, a)
    assert w["undeclared"] == ["言えない名が増えた: 10|核: y", "どの決まりも見なくなった: shibuya.b",
                               "読んでよい側に足した読み手が増えた: 決まり 5 の shibuya.r2", "載せた例外が増えた: ignores#2"]
    spec.split_weakens = [{"split": "x.py", "other": ["載せた例外が増えた: ignores#2"]}]
    w = CT.weakened(spec, "x.py", b, a)
    assert w["declared"] == ["載せた例外が増えた: ignores#2"] and len(w["undeclared"]) == 3 and w["unused"] == []
    assert CT.weakened(spec, "x.py", a, b)["undeclared"] == []  # 減る向きは弱まりでない


@pytest.mark.slow
def test_split_5a_5b_in_memory_keeps_the_import_rules_to_the_end():
    """〔検収 高-1〕本物の木で割る段の残りの本(5a の 17 本と 5b の 5 本=22 本の順の、木で済んでいない本)をメモリの中で順に当てる
    (書かない・手で直す読みは残す): どの本でも守りが「同じ」(宣言どおりの弱まりは 2 本目の agents と 10 本目の llm だけ)で、
    終わりに契約は 11(古い 2+新しい 9)、単位 foundation と決まり 2 が言える。〔割る段 5b の G0〕5b の 5 本の後は、単位
    interfaces が言え(run の本で入口の割り先 run_args が入る)、``shibuya.cli`` は入口の転送で済んだ本と見る(読んでよい側に
    足した古い読み手は 0)。〔割る段 6 の S6-G0〕23 本目(engine/resolve.py)まで: 宣言どおりの弱まりに段 6 の engine(包み engine が
    木から無くなり古い層の決まりが丸ごと消える=[[split_weakens]])が足され、終わりの契約は 11(古い 1+新しい 10=決まり 4 が言える)。
    〔割る段 6 の M0〕24 本目(延ばしていた engine/speech/port.py)まで: 弱まりは足されない(決まり 10 の例外=核 1 が載らなくなる)。"""
    from pkgmove import contracts as CT
    from pkgmove.table import SPLIT_ORDER

    spec = CT.load_spec(ROOT / CT.CONTRACTS_REL)
    frozen = frozen_of(ROOT)
    ledger = (ROOT / SP.LEDGER_REL).read_text(encoding="utf-8")
    tree = _root_tree()
    st = SP.split_state(tree, MAPDOC)
    assert st is not None
    weakened: dict[str, list[str]] = {}
    for old in SPLIT_ORDER[len(st):]:
        plan = SP.make_split_plan(tree, MAPDOC, old, frozen=frozen, ledger_text=ledger, strict=False, contracts_spec=spec)
        bad = {k: v for k, v in plan.guards.items() if v != "同じ" and not v.startswith("宣言どおり")}
        assert not bad and "contracts" in plan.guards, (old, bad)
        if plan.guards["contracts"] != "同じ":
            weakened[old] = plan.contracts["declared"]
        tree = plan.after
    assert set(weakened) <= {"agents/state.py", "llm/undefined.py", "engine/resolve.py"}, weakened
    assert SP.split_state(tree, MAPDOC) == list(SPLIT_ORDER) and SP.next_split(tree, MAPDOC) is None
    assert SP.is_forwarder(tree, MAPDOC.by_old()["cli.py"]) and "src/shibuya/engine/run.py" not in tree.files
    assert "src/shibuya/engine/resolve.py" not in tree.files and "src/shibuya/engine/__init__.py" not in tree.files
    _c, rep = CT.build(spec, MAPDOC, tree, CT.stage_of(tree, MAPDOC, spec))
    assert (rep["n_old"], rep["n_new"]) == (1, 10), rep["not_expressed"]
    ne = {(str(x["rule"]), x["name"]) for x in rep["not_expressed"]}
    assert ("単位", "foundation") not in ne and not [r for r, _n in ne if r in ("2", "4")], sorted(ne)
    assert ("単位", "interfaces") not in ne and not rep.get("late_allowed"), (sorted(ne), rep.get("late_allowed"))


def test_negative_alias_rewrite_captured_by_a_local_name_is_refused():
    """〔検収 低-1〕宣言した書き換え ``V.x`` → ``x`` の ``x`` が、その場所の局所の名(引数)に捕まる形は断る。捕まらなければ通す。"""
    def with_g(body: str):
        old = _OLD_SAMPLE.replace('B: Final[str] = V.word("x")\n', 'B: Final[str] = V.word("x")\n\n\n' + body)
        return _split_sample({"src/shibuya/pk/old.py": old}, names=(*_SAMPLE_ROW["names"], ("g", "vocab/base.py")))

    tree, md = with_g("def g(word: str) -> str:\n    return V.word(word)\n")
    with pytest.raises(SP.SplitRefused, match="局所の名に捕まる"):
        SP.make_split_plan(tree, md, "pk/old.py", check_order=False)
    tree, md = with_g("def g(s: str) -> str:\n    return V.word(s)\n")
    plan = SP.make_split_plan(tree, md, "pk/old.py", check_order=False)
    assert "    return word(s)\n" in plan.after.files["src/shibuya/vocab/base.py"] and set(plan.guards.values()) == {"同じ"}


def test_split_imports_a_name_that_shadows_a_builtin_and_guard_3_checks_it():
    """〔検収 中-1〕元が組み込みの名を覆う名(``def format``)を定義し、別の割り先の文がそれを読むなら、組み立ては import を作る。
    その import を落とす変異は ③ だけが止める(組み込みの format を読む形)。"""
    old = _OLD_SAMPLE.replace("def f(x: int) -> int:\n    return x + A + len(os.sep)\n",
                              "def format(x: int) -> int:\n    return x\n\n\ndef f(x: int) -> int:\n"
                              "    return format(x) + A + len(os.sep)\n")
    tree, md = _split_sample({"src/shibuya/pk/old.py": old}, names=(*_SAMPLE_ROW["names"], ("format", "vocab/base.py")))
    plan = SP.make_split_plan(tree, md, "pk/old.py", check_order=False)
    assert "from shibuya.vocab.base import A, B, format\n" in plan.after.files["src/shibuya/nw/main.py"]
    assert set(plan.guards.values()) == {"同じ"}
    drop = _then(lambda out: {**out, "nw/main.py": out["nw/main.py"].replace(", format\n", "\n")})
    with pytest.raises(SP.SplitStopped) as ei:
        SP.make_split_plan(tree, md, "pk/old.py", check_order=False, compose_fn=drop)
    assert [e[:1] for e in ei.value.errors] == ["③"] and "format" in ei.value.errors[0], ei.value.errors


@pytest.mark.parametrize("extra,word", [
    # 〔中-1〕星の import のある元は断る
    ({"src/shibuya/pk/old.py": _OLD_SAMPLE.replace("import os\n", "import os\nfrom os.path import *\n")}, "星の import"),
    # 〔中-2〕既に在る割り先が同じ名を持つ(後ろに足すと上書きする)
    ({"src/shibuya/vocab/base.py": _BASE_SAMPLE + "\n\nA = 0\n"}, "既に結んでいる"),
    # 〔低-3〕元が from __future__ import annotations を持たず、既に在る割り先が持つ
    ({"src/shibuya/pk/old.py": _OLD_SAMPLE.replace("from __future__ import annotations\n\n", "")}, "元は持たない"),
])
def test_negative_split_compositions_that_cannot_be_expressed_are_refused(extra, word):
    tree, md = _split_sample(extra)
    with pytest.raises(SP.SplitRefused, match=word):
        SP.make_split_plan(tree, md, "pk/old.py", check_order=False)


def test_split_rewrites_a_relative_import_of_the_source_to_the_absolute_form():
    """〔検収 中-2〕元の相対の import は、絶対の形に作り直して写す(割り先は別の包み)。守りは全部「同じ」。"""
    old = _OLD_SAMPLE.replace("import os\n", "import os\n\nfrom .helper import H\n").replace(
        "    return x + A + len(os.sep)\n", "    return x + A + len(os.sep) + H\n")
    tree, md = _split_sample({"src/shibuya/pk/old.py": old, "src/shibuya/pk/helper.py": "H = 1\n"})
    plan = SP.make_split_plan(tree, md, "pk/old.py", check_order=False)
    main = plan.after.files["src/shibuya/nw/main.py"]
    assert "from shibuya.pk.helper import H\n" in main and "from .helper" not in main
    assert any("相対 → 絶対" in x for x in plan.rebuilt_imports) and set(plan.guards.values()) == {"同じ"}


@pytest.mark.parametrize("reader", [
    "from .old import A\n\nX = A\n",  # 相対の import で割るモジュールを読む
    "from . import old\n\nX = old.A\n",
    "from shibuya.pk.old import *\n\nX = A\n",  # 星の import で割るモジュールを読む
])
def test_negative_relative_and_star_readers_of_the_split_module_are_listed_for_hand_fixing(reader):
    """〔検収 中-2〕相対の import と星の import で割るモジュールを読む読み手は書き換えず、「手で直す一覧」に出す(strict は断る)。"""
    tree, md = _split_sample({"src/shibuya/pk/r3.py": reader})
    with pytest.raises(SP.SplitRefused, match="手で直す"):
        SP.make_split_plan(tree, md, "pk/old.py", check_order=False)
    plan = SP.make_split_plan(tree, md, "pk/old.py", check_order=False, strict=False)
    assert [m for m in plan.manual if "src/shibuya/pk/r3.py" in m] and plan.after.files["src/shibuya/pk/r3.py"] == reader


def test_negative_guard_1_stops_a_reordered_destination():
    """〔検収 中-3〕同じ割り先の中で文の順を入れ替える変異(多重集合は同じ)は、① の順の確かめが止める。"""
    def swap(out):
        m = out["nw/main.py"]
        f_def = "def f(x: int) -> int:\n    return x + A + len(os.sep)\n"
        c_def = "class C:\n    def g(self) -> str:\n        return B\n"
        assert f_def + "\n\n" + c_def in m
        return {**out, "nw/main.py": m.replace(f_def + "\n\n" + c_def, c_def + "\n\n" + f_def)}

    tree, md = _split_sample()
    with pytest.raises(SP.SplitStopped) as ei:
        SP.make_split_plan(tree, md, "pk/old.py", check_order=False, compose_fn=_then(swap))
    assert [e for e in ei.value.errors if e.startswith("① 文") and "順" in e] and len(ei.value.errors) == 1, ei.value.errors


def test_negative_only_guard_2_stops_a_changed_module_docstring():
    """〔検収 中-4〕主な割り先のモジュールの docstring を変える変異は、② だけが止める(① は docstring を比べない)。"""
    tree, md = _split_sample()
    change = _then(lambda out: {**out, "nw/main.py": out["nw/main.py"].replace("見本の元のファイル。", "見本の元のファイル(変えた)。")})
    with pytest.raises(SP.SplitStopped) as ei:
        SP.make_split_plan(tree, md, "pk/old.py", check_order=False, compose_fn=change)
    assert [e[:1] for e in ei.value.errors] == ["②"], ei.value.errors


def test_split_reports_the_imports_and_comments_it_did_not_write():
    """〔検収 低-2〕どの割り先も使わない import・import の前の注・作り直した import の中の注は写さず、報告の ``unwritten`` に出す。"""
    old = _OLD_SAMPLE.replace("import os\nfrom typing import Final\n",
                              "import os\n# sys の前の注\nimport sys\nfrom typing import (  # typing の注\n    Final,\n)\n")
    tree, md = _split_sample({"src/shibuya/pk/old.py": old})
    plan = SP.make_split_plan(tree, md, "pk/old.py", check_order=False)
    un = plan.unwritten
    assert any(x.startswith("import 行 7: `import sys`") and "どの割り先も使わない" in x for x in un), un
    assert any("`# sys の前の注` — import の前" in x for x in un), un
    assert any("`# typing の注` — 作り直した import の中" in x for x in un), un
    assert SP.report(plan)["unwritten"] == un and set(plan.guards.values()) == {"同じ"}


_CYC_OLD = ('"""old — 見本。"""\n\nfrom __future__ import annotations\n\nfrom typing import Final\n\n'
            'from shibuya.lg.log import Proc\n\nA: Final[int] = 1\nC: Final[Proc] = Proc("x")\n')
_CYC_LOG = ('"""log — 見本の型の置き場(頂上で割り先 vocab.base を読む)。"""\n\nfrom __future__ import annotations\n\n'
            'from shibuya.vocab import base as V\n\n\nclass Proc:\n    def __init__(self, n: str) -> None:\n'
            '        self.n = n\n')


@pytest.mark.parametrize("dest_of_c,stops", [("vocab/base.py", True), ("nw/main.py", False)])
def test_negative_split_stops_a_new_import_cycle_through_an_existing_destination(dest_of_c, stops):
    """〔G2 の 5 本目の欠陥〕既に在る割り先(vocab/base.py)へ足す文が型を lg/log.py から読み、log が頂上で base を読むと、割った後に
    base ↔ log の循環になる(読み込みで落ちる)。守り「import の循環」が書く前に止め、循環の新しい辺と読む文の場所を出す。循環に
    ならない割り先(nw/main.py)なら通す。"""
    files = {"src/shibuya/__init__.py": "", "src/shibuya/pk/__init__.py": "", "src/shibuya/pk/old.py": _CYC_OLD,
             "src/shibuya/lg/__init__.py": "", "src/shibuya/lg/log.py": _CYC_LOG,
             "src/shibuya/vocab/__init__.py": "", "src/shibuya/vocab/base.py": _BASE_SAMPLE}
    row = Row(num="1", old="pk/old.py", package="nw", kind="split", new="nw/main.py",
              split_to=("nw/main.py", "vocab/base.py"), names=(("A", "nw/main.py"), ("C", dest_of_c)), names_complete=True)
    md = MV.MapDoc(rows=[row])
    if not stops:
        plan = SP.make_split_plan(Tree(files=files), md, "pk/old.py", check_order=False)
        assert plan.guards["import_cycles"] == "同じ" and set(plan.guards.values()) == {"同じ"}
        return
    with pytest.raises(SP.SplitStopped) as ei:
        SP.make_split_plan(Tree(files=files), md, "pk/old.py", check_order=False)
    errs = [e for e in ei.value.errors if e.startswith("import の循環")]
    assert errs and "shibuya.vocab.base -> shibuya.lg.log" in errs[0] and "src/shibuya/vocab/base.py:" in errs[0], ei.value.errors
    assert len(ei.value.errors) == 1, ei.value.errors  # ほかの守りは「同じ」



# ------------------------------------------------------------------ 〔割る段 5b の G0〕入口の転送(E2)・入口の移し(E3)・範囲の外(E4)
_CLI_SAMPLE = (
    '"""cli — 見本の入口。"""\n'
    "\n"
    "from __future__ import annotations\n"
    "\n"
    "import argparse\n"
    "\n"
    "\n"
    "def helper(x: int) -> int:\n"
    "    return x + 1\n"
    "\n"
    "\n"
    "def run(n: int) -> int:\n"
    "    return helper(n)\n"
    "\n"
    "\n"
    "def main(argv: list[str] | None = None) -> int:\n"
    "    ap = argparse.ArgumentParser()\n"
    '    ap.add_argument("--n", type=int, default=1)\n'
    "    return 0 if run(ap.parse_args(argv).n) else 1\n"
    "\n"
    "\n"
    'if __name__ == "__main__":\n'
    "    raise SystemExit(main())\n"
)
_CLI_ROW = dict(num="9", old="cli.py", package="ui", kind="split", new="ui/main.py", split_to=("ui/main.py", "ui/wire.py"),
                names=(("helper", "ui/wire.py"), ("run", "ui/main.py"), ("main", "ui/main.py")), names_complete=True)
_CLI_READER = ('import sys\n\nfrom shibuya import cli\n\n'
               'CMD = [sys.executable, "-m", "shibuya.cli", "--n", "2"]\nNAME = "shibuya.cli"\n\n\n'
               'def test_run():\n    assert cli.run(1) == 2\n')


def _cli_sample(monkeypatch, cli_text: str = _CLI_SAMPLE) -> tuple[Tree, MV.MapDoc]:
    monkeypatch.setattr(SP, "SPLIT_FORWARDERS", {"cli.py": "ui/main.py"})
    monkeypatch.setattr(SP, "SPLIT_ENTRIES", {})
    monkeypatch.setattr(SP, "SPLIT_ALIAS_DESTS", ())  # 〔E5〕本物の木の別名の宣言(同じ行 cli.py)を見本へ持ち込まない
    files = {"src/shibuya/__init__.py": "", "src/shibuya/cli.py": cli_text, "tests/test_cli_r.py": _CLI_READER}
    return Tree(files=files), MV.MapDoc(rows=[Row(**_CLI_ROW)])


def test_split_forwarder_keeps_the_entry_file_in_the_fixed_form(monkeypatch):
    """〔E2・親の裁定 Q6 の (a)・Q7〕入口の転送の行: 元のファイルを消さずに決まった型の転送で書き直す(``if __name__`` の中で割り先の
    ``main`` を読んで呼ぶだけ・名を結ばない)。入口(``if __name__``)は ``main`` の割り先へ。済んだかの判定は転送が型どおりのとき
    だけ真・元のファイルの判定は転送を元と見ない。名で読む読み手は割り先へ、名の無い ``"shibuya.cli"``(``-m`` の文脈も)は
    書き換えない(転送の名)。守りは全部「同じ」(守り「入口の転送」を含む)。"""
    tree, md = _cli_sample(monkeypatch)
    row = md.rows[0]
    assert SP.source_rel(tree, row) == "cli.py" and not SP.is_done(tree, row)
    plan = SP.make_split_plan(tree, md, "cli.py", check_order=False)
    a = plan.after.files
    fw = forwarder_text("cli.py", "ui/main.py")
    assert a["src/shibuya/cli.py"] == fw and plan.forwarder == "src/shibuya/cli.py" and plan.deleted == []
    assert fw.startswith('"""shibuya.cli — ``python -m shibuya.cli`` の入口(外との約束)。中身は ``shibuya.ui.main``')
    assert plan.entry == "ui/main.py" and 'if __name__ == "__main__":\n    raise SystemExit(main())\n' in a["src/shibuya/ui/main.py"]
    assert "def helper(" in a["src/shibuya/ui/wire.py"] and "from shibuya.ui.wire import helper\n" in a["src/shibuya/ui/main.py"]
    assert set(plan.guards.values()) == {"同じ"} and plan.guards["forwarder"] == "同じ"
    assert SP.is_done(plan.after, row) and SP.source_rel(plan.after, row) is None
    assert SP.forwarder_problems(fw, "cli.py", "ui/main.py") == []
    ns: dict = {"__name__": "shibuya.cli"}
    exec(compile(fw, "cli.py", "exec"), ns)  # import しても何も結ばない(古い道の口にならない)
    assert [k for k in ns if not k.startswith("__")] == []
    r = a["tests/test_cli_r.py"]
    assert "from shibuya.ui import main as cli\n" in r and '"-m", "shibuya.cli"' in r and 'NAME = "shibuya.cli"' in r
    assert [s["token"] for s in plan.str_stats.skipped if s["kind"] == "dotted_forwarder"] == ["shibuya.cli", "shibuya.cli"]
    assert plan.manual == [] and SP.report(plan)["forwarder"] == "src/shibuya/cli.py"
    # 転送の字面を変えた木は済んでいない(元のファイルの中身として扱う=順の次の本として当て直しを断る側)
    changed = Tree(files={**plan.after.files, "src/shibuya/cli.py": fw + "X = 1\n"})
    assert not SP.is_done(changed, row) and SP.source_rel(changed, row) == "cli.py"
    assert SP.forwarder_problems(fw + "X = 1\n", "cli.py", "ui/main.py")


def test_negative_split_forwarder_guard_stops_a_forwarder_that_binds_names(monkeypatch):
    """〔E2 の守り〕転送が頂上で ``main`` を結ぶ形(古い道の口)は、型を差し替えても守り「入口の転送」が止める(字面の同じだけに
    頼らない=AST の形で見る)。入口(``if __name__``)の無い元のファイルの転送の宣言は断る。"""
    tree, md = _cli_sample(monkeypatch)
    bad = ('"""shibuya.cli — 見本。"""\n\nfrom shibuya.ui.main import main\n\nif __name__ == "__main__":\n'
           '    raise SystemExit(main())\n')
    monkeypatch.setattr(SP, "forwarder_text", lambda old, dest: bad)
    with pytest.raises(SP.SplitStopped) as ei:
        SP.make_split_plan(tree, md, "cli.py", check_order=False)
    errs = [e for e in ei.value.errors if e.startswith("入口の転送")]
    assert errs and any("頂上で名を結ぶ" in e for e in errs) and any("頂上の文が" in e for e in errs), ei.value.errors
    monkeypatch.undo()
    tree, md = _cli_sample(monkeypatch, _CLI_SAMPLE.split("\n\nif __name__")[0] + "\n")
    with pytest.raises(SP.SplitRefused, match="入口の宣言"):
        SP.make_split_plan(tree, md, "cli.py", check_order=False)


def test_contract_view_puts_the_main_destination_of_a_forwarder_row_in_the_final_names(monkeypatch):
    """〔E2・計画 §4-2〕入口の転送が残る行: 元のファイルが型どおりの転送なら主な割り先が最終の名(単位 interfaces が言える)。
    転送のモジュール自身は最終の名を持たない。転送の字面が型と違えば、前と同じく元のファイルを古い置き場と見る。"""
    from pkgmove import contracts as CT

    monkeypatch.setattr(CT, "SPLIT_FORWARDERS", {"cli.py": "ui/main.py"})
    md = MV.MapDoc(rows=[Row(**_CLI_ROW)])
    base = {"src/shibuya/__init__.py": "", "src/shibuya/ui/__init__.py": ""}
    before = Tree(files={**base, "src/shibuya/cli.py": _CLI_SAMPLE})
    fw = forwarder_text("cli.py", "ui/main.py")
    after = Tree(files={**base, "src/shibuya/cli.py": fw, "src/shibuya/ui/main.py": "def main():\n    return 0\n",
                        "src/shibuya/ui/wire.py": "X = 1\n"})
    vb, va = CT.view(before, md), CT.view(after, md)
    assert vb.final_of["shibuya.cli"] == "shibuya.ui.main" and not vb.is_final("shibuya.ui.main")
    assert va.is_final("shibuya.ui.main") and "shibuya.cli" not in va.final_of
    assert ("shibuya.cli", "shibuya.ui.main") in va.moved_in
    vt = CT.view(Tree(files={**after.files, "src/shibuya/cli.py": fw + "X = 1\n"}), md)
    assert vt.final_of["shibuya.cli"] == "shibuya.ui.main" and not vt.is_final("shibuya.ui.main")


_RUN_SAMPLE = (
    '"""run — 見本のラン。"""\n'
    "\n"
    "from __future__ import annotations\n"
    "\n"
    "import argparse\n"
    "\n"
    "\n"
    "def run_day(n: int) -> int:\n"
    "    return n\n"
    "\n"
    "\n"
    "def main(argv: list[str] | None = None) -> int:\n"
    "    ap = argparse.ArgumentParser()\n"
    '    ap.add_argument("--n", type=int, default=1)\n'
    "    return run_day(ap.parse_args(argv).n) - 1\n"
    "\n"
    "\n"
    'if __name__ == "__main__":  # pragma: no cover\n'
    "    raise SystemExit(main())\n"
)
_RUN_ROW = dict(num="8", old="pk/run.py", package="rt", kind="split", new="rt/run.py", split_to=("rt/run.py", "ui/run_args.py"),
                names=(("run_day", "rt/run.py"), ("main", "ui/run_args.py")), names_complete=True)
_RUN_READER = ('import sys\n\n'
               'CMD = [sys.executable, "-m", "shibuya.pk.run", "--n", "2"]\n'
               'LINE = "python -m shibuya.pk.run --n 2"\n'
               'FN = "shibuya.pk.run.run_day"\n')


def _run_sample(monkeypatch, entries: dict[str, str] | None = None, extra: dict[str, str] | None = None):
    monkeypatch.setattr(SP, "SPLIT_FORWARDERS", {})
    monkeypatch.setattr(SP, "SPLIT_ENTRIES", {"pk/run.py": "ui/run_args.py"} if entries is None else entries)
    files = {"src/shibuya/__init__.py": "", "src/shibuya/pk/__init__.py": "", "src/shibuya/pk/run.py": _RUN_SAMPLE,
             "tests/test_run_r.py": _RUN_READER, **(extra or {})}
    return Tree(files=files), MV.MapDoc(rows=[Row(**_RUN_ROW)])


def test_split_entry_moves_the_main_block_and_the_m_strings(monkeypatch):
    """〔E3・返事その 8 §1-6 の 6〕入口の割り先の宣言: ``if __name__`` は ``main`` と同じ入口の割り先へ。名の無い点の道は ``-m`` の
    文脈(並びの 1 つ前が ``"-m"``・文字列の中の ``-m <名>``)なら入口の割り先へ。名つきの点の道は名の割り先へ。"""
    tree, md = _run_sample(monkeypatch)
    plan = SP.make_split_plan(tree, md, "pk/run.py", check_order=False)
    a = plan.after.files
    assert plan.entry == "ui/run_args.py" and plan.deleted == ["src/shibuya/pk/run.py", "src/shibuya/pk/__init__.py"]
    assert 'if __name__ == "__main__":  # pragma: no cover\n    raise SystemExit(main())\n' in a["src/shibuya/ui/run_args.py"]
    assert "__main__" not in a["src/shibuya/rt/run.py"]
    r = a["tests/test_run_r.py"]
    assert '"-m", "shibuya.ui.run_args", "--n"' in r and 'LINE = "python -m shibuya.ui.run_args --n 2"' in r
    assert 'FN = "shibuya.rt.run.run_day"' in r and plan.manual == [] and set(plan.guards.values()) == {"同じ"}


def test_negative_a_nameless_dotted_path_outside_m_is_listed_for_hand_fixing(monkeypatch):
    """〔E3〕``-m`` の文脈でない名の無い点の道は、主な割り先へ黙って向けず「手で直す一覧」に出す(既定=strict は断る)。記録の文
    (ASCII の外の字を含む文)の中のものは前と同じく書き換えず、一覧にも出さない。"""
    extra = {"tests/test_run_n.py": 'MOD = "shibuya.pk.run"\nDOC = "shibuya.pk.run を読む"\n'}
    tree, md = _run_sample(monkeypatch, extra=extra)
    with pytest.raises(SP.SplitRefused, match="手で直す"):
        SP.make_split_plan(tree, md, "pk/run.py", check_order=False)
    plan = SP.make_split_plan(tree, md, "pk/run.py", check_order=False, strict=False)
    assert len(plan.manual) == 1 and "tests/test_run_n.py::MOD" in plan.manual[0] and "名の無い点の道" in plan.manual[0]
    assert plan.after.files["tests/test_run_n.py"] == extra["tests/test_run_n.py"]


@pytest.mark.parametrize("entries,word", [
    ({"pk/run.py": "rt/run.py"}, "宣言した rt/run.py でない"),  # 入口が読む名(main)の割り先と食い違う宣言
    ({}, "入口の割り先の宣言"),  # 入口があるのに宣言が無い(-m の文字列の行き先が決まらない)
])
def test_negative_an_entry_without_a_matching_declaration_is_refused(monkeypatch, entries, word):
    tree, md = _run_sample(monkeypatch, entries=entries)
    with pytest.raises(SP.SplitRefused, match=word):
        SP.make_split_plan(tree, md, "pk/run.py", check_order=False)


def test_split_leaves_the_bytecheck_tool_and_its_test_alone(monkeypatch):
    """〔E4・親の裁定 Q9 の (a)〕byte-check の道具(``tools/bytecheck/``)とその試験は割る道具の書き換えの範囲の外: 書き換えず、
    書き換えたはずの所を ``excluded_sites`` に出す。負の対照: 範囲の外の一覧を空にすると、同じ字面が書き換わる。"""
    reader = 'from shibuya.pk.old import A\n\nP = "src/shibuya/pk/old.py"\n'
    extra = {"tools/bytecheck/x.py": reader, "tests/tools/test_bytecheck.py": reader, "tools/other.py": reader}
    tree, md = _split_sample(extra)
    # 〔割る段 6・E8〕名の手がかりの無い道(割り先 2 つの行)は宣言が無ければ手で直す一覧へ出る=主な割り先へ向ける宣言を置く
    # (範囲の外のファイルへの宣言は「範囲の外」で止まるので、範囲の中の 1 本だけ)
    monkeypatch.setattr(SP, "SPLIT_PATH_DESTS", (SP.PathDest("pk/old.py", "tools/other.py", "P", "nw/main.py"),))
    plan = SP.make_split_plan(tree, md, "pk/old.py", check_order=False)
    a = plan.after.files
    assert a["tools/bytecheck/x.py"] == reader == a["tests/tools/test_bytecheck.py"]
    assert a["tools/other.py"] == 'from shibuya.vocab.base import A\n\nP = "src/shibuya/nw/main.py"\n'
    assert sorted(x.split(":", 1)[0] for x in plan.excluded_sites) == ["tests/tools/test_bytecheck.py", "tools/bytecheck/x.py"]
    assert set(plan.guards.values()) == {"同じ"}
    monkeypatch.setattr(SP, "SPLIT_EXCLUDE_PATHS", ())
    monkeypatch.setattr(SP, "SPLIT_PATH_DESTS", tuple(SP.PathDest("pk/old.py", f, "P", "nw/main.py") for f in extra))
    plan2 = SP.make_split_plan(tree, md, "pk/old.py", check_order=False)
    assert plan2.after.files["tools/bytecheck/x.py"] == plan2.after.files["tools/other.py"] != reader
    assert plan2.excluded_sites == []


def test_import_check_runs_every_entry_with_help(tmp_path):
    """〔E3〕書いた後の確かめは、在る入口(``shibuya.cli``・``shibuya.interfaces.cli.run_args``)ごとに ``python -m <入口> --help``
    を回す。転送の ``-m shibuya.cli`` は割り先の ``main`` を呼ぶ。入口が落ちれば確かめも落ちる。"""
    from pkgmove import importcheck as IC

    main = ('import argparse\n\n\ndef main(argv=None):\n    argparse.ArgumentParser().parse_args(argv)\n    return 0\n\n\n'
            'if __name__ == "__main__":\n    raise SystemExit(main())\n')
    files = {"src/shibuya/__init__.py": "", "src/shibuya/interfaces/__init__.py": "",
             "src/shibuya/interfaces/cli/__init__.py": "", "src/shibuya/interfaces/cli/main.py": main,
             "src/shibuya/interfaces/cli/run_args.py": main,
             "src/shibuya/cli.py": forwarder_text("cli.py", "interfaces/cli/main.py")}
    doc = IC.check(_tiny_tree(tmp_path / "good", files), jobs=1)
    assert IC.ok(doc) and sorted(doc["entries"]) == ["shibuya.cli", "shibuya.interfaces.cli.run_args"], doc
    assert doc["cli_help_exit"] == 0 and "python -m shibuya.interfaces.cli.run_args --help 終了コード 0" in IC.summary(doc)
    broken = main.replace("def main(argv=None):\n", "def main(argv=None):\n    raise RuntimeError('壊れた入口')\n")
    doc = IC.check(_tiny_tree(tmp_path / "bad", {**files, "src/shibuya/interfaces/cli/run_args.py": broken}), jobs=1)
    assert not IC.ok(doc) and doc["entries"]["shibuya.interfaces.cli.run_args"]["exit"] != 0 and doc["cli_help_exit"] == 0


@pytest.mark.parametrize("mutate,word", [
    (lambda t: t.replace("    from shibuya.ui.main import main\n", "    from shibuya.ui.wire import main\n"), "if の中が"),
    (lambda t: t.replace("raise SystemExit(main())", "main()"), "if の中が"),
    (lambda t: t.split("\n", 2)[2], "docstring が無い"),
    (lambda t: t + "X = 1\n", "頂上で名を結ぶ"),
])
def test_negative_forwarder_problems_see_each_part_of_the_fixed_form(mutate, word):
    """〔E2 の守り〕転送の形の確かめは、字面の同じ(型との比べ)のほかに、各部分(docstring・名を結ばない・if の中の import と呼び)を
    AST で見る(型そのものを差し替えられても止まる)。"""
    fw = forwarder_text("cli.py", "ui/main.py")
    assert SP.forwarder_problems(fw, "cli.py", "ui/main.py") == []
    got = SP.forwarder_problems(mutate(fw), "cli.py", "ui/main.py")
    assert "字面が決まった型と違う" in got and any(word in x for x in got), got



# ------------------------------------------------------------------ 〔割る段 5b の G0 の直し〕検収の高-1・高-2・低-1・低-2
def test_split_keeps_the_table_keys_of_the_places_helpers(monkeypatch):
    """〔高-1〕``tests/_places.py`` の割る行の口(``split_files``・``split_source``・``split_module_names``・``_split_names``)の
    第 1 引数は対応表の割る行の鍵(元の道=値そのもの)なので書き換えない(割った後も表を引いて割り先へ付いていく)。書き換えなかった
    所は報告の ``table_key_sites`` に出す。負の対照: 規則を外すと、鍵が 1 つの割り先だけを指す見本(名の指定なし・名 1 つ)が
    主な割り先へ書き換わる(割った後に ``PlacesMapError`` で落ちる形)。ほかの道の文字列は前と同じく書き換える。"""
    reader = ('from tests import _places as PL\n\nA = PL.split_files("pk/old.py")\nB = PL.split_source("pk/old.py", ("f",))\n'
              'C = "src/shibuya/pk/old.py"\n')
    tree, md = _split_sample({"tests/test_keys.py": reader})
    # 〔割る段 6・E8〕名の手がかりの無い道(C・規則を外した後の A)は、宣言が無ければ手で直す一覧へ出る=主な割り先へ向ける宣言を置く
    monkeypatch.setattr(SP, "SPLIT_PATH_DESTS", (SP.PathDest("pk/old.py", "tests/test_keys.py", "C", "nw/main.py"),))
    plan = SP.make_split_plan(tree, md, "pk/old.py", check_order=False)
    got = plan.after.files["tests/test_keys.py"]
    assert got == reader.replace('C = "src/shibuya/pk/old.py"', 'C = "src/shibuya/nw/main.py"')
    assert SP.report(plan)["table_key_sites"] == ["tests/test_keys.py::A: pk/old.py", "tests/test_keys.py::B: pk/old.py"]
    assert set(plan.guards.values()) == {"同じ"}
    monkeypatch.setattr(ST, "TABLE_KEY_CALLS", frozenset())
    monkeypatch.setattr(SP, "SPLIT_PATH_DESTS", tuple(SP.PathDest("pk/old.py", "tests/test_keys.py", s, "nw/main.py")
                                                      for s in ("A", "C")))
    plan2 = SP.make_split_plan(tree, md, "pk/old.py", check_order=False)
    got2 = plan2.after.files["tests/test_keys.py"]
    assert 'PL.split_files("nw/main.py")' in got2 and 'PL.split_source("nw/main.py", ("f",))' in got2
    assert SP.report(plan2)["table_key_sites"] == []


@pytest.mark.parametrize("code,want", [
    # 属性の読みが 1 つの割り先=機械で書き換える
    ("import sys; from shibuya.pk import old; sys.exit(old.f(1))", "from shibuya.nw import main as old"),
    # 別名つき(from <包み> import <割るモジュール> as X)
    ("from shibuya.pk import old as X; X.f(1)", "from shibuya.nw import main as X"),
    # 2 つの割り先に割れる読み=手で直す一覧
    ("from shibuya.pk import old; print(old.A, old.f(1))", None),
    # コードとして読めない文字列(シェルの文)の中の import=手で直す一覧
    ('python -c "from shibuya.pk import old; old.f(1)"', None),
])
def test_split_sees_code_strings_that_import_the_split_module_from_its_package(monkeypatch, code, want):
    """〔高-2〕コードの文字列(子のプロセスの台本ほか)の ``from <包み> import <割るモジュール>`` の形を、書き換えるか「手で直す
    一覧」に出す(黙って残さない)。前は点の道と斜線の道の字面だけで文字列を選んだので、この形を見落とした。負の対照: 選ぶ口を
    前の形(点の道と斜線の道だけ)に戻すと、どの見本も書き換えも一覧も無く残る。"""
    reader = f"CODE = {code!r}\n"
    tree, md = _split_sample({"tests/test_code_s.py": reader})
    plan = SP.make_split_plan(tree, md, "pk/old.py", check_order=False, strict=False)
    got = plan.after.files["tests/test_code_s.py"]
    man = [m for m in plan.manual if "tests/test_code_s.py" in m]
    if want is None:
        assert got == reader and len(man) == 1, (got, plan.manual)
        with pytest.raises(SP.SplitRefused, match="手で直す"):
            SP.make_split_plan(tree, md, "pk/old.py", check_order=False)
    else:
        assert want in got and "from shibuya.pk import old" not in got and man == [], (got, plan.manual)
        compile(got, "t.py", "exec")
    monkeypatch.setattr(ST, "code_import_hits", lambda ctx, value: [])
    plan2 = SP.make_split_plan(tree, md, "pk/old.py", check_order=False, strict=False)
    assert plan2.after.files["tests/test_code_s.py"] == reader
    assert not [m for m in plan2.manual if "tests/test_code_s.py" in m]


def test_negative_forwarder_guard_branches_stop_one_by_one(monkeypatch):
    """〔低-1〕守り「入口の転送」の 2 つの枝を、それぞれほかの枝に当たらない見本で落とす: (1) 型そのものにつなぎの台帳の宣言
    (docstring の ``expedient:``)がある=字面と形は型どおり (2) 割る元に ``main`` が無く、転送が呼ぶ ``main`` が割り先の頂上に
    無い=表の読み込みの確かめ(本物の表は ``main`` の割り先を確かめる)を通らない見本の行。"""
    tree, md = _cli_sample(monkeypatch)
    with_decl = forwarder_text("cli.py", "ui/main.py").replace(
        "(割る段 5b)。\"\"\"", "(割る段 5b)。\n\nexpedient: 見本の仮の宣言。\n\"\"\"")
    monkeypatch.setattr(SP, "forwarder_text", lambda old, dest: with_decl)
    with pytest.raises(SP.SplitStopped) as ei:
        SP.make_split_plan(tree, md, "cli.py", check_order=False)
    assert [e for e in ei.value.errors] == ["入口の転送 src/shibuya/cli.py: つなぎの台帳の宣言がある"], ei.value.errors
    monkeypatch.undo()
    no_main = (_CLI_SAMPLE.split("def main(")[0].rstrip("\n") + "\n\n\nif __name__ == \"__main__\":\n"
               "    raise SystemExit(run(1))\n")
    tree, md = _cli_sample(monkeypatch, no_main)
    md = MV.MapDoc(rows=[Row(**{**_CLI_ROW, "names": (("helper", "ui/wire.py"), ("run", "ui/main.py"))})])
    with pytest.raises(SP.SplitStopped) as ei:
        SP.make_split_plan(tree, md, "cli.py", check_order=False)
    assert ei.value.errors == ["入口の転送 src/shibuya/cli.py: 呼ぶ main が割り先 ui/main.py の頂上に無い"], ei.value.errors


def test_split_groups_cover_the_split_order_in_order():
    """〔低-2〕群(親の裁定 Q11・``table.SPLIT_GROUPS``)を段の順・群の順につなぐと ``SPLIT_ORDER`` の全部と同じ(重なりも抜けも
    無い)。5b の群は G1=commit・presence・calendar_shadow・G2=run・G3=cli。〔割る段 6 の S6-G0・裁定 Q9〕段 6 の群は G1=resolve
    (23 本目)。〔割る段 6 の M0〕段 6 の群 M=延ばしていた ``engine/speech/port.py``(24 本目)。"""
    from pkgmove.table import SPLIT_GROUPS, SPLIT_ORDER

    seq: list[int] = []
    for stage in ("5a", "5b", "6"):
        for _g, (lo, hi) in SPLIT_GROUPS[stage].items():
            assert lo <= hi
            seq += list(range(lo, hi + 1))
    assert seq == list(range(1, len(SPLIT_ORDER) + 1))
    g = {k: SPLIT_ORDER[lo - 1: hi] for k, (lo, hi) in SPLIT_GROUPS["5b"].items()}
    assert g == {"G1": ("engine/commit.py", "engine/presence.py", "engine/calendar_shadow.py"), "G2": ("engine/run.py",),
                 "G3": ("cli.py",)}
    assert len(SPLIT_ORDER) == 24 and {k: SPLIT_ORDER[lo - 1: hi] for k, (lo, hi) in SPLIT_GROUPS["6"].items()} == {
        "G1": ("engine/resolve.py",), "M": ("engine/speech/port.py",)}


def test_split_lists_a_code_import_inside_an_f_string_for_hand_fixing(monkeypatch):
    """〔G0 の再検収 低-1〕f 文字列の部分の中のコードが割るモジュールを読む形(``f"from shibuya.pk import old; old.f({n})"``)は
    書き換えられないので「手で直す一覧」に出す(strict は断る)。負の対照: その枝(``code_import_hits`` を f 文字列の部分に使う所)を
    外すと、同じ記号の道の文字列は書き換わるが、f 文字列の部分は一覧に出ずに残る。"""
    reader = 'def build(n):\n    p = "src/shibuya/pk/old.py"\n    return p, f"from shibuya.pk import old; old.f({n})"\n'
    tree, md = _split_sample({"tests/test_fstr.py": reader})
    # 〔割る段 6・E8〕名の手がかりの無い道 p は宣言で主な割り先へ(宣言が無ければ手で直す一覧に 2 つ目の行として出る)
    monkeypatch.setattr(SP, "SPLIT_PATH_DESTS", (SP.PathDest("pk/old.py", "tests/test_fstr.py", "build", "nw/main.py"),))
    with pytest.raises(SP.SplitRefused, match="手で直す"):
        SP.make_split_plan(tree, md, "pk/old.py", check_order=False)
    plan = SP.make_split_plan(tree, md, "pk/old.py", check_order=False, strict=False)
    got = plan.after.files["tests/test_fstr.py"]
    assert '"src/shibuya/nw/main.py"' in got and 'f"from shibuya.pk import old; old.f({n})"' in got
    man = [m for m in plan.manual if "tests/test_fstr.py::build" in m]
    assert len(man) == 1 and "f 文字列の部分の中のコード" in man[0], plan.manual
    monkeypatch.setattr(ST, "code_import_hits", lambda ctx, value: [])
    plan2 = SP.make_split_plan(tree, md, "pk/old.py", check_order=False, strict=False)
    assert plan2.after.files["tests/test_fstr.py"] == got and not [m for m in plan2.manual if "test_fstr" in m]


# ------------------------------------------------------------------ 〔割る段 5b の G2 の直し〕検収の低-4・低-2
def _missing_string_excludes(entries) -> list[str]:  # noqa: ANN001
    """``split.STRING_EXCLUDE`` の (ファイル, 記号) のうち、今の木にファイルが無いか、記号がそのファイルの記号(道具が文字列の
    記号を引くのと同じ ``symbol_map``=頂上の代入・関数・クラス)に無いもの。"""
    out: list[str] = []
    for rel, sym in sorted(entries):
        p = ROOT / rel
        if not p.is_file():
            out.append(f"{rel}: ファイルが無い")
            continue
        if sym not in set(symbol_map(ast.parse(p.read_text(encoding="utf-8"))).values()):
            out.append(f"{rel}::{sym}: 記号が無い")
    return out


def test_string_excludes_name_symbols_that_exist_in_the_tree():
    """〔G2 の検収 低-4〕``STRING_EXCLUDE`` の除外は (ファイル, 記号) の字面で当たる=記号を改名・移すと除外が黙って外れる。今の木で
    全部のファイルが在り、記号がそのファイルで定義されていること。負の対照: 在りもしない記号を 1 つ足した一覧では「無い」と言う。"""
    assert _missing_string_excludes(SP.STRING_EXCLUDE) == []
    fake = ("tests/engine/test_state_format_10f.py", "_NO_SUCH_CHILD")
    assert _missing_string_excludes({*SP.STRING_EXCLUDE, fake}) == [f"{fake[0]}::{fake[1]}: 記号が無い"]
    assert _missing_string_excludes({("tests/no_such_file.py", "X")}) == ["tests/no_such_file.py: ファイルが無い"]


_THREE_SAMPLE = '"""three — 見本の 3 本目の元のファイル。"""\n\nfrom __future__ import annotations\n\nV = 1\nW = 2\n'
_THREE_ROW = dict(num="3", old="pk/three.py", package="nw", kind="split", new="nw/three.py",
                  split_to=("nw/three.py", "vocab/base.py"), names=(("V", "nw/three.py"), ("W", "vocab/base.py")),
                  names_complete=True)


def test_split_order_is_kept_in_a_sample_tree(monkeypatch):
    """〔G2 の検収 低-2〕割る段の順(``split_state``・``next_split``・``make_split_plan`` の順の確かめ)を見本の木で確かめる。本物の
    木の ``test_split_order_is_kept_in_the_real_tree`` は残りの本が 2 本未満で飛ぶ(割る段の終わり)ので、同じ確かめをここで残す:
    どの時点でも次の 1 本のほかは「順が違う」で断り、済んだ本は「当たっている」で断る。"""
    monkeypatch.setattr(SP, "SPLIT_ORDER", ("pk/old.py", "pk/two.py", "pk/three.py"))
    tree, _md = _split_sample({"src/shibuya/pk/two.py": _TWO_SAMPLE, "src/shibuya/pk/three.py": _THREE_SAMPLE})
    md = MV.MapDoc(rows=[Row(**_SAMPLE_ROW), Row(**_TWO_ROW), Row(**_THREE_ROW)])
    done: list[str] = []
    for old in SP.SPLIT_ORDER:
        assert SP.split_state(tree, md) == done and SP.next_split(tree, md) == old
        for later in SP.SPLIT_ORDER[len(done) + 1:]:
            with pytest.raises(SP.SplitRefused, match="順が違う"):
                SP.make_split_plan(tree, md, later)
        for prev in done:
            with pytest.raises(SP.SplitRefused, match="当たっている"):
                SP.make_split_plan(tree, md, prev)
        tree = SP.make_split_plan(tree, md, old).after
        done.append(old)
    assert SP.split_state(tree, md) == list(SP.SPLIT_ORDER) and SP.next_split(tree, md) is None


# ------------------------------------------------------------------ 〔割る段 5b の G3 の前・E5-a〕別名の割り先の宣言
#: 見本の読み手: 別名 cli で run(ui/main.py)を呼び、run が呼ぶ時に読む helper(定義は ui/wire.py)を同じ別名で差し替える。
#: 別名 cli_wire は helper(ui/wire.py)だけを読む=道具の既定で向く。
_ALIAS_READER = ('from shibuya import cli\nfrom shibuya import cli as cli_wire\n\n\n'
                 'def test_run(monkeypatch):\n    monkeypatch.setattr(cli, "helper", lambda x: x)\n'
                 '    assert cli.run(1) == 1 and cli_wire.helper(1) == 2\n')
_ALIAS_FILE = "tests/test_alias_r.py"


def _alias_sample(monkeypatch, decls, reader: str = _ALIAS_READER) -> tuple[Tree, MV.MapDoc]:
    tree, md = _cli_sample(monkeypatch)
    tree.files[_ALIAS_FILE] = reader
    monkeypatch.setattr(SP, "SPLIT_ALIAS_DESTS", tuple(decls))
    return tree, md


def _alias_errors(monkeypatch, decls, reader: str = _ALIAS_READER) -> list[str]:
    tree, md = _alias_sample(monkeypatch, decls, reader)
    with pytest.raises(SP.SplitStopped) as ei:
        SP.make_split_plan(tree, md, "cli.py", check_order=False, strict=False)
    errs = ei.value.errors
    assert errs and all(e.startswith("別名の割り先の宣言の守り: ") for e in errs), errs
    return errs


def test_split_alias_declaration_points_the_alias_to_the_declared_dest(monkeypatch):
    """〔E5-a〕宣言の在る別名は、名の定義の割り先でなく宣言の割り先へ向く(読む名が割り先をまたいでも手で直す一覧に出ない)。
    宣言の無い別名は今までどおり(読む名の割り先が 1 つなら向き、2 つにまたがれば手で直す一覧へ・``strict`` なら断る)。報告の
    ``alias_declared`` に使った宣言が出る。負の対照: 宣言を外すと、同じ読み手が手で直す一覧に出て当てられない。"""
    decl = SP.AliasDest("cli.py", _ALIAS_FILE, "cli", "ui/main.py")
    tree, md = _alias_sample(monkeypatch, [decl])
    plan = SP.make_split_plan(tree, md, "cli.py", check_order=False)
    r = plan.after.files[_ALIAS_FILE]
    assert r.startswith("from shibuya.ui import main as cli\nfrom shibuya.ui import wire as cli_wire\n"), r
    assert 'monkeypatch.setattr(cli, "helper", lambda x: x)' in r and "from shibuya.ui.wire import helper\n" in \
        plan.after.files["src/shibuya/ui/main.py"]
    assert plan.manual == [] and set(plan.guards.values()) == {"同じ"}
    assert SP.report(plan)["alias_declared"] == [f"{_ALIAS_FILE}: 別名 cli → ui/main.py(読む名 2)"]
    # 負の対照: 宣言が無い
    tree, md = _alias_sample(monkeypatch, [])
    plan2 = SP.make_split_plan(tree, md, "cli.py", check_order=False, strict=False)
    assert [m for m in plan2.manual if _ALIAS_FILE in m and "別名 cli の読みの割り先が 1 つに決まらない" in m]
    assert "from shibuya.ui import wire as cli_wire\n" in plan2.after.files[_ALIAS_FILE]  # 宣言の無い別名は道具の既定のまま
    assert SP.report(plan2)["alias_declared"] == []
    with pytest.raises(SP.SplitRefused, match="手で直す一覧"):
        SP.make_split_plan(tree, md, "cli.py", check_order=False)


@pytest.mark.parametrize("decl,reader,word", [
    # 別名が割るモジュールを import していない(同じ名の別名を別のモジュールに結ぶ)
    (SP.AliasDest("cli.py", _ALIAS_FILE, "cli", "ui/main.py"),
     _ALIAS_READER.replace("from shibuya import cli\n", "import os as cli\n"), "割るモジュール shibuya.cli を import していない"),
    # 宣言の割り先が、その割る行の割り先でない
    (SP.AliasDest("cli.py", _ALIAS_FILE, "cli", "ui/other.py"), _ALIAS_READER, "この割る行の割り先でない"),
    # 別名で読む名(run)が割り先(ui/wire.py)の頂上で結ばれていない
    (SP.AliasDest("cli.py", _ALIAS_FILE, "cli", "ui/wire.py"), _ALIAS_READER,
     "別名で読む名 ['run'] が割り先の頂上で結ばれていない"),
    # 名で読まない使い方(別名を素で渡す)=読む名を確かめられない
    (SP.AliasDest("cli.py", _ALIAS_FILE, "cli", "ui/main.py"), _ALIAS_READER + "\n\nMODS = [cli]\n", "名で読まない使い方がある"),
    # 宣言が使われなかった(ファイルが木に無い・別名がファイルに無い)
    (SP.AliasDest("cli.py", "tests/no_such_reader.py", "cli", "ui/main.py"), _ALIAS_READER, "宣言が使われなかった"),
    (SP.AliasDest("cli.py", _ALIAS_FILE, "cli_nope", "ui/main.py"), _ALIAS_READER, "宣言が使われなかった"),
])
def test_negative_alias_declaration_guards_each_stop(monkeypatch, decl, reader, word):
    """〔E5-a の守り〕宣言の守りは 1 つずつ止める(書かない・止めた文に場所と名): 別名が割るモジュールを import していない・宣言の
    割り先がその行の割り先でない・別名で読む名が割り先の頂上で結ばれていない・名で読まない使い方がある・宣言が使われなかった。
    書かない実行(``strict`` が偽)でも止める。"""
    errs = _alias_errors(monkeypatch, [decl], reader)
    assert any(word in e for e in errs), errs
    assert all(decl.file in e for e in errs), errs


def test_alias_declaration_names_the_names_that_may_be_absent(monkeypatch):
    """〔E5-a の 4〕割り先に無くてよい名(常に偽の ``hasattr`` で守られた読み): 宣言に名前で挙げれば通り、挙げなければ止まる
    (黙って通さない)。挙げた名を別名で読んでいない・挙げた名が割り先に在る、も止める(宣言が腐らない)。"""
    reader = ('from shibuya import cli\n\n\ndef test_x():\n'
              '    ap = cli.build_parser() if hasattr(cli, "build_parser") else None\n    assert cli.run(1) == 2\n'
              '    del ap\n')
    ok = SP.AliasDest("cli.py", _ALIAS_FILE, "cli", "ui/main.py", absent=("build_parser",))
    tree, md = _alias_sample(monkeypatch, [ok], reader)
    plan = SP.make_split_plan(tree, md, "cli.py", check_order=False)
    assert plan.after.files[_ALIAS_FILE].startswith("from shibuya.ui import main as cli\n") and plan.manual == []
    assert SP.report(plan)["alias_declared"] == [
        f"{_ALIAS_FILE}: 別名 cli → ui/main.py(読む名 2・無くてよい名 build_parser)"]
    errs = _alias_errors(monkeypatch, [SP.AliasDest("cli.py", _ALIAS_FILE, "cli", "ui/main.py")], reader)
    assert any("['build_parser'] が割り先の頂上で結ばれていない" in e for e in errs), errs
    errs = _alias_errors(monkeypatch, [dataclasses.replace(ok, absent=("build_parser", "no_such"))], reader)
    assert any("無くてよいと挙げた名 ['no_such'] をこの別名で読んでいない" in e for e in errs), errs
    errs = _alias_errors(monkeypatch, [dataclasses.replace(ok, absent=("build_parser", "run"))], reader)
    assert any("無くてよいと挙げた名 ['run'] が割り先の頂上に在る" in e for e in errs), errs


def _stale_alias_dests(decls) -> list[str]:  # noqa: ANN001
    """``split.SPLIT_ALIAS_DESTS`` の宣言のうち、今の木にファイルが無いか、その別名を「割る前のモジュール」か「宣言の割り先」の
    どちらでもないモジュールに結ぶ(または結ばない)もの。割る前と、割った後(道具が別名の import を宣言の割り先へ書き換えた後)の
    どちらの木でも空になる。"""
    out: list[str] = []
    for d in decls:
        p = ROOT / d.file
        if not p.is_file():
            out.append(f"{d.file}: ファイルが無い")
            continue
        mods = SP.alias_modules(p.read_text(encoding="utf-8"), d.file).get(d.alias, set())
        ok = {mod_of(d.old), mod_of(d.dest)}
        if not mods or not mods <= ok:
            out.append(f"{d.file}: 別名 {d.alias} が結ぶのは {sorted(mods)}(割る前 {mod_of(d.old)} か割り先 {mod_of(d.dest)})")
    return out


def test_alias_declarations_name_files_and_aliases_that_exist_in_the_tree():
    """〔E5-a の 5・F2 と同じ考え方〕当てた後に宣言が黙って腐らないこと: 宣言のファイルが今の木に在り、その別名が割る前の
    モジュールか宣言の割り先を import している。負の対照: 在りもしないファイル・別のモジュールに結ぶ別名・在りもしない別名。"""
    assert _stale_alias_dests(SP.SPLIT_ALIAS_DESTS) == []
    assert {d.old for d in SP.SPLIT_ALIAS_DESTS} <= set(SP.SPLIT_ORDER)
    real = SP.SPLIT_ALIAS_DESTS[0]
    assert _stale_alias_dests([dataclasses.replace(real, file="tests/no_such_file.py")]) == [
        "tests/no_such_file.py: ファイルが無い"]
    # 別名が割る前のモジュールにも宣言の割り先にも結ばれていない(割る前と割った後のどちらの木でも当たる形)
    got = _stale_alias_dests([dataclasses.replace(real, old="engine/run.py", dest="interfaces/cli/run_args.py")])
    assert got and "(割る前 shibuya.engine.run か割り先 shibuya.interfaces.cli.run_args)" in got[0], got
    assert _stale_alias_dests([dataclasses.replace(real, alias="no_such_alias")]) == [
        f"{real.file}: 別名 no_such_alias が結ぶのは [](割る前 shibuya.cli か割り先 shibuya.interfaces.cli.main)"]


# ------------------------------------------------------------------ 〔割る段 6 の S6-G0・E7〕台帳の道の前向きの表(親の裁定 Q1 の (ii))
_LP_HEAD = ('"""ledger_paths — 見本の台帳の道の表。"""\n\nfrom __future__ import annotations\n\n'
            "from types import MappingProxyType\nfrom typing import Final, Mapping\n\n")


def _lp_text(main: dict[str, str], split: dict[str, str] | None = None) -> str:
    """見本の ``ledger_paths.py``(``LEDGER_PATHS``・``split`` を渡せば ``LEDGER_PATHS_SPLIT`` も。鍵の昇順・1 行 1 組)。"""
    def lit(d: dict[str, str]) -> str:
        return "MappingProxyType({\n" + "".join(f'    "{k}": "{v}",\n' for k, v in sorted(d.items())) + "})\n"
    out = _LP_HEAD + "LEDGER_PATHS: Final[Mapping[str, str]] = " + lit(main)
    if split is not None:
        out += "\nLEDGER_PATHS_SPLIT: Final[Mapping[str, str]] = " + lit(split)
    return out


def test_ledger_paths_forward_table_reads_writes_and_follows_moves():
    """〔E7〕前向きの表(``LEDGER_PATHS_SPLIT``): 字面は ``LEDGER_PATHS`` と同じ形(鍵の昇順・1 行 1 組・空なら ``{`` の次の行が
    ``}``)。前向きに引く順は 1 対 1 の表 → 前向きの表 → そのまま。前向きの表の値は 1 対 1 の表の値と重なってよい。移すとき、前向きの
    表に載った鍵は前向きの表のまま付いて行く。表が無い木に行を足そうとすれば「前向きの表が無い」で止める。2 つの表の両方に同じ
    今の道は置かない。前向きの表は中身が変わったときだけ書き直す。"""
    a, b, c = "src/shibuya/a.py", "src/shibuya/b.py", "src/shibuya/c.py"
    led = "src/shibuya/old.py"
    empty = _lp_text({a: led}, {})
    assert "LEDGER_PATHS_SPLIT: Final[Mapping[str, str]] = MappingProxyType({\n})\n" in empty
    assert LPT.split_table_of(empty) == {} and LPT.split_table_of(_lp_text({a: led})) is None
    # 前向きの表に足す(値は 1 対 1 の表の値と重なってよい)・1 対 1 の表は移した行だけ
    t1, n1 = LPT.rewrite(empty, {}, {b: led})
    assert t1 == _lp_text({a: led}, {b: led}) and n1 == 1
    assert LPT.ledger_of(LPT.table_of(t1), LPT.split_table_of(t1), b) == led
    assert LPT.ledger_of(LPT.table_of(t1), LPT.split_table_of(t1), a) == led
    assert LPT.ledger_of(LPT.table_of(t1), LPT.split_table_of(t1), c) == c
    # 移す: 前向きの表に載った鍵は前向きの表のまま付いて行く・1 対 1 の表の鍵は 1 対 1 の表のまま
    d, e = "src/shibuya/d.py", "src/shibuya/e.py"
    t2, n2 = LPT.rewrite(t1, {b: d, a: e})
    assert t2 == _lp_text({e: led}, {d: led}) and n2 == 2
    # 1 対 1 の表だけを移すときは前向きの表の字面を書き直さない
    t3, _ = LPT.rewrite(t1, {a: e})
    assert t3.split("LEDGER_PATHS_SPLIT")[1] == t1.split("LEDGER_PATHS_SPLIT")[1]
    # 前向きの表が無い木=1 対 1 の表だけ(前と同じ字面)・行を足そうとすれば止める
    old_style = _lp_text({a: led})
    t4, _ = LPT.rewrite(old_style, {a: e})
    assert t4 == _lp_text({e: led})
    with pytest.raises(LPT.LedgerPathsError, match="前向きの表が無い"):
        LPT.rewrite(old_style, {}, {b: led})
    # 同じ今の道を 2 つの表に置かない・在る鍵へ足さない・1 対 1 の表の値は重ならない
    with pytest.raises(LPT.LedgerPathsError, match="既に在る"):
        LPT.rewrite(t1, {}, {a: led})
    with pytest.raises(LPT.LedgerPathsError, match="両方に在る"):
        LPT.rewrite(t1, {b: a})
    with pytest.raises(LPT.LedgerPathsError, match="台帳の道が重なる"):
        LPT.updated({a: led, c: led}, {})
    assert LPT.updated({a: led, b: led}, {}, unique_values=False) == {a: led, b: led}


def test_ledger_paths_check_sees_the_forward_table():
    """〔E7〕``check``: 前向きの表の今の道は木に在る・同じ今の道が 2 つの表の両方に無い。台帳の行は 1 対 1 の表だけで逆に引く
    (前向きの表の値は逆に引かない)。"""
    a, b = "src/shibuya/a.py", "src/shibuya/b.py"
    led = "src/shibuya/old.py"
    tree = {a, b}
    exists = tree.__contains__
    ledger = json.dumps({"bridges": [{"id": "X", "declared_in": f"{led}#docstring:abc"}]})
    assert LPT.check({a: led}, exists, ledger, split={b: led}) == []
    assert LPT.check({a: led}, exists, ledger, split={"src/shibuya/gone.py": led}) == [
        "前向きの表の今の道が木に無い: src/shibuya/gone.py"]
    assert LPT.check({a: led}, exists, None, split={a: led}) == [f"同じ今の道が 2 つの表の両方に在る: ['{a}']"]
    # 台帳の行は 1 対 1 の表で引く(前向きの表だけに載る道は逆に引かない=元の道のまま=木に無ければ届かない)
    assert LPT.check({}, exists, ledger, split={b: led}) == [f"台帳の道が今のファイルに届かない: X {led} → {led}"]


_LP_PATH = "src/shibuya/engine/bridging/ledger_paths.py"
_DECL_H = '\n\ndef h() -> int:\n    """仮の値を返す。\n\n    expedient: 見本の仮の値。\n    """\n    return 1\n'
_PLAIN_Z = "\n\nZ = 7\n"


def _e7_sample(*, lp: str | None = "split", h_dest: str = "nw/extra.py", extra: dict[str, str] | None = None):
    """見本の木: 元のファイルに宣言(``h`` の docstring の ``expedient:``)と宣言の無い名(``Z``)を足し、2 つ目以降の新しい割り先
    ``nw/extra.py``(宣言あり)・``nw/plain.py``(宣言なし)へ割る。``lp``: ``"split"``=前向きの表のある台帳の道の表・``"main"``=
    1 対 1 の表だけ・``None``=表のファイルが無い。"""
    files: dict[str, str] = {"src/shibuya/pk/old.py": _OLD_SAMPLE + _DECL_H + _PLAIN_Z, **(extra or {})}
    if lp is not None:
        files.update({"src/shibuya/engine/__init__.py": "", "src/shibuya/engine/bridging/__init__.py": "",
                      _LP_PATH: _lp_text({}, {} if lp == "split" else None)})
    return _split_sample(files, names=(*_SAMPLE_ROW["names"], ("h", h_dest), ("Z", "nw/plain.py")),
                         split_to=("nw/main.py", "vocab/base.py", "nw/extra.py", "nw/plain.py"))


def test_split_writes_a_forward_ledger_row_for_a_second_destination_with_a_declaration():
    """〔E7〕宣言の入る 2 つ目以降の新しい割り先(``nw/extra.py``)ごとに、前向きの表へ「割り先の今の道 → 元のファイルの台帳の道」を
    1 行書き足す。宣言の入らない割り先(``nw/plain.py``)の行は書かない(裁定 Q1 の条件 ③)。主な割り先の行は今までどおり 1 対 1 の
    表へ。守り ④ は台帳の道(1 対 1 の表 → 前向きの表 → そのまま)で数えて「同じ」。"""
    tree, md = _e7_sample()
    plan = SP.make_split_plan(tree, md, "pk/old.py", check_order=False)
    lp = plan.after.files[_LP_PATH]
    assert lp == _lp_text({"src/shibuya/nw/main.py": "src/shibuya/pk/old.py"},
                          {"src/shibuya/nw/extra.py": "src/shibuya/pk/old.py"})
    assert plan.ledger_paths_added == 1 and plan.ledger_paths_split == ["src/shibuya/nw/extra.py → src/shibuya/pk/old.py"]
    assert SP.report(plan)["ledger_paths_split"] == plan.ledger_paths_split
    assert plan.dests["nw/plain.py"] == "new" and "src/shibuya/nw/plain.py" not in lp
    assert set(plan.guards.values()) == {"同じ"} and plan.guards["declarations"] == "同じ"


def test_split_writes_a_forward_ledger_row_when_the_main_destination_is_the_source_file():
    """〔E7〕主な割り先が元のファイルの今の置き場の行(延ばした 18 本目の形): 1 対 1 の表は変えず、宣言の入る 2 つ目以降の割り先へ
    元のファイルの台帳の道(1 対 1 の表で引いた道)を前向きの表に書き足す。"""
    port = ('"""port — 見本。"""\n\nfrom __future__ import annotations\n\n_K: frozenset[str] = frozenset("ab")\n\n\n'
            'def m(s: str) -> int:\n    """数える。\n\n    expedient: 見本の仮の数え方。\n    """\n'
            "    return sum(1 for c in s if c not in _K)\n\n\nclass P:\n    def n(self) -> int:\n        return m(\"abc\")\n")
    led = {"src/shibuya/sp/port.py": "src/shibuya/old/port.py"}
    files = {"src/shibuya/__init__.py": "", "src/shibuya/sp/__init__.py": "", "src/shibuya/sp/port.py": port,
             "src/shibuya/sp/use.py": "from shibuya.sp.port import P, m\n", "src/shibuya/engine/__init__.py": "",
             "src/shibuya/engine/bridging/__init__.py": "", _LP_PATH: _lp_text(led, {})}
    row = Row(num="1", old="old/port.py", package="sp", kind="split", new="sp/port.py", split_to=("sp/port.py", "txt/mora.py"),
              names=(("_K", "txt/mora.py"), ("m", "txt/mora.py"), ("P", "sp/port.py")), names_complete=True)
    plan = SP.make_split_plan(Tree(files=files), MV.MapDoc(rows=[row]), "old/port.py", check_order=False)
    assert plan.in_place and plan.ledger_paths_added == 0
    assert plan.after.files[_LP_PATH] == _lp_text(led, {"src/shibuya/txt/mora.py": "src/shibuya/old/port.py"})
    assert set(plan.guards.values()) == {"同じ"}


def _drop_decl(out: dict[str, str]) -> dict[str, str]:
    t = out["nw/extra.py"]
    assert "\n\n    expedient: 見本の仮の値。\n    " in t
    return {**out, "nw/extra.py": t.replace("\n\n    expedient: 見本の仮の値。\n    ", "\n    ")}


@pytest.mark.parametrize("case,words", [
    # 2 つ目以降の割り先の宣言を 1 つ消す(組み立ての後に字面を変える)=台帳の道で数える宣言が元より減る
    ("drop_decl", ["④ 宣言: つなぎの台帳の宣言が元と割り先とで違う"]),
    # 前向きの表の行を 1 つ落とす=宣言の入った割り先が前向きの表に無い・台帳の道で数えると元と違う
    ("drop_row", ["④ 宣言: 2 つ目以降の割り先 nw/extra.py につなぎの台帳の宣言が入るが", "④ 宣言: つなぎの台帳の宣言が元と"]),
    # 宣言の無い割り先の行を足す(条件 ③)
    ("add_plain_row", ["④ 宣言: 宣言の無い 2 つ目以降の割り先 nw/plain.py の行が前向きの表に在る",
                       "④ 台帳の道の表: 前向きの表の今の道 src/shibuya/nw/plain.py に宣言が無い"]),
    # 既に在る割り先(別の台帳の道を持つ)へ宣言が入る=今までどおり止める
    ("existing_dest", ["④ 宣言: 既に在る割り先 vocab/base.py につなぎの台帳の宣言が入る", "④ 宣言: つなぎの台帳の宣言が元と"]),
])
def test_negative_forward_ledger_rows_keep_guard_4_as_strict_as_before(monkeypatch, case, words):
    """〔E7・裁定 Q1 の条件 ④〕比べの厳しさは前と同じ: 2 つ目以降の割り先の宣言を 1 つ消す・前向きの表の行を 1 つ落とす・宣言の
    無い割り先の行を足す・既に在る割り先へ宣言が入る、のどれでも守り ④ が止める。"""
    compose_fn = None
    if case == "existing_dest":
        tree, md = _e7_sample(h_dest="vocab/base.py")
    else:
        tree, md = _e7_sample()
    if case == "drop_decl":
        compose_fn = _then(_drop_decl)
    elif case == "drop_row":
        monkeypatch.setattr(SP, "ledger_split_rows", lambda plan, lp_text: {})
    elif case == "add_plain_row":
        real = SP.ledger_split_rows
        monkeypatch.setattr(SP, "ledger_split_rows", lambda plan, lp_text: {
            **real(plan, lp_text), "src/shibuya/nw/plain.py": "src/shibuya/pk/old.py"})
    with pytest.raises(SP.SplitStopped) as ei:
        SP.make_split_plan(tree, md, "pk/old.py", check_order=False, compose_fn=compose_fn)
    for w in words:
        assert any(e.startswith(w) for e in ei.value.errors), (w, ei.value.errors)


def test_negative_a_tree_without_the_forward_table_stops_when_a_row_is_needed():
    """〔E7〕前向きの表が無い木(src の側の下ごしらえ S6-A の前)で、宣言の入る 2 つ目以降の割り先があれば「前向きの表が無い」で止める
    (黙って通さない)。表のファイルが無い木は守り ④ が止める(前と同じ)。宣言の入る 2 つ目以降の割り先が無ければ、表が無くても
    前と同じに 1 対 1 の表へ主な割り先の行を足して通る。"""
    tree, md = _e7_sample(lp="main")
    with pytest.raises(SP.SplitStopped) as ei:
        SP.make_split_plan(tree, md, "pk/old.py", check_order=False)
    assert len(ei.value.errors) == 1 and "前向きの表が無い" in ei.value.errors[0], ei.value.errors
    tree, md = _e7_sample(lp=None)
    with pytest.raises(SP.SplitStopped) as ei:
        SP.make_split_plan(tree, md, "pk/old.py", check_order=False)
    assert any(e.startswith("④ 宣言: 2 つ目以降の割り先 nw/extra.py") for e in ei.value.errors), ei.value.errors
    tree, md = _e7_sample(lp="main", h_dest="nw/main.py")
    plan = SP.make_split_plan(tree, md, "pk/old.py", check_order=False)
    assert plan.after.files[_LP_PATH] == _lp_text({"src/shibuya/nw/main.py": "src/shibuya/pk/old.py"})
    assert plan.ledger_paths_split == [] and set(plan.guards.values()) == {"同じ"}


# ------------------------------------------------------------------ 〔割る段 6 の S6-G0・E8〕道の文字列の割り先の宣言(親の裁定 Q8)
_E8_FILE = "tests/test_e8.py"
_E8_READER = ('ROOT = None\n'
              'P = "src/shibuya/pk/old.py"\n'
              'S = "see src/shibuya/pk/old.py:3"\n'
              'CH = ROOT / "pk" / "old.py"\n'
              'M = "shibuya.pk.old"\n'
              'G = ("src/shibuya/pk/old.py", "f")\n'
              'Q = "nothing here"\n')


def _e8_plan(monkeypatch, decls, *, strict: bool = True, reader: str = _E8_READER, extra=None, **row_kw):
    monkeypatch.setattr(SP, "SPLIT_PATH_DESTS", tuple(decls))
    tree, md = _split_sample({_E8_FILE: reader, **(extra or {})}, **row_kw)
    return SP.make_split_plan(tree, md, "pk/old.py", check_order=False, strict=strict)


def test_split_path_declarations_point_nameless_paths_to_the_declared_dest(monkeypatch):
    """〔E8〕名の手がかりの無い割るファイルの道(斜線の道の全体・文の中の斜線の道・``/`` の連鎖・名の無い点の道)は、その記号の宣言の
    割り先へ。名の手がかりの在る道(同じ組の名)は前と同じく名の割り先へ(宣言は要らない)。使った宣言は報告の ``path_declared``。"""
    decls = [SP.PathDest("pk/old.py", _E8_FILE, s, "vocab/base.py") for s in ("P", "S", "CH", "M")]
    plan = _e8_plan(monkeypatch, decls)
    got = plan.after.files[_E8_FILE]
    assert got == ('ROOT = None\n'
                   'P = "src/shibuya/vocab/base.py"\n'
                   'S = "see src/shibuya/vocab/base.py:3"\n'
                   'CH = ROOT / "vocab" / "base.py"\n'
                   'M = "shibuya.vocab.base"\n'
                   'G = ("src/shibuya/nw/main.py", "f")\n'
                   'Q = "nothing here"\n'), got
    assert plan.manual == [] and set(plan.guards.values()) == {"同じ"}
    assert SP.report(plan)["path_declared"] == [f"{_E8_FILE}::{s} → vocab/base.py(道 1)" for s in ("P", "S", "CH", "M")]


def test_negative_nameless_paths_without_a_declaration_are_listed_for_hand_fixing(monkeypatch):
    """〔E8〕宣言も名の手がかりも無い割るファイルの道は、割り先が 2 つ以上の行では主な割り先へ黙って向けず「手で直す一覧」へ出す
    (``strict`` は断る)。名の手がかりの在る道は前と同じに書き換える。割り先が 1 つの行は前と同じに主な割り先へ。宣言と組の名が
    食い違えば手で直す一覧へ。"""
    with pytest.raises(SP.SplitRefused, match="手で直す"):
        _e8_plan(monkeypatch, [])
    plan = _e8_plan(monkeypatch, [], strict=False)
    man = sorted(m.split(": ", 1)[0] for m in plan.manual if _E8_FILE in m)
    assert man == [f"{_E8_FILE}::{s}" for s in ("CH", "M", "P", "S")], plan.manual
    assert plan.after.files[_E8_FILE] == _E8_READER.replace('G = ("src/shibuya/pk/old.py"', 'G = ("src/shibuya/nw/main.py"')
    # 割り先が 1 つの行: 前と同じに主な割り先へ(手で直す一覧に出さない)
    one = _e8_plan(monkeypatch, [], reader='P = "src/shibuya/pk/old.py"\n', split_to=("nw/main.py",), rewrites=(),
                   names=tuple((n, "nw/main.py") for n, _d in _SAMPLE_ROW["names"]))
    assert one.after.files[_E8_FILE] == 'P = "src/shibuya/nw/main.py"\n' and one.manual == []
    # 宣言と組の名が食い違う=手で直す一覧(宣言は引いた=使われなかったとは言わない)
    clash = _e8_plan(monkeypatch, [SP.PathDest("pk/old.py", _E8_FILE, "G", "vocab/base.py")], strict=False,
                     reader='G = ("src/shibuya/pk/old.py", "f")\n')
    assert [m for m in clash.manual if "食い違う" in m and f"{_E8_FILE}::G" in m], clash.manual
    assert clash.after.files[_E8_FILE] == 'G = ("src/shibuya/pk/old.py", "f")\n'


def test_split_path_declarations_apply_to_the_src_tables(monkeypatch):
    """〔E8〕src の道の表(許可の一覧 (b-src)・規則 ``exact``)の、名の手がかりの無い割るファイルの道も宣言の割り先へ(段 6 の
    ``_ALLOW_REVENUE`` の形=組の中の文字列が名でない)。宣言が無ければ手で直す一覧へ。"""
    table = 'from __future__ import annotations\n\n_ALLOW_REVENUE = (("pk/old.py", "_req(world, world.x)"),)\n'
    extra = {"src/shibuya/engine/__init__.py": "", "src/shibuya/engine/state_ledger.py": table}
    assert ("engine/state_ledger.py", "_ALLOW_REVENUE") in {(f, s) for f, s, _w in AL.SRC_TABLES}
    plan = _e8_plan(monkeypatch, [SP.PathDest("pk/old.py", "src/shibuya/engine/state_ledger.py", "_ALLOW_REVENUE",
                                              "vocab/base.py")], reader="", extra=extra)
    assert plan.after.files["src/shibuya/engine/state_ledger.py"] == table.replace('"pk/old.py"', '"vocab/base.py"')
    assert set(plan.guards.values()) == {"同じ"}
    plan = _e8_plan(monkeypatch, [], reader="", extra=extra, strict=False)
    assert [m for m in plan.manual if "src/shibuya/engine/state_ledger.py::_ALLOW_REVENUE" in m], plan.manual
    assert plan.after.files["src/shibuya/engine/state_ledger.py"] == table


@pytest.mark.parametrize("decls,word", [
    ([SP.PathDest("pk/old.py", "tests/no_such.py", "P", "vocab/base.py")], "ファイルが木に無い"),
    ([SP.PathDest("pk/old.py", _E8_FILE, "NOPE", "vocab/base.py")], "記号がファイルに無い"),
    ([SP.PathDest("pk/old.py", _E8_FILE, "P", "nw/other.py")], "この割る行の割り先でない"),
    ([SP.PathDest("pk/old.py", "tools/bytecheck/x.py", "P", "vocab/base.py")], "範囲の外"),
    ([SP.PathDest("pk/old.py", _E8_FILE, "P", "vocab/base.py")] * 2, "同じ記号に宣言が 2 つ"),
    ([SP.PathDest("pk/old.py", _E8_FILE, "Q", "vocab/base.py")], "宣言が使われなかった"),
])
def test_negative_path_declaration_guards_each_stop(monkeypatch, decls, word):
    """〔E8 の守り・E5-a と同じ考え〕宣言はその割る行でだけ使う・ファイルと記号が木に在る・宣言の割り先はその行の割り先・記号は
    書き換えの範囲の中・同じ記号に 2 つ無い・使われなかった宣言は止める(書かない実行でも止める)。"""
    extra = {"tools/bytecheck/x.py": 'P = "src/shibuya/pk/old.py"\n'}
    with pytest.raises(SP.SplitStopped) as ei:
        _e8_plan(monkeypatch, decls, strict=False, extra=extra)
    assert all(e.startswith("道の文字列の割り先の宣言の守り: ") for e in ei.value.errors), ei.value.errors
    assert any(word in e for e in ei.value.errors), ei.value.errors


def test_path_declarations_of_other_rows_are_not_used(monkeypatch):
    """〔E8〕宣言はその割る行でだけ使う: 別の割る行の宣言は、この行では引かない(使われなかったとも言わない)。"""
    plan = _e8_plan(monkeypatch, [SP.PathDest("pk/other.py", _E8_FILE, "P", "vocab/base.py")], strict=False)
    assert f"{_E8_FILE}::P" in "".join(plan.manual) and plan.path_declared == []


def _stale_path_dests(decls) -> list[str]:  # noqa: ANN001
    """``split.SPLIT_PATH_DESTS`` の宣言のうち、今の木にファイルが無いか、記号がそのファイルの記号(``symbol_map``)に無いもの。"""
    out: list[str] = []
    for d in decls:
        p = ROOT / d.file
        if not p.is_file():
            out.append(f"{d.file}: ファイルが無い")
            continue
        if d.symbol not in set(symbol_map(ast.parse(p.read_text(encoding="utf-8"))).values()):
            out.append(f"{d.file}::{d.symbol}: 記号が無い")
    return out


def test_path_declarations_name_files_and_symbols_that_exist_in_the_tree():
    """〔E8〕宣言が黙って腐らないこと: 宣言のファイルが今の木に在り、記号がそのファイルの記号に在り、割る行が順に在る(今は空=
    段 6 の 2 行は割る行が順に入る次の発注で載せる)。負の対照: 在りもしないファイル・記号。"""
    assert _stale_path_dests(SP.SPLIT_PATH_DESTS) == []
    assert {d.old for d in SP.SPLIT_PATH_DESTS} <= set(SP.SPLIT_ORDER)
    fake = SP.PathDest("engine/resolve.py", "src/shibuya/runtime/state/ledger.py", "_NO_SUCH", "act/ops/shop.py")
    assert _stale_path_dests([fake]) == ["src/shibuya/runtime/state/ledger.py::_NO_SUCH: 記号が無い"]
    assert _stale_path_dests([dataclasses.replace(fake, file="src/shibuya/no_such.py")]) == [
        "src/shibuya/no_such.py: ファイルが無い"]


def test_string_exclude_has_the_fake_tree_sample_of_the_repo_guide_test():
    """〔裁定 R2〕``tests/tools/test_repo_guide.py::LAYER_SRC`` は偽の木(合成の木)に書く見本のコード=割る道具は書き換えない。
    見本の字面は合成の木の resolve を読み、本物の src のモジュールを import しない(合成の木の置き場へ書くだけ=AST で読む)。"""
    assert ("tests/tools/test_repo_guide.py", "LAYER_SRC") in SP.STRING_EXCLUDE
    text = (ROOT / "tests/tools/test_repo_guide.py").read_text(encoding="utf-8")
    t = ast.parse(text)
    layer = next(n.value.value for n in t.body if isinstance(n, ast.Assign)
                 and any(isinstance(x, ast.Name) and x.id == "LAYER_SRC" for x in n.targets))
    assert "from shibuya.engine import resolve as RV" in layer
    uses = [n for n in ast.walk(t) if isinstance(n, ast.Name) and n.id == "LAYER_SRC" and isinstance(n.ctx, ast.Load)]
    assert len(uses) == 1 and 'f"{S}/engine/layer.py": LAYER_SRC,' in text  # 合成の木の engine/layer.py に書くだけ


# ------------------------------------------------------------------ 〔割る段 6 の S6-G0・E5-b〕差し替えの届く先の守り(親の裁定の追記)
#: 見本の割るモジュール: helper は g(a)と h(b)が呼ぶ時に読む=届かせる割り先は a と b。N は b の頂上の表 TABLE と k の既定の引数が
#: 読み込みの時にだけ読む=(a) に数えず、名を結ぶ割り先 a(src の読み手 use.py が呼ぶ時に別名の属性で読む=(b) も a)。
_REACH_SRC = (
    '"""mod — 見本(差し替えの届く先)。"""\n'
    "\n"
    "from __future__ import annotations\n"
    "\n"
    "\n"
    "def helper(x: int) -> int:\n"
    "    return x + 1\n"
    "\n"
    "\n"
    "N = 5\n"
    "\n"
    "\n"
    "def g(x: int) -> int:\n"
    "    return helper(x)\n"
    "\n"
    "\n"
    "def h(x: int) -> int:\n"
    "    return helper(x) * 2\n"
    "\n"
    "\n"
    "def k(x: int = N) -> int:\n"
    "    return x\n"
    "\n"
    "\n"
    'TABLE = {"k": N}\n'
)
_REACH_ROW = dict(num="7", old="pk/mod.py", package="pk2", kind="split", new="pk2/a.py", split_to=("pk2/a.py", "pk2/b.py"),
                  names=(("helper", "pk2/a.py"), ("N", "pk2/a.py"), ("g", "pk2/a.py"), ("h", "pk2/b.py"), ("k", "pk2/b.py"),
                         ("TABLE", "pk2/b.py")), names_complete=True)
_REACH_FILE = "tests/test_reach.py"
_REACH_HEAD = "from shibuya.pk import mod as A\nfrom shibuya.pk import mod as B\n\n\n"
_REACH_BOTH = ('def test_both(monkeypatch):\n    monkeypatch.setattr(A, "helper", lambda x: x)\n'
               '    monkeypatch.setattr(B, "helper", lambda x: x)\n    assert A.g(1) == 1 and B.h(1) == 2\n')
_REACH_USE = "from shibuya.pk import mod as M\n\n\ndef u() -> int:\n    return M.N\n"


def _reach(monkeypatch, body: str, *, decl_b: bool = True, strict: bool = True, head: str = _REACH_HEAD):
    """見本の木で割る(別名 B は宣言で b へ=読む名が a と b にまたがる)。止まれば止めた文の一覧、通れば計画を返す。"""
    monkeypatch.setattr(SP, "SPLIT_ALIAS_DESTS",
                        (SP.AliasDest("pk/mod.py", _REACH_FILE, "B", "pk2/b.py"),) if decl_b else ())
    monkeypatch.setattr(SP, "SPLIT_PATH_DESTS", ())
    files = {"src/shibuya/__init__.py": "", "src/shibuya/pk/__init__.py": "", "src/shibuya/pk/mod.py": _REACH_SRC,
             "src/shibuya/use.py": _REACH_USE, _REACH_FILE: head + body}
    try:
        return SP.make_split_plan(Tree(files=files), MV.MapDoc(rows=[Row(**_REACH_ROW)]), "pk/mod.py", check_order=False,
                                  strict=strict)
    except SP.SplitStopped as e:
        return e.errors


def test_patch_reach_passes_when_patches_point_to_every_reading_destination(monkeypatch):
    """〔E5-b〕読む関数が 2 つの割り先(g=a・h=b)に分かれた名 helper を、同じ関数の中で両方の割り先の別名で差し替える形は通る。
    確かめた差し替えは報告の ``patch_checked``。読み込みの時にだけ読む文(既定の引数・頂上の表)は ``patch_load_time``。"""
    plan = _reach(monkeypatch, _REACH_BOTH)
    assert isinstance(plan, SP.SplitPlan), plan
    assert plan.guards["patch_reach"] == "同じ" and set(plan.guards.values()) == {"同じ"}
    assert plan.patch_checked == [f"{_REACH_FILE}::test_both helper → ['pk2/a.py', 'pk2/b.py'](差し替え 2)"]
    assert plan.patch_unseen == [] and plan.patch_load_time == []  # helper は読み込みの時に読まない
    # 属性への代入の形も同じ
    plan = _reach(monkeypatch, _REACH_BOTH.replace('monkeypatch.setattr(A, "helper", lambda x: x)', "A.helper = abs")
                  .replace('monkeypatch.setattr(B, "helper", lambda x: x)', "B.helper = abs"))
    assert isinstance(plan, SP.SplitPlan) and plan.patch_checked == [
        f"{_REACH_FILE}::test_both helper → ['pk2/a.py', 'pk2/b.py'](差し替え 2)"], plan


_HEAD_A = "from shibuya.pk import mod as A\n\n\n"
_HEAD_B = "from shibuya.pk import mod as B\n\n\n"


@pytest.mark.parametrize("body,head,decl_b,words", [
    # 片方の割り先だけ(b の h が読む helper に届かない)
    ('def test_one(monkeypatch):\n    monkeypatch.setattr(A, "helper", abs)\n    assert A.g(1)\n', _HEAD_A, False,
     ["test_one の名 helper", "届かない割り先 ['pk2/b.py']", "pk/mod.py:18 h→pk2/b.py"]),
    # 属性への代入で片方だけ
    ("def test_one():\n    A.helper = abs\n    assert A.g(1)\n", _HEAD_A, False, ["届かない割り先 ['pk2/b.py']"]),
    # 集合の外の割り先へ向く(N を呼ぶ時に読む関数は無く、b の頂上の表は読み込みの時に読む=b への差し替えは空振り)
    ('def test_n(monkeypatch):\n    monkeypatch.setattr(B, "N", 0)\n    assert B.TABLE\n', _HEAD_B, True,
     ["test_n の名 N", "届かない割り先 ['pk2/a.py']", "集合の外の割り先 ['pk2/b.py']", "src/shibuya/use.py:5(別名の属性)"]),
    # 文字列の的(名の割り先 a へ書き換わる=b の h に届かない)
    ('def test_s(monkeypatch):\n    monkeypatch.setattr("shibuya.pk.mod.helper", abs)\n', "", False,
     ["test_s の名 helper", "届かない割り先 ['pk2/b.py']"]),
    # コードの文字列の中(子のプロセスの台本)
    ('CODE = "from shibuya.pk import mod as A\\nA.helper = print\\nA.g(1)\\n"\n', "", False,
     ["CODE(コードの文字列) の名 helper", "届かない割り先 ['pk2/b.py']"]),
])
def test_negative_patch_reach_stops_patches_that_miss_a_reader(monkeypatch, body, head, decl_b, words):
    """〔E5-b〕割る前にその名を呼ぶ時に素の名で読んでいた関数の割り先の全部へ、同じ関数の中の差し替えが向いていなければ止める
    (名・読む文の場所・届かない割り先を出す)。集合の外の割り先へ向く差し替え(誰も読まない=空振り)も止める。形ごとに 1 つずつ:
    片方だけ・属性への代入・集合の外・文字列の的・コードの文字列の中。"""
    errs = _reach(monkeypatch, body, head=head, decl_b=decl_b)
    assert isinstance(errs, list) and errs and all(e.startswith("差し替えの届く先の守り: ") for e in errs), errs
    for w in words:
        assert any(w in e for e in errs), (w, errs)


def test_patch_reach_lists_load_time_reads_and_passes_string_and_code_targets_that_reach(monkeypatch):
    """〔E5-b〕名 N の差し替えを、名を結ぶ割り先 a(src の読み手が呼ぶ時に別名の属性で読む)へ向ける形は通り、読み込みの時にだけ
    読む文(頂上の表 TABLE・k の既定の引数)は ``patch_load_time`` に出る。呼ぶ時に読む関数の無い名 g の文字列の的とコードの文字列の
    中の差し替えは、名を結ぶ割り先 a へ向けば通る。"""
    body = ('def test_n(monkeypatch):\n    monkeypatch.setattr(A, "N", 0)\n    monkeypatch.setattr("shibuya.pk.mod.g", abs)\n'
            '    assert A.g(1)\n\n\nCODE = "from shibuya.pk import mod as A\\nA.g = print\\n"\n')
    plan = _reach(monkeypatch, body, head="from shibuya.pk import mod as A\n\n\n", decl_b=False)
    assert isinstance(plan, SP.SplitPlan), plan
    assert sorted(plan.patch_checked) == [f"{_REACH_FILE}::CODE(コードの文字列) g → ['pk2/a.py'](差し替え 1)",
                                          f"{_REACH_FILE}::test_n N → ['pk2/a.py'](差し替え 1)",
                                          f"{_REACH_FILE}::test_n g → ['pk2/a.py'](差し替え 1)"], plan.patch_checked
    load = plan.patch_load_time
    assert any("名 N: pk/mod.py:" in x and "k(デコレータ・既定の引数・注釈=読み込みの時)" in x for x in load), load
    assert any("名 N: pk/mod.py:" in x and "頂上の代入 TABLE(読み込みの時)" in x for x in load), load


def test_patch_reach_lists_patches_it_cannot_see(monkeypatch):
    """〔E5-b〕守りが見られなかった形は黙って通さず ``patch_unseen`` に出す(止めない): 名が字面の定数でない・的の文字列を組み立てる・
    割った後も別名が元のモジュールを指す(手で直す一覧に残る別名=``strict`` はその一覧で断る)。"""
    body = ('def test_dyn(monkeypatch, name="helper", n="g"):\n    monkeypatch.setattr(A, name, abs)\n'
            '    monkeypatch.setattr(f"shibuya.pk.mod.{n}", abs)\n    assert A.g(1)\n\n\n' + _REACH_BOTH)
    plan = _reach(monkeypatch, body, decl_b=False, strict=False)
    assert isinstance(plan, SP.SplitPlan), plan
    un = plan.patch_unseen
    assert any("setattr: 名が字面の定数でない" in x for x in un), un
    assert any("setattr: 的の文字列を組み立てる" in x for x in un), un
    assert any("test_both の名 helper" in x and "手で直す一覧の別名" in x for x in un), un
    assert plan.patch_checked == [] and plan.guards["patch_reach"] == "同じ"
    assert [m for m in plan.manual if _REACH_FILE in m and "別名 B" in m], plan.manual
    with pytest.raises(SP.SplitRefused, match="手で直す"):
        _reach(monkeypatch, body, decl_b=False, strict=True)


def test_negative_patch_reach_guard_is_what_stops(monkeypatch):
    """〔E5-b の負の対照〕守りを外すと、片方だけの差し替えは止まらずに当たる(守りが止めていることの確かめ)。"""
    body = 'def test_one(monkeypatch):\n    monkeypatch.setattr(A, "helper", abs)\n    assert A.g(1)\n'
    assert isinstance(_reach(monkeypatch, body, decl_b=False, head=_HEAD_A), list)
    monkeypatch.setattr(SP, "patch_reach", lambda plan: [])
    plan = _reach(monkeypatch, body, decl_b=False, head=_HEAD_A)
    assert isinstance(plan, SP.SplitPlan) and plan.guards["patch_reach"] == "同じ"


# ------------------------------------------------------------------ 〔割る段 6 の S6-G0・検収の後の直し〕E5-b の中-1・低-1・低-3
#: 主な割り先が元のファイルの行(延ばした 18 本目の形): 元 ``sp/port.py`` に ``_K`` と ``P`` が残り、``m`` は ``txt/mora.py`` へ出る。
#: ``reader`` は呼ぶ時に ``_K`` を読む関数(``m``=外へ出る・``P.n``=元に残る)を選ぶ。
def _port_src(k_reader: str) -> str:
    m_body = "    return sum(1 for c in s if c not in _K)\n" if k_reader == "m" else "    return len(s)\n"
    n_body = "        return len(_K)\n" if k_reader == "P" else "        return 3\n"
    return ('"""port — 見本(元のファイルが主な割り先)。"""\n\nfrom __future__ import annotations\n\n'
            '_K: frozenset[str] = frozenset("ab")\n\n\n'
            f"def m(s: str) -> int:\n{m_body}\n\nclass P:\n    def n(self) -> int:\n{n_body}")


_PORT_ROW = Row(num="1", old="old/port.py", package="sp", kind="split", new="sp/port.py",
                split_to=("sp/port.py", "txt/mora.py"),
                names=(("_K", "sp/port.py"), ("m", "txt/mora.py"), ("P", "sp/port.py")), names_complete=True)


def _in_place_reach(monkeypatch, k_reader: str, body: str, *, strict: bool = True):
    monkeypatch.setattr(SP, "SPLIT_ALIAS_DESTS", ())
    monkeypatch.setattr(SP, "SPLIT_PATH_DESTS", ())
    files = {"src/shibuya/__init__.py": "", "src/shibuya/sp/__init__.py": "", "src/shibuya/sp/port.py": _port_src(k_reader),
             "src/shibuya/sp/use.py": "from shibuya.sp.port import P\n",
             "tests/test_ip.py": "from shibuya.sp import port as PO\n\n\n" + body}
    try:
        return SP.make_split_plan(Tree(files=files), MV.MapDoc(rows=[_PORT_ROW]), "old/port.py", check_order=False,
                                  strict=strict)
    except SP.SplitStopped as e:
        return e.errors


_PATCH_K = 'def test_k(monkeypatch):\n    monkeypatch.setattr(PO, "_K", frozenset())\n'


def test_patch_reach_checks_the_source_module_as_the_main_destination_of_an_in_place_row(monkeypatch):
    """〔検収の後の直し 1=中-1〕主な割り先が元のファイルの行では、元のモジュールを主な割り先として確かめる: 元に残る ``_K`` を
    元のモジュールへ向けて差し替える形は、呼ぶ時に読む関数が外へ出た(``m``=``txt/mora.py``)なら止め、元に残った(``P.n``)なら通る。
    元に残る名を誰も呼ぶ時に読まない(``P``)なら、名を結ぶ元のモジュールへ向けば通る。どれも別名は手で直す一覧に無い。"""
    errs = _in_place_reach(monkeypatch, "m", _PATCH_K)
    assert isinstance(errs, list), errs
    assert any("test_k の名 _K" in e and "届かない割り先 ['txt/mora.py']" in e for e in errs), errs
    assert any("集合の外の割り先 ['sp/port.py']" in e for e in errs), errs
    plan = _in_place_reach(monkeypatch, "P", _PATCH_K)
    assert isinstance(plan, SP.SplitPlan) and plan.in_place and plan.manual == [], plan
    assert plan.patch_checked == ["tests/test_ip.py::test_k _K → ['sp/port.py'](差し替え 1)"] and plan.patch_unseen == []
    plan = _in_place_reach(monkeypatch, "m", 'def test_p(monkeypatch):\n    monkeypatch.setattr(PO, "P", object)\n')
    assert isinstance(plan, SP.SplitPlan) and plan.patch_checked == [
        "tests/test_ip.py::test_p P → ['sp/port.py'](差し替え 1)"], plan


def test_negative_without_fix_1_an_in_place_patch_that_misses_slips_through(monkeypatch):
    """〔直し 1 の負の対照〕直しを外す(元のモジュールを割り先と見ない・手で直す一覧と突き合わせない=前の形)と、届かない差し替えが
    「見られなかった」に回り、守りは「同じ」のまま計画ができる(手で直す一覧は空)。直しの在る形では止まる。"""
    assert isinstance(_in_place_reach(monkeypatch, "m", _PATCH_K, strict=False), list)
    real = SP._dest_modules
    monkeypatch.setattr(SP, "_dest_modules", lambda plan: {k: v for k, v in real(plan).items()
                                                            if k != mod_of(plan.src_rel)})
    monkeypatch.setattr(SP, "_listed_manual", lambda manual, p, s: True)
    plan = _in_place_reach(monkeypatch, "m", _PATCH_K, strict=False)
    assert isinstance(plan, SP.SplitPlan) and plan.guards["patch_reach"] == "同じ" and plan.manual == []
    assert [x for x in plan.patch_unseen if "test_k の名 _K" in x], plan.patch_unseen


def test_patch_reach_stops_a_stale_target_that_is_not_in_the_hand_fix_list(monkeypatch):
    """〔直し 1〕割り先でないモジュール(割った後に無い元のモジュール)を指したままの差し替えは、別名が手で直す一覧に在るときだけ
    「見られなかった」。在らなければ止める(書き換えの外の記号に在る文字列の的=別名を通さない)。手で直す一覧の別名は「見られ
    なかった」のまま(``test_patch_reach_lists_patches_it_cannot_see``)。"""
    body = 'def test_s(monkeypatch):\n    monkeypatch.setattr("shibuya.pk.mod.g", abs)\n'
    monkeypatch.setattr(SP, "STRING_EXCLUDE", SP.STRING_EXCLUDE | {(_REACH_FILE, "test_s")})
    errs = _reach(monkeypatch, body, head="", decl_b=False)
    assert isinstance(errs, list) and any("test_s の名 g" in e and "割り先でないモジュール ['shibuya.pk.mod']" in e
                                          and "手で直す一覧に無い" in e for e in errs), errs


def test_strict_split_refuses_a_plan_with_patches_it_cannot_see(monkeypatch):
    """〔検収の後の直し 2=低-1・親の裁定〕厳しい当て(``strict``)は、見られなかった差し替えが 1 つでも在れば断る(手で直す一覧が
    空でも)。``strict=False``(``--through`` の報告)は一覧に出すだけ。"""
    body = 'def test_f(monkeypatch, n="g"):\n    monkeypatch.setattr(f"shibuya.pk.mod.{n}", abs)\n'
    plan = _reach(monkeypatch, body, head="", decl_b=False, strict=False)
    assert isinstance(plan, SP.SplitPlan) and plan.manual == [] and plan.guards["patch_reach"] == "同じ"
    assert len(plan.patch_unseen) == 1 and "的の文字列を組み立てる" in plan.patch_unseen[0], plan.patch_unseen
    with pytest.raises(SP.SplitRefused, match="見られなかった差し替えがあるので当てない") as ei:
        _reach(monkeypatch, body, head="", decl_b=False, strict=True)
    assert "tests/test_reach.py:" in str(ei.value)


def test_excluded_files_report_nameless_paths(monkeypatch):
    """〔検収の後の直し 3=低-3〕範囲の外のファイル(E4)の名の無い割るファイルの道は、書き換えず手で直す一覧にも入れないが、報告の
    ``excluded_sites`` には在ることを出す(E8 の前は書き換えに数えて出た)。"""
    tree, md = _split_sample({"tools/bytecheck/x.py": 'P = "src/shibuya/pk/old.py"\n'})
    plan = SP.make_split_plan(tree, md, "pk/old.py", check_order=False)
    assert plan.excluded_sites == ["tools/bytecheck/x.py: 書き換え 0・手で直す 1(範囲の外=書き換えない)"], plan.excluded_sites
    assert plan.manual == [] and plan.after.files["tools/bytecheck/x.py"] == 'P = "src/shibuya/pk/old.py"\n'


# ------------------------------------------------------------------ 〔割る段 6 の S6-G0・E5-c〕素で使ってよい別名(親の裁定 T5)
#: 見本の読み手(差し替えの届く先の見本 ``_REACH_SRC`` を割る): 別名 B を、b の名 h を読む助けへ渡す(素の使い方)。
_BARE_PASS = 'def _call_h(m):\n    return m.h(1)\n\n\ndef test_pass():\n    assert _call_h(B) == 4 and B.k() == 5\n'
_BARE_WHY = "_call_h(引数 m)へ渡す。中で m から読むのは h だけ"


def _bare_decl(**kw):  # noqa: ANN202
    base = dict(old="pk/mod.py", file=_REACH_FILE, alias="B", dest="pk2/b.py", bare=True, reads=("h",), why=_BARE_WHY)
    return SP.AliasDest(**{**base, **kw})


def _bare(monkeypatch, body: str, decls, *, strict: bool = True, head: str = _HEAD_B, extra: dict | None = None):
    """見本の木で割る(宣言は ``decls``)。止まれば止めた文の一覧、通れば計画を返す。"""
    monkeypatch.setattr(SP, "SPLIT_ALIAS_DESTS", tuple(decls))
    monkeypatch.setattr(SP, "SPLIT_PATH_DESTS", ())
    files = {"src/shibuya/__init__.py": "", "src/shibuya/pk/__init__.py": "", "src/shibuya/pk/mod.py": _REACH_SRC,
             "src/shibuya/use.py": _REACH_USE, _REACH_FILE: head + body, **(extra or {})}
    md = MV.MapDoc(rows=[Row(**_REACH_ROW)])
    try:
        return SP.make_split_plan(Tree(files=files), md, "pk/mod.py", check_order=False, strict=strict)
    except SP.SplitStopped as e:
        return e.errors


def test_bare_alias_declaration_lets_a_passed_alias_through(monkeypatch):
    """〔E5-c〕印 ``bare`` の宣言の在る別名は、素で渡しても宣言の割り先へ書き換わり、手で直す一覧に出ない(``strict`` でも当たる)。
    報告の ``alias_declared`` に素の使い方の形の数と渡した先で読む名が出る。負の対照: 宣言が無いと、同じ読み手は手で直す一覧に
    出て ``strict`` は断る(印の無い別名の素の使い方は今までどおり)。"""
    plan = _bare(monkeypatch, _BARE_PASS, [_bare_decl()])
    assert isinstance(plan, SP.SplitPlan), plan
    assert plan.after.files[_REACH_FILE].startswith("from shibuya.pk2 import b as B\n"), plan.after.files[_REACH_FILE]
    assert plan.manual == [] and set(plan.guards.values()) == {"同じ"} and plan.patch_declared == []
    assert SP.report(plan)["alias_declared"] == [
        f"{_REACH_FILE}: 別名 B → pk2/b.py(読む名 1・素の使い方 渡す 1・渡した先で読む名 h)"]
    # 負の対照: 宣言が無い
    plan2 = _bare(monkeypatch, _BARE_PASS, [], strict=False)
    assert [m for m in plan2.manual if _REACH_FILE in m and "別名 B の読みの割り先が 1 つに決まらない" in m], plan2.manual
    assert plan2.after.files[_REACH_FILE].startswith("from shibuya.pk import mod as B\n")
    with pytest.raises(SP.SplitRefused, match="手で直す一覧"):
        _bare(monkeypatch, _BARE_PASS, [])
    # 負の対照: ほかの割る行の宣言は、この割る行では使わない(印の無い素の使い方と同じに手で直す一覧へ)
    plan3 = _bare(monkeypatch, _BARE_PASS, [_bare_decl(old="pk/other.py")], strict=False)
    assert isinstance(plan3, SP.SplitPlan) and plan3.alias_declared == [] and [
        m for m in plan3.manual if _REACH_FILE in m and "別名 B" in m], plan3


def test_bare_alias_declaration_accepts_each_allowed_form(monkeypatch):
    """〔E5-c〕許す素の使い方の形(``imports.BARE_OK``)は 1 つずつ数える: 渡す(位置と名の引数)・返す・しまう(変数と属性)・
    既定の引数・``is None``/``is not None`` で比べる。"""
    body = ('class Box:\n    pass\n\n\ndef _ret():\n    return B\n\n\ndef _call_kw(*, m):\n    return m.h(1)\n\n\n'
            'def test_forms(m=B):\n    kept = B\n    box = Box()\n    box.mod = B\n'
            '    assert B is not None and m is kept\n    assert _ret().h(1) == 4 and isinstance(B, object)\n'
            '    assert print(B, sep=" ") is None and _call_kw(m=B) == 4\n')
    plan = _bare(monkeypatch, body, [_bare_decl()])
    assert isinstance(plan, SP.SplitPlan), plan
    assert plan.manual == [] and plan.after.files[_REACH_FILE].startswith("from shibuya.pk2 import b as B\n")
    assert plan.alias_declared == [f"{_REACH_FILE}: 別名 B → pk2/b.py(読む名 0・素の使い方 渡す 3・返す 1・しまう 2・"
                                   f"既定の引数 1・比べる 1・渡した先で読む名 h)"], plan.alias_declared


@pytest.mark.parametrize("decl,body,word", [
    # 印の腐り: 素の使い方が 1 つも無い(属性で読むだけ=印は要らない)
    (_bare_decl(), "def test_x():\n    assert B.h(1) == 4\n", "素の使い方が 1 つも無い(印の腐り"),
    # 宣言で表せない素の使い方: 入れ物に入れる・名を字面で書かない getattr へ渡す・== で比べる・呼ぶ
    (_bare_decl(), _BARE_PASS + "\n\nMODS = [B]\n", "宣言で表せない素の使い方 ['行 12: そのほか(List)']"),
    (_bare_decl(), _BARE_PASS + '\n\ndef test_dyn(n="h"):\n    assert getattr(B, n)(1) == 4\n',
     "名を字面で書かない呼び出し getattr へ渡す"),
    (_bare_decl(), _BARE_PASS + "\n\nSAME = B == 1\n", "そのほか(Compare)"),
    (_bare_decl(), _BARE_PASS + "\n\ndef test_call():\n    B()\n", "そのほか(Call)"),
    # reads・why が無い
    (_bare_decl(reads=()), _BARE_PASS, "読む名(reads)が無い"),
    (_bare_decl(why=""), _BARE_PASS, "わけ(why="),
    # reads の名が宣言の割り先の頂上に無い(g は a)
    (_bare_decl(reads=("h", "g")), _BARE_PASS, "素で渡した先・しまった先で読む名 ['g'] が割り先の頂上で結ばれていない"),
    # 別名の属性の読みが宣言の割り先の外の名を含む(B.g は a)
    (_bare_decl(), _BARE_PASS + "\n\ndef test_g():\n    assert B.g(1) == 2\n", "別名で読む名 ['g'] が割り先の頂上で結ばれていない"),
    # 差し替える名が宣言の割り先の頂上に無い
    (_bare_decl(patches=("g",)), _BARE_PASS, "差し替える名 ['g'] が割り先の頂上で結ばれていない"),
    # 印が無いのに reads・patches を書いた(印の無い宣言の素の使い方は今までどおり止まる)
    (_bare_decl(bare=False), _BARE_PASS, "素で使ってよい印(bare)が無いのに、reads・patches を書いている"),
    (_bare_decl(bare=False, reads=(), why=""), _BARE_PASS, "名で読まない使い方がある"),
    # 使われなかった宣言(ファイルが木に無い・別名がファイルに無い)
    (_bare_decl(file="tests/no_such_reader.py"), _BARE_PASS, "宣言が使われなかった"),
    (_bare_decl(alias="B_NOPE"), _BARE_PASS, "宣言が使われなかった"),
])
def test_negative_bare_alias_declaration_guards_each_stop(monkeypatch, decl, body, word):
    """〔E5-c の守り〕印のある宣言の守りは 1 つずつ止める(書かない実行でも): 印の腐り・宣言で表せない素の使い方・reads か why が
    無い・reads の名が割り先に無い・別名の属性の読みが割り先の外・差し替える名が割り先に無い・印の無い宣言の reads・使われなかった
    宣言。"""
    for strict in (True, False):
        errs = _bare(monkeypatch, body, [decl], strict=strict)
        assert isinstance(errs, list) and errs and all(e.startswith("別名の割り先の宣言の守り: ") for e in errs), errs
        assert any(word in e for e in errs), (word, errs)
        assert all(decl.file in e for e in errs), errs


#: 素で使った先で差し替える読み手: 別名 B をしまい、しまった先を通して h を元に戻す(道具には見えない差し替え)。
_BARE_STORE = ('class Rec:\n    def attach(self):\n        self._m = B\n        self._orig = B.h\n        B.h = abs\n\n'
               '    def detach(self):\n        self._m.h = self._orig\n')


def test_bare_alias_patches_are_checked_against_the_declared_destination(monkeypatch):
    """〔E5-c〕宣言の差し替える名(``patches``)は、E5-b の届かせる割り先の集合が宣言の割り先だけなら通り、報告の ``patch_declared``
    に出る(確かめた ``patch_checked``・見られなかった ``patch_unseen`` とは分ける)。字面で見える差し替え(``B.h = abs``)も数える。
    字面に差し替えの無い名(素で使った先だけ)も確かめる。負の対照: 宣言が無いと、字面の差し替えは「見られなかった」に回り、
    ``strict`` は断る。"""
    plan = _bare(monkeypatch, _BARE_STORE, [_bare_decl(patches=("h",))])
    assert isinstance(plan, SP.SplitPlan), plan
    assert plan.patch_declared == [f"{_REACH_FILE}: 別名 B の名 h → ['pk2/b.py'](字面で見えた差し替え 1・素で使った先は宣言)"]
    assert plan.patch_checked == [] and plan.patch_unseen == [] and plan.guards["patch_reach"] == "同じ"
    assert SP.report(plan)["patch_declared"] == plan.patch_declared
    assert "素の使い方 しまう 1" in plan.alias_declared[0] and "差し替える名 h" in plan.alias_declared[0], plan.alias_declared
    plan = _bare(monkeypatch, _BARE_PASS, [_bare_decl(reads=("h", "k"), patches=("k",))])
    assert isinstance(plan, SP.SplitPlan) and plan.patch_declared == [
        f"{_REACH_FILE}: 別名 B の名 k → ['pk2/b.py'](字面で見えた差し替え 0・素で使った先は宣言)"], plan
    # 負の対照: 宣言が無い
    plan2 = _bare(monkeypatch, _BARE_STORE, [], strict=False)
    assert isinstance(plan2, SP.SplitPlan) and plan2.patch_declared == []
    assert any("Rec.attach の名 h" in x and "手で直す一覧の別名" in x for x in plan2.patch_unseen), plan2.patch_unseen
    with pytest.raises(SP.SplitRefused):
        _bare(monkeypatch, _BARE_STORE, [])


@pytest.mark.parametrize("decl,body,words", [
    # helper を呼ぶ時に読む関数は a(g)と b(h)=素で使った先の差し替えは b にしか向かない=a に届かない
    (_bare_decl(reads=("h", "helper"), patches=("helper",)), _BARE_PASS,
     ["差し替える名 helper", "届かない割り先 ['pk2/a.py']"]),
    # N を呼ぶ時に読むのは src の use.py(別名の属性・名を定義する a)=宣言の割り先 b は集合の外(空振り)
    (_bare_decl(reads=("h", "N"), patches=("N",)), _BARE_PASS,
     ["差し替える名 N", "宣言の割り先が届かせる割り先の集合 ['pk2/a.py'] に無い(空振り"]),
    # 字面で見える差し替えの名が、宣言の差し替える名に無い
    (_bare_decl(), _BARE_STORE, ["Rec.attach の名 h", "宣言の差し替える名(patches)に無い"]),
])
def test_negative_bare_alias_patches_that_miss_stop(monkeypatch, decl, body, words):
    """〔E5-c の守り〕差し替える名の届かせる割り先の集合に、宣言の割り先が無い(空振り)・ほかの割り先も在る(届かない)・字面で見える
    差し替えの名が宣言に無い、は止める(差し替えの届く先の守り)。"""
    errs = _bare(monkeypatch, body, [decl], strict=False)
    assert isinstance(errs, list) and errs and all(e.startswith("差し替えの届く先の守り: ") for e in errs), errs
    for w in words:
        assert any(w in e for e in errs), (w, errs)


def test_negative_without_the_declared_patch_check_a_missing_patch_slips_through(monkeypatch):
    """〔E5-c の負の対照〕宣言の差し替える名の確かめは ``patch_reach`` が止めている(外すと、a に届かない helper の宣言が通る)。"""
    decl = _bare_decl(reads=("h", "helper"), patches=("helper",))
    assert isinstance(_bare(monkeypatch, _BARE_PASS, [decl]), list)
    monkeypatch.setattr(SP, "patch_reach", lambda plan: [])
    plan = _bare(monkeypatch, _BARE_PASS, [decl])
    assert isinstance(plan, SP.SplitPlan) and plan.guards["patch_reach"] == "同じ" and plan.manual == []


def test_bare_alias_declaration_works_the_same_in_a_src_file(monkeypatch):
    """〔E5-c〕src のファイルの別名にも同じに効く(S6-G1 で載せる ``runtime/systems/judge.py`` の形=別名を関数へ渡す)。負の対照:
    宣言が無いと手で直す一覧へ。"""
    user = "src/shibuya/user2.py"
    text = ('"""user2 — 見本(別名を渡す src の読み手)。"""\n\nfrom __future__ import annotations\n\n'
            'from shibuya.pk import mod as B\n\n\ndef _call_h(m):\n    return m.h(1)\n\n\ndef run() -> int:\n'
            '    return _call_h(B)\n')
    plan = _bare(monkeypatch, "", [_bare_decl(file=user)], head="", extra={user: text})
    assert isinstance(plan, SP.SplitPlan), plan
    assert "\nfrom shibuya.pk2 import b as B\n" in plan.after.files[user] and plan.manual == []
    assert plan.alias_declared == [f"{user}: 別名 B → pk2/b.py(読む名 0・素の使い方 渡す 1・渡した先で読む名 h)"]
    plan2 = _bare(monkeypatch, "", [], head="", extra={user: text}, strict=False)
    assert [m for m in plan2.manual if m.startswith(f"{user}:") and "別名 B" in m], plan2.manual


#: 〔E5-c・宣言が腐らない・親の裁定(検収の低-1)〕印(``bare``)のある宣言の受け手: (ファイル, 別名) → (受け手のファイル, 受け手=
#: 頂上の関数かクラス, 受け手の中でそのモジュールを持つ字面)。道具は、しまう・既定の引数で写した先の読みと差し替えを辿らない。
#: 印のある宣言を足すときは、ここに受け手を足す(``tools/pkgmove/README.md`` の E5-c の決まり)。足さなければ下の試験が落ちる。
#: 〔割る段 6 の M0・検収の低-2(意味の側)〕4 つ目の欄=外の差し替え: 受け手の外で、宣言の割り先のモジュールの名を差し替え、ランの
#: 中でこの別名を通って受け手の読みに届く所(ファイル, 記号, 名)。宣言の ``patches`` は、受け手の中で書く名と外の差し替えの名を
#: 合わせたもの。受け手の読む名を外で差し替える所が、同じ受け手のどの行にも無ければ落ちる。
_SETTLE = ("src/shibuya/runtime/run.py", "_settle_pending_invites", ("R",))
#: ランの中で ``judge.py`` の別名 ``R_TALK`` を通って ``_settle_pending_invites`` に読まれる差し替え(試験のランの包み)。
_RUN_PATCHES = (("tests/engine/proximity/test_runs.py", "_recorded_run", "set_conversing"),)
_BARE_RECEIVERS: dict[tuple[str, str], tuple[str, str, tuple[str, ...], tuple[tuple[str, str, str], ...]]] = {
    ("tests/engine/test_conversation_invite.py", "R_TALK"): (*_SETTLE, ()),
    ("tests/engine/test_defect_fixes_1103.py", "R_TALK"): (*_SETTLE, ()),
    ("src/shibuya/runtime/systems/judge.py", "R_TALK"): (*_SETTLE, _RUN_PATCHES),
    ("tools/c7/attr_arms.py", "module"): ("tools/c7/attr_arms.py", "AgentCellRecorder", ("module", "self._module"), ()),
    ("tools/c7/occupancy_series.py", "module"): ("tools/c7/occupancy_series.py", "OccupancyRecorder",
                                                 ("module", "self._module"), ()),
}


@lru_cache(maxsize=None)
def _outside_patch_sites(dest_mod: str, names: frozenset[str]) -> frozenset[tuple[str, str, str]]:
    """木の読み手(src・tools・``tests`` の c7 を除く全部)で、モジュール ``dest_mod`` の名 ``names`` を差し替える所(ファイル,
    記号, 名)。拾う形は割る道具の E5-b と同じ(``split._collect_patches``)。"""
    leaf = dest_mod.rpartition(".")[2]
    bases = [ROOT / "src" / "shibuya", ROOT / "tools", *[p for p in (ROOT / "tests").iterdir() if p.name != "c7"]]
    out: set[tuple[str, str, str]] = set()
    for base in bases:
        for f in ([base] if base.is_file() else sorted(base.rglob("*.py"))):
            if f.suffix != ".py" or "__pycache__" in f.parts:
                continue
            text = f.read_text(encoding="utf-8")
            if leaf not in text or not any(n in text for n in names):
                continue
            rel = f.relative_to(ROOT).as_posix()
            sites, _unseen = SP._collect_patches(text, rel, {dest_mod})
            out |= {(s.file, s.group, s.name) for s in sites if s.name in names}
    return frozenset(out)


def _receiver_names(text: str, owner: str, holders: set[str]) -> tuple[set[str], set[str]]:
    """頂上の関数かクラス ``owner`` の中で、``holders`` の字面(引数・別名・``self._module``)の属性として読み書きする名と、そのうち
    書く(代入・``del``・``setattr``/``delattr`` の字面の名)名。"""
    reads: set[str] = set()
    writes: set[str] = set()
    for n in ast.parse(text).body:
        if not (isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == owner):
            continue
        for x in ast.walk(n):
            if isinstance(x, ast.Attribute) and ast.unparse(x.value) in holders:
                reads.add(x.attr)
                if isinstance(x.ctx, (ast.Store, ast.Del)):
                    writes.add(x.attr)
            if (isinstance(x, ast.Call) and len(x.args) >= 2 and ast.unparse(x.args[0]) in holders
                    and isinstance(x.args[1], ast.Constant) and isinstance(x.args[1].value, str)):
                fn = x.func.attr if isinstance(x.func, ast.Attribute) else getattr(x.func, "id", "")
                if fn in ("setattr", "getattr", "hasattr", "delattr"):
                    reads.add(x.args[1].value)
                    if fn in ("setattr", "delattr"):
                        writes.add(x.args[1].value)
    return reads, writes


def _bare_uses_outside(text: str, alias: str, owner: str) -> list[int]:
    """宣言のファイルで、別名を属性で読まない使い方のうち、受け手の外のもの(受け手の関数を呼ぶ引数でもなく、受け手のクラスの
    中でもない)の行。"""
    tree = ast.parse(text)
    parents = {id(c): p for p in ast.walk(tree) for c in ast.iter_child_nodes(p)}
    inside = {id(x) for n in tree.body if isinstance(n, ast.ClassDef) and n.name == owner for x in ast.walk(n)}
    out: list[int] = []
    for x in ast.walk(tree):
        if not (isinstance(x, ast.Name) and x.id == alias and isinstance(x.ctx, ast.Load)) or id(x) in inside:
            continue
        up = parents.get(id(x))
        if isinstance(up, ast.Attribute) and up.value is x:
            continue  # 属性で読む=道具が見る
        call = parents.get(id(up)) if isinstance(up, ast.keyword) else up
        if isinstance(call, ast.Call) and owner in (getattr(call.func, "id", None), getattr(call.func, "attr", None)):
            continue
        out.append(x.lineno)
    return out


def _bare_receiver_problems(decls, receivers) -> list[str]:  # noqa: ANN001
    """印のある宣言と受け手の表の食い違い: 受け手の無い宣言・宣言の無い受け手・``reads`` が受け手の字面から引いた名と違う・
    ``patches`` が受け手の中で書く名と外の差し替えの名を合わせたものと違う・外の差し替えが木に無い・``why`` に受け手の名が無い・
    受け手の外の素の使い方・受け手の読む名を外で差し替える所が、同じ受け手のどの行にも無い。"""
    bare = {(d.file, d.alias): d for d in decls if d.bare}
    out = [f"{f}: 別名 {a}: 受け手が無い(_BARE_RECEIVERS に足す)" for f, a in sorted(set(bare) - set(receivers))]
    out += [f"{f}: 別名 {a}: 印のある宣言の無い受け手" for f, a in sorted(set(receivers) - set(bare))]
    listed: dict[tuple[str, str, str], set[tuple[str, str, str]]] = {}  # (受け手のファイル, 受け手, 割り先) → 外の差し替え
    reads_of: dict[tuple[str, str, str], set[str]] = {}
    for key in sorted(set(bare) & set(receivers)):
        d = bare[key]
        rf, owner, holders, outside_patches = receivers[key]
        reads, writes = _receiver_names((ROOT / rf).read_text(encoding="utf-8"), owner, set(holders))
        dest_mod = mod_of(d.dest)
        here = f"{d.file}: 別名 {d.alias}(受け手 {rf}::{owner})"
        if not reads:
            out.append(f"{here}: 受け手が無いか、モジュールの名を読まない")
        if set(d.reads) != reads:
            out.append(f"{here}: reads {sorted(d.reads)} が受け手の読み書きする名 {sorted(reads)} と違う")
        want = writes | {n for _f, _g, n in outside_patches}
        if set(d.patches) != want:
            out.append(f"{here}: patches {sorted(d.patches)} が受け手の書く名と外の差し替えの名 {sorted(want)} と違う")
        there = _outside_patch_sites(dest_mod, frozenset(reads)) if reads else frozenset()
        out += [f"{here}: 外の差し替え {s} が木に無い" for s in outside_patches if s not in there]
        if owner not in d.why:
            out.append(f"{here}: why に受け手の名が無い")
        outside = _bare_uses_outside((ROOT / d.file).read_text(encoding="utf-8"), d.alias, owner)
        if outside:
            out.append(f"{here}: 受け手の外の素の使い方(行 {outside})")
        g = (rf, owner, dest_mod)
        listed.setdefault(g, set()).update(outside_patches)
        reads_of.setdefault(g, set()).update(reads)
    for (rf, owner, dest_mod), names in sorted(reads_of.items()):
        sites = _outside_patch_sites(dest_mod, frozenset(names)) if names else frozenset()
        # 受け手の中の書き(同じ割り先の受け手どれかの中=その行の patches が持つ)は外の差し替えに数えない
        owners = {(f2, o2) for (f2, o2, m2) in reads_of if m2 == dest_mod}
        inside = {s for s in sites if any(s[0] == f2 and (s[1] == o2 or s[1].startswith(o2 + ".")) for f2, o2 in owners)}
        for s in sorted(sites - inside - listed[(rf, owner, dest_mod)]):
            out.append(f"受け手 {rf}::{owner}({dest_mod}): 読む名を外で差し替える {s} が、どの受け手の行の外の差し替えにも無い")
    return out


def test_bare_alias_declarations_name_what_the_receiving_functions_read():
    """〔E5-c・宣言が腐らない〕本物の印のある宣言 5 つ: 印のある宣言の集合と受け手の表 ``_BARE_RECEIVERS`` が同じで、``reads``・
    ``patches`` が受け手の字面から引いた名と同じ(``_settle_pending_invites`` が引数 ``R`` から読む 4 名・``tools/c7`` の 2 本の
    クラスが ``module``・``self._module`` から読み書きする ``apply``)。素の使い方は受け手へ渡すか受け手の中だけ。受け手を書き換えて
    読む名が増えた・印のある宣言を足して受け手を足さなかった、のどちらでも落ちる。"""
    assert _bare_receiver_problems(SP.SPLIT_ALIAS_DESTS, _BARE_RECEIVERS) == []
    bare = [d for d in SP.SPLIT_ALIAS_DESTS if d.bare]
    assert len(bare) == len(_BARE_RECEIVERS) == 5 and all(d.reads and d.why and d.old == "engine/resolve.py" for d in bare)
    rf, owner, holders = _SETTLE
    settle = _receiver_names((ROOT / rf).read_text(encoding="utf-8"), owner, set(holders))
    assert settle == ({"talk_within_reach", "set_conversing", "end_conversation", "revert_conversation"}, set()), settle
    # 〔M0・検収の低-2〕外の差し替え: 試験のランの包みが talk の set_conversing を差し替える(judge の別名を通って読まれる)
    assert _outside_patch_sites("shibuya.act.ops.talk", frozenset(settle[0])) == frozenset(_RUN_PATCHES)
    judge = next(d for d in bare if d.file == "src/shibuya/runtime/systems/judge.py")
    assert judge.patches == ("set_conversing",) and "test_runs.py" in judge.why


def test_negative_a_bare_declaration_without_its_receiver_fails_the_rot_check():
    """〔E5-c の決まりの負の対照〕メモリの中で印のある宣言を 1 行足し、受け手を足さないと食い違いが出る(試験が落ちる)。受け手の
    無い表の行・``reads`` の欠け・受け手の外の素の使い方も出る。"""
    real = next(d for d in SP.SPLIT_ALIAS_DESTS if d.bare and d.file == "src/shibuya/runtime/systems/judge.py")
    extra = dataclasses.replace(real, file="tests/engine/test_no_such_bare.py")
    assert _bare_receiver_problems((*SP.SPLIT_ALIAS_DESTS, extra), _BARE_RECEIVERS) == [
        "tests/engine/test_no_such_bare.py: 別名 R_TALK: 受け手が無い(_BARE_RECEIVERS に足す)"]
    others = tuple(d for d in SP.SPLIT_ALIAS_DESTS if d is not real)
    got = _bare_receiver_problems(others, _BARE_RECEIVERS)  # judge の行(外の差し替えを持つ行)も数えない
    assert got[0] == "src/shibuya/runtime/systems/judge.py: 別名 R_TALK: 印のある宣言の無い受け手" and len(got) == 2, got
    assert "'set_conversing') が、どの受け手の行の外の差し替えにも無い" in got[1], got
    short = dataclasses.replace(real, reads=real.reads[:3])
    got = _bare_receiver_problems((*others, short), _BARE_RECEIVERS)
    assert len(got) == 1 and "reads" in got[0] and "と違う" in got[0], got
    wrong = {**_BARE_RECEIVERS, ("src/shibuya/runtime/systems/judge.py", "R_TALK"): (_SETTLE[0], "_inviter_of", ("R",), ())}
    got = _bare_receiver_problems(SP.SPLIT_ALIAS_DESTS, wrong)
    assert any("受け手の外の素の使い方(行 [163])" in x for x in got) and any("受け手が無いか" in x for x in got), got
    # 〔M0・検収の低-2〕外の差し替えを表から外すと、宣言の patches と食い違い、差し替える所がどの行にも無いと出る
    no_run = {**_BARE_RECEIVERS, ("src/shibuya/runtime/systems/judge.py", "R_TALK"): (*_SETTLE, ())}
    got = _bare_receiver_problems(SP.SPLIT_ALIAS_DESTS, no_run)
    assert any("judge.py" in x and "patches ['set_conversing']" in x for x in got), got
    assert any("('tests/engine/proximity/test_runs.py', '_recorded_run', 'set_conversing')" in x and "どの受け手の行" in x
               for x in got), got
    # 宣言の patches を外しても食い違う(外の差し替えは表に在る)
    no_patch = tuple(dataclasses.replace(d, patches=()) if d is real else d for d in SP.SPLIT_ALIAS_DESTS)
    got = _bare_receiver_problems(no_patch, _BARE_RECEIVERS)
    assert len(got) == 1 and "patches []" in got[0], got
    # 木に無い外の差し替えを書くと出る
    ghost = {**_BARE_RECEIVERS, ("src/shibuya/runtime/systems/judge.py", "R_TALK"): (
        *_SETTLE, (*_RUN_PATCHES, ("tests/engine/proximity/test_runs.py", "_recorded_run", "end_conversation")))}
    got = _bare_receiver_problems(SP.SPLIT_ALIAS_DESTS, ghost)
    assert any("'end_conversation') が木に無い" in x for x in got), got


# ------------------------------------------------------------------ 〔割る段 6 の S6-G0・E9〕CLI の書かない道を見本の木で確かめる
def test_split_order_of_reads_the_split_rows_of_a_map():
    """〔E9〕``table.split_order_of``: 割る行の ``split_order``(1 から)で並べた順。番号が続かない・頭の ``split_order`` と食い違えば断る。
    本物の表では ``table.SPLIT_ORDER`` と同じ。"""
    from pkgmove.table import SPLIT_ORDER, split_order_of

    assert split_order_of(MAPDOC) == SPLIT_ORDER
    one, two = Row(**{**_SAMPLE_ROW, "split_order": 1}), Row(**{**_TWO_ROW, "split_order": 2})
    assert split_order_of(MV.MapDoc(rows=[two, one])) == ("pk/old.py", "pk/two.py")
    with pytest.raises(ValueError, match="1 から続かない"):
        split_order_of(MV.MapDoc(rows=[one, dataclasses.replace(two, split_order=3)]))
    with pytest.raises(ValueError, match="1 から続かない"):
        split_order_of(MV.MapDoc(rows=[one, dataclasses.replace(two, split_order=1)]))
    with pytest.raises(ValueError, match="食い違う"):
        split_order_of(MV.MapDoc(rows=[one, two], meta={"split_order": ["pk/two.py", "pk/old.py"]}))


#: 見本の決まり: 段 s1 だけ(古い決まりの段=新しい決まりは作らない)。古い決まり 1 つが見本の木の全部の包みを元の側に持つ(割り先の
#: 新しいモジュールも「どの決まりも見なくなった」にならない)。
_CT_SAMPLE = ('root_package = "shibuya"\nold_only_through = "s1"\nstage_order = ["s1"]\nlayers = []\nrule = []\nignore = []\n\n'
              '[[old]]\nname = "見本の決まり"\ntype = "forbidden"\n'
              'source = ["pk", "nw", "vocab", "foundation", "validation", "engine", "rngtab"]\nforbidden = ["nothing"]\n')
_LP_CLI = "src/shibuya/foundation/decl/ledger_paths.py"


def _cli_sample_tree(root: Path, monkeypatch, split_rows: list[Row]) -> tuple[Path, Path]:
    """CLI の見本の木を ``root`` に書き、見本の表(``map.toml`` の形)と決まり(``contracts.toml`` の形)の道を返す。

    木: 見本の割るファイル(``pk/old.py``・``pk/two.py``)と読み手・既に在る割り先・台帳の道の表(1 対 1 の表と前向きの表)・
    つなぎの宣言の走査(本物の ``bridging_scan.py`` と ``foundation/paths.py`` の写し=CLI は木の src から読む)・乱数の領域の表 3 つ・
    固定の表・凍結の JSON(見本の木から作る)。表: 割る行 2 本(順 1・2)と、段 s1 で移し済みの行 1 本(台帳の道の表の置き場)。"""
    from pkgmove import table as TBL

    src = {
        "src/shibuya/__init__.py": "", "src/shibuya/pk/__init__.py": "", "src/shibuya/pk/old.py": _OLD_SAMPLE,
        "src/shibuya/pk/two.py": _TWO_SAMPLE,
        "src/shibuya/pk/reader.py": "from shibuya.pk.old import A, f\nfrom shibuya.pk import old as OLD\n\nX = A + f(1) + OLD.A\n",
        "src/shibuya/vocab/__init__.py": "", "src/shibuya/vocab/base.py": _BASE_SAMPLE,
        "src/shibuya/rngtab.py": "POPULATION_RNG_DOMAINS = {}\nENVIRONMENT_RNG_DOMAINS = {}\nMOTION_RNG_DOMAINS = {}\n",
        "src/shibuya/foundation/__init__.py": "", "src/shibuya/foundation/decl/__init__.py": "",
        _LP_CLI: (_lp_text({_LP_CLI: "src/shibuya/engine/bridging/ledger_paths.py"}, {})
                  + "\n\ndef ledger_path(path: str) -> str:\n    return LEDGER_PATHS.get(path, path)\n"),
        "src/shibuya/foundation/paths.py": (ROOT / "src/shibuya/foundation/paths.py").read_text(encoding="utf-8"),
        "src/shibuya/validation/__init__.py": "", "src/shibuya/validation/static/__init__.py": "",
        "src/shibuya/validation/static/bridging_scan.py":
            (ROOT / "src/shibuya/validation/static/bridging_scan.py").read_text(encoding="utf-8"),
        "src/shibuya/engine/__init__.py": "",
    }
    classes = {f"{mod_of(p[len(SRC_PREFIX):])}.{q}": q for p, t in src.items() if p.endswith(".py")
               for q, _n in G._class_defs(ast.parse(t))}
    src["src/shibuya/engine/class_ids.py"] = "CLASS_IDS = {\n" + "".join(f'    "{k}": "{k}",\n' for k in sorted(classes)) + "}\n"
    stub = G.Frozen(names={"rng_domains_path_shaped": {}, "other_path_shaped": {}}, class_qual={})
    names = {**G.collect_names(Tree(files=src), stub), "run_path_shaped": {}}
    files = {**src, "tests/test_x.py": "from shibuya.pk.old import C\n",
             "tests/engine/state/names_frozen.json": json.dumps(names, ensure_ascii=False),
             "tests/engine/state/class_ids_frozen.json": json.dumps({"names": {k: q for k, q in classes.items()}})}
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8", newline="")
    rows = [*split_rows, Row(num="L", old="engine/bridging/ledger_paths.py", package="foundation", kind="move",
                             new="foundation/decl/ledger_paths.py", stage="s1")]
    for k, v in (("SPLIT_ORDER", tuple(r.old for r in sorted(split_rows, key=lambda r: r.split_order))),
                 ("SPLIT_DEFERRED", {}), ("SPLIT_FORWARDERS", {}), ("SPLIT_ENTRIES", {})):
        monkeypatch.setattr(TBL, k, v)
    mp, ct = root.parent / f"{root.name}_map.toml", root.parent / f"{root.name}_contracts.toml"
    mp.write_text(TBL.render_map(rows, "見本"), encoding="utf-8", newline="")
    ct.write_text(_CT_SAMPLE, encoding="utf-8", newline="")
    monkeypatch.undo()
    return mp, ct


def _no_pycache(root: Path) -> bool:
    return not [p for p in root.rglob("__pycache__")]


def test_split_cli_dry_run_writes_nothing_in_a_sample_tree(tmp_path, monkeypatch):
    """〔E9・追記=検収 低-2〕``cli.py split --through all`` を見本の木と見本の表・決まり(``--map``・``--contracts``)で回す: 終了 0・
    見本の木のファイルが 1 本も変わらない(全部のバイトの指紋・``__pycache__`` も作らない)・要約の JSON に行ごとの守りが載る・
    標準出力に「書いていない」。順は表の割る行の ``split_order`` から読む(割る行が残り 0 の本物の木に頼らない)。"""
    root = tmp_path / "sample"
    rows = [Row(**{**_SAMPLE_ROW, "split_order": 1}), Row(**{**_TWO_ROW, "split_order": 2})]
    mp, ct = _cli_sample_tree(root, monkeypatch, rows)
    before = digest(root)
    od = tmp_path / "out"
    r = run_cli("split", "--through", "all", "--tree", str(root), "--map", str(mp), "--contracts", str(ct),
                "--out-dir", str(od))
    assert r.returncode == 0, (r.stdout[-3000:], r.stderr[-3000:])
    assert "書いていない" in r.stdout
    assert digest(root) == before and _no_pycache(root)
    rows_out = json.loads((od / "split_through_summary.json").read_text(encoding="utf-8"))
    assert [x["row"] for x in rows_out] == ["pk/old.py", "pk/two.py"]
    for x in rows_out:
        assert {"stmts", "declarations", "names_frozen", "class_ids", "outside_allowlist", "patch_reach",
                "contracts"} <= set(x["guards"]), x["guards"]
        assert all(v == "同じ" or v.startswith("宣言どおり") for v in x["guards"].values()), x["guards"]
    assert sorted(p.name for p in od.iterdir()) == ["split_01.diff", "split_01_report.json", "split_02.diff",
                                                    "split_02_report.json", "split_through_summary.json"]
    # 名指しの書かない実行(次の 1 本)も同じ口で回り、何も書かない
    r = run_cli("split", "--next", "--tree", str(root), "--map", str(mp), "--contracts", str(ct))
    assert r.returncode == 0 and "書いていない" in r.stdout and '"row": "pk/old.py"' in r.stdout, r.stderr[-3000:]
    assert digest(root) == before and _no_pycache(root)


def test_negative_split_cli_dry_run_returns_nonzero_when_a_guard_stops_in_a_sample_tree(tmp_path, monkeypatch):
    """〔E9〕守りが止める見本では終了コードが 0 でない(どちらも木は 1 本も変わらない): 順の違う行の名指し(断る)と、割り先どうしが
    互いの名を読む行(``--through`` の要約に止めた理由)。表の割る順が 1 から続かない表は読む前に断る。"""
    root = tmp_path / "order"
    rows = [Row(**{**_SAMPLE_ROW, "split_order": 1}), Row(**{**_TWO_ROW, "split_order": 2})]
    mp, ct = _cli_sample_tree(root, monkeypatch, rows)
    before = digest(root)
    r = run_cli("split", "--only", "pk/two.py", "--tree", str(root), "--map", str(mp), "--contracts", str(ct))
    assert r.returncode == 2 and "順が違う" in r.stderr, (r.stdout[-2000:], r.stderr[-2000:])
    assert digest(root) == before
    # 割り先どうしが互いの名を読む(f → vocab/base.py は A を、C → nw/main.py は B を読む)
    root2 = tmp_path / "mutual"
    mutual = Row(**{**_SAMPLE_ROW, "split_order": 1, "names": (("A", "nw/main.py"), ("B", "vocab/base.py"),
                                                                ("f", "vocab/base.py"), ("C", "nw/main.py"))})
    mp2, ct2 = _cli_sample_tree(root2, monkeypatch, [mutual])
    before2 = digest(root2)
    od = tmp_path / "out2"
    r = run_cli("split", "--through", "all", "--tree", str(root2), "--map", str(mp2), "--contracts", str(ct2),
                "--out-dir", str(od))
    assert r.returncode == 2 and "互いの名を読む" in r.stderr, (r.stdout[-2000:], r.stderr[-2000:])
    assert "書いていない" in r.stdout
    summary = json.loads((od / "split_through_summary.json").read_text(encoding="utf-8"))
    assert [x["row"] for x in summary] == ["pk/old.py"] and "互いの名を読む" in summary[0]["stopped"][0]
    assert digest(root2) == before2 and _no_pycache(root2)
    # 割る順が 1 から続かない表は断る
    bad = mp.read_text(encoding="utf-8").replace("split_order = 2\n", "split_order = 3\n")
    mp3 = tmp_path / "bad_map.toml"
    mp3.write_text(bad, encoding="utf-8", newline="")
    r = run_cli("split", "--through", "all", "--tree", str(root), "--map", str(mp3), "--contracts", str(ct))
    assert r.returncode == 2 and "対応表を読めない" in r.stderr, r.stderr[-2000:]
    assert digest(root) == before


# ------------------------------------------------------------------ 〔割る段 6 の S6-G0・E5-b〕本物の履歴での確かめ(5b の G3 の土台)
#: 5b の G3 の土台(E5-a の commit・22 本目 ``cli.py`` を当てる前の木)。
_G3_BASE = "e6d221c"


def _git_tree(rev: str) -> tuple[Tree, dict[str, str]] | None:
    """``rev`` の木をメモリに読む(``Tree.load`` と同じ範囲=src/shibuya の全部・tests と tools の .py・docs の記録の道具)。凍結の
    JSON とつなぎの台帳は 2 つ目の戻り値。``tests/c7`` は中身を読まない(名前の一覧から外す)。git か commit が無ければ ``None``。"""
    git = shutil.which("git")
    if git is None or not (ROOT / ".git").exists():
        return None
    if subprocess.run([git, "-C", str(ROOT), "cat-file", "-e", f"{rev}^{{commit}}"], capture_output=True).returncode != 0:
        return None
    ls = subprocess.run([git, "-C", str(ROOT), "ls-tree", "-r", "-z", rev, "--", "src/shibuya", "tests", "tools",
                         *AL.RECORD_TOOLS, *FROZEN_FILES], capture_output=True, check=True).stdout
    entries: list[tuple[str, str]] = []
    for rec in ls.split(b"\0"):
        if not rec:
            continue
        meta, path = rec.split(b"\t", 1)
        _mode, typ, sha = meta.split(b" ")
        p = path.decode("utf-8")
        if typ != b"blob" or p.startswith("tests/c7/") or "__pycache__" in p.split("/"):
            continue
        if p in FROZEN_FILES or p.startswith("src/shibuya/") or p.endswith(".py"):
            entries.append((p, sha.decode()))
    out = subprocess.run([git, "-C", str(ROOT), "cat-file", "--batch"], input="".join(f"{s}\n" for _p, s in entries).encode(),
                         capture_output=True, check=True).stdout
    pos = 0
    files: dict[str, str] = {}
    blobs: dict[str, bytes] = {}
    side: dict[str, str] = {}
    for p, _sha in entries:
        nl = out.index(b"\n", pos)
        size = int(out[pos:nl].split(b" ")[2])
        data = out[nl + 1: nl + 1 + size]
        pos = nl + 1 + size + 1
        if p in FROZEN_FILES:
            side[p] = data.decode("utf-8")
        elif p.endswith(".py"):
            files[p] = data.decode("utf-8")
        else:
            blobs[p] = data
    return Tree(files=files, blobs=blobs), side


def _site_count(checked: list[str]) -> dict[str, int]:
    out: Counter = Counter()
    for x in checked:
        name = x.split("::", 1)[1].split(" ")[1]
        out[name] += int(x.rsplit("(差し替え ", 1)[1].rstrip(")"))
    return dict(out)


@pytest.mark.slow
def test_patch_reach_replays_the_22nd_split_on_the_g3_base_in_history(monkeypatch):
    """〔E5-b・本物の履歴〕5b の G3 の土台(``e6d221c``)をメモリに読み、22 本目(``cli.py``)を当て直す: (i) そのままなら守りは
    通り、差し替え 25 か所(``run`` 19・``build_ledger_bundle`` 1・台帳の型 5 行)を確かめる (ii) 助け
    ``tests/economy/_stage2_outside.py`` の main の側の 2 行を外すと止まる(台帳の型が main に届かない) (iii) 別名の割り先の宣言
    (E5-a)を外すと、宣言の在った別名は手で直す一覧に入り(``strict`` は断る)、その差し替えは「見られなかった」に出る(黙って
    通さない)。git が無いか commit が無い所(浅い写し)では飛ばす。"""
    from pkgmove import contracts as CT

    got = _git_tree(_G3_BASE)
    if got is None:
        pytest.skip(f"git か commit {_G3_BASE} が無い(git の外か浅い写し)")
    tree, side = got
    frozen = G.Frozen(names=json.loads(side["tests/engine/state/names_frozen.json"]),
                      class_qual=json.loads(side["tests/engine/state/class_ids_frozen.json"])["names"])
    ledger = side["docs/design/bridging-ledger.json"]
    spec = CT.load_spec(ROOT / CT.CONTRACTS_REL)
    assert SP.next_split(tree, MAPDOC) == "cli.py"
    plan = SP.make_split_plan(tree, MAPDOC, "cli.py", frozen=frozen, ledger_text=ledger, strict=True, contracts_spec=spec)
    assert plan.guards["patch_reach"] == "同じ" and all(v == "同じ" or v.startswith("宣言どおり")
                                                        for v in plan.guards.values()), plan.guards
    assert _site_count(plan.patch_checked) == {"run": 19, "build_ledger_bundle": 1, "Ledger": 2,
                                               "_HouseholdWalletLedger": 2, "GoodsLedger": 1}, plan.patch_checked
    helper = [x for x in plan.patch_checked if x.startswith("tests/economy/_stage2_outside.py::use_outside_bundle ")]
    assert sorted(helper) == [
        "tests/economy/_stage2_outside.py::use_outside_bundle GoodsLedger → ['interfaces/cli/wire_economy.py'](差し替え 1)",
        "tests/economy/_stage2_outside.py::use_outside_bundle Ledger → ['interfaces/cli/main.py', "
        "'interfaces/cli/wire_economy.py'](差し替え 2)",
        "tests/economy/_stage2_outside.py::use_outside_bundle _HouseholdWalletLedger → ['interfaces/cli/main.py', "
        "'interfaces/cli/wire_economy.py'](差し替え 2)"], helper
    assert any("build_ledger_bundle → ['interfaces/cli/main.py']" in x for x in plan.patch_checked)
    # (ii) 助けの main の側の 2 行を外す=台帳の型の差し替えが main(main() の isinstance)に届かない
    helper_p = "tests/economy/_stage2_outside.py"
    text = tree.files[helper_p]
    cut = text
    for line in ('    mp.setattr(cli, "Ledger", ledger)\n', '    mp.setattr(cli, "_HouseholdWalletLedger", wallet)\n'):
        assert cut.count(line) == 1, line
        cut = cut.replace(line, "")
    with pytest.raises(SP.SplitStopped) as ei:
        SP.make_split_plan(Tree(files={**tree.files, helper_p: cut}, blobs=tree.blobs), MAPDOC, "cli.py", frozen=frozen,
                           ledger_text=ledger, strict=True, contracts_spec=spec)
    errs = [e for e in ei.value.errors if e.startswith("差し替えの届く先の守り: ")]
    for name in ("Ledger", "_HouseholdWalletLedger"):
        assert any(f"use_outside_bundle の名 {name}" in e and "届かない割り先 ['interfaces/cli/main.py']" in e
                   for e in errs), (name, ei.value.errors)
    # (iii) 別名の割り先の宣言を外す=宣言の在った別名は手で直す一覧へ・その差し替えは「見られなかった」へ
    monkeypatch.setattr(SP, "SPLIT_ALIAS_DESTS", ())
    with pytest.raises(SP.SplitRefused, match="手で直す"):
        SP.make_split_plan(tree, MAPDOC, "cli.py", frozen=frozen, ledger_text=ledger, strict=True, contracts_spec=spec)
    plan3 = SP.make_split_plan(tree, MAPDOC, "cli.py", frozen=frozen, ledger_text=ledger, strict=False,
                               contracts_spec=spec)
    assert any("tests/engine/test_resume_10d.py" in x and "build_ledger_bundle" in x and "手で直す一覧の別名" in x
               for x in plan3.patch_unseen), plan3.patch_unseen
    assert any(f"{helper_p}::use_outside_bundle の名 Ledger" in x for x in plan3.patch_unseen), plan3.patch_unseen
    assert not [x for x in plan3.patch_checked if "build_ledger_bundle" in x or helper_p in x], plan3.patch_checked
