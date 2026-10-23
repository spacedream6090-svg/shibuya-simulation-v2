"""第 2 期 2-1 経済の段階 2: 世界資産の 2 日のラン(5,000 体・seed 1・既定 v3・開始日 2026-08-24(月)=25 日の給料日をまたぐ)。

``slow``・data が要る。腕 on(部品は全部)で、W6 の組織の雇用の行から賃金が払われる・OSM の ATM で引き出しが起きる・
運賃が IC(口座)で払われる・税が政府に入る・毎日 保存則の残差 0・``RunResult.conserved``。腕 off の同じランは段階 2 の欄が
立たない(既定の結果不変は byte-check 19 構成の受け持ち=記録 ec21/README.md)。
"""

from __future__ import annotations

import pytest

from shibuya.economy.accounts import AccountCode, Sector
from shibuya.engine import economy_stage2 as ES2

pytestmark = [pytest.mark.slow,
              pytest.mark.requires_data("world_v2:w17_schedule.parquet", "osm:poi_tags_overpass_20260928.json",
                                        "calendar")]


def _run(monkeypatch, arm: str):
    from shibuya import cli

    monkeypatch.setattr(ES2, "_ARM", arm)
    monkeypatch.setattr(ES2, "_PARTS", ES2.PARTS)
    monkeypatch.setattr(ES2, "_ATM_OVERRIDE", None)
    return cli.run(n_agents=5_000, seed=1, world_dir="data/world/v2", sim_days=2, vocab_version="v3",
                   start_sim_datetime="2026-08-24")


def test_world_two_days_with_the_arm(monkeypatch):
    res = _run(monkeypatch, "on")
    led = res.ledger.money
    man = res.run_manifest_fields()
    run = led.stage2.s2_meter["run"]
    assert led.sizes[int(Sector.EMPLOYER)] == 9_872  # W6 の組織の数(雇用主の口)
    assert run["wages"]["employer_rows"] > 0 and run["wages"]["outside_employer"] == 0
    assert run["withdraw"]["count"] > 0 and run["payment"]["fare_ic_rows"] > 0 and run["tax"]["amount"] > 0
    assert run["endow"]["visitor_rows"] > 0
    for d in man["daily"]:
        c = d["economy"]["conservation"]
        assert c["ok"] is True and c["residual"] == 0, c
    assert [d["economy"]["stage2"]["payday"] for d in man["daily"]] == [False, True]
    assert res.conserved
    wage = sum(int(f[:, :, int(AccountCode.WAGE)].sum()) for f in led.flow_daily)
    assert wage == run["wages"]["amount"] > 0
    assert man["economy"]["stage2"]["atms"]["n"] + man["economy"]["stage2"]["atms"]["dropped"] == 55
    # 腕のランの輪の係数 16.0 行/体/日(2 日の和の最大 14.2 の 1.1 倍以上・1 日の最大 8.8 の 1.5 倍以上)=溢れ 0
    assert man["economy"]["raw_capacity"] == 80_000 and man["economy"]["raw_rows_per_agent_day"] == 16.0
    assert man["economy"]["raw_overflow"] == 0


def test_world_two_days_without_the_arm(monkeypatch):
    res = _run(monkeypatch, "off")
    led = res.ledger.money
    assert led.stage2 is None and led.sizes[int(Sector.EMPLOYER)] == 1
    man = res.run_manifest_fields()
    assert "stage2" not in man["economy"]
    assert all(d["economy"]["conservation"]["ok"] for d in man["daily"])
    assert (led.raw_methods() == 0).all()
