"""core.time_consts — 時間の定数と、秒と刻みの換算(第 1 期 1-1 時計 T0・TM7・TM8)。

時間の直書き(``1440``・``86400``・``// 60``・``* 60`` など)をこのモジュールの名前に集める。値は T0 の前と同じ
(結果不変=byte-check 19 構成)。直書きが残っていないことは ``tests/engine/time/test_t0_literal_count.py`` が AST で
数える(残すものは ``tests/engine/time/time_literal_allow.json`` に理由つき)。

名前の使い分け(値はどれも T0 の前と同じ。分けるのは、刻みの幅を 60 秒から変えるときに直す場所を grep で拾うため):

- ``MINUTES_PER_HOUR``・``MINUTES_PER_DAY``・``SECONDS_PER_*``・``HOURS_PER_DAY``: 暦の上の時間(刻みの幅に依らない)。
- ``STEP_SECONDS``・``STEPS_PER_HOUR``・``STEPS_PER_DAY``・``NS_PER_STEP``: 1 刻み=60 秒を前提にした数。刻みの数を
  時・日に直す所(「日の中の刻み // 60 = 時」など)はこちらの名前を使う。幅を変える段(T1 以降)では、ここを使う所が
  ランの設定の幅(``RunConfig.tick_seconds``)から計算する形に直す候補になる。

旧い名前(``core.types`` の ``DEFAULT_TICK_SECONDS``・``MINUTES_PER_SIM_DAY``・``SECONDS_PER_MINUTE``・
``NS_PER_SECOND``)は残し、値はこのモジュールから取る(同じ値の別名)。

層契約: 標準ライブラリだけ(shibuya の他のモジュールも NumPy も import しない)。
逐次ループ宣言(P4): なし。
"""

from __future__ import annotations

import operator
from typing import Final

__all__ = [
    "NS_PER_SECOND",
    "SECONDS_PER_MINUTE",
    "MINUTES_PER_HOUR",
    "HOURS_PER_DAY",
    "SECONDS_PER_HOUR",
    "MINUTES_PER_DAY",
    "SECONDS_PER_DAY",
    "STEP_SECONDS",
    "STEPS_PER_HOUR",
    "STEPS_PER_DAY",
    "NS_PER_STEP",
    "CLOCK_KIND",
    "seconds_to_steps",
    "steps_to_seconds",
]

#: 1 秒のナノ秒(世界の時刻 ``t_sim_ns`` はナノ秒の整数=TM7 (a))。
NS_PER_SECOND: Final[int] = 1_000_000_000
#: 1 分の秒。
SECONDS_PER_MINUTE: Final[int] = 60
#: 1 時間の分。
MINUTES_PER_HOUR: Final[int] = 60
#: 1 日の時間。
HOURS_PER_DAY: Final[int] = 24
#: 1 時間の秒(3,600)。
SECONDS_PER_HOUR: Final[int] = SECONDS_PER_MINUTE * MINUTES_PER_HOUR
#: 1 日の分(1,440)。
MINUTES_PER_DAY: Final[int] = MINUTES_PER_HOUR * HOURS_PER_DAY
#: 1 日の秒(86,400)。
SECONDS_PER_DAY: Final[int] = SECONDS_PER_HOUR * HOURS_PER_DAY

#: 1 刻みの秒(既定の幅。ランの設定の欄 ``tick_seconds`` の既定と同じ値=``core.types.DEFAULT_TICK_SECONDS``)。
STEP_SECONDS: Final[int] = 60
#: 1 時間の刻みの数(1 刻み=60 秒のとき 60)。
STEPS_PER_HOUR: Final[int] = SECONDS_PER_HOUR // STEP_SECONDS
#: 1 日の刻みの数(1 刻み=60 秒のとき 1,440=``MINUTES_PER_DAY`` と同じ値)。
STEPS_PER_DAY: Final[int] = SECONDS_PER_DAY // STEP_SECONDS
#: 1 刻みのナノ秒。
NS_PER_STEP: Final[int] = STEP_SECONDS * NS_PER_SECOND

#: 時計の種類(TM9 の欄 ``clock_kind``・manifest と日次の記録)。``"steps"``=全員が同じ幅の刻みで進む今の時計(幅は
#: 欄 ``step_seconds``)。計算のまとめ(T1)・場所ごとの時計(T4)を入れる段で別の値を足す。
CLOCK_KIND: Final[str] = "steps"


def _positive_width(step_seconds: int) -> int:
    w = operator.index(step_seconds)
    if isinstance(step_seconds, bool) or w <= 0:
        raise ValueError(f"刻みの幅(秒)は正の整数: {step_seconds!r}")
    return w


def seconds_to_steps(seconds: int, step_seconds: int = STEP_SECONDS) -> int:
    """秒 → 刻みの数(整数)。

    丸めの規則: **床(``//``)**=その秒を含む刻みの番号。幅で割り切れない秒は切り捨て、負の秒は −∞ 側へ
    (``-1`` 秒 → ``-1`` 刻み)。``rng.run_tick_key`` の 1 日の刻みの数(``86_400 // 幅``)と同じ規則。

    Args:
        seconds: 秒(整数。``float`` は受けない=黙って丸めない)。
        step_seconds: 1 刻みの秒(正の整数。既定 ``STEP_SECONDS``)。

    Raises:
        TypeError: 整数でない値。ValueError: 幅が正でない。

    >>> seconds_to_steps(86_400), seconds_to_steps(119), seconds_to_steps(-1)
    (1440, 1, -1)
    """
    return operator.index(seconds) // _positive_width(step_seconds)


def steps_to_seconds(steps: int, step_seconds: int = STEP_SECONDS) -> int:
    """刻みの数 → 秒(整数・丸め無し=``steps × 幅``)。``seconds_to_steps`` の右逆(``seconds_to_steps(steps_to_seconds(n)) == n``)。

    >>> steps_to_seconds(1440), steps_to_seconds(-1, 30)
    (86400, -30)
    """
    return operator.index(steps) * _positive_width(step_seconds)
