"""world.processes.actual_log — **追記専用 ActualLog**(固定幅 numpy レコード+保持窓+増分索引)。

正典
- 世界過程設計書 §2 ``ActualLog``: 「{id, 対象, 逸脱語彙(列挙型・GTFS-RT式), 保持窓, 増分索引}
  ※**追記専用・不変**。**O(t) 成長する唯一の型**なので §3 の宣言を型レベルで強制
  (runB 構造の最有力再発地点)」。
- §3 実装原則2: 「O(t) 成長する状態を持つ場合は、(a)成長宣言+(b)**読み出しが O(定数) である保証**
  (増分計算・索引)の両方が必須。——runB を殺した『未有界コーパス×読者ごと全再走査』の構造的禁止。」
- §6 **D-R2-6**: 「**ActualLog は O(t) が本質→日次で集約行へ畳み・生ログは保持窓 N 日で退避を強制**」。
- §2 PlanSpec「遵守率の観測欄(死んだ規範の検出=歪み宣言の材料)」→ ``compliance_rate``。

本モジュールの構造的保証(runB 再発の禁止)
1. **全再走査をしない**: 過程 → 行位置の索引を追記時に O(1) で伸ばす(``index_for``)。
   読み出しは索引経由の fancy index だけで、生ログ全体を走査しない。
2. **保持窓**: ``evict_expired`` が保持窓を過ぎた日を**日次集約行**(過程×日×逸脱語彙のカウント)
   へ畳み、生ログから落とす。集約後も ``compliance_rate`` は数え落とさない。
3. **成長宣言**: ``growth_declarations()`` が D-R2-6 の 5 欄を返し、``core.growth.check_growth``
   で 24step→30日 外挿の CI ゲートに掛かる。

逐次ループ宣言(P4)
- ``append``: 1呼=1行(定数時間)。``append_many``: numpy のベクトル書き込み+索引の
  ``list.extend`` 1本(件数ぶん・全再走査ではない)。
- ``evict_expired``: **(過程×日)グループ数**ぶんのループ1本(数十)。行数には比例しない
  (行の選別・索引の再配置は numpy のベクトル演算)。1日1回の呼び出しを想定。

expedient(本モジュール分)
- 1行のバイト数 ``RAW_ROW_BYTES`` = 固定幅 dtype(23 B)+ 索引 8 B = **31 B**(見積り)。
- ``ENTRIES_PER_SUBJECT_PER_DAY = 4``(1対象=1便/1配達につき 予定・出発・到着・完了の4記録)は
  実測でなく見積り。第1陣の実測が出たら宣言を delta 改版する。
- cap(512 MB / 16 MB)は予算表 **S1**(恒久記録 ≤5GB/シミュ日)からの割当。予算表に個別行が
  無いので、delta 改版でこの割当を正典化する必要がある(``engine.growth_decl`` と同じ扱い)。
- ``per_day_growth`` を ``O(N)`` と宣言した理由: ``core.growth`` の ``per_day_growth`` は
  **1シミュ日あたりの増分**の位数で、``O(N)`` の D 日後累積は ``coef×N×D``(= 設計書の言う
  「O(t) が本質」)。日次増分が更に時間で伸びる形(``O(N·t)``)ではないので ``O(N)`` が正しい写し。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final, Iterable, Mapping, Sequence

import numpy as np

from shibuya.core.growth import GrowthDeclaration, Retention
from shibuya.world.processes.records import (
    DEVIATION_BY_CODE,
    DEVIATION_CODES,
    ActualLogEntry,
    DeviationVocab,
    PlanSpec,
)
from shibuya.world.processes.relations import Realizes, Relation

__all__ = [
    "ACTUAL_LOG_DTYPE",
    "RAW_ROW_BYTES",
    "AGG_ROW_BYTES",
    "RETENTION_DAYS",
    "TICKS_PER_DAY",
    "ENTRIES_PER_SUBJECT_PER_DAY",
    "ComplianceRate",
    "ActualLog",
    "plan_compliance",
]

#: 固定幅レコード(align=False で 23 B)。**列の順序と型は凍結**(過去ログの読み出し互換)。
ACTUAL_LOG_DTYPE: Final[np.dtype] = np.dtype(
    [
        ("subject_id", "<i8"),
        ("tick", "<i8"),
        ("process", "<i4"),
        ("deviation", "<i1"),
        ("delay_min", "<i2"),
    ],
    align=False,
)

#: 索引1件ぶんのバイト(過程→行位置)。
INDEX_BYTES_PER_ROW: Final[int] = 8
#: 生ログ1行の実効バイト(レコード+索引)。
RAW_ROW_BYTES: Final[int] = ACTUAL_LOG_DTYPE.itemsize + INDEX_BYTES_PER_ROW
#: 日次集約1行(過程×日)のバイト = 逸脱語彙6種のカウント(8B)+ 遅延合計(8B)。
AGG_ROW_BYTES: Final[int] = (len(DEVIATION_CODES) + 1) * 8

#: D-R2-6 の保持窓(生ログ)。
RETENTION_DAYS: Final[int] = 7
#: 1シミュ日の tick 数(1分tick)。
TICKS_PER_DAY: Final[int] = 1_440
#: 1対象あたりの1日の記録件数(見積り=expedient)。
ENTRIES_PER_SUBJECT_PER_DAY: Final[int] = 4

_N_CODES: Final[int] = len(DEVIATION_CODES)
_SCHEDULED_CODE: Final[int] = DEVIATION_CODES[DeviationVocab.SCHEDULED]


@dataclass(frozen=True)
class ComplianceRate:
    """PlanSpec の「遵守率の観測欄」の実測値。

    Attributes:
        process_ids: 対象にした世界過程 id。
        n_total: 分母(窓内の全記録)。
        n_scheduled: 分子(``SCHEDULED`` の件数)。
        rate: ``n_scheduled / n_total``(分母0なら ``float('nan')``)。
        window_ticks: 窓幅(None=全期間)。
        now_tick: 窓の右端。
        from_raw / from_aggregate: 生ログ由来 / 日次集約行由来の件数。
        by_deviation: 逸脱語彙別の件数(死んだ規範の中身を見るため)。
    """

    process_ids: tuple[str, ...]
    n_total: int
    n_scheduled: int
    rate: float
    window_ticks: int | None
    now_tick: int
    from_raw: int
    from_aggregate: int
    by_deviation: Mapping[str, int]

    def as_dict(self) -> dict[str, Any]:
        return {
            "process_ids": list(self.process_ids),
            "n_total": self.n_total,
            "n_scheduled": self.n_scheduled,
            "rate": self.rate,
            "window_ticks": self.window_ticks,
            "now_tick": self.now_tick,
            "from_raw": self.from_raw,
            "from_aggregate": self.from_aggregate,
            "by_deviation": dict(self.by_deviation),
        }


class ActualLog:
    """追記専用の実績ログ(固定幅 numpy + 保持窓 + 増分索引)。

    Args:
        log_id: ``records(ActualLog, …)`` 関係で使う id。
        retention_days: 生ログの保持窓(None=無期限・**D-R2-6 は有限を要求**)。
        ticks_per_day: 1日の tick 数。
        capacity: 初期容量(足りなくなったら倍化)。
    """

    def __init__(
        self,
        log_id: str = "actual_log",
        *,
        retention_days: int | None = RETENTION_DAYS,
        ticks_per_day: int = TICKS_PER_DAY,
        capacity: int = 1024,
    ) -> None:
        if not log_id.strip():
            raise ValueError("log_id は必須")
        if retention_days is not None and int(retention_days) <= 0:
            raise ValueError("retention_days は正か None")
        if int(ticks_per_day) <= 0 or int(capacity) <= 0:
            raise ValueError("ticks_per_day / capacity は正")
        self.log_id = log_id
        self.retention_days = None if retention_days is None else int(retention_days)
        self.ticks_per_day = int(ticks_per_day)
        self._rows = np.zeros(int(capacity), dtype=ACTUAL_LOG_DTYPE)
        self._n = 0
        self._next_entry_id = 0
        self._process_names: list[str] = []
        self._process_codes: dict[str, int] = {}
        #: 過程コード → 生ログの行位置(**増分索引**・読み出しは全再走査しない)。
        self._index: dict[int, list[int]] = {}
        #: (過程コード, 日) → 逸脱語彙別カウント(保持窓を超えた分の畳み先)。
        self._agg: dict[tuple[int, int], np.ndarray] = {}
        #: (過程コード, 日) → 遅延分の合計。
        self._agg_delay: dict[tuple[int, int], int] = {}
        self._max_tick = 0

    # ------------------------------------------------------------------ 基本情報
    def __len__(self) -> int:
        return self._n

    @property
    def n_entries(self) -> int:
        """生ログに残っている行数(集約済みは含まない)。"""
        return self._n

    @property
    def n_appended(self) -> int:
        """これまでに追記した総件数(集約・退避したぶんも含む)。"""
        return self._next_entry_id

    @property
    def process_ids(self) -> tuple[str, ...]:
        return tuple(self._process_names)

    @property
    def max_tick(self) -> int:
        return self._max_tick

    @property
    def nbytes(self) -> int:
        """生ログ+索引+日次集約行の実効バイト(成長宣言の実測に使う)。"""
        idx = sum(len(v) for v in self._index.values()) * INDEX_BYTES_PER_ROW
        return self._n * ACTUAL_LOG_DTYPE.itemsize + idx + len(self._agg) * AGG_ROW_BYTES

    # ------------------------------------------------------------------ 追記
    def _code(self, process_id: str) -> int:
        code = self._process_codes.get(process_id)
        if code is None:
            if not process_id.strip():
                raise ValueError("process_id は必須")
            code = len(self._process_names)
            self._process_names.append(process_id)
            self._process_codes[process_id] = code
            self._index[code] = []
        return code

    def _ensure(self, extra: int) -> None:
        need = self._n + extra
        if need <= self._rows.size:
            return
        cap = max(self._rows.size * 2, need)
        grown = np.zeros(cap, dtype=ACTUAL_LOG_DTYPE)
        grown[: self._n] = self._rows[: self._n]
        self._rows = grown

    def append(
        self,
        process_id: str,
        subject_id: int,
        tick: int,
        deviation: DeviationVocab,
        delay_minutes: int = 0,
    ) -> ActualLogEntry:
        """1行追記する(**不変・上書き不可**)。

        Returns:
            採番済みの ``ActualLogEntry``(値の検査は同クラスが行う)。
        """
        entry = ActualLogEntry(
            entry_id=self._next_entry_id,
            subject_id=int(subject_id),
            process_id=process_id,
            tick=int(tick),
            deviation=deviation,
            delay_minutes=int(delay_minutes),
        )
        code = self._code(process_id)
        self._ensure(1)
        pos = self._n
        self._rows[pos] = (
            entry.subject_id,
            entry.tick,
            code,
            entry.code,
            entry.delay_minutes,
        )
        self._index[code].append(pos)
        self._n += 1
        self._next_entry_id += 1
        self._max_tick = max(self._max_tick, entry.tick)
        return entry

    def append_many(
        self,
        process_id: str,
        subject_ids: Sequence[int] | np.ndarray,
        ticks: Sequence[int] | np.ndarray,
        deviations: Sequence[DeviationVocab] | np.ndarray,
        delay_minutes: Sequence[int] | np.ndarray | None = None,
    ) -> int:
        """同じ過程の複数行をベクトル追記する。

        Args:
            deviations: ``DeviationVocab`` の列、または既に数値コード化した配列。

        Returns:
            追記した件数。

        Raises:
            ValueError: 長さ不一致 / ``DELAY`` 以外に遅延が付いている。
        """
        subj = np.asarray(subject_ids, dtype=np.int64).ravel()
        tk = np.asarray(ticks, dtype=np.int64).ravel()
        if isinstance(deviations, np.ndarray) and deviations.dtype.kind in "iu":
            codes = deviations.astype(np.int8).ravel()
        else:
            codes = np.asarray(
                [DEVIATION_CODES[d] for d in deviations], dtype=np.int8
            ).ravel()
        delays = (
            np.zeros(subj.size, dtype=np.int16)
            if delay_minutes is None
            else np.asarray(delay_minutes, dtype=np.int16).ravel()
        )
        if not (subj.size == tk.size == codes.size == delays.size):
            raise ValueError("append_many: 列の長さが揃っていない")
        if subj.size == 0:
            return 0
        if (subj < 0).any() or (tk < 0).any():
            raise ValueError("append_many: subject_id / tick は 0 以上")
        is_delay = codes == DEVIATION_CODES[DeviationVocab.DELAY]
        if (delays[~is_delay] != 0).any() or (delays[is_delay] == 0).any():
            raise ValueError(
                "append_many: delay_minutes != 0 ⇔ deviation == DELAY(expedient 規約)"
            )
        if ((codes < 0) | (codes >= _N_CODES)).any():
            raise ValueError("append_many: 未知の逸脱コード")

        code = self._code(process_id)
        n = int(subj.size)
        self._ensure(n)
        sl = slice(self._n, self._n + n)
        self._rows["subject_id"][sl] = subj
        self._rows["tick"][sl] = tk
        self._rows["process"][sl] = code
        self._rows["deviation"][sl] = codes
        self._rows["delay_min"][sl] = delays
        self._index[code].extend(range(self._n, self._n + n))
        self._n += n
        self._next_entry_id += n
        self._max_tick = max(self._max_tick, int(tk.max()))
        return n

    # ------------------------------------------------------------------ 読み出し(索引経由)
    def rows(self) -> np.ndarray:
        """生ログの生存行(読み取り専用ビュー)。"""
        view = self._rows[: self._n]
        view.flags.writeable = False
        return view

    def index_for(self, process_id: str) -> np.ndarray:
        """**増分索引**: 過程 → 生ログの行位置(全再走査しない)。"""
        code = self._process_codes.get(process_id)
        if code is None:
            return np.empty(0, dtype=np.int64)
        return np.asarray(self._index[code], dtype=np.int64)

    def rows_for(self, process_id: str) -> np.ndarray:
        """過程1つぶんの生ログ行(索引の fancy index・O(その過程の行数))。"""
        return self._rows[self.index_for(process_id)]

    def entries(self) -> tuple[ActualLogEntry, ...]:
        """生存行を ``ActualLogEntry`` に戻す(テスト・診断用。大きいログには使わない)。"""
        out: list[ActualLogEntry] = []
        for i in range(self._n):
            r = self._rows[i]
            out.append(
                ActualLogEntry(
                    entry_id=i,
                    subject_id=int(r["subject_id"]),
                    process_id=self._process_names[int(r["process"])],
                    tick=int(r["tick"]),
                    deviation=DEVIATION_BY_CODE[int(r["deviation"])],
                    delay_minutes=int(r["delay_min"]),
                )
            )
        return tuple(out)

    # ------------------------------------------------------------------ 保持窓と日次集約
    def daily_counts(self, process_id: str) -> Mapping[int, tuple[int, ...]]:
        """畳み込み済みの日次集約行(日 → 逸脱語彙別カウント)。"""
        code = self._process_codes.get(process_id)
        if code is None:
            return {}
        return {
            day: tuple(int(x) for x in counts)
            for (c, day), counts in sorted(self._agg.items())
            if c == code
        }

    def evict_expired(self, current_tick: int) -> int:
        """保持窓を過ぎた生ログを**日次集約行へ畳んで**落とす(D-R2-6 の強制退避)。

        Args:
            current_tick: 現在 tick。保持するのは
                ``day >= current_day - retention_days + 1`` の行。

        Returns:
            畳んで落とした行数。

        Note:
            逐次ループ宣言(P4): (過程×日)グループ数ぶんのループ1本。行数には比例しない。
        """
        if self.retention_days is None or self._n == 0:
            return 0
        current_day = int(current_tick) // self.ticks_per_day
        cutoff_day = current_day - self.retention_days + 1
        if cutoff_day <= 0:
            return 0
        live = self._rows[: self._n]
        days = live["tick"] // self.ticks_per_day
        drop = days < cutoff_day
        n_drop = int(drop.sum())
        if n_drop == 0:
            return 0

        d_proc = live["process"][drop].astype(np.int64)
        d_day = days[drop].astype(np.int64)
        d_code = live["deviation"][drop].astype(np.int64)
        d_delay = live["delay_min"][drop].astype(np.int64)
        key = d_proc * (1 << 32) + d_day
        uniq, inv = np.unique(key, return_inverse=True)
        for i, k in enumerate(uniq):
            sel = inv == i
            slot = (int(k >> 32), int(k & 0xFFFFFFFF))
            counts = np.bincount(d_code[sel], minlength=_N_CODES).astype(np.int64)
            prev = self._agg.get(slot)
            self._agg[slot] = counts if prev is None else prev + counts
            self._agg_delay[slot] = self._agg_delay.get(slot, 0) + int(d_delay[sel].sum())

        keep = ~drop
        new_pos = np.cumsum(keep) - 1
        kept = live[keep]
        n_keep = int(kept.size)
        self._rows[:n_keep] = kept
        self._rows[n_keep : self._n] = np.zeros(self._n - n_keep, dtype=ACTUAL_LOG_DTYPE)
        self._n = n_keep
        for code, positions in self._index.items():
            if not positions:
                continue
            arr = np.asarray(positions, dtype=np.int64)
            self._index[code] = new_pos[arr[keep[arr]]].tolist()
        return n_drop

    # ------------------------------------------------------------------ 遵守率
    def compliance_rate(
        self,
        process_ids: str | Iterable[str],
        window_ticks: int | None = None,
        *,
        now_tick: int | None = None,
        include_aggregate: bool = True,
    ) -> ComplianceRate:
        """§2「遵守率の観測欄」= 窓内の記録のうち ``SCHEDULED`` の割合。

        Args:
            process_ids: 対象の世界過程 id(1つでも列でも)。
            window_ticks: 窓幅(tick)。None=全期間。
            now_tick: 窓の右端(None ならログ中の最大 tick)。
            include_aggregate: 保持窓を超えて畳まれた日次集約行も数えるか
                (窓が**丸ごと覆っている日**だけ足す)。

        Returns:
            ``ComplianceRate``。分母0なら ``rate`` は NaN(「観測なし」と「遵守0」を混ぜない)。
        """
        ids = (process_ids,) if isinstance(process_ids, str) else tuple(process_ids)
        now = self._max_tick if now_tick is None else int(now_tick)
        start = None if window_ticks is None else now - int(window_ticks) + 1

        counts = np.zeros(_N_CODES, dtype=np.int64)
        from_raw = 0
        for pid in ids:
            rows = self.rows_for(pid)
            if rows.size == 0:
                continue
            tk = rows["tick"]
            sel = (tk <= now) if start is None else ((tk >= start) & (tk <= now))
            if not sel.any():
                continue
            c = np.bincount(rows["deviation"][sel].astype(np.int64), minlength=_N_CODES)
            counts += c.astype(np.int64)
            from_raw += int(sel.sum())

        from_agg = 0
        if include_aggregate and self._agg:
            for pid in ids:
                code = self._process_codes.get(pid)
                if code is None:
                    continue
                for (c_code, day), row in self._agg.items():
                    if c_code != code:
                        continue
                    day_lo = day * self.ticks_per_day
                    day_hi = day_lo + self.ticks_per_day - 1
                    if day_hi > now:
                        continue
                    if start is not None and day_lo < start:
                        continue
                    counts += row
                    from_agg += int(row.sum())

        n_total = int(counts.sum())
        n_sched = int(counts[_SCHEDULED_CODE])
        rate = (n_sched / n_total) if n_total else float("nan")
        by_dev = {
            DEVIATION_BY_CODE[i].value: int(counts[i]) for i in range(_N_CODES) if counts[i]
        }
        return ComplianceRate(
            process_ids=ids,
            n_total=n_total,
            n_scheduled=n_sched,
            rate=rate,
            window_ticks=window_ticks,
            now_tick=now,
            from_raw=from_raw,
            from_aggregate=from_agg,
            by_deviation=by_dev,
        )

    # ------------------------------------------------------------------ 成長宣言(D-R2-6)
    def growth_declarations(
        self,
        *,
        n_processes: int = 64,
        raw_cap_bytes: int = 512 * 1024 * 1024,
        agg_cap_bytes: int = 16 * 1024 * 1024,
    ) -> Mapping[str, GrowthDeclaration]:
        """このログの D-R2-6 宣言(生ログ+日次集約行の2本)。

        Args:
            n_processes: 集約行を持つ過程数の上界(日次集約の増分係数に効く)。
            raw_cap_bytes: 生ログの cap(予算表 S1 からの割当=expedient)。
            agg_cap_bytes: 集約行の cap。
        """
        raw_name = f"{self.log_id}_raw"
        agg_name = f"{self.log_id}_daily"
        raw = GrowthDeclaration(
            name=raw_name,
            per_agent_bytes=0,
            per_cell_bytes=0,
            per_day_growth="O(N)",
            per_day_growth_coef=float(ENTRIES_PER_SUBJECT_PER_DAY * RAW_ROW_BYTES),
            retention=Retention(self.retention_days, f"日次集約行({agg_name})")
            if self.retention_days is not None
            else Retention(None, ""),
            worst_case_ops_per_tick=int(
                max(1, ENTRIES_PER_SUBJECT_PER_DAY * 1000 // max(1, self.ticks_per_day // 60))
            ),
            cap=int(raw_cap_bytes),
            cap_budget_row="S1",
            mechanism=False,
            note=(
                "expedient(感度試験 AB-ACTUALLOG-RETENTION・返済=第1陣の実測が出たら delta 改版)。"
                "D-R2-6「ActualLog は O(t) が本質→日次で集約行へ畳み・生ログは保持窓 N 日で退避」。"
                "per_day_growth は**1日あたり増分**の位数なので O(N)(累積は coef×N×D=O(N·t))。"
                f"1対象1日 {ENTRIES_PER_SUBJECT_PER_DAY} 件・1行 {RAW_ROW_BYTES}B は見積り。"
            ),
            unit="行",
            bytes_per_unit=RAW_ROW_BYTES,
            growth_per_simday=float(ENTRIES_PER_SUBJECT_PER_DAY),
        )
        agg = GrowthDeclaration(
            name=agg_name,
            per_agent_bytes=0,
            per_cell_bytes=0,
            per_day_growth="O(1)",
            per_day_growth_coef=float(n_processes * AGG_ROW_BYTES),
            retention=Retention(None, ""),
            worst_case_ops_per_tick=0,  # 日境界でのみ動く
            cap=int(agg_cap_bytes),
            cap_budget_row="S1",
            mechanism=True,
            note=(
                "畳み先。過程×日の逸脱語彙カウント(6種)+遅延合計。"
                f"1行 {AGG_ROW_BYTES}B × 過程 {n_processes}。"
            ),
            unit="行",
            bytes_per_unit=AGG_ROW_BYTES,
            growth_per_simday=float(n_processes),
        )
        return {raw.name: raw, agg.name: agg}


def plan_compliance(
    log: ActualLog,
    plan_spec: PlanSpec,
    relations: Iterable[Relation],
    window_ticks: int | None = None,
    *,
    now_tick: int | None = None,
) -> ComplianceRate:
    """PlanSpec の遵守率(``realizes`` 関係で結ばれた世界過程の記録から計算)。

    §2「遵守率の観測欄(死んだ規範の検出=歪み宣言の材料)」の計算口。

    Args:
        log: 実績ログ。
        plan_spec: 対象の計画仕様。
        relations: 台帳の関係(``realizes`` だけを見る)。
        window_ticks: 窓幅(tick)。
        now_tick: 窓の右端。

    Raises:
        ValueError: その PlanSpec を実現する ``realizes`` 関係が1本も無い
            (=遵守率を測る相手がいない)。
    """
    subjects = tuple(
        sorted(
            {
                r.subject_id
                for r in relations
                if isinstance(r, Realizes) and r.plan_spec_id == plan_spec.id
            }
        )
    )
    if not subjects:
        raise ValueError(
            f"{plan_spec.id}: realizes 関係が無く遵守率を測れない"
            "(§2 の遵守率観測欄は ActualLog との一致率)"
        )
    return log.compliance_rate(subjects, window_ticks, now_tick=now_tick)
