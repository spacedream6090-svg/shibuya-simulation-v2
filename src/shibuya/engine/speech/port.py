"""engine.speech.port — 発話の口(第 1 期 1-8b・Q57 (d)・10-03 §6 ⑤・10-12 §4-6 MR11・§4-2 TM3・10-13b §1 1-5)。

正典
- 口の約束 ``docs/design/v2-foundation-contracts-2026-10-13.md`` の「1-8b 発話の口」(口・約束 5 つ・受入の試験)と 1-8 の
  約束 (4)(「ひと言」の欄は会話の行だけに戻す)。計画 1-8b。
- 決定: 09-30 Q57 (d)(会話の側で「ひと言」を戻す・中身を誘導しない)・10-03 §6 ⑤(会話が起きていないことを最優先)・
  10-12 §4-6 MR11(根拠の札を書かせない)・§4-2 TM3(発言の長さ=モーラ数 × 話す速さ・会話の LLM の入力には聞こえた範囲の
  相手の発言が入る)・10-13b §1 1-5(第 1 期に腕で・既定化は GPU の後・将来の音声と表情(VRM)にも同じ口)。
- 仕分け ``docs/reviews/triage-2026-10-13/README.md`` §3-5(足りないのは 3 つ=プロンプトで書かせる欄・相手の次の入力に
  載せる描画・届け先の行。パーサと口コミの抽出は語彙 v3 でも ``comment`` を受け取る=欄が戻れば動く)。

形
- ``Utterance``(凍結): ``speaker``・``t_ns``(``SimTime``)・``text``(本文)・``addressees``(届け先=当面セッションの参加者)・
  ``via``(1-3 の ``Event.via`` と同じ語・対面が既定)・``mora``(本文のモーラ数=TM3 の入力・本文から数える)・``event_id``
  (1-3 の出来事ログの行=口が付ける)・``modality``(将来の音声・表情の欄=値は空)。本文の無い発話は作れない(``ValueError``)。
- ``SpeechContext``(凍結): その発話の呼び出し(刻みの番号・``call_id``・セル・入力に入っていた出来事 id・口コミの宛先と
  旧の源の欄)。
- ``SpeechPort.say(ctx, utterance) -> EventId``(**書く口は 1 つ**): (a) 出来事ログに 1 回だけ書く(``what="行為:発話"``・
  ``whom``=届け先・``via``・``how_much``=モーラ数・原因=``LlmCall(call_id, 入力の出来事 id)``)(b) 届け先ごとの未読の列に
  積む=相手の次の入力(描画の ``perceive`` が ``take_heard`` で 1 回だけ受け取り、B6 の末尾に素性タグと命令文の除去つきで
  載せる)(c) 口コミの抽出に渡す(組み立てが渡す口 ``wom_fn``=今の道と同じ抽出と転写)。
- ``take_heard(agent, step)``: 届け先の次の入力に載せる発話(目印・話し手・本文)を返して未読から外す(読み口=描画だけ)。

状態(状態台帳の行 ``S8``・``S8M``・腕 ``--speech-port on`` のランだけ持ち主がある)
- ``inbox``(届け先 → 未読の発話の列)=軸 1 behavior(次の入力の文に載る)・軸 2 required(刻みをまたぐ)。腕の行
  (``LedgerRow.arm``)=持ち主の居るランだけ 2 つのハッシュと状態のファイルに入る(既定 off のランは印も入らない=final 不変)。
- ``meter``・``_last_input``・``_own_last``・``_heard_taken``=診断(``S8M``=軸 1 diag・軸 2 discardable)。``_last_input`` は次の発話の
  原因の入力の出来事 id(出来事ログの原因=診断)・``_own_last`` は口の通し番号の控え(刻みの中でだけ効く)・``_heard_taken`` は
  ``take_heard`` で渡した発話の口の目印 → 記録の id(同じ刻みの ``report_shown``・``event_ids`` が引く)。
- 〔1-3 の (1) の直し〕未読の列の目印は**いつも口の通し番号** ``(t_ns, 通し番号)``(記録の有無に依らない=記録 on/off で
  behavior-hash と final が同じ)。記録に書いた出来事の id は診断の表 ``_mark_event_of``(口の目印 → 記録の id・未読の列にある
  発話だけ=``S8E``=軸 1 diag・軸 2 required=再開したランの原因の入力が通しと同じ)に持ち、原因の入力だけが読む。

届く範囲(つなぎ=台帳の行 ``DOC-s8b-reach-session``・``DOC-s8b-reach-hearing``): 当面セッションの参加者(距離・遮蔽・騒音を
見ない)。近接 11a(2-2)で距離の範囲へ・空間の段 3(5-3)で「聞こえた範囲」へ。

逐次ループ宣言(P4): ``say`` は届け先の数ぶん(≤ 2=参加の上限 3 から話し手を除く)・``take_heard`` は未読の数ぶん
(≤ ``HEARD_MAX_PER_ADDRESSEE``)・``mora_count`` は本文の字数ぶん(≤ 数十字)。どれも呼数に比例(体数に比例しない)。
"""

from __future__ import annotations

import dataclasses
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Callable, Final

from shibuya.core.time_consts import NS_PER_SECOND, STEP_SECONDS
from shibuya.core.types import SimTime
from shibuya.engine.conversation import SILENCE_TICKS
from shibuya.engine.events import vocab as V
from shibuya.engine.events.log import EventId

__all__ = [
    "SPEECH_SCHEMA", "WHAT", "VIA_FACE", "HEARD_TTL_STEPS", "HEARD_MAX_PER_ADDRESSEE", "METER_KEYS",
    "Utterance", "SpeechContext", "SpeechPort", "mora_count",
]

#: 口の形の版(欄を足したり意味を変えたりしたら上げる。manifest の ``speech_port.schema`` に出る)。
SPEECH_SCHEMA: Final[str] = "shibuya.engine.speech/port/1"
#: 出来事ログの語(1-3 の語彙表の末尾に 1-8b で足した語)。
WHAT: Final[str] = V.word(V.FAMILY_ACT, "発話")
#: 対面(1-3 の ``VIA_WORDS`` の語=CT9)。会話の番の発話の既定の道具。
VIA_FACE: Final[str] = "対面"
assert VIA_FACE in V.VIA_WORDS and VIA_FACE != V.VIA_NONE
#: セッションが閉じた後の最後のひと言の未読を届ける時間の窓[刻み](会話の沈黙のソフト終了の閾値
#: ``conversation.SILENCE_TICKS`` と同じ値=下の expedient)。セッションが開いている間(親の判断 A7)と返事待ちの招待への
#: 返事(招待した人に宛てた発話=親の判断 第 2 回)は窓を置かない。
HEARD_TTL_STEPS: Final[int] = int(SILENCE_TICKS)
#: 届け先ごとの未読の上限(新しいものを残す=参加の上限 3 の会話で 1 刻みに届く数 2 に余裕 1=下の expedient)。溢れは ``overflow``。
HEARD_MAX_PER_ADDRESSEE: Final[int] = 3
#: 計器の鍵(manifest の ``speech_port`` の観測の子の一部)。届けた発話の行き先は
#: ``posted`` = ``delivered``+``all_imperative``+``dropped_budget``+``expired``+``overflow``+``pending``(保存則・試験が見る)。
METER_KEYS: Final[tuple[str, ...]] = (
    "turns", "silent", "no_session", "to_inviter", "said", "events", "zero_mora", "posted", "delivered",
    "all_imperative", "dropped_budget", "expired", "overflow", "wom_passed",
)

# ---- モーラの数え方(仮名の数の近似) ----
_SMALL_KANA: Final[frozenset[str]] = frozenset("ぁぃぅぇぉゃゅょゎゕゖァィゥェォャュョヮ")


def mora_count(text: str) -> int:
    """本文のモーラ数(TM3 の入力=発言の長さ=モーラ数 × 話す速さ)。

    expedient: モーラ数は仮名の数の近似で数える(読みの辞書を使わない)。仮名 1 字=1 拍(拗音・小書きの母音の
    ゃゅょぁぃぅぇぉゎ は前の字と合わせて 1 拍=0 と数える・促音 っ・撥音 ん・長音 ー は 1 拍)・漢字 1 字=2 拍(音読みの多くが
    2 拍=仮の値)・英数字 1 字=1 拍・記号と空白は 0。TM3 の会話の時計(6-3 の T2)で読みの辞書に替える。

    逐次ループ宣言(P4): 本文の字数ぶん(≤ 数十字・呼数に比例)。
    """
    n = 0
    for ch in unicodedata.normalize("NFKC", str(text)):  # 逐次: 字数ぶん
        o = ord(ch)
        if ch in _SMALL_KANA:
            continue
        if 0x3041 <= o <= 0x3096 or 0x30A1 <= o <= 0x30FA or ch == "ー":
            n += 1
        elif 0x4E00 <= o <= 0x9FFF or 0x3400 <= o <= 0x4DBF or ch == "々":
            n += 2
        elif ch.isascii() and ch.isalnum():
            n += 1
    return n


def _is_int(x: Any) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


@dataclass(frozen=True, slots=True)
class Utterance:
    """発話 1 つ(口が出来事ログに書く前の形=``event_id`` は ``None``・口が付ける)。``mora`` は本文から数える。"""

    speaker: int
    t_ns: SimTime
    text: str
    addressees: tuple[int, ...]
    via: str = VIA_FACE
    mora: int = field(init=False)
    event_id: EventId | None = None
    #: 将来の音声・表情(VRM)の欄(10-13b §1 1-5)。値は空(None)で始める=値を作る段で足す。
    modality: Any = None

    def __post_init__(self) -> None:
        if not _is_int(self.speaker) or self.speaker < 0:
            raise ValueError(f"Utterance.speaker は 0 以上の体の id(いま {self.speaker!r})")
        if not _is_int(self.t_ns) or self.t_ns < 0:
            raise ValueError(f"Utterance.t_ns は 0 以上の整数(ナノ秒・SimTime)(いま {self.t_ns!r})")
        if not isinstance(self.text, str) or not self.text.strip():
            raise ValueError("本文の無い発話はエラー(1-8b の約束 (3)・TM3 はモーラ数を入力にする)")
        object.__setattr__(self, "text", self.text.strip())
        adr = tuple(self.addressees) if isinstance(self.addressees, (tuple, list)) else None
        if not adr or not all(_is_int(a) and a >= 0 for a in adr):
            raise ValueError(f"Utterance.addressees は 1 人以上の体の id の組(いま {self.addressees!r})")
        if len(set(adr)) != len(adr) or self.speaker in adr:
            raise ValueError(f"Utterance.addressees は重ならず話し手を含まない(いま {adr!r}・話し手 {self.speaker})")
        object.__setattr__(self, "addressees", tuple(int(a) for a in adr))
        if self.via not in V.VIA_CODES or self.via == V.VIA_NONE:
            raise ValueError(f"Utterance.via は {tuple(w for w in V.VIA_WORDS if w != V.VIA_NONE)} のどれか(いま {self.via!r})")
        e = self.event_id
        if e is not None and not (isinstance(e, tuple) and len(e) == 2 and all(_is_int(x) for x in e)):
            raise ValueError(f"Utterance.event_id は (t_ns, seq) の組か None(いま {e!r})")
        if self.modality is not None:
            raise ValueError("Utterance.modality は将来の音声・表情の欄=値は空(None)で始める")
        object.__setattr__(self, "mora", mora_count(self.text))


@dataclass(frozen=True, slots=True)
class SpeechContext:
    """発話の呼び出し(``say`` の ``ctx``)。口は値を解釈しない(書く・届ける・渡すのに使うだけ)。

    ``step``=通しの刻みの番号・``call_id``=会話の番の呼び出しの id(テープの ``call_id`` 列の形)・``cell``=話し手のセル
    (出来事の ``where``)・``input_event_ids``=その呼び出しの入力に入っていた出来事(聞こえた発話=原因の入力)・
    ``listener``=口コミの宛先(今の道と同じ選び方=会話の相手)・``reason``・``target``=口コミの旧の源(``reason-target``)の欄・
    ``session``=発話したセッションの番号(返事待ちの招待への返事=セッションの外は -1=未読の窓の決め方に使う)。
    """

    step: int
    call_id: str
    cell: int = -1
    input_event_ids: tuple[EventId, ...] = ()
    listener: int = -1
    reason: str = ""
    target: str = ""
    session: int = -1

    def __post_init__(self) -> None:
        if not _is_int(self.step) or self.step < 0:
            raise ValueError(f"SpeechContext.step は 0 以上の整数(いま {self.step!r})")
        if not isinstance(self.call_id, str) or not self.call_id.strip():
            raise ValueError("SpeechContext.call_id は空でない文字列(テープの call_id 列と同じ値)")
        object.__setattr__(self, "input_event_ids", tuple((int(t), int(s)) for t, s in self.input_event_ids))


class SpeechPort:
    """発話の口(書く口は ``say`` の 1 つ・読み口は ``take_heard``)。腕 ``--speech-port on`` のランだけ組み立てが作る。

    Args:
        events: 出来事の記録(``engine.events.log.EventLog``・無いか記録しないランは口の通し番号で目印を付ける)。
        wom_fn: 口コミの抽出の口 ``(Utterance, SpeechContext) → 書いた行の数``(組み立てが置く・無ければ渡さない)。
        step_seconds: 刻みの幅[秒](未読の時間の窓の換算)。
        session_active: セッションの番号 → まだ開いているか(会話の管理を読むだけの口・組み立てが置く・無ければ全部
            閉じているとみなす=窓を置く)。

    expedient(届け方)
    - 未読の発話は話した刻みより後の入力にだけ届ける(同じ刻みの中の呼び出しの順に左右されない)。発話したセッションが
      開いている間と、返事待ちの招待への返事(招待した人に宛てた発話)は届け先の次の入力まで持つ(窓なし)。セッションが
      閉じた後の最後のひと言は話した刻みから ``HEARD_TTL_STEPS`` 刻みより古い未読は届けない(会話の沈黙のソフト終了の
      閾値と同じ)。
    - 届け先ごとの未読は新しいものから ``HEARD_MAX_PER_ADDRESSEE`` 件(古いものを落とす=有界・``overflow`` に数える)。
    - 3 人の会話(腕 ``--conv-max-participants 3``)で届け先が 2 人のとき、出来事の ``whom`` は最初の届け先だけ(1-3 の
      ``Event.whom`` は 1 人の欄)。届けるのは全員。
    """

    #: 実装の名(manifest の ``speech_port.port``)。
    name: str = "speech"
    #: 状態台帳の腕の行の腕の名(``LedgerRow.arm``=``state_ledger.arm_items`` が持ち主の名と照合する=検収 低7)。
    LEDGER_ARM: str = "speech-port"

    def __init__(self, *, events: Any = None, wom_fn: Callable[["Utterance", SpeechContext], int] | None = None,
                 step_seconds: int = STEP_SECONDS, session_active: Callable[[int], bool] | None = None) -> None:
        if not _is_int(step_seconds) or step_seconds <= 0:
            raise ValueError(f"step_seconds は正の整数(いま {step_seconds!r})")
        self.events = events
        self.wom_fn = wom_fn
        self.session_active = session_active
        self.step_ns = int(step_seconds) * NS_PER_SECOND
        self.ttl_steps = HEARD_TTL_STEPS
        self.max_per_addressee = HEARD_MAX_PER_ADDRESSEE
        #: 届け先 → 未読の発話の列 ``[(目印 (t_ns, seq), 話し手, 本文, 話した時刻 ns, セッションの番号), …]``(状態台帳の行 S8)。
        self.inbox: dict[int, list[tuple[EventId, int, str, int, int]]] = {}
        #: 計器(状態台帳の行 S8M)。
        self.meter: dict[str, int] = {k: 0 for k in METER_KEYS}
        #: 体 → その体の直近の入力に載せた発話の目印(次の発話の原因の入力の出来事 id・S8M)。
        self._last_input: dict[int, tuple[EventId, ...]] = {}
        #: 口の通し番号の控え ``(t_ns, 次の通し番号)``(S8M=刻みの中でだけ効く=再開は刻みの境目=次の発話は新しい時刻)。
        self._own_last: tuple[int, int] = (-1, 0)
        #: 〔1-3 の (1)〕口の目印 → 出来事の記録の id(未読の列にある発話だけ・記録しないランは空・S8E)。
        self._mark_event_of: dict[tuple[int, int], tuple[int, int]] = {}
        #: 体 → 直近の ``take_heard`` で渡した発話の 口の目印 → 記録の id(``report_shown``・``event_ids`` が引く・S8M)。
        self._heard_taken: dict[int, dict[tuple[int, int], tuple[int, int]]] = {}

    def __setattr__(self, name: str, value: Any) -> None:
        # 欄は組み立ての 1 回だけ置ける(書く口は say・take_heard。付け替えは口の中で object.__setattr__)
        if not hasattr(self, name):
            object.__setattr__(self, name, value)
            return
        raise AttributeError(f"発話の口の欄 {name} は付け替えられない(書く口は say・take_heard)")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"発話の口の欄 {name} は消せない")

    # ------------------------------------------------------------------ 書く口(1 つ)
    def say(self, ctx: SpeechContext, utterance: Utterance) -> EventId:
        """発話 1 つを (a) 出来事ログに 1 回書き (b) 届け先の次の入力に積み (c) 口コミの抽出に渡す。目印(``EventId``)を返す。"""
        if type(utterance) is not Utterance:
            raise TypeError(f"SpeechPort.say は Utterance だけを受け取る(いま {type(utterance)!r})")
        if type(ctx) is not SpeechContext:
            raise TypeError(f"SpeechPort.say の ctx は SpeechContext(いま {type(ctx)!r})")
        if utterance.event_id is not None:
            raise ValueError("Utterance.event_id は口が付ける(書いた発話は書き直せない)")
        logged = self._write(ctx, utterance)
        mark = self._next_mark(int(utterance.t_ns))  # 〔1-3 の (1)〕未読の列の目印=記録に依らない口の通し番号
        if logged is not None:
            self._mark_event_of[mark] = logged
        eid = logged if logged is not None else mark
        said = dataclasses.replace(utterance, event_id=eid)
        m = self.meter
        m["said"] += 1
        if said.mora == 0:
            m["zero_mora"] += 1
        for a in said.addressees:  # 逐次ループ宣言: 届け先の数ぶん(≤ 2)
            q = self.inbox.setdefault(a, [])
            q.append((mark, said.speaker, said.text, int(said.t_ns), int(ctx.session)))
            m["posted"] += 1
            if len(q) > self.max_per_addressee:
                self._forget_mark(q[0][0])
                del q[0]
                m["overflow"] += 1
        if self.wom_fn is not None:
            self.wom_fn(said, ctx)
            m["wom_passed"] += 1
        return eid

    def _write(self, ctx: SpeechContext, u: Utterance) -> EventId | None:
        """出来事ログに 1 回書き、書いた出来事の id を返す(記録しないランは ``None``)。"""
        log = self.events
        if log is not None and bool(getattr(log, "enabled", False)):
            from shibuya.engine.events.log import Event, LlmCall

            eid = log.append(Event(
                t_ns=int(u.t_ns), who=int(u.speaker), what=WHAT, whom=int(u.addressees[0]),
                where=("cell", int(ctx.cell)) if int(ctx.cell) >= 0 else None, how_much=int(u.mora), via=u.via,
                cause=LlmCall(ctx.call_id, ctx.input_event_ids)))
            if eid is not None:
                self.meter["events"] += 1
                return (int(eid[0]), int(eid[1]))
        return None

    def _next_mark(self, t: int) -> tuple[int, int]:
        """口の通し番号の目印 ``(t_ns, 通し番号)``(同じ時刻の発話に 0 から振る・記録の有無に依らない)。"""
        t0, seq = self._own_last
        seq = seq if int(t) == t0 else 0
        object.__setattr__(self, "_own_last", (int(t), seq + 1))
        return (int(t), seq)

    def _forget_mark(self, mark: EventId) -> None:
        """未読の列から落ちた発話の目印を診断の表から落とす(有界)。"""
        self._mark_event_of.pop((int(mark[0]), int(mark[1])), None)

    # ------------------------------------------------------------------ 読み口(描画の perceive だけ)
    def take_heard(self, agent: int, step: int) -> tuple[tuple[EventId, int, str], ...]:
        """体 ``agent`` の今の入力(刻み ``step``)に載せる未読の発話 ``(目印, 話し手, 本文)`` を返し、未読から外す(1 回だけ)。

        話した刻みより後の入力にだけ届ける(同じ刻みの未読は残す)。発話したセッションが開いていれば窓なし・返事待ちの招待への
        返事(セッションの外)も窓なし・閉じたセッションの発話は話した刻みから窓より古い未読を届けずに落とす(``expired``)。「届いた」に数えるのは描画が
        B6 に実際に載せた後(``report_shown``=検収 低8)。前の入力の目印(次の発話の原因の入力)はここで外す。
        """
        a = int(agent)
        now = int(step) * self.step_ns
        self._last_input.pop(a, None)
        self._heard_taken.pop(a, None)
        q = self.inbox.get(a)
        out: list[tuple[EventId, int, str]] = []
        if q:
            keep: list[tuple[EventId, int, str, int, int]] = []
            taken: dict[tuple[int, int], tuple[int, int]] = {}
            for item in q:  # 逐次ループ宣言: 未読の数ぶん(≤ HEARD_MAX_PER_ADDRESSEE)
                eid, who, text, t, sid = item
                if t >= now:
                    keep.append(item)
                elif int(sid) >= 0 and (now - t) // self.step_ns > self.ttl_steps and not self._open(sid):
                    self._forget_mark(eid)
                    self.meter["expired"] += 1
                else:
                    out.append((eid, int(who), str(text)))
                    k = (int(eid[0]), int(eid[1]))
                    logged = self._mark_event_of.pop(k, None)
                    if logged is not None:
                        taken[k] = logged
            if taken:
                self._heard_taken[a] = taken
            if keep:
                q[:] = keep
            else:
                del self.inbox[a]
        return tuple(out)

    def _open(self, sid: int) -> bool:
        fn = self.session_active
        return int(sid) >= 0 and fn is not None and bool(fn(int(sid)))

    def report_shown(self, agent: int, shown: tuple[EventId, ...], all_imperative: int, dropped_budget: int) -> None:
        """描画の報告(``Renderer.heard_seen_fn``): B6 に実際に載せた発話の目印・本文が空になった(全部が命令文の)発話の数・
        個体群の予算で外した発話の数。載せた目印はその体の次の発話の原因の入力になる。"""
        m = self.meter
        m["delivered"] += len(shown)
        m["all_imperative"] += int(all_imperative)
        m["dropped_budget"] += int(dropped_budget)
        ids = self.event_ids(int(agent), shown)  # 〔1-3 の (1)〕口の目印 → 記録の id(記録しないランは空)
        if ids:
            self._last_input[int(agent)] = ids

    def event_ids(self, agent: int, marks: Any) -> tuple[EventId, ...]:
        """直近の ``take_heard`` で体 ``agent`` に渡した発話の口の目印 → 出来事の記録の id(原因の入力)。引いたら控えを落とす。
        記録しないランは空。"""
        taken = self._heard_taken.pop(int(agent), None)
        if not taken:
            return ()
        out: list[EventId] = []
        for m in marks:  # 逐次ループ宣言: 渡した発話の数ぶん(≤ HEARD_MAX_PER_ADDRESSEE)
            e = taken.get((int(m[0]), int(m[1])))
            if e is not None:
                out.append(e)
        return tuple(out)

    def take_input_ids(self, agent: int) -> tuple[EventId, ...]:
        """体の直近の入力に載せた発話の目印(その体の次の発話の原因の入力)を返して外す(診断=出来事ログの原因だけ)。"""
        return self._last_input.pop(int(agent), ())

    # ------------------------------------------------------------------ 計器
    def note(self, key: str) -> None:
        """会話の番の糸 ``speak_turn`` の計数(計器は持ち主の中だけで読み書きする=軸 1 diag)。"""
        if key not in ("turns", "silent", "no_session", "to_inviter"):
            raise KeyError(f"発話の口の計器で数えられるのは turns・silent・no_session・to_inviter(いま {key!r})")
        self.meter[key] += 1

    def observed(self) -> dict[str, Any]:
        """manifest の ``speech_port`` の観測の子(計器)。"""
        m = self.meter
        return {**{k: int(m[k]) for k in METER_KEYS}, "pending": int(sum(len(q) for q in self.inbox.values()))}
