"""〔11-03 §3〕棚卸し B の欠陥 4 件(M10・M11・M28・M16)の直しと切替口 ``engine.defect_fixes_1103`` の試験。

各欠陥について、小さな固定の状況で「ランの道(直した道)では直っている」を見る。部品の関数の既定(``resolve.apply`` の
``defect_fixes=False`` ほか=部品の単体試験の基準の口)は版上げの前の挙動の対も見る。〔第346〕ランの切替口
``--defect-fixes-1103 legacy``(環境変数 ``SHIBUYA_DEFECT_FIXES_1103``)と系の旧道の分かれは消した=渡すと止まる・見出しに
無い状態のファイルからは再開できない(旧値の再現は安定版のタグ)。記録 ``docs/bench/analysis/fix4-1103/README.md``・
``docs/bench/analysis/delete-346/README.md``。
"""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from shibuya.agents.state import Activity, AgentState, ResultCode
from shibuya.engine import commit as C
from shibuya.engine import defect_fixes_1103 as DF
from shibuya.engine import resolve as R
from shibuya.society.conversation import ConversationManager
from shibuya.world.laws.crowd import CrowdProcess
from shibuya.world.laws.rail import RailProcess
from shibuya.world.model.state import World

from .processes.conftest import fake_timetable_assets, make_agents, make_world

#: 合成 POI の営業時間は 10:00-22:00(``assets.DEFAULT_SHOP_FROM_TICK``)。購入はこの窓の中で試す(test_crowd と同じ)。
T_SHOP = 700
EMPTY = C.IntentBatch.empty()


def _batch(agent_ids, code, targets):
    a = np.asarray(agent_ids, dtype=np.int64)
    return C.IntentBatch(
        agent_id=a,
        action_code=np.full(a.size, code, dtype=np.int8),
        target_id=np.asarray(targets, dtype=np.int32),
        resource_id=np.full(a.size, -1, dtype=np.int32),
        t_notice_ns=np.zeros(a.size, dtype=np.int64),
    )


# ================================================================= 切替口そのもの
def test_the_default_arm_is_on_and_names_are_checked():
    assert DF.DEFAULT_MODE == DF.MODE_ON and DF.MODES == ("on", "legacy")
    assert DF.resolve(None) == DF.MODE_ON
    with pytest.raises(ValueError):
        DF.resolve("bogus")
    assert DF.FIXES == ("M10", "M11", "M28", "M16") and set(DF.FIX_DECLARATIONS) == set(DF.FIXES)
    assert set(DF.empty_counts()) == set(DF.COUNT_KEYS)
    m_on, m_leg = DF.manifest_fields("on"), DF.manifest_fields("legacy")
    assert m_on["schema"] == DF.SCHEMA and m_on["fixed"] == {f"fix_{k}": 1 for k in DF.FIXES}
    assert m_leg["fixed"] == {f"fix_{k}": 0 for k in DF.FIXES}
    assert m_on["counts"] == DF.empty_counts() == m_leg["counts"]


def test_state_header_and_resume_check():
    assert DF.header_fields() == DF.header_fields("on") == {"mode": "on"} and DF.header_fields("legacy") is None
    DF.check_resume({"mode": "on"})
    for saved in (None, {"mode": "legacy"}):  # 見出しに無い=版上げの前(legacy)のラン=〔第346〕再開できない
        with pytest.raises(ValueError, match="欠陥の直し.*消した.*stable-v2-before-switch-removal-346"):
            DF.check_resume(saved)


def test_removed_defect_fixes_switch_env_and_cli_flag_stop():
    """〔第346〕消した切替口: 環境変数 SHIBUYA_DEFECT_FIXES_1103 を与えると読み込みで止まる・CLI の旗は引数の誤り・系は
    箱の欄を読まない(旧道の分かれは消した)。"""
    import dataclasses
    import inspect
    import os
    import subprocess
    import sys

    from shibuya import cli
    from shibuya.engine.systems import boxes as BX
    from shibuya.engine.systems import talk as TK

    for name in ("arm", "set_arm", "_ARM"):
        assert not hasattr(DF, name), name
    assert "defect_fixes_1103" not in {f.name for f in dataclasses.fields(BX.RunConfig)}
    assert "cfg.defect_fixes_1103" not in inspect.getsource(TK)
    env = {**os.environ, "SHIBUYA_DEFECT_FIXES_1103": "legacy", "PYTHONIOENCODING": "utf-8"}
    r = subprocess.run([sys.executable, "-c", "import shibuya.engine.defect_fixes_1103"], env=env, capture_output=True,
                       text=True, encoding="utf-8")
    assert r.returncode != 0 and "消した切替口" in r.stderr
    assert '"--defect-fixes-1103"' not in inspect.getsource(cli)
    for value in ("legacy", "on"):
        with pytest.raises(SystemExit):
            cli.main(["--defect-fixes-1103", value])


def test_the_arm_is_not_a_run_day_argument():
    """腕は組み立てで 1 回読む(``run_day`` の引数にしない=設定の指紋に入れない)。"""
    import inspect

    from shibuya.engine.run import run_day

    assert "defect_fixes_1103" not in inspect.signature(run_day).parameters
    assert "defect_fixes" not in inspect.signature(run_day).parameters


# ================================================================= M10 会話の終わりの解放
def _talk_agents():
    world = World.synthetic(n_cells=9, seed=1)
    agents = AgentState(6)
    rep = np.asarray(world.assets.cell_rep_node)
    with agents.writable():
        r = agents.registry
        r.node[:] = int(rep[0])
        r.cell[:] = world.assets.node_cell[int(rep[0])]
        r.activity[:] = [int(Activity.CONVERSING), int(Activity.MOVING), int(Activity.RESTING),
                         int(Activity.SHOPPING), int(Activity.SLEEPING), int(Activity.IDLE)]
        r.talk_partner[:] = [1, 0, 3, 2, 5, 4]
    agents.freeze()
    world.freeze()
    return world, agents


def test_end_conversation_keeps_the_activity_of_bodies_that_are_not_conversing():
    _, agents = _talk_agents()
    kept = R.end_conversation(agents, np.arange(6, dtype=np.int64))
    act = np.asarray(agents.activity).tolist()
    assert act == [int(Activity.IDLE), int(Activity.MOVING), int(Activity.RESTING), int(Activity.SHOPPING),
                   int(Activity.SLEEPING), int(Activity.IDLE)]
    assert np.all(np.asarray(agents.registry.talk_partner) == -1)
    assert kept == {"MOVING": 1, "RESTING": 1, "SHOPPING": 1, "SLEEPING": 1, "IDLE": 1}
    assert R.end_conversation(agents, np.empty(0, dtype=np.int64)) == {}


def test_revert_conversation_is_the_legacy_release():
    _, agents = _talk_agents()
    R.revert_conversation(agents, np.arange(6, dtype=np.int64))
    assert np.all(np.asarray(agents.activity) == int(Activity.IDLE))
    assert np.all(np.asarray(agents.registry.talk_partner) == -1)


def _conversation_box(agents, conv):
    plan = SimpleNamespace(confirmed=EMPTY)
    return SimpleNamespace(
        soa=SimpleNamespace(agents=agents),
        scratch=SimpleNamespace(applied_now={}, outcome=SimpleNamespace(leave_conversing=[]), plan=plan),
        cfg=SimpleNamespace(attention_on=False),
        layers=SimpleNamespace(conv=conv, rel_layer=None, proximity=None, mem_layer=None, talk_clock=None),
        runstats=SimpleNamespace(leave_closed=0),
    )


def test_the_conversation_system_releases_only_conversing_bodies():
    """会話の番で「移動」を選んで歩き出した体(MOVING)は、セッションの終わりで止まらない(〔第346〕系の旧道=全員を IDLE は
    消した)。"""
    from shibuya.engine.systems.talk import sys_conversation

    world, agents = _talk_agents()
    conv = ConversationManager(master_seed=1)
    s = conv.invite(0, 1, tick=10, cell=int(agents.registry.cell[0]), same_cell=True, partner_idle=True,
                    answered=True)
    assert s is not None
    conv.close_now(0, 11, "退去")  # CLOSING → 次の step で TERMINAL
    b = _conversation_box(agents, conv)
    sys_conversation(SimpleNamespace(T=12), b)
    assert int(agents.activity[0]) == int(Activity.IDLE)  # 会話中だった体は戻す
    assert int(agents.registry.talk_partner[0]) == -1 and int(agents.registry.talk_partner[1]) == -1
    assert int(agents.activity[1]) == int(Activity.MOVING)
    assert conv.n_end_kept_activity == {"MOVING": 1}


# ================================================================= M11 列を離れる
def _queue_setup():
    """席 1 の店に 3 人が来る: 1 人が座り 2 人が並ぶ(test_crowd の ``_seat_one_and_queue_two`` と同じ)。"""
    world = make_world(4)
    agents, _ = make_agents(world, 30)
    crowd = CrowdProcess(world, agents)
    poi = 0
    cell = int(world.pois.cell[poi])
    ids = np.arange(3, dtype=np.int64)
    R.rail_arrive(agents, world, ids, np.full(ids.size, cell, dtype=np.int64))
    crowd.seats[poi] = 1
    crowd.step(T_SHOP)
    out = R.apply(_batch(ids, C.ACT_BUY, np.full(ids.size, poi)), EMPTY, agents, world, T_SHOP, crowd=crowd)
    assert out.n_purchases == 1 and out.n_queued == 2
    seated = int(np.flatnonzero(agents.registry.poi_ref == poi)[0])
    waiting = np.flatnonzero(agents.registry.queue_poi == poi)
    return world, agents, crowd, poi, seated, waiting


def _other_cell(world, cell: int) -> int:
    rep = np.asarray(world.assets.cell_rep_node)
    for c in range(world.n_cells):
        if c == cell or int(rep[c]) == int(rep[cell]):
            continue
        if int(world.graph.route_next_node(np.array([rep[cell]]), np.array([rep[c]]))[0]) >= 0:
            return c
    raise AssertionError("歩ける別のセルが無い")


@pytest.mark.parametrize("fix", [True, False])
def test_a_queued_body_that_walks_away_leaves_the_queue(fix):
    world, agents, crowd, poi, seated, waiting = _queue_setup()
    first = int(waiting[0])
    away = _other_cell(world, int(world.pois.cell[poi]))
    crowd.step(T_SHOP + 1)
    out = R.apply(_batch([first], C.ACT_MOVE, [away]), EMPTY, agents, world, T_SHOP + 1, crowd=crowd, defect_fixes=fix)
    assert int(agents.activity[first]) == int(Activity.MOVING)
    assert int(agents.last_result[first]) == int(ResultCode.OK)  # 失敗は書かない
    if fix:
        assert int(agents.registry.queue_poi[first]) == -1 and int(agents.registry.queue_since[first]) == -1
        assert out.n_queue_left_by_move == 1
    else:
        assert int(agents.registry.queue_poi[first]) == poi and out.n_queue_left_by_move == 0
    # 席が空く: 直した道では列に残った 2 人目が入る。旧道では歩き出した 1 人目が(離れた所で)入って在店になる
    R.release_indoor(agents, np.array([seated]))
    crowd.step(T_SHOP + 2)
    out = R.apply(C.engine_continuations(agents, None, T_SHOP + 2), EMPTY, agents, world, T_SHOP + 2, crowd=crowd,
                  defect_fixes=fix)
    assert out.n_served_from_queue == 1
    served = int(np.flatnonzero(agents.registry.poi_ref == poi)[0])
    assert served == (int(waiting[1]) if fix else first)
    if not fix:  # 旧道: 歩き出した体が店のセルの外で払って在席になる(場所の整合が崩れる=M11)
        assert int(agents.registry.cell[first]) != int(world.pois.cell[poi])


@pytest.mark.parametrize("fix", [True, False])
def test_a_queued_body_that_is_moved_elsewhere_is_dropped_before_serving(fix):
    """移動・乗車の外で動いた体(ここでは域の外からの到着の口で別のセルへ置いた)は、捌く前に列から外す(直した道だけ)。"""
    world, agents, crowd, poi, seated, waiting = _queue_setup()
    first = int(waiting[0])
    away = _other_cell(world, int(world.pois.cell[poi]))
    R.rail_arrive(agents, world, np.array([first]), np.array([away]))
    R.release_indoor(agents, np.array([seated]))
    crowd.step(T_SHOP + 2)
    out = R.apply(EMPTY, EMPTY, agents, world, T_SHOP + 2, crowd=crowd, defect_fixes=fix)
    if fix:
        assert out.n_queue_dropped_away == 1 and int(agents.registry.queue_poi[first]) == -1
        assert int(agents.registry.poi_ref[int(waiting[1])]) == poi  # 空いた席は次の体へ
    else:
        assert out.n_queue_dropped_away == 0 and int(agents.registry.poi_ref[first]) == poi


def _rail_setup():
    world = make_world(9)
    agents, schedule = make_agents(world, 6)
    pa = fake_timetable_assets(platform_cell=0, departures=(100, 200), lines=("山手線",))
    rail = RailProcess(world, agents, pa, master_seed=1, day_index=0, schedule=schedule)
    return world, agents, rail


@pytest.mark.parametrize("fix", [True, False])
def test_a_queued_body_that_walks_to_the_platform_leaves_the_queue(fix):
    world, agents, rail = _rail_setup()
    ids = np.array([0], dtype=np.int64)
    R.rail_arrive(agents, world, ids, np.array([8]))  # ホーム(セル 0)から遠いセル
    with agents.writable():  # 並んでいる状態を直に作る(どの店かは問わない=乗車の側の掃除だけを見る)
        agents.registry.queue_poi[0] = 0
        agents.registry.queue_since[0] = 80
    out = R.apply(_batch(ids, C.ACT_BOARD, [-1]), EMPTY, agents, world, 90, rail=rail, defect_fixes=fix)
    assert int(agents.activity[0]) == int(Activity.MOVING) and int(agents.registry.board_line[0]) >= 0
    if fix:
        assert int(agents.registry.queue_poi[0]) == -1 and out.n_queue_left_by_board == 1
    else:
        assert int(agents.registry.queue_poi[0]) == 0 and out.n_queue_left_by_board == 0


# ================================================================= M28 列の支払いの確かめ
class _AccountMoney:
    """経済の段階 2 の支払いの部品だけを持つ偽の金の台帳(口座で誰でも払える・支払いは通す)。"""

    def __init__(self) -> None:
        self.stage2 = SimpleNamespace(part=lambda name: name == "payment")
        self.paid: list[int] = []

    def can_pay_many(self, buyers, amounts):  # noqa: ANN001
        return np.ones(np.asarray(buyers).size, dtype=bool)

    def purchase_many(self, buyers, pois, amounts, step):  # noqa: ANN001
        self.paid.extend(np.asarray(buyers).tolist())
        return np.zeros(np.asarray(buyers).size, dtype=np.int8)


@pytest.mark.parametrize("fix", [True, False])
def test_the_queue_checks_payment_like_a_new_purchase(fix):
    world, agents, crowd, poi, seated, waiting = _queue_setup()
    first = int(waiting[0])
    with agents.writable():
        agents.registry.money[first] = 0  # 現金は無い(口座では払える)
    led = SimpleNamespace(money=_AccountMoney(), goods=None)
    R.release_indoor(agents, np.array([seated]))
    crowd.step(T_SHOP + 2)
    out = R.apply(EMPTY, EMPTY, agents, world, T_SHOP + 2, crowd=crowd, ledger=led, defect_fixes=fix)
    if fix:
        assert int(agents.registry.poi_ref[first]) == poi and led.money.paid == [first]
        assert out.n_queue_payable_not_cash == 1
    else:  # 旧道: 列の中でだけ現金で見る=MONEY_SHORT で外れる(新しい行の購入なら口座で払えた)
        assert int(agents.last_result[first]) == int(ResultCode.MONEY_SHORT)
        assert int(agents.registry.queue_poi[first]) == -1 and out.n_queue_payable_not_cash == 0


# ================================================================= M16 届かない承諾
def _pending_setup():
    world = World.synthetic(n_cells=9, seed=1)
    agents = AgentState(4)
    rep = np.asarray(world.assets.cell_rep_node)
    with agents.writable():
        r = agents.registry
        for a, c in ((0, 0), (1, 8)):  # 招待側と被招待が別のセル=届かない
            r.node[a] = int(rep[c])
            r.cell[a] = world.assets.node_cell[int(rep[c])]
        r.activity[0] = int(Activity.CONVERSING)  # 招待側は返事を待つ間 CONVERSING
    agents.freeze()
    world.freeze()
    conv = ConversationManager(master_seed=1)
    assert conv.register_pending(0, 1, tick=5, cell=int(agents.registry.cell[0]), same_cell=True)
    return agents, conv


@pytest.mark.parametrize("fix", [True, False])
@pytest.mark.parametrize("named", [0, -1])
def test_an_unreachable_acceptance_is_not_a_refusal(fix, named):
    from shibuya.engine.run import _settle_pending_invites

    agents, conv = _pending_setup()
    consumed = _settle_pending_invites(
        conv, agents, 6, np.array([1]), np.array([C.ACT_TALK]), np.array([named]), R, np,
        drop_unreachable=fix,
    )
    assert consumed == set() and not conv.pending_invites
    assert int(agents.activity[0]) == int(Activity.IDLE)  # 招待側は戻す(どちらの腕も)
    assert conv.n_accepted == 0
    if fix:
        assert conv.n_pending_unreachable == 1 and conv.n_declined == 0
        assert not conv.refused_recently(0, 1, 7)
    else:
        assert conv.n_pending_unreachable == 0 and conv.n_declined == 1
        assert conv.refused_recently(0, 1, 7)


@pytest.mark.parametrize("fix", [True, False])
def test_other_replies_are_still_refusals(fix):
    """届かなくても「会話」でない返事は今のまま断り(直すのは承諾の返事だけ)。"""
    from shibuya.engine.run import _settle_pending_invites

    agents, conv = _pending_setup()
    _settle_pending_invites(conv, agents, 6, np.array([1]), np.array([C.ACT_MOVE]), np.array([-1]), R, np,
                            drop_unreachable=fix)
    assert conv.n_declined == 1 and conv.n_pending_unreachable == 0 and conv.refused_recently(0, 1, 7)


def test_drop_pending_counts_the_origin():
    conv = ConversationManager(master_seed=1, count_unreachable=True)
    conv.track_origins(("invite", "chance"))
    assert conv.register_pending(0, 1, tick=1, cell=0, same_cell=True, origin=1)
    assert conv.drop_pending(1, 2) is not None and conv.drop_pending(1, 2) is None
    assert conv.origin_counts["chance"]["unreachable"] == 1 and conv.origin_counts["chance"]["declined"] == 0


# ================================================================= ランの全体(manifest の節・見出し・再開・CLI)
@pytest.fixture(scope="module")
def tiny_runs():
    from shibuya.engine.run import run_day

    return {"on": run_day(n_agents=60, seed=1, ticks=240, renderer="stub", vocab_version="v3", checkpoint_every=240)}


def test_run_manifest_section(tiny_runs):
    m = tiny_runs["on"].run_manifest_fields()
    df = m["defect_fixes_1103"]
    assert list(m)[-1] == "defect_fixes_1103"
    assert df["schema"] == DF.SCHEMA and df["mode"] == "on" and set(df["fixes"]) == set(DF.FIXES)
    assert all(v == 1 for v in df["fixed"].values()) and set(df["counts"]) == set(DF.COUNT_KEYS)
    leg = DF.manifest_fields("legacy")  # 部品の口(ランからは選べない)=旧道は数えない
    assert leg["mode"] == "legacy" and all(v == 0 for v in leg["fixed"].values())
    assert leg["counts"] == DF.empty_counts()


def test_resume_without_the_header_is_refused(tmp_path):
    """腕は設定の指紋に入れない=状態のファイルの見出しの ``defect_fixes_1103``(常に on)を見る。〔第346〕見出しに無い状態の
    ファイル(版上げの前のラン)は再開で止まる: 保存の間だけ見出しを書かない形にし、戻してから再開する(検収 M3)。"""
    from shibuya.engine import resume as RS
    from shibuya.engine.run import run_day

    kw = dict(n_agents=40, seed=1, n_cells=9, ticks=240, budget=40.0, vocab_version="v3")
    a = run_day(state_out=tmp_path / "st", stop_at_tick=120, **kw)  # 正の対照: 見出しのある保存は通る
    f = tmp_path / "st" / a.resume["state_files"][-1]["file"]
    assert RS.read_state(f).header["defect_fixes_1103"] == {"mode": "on"}
    run_day(resume_from=f, **kw)
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(DF, "header_fields", lambda *a_, **k_: None)  # 版上げの前のラン=見出しに defect_fixes_1103 が無い
        old = run_day(state_out=tmp_path / "old", stop_at_tick=120, **kw)
    g = tmp_path / "old" / old.resume["state_files"][-1]["file"]
    assert "defect_fixes_1103" not in RS.read_state(g).header
    with pytest.raises(ValueError, match="欠陥の直し.*消した.*stable-v2-before-switch-removal-346"):
        run_day(resume_from=g, **kw)


# ================================================================= M10 の続き: 招待が流れた招待側の戻し(11-03 親の依頼の続き)
def _waiting_inviter(activity):
    """招待側 0 が被招待 1 の返事を待つ(返事待ちの間に招待側の活動が ``activity`` になった)。"""
    agents, conv = _pending_setup()
    with agents.writable():
        agents.registry.activity[0] = int(activity)
        agents.registry.talk_partner[0] = 1
    return agents, conv


def test_an_expired_invite_keeps_the_inviters_new_activity():
    """返事待ちの間に歩き出した招待側(MOVING)は、期限切れの戻しで MOVING のまま(〔第346〕系の旧道=IDLE は消した)。"""
    from shibuya.society.conversation import PENDING_INVITE_TTL_TICKS
    from shibuya.engine.systems.talk import sys_conversation

    agents, conv = _waiting_inviter(Activity.MOVING)
    b = _conversation_box(agents, conv)
    sys_conversation(SimpleNamespace(T=5 + PENDING_INVITE_TTL_TICKS + 1), b)
    assert not conv.pending_invites and conv.n_pending_expired == 1
    assert int(agents.registry.talk_partner[0]) == -1
    assert int(agents.activity[0]) == int(Activity.MOVING)
    assert conv.n_revert_kept_activity == {"expired": {"MOVING": 1}} and conv.n_end_kept_activity == {}


def test_an_expired_invite_still_releases_a_waiting_conversing_inviter():
    """返事を待って CONVERSING のままの招待側は IDLE に戻る(戻しの意図そのもの)。"""
    from shibuya.society.conversation import PENDING_INVITE_TTL_TICKS
    from shibuya.engine.systems.talk import sys_conversation

    agents, conv = _waiting_inviter(Activity.CONVERSING)
    sys_conversation(SimpleNamespace(T=5 + PENDING_INVITE_TTL_TICKS + 1), _conversation_box(agents, conv))
    assert int(agents.activity[0]) == int(Activity.IDLE) and conv.n_revert_kept_activity == {}


@pytest.mark.parametrize("keep", [True, False])
def test_a_refusal_keeps_the_inviters_new_activity(keep):
    """返事の解決(``_settle_pending_invites``)の末尾の戻し: 断られた招待側が SHOPPING なら既定では残す(旧道は IDLE)。"""
    from shibuya.engine.run import _settle_pending_invites

    agents, conv = _waiting_inviter(Activity.SHOPPING)
    _settle_pending_invites(conv, agents, 6, np.array([1]), np.array([C.ACT_MOVE]), np.array([-1]), R, np,
                            drop_unreachable=keep, keep_activity=keep)
    assert conv.n_declined == 1 and int(agents.registry.talk_partner[0]) == -1
    if keep:
        assert int(agents.activity[0]) == int(Activity.SHOPPING) and conv.n_revert_kept_activity == {"settle": {"SHOPPING": 1}}
    else:
        assert int(agents.activity[0]) == int(Activity.IDLE) and conv.n_revert_kept_activity == {}


# ================================================================= 検収の直し(11-03 の 3 回目)
def test_a_body_choosing_a_talk_without_a_target_keeps_its_activity():
    """〔中-2〕対象の決まらない会話(resolve が失敗させた体=活動は変わっていない)。旧道は寝ている体を IDLE にして起こしていた
    (〔第346〕系の旧道は消した)。CONVERSING でない体を戻さない(対象のある失敗と揃う)。計器の原因は no_target。"""
    from shibuya.engine.systems.talk import sys_conversation

    _, agents = _talk_agents()  # 体 4 は SLEEPING
    conv = ConversationManager(master_seed=1)
    b = _conversation_box(agents, conv)
    b.scratch.plan = SimpleNamespace(confirmed=_batch([4], C.ACT_TALK, [-1]))
    sys_conversation(SimpleNamespace(T=3), b)
    assert int(agents.registry.talk_partner[4]) == -1
    assert int(agents.activity[4]) == int(Activity.SLEEPING)
    assert conv.n_revert_kept_activity == {"no_target": {"SLEEPING": 1}}


@pytest.mark.parametrize("fix", [True, False])
def test_a_body_that_joined_a_session_in_the_same_call_is_not_released(fix):
    """〔低-2〕A が B に断られて戻す候補に積まれ、同じ呼び出しの後の行で C の招待を承諾してセッションに入った。直した道は
    書く直前に会話中の体を除く(A は C と会話中のまま)。旧道は A を IDLE・talk_partner −1 にしてセッションから引き剥がす。"""
    from shibuya.engine.run import _settle_pending_invites

    world = World.synthetic(n_cells=9, seed=1)
    agents = AgentState(4)
    rep = np.asarray(world.assets.cell_rep_node)
    with agents.writable():
        r = agents.registry
        r.node[:] = int(rep[0])
        r.cell[:] = world.assets.node_cell[int(rep[0])]
        r.activity[:3] = int(Activity.CONVERSING)
    agents.freeze()
    world.freeze()
    conv = ConversationManager(master_seed=1)
    cell = int(agents.registry.cell[0])
    assert conv.register_pending(0, 1, tick=5, cell=cell, same_cell=True)  # A=0 → B=1
    assert conv.register_pending(2, 0, tick=5, cell=cell, same_cell=True)  # C=2 → A=0
    _settle_pending_invites(conv, agents, 6, np.array([1, 0]), np.array([C.ACT_MOVE, C.ACT_TALK]), np.array([-1, 2]),
                            R, np, drop_unreachable=fix, keep_activity=fix)
    assert conv.n_declined == 1 and conv.n_accepted == 1 and conv.is_busy(0)
    if fix:
        assert int(agents.activity[0]) == int(Activity.CONVERSING) and int(agents.registry.talk_partner[0]) == 2
    else:
        assert int(agents.activity[0]) == int(Activity.IDLE) and int(agents.registry.talk_partner[0]) == -1


def _identity(c):
    return (c["conv_accepted"] + c["conv_declined"] + c["conv_pending_expired"] + c["conv_pending_open"]
            + c.get("conv_pending_unreachable", 0)) == c["conv_invites"]


@pytest.mark.parametrize("fix", [True, False])
def test_an_invitee_that_moved_away_then_accepts_keeps_the_invite_ledger_balanced(fix):
    """〔中-1〕招待の後に被招待が別のセルへ動いてから承諾した。既定は不成立(``conv_pending_unreachable``=腕 on のランだけ
    ``counters`` に出る)・旧道は断り(鍵は出ない=旧道の出力は 1 字も変えない)。どちらも帳尻 招待 = 成立+断り+期限切れ+未決
    (+不成立)が合う。"""
    from shibuya.engine.run import _settle_pending_invites

    world = World.synthetic(n_cells=9, seed=1)
    agents = AgentState(4)
    rep = np.asarray(world.assets.cell_rep_node)
    with agents.writable():
        r = agents.registry
        r.node[:] = int(rep[0])
        r.cell[:] = world.assets.node_cell[int(rep[0])]
        r.activity[0] = int(Activity.CONVERSING)
    agents.freeze()
    world.freeze()
    conv = ConversationManager(master_seed=1, count_unreachable=fix)
    assert conv.register_pending(0, 1, tick=5, cell=int(agents.registry.cell[0]), same_cell=True)  # 同じセルで招待
    R.rail_arrive(agents, world, np.array([1]), np.array([8]))  # 被招待が別のセルへ動いた
    _settle_pending_invites(conv, agents, 6, np.array([1]), np.array([C.ACT_TALK]), np.array([0]), R, np,
                            drop_unreachable=fix, keep_activity=fix)
    c = dict(conv.counters())
    assert c["conv_invites"] == 1 and _identity(c), c
    if fix:
        assert c["conv_pending_unreachable"] == 1 and c["conv_declined"] == 0
    else:
        assert "conv_pending_unreachable" not in c and c["conv_declined"] == 1


def test_the_unreachable_origin_key_is_there_from_the_start_only_when_counted():
    """〔低-4〕起点の計数の鍵は最初から全部ある作り=腕 on のランは unreachable も最初から 0 で置く(旧道は鍵を足さない)。"""
    on = ConversationManager(master_seed=1, count_unreachable=True)
    on.track_origins(("invite",))
    assert on.origin_counts["invite"] == {"invites": 0, "accepted": 0, "declined": 0, "expired": 0, "rejected": 0,
                                         "unreachable": 0}
    leg = ConversationManager(master_seed=1)
    leg.track_origins(("invite",))
    assert "unreachable" not in leg.origin_counts["invite"]
    with pytest.raises(ValueError):
        leg.note_revert_kept("bogus", {"IDLE": 1})
