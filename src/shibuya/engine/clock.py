"""engine.clock — シミュレーション時計(壁時計に一切依存しない)。

正典
- 運用設計書 §1.2 設定節: ``tick_seconds``・``start_sim_datetime`` は manifest の欄。
- 実装計画書 §3: 「スケジューラ: **1分tick**のバケット配列+tick内は秒オフセット(δ_perc)」。
- 運用設計書 §2.3: δ_perc は**世界時刻を進めない**。同一 tick 内の順序(ナノ秒欄)としてのみ使う。
- CLAUDE.md §3 DT定義: 現実のある時点のスナップショットが舞台=**リアルタイム同期は不要**。

規約
- ``tick`` は ``start_sim_datetime`` からの経過 tick 数(既定 60 秒=1分)。負の tick は
  「開始前」を表す値としては許すが、``due`` などの実行系は 0 以上を前提にする。
- ``t_sim_ns`` は int64 ナノ秒 = ``tick * tick_seconds * 1e9 + offset_ns``。
- 本モジュールは ``datetime.now`` / ``time.time`` を**呼ばない**(決定論の前提)。

逐次ループ宣言(P4): なし。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from shibuya.core.types import (
    DEFAULT_TICK_SECONDS,
    MINUTES_PER_SIM_DAY,
    NS_PER_SECOND,
    split_t_sim_ns,
    t_sim_ns as _t_sim_ns,
)

__all__ = ["SimClock"]


@dataclass(frozen=True)
class SimClock:
    """開始時刻と tick 長だけを持つ不変の時計。

    Attributes:
        start_sim_datetime: シミュレーション開始の**世界内**日時(tz あり/なしのどちらも可・
            manifest の ``settings.start_sim_datetime`` をそのまま入れる)。
        tick_seconds: 1 tick の秒数(既定 60)。
    """

    start_sim_datetime: datetime
    tick_seconds: int = DEFAULT_TICK_SECONDS

    def __post_init__(self) -> None:
        if not isinstance(self.start_sim_datetime, datetime):
            raise TypeError("start_sim_datetime は datetime")
        if int(self.tick_seconds) <= 0:
            raise ValueError("tick_seconds は正の整数")

    # ---- 基本量 ----
    @property
    def tick_ns(self) -> int:
        """1 tick のナノ秒数。"""
        return int(self.tick_seconds) * NS_PER_SECOND

    @property
    def ticks_per_sim_day(self) -> int:
        """1 シミュ日の tick 数(tick_seconds=60 なら 1,440)。"""
        seconds = MINUTES_PER_SIM_DAY * 60
        if seconds % int(self.tick_seconds):
            raise ValueError(f"tick_seconds={self.tick_seconds} は 1 日を割り切らない")
        return seconds // int(self.tick_seconds)

    # ---- 変換 ----
    def to_datetime(self, tick: int, offset_ns: int = 0) -> datetime:
        """tick(+tick 内オフセット)→ 世界内日時。"""
        return self.start_sim_datetime + timedelta(
            seconds=int(tick) * int(self.tick_seconds), microseconds=int(offset_ns) // 1_000
        )

    def to_tick(self, when: datetime) -> int:
        """世界内日時 → tick(切り下げ)。tick 内の端数は捨てる。"""
        return self.to_tick_offset(when)[0]

    def to_tick_offset(self, when: datetime) -> tuple[int, int]:
        """世界内日時 → (tick, tick 内オフセット[ns])。"""
        if (when.tzinfo is None) != (self.start_sim_datetime.tzinfo is None):
            raise ValueError("start_sim_datetime と when の tz 有無が食い違う")
        delta = when - self.start_sim_datetime
        total_ns = (delta.days * 86_400 + delta.seconds) * NS_PER_SECOND + delta.microseconds * 1_000
        return split_t_sim_ns(total_ns, int(self.tick_seconds))

    def t_sim_ns(self, tick: int, offset_s: float = 0.0) -> int:
        """(tick, tick 内オフセット[**秒**]) → t_sim_ns(int64 ナノ秒)。

        δ_perc(0.2〜1.5 秒)を秒で受けてナノ秒欄に変換する入口(運用設計書 §2.3)。
        """
        offset_ns = int(round(float(offset_s) * NS_PER_SECOND))
        return _t_sim_ns(int(tick), offset_ns, int(self.tick_seconds))

    def split(self, t_ns: int) -> tuple[int, int]:
        """t_sim_ns → (tick, offset_ns)。"""
        return split_t_sim_ns(int(t_ns), int(self.tick_seconds))

    def ceil_tick(self, t_ns: int) -> int:
        """t_sim_ns を**次の tick 頭**へ切り上げる(§2.4 の t_apply=分tickへ切り上げ)。"""
        tick, offset = self.split(int(t_ns))
        return tick if offset == 0 else tick + 1
