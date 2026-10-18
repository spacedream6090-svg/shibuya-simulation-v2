"""〔小さな版上げ・回答 10-13b §7 の 2〕範囲外の人の既定の食事時刻と初期の空腹を W17 v2 の日課の分布(構築側)から。

受入(発注 meal_w17):
- エンジンが検証側の錨のファイル(``hunger_energy_validation_anchors_v0.json``・``presence_validation_anchors_v0.json``)を
  開かない(open の監査フック・負の対照=旧値の腕と「読む行を植えた」ランは落ちる)。
- 既定 w17 の決定性(同じ seed で同じ・鍵は体の番号=体の数に依らない)・分布から引いた時刻が W17 の分布と一致(JSD)・
  初期の空腹の範囲・既定の食事時刻を使っている体の割合の計器・2 日のラン・再開=通し(両方の腕)。
- 腕 validation は旧値の再現(前の版の既定の時刻=1 つの値・初期の空腹も 1 つの既定の分)。19 構成の byte-check は記録
  ``docs/bench/analysis/wallbounce-1012/meal_w17/README.md``。

**検証側の値(第 18-1 表の数値)はこの試験に写さない**(旧値の腕は「前の版の模型と同じ」で比べる)。
"""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

import numpy as np
import pytest

from shibuya import cli
from shibuya.agents.weekly import ACTIVITY_WORDS, N_DAYS, PLACE_WORDS, WeeklySchedule
from shibuya.engine import energy as E
from shibuya.engine.run import run_day

WORLD_DIR = Path("data/world/v2")
real_data = pytest.mark.requires_data("world_v2:w17_schedule.parquet")
TPD = 1_440
VALIDATION_TOKENS = ("hunger_energy_validation_anchors", "presence_validation_anchors")
SYN = dict(n_agents=80, seed=3, n_cells=16, hunger_model="energy")


# ================================================================= 監査フック(一度入れたら外せない=印が立つ間だけ控える)
_OPENED: list[str] = []
_WATCH = {"on": False}


def _hook(event: str, args: tuple) -> None:
    if not _WATCH["on"] or event != "open" or not args:
        return
    p = args[0]
    if isinstance(p, (str, bytes, os.PathLike)):
        s = os.fsdecode(os.fspath(p)).replace("\\", "/").lower()
        if any(t in s for t in VALIDATION_TOKENS):
            _OPENED.append(s.rsplit("/", 1)[-1])


sys.addaudithook(_hook)


class _watch:
    def __enter__(self) -> list[str]:
        _OPENED.clear()
        _WATCH["on"] = True
        return _OPENED

    def __exit__(self, *exc: object) -> None:
        _WATCH["on"] = False


@pytest.fixture(autouse=True)
def _arm_back():
    yield
    E.set_meal_default(E.DEFAULT_MEAL_DEFAULT)


def _weekly(rows, n_agents):
    rows = sorted(rows, key=lambda r: (r[0], r[1]))
    counts = np.zeros(n_agents * N_DAYS, dtype=np.int64)
    for r in rows:
        counts[int(r[0]) * N_DAYS] += 1
    offset = np.zeros(counts.size + 1, dtype=np.int64)
    np.cumsum(counts, out=offset[1:])
    return WeeklySchedule(
        source=None, agent_id=np.arange(n_agents, dtype=np.int64), day_offset=offset,
        start_min=np.asarray([r[1] for r in rows], dtype=np.int16),
        end_min=np.asarray([r[2] for r in rows], dtype=np.int16),
        activity=np.asarray([r[3] for r in rows], dtype=np.int8),
        place_kind=np.asarray([r[4] for r in rows], dtype=np.int8),
        target_cell=np.full(len(rows), -1, dtype=np.int32), seq=np.arange(len(rows), dtype=np.int16),
    )


def _jsd(p: np.ndarray, q: np.ndarray) -> float:
    p = np.asarray(p, dtype=np.float64) / max(1.0, float(np.sum(p)))
    q = np.asarray(q, dtype=np.float64) / max(1.0, float(np.sum(q)))
    m = (p + q) / 2.0

    def kl(a: np.ndarray, b: np.ndarray) -> float:
        k = a > 0
        return float(np.sum(a[k] * np.log2(a[k] / b[k])))

    return 0.5 * kl(p, m) + 0.5 * kl(q, m)


def _model(mode: str = "w17") -> E.EnergyModel:
    anc, md5 = E.load_anchors(mode=mode)
    return E.EnergyModel(anc, md5, meal_default=mode)


# ================================================================= 1. 検証側の錨を開かない(負の対照つき)
def test_default_engine_never_opens_the_validation_anchor_files():
    with _watch() as opened:
        anc, md5 = E.load_anchors()
        E.EnergyModel(anc, md5)
        res = run_day(ticks=120, **SYN)
    assert res.run_manifest_fields()["energy"]["meal_default"] == "w17"
    assert opened == [], f"既定のランが検証側の錨を開いた: {opened}"
    assert "ssb2021_t18_1_weekday" not in anc and "ssb2021_meal_rate_15min" not in anc
    assert md5 == hashlib.md5(E.ANCHORS_BUILD_PATH.read_bytes()).hexdigest()
    assert E.anchors_paths() == (E.ANCHORS_BUILD_PATH,)


def test_negative_control_validation_arm_and_a_planted_read_are_caught(monkeypatch):
    # (a) 旧値の腕は検証側を読む=フックが見つける(フックが働いていることの確かめ)
    E.set_meal_default("validation")
    with _watch() as opened:
        run_day(ticks=60, **SYN)
    assert "hunger_energy_validation_anchors_v0.json" in opened
    # (b) 既定の腕に「読む行」を植えると落ちる(錨の読み口が 2 本を返すように差し替える)
    E.set_meal_default("w17")
    monkeypatch.setattr(E, "anchors_paths", lambda mode=None: E.ANCHORS_PATHS)
    with _watch() as opened:
        try:
            run_day(ticks=60, **SYN)
        except Exception:  # noqa: BLE001 - 読んだかどうかだけを見る
            pass
    assert "hunger_energy_validation_anchors_v0.json" in opened


def test_energy_source_names_no_validation_file():
    """コードの読み口: 既定の腕で開く道筋に検証側の名が無い(錨の名は構築側だけ)。"""
    assert all("validation" not in q.name for q in E.anchors_paths("w17"))
    assert E.anchors_rel("w17") == "docs/bench/anchors/hunger_energy_build_anchors_v0.json"
    assert E.anchors_rel("validation") == E.ANCHORS_REL
    with pytest.raises(ValueError):
        E.EnergyModel(*E.load_anchors(mode="w17"), meal_default="validation")  # 旧の腕に構築側だけ=止める


# ================================================================= 2. 分布と引き(決定性・体の数に依らない・JSD)
def test_draw_is_deterministic_and_keyed_by_the_body():
    d = E.MealStartDistribution.frozen()
    a = d.draw(500, 7)
    assert np.array_equal(a, d.draw(500, 7))
    assert not np.array_equal(a, d.draw(500, 8))
    assert np.array_equal(a[:300], d.draw(300, 7))  # 体の数を変えても前の体は同じ(鍵=体の番号)
    for s, key in enumerate(("breakfast", "lunch", "dinner")):
        lo, hi = E.MEAL_WINDOWS_MIN[key]
        assert int(a[:, s].min()) >= lo and int(a[:, s].max()) < hi
    assert np.unique(a[:, 2]).size > 50  # 1 つの値ではない(分布から引く)


def test_frozen_draw_matches_the_frozen_histogram():
    d = E.MealStartDistribution.frozen()
    m = d.draw(200_000, 1)
    for s, key in enumerate(("breakfast", "lunch", "dinner")):
        lo, hi = E.MEAL_WINDOWS_MIN[key]
        h = np.bincount((m[:, s] - lo) // 15, minlength=(hi - lo) // 15)
        assert _jsd(h, np.asarray(E.W17V2_MEAL_START_HIST_15MIN[key])) < 1e-3, key
    assert d.n_samples() == {k: int(sum(v)) for k, v in E.W17V2_MEAL_START_HIST_15MIN.items()}
    assert d.manifest()["frozen"]["sha256"] == E.W17V2_FROZEN_SOURCE["sha256"]


def test_from_weekly_uses_the_day_rows_then_all_days_then_frozen():
    EAT, OUT = ACTIVITY_WORDS.index("食事"), PLACE_WORDS.index("域外")
    w = _weekly([(0, 760, 800, EAT, OUT), (1, 700, 730, EAT, OUT), (1, 1200, 1230, EAT, OUT)], 2)
    d = E.MealStartDistribution.from_weekly(w, 0)
    assert d.kinds == (E.SOURCE_FROZEN, E.SOURCE_W17_DAY, E.SOURCE_W17_DAY)
    assert d.sorted_min[1].tolist() == [700, 760] and d.sorted_min[2].tolist() == [1200]
    got = d.draw(100, 2)
    assert set(got[:, 1].tolist()) <= {700, 760} and set(got[:, 2].tolist()) == {1200}
    # その日に行の無い曜日は全曜日をまとめる
    d3 = E.MealStartDistribution.from_weekly(w, 3)
    assert d3.kinds == (E.SOURCE_FROZEN, E.SOURCE_W17_ALL_DAYS, E.SOURCE_W17_ALL_DAYS)
    assert E.MealStartDistribution.from_weekly(None).kinds == (E.SOURCE_FROZEN,) * 3
    assert E.meal_start_distribution(w, 0, mode="validation") is None


@real_data
def test_draw_from_the_world_w17_matches_its_meal_rows_jsd():
    from shibuya.agents.weekly import load_weekly

    w = load_weekly(WORLD_DIR)
    d = E.MealStartDistribution.from_weekly(w, 0)
    assert d.kinds == (E.SOURCE_W17_DAY,) * 3
    m = d.draw(w.n_agents, 1)
    for s, key in enumerate(("breakfast", "lunch", "dinner")):
        lo, hi = E.MEAL_WINDOWS_MIN[key]
        want = np.bincount(d.sorted_min[s] - lo, minlength=hi - lo)
        got = np.bincount(m[:, s] - lo, minlength=hi - lo)
        # 1 分刻み・体の数ぶんの引き(朝は行が 1.1 万本と少ない=引きの揺れの分だけ緩い)
        assert _jsd(got, want) < (0.02 if key == "breakfast" else 0.005), key
        hw = np.bincount((d.sorted_min[s] - lo) // 15, minlength=(hi - lo) // 15)
        assert np.array_equal(hw, np.asarray(E.W17V2_MEAL_START_HIST_15MIN[key])), "凍結の表が世界の W17 と違う"


# ================================================================= 3. 範囲外の予定・初期の空腹・計器
def _rows3():
    SLEEP, WORK, EAT = (ACTIVITY_WORDS.index(x) for x in ("就寝", "勤務", "食事"))
    HOME, OUT = PLACE_WORDS.index("自宅"), PLACE_WORDS.index("域外")
    return [
        (0, 0, 420, SLEEP, HOME), (0, 750, 780, EAT, OUT), (0, 1290, 1320, EAT, OUT),
        (1, 0, 480, SLEEP, HOME), (1, 540, 1080, WORK, OUT),
    ]


def test_out_of_area_defaults_are_drawn_per_body_and_rows_are_kept():
    w = _weekly(_rows3(), 2)
    n = 5
    oom = E.OutOfAreaMeals(_model("w17"), n, TPD, weekly=w, seed=11)
    drawn = oom.default_min
    assert drawn.shape == (n, 3)
    expect = oom.distribution.draw(n, 11)
    assert np.array_equal(drawn, expect)
    sched = {(int(a), int(t), int(s), bool(f)) for a, t, s, f in zip(oom.agent, oom.tick, oom.slot, oom.from_row)}
    assert (0, 750, 1, True) in sched and (0, 1290, 2, True) in sched  # 行由来はそのまま
    assert (0, int(drawn[0, 0]), 0, False) in sched  # 朝は行が無い=引いた既定
    assert not any(a == 0 and s in (1, 2) and not f for a, _t, s, f in sched)  # 行のある窓には既定を置かない
    for i in range(1, n):
        for s in range(3):
            assert (i, int(drawn[i, s]), s, False) in sched
    # 初期の空腹の前夜の夕食=自分の夕の行(体 0)・無ければ引いた夕食
    assert oom.prev_dinner_min[0] == 1290 and np.array_equal(oom.prev_dinner_min[1:], drawn[1:, 2])
    use = oom.default_use_summary()
    assert use["agents"] == n and use["agents_with_default_slot"] == n and use["agents_all_three_default"] == n - 1
    assert use["agents_without_plan_day"] == n - 2 and use["default_slots_by_slot"]["dinner"] == n - 1


def test_validation_arm_keeps_the_single_old_default_times():
    w = _weekly(_rows3(), 2)
    m = _model("validation")
    oom = E.OutOfAreaMeals(m, 4, TPD, weekly=w, seed=11)
    assert oom.distribution is None and oom.prev_dinner_min is None
    for s, key in enumerate(("breakfast", "lunch", "dinner")):
        assert set(oom.default_min[:, s].tolist()) == {m.default_meal_min[key]}
    lay = E.EnergyLayer(model=m, n_agents=4, out_of_area=oom)
    assert lay.initial_dinner_min is None
    eer = np.asarray([2000.0, 1800.0, 2400.0, 1500.0], dtype=np.float32)
    from shibuya.engine.body import rules as BR

    got = BR.initial_energy_values(lay, eer).since_meal
    assert np.array_equal(got, m.initial_since_meal(eer))  # 前の版と同じ 1 つの既定の分


def test_initial_hunger_comes_from_the_previous_dinner_and_stays_in_range():
    from shibuya.engine.body import rules as BR

    m = _model("w17")
    n = 400
    oom = E.OutOfAreaMeals(m, n, TPD, weekly=None, seed=5)
    lay = E.EnergyLayer(model=m, n_agents=n, out_of_area=oom)
    eer = np.linspace(1200.0, 3200.0, n).astype(np.float32)
    since = BR.initial_energy_values(lay, eer).since_meal
    dm = E.MealStartDistribution.frozen().draw(n, 5)[:, 2]
    assert np.array_equal(lay.initial_dinner_min, dm)
    want = (eer.astype(np.float64) * (TPD - dm) / TPD).astype(np.float32)
    assert np.array_equal(since, want)
    # 前夜の夕食は夕の窓(17:00〜23:59)=比 since/(eer/3) は (3/1440, 3·420/1440] に入る・体ごとに違う
    ratio = since.astype(np.float64) / (eer.astype(np.float64) / 3.0)
    assert ratio.min() > 3.0 / TPD - 1e-6 and ratio.max() <= 3.0 * 420 / TPD + 1e-6
    assert np.unique(dm).size > 20
    # 実際のランでも 0:00 の値はこの式(1 刻み後の値から 1 刻みの消費を引くと戻る=刻み 0 の SoA を直に見る)
    res = run_day(ticks=1, **SYN)
    r = res.agents.registry
    dm_run = E.MealStartDistribution.frozen().draw(SYN["n_agents"], SYN["seed"])[:, 2]
    e_run = np.asarray(r.eer_kcal, dtype=np.float64)
    since0 = (e_run * (TPD - dm_run) / TPD)
    got = np.asarray(r.since_meal_kcal, dtype=np.float64)
    assert np.all(got >= since0 - 1e-3) and np.all(got - since0 < e_run / TPD * 4.0)


def test_manifest_has_the_source_and_the_share_gauge():
    res = run_day(ticks=60, **SYN)
    e = res.run_manifest_fields()["energy"]
    assert e["meal_default"] == "w17"
    src = e["meal_default_source"]
    assert src["kind"] == {"breakfast": E.SOURCE_FROZEN, "lunch": E.SOURCE_FROZEN, "dinner": E.SOURCE_FROZEN}
    assert src["rng_domain"] == E.MEAL_DEFAULT_RNG_DOMAIN and set(src["quantiles_min_p5_p25_p50_p75_p95"]) == {
        "breakfast", "lunch", "dinner"}
    use = e["meal_default_use"]
    assert use["mode"] == "w17" and use["agents"] == SYN["n_agents"]
    assert use["share_with_default_slot"] == 1.0 and use["agents_without_plan_day"] == SYN["n_agents"]  # 合成=計画なし
    assert set(use["ate"]) == {"agents", "share", "meals"}
    E.set_meal_default("validation")
    ev = run_day(ticks=60, **SYN).run_manifest_fields()["energy"]
    assert ev["meal_default"] == "validation" and ev["anchors"] == E.ANCHORS_REL
    assert ev["meal_default_source"]["kind"].startswith("validation_anchors")


def test_cli_flag_and_the_fingerprint_stop_a_resume_with_the_other_arm(tmp_path):
    import inspect

    assert '"--meal-default"' in inspect.getsource(cli.main)
    E.set_meal_default("validation")
    a = run_day(ticks=120, state_out=tmp_path / "s", stop_at_tick=60, **SYN)
    path = tmp_path / "s" / a.resume["state_files"][-1]["file"]
    E.set_meal_default("w17")
    with pytest.raises(ValueError):
        run_day(ticks=120, resume_from=path, **SYN)
    E.set_meal_default("validation")
    b = run_day(ticks=120, resume_from=path, **SYN)
    assert b.final_hash == run_day(ticks=120, **SYN).final_hash


# ================================================================= 4. 2 日のラン・再開=通し(両方の腕)
@pytest.mark.parametrize("mode", ["w17", "validation"])
def test_two_day_run_resume_equals_straight(tmp_path, mode):
    E.set_meal_default(mode)
    kw = dict(SYN, ticks=TPD, sim_days=2, checkpoint_every=360)
    straight = run_day(**kw)
    a = run_day(state_out=tmp_path / "s", stop_at_tick=TPD + 300, **kw)
    files = a.resume["state_files"]
    b = run_day(resume_from=tmp_path / "s" / files[-1]["file"], **kw)
    want = [(c.tick, c.combined) for c in straight.checkpoints if c.tick >= TPD + 300]
    got = [(c.tick, c.combined) for c in b.checkpoints if c.tick >= TPD + 300]
    assert want and got == want
    assert b.final_hash == straight.final_hash
    assert straight.run_manifest_fields()["energy"]["meal_default"] == mode


def test_w17_moves_the_result_and_validation_keeps_one_time_for_any_seed():
    """〔検収 L3〕1 日: 既定 w17 は旧値と違う結果(版上げ=変わった量は記録の表)。旧値の腕の既定の時刻は seed に依らず
    全員 1 つの値(引きを使わない)、w17 は seed で変わる。"""
    kw = dict(SYN, ticks=TPD)
    w17 = run_day(**kw).final_hash
    E.set_meal_default("validation")
    old = run_day(**kw).final_hash
    assert w17 != old
    mv, mw = _model("validation"), _model("w17")
    for seed in (1, 2, 99):
        dv = E.OutOfAreaMeals(mv, 50, TPD, weekly=None, seed=seed).default_min
        assert all(np.unique(dv[:, s]).size == 1 for s in range(3))
        assert np.array_equal(dv, E.OutOfAreaMeals(mv, 50, TPD, weekly=None, seed=1).default_min)
    a = E.OutOfAreaMeals(mw, 50, TPD, weekly=None, seed=1).default_min
    b = E.OutOfAreaMeals(mw, 50, TPD, weekly=None, seed=2).default_min
    assert not np.array_equal(a, b)


#: 〔検収 L2〕凍結の表の中身の sha256(data の無い CI でも検査。世界の W17 との一致は data つきの試験)。
FROZEN_HIST_SHA256 = "6aa853445ad1f48b3d268a25491611da0019f63ec2ea4375715eb6c1aee28357"
FROZEN_SOURCE_SHA256 = "cdbe0773e36f9cd5e29180d875aab485f7cc6776690727f898e2dca70cc11be9"


def test_frozen_table_is_pinned_and_read_only():
    import json

    body = json.dumps({k: list(v) for k, v in E.W17V2_MEAL_START_HIST_15MIN.items()}, sort_keys=True)
    assert hashlib.sha256(body.encode()).hexdigest() == FROZEN_HIST_SHA256
    src = json.dumps(dict(E.W17V2_FROZEN_SOURCE), sort_keys=True, ensure_ascii=False)
    assert hashlib.sha256(src.encode()).hexdigest() == FROZEN_SOURCE_SHA256
    with pytest.raises(TypeError):
        E.W17V2_MEAL_START_HIST_15MIN["breakfast"] = (0,)  # type: ignore[index]
    with pytest.raises(TypeError):
        E.W17V2_FROZEN_SOURCE["sha256"] = "x"  # type: ignore[index]
    d = E.MealStartDistribution.frozen()
    with pytest.raises(ValueError):
        d.hist[0][0] = 1
    EAT, OUT = ACTIVITY_WORDS.index("食事"), PLACE_WORDS.index("域外")
    dw = E.MealStartDistribution.from_weekly(_weekly([(0, 760, 800, EAT, OUT)], 1), 0)
    with pytest.raises(ValueError):
        dw.sorted_min[1][0] = 1


@real_data
def test_validation_arm_reproduces_the_pre_meal_w17_final_on_the_world():
    """〔検収 M1〕旧値の再現を守る: 世界資産 5,000 体・1 日・seed 1・語彙 v3(w6_v3_default)を旧値の腕で回すと、前の版の
    final と呼数(定数 ``_K19_PRE_MEAL_W17``・``_T7_V3_FINAL_PRE_MEAL_W17``)と同じ。"""
    from tests.engine.test_state_checks_10f import _K19_PRE_MEAL_W17
    from tests.engine.test_state_ledger_10b import _T7_V3_FINAL_PRE_MEAL_W17

    assert _K19_PRE_MEAL_W17 == _T7_V3_FINAL_PRE_MEAL_W17
    E.set_meal_default("validation")
    res = cli.run(n_agents=5_000, seed=1, world_dir=str(WORLD_DIR), vocab_version="v3", activity=True)
    assert res.final_hash[:16] == _T7_V3_FINAL_PRE_MEAL_W17 and int(res.llm_calls) == PRE_MEAL_W17_V3_CALLS
    assert res.run_manifest_fields()["energy"]["meal_default"] == "validation"


#: 前の版(旧値の腕)の w6_v3_default の呼数(記録 meal_w17 §3)。
PRE_MEAL_W17_V3_CALLS = 64_528


@real_data
@pytest.mark.parametrize("mode", ["w17", "validation"])
def test_world_two_day_resume_equals_straight(tmp_path, mode):
    E.set_meal_default(mode)
    kw = dict(n_agents=300, seed=1, world_dir=str(WORLD_DIR), sim_days=2, vocab_version="v3", activity=True)
    straight = cli.run(**kw)
    a = cli.run(state_out=tmp_path / "s", stop_at_tick=TPD + 420, **kw)
    b = cli.run(resume_from=tmp_path / "s" / a.resume["state_files"][-1]["file"], **kw)
    assert b.final_hash == straight.final_hash
    e = straight.run_manifest_fields()["energy"]
    assert e["meal_default"] == mode
    if mode == "w17":
        assert e["meal_default_source"]["kind"]["dinner"] == E.SOURCE_W17_DAY
        use = e["meal_default_use"]
        assert 0.0 < use["share_with_default_slot"] <= 1.0 and use["agents_without_plan_day"] == 0
