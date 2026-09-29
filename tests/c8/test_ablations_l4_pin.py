"""第290(3 段目の問い Q29): 上限ありで回した凍結腕は ``l4_scale: 1.0`` を明示して旧構成で回る。

3 段目(第289・D-99 (a′)・D-110)で ``cli.run`` の既定が呼数無制限(``l4_scale=0``)になった。
腕定義表 ``tools/c8/ablations_v1.json`` の AB1〜AB7c・AB6b は上限あり(L4 按分+持ち越し 2 tick)で回した
記録なので、各ランの kwargs に ``l4_scale: 1.0`` を足した(表のトップ ``l4_scale_pin``)。無制限の版は
AB6c・AB7d・AB1b(``l4_scale: 0.0``)・AB8 は倍率の腕。
"""

from __future__ import annotations

import pytest

from shibuya.engine.arbiter import call_budget_per_tick

PINNED = [
    "AB1-BUDGET-MODE", "AB2-PNOTICE-D50", "AB3-REFRACTORY-PROX", "AB6-AD-ZERO",
    "AB7-OPEN-INTENT", "AB7b-HINT-INTENT", "AB7c-VOCAB-V2", "AB6b-AD-NOTICE",
]
UNCAPPED = ["AB6c-AD-NOTICE-UNCAPPED", "AB7d-VOCAB-UNCAPPED", "AB1b-BUDGET-MODE-UNCAPPED"]


@pytest.fixture(scope="module")
def table(c8lib):
    return c8lib.load_ablations()


def test_every_run_states_its_l4_scale(table):
    """ランの無い腕(AB4・AB5=未実装)を除き、全ランが ``l4_scale`` を明示している。"""
    for arm in table["arms"]:
        for run in arm.get("runs") or []:
            assert "l4_scale" in run["kwargs"], (arm["id"], run["tag"])


def test_the_capped_arms_are_pinned_to_the_old_budget(table):
    pin = table["l4_scale_pin"]
    assert pin["arms"] == PINNED and "第290" in pin["since"]
    by_id = {a["id"]: a for a in table["arms"]}
    for aid in PINNED:
        assert {r["kwargs"]["l4_scale"] for r in by_id[aid]["runs"]} == {1.0}, aid
    for aid in UNCAPPED:
        assert {r["kwargs"]["l4_scale"] for r in by_id[aid]["runs"]} == {0.0}, aid


def test_a_pinned_arm_reruns_with_the_old_capped_budget(ablation_runner, table, tmp_path):
    """回し直しても旧構成(上限あり=L4 按分)で回る=``budget_per_tick`` が按分値・倍率 1.0。"""
    arm = dict(ablation_runner.arm_by_id(table, "AB6-AD-ZERO"))
    out = ablation_runner.execute_arm(
        arm, agents=16, ticks=2, seed=1, world_dir=None,
        out_dir=tmp_path, fleet=None, tape_root=tmp_path / "t",
    )
    fields = [r["run_manifest_fields"] for r in out["runs"]]
    assert len(fields) == 2
    for f in fields:
        assert f["l4_scale"] == 1.0
        assert f["budget_per_tick"] == pytest.approx(call_budget_per_tick(16))
