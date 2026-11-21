# -*- coding: utf-8 -*-
"""relink.py で書いた後の確かめ(第348)。

使い方(リポの根で): ``python docs/bench/analysis/guide-links-348/tools/verify.py <リポの根> [--base HEAD]``

案内の手書きの .md ごとに、``--base``(既定 HEAD)の版と今の版を比べる:

1. 行の数と見出し(``#`` で始まる行)の数が同じ。CR が無い。
2. 各行で、リンクの向け先(括弧の中)を印に替えると、前と今の行が 1 字も違わない(リンクの数も同じ)。
3. 前に在る道を指していたリンクの向け先は変わっていない。
4. 今の版で無い道を指すリンクの数(消した物を指して残したものだけのはず)と、その一覧。

結果を標準出力と ``<--out-dir>/verify.json`` に書く。1〜3 が 1 つでも崩れれば終了コード 1。
"""
from __future__ import annotations

import argparse
import json
import posixpath
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import relink  # noqa: E402


def links(line: str) -> list[tuple[int, int, str]]:
    out = []
    for m in relink.LINK_RE.finditer(line):
        out.append((m.start(2), m.end(2), m.group(2)))
    return out


def masked(line: str) -> str:
    parts, last = [], 0
    for a, b, _t in links(line):
        parts.append(line[last:a])
        parts.append("\x00")
        last = b
    parts.append(line[last:])
    return "".join(parts)


def is_rel(t: str) -> bool:
    return not (t.startswith("#") or relink.re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", t))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--base", default="HEAD")
    ap.add_argument("--out-dir", default=None)
    a = ap.parse_args(argv)
    root = Path(a.root).resolve()
    out_dir = Path(a.out_dir) if a.out_dir else root / relink.DEFAULT_OUT
    res = {"base": a.base, "files": {}, "missing_after": [], "problems": []}
    for f in relink.guide_files(root):
        before = subprocess.run(["git", "show", f"{a.base}:{f}"], cwd=root, capture_output=True, check=True).stdout.decode("utf-8")
        after = (root / f).read_text(encoding="utf-8")
        base = posixpath.dirname(f)
        bl, al = before.split("\n"), after.split("\n")
        info = {"lines_before": len(bl), "lines_after": len(al),
                "headings_before": sum(1 for x in bl if x.startswith("#")),
                "headings_after": sum(1 for x in al if x.startswith("#")),
                "cr": "\r" in after, "changed_links": 0, "changed_lines": 0, "text_diff_lines": 0,
                "existing_link_changed": 0, "missing_after": 0}
        if info["lines_before"] != info["lines_after"] or info["headings_before"] != info["headings_after"] or info["cr"]:
            res["problems"].append(f"{f}: 行・見出しの数か CR")
        for i, (x, y) in enumerate(zip(bl, al), 1):
            if x != y:
                info["changed_lines"] += 1
            if masked(x) != masked(y):
                info["text_diff_lines"] += 1
                res["problems"].append(f"{f}:{i}: リンクの外の字が違う")
                continue
            for (_a, _b, t0), (_c, _d, t1) in zip(links(x), links(y)):
                if t0 == t1:
                    continue
                info["changed_links"] += 1
                if is_rel(t0) and (root / posixpath.normpath(posixpath.join(base, t0.partition("#")[0]))).exists():
                    info["existing_link_changed"] += 1
                    res["problems"].append(f"{f}:{i}: 在る道のリンクが変わった {t0} -> {t1}")
            for _a, _b, t in links(y):
                if is_rel(t):
                    full = posixpath.normpath(posixpath.join(base, t.partition("#")[0]))
                    if not (root / full).exists():
                        info["missing_after"] += 1
                        res["missing_after"].append({"file": f, "line": i, "target": t})
        res["files"][f] = info
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "verify.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(res, ensure_ascii=False, indent=1))
    return 1 if res["problems"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
