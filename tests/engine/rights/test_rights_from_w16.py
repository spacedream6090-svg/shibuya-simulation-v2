"""第 1 期 1-5 権利台帳の最初の中身(計画 1-5 の 4 つ・決定 10-12 §4-5 CP4)。

- (a) 雇用: 行の数=W16 の ``org_id`` を持つ体の数(全母集団 39 万体と 5,000 体の抽出の両方)・行の物=その体の組織・
  出どころ ``w16_population.org_id``・開始前から終わりなし・原因なし(初期状態)。
- (b) 営業許可: 0 行(空欄=つなぎの台帳の行)。
- (c) 店の賃借: POI ごとに 1 行(店 → 区画)・家賃は空欄(1-4 の ``BR-RENT-BLANK``)・相手(貸し手)は空欄。
- (d) 住まい: 0 行(空欄=つなぎの台帳の行)。
- 空欄の行(``BLANK_BRIDGES``)はつなぎの台帳に active で載っている。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import pytest

from shibuya.agents.population import load_population
from shibuya.engine.bridging import ledger as BR
from shibuya.engine.rights import initial as RI
from shibuya.engine.rights import ledger as L

WORLD = Path("data/world/v2")
w16 = pytest.mark.requires_data("world_v2:w16_population.parquet", "world_v2:w6_poi.parquet")


def _org_rows(led: L.Rights) -> list[L.Right]:
    return [r for r in led if r.kind == L.EMPLOY and r.object[0] == L.ORG]


@pytest.fixture(scope="module")
def full():
    pop = load_population(WORLD)
    n_poi = pq.read_metadata(WORLD / "w6_poi.parquet").num_rows
    org = pq.read_table(WORLD / "w16_population.parquet", columns=["org_id"]).column("org_id").to_numpy()
    return pop, n_poi, org, RI.build_initial(pop.kind, n_poi, pop.org_id)


@w16
def test_employment_rows_equal_the_bodies_with_an_org_id(full):
    pop, n_poi, org, led = full
    rows = _org_rows(led)
    assert len(rows) == int(np.count_nonzero(org >= 0)) == int(np.count_nonzero(pop.org_id >= 0)) > 0
    # 値まで: 行の持ち主の体の org_id が行の物
    holders = np.asarray([r.holder[1] for r in rows], dtype=np.int64)
    objects = np.asarray([r.object[1] for r in rows], dtype=np.int64)
    assert np.array_equal(objects, np.asarray(pop.org_id, dtype=np.int64)[holders])
    assert np.array_equal(holders, np.flatnonzero(np.asarray(pop.org_id) >= 0))
    assert {(r.source, r.since_ns, r.until_ns, r.counterparty, r.cause) for r in rows} == {
        (RI.SOURCE_W16_ORG, None, None, None, None)}


@w16
def test_the_four_contents_and_their_blanks(full):
    pop, n_poi, org, led = full
    c = led.tally()
    n_org = int(np.count_nonzero(org >= 0))
    n_staff = n_poi if np.any(pop.kind == 2) else 0
    assert c["by_kind"] == {"own": 0, "lease": n_poi, "employ": n_org + n_staff, "licence": 0}
    assert c["by_object_kind"] == {"org": n_org, "store": n_staff, "parcel": n_poi, "dwelling": 0}
    assert c["by_source"] == {RI.SOURCE_W16_ORG: n_org, RI.SOURCE_STAFF: n_staff, RI.SOURCE_POI: n_poi}
    assert c["rows"] == len(led) == n_org + n_staff + n_poi
    leases = [r for r in led if r.kind == L.LEASE]
    assert [(r.holder, r.object) for r in leases] == [((L.STORE, j), (L.PARCEL, j)) for j in range(n_poi)]
    assert all(r.counterparty is None for r in leases)  # 貸し手は空欄


@w16
def test_a_sampled_run_population():
    """5,000 体の抽出(byte-check と同じ seed 1)でも、雇用の行=``org_id`` を持つ体。組み立ての材料の関数を通す。"""
    from shibuya.engine.systems.build import _org_of_agent

    pop = load_population(WORLD, 5_000, 1)
    org = _org_of_agent(pop, 5_000)
    assert org.shape == (5_000,) and np.array_equal(org, np.asarray(pop.org_id, dtype=np.int64))
    led = RI.build_initial(pop.kind, 50, org)
    assert len(_org_rows(led)) == int(np.count_nonzero(pop.org_id >= 0)) > 0
    # 母集団より体が多いときは足りない体は組織なし
    more = _org_of_agent(pop, 5_010)
    assert (more[5_000:] == -1).all() and np.array_equal(more[:5_000], org)
    assert _org_of_agent(None, 10) is None


def test_no_population_means_no_employment_rows():
    kind = np.asarray([2, 0, 2, 1], dtype=np.int8)
    led = RI.build_initial(kind, 3)
    assert led.tally()["by_source"] == {RI.SOURCE_STAFF: 3, RI.SOURCE_POI: 3}
    assert _org_rows(led) == []


def test_blank_bridges_are_active_rows_of_the_ledger():
    led = BR.default_ledger()
    assert set(RI.BLANK_BRIDGES) == {"lease.rent", "licence", "dwelling"}
    for key, rid in RI.BLANK_BRIDGES.items():
        r = led.get(rid)
        assert r.status == "active" and r.remove_at == "4-2", (key, rid)
    for rid in ("BR-RIGHTS-LICENCE-BLANK", "BR-RIGHTS-DWELLING-BLANK"):
        assert led.get(rid).code_at == ("src/shibuya/engine/rights/initial.py",)
    with pytest.raises(TypeError):
        RI.BLANK_BRIDGES["licence"] = "x"  # type: ignore[index]
