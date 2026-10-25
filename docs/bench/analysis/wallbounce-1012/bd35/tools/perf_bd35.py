"""第 3 期 3-5: 体の刻みの時間(P4)を腕 sweep と reserve で測る(作り物の体の表・5,000 / 50,000 / 390,000 体)。

腕は 4 つ: ``pure``=体の層の持ち主を通さない純関数(``engine.body.rules.interoception``・``felt_temperature``=3-5 より前の
``advance_body`` と体感温度の写像と同じ計算=HEAD 相当)・``sweep``=既定(持ち主を通す・〔3-5 検収 L6〕段の境目の計器は
数えない)・``sweep_gauge``=sweep で段の境目の計器を数える(環境変数 ``SHIBUYA_BODY_BOUNDARY_GAUGE=1`` と同じ)・``reserve``=
TM5 の予約(計器は数えない)。

測るもの: ``BodyModel.step("interoception")``(体の刻み=空腹と疲れ・エネルギー収支・二層の段 2 あり)の 1 刻みあたりの時間と、
``BodyModel.step("felt")``(5 分の窓の体感温度・作り物の日の表)の 1 窓あたりの時間。体の表の書き戻し(resolve が書く分)も
含める(``resolve.advance_body`` と同じ書き方=作り物の表へ)。

外の書き手の量(1 刻みに活動が変わる体の割合・移動する体の割合)は、5,000 体・1 日の世界資産のラン(byte-check の
``w6_v3_default`` の腕 reserve)で数えた引き直しの延べ(manifest の ``body.replans``・``felt_moved``)を体数と刻みの数で割った値を
引数で渡す(``--change-rate``・``--move-rate``)。METs の 4 値と消費の式は energy.py と同じ形(錨は読まない=作り物)。

    PYTHONPATH=src python $D/tools/perf_bd35.py --sizes 5000,50000,390000 --steps 1440 --out $D/perf_bd35.json

逐次ループ宣言: 刻みの数ぶん(道具の計測)。絶対パスは JSON に書かない。
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from shibuya.agents.state import Activity, ActivityKind
from shibuya.core.time_consts import MINUTES_PER_DAY
from shibuya.engine.body import BodyModel
from shibuya.engine.energy import AVG_METS, EnergyModel


class _Model:
    stage_of = staticmethod(EnergyModel.stage_of)
    hunger_copy = staticmethod(EnergyModel.hunger_copy)

    def mets_of(self, activity, transit_state, activity_kind):  # noqa: ANN001, ANN201
        act = np.asarray(activity)
        mets = np.full(act.shape, np.float32(1.3), dtype=np.float32)
        moving = act == int(Activity.MOVING)
        wander = moving & (np.asarray(activity_kind) == int(ActivityKind.WANDER))
        mets[moving] = np.float32(3.5)
        mets[wander] = np.float32(3.0)
        mets[act == int(Activity.SLEEPING)] = np.float32(1.0)
        mets[np.asarray(transit_state) == 2] = AVG_METS
        return mets

    def expenditure(self, eer, mets, bmr=None):  # noqa: ANN001, ANN201
        return (np.asarray(eer, dtype=np.float32) * np.float32(1.0 / MINUTES_PER_DAY / AVG_METS) * mets).astype(np.float32)


def _registry(n: int, rng: np.random.Generator) -> SimpleNamespace:
    act = rng.choice(np.array([0, 1, 2, 4, 5, 6, 7], dtype=np.int8), n, p=[0.25, 0.08, 0.04, 0.4, 0.13, 0.05, 0.05])
    eer = rng.uniform(1200.0, 3000.0, n).astype(np.float32)
    since = rng.uniform(0.0, 1500.0, n).astype(np.float32)
    return SimpleNamespace(
        activity=act, fatigue=rng.integers(0, 11, n).astype(np.uint8),
        hunger=EnergyModel.hunger_copy(EnergyModel.stage_of(since, eer)),
        thermal=np.full(n, 5, dtype=np.uint8), transit_state=rng.choice(np.array([0, 2], dtype=np.int8), n, p=[0.8, 0.2]),
        cell=rng.integers(-1, 3000, n).astype(np.int32),
        activity_kind=rng.integers(0, 5, n).astype(np.int8), activity_until=rng.integers(-1, 1440, n).astype(np.int32),
        eer_kcal=eer, since_meal_kcal=since, energy_balance=np.zeros(n, dtype=np.float32))


def _write(r: SimpleNamespace, upd) -> None:  # noqa: ANN001
    if upd is None:
        return
    if upd.fatigue is not None:
        if upd.fatigue_ids is None:
            r.fatigue[:] = upd.fatigue
        else:
            r.fatigue[upd.fatigue_ids] = upd.fatigue
    if upd.hunger is not None:
        if upd.hunger_ids is None:
            r.hunger[:] = upd.hunger
        else:
            r.hunger[upd.hunger_ids] = upd.hunger
    if upd.spent is not None:
        r.since_meal_kcal[:] = upd.since_meal
        r.energy_balance -= upd.spent


def _measure(n: int, steps: int, arm: str, change_rate: float, move_rate: float, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    r = _registry(n, rng)
    ext = np.random.default_rng(seed + 1)
    from shibuya.engine.body import rules as BR

    bm = BodyModel(n, arm="reserve" if arm == "reserve" else "sweep", gauge=(arm == "sweep_gauge"))
    energy = SimpleNamespace(model=_Model(), bmr=None)
    n_cells = 3000
    table = np.full((288, n_cells + 1), 6, dtype=np.uint8)
    hours = np.arange(288) // 12
    table[:] = np.where((hours >= 10) & (hours < 16), 8, 6)[:, None].astype(np.uint8)
    shade = ext.random(n_cells + 1) < 0.3
    table[:, :n_cells] = np.where(shade[None, :n_cells], table[:, :n_cells] - 1, table[:, :n_cells])
    t_in, t_felt, n_felt = [], [], 0
    k_change = max(1, int(round(change_rate * n)))
    k_move = max(1, int(round(move_rate * n)))
    for t in range(steps):
        t0 = time.perf_counter()
        if arm == "pure":
            _write(r, BR.interoception(r, t, energy=energy, activity_columns=True))
        else:
            _write(r, bm.step("interoception", r, t, energy=energy, activity_columns=True))
        t_in.append(time.perf_counter() - t0)
        if t % 5 == 0:
            frame = (t // 5) % 288
            t0 = time.perf_counter()
            if arm == "pure":
                ids, vals = None, table[frame][BR.felt_columns(r.cell, n_cells)]
            else:
                ids, vals = bm.step("felt", r, t, cells=table[frame], frame=frame, serial=t // 5,
                                    table_fn=lambda: table)
            if ids is None:
                r.thermal[:] = vals
            else:
                r.thermal[ids] = vals
            t_felt.append(time.perf_counter() - t0)
            n_felt += 1
        # 外の書き手(活動の変化・移動)
        k = ext.integers(0, n, k_change)
        r.activity[k] = ext.choice(np.array([0, 1, 4, 5, 6], dtype=np.int8), k.size)
        r.activity_kind[k] = ext.integers(0, 5, k.size).astype(np.int8)
        m = ext.integers(0, n, k_move)
        r.cell[m] = ext.integers(-1, n_cells, m.size).astype(np.int32)
    a_in, a_f = np.asarray(t_in[10:]), np.asarray(t_felt[2:])
    mv = bm.meter_view
    return {"n": n, "arm": arm, "steps": steps, "interoception_us_mean": round(float(a_in.mean()) * 1e6, 1),
            "interoception_us_p50": round(float(np.median(a_in)) * 1e6, 1),
            "interoception_us_p99": round(float(np.percentile(a_in, 99)) * 1e6, 1),
            "felt_us_mean_per_window": round(float(a_f.mean()) * 1e6, 1),
            "per_step_us_total_mean": round((float(a_in.sum()) + float(np.asarray(t_felt).sum())) / steps * 1e6, 1),
            "agent_evals_per_step": None if arm == "pure" else round(mv["agent_evals"] / mv["steps"], 1),
            "felt_evals_per_window": None if arm == "pure" else round(mv["felt_evals"] / max(1, mv["felt_frames"]), 1),
            "reservations": int(mv["reservations"]), "replans": int(mv["replans"])}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", default="5000,50000,390000")
    ap.add_argument("--steps", type=int, default=1440)
    ap.add_argument("--change-rate", type=float, default=0.004)
    ap.add_argument("--move-rate", type=float, default=0.01)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    rows = []
    for n in [int(x) for x in a.sizes.split(",") if x]:
        for arm in ("pure", "sweep", "sweep_gauge", "reserve"):
            row = _measure(n, a.steps, arm, a.change_rate, a.move_rate, a.seed)
            rows.append(row)
            print(json.dumps(row), flush=True)
    doc = {"machine": {"python": platform.python_version(), "numpy": np.__version__, "machine": platform.machine()},
           "steps": a.steps, "change_rate": a.change_rate, "move_rate": a.move_rate, "rows": rows,
           "note": "作り物の体の表(活動の割合は固定の作り物・外の書き手は 1 刻みに change_rate × 体数が活動を変え、move_rate × "
                   "体数がセルを移る)。体の刻みは毎刻み・体感温度は 5 刻みに 1 回。resolve の書き戻し(作り物の表へ)を含む"}
    Path(a.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
