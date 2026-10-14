"""第 1 期 1-7 道具の台帳 C0(CT10・CT5): グループの一覧=家族(W16 の世帯)+職場(W16 の事業所=W6 の組織)。

約束 (2): 行の数=W16 の世帯の数+事業所の数(検算)。全母集団では ``w16_households.parquet`` の行と ``w6_org.parquet`` の行。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import pytest

from shibuya.agents.population import load_population, sample_population
from shibuya.engine.tools.groups import FAMILY, WORKPLACE, GroupList

WORLD = Path("data/world/v2")
w16 = pytest.mark.requires_data("world_v2:w16_population.parquet", "world_v2:w16_households.parquet",
                                "world_v2:w6_org.parquet")


# ================================================================= 合成の母集団
def test_csr_rows_and_members_on_a_small_population():
    hh = np.array([5, -1, 5, 2, -1, 2, 2])
    org = np.array([-1, 7, 3, 7, -1, -1, 3])
    g = GroupList(household_id=hh, org_id=org)
    assert len(g) == 2 + 2 and (g.n_family, g.n_workplace) == (2, 2)
    assert g.kinds.tolist() == [0, 0, 1, 1] and g.source_ids.tolist() == [2, 5, 3, 7]  # 家族 → 職場・番号の昇順
    assert [g.members(i).tolist() for i in range(4)] == [[3, 5, 6], [0, 2], [2, 6], [1, 3]]
    assert [g.kind_of(i) for i in range(4)] == [FAMILY, FAMILY, WORKPLACE, WORKPLACE]
    assert g.n_members().tolist() == [3, 2, 2, 2]
    t = g.tally()
    assert (t["rows"], t["family"], t["workplace"]) == (4, 2, 2)
    assert t["members"] == {FAMILY: 5, WORKPLACE: 4} and t["max_members"] == {FAMILY: 3, WORKPLACE: 2}
    with pytest.raises(IndexError):
        g.members(4)


def test_empty_and_one_sided():
    e = GroupList.empty(5)
    assert len(e) == 0 and e.tally()["members"] == {FAMILY: 0, WORKPLACE: 0}
    only_org = GroupList(household_id=np.full(3, -1), org_id=np.array([1, 1, 0]))
    assert (only_org.n_family, only_org.n_workplace) == (0, 2) and only_org.members(1).tolist() == [0, 1]
    with pytest.raises(ValueError):
        GroupList(household_id=np.zeros(3), org_id=np.zeros(4))


def test_group_list_is_read_only():
    g = GroupList(household_id=np.array([0, 0]), org_id=np.array([-1, 1]))
    with pytest.raises(AttributeError):
        g.x = 1  # type: ignore[attr-defined]
    with pytest.raises(AttributeError):
        del g.x  # type: ignore[attr-defined]
    with pytest.raises(ValueError):
        g.members(0)[0] = 9  # 読み取り専用の配列
    with pytest.raises(ValueError):
        g.source_ids[0] = 9
    assert not hasattr(g, "__dict__")


# ================================================================= W16 の実データ
@pytest.fixture(scope="module")
def full():
    pop = load_population(WORLD)
    return pop, GroupList.from_population(pop)


@w16
def test_rows_equal_households_plus_establishments_on_the_full_population(full):
    pop, g = full
    n_hh = pq.read_metadata(WORLD / "w16_households.parquet").num_rows
    n_org = pq.read_metadata(WORLD / "w6_org.parquet").num_rows
    hh = np.asarray(pop.household_id)
    org = np.asarray(pop.org_id)
    assert g.n_family == n_hh == np.unique(hh[hh >= 0]).size
    assert g.n_workplace == n_org == np.unique(org[org >= 0]).size
    assert len(g) == n_hh + n_org == 27_404 + 9_872  # 検算(記録 c0/README.md §3)
    t = g.tally()
    assert t["members"] == {FAMILY: int(np.count_nonzero(hh >= 0)), WORKPLACE: int(np.count_nonzero(org >= 0))}
    # 値まで: 世帯の番号の行の成員=その世帯の体(parquet の世帯の番号と一致)
    hh_ids = pq.read_table(WORLD / "w16_households.parquet", columns=["household_id"]).column("household_id")
    assert np.array_equal(np.sort(hh_ids.to_numpy()), g.source_ids[: g.n_family])
    for i in (0, g.n_family // 2, g.n_family - 1, g.n_family, len(g) - 1):
        sid = int(g.source_ids[i])
        col = hh if i < g.n_family else org
        assert np.array_equal(g.members(i), np.flatnonzero(col == sid)), i


@w16
def test_rows_on_the_5000_sample(full):
    pop, _ = full
    s = sample_population(pop, 5_000, 1)
    g = GroupList.from_population(s)
    hh, org = np.asarray(s.household_id), np.asarray(s.org_id)
    assert g.n_family == np.unique(hh[hh >= 0]).size and g.n_workplace == np.unique(org[org >= 0]).size
    assert len(g) == g.n_family + g.n_workplace
    # n_agents で先頭を切る(ランの体の数)
    g2 = GroupList.from_population(s, 1_000)
    assert g2.tally()["n_agents"] == 1_000
    assert g2.n_family == np.unique(hh[:1_000][hh[:1_000] >= 0]).size
