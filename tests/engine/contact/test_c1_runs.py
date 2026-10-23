"""第 6 期 6-4 C1 ランの試験: 既定 off は何も作らない・腕 c1 の合成のラン(manifest の節・節の表・監査・描画の計数)・2 日の再開=
通し(届いた箱・チャット・通話の状態を含む)・腕を取り違えた再開は止まる・ランの種類。"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from shibuya.core.time_consts import STEPS_PER_DAY
from shibuya.engine import manifest_sections as MS
from shibuya.engine import resume as RS
from shibuya.engine import state_ledger as SL
from shibuya.engine.contact import layer as LY
from shibuya.engine.run import run_day
from shibuya.engine.tools import record as TR
from shibuya.engine.tools.groups import GroupList

from tests.engine.contact._c1 import KW, STEP_NS, c1

TPD = int(STEPS_PER_DAY)


@pytest.fixture
def with_groups(monkeypatch):
    """合成の世界(母集団が無い=グループの一覧が無い)に、体 2 人ずつの家族と 10 人ずつの職場を入れる(宛先を作る)。"""
    real = TR.build_fixture

    def build(pop, n_agents, events):
        fx = real(pop, n_agents, events)
        if fx.groups is not None:
            return fx
        ids = np.arange(int(n_agents))
        return dataclasses.replace(fx, groups=GroupList(household_id=ids // 2, org_id=ids // 10))

    monkeypatch.setattr(TR, "build_fixture", build)
    yield


def test_default_off_builds_nothing():
    with c1(on=False):
        r = run_day(**dict(KW, ticks=120))
    assert getattr(r, "contact_layer", "missing") is None
    m = r.run_manifest_fields()
    assert "contact_c1" not in m
    assert not any(str(e.what).startswith("連絡:") for e in r.event_log.events())


def test_c1_synthetic_run_manifest_audit_and_sections(with_groups):
    with c1():  # 関係の層の無いラン=1 対 1 の宛先は家族(グループの一覧)
        r = run_day(**dict(KW, relations="off"))
    m = r.run_manifest_fields()
    cc = m["contact_c1"]
    assert set(cc) == set(LY.CONFIG_KEYS) | set(LY.OBSERVED_KEYS)
    # 節の表(混ざった辞書の子)と層の鍵が同じ
    assert {p.split(".", 1)[1] for p, s in MS.PATHS.items() if p.startswith("contact_c1.") and s == MS.CONFIG} \
        == set(LY.CONFIG_KEYS)
    assert {p.split(".", 1)[1] for p, s in MS.PATHS.items() if p.startswith("contact_c1.") and s == MS.OBSERVED} \
        == set(LY.OBSERVED_KEYS)
    assert MS.unlisted_in_mixed(m) == []
    assert cc["arm"] == "c1" and cc["unnoticed_arm"] == "i" and cc["send_arm"] == "b"
    evs = [e for e in r.event_log.events() if str(e.what).startswith("連絡:")]
    vias = {e.via for e in evs}
    assert {"メッセージ", "グループ"} <= vias, vias
    assert LY.audit_causes(r.event_log.events(), step_ns=STEP_NS)["violations"] == 0
    meter = cc["meter"]
    assert meter["delivered"] > 0 and meter["read_messages"] > 0 and meter["phone_looks"] > 0
    assert cc["chats"]["opened"] > 0 and cc["decisions"]["notice"] > 0 and cc["contacts_source"] == "groups.family"


def _cp(r):
    return [(int(c.tick), c.behavior_hash, c.full_hash) for c in r.checkpoints if int(c.tick) >= TPD]


def test_c1_two_days_resume_is_the_straight_run(with_groups, tmp_path):
    kw = dict(KW, ticks=TPD, sim_days=2, checkpoint_every=60, relations="off")
    with c1():
        straight = run_day(tape_path=tmp_path / "s", **kw)
        a = run_day(state_out=tmp_path / "state", stop_at_tick=TPD, tape_path=tmp_path / "a", **kw)
        path = tmp_path / "state" / a.resume["state_files"][-1]["file"]
        b = run_day(resume_from=path, tape_path=tmp_path / "b", **kw)
    assert b.final_hash == straight.final_hash and _cp(b) == _cp(straight) and _cp(b)
    bundle = RS.read_state(path)
    arm_paths = [p for _k, p in SL.arm_items({"contact": a.contact_layer}, behavior=False)]
    assert arm_paths and set(arm_paths) <= set(bundle.items)
    assert bundle.header["fingerprint"]["contact"] == {"arm": "c1", "unnoticed": "i", "send": "b"}
    ms, mb = straight.run_manifest_fields()["contact_c1"], b.run_manifest_fields()["contact_c1"]
    assert ms["mail"] == mb["mail"] and ms["chats"]["live"] == mb["chats"]["live"]


def test_resuming_with_the_arm_off_stops(with_groups, tmp_path):
    kw = dict(KW, ticks=TPD, sim_days=2, checkpoint_every=60)
    with c1():
        a = run_day(state_out=tmp_path / "state", stop_at_tick=TPD, **kw)
    path = tmp_path / "state" / a.resume["state_files"][-1]["file"]
    with c1(on=False), pytest.raises(ValueError, match="contact"):
        run_day(resume_from=path, **kw)


def test_arm_rows_enter_the_hashes_only_when_the_owner_exists():
    owners = {"contact": None}
    assert SL.arm_items(owners, behavior=True) == () and SL.arm_items(owners, behavior=False) == ()
    keys = {r.key for r in SL.arm_rows() if r.arm == "contact-c1"}
    assert keys == {"CT1D", "CT1A", "CT1AS", "CT1I", "CT1IS", "CT1C", "CT1K", "CT1S", "CT1M", "CT1G", "CT1Q",
                    "CT1B", "CT1H"}  # 〔C2〕宛先の帳・習慣の表
    for r in SL.arm_rows():
        if r.arm == "contact-c1":
            assert r.items and all(it.startswith("contact.") for it in r.items), r.key
    beh = {r.key for r in SL.arm_rows() if r.arm == "contact-c1" and r.behavior == SL.BEHAVIOR}
    # 〔検収 M1・M5〕CT1G・〔C2〕既読の印を候補の文に載せた CT1IS と宛先の帳 CT1B・習慣の表 CT1H
    assert beh == {"CT1D", "CT1A", "CT1I", "CT1IS", "CT1C", "CT1K", "CT1S", "CT1G", "CT1B", "CT1H"}
    # 〔1-3 の (1) の直し〕出来事の id の診断の表は diag・required の行 CT1Q(behavior の行には無い)
    q = SL.row("CT1Q")
    assert (q.behavior, q.restore) == (SL.DIAG, SL.REQUIRED)
    assert {"contact._ct_event_of", "contact.speech._mark_event_of"} <= set(q.items)
    assert not any(it in ("contact._ct_event_of", "contact.speech._mark_event_of")
                   for r in SL.arm_rows() if r.behavior == SL.BEHAVIOR for it in r.items)


def test_cli_run_kind_is_arm(monkeypatch):
    from shibuya import cli
    from shibuya.engine import run_kind as RK

    monkeypatch.delenv(RK.PYTEST_ENV, raising=False)  # 試験の中は種類が test になる=外して腕の数え方を見る
    kw = dict(n_agents=30, seed=1, world_dir=None, n_cells=9, ticks=30, checkpoint_every=30, vocab_version="v3")
    with c1():
        r1 = cli.run(**kw)
    with c1(on=False):
        r0 = cli.run(**kw)
    assert r1.run_kind == "arm" and "contact_c1" in r1.run_manifest_fields()
    assert r0.run_kind != "arm" and "contact_c1" not in r0.run_manifest_fields()


def test_cli_flag_sets_the_arm(monkeypatch):
    """CLI の ``--contact`` は環境変数より強い(組み立てが読む切替口を置く)。"""
    from shibuya import cli
    from shibuya.engine.contact import arm as A

    seen = {}

    def fake_run(**kw):
        seen["arm"] = A.arm()
        raise SystemExit(0)

    monkeypatch.setattr(cli, "run", fake_run)
    with c1(on=False):
        with pytest.raises(SystemExit):
            cli.main(["--contact", "c1", "--agents", "5", "--ticks", "1"])
        assert seen["arm"] == "c1"


def test_the_contact_system_runs_only_on_the_arm():
    from shibuya.engine.systems import conductor as CD
    from shibuya.engine.systems.table import SPECS

    sp = SPECS["contact"]
    assert sp.when == "contact" and sp.timing == "tick" and sp.writes.soa == frozenset()
    assert "CT1*:contact.*" in sp.writes.paths and "E:events.*" in sp.writes.paths
    assert CD.path_allowed("CT1I:contact.mail._inbox", CD.WINDOW_PATHS)
    assert not CD.path_allowed("O39:conv.sessions", CD.WINDOW_PATHS)
