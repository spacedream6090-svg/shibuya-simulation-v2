# -*- coding: utf-8 -*-
"""tests 共通(ルート)。

層2(第137)の指摘: cp932 端末(PYTHONUTF8 なしの Windows)では ``capsys.disabled()`` 下の
``print`` が「≤」「m²」で ``UnicodeEncodeError`` を出し、assert に達する前に偽赤になる
(tests/engine/test_processes_run.py・tests/perception/test_b4_detector_gap.py)。
標準出力/標準エラーを UTF-8 に揃えて環境要因を消す(CI の Linux では元から UTF-8=無害)。
"""

from __future__ import annotations

import sys

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="backslashreplace")  # type: ignore[union-attr]
    except Exception:  # pragma: no cover - reconfigure の無いストリーム(capture 中など)
        pass
