"""第 1 期 1-2 知覚の分離: ``perception.facts.Percept`` の形(口の約束 1-2・回答 10-13b §4-2)。

見るもの
(a) 欄の名と並び(凍結)・凍結の dataclass(書けない・slots)・下の記録(見えた物・人・音・時刻の見方・体の段ほか)も凍結
(b) 欄だけの 9 欄(``EMPTY_FIELDS``)は値が空(None)=描画が作る ``Percept`` でも空
(c) 事実の中身が状態と描画に合う(見えた人=B5 の近接行の人と並び・時刻の見方・体の段・自分の状態・見えた物)
(d) ``EventRef`` は出来事の記録の ``EventId`` と同じ形・判断の入力の形(``PerceptCarrier``)・描き方の口(``PerceptDrawing``)
(e) manifest の計器(欄の数・空の欄の一覧・係数の腕)
"""

from __future__ import annotations

import dataclasses
import typing
from datetime import timedelta

import numpy as np
import pytest

from shibuya.agents.state import INTEROCEPTION_FIELDS, IntentKind
from shibuya.perception import facts as F
from shibuya.perception import normalize as N
from shibuya.perception import renderer as R
from shibuya.perception import templates as T
from tests.perception.facts.scenes import build

#: 欄の名と並び(凍結。足したら ``PERCEPT_SCHEMA`` を上げて記録に書く)。
FIELDS = (
    "agent_id", "step", "t_ns", "cell", "self_view", "seen_objects", "seen_people", "sounds", "time_view", "body",
    "wake", "intent", "memories", "signage_shown", "watched_n", "scene",
    "eye_dir", "mind_dir", "belongings", "tool_state", "watched_by", "heard_speech", "nearby_change",
    "acquaintance_seen", "prediction",
    "heard_referents",  # 〔第 6 期 6-5〕話し手が指した相手の見えない ID(空の欄・版 /2)
)
EMPTY = ("eye_dir", "mind_dir", "belongings", "tool_state", "watched_by", "heard_speech", "nearby_change",
         "acquaintance_seen", "prediction", "heard_referents")


def _render_some(n_ticks: int = 3):
    w, a = build(n_agents=80, seed=3)
    r = R.Renderer(w, a, seed=5)
    outs = []
    for t in (480, 750, 1140)[:n_ticks]:
        r.prepare_tick(t)
        outs += [r.render(i, tick=t, wake_reason=3) for i in range(0, a.n, 4)]
    return w, a, r, outs


# ---------------------------------------------------------------- (a)
def test_fields_and_order_are_frozen():
    assert F.percept_fields() == FIELDS
    assert F.EMPTY_FIELDS == EMPTY
    assert set(EMPTY) <= set(FIELDS)
    assert F.PERCEPT_SCHEMA == "shibuya.perception/percept/2"  # 〔6-5〕/1 → /2


@pytest.mark.parametrize("cls", [F.Percept, F.SeenObject, F.SeenPerson, F.Sound, F.TimeView, F.BodyView, F.SelfView,
                                 F.IntentView, F.WakeView, F.SceneView])
def test_records_are_frozen_with_slots(cls):
    params = getattr(cls, "__dataclass_params__")
    assert params.frozen
    assert "__slots__" in vars(cls)
    assert not hasattr(cls, "__dict__") or "__dict__" not in vars(cls)


def test_percept_cannot_be_written():
    _w, _a, _r, outs = _render_some(1)
    p = outs[0].percept
    with pytest.raises(dataclasses.FrozenInstanceError):
        p.cell = 3  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        p.time_view.tod_s = 0  # type: ignore[misc]
    with pytest.raises((AttributeError, TypeError)):
        p.new_field = 1  # type: ignore[attr-defined]


def test_brief_fields_carry_the_named_parts():
    """発注の欄: 見えた物(id・種類・距離・向き)・見えた人(id・向き・行為)・音(段)・時刻の見方(日の中の秒・暦の日の種類)・
    体の段(空腹・疲れ・暑さ)。"""
    names = lambda c: [f.name for f in dataclasses.fields(c)]  # noqa: E731
    assert names(F.SeenObject)[:4] == ["id", "kind", "distance_m", "direction"]
    assert names(F.SeenPerson)[:3] == ["id", "direction", "action"]
    assert names(F.Sound) == ["kind", "stage"]
    assert names(F.TimeView)[:2] == ["tod_s", "day_kind"]
    assert names(F.BodyView) == ["hunger", "fatigue", "thermal", "hunger_stage", "fatigue_stage", "thermal_stage"]
    assert tuple(names(F.BodyView)[:3]) == tuple(INTEROCEPTION_FIELDS)  # 描画は内受容の名で引く


# ---------------------------------------------------------------- (b)
def test_empty_fields_default_to_none():
    defaults = {f.name: f.default for f in dataclasses.fields(F.Percept)}
    assert all(defaults[k] is None for k in EMPTY)
    # 欄だけの 9 欄以外には既定値が無い(作る側が必ず埋める)
    assert all(defaults[k] is dataclasses.MISSING for k in FIELDS if k not in EMPTY)


def test_rendered_percepts_have_the_empty_fields_empty():
    _w, _a, _r, outs = _render_some()
    assert outs
    for out in outs:
        p = out.percept
        assert isinstance(p, F.Percept)
        assert all(getattr(p, k) is None for k in EMPTY), [k for k in EMPTY if getattr(p, k) is not None]


# ---------------------------------------------------------------- (c)
def test_seen_people_are_the_near_line_in_order():
    _w, _a, _r, outs = _render_some()
    marks = T.NEAR_PERSON_MARKS
    for out in outs:
        p = out.percept
        b5 = out.blocks["B5"].decode("utf-8")
        line = next(x for x in b5.split("\n") if x.startswith("[B5 近接]"))
        if p.seen_people:
            items = [f"P-{sp.id}({marks[1] if sp.acquainted else marks[0]})" for sp in p.seen_people]
            fmt = lambda xs: T.TEMPLATES["B5.near_person"].format(items=N.LIST_SEPARATOR.join(xs))  # noqa: E731
            assert line == fmt(items) or any(line == fmt(items[:k]) for k in range(1, len(items)))  # 枠の切り詰め
        else:
            assert line == T.TEMPLATES["B5.near_person_empty"]
        assert all(sp.direction is None for sp in p.seen_people)
        assert all(sp.distance_m >= 0.1 for sp in p.seen_people)


def test_facts_match_the_state():
    w, a, r, outs = _render_some()
    for out in outs:
        p = out.percept
        i = p.agent_id
        assert (p.cell, p.self_view.kind, p.self_view.money) == (int(a.cell[i]), int(a.kind[i]), int(a.money[i]))
        assert p.self_view.hands_full == (int(a.holdings[i]) > 0)
        assert p.self_view.activity == int(a.activity[i])
        for nm in INTEROCEPTION_FIELDS:
            v = int(getattr(a, nm)[i])
            assert getattr(p.body, nm) == v
            assert getattr(p.body, f"{nm}_stage") == sum(1 for e in R.INTERO_UP_EDGES if v >= e)
        for sp in p.seen_people:
            assert sp.action == int(a.activity[sp.id]) and int(a.cell[sp.id]) == p.cell
        when = r.clock_fn(p.step)
        assert p.time_view.tod_s == when.hour * 3_600 + when.minute * 60 + when.second
        assert p.t_ns == (when - r.clock_fn(0)) // timedelta(microseconds=1) * 1_000
        assert (p.time_view.hour, p.time_view.minute) == (when.hour, when.minute // 5 * 5)
        assert p.time_view.day_kind is None  # 暦の口を渡していない描画
        # 見えた物: そのセルの店と目印(+注視を通った看板)
        pois = [o.id for o in p.seen_objects if o.kind == "poi"]
        assert pois == list(r.assets.visible_poi[p.cell])
        sig = [o.id for o in p.seen_objects if o.kind == "signage"]
        assert sig == ([p.scene.signage_poi] if p.scene.signage_poi >= 0 else [])
        assert p.sounds == p.scene.sounds and p.sounds[0].kind == "noise"
        assert all(o.distance_m is None and o.direction is None for o in p.seen_objects)


def test_day_kind_comes_from_the_calendar_hook_and_does_not_touch_bytes():
    w, a = build(n_agents=30, seed=4)
    plain = R.Renderer(w, a, seed=1)
    hooked = R.Renderer(w, a, seed=1, day_kind_fn=lambda T_: "saturday" if T_ >= 1_440 else "weekday")
    for t in (700, 1_500):
        x, y = plain.render(0, tick=t), hooked.render(0, tick=t)
        assert x.text == y.text
        assert y.percept.time_view.day_kind == ("saturday" if t >= 1_440 else "weekday")


def test_intent_wake_and_memories_are_carried():
    w, a = build(n_agents=40, seed=6)
    a2 = a
    r = R.Renderer(w, a2, seed=1)
    r.memory_recall = lambda i, t, c, inv: []  # 想起の口あり・0 件
    with a2.writable():
        a2.intent_action[0] = 3
        a2.intent_kind[0] = int(IntentKind.POI_NAMED)
        a2.intent_target[0] = 1
    p = r.render(0, tick=760, wake_reason=5, inviter=7).percept
    assert p.intent == F.IntentView(action=3, target_kind=int(IntentKind.POI_NAMED), target=1)
    assert p.memories == ()
    assert (p.wake.reason, p.wake.inviter) == (5, 7)
    q = r.render(1, tick=760, wake_reason="文言の理由").percept
    assert q.wake.reason == "文言の理由" and q.wake.inviter is None and q.intent is None
    r.memory_recall = None
    assert r.render(2, tick=760).percept.memories is None


# ---------------------------------------------------------------- (d)
def test_event_ref_has_the_shape_of_the_event_id():
    from shibuya.engine.events.log import EventId

    assert F.EventRef == EventId == tuple[int, int]
    hint = typing.get_type_hints(F.Percept, globalns=vars(F))["heard_speech"]
    assert F.EventRef in typing.get_args(hint) or tuple[F.EventRef, ...] in typing.get_args(hint)


def test_decision_input_shape_and_drawing_port():
    _w, _a, r, outs = _render_some(1)
    p = outs[0].percept

    @dataclasses.dataclass(frozen=True)
    class Ctx:  # 1-8 の DecisionPort.choose(ctx, …) の ctx の形(型だけ)
        percept: F.Percept

    ctx = Ctx(F.with_prediction(p, {"next_cell": 3}))
    assert isinstance(ctx, F.PerceptCarrier)
    assert ctx.percept.prediction == {"next_cell": 3}
    assert dataclasses.replace(ctx.percept, prediction=None) == p  # 予想の欄だけが違う
    assert isinstance(r, F.PerceptDrawing)
    assert r.draw(p) == outs[0].text


# ---------------------------------------------------------------- (e)
def test_manifest_instrument():
    m = F.percept_manifest()
    assert m == {
        "schema": F.PERCEPT_SCHEMA, "n_fields": len(FIELDS), "fields": list(FIELDS), "empty_fields": list(EMPTY),
        "n_empty_fields": len(EMPTY),
    }


def test_run_manifest_has_the_percept_section():
    from shibuya.engine.run import run_day

    res = run_day(n_agents=60, seed=2, ticks=90, n_cells=9, processes=False)
    m = res.run_manifest_fields()
    assert m["percept"] == F.percept_manifest()
    keys = list(m)
    # 末尾=T0 の TM9 → 1-4 の欄 → 1-9 の economy → 1-2 → 1-5 の rights → 1-8 J0 の decision_port → 1-7 の tools
    # → 1-8b の speech_port → 2-2 の proximity → 3-3 の experiment → 〔第 3 期 3-2〕batching → 〔第 3 期 3-5〕body → 〔第 3 期 3-1〕calendar_shadow(列追加のみ)
    assert keys[-11:] == ["economy", "percept", "rights", "decision_port", "tools", "speech_port", "proximity",
                          "experiment", "batching", "body", "calendar_shadow"]
    assert np.isfinite(m["percept"]["n_fields"])
