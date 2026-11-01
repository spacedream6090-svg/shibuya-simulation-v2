"""第 6 期 6-4 C1 の独立検収の直しの試験(H1・M1・M2・M4・M5・L8)。

- H1: 腕 c1 を段 B(``SHIBUYA_SYSTEMS_CHECK=1``)で回すと宣言の外の変化 0・系 contact の宣言から ``BW:batching.*`` を外すと落ちる
  (負の対照)。腕 port(主の判断の候補)でも同じ。
- M1: 顕著行為の門の結果は連絡の持ち主の側(過程のキャッシュは書き換えない)・記憶の系は ``salient_view`` から読む(門の前は止まる)。
- M2: 監査は発行した呼びと突き合わせる(偽の ``LlmCall`` を植えると落ちる)+AST(本人の語の原因は判断の口の答えだけ)。
- M4: 関心の的は判断の後の値(刻みの終わり)=次の刻みの描画と門が同じ値を読む。
- M5: 「スマホを見る」は主の判断の候補・連絡の呼び数は calls_by_model に入る・仲裁(主の判断が先)。
- L8: 通話中の日の途中の再開=通し。
"""

from __future__ import annotations

import ast
import dataclasses
from pathlib import Path

import numpy as np
import pytest

from shibuya.agents.state import Activity
from shibuya.engine.contact import attention as AT
from shibuya.engine.contact import layer as LY
from shibuya.engine.contact import port as P
from shibuya.engine.contact.layer import W_LOOK, W_READ, audit_causes
from shibuya.engine.conversation import ConvState
from shibuya.engine.decision import layer as DCL
from shibuya.engine.decision import ports as DPS
from shibuya.engine.decision.port import DecisionContext
from shibuya.engine.events.log import LlmCall
from shibuya.engine.run import run_day
from shibuya.engine.systems import table as TB
from shibuya.engine.tools import record as TR
from shibuya.engine.tools.groups import GroupList

from tests.engine.contact._c1 import KW, ROOT, STEP_NS, Harness, by_kind, c1, choose

SRC = ROOT / "src" / "shibuya" / "engine" / "contact"


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


@pytest.fixture
def port_arm():
    prev = DCL.arm()
    DCL.set_arm(DCL.ARM_PORT)
    try:
        yield
    finally:
        DCL.set_arm(prev)


# ================================================================= H1 段 B
def test_h1_arm_c1_passes_stage_b(with_groups, monkeypatch):
    monkeypatch.setenv("SHIBUYA_SYSTEMS_CHECK", "1")
    with c1():
        r = run_day(**dict(KW, ticks=360, relations="off"))
    m = r.run_manifest_fields()["contact_c1"]["meter"]
    assert m.get("typed", 0) > 0 and m.get("delivered", 0) > 0  # 系の中から待ち行列に予約した(送信)


def test_h1_negative_control_without_the_bw_declaration_fails(with_groups, monkeypatch):
    spec = TB.SPECS["contact"]
    paths = frozenset(p for p in spec.writes.paths if not p.startswith("BW:"))
    monkeypatch.setitem(TB.SPECS, "contact", dataclasses.replace(spec, writes=dataclasses.replace(spec.writes, paths=paths)))
    monkeypatch.setenv("SHIBUYA_SYSTEMS_CHECK", "1")
    with c1(), pytest.raises(AssertionError, match="宣言の外"):
        run_day(**dict(KW, ticks=360, relations="off"))


def _prefer_look(monkeypatch):
    real = DPS.MockPort.pick

    def pick(self, ctx, presented):
        for c in presented:
            if c.kind == P.K_LOOK:
                return c.id
        return real(self, ctx, presented)

    monkeypatch.setattr(DPS.MockPort, "pick", pick)


def test_m5_look_is_a_main_candidate_and_counts(with_groups, port_arm, monkeypatch):
    """腕 port: 暇なときの「スマホを見る」は主の判断の候補(選ぶと同じ刻みに画面を見る)・別の暇の判断はしない・段 B も通る。"""
    _prefer_look(monkeypatch)
    monkeypatch.setenv("SHIBUYA_SYSTEMS_CHECK", "1")
    with c1():
        r = run_day(**dict(KW, ticks=720, relations="off"))
    man = r.run_manifest_fields()
    m = man["contact_c1"]["meter"]
    assert m.get("main_offered", 0) > 0 and m.get("main_looks", 0) > 0
    assert man["contact_c1"]["decisions"].get("idle", 0) == 0  # 暇の判断は主の判断の候補に入った
    looks = [e for e in r.event_log.events() if e.what == W_LOOK]
    assert looks and all(P.parse_call_id(e.cause.call_id) is None for e in looks)  # 主の判断の呼び
    a = audit_causes(r.event_log.events(), step_ns=STEP_NS, issued=r.contact_layer.issued_keys())
    assert a["violations"] == 0, a
    cbm = man["calls_by_model"]
    j, t = r.contact_layer.model_calls()
    assert cbm["contact"] == {"judge_model": j, "llm": t} and cbm["judge_model"] == j and j > 0
    assert cbm["llm"] == int(r.llm_calls) + t


def test_m5_calls_by_model_is_unchanged_without_the_arm():
    with c1(on=False):
        r = run_day(**dict(KW, ticks=60))
    assert r.run_manifest_fields()["calls_by_model"] == {"judge_model": 0, "llm": int(r.llm_calls)}


def test_m5_arbitration_main_decision_first(monkeypatch):
    """同じ刻みに主の判断の呼びがある体は、連絡の通知の判断を次の刻みに回す(仲裁)。"""

    class Sel:
        def __init__(self, ids):
            self.agent_id = np.asarray(ids, dtype=np.int64)
            self.condition = np.full(len(ids), -1, dtype=np.int64)

        def __len__(self):
            return int(self.agent_id.size)

    class Dec:
        selected = Sel([1])

    with choose(monkeypatch, by_kind(P.K_LATER)):
        h = Harness()
        mb = h.layer.mail
        mb.deliver(mb.new_message_id(), 0, [1], -1, 0, 0, 5, "こんにちは", lambda a: True)
        h.layer.run_step(0, 0, 0, agents=h.agents, world=h.world, conv=None, runner=None, decision=Dec())
        assert h.layer._defer == {1: 0} and h.layer._meter.get("decisions:notice", 0) == 0
        h.layer.run_step(1, STEP_NS, 1, agents=h.agents, world=h.world, conv=None, runner=None, decision=None)
    assert h.layer._defer == {} and h.layer._meter["decisions:notice"] == 1
    assert "main_first" in P.ARBITRATION


# ================================================================= M1 門の結果は連絡の側
def test_m1_gate_is_kept_on_the_contact_side():
    h = Harness()
    h.layer.attn._focus[1] = AT.FOCUS_SCREEN

    @dataclasses.dataclass
    class Ev:
        cell: int
        noticed: np.ndarray

    class Sal:
        events = [Ev(0, np.array([0, 1]))]
        noticed_agents = np.array([0, 1])

    with pytest.raises(RuntimeError):
        h.layer.salient_view(Sal.events, 5)  # 門の前は止まる(順は依存で守る)
    h.layer._salient_gate(5, 5 * STEP_NS, Sal, np.zeros(6, dtype=np.int64), np.zeros(6, dtype=bool))
    v = h.layer.salient_view(Sal.events, 5)
    assert v[0].noticed.tolist() == [0] and v[0].cell == 0
    assert Sal.events[0].noticed.tolist() == [0, 1] and Sal.noticed_agents.tolist() == [0, 1]  # 書き換えない
    with pytest.raises(RuntimeError):
        h.layer.salient_view(Sal.events, 6)
    assert "layers.contact" in TB.SPECS["memory"].reads.box


# ================================================================= M2 監査(発行した呼び)と AST
def test_m2_a_forged_llm_call_is_caught_by_the_issued_check(monkeypatch):
    def forged(self, T, t_ns, a):  # 植えた規則: 通知に気づいたらエンジンが読む(原因を偽る)
        c = LlmCall(P.call_id_of(T, a, P.serial_of(P.P_NOTICE, 77)), (), source="affordance", number=1)
        self._log(t_ns, a, W_READ, c, whom=0, received_ns=t_ns, read_ns=t_ns)

    monkeypatch.setattr(LY.ContactLayer, "_notice_decision", forged)
    with choose(monkeypatch, by_kind(P.K_KEEP)):
        h = Harness()
        mb = h.layer.mail
        mb.deliver(mb.new_message_id(), 0, [1], -1, 0, 0, 5, "こんにちは", lambda a: True)
        h.run(2)
    evs = list(h.log.events())
    assert [e for e in evs if e.what == W_READ]
    assert audit_causes(evs, step_ns=STEP_NS)["violations"] == 0  # 型だけ見る監査は見逃す(対照)
    assert audit_causes(evs, step_ns=STEP_NS, issued=h.layer.issued_keys())["violations"] > 0


_PERSON = {"W_SENT", "W_READ", "W_LATER", "W_IGNORE", "W_LOOK", "W_UP", "W_DIAL", "W_ANSWER", "W_DECLINE", "W_HANG"}
# 〔第 6 期 6-4 C2〕足した本人の語(充電・交換・グループ・ビデオ通話・店の番号)も同じ規則で見る
_PERSON |= {"W_CHARGE", "W_UNPLUG", "W_EXCH_ASK", "W_EXCH_OK", "W_EXCH_NO", "W_GMAKE", "W_GINVITE", "W_GJOIN", "W_GREFUSE",
            "W_GLEAVE", "W_VIDEO_DIAL", "W_LOOKUP"}
#: 〔C2〕判断の口の答えを返す口(判断の口か CT4 の習慣=本人の過去の選びから作った答え)。
_DECIDE_FUNCS = {"_decide", "_habit_or_decide"}
#: 判断の答えを予約や控えから作り直してよい関数(送った=予約の行の call_id・主の判断の候補で選んだ=判断の系が渡した call_id・
#: 通話の終わり=切った判断の call_id の控えか会話の過程)。
_REBUILD_OK = {"_send_now", "_take_main_looks", "_call_ended"}


def _cause_problems(src: str) -> list[str]:
    """本人の語の出来事の原因が判断の口の答え(``self._decide`` の戻り)だけかを AST で見る。read_ns は本人の語だけ。"""
    bad: list[str] = []
    tree = ast.parse(src)
    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        params = {a.arg for a in fn.args.args + fn.args.kwonlyargs}
        for node in ast.walk(fn):
            if isinstance(node, ast.Assign):
                names = [t.id for t in node.targets if isinstance(t, ast.Name)]
                for t in node.targets:
                    if isinstance(t, ast.Tuple):
                        names += [e.id for e in t.elts if isinstance(e, ast.Name)]
                if "cause" in names:
                    v = node.value
                    ok = (isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute) and v.func.attr in _DECIDE_FUNCS)
                    ok = ok or fn.name in _REBUILD_OK
                    if not ok:
                        bad.append(f"{fn.name}: cause を判断の口の外から作った(行 {node.lineno})")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "_log":
                what = node.args[2] if len(node.args) > 2 else None
                cause = node.args[3] if len(node.args) > 3 else None
                kws = {k.arg for k in node.keywords}
                person = isinstance(what, ast.Name) and what.id in _PERSON
                if person:
                    ok = isinstance(cause, ast.Name) and cause.id == "cause"
                    ok = ok or (fn.name in _REBUILD_OK and isinstance(cause, ast.Call)
                                and getattr(cause.func, "id", "") == "LlmCall")
                    if not ok:
                        bad.append(f"{fn.name}: 本人の語 {what.id} の原因が判断の口の答えでない(行 {node.lineno})")
                if "read_ns" in kws and not (isinstance(what, ast.Name) and what.id in {"W_READ", "W_ANSWER"}):
                    bad.append(f"{fn.name}: 本人の読んだ・出た以外の行に read_ns(行 {node.lineno})")
    return bad


def test_m2_ast_person_events_come_only_from_decisions():
    assert _cause_problems((SRC / "layer.py").read_text(encoding="utf-8")) == []
    # 読んだ時刻を作るのは層だけ(届く側=deliver・道具・向きのコードは read_ns を作らない)
    for f in ("deliver.py", "device.py", "attention.py", "chat_state.py", "calls.py", "book.py", "port.py"):
        tree = ast.parse((SRC / f).read_text(encoding="utf-8"))
        assert not [k for k in ast.walk(tree) if isinstance(k, ast.keyword) and k.arg in ("read_ns", "sent_ns")], f


def test_m2_ast_negative_control_catches_a_planted_rule():
    planted = '''
class X:
    def _notice_decision(self, T, t_ns, a):
        cause = _P_CONTACT
        self._log(t_ns, a, W_READ, cause, whom=0, received_ns=t_ns, read_ns=t_ns)

    def _engine_reads(self, T, t_ns, a):
        self._log(t_ns, a, W_READ, LlmCall("1:2:-17"), whom=0, read_ns=t_ns)
        self._log(t_ns, a, W_DELIVERED, _P_CONTACT, whom=0, read_ns=t_ns)
'''
    got = _cause_problems(planted)
    assert len(got) == 3, got


# ================================================================= M4 関心の的は判断の後の値
def test_m4_focus_is_the_value_after_the_decisions(monkeypatch):
    with choose(monkeypatch, by_kind(P.K_LOOK, P.K_UP)):
        h = Harness()
        h.agents.registry.activity[1] = int(Activity.MOVING)
        h.run(1)
        h.agents.registry.activity[1] = int(Activity.WAITING)
        h.run(1)  # 暇になった刻み=スマホを見る
        assert int(h.layer.attn.gaze([1])[0]) == AT.GAZE_SCREEN
        assert int(h.layer.attn._focus[1]) == AT.FOCUS_SCREEN  # 判断の後の値=次の刻みの描画と門が読む
        h.run(1)  # 画面の判断=顔を上げる
    assert int(h.layer.attn.gaze([1])[0]) == AT.GAZE_FRONT and int(h.layer.attn._focus[1]) == AT.FOCUS_SURROUND


# ================================================================= L8 通話中の日の途中の再開
def _prefer_calls(monkeypatch):
    real = P.ContactPort._pick
    order = (P.K_ANSWER, P.K_TALK, P.K_WAIT, P.K_CALL, P.K_TO, P.K_READ_NOW, P.K_LOOK)

    def pick(self, ctx, presented):
        kinds = {c.kind: c.id for c in presented}
        for k in order:
            if k in kinds:
                return kinds[k]
        return real(self, ctx, presented)

    monkeypatch.setattr(P.ContactPort, "_pick", pick)


L8_STOP = 97  # 通話の続いている刻み(仮のモデルの規則を差し替えた合成のランで確かめた)


def test_l8_resume_in_the_middle_of_a_call_is_the_straight_run(with_groups, monkeypatch, tmp_path):
    _prefer_calls(monkeypatch)
    kw = dict(KW, ticks=240, checkpoint_every=30, relations="off")
    with c1():
        straight = run_day(tape_path=tmp_path / "s", **kw)
        a = run_day(state_out=tmp_path / "state", stop_at_tick=L8_STOP, tape_path=tmp_path / "a", **kw)
        live = [s for s in a.contact_layer.calls.sessions.values() if s.state is ConvState.PARTICIPATING]
        assert live, "止めた時刻に通話中のセッションが無い(試験の前提)"
        path = tmp_path / "state" / a.resume["state_files"][-1]["file"]
        b = run_day(resume_from=path, tape_path=tmp_path / "b", **kw)
    assert b.final_hash == straight.final_hash
    cp = lambda r: [(int(c.tick), c.behavior_hash, c.full_hash) for c in r.checkpoints if int(c.tick) >= L8_STOP]
    assert cp(b) == cp(straight) and cp(b)
    assert straight.run_manifest_fields()["contact_c1"]["meter"].get("call_turns", 0) > 0


def test_contact_ctx_does_not_use_the_wake_class_field():
    """〔検収 L5〕連絡の判断の文脈の wake_class は使わない(−1)・乱数の鍵は call_id の通し番号。"""
    port = P.ContactPort(seed=1, day_key0=0, step_seconds=60)
    cands = [P.cand(P.K_READ_NOW), P.cand(P.K_LATER), P.cand(P.K_IGNORE)]
    mk = lambda wc: DecisionContext(agent_id=3, step=4, t_ns=4 * STEP_NS, wake_class=wc, condition=-1, cell=0,
                                    call_id=P.call_id_of(4, 3, 17))
    assert port.choose(mk(-1), cands).candidate_id == port.choose(mk(999), cands).candidate_id
    with pytest.raises(ValueError):
        port.choose(dataclasses.replace(mk(-1), call_id="4:3:17"), cands)
