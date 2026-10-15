"""第 3 期 3-3b manifest の ``experiment`` の足した欄・慣らしの規則の事前登録・技量スコアの隣の生の点数の欄・床の分布・封印の証拠。

- 設定の欄を末尾に 4 つ足した(``switch``・``start0``・``known_to_model``・``warmup``)。3-3 の欄の名と並びは変えない。申込書を
  渡さないランは ``experiment`` が null のまま。分岐でないランの ``switch`` は null。
- 慣らしの規則(``warmup.RULE``)は日付ではなく規則と parameter・印(mechanism/expedient/未リサーチ)・指紋は決定的。manifest と
  事前登録の記録に同じ記録が入る。
- 技量スコアの器の隣に生の点数の欄(値は空)・事前登録の記録に封印の証拠の欄(手元の git+公開リポへの push=値は空)。
- 床の分布(``floor_values``・``floor_summary``): A/A の対の差の分布(6 対の合成の値で平均・標準偏差が既知の値)。
- 〔検収 L5〕慣らしの規則の全部の項に印がある(印の無い項・項の無い印は無い)・刻みの数の直書きは無い。候補の数え方の宣言(R-117 の pymser の数え方とは 1 つずれる)・累計の印と慣らしの日数の定義(〔検収 M1・L3〕)が規則にある。
"""

from __future__ import annotations

import json

import pytest

from shibuya import cli
from shibuya.engine import manifest_sections as MS
from shibuya.engine.experiment import ensemble as EN
from shibuya.engine.experiment import layer as XL
from shibuya.engine.experiment import warmup as WU

from tests.engine.experiment._x33 import NS_HOUR, form, form_dict

X33_CONFIG = (
    "schema", "form_sha256", "kind", "level", "aa", "decisions", "t0_ns", "t0_step", "end_ns", "notice",
    "registration_sha256", "preregistration_sha256", "seal_sha256", "branch_t0_step", "member", "half", "aa_of",
)
KW = dict(n_agents=40, seed=1, world_dir=None, n_cells=9, ticks=240, renderer="stub", vocab_version="v3")


def test_config_keys_were_appended_and_old_ones_kept():
    assert XL.MANIFEST_CONFIG[: len(X33_CONFIG)] == X33_CONFIG
    assert XL.MANIFEST_CONFIG[len(X33_CONFIG):] == ("switch", "start0", "known_to_model", "warmup")
    assert XL.MANIFEST_OBSERVED == ("applied", "unapplied", "applied_rows", "unapplied_rows", "meter", "replay", "checks")
    for k in ("switch", "start0", "known_to_model", "warmup"):
        assert MS.section_of(f"experiment.{k}") == MS.CONFIG
        assert MS.section_of(f"experiment.{k}.anything") == MS.CONFIG


def test_manifest_fields_of_a_form_run():
    plain = cli.run(**KW)
    assert plain.run_manifest_fields()["experiment"] is None
    res = cli.run(**KW, experiment=form(start=NS_HOUR))
    m = res.run_manifest_fields()
    e = m["experiment"]
    assert list(e)[: len(XL.MANIFEST_CONFIG)] == list(XL.MANIFEST_CONFIG)
    assert e["switch"] is None and e["replay"] is None  # 分岐でないラン
    assert e["start0"]["warning"] is False and e["known_to_model"] == []
    assert e["warmup"] == WU.rule_record() and e["warmup"]["rule_sha256"] == WU.rule_sha256()
    assert MS.unlisted_in_mixed(m) == []
    assert res.final_hash == plain.final_hash  # 表を変えない申込書(合成の世界に W7 が無い)は結果を変えない


# ================================================================= 慣らしの規則
def test_warmup_rule_is_a_registered_rule_not_dates():
    r = WU.rule_record()
    assert r["registered"] == "rule_not_dates" and r["gauge"] == "tools/instruments/warmup_gauge.py"
    rule = r["rule"]
    assert rule["series"] == "difference" and rule["sensitivity_arm"] == "raw" and rule["batch_days"] == 1
    assert rule["exclude_last_batches"] == 5 and rule["invalid_if_d_over_n"] == 0.5 and rule["extend_fraction"] == 0.1
    assert rule["max_invalid"] == 3 and rule["bundle"] == "max" and rule["cumulative"] == "reject"
    assert rule["stock"] == "flow" and rule["monthly"] == "transition" and rule["min_days"] == 7
    assert rule["q1"]["pairs_min"] == 5 and rule["q1"]["lead_days"] == 28 and rule["q2"]["pairs_min"] == 6
    assert rule["q2"]["intervals"] == ["prepare", "switch", "new_normal"]
    assert r["marks"]["series"] == "expedient" and r["marks"]["min_days"] == "unresearched"
    assert r["marks"]["method"] == "mechanism" and r["marks"]["q1.pairs_min"] == "expedient"
    assert len(r["rule_sha256"]) == 64 and r["rule_sha256"] == WU.rule_sha256()
    # 日付は無い(規則だけ)
    assert "2026" not in json.dumps(r, ensure_ascii=False)
    with pytest.raises(TypeError):
        WU.RULE["max_invalid"] = 4  # type: ignore[index]



def test_every_rule_item_has_a_mark():
    items = WU.rule_items()
    assert set(items) == set(WU.MARKS)  # 印の無い項も、項の無い印も無い(〔検収 L5〕)
    assert set(WU.MARKS.values()) <= set(WU.MARK_VALUES)
    assert {WU.MARKS[k] for k in ("statistic", "q1.series", "q2.series", "q2.bounds")} <= set(WU.MARK_VALUES)
    assert "q2.fine_steps" not in items  # 刻みの数で時間を書いた直書きは消した
    r = WU.rule_record()["rule"]
    # 候補は d <= n - 5 のまま・R-117 §4-4 の pymser の数え方とは 1 つずれる宣言(未リサーチ)
    assert r["exclude_last_batches"] == 5 and "n - 6" in r["exclude_last_counting"]
    assert WU.MARKS["exclude_last_counting"] == "unresearched" and WU.MARKS["exclude_last_batches"] == "mechanism"
    # 〔検収 M1〕累計の印・〔検収 L3〕慣らしの日数の定義
    assert (r["counter"], r["counter_unmarked"], r["counter_first_day"]) == ("daily_difference", "reject", "drop")
    assert r["warmup_days"] == "first_day + d_star - head_day"

# ================================================================= 技量スコアの隣の生の点数・封印の証拠
def test_skill_container_has_raw_scores_next_to_the_skill():
    c = EN.skill_container(form())
    assert c["raw_scores"] == ["crps_fair", "rank_histogram", "spread_skill"] and "proper" in c["raw_note"]
    assert c["spread_skill_correction"] == "sqrt((M + 1) / M)"
    for m in c["metrics"].values():
        assert m["skill"] == {b: None for b in EN.SKILL_BASELINES}  # 3-3 の欄はそのまま
        assert m["raw"] == {"crps_fair": None, "baseline_crps": {b: None for b in EN.SKILL_BASELINES},
                            "rank_histogram": None, "spread_skill": None, "members": None}


def test_preregistration_has_the_evidence_slot_and_the_warmup_rule():
    ens = {"initial": 4, "model": ["mock"], "chance": 2, "aa": True, "seed0": 10}
    rec, cf = EN.preregister(form_dict(ensemble=ens), EN.seal(form(ensemble=ens)))
    ev = rec["evidence"]
    assert ev["kind"] == "git+push" and ev["git_commit"] is None and ev["pushed_to"] is None
    assert ev["third_party_timestamp"] is False
    assert rec["warmup"] == WU.rule_record()
    rec2, _ = EN.preregister(form_dict(ensemble=ens), EN.seal(form(ensemble=ens)), registered_at="2027-01-01")
    assert rec2["record_sha256"] == rec["record_sha256"]  # 時刻は指紋に入らない(3-3 と同じ)


# ================================================================= 床の分布
def _payload(calls):
    return {"manifest": {"llm_calls_total": calls}, "n_agents": 50}


def test_floor_distribution_of_aa_pairs():
    a = [100.0, 120.0, 110.0, 130.0, 90.0, 105.0]
    d = [1.0, -1.0, 2.0, 0.0, -2.0, 0.0]
    pairs = [(_payload(x), _payload(x + e)) for x, e in zip(a, d)]
    vals = EN.floor_values(form(), pairs)
    assert vals["calls"]["diff"] == d and vals["final_len"]["diff"] == [0.0] * 6
    s = EN.floor_summary(vals)
    c = s["calls"]
    assert c["n"] == 6 and c["mean"] == pytest.approx(0.0) and c["sd"] == pytest.approx((10.0 / 5) ** 0.5)
    assert c["abs_max"] == 2.0 and c["zero_share"] == pytest.approx(2 / 6) and (c["min"], c["max"]) == (-2.0, 2.0)
    assert s["final_len"]["zero_share"] == 1.0 and s["final_len"]["sd"] == 0.0
    # 道筋が無い・数でない値は None(差も None)=数えない
    miss = EN.floor_summary(EN.floor_values(form(metrics={"primary": {"id": "x", "path": "manifest.nope"}}), pairs))
    assert miss["x"]["n"] == 0 and miss["x"]["mean"] is None
    one = EN.floor_summary(EN.floor_values(form(), pairs[:1]))
    assert one["calls"]["n"] == 1 and one["calls"]["sd"] is None
