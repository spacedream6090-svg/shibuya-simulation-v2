# -*- coding: utf-8 -*-
"""tests 共通(ルート)。

層2(第137)の指摘: cp932 端末(PYTHONUTF8 なしの Windows)では ``capsys.disabled()`` 下の
``print`` が「≤」「m²」で ``UnicodeEncodeError`` を出し、assert に達する前に偽赤になる
(tests/engine/test_processes_run.py・tests/perception/test_b4_detector_gap.py)。
``capsys.disabled()`` は pytest の捕捉を外して**元の端末ストリーム**(``sys.__stdout__``)へ
書くので、そちらも UTF-8 に揃える(CI の Linux では元から UTF-8=無害)。
第137 の初版は ``sys.stdout``(=捕捉ストリーム)だけを直していて効かなかった(第137b で訂正)。

第333(3-2-4 取り出したばかりの状態での試験)で足したもの:

1. 祝日の CSV: ``data/calendar/syukujitsu.csv`` が無ければ ``tests/fixtures/calendar/syukujitsu.csv``
   (内閣府の CSV を 1 バイトも変えずに複製したもの・出典は ``tests/fixtures/README.md``)をそこへ複製する。
   既にあれば触らない。``data/`` は gitignore のまま。
2. 子プロセスの import 先: 環境変数 ``PYTHONPATH`` の先頭にこのリポの ``src`` を足す。共有の venv の editable
   install は本体の作業コピーを指すので、作業木や写しで回すと ``subprocess`` の子が本体の ``src`` を読む穴があった。
3. data が要る試験の印 ``requires_data(<id>, ...)``(登録表は ``tests/_data_ids.py``): 無ければ一律の理由で飛ばし、
   id ごとの飛ばした数を要約に出す(合否にしない。``GITHUB_STEP_SUMMARY`` があれば Markdown でも書く)。
"""

from __future__ import annotations

import os
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

import pytest

for _stream in (sys.stdout, sys.stderr, sys.__stdout__, sys.__stderr__):
    try:
        _stream.reconfigure(encoding="utf-8", errors="backslashreplace")  # type: ignore[union-attr]
    except Exception:  # pragma: no cover - reconfigure の無いストリーム(capture 中など)
        pass

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
HOLIDAY_CSV = ROOT / "data" / "calendar" / "syukujitsu.csv"
HOLIDAY_FIXTURE = ROOT / "tests" / "fixtures" / "calendar" / "syukujitsu.csv"


def _same_path(a: str, b: Path) -> bool:
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(str(b)))


def _prepend_src_to_pythonpath() -> None:
    """``PYTHONPATH`` の先頭に ``<rootdir>/src``(既に先頭なら何もしない)。"""
    parts = [p for p in os.environ.get("PYTHONPATH", "").split(os.pathsep) if p]
    if parts and _same_path(parts[0], SRC):
        return
    os.environ["PYTHONPATH"] = os.pathsep.join([str(SRC), *parts])


def _ensure_holiday_csv() -> None:
    """``data/calendar/syukujitsu.csv`` が無ければ fixture を複製する(あれば触らない)。"""
    if HOLIDAY_CSV.exists() or not HOLIDAY_FIXTURE.is_file():
        return
    HOLIDAY_CSV.parent.mkdir(parents=True, exist_ok=True)
    tmp = HOLIDAY_CSV.with_name(f".{HOLIDAY_CSV.name}.{os.getpid()}.tmp")
    shutil.copyfile(HOLIDAY_FIXTURE, tmp)
    try:
        if HOLIDAY_CSV.exists():  # 並べた別のプロセスが先に置いた
            return
        os.replace(tmp, HOLIDAY_CSV)
    finally:
        if tmp.exists():
            tmp.unlink()
    print("[tests/conftest] data/calendar/syukujitsu.csv が無いので fixture から複製した"
          "(tests/fixtures/calendar/syukujitsu.csv)", file=sys.stderr)


_prepend_src_to_pythonpath()
_ensure_holiday_csv()

from tests import _data_ids as D  # noqa: E402  (PYTHONPATH と祝日の表を整えた後)

_REASON_RE = re.compile(rf"{D.PREFIX}: (\S+) が無い")


def pytest_collection_modifyitems(session, config, items):
    """印 ``requires_data(<id>, ...)`` の id が 1 つでも無ければ、一律の理由で飛ばす。"""
    for item in items:
        ids: list[str] = []
        for mark in item.iter_markers(name="requires_data"):
            if not mark.args:
                raise pytest.UsageError(f"{item.nodeid}: requires_data に id が無い")
            ids.extend(str(a) for a in mark.args)
        if not ids:
            continue
        try:
            miss = D.first_missing(ids)
        except ValueError as e:
            raise pytest.UsageError(f"{item.nodeid}: {e}") from None
        if miss is not None:
            item.add_marker(pytest.mark.skip(reason=D.reason(miss)))


def _skip_reason(rep) -> str:
    lr = getattr(rep, "longrepr", None)
    if isinstance(lr, tuple) and len(lr) == 3:
        return str(lr[2])
    return str(lr or "")


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """id ごとの飛ばした数の表(合否にしない)。"""
    counts: Counter[str] = Counter()
    other = 0
    for rep in terminalreporter.stats.get("skipped", []):
        m = _REASON_RE.search(_skip_reason(rep))
        if m:
            counts[m.group(1)] += 1
        else:
            other += 1
    total = sum(counts.values())
    rows = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    tr = terminalreporter
    tr.write_sep("-", f"requires_data: data が無くて飛ばした試験 {total} 件(id {len(rows)} 種・合否にしない)")
    for data_id, n in rows:
        tr.write_line(f"  {n:5d}  {data_id}")
    tr.write_line(f"  data 以外の理由で飛ばした試験 {other} 件")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary and not hasattr(config, "workerinput"):
        lines = [
            f"### requires_data: data が無くて飛ばした試験 {total} 件(合否にしない)",
            "",
            "| id | 飛ばした数 |",
            "|---|---:|",
            *[f"| `{data_id}` | {n} |" for data_id, n in rows],
            "",
            f"data 以外の理由で飛ばした試験: {other} 件",
            "",
        ]
        try:
            with open(summary, "a", encoding="utf-8") as fh:
                fh.write("\n".join(lines) + "\n")
        except OSError as e:  # pragma: no cover - 要約が書けなくても試験の結果は変えない
            tr.write_line(f"  (GITHUB_STEP_SUMMARY に書けなかった: {e})")
