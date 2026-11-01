"""第 3 期 3-3 探索と確認・アンサンブルの封印・事前登録(CP14)・対の差の形・技量スコアの器。

- アンサンブル=初期状態 × モデル × 偶然(seed の 3 分割)。〔親の判断 M2〕封印の単位=初期状態: 探索の半分と確認の半分は初期状態
  を共有しない。封印の指紋は決定的(探索と確認の申込書で同じ)。
- 探索は封印した半分を読めない(``PermissionError``=負の対照)・確認は事前登録の封印の指紋が合うときだけ封印の半分を受け取る。
  ``members(form)`` は自分の半分だけ・``Seal`` は指紋と数だけ(付け替えられない)。
- 〔親の判断 M1〕封印の入口(``entrance``): 探索の申込書が封印した半分の初期状態で回ろうとすると ``ValueError``(負の対照)。
- 事前登録の記録(登録の指紋 sha256・blake3・封印の指紋・記録の指紋=時刻は入らない)。
- 対の差が ``tools/c7/salt_compare.py`` の ``--values``・``--metrics`` の形で渡り、6 対の合成の値で p(両側 2/2^6)が出る。
- 技量スコアは器だけ(値は空)・式 1 − 誤差/基準の誤差。
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from shibuya.engine.experiment import ensemble as EN
from shibuya.engine.experiment.form import ExperimentForm

from tests.engine.experiment._x33 import form, form_dict

ROOT = Path(__file__).resolve().parents[3]
ENS = {"initial": 4, "model": ["mock", "classical"], "chance": 3, "aa": True, "seed0": 10}


def _salt_compare():
    name = "salt_compare_x33"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / "c7" / "salt_compare.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def _confirm(ens=ENS):
    return EN.preregister(form_dict(ensemble=ens), EN.seal(form(ensemble=ens)))


def test_members_are_my_half_of_initial_times_model_times_chance():
    f = form(ensemble=ENS)
    s = EN.seal(f)
    assert s.n_initial == 4 and s.n_sealed_initial == 2 and s.n_members == 4 * 2 * 3
    mine = EN.members(f)
    assert len(mine) == 2 * 2 * 3  # 探索の半分(封印していない初期状態 2 つ × モデル 2 × 偶然 3)
    m = mine[0]
    assert (m.population_seed, m.environment_seed) == (10 + m.initial, 10 + m.initial) and m.seed == 10 + m.chance
    assert m.run_kwargs() == {"seed": m.seed, "population_seed": m.population_seed,
                              "environment_seed": m.environment_seed, "experiment_model": m.model}
    _rec, cf = _confirm()
    theirs = EN.members(cf)
    assert len(theirs) == 12
    # 〔M2〕初期状態を共有しない・モデルと偶然は各半分の中で組む
    assert not ({x.initial for x in mine} & {x.initial for x in theirs})
    assert {(x.model, x.chance) for x in mine} == {(x.model, x.chance) for x in theirs}


def test_seal_is_deterministic_and_exposes_only_fingerprints():
    f = form(ensemble=ENS)
    a, b = EN.seal(f), EN.seal(ExperimentForm.from_json(f.to_json()))
    assert a.sealed_sha256 == b.sealed_sha256 and len(a.sealed_sha256) == 64
    assert not hasattr(a, "_sealed") and not hasattr(a, "open")  # 封印の一覧を持たない
    with pytest.raises(AttributeError):
        a.sealed_sha256 = "0" * 64  # type: ignore[misc]
    rec = EN.seal_record(a, f)
    assert rec["unit"] == "initial" and rec["sealed_sha256"] == a.sealed_sha256 and rec["n_sealed_initial"] == 2
    assert len(rec["open"]) == 12 and "sealed" not in rec
    # 問いや改変が違ってもアンサンブルが同じなら同じ封印(探索と確認で同じ半分を指す)
    other = form(ensemble=ENS, question="別の問い", content=[{"decision": "event"}])
    assert EN.seal(other).sealed_sha256 == a.sealed_sha256
    assert EN.seal(form(ensemble={**ENS, "seed0": 11})).sealed_sha256 != a.sealed_sha256
    assert EN.seal(form()).n_sealed_initial == 0  # 初期状態 1 つは封印が空(確認には 2 つ以上要る)


def test_explore_cannot_read_the_sealed_half():
    f = form(ensemble=ENS)
    s = EN.seal(f)
    assert s.members_for(f) == EN.members(f)
    with pytest.raises(PermissionError, match="探索は封印"):
        s.members_for(f, half="confirm")


def test_confirm_with_the_matching_preregistration_gets_the_sealed_half():
    rec, cf = _confirm()
    s = EN.seal(cf)
    assert cf.kind == "confirm" and cf.preregistration["seal_sha256"] == s.sealed_sha256
    assert rec["registration_sha256"] == cf.registration_digest() == cf.preregistration["registration_sha256"]
    assert len(rec["registration_blake3"]) == 64 and rec["seal_sha256"] == s.sealed_sha256
    with pytest.raises(PermissionError, match="確認のランは封印"):
        s.members_for(cf, half="explore")
    rec2, _ = EN.preregister(form_dict(ensemble=ENS), s, registered_at="2027-01-01T00:00:00+09:00")
    assert rec2["record_sha256"] == rec["record_sha256"]  # 時刻は指紋に入らない
    json.dumps(rec, ensure_ascii=False)  # 公開の記録に書ける JSON
    assert all(v is None for m in rec["skill"]["metrics"].values() for v in m["skill"].values())
    other = EN.seal(form(ensemble={**ENS, "seed0": 99}))
    with pytest.raises(ValueError, match="アンサンブル"):
        other.members_for(cf)


# ================================================================= 封印の入口(〔親の判断 M1〕)
def _seeds(m: EN.Member) -> dict:
    return {"seed": m.seed, "population_seed": m.population_seed, "environment_seed": m.environment_seed}


def test_entrance_lets_each_form_run_only_its_half():
    f = form(ensemble=ENS)
    _rec, cf = _confirm()
    mine, theirs = EN.members(f), EN.members(cf)
    m, half = EN.entrance(f, **_seeds(mine[0]), model=mine[0].model)
    assert m == mine[0] and half == EN.HALF_EXPLORE
    m2, half2 = EN.entrance(cf, **_seeds(theirs[0]), model=theirs[0].model)
    assert m2 == theirs[0] and half2 == EN.HALF_CONFIRM
    # 負の対照: 探索の申込書が封印した半分の初期状態で回る・確認の申込書が探索の半分で回る
    with pytest.raises(ValueError, match="封印した半分"):
        EN.entrance(f, **_seeds(theirs[0]), model=theirs[0].model)
    with pytest.raises(ValueError, match="封印した半分の初期状態だけ"):
        EN.entrance(cf, **_seeds(mine[0]), model=mine[0].model)
    with pytest.raises(ValueError, match="メンバーでない"):
        EN.entrance(f, seed=999, population_seed=10, environment_seed=10, model="mock")
    with pytest.raises(ValueError, match="モデルの札"):
        EN.entrance(f, **_seeds(mine[0]))  # 札が 2 つあるのに渡さない
    assert EN.entrance(form(), seed=1, population_seed=1, environment_seed=1)[1] == EN.HALF_EXPLORE


def _payload(calls: float, n: int) -> dict:
    return {"n_agents": n, "manifest": {"llm_calls_total": calls}}


def test_paired_values_go_to_salt_compare_and_give_a_p():
    sc = _salt_compare()
    f = form()
    base = [100.0, 120.0, 110.0, 130.0, 90.0, 105.0]
    arm = [b + d for b, d in zip(base, (3.0, 5.0, 2.0, 7.0, 4.0, 1.0))]
    pairs = [(_payload(b, 50), _payload(a, 50)) for b, a in zip(base, arm)]
    vals = EN.paired_values(f, pairs)
    assert vals["calls"] == {"base": base, "arm": arm}
    spec = EN.metrics_spec(f)
    assert spec["primary"] == {"id": "calls", "path": "manifest.llm_calls_total", "preregistered": False}
    out = sc.analyze(vals, spec)
    r = out["metrics"]["calls"]
    assert r["n_pairs"] == 6 and r["p"] == pytest.approx(2 / 64) and r["status"] == sc.TESTED and r["decision"] is True
    assert EN.pairs_status(6)["ok"] and EN.pairs_status(6)["p_floor"] == pytest.approx(2 / 64)
    out3 = sc.analyze(EN.paired_values(f, pairs[:3]), spec)
    assert out3["metrics"]["calls"]["status"] == sc.DESCRIPTIVE and not EN.pairs_status(3)["ok"]
    assert not EN.pairs_status(5)["ok"] and EN.pairs_status(5, one_sided=True)["ok"]


def test_skill_score_is_a_container_with_a_formula():
    c = EN.skill_container(form())
    assert c["baselines"] == ["last_year_same_day", "mean", "previous_week"]
    assert set(c["metrics"]) == {"calls", "final_len"}
    assert all(v["error"] is None for v in c["metrics"].values())
    assert EN.skill_score(1.0, 2.0) == pytest.approx(0.5) and EN.skill_score(3.0, 2.0) == pytest.approx(-0.5)
    with pytest.raises(ValueError):
        EN.skill_score(1.0, 0.0)
