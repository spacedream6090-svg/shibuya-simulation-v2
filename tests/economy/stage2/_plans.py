"""経済の段階 2 の試験の代役の組み立ての物(試験の中だけの共有の助け)。

〔第347・検収 F-4〕前は ``tests/economy/stage2/test_stage2_money_rules.py`` の非公開の ``_plan`` を、``tests/engine/test_ledger_wiring.py``
が別の試験のモジュールから import していた。共有の助けに移し、両方がここを読む。

本物の ``economy.stage2_bind.Stage2Plan`` と違う所(代役): 規則の表の材料 ``law`` が無い・ATM の表が無い(``atms=None``)・給料日が
来ない(``is_payday`` は偽)・雇用の行が空・日付は 2026-08-24 に固定。体の種別は ``kinds`` で渡す(既定は 4 種=通勤者・来街者・
居住者・訪日来街者)。
"""

from __future__ import annotations

import datetime as dt
import types

import numpy as np

from shibuya.economy import stage2 as S2
from shibuya.foundation.journal import log as EV

#: 既定の体の種別(通勤者・来街者・居住者・訪日来街者)。
KINDS_4 = np.array([0, 1, 3, 7])


def stage2_plan(parts=S2.PARTS, kinds=KINDS_4) -> types.SimpleNamespace:  # noqa: ANN001
    """段階 2 の代役の組み立ての物(``Ledger.attach_stage2`` に渡す)。"""
    cal_day = dt.date(2026, 8, 24)
    return types.SimpleNamespace(
        parts=tuple(parts), kinds=kinds, monthly_hours=None, hours_source="default", atms=None,
        cause=lambda name: EV.Process(name), date_of_step=lambda step: cal_day, date_of=lambda day: cal_day,
        is_payday=lambda day: False, close_step=lambda day: 1439, employment=lambda day: (np.zeros(0),) * 3,
        record=lambda: {},
    )
