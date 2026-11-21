"""第347(Q13): 語彙を渡さずに回した腕は ``vocab_version: "v1"`` を明示して旧構成で回る(第290 の ``l4_scale_pin`` と同じ形)。

Q13(返事その 8 §1-2)で ``run_day``・``cli.run`` の語彙の既定が v1 から v3 になった(CLI の既定にそろえた)。腕定義表
``tools/c8/ablations_v1.json`` の腕のうち、ランの kwargs に語彙の無かった 10 腕は語彙 v1(旧の既定)で回した記録なので、各ランに
``vocab_version: "v1"`` を足した(表のトップ ``vocab_version_pin``)。空腹のモデル(``cli.run`` の既定 energy)と倍率(全ランが
明示=``test_ablations_l4_pin.py``)は前後で同じ=腕のランの中身は前と同じ。記録 ``docs/bench/analysis/library-defaults-q13-347/``。
"""

from __future__ import annotations

import pytest

PINNED = [
    "AB1-BUDGET-MODE", "AB2-PNOTICE-D50", "AB3-REFRACTORY-PROX", "AB6-AD-ZERO", "AB7-OPEN-INTENT", "AB7b-HINT-INTENT",
    "AB6b-AD-NOTICE", "AB8-L4-SCALE", "AB6c-AD-NOTICE-UNCAPPED", "AB1b-BUDGET-MODE-UNCAPPED",
]


@pytest.fixture(scope="module")
def table(c8lib):
    return c8lib.load_ablations()


def test_every_run_states_its_vocab_version(table):
    """ランの無い腕(AB4・AB5=未実装)を除き、全ランが ``vocab_version`` を明示している(既定に頼らない)。"""
    for arm in table["arms"]:
        for run in arm.get("runs") or []:
            assert "vocab_version" in run["kwargs"], (arm["id"], run["tag"])


def test_the_arms_without_a_vocab_are_pinned_to_the_old_default(table):
    pin = table["vocab_version_pin"]
    assert pin["arms"] == PINNED and "第347" in pin["since"]
    by_id = {a["id"]: a for a in table["arms"]}
    for aid in PINNED:
        assert {r["kwargs"]["vocab_version"] for r in by_id[aid]["runs"]} == {"v1"}, aid


def test_a_pinned_open_intent_arm_reruns_with_the_old_vocab(ablation_runner, table, tmp_path):
    """回し直しても旧構成(語彙 v1)で回る=open の腕は語彙 v3 の既定では止まる組だが、明示した v1 で回る。"""
    arm = dict(ablation_runner.arm_by_id(table, "AB7-OPEN-INTENT"))
    out = ablation_runner.execute_arm(
        arm, agents=16, ticks=2, seed=1, world_dir=None,
        out_dir=tmp_path, fleet=None, tape_root=tmp_path / "t",
    )
    fields = [r["run_manifest_fields"] for r in out["runs"]]
    assert [f["vocab_version"] for f in fields] == ["v1", "v1"]
    assert [f["intent_mode"] for f in fields] == ["vocab", "open"]
