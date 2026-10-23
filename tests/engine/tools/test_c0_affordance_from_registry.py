"""第 1 期 1-7 の 1-8 への結線: 候補の源「周りが示すできること」を道具の台帳から読む。

``DecisionLayer.affordance_words`` は、場所の種類と営業時間と知覚の読み(今のまま)に加えて、道具の台帳(``Fixtures.tools`` の
``ToolRegistry``)から「この体が知っていて・要るものが満たされ・今の世界で使う段」の道具を、道具 → 判断の語彙の語の凍結の表
``engine.tools.registry.TOOL_ACTION_WORDS`` で語に写して足す。**表は今は空**=候補の列は結線の前と同じ。

見るもの: 表が空なら語も候補も結線の前と同じ(層を直接呼ぶ単体・小さなランの候補の番号列と final)・負の対照(表に 1 語を仮に
入れると候補の源が増える)・知らない体には出ない・要るものが満たされない道具は出ない・登録だけの段の道具は出ない・組み立てが
``Fixtures.tools`` と同じ台帳を渡す。
"""

from __future__ import annotations

from types import MappingProxyType, SimpleNamespace

import numpy as np
import pytest

from shibuya.engine.decision import layer as DL
from shibuya.engine.decision.sources import build_candidates
from shibuya.engine.llm_bridge import ACTION_WORD_BY_CODE
from shibuya.engine.run import run_day
from shibuya.engine.tools import record as REC
from shibuya.engine.tools import registry as TR
from shibuya.engine.tools.registry import KnownBy, Tool, ToolRegistry
from shibuya.llm.contract import cross_action_words, safe_action_word
from tests.engine.decision._j0 import SMALL, ctx_of, decision_arm

V3 = cross_action_words("v3")


def _layer(tools) -> DL.DecisionLayer:  # noqa: ANN001
    return DL.DecisionLayer(port=SimpleNamespace(name="x"), vocab=V3, continue_word=safe_action_word("v3"),
                            word_of_code=ACTION_WORD_BY_CODE, tools=tools)


def _ctxs():  # noqa: ANN202
    seen = SimpleNamespace(seen_people=(1,), intent=None, memories=None, belongings=None)
    alone = SimpleNamespace(seen_people=(), intent=None, memories=None, belongings=None)
    return [ctx_of(agent_id=a, cell=-1, percept=p, inviter=inv) for a in (0, 3) for p in (seen, alone, None)
            for inv in (-1, 5)]


def _cands(layer, ctx):  # noqa: ANN001, ANN202
    return build_candidates(ctx, vocab=V3, continue_word=safe_action_word("v3"), word_of_code=ACTION_WORD_BY_CODE,
                            kind_words=layer.kind_words, affordance_words=layer.affordance_words)


def test_the_table_is_empty_and_frozen():
    assert isinstance(TR.TOOL_ACTION_WORDS, MappingProxyType) and len(TR.TOOL_ACTION_WORDS) == 0
    with pytest.raises(TypeError):
        TR.TOOL_ACTION_WORDS["看板"] = ("通報",)  # type: ignore[index]
    assert TR.affordance_words(TR.default_registry(), 0) == ()


def test_empty_table_gives_the_same_words_and_candidates_as_before():
    """表が空なら、道具の台帳を渡した層と渡さない層(結線の前=HEAD の形)で語も候補の列も同じ。"""
    with_tools, before = _layer(TR.default_registry()), _layer(None)
    for ctx in _ctxs():
        assert with_tools.affordance_words(ctx, V3) == before.affordance_words(ctx, V3)
        assert _cands(with_tools, ctx) == _cands(before, ctx)


def test_one_word_in_the_table_adds_a_candidate(monkeypatch):
    """負の対照: 表に 1 語を仮に入れると、その語が「周りが示すできること」の候補になる(源 vocab → affordance)。"""
    ctx = ctx_of(agent_id=0, cell=-1, percept=SimpleNamespace(seen_people=(), intent=None, memories=None,
                                                             belongings=None))
    layer = _layer(TR.default_registry())
    base = _cands(layer, ctx)
    assert {c.kind: c.source for c in base}["通報"] == "vocab"
    monkeypatch.setattr(TR, "TOOL_ACTION_WORDS", MappingProxyType({TR.SIGNBOARD: ("通報",)}))
    assert "通報" in layer.affordance_words(ctx, V3)
    after = _cands(layer, ctx)
    src = {c.kind: c.source for c in after}
    assert src["通報"] == "affordance"
    n_aff = lambda cs: sum(1 for c in cs if c.source == "affordance")  # noqa: E731
    assert n_aff(after) == n_aff(base) + 1 and len(after) == len(base)
    # 語彙に無い語は候補にならない(語彙の外の語を表に入れても足されない)
    monkeypatch.setattr(TR, "TOOL_ACTION_WORDS", MappingProxyType({TR.SIGNBOARD: ("看板を読む",)}))
    assert _cands(layer, ctx) == base


def _reg(*tools: Tool) -> ToolRegistry:
    return ToolRegistry(tools)


def test_unknown_agents_get_nothing(monkeypatch):
    monkeypatch.setattr(TR, "TOOL_ACTION_WORDS", MappingProxyType({"道具 A": ("通報",)}))
    reg = _reg(Tool(name="道具 A", owner="本人", content_writer="本人", known_by=KnownBy.of([3])))
    layer = _layer(reg)
    p = SimpleNamespace(seen_people=(), intent=None, memories=None, belongings=None)
    assert "通報" not in layer.affordance_words(ctx_of(agent_id=0, cell=-1, percept=p), V3)
    assert "通報" in layer.affordance_words(ctx_of(agent_id=3, cell=-1, percept=p), V3)
    assert reg.usable(0) == () and [t.name for t in reg.usable(3)] == ["道具 A"]


def test_unmet_requirements_hide_the_tool(monkeypatch):
    monkeypatch.setattr(TR, "TOOL_ACTION_WORDS", MappingProxyType({"道具 B": ("通報",)}))
    reg = _reg(Tool(name="道具 B", owner="本人", content_writer="本人", requires=("持ち物:携帯電話", "回線:電話の網")))
    layer = _layer(reg)
    none = SimpleNamespace(seen_people=(), intent=None, memories=None, belongings=None)
    half = SimpleNamespace(seen_people=(), intent=None, memories=None, belongings=("持ち物:携帯電話",))
    full = SimpleNamespace(seen_people=(), intent=None, memories=None,
                           belongings=("持ち物:携帯電話", "回線:電話の網"))
    assert "通報" not in layer.affordance_words(ctx_of(agent_id=0, cell=-1, percept=none), V3)  # 持ち物の台帳が無い=空
    assert "通報" not in layer.affordance_words(ctx_of(agent_id=0, cell=-1, percept=half), V3)
    assert "通報" in layer.affordance_words(ctx_of(agent_id=0, cell=-1, percept=full), V3)


def test_registered_only_tools_are_not_offered(monkeypatch):
    """登録だけの段(``stage`` が 6-4)の道具は、表に語があっても出ない(電話・乗換案内・地図ほか)。"""
    monkeypatch.setattr(TR, "TOOL_ACTION_WORDS", MappingProxyType({n: ("通報",) for n in TR.TOOL_NAMES
                                                                  if n not in (TR.SIGNBOARD, TR.NOTICE)}))
    reg = TR.default_registry()
    full = SimpleNamespace(seen_people=(), intent=None, memories=None,
                           belongings=tuple(r for t in reg for r in t.requires))
    assert "通報" not in _layer(reg).affordance_words(ctx_of(agent_id=0, cell=-1, percept=full), V3)
    assert [t.name for t in reg.usable(0, full.belongings)] == [TR.SIGNBOARD, TR.NOTICE]


# ================================================================= 組み立てとラン(腕 port)
def test_build_passes_the_fixture_registry_and_the_run_is_unchanged(monkeypatch):
    """組み立ては ``Fixtures.tools`` と同じ台帳を層に渡す。表が空なので、台帳を渡さない層(結線の前)と候補の番号列・
    源の分布・final・呼数が同じ(腕 port の小さなラン)。"""
    got: dict = {}
    real_fx, real_init = REC.build_fixture, DL.DecisionLayer.__init__

    def fx(*a, **kw):  # noqa: ANN001, ANN202
        got["fx"] = real_fx(*a, **kw)
        return got["fx"]

    def init(self, *a, **kw):  # noqa: ANN001
        real_init(self, *a, **kw)
        got["layer"] = self

    with decision_arm(DL.ARM_PORT):
        with monkeypatch.context() as m:
            m.setattr(REC, "build_fixture", fx)
            m.setattr(DL.DecisionLayer, "__init__", init)
            wired = run_day(**SMALL)
        assert got["layer"].tools is got["fx"].registry and got["layer"].tools is not None

        def init_none(self, *a, **kw):  # noqa: ANN001
            kw["tools"] = None
            real_init(self, *a, **kw)

        with monkeypatch.context() as m:
            m.setattr(DL.DecisionLayer, "__init__", init_none)
            before = run_day(**SMALL)
    mw, mb = wired.run_manifest_fields()["decision_port"], before.run_manifest_fields()["decision_port"]
    assert mw["decisions"] > 0
    for k in ("decisions", "chosen_number", "presented_by_source", "chosen_by_source", "n_candidates", "mismatch"):
        assert mw[k] == mb[k], k
    assert wired.final_hash == before.final_hash and wired.llm_calls == before.llm_calls
    assert np.array_equal(wired.agents.registry.activity, before.agents.registry.activity)
