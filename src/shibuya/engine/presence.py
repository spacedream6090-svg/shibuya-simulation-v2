"""engine.presence — 計画実行層(Presence & Plan Executor・D-66 第1段)。

正典
- ``docs/design/v2-plan-executor-design.md``(ユーザー承認・第145)。§1 責務・§2 データ・
  §3 イベントと tick 処理・§4 LLM との分担・§5 不変条件 I1-I6・§6 帰無腕と expedient。
- 背景の数値は ``docs/design/v2-d66-outside-residents-agenda.md`` §1(親検証済み)。

何をする層か
    「誰がいつ舞台に居て何をしているか」を**機構として**持つ。W17 週次表を **在圏ブロック**
    に畳み、日次のイベント列(到着・退出・就寝・起床)を組んで、tick ごとに
    ``engine.resolve`` の既存の書き込み口だけを叩く。**世界への書き込み口は増やさない**
    (``rail_arrive`` / ``rail_depart`` / ``begin_planned_sleep`` / ``wake_from_plan`` /
    ``release_indoor`` / ``balk_queue`` / ``place_at_external`` / ``set_plan_state``)。

層契約
    ``engine`` 内・``world`` と ``agents`` は**読むだけ**・``build`` は import しない
    (方面ノード → 路線の表は ``world.assets.ProcessAssets`` が Parquet から読む)。

逐次ループ宣言(P4)
1. **日次構築 1 回**: 到着の山の分散(``_spread_arrivals``)が**便数**ぶんのループを 1 本持つ
   (線ごとに、その線の便を時刻の降順に 1 回走る。個体数には比例しない)。
2. **tick ごと**: イベント種(5)ぶんの ``flatnonzero`` と、退出繰り延べの**繰り延べ中の体数**
   ぶんのベクトル演算。**個体数に比例する Python ループは無い**。

expedient(本モジュール分・実装計画書 §8「D-66/計画実行層(第1段)」が正典)
- E1 到着便=「ブロック開始に間に合う最も遅い便」(始発前は始発)。
- E2 方面 → 線(埼京/湘南新宿ラインは W12 の ``lines[0]`` = 埼京線に畳む)。
- E3 非鉄道ゲート(方面 8/9)は所要時間なし=開始 tick ちょうどにゲートセルへ。
- E4 退出は即時 ``rail_depart``(受容関数を通さない)。``--exit-mode`` は ``immediate`` のみ実装。
- E5 W17 の乗車行は在圏に数えない(``count_transit=False``)。
- E6 出勤率(``--attendance-rate``)= 通勤・通学の一部をその日「終日域外」にする。
- E7 その日の在圏ブロックが 0 本の体は終日域外。
- E8 到着分散の上限 k=8 便・容量ベース backward fill。
- E9 計画一致率の定義(正時標本・両側)。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

import numpy as np

from shibuya.agents.state import Activity, AgentState
from shibuya.agents.weekly import (
    ACTIVITY_WORDS,
    MINUTES_PER_DAY,
    N_DAYS,
    PLACE_KIND_OUTSIDE,
    PLACE_WORDS,
)
from shibuya.engine import resolve as R
from shibuya.world.state import World

__all__ = [
    "ARRIVAL_SPREAD_MAX_TRAINS",
    "EXIT_DEFER_LIMIT",
    "EXIT_MODES",
    "EventType",
    "PlanBlocks",
    "PlanExecutor",
]

#: 到着の山を溢れさせる上限[便](§3「容量ベース backward fill」・expedient E8)。
ARRIVAL_SPREAD_MAX_TRAINS: Final[int] = 8

#: 退出 tick に会話中だった体を繰り延べる上限[tick](§4・expedient)。
EXIT_DEFER_LIMIT: Final[int] = 30

#: 退出の実行形(§10-3)。第1段は ``immediate`` のみ実装(他は ``NotImplementedError``)。
EXIT_MODES: Final[tuple[str, ...]] = ("immediate", "board_intent", "walk_to_platform")

#: 「乗車」の活動語コード(``ACTIVITY_WORDS`` の索引)。
RIDE_ACTIVITY_CODE: Final[int] = ACTIVITY_WORDS.index("乗車")
#: 「就寝」の活動語コード。
SLEEP_ACTIVITY_CODE: Final[int] = ACTIVITY_WORDS.index("就寝")
#: 「自宅」の場所種別コード。
PLACE_KIND_HOME: Final[int] = PLACE_WORDS.index("自宅")
#: 「宿泊施設」の場所種別コード(**そこで寝るのは正当**=職場就寝の計数から外す)。
PLACE_KIND_LODGING: Final[int] = PLACE_WORDS.index("宿泊施設")

#: 「次の行」を探すときに飛ばせる連続乗車行の上限(逐次ループの上界・expedient)。
_MAX_RIDE_RUN: Final[int] = 8

#: 出勤率(E6)の対象種別(``agents.state.AgentKind``: 0=通勤者 / 5=通学者)。
ATTENDANCE_KINDS: Final[tuple[int, ...]] = (0, 5)


class EventType:
    """日次イベントの種(設計書 §3 の表)。値は表の番号。"""

    ARRIVE: Final[int] = 0
    DEPART: Final[int] = 1
    SLEEP: Final[int] = 2
    WAKE: Final[int] = 3
    WORK_START: Final[int] = 4  # 第2陣(``target_node`` の書き込み口が無い=未実装)
    AT_HOME: Final[int] = 5  # 同上


#: 同一 tick 内の実行順(**退出 → 到着**の順にする=同 tick に両方ある体を取りこぼさない)。
_TYPE_ORDER: Final[dict[int, int]] = {
    EventType.DEPART: 0,
    EventType.ARRIVE: 1,
    EventType.SLEEP: 2,
    EventType.WAKE: 3,
}

#: ``plan_flags`` のビット(設計書 §2)。
FLAG_HOME_OUT: Final[int] = 1 << 0
FLAG_HAS_PLAN: Final[int] = 1 << 1
FLAG_EXIT_DEFERRED: Final[int] = 1 << 2
FLAG_ARRIVED: Final[int] = 1 << 3


def _mix64(x: np.ndarray) -> np.ndarray:
    """splitmix64 の最終混合(決定論・ベクトル化・**乱数ではない**)。

    出勤率(E6)の「その日来ない 12%」を ``agent_id`` だけから決めるのに使う。
    ``core.rng`` の Philox を使わないのは**ランの乱数列を 1 語も消費しない**ため
    (T4 規模不変・帰無腕とのバイト一致を保つ)。``build.sched.w17_schedule._mix64``
    と同じ式(二重定義・テストが一致を機械検査)。
    """
    v = np.asarray(x, dtype=np.uint64).copy()
    with np.errstate(over="ignore"):
        v ^= v >> np.uint64(33)
        v *= np.uint64(0xFF51AFD7ED558CCD)
        v ^= v >> np.uint64(33)
        v *= np.uint64(0xC4CEB9FE1A85EC53)
        v ^= v >> np.uint64(33)
    return v


def _day_rows(weekly, day: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """その曜日の全活動を ``(体行, 全体行索引, 体ごとの件数)`` に展開する(ループなし)。

    ``agents.weekly.WeeklySchedule._day_rows`` と同じ式(private に依存しないための写し)。
    """
    n = int(weekly.n_agents)
    d = int(day) % N_DAYS
    off = np.asarray(weekly.day_offset, dtype=np.int64)
    lo = off[d::N_DAYS][:n]
    hi = off[d + 1 :: N_DAYS][:n]
    counts = hi - lo
    total = int(counts.sum())
    if total == 0:
        e = np.empty(0, dtype=np.int64)
        return e, e, counts
    rows = np.repeat(np.arange(n, dtype=np.int64), counts)
    base = np.repeat(np.cumsum(counts) - counts, counts)
    idx = np.repeat(lo, counts) + (np.arange(total, dtype=np.int64) - base)
    return rows, idx, counts


@dataclass(frozen=True)
class PlanBlocks:
    """**在圏ブロック**(その体がその日「舞台に居る」連続区間)の CSR。

    Attributes:
        n_agents: 体行の数。
        offset: ``(n_agents+1,)`` の CSR 索引(体行 → ブロック範囲)。
        start / end: ブロックの開始・終了[分]。
        activity / place_kind / target_cell: ブロック**先頭行**の属性。
        mode: ``"derive"``(現行 W17 を畳んだ)/ ``"native"``(ブロック形式をそのまま読んだ)。
        count_transit: 「乗車」行を在圏に数えたか(E5 の切替口)。

    Note:
        ブロックの定義(**居住区分つき**・設計書 §2):
        ``place_kind ≠ 域外`` ∧ ``活動 ≠ 乗車`` の**連続行**を 1 本に畳む。
        **域外居住者(``home_out``)の「自宅」行は域外**として扱う(=在圏でない)。
        域内居住者の「自宅」行は在圏(舞台の中に家がある)。
    """

    n_agents: int
    offset: np.ndarray
    start: np.ndarray
    end: np.ndarray
    activity: np.ndarray
    place_kind: np.ndarray
    target_cell: np.ndarray
    #: そのブロックの**直後の行**(乗車行は飛ばす)が「域外」か。``home_in`` の退出判定に使う
    #: (設計書 §10-7 (a)「域外行の開始で退出」)。次の行が無ければ False。
    next_outside: np.ndarray | None = None
    mode: str = "derive"
    count_transit: bool = False

    @property
    def n_blocks(self) -> int:
        return int(self.start.size)

    @property
    def agent_of_block(self) -> np.ndarray:
        """ブロック → 体行(CSR の展開)。"""
        counts = np.diff(self.offset)
        return np.repeat(np.arange(self.n_agents, dtype=np.int64), counts)

    def blocks_per_agent(self) -> np.ndarray:
        return np.diff(self.offset).astype(np.int64)

    def all_day_outside(self) -> np.ndarray:
        """その日 1 本も在圏ブロックが無い体行(=終日域外・E7)。"""
        return np.flatnonzero(self.blocks_per_agent() == 0)

    def in_area_at(self, minute: int) -> np.ndarray:
        """その分に**計画上**在圏のはずの体(``(n_agents,)`` bool・ループなし)。"""
        out = np.zeros(self.n_agents, dtype=bool)
        if self.n_blocks == 0:
            return out
        m = int(minute)
        key = self.agent_of_block * (MINUTES_PER_DAY + 1) + self.start.astype(np.int64)
        probe = np.arange(self.n_agents, dtype=np.int64) * (MINUTES_PER_DAY + 1) + m
        pos = np.searchsorted(key, probe, side="right") - 1
        ok = (pos >= self.offset[:-1]) & (self.offset[1:] > self.offset[:-1])
        safe = np.where(ok, pos, 0)
        out = ok & (self.start[safe] <= m) & (self.end[safe] > m)
        return out

    @classmethod
    def from_weekly(
        cls,
        weekly,
        day: int,
        home_out,
        *,
        mode: str = "derive",
        count_transit: bool = False,
        exclude=None,
    ) -> "PlanBlocks":
        """W17 週次表 → 在圏ブロック(§2 の読み口)。

        Args:
            weekly: ``agents.weekly.WeeklySchedule``(ランの体行へ ``restrict_to`` 済み)。
            day: 曜日(0=月曜)。
            home_out: ``(n_agents,)`` の bool。域外居住(``home_cell < 0``)。
            mode: ``"derive"``(現行 W17 を畳む)/ ``"native"``(``block_kind`` 列を読む・**未実装**)。
            count_transit: True なら「乗車」行も在圏に数える(E5 の帰無側)。
            exclude: ``(n_agents,)`` bool。True の体は**ブロック 0 本**にする(E6 出勤率)。

        Returns:
            ``PlanBlocks``。

        Raises:
            NotImplementedError: ``mode="native"``(W17 ブロック形式は第2弾)。
        """
        if mode == "native":
            raise NotImplementedError(
                "PlanBlocks(mode='native') は W17 ブロック形式(設計書 §9)の再生成後=第2弾"
            )
        if mode != "derive":
            raise ValueError(f"mode は 'derive' / 'native'(いま {mode!r})")
        n = int(weekly.n_agents)
        ho = np.asarray(home_out, dtype=bool).ravel()
        if ho.size < n:
            ho = np.concatenate([ho, np.zeros(n - ho.size, dtype=bool)])
        ex = (
            np.zeros(n, dtype=bool)
            if exclude is None
            else np.asarray(exclude, dtype=bool).ravel()[:n]
        )
        if ex.size < n:
            ex = np.concatenate([ex, np.zeros(n - ex.size, dtype=bool)])
        rows, idx, _counts = _day_rows(weekly, day)
        empty = np.empty(0, dtype=np.int64)
        if idx.size == 0:
            return cls(
                n_agents=n,
                offset=np.zeros(n + 1, dtype=np.int64),
                start=empty,
                end=empty,
                activity=np.empty(0, dtype=np.int8),
                place_kind=np.empty(0, dtype=np.int8),
                target_cell=np.empty(0, dtype=np.int32),
                next_outside=np.empty(0, dtype=bool),
                mode=mode,
                count_transit=count_transit,
            )
        s = np.asarray(weekly.start_min, dtype=np.int64)[idx]
        order = np.lexsort((s, rows))  # (体行, 開始分) 昇順へ揃える
        rows, idx, s = rows[order], idx[order], s[order]
        e = np.asarray(weekly.end_min, dtype=np.int64)[idx]
        act = np.asarray(weekly.activity, dtype=np.int8)[idx]
        pk = np.asarray(weekly.place_kind, dtype=np.int8)[idx]
        cell = np.asarray(weekly.target_cell, dtype=np.int32)[idx]

        live = pk != PLACE_KIND_OUTSIDE
        if not count_transit:
            live &= act != RIDE_ACTIVITY_CODE
        live &= ~(ho[rows] & (pk == PLACE_KIND_HOME))  # 域外居住者の「自宅」行は域外
        live &= ~ex[rows]

        same = np.empty(rows.size, dtype=bool)
        same[0] = False
        same[1:] = rows[1:] == rows[:-1]
        prev_live = np.empty(rows.size, dtype=bool)
        prev_live[0] = False
        prev_live[1:] = live[:-1]
        next_live = np.empty(rows.size, dtype=bool)
        next_live[-1] = False
        next_live[:-1] = live[1:]
        next_same = np.empty(rows.size, dtype=bool)
        next_same[-1] = False
        next_same[:-1] = rows[:-1] == rows[1:]

        head = live & ~(prev_live & same)
        tail = live & ~(next_live & next_same)
        # ---- ブロックの直後の行(**乗車行は飛ばす**)が「域外」か ----
        # 設計書 §10-7 (a)「域内居住者は域外行の開始で退出」。乗車行を飛ばすのは E5
        # (乗車行はそもそもブロックに数えない)との整合——自宅 → 乗車(駅) → 域外 の
        # 並びで「次の行=乗車」と読むと住民が一生退出しなくなる。
        nxt = np.arange(rows.size, dtype=np.int64) + 1
        ok_n = (nxt < rows.size) & (rows[np.minimum(nxt, rows.size - 1)] == rows)
        is_ride = act == RIDE_ACTIVITY_CODE
        for _ in range(_MAX_RIDE_RUN):  # 逐次ループ宣言: 連続する乗車行の最大長(≤8)ぶん
            hop = ok_n & is_ride[np.minimum(nxt, rows.size - 1)]
            if not hop.any():
                break
            nxt = np.where(hop, nxt + 1, nxt)
            ok_n = ok_n & (nxt < rows.size) & (rows[np.minimum(nxt, rows.size - 1)] == rows)
        next_out_row = ok_n & (pk[np.minimum(nxt, rows.size - 1)] == PLACE_KIND_OUTSIDE)
        b_agent = rows[head]
        b_start = s[head]
        b_end = e[tail]
        counts = np.bincount(b_agent, minlength=n)[:n]
        offset = np.zeros(n + 1, dtype=np.int64)
        np.cumsum(counts, out=offset[1:])
        return cls(
            n_agents=n,
            offset=offset,
            start=b_start.astype(np.int32),
            end=b_end.astype(np.int32),
            activity=act[head],
            place_kind=pk[head],
            target_cell=cell[head],
            next_outside=next_out_row[tail],
            mode=mode,
            count_transit=count_transit,
        )


class _HomeShim:
    """``resolve.begin_planned_sleep(schedule=…)`` に渡す自宅セルの入れ物。

    ``schedule.home_cell`` だけを読む口なので、**域外居住者は −1 のまま**の配列を渡す
    (−1 は ``begin_planned_sleep`` の ``ok_cell`` で落ちる=**職場で寝ない**)。
    """

    __slots__ = ("home_cell",)

    def __init__(self, home_cell: np.ndarray) -> None:
        self.home_cell = np.asarray(home_cell, dtype=np.int32)


class PlanExecutor:
    """計画実行層(D-66 第1段)。日次でイベント列を組み、tick ごとに resolve を叩く。

    Args:
        world / agents: 状態(**読むだけ**。書き込みは ``engine.resolve`` の口)。
        weekly: ``agents.weekly.WeeklySchedule``(ランの体行へ ``restrict_to`` 済み)。
        day_index: 曜日(0=月曜)。
        home_cell: ``(n,)`` の自宅セル(**域外居住は −1 のまま**)。
        direction_node: ``(n,)`` の方面ノード索引(W16。-1=未付与)。
        kind: ``(n,)`` の ``AgentKind``(出勤率 E6 の対象判定)。
        agent_id: ``(n,)`` の元 ``agent_id``(出勤率 E6 の決定論キー=T4 規模不変)。
        rail: ``engine.processes.rail.RailProcess``(``None`` 可=全方面をゲート扱い)。
        assets: ``world.assets.ProcessAssets``(方面→線・駅出口セル)。
        ticks: ラン長[tick]。
        exit_mode: ``immediate`` のみ実装(他は ``NotImplementedError``)。
        attendance_rate: 出勤率(E6・既定 1.0=全員来る)。
    """

    #: 台帳の感度試験 id(``--ablate AB-PLAN-EXECUTOR`` / 帰無腕 ``--no-plan-executor``)。
    ablation_id: Final[str] = "AB-PLAN-EXECUTOR"
    process_ids: Final[tuple[str, ...]] = ("plan_execution",)

    def __init__(
        self,
        world: World,
        agents: AgentState,
        weekly,
        *,
        day_index: int = 0,
        home_cell=None,
        direction_node=None,
        kind=None,
        agent_id=None,
        rail: Any | None = None,
        assets: Any | None = None,
        ticks: int = MINUTES_PER_DAY,
        exit_mode: str = "immediate",
        attendance_rate: float = 1.0,
        mode: str = "derive",
    ) -> None:
        if exit_mode not in EXIT_MODES:
            raise ValueError(f"--exit-mode は {EXIT_MODES} のどれか(いま {exit_mode!r})")
        if exit_mode != "immediate":
            raise NotImplementedError(
                f"exit_mode={exit_mode!r} は第2陣(設計書 §10-3・切替口だけ予約)"
            )
        rate = float(attendance_rate)
        if not (0.0 <= rate <= 1.0):
            raise ValueError(f"--attendance-rate は 0.0〜1.0(いま {rate})")
        self.world = world
        self.agents = agents
        self.weekly = weekly
        self.rail = rail
        self.assets = assets
        self.day_index = int(day_index)
        self.ticks = int(ticks)
        self.exit_mode = str(exit_mode)
        self.attendance_rate = rate
        self.mode = str(mode)
        n = int(agents.n)
        self.n = n
        m = min(n, int(weekly.n_agents))
        #: 層が面倒を見る体(週次表に行がある体)。それ以外は在圏のまま触らない。
        self.managed = np.zeros(n, dtype=bool)
        self.managed[:m] = True

        hc = np.full(n, -1, dtype=np.int32)
        if home_cell is not None:
            src = np.asarray(home_cell, dtype=np.int64).ravel()
            hc[: min(n, src.size)] = src[: min(n, src.size)].astype(np.int32)
        self.home_cell = hc
        self.home_out = self.managed & (hc < 0)
        self._home_shim = _HomeShim(hc)

        dn = np.full(n, -1, dtype=np.int64)
        if direction_node is not None:
            src = np.asarray(direction_node, dtype=np.int64).ravel()
            dn[: min(n, src.size)] = src[: min(n, src.size)]
        self.direction_node = dn
        self.line_of_agent = self._lines_of_direction(dn)

        kd = np.full(n, -1, dtype=np.int64)
        if kind is not None:
            src = np.asarray(kind, dtype=np.int64).ravel()
            kd[: min(n, src.size)] = src[: min(n, src.size)]
        aid = np.arange(n, dtype=np.int64)
        if agent_id is not None:
            src = np.asarray(agent_id, dtype=np.int64).ravel()
            aid[: min(n, src.size)] = src[: min(n, src.size)]
        self.absent = self._attendance_absent(kd, aid, rate)

        # ---- 在圏ブロック(§2)----
        exclude = np.zeros(int(weekly.n_agents), dtype=bool)
        exclude[: min(m, exclude.size)] = self.absent[: min(m, exclude.size)]
        self.blocks = PlanBlocks.from_weekly(
            weekly, self.day_index, self.home_out[:m], mode=self.mode, exclude=exclude
        )
        # ---- 診断カウンタ ----
        self.n_arrivals = 0
        self.n_departures = 0
        self.n_arrive_skipped = 0
        self.n_depart_skipped = 0
        self.n_exit_deferred = 0
        self.n_exit_forced = 0
        self.n_shopping_interrupted = 0
        self.n_queue_balked = 0
        self.n_pulled_in = 0
        self.n_pushed_out = 0
        self.n_departed_by_llm = 0
        self.n_depart_dropped = 0
        self.n_rearmed = 0
        self.n_placed_at_start = 0
        self.n_gate_arrivals = 0
        self.n_spread_moved = 0
        #: 前後どちらにも行き場が無く**便が受け切った**体(=混雑率が上限を超える分)。
        self.n_spread_overflow = 0
        self.sleep_counts: dict[str, int] = {}
        #: 正時標本(計画一致率・昼夜比・在圏人数)。
        self.sample_hours: list[int] = []
        self.sample_in_area: list[int] = []
        self.match_in_num = 0
        self.match_in_den = 0
        self.match_out_num = 0
        self.match_out_den = 0
        self.in_area_by_hour: list[float] = [float("nan")] * 24
        #: 正時の「**在圏の体のうち**起きている割合」(``RunResult.wake_rate_by_hour`` は
        #: 域外の体も「起きている」に数えるので、a(h) と並べるならこちら=診断の補助欄)。
        self.wake_in_area_by_hour: list[float] = [float("nan")] * 24
        #: **域外常住(``home_out``)なのに舞台の中で寝た**体の延べ数(=「職場で寝る」の直接計測)。
        self.n_home_out_slept_inside = 0
        # ---- 退出の繰り延べ(§4)----
        self._defer_ids = np.empty(0, dtype=np.int64)
        self._defer_deadline = np.empty(0, dtype=np.int64)
        self._defer_line = np.empty(0, dtype=np.int64)
        # ---- 動的に張り直す到着(civic の押し出し・LLM の乗車)----
        self._extra: dict[int, list[tuple[int, int]]] = {}
        #: **落とす DEPART の tick**(域外へ出た体の進行中ブロックぶん。-1=落とさない)。
        self._skip_depart_at = np.full(n, -1, dtype=np.int32)

        self._build_events()

    # ------------------------------------------------------------------ 起動時の展開
    def _lines_of_direction(self, direction: np.ndarray) -> np.ndarray:
        """方面ノード索引 → 路線索引(``tt_lines`` の索引。-1=非鉄道ゲート/未知)。

        表は ``world.assets.ProcessAssets.ext_node_line_idx``(W12 ``w12_external_nodes``
        の ``lines[0]`` を ``tt_lines`` に引いたもの)。**expedient E2**: 埼京線/湘南新宿
        ラインのような複数線の方面は先頭の線に畳む。
        """
        table = getattr(self.assets, "ext_node_line_idx", None)
        out = np.full(direction.size, -1, dtype=np.int64)
        if table is None:
            return out
        t = np.asarray(table, dtype=np.int64)
        ok = (direction >= 0) & (direction < t.size)
        out[ok] = t[direction[ok]]
        # 便が 1 本も無い線はゲート扱い(=時刻表に載っていない線)
        present = getattr(self.rail, "lines_present", None)
        if present is not None and np.asarray(present).size:
            has = np.isin(out, np.asarray(present, dtype=np.int64))
            out = np.where(has, out, -1)
        elif self.rail is not None:
            out[:] = -1
        return out

    def _attendance_absent(
        self, kind: np.ndarray, agent_id: np.ndarray, rate: float
    ) -> np.ndarray:
        """出勤率(E6)で「その日来ない」体(``(n,)`` bool)。既定 1.0 では全て False。"""
        out = np.zeros(self.n, dtype=bool)
        if rate >= 1.0:
            return out
        target = np.isin(kind, np.asarray(ATTENDANCE_KINDS, dtype=np.int64))
        u = (_mix64(np.maximum(agent_id, 0).astype(np.uint64)) % np.uint64(10_000)).astype(
            np.int64
        )
        thr = int(round(rate * 10_000))
        return target & self.managed & (u >= thr)

    def _exit_cells(self) -> np.ndarray:
        """降車セルの候補(W11 駅出口セル。無ければホームセル。どちらも無ければ空)。"""
        ex = getattr(self.assets, "station_exit_cell", None)
        if ex is not None:
            c = np.asarray(ex, dtype=np.int64).ravel()
            c = c[(c >= 0) & (c < self.world.n_cells)]
            if c.size:
                return np.unique(c)
        cells = getattr(self.rail, "line_cell", None)
        if cells is not None:
            c = np.asarray(cells, dtype=np.int64).ravel()
            c = c[(c >= 0) & (c < self.world.n_cells)]
            if c.size:
                return np.unique(c)
        return np.zeros(0, dtype=np.int64)

    def _assign_trains(self, b_agent: np.ndarray, b_start: np.ndarray) -> np.ndarray:
        """ブロック → 到着便(**間に合う最も遅い便**・始発前は始発。-1=ゲート)。E1。"""
        train = np.full(b_agent.size, -1, dtype=np.int64)
        rail = self.rail
        if rail is None or not getattr(rail, "active", False):
            return train
        line_of = self.line_of_agent[b_agent]
        enter = np.asarray(rail.enter_tick, dtype=np.int64)
        tline = np.asarray(rail.train_line, dtype=np.int64)
        for li in np.unique(line_of[line_of >= 0]).tolist():  # 逐次: 線数(≤8)
            idx = np.flatnonzero(tline == li)
            if idx.size == 0:
                continue
            order = idx[np.argsort(enter[idx], kind="stable")]
            ent = enter[order]
            here = np.flatnonzero(line_of == li)
            pos = np.searchsorted(ent, b_start[here], side="right") - 1
            pos = np.maximum(pos, 0)  # 始発前は始発(E1)
            train[here] = order[pos]
        return train

    def _spread_arrivals(self, train: np.ndarray, b_agent: np.ndarray) -> np.ndarray:
        """到着の山を**容量ベースで前後へ**散らす(E8・§3)。

        規則(2026-09-11・層2 指摘で両側化): 便の受け入れ上限 = ``定員 × 混雑率上限``。
        ① **後ろ向き(早い便へ)**: 時刻の降順に走り、溢れた分を ``agent_row`` の大きい方から
        1 便ずつ早い便へ送る(上限 ``ARRIVAL_SPREAD_MAX_TRAINS`` 便)。**間に合う**側なので
        こちらが第一。② **前向き(遅い便へ)**: ① で置き切れずに残った分(=最も早い便に
        山積みになる分)を時刻の昇順に 1 便ずつ遅い便へ送る(同じ上限)。こちらは**遅刻**
        するので第二。③ それでも置けない分はその便が受け切る(混雑率が上限を超える)。

        ①だけだと 390,067 体の朝ピークで最も早い便に 8 hop 分が山積みになり、実測で
        混雑率 401%(埼京線 08:41 便 6,641 体)まで跳ねた。

        Note:
            逐次ループ宣言(P4): **その線の便数**ぶんのループ 2 本(降順と昇順・日次構築
            1 回)。個体数には比例しない。
        """
        rail = self.rail
        out = train.copy()
        if rail is None or not getattr(rail, "active", False):
            return out
        served = np.flatnonzero(train >= 0)
        if served.size == 0:
            return out
        cap = np.floor(
            np.asarray(rail.capacity100, dtype=np.float64)
            * np.asarray(rail.cap_pct, dtype=np.float64)
            / 100.0
        ).astype(np.int64)
        enter = np.asarray(rail.enter_tick, dtype=np.int64)
        tline = np.asarray(rail.train_line, dtype=np.int64)
        lines = np.unique(tline[train[served]])
        for li in lines.tolist():  # 逐次: 線数(≤8)
            slots = np.flatnonzero(tline == li)
            slots = slots[np.argsort(enter[slots], kind="stable")]
            n_slot = int(slots.size)
            slot_of = np.full(int(tline.size), -1, dtype=np.int64)
            slot_of[slots] = np.arange(n_slot, dtype=np.int64)
            rowsel = served[tline[train[served]] == li]
            if rowsel.size == 0:
                continue
            s_idx = slot_of[train[rowsel]]
            order = np.lexsort((b_agent[rowsel], s_idx))
            rowsel, s_idx = rowsel[order], s_idx[order]
            starts = np.searchsorted(s_idx, np.arange(n_slot + 1), side="left")
            used = np.zeros(n_slot, dtype=np.int64)
            placed: list[list[np.ndarray]] = [[] for _ in range(n_slot)]

            def _take(pool, hops, j):
                """便 ``j`` に残容量ぶんだけ載せ、載らなかった分と hop 数を返す。"""
                room = int(max(0, int(cap[slots[j]]) - int(used[j])))
                keep = np.zeros(pool.size, dtype=bool)
                if room:
                    keep[np.argsort(b_agent[pool], kind="stable")[:room]] = True
                if keep.any():
                    placed[j].append(pool[keep])
                    used[j] += int(np.count_nonzero(keep))
                return pool[~keep], hops[~keep]

            # ---- ① 後ろ向き(早い便へ) ----
            carried = np.empty(0, dtype=np.int64)
            hops = np.empty(0, dtype=np.int64)
            for j in range(n_slot - 1, -1, -1):  # 逐次: その線の便数ぶん
                own = rowsel[starts[j] : starts[j + 1]]
                if own.size == 0 and carried.size == 0:
                    continue
                pool = np.concatenate([carried, own]) if carried.size else own
                hp = (
                    np.concatenate([hops, np.zeros(own.size, dtype=np.int64)])
                    if carried.size else np.zeros(own.size, dtype=np.int64)
                )
                over = hp >= ARRIVAL_SPREAD_MAX_TRAINS
                rest, rest_h = _take(pool[~over], hp[~over], j)
                # hop 上限に達した分は①ではもう動かさない(②で前へ送る)
                carried = np.concatenate([rest, pool[over]])
                hops = np.concatenate([rest_h + 1, hp[over]])
                if j == 0:
                    break
            left, left_h = carried, np.zeros(carried.size, dtype=np.int64)
            # ---- ② 前向き(遅い便へ・①で置けなかった分だけ) ----
            for j in range(0, n_slot):  # 逐次: その線の便数ぶん
                if left.size == 0:
                    break
                over = left_h >= ARRIVAL_SPREAD_MAX_TRAINS
                if over.any():  # 前後どちらにも行き場が無い=この便が受け切る
                    placed[j].append(left[over])
                    used[j] += int(np.count_nonzero(over))
                    self.n_spread_overflow += int(np.count_nonzero(over))
                    left, left_h = left[~over], left_h[~over]
                if left.size == 0:
                    break
                left, left_h = _take(left, left_h, j)
                left_h = left_h + 1
                if j == n_slot - 1 and left.size:  # 最後の便が受け切る
                    placed[j].append(left)
                    used[j] += int(left.size)
                    self.n_spread_overflow += int(left.size)
                    left = np.empty(0, dtype=np.int64)
            for j in range(n_slot):  # 逐次: その線の便数ぶん(書き戻し)
                if placed[j]:
                    rows = np.concatenate(placed[j])
                    self.n_spread_moved += int(
                        np.count_nonzero(out[rows] != slots[j])
                    )
                    out[rows] = slots[j]
        return out

    def _build_events(self) -> None:
        """日次イベント列(§3)を 1 回だけ組む(``lexsort`` のみ・個体比例ループなし)。"""
        blocks = self.blocks
        n = self.n
        b_agent = blocks.agent_of_block
        b_start = blocks.start.astype(np.int64)
        b_end = blocks.end.astype(np.int64)
        # ---- 到着便と到着 tick(E1・E8)----
        train = self._assign_trains(b_agent, b_start)
        train = self._spread_arrivals(train, b_agent)
        rail = self.rail
        if rail is not None and getattr(rail, "active", False) and train.size:
            enter = np.asarray(rail.enter_tick, dtype=np.int64)
            plat = np.asarray(rail.platform_cell, dtype=np.int64)
            arr_tick = np.where(train >= 0, enter[np.maximum(train, 0)], b_start)
            arr_cell = np.where(train >= 0, plat[np.maximum(train, 0)], -1)
        else:
            arr_tick = b_start.copy()
            arr_cell = np.full(b_start.size, -1, dtype=np.int64)
        self.n_gate_arrivals = int(np.count_nonzero(train < 0))
        # 降車セルの分散(§3・W11 出口セルへ round-robin)
        exits = self._exit_cells()
        if exits.size:
            rank = np.arange(b_start.size, dtype=np.int64)
            arr_cell = exits[rank % exits.size]
        prev_end = np.zeros(b_start.size, dtype=np.int64)
        if b_start.size:
            same = np.zeros(b_start.size, dtype=bool)
            same[1:] = b_agent[1:] == b_agent[:-1]
            prev_end[1:] = np.where(same[1:], b_end[:-1], 0)
        # 前のブロックの終了より**前**には戻らない(戻ると DEPART より先に ARRIVE が来て
        # その体が域外へ出たきりになる)。始発前のブロックは**始発まで到着しない**
        # (=遅刻する。E1 の宣言どおり)ので、ここでは開始 tick への切り下げはしない。
        arr_tick = np.maximum(arr_tick, prev_end)
        arr_tick = np.clip(arr_tick, 0, max(0, self.ticks))
        self.arrival_tick = arr_tick
        self.arrival_cell = arr_cell
        self.arrival_train = train

        # tick 0 から在圏の体(= 最初のブロックが 0 分から始まる)
        first = blocks.offset[:-1]
        has = blocks.blocks_per_agent() > 0
        self.in_area_at_start = np.zeros(n, dtype=bool)
        if blocks.n_blocks:
            m = min(n, blocks.n_agents)
            starts0 = np.where(has[:m], b_start[np.minimum(first[:m], blocks.n_blocks - 1)], 1)
            self.in_area_at_start[:m] = has[:m] & (starts0 <= 0)
        # 週次表の行を持たない体(mock 補充分)は触らない=在圏のまま
        self.in_area_at_start |= ~self.managed

        keep_arrive = np.ones(b_start.size, dtype=bool)
        if blocks.n_blocks:
            is_first = np.zeros(b_start.size, dtype=bool)
            is_first[first[has]] = True
            keep_arrive = ~(is_first & (b_start <= 0))
            # 到着がブロックの**終了より後**になるなら、そのブロックには来ない(始発前の
            # 短いブロック。来ないと決めないと DEPART だけが先に流れて状態が壊れる)
            keep_arrive &= arr_tick < b_end

        ev_tick: list[np.ndarray] = []
        ev_agent: list[np.ndarray] = []
        ev_type: list[np.ndarray] = []
        ev_rank: list[np.ndarray] = []
        ev_arg: list[np.ndarray] = []
        ev_act: list[np.ndarray] = []
        ev_place: list[np.ndarray] = []

        def _push(when, who, ty, arg, act=-1, place=-1) -> None:
            """1 種ぶんをまとめて積む。**種は 1 回の ``_push`` で 1 つ**なので、
            同一 tick 内の実行順 ``rank`` は**定数のブロードキャスト**で作れる
            (P4: 件数比例の Python ループを作らない)。
            """
            k = int(np.asarray(when).size)
            if k == 0:
                return
            ev_tick.append(np.asarray(when, dtype=np.int64))
            ev_agent.append(np.asarray(who, dtype=np.int64))
            ev_type.append(np.full(k, int(ty), dtype=np.int64))
            ev_rank.append(np.full(k, _TYPE_ORDER[int(ty)], dtype=np.int64))
            ev_arg.append(np.asarray(arg, dtype=np.int64))
            ev_act.append(
                np.full(k, int(act), dtype=np.int64)
                if np.isscalar(act) else np.asarray(act, dtype=np.int64)
            )
            ev_place.append(
                np.full(k, int(place), dtype=np.int64)
                if np.isscalar(place) else np.asarray(place, dtype=np.int64)
            )

        # ---- 退出(DEPART)を出すブロック ----
        # 域外居住者: ブロックの終了=退出(舞台の外に家がある)。
        # **域内居住者(住民): 次の行が「域外」のときだけ退出**(設計書 §10-7 (a))。
        # 隙間・自宅行・別の在圏行が続くだけなら**舞台に留まる**(層2 指摘・2026-09-11:
        # 旧実装は住民 434 体のうち 263 体を 21 時に域外へ出していた)。
        dep_ok = (b_end < self.ticks) & (keep_arrive | (b_start <= 0))
        if blocks.n_blocks:
            home_in_block = ~self.home_out[np.minimum(b_agent, n - 1)]
            nxt_out = (
                np.asarray(blocks.next_outside, dtype=bool)
                if blocks.next_outside is not None
                else np.ones(b_start.size, dtype=bool)
            )
            dep_ok &= ~home_in_block | nxt_out

        _push(arr_tick[keep_arrive], b_agent[keep_arrive], EventType.ARRIVE,
              arr_cell[keep_arrive], act=blocks.activity[keep_arrive].astype(np.int64))
        _push(b_end[dep_ok], b_agent[dep_ok], EventType.DEPART,
              self.line_of_agent[b_agent[dep_ok]])

        # ---- 就寝・起床(W17 の境界そのもの。D-62 の発火元を層へ移す)----
        # **計画上の活動(``plan_activity``)はこの 2 種 + ARRIVE の時点で更新する**
        # (旧実装は全行ぶんの PLAN_ACTIVITY イベントを別に積んでいた=390k で 1.8M 件・
        # 16 B/件・誰も読まない。行の**被覆は同じ**=非就寝行は WAKE・就寝行は SLEEP)。
        rows, idx, _ = _day_rows(self.weekly, self.day_index)
        if idx.size:
            rt = np.asarray(self.weekly.start_min, dtype=np.int64)[idx]
            ract = np.asarray(self.weekly.activity, dtype=np.int8)[idx]
            rcell = np.asarray(self.weekly.target_cell, dtype=np.int64)[idx]
            rpk = np.asarray(self.weekly.place_kind, dtype=np.int64)[idx]
            live = (
                (rt >= 0) & (rt < self.ticks) & (rows < n)
                & ~self.absent[np.minimum(rows, n - 1)]
            )
            rt, ract, rcell, rpk, rws = rt[live], ract[live], rcell[live], rpk[live], rows[live]
            to_bed = ract == SLEEP_ACTIVITY_CODE
            _push(rt[to_bed], rws[to_bed], EventType.SLEEP, rcell[to_bed],
                  act=SLEEP_ACTIVITY_CODE, place=rpk[to_bed])
            _push(rt[~to_bed], rws[~to_bed], EventType.WAKE,
                  np.full(int((~to_bed).sum()), -1, dtype=np.int64),
                  act=ract[~to_bed].astype(np.int64), place=rpk[~to_bed])

        if ev_tick:
            tick = np.concatenate(ev_tick)
            agent = np.concatenate(ev_agent)
            typ = np.concatenate(ev_type)
            rank = np.concatenate(ev_rank)
            arg = np.concatenate(ev_arg)
            act = np.concatenate(ev_act)
            place = np.concatenate(ev_place)
            order = np.lexsort((agent, rank, tick))
            self.ev_tick = tick[order].astype(np.int32)
            self.ev_agent = agent[order].astype(np.int32)
            self.ev_type = typ[order].astype(np.int8)
            self.ev_arg = arg[order].astype(np.int32)
            self.ev_act = act[order].astype(np.int8)
            self.ev_place = place[order].astype(np.int8)
        else:
            self.ev_tick = np.empty(0, dtype=np.int32)
            self.ev_agent = np.empty(0, dtype=np.int32)
            self.ev_type = np.empty(0, dtype=np.int8)
            self.ev_arg = np.empty(0, dtype=np.int32)
            self.ev_act = np.empty(0, dtype=np.int8)
            self.ev_place = np.empty(0, dtype=np.int8)
        self._ev_start = np.searchsorted(
            self.ev_tick.astype(np.int64), np.arange(self.ticks + 1), side="left"
        )

    # ------------------------------------------------------------------ 起動時の配置
    def initialize(self) -> int:
        """tick 0 に**在圏でない体**を域外へ置く(I1 の分母を立てる)。

        Returns:
            域外へ置いた体数。
        """
        out = np.flatnonzero(~self.in_area_at_start)
        flags = np.zeros(self.n, dtype=np.int64)
        flags |= np.where(self.home_out, FLAG_HOME_OUT, 0)
        has_plan = np.zeros(self.n, dtype=bool)
        m = min(self.n, self.blocks.n_agents)
        has_plan[:m] = self.blocks.blocks_per_agent()[:m] > 0
        flags |= np.where(has_plan, FLAG_HAS_PLAN, 0)
        flags |= np.where(self.in_area_at_start, FLAG_ARRIVED, 0)
        plan_act = np.full(self.n, -1, dtype=np.int64)
        act0 = self._plan_activity_at(0)
        plan_act[: act0.size] = act0
        R.set_plan_state(self.agents, activity=plan_act, flags=flags)
        if out.size:
            ref = self.line_of_agent[out]
            R.place_at_external(self.agents, out, ref)
        # **在圏 ⇒ セルがある**(I6・層2 指摘 2026-09-11): 域外居住(``home_cell < 0``)
        # なのに 0 時から在圏の体は ``resolve.initialize`` が ``cell = node = -1`` のまま
        # 置いている(ARRIVE も出ない=その日ずっと「どこにも居ない在圏」になる)。
        # tick 0 に出口セルへ降ろす(到着の経路は ARRIVE と同じ ``rail_arrive``)。
        r = self.agents.registry
        ghost = np.flatnonzero(
            self.home_out & self.in_area_at_start & (np.asarray(r.cell) < 0)
        )
        self.n_placed_at_start = int(ghost.size)
        if ghost.size:
            exits = self._exit_cells()
            if exits.size:
                cells = exits[np.arange(ghost.size, dtype=np.int64) % exits.size]
                R.rail_arrive(self.agents, self.world, ghost, cells)
                R.set_plan_state(self.agents, ghost, flags_set=FLAG_ARRIVED)
            else:  # 降りる先が 1 つも無い世界=外へ置く(在圏でセル無しは作らない)
                R.place_at_external(self.agents, ghost, self.line_of_agent[ghost])
        self.n_all_day_outside = int(
            np.count_nonzero(self.managed & ~has_plan)
        )
        return int(out.size)

    def _plan_activity_at(self, minute: int) -> np.ndarray:
        """その分の計画上の活動(``ACTIVITY_WORDS`` 索引・-1=隙間)。"""
        return np.asarray(self.weekly.activity_at(self.day_index, int(minute)), dtype=np.int64)

    # ------------------------------------------------------------------ 1 tick
    #: ``step`` が実行するイベント種(在圏の出入り)。世界過程(⓪a)と同じ位置で回す。
    _PRESENCE_TYPES: Final[tuple[int, ...]] = (EventType.DEPART, EventType.ARRIVE)
    #: ``step_plan_boundaries`` が実行する種(計画境界)。**D-62 と同じ位置**で回す
    #: (run.py の「計画境界の起床候補」の所=tick の骨格を動かさない)。
    _BOUNDARY_TYPES: Final[tuple[int, ...]] = (EventType.SLEEP, EventType.WAKE)

    def step(self, tick: int) -> None:
        """在圏の出入り(到着・退出・計画活動)を実行する(§3・§4 の優先規則)。"""
        t = int(tick)
        self._flush_deferred_exits(t)
        extra = self._extra.pop(t, None)
        if extra:
            self._do_arrive(
                np.array([a for a, _ in extra], dtype=np.int64),
                np.array([c for _, c in extra], dtype=np.int64),
            )
        self._run_tick(t, self._PRESENCE_TYPES)

    def step_plan_boundaries(self, tick: int) -> None:
        """計画境界(就寝・起床)を実行する(D-62 の発火元。run.py から層へ移した)。"""
        self._run_tick(int(tick), self._BOUNDARY_TYPES)

    def _run_tick(self, t: int, types: tuple[int, ...]) -> None:
        if not (0 <= t < self.ticks) or self.ev_tick.size == 0:
            return
        lo, hi = int(self._ev_start[t]), int(self._ev_start[t + 1])
        if hi <= lo:
            return
        seg_type = self.ev_type[lo:hi]
        seg_agent = self.ev_agent[lo:hi].astype(np.int64)
        seg_arg = self.ev_arg[lo:hi].astype(np.int64)
        seg_act = self.ev_act[lo:hi].astype(np.int64)
        seg_place = self.ev_place[lo:hi].astype(np.int64)
        for ty in types:  # 逐次ループ宣言: イベント種(≤4)ぶん
            sel = np.flatnonzero(seg_type == ty)
            if sel.size == 0:
                continue
            self._run_type(
                ty, seg_agent[sel], seg_arg[sel], t, seg_act[sel], seg_place[sel]
            )

    def _run_type(
        self, ty: int, ids: np.ndarray, arg: np.ndarray, tick: int,
        act: np.ndarray, place: np.ndarray,
    ) -> None:
        if ty == EventType.DEPART:
            self._do_depart(ids, arg, tick)
        elif ty == EventType.ARRIVE:
            self._do_arrive(ids, arg)
        elif ty == EventType.SLEEP:
            got = R.begin_planned_sleep(
                self.agents, self.world, ids, arg, tick, schedule=self._home_shim
            )
            for k, v in got.items():
                self.sleep_counts[k] = self.sleep_counts.get(k, 0) + int(v)
            r = self.agents.registry
            # **宿泊施設で寝るのは正当**(来街者のホテル泊)なので「職場で寝た」から外す。
            self.n_home_out_slept_inside += int(
                np.count_nonzero(
                    self.home_out[ids]
                    & (place != PLACE_KIND_LODGING)
                    & (np.asarray(r.activity)[ids] == int(Activity.SLEEPING))
                    & (np.asarray(r.transit_state)[ids] == 0)
                )
            )
        elif ty == EventType.WAKE:
            self.sleep_counts["woke"] = self.sleep_counts.get("woke", 0) + R.wake_from_plan(
                self.agents, ids
            )
        # ``plan_activity``(計画上の活動)はイベントの時点で更新する(別のイベント種は持たない)
        upd = np.flatnonzero(act >= 0)
        if upd.size:
            R.set_plan_state(self.agents, ids[upd], activity=act[upd])

    def _do_arrive(self, ids: np.ndarray, cells: np.ndarray) -> None:
        """ARRIVE: **域外に居る体だけ**を降ろす(I2 二重到着なし)。"""
        if ids.size == 0:
            return
        r = self.agents.registry
        ok = (
            (np.asarray(r.transit_state)[ids] == 2)
            & (cells >= 0)
            & (cells < self.world.n_cells)
        )
        self.n_arrive_skipped += int(np.count_nonzero(~ok))
        got = ids[ok]
        if got.size == 0:
            return
        R.rail_arrive(self.agents, self.world, got, cells[ok])
        R.set_plan_state(self.agents, got, flags_set=FLAG_ARRIVED)
        self.n_arrivals += int(got.size)

    def _do_depart(self, ids: np.ndarray, lines: np.ndarray, tick: int) -> None:
        """DEPART: 在圏の体を域外へ(§4 の優先規則: 会話中は繰り延べ・買物/待ちは中断)。"""
        if ids.size == 0:
            return
        # 域外へ出た体(LLM の乗車/退去・civic の押し出し)の**進行中ブロックの DEPART**は落とす
        drop = self._skip_depart_at[ids] == np.int32(tick)
        if drop.any():
            self.n_depart_dropped += int(np.count_nonzero(drop))
            self._skip_depart_at[ids[drop]] = -1
            ids, lines = ids[~drop], lines[~drop]
            if ids.size == 0:
                return
        r = self.agents.registry
        st = np.asarray(r.transit_state)[ids]
        here = st == 0
        self.n_depart_skipped += int(np.count_nonzero(~here))
        ids, lines = ids[here], lines[here]
        if ids.size == 0:
            return
        act = np.asarray(r.activity)[ids]
        talking = act == int(Activity.CONVERSING)
        if talking.any():
            self._defer_ids = np.concatenate([self._defer_ids, ids[talking]])
            self._defer_deadline = np.concatenate(
                [self._defer_deadline, np.full(int(talking.sum()), tick + EXIT_DEFER_LIMIT)]
            )
            self._defer_line = np.concatenate([self._defer_line, lines[talking]])
            R.set_plan_state(self.agents, ids[talking], flags_set=FLAG_EXIT_DEFERRED)
            self.n_exit_deferred += int(talking.sum())
        go, line = ids[~talking], lines[~talking]
        if go.size:
            self._depart_now(go, line, tick)

    def _depart_now(self, ids: np.ndarray, lines: np.ndarray, tick: int) -> None:
        """買物・待ち行列を解いてから ``rail_depart``(§4)。"""
        if ids.size == 0:
            return
        r = self.agents.registry
        shopping = ids[np.asarray(r.poi_ref)[ids] >= 0]
        if shopping.size:
            R.release_indoor(self.agents, shopping)
            self.n_shopping_interrupted += int(shopping.size)
        queued = ids[np.asarray(r.queue_poi)[ids] >= 0]
        if queued.size:
            R.balk_queue(self.agents, queued, int(tick))
            self.n_queue_balked += int(queued.size)
        R.rail_depart(self.agents, ids, lines)
        R.set_plan_state(self.agents, ids, flags_clear=FLAG_EXIT_DEFERRED)
        self.n_departures += int(ids.size)

    def _flush_deferred_exits(self, tick: int) -> None:
        """繰り延べ中の退出を捌く(会話が終わった / 上限 30 tick 超過 / 既に域外)。"""
        if self._defer_ids.size == 0:
            return
        r = self.agents.registry
        ids = self._defer_ids
        st = np.asarray(r.transit_state)[ids]
        act = np.asarray(r.activity)[ids]
        gone = st != 0
        expired = self._defer_deadline <= tick
        ready = (act != int(Activity.CONVERSING)) | expired
        go = ids[ready & ~gone]
        line = self._defer_line[ready & ~gone]
        self.n_exit_forced += int(np.count_nonzero(expired & ~gone & (act == int(Activity.CONVERSING))))
        keep = ~ready & ~gone
        if int(np.count_nonzero(gone)):
            R.set_plan_state(self.agents, ids[gone], flags_clear=FLAG_EXIT_DEFERRED)
        self._defer_ids = ids[keep]
        self._defer_deadline = self._defer_deadline[keep]
        self._defer_line = self._defer_line[keep]
        if go.size:
            self._depart_now(go, line, int(tick))

    # ------------------------------------------------------------------ civic 連携(I4)
    def candidates_for_pull(self, tick: int) -> np.ndarray:
        """**その日在圏予定のある域外の体**(大規模イベントの引き込み候補・I4)。"""
        r = self.agents.registry
        flags = getattr(r, "plan_flags", None)
        outside = np.asarray(r.transit_state) == 2
        if flags is None:
            return np.flatnonzero(outside)
        return np.flatnonzero(outside & ((np.asarray(flags) & FLAG_HAS_PLAN) != 0))

    def notify_pulled_in(self, agent_ids, tick: int) -> None:
        """鉄道を通さず域外から引き込まれた体(``LargeEventProcess._arrive``)。

        古い ARRIVE は ``transit_state == 2`` の体にしか適用されない(I2)ので、印を
        立てるだけで**二重到着は起きない**。
        """
        a = np.asarray(agent_ids, dtype=np.int64).ravel()
        if a.size == 0:
            return
        R.set_plan_state(self.agents, a, flags_set=FLAG_ARRIVED)
        self.n_pulled_in += int(a.size)

    def notify_pushed_out(self, agent_ids, tick: int) -> None:
        """鉄道を通さず域外へ出された体(``LargeEventProcess._leave``)。"""
        a = np.asarray(agent_ids, dtype=np.int64).ravel()
        if a.size == 0:
            return
        self.n_pushed_out += int(a.size)
        self._rearm_after_leaving(a, int(tick))

    def notify_departed_by_llm(self, agent_ids, tick: int) -> None:
        """**LLM が「乗車」/「退去」を選んで域外へ出た**体(設計書 §4「LLM 優先」)。

        呼び手は ``engine.processes.rail.RailProcess.step`` の発車ブロック(=
        ``resolve.rail_depart`` を直に叩く経路)。当日の残り DEPART を落とし、
        **次の**在圏ブロックに ARRIVE を張り直す。
        """
        a = np.asarray(agent_ids, dtype=np.int64).ravel()
        if a.size == 0:
            return
        self.n_departed_by_llm += int(a.size)
        self._rearm_after_leaving(a, int(tick))

    def _rearm_after_leaving(self, a: np.ndarray, t: int) -> None:
        """域外へ出た体の**進行中ブロックの DEPART を落とし・次のブロックに ARRIVE を張る**。

        「次の」= ``start > tick`` の最初のブロック(**進行中のブロックには張らない**——
        張ると押し出された体が翌 tick に戻ってしまう。層2 指摘 2026-09-11: civic の
        退場 200 体のうち 175 体が翌 tick に戻っていた)。次のブロックの到着 tick が
        既に過ぎていれば ``tick+1`` に張り直し、まだ先なら通常のイベントがそのまま出る。

        Note:
            逐次ループ宣言(P4): なし(``searchsorted`` 1 本)。
        """
        blocks = self.blocks
        if blocks.n_blocks == 0 or a.size == 0:
            return
        a = a[a < blocks.n_agents]
        if a.size == 0:
            return
        key = blocks.agent_of_block * (MINUTES_PER_DAY + 1) + blocks.start.astype(np.int64)
        pos = np.searchsorted(key, a * (MINUTES_PER_DAY + 1) + t, side="right")
        lo = blocks.offset[a]
        hi = blocks.offset[a + 1]
        # ① 進行中ブロック(start ≤ tick < end)の DEPART を落とす
        cur = pos - 1
        ok_cur = (cur >= lo) & (cur < hi)
        safe_cur = np.where(ok_cur, cur, 0)
        live_cur = ok_cur & (blocks.end[safe_cur].astype(np.int64) > t)
        if live_cur.any():
            self._skip_depart_at[a[live_cur]] = blocks.end[safe_cur[live_cur]].astype(np.int32)
        # ② **次の**ブロック(start > tick)の到着が過ぎていれば張り直す
        ok_nxt = (pos >= lo) & (pos < hi)
        safe_nxt = np.where(ok_nxt, pos, 0)
        late = ok_nxt & (self.arrival_tick[safe_nxt] <= t)
        rows = np.flatnonzero(late)
        if rows.size:
            # 便に乗り遅れた形なので、**ブロックの開始 tick ちょうど**にゲートから入る
            # (非鉄道ゲート E3 と同じ扱い)。``t+1`` に戻すと押し出された体が翌 tick に
            # 舞台へ帰ってしまう(層2 指摘 2026-09-11: civic の退場 200 中 175 体)。
            when = np.maximum(blocks.start[safe_nxt[rows]].astype(np.int64), t + 1)
            cells = self.arrival_cell[safe_nxt[rows]]
            good = (cells >= 0) & (when < self.ticks)
            for aid, c, w in zip(
                a[rows][good].tolist(), cells[good].tolist(), when[good].tolist()
            ):
                # 逐次ループ宣言: **張り直す体数**ぶん(civic の退場 200 体級・個体比例でない)
                self._extra.setdefault(int(w), []).append((int(aid), int(c)))
                self.n_rearmed += 1

    # ------------------------------------------------------------------ 診断(§5)
    def sample(self, tick: int) -> None:
        """正時の標本(計画一致率 両側・在圏人数)。E9。**run.py が在圏 journal と同じ位置で呼ぶ**。"""
        if int(tick) % 60:
            return
        r = self.agents.registry
        st = np.asarray(r.transit_state)
        in_area = st == 0
        self.sample_hours.append((tick // 60) % 24)
        self.sample_in_area.append(int(np.count_nonzero(in_area)))
        want = self.blocks.in_area_at(tick % MINUTES_PER_DAY)
        m = min(self.n, want.size)
        managed = self.managed[:m]
        w = want[:m] & managed
        o = (~want[:m]) & managed
        self.match_in_den += int(np.count_nonzero(w))
        self.match_in_num += int(np.count_nonzero(w & in_area[:m]))
        self.match_out_den += int(np.count_nonzero(o))
        self.match_out_num += int(np.count_nonzero(o & ~in_area[:m]))
        h = (tick // 60) % 24
        if self.in_area_by_hour[h] != self.in_area_by_hour[h]:  # NaN = その時の初標本
            self.in_area_by_hour[h] = float(np.count_nonzero(in_area))
            n_in = int(np.count_nonzero(in_area))
            awake = int(
                np.count_nonzero(in_area & (np.asarray(r.activity) != int(Activity.SLEEPING)))
            )
            self.wake_in_area_by_hour[h] = (awake / n_in) if n_in else 0.0

    @property
    def plan_match_in(self) -> float:
        """計画一致率(在圏側)= 計画が在圏と言う体のうち実際に在圏だった割合。"""
        return self.match_in_num / self.match_in_den if self.match_in_den else 0.0

    @property
    def plan_match_out(self) -> float:
        """計画一致率(域外側)= 計画が域外と言う体のうち実際に域外/乗車中だった割合。"""
        return self.match_out_num / self.match_out_den if self.match_out_den else 0.0

    @property
    def day_night_ratio(self) -> float:
        """昼夜比 09/03(在圏人数)。どちらかが取れなければ 0.0。"""
        a, b = self.in_area_by_hour[9], self.in_area_by_hour[3]
        if a != a or b != b or b <= 0:
            return 0.0
        return float(a) / float(b)

    def counters(self) -> dict[str, float]:
        return {
            "home_out": float(int(np.count_nonzero(self.home_out))),
            "blocks": float(self.blocks.n_blocks),
            "all_day_outside": float(getattr(self, "n_all_day_outside", 0)),
            "absent": float(int(np.count_nonzero(self.absent))),
            "arrivals": float(self.n_arrivals),
            "departures": float(self.n_departures),
            "arrive_skipped": float(self.n_arrive_skipped),
            "depart_skipped": float(self.n_depart_skipped),
            "exit_deferred": float(self.n_exit_deferred),
            "exit_forced": float(self.n_exit_forced),
            "shopping_interrupted": float(self.n_shopping_interrupted),
            "queue_balked": float(self.n_queue_balked),
            "gate_arrivals": float(self.n_gate_arrivals),
            "spread_moved": float(self.n_spread_moved),
            "spread_overflow": float(self.n_spread_overflow),
            "pulled_in": float(self.n_pulled_in),
            "pushed_out": float(self.n_pushed_out),
            "departed_by_llm": float(self.n_departed_by_llm),
            "depart_dropped": float(self.n_depart_dropped),
            "rearmed": float(self.n_rearmed),
            "placed_at_start": float(self.n_placed_at_start),
            "home_out_slept_inside": float(self.n_home_out_slept_inside),
            "wake_in_area_03": float(self.wake_in_area_by_hour[3]),
            "wake_in_area_09": float(self.wake_in_area_by_hour[9]),
            "wake_in_area_12": float(self.wake_in_area_by_hour[12]),
            "in_area_03": float(self.in_area_by_hour[3]),
            "in_area_09": float(self.in_area_by_hour[9]),
            "in_area_12": float(self.in_area_by_hour[12]),
            "plan_match_in": float(self.plan_match_in),
            "plan_match_out": float(self.plan_match_out),
            "day_night_ratio_09_03": float(self.day_night_ratio),
        }

    def summary(self) -> str:
        """要約 1 行(``c7lib.parse_run_summary`` の正規表現に当たらない書式)。"""
        return (
            f"計画実行: 域外居住 {int(np.count_nonzero(self.home_out)):,}"
            f" / 到着 {self.n_arrivals:,} / 退出 {self.n_departures:,}"
            f" / 終日域外 {int(getattr(self, 'n_all_day_outside', 0)):,}"
            f" / 計画一致率(在圏) {self.plan_match_in:.3f}"
            f" / (域外) {self.plan_match_out:.3f}"
            f" / 昼夜比 09-03 {self.day_night_ratio:.2f}"
        )
