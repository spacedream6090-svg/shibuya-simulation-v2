"""engine.calendar3.port — カレンダー 3 の本人の判断(候補の口 J0 の形)の仮のモデルと候補の語(第 6 期 6-2・雇い主・C3)。

正: 決定 10-12 §4-1 CA1(「正規雇用は毎週固定、非正規とシフト勤務は週ごとにします(雇い主がエージェントになるまでのつなぎ)」
「休むかどうかは本人の判断」)・CA11(日付・曜日・祝日は全員が常識として知っている)・§4-4 CT1 の C3(職場の連絡)・CT2(送るかと
宛先は判断・文は LLM=仮のモデルは定型の文)・回答 2-1(GPU の前は仮のモデル)。口の約束 1-8(候補の口 J0)。**エンジンは時刻も
中身も決めない**: 候補は本人が知っていること(W20 の約束の形の枠・暦・自分の予定・届いた連絡)から並べるだけ・どれを選ぶかは
口(仮のモデル=候補から一様に選ぶ=構造だけ)。

- :class:`Calendar3Port`(``DecisionPort`` の子=同じ入口 ``choose(ctx, candidates)``): ``engine.calendar2.port.Calendar2Port`` と
  同じ形(候補を並べ替えて番号を振り・仮のモデルは中身で選ぶ=候補を (語・id) の順に並べ、乱数の値を候補の数で割った余り)。
  乱数は 10c の counter(用途名 ``calendar3.mock``・``calendar3.present``=動きの側・鍵=刻みの鍵・体・その刻みのその体の判断の
  通し番号)。
- 判断の呼びの ``call_id`` はテープの形 ``<刻み>:<体>:<−通し番号>``(連絡の判断=< 2^18・カレンダー 2 の判断=2^20 から 2^18 の
  幅・本段=``SERIAL_BASE``=2^21 から=どれともぶつからない)。通し番号=``SERIAL_BASE``+その刻みのその体の判断の数 k × 16+種類。
- 判断の種類と候補(源は DM-0 の 5 つの源):

  | 判断 | 誰が | 候補(源) |
  |---|---|---|
  | その日の枠 | 雇い主(シフトを組む人) | 休み(続ける)・W20 の約束の形の枠 1 つずつ(近い予定=始業〜終業) |
  | 知らせ | 働く人(届いたシフトを書く) | 始まりの 10/30/60 分前・知らせない(カレンダー 2 の候補と同じ) |
  | 休みの申し出 | 働く人 | 休みを申し出る(近い予定)・申し出ない(続ける) |
  | 休みたい日 | 働く人 | 書いたシフトの行 1 つずつ(経験=自分の予定) |
  | 申し出への返事 | 雇い主 | 受ける・断る(近い予定) |
  | 返事を受けて | 働く人 | 自分の行を休みにする(近い予定)・そのまま(続ける) |
  | 知らせの時 | 働く人(勤め先に居ないとき) | 遅れると連絡する(近い予定)・このまま(続ける) |

**未リサーチ(expedient)**(つなぎの台帳 ``DOC-ca3-port-candidates``): 候補の語と源の当て方・仮のモデルの一様な選び方(判断
モデル 6-1 の代わり=数は振る舞いのモデルではない)。

逐次ループ宣言: ``choose`` は候補の数ぶん(≤ 8 か書いた行の数)。
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
    "P_FRAME", "P_NOTIFY", "P_REST", "P_REST_DAY", "P_ANSWER", "P_APPLY", "P_LATE",
    "K_DAY_OFF", "K_FRAME", "K_LEAD", "K_NO_NOTIFY", "K_ASK_REST", "K_NO_ASK", "K_ROW", "K_ACCEPT", "K_DECLINE",
    "K_APPLY", "K_KEEP", "K_LATE", "K_AS_IS", "PROVISIONAL_VALUES",
    "cand", "serial_of", "purpose_of_serial", "call_id_of", "parse_call_id", "Calendar3Port",
]

#: 仮のモデルの選びの乱数の用途名(動きの側=``engine.run.MOTION_RNG_DOMAINS``)。
MOCK_DOMAIN: Final[str] = "calendar3.mock"
#: 候補の提示の並べ替えの乱数の用途名(動きの側)。
PRESENT_DOMAIN: Final[str] = "calendar3.present"
#: 通し番号の始まり(連絡の判断 < 2^18・カレンダー 2 の判断 2^20〜2^20+2^18 とぶつからない)。
SERIAL_BASE: Final[int] = 1 << 21
#: 1 体 1 刻みの判断の数の上限(通し番号がぶつからない形の安全装置=当たったら ``ValueError``)。
MAX_DECISIONS_PER_STEP: Final[int] = 1 << 14

# ---- 判断の種類 ----
P_FRAME, P_NOTIFY, P_REST, P_REST_DAY, P_ANSWER, P_APPLY, P_LATE = range(1, 8)
PURPOSES: Final = MappingProxyType({
    P_FRAME: "frame", P_NOTIFY: "notify", P_REST: "rest", P_REST_DAY: "rest_day", P_ANSWER: "answer",
    P_APPLY: "apply", P_LATE: "late",
})

# ---- 候補の語 ----
K_DAY_OFF, K_FRAME = "休み", "枠"
K_LEAD, K_NO_NOTIFY = "知らせ", "知らせない"
K_ASK_REST, K_NO_ASK = "休みを申し出る", "申し出ない"
K_ROW = "休みたい日"
K_ACCEPT, K_DECLINE = "受ける", "断る"
K_APPLY, K_KEEP = "自分の行を休みにする", "そのまま"
K_LATE, K_AS_IS = "遅れると連絡する", "このまま"

#: 本モジュールの仮の値の宣言(つなぎの台帳 DOC-ca3-port-candidates と 1 対 1)。
PROVISIONAL_VALUES: Final[tuple[str, ...]] = (
    "判断の候補の語と源の当て方(その日の枠・知らせ・休みの申し出・休みたい日・返事・返事を受けて・遅れの連絡)",
    "仮のモデル(mock)は候補を語と id の順に並べ乱数の余りで一様に選ぶ(判断モデルの代わり)",
)

_SOURCE_OF: Final = MappingProxyType({
    K_DAY_OFF: SOURCE_CONTINUE, K_FRAME: SOURCE_PLAN,
    K_LEAD: SOURCE_EXPERIENCE, K_NO_NOTIFY: SOURCE_CONTINUE,
    K_ASK_REST: SOURCE_PLAN, K_NO_ASK: SOURCE_CONTINUE, K_ROW: SOURCE_EXPERIENCE,
    K_ACCEPT: SOURCE_PLAN, K_DECLINE: SOURCE_PLAN,
    K_APPLY: SOURCE_PLAN, K_KEEP: SOURCE_CONTINUE,
    K_LATE: SOURCE_PLAN, K_AS_IS: SOURCE_CONTINUE,
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
        raise ValueError(f"1 体 1 刻みのカレンダー 3 の判断の数が上限 {MAX_DECISIONS_PER_STEP} に当たった(k={k})")
    return SERIAL_BASE + int(k) * 16 + int(purpose)


def purpose_of_serial(serial: int) -> int:
    return (int(serial) - SERIAL_BASE) % 16


def call_id_of(step: int, agent: int, serial: int) -> str:
    """判断の呼びの id(テープの形 ``<刻み>:<体>:<−通し番号>``)。"""
    if int(serial) < SERIAL_BASE:
        raise ValueError("通し番号は SERIAL_BASE から")
    return f"{int(step)}:{int(agent)}:{-int(serial)}"


def parse_call_id(call_id: str) -> tuple[int, int, int] | None:
    """カレンダー 3 の判断の呼びの id → ``(刻み, 体, 通し番号)``(この形でなければ ``None``)。"""
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
        raise ValueError(f"カレンダー 3 の判断の呼びの id でない: {ctx.call_id!r}")
    return got[2]


class Calendar3Port(DecisionPort):
    """カレンダー 3 の判断の仮のモデル(mock・判断モデルの代わり)。乱数の鍵はその刻みのその体の判断の通し番号。"""

    name = "calendar3-mock"

    def choose(self, ctx: DecisionContext, candidates: Sequence[Candidate]) -> Choice:
        """候補を並べ替えて番号を振り(用途名 ``calendar3.present``)、仮のモデルの答えを元の id に戻す。"""
        key = k19_counters(self.step_key(ctx.step), int(ctx.agent_id), _serial(ctx))
        presented = present(candidates, stream(self.seed, PRESENT_DOMAIN, *key))
        cid = self._pick(ctx, presented)
        for c in presented:
            if c.id == cid:
                return Choice(candidate_id=c.id, number=int(c.number or 0), kind=c.kind)
        raise ValueError(f"仮のモデルが提示に無い候補 {cid!r} を返した")

    def _draw(self, ctx: DecisionContext) -> int:
        """選びの乱数(用途名 ``calendar3.mock``・1 語)。"""
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
