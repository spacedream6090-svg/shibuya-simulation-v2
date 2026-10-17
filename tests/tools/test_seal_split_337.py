# -*- coding: utf-8 -*-
"""第337 封印の分離の残り(回答 10-13b §7 の 5): 分けた錨のファイルと読み口の守りの試験。

検証側の錨のファイルは開かない(名と守りの語だけを見る)。値を見るのは構築側・較正側のファイルだけ。
- 構築側の写しの値が元と同じ(錨ごとの md5=分けたときに ``tools/instruments/anchor_split.py check`` で元の 1 本と
  合わせて確かめた値を固定)。
- 計器の守り(``read_guard``)と W21 の守りが分けた検証側の名を落とし、構築側の名は落とさない。
- 開いたファイルを監査フックで数える: 物差しの試験の fixture(構築側+作り物)は検証側の名を開かない。
  負の対照=検証側の名のファイルを開くとフックが数える(作り物の置き場で)。
- 中核 9 町丁目の較正側の写し 2 本(在圏の較正側・2-0 の計器の較正側)の値と単位が同じ。
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ANCH = ROOT / "docs" / "bench" / "anchors"
for sub in ("tools/instruments", "tools/w17"):
    if str(ROOT / sub) not in sys.path:
        sys.path.insert(0, str(ROOT / sub))

import anchor_split as AS  # noqa: E402
import read_guard as RG  # noqa: E402

#: 構築側の錨の md5(正規化した JSON=sort_keys)。元の 1 本の同じ錨と同じ(分けたときの check=17/17)。
BUILD_MD5 = {
    "depart_on_00_30_band_by_employment": "849d3f67d8c8974464d94c4d7062ba32",
    "song_pi_max": "3b040ec9d88e352728a00925b9adc816",
    "song_regularity_R": "ef005ea6bd4c6a5f9153787d8160054a",
    "song_top2_locations_share": "1a868982dfbc890fd8ee11f25f836c43",
    "activity_set_capacity": "f7dc9423445744a56fc7ed309ced02ee",
    "activity_set_jaccard_decay_lambda": "24b97143e9baa205267e3257fe64133a",
}
P0_PRIOR_MD5 = "72f9c8085d76c0fc3533806b2fdb823c"
VALIDATION_NAMES = ("diversity_validation_anchors_v0.json", "presence_validation_anchors_v0.json",
                    "hunger_energy_validation_anchors_v0.json")


def test_build_side_copy_equals_the_original_anchors():
    doc = json.loads((ANCH / "diversity_build_anchors_v0.json").read_text(encoding="utf-8"))
    assert {k: AS.anchor_md5(v) for k, v in doc["anchors"].items()} == BUILD_MD5
    assert AS.anchor_md5(doc["p0_prior"]) == P0_PRIOR_MD5
    assert set(BUILD_MD5) == set(AS.PLANS["diversity"].build_anchors)
    assert not (ANCH / "diversity_anchors_v0.json").exists()  # 元の 1 本は消した
    assert (ANCH / "diversity_validation_anchors_v0.json").exists()  # 名があることだけ(開かない)


def test_plan_has_a_reason_for_every_anchor_and_no_overlap():
    plan = AS.PLANS["diversity"]
    names = set(plan.build_anchors) | set(plan.validation_anchors)
    assert not (set(plan.build_anchors) & set(plan.validation_anchors))
    assert set(plan.why) == names


def test_split_doc_refuses_unknown_names():
    plan = AS.PLANS["diversity"]
    doc = {"schema": "s", "anchors": {**{k: {} for k in plan.build_anchors + plan.validation_anchors}, "new_one": {}}}
    with pytest.raises(ValueError):
        AS.split_doc(plan, doc)
    ok = {"schema": "s", "version": "v", "rules": ["r"], "p0_prior": {"values": {}},
          "anchors": {k: {"v": i} for i, k in enumerate(plan.build_anchors + plan.validation_anchors)}}
    b, v = AS.split_doc(plan, ok)
    assert set(b["anchors"]) == set(plan.build_anchors) and set(v["anchors"]) == set(plan.validation_anchors)
    assert "p0_prior" in b and "rules" in v and "rules" not in b
    assert {k: x for k, x in AS.merge(b, v).items() if k != "purpose"} == ok  # purpose は構築側に足した文


@pytest.mark.parametrize("name", VALIDATION_NAMES)
def test_gauge_guard_denies_the_validation_side(name):
    assert RG.deny_hit(ANCH / name) is not None


@pytest.mark.parametrize("name", ("diversity_build_anchors_v0.json", "presence_calib_anchors_v0.json",
                                  "hunger_energy_build_anchors_v0.json", "ssb2021_activity_prior_v0.json",
                                  "commute_time_dist_r3.json"))
def test_gauge_guard_allows_the_build_side_names(name):
    assert RG.deny_hit(ANCH / name) is None


def test_old_odpt_rt_dir_is_sealed_for_both_guards():
    from shibuya.build.pop import w21_sources as S

    assert RG.deny_hit(ROOT / "data" / "realworld" / "odpt_rt" / "2026" / "x.json.gz") is not None
    toks = [t for _r, t in S.verify_tokens()]
    assert "realworld/odpt_rt" in toks and "diversity_validation_anchors" in toks


class _Recorder:
    """監査フック: 守りの名(検証側の 3 本)を含む open を数える(名だけ)。"""

    def __init__(self):
        self.on = False
        self.hits: list[str] = []
        sys.addaudithook(self)

    def __call__(self, event, args):
        if not self.on or event != "open" or not args:
            return
        try:
            s = str(args[0]).replace("\\", "/")
        except Exception:  # pragma: no cover
            return
        if any(n.split("_v0")[0] in s for n in VALIDATION_NAMES):
            self.hits.append(s.rsplit("/", 1)[-1])


_REC = _Recorder()


def test_yardstick_fixture_reads_no_validation_file_and_the_hook_works(tmp_path):
    import diversity_yardstick as dy

    build = ANCH / "diversity_build_anchors_v0.json"
    _REC.hits.clear()
    _REC.on = True
    try:
        doc = dy.load_anchors(build)
        n_before = len(_REC.hits)
        planted = tmp_path / "diversity_validation_anchors_v0.json"  # 負の対照(作り物の置き場)
        planted.write_text("{}", encoding="utf-8")
        planted.read_text(encoding="utf-8")
    finally:
        _REC.on = False
    assert n_before == 0, _REC.hits
    assert len(_REC.hits) >= 1  # 植えた名は数えられる=フックが効いている
    assert set(doc["anchors"]) == set(BUILD_MD5)


def test_core9_calib_copies_agree():
    a = json.loads((ANCH / "presence_calib_anchors_v0.json").read_text(encoding="utf-8"))["anchors"]
    b = json.loads((ROOT / "docs" / "bench" / "instruments" / "anchor_gauge" / "calib_anchors_v0.json")
                   .read_text(encoding="utf-8"))["core9"]
    for k in ("daytime_population", "night_population", "day_night_ratio"):
        assert a[f"core9_{k}"]["value"] == b[k]["value"] and a[f"core9_{k}"]["unit"] == b[k]["unit"], k


def test_md5_helper_is_order_free():
    assert AS.anchor_md5({"a": 1, "b": 2}) == AS.anchor_md5({"b": 2, "a": 1})
    assert AS.anchor_md5({"a": 1}) == hashlib.md5(b'{"a": 1}').hexdigest()


def test_plan_tables_are_read_only():
    with pytest.raises(TypeError):
        AS.PLANS["x"] = AS.PLANS["diversity"]  # type: ignore[index]
    with pytest.raises(TypeError):
        AS.PLANS["diversity"].why["x"] = "y"  # type: ignore[index]
