"""engine.tools.registry — 道具の台帳(第 1 期 1-7 C0・CT0)。

口の約束 1-7(``docs/design/v2-foundation-contracts-2026-10-13.md`` の「1-7 道具の台帳 C0」)・決定 10-12 §4-4 CT0
(道具は台帳に 1 行ずつ足す形=知っている/知らない・要るもの・体と知覚への影響・誰が持つか・中身を書くのは誰か。これから
増やせる)・§1-13(将来のマルチモーダル=音声・表情の欄を空で持つ・回答 10-13b §1 1-5 と同じ口)。

- ``Tool``(凍結・slots): 口の約束の 6 欄 ``name``・``known_by``・``requires``・``affects``・``owner``・``content_writer`` と、
  ``modality``(将来の音声・表情=空)・``content_origin``(中身の出どころ=実データ/作り物/無し=CT0 の「作り物」の印)・
  ``stage``(使う口が動く計画の段・``None``=今の世界で使っている)・``bridge``(つなぎの台帳の行の id)。
- ``KnownBy``: 「知っている/知らない」の体の集合の表し方(全員・誰も・番号の集合)。既定は ``EVERYONE``(全員が知っている
  の印)。知る・忘れるは本人の行動(後の段)。
- ``ToolRegistry``: 読み口 ``get(name)``・``known(agent, name)``・``names``・``rows``(``MappingProxyType``)。**書く口は
  ``register`` の 1 つ**(足すだけ=同じ名は ``ValueError``・差し替えと消去の口は無い)。中身は名を変えた slot 1 つ
  (``_ToolRegistry__rows``)で、属性の付け替えと消去は ``AttributeError``。
- 最初の中身 ``DEFAULT_TOOLS``(今の世界にある道具と将来の口): 看板・掲示(店の営業時間)・電話(店の番号=場所の表)・
  連絡先(関係の記憶の印)・グループ(家族・職場)・乗換案内・地図(登録だけ=中身は第 6 期 C1〜=計画 6-4)。

C0 では台帳を読む挙動は無い(読み手は manifest の ``tools`` と記録の口=``engine.tools.record``)。

〔1-7 の 1-8 への結線〕判断の候補の源「周りが示すできること」(``engine.decision.layer.DecisionLayer.affordance_words``)は、
``usable``(この体が知っていて・要るものが満たされ・今の世界で使う段の道具)を道具 → 判断の語彙の語の凍結の表
``TOOL_ACTION_WORDS`` で語に写して足す(``affordance_words``)。**表は今は空**=道具を使う行為の語(看板を読む・電話を
かける等)は判断の語彙に無い(6-4 C1 で語を足すまで候補に出ない=つなぎの台帳の行・``engine/decision/layer.py`` の見出し)。
要るもの(``requires``)は本人の持ち物・契約・回線の集合(``have``)に全部あれば満たされる。持ち物の台帳はまだ無い
(``Percept.belongings`` は空)ので、要るもののある道具は満たされない扱い。

先例(R-113 §8・形だけ借りた・コードは写していない): AgentSociety 2 の ``@tool(readonly, kind)`` と ``EnvMeta`` の登録表
(``packages/agentsociety2/agentsociety2/env/base.py``・Apache-2.0=登録の時に性質を検査する形)・OASIS の体ごとの
``available_actions``(``known_by`` の最初の形)・UE の Smart Objects(物の側が「何ができるか」を持つ)。「知っている/
知らない」「中身を書くのは誰か」の欄を道具の行に持つ実装は先例が無い(自前の構成)。

**未リサーチ(expedient)**: 最初の中身の各欄の値(要るもの・誰が持つか・中身を書くのは誰か・中身の出どころ・段)は実装役が
決定 10-12 §4-4 と R-85 §1 の道具の一覧から当てた(C0 では誰も読まない=結果に効かない)。

逐次ループ宣言: なし(台帳を作るのは起動時に 1 回・行の数ぶん)。
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from types import MappingProxyType
from typing import Any, Final, Iterable, Iterator, Mapping

import numpy as np

__all__ = [
    "SIGNBOARD", "NOTICE", "PHONE", "CONTACTS", "GROUP", "TRANSIT", "MAP", "TOOL_NAMES",
    "REQUIRE_KINDS", "OWNERS", "CONTENT_WRITERS", "CONTENT_ORIGINS", "ORIGIN_REAL", "ORIGIN_SYNTHETIC",
    "ORIGIN_NONE", "KNOWN_KINDS", "KnownBy", "EVERYONE", "NOBODY", "Tool", "TOOL_FIELDS", "ToolRegistry",
    "DEFAULT_TOOLS", "default_registry", "SIGNAGE_BRIDGE", "PHONE_BRIDGE", "NOTICE_BRIDGE", "TOOL_ACTION_WORDS",
    "affordance_words",
]

# ---------------------------------------------------------------- 道具の名(台帳の鍵)
SIGNBOARD: Final[str] = "看板"
NOTICE: Final[str] = "掲示"
PHONE: Final[str] = "電話"
CONTACTS: Final[str] = "連絡先"
GROUP: Final[str] = "グループ"
TRANSIT: Final[str] = "乗換案内"
MAP: Final[str] = "地図"
#: 最初の中身の名(並びは台帳の並び)。
TOOL_NAMES: Final[tuple[str, ...]] = (SIGNBOARD, NOTICE, PHONE, CONTACTS, GROUP, TRANSIT, MAP)

#: 要るものの種類(決定 10-12 §4-4 CT0「要るもの=持ち物・契約・回線」)。``requires`` の要素は ``"<種類>:<名>"``。
REQUIRE_KINDS: Final[tuple[str, ...]] = ("持ち物", "契約", "回線")
#: 誰が持つか(本人=使う人・店=店の主体・組織=組織の主体・成員=グループの成員)。
OWNERS: Final[tuple[str, ...]] = ("本人", "店", "組織", "成員")
#: 中身を書くのは誰か(口の約束 1-7=本人/他人/機械)。
CONTENT_WRITERS: Final[tuple[str, ...]] = ("本人", "他人", "機械")
ORIGIN_REAL: Final[str] = "実データ"
ORIGIN_SYNTHETIC: Final[str] = "作り物"
ORIGIN_NONE: Final[str] = "無し"
#: 中身の出どころ(実データ=現実のデータから・作り物=現実のデータに置き換わるまでのつなぎ(CT0)・無し=中身がまだ無い)。
CONTENT_ORIGINS: Final[tuple[str, ...]] = (ORIGIN_REAL, ORIGIN_SYNTHETIC, ORIGIN_NONE)

#: 看板の文が作り物であることのつなぎの台帳の行(1-4 で足した行=決定 10-12 §4-4 CT0・§1-5 の 6)。
SIGNAGE_BRIDGE: Final[str] = "BR-SIGNAGE-FICTION"
#: 店の番号の場所の表が空であることのつなぎの台帳の行(1-7 で足した行)。
PHONE_BRIDGE: Final[str] = "BR-PHONE-TABLE-BLANK"
#: 営業時間のうち OSM の実値が無い店のカテゴリの既定値(W7 の構築の段が宣言したつなぎ)。
NOTICE_BRIDGE: Final[str] = "W7#1"

#: 「知っている/知らない」の表し方の種類(全員・誰も・番号の集合)。
KNOWN_KINDS: Final[tuple[str, ...]] = ("all", "none", "set")


def _is_int(x: Any) -> bool:
    return isinstance(x, (int, np.integer)) and not isinstance(x, (bool, np.bool_))


@dataclass(frozen=True, slots=True)
class KnownBy:
    """道具を知っている体の集合の表し方(凍結)。``kind``=``all``(全員)・``none``(誰も)・``set``(``members`` の体だけ)。"""

    kind: str = "all"
    members: frozenset[int] = frozenset()

    def __post_init__(self) -> None:
        if self.kind not in KNOWN_KINDS:
            raise ValueError(f"KnownBy.kind は {KNOWN_KINDS} のどれか(いま {self.kind!r})")
        if not isinstance(self.members, frozenset):
            raise TypeError("KnownBy.members は frozenset(体の番号の集合)")
        for m in self.members:
            if not _is_int(m) or int(m) < 0:
                raise ValueError(f"KnownBy.members は 0 以上の体の番号(いま {m!r})")
        if self.kind != "set" and self.members:
            raise ValueError("KnownBy の members は kind='set' のときだけ")
        object.__setattr__(self, "members", frozenset(int(m) for m in self.members))

    @staticmethod
    def of(agents: Iterable[int]) -> "KnownBy":
        """番号の集合(``set``)。"""
        return KnownBy("set", frozenset(int(a) for a in agents))

    def knows(self, agent: int) -> bool:
        if self.kind == "all":
            return True
        if self.kind == "none":
            return False
        return int(agent) in self.members

    def describe(self) -> str:
        """manifest に書く短い表し方(番号の集合は数だけ)。"""
        return self.kind if self.kind != "set" else f"set:{len(self.members)}"


#: 全員が知っている(既定の印)。
EVERYONE: Final[KnownBy] = KnownBy("all")
#: 誰も知らない。
NOBODY: Final[KnownBy] = KnownBy("none")


def _closed(value: Any, allowed: tuple[str, ...], name: str) -> str:
    if value not in allowed:
        raise ValueError(f"Tool.{name} は {allowed} のどれか(いま {value!r})")
    return str(value)


@dataclass(frozen=True, slots=True, kw_only=True)
class Tool:
    """道具の台帳の 1 行(凍結)。欄の名と順は口の約束 1-7 の 6 欄+将来の欄・出どころ・段・つなぎの行。"""

    #: 道具の名(台帳の鍵)。
    name: str
    #: 知っている/知らない(体の集合の表し方・既定は全員が知っている)。
    known_by: KnownBy = EVERYONE
    #: 要るもの(``"持ち物:…"``・``"契約:…"``・``"回線:…"``)。
    requires: tuple[str, ...] = ()
    #: 体と知覚への影響の欄(C0 は値が空=``None``・目の向き・心の向きは CT2 の段)。
    affects: Mapping[str, Any] | None = None
    #: 誰が持つか(``OWNERS``)。
    owner: str
    #: 中身を書くのは誰か(``CONTENT_WRITERS``)。
    content_writer: str
    #: 将来の音声・表情の欄(決定 10-12 §1-13・回答 10-13b §1 1-5。C0 は空=``None``)。
    modality: tuple[str, ...] | None = None
    #: 中身の出どころ(``CONTENT_ORIGINS``)。``作り物``=つなぎ(``bridge`` の行)。
    content_origin: str = ORIGIN_NONE
    #: 使う口が動く計画の段(``None``=今の世界で使っている。``"6-4"``=第 6 期 C1〜)。
    stage: str | None = None
    #: つなぎの台帳の行の id(無ければ ``None``)。
    bridge: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Tool.name は空でない文字列")
        if type(self.known_by) is not KnownBy:
            raise TypeError(f"Tool.known_by は KnownBy(いま {type(self.known_by)!r})")
        req = tuple(self.requires)
        for r in req:
            if not isinstance(r, str) or ":" not in r or r.split(":", 1)[0] not in REQUIRE_KINDS or not r.split(":", 1)[1]:
                raise ValueError(f"Tool.requires の要素は '<{'/'.join(REQUIRE_KINDS)}>:<名>'(いま {r!r})")
        if len(set(req)) != len(req):
            raise ValueError("Tool.requires に同じものが 2 回ある")
        object.__setattr__(self, "requires", req)
        if self.affects is not None:
            if not isinstance(self.affects, Mapping):
                raise TypeError("Tool.affects は Mapping か None")
            object.__setattr__(self, "affects", MappingProxyType(dict(self.affects)))
        _closed(self.owner, OWNERS, "owner")
        _closed(self.content_writer, CONTENT_WRITERS, "content_writer")
        _closed(self.content_origin, CONTENT_ORIGINS, "content_origin")
        if self.modality is not None:
            mod = tuple(self.modality)
            if not all(isinstance(m, str) and m for m in mod):
                raise ValueError("Tool.modality は空でない文字列の組か None")
            object.__setattr__(self, "modality", mod)
        if self.stage is not None:
            from shibuya.engine.bridging.ledger import PLAN_STAGES

            if self.stage not in PLAN_STAGES:
                raise ValueError(f"Tool.stage は計画の段の番号か None(いま {self.stage!r})")
        if self.bridge is not None and (not isinstance(self.bridge, str) or not self.bridge.strip()):
            raise ValueError("Tool.bridge は空でない文字列(つなぎの台帳の行の id)か None")
        if self.content_origin == ORIGIN_SYNTHETIC and self.bridge is None:
            raise ValueError("中身が作り物の道具は、つなぎの台帳の行(bridge)を持つ(CT0)")

    def as_dict(self) -> dict[str, Any]:
        """manifest・記録に書ける形。"""
        return {
            "name": self.name, "known_by": self.known_by.describe(), "requires": list(self.requires),
            "affects": None if self.affects is None else dict(self.affects), "owner": self.owner,
            "content_writer": self.content_writer, "modality": None if self.modality is None else list(self.modality),
            "content_origin": self.content_origin, "stage": self.stage, "bridge": self.bridge,
        }


#: ``Tool`` の欄の名と順(口の約束 1-7 の 6 欄が先頭)。
TOOL_FIELDS: Final[tuple[str, ...]] = tuple(f.name for f in fields(Tool))


class ToolRegistry:
    """道具の台帳。**書く口は ``register`` の 1 つ**(足すだけ)。

    中身は名を変えた slot 1 つ(``_ToolRegistry__rows``=名 → ``Tool`` の ``MappingProxyType``)。``register`` は表を写して
    1 行を足した新しい表に替える(前に読み手へ渡した表は変わらない)。``__slots__`` だけで ``__dict__`` を持たないので、
    名の無い属性は置けない。
    """

    __slots__ = ("__rows",)

    def __init__(self, tools: Iterable[Tool] = ()) -> None:
        try:  # 検収 L2: 作った後に __init__ を呼び直して中身を入れ替えない
            object.__getattribute__(self, "_ToolRegistry__rows")
        except AttributeError:
            pass
        else:
            raise RuntimeError("ToolRegistry は作った後に __init__ を呼び直せない(中身を入れ替えない)")
        object.__setattr__(self, "_ToolRegistry__rows", MappingProxyType({}))
        for t in tools:
            self.register(t)

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"ToolRegistry の書く口は register だけ({name} は書けない)")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"ToolRegistry の書く口は register だけ({name} は消せない)")

    # ------------------------------------------------------------------ 書く口(1 つ)
    def register(self, tool: Tool) -> None:
        """道具を 1 行足す(同じ名は ``ValueError``=差し替えない)。**書く口はこれ 1 つ**。"""
        if type(tool) is not Tool:
            raise TypeError(f"ToolRegistry.register は Tool だけを受け取る(いま {type(tool)!r})")
        rows = self.__rows
        if tool.name in rows:
            raise ValueError(f"道具 {tool.name!r} はもう台帳にある(差し替えない=足すだけ)")
        object.__setattr__(self, "_ToolRegistry__rows", MappingProxyType({**rows, tool.name: tool}))

    # ------------------------------------------------------------------ 読む口
    def get(self, name: str) -> Tool:
        """名の行(無ければ ``KeyError``)。"""
        try:
            return self.__rows[name]
        except KeyError:
            raise KeyError(f"道具 {name!r} は台帳に無い(台帳は {tuple(self.__rows)})") from None

    def known(self, agent: int, name: str) -> bool:
        """体 ``agent`` が道具 ``name`` を知っているか。"""
        if not _is_int(agent) or int(agent) < 0:
            raise ValueError(f"agent は 0 以上の体の番号(いま {agent!r})")
        return self.get(name).known_by.knows(int(agent))

    @property
    def rows(self) -> Mapping[str, Tool]:
        """名 → 行(読み取り専用の表)。"""
        return self.__rows

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(self.__rows)

    def __len__(self) -> int:
        return len(self.__rows)

    def __iter__(self) -> Iterator[Tool]:
        return iter(tuple(self.__rows.values()))

    def __contains__(self, name: object) -> bool:
        return name in self.__rows

    def in_use(self) -> tuple[str, ...]:
        """今の世界で使っている道具(``stage`` が ``None``)。"""
        return tuple(t.name for t in self if t.stage is None)

    def registered_only(self) -> tuple[str, ...]:
        """登録だけの道具(使う口は後の段)。"""
        return tuple(t.name for t in self if t.stage is not None)

    def usable(self, agent: int, have: Iterable[str] = ()) -> tuple[Tool, ...]:
        """体 ``agent`` が使える道具(知っている・要るものが ``have`` に全部ある・今の世界で使う段=``stage`` が ``None``)。

        台帳の並び。読むだけ。逐次ループ宣言: 台帳の行の数ぶん(7)。
        """
        if not _is_int(agent) or int(agent) < 0:
            raise ValueError(f"agent は 0 以上の体の番号(いま {agent!r})")
        h = frozenset(have)
        return tuple(t for t in self if t.stage is None and t.known_by.knows(int(agent)) and set(t.requires) <= h)


#: 最初の中身(今の世界にある道具と将来の口)。値の根拠は各行の注(未リサーチ=expedient・C0 では誰も読まない)。
DEFAULT_TOOLS: Final[tuple[Tool, ...]] = (
    # 看板: 店の主体が持ち、中身は店(他人)が書く。今の文は W14 で LLM が書いた作り物=つなぎ(CT0・BR-SIGNAGE-FICTION)。
    # 今の世界で使っている(描画の B2 の看板の行・注視のゲート)。
    Tool(name=SIGNBOARD, owner="店", content_writer="他人", content_origin=ORIGIN_SYNTHETIC, bridge=SIGNAGE_BRIDGE),
    # 掲示(店の営業時間): 店の主体が持ち、中身は店(他人)が書く。営業時間は W7 の予定の表=OSM の opening_hours の実値
    # (565 件)とチェーンの伝播・残りはカテゴリの既定値(つなぎ W7#1)。今の世界で使っている(開いているかの判定・失敗の
    # 直後の次の開店の時刻)。
    Tool(name=NOTICE, owner="店", content_writer="他人", content_origin=ORIGIN_REAL, bridge=NOTICE_BRIDGE),
    # 電話: 本人が持ち、要るのは電話機と契約と網。店の番号は場所の表(engine.tools.places・C0 は空=BR-PHONE-TABLE-BLANK)。
    # 通話の中身は C1(計画 6-4)。
    Tool(name=PHONE, owner="本人", content_writer="本人", requires=("持ち物:携帯電話", "契約:電話の契約", "回線:電話の網"),
         stage="6-4", bridge=PHONE_BRIDGE),
    # 連絡先: 関係の記憶に手段ごとの印(CT5)。家族と職場は初めから(W16 の世帯と事業所=実データ)。使う口は C1。
    Tool(name=CONTACTS, owner="本人", content_writer="本人", content_origin=ORIGIN_REAL, stage="6-4"),
    # グループ(家族・職場): 成員が持ち、中身(グループのメッセージ)は成員が書く。一覧は W16(実データ)。使う口は C1。
    Tool(name=GROUP, owner="成員", content_writer="本人", requires=("持ち物:スマートフォン", "契約:メッセージのアカウント",
                                                                  "回線:データ通信"),
         content_origin=ORIGIN_REAL, stage="6-4"),
    # 乗換案内・地図: 本人のスマートフォンの機能で、中身は機械が書く。登録だけ(中身は第 6 期 C1〜)。
    Tool(name=TRANSIT, owner="本人", content_writer="機械", requires=("持ち物:スマートフォン", "回線:データ通信"),
         stage="6-4"),
    Tool(name=MAP, owner="本人", content_writer="機械", requires=("持ち物:スマートフォン", "回線:データ通信"), stage="6-4"),
)
assert tuple(t.name for t in DEFAULT_TOOLS) == TOOL_NAMES


#: 道具 → 判断の語彙の語(道具を使う行為の語)の凍結の表。**今は空**=道具を使う行為の語は判断の語彙(v1〜v3)に無い。
#: 語を足すのは語彙の版上げ(6-4 C1)と同じ時(つなぎの台帳の行=``engine/decision/layer.py`` の見出しの行)。
TOOL_ACTION_WORDS: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType({})


def affordance_words(registry: ToolRegistry, agent: int, have: Iterable[str] | None = None) -> tuple[str, ...]:
    """体 ``agent`` が使える道具を、``TOOL_ACTION_WORDS`` で判断の語彙の語に写した語(台帳の並び・重ねない)。

    ``have`` は本人の持ち物・契約・回線(``"持ち物:…"`` の形・無ければ空=要るもののある道具は使えない)。表は呼ぶたびに
    この置き場から読む(試験の差し替えが効く)。今は表が空なので、いつも空の組を返す。
    """
    table = TOOL_ACTION_WORDS
    if not table:
        return ()
    out: list[str] = []
    for t in registry.usable(agent, () if have is None else have):  # 逐次ループ宣言: 使える道具の数(≤ 7)
        for w in table.get(t.name, ()):
            if w not in out:
                out.append(w)
    return tuple(out)


def default_registry() -> ToolRegistry:
    """最初の中身の台帳(呼ぶたびに新しい物=ランごとに 1 つ)。"""
    return ToolRegistry(DEFAULT_TOOLS)
