"""10c: 状態を持つ乱数 2 本(顕著行為の発生・出動の遅れ)をカウンタ型にする(10c の切替口 ``rng_scheme``)。

〔改訂(第330・RET)〕10e より前の ``stateful`` と切替口 ``rng_scheme`` は版上げ 1 回目の後に消した。stateful と比べていた
試験は counter だけの形に直し、stateful の旧値・旧テープの再生の試験は消した(第330 ACT の commit で通っていたことを
10e の記録 §RET に書いた)。

アジェンダ ``docs/design/v2-d102-foundation-implementation-agenda.md`` §3 と A5 (a′)(鍵は (T, 場所, k)・
事象の通し番号は使わない)。既定は ``stateful`` のまま(byte-check は記録 10c/README.md)。

既知の答え:
- (i) counter の腕を 2 回回して final・件数・列が一致。
- (ii) 同じ T・同じセルの複数の出動が違う遅れを引く(``test_civic.py`` の 400 件の形を counter でも)。
- (iii) 率を上げた合成世界で、tick ごとの件数が既知の答え(ポアソン・期待値 = 率 × 体数)に合う(z 検定・主の判定)。
  stateful と counter の 5 seed の平均と分散の比較は記録 10c/README.md に残す副の判定。
- (v) 2 日のランで 2 日目の鍵が 1 日目と違う(T が鍵に入っている)。
- 状態を持たない: 前の tick を回したかどうかで counter の引きが変わらない。台帳の軸 2 で、counter では
  再開で保存が要る Generator が 0 本(stateful は 2 本)。
"""

from __future__ import annotations


import numpy as np
import pytest

import shibuya.engine.processes.civic as CIV
import shibuya.engine.processes.salient as SAL
import shibuya.engine.run as RUN
from shibuya.core.rng import RNG_SCHEME, run_tick_key
from shibuya.core.rng import stream as core_stream
from shibuya.engine import state_hashes as SH
from shibuya.engine import state_ledger as SL
from shibuya.engine.processes.civic import DISPATCH_MEDIAN_MIN, PublicServiceDispatchProcess
from shibuya.engine.processes.salient import COLLAPSE_PER_10K_PER_DAY, SalientProcess
from shibuya.engine.run import run_day

from .conftest import make_agents, make_world

TPD = 1_440
#: (iii) の合成世界: 既定の率 3/万/日の ×1000(1 日で体数の 30% が倒れる=件数の分布を比べるための率)。
RATE_X1000 = COLLAPSE_PER_10K_PER_DAY * 1_000.0
SEEDS = (1, 2, 3, 4, 5)
#: (iii) の主の判定の線: |z| ≤ 3(両側 p ≈ 0.0027。1 方式につき 2 つの z(件数の合計・分散の指数)× 2 方式 = 4 つで、
#: 誤報は合わせて約 1%。率を 10% 下げると合計の z は約 −3.9 になる=記録 10c/README.md の「検収後の直し」)。
Z_MAX = 3.0


# ================================================================= 0. 切替口
def test_scheme_values_and_default_is_counter():
    # 〔改訂(第330・RET)〕方式は counter だけ(stateful と切替口を消した)。過程は rng_scheme を受け取らない
    assert RNG_SCHEME == "counter"
    import shibuya.core.rng as RNG

    assert not hasattr(RNG, "RNG_SCHEMES") and not hasattr(RNG, "check_rng_scheme")
    with pytest.raises(TypeError):
        PublicServiceDispatchProcess(make_world(4), rng_scheme="counter")


def test_run_tick_key_is_day_key_times_ticks_per_day_plus_T():
    assert run_tick_key(0, 17, 60) == 17
    assert run_tick_key(3, 17, 60) == 3 * TPD + 17
    # day_key(日) = day_key0 + 日 なので、2 日目の頭は「日の鍵 1 の 0 tick」と同じ
    assert run_tick_key(0, TPD, 60) == run_tick_key(1, 0, 60)
    assert run_tick_key(0, 10, 30) == 10  # tick 30 秒でも T はそのまま


def test_run_tick_key_multiplies_by_the_ticks_per_day_not_1440():
    """検収 T1: tick 30 秒なら 1 日の tick 数は 2,880(定数 1,440 にすると落ちる)。"""
    assert run_tick_key(1, 0, 30) == 2_880 == run_tick_key(0, 2_880, 30)
    assert run_tick_key(2, 7, 30) == 2 * 2_880 + 7
    assert run_tick_key(1, 0, 120) == 720


def test_counter_streams_have_their_own_names_and_word0_is_zero(monkeypatch):
    """検収 M3・M9: counter の用途名は stateful と別・カウンタの 1 語目は 0(単体で守る)。"""
    assert SAL.SALIENT_COUNTER_DOMAIN != "world.salient"
    assert CIV.DISPATCH_COUNTER_DOMAIN != "world.public_service_dispatch"
    seen: list[tuple[str, tuple[int, ...]]] = []

    def spy(real):
        def f(seed, domain, *ctr):
            seen.append((domain, tuple(int(c) for c in ctr)))
            return real(seed, domain, *ctr)
        return f

    monkeypatch.setattr(SAL, "stream", spy(SAL.stream))
    monkeypatch.setattr(CIV, "stream", spy(CIV.stream))
    world = make_world(9)
    agents, _ = make_agents(world, 200)
    d = PublicServiceDispatchProcess(world, master_seed=1)
    sp = SalientProcess(world, agents, master_seed=1, dispatch=d, rate_per_10k_per_day=RATE_X1000 * 20)
    for t in range(20):
        sp.step(t)
    ctr = [c for dom, c in seen if dom in (SAL.SALIENT_COUNTER_DOMAIN, CIV.DISPATCH_COUNTER_DOMAIN)]
    assert d.n_dispatched > 0 and len(ctr) == 20 + d.n_dispatched
    assert all(c[0] == 0 for c in ctr)


def test_day_key0_enters_the_key():
    """検収 T2: ``--day`` が違うランは counter の乱数が違う(鍵から ``day_key(0)`` を落とすと落ちる)。"""
    world = make_world(16)

    def delay(day_index: int, T: int) -> list[int]:
        d = PublicServiceDispatchProcess(world, master_seed=5, day_index=day_index)
        return [d.request(T, 3, (0.0, 0.0)) - T for _ in range(6)]

    assert delay(0, 100) != delay(3, 100)
    assert delay(1, 100) == delay(0, 100 + TPD)  # 日の鍵 1 の T=100 = 日の鍵 0 の T=1,540


def test_run_day_passes_day_key0_to_the_counter_key(monkeypatch):
    """検収 T2(ランの経路): 顕著行為の鍵の時刻は ``day_key(0)`` × 1,440 + T。

    〔改訂(第330・RET)〕暦は real だけ(日の鍵=日番号・0 日目は 0)。前は ``day_index=3``(day_index の暦)で
    「鍵の時刻 = 3 × 1,440 + T」を見ていた(day_index の暦は消した)。``day_index=14``(2026-07-27・月曜)のランでも
    日の鍵は 0=鍵の時刻は T そのもの(day_index は開始日をずらすだけ)。"""
    seen: list[tuple[int, ...]] = []
    real = SAL.stream

    def spy(seed, domain, *ctr):
        if domain == SAL.SALIENT_COUNTER_DOMAIN:
            seen.append(tuple(int(c) for c in ctr))
        return real(seed, domain, *ctr)

    monkeypatch.setattr(SAL, "stream", spy)
    res = run_day(n_agents=20, seed=1, n_cells=9, ticks=5, day_index=14)
    assert res.run_manifest_fields()["start_sim_datetime"] == "2026-07-27T00:00:00"
    assert res.runner.calendar.day_key(0) == 0
    assert res.runner.salient.day_index == 0 and res.runner.dispatch.day_index == 0
    assert seen == [(0, t) for t in range(5)]


def test_counter_keeps_no_generator():
    """〔改訂(第330・RET)〕前は「stateful は Generator を持ち counter は持たない」。stateful を消したので、どの過程も
    Generator を持たない(``rng`` は常に None=状態台帳 O46・O47 の道筋は「無い」の印のまま)。"""
    world = make_world(9)
    agents, _ = make_agents(world, 20)
    d = PublicServiceDispatchProcess(world, master_seed=1)
    s = SalientProcess(world, agents, master_seed=1, dispatch=d)
    assert d.rng is None and s.rng is None
    assert not hasattr(d, "relay_day") and not hasattr(s, "relay_day")


def test_run_day_has_no_scheme_argument_and_writes_the_manifest():
    """〔改訂(第330・RET)〕切替口 ``rng_scheme`` を消した(渡すと TypeError)。manifest の ``rng_scheme`` は counter の記録。"""
    with pytest.raises(TypeError):
        run_day(n_agents=10, seed=1, n_cells=9, ticks=10, rng_scheme="counter")
    res = run_day(n_agents=10, seed=1, n_cells=9, ticks=10)
    assert res.run_manifest_fields()["rng_scheme"] == "counter"
    res = run_day(n_agents=10, seed=1, n_cells=9, ticks=10, processes=False)
    assert res.run_manifest_fields()["rng_scheme"] == "counter"


def test_cli_flag_is_shared_by_engine_run_and_cli():
    """〔改訂(第330・RET)〕``--rng-scheme`` を消した(渡すと argparse が止める)。暦の引数の口は engine.run と cli で同じ。"""
    import argparse

    ap = argparse.ArgumentParser()
    RUN.add_calendar_args(ap)
    assert "rng_scheme" not in RUN.calendar_kwargs_from_args(ap.parse_args([]))
    with pytest.raises(SystemExit):
        ap.parse_args(["--rng-scheme", "counter"])
    import inspect

    from shibuya import cli

    src = inspect.getsource(cli.main)
    assert "add_calendar_args(ap)" in src and "calendar_kwargs_from_args(args)" in src


# ================================================================= (ii) 同じ T・同じセルの出動
def test_counter_dispatches_in_one_cell_and_tick_draw_different_delays():
    """``test_civic.py`` の 400 件(同じ tick・16 セル × 25 件)を counter で。"""
    world = make_world(16)
    d = PublicServiceDispatchProcess(world, master_seed=3)
    arrive: dict[int, list[int]] = {}
    for k in range(400):
        arrive.setdefault(k % 16, []).append(d.request(0, k % 16, (0.0, 0.0)))
    mean = d.delay_minutes_total / d.n_dispatched
    assert 1.0 <= mean <= 4.0 * DISPATCH_MEDIAN_MIN and d.n_dispatched == 400
    for cell, got in arrive.items():
        assert len(set(got)) > 1, f"セル {cell} の 25 件が同じ遅れ"
    # 生の引き(丸める前)は 400 件すべて違う
    raws = {
        float(core_stream(3, CIV.DISPATCH_COUNTER_DOMAIN, 0, 0, c, k).lognormal(np.log(8.0), 0.5))
        for c in range(16) for k in range(25)
    }
    assert len(raws) == 400


def test_counter_dispatch_delay_depends_only_on_T_cell_k():
    """状態を持たない: 前に何件出動したかで (T, セル, k) の引きが変わらない(通し番号を使っていない)。

    〔改訂(第330・RET)〕前は後半で「stateful は前の出動で列が進む」を比べた(stateful を消した)。"""
    world = make_world(16)
    a = PublicServiceDispatchProcess(world, master_seed=7)
    b = PublicServiceDispatchProcess(world, master_seed=7)
    for t in range(1, 5):  # b だけ前の tick で 12 件出動
        for c in (3, 5, 3):
            b.request(t, c, (0.0, 0.0))
    got_a = [a.request(5, 3, (0.0, 0.0)) for _ in range(3)] + [a.request(5, 9, (0.0, 0.0))]
    got_b = [b.request(5, 3, (0.0, 0.0)) for _ in range(3)] + [b.request(5, 9, (0.0, 0.0))]
    assert got_a == got_b


def test_counter_k_restarts_for_each_tick_and_cell():
    world = make_world(16)
    d = PublicServiceDispatchProcess(world, master_seed=2)
    e = PublicServiceDispatchProcess(world, master_seed=2)
    d.request(4, 1, (0.0, 0.0))
    d.request(4, 2, (0.0, 0.0))
    x = d.request(4, 1, (0.0, 0.0))  # (T=4, セル 1, k=1)
    e.request(4, 1, (0.0, 0.0))
    assert e.request(4, 1, (0.0, 0.0)) == x
    assert d.request(6, 1, (0.0, 0.0)) == e.request(6, 1, (0.0, 0.0))  # 新しい T では k=0 から


# ================================================================= 状態を持たない(顕著行為)
def _events(sp: SalientProcess, tick: int) -> list[tuple[str, int]]:
    sp.step(tick)
    return [(ev.kind, int(ev.cell)) for ev in sp.events]


def test_counter_collapse_at_T_does_not_depend_on_earlier_ticks():
    """〔改訂(第330・RET)〕前は後半で「stateful は前の tick を回したかで変わる」を比べた(stateful を消した)。"""
    world = make_world(25)
    agents, _ = make_agents(world, 400)
    fresh = SalientProcess(world, agents, master_seed=4, rate_per_10k_per_day=RATE_X1000 * 10)
    walked = SalientProcess(world, agents, master_seed=4, rate_per_10k_per_day=RATE_X1000 * 10)
    for t in range(30):
        walked.step(t)
    assert walked.n_collapse > 0
    assert _events(fresh, 30) == _events(walked, 30)


def test_counter_calls_the_dispatch_in_ascending_agent_id():
    world = make_world(4)
    agents, _ = make_agents(world, 300)
    calls: list[tuple[int, int, float]] = []

    class Spy(PublicServiceDispatchProcess):
        def request(self, tick, cell, xy):
            calls.append((int(tick), int(cell), float(xy[0])))
            return super().request(tick, cell, xy)

    # 体の id を x 座標に書いておく(呼ばれた順の体を出動の座標から引き戻すため・試験だけ)
    xy = agents.registry.xy
    was = xy.flags.writeable
    xy.flags.writeable = True
    xy[:, 0] = np.arange(agents.n, dtype=xy.dtype)
    xy.flags.writeable = was
    d = Spy(world, master_seed=1)
    sp = SalientProcess(world, agents, master_seed=1, dispatch=d, rate_per_10k_per_day=RATE_X1000 * 20)
    multi = 0
    for t in range(60):
        before = len(calls)
        sp.step(t)
        got = calls[before:]
        if len(got) > 1:
            multi += 1
            ids = [int(round(x)) for _, _, x in got]
            assert ids == sorted(ids) and len(set(ids)) == len(ids)
    assert multi > 0


# ================================================================= (iii) 件数が既知の答えに合う(主の判定)
N_X1000 = 1_000


def _per_tick_counts(seed: int) -> np.ndarray:
    """1 日の tick ごとの「倒れる」の件数(過程だけ・25 セル・1,000 体・体は動かない)。"""
    world = make_world(25, seed=seed)
    agents, _ = make_agents(world, N_X1000, seed=seed)
    d = PublicServiceDispatchProcess(world, master_seed=seed)
    sp = SalientProcess(world, agents, master_seed=seed, dispatch=d, rate_per_10k_per_day=RATE_X1000)
    out = np.zeros(TPD, dtype=np.int64)
    for t in range(TPD):
        before = sp.n_collapse
        sp.step(t)
        out[t] = sp.n_collapse - before
    assert d.n_dispatched == sp.n_collapse  # 倒れる事象への出動率 100%
    return out


def poisson_z(counts: np.ndarray, lam: float) -> tuple[float, float]:
    """tick ごとの件数(ポアソン・期待値 ``lam``)→ (合計の z, 分散の指数の z)。

    合計の z = (Σx − N λ) / √(N λ)。分散の指数 D = Σ(x − x̄)² / x̄ はポアソンなら自由度 N−1 の χ² に従うので、
    z = (D − (N−1)) / √(2(N−1))。
    """
    x = np.asarray(counts, dtype=np.float64).ravel()
    n = x.size
    z_sum = (x.sum() - n * lam) / np.sqrt(n * lam)
    m = x.mean()
    disp = float(((x - m) ** 2).sum() / m) if m > 0 else float("nan")
    z_disp = (disp - (n - 1)) / np.sqrt(2.0 * (n - 1))
    return float(z_sum), float(z_disp)


def test_per_tick_counts_match_the_known_poisson_rate():
    """〔改訂(第330・RET)〕前は stateful と counter の両方で見た(stateful を消した=counter だけ)。"""
    lam = RATE_X1000 * (N_X1000 / 10_000.0) / TPD  # 期待値 = 率 × 体数(1 tick あたり 0.2083 件)
    x = np.concatenate([_per_tick_counts(seed) for seed in SEEDS])  # 5 seed × 1,440 tick
    z_sum, z_disp = poisson_z(x, lam)
    assert abs(z_sum) <= Z_MAX and abs(z_disp) <= Z_MAX, (z_sum, z_disp, int(x.sum()))


def test_poisson_z_catches_a_ten_percent_lower_rate():
    """線の検出力の既知の答え: 期待値 1,500 件に対して 10% 少ない率なら合計の z < −3。"""
    lam = RATE_X1000 * (N_X1000 / 10_000.0) / TPD
    g = np.random.default_rng(0)
    assert poisson_z(g.poisson(lam * 0.9, size=len(SEEDS) * TPD), lam)[0] < -Z_MAX
    assert abs(poisson_z(g.poisson(lam, size=len(SEEDS) * TPD), lam)[0]) <= Z_MAX


# ================================================================= (i)・(v) ラン
KW = dict(n_agents=60, n_cells=16, checkpoint_every=360, budget=60.0)


def test_counter_run_twice_is_identical():
    """〔改訂(第330・RET)〕前は最後に「stateful に変えると引きが変わる」を見た(stateful を消した)。"""
    a = run_day(seed=3, ticks=TPD, salient_rate_per_10k=RATE_X1000, **KW)
    b = run_day(seed=3, ticks=TPD, salient_rate_per_10k=RATE_X1000, **KW)
    assert a.final_hash == b.final_hash and a.llm_calls == b.llm_calls
    assert [c.combined for c in a.checkpoints] == [c.combined for c in b.checkpoints]
    assert (a.salient_events, a.dispatches, a.noticed) == (b.salient_events, b.dispatches, b.noticed)
    assert a.dispatches > 0


def test_two_day_counter_keys_carry_T(monkeypatch):
    """(v) 2 日目の顕著行為と出動の鍵が 1 日目と違う(T が鍵に入っている)。〔改訂(第330・RET)〕前は最後に
    「stateful の 2 日のランは counter の用途名を作らない」を見た(stateful を消した)。"""
    seen: list[tuple[str, tuple[int, ...]]] = []

    def spy(real):
        def f(seed, domain, *ctr):
            seen.append((domain, tuple(int(c) for c in ctr)))
            return real(seed, domain, *ctr)
        return f

    monkeypatch.setattr(SAL, "stream", spy(SAL.stream))
    monkeypatch.setattr(CIV, "stream", spy(CIV.stream))
    res = run_day(seed=1, ticks=TPD, sim_days=2, salient_rate_per_10k=RATE_X1000, **KW)
    sal = [c for d, c in seen if d == SAL.SALIENT_COUNTER_DOMAIN]
    dis = [c for d, c in seen if d == CIV.DISPATCH_COUNTER_DOMAIN]
    # 顕著行為は毎 tick 1 本(鍵の時刻 = T・日の鍵 0)
    assert [c[1] for c in sal] == list(range(2 * TPD)) and all(c[0] == 0 for c in sal)
    d1 = {c for c in dis if c[1] < TPD}
    d2 = {c for c in dis if c[1] >= TPD}
    assert d1 and d2 and not (d1 & d2)
    assert res.dispatches == len(dis)
    # 2 日目の頭の引きは 1 日目の頭と違う(同じ日の中の tick でも T が違えば違う列)
    raw1 = core_stream(1, SAL.SALIENT_COUNTER_DOMAIN, 0, 0).random(4)
    raw2 = core_stream(1, SAL.SALIENT_COUNTER_DOMAIN, 0, TPD).random(4)
    assert not np.array_equal(raw1, raw2)
    # 10e より前の stateful の用途名(日の頭の Generator)は 1 本も作らない
    assert not [d for d, _ in seen if d in ("world.salient", "world.public_service_dispatch")]


# ================================================================= 台帳の軸 2: 保存が要る状態を増やさない
def _full_values(monkeypatch) -> dict[str, object]:
    got: list[dict] = []
    real = RUN.full_state_hash

    def spy(agents, world, pstate, pop, sched, owners, **kw):
        got.append(owners)
        return real(agents, world, pstate, pop, sched, owners, **kw)

    monkeypatch.setattr(RUN, "full_state_hash", spy)
    run_day(seed=1, ticks=60, checkpoint_every=60, salient_rate_per_10k=RATE_X1000, **{
        k: v for k, v in KW.items() if k != "checkpoint_every"})
    monkeypatch.setattr(RUN, "full_state_hash", real)
    owners = got[-1]
    return {path: SH.resolve_item(owners, path) for _, path in SL.full_items()}


def test_counter_adds_no_state_to_restore_and_drops_the_two_generators(monkeypatch):
    """〔改訂(第330・RET)〕前は stateful のランと道筋ごとに比べた(stateful を消した)。いまは: 2 つの道筋は「無い」の印
    (None)・Generator を持つ道筋は 1 本も無い・台帳の行は道筋を残している(behavior-hash の定義の一部)。"""
    ct = _full_values(monkeypatch)
    gens = sorted(p for p, v in ct.items() if isinstance(v, np.random.Generator))
    two = ["runner.dispatch.rng", "runner.salient.rng"]
    assert not (set(two) & set(gens))
    assert ct["runner.salient.rng"] is None and ct["runner.dispatch.rng"] is None
    rows = {r.key: r for r in SL.LEDGER if r.place == SL.EXTERNAL}
    for path in two:
        row = next(r for r in rows.values() if path in r.items)
        assert row.restore == SL.REQUIRED and "10c" in row.note and "第330・RET" in row.note


# ================================================================= 再生の突き合わせ(テープの脇の meta)
def _rec(tmp_path, name: str, **kw):
    return run_day(seed=3, ticks=120, tape_path=tmp_path / name, salient_rate_per_10k=RATE_X1000 * 10,
                   **KW, **kw)


def _rep(tmp_path, name: str, **kw):
    from tests.engine.test_tape_wiring import BoomLLM

    return run_day(seed=3, ticks=120, mode="replay", replay=tmp_path / name, llm=BoomLLM(),
                   salient_rate_per_10k=RATE_X1000 * 10, **KW, **kw)


def test_the_tape_carries_the_scheme_and_the_replay_matches(tmp_path):
    """〔改訂(第330・RET)〕前は「counter で録って stateful で再生すると止まる」「stateful のテープ」も見た(消した)。"""
    from shibuya.engine.tape import read_run_meta

    rec = _rec(tmp_path, "c")
    assert rec.dispatches > 0
    meta = read_run_meta(tmp_path / "c")
    assert (meta["rng_scheme"], meta["rng_layout"]) == ("counter", "10e")
    rep = _rep(tmp_path, "c")
    assert rep.final_hash == rec.final_hash and rep.tape_miss_count == 0


def test_a_tape_from_before_10e_is_not_replayed(tmp_path):
    """〔改訂(第330・RET)〕前は「記録の無いテープ(10c より前)は stateful とみなして警告 1 回で再生する」。stateful を
    消したので、記録の無いテープ・stateful のテープ・10c〜10f の counter のテープは止める(警告でなく例外)。"""
    import json

    from shibuya.engine.tape import RUN_META_FILENAME

    _rec(tmp_path, "t")
    meta = tmp_path / "t" / RUN_META_FILENAME
    base = json.loads(meta.read_text(encoding="utf-8"))
    for name, change in (("no_value", {"rng_scheme": None}), ("stateful", {"rng_scheme": "stateful"}),
                         ("pre_layout", {"rng_layout": None})):
        d = dict(base)
        for k, v in change.items():
            if v is None:
                d.pop(k)
            else:
                d[k] = v
        meta.write_text(json.dumps(d) + "\n", encoding="utf-8")
        with pytest.raises(ValueError, match="10e より前"):
            _rep(tmp_path, "t")
    meta.write_text(json.dumps(base) + "\n", encoding="utf-8")
    assert _rep(tmp_path, "t").tape_miss_count == 0


