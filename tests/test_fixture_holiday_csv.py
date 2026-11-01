# -*- coding: utf-8 -*-
"""祝日の fixture(``tests/fixtures/calendar/syukujitsu.csv``)が内閣府の CSV のバイトのままであること(第333)。

git の改行の変換などで 1 バイトでも変わると md5 が変わる(``.gitattributes`` で ``binary``)。値は
``tests/fixtures/README.md`` の表と同じ。
"""

from __future__ import annotations

import hashlib
from pathlib import Path

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "calendar" / "syukujitsu.csv"
MD5 = "733fabb6b488794a0cd3d94df4b1f24a"
SIZE = 21_538


def test_holiday_fixture_is_byte_identical_to_the_cabinet_office_csv():
    raw = FIXTURE.read_bytes()
    assert len(raw) == SIZE
    assert hashlib.md5(raw).hexdigest() == MD5
    assert raw.count(b"\r\n") == raw.count(b"\n")  # CRLF のまま
