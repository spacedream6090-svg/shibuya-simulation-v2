# -*- coding: utf-8 -*-
"""第348 試験の地図(docs/design/plan-348-test-map.md)の数え。読むだけ。試験は回さない。

入力(どれも引数で渡す。機械の道は書かない):
  --fast  `pytest --collect-only -q -m "not gpu and not slow"` の出力(addopts の -q と重なって「ファイル: 本数」の形)
  --slow  `pytest --collect-only -q -m "slow and not gpu"` の出力
  --tests tests の根(静的に数える。tests/c7 は開かない=名前と本数だけを --fast から数える)
  --ci-log CI の ci-1 の job の記録(進み具合の行に時刻がある形)。何本でも。ディレクトリごとの時間の見積りに使う

出力(標準出力・Markdown):
  1. tests の直下ごとの本数(速い/slow)と、data の印のある試験関数の割合(静的)
  2. tests/engine の下ごとの本数
  3. CI の進み具合の行から割り当てたディレクトリごとの分(推測。集めた順に終わるとみなした見積り)

data の印の数え方(静的・試験関数の数で、parametrize の展開の前):
  - モジュールの pytestmark に requires_data(または requires_data から作った別名)があれば、そのファイルの全部
  - 関数かクラスの飾りに requires_data か別名があれば、その関数(クラスなら中の全部)
  - 関数の中で skip_unless( を呼ぶものは「途中で data を見る」として別に数える
tests/c7 は開かないので、この欄は「数えていない」。
"""
from __future__ import annotations

import argparse
import ast
import bisect
import datetime as dt
import re
from collections import Counter, defaultdict
from pathlib import Path

LINE = re.compile(r"^(tests[/\\]\S+?\.py): (\d+)$")
TS = re.compile(r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d+)Z ([.sxXFE]+)\s+\[\s*(\d+)%\]\s*$")
SEALED_DIR = "c7"


def read_collect(path: str) -> list[tuple[str, int]]:
    out = []
    for line in open(path, encoding="utf-8", errors="replace"):
        m = LINE.match(line.strip())
        if m:
            out.append((m.group(1).replace("\\", "/"), int(m.group(2))))
    return out


def top_of(rel: str) -> str:
    parts = rel.split("/")
    return parts[1] if len(parts) > 2 else "(直下のファイル)"


def _mentions(node: ast.AST, names: set[str]) -> bool:
    for sub in ast.walk(node):
        if isinstance(sub, ast.Attribute) and sub.attr == "requires_data":
            return True
        if isinstance(sub, ast.Name) and sub.id in names:
            return True
    return False


def scan_file(path: Path) -> tuple[int, int, int]:
    """(試験関数の数, data の印のある数, 途中で skip_unless を呼ぶ数)。"""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception:
        return (0, 0, 0)
    alias: set[str] = set()
    module_marked = False
    for st in tree.body:
        if isinstance(st, ast.Assign):
            if _mentions(st.value, alias):
                for t in st.targets:
                    if isinstance(t, ast.Name):
                        if t.id == "pytestmark":
                            module_marked = True
                        else:
                            alias.add(t.id)
    n = marked = mid = 0

    def visit(fn: ast.AST, inherited: bool) -> None:
        nonlocal n, marked, mid
        n += 1
        deco = any(_mentions(d, alias) for d in getattr(fn, "decorator_list", []))
        if module_marked or inherited or deco:
            marked += 1
        elif any(isinstance(c, ast.Call) and getattr(c.func, "attr", getattr(c.func, "id", "")) == "skip_unless"
                 for c in ast.walk(fn)):
            mid += 1

    for st in tree.body:
        if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef)) and st.name.startswith("test"):
            visit(st, False)
        elif isinstance(st, ast.ClassDef) and st.name.startswith("Test"):
            cls = any(_mentions(d, alias) for d in st.decorator_list)
            for b in st.body:
                if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef)) and b.name.startswith("test"):
                    visit(b, cls)
    return (n, marked, mid)


def ci_minutes(log: str, order: list[tuple[str, int]]) -> tuple[dict[str, float], int, float]:
    start = None
    pts = []
    for line in open(log, encoding="utf-8", errors="replace"):
        if "bringing up nodes" in line and start is None:
            m = re.search(r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d+)Z", line)
            start = dt.datetime.fromisoformat(m.group(1)[:26])
        m = TS.search(line)
        if m:
            pts.append((dt.datetime.fromisoformat(m.group(1)[:26]), len(m.group(2))))
    if not pts or start is None:
        return {}, 0, 0.0
    cum, c = [], 0
    for t, k in pts:
        c += k
        cum.append((c, (t - start).total_seconds()))
    counts = [x for x, _ in cum]

    def t_at(k: float) -> float:
        i = bisect.bisect_left(counts, k)
        if i == 0:
            return cum[0][1] * k / max(1, cum[0][0])
        if i >= len(cum):
            return cum[-1][1]
        (c0, t0), (c1, t1) = cum[i - 1], cum[i]
        return t0 + (t1 - t0) * (k - c0) / max(1, c1 - c0)

    local = sum(n for _, n in order)
    scale = c / local if local else 1.0  # CI の本数と手元の本数の違いを比で均す
    per: dict[str, float] = defaultdict(float)
    acc = 0.0
    for name, n in order:
        per[name] += (t_at((acc + n) * scale) - t_at(acc * scale)) / 60
        acc += n
    return dict(per), c, cum[-1][1] / 60


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", required=True)
    ap.add_argument("--slow", required=True)
    ap.add_argument("--tests", required=True)
    ap.add_argument("--ci-log", nargs="*", default=[])
    a = ap.parse_args()

    fast = read_collect(a.fast)
    slow = read_collect(a.slow)
    f_by, s_by = Counter(), Counter()
    f_files, s_files = Counter(), Counter()
    for rel, k in fast:
        f_by[top_of(rel)] += k
        f_files[top_of(rel)] += 1
    for rel, k in slow:
        s_by[top_of(rel)] += k
        s_files[top_of(rel)] += 1

    root = Path(a.tests)
    st_n, st_m, st_mid = Counter(), Counter(), Counter()
    for p in root.rglob("test_*.py"):
        rel = p.relative_to(root.parent).as_posix()
        if rel.split("/")[1] == SEALED_DIR:
            continue  # 開かない
        n, m, mid = scan_file(p)
        key = top_of(rel)
        st_n[key] += n
        st_m[key] += m
        st_mid[key] += mid

    tops = sorted(set(f_by) | set(s_by), key=lambda t: -(f_by[t] + s_by[t]))
    print("## 1. tests の直下ごと\n")
    print("| 直下 | 速い(本) | 速いのファイル | slow(本) | 試験関数(静的) | data の印(静的) | 途中で data を見る(静的) |")
    print("|---|---:|---:|---:|---:|---:|---:|")
    for t in tops:
        if t == SEALED_DIR:
            print(f"| {t} | {f_by[t]} | {f_files[t]} | {s_by[t]} | 数えていない | 数えていない | 数えていない |")
        else:
            print(f"| {t} | {f_by[t]} | {f_files[t]} | {s_by[t]} | {st_n[t]} | {st_m[t]} | {st_mid[t]} |")
    print(f"| 計 | {sum(f_by.values())} | {sum(f_files.values())} | {sum(s_by.values())} | "
          f"{sum(st_n.values())} | {sum(st_m.values())} | {sum(st_mid.values())} |\n")

    print("## 2. tests/engine の下ごと\n")
    sub_f, sub_s = Counter(), Counter()
    for rel, k in fast:
        p = rel.split("/")
        if p[1] == "engine":
            sub_f[p[2] if len(p) > 3 else "(engine 直下)"] += k
    for rel, k in slow:
        p = rel.split("/")
        if p[1] == "engine":
            sub_s[p[2] if len(p) > 3 else "(engine 直下)"] += k
    print("| engine の下 | 速い(本) | slow(本) |")
    print("|---|---:|---:|")
    for s in sorted(set(sub_f) | set(sub_s), key=lambda x: -(sub_f[x] + sub_s[x])):
        print(f"| {s} | {sub_f[s]} | {sub_s[s]} |")
    print()

    if a.ci_log:
        order: list[tuple[str, int]] = []
        for rel, k in fast:
            t = top_of(rel)
            if order and order[-1][0] == t:
                order[-1] = (t, order[-1][1] + k)
            else:
                order.append((t, k))
        print("## 3. CI の ci-1 のディレクトリごとの分(推測=集めた順に終わるとみなして、進み具合の行の時刻を割り当てた)\n")
        res = [ci_minutes(f, order) for f in a.ci_log]
        print("| 直下 | " + " | ".join(f"記録 {i + 1}" for i in range(len(res))) + " |")
        print("|---|" + "---:|" * len(res))
        names = []
        for n, _ in order:
            if n not in names:
                names.append(n)
        for n in sorted(names, key=lambda x: -sum(r[0].get(x, 0.0) for r in res)):
            print(f"| {n} | " + " | ".join(f"{r[0].get(n, 0.0):.1f}" for r in res) + " |")
        print("| 計(試験の段の壁時計) | " + " | ".join(f"{r[2]:.1f}" for r in res) + " |")
        print("| CI の本数(進み具合の字の数) | " + " | ".join(str(r[1]) for r in res) + " |")


if __name__ == "__main__":
    main()
