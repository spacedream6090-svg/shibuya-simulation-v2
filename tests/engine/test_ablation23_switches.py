"""ablation ②「p_notice の d50 を 0.5×/2×」・③「近接入替の不応期 15 分 ±50%」の切替口。

正典: 知覚契約書 **§8 第1陣 ②③**・**§3.1**(TTPF 2 段ヒル型・d50 40 m・打ち切り 80 m・A0-A4)・
**§6 不応期表**(11 行・近接入替 15 分=expedient「最大の暴発源」)。

見るもの
② (a) 既定 1.0 でバイト不変(checkpoint・呼数・診断行)/(b) d50 を振ると**気づいた人数=
   起床候補**が単調に動く(A0 を除く全 ablation 段で)/(c) 事象クラス別の表も同じ倍率で動く/
   (d) A0-A4 と**併用できる**/(e) 正でない倍率は例外/(f) run_day・cli・manifest の往復。
③ (a) 既定 None で §6 の表そのもの(**同じ配列を返す**=バイト不変)/(b) 倍率で実効表が動く
   (7.5→8 分・22.5→23 分の half-up)/(c) ``set_refractory`` がランの表を使う/
   (d) run_day に通すと起床(=checkpoint)が動く/(e) 鍵は名前・列番号・enum のどれでも/
   (f) 未知の条件・負の倍率は例外/(g) run_day・cli・manifest の往復。

**測れる範囲の記録(親への報告事項)**
- ② 合成世界では個体が街路ノード=セル中心に固まるので、事象までの距離が 0 か 100 m
  (打ち切り 80 m の外)しかない → **d50 を振っても何も動かない**。差が出るのは xy に
  広がりがある実資産か、本ファイルのように座標を並べた場面。
- ③ ``PROXIMITY_SWAP`` を起床候補に出すコードは**まだ無い**(``change_detect`` が出すのは
  ``INTEROCEPTION`` と ``CELL_BLOCK`` だけ・近接入替は §9 第2陣)。よって腕そのものは
  現状 no-op で、ここでは**切替口が効くこと**を ``CELL_BLOCK`` で示し、``PROXIMITY_SWAP``
  については**実効表が正しく動くこと**までを釘付けする。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.agents.schedule import synthesize
from shibuya.agents.state import REFRACTORY_MINUTES, AgentState, WakeCondition
from shibuya.engine import resolve as R
from shibuya.engine.arbiter import REFRACTORY_TICKS as ARBITER_MIRROR
from shibuya.engine.processes.salient import D50_BY_KIND, SalientProcess, ablation_name
from shibuya.engine.run import run_day
from shibuya.perception import p_notice as PN
from shibuya.world.state import World

PROX = int(WakeCondition.PROXIMITY_SWAP)


# ================================================================= ② p_notice d50
def spread_scene(scale: float, ablation="A4", *, n: int = 120, ticks: int = 240):
    """1 セルに個体を **0-79 m の直線上に並べた**場面(距離が効く唯一の合成場面)。"""
    world = World.synthetic(n_cells=25, seed=1)
    agents = AgentState(n)
    R.initialize(agents, world, synthesize(n, 1, world.n_cells))
    with agents.writable():
        agents.registry.cell[:] = 12
        base = np.asarray(world.assets.node_xy)[int(agents.registry.node[0])]
        agents.registry.xy[:, 0] = base[0] + np.linspace(0.0, 79.0, n)
        agents.registry.xy[:, 1] = base[1]
    agents.freeze()
    world.freeze()
    sp = SalientProcess(
        world, agents, master_seed=1, rate_per_10k_per_day=5_000.0,
        ablation=ablation, d50_scale=scale,
    )
    for t in range(ticks):
        sp.step(t)
    return sp


def test_d50_default_is_the_section31_table():
    sp = spread_scene(1.0)
    assert sp.d50_scale == 1.0
    assert sp.params.d50_m == PN.D50_DEFAULT_M == 40.0
    assert sp.d50_by_kind == D50_BY_KIND
    assert sp.counters()["d50_scale"] == 1.0


def test_d50_scale_multiplies_both_the_default_and_the_per_kind_table():
    """§3.1 の既定 40 m と ``D50_BY_KIND``(事象クラス別)を**同じ倍率**で振る。"""
    sp = spread_scene(0.5)
    assert sp.params.d50_m == 20.0
    assert sp.d50_by_kind == {"collapse": 20.0, "police": 22.5, "broadcast": 30.0}
    assert spread_scene(2.0).d50_by_kind["collapse"] == 80.0


@pytest.mark.parametrize("ablation", ["A1", "A2", "A3", "A4"])
def test_reach_grows_with_d50_at_every_ablation_step(ablation):
    """0.5× < 1.0× < 2.0×(=情報到達半径。§8 ② の指標)。同じ事象・同じ候補で比べる。"""
    got = [spread_scene(s, ablation) for s in (0.5, 1.0, 2.0)]
    assert len({sp.n_events for sp in got}) == 1, "事象の引きが腕で変わってはいけない"
    reach = [sp.n_noticed for sp in got]
    assert reach[0] < reach[1] < reach[2], (ablation, reach)


def test_a0_is_a_constant_and_ignores_d50():
    """A0(定数 0.54)は距離を見ない=d50 を振っても到達は動かない(§3.1)。"""
    assert [spread_scene(s, "A0").n_noticed for s in (0.5, 2.0)] == [
        spread_scene(1.0, "A0").n_noticed
    ] * 2


def test_wake_candidates_follow_the_reach():
    """起床候補 (i) は ``noticed_agents`` そのもの=腕は起床数に出る。"""
    small, big = spread_scene(0.5), spread_scene(2.0)
    a_s, _, _ = small.wake_candidates(239)
    a_b, _, _ = big.wake_candidates(239)
    assert small.noticed_agents.size == a_s.size
    assert big.noticed_agents.size == a_b.size


@pytest.mark.parametrize("bad", [0.0, -1.0, float("nan"), float("inf")])
def test_bad_d50_scale_is_refused(bad):
    with pytest.raises(ValueError):
        spread_scene(bad, ticks=1)


def test_ablation_name_normalizes_every_form():
    assert ablation_name("A2") == "A2"
    assert ablation_name("AB-PNOTICE-A0") == "A0"
    assert ablation_name(3) == "A3"
    assert ablation_name(PN.Ablation.A4_SOCIAL) == "A4"


# ================================================================= ③ 不応期表
def test_default_table_is_the_section6_table_object():
    """既定は §6 の表**そのもの**(新しい配列すら作らない=バイト不変の担保)。"""
    assert R.refractory_ticks() is R.refractory_ticks(None)
    assert R.refractory_ticks({}) is R.refractory_ticks(None)
    assert R.refractory_ticks(None).tolist() == list(REFRACTORY_MINUTES)
    assert ARBITER_MIRROR.tolist() == list(REFRACTORY_MINUTES)  # 写しがずれていない


def test_scaled_table_rounds_half_up():
    """15 分 ×0.5 = 7.5 → **8 分**・×1.5 = 22.5 → **23 分**(自前規約・§8 に丸めの規定なし)。"""
    half = R.refractory_ticks({"PROXIMITY_SWAP": 0.5})
    one_and_half = R.refractory_ticks({"PROXIMITY_SWAP": 1.5})
    assert half[PROX] == 8 and one_and_half[PROX] == 23
    # 触っていない 10 行は 1 分も動かない
    for c in range(len(REFRACTORY_MINUTES)):
        if c != PROX:
            assert half[c] == one_and_half[c] == REFRACTORY_MINUTES[c]


def test_key_forms_and_zero_factor():
    for key in ("PROXIMITY_SWAP", "proximity-swap", PROX, WakeCondition.PROXIMITY_SWAP):
        assert R.refractory_ticks({key: 0.5})[PROX] == 8
    assert R.refractory_ticks({"CELL_BLOCK": 0.0})[int(WakeCondition.CELL_BLOCK)] == 0


@pytest.mark.parametrize(
    "scale", [{"NOPE": 1.0}, {99: 1.0}, {"PROXIMITY_SWAP": -0.5}, {"PROXIMITY_SWAP": float("nan")}]
)
def test_bad_scale_is_refused(scale):
    with pytest.raises(ValueError):
        R.refractory_ticks(scale)


def test_normalized_scale_is_the_manifest_form():
    assert R.normalized_refractory_scale({PROX: 0.5}) == {"PROXIMITY_SWAP": 0.5}
    assert R.normalized_refractory_scale(None) == {}
    # 名前昇順(manifest の欄が seed 依存の順にならない)
    got = R.normalized_refractory_scale({"cell_block": 2, "PROXIMITY_SWAP": 0.5})
    assert list(got) == ["CELL_BLOCK", "PROXIMITY_SWAP"]


def test_set_refractory_uses_the_run_table():
    """``set_refractory`` は渡された実効表でタイマーを張る(既定は §6 の表)。"""
    a = AgentState(4)
    R.set_refractory(a, [0], [PROX], tick=5)
    assert int(a.registry.refractory_until[0, PROX]) == 5 + REFRACTORY_MINUTES[PROX]
    a2 = AgentState(4)
    R.set_refractory(a2, [0], [PROX], tick=5, table=R.refractory_ticks({PROX: 0.5}))
    assert int(a2.registry.refractory_until[0, PROX]) == 5 + 8


def test_set_refractory_refuses_a_wrong_shaped_table():
    a = AgentState(2)
    with pytest.raises(ValueError):
        R.set_refractory(a, [0], [PROX], tick=0, table=np.zeros(3, dtype=np.int32))


# ================================================================= run_day / cli / manifest
def _run(**kw):
    # ticks: D-56(就寝抑止)以降、tick 0 は世界内 00:00 で全員 ``SLEEPING`` なので
    # 最初の計画境界(合成日課の「起床」= tick 300-480)を跨ぐ窓にしないと呼が 0 になる。
    return run_day(
        n_agents=800, seed=2, ticks=540, checkpoint_every=540, n_cells=25,
        processes=False, conversations=True, **kw,
    )


def test_defaults_are_byte_identical():
    """既定値を明示的に渡しても checkpoint・呼数・診断行が 1 ビットも動かない。"""
    base = _run()
    same = _run(p_notice_d50_scale=1.0, refractory_scale=None, signage=True)
    assert base.llm_calls > 0
    assert base.final_hash == same.final_hash
    assert base.llm_calls == same.llm_calls
    assert base.diagnostics_day() == same.diagnostics_day()


def test_refractory_scale_moves_the_run():
    """**起床規則はエンジン側**なので mock でも動く(§8 ③ が mock で測れる根拠)。

    振る条件が ``CELL_BLOCK`` から ``INTEROCEPTION`` に変わったのは **D-56(就寝抑止)**の
    副作用。寝ている個体は動かないのでセル動的ブロックがほとんど変化せず、この合成
    fixture(800体・25セル・過程なし)では ``CELL`` クラスの候補が 0 件になり、
    ``CELL_BLOCK`` の不応期を振っても 1 ビットも動かない(D-49 の「第2陣まで no-op」に
    ``CELL_BLOCK`` も並んだ=親へ報告済み)。``INTEROCEPTION``/``PLAN_*`` は動く。
    """
    base = _run()
    short = _run(refractory_scale={"INTEROCEPTION": 0.5})
    assert short.final_hash != base.final_hash
    assert short.run_manifest_fields()["refractory_scale"] == {"INTEROCEPTION": 0.5}


def test_proximity_swap_arm_is_a_no_op_until_the_second_wave():
    """③ の腕(近接入替 ±50%)は**起床候補を出す側がまだ無い**ので現状 no-op。

    切替口の欠陥ではない(``INTEROCEPTION`` では動く)。近接入替の起床が §9 第2陣で入った
    日に、このテストが**落ちて**気づけるようにしておく。
    """
    base = _run()
    for factor in (0.5, 1.5):
        got = _run(refractory_scale={"PROXIMITY_SWAP": factor})
        assert got.final_hash == base.final_hash
        assert got.run_manifest_fields()["refractory_scale"] == {"PROXIMITY_SWAP": factor}


def test_manifest_carries_the_first_wave_arms():
    res = _run(p_notice_d50_scale=2.0, refractory_scale={PROX: 0.5}, signage=False)
    f = res.run_manifest_fields()
    assert f["p_notice_d50_scale"] == 2.0
    assert f["refractory_scale"] == {"PROXIMITY_SWAP": 0.5}
    assert f["signage"] is False
    assert f["p_notice_ablation"] == "A4"
    base = _run().run_manifest_fields()
    assert (base["p_notice_d50_scale"], base["refractory_scale"], base["signage"]) == (1.0, {}, True)


def test_d50_scale_reaches_the_salient_process_through_run_day():
    res = run_day(
        n_agents=300, seed=3, ticks=30, checkpoint_every=30, n_cells=25,
        processes=True, conversations=False, salient_rate_per_10k=4_000.0,
        p_notice_d50_scale=0.5, p_notice_ablation="A1",
    )
    assert res.runner.salient.d50_scale == 0.5
    assert res.runner.salient.params.d50_m == 20.0
    assert res.process_counters["salient.d50_scale"] == 0.5
    assert res.run_manifest_fields()["p_notice_ablation"] == "A1"


def test_run_day_checks_the_arm_even_without_processes():
    """過程を切ったランでも腕の値を検査する(manifest が嘘の値を持たない)。"""
    with pytest.raises(ValueError):
        run_day(
            n_agents=8, seed=1, ticks=1, checkpoint_every=1, n_cells=9,
            processes=False, conversations=False, p_notice_d50_scale=0.0,
        )
    with pytest.raises(ValueError):
        run_day(
            n_agents=8, seed=1, ticks=1, checkpoint_every=1, n_cells=9,
            processes=False, conversations=False, refractory_scale={"NOPE": 1.0},
        )


def test_cli_run_passes_both_arms_through_kwargs():
    from shibuya import cli

    res = cli.run(
        n_agents=64, seed=1, world_dir=None, n_cells=9, ticks=2, checkpoint_every=2,
        processes=False, conversations=False,
        p_notice_d50_scale=0.5, refractory_scale={"PROXIMITY_SWAP": 0.5},
    )
    f = res.run_manifest_fields()
    assert f["p_notice_d50_scale"] == 0.5
    assert f["refractory_scale"] == {"PROXIMITY_SWAP": 0.5}


def test_cli_parse_refractory_scale():
    from shibuya import cli

    assert cli.parse_refractory_scale([]) == {}
    assert cli.parse_refractory_scale(["PROXIMITY_SWAP=0.5", "cell-block=2"]) == {
        "PROXIMITY_SWAP": 0.5, "CELL_BLOCK": 2.0
    }
    assert cli.parse_refractory_scale(["PROXIMITY_SWAP=0.5", "PROXIMITY_SWAP=2"]) == {
        "PROXIMITY_SWAP": 2.0
    }
    for bad in (["PROXIMITY_SWAP"], ["PROXIMITY_SWAP=x"], ["NOPE=1"]):
        with pytest.raises(Exception):
            cli.parse_refractory_scale(bad)


@pytest.mark.parametrize(
    "argv,d50,scale",
    [
        ([], 1.0, None),
        (["--pnotice-d50-scale", "0.5"], 0.5, None),
        (["--p-notice-d50-scale", "2"], 2.0, None),
        (["--refractory-scale", "PROXIMITY_SWAP=1.5"], 1.0, {"PROXIMITY_SWAP": 1.5}),
        (
            ["--refractory-scale", "PROXIMITY_SWAP=0.5", "--refractory-scale", "CELL_BLOCK=2"],
            1.0,
            {"PROXIMITY_SWAP": 0.5, "CELL_BLOCK": 2.0},
        ),
    ],
)
def test_cli_main_flags(monkeypatch, argv, d50, scale):
    from shibuya import cli

    seen: dict = {}

    class _Stub:
        fleet_fields: dict = {}

        def summary(self) -> str:
            return "(stub)"

    monkeypatch.setattr(cli, "run", lambda **kw: (seen.update(kw), _Stub())[1])
    assert cli.main(["--agents", "8", "--world", "__no_such_dir__", "--cells", "9", *argv]) == 0
    assert seen["p_notice_d50_scale"] == d50
    assert seen["refractory_scale"] == scale


@pytest.mark.parametrize(
    "argv",
    [["--refractory-scale", "NOPE=1"], ["--refractory-scale", "x"], ["--pnotice-d50-scale", "-1"]],
)
def test_cli_main_rejects_bad_arms(argv):
    """使い方の誤りは traceback ではなく usage(exit 2)で返す。"""
    from shibuya import cli

    with pytest.raises(SystemExit) as got:
        cli.main(["--agents", "8", "--world", "__no_such_dir__", "--cells", "9", *argv])
    assert got.value.code == 2
