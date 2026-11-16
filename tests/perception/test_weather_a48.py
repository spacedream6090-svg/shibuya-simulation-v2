"""〔A48・第347〕天気の語の最頻値の補いを消した(返事その 8 §3・§8・壁打ちの記録 2-55・記録
``docs/bench/analysis/weather-a48-347/README.md``)。

- 実データの資産で W13 の時の表に ``(日付, 時)`` の行が無ければ止める(日付と時を書いた ``ValueError``=黙って埋めない)。
  描画の口(``PerceptionAssets.weather``)と、組み立て(引きうる再生日の全部)・日の頭(引いた再生日)の確かめ。
- 合成の世界(試験用)だけは決まった天気を宣言して使い、manifest の ``weather.declared`` に出す。
- 世界過程の無いラン(``processes=False``)も本筋と同じ規則で再生日を引く(天気だけの環境の過程・体感温度は書かない)。
- 注入の描画(アダプタでない)にも同じ口が挿さる。資産の片方だけなら(どちらの向きでも)組み立てで止める。
- 〔検収の直し〕data の無い機械(CI)でも、天気だけの環境の過程を組み立てる道と注入の描画に口が挿さる道を、試験の中で作る
  小さな資産(合成の世界の形の描画の資産と、W13 の 2 日分の過程の資産)で回す。

逐次ループ宣言: なし(試験)。
"""

from __future__ import annotations

import dataclasses
import re
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from shibuya.world.model.agent_table import AgentState
from shibuya.engine.llm_bridge import StubRenderer
from shibuya.engine.run import run_day
from shibuya.foundation.text import normalize as N
from shibuya.foundation.text import templates as T
from shibuya.perception import renderer as RD
from shibuya.runtime.systems import assemble as ASM
from shibuya.runtime.systems import state_io as SIO
from shibuya.world.model.assets import ProcessAssets
from shibuya.world.laws.environment import sample_calendar_day
from shibuya.world.model.state import World

REPO = Path(__file__).resolve().parents[2]
WORLD_DIR = REPO / "data" / "world" / "v2"
needs_world = pytest.mark.requires_data(
    "world_v2:w13_weather_days.parquet", "world_v2:w13_weather_hourly.parquet", "world_v2:w17_schedule.parquet"
)
DAY = "2026-07-13"  # run_day の既定の開始日(月曜)
DAY2 = "2026-07-14"
ROW = ("曇", T.DAYLIGHT_WORDS[1], T.HEAT_STAGE_WORDS[2])
SMALL_SYN = dict(n_agents=30, seed=1, n_cells=9, ticks=60, checkpoint_every=60)


def _real_shaped(world: World, *, days=(DAY,), drop: tuple[tuple[str, int], ...] = (),
                 words: dict[str, str] | None = None) -> RD.PerceptionAssets:
    """合成の世界の形で、実データと同じ扱い(``source`` が合成でない)の知覚の資産。W13 の時の表は ``days`` の 24 時。

    ``words`` は日付 → 天候の語(無ければ ``ROW`` の語)。"""
    rows = {(d, h): ((words or {}).get(d, ROW[0]),) + ROW[1:] for d in days for h in range(24) if (d, h) not in drop}
    return dataclasses.replace(RD.PerceptionAssets.synthetic(world), source="test-real",
                               weather_by_date_hour=rows, declared_weather_by_hour={})


def _w13_process_assets(days=(DAY, DAY2), types: tuple[str, ...] | None = None) -> ProcessAssets:
    """W13 の日の表を ``days`` だけ持つ小さな過程の資産(ほかの欄は合成=過程は休む)。``asset_sources`` に W13 の 2 表と
    W13 でない表の名を 1 つ置く(世界過程の無いランの manifest に W13 の 2 表だけが写るかを見る)。天候型は ``types``
    (無ければ全部「曇」)。日はどれも夏の平日として置く。"""
    n = len(days)
    types = types or tuple("曇" for _ in days)
    full = lambda v: np.full((n, 24), v, dtype=np.float64)  # noqa: E731
    return dataclasses.replace(
        ProcessAssets.synthetic(), source="test-w13",
        weather_dates=tuple(days), weather_stratum=tuple(f"夏|平日|{t}" for t in types),
        weather_weekday_kind=tuple("平日" for _ in days), weather_type=tuple(types),
        sunrise_min=np.full(n, 285.0), sunset_min=np.full(n, 1140.0),
        hourly_wbgt=full(26.0), hourly_heat_stage=np.full((n, 24), 2, dtype=np.int8),
        hourly_temp_c=full(30.0), hourly_rh=full(60.0), hourly_wind_ms=full(2.0), hourly_sunshine_h=full(0.5),
        asset_sources={"w13_weather_days.parquet": "d" * 64, "w13_weather_hourly.parquet": "h" * 64,
                       "w12_timetables.parquet": "t" * 64},
    )


@pytest.fixture
def made(monkeypatch):
    """ランの中で作られた描画(``Renderer``)の控え。"""
    out: list = []
    _init = RD.Renderer.__init__

    def spy(self, *a, **k):
        _init(self, *a, **k)
        out.append(self)

    monkeypatch.setattr(RD.Renderer, "__init__", spy)
    return out


# ================================================================ ① 実データの形の資産は表に無い行で止まる
def test_real_shaped_assets_stop_on_a_missing_row_and_the_synthetic_world_uses_the_declared_weather():
    """何を確かめるか: 実データの形の資産は (日付, 時) の行が無ければ日付と時を書いて止まる(補いに落ちない)。合成の世界は
    表に無い日付でも宣言した決まった天気(晴・日照は時から・やや暑い)を返す。"""
    w = World.synthetic(n_cells=4, seed=1)
    real = _real_shaped(w, drop=((DAY, 5),))
    assert not real.is_synthetic
    assert real.weather(datetime(2026, 7, 13, 12, 0)) == ROW
    with pytest.raises(ValueError, match="2026-07-13 5 時"):
        real.weather(datetime(2026, 7, 13, 5, 30))
    with pytest.raises(ValueError, match="2020-01-01 12 時"):
        real.weather(datetime(2020, 1, 1, 12, 0))
    assert real.missing_weather_hours(DAY) == (5,)
    with pytest.raises(ValueError, match="2026-07-13 の 5 時"):
        real.require_weather_days([DAY])
    _real_shaped(w).require_weather_days([DAY])  # 24 時そろえば止まらない
    syn = RD.PerceptionAssets.synthetic(w)
    assert syn.is_synthetic and syn.missing_weather_hours("2020-01-01") == ()
    syn.require_weather_days(["2020-01-01"])  # 合成の世界は確かめない(宣言の天気)
    for h in (3, 12, 20):
        got = syn.weather(datetime(2020, 1, 1, h, 0))
        assert got == syn.declared_weather_by_hour[h]
        assert got[0] == T.WEATHER_WORDS[0] and got[2] == T.HEAT_STAGE_WORDS[1]
    assert [syn.weather(datetime(2020, 1, 1, h))[1] for h in (4, 5, 18, 19)] == [
        T.DAYLIGHT_WORDS[0], T.DAYLIGHT_WORDS[1], T.DAYLIGHT_WORDS[1], T.DAYLIGHT_WORDS[2]]
    # 〔検収 低-6〕合成の世界でも、宣言した表にその時が無ければ止まる(宣言していない定数で埋めない)
    holed = dataclasses.replace(syn, declared_weather_by_hour={h: v for h, v in syn.declared_weather_by_hour.items()
                                                               if h != 7})
    with pytest.raises(ValueError, match="2020-01-01 7 時"):
        holed.weather(datetime(2020, 1, 1, 7, 0))


def test_the_renderer_port_stops_too():
    """何を確かめるか: 描画の口(B3 の時刻の見方)でも、実データの形の資産の行が無ければ止まる(刻みの途中で黙って埋めない)。"""
    w = World.synthetic(n_cells=4, seed=1)
    r = RD.Renderer(w, AgentState(2), _real_shaped(w, drop=((DAY, 12),)))

    def b3(when: datetime) -> str:
        return r._b3(RD._TickCache(when=when, band5=N.time_band(when))).decode("utf-8")

    assert T.TEMPLATES["B3.weather"].format(weather=ROW[0], daylight=ROW[1]) in b3(datetime(2026, 7, 13, 11, 0))
    with pytest.raises(ValueError, match="2026-07-13 12 時"):
        b3(datetime(2026, 7, 13, 12, 0))


# ================================================================ ② 合成の世界の宣言
@pytest.mark.parametrize("processes", [True, False])
def test_synthetic_runs_declare_the_fixed_weather_in_the_manifest(processes):
    """何を確かめるか: 合成の世界のランは、世界過程のあり・なしのどちらでも manifest の ``weather.declared`` に宣言した
    決まった天気(文と 24 時の表)を出す。世界過程の無いランの日ごとの記録は空のまま。"""
    res = run_day(processes=processes, **SMALL_SYN)
    wx = res.run_manifest_fields()["weather"]
    assert wx["declared"]["note"] == RD.SYNTHETIC_WEATHER_NOTE
    # 宣言の表を語で書き下した値と比べる(晴・日照は 0〜4 時が夜明け前・5〜18 時が日中・19〜23 時が日没後・やや暑い)
    want = [[T.WEATHER_WORDS[0], T.DAYLIGHT_WORDS[0 if h < 5 else (1 if h < 19 else 2)], T.HEAT_STAGE_WORDS[1]]
            for h in range(24)]
    assert wx["declared"]["by_hour"] == want
    if not processes:
        assert wx["days"] == [] and res.run_manifest_fields()["replay_date"] == ""


# ================================================================ ④ 資産の片方だけ
@pytest.mark.parametrize("processes", [True, False])
def test_assets_on_one_side_only_stop_at_assembly(monkeypatch, processes):
    """何を確かめるか: 描画に実データの形の W13 の時の表があるのに、環境の過程の日の表が無い(合成の過程の資産)と、組み立てで
    止まる(世界過程のあり・なしの両方=天気だけの環境の過程を立てる前にも止まる)。"""
    monkeypatch.setattr(RD.PerceptionAssets, "load_or_synthetic", classmethod(lambda cls, p, world: _real_shaped(world)))
    with pytest.raises(ValueError, match="片方だけ"):
        run_day(processes=processes, **SMALL_SYN)


def test_the_reverse_one_side_stops_too(monkeypatch):
    """何を確かめるか(検収 中-1・再検収 低-A): 描画の資産が合成なのに、環境の過程に W13 の日の表があると、組み立てで止まる
    (合成の世界の決まった天気「晴」で黙って埋めない)。止める文は当たった形の事実と直し方を書く: 合成の世界なら「世界が合成
    なので描画の資産も合成」(ファイルが無いとは書かない)、注入の描画なら「注入の描画の資産が合成」。過程の資産も合成なら
    止まらない(②)。"""
    monkeypatch.setattr(ASM, "load_process_assets_or_synthetic", lambda path, assets: _w13_process_assets())
    with pytest.raises(ValueError, match=re.escape("描画の資産が合成(世界が合成なので描画の資産も合成。描画のファイルの有無は"
                                                   "見ていない)なのに、環境の過程に W13 の日の表がある。直し方: 合成の世界で"
                                                   "回すなら環境の過程に W13 の日の表を渡さない")) as e:
        run_day(**SMALL_SYN)
    assert "世界が実データ" not in str(e.value) and "ファイルが無い" not in str(e.value)
    w = World.synthetic(n_cells=9, seed=1)
    with pytest.raises(ValueError, match=re.escape("描画の資産が合成(注入の描画の資産が合成)なのに、環境の過程に W13 の日の表が"
                                                   "ある。直し方: 注入の描画に実データの描画の資産を持たせる")):
        run_day(renderer=_InjectedRenderer(RD.PerceptionAssets.synthetic(w)), **SMALL_SYN)


def test_a_real_world_with_synthetic_perception_assets_stops(monkeypatch, tmp_path):
    """何を確かめるか(検収 中-1・再検収 低-A): 世界が実データなのに描画の資産が合成だと、世界過程の無いランでも組み立てで止まる
    (世界の資産の出どころを実データの印に替えた合成の世界で=data 不要)。止める文は、world_dir が無いときはそう書き、world_dir
    があるときは無い描画のファイルの名を書く。環境の過程にも W13 の日の表があれば、当たった条件を両方書く。"""
    def world() -> World:  # 世界はランが書き換えうるのでランごとに作る
        w = World.synthetic(n_cells=9, seed=1)
        w.assets = dataclasses.replace(w.assets, source="test-real")
        return w

    kw = dict(n_agents=30, seed=1, ticks=60, checkpoint_every=60)
    with pytest.raises(ValueError, match=re.escape("描画の資産が合成(world_dir が無いので描画のファイルを読めない)なのに、"
                                                   "世界が実データ。直し方: 描画の資産のファイルがそろった world_dir を渡す")):
        run_day(world=world(), processes=False, **kw)
    with pytest.raises(ValueError, match=re.escape("描画の資産が合成(world_dir に描画の資産のファイルが無い: "
                                                   + "・".join(RD.PerceptionAssets.REQUIRED_FILES)
                                                   + ")なのに、世界が実データ。直し方: world_dir に描画の資産のファイルを"
                                                   "そろえる")):
        run_day(world=world(), processes=False, world_dir=str(tmp_path), **kw)  # 空の置き場=描画の 7 ファイルが全部無い
    monkeypatch.setattr(ASM, "load_process_assets_or_synthetic", lambda path, assets: _w13_process_assets())
    with pytest.raises(ValueError, match=re.escape("なのに、世界が実データ・環境の過程に W13 の日の表がある。直し方: "
                                                   "描画の資産の")):
        run_day(world=world(), **kw)


# ================================================================ ⑤ 注入の描画
class _InjectedRenderer(StubRenderer):
    """注入の描画(アダプタでない)の代わり: スタブの描画に B3 の天気の口と実データの形の資産を持たせた物。"""

    def __init__(self, assets: RD.PerceptionAssets) -> None:
        super().__init__()
        self.assets = assets
        self.weather_date_fn = None
        self.weather_words_fn = None
        self.weather_words_key_fn = None


def test_an_injected_renderer_is_checked_at_assembly():
    """何を確かめるか: 注入の描画(アダプタでない)も組み立ての確かめに入る。世界過程のあるランで過程に天気の日の表が無ければ
    止まり、世界過程の無いランでは暦の日付(ランの日)の 24 時がそろえば回り、欠ければ日付と時を書いて止まる。"""
    w = World.synthetic(n_cells=9, seed=1)  # 資産の形だけ(ランは自分の合成の世界=同じ 9 セル)
    with pytest.raises(ValueError, match="片方だけ"):
        run_day(renderer=_InjectedRenderer(_real_shaped(w)), **SMALL_SYN)
    run_day(renderer=_InjectedRenderer(_real_shaped(w)), processes=False, **SMALL_SYN)
    with pytest.raises(ValueError, match="2026-07-13 の 0 時"):
        run_day(renderer=_InjectedRenderer(_real_shaped(w, drop=((DAY, 0),))), processes=False, **SMALL_SYN)


def test_wire_weather_puts_the_main_path_hooks_on_any_renderer():
    """何を確かめるか: ``state_io.wire_weather`` は描画(注入の描画を含む)に本筋と同じ口を挿す=天気の日=環境の過程の再生日・
    天候の語=再生日の W13 の行・日照と暑さ=環境の過程の語・キャッシュの鍵=(再生日, 暦の日付)。行が無ければ止まる。"""
    w = World.synthetic(n_cells=4, seed=1)
    r = RD.Renderer(w, AgentState(2), _real_shaped(w, days=("2026-08-03",), drop=(("2026-08-03", 9),)))
    env = SimpleNamespace(replay_date="2026-08-03", assets=SimpleNamespace(has_weather=True),
                          b3_sun_heat=lambda h: (T.DAYLIGHT_WORDS[1], T.HEAT_STAGE_WORDS[3]))
    SIO.wire_weather(r, env)
    when = datetime(2026, 9, 14, 12, 0)  # 暦の日付は再生日と別
    assert r.weather_date_fn() == "2026-08-03"
    assert r.weather_words_fn(when) == (ROW[0], T.DAYLIGHT_WORDS[1], T.HEAT_STAGE_WORDS[3])
    assert r.weather_words_key_fn(when) == ("2026-08-03", "2026-09-14")
    with pytest.raises(ValueError, match="2026-08-03 9 時"):
        r.weather_words_fn(datetime(2026, 9, 14, 9, 0))


def test_wire_weather_puts_only_the_day_hook_when_the_environment_has_no_weather_days():
    """何を確かめるか(検収 低-3): 環境の過程に W13 の日の表が無い(``has_weather`` が偽)と、日の口だけを挿し、語と鍵の口は
    挿さない(前の結線と同じ分かれ)。"""
    w = World.synthetic(n_cells=4, seed=1)
    r = RD.Renderer(w, AgentState(2), _real_shaped(w))
    SIO.wire_weather(r, SimpleNamespace(replay_date="", assets=SimpleNamespace(has_weather=False)))
    assert r.weather_date_fn is not None and r.weather_date_fn() is None
    assert r.weather_words_fn is None and r.weather_words_key_fn is None


def test_an_injected_renderer_gets_the_main_path_hooks_in_a_run(monkeypatch):
    """何を確かめるか(検収 低-3): 世界過程のあるランで、注入の描画(アダプタでない)に本筋の口が実際に挿さる(天気の日=環境の
    過程の再生日・天候の語=その日の行・鍵=(再生日, 暦の日付))。過程の資産は試験の中で作る W13 の 2 日分(data 不要)。"""
    monkeypatch.setattr(ASM, "load_process_assets_or_synthetic", lambda path, assets: _w13_process_assets())
    w = World.synthetic(n_cells=9, seed=1)
    inj = _InjectedRenderer(_real_shaped(w, days=(DAY, DAY2), words={DAY: "雨"}))
    res = run_day(renderer=inj, **SMALL_SYN)
    assert res.run_manifest_fields()["weather"]["days"][0]["replay_date"] == DAY
    assert inj.weather_date_fn() == DAY
    assert inj.weather_words_fn(datetime(2026, 7, 13, 12, 0))[0] == "雨"
    assert inj.weather_words_key_fn(datetime(2026, 7, 13, 12, 0)) == (DAY, DAY)


# ================================================================ ③′ 天気だけの環境の過程(data 不要)
def test_a_run_without_processes_builds_the_weather_only_environment_without_data(monkeypatch, made):
    """何を確かめるか(検収 低-3・低-1): data の無い機械でも、世界過程の無いランで天気だけの環境の過程が立ち、日の頭に 2 日目の
    再生日を引き直し(暦の日付=窓の中=その日)、B3 の語がその日の行から出る。manifest の日ごとの記録(影は空)・一番上の
    ``replay_date``・``frozen_sources`` の W13 の 2 表(W13 でない表は写さない)がそろい、宣言は出ず、体感温度は書かない。"""
    monkeypatch.setattr(RD.PerceptionAssets, "load_or_synthetic", classmethod(
        lambda cls, p, world: _real_shaped(world, days=(DAY, DAY2), words={DAY: "曇", DAY2: "雨"})))
    monkeypatch.setattr(ASM, "load_process_assets_or_synthetic", lambda path, assets: _w13_process_assets())
    res = run_day(n_agents=20, seed=1, n_cells=9, ticks=1_440, sim_days=2, checkpoint_every=1_440, processes=False)
    ren = made[-1]
    env = ren.weather_env
    assert env is not None and env.n_updates == 0 and env.replay_date == DAY2
    m = res.run_manifest_fields()
    days = [(d["calendar_date"], d["replay_date"], d["how"], d["shadow_date"]) for d in m["weather"]["days"]]
    assert days == [(DAY, DAY, "actual", ""), (DAY2, DAY2, "actual", "")]
    assert m["replay_date"] == DAY2 and "declared" not in m["weather"]
    fs = m["frozen_sources"]
    assert fs["process:w13_weather_days.parquet"] == "d" * 64 and fs["process:w13_weather_hourly.parquet"] == "h" * 64
    assert not any(k.startswith("process:") and "w13_" not in k for k in fs)
    assert ren.weather_words_fn(datetime(2026, 7, 14, 12, 0))[0] == "雨"


def test_a_run_without_processes_draws_from_the_stratum_like_the_main_path_without_data(monkeypatch, made):
    """何を確かめるか(再検収 低-B): data の無い機械でも、開始日が W13 の窓の外なら、世界過程の無いランの天気だけの環境の過程は
    層から再生日を引き(``sample_calendar_day``・環境の seed)、世界過程のあるランと同じ再生日と層になる。B3 の語は世界過程の
    あるランと同じで、天候の語は引いた再生日の行から出る。資産は試験の中で作る W13 の 3 日分(夏の平日・天候型が 3 つ)。"""
    days, types = (DAY, DAY2, "2026-07-15"), ("曇", "雨", "晴")
    words = dict(zip(days, types))
    pa = _w13_process_assets(days, types)
    monkeypatch.setattr(RD.PerceptionAssets, "load_or_synthetic", classmethod(
        lambda cls, p, world: _real_shaped(world, days=days, words=words)))
    monkeypatch.setattr(ASM, "load_process_assets_or_synthetic", lambda path, assets: pa)
    kw = dict(n_agents=20, seed=1, n_cells=9, ticks=60, checkpoint_every=60, start_sim_datetime="2026-07-27")  # 窓の外の月曜
    on = run_day(**kw)
    ren_on = made[-1]
    off = run_day(processes=False, **kw)
    ren_off = made[-1]
    d_on = on.run_manifest_fields()["weather"]["days"][0]
    d_off = off.run_manifest_fields()["weather"]["days"][0]
    assert d_off["calendar_date"] == "2026-07-27" and d_off["how"] == d_on["how"] == "sampled"
    assert (d_off["replay_date"], d_off["stratum"]) == (d_on["replay_date"], d_on["stratum"])
    want = sample_calendar_day(ren_off.weather_env.master_seed, 0, "夏", "平日", pa)
    assert (d_off["replay_date"], d_off["stratum"], d_off["widened"]) == want
    assert off.run_manifest_fields()["replay_date"] == d_off["replay_date"]
    for h in (0, 12, 23):
        when = datetime(2026, 7, 27, h, 0)
        assert ren_off.weather_words_fn(when) == ren_on.weather_words_fn(when)
        assert ren_off.weather_words_fn(when)[0] == words[d_off["replay_date"]]


# ================================================================ ⑥ 日の頭
def test_relay_weather_picks_the_day_without_processes_and_checks_the_rows():
    """何を確かめるか: 日の頭の ``state_io.relay_weather`` は、世界過程の無いランでは描画の天気だけの環境の過程に日番号で
    再生日を引き直させ、引いた再生日の 24 時の行を確かめる(欠ければ止まる)。世界過程のあるランは引き直さない(runner の側)。"""
    w = World.synthetic(n_cells=4, seed=1)
    picked: list[int] = []
    env = SimpleNamespace(replay_date="2026-08-03", pick_day=picked.append)
    rend = SimpleNamespace(weather_env=env, assets=_real_shaped(w, days=("2026-08-03",)))
    b = SimpleNamespace(layers=SimpleNamespace(runner=None, renderer=rend))
    SIO.relay_weather(b, 2)
    assert picked == [2] and SIO.weather_source(b) is env
    env.replay_date = "2026-08-04"  # 表に無い日を引いた
    with pytest.raises(ValueError, match="2026-08-04 の 0,1,"):
        SIO.relay_weather(b, 3)
    runner = SimpleNamespace(environment=SimpleNamespace(replay_date="2026-08-03", pick_day=picked.append))
    b.layers.runner = runner
    SIO.relay_weather(b, 4)
    assert picked == [2, 3] and SIO.weather_source(b) is runner.environment
    b.layers.renderer = None  # 描画の無いラン(スタブ)は確かめない
    SIO.relay_weather(b, 5)


# ================================================================ ③ 世界過程の無い実データのラン
@needs_world
def test_a_run_without_processes_draws_the_same_replay_day_as_the_main_path(made):
    """何を確かめるか: 世界過程の無い実データのランも、本筋と同じ規則・同じ環境の seed で再生日を引き(窓の外の開始日=層から
    引く)、B3 の天候・日照・暑さの語が本筋のランと同じ。天気だけの環境の過程は体感温度を書かず(更新 0 回)、影も開かない。
    実データのランには、世界過程のあり・なしとも宣言が出ない(負の対照)。一番上の ``replay_date`` と ``frozen_sources`` の
    W13 の 2 表は、世界過程のあるランと同じ値。"""
    kw = dict(n_agents=60, seed=1, world_dir=str(WORLD_DIR), ticks=60, checkpoint_every=60,
              start_sim_datetime="2026-09-14")
    on = run_day(world=World.load(WORLD_DIR), **kw)  # 世界はランが書き換えるのでランごとに読む
    ren_on = made[-1]
    off = run_day(world=World.load(WORLD_DIR), processes=False, **kw)
    ren_off = made[-1]
    d_on = on.run_manifest_fields()["weather"]["days"][0]
    d_off = off.run_manifest_fields()["weather"]["days"][0]
    assert d_off["calendar_date"] == "2026-09-14" and d_off["how"] == "sampled"
    assert (d_off["replay_date"], d_off["stratum"]) == (d_on["replay_date"], d_on["stratum"])
    assert d_off["shadow_date"] == "" and "declared" not in off.run_manifest_fields()["weather"]
    assert "declared" not in on.run_manifest_fields()["weather"]
    m_on, m_off = on.run_manifest_fields(), off.run_manifest_fields()
    assert m_off["replay_date"] == m_on["replay_date"] == d_on["replay_date"]
    for name in ("w13_weather_days.parquet", "w13_weather_hourly.parquet"):
        assert m_off["frozen_sources"][f"process:{name}"] == m_on["frozen_sources"][f"process:{name}"]
    assert ren_on.weather_env is None and ren_off.weather_env is not None
    assert ren_off.weather_env.n_updates == 0  # 体感温度は書かない(刻みの更新を呼ばない)
    for h in (0, 6, 12, 18, 23):
        when = datetime(2026, 9, 14, h, 0)
        assert ren_off.weather_words_fn(when) == ren_on.weather_words_fn(when)
        assert ren_off.weather_words_fn(when)[0] == ren_off.assets.weather_by_date_hour[(d_on["replay_date"], h)][0]
