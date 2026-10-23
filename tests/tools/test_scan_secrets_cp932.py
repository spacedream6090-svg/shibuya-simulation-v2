# -*- coding: utf-8 -*-
"""第333(検収 L8): 秘密スキャンは cp932 のファイル(祝日の fixture)を文字化けで偽陽性にしない。"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCAN = ROOT / "tools" / "scan_secrets.py"
FIXTURE = ROOT / "tests" / "fixtures" / "calendar" / "syukujitsu.csv"


def _scan(*paths: Path) -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(SCAN), *map(str, paths)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=str(ROOT), timeout=120)
    return r.returncode, r.stdout + r.stderr


def test_cp932_fixture_is_clean():
    rc, out = _scan(FIXTURE)
    assert rc == 0 and "CLEAN" in out, out[-500:]


def test_cp932_file_is_decoded_not_replaced(tmp_path):
    p = tmp_path / "x.csv"
    p.write_bytes("国民の祝日・休日月日,国民の祝日・休日名称\r\n2026/1/1,元日\r\n".encode("cp932"))
    rc, out = _scan(p)
    assert rc == 0 and "CLEAN" in out, out[-500:]
