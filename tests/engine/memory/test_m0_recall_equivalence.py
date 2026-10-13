"""第 1 期 1-6 記憶の器 M0: 腕 on で、今の記憶の表の想起と器の想起が同じ候補を返す(口の約束 1-6 の約束 (2))。

- 腕 on のランで、抜き取った刻みの**全部の想起**を 2 通りに引いて突き合わせる: (a) 今の表(``mem_*``・器を外して
  ``MemoryLayer.recall`` を呼ぶ=既定の道)と (b) 器(腕の道)。描き方に渡す ``RecallItem`` の列(候補の集合と順と中身=
  行・時刻・種類・相手・対象・結果・セル・要旨・店の行の向きと出どころ)が同じ。計数は (a) の分を戻す。
- ランの終わりに、全部の体・全部の行で器の行(仮の出来事・強さ・目印の時刻・注釈と順)が記憶の表と同じ。
- final・呼数・想起の計数が腕 on/off で同じ(器は結果を変えない=約束 (1))。
- 再開: 腕 on の 2 日のランを日中で止めて再開すると、器は戻した記憶の表から作り直され、再開の後の checkpoint と
  テープの列 ``recalled_event_ids`` が通しのランと同じ。
- 合成の世界(data 無し)は全部の刻み。世界資産 5,000 体(``slow``・data あり)は刻みの 1/7 を抜き取る
  (``T % 7 == 0``・206 刻み)。
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Callable

import pytest

from shibuya.engine.memory import MemoryLayer
from shibuya.engine.run import run_day
from shibuya.engine.tape import Tape

from tests.engine.memory._m0 import KW, WORLD, run_with_arm, table_vs_store


@dataclass
class Probe:
    sample: Callable[[int], bool]
    compared: int = 0
    nonempty: int = 0
    items: int = 0
    store_items: int = 0
    steps: set = field(default_factory=set)
    mismatch: list = field(default_factory=list)
    layer: Any = None
    agents: Any = None


@pytest.fixture
def probe(monkeypatch):
    """``MemoryLayer.recall`` を包み、抜き取った刻みで今の表の道と器の道を両方引いて比べる(返すのは器の道)。"""
    orig_recall = MemoryLayer.recall
    orig_after = MemoryLayer.after_tick
    made: list[Probe] = []

    def make(sample: Callable[[int], bool]) -> Probe:
        pr = Probe(sample)
        made.append(pr)

        def recall(self, agents, agent_id, tick, condition, inviter=-1):  # noqa: ANN001, ANN202
            if self.memory_store is None or not pr.sample(int(tick)):
                return orig_recall(self, agents, agent_id, tick, condition, inviter)
            ms = self.memory_store
            saved = Counter(self.recall_stats)
            self.memory_store = None
            try:
                ref = orig_recall(self, agents, agent_id, tick, condition, inviter)
            finally:
                self.memory_store = ms
            self.recall_stats = saved  # 計数は 1 回分に戻す(manifest の比べのため)
            got = orig_recall(self, agents, agent_id, tick, condition, inviter)
            pr.compared += 1
            pr.steps.add(int(tick))
            if got:
                pr.nonempty += 1
                pr.items += len(got)
                pr.store_items += sum(1 for it in got if it.row >= self.n_rows)
            if list(ref) != list(got):
                pr.mismatch.append((int(agent_id), int(tick), list(ref), list(got)))
            return got

        def after_tick(self, agents, tick, **kw):  # noqa: ANN001, ANN202
            pr.layer, pr.agents = self, agents
            return orig_after(self, agents, tick, **kw)

        monkeypatch.setattr(MemoryLayer, "recall", recall)
        monkeypatch.setattr(MemoryLayer, "after_tick", after_tick)
        return pr

    return make


def _check(pr: Probe, off: Any, on: Any) -> None:
    assert pr.compared > 0 and pr.nonempty > 0 and pr.items > 0
    assert pr.mismatch == [], pr.mismatch[:3]
    assert table_vs_store(pr.agents, pr.layer) == []
    assert (on.final_hash, on.llm_calls) == (off.final_hash, off.llm_calls)
    assert on.memory_summary["recall"] == off.memory_summary["recall"]
    ms = on.memory_summary["memory_store"]
    assert ms["arm"] == "events" and ms["origins"]["log"] == 0 and ms["origins"]["legacy"] == ms["rows"] > 0
    assert "memory_store" not in off.memory_summary


@pytest.mark.parametrize("store_memory,memory_n", [("on", 128), ("off", 128), ("on", 4), ("off", 3)])
def test_synthetic_every_recall_is_the_same(probe, store_memory, memory_n):
    """``memory_n`` を小さくした 2 本は追い出しが何百回も起きる(検収 L10: 追い出しの同値をランで確かめる)。"""
    kw = dict(KW, store_memory=store_memory, memory_n=memory_n)
    off = run_with_arm("mem", run_day, **kw)
    pr = probe(lambda t: True)
    on = run_with_arm("events", run_day, **kw)
    _check(pr, off, on)
    if store_memory == "on":
        assert pr.store_items > 0  # 7c の店の行が器の想起の内側で競った
    ev = on.memory_summary["memory_store"]["counts"].get("evictions", 0)
    assert ev == on.memory_summary["counts"].get("evictions", 0)
    if memory_n <= 4:
        assert ev > 100


#: 比べない葉(環境の欄・壁時計・ランごとに違う印=1-3 の試験と同じ)。
SKIP_LEAVES = ("env_id", "environment", "wall", "seconds", "phase", "checkpoint_s", "run_id", "state_files")


def _flat(x, path=""):
    if isinstance(x, dict):
        out = {}
        for k, v in x.items():
            out.update(_flat(v, f"{path}.{k}" if path else str(k)))
        return out
    if isinstance(x, list):
        out = {}
        for i, v in enumerate(x):
            out.update(_flat(v, f"{path}[{i}]"))
        return out
    return {path: x}


def test_manifest_differs_only_by_the_store_instrument():
    """腕 on/off の manifest: 既存の葉は全部同じ。足したのは ``memory_summary.memory_store`` の下の葉だけ。"""
    off = _flat(run_with_arm("mem", run_day, **KW).run_manifest_fields())
    on = _flat(run_with_arm("events", run_day, **KW).run_manifest_fields())
    keep = lambda d: {k: v for k, v in d.items() if not any(s in k for s in SKIP_LEAVES)}  # noqa: E731
    off, on = keep(off), keep(on)
    added = sorted(set(on) - set(off))
    assert set(off) <= set(on) and added and all(k.startswith("memory_summary.memory_store.") for k in added)
    assert [k for k in off if off[k] != on[k]] == []
    assert on["memory_summary.memory_store.arm"] == "events"


def test_synthetic_two_days_resume_rebuilds_the_store(probe, tmp_path):
    """腕 on の 2 日のラン: 日中(12:30)で止めて再開=器は戻した表から作り直す。再開の後は通しのランと同じ。"""
    kw = dict(KW, ticks=1440, sim_days=2, checkpoint_every=60)
    straight = run_with_arm("events", run_day, tape_path=tmp_path / "s", **kw)
    off = run_with_arm("mem", run_day, **kw)
    assert straight.final_hash == off.final_hash
    stop = 750
    a = run_with_arm("events", run_day, state_out=tmp_path / "state", stop_at_tick=stop, tape_path=tmp_path / "a",
                     **kw)
    pr = probe(lambda t: True)
    b = run_with_arm("events", run_day, resume_from=tmp_path / "state" / a.resume["state_files"][-1]["file"],
                     tape_path=tmp_path / "b", **kw)
    assert pr.mismatch == [] and pr.nonempty > 0
    assert table_vs_store(pr.agents, pr.layer) == []
    assert pr.layer.stats["memory_store_rebuilt_rows"] > 0
    want = [(c.tick, c.behavior_hash, c.full_hash) for c in straight.checkpoints if c.tick >= stop]
    got = [(c.tick, c.behavior_hash, c.full_hash) for c in b.checkpoints if c.tick >= stop]
    assert got == want and b.final_hash == straight.final_hash

    def col(path, name):
        t = Tape(path)
        rows = zip(t.column("tick"), t.column("agent_id"), t.column("wake_class"), t.column(name))
        return sorted((int(x), int(y), int(z), tuple(v)) for x, y, z, v in rows if int(x) >= stop)

    assert col(tmp_path / "b", "recalled_event_ids") == col(tmp_path / "s", "recalled_event_ids")
    assert col(tmp_path / "b", "recalled_rows") == col(tmp_path / "s", "recalled_rows")
    assert any(v for *_k, v in col(tmp_path / "b", "recalled_event_ids"))


@pytest.mark.slow
@pytest.mark.requires_data("world_v2:w17_schedule.parquet")
@pytest.mark.parametrize("cfg", ["v3_mem_rel", "v3_mem_store"])
def test_world_5000_sampled_recalls_are_the_same(probe, cfg):
    """世界資産 5,000 体・mock・1 日(byte-check の記憶の構成)で、刻みの 1/7 の全部の想起を突き合わせる。"""
    from shibuya import cli

    extra = {"v3_mem_rel": {"relations": "on"}, "v3_mem_store": {"store_memory": "on"}}[cfg]
    kw = dict(n_agents=5_000, seed=1, world_dir=str(WORLD), vocab_version="v3", memory="on", **extra)
    off = run_with_arm("mem", cli.run, **kw)
    pr = probe(lambda t: t % 7 == 0)
    on = run_with_arm("events", cli.run, **kw)
    _check(pr, off, on)
    assert len(pr.steps) >= 150 and pr.compared > 1_000
