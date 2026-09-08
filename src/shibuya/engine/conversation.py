"""engine.conversation — 会話プロトコル(行動契約書 §3)のセッション状態機械。

正典(逐語・行動契約書 §3)
    「**1呼=1発話ブロック**(実会話30-60秒相当を1発話に圧縮して言語化)。…**知覚契約書§6の
    会話ターン起床(不応期0)の単位は発話ブロック**。」
    「開始ゲート(エンジン): 同一セル∧距離≦d_talk∧相手idle∧拒否履歴なし∧双方に会話呼予算。
    招待→応答判定(エンジン確率・較正目標=声かけ応答率≈0.8)→不応答は「無視された」イベント
    (呼を消費しない)。状態=invited/walkingOver/participating(AI Town先例)。」
    「進行: 話者選択(WHO)=エンジン(会話分析規則)・相槌/最小応答=エンジン生成(LLMを呼ばない)・
    参加上限3(2者既定)・1人1会話・割り込みは次の移行点での優先権奪取に離散化。」
    「**終了はLLMに決めさせない**: ハード=max_turns 1体3呼(往復6呼・重要度上位のみ+2呼)/
    ソフト=話題スタック空∨沈黙>閾値∨片方が「退去」∨セル離脱/CLOSING=定型の締め1発話→terminal。」
- 知覚契約書 §6 不応期表: 「(iv)会話ターン **0**」=会話起床には床を置かない。
- 運用設計書 §2.2 Phase C: 世界状態の書き込みは resolve 一本。**本モジュールは書かない**
  (セッション表はエンジン側の付帯状態で、``AgentState``/``World`` には触れない)。

逐次ループ宣言(P4)
1. ``ConversationManager.step``: **活動中セッション数**ぶんのループ(個体数ではない。
   1体1会話・参加上限2で、選抜呼数(平均35/tick)に律速される数十件級)。
2. ``ConversationManager.wake_candidates``: 同上(活動中セッション数ぶん)。
どちらも個体数 n に比例するループではない(P4 の禁止対象外)。

expedient(本モジュール分)
- **d_talk の代理**: C2/C3 の個体はセル内座標を持たない(``AgentState`` は cell と xy を
  持つが会話距離の判定に使える精度が無い)。よって「距離≦d_talk(≈1m)」は
  **「同一セル ∧ 双方 idle」**で代理する。``D_TALK_METERS`` は宣言だけ置く(C4 で群衆物理が
  入ったら xy 距離に差し替える)。
- 応答確率 **0.8**(契約書「較正目標=声かけ応答率≈0.8」)。較正データ無しの定数。
- 話者交替は**招待者始まりの単純交替**。契約書は「話者選択(WHO)=エンジン(会話分析規則)」
  としか言わず規則を与えていない。
- **話題スタック**の初期本数 = ``max_turns``(1往復ごとに1本消費)。契約書に本数の規定なし。
- **沈黙閾値** ``silence_ticks=5``・**セッション寿命** ``max_session_ticks=60``。
  契約書は「沈黙>閾値」としか言わない。寿命はアービタが話者を選ばないまま残るセッションの
  掃除口(有界化 D-R2-6)。
- **拒否履歴の記憶** ``refusal_memory_ticks=60``(知覚契約書 §6「知人出現: 同一相手60分」に
  合わせた)。「無視された」も同じ表に入れる(でないと同じ相手へ毎tick招待し続ける)。
  向きは持たない(無順序対で記憶する)。
- 相槌・締めの定型文(``BACKCHANNELS``/``CLOSING_UTTERANCE``)。文面凍結の対象。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Final, Iterable, Mapping, Sequence

import numpy as np

from shibuya.agents.state import WakeCondition
from shibuya.core.rng import stream
from shibuya.core.types import EventClass

__all__ = [
    "D_TALK_METERS",
    "ACCEPT_PROBABILITY",
    "MAX_TURNS",
    "IMPORTANT_EXTRA_TURNS",
    "MAX_PARTICIPANTS",
    "REFUSAL_MEMORY_TICKS",
    "SILENCE_TICKS",
    "MAX_SESSION_TICKS",
    "INVITE_RNG_DOMAIN",
    "BACKCHANNELS",
    "CLOSING_UTTERANCE",
    "CLOSE_REASONS",
    "ConvState",
    "Session",
    "GateResult",
    "ConversationManager",
]

#: 契約書 §2.1「距離≦d_talk(≈1m)」。C3 では**同一セル**で代理する(上の expedient)。
D_TALK_METERS: Final[float] = 1.0
#: 声かけ応答率(契約書「較正目標≈0.8」・expedient)。
ACCEPT_PROBABILITY: Final[float] = 0.8
#: ハード終了: 1体あたりの発話ブロック数(契約書 max_turns=3・予算由来の expedient)。
MAX_TURNS: Final[int] = 3
#: 「重要度上位のみ+2呼」(契約書 §3)。
IMPORTANT_EXTRA_TURNS: Final[int] = 2
#: 参加上限(契約書「参加上限3(2者既定)」)。
MAX_PARTICIPANTS: Final[int] = 2
#: 拒否/無視の記憶[tick](expedient)。
REFUSAL_MEMORY_TICKS: Final[int] = 60
#: 沈黙のソフト終了閾値[tick](expedient)。
SILENCE_TICKS: Final[int] = 5
#: セッション寿命の上限[tick](有界化・expedient)。
MAX_SESSION_TICKS: Final[int] = 60
#: 招待の応答判定に使う RNG ドメイン。
INVITE_RNG_DOMAIN: Final[str] = "conversation.invite"

#: 相槌・最小応答(**エンジン生成=LLMを呼ばない**・文面凍結)。
BACKCHANNELS: Final[tuple[str, ...]] = ("うん", "なるほど", "そうですね")
#: CLOSING の定型締め1発話(文面凍結)。
CLOSING_UTTERANCE: Final[str] = "それじゃ、また。"

#: 終了理由(診断行の分類)。
CLOSE_REASONS: Final[tuple[str, ...]] = (
    "hard",  # max_turns 到達
    "soft_topics",  # 話題スタック空
    "soft_silence",  # 沈黙 > 閾値
    "退去",  # 片方が「退去」
    "left_cell",  # セル離脱(相手が去った)
    "timeout",  # セッション寿命(expedient の掃除口)
)


class ConvState(IntEnum):
    """セッションの状態(契約書 §3「invited/walkingOver/participating」+ 終了2段)。"""

    INVITED = 0
    WALKING_OVER = 1
    PARTICIPATING = 2
    CLOSING = 3
    TERMINAL = 4


@dataclass
class Session:
    """1会話セッション。

    Attributes:
        session_id: 通し番号(決定論・生成順)。
        participants: 参加者(``participants[0]`` = 招待者)。
        cell: 開始セル。
        state: ``ConvState``。
        opened_tick: 招待が通った tick。
        speaker_index: 次に話す参加者の添字。
        calls: 参加者 → 消費した発話ブロック数(=呼数)。
        max_turns_of: 参加者 → その個体のハード上限(重要度上位は +2)。
        topics: 話題スタック(本数だけを持つ・中身は使わない)。
        last_utterance_tick: 直近の発話ブロック tick(沈黙判定の基準)。
        blocks: 生成された発話ブロック数(相槌を含まない)。
        interrupt_queue: 割り込み要求(次の移行点で優先権を渡す)。
        closed_tick / close_reason: 終了時に埋まる。
    """

    session_id: int
    participants: list[int]
    cell: int
    state: ConvState
    opened_tick: int
    speaker_index: int = 0
    calls: dict[int, int] = field(default_factory=dict)
    max_turns_of: dict[int, int] = field(default_factory=dict)
    topics: int = 0
    last_utterance_tick: int = -1
    blocks: int = 0
    interrupt_queue: list[int] = field(default_factory=list)
    closed_tick: int = -1
    close_reason: str = ""

    @property
    def inviter(self) -> int:
        return self.participants[0]

    @property
    def speaker(self) -> int:
        """いま話す番の参加者。"""
        return self.participants[self.speaker_index % len(self.participants)]

    @property
    def active(self) -> bool:
        return self.state in (ConvState.INVITED, ConvState.WALKING_OVER, ConvState.PARTICIPATING)

    def has_budget(self, agent_id: int) -> bool:
        """その個体にまだ発話ブロックの残りがあるか(ハード上限)。"""
        return self.calls.get(agent_id, 0) < self.max_turns_of.get(agent_id, MAX_TURNS)


@dataclass(frozen=True)
class GateResult:
    """開始ゲートの判定(契約書 §3 の5条件)。"""

    ok: bool
    reason: str = ""


class ConversationManager:
    """会話セッションの生成・進行・終了(**終了はLLMに決めさせない**)。

    Args:
        master_seed: ランの ``master_seed``(応答判定の RNG 鍵)。
        max_turns: 1体あたりの発話ブロック上限(ハード終了)。
        extra_turns_for_important: 重要度上位の追加呼数。
        max_participants: 参加上限(既定2・契約書の上限は3)。
        accept_probability: 声かけ応答率。
        refusal_memory_ticks: 拒否/無視の記憶[tick]。
        silence_ticks: 沈黙のソフト終了閾値[tick]。
        max_session_ticks: セッション寿命[tick]。
        walk_over_ticks: WALKING_OVER に留まる tick(既定0=ゲートが同一セルを要求するため)。
        important: 重要度上位の個体 id(``+2呼``の対象)。

    Example:
        >>> m = ConversationManager(master_seed=1)
        >>> s = m.invite(3, 5, tick=0, cell=7, same_cell=True, partner_idle=True)
        >>> s is None or s.state is ConvState.PARTICIPATING
        True
    """

    def __init__(
        self,
        master_seed: int | str,
        *,
        max_turns: int = MAX_TURNS,
        extra_turns_for_important: int = IMPORTANT_EXTRA_TURNS,
        max_participants: int = MAX_PARTICIPANTS,
        accept_probability: float = ACCEPT_PROBABILITY,
        refusal_memory_ticks: int = REFUSAL_MEMORY_TICKS,
        silence_ticks: int = SILENCE_TICKS,
        max_session_ticks: int = MAX_SESSION_TICKS,
        walk_over_ticks: int = 0,
        topics_per_session: int | None = None,
        important: Iterable[int] = (),
        domain: str = INVITE_RNG_DOMAIN,
    ) -> None:
        if max_participants < 2 or max_participants > 3:
            raise ValueError("参加上限は 2..3(契約書 §3)")
        if not (0.0 <= accept_probability <= 1.0):
            raise ValueError("accept_probability は 0..1")
        self.master_seed = master_seed
        self.domain = domain
        self.max_turns = int(max_turns)
        self.extra_turns_for_important = int(extra_turns_for_important)
        self.max_participants = int(max_participants)
        self.accept_probability = float(accept_probability)
        self.refusal_memory_ticks = int(refusal_memory_ticks)
        self.silence_ticks = int(silence_ticks)
        self.max_session_ticks = int(max_session_ticks)
        self.walk_over_ticks = int(walk_over_ticks)
        self.topics_per_session = int(topics_per_session if topics_per_session is not None else max_turns)
        self.important: set[int] = {int(a) for a in important}

        self.sessions: dict[int, Session] = {}
        self._of_agent: dict[int, int] = {}  # agent → session_id(1人1会話)
        self._refusal_until: dict[tuple[int, int], int] = {}
        self._next_id = 0
        # ---- 診断 ----
        self.n_opened = 0
        self.n_ignored_invites = 0
        self.n_gate_rejected = 0
        self.n_blocks = 0
        self.n_backchannels = 0
        self.n_interrupts = 0
        self.closed_by_reason: dict[str, int] = {r: 0 for r in CLOSE_REASONS}
        #: 「無視された」イベント(呼を消費しない)。``(tick, inviter, invitee)``。
        self.ignored_events: list[tuple[int, int, int]] = []

    # ---------------------------------------------------------------- 参照
    def session_of(self, agent_id: int) -> Session | None:
        """その個体が参加中のセッション(なければ None)。"""
        sid = self._of_agent.get(int(agent_id))
        return self.sessions.get(sid) if sid is not None else None

    def is_busy(self, agent_id: int) -> bool:
        """1人1会話の判定。"""
        return self.session_of(agent_id) is not None

    @property
    def n_active(self) -> int:
        return sum(1 for s in self.sessions.values() if s.active)

    def max_turns_for(self, agent_id: int) -> int:
        """その個体のハード上限(重要度上位は +2)。"""
        return self.max_turns + (
            self.extra_turns_for_important if int(agent_id) in self.important else 0
        )

    @staticmethod
    def _pair(a: int, b: int) -> tuple[int, int]:
        return (int(a), int(b)) if int(a) <= int(b) else (int(b), int(a))

    def refused_recently(self, a: int, b: int, tick: int) -> bool:
        """拒否/無視の履歴が記憶内に残っているか。"""
        until = self._refusal_until.get(self._pair(a, b))
        return until is not None and int(tick) < until

    # ---------------------------------------------------------------- 開始ゲート
    def gate(
        self,
        inviter: int,
        invitee: int,
        tick: int,
        *,
        same_cell: bool,
        partner_idle: bool,
        inviter_has_budget: bool = True,
        partner_has_budget: bool = True,
    ) -> GateResult:
        """契約書 §3 の開始ゲート(同一セル∧距離≦d_talk∧相手idle∧拒否履歴なし∧双方に呼予算)。

        ``距離≦d_talk`` は ``same_cell`` で代理する(本モジュール冒頭の expedient)。
        """
        if int(inviter) == int(invitee):
            return GateResult(False, "self")
        if not same_cell:
            return GateResult(False, "not_same_cell")
        if not partner_idle:
            return GateResult(False, "partner_busy")
        if self.is_busy(inviter):
            return GateResult(False, "inviter_in_session")
        if self.is_busy(invitee):
            return GateResult(False, "partner_in_session")
        if self.refused_recently(inviter, invitee, tick):
            return GateResult(False, "refused_before")
        if not (inviter_has_budget and partner_has_budget):
            return GateResult(False, "no_call_budget")
        return GateResult(True, "")

    def _accepts(self, inviter: int, tick: int) -> bool:
        """応答判定(エンジン確率・決定論)。

        RNG: ``core.rng.stream(master_seed, "conversation.invite", tick, inviter)``(運用設計書 §2.5 のカウンタ順)
        (**親の指定どおりの引数順**。運用設計書 §2.5 のカウンタ順は
        ``(tick, entity_id, draw_index)`` で、``llm.mock`` はそちらに従っている=不一致を
        報告済み。どちらもカウンタベースなので T4「規模不変」は満たす)。
        """
        g = stream(self.master_seed, self.domain, int(tick), int(inviter))  # 運用設計書 §2.5: カウンタ=(tick, entity_id, …)
        return bool(g.random() < self.accept_probability)

    # ---------------------------------------------------------------- 招待
    def invite(
        self,
        inviter: int,
        invitee: int,
        tick: int,
        cell: int,
        *,
        same_cell: bool,
        partner_idle: bool,
        inviter_has_budget: bool = True,
        partner_has_budget: bool = True,
    ) -> Session | None:
        """招待 → 応答判定 → セッション生成。

        Returns:
            成立した ``Session``。ゲート不通過・不応答なら ``None``
            (**不応答は「無視された」イベントで呼を消費しない**=契約書 §3)。
        """
        g = self.gate(
            inviter, invitee, tick,
            same_cell=same_cell, partner_idle=partner_idle,
            inviter_has_budget=inviter_has_budget, partner_has_budget=partner_has_budget,
        )
        if not g.ok:
            self.n_gate_rejected += 1
            return None
        if not self._accepts(inviter, tick):
            self.n_ignored_invites += 1
            self.ignored_events.append((int(tick), int(inviter), int(invitee)))
            self._remember_refusal(inviter, invitee, tick)
            return None
        return self._open(inviter, invitee, tick, cell)

    def _open(self, inviter: int, invitee: int, tick: int, cell: int) -> Session:
        sid = self._next_id
        self._next_id += 1
        participants = [int(inviter), int(invitee)]
        session = Session(
            session_id=sid,
            participants=participants,
            cell=int(cell),
            state=ConvState.WALKING_OVER if self.walk_over_ticks > 0 else ConvState.PARTICIPATING,
            opened_tick=int(tick),
            calls={a: 0 for a in participants},
            max_turns_of={a: self.max_turns_for(a) for a in participants},
            topics=self.topics_per_session,
            last_utterance_tick=int(tick),
        )
        self.sessions[sid] = session
        for a in participants:
            self._of_agent[a] = sid
        self.n_opened += 1
        return session

    def join(self, session: Session, agent_id: int, tick: int) -> bool:
        """3人目の参加(契約書「参加上限3」)。上限・1人1会話を満たすときだけ通る。"""
        if not session.active or len(session.participants) >= self.max_participants:
            return False
        if self.is_busy(agent_id):
            return False
        a = int(agent_id)
        session.participants.append(a)
        session.calls[a] = 0
        session.max_turns_of[a] = self.max_turns_for(a)
        self._of_agent[a] = session.session_id
        return True

    def _remember_refusal(self, a: int, b: int, tick: int) -> None:
        self._refusal_until[self._pair(a, b)] = int(tick) + self.refusal_memory_ticks

    def record_refusal(self, a: int, b: int, tick: int) -> None:
        """「断る」による拒否履歴(契約書 §2.1 断る=関係辺強度−Δ・§3 ゲートの材料)。"""
        self._remember_refusal(a, b, tick)

    # ---------------------------------------------------------------- 進行
    def wake_candidates(self, tick: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """この tick に起こすべき話者(会話ターン起床・**不応期0**)。

        Returns:
            ``(agent_id[int64], condition[int8], class_rank[int64])``。
            ``condition`` は ``WakeCondition.CONVERSATION_TURN``、
            ``class_rank`` は ``EventClass.CONVERSATION``(最優先クラス)。

        逐次ループ宣言(P4): 活動中セッション数ぶん。
        """
        speakers: list[int] = []
        for s in self.sessions.values():
            if s.state is not ConvState.PARTICIPATING:
                continue
            if s.last_utterance_tick >= int(tick):
                continue  # この tick で既に話した
            speaker = s.speaker
            if s.has_budget(speaker):
                speakers.append(speaker)
        n = len(speakers)
        return (
            np.asarray(speakers, dtype=np.int64),
            np.full(n, int(WakeCondition.CONVERSATION_TURN), dtype=np.int8),
            np.full(n, int(EventClass.CONVERSATION), dtype=np.int64),
        )

    def backchannel_for(self, session: Session, agent_id: int) -> str:
        """相槌・最小応答(**エンジン生成=LLMを呼ばない**・決定論)。"""
        self.n_backchannels += 1
        return BACKCHANNELS[(session.session_id + session.blocks + int(agent_id)) % len(BACKCHANNELS)]

    def request_interrupt(self, session_id: int, agent_id: int) -> bool:
        """割り込み要求(**次の移行点**で優先権を渡す=契約書 §3 の離散化)。"""
        s = self.sessions.get(int(session_id))
        if s is None or not s.active or int(agent_id) not in s.participants:
            return False
        s.interrupt_queue.append(int(agent_id))
        self.n_interrupts += 1
        return True

    def utterance(
        self, agent_id: int, tick: int, *, action: str | None = None, comment: str = ""
    ) -> Session | None:
        """1発話ブロック(=1呼)を記録し、話者を進め、終了条件を見る。

        Args:
            agent_id: 話した個体。
            tick: 発話 tick。
            action: パーサが取った行動語(``退去`` ならソフト終了)。
            comment: 「ひと言」欄(発話本文)。

        Returns:
            そのセッション(参加していなければ None)。
        """
        s = self.session_of(agent_id)
        if s is None or s.state is not ConvState.PARTICIPATING:
            return None
        a = int(agent_id)
        s.calls[a] = s.calls.get(a, 0) + 1
        s.blocks += 1
        s.last_utterance_tick = int(tick)
        self.n_blocks += 1

        if action == "退去":
            self._close(s, int(tick), "退去")
            return s

        # 話者交替(次の移行点)。割り込みがあればそこで優先権を渡す。
        self._advance_speaker(s)

        # ハード終了: 全員が上限に達した
        if all(not s.has_budget(p) for p in s.participants):
            self._close(s, int(tick), "hard")
            return s
        # ソフト終了: 話題スタック空
        if s.topics <= 0:
            self._close(s, int(tick), "soft_topics")
        return s

    def _advance_speaker(self, s: Session) -> None:
        if s.interrupt_queue:
            nxt = s.interrupt_queue.pop(0)
            if nxt in s.participants:
                s.speaker_index = s.participants.index(nxt)
                return
        s.speaker_index = (s.speaker_index + 1) % len(s.participants)
        if s.speaker_index == 0:
            s.topics -= 1  # 1往復=話題1本(expedient)
        # 上限に達した話者は飛ばす(最大 参加者数 回)
        for _ in range(len(s.participants)):
            if s.has_budget(s.speaker):
                break
            s.speaker_index = (s.speaker_index + 1) % len(s.participants)

    # ---------------------------------------------------------------- 終了
    def step(
        self,
        tick: int,
        *,
        cell: Sequence[int] | np.ndarray | None = None,
        in_conversation: Sequence[bool] | np.ndarray | None = None,
    ) -> list[Session]:
        """1 tick 進める(WALKING_OVER→PARTICIPATING・ソフト終了・CLOSING→TERMINAL)。

        Args:
            tick: 現在 tick。
            cell: 個体 → 現在セル(セル離脱の判定に使う。None なら判定しない)。
            in_conversation: 個体 → まだ会話状態か(resolve が ``退去`` を適用した後の掃除)。

        Returns:
            この tick に TERMINAL へ落ちたセッション。

        逐次ループ宣言(P4): 活動中セッション数ぶん。
        """
        finished: list[Session] = []
        for s in list(self.sessions.values()):
            if s.state is ConvState.TERMINAL:
                continue
            if s.state is ConvState.CLOSING:
                self._terminate(s, int(tick))
                finished.append(s)
                continue
            if s.state is ConvState.INVITED or s.state is ConvState.WALKING_OVER:
                if int(tick) - s.opened_tick >= self.walk_over_ticks:
                    s.state = ConvState.PARTICIPATING
                continue
            # --- PARTICIPATING のソフト終了 ---
            if cell is not None and self._left_cell(s, cell):
                self._close(s, int(tick), "left_cell")
                continue
            if in_conversation is not None and self._dropped_out(s, in_conversation):
                self._close(s, int(tick), "left_cell")
                continue
            if int(tick) - s.last_utterance_tick > self.silence_ticks:
                self._close(s, int(tick), "soft_silence")
                continue
            if int(tick) - s.opened_tick >= self.max_session_ticks:
                self._close(s, int(tick), "timeout")
        return finished

    def _left_cell(self, s: Session, cell) -> bool:
        arr = np.asarray(cell)
        for p in s.participants:
            if p >= arr.size or int(arr[p]) != s.cell:
                return True
        return False

    def _dropped_out(self, s: Session, in_conversation) -> bool:
        arr = np.asarray(in_conversation)
        for p in s.participants:
            if p >= arr.size or not bool(arr[p]):
                return True
        return False

    def _close(self, s: Session, tick: int, reason: str) -> None:
        """CLOSING へ入る(**定型の締め1発話**を出してから TERMINAL)。"""
        if s.state in (ConvState.CLOSING, ConvState.TERMINAL):
            return
        s.state = ConvState.CLOSING
        s.close_reason = reason
        self.closed_by_reason[reason] = self.closed_by_reason.get(reason, 0) + 1
        # 締めの1発話はエンジン生成(LLMを呼ばない)
        s.blocks += 1

    def closing_utterance(self, s: Session) -> str:
        """CLOSING の定型締め(文面凍結)。"""
        return CLOSING_UTTERANCE

    def _terminate(self, s: Session, tick: int) -> None:
        s.state = ConvState.TERMINAL
        s.closed_tick = int(tick)
        for p in s.participants:
            if self._of_agent.get(p) == s.session_id:
                del self._of_agent[p]

    def close_now(self, agent_id: int, tick: int, reason: str = "退去") -> Session | None:
        """その個体のセッションを即座に閉じる(``退去`` の即時反映)。"""
        s = self.session_of(agent_id)
        if s is None:
            return None
        self._close(s, int(tick), reason)
        return s

    def purge_terminal(self) -> int:
        """TERMINAL のセッションを表から落とす(有界化 D-R2-6)。

        逐次ループ宣言(P4): セッション数ぶん。
        """
        dead = [sid for sid, s in self.sessions.items() if s.state is ConvState.TERMINAL]
        for sid in dead:
            del self.sessions[sid]
        return len(dead)

    # ---------------------------------------------------------------- 診断
    def counters(self) -> Mapping[str, int]:
        """診断行に載せる計数(§9.1 の会話行)。"""
        out: dict[str, int] = {
            "sessions_opened": self.n_opened,
            "sessions_active": sum(1 for s in self.sessions.values() if s.active),
            "sessions_closed": sum(self.closed_by_reason.values()),
            "ignored_invites": self.n_ignored_invites,
            "gate_rejected": self.n_gate_rejected,
            "utterance_blocks": self.n_blocks,
            "backchannels": self.n_backchannels,
            "interrupts": self.n_interrupts,
        }
        for reason in CLOSE_REASONS:
            out[f"closed_{reason}"] = int(self.closed_by_reason.get(reason, 0))
        return out
