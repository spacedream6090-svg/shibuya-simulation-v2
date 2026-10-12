"""第330 ACT(10e 版上げ 1 回目の活性化): テープの脇の meta の暦の規則(親の決定 (5))。

- 録画はテープの脇の meta(``run_meta.json``)に ``calendar_weekday``・``weather_scheme`` を書く。
- 〔改訂(第330・RET)〕ACT では「再生は meta の値を既定にし、記録の無いテープは day_index・legacy とみなして警告」だった
  (``resolve_calendar_schemes``・``CalendarSchemeWarning``)。RET で暦の切替口(``calendar_weekday``・``weather_scheme``)を
  消したので、記録の無いテープ・旧い値のテープは止める(``check_replay_tape``=警告でなく例外)。ACT の commit で
  旧テープが同じ値で再生されたことは 10e の記録 §ACT-4 に残した。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import shibuya.engine.run as RUN
from shibuya.engine.tape import RUN_META_FILENAME, read_run_meta

REPO = Path(__file__).resolve().parents[2]
WORLD_DIR = REPO / "data" / "world" / "v2"
pytestmark = pytest.mark.skipif(not (WORLD_DIR / "w13_weather_days.parquet").is_file(), reason="世界資産が無い環境")
#: 世界資産で回す(合成世界は気象の資産が無く、暦の規則で値が動かない)
KW = dict(n_agents=60, seed=3, ticks=480, checkpoint_every=240)


def _rec(tmp_path, name: str, **kw):
    from shibuya import cli

    return cli.run(world_dir=str(WORLD_DIR), tape_path=tmp_path / name, **KW, **kw)


def _rep(tmp_path, name: str, **kw):
    from shibuya import cli
    from tests.engine.test_tape_wiring import BoomLLM

    return cli.run(world_dir=str(WORLD_DIR), mode="replay", replay=tmp_path / name, llm=BoomLLM(), **KW, **kw)


def test_act_the_tape_carries_the_calendar_rules_and_the_replay_matches(tmp_path):
    new = _rec(tmp_path, "new")
    meta = read_run_meta(tmp_path / "new")
    assert (meta["calendar_weekday"], meta["weather_scheme"]) == ("real", "calendar")
    assert (meta["rng_scheme"], meta["rng_layout"]) == ("counter", "10e")
    assert new.run_manifest_fields()["weather"]["scheme"] == "calendar"
    rep = _rep(tmp_path, "new")
    assert rep.final_hash == new.final_hash and rep.tape_miss_count == 0
    # 〔第330・RET〕暦の切替口は無い(渡すと止まる)
    for k, v in (("calendar_weekday", "real"), ("weather_scheme", "calendar")):
        with pytest.raises(TypeError):
            RUN.run_day(n_agents=4, ticks=2, **{k: v})


def test_ret_a_tape_from_before_the_activation_is_not_replayed(tmp_path):
    """〔改訂(第330・RET)〕暦の規則の記録が無いテープ(活性化より前の録画)と旧い値(day_index・legacy)のテープは止める。"""
    _rec(tmp_path, "t")
    meta = tmp_path / "t" / RUN_META_FILENAME
    base = json.loads(meta.read_text(encoding="utf-8"))
    for change in ({"calendar_weekday": None, "weather_scheme": None}, {"calendar_weekday": "day_index"},
                   {"weather_scheme": "legacy"}):
        d = dict(base)
        for k, v in change.items():
            if v is None:
                d.pop(k)
            else:
                d[k] = v
        meta.write_text(json.dumps(d) + "\n", encoding="utf-8")
        with pytest.raises(ValueError, match="今の版では再生できない"):
            _rep(tmp_path, "t")
    meta.write_text(json.dumps(base) + "\n", encoding="utf-8")
    assert _rep(tmp_path, "t").tape_miss_count == 0
    assert not hasattr(RUN, "resolve_calendar_schemes") and not hasattr(RUN, "CalendarSchemeWarning")


def test_act_weather_manifest_declares_the_two_expedients(tmp_path):
    """親の決定 (3): 層を広げる順と「同じ近さの影は前の日」は expedient として manifest に載る。"""
    from shibuya.engine.processes.environment import WEATHER_EXPEDIENTS

    new = _rec(tmp_path, "m")
    w = new.run_manifest_fields()["weather"]
    assert w["expedients"] == list(WEATHER_EXPEDIENTS) and len(WEATHER_EXPEDIENTS) == 2
    assert "広げる順" in WEATHER_EXPEDIENTS[0] and "前の日" in WEATHER_EXPEDIENTS[1]


def test_ret_check_replay_tape_does_nothing_outside_replay():
    assert RUN.check_replay_tape("record", None) is None
    assert RUN.check_replay_tape("mock", "somewhere") is None
