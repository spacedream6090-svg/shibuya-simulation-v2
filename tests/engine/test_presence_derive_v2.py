"""在圏ブロックの読み口 v2(``engine.presence.PlanBlocks.from_weekly(derive_rule="v2")``)。

設計書 §2 追補(2026-09-12): W17 v2 の語彙は場所語に域内/域外を持たない。域外居住者が
「乗車の前の 移動 駅」(自宅側の駅)や「帰りの乗車の後の 食事 飲食店」(自宅近く)を書くと、
原則(v1: 域外行・乗車行・自宅行以外は在圏)はそれを舞台の中と読み、1 日 2.0 本の在圏
ブロック(本番 v2 第 1 回・域外居住 346,445 体)を作った。v2 は「錨」(cell≥0・職場/学校/宿泊)
と「乗車の区切り」の偶奇でランを選ぶ。**域内居住者の読み方は v1 と同一**。
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from shibuya.agents.weekly import (
    ACTIVITY_WORDS,
    N_DAYS,
    PLACE_WORDS,
    WeeklySchedule,
)
from shibuya.engine.presence import (
    ANCHOR_PLACE_KINDS,
    DERIVE_RULE_DEFAULT,
    DERIVE_RULES,
    PlanBlocks,
)

ACT_SLEEP = ACTIVITY_WORDS.index("就寝")
ACT_PREP = ACTIVITY_WORDS.index("支度")
ACT_MOVE = ACTIVITY_WORDS.index("移動")
ACT_RIDE = ACTIVITY_WORDS.index("乗車")
ACT_WORK = ACTIVITY_WORDS.index("勤務")
ACT_EAT = ACTIVITY_WORDS.index("食事")
ACT_SHOP = ACTIVITY_WORDS.index("買物")
ACT_FUN = ACTIVITY_WORDS.index("娯楽")
ACT_REST = ACTIVITY_WORDS.index("休憩")
PK_HOME = PLACE_WORDS.index("自宅")
PK_WORK = PLACE_WORDS.index("職場")
PK_STATION = PLACE_WORDS.index("駅")
PK_FOOD = PLACE_WORDS.index("飲食店")
PK_SHOP = PLACE_WORDS.index("物販店")
PK_FUN = PLACE_WORDS.index("娯楽施設")
PK_LODGING = PLACE_WORDS.index("宿泊施設")
PK_OUT = PLACE_WORDS.index("域外")

WORLD_DIR = Path(__file__).resolve().parents[2] / "data" / "world" / "v2"


def make_weekly(rows, n_agents: int, day: int = 0) -> WeeklySchedule:
    """``rows`` = ``[(agent_row, start, end, activity, place_kind, target_cell), …]``。"""
    rows = sorted(rows, key=lambda r: (r[0], r[1]))
    counts = np.zeros(n_agents * N_DAYS, dtype=np.int64)
    for r in rows:
        counts[int(r[0]) * N_DAYS + day] += 1
    offset = np.zeros(counts.size + 1, dtype=np.int64)
    np.cumsum(counts, out=offset[1:])
    return WeeklySchedule(
        source=None,
        agent_id=np.arange(n_agents, dtype=np.int64),
        day_offset=offset,
        start_min=np.asarray([r[1] for r in rows], dtype=np.int16),
        end_min=np.asarray([r[2] for r in rows], dtype=np.int16),
        activity=np.asarray([r[3] for r in rows], dtype=np.int8),
        place_kind=np.asarray([r[4] for r in rows], dtype=np.int8),
        target_cell=np.asarray([r[5] for r in rows], dtype=np.int32),
        seq=np.asarray(list(range(len(rows))), dtype=np.int16),
    )


def spans(blocks: PlanBlocks, agent: int = 0) -> list[tuple[int, int]]:
    lo, hi = int(blocks.offset[agent]), int(blocks.offset[agent + 1])
    return [(int(blocks.start[i]), int(blocks.end[i])) for i in range(lo, hi)]


def both(rows, home_out=True):
    wk = make_weekly(rows, 1)
    ho = np.asarray([home_out])
    return (
        PlanBlocks.from_weekly(wk, 0, ho, derive_rule="v1"),
        PlanBlocks.from_weekly(wk, 0, ho, derive_rule="v2"),
    )


# ================================================================= 既定と切替口
def test_default_rule_is_v2_and_bad_rules_are_rejected():
    assert DERIVE_RULE_DEFAULT == "v2"
    assert DERIVE_RULES == ("v1", "v2")
    assert set(ANCHOR_PLACE_KINDS) == {PK_WORK, PLACE_WORDS.index("学校"), PK_LODGING}
    wk = make_weekly([(0, 0, 1_440, ACT_SLEEP, PK_HOME, -1)], 1)
    assert PlanBlocks.from_weekly(wk, 0, np.array([True])).derive_rule == "v2"
    with pytest.raises(ValueError):
        PlanBlocks.from_weekly(wk, 0, np.array([True]), derive_rule="v3")


# ================================================================= 通勤者: 自宅側の駅と帰宅後の店
def test_home_side_station_and_after_ride_dinner_are_not_in_the_stage():
    """本番 v2 第 1 回の典型: 移動 駅(自宅側)→乗車→勤務*→移動 駅→乗車→食事 飲食店(自宅近く)。"""
    rows = [
        (0, 0, 400, ACT_SLEEP, PK_HOME, -1),
        (0, 400, 430, ACT_PREP, PK_HOME, -1),
        (0, 430, 470, ACT_MOVE, PK_STATION, -1),   # 自宅側の駅(v1 はここを在圏に読む)
        (0, 470, 530, ACT_RIDE, PK_OUT, -1),
        (0, 530, 1_050, ACT_WORK, PK_WORK, 3),     # 錨
        (0, 1_050, 1_080, ACT_MOVE, PK_STATION, -1),  # 渋谷駅へ(在圏)
        (0, 1_080, 1_140, ACT_RIDE, PK_OUT, -1),
        (0, 1_140, 1_200, ACT_EAT, PK_FOOD, -1),   # 自宅近くの店(v1 はここも在圏)
        (0, 1_200, 1_440, ACT_REST, PK_HOME, -1),
    ]
    v1, v2 = both(rows)
    assert spans(v1) == [(430, 470), (530, 1_080), (1_140, 1_200)]
    assert spans(v2) == [(530, 1_080)]


def test_a_return_ride_only_day_keeps_the_anchored_run_before_it():
    """行きの乗車を書かず帰りだけ書いた通勤者: 錨のラン(区間 0)が在圏側・乗車後の店は域外。"""
    rows = [
        (0, 0, 420, ACT_SLEEP, PK_HOME, -1),
        (0, 420, 470, ACT_MOVE, PK_STATION, -1),
        (0, 470, 1_050, ACT_WORK, PK_WORK, 3),
        (0, 1_050, 1_080, ACT_MOVE, PK_STATION, -1),
        (0, 1_080, 1_110, ACT_RIDE, PK_OUT, -1),
        (0, 1_110, 1_200, ACT_SHOP, PK_SHOP, -1),
        (0, 1_200, 1_440, ACT_REST, PK_HOME, -1),
    ]
    _, v2 = both(rows)
    assert spans(v2) == [(420, 1_080)]


def test_a_mid_day_outside_row_still_splits_the_anchored_day_into_two_blocks():
    """⑦(既存)の並び: 勤務*→休憩 域外→勤務* は v1 と同じく 2 本(錨は常に在圏)。"""
    rows = [
        (0, 0, 420, ACT_SLEEP, PK_HOME, -1),
        (0, 420, 480, ACT_RIDE, PK_STATION, -1),
        (0, 480, 720, ACT_WORK, PK_WORK, 3),
        (0, 720, 780, ACT_REST, PK_OUT, -1),
        (0, 780, 1_020, ACT_WORK, PK_WORK, 3),
        (0, 1_020, 1_440, ACT_SLEEP, PK_HOME, -1),
    ]
    v1, v2 = both(rows)
    assert spans(v1) == spans(v2) == [(480, 720), (780, 1_020)]


# ================================================================= 来街者(錨なし): 乗車の偶奇
def test_a_visitor_with_two_rides_is_in_the_stage_between_them():
    rows = [
        (0, 0, 500, ACT_SLEEP, PK_HOME, -1),
        (0, 500, 540, ACT_MOVE, PK_STATION, -1),   # 自宅側
        (0, 540, 600, ACT_RIDE, PK_STATION, -1),   # 行き
        (0, 600, 720, ACT_SHOP, PK_SHOP, -1),
        (0, 720, 800, ACT_EAT, PK_FOOD, -1),
        (0, 800, 830, ACT_MOVE, PK_STATION, -1),
        (0, 830, 900, ACT_RIDE, PK_OUT, -1),       # 帰り
        (0, 900, 1_000, ACT_FUN, PK_FUN, -1),      # 自宅近く
        (0, 1_000, 1_440, ACT_REST, PK_HOME, -1),
    ]
    v1, v2 = both(rows)
    assert spans(v1) == [(500, 540), (600, 830), (900, 1_000)]
    assert spans(v2) == [(600, 830)]


def test_a_visitor_who_wrote_only_the_return_ride_is_rescued():
    """奇数側(乗車の後)に滞在ランが無く偶数側にある → 偶数側が在圏(救済)。"""
    rows = [
        (0, 0, 500, ACT_SLEEP, PK_HOME, -1),
        (0, 500, 600, ACT_MOVE, PK_STATION, -1),
        (0, 600, 720, ACT_SHOP, PK_SHOP, -1),
        (0, 720, 750, ACT_MOVE, PK_STATION, -1),
        (0, 750, 800, ACT_RIDE, PK_OUT, -1),
        (0, 800, 1_440, ACT_REST, PK_HOME, -1),
    ]
    _, v2 = both(rows)
    assert spans(v2) == [(500, 750)]


def test_without_rides_and_anchors_only_transit_only_runs_are_dropped():
    """乗車も錨も無い体: 滞在のあるランは全部在圏(v1 と同じ)・移動だけのランは落とす。"""
    rows = [
        (0, 0, 600, ACT_SLEEP, PK_HOME, -1),
        (0, 600, 640, ACT_MOVE, PK_STATION, -1),
        (0, 640, 700, ACT_REST, PK_OUT, -1),
        (0, 700, 800, ACT_SHOP, PK_SHOP, -1),
        (0, 800, 840, ACT_MOVE, PK_STATION, -1),
        (0, 840, 1_440, ACT_REST, PK_HOME, -1),
    ]
    v1, v2 = both(rows)
    assert spans(v1) == [(600, 640), (700, 840)]
    assert spans(v2) == [(700, 840)]


def test_a_whole_day_outside_has_no_block_even_with_a_station_row():
    """本番 v2 で新たに 0 本になった体の形(0807-2340 用事 域外): 移動 駅 だけでは在圏にしない。"""
    rows = [
        (0, 0, 412, ACT_SLEEP, PK_OUT, -1),
        (0, 412, 443, ACT_PREP, PK_OUT, -1),
        (0, 443, 487, ACT_MOVE, PK_STATION, -1),
        (0, 487, 1_420, ACT_REST, PK_OUT, -1),
        (0, 1_420, 1_440, ACT_REST, PK_OUT, -1),
    ]
    v1, v2 = both(rows)
    assert spans(v1) == [(443, 487)]
    assert spans(v2) == []


# ================================================================= 宿(錨)と域内居住者
def test_a_lodging_row_is_an_anchor_so_a_tourist_sleeps_in_the_stage():
    rows = [
        (0, 0, 420, ACT_SLEEP, PK_LODGING, -1),
        (0, 420, 450, ACT_PREP, PK_HOME, -1),        # 語彙の癖(自宅=宿)・域外行として割れる
        (0, 450, 480, ACT_MOVE, PK_STATION, -1),
        (0, 480, 1_200, ACT_FUN, PK_FUN, -1),
        (0, 1_200, 1_440, ACT_REST, PK_LODGING, -1),
    ]
    _, v2 = both(rows)
    assert spans(v2) == [(0, 420), (450, 1_440)]


def test_in_area_residents_read_exactly_as_v1():
    rows = [
        (0, 0, 420, ACT_SLEEP, PK_HOME, -1),
        (0, 420, 450, ACT_MOVE, PK_STATION, -1),
        (0, 450, 500, ACT_RIDE, PK_OUT, -1),
        (0, 500, 1_000, ACT_WORK, PK_OUT, -1),      # 域外で働く住民
        (0, 1_000, 1_050, ACT_RIDE, PK_OUT, -1),
        (0, 1_050, 1_100, ACT_EAT, PK_FOOD, -1),
        (0, 1_100, 1_440, ACT_REST, PK_HOME, -1),
    ]
    v1, v2 = both(rows, home_out=False)
    assert spans(v1) == spans(v2) == [(0, 450), (1_050, 1_440)]
    assert np.array_equal(v1.next_outside, v2.next_outside)


# ================================================================= 実 W17(v1 表)の golden
@pytest.mark.skipif(not (WORLD_DIR / "w17_schedule.parquet").exists(), reason="W17 が無い")
def test_v2_rule_on_the_real_w17_matches_the_parent_verified_counts():
    """親検証値(2026-09-12・全 390,067 体・day0・現行 W17 v1 表):
    v1 読み口 = 域外居住者 0..3 本 [85,766 / 214,998 / 45,631 / 50](既存 golden)
    v2 読み口 = [97,242 / 247,395 / 1,808 / 0]・域内居住者のブロックは v1 と同一。
    """
    from shibuya.agents.population import load_population
    from shibuya.agents.weekly import load_weekly

    full = load_population(WORLD_DIR, n=None, seed=1)
    wk = load_weekly(WORLD_DIR)
    ho = np.asarray(full.home_cell) < 0
    b1 = PlanBlocks.from_weekly(wk, 0, ho, derive_rule="v1")
    b2 = PlanBlocks.from_weekly(wk, 0, ho, derive_rule="v2")
    p1, p2 = b1.blocks_per_agent(), b2.blocks_per_agent()
    assert np.bincount(p1[ho])[:4].tolist() == [85_766, 214_998, 45_631, 50]
    assert np.bincount(p2[ho], minlength=4)[:4].tolist() == [97_242, 247_395, 1_808, 0]
    assert np.array_equal(p1[~ho], p2[~ho])
    m1, m2 = np.repeat(~ho, p1), np.repeat(~ho, p2)
    assert np.array_equal(b1.start[m1], b2.start[m2])
    assert np.array_equal(b1.end[m1], b2.end[m2])
