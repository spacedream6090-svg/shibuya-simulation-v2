"""第 2 期 2-3: 体の出来事を出来事の記録(1-3)に載せる(腕 ``--memory-store events`` のときだけ)。

- 既定(腕 ``mem``)では記録に体の出来事は無く、器も作らない(byte-check 19 構成は記録 md23/README.md)。
- 腕 on: 記憶が書く体の出来事(行為の成否・移動の到着・会話の始まりと番・会話の終わり・看板の初見・気づき)が記録に書かれる。
  原因は LLM の呼び出し(この刻みに適用した判断の呼=テープの call_id と同じ形)か過程(``resolve``・``conversation``・
  ``perception``)だけ。
- 器の目印の先は記録の出来事(出どころ None)。記録に無い id・本人でない出来事・種類の合わない出来事は ``ValueError``(負の対照)。
- 想起の候補は前(legacy の形)と同じ: テープの既存の 21 列が腕 on/off で同じ(増えたのは目印の列の値=記録の id だけ)。
  ランの中の想起の 1 つずつの突き合わせは 1-6 の試験 ``tests/engine/memory/test_m0_recall_equivalence.py``(腕 on=記録の目印)。
"""

from __future__ import annotations

import re
from types import SimpleNamespace

import numpy as np
import pytest

from shibuya.agents.state import AgentState, ResultCode
from shibuya.core.time_consts import NS_PER_STEP
from shibuya.engine import memory as M
from shibuya.engine import memory_store as MS
from shibuya.engine import state_ledger as SL
from shibuya.engine.events import body as B
from shibuya.engine.events import log as EV
from shibuya.engine.events import vocab as V
from shibuya.engine.run import run_day
from shibuya.engine.tape import CALLS_SCHEMA, Tape
from shibuya.engine.tools import record as TR

from tests.engine.multiday._md import KW, Capture, arms

CALL_RE = re.compile(r"^(\d+):(\d+):(-?\d+)$")
BODY_FAMILIES = ("行為:", "知覚:", "道具:")


@pytest.fixture(scope="module")
def runs(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("md23_body")
    with arms():
        off = run_day(tape_path=tmp / "off", **KW)
    with pytest.MonkeyPatch.context() as mp, arms(memory_store="events"):
        cap = Capture(mp)
        on = run_day(tape_path=tmp / "on", **KW)
    return off, on, cap, tmp


def _body(log: EV.EventLog) -> list[EV.Event]:
    return [e for e in log.events() if e.what.startswith(BODY_FAMILIES)]


# ================================================================= 既定は不変
def test_default_run_has_no_body_events_and_no_store(runs):
    off, on, _cap, _tmp = runs
    words = off.daily[-1]["events"]["by_what"]
    assert words and not [w for w in words if w.startswith(BODY_FAMILIES)]
    assert "memory_store" not in off.memory_summary
    assert (on.final_hash, on.llm_calls) == (off.final_hash, off.llm_calls)  # 記録と器は結果を変えない


# ================================================================= 腕 on: 体の出来事が記録に
def test_arm_on_writes_the_body_events(runs):
    _off, on, cap, _tmp = runs
    assert cap.log is not None and cap.store is not None
    by = on.daily[-1]["events"]["by_what"]
    for w in ("行為:移動", "行為:会話", "行為:会話の始まり", "行為:会話の終わり", "道具:看板"):
        assert by.get(w, 0) > 0, w
    ev = _body(cap.log)
    acts = [e for e in ev if e.what in B.ACT_FAMILY_WORDS]
    assert any(e.how_much == 0 for e in acts) and any(e.how_much and e.how_much > 0 for e in acts)  # 成功と失敗
    assert {e.how_much for e in acts} <= {int(c) for c in ResultCode}
    assert all(e.how_much is None for e in ev if e.what not in B.ACT_FAMILY_WORDS)
    opened = sum(1 for e in ev if e.what == B.WHAT_TALK_OPEN)
    ended = sum(1 for e in ev if e.what == B.WHAT_TALK_END)
    assert 0 < ended <= opened  # 閉じたセッションの参加者ごとに 1 行(日の終わりに開いたままのセッションは閉じない)


def test_causes_are_the_call_or_a_body_process(runs):
    _off, _on, cap, _tmp = runs
    ev = _body(cap.log)
    kinds = {"llm": 0, "resolve": 0, "conversation": 0, "perception": 0}
    for e in ev:
        c = e.cause
        if isinstance(c, EV.LlmCall):
            m = CALL_RE.match(c.call_id)
            assert m and int(m.group(2)) == e.who and int(m.group(1)) * NS_PER_STEP <= e.t_ns, (c.call_id, e)
            assert e.what in B.ACT_FAMILY_WORDS | {B.WHAT_TALK_OPEN}
            kinds["llm"] += 1
            continue
        assert isinstance(c, EV.Process) and c.name in ("resolve", "conversation", "perception"), (e.what, c)
        kinds[c.name] += 1
        if e.what == B.WHAT_TALK_END:
            assert c.name == "conversation" and e.via == "対面"
        if e.what in (B.WHAT_SIGNAGE, B.WHAT_NOTICE):
            assert c.name == "perception"
        if e.what == B.WHAT_SIGNAGE:
            assert e.origin == TR.SIGNBOARD_ORIGIN and e.where[0] == "poi" and e.received_ns == e.read_ns == e.t_ns
    assert kinds["llm"] > 0 and kinds["resolve"] > 0 and kinds["conversation"] > 0 and kinds["perception"] > 0


def test_store_pointers_are_log_events(runs):
    _off, on, cap, _tmp = runs
    ms, log = cap.store, cap.log
    used = np.flatnonzero(ms._ms_origin >= 0)
    assert used.size > 0 and (ms._ms_origin[used] == 0).all()
    seq = ms._ms_ev_seq[used].astype(np.int64)
    assert np.array_equal(seq, ms._ms_log_seq[used].astype(np.int64)) and (seq >= 0).all()
    pos = log.positions(ms._ms_ev_t_ns[used], seq)
    assert (pos >= 0).all()
    who, what = log.who_what(pos)
    assert np.array_equal(who, used // ms.n_rows)
    assert np.array_equal(MS._KIND_OF_CODE[what], ms._lg_kind[used].astype(np.int64))  # 中身の写像
    s = on.memory_summary["memory_store"]
    assert s["origins"] == {"log": int(used.size), "legacy": 0}
    assert list(s)[-2:] == ["targets_log_live", "targets_log_gone"]  # manifest の 2 欄(末尾)
    assert (s["targets_log_live"], s["targets_log_gone"]) == (int(used.size), 0)
    assert s["counts"]["log_events"] == s["counts"]["remember"] and "legacy_events" not in s["counts"]


def test_recall_candidates_are_the_same_as_the_legacy_form(runs):
    _off, _on, cap, tmp = runs
    t_on, t_off = Tape(tmp / "on"), Tape(tmp / "off")
    for name in CALLS_SCHEMA.names:  # 既存の 21 列(想起の行・種類・対象・B5 の本文・プロンプトの hash)は全部同じ
        assert t_on.column(name) == t_off.column(name), name
    n_rows = cap.store.n_rows
    ids = []
    for rows, eids in zip(t_on.column("recalled_rows"), t_on.column("recalled_event_ids")):
        for r, s in zip(rows, eids):
            if r < n_rows:
                t, q = (int(x) for x in s.split(":"))
                ids.append((t, q))
    assert ids and all(q >= 0 for _t, q in ids)  # 見せた記憶の目印は記録の出来事の id
    pos = cap.log.positions([t for t, _ in ids], [q for _, q in ids])
    assert (pos >= 0).all()


# ================================================================= 器の守り(負の対照)
def _log_and_store(n: int = 3, n_rows: int = 4) -> tuple[EV.EventLog, MS.MemoryStore, B.BodyEventLink]:
    log = EV.EventLog()
    log.begin_step(10 * NS_PER_STEP)
    ms = MS.MemoryStore(n, n_rows, step_seconds=60, minutes_per_step=1.0)
    link = B.BodyEventLink(log)
    ms.attach_events(link)
    return log, ms, link


def _w(link: B.BodyEventLink, who, kind, partner=-1, obj=-1, result=0, cell=5, src=B.SRC_ACT):
    one = lambda x: np.asarray([x], dtype=np.int64)  # noqa: E731
    return link.write(one(who), one(kind), one(partner), one(obj), one(result), one(cell), one(src))


def test_remember_takes_only_ids_in_the_log():
    log, ms, link = _log_and_store()
    t, s = _w(link, 0, 1, obj=7)
    got = ms.remember(0, MS.LoggedEvent(t, s, 1, -1, 7, 0, 5), 1, None)
    assert got.tolist() == [0] and ms.origin(0, 0) is None and ms.event_id(0, 0) == (int(t[0]), int(s[0]))
    assert ms._ms_log_seq[0] == int(s[0])
    # 記録に無い id(負の対照)
    with pytest.raises(ValueError, match="記録に無い出来事"):
        ms.remember(1, MS.LoggedEvent(t, s + 99, 1, -1, 7, 0, 5), 1, None)
    with pytest.raises(ValueError, match="seq は 0 以上"):
        ms.remember(1, MS.LoggedEvent(t, np.asarray([-3]), 1, -1, 7, 0, 5), 1, None)
    # 本人でない出来事・種類の合わない出来事
    with pytest.raises(ValueError, match="who"):
        ms.remember(1, MS.LoggedEvent(t, s, 1, -1, 7, 0, 5), 1, None)
    with pytest.raises(ValueError, match="what"):
        ms.remember(0, MS.LoggedEvent(t, s, 2, -1, 7, 0, 5), 1, None)
    # 目印の形と出どころ
    with pytest.raises(TypeError):
        ms.remember(0, MS.LegacyEvent(t, 1, -1, 7, 0, 5), 1, None)
    with pytest.raises(ValueError, match="出どころは"):
        ms.remember(0, MS.LoggedEvent(t, s, 1, -1, 7, 0, 5), 1, "log")
    # 口の無い器(記録 off・器だけの道)は legacy だけ
    bare = MS.MemoryStore(2, 3, step_seconds=60, minutes_per_step=1.0)
    with pytest.raises(ValueError, match="legacy"):
        bare.remember(0, MS.LoggedEvent(t, s, 1, -1, 7, 0, 5), 1, None)
    off_log = EV.EventLog(enabled=False)
    bare2 = MS.MemoryStore(2, 3, step_seconds=60, minutes_per_step=1.0)
    bare2.attach_events(B.BodyEventLink(off_log))
    with pytest.raises(ValueError, match="legacy"):
        bare2.remember(0, MS.LoggedEvent(t, s, 1, -1, 7, 0, 5), 1, None)
    with pytest.raises(RuntimeError, match="1 回だけ"):
        ms.attach_events(link)


def test_rebuild_keeps_the_log_pointer_from_the_saved_seq():
    """再開: 作り直しは行 M0L(記録の seq)から目印と出どころを戻す(記録の行は再開のランに無くても目印は残る)。"""
    from shibuya.agents.state import AgentState

    agents = AgentState(2, memory_columns=True, memory_n=4)
    layer = M.MemoryLayer(2, 4)
    ms = layer.enable_memory_store(step_seconds=60)
    log = EV.EventLog()
    log.begin_step(3 * NS_PER_STEP)
    ms.attach_events(B.BodyEventLink(log))
    layer.record(agents, 3, np.asarray([0, 1]), np.asarray([1, 4]), np.asarray([-1, -1]), np.asarray([9, -7]),
                 np.asarray([0, 1]), np.asarray([5, 5]))
    before = {n: getattr(ms, n).copy() for n in ("_ms_ev_t_ns", "_ms_ev_seq", "_ms_origin", "_ms_log_seq")}
    saved = ms._ms_log_seq.copy()
    ms2 = M.MemoryLayer(2, 4).enable_memory_store(step_seconds=60)
    ms2._ms_log_seq[:] = saved  # 状態のファイルから戻した列(restore_items は配列の中身を入れ替える)
    layer.memory_store = ms2
    layer.rebuild_memory_store(agents)
    for n, v in before.items():
        assert np.array_equal(getattr(ms2, n), v), n


def test_notice_and_signage_are_perception_events():
    n = 4
    agents = AgentState(n, memory_columns=True, memory_n=8)
    agents.registry.cell[:] = 3
    layer = M.MemoryLayer(n, 8)
    ms = layer.enable_memory_store(step_seconds=60)
    log = EV.EventLog()
    log.begin_step(20 * NS_PER_STEP)
    ms.attach_events(B.BodyEventLink(log))
    layer.after_tick(agents, 20, salient_events=[SimpleNamespace(cell=6, noticed=[0, 1])], signage=[(2, 7)])
    ev = list(log.events())
    notice = [e for e in ev if e.what == B.WHAT_NOTICE]
    sign = [e for e in ev if e.what == B.WHAT_SIGNAGE]
    assert sorted(e.who for e in notice) == [0, 1] and all(e.where == ("cell", 6) for e in notice)
    assert [(e.who, e.where) for e in sign] == [(2, ("poi", 7))]
    assert all(isinstance(e.cause, EV.Process) and e.cause.name == "perception" for e in notice + sign)
    assert all(e.how_much is None for e in notice + sign)
    assert ms.summary()["origins"] == {"log": 3, "legacy": 0}


def test_signboard_rows_of_the_1_7_arm_are_reused():
    log = EV.EventLog()
    t = 30 * NS_PER_STEP
    log.begin_step(t)
    first = log.append(EV.Event(t_ns=t, who=2, what=TR.SIGNBOARD_WHAT, where=("poi", 7), received_ns=t, read_ns=t,
                                origin=TR.SIGNBOARD_ORIGIN, cause=TR.SIGNBOARD_CAUSE))
    link = B.BodyEventLink(log, signboard_reads=True)
    n0 = len(log)
    ts, seqs = _w(link, 2, 11, obj=7, src=B.SRC_SIGNAGE)
    assert (int(ts[0]), int(seqs[0])) == first and len(log) == n0  # 1-7 の行を目印にする(同じ読みを 2 行にしない)
    ts, seqs = _w(link, 3, 11, obj=7, src=B.SRC_SIGNAGE)  # 1-7 の行が無い体はこの口が書く
    assert len(log) == n0 + 1 and log.get((int(ts[0]), int(seqs[0]))).who == 3


def test_conversation_end_rows_per_participant():
    log = EV.EventLog()
    log.begin_step(5 * NS_PER_STEP)
    link = B.BodyEventLink(log)
    s = SimpleNamespace(participants=[4, 9, 2], cell=11)
    assert link.conversation_end([s], np.zeros(20, dtype=np.int64)) == 3
    rows = [(e.who, e.whom, e.where, e.via) for e in log.events()]
    assert rows == [(4, 9, ("cell", 11), "対面"), (9, 4, ("cell", 11), "対面"), (2, 4, ("cell", 11), "対面")]


# ================================================================= 表と台帳
def test_word_tables_agree_with_the_memory_and_the_vocab():
    want = {"buy": "購入", "eat": "食事", "queue": "並ぶ", "move": "移動", "board": "乗車", "sleep": "就寝",
            "talk": "会話", "report": "通報", "help": "手伝い"}
    assert {M.KIND_NAMES[k]: w for k, w in B.KIND_ACT_WORD.items()} == want
    assert set(B.KIND_ACT_WORD.values()) <= set(V.ACT_WORDS)
    assert (M._SRC_ACT, M._SRC_ARRIVE, M._SRC_TALK_OPEN, M._SRC_TURN, M._SRC_NOTICE, M._SRC_SIGNAGE) == (
        B.SRC_ACT, B.SRC_ARRIVE, B.SRC_TALK_OPEN, B.SRC_TURN, B.SRC_NOTICE, B.SRC_SIGNAGE)
    for k, w in B.KIND_ACT_WORD.items():
        assert B.kind_of_what(V.code_of(V.word(V.FAMILY_ACT, w))) == k
    assert B.kind_of_what(V.code_of(B.WHAT_TALK_OPEN)) == M.EVENT_KINDS["talk"]
    assert B.kind_of_what(V.code_of(B.WHAT_NOTICE)) == M.EVENT_KINDS["notice"]
    assert B.kind_of_what(V.code_of(B.WHAT_SIGNAGE)) == M.EVENT_KINDS["signage"]
    assert B.kind_of_what(V.code_of("過程:rail")) == 0
    # 〔第 6 期 6-4 C1〕体の過程の名の後ろに網の名 contact を足した
    assert V.BODY_PROCESSES == ("resolve", "conversation") and V.CAUSE_PROCESS_NAMES[-3:-1] == V.BODY_PROCESSES
    assert V.CAUSE_PROCESS_NAMES[-1:] == V.CONTACT_PROCESSES == ("contact",)
    assert B.WHAT_SIGNAGE == TR.SIGNBOARD_WHAT and V.FAMILIES[-2] == "知覚" and V.FAMILIES[-1] == "連絡"


def test_m0l_is_an_arm_row_present_only_with_the_store():
    r = SL.row("M0L")
    assert (r.behavior, r.restore, r.arm, r.items) == (SL.NO, SL.REQUIRED, "memory-store",
                                                      ("mem_layer.memory_store._ms_log_seq",))
    layer = M.MemoryLayer(2, 3)
    assert SL.arm_items({"mem_layer": layer}, behavior=False) == ()  # 既定の腕(器が None)=入らない
    layer.enable_memory_store(step_seconds=60)
    assert ("M0L", "mem_layer.memory_store._ms_log_seq") in SL.arm_items({"mem_layer": layer}, behavior=False)
    assert ("M0L", "mem_layer.memory_store._ms_log_seq") not in SL.arm_items({"mem_layer": layer}, behavior=True)
    assert all(k != "M0L" for k, _ in SL.full_items() + SL.behavior_items())


# ================================================================= 検収の直し(親の判断 M3・L1・L4)
def test_pointer_beyond_the_retention_window_recalls_only_the_summary():
    """〔親の判断 M3〕目印の先が記録の保持窓(7 日)の外に出た行=要旨(注釈と強さ)だけで想起に使う・本文は無い。

    LegacyEvent にはしない(出どころ None・目印はそのまま)。``ValueError`` にならない。窓の中はそのまま。
    """
    log, ms, link = _log_and_store(n=2, n_rows=4)
    t, s = _w(link, 0, 7, partner=1, obj=5, src=B.SRC_TURN)
    ms.remember(0, MS.LoggedEvent(t, s, 7, 1, 5, 0, 5), 2, None, annotation=["駅前で話した"])
    tau = -50.0  # 窓の外まで強さが残る行(想起の閾値を下げる=言葉の段の境目も同じ τ)
    near = ms.recall(0, int(t[0]) + EV.NS_PER_DAY, 2, cue=MS.Cue(partner=1), tau=tau)
    assert [(v.grain, v.kind, v.partner, v.obj, v.annotation) for v in near] == [("そのまま", 7, 1, 5, "駅前で話した")]
    far_ns = (int(t[0]) // EV.NS_PER_DAY + EV.RETENTION_DAYS + 1) * EV.NS_PER_DAY
    far = ms.recall(0, far_ns, 2, cue=MS.Cue(partner=1, obj=5), tau=tau)
    assert len(far) == 1
    v = far[0]
    assert (v.grain, v.kind, v.partner, v.obj, v.result, v.cell) == ("要旨だけ", 0, -1, -1, 0, -1)
    assert v.annotation == "駅前で話した" and v.origin is None and v.event_id == (int(t[0]), int(s[0]))
    assert ms.last_recall.filled == 1  # 本文が無い=手がかりの一致には使わず、強さの順の補いで出る
    assert MS.to_item(v, ms.ns_per_step).gist == "駅前で話した"  # 描画へ渡す形も落ちない
    # 窓のちょうど内側(D − 窓 日の出来事)はそのまま
    edge = (int(t[0]) // EV.NS_PER_DAY + EV.RETENTION_DAYS) * EV.NS_PER_DAY
    assert ms.recall(0, edge, 2, cue=MS.Cue(partner=1), tau=tau)[0].grain == "そのまま"


def test_legacy_path_with_the_log_off_is_the_1_6_form(tmp_path):
    """〔検収 L1〕腕 events+記録 off(器だけの道)=1-6 と同じ legacy の行(目印 −1−番地)・final とテープの既存の列も同じ。"""
    with arms():
        off = run_day(tape_path=tmp_path / "off", **KW)
    prev = EV.enabled()
    EV.set_enabled(False)
    try:
        with arms(memory_store="events"):
            on = run_day(tape_path=tmp_path / "on", **KW)
    finally:
        EV.set_enabled(prev)
    assert (on.final_hash, on.llm_calls) == (off.final_hash, off.llm_calls)
    s = on.memory_summary["memory_store"]
    assert s["origins"]["log"] == 0 and s["origins"]["legacy"] == s["rows"] > 0
    assert (s["targets_log_live"], s["targets_log_gone"]) == (0, 0)
    t_on, t_off = Tape(tmp_path / "on"), Tape(tmp_path / "off")
    for name in CALLS_SCHEMA.names:
        assert t_on.column(name) == t_off.column(name), name
    n_rows = int(s["n_rows"])
    seen = 0
    for agent, rows, ids in zip(t_on.column("agent_id"), t_on.column("recalled_rows"), t_on.column("recalled_event_ids")):
        for r, x in zip(rows, ids):
            if r < n_rows:
                assert int(x.split(":")[1]) == -1 - (int(agent) * n_rows + int(r))  # 仮の出来事=行と同じ番地(1-6)
                seen += 1
    assert seen > 0


def test_body_link_fields_cannot_be_rebound():
    """〔検収 L4〕口の欄(記録・看板の印)は組み立ての 1 回だけ=付け替えと消去は落ちる(負の対照)。"""
    link = B.BodyEventLink(EV.EventLog())
    with pytest.raises(AttributeError, match="付け替えられない"):
        link.log = EV.EventLog()
    with pytest.raises(AttributeError, match="付け替えられない"):
        link.signboard_reads = True
    with pytest.raises(AttributeError, match="消せない"):
        del link.log
