"""ablation 第1陣 6 本の**腕定義表**のスキーマと、設計書(知覚契約書 §8)との突合。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

import pytest


@pytest.fixture(scope="module")
def table(c8lib):
    return c8lib.load_ablations()


# ------------------------------------------------------------------ スキーマ
def test_table_validates(ablation_runner, table):
    assert ablation_runner.validate_table(table) == []


def test_six_arms_in_priority_order(ablation_runner, table):
    """§8「第1陣=6 本」・rank は優先順位規則(expedient の量 × 駆動可能性 ÷ コスト)の順。

    第1陣より後に足した腕(``first_wave`` の外・2026-09-16 の ``AB7-OPEN-INTENT``)は
    **表の先頭 6 本より後ろ**に並び、rank は 7 以降の通し番号を続ける。
    """
    arms = table["arms"]
    wave1 = ablation_runner.first_wave_ids(table)
    assert len(wave1) == 6
    assert [a["id"] for a in arms[:6]] == wave1
    assert [a["rank"] for a in arms[:6]] == [1, 2, 3, 4, 5, 6]
    assert [a["index"] for a in arms[:6]] == ["①", "②", "③", "④", "⑤", "⑥"]
    assert [a["rank"] for a in arms] == list(range(1, len(arms) + 1))


def test_arms_match_design_text(c8lib, table):
    """設計書 §8 の逐語と腕定義表の対応(**設計書が変わったら落ちる**)。"""
    design = c8lib.scan_first_wave_arms()
    assert len(design) == 6
    keys = ["単一ランキング", "d50", "不応期", "SNR", "内省", "広告ゼロ"]
    for arm, want, key in zip(table["arms"], design, keys):
        assert key in want, f"設計書 §8 の第1陣が変わった: {want!r}"
        assert key in arm["name"] or key in arm["design_source"], arm["id"]


def test_every_arm_declares_switch_state(table):
    """切替口が無い腕は**差分案**を必ず持つ(自前で src/ を触らないための規律)。"""
    for a in table["arms"]:
        sw = a["switch"]
        assert isinstance(sw["implemented"], bool)
        if not sw["implemented"]:
            assert sw["diff_proposal"], a["id"]
            assert a["status"] in ("blocked_switch", "blocked_feature")
        else:
            assert a["status"] == "ready"


def test_pending_kwargs_are_marked(ablation_runner, table):
    """未実装の口を使う ``runs`` は ``pending`` 印が要る(実行器が飛ばす目印)。"""
    for a in table["arms"]:
        for r in a.get("runs", ()):
            if set(r.get("kwargs", {})) & ablation_runner.PENDING_KWARGS:
                assert r.get("pending") is True, (a["id"], r["tag"])


def test_kwargs_are_allowlisted(ablation_runner, table):
    """腕定義表(データ)から任意のキーワード引数を通さない。"""
    for a in table["arms"]:
        for r in a.get("runs", ()):
            assert set(r.get("kwargs", {})) <= ablation_runner.ALLOWED_KWARGS


def test_budget_within_l2(table):
    """共有ベースラインの見積りと ``within_l2`` フラグの**整合**を機械で守る。

    2026-09-17(AB7c-VOCAB-V2 の追加)までは「L2 の枠に収まる計画であること」を直接の
    合否にしていた。語彙 v2 の腕(3 ラン)を足した時点で共有ベースライン込みの合計が
    **5.32 h** になり、枠の目安 **4.8 h** を超えた(``within_l2=false``)。L2 は割合宣言で
    絶対値が無く(``budget.note`` の expedient=親判断待ち)、**どの腕を先に回すかは
    ユーザー判断**なので、ここで守るのは次の 2 点にする——超過を黙って飲み込まないため:
      ① フラグが算術と一致する(表が自分の見積りについて嘘をつけない)
      ② 超えているなら ``totals.note`` に L2 と明記されている(宣言が残る)
    """
    t = table["totals"]
    assert t["within_l2"] is (
        t["gpu_hours_with_shared_baseline"] <= t["l2_reserve_hours"]
    )
    if not t["within_l2"]:
        assert "L2" in t["note"], "L2 超過は totals.note に明記すること"
    assert t["runs_with_shared_baseline"] < t["runs_if_independent"]


def test_gpu_hours_match_the_conversion(c8lib, table):
    """表の GPU 時間は ``c8lib.gpu_hours_for_calls``(C6 実測の外挿)と一致すること。

    手で書いた見積りが換算式とずれると L2 の枠判定が嘘になる。
    """
    for a in table["arms"]:
        c = a["cost"]
        assert c["gpu_hours"] == pytest.approx(c8lib.gpu_hours_for_calls(c["calls"]), abs=1e-3)
        if "calls_with_shared_baseline" in c:
            assert c["gpu_hours_with_shared_baseline"] == pytest.approx(
                c8lib.gpu_hours_for_calls(c["calls_with_shared_baseline"]), abs=1e-3
            )
    t = table["totals"]
    assert t["gpu_hours_with_shared_baseline"] == pytest.approx(
        c8lib.gpu_hours_for_calls(t["calls_with_shared_baseline"]), abs=1e-3
    )
    assert t["gpu_hours_if_independent"] == pytest.approx(
        c8lib.gpu_hours_for_calls(t["calls_if_independent"]), abs=1e-3
    )


def test_totals_match_the_arms(table):
    """合計欄は腕の積み上げと一致すること(手書きの合計がずれない)。"""
    t = table["totals"]
    assert t["runs_if_independent"] == sum(a["cost"]["runs"] for a in table["arms"])
    assert t["calls_if_independent"] == sum(a["cost"]["calls"] for a in table["arms"])
    shared = 1 + sum(
        len([r for r in a.get("runs", ()) if not r.get("is_baseline")]) for a in table["arms"]
    )
    assert t["runs_with_shared_baseline"] == shared
    assert t["calls_with_shared_baseline"] == shared * table["default_scale"]["calls_per_run"]


def test_only_the_second_wave_arms_are_still_blocked(ablation_runner, table):
    """切替口の実装状況(C6 で ①・**C8 で ②③⑥**=2026-09-09)。

    残るのは ④聴覚 ΔSNR・⑤日次内省で、どちらも**前提機能が §9 第2陣**(聴覚の物理軸は
    コードに無く同一セル代理・日次内省は就寝で「発火を記録するだけ」)。**第1陣の 6 本だけ**
    を見る(追加腕は下の ``test_the_added_arms_are_implemented``)。
    """
    wave1 = set(ablation_runner.first_wave_ids(table))
    arms1 = [a for a in table["arms"] if a["id"] in wave1]
    ready = [a["id"] for a in arms1 if a["switch"]["implemented"]]
    assert ready == [
        "AB1-BUDGET-MODE", "AB2-PNOTICE-D50", "AB3-REFRACTORY-PROX", "AB6-AD-ZERO"
    ]
    blocked = {a["id"]: a["status"] for a in arms1 if not a["switch"]["implemented"]}
    assert blocked == {"AB4-HEARING-SNR": "blocked_feature", "AB5-INTROSPECTION": "blocked_feature"}


def test_the_added_arms_are_implemented(ablation_runner, table):
    """第1陣より後に足した腕は**切替口つきで足す**(未実装の腕を後ろに積まない)。"""
    wave1 = set(ablation_runner.first_wave_ids(table))
    extra = [a for a in table["arms"] if a["id"] not in wave1]
    assert [a["id"] for a in extra] == [
        "AB7-OPEN-INTENT", "AB7b-HINT-INTENT", "AB7c-VOCAB-V2",
    ]
    for a in extra:
        assert a["switch"]["implemented"] is True and a["status"] == "ready"


def test_mock_ineffective_arms_are_prompt_only(table):
    """mock で差が出ない腕=**プロンプト本文しか変えない**腕(①⑥と AB7・AB7b)。"""
    prompt_only = {a["id"] for a in table["arms"] if not a["switch"]["mock_effective"]}
    assert prompt_only == {
        "AB1-BUDGET-MODE", "AB6-AD-ZERO", "AB7-OPEN-INTENT", "AB7b-HINT-INTENT",
    }


# ------------------------------------------------------------------ 引き当てと表
def test_arm_by_id_forms(ablation_runner, table):
    assert ablation_runner.arm_by_id(table, "AB1-BUDGET-MODE")["rank"] == 1
    assert ablation_runner.arm_by_id(table, "ab1")["rank"] == 1
    assert ablation_runner.arm_by_id(table, "③")["id"] == "AB3-REFRACTORY-PROX"
    with pytest.raises(KeyError):
        ablation_runner.arm_by_id(table, "AB9")


def test_table_markdown_is_a_valid_table(ablation_runner, table):
    md = ablation_runner.table_markdown(table)
    body = [ln for ln in md.splitlines() if ln.startswith("|")]
    ncol = body[0].count("|")
    for line in body:
        assert line.replace("\\|", "").count("|") == ncol, line


def test_validate_table_detects_breakage(ablation_runner, table):
    broken = json.loads(json.dumps(table))
    broken["arms"][0]["switch"]["implemented"] = False
    broken["arms"][0]["switch"].pop("diff_proposal", None)
    broken["arms"][1]["runs"][0]["kwargs"] = {"os": "rm -rf"}
    problems = ablation_runner.validate_table(broken)
    assert any("diff_proposal" in p for p in problems)
    assert any("許されない kwargs" in p for p in problems)


# ------------------------------------------------------------------ 指標(純関数)
@dataclass
class _StubResult:
    """``RunResult`` の指標だけを持つスタブ(ランを回さずに ``run_metrics`` を試す)。"""

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

    def diagnostics_day(self) -> dict[str, float]:
        return {"deferred": 5.0, "promoted": 2.0, "degraded": 0.0, "suppressed": 7.0}


def test_run_metrics_from_stub(ablation_runner):
    m = ablation_runner.run_metrics(_StubResult(), None)
    assert m["calls_per_agent_day"] == pytest.approx(2.5)
    assert m["notice_reach"] == pytest.approx(3.0)
    assert m["diagnostics_day"]["suppressed"] == 7.0
    assert m["group_tokens"]["cell"] == 180.0
    assert m["run_manifest_fields"] == {}  # スタブは manifest を持たない


def test_manifest_whitelist_carries_the_arms(ablation_runner):
    """腕の同定欄が ``run_metrics`` の白リストを通る(D-66 の 3 欄を含む・2026-09-11)。"""

    class _Res(_StubResult):
        def run_manifest_fields(self):  # type: ignore[override]
            return {
                "budget_mode": "fixed_slots", "ablations": (), "template_sha256": "t",
                "catalog_sha16": "c", "replay_date": "2026-07-28",
                "p_notice_ablation": "A4", "p_notice_d50_scale": 1.0,
                "refractory_scale": {}, "signage": True,
                "plan_executor": True, "exit_mode": "immediate", "attendance_rate": 0.88,
                "registry_hash": "落とす欄", "fleet": {},
            }

    f = ablation_runner.run_metrics(_Res(), None)["run_manifest_fields"]
    for key in ("plan_executor", "exit_mode", "attendance_rate"):
        assert key in f, f
    assert f["attendance_rate"] == 0.88 and f["exit_mode"] == "immediate"
    assert "registry_hash" not in f and "fleet" not in f  # 白リストの外は落ちる


def test_run_metrics_handles_zero_salient(ablation_runner):
    m = ablation_runner.run_metrics(_StubResult(salient_events=0, noticed=0), None)
    assert m["notice_reach"] == 0.0


def test_compare_runs(ablation_runner):
    base = {
        "final_hash": "h", "llm_calls": 100, "format_error_rate": 0.05, "notice_reach": 1.0,
        "prompt_tokens_mean": 900.0, "action_counts": {"移動": 60, "待機": 40},
    }
    arm = {
        "final_hash": "h2", "llm_calls": 120, "format_error_rate": 0.03, "notice_reach": 2.0,
        "prompt_tokens_mean": 880.0, "action_counts": {"移動": 40, "待機": 60},
    }
    c = ablation_runner.compare_runs(base, arm)
    assert c["identical_final_hash"] is False
    assert c["d_llm_calls"] == 20
    assert c["d_prompt_tokens_mean"] == pytest.approx(-20.0)
    assert c["action_jsd"] > 0.0
    assert c["null_reference_bits"] == 0.0035  # T7(seed 違い)= 受入報告 C6 §3
    assert c["exceeds_null"] is True


def test_compare_runs_without_tape(ablation_runner):
    """テープが無い(行動分布が取れない)ときは JSD 欄を作らない=**推測で埋めない**。"""
    c = ablation_runner.compare_runs({"final_hash": "h"}, {"final_hash": "h"})
    assert "action_jsd" not in c
    assert c["identical_final_hash"] is True


# ------------------------------------------------------------------ 実行器の門
def test_execute_arm_refuses_unimplemented_switch(ablation_runner, table, tmp_path):
    """切替口が無い腕は**回さず**差分案を印字して返る(src/ を触らないため)。"""
    arm = ablation_runner.arm_by_id(table, "AB4-HEARING-SNR")
    out = ablation_runner.execute_arm(
        arm, agents=8, ticks=1, seed=1, world_dir=None,
        out_dir=tmp_path, fleet=None, tape_root=tmp_path / "t",
    )
    assert out["executed"] is False
    assert out["runs"] == []
    assert any("差分案" in n for n in out["notes"])


def test_execute_arm_notes_real_llm_required(ablation_runner, table, tmp_path):
    """mock で差が出ない腕は「実 LLM 必須」を印字する。"""
    arm = ablation_runner.arm_by_id(table, "AB1-BUDGET-MODE")
    stub = dict(arm)
    stub["runs"] = []  # ラン自体は回さずに注記だけを見る
    out = ablation_runner.execute_arm(
        stub, agents=8, ticks=1, seed=1, world_dir=None,
        out_dir=tmp_path, fleet=None, tape_root=tmp_path / "t",
    )
    assert any("実 LLM 必須" in n for n in out["notes"])


def test_execute_arm_rejects_unknown_kwargs(ablation_runner, tmp_path):
    arm = {
        "id": "X", "switch": {"implemented": True, "mock_effective": True},
        "runs": [{"tag": "t", "kwargs": {"eval": "1"}}],
    }
    with pytest.raises(ValueError):
        ablation_runner.execute_arm(
            arm, agents=4, ticks=1, seed=1, world_dir=None,
            out_dir=tmp_path, fleet=None, tape_root=tmp_path / "t",
        )


def test_arm_markdown_renders_without_runs(ablation_runner, table):
    arm = ablation_runner.arm_by_id(table, "AB4-HEARING-SNR")
    md = ablation_runner.arm_markdown(
        {"arm": arm["id"], "index": arm["index"], "name": arm["name"],
         "design_source": arm["design_source"], "switch": arm["switch"],
         "scale": {}, "route": "mock", "notes": ["未実装"], "runs": []}
    )
    assert "**未実装**" in md
