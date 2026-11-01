"""engine.calendar3.roster — 雇い主の口のつなぎの形(第 6 期 6-2 カレンダー 3・CA1「雇い主がエージェントになるまでのつなぎ」)。

正: 決定 10-12 §4-1 CA1(正規雇用は毎週固定・非正規とシフト勤務は週ごと)・§1-5 の 55 件の ②「人の仕事を働く人のエージェントへ」
(本段は**シフトを組んで知らせる**だけ)・口の約束 1-5(権利台帳の雇用の行=読むだけ)。W20(構築の段 W20cal の週の表)の
``recurrence``(1=毎週固定・2=週ごとの抽選=非正規と交替制)を読む(``engine.calendar_shadow.load_table``)。

ランで 1 回作る(世界の状態でない=権利台帳の雇用の行・母集団の役割の語・W20 の表から作り直せる導出)。〔検収 H1〕作るのは最初の
刻みの頭(``Calendar3Layer.ensure_roster``)=再開では状態を戻して権利台帳を作り直した後(``rebuild_derived``)=通しと同じ台帳・
同じ並びの単位:

- 組織(単位): 働く人の勤め先=権利台帳の雇用の行(体 → 組織。外の雇用主の番号 ``OUTSIDE_EMPLOYER_ORG`` は除く=渋谷の外の雇い主は
  世界のデータのまま)。組織の行の無い体は店の担当の行(体 → 店)の店を単位にする。どちらも無い体・外の雇用主の体は組まない(W20 の
  約束のまま=数える)。
- シフトを組む人(雇い主の口): 単位の担当(雇用の行の体=台帳の行の順)のうち、**役割の語「店長」の体の最初の 1 人・居なければ
  最初の担当**(つなぎ=宣言 ``DOC-ca3-scheduler-pick``)。働く人本人しか居ない単位は本人が組む(同じ宣言)。
- 週ごとの働く人: W20 の表で ``recurrence``=週ごと(2)の勤務の日を持つ体。毎週固定(1)の体は触らない(数えるだけ)。
- 枠(候補の素): その人の W20 の勤務の日の (始業[分]・終業[分]・勤め先のセル・場所の種類) の重ならない組(その人の約束の形)。
  エンジンは枠の数だけを用意する(どの日にどの枠かは雇い主の判断)。

**未リサーチ(expedient)**(つなぎの台帳 ``DOC-ca3-scheduler-pick``・``DOC-ca3-frame-form``): 単位の決め方(組織 → 店の順)・
シフトを組む人の選び方・枠=その人の W20 の約束の形(週の中の重ならない組)。

逐次ループ宣言: 組み立てで 1 回=単位の数と週ごとの働く人の数ぶん(体の数に比例する配列演算は 1 回)。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Final

import numpy as np

__all__ = ["RECUR_FIXED", "RECUR_WEEKLY", "COMMIT_WORK", "UNIT_ORG", "UNIT_STORE", "UNIT_KIND_WORDS", "SCHEDULER_ROLE",
           "Roster", "build_roster", "empty_roster", "roster_for_run", "w20_table_for_run"]

#: W20 の ``recurrence`` の値(``build.sched.w20_calendar_1a`` の RECUR_FIXED・RECUR_WEEKLY の写し=engine は build を import しない)。
RECUR_FIXED: Final[int] = 1
RECUR_WEEKLY: Final[int] = 2
#: W20 の ``commit`` の勤務(1)。
COMMIT_WORK: Final[int] = 1
#: 単位の種類(組織・店)。
UNIT_ORG, UNIT_STORE = 0, 1
UNIT_KIND_WORDS: Final[tuple[str, str]] = ("組織", "店")
#: シフトを組む人に先に選ぶ役割の語(母集団の ``duty_role``)。
SCHEDULER_ROLE: Final[str] = "店長"


@dataclass
class Roster:
    """雇い主の口の表(組み立てで 1 回作る導出・読むだけ)。"""

    #: 単位の種類(``UNIT_ORG``/``UNIT_STORE``)・物の番号(組織か店)・シフトを組む人・選び方の語・担当の数。
    unit_kind: list[int] = field(default_factory=list)
    unit_obj: list[int] = field(default_factory=list)
    scheduler: list[int] = field(default_factory=list)
    sched_by: list[str] = field(default_factory=list)
    members_n: list[int] = field(default_factory=list)
    #: 単位 → 週ごとの働く人(体の番号の昇順)。
    workers: list[list[int]] = field(default_factory=list)
    #: 週ごとの働く人 → 単位。
    unit_of: dict[int, int] = field(default_factory=dict)
    #: 週ごとの働く人 → 枠 ``[[始業[分], 終業[分], セル, 場所の種類], …]``(重ならない組・始業の順)。
    frames: dict[int, list[list[int]]] = field(default_factory=dict)
    #: 週ごとの働く人 → 店の担当の店(営業時間を読む・無ければ載せない)。
    store_of: dict[int, int] = field(default_factory=dict)
    #: 数(計器): 週ごとの働く人(全部)・毎週固定の人・外の雇用主の週ごとの人・勤め先の無い週ごとの人。
    head_counts: dict[str, int] = field(default_factory=dict)

    @property
    def n_units(self) -> int:
        return len(self.unit_kind)

    def units_of(self, agent: int) -> list[int]:
        """体がシフトを組む単位(番号の昇順)。"""
        return [u for u, s in enumerate(self.scheduler) if int(s) == int(agent)]


def empty_roster() -> Roster:
    return Roster(head_counts={"weekly_workers": 0, "fixed_workers": 0, "weekly_outside_employer": 0,
                          "weekly_no_employer": 0, "weekly_scheduled": 0})


def _first_rows(holders: np.ndarray, objects: np.ndarray, n: int) -> np.ndarray:
    """体 → 最初の行の物の番号(−1=無い)。"""
    out = np.full(int(n), -1, dtype=np.int64)
    ok = (holders >= 0) & (holders < int(n))
    h, o = holders[ok], objects[ok]
    if h.size:
        uniq, first = np.unique(h, return_index=True)
        out[uniq] = o[first]
    return out


def build_roster(*, n_agents: int, rights: Any, table: Any, duty_role: Any = None, t_ns: int = 0,
                 outside_org: int | None = None) -> Roster:
    """権利台帳の雇用の行・W20 の表・母集団の役割の語から雇い主の口の表を作る(読むだけ)。

    Args:
        rights: 権利台帳(``engine.rights.ledger.Rights``=``pairs`` だけ読む)。``None`` は単位なし。
        table: W20 の週の表(``engine.calendar_shadow.CalendarTable``=``cols`` の ``commit``・``start_min``・``end_min``・
            ``target_cell``・``place_kind``・``recurrence``)。``None`` は週ごとの働く人なし。
        duty_role: 体 → 役割の語(``Population.duty_role``・``None``=語なし=最初の担当)。
        outside_org: 外の雇用主の組織の番号(``engine.rights.initial.OUTSIDE_EMPLOYER_ORG``)。
    """
    from shibuya.engine.rights.initial import OUTSIDE_EMPLOYER_ORG
    from shibuya.engine.rights.ledger import AGENT, EMPLOY, ORG, STORE

    n = int(n_agents)
    out_org = int(OUTSIDE_EMPLOYER_ORG if outside_org is None else outside_org)
    r = empty_roster()
    if table is None:
        return r
    cols = table.cols
    commit = np.asarray(cols["commit"], dtype=np.int64)[:n]
    rec = np.asarray(cols["recurrence"], dtype=np.int64)[:n]
    work = commit == COMMIT_WORK
    weekly = (work & (rec == RECUR_WEEKLY)).reshape(commit.shape[0], -1).any(axis=1)
    fixed = (work & (rec == RECUR_FIXED)).reshape(commit.shape[0], -1).any(axis=1) & ~weekly
    r.head_counts["weekly_workers"] = int(weekly.sum())
    r.head_counts["fixed_workers"] = int(fixed.sum())
    if rights is None:
        r.head_counts["weekly_no_employer"] = int(weekly.sum())
        return r
    oh, oo = rights.pairs(EMPLOY, AGENT, ORG, int(t_ns))
    sh, so = rights.pairs(EMPLOY, AGENT, STORE, int(t_ns))
    oh, oo, sh, so = (np.asarray(x, dtype=np.int64) for x in (oh, oo, sh, so))
    inside = oo != out_org
    org_of = _first_rows(oh[inside], oo[inside], n)
    outside_of = _first_rows(oh[~inside], oo[~inside], n)
    store_of = _first_rows(sh, so, n)
    roles = None if duty_role is None else np.asarray(duty_role, dtype=object)
    wk = np.flatnonzero(weekly)
    kind_of = np.where(org_of[wk] >= 0, UNIT_ORG, np.where(store_of[wk] >= 0, UNIT_STORE, -1))
    r.head_counts["weekly_outside_employer"] = int(np.count_nonzero((kind_of < 0) & (outside_of[wk] >= 0)))
    r.head_counts["weekly_no_employer"] = int(np.count_nonzero((kind_of < 0) & (outside_of[wk] < 0)))
    unit_key: dict[tuple[int, int], int] = {}
    for a, k in zip(wk.tolist(), kind_of.tolist()):  # 逐次: 週ごとの働く人の数ぶん(組み立てで 1 回)
        if k < 0:
            continue
        obj = int(org_of[a]) if k == UNIT_ORG else int(store_of[a])
        key = (int(k), obj)
        if key not in unit_key:
            hs = oh[inside][oo[inside] == obj] if k == UNIT_ORG else sh[so == obj]
            hs = hs[(hs >= 0) & (hs < n)]
            pick, by = (int(hs[0]) if hs.size else int(a)), "最初の担当"
            if roles is not None and hs.size:
                mgr = [int(h) for h in hs.tolist() if 0 <= int(h) < roles.size and str(roles[int(h)]) == SCHEDULER_ROLE]
                if mgr:
                    pick, by = mgr[0], SCHEDULER_ROLE
            if hs.size <= 1 and by != SCHEDULER_ROLE:  # 担当が働く人本人だけ(ランの体の中で)=本人が組む
                by = "本人"
            unit_key[key] = len(r.unit_kind)
            r.unit_kind.append(int(k))
            r.unit_obj.append(obj)
            r.scheduler.append(pick)
            r.sched_by.append(by)
            r.members_n.append(int(hs.size))
            r.workers.append([])
        u = unit_key[key]
        r.workers[u].append(int(a))
        r.unit_of[int(a)] = u
        if int(store_of[a]) >= 0:
            r.store_of[int(a)] = int(store_of[a])
        r.frames[int(a)] = _frames_of(cols, int(a))
    r.head_counts["weekly_scheduled"] = int(len(r.unit_of))
    return r


def _frames_of(cols: Any, a: int) -> list[list[int]]:
    """その人の W20 の勤務の日の (始業・終業・セル・場所の種類) の重ならない組(始業の順)。"""
    commit = np.asarray(cols["commit"][a], dtype=np.int64).ravel()
    m = commit == COMMIT_WORK
    rows = {(int(s), int(e), int(c), int(p)) for s, e, c, p in zip(
        np.asarray(cols["start_min"][a]).ravel()[m].tolist(), np.asarray(cols["end_min"][a]).ravel()[m].tolist(),
        np.asarray(cols["target_cell"][a]).ravel()[m].tolist(), np.asarray(cols["place_kind"][a]).ravel()[m].tolist())
        if int(s) >= 0 and int(e) > int(s)}
    return [list(x) for x in sorted(rows)]


def w20_table_for_run(world_dir: Any, pop: Any) -> Any:
    """組み立ての口: ランの W20 の週の表(世界の資産=状態でない・母集団の無いラン=合成の世界は ``None``)。

    Raises:
        FileNotFoundError: 母集団のあるランで W20 の週の表が無い(``engine.calendar_shadow.resolve_path`` と同じ置き場)。
    """
    if pop is None:
        return None
    from shibuya.engine import calendar_shadow as _CS

    path = _CS.resolve_path(world_dir)
    if path is None:
        raise FileNotFoundError("腕 --calendar-3 arm には世界資産の置き場(world_dir)か SHIBUYA_CALENDAR_W20 が要る")
    return _CS.load_table(path, np.asarray(pop.source_agent_id, dtype=np.int64))


def roster_for_run(table: Any, pop: Any, runner: Any, n_agents: int) -> Roster:
    """ランの雇い主の口の表(〔検収 H1〕最初の刻みの頭に呼ぶ=再開では状態を戻して権利台帳を作り直した後)。W20 の表が無い
    (合成の世界)ときは空=週ごとの働く人なし。権利台帳は開閉の過程の台帳(``runner.rights``)を読むだけ。"""
    if table is None:
        return empty_roster()
    try:  # 開閉の過程の無いラン(権利台帳の置き場が無い)は単位なし
        rights = runner.rights if runner is not None else None
    except AttributeError:
        rights = None
    return build_roster(n_agents=int(n_agents), rights=rights, table=table,
                        duty_role=None if pop is None else getattr(pop, "duty_role", None))
