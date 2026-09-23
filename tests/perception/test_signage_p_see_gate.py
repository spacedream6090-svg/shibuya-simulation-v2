"""看板(広告面)の**注視ゲート** ``signage_p_see``(知覚契約書 §4 段1 の p_see)。

出典と経緯
    D-59 (b)(ユーザー決定 2026-09-17)。ablation ⑥「広告ゼロ」の初回実測(5,000 体・実 LLM)で
    看板行を全消去すると 購入 −1.0〜−1.3 pp(seed 差の 6〜8 倍で再現)=**AD1(パターン台帳
    第3封印行 S3「広告全消去で絶対 1pp 未満」)を超える**=LLM の広告過剰反応の徴候。
    決定 (b)=「注意ゲートの較正(広告への注視確率を実測帯 0.14〜0.79 の下側へ)を 1 回」。
    腕は ``tools/c8`` の **AB6b-AD-NOTICE**(baseline 1.0 / ad_zero / 0.30 / 0.14)。

見るもの
(a) **既定 p_see=1.0 は 1 バイトも動かない**(golden prompt_hash・テンプレ SHA・抽選も引かない)/
(b) ``p_see=0.0`` で看板行が 0 件(=⑥「広告ゼロ」と同じ描画)/
(c) ``p_see=0.30`` で載る件数が二項分布の帯に入る(合成世界・n=2,000)/
(d) **決定論**: 同じ (seed, tick, 体, 看板) は常に同じ・2 回引いて同一・導出式を釘付け/
(e) run manifest に ``signage_p_see`` が出る(CLI ``--signage-p-see`` から往復する)/
(f) **落ちた看板の枠を他に回さない**(固定枠では他の行がバイト一致)/
(g) §2.4 ⑧ の扱い: p=1.0 では従来どおり成り立つ・p<1.0 では**体ごとに分かれる**が
    同セルの変種は**高々 2 つ**(看板あり/なし)=共有 prefix の断片化は高々 2 倍。

**mock では行動は変わらない**(MockLLM はプロンプト本文を読まない=C6 実測)。この切替口で
mock でも動くのは**描画バイトと入力トークン**だけ。腕の行動差は実 LLM でしか出ない。
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from shibuya.agents.state import AgentKind, AgentState
from shibuya.engine.run import run_day
from shibuya.perception import templates as T
from shibuya.perception.attention import P_SEE_MEDIUM_RANGE, gate_stage1
from shibuya.perception.renderer import (
    SIGNAGE_P_SEE_DEFAULT,
    Renderer,
    check_signage_p_see,
)
from shibuya.world.state import World

SHARED_BLOCKS = ("B0", "B1", "B2", "B3", "B4", "B4b")
#: 看板ありの参照場面の指紋(``tests/perception/test_ablation6_signage.py`` と**同じ値**)。
GOLDEN_FIXED_PROMPT_HASH = "bb23f7c69a82460b6820292404eb640b722ed0c7aa7a545afc9e09c697d8a5c5"
SIGNAGE_PREFIX = "[B2 看板]"
#: 腕が回す較正値(実測帯 0.14〜0.79 の下側)。
ARM_P_SEE = (0.30, 0.14)


def scene(*, p_see: float = SIGNAGE_P_SEE_DEFAULT, mode: str = "fixed", n: int = 12, n_cells: int = 9):
    """``test_ablation6_signage.scene`` と同じ合成場面(乱数の引き方まで同じ)。"""
    w = World.synthetic(n_cells=n_cells, seed=2)
    a = AgentState(n)
    g = np.random.default_rng(11)
    with a.writable():
        a.cell[:] = g.integers(0, n_cells, size=n)
        a.xy[:] = g.uniform(0.0, 80.0, size=(n, 2))
        a.kind[:] = AgentKind.VISITOR
        a.money[:] = 5_000
        a.hunger[:] = 6
        a.last_result_tick[:] = 1
    w.cells.density[:] = w.compute_density(a.cell)
    r = Renderer(w, a, seed=13, budget_mode=mode, signage_p_see=p_see)
    r.prepare_tick(750)
    return r, r.render(0, tick=750, wake_reason=3)


def signage_line(text: str) -> str:
    return next(ln for ln in text.splitlines() if ln.startswith(SIGNAGE_PREFIX))


def crowd(p_see: float, *, n: int = 100, n_cells: int = 9, seed: int = 13):
    """看板のあるセルへ全員を置いた場面(二項分布の検定用)。"""
    w = World.synthetic(n_cells=n_cells, seed=2)
    a = AgentState(n)
    g = np.random.default_rng(3)
    with a.writable():
        a.xy[:] = g.uniform(0.0, 80.0, size=(n, 2))
        a.kind[:] = AgentKind.VISITOR
        a.money[:] = 5_000
        a.hunger[:] = 6
        a.last_result_tick[:] = 1
    probe = Renderer(w, a, seed=seed)
    cell = next(c for c in range(n_cells) if probe._signage_body(c) is not None)
    with a.writable():
        a.cell[:] = cell
    w.cells.density[:] = w.compute_density(a.cell)
    return Renderer(w, a, seed=seed, signage_p_see=p_see), cell


# ---------------------------------------------------------------- (a) 既定不変
def test_the_default_is_one_and_the_golden_bytes_do_not_move():
    """既定 p_see=1.0。参照場面のバイトもテンプレ SHA も切替口の導入で動かない。"""
    r, out = scene()
    assert SIGNAGE_P_SEE_DEFAULT == 1.0
    assert Renderer(r.world, r.agents).signage_p_see == 1.0
    assert T.template_sha256().startswith("161fe181")
    assert out.prompt_hash == GOLDEN_FIXED_PROMPT_HASH


@pytest.mark.parametrize("mode", ["fixed", "ranking"])
def test_explicit_one_is_byte_identical_to_not_passing_it(mode):
    """``signage_p_see=1.0`` を明示しても描画は 1 バイトも変わらない(両モード)。"""
    base_r, base = scene(mode=mode)
    same_r, same = scene(p_see=1.0, mode=mode)
    assert same.text == base.text and same.prompt_hash == base.prompt_hash
    for b in T.BLOCK_IDS:
        assert same.blocks[b] == base.blocks[b], b
    # 既定では**抽選を 1 回も引かない**(乱数の消費が増えない=他の抽選も動かない)
    assert (base_r.signage_gate_draws, same_r.signage_gate_draws) == (0, 0)


def test_the_default_draws_nothing_even_where_there_is_signage():
    r, _ = crowd(1.0)
    for i in range(10):
        r.render(i, tick=700, wake_reason=3)
    assert r.signage_gate_draws == 0 and r.signage_gate_shown == 0


# ---------------------------------------------------------------- (b) p=0
@pytest.mark.parametrize("mode", ["fixed", "ranking"])
def test_zero_removes_every_signage_line(mode):
    """``p_see=0.0`` は全員・全 tick で看板行が空文言になる(=⑥ 広告ゼロと同じ描画)。"""
    r, _ = scene(p_see=0.0, mode=mode)
    for i in range(12):
        out = r.render(i, tick=750, wake_reason=3)
        assert signage_line(out.text) == T.TEMPLATES["B2.signage_empty"]


def test_zero_matches_the_ad_zero_arm_bytes():
    """``p_see=0.0`` の B2 は ⑥(``signage_enabled=False``)の B2 とバイト一致。"""
    w = World.synthetic(n_cells=9, seed=2)
    a = AgentState(12)
    g = np.random.default_rng(11)
    with a.writable():
        a.cell[:] = g.integers(0, 9, size=12)
        a.xy[:] = g.uniform(0.0, 80.0, size=(12, 2))
        a.kind[:] = AgentKind.VISITOR
        a.money[:] = 5_000
        a.hunger[:] = 6
        a.last_result_tick[:] = 1
    w.cells.density[:] = w.compute_density(a.cell)
    gated = Renderer(w, a, seed=13, signage_p_see=0.0)
    zeroed = Renderer(w, a, seed=13, signage_enabled=False)
    gated.prepare_tick(750)
    zeroed.prepare_tick(750)
    for i in range(12):
        assert gated.render(i, 750, 3).blocks["B2"] == zeroed.render(i, 750, 3).blocks["B2"]


def test_zero_is_not_a_no_op():
    _, on = scene(p_see=1.0)
    _, off = scene(p_see=0.0)
    assert on.blocks["B2"] != off.blocks["B2"]
    assert on.prompt_hash != off.prompt_hash


# ---------------------------------------------------------------- (c) 二項分布の帯
@pytest.mark.parametrize("p", [0.30, 0.14])
def test_the_realised_rate_is_inside_the_binomial_band(p):
    """n=2,000 の描画で「看板が載った回数」が二項分布 ±4σ に入る(合成世界)。

    ±4σ は**片側 3×10⁻⁵ の帯**(seed を選ばずに固定できる幅)。分母は
    ``signage_gate_draws``(看板のあるセルでの抽選回数)= 2,000 ちょうど。
    """
    n_agents, ticks = 100, 20
    r, _cell = crowd(p, n=n_agents)
    shown = 0
    for t in range(700, 700 + ticks):
        for i in range(n_agents):
            if signage_line(r.render(i, tick=t, wake_reason=3).text) != T.TEMPLATES["B2.signage_empty"]:
                shown += 1
    n = n_agents * ticks
    assert r.signage_gate_draws == n
    assert r.signage_gate_shown == shown
    sd = math.sqrt(n * p * (1.0 - p))
    assert abs(shown - n * p) <= 4.0 * sd, (shown, n * p, sd)


def test_the_gate_is_independent_across_ticks_and_agents():
    """同じ体でも tick が違えば別の抽選・同じ tick でも体が違えば別の抽選。"""
    r, cell = crowd(0.30, n=40)
    by_tick = [r._signage_seen(0, cell, t) for t in range(700, 740)]
    by_agent = [r._signage_seen(i, cell, 700) for i in range(40)]
    assert len(set(by_tick)) == 2, "同一体の 40 tick が全部同じ=tick が効いていない"
    assert len(set(by_agent)) == 2, "同一 tick の 40 体が全部同じ=体が効いていない"


# ---------------------------------------------------------------- (d) 決定論
def test_two_renderers_with_the_same_seed_agree():
    """同じ seed・同じ場面を 2 回作ると**同じ体が同じ tick で同じ結果**になる。"""
    a_r, cell = crowd(0.30, n=30)
    b_r, _ = crowd(0.30, n=30)
    pairs = [(i, t) for i in range(30) for t in (700, 701, 702)]
    assert [a_r._signage_seen(i, cell, t) for i, t in pairs] == [
        b_r._signage_seen(i, cell, t) for i, t in pairs
    ]


def test_the_seed_changes_the_draw():
    a_r, cell = crowd(0.30, n=30, seed=13)
    b_r, _ = crowd(0.30, n=30, seed=14)
    x = [a_r._signage_seen(i, cell, 700) for i in range(30)]
    y = [b_r._signage_seen(i, cell, 700) for i in range(30)]
    assert x != y, "seed を変えても同じ=seed が鍵に入っていない"


def test_the_derivation_is_pinned_to_gate_stage1():
    """**導出式の釘付け**: ``gate_stage1(1, p, seed=seed, counters=(tick, agent, poi))``。

    ドメインは ``perception.attention.p_see``(``core.rng`` の Philox4x64)。テープの
    ``(seed, tick, agent_id, poi_id)`` だけから同じ真偽値を再現できる=**再生可能**。
    """
    r, cell = crowd(0.30, n=8)
    poi = r._signage_poi(cell)
    assert poi >= 0
    for i in range(8):
        for t in (700, 701):
            want = bool(gate_stage1(1, 0.30, seed=13, domain_counters=(t, i, poi))[0])
            assert r._signage_seen(i, cell, t) is want, (i, t)


def test_no_lottery_where_there_is_no_signage():
    """看板の無いところでは抽選を引かない(乱数を無駄に消費しない)。

    合成世界は**全セルに可視 POI がある**ので、「看板が無い」は (i) 世界の外のセル と
    (ii) ⑥ 広告ゼロ(``signage_enabled=False``)を重ねた場合の 2 つで作る。
    """
    r, _cell = crowd(0.30, n=6)
    assert r._signage_poi(-1) == -1 and r._signage_poi(10_000) == -1
    assert r._signage_seen(0, -1, 700) is True
    assert r.signage_gate_draws == 0

    zero = Renderer(r.world, r.agents, seed=13, signage_enabled=False, signage_p_see=0.30)
    zero.prepare_tick(700)
    for i in range(6):
        out = zero.render(i, tick=700, wake_reason=3)
        assert signage_line(out.text) == T.TEMPLATES["B2.signage_empty"]
    assert zero.signage_gate_draws == 0


# ---------------------------------------------------------------- (f) 枠を他に回さない
def test_the_freed_slot_is_not_given_to_another_channel():
    """固定枠では、落ちた看板行の**枠を他へ回さない**(他の行はバイト一致・群予算は減る)。"""
    r, cell = crowd(0.30, n=60)
    on = off = None
    for i in range(60):
        out = r.render(i, tick=700, wake_reason=3)
        if signage_line(out.text) == T.TEMPLATES["B2.signage_empty"]:
            off = off or out
        else:
            on = on or out
        if on is not None and off is not None:
            break
    assert on is not None and off is not None, "60 体で両方の腕が出ない=場面を見直す"
    lines_on = [ln for ln in on.blocks["B2"].decode("utf-8").splitlines()]
    lines_off = [ln for ln in off.blocks["B2"].decode("utf-8").splitlines()]
    assert len(lines_on) == len(lines_off)
    for x, y in zip(lines_on, lines_off):
        if x.startswith(SIGNAGE_PREFIX):
            assert y == T.TEMPLATES["B2.signage_empty"]
        else:
            assert x == y, "看板以外の行が動いた=枠が再配分されている"
    assert off.group_tokens["cell"] < on.group_tokens["cell"]
    assert off.within_group_budgets()


# ---------------------------------------------------------------- (g) 規約⑧ の扱い
def test_rule8_still_holds_at_p_see_one():
    """p=1.0 では §2.4 ⑧「同セル同時間帯の 2 体で B0-B4b バイト一致」は従来どおり。"""
    r, _ = crowd(1.0, n=24)
    x, y = r.render(0, 700, 3), r.render(1, 700, 3)
    for b in SHARED_BLOCKS:
        assert x.blocks[b] == y.blocks[b], b
    assert x.prefix_key == y.prefix_key


def test_the_gate_splits_the_shared_prefix_into_at_most_two_variants():
    """p<1.0 では ⑧ が**体ごとに分かれる**が、同セルの変種は看板あり/なしの高々 2 つ。"""
    r, _ = crowd(0.30, n=60)
    keys = {r.render(i, 700, 3).prefix_key for i in range(60)}
    assert 1 <= len(keys) <= 2, keys
    b2 = {r.render(i, 700, 3).blocks["B2"] for i in range(60)}
    assert len(b2) == len(keys)


# ---------------------------------------------------------------- 入力の検査
@pytest.mark.parametrize("bad", [-0.01, 1.01, 2.0, float("nan")])
def test_out_of_range_is_refused(bad):
    with pytest.raises(ValueError):
        check_signage_p_see(bad)
    with pytest.raises(ValueError):
        Renderer(World.synthetic(n_cells=9, seed=1), AgentState(2), signage_p_see=bad)


def test_the_arm_values_sit_inside_the_declared_band():
    """腕の 0.30 / 0.14 は §4 段1 の帯の下側(0.14=中小媒体の帯の下端そのもの)。"""
    assert ARM_P_SEE[1] == P_SEE_MEDIUM_RANGE[0]
    for p in ARM_P_SEE:
        assert P_SEE_MEDIUM_RANGE[0] <= p <= P_SEE_MEDIUM_RANGE[1]
        assert check_signage_p_see(p) == p


# ---------------------------------------------------------------- (e) run_day / cli / manifest
def _run(**kw):
    # ticks: D-56(就寝抑止)以降、tick 0 は世界内 00:00 で全員 ``SLEEPING`` なので、
    # 最初の計画境界(合成日課の起床 tick 300-480)を跨ぐ窓にする。
    return run_day(
        n_agents=200, seed=1, ticks=540, checkpoint_every=540, n_cells=9,
        processes=False, conversations=False, **kw,
    )


def test_run_day_defaults_to_one_and_is_byte_identical():
    base = _run()
    same = _run(signage_p_see=1.0)
    assert base.llm_calls > 0  # 呼が 0 だと「不変」が何も測れていない
    assert base.run_manifest_fields()["signage_p_see"] == 1.0
    assert base.final_hash == same.final_hash
    assert base.renderer_counters == same.renderer_counters
    # 既定の診断行には注視ゲートの欄が 1 つも増えない
    assert not any(k.startswith("signage_") for k in base.renderer_counters)


def test_run_day_carries_the_gate_into_the_manifest_and_counters():
    res = _run(signage_p_see=0.30)
    fields = res.run_manifest_fields()
    assert fields["signage_p_see"] == 0.30
    assert fields["signage"] is True  # ⑥ とは別の切替口(広告はまだ在る)
    rc = res.renderer_counters
    assert rc["signage_p_see"] == 0.30
    assert rc["signage_gate_draws"] > 0
    assert 0.0 < rc["signage_shown_rate"] < 1.0
    assert rc["tokens_cell_mean"] < _run().renderer_counters["tokens_cell_mean"]
    # MockLLM は本文を読まない=行動(=checkpoint)は動かない。腕の差は実 LLM でしか出ない。
    assert res.final_hash == _run().final_hash


def test_run_day_refuses_a_bad_probability():
    with pytest.raises(ValueError):
        run_day(
            n_agents=8, seed=1, ticks=1, checkpoint_every=1, n_cells=9,
            processes=False, conversations=False, signage_p_see=1.5,
        )


def test_cli_run_passes_the_gate_through_kwargs():
    from shibuya import cli

    res = cli.run(
        n_agents=32, seed=1, world_dir=None, n_cells=9, ticks=2, checkpoint_every=2,
        processes=False, conversations=False, signage_p_see=0.14,
    )
    assert res.run_manifest_fields()["signage_p_see"] == 0.14


@pytest.mark.parametrize(
    "argv,expected",
    [([], 1.0), (["--signage-p-see", "0.30"], 0.30), (["--signage-p-see", "0.14"], 0.14)],
)
def test_cli_main_has_the_flag(monkeypatch, argv, expected):
    from shibuya import cli

    seen: dict = {}

    class _Stub:
        fleet_fields: dict = {}

        def summary(self) -> str:
            return "(stub)"

    monkeypatch.setattr(cli, "run", lambda **kw: (seen.update(kw), _Stub())[1])
    assert cli.main(["--agents", "8", "--world", "__no_such_dir__", "--cells", "9", *argv]) == 0
    assert seen["signage_p_see"] == expected


def test_cli_main_rejects_a_bad_probability():
    from shibuya import cli

    with pytest.raises(SystemExit):
        cli.main(["--agents", "8", "--world", "__no_such_dir__", "--cells", "9",
                  "--signage-p-see", "1.5"])
