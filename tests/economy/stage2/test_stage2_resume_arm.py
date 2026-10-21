"""第 2 期 2-1 経済の段階 2: 腕と部品を状態のファイルの見出しに書き、再開で今の腕と違えば止める(検収 A5・2-2 の M1 と同じ形)。

腕は設定の指紋に入れない(``run_day`` の引数ではない)ので、指紋の検査では見つからない。見出しの ``economy_stage2``
(腕 off のランは書かない=今の見出しのまま)と今の腕・部品を突き合わせる。そろえた再開は通しのランと同じ final。
"""

from __future__ import annotations

import pytest

from shibuya.engine import economy_stage2 as ES2
from shibuya.engine import resume as RS
from shibuya.world.state import World
from tests.economy.stage2 import test_stage2_runs as TR

STOP = 1_440 + 75


@pytest.fixture
def arm(monkeypatch):
    monkeypatch.setattr(ES2, "_ARM", ES2.ARM_OFF)
    monkeypatch.setattr(ES2, "_PARTS", ES2.PARTS)
    monkeypatch.setattr(ES2, "_ATM_OVERRIDE", None)
    ES2.set_atm_table(TR._atm_everywhere(World.synthetic(n_cells=64, seed=2).n_cells))


def test_resume_stops_when_the_arm_or_parts_differ(arm, tmp_path):
    ES2.set_arm("on")
    straight, _ = TR._run(sim_days=2)
    first, _ = TR._run(sim_days=2, state_out=tmp_path / "s", stop_at_tick=STOP)
    path = tmp_path / "s" / first.resume["state_files"][-1]["file"]
    want = {"arm": "on", "parts": list(ES2.PARTS)}
    want["wage"] = ES2.wage_arm()  # 〔賃金の小さな版上げ〕見出しは賃金の道も持つ(〔第 2 部〕w17 の腕は消した)
    assert RS.read_state(path).header["economy_stage2"] == want
    ES2.set_parts(("wages", "payment"))
    with pytest.raises(ValueError, match="経済の段階 2 の腕が親と違う"):
        TR._run(sim_days=2, resume_from=path)
    ES2.set_parts(ES2.PARTS)
    ES2.set_arm("off")
    with pytest.raises(ValueError, match="経済の段階 2 の腕が親と違う"):
        TR._run(sim_days=2, resume_from=path)
    ES2.set_arm("on")
    resumed, led = TR._run(sim_days=2, resume_from=path)
    assert resumed.final_hash == straight.final_hash and led.stage2 is not None


def test_arm_off_state_files_keep_the_header_and_refuse_an_on_resume(arm, tmp_path):
    first, _ = TR._run(sim_days=2, state_out=tmp_path / "s", stop_at_tick=STOP)
    path = tmp_path / "s" / first.resume["state_files"][-1]["file"]
    assert "economy_stage2" not in RS.read_state(path).header  # 腕 off の見出しは今のまま
    ES2.set_arm("on")
    with pytest.raises(ValueError, match="経済の段階 2 の腕が親と違う"):
        TR._run(sim_days=2, resume_from=path)
    ES2.set_arm("off")
    ES2.check_resume(None)  # 見出しに無い=off と同じ
