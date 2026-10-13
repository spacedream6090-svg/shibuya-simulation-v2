"""第 1 期 1-4 規則の表(CP10・決定 10-12 §1-12): 出典と版が必須・asof で版を引ける・表の sha が決定的(口の約束 1-4)。

- リポの表 ``docs/design/rules-table.json`` は実在の規則 3 行(消費税の標準税率・東京都の最低賃金・深夜の酒類提供の
  住居集合地域での禁止)。数と出典は R-106(親検収済)と W7 の一次確認(等級 A)から写した=写し検査(CLAUDE.md §5)を
  ここでも機械で見る(法令 ID と版が答申の表の同じ行にある・URL が答申にある)。
- 1-4 では読み手を作らない(約束 (1))=表を import するのは manifest と日次の記録の 2 か所だけ(AST)。
- 凍結: 行・出典・値は書き換えられない(1-3 検収 L2・L7 の守り)。
"""

from __future__ import annotations

import ast
import dataclasses
import datetime as dt
import json
from pathlib import Path

import pytest

from shibuya.engine.rules import table as RT

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src" / "shibuya"
R106 = (ROOT / "docs" / "research" / "v2-r106-rights-institutions-tax-credit.md").read_text(encoding="utf-8")
W7 = (ROOT / "docs" / "research" / "v2-w7-law-primary-check-research.md").read_text(encoding="utf-8")


def _src(**kw) -> RT.Source:
    base = dict(law="最低賃金法", article="4 条", version="2025-06-01", url="https://example.invalid/x")
    base.update(kw)
    return RT.Source(**base)


def _rule(**kw) -> RT.Rule:
    base = dict(id="minimum_wage.tokyo", kind="machine", source=(_src(),), asof="2026-10-01",
                params={"yen_per_hour": 1280})
    base.update(kw)
    return RT.Rule(**base)


# ================================================================= リポの表
def test_the_repo_table_has_three_real_rules():
    rules = RT.default_rules()
    assert rules.ids() == ("consumption_tax.standard_rate", "late_night_alcohol.residential_ban", "minimum_wage.tokyo")
    assert len(rules) == 3
    for r in rules:
        assert r.kind in RT.KINDS and r.source
        for s in r.source:
            assert s.law and s.article and s.version and s.url.startswith("https://")


def test_the_values_are_the_r106_values():
    rules = RT.default_rules()
    tax = rules.get("consumption_tax.standard_rate", "2026-07-13")
    assert tax.kind == "machine" and tax.asof == "2019-10-01"
    assert tax.params["national_rate"] == 0.078 and tuple(tax.params["local_tax_ratio"]) == (22, 78)
    assert tax.params["combined_rate"] == pytest.approx(0.078 * (1 + 22 / 78))
    wage = rules.get("minimum_wage.tokyo", "2026-10-14")
    assert wage.kind == "machine" and wage.asof == "2026-10-01" and wage.params["yen_per_hour"] == 1280
    late = rules.get("late_night_alcohol.residential_ban", "2026-07-13")
    assert late.kind == "human"
    assert (late.params["closed_from"], late.params["closed_until"], late.params["area"]) == ("00:00", "06:00", "住居集合地域")
    assert late.applies_to == "plan.law_cap_key == 'shinya_shurui'"


def test_sources_are_copied_from_the_research_tables():
    """写し検査: e-Gov の法令 ID と版は R-106 §0-2 の表の同じ行にある・URL は答申の本文にある。"""
    rows = {line.split("|")[2].strip(): line for line in R106.splitlines() if line.startswith("| ") and line.count("|") >= 5}
    for r in RT.default_rules():
        for s in r.source:
            if s.law_id:
                assert s.law_id in rows, (r.id, s.law_id)
                assert s.version in rows[s.law_id], (r.id, s.law_id, s.version)
                assert s.url == f"https://laws.e-gov.go.jp/api/2/law_data/{s.law_id}?asof={s.version}"
            else:
                bare = s.url.removeprefix("https://")
                assert s.url in R106 or bare in W7, (r.id, s.url)
    # 条例 15 条の時間帯の逐語は W7 の一次確認の表にある
    assert "午前零時から午前六時までの時間において営んではならない" in W7


def test_the_table_sha_is_deterministic_and_is_the_rules_version(tmp_path):
    doc = json.loads(RT.default_path().read_text(encoding="utf-8"))
    a = RT.load(RT.default_path())
    p = tmp_path / "t.json"
    p.write_bytes(json.dumps(doc, ensure_ascii=False, indent=4).replace("\n", "\r\n").encode("utf-8"))
    b = RT.load(p)  # 書式と改行が違っても同じ
    assert a.sha == b.sha == RT.canonical_sha(doc) == RT.rules_version()
    assert len(a.sha) == 16 and int(a.sha, 16) >= 0
    doc["rules"][1]["params"]["yen_per_hour"] = 1281
    p.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    assert RT.load(p).sha != a.sha


# ================================================================= asof で版を引く
def test_get_returns_the_version_in_force_on_the_day():
    rules = RT.Rules([
        _rule(asof="2025-10-03", params={"yen_per_hour": 1226}),
        _rule(asof="2026-10-01", params={"yen_per_hour": 1280}),
    ])
    assert rules.get("minimum_wage.tokyo", "2026-07-13").params["yen_per_hour"] == 1226
    assert rules.get("minimum_wage.tokyo", dt.date(2026, 7, 13)).params["yen_per_hour"] == 1226
    assert rules.get("minimum_wage.tokyo", "2026-09-30").params["yen_per_hour"] == 1226
    assert rules.get("minimum_wage.tokyo", "2026-10-01").params["yen_per_hour"] == 1280
    assert rules.get("minimum_wage.tokyo", "2030-01-01").params["yen_per_hour"] == 1280
    assert [r.asof for r in rules.versions("minimum_wage.tokyo")] == ["2025-10-03", "2026-10-01"]
    with pytest.raises(RT.RuleNotInForce):
        rules.get("minimum_wage.tokyo", "2025-10-02")
    with pytest.raises(KeyError):
        rules.get("no.such_rule", "2026-07-13")
    with pytest.raises(ValueError):
        rules.get("minimum_wage.tokyo", "2026/07/13")


def test_the_repo_minimum_wage_has_no_version_on_the_world_date():
    """世界の時点 2026-07-13 の 1,226 円は R-106 で △ なので表に無い=その日に引くと版が無い(4-2 で足す)。"""
    with pytest.raises(RT.RuleNotInForce):
        RT.default_rules().get("minimum_wage.tokyo", "2026-07-13")


def test_two_rows_with_the_same_id_and_asof_are_refused():
    with pytest.raises(ValueError):
        RT.Rules([_rule(), _rule()])


# ================================================================= 出典と版は必須
@pytest.mark.parametrize("field", ["law", "article", "version", "url"])
def test_a_source_needs_law_article_version_and_url(field):
    with pytest.raises(ValueError):
        _src(**{field: ""})
    with pytest.raises(ValueError):
        _src(**{field: "   "})


def test_a_source_url_is_https_and_retrieved_is_a_date():
    with pytest.raises(ValueError):
        _src(url="http://example.invalid/x")
    with pytest.raises(ValueError):
        _src(retrieved="昨日")
    assert _src(retrieved="2026-10-12").retrieved == "2026-10-12"


@pytest.mark.parametrize("bad", [
    dict(source=()), dict(source=("消費税法",)), dict(kind="police"), dict(asof="2026-13-01"), dict(id="Bad Id"),
    dict(params={"x": {1, 2}}), dict(params=[1]), dict(applies_to=None),
])
def test_bad_rules_are_refused(bad):
    with pytest.raises((ValueError, TypeError)):
        _rule(**bad)


def test_from_dict_refuses_unknown_and_missing_fields():
    d = _rule().as_dict()
    assert RT.Rule.from_dict(d) == _rule()
    with pytest.raises(ValueError):
        RT.Rule.from_dict({**d, "extra": 1})
    for k in ("id", "kind", "asof", "source"):
        with pytest.raises(ValueError):
            RT.Rule.from_dict({x: v for x, v in d.items() if x != k})


def test_load_refuses_another_schema(tmp_path):
    p = tmp_path / "t.json"
    p.write_text(json.dumps({"schema": "x/1", "rules": []}), encoding="utf-8")
    with pytest.raises(ValueError):
        RT.load(p)


# ================================================================= 凍結
def test_rows_sources_and_params_are_frozen():
    r = _rule(params={"yen_per_hour": 1280, "bands": [1, 2], "nested": {"a": [3]}})
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.asof = "2027-01-01"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.source[0].url = "https://x"  # type: ignore[misc]
    with pytest.raises(TypeError):
        r.params["yen_per_hour"] = 1  # type: ignore[index]
    with pytest.raises(TypeError):
        r.params["nested"]["a"] = 1  # type: ignore[index]
    assert r.params["bands"] == (1, 2)
    assert not hasattr(r, "__dict__")


def test_the_table_object_cannot_be_rewired():
    rules = RT.default_rules()
    with pytest.raises(AttributeError):
        rules._by_id = {}  # type: ignore[misc]
    with pytest.raises(AttributeError):
        rules.extra = 1  # type: ignore[attr-defined]
    with pytest.raises(AttributeError):
        del rules._sha
    with pytest.raises(TypeError):
        rules._by_id["x"] = ()  # type: ignore[index]


# ================================================================= 1-4 では読み手を作らない
TARGET = "shibuya.engine.rules"


def _imports_target(node: ast.AST, module_of_file: str) -> bool:
    """``import shibuya.engine.rules…``・``from shibuya.engine.rules… import``・``from shibuya.engine import rules``・
    相対 import(``from .rules import table``・``from ..engine import rules``)を見る(検収 L8)。"""
    if isinstance(node, ast.Import):
        return any(a.name == TARGET or a.name.startswith(TARGET + ".") for a in node.names)
    if not isinstance(node, ast.ImportFrom):
        return False
    if node.level:
        base = module_of_file.split(".")[: -node.level]
        mod = ".".join(base + ([node.module] if node.module else []))
    else:
        mod = node.module or ""
    if mod == TARGET or mod.startswith(TARGET + "."):
        return True
    return any(f"{mod}.{a.name}" == TARGET for a in node.names)


def _readers() -> set[str]:
    out = set()
    for p in SRC.rglob("*.py"):
        rel = p.relative_to(SRC).as_posix()
        if rel.startswith("engine/rules/"):
            continue
        parts = ["shibuya", *rel.removesuffix(".py").split("/")]
        if parts[-1] == "__init__":
            parts = parts[:-1] + ["__init__"]  # パッケージの __init__ は自分のパッケージが基準(level 1 で親を落とす)
        module_of_file = ".".join(parts)
        if any(_imports_target(n, module_of_file) for n in ast.walk(ast.parse(p.read_text(encoding="utf-8")))):
            out.add(rel)
    return out


def test_only_the_manifest_and_the_daily_record_import_the_table():
    """約束 (1): 規則の表を読んでも挙動は変わらない=読むのは manifest(run.py)と日次の記録(state_io.py)と、ランの始めに
    壊れた表で落とすための組み立て(systems/build.py=読むだけ・検収 L10)だけ。"""
    assert _readers() == {"engine/run.py", "engine/systems/state_io.py", "engine/systems/build.py"}


@pytest.mark.parametrize("src,module", [
    ("from shibuya.engine import rules\n", "shibuya.engine.x"),
    ("from shibuya.engine.rules import table\n", "shibuya.engine.x"),
    ("import shibuya.engine.rules.table as T\n", "shibuya.engine.x"),
    ("from .rules import table\n", "shibuya.engine.x"),
    ("from ..rules.table import Rules\n", "shibuya.engine.systems.x"),
    ("from .. import rules\n", "shibuya.engine.systems.x"),
])
def test_the_reader_check_sees_every_import_form(src, module):
    """検収 L8 の負の対照: 別名・相対の import も読み手として見つかる。"""
    assert any(_imports_target(n, module) for n in ast.walk(ast.parse(src)))
    assert not any(_imports_target(n, module) for n in ast.walk(ast.parse("from shibuya.engine import run\n")))
