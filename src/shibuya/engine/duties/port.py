"""engine.duties.port — 店の仕事の本人の判断(候補の口 J0 の形)の仮のモデルと候補の語(第 6 期 6-6 ② 第 1 部)。

正: 決定 10-12 §1-5(② 他の人の仕事をエンジンが代わりにしている=働く人のエージェントへ)・§1-4(人の手続きはコードに書かない=
住人の知識から出す)・回答 2-1(GPU の前は仮のモデル)。口の約束 1-8(候補の口 J0)。**エンジンは時刻も中身も決めない**: 候補は
本人が知っていること(店の決まり=営業時間・店の中の気づき=棚が減った・自分が閉めた店)から並べるだけ・どれを選ぶかは口
(仮のモデル=候補から一様に選ぶ=構造だけ)。

- :class:`DutiesPort`(``DecisionPort`` の子=同じ入口 ``choose(ctx, candidates)``): ``engine.calendar3.port.Calendar3Port`` と
  同じ形(候補を並べ替えて番号を振り・仮のモデルは中身で選ぶ=候補を (語・id) の順に並べ、乱数の値を候補の数で割った余り)。
  乱数は 10c の counter(用途名 ``duties.mock``・``duties.present``=動きの側・鍵=刻みの鍵・体・その刻みのその体の判断の
  通し番号)。
- 判断の呼びの ``call_id`` はテープの形 ``<刻み>:<体>:<−通し番号>``(連絡の判断=< 2^18・カレンダー 2=2^20 から・カレンダー 3=
  2^21 から 2^18 の幅・本段=``SERIAL_BASE``=2^22 から=どれともぶつからない)。通し番号=``SERIAL_BASE``+その刻みのその体の
  判断の数 k × 16+種類。
- 候補の語(``kind``)は語彙 v3 の役割語(``開閉店``・``補充``・``接客``)と安全弁の語 ``なし``(まだ・待つ)+本段の語 ``廃棄``
  (役割語に無い=閉じた表 :data:`KINDS`)。判断モデルや LLM の口が役割語で答えたとき候補に写せる形(``LlmPort`` は答えの語を
  候補の語に当てる)。

  | 判断 | 誰が | 候補(源) |
  |---|---|---|
  | 開閉 | 店に居る担当 | 店を開ける/店を閉める(近い予定=店の決まり)・まだ(続ける) |
  | 補充 | 店に居る担当(棚が減った気づき) | 棚に補充する(周りが示すできること)・接客する・待つ(続ける) |
  | 廃棄 | 自分が閉めた店に居る担当 | 売れ残りを捨てる(近い予定=閉店の作業)・まだ(続ける) |

**未リサーチ(expedient)**(つなぎの台帳 ``DOC-du1-port-candidates``): 候補の語と源の当て方・仮のモデルの一様な選び方(判断
モデル 6-1 の代わり=数は振る舞いのモデルではない)。

逐次ループ宣言: ``choose`` は候補の数ぶん(≤ 4)。
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Sequence

from shibuya.core.rng import k19_counters, stream
from shibuya.engine.decision.port import (
    OTHER_ID,
    SOURCE_AFFORDANCE,
    SOURCE_CONTINUE,
    SOURCE_PLAN,
    Candidate,
    Choice,
    DecisionContext,
    DecisionPort,
    present,
)
from shibuya.llm.contract import ACTION_WORD_NONE

__all__ = [
    "MOCK_DOMAIN", "PRESENT_DOMAIN", "SERIAL_BASE", "MAX_DECISIONS_PER_STEP", "PURPOSES", "P_SHOP", "P_SHELF",
    "P_WASTE", "K_SHOP", "K_RESTOCK", "K_SERVE", "K_WAIT", "K_DISCARD", "KINDS", "ROLE_KINDS", "ID_UNLOCK", "ID_LOCK",
    "PROVISIONAL_VALUES", "cand", "serial_of", "purpose_of_serial", "call_id_of", "parse_call_id", "DutiesPort",
]

#: 仮のモデルの選びの乱数の用途名(動きの側=``engine.run.MOTION_RNG_DOMAINS``)。
MOCK_DOMAIN: Final[str] = "duties.mock"
#: 候補の提示の並べ替えの乱数の用途名(動きの側)。
PRESENT_DOMAIN: Final[str] = "duties.present"
#: 通し番号の始まり(連絡・カレンダー 2・カレンダー 3 の判断とぶつからない)。
SERIAL_BASE: Final[int] = 1 << 22
#: 1 体 1 刻みの判断の数の上限(通し番号がぶつからない形の安全装置=当たったら ``ValueError``)。
MAX_DECISIONS_PER_STEP: Final[int] = 1 << 14

# ---- 判断の種類 ----
P_SHOP, P_SHELF, P_WASTE = range(1, 4)
PURPOSES: Final = MappingProxyType({P_SHOP: "shop", P_SHELF: "shelf", P_WASTE: "waste"})

# ---- 候補の語(語彙 v3 の役割語と安全弁の語+本段の語) ----
K_SHOP = "開閉店"
K_RESTOCK = "補充"
K_SERVE = "接客"
K_WAIT = ACTION_WORD_NONE
K_DISCARD = "廃棄"
#: 候補の語の閉じた表(仮のモデルの語彙=この外の語は候補にしない)。
KINDS: Final[tuple[str, ...]] = (K_SHOP, K_RESTOCK, K_SERVE, K_WAIT, K_DISCARD)
#: 主の判断の役割語のうち本段で効く語(``engine.llm_bridge.LLMBridge.role_sink`` に渡す語=腕 arm のランだけ)。
ROLE_KINDS: Final[frozenset[str]] = frozenset({K_SHOP, K_RESTOCK})
#: 開閉の候補の id(店を開ける・店を閉める)。
ID_UNLOCK, ID_LOCK = "unlock", "lock"

#: 本モジュールの仮の値の宣言(つなぎの台帳 DOC-du1-port-candidates と 1 対 1)。
PROVISIONAL_VALUES: Final[tuple[str, ...]] = (
    "判断の候補の語と源の当て方(開閉=店を開ける/店を閉める/まだ・補充=棚に補充する/接客する/待つ・廃棄=売れ残りを捨てる/まだ)",
    "仮のモデル(mock)は候補を語と id の順に並べ乱数の余りで一様に選ぶ(判断モデルの代わり)",
)

_SOURCE_OF: Final = MappingProxyType({
    K_SHOP: SOURCE_PLAN, K_RESTOCK: SOURCE_AFFORDANCE, K_SERVE: SOURCE_CONTINUE, K_WAIT: SOURCE_CONTINUE,
    K_DISCARD: SOURCE_PLAN,
})


def cand(kind: str, text: str, *, id: str | None = None, basis: Sequence[tuple[int, int]] = ()) -> Candidate:
    """候補 1 つ(源は語から・id は省略で語)。語が閉じた表の外なら ``KeyError``。"""
    return Candidate(id=id or kind, kind=kind, text=text, source=_SOURCE_OF[kind], basis=tuple(basis))


def serial_of(purpose: int, k: int) -> int:
    """判断の通し番号(``SERIAL_BASE``+その刻みのその体の k 回目 × 16+判断の種類)。上限を超えたら ``ValueError``。"""
    if not (1 <= int(purpose) < 16):
        raise ValueError(f"判断の種類 {purpose} が表の外")
    if not (1 <= int(k) < MAX_DECISIONS_PER_STEP):
        raise ValueError(f"1 体 1 刻みの店の仕事の判断の数が上限 {MAX_DECISIONS_PER_STEP} に当たった(k={k})")
    return SERIAL_BASE + int(k) * 16 + int(purpose)


def purpose_of_serial(serial: int) -> int:
    return (int(serial) - SERIAL_BASE) % 16


def call_id_of(step: int, agent: int, serial: int) -> str:
    """判断の呼びの id(テープの形 ``<刻み>:<体>:<−通し番号>``)。"""
    if int(serial) < SERIAL_BASE:
        raise ValueError("通し番号は SERIAL_BASE から")
    return f"{int(step)}:{int(agent)}:{-int(serial)}"


def parse_call_id(call_id: str) -> tuple[int, int, int] | None:
    """店の仕事の判断の呼びの id → ``(刻み, 体, 通し番号)``(この形でなければ ``None``)。"""
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
        raise ValueError(f"店の仕事の判断の呼びの id でない: {ctx.call_id!r}")
    return got[2]


class DutiesPort(DecisionPort):
    """店の仕事の判断の仮のモデル(mock・判断モデルの代わり)。乱数の鍵はその刻みのその体の判断の通し番号。"""

    name = "duties-mock"

    def choose(self, ctx: DecisionContext, candidates: Sequence[Candidate]) -> Choice:
        """候補を並べ替えて番号を振り(用途名 ``duties.present``)、仮のモデルの答えを元の id に戻す。"""
        key = k19_counters(self.step_key(ctx.step), int(ctx.agent_id), _serial(ctx))
        presented = present(candidates, stream(self.seed, PRESENT_DOMAIN, *key))
        cid = self._pick(ctx, presented)
        for c in presented:
            if c.id == cid:
                return Choice(candidate_id=c.id, number=int(c.number or 0), kind=c.kind)
        raise ValueError(f"仮のモデルが提示に無い候補 {cid!r} を返した")

    def _draw(self, ctx: DecisionContext) -> int:
        """選びの乱数(用途名 ``duties.mock``・1 語)。"""
        return int(stream(self.seed, MOCK_DOMAIN, *k19_counters(self.step_key(ctx.step), int(ctx.agent_id),
                                                                _serial(ctx))).integers(0, 1 << 31))

    def _pick(self, ctx: DecisionContext, presented: tuple[Candidate, ...]) -> str:
        """中身で選ぶ(提示の並びは使わない): 閉じた表の語の候補を (語・id) の順に並べ、乱数の値を候補の数で割った余り。"""
        cands = sorted((c for c in presented if c.kind in KINDS), key=lambda c: (c.kind, c.id))
        if not cands:
            return OTHER_ID
        return cands[self._draw(ctx) % len(cands)].id

    def _answer(self, ctx: DecisionContext, presented: tuple[Candidate, ...]) -> tuple[str, dict[str, Any]]:
        return self._pick(ctx, presented), {}
