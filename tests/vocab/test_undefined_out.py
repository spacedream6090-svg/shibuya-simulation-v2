"""``python -m shibuya.cli --undefined-out PATH``(D-71 段2 バッチの入力口)の検査。

規律: **既定経路のバイト不変**(渡さなければ 1 バイトも書かない・checkpoint 列が動かない)。
裁定はランの中では起こさない(語彙成長の設計 v0 §2「run.py への注入口は作らない」)。
"""

from __future__ import annotations

import json

from shibuya import cli
from shibuya.llm import UndefinedActionRegistry
from shibuya.llm.undefined import SYNONYM_TABLE_VERSION

_BASE = ["--agents", "100", "--seed", "1", "--world", "__no_such_dir__", "--cells", "9"]


def test_default_run_does_not_write_the_undefined_ledger(tmp_path, capsys):
    """既定は**書かない**(``--census-out`` と同じ作法)。"""
    assert cli.main([*_BASE, "--ticks", "10"]) == 0
    assert "未定義台帳" not in capsys.readouterr().out
    assert list(tmp_path.iterdir()) == []


def test_undefined_out_writes_the_batch_input(tmp_path, capsys):
    """渡すと JSON が出る。版・記録リング・集計・カウンタが揃う。"""
    out = tmp_path / "undef.json"
    assert cli.main([*_BASE, "--ticks", "30", "--undefined-out", str(out)]) == 0
    assert "未定義台帳 JSON undef.json" in capsys.readouterr().out
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["schema"] == cli.UNDEFINED_PAYLOAD_SCHEMA
    assert doc["source"] == "run_day"
    assert doc["versions"]["synonym_table"] == SYNONYM_TABLE_VERSION
    assert doc["threshold_agents"] == 10
    assert doc["cell_source"] == "unavailable"  # 台帳はセルを持たない(推測で埋めない)
    assert set(doc) >= {"counters", "dropped", "summary", "records", "words"}
    assert "undefined_records" in doc["counters"]
    assert str(tmp_path) not in json.dumps(doc, ensure_ascii=False)  # 絶対パスを書かない


def test_undefined_out_does_not_move_the_checkpoint_series(tmp_path):
    """**既定経路のバイト不変**: ``--undefined-out`` を足しても checkpoint 列は同じ。"""
    docs = []
    for name, extra in (("a", []), ("b", ["--undefined-out", str(tmp_path / "u.json")])):
        ck = tmp_path / f"{name}.json"
        assert cli.main([
            *_BASE, "--ticks", "20", "--checkpoint-every", "10",
            "--checkpoints-out", str(ck), *extra,
        ]) == 0
        docs.append(json.loads(ck.read_text(encoding="utf-8")))
    assert [c["combined"] for c in docs[0]["checkpoints"]] == [
        c["combined"] for c in docs[1]["checkpoints"]
    ]
    assert docs[0]["final_hash"] == docs[1]["final_hash"]
    assert (tmp_path / "u.json").exists()


def test_payload_is_a_pure_function_of_the_registry():
    """``undefined_registry_payload`` は台帳だけから決まる純関数(集計の式を固定する)。"""
    reg = UndefinedActionRegistry(adjudicator=None)
    for i in range(3):
        reg.observe("ほげ", agent_id=i, tick=i * 60 + 5, context_hash="h")
    reg.observe("ほげ", agent_id=0, tick=5, context_hash="h")  # 同じ体・同じ時間帯
    reg.observe("ふが", agent_id=9, tick=700)
    cells = {(0, 5): "c0", (1, 65): "c1", (2, 125): "c0"}

    doc = cli.undefined_registry_payload(reg, source="unit", cells=cells)
    hoge = doc["words"]["ほげ"]
    assert hoge["n_rows"] == 4 and hoge["distinct_agents"] == 3
    assert hoge["distinct_cells"] == 2 and hoge["distinct_hours"] == 3
    assert hoge["first_tick"] == 5 and len(hoge["samples"]) == 3
    assert doc["cell_source"] == "prompt_block"
    assert doc["summary"]["n_records_kept"] == 5 and doc["summary"]["ring_truncated"] is False
    assert doc["records"][0]["stage"] == 1
    assert doc["records"][0]["word"] == doc["records"][0]["raw"] == "ほげ"
    assert doc["records"][-1]["cell"] is None  # 渡されなかった (体, tick) は埋めない
    assert list(doc["words"]) == ["ほげ", "ふが"]  # 行数の多い順


def test_payload_without_a_registry_is_empty_not_guessed():
    """台帳の無いラン(スタブ)は**空で返す**(推測で埋めない)。"""
    doc = cli.undefined_registry_payload(None, source="none")
    assert doc["records"] == [] and doc["words"] == {} and doc["counters"] == {}
    assert doc["threshold_agents"] == 10
