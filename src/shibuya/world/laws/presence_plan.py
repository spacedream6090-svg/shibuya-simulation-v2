"""world.laws.presence_plan — 割る段で ``engine/presence.py`` を割った割り先(全ファイルの表 §4・名の表は
``tools/pkgmove/map.toml`` の割る行)。

中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の
方針は、主な割り先 ``world/laws/presence.py`` に残した元の docstring を読むこと。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final
import numpy as np
from shibuya.world.facts.weekly_reader import (
    ACTIVITY_WORDS,
    MINUTES_PER_DAY,
    N_DAYS,
    PLACE_KIND_OUTSIDE,
    PLACE_WORDS,
)

__all__ = [
    "PlanBlocks",
]


#: 「乗車」の活動語コード(``ACTIVITY_WORDS`` の索引)。
RIDE_ACTIVITY_CODE: Final[int] = ACTIVITY_WORDS.index("乗車")
#: 「自宅」の場所種別コード。
PLACE_KIND_HOME: Final[int] = PLACE_WORDS.index("自宅")
#: 「移動」「支度」の活動語コード(在圏ブロックの読み口 v2 が使う)。
MOVE_ACTIVITY_CODE: Final[int] = ACTIVITY_WORDS.index("移動")
PREP_ACTIVITY_CODE: Final[int] = ACTIVITY_WORDS.index("支度")

#: 在圏ブロックの**読み口**(``derive_rule``・設計書 §2 追補 2026-09-12)。
#: ``"v1"`` = §2 の原則そのまま(域外行・乗車行・域外居住者の自宅行以外は在圏)。
#: ``"v2"`` = W17 v2 の語彙(場所語が域内/域外を持たない)で、域外居住者の**自宅側の行**
#: (乗車の前の「移動 駅」・帰りの乗車の後の「食事 飲食店」など)を在圏に読まない。
#: 域内居住者の読み方は v1 と同一。
#: ``"v2.1"`` = v2 に加えて、域外居住者のランの**先頭/末尾の非滞在行(移動・支度)で乗車行に
#: 隣接しないもの**をブロックから落とす(移動行は「行程全体」と読む=着いた時刻が行の終わり・
#: 発つ時刻が行の始まり)。第170 の計測: 本番 v2 表のブロック 440,971 本のうち先頭が乗車なしの
#: 移動 48.4%(中央値 40 分早く在圏に入る)・末尾が乗車なしの移動 26.3%(40 分遅く出る)。
DERIVE_RULES: Final[tuple[str, ...]] = ("v1", "v2", "v2.1")
DERIVE_RULE_DEFAULT: Final[str] = "v2"
#: 読み口 v2 の「錨」= 舞台に居るとしか読めない行: ``target_cell ≥ 0`` か、場所が
#: 職場/学校/宿泊施設(W16 の勤務先・学校・宿は舞台の中)。
ANCHOR_PLACE_KINDS: Final[tuple[int, ...]] = tuple(
    PLACE_WORDS.index(w) for w in ("職場", "学校", "宿泊施設")
)
#: 読み口 v2 の「滞在」でない活動(乗車・移動・支度)。これだけのランは在圏に採らない。
NON_STAY_ACTIVITY_CODES: Final[tuple[int, ...]] = (
    RIDE_ACTIVITY_CODE, MOVE_ACTIVITY_CODE, PREP_ACTIVITY_CODE,
)
#: 読み口 v2.1 がランの先頭/末尾から落とす活動(移動・支度)。乗車行は v1 の時点で在圏でない。
EDGE_TRIM_ACTIVITY_CODES: Final[tuple[int, ...]] = (MOVE_ACTIVITY_CODE, PREP_ACTIVITY_CODE)

#: 「次の行」を探すときに飛ばせる連続乗車行の上限(逐次ループの上界・expedient)。
_MAX_RIDE_RUN: Final[int] = 8


def _mix64(x: np.ndarray) -> np.ndarray:
    """splitmix64 の最終混合(決定論・ベクトル化・**乱数ではない**)。

    〔11-01 段 2 の 4〕本モジュールの中に呼び手は無い(出勤率 E6 の「その日来ない 12%」を ``agent_id`` だけから
    決めるのに使っていた=くじは消した)。式は ``build.sched.w17_schedule._mix64``・``engine.geometry._mix64``
    と同じで、``tests/engine/test_geometry_c9.py`` と ``tests/engine/test_presence_executor.py`` が本関数を import して
    一致を機械検査するので残している。
    ``core.rng`` の Philox を使わなかったのは**ランの乱数列を 1 語も消費しない**ため
    (T4 規模不変・帰無腕とのバイト一致を保つ)。
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


def _apply_derive_v2(rows, live, home_out, act, pk, cell):
    """読み口 v2(設計書 §2 追補 2026-09-12): 域外居住者の在圏ランを「錨」と「乗車の区切り」で選ぶ。

    入力は (体行, 開始分) 昇順の当日行。``live`` は v1 の在圏行(域外行・乗車行・域外居住者の
    自宅行を除いた行)。**域内居住者の行は変更しない**。ループなし(bincount / cumsum)。

    規則(域外居住者だけ):
      - ラン = ``live`` の連続行。乗車区切り = 「乗車」行または「移動・域外」行の連続 1 つ。
        区間番号 = その行より前(同じ体)に始まった乗車区切りの数(0 = 最初の乗車の前)。
      - 錨 = ``target_cell ≥ 0`` または 場所 ∈ {職場, 学校, 宿泊施設}。
        滞在 = 活動 ∉ {乗車, 移動, 支度}。
      - ランを在圏に採る = 錨を含む、または 滞在を含み**区間番号の偶奇が在圏側**。
        在圏側 = 錨のある体: 最初の錨ランの偶奇 / 乗車区切りの無い体: 全区間 /
        それ以外: 奇数(最初の乗車=行き)。ただし奇数側に滞在ランが無く偶数側にあれば偶数
        (行きの乗車を書かず帰りだけ書いた体の救済)。

    Args:
        rows / live / act / pk / cell: 当日行の体行・v1 在圏・活動・場所・目標セル。
        home_out: ``(n_agents,)`` bool。

    Returns:
        v2 の在圏行 ``(rows.size,)`` bool。
    """
    n_rows = int(rows.size)
    n = int(home_out.size)
    if n_rows == 0:
        return live
    same_prev = np.empty(n_rows, dtype=bool)
    same_prev[0] = False
    same_prev[1:] = rows[1:] == rows[:-1]
    first_of_agent = ~same_prev
    last_of_agent = np.empty(n_rows, dtype=bool)
    last_of_agent[-1] = True
    last_of_agent[:-1] = ~same_prev[1:]
    # ---- 乗車区切りと区間番号 ----
    is_ride = (act == RIDE_ACTIVITY_CODE) | (
        (act == MOVE_ACTIVITY_CODE) & (pk == PLACE_KIND_OUTSIDE)
    )
    prev_ride = np.empty(n_rows, dtype=bool)
    prev_ride[0] = False
    prev_ride[1:] = is_ride[:-1]
    ride_start = is_ride & ~(prev_ride & same_prev)
    g = np.cumsum(ride_start.astype(np.int64))
    base = np.zeros(n, dtype=np.int64)
    base[rows[first_of_agent]] = g[first_of_agent] - ride_start[first_of_agent]
    seg = g - base[rows]
    n_rides = np.zeros(n, dtype=np.int64)
    n_rides[rows[last_of_agent]] = seg[last_of_agent]
    # ---- ラン(v1 在圏の連続行) ----
    prev_live = np.empty(n_rows, dtype=bool)
    prev_live[0] = False
    prev_live[1:] = live[:-1]
    head = live & ~(prev_live & same_prev)
    n_runs = int(np.count_nonzero(head))
    if n_runs == 0:
        return live
    run_id = np.cumsum(head.astype(np.int64)) - 1
    run_agent = rows[head]
    run_seg = seg[head]
    anchor = (cell >= 0) | np.isin(pk, np.asarray(ANCHOR_PLACE_KINDS, dtype=pk.dtype))
    stay = ~np.isin(act, np.asarray(NON_STAY_ACTIVITY_CODES, dtype=act.dtype))
    run_anchor = np.bincount(run_id[live & anchor], minlength=n_runs) > 0
    run_stay = np.bincount(run_id[live & stay], minlength=n_runs) > 0
    # ---- 体ごとの在圏側の偶奇(-1 = 全区間) ----
    parity_in = np.full(n, -1, dtype=np.int64)
    first_anchor_run = np.full(n, n_runs, dtype=np.int64)
    np.minimum.at(first_anchor_run, run_agent[run_anchor], np.flatnonzero(run_anchor))
    has_anchor = first_anchor_run < n_runs
    parity_in[has_anchor] = run_seg[first_anchor_run[has_anchor]] % 2
    odd_stay = np.bincount(run_agent[run_stay & (run_seg % 2 == 1)], minlength=n) > 0
    even_stay = np.bincount(run_agent[run_stay & (run_seg % 2 == 0)], minlength=n) > 0
    rides_only = ~has_anchor & (n_rides > 0)
    parity_in[rides_only] = np.where(odd_stay[rides_only] | ~even_stay[rides_only], 1, 0)
    ra = run_agent
    keep = run_anchor | (run_stay & ((parity_in[ra] < 0) | (run_seg % 2 == parity_in[ra])))
    keep |= ~home_out[ra]  # 域内居住者は v1 のまま
    out = live.copy()
    out[live] = keep[run_id[live]]
    return out


def _trim_nonstay_edges(rows, live, home_out, act, pk):
    """読み口 v2.1: 域外居住者のランの先頭/末尾の非滞在行(移動・支度)で**乗車行に隣接しない**
    ものを落とす。

    入力は (体行, 開始分) 昇順の当日行。``live`` は v2 までを適用した在圏行。
    **域内居住者の行は変更しない**。ループなし(cumsum / bincount)。

    規則(域外居住者だけ):
      - ラン = ``live`` の連続行。先頭側 = ランの頭から続く 移動/支度 の行。末尾側 = ランの尻から
        続く 移動/支度 の行。ランが全部 移動/支度 なら両側が全行。
      - 直前の行(同じ体)が乗車行(「乗車」または「移動・域外」)なら先頭側は残す
        (駅から歩いた=舞台の中)。直後の行が乗車行なら末尾側は残す。それ以外は落とす
        (自宅から舞台までの行程・舞台から自宅までの行程=舞台の外)。
      - 落とした結果ランが空になることがある(移動だけのランで錨(cell≥0)があった場合)。

    Args:
        rows / live / act / pk: 当日行の体行・在圏・活動・場所。
        home_out: ``(n_agents,)`` bool。

    Returns:
        v2.1 の在圏行 ``(rows.size,)`` bool。
    """
    n_rows = int(rows.size)
    if n_rows == 0:
        return live
    same_prev = np.empty(n_rows, dtype=bool)
    same_prev[0] = False
    same_prev[1:] = rows[1:] == rows[:-1]
    same_next = np.empty(n_rows, dtype=bool)
    same_next[-1] = False
    same_next[:-1] = same_prev[1:]
    is_ride = (act == RIDE_ACTIVITY_CODE) | (
        (act == MOVE_ACTIVITY_CODE) & (pk == PLACE_KIND_OUTSIDE)
    )
    prev_ride = np.empty(n_rows, dtype=bool)
    prev_ride[0] = False
    prev_ride[1:] = is_ride[:-1]
    prev_ride &= same_prev
    next_ride = np.empty(n_rows, dtype=bool)
    next_ride[-1] = False
    next_ride[:-1] = is_ride[1:]
    next_ride &= same_next
    # ---- ラン(在圏の連続行)と、ラン内の「滞在行の累積数」 ----
    prev_live = np.empty(n_rows, dtype=bool)
    prev_live[0] = False
    prev_live[1:] = live[:-1]
    head = live & ~(prev_live & same_prev)
    n_runs = int(np.count_nonzero(head))
    if n_runs == 0:
        return live
    run_id = np.cumsum(head.astype(np.int64)) - 1
    next_live = np.empty(n_rows, dtype=bool)
    next_live[-1] = False
    next_live[:-1] = live[1:]
    tail = live & ~(next_live & same_next)
    edge_act = np.isin(act, np.asarray(EDGE_TRIM_ACTIVITY_CODES, dtype=act.dtype))
    stay_row = live & ~edge_act
    c = np.cumsum(stay_row.astype(np.int64))
    rid = np.where(live, run_id, 0)
    c_head = np.zeros(n_runs, dtype=np.int64)
    c_head[run_id[head]] = c[head] - stay_row[head]
    c_rel = np.where(live, c - c_head[rid], 0)
    run_total = np.bincount(run_id[stay_row], minlength=n_runs)
    leading = live & edge_act & (c_rel == 0)
    trailing = live & edge_act & (c_rel == run_total[rid])
    run_prev_ride = np.zeros(n_runs, dtype=bool)
    run_prev_ride[run_id[head]] = prev_ride[head]
    run_next_ride = np.zeros(n_runs, dtype=bool)
    run_next_ride[run_id[tail]] = next_ride[tail]
    drop = (leading & ~run_prev_ride[rid]) | (trailing & ~run_next_ride[rid])
    drop &= home_out[rows]  # 域内居住者は触らない
    out = live.copy()
    out[drop] = False
    return out


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
        ``place_kind ≠ 域外`` ∧ ``活動 ≠ 乗車`` の**連続行**を 1 本に畳む(読み口 v1 の原則)。
        **域外居住者(``home_out``)の「自宅」行は域外**として扱う(=在圏でない)。
        域内居住者の「自宅」行は在圏(舞台の中に家がある。設計書 §2 の ``derive`` の行は
        「``place_kind ∉ {自宅, 域外}``」と書くが、実装は域内居住者の自宅行を在圏に数える)。
        既定の読み口 v2 は、この原則で得たランを ``_apply_derive_v2`` でさらに選ぶ(v2.1 は
        ``_trim_nonstay_edges`` も通す)。
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
    #: 読み口(``DERIVE_RULES``)。v2 = §2 追補(域外居住者の自宅側の行を在圏に読まない)・
    #: v2.1 = v2+乗車に隣接しない先頭/末尾の移動・支度を落とす(``_trim_nonstay_edges``)。
    derive_rule: str = DERIVE_RULE_DEFAULT

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
        derive_rule: str = DERIVE_RULE_DEFAULT,
    ) -> "PlanBlocks":
        """W17 週次表 → 在圏ブロック(§2 の読み口)。

        Args:
            weekly: ``agents.weekly.WeeklySchedule``(ランの体行へ ``restrict_to`` 済み)。
            day: 曜日(0=月曜)。
            home_out: ``(n_agents,)`` の bool。域外居住(``home_cell < 0``)。
            mode: ``"derive"``(現行 W17 を畳む)/ ``"native"``(``block_kind`` 列を読む・**未実装**)。
            count_transit: True なら「乗車」行も在圏に数える(E5 の帰無側)。
            exclude: ``(n_agents,)`` bool。True の体は**ブロック 0 本**にする(旧 E6 出勤率の口。〔11-01 段 2 の 4〕
                ``PlanExecutor`` は ``absent_on``=全員 False を渡す=今は誰も外れない)。
            derive_rule: 読み口(``"v1"`` / ``"v2"`` / ``"v2.1"``・既定 v2・
                ``_apply_derive_v2`` / ``_trim_nonstay_edges``)。

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
        if derive_rule not in DERIVE_RULES:
            raise ValueError(f"derive_rule は {DERIVE_RULES} のどれか(いま {derive_rule!r})")
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
                derive_rule=derive_rule,
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
        if derive_rule in ("v2", "v2.1"):
            live = _apply_derive_v2(rows, live, ho, act, pk, cell)
        if derive_rule == "v2.1":
            live = _trim_nonstay_edges(rows, live, ho, act, pk)

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
            derive_rule=derive_rule,
        )
