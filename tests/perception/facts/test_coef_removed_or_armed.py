"""第 1 期 1-2 知覚の分離: 係数は消した(口の約束 1-2 の〔決定〕・決定 10-12 §1-6「係数で持たない」)。

経緯: 1-2 の最初に、歩きスマホの負荷の係数 0.46(``p_notice``)と看板の注視の活動の乗数(表は既定で全部 1.0・腕の例は
通話 0.49・連れとの会話 1.39)を 1.0 にした HEAD の写しで byte-check を回し、19/19 構成・25 欄とも HEAD と同じ=**既定の
結果は動かない**と分かった(記録 ``docs/bench/analysis/wallbounce-1012/p12/README.md``)。親の判断(〔決定〕=動かなければ
消す)で、係数・乗数の表・腕(``--p-see-activity``・一時の ``--percept-coefs``)を消した。消した値はパターン台帳 §10 の
検証専用(親が設計書に書く): 0.46=歩きスマホの気づき(Hyman 2010・``p_notice`` の ``M_LOAD``)/0.49・1.39=通話・連れとの
会話の気づきの比(Hyman 2010 表 2 の 25.0/51.3・71.4/51.3・``renderer`` の活動の乗数の腕の例)。

(a) 消した値の数のリテラルが src のどこにも無い(AST)・名(定数・欄・関数・腕・CLI の旗)が残らない
(b) 歩きスマホの旗は事実として受けるが、一次検出の確率に効かない
(c) 看板の注視は p_see 1 つの値だけ(活動で変わらない)
(d) manifest: ``p_see_activity`` の欄は残して値は null・``percept`` に係数の腕の欄は無い
"""

from __future__ import annotations

import ast
import dataclasses
import inspect
from pathlib import Path

import numpy as np
import pytest

from shibuya.perception import facts as F
from shibuya.perception import p_notice as P
from shibuya.perception import renderer as R

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src" / "shibuya"
#: 消した値(数のリテラル)。src に 1 つも残らない(定数・既定値・例のどれにも)。
REMOVED_VALUES = (0.46, 0.49, 1.39)


# ---------------------------------------------------------------- (a)
def test_removed_values_are_not_in_src():
    hits = []
    for p in sorted(SRC.rglob("*.py")):
        for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if isinstance(n, ast.Constant) and type(n.value) in (int, float) and n.value in REMOVED_VALUES:
                hits.append(f"{p.relative_to(ROOT).as_posix()}:{n.lineno} {n.value}")
    assert hits == []


def test_names_are_gone():
    assert not hasattr(P, "M_LOAD")
    assert "m_load" not in {f.name for f in dataclasses.fields(P.PNoticeParams)}
    assert "m_load" not in inspect.signature(P.p1_primary).parameters
    for name in ("P_SEE_BY_ACTIVITY", "check_p_see_activity"):
        assert not hasattr(R, name), name
    assert "p_see_activity" not in inspect.signature(R.Renderer).parameters
    for name in ("percept_coefs", "set_percept_coefs", "coefs_on", "PERCEPT_COEFS_ENV", "PERCEPT_COEFS_MODES"):
        assert not hasattr(F, name), name
    cli_src = (SRC / "cli.py").read_text(encoding="utf-8")
    assert "--p-see-activity" not in cli_src and "--percept-coefs" not in cli_src
    assert "SHIBUYA_PERCEPT_COEFS" not in "".join(p.read_text(encoding="utf-8") for p in SRC.rglob("*.py"))


# ---------------------------------------------------------------- (b)
def test_phone_flag_does_not_change_the_primary_detection():
    xy = np.array([[20.0, 0.0], [60.0, 10.0]])
    h = np.array([8, 9], np.uint8)
    p1 = {t: P.notice_event(event_xy=(0.0, 0.0), agent_xy=xy, heading_u8=h, task_flag=int(t), seed=1,
                            event_id=1, tick=1).p1 for t in P.TaskLoad}
    assert np.array_equal(p1[P.TaskLoad.PHONE], p1[P.TaskLoad.FREE])
    assert np.array_equal(p1[P.TaskLoad.TALKING], p1[P.TaskLoad.FREE])


# ---------------------------------------------------------------- (c)
def test_signage_gate_is_one_p_for_every_activity():
    from tests.perception.facts.scenes import build

    w, a = build(n_agents=60, seed=31, activity_columns=True)
    with a.writable():
        a.activity_kind[:] = np.arange(a.n) % 5
    r = R.Renderer(w, a, seed=5, signage_p_see=0.4)
    cell = next(c for c in range(w.n_cells) if r._signage_poi(c) >= 0)
    poi = r._signage_poi(cell)
    from shibuya.perception.attention import gate_stage1

    got = [r._signage_seen(i, cell, 700) for i in range(a.n)]
    want = [bool(gate_stage1(1, 0.4, seed=5, domain_counters=(700, i, poi))[0]) for i in range(a.n)]
    assert got == want


# ---------------------------------------------------------------- (d)
def test_manifest_fields():
    from shibuya.engine.run import run_day

    res = run_day(n_agents=60, seed=2, ticks=120, n_cells=9, vocab_version="v3")
    m = res.run_manifest_fields()
    assert "p_see_activity" in m and m["p_see_activity"] is None
    assert "coefs" not in m["percept"]
    with pytest.raises(ValueError):
        run_day(n_agents=20, seed=2, ticks=5, p_see_activity={"phone": 0.5})
