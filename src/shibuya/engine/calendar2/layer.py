"""engine.calendar2.layer — カレンダー 2「会話とメッセージから生まれる予定」の持ち主と系 ``calendar_2``(第 6 期 6-2・腕
``--calendar-2 arm``・既定 off)。

正: 決定 10-12 §4-1 CA2 (c)(d)(初めの個人の予定=本人がランの始まりに書く・慣らし期間で人との約束が生まれる・統計は検証だけ)・
CA3(二人の約束=各自が自分の理解の行・変えられるのは自分の行だけ・変更は最新値と出来事の記録への 1 行・置き場所・確かさ・元の
会話・頭の中だけの予定も保管し記憶で思い出せたときだけ見せる・計器=1 人 1 週間の約束の数と誘いを受けた/断った割合)・CA4 (d)
(壊れた予定だけ拒む・本人に見せるのは置き場所の道具が現実に教えることだけ=アプリなら重なりの警告・間に合わない/閉店中は記録
だけ・地名帳に無い場所は言葉のまま)・CA6 (b)(範囲外の過ごし方=本人の計画・置き場所=頭の中)・CA7(アラームと時刻の実行意図は
同じ種類・上限なし・出来事がきっかけのものは計画の記憶)・CA8(計器・合否なし)・CA9(段 2=会話とメッセージ・C1 と束ねる)・CA11
(日付・曜日・祝日は常識)・§4-4 CT0(使用は全部出来事の記録へ)・§4-2 TM3(会話)・§2 の 1(人の手続きはコードに書かず住人の知識
から)・回答 2-1(GPU の前に腕で)。口の約束 1-3(出来事の記録)・1-8(候補の口 J0)。記録
``docs/bench/analysis/wallbounce-1012/ca2/README.md``。

持ち主 :class:`Calendar2Layer`(道筋 ``calendar2``・状態台帳の腕の行 ``CA2*``=腕 arm のランだけ持ち主がある=既定のランの 2 つの
ハッシュと状態のファイルは不変)。子の持ち主 ``book``(本人の予定の器=:class:`engine.calendar2.book.PromiseBook`)。

流れ(系 ``calendar_2``=刻みの中・連絡の系の後・記憶の系の前):

1. **会話の番**(口 :meth:`Calendar2Layer.note_turn`=対面の会話の番の発話 ``engine.systems.llm_io.utter``・通話の番と
   メッセージを送る判断 ``engine.contact.layer``(腕 c1 のラン)が控えに積む): その番の話し手 A は (a) その会話で A に宛てた
   返事待ちの誘いに返事をする(受ける/仮で受ける/断る=受けたら自分の行を書く)(b) 自分が出した誘いの返事が全部そろって
   いれば聞いて自分の行を書く(c) 自分の番の判断=約束を持ちかける/持ちかけない/自分の約束を変える。持ちかけたら、いつ(日と
   時刻)・長さ・どこで(ここ/言葉)を選び、何をは文の口(仮のモデル=定型の文)。誘いは会話の鍵に付く(会話の番の id=元の会話)。
2. **会話の終わり**: 誘いの会話が終わったら、返事のあった誘いは出した人が聞いて自分の行を書く・返事の無い誘いは消える
   (返事なし)。
3. **書く**(:meth:`_write_own`): 置き場所を選び(アプリ/アラーム/手帳/頭の中)・アプリとアラームは知らせの時刻を選び・頭の中は
   出来事がきっかけの実行意図(相手に会ったら確かめる)を持つか選ぶ。壊れた予定だけ拒む(道具の語 ``拒んだ``・アプリは本人に
   教える)。間に合わない・閉店中は記録だけ。アプリは重なりを警告する(数える)。アラームは同じ種類の行(結びつく行=約束)。
4. **見える・出発する**: 本人が考えた刻み(主の判断の呼びのあった刻み=仲裁で次の刻み)と、本人が選んだ知らせの時刻(アプリの
   通知・アラーム=道具が鳴る=寝ていれば起きたときに見る)に、その日の自分の予定のうち置き場所の性質で見える行(アプリ=知らせ
   か画面・手帳=その日に開いた最初の回・頭の中=記憶で思い出せたとき=:mod:`engine.calendar2.recall`・相手が同じ所に居れば
   手がかり・出来事の実行意図のきっかけ)について「出発する/まだ/行かない」。出発=約束の場所のセルへ歩く(体の基本動作
   ``engine.resolve.begin_walk_to``)。**エンジンは時刻も回数も決めない**(機会は本人が考えた刻みと本人が選んだ知らせの時刻だけ・
   逆算して起こさない)。
5. **範囲外の過ごし方**(CA6 (b)): 体が範囲の外に出た刻みに、本人が範囲外の過ごし方を本人の計画(頭の中)に書くか選ぶ(何を
   は文の口)。実行は今のまま(範囲外の食事の予定・W17 の行)=1b の出入りの判断と W17 の行の関係を壊さない。戻ったら締める。
6. **初めの個人の予定**(CA2 (c)): ランの始まりに本人が自分の予定を書く口 :meth:`write_initial`(仮のモデル=空で始める=
   つなぎ ``DOC-ca2-initial-empty``)。慣らし期間で人との約束が生まれるのは 1 の仕組み。統計は検証にだけ使う(錨は読まない)。
7. **計器**(CA8・合否なし): 約束の数(1 人 1 週間)・誘いを受けた/仮で受けた/断った/返事なしの割合・初めの予定の頻度・忘れた
   割合(置き場所ごと)・5 分前到着・間に合った・遅刻・着かなかった・計画一致率(始まりの刻みに約束の場所に居た割合)・不可能な
   予定(間に合わない・閉店中=書いたときと出発のとき)・メッセージを読むまでの時間(連絡の道具 C1 の計器を読むだけ=重ねない)・
   範囲外の計画の数。manifest の ``calendar_2``(腕のランだけ)。

記録(CT0 の 5・CA3): 族 ``約束`` の語。本人の語の原因は判断の呼び(``LlmCall``=テープの形の call_id・選んだ候補の源と番号)・
道具の語(``拒んだ``・``知らせ``)の原因は過程 ``calendar2``。監査 :func:`audit_causes` は発行した判断の呼びの控え(腕の行
``CA2Q``)と突き合わせる(``engine.contact.layer.audit_causes`` と同じ形)。

仲裁(``ARBITRATION``=宣言): 見える予定の判断(出発する/まだ/行かない)は、その刻みに主の判断の呼びのあった体ではしない(主の
判断が先=次の刻みに回す=連絡の道具 C1 と同じ規則)。会話の番の判断(誘う・返事・書く・変える)はその番の中身=主の判断と同じ
刻み(番の呼びと別の呼び=GPU の後は番の LLM の出力に畳む)。

**未リサーチ(expedient)**(記録 §仮採用・つなぎの台帳 ``DOC-ca2-*``): 誘いの機会=会話の自分の番ごと・返事は相手の次の番・出した
人が聞くのは自分の次の番か会話の終わり・見える予定はその日の行だけ・アプリは連絡の道具の無いランでは考えたとき見える(ある
ランは画面を見ているとき)・手帳はその日に最初に考えたとき・範囲外の過ごし方の機会=範囲の外に出た刻み・5 分前到着の 5 分は
CA8 の計器の定義。

逐次ループ宣言(新設・P4): 系 ``calendar_2`` は (a) その刻みの会話の番の数ぶん(番ごとの判断=会話の数で決まる)・(b) 生きている
誘いの数ぶん・(c) 考えた体と知らせの数ぶん(その体の行の数ぶん)・(d) その刻みに始まり/終わる行と歩いている行の数ぶん・(e) その
刻みに範囲の外に出た/戻った体の数ぶん。体ごとの範囲の外の印は配列演算。体の数に比例する Python のループは無い。
"""

from __future__ import annotations

import math
from types import MappingProxyType
from typing import Any, Final, Iterable, Mapping, Sequence

import numpy as np

from shibuya.agents.state import Activity
from shibuya.core.time_consts import HOURS_PER_DAY, NS_PER_SECOND, SECONDS_PER_HOUR, SECONDS_PER_MINUTE
from shibuya.engine import resolve as R
from shibuya.engine.calendar2 import arm as _ARM
from shibuya.engine.calendar2 import book as _B
from shibuya.engine.calendar2 import port as _P
from shibuya.engine.calendar2.recall import IMPORTANCE_HEAD, HeadRecall
from shibuya.engine.decision.port import Candidate, DecisionContext
from shibuya.engine.events import vocab as V
from shibuya.engine.events.log import Event, LlmCall, Process
from shibuya.llm.mock import MOCK_UTTERANCE

__all__ = [
    "SCHEMA", "CONFIG_KEYS", "OBSERVED_KEYS", "ARBITRATION", "EARLY_MIN", "W_OFFER", "W_ACCEPT", "W_TENTATIVE",
    "W_DECLINE", "W_WRITE", "W_EDIT_TIME", "W_EDIT_PLACE", "W_EDIT_CERTAIN", "W_CANCEL", "W_REJECT", "W_DEPART",
    "W_NOT_GO", "W_NOTIFY", "PERSON_WORDS", "ENGINE_WORDS", "WORD_PURPOSES", "VIA_OF_KEY", "Calendar2Layer",
    "sys_calendar_2", "manifest_fields", "audit_causes", "issued_key", "P_OUTSIDE", "EDIT_MAX_CANDIDATES",
    "OFFER_GRACE_STEPS", "P_CERTAIN",
]

#: manifest の ``calendar_2`` の形の版。
SCHEMA: Final[str] = "shibuya.engine.calendar2/1"

# ---- 出来事の記録の語(族 約束=1-3 の語彙表の末尾に足した語) ----
W_OFFER = V.word(V.FAMILY_PROMISE, "誘った")
W_ACCEPT = V.word(V.FAMILY_PROMISE, "受けた")
W_TENTATIVE = V.word(V.FAMILY_PROMISE, "仮で受けた")
W_DECLINE = V.word(V.FAMILY_PROMISE, "断った")
W_WRITE = V.word(V.FAMILY_PROMISE, "書いた")
W_EDIT_TIME = V.word(V.FAMILY_PROMISE, "時刻を変えた")
W_EDIT_PLACE = V.word(V.FAMILY_PROMISE, "場所を変えた")
W_EDIT_CERTAIN = V.word(V.FAMILY_PROMISE, "確かさを変えた")
W_CANCEL = V.word(V.FAMILY_PROMISE, "取り消した")
W_REJECT = V.word(V.FAMILY_PROMISE, "拒んだ")
W_DEPART = V.word(V.FAMILY_PROMISE, "出発した")
W_NOT_GO = V.word(V.FAMILY_PROMISE, "行かない")
W_NOTIFY = V.word(V.FAMILY_PROMISE, "知らせ")

#: 範囲外の過ごし方を書くかの判断の種類(``engine.calendar2.port`` の 12 の後ろ)。
P_OUTSIDE: Final[int] = 13
#: 〔検収 L1〕返事を聞いた人が自分の行の確かさ(確定/仮)を選ぶ判断の種類。
P_CERTAIN: Final[int] = 14
_PURPOSE_NAMES: Final = MappingProxyType({**dict(_P.PURPOSES), P_OUTSIDE: "outside", P_CERTAIN: "certain"})
#: 範囲外の過ごし方の候補の語。
K_OUTSIDE, K_NO_OUTSIDE = "範囲外の過ごし方を決めておく", "決めない"

#: 本人の判断の語(原因は LlmCall でなければならない=負の対照の監査)。
PERSON_WORDS: Final[frozenset[str]] = frozenset({W_OFFER, W_ACCEPT, W_TENTATIVE, W_DECLINE, W_WRITE, W_EDIT_TIME,
                                                 W_EDIT_PLACE, W_EDIT_CERTAIN, W_CANCEL, W_DEPART, W_NOT_GO})
#: 道具の語(原因は過程 calendar2)。
ENGINE_WORDS: Final[frozenset[str]] = frozenset({W_REJECT, W_NOTIFY})
#: 本人の語 → 合う判断の種類(監査の突き合わせ)。
WORD_PURPOSES: Final[Mapping[str, frozenset[int]]] = MappingProxyType({
    W_OFFER: frozenset({_P.P_TURN}), W_ACCEPT: frozenset({_P.P_RESPOND}), W_TENTATIVE: frozenset({_P.P_RESPOND}),
    W_DECLINE: frozenset({_P.P_RESPOND}), W_WRITE: frozenset({_P.P_PLACEMENT, _P.P_NOTIFY, _P.P_INTENT, P_OUTSIDE}),
    W_EDIT_TIME: frozenset({_P.P_EDIT_WHAT}), W_EDIT_PLACE: frozenset({_P.P_EDIT_WHAT}),
    W_EDIT_CERTAIN: frozenset({_P.P_EDIT_WHAT}), W_CANCEL: frozenset({_P.P_EDIT_WHAT}),
    W_DEPART: frozenset({_P.P_GO}), W_NOT_GO: frozenset({_P.P_GO}),
})
#: 仲裁の規則(宣言=実装は :meth:`Calendar2Layer._opportunities`)。
ARBITRATION: Final = MappingProxyType({
    "main_first": "見える予定の判断(出発する/まだ/行かない)は、その刻みに主の判断の呼びのあった体ではしない(次の刻みに回す)",
    "turn_content": "会話の番の判断(誘う・返事・書く・変える)はその番の中身=番と同じ刻みの別の呼び(GPU の後は番の出力に畳む)",
})
#: 5 分前到着の分(CA8 の計器の定義「5 分前到着」)。
EARLY_MIN: Final[int] = 5
#: 変える予定の候補の数の上限(〔検収 L4〕候補=見える行の全部・これは提示の番号の上限 127 の下の安全装置だけ=
#: 当たったら数える=manifest の ``changes.candidates_capped``)。候補が 127 を超えると口の番号の欄に入らない=始まりの
#: 近い順に上限まで。
EDIT_MAX_CANDIDATES: Final[int] = 120
#: 〔検収 L2〕返事の無い誘いの会話が一度も生きていないとき(送ったメッセージは次の窓の境目でチャットの会話になる)に
#: 待つ刻みの数(これを過ぎたら消す)=つなぎ ``DOC-ca2-offer-grace``(外す段=実 LLM の段 6-2)。
OFFER_GRACE_STEPS: Final[int] = 2

_P_CAL2: Final[Process] = Process("calendar2")
#: 会話の鍵の頭 → 道具の語(CT9)。
VIA_OF_KEY: Final = MappingProxyType({"f": "対面", "c": "通話", "p": "メッセージ", "g": "グループ"})
#: 書く行の答えの番号(返事)。
_ANS_DECLINE, _ANS_TENTATIVE, _ANS_ACCEPT = 0, 1, 2
_ANSWER_WORDS: Final = MappingProxyType({_ANS_DECLINE: W_DECLINE, _ANS_TENTATIVE: W_TENTATIVE, _ANS_ACCEPT: W_ACCEPT})
_ANSWER_OF_KIND: Final = MappingProxyType({_P.K_ACCEPT: _ANS_ACCEPT, _P.K_TENTATIVE: _ANS_TENTATIVE,
                                           _P.K_DECLINE: _ANS_DECLINE})
#: 予定の帳面の事象の種類(知らせ・始まり・終わり)。
_AG_NOTIFY, _AG_START, _AG_END = 0, 1, 2
_TRANSIT_OUTSIDE: Final[int] = 2

#: manifest の ``calendar_2`` の設定の子と観測の子(``engine.manifest_sections`` の混ざった辞書)。
CONFIG_KEYS: Final[tuple[str, ...]] = (
    "schema", "arm", "port", "placements", "kinds", "certainty", "candidates", "recall", "early_min", "arbitration",
    "provisional")
OBSERVED_KEYS: Final[tuple[str, ...]] = (
    "meter", "decisions", "promises", "responses", "initial", "forgot", "arrival", "plan_match", "impossible",
    "read_delay_minutes", "outside_plan", "intentions", "rejected", "changes", "live_rows", "calls")

#: 発行した判断の呼びの控えの詰め方(刻み 22 ビット・体 20 ビット・通し番号−SERIAL_BASE 21 ビット)。
_ISS_T_SHIFT, _ISS_A_SHIFT = 41, 21
_ISS_MAX_T, _ISS_MAX_A, _ISS_MAX_S = 1 << 22, 1 << 20, 1 << 21


def issued_key(step: int, agent: int, serial: int) -> int:
    t, a, c = int(step), int(agent), int(serial) - _P.SERIAL_BASE
    if not (0 <= t < _ISS_MAX_T and 0 <= a < _ISS_MAX_A and 0 <= c < _ISS_MAX_S):
        raise ValueError(f"判断の呼びの控えの範囲の外: 刻み {t}・体 {a}・通し番号 {serial}")
    return (t << _ISS_T_SHIFT) | (a << _ISS_A_SHIFT) | c


class Calendar2Layer:
    """カレンダー 2 の持ち主(状態台帳の腕の行 ``CA2*``)。"""

    LEDGER_ARM: Final[str] = _ARM.LEDGER_ARM

    def __init__(self, *, n_agents: int, seed: int | str, population_seed: int | str, day_key0: int,
                 step_seconds: int, steps_per_day: int, events: Any, agents: Any, world: Any, calendar: Any = None,
                 conv: Any = None, contact: Any = None, runner: Any = None, hop_steps: Any = None) -> None:
        #: 〔第 5 期 空間の段 1・検収 M5〕節 1 つを歩く刻み(体ごと)。None=1 刻み 1 節(legacy=B8)・nav1 は本人の歩く速さから
        self.hop_steps = None if hop_steps is None else np.asarray(hop_steps, dtype=np.float64)
        self.n = int(n_agents)
        self.step_seconds = int(step_seconds)
        self.step_ns = self.step_seconds * NS_PER_SECOND
        self.steps_per_day = int(steps_per_day)
        self.day_ns = self.steps_per_day * self.step_ns
        # ---- 参照 ----
        self.events = events
        self.agents = agents
        self.world = world
        self.calendar = calendar
        self.conv = conv
        self.contact = contact
        self.runner = runner
        # ---- 口(参照・設定) ----
        self.port = _P.Calendar2Port(seed=seed, day_key0=int(day_key0), step_seconds=self.step_seconds)
        self.recall = HeadRecall(self.n, population_seed)
        # ---- 子の持ち主(本人の予定の器=腕の行 CA2B) ----
        self.book = _B.PromiseBook()
        # ---- 状態(腕の行 CA2O=誘いと帳面・CA2G=系の間と刻みの間に渡す値) ----
        #: 誘いの番号 → 誘い(出した人・宛先・会話の鍵・道具・会話の番の id・中身・返事・聞いたか)。
        self._offers: dict[int, dict[str, Any]] = {}
        self._offer_next: list[int] = [0]
        #: 刻み → ``[[種類, 行], …]``(本人が選んだ知らせの時刻・行の始まりと終わり=道具と計器の帳面)。
        self._agenda: dict[int, list[list[int]]] = {}
        #: 出発して約束の場所に着いていない行(到着を見る)。
        self._watch: list[int] = []
        #: その刻みの会話の番の控え ``[[会話の鍵, 体, 刻み, 番の id, [相手]], …]``(系の間=刻みの境目では空)。
        self._turns: list[list[Any]] = []
        #: 主の判断が先だったので次の刻みに回した「考えた」体 → 考えた刻み(仲裁)。
        self._think: dict[int, int] = {}
        #: 知らせで次に考えたときに見える行(体 → 行の列)=寝ていて鳴ったアラームを起きたときに見る。
        self._noticed: dict[int, list[int]] = {}
        #: 体 → 手帳を最後に開いた日。
        self._planner_day: dict[int, int] = {}
        #: 前の刻みに範囲の外に居た体(体ごと)と範囲外の計画の行(体 → 行)。
        self._was_out: np.ndarray = np.zeros(0, dtype=bool)
        self._out_row: dict[int, int] = {}
        # ---- 計器(腕の行 CA2M=診断・再開でも通しと同じ) ----
        self._c2_meter: dict[str, int] = {}
        self._c2_hist: dict[str, dict[str, int]] = {"arrive_minus_start_min": {}}
        #: 体 → 書いた二人の約束の数(1 人 1 週間の約束の数の素)。
        self._c2_per_agent: dict[int, int] = {}
        #: 〔検収 M3〕行の番号 → 書いた出来事の id・誘いの番号 → 誘った出来事の id(記録の有無で行と誘いが変わらないよう
        #: 診断の表に分けた=返事の判断の入力の目印=原因の表だけが読む)。
        self._c2_event_of: dict[int, list[int]] = {}
        self._c2_offer_event: dict[int, list[int]] = {}
        #: 計器の日の数(日の頭の数)。
        self._days: list[int] = [0, -1]
        # ---- 発行した判断の呼びの控えと呼び数(腕の行 CA2Q=監査) ----
        self._c2_issued: np.ndarray = np.zeros(1024, dtype=np.int64)
        #: ``[控えの数, 判断の呼び(判断モデル), 文の口の呼び(LLM)]``。
        self._c2_issued_n: list[int] = [0, 0, 0]
        # ---- 刻みの中の作業の値 ----
        self._codes: dict[int, int] = {}

    # ================================================================== 小さな口
    def _bump(self, key: str, n: int = 1) -> None:
        self._c2_meter[key] = self._c2_meter.get(key, 0) + int(n)

    def _hist_add(self, name: str, v: int) -> None:
        h = self._c2_hist[name]
        k = str(int(v))
        h[k] = h.get(k, 0) + 1

    def _log(self, t_ns: int, who: int, what: str, cause: Any, *, whom: Any = None, via: str = V.VIA_NONE,
             how_much: int | None = None) -> list[int] | None:
        """出来事の記録へ 1 行(記録が off のランは何もしない)。書く口はこれ 1 つ。"""
        log = self.events
        if log is None or not bool(getattr(log, "enabled", False)):
            return None
        cell = int(self.agents.registry.cell[int(who)])
        eid = log.append(Event(t_ns=int(t_ns), who=int(who), what=what, whom=whom,
                               where=("cell", cell) if cell >= 0 else None, how_much=how_much, via=via, cause=cause))
        if eid is not None:
            self._bump(f"events:{what}")
        return None if eid is None else [int(eid[0]), int(eid[1])]

    def _decide(self, T: int, t_ns: int, a: int, purpose: int, cands: Sequence[Candidate]) -> tuple[Candidate, LlmCall]:
        """本人の判断 1 回(候補の口 J0 の形・仮のモデル)。選んだ候補と原因(LlmCall)を返す。"""
        k = self._codes.get(a, 0) + 1
        self._codes[a] = k
        serial = _P.serial_of(purpose, k)
        cell = int(self.agents.registry.cell[a])
        ctx = DecisionContext(agent_id=int(a), step=int(T), t_ns=int(t_ns), wake_class=-1, condition=-1, cell=cell,
                              call_id=_P.call_id_of(T, a, serial))
        ch = self.port.choose(ctx, cands)
        self._issue(T, a, serial)
        self._c2_issued_n[1] += 1
        c = next(x for x in cands if x.id == ch.candidate_id)
        basis = tuple(sorted({b for x in cands for b in x.basis}))
        self._bump(f"decisions:{_PURPOSE_NAMES[purpose]}")
        self._bump(f"chosen:{c.kind}")
        return c, LlmCall(ctx.call_id, basis, source=c.source, number=int(ch.number))

    def _issue(self, T: int, a: int, serial: int) -> None:
        n = int(self._c2_issued_n[0])
        if n >= self._c2_issued.size:
            grown = np.zeros(self._c2_issued.size * 2, dtype=np.int64)
            grown[:n] = self._c2_issued[:n]
            self._c2_issued = grown
        self._c2_issued[n] = issued_key(T, a, serial)
        self._c2_issued_n[0] = n + 1

    def _text(self, kind: str) -> str:
        """文の口(LLM の口の代わり=定型の文)。呼び数を数える。"""
        self._c2_issued_n[2] += 1
        self._bump(f"text:{kind}")
        return str(MOCK_UTTERANCE)

    def issued_keys(self) -> np.ndarray:
        """発行した判断の呼びの控え(写し・監査の道具が読む)。"""
        return self._c2_issued[: int(self._c2_issued_n[0])].copy()

    def model_calls(self) -> tuple[int, int]:
        """カレンダー 2 の呼び数 ``(判断の呼び=判断モデル, 文の口=LLM)``。"""
        return int(self._c2_issued_n[1]), int(self._c2_issued_n[2])

    def _note_event(self, rid: int, eid: list[int] | None) -> None:
        """〔検収 M3〕書いた出来事の id を診断の表に置く(記録が off なら何もしない=行は記録に依らない)。"""
        if eid is not None:
            self._c2_event_of[int(rid)] = [int(eid[0]), int(eid[1])]

    def _drop(self, rid: int) -> None:
        """締めた行を器から落とす(診断の表の目印も)。"""
        self.book.drop(int(rid))
        self._c2_event_of.pop(int(rid), None)

    def _drop_offer(self, oid: int) -> None:
        del self._offers[int(oid)]
        self._c2_offer_event.pop(int(oid), None)

    def _notify_step(self, row: Mapping[str, Any]) -> int:
        """知らせが鳴る刻み(本人が選んだ時刻・書いた刻みの次より前にはしない)。"""
        return max(self._step_of(int(row["notify_ns"])), self._step_of(int(row["written_ns"])) + 1)

    def _at(self, step: int, code: int, rid: int) -> None:
        self._agenda.setdefault(int(step), []).append([int(code), int(rid)])

    def _step_of(self, t_ns: int) -> int:
        return int(t_ns) // self.step_ns

    def _end_step(self, row: Mapping[str, Any]) -> int:
        """行を締める刻み(終わりの刻み・終わりを決めていない行は始まりの日の最後の刻み)。"""
        if int(row["end_ns"]) >= 0:
            return max(self._step_of(int(row["end_ns"])), self._step_of(int(row["start_ns"])))
        d = int(row["start_ns"]) // self.day_ns
        return (d + 1) * self.steps_per_day - 1

    # ================================================================== 口(ほかの系から)
    def note_turn(self, key: str, agent: int, step: int, call_id: str, partners: Iterable[int]) -> None:
        """会話の番の控え(対面の会話の番の発話・通話の番・メッセージを送る判断=ほかの系が呼ぶ)。読むのは系 calendar_2。"""
        self._turns.append([str(key), int(agent), int(step), str(call_id or ""),
                            sorted({int(p) for p in partners if int(p) != int(agent)})])

    def write_initial(self, T: int, t_ns: int) -> int:
        """〔CA2 (c)〕ランの始まりに本人が自分の予定を書く口。仮のモデルは空で始める(つなぎ ``DOC-ca2-initial-empty``)。
        書いた行の数を返す(本段は 0)。統計(錨)は読まない=検証にだけ使う。"""
        n = 0
        self._bump("initial_offered", self.n)
        self._bump("initial_rows", n)
        return n

    # ================================================================== 1 刻み(系 calendar_2 の本体)
    def run_step(self, T: int, t_ns: int, td: int, day: int, *, agents: Any, world: Any, decision: Any) -> None:
        self._codes.clear()
        reg = agents.registry
        cells = np.asarray(reg.cell, dtype=np.int64)
        sleeping = np.asarray(reg.activity, dtype=np.int64) == int(Activity.SLEEPING)
        if int(self._days[1]) != int(day):  # 日の頭(計器の日の数)
            if int(self._days[1]) < 0:
                self.write_initial(T, t_ns)
            self._days[1] = int(day)
            self._days[0] += 1
        # ---- 1. 会話の番 ----
        turns, self._turns = self._turns, []
        for key, a, _st, cid, partners in turns:  # 逐次ループ宣言 (a): その刻みの会話の番の数ぶん
            self._on_turn(T, t_ns, td, day, str(key), int(a), str(cid), [int(p) for p in partners], cells)
        # ---- 2. 会話の終わった誘い ----
        self._settle_offers(T, t_ns)
        # ---- 3. 範囲外の過ごし方(CA6 (b)) ----
        self._outside(T, t_ns, np.asarray(reg.transit_state, dtype=np.int64))
        # ---- 4. 見える予定・出発する(仲裁=主の判断が先) ----
        self._opportunities(T, t_ns, day, cells, sleeping, decision)
        # ---- 5. 着いたか・始まり・終わり(計器) ----
        self._track(T, t_ns, cells)

    # ---------------------------------------------------------------- 1. 会話の番
    def _session_alive(self, key: str) -> bool:
        head, _, rest = key.partition(":")
        if head == "f":
            s = None if self.conv is None else self.conv.sessions.get(int(rest))
            return s is not None and bool(s.active)
        if self.contact is None:
            return False
        if head == "c":
            s = self.contact.calls.sessions.get(int(rest))
            return s is not None and bool(s.active)
        s = self.contact.chats.session(key)
        return s is not None and bool(s.active)

    def _on_turn(self, T: int, t_ns: int, td: int, day: int, key: str, a: int, cid: str, partners: list[int],
                 cells: np.ndarray) -> None:
        via = VIA_OF_KEY.get(key.partition(":")[0], V.VIA_NONE)
        for oid in sorted(self._offers):  # 逐次: 生きている誘いの数ぶん
            off = self._offers[oid]
            if off["key"] == key and a in off["to"] and int(a) not in off["answers"] and int(off["from"]) != a:
                self._respond(T, t_ns, a, off)
        for oid in sorted(self._offers):  # 逐次: 生きている誘いの数ぶん(出した人が聞く=返事が全部そろった誘い)
            off = self._offers[oid]
            if (off["key"] == key and int(off["from"]) == a and not off["heard"]
                    and set(off["to"]) <= set(off["answers"])):
                self._hear(T, t_ns, off)
        own = self._changeable(T, t_ns, day, a, partners, cells)
        cands = [_P.cand(_P.K_PROPOSE), _P.cand(_P.K_NO_PROPOSE)] + ([_P.cand(_P.K_CHANGE)] if own else [])
        c, cause = self._decide(T, t_ns, a, _P.P_TURN, cands)
        self._bump(f"turns:{via}")
        if c.kind == _P.K_PROPOSE and partners:
            self._propose(T, t_ns, td, day, a, via, key, cid, partners, cells, cause)
        elif c.kind == _P.K_CHANGE:
            self._change(T, t_ns, td, day, a, own, cells)

    def _changeable(self, T: int, t_ns: int, day: int, a: int, partners: list[int],
                    cells: np.ndarray) -> list[dict[str, Any]]:
        """〔検収 M2〕変えられる自分の行=会話の相手との自分の行のうち、置き場所の性質で今見える行だけ(``_visible`` と同じ
        口=頭の中は思い出せたとき・手帳はその日にまだ開いていないとき(開くのはその日に最初に考えたとき=``_look``・会話の番の
        確かめは開いた印を付けない=仮採用 ``DOC-ca2-visibility``)・アプリは見えるとき・アラームは鳴った後)。"""
        noticed = set(self._noticed.get(a, []))
        out = []
        for r in self.book.own_rows(a):  # 逐次: 持ち主の行の数ぶん
            if not (r["kind"] == _B.K_PROMISE and r["state"] == _B.ST_LIVE and not r["closed"]
                    and any(int(w) in partners for w in r["with"])):
                continue
            if self._visible(T, t_ns, day, a, r, cells, noticed, set(), probe=True):
                out.append(r)
        return out

    def _day_cands(self, td: int, day: int) -> list[Candidate]:
        """いつ(日)の候補=今日から 7 日先まで(曜日と祝日は暦の常識=CA11)。今日は今より後の正時があるときだけ。"""
        tod_s = int(td) * self.step_seconds
        out = []
        for k in range(_P.HORIZON_DAYS):  # 逐次: 7 日
            if k == 0 and (HOURS_PER_DAY - 1) * SECONDS_PER_HOUR <= tod_s:
                continue
            label = "今日" if k == 0 else ("明日" if k == 1 else f"{k} 日後")
            if self.calendar is not None:
                wd = "月火水木金土日"[int(self.calendar.weekday(int(day) + k))]
                hol = "・祝日" if bool(self.calendar.is_holiday(int(day) + k)) else ""
                label = f"{label}({wd}{hol})"
            out.append(_P.cand(_P.K_DAY, label, id=f"day:{k}"))
        return out

    def _hour_cands(self, td: int, k: int) -> list[Candidate]:
        tod_s = int(td) * self.step_seconds
        return [_P.cand(_P.K_HOUR, f"{h} 時", id=f"hour:{h}") for h in range(HOURS_PER_DAY)
                if int(k) > 0 or h * SECONDS_PER_HOUR > tod_s]

    def _when(self, T: int, t_ns: int, td: int, day: int, a: int) -> int | None:
        """いつ(日と時刻)を本人が選ぶ → 始まりの時刻[ns](候補が無ければ None)。"""
        days = self._day_cands(td, day)
        if not days:
            return None
        cd, _c = self._decide(T, t_ns, a, _P.P_DAY, days)
        k = int(cd.id.split(":", 1)[1])
        ch, _c = self._decide(T, t_ns, a, _P.P_HOUR, self._hour_cands(td, k))
        h = int(ch.id.split(":", 1)[1])
        return (int(day) + k) * self.day_ns + h * SECONDS_PER_HOUR * NS_PER_SECOND

    def _where(self, T: int, t_ns: int, a: int, cells: np.ndarray) -> tuple[int, str]:
        """どこで(ここ=今いるセル・言葉で決める=地名帳に無い場所は言葉のまま)を本人が選ぶ → (セル, 言葉)。"""
        cands = ([_P.cand(_P.K_HERE, id="here")] if int(cells[a]) >= 0 else []) + [_P.cand(_P.K_WORDS)]
        c, _c = self._decide(T, t_ns, a, _P.P_PLACE, cands)
        if c.kind == _P.K_HERE:
            return int(cells[a]), ""
        return -1, self._text("place")

    def _propose(self, T: int, t_ns: int, td: int, day: int, a: int, via: str, key: str, cid: str,
                 partners: list[int], cells: np.ndarray, cause: LlmCall) -> None:
        start = self._when(T, t_ns, td, day, a)
        if start is None:
            self._bump("propose_no_time")
            return
        lens = [_P.cand(_P.K_LENGTH, f"{h} 時間", id=f"len:{h}") for h in _P.LENGTH_HOURS] + [_P.cand(_P.K_NO_END)]
        cl, _c = self._decide(T, t_ns, a, _P.P_LENGTH, lens)
        end = -1 if cl.kind == _P.K_NO_END else start + int(cl.id.split(":", 1)[1]) * SECONDS_PER_HOUR * NS_PER_SECOND
        cell, place = self._where(T, t_ns, a, cells)
        what = self._text("what")
        oid = int(self._offer_next[0])
        self._offer_next[0] = oid + 1
        whom: Any = (f"group:{key.partition(':')[2]}" if key.startswith("g:")
                     else (int(partners[0]) if partners else None))
        eid = self._log(t_ns, a, W_OFFER, cause, whom=whom, via=via, how_much=oid)
        if eid is not None:
            self._c2_offer_event[oid] = [int(eid[0]), int(eid[1])]
        self._offers[oid] = {
            "id": oid, "from": int(a), "to": [int(p) for p in partners], "key": key, "via": via, "turn": cid,
            "made_T": int(T), "content": {"start_ns": int(start), "end_ns": int(end), "cell": int(cell),
                                          "place": str(place), "what": str(what)},
            "answers": {}, "heard": 0, "alive_seen": 0,
        }
        self._bump("offers")
        self._bump(f"offers:{via}")

    def _respond(self, T: int, t_ns: int, a: int, off: dict[str, Any]) -> None:
        eid = self._c2_offer_event.get(int(off["id"]))
        basis = (tuple(eid),) if eid is not None else ()
        cands = [_P.cand(_P.K_ACCEPT, basis=basis), _P.cand(_P.K_TENTATIVE, basis=basis),
                 _P.cand(_P.K_DECLINE, basis=basis)]
        c, cause = self._decide(T, t_ns, a, _P.P_RESPOND, cands)
        ans = _ANSWER_OF_KIND[c.kind]
        off["answers"][int(a)] = int(ans)
        self._log(t_ns, a, _ANSWER_WORDS[ans], cause, whom=int(off["from"]), via=str(off["via"]), how_much=int(off["id"]))
        self._bump(f"answers:{c.kind}")
        if ans != _ANS_DECLINE:
            others = [int(off["from"])] + [int(p) for p in off["to"] if int(p) != a]
            self._write_own(T, t_ns, a, dict(off["content"]), others, 1 if ans == _ANS_ACCEPT else 0,
                            origin=[str(off["via"]), str(off["key"]), str(off["turn"])], offer=int(off["id"]))

    def _hear(self, T: int, t_ns: int, off: dict[str, Any]) -> None:
        """出した人が返事を聞いて自分の行を書く(受けた/仮で受けた相手がいれば)。"""
        off["heard"] = 1
        acc = [int(p) for p, v in sorted(off["answers"].items()) if int(v) != _ANS_DECLINE]
        if not acc:
            self._bump("offers_all_declined")
            return
        a = int(off["from"])
        cc, _c = self._decide(T, t_ns, a, P_CERTAIN, [_P.cand(_P.K_FIRM), _P.cand(_P.K_TENT)])
        certain = 1 if cc.kind == _P.K_FIRM else 0
        self._bump(f"heard_certainty:{_B.CERTAINTY[certain]}")
        self._write_own(T, t_ns, a, dict(off["content"]), acc, certain,
                        origin=[str(off["via"]), str(off["key"]), str(off["turn"])], offer=int(off["id"]))

    # ---------------------------------------------------------------- 2. 会話の終わり
    def _settle_offers(self, T: int, t_ns: int) -> None:
        for oid in sorted(self._offers):  # 逐次ループ宣言 (b): 生きている誘いの数ぶん
            off = self._offers[oid]
            if self._session_alive(str(off["key"])):
                off["alive_seen"] = 1
                if off["heard"] and set(off["to"]) <= set(off["answers"]):
                    self._drop_offer(oid)
                continue
            if not off["alive_seen"] and int(T) - int(off["made_T"]) <= OFFER_GRACE_STEPS:
                continue  # 送ったメッセージは次の窓の境目でチャットの会話になる(つなぎ DOC-ca2-offer-grace)
            if off["answers"] and not off["heard"]:
                self._hear(T, t_ns, off)
            if not off["answers"]:
                self._bump("offers_no_answer")
            n_wait = len(set(off["to"]) - set(off["answers"]))
            if n_wait:
                self._bump("answers:返事なし", n_wait)
            self._drop_offer(oid)

    # ---------------------------------------------------------------- 3. 書く
    def _write_own(self, T: int, t_ns: int, a: int, content: dict[str, Any], with_: list[int], certain: int, *,
                   origin: list[str] | None, offer: int, kind: int = _B.K_PROMISE) -> int | None:
        """本人 a が自分の理解の行を書く(置き場所・知らせ・実行意図は本人の判断)。"""
        cp, cause = self._decide(T, t_ns, a, _P.P_PLACEMENT, [
            _P.cand(_P.K_PLACE_APP), _P.cand(_P.K_PLACE_ALARM), _P.cand(_P.K_PLACE_PLANNER), _P.cand(_P.K_PLACE_HEAD)])
        pl = int(_P.PLACEMENT_OF_KIND[cp.kind])
        notify = -1
        n_cause = None
        if pl in (_B.PL_APP, _B.PL_ALARM):
            leads = [_P.cand(_P.K_LEAD, f"始まりの {m} 分前", id=f"lead:{m}") for m in _P.NOTIFY_LEAD_MIN]
            if pl == _B.PL_APP:
                leads.append(_P.cand(_P.K_NO_NOTIFY))
            cl, n_cause = self._decide(T, t_ns, a, _P.P_NOTIFY, leads)
            if cl.kind == _P.K_LEAD:
                notify = int(content["start_ns"]) - int(cl.id.split(":", 1)[1]) * SECONDS_PER_MINUTE * NS_PER_SECOND
        fields = {"kind": int(kind), "start_ns": int(content["start_ns"]), "end_ns": int(content["end_ns"]),
                  "cell": int(content["cell"]), "place": str(content["place"]), "with": [int(w) for w in with_],
                  "what": str(content["what"]), "placement": pl, "certain": int(certain), "origin": origin,
                  "offer": int(offer), "state": _B.ST_LIVE, "notify_ns": int(notify) if pl == _B.PL_APP else -1}
        whom = int(with_[0]) if with_ else None
        why = _B.broken(fields)
        if why is not None:  # CA4 (d): 壊れた予定だけ拒む(道具の性質)・本人に教えるのはアプリだけ
            self._log(t_ns, a, W_REJECT, _P_CAL2, whom=whom)
            self._bump(f"rejected:{why}")
            self._bump("rejected_shown" if pl == _B.PL_APP else "rejected_silent")
            return None
        self._impossible(T, t_ns, a, fields, at="write")
        if pl == _B.PL_APP and self._overlaps(a, fields):
            self._bump("overlap_warned")  # アプリが重なりを警告する(本人に見せる=記録だけ・書くのは本人)
        rid = self.book.write(a, fields, written_ns=t_ns)
        self._note_event(rid, self._log(t_ns, a, W_WRITE, cause, whom=whom, how_much=rid))
        if pl == _B.PL_HEAD:
            self.book.observe(rid, "trace", self.recall.new_trace(t_ns))
        self._schedule_row(rid, self._step_of(t_ns))
        self._bump(f"written:{_B.KINDS[kind]}:{_B.PLACEMENTS[pl]}")
        if kind == _B.K_PROMISE:
            self._c2_per_agent[int(a)] = self._c2_per_agent.get(int(a), 0) + 1
        if pl == _B.PL_ALARM and notify >= 0 and n_cause is not None:  # CA7: アラーム=時刻の実行意図と同じ種類の行(上限なし)
            alarm = {"kind": _B.K_ALARM, "start_ns": max(int(notify), int(t_ns)), "end_ns": -1, "cell": -1,
                     "place": "アラーム", "with": [], "what": "", "placement": _B.PL_ALARM, "certain": 1,
                     "origin": origin, "offer": int(offer), "state": _B.ST_LIVE, "notify_ns": max(int(notify), int(t_ns)),
                     "link": rid}
            ar = self.book.write(a, alarm, written_ns=t_ns)
            self._note_event(ar, self._log(t_ns, a, W_WRITE, n_cause, how_much=ar))
            self._schedule_row(ar, self._step_of(t_ns))
            self._bump("intentions:アラーム")
        if pl == _B.PL_HEAD and whom is not None:  # CA7: 出来事がきっかけの実行意図は計画の記憶(頭の中)
            ci, i_cause = self._decide(T, t_ns, a, _P.P_INTENT, [_P.cand(_P.K_INTENT), _P.cand(_P.K_NO_INTENT)])
            if ci.kind == _P.K_INTENT:
                intent = {"kind": _B.K_INTENT, "start_ns": int(t_ns), "end_ns": max(int(fields["start_ns"]), int(t_ns)),
                          "cell": -1, "place": "相手に会ったとき", "with": [whom], "what": "", "placement": _B.PL_HEAD,
                          "certain": 1, "origin": origin, "offer": int(offer), "state": _B.ST_LIVE, "link": rid,
                          "trigger": whom}
                ir = self.book.write(a, intent, written_ns=t_ns)
                self._note_event(ir, self._log(t_ns, a, W_WRITE, i_cause, whom=whom, how_much=ir))
                self._schedule_row(ir, self._step_of(t_ns))
                self._bump("intentions:出来事")
        return rid

    def _schedule_row(self, rid: int, now_step: int) -> None:
        """帳面に知らせ・始まり・終わりを置く(知らせの時刻は本人が選んだ値=道具が鳴る)。〔検収 M1〕``now_step`` より前の
        刻み(過ぎた刻み)には置かない・知らせは今の刻みより後だけ(帳面の古い印は取り出すときに今の行と照らして捨てる)。"""
        row = self.book.rows[int(rid)]
        if int(row["notify_ns"]) >= 0 and self._notify_step(row) > int(now_step):
            self._at(self._notify_step(row), _AG_NOTIFY, rid)
        if int(row["kind"]) in (_B.K_PROMISE, _B.K_OWN):
            st = max(self._step_of(int(row["start_ns"])), self._step_of(int(row["written_ns"])))
            if st >= int(now_step):
                self._at(st, _AG_START, rid)
        self._at(max(self._end_step(row), self._step_of(int(row["written_ns"])), int(now_step)), _AG_END, rid)

    def _overlaps(self, a: int, fields: Mapping[str, Any]) -> bool:
        s0 = int(fields["start_ns"])
        e0 = int(fields["end_ns"]) if int(fields["end_ns"]) >= 0 else s0
        for r in self.book.own_rows(a):  # 逐次: 持ち主の行の数ぶん
            if r["placement"] != _B.PL_APP or r["state"] != _B.ST_LIVE or r["closed"] or r["kind"] not in (
                    _B.K_PROMISE, _B.K_OWN):
                continue
            s1 = int(r["start_ns"])
            e1 = int(r["end_ns"]) if int(r["end_ns"]) >= 0 else s1
            if s0 <= e1 and s1 <= e0:
                return True
        return False

    def _impossible(self, T: int, t_ns: int, a: int, fields: Mapping[str, Any], *, at: str) -> None:
        """不可能な予定を数える(記録だけ=拒まない): 間に合わない(今の居場所から歩く節の数 × 節 1 つの刻み > 始まりまで・
        節 1 つの刻みは legacy で 1・nav1 で本人の歩く速さから)・閉店中。"""
        start = int(fields["start_ns"])
        cell = int(fields["cell"])
        if start <= int(t_ns):
            self._bump(f"impossible:{at}:過ぎた時刻")
            return
        if cell < 0:
            return
        node = int(self.agents.registry.node[a])
        dest = int(np.asarray(self.world.assets.cell_rep_node, dtype=np.int64)[cell])
        if node >= 0 and dest >= 0 and int(self.agents.registry.transit_state[a]) == 0:
            from shibuya.engine.calendar_self import hop_walk_steps, route_steps

            steps = int(route_steps(self.world, np.asarray([node]), np.asarray([dest]))[0])
            walk_ns = int(math.ceil(float(hop_walk_steps(np.asarray([steps]), self.hop_steps, [a])[0]))) * self.step_ns
            if steps >= 0 and int(t_ns) + walk_ns > start:
                self._bump(f"impossible:{at}:間に合わない")
        if self._closed_at(cell, start, int(t_ns) // self.day_ns):
            self._bump(f"impossible:{at}:閉店中")

    def _closed_at(self, cell: int, start_ns: int, today: int) -> bool:
        """〔検収 L8〕約束のセルの店がどれも始まりの分に開いていないか(**始まりの日の営業の表**で見る=今日なら今の表・
        ほかの日は W7 の区間からその日の行=暦の ``opening_row``)。店の無いセル・営業の表の無い世界は偽。"""
        op = getattr(self.runner, "opening", None)
        om = getattr(op, "open_matrix", None)
        if om is None or not getattr(om, "size", 0):
            return False
        pois = np.flatnonzero(np.asarray(self.world.pois.cell, dtype=np.int64) == int(cell))
        if pois.size == 0:
            return False
        sday = int(start_ns) // self.day_ns
        minute = int((int(start_ns) % self.day_ns) // (SECONDS_PER_MINUTE * NS_PER_SECOND))
        if sday == int(today) or self.calendar is None:
            return not bool(np.asarray(om)[pois, minute % np.asarray(om).shape[1]].any())
        from shibuya.engine.processes.opening import rows_of_day

        a = op.assets
        pp = np.asarray(a.plan_poi, dtype=np.int64)
        sel = rows_of_day(pp, np.asarray(a.plan_day), int(self.calendar.opening_row(sday)), a.plan_ph_poi)
        sel = sel & np.isin(pp, pois)
        s = np.asarray(a.plan_start, dtype=np.int64)[sel]
        e = np.asarray(a.plan_end, dtype=np.int64)[sel]
        day_min = self.day_ns // (SECONDS_PER_MINUTE * NS_PER_SECOND)
        ok = e > s
        inside = ((s <= minute) & (minute < e)) | ((e > day_min) & (minute < e - day_min))
        return not bool((ok & inside).any())

    # ---------------------------------------------------------------- 変える(自分の行だけ)
    def _change(self, T: int, t_ns: int, td: int, day: int, a: int, rows: list[dict[str, Any]],
                cells: np.ndarray) -> None:
        rows = sorted(rows, key=lambda r: (int(r["start_ns"]), int(r["id"])))
        # 〔検収 L4〕候補=見える行の全部。提示の番号の上限(127)を超えるときは、本人が先に日を選び、まだ多ければ時刻(正時)を
        # 選んで絞る(どれも P_EDIT の判断)。それでも超えたら安全装置(始まりの近い順に上限まで=当たったら数える)
        for unit, word, size in (("eday", "日", self.day_ns), ("ehour", "時", SECONDS_PER_HOUR * NS_PER_SECOND)):
            if len(rows) <= EDIT_MAX_CANDIDATES:
                break
            groups = sorted({int(r["start_ns"]) // size for r in rows})
            cg, _c = self._decide(T, t_ns, a, _P.P_EDIT, [
                _P.cand(_P.K_ROW, f"{g - (int(day) if unit == 'eday' else 0)} {word}", id=f"{unit}:{g}") for g in groups])
            g = int(cg.id.split(":", 1)[1])
            rows = [r for r in rows if int(r["start_ns"]) // size == g]
            self._bump(f"edit_narrowed:{unit}")
        if len(rows) > EDIT_MAX_CANDIDATES:  # 安全装置(提示の番号の上限 127 の下)=始まりの近い順に上限まで
            self._bump("edit_candidates_capped")
            rows = rows[:EDIT_MAX_CANDIDATES]
        cr, _c = self._decide(T, t_ns, a, _P.P_EDIT, [_P.cand(_P.K_ROW, f"予定 {r['id']}", id=f"row:{r['id']}")
                                                       for r in rows])
        rid = int(cr.id.split(":", 1)[1])
        row = self.book.rows[rid]
        if int(row["placement"]) == _B.PL_HEAD and row["trace"] is not None:  # 選んで使った頭の中の行=想起の練習
            self.book.observe(rid, "trace", self.recall.touch(row["trace"], t_ns))
        cw, cause = self._decide(T, t_ns, a, _P.P_EDIT_WHAT, [
            _P.cand(_P.K_EDIT_TIME), _P.cand(_P.K_EDIT_PLACE), _P.cand(_P.K_EDIT_CERTAIN), _P.cand(_P.K_EDIT_CANCEL)])
        whom = int(row["with"][0]) if row["with"] else None
        if cw.kind == _P.K_EDIT_TIME:
            start = self._when(T, t_ns, td, day, a)
            if start is None:
                self._bump("change_no_time")
                return
            delta = int(start) - int(row["start_ns"])
            self.book.edit(a, rid, "start_ns", int(start))
            if int(row["end_ns"]) >= 0:
                self.book.edit(a, rid, "end_ns", int(row["end_ns"]) + delta)
            if int(row["notify_ns"]) >= 0:  # 〔検収 M1〕アプリの知らせは予定について動く(道具の性質)
                self.book.edit(a, rid, "notify_ns", int(row["notify_ns"]) + delta)
            for al in self.book.own_rows(a):  # 逐次: 持ち主の行の数ぶん(結びつくアラームも同じだけずらす)
                if (al["kind"] == _B.K_ALARM and int(al["link"]) == rid and not al["closed"]
                        and al["state"] == _B.ST_LIVE):
                    self.book.edit(a, int(al["id"]), "start_ns", max(int(al["start_ns"]) + delta, int(t_ns)))
                    self.book.edit(a, int(al["id"]), "notify_ns", int(al["notify_ns"]) + delta)
                    self._schedule_row(int(al["id"]), int(T))
            self._log(t_ns, a, W_EDIT_TIME, cause, whom=whom, how_much=rid)
            self._schedule_row(rid, int(T))
            self._bump("changes:時刻")
        elif cw.kind == _P.K_EDIT_PLACE:
            cell, place = self._where(T, t_ns, a, cells)
            self.book.edit(a, rid, "cell", int(cell))
            self.book.edit(a, rid, "place", str(place))
            self._log(t_ns, a, W_EDIT_PLACE, cause, whom=whom, how_much=rid)
            self._bump("changes:場所")
        elif cw.kind == _P.K_EDIT_CERTAIN:
            self.book.edit(a, rid, "certain", 1 - int(row["certain"]))
            self._log(t_ns, a, W_EDIT_CERTAIN, cause, whom=whom, how_much=rid)
            self._bump("changes:確かさ")
        else:
            self.book.edit(a, rid, "state", _B.ST_CANCELLED)
            self._log(t_ns, a, W_CANCEL, cause, whom=whom, how_much=rid)
            self._bump("changes:取り消し")

    # ---------------------------------------------------------------- 3b. 範囲外の過ごし方(CA6 (b))
    def _outside(self, T: int, t_ns: int, transit: np.ndarray) -> None:
        out = transit == _TRANSIT_OUTSIDE
        if self._was_out.size != out.size:  # ランの始まり(初期の状態=範囲の外に居る体は書かない)
            self._was_out = out.copy()
            return
        left = np.flatnonzero(out & ~self._was_out)
        back = np.flatnonzero(~out & self._was_out)
        self._was_out = out.copy()
        for a in back.tolist():  # 逐次ループ宣言 (e): 戻った体の数ぶん
            rid = self._out_row.pop(int(a), None)
            if rid is not None and int(rid) in self.book.rows:
                self.book.observe(rid, "outcome", "戻った")
                self.book.observe(rid, "closed", 1)
                self._drop(rid)
                self._bump("outside_plan:戻った")
        for a in left.tolist():  # 逐次ループ宣言 (e): 範囲の外に出た体の数ぶん
            c, cause = self._decide(T, t_ns, int(a), P_OUTSIDE,
                                    [_P.cand(_P.K_NO_PROPOSE, K_NO_OUTSIDE, id="outside:no"),
                                     _P.cand(_P.K_PROPOSE, K_OUTSIDE, id="outside:yes")])
            self._bump("outside_plan:出た")
            if c.id != "outside:yes":
                continue
            fields = {"kind": _B.K_PLAN, "start_ns": int(t_ns), "end_ns": -1, "cell": -1, "place": "範囲の外",
                      "with": [], "what": self._text("outside"), "placement": _B.PL_HEAD, "certain": 1,
                      "state": _B.ST_LIVE}
            rid = self.book.write(int(a), fields, written_ns=t_ns)
            self._note_event(rid, self._log(t_ns, int(a), W_WRITE, cause, how_much=rid))
            self._out_row[int(a)] = rid
            self._bump("outside_plan:書いた")

    # ---------------------------------------------------------------- 4. 見える予定・出発する
    def _opportunities(self, T: int, t_ns: int, day: int, cells: np.ndarray, sleeping: np.ndarray,
                       decision: Any) -> None:
        sel = getattr(decision, "selected", None) if decision is not None else None
        main_now: set[int] = set()
        if sel is not None and len(sel):
            main_now = {int(x) for x in np.asarray(sel.agent_id, dtype=np.int64).tolist()}
        # 知らせ(本人が選んだ時刻に道具が鳴る)=鳴った行は次に考えたときに見える・起きている体は考える
        rung: set[int] = set()
        for code, rid in self._agenda.pop(int(T), []):  # 逐次ループ宣言 (c): その刻みの帳面の事象の数ぶん
            if code != _AG_NOTIFY or int(rid) not in self.book.rows:
                if code != _AG_NOTIFY:
                    self._agenda.setdefault(int(T), []).append([int(code), int(rid)])
                continue
            row = self.book.rows[int(rid)]
            if (row["closed"] or row["state"] != _B.ST_LIVE or int(row["notify_ns"]) < 0
                    or self._notify_step(row) != int(T) or int(rid) in rung):
                continue  # 〔検収 M1〕時刻を変えた行の古い印・同じ刻みの 2 つ目の印
            rung.add(int(rid))
            a = int(row["owner"])
            self._log(t_ns, a, W_NOTIFY, _P_CAL2, how_much=int(rid))
            target = int(row["link"]) if int(row["kind"]) == _B.K_ALARM else int(rid)
            self._noticed.setdefault(a, []).append(target)
            self._bump(f"notified:{_B.PLACEMENTS[int(row['placement'])]}")
            if bool(sleeping[a]):
                self._bump("notified_asleep")
                continue
            self._think.setdefault(a, int(T))
            if int(row["kind"]) == _B.K_ALARM:
                self.book.observe(int(rid), "closed", 1)
        todo = sorted(self._think)
        keep: dict[int, int] = {}
        for a in todo:  # 逐次ループ宣言 (c): 考えた体の数ぶん
            if a in main_now:
                keep[a] = self._think[a]
                self._bump("arbitration:main_first")
                continue
            if bool(sleeping[a]):
                continue
            self._look(T, t_ns, day, int(a), cells)
        self._think = keep
        for a in sorted(main_now):  # 逐次: 主の判断の呼びのあった体の数ぶん(考えた=次の刻みに見る)
            if a in self.book.by_owner or a in self._noticed:
                self._think.setdefault(a, int(T))

    def _visible(self, T: int, t_ns: int, day: int, a: int, row: dict[str, Any], cells: np.ndarray,
                 noticed: set[int], cued: set[int], *, probe: bool = False) -> bool:
        """置き場所の性質で見えるか(本人に見せるのは道具が現実に教えることだけ)。``probe``=確かめるだけ(頭の中の行の
        想起の練習=痕跡を足さない・計器に数えない=会話の番の「変える」の候補を作るとき。選んで使った行だけ練習に足す)。"""
        if int(row["id"]) in noticed:
            return True
        pl = int(row["placement"])
        if pl == _B.PL_APP:
            if self.contact is None:
                return True
            from shibuya.engine.contact.attention import GAZE_SCREEN

            return int(self.contact.attn._gaze[a]) == GAZE_SCREEN
        if pl == _B.PL_PLANNER:
            return int(self._planner_day.get(a, -1)) != int(day)
        if pl == _B.PL_HEAD:
            cue = int(row["id"]) in cued or any(
                0 <= int(w) < self.n and int(cells[int(w)]) >= 0 and int(cells[int(w)]) == int(cells[a])
                for w in row["with"])
            hit = self.recall.recalled(a, row["trace"], t_ns, cue=cue)
            if probe:
                return hit
            self._bump("head_recall:思い出した" if hit else "head_recall:思い出せない")
            if hit:
                self.book.observe(int(row["id"]), "trace", self.recall.touch(row["trace"], t_ns))
            return hit
        return False

    def _look(self, T: int, t_ns: int, day: int, a: int, cells: np.ndarray) -> None:
        """本人が考えた刻み: その日の自分の予定のうち見える行について「出発する/まだ/行かない」。"""
        noticed = set(self._noticed.pop(a, []))
        day0, day1 = int(day) * self.day_ns, (int(day) + 1) * self.day_ns
        cued: set[int] = set()
        for r in self.book.own_rows(a):  # 逐次: 持ち主の行の数ぶん(出来事がきっかけの実行意図)
            if (r["kind"] == _B.K_INTENT and not r["closed"] and r["state"] == _B.ST_LIVE
                    and 0 <= int(r["trigger"]) < self.n and int(cells[int(r["trigger"])]) >= 0
                    and int(cells[int(r["trigger"])]) == int(cells[a])):
                cued.add(int(r["link"]))
                self.book.observe(int(r["id"]), "outcome", "きっかけで思い出した")
                self.book.observe(int(r["id"]), "closed", 1)
                self._bump("intentions:きっかけ")
        rows = [r for r in self.book.own_rows(a) if r["kind"] in (_B.K_PROMISE, _B.K_OWN) and not r["closed"]
                and r["state"] == _B.ST_LIVE and int(r["departed_ns"]) < 0 and day0 <= int(r["start_ns"]) < day1]
        planner_seen = False
        for r in rows:  # 逐次: その日の自分の行の数ぶん
            if not self._visible(T, t_ns, day, a, r, cells, noticed, cued):
                continue
            planner_seen = planner_seen or int(r["placement"]) == _B.PL_PLANNER
            self.book.observe(int(r["id"]), "seen", int(r["seen"]) + 1)
            c, cause = self._decide(T, t_ns, a, _P.P_GO, [_P.cand(_P.K_DEPART), _P.cand(_P.K_NOT_YET),
                                                          _P.cand(_P.K_NOT_GO)])
            if c.kind == _P.K_DEPART:
                self._depart(T, t_ns, a, r, cause)
            elif c.kind == _P.K_NOT_GO:
                self.book.edit(a, int(r["id"]), "state", _B.ST_NOT_GOING)
                self._log(t_ns, a, W_NOT_GO, cause, whom=int(r["with"][0]) if r["with"] else None,
                          how_much=int(r["id"]))
                self._bump("go:行かない")
            else:
                self._bump("go:まだ")
        if planner_seen or any(int(r["placement"]) == _B.PL_PLANNER for r in rows):
            self._planner_day[a] = int(day)

    def _depart(self, T: int, t_ns: int, a: int, row: dict[str, Any], cause: LlmCall) -> None:
        rid = int(row["id"])
        whom = int(row["with"][0]) if row["with"] else None
        self._impossible(T, t_ns, a, row, at="go")
        if int(row["cell"]) < 0:  # 地名帳に無い場所(言葉のまま)=歩く先が無い=記録だけ
            self.book.observe(rid, "departed_ns", int(t_ns))
            self._log(t_ns, a, W_DEPART, cause, whom=whom, how_much=rid)
            self._bump("go:言葉の場所")
            return
        good, here, busy, fail = R.begin_walk_to(self.agents, self.world, np.asarray([a]), np.asarray([int(row["cell"])]))
        if bool(busy[0]):
            self._bump("go:会話中で出られない")
            return
        if bool(fail[0]):
            self._bump("go:歩けない")
            return
        self.book.observe(rid, "departed_ns", int(t_ns))
        self._log(t_ns, a, W_DEPART, cause, whom=whom, how_much=rid)
        if bool(here[0]):
            self.book.observe(rid, "arrived_ns", int(t_ns))
            self._bump("go:もう居た")
        else:
            self._watch.append(rid)
            self._bump("go:歩き出した")

    # ---------------------------------------------------------------- 5. 着いたか・始まり・終わり
    def _track(self, T: int, t_ns: int, cells: np.ndarray) -> None:
        still: list[int] = []
        for rid in self._watch:  # 逐次ループ宣言 (d): 歩いている行の数ぶん
            row = self.book.rows.get(int(rid))
            if row is None or row["closed"]:
                continue
            if int(cells[int(row["owner"])]) == int(row["cell"]):
                self.book.observe(int(rid), "arrived_ns", int(t_ns))
            else:
                still.append(int(rid))
        self._watch = still
        for code, rid in self._agenda.pop(int(T), []):  # 逐次ループ宣言 (d): その刻みに始まり/終わる行の数ぶん
            row = self.book.rows.get(int(rid))
            if row is None:
                continue
            if row["closed"]:  # 鳴ったアラーム・きっかけで思い出した実行意図は終わりの刻みで落とす(有界化)
                if code == _AG_END and self._end_step(row) <= int(T):
                    self._bump(f"closed:{_B.KINDS[int(row['kind'])]}")
                    self._drop(int(rid))
                continue
            if code == _AG_START:
                if self._step_of(int(row["start_ns"])) != int(T) or int(row["at_start"]) >= 0:
                    continue  # 時刻を変えた行の古い印・同じ刻みの 2 つ目の印
                if row["state"] == _B.ST_LIVE and int(row["cell"]) >= 0:
                    at = int(int(cells[int(row["owner"])]) == int(row["cell"]))
                    self.book.observe(int(rid), "at_start", at)
                    self._bump("plan_match:見た数")
                    self._bump("plan_match:居た", at)
            elif code == _AG_END:
                if self._end_step(row) > int(T):
                    continue  # 時刻を変えた行の古い印
                self._close(int(rid), row, t_ns)

    def _close(self, rid: int, row: dict[str, Any], t_ns: int) -> None:
        kind = int(row["kind"])
        pl = _B.PLACEMENTS[int(row["placement"])]
        if kind in (_B.K_PROMISE, _B.K_OWN):
            if row["state"] == _B.ST_CANCELLED:
                out = "取り消し"
            elif row["state"] == _B.ST_NOT_GOING:
                out = "行かない"
            elif int(row["arrived_ns"]) >= 0:
                d = int(row["arrived_ns"]) - int(row["start_ns"])
                self._hist_add("arrive_minus_start_min", d // (SECONDS_PER_MINUTE * NS_PER_SECOND))
                out = ("5 分前までに着いた" if d <= -EARLY_MIN * SECONDS_PER_MINUTE * NS_PER_SECOND
                       else ("間に合った" if d <= 0 else "遅れて着いた"))
            elif int(row["departed_ns"]) >= 0:
                out = "出発したが着かなかった"
            elif int(row["seen"]) == 0:
                out = "忘れた"
            else:
                out = "出発しなかった"
            self._bump(f"outcome:{out}")
            self._bump(f"outcome_by_placement:{pl}:{out}")
            self._bump(f"closed_by_placement:{pl}")
        else:
            self._bump(f"closed:{_B.KINDS[kind]}")
            out = row["outcome"] or "締めた"
        self.book.observe(rid, "outcome", out)
        self.book.observe(rid, "closed", 1)
        if int(rid) in self._watch:
            self._watch.remove(int(rid))
        self._drop(rid)

    # ================================================================== 計器・manifest
    def manifest(self) -> dict[str, Any]:
        m = dict(sorted(self._c2_meter.items()))

        def pick(prefix: str) -> dict[str, int]:
            return {k[len(prefix):]: v for k, v in m.items() if k.startswith(prefix)}

        days = max(int(self._days[0]), 1)
        n_promises = int(sum(self._c2_per_agent.values()))
        ans = pick("answers:")
        n_ans = sum(ans.values())
        outcome = pick("outcome:")
        n_close = sum(outcome.values())
        n_promise_close = n_close - outcome.get("取り消し", 0) - outcome.get("行かない", 0)
        arrived = sum(outcome.get(k, 0) for k in ("5 分前までに着いた", "間に合った", "遅れて着いた"))
        forgot = {}
        for pl in _B.PLACEMENTS:  # 逐次: 置き場所の数(4)
            n = m.get(f"closed_by_placement:{pl}", 0)
            f = m.get(f"outcome_by_placement:{pl}:忘れた", 0)
            forgot[pl] = {"closed": n, "forgot": f, "rate": (f / n) if n else None}
        seen = m.get("plan_match:見た数", 0)
        cfg = {
            "schema": SCHEMA, "arm": _ARM.ARM_ON, "port": self.port.name,
            "placements": {k: dict(v) for k, v in _B.PLACEMENT_TRAITS.items()}, "kinds": list(_B.KINDS),
            "certainty": list(_B.CERTAINTY),
            "candidates": {"length_hours": list(_P.LENGTH_HOURS), "notify_lead_min": list(_P.NOTIFY_LEAD_MIN),
                           "horizon_days": int(_P.HORIZON_DAYS), "hours": "正時",
                           "edit_max_candidates": int(EDIT_MAX_CANDIDATES)},
            "recall": {"tau": float(self.recall.tau), "importance": int(IMPORTANCE_HEAD), "form": "memory_m1.base_level",
                       "cue": "約束の相手が同じセル"},
            "early_min": int(EARLY_MIN), "arbitration": dict(ARBITRATION),
            "provisional": list(_P.PROVISIONAL_VALUES),
        }
        rd = None
        ct = self.contact
        if ct is not None:  # 連絡の道具 C1 の計器を読むだけ(重ねない)
            h = {int(k): int(v) for k, v in dict(ct._ct_hist.get("read_delay_minutes", {})).items()}
            rd = {"source": "contact_c1.read_delay_minutes", **_quantiles(h)}
        obs = {
            "meter": m, "decisions": pick("decisions:"),
            "promises": {"written": pick("written:"), "rows_promise": n_promises, "agents": len(self._c2_per_agent),
                         "days": days, "per_agent_week": n_promises / max(self.n, 1) / days * 7.0,
                         "offers": int(m.get("offers", 0)), "offers_by_via": pick("offers:")},
            "responses": {"counts": ans, "rates": {k: v / n_ans for k, v in ans.items()} if n_ans else {},
                          "offers_no_answer": int(m.get("offers_no_answer", 0)),
                          "offers_all_declined": int(m.get("offers_all_declined", 0))},
            "initial": {"offered": int(m.get("initial_offered", 0)), "rows": int(m.get("initial_rows", 0)),
                        "per_agent": int(m.get("initial_rows", 0)) / max(self.n, 1)},
            "forgot": forgot,
            "arrival": {"outcomes": outcome, "closed_promises": n_close,
                        "early_rate": (outcome.get("5 分前までに着いた", 0) / n_promise_close) if n_promise_close else None,
                        "late_rate": (outcome.get("遅れて着いた", 0) / n_promise_close) if n_promise_close else None,
                        "arrived": arrived,
                        "arrive_minus_start_min": dict(sorted(self._c2_hist["arrive_minus_start_min"].items(),
                                                              key=lambda kv: int(kv[0])))},
            "plan_match": {"sampled": seen, "at_place": int(m.get("plan_match:居た", 0)),
                           "rate": (m.get("plan_match:居た", 0) / seen) if seen else None},
            "impossible": pick("impossible:"),
            "read_delay_minutes": rd,
            "outside_plan": pick("outside_plan:"),
            "intentions": pick("intentions:"),
            "rejected": {"reasons": pick("rejected:"), "shown": int(m.get("rejected_shown", 0)),
                         "silent": int(m.get("rejected_silent", 0))},
            "changes": {**pick("changes:"), "candidates_capped": int(m.get("edit_candidates_capped", 0))},
            # 〔第 6 期 6-2 カレンダー 3 検収 L4〕勤務の行(カレンダー 3 が書く=腕 --calendar-3 arm のランだけ)は rows に数えず work_rows に分ける
            "live_rows": {"rows": sum(1 for r in self.book.rows.values() if int(r["kind"]) != _B.K_WORK),
                          "work_rows": sum(1 for r in self.book.rows.values() if int(r["kind"]) == _B.K_WORK),
                          "offers": len(self._offers), "watch": len(self._watch),
                          "agenda_steps": len(self._agenda)},
            # 判断の呼び(判断モデル)と文の口の呼び(LLM)=TM9 の呼び数の内訳(calls_by_model には足していない=親の判断)
            "calls": dict(zip(("judge_model", "llm"), self.model_calls())),
        }
        return {**cfg, **obs}


def _quantiles(h: Mapping[int, int]) -> dict[str, Any]:
    n = int(sum(h.values()))
    if n == 0:
        return {"n": 0, "p50": None, "p75": None, "p95": None}
    keys = sorted(h)
    out: dict[str, Any] = {"n": n}
    for name, q in (("p50", 0.5), ("p75", 0.75), ("p95", 0.95)):
        acc = 0
        for k in keys:  # 逐次: 分布の階級の数ぶん
            acc += int(h[k])
            if acc >= q * n:
                out[name] = int(k)
                break
    return out


def manifest_fields(layer: Calendar2Layer | None) -> dict[str, Any]:
    """manifest の ``calendar_2``(腕 arm のランだけ・ほかは空=欄を出さない)。"""
    return {} if layer is None else {_ARM.MANIFEST_KEY: layer.manifest()}


def sys_calendar_2(ctx: Any, b: Any) -> None:
    """系 calendar_2(刻みの中・腕 arm のランだけ立つ)。"""
    b.layers.calendar2.run_step(ctx.T, int(ctx.t_ns), ctx.td, ctx.day, agents=b.soa.agents, world=b.soa.world,
                                decision=b.scratch.decision)


def audit_causes(events: Iterable[Any], *, step_ns: int, issued: Any = None) -> dict[str, Any]:
    """負の対照の監査: 族 ``約束`` の出来事のうち、本人の判断の語の原因が判断の呼び(LlmCall・源と番号つき・この層の形の
    call_id)で、時刻が判断の刻みか・道具の語の原因が過程 calendar2 か。``issued``(:meth:`Calendar2Layer.issued_keys`)を渡すと、
    原因の call_id が層の発行した呼びにあり・体が同じで・判断の種類が語に合うか(:data:`WORD_PURPOSES`)も突き合わせる。"""
    have = None if issued is None else set(int(x) for x in np.asarray(issued, dtype=np.int64).tolist())
    bad: list[str] = []
    n = 0
    for ev in events:  # 逐次: 出来事の数ぶん(試験と記録の道具だけ)
        if not str(ev.what).startswith(f"{V.FAMILY_PROMISE}:"):
            continue
        n += 1
        c = ev.cause
        if ev.what in PERSON_WORDS:
            got = _P.parse_call_id(getattr(c, "call_id", "")) if isinstance(c, LlmCall) else None
            if got is None or c.source is None or c.number is None:
                bad.append(f"{ev.what} の原因が本人の判断でない: {c!r}")
                continue
            st, who, serial = got
            if int(who) != int(ev.who):
                bad.append(f"{ev.what} の体 {ev.who} と判断の呼びの体 {who} が違う")
            if have is not None:
                try:
                    k = issued_key(st, who, serial)
                except ValueError:
                    k = -1
                if k not in have:
                    bad.append(f"{ev.what} の原因 {c.call_id} は層の発行した判断の呼びに無い")
            if _P.purpose_of_serial(serial) not in WORD_PURPOSES.get(ev.what, frozenset()):
                bad.append(f"{ev.what} の原因の判断の種類 {_P.purpose_of_serial(serial)} が語に合わない")
            if int(ev.t_ns) != int(st) * int(step_ns):
                bad.append(f"{ev.what} の時刻 {ev.t_ns} が判断の刻み {st} と違う")
        elif ev.what in ENGINE_WORDS:
            if not (isinstance(c, Process) and c.name == "calendar2"):
                bad.append(f"{ev.what} の原因が道具(過程 calendar2)でない: {c!r}")
    return {"events": n, "violations": len(bad), "examples": bad[:5]}
