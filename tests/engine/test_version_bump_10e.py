"""10e(版上げ 1 回目)の試験: E2 の期限つきの辞書の掃除・O64 の分類の確かめ(E1 の試験は状態台帳の試験の中)。

記録: ``docs/bench/analysis/wallbounce-1012/10e/README.md``。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from tests import _data_ids as D

import shibuya.engine.run as RUN
from shibuya.engine.systems import state_io as SIO  # 1-0: full-hash の呼び出しは state_io を通す(差し替えの的)
from shibuya.engine.conversation import (
    PAIR_INVITE_REFRACTORY_TICKS,
    SPEAKER_INVITE_REFRACTORY_TICKS,
    ConversationManager,
)
from shibuya.engine.run import run_day

WORLD_DIR = Path("data/world/v2")
real_data = pytest.mark.requires_data("world_v2:w17_schedule.parquet")
TPD = 1_440


# ================================================================= E2: 期限つきの辞書の掃除
def test_e2_purge_expired_drops_only_expired_entries_and_reads_stay_the_same():
    """期限 ``<= tick`` の項だけを落とす。落とした後も、その tick から先の読み(拒否・相手別と話者別の不応期)は同じ。"""
    conv = ConversationManager(1, refusal_memory_ticks=30)
    conv.record_refusal(1, 2, 0)          # 期限 30
    conv.record_refusal(3, 4, 20)         # 期限 50
    conv.stamp_invite_refractory(5, 6, 0)  # 対の期限 60・話者の期限 30
    conv.stamp_invite_refractory(7, 8, 40)
    probe = [(1, 2), (3, 4), (5, 6), (7, 8), (6, 5)]

    def reads(t):
        return [(conv.refused_recently(a, b, t), conv.invite_blocked_by_refractory(a, b, t)) for a, b in probe]

    for t in (30, 31, 49, 50, 59, 60, 61, 79, 80, 100, 101, 200):
        before = {k: reads(k) for k in range(t, t + 120)}
        n0 = len(conv._refusal_until) + len(conv._pair_invite_until) + len(conv._speaker_invite_until)
        got = conv.purge_expired(t)
        n1 = len(conv._refusal_until) + len(conv._pair_invite_until) + len(conv._speaker_invite_until)
        assert n0 - n1 == got
        assert all(until > t for table in (conv._refusal_until, conv._pair_invite_until, conv._speaker_invite_until)
                   for until in table.values())
        assert {k: reads(k) for k in range(t, t + 120)} == before, t
    assert conv._refusal_until == {} and conv._pair_invite_until == {} and conv._speaker_invite_until == {}
    assert conv.n_expired_purged == 2 + 2 * 2
    assert PAIR_INVITE_REFRACTORY_TICKS == 60 and SPEAKER_INVITE_REFRACTORY_TICKS >= 1


@pytest.fixture(scope="module")
def purge_runs(tmp_path_factory):
    """合成世界 300 体・語彙 v3・2 日。掃除あり(既定)と、掃除を止めた(``purge_expired`` を何もしない)ラン。"""
    d = tmp_path_factory.mktemp("e2")
    kw = dict(n_agents=300, seed=3, n_cells=16, ticks=TPD, sim_days=2, checkpoint_every=360, budget=300.0,
              vocab_version="v3", memory="on", relations="on")
    seen: dict[str, list] = {"on": [], "off": []}
    real = SIO.full_state_hash

    def spy(label):
        def f(agents, world, pstate, pop, sched, owners, **k):
            conv = owners.get("conv")
            if conv is not None:
                seen[label].append((len(conv._refusal_until), len(conv._pair_invite_until),
                                    len(conv._speaker_invite_until)))
            return real(agents, world, pstate, pop, sched, owners, **k)
        return f

    mp = pytest.MonkeyPatch()
    try:
        mp.setattr(SIO, "full_state_hash", spy("on"))
        on = run_day(tape_path=d / "on", **kw)
        mp.setattr(SIO, "full_state_hash", spy("off"))
        mp.setattr(ConversationManager, "purge_expired", lambda self, tick: 0)
        off = run_day(tape_path=d / "off", **kw)
    finally:
        mp.undo()
    assert seen["on"] and seen["off"], "full_state_hash の差し替えが使われていない(1-0: state_io を通す)"
    return on, off, seen, d


def test_e2_purge_does_not_change_behavior(purge_runs):
    """掃除を止めたランと、呼数・行動の件数・起床の内訳・各呼の prompt_hash が同じ(期限切れは「無い」と同じ)。

    状態(O39)の中身は変わるので、behavior-hash(=既定の final)と full-hash は動く=記録の「動いた量」。
    """
    import pyarrow.parquet as pq

    on, off, seen, d = purge_runs
    assert on.llm_calls == off.llm_calls and on.action_usage == off.action_usage
    assert on.calls_by_condition == off.calls_by_condition
    ph = lambda t: pq.read_table(t / "calls.parquet").column("prompt_hash").to_pylist()  # noqa: E731
    assert ph(d / "on") == ph(d / "off")
    assert int(on.conversation_counters.get("sessions_opened", 0)) > 0
    assert on.final_hash != off.final_hash  # 状態の中身が変わる(O39)=定義どおり動く


def test_e2_dicts_stay_bounded_over_days(purge_runs):
    """掃除ありの辞書の大きさは日をまたいでも増え続けない(止めたランは日数に比例して増える)。"""
    on, off, seen, _d = purge_runs
    tot = lambda rows: [sum(r) for r in rows]  # noqa: E731
    s_on, s_off = tot(seen["on"]), tot(seen["off"])
    # 控えは checkpoint ごと(2 日 × 4 回)と日の締めの後(1 日 1 回)。実測(seed 3): 掃除あり 0〜14・止めたラン 3 → 464
    assert len(s_on) == len(s_off) >= 8
    assert s_off[-1] > s_off[3] > 0          # 止めたランは 1 日目の終わりより 2 日目の終わりが大きい(日数に比例)
    assert max(s_on) < min(s_off[3:])        # 掃除ありは期限の窓の中の項だけ=止めたランの 1 日目の終わりより小さい
    assert max(s_on[len(s_on) // 2:]) <= 2 * max(s_on[: len(s_on) // 2]) + 10  # 2 日目も 1 日目と同じ桁


# ================================================================= E2: O64 の分類(no のまま)の確かめ
@real_data
def test_e2_o64_signage_exposures_are_empty_at_every_checkpoint():
    """O64 の ``renderer.signage_exposures`` は tick の中だけの口=checkpoint の時点では常に空(no のままでよい根拠)。"""
    from shibuya import cli
    from shibuya.engine import state_ledger as SL

    row = SL.row("O64")
    assert (row.behavior, row.restore) == (SL.NO, SL.DISCARDABLE) and "renderer.signage_exposures" in row.items
    sizes: list[int] = []
    real = SIO.full_state_hash

    def spy(agents, world, pstate, pop, sched, owners, **k):
        r = owners.get("renderer")
        sizes.append(-1 if r is None else len(getattr(r, "signage_exposures", [])))
        return real(agents, world, pstate, pop, sched, owners, **k)

    mp = pytest.MonkeyPatch()
    try:
        mp.setattr(SIO, "full_state_hash", spy)
        res = cli.run(n_agents=500, seed=1, world_dir=str(WORLD_DIR), vocab_version="v3", familiarity="on")
    finally:
        mp.undo()
    c = res.run_manifest_fields()["familiarity_summary"]["counts"]
    assert c["exposures_signage_render"] > 0  # 露出は実際に集まっていた
    assert sizes and all(n == 0 for n in sizes), sizes


# ================================================================= E4: 既定の乱数を counter に・K19 の鍵の並べ方・U2
def test_e4_default_rng_scheme_is_counter_and_stateful_is_the_old_switch():
    """〔改訂(第330・RET)〕方式は counter だけ。``stateful``・``--rng-scheme``・``k19_counters`` の方式の引数を消した
    (前: 既定 counter・stateful は旧値の再現の切替口・``k19_counters("stateful", 7) == (7,)``)。"""
    import argparse

    from shibuya.core import rng as R
    from shibuya.engine.run import add_calendar_args, calendar_kwargs_from_args

    assert R.RNG_SCHEME == "counter" and not hasattr(R, "RNG_SCHEMES") and not hasattr(R, "DEFAULT_RNG_SCHEME")
    ap = argparse.ArgumentParser()
    add_calendar_args(ap)
    assert "rng_scheme" not in calendar_kwargs_from_args(ap.parse_args([]))
    with pytest.raises(SystemExit):
        ap.parse_args(["--rng-scheme", "stateful"])
    res = run_day(n_agents=10, seed=1, n_cells=9, ticks=30, checkpoint_every=30)
    assert res.run_manifest_fields()["rng_scheme"] == "counter"
    assert R.k19_counters(7) == (0, 7) and R.k19_counters(1, 2, 3) == (0, 1, 2, 3) and R.k19_counters() == (0,)
    with pytest.raises(ValueError):
        R.k19_counters(1, 2, 3, 4)


@pytest.mark.parametrize("domain", ["world.delivery_inbound", "world.road_works", "w16.sample.stratum", "body.weight",
                                    "perception.p_notice"])
def test_e4_u2_next_key_is_no_longer_a_shifted_copy(domain):
    """U2(既知の答え): 旧の並び(鍵を 0 語目に置く)では「鍵 d+1 の流れ」が「鍵 d の流れを 1 ブロック(4 語)ずらした写し」に
    なる。counter では 0 語目を空けたので、鍵 d の流れを何ブロック引いても鍵 d+1 の流れと同じ語は出ない。
    〔改訂(第330・RET)〕旧の並びは ``k19_counters("stateful", d)`` を消したので ``stream(seed, 用途名, d)`` で直に作る。"""
    from shibuya.core.rng import k19_counters, stream

    for d in (0, 3):
        old_d = stream(1, domain, d).integers(0, 2**63, 40, dtype=np.int64)
        old_n = stream(1, domain, d + 1).integers(0, 2**63, 36, dtype=np.int64)
        assert np.array_equal(old_d[4:], old_n)  # 旧: 次の鍵の流れは写し
        new_d = stream(1, domain, *k19_counters(d)).integers(0, 2**63, 4000, dtype=np.int64)
        new_n = stream(1, domain, *k19_counters(d + 1)).integers(0, 2**63, 40, dtype=np.int64)
        assert not set(new_n.tolist()) & set(new_d.tolist())


def test_e4_u2_two_day_run_has_independent_day_streams():
    """U2: 2 日のラン(合成世界・counter)で、日の鍵の流れ(配送・工事)はどれも重ならない=日ごとの差を主張に使える。
    〔改訂(第330・RET)〕前は stateful(旧値の再現)では 1 日目の配送の流れが 0 日目と重なることも見た(stateful を消した)。"""
    from shibuya.engine import rng_audit as RA

    kw = dict(n_agents=120, seed=2, n_cells=16, ticks=TPD, sim_days=2, checkpoint_every=360, budget=120.0)
    with RA.StreamRecorder() as rec:
        run_day(**kw)
    st = rec.analyze()
    assert RA.check_overlaps(st) == [] and {d for d, s in st.items() if s.actual_overlaps} == set()
    assert st["world.delivery_inbound"].streams >= 2 and st["world.delivery_inbound"].keyed is False


def test_e4_recorder_groups_by_seed_u8():
    """U8: 束ねる鍵に master seed を入れた=seed の違う同じ用途名・同じカウンタの流れを重なりと数えない。"""
    from shibuya.core.rng import stream
    from shibuya.engine import rng_audit as RA

    with RA.StreamRecorder() as rec:
        for seed in (1, 2):
            for k in (0, 1):
                stream(seed, "test.e4.u8", k).random(9)  # 1 語目に値・3 ブロック=同じ seed の中では重なる
    st = rec.analyze()["test.e4.u8"]
    assert st.streams == 4 and st.actual_overlaps == 2  # seed ごとに 1 つずつ(seed をまたいだ 2 つは数えない)


# ================================================================= E5: テープ版 4(A8・K1)
def test_e5_schema_is_version_4_and_appends_seven_columns():
    from shibuya.engine import tape as TP

    assert TP.TAPE_SCHEMA_VERSION == "shibuya.tape/4"
    names = TP.CALLS_SCHEMA.names
    v3 = list(TP.CALLS_SCHEMA_V1_NAMES) + list(TP.CALLS_SCHEMA_V2_DEFAULTS) + list(TP.CALLS_SCHEMA_V3_DEFAULTS)
    assert names[: len(v3)] == v3  # 版 3 までの 14 列は順序ごと不変
    assert names[len(v3):] == list(TP.CALLS_SCHEMA_V4_DEFAULTS) == [
        "recalled_first_tick", "recalled_kind", "recalled_object", "recalled_source", "acquaintance_ids",
        "b5_text", "b6_block_id"]


def test_e5_a_version_3_tape_reads_as_day_0_and_replays(tmp_path):
    """旧版(版 3)のテープは「日=0」として読める: 新しい 7 列は空で埋まり、鍵(tick=日の中の tick=T)で再生できる。"""
    import pyarrow as pa
    import pyarrow.parquet as pq

    from shibuya.engine import tape as TP

    kw = dict(n_agents=60, seed=1, n_cells=9, ticks=360, checkpoint_every=60, budget=60.0, vocab_version="v3")
    rec = run_day(tape_path=tmp_path / "rec", **kw)
    t = pq.read_table(tmp_path / "rec" / TP.CALLS_FILENAME)
    v3_names = list(TP.CALLS_SCHEMA.names)[: -len(TP.CALLS_SCHEMA_V4_DEFAULTS)]
    old = pa.Table.from_arrays([t.column(n) for n in v3_names], names=v3_names).replace_schema_metadata(
        {TP.TAPE_SCHEMA_METADATA_KEY: b"shibuya.tape/3"})
    d3 = tmp_path / "v3"
    d3.mkdir()
    pq.write_table(old, d3 / TP.CALLS_FILENAME)
    (d3 / TP.BLOCKS_FILENAME).write_bytes((tmp_path / "rec" / TP.BLOCKS_FILENAME).read_bytes())
    (d3 / TP.RUN_META_FILENAME).write_bytes((tmp_path / "rec" / TP.RUN_META_FILENAME).read_bytes())
    tape = TP.Tape(d3)
    assert tape.schema_version == "shibuya.tape/3"
    rows = list(tape.rows())
    assert rows and all(r.b5_text == "" and r.b6_block_id == "" and r.acquaintance_ids == () for r in rows)
    assert all(0 <= r.tick < 360 for r in rows)  # 日=0: tick は日の中の tick(=T)
    from tests.engine.test_tape_wiring import BoomLLM

    rep = run_day(mode="replay", replay=d3, llm=BoomLLM(), **kw)
    assert rep.final_hash == rec.final_hash and rep.tape_miss_count == 0


def test_e5_key_has_the_day_through_T(tmp_path):
    """鍵に日(A8 の 1): 2 日のランのテープの tick は通しの T(1 日目は 1,440 以上)・鍵は日をまたいで衝突しない。"""
    from shibuya.engine import tape as TP

    run_day(n_agents=40, seed=1, n_cells=9, ticks=TPD, sim_days=2, checkpoint_every=360, budget=40.0,
            vocab_version="v3", tape_path=tmp_path / "t")
    rows = list(TP.Tape(tmp_path / "t").rows())
    ticks = [r.tick for r in rows]
    assert min(ticks) < TPD <= max(ticks) < 2 * TPD
    keys = [r.key for r in rows]
    assert len(set(keys)) == len(keys)


@pytest.fixture(scope="module")
def v4_tape(tmp_path_factory):
    """世界資産 300 体・1 日・語彙 v3・記憶 on・関係 on(初期の関係辺がある=知人の印が出る)。"""
    D.skip_unless("world_v2:w17_schedule.parquet")
    from shibuya import cli
    from shibuya.engine import tape as TP

    d = tmp_path_factory.mktemp("e5")
    res = cli.run(n_agents=300, seed=1, world_dir=str(WORLD_DIR), vocab_version="v3", memory="on", relations="on",
                  tape_path=d / "t")
    return res, TP.Tape(d / "t"), d


def test_e5_b5_b6_texts_rebuild_the_prompt_hash(v4_tape):
    """B5 は列に直接・B6 は intern(K1): 共有ブロック 6 本+B5+B6 の本文から ``prompt_hash`` を作り直せる(再描画の検算)。"""
    from shibuya.core.hashing import sha256_cbor

    _res, tape, _d = v4_tape
    rows = [r for r in tape.rows() if not r.deferred]
    assert rows
    n_checked = 0
    for r in rows:
        assert r.b5_text and r.b6_block_id
        shared = [tape.block_text(b) for b in r.block_ids]
        assert len(shared) == 6
        body = "\n".join(shared + [r.b5_text, tape.block_text(r.b6_block_id)])
        assert sha256_cbor(body) == r.prompt_hash  # テープの鍵=本文の sha256_cbor(LLMRequest.prompt_hash)
        n_checked += 1
    assert n_checked == len(rows)


def test_e5_recalled_memory_identity_and_acquaintances(v4_tape):
    """引いた記憶の同定(A8 の 2)と「(知人)」の相手の id・出どころの予約(A8 の 3)。"""
    res, tape, _d = v4_tape
    rows = list(tape.rows())
    with_mem = [r for r in rows if r.recalled_rows]
    assert with_mem, "記憶 on の 1 日で想起のある呼があるはず"
    for r in with_mem:
        n = len(r.recalled_rows)
        assert len(r.recalled_first_tick) == len(r.recalled_kind) == len(r.recalled_object) == n
        assert all(-10**9 < t <= r.tick for t in r.recalled_first_tick)
        assert all(k > 0 for k in r.recalled_kind)
    assert all(r.recalled_source == () for r in rows)  # 予約(記憶の作り直しまでは空)
    with_acq = [r for r in rows if r.acquaintance_ids]
    assert with_acq, "関係 on のランでは知人の印が出るはず"
    for r in with_acq:
        for a in r.acquaintance_ids:
            assert f"P-{a}(知人)" in r.b5_text
    for r in rows:
        if "(知人)" not in r.b5_text:
            assert r.acquaintance_ids == ()


# ================================================================= E4 の検収の直し(L1・L2・L3)
def test_e4_l1_tape_meta_carries_the_rng_layout_and_old_counter_tapes_stop(tmp_path):
    """L1: テープの脇の meta に鍵の配置の印(``rng_layout``)。10c〜10f の counter で録ったテープ(印が無い)は再生で
    明示的に止まる。〔改訂(第330・RET)〕前は「stateful のテープは印が無くても回る(meta の無い実テープと同じ扱い)」も
    見た=stateful を消したので、印が無いテープ・stateful のテープ・meta の無いテープはどれも止まる。"""
    import json

    from shibuya.engine.run import RNG_LAYOUT
    from shibuya.engine.tape import RUN_META_FILENAME, read_run_meta
    from tests.engine.test_tape_wiring import BoomLLM

    kw = dict(n_agents=40, seed=3, n_cells=9, ticks=120, checkpoint_every=60, budget=40.0,
              salient_rate_per_10k=30000.0)
    rec = run_day(tape_path=tmp_path / "c", **kw)
    meta = read_run_meta(tmp_path / "c")
    assert meta["rng_scheme"] == "counter" and meta["rng_layout"] == RNG_LAYOUT == "10e"
    assert run_day(mode="replay", replay=tmp_path / "c", llm=BoomLLM(), **kw).final_hash == rec.final_hash
    p = tmp_path / "c" / RUN_META_FILENAME
    base = json.loads(p.read_text(encoding="utf-8"))
    for drop in ("rng_layout", "rng_scheme"):
        d = dict(base)
        d.pop(drop)
        p.write_text(json.dumps(d) + "\n", encoding="utf-8")
        with pytest.raises(ValueError, match="10e より前"):
            run_day(mode="replay", replay=tmp_path / "c", llm=BoomLLM(), **kw)
    p.unlink()  # meta の無いテープ(10a より前の録画)
    with pytest.raises(ValueError, match="10e より前"):
        run_day(mode="replay", replay=tmp_path / "c", llm=BoomLLM(), **kw)


@pytest.mark.requires_data("world_v2:w16_population.parquet")
def test_e4_l2_load_population_and_three_argument_samplers_follow_the_engine(monkeypatch):
    """L2: ``load_population(n=…)`` は engine と同じ鍵の並べ方(counter)。3 引数の抽出の差し替え(凍結した測りの道具)も
    engine から呼べる。〔改訂(第330・RET)〕前は ``rng_scheme`` の 2 通り(counter・stateful)で見た(stateful を消した)。"""
    import numpy as np

    import shibuya.engine.run as RUN
    from shibuya.agents import population as POP

    full = POP.load_population(WORLD_DIR, n=None, seed=1)
    a = POP.load_population(WORLD_DIR, n=500, seed=1)
    b = POP.sample_population(full, 500, 1)
    assert np.array_equal(a.source_agent_id, b.source_agent_id)
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "rel8b_measure", Path("docs/bench/analysis/c10-relations-2026-09-28/rel8b_measure.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    monkeypatch.setattr(RUN, "sample_population", mod.stratified_sample)
    pop = RUN._resolve_population(None, WORLD_DIR, 300, 1, 520)  # TypeError にならない(世界資産は 520 セル)
    assert pop is not None and pop.n == 300


def test_e4_l3_checkpoints_payload_is_version_2():
    """L3: CLI の checkpoints の JSON は版 2(``combined`` は既定で behavior-hash)。"""
    from shibuya import cli

    res = run_day(n_agents=10, seed=1, n_cells=9, ticks=30, checkpoint_every=30)
    doc = cli.checkpoints_payload(res)
    assert doc["schema"] == "shibuya.cli/checkpoints/2"
    assert doc["checkpoints"][-1]["combined"] == doc["checkpoints"][-1]["behavior_hash"] == res.final_hash


# ================================================================= E5 の検収の直し(T1・T3)
def test_e5_t1_fleet_rows_carry_b5_b6_and_rebuild_the_prompt_hash(tmp_path):
    """T1: 艦隊の経路(``FleetBridge``)の応答の行と繰り延べの行にも B5・B6 が入り、``prompt_hash`` を本文から作り直せる。"""
    from shibuya.core.hashing import sha256_cbor
    from shibuya.engine import tape as TP
    from shibuya.world.state import World
    from tests.engine.test_tape_deferred import make_client
    from tests.llm.test_fleet import FakeVLLM

    servers = [FakeVLLM(), FakeVLLM()]
    try:
        for srv in servers:
            srv.total_delay_s = 0.02
        client = make_client(servers, per_replica_in_flight=4, queue_capacity=8)
        run_day(n_agents=120, seed=1, world=World.synthetic(n_cells=16, seed=1), ticks=40, processes=False,
                population=False, world_dir=None, sleep_suppression=False, vocab_version="v3", checkpoint_every=10,
                budget=30.0, fleet=client, tape_path=tmp_path / "t", fleet_wait_s=2.0)
    finally:
        for srv in servers:
            srv.close()
    tape = TP.Tape(tmp_path / "t")
    rows = list(tape.rows())
    answered = [r for r in rows if not r.deferred]
    deferred = [r for r in rows if r.deferred]
    assert answered and deferred, "応答の行と繰り延べの行が混ざる設定のはず"
    for r in rows:
        assert r.b5_text and r.b6_block_id, r.call_id
        body = "\n".join([tape.block_text(b) for b in r.block_ids] + [r.b5_text, tape.block_text(r.b6_block_id)])
        assert sha256_cbor(body) == r.prompt_hash, r.call_id


def test_e5_t3_recalled_identity_matches_the_memory_table(tmp_path, monkeypatch):
    """T3: 引いた記憶の同定 3 列を、想起した時点の記憶の表(``mem_tick``・``mem_kind``・``mem_object``・店の行は
    ``sm_first``・``sm_poi``)と突き合わせる。並びのずれ・種類と対象の取り違えで落ちる。"""
    from shibuya.engine import tape as TP
    from shibuya.engine.memory import STORE_ITEM_KIND, MemoryLayer

    seen: dict[tuple[int, int], list[tuple[int, tuple[int, int, int]]]] = {}
    real = MemoryLayer.recall

    def spy(self, agents, agent_id, tick, condition, inviter=-1):
        items = real(self, agents, agent_id, tick, condition, inviter)
        f = agents.registry.field
        out = []
        for it in items:
            if it.kind == STORE_ITEM_KIND:  # 店の行(row = N + 店の行)
                j = int(it.row) - int(self.n_rows)
                ident = (int(f("sm_first")[agent_id][j]), int(STORE_ITEM_KIND), int(f("sm_poi")[agent_id][j]))
            else:
                j = int(it.row)
                ident = (int(f("mem_tick")[agent_id][j]), int(f("mem_kind")[agent_id][j]),
                         int(f("mem_object")[agent_id][j]))
            out.append((int(it.row), ident))
        seen.setdefault((int(agent_id), int(tick)), []).append(out)
        return items

    monkeypatch.setattr(MemoryLayer, "recall", spy)
    run_day(n_agents=100, seed=2, ticks=TPD, vocab_version="v3", memory="on", store_memory="on",
            tape_path=tmp_path / "t")
    rows = [r for r in TP.Tape(tmp_path / "t").rows() if r.recalled_rows]
    assert len(rows) > 100
    n_store = 0
    for r in rows:
        got = list(zip(r.recalled_rows, zip(r.recalled_first_tick, r.recalled_kind, r.recalled_object)))
        cands = seen[(int(r.agent_id), int(r.tick))]
        assert any(c[: len(got)] == got for c in cands), (r.call_id, got, cands)
        n_store += sum(1 for k in r.recalled_kind if k == STORE_ITEM_KIND)
    assert n_store > 0, "店の行も想起されるはず(記憶+店の記憶)"
