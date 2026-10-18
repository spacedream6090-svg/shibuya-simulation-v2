"""perception.contact_view — 連絡の道具 C1 の知覚の事実の値(目と心の向き・道具の状態)と描き方の行(第 6 期 6-4・腕 c1 だけ)。

正: 決定 10-12 §4-4 CT0(目の向き=視線の先・心の向き=関心の的・画面を見ている間は周辺視の粗い気配だけ・割り込めなかった出来事の
載せ方の 3 つの腕)・CT3(通知は周りの出来事の 1 つ)・口の約束 1-2(知覚の事実 ``Percept`` の欄だけ用意=値は後の段)。

- ``Percept`` の形は変えない(欄を足さない=``PERCEPT_SCHEMA`` も manifest の ``percept`` も今のまま)。腕 c1 のランだけ、空で
  始めた既存の欄 ``mind_dir``(心の向き)に :class:`AttentionView`(視線の先と関心の的を 1 つに)・``tool_state``(道具の状態)に
  :class:`DeviceView`(通知を含む)を入れる。``eye_dir`` は 16 方位の索引の欄(空間の段)のまま空(視線の先は ``mind_dir`` の
  ``gaze``)=仮採用。
- 描き方(``perception.renderer.Renderer`` の腕 c1 の口だけが使う): 画面を見ている体は B2 の可視物の行と B5 の近接の行を周辺視の
  行に替え、B6 の末尾に通知・着信・未読・通話・割り込めなかった出来事(腕 (ii))の行を足す。行の文面はここで決める(テンプレの
  版 ``template_sha256`` には入れない=腕のランだけ現れる行=1-8b の発話の行と同じ扱い)。

層契約: 標準ライブラリだけ(``perception.facts`` と同じ=描画と engine の両方から読める)。
**未リサーチ(expedient)**: 行の文面・人の気配の数の粗い段(0/1/2〜4/5 以上)。

逐次ループ宣言: なし(行の数ぶん=≤ 6)。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Final

__all__ = [
    "GAZE_WORDS", "FOCUS_WORDS", "AttentionView", "DeviceView", "B2_PERIPHERAL_LINE", "B5_PERIPHERAL_NEAR_LINE",
    "B6_NOTICE_LINE", "B6_RING_LINE", "B6_UNREAD_LINE", "B6_CALL_LINE", "B6_UNNOTICED_LINE", "people_hint_word",
    "contact_lines",
]

#: 視線の先(目の向き)の語。並びがコード(``engine.contact.attention.GAZE_*``)。
GAZE_WORDS: Final[tuple[str, ...]] = ("前", "画面", "手元", "相手")
#: 関心の的(心の向き)の語。並びがコード(``engine.contact.attention.FOCUS_*``)。
FOCUS_WORDS: Final[tuple[str, ...]] = ("周り", "画面", "通話", "会話")

B2_PERIPHERAL_LINE: Final[str] = "[B2 可視] 画面を見ていて、周りの物は見分けていない。"
B5_PERIPHERAL_NEAR_LINE: Final[str] = "[B5 近接] 近くの人物: 視界の端に人の気配({hint})。"
B6_NOTICE_LINE: Final[str] = "[B6 通知] {kind}の通知({level}・{channels})。"
B6_RING_LINE: Final[str] = "[B6 着信] {who}からの電話が鳴っている。"
B6_UNREAD_LINE: Final[str] = "[B6 画面] 未読 {n} 件。"
B6_CALL_LINE: Final[str] = "[B6 通話] {person}と通話中。"
B6_UNNOTICED_LINE: Final[str] = "[B6 周り] 周りで何かあったようだ(注意は向いていない)。"


@dataclass(frozen=True, slots=True)
class AttentionView:
    """目と心の向き(``Percept.mind_dir`` の値=腕 c1 のランだけ)。

    ``gaze``=視線の先(``GAZE_WORDS``)・``focus``=関心の的(``FOCUS_WORDS``)・``interrupted``=この呼び出しが驚き駆動の入口
    (セルの B4 の変化の起床)で起きたか・``peripheral``=視線が画面(周りは周辺視の粗い気配だけ)・``people_hint``=周辺視の範囲の
    人の気配の数・``unnoticed``=割り込めなかった周りの出来事(B4 の顕著行為の行)・``unnoticed_arm``=載せ方の腕・
    ``scene_filtered``=描画の B4 から顕著行為の行を落としたか。
    """

    gaze: str
    focus: str
    interrupted: bool
    peripheral: bool
    people_hint: int
    unnoticed: tuple[str, ...]
    unnoticed_arm: str
    scene_filtered: bool


@dataclass(frozen=True, slots=True)
class DeviceView:
    """道具の状態と通知(``Percept.tool_state`` の値=腕 c1 のランだけ)。返すのは現実の道具が知り得ることだけ(CT0 の 4)。

    ``unread``・``chats``・``ringing_from`` の相手は画面を見ているときだけ分かる(見ていなければ ``None`` か -1=誰からかは
    分からない)。``notice_*``=この刻みに System 1 に届いた通知(段と経路)。
    """

    battery_pct: int
    on: bool
    manner: bool
    place: str
    earphones: bool
    signal: bool
    notice_kind: str | None
    notice_level: str | None
    notice_channels: tuple[str, ...]
    unread: int | None
    ringing_from: int | None
    in_call_with: int | None
    chats: tuple[int, ...] | None


def people_hint_word(n: int) -> str:
    """人の気配の数 → 粗い語(周辺視=数えない)。"""
    n = int(n)
    if n <= 0:
        return "なし"
    if n == 1:
        return "1 人"
    if n <= 4:
        return "数人"
    return "多くの人"


def contact_lines(att: AttentionView | None, dev: DeviceView | None,
                  person_word: Callable[[int], str]) -> list[str]:
    """B6 の末尾に足す行(通話 → 着信 → 通知 → 未読 → 割り込めなかった出来事の順)。"""
    out: list[str] = []
    if dev is not None:
        if dev.in_call_with is not None and int(dev.in_call_with) >= 0:
            out.append(B6_CALL_LINE.format(person=person_word(int(dev.in_call_with))))
        if dev.ringing_from is not None:
            who = person_word(int(dev.ringing_from)) if int(dev.ringing_from) >= 0 else "誰か"
            out.append(B6_RING_LINE.format(who=who))
        if dev.notice_kind is not None and dev.notice_level is not None:
            out.append(B6_NOTICE_LINE.format(kind=dev.notice_kind, level=dev.notice_level,
                                             channels="・".join(dev.notice_channels) or "画面"))
        if dev.unread is not None and int(dev.unread) > 0:
            out.append(B6_UNREAD_LINE.format(n=int(dev.unread)))
    if att is not None and att.unnoticed and att.unnoticed_arm == "ii":
        out.append(B6_UNNOTICED_LINE)
    return out
