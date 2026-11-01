# -*- coding: utf-8 -*-
"""slow の試験の時間の門(壁時計の上限)を「記録だけ」にする切替(第333・3-2-4)。

既定は今までどおり ``assert``(落ちる)。環境変数 ``SHIBUYA_TIME_GATES=record`` のときは、門を超えても落とさず
``TimeGateWarning`` と ``print`` で記録だけにする(GitHub の共有の機械は速さが揺れるので、夜の CI-2 で使う)。
門の条件・上限の値・失敗の文言は変えない。

使い方(条件と文言は元の ``assert`` のまま)::

    assert TG.check(worst <= 2.0, "P6 2 ms/tick"), f"P6 超過: {worst:.3f} ms/tick > 2 ms"
"""

from __future__ import annotations

import os
import warnings

ENV = "SHIBUYA_TIME_GATES"


class TimeGateWarning(UserWarning):
    """時間の門を超えた(``SHIBUYA_TIME_GATES=record`` なので落とさず記録だけにした)。"""


def recording() -> bool:
    """``SHIBUYA_TIME_GATES=record`` か。"""
    return os.environ.get(ENV, "").strip().lower() == "record"


def check(ok: bool, what: str) -> bool:
    """時間の門の判定。既定は ``ok`` をそのまま返す(呼び手の ``assert`` が落とす)。

    記録だけのときは結果を 1 行 ``print`` し、超えていれば ``TimeGateWarning`` を出して ``True`` を返す。
    """
    if not recording():
        return bool(ok)
    status = "内" if ok else "超過"
    print(f"[time-gate] {status}(記録だけ・{ENV}=record): {what}")
    if not ok:
        warnings.warn(TimeGateWarning(f"時間の門を超えた(記録だけ・{ENV}=record): {what}"), stacklevel=2)
    return True
