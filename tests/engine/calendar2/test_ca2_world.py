"""第 6 期 6-2 カレンダー 2 腕 arm(mock 5,000 体・1 日・世界の資産)の試験(slow・data が要る)。

- ランが最後まで回る・約束の族の出来事が 1-3 の記録に出る・監査の食い違い 0(本人の語の原因は発行した判断の呼び)。
- 計器の数と出来事の記録の行が合う・範囲外の過ごし方の本人の計画が書かれる(範囲の外に出る体が居る世界)。
- 日の途中(T=720)で止めて再開=通し(final と checkpoint)。
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

from shibuya.engine.calendar2 import layer as LY

from tests.engine.calendar2._ca2 import STEP_NS, ca2

pytestmark = [pytest.mark.slow, pytest.mark.requires_data("world_v2:w17_schedule.parquet")]

WORLD = Path(__file__).resolve().parents[3] / "data" / "world" / "v2"
KW5 = dict(n_agents=5000, seed=1, world_dir=str(WORLD), vocab_version="v3")


def test_world_5000_one_day_records_meters_and_resume(tmp_path):
    from shibuya import cli

    with ca2():
        a = cli.run(state_out=str(tmp_path / "state"), stop_at_tick=720, checkpoint_every=60, **KW5)
        path = tmp_path / "state" / a.resume["state_files"][-1]["file"]
        b = cli.run(resume_from=str(path), checkpoint_every=60, **KW5)
        r = s = cli.run(checkpoint_every=60, **KW5)
    cc = r.run_manifest_fields()["calendar_2"]
    evs = [e for e in r.event_log.events() if str(e.what).startswith("約束:")]
    au = LY.audit_causes(r.event_log.events(), step_ns=STEP_NS, issued=r.calendar2_layer.issued_keys())
    assert au["events"] > 100 and au["violations"] == 0, au
    by = Counter(e.what for e in evs)
    assert by[LY.W_OFFER] == cc["meter"]["offers"] > 0
    assert cc["outside_plan"].get("出た", 0) > 0 and cc["outside_plan"].get("書いた", 0) > 0
    assert cc["promises"]["rows_promise"] > 0
    cp = lambda x: [(int(c.tick), c.behavior_hash, c.full_hash) for c in x.checkpoints if int(c.tick) >= 720]  # noqa: E731
    assert b.final_hash == s.final_hash and cp(b) == cp(s) and cp(b)
