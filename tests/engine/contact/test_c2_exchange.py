"""第 6 期 6-4 C2: CT5 連絡先の交換とグループ・店の番号(場所の表の側)。

対面の会話の自分の最初の番で本人が「連絡先を交換する」を選べる → 相手も応じる/断るを選ぶ → 応じれば両方の帳にメッセージの印。
グループを作る/招く/入る/断る/抜けるは本人の判断(画面の候補)。店の番号は場所の表に番号のある POI だけ調べられる(本段は空欄)。
"""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np

from shibuya.engine.contact import port as P
from shibuya.engine.contact.book import FRIEND
from shibuya.engine.contact.layer import (
    W_EXCH_ASK, W_EXCH_NO, W_EXCH_OK, W_GINVITE, W_GJOIN, W_GLEAVE, W_GMAKE, W_GREFUSE, W_LOOKUP, audit_causes,
)
from shibuya.engine.tools import contacts as CT
from shibuya.engine.tools.places import PhoneTable

from tests.engine.contact._c1 import STEP_NS, by_kind, choose
from tests.engine.contact._c2 import Harness2, loud


def _turn(a: int, partners: list[int], n_turns: int = 1):
    def hook(h, T):
        if T == 0:
            h.layer.note_face_turn("f:7", a, T, "", partners, n_turns)
    return hook


def _issued_ok(h) -> None:
    assert audit_causes(h.log.events(), step_ns=STEP_NS, issued=h.layer.issued_keys())["violations"] == 0


def test_exchange_both_decide_and_both_books_get_the_mark(monkeypatch):
    with choose(monkeypatch, by_kind(P.K_EXCHANGE, P.K_EXCH_YES)):
        h = Harness2()
        h.before_step = _turn(4, [5])
        assert 5 not in h.layer.book.personal(h.agents, 4, CT.MESSAGE, 0)
        h.run(1)
    ask, ok = h.of(W_EXCH_ASK), h.of(W_EXCH_OK)
    assert [(e.who, e.whom, e.via) for e in ask] == [(4, 5, "対面")]
    assert [(e.who, e.whom) for e in ok] == [(5, 4)]
    assert 5 in h.layer.book.personal(h.agents, 4, CT.MESSAGE, 0)
    assert 4 in h.layer.book.personal(h.agents, 5, CT.MESSAGE, 0)
    assert 4 not in h.layer.book.personal(h.agents, 5, CT.CALL, 0)  # 交換で足すのはメッセージの印だけ
    m = h.layer._meter
    assert m["exchange:asked"] == 1 and m["exchange:done"] == 1
    _issued_ok(h)


def test_exchange_follows_arbitration_main_decision_first(monkeypatch):
    """〔検収 L2〕主の判断が先: その刻みに主の判断の呼びのあった体は持ちかけるのを次の刻みに回す(例外にしない)。"""
    class Sel:
        agent_id = np.array([4])
        condition = np.array([0])

        def __len__(self):
            return 1

    with choose(monkeypatch, by_kind(P.K_EXCHANGE, P.K_EXCH_YES)):
        h = Harness2()
        h.before_step = _turn(4, [5])
        h.decision_fn = lambda T: SimpleNamespace(selected=Sel()) if T == 0 else None
        h.run(1)
        assert not h.of(W_EXCH_ASK) and h.layer._meter.get("arbitration:exchange") == 1
        assert h.layer._defer_exchange == [["ask", 4, [5]]]
        h.run(1)
    ask = h.of(W_EXCH_ASK)
    assert [(e.who, e.whom, int(e.t_ns) // STEP_NS) for e in ask] == [(4, 5, 1)] and h.of(W_EXCH_OK)
    assert h.layer._defer_exchange == []
    _issued_ok(h)


def test_refused_exchange_adds_nothing(monkeypatch):
    with choose(monkeypatch, by_kind(P.K_EXCHANGE, P.K_EXCH_NO)):
        h = Harness2()
        h.before_step = _turn(4, [5])
        h.run(1)
    assert h.of(W_EXCH_NO) and not h.of(W_EXCH_OK)
    assert 5 not in h.layer.book.personal(h.agents, 4, CT.MESSAGE, 0) and h.layer._meter["exchange:refused"] == 1
    assert h.layer.book.tally()["exchanged_pairs"] == 0


def test_only_the_first_turn_and_not_known_partners(monkeypatch):
    with choose(monkeypatch, by_kind(P.K_EXCHANGE, P.K_EXCH_YES)):
        h = Harness2()
        h.before_step = _turn(4, [5], n_turns=2)  # 2 番目の番=機会でない
        h.run(1)
        assert not h.of(W_EXCH_ASK)
        h2 = Harness2()
        h2.before_step = _turn(0, [1])  # 家族=もう連絡先がある
        h2.run(1)
    assert not h2.of(W_EXCH_ASK) and h2.layer._meter.get("exchange:all_known") == 1


def test_groups_make_invite_join_and_leave(monkeypatch):
    order = {"step": 0}

    def rule(ctx, presented):
        kinds = {c.kind: c.id for c in presented}
        if P.K_JOIN in kinds:
            return kinds[P.K_JOIN]
        if int(ctx.agent_id) == 0 and order["step"] == 0 and P.K_MAKE_GROUP in kinds:
            return kinds[P.K_MAKE_GROUP]
        if int(ctx.agent_id) == 1 and order["step"] == 2 and P.K_LEAVE in kinds:
            return kinds[P.K_LEAVE]
        for k in (P.K_TO, P.K_GROUP):
            if k in kinds:
                return sorted(c.id for c in presented if c.kind == k)[0]
        return kinds.get(P.K_KEEP) or sorted(c.id for c in presented)[0]

    with choose(monkeypatch, rule):
        h = Harness2()
        loud(h)
        h.layer.attn.look_at_screen([0, 1], 0)
        h.run(1)
        order["step"] = 1
        h.run(1)
        order["step"] = 2
        h.run(1)
    g = h.of(W_GMAKE)[0]
    gid = int(str(g.whom).split(":")[1])
    assert h.layer.book.group_kind(gid) == FRIEND and g.who == 0
    inv = h.of(W_GINVITE)[0]
    assert inv.who == 0 and inv.whom == 1 and inv.how_much == gid  # 作るときは連絡先から 1 人を招く
    joins = h.of(W_GJOIN)
    assert [(e.who, e.whom) for e in joins] == [(1, f"group:{gid}")]
    assert [(e.who, e.whom) for e in h.of(W_GLEAVE)] == [(1, f"group:{gid}")]
    assert h.layer.book.members(gid) == (0,)
    assert gid not in h.layer.book.groups_of(1) and gid in h.layer.book.groups_of(0)
    assert not h.layer.book.leave(0, 0)  # 実データ(家族・職場)の行は抜けない
    _issued_ok(h)


def test_a_group_with_no_members_disappears_and_its_invites_too():
    """〔検収 L7〕抜けて成員が 0 人になったグループは無くなる(招待も消える)・体 → グループの索引で引く(日数で重くならない)。"""
    h = Harness2()
    b = h.layer.book
    g = b.make_group(0)
    assert b.invite(g, 1) and b.groups_of(0)[-1] == g and b.made_groups_of(0) == (g,)
    assert b.leave(g, 0)
    assert not b.is_made(g) and b.members(g) == () and b.invites_of(1) == () and b.made_groups_of(0) == ()
    assert g not in b.groups_of(0) and b.tally()["made_groups"] == 0 and b.tally()["made_ever"] == 1
    g2 = b.make_group(2)
    assert g2 == g + 1  # 番号は通し番号(無くなった番号は使い直さない)
    b.invite(g2, 3)
    b.answer_invite(g2, 3, True)
    assert b.members(g2) == (2, 3) and b.made_groups_of(3) == (g2,)
    assert b.leave(g2, 2) and b.members(g2) == (3,) and b.is_made(g2)


def test_invite_refused(monkeypatch):
    with choose(monkeypatch, by_kind(P.K_REFUSE, P.K_KEEP)):
        h = Harness2()
        loud(h)
        g = h.layer.book.make_group(0)
        assert h.layer.book.invite(g, 1) and not h.layer.book.invite(g, 1)  # 二重に招かない
        h.layer.attn.look_at_screen([1], 0)
        h.run(1)
    assert [(e.who, e.whom) for e in h.of(W_GREFUSE)] == [(1, f"group:{g}")]
    assert h.layer.book.members(g) == (0,) and h.layer.book.invites_of(1) == ()


def test_store_number_lookup_only_where_the_place_table_has_a_number(monkeypatch):
    world = SimpleNamespace(pois=SimpleNamespace(cell=np.array([0, 0, 3])))
    with choose(monkeypatch, by_kind(P.K_LOOKUP, P.K_TO, P.K_KEEP)):
        h = Harness2(phones=PhoneTable({1: "03-0000-0000", 2: "03-1111-1111"}), world=world)
        loud(h)
        h.layer.attn.look_at_screen([4], 0)
        h.run(2)
    lk = h.of(W_LOOKUP)
    assert [(e.who, e.whom) for e in lk] == [(4, "poi:1")]  # セル 0 の番号のある POI=1 だけ・保存したら 2 回目は出ない
    assert h.layer.book.places_of(4) == (1,)
    with choose(monkeypatch, by_kind(P.K_LOOKUP, P.K_TO, P.K_KEEP)):
        h0 = Harness2(phones=PhoneTable(), world=world)  # 本段の表=空欄
        h0.layer.attn.look_at_screen([4], 0)
        h0.run(2)
    assert not h0.of(W_LOOKUP) and h0.layer._lookup_cells == {}
