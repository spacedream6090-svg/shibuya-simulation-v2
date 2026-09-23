# -*- coding: utf-8 -*-
"""tests 共通(ルート)。

層2(第137)の指摘: cp932 端末(PYTHONUTF8 なしの Windows)では ``capsys.disabled()`` 下の
``print`` が「≤」「m²」で ``UnicodeEncodeError`` を出し、assert に達する前に偽赤になる
(tests/engine/test_processes_run.py・tests/perception/test_b4_detector_gap.py)。
``capsys.disabled()`` は pytest の捕捉を外して**元の端末ストリーム**(``sys.__stdout__``)へ
書くので、そちらも UTF-8 に揃える(CI の Linux では元から UTF-8=無害)。
第137 の初版は ``sys.stdout``(=捕捉ストリーム)だけを直していて効かなかった(第137b で訂正)。
"""

from __future__ import annotations

import sys

for _stream in (sys.stdout, sys.stderr, sys.__stdout__, sys.__stderr__):
    try:
        _stream.reconfigure(encoding="utf-8", errors="backslashreplace")  # type: ignore[union-attr]
    except Exception:  # pragma: no cover - reconfigure の無いストリーム(capture 中など)
        pass
