"""第 1 期 1-2 知覚の分離: ``Percept`` は刻みの中の一時(口の約束 1-2 の約束 (3)・段 C の守り)。

(a) ``TickScratch`` の欄 ``percepts``・書く系は decide だけ(宣言 ``writes.scratch``)・宣言の外の系が書くと段 C が止める
(b) 状態台帳の行 P(軸 1 no・軸 2 discardable・道筋なし)=どちらのハッシュにも状態のファイルにも入らない
(c) ランの中: 刻みの頭で空になる・decide が書くのはその刻みに描いた体の Percept(刻みが合う・読むだけの写し)・
    描画は Percept を刻みをまたいで持たない(ランの後の描画の属性に Percept が無い)
(d) 段 B と番兵の検査(``SHIBUYA_SYSTEMS_CHECK``)の上でも回る=宣言の外の書きが無い
(e) 〔検収 M1〕艦隊で録ったテープの再生(D-58): 後の刻みに届く呼の結果は ``run_day.replay_inbox``(状態台帳 O96=軸 2
    required=full-hash と状態のファイルに入る)に置かれる。``Percept`` はそこに入らない(結果 ``BridgeResult`` に欄が無い・
    直列化した中身にも無い)・状態のファイルにも無い・再生の full-hash は HEAD の写し(1-2 の前)と全部の checkpoint で同じ・
    Percept を作らない形と比べても同じ
"""

from __future__ import annotations

import dataclasses
from types import MappingProxyType

import pytest

from shibuya.engine import state_ledger as SL
from shibuya.engine.systems import boxes as BX
from shibuya.engine.systems import conductor as CD
from shibuya.engine.systems import guard as G
from shibuya.engine.systems.table import SPECS, SYSTEMS
from shibuya.perception import facts as F


# ---------------------------------------------------------------- (a)
def test_scratch_field_and_its_single_writer():
    assert "percepts" in BX.SCRATCH_FIELDS
    writers = [s.name for s in SYSTEMS if "percepts" in s.writes.scratch]
    assert writers == ["decide"]
    assert "scratch.percepts" in SPECS["decide"].reads.box
    readers = [s.name for s in SYSTEMS if "percepts" in s.reads.scratch]
    assert readers == []  # 今は読む系が無い(1-8 の判断の口が読む)


def test_stage_c_stops_a_write_from_another_system():
    sc = BX.TickScratch()
    with G.system_scope("decide", SPECS["decide"].writes.soa, SPECS["decide"].writes.scratch,
                        SPECS["decide"].writes.buffers, SPECS["decide"].writes.paths):
        sc.percepts = MappingProxyType({})
    for name in ("observe", "memory", "perceive_prepare"):
        sp = SPECS[name]
        with G.system_scope(name, sp.writes.soa, sp.writes.scratch, sp.writes.buffers, sp.writes.paths):
            with pytest.raises(AttributeError, match="percepts"):
                sc.percepts = MappingProxyType({})


def test_reset_empties_the_field():
    sc = BX.TickScratch()
    object.__setattr__(sc, "percepts", MappingProxyType({1: "x"}))
    sc.reset(None)
    assert sc.percepts is None
    strict = BX.TickScratchStrict()
    strict.reset(BX.UNSET)
    with pytest.raises(AttributeError, match="percepts"):
        _ = strict.percepts


# ---------------------------------------------------------------- (b)
def test_ledger_row_p_is_out_of_both_hashes():
    row = SL.row("P")
    assert (row.place, row.behavior, row.restore, row.items) == (SL.EXTERNAL, SL.NO, SL.DISCARDABLE, ())
    assert not row.in_full and not row.in_behavior
    assert all(k != "P" for k, _ in SL.full_items())
    assert all("percept" not in path for _k, path in SL.full_items())
    assert all("percept" not in str(item) for item in SL.behavior_items())


# ---------------------------------------------------------------- (c)
#: 合成の世界の小さなラン(朝 8 時まで=呼がある)。
KW = dict(n_agents=80, seed=3, ticks=480, n_cells=9, processes=False, vocab_version="v3")


def _run_with_watch(monkeypatch, **kw):
    from shibuya.engine.run import run_day

    seen: dict = {"steps": [], "heads": 0, "box": None, "ctx": {}}
    orig = CD.run_system
    first = {"name": None}

    def watch(spec, ctx, box):  # noqa: ANN001
        if ctx is not None and spec.timing == "tick":
            if first["name"] is None:
                first["name"] = spec.name
            if spec.name == first["name"]:
                # 刻みの頭で空にした直後(この刻みの最初の系の前)
                assert box.scratch.percepts is None
                seen["heads"] += 1
        out = orig(spec, ctx, box)
        if spec.name == "decide":
            pc = box.scratch.percepts
            assert isinstance(pc, MappingProxyType)
            seen["steps"].append((int(ctx.T), dict(pc)))
            seen["ctx"][int(ctx.T)] = (int(ctx.t_ns), int(ctx.tod_s))
            seen["box"] = box
        return out

    monkeypatch.setattr(CD, "run_system", watch)
    res = run_day(**kw)
    return res, seen


def test_percepts_live_only_inside_their_step(monkeypatch):
    res, seen = _run_with_watch(monkeypatch, **KW)
    assert seen["heads"] == 480 and len(seen["steps"]) == 480
    n = 0
    for T, pc in seen["steps"]:
        for aid, p in pc.items():
            assert isinstance(p, F.Percept)
            assert (p.step, p.agent_id) == (T, aid)
            assert all(getattr(p, k) is None for k in F.EMPTY_FIELDS)
            # 検収 L9: 時刻の見方は進行役の刻みの時刻(TickCtx の t_ns・tod_s)と同じ値
            assert (p.t_ns, p.time_view.tod_s) == seen["ctx"][T]
            n += 1
    assert n > 0
    assert n == res.llm_calls  # 呼んだ体ごとに 1 つ(本物の描画の道)
    # 描画は Percept を持ち越さない(属性の値に Percept が無い・刻みの前計算の SceneView は今の刻みの物だけ)
    rend = seen["box"].layers.renderer  # 状態台帳の持ち主 renderer=知覚の描画そのもの
    for k, v in vars(rend).items():
        assert not isinstance(v, F.Percept), k
        if isinstance(v, (list, tuple, dict)):
            vals = v.values() if isinstance(v, dict) else v
            assert not any(isinstance(x, F.Percept) for x in vals), k
    last_T = seen["steps"][-1][0]
    assert all(s.cell >= -10**9 for s in rend._tickc.scenes.values())
    assert rend._tickc.tick == last_T
    # 検収 L8: 刻みの外の箱(到着待ち・保留・艦隊の在途)にも Percept が無い
    llm = seen["box"].llm
    for name in ("pending", "fleet_deferred", "fleet_inflight", "replay_inbox"):
        assert not _holds_percept(getattr(llm, name)), name


def _holds_percept(v, depth: int = 0) -> bool:
    """値の中(列・辞書・dataclass の欄)に ``Percept`` があるか、``percept`` という名の欄があるか。"""
    if depth > 8:
        return False
    if isinstance(v, F.Percept):
        return True
    if dataclasses.is_dataclass(v) and not isinstance(v, type):
        return any(f.name == "percept" or _holds_percept(getattr(v, f.name), depth + 1) for f in dataclasses.fields(v))
    if isinstance(v, dict):
        return any(_holds_percept(x, depth + 1) for x in v.values())
    if isinstance(v, (list, tuple, set, frozenset)):
        return any(_holds_percept(x, depth + 1) for x in v)
    return False


def test_stub_renderer_writes_an_empty_mapping(monkeypatch):
    res, seen = _run_with_watch(monkeypatch, **{**KW, "renderer": "stub"})
    assert len(seen["steps"]) == 480 and res.llm_calls > 0
    assert all(pc == {} for _T, pc in seen["steps"])


def test_percepts_are_not_in_the_final_or_the_state_files(monkeypatch, tmp_path):
    """Percept の有無は状態に入らない: 描いた Percept を捨てても(scratch に書かない形)final は同じ。"""
    from shibuya.engine.run import run_day
    from shibuya.engine.systems import decide as DC

    kw = {**KW, "checkpoint_every": 120}
    base = run_day(**kw)
    assert base.llm_calls > 0
    orig_proxy = DC.MappingProxyType
    monkeypatch.setattr(DC, "MappingProxyType", lambda d: orig_proxy({}))
    blank = run_day(**kw)
    assert base.final_hash == blank.final_hash
    assert [c.full_hash for c in base.checkpoints] == [c.full_hash for c in blank.checkpoints]


# ---------------------------------------------------------------- (d)
def test_runs_under_the_stage_b_and_sentinel_checks(monkeypatch):
    from shibuya.engine.run import run_day

    monkeypatch.setenv("SHIBUYA_SYSTEMS_CHECK", "1")  # 段 B(全部の刻み)+番兵の scratch(T4)
    res = run_day(**KW)
    assert res.final_hash and res.llm_calls > 0
    assert dataclasses.is_dataclass(F.Percept)


# ---------------------------------------------------------------- (e) 検収 M1: 艦隊のテープの再生
#: 検収役の形(偽 vLLM 2 台・受理枠 8・遅れ 0.02 秒・合成 120 体・40 刻み・語彙 v3・予算 30・4 刻みごとの checkpoint)。
#: 描画は本物(``renderer`` を渡さない=Percept を作る道)。
FLEET_KW = dict(n_agents=120, seed=1, ticks=40, processes=False, population=False, world_dir=None,
                checkpoint_every=4, sleep_suppression=False, vocab_version="v3", budget=30.0)
FLEET_CELLS = 16
#: 1-2 の前の src(この枝の土台)。再生の full-hash を比べる相手。〔rebase〕1-4・1-6・1-9 を取り込んだ本体 ``a3a8104``
#: (1-2 の枝を作った時の土台は ``136fdbb``=記録 p12/README.md §15)。
BASE_COMMIT = "a3a8104"

_REPLAY_CHILD = r"""
import json, sys
import shibuya
from shibuya.engine.run import run_day
from shibuya.world.state import World

class BoomLLM:
    def complete(self, request):
        raise AssertionError("再生の中で LLM を呼んだ")

kw = json.loads(sys.argv[2])
cells = kw.pop("_cells")
res = run_day(mode="replay", replay=sys.argv[1], llm=BoomLLM(), world=World.synthetic(n_cells=cells, seed=1), **kw)
print(json.dumps({"src": shibuya.__file__, "full": [c.full_hash for c in res.checkpoints],
                  "behavior": [c.behavior_hash for c in res.checkpoints], "final": res.final_hash,
                  "misses": int(res.tape_miss_count), "calls": int(res.llm_calls)}))
"""


@pytest.fixture
def recorded_tape(tmp_path):
    """偽 vLLM で録ったテープ(作業木の src)。"""
    from shibuya.engine.run import run_day
    from shibuya.world.state import World
    from tests.engine.test_tape_deferred import make_client
    from tests.llm.test_fleet import FakeVLLM

    servers = [FakeVLLM(), FakeVLLM()]
    try:
        for srv in servers:
            srv.total_delay_s = 0.02
        client = make_client(servers, per_replica_in_flight=4, queue_capacity=8)
        rec = run_day(fleet=client, tape_path=tmp_path / "tape", fleet_wait_s=2.0,
                      world=World.synthetic(n_cells=FLEET_CELLS, seed=1), **FLEET_KW)
    finally:
        for srv in servers:
            srv.close()
    assert rec.llm_calls > 0
    return tmp_path / "tape", rec


def _replay(monkeypatch, tape, *, drop_percepts: bool = False):
    """作業木の src で再生し、刻みごとの到着待ち(``replay_inbox``)を見る。"""
    from shibuya.engine.run import run_day
    from shibuya.engine.state_hashes import to_state
    from shibuya.perception import renderer as R
    from shibuya.world.state import World
    from tests.engine.test_tape_wiring import BoomLLM

    seen = {"inbox_items": 0, "percepts": 0, "bad": []}
    orig = CD.run_system

    def watch(spec, ctx, box):  # noqa: ANN001
        out = orig(spec, ctx, box)
        if spec.name == "decide":
            seen["percepts"] += len(box.scratch.percepts)
            inbox = box.llm.replay_inbox
            seen["inbox_items"] += sum(len(v) for v in inbox.values())
            if _holds_percept(inbox):
                seen["bad"].append(("held", int(ctx.T)))
            raw = to_state(inbox)
            if b"percept" in raw or b"Percept" in raw:
                seen["bad"].append(("serialized", int(ctx.T)))
        return out

    monkeypatch.setattr(CD, "run_system", watch)
    if drop_percepts:  # Percept を作らない形(描画の結果から外す)=状態に入っていなければ full-hash は同じ
        orig_render = R.Renderer.render
        monkeypatch.setattr(R.Renderer, "render",
                            lambda self, *a, **k: dataclasses.replace(orig_render(self, *a, **k), percept=None))
    res = run_day(mode="replay", replay=tape, llm=BoomLLM(), world=World.synthetic(n_cells=FLEET_CELLS, seed=1),
                  **FLEET_KW)
    monkeypatch.undo()
    return res, seen


def test_replay_inbox_never_holds_a_percept(recorded_tape, monkeypatch, tmp_path):
    from shibuya.engine.llm_bridge import BridgeResult
    from shibuya.engine.run import run_day
    from shibuya.engine import resume as RS
    from shibuya.engine.state_hashes import to_state
    from shibuya.llm.fleet import FleetBridgeResult
    from shibuya.world.state import World

    assert "percept" not in {f.name for f in dataclasses.fields(BridgeResult)}
    assert "percept" not in {f.name for f in dataclasses.fields(FleetBridgeResult)}
    tape, rec = recorded_tape
    res, seen = _replay(monkeypatch, tape)
    assert res.tape_miss_count == 0 and res.final_hash == rec.final_hash
    assert seen["inbox_items"] > 0 and seen["percepts"] > 0  # 到着待ちの道と Percept の道を両方通った
    assert seen["bad"] == []
    # 状態のファイルにも Percept と欄の名が無い(再生と状態の口は一緒に使えない=10d の範囲の外なので、艦隊で録る
    # ランを在途の呼のある刻みで止めて書く=保留・艦隊の在途・到着待ちの箱がファイルに入る形)
    from tests.engine.test_tape_deferred import make_client
    from tests.llm.test_fleet import FakeVLLM

    servers = [FakeVLLM(), FakeVLLM()]
    try:
        for srv in servers:
            srv.total_delay_s = 0.02
        st = run_day(fleet=make_client(servers, per_replica_in_flight=4, queue_capacity=8),
                     tape_path=tmp_path / "tape_st", fleet_wait_s=2.0, state_out=tmp_path / "st", stop_at_tick=21,
                     world=World.synthetic(n_cells=FLEET_CELLS, seed=1), **FLEET_KW)
    finally:
        for srv in servers:
            srv.close()
    files = sorted((tmp_path / "st").glob("state-T*"))
    assert files and st.resume["state_files"]
    items = RS.read_state(files[-1]).items
    assert "run_day.replay_inbox" in items and "run_day.pending" in items
    blob = to_state(items)
    assert b"percept" not in blob and b"Percept" not in blob


def test_replay_full_hash_does_not_see_percepts(recorded_tape, monkeypatch):
    """Percept を作る形と作らない形で、再生の全部の checkpoint の full-hash が同じ(Percept は状態に入らない)。"""
    tape, _rec = recorded_tape
    a, _ = _replay(monkeypatch, tape)
    b, _ = _replay(monkeypatch, tape, drop_percepts=True)
    assert [c.full_hash for c in a.checkpoints] == [c.full_hash for c in b.checkpoints]
    assert [c.behavior_hash for c in a.checkpoints] == [c.behavior_hash for c in b.checkpoints]


def test_replay_full_hash_matches_the_head_copy(recorded_tape, tmp_path):
    """検収 M1 の再現の形: 同じテープを HEAD の写し(1-2 の前の src)と作業木の src で再生し、全部の checkpoint の
    full-hash・behavior-hash・final が同じ(別々のプロセス・``PYTHONHASHSEED=0``)。"""
    import io
    import json
    import os
    import shutil
    import subprocess
    import sys
    import tarfile
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    if shutil.which("git") is None:
        pytest.skip("git が無い")
    r = subprocess.run(["git", "-C", str(root), "archive", "--format=tar", BASE_COMMIT, "src", "docs/bench/anchors",
                        "docs/design/v2-budget-declaration.md"], capture_output=True)
    if r.returncode != 0:
        pytest.skip(f"commit {BASE_COMMIT} が無い")
    head = tmp_path / "head_src"
    with tarfile.open(fileobj=io.BytesIO(r.stdout)) as tf:
        tf.extractall(head, filter="data")
    (head / "data" / "calendar").mkdir(parents=True)
    shutil.copy(root / "data" / "calendar" / "syukujitsu.csv", head / "data" / "calendar" / "syukujitsu.csv")
    tape, rec = recorded_tape
    kw = json.dumps({**FLEET_KW, "_cells": FLEET_CELLS})

    def child(src: Path) -> dict:
        env = dict(os.environ, PYTHONPATH=str(src), PYTHONIOENCODING="utf-8", PYTHONHASHSEED="0")
        c = subprocess.run([sys.executable, "-c", _REPLAY_CHILD, str(tape), kw], cwd=str(root), env=env,
                           capture_output=True, text=True, encoding="utf-8", timeout=600)
        assert c.returncode == 0, c.stderr[-3000:]
        return json.loads(c.stdout.strip().splitlines()[-1])

    h = child(head / "src")
    w = child(root / "src")
    assert "head_src" in h["src"] and "head_src" not in w["src"]
    assert h["misses"] == w["misses"] == 0 and h["calls"] == w["calls"] == rec.llm_calls
    assert len(h["full"]) == FLEET_KW["ticks"] // FLEET_KW["checkpoint_every"]
    assert w["behavior"] == h["behavior"] and w["final"] == h["final"]
    assert w["full"] == h["full"]
