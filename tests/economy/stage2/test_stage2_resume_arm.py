"""第 2 期 2-1 経済の段階 2: 腕と部品を状態のファイルの見出しに書き、再開で今の腕と違えば止める(検収 A5・2-2 の M1 と同じ形)。

腕は設定の指紋に入れない(``run_day`` の引数ではない)ので、指紋の検査では見つからない。見出しの ``economy_stage2``
(腕 off のランは書かない=今の見出しのまま)と今の腕・部品を突き合わせる。そろえた再開は通しのランと同じ final。

〔第347 止めた切替口の削除〕切替口 off の代わりに、段階 2 の外の台帳(段階 2 の口を持たない=試験の中だけの束
``tests/economy/_stage2_outside.py``・手順 0 で off と同じ値を確かめた=記録 ``docs/bench/analysis/switch-removal-347/README.md``)で
腕の食い違いを作る(再開の検査は台帳が段階 2 の口を持つか=``effective`` で今の腕を決める)。
"""

from __future__ import annotations

import pytest

from shibuya.economy import stage2_bind as ES2
from shibuya.runtime.state import resume as RS
from shibuya.world.model.state import World
from tests.economy.stage2 import test_stage2_runs as TR

STOP = 1_440 + 75


@pytest.fixture
def arm(monkeypatch):
    monkeypatch.setattr(ES2, "_PARTS", ES2.PARTS)
    monkeypatch.setattr(ES2, "_ATM_OVERRIDE", None)
    ES2.set_atm_table(TR._atm_everywhere(World.synthetic(n_cells=64, seed=2).n_cells))


def test_resume_stops_when_the_arm_or_parts_differ(arm, tmp_path):
    straight, _ = TR._run(sim_days=2)
    first, _ = TR._run(sim_days=2, state_out=tmp_path / "s", stop_at_tick=STOP)
    path = tmp_path / "s" / first.resume["state_files"][-1]["file"]
    want = {"arm": "on", "parts": list(ES2.PARTS)}
    want["wage"] = ES2.wage_arm()  # 〔賃金の小さな版上げ〕見出しは賃金の道も持つ(〔第 2 部〕w17 の腕は消した)
    # 〔第 4 期 4-2・4-2b〕見出しは規則の表の中身と空欄 3 件を埋めた値も持つ(〔第346〕切替口 SHIBUYA_RULES_42・42B は消した)
    want["rules_42"] = "on"
    want["rules_42b"] = "on"
    assert RS.read_state(path).header["economy_stage2"] == want
    ES2.set_parts(("wages", "payment"))
    with pytest.raises(ValueError, match="経済の段階 2 の腕が親と違う"):
        TR._run(sim_days=2, resume_from=path)
    ES2.set_parts(ES2.PARTS)
    # 〔第347〕前は切替口 off で再開した=段階 2 の外の台帳で再開する(今の腕は off と同じ)
    with pytest.raises(ValueError, match="経済の段階 2 の腕が親と違う"):
        TR._run(sim_days=2, resume_from=path, outside=True)
    resumed, led = TR._run(sim_days=2, resume_from=path)
    assert resumed.final_hash == straight.final_hash and led.stage2 is not None


def test_state_files_outside_stage2_keep_the_header_and_refuse_a_stage2_resume(arm, tmp_path):
    """〔第347〕前は切替口 off のラン(``test_arm_off_state_files_keep_the_header_and_refuse_an_on_resume``)。段階 2 の外の台帳の
    ランで同じことを見る。"""
    first, _ = TR._run(sim_days=2, state_out=tmp_path / "s", stop_at_tick=STOP, outside=True)
    path = tmp_path / "s" / first.resume["state_files"][-1]["file"]
    assert "economy_stage2" not in RS.read_state(path).header  # 段階 2 の外のランの見出しは今のまま
    with pytest.raises(ValueError, match="経済の段階 2 の腕が親と違う"):
        TR._run(sim_days=2, resume_from=path)
    ES2.check_resume(None, effective=False)  # 見出しに無い=段階 2 の外の台帳(off と同じ)どうし
