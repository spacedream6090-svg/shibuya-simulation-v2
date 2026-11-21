# -*- coding: utf-8 -*-
"""入っている版がロックのファイル(``requirements-lock.txt``)と同じかを確かめる(第348・返事その 9 §1 の 13)。

CI の 3 つの仕事と手元で、ロックの版を入れた後に回す。違えば終了コード 1 で落とす。

    python tools/ci/check_lock.py [--lock requirements-lock.txt] [--freeze <pip freeze の出力のファイル>]

比べるもの:

1. 配布の版: ロックの行(``名==版`` と、あれば ``; 環境の印``)のうち、今の環境で印が真の行と、
   ``python -m pip freeze --exclude-editable`` の行を、名前を正規化して(小文字・``-_.`` を ``-`` に)比べる。
   足りない(ロックにあるのに入っていない)・余る(入っているのにロックに無い)・版が違う、のどれかがあれば 1。
   印が偽の行(Linux での colorama など)は数えない。
2. pip と Python の版: ロックの頭の注の ``# pip==…``・``# python==…`` の行と、入っている pip・動いている Python の版。

ロックの行は ``==`` の固定だけを許す(``>=`` など・同じ名の重なり・読めない行は誤り=2)。
``--freeze`` は試験と、別の venv の一覧を比べるときの口(無ければこの python で ``pip freeze`` を回す)。

終了コード: 0=同じ・1=違う・2=誤り(ロックが読めない・``pip freeze`` が回らない)。
"""

from __future__ import annotations

import argparse
import importlib.metadata
import platform
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Sequence

ROOT = Path(__file__).resolve().parents[2]
LOCK: Final[Path] = ROOT / "requirements-lock.txt"

EXIT_SAME, EXIT_DIFF, EXIT_ERROR = 0, 1, 2

#: ロックの頭の注で、入っている pip と動いている Python の版を書く行(``# pip==26.2.1`` の形)。
HEAD_RE: Final[re.Pattern[str]] = re.compile(r"^#\s*(pip|python)==(\S+)\s*$")
#: ロックの行(``名==版`` と任意の ``; 環境の印``)。
LINE_RE: Final[re.Pattern[str]] = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==([^\s;]+)\s*(?:;\s*(.+))?$")


def normalize(name: str) -> str:
    """配布の名を比べる形に(PEP 503: 小文字・``-_.`` の続きを ``-`` に)。"""
    return re.sub(r"[-_.]+", "-", name).lower()


@dataclass(frozen=True)
class LockLine:
    name: str
    version: str
    marker: str
    lineno: int


@dataclass(frozen=True)
class Lock:
    lines: tuple[LockLine, ...]
    head: dict[str, str]


def parse_lock(text: str) -> Lock:
    """ロックの文を読む。``==`` でない行・同じ名の重なり・頭の行の重なりは ``ValueError``。"""
    lines: list[LockLine] = []
    head: dict[str, str] = {}
    seen: dict[str, int] = {}
    for i, raw in enumerate(text.splitlines(), start=1):
        s = raw.strip()
        if not s:
            continue
        if s.startswith("#"):
            m = HEAD_RE.match(s)
            if m:
                if m.group(1) in head:
                    raise ValueError(f"{i} 行目: 頭の行 {m.group(1)}== が 2 つある")
                head[m.group(1)] = m.group(2)
            continue
        m = LINE_RE.match(s)
        if not m:
            raise ValueError(f"{i} 行目: `名==版` の形でない(ロックは == の固定だけ): {s!r}")
        key = normalize(m.group(1))
        if key in seen:
            raise ValueError(f"{i} 行目: {m.group(1)} が {seen[key]} 行目と重なる")
        seen[key] = i
        lines.append(LockLine(m.group(1), m.group(2), (m.group(3) or "").strip(), i))
    return Lock(tuple(lines), head)


def parse_freeze(text: str) -> dict[str, str]:
    """``pip freeze`` の出力を読む(正規化した名 → 版)。``-e`` の行と注は飛ばす。``名 @ URL`` は版を ``@ URL`` とする。"""
    out: dict[str, str] = {}
    for raw in text.splitlines():
        s = raw.strip()
        if not s or s.startswith(("#", "-e ", "--editable")):
            continue
        if "==" in s:
            name, _, ver = s.partition("==")
        elif " @ " in s:
            name, _, url = s.partition(" @ ")
            ver = "@ " + url.strip()
        else:
            name, ver = s, "(版なし)"
        out[normalize(name.strip())] = ver.strip()
    return out


def marker_applies(marker: str, env: dict[str, str] | None = None) -> bool:
    """環境の印が今の環境(か ``env`` で上書きした環境)で真か。印が無ければ真。"""
    if not marker:
        return True
    from packaging.markers import Marker  # ロックに入っている(pytest の依存)

    return bool(Marker(marker).evaluate(env))


def compare(lock: Lock, installed: dict[str, str], *, env: dict[str, str] | None = None) -> dict[str, Any]:
    """ロックと入っている版を比べる。戻り値の ``missing``・``extra``・``differ`` のどれかが空でなければ違う。"""
    want: dict[str, LockLine] = {}
    not_here: list[str] = []
    for ln in lock.lines:
        if marker_applies(ln.marker, env):
            want[normalize(ln.name)] = ln
        else:
            not_here.append(ln.name)
    missing = sorted(f"{ln.name}=={ln.version}" for k, ln in want.items() if k not in installed)
    extra = sorted(f"{k}=={v}" for k, v in installed.items() if k not in want)
    differ = sorted(f"{ln.name}: ロック {ln.version}・入っている {installed[k]}"
                    for k, ln in want.items() if k in installed and installed[k] != ln.version)
    return {"missing": missing, "extra": extra, "differ": differ, "not_here": sorted(not_here),
            "n_lock": len(want), "n_installed": len(installed)}


def head_checks(lock: Lock, *, pip_version: str, python_version: str) -> list[str]:
    """頭の行の pip と Python の版が、入っている pip と動いている Python と同じか(頭の行が無いのも違いに数える)。"""
    out: list[str] = []
    for key, now in (("pip", pip_version), ("python", python_version)):
        want = lock.head.get(key)
        if want is None:
            out.append(f"ロックの頭に `# {key}==…` の行が無い")
        elif want != now:
            out.append(f"{key}: ロック {want}・今 {now}")
    return out


def freeze_here() -> str:
    """この python で ``pip freeze --exclude-editable`` を回した出力。"""
    r = subprocess.run([sys.executable, "-m", "pip", "freeze", "--exclude-editable"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"pip freeze が終了コード {r.returncode}: {r.stderr.strip()[-500:]}")
    return r.stdout


def pip_here() -> str:
    try:
        return importlib.metadata.version("pip")
    except importlib.metadata.PackageNotFoundError:
        return "(pip が無い)"


def render(diff: dict[str, Any], heads: list[str]) -> list[str]:
    """人が読む行(違いがあれば 1 行ずつ)。"""
    lines: list[str] = []
    for key, label in (("missing", "足りない(ロックにあるのに入っていない)"), ("extra", "余る(入っているのにロックに無い)"),
                       ("differ", "版が違う")):
        for x in diff[key]:
            lines.append(f"  {label}: {x}")
    for x in heads:
        lines.append(f"  頭の行と違う: {x}")
    return lines


def main(argv: Sequence[str] | None = None, *, freeze_text: str | None = None, pip_version: str | None = None,
         python_version: str | None = None, env: dict[str, str] | None = None) -> int:
    """入口。``freeze_text``・``pip_version``・``python_version``・``env`` は試験の口(無ければ今の環境から取る)。"""
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--lock", type=Path, default=LOCK, help="ロックのファイル(既定はリポの根の requirements-lock.txt)")
    ap.add_argument("--freeze", type=Path, default=None, help="pip freeze の出力のファイル(無ければこの python で回す)")
    a = ap.parse_args(argv)
    try:
        lock = parse_lock(a.lock.read_text(encoding="utf-8"))
        if freeze_text is None:
            freeze_text = a.freeze.read_text(encoding="utf-8") if a.freeze is not None else freeze_here()
    except (OSError, ValueError, RuntimeError) as e:
        print(f"誤り: {e}", file=sys.stderr)
        return EXIT_ERROR
    diff = compare(lock, parse_freeze(freeze_text), env=env)
    heads = head_checks(lock, pip_version=pip_version if pip_version is not None else pip_here(),
                        python_version=python_version if python_version is not None else platform.python_version())
    bad = render(diff, heads)
    status = "違う" if bad else "同じ"
    print(f"ロック {diff['n_lock']} 本(印で外れた {len(diff['not_here'])} 本: {', '.join(diff['not_here']) or 'なし'})"
          f"・入っている {diff['n_installed']} 本 → {status}")
    for line in bad:
        print(line)
    return EXIT_DIFF if bad else EXIT_SAME


if __name__ == "__main__":
    sys.exit(main())
