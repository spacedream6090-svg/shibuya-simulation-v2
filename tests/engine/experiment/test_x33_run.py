"""第 3 期 3-3 申込書をランに置く口(``layer.staged`` → 組み立て → 系 ``experiment``)・使わないとき不変・ランの種類・再開・宣言。

- 申込書を渡さないラン: 系 ``experiment`` は立たない(呼ばれない)・manifest の ``experiment`` は null。
- A/A(改変が空)・効かせていない改変・告知だけの申込書は final と全 checkpoint を変えない(控えの行 X と出来事の記録は診断)。
- ランの種類: 申込書を渡した ``cli.run`` は ``counterfactual``(試験 > 反実仮想 > 腕 > 再現)。指紋には入れない。
- 再開: 申込書つきのランの状態の見出しに申込書の指紋。違う申込書・申込書なしの再開は止める。基準のラン(申込書なし)からの
  分岐は通す。
- 書きの宣言(段 B): 系 ``experiment`` の差 ⊆ 宣言(``X:experiment.*``・``E:events.*``)・宣言を外すと見つかる(負の対照)。
- manifest の節の表の子の鍵=``layer.MANIFEST_CONFIG``・``MANIFEST_OBSERVED``。状態台帳の行 X はどちらのハッシュにも入らない。
"""

from __future__ import annotations

import json

import pytest

from shibuya import cli
from shibuya.core import write_permit as WP
from shibuya.engine import manifest_sections as MS
from shibuya.engine import run_kind as RK
from shibuya.engine import state_ledger as SL
from shibuya.engine.experiment import layer as XL
from shibuya.engine.run import run_day
from shibuya.engine.systems import conductor as CD
from shibuya.engine.systems import overrides as OV
from shibuya.engine.systems import probe as PR
from shibuya.engine.systems.table import SPECS

from tests.engine.experiment._x33 import NS_HOUR, form

T0_NS = 10 * NS_HOUR
KW = dict(n_agents=60, seed=1, ticks=1440, n_cells=9, renderer="stub", checkpoint_every=120)


def _cps(res):
    return [(c.tick, c.behavior_hash, c.full_hash) for c in res.checkpoints]


@pytest.fixture(scope="module")
def plain():
    return run_day(**KW)


def _run(f, **kw):
    with XL.staged(f):
        return run_day(**{**KW, **kw})


def test_no_form_no_system_and_null_manifest(plain, monkeypatch):
    assert plain.run_manifest_fields()["experiment"] is None and plain.experiment_layer is None
    assert CD.WHEN["experiment"](type("B", (), {"layers": type("L", (), {"experiment": None})()})()) is False
    # 申込書を渡さないランでは系 experiment を呼ばない(呼ばれたら落ちる関数に差し替えても通る)
    import dataclasses

    boom = dataclasses.replace(SPECS["experiment"], fn=lambda ctx, b: (_ for _ in ()).throw(AssertionError("呼んだ")))
    from shibuya.engine.systems import table as TB

    monkeypatch.setattr(TB, "SYSTEMS", tuple(boom if s.name == "experiment" else s for s in TB.SYSTEMS))
    again = run_day(**KW)
    assert again.final_hash == plain.final_hash


@pytest.mark.parametrize("over", [
    dict(),                                                                  # A/A(改変が空)
    dict(content=[{"decision": "closure"}]),                                 # 合成の世界に W7 が無い=効かせていない
    dict(content=[{"decision": "event"}], notice={"to": [1, 2], "via": "メッセージ"}),  # 決定と告知の行だけ
    dict(subject={"level": "L4", "ids": []}, content=[{"decision": "visitors", "scale": 2.0}]),  # 宣言して未実装
], ids=["aa", "closure_no_w7", "event_notice", "l4_declared"])
def test_forms_that_change_no_table_keep_every_checkpoint(plain, over):
    f = form(start=T0_NS, **over)
    f = f.aa() if not over else f
    res = _run(f)
    assert _cps(res) == _cps(plain) and res.final_hash == plain.final_hash
    m = res.run_manifest_fields()["experiment"]
    assert m["form_sha256"] == f.sha256() and m["t0_step"] == 600 and m["kind"] == "explore"
    assert m["aa"] is (not f.content) and m["checks"] is None and m["replay"] is None
    assert MS.unlisted_in_mixed(res.run_manifest_fields()) == []
    if over.get("notice"):
        evs = [e for e in res.event_log.events() if e.what.startswith("実験:")]
        assert [e.what for e in evs] == ["実験:改変", "実験:届いた情報", "実験:届いた情報"] and m["applied"] == 1
    if over.get("content") == [{"decision": "closure"}]:
        assert m["unapplied"] == 1 and m["unapplied_rows"][0]["reason_key"] == "no_w7"


def test_a_form_that_starts_after_the_run_is_out_of_period():
    res = _run(form(start=3 * 24 * NS_HOUR))
    m = res.run_manifest_fields()["experiment"]
    assert m["applied"] == 0 and [r["reason_key"] for r in m["unapplied_rows"]] == ["not_started"]


def test_manifest_section_keys_match_the_layer():
    cfg = sorted(k.split(".", 1)[1] for k, v in MS.PATHS.items() if k.startswith("experiment.") and v == MS.CONFIG)
    obs = sorted(k.split(".", 1)[1] for k, v in MS.PATHS.items() if k.startswith("experiment.") and v == MS.OBSERVED)
    assert cfg == sorted(XL.MANIFEST_CONFIG) and obs == sorted(XL.MANIFEST_OBSERVED)
    assert MS.PATHS["experiment"] == MS.OBSERVED and "experiment" in MS.MIXED


def test_ledger_row_x_enters_no_hash():
    r = SL.row("X")
    assert (r.behavior, r.restore) == (SL.DIAG, SL.DISCARDABLE) and r.items == ("experiment.handle", "experiment.xchecks")
    paths = {p for _k, p in SL.full_items()} | {p for _k, p in SL.behavior_items()}
    assert not any(p.startswith("experiment.") for p in paths)
    assert SL.OWNER_CLASSES["experiment"] == ("engine/experiment/layer.py", "ExperimentLayer")


# ================================================================= ランの種類
def test_run_kind_rule():
    assert RK.decide(arms_on=False, testing=False, counterfactual=True) == RK.COUNTERFACTUAL
    assert RK.decide(arms_on=True, testing=False, counterfactual=True) == RK.COUNTERFACTUAL
    assert RK.decide(arms_on=True, testing=True, counterfactual=True) == RK.TEST
    assert RK.decide(arms_on=False, testing=False) == RK.REPRODUCTION


def test_cli_run_with_a_form_is_counterfactual(monkeypatch, tmp_path):
    p = tmp_path / "form.json"
    f = form(start=T0_NS)
    p.write_text(f.to_json(), encoding="utf-8")
    monkeypatch.delenv(RK.PYTEST_ENV, raising=False)
    kw = dict(n_agents=40, seed=1, world_dir=None, n_cells=9, ticks=720, renderer="stub", vocab_version="v3")
    base = cli.run(**kw)
    res = cli.run(**kw, experiment=str(p))
    assert base.run_kind == RK.ARM and res.run_kind == RK.COUNTERFACTUAL  # 描画 stub は腕=反実仮想が腕より先
    m = res.run_manifest_fields()
    assert m["run_kind"] == RK.COUNTERFACTUAL and m["experiment"]["form_sha256"] == f.sha256()
    aa = cli.run(**kw, experiment=f, experiment_aa=True)
    assert aa.run_manifest_fields()["experiment"]["aa"] is True and aa.final_hash == base.final_hash
    with pytest.raises(ValueError, match="申込書"):
        cli.run(**kw, experiment_aa=True)


def test_cli_main_flags(tmp_path, monkeypatch):
    seen: dict = {}

    class _Stub:
        def summary(self):
            return "(stub)"

        fleet_fields: dict = {}
        ledger = None

    monkeypatch.setattr(cli, "run", lambda **kw: (seen.update(kw), _Stub())[1])
    p = tmp_path / "f.json"
    p.write_text(form().to_json(), encoding="utf-8")
    assert cli.main(["--world", "__no_such_dir__"]) == 0 and "experiment" not in seen  # 既定は欄を足さない
    seen.clear()
    assert cli.main(["--world", "__no_such_dir__", "--experiment", str(p), "--experiment-aa"]) == 0
    assert seen["experiment"] == str(p) and seen["experiment_aa"] is True
    with pytest.raises(SystemExit):
        cli.main(["--world", "__no_such_dir__", "--experiment-aa"])
    with pytest.raises(SystemExit):
        cli.main(["--world", "__no_such_dir__", "--experiment-branch", str(tmp_path)])


# ================================================================= 再開(見出しの申込書の指紋)
def test_state_header_and_resume_checks(tmp_path):
    kw = dict(KW, sim_days=2)
    f = form(start=T0_NS, content=[{"decision": "event"}])
    _run(f, sim_days=2, state_out=tmp_path / "s")
    side = json.loads((tmp_path / "s" / "state-T00001440.json").read_text(encoding="utf-8"))
    assert side["experiment"] == {"form_sha256": f.sha256(), "t0_step": 600}
    st = tmp_path / "s" / "state-T00001440.npz"
    with pytest.raises(ValueError, match="申込書の指紋が違う"):
        _run(form(start=T0_NS, content=[{"decision": "event"}], question="別の問い"), sim_days=2, resume_from=st)
    with pytest.raises(ValueError, match="申込書なしで再開しない"):
        run_day(**kw, resume_from=st)
    res = _run(f, sim_days=2, resume_from=st)  # 同じ申込書=引き継ぐ(決定の行は親のラン)
    m = res.run_manifest_fields()["experiment"]
    assert m["applied"] == 0 and m["unapplied"] == 0 and res.experiment_layer.handle.inherited
    # 基準のラン(申込書なし)の状態からの分岐は通す(始まりが再開の時刻より前の決定は期間の外)
    run_day(**kw, state_out=tmp_path / "b")
    br = _run(f, sim_days=2, resume_from=tmp_path / "b" / "state-T00001440.npz")
    assert [r["reason_key"] for r in br.run_manifest_fields()["experiment"]["unapplied_rows"]] == ["before_begin"]
    plain_head = json.loads((tmp_path / "b" / "state-T00001440.json").read_text(encoding="utf-8"))
    assert "experiment" not in plain_head  # 申込書の無いランの見出しは今のまま


# ================================================================= 書きの宣言(段 B)
def _probe_run(check, **over):
    pr = PR.Probe(check=check, ticks=frozenset({599, 600, 601}))
    PR.ACTIVE = pr
    try:
        _run(form(start=T0_NS, content=[{"decision": "event"}], notice={"to": [1], "via": "メッセージ"}), **over)
    finally:
        PR.ACTIVE = None
    return pr


def test_experiment_writes_are_within_the_declaration():
    pr = _probe_run(CD.declared_check(SPECS))
    assert pr.n_snap > 0 and not pr.violations, pr.violations[:10]
    mine = [keys for t, s, _d, keys in pr.entries if s == "experiment"]
    assert mine and any(k.startswith("X:experiment.") for k in mine[0]) and any(k.startswith("E:") for k in mine[0])


def test_undeclared_experiment_write_shows_in_stage_b():
    """負の対照: 系 experiment の宣言から X:experiment.* を外すと、段 B が宣言の外の書きとして見つける。"""
    prev = WP.enabled()
    WP.set_enabled(False)
    try:
        with OV.drop_path("experiment", "X:experiment.*"):
            pr = _probe_run(CD.declared_check(SPECS))
    finally:
        WP.set_enabled(prev)
    bad = [(t, s, k) for t, s, k in pr.violations if k.startswith("X:")]
    assert bad and all(s == "experiment" for _t, s, _k in bad), pr.violations[:5]


def test_runtime_owner_instance_is_fully_declared():
    """状態台帳の網羅(10b-2・検収 2-6 の実行時の形): 申込書の持ち主のインスタンスの属性は行 X の道筋か除外の一覧にある。"""
    from shibuya.engine import state_ledger_ast as SA

    res = _run(form(start=T0_NS, content=[{"decision": "event"}]))
    layer = res.experiment_layer
    assert type(layer).__name__ == "ExperimentLayer"
    assert SA.runtime_uncovered({"experiment": layer}) == {}
    layer.new_state_x33 = 1  # 負の対照: 宣言の無い属性は見つかる
    assert SA.runtime_uncovered({"experiment": layer}) == {"experiment": ["new_state_x33"]}


# ================================================================= 〔検収 M4〕持ち主の守り
def test_owner_fields_cannot_be_replaced_and_checks_are_written_once():
    res = _run(form(start=T0_NS, content=[{"decision": "event"}]))
    layer = res.experiment_layer
    for name in ("form", "handle", "branch", "xchecks", "t0_step", "member", "half"):
        with pytest.raises(AttributeError, match="付け替えられない"):
            setattr(layer, name, None)
        with pytest.raises(AttributeError, match="消せない"):
            delattr(layer, name)
    layer.record_checks({"ok": True, "a": True})
    assert res.run_manifest_fields()["experiment"]["checks"] == {"ok": True, "a": True}
    with pytest.raises(AttributeError, match="1 回だけ"):
        layer.record_checks({"ok": False})
    with pytest.raises(TypeError):
        layer.xchecks["ok"] = False  # type: ignore[index]


# ================================================================= 〔親の判断 M1〕封印の入口(ランで効く)
ENS2 = {"initial": 4, "model": ["mock"], "chance": 2, "seed0": 1}


def test_the_seal_is_enforced_at_the_run_entrance():
    from shibuya.engine.experiment import ensemble as EN

    f = form(start=T0_NS, content=[{"decision": "event"}], ensemble=ENS2)
    mine = EN.members(f)
    _rec, cf = EN.preregister(dict(f.to_dict(), kind="confirm"), EN.seal(f))
    theirs = EN.members(cf)
    m = mine[0]
    res = _run(f, seed=m.seed, population_seed=m.population_seed, environment_seed=m.environment_seed)
    got = res.run_manifest_fields()["experiment"]
    assert got["member"] == m.to_dict() and got["half"] == "explore"
    # 負の対照: 探索の申込書が封印した半分の初期状態で回ろうとすると、世界を触る前に止まる
    t = theirs[0]
    with pytest.raises(ValueError, match="封印した半分"):
        _run(f, seed=t.seed, population_seed=t.population_seed, environment_seed=t.environment_seed)
    with pytest.raises(ValueError, match="メンバーでない"):
        _run(f, seed=99)
    # 確認の申込書は封印した半分だけで回る
    res2 = _run(cf, seed=t.seed, population_seed=t.population_seed, environment_seed=t.environment_seed)
    assert res2.run_manifest_fields()["experiment"]["half"] == "confirm"
    with pytest.raises(ValueError, match="封印した半分の初期状態だけ"):
        _run(cf, seed=m.seed, population_seed=m.population_seed, environment_seed=m.environment_seed)
