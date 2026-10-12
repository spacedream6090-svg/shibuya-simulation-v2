"""10e(版上げ 1 回目)の試験: E2 の期限つきの辞書の掃除・O64 の分類の確かめ(E1 の試験は状態台帳の試験の中)。

記録: ``docs/bench/analysis/wallbounce-1012/10e/README.md``。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

import shibuya.engine.run as RUN
from shibuya.engine.conversation import (
    PAIR_INVITE_REFRACTORY_TICKS,
    SPEAKER_INVITE_REFRACTORY_TICKS,
    ConversationManager,
)
from shibuya.engine.run import run_day

WORLD_DIR = Path("data/world/v2")
real_data = pytest.mark.skipif(not (WORLD_DIR / "w17_schedule.parquet").exists(), reason="実世界資産が無い")
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
    real = RUN.full_state_hash

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
        mp.setattr(RUN, "full_state_hash", spy("on"))
        on = run_day(tape_path=d / "on", **kw)
        mp.setattr(RUN, "full_state_hash", spy("off"))
        mp.setattr(ConversationManager, "purge_expired", lambda self, tick: 0)
        off = run_day(tape_path=d / "off", **kw)
    finally:
        mp.undo()
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
    real = RUN.full_state_hash

    def spy(agents, world, pstate, pop, sched, owners, **k):
        r = owners.get("renderer")
        sizes.append(-1 if r is None else len(getattr(r, "signage_exposures", [])))
        return real(agents, world, pstate, pop, sched, owners, **k)

    mp = pytest.MonkeyPatch()
    try:
        mp.setattr(RUN, "full_state_hash", spy)
        res = cli.run(n_agents=500, seed=1, world_dir=str(WORLD_DIR), vocab_version="v3", familiarity="on")
    finally:
        mp.undo()
    c = res.run_manifest_fields()["familiarity_summary"]["counts"]
    assert c["exposures_signage_render"] > 0  # 露出は実際に集まっていた
    assert sizes and all(n == 0 for n in sizes), sizes
