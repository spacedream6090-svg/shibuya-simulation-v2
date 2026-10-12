"""第330 ACT(10e 版上げ 1 回目の活性化): テープの脇の meta の暦の規則(親の決定 (5))。

- 録画はテープの脇の meta(``run_meta.json``)に ``calendar_weekday``・``weather_scheme`` を書く。
- 再生は meta の値を既定にする(``rng_scheme`` と同じ形)。明示の値が meta と違えば止める。
- 記録の無いテープ(活性化より前の録画)は ``day_index``・``legacy`` とみなし、警告を 1 回出す
  (``CalendarSchemeWarning``)=旧テープは止まらず、録画と同じ値で再生される。
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import pytest

import shibuya.engine.run as RUN
from shibuya.engine.tape import RUN_META_FILENAME, read_run_meta

REPO = Path(__file__).resolve().parents[2]
WORLD_DIR = REPO / "data" / "world" / "v2"
pytestmark = pytest.mark.skipif(not (WORLD_DIR / "w13_weather_days.parquet").is_file(), reason="世界資産が無い環境")
#: 世界資産で回す(合成世界は気象の資産が無く、暦の規則で値が動かない=meta が効くことを示せない)
KW = dict(n_agents=60, seed=3, ticks=480, checkpoint_every=240)


def _rec(tmp_path, name: str, **kw):
    from shibuya import cli

    return cli.run(world_dir=str(WORLD_DIR), tape_path=tmp_path / name, **KW, **kw)


def _rep(tmp_path, name: str, **kw):
    from shibuya import cli
    from tests.engine.test_tape_wiring import BoomLLM

    return cli.run(world_dir=str(WORLD_DIR), mode="replay", replay=tmp_path / name, llm=BoomLLM(), **KW, **kw)


def _drop_calendar_meta(tmp_path, name: str) -> None:
    """活性化より前の録画と同じ形(暦の規則の欄が無い・ほかの欄は残す)。"""
    meta = tmp_path / name / RUN_META_FILENAME
    d = json.loads(meta.read_text(encoding="utf-8"))
    d.pop("calendar_weekday")
    d.pop("weather_scheme")
    meta.write_text(json.dumps(d) + "\n", encoding="utf-8")


def test_act_the_tape_carries_the_calendar_rules_and_the_replay_defaults_to_them(tmp_path):
    new = _rec(tmp_path, "new")                                   # 既定=real・calendar
    meta = read_run_meta(tmp_path / "new")
    assert (meta["calendar_weekday"], meta["weather_scheme"]) == ("real", "calendar")
    assert new.run_manifest_fields()["weather"]["scheme"] == "calendar"
    rep = _rep(tmp_path, "new")
    assert rep.final_hash == new.final_hash and rep.tape_miss_count == 0
    old = _rec(tmp_path, "old", calendar_weekday="day_index", weather_scheme="legacy")
    meta = read_run_meta(tmp_path / "old")
    assert (meta["calendar_weekday"], meta["weather_scheme"]) == ("day_index", "legacy")
    assert old.final_hash != new.final_hash                      # 世界の日付・再生日・影が違う=規則が効く
    with warnings.catch_warnings():
        warnings.simplefilter("error", RUN.CalendarSchemeWarning)  # 記録があれば警告しない
        rep = _rep(tmp_path, "old")                               # 未指定=テープの値(day_index・legacy)
    assert rep.final_hash == old.final_hash and rep.tape_miss_count == 0
    # 明示の値がテープと違えば止める(文言に両方の値)
    with pytest.raises(ValueError, match="テープは calendar_weekday=day_index・weather_scheme=legacy"):
        _rep(tmp_path, "old", weather_scheme="calendar")
    with pytest.raises(ValueError, match="今の設定は calendar_weekday=day_index・weather_scheme=calendar"):
        _rep(tmp_path, "new", calendar_weekday="day_index")


def test_act_a_tape_without_the_calendar_rules_is_replayed_as_day_index_and_legacy(tmp_path):
    old = _rec(tmp_path, "pre", calendar_weekday="day_index", weather_scheme="legacy")  # 活性化より前の既定
    _drop_calendar_meta(tmp_path, "pre")
    assert "calendar_weekday" not in read_run_meta(tmp_path / "pre")
    RUN._WARNED_CAL.discard(str(tmp_path / "pre"))
    with pytest.warns(RUN.CalendarSchemeWarning) as got:          # 警告を 1 回出して止まらない
        rep = _rep(tmp_path, "pre")
    assert len([w for w in got if issubclass(w.category, RUN.CalendarSchemeWarning)]) == 1
    assert rep.final_hash == old.final_hash and rep.tape_miss_count == 0
    assert rep.run_manifest_fields()["weather"]["scheme"] == "legacy"
    with warnings.catch_warnings():
        warnings.simplefilter("error", RUN.CalendarSchemeWarning)  # 同じテープの 2 回目は警告しない
        assert _rep(tmp_path, "pre").final_hash == old.final_hash
    with pytest.raises(ValueError, match="暦の規則がテープと違う"):
        _rep(tmp_path, "pre", calendar_weekday="real", weather_scheme="calendar")


def test_act_weather_manifest_declares_the_two_expedients(tmp_path):
    """親の決定 (3): 層を広げる順と「同じ近さの影は前の日」は expedient として manifest に載る(calendar のランだけ)。"""
    from shibuya.engine.processes.environment import WEATHER_EXPEDIENTS

    new = _rec(tmp_path, "m")
    w = new.run_manifest_fields()["weather"]
    assert w["expedients"] == list(WEATHER_EXPEDIENTS) and len(WEATHER_EXPEDIENTS) == 2
    assert "広げる順" in WEATHER_EXPEDIENTS[0] and "前の日" in WEATHER_EXPEDIENTS[1]
    old = _rec(tmp_path, "o", calendar_weekday="day_index", weather_scheme="legacy")
    assert "expedients" not in old.run_manifest_fields()["weather"]


def test_act_resolve_calendar_schemes_outside_replay_takes_the_given_or_the_default():
    assert RUN.resolve_calendar_schemes(None, None) == ("real", "calendar")
    assert RUN.resolve_calendar_schemes("day_index", "legacy") == ("day_index", "legacy")
    assert RUN.resolve_calendar_schemes("day_index", None, mode="record") == ("day_index", "calendar")
    with pytest.raises(ValueError):
        RUN.resolve_calendar_schemes("lunar", None)
