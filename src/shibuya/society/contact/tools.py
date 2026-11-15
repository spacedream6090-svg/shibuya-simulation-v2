"""engine.contact.tools — 連絡の道具の台帳の行(第 6 期 6-4 C1 の限界・C2・C6=口の約束 1-7・決定 10-12 §4-4 CT0)。

正: CT0「道具は、台帳に 1 行ずつ足す形にします(知っている/知らない/要るもの/体と知覚への影響/誰が持つか/中身を書くのは誰か)。
これから増やせます」・CT1(C2 ビデオ通話 → … → C6 手紙ほか)・CT5(店や組織の番号は場所の表の側・調べるは本人の行動)。

C1 は電話の行(``engine.tools.registry.PHONE``)だけを使い、メッセージの道具の行を足していなかった(C1 の記録の限界)。本段で
足す行(:data:`CONTACT_TOOLS`): メッセージ・ビデオ通話・充電器・店の番号を調べる(看板・地図)・郵便・置き手紙。

- **腕 c1 のランだけ**、組み立てがランの道具の台帳(``ToolsFixture.registry``)に ``register`` で足す(台帳は足すだけの形=
  既定のランの台帳と manifest の ``tools`` は今のまま=既定 off の 19 構成は不変)。
- 郵便・置き手紙(C6)は**行だけ**(実体は物=第 5 期 段 2・配達=6-6 ② の後=宣言)。使う口は無い(``stage`` の段)。
- 店の番号を調べる: 場所の表(``engine.tools.places.PhoneTable``)が空欄の間は誰も調べられない(つなぎ ``BR-PHONE-TABLE-BLANK``)。
  店に電話をかける口は店のエージェント(6-6 ②)の後。

**未リサーチ(expedient)**(つなぎの台帳 ``DOC-ct-c2-tool-rows``): 各行の欄の値(要るもの・体と知覚への影響の書き方・誰が持つか・
中身を書くのは誰か・段)は実装役が決定 10-12 §4-4 から当てた。

逐次ループ宣言: なし(行の数ぶん=6)。
"""

from __future__ import annotations

from typing import Any, Final

from shibuya.engine.tools.registry import ORIGIN_NONE, PHONE_BRIDGE, Tool

__all__ = [
    "MESSAGE", "VIDEO", "CHARGER", "LOOKUP", "POST", "NOTE", "CONTACT_TOOL_NAMES", "CONTACT_TOOLS", "register_into",
]

MESSAGE: Final[str] = "メッセージ"
VIDEO: Final[str] = "ビデオ通話"
CHARGER: Final[str] = "充電器"
LOOKUP: Final[str] = "店の番号を調べる"
POST: Final[str] = "郵便"
NOTE: Final[str] = "置き手紙"
CONTACT_TOOL_NAMES: Final[tuple[str, ...]] = (MESSAGE, VIDEO, CHARGER, LOOKUP, POST, NOTE)

_SMART: Final[tuple[str, ...]] = ("持ち物:スマートフォン", "契約:メッセージのアカウント", "回線:データ通信")

#: 足す行(並びは台帳に足す順)。
CONTACT_TOOLS: Final[tuple[Tool, ...]] = (
    # メッセージ(1 対 1・グループ): 本人が持ち、中身は本人が書く(文は LLM の口)。既読は道具の性質(送った側の画面に出る)。
    Tool(name=MESSAGE, owner="本人", content_writer="本人", requires=_SMART,
         affects={"目": "打つ・読む間は画面(周りは周辺視の気配だけ)", "心": "画面", "電池": "画面の減り",
                  "記録": "送った・届いた・読んだ(既読は読んだの whom から)"}),
    # ビデオ通話(C2): 電話の会話の器の種類違い。目は画面(相手の顔)・心は通話・電池は通話より大きく減る。
    Tool(name=VIDEO, owner="本人", content_writer="本人", requires=_SMART,
         affects={"目": "画面(相手の顔)", "心": "通話", "電池": "ビデオ通話の減り(通話より大きい・仮の値)",
                  "記録": "ビデオ通話をかけた・着信・出た・発話(via=ビデオ通話)"}),
    # 充電器: 家にある(持ち物の実データが無い=全員 1 台・宣言)。差す/抜くは本人の行動・家を離れたら抜ける(物理)。
    Tool(name=CHARGER, owner="本人", content_writer="機械", requires=("持ち物:充電器",),
         affects={"電池": "差している間は減らず増える(物理)", "場所": "家だけ", "記録": "充電した・充電をやめた"}),
    # 店の番号を調べる(看板・地図・検索): 中身(店の番号)は場所の表=W6 の POI の欄(空欄=BR-PHONE-TABLE-BLANK)。
    Tool(name=LOOKUP, owner="本人", content_writer="他人", requires=("持ち物:スマートフォン", "回線:データ通信"),
         affects={"目": "画面", "記録": "番号を調べた(場所の表に番号のある POI だけ)"},
         content_origin=ORIGIN_NONE, bridge=PHONE_BRIDGE),
    # 〔C6〕郵便・置き手紙: 行だけ(実体は物=第 5 期 段 2・配達=6-6 ② の後)。
    Tool(name=POST, owner="本人", content_writer="本人", requires=("持ち物:便箋", "持ち物:切手"), stage="6-6"),
    Tool(name=NOTE, owner="本人", content_writer="本人", requires=("持ち物:紙",), stage="5-2"),
)
assert tuple(t.name for t in CONTACT_TOOLS) == CONTACT_TOOL_NAMES


def register_into(registry: Any) -> int:
    """ランの道具の台帳に足す(腕 c1 の組み立てだけが呼ぶ)。もうある名は足さない(差し替えない)。足した行の数。"""
    n = 0
    for t in CONTACT_TOOLS:  # 逐次: 行の数ぶん(6)
        if t.name not in registry:
            registry.register(t)
            n += 1
    return n
