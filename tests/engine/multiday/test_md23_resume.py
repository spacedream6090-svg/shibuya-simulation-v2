"""第 2 期 2-3: 複数日のランの日の境目で保存 → 翌日を再開=通しと同じ(10d の再開を複数日の腕の組で)。

- 合成の世界(data 無し・80 体・2 日): 既定の腕と腕 a(``--memory-store events``)。腕 a は器の目印(記録の出来事)が
  状態台帳の腕の行 ``M0L`` から戻る=再開の後のテープの目印の列が通しと同じ。前の日の出来事は再開のランの記録に無い
  (記録は discardable)=目印の先が記録に無い行は計器 ``targets_log_gone`` に出る(宣言)。
- 世界資産(300 体・2 日・data あり): 既定の腕と腕 d(a+b+c=``--memory-store events``・``--proximity distance``・
  ``--economy-stage2 on``)。5,000 体の 2 日は記録の道具(md23/README.md)。
"""

from __future__ import annotations

import pytest

from shibuya.core.time_consts import STEPS_PER_DAY
from shibuya.engine.run import run_day
from shibuya.engine.tape import Tape

from tests.engine.multiday._md import KW, WORLD, arms, tool

TPD = int(STEPS_PER_DAY)


def _cp(r):
    return [(int(c.tick), c.behavior_hash, c.full_hash) for c in r.checkpoints if int(c.tick) >= TPD]


def _col(path, name):
    t = Tape(path)
    rows = zip(t.column("tick"), t.column("agent_id"), t.column("wake_class"), t.column(name))
    return sorted((int(x), int(y), int(z), tuple(v)) for x, y, z, v in rows if int(x) >= TPD)


@pytest.mark.parametrize("arm", ["mem", "events"])
def test_synthetic_two_days_resume_at_the_day_boundary(tmp_path, arm):
    kw = dict(KW, ticks=TPD, sim_days=2, checkpoint_every=60)
    with arms(memory_store=arm):
        straight = run_day(tape_path=tmp_path / "s", **kw)
        a = run_day(state_out=tmp_path / "state", stop_at_tick=TPD, tape_path=tmp_path / "a", **kw)
        b = run_day(resume_from=tmp_path / "state" / a.resume["state_files"][-1]["file"], tape_path=tmp_path / "b",
                    **kw)
    assert int(a.resume["state_files"][-1]["file"].split("T")[-1].split(".")[0]) == TPD
    assert b.final_hash == straight.final_hash and _cp(b) == _cp(straight) and _cp(b)
    if arm == "events":
        assert _col(tmp_path / "b", "recalled_event_ids") == _col(tmp_path / "s", "recalled_event_ids")
        assert any(v for *_k, v in _col(tmp_path / "b", "recalled_event_ids"))
        sb, ss = b.memory_summary["memory_store"], straight.memory_summary["memory_store"]
        assert sb["origins"] == ss["origins"] and sb["origins"]["legacy"] == 0
        assert ss["targets_log_gone"] == 0 and sb["targets_log_gone"] > 0  # 前の日の出来事は再開のランの記録に無い


@pytest.mark.requires_data("world_v2:w17_schedule.parquet")
@pytest.mark.parametrize("config", ["default", "d"])
def test_world_two_days_resume_default_and_arm_d(tmp_path, config):
    md = tool()
    md.set_arms(config)
    try:
        from shibuya import cli

        kw = dict(md.BASE, n_agents=300, seed=1, sim_days=2, world_dir=str(WORLD))
        straight = cli.run(**kw)
        a = cli.run(**kw, state_out=str(tmp_path / "a"), stop_at_tick=TPD)
        b = cli.run(**kw, resume_from=str(tmp_path / "a" / a.resume["state_files"][-1]["file"]))
    finally:
        md.set_arms("default")
    assert b.final_hash == straight.final_hash and _cp(b) == _cp(straight) and _cp(b)
    if config == "d":
        man = b.run_manifest_fields()
        assert man["memory_summary"]["memory_store"]["origins"]["legacy"] == 0
        assert man["economy"].get("stage2") is not None
