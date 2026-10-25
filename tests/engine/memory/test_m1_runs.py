"""第 6 期 6-5 記憶 M1 の腕(``--memory-model m1``)のラン・器・守りの試験(合成の世界・data 無し)。

- 既定の腕(器だけ=M0): M1 の状態も意味の手がかりも作らない・manifest に ``mr65`` の葉が出ない(1-6 の葉のまま)。
- 器の単体: 同じ鍵を重ねると直近の時刻が進む・想起は M1 の τ と言葉(はっきり/うろ覚え)・言葉の描き方の口。
- M0 との比べ(負の対照=記録の数): 腕 m1 のランの全部の想起で、同じ器の行を M0 の式で並べた上位 k と比べる。
  同じである必要はない(数を記録 mr65/README.md)。M1 が何もしていない(全部同じ)なら落とす。
- 再開: 腕 m1 の 2 日の日の境目の再開=通し(行 M0M=直近の時刻と倍率が状態のファイルから戻る)。
- 守り: 書く口の宣言(``M0M``)を外すと書いた所で落ちる・付け替えの守り・腕は組み立てで 1 回だけ。
- 〔検収 M1〕人ごとの忘れる速さの鍵の seed=ランの母集団の seed(10f S1 の ``_check_split`` を腕 m1 で回す・前のランの値が
  残らない負の対照)。〔検収 L6〕記憶 off のランで腕を立てると止める。
"""

from __future__ import annotations

from collections import Counter

import numpy as np
import pytest

from shibuya.core.time_consts import NS_PER_SECOND, STEPS_PER_DAY
from shibuya.engine import memory_m1 as M1
from shibuya.engine import memory_store as MS
from shibuya.engine.memory_store import LegacyEvent, MemoryStore
from shibuya.engine.run import run_day
from shibuya.engine.systems import guard as G
from shibuya.engine.tape import Tape

from tests.engine.memory._mr65 import KW, arms, mr65

TPD = int(STEPS_PER_DAY)
S = NS_PER_SECOND


def _store(n: int = 3, rows: int = 4) -> MemoryStore:
    ms = MemoryStore(n, rows, step_seconds=60, minutes_per_step=1.0)
    ms.enable_arms(m1=M1.M1State(n, n * rows, tau=M1.tau_from_m0(-2.0), seed=1))
    return ms


def _ev(t_s: int, kind: int = 1, partner: int = -1, obj: int = 5) -> LegacyEvent:
    return LegacyEvent(t_s * S, kind, partner, obj, 0, 2)


def test_default_arms_create_nothing_and_add_no_manifest_leaves():
    with arms("events"):
        r = run_day(**KW)
    ms_sum = r.run_manifest_fields()["memory_summary"]["memory_store"]
    assert "mr65" not in ms_sum
    with arms("mem"):
        r0 = run_day(**KW)
    assert r0.final_hash == r.final_hash  # 器(M0)は結果を変えない=既定の腕のまま


def test_store_unit_touch_times_strength_and_words():
    ms = _store()
    ms.remember(0, _ev(600), 1, "legacy")
    ms.remember(0, _ev(1200), 1, "legacy")  # 同じ鍵を重ねる
    ms.remember(0, _ev(1260, kind=2, obj=7), 1, "legacy")
    rec = ms.m1.recent_ns
    assert rec[0].tolist() == [1200 * S, 600 * S, M1.NO_TIME]
    assert rec[1].tolist() == [1260 * S, M1.NO_TIME, M1.NO_TIME]
    assert int(ms._ms_n[0]) == 2 and int(ms._ms_n[1]) == 1
    now = 1320 * S
    views = ms.recall(0, now, 3, tau=99.0)  # tau の引数は M1 では読まない(M1 の τ)
    assert {v.kind for v in views} == {1, 2}
    A = ms.m1.strength(np.asarray([0, 1]), 0, now, ms._ms_n[:2], ms._ms_first_ns[:2], ms._lg_kind[:2], ms._ms_imp[:2])
    for v in views:
        assert v.clarity == str(M1.clarity_words(A[v.row], ms.m1.tau))
    # ずっと後には思い浮かばない(τ を下回る)
    assert ms.recall(0, now + 30 * 24 * 3600 * S, 3) == ()


def test_render_words_port_marks_vague_items():
    from datetime import datetime, timedelta

    v = MS.MemoryView(row=0, event_id=(0, -1), origin="legacy", clarity="うろ覚え", grain="そのまま", kind=1,
                      partner=-1, obj=0, result=0, cell=0, annotation="", when_ns=0, first_ns=0)
    clear = v._replace(clarity="はっきり")
    clock = lambda step: datetime(2026, 7, 28) + timedelta(minutes=int(step))  # noqa: E731
    kw = dict(clock=clock, poi_names=["カフェ"], place_ids=["c0"])
    with pytest.raises(ValueError, match="M0 の描き方"):
        MS.render_memories([v], **kw)
    plain = MS.render_memories([clear], **kw)
    worded = MS.render_memories([v], words=True, **kw)
    assert MS.render_memories([clear], words=True, **kw) == plain  # はっきりは M0 と同じバイト
    assert MS.WORD_PREFIX["うろ覚え"] in worded and worded != plain


def _topk_harness(monkeypatch):
    """腕 m1 の想起ごとに、同じ器の行を M0 の式で並べた上位 k と比べる(計数を戻す=ランを変えない)。"""
    tally: Counter = Counter()
    orig = MemoryStore.recall

    def recall(self, agent, t_ns, k, **kw):
        got = orig(self, agent, t_ns, k, **kw)
        if self.m1 is None:
            return got
        last, stats = self._ms_last, Counter(self._ms_stats)
        m1 = self.m1
        object.__setattr__(self, "m1", None)
        try:
            m0 = orig(self, agent, t_ns, k, **kw)
        finally:
            object.__setattr__(self, "m1", m1)
            object.__setattr__(self, "_ms_last", last)
            self._ms_stats.clear()
            self._ms_stats.update(stats)
        a = [(v.row, v.kind) for v in got]
        b = [(v.row, v.kind) for v in m0]
        tally["calls"] += 1
        tally["same_order"] += int(a == b)
        tally["same_set"] += int(set(a) == set(b))
        tally["m1_fewer"] += int(len(a) < len(b))
        tally["m1_more"] += int(len(a) > len(b))
        tally["both_empty"] += int(not a and not b)
        return got

    monkeypatch.setattr(MemoryStore, "recall", recall)
    return tally


def test_m1_recall_differs_from_m0_top_k(monkeypatch, tmp_path):
    tally = _topk_harness(monkeypatch)
    with arms("events", model="m1"):
        r = run_day(tape_path=tmp_path / "m1", **KW)
    assert tally["calls"] > 100
    # 負の対照: M1 が何もしていないなら全部同じ=落とす。違う所の数は記録(mr65/README.md)
    assert tally["same_order"] < tally["calls"]
    assert mr65(r)["m1"]["counts"]["touched"] > 0
    assert mr65(r)["arms"]["model"] == "m1"


def _cp(r):
    return [(int(c.tick), c.behavior_hash, c.full_hash) for c in r.checkpoints if int(c.tick) >= TPD]


def test_m1_two_days_resume_is_the_straight_run(tmp_path):
    kw = dict(KW, ticks=TPD, sim_days=2, checkpoint_every=60, population_seed=5)
    with arms("events", model="m1"):
        straight = run_day(tape_path=tmp_path / "s", **kw)
        a = run_day(state_out=tmp_path / "state", stop_at_tick=TPD, tape_path=tmp_path / "a", **kw)
        b = run_day(resume_from=tmp_path / "state" / a.resume["state_files"][-1]["file"], tape_path=tmp_path / "b",
                    **kw)
    assert b.final_hash == straight.final_hash and _cp(b) == _cp(straight) and _cp(b)

    def col(p):
        t = Tape(p)
        return sorted((int(x), int(y), tuple(v)) for x, y, v in zip(t.column("tick"), t.column("agent_id"),
                                                                     t.column("recalled_rows")) if int(x) >= TPD)
    assert col(tmp_path / "b") == col(tmp_path / "s")
    sb, ss = mr65(b)["m1"], mr65(straight)["m1"]
    assert sb["rows_by_known_times"] == ss["rows_by_known_times"] and sb["scale"] == ss["scale"]
    assert sb["rate_seed"] == ss["rate_seed"] == 5  # 〔検収 M1〕母集団の seed


def test_m1_rate_seed_is_the_population_seed(monkeypatch):
    """〔検収 M1〕腕 m1 の人ごとの忘れる速さ(用途名 memory.forgetting_rate=母集団の側)は、そのランの母集団の seed から引く
    (10f S1・``_check_split``)。``cli.run(population_seed=7)`` の後に ``run_day(population_seed=9)`` を直に回しても 9
    (プロセスの大域の値が残らない=負の対照)。"""
    from shibuya import cli
    from tests.engine.test_salt_seed_split_10f import _check_split, _record_keys

    seen = _record_keys(monkeypatch)
    with arms("events", model="m1"):
        r = cli.run(n_agents=60, seed=3, population_seed=7, environment_seed=11, n_cells=9, ticks=240,
                    checkpoint_every=60, memory="on", vocab_version="v3")
    used = _check_split(seen, 3, 7, 11)
    assert "memory.forgetting_rate" in used
    assert mr65(r)["m1"]["rate_seed"] == 7
    seen.clear()
    with arms("events", model="m1"):
        r2 = run_day(n_agents=60, seed=3, population_seed=9, environment_seed=11, n_cells=9, ticks=240,
                     checkpoint_every=60, memory="on", vocab_version="v3")
    by = {s for s, d in seen if d == "memory.forgetting_rate"}
    assert by == {9}, by  # 前のラン(7)の値が残らない
    assert mr65(r2)["m1"]["rate_seed"] == 9
    used2 = _check_split(seen, 3, 9, 11)
    assert "memory.forgetting_rate" in used2
    # 省略=seed と同じ(10f の規則)
    seen.clear()
    with arms("events", model="m1"):
        run_day(n_agents=30, seed=4, n_cells=9, ticks=60, memory="on", vocab_version="v3")
    assert {s for s, d in seen if d == "memory.forgetting_rate"} == {4}


def test_m1_needs_the_population_seed_at_assembly():
    """〔検収 M1〕器に腕 m1 を置くときに母集団の seed が無ければ止める(既定の 0 で黙って引かない)。"""
    from shibuya.engine.memory import MemoryLayer

    with arms("events", model="m1"):
        layer = MemoryLayer(4, 8)
        with pytest.raises(ValueError, match="母集団の seed"):
            layer.enable_memory_store(step_seconds=60)
        layer2 = MemoryLayer(4, 8)
        ms = layer2.enable_memory_store(step_seconds=60, population_seed=7)
    assert ms.m1.seed == 7


@pytest.mark.parametrize("kw", [{"model": "m1"}, {"cue": "embed", "embed_model": "ngram-test"}, {"grain": "day"}])
def test_memory_off_with_memory_arms_is_refused(kw):
    """〔検収 L6〕記憶 off のランで 6-5 の腕を立てたら止める(check_arms と同じ形・ランの種類が「腕」になる抜け道を塞ぐ)。
    負の対照: 腕が既定なら記憶 off のランは通る。"""
    from shibuya import cli

    off = dict(KW, memory="off", relations="off", store_memory="off", ticks=60)
    with arms("events", **kw):
        with pytest.raises(ValueError, match="器のラン"):
            run_day(**off)
        with pytest.raises(ValueError, match="器のラン"):
            cli.run(**off)
    with arms("events"):
        assert run_day(**off).final_hash


def test_write_needs_the_declared_m0m_path():
    ms = _store()
    with G.system_scope("memory", None, None, paths=frozenset({"M0:mem_layer.memory_store.*",
                                                                 "M0R:mem_layer.memory_store.*"})):
        if G.PATHS_PERMIT is None:
            pytest.skip("書きの検査の切替口が off")
        with pytest.raises(PermissionError, match="M0M"):
            ms.remember(0, _ev(60), 1, "legacy")
    with G.system_scope("memory", None, None, paths=frozenset({"M0*:mem_layer.memory_store.*"})):
        ms.remember(0, _ev(60), 1, "legacy")


def test_enable_arms_once_and_outside_the_systems():
    ms = MemoryStore(2, 4, step_seconds=60, minutes_per_step=1.0)
    with G.system_scope("memory", None, None):
        with pytest.raises(RuntimeError, match="系の外"):
            ms.enable_arms(m1=M1.M1State(2, 8, tau=-3.0, seed=1))
    ms.enable_arms(m1=M1.M1State(2, 8, tau=-3.0, seed=1))
    with pytest.raises(RuntimeError, match="1 回だけ"):
        ms.enable_arms(grain="day")
    with pytest.raises(AttributeError):
        ms.m1 = None
    with pytest.raises(ValueError, match="M1 の強さ"):
        MemoryStore(2, 4, step_seconds=60, minutes_per_step=1.0).enable_arms(uncapped=True)


def test_arms_without_the_store_are_refused():
    with arms("mem", model="m1"):
        with pytest.raises(ValueError, match="器のラン"):
            run_day(**KW)
