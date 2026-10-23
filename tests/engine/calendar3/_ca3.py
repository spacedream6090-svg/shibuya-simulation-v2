"""第 6 期 6-2 カレンダー 3 の試験の共通(腕の切替・合成の雇い主の口の表・グループの一覧・決まった判断の規則)。"""

from __future__ import annotations

import dataclasses
from contextlib import contextmanager
from types import SimpleNamespace
from typing import Any, Iterator

import numpy as np

from shibuya.core.time_consts import NS_PER_SECOND, STEP_SECONDS, STEPS_PER_DAY
from shibuya.engine.calendar2 import arm as A2
from shibuya.engine.calendar3 import arm as A3
from shibuya.engine.calendar3 import port as P3
from shibuya.engine.calendar3 import roster as R3
from shibuya.engine.contact import arm as AC

STEP_NS = STEP_SECONDS * NS_PER_SECOND
TPD = int(STEPS_PER_DAY)
#: 週の最後の日(日曜)=組む機会が開く日。祝日を含む日付(日曜 → 月曜=海の日)。
SUNDAY = "2026-07-26"
HOLIDAY_SUNDAY = "2026-07-19"
#: 合成の世界の小さなラン(記憶・関係なし=C1 の宛先は家族と職場のグループ・活動層なし=日曜 → 月曜の日の頭で計画境界の表が
#: 変わる=活動層のあるランは K9 の張り直しの外で止まる)。
KW = dict(n_agents=80, seed=1, n_cells=9, ticks=TPD, budget=80.0, sleep_suppression=False, vocab_version="v3",
          memory="on", relations="off", store_memory="off", activity="off", checkpoint_every=60,
          start_sim_datetime=SUNDAY)
#: 合成の単位の大きさ(組織=体の番号 // 10)・店長の役割の体(単位 2 の 25 番=最初の担当 20 番より先に選ばれる)。
UNIT = 10
MANAGER = 25
#: 週ごとの働く人(奇数の番号)の W20 の枠の形(月〜金・水だけ長い枠=1 日 8 時間を超える)。
FRAME_A = (540, 1020)
FRAME_B = (600, 1080)
FRAME_LONG = (480, 1080)


def synthetic_table(n: int) -> Any:
    """合成の W20 の週の表(奇数の体=週ごと・偶数の体=毎週固定・月〜金に勤務・場所の種類=建物)。"""
    commit = np.zeros((n, 1, 7), dtype=np.int64)
    rec = np.zeros((n, 1, 7), dtype=np.int64)
    st = np.full((n, 1, 7), -1, dtype=np.int64)
    en = np.full((n, 1, 7), -1, dtype=np.int64)
    cell = np.zeros((n, 1, 7), dtype=np.int64)
    pk = np.ones((n, 1, 7), dtype=np.int64)
    ids = np.arange(n)
    for d in range(5):  # 月〜金
        fr = FRAME_LONG if d == 2 else (FRAME_A if d % 2 == 0 else FRAME_B)
        commit[:, 0, d] = 1
        rec[:, 0, d] = np.where(ids % 2 == 1, R3.RECUR_WEEKLY, R3.RECUR_FIXED)
        st[:, 0, d], en[:, 0, d] = fr
        cell[:, 0, d] = ids % 9
    return SimpleNamespace(cols={"commit": commit, "recurrence": rec, "start_min": st, "end_min": en,
                                 "target_cell": cell, "place_kind": pk})


class FakeRights:
    """合成の権利台帳(雇用の行=体 → 組織 体の番号 // UNIT)。"""

    def __init__(self, n: int) -> None:
        self.n = int(n)

    def pairs(self, kind: str, holder_kind: str, object_kind: str, t_ns: int) -> tuple[np.ndarray, np.ndarray]:
        ids = np.arange(self.n, dtype=np.int64)
        if object_kind == "org":
            return ids, ids // UNIT
        return np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int64)


def synthetic_roster(n: int) -> R3.Roster:
    roles = np.full(int(n), "", dtype=object)
    if int(n) > MANAGER:
        roles[MANAGER] = R3.SCHEDULER_ROLE
    return R3.build_roster(n_agents=int(n), rights=FakeRights(n), table=synthetic_table(int(n)), duty_role=roles)


def roster_fixture(monkeypatch: Any) -> None:
    """合成の世界(母集団が無い=W20 と雇用の行が無い)に、合成の雇い主の口の表とグループの一覧(家族 2 人・職場 10 人)を入れる。"""
    from shibuya.engine.tools import record as TR
    from shibuya.engine.tools.groups import GroupList

    monkeypatch.setattr(R3, "roster_for_run", lambda table, pop, runner, n: synthetic_roster(int(n)))
    real = TR.build_fixture

    def build(pop, n_agents, events):
        fx = real(pop, n_agents, events)
        if fx.groups is not None:
            return fx
        ids = np.arange(int(n_agents))
        return dataclasses.replace(fx, groups=GroupList(household_id=ids // 2, org_id=ids // UNIT))

    monkeypatch.setattr(TR, "build_fixture", build)


@contextmanager
def ca3(*, on: bool = True, trial: bool = True, contact: bool = True, calendar2: bool = True) -> Iterator[None]:
    """腕 arm(と C1・カレンダー 2 の腕・試験用の印)を一時的に選ぶ(組み立てが読む)。"""
    prev = (A3.arm(), A3.trial(), AC.arm(), A2.arm())
    A3.set_arm(A3.ARM_ON if on else A3.ARM_OFF)
    A3.set_trial("on" if trial else "off")
    AC.set_arm(AC.ARM_C1 if contact else AC.ARM_OFF)
    A2.set_arm(A2.ARM_ON if calendar2 else A2.ARM_OFF)
    try:
        yield
    finally:
        A3.set_arm(prev[0])
        A3.set_trial(prev[1])
        AC.set_arm(prev[2])
        A2.set_arm(prev[3])


@contextmanager
def choose(monkeypatch: Any, rule: Any) -> Iterator[None]:
    """カレンダー 3 の仮のモデルの選びを試験の規則に差し替える(``rule(ctx, presented) -> 候補の id``)。"""
    monkeypatch.setattr(P3.Calendar3Port, "_pick", lambda self, ctx, presented: rule(ctx, presented))
    yield


def by_pref(*prefs: str) -> Any:
    """候補の語か id の好みの順で選ぶ規則(どれも無ければ (語・id) の順の最初の候補)。"""
    def rule(ctx: Any, presented: Any) -> str:
        for k in prefs:
            for c in presented:
                if c.kind == k or c.id == k:
                    return c.id
        return sorted(presented, key=lambda c: (c.kind, c.id))[0].id
    return rule
