"""第 3 期 3-5: 体の規則の出典の欄(③ の 3 件に conf と出典・倒れる率は出典なし=expedient)とつなぎの台帳の行の結び。

- ``BODY_RULES``: 洗い出しの A2・D8・D9・D18 を全部持つ・conf は mechanism/expedient・出典は空でない・expedient の規則は
  つなぎの台帳の active な行に結ぶ(mechanism は結ばない)。倒れる率は expedient で出典に「出典なし」。
- 宣言の表(``BODY_EXPEDIENTS``・``RESERVE_EXPEDIENTS``・``SYSTEM1_EXPEDIENTS``)の各文はつなぎの台帳の行の ``what`` と同じ
  (``BR-BODY-*``・``BR-BODY-RESERVE-*``・``BR-SYSTEM1-*``)。器だけの 3 件は外す段 5-3・5-1・5-3・inferred。
- 既存の ③ の行(環境と顕著行為の見出し)は項の数を移した分だけ減らし、注に移した先を書いた(持ち主の付け替え)。
"""

from __future__ import annotations

import pytest

from shibuya.engine.bridging import ledger as L
from shibuya.engine.bridging import scan as S
from shibuya.engine.body import rules as BR
from shibuya.engine.body import schedule as BS
from shibuya.engine.body import system1 as S1


@pytest.fixture(scope="module")
def ledger():
    return L.load(L.default_path())


def test_rules_cover_the_inventory_rows_with_conf_and_source(ledger):
    assert {r.inventory for r in BR.BODY_RULES} == {"A2", "D8", "D9", "D18"}
    ids = [r.id for r in BR.BODY_RULES]
    assert len(ids) == len(set(ids))
    active = {r.id: r for r in ledger if r.status == "active"}
    for r in BR.BODY_RULES:
        assert r.conf in ("mechanism", "expedient"), r.id
        assert r.source.strip() and r.what.strip() and r.port.startswith("BodyModel."), r.id
        if r.conf == "expedient":
            assert r.bridge in active, (r.id, r.bridge)
            assert active[r.bridge].conf == "expedient"
        else:
            assert r.bridge == "", r.id
    col = BR.rule("body.collapse_rate")
    assert col.conf == "expedient" and "出典なし" in col.source and col.inventory == "D9"
    assert col.bridge == "BR-BODY-COLLAPSE-RATE"
    assert BR.rule("body.shade_factor").conf == "mechanism"
    with pytest.raises(KeyError):
        BR.rule("body.nothing")


@pytest.mark.parametrize("table,prefix,path", [
    (BR.BODY_EXPEDIENTS, "BR-BODY-", "src/shibuya/engine/body/rules.py"),
    (BS.RESERVE_EXPEDIENTS, "BR-BODY-RESERVE-", "src/shibuya/engine/body/schedule.py"),
    (S1.SYSTEM1_EXPEDIENTS, "BR-SYSTEM1-", "src/shibuya/engine/body/system1.py"),
])
def test_declaration_tables_are_one_to_one_with_ledger_rows(ledger, table, prefix, path):
    by_key = {r.declared_in: r for r in ledger}
    for text in table:
        key = S.declared_in_of(path, S.FORM_EXPEDIENTS, text)
        row = by_key[key]
        assert row.what == text and row.id.startswith(prefix) and row.status == "active" and row.conf == "expedient"
        assert row.since == "2026-10-15" and row.remove_basis == "inferred"


def test_system1_rows_remove_at_the_spatial_stages(ledger):
    rows = {r.id: r for r in ledger}
    assert [rows[s.bridge].remove_at for s in S1.SLOTS] == ["5-3", "5-1", "5-3"]
    assert [s.stage for s in S1.SLOTS] == ["5-3", "5-1", "5-3"]
    assert rows["BR-BODY-RESERVE-DETECT"].remove_at == rows["BR-BODY-RESERVE-ACCUMULATE"].remove_at == "T3"


def test_moved_items_left_the_old_headings(ledger):
    rows = {r.id: r for r in ledger}
    env = rows["HD-engine.processes.environment-1af925f4"]
    sal = rows["HD-engine.processes.salient-1af925f4"]
    assert "項 2 個" in env.what and "BR-BODY-FELT-MAP" in env.why
    assert "項 4 個" in sal.what and "BR-BODY-COLLAPSE-RATE" in sal.why
    assert "BR-BODY-NATURAL-VARIATION" in rows["HD-engine.resolve-1af925f4"].why
    heads = {d.declared_in: d for d in S.scan_package() if d.form == S.FORM_HEADING}
    assert heads[env.declared_in].items == 2 and heads[sal.declared_in].items == 4
