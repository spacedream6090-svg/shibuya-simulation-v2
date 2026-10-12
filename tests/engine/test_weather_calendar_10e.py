"""10e B6(第330): 天気=再生日・太陽と影=暦の日付の規則(``weather_scheme="calendar"``・既定は ``legacy`` のまま)。

ユーザーの答え 1-3。試験は合成の W13(2025-09-01〜2026-08-31 の 1 年ぶん)と実資産(35 日・2026-07-28〜08-31)で:

- 太陽の式(``engine.solar``)は構築段 ``build.field.w13_weather`` と同じ値を返す。実資産の 35 日すべてで、暦の日付=
  再生日なら計算し直した WBGT・暑さ段・日の出・日の入り・日照の語が W13 の値と同じ。
- 暦の日付が窓の中=その日の実際の天気(再生日=暦の日付)。揺らすとき(環境の seed を別に渡した)と窓の外は、
  同じ季節 × 平日/土休の中から天候型を日数の割合で引く。層が空なら隣の季節へ広げて警告。
- 影は暦の日付のファイル。無ければいちばん近い日の影を読んで警告と記録。
- 描画の天気(B3)・体感温度・日の出と日の入りの語が同じ規則(README §E6-1「B6 のための注」の (1)〜(3))。
- 複数日は日ごとに暦の日付が進んで引き直す。乱数は環境の seed だけ(母集団の seed・動きの seed では動かない)。
- 暦の日付=再生日のランは、legacy のランと層の名前(O56 の ``stratum``)のほかは全部同じ(既知の答え)。
"""

from __future__ import annotations

import datetime as dt
import math
import warnings
from collections import Counter
from pathlib import Path

import numpy as np
import pytest

from shibuya.agents.state import AgentState
from shibuya.engine import solar as SOL
from shibuya.engine.calendar import SEASON_OF_MONTH, SimCalendar, load_holidays
from shibuya.engine.processes import environment as ENV
from shibuya.world.assets import HEAT_STAGE_ORDER, ProcessAssets
from shibuya.world.state import World

REPO = Path(__file__).resolve().parents[2]
WORLD_DIR = REPO / "data" / "world" / "v2"
HOLIDAYS = REPO / "data" / "calendar" / "syukujitsu.csv"
needs_world = pytest.mark.skipif(not (WORLD_DIR / "w13_weather_hourly.parquet").is_file(), reason="世界資産が無い環境")
TYPES = ("晴", "曇", "雨", "猛暑")


# ================================================================ 合成の W13(1 年)
def _synthetic_w13(tmp_path: Path, *, drop_season: str | None = None, shadow_dates=("2026-07-13", "2026-07-28"),
                   n_cells: int = 9) -> ProcessAssets:
    """1 年ぶん(2025-09-01〜2026-08-31)の日の層と時ごとの気象。天候型は日付から決まる(季節で偏らせる)。"""
    table = load_holidays(HOLIDAYS) if HOLIDAYS.is_file() else None
    d0 = dt.date(2025, 9, 1)
    dates, kinds, types = [], [], []
    for k in range(365):
        d = d0 + dt.timedelta(days=k)
        if drop_season is not None and SEASON_OF_MONTH[d.month] == drop_season:
            continue
        rest = d.weekday() >= 5 or (table is not None and d in table.days)
        # 夏は猛暑 3:晴 2:雨 1・ほかの季節は晴 2:曇 1:雨 1(日数の割合の試験の既知の答え)
        cyc = ("猛暑", "猛暑", "猛暑", "晴", "晴", "雨") if SEASON_OF_MONTH[d.month] == "夏" else ("晴", "晴", "曇", "雨")
        dates.append(d.isoformat())
        kinds.append("土休" if rest else "平日")
        types.append(cyc[k % len(cyc)])
    n = len(dates)
    rng = np.random.default_rng(3)
    temp = 15.0 + 10.0 * rng.random((n, 24))
    rh = 40.0 + 40.0 * rng.random((n, 24))
    wind = 3.0 * rng.random((n, 24))
    sun = rng.random((n, 24))
    shadow_dir = tmp_path / "shadow"
    shadow_dir.mkdir(parents=True, exist_ok=True)
    for sd in shadow_dates:
        planes = np.zeros((288, 2), dtype=np.uint8)
        planes[:, 0] = int(sd[-2:])   # 日付ごとに違う面(どの日の影を読んだか分かる)
        np.save(shadow_dir / f"w9_shadow_{sd}.npy", planes)
    return ProcessAssets(
        source="synthetic-w13",
        weather_dates=tuple(dates),
        weather_stratum=tuple(f"{k}|{t}" for k, t in zip(kinds, types)),
        weather_weekday_kind=tuple(kinds),
        weather_type=tuple(types),
        sunrise_min=np.full(n, 300.0), sunset_min=np.full(n, 1100.0),   # 暦の規則では使わない値
        hourly_wbgt=np.full((n, 24), 20.0), hourly_heat_stage=np.zeros((n, 24), dtype=np.int8),
        shadow_dates=tuple(sorted(shadow_dates)), shadow_dir=str(shadow_dir),
        cell_street_point=np.arange(n_cells, dtype=np.int32), n_street_points=16,
        hourly_temp_c=temp, hourly_rh=rh, hourly_wind_ms=wind, hourly_sunshine_h=sun,
    )


def _env(passets, start: str, *, seed=1, perturbed=False, scheme="calendar", mode="real"):
    world = World.synthetic(n_cells=9, seed=1)
    agents = AgentState(10)
    table = load_holidays(HOLIDAYS)
    cal = SimCalendar(dt.datetime.fromisoformat(start), weekday_mode=mode, holidays=table)
    return ENV.EnvironmentProcess(world, agents, passets, master_seed=seed, calendar=cal,
                                  weather_scheme=scheme, perturbed=perturbed)


# ================================================================ 太陽の式=構築段
def test_b6_solar_formulas_equal_the_build_stage():
    from shibuya.build.field import w13_weather as W13
    from shibuya.build.geo.common import ORIGIN_LATLON

    assert (SOL.LAT, SOL.LON) == tuple(ORIGIN_LATLON) == (W13.LAT, W13.LON)
    assert SOL.DAYLIGHT_VOCAB == W13.DAYLIGHT_VOCAB and SOL.HEAT_BOUNDS == W13.HEAT_BOUNDS
    assert tuple(HEAT_STAGE_ORDER) == W13.HEAT_VOCAB
    assert SOL.WBGT_COEFF == W13.WBGT_COEFF and SOL.SOLAR_CONST_KW == W13.SOLAR_CONST_KW
    for k in range(0, 366, 7):
        d = dt.date(2025, 9, 1) + dt.timedelta(days=k)
        assert SOL.sun_times(d) == W13.sun_times(d)
        for m in (0.0, 330.0, 750.0, 1110.0, 1410.0):
            assert SOL.solar_elevation_deg(d, m) == W13.solar_elevation_deg(d, m)
            assert SOL.daylight_phase(m, *SOL.sun_times(d)) == W13.daylight_phase(m, *W13.sun_times(d))
    for args in ((30.1, 70.2, 2.3, 0.4), (35.0, 50.0, 0.0, 0.0), (20.5, 90.0, 5.5, 0.81)):
        assert SOL.wbgt_estimate(*args) == W13.wbgt_estimate(*args)
    for w in (20.9, 21.0, 24.99, 25.0, 28.0, 30.9, 31.0, 40.0):
        assert SOL.heat_stage(w) == W13.heat_stage(w)


@needs_world
def test_b6_recomputed_heat_and_sun_equal_w13_when_the_dates_match():
    """実資産の 35 日すべて: 暦の日付=再生日なら、計算し直した WBGT・暑さ段・日の出・日の入りが W13 の値と同じ。"""
    from shibuya.world.assets import load_process_assets

    world = World.load_or_synthetic(WORLD_DIR, seed=1)
    pa = load_process_assets(WORLD_DIR, world.assets)
    assert pa.hourly_temp_c is not None and len(pa.weather_dates) >= 35
    for r, iso in enumerate(pa.weather_dates):
        d = dt.date.fromisoformat(iso)
        assert SOL.sun_minutes(d) == (pa.sunrise_min[r], pa.sunset_min[r]), iso
        for h in range(24):
            w = SOL.hourly_wbgt(d, h, pa.hourly_temp_c[r, h], pa.hourly_rh[r, h], pa.hourly_wind_ms[r, h],
                                pa.hourly_sunshine_h[r, h])
            if w is None:
                assert math.isnan(pa.hourly_wbgt[r, h]) and pa.hourly_heat_stage[r, h] == 0
            else:
                assert round(w, 2) == pa.hourly_wbgt[r, h] and SOL.heat_stage(w) == pa.hourly_heat_stage[r, h]


# ================================================================ 再生日の決め方
def test_b6_inside_the_window_replays_the_actual_day_and_takes_the_sun_from_the_calendar(tmp_path):
    pa = _synthetic_w13(tmp_path)
    env = _env(pa, "2026-01-19")    # 冬・月曜(窓の中)
    rec = env.weather_days[0]
    assert env.replay_date == "2026-01-19" and rec["how"] == "actual" and rec["calendar_date"] == "2026-01-19"
    assert env.stratum.startswith("冬|平日|")
    assert (env._sunrise, env._sunset) == SOL.sun_minutes(dt.date(2026, 1, 19))
    assert env._sunrise != 300.0                                   # W13 の行の日の出は使わない
    # 揺らしていないので seed を変えても同じ日
    assert _env(pa, "2026-01-19", seed=99).replay_date == "2026-01-19"


def test_b6_perturbed_draws_follow_the_day_counts_of_season_kind_and_type(tmp_path):
    pa = _synthetic_w13(tmp_path)
    season_kind = [(SEASON_OF_MONTH[int(d[5:7])], k, t) for d, k, t in
                   zip(pa.weather_dates, pa.weather_weekday_kind, pa.weather_type)]
    want = Counter(t for s, k, t in season_kind if s == "夏" and k == "平日")
    got: Counter = Counter()
    n = 0
    for seed in range(60):
        for day in range(20):
            date, stratum, widened = ENV.sample_calendar_day(seed, day, "夏", "平日", pa)
            assert widened == "" and SEASON_OF_MONTH[int(date[5:7])] == "夏"
            assert pa.weather_weekday_kind[pa.day_index_of(date)] == "平日"
            assert stratum == f"夏|平日|{pa.weather_type[pa.day_index_of(date)]}"
            got[stratum.split("|")[2]] += 1
            n += 1
    total = sum(want.values())
    for t, c in want.items():   # 日数の割合(猛暑 1/2・晴 1/3・雨 1/6 前後)で引く(一様の 1/3 ずつではない)
        assert abs(got[t] / n - c / total) < 0.04, (t, got[t] / n, c / total)
    # 揺らしたラン: 環境の過程も同じ関数で引く
    env = _env(pa, "2026-07-13", seed=5, perturbed=True)
    assert env.weather_days[0]["how"] == "sampled"
    assert env.replay_date == ENV.sample_calendar_day(5, 0, "夏", "平日", pa)[0]


def test_b6_outside_the_window_samples_and_an_empty_stratum_widens_with_a_warning(tmp_path):
    pa = _synthetic_w13(tmp_path)
    env = _env(pa, "2026-10-05")    # 窓の外(秋・月曜)
    assert env.weather_days[0]["how"] == "sampled" and env.stratum.startswith("秋|平日|")
    assert env.weather_days[0]["widened"] == "" and not any("広げ" in w for w in env.weather_warnings)
    # 冬の無い W13 で冬の日 → 隣の季節(秋・春)へ広げて警告
    pb = _synthetic_w13(tmp_path / "b", drop_season="冬")
    with pytest.warns(ENV.WeatherWarning, match="隣の季節"):
        env = _env(pb, "2027-01-11")
    assert env.weather_days[0]["widened"] == "隣の季節" and env.stratum.split("|")[0] in ("秋", "春")
    assert any("隣の季節" in w for w in env.weather_warnings)


def test_b6_shadow_comes_from_the_calendar_date_or_the_nearest_with_a_warning(tmp_path):
    pa = _synthetic_w13(tmp_path)
    env = _env(pa, "2026-07-13")
    assert env.weather_days[0]["shadow_date"] == "2026-07-13" and not env.weather_days[0]["shadow_fallback"]
    assert int(env._planes[0, 0]) == 13
    with pytest.warns(ENV.WeatherWarning, match="いちばん近い 2026-07-28"):
        env = _env(pa, "2026-07-27")
    assert env.weather_days[0]["shadow_date"] == "2026-07-28" and env.weather_days[0]["shadow_fallback"]
    assert int(env._planes[0, 0]) == 28
    assert ENV.nearest_shadow_date(("2026-07-13", "2026-07-28"), "2026-07-20") == "2026-07-13"   # 同じ近さ=前の日
    assert ENV.nearest_shadow_date(("2026-07-13", "2026-07-28"), "2026-07-21") == "2026-07-28"
    # 影は再生日でなく暦の日付(再生日が窓の別の日でも 07-13 の影)
    env = _env(pa, "2026-07-13", seed=3, perturbed=True)
    assert env.weather_days[0]["shadow_date"] == "2026-07-13"


def test_b6_heat_uses_the_replay_weather_and_the_calendar_sun(tmp_path):
    pa = _synthetic_w13(tmp_path)
    env = _env(pa, "2026-01-19", seed=4, perturbed=True)
    r = env._row
    cal = dt.date(2026, 1, 19)
    for h in range(24):
        w = SOL.hourly_wbgt(cal, h, pa.hourly_temp_c[r, h], pa.hourly_rh[r, h], pa.hourly_wind_ms[r, h],
                            pa.hourly_sunshine_h[r, h])
        assert env._cal_wbgt[h] == round(w, 2) and env._cal_stage[h] == SOL.heat_stage(w)
        assert env._heat_now(h * 60) == (int(env._cal_stage[h]), float(env._cal_wbgt[h]))


def test_b6_days_advance_and_only_the_environment_seed_moves_the_draws(tmp_path):
    from shibuya.agents.schedule import synthesize
    from shibuya.engine.processes.runner import WorldProcessRunner

    pa = _synthetic_w13(tmp_path)
    env = _env(pa, "2026-10-05")
    first = env.replay_date
    env.pick_day(1)
    assert env.weather_days[1]["calendar_date"] == "2026-10-06" and env.weather_days[1]["how"] == "sampled"
    assert env._sunrise == SOL.sun_minutes(dt.date(2026, 10, 6))[0]
    assert set(env.weather_days) == {0, 1} and env.weather_days[0]["replay_date"] == first

    def runner(start="2026-07-13", **kw):
        world = World.synthetic(n_cells=9, seed=1)
        agents = AgentState(20)
        agents.freeze()
        world.freeze()
        cal = SimCalendar(dt.datetime.fromisoformat(start), weekday_mode="real", holidays=load_holidays(HOLIDAYS))
        r = WorldProcessRunner(world=world, agents=agents, assets=pa, calendar=cal, weather_scheme="calendar",
                               schedule=synthesize(20, 1, world.n_cells), **kw)
        return r.environment

    base = runner(seed=1)
    assert not base.perturbed and base.replay_date == "2026-07-13"                     # 窓の中=実際の天気
    # 揺らさない限り、環境の seed・動きの seed を変えても実際の天気(salt の比較=10f で環境が揺れない)
    assert runner(seed=2, environment_seed=1).replay_date == "2026-07-13"
    assert runner(seed=1, environment_seed=9).replay_date == "2026-07-13"
    # 揺らす(weather_perturb)=環境の seed で引き直す
    shaken = [runner(seed=1, environment_seed=e, weather_perturb=True) for e in range(2, 12)]
    assert all(x.perturbed for x in shaken) and len({x.replay_date for x in shaken}) > 1
    # 揺らしたランでも、動きの seed・母集団の seed では動かない
    one = runner(seed=5, environment_seed=3, weather_perturb=True).replay_date
    assert one == runner(seed=9, environment_seed=3, weather_perturb=True).replay_date
    assert one == runner(seed=5, population_seed=77, environment_seed=3, weather_perturb=True).replay_date
    # 窓の外は揺らさなくても層から(鍵は環境の seed)
    out = runner("2026-10-05", seed=1)
    assert out.weather_days[0]["how"] == "sampled" and not out.perturbed


def test_b6_legacy_default_is_untouched(tmp_path):
    pa = _synthetic_w13(tmp_path)
    env = _env(pa, "2026-07-13", scheme="legacy", mode="day_index")
    assert env.weather_scheme == "legacy" and env.weather_days[0]["how"] == "legacy"
    assert env.replay_date in pa.shadow_dates                       # legacy は影のある日に絞る(今のまま)
    assert env._sunrise == 300.0                                    # 日の出は再生日の行(今のまま)


# ================================================================ 実資産のラン
SMALL = dict(n_agents=200, seed=1, ticks=1440, checkpoint_every=360)


@needs_world
def test_b6_known_answer_calendar_on_the_replay_day_equals_legacy_but_the_label(monkeypatch):
    """暦の日付=再生日(窓の中=実際の天気)のランは legacy と O56 の層の名前のほかは全部同じ。

    〔改訂(第330・ACT)〕legacy の再生日は影のある日に絞って引く(``prefer_shadow_days``)ので、影が 07-28 だけだった
    資産では 07-28、影 6 日(07-13〜17+07-28)の資産では seed 1 で 07-14 になる。暦の日付は legacy の再生日に合わせる
    (前: 07-28 の固定)。"""
    from shibuya import cli

    a = cli.run(world_dir=str(WORLD_DIR), checkpoint_detail=True, weather_scheme="legacy",
                calendar_weekday="day_index", **SMALL)
    rd = a.run_manifest_fields()["replay_date"]
    b = cli.run(world_dir=str(WORLD_DIR), checkpoint_detail=True, weather_scheme="calendar",
                calendar_weekday="day_index", start_sim_datetime=rd, **SMALL)
    assert a.llm_calls == b.llm_calls
    for da, db in zip(a.checkpoint_details, b.checkpoint_details):
        diff = sorted(k for k in set(da["items"]) | set(db["items"]) if da["items"].get(k) != db["items"].get(k))
        assert diff == ["O56:runner.environment.stratum"], diff
        assert {k: v for k, v in da.items() if k != "items"} == {k: v for k, v in db.items() if k != "items"}
    wb = b.run_manifest_fields()["weather"]
    assert wb["days"][0]["how"] == "actual" and wb["days"][0]["replay_date"] == rd
    assert wb["days"][0]["shadow_date"] == rd and not wb["days"][0]["shadow_fallback"]
    assert a.run_manifest_fields()["weather"]["scheme"] == "legacy"


@needs_world
def test_b6_b3_words_body_heat_and_sun_follow_one_rule(monkeypatch):
    """README §E6-1 B6 のための注 (1)〜(3): 描画の天気(B3)・体感温度・日の出と日の入りの語が同じ規則
    (天気=再生日・太陽=暦の日付)。

    〔改訂(第330・ACT)〕前は「実資産の 35 日は 07-13 を持たない=窓の外で層から引く(警告も出る)」で再生日と暦の日付を
    分けていた。W13 の年間化(B5)と影 6 日(ACT)の後は 07-13 が窓の中で影もあるので、既定のランは実際の天気
    (再生日=暦の日付・警告なし)。再生日と暦の日付を分けるのは ``weather_perturb=True``(同じ層から引く)で行う。"""
    from shibuya import cli
    from shibuya.perception import normalize as N
    from shibuya.perception import renderer as REN

    made: list = []
    _init = REN.Renderer.__init__

    def spy(self, *a, **k):
        _init(self, *a, **k)
        made.append(self)

    monkeypatch.setattr(REN.Renderer, "__init__", spy)
    # 既定(暦の規則・揺らさない): 07-13 は窓の中=その日の実際の天気・影も暦の日付の 07-13(警告なし)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        res0 = cli.run(world_dir=str(WORLD_DIR), **SMALL)
    assert not any(issubclass(w.category, ENV.WeatherWarning) for w in caught)
    d0 = res0.run_manifest_fields()["weather"]["days"][0]
    assert (d0["calendar_date"], d0["replay_date"], d0["how"]) == ("2026-07-13", "2026-07-13", "actual")
    assert d0["shadow_date"] == "2026-07-13" and not d0["shadow_fallback"]
    env0 = res0.runner.environment
    r0 = res0.runner.assets.day_index_of(env0.replay_date)
    assert (env0._sunrise, env0._sunset) == SOL.sun_minutes(dt.date(2026, 7, 13))
    assert (env0._sunrise, env0._sunset) == (res0.runner.assets.sunrise_min[r0], res0.runner.assets.sunset_min[r0])
    # 揺らしたラン: 再生日は同じ層(夏|平日)から引いた別の日・太陽と影は暦の日付のまま
    res = cli.run(world_dir=str(WORLD_DIR), weather_perturb=True, **SMALL)
    m = res.run_manifest_fields()
    env = res.runner.environment
    day = m["weather"]["days"][0]
    assert m["start_sim_datetime"] == "2026-07-13T00:00:00" and day["calendar_date"] == "2026-07-13"
    assert day["how"] == "sampled" and day["replay_date"] != "2026-07-13" and m["weather"]["perturbed"]
    assert day["shadow_date"] == "2026-07-13" and not day["shadow_fallback"]
    assert day["stratum"].startswith("夏|平日|")
    ren = made[-1]
    cal = dt.date(2026, 7, 13)
    sr, ss = SOL.sun_times(cal)
    replay = dt.datetime.fromisoformat(env.replay_date)
    for h in range(24):
        when = dt.datetime(2026, 7, 13, h, 10)
        weather, daylight, heat = ren.weather_words_fn(when)
        assert weather == ren.assets.weather(replay.replace(hour=h))[0]            # (1) 天候=再生日の行
        assert daylight == SOL.daylight_phase(h * 60 + 30.0, sr, ss)               # (3) 日照=暦の日付
        stage, wbgt = env._heat_now(h * 60)                                        # (2) 体感温度と同じ暑さ段
        assert heat == (HEAT_STAGE_ORDER[stage] if np.isfinite(wbgt) else "")
        tc = REN._TickCache(tick=h * 60, when=when, band5=N.time_band(when))
        text = ren._b3(tc).decode("utf-8")
        assert weather in text and daylight in text and (heat in text)
    assert (env._sunrise, env._sunset) == SOL.sun_minutes(cal)                    # 体の昼夜も暦の日付
    r = res.runner.assets.day_index_of(env.replay_date)
    assert (env._sunrise, env._sunset) != (res.runner.assets.sunrise_min[r], res.runner.assets.sunset_min[r])
