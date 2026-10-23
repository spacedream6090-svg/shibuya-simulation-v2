"""第 6 期 6-4 C2: 充電を本人の行動に(CT0 の共通の決まり 2・3)。

道具が「電池が少ない」・満充電を知らせる(System 1 の通知と同じ段)→ 家で本人が充電する/やめるを選ぶ → 差した体だけ物理で電池が
増える(家を離れたら抜ける)。カレンダー 3 のつなぎ ``BR-CT1-CHARGE-AT-HOME``(家に居ると増えるエンジン規則)は外した=判断が
無ければ増えない(負の対照)。
"""

from __future__ import annotations

import numpy as np

from shibuya.core.time_consts import SECONDS_PER_HOUR, STEP_SECONDS
from shibuya.engine.bridging import ledger as BR
from shibuya.engine.contact import deliver as DL
from shibuya.engine.contact import device as DV
from shibuya.engine.contact import port as P
from shibuya.engine.contact.layer import W_BATTERY, W_CHARGE, W_DELIVERED, W_UNPLUG, audit_causes

from tests.engine.contact._c1 import STEP_NS, by_kind, choose
from tests.engine.contact._c2 import Harness2, loud


def test_physics_plugged_charges_unplugged_does_not():
    d = DV.Devices(4, 1)
    d.drain(np.full(4, DV.USE_SCREEN), SECONDS_PER_HOUR * 9)  # 12%/時 × 9 時間 → 全員 0 で電源が切れる
    assert not d.on(np.arange(4)).any() and d.summary()["low_known"] == 4  # 電源が切れたことは本人が知る
    n, back, full = d.charge_plugged(STEP_SECONDS)
    assert n == 0 and back.size == 0  # 差していなければ増えない(エンジンは充電しない)
    d.plug([0, 1])
    n, back, full = d.charge_plugged(STEP_SECONDS)
    assert n == 2 and back.tolist() == [0, 1] and float(d.battery()[2]) == 0.0
    for _ in range(int(SECONDS_PER_HOUR * 3 // STEP_SECONDS)):  # 3 時間=満充電(2 時間相当)を超えても 1 で止まる
        d.charge_plugged(STEP_SECONDS)
    assert float(d.battery()[0]) == DV.INITIAL_BATTERY and d.summary()["low_known"] == 2
    before = d.battery().copy()
    d.drain(np.full(4, DV.USE_SCREEN), SECONDS_PER_HOUR)  # 差している間は減らない(家の電源)
    assert float(d.battery()[0]) == float(before[0])
    d.unplug([0])
    d.drain(np.full(4, DV.USE_SCREEN), SECONDS_PER_HOUR)
    assert float(d.battery()[0]) < float(before[0])


def test_full_is_reported_once_and_low_alerts_cross_thresholds():
    d = DV.Devices(2, 1)
    d._battery[:] = np.float32(0.2015)
    b0 = d.battery().copy()
    d.drain(np.full(2, DV.USE_SCREEN), STEP_SECONDS)  # 0.2015 − 0.002 → 20% を下に越えた
    assert d.low_alerts(b0).tolist() == [0, 1]
    b1 = d.battery().copy()
    d.drain(np.full(2, DV.USE_SCREEN), STEP_SECONDS)
    assert d.low_alerts(b1).size == 0  # 越えた刻みだけ
    d._battery[:] = np.float32(0.995)
    d.plug([0])
    _n, _b, full = d.charge_plugged(STEP_SECONDS)
    assert full.tolist() == [0]
    _n, _b, full = d.charge_plugged(STEP_SECONDS)
    assert full.size == 0


def test_power_on_only_for_a_plugged_device():
    d = DV.Devices(2, 1)
    d._on[:] = False  # 電池はあるが電源が切れている(差していない)
    _n, back, _f = d.charge_plugged(STEP_SECONDS)
    assert back.size == 0 and not d.on(np.arange(2)).any()


def _low_at_home(h):
    h.layer.dev._battery[:] = np.float32(0.20005)  # 次の刻み(待ち受け 1%/時)に 20% を下に越える


def test_low_alert_at_home_the_person_decides_to_charge(monkeypatch):
    with choose(monkeypatch, by_kind(P.K_CHARGE, P.K_KEEP)):
        h = Harness2(home_cell=[0] * 6)
        loud(h)
        _low_at_home(h)
        h.run(3)
    alerts = h.of(W_BATTERY)
    assert alerts and all(e.cause.name == "contact" for e in alerts)  # 知らせは道具の性質(網=過程 contact)
    ch = h.of(W_CHARGE)
    assert ch and {e.who for e in ch} <= set(range(6))
    a = ch[0].who
    st = P.step_of_call_id(ch[0].cause.call_id)
    assert ch[0].t_ns == st * STEP_NS and P.purpose_of_serial(P.parse_call_id(ch[0].cause.call_id)[2]) == P.P_CHARGE
    assert bool(h.layer.dev._plugged[a])
    b = float(h.layer.dev._battery[a])
    h.run(5)
    assert float(h.layer.dev._battery[a]) > b  # 差した体は物理で増える
    assert audit_causes(h.log.events(), step_ns=STEP_NS, issued=h.layer.issued_keys())["violations"] == 0


def test_negative_control_no_decision_no_charge(monkeypatch):
    """本人が「このまま」を選ぶ(判断なし)と家に居ても電池は増えない(エンジン規則の充電は外した)。"""
    with choose(monkeypatch, by_kind(P.K_NO_CHARGE, P.K_KEEP)):
        h = Harness2(home_cell=[0] * 6)
        loud(h)
        _low_at_home(h)
        h.run(3)
        b = h.layer.dev.battery().copy()
        h.run(30)
    assert not h.of(W_CHARGE) and h.layer._meter.get("charge:declined", 0) > 0
    assert not h.layer.dev._plugged.any()
    assert (h.layer.dev.battery() <= b).all()  # 増えない
    assert "BR-CT1-CHARGE-AT-HOME" not in {r.id for r in BR.default_ledger().active()}


def test_not_at_home_no_charge_opportunity(monkeypatch):
    with choose(monkeypatch, by_kind(P.K_CHARGE, P.K_KEEP)):
        h = Harness2(home_cell=[1] * 6)  # 住まいはセル 1・全員セル 0(家の外)
        loud(h)
        _low_at_home(h)
        h.run(5)
    assert h.of(W_BATTERY) and not h.of(W_CHARGE) and not h.layer.dev._plugged.any()


def test_outside_residents_are_at_home_while_outside(monkeypatch):
    """〔親の判断 2026-10-23=問い 1〕住まいが範囲の外の体は範囲の外に居る刻みを家とする(範囲の外の活動は作っていない=「寝ている」が
    立たない)。範囲の中に入ると家でない(差していれば抜ける)。"""
    with choose(monkeypatch, by_kind(P.K_CHARGE, P.K_KEEP)):
        h = Harness2(home_cell=[-1] * 6, cells=[-1] * 6)
        h.agents.registry.transit_state[:] = 2
        loud(h)
        _low_at_home(h)
        h.run(3)
    assert h.of(W_CHARGE) and h.layer.dev._plugged.any() and bool(h.layer._at_home.all())
    a = int(np.flatnonzero(h.layer.dev._plugged)[0])
    h.agents.registry.transit_state[a] = 0
    h.agents.registry.cell[a] = 0  # 範囲に入った
    h.run(1)
    assert not bool(h.layer.dev._plugged[a]) and h.layer._meter.get("charge:unplugged_left_home", 0) >= 1


def test_charge_is_offered_whenever_the_person_thinks_at_home_with_a_low_battery(monkeypatch):
    """〔検収 L6〕家に居て電池が閾値の下の体は、その刻みに判断したとき(連絡の判断・主の判断)にいつも充電の候補が出る
    (家に着いた刻みの 1 回だけではない)。電池が少ないと知らなくても判断のときに見る。"""
    seen = []

    def rule(ctx, presented):
        kinds = [c.kind for c in presented]
        if P.K_CHARGE in kinds:
            seen.append(int(ctx.step))
            return next(c.id for c in presented if c.kind == P.K_NO_CHARGE)  # 断り続ける
        return by_kind(P.K_KEEP)(ctx, presented)

    with choose(monkeypatch, rule):
        h = Harness2(home_cell=[0] * 6)
        loud(h)
        d = h.layer.dev
        d._battery[2] = np.float32(0.15)  # 閾値の下(知らせはもう過ぎた=少ないと知らない)
        d._home_prev[:] = True  # 家に着いた刻みではない
        h.layer.attn.look_at_screen([2], 0)  # 画面を見ている=毎刻み連絡の判断をする
        h.run(4)
    assert seen and len(set(seen)) >= 3  # 判断のたびに候補が出る
    assert h.layer._meter.get("charge:opportunities_on_thinking", 0) >= 3


def test_leaving_home_unplugs_and_full_alert_asks_to_stop(monkeypatch):
    with choose(monkeypatch, by_kind(P.K_UNPLUG, P.K_KEEP)):
        h = Harness2(home_cell=[0] * 6)
        loud(h)
        h.layer.dev._battery[:] = np.float32(0.999)
        h.layer.dev.plug([0, 1])
        h.run(2)
    assert {e.who for e in h.of(W_UNPLUG)} == {0, 1} and not h.layer.dev._plugged[[0, 1]].any()
    h.layer.dev.plug([2])
    h.agents.registry.cell[2] = 3  # 家を離れた
    h.run(1)
    assert not bool(h.layer.dev._plugged[2]) and h.layer._meter.get("charge:unplugged_left_home") == 1


def test_charging_powers_on_and_releases_held_messages(monkeypatch):
    with choose(monkeypatch, by_kind(P.K_CHARGE, P.K_KEEP)):
        h = Harness2(home_cell=[0] * 6)
        loud(h)
        d = h.layer.dev
        d._battery[1] = np.float32(0.0)
        d._on[1] = False
        d._low_known[1] = True
        mb = h.layer.mail
        mb.deliver(mb.new_message_id(), 0, [1], -1, 0, 0, 5, "こんにちは", lambda a: bool(d._on[a]))
        assert mb.mail_counts()["held"] == 1
        d._home_prev[1] = False  # 次の刻みに家に着いた(機会)
        h.run(3)
    assert h.of(W_CHARGE) and bool(d._on[1]) and mb.mail_counts()["held"] == 0
    assert [e for e in h.of(W_DELIVERED) if e.who == 1]


def test_mailbox_release_held():
    mb = DL.Mailbox()
    got, held = mb.deliver(mb.new_message_id(), 0, [1, 2], -1, 0, 100, 5, "こんにちは", lambda a: a == 1)
    assert got == [1] and held == [2] and mb.unread_count(2) == 0
    rows = mb.release_held([2], 500)
    assert rows == [[2, 0, 0, -1, 0]] and mb.unread_count(2) == 1
    assert mb.take_unseen() == [(1, 1, 100), (2, 1, 500)]
