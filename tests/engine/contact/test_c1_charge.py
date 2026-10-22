"""〔つなぎ BR-CT1-CHARGE-AT-HOME〕連絡の道具 C1 の家での充電(エンジン規則=充電が本人の行動になるまで・腕 c1 のランだけ)。

家に居る体だけ電池が増える(職場では増えない)・満充電で止まる・電池が 0 でなくなった体は電源が入る・網が預かっていたメッセージは
電源が入った刻みに届く(出来事 ``連絡:届いた``=原因 過程 contact)。
"""

from __future__ import annotations

import numpy as np

from shibuya.core.time_consts import SECONDS_PER_HOUR, STEP_SECONDS
from shibuya.engine.contact import deliver as DL
from shibuya.engine.contact import device as DV


def test_charge_only_at_home_up_to_full_and_powers_on():
    d = DV.Devices(4, 1)
    d.drain(np.full(4, DV.USE_SCREEN), SECONDS_PER_HOUR * 9)  # 12%/時 × 9 時間 → 全員 0 で電源が切れる
    assert not d.on(np.arange(4)).any() and float(d.battery().max()) == 0.0
    home = np.array([True, True, False, False])
    n, back = d.charge(home, STEP_SECONDS)
    assert n == 2 and back.tolist() == [0, 1]
    assert d.on(np.arange(4)).tolist() == [True, True, False, False]
    assert float(d.battery()[0]) > 0.0 and float(d.battery()[2]) == 0.0  # 家の外(職場)では増えない
    for _ in range(int(SECONDS_PER_HOUR * 3 // STEP_SECONDS)):  # 3 時間=満充電(2 時間相当)を超えても 1 で止まる
        d.charge(home, STEP_SECONDS)
    assert float(d.battery()[0]) == DV.INITIAL_BATTERY and d.summary()["battery_zero"] == 2
    n, back = d.charge(home, STEP_SECONDS)
    assert n == 0 and back.size == 0


def test_held_messages_are_delivered_when_the_power_comes_back():
    mb = DL.Mailbox()
    got, held = mb.deliver(mb.new_message_id(), 0, [1, 2], -1, 0, 100, 5, "こんにちは", lambda a: a == 1)
    assert got == [1] and held == [2] and mb.unread_count(2) == 0
    rows = mb.release_held([2], 500)
    assert rows == [[2, 0, 0, -1, 0]] and mb.unread_count(2) == 1
    assert mb.take_unseen() == [(1, 1, 100), (2, 1, 500)]
    assert mb.release_held([2], 600) == [] and mb.mail_counts()["held"] == 0
