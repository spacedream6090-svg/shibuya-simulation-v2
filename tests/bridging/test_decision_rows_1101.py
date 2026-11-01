"""第340 段 2 の 2: 判断ごとの行(``DEC-…``)とその欄(tools/ledger/add_decision_rows_1101.py)。

- routing §1 の 112 行が台帳に 1 行ずつある(id=``DEC-<#>-<英数>``・``routing_row``=#・行き先の件数が routing §2-1 と同じ)。
- 道具は冪等(いまの台帳に回しても 1 バイトも変わらない=本体の版の上で何度回しても同じ)。
- 既存の束の行(``HD-``)は消していない(85 行のまま)。土台の 673 行は中身ごと不変(id → 行の指紋を固定=検収 低-3)。
- 欄は ``Bridge`` の欄(``engine.bridging.ledger``)で読める(前の版の頭の鍵 ``row_fields`` は無い)。
"""

from __future__ import annotations

import collections
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_TOOL = ROOT / "tools" / "ledger" / "add_decision_rows_1101.py"
LEDGER = ROOT / "docs" / "design" / "bridging-ledger.json"


@pytest.fixture(scope="module")
def tool():
    spec = importlib.util.spec_from_file_location("add_decision_rows_1101", _TOOL)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def doc():
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def test_tool_is_idempotent_on_the_current_ledger(tool, doc):
    raw = LEDGER.read_bytes()
    again = tool.dumps(tool.build(json.loads(raw), tool.parse_routing(tool.ROUTING))).encode("utf-8")
    assert again == raw


def test_one_row_per_routing_decision(tool, doc):
    decs = [r for r in doc["bridges"] if r["id"].startswith("DEC-")]
    assert len(decs) == 112
    nums = []
    for r in decs:
        m = re.match(r"^DEC-(\d+)-([A-Za-z0-9]+)$", r["id"])
        assert m, r["id"]
        assert "open" not in r["id"].lower() and "tick" not in r["id"].lower()
        nums.append(int(m.group(1)))
        assert r["routing_row"] == int(m.group(1))
        assert r["declared_in"].endswith(f"§1 行 {m.group(1)}") and r["remove_basis"] == "inferred"
    assert nums == list(range(1, 113))
    # 行き先の件数(routing §2-1: L1 残す 9・L1.5 55・L2 7・初期の予定 8・代打 1・無い 6・要判断 26)
    dest = collections.Counter(re.search(r"行き先: (L1 残す|L1\.5|L2|初期の予定|代打|無いと宣言|要判断)", r["why"]).group(1)
                               for r in decs)
    assert dest == {"L1 残す": 9, "L1.5": 55, "L2": 7, "初期の予定": 8, "代打": 1, "無いと宣言": 6, "要判断": 26}


#: 土台の DEC 以外の行の指紋(id 順に並べた行の正規化 JSON の sha256)。固定した版の由来: 第340 段 2 の 5(規則の表・6a943af=
#: +1 行)と段 2 の 3・4(率の規則・ce52662=+4 行・13 行に注)の後の 678 行(=c0729a4 の 673+1+4)。並走の段がこの行を
#: 変えたら、変えた行を記録に書いてこの値を直す(前の値=c0729a4 の 673 行 3871dcc2…dd42c75bd)。
BASE_ROWS = 678
BASE_ROWS_SHA = "7130eb39a961f5154716eec965ef2808e9267d8b0e214088f43c3f3c1f5e81a7"


def test_base_rows_are_byte_identical(doc):
    base = sorted((r for r in doc["bridges"] if not r["id"].startswith("DEC-")), key=lambda r: r["id"])
    raw = json.dumps(base, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    assert len(base) == BASE_ROWS and hashlib.sha256(raw).hexdigest() == BASE_ROWS_SHA
    assert "row_fields" not in doc and "row_fields_note" not in doc
    assert all(not ({"drives_from", "routing_row", "world_process", "decided"} & set(r)) for r in base)


def test_rows_load_as_bridges_with_the_new_fields():
    from shibuya.engine.bridging import ledger as L

    led = L.load(LEDGER)
    r = led.get("DEC-109-driveCars")
    assert r.drives_from == ("data:road_census_r3",) and r.routing_row == 109 and r.world_process == "vehicle_cross_section"
    assert led.get("DEC-101-changePrice").calibration_declined == ("E7",)
    assert led.get("DEC-55-help").decided == "11-01/§10-1"
    assert {"11-01p-1", "11-01p-3", "11-01p-5"} <= L.PLAN_STAGES
    # 既存の行は欄が空で、as_dict は前と同じ形
    old = led.get("BR-W17-IO-SLEEP")
    assert old.drives_from == () and old.routing_row == 0 and "drives_from" not in old.as_dict()
    raw = {d["id"]: d for d in json.loads(LEDGER.read_text(encoding="utf-8"))["bridges"]}
    assert old.as_dict() == raw["BR-W17-IO-SLEEP"] and r.as_dict() == raw["DEC-109-driveCars"]


def test_existing_rows_are_kept(doc):
    rows = doc["bridges"]
    assert sum(1 for r in rows if r["id"].startswith("HD-")) == 85
    first_dec = next(i for i, r in enumerate(rows) if r["id"].startswith("DEC-"))
    assert all(r["id"].startswith("DEC-") for r in rows[first_dec:])
    assert first_dec >= BASE_ROWS  # 既存の行は前に・不変(並走の段が足した行も前に来る)


def test_pattern_columns_tool_is_idempotent_and_keeps_cells():
    spec = importlib.util.spec_from_file_location("add_pattern_columns_1101",
                                                  ROOT / "tools" / "ledger" / "add_pattern_columns_1101.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    md = (ROOT / "docs" / "design" / "v2-pattern-ledger.md").read_text(encoding="utf-8")
    again, n = mod.transform(md)
    assert (again, n) == (md, 0)
    # 列を足す前の形の表に回すと、既存のセルはそのままで末尾に 2 つ足す
    before = "## §9 x\n\n| 行 | パターン | 区分 |\n|---|---| --- |\n| W2 | 宅配 | 錨 |\n| F1 | 年齢 | 初期化 |\n"
    after, n = mod.transform(before)
    assert n == 1
    assert after.split("\n")[4] == "| W2 | 宅配 | 錨 | W2 | — |"
    assert after.split("\n")[5].startswith("| F1 | 年齢 | 初期化 | F1 | burned(")
    assert mod.transform(after) == (after, 0)
