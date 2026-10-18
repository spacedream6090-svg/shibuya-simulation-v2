"""第 1 期 1-7 道具の台帳 C0(CT0): 欄・凍結・書き換え不可・最初の中身・つなぎの台帳との結び・書く口は register だけ。

口の約束 1-7(``docs/design/v2-foundation-contracts-2026-10-13.md``)・決定 10-12 §4-4 CT0・§1-13・回答 10-13b §1 1-5。
"""

from __future__ import annotations

import ast
import dataclasses
import json
from pathlib import Path
from types import MappingProxyType

import pytest

from shibuya.engine.bridging import ledger as BR
from shibuya.engine.events import vocab as V
from shibuya.engine.tools import registry as TR
from shibuya.engine.tools.registry import EVERYONE, NOBODY, KnownBy, Tool, ToolRegistry

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src" / "shibuya"
REG_PATH = SRC / "engine" / "tools" / "registry.py"


def _tool(**kw) -> Tool:
    base = dict(name="試しの道具", owner="本人", content_writer="本人")
    base.update(kw)
    return Tool(**base)


# ================================================================= 欄と凍結
def test_fields_are_the_contract_six_then_the_extra_four():
    assert TR.TOOL_FIELDS[:6] == ("name", "known_by", "requires", "affects", "owner", "content_writer")
    assert TR.TOOL_FIELDS[6:] == ("modality", "content_origin", "stage", "bridge")
    assert TR.CONTENT_WRITERS == ("本人", "他人", "機械")
    assert TR.REQUIRE_KINDS == ("持ち物", "契約", "回線")


def test_tool_is_frozen_with_slots():
    t = _tool()
    with pytest.raises(dataclasses.FrozenInstanceError):
        t.name = "別の名"  # type: ignore[misc]
    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError, TypeError)):
        t.extra = 1  # type: ignore[attr-defined]
    assert not hasattr(t, "__dict__")
    # 既定: 全員が知っている・影響と音声表情の欄は空・中身の出どころは無し・今の世界で使う
    assert (t.known_by, t.affects, t.modality, t.content_origin, t.stage, t.bridge) == (
        EVERYONE, None, None, TR.ORIGIN_NONE, None, None)


def test_affects_becomes_read_only():
    t = _tool(affects={"目の向き": "画面"})
    assert isinstance(t.affects, MappingProxyType)
    with pytest.raises(TypeError):
        t.affects["目の向き"] = "前"  # type: ignore[index]


@pytest.mark.parametrize("kw,err", [
    ({"name": ""}, ValueError),
    ({"name": "  "}, ValueError),
    ({"requires": ("携帯電話",)}, ValueError),            # 種類の頭が無い
    ({"requires": ("財布:携帯電話",)}, ValueError),       # 種類の外
    ({"requires": ("持ち物:",)}, ValueError),            # 名が空
    ({"requires": ("持ち物:鍵", "持ち物:鍵")}, ValueError),  # 重複
    ({"owner": "誰か"}, ValueError),
    ({"content_writer": "神"}, ValueError),
    ({"content_origin": "推定"}, ValueError),
    ({"stage": "9-9"}, ValueError),                     # 計画の段の外
    ({"content_origin": "作り物"}, ValueError),          # 作り物はつなぎの行が要る
    ({"known_by": "all"}, TypeError),
    ({"affects": ["目"]}, TypeError),
    ({"modality": ("",)}, ValueError),
    ({"bridge": ""}, ValueError),
])
def test_invalid_rows_are_rejected(kw, err):
    with pytest.raises(err):
        _tool(**kw)


def test_known_by_kinds():
    assert EVERYONE.knows(0) and EVERYONE.knows(10**6)
    assert not NOBODY.knows(0)
    k = KnownBy.of([3, 5])
    assert k.knows(3) and not k.knows(4) and k.describe() == "set:2"
    with pytest.raises(ValueError):
        KnownBy("some")
    with pytest.raises(ValueError):
        KnownBy("all", frozenset({1}))
    with pytest.raises(ValueError):
        KnownBy.of([-1])
    with pytest.raises(TypeError):
        KnownBy("set", {1})  # type: ignore[arg-type]


# ================================================================= 台帳
def test_default_registry_contents():
    reg = TR.default_registry()
    # 〔第 6 期 6-2〕時計と天気予報を末尾に足した(決定 10-12 §4-4 CT0「天気予報と時計はカレンダー 1b と一緒」=段 6-2)
    assert reg.names == TR.TOOL_NAMES == ("看板", "掲示", "電話", "連絡先", "グループ", "乗換案内", "地図", "時計", "天気予報")
    assert len(reg) == 9 and all(isinstance(t, Tool) for t in reg)
    assert reg.in_use() == ("看板", "掲示")
    assert reg.registered_only() == ("電話", "連絡先", "グループ", "乗換案内", "地図", "時計", "天気予報")
    assert {reg.get(n).stage for n in reg.registered_only()} == {"6-4", "6-2"}  # 中身は第 6 期 C1〜・時計と天気予報は 6-2
    assert reg.get(TR.FORECAST).bridge == TR.FORECAST_BRIDGE and reg.get(TR.FORECAST).content_origin == TR.ORIGIN_NONE
    assert reg.get(TR.CLOCK).content_writer == "機械" and reg.get(TR.CLOCK).requires == ()
    sign = reg.get(TR.SIGNBOARD)
    assert (sign.content_origin, sign.bridge, sign.owner, sign.content_writer) == (
        TR.ORIGIN_SYNTHETIC, "BR-SIGNAGE-FICTION", "店", "他人")
    assert reg.get(TR.PHONE).bridge == "BR-PHONE-TABLE-BLANK"
    assert reg.get(TR.TRANSIT).content_writer == reg.get(TR.MAP).content_writer == "機械"
    assert all(t.known_by == EVERYONE and t.affects is None and t.modality is None for t in reg)  # C0 は欄だけ
    json.dumps([t.as_dict() for t in reg], ensure_ascii=False)
    # 呼ぶたびに新しい物
    assert TR.default_registry() is not reg


def test_bridges_of_the_tools_are_active_rows_of_the_ledger():
    led = BR.default_ledger()
    active = {b.id for b in led.active()}
    for t in TR.DEFAULT_TOOLS:
        if t.bridge is not None:
            assert t.bridge in active, t.name
    synth = [t for t in TR.DEFAULT_TOOLS if t.content_origin == TR.ORIGIN_SYNTHETIC]
    assert [t.name for t in synth] == ["看板"]


def test_register_adds_only():
    reg = ToolRegistry()
    assert len(reg) == 0
    before = reg.rows
    reg.register(_tool())
    assert len(reg) == 1 and "試しの道具" in reg and len(before) == 0  # 前に渡した表は変わらない
    with pytest.raises(ValueError, match="差し替えない"):
        reg.register(_tool(owner="店"))
    with pytest.raises(TypeError):
        reg.register({"name": "x"})  # type: ignore[arg-type]
    assert isinstance(reg.rows, MappingProxyType)
    with pytest.raises(TypeError):
        reg.rows["x"] = _tool(name="x")  # type: ignore[index]
    with pytest.raises(KeyError):
        reg.get("無い道具")


def test_registry_cannot_be_rewritten():
    reg = TR.default_registry()
    for name in ("rows", "_ToolRegistry__rows", "x"):
        with pytest.raises(AttributeError):
            setattr(reg, name, {})
        with pytest.raises(AttributeError):
            delattr(reg, name)
    with pytest.raises(AttributeError):
        object.__setattr__(reg, "_rows", {})  # 名の無い属性は置けない(slots)
    with pytest.raises(TypeError):
        vars(reg)
    assert not hasattr(reg, "__dict__")


def test_known_reads_the_row():
    reg = ToolRegistry([_tool(name="a"), _tool(name="b", known_by=KnownBy.of([2])), _tool(name="c", known_by=NOBODY)])
    assert reg.known(0, "a") and reg.known(2, "b") and not reg.known(1, "b") and not reg.known(0, "c")
    with pytest.raises(ValueError):
        reg.known(-1, "a")
    with pytest.raises(KeyError):
        reg.known(0, "d")


# ================================================================= 書く口は register だけ(AST・負の対照)
def _slot_writers(tree: ast.AST, cls_name: str, slot: str) -> list[str]:
    """クラス ``cls_name`` の中で名を変えた slot ``slot`` を置く所(メソッドの名)・クラスの外の参照。"""
    out: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == cls_name:
            for fn in node.body:
                if not isinstance(fn, ast.FunctionDef):
                    continue
                for c in ast.walk(fn):
                    if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and c.func.attr in (
                            "__setattr__", "__delattr__") and c.args[1:2] and isinstance(c.args[1], ast.Constant) \
                            and c.args[1].value == slot:
                        out.append(fn.name)
                    if isinstance(c, (ast.Assign, ast.AugAssign)):
                        tg = c.targets if isinstance(c, ast.Assign) else [c.target]
                        for t in tg:
                            if isinstance(t, ast.Attribute) and t.attr in (slot, "__rows"):
                                out.append(fn.name)
    return out


def test_only_init_and_register_rebind_the_rows():
    tree = ast.parse(REG_PATH.read_text(encoding="utf-8"))
    assert sorted(set(_slot_writers(tree, "ToolRegistry", "_ToolRegistry__rows"))) == ["__init__", "register"]
    # 公開の口で書くのは register だけ(ほかの公開のメソッドは slot を置かない)
    cls = next(c for c in ast.walk(tree) if isinstance(c, ast.ClassDef) and c.name == "ToolRegistry")
    pub = [f.name for f in cls.body if isinstance(f, ast.FunctionDef) and not f.name.startswith("_")]
    assert "register" in pub


def test_no_one_outside_touches_the_registry_slot():
    hits = []
    for p in sorted(SRC.rglob("*.py")):
        if p == REG_PATH:
            continue
        txt = p.read_text(encoding="utf-8")
        if "_ToolRegistry__rows" in txt or "ToolRegistry__" in txt:
            hits.append(p.relative_to(ROOT).as_posix())
    assert hits == []


def test_negative_control_second_writer_is_found():
    src = (
        "class ToolRegistry:\n"
        "    def __init__(self):\n"
        "        object.__setattr__(self, '_ToolRegistry__rows', {})\n"
        "    def register(self, t):\n"
        "        object.__setattr__(self, '_ToolRegistry__rows', {1: t})\n"
        "    def clear(self):\n"
        "        object.__setattr__(self, '_ToolRegistry__rows', {})\n"
        "    def reset(self):\n"
        "        self.__rows = {}\n"
    )
    assert sorted(set(_slot_writers(ast.parse(src), "ToolRegistry", "_ToolRegistry__rows"))) == [
        "__init__", "clear", "register", "reset"]


# ================================================================= 語彙の族「道具」との結び
def test_tool_words_are_names_of_the_registry_and_appended_at_the_end():
    assert set(V.TOOL_WORDS) <= set(TR.TOOL_NAMES)
    # 〔第 3 期 3-3〕族の並びに「実験」を足した・〔第 2 期 2-3〕その後ろに「知覚」を足した=道具は後ろから 3 つ目
    assert V.FAMILIES[-4] == V.FAMILY_TOOL == "道具" and V.FAMILIES[-3] == V.FAMILY_EXPERIMENT == "実験"
    assert V.FAMILIES[-2] == V.FAMILY_PERCEPT == "知覚"  # 〔第 6 期 6-4 C1〕その後ろに連絡の族
    assert V.FAMILIES[-1] == V.FAMILY_CONTACT == "連絡"
    assert V.VOCAB_CODES["行為:許可のない行動"] == 55 and V.VOCAB_CODES["道具:看板"] == 56  # 1-5 までのコードは動かない
    # 〔第 2 期 2-1〕知覚の名の後ろに経済の段階 2 の過程の名(payroll・atm・register)を足した(知覚の名の位置は動かない)
    assert V.PERCEPTION_PROCESSES == ("perception",)
    assert V.CAUSE_PROCESS_NAMES[len(V.PROCESS_NAMES) + len(V.CHECK_PROCESSES)] == "perception"
    assert V.CAUSE_PROCESS_NAMES[-6:-3] == V.ECONOMY_PROCESSES  # 〔第 2 期 2-3〕その後ろに体の過程の名 2 つ(〔6-4 C1〕その後ろに網の名 1 つ)
    assert "過程:perception" not in V.VOCAB_CODES
