"""engine.contact.layer — 連絡の道具 C1 の持ち主と系 ``contact`` の本体(第 6 期 6-4・腕 ``--contact c1``・既定 off)。

正: 決定 10-12 §4-4 CT0〜CT5・CT9・§4-2 TM1・TM3・§4-1 CA3・回答 2-1(第 6 期のコードを GPU の前に腕で)。口の約束 1-2(知覚の
事実)・1-3(出来事の記録)・1-7(道具の台帳 C0)・1-8(候補の口 J0)・1-8b(発話の口)・1-6(記憶の器)。記録
``docs/bench/analysis/wallbounce-1012/ct_c1/README.md``。

持ち主 :class:`ContactLayer`(道筋 ``contact``・状態台帳の腕の行 ``CT1*``=腕 c1 のランだけ持ち主がある=既定のランの 2 つの
ハッシュと状態のファイルは不変)。子の持ち主: ``dev``(道具の状態)・``attn``(目と心の向き)・``mail``(届く・予約)・
``chats``(チャットの会話の状態)・``calls``(電話の会話)・``speech``(通話の発話の口)。

系 ``contact``(刻みの中・会話の系の後=その刻みの判断と会話が決まった後・記憶の系の前=気づきの門が記憶の書き手より先):

1. 物理: 電池の減り(使い方で)・電源が切れた体の画面は消える(計器)。
2. 目と心の向き: 寝た体の画面を閉じる・体の反射の口(3-5 の器=値は空)。〔検収 M4〕関心の的は刻みの**終わり**(判断の後)に
   状態から置き直す=次の刻みの描画(``percept_hook``)・次の刻みの周りの出来事の門・通知の門は、どれも同じ値(前の刻みの判断の
   後の値)を読む(描画と記憶の門が同じ写しを読む=宣言)。
3. 周りの出来事の門: その刻みの顕著行為の「気づいた体」から、関心の的が周りでなく驚き駆動の入口で起きていない体を外した写しを
   **連絡の持ち主の側に持つ**(〔検収 M1〕状態台帳の腕の行 ``CT1G``・顕著行為の過程のキャッシュは書き換えない)。記憶の系は
   宣言した読み口 :meth:`ContactLayer.salient_view` から読む(その刻みに門を通していなければ止まる=順は依存で守る)。関心の的
   ごとの「居合わせた・気づいた・外した」の数と、前の刻みの気づきが記憶(1-6 の器の記録の出来事 ``知覚:気づき``)に残ったかを
   数える(計器=合否なし)。
4. System 1: 新しく届いたメッセージと鳴っている電話の刺激(道具の状態と SNR の形)→ 関心の的で気づくか(周り=弱い刺激から・
   画面=画面に出る・通話と会話=強い刺激だけ=割り込み)。気づいた通知は次の刻みの知覚の事実(``Percept.tool_state``)に載る。
5. 本人の判断(候補の口 J0 の形・仮のモデル):着信・呼び出し・通話の番・通知(今読む/後で/無視)・画面(読む/送る/かける/
   見続ける/顔を上げる)・暇(スマホを見る)・宛先・返す・スタンプ。読む・送る・かける・出る・切るは全部ここ(本人)=エンジンは
   時刻も回数も決めない。送信と着信は窓の境目の予約(``bind_queue`` の種類 ``contact.send``・``contact.ring``)。
6. チャットと通話の状態を 1 刻み進める(沈黙・締め・終わり=対面の会話と同じ仕組み)・日の頭で古い既読を落とす。

記録(CT9): 道具を使った出来事は全部 1-3 の記録へ(族 ``連絡`` の語・``via``=メッセージ/グループ/通話・届いた/読んだ時刻・範囲の
外の送り手の印 ``contact:outside``)。原因: 本人の判断=``LlmCall``(テープの形の call_id ``刻み:体:−通し番号``・選んだ候補の源と
番号)・届く(網)=``Process("contact")``・通話の発話=発話の口(``行為:発話``)。〔検収 M3〕量を畳む: グループの「届いた」は
「送った」の 1 行に畳む(届け先=送った時のグループの成員から送り手を除いた体・電源の切れた相手だけ例外の行 ``連絡:預かった``)・
既読は ``連絡:読んだ`` の whom から作る(既読の行を書かない)・読んだは会話ごとに 1 行(``how_much``=読んだ通数)。

監査(〔検収 M2〕): 層は発行した判断の呼びの控え(``_issued``=刻み・体・通し番号を詰めた整数・腕の行 ``CT1Q``)を持ち、
:func:`audit_causes` は本人の語の原因がこの控えにあり・体が同じで・判断の種類が語に合うかを突き合わせる(偽の ``LlmCall`` を
植えると落ちる)。

記録の有無(〔第 6 期 6-4 C1 の直し=口の約束 1-3 の (1)〕): 出来事の記録の id(``(t_ns, seq)``)は behavior の行に置かない。届いた行の
目印は層の診断の表 ``_ct_event_of``(体 → 未読の届いた行の目印・読んだら落とす)・通話の発話の目印は発話の口の診断の表
``SpeechPort._mark_event_of``(口の通し番号 → 出来事の id)に持ち(どちらも腕の行 ``CT1Q``=diag・required)、読む判断と通話の番の
判断の原因の入力(``LlmCall`` の入力の出来事 id=原因の表)だけが読む=記録 on/off で behavior-hash・final・checkpoint が同じ。

呼び数(〔検収 M5〕): 連絡の判断は主の判断と別の呼び(宣言)だが、manifest と日次の記録の ``calls_by_model`` に数える
(判断の呼び=判断モデル・文の口=LLM)。暇なときの「スマホを見る」は、判断の口の腕(``--decision-port port``)のランでは**主の
判断の候補**(源=できること)に入れる(:meth:`offer_main`・選んだら :meth:`take_main`・主の行為のコードは今のまま)。腕 legacy
のランは主の判断が候補を出さないので、別の呼びで代える(宣言)。仲裁は ``engine.contact.port.ARBITRATION``(主の判断が先)。

**未リサーチ(expedient)**(記録 §仮採用・つなぎの台帳 ``DOC-ct-c1-*``): 気づきの門の段(通話と会話は強い刺激だけ)・寝た体は通知に
気づかない・判断は刻みの頭の時刻・暇の判断の時(暇な活動に入った刻みと、暇な間に起きた刻み)・1 体 1 刻みに通知の刺激 1 回
(まとめて 1 回震える)・読むとその体の未読を全部読む。

逐次ループ宣言(新設・P4): 系 ``contact`` は (a) その刻みに判断する体の数ぶん(新しく届いた・鳴っている・画面を見ている・暇に
なった体=送った数と見ている数で決まる・体の数に比例しない)・(b) 生きている通話とチャットの数ぶん・(c) 顕著行為の数ぶん。
窓の境目の処理は予約の数ぶん。体ごとの物理(電池)と向きの置き直しは配列演算。
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Callable, Final, Iterable, Mapping, Sequence

import numpy as np

from shibuya.agents.state import Activity
from shibuya.core.time_consts import NS_PER_SECOND, SECONDS_PER_MINUTE
from shibuya.engine.batching import WORLD
from shibuya.engine.body.system1 import loud_sound_notice, noise_stage_at
from shibuya.engine.contact import arm as _ARM
from shibuya.engine.contact import attention as _AT
from shibuya.engine.contact import device as _DV
from shibuya.engine.contact import deliver as _DL
from shibuya.engine.contact import port as _P
from shibuya.engine.contact.book import ContactBook
from shibuya.engine.contact.calls import CallManager, CallSpeechPort
from shibuya.engine.contact.chat_state import CHAT_SILENCE_STEPS, ChatBook, group_key, pair_key
from shibuya.engine.conversation import ConvState
from shibuya.engine.decision.port import SOURCE_AFFORDANCE, Candidate, DecisionContext
from shibuya.engine.events import vocab as V
from shibuya.engine.events.log import Event, LlmCall, Process
from shibuya.engine.speech.port import SpeechContext, Utterance
from shibuya.engine.tools import contacts as _CT
from shibuya.engine.tools.groups import GROUP_KINDS
from shibuya.perception.contact_view import DeviceView

__all__ = [
    "SCHEMA", "CONFIG_KEYS", "OBSERVED_KEYS", "W_SENT", "W_DELIVERED", "W_READ", "W_LATER", "W_IGNORE", "W_HELD",
    "W_LOOK", "W_UP", "W_DIAL", "W_RING", "W_ANSWER", "W_DECLINE", "W_UNREACHABLE", "W_HANG", "W_CALL_END",
    "PERSON_WORDS", "ENGINE_WORDS", "WORD_PURPOSES", "ContactLayer", "sys_contact", "manifest_fields", "audit_causes",
    "issued_key", "GatedSalient",
]

#: manifest の ``contact_c1`` の形の版。
SCHEMA: Final[str] = "shibuya.engine.contact/c1/1"

# ---- 出来事の記録の語(族 連絡=1-3 の語彙表の末尾に足した語) ----
W_SENT = V.word(V.FAMILY_CONTACT, "送った")
W_DELIVERED = V.word(V.FAMILY_CONTACT, "届いた")
W_READ = V.word(V.FAMILY_CONTACT, "読んだ")
W_LATER = V.word(V.FAMILY_CONTACT, "後で")
W_IGNORE = V.word(V.FAMILY_CONTACT, "無視")
W_HELD = V.word(V.FAMILY_CONTACT, "預かった")
W_LOOK = V.word(V.FAMILY_CONTACT, "スマホを見た")
W_UP = V.word(V.FAMILY_CONTACT, "顔を上げた")
W_DIAL = V.word(V.FAMILY_CONTACT, "電話をかけた")
W_RING = V.word(V.FAMILY_CONTACT, "着信")
W_ANSWER = V.word(V.FAMILY_CONTACT, "出た")
W_DECLINE = V.word(V.FAMILY_CONTACT, "出ない")
W_UNREACHABLE = V.word(V.FAMILY_CONTACT, "不通")
W_HANG = V.word(V.FAMILY_CONTACT, "切った")
W_CALL_END = V.word(V.FAMILY_CONTACT, "通話の終わり")
#: 本人の判断の語(原因は LlmCall でなければならない=負の対照の監査)。
PERSON_WORDS: Final[frozenset[str]] = frozenset({W_SENT, W_READ, W_LATER, W_IGNORE, W_LOOK, W_UP, W_DIAL, W_ANSWER,
                                                 W_DECLINE, W_HANG})
#: 届く(網=エンジン)の語(原因は過程 contact)。
ENGINE_WORDS: Final[frozenset[str]] = frozenset({W_DELIVERED, W_HELD, W_RING, W_UNREACHABLE})
#: 本人の語 → 合う判断の種類(監査の突き合わせ=〔検収 M2〕)。「スマホを見た」は主の判断の呼び(候補)でもよい。
WORD_PURPOSES: Final[Mapping[str, frozenset[int]]] = MappingProxyType({
    W_SENT: frozenset({_P.P_WHOM, _P.P_GROUP, _P.P_REPLY, _P.P_STAMP}), W_READ: frozenset({_P.P_NOTICE, _P.P_SCREEN}),
    W_LATER: frozenset({_P.P_NOTICE}), W_IGNORE: frozenset({_P.P_NOTICE}), W_LOOK: frozenset({_P.P_IDLE}),
    W_UP: frozenset({_P.P_SCREEN}), W_DIAL: frozenset({_P.P_WHOM}), W_ANSWER: frozenset({_P.P_RING}),
    W_DECLINE: frozenset({_P.P_RING}), W_HANG: frozenset({_P.P_WAIT, _P.P_TURN}),
})
#: 発行した判断の呼びの控えの詰め方(刻み 23 ビット・体 22 ビット・通し番号 18 ビット)。主の判断の候補で選んだ
#: 「スマホを見る」は通し番号 0 で控える。
_ISS_T_SHIFT, _ISS_A_SHIFT = 40, 18
_ISS_MAX_T, _ISS_MAX_A, _ISS_MAX_S = 1 << 23, 1 << 22, 1 << 18


def issued_key(step: int, agent: int, serial: int) -> int:
    t, a, c = int(step), int(agent), int(serial)
    if not (0 <= t < _ISS_MAX_T and 0 <= a < _ISS_MAX_A and 0 <= c < _ISS_MAX_S):
        raise ValueError(f"判断の呼びの控えの範囲の外: 刻み {t}・体 {a}・通し番号 {c}")
    return (t << _ISS_T_SHIFT) | (a << _ISS_A_SHIFT) | c
_P_CONTACT: Final[Process] = Process("contact")
#: 範囲の外に居る体の ``transit_state``(〔つなぎ BR-CT1-CHARGE-AT-HOME〕住まいが範囲の外の体の家での充電)。
_TRANSIT_OUTSIDE: Final[int] = 2
_P_CONV: Final[Process] = Process("conversation")
_P_PERCEPTION: Final[Process] = Process("perception")
_W_NOTICE: Final[str] = V.word(V.FAMILY_PERCEPT, "気づき")

#: 気づきの門の段: 関心の的ごとに気づける最小の刺激の段(周り=弱い・画面=弱い(画面に出る)・通話と会話=強い=割り込み)。
NOTICE_MIN_LEVEL: Final[tuple[int, int, int, int]] = (_DV.LEVEL_WEAK, _DV.LEVEL_WEAK, _DV.LEVEL_STRONG, _DV.LEVEL_STRONG)

_NOTICE_MSG, _NOTICE_RING = 0, 1
_NOTICE_KIND_WORDS: Final[tuple[str, str]] = ("メッセージ", "着信")

#: manifest の ``contact_c1`` の設定の子と観測の子(``engine.manifest_sections`` の混ざった辞書)。
CONFIG_KEYS: Final[tuple[str, ...]] = (
    "schema", "arm", "unnoticed_arm", "send_arm", "contacts_source", "queue_kinds", "notice_min_level", "device",
    "attention", "port", "stamps", "mock_text", "message_max_chars", "chat_silence_steps", "provisional")
OBSERVED_KEYS: Final[tuple[str, ...]] = (
    "meter", "decisions", "read_delay_minutes", "call_steps", "screen_minutes", "chats", "calls", "mail", "devices",
    "attention_now", "salient", "remembered", "bodiless_dropped", "rendered")


@dataclass(frozen=True)
class GatedSalient:
    """門を通した顕著行為の読み口の写し(記憶の系の (c) 気づきが読む ``cell``・``noticed`` だけ)。"""

    cell: int
    noticed: np.ndarray


class ContactLayer:
    """連絡の道具 C1 の持ち主(状態台帳の腕の行 ``CT1*``)。"""

    LEDGER_ARM: Final[str] = _ARM.LEDGER_ARM
    #: 主の判断の候補に足す語(〔検収 M5 (i)〕)。
    MAIN_LOOK_WORD: Final[str] = _P.K_LOOK

    def __init__(self, *, n_agents: int, seed: int | str, population_seed: int | str, day_key0: int,
                 step_seconds: int, events: Any, agents: Any, world: Any, groups: Any = None, rel_layer: Any = None,
                 conv: Any = None, remember_link: bool = False, unnoticed_arm: str | None = None,
                 send_arm: str | None = None, renderer: Any = None, home_cell: Any = None) -> None:
        n = int(n_agents)
        self.n = n
        self.step_seconds = int(step_seconds)
        self.step_ns = self.step_seconds * NS_PER_SECOND
        self.unnoticed_arm = str(unnoticed_arm or _ARM.unnoticed())
        self.send_arm = str(send_arm or _ARM.send())
        if self.unnoticed_arm not in _ARM.UNNOTICED_ARMS or self.send_arm not in _ARM.SEND_ARMS:
            raise ValueError("腕 c1 の下の腕の値が表の外")
        self.events = events
        self.agents = agents
        self.world = world
        self.conv = conv
        self.renderer = renderer
        self.remember_link = bool(remember_link)
        #: 〔つなぎ BR-CT1-CHARGE-AT-HOME〕体 → 住まいのセル(−1=範囲の外)。``None``=充電なし(住まいの表の無い呼び手)。
        self.home_cell = None if home_cell is None else np.asarray(home_cell, dtype=np.int64)[:n].copy()
        # ---- 子の持ち主(状態台帳の腕の行) ----
        self.dev = _DV.Devices(n, population_seed)
        self.attn = _AT.Attention(n)
        self.mail = _DL.Mailbox()
        self.chats = ChatBook()
        self.calls = CallManager(seed)
        calls = self.calls

        def _active(sid: int) -> bool:
            s = calls.sessions.get(int(sid))
            return s is not None and bool(s.active)

        self.speech = CallSpeechPort(events=events, step_seconds=self.step_seconds, session_active=_active)
        # ---- 口(参照・設定) ----
        self.port = _P.ContactPort(seed=seed, day_key0=int(day_key0), step_seconds=self.step_seconds)
        self.text = _P.MockTextPort()
        self.book = ContactBook(n, groups=groups, rel_layer=rel_layer)
        # ---- 窓の境目の結び(作業の値=組み立ての後に結ぶ) ----
        self._queue: Any = None
        self._seq_key: dict[int, int] = {}
        # ---- 刻みの中の作業の値 ----
        self._codes: dict[int, int] = {}
        # ---- 計器(診断) ----
        self._meter: dict[str, int] = {}
        self._ct_hist: dict[str, dict[str, int]] = {"read_delay_minutes": {}, "call_steps": {}, "screen_minutes": {}}
        #: 通話の番号 → 切った判断の call_id(通話の終わりの出来事の原因=診断)。
        self._hangup: dict[int, str] = {}
        #: 前の刻みに顕著行為に気づいた体 ``[(t_ns, 体, 関心の的, セル)]``(記憶に残ったかを次の刻みに数える=診断)。
        self._exposed_prev: list[tuple[int, int, int, int]] = []
        # ---- 〔検収 M1・M5〕刻みの中で系の間を渡す値(腕の行 CT1G=刻みの境目では前の刻みの値か空) ----
        #: その刻みの顕著行為ごとの門を通った体(記憶の系が salient_view で読む)と、門を通した刻み ``[T]``。
        self._sal_noticed: list[np.ndarray] = []
        self._sal_step: list[int] = [-1]
        #: 主の判断が先だったので次の刻みに回した連絡の判断 ``体 → 種類(0=通知・1=暇)``(仲裁)。
        self._defer: dict[int, int] = {}
        #: 主の判断の候補で「スマホを見る」を選んだ体 ``体 → [call_id, 提示の番号]``(判断の系が書き・同じ刻みに系 contact が読む)。
        self._look_main: dict[int, list[Any]] = {}
        # ---- 〔検収 M2・M5〕発行した判断の呼びの控えと呼び数(腕の行 CT1Q=監査と calls_by_model) ----
        self._issued: np.ndarray = np.zeros(1024, dtype=np.int64)
        #: ``[控えの数, 判断の呼び(判断モデル), 文の口の呼び(LLM)]``。
        self._issued_n: list[int] = [0, 0, 0]
        # ---- 〔1-3 の (1) の直し〕出来事の id の診断の表(腕の行 CT1Q=記録 on/off で behavior の行が変わらない) ----
        #: 体 → 未読の届いた行の出来事の目印 ``[[メッセージの番号, t_ns, seq], …]``(届いた順・読む判断の原因の入力だけが読む・
        #: 読んだら落とす=記録しないランは空)。
        self._ct_event_of: dict[int, list[list[int]]] = {}
        #: 判断の口の腕(候補)のランか(主の判断が「スマホを見る」を候補に出す=別の暇の判断をしない)。組み立てが置く。
        self.main_offer: bool = False
        #: 〔第 6 期 6-2 カレンダー 2〕会話の番の控えの口(腕 --calendar-2 arm のランだけ組み立てが
        #: ``Calendar2Layer.note_turn`` を挿す=参照・既定 None=今の道)。通話の番とメッセージを送る判断で呼ぶ(控えるだけ)。
        self.turn_sink: Callable[..., None] | None = None
        #: 〔第 6 期 6-2 カレンダー 3=C3 職場の連絡〕網が送った(打ち終わり)メッセージの番号と送った判断の call_id を知らせる口・
        #: 読む判断で読んだメッセージを知らせる口(腕 --calendar-3 arm のランだけ組み立てが ``Calendar3Layer.note_sent``・
        #: ``note_read`` を挿す=参照・既定 None=今の道)。控えるだけ(読んだ中身を使うのは系 calendar_3)。
        self.sent_sink: Callable[..., None] | None = None
        self.read_sink: Callable[..., None] | None = None

    # ================================================================== 小さな口
    def _bump(self, key: str, n: int = 1) -> None:
        self._meter[key] = self._meter.get(key, 0) + int(n)

    def _hist_add(self, name: str, v: int) -> None:
        h = self._ct_hist[name]
        k = str(int(v))
        h[k] = h.get(k, 0) + 1

    def _log(self, t_ns: int, who: int, what: str, cause: Any, *, whom: Any = None, via: str = V.VIA_NONE,
             received_ns: int | None = None, read_ns: int | None = None, how_much: int | None = None,
             origin: str | None = None) -> tuple[int, int] | None:
        """出来事の記録へ 1 行(記録が off のランは何もしない)。書く口はこれ 1 つ(通話の発話は発話の口)。"""
        log = self.events
        if log is None or not bool(getattr(log, "enabled", False)):
            return None
        cell = int(self.agents.registry.cell[int(who)]) if isinstance(who, (int, np.integer)) else -1
        eid = log.append(Event(t_ns=int(t_ns), who=who, what=what, whom=whom,
                               where=("cell", cell) if cell >= 0 else None, how_much=how_much, via=via,
                               received_ns=received_ns, read_ns=read_ns, origin=origin, cause=cause))
        if eid is not None:
            self._bump(f"events:{what}")
        return None if eid is None else (int(eid[0]), int(eid[1]))

    def _charge_at_home(self, t_ns: int, cells: np.ndarray, sleeping: np.ndarray, agents: Any) -> None:
        """〔つなぎ BR-CT1-CHARGE-AT-HOME・外す段=判断モデルの段 6-6〕家に居る体の電池を増やす(エンジン規則=充電が本人の行動に
        なるまで)。家に居る=住まいのセルに居る(範囲の中)か、住まいが範囲の外の体が範囲の外で寝ている(住まいの場所が無い=宣言)。
        職場では増えない。電源が入った体には網が預かっていたメッセージを届ける(出来事 ``連絡:届いた``=原因 過程 contact)。"""
        home = self.home_cell
        transit = np.asarray(agents.registry.transit_state, dtype=np.int64)
        inside_home = (home >= 0) & (cells == home) & (transit == 0)
        outside_home = (home < 0) & (transit == _TRANSIT_OUTSIDE) & sleeping
        n, back = self.dev.charge(inside_home | outside_home, self.step_seconds)
        if n:
            self._bump("charge:agent_steps", n)
        if back.size:
            self._bump("charge:power_on", int(back.size))
            for a, msg, sender, group, via in self.mail.release_held(back.tolist(), t_ns):  # 逐次: 届けた預かりの数ぶん
                eid = self._log(t_ns, int(a), W_DELIVERED, _P_CONTACT, whom=int(sender), via=_DL.VIAS[int(via)],
                                received_ns=int(t_ns), origin=self._origin_of(int(sender)))
                if eid is not None:
                    self._ct_event_of.setdefault(int(a), []).append([int(msg), int(eid[0]), int(eid[1])])
                self._bump("held_released")

    def _screen_end(self, a: Any, t_ns: int, reason: str) -> None:
        """視線を画面から前に戻す(本人の判断・寝た・電池が切れた・電話を耳に当てた)。画面を見ていた長さ[分]を数える。"""
        on, mins = self.attn.end_screen(a, t_ns)
        if on.size == 0:
            return
        for d in mins:  # 逐次: 戻した体の数ぶん
            self._hist_add("screen_minutes", int(d))
        self._bump(f"screen_end:{reason}", int(on.size))

    def _origin_of(self, sender: int) -> str | None:
        return _DL.OUTSIDE_ORIGIN if int(self.agents.registry.cell[int(sender)]) < 0 else None

    def _decide(self, T: int, t_ns: int, a: int, purpose: int, cands: Sequence[Candidate]) -> tuple[Candidate, LlmCall]:
        """本人の判断 1 回(候補の口 J0 の形・仮のモデル)。選んだ候補と原因(LlmCall)を返す。"""
        if _P.habit_answer(a, _P.PURPOSES[purpose]) is None:  # CT4: 習慣は本段では作らない=判断の口に戻す
            self._bump("habit_fallbacks")
        k = self._codes.get(a, 0) + 1
        self._codes[a] = k
        serial = _P.serial_of(purpose, k)
        cell = int(self.agents.registry.cell[a])
        ctx = DecisionContext(agent_id=int(a), step=int(T), t_ns=int(t_ns), wake_class=-1, condition=-1, cell=cell,
                              call_id=_P.call_id_of(T, a, serial))
        ch = self.port.choose(ctx, cands)
        self._issue(T, a, serial)
        self._issued_n[1] += 1
        c = next(x for x in cands if x.id == ch.candidate_id)
        basis = tuple(sorted({b for x in cands for b in x.basis}))
        self._bump(f"decisions:{_P.PURPOSES[purpose]}")
        self._bump(f"chosen:{c.kind}")
        return c, LlmCall(ctx.call_id, basis, source=c.source, number=int(ch.number))

    def _issue(self, T: int, a: int, serial: int) -> None:
        """発行した判断の呼びを控える(監査の突き合わせ)。"""
        n = int(self._issued_n[0])
        if n >= self._issued.size:
            grown = np.zeros(self._issued.size * 2, dtype=np.int64)
            grown[:n] = self._issued[:n]
            self._issued = grown
        self._issued[n] = issued_key(T, a, serial)
        self._issued_n[0] = n + 1

    def _write_text(self, *, kind: str, sender: int, addressees: Sequence[int]) -> str:
        """文の口(LLM の口の代わり)。呼び数を数える(calls_by_model の llm)。"""
        self._issued_n[2] += 1
        return self.text.write(kind=kind, sender=sender, addressees=addressees)

    def issued_keys(self) -> np.ndarray:
        """発行した判断の呼びの控え(写し・監査の道具が読む)。"""
        return self._issued[: int(self._issued_n[0])].copy()

    def model_calls(self) -> tuple[int, int]:
        """連絡の呼び数 ``(判断の呼び=判断モデル, 文の口=LLM)``(manifest と日次の記録の calls_by_model)。"""
        return int(self._issued_n[1]), int(self._issued_n[2])

    # ================================================================== 主の判断の口(〔検収 M5 (i)〕)
    def offer_main(self, ctx: DecisionContext, cands: Sequence[Candidate]) -> tuple[Candidate, ...]:
        """主の判断の候補に「スマホを見る」(源=できること)を足す(暇な活動・電源が入っている・画面を見ていない体)。"""
        a = int(ctx.agent_id)
        out = tuple(cands)
        if not (0 <= a < self.n):
            return out
        act = int(self.agents.registry.activity[a])
        if act not in _AT.IDLE_ACTIVITIES or not bool(self.dev._on[a]) or int(self.attn._gaze[a]) == _AT.GAZE_SCREEN:
            return out
        w = Candidate(id=f"{SOURCE_AFFORDANCE}:{_P.K_LOOK}", kind=_P.K_LOOK, text=f"{_P.K_LOOK}(ここでできる)",
                      source=SOURCE_AFFORDANCE)
        lst = list(out)
        lst.insert(max(0, len(lst) - 1), w)  # よく考える(最後)の前
        self._bump("main_offered")
        return tuple(lst)

    def take_main(self, ctx: DecisionContext, choice: Any) -> None:
        """主の判断が「スマホを見る」を選んだ(判断の系が呼ぶ・同じ刻みの系 contact が画面を見る)。"""
        self._look_main[int(ctx.agent_id)] = [str(ctx.call_id), int(choice.number)]

    def _take_main_looks(self, T: int, t_ns: int, sleeping: np.ndarray) -> None:
        for a, (cid, num) in sorted(self._look_main.items()):  # 逐次: 選んだ体の数ぶん
            if bool(sleeping[a]) or not bool(self.dev._on[a]) or int(self.attn._gaze[a]) == _AT.GAZE_SCREEN:
                self._bump("main_look_dropped")
                continue
            self.dev.take_out([a])
            self.attn.look_at_screen([a], t_ns)
            self._issue(T, a, 0)
            self._log(t_ns, a, W_LOOK, LlmCall(str(cid), (), source=SOURCE_AFFORDANCE, number=int(num)))
            self._bump("phone_looks")
            self._bump("main_looks")
        self._look_main.clear()

    def salient_view(self, events: Sequence[Any], step: int) -> tuple[GatedSalient, ...]:
        """記憶の系の読み口: その刻みの顕著行為の、門を通った「気づいた体」の写し(〔検収 M1〕)。系 contact がその刻みに
        門を通していなければ止まる(順は依存で守る)。"""
        if int(self._sal_step[0]) != int(step) or len(events) != len(self._sal_noticed):
            raise RuntimeError(f"系 contact が刻み {step} の顕著行為の門をまだ通していない(記憶の系より先に立つ)")
        return tuple(GatedSalient(cell=int(getattr(ev, "cell", -1)), noticed=arr)
                     for ev, arr in zip(events, self._sal_noticed))

    # ================================================================== 窓の境目(進行役の待ち行列)
    def bind_queue(self, queue: Any) -> None:
        """進行役の待ち行列に種類を置き、予約の表の事象を入れる(ランの始め=組み立てと再開の後・1 回)。"""
        if self._queue is not None:
            raise RuntimeError("連絡の層はランの始めに 1 回だけ待ち行列に結ぶ")
        queue.register(_DL.KIND_RING, "contact.ring", self._on_due, rank=_DL.RANK_RING, delivery=_DL.RING_DELIVERY)
        queue.register(_DL.KIND_SEND, "contact.send", self._on_due, rank=_DL.RANK_SEND, delivery=_DL.SEND_DELIVERY)
        self._queue = queue
        head = int(queue.head_ns)
        for key, row in self.mail.pending_items():  # 逐次: 予約の数ぶん(再開で入れ直す=境目の時刻で)
            if int(row[2]) < head:
                raise RuntimeError(f"連絡の予約の境目の時刻 {row[2]} が待ち行列の頭 {head} より前(状態の取り違え)")
            self._schedule(key, row, int(row[2]))

    def _schedule(self, key: int, row: list[Any], t_ns: int) -> None:
        kind = _DL.KIND_SEND if int(row[0]) == _DL.P_SEND else _DL.KIND_RING
        seq = self._queue.schedule(int(t_ns), WORLD, kind)
        self._seq_key[int(np.asarray(seq).ravel()[0])] = int(key)

    def _reserve(self, kind: int, t_ns: int, payload: list[Any]) -> None:
        """窓の境目の予約。頼んだ時刻 ``t_ns`` で待ち行列に入れる(届く時刻は待ち行列の種類の届け方が決める=既定 BOUNDARY=
        処理中の窓の中なら次の窓の頭)。予約の表には境目の時刻(BOUNDARY の規則で計算した値=再開で入れ直す時刻)も置く。"""
        q = self._queue
        if q is None:
            raise RuntimeError("連絡の層が待ち行列に結ばれていない(進行役を通らないラン)")
        w = int(q.width_ns)
        t = int(t_ns)
        due = max(-((-t) // w) * w, int(q.head_ns) + w)
        row = [int(kind), t, int(due), *payload]
        key = self.mail.reserve(row)
        self._schedule(key, row, t)

    def _on_due(self, t_ns: int, _agents: Any, seqs: Any) -> None:
        """窓の境目の処理(送信=打ち終わり・着信)。予約の順(鍵の順)に処理する。"""
        for s in np.asarray(seqs).ravel().tolist():  # 逐次ループ宣言: その時刻の予約の数ぶん
            key = self._seq_key.pop(int(s), None)
            if key is None:
                continue
            row = self.mail.take_pending(key)
            if row is None:
                continue
            if int(row[0]) == _DL.P_SEND:
                self._send_now(int(t_ns), row)
            else:
                self._ring_now(int(t_ns), row)

    def _send_now(self, t: int, row: list[Any]) -> None:
        """打ち終わり=送る(送った時刻に届く)。row=[種類, 頼んだ時刻, 境目, 送り手, グループ, 道具, 本文, モーラ数, call_id, 源,
        番号, 届け先]。"""
        _k, _t_req, _due, sender, group, via, text, mora, call_id, src, number, to = row
        cause = LlmCall(str(call_id), (), source=str(src), number=int(number))
        via_w = _DL.VIAS[int(via)]
        origin = self._origin_of(int(sender))
        whom: Any = f"group:{int(group)}" if int(group) >= 0 else int(to[0])
        sent = self._log(t, int(sender), W_SENT, cause, whom=whom, via=via_w, how_much=int(mora), origin=origin)
        msg = self.mail.new_message_id()
        if self.sent_sink is not None:  # 〔6-2 カレンダー 3=C3〕送った判断の call_id とメッセージの番号の控え(腕のランだけ)
            self.sent_sink(int(msg), str(call_id))
        got, held = self.mail.deliver(msg, int(sender), [int(x) for x in to], int(group), int(via), t, int(mora),
                                      str(text), lambda a: bool(self.dev._on[a]))
        for r in got:  # 逐次: 届いた体の数ぶん
            if int(group) >= 0:  # 〔検収 M3 ①〕グループの「届いた」は「送った」の 1 行に畳む(届いた行の目印=送った行)
                eid = sent
            else:
                eid = self._log(t, r, W_DELIVERED, _P_CONTACT, whom=int(sender), via=via_w, received_ns=t,
                                origin=origin)
            if eid is not None:  # 〔1-3 の (1)〕目印は診断の表へ(届いた行は記録に依らない)
                self._ct_event_of.setdefault(int(r), []).append([int(msg), int(eid[0]), int(eid[1])])
        for r in held:  # 逐次: 預かった体の数ぶん(畳んだときの例外の行)
            self._log(t, r, W_HELD, _P_CONTACT, whom=int(sender), via=via_w, origin=origin)
        self._bump("sent_group" if int(group) >= 0 else "sent_messages")
        self._bump("delivered", len(got))
        self._bump("held", len(held))
        key = group_key(int(group)) if int(group) >= 0 else pair_key(int(sender), int(to[0]))
        self.chats.on_message(key, int(sender), [int(x) for x in to], t // self.step_ns)

    def _ring_now(self, t: int, row: list[Any]) -> None:
        """着信(窓の境目で届く)。row=[種類, 頼んだ時刻, 境目, かけた人, 相手, かけた時刻]。"""
        _k, _t_req, _due, caller, callee, t_call = row
        c = self.mail.calling_of(int(caller))
        if c is None or int(c[0]) != int(callee):  # 鳴る前に切った
            self._bump("ring_after_hangup")
            return
        busy = self.calls.is_busy(int(callee)) or self.mail.ringing_of(int(callee)) is not None
        if not bool(self.dev._on[int(callee)]) or busy:
            self._log(t, int(caller), W_UNREACHABLE, _P_CONTACT, whom=int(callee), via=_DL.VIA_CALL)
            self.mail.stop_ringing(int(caller), int(callee))
            self._bump("unreachable_busy" if busy else "unreachable_off")
            return
        self.mail.ring(int(caller), int(callee), t, int(t_call))
        self._log(t, int(callee), W_RING, _P_CONTACT, whom=int(caller), via=_DL.VIA_CALL, received_ns=t)
        self._bump("rings")
        self._bump("ring_delay_ns_sum", t - int(t_call))

    # ================================================================== 知覚の事実(描画の口)
    def percept_hook(self, p: Any) -> Any:
        """描画の ``perceive`` の後に知覚の事実を目と心の向きの形にする(読むだけ・書かない)。"""
        a = int(p.agent_id)
        gaze = int(self.attn._gaze[a])
        focus = int(self.attn._focus[a])
        dv = self.dev.view_fields(a)
        screen = gaze == _AT.GAZE_SCREEN
        nt = self.attn.notice_of(a)
        fresh = nt is not None and int(nt[0]) == int(p.t_ns) - self.step_ns
        ring = self.mail.ringing_of(a)
        in_call = self.calls.session_of(a)
        partner = None
        if in_call is not None and in_call.state is ConvState.PARTICIPATING:
            partner = next((q for q in in_call.participants if q != a), None)
        view = DeviceView(
            battery_pct=dv["battery_pct"], on=dv["on"], manner=dv["manner"], place=dv["place"],
            earphones=dv["earphones"], signal=True,
            notice_kind=_NOTICE_KIND_WORDS[int(nt[1])] if fresh else None,
            notice_level=_DV.LEVEL_WORDS[int(nt[2])] if fresh else None,
            notice_channels=_DV.channel_words(int(nt[3])) if fresh else (),
            unread=self.mail.unread_count(a) if screen else None,
            ringing_from=(int(ring[0]) if screen else -1) if (ring is not None and fresh and int(nt[1]) == _NOTICE_RING)
            else None,
            in_call_with=partner,
            chats=self.chats.partners_of(a) if screen else None,
        )
        return _AT.coarsen(p, gaze, focus, unnoticed_arm=self.unnoticed_arm, device_view=view)

    # ================================================================== 1 刻み(系 contact の本体)
    def run_step(self, T: int, t_ns: int, td: int, *, agents: Any, world: Any, conv: Any, runner: Any,
                 decision: Any) -> None:
        self._codes.clear()
        act = np.asarray(agents.registry.activity, dtype=np.int64)
        cells = np.asarray(agents.registry.cell, dtype=np.int64)
        sleeping = act == int(Activity.SLEEPING)
        # ---- 1. 物理(電池) ----
        in_call = np.zeros(self.n, dtype=bool)
        for s in self.calls.sessions.values():  # 逐次: 生きている通話の数ぶん
            if s.state is ConvState.PARTICIPATING:
                in_call[[p for p in s.participants if p < self.n]] = True
        for caller, _c in self.mail.calling_items():  # 呼び出し中も通話に心が向く
            in_call[int(caller)] = True
        screen = self.attn._gaze == _AT.GAZE_SCREEN
        use = np.where(in_call, _DV.USE_CALL, np.where(screen, _DV.USE_SCREEN, _DV.USE_STANDBY))
        off_now = self.dev.drain(use, self.step_seconds)
        if off_now:
            self._bump("devices_off", off_now)
        if self.home_cell is not None:  # 〔つなぎ BR-CT1-CHARGE-AT-HOME〕家に居る体の充電(エンジン規則)・電源が入った体に預かりを届ける
            self._charge_at_home(t_ns, cells, sleeping, agents)
        dead = np.flatnonzero(screen & ~self.dev._on).astype(np.int64)
        if dead.size:  # 電池が切れた=画面が消えた(物理)
            self._screen_end(dead, t_ns, "battery")
        # ---- 2. 目と心の向き(寝た体の画面は閉じる=本人が寝るを選んだ) ----
        closed = np.flatnonzero(sleeping & (self.attn._gaze == _AT.GAZE_SCREEN)).astype(np.int64)
        if closed.size:
            self._screen_end(closed, t_ns, "sleep")
            self.dev.put_back(closed)
        on_screen = self.attn.on_screen()
        if on_screen.size and loud_sound_notice(None, agent_id=on_screen) is not None:  # 3-5 の器(値は空=起きない)
            self._bump("look_up_reflex")
        idle_onset = self.attn.idle_onset(act)
        # ---- 3. 周りの出来事の門(顕著行為)と記憶に残ったか ----
        interrupted = np.zeros(self.n, dtype=bool)
        sel = getattr(decision, "selected", None) if decision is not None else None
        sel_agents = np.zeros(0, dtype=np.int64)
        if sel is not None and len(sel):
            sel_agents = np.asarray(sel.agent_id, dtype=np.int64)
            cond = np.asarray(sel.condition, dtype=np.int64)
            hit = np.isin(cond, tuple(_AT.INTERRUPT_CONDITIONS))
            interrupted[sel_agents[hit]] = True
        self._remembered_check()
        self._sal_step[0] = int(T)
        self._sal_noticed = []
        if runner is not None and runner.is_enabled("salient"):
            self._salient_gate(T, t_ns, runner.salient, cells, interrupted)
        # ---- 4. System 1(通知の刺激)----
        notice_msg = self._system1(T, t_ns, cells, sleeping, world)
        # ---- 5. 本人の判断(仲裁=主の判断が先: その刻みに主の判断の呼びのあった体は連絡の判断をしない) ----
        main_now = set(int(a) for a in sel_agents.tolist())
        self._take_main_looks(T, t_ns, sleeping)
        self._calls_turns(T, t_ns, main_now)
        self._ring_decisions(T, t_ns, sleeping, main_now)
        self._caller_decisions(T, t_ns, main_now)
        idle_sel = set(int(a) for a in sel_agents.tolist() if int(act[int(a)]) in _AT.IDLE_ACTIVITIES)
        idle = [] if self.main_offer else sorted(set(int(a) for a in idle_onset.tolist()) | idle_sel)
        self._person_decisions(T, t_ns, sleeping, idle, notice_msg, main_now)
        # ---- 6. チャットと通話を 1 刻み進める・日の頭の掃除 ----
        self.chats.step(T)
        for s in self.calls.step(T):  # 逐次: この刻みに終わった通話の数ぶん
            self._call_ended(T, t_ns, s)
        self.calls.purge_terminal()
        # ---- 7. 〔検収 M4〕関心の的を判断の後の状態から置き直す(次の刻みの描画と門が読む値) ----
        in_call2 = np.zeros(self.n, dtype=bool)
        for s in self.calls.sessions.values():  # 逐次: 生きている通話の数ぶん
            if s.state is ConvState.PARTICIPATING:
                in_call2[[p for p in s.participants if p < self.n]] = True
        for caller, _c in self.mail.calling_items():  # 呼び出し中も通話に心が向く
            in_call2[int(caller)] = True
        in_talk = np.zeros(self.n, dtype=bool)
        if conv is not None:
            for s in conv.sessions.values():  # 逐次: 対面の会話の数ぶん
                if s.state is ConvState.PARTICIPATING:
                    in_talk[[p for p in s.participants if p < self.n]] = True
        self.attn.sync(in_call2, in_talk)
        if int(td) == 0 and T > 0:
            self._bump("pruned", self.mail.prune(t_ns, _DL.MAIL_KEEP_S * NS_PER_SECOND))

    # ---------------------------------------------------------------- 3. 周りの出来事
    def _salient_gate(self, T: int, t_ns: int, sal: Any, cells: np.ndarray, interrupted: np.ndarray) -> None:
        events = list(getattr(sal, "events", ()) or ())
        self._sal_step[0] = int(T)
        if not events:
            self._sal_noticed = []
            self._exposed_prev = []
            return
        focus = self.attn._focus
        for ev in events:  # 逐次: 顕著行為の数ぶん(居合わせた体を関心の的ごとに数える)
            occ = np.flatnonzero(cells == int(ev.cell))
            for k in np.unique(focus[occ]).tolist() if occ.size else ():
                self._bump(f"exposed:{_AT.FOCUS_WORDS[int(k)]}", int(np.count_nonzero(focus[occ] == k)))
        kept, blocked, reached, by = _AT.gate_salient(events, focus, interrupted)
        self._sal_noticed = kept
        self._bump("salient_reached", reached)
        self._bump("salient_blocked", blocked)
        for k, v in by.items():
            if v:
                self._bump(f"salient_blocked:{k}", v)
        # 記憶の書き手の気づきの行の場所=顕著行為のセル(engine.memory の (c) 気づき・engine.events.body の where)
        self._exposed_prev = [(int(t_ns), int(a), int(focus[int(a)]), int(ev.cell)) for ev, arr in zip(events, kept)
                              for a in arr.tolist()]
        for _t, _a, f, _c in self._exposed_prev:
            self._bump(f"noticed_salient:{_AT.FOCUS_WORDS[f]}")

    def _remembered_check(self) -> None:
        """前の刻みに顕著行為に気づいた体が、記憶(1-6 の器)に残ったか=記録の出来事 ``知覚:気づき`` があるか。"""
        prev, self._exposed_prev = self._exposed_prev, []
        if not prev or not self.remember_link or self.events is None or not bool(self.events.enabled):
            return
        for t, a, f, c in prev:  # 逐次: 前の刻みに気づいた体の数ぶん(記憶の書き手の行の場所=顕著行為のセル)
            hit = self.events.find(int(t), int(a), _W_NOTICE, ("cell", int(c)) if int(c) >= 0 else None) >= 0
            self._bump(f"remembered:{_AT.FOCUS_WORDS[f]}" if hit else f"not_remembered:{_AT.FOCUS_WORDS[f]}")

    # ---------------------------------------------------------------- 4. System 1
    def _system1(self, T: int, t_ns: int, cells: np.ndarray, sleeping: np.ndarray, world: Any) -> set[int]:
        """新しく届いたメッセージと鳴っている電話の刺激 → 気づいた体。画面を見ていない体でメッセージに気づいた体の集合を返す。"""
        unseen = self.mail.take_unseen()
        ringing = self.mail.ringing_items()
        who = sorted({a for a, _n, _t in unseen} | {int(a) for a, _r in ringing})
        out: set[int] = set()
        if not who:
            return out
        kind = {a: _NOTICE_MSG for a, _n, _t in unseen}
        for a, _r in ringing:
            kind[int(a)] = _NOTICE_RING  # 鳴っている電話は毎刻みの刺激(メッセージより強い印)
        ag = np.asarray(who, dtype=np.int64)
        stage = noise_stage_at(world, cells[ag], T, self.step_seconds)
        level, bits = self.dev.stimulus(ag, _DV.noise_db_of_stage(stage), self.attn._gaze[ag] == _AT.GAZE_SCREEN)
        focus = self.attn._focus[ag]
        need = np.asarray(NOTICE_MIN_LEVEL, dtype=np.int64)[focus.astype(np.int64)]
        noticed = (level.astype(np.int64) >= need) & (level > 0) & ~sleeping[ag]
        manner = self.dev._manner[ag]
        place = self.dev._place[ag]
        for i, a in enumerate(who):  # 逐次: 刺激のあった体の数ぶん
            self._bump(f"stimulus:{_DV.LEVEL_WORDS[int(level[i])]}")
            self._bump(f"stimulus_state:{'マナー' if bool(manner[i]) else '音'}・{_DV.PLACE_WORDS[int(place[i])]}"
                       f":{_DV.LEVEL_WORDS[int(level[i])]}")
            if bool(noticed[i]):
                self.attn.note_notice(a, t_ns, int(kind[a]), int(level[i]), int(bits[i]))
                self._bump("noticed")
                self._bump(f"noticed:{_AT.FOCUS_WORDS[int(focus[i])]}")
                if kind[a] == _NOTICE_MSG and int(self.attn._gaze[a]) != _AT.GAZE_SCREEN:
                    out.add(int(a))
            else:
                self._bump("not_noticed")
                self._bump(f"not_noticed:{_AT.FOCUS_WORDS[int(focus[i])]}")
        return out

    # ---------------------------------------------------------------- 5. 判断
    def _calls_turns(self, T: int, t_ns: int, main_now: set[int] = frozenset()) -> None:
        """通話の番(話す/切る)。話者=セッションの話す番(対面の会話と同じ交替)。主の判断が先の体は次の刻み(仲裁)。"""
        for s in list(self.calls.sessions.values()):  # 逐次: 生きている通話の数ぶん
            if s.state is not ConvState.PARTICIPATING or int(s.last_utterance_tick) >= int(T):
                continue
            a = int(s.speaker)
            if not s.has_budget(a):
                continue
            if a in main_now:
                self._bump("arbitration:turn")
                continue
            partner = next(q for q in s.participants if q != a)
            heard = self.speech.take_heard(a, T)
            basis = self.speech.event_ids(a, [e for e, _w, _t in heard])  # 〔1-3 の (1)〕口の目印 → 出来事の id(診断の表)
            c, cause = self._decide(T, t_ns, a, _P.P_TURN, [_P.cand(_P.K_TALK, basis=basis), _P.cand(_P.K_HANG)])
            if c.kind == _P.K_TALK:
                text, capped = _P.cap_text(self._write_text(kind="call", sender=a, addressees=(partner,))
                                           if self.send_arm == "b" else c.text)
                if capped:
                    self._bump("length_cap_hits")
                ctx = SpeechContext(step=int(T), call_id=cause.call_id,
                                    cell=int(self.agents.registry.cell[a]), input_event_ids=basis,
                                    session=int(s.session_id))
                self.speech.say(ctx, Utterance(speaker=a, t_ns=int(t_ns), text=text, addressees=(int(partner),),
                                               via=_DL.VIA_CALL))
                self.calls.utterance(a, T)
                self._bump("call_turns")
                if self.turn_sink is not None:  # 〔6-2 カレンダー 2〕通話の番の控え(腕のランだけ)
                    self.turn_sink(f"c:{int(s.session_id)}", a, T, cause.call_id, s.participants)
            else:
                self._hangup[int(s.session_id)] = cause.call_id
                self.calls.close_now(a, T, "退去")
                self._log(t_ns, a, W_HANG, cause, whom=int(partner), via=_DL.VIA_CALL)
                self._bump("call_hangups")

    def _ring_decisions(self, T: int, t_ns: int, sleeping: np.ndarray, main_now: set[int] = frozenset()) -> None:
        """着信に気づいた体(出る/出ない)。主の判断が先の体は鳴り続ける(次の刻みにまた気づく=仲裁)。"""
        for callee, r in self.mail.ringing_items():  # 逐次: 鳴っている電話の数ぶん
            nt = self.attn.notice_of(int(callee))
            if nt is None or int(nt[0]) != int(t_ns) or int(nt[1]) != _NOTICE_RING:
                continue  # この刻みに気づいていない(鳴り続ける)
            if int(callee) in main_now:
                self._bump("arbitration:ring")
                continue
            caller, t_ring = int(r[0]), int(r[1])
            c, cause = self._decide(T, t_ns, int(callee), _P.P_RING, [_P.cand(_P.K_ANSWER), _P.cand(_P.K_DECLINE)])
            self.mail.stop_ringing(caller, int(callee))
            if c.kind == _P.K_ANSWER:
                s = self.calls.invite(caller, int(callee), T, -1, same_cell=True, partner_idle=True, answered=True)
                if s is None:  # 話し中(1 人 1 会話の門)
                    self._log(t_ns, caller, W_UNREACHABLE, _P_CONTACT, whom=int(callee), via=_DL.VIA_CALL)
                    self._bump("unreachable_busy")
                    continue
                self._log(t_ns, int(callee), W_ANSWER, cause, whom=caller, via=_DL.VIA_CALL, received_ns=int(t_ns),
                          read_ns=int(t_ns))
                self.dev.take_out([int(callee)])
                self._screen_end([int(callee)], t_ns, "answer")  # 耳に当てる=画面から目を離す
                self._bump("answered")
            else:
                self._log(t_ns, int(callee), W_DECLINE, cause, whom=caller, via=_DL.VIA_CALL)
                self._bump("declined")

    def _caller_decisions(self, T: int, t_ns: int, main_now: set[int] = frozenset()) -> None:
        """鳴らしている人(待つ/切る)。主の判断が先の体は待ち続ける(仲裁)。"""
        for caller, c in self.mail.calling_items():  # 逐次: 呼び出しの数ぶん
            if int(c[2]) != 1 or int(c[1]) >= int(t_ns):
                continue
            if int(caller) in main_now:
                self._bump("arbitration:wait")
                continue
            callee = int(c[0])
            ch, cause = self._decide(T, t_ns, int(caller), _P.P_WAIT, [_P.cand(_P.K_WAIT), _P.cand(_P.K_HANG)])
            if ch.kind == _P.K_HANG:
                self.mail.stop_ringing(int(caller), callee)
                self._log(t_ns, int(caller), W_HANG, cause, whom=callee, via=_DL.VIA_CALL)
                self._bump("hung_up_waiting")
                self._bump("missed")

    def _person_decisions(self, T: int, t_ns: int, sleeping: np.ndarray, idle: list[int], notice: set[int],
                          main_now: set[int] = frozenset()) -> None:
        """画面を見ている体・通知に気づいた体・暇になった体の判断(体の番号の順)。通話中と呼び出し中の体は通話の判断だけ。
        主の判断が先の体(仲裁)は、通知と暇の判断を次の刻みに回す(``_defer``)・画面の判断は次の刻みにまた起きる。"""
        screen = set(int(a) for a in self.attn.on_screen().tolist())
        deferred, self._defer = self._defer, {}
        notice = set(notice) | {a for a, k in deferred.items() if k == 0}
        idle_set = set(idle) | {a for a, k in deferred.items() if k == 1}
        todo = sorted(screen | notice | idle_set)
        for a in todo:  # 逐次ループ宣言: その刻みに判断する体の数ぶん
            if bool(sleeping[a]) or not bool(self.dev._on[a]) or self.calls.is_busy(a) \
                    or self.mail.calling_of(a) is not None:
                continue
            if a in main_now:
                if a not in screen:
                    self._defer[a] = 0 if a in notice else 1
                self._bump("arbitration:person")
                continue
            if a in screen:
                self._screen_decision(T, t_ns, a)
            elif a in notice:
                if self.mail.unread_count(a):
                    self._notice_decision(T, t_ns, a)
            elif int(self.attn._gaze[a]) != _AT.GAZE_SCREEN:
                self._idle_decision(T, t_ns, a)

    def _unread_basis(self, a: int) -> tuple[tuple[int, int], ...]:
        """未読の届いた行の出来事の目印(診断の表から・届いた順)=読む判断の原因の入力。記録しないランは空。"""
        marks = self._ct_event_of.get(int(a))
        if not marks:
            return ()
        un = {int(r[0]) for r in self.mail.unread(a)}
        return tuple((int(x[1]), int(x[2])) for x in marks if int(x[0]) in un)

    def _drop_read_marks(self, a: int) -> None:
        """読んだ行の目印を診断の表から落とす(未読の行の目印だけ残す=有界)。"""
        marks = self._ct_event_of.get(int(a))
        if marks is None:
            return
        un = {int(r[0]) for r in self.mail.unread(a)}
        keep = [x for x in marks if int(x[0]) in un]
        if keep:
            marks[:] = keep
        else:
            del self._ct_event_of[int(a)]

    def _notice_decision(self, T: int, t_ns: int, a: int) -> None:
        basis = self._unread_basis(a)
        c, cause = self._decide(T, t_ns, a, _P.P_NOTICE,
                                [_P.cand(_P.K_READ_NOW, basis=basis), _P.cand(_P.K_LATER), _P.cand(_P.K_IGNORE)])
        if c.kind == _P.K_READ_NOW:
            self.dev.take_out([a])
            self.attn.look_at_screen([a], t_ns)
            self._bump("read_now")
            self._bump("phone_looks")
            self._read(T, t_ns, a, cause)
            return
        un = self.mail.unread(a)
        last = un[-1] if un else None
        w = W_LATER if c.kind == _P.K_LATER else W_IGNORE
        self._log(t_ns, a, w, cause, whom=None if last is None else int(last[1]),
                  via=_DL.VIAS[int(last[3])] if last is not None else V.VIA_NONE)
        self._bump("later" if c.kind == _P.K_LATER else "ignored")

    def _idle_decision(self, T: int, t_ns: int, a: int) -> None:
        c, cause = self._decide(T, t_ns, a, _P.P_IDLE, [_P.cand(_P.K_LOOK), _P.cand(_P.K_STAY)])
        if c.kind == _P.K_LOOK:
            self.dev.take_out([a])
            self.attn.look_at_screen([a], t_ns)
            self._log(t_ns, a, W_LOOK, cause)
            self._bump("phone_looks")
            self._bump("idle_looks")

    def _screen_decision(self, T: int, t_ns: int, a: int) -> None:
        cands = []
        if self.mail.unread_count(a):
            cands.append(_P.cand(_P.K_READ, basis=self._unread_basis(a)))
        msg_to = self.book.personal(self.agents, a, _CT.MESSAGE, T)
        call_to = self.book.personal(self.agents, a, _CT.CALL, T)
        groups = self.book.groups_of(a)
        if msg_to:
            cands.append(_P.cand(_P.K_SEND))
        if groups:
            cands.append(_P.cand(_P.K_SEND_GROUP))
        if call_to:
            cands.append(_P.cand(_P.K_CALL))
        cands += [_P.cand(_P.K_KEEP), _P.cand(_P.K_UP)]
        c, cause = self._decide(T, t_ns, a, _P.P_SCREEN, cands)
        self._bump("screen_steps")
        if c.kind == _P.K_READ:
            self._read(T, t_ns, a, cause)
        elif c.kind == _P.K_SEND:
            self._compose_personal(T, t_ns, a, msg_to)
        elif c.kind == _P.K_SEND_GROUP:
            self._compose_group(T, t_ns, a, groups)
        elif c.kind == _P.K_CALL:
            self._dial(T, t_ns, a, call_to)
        elif c.kind == _P.K_UP:
            self._screen_end([a], t_ns, "decided")
            self.dev.put_back([a])
            self._log(t_ns, a, W_UP, cause)
            self._bump("look_up_decided")

    def _read(self, T: int, t_ns: int, a: int, cause: LlmCall) -> None:
        rows = self.mail.read_all(a, t_ns)
        self._drop_read_marks(a)
        for r in rows:  # 逐次: 読んだ数ぶん
            self._hist_add("read_delay_minutes", (int(t_ns) - int(r[5])) // (SECONDS_PER_MINUTE * NS_PER_SECOND))
        self._bump("read_messages", len(rows))
        convs = _DL.senders_of(rows)
        for kind, key, _m in convs:  # 逐次: 読んだ会話の数ぶん(〔検収 M3 ②③〕読んだは会話ごとに 1 行・既読の行は書かない)
            sub = [r for r in rows if (int(r[2]) == int(key) if kind == "g" else (int(r[2]) < 0 and int(r[1]) == int(key)))]
            via = _DL.VIAS[int(sub[-1][3])]
            # 1-3 の欄の約束(届いた ≥ 起きた)により、読んだ行の届いた時刻は読んだ時刻(届いた時刻は原因の入力の行)
            self._log(t_ns, a, W_READ, cause, whom=f"group:{int(key)}" if kind == "g" else int(key), via=via,
                      received_ns=int(t_ns), read_ns=int(t_ns), how_much=len(sub))
        self._bump("read_rows", len(convs))
        if self.read_sink is not None and rows:  # 〔6-2 カレンダー 3=C3〕読んだメッセージの控え(腕のランだけ・控えるだけ)
            self.read_sink(int(T), int(a), [[int(r[0]), int(r[1]), int(r[2]), int(r[3])] for r in rows])
        for kind, key, _m in convs:  # 逐次: 読んだ会話の数ぶん
            self._reply_decision(T, t_ns, a, kind, key)

    def _reply_decision(self, T: int, t_ns: int, a: int, kind: str, key: int) -> None:
        c, cause = self._decide(T, t_ns, a, _P.P_REPLY,
                                [_P.cand(_P.K_REPLY), _P.cand(_P.K_STAMP), _P.cand(_P.K_NOREPLY)])
        if c.kind == _P.K_NOREPLY:
            self._bump("no_reply")
            return
        if c.kind == _P.K_STAMP:
            st, cause = self._decide(T, t_ns, a, _P.P_STAMP,
                                     [_P.cand(_P.K_STAMP_ITEM, f"[スタンプ]{w}", id=f"stamp:{w}") for w in _P.STAMPS])
            text = st.text
            self._bump("stamps")
        else:
            text = self._write_text(kind="message", sender=a, addressees=(key,)) if self.send_arm == "b" else c.text
            self._bump("replies")
        if kind == "g":
            members = [m for m in self.book.members(key) if m != a]
            if members:
                self._queue_send(T, t_ns, a, members, int(key), _DL.VIAS.index(_DL.VIA_GROUP), text, cause)
        else:
            self._queue_send(T, t_ns, a, [int(key)], -1, _DL.VIAS.index(_DL.VIA_MESSAGE), text, cause)

    def _compose_personal(self, T: int, t_ns: int, a: int, to: tuple[int, ...]) -> None:
        cands = [_P.cand(_P.K_TO, f"P-{b}", id=f"to:{b}") for b in to]
        c, cause = self._decide(T, t_ns, a, _P.P_WHOM, cands)
        b = int(c.id.split(":", 1)[1])
        text = self._write_text(kind="message", sender=a, addressees=(b,)) if self.send_arm == "b" else _P.K_SEND
        self._queue_send(T, t_ns, a, [b], -1, _DL.VIAS.index(_DL.VIA_MESSAGE), text, cause)
        self._bump("new_messages")

    def _compose_group(self, T: int, t_ns: int, a: int, groups: tuple[int, ...]) -> None:
        cands = [_P.cand(_P.K_GROUP, f"{self.book.group_kind(g)}のグループ", id=f"group:{g}") for g in groups]
        c, cause = self._decide(T, t_ns, a, _P.P_GROUP, cands)
        g = int(c.id.split(":", 1)[1])
        members = [m for m in self.book.members(g) if m != a]
        if not members:
            self._bump("group_alone")
            return
        text = (self._write_text(kind="group", sender=a, addressees=tuple(members)) if self.send_arm == "b"
                else _P.K_SEND_GROUP)
        self._queue_send(T, t_ns, a, members, g, _DL.VIAS.index(_DL.VIA_GROUP), text, cause)
        self._bump("new_group_messages")

    def _queue_send(self, T: int, t_ns: int, a: int, to: Sequence[int], group: int, via: int, text: str,
                    cause: LlmCall) -> None:
        """送る(打ち終わりは次の窓の境目=打つ時間の代わり)。文は発話の口の届け先の行の形(``Utterance``)で検査する。"""
        text, capped = _P.cap_text(text)
        if capped:
            self._bump("length_cap_hits")
        u = Utterance(speaker=int(a), t_ns=int(t_ns), text=text, addressees=tuple(int(x) for x in to),
                      via=_DL.VIAS[int(via)])
        self._reserve(_DL.P_SEND, int(t_ns), [int(a), int(group), int(via), u.text, int(u.mora), cause.call_id,
                                              str(cause.source), int(cause.number or 1), [int(x) for x in u.addressees]])
        self._bump("typed")
        if self.turn_sink is not None:  # 〔6-2 カレンダー 2〕メッセージを送る判断=チャットの番の控え(腕のランだけ)
            key = group_key(int(group)) if int(group) >= 0 else pair_key(int(a), int(to[0]))
            self.turn_sink(key, int(a), int(T), cause.call_id, u.addressees)

    def _dial(self, T: int, t_ns: int, a: int, to: tuple[int, ...]) -> None:
        cands = [_P.cand(_P.K_TO, f"P-{b}", id=f"to:{b}") for b in to]
        c, cause = self._decide(T, t_ns, a, _P.P_WHOM, cands)
        b = int(c.id.split(":", 1)[1])
        self._place_call(T, t_ns, a, b, cause)

    def _place_call(self, T: int, t_ns: int, a: int, b: int, cause: LlmCall) -> None:
        """電話をかける(本人の判断の答え ``cause`` の後=呼び出しの予約・着信は窓の境目)。"""
        self.mail.start_calling(a, b, t_ns)
        self._log(t_ns, a, W_DIAL, cause, whom=b, via=_DL.VIA_CALL)
        self._reserve(_DL.P_RING, int(t_ns), [int(a), int(b), int(t_ns)])
        self._screen_end([a], t_ns, "dial")  # 耳に当てる
        self._bump("calls_placed")

    def workplace_send(self, T: int, t_ns: int, a: int, target: int, *, groups: Sequence[int] = (),
                       words: str = "") -> tuple[str, str] | None:
        """〔第 6 期 6-2 カレンダー 3=C3 職場の連絡〕職場の連絡を C1 の口で送る(呼ぶのは系 calendar_3=腕のランだけ)。

        手段と宛先は本人の連絡の判断(J0・判断の種類=宛先 ``P_WHOM``=相手にメッセージ・相手に電話・職場のグループ)・文は文の口
        (腕 (c) は選択の言葉 ``words``=何の連絡か)・送るのは今の口(``_queue_send``=打ち終わりは次の窓の境目・``_place_call``)。
        職場の相手は初めから連絡先に持つ(CT5 (c))。寝ている・電源が切れた・通話中・呼び出し中の体は送れない(``None``=呼び手が
        控えて送り直す)。返り値=``(手段 msg/call/group, 送った判断の call_id)``。"""
        a, b = int(a), int(target)
        why = ("asleep" if int(self.agents.registry.activity[a]) == int(Activity.SLEEPING) else
               "device_off" if not bool(self.dev._on[a]) else
               "in_call" if self.calls.is_busy(a) or self.mail.calling_of(a) is not None else
               "no_target" if not (0 <= b < self.n) or b == a else "")
        if why:
            self._bump(f"c3:cannot_send:{why}")
            return None
        cands = [_P.cand(_P.K_TO, f"P-{b}(メッセージ)", id=f"msg:{b}"), _P.cand(_P.K_TO, f"P-{b}(電話)", id=f"call:{b}")]
        cands += [_P.cand(_P.K_GROUP, f"{self.book.group_kind(int(g))}のグループ", id=f"group:{int(g)}") for g in groups]
        c, cause = self._decide(T, t_ns, a, _P.P_WHOM, cands)
        how, _, x = c.id.partition(":")
        self._bump(f"c3:{how}")
        if how == "call":
            self._place_call(T, t_ns, a, b, cause)
            return how, cause.call_id
        if how == "group":
            g = int(x)
            members = [m for m in self.book.members(g) if m != a]
            text = (self._write_text(kind="group", sender=a, addressees=tuple(members)) if self.send_arm == "b"
                    else str(words or c.text))
            self._queue_send(T, t_ns, a, members, g, _DL.VIAS.index(_DL.VIA_GROUP), text, cause)
            return how, cause.call_id
        text = self._write_text(kind="message", sender=a, addressees=(b,)) if self.send_arm == "b" else str(words or c.text)
        self._queue_send(T, t_ns, a, [b], -1, _DL.VIAS.index(_DL.VIA_MESSAGE), text, cause)
        return how, cause.call_id

    def _call_ended(self, T: int, t_ns: int, s: Any) -> None:
        cid = self._hangup.pop(int(s.session_id), None)
        for p in s.participants:  # 逐次: 参加者の数ぶん(2)
            other = next((q for q in s.participants if q != p), None)
            cause = LlmCall(cid) if cid is not None else _P_CONV
            self._log(t_ns, int(p), W_CALL_END, cause, whom=other, via=_DL.VIA_CALL)
            self.dev.put_back([int(p)])
        self._bump(f"calls_closed:{s.close_reason}")
        self._hist_add("call_steps", int(T) - int(s.opened_tick))

    # ================================================================== 計器・manifest
    def manifest(self) -> dict[str, Any]:
        m = dict(sorted(self._meter.items()))
        dec = {k.split(":", 1)[1]: v for k, v in m.items() if k.startswith("decisions:")}
        rem = {k: v for k, v in m.items() if k.startswith(("remembered:", "not_remembered:"))}
        sal = {k: v for k, v in m.items() if k.startswith(("salient", "exposed:", "noticed_salient:"))}
        cfg = {
            "schema": SCHEMA, "arm": _ARM.ARM_C1, "unnoticed_arm": self.unnoticed_arm, "send_arm": self.send_arm,
            "contacts_source": self.book.source(),
            "queue_kinds": {"contact.ring": {"kind": _DL.KIND_RING, "rank": _DL.RANK_RING, "delivery": _DL.RING_DELIVERY},
                            "contact.send": {"kind": _DL.KIND_SEND, "rank": _DL.RANK_SEND, "delivery": _DL.SEND_DELIVERY}},
            "notice_min_level": {_AT.FOCUS_WORDS[k]: _DV.LEVEL_WORDS[v] for k, v in enumerate(NOTICE_MIN_LEVEL)},
            "device": {"ring_db_1m": _DV.RING_DB_1M, "place_atten_db": list(_DV.PLACE_ATTEN_DB),
                       "earphone_db": _DV.EARPHONE_DB, "snr_clear_db": _DV.SNR_CLEAR_DB,
                       "snr_detect_db": _DV.SNR_DETECT_DB, "noise_stage_db": list(_DV.NOISE_STAGE_DB),
                       "drain_per_hour": list(_DV.DRAIN_PER_HOUR),
                       # 〔つなぎ BR-CT1-CHARGE-AT-HOME〕家での充電の速さ(住まいの表の無いランは null=充電なし)
                       "charge_per_hour": None if self.home_cell is None else _DV.CHARGE_PER_HOUR, "shares0": {
                           "manner": _DV.MANNER_SHARE0, "bag": _DV.BAG_SHARE0, "earphones": _DV.EARPHONE_SHARE0}},
            "attention": {"peripheral_range_m": _AT.PERIPHERAL_RANGE_M,
                          "interrupt_conditions": sorted(int(x) for x in _AT.INTERRUPT_CONDITIONS),
                          "idle_activities": sorted(int(x) for x in _AT.IDLE_ACTIVITIES)},
            "port": self.port.name, "stamps": list(_P.STAMPS), "mock_text": _P.MOCK_TEXT,
            "message_max_chars": _P.MESSAGE_MAX_CHARS,
            "chat_silence_steps": int(CHAT_SILENCE_STEPS),
            "provisional": list(_DV.PROVISIONAL_VALUES + _AT.PROVISIONAL_VALUES + _P.PROVISIONAL_VALUES),
        }
        obs = {
            "meter": m, "decisions": dec,
            "read_delay_minutes": dict(sorted(self._ct_hist["read_delay_minutes"].items(), key=lambda kv: int(kv[0]))),
            "call_steps": dict(sorted(self._ct_hist["call_steps"].items(), key=lambda kv: int(kv[0]))),
            "screen_minutes": dict(sorted(self._ct_hist["screen_minutes"].items(), key=lambda kv: int(kv[0]))),
            "chats": self.chats.chat_counts(),
            "calls": {k: int(v) for k, v in self.calls.counters().items()},
            "mail": self.mail.mail_counts(), "devices": self.dev.summary(), "attention_now": self.attn.summary(),
            "salient": sal, "remembered": rem if self.remember_link else None,
            "bodiless_dropped": int(self.book.bodiless_dropped),
            "rendered": None if self.renderer is None else {k: int(getattr(self.renderer, k, 0)) for k in (
                "contact_lines", "contact_lines_over_budget", "contact_unnoticed_renders")},
        }
        return {**cfg, **obs}


def manifest_fields(layer: ContactLayer | None) -> dict[str, Any] | None:
    """manifest の ``contact_c1``(腕 c1 のランだけ・ほかは ``None``=欄を出さない)。"""
    return None if layer is None else layer.manifest()


def sys_contact(ctx: Any, b: Any) -> None:
    """系 contact(刻みの中・腕 c1 のランだけ立つ)。"""
    b.layers.contact.run_step(ctx.T, int(ctx.t_ns), ctx.td, agents=b.soa.agents, world=b.soa.world,
                              conv=b.layers.conv, runner=b.layers.runner, decision=b.scratch.decision)


def audit_causes(events: Iterable[Any], *, step_ns: int, issued: Any = None) -> dict[str, Any]:
    """負の対照の監査: 族 ``連絡`` の出来事のうち、本人の判断の語の原因が判断の呼び(LlmCall・源と番号つき)で、その時刻が
    判断の刻みかその後の窓の境目(送った=打ち終わり)か・届く語の原因が過程 contact か。

    〔検収 M2〕``issued``(層の :meth:`ContactLayer.issued_keys`)を渡すと、原因の call_id が層の発行した呼びにあり・体が出来事の
    体と同じで・判断の種類が語に合うか(:data:`WORD_PURPOSES`)も突き合わせる(偽の ``LlmCall`` を植えると落ちる)。
    食い違いの数と例を返す。"""
    have = None if issued is None else set(int(x) for x in np.asarray(issued, dtype=np.int64).tolist())
    bad: list[str] = []
    n = 0
    for ev in events:  # 逐次: 出来事の数ぶん(試験と記録の道具だけ)
        if not str(ev.what).startswith(f"{V.FAMILY_CONTACT}:"):
            continue
        n += 1
        c = ev.cause
        if ev.what in PERSON_WORDS:
            got = _P.parse_call_id(getattr(c, "call_id", "")) if isinstance(c, LlmCall) else None
            main = None
            if got is None and isinstance(c, LlmCall) and ev.what == W_LOOK:  # 主の判断の候補で選んだ(起床の級 ≥ 0)
                parts = str(c.call_id).split(":")
                if len(parts) == 3 and all(x.lstrip("-").isdigit() for x in parts) and int(parts[2]) >= 0:
                    main = (int(parts[0]), int(parts[1]), 0)
            if got is None and main is None or c.source is None or c.number is None:
                bad.append(f"{ev.what} の原因が本人の判断でない: {c!r}")
                continue
            st, who, serial = got if got is not None else main
            if int(who) != int(ev.who):
                bad.append(f"{ev.what} の体 {ev.who} と判断の呼びの体 {who} が違う")
            if have is not None:
                try:
                    k = issued_key(st, who, serial)
                except ValueError:
                    k = -1
                if k not in have:
                    bad.append(f"{ev.what} の原因 {c.call_id} は層の発行した判断の呼びに無い")
            if got is not None and _P.purpose_of_serial(serial) not in WORD_PURPOSES.get(ev.what, frozenset()):
                bad.append(f"{ev.what} の原因の判断の種類 {_P.purpose_of_serial(serial)} が語に合わない")
            t_dec = int(st) * int(step_ns)
            if ev.what == W_SENT:
                if not (t_dec < int(ev.t_ns) <= t_dec + int(step_ns)):
                    bad.append(f"送った時刻 {ev.t_ns} が判断の刻み {st} の次の窓の境目でない")
            elif int(ev.t_ns) != t_dec:
                bad.append(f"{ev.what} の時刻 {ev.t_ns} が判断の刻み {st} と違う")
            if ev.what == W_READ and int(ev.read_ns) != int(ev.t_ns):
                bad.append("読んだ時刻が判断の時刻と違う")
        elif ev.what in ENGINE_WORDS:
            if not (isinstance(c, Process) and c.name == "contact"):
                bad.append(f"{ev.what} の原因が網(過程 contact)でない: {c!r}")
    return {"events": n, "violations": len(bad), "examples": bad[:5]}
