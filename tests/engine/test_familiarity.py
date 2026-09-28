"""4 段目(記憶の先行部品=M13 訪問カウンタ+M17 露出カウンタ・親しみの表・第290)。

正典: ``docs/design/v2-familiarity-counters-implementation-agenda.md`` §1〜§3。

見るもの
(a) 既定 off=表を確保しない・manifest は空=既定 checkpoint 不変(15 腕は記録で固定)/
(b) 表の形(K 行 × 16 B・空行 −1)と ``thing_id`` の符号化(POI・場所 −(cell+2)・人 1<<30|id)/
(c) 書き手 3 つ(訪問・看板の露出・セルに入った回)・統合・新規・追い出し(A 最小)/
(d) A の読み口(近似式・厳密式との差・表に無いもの)/ (e) 描画の控え(p_see の通過だけ)・
    resolve の訪問の控え(成立した行だけ)/ (f) on でも挙動は変えない(表の欄を除けば off と一致)/
(g) 親決定 (f): 看板の露出=描画による露出+**入った回 × そのセルの看板 × p_see**(同じ tick の同じ
    (体, POI) は 1 回)。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from shibuya.agents.state import FAMILIARITY_FIELDS, AgentState
from shibuya.engine import resolve as R
from shibuya.engine.familiarity import (
    ACTIVATION_ABSENT,
    FAMILIARITY_K,
    FAMILIARITY_MODES,
    FamiliarityLayer,
    activation_approx,
    activation_exact,
    person_thing,
    place_thing,
    thing_kind,
)
from shibuya.engine.run import run_day

WORLD_DIR = Path("data/world/v2")


def _agents(cells, k=4):
    a = AgentState(len(cells), familiarity_columns=True, familiarity_k=k)
    with a.writable():
        a.registry.cell[:] = np.asarray(cells)
    a.freeze()
    return a


# ------------------------------------------------------------------ (a) 既定 off
def test_off_by_default_allocates_nothing_and_writes_nothing():
    a = AgentState(3)
    assert not any(n in a.registry.arrays for n in FAMILIARITY_FIELDS)
    assert FAMILIARITY_MODES == ("off", "on") and FAMILIARITY_K == 64
    res = run_day(n_agents=30, seed=1, ticks=20, renderer="stub", checkpoint_every=20)
    m = res.run_manifest_fields()
    assert m["familiarity"] is False and m["familiarity_summary"] == {} and m["familiarity_k"] == 64
    explicit = run_day(n_agents=30, seed=1, ticks=20, renderer="stub", checkpoint_every=20,
                       familiarity="off")
    assert explicit.final_hash == res.final_hash
    with pytest.raises(ValueError):
        run_day(n_agents=4, seed=1, ticks=2, renderer="stub", familiarity="maybe")
    with pytest.raises(ValueError):
        run_day(n_agents=4, seed=1, ticks=2, renderer="stub", familiarity=True, familiarity_k=0)


# ------------------------------------------------------------------ (b) 表の形・符号化
def test_the_table_is_k_rows_of_16_bytes_with_empty_rows():
    a = AgentState(2, familiarity_columns=True, familiarity_k=64)
    assert a.fam_thing.shape == (2, 64) and (a.fam_thing == -1).all()
    assert a.declared_bytes_per_agent - AgentState(2).declared_bytes_per_agent == 1_024
    assert int(place_thing(0)) == -2 and int(place_thing(519)) == -521  # 空行 −1 と重ならない
    assert int(person_thing(17)) == (1 << 30) | 17
    kinds = thing_kind(np.array([-1, 0, 12, -2, -600, (1 << 30) | 3]))
    assert kinds.tolist() == ["empty", "poi", "poi", "place", "place", "person"]


# ------------------------------------------------------------------ (c) 書き手・統合・追い出し
def test_visit_signage_and_place_entries_merge_into_one_row_per_thing():
    a = _agents([5, 5], k=4)
    lay = FamiliarityLayer(2, 4)
    # tick 0: 両者がセル 5 に居る(入場 1 回)・体 0 が POI 7 を訪問・体 1 が POI 7 の看板を見た
    lay.after_tick(a, 0, ([np.array([0])], [np.array([7])]), [(1, 7)])
    r = a.registry
    assert sorted(r.fam_thing[0].tolist()) == sorted([7, int(place_thing(5)), -1, -1])
    j0 = r.fam_thing[0].tolist().index(7)
    j1 = r.fam_thing[1].tolist().index(7)
    assert (int(r.fam_visits[0, j0]), int(r.fam_exposures[0, j0])) == (1, 0)
    assert (int(r.fam_visits[1, j1]), int(r.fam_exposures[1, j1])) == (0, 1)
    # tick 3: 体 0 がもう一度訪問・同じセルに居続ける=入場は数えない
    lay.after_tick(a, 3, ([np.array([0])], [np.array([7])]), None)
    assert int(r.fam_visits[0, j0]) == 2 and int(r.fam_first[0, j0]) == 0
    assert int(r.fam_last[0, j0]) == 3
    jp = r.fam_thing[0].tolist().index(int(place_thing(5)))
    assert int(r.fam_exposures[0, jp]) == 1
    s = lay.stats
    assert s["visits"] == 2 and s["exposures_signage_render"] == 1 and s["exposures_place"] == 2
    assert s["exposures_signage_entry"] == 0  # 看板の表を渡していない層=入った回の露出なし
    assert s["new_rows"] == 4 and s["merged"] == 1 and s["evictions"] == 0


def test_a_full_table_evicts_the_row_with_the_smallest_activation():
    a = _agents([-1], k=2)
    lay = FamiliarityLayer(1, 2)
    lay.after_tick(a, 0, ([np.array([0])], [np.array([10])]), None)       # POI 10: 古い 1 回
    for t in (50, 51, 52):
        lay.after_tick(a, t, ([np.array([0])], [np.array([11])]), None)   # POI 11: 最近 3 回
    lay.after_tick(a, 100, ([np.array([0])], [np.array([12])]), None)     # 満杯 → 10 を落とす
    r = a.registry
    assert sorted(r.fam_thing[0].tolist()) == [11, 12]
    assert lay.stats["evictions"] == 1


def test_entering_a_cell_counts_once_and_again_after_leaving():
    a = AgentState(1, familiarity_columns=True, familiarity_k=4)
    lay = FamiliarityLayer(1, 4)
    for t, c in enumerate([3, 3, 4, 4, -1, 3]):
        with a.writable():
            a.registry.cell[0] = c
        lay.after_tick(a, t, None, None)
    r = a.registry
    j3 = r.fam_thing[0].tolist().index(int(place_thing(3)))
    j4 = r.fam_thing[0].tolist().index(int(place_thing(4)))
    assert int(r.fam_exposures[0, j3]) == 2 and int(r.fam_exposures[0, j4]) == 1
    assert lay.stats["exposures_place"] == 3


# ------------------------------------------------------------------ (d) A の読み口
def test_activation_reads_the_approximation_and_absent_things():
    a = _agents([5], k=4)
    lay = FamiliarityLayer(1, 4)
    lay.after_tick(a, 0, ([np.array([0])], [np.array([7])]), None)
    lay.after_tick(a, 10, ([np.array([0])], [np.array([7])]), None)
    got = lay.activation(a, [0, 0, 0], [7, 99, int(place_thing(5))], 100)
    assert got[0] == pytest.approx(float(activation_approx(2, 100)), rel=1e-6)
    assert got[1] == np.float32(ACTIVATION_ABSENT)
    assert got[2] == pytest.approx(float(activation_approx(1, 100)), rel=1e-6)
    top = lay.top_k(a, 0, 100)
    assert [x["thing"] for x in top] == [7, int(place_thing(5))]
    assert top[0]["kind"] == "poi" and top[1]["kind"] == "place"


def test_the_approximation_versus_the_exact_base_level():
    # 1 回きりの接触は近似が ln 2(=1/(1−d))だけ高い(式の構造)
    assert float(activation_approx(1, 0)) - activation_exact([0.0]) == pytest.approx(np.log(2))
    assert float(activation_approx(1, 600)) - activation_exact([600.0]) == pytest.approx(np.log(2))
    # 等間隔 60 回(24 分おき・1 日)では差が小さい
    ages = [24.0 * i for i in range(60)]
    assert abs(float(activation_approx(60, max(ages))) - activation_exact(ages)) < 0.25
    # 最近にまとめた接触では近似が低く出る
    recent = [600.0] + [float(i) for i in range(9)]
    assert float(activation_approx(10, 600)) < activation_exact(recent)


# ------------------------------------------------------------------ (e) 控え(描画・resolve)
def test_the_renderer_notes_signage_only_when_asked_and_seen():
    from shibuya.perception.renderer import Renderer
    from shibuya.world.state import World

    w = World.synthetic(n_cells=9, seed=2)
    a = AgentState(2)
    with a.writable():
        a.cell[:] = 4
        a.last_result_tick[:] = -1
    w.cells.density[:] = w.compute_density(a.cell)
    r = Renderer(w, a, seed=3, vocab_version="v3")
    r.prepare_tick(700)
    assert r.signage_exposures is None
    before = r.render(0, tick=700, wake_reason=3).prompt_hash
    r.signage_exposures = []
    after = r.render(0, tick=700, wake_reason=3).prompt_hash
    assert after == before                                  # 描画は 1 バイトも変わらない
    sp = r._signage_poi(4)
    assert r.signage_exposures == ([(0, sp)] if sp >= 0 else [])
    off = Renderer(w, a, seed=3, vocab_version="v3", signage_p_see=0.0)
    off.prepare_tick(700)
    off.signage_exposures = []
    off.render(1, tick=700, wake_reason=3)
    assert off.signage_exposures == []                      # 注視ゲートを通らない=露出なし


def test_resolve_notes_only_the_successful_visits():
    from types import SimpleNamespace

    from tests.engine.test_move_destination import NOON, _world
    from tests.engine.test_stage3_small_fixes import _PickyMoney
    from tests.engine.test_intent_hold import _FakeGoods

    w = _world()
    ag = AgentState(3)
    with ag.writable(), w.writable():
        ag.registry.money[:] = 10_000
        w.pois.stock[7] = 5
        led = SimpleNamespace(money=_PickyMoney(ag, refuse={1}), goods=_FakeGoods(w.pois.stock))
        out = R.ResolveOutcome(tick=NOON, ledger=led, track_visits=True)
        R._complete_buy(ag, w, np.array([0, 1, 2]), np.array([7, 7, 7]),
                        np.array([800, 800, 800]), NOON, out)
        off = R.ResolveOutcome(tick=NOON, ledger=led)
        R._complete_buy(ag, w, np.array([0]), np.array([7]), np.array([800]), NOON, off)
    assert np.concatenate(out.visit_agents).tolist() == [0, 2]
    assert np.concatenate(out.visit_pois).tolist() == [7, 7]
    assert off.visit_agents == []


def test_cli_passes_the_familiarity_flags(monkeypatch):
    from shibuya import cli

    seen: dict = {}

    class _Stub:
        fleet_fields: dict = {}

        def summary(self) -> str:
            return "(stub)"

    monkeypatch.setattr(cli, "run", lambda **kw: (seen.update(kw), _Stub())[1])
    assert cli.main(["--agents", "8", "--world", "__no_such_dir__", "--cells", "9"]) == 0
    assert seen["familiarity"] == "off" and seen["familiarity_k"] == 64
    assert cli.main(["--agents", "8", "--world", "__no_such_dir__", "--cells", "9",
                     "--familiarity", "on", "--familiarity-k", "32"]) == 0
    assert seen["familiarity"] == "on" and seen["familiarity_k"] == 32


# ------------------------------------------------------------------ (f) on でも挙動は変えない
@pytest.mark.skipif(not (WORLD_DIR / "w17_schedule.parquet").exists(), reason="実世界資産が無い")
def test_on_counts_contacts_and_does_not_change_behaviour_on_the_real_world(monkeypatch):
    from shibuya.agents import state as S
    from shibuya.cli import run as cli_run

    off = cli_run(n_agents=1_000, seed=1, world_dir=str(WORLD_DIR), vocab_version="v3")
    monkeypatch.setattr(
        S.AgentState, "state_hash",
        lambda self: self.registry.state_hash(exclude=FAMILIARITY_FIELDS),
    )
    on = cli_run(n_agents=1_000, seed=1, world_dir=str(WORLD_DIR), vocab_version="v3",
                 familiarity="on")
    assert on.final_hash == off.final_hash       # 表の 5 欄を除けば 1 バイトも変わらない
    assert on.llm_calls == off.llm_calls
    s = on.run_manifest_fields()["familiarity_summary"]
    c = s["counts"]
    assert c["visits"] > 0 and c["exposures_place"] > 0
    assert c["exposures_signage_render"] > 0 and c["exposures_signage_entry"] > 0
    assert set(s["rows_by_kind"]) == {"poi", "place"}   # 人と道は書かない
    assert s["rows_used_per_agent"]["p100"] <= 64


# ------------------------------------------------------------------ (g) 入った回 × 看板 × p_see
def _layer_with_signage(p_see=1.0, n=3):
    table = np.full(10, -1, dtype=np.int64)
    table[5] = 70     # セル 5 の看板は POI 70
    table[6] = 70     # セル 6 も同じ POI が看板(W8 で見える店が重なる)
    return FamiliarityLayer(n, 4, signage_poi_by_cell=table, p_see=p_see, seed=3)


def test_entering_a_cell_exposes_its_signage_once_per_entry():
    a = _agents([5, 2, -1], k=4)
    lay = _layer_with_signage()
    lay.after_tick(a, 0, None, None)             # 体 0 はセル 5 に入る(看板 70)・体 1 はセル 2(看板なし)
    lay.after_tick(a, 1, None, None)             # 居続け=数えない
    r = a.registry
    j = r.fam_thing[0].tolist().index(70)
    assert int(r.fam_exposures[0, j]) == 1 and int(r.fam_visits[0, j]) == 0
    assert 70 not in r.fam_thing[1].tolist()
    s = lay.stats
    assert s["exposures_signage_entry"] == 1 and s["exposures_signage_render"] == 0


def test_the_render_and_the_entry_of_the_same_signage_count_once_per_tick():
    a = _agents([5], k=4)
    lay = _layer_with_signage(n=1)
    lay.after_tick(a, 0, None, [(0, 70)])        # 同じ tick に描画でも入った回でも POI 70
    j = a.registry.fam_thing[0].tolist().index(70)
    assert int(a.registry.fam_exposures[0, j]) == 1
    assert lay.stats["exposures_signage_render"] == 1
    assert lay.stats["exposures_signage_entry"] == 0
    assert lay.stats["exposures_signage_entry_dedup"] == 1


def test_the_entry_gate_draws_the_same_stream_as_the_renderer():
    from shibuya.perception.attention import gate_stage1

    n = 40
    a = AgentState(n, familiarity_columns=True, familiarity_k=4)
    lay = FamiliarityLayer(n, 4, signage_poi_by_cell=np.array([-1, -1, -1, -1, -1, 70]),
                           p_see=0.3, seed=3)
    with a.writable():
        a.registry.cell[:] = 5
    lay.after_tick(a, 7, None, None)
    want = [bool(gate_stage1(1, 0.3, seed=3, domain_counters=(7, i, 70))[0]) for i in range(n)]
    got = [70 in a.registry.fam_thing[i].tolist() for i in range(n)]
    assert got == want and 0 < sum(got) < n
    none = FamiliarityLayer(n, 4, signage_poi_by_cell=np.array([-1, -1, -1, -1, -1, 70]),
                            p_see=0.0, seed=3)
    b = AgentState(n, familiarity_columns=True, familiarity_k=4)
    with b.writable():
        b.registry.cell[:] = 5
    none.after_tick(b, 7, None, None)
    assert none.stats["exposures_signage_entry"] == 0


def test_the_renderer_publishes_the_same_signage_set_it_draws():
    from shibuya.perception.renderer import Renderer
    from shibuya.world.state import World

    w = World.synthetic(n_cells=9, seed=2)
    a = AgentState(2)
    r = Renderer(w, a, seed=3, vocab_version="v3")
    tab = r.signage_poi_by_cell()
    assert tab.tolist() == [r._signage_poi(c) for c in range(r.assets.n_cells)]
    off = Renderer(w, a, seed=3, vocab_version="v3", signage_enabled=False)
    assert (off.signage_poi_by_cell() == -1).all()

