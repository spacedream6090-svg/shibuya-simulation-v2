"""engine.rights.record — 許可のない行動の記録と、役割語の権利の確かめ(第 1 期 1-5・CP3・決定 10-12 §1-4)。

行動を止めるのは物理と、現実でも物理的に止める仕組み(鍵・改札・ATM の認証など機械の決まった動き)だけ。権利に反する
行動は止めず、**行動が起きた所で** 1-3 の出来事の記録に ``行為:許可のない行動``(原因 ``Process("rights")``)として
1 行ずつ書く。気づいた人・持ち主・警察などの事後の反応は後の段(違反を促さない=プロンプトで示唆しない)。

- ``record_unauthorized``: 起きた行為(今は開閉店=開閉の過程が旗を確定した行)を出来事の記録へ書く口。出来事の記録は
  開閉の過程の ActualLog の口(``event_sink`` の ``ActualLogLink``)から引く(``events_of``=新しい参照を持たない)。数え
  は書いた過程の持ち物(開閉の過程の ``n_unauthorized``=状態台帳の O73・diag)。
- ``RoleActCheck``: 判断の応答が役割語(行動契約書 §2.2)だったとき、権利台帳で許可を確かめて判定を返す(副作用なし)。
  役割語は効果の先(C4)がまだ無いので誰が言っても待機/なしに落ちる=**行動は起きていない**ので出来事は書かない
  (検収 L4)。数え(許可なし・判定しない)は判断の口(``LLMBridge``=decide の系の持ち物)が持つ(検収 L10)。

expedient(本モジュール分)
- 役割語の権利の判定: 権限の持ち主が「従業者」の語(接客・補充・開閉店・価格改定)は、体が雇用の行を 1 つでも持てば
  許可あり(対象の店を見ない。対象の解決は役割語の効果と一緒に作る)。乗務員・駅員・指令の語は、権利台帳に職務の行が
  無いので判定しない(``None``)。持ち主が「全員」の語は許可あり。
- 許可のない行動の出来事の欄: ``who``=体・``where``=店の POI・原因=``Process("rights")``。行為の名は出来事の欄に無い
  (語彙表は 1 語)=今は開閉店だけが書く。

逐次ループ宣言: ``record_unauthorized`` は許可のない行為の行ぶん(今の既定では 0 行=記録 r15/README.md §4)。
"""

from __future__ import annotations

from typing import Any, Final

import numpy as np

from shibuya.core.types import t_sim_ns
from shibuya.engine.events import log as _EV
from shibuya.engine.rights.ledger import AGENT, EMPLOY

__all__ = ["WHAT_UNAUTHORIZED", "CAUSE_NAME", "EMPLOYEE_HOLDER", "EVERYONE_HOLDER", "events_of",
           "record_unauthorized", "RoleActCheck", "manifest_fields"]

#: 出来事の語彙表の語(1-5 で足した語)。
WHAT_UNAUTHORIZED: Final[str] = "行為:許可のない行動"
#: 原因の過程の名(``engine.events.vocab.CHECK_PROCESSES``)。
CAUSE_NAME: Final[str] = "rights"
#: 行動契約書 §2.2 の権限の持ち主の語(``llm.contract.ROLE_ACTIONS`` の値)。
EMPLOYEE_HOLDER: Final[str] = "従業者"
EVERYONE_HOLDER: Final[str] = "全員"


def events_of(actual_log: Any) -> Any | None:
    """過程の ActualLog に挿した出来事の記録(``ActualLogLink.log``)。挿していなければ ``None``。"""
    sink = getattr(actual_log, "event_sink", None) if actual_log is not None else None
    return getattr(sink, "log", None)


def record_unauthorized(events: Any | None, agent_ids: Any, poi_ids: Any) -> int:
    """起きた許可のない行為を体ごとに 1 行書く(``events`` が ``None`` なら書かない)。行の数を返す。"""
    a = np.asarray(agent_ids, dtype=np.int64).ravel()
    p = np.asarray(poi_ids, dtype=np.int64).ravel()
    if p.shape != a.shape:
        raise ValueError("agent_ids と poi_ids の長さが違う")
    if a.size and events is not None:
        t = events.now_ns
        cause = _EV.Process(CAUSE_NAME)
        # 逐次ループ: 許可のない行為の行ぶん
        for i in range(a.size):
            events.append(_EV.Event(t_ns=t, who=int(a[i]), what=WHAT_UNAUTHORIZED, where=("poi", int(p[i])),
                                    cause=cause))
    return int(a.size)


class RoleActCheck:
    """役割語の行為の権利を確かめる(判定だけ・書かない)。``LLMBridge`` が役割語のときに呼び、数えは判断の口が持つ。

    Args:
        owner: 権利台帳の持ち主(``rights``・``tick_seconds`` を持つ=開閉の過程)。呼ぶたびに今の ``rights`` を読む
            (再開で作り直した台帳も見える)。
    """

    __slots__ = ("_owner",)

    def __init__(self, owner: Any) -> None:
        self._owner = owner

    def __call__(self, agent_id: int, step: int, word: str) -> bool | None:
        """許可あり=True・許可なし=False・判定しない語(職務・役割語の外)=None。``step`` は通しの刻みの番号。"""
        from shibuya.llm.contract import ROLE_ACTIONS

        holder = str(ROLE_ACTIONS.get(str(word), ""))
        if holder == EVERYONE_HOLDER:
            return True
        if EMPLOYEE_HOLDER not in holder:
            return None
        t = t_sim_ns(int(step), tick_seconds=int(self._owner.tick_seconds))
        return bool(self._owner.rights.holds_any((AGENT, int(agent_id)), EMPLOY, t))


def manifest_fields(runner: Any | None, bridge_counters: Any) -> dict[str, Any] | None:
    """manifest の ``rights``: 実行器の権利台帳の欄に、判断の口の役割語の数え(許可なし・判定しない)を足す。"""
    if runner is None:
        return None
    out = runner.rights_fields()
    c = dict(bridge_counters or {})
    out["unauthorized"] = {**out["unauthorized"],
                           "role_action_unauthorized": int(c.get("role_unauthorized", 0)),
                           "role_action_unjudged": int(c.get("role_unjudged", 0))}
    return out
