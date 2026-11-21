# -*- coding: utf-8 -*-
"""手で書いたコードの案内のリンクを、移した先・割った先の表で引き直す(第348・返事その 9 §1 の 25)。

使い方(リポの根で、venv の python で):

    python docs/bench/analysis/guide-links-348/tools/relink.py <リポの根>            # 書かない(数と差分だけ)
    python docs/bench/analysis/guide-links-348/tools/relink.py <リポの根> --apply    # 書く

- 対象: ``docs/reference/repo-guide/`` の手書きの .md(``cards/`` は自動で作るので外す)。
- 拾うのは行の中の ``[文字](向け先)`` の形の相対リンク(``http:`` などと、ファイルの中の ``#見出し`` だけのものは外す)。
- 直すのは、向け先が今の木に無いリンクだけ。向け先の括弧の中の道(と行の錨 ``#L42``)のほかは 1 字も変えない。
- 対応の表は ``tools/pkgmove/map.toml``(移す道具と割る道具の表)。
  - ``move`` の行: 新しい道へ(1 対 1)。
  - ``split`` の行: リンクの文字、無ければその行の文の `` ` `` で囲んだ名のうち、今の木(``src``)で頂上の定義がちょうど 1 か所に
    在り、その場所が割り先の 1 つであるものを探す。当たった割り先が 1 つならそこへ(名で割り先へ)。当たらない・2 つ以上に
    当たるときは表の主な割り先(``new``)へ(主な割り先へ)。
  - ディレクトリ: 古いディレクトリの中のファイルが全部同じ新しいディレクトリへ移ったときだけ、そのディレクトリへ。
  - ``delete`` の行(消した物)と表に無い道: 向け先を作らず、一覧に残す。
- 行の錨 ``#L<n>``・``#L<n>-L<m>`` は、名が当たればその定義の行へ付け替え、名が無ければ外す。
- 出力(``--out-dir``・既定は ``docs/bench/analysis/guide-links-348``): 書かない実行は ``dryrun_report.json`` と ``dryrun.diff``、
  ``--apply`` は ``apply_report.json`` と ``apply.diff``。
"""
from __future__ import annotations

import argparse
import ast
import difflib
import json
import posixpath
import re
import sys
import tomllib
from collections import Counter, defaultdict
from pathlib import Path

GUIDE_DIR = "docs/reference/repo-guide"
MAP_REL = "tools/pkgmove/map.toml"
SRC_PREFIX = "src/shibuya/"
DEFAULT_OUT = "docs/bench/analysis/guide-links-348"

LINK_RE = re.compile(r"\[((?:[^\[\]]|\[[^\]]*\])*)\]\(([^)\s]+)\)")
CODE_RE = re.compile(r"`([^`]+)`")
IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
LINE_ANCHOR_RE = re.compile(r"^L(\d+)(?:-L(\d+))?$")


def guide_files(root: Path) -> list[str]:
    out = []
    for p in sorted((root / GUIDE_DIR).rglob("*.md")):
        rel = p.relative_to(root).as_posix()
        if rel.startswith(GUIDE_DIR + "/cards/"):
            continue
        out.append(rel)
    return out


def load_map(root: Path) -> dict[str, dict]:
    doc = tomllib.loads((root / MAP_REL).read_text(encoding="utf-8"))
    return {r["old"]: r for r in doc["row"]}


def _top_defs(tree: ast.Module) -> list[tuple[str, int, int]]:
    """頂上の定義(関数・クラス・代入の左辺の名)と行。頂上の if・try の中も見る。"""
    out: list[tuple[str, int, int]] = []

    def walk(body):
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                out.append((node.name, node.lineno, node.end_lineno or node.lineno))
            elif isinstance(node, ast.Assign):
                for t in node.targets:
                    for n in ast.walk(t):
                        if isinstance(n, ast.Name):
                            out.append((n.id, node.lineno, node.end_lineno or node.lineno))
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                out.append((node.target.id, node.lineno, node.end_lineno or node.lineno))
            elif isinstance(node, ast.If):
                walk(node.body)
                walk(node.orelse)
            elif isinstance(node, ast.Try):
                walk(node.body)
                for h in node.handlers:
                    walk(h.body)
                walk(node.orelse)
                walk(node.finalbody)
    walk(tree.body)
    return out


def definition_index(root: Path) -> dict[str, list[tuple[str, int, int]]]:
    """名 → [(src/shibuya からの道, 始めの行, 終わりの行)]。同じファイルの中の重ねての定義は 1 か所に数える。"""
    idx: dict[str, list[tuple[str, int, int]]] = defaultdict(list)
    base = root / "src" / "shibuya"
    for p in sorted(base.rglob("*.py")):
        rel = p.relative_to(base).as_posix()
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        seen: set[str] = set()
        for name, a, b in _top_defs(tree):
            if name in seen:
                continue
            seen.add(name)
            idx[name].append((rel, a, b))
    return idx


def names_in(text: str) -> list[str]:
    out: list[str] = []
    for m in CODE_RE.finditer(text):
        for t in IDENT_RE.findall(m.group(1)):
            if t not in out:
                out.append(t)
    return out


def pick_split(row: dict, link_text: str, line: str, idx) -> tuple[str, str, list[str], dict]:
    """割る行の向け先。戻り値: (割り先, 方法, 当たった名, 当たった名ごとの定義)。"""
    dests = list(row.get("split_to") or [row["new"]])
    for scope, text in (("link", link_text), ("line", line)):
        hits: dict[str, tuple[str, int, int]] = {}
        for n in names_in(text):
            defs = idx.get(n, [])
            if len(defs) == 1 and defs[0][0] in dests:
                hits[n] = defs[0]
        found = {d[0] for d in hits.values()}
        if len(found) == 1:
            dest = found.pop()
            return dest, f"name_{scope}", sorted(hits), {k: list(v) for k, v in hits.items()}
        if len(found) > 1:
            return row["new"], f"main_many_{scope}", sorted(hits), {k: list(v) for k, v in hits.items()}
    return row["new"], "main_none", [], {}


def resolve(target_rel: str, link_text: str, line: str, rows, idx, root: Path):
    """無い道(リポの根からの相対)→ (新しい道 or None, 方法, 当たった名, 定義)。"""
    if not target_rel.startswith(SRC_PREFIX):
        return None, "outside_src", [], {}
    rel = target_rel[len(SRC_PREFIX):].rstrip("/")
    r = rows.get(rel)
    if r is None:
        # ディレクトリ: 古いディレクトリの中のファイルが全部同じ新しいディレクトリへ移ったときだけ
        inside = [x for o, x in rows.items() if o.startswith(rel + "/")]
        if inside:
            news = {posixpath.dirname(x.get("new", "")) for x in inside if x["kind"] == "move"}
            kinds = {x["kind"] for x in inside}
            if kinds == {"move"} and len(news) == 1:
                nd = news.pop()
                if (root / SRC_PREFIX / nd).is_dir():
                    return SRC_PREFIX + nd, "dir_one", [], {}
            return None, "dir_many", [], {}
        return None, "no_row", [], {}
    kind = r["kind"]
    if kind == "move":
        return SRC_PREFIX + r["new"], "move", [], {}
    if kind == "split":
        dest, how, hit, defs = pick_split(r, link_text, line, idx)
        return SRC_PREFIX + dest, how, hit, defs
    if kind == "delete":
        return None, "deleted", [], {}
    return None, f"kind_{kind}", [], {}


def process(root: Path, apply: bool, out_dir: Path) -> int:
    rows = load_map(root)
    idx = definition_index(root)
    report = {"schema": "guide-links-348/relink/1", "apply": apply, "files": {}, "changes": [], "left": [],
              "anchor": {"retargeted": 0, "dropped": 0}, "map_mismatch": []}
    diffs: list[str] = []
    for f in guide_files(root):
        p = root / f
        text = p.read_text(encoding="utf-8")
        if "\r" in text:
            print(f"CR が入っている: {f}", file=sys.stderr)
            return 2
        base = posixpath.dirname(f)
        lines = text.split("\n")
        cnt = Counter()
        new_lines = []
        for ln, line in enumerate(lines, 1):
            pieces = []
            last = 0
            for m in LINK_RE.finditer(line):
                link_text, target = m.group(1), m.group(2)
                if re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", target) or target.startswith("#"):
                    continue
                cnt["picked"] += 1
                path, sep, anchor = target.partition("#")
                full = posixpath.normpath(posixpath.join(base, path))
                if (root / full).exists():
                    cnt["exists"] += 1
                    continue
                cnt["missing"] += 1
                new_full, how, hit, defs = resolve(full, link_text, line, rows, idx, root)
                rec = {"file": f, "line": ln, "text": link_text, "old": target, "how": how, "names": hit}
                if new_full is not None and not (root / new_full).exists():
                    rec["how"] = f"{how}_dest_missing"
                    new_full = None
                if new_full is None:
                    cnt["left"] += 1
                    report["left"].append(rec)
                    continue
                new_path = posixpath.relpath(new_full, base)
                if path.endswith("/"):
                    new_path += "/"
                new_anchor = anchor
                if sep and LINE_ANCHOR_RE.match(anchor):
                    if hit:
                        a, b = defs[hit[0]][1], defs[hit[0]][2]
                        new_anchor = f"L{a}" if LINE_ANCHOR_RE.match(anchor).group(2) is None else f"L{a}-L{b}"
                        report["anchor"]["retargeted"] += 1
                        cnt["anchor_retargeted"] += 1
                    else:
                        new_anchor = ""
                        report["anchor"]["dropped"] += 1
                        cnt["anchor_dropped"] += 1
                new_target = new_path + (("#" + new_anchor) if new_anchor else "")
                # 割る行の名ごとの表と、今の木の定義の場所が違えば記録する(向け先は今の木に従う)
                if how.startswith("name_"):
                    row = rows[full[len(SRC_PREFIX):]]
                    for n in hit:
                        mp = (row.get("names") or {}).get(n)
                        if mp is not None and mp != defs[n][0]:
                            report["map_mismatch"].append({"file": f, "line": ln, "name": n, "map": mp, "tree": defs[n][0]})
                key = {"move": "one_to_one", "dir_one": "one_to_one_dir"}.get(how, "by_name" if how.startswith("name_") else "main")
                cnt[key] += 1
                if how.startswith("main_many"):
                    cnt["main_many"] += 1
                rec.update({"new": new_target, "dest": new_full})
                report["changes"].append(rec)
                pieces.append(line[last:m.start(2)])
                pieces.append(new_target)
                last = m.end(2)
            pieces.append(line[last:])
            new_lines.append("".join(pieces))
        new_text = "\n".join(new_lines)
        report["files"][f] = dict(cnt)
        if new_text != text:
            diffs.extend(difflib.unified_diff(text.split("\n"), new_text.split("\n"), f"a/{f}", f"b/{f}", lineterm="", n=0))
            if apply:
                with open(p, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(new_text)
    tot = Counter()
    for c in report["files"].values():
        tot.update(c)
    report["total"] = dict(tot)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = "apply" if apply else "dryrun"
    (out_dir / f"{stem}_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8",
                                                 newline="\n")
    (out_dir / f"{stem}.diff").write_text("\n".join(diffs) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"files": report["files"], "total": report["total"], "anchor": report["anchor"],
                      "left": len(report["left"]), "map_mismatch": len(report["map_mismatch"])}, ensure_ascii=False, indent=1))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("root", help="リポの根")
    ap.add_argument("--apply", action="store_true", help="書く(既定は書かずに数と差分だけ)")
    ap.add_argument("--out-dir", default=None, help=f"出力の置き場(既定 <根>/{DEFAULT_OUT})")
    a = ap.parse_args(argv)
    root = Path(a.root).resolve()
    out = Path(a.out_dir) if a.out_dir else root / DEFAULT_OUT
    return process(root, a.apply, out)


if __name__ == "__main__":
    raise SystemExit(main())
