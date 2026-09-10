"""agents.weekly — W17 週次活動表(``w17_schedule.parquet``)の読み込みと計画境界の取り出し。

位置づけ
- **W17(build.sched)が作った資産を、ランが読むだけ**の口(``agents.population`` と同じ形)。
  層契約により ``agents`` は ``build`` を import しない → Parquet を直接読み、
  **語彙定数は二重定義**する(``tests/build_sched/test_weekly_loader.py`` が一致を機械検査)。
- 資産が無ければ ``None`` を返し、呼び出し側は従来の合成日課(``agents.schedule.synthesize``)
  へ落ちる。W17 が入っている世界では、``events_of_day`` の代わりに ``boundary_events`` を
  使うと「1日5境界の固定表」ではなく**個体ごとに本数の違う実際の計画境界**が出る。

データ形(SoA・CSR)
    行は ``(agent_id, day, seq)`` 昇順。``day_offset`` は ``(n_agents*7 + 1,)`` の索引で、
    体 ``r`` の曜日 ``d`` の行は ``day_offset[r*7+d] : day_offset[r*7+d+1]``= **O(1) 参照**。

バイト予算(M1 ≤30KB/体・M3 T0習慣スロット表 ≤12.8KB/体)
    1 活動 = start 2 + end 2 + activity 1 + place 1 + target_cell 4 + seq 2 = **12 B**、
    加えて体あたり ``day_offset`` 8 B × 8 = 64 B。週 7 日 × 平均 6 活動 ≈ 42 活動/体なら
    約 **570 B/体**= M3 の 4.5% (``nbytes``/``bytes_per_agent`` で実測して報告する)。

逐次ループ宣言(P4)
- なし(構築は ``np.searchsorted``/``np.bincount`` のベクトル演算だけ)。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np

from shibuya.agents.state import Activity, WakeCondition
from shibuya.core.hashing import blake3_hex

__all__ = [
    "WEEKLY_FILE",
    "N_DAYS",
    "MINUTES_PER_DAY",
    "ACTIVITY_WORDS",
    "PLACE_WORDS",
    "ACTIVITY_TO_ACTION",
    "ACTIVITY_TO_WAKE",
    "ACTIVITY_TO_STATE",
    "SLEEP_ACTIVITY_CODE",
    "CELL_UNRESOLVED",
    "PLACE_KIND_OUTSIDE",
    "InboundStarts",
    "WeeklySchedule",
    "weekly_available",
    "load_weekly",
    "apply_to_mock_schedule",
]

#: W17 の出力ファイル名(``<world_dir>/w17_schedule.parquet``)。
WEEKLY_FILE: Final[str] = "w17_schedule.parquet"

N_DAYS: Final[int] = 7
MINUTES_PER_DAY: Final[int] = 1_440

# --- 語彙(``build.sched.vocab`` の**二重定義**・テストが一致を機械検査)--------------
ACTIVITY_WORDS: Final[tuple[str, ...]] = (
    "就寝", "支度", "移動", "乗車", "勤務", "通学",
    "食事", "買物", "娯楽", "用事", "交流", "休憩",
)
PLACE_WORDS: Final[tuple[str, ...]] = (
    "自宅", "職場", "学校", "駅", "飲食店", "物販店",
    "公園", "娯楽施設", "宿泊施設", "医療施設", "路上", "域外",
)
#: 活動語 → 行動契約書 §2.1 の行動語(その計画境界で最初に試みる行動)。
ACTIVITY_TO_ACTION: Final[dict[str, str]] = {
    "就寝": "就寝", "支度": "休憩", "移動": "移動", "乗車": "乗車",
    "勤務": "待機", "通学": "待機", "食事": "購入", "買物": "購入",
    "娯楽": "待機", "用事": "待機", "交流": "会話", "休憩": "休憩",
}
#: 活動語コード → 起床条件(知覚契約書 §6 の計画境界 4 行)。
ACTIVITY_TO_WAKE: Final[tuple[int, ...]] = (
    int(WakeCondition.PLAN_SLEEPING),  # 就寝
    int(WakeCondition.PLAN_GENERAL),  # 支度
    int(WakeCondition.PLAN_TRANSIT),  # 移動
    int(WakeCondition.PLAN_TRANSIT),  # 乗車
    int(WakeCondition.PLAN_WORKING),  # 勤務
    int(WakeCondition.PLAN_WORKING),  # 通学
    int(WakeCondition.PLAN_GENERAL),  # 食事
    int(WakeCondition.PLAN_GENERAL),  # 買物
    int(WakeCondition.PLAN_GENERAL),  # 娯楽
    int(WakeCondition.PLAN_GENERAL),  # 用事
    int(WakeCondition.PLAN_GENERAL),  # 交流
    int(WakeCondition.PLAN_GENERAL),  # 休憩
)
#: 「就寝」の活動語コード(``ACTIVITY_WORDS`` の索引 0)。
SLEEP_ACTIVITY_CODE: Final[int] = 0
#: 活動語コード → ``agents.state.Activity``(**D-62 (b)**「tick 0 の活動は計画から立てる」)。
#:
#: expedient(自前の写像・登録簿 §8 D-62)
#: - 「勤務」「通学」に対応する ``Activity`` が無い(在席を表す語は ``SHOPPING`` しかなく、
#:   それは店頭滞在の意味)ので ``IDLE`` に落とす。**在席していないという意味ではない**——
#:   位置は ``target_cell_at`` が別に持つ。
#: - 「乗車」は tick 0 では列車に乗っていない(``transit_state`` は rail の事前割当が正)ので
#:   ``MOVING``(=駅へ向かっている途中)に落とす。``target_node`` は張らない。
#: - 「支度・食事・買物・娯楽・用事・交流」は起きているだけ=``IDLE``、「休憩」は ``RESTING``。
ACTIVITY_TO_STATE: Final[tuple[int, ...]] = (
    int(Activity.SLEEPING),  # 就寝
    int(Activity.IDLE),      # 支度
    int(Activity.MOVING),    # 移動
    int(Activity.MOVING),    # 乗車
    int(Activity.IDLE),      # 勤務
    int(Activity.IDLE),      # 通学
    int(Activity.IDLE),      # 食事
    int(Activity.IDLE),      # 買物
    int(Activity.IDLE),      # 娯楽
    int(Activity.IDLE),      # 用事
    int(Activity.IDLE),      # 交流
    int(Activity.RESTING),   # 休憩
)

#: 場所種別だけが決まっていてセルが未解決(店・駅・公園はランが経路と選好から決める)。
CELL_UNRESOLVED: Final[int] = -1

#: 「域外」の場所種別コード(``PLACE_WORDS`` の索引)。**D-61 追補**の「域内活動」の定義=
#: ``place_kind != PLACE_KIND_OUTSIDE``(下の ``inbound_starts`` 参照)。
PLACE_KIND_OUTSIDE: Final[int] = PLACE_WORDS.index("域外")

_COLUMNS: Final[tuple[str, ...]] = (
    "agent_id", "day", "seq", "start_min", "end_min",
    "activity_code", "place_kind", "target_cell",
)


@dataclass(frozen=True)
class InboundStarts:
    """その日の**域内活動**(``place_kind != 域外``)の開始分を体行ごとに束ねた索引(D-61)。

    鉄道の「帰りの便」(``engine.processes.rail``)が
    「いま域外へ出た体は、次にいつ渋谷に居なければならないか」を引くための形。
    1 日ぶんを 1 回組み、以後は ``next_after`` の ``searchsorted`` 1 本で引く。

    Attributes:
        n_agents: 体行の数(``WeeklySchedule.n_agents``)。
        offset: ``(n_agents+1,)`` の CSR 索引。
        start: 開始分[分](体行ごとに昇順)。
        key: ``体行*(MINUTES_PER_DAY+1) + start``。**全体で昇順**なので、体ごとの
            二分探索を 1 本の ``searchsorted`` で済ませられる(``target_cell_at`` と同じ手)。

    Note:
        逐次ループ宣言(P4): なし。
    """

    n_agents: int
    offset: np.ndarray
    start: np.ndarray
    key: np.ndarray

    @property
    def n_starts(self) -> int:
        return int(self.start.size)

    def next_after(self, rows, minute) -> np.ndarray:
        """体行 ``rows`` の「``minute`` **より後**の最初の域内活動」の開始分(無ければ ``-1``)。

        Args:
            rows: 体行(``(k,)``)。範囲外の行は ``-1`` を返す。
            minute: スカラーか ``(k,)``。0-1440 に丸める。

        Returns:
            ``(k,)`` の ``int64``。``-1`` = その日はもう域内活動が無い。
        """
        r = np.asarray(rows, dtype=np.int64).ravel()
        out = np.full(r.size, -1, dtype=np.int64)
        if r.size == 0 or self.start.size == 0:
            return out
        ok = (r >= 0) & (r < self.n_agents)
        safe = np.where(ok, r, 0)
        m = np.clip(np.asarray(minute, dtype=np.int64), 0, MINUTES_PER_DAY)
        probe = safe * (MINUTES_PER_DAY + 1) + np.where(ok, m, MINUTES_PER_DAY)
        pos = np.searchsorted(self.key, probe, side="right")
        hit = ok & (pos < self.offset[safe + 1])
        out[hit] = self.start[pos[hit]]
        return out


@dataclass(frozen=True)
class WeeklySchedule:
    """週次活動表(行順=``(agent_id, day, seq)`` 昇順)。

    Attributes:
        source: 読み出したファイル(``None``=部分集合・合成)。
        agent_id: 体の ``agent_id``(昇順・重複なし)。索引= **体行**。
        day_offset: ``(n_agents*7+1,)`` の CSR 索引。
        start_min / end_min: 活動の開始・終了[分](0-1440)。
        activity / place_kind: ``ACTIVITY_WORDS`` / ``PLACE_WORDS`` の索引。
        target_cell: 解決済みのセル(自宅/職場/学校)か ``-1``。
        seq: (体, 曜日)内の連番。
    """

    source: Path | None
    agent_id: np.ndarray
    day_offset: np.ndarray
    start_min: np.ndarray
    end_min: np.ndarray
    activity: np.ndarray
    place_kind: np.ndarray
    target_cell: np.ndarray
    seq: np.ndarray

    # ---- 規模・バイト ----
    @property
    def n_agents(self) -> int:
        return int(self.agent_id.size)

    @property
    def n_activities(self) -> int:
        return int(self.start_min.size)

    @property
    def nbytes(self) -> int:
        """実バイト数(予算 M1/M3 に対する実測値)。"""
        return int(
            sum(
                np.asarray(getattr(self, f)).nbytes
                for f in ("agent_id", "day_offset", "start_min", "end_min",
                          "activity", "place_kind", "target_cell", "seq")
            )
        )

    @property
    def bytes_per_agent(self) -> float:
        return self.nbytes / self.n_agents if self.n_agents else 0.0

    def schedule_hash(self) -> str:
        """週次表の同定ハッシュ(状態ハッシュ T1/T2 に混ぜる)。"""
        parts: list[bytes] = [b"shibuya.agents.weekly/v1", str(self.n_agents).encode("ascii")]
        for name in ("agent_id", "day_offset", "start_min", "end_min",
                     "activity", "place_kind", "target_cell"):
            arr = np.ascontiguousarray(getattr(self, name))
            parts.append(name.encode("ascii"))
            parts.append(arr.dtype.str.encode("ascii"))
            parts.append(arr.tobytes())
        return blake3_hex(b"\x1f".join(parts))

    # ---- 参照 ----
    def day_span(self, agent_row: int, day: int) -> tuple[int, int]:
        """体行 ``agent_row`` の曜日 ``day`` の行範囲(O(1))。"""
        k = int(agent_row) * N_DAYS + int(day) % N_DAYS
        return int(self.day_offset[k]), int(self.day_offset[k + 1])

    def activities_of(self, agent_row: int, day: int) -> dict[str, np.ndarray]:
        """1 体 1 日の活動(列辞書)。"""
        lo, hi = self.day_span(agent_row, day)
        return {
            "start_min": self.start_min[lo:hi],
            "end_min": self.end_min[lo:hi],
            "activity": self.activity[lo:hi],
            "place_kind": self.place_kind[lo:hi],
            "target_cell": self.target_cell[lo:hi],
        }

    def _day_bounds(self, day: int) -> tuple[np.ndarray, np.ndarray]:
        d = int(day) % N_DAYS
        n = self.n_agents
        lo = self.day_offset[d::N_DAYS][:n].astype(np.int64)
        hi = self.day_offset[d + 1::N_DAYS][:n].astype(np.int64)
        return lo, hi

    def _day_rows(self, day: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """その曜日の全活動を ``(体行, 全体行索引, 体ごとの件数)`` に展開する(ループなし)。"""
        lo, hi = self._day_bounds(day)
        counts = hi - lo
        total = int(counts.sum())
        if total == 0:
            e = np.empty(0, dtype=np.int64)
            return e, e, counts
        rows = np.repeat(np.arange(self.n_agents, dtype=np.int64), counts)
        base = np.repeat(np.cumsum(counts) - counts, counts)
        idx = np.repeat(lo, counts) + (np.arange(total, dtype=np.int64) - base)
        return rows, idx, counts

    def agent_rows_of_day(self, day: int) -> np.ndarray:
        """その曜日に 1 件でも活動を持つ体行(ループなし)。"""
        lo, hi = self._day_bounds(day)
        return np.flatnonzero(hi > lo)

    def boundary_events(self, day_index: int = 0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """その日の**計画境界**を ``(tick 昇順の体行, 起床条件, tick)`` に平坦化する。

        ``agents.schedule.MockWeeklySchedule.events_of_day`` の**差し替え先**。あちらは
        ``(agent, slot, tick)`` を返して呼び出し側が ``boundary_condition[slot]`` を引くが、
        W17 は体ごとに境界の本数が違うので**条件を直接返す**(= 呼び出し側は
        ``p_cond = b_cond[lo:hi]`` に変わるだけ)。

        Returns:
            ``(agent_row, condition, tick)``。tick=活動の開始分(0-1439)。
        """
        rows, cond, tick, _cell = self.boundary_events_full(day_index)
        return rows, cond, tick

    def boundary_events_full(
        self, day_index: int = 0
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """``boundary_events`` に**その境界で始まる活動の行き先セル**を足した形(D-62)。

        就寝境界(``WakeCondition.PLAN_SLEEPING``)で「どこで寝るか」をエンジンが知るために
        要る(D-62 (a)「就寝は計画の実行」)。``boundary_events`` はこの関数の**薄い包み**なので、
        4 本の並びは常に一致する(並べ替えを二重に書かない)。

        Returns:
            ``(agent_row, condition, tick, target_cell)``。``target_cell`` は
            ``CELL_UNRESOLVED``(-1)= その活動の行き先が未解決(呼び出し側の既定へ落とす)。
        """
        rows, idx, _ = self._day_rows(day_index)
        if idx.size == 0:
            e = np.empty(0, dtype=np.int64)
            return e, np.empty(0, dtype=np.int8), e, np.empty(0, dtype=np.int32)
        tick = self.start_min[idx].astype(np.int64)
        cond = np.asarray(ACTIVITY_TO_WAKE, dtype=np.int8)[self.activity[idx]]
        cell = np.asarray(self.target_cell, dtype=np.int32)[idx]
        order = np.lexsort((rows, tick))
        return rows[order], cond[order], tick[order], cell[order]

    def _row_at(self, day_index: int, minute: int) -> tuple[np.ndarray, np.ndarray]:
        """その時刻に**進行中**の活動の全体行索引と有効印(``(n_agents,)`` を 2 本)。

        (体行, 開始分)の複合キーは昇順なので、体ごとの「開始 ≤ minute」の最後を
        **1 回の二分探索**で引ける(ループなし)。``target_cell_at`` / ``activity_at`` の共通部。
        """
        rows, idx, counts = self._day_rows(day_index)
        if idx.size == 0:
            return (
                np.zeros(self.n_agents, dtype=np.int64),
                np.zeros(self.n_agents, dtype=bool),
            )
        gkey = rows * (MINUTES_PER_DAY + 1) + self.start_min[idx].astype(np.int64)
        probe = np.arange(self.n_agents, dtype=np.int64) * (MINUTES_PER_DAY + 1) + int(minute)
        pos = np.searchsorted(gkey, probe, side="right") - 1
        base = np.cumsum(counts) - counts
        ok = (counts > 0) & (pos >= base)
        pos = np.where(ok, pos, 0)
        sel = idx[pos]
        live = ok & (self.start_min[sel] <= minute) & (self.end_min[sel] > minute)
        return sel, live

    def activity_at(self, day_index: int, minute: int) -> np.ndarray:
        """その時刻に各体が**していること**(``ACTIVITY_WORDS`` の索引・隙間は ``-1``)。

        Returns:
            ``(n_agents,)`` の ``int8``。``-1`` = その分を覆う活動がない(その日に 1 件も
            活動が無い体・活動と活動の隙間)。
        """
        out = np.full(self.n_agents, -1, dtype=np.int8)
        sel, live = self._row_at(day_index, minute)
        if not live.any():
            return out
        out[live] = np.asarray(self.activity, dtype=np.int8)[sel[live]]
        return out

    def initial_activity(
        self, day_index: int = 0, *, fallback: int = int(Activity.SLEEPING)
    ) -> np.ndarray:
        """その日の **0:00 時点**の ``agents.state.Activity``(D-62 (b) tick 0 の初期化)。

        Args:
            day_index: 曜日。
            fallback: 0:00 を覆う活動が無い体に入れる値。既定 ``SLEEPING``=
                **D-62 前の挙動**(``resolve.initialize`` の一括代入)を隙間にだけ残す
                (expedient・登録簿 §8 D-62)。

        Returns:
            ``(n_agents,)`` の ``int8``(``Activity`` の値)。
        """
        code = self.activity_at(day_index, 0)
        out = np.full(self.n_agents, int(fallback), dtype=np.int8)
        live = code >= 0
        if live.any():
            out[live] = np.asarray(ACTIVITY_TO_STATE, dtype=np.int8)[code[live]]
        return out

    def inbound_starts(self, day_index: int = 0) -> InboundStarts:
        """その日の**域内活動**(``place_kind != 域外``)の開始分を CSR に束ねる(D-61)。

        **域内活動の定義 = ``place_kind != PLACE_KIND_OUTSIDE``**(D-61 追補・2026-09-10・
        親判断。**expedient**)。当初の逐語定義は「``target_cell >= 0``(行き先セルが解決)」
        だったが、W17 の**「自宅」活動の 84% が ``target_cell = -1``**(day0 全 1,805,177 活動の
        うち解決済みは 26.9% = 職場・自宅の一部・学校だけ)で、10:00 以降に「次の域内活動」を
        持つ体が 15% しか居らず、決定 (a) の趣旨(住民は戻る)が果たせなかった。
        セルが未解決でも**渋谷の中の活動**(自宅・駅・飲食店・公園…)なら「その時刻に渋谷に
        居なければならない」ことは決まっているので、場所種別だけで判定する。
        **W17 側で自宅セルが解決されれば ``target_cell >= 0`` の条件へ戻せる**(登録簿 §8 D-61)。

        Note:
            逐次ループ宣言(P4): なし(``_day_rows`` + ``lexsort`` + ``bincount``)。
        """
        n = self.n_agents
        rows, idx, _ = self._day_rows(day_index)
        if idx.size:
            keep = np.asarray(self.place_kind)[idx] != PLACE_KIND_OUTSIDE
            rows, idx = rows[keep], idx[keep]
        start = (
            self.start_min[idx].astype(np.int64) if idx.size else np.empty(0, dtype=np.int64)
        )
        offset = np.zeros(n + 1, dtype=np.int64)
        if start.size:
            # W17 の seq 順を当てにせず (体行, 開始分) 昇順へ揃える(key の全体昇順が前提)
            order = np.lexsort((start, rows))
            rows, start = rows[order], start[order]
            np.cumsum(np.bincount(rows, minlength=n)[:n], out=offset[1:])
        else:
            rows = np.empty(0, dtype=np.int64)
        return InboundStarts(
            n_agents=n,
            offset=offset,
            start=start,
            key=rows * (MINUTES_PER_DAY + 1) + start,
        )

    def target_cell_at(self, day_index: int, minute: int, fallback: np.ndarray) -> np.ndarray:
        """その時刻に各体が居るべきセル(``-1`` の活動と隙間は ``fallback``)。

        Args:
            day_index: 曜日。
            minute: 0-1439。
            fallback: 形 ``(n_agents,)`` の既定セル(``Population.start_cell`` など)。
        """
        out = np.asarray(fallback, dtype=np.int32).copy()
        sel, live = self._row_at(day_index, minute)
        if not live.any():
            return out
        cell = self.target_cell[sel]
        take = live & (cell >= 0)
        out[take] = cell[take]
        return out

    def restrict_to(self, agent_ids: np.ndarray) -> "WeeklySchedule":
        """指定 ``agent_id`` の順に並べ替えた部分集合(ランの体行に合わせる)。

        Raises:
            KeyError: 表に無い ``agent_id`` が含まれる。
        """
        want = np.asarray(agent_ids, dtype=np.int64)
        rows = np.searchsorted(self.agent_id, want)
        if rows.size:
            probe = np.clip(rows, 0, max(self.n_agents - 1, 0))
            if self.n_agents == 0 or not np.array_equal(self.agent_id[probe], want):
                raise KeyError("週次表に無い agent_id がある(世界資産と母集団の版が違う)")
        lo = self.day_offset[rows[:, None] * N_DAYS + np.arange(N_DAYS)[None, :]]
        hi = self.day_offset[rows[:, None] * N_DAYS + np.arange(N_DAYS)[None, :] + 1]
        counts = (hi - lo).ravel().astype(np.int64)
        total = int(counts.sum())
        idx = np.repeat(lo.ravel().astype(np.int64), counts) + (
            np.arange(total, dtype=np.int64) - np.repeat(np.cumsum(counts) - counts, counts)
        )
        offset = np.zeros(counts.size + 1, dtype=np.int64)
        np.cumsum(counts, out=offset[1:])
        return WeeklySchedule(
            source=self.source,
            agent_id=want.astype(np.int64),
            day_offset=offset,
            start_min=self.start_min[idx],
            end_min=self.end_min[idx],
            activity=self.activity[idx],
            place_kind=self.place_kind[idx],
            target_cell=self.target_cell[idx],
            seq=self.seq[idx],
        )


def weekly_available(world_dir: str | Path | None) -> bool:
    """``<world_dir>/w17_schedule.parquet`` があるか。"""
    if world_dir is None:
        return False
    return (Path(world_dir) / WEEKLY_FILE).exists()


def load_weekly(world_dir: str | Path | None) -> WeeklySchedule | None:
    """W17 週次表を読む。資産が無ければ ``None``。

    Raises:
        ValueError: 行が ``(agent_id, day, seq)`` 昇順でない(W17 の出力仕様違反)。
    """
    if not weekly_available(world_dir):
        return None
    import pyarrow.parquet as pq  # 遅延 import(週次表が無いランに読み込ませない)

    path = Path(world_dir) / WEEKLY_FILE
    table = pq.read_table(path, columns=list(_COLUMNS))
    cols = {n: np.asarray(table.column(n).to_numpy(zero_copy_only=False)) for n in _COLUMNS}
    aid = cols["agent_id"].astype(np.int64)
    day = cols["day"].astype(np.int64)
    if aid.size and np.any(
        (aid[1:] < aid[:-1]) | ((aid[1:] == aid[:-1]) & (day[1:] < day[:-1]))
    ):
        raise ValueError("w17_schedule.parquet が (agent_id, day) 昇順でない")
    agents = np.unique(aid)
    key = np.searchsorted(agents, aid) * N_DAYS + day
    offset = np.zeros(agents.size * N_DAYS + 1, dtype=np.int64)
    np.cumsum(np.bincount(key, minlength=agents.size * N_DAYS), out=offset[1:])
    return WeeklySchedule(
        source=path,
        agent_id=agents,
        day_offset=offset,
        start_min=cols["start_min"].astype(np.int16),
        end_min=cols["end_min"].astype(np.int16),
        activity=cols["activity_code"].astype(np.int8),
        place_kind=cols["place_kind"].astype(np.int8),
        target_cell=cols["target_cell"].astype(np.int32),
        seq=cols["seq"].astype(np.int16),
    )


def apply_to_mock_schedule(mock, weekly: WeeklySchedule, day_index: int = 0):
    """合成日課(``MockWeeklySchedule``)の拠点セルを W17 の当日の行き先で上書きする。

    **結線用の変換関数**(親が ``engine.run`` へ入れる)。計画境界そのものは
    ``weekly.boundary_events(day)`` を使うのが正で、この関数が埋めるのは
    ``engine.resolve.intents_from_responses`` が読む ``home_cell``/``work_cell`` の 2 本だけ。

    Args:
        mock: ``agents.schedule.MockWeeklySchedule``。
        weekly: ``restrict_to`` でランの体行に揃えた週次表。
        day_index: 曜日。

    Returns:
        置き換え後の ``MockWeeklySchedule``(``dataclasses.replace``)。
    """
    import dataclasses

    n = int(mock.n_agents)
    if weekly.n_agents < n:
        raise ValueError("週次表の体数がランの体数より少ない(restrict_to を先に掛ける)")
    home = np.asarray(mock.home_cell).copy()
    work = np.asarray(mock.work_cell).copy()
    home_at = weekly.target_cell_at(day_index, 0, home)  # 0:00 の居場所=自宅相当
    work_at = weekly.target_cell_at(day_index, 12 * 60, work)  # 正午の行き先
    home[:n] = np.where(home_at[:n] >= 0, home_at[:n], home[:n])
    work[:n] = np.where(work_at[:n] >= 0, work_at[:n], work[:n])
    out = dataclasses.replace(
        mock, home_cell=home.astype(np.int32), work_cell=work.astype(np.int32)
    )
    # ---- D-61 の結線口: 週次表そのものを mock 日課へ**添付**する ----
    # 鉄道過程(``engine.processes.rail.RailProcess``)は ``WorldProcessRunner`` 経由で
    # **この mock オブジェクト**を握っており、``engine.run`` は tick ループの前にこの関数を
    # 1 回呼ぶ。ここで貼っておけば ``run.py`` を書き換えずに週次表が鉄道へ届く
    # (帰りの便=D-61 が「次の域内活動の開始時刻」を引く先)。
    # **入力側にも貼る**のは、``dataclasses.replace`` が新しい実体を返すのに対して
    # runner が握っているのは**置き換え前**の方だから。データクラスの**フィールドではない**ので
    # ``schedule_hash``・バイト予算・``dataclasses.replace`` の等価性には影響しない。
    for obj in (mock, out):
        try:
            object.__setattr__(obj, "weekly", weekly)
        except AttributeError:  # ``__slots__`` を持つ差し替え実装(貼れなくても落とさない)
            pass
    return out
