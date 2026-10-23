"""engine.experiment.apply — 申込書の改変を世界に入れる口 ``apply``(第 3 期 3-3・決定 10-12 §1-1 CP6・§4-5 CP5・CP12)。

**口は 1 つ**: ``apply(form, world, t)``。実験が世界に入れるのは「決定」だけ(CLAUDE.md §3・§1-1)。準備・告知・実行は世界の中の
人が行う。この口は決定を世界の「表」に入れ(営業時間の表の行・天気の再生日・暦の祝日)、決定を出来事ログに 1 行書く(原因は
実験の条件=``engine.experiment.gate.admit`` を通す=CP12)。表を実行するのは世界の中の過程と人(営業時間の表は担当の従業者が
開け閉めする=``engine.processes.opening``)。エンジンが代わりに実行する仕組みを足さない(§1-1)。

- 呼び手は系 ``experiment``(``engine.experiment.layer.sys_experiment``・刻みの頭の最初の系)だけ。毎刻み呼ばれ、決定が始まる刻み
  (``form.start`` 以後の最初の刻み)に 1 回だけ決定を記録し、効いている間は日が替わるごとに表へ当て直す(日の頭で過程が表を
  張り直すため=``relay_day``)。終わり(``form.end``)の刻みで表を元(W7 の行・その日の実際の天気)に戻す。
- **効かせていない改変は記録して続ける**(計器 ``unapplied``・行に理由): 対象が無い(番号が世界に無い・種別が無い・W7 が無い・
  W13 が無い)・期間の外(分岐の元の状態より前に始まる・当日以前の暦)・宣言して未実装(L2〜L4)。止めない。
- 告知(CP6・本段): 申込書の ``notice`` の宛先ごとに「届いた情報」の出来事を 1 行(``via``=道具・``received_ns``=届いた時刻)。
  宛先 ``staff`` は対象の店の担当の従業者(権利台帳の雇用の行=``OpeningProcess.staff_of_poi``)。住人の意識は書き換えない
  (届いた情報を本人が受け取る段は CT の道具の段=本段は出来事の行まで)。

本段で実装した改変(``form.DECISIONS`` の ``implemented``):

| 水準 | 決定 | 世界の表 | 実行する人 |
|---|---|---|---|
| L0 | ``weather_date`` | 天気の再生日(``EnvironmentProcess.set_replay_date``) | 自然(人はいない) |
| L0 | ``holiday`` | 暦の祝日の表(``SimCalendar.set_holiday``・その日の頭より前に入れる) | 社会の決まり |
| L1 | ``opening_hours`` | 対象の店の営業時間の表(``OpeningProcess.set_plan_rows``) | 担当の従業者(居なければ今の過程のつなぎ) |
| L1 | ``closure`` | 対象の店の営業時間の表を空に | 同上 |
| L1 | ``event`` | (表は変えない=催しの決定と告知の行だけ) | 世界の中の人(本段では告知まで) |

未リサーチ(expedient): 当て直しの単位(日が替わるごと・日の頭の後の最初の刻み)・祝日は翌日以後だけ(当日の表は張り直し済み)・
終わりに戻す形(W7 の行の作り直し・その日の実際の天気の引き直し)・決定の行の ``where``(最初の対象の店)・``who``(持ち主の名
``experiment``)・``origin``(``境界の外``=外での決定・``自然``=天気)。

逐次ループ宣言: ``apply`` は決定の数ぶん(申込書の数個)× 刻み。告知は宛先の数ぶん(1 回だけ)。
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Callable, Final, Mapping

import numpy as np

from shibuya.core.time_consts import MINUTES_PER_DAY, NS_PER_SECOND
from shibuya.engine.experiment import gate as _GATE
from shibuya.engine.experiment.form import DECISIONS, NOTICE_STAFF, ExperimentForm

__all__ = [
    "ApplyRecord", "WorldHandle", "apply", "WHAT_DECISION", "WHAT_NOTICE", "WHO", "ORIGIN_OUTSIDE", "ORIGIN_NATURE",
    "cond_id_of", "hours_mask", "REASONS", "targets_of",
]

#: 出来事の語(1-3 の語彙表の ``実験`` の族)。
WHAT_DECISION: Final[str] = "実験:改変"
WHAT_NOTICE: Final[str] = "実験:届いた情報"
#: 出来事の ``who``(持ち主の名)・``origin``(範囲の外からの印)。
WHO: Final[str] = "experiment"
ORIGIN_OUTSIDE: Final[str] = "境界の外"
ORIGIN_NATURE: Final[str] = "自然"

#: 効かせていない理由の語(計器の行の ``reason``)。読み取り専用(検収 L6)。
REASONS: Final[Mapping[str, str]] = MappingProxyType({
    "no_target": "対象が無い",
    "no_category": "対象の種別が世界に無い",
    "no_w7": "営業時間の表(W7)が無い世界",
    "no_w13": "気象の資産(W13)が無い世界",
    "no_replay_date": "再生日が W13 に無い",
    "before_begin": "期間の外(分岐の元の状態より前に始まる)",
    "after_end": "期間の外(終わりの後)",
    "past_day": "期間の外(当日以前の暦=その日の表は日の頭で張り直し済み)",
    "holiday_table": "祝日の表が書けない",
    "not_implemented": "宣言して未実装",
    "no_recipient": "告知の宛先が無い",
})


@dataclass
class ApplyRecord:
    """申込書の改変の控え(持ち主 ``experiment`` の ``handle.rec``・状態台帳の行 ``X``=軸 1 diag・軸 2 discardable)。

    読み手は manifest の ``experiment`` と分岐の報告と試験だけ(挙動は読まない=表への当て方は申込書と刻みから決まる)。
    """

    applied: list[dict[str, Any]] = field(default_factory=list)
    unapplied: list[dict[str, Any]] = field(default_factory=list)
    tallies: dict[str, int] = field(default_factory=lambda: {
        "decided": 0, "unapplied": 0, "reapplied": 0, "restored": 0, "notices": 0, "notice_unreached": 0,
        "events": 0})
    #: 決定を記録した(か効かせなかった)決定の番号・効いている決定・決定 → 最後に表へ当てた日・終わりに戻した決定。
    decided: set[int] = field(default_factory=set)
    active: set[int] = field(default_factory=set)
    day_done: dict[int, int] = field(default_factory=dict)
    ended: set[int] = field(default_factory=set)
    notice_sent: bool = False


@dataclass(frozen=True)
class WorldHandle:
    """口 ``apply`` が触る世界の物(組み立てが 1 回だけ作る・物はそのまま指す)。

    - ``world``: 世界の SoA(``World``)。``runner``: 世界過程(``opening``・``environment`` を読む・無ければ ``None``)。
    - ``calendar``: 暦の口(``SimCalendar``・祝日の表はランごとに読み直した物)。``events``: 出来事の記録。
    - ``step_seconds``・``steps_per_day``: 刻みの幅と 1 日の刻みの数。``n_agents``: 体の数(告知の宛先の検査)。
    - ``begin_ns``: このランの最初の刻みの時刻(再開のランは再開の時刻)。``inherited``: 親の状態のファイルが同じ申込書の
      ラン(再開)=始まりが ``begin_ns`` より前の決定は「決めた後」として表へ当てるだけ(行は親のランが書いた)。
    - ``rec``: 控え(``ApplyRecord``)。
    """

    world: Any
    runner: Any
    calendar: Any
    events: Any
    step_seconds: int
    steps_per_day: int
    n_agents: int
    begin_ns: int
    inherited: bool
    rec: ApplyRecord


def cond_id_of(form: ExperimentForm, i: int | str) -> str:
    """実験の条件の名(``<申込書の指紋の先頭 16 字>:<決定の番号か notice>``)。"""
    return f"{form.sha256()[:16]}:{i}"


def hours_mask(hours: Any) -> np.ndarray:
    """営業時間の区間の列 → 1 日の分の真偽の列(閉じる分が 1 日を超える区間は同じ日の頭へ回す=W7 の畳み方と同じ)。"""
    m = np.zeros(MINUTES_PER_DAY, dtype=bool)
    for s, e in hours:
        s, e = int(s), int(e)
        if e <= MINUTES_PER_DAY:
            m[s:e] = True
        else:
            m[s:] = True
            m[: min(MINUTES_PER_DAY, e - MINUTES_PER_DAY)] = True
    return m


# ================================================================ 対象
def _opening(world: WorldHandle) -> Any:
    return getattr(world.runner, "opening", None) if world.runner is not None else None


def _environment(world: WorldHandle) -> Any:
    return getattr(world.runner, "environment", None) if world.runner is not None else None


def targets_of(form: ExperimentForm, world: WorldHandle) -> np.ndarray:
    """対象の店の番号(昇順・空もある)。読むだけ(分岐の報告の実行の内訳が使う)。"""
    return _targets(form, world)[0]


def _targets(form: ExperimentForm, world: WorldHandle) -> tuple[np.ndarray, str]:
    """対象の店の番号(昇順・重なりなし)と、空のときの理由の鍵。"""
    n_poi = int(world.world.n_poi)
    ids = [int(j) for j in form.subject["ids"] if 0 <= int(j) < n_poi]
    cat = form.subject["category"]
    if cat is not None:
        op = _opening(world)
        names = tuple(getattr(getattr(op, "assets", None), "poi_cat_names", ()) or ())
        codes = getattr(getattr(op, "assets", None), "poi_cat_code", None)
        if cat not in names or codes is None:
            return np.zeros(0, dtype=np.int64), "no_category"
        ids += np.flatnonzero(np.asarray(codes) == names.index(cat)).tolist()
    out = np.unique(np.asarray(ids, dtype=np.int64))
    return out, ("" if out.size else "no_target")


# ================================================================ 決定ごとの実装(表に当てる・戻す)
#: 戻り値 ``(効いたか, 効かなかった理由の鍵, 対象の店)``。
_Result = tuple[bool, str, np.ndarray]
_NONE = np.zeros(0, dtype=np.int64)


def _hours(form: ExperimentForm, dec: Any, world: WorldHandle, day: int) -> _Result:
    op = _opening(world)
    if op is None or not bool(getattr(op, "active", False)):
        return False, "no_w7", _NONE
    tg, why = _targets(form, world)
    if why:
        return False, why, _NONE
    mask = hours_mask(dec["hours"]) if dec["decision"] == "opening_hours" else np.zeros(MINUTES_PER_DAY, dtype=bool)
    op.set_plan_rows(tg, mask)
    return True, "", tg


def _hours_restore(form: ExperimentForm, dec: Any, world: WorldHandle, day: int) -> None:
    op = _opening(world)
    tg, why = _targets(form, world)
    if op is not None and not why:
        op.restore_plan_rows(tg)


def _event(form: ExperimentForm, dec: Any, world: WorldHandle, day: int) -> _Result:
    tg, why = _targets(form, world)
    if why:
        return False, why, _NONE
    return True, "", tg


def _weather(form: ExperimentForm, dec: Any, world: WorldHandle, day: int) -> _Result:
    env = _environment(world)
    assets = getattr(env, "assets", None)
    if env is None or assets is None or not bool(getattr(assets, "has_weather", False)):
        return False, "no_w13", _NONE
    if not env.set_replay_date(int(day), str(dec["replay_date"]), how="experiment"):
        return False, "no_replay_date", _NONE
    return True, "", _NONE


def _weather_restore(form: ExperimentForm, dec: Any, world: WorldHandle, day: int) -> None:
    env = _environment(world)
    if env is not None:
        env.pick_day(int(day))


def _holiday(form: ExperimentForm, dec: Any, world: WorldHandle, day: int) -> _Result:
    cal = world.calendar
    d = _dt.date.fromisoformat(str(dec["date"]))
    target_day = int(cal.day_index_of(d))
    inherited = world.inherited and int(form.start) < int(world.begin_ns)  # 再開: 親のランが決めた暦を読み直した表に戻す
    if target_day <= int(day) and not inherited:
        return False, "past_day", _NONE
    if not cal.set_holiday(d, on=bool(dec["on"]), name=str(dec["name"])):  # 暦の書き口(検収 L5)
        return False, "holiday_table", _NONE
    return True, "", _NONE


def _nothing(form: ExperimentForm, dec: Any, world: WorldHandle, day: int) -> None:
    return None


#: 決定の名 → (表に当てる・終わりに戻す・日が替わるごとに当て直すか・``origin``)。
_IMPL: Final[Mapping[str, tuple[Callable[..., _Result], Callable[..., None], bool, str]]] = MappingProxyType({
    "weather_date": (_weather, _weather_restore, True, ORIGIN_NATURE),
    "holiday": (_holiday, _nothing, False, ORIGIN_OUTSIDE),
    "opening_hours": (_hours, _hours_restore, True, ORIGIN_OUTSIDE),
    "closure": (_hours, _hours_restore, True, ORIGIN_OUTSIDE),
    "event": (_event, _nothing, False, ORIGIN_OUTSIDE),
})


# ================================================================ 口
def _row(i: int, dec: Any, t: int, step: int, **kw: Any) -> dict[str, Any]:
    return {"i": int(i), "decision": str(dec["decision"]), "level": DECISIONS[dec["decision"]].level,
            "t_ns": int(t), "step": int(step), **kw}


def _unapplied(rec: ApplyRecord, i: int, dec: Any, t: int, step: int, key: str) -> None:
    lv = DECISIONS[dec["decision"]].level
    reason = REASONS[key] + (f"({lv})" if key == "not_implemented" else "")
    rec.unapplied.append(_row(i, dec, t, step, reason=reason, reason_key=key))
    rec.tallies["unapplied"] += 1


def _admit(world: WorldHandle, cond: str, **kw: Any) -> Any:
    log = world.events
    if log is None:
        return None
    eid = _GATE.admit(log, cond, **kw)
    if eid is not None:
        world.rec.tallies["events"] += 1
    return eid


def _send_notice(form: ExperimentForm, world: WorldHandle, t: int, step: int) -> None:
    """告知の宛先ごとに「届いた情報」を 1 行(宛先が無ければ計器 ``notice_unreached``・効かせていない行)。"""
    rec = world.rec
    nt = form.notice
    who: list[int] = []
    for x in nt["to"]:
        if x == NOTICE_STAFF:
            op = _opening(world)
            staff = getattr(op, "staff_of_poi", None)
            tg, why = _targets(form, world)
            if staff is not None and not why:
                s = np.asarray(staff)[tg]
                who += [int(a) for a in s[s >= 0].tolist()]
        elif 0 <= int(x) < int(world.n_agents):
            who.append(int(x))
    who = sorted(set(who))
    cond = cond_id_of(form, "notice")
    if not who:
        rec.tallies["notice_unreached"] += 1
        rec.unapplied.append({"i": -1, "decision": "notice", "level": form.level, "t_ns": int(t), "step": int(step),
                              "reason": REASONS["no_recipient"], "reason_key": "no_recipient"})
        return
    log = world.events
    now = int(log.now_ns) if log is not None else int(t)
    for a in who:  # 逐次ループ宣言: 告知の宛先の数ぶん(1 回だけ)
        _admit(world, cond, what=WHAT_NOTICE, who=WHO, whom=a, origin=ORIGIN_OUTSIDE, via=str(nt["via"]),
               received_ns=now)
    rec.tallies["notices"] += len(who)


def apply(form: ExperimentForm, world: WorldHandle, t: int, *, prime: bool = False) -> int:
    """申込書 ``form`` の改変を時刻 ``t``(ナノ秒・刻みの頭)の世界に入れる(**唯一の口**)。表を変えた回数を返す。

    同じ刻みに 2 回呼んでも 2 回目は何もしない(決定の記録は 1 回・当て直しは日に 1 回)。

    ``prime=True``: 組み立ての中(刻みのループの前)で 1 回だけ=親のランから引き継いだ決定(再開)のうち、日の頭より前に要る
    表(暦の祝日)だけを当てる(出来事は書かない・日が替わるごとに当て直す表はループの最初の刻みで当てる)。
    """
    rec = world.rec
    t = int(t)
    if prime:
        if not world.inherited or int(form.start) >= int(world.begin_ns):
            return 0
        step = t // (int(world.step_seconds) * NS_PER_SECOND)
        day = step // int(world.steps_per_day)
        n = 0
        for i, dec in enumerate(form.content):  # 逐次ループ宣言: 決定の数ぶん(1 回だけ)
            name = str(dec["decision"])
            if not DECISIONS[name].implemented or _IMPL[name][2]:
                continue
            ok, _why, _tg = _IMPL[name][0](form, dec, world, day)
            n += int(ok)
        return n
    if t < int(form.start):
        return 0
    step_ns = int(world.step_seconds) * NS_PER_SECOND
    step = t // step_ns
    day = step // int(world.steps_per_day)
    ended = form.end is not None and t >= int(form.end)
    n = 0
    for i, dec in enumerate(form.content):  # 逐次ループ宣言: 決定の数ぶん
        name = str(dec["decision"])
        spec = DECISIONS[name]
        if i not in rec.decided:
            rec.decided.add(i)
            rec.tallies["decided"] += 1
            before = int(form.start) < int(world.begin_ns)
            if ended:
                if not (before and world.inherited):  # 親のランが当てて戻した決定(再開)は記録しない
                    _unapplied(rec, i, dec, t, step, "after_end")
                continue
            if not spec.implemented:
                _unapplied(rec, i, dec, t, step, "not_implemented")
                continue
            if before and not world.inherited:
                _unapplied(rec, i, dec, t, step, "before_begin")
                continue
            put, _restore, _daily, origin = _IMPL[name]
            ok, why, tg = put(form, dec, world, day)
            if not ok:
                _unapplied(rec, i, dec, t, step, why)
                continue
            rec.active.add(i)
            rec.day_done[i] = day
            n += 1
            if before:  # 親のランが決定の行を書いた(再開)=表へ当てるだけ
                rec.tallies["reapplied"] += 1
                continue
            eid = _admit(world, cond_id_of(form, i), what=WHAT_DECISION, who=WHO,
                         where=(("poi", int(tg[0])) if tg.size else None),
                         how_much=(int(tg.size) if tg.size else None), origin=origin)
            rec.applied.append(_row(i, dec, t, step, targets=int(tg.size),
                                    event_id=(None if eid is None else [int(eid[0]), int(eid[1])])))
            continue
        if i not in rec.active:
            continue
        put, restore, daily, _origin = _IMPL[name]
        if ended:
            if i not in rec.ended:
                restore(form, dec, world, day)
                rec.ended.add(i)
                rec.active.discard(i)
                rec.tallies["restored"] += 1
                n += 1
            continue
        if daily and rec.day_done.get(i) != day:
            ok, _why, _tg = put(form, dec, world, day)
            rec.day_done[i] = day
            if ok:
                rec.tallies["reapplied"] += 1
                n += 1
    nt = form.notice
    if nt is not None and form.content and not rec.notice_sent:
        at = int(form.start if nt["at"] is None else nt["at"])
        if world.inherited and at < int(world.begin_ns):
            rec.notice_sent = True  # 親のランが告知の行を書いた(再開)
        elif t >= at and not (form.end is not None and t >= int(form.end)):
            rec.notice_sent = True
            _send_notice(form, world, t, step)
    return n
