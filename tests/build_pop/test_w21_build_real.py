"""W21 を実データで組む(``requires_data("world_v2")``+W21 の材料=無ければ飛ばす)。

- 2 回組んで 6 本(4 本+manifest+見出し)の sha256 が一致・seed を変えると人が変わる(枠は変わらない)。
- 計器の値(golden は記録 pop41/README.md)・全員が別人・家族の整合・詰め on/off の誤差の差。
- 枠は都市圏の私事と業務の来街が空欄・検証側の値を書かない・材料はすべて構築側・PT を開かない。
- 既定は不変: W21 は ``build.run`` の段に入らない・本体の v2 に W21 の資産を書かない。
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import pytest

from shibuya.build import run as build_run
from shibuya.build.pop import STAGES as POP_STAGES
from shibuya.build.pop import w21_build as W
from shibuya.build.pop import w21_frame as WF
from shibuya.build.pop import w21_households as H
from shibuya.build.pop import w21_sources as S

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "data"
FILES = (*W.OUTPUTS, W.MANIFEST_NAME, "W21.header.json")

pytestmark = pytest.mark.requires_data("world_v2")

#: golden(記録 pop41/README.md §決定性・seed 20260909・詰め on)。
GOLDEN = {
    "persons": 42642, "households": 28290, "general_households": 27751, "institution_persons": 539,
    "foreign_persons": 3559, "stage_chome": 42,
}
GOLDEN_BUILD_HASH = "ca823451cad3f57b5a2636b65a6cc94806e9a62f9b7a9b7dd6546370c97f00c0"


def _need_sources() -> None:
    for s in S.SOURCES:
        for parts in (s.path, s.derived):
            if parts and not DATA.joinpath(*parts).exists():
                pytest.skip(f"requires_data: W21 の材料が無い({'/'.join(parts[:2])})")


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    _need_sources()
    out = tmp_path_factory.mktemp("w21a")
    _res, man = W.build(DATA, out)
    return out, man


def test_two_builds_are_byte_identical(built, tmp_path):
    out, man = built
    W.build(DATA, tmp_path)
    for f in FILES:
        assert _sha(out / f) == _sha(tmp_path / f), f


def test_seed_changes_people_but_not_the_frame(built, tmp_path):
    out, _ = built
    W.build(DATA, tmp_path, seed=W.DEFAULT_SEED + 1)
    assert _sha(out / "w21_persons.parquet") != _sha(tmp_path / "w21_persons.parquet")
    assert _sha(out / "w21_frame.json") == _sha(tmp_path / "w21_frame.json")


def test_golden_counts_and_build_hash(built):
    _, man = built
    assert man["counts"] == GOLDEN
    assert man["w21_build_hash"] == GOLDEN_BUILD_HASH
    assert man["population_seed"] == W.DEFAULT_SEED and man["stage_version"] == "1.0.0"


def test_everyone_is_distinct_and_families_are_consistent(built):
    out, _ = built
    c = json.loads((out / "w21_checks.json").read_text(encoding="utf-8"))
    u, f = c["uniqueness"], c["family"]
    for k in ("person_id_duplicates", "household_member_duplicates", "households_without_exactly_one_head",
              "households_with_two_or_more_spouses", "synthetic"):
        assert u[k] == 0, k
    for k in ("children_older_than_a_parent", "children_parent_gap_under_15", "parents_younger_than_head",
              "parents_gap_under_15", "heads_under_15", "grandchildren_gap_under_30", "grandparents_gap_under_30",
              "child_spouses_gap_under_15"):
        assert f[k] == 0, k
    assert f["grandchildren"] > 0  # 孫の行があって、どれも世帯主と 30 歳以上離れている〔検収 L2〕
    assert c["draw_fallbacks"]["window_empty"] == 0
    p = pq.read_table(out / "w21_persons.parquet", columns=["person_id", "household_id", "synthetic"])
    assert np.array_equal(np.asarray(p.column("person_id")), np.arange(p.num_rows))
    # 世帯の表と人の表の人数がそろう
    h = pq.read_table(out / "w21_households.parquet", columns=["household_id", "size"])
    assert int(np.asarray(h.column("size")).sum()) == p.num_rows


def test_anneal_on_off_arms(built, tmp_path):
    out, man = built
    _r, off = W.build(DATA, tmp_path, anneal=H.AnnealParams(enabled=False))
    assert off["anneal"]["error_after"] == off["anneal"]["error_before"]
    assert man["anneal"]["error_before"] == off["anneal"]["error_before"]
    assert man["anneal"]["error_after"] < 0.7 * off["anneal"]["error_after"]


def test_distribution_check_is_recorded_for_every_table(built):
    out, _ = built
    d = json.loads((out / "w21_checks.json").read_text(encoding="utf-8"))["distribution"]
    assert {"t03_age16_sex", "t04_marital3_sex", "t05_2_household_size", "t06_1_family_group", "t07_1_tenure",
            "t08_1_building_type", "attr_labour_status", "attr_emp_status", "attr_industry_major",
            "attr_occupation_major", "attr_workplace_kind", "attr_school_kind", "attr_school_place",
            "attr_residence_period"} == set(d)
    assert d["t05_2_household_size"]["stage_srmse"] < 0.01 and d["t06_1_family_group"]["stage_srmse"] < 0.01


def test_frame_blanks_and_no_verify_side_values(built):
    out, _ = built
    raw = (out / "w21_frame.json").read_text(encoding="utf-8")
    fr = json.loads(raw)
    assert "visitors_metro_private_business" in fr["blank_layers"]
    row = next(r for r in fr["rows"] if r["layer"] == "visitors_metro_private_business")
    assert row["value"] is None and row["mark"] == "空欄"
    for term in WF.FORBIDDEN_TERMS:
        assert term not in raw, term
    assert {r["mark"] for r in fr["rows"]} <= {"計算", "引", "空欄"}


def test_materials_are_build_side_and_pt_is_never_opened(built):
    _, man = built
    assert man["sources"] and all(s["side"] == "build" for s in man["sources"])
    toks = [t for _row, t in S.verify_tokens()]
    for rel in man["opened"]:
        assert not any(t in rel.lower() for t in toks), rel
        assert "pt2018" not in rel and "pt6_" not in rel
    # 〔検収 L8〕検証側の行は id だけ(説明文は資産に書かない)
    assert man["verify_side_rows"] == [r.row for r in S.VERIFY_SIDE]


def test_default_build_is_unchanged():
    assert "W21" not in build_run.ALL_STAGES and POP_STAGES == ("W16",)
    # 〔検収 M1〕--out が本体の v2 なら何も書かずに止める
    before = sorted(p.name for p in (DATA / "world" / "v2").iterdir())
    assert W.main(["--out", str(DATA / "world" / "v2"), "--data", str(DATA)]) == 2
    assert sorted(p.name for p in (DATA / "world" / "v2").iterdir()) == before
    assert not list((DATA / "world" / "v2").glob("w21_*")) and not (DATA / "world" / "v2" / "W21.header.json").exists()
