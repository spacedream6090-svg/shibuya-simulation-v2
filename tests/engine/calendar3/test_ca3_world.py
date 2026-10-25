"""第 6 期 6-2 カレンダー 3 の世界の試験(slow・data): 5,000 体の日曜 1 日(試験用の印)=権利台帳の雇用の行と W20 の週の表から
雇い主の口の表ができ、雇い主が組んで C3 の連絡が C1 の口を通る(監査 0)。"""

from __future__ import annotations

import pytest

from shibuya.engine.calendar3 import layer as LY
from shibuya.engine.contact import layer as CL

from tests.engine.calendar3._ca3 import STEP_NS, SUNDAY, ca3

pytestmark = [pytest.mark.slow, pytest.mark.requires_data("world_v2:w20_calendar_1a.parquet")]


def test_world_5000_sunday_composes_and_audits_are_clean():
    from shibuya import cli

    with ca3():
        r = cli.run(n_agents=5_000, seed=1, world_dir="data/world/v2", vocab_version="v3", start_sim_datetime=SUNDAY)
    m = r.run_manifest_fields()["calendar_3"]
    ro = m["roster"]
    assert ro["units"] > 0 and ro["weekly_scheduled"] > 0 and ro["fixed_workers"] > 0
    assert ro["weekly_scheduled"] + ro["weekly_outside_employer"] + ro["weekly_no_employer"] == ro["weekly_workers"]
    assert m["composed"]["units"] == ro["units"] and m["composed"]["workers"] <= ro["weekly_scheduled"]
    evs = list(r.event_log.events())
    assert LY.audit_causes(evs, step_ns=STEP_NS, issued=r.calendar3_layer.issued_keys())["violations"] == 0
    assert CL.audit_causes(evs, step_ns=STEP_NS, issued=r.contact_layer.issued_keys())["violations"] == 0
