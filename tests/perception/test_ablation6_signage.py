"""ablation ⑥「広告ゼロ」(知覚契約書 §8 第1陣 ⑥)の切替口。

見るもの
(a) 既定は看板あり=**golden 不変**(テンプレ SHA 161fe181・参照場面の prompt_hash 釘付け)/
(b) ``signage_enabled=False`` で B2 看板行が ``B2.signage_empty`` になる(W14 凍結文でも合成文でも)/
(c) **固定枠と単一ランキングの両方**で効く(材料が ``_signage_body`` 1 本だから)/
(d) テンプレ本体・``template_sha256`` は不変(空文言は元からあるテンプレ)/
(e) 規約⑧(同セル同時間帯同種別で B0-B4b バイト一致)は腕を切っても成り立つ/
(f) 群予算は減る側にしか動かない/
(g) ``run_day``/``cli.run``/CLI ``--no-signage`` の往復と run manifest 欄。

**mock では行動は変わらない**(MockLLM はプロンプト本文を読まない=C6 実測)。この腕で
mock でも動くのは**描画バイトと入力トークン**だけ。腕の行動差は実 LLM でしか出ない。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.agents.state import AgentKind, AgentState
from shibuya.engine.run import run_day
from shibuya.perception import templates as T
from shibuya.perception.renderer import Renderer
from shibuya.world.state import World

SHARED_BLOCKS = ("B0", "B1", "B2", "B3", "B4", "B4b")
#: 看板ありの参照場面の指紋(``tests/perception/test_ablation1.py`` と**同じ場面・同じ値**)。
GOLDEN_FIXED_PROMPT_HASH = "bb23f7c69a82460b6820292404eb640b722ed0c7aa7a545afc9e09c697d8a5c5"
SIGNAGE_PREFIX = "[B2 看板]"


def scene(*, signage: bool = True, mode: str = "fixed", n: int = 12, n_cells: int = 9):
    """``test_ablation1.reference_scene`` と同じ合成場面(乱数の引き方まで同じ)。"""
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
    r = Renderer(w, a, seed=13, budget_mode=mode, signage_enabled=signage)
    r.prepare_tick(750)
    return r, r.render(0, tick=750, wake_reason=3)


def signage_line(text: str) -> str:
    return next(ln for ln in text.splitlines() if ln.startswith(SIGNAGE_PREFIX))


# ---------------------------------------------------------------- (a) 既定=看板あり
def test_default_is_signage_on_and_the_golden_bytes_do_not_move():
    """既定は看板あり。参照場面のバイトもテンプレ SHA も ⑥ の導入で動かない。"""
    r, out = scene()
    assert Renderer(r.world, r.agents).signage_enabled is True
    assert T.template_sha256().startswith("161fe181")
    assert out.prompt_hash == GOLDEN_FIXED_PROMPT_HASH


def test_the_switch_is_not_a_no_op():
    _, on = scene(signage=True)
    _, off = scene(signage=False)
    assert on.text != off.text
    assert on.prompt_hash != off.prompt_hash
    assert on.blocks["B2"] != off.blocks["B2"]


# ---------------------------------------------------------------- (b)(c) 空文言・両モード
@pytest.mark.parametrize("mode", ["fixed", "ranking"])
def test_signage_off_renders_the_empty_line_in_both_modes(mode):
    """看板行は「表示が無いセル」と**同じ描画**になる(テンプレは元からある空文言)。"""
    _, off = scene(signage=False, mode=mode)
    assert signage_line(off.text) == T.TEMPLATES["B2.signage_empty"]
    _, on = scene(signage=True, mode=mode)
    assert signage_line(on.text) != T.TEMPLATES["B2.signage_empty"]
    assert signage_line(on.text).startswith(T.TEMPLATES["B2.signage"].split("{")[0])


def test_every_cell_loses_its_signage_line():
    """1 セルだけでなく**全セル**で空になる(腕は「広告ゼロ」)。"""
    r, _ = scene(signage=False)
    for i in range(12):
        out = r.render(i, tick=750, wake_reason=3)
        assert signage_line(out.text) == T.TEMPLATES["B2.signage_empty"]


def test_signage_body_is_the_single_material_for_both_modes():
    """材料は ``_signage_body`` 1 本(固定枠=行・ランキング=候補列)。"""
    r_on, _ = scene(signage=True)
    r_off, _ = scene(signage=False)
    cells = [c for c in range(9) if r_on._signage_body(c) is not None]
    assert cells, "参照場面に看板のあるセルが 1 つも無い(場面の作り方を見直す)"
    for c in cells:
        assert r_off._signage_body(c) is None
        assert r_off._signage(c) == T.TEMPLATES["B2.signage_empty"]


# ---------------------------------------------------------------- (d) テンプレ不変
def test_templates_and_sha_are_untouched():
    """凍結テンプレの payload に 1 文字も足していない(v1.1 delta は不要)。"""
    assert T.template_sha256() == T.template_sha256()
    assert T.template_sha256().startswith("161fe181")
    assert "B2.signage" in T.TEMPLATES and "B2.signage_empty" in T.TEMPLATES


# ---------------------------------------------------------------- (e) 規約⑧
@pytest.mark.parametrize("signage", [True, False])
def test_rule8_holds_with_the_arm(signage):
    """§2.4 ⑧「同セル同時間帯の 2 体で B0-B4b バイト一致」は腕を切っても成り立つ。"""
    w = World.synthetic(n_cells=9, seed=4)
    a = AgentState(24)
    g = np.random.default_rng(2)
    with a.writable():
        a.cell[:] = 0
        a.xy[:] = g.uniform(0.0, 50.0, size=(24, 2))
        a.kind[:] = AgentKind.VISITOR
        a.money[:] = g.integers(0, 9_000, size=24)
        a.hunger[:] = g.integers(0, 11, size=24)
        a.last_result_tick[:] = 1
    w.cells.density[:] = w.compute_density(a.cell)
    r = Renderer(w, a, seed=5, signage_enabled=signage)
    r.prepare_tick(700)
    x, y = r.render(0, 700, 3), r.render(1, 700, 3)
    for b in SHARED_BLOCKS:
        assert x.blocks[b] == y.blocks[b], b
    assert x.prefix_key == y.prefix_key


# ---------------------------------------------------------------- (f) 群予算
def test_group_budget_only_shrinks():
    _, on = scene(signage=True)
    _, off = scene(signage=False)
    assert off.group_tokens["cell"] < on.group_tokens["cell"]
    assert off.group_tokens["shared_static"] == on.group_tokens["shared_static"]
    assert off.group_tokens["individual"] == on.group_tokens["individual"]
    assert off.within_group_budgets()


# ---------------------------------------------------------------- (g) run_day / cli / manifest
def _run(**kw):
    return run_day(
        n_agents=200, seed=1, ticks=30, checkpoint_every=30, n_cells=9,
        processes=False, conversations=False, **kw,
    )


def test_run_day_defaults_to_signage_on_and_is_byte_identical():
    base = _run()
    same = _run(signage=True)
    assert base.llm_calls > 0  # 呼が 0 だと「不変」が何も測れていない
    assert base.run_manifest_fields()["signage"] is True
    assert base.final_hash == same.final_hash
    assert base.renderer_counters["prompt_tokens_mean"] == same.renderer_counters["prompt_tokens_mean"]


def test_run_day_signage_off_changes_the_prompt_but_not_the_mock_actions():
    on, off = _run(signage=True), _run(signage=False)
    assert off.run_manifest_fields()["signage"] is False
    assert off.renderer_counters["tokens_cell_mean"] < on.renderer_counters["tokens_cell_mean"]
    # MockLLM は本文を読まない=行動(=checkpoint)は動かない。腕の差は実 LLM でしか出ない。
    assert off.final_hash == on.final_hash
    assert off.llm_calls == on.llm_calls


def test_cli_run_passes_signage_through_kwargs():
    from shibuya import cli

    res = cli.run(
        n_agents=32, seed=1, world_dir=None, n_cells=9, ticks=2, checkpoint_every=2,
        processes=False, conversations=False, signage=False,
    )
    assert res.run_manifest_fields()["signage"] is False


@pytest.mark.parametrize("argv,expected", [([], True), (["--no-signage"], False)])
def test_cli_main_has_the_no_signage_flag(monkeypatch, argv, expected):
    from shibuya import cli

    seen: dict = {}

    class _Stub:
        fleet_fields: dict = {}

        def summary(self) -> str:
            return "(stub)"

    monkeypatch.setattr(cli, "run", lambda **kw: (seen.update(kw), _Stub())[1])
    assert cli.main(["--agents", "8", "--world", "__no_such_dir__", "--cells", "9", *argv]) == 0
    assert seen["signage"] is expected
