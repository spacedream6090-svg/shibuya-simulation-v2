"""core.paths — リポの根と包みの根を 1 か所で求める(移す段 2-2・計画 docs/reference/package-map-final-2026-11-09.md §7-3)。

ランの側(``build/`` の外)で ``Path(__file__)`` から根の道を求めるのは本モジュールだけ。段 4 で本モジュールを
``foundation/paths.py`` へ動かすときは、ここの深さだけを直せばよい(読み手は名で引く)。

- :data:`PACKAGE_ROOT` = 包みの根(``src/shibuya``)。:data:`REPO_ROOT` = リポの根(``src`` の親)。
- :func:`resolve_repo_path` = 相対の道筋はリポの根から、絶対の道筋はそのまま(作業ディレクトリに依らない)。
  ``engine.calendar`` から移した(経済と再開の口が暦を読まなくてよい)。
- :func:`find_upward` = 指定のディレクトリから上へ辿り、相対の道筋のファイルを含む最初のディレクトリ(予算の宣言表・
  知覚の契約書など。写しの木でも同じ探し方)。
- :func:`module_dir` = モジュールの名(``__name__``)→ そのファイルのあるディレクトリ(包みの頭 ``__init__`` には使わない)。

時間の方針: 本モジュールは時刻を持たない。逐次ループ宣言: なし(上へ辿るのはディレクトリの深さぶん)。
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

__all__ = ["PACKAGE_ROOT", "REPO_ROOT", "resolve_repo_path", "find_upward", "module_dir"]

#: 本ファイル(``src/shibuya/core/paths.py``)の実の道筋。
_HERE: Final[Path] = Path(__file__).resolve()
#: 包みの根(``src/shibuya``=本ファイルのディレクトリの 1 つ上)。
PACKAGE_ROOT: Final[Path] = _HERE.parents[1]
#: リポの根(``src`` の親=本ファイルから ``parents[3]``)。相対の道筋はここから解決する。
REPO_ROOT: Final[Path] = _HERE.parents[3]


def resolve_repo_path(path: str | Path) -> Path:
    """相対パスはリポの根から、絶対パスはそのまま(検収後 P4: 作業ディレクトリに依らない)。"""
    p = Path(path)
    return p if p.is_absolute() else REPO_ROOT / p


def module_dir(module_name: str) -> Path:
    """モジュールの名(``__name__``)→ そのファイルのあるディレクトリ(包みの根から名の部品をたどる)。"""
    return PACKAGE_ROOT.joinpath(*module_name.split(".")[1:-1])


def find_upward(relpath: str | Path, start: Path) -> Path:
    """``start`` から上へ辿り、``relpath`` のファイルを含む最初のディレクトリ(無ければ ``FileNotFoundError``)。"""
    for parent in (start, *start.parents):
        if (parent / relpath).is_file():
            return parent
    raise FileNotFoundError(f"{relpath} が見つからない({start} から上位を探索)")
