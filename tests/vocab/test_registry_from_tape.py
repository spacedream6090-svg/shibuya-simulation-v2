"""``tools/vocab/registry_from_tape.py``(テープ → 未定義台帳 JSON)の検査。

実テープ(``data/tape/c8_ab7_s1/…``)が無い環境では実データの検査だけ飛ばす。
"""

from __future__ import annotations

import json

import pytest

from shibuya.cli import UNDEFINED_PAYLOAD_SCHEMA

from .conftest import TAPE_S1, real_tape


def test_cell_regex_reads_the_b2_place_block(registry_from_tape):
    """セル ID の抽出は [B2 場所] の文面に依る(**取れなければ 0 件**・別の値にはならない)。"""
    rx = registry_from_tape.PLACE_RE
    assert rx.search("[B2 場所] 現在地はセルg-9_-4_GL(地上)です。").group(1) == "g-9_-4_GL"
    assert rx.search("[B3 時刻] 現在時刻は19時55分です。") is None


@real_tape
def test_ab7_seed1_open_matches_the_parent_report(registry_from_tape):
    """AB7 seed 1 open のテープから台帳を再構成すると、親報告 §1 の値に一致する。

    親報告 ``docs/bench/c8/ablation/ab7_s1_parent_report.md`` §1:
    M2 未定義 **603 行・26 語**/ 食事 328 行・309 体 / 行動 90・90 / 近づく 49・45 /
    見る 33・31 / 近寄る 30・29 / 進む 10・10。
    """
    doc = registry_from_tape.payload_from_tape(TAPE_S1, tag="ab7_s1_open")
    assert doc["schema"] == UNDEFINED_PAYLOAD_SCHEMA
    assert doc["source"] == "tape"
    assert doc["summary"]["n_records_kept"] == 603
    assert doc["summary"]["n_words"] == 26
    words = doc["words"]
    assert (words["食事"]["n_rows"], words["食事"]["distinct_agents"]) == (328, 309)
    assert (words["行動"]["n_rows"], words["行動"]["distinct_agents"]) == (90, 90)
    assert (words["近づく"]["n_rows"], words["近づく"]["distinct_agents"]) == (49, 45)
    assert (words["見る"]["n_rows"], words["見る"]["distinct_agents"]) == (33, 31)
    assert (words["近寄る"]["n_rows"], words["近寄る"]["distinct_agents"]) == (30, 29)
    assert (words["進む"]["n_rows"], words["進む"]["distinct_agents"]) == (10, 10)
    # 被覆の 3 つ目の軸(セル)はテープの共有ブロックからしか作れない
    assert doc["cell_source"] == "prompt_block"
    assert words["食事"]["distinct_cells"] > 1 and words["食事"]["distinct_hours"] > 1
    assert doc["tape"]["dir"].startswith("data/tape/")  # 相対パスのみ


@real_tape
def test_main_writes_a_relative_path_json(registry_from_tape, tmp_path, capsys):
    out = tmp_path / "reg.json"
    assert registry_from_tape.main([str(TAPE_S1), "--out", str(out), "--tag", "t"]) == 0
    assert "reg.json" in capsys.readouterr().out
    text = out.read_text(encoding="utf-8")
    assert str(tmp_path) not in text
    doc = json.loads(text)
    assert doc["tape"]["tag"] == "t"
    assert doc["tape"]["scan"]["rows"] == 36_868


def test_relative_keeps_outside_paths_as_a_bare_name(registry_from_tape, tmp_path):
    """リポジトリ外のパスは**名前だけ**にする(絶対パスを記録に残さない)。"""
    assert registry_from_tape._relative(tmp_path / "x.json") == "x.json"


@pytest.mark.parametrize("missing", ["calls.parquet"])
def test_missing_tape_is_an_error_not_an_empty_ledger(registry_from_tape, tmp_path, missing):
    with pytest.raises(FileNotFoundError):
        registry_from_tape.payload_from_tape(tmp_path)
