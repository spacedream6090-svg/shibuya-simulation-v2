"""〔Q13・第347〕空腹の旧規則 ``v1`` を試験の中だけで選ぶ助け(切替口 ③a の ``tests/engine/space/_legacy.py`` と同じ形)。

Q13 の版上げ(返事その 8 §1-2 Q7 (d)・Q13)で、ランの既定の空腹のモデルは ``energy`` になり、``hunger_model="v1"`` はランの口
(``run_day``・``cli.run`` の引数)から選べなくなった(組み立ての入口 ``world.body.energy.check_hunger_model`` が止める)。
旧規則そのものは残っていて、``world.body.energy`` の非公開の印 ``_HUNGER_V1_FOR_TESTS`` が立っていれば通る。前の既定(空腹 v1)で
録った golden・場面を確かめる試験は、この助けで印を立ててから ``hunger_model="v1"`` を明示して回す。

印は ``monkeypatch`` で立てるので、試験が終われば戻る。子のプロセスには届かない=子のプロセスで回すコードの頭に
:data:`CHILD_PRELUDE` を足す(子のコードそのものの字面は変えない)。旧値の再現は安定版のタグ
``stable-v2-before-library-defaults-q13``。記録 ``docs/bench/analysis/library-defaults-q13-347/README.md``。
"""

from __future__ import annotations

import pytest

from shibuya.world.body import energy as E

#: 子のプロセス(``python -c``)で回すコードの頭に足す 2 行(印を立てる)。
CHILD_PRELUDE: str = "from shibuya.world.body import energy as _E\n_E._HUNGER_V1_FOR_TESTS = True\n"


def hunger_v1(mp: pytest.MonkeyPatch) -> None:
    """空腹の旧規則 v1 を通す印を立てる(``mp`` が戻すまで)。"""
    mp.setattr(E, "_HUNGER_V1_FOR_TESTS", True)
