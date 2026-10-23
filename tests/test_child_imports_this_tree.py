# -*- coding: utf-8 -*-
"""試験が起こす子プロセスは、この木(rootdir)の ``src`` の ``shibuya`` を import する(第333・3-2-4)。

共有の venv は ``shibuya-sim`` を editable で入れていて、その ``.pth`` は本体の作業コピーの ``src`` を指す。
作業木や data の無い写しで試験を回すと、``subprocess.run([sys.executable, ...])`` の子が本体の ``src`` を読み、
**その木のコードを試していないのに通る**穴があった。ルートの ``tests/conftest.py`` が ``PYTHONPATH`` の先頭に
``<rootdir>/src`` を足すので、子も同じ ``src`` を読む。ここではそれを確かめる。
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import shibuya

ROOT = Path(__file__).resolve().parents[1]
SRC_PKG = ROOT / "src" / "shibuya"


def _norm(p: str | Path) -> str:
    return os.path.normcase(os.path.realpath(str(p)))


def test_this_process_imports_shibuya_from_this_tree():
    assert _norm(Path(shibuya.__file__).parent) == _norm(SRC_PKG), shibuya.__file__


def test_child_process_imports_shibuya_from_this_tree(tmp_path):
    code = "import shibuya, sys; sys.stdout.write(shibuya.__file__)"
    # cwd は木の外(子の sys.path の先頭=cwd に頼らず、PYTHONPATH だけで決まることを見る)
    r = subprocess.run([sys.executable, "-c", code], cwd=str(tmp_path), capture_output=True, text=True,
                       encoding="utf-8", timeout=120)
    assert r.returncode == 0, r.stderr[-2000:]
    child = Path(r.stdout.strip())
    assert _norm(child.parent) == _norm(SRC_PKG), (
        f"子が別の木の shibuya を読んだ: {child}(期待={SRC_PKG})")
