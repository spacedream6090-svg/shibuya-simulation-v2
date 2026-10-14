"""第 1 期 1-5(口の約束 1-5 の約束 (3)): 権利台帳の行数と種類の分布を manifest に出す(計器)。

- 一番上の鍵の末尾に ``rights``(凍結の表 ``tests/engine/time/manifest_keys_frozen.json``)・節は観測。
- 中身=権利台帳の ``tally()``+空欄のつなぎの台帳の行+許可のない行動の数(開閉=開閉の過程の数え・役割語=判断の口の
  数え)。世界過程の無いランは ``None``。
- 記録だけ: 権利台帳を作らない形に差し替えても final と呼数は同じ(manifest は状態に入らない)。
- 再開(rebuild_derived)で作り直した台帳も同じ中身。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from shibuya.core.time_consts import STEPS_PER_DAY
from shibuya.engine import manifest_sections as MS
from shibuya.engine.rights import initial as RI
from shibuya.engine.run import run_day

HERE = Path(__file__).resolve().parent
TOP = json.loads((HERE.parent / "time" / "manifest_keys_frozen.json").read_text(encoding="utf-8"))["keys"]
KW = dict(n_agents=60, seed=3, n_cells=9, ticks=STEPS_PER_DAY // 4, budget=60.0, vocab_version="v3",
          checkpoint_every=120)


@pytest.fixture(scope="module")
def res():
    return run_day(**KW)


def test_rights_is_the_last_key_and_observed(res):
    keys = list(res.run_manifest_fields())
    # 〔第 1 期 1-8 J0 の取り込み〕1-8 の decision_port が rights の後ろに入った・〔第 1 期 1-7〕その後ろに tools・
    # 〔第 1 期 1-8b〕その後ろに speech_port・〔第 2 期 2-2 段 11a〕その後ろに proximity・〔第 3 期 3-3〕その後ろ(末尾)に
    # experiment・〔第 3 期 3-2〕その後ろに batching・〔第 3 期 3-5〕その後ろ(末尾)に body(試験の名は履歴のまま)
    assert keys == TOP and keys[-8:] == ["rights", "decision_port", "tools", "speech_port", "proximity", "experiment",
                                         "batching", "body"]
    assert MS.section_of("rights") == MS.OBSERVED and MS.section_of("rights.by_kind") == MS.OBSERVED


def test_values_come_from_the_ledger(res):
    m = res.run_manifest_fields()["rights"]
    led = res.runner.rights
    c = led.tally()
    assert {k: m[k] for k in c} == c
    assert m["rows"] == len(led) > 0
    assert set(m["by_kind"]) == {"own", "lease", "employ", "licence"}
    assert m["by_kind"]["licence"] == 0 and m["by_object_kind"]["dwelling"] == 0   # 空欄の 2 つ
    assert m["by_kind"]["lease"] == res.runner.world.n_poi
    assert m["blank_bridges"] == dict(RI.BLANK_BRIDGES)
    assert m["unauthorized"] == {"open_close": 0, "role_action_unauthorized": 0, "role_action_unjudged": 0}
    json.dumps(m)  # JSON に書ける


def test_no_world_processes_means_none():
    r = run_day(**{**KW, "processes": False, "ticks": 30})
    assert r.run_manifest_fields()["rights"] is None


def test_the_record_does_not_move_the_result(res, monkeypatch):
    """権利台帳の中身を空にしても(担当の表は同じに読む)final と呼数は同じ=manifest の欄は記録だけ。"""
    from shibuya.engine.processes import opening as OP

    real = OP.OpeningProcess._build_rights

    def only_staff(self):  # noqa: ANN001  雇用(W16)と賃借の行を作らない台帳
        from shibuya.engine.rights import ledger as L

        full = real(self)
        led = L.Rights()
        for r in full:
            if r.source == RI.SOURCE_STAFF:
                led.grant(r)
        return led

    monkeypatch.setattr(OP.OpeningProcess, "_build_rights", only_staff)
    other = run_day(**KW)
    assert other.final_hash == res.final_hash and other.llm_calls == res.llm_calls
    assert other.run_manifest_fields()["rights"]["rows"] < res.run_manifest_fields()["rights"]["rows"]


def test_rebuild_gives_the_same_ledger(res):
    op = res.runner.opening
    before = list(op.rights)
    arr = op.staff_of_poi
    op.rebuild_derived()
    assert list(op.rights) == before and op.staff_of_poi is arr
    assert res.runner.rights is op.rights
