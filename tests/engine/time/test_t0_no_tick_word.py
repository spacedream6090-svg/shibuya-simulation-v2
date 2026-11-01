"""第 1 期 1-1 時計 T0: 「tick」の語(用語集 :165・:208-209=使わない。「刻み」「計算のまとめ」)。

(a) ``src/shibuya/core/`` と ``src/shibuya/engine/systems/`` の注釈(``#``)と docstring に、引用の外の「tick」が無い。
    引用=バッククォートで囲んだ名(``tick_seconds`` など=ハッシュの鍵・manifest の欄・識別子をそのまま書く所)。
(b) ``src/shibuya`` の識別子のうち「tick」を含むものは ``tick_word_allow.json`` の中だけ(T0 の最初の一覧を凍結。
    名を足すと落ちる=新しいコードは「刻み」系の名を使う。名を替えたら表から消す=古い行が残っても落ちる)。
    ハッシュに入る名(状態台帳の鍵・道筋・持ち主)・manifest の欄・CLI の引数・テープの列は変えない(1-0 の規則)。
    それ以外の名の置き換えは段階的(T0 では替えない)。
"""

from __future__ import annotations

import ast
import io
import json
import re
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src" / "shibuya"
ALLOW = Path(__file__).with_name("tick_word_allow.json")
WORD_DIRS = (SRC / "core", SRC / "engine" / "systems")

TICK = re.compile(r"tick", re.I)
QUOTED = re.compile(r"``[^`]*``|`[^`]*`")


# ================================================================= (b) 識別子
def identifiers(text: str) -> set[str]:
    """識別子(名・属性・関数とクラスの名・引数・キーワード引数・import の名・global/nonlocal)のうち「tick」を含むもの。"""
    out: set[str] = set()
    for n in ast.walk(ast.parse(text)):
        names: list[str] = []
        if isinstance(n, ast.Name):
            names = [n.id]
        elif isinstance(n, ast.Attribute):
            names = [n.attr]
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names = [n.name]
        elif isinstance(n, ast.arg):
            names = [n.arg]
        elif isinstance(n, ast.keyword) and n.arg:
            names = [n.arg]
        elif isinstance(n, ast.alias):
            names = [n.asname or n.name.split(".")[-1]]
        elif isinstance(n, (ast.Global, ast.Nonlocal)):
            names = list(n.names)
        out |= {x for x in names if TICK.search(x)}
    return out


def tree_identifiers(root: Path = SRC) -> dict[str, set[str]]:
    found: dict[str, set[str]] = {}
    for p in sorted(root.rglob("*.py")):
        for name in identifiers(p.read_text(encoding="utf-8")):
            found.setdefault(name, set()).add(p.relative_to(ROOT).as_posix())
    return found


def test_no_new_identifier_with_the_word():
    allow = json.loads(ALLOW.read_text(encoding="utf-8"))
    found = tree_identifiers()
    new = {k: sorted(v) for k, v in found.items() if k not in allow}
    assert new == {}, f"「tick」を含む新しい識別子(刻み系の名にする): {new}"


def test_allow_table_has_reasons_and_no_stale_names():
    allow = json.loads(ALLOW.read_text(encoding="utf-8"))
    assert all(isinstance(v, str) and v.strip() for v in allow.values())
    found = tree_identifiers()
    stale = sorted(set(allow) - set(found))
    assert stale == [], f"allow の表の名がもう使われていない(表から消す): {stale}"


def test_kept_names_include_the_hash_and_interface_names():
    """変えない名(1-0 の規則)が理由つきで載っている(例: 状態台帳の道筋・manifest の欄・CLI の引数・テープの列)。"""
    allow = json.loads(ALLOW.read_text(encoding="utf-8"))
    for name in ("tick_ms_max", "tick_seconds", "ticks", "budget_per_tick", "stop_at_tick", "observed_tick",
                 "TickCtx"):
        assert name in allow, name
    assert "変えない" in allow["tick_ms_max"] and "変えない" in allow["budget_per_tick"]


def test_negative_control_identifiers():
    src = (
        "import tickle as tickle_mod\n"
        "def next_tick(tick_width, *, step):\n"
        "    T_TICK = 1\n"
        "    obj.tick_cache = f(ticks=2)\n"
        "    s = 'tick in a string is not a name'\n"
        "    # tick in a comment is not a name\n"
    )
    assert identifiers(src) == {"tickle_mod", "next_tick", "tick_width", "T_TICK", "tick_cache", "ticks"}


# ================================================================= (a) 注釈と docstring の語
def bare_word_lines(text: str) -> list[tuple[int, str]]:
    """注釈と docstring の行のうち、引用(バッククォート)の外に「tick」がある行。"""
    out: list[tuple[int, str]] = []
    for tok in tokenize.generate_tokens(io.StringIO(text).readline):
        if tok.type == tokenize.COMMENT and TICK.search(QUOTED.sub("", tok.string)):
            out.append((tok.start[0], tok.string.strip()))
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                d = body[0].value
                for k, line in enumerate(d.value.split("\n")):
                    if TICK.search(QUOTED.sub("", line)):
                        out.append((d.lineno + k, line.strip()))
    return sorted(out)


def test_no_bare_word_in_comments_and_docstrings_of_core_and_systems():
    bad = {}
    for d in WORD_DIRS:
        for p in sorted(d.rglob("*.py")):
            hits = bare_word_lines(p.read_text(encoding="utf-8"))
            if hits:
                bad[p.relative_to(ROOT).as_posix()] = hits
    assert bad == {}, f"注釈と docstring の「tick」(「刻み」「計算のまとめ」にする・名の引用はバッククォートで): {bad}"


def test_negative_control_words():
    src = (
        '"""1 tick の中の受け渡し(``tick_seconds`` は引用)。"""\n'
        "x = 1  # この tick に届く\n"
        "y = 2  # ``TickCtx`` は引用・刻み\n"
        "def f():\n"
        '    """刻みの頭で空にする。`ticks` は引用。"""\n'
        "    s = 'tick in a runtime string'\n"
    )
    assert [ln for ln, _ in bare_word_lines(src)] == [1, 2]
