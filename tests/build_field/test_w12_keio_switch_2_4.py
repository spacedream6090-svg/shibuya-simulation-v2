"""〔第 2 期 2-4 V1〕W12 の京王(ODPT チャレンジ枠)の切替口 ``w12_real_timetables.USE_ODPT_CHALLENGE``。

既定 True=今の実ダイヤ(京王の行を含めたまま活性化=PENDING 仮-15 のユーザーの最終の確認まで)。False=チャレンジ枠の表を
読まず、井の頭線は実データの無い線として等間隔の推定の道で作る(戻す口)。記録 ``docs/bench/analysis/wallbounce-1012/vb24``。
"""

from __future__ import annotations

import json
import shutil
from collections import Counter
from pathlib import Path

import pytest

from shibuya.build.audit import w19_freeze as W19
from shibuya.build.field import common as C
from shibuya.build.field import w12_external_nodes as w12
from shibuya.build.field import w12_real_timetables as RT
from tests import _data_ids as D

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
WORLD = DATA_DIR / "world" / "v2"
_UPSTREAM = ("w11_station_exits.parquet", "w1_nodes.parquet", "w1_edges.parquet")


def test_switch_default_reads_every_table(monkeypatch):
    assert RT.USE_ODPT_CHALLENGE is True
    assert RT.tables_in_use() == RT.USER_TABLES
    for fam in RT.INPUT_FAMILIES:
        assert RT.input_rel_paths(fam) == RT.input_rel_paths(fam, in_use=False)


def test_switch_off_drops_only_the_challenge_tables(monkeypatch):
    monkeypatch.setattr(RT, "USE_ODPT_CHALLENGE", False)
    used = RT.tables_in_use()
    assert {s.family for s in used} == {RT.FAMILY_USER}
    assert [s for s in RT.USER_TABLES if s not in used] == [
        s for s in RT.USER_TABLES if s.family == RT.FAMILY_CHALLENGE
    ]
    assert RT.input_rel_paths(RT.FAMILY_CHALLENGE) == ()
    assert RT.input_rel_paths(RT.FAMILY_CHALLENGE, in_use=False)  # 元の宣言は切替口に依らない
    assert not set(RT.input_rel_paths(RT.FAMILY_CHALLENGE, in_use=False)) & set(RT.all_input_rel_paths())
    # W19 の元の宣言(holdout の層と同じ元かの照合)は切替口に依らない
    assert W19.BUILD_INPUT_FAMILIES[RT.FAMILY_CHALLENGE] == RT.input_rel_paths(RT.FAMILY_CHALLENGE, in_use=False)


def test_w19_asset_table_follows_the_switch(tmp_path, monkeypatch):
    on = set(W19.data_asset_paths(tmp_path))
    monkeypatch.setattr(RT, "USE_ODPT_CHALLENGE", False)
    off = set(W19.data_asset_paths(tmp_path))
    challenge = set(RT.input_rel_paths(RT.FAMILY_CHALLENGE, in_use=False))
    assert challenge <= on
    assert on - off == challenge


needs_data = pytest.mark.requires_data(
    "user_timetables",
    "odpt_static",
    *D.ids_of(
        *(WORLD / n for n in _UPSTREAM),
        DATA_DIR / "odpt",
        DATA_DIR / "realworld" / "transport_census" / "station_flow_12.json",
    ),
)


def _run(tmp: Path, keio: bool, monkeypatch) -> tuple[C.StageResult, dict]:
    tmp.mkdir(parents=True, exist_ok=True)
    for n in _UPSTREAM:
        shutil.copy2(WORLD / n, tmp / n)
    monkeypatch.setattr(RT, "USE_ODPT_CHALLENGE", keio)
    res = w12.run(C.Ctx(data=DATA_DIR, out=tmp))
    return res, C.read_parquet_columns(tmp / "w12_timetables.parquet")


@needs_data
def test_switch_off_rebuilds_inokashira_by_equal_interval(tmp_path, monkeypatch):
    res_on, tt_on = _run(tmp_path / "on", True, monkeypatch)
    res_off, tt_off = _run(tmp_path / "off", False, monkeypatch)
    src_on = Counter(tt_on["source"])
    src_off = Counter(tt_off["source"])
    assert src_on[RT.SRC_KEIO] > 0 and src_off[RT.SRC_KEIO] == 0
    # 井の頭線は等間隔の推定の行だけ・ほかの線の行は同じ(出どころと本数)
    ino = [s for ln, s in zip(tt_off["line"], tt_off["source"]) if ln == "井の頭線"]
    assert ino and set(ino) == {"equal_interval_expedient"}
    others_on = Counter((ln, c, s) for ln, c, s in zip(tt_on["line"], tt_on["calendar"], tt_on["source"])
                        if ln != "井の頭線")
    others_off = Counter((ln, c, s) for ln, c, s in zip(tt_off["line"], tt_off["calendar"], tt_off["source"])
                         if ln != "井の頭線")
    assert others_on == others_off
    assert res_off.notes["equal_interval_lines"] == ["井の頭線"]
    gates = {g.name: g.to_json() for g in res_off.gates}
    assert gates["equal_interval_lines_remaining"]["value"] == 1
    assert not gates["equal_interval_lines_remaining"]["pass"]
    assert all(g.to_json()["pass"] for g in res_on.gates)
    # 等間隔の道の宣言が expedients に入る(切替口 on では入らない)
    assert set(w12.EQUAL_INTERVAL_TIMETABLE_EXPEDIENTS) <= set(res_off.expedients)
    assert not set(w12.EQUAL_INTERVAL_TIMETABLE_EXPEDIENTS) & set(res_on.expedients)
    # 方面ノードと生成の重みは動かない
    out_on = {o["path"]: o["sha256"] for o in res_on.outputs}
    out_off = {o["path"]: o["sha256"] for o in res_off.outputs}
    for name in ("w12_external_nodes.parquet", "w12_generation_weights.parquet"):
        assert out_on[name] == out_off[name]
    ver = json.loads((tmp_path / "off" / w12.VERSIONS_FILE).read_text(encoding="utf-8"))
    assert ver["lines"]["井の頭線"]["relation_to_world_time"] == "unknown"
    assert ver["lines"]["井の頭線"]["sources"] == ["equal_interval_expedient"]
    assert not {i["family"] for i in ver["inputs"]} & {RT.FAMILY_CHALLENGE}
