"""第 6 期 6-4 C1 腕 c1(mock 5,000 体・1 日・世界の資産)の試験(slow・data が要る)。

- ランが最後まで回る・届く/気づく/読む/返すの記録が 1-3 の記録に ``via`` つきで出る。
- エンジンが時刻や回数を決めていない(読む・送る・見る・かける・出る・切るの原因は本人の判断の呼び・時刻は判断の刻みか次の
  窓の境目=負の対照は ``test_c1_flow`` の差し替え)。
- 電話は窓の境目で届く(着信の時刻=かけた刻みの次の窓の頭)。
- マナーモードとかばんの中で通知が弱い(刺激の段の数=道具の状態ごと)。
- 画面を見ている間の周辺視の粒度が落ちる(B5 の近接の行が周辺視の行に替わった呼びがある=形)。
- 割り込めなかった出来事の 3 つの腕の数(計器=合否なし)。
- 再開=通し(日の途中で止めて再開=final と checkpoint が通しと同じ)。
"""

from __future__ import annotations

import pyarrow.parquet as pq
import pytest

from shibuya.engine.contact.layer import W_DIAL, W_RING, W_VIDEO_DIAL, audit_causes
from shibuya.perception import contact_view as CV

from tests.engine.contact._c1 import STEP_NS, WORLD, c1

pytestmark = [pytest.mark.slow, pytest.mark.requires_data("world_v2:w17_schedule.parquet")]

KW5 = dict(n_agents=5000, seed=1, world_dir=str(WORLD), vocab_version="v3")


@pytest.fixture(scope="module")
def world_runs(tmp_path_factory):
    from shibuya import cli

    base = tmp_path_factory.mktemp("c1w")
    out = {}
    for arm in ("i", "ii", "iii"):
        with c1(unnoticed=arm):
            out[arm] = cli.run(tape_path=str(base / f"tape_{arm}"), **KW5)
    out["tape_i"] = base / "tape_i"
    return out


def test_world_5000_one_day_records_with_via_and_audit(world_runs):
    r = world_runs["i"]
    m = r.run_manifest_fields()["contact_c1"]
    evs = [e for e in r.event_log.events() if str(e.what).startswith("連絡:")]
    vias = {e.via for e in evs}
    assert {"メッセージ", "グループ"} <= vias
    whats = {e.what for e in evs}
    assert {"連絡:送った", "連絡:届いた", "連絡:読んだ", "連絡:スマホを見た", "連絡:顔を上げた"} <= whats
    assert "連絡:既読" not in whats  # 〔検収 M3〕既読は読んだの whom から作る
    for e in evs:
        if e.what == "連絡:届いた":
            assert e.received_ns == e.t_ns
        if e.what == "連絡:読んだ":
            assert e.read_ns == e.t_ns and e.received_ns is not None
    a = audit_causes(r.event_log.events(), step_ns=STEP_NS)
    assert a["events"] > 1000 and a["violations"] == 0, a
    meter = m["meter"]
    assert meter["delivered"] > 0 and meter["read_messages"] > 0 and meter["replies"] > 0
    assert meter["later"] > 0 and meter["ignored"] > 0 and meter["phone_looks"] > 0
    assert m["chats"]["opened"] > 0 and sum(m["read_delay_minutes"].values()) == meter["read_messages"]


def test_world_ring_arrives_at_the_window_boundary(world_runs):
    r = world_runs["i"]
    evs = list(r.event_log.events())
    # 〔第 4 期 4-3 段 10〕同じ組が 1 日に 2 回以上かけることがある(差し替えの世界の 5,000 体で 1 組)=組ごとにかけた時刻の集まり
    # で見る(前は組ごとに最後の 1 回だけを持っていた)
    # 〔第 6 期 6-4 C2 検収 M1〕ビデオ通話のかけた語(W_VIDEO_DIAL)も集め、(かけた人・相手・via)で突き合わせる
    dial: dict[tuple, set] = {}
    for e in evs:
        if e.what in (W_DIAL, W_VIDEO_DIAL):
            dial.setdefault((e.who, e.whom, e.via), set()).add(e.t_ns)
    rings = [e for e in evs if e.what == W_RING]
    assert {e.via for e in rings} <= {"通話", "ビデオ通話"}
    for e in rings:  # かけた刻みの次の窓の頭(幅=刻み 60 秒)
        t_calls = dial.get((e.whom, e.who, e.via), set())
        assert (e.t_ns - STEP_NS) in t_calls, (e.t_ns, sorted(t_calls))
    assert r.run_manifest_fields()["batching"]["boundary_events"] >= len(rings)


def test_world_manner_mode_and_bag_are_weaker(world_runs):
    meter = world_runs["i"].run_manifest_fields()["contact_c1"]["meter"]
    st = {k.split(":", 1)[1]: v for k, v in meter.items() if k.startswith("stimulus_state:")}
    # マナーモード+かばん=届かないだけ(段の形)。手に持つ体の「届かない」は電池が切れた体だけ(電源の切れた数以下)
    assert not any(k.startswith("マナー・かばん:") and not k.endswith(":届かない") for k in st), st
    assert st.get("音・手:届かない", 0) + st.get("マナー・手:届かない", 0) <= 0 or meter.get("devices_off", 0) > 0
    strong = lambda pre: sum(v for k, v in st.items() if k.startswith(pre) and k.endswith(":強い"))  # noqa: E731
    total = lambda pre: sum(v for k, v in st.items() if k.startswith(pre))  # noqa: E731
    assert total("音・手") and total("マナー") and strong("マナー") / total("マナー") < strong("音・手") / total("音・手")


def test_world_peripheral_vision_coarsens_the_rendered_input(world_runs):
    t = pq.read_table(world_runs["tape_i"] / "calls.parquet", columns=["b5_text"])
    head = CV.B5_PERIPHERAL_NEAR_LINE.split("{")[0]
    n = sum(1 for x in t.column("b5_text").to_pylist() if head in str(x))
    assert n > 0  # 画面を見ていて起きた体の B5 の近接の行は周辺視の行(誰か・何をしているかは無い)


def test_world_unnoticed_three_arms_are_counted(world_runs):
    ms = {a: world_runs[a].run_manifest_fields()["contact_c1"] for a in ("i", "ii", "iii")}
    for a, m in ms.items():
        assert m["unnoticed_arm"] == a
        assert "salient_reached" in m["salient"]
    # 世界の状態の門(顕著行為の気づいた体から外す)は 3 つの腕で同じ規則(数は判断の違いで揺れてよい=計器)
    for a in ("i", "ii", "iii"):
        assert ms[a]["meter"]["salient_blocked"] <= ms[a]["meter"]["salient_reached"]


def test_world_resume_mid_day_is_the_straight_run(world_runs, tmp_path):
    from shibuya import cli

    straight = world_runs["i"]
    with c1(unnoticed="i"):
        a = cli.run(state_out=str(tmp_path / "state"), stop_at_tick=720, tape_path=str(tmp_path / "a"), **KW5)
        path = tmp_path / "state" / a.resume["state_files"][-1]["file"]
        b = cli.run(resume_from=str(path), tape_path=str(tmp_path / "b"), **KW5)
    assert b.final_hash == straight.final_hash
    assert [(c.tick, c.behavior_hash, c.full_hash) for c in b.checkpoints] == \
        [(c.tick, c.behavior_hash, c.full_hash) for c in straight.checkpoints if c.tick >= 720]
