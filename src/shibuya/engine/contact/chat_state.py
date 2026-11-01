"""engine.contact.chat_state — チャットの会話の状態(第 6 期 6-4 C1・決定 10-12 §4-2 TM1)。

正: TM1「続いているチャットは『チャットの会話の状態』にし、対面の会話と同じ細かい時計(打つ時間・読む間)で 1 通ずつ扱う。
ながらスマホもある」・発注「対面の会話(``conversation.py``)と同じ形の状態にする(二重に作らない=共通の部分を読む)」。

- 状態の器は対面の会話と同じ ``engine.conversation.Session``(参加者・状態 ``ConvState``・開いた刻み・話す番・人ごとの数・
  最後の発話の刻み・発話の数・終わった刻みと理由)と ``ConvState`` の遷移(招待 → 参加 → 締め → 終わり)。終わりの理由の語も
  同じ表(``CLOSE_REASONS``)。持ち主 :class:`ChatBook`(状態台帳の腕の行 ``CT1C``・道筋 ``contact.chats``)。
- 1 通ずつ: 最初の 1 通で招待(``INVITED``)・相手(最初に送った人と違う人)の 1 通で参加(``PARTICIPATING``=続いている
  チャット)・話す番は最後に送った人の次。沈黙の閾値(``CHAT_SILENCE_STEPS``=対面の会話の ``SILENCE_TICKS`` と同じ値)を
  超えて 1 通も無ければ締め(``soft_silence``)→ 次の刻みで終わり → 掃除。
- 細かい時計(打つ時間・読む間)は 6-3 の T2 の口が来るまで窓の境目で代える(``engine.contact.deliver`` の送信の予約=打ち終わりは
  次の窓の境目・読む時刻は本人の判断の時刻=宣言・つなぎの台帳 ``DOC-ct-c1-chat-clock``)。
- 上限 ``CHAT_MAX_BLOCKS``(1 つのチャットの発話の数)は安全装置だけ(当たったら締めて数える)。
- 〔検収 L1〕遷移は会話の器のコード(``ConversationManager`` の子=締め ``_close``・終わり ``_terminate``・参加の沈黙の
  ソフト終了と締め → 終わりの ``step``・掃除 ``purge_terminal``・終わりの理由の数え)をそのまま使う。チャットだけの違いは 3 つ:
  (1) 1 人が同時に幾つものチャットに居る=1 人 1 会話の表 ``_of_agent`` を使わない(チャットの鍵 ``_of_key`` で引く)・
  (2) 招待(返事の無い 1 通)は歩いて近づく段が無い=``walk_over_ticks`` を使わず相手の返事で参加になる・返事の無いまま沈黙の
  閾値を超えたら締める(会話の器の ``step`` は参加の段の沈黙しか見ない=この 1 行だけ足す)・(3) 話題の数で締めない。

**未リサーチ(expedient)**: 沈黙の閾値を対面と同じ値にしたこと・安全装置の上限 200 通・グループのチャットも同じ器(参加者=
グループの成員)。

逐次ループ宣言: :meth:`ChatBook.step` は生きているチャットの数ぶん(体の数に比例しない=送った数で決まる)。
"""

from __future__ import annotations

from typing import Any, Final, Sequence

from shibuya.engine.contact.arm import LEDGER_ARM
from shibuya.engine.conversation import CLOSE_REASONS, SILENCE_TICKS, ConversationManager, ConvState, Session

__all__ = ["CHAT_SILENCE_STEPS", "CHAT_MAX_BLOCKS", "ChatBook", "pair_key", "group_key"]

#: チャットの沈黙の閾値[刻み](対面の会話の ``SILENCE_TICKS`` と同じ値=同じ仕組み)。
CHAT_SILENCE_STEPS: Final[int] = int(SILENCE_TICKS)
#: 1 つのチャットの発話の数の上限(安全装置)。
CHAT_MAX_BLOCKS: Final[int] = 200
_CAP_REASON: Final[str] = "hard"
#: 使わない段の長さ(歩いて近づく・寿命・話題の数=チャットには無い)。
_NEVER: Final[int] = 1 << 40
assert _CAP_REASON in CLOSE_REASONS


def pair_key(a: int, b: int) -> str:
    """1 対 1 のチャットの鍵(順に依らない)。"""
    x, y = sorted((int(a), int(b)))
    return f"p:{x}:{y}"


def group_key(g: int) -> str:
    """グループのチャットの鍵(グループの一覧の行の番号)。"""
    return f"g:{int(g)}"


class ChatBook(ConversationManager):
    """続いているチャットの状態(会話の器の子・``Session`` の表)。書く口は :meth:`on_message` と :meth:`step` だけ。"""

    LEDGER_ARM: Final[str] = LEDGER_ARM

    def __init__(self) -> None:
        super().__init__(0, max_turns=CHAT_MAX_BLOCKS, max_participants=3, silence_ticks=CHAT_SILENCE_STEPS,
                         max_session_ticks=_NEVER, walk_over_ticks=_NEVER, topics_per_session=_NEVER)
        # 参加上限(max_participants)は会話の器の招待と参加の門だけが読む=チャットは門を通らない(成員はグループの一覧)
        #: チャットの鍵 → 生きているセッションの番号。
        self._of_key: dict[str, int] = {}
        #: 計器(診断): 開いた・参加になった・通の数・安全装置に当たった(締めの理由は会話の器の ``closed_by_reason``)。
        self._chat_meter: dict[str, int] = {"opened": 0, "joined": 0, "messages": 0, "cap_hits": 0}

    # ------------------------------------------------------------------ 書く口
    def on_message(self, key: str, sender: int, members: Sequence[int], step: int) -> Session:
        """1 通(``sender`` から ``members`` へ)をチャットの状態に入れる。開いていなければ開く(招待)。"""
        a = int(sender)
        sid = self._of_key.get(key)
        s = self.sessions.get(sid) if sid is not None else None
        if s is None or not s.active:
            sid = int(self._next_id)
            self._next_id = sid + 1
            parts = [a] + [int(m) for m in members if int(m) != a]
            s = Session(session_id=sid, participants=parts, cell=-1, state=ConvState.INVITED, opened_tick=int(step),
                        calls={p: 0 for p in parts}, max_turns_of={p: CHAT_MAX_BLOCKS for p in parts},
                        topics=_NEVER, last_utterance_tick=int(step))
            self.sessions[sid] = s
            self._of_key[key] = sid
            self.n_opened += 1
            self._chat_meter["opened"] += 1
        elif s.state is ConvState.INVITED and a != s.participants[0]:
            s.state = ConvState.PARTICIPATING
            self._chat_meter["joined"] += 1
        if a not in s.calls:  # グループの後から入った成員(一覧は組み立ての時の表=本段では起きない)
            s.participants.append(a)
            s.calls[a] = 0
            s.max_turns_of[a] = CHAT_MAX_BLOCKS
        s.calls[a] = s.calls.get(a, 0) + 1
        s.blocks += 1
        s.last_utterance_tick = int(step)
        s.speaker_index = (s.participants.index(a) + 1) % len(s.participants)
        self.n_blocks += 1
        self._chat_meter["messages"] += 1
        if s.blocks >= CHAT_MAX_BLOCKS:
            self._close(s, int(step), _CAP_REASON)
            self._chat_meter["cap_hits"] += 1
        return s

    def step(self, step: int) -> list[Session]:  # type: ignore[override]
        """1 刻み進める(会話の器の ``step``=締め → 終わり・参加の沈黙で締め)。返事の無い招待の沈黙だけここで締める。
        終わったものを掃除して返す。"""
        t = int(step)
        for s in list(self.sessions.values()):  # 逐次ループ宣言: 生きているチャットの数ぶん
            if s.state is ConvState.INVITED and t - int(s.last_utterance_tick) > self.silence_ticks:
                self._close(s, t, "soft_silence")
        done = super().step(t)
        self.purge_terminal()
        for s in done:
            for k in [k for k, v in self._of_key.items() if v == s.session_id]:
                del self._of_key[k]
        return done

    # ------------------------------------------------------------------ 読む口
    def session(self, key: str) -> Session | None:
        sid = self._of_key.get(key)
        return None if sid is None else self.sessions.get(sid)

    def partners_of(self, agent: int) -> tuple[int, ...]:
        """体が参加している続いているチャット(参加の段)の相手(1 対 1 は相手・グループは -1−グループの鍵の番号は持たない=成員)。"""
        a = int(agent)
        out: list[int] = []
        for s in self.sessions.values():  # 逐次: 生きているチャットの数ぶん
            if s.state is ConvState.PARTICIPATING and a in s.calls:
                out.extend(p for p in s.participants if p != a and p not in out)
        return tuple(out)

    def chat_counts(self) -> dict[str, Any]:
        by = {st.name: 0 for st in ConvState}
        for s in self.sessions.values():
            by[s.state.name] += 1
        closed = {f"closed:{r}": int(self.closed_by_reason.get(r, 0)) for r in CLOSE_REASONS}
        return {"live": by, **{k: int(v) for k, v in self._chat_meter.items()}, **closed}
