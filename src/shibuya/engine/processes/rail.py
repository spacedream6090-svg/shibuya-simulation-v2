"""engine.processes.rail — 鉄道運行(ODPT 静的ダイヤ・D-R2-5 第1陣の 3 行目)。

正典
- 世界過程設計書 §6 D-R2-5: 「鉄道運行(ODPT 静的ダイヤ=U10 第1陣)」。台帳側の宣言は
  ``world.processes.first_batch._RAIL``(``executor=engine_rule``・conf 0.6・
  返済期限=第2陣で乗務員・指令エージェントへ・contributes=D10/D10′)。
- 境界・経済設計書 §1.3: 「**第1陣**: A+C(方面ノード)を設計どおり実装。鉄道は**静的ダイヤ**
  (ODPT)で到着時刻を作る」。§1.1「域外は方面別の外界ノード…**経済の外界(RoW)は同一実体**」。
- 行動契約書 §2.1: 乗車=「同一セルに停車中・運賃≦残高orIC・定員に空き」/失敗=満員・運賃不足・
  列車なし。降車=「乗車中・当該駅に停車」/失敗=「その駅には止まらない」。
- 運用設計書 **§2.6**(乗車の意味論・混雑率上限型): 「(i)列車の実効容量=定員×混雑率上限
  (国交省の最混雑区間混雑率を線別に採用=mechanism)…(iii)上限到達時のみ『乗り残し』…
  **受容関数の初期値(expedient)**: 混雑率≤150%で受容1.0、150-200%で線形に0.7へ、
  200%超で乗り残し。実効容量=定員×2.0」。
- 世界データ構築仕様書 D-W14: 「ダイヤ=メトロ3線 GTFS+StationTimetable(実・平日/土休)・
  **JR3線・東急2線・京王=等間隔ダイヤ(expedient・F10)**」。

**設計書との食い違い(親へ報告・解決しない)**
1. §2.6 は実効容量を 2 通りに書く: 「(i) 定員×**線別の混雑率上限**」と
   「実効容量=定員×**2.0**(200%=『体が触れ合い圧迫感』の国交省目安)」。
   本実装は **2.0 を乗り残しのハード上限**に、**線別上限を照合対象(D10′)**に使う
   (§2.6 (iv)「混雑率そのものをパターン照合の対象にする」と整合する読み)。
2. 親指示は定員を ``data/realworld/transport_census/line_capacity_12.json`` から取れとするが、
   同ファイルの ``_meta.usage_note`` は「較正(ラン前)と事後検証(ラン後)にのみ使う。
   **シミュ本体(src/)はこのディレクトリを一切読まない**」と宣言している。よって
   ``src`` からは読まず、**§2.6 に逐語で載っている輸送力÷本数**を定数表にした(下記)。
3. 資料3の混雑率は**線別の最混雑区間**であって渋谷断面ではない(§2.6 が自ら「渋谷断面の
   上界として採用」と宣言済み)。山手線の 134%(外回り)/139%(内回り)は
   ``w12_timetables.direction`` の「上り/下り」に写せない(内/外回りの識別欄が無い)ので
   **上界の 139% を線に 1 つ**当てる。

expedient(本モジュール分)
- 停車時間 ``DWELL_TICKS=2``(1 tick では乗って降りる余地が無い。実ダイヤの停車時分は未取得)。
- 運賃 ``FARE_YEN``(運賃表は未取得=空欄)。IC/切符の区別を持たない。
- 定員の空欄(東横線・半蔵門線・銀座線)は車両数からの推定(下表の ``expedient`` 印)。
- 通勤者の「域外に住む割合」``EXTERNAL_HOME_PERMILLE``(mock 日課には方面が無い=C5 の W17 待ち)。
- 到着便の割り当て=「自分の外出時刻以降で最初の当該路線の便」(乗換・所要時間を持たない)。
- 混雑率は**シミュ内の乗客だけ**で測る(域外区間の既存乗客を外生投入しない=第2陣)。
  したがって 5,000 体規模では受容関数は発火せず、乗り残しは 0 になる。

**§2.6 の未実装(親への申し送り・本サブの範囲外)**
    (ii)「混雑率で**内受容**(不快)と**停車時間**が増える」は入れていない。停車時間は定数
    ``DWELL_TICKS=2`` のままで混雑率を見ないし、混雑率を内受容(認知設計書 §2 の 3 変数)へ
    書き戻す口も無い。(iii)「乗り残し」だけを実装し、診断行 ``left_behind`` /
    ``left_behind_rate`` として ``counters()`` に出す(上記のとおり第1陣の規模では 0)。
"""

from __future__ import annotations

from typing import Final

import numpy as np

from shibuya.agents.state import AgentState
from shibuya.core.rng import philox
from shibuya.engine import resolve as R
from shibuya.engine.ledger_api import SECTOR_HOUSEHOLD, SECTOR_ROW
from shibuya.world.assets import ProcessAssets
from shibuya.world.processes.records import DeviationVocab
from shibuya.world.state import World

__all__ = [
    "ACCOUNT_CODE_CARRY_OUT",
    "DWELL_TICKS",
    "FARE_YEN",
    "ACCEPT_FULL_RATIO",
    "ACCEPT_MAX_RATIO",
    "ACCEPT_MIN_RATE",
    "EXTERNAL_HOME_PERMILLE",
    "LINE_CAPACITY_PERSONS",
    "LINE_CONGESTION_CAP_PCT",
    "DEFAULT_CAPACITY_PERSONS",
    "DEFAULT_CONGESTION_CAP_PCT",
    "RNG_DOMAIN",
    "RailProcess",
]

#: 運賃の科目=「持ち出し」(世帯→外界の sink)。**engine は科目名を知らない**ので番号だけを持ち、
#: ``economy.accounts.AccountCode.CARRY_OUT`` と一致することをテストで強制する
#: (``engine.ledger_api`` の ``SECTOR_*`` と同じ流儀)。
#: 鉄道事業者は境界・経済設計書 §2.1 の 6 部門に無く、§1.1 は「経済の外界(RoW)は同一実体」と
#: 宣言しているので、運賃は RoW への持ち出しとして落ちる。
ACCOUNT_CODE_CARRY_OUT: Final[int] = 8

#: 停車時間[tick](expedient)。``dep_tick-1`` から ``dep_tick`` までホームに居る。
DWELL_TICKS: Final[int] = 2

#: 運賃[円](expedient・運賃表は未取得)。
FARE_YEN: Final[int] = 180

#: §2.6 受容関数(expedient): ここまでは受容 1.0。
ACCEPT_FULL_RATIO: Final[float] = 1.50
#: 乗り残しが始まる混雑率(=実効容量 定員×2.0)。
ACCEPT_MAX_RATIO: Final[float] = 2.00
#: ``ACCEPT_MAX_RATIO`` での受容率。
ACCEPT_MIN_RATE: Final[float] = 0.70

#: 域外に住む個体の割合[‰](expedient・mock 日課に方面が無いための代替)。
EXTERNAL_HOME_PERMILLE: Final[int] = 120

#: 乱数ドメイン(域外居住の抽選・カウンタベース=T4 を保つ)。
RNG_DOMAIN: Final[str] = "engine.processes.rail"

#: 線別の 1 列車あたり定員[人]。
#: **mechanism**(運用設計書 §2.6 の逐語値 輸送力 ÷ 本数):
#:   山手線 26,032/16 = 1,627(内回り 32,540/20 も 1,627 で一致)・埼京線 28,040/19 = 1,476・
#:   井の頭線 18,900/27 = 700・田園都市線 40,338/27 = 1,494・副都心線 24,244/18 = 1,347。
#: **expedient**(§2.6 に輸送力の記載が無い線・車両数からの推定):
#:   東横線(8両級)・半蔵門線(田園都市線と 10 両で直通)・銀座線(6両・小型車)。
LINE_CAPACITY_PERSONS: Final[dict[str, int]] = {
    "山手線": 1_627,       # mechanism
    "埼京線": 1_476,       # mechanism
    "井の頭線": 700,       # mechanism
    "田園都市線": 1_494,   # mechanism
    "副都心線": 1_347,     # mechanism
    "東横線": 1_200,       # expedient
    "半蔵門線": 1_494,     # expedient(田園都市線と同編成で直通)
    "銀座線": 640,         # expedient(6両・小型車)
}
#: 線別の混雑率上限[%](国交省 令和6年度 資料2/資料3・§2.6 逐語)。**照合対象=D10′**。
#: 山手線は 134(外回り)/139(内回り)のうち**上界の 139**(方向の識別欄が時刻表に無い)。
LINE_CONGESTION_CAP_PCT: Final[dict[str, float]] = {
    "山手線": 139.0,
    "埼京線": 163.0,
    "井の頭線": 123.0,
    "副都心線": 117.0,
    "半蔵門線": 103.0,
    "銀座線": 147.0,
    "田園都市線": 133.0,
    "東横線": 122.0,
}
#: 表に無い線の既定(東京圏 31 区間平均 139%・§2.6 逐語)。
DEFAULT_CONGESTION_CAP_PCT: Final[float] = 139.0
#: 表に無い線の既定定員(expedient)。
DEFAULT_CAPACITY_PERSONS: Final[int] = 1_200


class RailProcess:
    """静的ダイヤで列車を進め、乗車・降車の前提条件と混雑率受容を持つ世界過程。

    列車は SoA(路線・方向・発車 tick・定員・混雑率上限・乗車人数)。1 日ぶんを起動時に
    展開し、tick では ``searchsorted`` で「停車中の便」を切り出すだけ(逐次ループ無し)。

    Args:
        world / agents: 状態(**読むだけ**。書き込みは ``engine.resolve`` の口)。
        passets: ``world.assets.ProcessAssets``。
        master_seed: 域外居住の抽選 seed。
        day_index: 曜日(0=月曜)。
        schedule: mock 日課(到着便の割り当てに「外出」境界を使う。``None`` 可)。
        actual_log: ``world.processes.actual_log.ActualLog``(``None`` なら記録しない)。
    """

    process_ids: Final[tuple[str, ...]] = ("rail_operation_static",)
    #: 台帳の感度試験 ID(ablation で切るときの名前)。
    ablation_id: Final[str] = "AB-RAIL-EXECUTOR"

    def __init__(
        self,
        world: World,
        agents: AgentState,
        passets: ProcessAssets,
        *,
        master_seed: int | str = 1,
        day_index: int = 0,
        schedule=None,
        actual_log=None,
        fare_yen: int = FARE_YEN,
    ) -> None:
        self.world = world
        self.agents = agents
        self.assets = passets
        self.master_seed = master_seed
        self.day_index = int(day_index)
        self.log = actual_log
        self.fare_yen = int(fare_yen)
        self.n_departures = 0
        self.n_arrivals = 0
        self.n_departed_riders = 0
        self.n_fare_rejected = 0
        #: §2.6 (iii) 乗り残し: **受容関数/詰め込み上限で断られた**乗車希望者の延べ数。
        #: 分母は ``n_board_applicants``(運賃を払えた希望者=受容関数にかかった延べ数)。
        self.n_left_behind = 0
        self.n_board_applicants = 0
        self.lines: tuple[str, ...] = ()
        self.dep_tick = np.empty(0, dtype=np.int64)
        self.train_line = np.empty(0, dtype=np.int64)
        self.train_dir = np.empty(0, dtype=np.int64)
        self.platform_cell = np.empty(0, dtype=np.int64)
        self.capacity100 = np.empty(0, dtype=np.float64)
        self.cap_pct = np.empty(0, dtype=np.float64)
        self.occupancy = np.empty(0, dtype=np.int64)
        self.peak_ratio = np.empty(0, dtype=np.float64)
        self.arrival_train = np.full(agents.n, -1, dtype=np.int64)
        self.external_line = np.full(agents.n, -1, dtype=np.int64)
        self._arr_order = np.empty(0, dtype=np.int64)
        self._arr_start = np.empty(0, dtype=np.int64)
        self._build_trains()
        self._build_external_home(schedule)

    # ------------------------------------------------------------------ 起動時の展開
    @property
    def active(self) -> bool:
        """時刻表とホームのセルが揃っているか(合成世界では False=休む)。"""
        return self.dep_tick.size > 0

    def _build_trains(self) -> None:
        a = self.assets
        if not a.has_timetable or a.line_platform_cell is None:
            return
        calendar = 1 if self.day_index % 7 >= 5 else 0
        sel = np.flatnonzero(np.asarray(a.tt_calendar) == calendar)
        if sel.size == 0:
            return
        line = np.asarray(a.tt_line_idx, dtype=np.int64)[sel]
        cell = np.asarray(a.line_platform_cell, dtype=np.int64)[line]
        keep = cell >= 0  # ホームが bbox のセルに載っている線だけ回す
        sel, line, cell = sel[keep], line[keep], cell[keep]
        if sel.size == 0:
            return
        dep = np.asarray(a.tt_departure_min, dtype=np.int64)[sel]
        direction = np.asarray(a.tt_direction, dtype=np.int64)[sel]
        order = np.lexsort((direction, line, dep))  # 発車 tick 昇順(決定論)
        self.lines = a.tt_lines
        self.dep_tick = dep[order]
        self.train_line = line[order]
        self.train_dir = direction[order]
        self.platform_cell = cell[order]
        cap = np.array(
            [LINE_CAPACITY_PERSONS.get(a.tt_lines[i], DEFAULT_CAPACITY_PERSONS) for i in
             self.train_line],
            dtype=np.float64,
        )
        pct = np.array(
            [LINE_CONGESTION_CAP_PCT.get(a.tt_lines[i], DEFAULT_CONGESTION_CAP_PCT) for i in
             self.train_line],
            dtype=np.float64,
        )
        self.capacity100 = cap
        self.cap_pct = pct
        self.occupancy = np.zeros(self.dep_tick.size, dtype=np.int64)
        self.peak_ratio = np.zeros(self.dep_tick.size, dtype=np.float64)

    def _build_external_home(self, schedule) -> None:
        """域外に住む個体(通勤者)を決定論で選び、到着便を割り当てる。

        Note:
            逐次ループ宣言(P4): **路線数**(≤8)ぶんの ``searchsorted`` 1 本。起動時 1 回。
        """
        n = self.agents.n
        if not self.active or n == 0:
            return
        raw = np.asarray(
            philox(self.master_seed, RNG_DOMAIN, 0).random_raw(3 * n), dtype=np.uint64
        ).reshape(n, 3)
        # T4(規模不変): 生列の先頭 n 語は n+1 体のランでも同じ
        lines_present = np.unique(self.train_line)
        is_ext = (raw[:, 0] % np.uint64(1_000)).astype(np.int64) < EXTERNAL_HOME_PERMILLE
        pick = (raw[:, 1] % np.uint64(max(1, lines_present.size))).astype(np.int64)
        line_of = lines_present[pick]
        if schedule is not None:
            want = np.asarray(schedule.boundary_ticks(self.day_index), dtype=np.int64)[:n, 1]
        else:
            want = 300 + (raw[:, 2] % np.uint64(300)).astype(np.int64)
        train = np.full(n, -1, dtype=np.int64)
        # 逐次ループ宣言: 路線ぶん(≤8)
        for li in lines_present.tolist():
            idx = np.flatnonzero(self.train_line == li)
            if idx.size == 0:
                continue
            here = np.flatnonzero(is_ext & (line_of == li))
            if here.size == 0:
                continue
            pos = np.searchsorted(self.dep_tick[idx], want[here], side="left")
            pos = np.where(pos >= idx.size, 0, pos)  # 終電後は始発へ回す
            train[here] = idx[pos]
        self.arrival_train = train
        self.external_line = np.where(is_ext, line_of, -1)
        served = np.flatnonzero(train >= 0)
        self._arr_order = served[np.argsort(train[served], kind="stable")]
        self._arr_start = np.searchsorted(
            train[self._arr_order], np.arange(self.dep_tick.size + 1), side="left"
        )

    def external_home_agents(self) -> np.ndarray:
        """域外に住む個体(ランの最初に ``resolve.place_at_external`` で外へ置く)。"""
        return np.flatnonzero(self.external_line >= 0)

    # ------------------------------------------------------------------ 停車の判定
    def trains_at_platform(self, tick: int) -> np.ndarray:
        """この tick にホームへ停まっている便(``dep_tick`` が ``tick``..``tick+DWELL-1``)。"""
        if not self.active:
            return np.empty(0, dtype=np.int64)
        lo = int(np.searchsorted(self.dep_tick, int(tick), side="left"))
        hi = int(np.searchsorted(self.dep_tick, int(tick) + DWELL_TICKS - 1, side="right"))
        return np.arange(lo, hi, dtype=np.int64)

    def is_at_platform(self, train_idx, tick: int) -> np.ndarray:
        """便ごとに「いまホームに停まっているか」。"""
        t = np.asarray(train_idx, dtype=np.int64)
        out = np.zeros(t.shape, dtype=bool)
        ok = (t >= 0) & (t < self.dep_tick.size)
        if ok.any():
            d = self.dep_tick[t[ok]]
            out[ok] = (d >= int(tick)) & (d <= int(tick) + DWELL_TICKS - 1)
        return out

    # ------------------------------------------------------------------ §2.6 受容関数
    def congestion_ratio(self, train_idx) -> np.ndarray:
        """混雑率(乗車人数 ÷ 定員)。**照合対象は線別最混雑区間の混雑率**(D10′)。"""
        t = np.asarray(train_idx, dtype=np.int64)
        return self.occupancy[t] / np.maximum(self.capacity100[t], 1.0)

    def accept_rate(self, ratio: float) -> float:
        """§2.6 の受容関数(expedient): ≤150% で 1.0・150-200% で線形に 0.7・200% 超で 0。"""
        if ratio >= ACCEPT_MAX_RATIO:
            return 0.0
        if ratio <= ACCEPT_FULL_RATIO:
            return 1.0
        span = ACCEPT_MAX_RATIO - ACCEPT_FULL_RATIO
        return 1.0 - (1.0 - ACCEPT_MIN_RATE) * (ratio - ACCEPT_FULL_RATIO) / span

    def accept_quota(self, train_idx: int, n_candidates: int) -> int:
        """この tick に受け入れる人数(受容率をその tick の希望者へ一括適用=expedient)。

        §2.6 (iii)「上限到達時のみ『乗り残し』」の**診断行**をここで数える:
        断られた ``n_candidates - quota`` 人が乗り残し(``n_left_behind``)。
        呼び出し元(``resolve._apply_board``)は運賃を払えた希望者だけを渡すので、分母
        ``n_board_applicants`` は「定員裁定にかかった延べ人数」であり運賃不足は含まない。
        """
        t = int(train_idx)
        if t < 0 or t >= self.dep_tick.size or n_candidates <= 0:
            return 0
        ratio = float(self.occupancy[t]) / max(float(self.capacity100[t]), 1.0)
        rate = self.accept_rate(ratio)
        hard = int(np.floor(ACCEPT_MAX_RATIO * self.capacity100[t] - self.occupancy[t]))
        quota = int(max(0, min(n_candidates, int(np.floor(rate * n_candidates)), hard)))
        self.n_board_applicants += int(n_candidates)
        self.n_left_behind += int(n_candidates) - quota
        return quota

    @property
    def left_behind_rate(self) -> float:
        """乗り残し率 = 乗り残し ÷ 定員裁定にかかった希望者(希望者 0 なら 0.0)。"""
        return self.n_left_behind / self.n_board_applicants if self.n_board_applicants else 0.0

    def on_board(self, train_of) -> None:
        """乗車の反映(**列車 SoA は台帳の私物**であり世界状態ではない)。"""
        t = np.asarray(train_of, dtype=np.int64)
        if t.size == 0:
            return
        np.add.at(self.occupancy, t, 1)
        self.peak_ratio[t] = np.maximum(
            self.peak_ratio[t], self.occupancy[t] / np.maximum(self.capacity100[t], 1.0)
        )

    def on_alight(self, train_of) -> None:
        t = np.asarray(train_of, dtype=np.int64)
        if t.size == 0:
            return
        np.add.at(self.occupancy, t, -1)
        np.maximum(self.occupancy, 0, out=self.occupancy)

    def pay_fares(self, money_ledger, riders, fare: int, tick: int) -> np.ndarray:
        """運賃の金の脚(世帯 → 外界・科目「持ち出し」)。行ごとの ``TransferStatus``。"""
        r = np.asarray(riders, dtype=np.int64)
        status = money_ledger.transfer_many(
            SECTOR_HOUSEHOLD,
            r,
            SECTOR_ROW,
            np.zeros(r.size, dtype=np.int64),
            np.full(r.size, int(fare), dtype=np.int64),
            ACCOUNT_CODE_CARRY_OUT,
            int(tick),
        )
        bad = int(np.count_nonzero(np.asarray(status) != 0))
        self.n_fare_rejected += bad
        return np.asarray(status)

    # ------------------------------------------------------------------ 1 tick
    def step(self, tick: int) -> None:
        """到着(域外→bbox)・発車(bbox→域外)・実績記録。"""
        if not self.active:
            return
        t = int(tick)
        # ---- 到着: ホームに入る便(dep_tick-1)に割り当てられた域外居住者を降ろす ----
        entering = np.flatnonzero(self.dep_tick == t + DWELL_TICKS - 1)
        if entering.size and self._arr_order.size:
            picks = [
                self._arr_order[self._arr_start[k] : self._arr_start[k + 1]] for k in entering
            ]
            arriving = np.concatenate(picks) if picks else np.empty(0, dtype=np.int64)
            if arriving.size:
                still_out = arriving[self.agents.registry.transit_state[arriving] == 2]
                if still_out.size:
                    cells = np.asarray(self.platform_cell, dtype=np.int64)[
                        self.arrival_train[still_out]
                    ]
                    R.rail_arrive(self.agents, self.world, still_out, cells)
                    self.n_arrivals += int(still_out.size)
        # ---- 発車: 乗客を方面別の外界ノードへ運び出す ----
        # 実行器は tick の**先頭**で回るので、``dep_tick`` の tick に確定した乗車
        # (Phase C は tick の末尾)を取りこぼさないよう **1 tick 遅らせて**運び出す。
        # ``ActualLog`` の記録時刻は予定どおり ``dep_tick``。
        leaving = np.flatnonzero(self.dep_tick == t - 1)
        if leaving.size:
            state = self.agents.registry.transit_state
            ref = self.agents.registry.transit_ref.astype(np.int64)
            riding = np.flatnonzero(state == 1)
            if riding.size:
                on_leaving = riding[np.isin(ref[riding], leaving)]
                if on_leaving.size:
                    R.rail_depart(
                        self.agents, on_leaving, self.train_line[ref[on_leaving]]
                    )
                    self.n_departed_riders += int(on_leaving.size)
            self.occupancy[leaving] = 0
            self.n_departures += int(leaving.size)
            if self.log is not None:
                self.log.append_many(
                    self.process_ids[0],
                    leaving,
                    self.dep_tick[leaving],  # 予定発車時刻(遅延は第2陣)
                    np.full(leaving.size, 0, dtype=np.int8),  # SCHEDULED
                )
        R.sync_transit_activity(self.agents)

    # ------------------------------------------------------------------ 診断・検算
    def trains_per_line(self) -> dict[str, int]:
        """路線別の 1 日の便数(時刻表の行数と一致すべき=ゲート)。"""
        out: dict[str, int] = {}
        for li, name in enumerate(self.lines):
            n = int(np.count_nonzero(self.train_line == li))
            if n:
                out[name] = n
        return out

    def rider_census(self) -> tuple[int, int, int]:
        """``(bbox 内, 乗車中, 域外滞在)`` の件数。**和 = 個体数**(乗客の保存則)。"""
        s = self.agents.registry.transit_state
        return (
            int(np.count_nonzero(s == 0)),
            int(np.count_nonzero(s == 1)),
            int(np.count_nonzero(s == 2)),
        )

    def counters(self) -> dict[str, float]:
        inb, riding, outside = self.rider_census()
        return {
            "trains": float(self.dep_tick.size),
            "departures": float(self.n_departures),
            "arrivals": float(self.n_arrivals),
            "departed_riders": float(self.n_departed_riders),
            "fare_rejected": float(self.n_fare_rejected),
            "board_applicants": float(self.n_board_applicants),
            "left_behind": float(self.n_left_behind),  # §2.6 (iii)
            "left_behind_rate": float(self.left_behind_rate),
            "external_home_agents": float(int(self.external_home_agents().size)),
            "in_bbox": float(inb),
            "riding": float(riding),
            "at_external": float(outside),
            "peak_congestion_pct": float(self.peak_ratio.max() * 100.0)
            if self.peak_ratio.size
            else 0.0,
        }

    def summary(self) -> str:
        per = self.trains_per_line()
        body = " ".join(f"{k}={v}" for k, v in sorted(per.items()))
        inb, riding, outside = self.rider_census()
        return (
            f"鉄道: 便 {self.dep_tick.size:,} ({body}) / 発車 {self.n_departures:,} "
            f"到着降車 {self.n_arrivals:,} / 在圏 {inb:,} 乗車中 {riding:,} 域外 {outside:,}"
            f" / 乗り残し {self.n_left_behind:,}"
            f"({self.left_behind_rate:.4f}・希望 {self.n_board_applicants:,})"
        )


#: ``ActualLog`` の逸脱語彙(第1陣は遅延を作らないので常に SCHEDULED)。
SCHEDULED: Final[DeviationVocab] = DeviationVocab.SCHEDULED
