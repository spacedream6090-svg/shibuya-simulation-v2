#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""段 3 ファイルのカードを作る(11-05/§3-1 の 1)。標準ライブラリだけ。対象のコードは import も実行もしない。

  python tools/repo_guide/build.py            # 全部を作り直す
  python tools/repo_guide/build.py --check    # src・tests・tools のカードだけを作って置いてあるものと比べる(違えば exit 1)

出力は ``docs/reference/repo-guide/cards/``。読み方の規則は入口の索引 ``cards/README.md``(``guide_render.RULES``)。
``data/`` の中のファイルは 1 本も開かない(``os.scandir`` の名前と stat の大きさだけ)。``--check`` は docs と data に触らない。
"""
from __future__ import annotations

import argparse
import base64
import os
import re
import subprocess
import sys
import time
import warnings
from pathlib import Path

import guide_facts as F
import guide_permits as P
import guide_render as R

CODE_ROOTS = ("src", "tests", "tools")
SKIP_DIRS = {"__pycache__", ".git", ".venv", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules"}
MASK = "〔伏〕"
DATA_DEPTH = 2


def list_files(root: Path, tops: tuple[str, ...]) -> list[str]:
    """リポからの道筋の一覧(sort 済み・``/`` 区切り)。git があれば追跡+無視されない未追跡、無ければ歩く。"""
    if (root / ".git").exists():
        cp = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", *tops],
            capture_output=True, check=True)
        rels = [x.decode("utf-8") for x in cp.stdout.split(b"\0") if x]
        return sorted(r for r in rels if (root / r).is_file())
    out: list[str] = []
    for top in tops:
        base = root / top
        if not base.is_dir():
            continue
        for d, subdirs, names in os.walk(base):
            subdirs[:] = [s for s in subdirs if s not in SKIP_DIRS]
            rel_dir = Path(d).relative_to(root).as_posix()
            out.extend(f"{rel_dir}/{n}" for n in names)
    return sorted(out)


def list_untracked(root: Path, tops: tuple[str, ...]) -> list[str]:
    """無視されない未追跡のファイル(``.git`` が無ければ空)。カードには載るが commit に入るとは限らないので知らせる。"""
    if not (root / ".git").exists():
        return []
    cp = subprocess.run(["git", "-C", str(root), "ls-files", "-z", "--others", "--exclude-standard", "--", *tops],
                        capture_output=True, check=True)
    return sorted(x.decode("utf-8") for x in cp.stdout.split(b"\0") if x)


# ---------------------------------------------------------------- 伏せる語
def mask_patterns(root: Path) -> list[re.Pattern[str]]:
    """検出パターンを 2 つの検査の道具のソースから AST で読む(本道具に語を持たない)。"""
    out: list[re.Pattern[str]] = []
    for rel, name in (("tools/scan_secrets.py", "_B64"), ("tools/commit_check.py", "_BAD_PATH_B64")):
        path = root / rel
        if not path.is_file():
            continue
        value = P.read_constant(path, name)  # 無ければ KeyError=止まる(検査の道具の形が変わったら直す)
        out.append(re.compile(base64.b64decode(str(value)).decode("utf-8")))
    return out


def apply_masks(text: str, patterns: list[re.Pattern[str]]) -> tuple[str, int]:
    total = 0
    for pat in patterns:
        text, n = pat.subn(MASK, text)
        total += n
    return text, total


# ---------------------------------------------------------------- src・tests・tools のカード
class CodeCards:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.all_files = list_files(root, CODE_ROOTS)
        self.untracked = list_untracked(root, CODE_ROOTS)
        self.py_files = [r for r in self.all_files if r.endswith(".py")]
        regexes = F.decision_regexes(self._decision_prefixes())
        self.facts = {r: F.read_python(r, (root / r).read_bytes(), regexes) for r in self.py_files}
        self.permits = P.read_permits(root)
        self.index = F.ModuleIndex(self.py_files, self.facts)
        self.edges = R.build_edges(self.index, self.facts)
        self.dirs = R.build_dir_table(self.all_files, set(self.py_files))
        self.problems = list(self.permits.problems)
        for r, f in sorted(self.facts.items()):
            if f.error:
                self.problems.append(f"`{r}`: {f.error}")
            if f.syspath_unread:
                self.problems.append(f"`{r}`: `sys.path` に足す先を読めない所 {f.syspath_unread} か所")
            for name, target in sorted(self.index.unresolved_bare(r).items()):
                self.problems.append(f"`{r}`: 解けない素の import `{name}`(同じ名のファイル `{target}` が 1 つある)")

    def _decision_prefixes(self) -> list[str]:
        path = self.root / "tools" / "decision_index.py"
        if not path.is_file():
            return []
        docs = P.read_constant(path, "DOCS")
        return sorted(str(row[0]) for row in docs)  # type: ignore[union-attr, index]

    def render(self) -> dict[str, str]:
        ledger = R.ledger_lines_by_file(self.permits)
        permits = R.permit_lines_by_file(self.permits)
        cards: dict[str, str] = {}
        for d in sorted(self.dirs):
            cards[R.card_path(d)] = R.render_dir_card(self.dirs[d], self.facts, self.index, self.edges, ledger, permits)
        return cards


def masked(cards: dict[str, str], patterns: list[re.Pattern[str]]) -> tuple[dict[str, str], dict[str, int]]:
    out: dict[str, str] = {}
    counts: dict[str, int] = {}
    for path, text in cards.items():
        t, n = apply_masks(text, patterns)
        out[path] = t
        if n:
            counts[path] = n
    return out, counts


def _on_disk_lf(path: Path) -> str | None:
    if not path.is_file():
        return None
    return path.read_bytes().replace(b"\r\n", b"\n").decode("utf-8", errors="replace")


def check(root: Path, cards: dict[str, str]) -> list[str]:
    """(差のあるファイルの一覧)。無いカード・余計なカードも差に入れる。"""
    diffs: list[str] = []
    for rel in sorted(cards):
        cur = _on_disk_lf(root / rel)
        if cur is None:
            diffs.append(f"無い: {rel}")
        elif cur != cards[rel]:
            diffs.append(f"違う: {rel}")
    for top in CODE_ROOTS:
        base = root / R.CARDS_REL / top
        if base.is_dir():
            for p in sorted(base.rglob("*.md")):
                rel = p.relative_to(root).as_posix()
                if rel not in cards:
                    diffs.append(f"余計: {rel}")
    return diffs


# ---------------------------------------------------------------- docs の索引
_HEADING = re.compile(r"^#{1,6}\s+(.*\S)\s*$")


def first_heading(raw: bytes) -> str:
    text = raw.decode("utf-8-sig", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
    fenced = False
    for line in text.split("\n"):
        if line.startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            m = _HEADING.match(line)
            if m:
                return m.group(1)
    return "(見出しなし)"


def docs_rows(root: Path) -> dict[str, tuple[int, list[tuple[str, str]]]]:
    rows: dict[str, tuple[int, list[tuple[str, str]]]] = {}
    for rel in list_files(root, ("docs",)):
        if rel.startswith(R.CARDS_REL + "/"):
            continue
        d, _, name = rel.rpartition("/")
        n, mds = rows.get(d, (0, []))
        if name.lower().endswith(".md"):
            mds.append((name, first_heading((root / rel).read_bytes())))
        rows[d] = (n + 1, mds)
    return rows


# ---------------------------------------------------------------- data の一覧(ファイルは 1 本も開かない)
def _dir_size(path: str, problems: list[str], label: str) -> int:
    """下の全部のファイルの大きさの合計(``os.scandir`` と stat だけ・リンクはたどらない)。

    読めなかった所は、深い階層の名前を出さず、一覧に載せるディレクトリの名前 ``label`` で止める。
    """
    total = 0
    stack = [path]
    while stack:
        cur = stack.pop()
        try:
            with os.scandir(cur) as it:
                entries = list(it)
        except OSError:
            problems.append(label)
            continue
        for e in entries:
            try:
                if e.is_symlink() or (hasattr(e, "is_junction") and e.is_junction()):
                    continue
                if e.is_dir(follow_symlinks=False):
                    stack.append(e.path)
                else:
                    total += e.stat(follow_symlinks=False).st_size
            except OSError:
                problems.append(label)
    return total


def data_rows(root: Path) -> tuple[list[tuple[str, int | None]], list[str]]:
    base = str(root / "data")
    rows: list[tuple[str, int | None]] = []
    problems: list[str] = []

    def walk(path: str, label: str, depth: int) -> None:
        rows.append((label, _dir_size(path, problems, label)))
        if depth >= DATA_DEPTH:
            return
        try:
            with os.scandir(path) as it:
                entries = sorted(it, key=lambda e: e.name)
        except OSError:
            return
        for e in entries:
            child = f"{label}/{e.name}"
            if e.is_symlink() or (hasattr(e, "is_junction") and e.is_junction()):
                rows.append((child, None))
            elif e.is_dir(follow_symlinks=False):
                walk(e.path, child, depth + 1)

    walk(base, "data", 0)
    return rows, sorted(set(problems))


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def build_all(root: Path, code: CodeCards, cards: dict[str, str], patterns: list[re.Pattern[str]]) -> dict[str, int]:
    """全部を書く。戻り値は伏せた語の数(ファイルごと)。"""
    for rel, text in cards.items():
        _write(root, rel, text)
    for top in CODE_ROOTS:
        base = root / R.CARDS_REL / top
        if base.is_dir():
            for p in base.rglob("*.md"):
                if p.relative_to(root).as_posix() not in cards:
                    p.unlink()
    counts: dict[str, int] = {}
    rows = docs_rows(root)
    extra: dict[str, str] = {f"{R.CARDS_REL}/docs.md": R.render_docs_index(rows)}
    if (root / "data").is_dir():
        d_rows, d_problems = data_rows(root)
        extra[f"{R.CARDS_REL}/data.md"] = R.render_data_index(d_rows, d_problems)
    else:
        print("[repo_guide] data が無いので data の一覧は作り直さない")
    extra[f"{R.CARDS_REL}/README.md"] = R.render_readme(code.dirs, rows, code.problems)
    for rel, text in extra.items():
        t, n = apply_masks(text, patterns)
        if n:
            counts[rel] = n
        _write(root, rel, t)
    return counts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="src・tests・tools のカードだけを作って比べる(違えば exit 1)")
    ap.add_argument("--root", type=Path, default=None, help="リポの根(既定はこのファイルから 2 つ上・試験用)")
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")  # 端末の文字コードに無い字で止まらない
    root = (args.root if args.root is not None else Path(__file__).resolve().parents[2]).resolve()
    started = time.perf_counter()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # 対象のコードの SyntaxWarning(無効なエスケープなど)を出さない
        code = CodeCards(root)
    patterns = mask_patterns(root)
    cards, counts = masked(code.render(), patterns)
    if code.untracked:
        print(f"[repo_guide] 未追跡 {len(code.untracked)} 本を含む(カードには載る。commit に入れないなら CI と食い違う)")
        for rel in code.untracked:
            print(f"  未追跡: {rel}")
    if args.check:
        diffs = check(root, cards)
        if diffs:
            for d in diffs:
                print(d)
            print(f"[repo_guide] カードが古い({len(diffs)} 本)。`python tools/repo_guide/build.py` で作り直す", file=sys.stderr)
            return 1
        print(f"[repo_guide] 最新(カード {len(cards)} 本)")
        return 0
    counts.update(build_all(root, code, cards, patterns))
    print(f"[repo_guide] カード {len(cards)} 本・Python {len(code.py_files)} 本・読めなかったもの {len(code.problems)} 件"
          f"・伏せた語 {sum(counts.values())} 件・{time.perf_counter() - started:.1f} 秒")
    for rel in sorted(counts):
        print(f"  伏せた {counts[rel]} 件: {rel}")
    for p in code.problems:
        print(f"  読めなかった: {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
