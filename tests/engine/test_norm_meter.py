"""第308 D-107 (a): 群・規範の計器(``engine.norm_meter``)。**読むだけ**=ランの状態を変えない。"""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from shibuya.agents.state import Activity, AgentKind, AgentState, ResultCode
from shibuya.engine import norm_meter as NM
from shibuya.world.state import World


def meter(n: int = 6, *, station=(2,)):
    w = World.synthetic(n_cells=4, seed=3)
    a = AgentState(n)
    with a.writable():
        a.cell[:] = 0
        a.kind[:] = AgentKind.VISITOR
    m = NM.GroupNormMeter(a, w, role_codes={"接客": 12, "補充": 13}, code_words={0: "移動", 5: "会話", 12: "接客"},
                          process_assets=SimpleNamespace(station_exit_cell=np.asarray(station)))
    return m, a


def test_entropy_bits_matches_the_d68_formula():
    assert NM.entropy_bits(np.array([1, 1, 1, 1])) == pytest.approx(2.0)
    assert NM.entropy_bits(np.array([5, 0, 0])) == 0.0
    assert NM.entropy_bits(np.array([0, 0])) == 0.0


def _walk(a, ids, target, xy):
    with a.writable():
        a.activity[:] = int(Activity.IDLE)
        a.target_node[:] = -1
        a.activity[ids] = int(Activity.MOVING)
        a.target_node[ids] = target
        a.xy[ids] = xy


def test_cowalk_needs_same_cell_same_target_within_2m_for_5_minutes():
    m, a = meter(6)
    for t in range(6):
        _walk(a, np.array([0, 1, 2]), 7, np.array([[0.0, 0.0], [1.0, 0.0], [1.5, 0.5]]))
        with a.writable():  # 体 3 は 3 m 離れる・体 4 は別の移動先
            a.activity[[3, 4]] = int(Activity.MOVING)
            a.target_node[3] = 7
            a.xy[3] = (4.5, 0.0)
            a.target_node[4] = 8
            a.xy[4] = (0.5, 0.0)
        m.observe_tick(t)
    s = m.summary()["cowalk"]
    assert s["episodes_5min"] == 3 and s["distinct_pairs_5min"] == 3      # (0,1)(0,2)(1,2)
    assert s["group_size_minutes"] == {3: 2}                              # 5 分目と 6 分目の 2 分
    assert s["cowalk_agent_minutes"] == 6 and s["moving_agent_minutes"] == 6 * 5
    assert s["ticks_skipped_over_pair_cap"] == 0


def test_cowalk_run_resets_when_the_pair_breaks():
    m, a = meter(4)
    for t in range(9):
        far = t == 3  # 4 分目に離れる → 5 分続かない/その後 5 分続けば 1 回
        _walk(a, np.array([0, 1]), 5, np.array([[0.0, 0.0], [10.0 if far else 1.0, 0.0]]))
        m.observe_tick(t)
    s = m.summary()["cowalk"]
    assert s["episodes_5min"] == 1 and s["group_size_minutes"] == {2: 1}


def test_context_entropy_counts_actions_by_place_and_hour():
    m, a = meter(6, station=(2,))
    with a.writable():
        a.cell[:] = [0, 0, 2, 2, 1, -1]
        a.poi_ref[:] = -1
        a.poi_ref[4] = 0          # 在店=店
        a.transit_state[:] = 0
    m.observe_actions(60 * 9, np.arange(6), np.array([0, 5, 0, 0, 5, 0]))   # 9 時
    s = m.summary()["context_entropy"]
    bp = s["by_place"]
    assert bp["街路"]["n"] == 2 and bp["街路"]["entropy_bit"] == pytest.approx(1.0)
    assert bp["駅"]["n"] == 2 and bp["駅"]["mode_action"] == "移動" and bp["駅"]["mode_share"] == 1.0
    assert bp["店"]["n"] == 1 and bp["店"]["mode_action"] == "会話"
    assert s["actions_off_stage"] == 1
    assert {r["hour"] for r in s["by_place_hour"]} == {9}


def test_role_words_count_results_and_no_permission():
    m, a = meter(4)
    m.observe_actions(10, np.array([0, 1, 2, 3]), np.array([12, 12, 13, 0]))
    with a.writable():
        a.last_result[:] = [int(ResultCode.OK), int(ResultCode.NO_PERMISSION), int(ResultCode.NO_PERMISSION), 0]
        a.last_result_tick[:] = 10
    m.observe_results(10)
    rw = m.summary()["role_words"]
    assert rw["role_actions"] == 3 and rw["no_permission"] == 2
    assert rw["by_word_result"]["接客"] == {"権限なし": 1, "成立": 1}
    assert rw["by_word_result"]["補充"] == {"権限なし": 1}


def test_summary_declares_convention_not_norm_and_does_not_judge():
    m, _a = meter(2)
    d = m.summary()["declared"]
    assert "慣習" in d["norm_layers"] and "判定しない" in d["judgement"]
    assert d["reference"]["moussaid_2010_group_share"] == [0.55, 0.70]


def test_the_meter_only_reads_the_run_state():
    """計器を空にしたランと final・呼数が一致する=**読むだけ**(状態・乱数・テープに触れない)。"""
    from shibuya import cli

    kw = dict(n_agents=150, seed=2, world_dir=None, n_cells=16, ticks=240, checkpoint_every=120)
    with_meter = cli.run(**kw)
    g = with_meter.run_manifest_fields()["group_norms"]
    assert set(g) >= {"declared", "cowalk", "conversation_group_size_a1", "context_entropy", "role_words", "propagation"}
    saved = {k: getattr(NM.GroupNormMeter, k) for k in ("observe_actions", "observe_results", "observe_tick")}
    try:
        for k in saved:
            setattr(NM.GroupNormMeter, k, lambda self, *a, **kw: None)
        without = cli.run(**kw)
    finally:
        for k, v in saved.items():
            setattr(NM.GroupNormMeter, k, v)
    assert (with_meter.final_hash, with_meter.llm_calls) == (without.final_hash, without.llm_calls)
    again = cli.run(**kw)
    assert again.run_manifest_fields()["group_norms"] == g  # 決定論


# ---------------------------------------------------------------- 第309 Q148: 瞬間の群れ歩き
def _step(m, a, t, xy_now, moving=None):
    with a.writable():
        a.xy[:] = np.asarray(xy_now, dtype=np.float32)
        a.activity[:] = int(Activity.IDLE)
        a.activity[list(moving if moving is not None else range(a.n))] = int(Activity.MOVING)
        a.transit_state[:] = 0
    m.observe_tick(t)


def test_instant_group_walk_needs_2m_same_direction_and_both_walking():
    m, a = meter(5)
    base = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.5], [50.0, 50.0], [0.5, 0.5]])
    _step(m, a, 0, base)  # 最初の tick は進行方向が無い=数えない
    s0 = m.summary()["instant_group_walk"]
    assert s0["walker_minutes"] == 0
    # 体 0・1・2 は +x へ 1 m(2 m 内・同方向)/体 3 は遠い/体 4 は逆向き(−x)
    nxt = base + np.array([[1, 0], [1, 0], [1, 0], [1, 0], [-1, 0]], dtype=float)
    _step(m, a, 1, nxt)
    s = m.summary()["instant_group_walk"]
    assert s["walker_minutes"] == 5 and s["grouped_walker_minutes"] == 3
    assert s["grouped_share"] == pytest.approx(0.6)
    assert s["group_minutes_by_size"] == {"3": 1}
    assert s["walker_minutes_by_group_size"] == {"1(独り)": 2, "2": 0, "3": 3, "4+": 0}
    assert s["reference_moussaid_2010_group_share"] == [0.55, 0.70]
    assert "瞬間" in s["definition"] and "5 分連続" in s["definition"]


def test_instant_group_walk_counts_neighbours_across_grid_cells_and_ignores_standing_agents():
    m, a = meter(3)
    base = np.array([[1.9, 1.9], [2.1, 2.1], [2.0, 0.0]])   # 体 0 と 1 は別の 2 m 格子で 0.28 m
    _step(m, a, 0, base)
    nxt = base + np.array([[0.0, 1.0], [0.3, 1.0], [0.0, 0.0]])  # 体 2 は動かない(変位 0)=歩行者に数えない
    _step(m, a, 1, nxt)
    s = m.summary()["instant_group_walk"]
    assert s["walker_minutes"] == 2 and s["grouped_walker_minutes"] == 2
    assert s["group_minutes_by_size"] == {"2": 1}


def test_group_norms_switch_off_is_byte_identical():
    """第309 Q150: ``group_norms="off"`` は計器の口を通さない=final・呼数が既定(on)と同じ・manifest は enabled=False。"""
    from shibuya import cli
    from shibuya.engine import run as RUN

    kw = dict(n_agents=150, seed=2, world_dir=None, n_cells=16, ticks=240, checkpoint_every=120)
    on = cli.run(**kw)
    off = cli.run(group_norms="off", **kw)
    assert (on.final_hash, on.llm_calls) == (off.final_hash, off.llm_calls)
    assert off.run_manifest_fields()["group_norms"] == {"enabled": False}
    g = on.run_manifest_fields()["group_norms"]
    assert g["enabled"] is True and "instant_group_walk" in g and "cowalk" in g
    assert "group_norms" not in off.phase_seconds and on.phase_seconds["group_norms"] >= 0.0
    with pytest.raises(ValueError):
        cli.run(group_norms="maybe", **kw)
    src = open(cli.__file__, encoding="utf-8").read()
    assert '"--group-norms"' in src and "group_norms=str(args.group_norms)" in src
    assert '"--group-norms"' in open(RUN.__file__, encoding="utf-8").read()
