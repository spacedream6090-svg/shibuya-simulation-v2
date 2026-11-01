"""第340 段 2 の 6: 「無いと宣言」の一覧の計器(tools/instruments/absent_declarations.py)。

- 出力は決定論(2 回出して同じ)・宣言の数(主体が居ない 8・入力/初期の予定 2・口が無い 13・率を外す 2+補足 1・入力 13)。
- 回答 11-01 §10-3 の過程と判断がすべて載る。指紋は宣言を変えると変わる(版上げの前後で比べる用)。
- 記録 docs/bench/analysis/s2-ledger-1101/absent_declarations.md はいまの出力と同じ。
"""

from __future__ import annotations

import dataclasses
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_PATH = ROOT / "tools" / "instruments" / "absent_declarations.py"
RECORD = ROOT / "docs" / "bench" / "analysis" / "s2-ledger-1101" / "absent_declarations.md"


@pytest.fixture(scope="module")
def gauge():
    spec = importlib.util.spec_from_file_location("absent_declarations", _PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_render_is_deterministic_and_lists_every_declaration(gauge):
    a, b = gauge.render(), gauge.render()
    assert a == b
    for subject in ("ごみ収集", "街路の清掃", "道路工事", "救急と警察の出動", "催しの人の注入", "採用と解雇",
                    "電気と水の負荷", "宅配", "納品", "発注"):
        assert f"| {subject} |" in a, subject
    for subject in ("電車を見送る", "品と数を選ぶ", "値段を見て見送る", "3 人目として加わる", "予定を考え直す", "家で食べる",
                    "よく考える", "ひと言", "1 日の振り返り", "予想と違って直す", "接客", "値段を変える", "倒れる"):
        assert f"| {subject} |" in a, subject
    assert "主体が居ない過程 8・入力/初期の予定 2・口が無い判断 13・率を外すもの 2(+補足 1)=宣言 26" in a
    assert "止めた=循環の検査の例外になる)20・まだ動く 6" in a  # 率の規則(ce52662)の後
    for subject in ("ポイ捨て", "売れ残りの廃棄"):
        assert f"| {subject} |" in a, subject
    assert "入力の宣言 13(埋めた 5・欄だけ 8)" in a


def test_fingerprint_moves_when_a_declaration_changes(gauge, monkeypatch):
    before = gauge.fingerprint()
    ab = gauge.AB
    changed = (dataclasses.replace(ab.NO_ACTOR[0], remove_at="x"),) + ab.NO_ACTOR[1:]
    monkeypatch.setattr(ab, "ABSENCES", changed + ab.REPLACED + ab.NO_PORT + ab.RATE_REMOVED + ab.NO_PORT_EXTRA)
    assert gauge.fingerprint() != before


def test_record_matches_the_current_output(gauge, tmp_path):
    out = tmp_path / "a.md"
    assert gauge.main(["--out", str(out)]) == 0
    assert out.read_bytes() == RECORD.read_bytes(), "記録を出し直す: python tools/instruments/absent_declarations.py --out …"
