"""第 3 期 3-3 「T0 までテープを再生して T0 から今の方策」の分岐と R-71 の 4 つの確認(``engine.experiment.branch``)。

- 世界資産 1,000 体・2 日の基準のラン(録画・日の境目の状態・checkpoints)→ T0=2 日目の正午で L1 の改変(正午に開いている店の
  休業)→ (a) 入力の一致 (b) T0 より前の全 checkpoint の一致・テープ外 0・再開した状態のハッシュ (c) T0 以後の最初の食い違いの
  刻みと部品(系 world・欄 ``pois.open_now``)(d) A/A の差が厳密に 0・A/A の final が基準と同じ。報告 ``branch_report.json``。
- 合成の世界の小さな分岐(決定と告知の行だけ=世界は変わらない=(c) の世界の食い違いは無い・自分の欄の食い違いだけ)。
- 確認の関数の負の対照(設定の差・checkpoint の改ざん・テープ外・final の改ざん・指紋の行)。
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from shibuya import cli
from shibuya.core.time_consts import NS_PER_SECOND, SECONDS_PER_DAY
from shibuya.engine.experiment import branch as BR
from shibuya.engine.experiment.form import ExperimentForm

from tests.engine.experiment._x33 import form

WORLD_DIR = Path("data/world/v2")
real_data = pytest.mark.requires_data("world_v2:w17_schedule.parquet")
NOON_DAY2_NS = (SECONDS_PER_DAY + SECONDS_PER_DAY // 2) * NS_PER_SECOND
T0 = (SECONDS_PER_DAY + SECONDS_PER_DAY // 2) // 60


def _record_base(out: Path, **kw) -> Path:
    return _record_base_res(out, **kw)[0]


def _record_base_res(out: Path, **kw):
    res = cli.run(tape_path=out / BR.BASE_TAPE, state_out=out / BR.BASE_STATE, **kw)
    (out / BR.BASE_CHECKPOINTS).write_text(json.dumps(cli.checkpoints_payload(res), ensure_ascii=False, default=str),
                                           encoding="utf-8")
    return out, res


def _no_abs_paths(text: str) -> bool:
    return ":\\" not in text and ":/" not in text.replace("://", "") and "/Users/" not in text


# ================================================================= 世界資産 1,000 体・2 日
WKW = dict(n_agents=1000, seed=1, world_dir=str(WORLD_DIR), sim_days=2, vocab_version="v3", checkpoint_every=60)


def _open_at_noon_on_day2() -> list[int]:
    """2 日目(火曜)の正午に W7 で開いている店(番号の昇順)。"""
    from shibuya.engine.calendar import DEFAULT_WORLD_START, SimCalendar, load_holidays
    from shibuya.engine.processes.opening import rows_of_day
    from shibuya.world.assets import load_process_assets_or_synthetic
    from shibuya.world.state import World

    w = World.load(WORLD_DIR)
    pa = load_process_assets_or_synthetic(WORLD_DIR, w.assets)
    row = SimCalendar(DEFAULT_WORLD_START, holidays=load_holidays()).opening_row(1)
    sel = rows_of_day(pa.plan_poi, pa.plan_day, row, pa.plan_ph_poi) & (pa.plan_start <= 720) & (pa.plan_end > 720)
    return sorted({int(x) for x in np.asarray(pa.plan_poi)[sel]})


@pytest.fixture(scope="module")
def world_branch(tmp_path_factory):
    base, res = _record_base_res(tmp_path_factory.mktemp("x33_world_base"), **WKW)
    open_ = _open_at_noon_on_day2()
    staff = np.asarray(res.runner.opening.staff_of_poi)
    staffed = [j for j in open_ if staff[j] >= 0]  # 担当の従業者のいる店(告知の宛先 staff)
    ids = sorted(set(open_[:200]) | set(staffed[:20]))
    f = ExperimentForm.from_dict({
        "kind": "explore", "subject": {"level": "L1", "ids": ids}, "content": [{"decision": "closure"}],
        "start": NOON_DAY2_NS, "notice": {"to": ["staff", 1, 2, 3], "via": "メッセージ"},
        "question": "正午に店を休むと人の流れはどう変わるか",
        "metrics": {"primary": {"id": "calls", "path": "manifest.llm_calls_total"}},
    })
    out = BR.run_branch(f, base, runner=cli.run, run_kwargs=WKW)
    return base, f, out, ids


@real_data
def test_world_branch_four_checks(world_branch):
    base, f, out, ids = world_branch
    rep = out.report
    assert len(ids) >= 50 and rep["T0_step"] == T0 and rep["resume_from"] == "state-T00001440.npz"
    s = rep["summary"]
    assert s["a"] and s["b"] is True and s["d"] and s["ok"]
    a = rep["checks"]["a_input_match"]
    # 〔第 2 期 2-4 V5〕group_norms.cost.ticks は観測の節=設定の差に出ない(前は resume_derived で許した)
    assert a["branch"]["config_diffs_outside_arm"] == [] and a["branch"]["resume_derived"] == []
    assert "group_norms.cost.ticks" not in a["branch"]["config_diffs"]
    b = rep["checks"]["b_pre_t0"]
    assert b["branch"]["checkpoints_before_T0"] == 12 and b["branch"]["tape_miss_before_t0"] == 0
    assert b["resume_state"]["base_state_matches_base_end_of_day"] is True  # 〔検収 L2〕基準の自己一致
    c = rep["checks"]["c_first_divergence"]
    assert c["world"]["step"] == T0 and c["world"]["system"] == "world" and "pois.open_now" in c["world"]["keys"]
    assert c["any"]["step"] == T0 and c["any"]["system"] == "experiment"  # 申込書の控えと決定の行が最初
    assert c["coarse"]["first_step"] == T0 + 59 and "behavior_hash" in c["coarse"]["hashes_differ"]
    # 〔検収 L1〕窓=T0 以後の全 checkpoint の走査で決めた区間(一致した最後の checkpoint の次 〜 最初に食い違った checkpoint)
    assert c["window_steps"] == [T0, T0 + 59] and c["branch_repeat_same"] is True and c["reason"] == ""
    # 〔親の判断 M3〕実行の内訳と §1-1 の判定(4 つの確認とは別の欄)。〔第 4 期 4-3 段 10・版上げ 3 回目〕差し替えの世界(W16 を
    # W21 に)の 1,000 体では全 2,337 店に担当が居る(W21 の担当+残りの店の丸振り)=宛先 200 店とも担当つき・担当の開け閉めの
    # 行為 1・つなぎ 199(前=W16 の世界: 担当 0 人=staffed_pois 0・role_actions 0=全部つなぎ・記録 pop43)
    ex = rep["execution"]["branch"]
    assert ex["targets"] == len(ids) and ex["staffed_targets"] == len(ids) and ex["staffed_pois"] == 2337
    assert ex["role_actions"] == 1 and ex["fallback"] == len(ids) - 1
    assert s["executed_by_agents"] is False and s["ok"] is True
    d = rep["checks"]["d_aa"]
    assert d["ok"] and d["final_same"] and d["probe_first_divergence"] is None and d["final_equals_base"]
    assert out.twin_a.final_hash == json.loads((base / BR.BASE_CHECKPOINTS).read_text(encoding="utf-8"))["final_hash"]
    assert out.branch.final_hash != out.twin_a.final_hash


@real_data
def test_world_branch_replay_and_manifest(world_branch):
    _base, f, out, _ids = world_branch
    m = out.branch.run_manifest_fields()["experiment"]
    assert m["form_sha256"] == f.sha256() and m["branch_t0_step"] == T0 and m["applied"] == 1
    r = m["replay"]
    assert r["replayed_before_t0"] > 0 and r["tape_miss_before_t0"] == 0 and r["live_from_t0"] > 0
    assert not r["stateful_policy"] and m["checks"]["ok"] is True and m["checks"]["c_system"] == "world"
    # 告知の「届いた情報」: 番号で書いた 3 人+宛先 staff(宛先の店の担当)に届く。〔第 4 期 4-3 段 10〕差し替えの世界の 1,000 体
    # では店の担当が居る=告知 21(前=W16 の世界: 担当 0 人=番号の 3 人だけ・staff_of_poi ≥ 0 の店 0=記録 cf33/README.md の限界)
    assert m["meter"]["notices"] == 21 and m["meter"]["notice_unreached"] == 0
    assert int((np.asarray(out.branch.runner.opening.staff_of_poi) >= 0).sum()) == 2337
    aa = out.twin_a.run_manifest_fields()["experiment"]
    assert aa["aa"] is True and aa["applied"] == 0 and aa["replay"]["tape_miss_before_t0"] == 0


@real_data
def test_world_branch_switch_and_the_split_of_d(world_branch):
    """〔3-3b〕同じ分岐(世界資産 1,000 体・mock)が T からの切り替えの口を通る: 窓の頭・再生の箱 0・(d) の決定論の確認と床 0・
    (c) の A/A の枝 2 本は食い違わない(床 0=改変の枝の食い違いは床の外)。"""
    _base, _f, out, _ids = world_branch
    rep = out.report
    s = rep["summary"]
    assert s["model"] == "mock" and s["deterministic"] and s["d"] is True and s["d_floor_zero"] is True
    det = rep["checks"]["d_determinism"]
    assert det["aa_exact"] and det["final_equals_base"] and det["twins_vs_base_before_t0"] is True
    vs = rep["checks"]["c_first_divergence"]["vs_aa"]
    assert vs["branch_first_step"] == T0 + 59 and vs["aa_first_step"] is None and vs["gap_steps"] is None
    assert rep["switch"]["window_ns"] == 60 * NS_PER_SECOND and rep["switch"]["t0_step"] == T0
    assert rep["checks"]["b_pre_t0"]["aa_b"]["ok"] is True
    for res in (out.twin_a, out.twin_b, out.branch):
        r = res.run_manifest_fields()["experiment"]["replay"]
        assert r["box_carried"] == 0 and r["box_at_switch"] == 0 and r["rows_crossing_t0"] == 0


@real_data
def test_world_branch_report_file(world_branch):
    base, f, out, _ids = world_branch
    p = out.report_path
    assert p is not None and p.name == BR.REPORT_NAME and p.parent.name == f.sha256()[:16]
    text = p.read_text(encoding="utf-8")
    doc = json.loads(text)
    assert doc["schema"] == BR.REPORT_SCHEMA and doc["summary"]["ok"] is True
    assert _no_abs_paths(text)


# ================================================================= 合成の世界(小さい・データ無しでも回る)
SKW = dict(n_agents=80, seed=1, world_dir=None, n_cells=9, sim_days=2, renderer="stub", checkpoint_every=60)


def test_synthetic_branch_with_only_decision_and_notice_rows(tmp_path):
    base = _record_base(tmp_path / "base", **SKW)
    f = form(start=NOON_DAY2_NS, content=[{"decision": "event"}], notice={"to": [1, 2], "via": "メッセージ"})
    out = BR.run_branch(f, base, runner=cli.run, run_kwargs=SKW, out_dir=tmp_path / "br")
    s = out.report["summary"]
    assert s["a"] and s["b"] is True and s["d"] and s["ok"]
    c = out.report["checks"]["c_first_divergence"]
    assert c["world"] is None and c["coarse"]["first_step"] is None  # 世界は変わらない(決定と告知の行だけ)
    assert c["any"] is None and "食い違いが無い" in c["reason"] and c["window_steps"] is None  # 窓の回し直しはしない
    assert out.branch_probe is None and out.report["summary"]["executed_by_agents"] is None  # 表を実行する決定が無い
    assert out.branch.final_hash == out.twin_a.final_hash == out.twin_b.final_hash
    # A/A だけ(--experiment-aa): 3 本とも同じ
    out2 = BR.run_branch(f, base, runner=cli.run, run_kwargs=SKW, aa_only=True, out_dir=tmp_path / "aa")
    assert out2.report["checks"]["c_first_divergence"]["any"] is None and out2.report["summary"]["ok"]
    assert _no_abs_paths(out2.report_path.read_text(encoding="utf-8"))
    with pytest.raises(FileExistsError):  # 既にある報告は上書きしない
        BR.run_branch(f, base, runner=cli.run, run_kwargs=SKW, aa_only=True, out_dir=tmp_path / "aa")


def test_branch_refuses_a_t0_outside_the_base(tmp_path):
    base = tmp_path / "b"
    base.mkdir()
    (base / BR.BASE_CHECKPOINTS).write_text(json.dumps({"manifest": {"tick_seconds": 60, "sim_days": 1}}),
                                            encoding="utf-8")
    with pytest.raises(ValueError, match="内側に無い"):
        BR.run_branch(form(start=NOON_DAY2_NS), base, runner=cli.run, run_kwargs={})


# ================================================================= 確認の関数(負の対照)
def _doc(final="f", hashes=(("a", "x"), ("b", "y")), steps=(10, 20), manifest=None):
    cps = [{"tick": t, "behavior_hash": h[0], "full_hash": h[1], "population_hash": "P", "schedule_hash": "S",
            "agents_hash": h[0], "world_hash": h[0]} for t, h in zip(steps, hashes)]
    return {"seed": 1, "final_hash": final, "checkpoints": cps,
            "manifest": manifest or {"tick_seconds": 60, "run_kind": "test", "experiment": None,
                                     "population_seed": 1, "environment_seed": 1}}


def test_input_match_negative_controls():
    base = _doc()
    ok = BR.input_match(base, _doc(manifest={**base["manifest"], "run_kind": "counterfactual",
                                             "experiment": {"form_sha256": "z"}}))
    assert ok["ok"] and ok["config_diffs_outside_arm"] == []
    bad = BR.input_match(base, _doc(manifest={**base["manifest"], "tick_seconds": 30}))
    assert not bad["ok"] and bad["config_diffs_outside_arm"] == ["tick_seconds"]
    seed = BR.input_match(base, {**_doc(), "seed": 2})
    assert not seed["ok"] and not seed["seeds_same"]
    # 再開で動く欄は宣言した値のときだけ許す
    # 〔第 2 期 2-4 V5〕group_norms.cost.ticks は観測の節に移した=今の節の表では設定の差に出ない。RESUME_DERIVED は 2-4 より前の
    # 節の表(cost ごと設定)で録った基準との比べのために残す=その表を manifest に載せた基準で負の対照を見る
    from shibuya.engine import manifest_sections as MS

    old_paths = {k: v for k, v in MS.PATHS.items() if not k.startswith("group_norms.cost")}
    old_paths["group_norms.cost"] = MS.CONFIG
    old = {**base["manifest"], "manifest_sections": {"paths": old_paths}}
    gb = _doc(manifest={**old, "group_norms": {"cost": {"ticks": 2880}}})
    gr = _doc(manifest={**old, "group_norms": {"cost": {"ticks": 1440}}})
    assert BR.input_match(gb, gr, resume_expect={"group_norms.cost.ticks": (2880, 1440)})["ok"]
    assert not BR.input_match(gb, gr, resume_expect={"group_norms.cost.ticks": (2880, 1000)})["ok"]
    nb = _doc(manifest={**base["manifest"], "group_norms": {"cost": {"ticks": 2880}}})
    nr = _doc(manifest={**base["manifest"], "group_norms": {"cost": {"ticks": 1440}}})
    now = BR.input_match(nb, nr)  # 今の節の表=観測=宣言なしでも差に出ない
    assert now["ok"] and "group_norms.cost.ticks" not in now["config_diffs"]


def test_pre_t0_and_aa_negative_controls():
    base = _doc()
    assert BR.pre_t0_match(base, _doc(), 15)["ok"] is True
    tampered = _doc(hashes=(("A", "x"), ("b", "y")))
    r = BR.pre_t0_match(base, tampered, 15)
    assert r["ok"] is False and r["first_bad_step"] == 10
    assert BR.pre_t0_match(base, _doc(), 15, replay={"tape_miss_before_t0": 1})["ok"] is False
    assert BR.pre_t0_match(base, _doc(), 5)["ok"] is None  # T0 より前の checkpoint が無い=未検査
    assert BR.aa_match(base, _doc())["ok"]
    assert not BR.aa_match(base, _doc(final="g"))["ok"]
    assert not BR.aa_match(base, _doc(), probe_a=[[1, "world", [["k", "1"]]]], probe_b=[[1, "world", [["k", "2"]]]])["ok"]
    cd = BR.first_divergence_coarse(base, tampered, from_step=0)
    assert cd["first_step"] == 10 and "behavior_hash" in cd["hashes_differ"]


def test_probe_first_divergence_and_filters():
    a = [[5, "experiment", []], [5, "world", [["pois.open_now", "1"], ["O61:runner.log", "X:aa"]]]]
    b = [[5, "experiment", [["X:experiment.handle", "r"], ["E:events._ev_n", "e"]]],
         [5, "world", [["pois.open_now", "2"], ["O61:runner.log", "X:bb"]]]]
    world = BR.probe_first_divergence(a, b, skip=BR.SELF_KEY_PREFIXES)
    assert world["step"] == 5 and world["system"] == "world" and world["keys"] == ["pois.open_now"]
    anyd = BR.probe_first_divergence(a, b)
    assert anyd["system"] == "experiment" and anyd["b"][2] == ["E:events._ev_n", "X:experiment.handle"]
    # 物の番号を含む digest(X:)はランをまたいで比べない
    assert BR.probe_first_divergence([[1, "world", [["O61:runner.log", "X:aa"]]]],
                                     [[1, "world", [["O61:runner.log", "X:bb"]]]]) is None
    assert BR.nonportable_keys(a) == ["O61:runner.log"]


def test_choose_state(tmp_path):
    st = tmp_path / "state"
    st.mkdir()
    for t, fin in ((1440, False), (2880, True)):
        (st / f"state-T{t:08d}.npz").write_bytes(b"")
        (st / f"state-T{t:08d}.json").write_text(json.dumps({"finished": fin, "progress": {"next_T": t}}),
                                                  encoding="utf-8")
    assert BR.choose_state(st, 2160)[0].name == "state-T00001440.npz"
    assert BR.choose_state(st, 1440) == (None, None)  # T0 と同じ境目は使わない(T0 より前の窓が要る)
    assert BR.choose_state(st, 4000)[0].name == "state-T00001440.npz"  # finished の状態からは再開しない


def test_cli_branch_end_to_end(tmp_path, capsys):
    """CLI: 基準のランを既存の引数(--tape・--state-out・--checkpoints-out・--sim-days)で記録し、--experiment と
    --experiment-branch で分岐を回す(報告は <記録>/branches/<申込書の指紋の先頭 16 字>/branch_report.json)。"""
    base = tmp_path / "base"
    common = ["--world", "__no_such_dir__", "--agents", "60", "--cells", "9", "--sim-days", "2",
              "--checkpoint-every", "60"]
    assert cli.main(common + ["--tape", str(base / BR.BASE_TAPE), "--state-out", str(base / BR.BASE_STATE),
                              "--checkpoints-out", str(base / BR.BASE_CHECKPOINTS)]) == 0
    f = form(start=NOON_DAY2_NS, content=[{"decision": "event"}], notice={"to": [1], "via": "メッセージ"})
    p = tmp_path / "form.json"
    p.write_text(f.to_json(), encoding="utf-8")
    assert cli.main(common + ["--experiment", str(p), "--experiment-branch", str(base)]) == 0
    rep = json.loads((base / "branches" / f.sha256()[:16] / BR.REPORT_NAME).read_text(encoding="utf-8"))
    assert rep["summary"]["ok"] is True and rep["T0_step"] == T0
    assert "[分岐]" in capsys.readouterr().out


def test_synthetic_branch_with_the_classical_policy(tmp_path):
    """古典の方策(内部の状態を持つエンジンの方策)は T0 より前も方策に答えさせ、テープの答えとの食い違いを数える(0 のはず)。"""
    kw = dict(n_agents=60, seed=1, world_dir=None, n_cells=9, sim_days=2, checkpoint_every=60, vocab_version="v3",
              policy="classical", chooser="classical", memory="on", relations="on")
    base = _record_base(tmp_path / "base", **kw)
    f = form(start=NOON_DAY2_NS, content=[{"decision": "event"}])
    out = BR.run_branch(f, base, runner=cli.run, run_kwargs=kw, out_dir=tmp_path / "br")
    assert out.report["summary"]["ok"] is True
    r = out.branch.run_manifest_fields()["experiment"]["replay"]
    assert r["stateful_policy"] and r["replayed_before_t0"] == 0 and r["policy_before_t0"] > 0
    assert r["policy_mismatch_before_t0"] == 0 and r["tape_miss_before_t0"] == 0 and r["live_from_t0"] > 0


@real_data
def test_world_resume_with_the_same_form_equals_straight(tmp_path):
    """申込書つきのラン(1 日目の正午から 200 店の休業)を日の境目で止めて同じ申込書で再開すると、通しのランと同じ
    (再開のランは表へ当て直すだけ=決定の行は親のラン・日の頭で張り直した営業時間の表に当て直す)。"""
    from shibuya.core.time_consts import SECONDS_PER_HOUR

    kw = dict(n_agents=300, seed=1, world_dir=str(WORLD_DIR), sim_days=2, vocab_version="v3", checkpoint_every=120)
    f = form(subject={"level": "L1", "ids": _open_at_noon_on_day2()[:200]}, start=12 * SECONDS_PER_HOUR * NS_PER_SECOND)
    straight = cli.run(**kw, experiment=f)
    a = cli.run(**kw, experiment=f, state_out=tmp_path / "s", stop_at_tick=1440)
    b = cli.run(**kw, experiment=f, resume_from=tmp_path / "s" / "state-T00001440.npz")
    got = [(c.tick, c.behavior_hash, c.full_hash) for c in b.checkpoints]
    want = [(c.tick, c.behavior_hash, c.full_hash) for c in straight.checkpoints if c.tick >= 1440]
    assert got == want and b.final_hash == straight.final_hash
    ma, mb = a.run_manifest_fields()["experiment"], b.run_manifest_fields()["experiment"]
    assert ma["applied"] == 1 and mb["applied"] == 0 and mb["meter"]["reapplied"] == 1  # 再開は当て直すだけ
    plain = cli.run(**kw)
    assert plain.final_hash != straight.final_hash  # 休業は効いている


@real_data
@pytest.mark.slow
def test_world_branch_with_staff_5000(tmp_path):
    """〔親の判断 M3〕担当の従業者のいる世界(5,000 体=1-5 の担当 2,337 人)で同じ休業の分岐を回し、担当が実行した件数と
    つなぎの件数を報告に出す(4 つの確認は通る・§1-1 の判定は別の欄)。"""
    kw = dict(WKW, n_agents=5000)
    base, res = _record_base_res(tmp_path / "base", **kw)
    staff = np.asarray(res.runner.opening.staff_of_poi)
    assert int((staff >= 0).sum()) > 2000
    ids = _open_at_noon_on_day2()[:200]
    f = ExperimentForm.from_dict({
        "kind": "explore", "subject": {"level": "L1", "ids": ids}, "content": [{"decision": "closure"}],
        "start": NOON_DAY2_NS, "notice": {"to": ["staff"], "via": "メッセージ"},
        "question": "正午に店を休むと人の流れはどう変わるか",
        "metrics": {"primary": {"id": "calls", "path": "manifest.llm_calls_total"}},
    })
    out = BR.run_branch(f, base, runner=cli.run, run_kwargs=kw, out_dir=tmp_path / "br")
    s, ex = out.report["summary"], out.report["execution"]["branch"]
    assert s["a"] and s["b"] is True and s["d"] and s["ok"]
    assert ex["staffed_targets"] > 0 and ex["role_actions"] + ex["fallback"] > 0
    assert s["executed_by_agents"] is (ex["fallback"] == 0)
    m = out.branch.run_manifest_fields()["experiment"]
    assert m["meter"]["notices"] > 0  # 担当の従業者に「届いた情報」
