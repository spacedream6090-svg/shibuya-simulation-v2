"""第 1 期 1-6 記憶の器 M0: 描き方の口 ``render_memories`` が今の描き方とバイトで同じ(``test_m0_render_bytes``)。

- 腕 on のランの全部の描画で、器が返した ``MemoryView``(想起の結果)を ``render_memories`` で文にすると、描画が B5 の
  最後に載せた「記憶」の 1 行とバイトで同じ(個体枠で末尾の項を削った呼び出しは、載せた項の数までの ``MemoryView``)。
- 腕 on/off で描画の B5 の本文が全部同じ(想起が同じ=描画のバイトも同じ)。
- 1-2 の ``Percept`` への結線は 1-2 の取り込みの後(本段は口だけ)。
"""

from __future__ import annotations

import pytest

from shibuya.core.time_consts import NS_PER_STEP
from shibuya.engine.llm_bridge import PerceptionRendererAdapter
from shibuya.engine import memory_store as MS
from shibuya.engine.run import run_day

from tests.engine.memory._m0 import KW, run_with_arm


def _capture(monkeypatch, store: bool):
    renders: list[tuple[int, int, str, tuple[int, ...]]] = []
    views: dict[tuple[int, int], tuple[MS.MemoryView, ...]] = {}
    ctx: dict = {}
    orig_render = PerceptionRendererAdapter.render
    orig_recall = MS.MemoryStore.recall

    def render(self, **kw):  # noqa: ANN001, ANN202
        out = orig_render(self, **kw)
        ctx["renderer"] = self.renderer
        renders.append((int(kw["agent_id"]), int(kw["tick"]), out.b5_text, tuple(out.recalled_rows)))
        return out

    def recall(self, agent, t_ns, k, **kw):  # noqa: ANN001, ANN202
        got = orig_recall(self, agent, t_ns, k, **kw)
        views[(int(agent), int(t_ns))] = got
        return got

    monkeypatch.setattr(PerceptionRendererAdapter, "render", render)
    if store:
        monkeypatch.setattr(MS.MemoryStore, "recall", recall)
    return renders, views, ctx


@pytest.mark.parametrize("store_memory", ["on", "off"])
def test_render_memories_equals_the_b5_memory_line(monkeypatch, store_memory):
    kw = dict(KW, store_memory=store_memory)
    renders, views, ctx = _capture(monkeypatch, store=True)
    run_with_arm("events", run_day, **kw)
    rnd = ctx["renderer"]
    compared = 0
    for agent, step, b5, rows in renders:
        if not rows:
            continue
        vs = views[(agent, step * NS_PER_STEP)]
        line = MS.render_memories(vs[: len(rows)], clock=rnd.clock_fn, poi_names=rnd.assets.poi_name,
                                  place_ids=rnd.assets.place_ids, now_ns=step * NS_PER_STEP)
        assert line and b5.split("\n")[-1] == line, (agent, step)
        assert line.encode("utf-8") == b5.encode("utf-8").split(b"\n")[-1]
        compared += 1
    assert compared > 50


def test_b5_text_is_the_same_with_and_without_the_store(monkeypatch):
    on_renders, _v, _c = _capture(monkeypatch, store=False)
    run_with_arm("events", run_day, **KW)
    on = list(on_renders)
    on_renders.clear()
    run_with_arm("mem", run_day, **KW)
    off = list(on_renders)
    assert on == off and any(rows for *_x, rows in on)


def test_render_memories_edges():
    assert MS.render_memories((), clock=lambda s: None, poi_names=(), place_ids=()) == ""
    v = MS.MemoryView(row=0, event_id=(0, -1), origin="legacy", clarity="うろ覚え", grain="そのまま", kind=1,
                      partner=-1, obj=-1, result=0, cell=0, annotation="", when_ns=0, first_ns=0)
    with pytest.raises(ValueError, match="M0 の描き方"):
        MS.render_memories((v,), clock=lambda s: None, poi_names=(), place_ids=("P0",))
