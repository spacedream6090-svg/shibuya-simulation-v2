"""engine.calendar2.port — カレンダー 2 の本人の判断(候補の口 J0 の形)の仮のモデルと候補の作り方(第 6 期 6-2)。

正: 決定 10-12 §4-1 CA3(約束を結ぶか・中身は本人の判断)・CA4・CA5 問い 2(モックは「そのまま」寄り=本段は一様)・CA7・CA11
(日付・曜日・祝日は全員が常識として知っている)・§4-4 CT2(文は LLM=仮のモデルは定型の文)・回答 2-1(GPU の前は仮のモデル)。
口の約束 1-8(候補の口 J0)。**エンジンは時刻も回数も決めない**: 候補は本人が知っていること(暦・今いる所・会話の相手・自分の
予定)から並べるだけ・どれを選ぶかは口(仮のモデル=候補から一様に選ぶ=構造だけ)。

- :class:`Calendar2Port`(``DecisionPort`` の子=同じ入口 ``choose(ctx, candidates)``): ``engine.contact.port.ContactPort`` と
  同じ形(候補を並べ替えて番号を振り・仮のモデルは中身で選ぶ=候補を (語・id) の順に並べ、乱数の値を候補の数で割った余り)。
  乱数は 10c の counter(用途名 ``calendar2.mock``・``calendar2.present``=動きの側・鍵=刻みの鍵・体・その刻みのその体の判断の
  通し番号)。
- 判断の呼びの ``call_id`` はテープの形 ``<刻み>:<体>:<−通し番号>``(連絡の判断と同じ形・通し番号は ``SERIAL_BASE`` から
  =連絡の判断の通し番号(< 2^18)とぶつからない)。通し番号=``SERIAL_BASE``+その刻みのその体の判断の数 k × 16+判断の種類。
- 判断の種類と候補(源は DM-0 の 5 つの源):

  | 判断 | 候補(源) |
  |---|---|
  | 会話の自分の番 | 約束を持ちかける(近い予定)・持ちかけない(続ける)・自分の約束を変える(近い予定=相手との自分の行があるとき) |
  | いつ(日) | 今日・明日・N 日後(曜日つき=暦の常識・7 日先まで) |
  | いつ(時刻) | その日の 0〜23 時の正時(今日は今より後だけ) |
  | 長さ | 1 時間・2 時間・3 時間・終わりは決めない |
  | どこで | ここ(今いるセル)・言葉で決める(地名帳に無い場所=文の口の言葉のまま) |
  | 誘いへの返事 | 受ける・仮で受ける・断る |
  | 返事を聞いた人の確かさ | 確定で書く・仮で書く |
  | 置き場所 | アプリに書く・アラームをかける・手帳に書く・覚えておく(頭の中) |
  | 知らせ(アプリとアラーム) | 始まりの 10/30/60 分前(アプリは知らせないも) |
  | 実行意図(頭の中) | 相手に会ったら確かめる・何もしない |
  | 見えた予定 | 出発する(近い予定)・まだ(続ける)・行かない(近い予定) |
  | 変える予定 | 自分の行のうち今見える行(会話の相手との行) |
  | 何を変える | 時刻を変える・場所を変える・確かさを変える・取り消す |

**未リサーチ(expedient)**(つなぎの台帳 ``DOC-ca2-port-candidates``): 候補の語と源の当て方・長さの候補(1/2/3 時間)・知らせの
候補(10/30/60 分前)・7 日先まで・正時だけ・仮のモデルの一様な選び方(判断モデル 6-1 の代わり=数は振る舞いのモデルではない)。

逐次ループ宣言: ``choose`` は候補の数ぶん(≤ 30)。
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Sequence

from shibuya.core.rng import k19_counters, stream
from shibuya.engine.decision.port import (
    OTHER_ID,
    SOURCE_CONTINUE,
    SOURCE_EXPERIENCE,
    SOURCE_PLAN,
    Candidate,
    Choice,
    DecisionContext,
    DecisionPort,
    present,
)

__all__ = [
    "MOCK_DOMAIN", "PRESENT_DOMAIN", "SERIAL_BASE", "MAX_DECISIONS_PER_STEP", "PURPOSES",
    "P_TURN", "P_DAY", "P_HOUR", "P_LENGTH", "P_PLACE", "P_RESPOND", "P_PLACEMENT", "P_NOTIFY", "P_INTENT", "P_GO",
    "P_EDIT", "P_EDIT_WHAT",
    "K_PROPOSE", "K_NO_PROPOSE", "K_CHANGE", "K_DAY", "K_HOUR", "K_LENGTH", "K_NO_END", "K_HERE", "K_WORDS",
    "K_ACCEPT", "K_TENTATIVE", "K_DECLINE", "K_PLACE_APP", "K_PLACE_ALARM", "K_PLACE_PLANNER", "K_PLACE_HEAD",
    "K_LEAD", "K_NO_NOTIFY", "K_INTENT", "K_NO_INTENT", "K_DEPART", "K_NOT_YET", "K_NOT_GO", "K_ROW",
    "K_EDIT_TIME", "K_EDIT_PLACE", "K_EDIT_CERTAIN", "K_EDIT_CANCEL", "K_FIRM", "K_TENT",
    "LENGTH_HOURS", "NOTIFY_LEAD_MIN", "HORIZON_DAYS", "PLACEMENT_OF_KIND", "PROVISIONAL_VALUES",
    "cand", "serial_of", "purpose_of_serial", "call_id_of", "parse_call_id", "Calendar2Port",
]

#: 仮のモデルの選びの乱数の用途名(動きの側=``engine.run.MOTION_RNG_DOMAINS``)。
MOCK_DOMAIN: Final[str] = "calendar2.mock"
#: 候補の提示の並べ替えの乱数の用途名(動きの側)。
PRESENT_DOMAIN: Final[str] = "calendar2.present"
#: 通し番号の始まり(連絡の判断の通し番号 < 2^18 とぶつからない)。
SERIAL_BASE: Final[int] = 1 << 20
#: 1 体 1 刻みの判断の数の上限(通し番号がぶつからない形の安全装置=当たったら ``ValueError``)。
MAX_DECISIONS_PER_STEP: Final[int] = 1 << 14

# ---- 判断の種類 ----
(P_TURN, P_DAY, P_HOUR, P_LENGTH, P_PLACE, P_RESPOND, P_PLACEMENT, P_NOTIFY, P_INTENT, P_GO, P_EDIT,
 P_EDIT_WHAT) = range(1, 13)
PURPOSES: Final = MappingProxyType({
    P_TURN: "turn", P_DAY: "day", P_HOUR: "hour", P_LENGTH: "length", P_PLACE: "place", P_RESPOND: "respond",
    P_PLACEMENT: "placement", P_NOTIFY: "notify", P_INTENT: "intent", P_GO: "go", P_EDIT: "edit",
    P_EDIT_WHAT: "edit_what",
})

# ---- 候補の語 ----
K_PROPOSE, K_NO_PROPOSE, K_CHANGE = "約束を持ちかける", "持ちかけない", "自分の約束を変える"
K_DAY, K_HOUR, K_LENGTH, K_NO_END = "日", "時刻", "長さ", "終わりは決めない"
K_HERE, K_WORDS = "ここ", "言葉で決める"
K_ACCEPT, K_TENTATIVE, K_DECLINE = "受ける", "仮で受ける", "断る"
K_PLACE_APP, K_PLACE_ALARM, K_PLACE_PLANNER, K_PLACE_HEAD = "アプリに書く", "アラームをかける", "手帳に書く", "覚えておく"
K_LEAD, K_NO_NOTIFY = "知らせ", "知らせない"
K_INTENT, K_NO_INTENT = "相手に会ったら確かめる", "何もしない"
K_DEPART, K_NOT_YET, K_NOT_GO = "出発する", "まだ", "行かない"
K_ROW = "変える予定"
K_EDIT_TIME, K_EDIT_PLACE, K_EDIT_CERTAIN, K_EDIT_CANCEL = "時刻を変える", "場所を変える", "確かさを変える", "取り消す"
#: 〔検収 L1〕返事を聞いた人が自分の行の確かさを選ぶ候補。
K_FIRM, K_TENT = "確定で書く", "仮で書く"

#: 長さの候補[時間](``K_NO_END`` を足す)。
LENGTH_HOURS: Final[tuple[int, ...]] = (1, 2, 3)
#: 知らせの候補[分前](アプリは ``K_NO_NOTIFY`` を足す)。
NOTIFY_LEAD_MIN: Final[tuple[int, ...]] = (10, 30, 60)
#: いつ(日)の候補の先[日](今日=0 から HORIZON_DAYS−1 日後まで)。
HORIZON_DAYS: Final[int] = 7
#: 置き場所の候補の語 → 置き場所の番号(``engine.calendar2.book.PLACEMENTS`` の並び)。
PLACEMENT_OF_KIND: Final = MappingProxyType({K_PLACE_APP: 0, K_PLACE_ALARM: 1, K_PLACE_PLANNER: 2, K_PLACE_HEAD: 3})

#: 本モジュールの仮の値の宣言(つなぎの台帳 DOC-ca2-port-candidates と 1 対 1)。
PROVISIONAL_VALUES: Final[tuple[str, ...]] = (
    "判断の候補の語と源の当て方(会話の番 3・いつ 2 段・長さ・どこで・返事 3・置き場所 4・知らせ・実行意図・見えた予定 3・変える)",
    "長さの候補 1/2/3 時間と終わりは決めない・知らせの候補 10/30/60 分前・いつは 7 日先まで・正時だけ",
    "仮のモデル(mock)は候補を語と id の順に並べ乱数の余りで一様に選ぶ(判断モデルの代わり)",
)

_SOURCE_OF: Final = MappingProxyType({
    K_PROPOSE: SOURCE_PLAN, K_NO_PROPOSE: SOURCE_CONTINUE, K_CHANGE: SOURCE_PLAN,
    K_DAY: SOURCE_PLAN, K_HOUR: SOURCE_PLAN, K_LENGTH: SOURCE_PLAN, K_NO_END: SOURCE_PLAN,
    K_HERE: SOURCE_EXPERIENCE, K_WORDS: SOURCE_EXPERIENCE,
    K_ACCEPT: SOURCE_PLAN, K_TENTATIVE: SOURCE_PLAN, K_DECLINE: SOURCE_CONTINUE,
    K_PLACE_APP: SOURCE_EXPERIENCE, K_PLACE_ALARM: SOURCE_EXPERIENCE, K_PLACE_PLANNER: SOURCE_EXPERIENCE,
    K_PLACE_HEAD: SOURCE_EXPERIENCE, K_LEAD: SOURCE_EXPERIENCE, K_NO_NOTIFY: SOURCE_CONTINUE,
    K_INTENT: SOURCE_PLAN, K_NO_INTENT: SOURCE_CONTINUE,
    K_DEPART: SOURCE_PLAN, K_NOT_YET: SOURCE_CONTINUE, K_NOT_GO: SOURCE_PLAN,
    K_ROW: SOURCE_EXPERIENCE,
    K_EDIT_TIME: SOURCE_PLAN, K_EDIT_PLACE: SOURCE_PLAN, K_EDIT_CERTAIN: SOURCE_PLAN, K_EDIT_CANCEL: SOURCE_PLAN,
    K_FIRM: SOURCE_PLAN, K_TENT: SOURCE_PLAN,
})


def cand(kind: str, text: str | None = None, *, id: str | None = None,
         basis: Sequence[tuple[int, int]] = ()) -> Candidate:
    """候補 1 つ(源は語から・見せ方の文は省略で語そのもの・id は省略で語)。"""
    return Candidate(id=id or kind, kind=kind, text=text or kind, source=_SOURCE_OF[kind], basis=tuple(basis))


def serial_of(purpose: int, k: int) -> int:
    """判断の通し番号(``SERIAL_BASE``+その刻みのその体の k 回目 × 16+判断の種類)。上限を超えたら ``ValueError``。"""
    if not (1 <= int(purpose) < 16):
        raise ValueError(f"判断の種類 {purpose} が表の外")
    if not (1 <= int(k) < MAX_DECISIONS_PER_STEP):
        raise ValueError(f"1 体 1 刻みのカレンダー 2 の判断の数が上限 {MAX_DECISIONS_PER_STEP} に当たった(k={k})")
    return SERIAL_BASE + int(k) * 16 + int(purpose)


def purpose_of_serial(serial: int) -> int:
    return (int(serial) - SERIAL_BASE) % 16


def call_id_of(step: int, agent: int, serial: int) -> str:
    """判断の呼びの id(テープの形 ``<刻み>:<体>:<−通し番号>``)。"""
    if int(serial) < SERIAL_BASE:
        raise ValueError("通し番号は SERIAL_BASE から")
    return f"{int(step)}:{int(agent)}:{-int(serial)}"


def parse_call_id(call_id: str) -> tuple[int, int, int] | None:
    """カレンダー 2 の判断の呼びの id → ``(刻み, 体, 通し番号)``(この形でなければ ``None``)。"""
    parts = str(call_id).split(":")
    if len(parts) != 3:
        return None
    try:
        t, a, c = (int(x) for x in parts)
    except ValueError:
        return None
    if f"{t}:{a}:{c}" != str(call_id) or t < 0 or a < 0 or -c < SERIAL_BASE:
        return None
    return t, a, -c


def _serial(ctx: DecisionContext) -> int:
    got = parse_call_id(ctx.call_id)
    if got is None:
        raise ValueError(f"カレンダー 2 の判断の呼びの id でない: {ctx.call_id!r}")
    return got[2]


class Calendar2Port(DecisionPort):
    """カレンダー 2 の判断の仮のモデル(mock・判断モデルの代わり)。乱数の鍵はその刻みのその体の判断の通し番号。"""

    name = "calendar2-mock"

    def choose(self, ctx: DecisionContext, candidates: Sequence[Candidate]) -> Choice:
        """候補を並べ替えて番号を振り(用途名 ``calendar2.present``)、仮のモデルの答えを元の id に戻す。"""
        key = k19_counters(self.step_key(ctx.step), int(ctx.agent_id), _serial(ctx))
        presented = present(candidates, stream(self.seed, PRESENT_DOMAIN, *key))
        cid = self._pick(ctx, presented)
        for c in presented:
            if c.id == cid:
                return Choice(candidate_id=c.id, number=int(c.number or 0), kind=c.kind)
        raise ValueError(f"仮のモデルが提示に無い候補 {cid!r} を返した")

    def _draw(self, ctx: DecisionContext) -> int:
        """選びの乱数(用途名 ``calendar2.mock``・1 語)。"""
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
