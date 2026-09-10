"""ablation ①「チャネル固定枠 vs 同一総トークンの単一ランキング」(知覚契約書 §3.2 の**義務**)。

見るもの
(a) 既定は固定枠=**golden 不変**(テンプレ SHA 161fe181・参照場面の prompt_hash 釘付け)/
(b) 単一ランキングでも**群予算**(セル ≤250・個体 ≤300)に収まる/
(c) 固定枠が切る場面で**差が出る**(件数枠 B4.salient・トークン枠 B5.near_person)/
(d) §2.4 ⑧「同セル同時間帯の 2 体で B0-B4b バイト一致」が**両モードで**成り立つ/
(e) 決定論(2 回描いて同バイト)・共有静的(B0/B1/B3)は両モードで同一/
(f) 池の総額=固定枠の総和(§3.2「同一総トークン」)/
(g) ``run_day``/CLI のフラグと run manifest 欄/
(h) ``tools/c6/ablation1_fixed_vs_ranking.py`` を偽 vLLM で端から端まで(差 >0)。
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

from shibuya.agents.state import AgentKind, AgentState
from shibuya.engine.run import run_day
from shibuya.perception import channels as ch
from shibuya.perception import templates as T
from shibuya.perception.renderer import RANKING_PRIOR_SCORES, Renderer
from shibuya.world.state import World

REPO_ROOT = Path(__file__).resolve().parents[2]
SHARED_BLOCKS = ("B0", "B1", "B2", "B3", "B4", "B4b")
#: 参照場面(下の ``reference_scene``)の固定枠での指紋。**ablation ① で動いてはいけない**。
GOLDEN_FIXED_PROMPT_HASH = "bb23f7c69a82460b6820292404eb640b722ed0c7aa7a545afc9e09c697d8a5c5"


def reference_scene(mode, n: int = 12, n_cells: int = 9):
    """釘付け用の小さな合成場面(乱数の引き方まで固定)。"""
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
    r = Renderer(w, a, seed=13, budget_mode=mode)
    r.prepare_tick(750)
    return r, r.render(0, tick=750, wake_reason=3)


def crowded_scene(mode, n: int = 40, n_salient: int = 12):
    """固定枠が**件数でもトークンでも**切る場面(全員が同一セル・全員が知人)。"""
    w = World.synthetic(n_cells=9, seed=3)
    a = AgentState(n)
    g = np.random.default_rng(5)
    with a.writable():
        a.cell[:] = 0
        a.xy[:] = g.uniform(0.0, 60.0, size=(n, 2))
        a.kind[:] = AgentKind.VISITOR
        a.money[:] = 3_000
        a.hunger[:] = 9
        a.fatigue[:] = 8
        a.thermal[:] = 7
        a.last_result_tick[:] = 1
    w.cells.density[:] = w.compute_density(a.cell)
    r = Renderer(w, a, seed=7, budget_mode=mode, acquaintances={0: list(range(1, n))})
    r.prepare_tick(600, salient_events={0: tuple(f"誰かが倒れた({k})" for k in range(n_salient))})
    return r, r.render(0, tick=600, wake_reason=3)


def n_items(text: str, prefix: str) -> int:
    """``[B4 行為] 目につく出来事: a、b。`` のような列挙行の件数。"""
    for line in text.splitlines():
        if line.startswith(prefix):
            body = line.split(": ", 1)[1].rstrip("。") if ": " in line else ""
            return len([x for x in body.split("、") if x]) if body and body != "なし" else 0
    return 0


# ---------------------------------------------------------------- (a) 既定=固定枠
def test_default_mode_is_fixed_slots_and_the_golden_bytes_do_not_move():
    """既定は固定枠。参照場面のバイトもテンプレ SHA も ablation ① で動かない。"""
    r, out = reference_scene(ch.BudgetMode.FIXED_SLOTS)
    assert Renderer(r.world, r.agents).budget_mode is ch.BudgetMode.FIXED_SLOTS
    assert T.template_sha256().startswith("161fe181")
    assert out.prompt_hash == GOLDEN_FIXED_PROMPT_HASH
    _, default_out = reference_scene(ch.BudgetMode.FIXED_SLOTS.value)
    assert default_out.prompt_hash == GOLDEN_FIXED_PROMPT_HASH


def test_the_switch_is_not_a_no_op():
    """§3.2 の義務 ablation が**測定可能**であること(C6-b の no-op 報告の解消)。"""
    _, fixed = reference_scene("fixed")
    _, ranked = reference_scene("ranking")
    assert fixed.text != ranked.text
    assert fixed.prompt_hash != ranked.prompt_hash


# ---------------------------------------------------------------- (b) 群予算
@pytest.mark.parametrize("mode", ["fixed", "ranking"])
def test_group_budgets_hold_in_both_modes(mode):
    """§2.2 の実効ゲート(共有静的 ≤750・セル ≤250・個体 ≤300)。"""
    r, out = crowded_scene(mode)
    assert out.within_group_budgets(), dict(out.group_tokens)
    assert out.group_tokens["cell"] <= T.GROUP_TOKEN_BUDGET["cell"]
    assert out.group_tokens["individual"] <= T.GROUP_TOKEN_BUDGET["individual"]
    # 1 セルに 40 体・12 件の顕著行為でも例外にならない(strict_group_budget=True の既定)
    for i in range(0, 40, 7):
        assert r.render(i, tick=600, wake_reason=3).within_group_budgets()


def test_ranking_stays_within_budget_on_many_cells():
    """多数セル×多数個体を単一ランキングで描いても予算を破らない。"""
    w = World.synthetic(n_cells=16, seed=1)
    a = AgentState(200)
    g = np.random.default_rng(1)
    with a.writable():
        a.cell[:] = g.integers(0, 16, size=200)
        a.xy[:] = g.uniform(0.0, 100.0, size=(200, 2))
        a.kind[:] = AgentKind.VISITOR
        a.hunger[:] = g.integers(0, 11, size=200)
        a.fatigue[:] = g.integers(0, 11, size=200)
        a.thermal[:] = g.integers(0, 11, size=200)
        a.last_result_tick[:] = 1
    w.cells.density[:] = w.compute_density(a.cell)
    r = Renderer(w, a, seed=3, budget_mode="ranking")
    r.prepare_tick(760)
    for i in range(0, 200, 3):
        out = r.render(i, tick=760, wake_reason=3)
        assert out.within_group_budgets(), (i, dict(out.group_tokens))


# ---------------------------------------------------------------- (c) 差が出る場面
def test_ranking_keeps_what_the_fixed_slots_cut():
    """件数枠(B4.salient 上位2)とトークン枠(B5.near_person 100 tok)を外した差。"""
    _, fixed = crowded_scene("fixed")
    _, ranked = crowded_scene("ranking")
    n_sal_fixed = n_items(fixed.text, "[B4 行為]")
    n_sal_rank = n_items(ranked.text, "[B4 行為]")
    n_near_fixed = n_items(fixed.text, "[B5 近接]")
    n_near_rank = n_items(ranked.text, "[B5 近接]")
    assert n_sal_fixed == 2 and n_sal_rank > n_sal_fixed, (n_sal_fixed, n_sal_rank)
    assert n_near_rank > n_near_fixed, (n_near_fixed, n_near_rank)
    # 群予算は守ったまま(池は §2.2 の中でしか増えない)
    assert ranked.group_tokens["cell"] <= T.GROUP_TOKEN_BUDGET["cell"]
    assert ranked.group_tokens["individual"] <= T.GROUP_TOKEN_BUDGET["individual"]


def test_ranking_orders_near_persons_by_distance():
    """単一ランキングの順位は顕著性(視角=サイズ/距離)。近接人物は**近い順**になる。"""
    r, out = crowded_scene("ranking")
    line = [ln for ln in out.text.splitlines() if ln.startswith("[B5 近接]")][0]
    ids = [int(x.split("(")[0][2:]) for x in line.split(": ", 1)[1].rstrip("。").split("、")]
    xy = np.asarray(r.agents.xy, dtype=np.float64)
    d = [float(np.hypot(*(xy[j] - xy[0]))) for j in ids]
    assert d == sorted(d), d[:5]


# ---------------------------------------------------------------- (d) 規約⑧
@pytest.mark.parametrize("mode", ["fixed", "ranking"])
def test_rule8_same_cell_same_band_same_kind_is_byte_identical(mode):
    """§2.4 ⑧ は**両モードで**成り立つ(池の材料はセルの情報だけ=prefix を壊さない)。"""
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
    r = Renderer(w, a, seed=5, budget_mode=mode)
    r.prepare_tick(700, salient_events={0: ("誰かが倒れた", "客引きがいる", "行列ができた")})
    x, y = r.render(0, 700, 3), r.render(1, 700, 3)
    for b in SHARED_BLOCKS:
        assert x.blocks[b] == y.blocks[b], b
    assert x.shared_static_bytes() == y.shared_static_bytes()
    assert x.prefix_key == y.prefix_key


def test_shared_static_blocks_are_identical_across_arms():
    """共有静的(B0/B1/B3)は両腕で 1 バイトも変わらない(prefix キャッシュの土台)。"""
    _, fixed = crowded_scene("fixed")
    _, ranked = crowded_scene("ranking")
    for b in ("B0", "B1", "B3"):
        assert fixed.blocks[b] == ranked.blocks[b], b
    assert fixed.group_tokens["shared_static"] == ranked.group_tokens["shared_static"]


# ---------------------------------------------------------------- (e) 決定論
@pytest.mark.parametrize("mode", ["fixed", "ranking"])
def test_two_runs_give_the_same_bytes(mode):
    """同入力 → 同バイト(2 回組み直して比較)。"""
    _, a1 = crowded_scene(mode)
    _, a2 = crowded_scene(mode)
    assert a1.prompt_hash == a2.prompt_hash
    assert a1.text == a2.text
    assert dict(a1.block_hashes) == dict(a2.block_hashes)


def test_ranking_cache_returns_the_same_cell_bytes():
    """セル依存ブロックのキャッシュ(鍵=セル×B4 欄ハッシュ)が同じバイトを返す。"""
    r, first = crowded_scene("ranking")
    again = r.render(0, tick=600, wake_reason=3)
    assert first.blocks["B2"] == again.blocks["B2"]
    assert first.blocks["B4"] == again.blocks["B4"]
    assert r.cache_hits > 0


# ---------------------------------------------------------------- (f) 同一総トークン
def test_pool_budget_equals_the_fixed_slot_total():
    """§3.2「**同一総トークン**」= 池の総額はチャネル上限の総和と一致する。"""
    assert ch.pool_token_budget(("B2", "B4", "B4b")) == 250
    assert ch.pool_token_budget(("B5",)) == 220
    assert ch.pool_token_budget(("B2", "B4", "B4b")) == T.GROUP_TOKEN_BUDGET["cell"]
    assert (
        ch.pool_token_budget(("B5",)) + T.BLOCK_TOKEN_BUDGET["B6"]
        == T.GROUP_TOKEN_BUDGET["individual"]
    )
    assert set(ch.RANKING_POOL_BLOCKS) == {"cell", "individual"}


def test_take_within_pool_never_splits_a_line():
    n, used = ch.take_within_pool(["あ" * 20, "い" * 20, "う" * 20], 25)
    assert (n, used) == (2, 20)  # 1 行 10 tok・3 行目は入らないので打ち切る
    assert ch.take_within_pool([], 100) == (0, 0)


def test_budget_mode_parse_accepts_cli_words():
    assert ch.BudgetMode.parse("fixed") is ch.BudgetMode.FIXED_SLOTS
    assert ch.BudgetMode.parse("ranking") is ch.BudgetMode.SINGLE_RANKING
    assert ch.BudgetMode.parse("single_ranking") is ch.BudgetMode.SINGLE_RANKING
    assert ch.BudgetMode.parse(ch.BudgetMode.FIXED_SLOTS) is ch.BudgetMode.FIXED_SLOTS
    with pytest.raises(ValueError):
        ch.BudgetMode.parse("hybrid")


def test_every_channel_has_a_ranking_prior():
    """上限表の全チャネルに顕著性の既定素性がある(片方だけ増える事故の防止)。"""
    assert set(ch.RANKING_PRIORS) == {c.channel_id for c in ch.CHANNEL_LIMITS}
    assert set(RANKING_PRIOR_SCORES) == set(ch.RANKING_PRIORS)
    # 逸脱度つきの顕著行為は、根拠のない地物より上に来る(§4 段2 の順位規則)
    assert RANKING_PRIOR_SCORES["B4.salient"] > RANKING_PRIOR_SCORES["B2.landmark"]


# ---------------------------------------------------------------- (g) run_day / CLI / manifest
@pytest.mark.parametrize("mode,expected", [("fixed", "fixed_slots"), ("ranking", "single_ranking")])
def test_run_day_carries_the_arm_into_the_manifest(mode, expected):
    res = run_day(
        n_agents=64, seed=1, ticks=2, checkpoint_every=2, n_cells=9,
        processes=False, conversations=False, budget_mode=mode,
    )
    assert res.budget_mode == expected
    assert res.run_manifest_fields()["budget_mode"] == expected
    assert res.renderer_name == "perception.Renderer"


def test_run_day_defaults_to_fixed_slots():
    res = run_day(
        n_agents=32, seed=1, ticks=2, checkpoint_every=2, n_cells=9,
        processes=False, conversations=False,
    )
    assert res.run_manifest_fields()["budget_mode"] == "fixed_slots"


def test_cli_run_passes_the_arm_through_kwargs():
    from shibuya import cli

    res = cli.run(
        n_agents=32, seed=1, world_dir=None, n_cells=9, ticks=2, checkpoint_every=2,
        processes=False, conversations=False, budget_mode="ranking",
    )
    assert res.run_manifest_fields()["budget_mode"] == "single_ranking"


@pytest.mark.parametrize("argv,expected", [([], "fixed"), (["--budget-mode", "ranking"], "ranking")])
def test_cli_main_has_the_budget_mode_flag(monkeypatch, capsys, argv, expected):
    """``--budget-mode {fixed,ranking}``(既定 fixed)が ``run`` まで届く。"""
    from shibuya import cli

    seen: dict = {}

    class _Stub:
        fleet_fields: dict = {}

        def summary(self) -> str:
            return "(stub)"

    def fake_run(**kwargs):
        seen.update(kwargs)
        return _Stub()

    monkeypatch.setattr(cli, "run", fake_run)
    rc = cli.main(["--agents", "8", "--world", "__no_such_dir__", "--cells", "9", *argv])
    assert rc == 0 and capsys.readouterr().out.strip() == "(stub)"
    assert seen["budget_mode"] == expected


# ---------------------------------------------------------------- (h) ツールの端から端まで
def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def ab1_tool():
    tools_c6 = REPO_ROOT / "tools" / "c6"
    if str(tools_c6) not in sys.path:
        sys.path.insert(0, str(tools_c6))
    import ablation1_fixed_vs_ranking as mod

    return mod


def test_tool_probe_reports_that_the_switch_is_effective(ab1_tool):
    probe = ab1_tool.probe_switch(n_agents=16, n_cells=9, seed=1, n_scenes=6)
    assert probe["n_scenes"] == 6
    assert probe["n_different"] == 6
    assert probe["switch_effective"] and probe["note"] == ""


def test_tool_runs_end_to_end_against_a_fake_vllm(ab1_tool, tmp_path, capsys):
    """偽 vLLM 2 本に対して ``ablation1_fixed_vs_ranking.py`` を端から端まで回す。"""
    fake_mod = _load("_fake_vllm_ab1", REPO_ROOT / "tests" / "c6" / "_fake_vllm.py")
    fakes = [fake_mod.FakeVLLM(), fake_mod.FakeVLLM()]
    try:
        rc = ab1_tool.main(
            [
                "--endpoints", ",".join(f.endpoint for f in fakes),
                "--world", str(tmp_path / "no-world"),
                "--agents", "300",
                # D-56(就寝抑止)以降、最初の計画境界(tick 300-480)を跨ぐ窓が要る
                "--ticks", "400",
                "--seed", "1",
                "--out", str(tmp_path / "out"),
                "--tape-dir", str(tmp_path / "tapes"),
            ]
        )
    finally:
        for f in fakes:
            f.close()
    assert rc == 0
    payload = json.loads((tmp_path / "out" / "ablation1_fixed_vs_ranking.json").read_text("utf-8"))
    probe = payload["switch_probe"]
    with capsys.disabled():
        print(f"\n[ablation①] 描画差 {probe['n_different']}/{probe['n_scenes']} 場面・腕 {len(payload['arms'])}")
    assert probe["switch_effective"] and probe["n_different"] > 0
    assert len(payload["arms"]) == 2
    assert sum(a["llm_calls"] for a in payload["arms"]) > 0
    assert all(a["route"].startswith("cli.run(fleet=") for a in payload["arms"])
    md = (tmp_path / "out" / "ablation1_fixed_vs_ranking.md").read_text("utf-8")
    assert "**いいえ(no-op)**" not in md
