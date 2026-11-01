"""第 3 期 3-5: manifest の ``body``(持ち主・腕・予約の数・境目の数・一致の計器)と CLI の腕 ``--body-schedule``。

- 子の鍵は ``engine.body.model`` の ``CONFIG_KEYS``・``OBSERVED_KEYS`` の並び・``manifest_sections`` の混ざった辞書と同じ。
- 腕は組み立てで読む(環境変数・``set_arm``・``--body-schedule``)・設定の指紋に入れない(final は同じ)・既定と違えばランの
  種類は arm。manifest は final を変えない。
- 世界資産のラン(300 体・1 日・既定の腕): sweep と reserve で final・境目の列が同じ・体感温度の境目がある(世界資産の天気と
  日陰の表=予約の窓)。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from shibuya import cli
from shibuya.engine import body as B
from shibuya.engine import manifest_sections as MS
from shibuya.engine import run_kind as RK
from shibuya.engine.body import model as BM
from shibuya.engine.run import run_day

WORLD_DIR = Path("data/world/v2")
real_data = pytest.mark.requires_data("world_v2:w17_schedule.parquet")


@pytest.fixture(autouse=True)
def _arm_back():
    yield
    B.set_arm(B.DEFAULT_ARM)


def test_manifest_body_keys_and_sections(monkeypatch):
    kw = dict(n_agents=40, seed=1, n_cells=9, ticks=240, budget=40.0, checkpoint_every=60, vocab_version="v3")
    off = run_day(**kw).run_manifest_fields()["body"]
    # 〔3-5 検収 L6〕既定は段の境目の計器を数えない(欄は残し null)
    assert off["boundaries"] is None and off["boundary_digest"] is None and off["steps"] > 0
    monkeypatch.setenv(BM.GAUGE_ENV, "1")
    res = run_day(**kw)
    m = res.run_manifest_fields()
    assert res.final_hash == run_day(**kw).final_hash
    assert list(m)[-3:] == ["body", "calendar_shadow", "space"]  # 〔第 5 期 空間の段 1〕末尾に space  # 〔第 3 期 3-1 の取り込み〕その後ろ(末尾)に calendar_shadow
    body = m["body"]
    assert list(body) == list(BM.CONFIG_KEYS) + list(BM.OBSERVED_KEYS)
    assert body["owner"] == "body" and body["arm"] == "sweep" and body["arms"] == ["sweep", "reserve"]
    assert body["schema"] == BM.SCHEMA and len(body["rules"]) == 10 and len(body["system1"]) == 3
    assert {r["conf"] for r in body["rules"]} == {"mechanism", "expedient"}
    for k in BM.CONFIG_KEYS:
        assert MS.section_of(f"body.{k}") == MS.CONFIG, k
    for k in BM.OBSERVED_KEYS:
        assert MS.section_of(f"body.{k}") == MS.OBSERVED, k
    assert body["steps"] > 0 and body["boundaries"]["fatigue"] > 0 and len(body["boundary_digest"]) == 64
    assert body["reservations"] == 0 and body["pending"] == {"interoception": 0, "felt": 0}  # sweep は予約しない


def test_manifest_fields_without_a_layer_are_null():
    m = BM.manifest_fields(None)
    assert m["arm"] == "sweep" and all(m[k] is None for k in BM.OBSERVED_KEYS)


def test_arm_switch_reads_env_and_cli(monkeypatch):
    with pytest.raises(ValueError):
        B.set_arm("lazy")
    B.set_arm("reserve")
    assert B.arm() == "reserve" and B.BodyModel(3).arm == "reserve"
    B.set_arm("sweep")
    seen = {}
    monkeypatch.setattr(cli, "run", lambda **kw: (seen.update(arm=B.arm()), type("S", (), {
        "fleet_fields": {}, "summary": lambda self: ""})())[1])
    assert cli.main(["--world", "__no_such_dir__", "--body-schedule", "reserve"]) == 0
    assert seen["arm"] == "reserve"


def test_the_arm_is_not_in_the_fingerprint_and_marks_the_run_kind(monkeypatch):
    monkeypatch.setenv(BM.GAUGE_ENV, "1")
    kw = dict(n_agents=20, seed=1, world_dir=None, n_cells=9, ticks=60, checkpoint_every=30, vocab_version="v3")
    monkeypatch.delenv(RK.PYTEST_ENV, raising=False)
    a = cli.run(**kw)
    B.set_arm("reserve")
    b = cli.run(**kw)
    B.set_arm("sweep")
    assert (a.run_kind, b.run_kind) == ("reproduction", "arm")
    assert a.final_hash == b.final_hash
    ma, mb = a.run_manifest_fields(), b.run_manifest_fields()
    assert ma["body"]["boundary_digest"] == mb["body"]["boundary_digest"]
    assert (ma["body"]["arm"], mb["body"]["arm"]) == ("sweep", "reserve")


@real_data
def test_world_assets_reserve_equals_sweep_with_thermal_boundaries(monkeypatch):
    monkeypatch.setenv(BM.GAUGE_ENV, "1")
    kw = dict(n_agents=300, seed=1, world_dir=str(WORLD_DIR), vocab_version="v3", activity=True)
    a = cli.run(**kw)
    B.set_arm("reserve")
    b = cli.run(**kw)
    B.set_arm("sweep")
    ma, mb = a.run_manifest_fields()["body"], b.run_manifest_fields()["body"]
    assert a.final_hash == b.final_hash and int(a.llm_calls) == int(b.llm_calls)
    assert [(c.tick, c.behavior_hash, c.full_hash) for c in a.checkpoints] == \
           [(c.tick, c.behavior_hash, c.full_hash) for c in b.checkpoints]
    assert ma["boundary_digest"] == mb["boundary_digest"] and ma["boundaries"] == mb["boundaries"]
    assert ma["boundaries"]["thermal"] > 0 and mb["felt_tables"] >= 1
    assert mb["felt_evals"] < ma["felt_evals"] and mb["agent_evals"] < ma["agent_evals"]
