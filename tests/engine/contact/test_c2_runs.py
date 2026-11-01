"""第 6 期 6-4 C2 ランの試験(合成の世界・腕 c1 の中): 既定 off は何も作らない・manifest の節(習慣・交換・充電・ビデオ)と
節の表・道具の台帳の行(腕のランだけ)・監査・習慣 off は判断の口だけ(閾値に届かない習慣 on と同じ選び)・記録 on/off で final と
checkpoint が同じ・日の途中の再開=通し(習慣の表・宛先の帳・充電を含む)・段 B・充電を外すと電源の切れた体が増える(負の対照)・
既読の印が候補の文に出る。"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from shibuya.core.time_consts import STEPS_PER_DAY
from shibuya.engine import manifest_sections as MS
from shibuya.engine import resume as RS
from shibuya.engine import state_ledger as SL
from shibuya.engine.contact import habit as HB
from shibuya.engine.contact import layer as LY
from shibuya.engine.contact import port as P
from shibuya.engine.contact import tools as TL
from shibuya.engine.events import log as EV
from shibuya.engine.run import run_day
from shibuya.engine.tools import record as TR
from shibuya.engine.tools.groups import GroupList

from tests.engine.contact._c1 import KW, STEP_NS, by_kind, c1, choose
from tests.engine.contact._c2 import Harness2, habit_arm, loud

TPD = int(STEPS_PER_DAY)


@pytest.fixture
def with_groups(monkeypatch):
    real = TR.build_fixture

    def build(pop, n_agents, events):
        fx = real(pop, n_agents, events)
        if fx.groups is not None:
            return fx
        ids = np.arange(int(n_agents))
        return dataclasses.replace(fx, groups=GroupList(household_id=ids // 2, org_id=ids // 10))

    monkeypatch.setattr(TR, "build_fixture", build)
    yield


def test_default_off_builds_nothing_and_counts_zero():
    with c1(on=False), habit_arm(True):  # 習慣の腕だけ立てても c1 が off なら何も作らない
        r = run_day(**dict(KW, ticks=120))
    m = r.run_manifest_fields()
    assert getattr(r, "contact_layer", "missing") is None and "contact_c1" not in m
    assert sum(1 for e in r.event_log.events() if str(e.what).startswith("連絡:")) == 0
    assert not set(TL.CONTACT_TOOL_NAMES) & set(m["tools"]["names"])  # 既定の台帳は今のまま


def test_c1_run_sections_tools_and_audit(with_groups):
    with c1(), habit_arm(True):
        r = run_day(**dict(KW, ticks=360))
    m = r.run_manifest_fields()
    cc = m["contact_c1"]
    assert set(cc) == set(LY.CONFIG_KEYS) | set(LY.OBSERVED_KEYS)
    assert {p.split(".", 1)[1] for p, s in MS.PATHS.items() if p.startswith("contact_c1.") and s == MS.CONFIG} \
        == set(LY.CONFIG_KEYS)
    assert {p.split(".", 1)[1] for p, s in MS.PATHS.items() if p.startswith("contact_c1.") and s == MS.OBSERVED} \
        == set(LY.OBSERVED_KEYS)
    assert MS.unlisted_in_mixed(m) == []
    assert cc["c2"]["habit_arm"] == "on" and cc["c2"]["place_numbers"] == 0 and cc["c2"]["tools"] == list(TL.CONTACT_TOOL_NAMES)
    hm = cc["habit"]["meter"]  # 〔問い 2〕範囲の中の体は判断の口へ(合成の世界の体は範囲の中)
    assert hm.get("habit:in_range:notice", 0) > 0 and cc["habit"]["book"]["agents"] > 0
    assert list(m["tools"]["names"])[-len(TL.CONTACT_TOOL_NAMES):] == list(TL.CONTACT_TOOL_NAMES)
    assert LY.audit_causes(r.event_log.events(), step_ns=STEP_NS, issued=r.contact_layer.issued_keys())["violations"] == 0


def _choices(r):
    """連絡の出来事(習慣で答えた原因の印を除いた中身)。"""
    return [(int(e.t_ns), str(e.who), e.what, str(e.whom), e.via) for e in r.event_log.events()
            if str(e.what).startswith("連絡:")]


def test_habit_records_do_not_move_anything_until_used(with_groups, monkeypatch):
    """習慣 off(判断の口だけ)と、閾値に届かない習慣 on(数えるだけ)は同じ選び・同じ出来事・同じ控え(数えるのは習慣の表だけ)。"""
    kw = dict(KW, ticks=360)
    with c1(), habit_arm(False):
        off = run_day(**kw)
    monkeypatch.setattr(HB, "HABIT_MIN_RECORDS", 10 ** 9)
    with c1(), habit_arm(True):
        on = run_day(**kw)
    assert _choices(off) == _choices(on) and _choices(off)
    assert np.array_equal(off.contact_layer.issued_keys(), on.contact_layer.issued_keys())
    assert off.contact_layer.habit._counts == {} and on.contact_layer.habit._counts
    assert on.run_manifest_fields()["contact_c1"]["habit"]["meter"].get("habit:answered:notice", 0) == 0


def test_event_log_on_off_same_with_habit(with_groups):
    kw = dict(KW, ticks=360)
    prev = EV.enabled()
    try:
        with c1(), habit_arm(True):
            EV.set_enabled(True)
            a = run_day(**kw)
            EV.set_enabled(False)
            b = run_day(**kw)
    finally:
        EV.set_enabled(prev)
    assert a.final_hash == b.final_hash
    assert [(c.tick, c.behavior_hash) for c in a.checkpoints] == [(c.tick, c.behavior_hash) for c in b.checkpoints]
    assert a.contact_layer.habit._counts == b.contact_layer.habit._counts


def _cp(r):
    return [(int(c.tick), c.behavior_hash, c.full_hash) for c in r.checkpoints if int(c.tick) >= TPD + 300]


def test_mid_day_resume_is_the_straight_run_with_c2_state(with_groups, tmp_path):
    kw = dict(KW, ticks=TPD, sim_days=2, checkpoint_every=60, relations="off")
    with c1(), habit_arm(True):
        straight = run_day(tape_path=tmp_path / "s", **kw)
        a = run_day(state_out=tmp_path / "state", stop_at_tick=TPD + 300, tape_path=tmp_path / "a", **kw)
        path = tmp_path / "state" / a.resume["state_files"][-1]["file"]
        b = run_day(resume_from=path, tape_path=tmp_path / "b", **kw)
    assert b.final_hash == straight.final_hash and _cp(b) == _cp(straight) and _cp(b)
    bundle = RS.read_state(path)
    for it in ("contact.habit._counts", "contact.book._exchanged", "contact.dev._plugged", "contact._defer_charge"):
        assert it in bundle.items, it
    assert bundle.header["fingerprint"]["contact"] == {"arm": "c1", "unnoticed": "i", "send": "b", "habit": "on"}
    ms, mb = straight.run_manifest_fields()["contact_c1"], b.run_manifest_fields()["contact_c1"]
    assert ms["habit"]["book"] == mb["habit"]["book"] and ms["exchange"]["book"] == mb["exchange"]["book"]
    assert ms["devices"] == mb["devices"]


def test_stage_b_with_c2(with_groups, monkeypatch):
    monkeypatch.setenv("SHIBUYA_SYSTEMS_CHECK", "1")
    with c1(), habit_arm(True):
        r = run_day(**dict(KW, ticks=360))
    m = r.run_manifest_fields()["contact_c1"]
    assert m["exchange"]["meter"].get("exchange:opportunities", 0) > 0  # 対面の会話の番の控え(判断の系 → 系 contact)


def test_charging_by_the_person_keeps_devices_alive(with_groups, monkeypatch):
    """4 日: 本人が充電するラン(mock)は、充電の判断を外したラン(負の対照)より電源の切れた体が少ない。"""
    kw = dict(KW, ticks=TPD, sim_days=4, relations="off", checkpoint_every=TPD)
    with c1():
        r = run_day(**kw)
    monkeypatch.setattr(LY.ContactLayer, "_charge_decisions", lambda self, T, t_ns, main_now: None)
    with c1():
        r0 = run_day(**kw)
    m, m0 = r.run_manifest_fields()["contact_c1"], r0.run_manifest_fields()["contact_c1"]
    assert m["charge"]["meter"].get("charge:plugged", 0) > 0 and m0["charge"]["meter"].get("charge:plugged", 0) == 0
    assert m0["charge"]["meter"].get("charge:agent_steps", 0) == 0  # 判断が無ければ誰も充電しない
    off, off0 = m["charge"]["meter"].get("devices_off", 0), m0["charge"]["meter"].get("devices_off", 0)
    assert off0 > off, (off0, off)
    assert m["devices"]["off"] < m0["devices"]["off"]


def test_read_receipts_reach_the_senders_candidates(monkeypatch):
    texts = []

    def rule(ctx, presented):
        for c in presented:
            if c.kind == P.K_KEEP:
                texts.append(c.text)
        return by_kind(P.K_READ_NOW, P.K_NOREPLY, P.K_KEEP)(ctx, presented)

    with choose(monkeypatch, rule):
        h = Harness2()
        loud(h)
        mb = h.layer.mail
        mb.deliver(mb.new_message_id(), 0, [1], -1, 0, 0, 5, "こんにちは", lambda a: True)
        h.layer.attn.look_at_screen([0], 0)
        h.run(3)
    assert any("既読 1/1" in t for t in texts), texts
    assert h.layer._meter.get("receipts:shown", 0) > 0
    assert SL.row("CT1IS").behavior == SL.BEHAVIOR
