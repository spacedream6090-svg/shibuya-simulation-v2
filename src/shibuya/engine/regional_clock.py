"""engine.regional_clock — 場所ごとの時計(第 6 期 6-3 時計の段 T4・TM1・腕 ``--clock regional``)。

正典: 決定 10-12 §4-2 TM1(時計は「全体で 1 つ」「混合」「区域ごと」の 3 つを作り比べる要素に=正しければ行動は一致する=誤りの
検出・メッセージの遅れの影響・速さ/電話は窓の境目で届ける)・TM4(指標に遅刻と待ち合わせの成否を足す・目標はメッセージの
遅れ 10 秒以下)・TM6 の T4(場所ごとの時計=一致が条件=版上げなし・一致の確認は GPU 不要)・TM9(時計の種類の欄)。答申 R-73
§2(保守的な同期・先読み幅)・§7-1(案 b 区域ごとの別々の時計・案 c 混合)。記録 ``docs/bench/analysis/wallbounce-1012/tm234/README.md``。

腕(切替口): ``--clock {global,regional,mixed}``(環境変数 ``SHIBUYA_CLOCK``・:func:`set_arm`)。既定 ``global``=全体で 1 つの
時計(計算のまとめの窓 ``engine.batching.WindowQueue`` だけ=持ち主を作らない)。``regional`` は進行役が :class:`RegionalClock`
を作る。``mixed``(全体+区域)は口だけ=値は空欄(選ぶと組み立てで止める=宣言・TM1 の作る順の 2 番目は後の段)。

区域ごとの時計の形(仮採用=記録 §T4・つなぎの台帳 ``DOC-tm234-t4-*``):

1. 区域: セルの重心を 500 m の格子で塊にしたもの(世界資産 520 セル → 29 区域)+舞台の外(セル < 0)の区域 1 つ。区域の番号は
   格子の (x, y) の昇順。
2. 区域ごとに窓の頭(``_rc_head``)を持ち、区域の事象(今は会話の時計 T2 の発言の事象)をその区域の窓の中で時刻順に処理する
   (区域の番号の昇順に区域ごと・区域の中は時刻 → 体 → 予約の番号)。区域どうしは窓の中で互いを待たない。
3. 世界の 1 回の系の並び(刻みの事象)は全体の事象=全部の区域の窓の境目にそろう(先読み幅=窓の幅・障壁)。系はこれまでどおり
   全員の配列を 1 回で処理する(区域ごとに系を割らない=結果は全体で 1 つの時計と同じ)。
4. 区域をまたぐ事象は境目で届ける: (a) 移動=窓の境目で体の区域を前の境目の写しと比べ、変わった体を数える(移動は刻みの事象の
   中で起き、刻みは窓の頭に乗る=次に読まれるのは次の刻み=全体で 1 つの時計との遅れ 0)。(b) 発言を聞く人が別の区域=その窓の
   終わりに届く(遅れ=窓の終わり − 発言の時刻=``hear_delay_ns``)。(c) 区域の事象を処理し終えた区域へ同じ窓の中に予約した
   事象=窓の終わりに届ける(``cross_events``)。(d) メッセージと電話=今の世界に無い(C1 の後)=欄だけ。
5. 遅刻(TM4 の指標): 計画実行層の日の表(到着の刻み・ブロックの始め)から、到着が始めより遅い数と分を、窓に入った刻みごとに
   数える(計器だけ)。待ち合わせの成否は今の世界に約束の仕組みが無い(C10 8d の後)=欄だけ(null)。

状態(状態台帳の腕の行 ``T4W``=軸 1 diag・軸 2 discardable): 区域ごとの窓の頭・区域の事象の列・体の区域の写し・遅刻の日の表・
計器。世界の状態を書かない=どちらのハッシュにも状態のファイルにも入らない(再開では進行役が作り直す)。

逐次ループ宣言(P4): ``run_windows`` は事象のある区域の数ぶん(≤ 30)× 区域の中の相異なる時刻の数ぶん × 種類の続きの数ぶん。
移動と遅刻は配列演算(体の数・ブロックの数の Python のループは無い)。
"""

from __future__ import annotations

import os
from types import MappingProxyType
from typing import Any, Callable, Final, Mapping

import numpy as np

from shibuya.core.time_consts import CLOCK_KIND, NS_PER_SECOND, SECONDS_PER_MINUTE, STEP_SECONDS
from shibuya.engine import owner_guard as _OG

__all__ = [
    "SCHEMA", "ENV", "FP_KEY", "ARM_GLOBAL", "ARM_REGIONAL", "ARM_MIXED", "ARMS", "DEFAULT_ARM", "arm", "set_arm",
    "is_default", "CLOCK_KIND_REGIONAL", "REGION_SIZE_M", "REGION_CELLS_FALLBACK", "MIXED_NOTE", "region_of_cells",
    "clock_kind", "RegionalClock", "CONFIG_KEYS", "OBSERVED_KEYS", "manifest_fields", "make",
]

SCHEMA: Final[str] = "shibuya.engine.regional_clock/1"
ENV: Final[str] = "SHIBUYA_CLOCK"
FP_KEY: Final[str] = "clock"
ARM_GLOBAL: Final[str] = "global"
ARM_REGIONAL: Final[str] = "regional"
ARM_MIXED: Final[str] = "mixed"
ARMS: Final[tuple[str, ...]] = (ARM_GLOBAL, ARM_REGIONAL, ARM_MIXED)
DEFAULT_ARM: Final[str] = ARM_GLOBAL
#: TM9 の欄 ``clock_kind`` の値(区域ごとの時計のラン)。全体で 1 つの時計は ``core.time_consts.CLOCK_KIND``(steps)のまま。
CLOCK_KIND_REGIONAL: Final[str] = "regional"
#: 区域の格子の幅[m](セル 100 m の 5 × 5=仮採用)。
REGION_SIZE_M: Final[float] = 500.0
#: セルの重心の無い世界の区域(セルの番号 ÷ この数=仮採用・世界資産と合成の世界はどちらも重心を持つ)。
REGION_CELLS_FALLBACK: Final[int] = 25
#: 混合の時計の宣言(口だけ・値は空欄)。
MIXED_NOTE: Final[str] = ("混合の時計(全体の窓で揃え、窓の中は区域ごとに順序を外す=R-73 §7-1 案 c)は口だけ・値は空欄"
                          "(TM1 の作る順は全体 → 混合 → 区域ごと・計画 6-3 は区域ごとの一致の確認を先に作った)")

_raw = os.environ.get(ENV, "").strip().lower()
if _raw and _raw not in ARMS:
    raise ValueError(f"{ENV} は {ARMS} のどれか(いま {_raw!r})")
_ARM: str = _raw or DEFAULT_ARM
del _raw


def arm() -> str:
    """いまの腕(``global``=既定・``regional``・``mixed``=口だけ)。進行役と組み立てが読む。"""
    return _ARM


def set_arm(name: str) -> None:
    """腕を選ぶ(CLI ``--clock``・試験の切替口)。ランの始めに読む。"""
    global _ARM
    if str(name) not in ARMS:
        raise ValueError(f"--clock は {ARMS} のどれか(いま {name!r})")
    _ARM = str(name)


def is_default(name: str | None = None) -> bool:
    return (_ARM if name is None else str(name)) == DEFAULT_ARM


def region_of_cells(world: Any) -> tuple[np.ndarray, str]:
    """セル → 区域の番号(int64・0 から)と作り方の名。重心を 500 m の格子で塊にする(格子の (x, y) の昇順に番号)。"""
    n_cells = int(world.n_cells)
    xy = getattr(getattr(world, "assets", None), "cell_centroid", None)
    if xy is None or np.asarray(xy).shape != (n_cells, 2):
        return (np.arange(n_cells, dtype=np.int64) // REGION_CELLS_FALLBACK), "cell_index"
    c = np.asarray(xy, dtype=np.float64)
    ix = np.floor((c - c.min(axis=0)) / REGION_SIZE_M).astype(np.int64)
    key = ix[:, 0] * (int(ix[:, 1].max()) + 1) + ix[:, 1]
    _uniq, inv = np.unique(key, return_inverse=True)
    return inv.astype(np.int64).reshape(-1), "cell_centroid"


def clock_kind(layer: Any) -> str:
    """TM9 の欄 ``clock_kind``(区域ごとの時計の持ち主があれば ``regional``・無ければ今の ``steps``)。"""
    return CLOCK_KIND if layer is None else CLOCK_KIND_REGIONAL


def _new_meter() -> dict[str, Any]:
    return {
        "windows": 0, "region_windows": 0, "events": 0, "dispatches": 0, "cross_events": 0, "cross_delay_ns_sum": 0,
        "cross_delay_ns_max": 0, "boundaries": 0, "cross_moves": 0, "cross_move_delay_ns_max": 0, "hear": 0,
        "hear_cross": 0, "hear_delay_ns_sum": 0, "hear_delay_ns_max": 0, "planned_arrivals": 0, "late_arrivals": 0,
        "late_minutes_sum": 0, "late_minutes_max": 0,
    }


class RegionalClock:
    """場所ごとの時計(状態台帳の腕の行 ``T4W``・持ち主の名 ``clock``)。腕 regional のランだけ進行役が作る。

    〔6-3 検収 M2〕実行時の守り(``engine.owner_guard``=3-2 の ``WindowQueue`` と同じ形): 欄の代入と消去は ``AttributeError``
    (書く口は ``__init__``・``schedule``・``run_windows`` の自分の文だけ・区域の事象の処理の関数を呼ぶ間は閉じる)。区域の事象の
    表・種類の表・計器は読み取り専用の写し(``MappingProxyType``・事象の列は組)・窓の頭と区域の写しと遅刻の日の表の配列は書けない
    印つき(書く口が新しい配列に置き換える)。

    Args:
        region_of_cell: セル → 区域の番号(:func:`region_of_cells`)。
        agents: 体の状態(区域を引くセルを読むだけ)。
        width_s: 窓の幅[秒](計算のまとめの幅と同じ)。
        start_ns: 最初の窓の頭(ランの始め)。
        step_s: 刻みの幅[秒]。
        regions_from: 区域の作り方の名(manifest)。
    """

    LEDGER_ARM: str = "clock-regional"
    name: str = "clock"

    def __init__(self, *, region_of_cell: np.ndarray, agents: Any, width_s: int, start_ns: int,
                 step_s: int = STEP_SECONDS, regions_from: str = "cell_centroid") -> None:
        roc = np.array(region_of_cell, dtype=np.int64, copy=True)
        if roc.ndim != 1 or (roc.size and int(roc.min()) < 0):
            raise ValueError("region_of_cell はセルの数の 0 以上の整数の配列")
        h = _OG.hidden(self)
        h["events"], h["meter"], h["kinds"] = {}, _new_meter(), {}
        with _OG.writing(self):
            self.region_of_cell = _OG.frozen_array(roc)
            self.n_regions = (int(roc.max()) + 1 if roc.size else 0) + 1
            self.outside = self.n_regions - 1
            self.agents = agents
            self.width_ns = int(width_s) * NS_PER_SECOND
            self.step_ns = int(step_s) * NS_PER_SECOND
            self.start_ns = int(start_ns)
            self.regions_from = str(regions_from)
            #: 区域ごとの窓の頭[ns](行 T4W・書けない印つき)。
            self._rc_head: np.ndarray = _OG.frozen_array(np.full(self.n_regions, self.start_ns, dtype=np.int64))
            #: 区域 → 事象の組 ``((時刻 ns, 体, 種類, 予約の番号), …)``(行 T4W・読み取り専用の写し)。
            self._rc_events: Mapping[int, tuple[tuple[int, int, int, int], ...]] = MappingProxyType(h["events"])
            #: 次の予約の番号(行 T4W)。
            self._rc_seq: int = 0
            #: 体の区域の写し(前の境目・最初の境目の前は None・書けない印つき)(行 T4W)。
            self._rc_snap: np.ndarray | None = None
            #: 遅刻の日の表(日の番号・刻み → 予定の到着の数・遅い到着の数・遅れた分=書けない印つき)(行 T4W)。
            self._rc_late: tuple[int, np.ndarray, np.ndarray, np.ndarray] | None = None
            #: 計器(行 T4W・読み取り専用の写し)。
            self._rc_meter: Mapping[str, Any] = MappingProxyType(h["meter"])
            #: 種類の番号 → (名, 処理の関数)(参照=``register``・読み取り専用の写し)。
            self._rc_kinds: Mapping[int, tuple[str, Callable[..., Any]]] = MappingProxyType(h["kinds"])
            #: 処理中の時刻と窓の終わり・この窓で処理し終えた区域(窓の中だけの作業の値)。
            self._rc_now: int | None = None
            self._rc_end: int | None = None
            self._rc_done: frozenset[int] = frozenset()

    def __setattr__(self, name: str, value: Any) -> None:
        _OG.guarded_setattr(self, name, value, "場所ごとの時計")

    def __delattr__(self, name: str) -> None:
        _OG.guarded_delattr(self, name, "場所ごとの時計")

    def _m(self) -> dict[str, Any]:
        return _OG.hidden(self)["meter"]

    # ------------------------------------------------------------------ 区域
    def region_of_agents(self, agents: Any) -> np.ndarray:
        """体の配列 → 区域の番号(セル < 0=舞台の外の区域)。"""
        cell = np.asarray(self.agents.registry.cell, dtype=np.int64)[np.asarray(agents, dtype=np.int64)]
        ok = (cell >= 0) & (cell < self.region_of_cell.size)
        return np.where(ok, self.region_of_cell[np.where(ok, cell, 0)], self.outside)

    def _all_regions(self) -> np.ndarray:
        cell = np.asarray(self.agents.registry.cell, dtype=np.int64)
        ok = (cell >= 0) & (cell < self.region_of_cell.size)
        return np.where(ok, self.region_of_cell[np.where(ok, cell, 0)], self.outside)

    # ------------------------------------------------------------------ 口(会話の時計の ``QueueRouter`` と同じ形)
    def register(self, kind: int, name: str, fn: Callable[..., Any]) -> None:
        """区域の事象の種類を置く(ランの始めだけ=最初の窓の後は ``RuntimeError``)。"""
        k = int(kind)
        kinds = _OG.hidden(self)["kinds"]
        if k in kinds:
            raise ValueError(f"種類 {k} はもう置いた")
        if int(self._m()["windows"]) > 0:
            raise RuntimeError("種類の表は最初の窓で閉じた(register はランの始めだけ)")
        kinds[k] = (str(name), fn)

    def now_ns(self) -> int:
        """処理中の時刻(区域の窓の中)か、全体の窓の頭(=全部の区域の頭の最小)。"""
        return int(self._rc_now) if self._rc_now is not None else int(self._rc_head.min())

    def window_end_ns(self, t_ns: int) -> int:
        """時刻 ``t_ns`` を含む窓の終わり(窓の格子はランの始めから幅ずつ)。"""
        return self.start_ns + ((int(t_ns) - self.start_ns) // self.width_ns + 1) * self.width_ns

    def schedule(self, t_ns: Any, agents: Any, kind: int) -> np.ndarray:
        """区域の事象を予約する(体の今のセルの区域へ)。区域の頭より前の時刻=境目で届ける(``cross_events``)。"""
        k = int(kind)
        if k not in self._rc_kinds:
            raise ValueError(f"置いていない種類 {k}")
        a = np.atleast_1d(np.asarray(agents, dtype=np.int64)).ravel()
        t = np.atleast_1d(np.asarray(t_ns, dtype=np.int64)).ravel()
        if t.size == 1 and a.size != 1:
            t = np.full(a.size, int(t[0]), dtype=np.int64)
        if t.size != a.size:
            raise ValueError(f"時刻と体の数が違う({t.size} と {a.size})")
        floor = self.now_ns()
        if np.any(t < floor):
            raise ValueError(f"過去への予約(処理中の時刻 {floor} ns より前)")
        regs = self.region_of_agents(a)
        out = np.empty(a.size, dtype=np.int64)
        m = self._m()
        events = _OG.hidden(self)["events"]
        seq = int(self._rc_seq)
        for i in range(a.size):  # 逐次: 予約の数ぶん(会話の番 1 つで 1)
            r = int(regs[i])
            ti = int(t[i])
            head = int(self._rc_head[r])
            if self._rc_end is not None and r in self._rc_done and ti < int(self._rc_end):
                head = int(self._rc_end)  # この窓を処理し終えた区域=窓の終わり(境目)で届ける
            if ti < head:  # この区域の窓はもう進んだ=境目で届ける
                d = head - ti
                m["cross_events"] += 1
                m["cross_delay_ns_sum"] += d
                m["cross_delay_ns_max"] = max(int(m["cross_delay_ns_max"]), d)
                ti = head
            events[r] = (*events.get(r, ()), (ti, int(a[i]), k, seq))
            out[i] = seq
            seq += 1
        with _OG.writing(self):
            self._rc_seq = seq
        return out

    def hear_delay_ns(self, t_ns: int, speaker: int, listener: int) -> int:
        """発言を聞く人が別の区域なら窓の終わりに届く(遅れ=窓の終わり − 発言の時刻)・同じ区域は 0。"""
        r = self.region_of_agents(np.asarray([int(speaker), int(listener)], dtype=np.int64))
        m = self._m()
        m["hear"] += 1
        if int(r[0]) == int(r[1]):
            return 0
        d = self.window_end_ns(int(t_ns)) - int(t_ns)
        m["hear_cross"] += 1
        m["hear_delay_ns_sum"] += d
        m["hear_delay_ns_max"] = max(int(m["hear_delay_ns_max"]), d)
        return d

    # ------------------------------------------------------------------ 窓
    def run_windows(self, head: int, end: int, *, presence: Any = None, tpd: int = 0) -> None:
        """全体の窓 [head, end) の後: 境目の移動と遅刻を数え、区域ごとの事象を時刻順に処理し、全部の区域の頭を end にする。"""
        m = self._m()
        m["windows"] += 1
        self._boundary(int(head), int(end))
        if presence is not None and tpd > 0:
            self._lateness(int(head), int(end), presence, int(tpd))
        events = _OG.hidden(self)["events"]
        with _OG.writing(self):
            self._rc_end = int(end)
        try:
            while True:  # 逐次: 事象のある区域の数ぶん(区域の番号の昇順・処理の中で足された区域も拾う)
                todo = [r for r, ev in events.items()
                        if r not in self._rc_done and any(e[0] < int(end) for e in ev)]
                if not todo:
                    break
                r = min(todo)
                self._run_region(int(r), int(end))
                with _OG.writing(self):
                    self._rc_done = self._rc_done | {int(r)}
        finally:
            with _OG.writing(self):
                self._rc_now = None
                self._rc_end = None
                self._rc_done = frozenset()
        with _OG.writing(self):
            self._rc_head = _OG.frozen_array(np.full(self.n_regions, int(end), dtype=np.int64))
        for r in [r for r, ev in events.items() if not ev]:  # 逐次: 区域の数ぶん
            del events[r]

    def _run_region(self, r: int, end: int) -> None:
        m = self._m()
        events = _OG.hidden(self)["events"]
        ran = False
        while True:  # 逐次: 区域の窓の中の相異なる時刻の数ぶん(処理の中の予約で増える)
            ev = events.get(r, ())
            due = sorted(e for e in ev if e[0] < end)
            if not due:
                break
            t0 = due[0][0]
            group = [e for e in due if e[0] == t0]
            events[r] = tuple(e for e in ev if not (e[0] == t0))
            with _OG.writing(self):
                self._rc_now = t0
            ran = True
            m["events"] += len(group)
            i = 0
            while i < len(group):  # 逐次: 種類の続きの数ぶん
                j = i
                while j < len(group) and group[j][2] == group[i][2]:
                    j += 1
                k0 = group[i][2]
                fn = self._rc_kinds[k0][1]
                with _OG.closed(self):  # 外のコード(区域の事象の処理の関数)が走る間は欄を書けない
                    fn(t0, np.asarray([e[1] for e in group[i:j]], dtype=np.int64),
                       np.asarray([e[3] for e in group[i:j]], dtype=np.int64))
                m["dispatches"] += 1
                i = j
        if ran:
            m["region_windows"] += 1

    def _boundary(self, head: int, end: int) -> None:
        """境目の移動: 体の区域を前の境目の写しと比べる(移動は刻みの事象の中=次に読まれるのは次の刻み)。刻みの事象の無い窓
        (幅が刻みより細かいときの 2 つ目以降の窓)では体は動かない=比べない(体の数の走査を窓ごとでなく刻みごとに)。"""
        m = self._m()
        m["boundaries"] += 1
        if self._rc_snap is not None and (head - self.start_ns) % self.step_ns != 0:
            return
        now = self._all_regions()
        if self._rc_snap is not None and self._rc_snap.shape == now.shape:
            moved = int(np.count_nonzero(now != self._rc_snap))
            if moved:
                m["cross_moves"] += moved
                # 全体で 1 つの時計との遅れ: 届く境目(end)と次の刻み(この窓の頭の次の刻み)の遅い方 − 次の刻み=0 以上
                nxt = (head // self.step_ns + 1) * self.step_ns
                m["cross_move_delay_ns_max"] = max(int(m["cross_move_delay_ns_max"]), max(0, end - nxt))
        with _OG.writing(self):
            self._rc_snap = _OG.frozen_array(now)

    def _lateness(self, head: int, end: int, presence: Any, tpd: int) -> None:
        """遅刻: 窓に入った刻みの予定の到着のうち、到着の刻みがブロックの始めより遅い数と分(計器だけ)。到着の刻みは計画実行層の
        日の表の値=窓の幅で動かない(本人の出入りの遅れではない=計画 6-2 の 1b の後)。"""
        lo = -(-head // self.step_ns)
        hi = -(-end // self.step_ns)
        if hi <= lo:
            return
        day = lo // tpd
        late = self._rc_late
        if late is None or int(late[0]) != day:
            arr = getattr(presence, "arrival_tick", None)
            blocks = getattr(presence, "blocks", None)
            if arr is None or blocks is None:
                return
            a = np.asarray(arr, dtype=np.int64)
            s = np.asarray(blocks.start, dtype=np.int64)[: a.size]
            ok = (a >= 0) & (a < tpd)
            is_late = ok & (a > s)
            n_plan = np.bincount(a[ok], minlength=tpd)[:tpd]
            n_late = np.bincount(a[is_late], minlength=tpd)[:tpd]
            mins = np.bincount(a[is_late], weights=(a - s)[is_late].astype(np.float64), minlength=tpd)[:tpd]
            late = (day, _OG.frozen_array(n_plan.astype(np.int64)), _OG.frozen_array(n_late.astype(np.int64)),
                    _OG.frozen_array(mins))
            with _OG.writing(self):
                self._rc_late = late
        m = self._m()
        steps = np.arange(lo, hi, dtype=np.int64) - day * tpd
        steps = steps[(steps >= 0) & (steps < tpd)]
        if steps.size == 0:
            return
        m["planned_arrivals"] += int(late[1][steps].sum())
        m["late_arrivals"] += int(late[2][steps].sum())
        step_min = self.step_ns / NS_PER_SECOND / SECONDS_PER_MINUTE
        add = float(late[3][steps].sum()) * step_min
        m["late_minutes_sum"] += int(round(add))
        if int(late[2][steps].sum()):
            per = np.where(late[2][steps] > 0, late[3][steps] / np.maximum(late[2][steps], 1), 0.0)
            m["late_minutes_max"] = max(int(m["late_minutes_max"]), int(round(float(per.max()) * step_min)))

    # ------------------------------------------------------------------ 計器
    def observed(self) -> dict[str, Any]:
        m = self._rc_meter
        out = {k: int(v) for k, v in m.items()}
        out["message_delay_ns_max"] = max(int(m["hear_delay_ns_max"]), int(m["cross_delay_ns_max"]))
        out["pending_at_end"] = int(sum(len(v) for v in self._rc_events.values()))
        out["meeting"] = None
        return out


CONFIG_KEYS: Final[tuple[str, ...]] = ("schema", "arm", "clock_kind", "region_size_m", "regions_from", "n_regions",
                                       "outside_region", "width_s", "messages", "meeting_note", "mixed")
OBSERVED_KEYS: Final[tuple[str, ...]] = (*_new_meter(), "message_delay_ns_max", "pending_at_end", "meeting")


def manifest_fields(clock: RegionalClock | None) -> dict[str, Any] | None:
    """manifest の ``clock``(腕 regional のランだけ・既定の腕は None=節を出さない)。"""
    if clock is None:
        return None
    cfg: Mapping[str, Any] = {
        "schema": SCHEMA, "arm": ARM_REGIONAL, "clock_kind": CLOCK_KIND_REGIONAL, "region_size_m": REGION_SIZE_M,
        "regions_from": clock.regions_from, "n_regions": int(clock.n_regions), "outside_region": int(clock.outside),
        "width_s": int(clock.width_ns // NS_PER_SECOND),
        "messages": "メッセージと電話は今の世界に無い(C1 の後)=欄だけ・遅れは発言を聞く人の区域またぎで測る",
        "meeting_note": "待ち合わせの成否は約束の仕組みの後(C10 8d)=欄だけ(null)", "mixed": MIXED_NOTE,
    }
    return {**cfg, **clock.observed()}


def make(*, world: Any, agents: Any, width_s: int, start_ns: int, step_s: int) -> RegionalClock | None:
    """進行役の口: 腕 regional のときだけ区域ごとの時計を作る(既定 global は None・mixed は止める=口だけ)。"""
    if _ARM == ARM_GLOBAL:
        return None
    if _ARM == ARM_MIXED:
        raise NotImplementedError(MIXED_NOTE)
    roc, how = region_of_cells(world)
    return RegionalClock(region_of_cell=roc, agents=agents, width_s=int(width_s), start_ns=int(start_ns),
                         step_s=int(step_s), regions_from=how)
