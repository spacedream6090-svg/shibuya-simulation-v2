"""第 2 期 2-1 経済の段階 2: 腕 on のランの再開(10d)=通しのランと同じ(段階 2 の中身は組み立てで作り直す・預金は帳簿の残高
O57 で戻す・計器は 0 から)。

世界資産の 300 体・2 日(開始日 2026-08-24=1 日目が給料日)。日の境目(1,440)と 1 日目の昼(2,190)で止めて再開し、final・
日の終わりの 2 つのハッシュ・帳簿の残高・保存則の検算(日の境目なら段階 2 の日の欄も)が通しのランと同じ。300 体の母集団の
抽出には雇用の行が無い(賃金は 0=給料日の印だけ。〔検収 A9〕10e の二層抽出は定員先取り層(乗務員・職務者 273・指令 10)を先に
取り、統計層は居住者 17 だけ=W16 の org_id を持つ通勤者と従業者が 0 体)。``slow``・data が要る。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.economy.accounts import BalanceLine, Sector
from shibuya.engine import economy_stage2 as ES2

pytestmark = [pytest.mark.slow,
              pytest.mark.requires_data("world_v2:w17_schedule.parquet", "osm:poi_tags_overpass_20260928.json",
                                        "calendar")]

KW = dict(n_agents=300, seed=1, world_dir="data/world/v2", sim_days=2, vocab_version="v3",
          start_sim_datetime="2026-08-24", checkpoint_every=360)


@pytest.mark.parametrize("stop", [1_440, 2_190])
def test_resume_equals_straight_with_the_arm(tmp_path, monkeypatch, stop):
    from shibuya import cli

    monkeypatch.setattr(ES2, "_ARM", ES2.ARM_ON)
    monkeypatch.setattr(ES2, "_PARTS", ES2.PARTS)
    monkeypatch.setattr(ES2, "_ATM_OVERRIDE", None)
    straight = cli.run(**KW)
    a = cli.run(state_out=tmp_path / "s", stop_at_tick=stop, **KW)
    b = cli.run(resume_from=tmp_path / "s" / a.resume["state_files"][-1]["file"], **KW)
    assert b.final_hash == straight.final_hash
    want = [(d["day"], d.get("state_hashes_end_of_day")) for d in straight.daily if int(d["end_T"]) > stop]
    got = [(d["day"], d.get("state_hashes_end_of_day")) for d in b.daily if int(d["end_T"]) > stop]
    assert got == want
    for line in (BalanceLine.CASH, BalanceLine.DEPOSIT):
        for s in Sector:
            assert np.array_equal(np.asarray(b.ledger.money.balance(line, s)),
                                  np.asarray(straight.ledger.money.balance(line, s))), (line, s)
    assert b.ledger.money.stage2 is not None
    # 保存則の検算(締めの日の流れの表は O77 で戻る)は止めた位置によらず同じ・日の境目で止めたら段階 2 の日の欄も同じ
    s_days = {int(d["day"]): d["economy"] for d in straight.daily}
    for d in b.daily:
        assert d["economy"]["conservation"] == s_days[int(d["day"])]["conservation"]
        assert d["economy"]["conservation"]["ok"] is True
        if stop % 1_440 == 0:
            assert d["economy"]["stage2"] == s_days[int(d["day"])]["stage2"]
    assert [d["economy"]["stage2"]["payday"] for d in straight.daily] == [False, True]
    assert straight.ledger.money.stage2.s2_meter["run"]["endow"]["deposit_rows"] > 0
