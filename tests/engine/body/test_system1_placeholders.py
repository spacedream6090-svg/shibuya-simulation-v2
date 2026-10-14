"""第 3 期 3-5: 器だけの 3 件(ロンバード効果・混雑の中の歩き方と避け方・大きな音に注意が向く)=欄と口だけ・値は空。

- 口は値を作らない(None)。W10 の騒音の段の読みの口は世界の値を読むだけ。
- ``Percept.nearby_change`` の種類に ``loud_sound``(``NEARBY_CHANGE_KINDS``)。``Percept`` の欄と並び・空の欄・manifest の
  ``percept`` は前と同じ(描画のバイト不変=欄が空のまま)。
- 合成の世界のランで描いた知覚の事実の ``nearby_change``・``heard_speech`` は空(None)のまま。
"""

from __future__ import annotations

import numpy as np

from shibuya.engine.body import system1 as S1
from shibuya.perception import facts as F
from shibuya.world.state import World

#: HEAD の ``percept_manifest()``(欄 26・空の欄 9=1-2 の凍結と同じ)。
HEAD_EMPTY = ["eye_dir", "mind_dir", "belongings", "tool_state", "watched_by", "heard_speech", "nearby_change",
              "acquaintance_seen", "prediction"]


def test_ports_return_empty_values():
    assert S1.speech_loudness(3) is None
    assert S1.crowd_gait(5) is None
    assert S1.loud_sound_notice("horn") is None
    assert [s.id for s in S1.SLOTS] == ["system1.lombard", "system1.crowd_gait", "system1.loud_sound"]
    rows = S1.manifest_rows()
    assert all(r["value"] == "empty" for r in rows) and len(rows) == 3


def test_noise_reading_port_reads_w10_only():
    w = World.synthetic(n_cells=6, seed=1)
    cells = np.array([0, 3, -1, 5], dtype=np.int32)
    got = S1.noise_stage_at(w, cells, 600, 60)
    want = np.asarray(w.noise_stage_for_tick(600, 60), dtype=np.uint8)
    assert got.dtype == np.uint8 and got[2] == 0 and list(got[[0, 1, 3]]) == list(want[[0, 3, 5]])


def test_loud_sound_is_a_nearby_change_kind_and_the_percept_shape_is_unchanged():
    assert F.NEARBY_CHANGE_KINDS == ("loud_sound",) and S1.LOUD_SOUND in F.NEARBY_CHANGE_KINDS
    assert list(F.EMPTY_FIELDS) == HEAD_EMPTY
    m = F.percept_manifest()
    assert m["schema"] == "shibuya.perception/percept/1" and m["empty_fields"] == HEAD_EMPTY
    for name in ("heard_speech", "nearby_change"):
        f = next(x for x in F.percept_fields() if x == name)
        assert f == name


def test_percepts_of_a_run_keep_the_fields_empty(monkeypatch):
    """合成の世界のランで描いた知覚の事実(系 decide が ``TickScratch.percepts`` に書く)の器の欄は None のまま。"""
    from shibuya.engine.run import run_day
    from shibuya.engine.systems import conductor as CD

    seen: list = []
    orig = CD.run_system

    def watch(spec, ctx, box):  # noqa: ANN001, ANN202
        out = orig(spec, ctx, box)
        if spec.name == "decide" and box.scratch.percepts:
            seen.extend(box.scratch.percepts.values())
        return out

    monkeypatch.setattr(CD, "run_system", watch)
    run_day(n_agents=80, seed=3, ticks=480, n_cells=9, processes=False, vocab_version="v3")
    assert seen and all(isinstance(p, F.Percept) for p in seen)
    assert all(p.nearby_change is None and p.heard_speech is None for p in seen)
