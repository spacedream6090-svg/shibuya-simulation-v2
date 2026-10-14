"""第 2 期 2-3: 影の日付(W9)を 7 日の窓(2026-07-13 月〜07-19 日)に広げた(構築側・活性化は 2-4)。

- ``SHADOW_DATES`` が窓の 7 日と主の日 07-28 を持つ(先頭=主の日は前のまま)。
- 窓の中の日は暦の日付の影を読む=近い日の影(つなぎ ``BR-SHADOW-NEAREST-DAY``)を使わない。窓の外(07-20)は使う。
  計器=manifest の ``weather.days[].shadow_fallback``(世界資産 ``data/world/v2_stage_2-3/`` の 8 日のラン)。
- つなぎの台帳: ``BR-SHADOW-NEAREST-DAY``・``W9#5`` は「窓の外の日だけ」=active のまま。外す段は 2-4(窓を広げる版上げ)
  → 〔第334・2-4〕7(親の判断=窓の外の日は残る)。
  ``DOC-memory-store-legacy`` は removed(2-3)。近接に左右される値の暫定の印の行(外す段 5-2)。
"""

from __future__ import annotations

import datetime as dt

import pytest

from shibuya.build.vis import w9_shadow as W9
from shibuya.engine.bridging.ledger import load as load_ledger
from shibuya.engine.processes import environment as ENV

from tests.engine.multiday._md import STAGE, tool

WINDOW = tuple((dt.date(2026, 7, 13) + dt.timedelta(days=i)).isoformat() for i in range(7))


def test_shadow_dates_cover_the_seven_day_window():
    assert WINDOW[0] == "2026-07-13" and WINDOW[-1] == "2026-07-19"
    assert W9.SHADOW_DATES[0] == "2026-07-28" and len(set(W9.SHADOW_DATES)) == len(W9.SHADOW_DATES)
    assert set(WINDOW) <= set(W9.SHADOW_DATES) and len(W9.SHADOW_DATES) == 8
    for d in WINDOW:  # 窓の中: 暦の日付そのもの(近い日の影は使わない)
        assert ENV.nearest_shadow_date(W9.SHADOW_DATES, d) == d
    assert ENV.nearest_shadow_date(W9.SHADOW_DATES, "2026-07-20") == "2026-07-19"  # 窓の外は近い日


def test_bridging_rows_after_2_3():
    led = load_ledger()
    for rid in ("BR-SHADOW-NEAREST-DAY", "W9#5"):
        r = led.get(rid)
        assert (r.status, r.remove_at) == ("active", "7"), rid  # 〔第334・2-4〕外す段を改めた(親)=2-4 → 7
        assert "窓の外" in r.why, rid
    r = led.get("DOC-memory-store-legacy")
    assert (r.status, r.remove_at) == ("removed", "2-3")
    prov = [r for r in led if r.id.startswith("DOC-md23-provisional-")]
    assert len(prov) == 3 and all(r.remove_at == "5-2" and r.status == "active" for r in prov)


@pytest.mark.requires_data("world_stage_2-3:w9_shadow_2026-07-19.npy", "world_v2")
def test_stage_asset_has_the_window_and_the_fallback_is_used_only_outside():
    for d in WINDOW:
        assert (STAGE / f"w9_shadow_{d}.npy").exists(), d
    assert not (STAGE / "w9_shadow_2026-07-20.npy").exists()
    md = tool()
    doc = md.run_collect("default", days=8, agents=30, seed=1, world=str(STAGE), scratch=None, gauge=False,
                         allow_rest_days=True)  # 窓の外の日まで回す試験=A1-3 の規則の違反を記録に写す(test_only)
    days = {w["calendar_date"]: w for w in doc["weather"]}
    assert set(days) == set(WINDOW) | {"2026-07-20"}
    for d in WINDOW:  # 計器 0(窓の中は近い日の影を読まない)
        assert days[d]["shadow_date"] == d and days[d]["shadow_fallback"] is False, days[d]
    assert days["2026-07-20"]["shadow_fallback"] is True and days["2026-07-20"]["shadow_date"] == "2026-07-19"
    assert doc["test_only"] and any("連続する平日" in w for w in doc["start_check_waived"])  # A1-3 は道具だけが外した
