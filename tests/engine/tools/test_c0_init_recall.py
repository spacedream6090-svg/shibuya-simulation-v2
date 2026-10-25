"""第 1 期 1-7 道具の台帳 C0(検収 L2): 作った後の物に ``__init__`` を呼び直して中身を入れ替えられない。

``ToolRegistry``・``GroupList``・``PhoneTable`` は、名を変えた slot が置かれた後の ``__init__`` を ``RuntimeError`` で止める
(呼び直しの前の中身は残る)。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.engine.tools.groups import GroupList
from shibuya.engine.tools.places import PhoneTable
from shibuya.engine.tools.registry import default_registry


def test_init_cannot_be_called_again():
    reg = default_registry()
    with pytest.raises(RuntimeError, match="呼び直せない"):
        reg.__init__()  # type: ignore[misc]
    assert len(reg) == 9  # 〔第 6 期 6-2〕時計と天気予報を足した(7 → 9)

    g = GroupList(household_id=np.array([0, 0, -1]), org_id=np.array([-1, 1, 1]))
    with pytest.raises(RuntimeError, match="呼び直せない"):
        g.__init__(household_id=np.full(3, -1), org_id=np.full(3, -1))  # type: ignore[misc]
    assert len(g) == 2 and g.members(0).tolist() == [0, 1]

    t = PhoneTable({1: "03"})
    with pytest.raises(RuntimeError, match="呼び直せない"):
        t.__init__({})  # type: ignore[misc]
    assert t.phone_of(1) == "03"

    # 作る口は今までどおり(新しい物は作れる)
    assert len(PhoneTable()) == 0 and len(GroupList.empty(2)) == 0 and len(default_registry()) == 9
