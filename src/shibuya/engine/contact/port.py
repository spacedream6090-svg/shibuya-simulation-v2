"""engine.contact.port — 連絡の本人の判断(候補の口 J0 の形)の仮のモデル・文の口・習慣の口(第 6 期 6-4 C1)。

正: 決定 10-12 §4-4 CT2(送るかと宛先は判断モデル・文は LLM=比べる腕 (c) は選択の言葉をそのまま・スタンプは一覧から・長さの
上限は安全装置だけ)・CT3(気づいたら判断モデルが「今読む/後で/無視」・暇なとき=待ち・電車はスマホを見るを過ごし方の 1 つに・
エンジンは時刻も回数も決めない)・CT4(範囲の外の人も本人が返す・習慣は本人の過去の判断から=本段は作らず判断の口に戻す)・
TM1(出るかは本人)・回答 2-1(GPU の前は仮のモデル=mock)。口の約束 1-8(候補の口 J0)・1-8b(発話の口=届け先の行の形)。

- :class:`ContactPort`(``DecisionPort`` の子=同じ入口 ``choose(ctx, candidates)``): 候補を並べ替えて番号を振り(C-2 の 1)、
  仮のモデル(mock)が中身で選ぶ=候補を (語・id) の順に並べ、乱数の値を候補の数で割った余りの候補(``engine.decision.ports.
  MockPort.pick`` と同じ形)。乱数は 10c の counter(用途名 ``contact.mock``・``contact.present``=動きの側・鍵=刻みの鍵・体・
  その刻みのその体の判断の通し番号)。判断の呼びの ``call_id`` は**テープの形** ``<刻み>:<体>:<−通し番号>``(〔検収 M3 ④・L5〕
  3 つ目の数を負にして主の判断の呼び(起床の級 ≥ 0)と分ける=出来事の記録の原因の表は整数 3 つ=文字列の表を使わない)。
  通し番号=その刻みのその体の判断の数 k × 16+判断の種類(1〜10)。k は 1 体 1 刻みに ``MAX_DECISIONS_PER_STEP`` 未満(上限を
  超えたら ``ValueError``=番号がぶつからない)。
- 仲裁(〔検収 M5 (iii)〕``ARBITRATION``=宣言): 同じ体が同じ刻みに主の判断(起床して判断の呼び)と連絡の判断の両方を要する
  ときは主の判断が先・連絡の判断はその刻みにしない(通知の判断は次の刻みに回す・画面と着信と通話の番は次の刻みにまた起きる)。
- 判断の種類と候補(語は下の定数・源は DM-0 の 5 つの源):

  | 判断 | 候補(源) |
  |---|---|
  | 通知に気づいた | 今読む(周りが示すできること)・後で(近い予定)・無視(続ける) |
  | 暇になった(待機・乗車に入った/起きた) | スマホを見る(できること)・このまま過ごす(続ける) |
  | 画面を見ている | 読む(未読があるとき)・メッセージを送る・グループに送る・電話をかける(宛先があるとき)・画面を見続ける(続ける)・顔を上げる |
  | 宛先・グループ | 連絡先の人/グループ(経験=関係の記憶の印・グループの一覧) |
  | 読んだ後 | 返す・スタンプを送る(できること)・返さない(続ける) |
  | スタンプ | 一覧 ``STAMPS`` の 1 つ |
  | 着信に気づいた | 出る(できること)・出ない(続ける) |
  | かけて鳴らしている | 待つ(続ける)・切る(できること) |
  | 通話の番 | 話す(続ける)・切る(できること) |
  | 〔C2〕充電(家で電池が少ない・満充電の知らせ) | 充電する(できること)・このまま(続ける)/充電をやめる(できること)・そのまま(続ける) |
  | 〔C2〕対面の会話の自分の最初の番 | 相手と連絡先を交換する(できること)・交換しない(続ける)/持ちかけられた側: 交換する・断る |
  | 〔C2〕画面(足した候補) | ビデオ通話をかける・グループを作る・グループに招く・グループを抜ける・店の番号を調べる(どれも宛先・グループ・
    番号があるとき) |
  | 〔C2〕招待 | 入る(できること)・断る(続ける) |

- :class:`MockTextPort`(文の口=LLM の口の代わり): 定型の文 1 つ(``llm.mock.MOCK_UTTERANCE``=中身を誘導しない配管)。
  腕 (c) は選んだ候補の見せ方の文をそのまま送る(``engine.contact.layer``)。長さの上限 ``MESSAGE_MAX_CHARS`` は安全装置だけ
  (当たったら切って計器に数える)。
- 〔C2〕CT4 の習慣(``engine.contact.habit``・腕 ``SHIBUYA_CONTACT_HABIT``): 習慣で答えた選びの原因は判断の種類
  ``P_HABIT_NOTICE``・``P_HABIT_REPLY``(通し番号の下の 4 ビット)の呼びの id(源=経験・判断モデルの呼び数には数えない)。ときどき
  判断の口へ戻すかは :func:`habit_recheck_u`(乱数の用途名 ``contact.habit``=動きの側・鍵=刻みの鍵・体・その刻みのその体の通し番号)。

**未リサーチ(expedient)**(つなぎの台帳 ``DOC-ct-c1-port-*``): 候補の語と源の当て方・スタンプの一覧の 4 語・定型の文・長さの上限
1,000 字・mock の一様な選び方(判断モデルの代わり=結果の数は振る舞いのモデルではない)。

逐次ループ宣言: ``choose`` は候補の数ぶん(≤ 20)。
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Sequence

from shibuya.core.rng import k19_counters, stream
from shibuya.engine.decision.port import (
    OTHER_ID,
    SOURCE_AFFORDANCE,
    SOURCE_CONTINUE,
    SOURCE_EXPERIENCE,
    SOURCE_PLAN,
    Candidate,
    Choice,
    DecisionContext,
    DecisionPort,
    present,
)
from shibuya.llm.mock import MOCK_UTTERANCE

__all__ = [
    "HABIT_DOMAIN", "P_CHARGE", "P_EXCHANGE", "P_GROUPS", "P_HABIT_NOTICE", "P_HABIT_REPLY", "K_CHARGE", "K_NO_CHARGE",
    "K_UNPLUG", "K_KEEP_PLUGGED", "K_EXCHANGE", "K_NO_EXCHANGE", "K_EXCH_YES", "K_EXCH_NO", "K_VIDEO", "K_MAKE_GROUP",
    "K_INVITE", "K_LEAVE", "K_JOIN", "K_REFUSE", "K_LOOKUP", "habit_recheck_u",
    "MOCK_DOMAIN", "PRESENT_DOMAIN", "STAMPS", "MOCK_TEXT", "MESSAGE_MAX_CHARS", "PURPOSES",
    "P_NOTICE", "P_IDLE", "P_SCREEN", "P_WHOM", "P_GROUP", "P_REPLY", "P_STAMP", "P_RING", "P_WAIT", "P_TURN",
    "K_READ_NOW", "K_LATER", "K_IGNORE", "K_LOOK", "K_STAY", "K_READ", "K_SEND", "K_SEND_GROUP", "K_CALL", "K_KEEP",
    "K_UP", "K_TO", "K_GROUP", "K_REPLY", "K_STAMP", "K_NOREPLY", "K_STAMP_ITEM", "K_ANSWER", "K_DECLINE", "K_WAIT",
    "K_HANG", "K_TALK", "cand", "ContactPort", "MockTextPort", "call_id_of", "step_of_call_id",
    "cap_text", "PROVISIONAL_VALUES", "MAX_DECISIONS_PER_STEP", "serial_of", "purpose_of_serial", "parse_call_id",
    "ARBITRATION",
]

#: 仮のモデルの選びの乱数の用途名(動きの側=``engine.run.MOTION_RNG_DOMAINS``)。
MOCK_DOMAIN: Final[str] = "contact.mock"
#: 候補の提示の並べ替えの乱数の用途名(動きの側)。
PRESENT_DOMAIN: Final[str] = "contact.present"
#: 〔C2〕習慣で答えられるときも判断の口へ戻すかの乱数の用途名(動きの側)。
HABIT_DOMAIN: Final[str] = "contact.habit"

#: スタンプの一覧(判断が一覧から選ぶ=CT2)。
STAMPS: Final[tuple[str, ...]] = ("了解", "ありがとう", "おつかれさま", "おやすみ")
#: 文の口の仮のモデルの定型の文(``llm.mock.MOCK_UTTERANCE`` と同じ=会話の番の ひと言 と同じ配管)。
MOCK_TEXT: Final[str] = MOCK_UTTERANCE
#: メッセージの長さの上限(安全装置だけ・当たったら切って数える)。
MESSAGE_MAX_CHARS: Final[int] = 1000

# ---- 判断の種類(乱数の鍵とテープの形でない call_id に入る番号) ----
P_NOTICE, P_IDLE, P_SCREEN, P_WHOM, P_GROUP, P_REPLY, P_STAMP, P_RING, P_WAIT, P_TURN = range(1, 11)
#: 〔C2〕充電する/やめる・連絡先の交換(持ちかける/応じる)・招待に答える・習慣で答えた(通知・返事)=判断の種類 11〜15
#: (通し番号の下の 4 ビットに入る最後の 5 つ)。〔検収 L9〕これで 4 ビット(1〜15)が埋まった=次に判断の種類を足す段は通し番号の
#: 形(k × 16+種類)を変える(たとえば × 32=call_id とテープの形が変わる=腕のランの final が動く)。
P_CHARGE, P_EXCHANGE, P_GROUPS, P_HABIT_NOTICE, P_HABIT_REPLY = range(11, 16)
PURPOSES: Final = MappingProxyType({
    P_NOTICE: "notice", P_IDLE: "idle", P_SCREEN: "screen", P_WHOM: "whom", P_GROUP: "group", P_REPLY: "reply",
    P_STAMP: "stamp", P_RING: "ring", P_WAIT: "wait", P_TURN: "turn",
    P_CHARGE: "charge", P_EXCHANGE: "exchange", P_GROUPS: "invite_answer", P_HABIT_NOTICE: "habit_notice",
    P_HABIT_REPLY: "habit_reply",
})
#: 1 体 1 刻みの連絡の判断の数の上限(通し番号がぶつからない形の安全装置=当たったら ``ValueError``)。
MAX_DECISIONS_PER_STEP: Final[int] = 1 << 14
#: 仲裁の規則の表(〔検収 M5 (iii)〕宣言=実装は ``engine.contact.layer.ContactLayer._person_decisions`` ほか)。
ARBITRATION: Final = MappingProxyType({
    "main_first": "同じ体が同じ刻みに主の判断(起床して判断の呼び)と連絡の判断の両方を要するときは主の判断が先・連絡の判断は"
                  "その刻みにしない(通知の判断は次の刻みに回す・画面・着信・呼び出し・通話の番は次の刻みにまた起きる)",
})

# ---- 候補の語 ----
K_READ_NOW, K_LATER, K_IGNORE = "今読む", "後で", "無視"
K_LOOK, K_STAY = "スマホを見る", "このまま過ごす"
K_READ, K_SEND, K_SEND_GROUP, K_CALL, K_KEEP, K_UP = "読む", "メッセージを送る", "グループに送る", "電話をかける", "画面を見続ける", "顔を上げる"
K_TO, K_GROUP = "宛先", "グループ"
K_REPLY, K_STAMP, K_NOREPLY, K_STAMP_ITEM = "返す", "スタンプを送る", "返さない", "スタンプ"
K_ANSWER, K_DECLINE = "出る", "出ない"
K_WAIT, K_HANG, K_TALK = "待つ", "切る", "話す"
# 〔C2〕
K_CHARGE, K_NO_CHARGE, K_UNPLUG, K_KEEP_PLUGGED = "充電する", "このまま", "充電をやめる", "そのまま"
K_EXCHANGE, K_NO_EXCHANGE, K_EXCH_YES, K_EXCH_NO = "連絡先を交換する", "交換しない", "交換する", "断る"
K_VIDEO, K_MAKE_GROUP, K_INVITE, K_LEAVE = "ビデオ通話をかける", "グループを作る", "グループに招く", "グループを抜ける"
K_JOIN, K_REFUSE, K_LOOKUP = "グループに入る", "招待を断る", "店の番号を調べる"

#: 本モジュールの仮の値の宣言(つなぎの台帳 DOC-ct-c1-port-* と 1 対 1)。
PROVISIONAL_VALUES: Final[tuple[str, ...]] = (
    "判断の候補の語と源の当て方(今読む/後で/無視・スマホを見る・画面の 6 つ・宛先・返す・出る/出ない・待つ/切る・話す/切る)",
    "仮のモデル(mock)は候補を語と id の順に並べ乱数の余りで一様に選ぶ(判断モデルの代わり)",
    "スタンプの一覧 4 語・文の口の定型の文(MOCK_UTTERANCE)・長さの上限 1,000 字(安全装置だけ)",
    "〔C2〕充電・連絡先の交換・グループ・ビデオ通話・店の番号を調べるの候補の語と源の当て方(仮のモデルは一様)",
)

_SOURCE_OF: Final = MappingProxyType({
    K_READ_NOW: SOURCE_AFFORDANCE, K_LATER: SOURCE_PLAN, K_IGNORE: SOURCE_CONTINUE,
    K_LOOK: SOURCE_AFFORDANCE, K_STAY: SOURCE_CONTINUE,
    K_READ: SOURCE_AFFORDANCE, K_SEND: SOURCE_AFFORDANCE, K_SEND_GROUP: SOURCE_AFFORDANCE, K_CALL: SOURCE_AFFORDANCE,
    K_KEEP: SOURCE_CONTINUE, K_UP: SOURCE_AFFORDANCE,
    K_TO: SOURCE_EXPERIENCE, K_GROUP: SOURCE_EXPERIENCE,
    K_REPLY: SOURCE_AFFORDANCE, K_STAMP: SOURCE_AFFORDANCE, K_NOREPLY: SOURCE_CONTINUE, K_STAMP_ITEM: SOURCE_AFFORDANCE,
    K_ANSWER: SOURCE_AFFORDANCE, K_DECLINE: SOURCE_CONTINUE,
    K_WAIT: SOURCE_CONTINUE, K_HANG: SOURCE_AFFORDANCE, K_TALK: SOURCE_CONTINUE,
    K_CHARGE: SOURCE_AFFORDANCE, K_NO_CHARGE: SOURCE_CONTINUE, K_UNPLUG: SOURCE_AFFORDANCE,
    K_KEEP_PLUGGED: SOURCE_CONTINUE, K_EXCHANGE: SOURCE_AFFORDANCE, K_NO_EXCHANGE: SOURCE_CONTINUE,
    K_EXCH_YES: SOURCE_AFFORDANCE, K_EXCH_NO: SOURCE_CONTINUE, K_VIDEO: SOURCE_AFFORDANCE,
    K_MAKE_GROUP: SOURCE_AFFORDANCE, K_INVITE: SOURCE_AFFORDANCE, K_LEAVE: SOURCE_AFFORDANCE, K_JOIN: SOURCE_AFFORDANCE,
    K_REFUSE: SOURCE_CONTINUE, K_LOOKUP: SOURCE_AFFORDANCE,
})


def cand(kind: str, text: str | None = None, *, id: str | None = None,
         basis: Sequence[tuple[int, int]] = ()) -> Candidate:
    """候補 1 つ(源は語から・見せ方の文は省略で語そのもの・id は省略で語)。"""
    return Candidate(id=id or kind, kind=kind, text=text or kind, source=_SOURCE_OF[kind], basis=tuple(basis))


def serial_of(purpose: int, k: int) -> int:
    """判断の通し番号(その刻みのその体の k 回目 × 16+判断の種類)。上限を超えたら ``ValueError``(番号がぶつからない)。"""
    if not (1 <= int(purpose) < 16):
        raise ValueError(f"判断の種類 {purpose} が表の外")
    if not (1 <= int(k) < MAX_DECISIONS_PER_STEP):
        raise ValueError(f"1 体 1 刻みの連絡の判断の数が上限 {MAX_DECISIONS_PER_STEP} に当たった(k={k})")
    return int(k) * 16 + int(purpose)


def purpose_of_serial(serial: int) -> int:
    return int(serial) % 16


def call_id_of(step: int, agent: int, serial: int) -> str:
    """判断の呼びの id(テープの形 ``<刻み>:<体>:<−通し番号>``=主の判断の起床の級 ≥ 0 と分ける)。"""
    if int(serial) <= 0:
        raise ValueError("通し番号は正")
    return f"{int(step)}:{int(agent)}:{-int(serial)}"


def parse_call_id(call_id: str) -> tuple[int, int, int] | None:
    """連絡の判断の呼びの id → ``(刻み, 体, 通し番号)``(連絡の形でなければ ``None``)。"""
    parts = str(call_id).split(":")
    if len(parts) != 3:
        return None
    try:
        t, a, c = (int(x) for x in parts)
    except ValueError:
        return None
    if f"{t}:{a}:{c}" != str(call_id) or t < 0 or a < 0 or c >= 0:
        return None
    return t, a, -c


def step_of_call_id(call_id: str) -> int | None:
    """判断の呼びの id → 刻み(連絡の形でなければ ``None``)。負の対照の試験と監査が読む。"""
    got = parse_call_id(call_id)
    return None if got is None else got[0]


def _serial(ctx: DecisionContext) -> int:
    got = parse_call_id(ctx.call_id)
    if got is None:
        raise ValueError(f"連絡の判断の呼びの id でない: {ctx.call_id!r}")
    return got[2]


def cap_text(text: str) -> tuple[str, bool]:
    """長さの上限(安全装置): 超えたら切って ``True``。"""
    t = str(text)
    if len(t) > MESSAGE_MAX_CHARS:
        return t[:MESSAGE_MAX_CHARS], True
    return t, False


class ContactPort(DecisionPort):
    """連絡の判断の仮のモデル(mock・判断モデルの代わり)。乱数の鍵はその刻みのその体の判断の通し番号(``ctx.call_id`` から読む・
    ``ctx.wake_class`` は使わない=−1)。"""

    name = "contact-mock"

    def choose(self, ctx: DecisionContext, candidates: Sequence[Candidate]) -> Choice:
        """候補を並べ替えて番号を振り(用途名 ``contact.present``)、仮のモデルの答えを元の id に戻す。"""
        key = k19_counters(self.step_key(ctx.step), int(ctx.agent_id), _serial(ctx))
        presented = present(candidates, stream(self.seed, PRESENT_DOMAIN, *key))
        cid = self._pick(ctx, presented)
        for c in presented:
            if c.id == cid:
                return Choice(candidate_id=c.id, number=int(c.number or 0), kind=c.kind)
        raise ValueError(f"仮のモデルが提示に無い候補 {cid!r} を返した")

    def _draw(self, ctx: DecisionContext) -> int:
        """選びの乱数(用途名 ``contact.mock``・1 語)。"""
        return int(stream(self.seed, MOCK_DOMAIN, *k19_counters(self.step_key(ctx.step), int(ctx.agent_id),
                                                                _serial(ctx))).integers(0, 1 << 31))

    def _pick(self, ctx: DecisionContext, presented: tuple[Candidate, ...]) -> str:
        """中身で選ぶ(提示の並びは使わない): 候補を (語・id) の順に並べ、乱数の値を候補の数で割った余りの候補。"""
        cands = sorted(presented, key=lambda c: (c.kind, c.id))
        if not cands:
            return OTHER_ID
        return cands[self._draw(ctx) % len(cands)].id

    def _answer(self, ctx: DecisionContext, presented: tuple[Candidate, ...]) -> tuple[str, dict[str, Any]]:
        return self._pick(ctx, presented), {}


@dataclass(frozen=True)
class MockTextPort:
    """文の口の仮のモデル(LLM の口の代わり=定型の文 1 つ)。"""

    name: str = "mock-text"

    def write(self, *, kind: str, sender: int, addressees: Sequence[int]) -> str:
        return MOCK_TEXT


def habit_recheck_u(seed: int | str, step_key: int, agent: int, serial: int) -> float:
    """〔C2〕習慣で答えられるときに判断の口へ戻すかの一様乱数(用途名 ``contact.habit``・0 語目を空け 1〜3 語目に刻みの鍵・体・
    その刻みのその体の通し番号=k19_counters・1 語だけ引く)。"""
    v = int(stream(seed, HABIT_DOMAIN, *k19_counters(int(step_key), int(agent), int(serial))).integers(0, 1 << 31))
    return v / float(1 << 31)
