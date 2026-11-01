"""engine.tools.record — 道具の記録の欄(CT9)と、ランの道具の一式・manifest の ``tools``(第 1 期 1-7 C0)。

決定 10-12 §4-4 CT9 (b)(記録に道具の欄と届いた/読んだ時刻・範囲の外から来た情報に出どころの印)・CT0(今ある看板の文は
現実のデータに置き換わるまでのつなぎとして「作り物」の印を付けて残す)・共通の決まり 5(使用は全部、出来事の記録へ残す)・
口の約束 1-7 の約束 (3)(看板の作り物の印は描画のバイトを変えない=印は記録にだけ)。

- 記録の欄は 1-3 の ``Event.via``・``received_ns``/``read_ns``・``origin`` を使う(新しい欄は足さない)。
- **看板を読んだ出来事**(``SignboardReadLink``): 判断の系(decide)が描いた知覚の事実(``Percept``)のうち、見えた物に看板
  (``seen_objects`` の種類 ``signage``=注視のゲートを通って B2 に看板の行が載った)がある体ごとに 1 行。``who``=体・
  ``what``=``道具:看板``・``where``=看板の POI・``via``=``無し``(CT9 の 5 つの道具の外)・``received_ns``=``read_ns``=
  ``t_ns``(その刻みの頭)・``origin``=``signboard:synthetic``(作り物の印=つなぎの台帳 ``BR-SIGNAGE-FICTION``)・
  ``cause``=``Process("perception")``(知覚=System 1)。描画の後に知覚の事実を読むだけ=描画・判断・テープは変わらない。
- 腕(切替口): **既定 off**(``SHIBUYA_TOOL_EVENTS=on``・``set_enabled(True)`` で書く)。組み立ての時に読む。既定で書くと
  manifest の日次の記録 ``events`` の行数と分布(既存の欄)が動くため、C0 では腕にした(仮採用・記録 c0/README.md)。記録は
  結果を変えないので設定の指紋には入れない(出来事の記録の切替口 ``SHIBUYA_EVENTS`` と同じ扱い)。
- ``ToolsFixture``: ランの道具の一式(台帳・グループの一覧・店の番号の表・看板の口)。組み立てで作り、ランの間は読むだけ
  (箱 ``Fixtures.tools``=状態台帳の対象外)。
- ``manifest_fields``: manifest の ``tools``(道具の数・グループの数・連絡先の印の数・店の番号の表の行・看板の印)。

先例(R-113 §3・§8): AgentSociety 2 の道具の呼び出しの記録(``env/base.py``・Apache-2.0=全呼び出しを記録の列に足す形)・
Concordia の ``Event.source="__external__"``(外から来た出来事の印)。形だけ借りた(コードは写していない)。

**未リサーチ(expedient)**: 看板を読んだ出来事の語(``道具:看板``)・原因の名(``perception``)・``via`` を ``無し`` にしたこと・
1 体 1 刻み 1 行(同じ体が同じ看板を続けて読んでも毎回 1 行)。

逐次ループ宣言: ``SignboardReadLink.__call__`` はその刻みに描いた体の数ぶん(選ばれた呼の数=平均 35/刻み・腕のランだけ)。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Final, Mapping

from shibuya.engine.events import vocab as V
from shibuya.engine.events.log import Event, EventLog, Process
from shibuya.engine.tools.groups import GroupList
from shibuya.engine.tools.places import PhoneTable
from shibuya.engine.tools.registry import SIGNAGE_BRIDGE, SIGNBOARD, ToolRegistry, default_registry

__all__ = [
    "SIGNBOARD_ORIGIN", "SIGNBOARD_WHAT", "SIGNBOARD_CAUSE", "MANIFEST_SCHEMA", "ARM_ENV", "arm_from_env", "enabled",
    "set_enabled",
    "SignboardReadLink", "ToolsFixture", "build_fixture", "manifest_fields",
]

#: 看板の作り物の印(``Event.origin``)。
SIGNBOARD_ORIGIN: Final[str] = "signboard:synthetic"
#: 看板を読んだ出来事の語(族 ``道具``・語は台帳の道具の名)。
SIGNBOARD_WHAT: Final[str] = V.word(V.FAMILY_TOOL, SIGNBOARD)
#: 原因(知覚=System 1)。
SIGNBOARD_CAUSE: Final[Process] = Process("perception")
#: manifest の ``tools`` の形の版。
MANIFEST_SCHEMA: Final[str] = "shibuya.engine.tools/c0/1"

#: 切替口の環境変数(既定 off)。
ARM_ENV: Final[str] = "SHIBUYA_TOOL_EVENTS"


def arm_from_env(value: str | None) -> bool:
    """環境変数の値 → 腕を入れるか(``on``・``1``・``true``・``yes`` だけ真=既定 off)。"""
    return str(value or "off").strip().lower() in ("on", "1", "true", "yes")


_ENABLED: bool = arm_from_env(os.environ.get(ARM_ENV))


def enabled() -> bool:
    """看板を読んだ出来事を書くか(切替口 ``SHIBUYA_TOOL_EVENTS``・``set_enabled``。既定 off)。"""
    return _ENABLED


def set_enabled(flag: bool) -> None:
    """腕を入れる/外す(組み立ての時に読む=ランの途中で変えても、そのランは変わらない)。"""
    global _ENABLED
    _ENABLED = bool(flag)


class SignboardReadLink:
    """看板を読んだ出来事を書く口(判断の系が刻みの終わりに知覚の事実を渡す)。"""

    __slots__ = ("log",)

    def __init__(self, log: EventLog) -> None:
        if type(log) is not EventLog:
            raise TypeError("SignboardReadLink は EventLog に書く")
        self.log = log

    def __call__(self, percepts: Mapping[int, Any]) -> int:
        """体 → ``Percept`` の表から、看板が見えた体ごとに出来事を 1 行書き、書いた行の数を返す。"""
        if not self.log.enabled:
            return 0
        n = 0
        for p in percepts.values():  # 逐次ループ宣言: その刻みに描いた体の数ぶん
            for o in p.seen_objects:
                if o.kind != "signage" or int(o.id) < 0:
                    continue
                t = int(p.t_ns)
                eid = self.log.append(Event(
                    t_ns=t, who=int(p.agent_id), what=SIGNBOARD_WHAT, where=("poi", int(o.id)), via=V.VIA_NONE,
                    received_ns=t, read_ns=t, origin=SIGNBOARD_ORIGIN, cause=SIGNBOARD_CAUSE))
                n += int(eid is not None)
        return n


@dataclass(frozen=True)
class ToolsFixture:
    """ランの道具の一式(組み立てで作り、ランの間は読むだけ)。"""

    registry: ToolRegistry
    #: グループの一覧(母集団の無いランは ``None``)。
    groups: GroupList | None
    phones: PhoneTable
    #: 看板を読んだ出来事の口(腕が off・出来事の記録が off のランは ``None``)。
    signboard_link: SignboardReadLink | None = None


def build_fixture(pop: Any, n_agents: int, events: EventLog | None) -> ToolsFixture:
    """組み立て: 台帳(最初の中身)・グループの一覧(W16 の母集団から)・店の番号の表(空)・看板の口(腕のときだけ)。"""
    groups = GroupList.from_population(pop, n_agents) if pop is not None else None
    link = SignboardReadLink(events) if (enabled() and events is not None and events.enabled) else None
    return ToolsFixture(registry=default_registry(), groups=groups, phones=PhoneTable(), signboard_link=link)


def _signboard_reads(daily_records: Any) -> int:
    n = 0
    for d in daily_records or ():
        ev = d.get("events") if isinstance(d, Mapping) else None
        if isinstance(ev, Mapping):
            n += int(dict(ev.get("by_what") or {}).get(SIGNBOARD_WHAT, 0))
    return n


def manifest_fields(fx: ToolsFixture | None, rel_layer: Any, agents: Any, daily_records: Any) -> dict[str, Any] | None:
    """manifest の ``tools``(計器): 道具の数と名・登録だけの道具・グループの数・連絡先の印の数・店の番号の表・看板の印。

    道具の一式の無いラン(組み立てを通らない)は ``None``。連絡先の印は関係の記憶のあるランだけ(無ければ ``None``)。
    """
    if fx is None:
        return None
    reg = fx.registry
    # 連絡先の印は持ち主(関係の記憶の層)の数えの口から読む(状態台帳の行 CT5=軸 1 diag・持ち主の外で欄を読まない)
    contact = rel_layer.contact_tally(agents) if (rel_layer is not None and agents is not None) else None
    return {
        "schema": MANIFEST_SCHEMA,
        "n_tools": len(reg),
        "names": list(reg.names),
        "registered_only": list(reg.registered_only()),
        "groups": None if fx.groups is None else fx.groups.tally(),
        "contact_flags": contact,
        "phone_table": fx.phones.tally(),
        "signboard": {
            "origin": SIGNBOARD_ORIGIN, "bridge": SIGNAGE_BRIDGE, "what": SIGNBOARD_WHAT,
            "events_arm": fx.signboard_link is not None,
            "read_events": _signboard_reads(daily_records) if fx.signboard_link is not None else 0,
        },
    }
