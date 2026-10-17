"""第 1 期 1-7 道具の台帳 C0(CT0・CT9): 看板の文の「作り物」の印は記録にだけ(描画のバイトは変えない)。

口の約束 1-7 の約束 (3)。看板を読んだ出来事(``道具:看板``)に ``origin="signboard:synthetic"``(つなぎの台帳
``BR-SIGNAGE-FICTION``)を付ける。腕 ``SHIBUYA_TOOL_EVENTS``(既定 off)のランだけ書く。

見るもの: 口の単体(欄=1-3 の via・received_ns/read_ns・origin・原因)/ 腕の on と off で final・呼数・描画の全部のバイト
(本文・ブロック・指紋)が同じ / on の記録の行=看板の見えた描画の数・欄の値 / 日次の記録の差は ``道具:看板`` だけ /
既定は書かない / 出来事の記録が off なら口を作らない / decide の宣言を外すと書いた所で止まる。
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from shibuya.core import write_permit as WP
from shibuya.engine.bridging import ledger as BR
from shibuya.engine.events import log as EV
from shibuya.engine.events import vocab as V
from shibuya.engine.run import run_day
from shibuya.engine.systems import overrides as OV
from shibuya.engine.tools import record as TR
from shibuya.engine.tools.registry import SIGNAGE_BRIDGE
from shibuya.perception import renderer as RD
from shibuya.perception.facts import SeenObject

KW = dict(n_agents=60, seed=2, n_cells=9, ticks=240, budget=60.0, sleep_suppression=False, vocab_version="v3",
          checkpoint_every=60)
WORLD_KW = dict(n_agents=2_000, seed=1, world_dir="data/world/v2", ticks=120, checkpoint_every=60)


@pytest.fixture(autouse=True)
def _arm_default():
    prev = TR.enabled()
    TR.set_enabled(False)
    yield
    TR.set_enabled(prev)


# ================================================================= 口の単体
def test_link_writes_one_marked_row_per_visible_signboard():
    log = EV.EventLog()
    log.begin_step(5_000)
    link = TR.SignboardReadLink(log)
    p_sign = SimpleNamespace(agent_id=7, t_ns=5_000, seen_objects=(
        SeenObject(id=3, kind="poi"), SeenObject(id=11, kind="signage")))
    p_none = SimpleNamespace(agent_id=8, t_ns=5_000, seen_objects=(SeenObject(id=-1, kind="landmark"),))
    assert link({7: p_sign, 8: p_none}) == 1
    (e,) = list(log.events())
    assert (e.who, e.what, e.where, e.via, e.received_ns, e.read_ns, e.origin, e.cause) == (
        7, "道具:看板", ("poi", 11), "無し", 5_000, 5_000, "signboard:synthetic", EV.Process("perception"))
    off = EV.EventLog(enabled=False)
    assert TR.SignboardReadLink(off)({7: p_sign}) == 0 and len(off) == 0
    with pytest.raises(TypeError):
        TR.SignboardReadLink(object())  # type: ignore[arg-type]


def test_the_mark_is_tied_to_the_ledger_and_the_vocab():
    assert TR.SIGNBOARD_ORIGIN == "signboard:synthetic" and TR.SIGNBOARD_WHAT in V.VOCAB_CODES
    assert SIGNAGE_BRIDGE in {b.id for b in BR.default_ledger().active()}
    assert V.VIA_NONE == "無し" and V.VIA_WORDS[:5] == ("対面", "通話", "メッセージ", "グループ", "SNS")  # 新しい欄・語は無い
    assert EV.EVENT_FIELDS == ("id", "t_ns", "who", "what", "whom", "where", "how_much", "via", "received_ns",
                               "read_ns", "origin", "cause")


# ================================================================= ラン: 腕の on/off で描画のバイトは同じ
def _render_spy(monkeypatch):  # noqa: ANN001
    seen: list[tuple] = []
    orig = RD.Renderer.render

    def render(self, *a, **kw):  # noqa: ANN001
        out = orig(self, *a, **kw)
        p = out.percept
        sig = [int(o.id) for o in p.seen_objects if o.kind == "signage"]
        blocks = hashlib.sha256(repr(out.blocks).encode("utf-8")).hexdigest()
        seen.append((int(p.step), int(p.agent_id), hashlib.sha256(out.text.encode("utf-8")).hexdigest(), blocks,
                     str(out.prompt_hash), tuple(sig)))
        return out

    monkeypatch.setattr(RD.Renderer, "render", render)
    return seen


def _rows(res) -> list:  # noqa: ANN001
    return [e for e in res.event_log.events() if e.what == TR.SIGNBOARD_WHAT]


def _pair(monkeypatch, run, kw):  # noqa: ANN001
    with monkeypatch.context() as m:
        seen_off = _render_spy(m)
        off = run(**kw)
    TR.set_enabled(True)
    with monkeypatch.context() as m:
        seen_on = _render_spy(m)
        on = run(**kw)
    TR.set_enabled(False)
    return off, seen_off, on, seen_on


def _check_pair(off, seen_off, on, seen_on) -> int:  # noqa: ANN001
    assert on.final_hash == off.final_hash and on.llm_calls == off.llm_calls
    assert seen_on == seen_off and len(seen_on) > 0          # 描画の全部(本文・ブロック・指紋・看板の物)が同じ
    n_sign = sum(len(s[5]) for s in seen_on)
    rows = _rows(on)
    assert len(rows) == n_sign > 0 and _rows(off) == []
    for e in rows:
        assert (e.origin, e.via, e.cause) == (TR.SIGNBOARD_ORIGIN, V.VIA_NONE, TR.SIGNBOARD_CAUSE)
        assert e.received_ns == e.read_ns == e.t_ns and e.where[0] == "poi" and isinstance(e.who, int)
    want = sorted((s[1], p) for s in seen_on for p in s[5])
    assert sorted((int(e.who), int(e.where[1])) for e in rows) == want
    # 日次の記録の差は「道具:看板」の行だけ
    m_on, m_off = on.run_manifest_fields(), off.run_manifest_fields()
    for d_on, d_off in zip(m_on["daily"], m_off["daily"]):
        bw_on = dict(d_on["events"]["by_what"])
        k = bw_on.pop(TR.SIGNBOARD_WHAT, 0)
        assert bw_on == d_off["events"]["by_what"]
        assert d_on["events"]["rows"] - d_off["events"]["rows"] == k
    assert m_off["tools"]["signboard"] == {"origin": TR.SIGNBOARD_ORIGIN, "bridge": SIGNAGE_BRIDGE,
                                           "what": TR.SIGNBOARD_WHAT, "events_arm": False, "read_events": 0}
    assert m_on["tools"]["signboard"]["events_arm"] and m_on["tools"]["signboard"]["read_events"] == n_sign
    assert list(m_on) == list(m_off)  # manifest の欄の並びは同じ(値の比べは記録の道具=c0/README.md §7)
    return n_sign


def test_synthetic_run_arm_on_and_off_render_the_same_bytes(monkeypatch):
    off, seen_off, on, seen_on = _pair(monkeypatch, run_day, KW)
    _check_pair(off, seen_off, on, seen_on)


@pytest.mark.requires_data("world_v2", "world_v2:w14_signage.parquet")
def test_world_run_arm_on_and_off_render_the_same_bytes(monkeypatch):
    from shibuya import cli

    off, seen_off, on, seen_on = _pair(monkeypatch, cli.run, WORLD_KW)
    n = _check_pair(off, seen_off, on, seen_on)
    n_poi = int(on.world.n_poi)
    assert all(0 <= int(e.where[1]) < n_poi for e in _rows(on)) and n > 0


# ================================================================= 既定・切替口・宣言
def test_default_run_writes_nothing_and_has_no_link():
    res = run_day(**KW)
    assert _rows(res) == [] and res.run_manifest_fields()["tools"]["signboard"]["events_arm"] is False


def test_no_link_when_the_event_log_is_off():
    TR.set_enabled(True)
    prev = EV.enabled()
    EV.set_enabled(False)
    try:
        res = run_day(**KW)
    finally:
        EV.set_enabled(prev)
    assert res.run_manifest_fields()["tools"]["signboard"]["events_arm"] is False and len(res.event_log) == 0


def test_undeclared_write_from_decide_fails_at_run_time():
    TR.set_enabled(True)
    prev = WP.enabled()
    WP.set_enabled(True)
    try:
        with OV.drop_path("decide", "E:events.*"):
            with pytest.raises(PermissionError, match="系 decide は出来事の記録"):
                run_day(**KW)
    finally:
        WP.set_enabled(prev)


def test_arm_reads_the_environment_value():
    assert TR.ARM_ENV == "SHIBUYA_TOOL_EVENTS"
    assert [TR.arm_from_env(v) for v in ("on", "ON", " 1 ", "true", "yes")] == [True] * 5
    assert [TR.arm_from_env(v) for v in (None, "", "off", "0", "no", "of")] == [False] * 6
