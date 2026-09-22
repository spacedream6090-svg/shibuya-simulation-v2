"""腕 ``AB8-L4-SCALE`` / ``AB6c-AD-NOTICE-UNCAPPED`` と**実現量**の欄 — 2026-09-19。

出典
    PENDING **D-99 (a)**(2026-09-18)「L4 の感度腕」+ PENDING **D-59** 第245 ユーザー指示
    (2026-09-19)「呼数制限なしで看板の腕を再検証」+ 予算宣言表 **L4**(上限 400 万呼/日・
    40 万体基準=平均 10 呼/体/日が繰り延べアービタの制御目標)。

見るもの
(t2) 変換規則 ``倍率>0 → call_budget_per_tick(n)×倍率`` / ``0 → float(n)``(**無制限**)/
(t3) **変異検出**: 既定と ``l4_scale=1.0`` は final_hash が一致し、0.5 / 0 では
     繰り延べ・抑止・呼数が動く(mock でも動く=予算はエンジン側の量)/
(t4) ``run_metrics`` が ``realized`` / ``realized_per_agent_day`` / ``l4_scale`` /
     ``budget_per_tick`` を出し、**既存の欄の値は 1 つも動かない**/
(t5) 腕定義表の末尾に 2 本が足され、**既存 10 腕(AB6b を含む)の定義はバイト不変**。

``l4_scale=0`` を「無制限」と書ける根拠(``src/shibuya/engine/arbiter.py``)
    ``arbitrate`` は ⑤ の予算配分より**前**に ③ 同一体の合流を通す。合流は
    ``first[1:] = sorted_agent[1:] != sorted_agent[:-1]`` で体ごとの先頭 1 件だけを残すので、
    ⑤ に入る ``agent.size`` は**体数を超えない**。⑤ は
    ``n_sel = min(コスト基準, floor(budget), agent.size)`` なので ``budget = n_agents`` なら
    常に全件が選ばれる(``inf`` は ``Arbiter._pool_cap`` と ``int(np.floor(...))`` を壊すので
    使わない)。下の ``test_zero_defers_nothing`` がこの含意を実測で押さえる。
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

import pytest

from shibuya.engine.arbiter import call_budget_per_tick

ARM_ID = "AB8-L4-SCALE"
#: ⑥b を呼数制限なしで回し直す腕(第245 ユーザー指示)。
ARM_UNCAPPED_ID = "AB6c-AD-NOTICE-UNCAPPED"

#: AB6b(看板の注視ゲート)の腕定義の凍結 SHA256。**2026-09-19 に末尾でなくなったので凍らせる**
#: (第1陣 6 本〜AB7c の 9 本は ``tests/c8/test_ablations_ab7.py`` の FROZEN_ARM_SHA256 が持つ)。
FROZEN_AB6B_SHA256 = "1be4e00f74c52ab82e3ff15474815a71ac6f9b95319155c3819c9bf6972f4976"

#: 変異検出用の極小ラン。**就寝抑止を切る**=合成世界の 0 時台でも起床候補が立つ
#: (既定の D-56 抑止が効くと候補が 0 件になり、予算の腕が何も動かさない)。
MUTATION_RUN = dict(
    n_agents=200, seed=1, world_dir=None, n_cells=20, ticks=24, checkpoint_every=24,
    sleep_suppression=False,
)


@pytest.fixture(scope="module")
def table(c8lib):
    return c8lib.load_ablations()


def _canonical_sha256(arm) -> str:
    return hashlib.sha256(
        json.dumps(arm, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


# ------------------------------------------------------------ (t2) 変換規則
@pytest.mark.parametrize("scale", [1.0, 0.5, 2.0])
def test_the_factor_multiplies_the_l4_share(scale):
    from shibuya import cli

    res = cli.run(l4_scale=scale, **MUTATION_RUN)
    assert res.budget_per_tick == pytest.approx(call_budget_per_tick(200) * scale)


def test_zero_means_the_agent_count():
    from shibuya import cli

    res = cli.run(l4_scale=0.0, **MUTATION_RUN)
    assert res.budget_per_tick == 200.0


# ------------------------------------------------------------ (t3) 変異検出
@pytest.fixture(scope="module")
def mutation_runs():
    """既定 / 1.0 / 0.5 / 0 の 4 ラン(mock・極小)を 1 回だけ回して使い回す。"""
    from shibuya import cli

    out = {"default": cli.run(**MUTATION_RUN)}
    for key, scale in (("x1", 1.0), ("x0.5", 0.5), ("unlimited", 0.0)):
        out[key] = cli.run(l4_scale=scale, **MUTATION_RUN)
    return out


def test_the_default_and_the_explicit_1_0_are_byte_identical(mutation_runs):
    """既定 ``1.0`` は ``budget=None`` のまま渡る=**現行の経路・現行のバイト**。"""
    base, x1 = mutation_runs["default"], mutation_runs["x1"]
    assert base.final_hash == x1.final_hash
    assert base.llm_calls == x1.llm_calls
    assert base.run_manifest_fields() == x1.run_manifest_fields()
    assert base.l4_scale == 1.0


def test_halving_the_budget_moves_the_diagnostics(mutation_runs):
    """0.5 で**呼数が減り final_hash が動く**(mock でも腕が効く=予算はエンジン側の量)。"""
    base, half = mutation_runs["default"], mutation_runs["x0.5"]
    assert base.llm_calls > 0, "候補が 1 件も立たないランでは腕を検定できない"
    assert half.llm_calls < base.llm_calls
    assert half.final_hash != base.final_hash


def test_zero_defers_nothing(mutation_runs):
    """**無制限**=繰り延べが 0 件になり、呼数は上限つきのランを上回る。

    これが「1 tick の起床候補は合流後に高々 体数」の実測の裏づけ
    (``engine.arbiter.arbitrate`` ③ → ⑤ の ``n_sel = min(…, floor(budget), agent.size)``)。
    """
    base, free = mutation_runs["default"], mutation_runs["unlimited"]
    assert free.diagnostics_day()["deferred"] == 0.0
    assert base.diagnostics_day()["deferred"] > 0.0
    assert free.llm_calls > base.llm_calls
    assert free.llm_calls <= MUTATION_RUN["n_agents"] * MUTATION_RUN["ticks"]
    assert free.final_hash != base.final_hash


# ------------------------------------------------------------ (t4) 指標 JSON
@dataclass
class _StubResult:
    """``RunResult`` の指標だけを持つスタブ(``tests/c8/test_ablations_table.py`` と同型)。"""

    n_agents: int = 100
    llm_calls: int = 250
    parse_error_rate: float = 0.02
    parse_error_rate_strict: float = 0.10
    undefined_action_count: int = 1
    conversation_sessions: int = 3
    renderer_counters: dict = field(
        default_factory=lambda: {
            "prompt_tokens_mean": 900.0,
            "tokens_shared_static_mean": 600.0,
            "tokens_cell_mean": 180.0,
            "tokens_individual_mean": 120.0,
        }
    )
    conserved: bool = True
    census_pass: bool = True
    salient_events: int = 4
    noticed: int = 12
    final_hash: str = "abc123"
    budget_mode: str = "fixed_slots"
    # ---- 実現量(第245) ----
    n_boarded: int = 40
    n_alighted: int = 38
    n_board_waiting: int = 11
    n_board_timeout: int = 2
    meals: int = 5
    meal_yen: int = 4_000
    revenue_end: int = 123_456
    fares_paid: int = 7_700
    l4_scale: float = 1.0
    budget_per_tick: float = 34.72

    def diagnostics_day(self) -> dict[str, float]:
        return {"deferred": 5.0, "promoted": 2.0, "degraded": 0.0, "suppressed": 7.0}


def test_run_metrics_carries_the_realized_block(ablation_runner):
    m = ablation_runner.run_metrics(_StubResult(), None)
    assert set(m["realized"]) == set(ablation_runner.REALIZED_FIELDS)
    assert m["realized"]["n_boarded"] == 40
    assert m["realized"]["revenue_end"] == 123_456
    assert m["realized"]["conversation_sessions"] == 3
    # purchases は RunResult の属性ではなく診断列。スタブには無い=**0(推測で埋めない)**
    assert m["realized"]["purchases"] == 0
    assert m["realized_per_agent_day"]["n_boarded"] == pytest.approx(0.40)
    assert m["realized_per_agent_day"]["revenue_end"] == pytest.approx(1234.56)
    assert m["l4_scale"] == 1.0 and m["budget_per_tick"] == pytest.approx(34.72)


def test_the_existing_metric_keys_keep_their_values(ablation_runner):
    """**列追加のみ**: 既存の欄は 1 つも動かない(値を別経路で作り直さない)。"""
    m = ablation_runner.run_metrics(_StubResult(), None)
    assert m["llm_calls"] == 250
    assert m["calls_per_agent_day"] == pytest.approx(2.5)
    assert m["notice_reach"] == pytest.approx(3.0)
    assert m["diagnostics_day"]["suppressed"] == 7.0
    assert m["group_tokens"]["cell"] == 180.0
    assert m["meals"] == 5 and m["meal_yen"] == 4_000
    assert m["final_hash"] == "abc123"


def test_the_manifest_whitelist_carries_the_budget_fields(ablation_runner):
    class _Res(_StubResult):
        def run_manifest_fields(self):  # type: ignore[override]
            return {
                "budget_mode": "fixed_slots", "l4_scale": 0.0, "budget_per_tick": 5000.0,
                "registry_hash": "落とす欄",
            }

    f = ablation_runner.run_metrics(_Res(), None)["run_manifest_fields"]
    assert f == {"budget_mode": "fixed_slots", "l4_scale": 0.0, "budget_per_tick": 5000.0}


def test_compare_runs_reports_the_realized_delta(ablation_runner):
    base = ablation_runner.run_metrics(_StubResult(), None)
    arm = ablation_runner.run_metrics(_StubResult(n_boarded=60, revenue_end=100_000), None)
    cmp = ablation_runner.compare_runs(base, arm)
    assert cmp["d_realized"]["n_boarded"] == 20
    assert cmp["d_realized"]["revenue_end"] == -23_456
    assert cmp["d_realized"]["purchases"] == 0
    # 既存の差の欄は動かない
    assert cmp["d_llm_calls"] == 0 and cmp["identical_final_hash"] is True


def test_compare_runs_without_realized_makes_no_column(ablation_runner):
    """**推測で埋めない**: 片方に欄が無ければ差の欄も作らない。"""
    assert "d_realized" not in ablation_runner.compare_runs({}, {"realized": {}})


def test_the_markdown_carries_the_realized_table(ablation_runner, table, tmp_path):
    arm = dict(ablation_runner.arm_by_id(table, ARM_ID))
    out = ablation_runner.execute_arm(
        arm, agents=16, ticks=2, seed=1, world_dir=None,
        out_dir=tmp_path, fleet=None, tape_root=tmp_path / "t",
    )
    md = ablation_runner.arm_markdown(out)
    assert "## 実現量(世界で実際に起きたこと)" in md
    assert "L4 倍率" in md and "呼/tick" in md
    # 表ごとに列数が揃っていること(ab6b のテストと同じ物差し)
    block: list[str] = []
    blocks: list[list[str]] = []
    for ln in md.splitlines():
        if ln.startswith("|"):
            block.append(ln)
        elif block:
            blocks.append(block)
            block = []
    if block:
        blocks.append(block)
    for b in blocks:
        assert len({ln.replace("\\|", "").count("|") for ln in b}) == 1, b[0]


# ------------------------------------------------------------ (t5) 腕定義表
def test_the_two_arms_are_appended(ablation_runner, table):
    ids = [a["id"] for a in table["arms"]]
    # 2026-09-22: AB7d・AB1b が末尾に付いた=この 2 腕は末尾の 2 つ手前
    assert ids[-4:-2] == [ARM_ID, ARM_UNCAPPED_ID]
    a8 = ablation_runner.arm_by_id(table, ARM_ID)
    a6c = ablation_runner.arm_by_id(table, ARM_UNCAPPED_ID)
    assert (a8["rank"], a8["index"]) == (11, "⑧")
    assert (a6c["rank"], a6c["index"]) == (12, "⑥c")
    assert a8["design_source"].startswith("PENDING D-99 (a)")
    assert a6c["design_source"].startswith("PENDING D-59 第245")
    assert a8["status"] == a6c["status"] == "ready"
    for a in (a8, a6c):
        assert a["switch"]["implemented"] is True
        assert ARM_ID not in ablation_runner.first_wave_ids(table)
    assert a8["switch"]["mock_effective"] is True, "予算はエンジン側の量=mock でも動く"
    assert a6c["switch"]["mock_effective"] is False, "腕の中の差は看板だけ=実 LLM 必須"
    assert "--l4-scale" in a8["switch"]["how"]
    assert ablation_runner.validate_table(table) == []


def test_the_runs_and_their_kwargs(ablation_runner, table):
    a8 = ablation_runner.arm_by_id(table, ARM_ID)
    assert [r["tag"] for r in a8["runs"]] == ["l4_x1", "l4_x0.5", "l4_x2", "l4_unlimited"]
    assert [r["kwargs"] for r in a8["runs"]] == [
        {"l4_scale": 1.0}, {"l4_scale": 0.5}, {"l4_scale": 2.0}, {"l4_scale": 0.0},
    ]
    a6c = ablation_runner.arm_by_id(table, ARM_UNCAPPED_ID)
    assert [r["tag"] for r in a6c["runs"]] == [
        "p_see_1_00", "ad_zero", "p_see_0_30", "p_see_0_14",
    ]
    assert [r["kwargs"] for r in a6c["runs"]] == [
        {"l4_scale": 0.0, "signage_p_see": 1.0},
        {"l4_scale": 0.0, "signage": False},
        {"l4_scale": 0.0, "signage_p_see": 0.3},
        {"l4_scale": 0.0, "signage_p_see": 0.14},
    ]
    for arm in (a8, a6c):
        assert arm["runs"][0]["is_baseline"] is True
        for r in arm["runs"][1:]:
            assert "is_baseline" not in r
        for r in arm["runs"]:
            assert set(r["kwargs"]) <= ablation_runner.ALLOWED_KWARGS
            assert not (set(r["kwargs"]) & ablation_runner.PENDING_KWARGS)
    assert "l4_scale" in ablation_runner.ALLOWED_KWARGS


def test_the_metrics_are_the_ad_zero_five_plus_realized(ablation_runner, table):
    base = ablation_runner.arm_by_id(table, "AB6-AD-ZERO")["metrics"]
    for arm_id in (ARM_ID, ARM_UNCAPPED_ID):
        got = ablation_runner.arm_by_id(table, arm_id)["metrics"]
        assert got == [*base, "realized"]
        for m in got:
            assert m in table["metrics"]


def test_the_existing_arms_are_byte_identical(table):
    """**後ろに 2 本足しても既存 10 腕の定義は 1 バイトも動かない**。"""
    from tests.c8.test_ablations_ab7 import FROZEN_ARM_SHA256

    frozen = {**FROZEN_ARM_SHA256, "AB6b-AD-NOTICE": FROZEN_AB6B_SHA256}
    got = {a["id"]: _canonical_sha256(a) for a in table["arms"] if a["id"] in frozen}
    assert got == frozen
    assert len(frozen) == 10


def test_the_kwargs_reach_run_day(ablation_runner, table, tmp_path):
    """腕定義の ``kwargs`` が ``cli.run`` → ``run_day`` → manifest まで通る(mock・極小)。"""
    arm = dict(ablation_runner.arm_by_id(table, ARM_ID))
    out = ablation_runner.execute_arm(
        arm, agents=16, ticks=2, seed=1, world_dir=None,
        out_dir=tmp_path, fleet=None, tape_root=tmp_path / "t",
    )
    assert out["executed"] is True
    assert [r["l4_scale"] for r in out["runs"]] == [1.0, 0.5, 2.0, 0.0]
    got = [r["run_manifest_fields"]["budget_per_tick"] for r in out["runs"]]
    ref = call_budget_per_tick(16)
    assert got == pytest.approx([ref, ref * 0.5, ref * 2.0, 16.0])


def test_the_uncapped_arm_reaches_run_day_too(ablation_runner, table, tmp_path):
    """⑥c は ⑥b の 4 構成に ``l4_scale=0`` を重ねただけ(新しい口は作っていない)。"""
    arm = dict(ablation_runner.arm_by_id(table, ARM_UNCAPPED_ID))
    out = ablation_runner.execute_arm(
        arm, agents=16, ticks=2, seed=1, world_dir=None,
        out_dir=tmp_path, fleet=None, tape_root=tmp_path / "t",
    )
    fields = [r["run_manifest_fields"] for r in out["runs"]]
    assert [f["signage_p_see"] for f in fields] == [1.0, 1.0, 0.3, 0.14]
    assert [f["signage"] for f in fields] == [True, False, True, True]
    assert all(f["budget_per_tick"] == 16.0 for f in fields), "4 ランとも無制限"


# ------------------------------------------------------------ 予算の通算
def test_the_cost_and_totals_are_arithmetic(c8lib, table, ablation_runner):
    for arm_id in (ARM_ID, ARM_UNCAPPED_ID):
        c = ablation_runner.arm_by_id(table, arm_id)["cost"]
        assert c["runs"] == 4 and c["calls"] == 200_000
        assert c["gpu_hours"] == pytest.approx(c8lib.gpu_hours_for_calls(c["calls"]), abs=1e-3)
        # 無制限腕は本表の「1 ラン=呼 50,000」の規約の外=note で宣言する
        assert "約 1 h/本" in c["note"] or "無制限" in c["note"]
    t = table["totals"]
    assert t["runs_if_independent"] == sum(a["cost"]["runs"] for a in table["arms"]) == 38  # 2026-09-22: +AB7d 3 +AB1b 2
    assert t["within_l2"] is (t["gpu_hours_with_shared_baseline"] <= t["l2_reserve_hours"])
    if not t["within_l2"]:
        assert "L2" in t["note"]


def test_the_open_questions_declare_the_expedients(table):
    """『無制限=体数』の置き方と合格線の不在を**親判断待ちとして残す**(黙って決めない)。"""
    q8 = [q for q in table["open_questions"] if ARM_ID in q]
    q6c = [q for q in table["open_questions"] if ARM_UNCAPPED_ID in q]
    assert len(q8) == 1 and len(q6c) == 1
    assert "expedient" in q8[0] and "合格線" in q8[0]
