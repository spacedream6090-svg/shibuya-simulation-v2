"""第 3 期 3-5 TM5 の予約の腕(``--body-schedule reserve``)=「全員を毎回見る版」(sweep)と一致すること(受入の条件)。

単体(作り物の体の表・外の書き手を毎刻み混ぜる):
- 内受容(空腹 v1/エネルギー収支 × 二層の段 2 あり/なし)と体感温度(作り物の日の表・移動・表の差し替え)で、腕 reserve の
  値と段の境目の列(鎖のハッシュ・数)が sweep と毎刻み同じ。規則に通した体は少ない。
- 負の対照: 予約を 1 刻み遅らせると食い違う(値と境目の列)。1 刻み早めても同じ(下界の予約)。
- 活動が変わると予約が引き直される(就寝で 0 の疲れ=予約なし → 起きる → 次の体の刻みに予約)。
ランの単位(合成の世界の ``run_day``):
- 3 つの構成で final・全 checkpoint の behavior/full・境目の列が sweep と同じ。
- 再開: 腕 sweep で保存した状態から腕 reserve で再開しても通しと同じ(予約の列は状態から引き直す=軸 2 discardable)。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.engine import body as B
from shibuya.engine.body import BodyModel
from shibuya.engine.body import schedule as BS
from shibuya.engine.run import run_day

from tests.engine.body.body_fixtures import apply_update, copy_registry, fake_registry, stub_energy


@pytest.fixture(autouse=True)
def _arm_back(monkeypatch):
    # 〔3-5 検収 L6〕段の境目の計器は既定で数えない=一致の試験は環境変数を立てて回す
    from shibuya.engine.body.model import GAUGE_ENV

    monkeypatch.setenv(GAUGE_ENV, "1")
    yield
    B.set_arm(B.DEFAULT_ARM)


def _external(rr, rng: np.random.Generator, t: int, energy: bool, ac: bool) -> None:  # noqa: ANN001
    """外の書き手(活動の変化・乗車・食事と軽食・休憩・活動の期限)を同じ乱数で両方の表へ。"""
    n = rr.activity.size
    k = rng.integers(0, n, 12)
    rr.activity[k[:6]] = (rr.activity[k[:6]] + 1 + t % 3) % 8
    rr.transit_state[k[6:8]] = (rr.transit_state[k[6:8]] + 1) % 3
    rr.fatigue[k[8:10]] = np.maximum(rr.fatigue[k[8:10]].astype(np.int16) - 3, 0).astype(np.uint8)
    if ac:
        rr.activity_kind[k[:4]] = (rr.activity_kind[k[:4]] + 1) % 5
        rr.activity_until[k[4:8]] = t + 7 + (t % 11)
    if energy:
        rr.since_meal_kcal[k[10:11]] = 0.0
        rr.since_meal_kcal[k[11:12]] = np.maximum(rr.since_meal_kcal[k[11:12]] - np.float32(200.0), np.float32(0.0))
        from shibuya.engine.energy import EnergyModel as EM
        rr.hunger[k[10:12]] = EM.hunger_copy(EM.stage_of(rr.since_meal_kcal[k[10:12]], rr.eer_kcal[k[10:12]]))
    else:
        rr.hunger[k[10:12]] = np.maximum(rr.hunger[k[10:12]].astype(np.int16) - 4, 0).astype(np.uint8)


def _twin_intero(energy: bool, ac: bool, seed: int, steps: int = 400, n: int = 500):
    rng = np.random.default_rng(seed)
    a = fake_registry(n, rng, energy=energy, activity_columns=ac)
    b = copy_registry(a)
    sw, rs = BodyModel(n, arm="sweep"), BodyModel(n, arm="reserve")
    en = stub_energy() if energy else None
    ext = np.random.default_rng(seed + 100)
    bad = []
    for t in range(steps):
        apply_update(a, sw.step("interoception", a, t, energy=en, activity_columns=ac))
        apply_update(b, rs.step("interoception", b, t, energy=en, activity_columns=ac))
        for f in ("hunger", "fatigue") + (("since_meal_kcal", "energy_balance") if energy else ()):
            if not np.array_equal(getattr(a, f), getattr(b, f)):
                bad.append((t, f))
        st = ext.bit_generator.state
        _external(a, ext, t, energy, ac)
        ext.bit_generator.state = st
        _external(b, ext, t, energy, ac)
    return sw, rs, bad


@pytest.mark.parametrize("energy", [False, True], ids=["v1", "energy"])
@pytest.mark.parametrize("ac", [False, True], ids=["no_activity", "activity"])
@pytest.mark.parametrize("seed", [1, 2])
def test_reserve_equals_sweep_with_outside_writers(energy, ac, seed):
    sw, rs, bad = _twin_intero(energy, ac, seed)
    assert bad == []
    ms, mr = sw.meter_view, rs.meter_view
    assert ms["boundary_digest"] == mr["boundary_digest"] and dict(ms["boundaries"]) == dict(mr["boundaries"])
    assert ms["boundaries"]["fatigue"] > 0 and ms["boundaries"]["hunger"] > 0
    assert mr["agent_evals"] < ms["agent_evals"]  # 規則に通した体は少ない(予約の来た体と入力の変わった体だけ)
    assert mr["reservations"] > 0 and mr["replans"] > 0


@pytest.mark.parametrize("shift,same", [(1, False), (-1, True)], ids=["late_differs", "early_same"])
def test_negative_control_shifting_the_reservation(monkeypatch, shift, same):
    """負の対照: 予約の式を 1 刻み遅らせると値と境目の列が食い違う。早めても同じ(下界の予約=空振りして引き直す)。"""
    real = BS.next_intero_steps

    def shifted(now, **kw):  # noqa: ANN001, ANN003, ANN202
        at = real(now, **kw)
        fin = at != BS.NEVER
        out = at.copy()
        out[fin] = np.maximum(at[fin] + shift, int(now) + 1)
        return out

    monkeypatch.setattr(BS, "next_intero_steps", shifted)
    for energy in (False, True):
        sw, rs, bad = _twin_intero(energy, True, 3, steps=200)
        same_digest = sw.meter_view["boundary_digest"] == rs.meter_view["boundary_digest"]
        assert (bad == [] and same_digest) is same, (energy, bad[:3])


def test_activity_change_replans_the_reservation():
    """就寝で疲れ 0・空腹がいちばん上の段の体は予約なし → 起きると次の体の刻みに予約(活動の変更で引き直す)。"""
    rng = np.random.default_rng(0)
    r = fake_registry(4, rng, energy=True, activity_columns=False)
    r.activity[:] = 4  # 就寝
    r.fatigue[:] = 0
    r.transit_state[:] = 0
    r.since_meal_kcal[:] = 2.0 * r.eer_kcal  # 比 6 ≥ 1.5=とても空腹(次の境目が無い)
    from shibuya.engine.energy import EnergyModel as EM
    r.hunger[:] = EM.hunger_copy(EM.stage_of(r.since_meal_kcal, r.eer_kcal))
    bm = BodyModel(4, arm="reserve")
    en = stub_energy()
    apply_update(r, bm.step("interoception", r, 0, energy=en))
    assert bm.reserved_steps()[0] == -1  # 就寝で 0 の疲れは体の刻みで変わらない・空腹は上の段=予約なし
    before = bm.meter_view["replans"]
    for t in (1, 2):
        apply_update(r, bm.step("interoception", r, t, energy=en))
    assert bm.meter_view["replans"] == before  # 入力が変わらなければ引き直さない
    r.activity[0] = 0  # 起きる(活動の変更)
    apply_update(r, bm.step("interoception", r, 3, energy=en))
    assert bm.meter_view["replans"] == before + 1
    assert bm.reserved_steps()[0] == 30  # 起きて 0 の疲れは次の体の刻み(30)に +1


# ================================================================= 体感温度(作り物の日の表)
def _felt_twin(shift: int = 0, monkeypatch=None, frames: int = 288, n: int = 400, n_cells: int = 12):  # noqa: ANN001
    rng = np.random.default_rng(7)
    tables = []
    for _ in range(2):  # 表は 2 枚(日の頭・天気の差し替え)
        t = rng.integers(2, 11, (frames, n_cells + 1)).astype(np.uint8)
        hold = rng.random((frames, n_cells + 1)) < 0.9  # 値はほとんどの窓で前の窓のまま
        for f in range(1, frames):
            t[f] = np.where(hold[f], t[f - 1], t[f])
        tables.append(t)
    if shift:
        real = BS.next_felt_frames

        def shifted(frame, cols, nxt):  # noqa: ANN001, ANN202
            nf = real(frame, cols, nxt)
            fin = nf != BS.NEVER
            out = nf.copy()
            out[fin] = np.maximum(nf[fin] + shift, int(frame) + 1)
            return out

        monkeypatch.setattr(BS, "next_felt_frames", shifted)
    from types import SimpleNamespace

    cell = rng.integers(-1, n_cells, n).astype(np.int32)
    a = SimpleNamespace(cell=cell.copy(), thermal=np.full(n, 5, dtype=np.uint8))
    b = SimpleNamespace(cell=cell.copy(), thermal=np.full(n, 5, dtype=np.uint8))
    sw, rs = BodyModel(n, arm="sweep"), BodyModel(n, arm="reserve")
    bad = []
    for serial in range(2 * frames):
        table = tables[serial // frames] if serial < frames + 100 else tables[0]  # 2 日目の途中で表を差し替える
        frame = serial % frames
        for rr, bm in ((a, sw), (b, rs)):
            ids, vals = bm.step("felt", rr, serial * 5, cells=table[frame], frame=frame, serial=serial,
                                table_fn=lambda tb=table: tb)
            if ids is None:
                rr.thermal[:] = vals
            else:
                rr.thermal[ids] = vals
        if not np.array_equal(a.thermal, b.thermal):
            bad.append(serial)
        mv = rng.integers(0, n, 9)
        dest = rng.integers(-1, n_cells, 9).astype(np.int32)
        a.cell[mv] = dest
        b.cell[mv] = dest
    return sw, rs, bad


def test_felt_reserve_equals_sweep():
    sw, rs, bad = _felt_twin()
    assert bad == []
    assert sw.meter_view["boundary_digest"] == rs.meter_view["boundary_digest"]
    assert sw.meter_view["boundaries"]["thermal"] > 0
    assert rs.meter_view["felt_evals"] < sw.meter_view["felt_evals"] and rs.meter_view["felt_tables"] == 3


@pytest.mark.parametrize("shift,same", [(1, False), (-1, True)], ids=["late_differs", "early_same"])
def test_felt_negative_control(monkeypatch, shift, same):
    sw, rs, bad = _felt_twin(shift, monkeypatch)
    assert (bad == [] and sw.meter_view["boundary_digest"] == rs.meter_view["boundary_digest"]) is same


def test_felt_guard_refuses_a_table_that_disagrees_with_the_window():
    """守り: その日の表がいまの窓の値と違えば止める(予約の前提が崩れた)。"""
    from types import SimpleNamespace

    bm = BodyModel(3, arm="reserve")
    r = SimpleNamespace(cell=np.array([0, 1, -1], dtype=np.int32), thermal=np.zeros(3, dtype=np.uint8))
    table = np.full((288, 3), 4, dtype=np.uint8)
    with pytest.raises(RuntimeError, match="日の表"):
        bm.step("felt", r, 0, cells=np.array([4, 5, 4], dtype=np.uint8), frame=0, serial=0, table_fn=lambda: table)


# ================================================================= ランの単位(合成の世界)
KW = dict(n_agents=150, seed=1, n_cells=9, ticks=1440, budget=150.0, sleep_suppression=False, checkpoint_every=60)
CONFIGS = {
    "v3_energy_activity_mem_rel": dict(vocab_version="v3", hunger_model="energy", activity=True, memory="on",
                                       relations="on"),
    "v1": dict(vocab_version="v1"),
    "v3_v1hunger_activity": dict(vocab_version="v3", activity=True),
}


def _run(arm: str, **kw):  # noqa: ANN003, ANN202
    B.set_arm(arm)
    try:
        return run_day(**kw)
    finally:
        B.set_arm(B.DEFAULT_ARM)


def _sig(res):  # noqa: ANN001, ANN202
    m = res.run_manifest_fields()["body"]
    return (res.final_hash, [(c.tick, c.behavior_hash, c.full_hash) for c in res.checkpoints], int(res.llm_calls),
            m["boundary_digest"], dict(m["boundaries"]))


@pytest.mark.parametrize("name", sorted(CONFIGS))
def test_run_day_reserve_equals_sweep(name):
    kw = dict(KW, **CONFIGS[name])
    a, b = _run("sweep", **kw), _run("reserve", **kw)
    assert _sig(a) == _sig(b)
    ma, mb = a.run_manifest_fields()["body"], b.run_manifest_fields()["body"]
    assert (ma["arm"], mb["arm"]) == ("sweep", "reserve")
    assert mb["agent_evals"] < ma["agent_evals"] and mb["reservations"] > 0


def test_resume_with_the_reserve_arm_equals_the_straight_run(tmp_path):
    """腕 sweep で日の途中と日の境目に保存した状態から腕 reserve で再開=通し(sweep)と同じ(予約の列は状態から引き直す)。"""
    kw = dict(KW, sim_days=2, **CONFIGS["v3_energy_activity_mem_rel"])
    straight = _run("sweep", **kw)
    for stop in (750, 1440):
        a = _run("sweep", state_out=tmp_path / f"s{stop}", stop_at_tick=stop, **kw)
        f = a.resume["state_files"][-1]
        b = _run("reserve", resume_from=tmp_path / f"s{stop}" / f["file"], **kw)
        assert b.final_hash == straight.final_hash, stop
        want = [(c.tick, c.behavior_hash, c.full_hash) for c in straight.checkpoints if c.tick >= stop]
        got = [(c.tick, c.behavior_hash, c.full_hash) for c in b.checkpoints if c.tick >= stop]
        assert got == want, stop
        assert b.run_manifest_fields()["body"]["arm"] == "reserve"
