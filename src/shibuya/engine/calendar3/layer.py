"""engine.calendar3.layer — カレンダー 3「雇い主・祝日」の持ち主と系 ``calendar_3``(第 6 期 6-2・C3 職場の連絡と束ねる・腕
``--calendar-3 arm``・既定 off)。

正: 決定 10-12 §4-1 CA1「正規雇用は毎週固定、非正規とシフト勤務は週ごとにします(雇い主がエージェントになるまでのつなぎ)」・
「休むかどうかは本人の判断です」・「祝日を含むランは、第 3 段まで回しません」(本段が第 3 段)・CA9(段の順=3 雇い主・祝日)・
CA10(試験用=分析に使わない印)・CA11(祝日は常識)・§1-1 CP6 と §2 の 2(例外=社会の決まり=暦・祝日は外からの決定=L0)・
§4-4 CT1 の C3(職場の連絡=雇い主の段=カレンダー段 3 と合わせる)・CT2(送るかと宛先は判断・文は LLM)・CT3(届くのはエンジン・
読む/返すは本人)・CT5(職場は初めから連絡先に持つ)・CT9(使用は全部出来事の記録へ)・§1-5 の 55 件の ②(人の仕事を働く人の
エージェントへ=本段は**シフトを組んで知らせる**だけ・ほかは触らない)・§2 の 1(人の手続きはコードに書かず住人の知識から)・
回答 2-1(GPU の前に腕で)。口の約束 1-3(出来事の記録)・1-5(権利台帳=読むだけ)・1-8(候補の口 J0)。記録
``docs/bench/analysis/wallbounce-1012/ca3/README.md``。

持ち主 :class:`Calendar3Layer`(道筋 ``calendar3``・状態台帳の腕の行 ``CA3*``=腕 arm のランだけ持ち主がある=既定のランの 2 つの
ハッシュと状態のファイルは不変)。**再利用**: 職場の連絡は連絡の道具 C1 の口(``ContactLayer.workplace_send``=宛先と手段は本人の
連絡の判断・文は文の口・届くのは網)・働く人の行はカレンダー 2 の本人の予定の器(``Calendar2Layer.book``=``PromiseBook`` の種類
「勤務」の行・置き場所=アプリ・確かさ=確定・元の会話=その連絡)。どちらも二重に作らない。

流れ(系 ``calendar_3``=刻みの中・連絡の系の後・カレンダー 2 の系の前):

1. **雇い主がシフトを組む**: シフトを組む人(``engine.calendar3.roster``=組織の担当のうち店長か最初の担当=つなぎ)は、**週の境目の
   前の決まった刻み**(〔検収 M1〕週の最後の平日=金曜の頭=暦の口の曜日と刻みの番号だけから=``_begin_compose``・試験用の印の
   ランは土日始まりの 0 日目の頭にも)に組む機会が始まり、**本人の判断の刻み**(起きていて主の判断の呼びの無い最初の刻み=仲裁)で、
   受け持つ単位の週ごとの働く人の**翌週(次の月曜から)7 日の枠**をそれぞれ選ぶ(J0 の口・候補=休み+その人の W20 の約束の形の枠=始業〜終業・日の言葉は暦の
   常識の口=祝日の名つき)。正規雇用(W20 の毎週固定)は触らない。労働時間の行(規則の表の human の行=週 40 時間・1 日 8 時間・
   毎週 1 回の休日)と店の営業時間は**読むだけで止めない**(超えたら数える=計器)。店の休業日は店の決まりの口が知らせる=枠だけ。
2. **シフトの知らせ**(C3): 雇い主は働く人ごとに C1 の口で送る(メッセージ・電話・職場のグループ=手段と宛先は C1 の判断)。送れない
   とき(寝ている・電源が無い・通話中)は控え、次に考えた刻みに送り直す。
3. **働く人が書く**: 知らせを読んだ(C1 の読む判断)か電話で聞いた働く人は、知らせの時刻を選び(J0)、勤務の日ごとに自分の行を
   カレンダー 2 の形で書く(種類 勤務・置き場所 アプリ・確かさ 確定・元の会話=その連絡・誰と=雇い主)。
4. **休みの申し出**(休むかどうかは本人の判断): 書いた後に「休みを申し出る/申し出ない」・申し出るならどの日か(J0)→ C1 の口で
   雇い主へ。雇い主は読んだ(聞いた)ときに「受ける/断る」(J0)→ 自分の記録(組んだシフト)を直し、返事を C1 の口で送る(電話の
   申し出は同じ通話で返す)。働く人は返事を読んだとき「自分の行を休みにする/そのまま」(J0)→ 自分の行だけ変える(``edit``)。
5. **遅刻の連絡**: 本人が選んだ知らせの時刻(アプリの通知=道具が鳴る)の後に考えた刻みに、勤め先のセルに居ない働く人は「遅れると
   連絡する/このまま」(J0)→ C1 の口で雇い主へ。
6. **祝日**: 暦の祝日は世界の常識(``engine.calendar3.knowledge.CommonCalendar``=問い合わせの口・常識の文の 1 行)。
7. **計器**(合否なし): 組んだ単位と働く人・1 人 1 週の勤務日数の分布・休みの申し出と受け入れの割合・C3 の連絡の数(種類 × 手段)・
   労働時間の行を超えた数・祝日の日の枠・店の決まり(枠)。manifest の ``calendar_3``。

記録(CT0 の 5): 族 ``勤務`` の語。本人の語の原因は判断の呼び(``LlmCall``=テープの形の call_id・選んだ候補の源と番号)・道具の語
(``知らせ``)の原因は過程 ``calendar3``。送る・読む・電話は C1 の語(族 ``連絡``=C1 の監査)。監査 :func:`audit_causes` は発行した
判断の呼びの控え(腕の行 ``CA3Q``)と突き合わせる(``engine.calendar2.layer.audit_causes`` と同じ形)。

仲裁(``ARBITRATION``=宣言): 雇い主の組む・送り直す・働く人の遅れの判断は、その刻みに主の判断の呼びのあった体ではしない(次の
刻みに回す=C1・カレンダー 2 と同じ規則)。読んだ・聞いたときの判断(書く・申し出る・返事・休みにする)は読んだ刻みの中身(C1 の
読む判断は主の判断の無い刻み)。

**未リサーチ(expedient)**(記録 §仮採用・つなぎの台帳 ``DOC-ca3-*``): シフトを組む機会=金曜の頭に始まり(試験用の印のランは土日始まりの 0 日目にも)、起きていて主の判断の無い最初の刻み(範囲の外の
体は寝ていなければ起きている)・翌週 7 日を
一度に組む・枠=その人の W20 の約束の形・送り直しは考えた刻み(電話がつながらなければ ``MAX_SEND_TRIES`` 回まで)・遅れの連絡の
機会=知らせの後に考えた刻みで勤め先のセルに居ないとき・労働時間は休憩を除かずに数える。

逐次ループ宣言(新設・P4): 系 ``calendar_3`` は (a) 考えた体の数ぶん(組む=受け持つ働く人 × 7 日・送り直し・遅れの判断)・(b) その刻みに
読んだ C3 の連絡の数ぶん(書く=勤務の日の数)・(c) その刻みの帳面の事象の数ぶん・(d) 電話の C3 の連絡の数ぶん。体の数に比例する
Python のループは無い。
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Callable, Final, Iterable, Mapping, Sequence

import numpy as np

from shibuya.agents.state import Activity
from shibuya.core.time_consts import MINUTES_PER_DAY, MINUTES_PER_HOUR, NS_PER_SECOND, SECONDS_PER_HOUR, SECONDS_PER_MINUTE
from shibuya.engine.calendar2 import book as _B
from shibuya.engine.calendar2.port import NOTIFY_LEAD_MIN
from shibuya.engine.calendar3 import arm as _ARM
from shibuya.engine.calendar3 import port as _P
from shibuya.engine.calendar3.knowledge import CommonCalendar, StoreRules, common_line
from shibuya.engine.decision.port import Candidate, DecisionContext
from shibuya.engine.events import vocab as V
from shibuya.engine.events.log import Event, LlmCall, Process

__all__ = [
    "SCHEMA", "CONFIG_KEYS", "OBSERVED_KEYS", "ARBITRATION", "MAX_SEND_TRIES", "WEEK_DAYS", "COMPOSE_WEEKDAY",
    "W_FRAME", "W_WRITE", "W_ASK_REST", "W_ACCEPT", "W_DECLINE", "W_APPLY", "W_LATE", "W_NOTIFY", "PERSON_WORDS",
    "ENGINE_WORDS", "WORD_PURPOSES", "PAY_NOTICE", "PAY_REST", "PAY_REPLY", "PAY_LATE", "PAY_WORDS",
    "Calendar3Layer", "sys_calendar_3", "manifest_fields", "audit_causes", "issued_key", "labor_params",
]

#: manifest の ``calendar_3`` の形の版。
SCHEMA: Final[str] = "shibuya.engine.calendar3/1"

# ---- 出来事の記録の語(族 勤務=1-3 の語彙表の末尾に足した語) ----
W_FRAME = V.word(V.FAMILY_WORK, "枠を決めた")
W_WRITE = V.word(V.FAMILY_WORK, "書いた")
W_ASK_REST = V.word(V.FAMILY_WORK, "休みを申し出た")
W_ACCEPT = V.word(V.FAMILY_WORK, "受けた")
W_DECLINE = V.word(V.FAMILY_WORK, "断った")
W_APPLY = V.word(V.FAMILY_WORK, "休みにした")
W_LATE = V.word(V.FAMILY_WORK, "遅れると伝えた")
W_NOTIFY = V.word(V.FAMILY_WORK, "知らせ")

#: 本人の判断の語(原因は LlmCall でなければならない=負の対照の監査)。
PERSON_WORDS: Final[frozenset[str]] = frozenset({W_FRAME, W_WRITE, W_ASK_REST, W_ACCEPT, W_DECLINE, W_APPLY, W_LATE})
#: 道具の語(原因は過程 calendar3)。
ENGINE_WORDS: Final[frozenset[str]] = frozenset({W_NOTIFY})
#: 本人の語 → 合う判断の種類(監査の突き合わせ)。
WORD_PURPOSES: Final[Mapping[str, frozenset[int]]] = MappingProxyType({
    W_FRAME: frozenset({_P.P_FRAME}), W_WRITE: frozenset({_P.P_NOTIFY}), W_ASK_REST: frozenset({_P.P_REST_DAY}),
    W_ACCEPT: frozenset({_P.P_ANSWER}), W_DECLINE: frozenset({_P.P_ANSWER}), W_APPLY: frozenset({_P.P_APPLY}),
    W_LATE: frozenset({_P.P_LATE}),
})
#: 仲裁の規則(宣言=実装は :meth:`Calendar3Layer._opportunities`)。
ARBITRATION: Final = MappingProxyType({
    "main_first": "雇い主の組む・送り直す・働く人の遅れの判断は、その刻みに主の判断の呼びのあった体ではしない(次の刻みに回す)",
    "read_content": "読んだ・聞いたときの判断(書く・申し出る・返事・休みにする)は読んだ刻みの中身(C1 の読む判断は主の判断の無い刻み)",
})
#: 週の日の数(W20 の週の表と同じ 7)。
WEEK_DAYS: Final[int] = 7
#: 平日の数(月〜金=暦の口の曜日 0〜4)。
WEEKDAYS: Final[int] = 5
#: 〔検収 M1〕シフトを組む日の曜日=週の境目の前の最後の平日=金曜(W20 の週は月曜から=``engine.calendar_shadow.WEEK0_MONDAY``・
#: 暦の口の曜日 0=月)。試験用の印の無いランは月曜始まりの連続する平日だけ=金曜なら印の外でも組める。
COMPOSE_WEEKDAY: Final[int] = WEEKDAYS - 1
#: C3 の連絡を送り直す回数の上限(電話がつながらなかったとき=安全装置・つなぎ ``DOC-ca3-resend``)。
MAX_SEND_TRIES: Final[int] = 3

#: C3 の連絡の中身の種類(シフトの知らせ・休みの申し出・返事・遅れの連絡)。
PAY_NOTICE, PAY_REST, PAY_REPLY, PAY_LATE = range(4)
PAY_WORDS: Final[tuple[str, ...]] = ("シフトの知らせ", "休みの申し出", "申し出への返事", "遅れの連絡")

_P_CAL3: Final[Process] = Process("calendar3")
#: 予定の帳面の事象の種類(知らせ・終わり)。
_AG_NOTIFY, _AG_END = 0, 1
#: 連絡が届いた道具の語(C1 の ``deliver.VIAS`` の番号 → 語)。
_VIA_WORDS: Final[tuple[str, ...]] = ("メッセージ", "グループ", "通話")
#: 置き場所の語の番号(W20 の場所の語=``engine.calendar_self.W20_PLACE_WORDS``)。
_MIN_NS: Final[int] = SECONDS_PER_MINUTE * NS_PER_SECOND

#: manifest の ``calendar_3`` の設定の子と観測の子(``engine.manifest_sections`` の混ざった辞書)。
CONFIG_KEYS: Final[tuple[str, ...]] = (
    "schema", "arm", "trial", "port", "compose", "labor", "arbitration", "store_rules", "provisional")
OBSERVED_KEYS: Final[tuple[str, ...]] = (
    "meter", "decisions", "roster", "composed", "work_days_per_week", "rest", "contacts", "rows", "late", "labor_over",
    "holiday", "common_knowledge", "live", "calls")

#: 発行した判断の呼びの控えの詰め方(刻み 22 ビット・体 20 ビット・通し番号−SERIAL_BASE 21 ビット)。
_ISS_T_SHIFT, _ISS_A_SHIFT = 41, 21
_ISS_MAX_T, _ISS_MAX_A, _ISS_MAX_S = 1 << 22, 1 << 20, 1 << 21


def issued_key(step: int, agent: int, serial: int) -> int:
    t, a, c = int(step), int(agent), int(serial) - _P.SERIAL_BASE
    if not (0 <= t < _ISS_MAX_T and 0 <= a < _ISS_MAX_A and 0 <= c < _ISS_MAX_S):
        raise ValueError(f"判断の呼びの控えの範囲の外: 刻み {t}・体 {a}・通し番号 {serial}")
    return (t << _ISS_T_SHIFT) | (a << _ISS_A_SHIFT) | c


def labor_params(asof: Any) -> dict[str, Any]:
    """規則の表の労働時間の行(human=人が取り締まる側=止めない)を読む。表が無い写し・施行の前は空(記録だけの形)。"""
    if asof is None:
        return {}
    try:
        from shibuya.engine.rules.table import default_rules

        rules = default_rules()
        h = rules.get("labor.statutory_hours", asof)
        r = rules.get("labor.weekly_rest_day", asof)
    except (FileNotFoundError, KeyError, LookupError):
        return {}
    return {"source": ["labor.statutory_hours", "labor.weekly_rest_day"], "kind": [h.kind, r.kind],
            "max_hours_per_week": int(h.params["max_hours_per_week"]),
            "max_hours_per_day": int(h.params["max_hours_per_day"]),
            "min_rest_days_per_week": int(r.params["min_rest_days_per_week"]), "enforced": False}


def _hhmm(minute: int) -> str:
    m = int(minute)
    return f"{m // MINUTES_PER_HOUR}:{m % MINUTES_PER_HOUR:02d}"


class Calendar3Layer:
    """カレンダー 3 の持ち主(状態台帳の腕の行 ``CA3*``)。"""

    LEDGER_ARM: Final[str] = _ARM.LEDGER_ARM

    def __init__(self, *, n_agents: int, seed: int | str, day_key0: int, step_seconds: int, steps_per_day: int,
                 events: Any, agents: Any, world: Any, calendar: Any, contact: Any, calendar2: Any, runner: Any,
                 roster_fn: Callable[[], Any], trial: Any = None) -> None:
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
        self.contact = contact
        self.calendar2 = calendar2
        self.runner = runner
        #: 〔検収 H1〕雇い主の口の表を作る口(権利台帳の雇用の行・W20・役割の語から作る導出)。表は組み立てでは作らず、
        #: 最初の刻みの頭(=再開では状態を戻して権利台帳を作り直した ``rebuild_derived`` の後)に作る(:meth:`ensure_roster`)=
        #: 通しと再開で同じ台帳から同じ並びの単位になる。
        self.roster_fn = roster_fn
        self.roster: Any = None
        # ---- 口(参照・設定) ----
        self.port = _P.Calendar3Port(seed=seed, day_key0=int(day_key0), step_seconds=self.step_seconds)
        self.cc = CommonCalendar(calendar)
        self.rules = StoreRules()
        self.labor = labor_params(calendar.date_of_day(0) if calendar is not None else None)
        #: 試験用の印(開始日の検査の規則の違反の一覧・腕の下の腕 on のランだけ=組み立てが置く・設定)。
        self.trial = None if trial is None else dict(trial)
        #: シフトを組む人 → 受け持つ単位(雇い主の口の表から作る導出=:meth:`ensure_roster`)。
        self.sched_units: dict[int, list[int]] = {}
        # ---- 状態(腕の行 CA3S=雇い主の記録・CA3P=連絡と帳面・CA3G=系の間) ----
        #: 単位 → 組んだ週の最初の日(組んだ記録)。
        self._composed: dict[int, int] = {}
        #: シフトを組む人 → 組む機会の開いた週の最初の日(組んだら消す)。
        self._compose_due: dict[int, int] = {}
        #: 単位 → {働く人: [[日, 枠の番号(−1=休み)], …]}(雇い主が組んだシフト=雇い主の記録)。
        self._plan: dict[int, dict[int, list[list[int]]]] = {}
        #: 送った判断の call_id → 中身(網が送った時刻にメッセージの番号へ移す)。
        self._out: dict[str, dict[str, Any]] = {}
        #: メッセージの番号 → 中身(宛てた人が読むまで)。
        self._msg: dict[int, dict[str, Any]] = {}
        #: 電話をかけた体 → 中身(つながったら伝わる)。
        self._calls: dict[int, dict[str, Any]] = {}
        #: 送れなかった中身(送る人 → 列=次に考えた刻みに送り直す)。
        self._wait: dict[int, list[dict[str, Any]]] = {}
        #: 刻み → ``[[種類, 行], …]``(本人が選んだ知らせの時刻・行の終わり)。
        self._agenda: dict[int, list[list[int]]] = {}
        #: 勤務の行 → ``[働く人, 単位, 雇い主, 日]``。
        self._work_rows: dict[int, list[int]] = {}
        #: 知らせが鳴った勤務の行(体 → 行の列)=次に考えたときの遅れの判断。
        self._noticed: dict[int, list[int]] = {}
        #: 主の判断が先だったので次の刻みに回した体 → 考えた刻み(仲裁)。
        self._think: dict[int, int] = {}
        #: 中身の通し番号・休みの申し出の通し番号。
        self._next: list[int] = [0, 0]
        #: その刻みに C1 の読む判断で読んだ C3 の連絡の控え ``[[体, メッセージの番号, 送った人, グループ, 道具], …]``
        #: (連絡の系が積み・同じ刻みの系 calendar_3 が読む=刻みの境目では空)。
        self._reads: list[list[int]] = []
        # ---- 計器(腕の行 CA3M=診断・再開でも通しと同じ) ----
        self._c3_meter: dict[str, int] = {}
        self._c3_hist: dict[str, dict[str, int]] = {"work_days_per_week": {}, "assigned_per_unit_day": {},
                                                    "compose_hour": {}}
        #: 休みの申し出の番号 → 申し出た出来事の id(返事の判断の入力の目印=原因の表だけが読む=記録の有無で behavior が同じ)。
        self._c3_event_of: dict[int, list[int]] = {}
        self._days: list[int] = [0, -1]
        # ---- 発行した判断の呼びの控えと呼び数(腕の行 CA3Q=監査) ----
        self._c3_issued: np.ndarray = np.zeros(1024, dtype=np.int64)
        #: ``[控えの数, 判断の呼び(判断モデル), 文の口の呼び(LLM)]``。
        self._c3_issued_n: list[int] = [0, 0, 0]
        # ---- 刻みの中の作業の値 ----
        self._codes: dict[int, int] = {}

    # ================================================================== 小さな口
    def _bump(self, key: str, n: int = 1) -> None:
        self._c3_meter[key] = self._c3_meter.get(key, 0) + int(n)

    def _hist_add(self, name: str, v: int) -> None:
        h = self._c3_hist[name]
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
        self._c3_issued_n[1] += 1
        c = next(x for x in cands if x.id == ch.candidate_id)
        basis = tuple(sorted({b for x in cands for b in x.basis}))
        self._bump(f"decisions:{_P.PURPOSES[purpose]}")
        self._bump(f"chosen:{c.kind}")
        return c, LlmCall(ctx.call_id, basis, source=c.source, number=int(ch.number))

    def _issue(self, T: int, a: int, serial: int) -> None:
        n = int(self._c3_issued_n[0])
        if n >= self._c3_issued.size:
            grown = np.zeros(self._c3_issued.size * 2, dtype=np.int64)
            grown[:n] = self._c3_issued[:n]
            self._c3_issued = grown
        self._c3_issued[n] = issued_key(T, a, serial)
        self._c3_issued_n[0] = n + 1

    def issued_keys(self) -> np.ndarray:
        """発行した判断の呼びの控え(写し・監査の道具が読む)。"""
        return self._c3_issued[: int(self._c3_issued_n[0])].copy()

    def model_calls(self) -> tuple[int, int]:
        """カレンダー 3 の呼び数 ``(判断の呼び=判断モデル, 文の口=LLM)``(C3 の連絡の送る判断と文は C1 の内訳)。"""
        return int(self._c3_issued_n[1]), int(self._c3_issued_n[2])

    def _step_of(self, t_ns: int) -> int:
        return int(t_ns) // self.step_ns

    def _notify_step(self, row: Mapping[str, Any]) -> int:
        """知らせが鳴る刻み(本人が選んだ時刻・書いた刻みの次より前にはしない)。"""
        return max(self._step_of(int(row["notify_ns"])), self._step_of(int(row["written_ns"])) + 1)

    def _at(self, step: int, code: int, rid: int) -> None:
        self._agenda.setdefault(int(step), []).append([int(code), int(rid)])

    @property
    def book(self) -> Any:
        """本人の予定の器(カレンダー 2 の ``PromiseBook`` を再利用=二重に作らない)。"""
        return self.calendar2.book

    # ================================================================== 口(連絡の道具 C1 から)
    def note_sent(self, msg: int, call_id: str) -> None:
        """網がメッセージを送った(C1 の打ち終わり=窓の境目): 送った判断の call_id の中身をメッセージの番号へ移す。"""
        p = self._out.pop(str(call_id), None)
        if p is not None:
            self._msg[int(msg)] = p

    def note_read(self, T: int, a: int, rows: Iterable[Sequence[int]]) -> None:
        """C1 の読む判断で読んだメッセージ(``[番号, 送った人, グループ, 道具]``)のうち C3 の連絡を控える(読むのは系 calendar_3)。"""
        for m, sender, group, via in rows:  # 逐次: 読んだ数ぶん
            if int(m) in self._msg:
                self._reads.append([int(a), int(m), int(sender), int(group), int(via)])

    # ================================================================== 1 刻み(系 calendar_3 の本体)
    def ensure_roster(self) -> Any:
        """〔検収 H1〕雇い主の口の表と ``sched_units`` を作る(まだなら=最初の刻みの頭か manifest)。権利台帳は再開では状態を戻した
        後の ``rebuild_derived`` で作り直される=表はその後に読む(通しと再開で同じ台帳・同じ並び)。"""
        if self.roster is None:
            self.roster = self.roster_fn()
            units: dict[int, list[int]] = {}
            for u, s in enumerate(self.roster.scheduler):  # 逐次: 単位の数ぶん(ランで 1 回)
                units.setdefault(int(s), []).append(int(u))
            self.sched_units = units
        return self.roster

    def run_step(self, T: int, t_ns: int, td: int, day: int, *, agents: Any, world: Any, decision: Any) -> None:
        self._codes.clear()
        self.ensure_roster()
        reg = agents.registry
        cells = np.asarray(reg.cell, dtype=np.int64)
        sleeping = np.asarray(reg.activity, dtype=np.int64) == int(Activity.SLEEPING)
        if int(self._days[1]) != int(day):  # 日の頭(計器の日の数・古い連絡の控えを落とす=有界)
            self._days[1] = int(day)
            self._days[0] += 1
            self._prune(T)
            if self.calendar is not None and bool(self.calendar.is_holiday(int(day))):
                self._bump("holiday:ランの中の祝日")
        # ---- 1. 電話の C3 の連絡(つながったら伝わる) ----
        self._poll_calls(T, t_ns)
        # ---- 2. 読んだ C3 の連絡(C1 の読む判断=同じ刻み) ----
        reads, self._reads = self._reads, []
        for a, m, sender, group, via in reads:  # 逐次ループ宣言 (b): その刻みに読んだ C3 の連絡の数ぶん
            p = self._msg.get(int(m))
            if p is None:
                continue
            if int(p["to"]) != int(a):
                self._bump("contacts:read_by_other")  # 職場のグループで読んだほかの人(中身は宛てた人のもの)
                continue
            del self._msg[int(m)]
            key = f"g:{int(group)}" if int(group) >= 0 else "p:" + ":".join(str(x) for x in sorted((int(sender), int(a))))
            self._deliver(T, t_ns, int(a), p, [_VIA_WORDS[int(via)], key, f"msg:{int(m)}"])
        # ---- 3. 帳面(知らせ・終わり) ----
        self._agenda_step(T, t_ns, sleeping)
        # ---- 4. 考えた体(組む・送り直す・遅れ)=仲裁は主の判断が先 ----
        self._opportunities(T, t_ns, td, day, cells, sleeping, decision)

    def _prune(self, T: int) -> None:
        cut = int(T) - WEEK_DAYS * self.steps_per_day
        for d in (self._msg, self._out):  # 逐次: 控えの数ぶん(日に 1 回)
            old = [k for k, p in d.items() if int(p["T"]) < cut]
            for k in old:
                del d[k]
            if old:
                self._bump("contacts:pruned", len(old))

    # ---------------------------------------------------------------- 送る(C1 の口)
    def _payload(self, T: int, kind: int, frm: int, to: int, unit: int, **kw: Any) -> dict[str, Any]:
        pid = int(self._next[0])
        self._next[0] = pid + 1
        return {"id": pid, "t": int(kind), "from": int(frm), "to": int(to), "unit": int(unit), "T": int(T), "tries": 0,
                "held": 0, **kw}

    def _send(self, T: int, t_ns: int, a: int, p: dict[str, Any]) -> bool:
        """C3 の連絡を C1 の口で送る(手段と宛先は C1 の判断)。送れなければ控える(次に考えた刻みに送り直す)。"""
        ct = self.contact
        to = int(p["to"])
        kind = PAY_WORDS[int(p["t"])]
        if to == int(a):  # 本人しか居ない単位=本人が組んだシフト(連絡は要らない=自分で知っている)
            self._bump(f"contacts:self:{kind}")
            self._deliver(T, t_ns, int(a), p, ["本人", "", ""])
            return True
        groups = sorted(set(ct.book.groups_of(a)) & set(ct.book.groups_of(to)))
        groups = [g for g in groups if ct.book.group_kind(g) == "職場"]
        j0, t0 = ct.model_calls()
        got = ct.workplace_send(T, t_ns, a, to, groups=groups, words=kind)
        j1, t1 = ct.model_calls()
        self._bump("contacts:c1_judge_calls", j1 - j0)
        self._bump("contacts:c1_llm_calls", t1 - t0)
        if got is None:
            self._wait.setdefault(int(a), []).append(p)
            if int(p["held"]) == 0:  # 控えた中身の数(送り直しの回数は held_retries)
                self._bump(f"contacts:held:{kind}")
            else:
                self._bump("contacts:held_retries")
            p["held"] = int(p["held"]) + 1
            return False
        how, cid = got
        self._bump(f"contacts:sent:{kind}:{how}")
        if how == "call":
            self._calls[int(a)] = p
        else:
            self._out[str(cid)] = p
        return True

    def _poll_calls(self, T: int, t_ns: int) -> None:
        ct = self.contact
        for caller in sorted(self._calls):  # 逐次ループ宣言 (d): 電話の C3 の連絡の数ぶん
            p = self._calls[caller]
            callee = int(p["to"])
            s = ct.calls.session_of(int(caller))
            if s is not None and bool(s.active) and callee in s.participants:
                del self._calls[caller]
                self._bump(f"contacts:call_connected:{PAY_WORDS[int(p['t'])]}")
                self._deliver(T, t_ns, callee, p, ["通話", f"c:{int(s.session_id)}", f"call:{int(s.session_id)}"],
                              in_call=True)
            elif ct.mail.calling_of(int(caller)) is None and s is None:
                del self._calls[caller]
                self._bump(f"contacts:call_failed:{PAY_WORDS[int(p['t'])]}")
                p["tries"] = int(p["tries"]) + 1
                if int(p["tries"]) < MAX_SEND_TRIES:
                    self._wait.setdefault(int(caller), []).append(p)
                else:
                    self._bump("contacts:gave_up")

    # ---------------------------------------------------------------- 届いた(読んだ・聞いた)
    def _deliver(self, T: int, t_ns: int, a: int, p: dict[str, Any], origin: list[str], *, in_call: bool = False) -> None:
        kind = int(p["t"])
        self._bump(f"contacts:received:{PAY_WORDS[kind]}")
        if kind == PAY_NOTICE:
            rids = self._write_rows(T, t_ns, a, p, origin)
            self._ask_rest(T, t_ns, a, p, rids)
        elif kind == PAY_REST:
            self._answer(T, t_ns, a, p, in_call=in_call)
        elif kind == PAY_REPLY:
            self._apply(T, t_ns, a, p)

    def _write_rows(self, T: int, t_ns: int, a: int, p: dict[str, Any], origin: list[str]) -> list[int]:
        """働く人が届いたシフトを自分の行に書く(カレンダー 2 の形・種類 勤務・置き場所 アプリ・確かさ 確定・元の会話=その連絡)。
        知らせの時刻は本人の判断。"""
        days = [d for d in p["days"]]
        if not days:
            self._bump("rows:no_work_days")
            return []
        leads = [_P.cand(_P.K_LEAD, f"始まりの {m} 分前", id=f"lead:{m}") for m in NOTIFY_LEAD_MIN]
        cl, cause = self._decide(T, t_ns, a, _P.P_NOTIFY, leads + [_P.cand(_P.K_NO_NOTIFY)])
        lead = int(cl.id.split(":", 1)[1]) if cl.kind == _P.K_LEAD else -1
        from shibuya.engine.calendar_self import W20_PLACE_WORDS

        out: list[int] = []
        for d, s_min, e_min, cell, pk in days:  # 逐次: 勤務の日の数ぶん(≤ 7)
            start = int(d) * self.day_ns + int(s_min) * _MIN_NS
            fields = {"kind": _B.K_WORK, "start_ns": start, "end_ns": int(d) * self.day_ns + int(e_min) * _MIN_NS,
                      "cell": int(cell), "place": W20_PLACE_WORDS[int(pk)] if 0 < int(pk) < len(W20_PLACE_WORDS)
                      else "勤め先", "with": [int(p["from"])], "what": "勤務", "placement": _B.PL_APP, "certain": 1,
                      "origin": list(origin), "offer": -1, "state": _B.ST_LIVE,
                      "notify_ns": start - lead * _MIN_NS if lead >= 0 else -1}
            why = _B.broken(fields)
            if why is not None:
                self._bump(f"rows:broken:{why}")
                continue
            rid = self.book.write(a, fields, written_ns=t_ns)
            self._log(t_ns, a, W_WRITE, cause, whom=int(p["from"]), how_much=rid)
            self._work_rows[rid] = [int(a), int(p["unit"]), int(p["from"]), int(d)]
            self._schedule_row(rid, self._step_of(t_ns))
            self._bump("rows:written")
            out.append(rid)
        return out

    def _schedule_row(self, rid: int, now_step: int) -> None:
        """帳面に知らせ(本人が選んだ時刻=道具が鳴る)と終わりを置く。過ぎた刻みには置かない。"""
        row = self.book.rows[int(rid)]
        if int(row["notify_ns"]) >= 0 and self._notify_step(row) > int(now_step):
            self._at(self._notify_step(row), _AG_NOTIFY, rid)
        self._at(max(self._step_of(int(row["end_ns"])), int(now_step) + 1), _AG_END, rid)

    def _ask_rest(self, T: int, t_ns: int, a: int, p: dict[str, Any], rids: list[int]) -> None:
        """休むかどうかは本人の判断(申し出=C3 の連絡)。本人が組んだシフト(本人しか居ない単位)は申し出る相手が無い。"""
        if not rids:
            return
        if int(p["from"]) == int(a):
            self._bump("rest:self_scheduled")
            return
        c, _c = self._decide(T, t_ns, a, _P.P_REST, [_P.cand(_P.K_ASK_REST), _P.cand(_P.K_NO_ASK)])
        if c.kind != _P.K_ASK_REST:
            self._bump("rest:not_asked")
            return
        cr, cause = self._decide(T, t_ns, a, _P.P_REST_DAY, [
            _P.cand(_P.K_ROW, self.cc.words(self._work_rows[r][3]), id=f"row:{r}") for r in rids])
        self._bump("common:asked", len(rids))
        rid = int(cr.id.split(":", 1)[1])
        req = int(self._next[1])
        self._next[1] = req + 1
        eid = self._log(t_ns, a, W_ASK_REST, cause, whom=int(p["from"]), how_much=req)
        if eid is not None:
            self._c3_event_of[req] = eid
        self._bump("rest:asked")
        if self.calendar is not None and bool(self.calendar.is_holiday(int(self._work_rows[rid][3]))):
            self._bump("holiday:rest_asked_on_holiday")
        self._send(T, t_ns, a, self._payload(T, PAY_REST, a, int(p["from"]), int(p["unit"]), rid=rid, req=req,
                                             day=int(self._work_rows[rid][3])))

    def _answer(self, T: int, t_ns: int, a: int, p: dict[str, Any], *, in_call: bool) -> None:
        """雇い主が休みの申し出に返事をする(受ける/断る=本人の判断)。自分の記録(組んだシフト)を直し、返事を送る。"""
        eid = self._c3_event_of.pop(int(p["req"]), None)
        basis = (tuple(eid),) if eid is not None else ()
        c, cause = self._decide(T, t_ns, a, _P.P_ANSWER, [_P.cand(_P.K_ACCEPT, basis=basis),
                                                          _P.cand(_P.K_DECLINE, basis=basis)])
        acc = int(c.kind == _P.K_ACCEPT)
        worker = int(p["from"])
        self._log(t_ns, a, W_ACCEPT if acc else W_DECLINE, cause, whom=worker, how_much=int(p["req"]))
        self._bump("rest:accepted" if acc else "rest:declined")
        if acc:
            plan = self._plan.get(int(p["unit"]), {}).get(worker)
            for slot in plan or ():  # 逐次: 7 日(雇い主の記録=受けた日を休みに)
                if int(slot[0]) == int(p["day"]):
                    slot[1] = -1
        reply = self._payload(T, PAY_REPLY, a, worker, int(p["unit"]), rid=int(p["rid"]), req=int(p["req"]), acc=acc)
        if in_call:  # 電話の申し出は同じ通話で返す
            self._bump("rest:replied_in_call")
            self._deliver(T, t_ns, worker, reply, ["通話", "", ""])
            return
        self._send(T, t_ns, a, reply)

    def _apply(self, T: int, t_ns: int, a: int, p: dict[str, Any]) -> None:
        """働く人が返事を受けて自分の行を変える(自分の行だけ)。"""
        if not int(p["acc"]):
            self._bump("rest:reply_declined_read")
            return
        rid = int(p["rid"])
        row = self.book.rows.get(rid)
        if row is None or int(row["owner"]) != int(a) or int(row["state"]) != _B.ST_LIVE:
            self._bump("rest:row_gone")
            return
        c, cause = self._decide(T, t_ns, a, _P.P_APPLY, [_P.cand(_P.K_APPLY), _P.cand(_P.K_KEEP)])
        if c.kind != _P.K_APPLY:
            self._bump("rest:kept")
            return
        self.book.edit(a, rid, "state", _B.ST_CANCELLED)
        self._log(t_ns, a, W_APPLY, cause, whom=int(p["from"]), how_much=rid)
        self._bump("rest:applied")

    # ---------------------------------------------------------------- 帳面
    def _agenda_step(self, T: int, t_ns: int, sleeping: np.ndarray) -> None:
        for code, rid in self._agenda.pop(int(T), []):  # 逐次ループ宣言 (c): その刻みの帳面の事象の数ぶん
            row = self.book.rows.get(int(rid))
            if row is None or int(rid) not in self._work_rows:
                continue
            a = int(row["owner"])
            if code == _AG_NOTIFY:
                if int(row["state"]) != _B.ST_LIVE or int(row["notify_ns"]) < 0 or self._notify_step(row) != int(T):
                    continue
                self._log(t_ns, a, W_NOTIFY, _P_CAL3, how_much=int(rid))
                self._bump("rows:notified")
                self._noticed.setdefault(a, []).append(int(rid))
                if bool(sleeping[a]):
                    self._bump("rows:notified_asleep")
                    continue
                self._think.setdefault(a, int(T))
            elif code == _AG_END:
                if self._step_of(int(row["end_ns"])) > int(T):
                    continue
                out = "休み" if int(row["state"]) == _B.ST_CANCELLED else "済み"
                self.book.observe(int(rid), "outcome", out)
                self.book.observe(int(rid), "closed", 1)
                self.book.drop(int(rid))
                del self._work_rows[int(rid)]
                lst = self._noticed.get(a)
                if lst and int(rid) in lst:
                    lst.remove(int(rid))
                    if not lst:
                        del self._noticed[a]
                self._bump(f"rows:closed:{out}")

    # ---------------------------------------------------------------- 考えた体
    def _due_units(self, a: int) -> list[int]:
        """体が組む単位(組む機会の開いた週=``_compose_due`` の週をまだ組んでいない単位)。"""
        d0 = self._compose_due.get(int(a))
        if d0 is None:
            return []
        return [u for u in self.sched_units.get(int(a), ()) if int(self._composed.get(u, -1)) != int(d0)]

    def _begin_compose(self, T: int, td: int, day: int) -> None:
        """週の境目の前の決まった刻み(〔検収 M1〕週の最後の平日=金曜の頭=暦の口の曜日と刻みの番号だけから)に、シフトを組む人の
        組む機会を始める(組むのは本人の判断の刻み=起きていて主の判断の無い最初の刻み)。翌週=次の月曜からの 7 日。
        試験用の印のランだけ、土日に始まるランの 0 日目の頭にも 1 回(金曜が来ない=宣言 ``DOC-ca3-compose-opportunity``)。"""
        if self.calendar is None or int(td) != 0:
            return
        wd = int(self.calendar.weekday(int(day)))
        first_trial = self.trial is not None and int(day) == 0 and wd > COMPOSE_WEEKDAY
        if wd != COMPOSE_WEEKDAY and not first_trial:
            return
        d0 = int(day) + WEEK_DAYS - wd  # 次の月曜
        self._bump("composed:begun_on_trial_day0" if first_trial else "composed:begun_on_friday")
        for a in sorted(self.sched_units):  # 逐次: シフトを組む人の数ぶん(週に 1 回)
            if any(int(self._composed.get(u, -1)) != d0 for u in self.sched_units[a]):
                self._compose_due[int(a)] = d0
                self._think.setdefault(int(a), int(T))
                self._bump("composed:begun")

    def _opportunities(self, T: int, t_ns: int, td: int, day: int, cells: np.ndarray, sleeping: np.ndarray,
                       decision: Any) -> None:
        sel = getattr(decision, "selected", None) if decision is not None else None
        main_now: set[int] = set()
        if sel is not None and len(sel):
            main_now = {int(x) for x in np.asarray(sel.agent_id, dtype=np.int64).tolist()}
        self._begin_compose(T, td, day)
        keep: dict[int, int] = {}
        for a in sorted(self._think):  # 逐次ループ宣言 (a): 考えた体の数ぶん
            if a in main_now:
                keep[a] = self._think[a]
                self._bump("arbitration:main_first")
                continue
            if bool(sleeping[a]):
                if a in self._compose_due:  # 組む機会は起きるまで待つ(寝ている人は組まない)
                    keep[a] = self._think[a]
                continue
            self._act(T, t_ns, day, int(a), cells)
        self._think = keep
        for a in sorted(main_now):  # 逐次: 主の判断の呼びのあった体の数ぶん(考えた=次の刻みに)
            if a in self._wait or a in self._noticed or a in self._compose_due:
                self._think.setdefault(a, int(T))

    def _act(self, T: int, t_ns: int, day: int, a: int, cells: np.ndarray) -> None:
        units = self._due_units(a)
        d0 = self._compose_due.pop(a, None)
        if units and d0 is not None and int(day) >= int(d0):
            self._bump("composed:after_week_began")
        for u in units:  # 逐次: 受け持つ単位の数ぶん
            self._compose(T, t_ns, int(d0), a, u)
        waiting = self._wait.pop(a, [])
        while waiting and a not in self._calls:  # 逐次: 送れなかった中身の数ぶん(電話中の連絡があれば次に)
            if not self._send(T, t_ns, a, waiting.pop(0)):  # 送れなかった中身は _send が控えに戻す=残りも控える(順を守る)
                break
        if waiting:
            self._wait.setdefault(a, []).extend(waiting)
        for rid in self._noticed.pop(a, []):  # 逐次: 知らせが鳴った行の数ぶん
            self._late(T, t_ns, a, int(rid), cells)

    def _compose(self, T: int, t_ns: int, d0: int, a: int, u: int) -> None:
        """雇い主が単位 u の週ごとの働く人の翌週 7 日(``d0`` 日目から)の枠を選ぶ(J0)→ 自分の記録 → 知らせる(C1)。"""
        ro = self.roster
        d0 = int(d0)
        self._composed[u] = d0
        plan: dict[int, list[list[int]]] = {}
        self._plan[u] = plan
        self._bump("composed:units")
        # 〔検収 M1〕組んだ時刻[時](その日の刻みから=計器)と組んだ曜日
        self._hist_add("compose_hour", (int(T) % self.steps_per_day) * self.step_seconds // SECONDS_PER_HOUR)
        if self.calendar is not None:
            self._bump(f"composed:weekday:{int(self.calendar.weekday(int(T) // self.steps_per_day))}")
        self._bump(f"composed:by:{ro.sched_by[u]}")
        self.rules.closed_days(u, range(d0, d0 + WEEK_DAYS))  # 店の決まりの口(枠だけ=空)
        self._bump("store_rules:asked")
        labels = [self.cc.words(d0 + k) for k in range(WEEK_DAYS)]  # 暦の常識の口(祝日の名つき)
        self._bump("common:asked", WEEK_DAYS)
        assigned = [0] * WEEK_DAYS
        for w in ro.workers[u]:  # 逐次: 受け持つ働く人の数ぶん
            frames = ro.frames.get(int(w), [])
            if not frames:
                self._bump("composed:no_frames")
                continue
            days: list[list[int]] = []
            work: list[list[int]] = []
            for k in range(WEEK_DAYS):  # 逐次: 7 日
                d = d0 + k
                cands = [_P.cand(_P.K_DAY_OFF, f"{labels[k]} 休み", id="off")] + [
                    _P.cand(_P.K_FRAME, f"{labels[k]} {_hhmm(f[0])}〜{_hhmm(f[1])}", id=f"frame:{i}")
                    for i, f in enumerate(frames)]
                c, cause = self._decide(T, t_ns, a, _P.P_FRAME, cands)
                fi = -1 if c.kind == _P.K_DAY_OFF else int(c.id.split(":", 1)[1])
                days.append([d, fi])
                length = 0 if fi < 0 else int(frames[fi][1]) - int(frames[fi][0])
                self._log(t_ns, a, W_FRAME, cause, whom=int(w), how_much=length)
                holiday = self.calendar is not None and bool(self.calendar.is_holiday(d))
                if fi >= 0:
                    work.append([d, *[int(x) for x in frames[fi]]])
                    assigned[k] += 1
                    self._closed_check(int(w), d, int(frames[fi][0]))
                if holiday:
                    self._bump("holiday:frames_off" if fi < 0 else "holiday:frames_work")
            plan[int(w)] = days
            self._labor(work)
            self._hist_add("work_days_per_week", len(work))
            self._bump("composed:workers")
            self._send(T, t_ns, a, self._payload(T, PAY_NOTICE, a, int(w), u, week=d0, days=work))
        for k in range(WEEK_DAYS):  # 逐次: 7 日
            self._hist_add("assigned_per_unit_day", assigned[k])

    def _labor(self, work: list[list[int]]) -> None:
        """労働時間の行(human)を読むだけで止めない=超えたら数える(休憩は除かない=記録の形)。"""
        lp = self.labor
        if not lp:
            self._bump("labor:no_rules")
            return
        mins = [int(e) - int(s) for _d, s, e, _c, _p in work]
        if sum(mins) > int(lp["max_hours_per_week"]) * MINUTES_PER_HOUR:
            self._bump("labor:over_week_hours")
        over_day = sum(1 for m in mins if m > int(lp["max_hours_per_day"]) * MINUTES_PER_HOUR)
        if over_day:
            self._bump("labor:over_day_hours", over_day)
        if WEEK_DAYS - len(work) < int(lp["min_rest_days_per_week"]):
            self._bump("labor:short_rest_days")

    def _closed_check(self, w: int, d: int, start_min: int) -> None:
        """枠の始業にその人の店が営業の表で閉まっているか(読むだけ=記録)。店の担当でない人・営業の表の無い世界は数えない。"""
        poi = self.roster.store_of.get(int(w))
        op = getattr(self.runner, "opening", None)
        a = getattr(op, "assets", None)
        if (poi is None or a is None or self.calendar is None or getattr(a, "plan_poi", None) is None
                or getattr(a, "plan_day", None) is None):  # 営業の表の無い世界(合成)は数えない
            return
        from shibuya.engine.processes.opening import rows_of_day

        pp = np.asarray(a.plan_poi, dtype=np.int64)
        sel = rows_of_day(pp, np.asarray(a.plan_day), int(self.calendar.opening_row(int(d))), a.plan_ph_poi)
        sel = sel & (pp == int(poi))
        s = np.asarray(a.plan_start, dtype=np.int64)[sel]
        e = np.asarray(a.plan_end, dtype=np.int64)[sel]
        minute = int(start_min) % MINUTES_PER_DAY
        inside = ((s <= minute) & (minute < e)) | ((e > MINUTES_PER_DAY) & (minute < e - MINUTES_PER_DAY))
        self._bump("labor:frames_checked_hours")
        if not bool(((e > s) & inside).any()):
            self._bump("labor:frame_outside_store_hours")

    def _late(self, T: int, t_ns: int, a: int, rid: int, cells: np.ndarray) -> None:
        """知らせの後に考えた刻み: 勤め先のセルに居ない働く人は「遅れると連絡する/このまま」。"""
        row = self.book.rows.get(int(rid))
        if row is None or int(row["state"]) != _B.ST_LIVE or int(rid) not in self._work_rows:
            return
        if int(row["cell"]) < 0 or int(cells[a]) == int(row["cell"]):
            self._bump("late:at_work_or_no_cell")
            return
        if int(self._work_rows[int(rid)][2]) == int(a):  # 本人が組んだシフト=伝える相手が無い
            self._bump("late:self_scheduled")
            return
        c, cause = self._decide(T, t_ns, a, _P.P_LATE, [_P.cand(_P.K_LATE), _P.cand(_P.K_AS_IS)])
        if c.kind != _P.K_LATE:
            self._bump("late:as_is")
            return
        info = self._work_rows[int(rid)]
        self._log(t_ns, a, W_LATE, cause, whom=int(info[2]), how_much=int(rid))
        self._bump("late:told")
        self._send(T, t_ns, a, self._payload(T, PAY_LATE, a, int(info[2]), int(info[1]), rid=int(rid)))

    # ================================================================== 計器・manifest
    def manifest(self) -> dict[str, Any]:
        self.ensure_roster()
        m = dict(sorted(self._c3_meter.items()))

        def pick(prefix: str) -> dict[str, int]:
            return {k[len(prefix):]: v for k, v in m.items() if k.startswith(prefix)}

        ro = self.roster
        rest = pick("rest:")
        n_ans = int(rest.get("accepted", 0)) + int(rest.get("declined", 0))
        cfg = {
            "schema": SCHEMA, "arm": _ARM.ARM_ON, "trial": self.trial, "port": self.port.name,
            "compose": {"weekday": int(COMPOSE_WEEKDAY),
                        "begins_at": "週の最後の平日(金曜)の頭(その日の最初の刻み)・試験用の印のランは土日始まりの 0 日目の頭にも",
                        "decides_at": "起きていて主の判断の呼びの無い最初の刻み(範囲の外の体は寝ていなければ起きている)",
                        "week": "次の月曜から 7 日", "week_days": int(WEEK_DAYS),
                        "scheduler_role": "店長",
                        "frames": "その人の W20 の約束の形(始業〜終業・重ならない組)", "max_send_tries": int(MAX_SEND_TRIES)},
            "labor": dict(self.labor), "arbitration": dict(ARBITRATION),
            "store_rules": {"closed_days": "枠だけ(本段は空=店のエージェントの段)"},
            "provisional": list(_P.PROVISIONAL_VALUES),
        }
        sb: dict[str, int] = {}
        for w in ro.sched_by:  # 逐次: 単位の数
            sb[w] = sb.get(w, 0) + 1
        obs = {
            "meter": m, "decisions": pick("decisions:"),
            "roster": {"units": int(ro.n_units),
                       "by_kind": {k: sum(1 for x in ro.unit_kind if int(x) == i) for i, k in enumerate(("組織", "店"))},
                       "scheduler_by": sb, "schedulers": len(self.sched_units), **dict(ro.head_counts)},
            "composed": {**pick("composed:"), "hour_of_day": dict(sorted(self._c3_hist["compose_hour"].items(),
                                                                          key=lambda kv: int(kv[0])))},
            "work_days_per_week": dict(sorted(self._c3_hist["work_days_per_week"].items(), key=lambda kv: int(kv[0]))),
            "rest": {**rest, "accept_rate": (int(rest.get("accepted", 0)) / n_ans) if n_ans else None},
            "contacts": pick("contacts:"),
            "rows": pick("rows:"),
            "late": pick("late:"),
            "labor_over": pick("labor:"),
            "holiday": pick("holiday:"),
            "common_knowledge": {"asked": int(m.get("common:asked", 0)),
                                 "line": common_line(self.cc, max(int(self._days[1]), 0))},
            "live": {"rows": len(self._work_rows), "plans": len(self._plan), "messages": len(self._msg),
                     "out": len(self._out), "calls": len(self._calls), "wait": sum(len(v) for v in self._wait.values()),
                     "agenda_steps": len(self._agenda),
                     "assigned_per_unit_day": dict(sorted(self._c3_hist["assigned_per_unit_day"].items(),
                                                          key=lambda kv: int(kv[0])))},
            "calls": dict(zip(("judge_model", "llm"), self.model_calls())),
        }
        return {**cfg, **obs}


def manifest_fields(layer: Calendar3Layer | None) -> dict[str, Any]:
    """manifest の ``calendar_3``(腕 arm のランだけ・ほかは空=欄を出さない)。"""
    return {} if layer is None else {_ARM.MANIFEST_KEY: layer.manifest()}


def sys_calendar_3(ctx: Any, b: Any) -> None:
    """系 calendar_3(刻みの中・腕 arm のランだけ立つ)。"""
    b.layers.calendar3.run_step(ctx.T, int(ctx.t_ns), ctx.td, ctx.day, agents=b.soa.agents, world=b.soa.world,
                                decision=b.scratch.decision)


def audit_causes(events: Iterable[Any], *, step_ns: int, issued: Any = None) -> dict[str, Any]:
    """負の対照の監査: 族 ``勤務`` の出来事のうち、本人の判断の語の原因が判断の呼び(LlmCall・源と番号つき・この層の形の
    call_id)で時刻が判断の刻みか・道具の語の原因が過程 calendar3 か。``issued``(:meth:`Calendar3Layer.issued_keys`)を渡すと、
    原因の call_id が層の発行した呼びにあり・体が同じで・判断の種類が語に合うか(:data:`WORD_PURPOSES`)も突き合わせる。"""
    have = None if issued is None else set(int(x) for x in np.asarray(issued, dtype=np.int64).tolist())
    bad: list[str] = []
    n = 0
    for ev in events:  # 逐次: 出来事の数ぶん(試験と記録の道具だけ)
        if not str(ev.what).startswith(f"{V.FAMILY_WORK}:"):
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
            if not (isinstance(c, Process) and c.name == "calendar3"):
                bad.append(f"{ev.what} の原因が道具(過程 calendar3)でない: {c!r}")
    return {"events": n, "violations": len(bad), "examples": bad[:5]}
