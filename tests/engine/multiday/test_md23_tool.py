"""第 2 期 2-3: 複数日の計器の道具(``md23/tools/multiday_md23.py``)の単体と、実データの 5 日(``slow``・1 本=既定・seed 1)。

- 合成の 3 日の記録(手で組んだ辞書)から日ごとの表を作る: 呼数・会話の差分・財布の増減(前の日の終わりからの 1 体あたり)・
  状態のファイル(見出しと配列の 2 本を刻みの番号でまとめる)・満杯率から満杯までの日数(届いた日/外挿=推測)。
- 合成の世界の 3 日のラン(80 体・腕 a)で道具が日ごとの行を集める(計器の 2-0 の式は世界資産のランだけ)。
"""

from __future__ import annotations

import datetime as dt

import pytest

from shibuya.core.time_consts import STEPS_PER_DAY

from tests.engine.multiday._md import WORLD, tool


def _doc() -> dict:
    daily, probe = [], []
    cash = [9_000, 7_500, 7_000]
    for d in range(3):
        daily.append({"day": d, "llm_calls": 100 + d, "money": {"households": cash[d]},
                      "events": {"rows": 50 + d, "by_what": {"行為:移動": 3, "行為:会話の始まり": 2, "過程:rail": 9,
                                                             "知覚:気づき": 1, "道具:看板": d}},
                      "stage2": ({"withdraw": {"amount": 1_000 * d, "count": d}, "wages": {"amount": 0},
                                  "deposit": {"p10": 1, "p50": 2, "p90": 3}} if d else None)})
        probe.append({"day": d, "wall_s_nondeterministic": 1.5,
                      "conv": {"opened": 3 * (d + 1), "closed": 2 * (d + 1), "joined": 0},
                      "relations": {"edges_live": 10 + d, "edges_filled": 12 + d, "full_rate": [0.2, 0.3, 0.4][d],
                                    "full_live_rate": 0.1, "acquaintance_edges": d, "tau_recalibrated": -2.3},
                      "memory": {"rows": 40 * (d + 1), "full_agents": 0, "store": {"origins": {"log": 40, "legacy": 0}}},
                      "money": {"cash_per_agent": {"p50": 3_000.0}}})
    files = [{"name": f"state-T{STEPS_PER_DAY * (d + 1):08d}.{ext}", "bytes": b}
             for d in range(3) for ext, b in (("json", 100), ("npz", 1_000 * (d + 1)))]
    return {"config": "a", "agents": 2, "money_start": 10_000, "daily": daily, "probe": probe, "gauge": None,
            "state_files": files}


def test_day_rows_from_a_synthetic_three_day_record():
    md = tool()
    rows = md.day_rows(_doc())
    assert [r["day"] for r in rows] == [0, 1, 2]
    assert [r["llm_calls"] for r in rows] == [100, 101, 102]
    assert [r["conv_opened"] for r in rows] == [3, 3, 3] and [r["conv_closed"] for r in rows] == [2, 2, 2]
    assert [r["cash_per_agent_change"] for r in rows] == [-500.0, -750.0, -250.0]  # 2 体・前の日の終わりから
    assert [r["state_file_bytes"] for r in rows] == [1_100, 2_100, 3_100]  # 見出しと配列の 2 本をまとめる
    assert [r["body_events"] for r in rows] == [6, 7, 8]  # 行為・知覚・道具の語(過程の語は数えない)
    assert rows[0]["withdraw"] is None and rows[2]["withdraw"] == 2_000 and rows[1]["deposit"]["p50"] == 2
    assert rows[1]["store_origins"] == {"log": 40, "legacy": 0} and rows[2]["mem_rows"] == 120


def test_days_to_full():
    md = tool()
    rows = md.day_rows(_doc())
    got = md.days_to_full(rows)
    assert got["reached_day"] is None and got["slope_per_day"] == pytest.approx(0.1)
    assert got["extrapolated_days"] == pytest.approx(2 + 0.6 / 0.1)  # 推測(外挿)
    assert md.days_to_full([{"day": 0, "full_rate": 0.5}, {"day": 1, "full_rate": 1.0}])["reached_day"] == 1
    assert md.days_to_full([{"day": 0, "full_rate": 0.5}, {"day": 1, "full_rate": 0.5}])["extrapolated_days"] is None


def test_the_tool_collects_three_synthetic_days():
    md = tool()
    doc = md.run_collect("a", days=3, agents=80, seed=1, world=None, scratch=None, gauge=False,
                         extra=dict(n_cells=9, budget=80.0, sleep_suppression=False))
    rows = md.day_rows(doc)
    assert [r["day"] for r in rows] == [0, 1, 2] and all(r["llm_calls"] for r in rows)
    assert all(r["store_origins"]["legacy"] == 0 and r["store_origins"]["log"] > 0 for r in rows)
    assert all(r["body_events"] > 0 for r in rows) and rows[-1]["mem_rows"] >= rows[0]["mem_rows"]
    assert doc["arms"] == {"memory_store": "events"} and doc["start_check_waived"] == [] and not doc["test_only"]
    md.set_arms("default")


@pytest.mark.slow
@pytest.mark.requires_data("world_v2:w17_schedule.parquet")
def test_world_five_days_default(tmp_path):
    """実データの 5 日(月〜金・5,000 体・seed 1・既定の腕=土台 v3_mem_rel・開始日の検査 A1-3 は外さない=親の判断 M1)。
    曜日の比較はしない(K9・記録 md23/README.md)。"""
    md = tool()
    doc = md.run_collect("default", days=5, agents=5_000, seed=1, world=str(WORLD), scratch=tmp_path, gauge=True)
    rows = md.day_rows(doc)
    assert [r["day"] for r in rows] == list(range(5)) and all(r["llm_calls"] > 0 for r in rows)
    assert all(r["presence_peak_stage"] is not None and r["arrivals_n"] > 0 for r in rows)
    assert all(r["state_file_bytes"] for r in rows)
    # 〔検収 L2〕影の日は資産の影のファイルから導く(2-4 の活性化で資産が変わっても落ちない)
    have = {p.name[len("w9_shadow_"):-len(".npy")] for p in WORLD.glob("w9_shadow_2*.npy")}
    days = [(dt.date(2026, 7, 13) + dt.timedelta(days=i)).isoformat() for i in range(5)]
    w = {x["calendar_date"]: x["shadow_fallback"] for x in doc["weather"]}
    assert sorted(w) == days and all(w[d] is (d not in have) for d in days)
    assert doc["start_check_waived"] == [] and not doc["test_only"] and doc["memory_store"] is None
