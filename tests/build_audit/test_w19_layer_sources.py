# -*- coding: utf-8 -*-
"""第333: W19 の「層の元」の表(回答 10-13b §1 1-2)。値は読まない・表だけの試験。"""
from __future__ import annotations

from shibuya.build.audit import w19_freeze as W19


def test_every_holdout_layer_has_a_source_family():
    names = {name for name, _ in W19.HOLDOUT_LAYERS}
    assert names <= set(W19.SOURCE_FAMILIES), names - set(W19.SOURCE_FAMILIES)


def test_build_input_families_come_from_w12_constants():
    fam = W19.BUILD_INPUT_FAMILIES["transport_census_12+odpt_passenger_survey"]
    assert "realworld/transport_census/station_flow_12.json" in fam
    assert "realworld/odpt_passenger_survey/shibuya.json" in fam


def test_shibuya_jinryu_and_boundary_counts_are_marked_not_independent():
    rows = {r["name"]: r for r in W19.layer_independence()}
    assert rows["shibuya_jinryu"]["source_family"] == rows["kddi_la"]["source_family"]
    assert rows["shibuya_jinryu"]["independent"] is False
    assert rows["shibuya_jinryu"]["same_family_as_opened"] is True
    assert rows["boundary_counts"]["independent"] is False
    assert rows["boundary_counts"]["shares_build_input"] is True
    assert rows["kddi_la"]["opened"] is True and rows["kddi_la"]["independent"] is False
    for r in rows.values():
        assert r["mark"] == ("独立" if r["independent"] else "照合用(独立でない)")
        assert r["reasons"], r


def test_independence_rows_cover_all_layers_in_order():
    rows = W19.layer_independence()
    assert [r["name"] for r in rows] == [name for name, _ in W19.HOLDOUT_LAYERS]
