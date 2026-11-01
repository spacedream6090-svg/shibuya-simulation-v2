"""第 6 期 6-6 ② 第 1 部 店の仕事の世界の試験(slow・data): 5,000 体の 1 日(腕 arm)=担当が店に居る店を本人が開け閉めし、
エンジンのつなぎは担当が居ない/寝ている店だけ(担当の行動の ActualLog は SCHEDULED)・監査 0・計器の節がある。"""

from __future__ import annotations

import pytest

from shibuya.engine.duties import layer as LY

from tests.engine.duties._du import STEP_NS, du

pytestmark = [pytest.mark.slow, pytest.mark.requires_data("world_v2:w2_cells.parquet")]


def test_world_5000_one_day_with_the_duties_arm():
    from shibuya import cli

    with du():
        r = cli.run(n_agents=5_000, seed=1, world_dir="data/world/v2", vocab_version="v3")
    m = r.run_manifest_fields()["duties"]
    tot = m["coverage"]["total"]
    assert tot["unlock"]["person"] > 0 and tot["unlock"]["bridge"] > 0
    # 〔検収 M1・M3〕出どころ別のカバー率(W21c/丸振り・W7 の src)と出どころの印
    assert set(m["coverage"]["by_employment_origin"]["unlock"]) <= {"w21c", "round_robin", "none"}
    assert set(m["coverage"]["by_rule_source"]["unlock"]) <= {"category_default", "chain_default", "osm_opening_hours"}
    assert m["shop"]["stores_by_staff_origin"]["w21c"] > 0 and m["shelf"].get("person_failed", 0) == 0  # 〔検収 M2〕
    assert r.runner.opening.n_role_actions == 0  # 担当が店に居て起きている店はエンジンが代わりにしない
    lay = r.duties_layer
    assert LY.audit_causes(r.event_log.events(), step_ns=STEP_NS, issued=lay.issued_keys(),
                           role_ids=lay.role_call_ids())["violations"] == 0
