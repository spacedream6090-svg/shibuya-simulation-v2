# -*- coding: utf-8 -*-
"""第348 試験の地図の数え(その 2): 消した旧道を「試験の中だけの口」で回す試験関数と、古い写しと比べる試験関数を数える。

静的(AST)に数える。試験は回さない。tests/c7 は開かない。
- 助けのモジュール(下の HELPERS)から import した名を、試験関数の本体が読んでいれば数える。
- fixture を通した間接の使い方は数えない(下限の数)。parametrize の展開の前の関数の数。

使い方: python -X utf8 count_legacy.py <tests の根>
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

#: 助けのモジュールの道(完全な名)。`from <親> import <名>` の形と `from <道> import <名>` の形の両方を見る。
HELPERS = {
    "空腹 v1(試験の中だけの口)": ("tests.engine.body._hunger_v1",),
    "旧のセルの移動 legacy(試験の中だけの口)": ("tests.engine.space._legacy",),
    "率の規則と「無い」の過程の旧道(試験の中だけの口)": ("tests.engine._legacy_world",),
    "古い commit 136fdbb の写しと比べる": ("tests.perception.facts.head_renderer_136fdbb", "tests.perception.facts.scenes",
                                         "tests.economy.cp2.head_copies"),
}


def imported_names(tree: ast.Module, keys: tuple[str, ...]) -> set[str]:
    names: set[str] = set()
    for st in ast.walk(tree):
        if isinstance(st, ast.ImportFrom) and st.module:
            mod = st.module
            for al in st.names:
                if mod in keys or f"{mod}.{al.name}" in keys:
                    names.add(al.asname or al.name)
        elif isinstance(st, ast.Import):
            for al in st.names:
                if al.name in keys:
                    names.add(al.asname or al.name.split(".")[0])
    return names


def main() -> None:
    root = Path(sys.argv[1])
    print("| 種類 | ファイル | 試験関数(静的) | うち助けを読む関数(静的・下限) |")
    print("|---|---|---:|---:|")
    totals: dict[str, tuple[int, int, int]] = {}
    for p in sorted(root.rglob("test_*.py")):
        rel = p.relative_to(root.parent).as_posix()
        if rel.split("/")[1] == "c7":
            continue  # 開かない
        tree = ast.parse(p.read_text(encoding="utf-8"))
        tests = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                 and n.name.startswith("test")]
        for label, keys in HELPERS.items():
            names = imported_names(tree, keys)
            if not names:
                continue
            hit = sum(1 for fn in tests if any(isinstance(x, ast.Name) and x.id in names for x in ast.walk(fn)))
            print(f"| {label} | `{rel}` | {len(tests)} | {hit} |")
            f, t, h = totals.get(label, (0, 0, 0))
            totals[label] = (f + 1, t + len(tests), h + hit)
    print()
    print("| 種類 | ファイル数 | 試験関数(静的) | うち助けを読む関数(静的・下限) |")
    print("|---|---:|---:|---:|")
    for label, (f, t, h) in totals.items():
        print(f"| {label} | {f} | {t} | {h} |")


if __name__ == "__main__":
    main()
