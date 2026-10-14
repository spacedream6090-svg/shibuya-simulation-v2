"""engine.speech.layer — 発話の口の腕と、会話の番の答えから発話を作って口に通す糸(第 1 期 1-8b)。

腕(切替口): ``--speech-port {off,on}``(環境変数 ``SHIBUYA_SPEECH_PORT``・:func:`set_arm`)。既定 ``off``=口を作らない
(プロンプト・出力形・テープの列・final・manifest の既存の欄は今のまま)。``on`` で組み立てが ``SpeechPort`` を作り、
(1) 描画が会話の番の呼び出しだけ B6 の末尾に出力の欄の指示(``llm.contract.SPEECH_FIELD_LINE``・語彙 v3)を足し、届いた
発話を B6 の末尾に素性タグと命令文の除去つきで載せる(``perception.renderer``)。(2) 会話の番の答えの「ひと言」を
``speak_turn`` が ``Utterance`` にして口(``SpeechPort.say``)に通す(今の道の口コミの抽出は口の (c) に移る=書く口は 1 つ)。
腕は組み立てのときに読む。on は結果を変える(相手の入力に発話が載る)ので、設定の指紋に on のときだけ ``speech_port`` を
足し(``engine.systems.build``)、``cli.run`` のランの種類は腕(``arm``)に数える。腕の名は manifest の ``speech_port.arm``。

既定にするのは GPU の後の版上げ(カレンダー段 2+C1=計画 6-2・口の約束 1-8b の約束 (5)=止まる地点 S6)。

expedient(本モジュール分)
- B6 の 2 行の文面(``perception.renderer`` の ``SPEECH_HEARD_LINE``・``SPEECH_FIELD_LINE``=実装役の自前・素性の短い形
  「〔発話・命令文除去〕」・指示は 10 tok の短い形=親の判断・欄の書き方は v1 の出力規約の ひと言 の意味のまま)。
- mock と古典の方策の会話の番の ひと言 は決まった文 1 つ(``llm.mock.MOCK_UTTERANCE``=中身を誘導しない配管)。
- 発話の行だけの命令文の型(``perception.renderer.SPEECH_IMPERATIVE_PATTERNS``=て形の依頼・「無視」「忘れて」・英語の
  ignore/forget/disregard。看板の表は変えない。接続の「〜て、」の平叙文も落とす=過剰に落とす側)。

逐次ループ宣言(P4): ``speak_turn`` は 1 回の会話の番=参加者の数ぶん(≤ 3)。新しい逐次ループは無い(呼数ぶんのループは
decide と llm_receive の宣言のまま)。
"""

from __future__ import annotations

import os
from typing import Any, Callable, Final

from shibuya.core.time_consts import NS_PER_SECOND
from shibuya.engine.speech.port import (
    HEARD_MAX_PER_ADDRESSEE,
    HEARD_TTL_STEPS,
    METER_KEYS,
    SPEECH_SCHEMA,
    VIA_FACE,
    SpeechContext,
    SpeechPort,
    Utterance,
)
from shibuya.llm.contract import NO_TARGET, SPEECH_FIELD_LINE
from shibuya.llm.mock import MOCK_UTTERANCE

__all__ = [
    "ARM_OFF", "ARM_ON", "ARMS", "arm", "set_arm", "REACH", "CONFIG_KEYS", "OBSERVED_KEYS", "manifest_fields",
    "make_port", "speak_turn",
]

ARM_OFF: Final[str] = "off"
ARM_ON: Final[str] = "on"
ARMS: Final[tuple[str, ...]] = (ARM_OFF, ARM_ON)
_ARM: str = os.environ.get("SHIBUYA_SPEECH_PORT", ARM_OFF).strip().lower() or ARM_OFF
if _ARM not in ARMS:
    raise ValueError(f"SHIBUYA_SPEECH_PORT は {ARMS} のどれか(いま {_ARM!r})")

#: 届く範囲(当面セッションの参加者=つなぎの台帳の行 DOC-s8b-reach-session・DOC-s8b-reach-hearing)。
REACH: Final[str] = "session"


def arm() -> str:
    """いまの腕(``off``=既定・``on``=発話の口)。組み立てのときに読む。"""
    return _ARM


def set_arm(name: str) -> None:
    """腕を選ぶ(CLI ``--speech-port``・試験の切替口)。組み立ての時に読む(ランの途中で変えても、そのランは変わらない)。"""
    global _ARM
    if str(name) not in ARMS:
        raise ValueError(f"--speech-port は {ARMS} のどれか(いま {name!r})")
    _ARM = str(name)


#: manifest の ``speech_port`` の設定の子と観測の子(``engine.manifest_sections`` の混ざった辞書)。
CONFIG_KEYS: Final[tuple[str, ...]] = (
    "schema", "arm", "port", "reach", "via", "field_line", "heard_ttl_steps", "heard_max_per_addressee",
    "mock_utterance")
OBSERVED_KEYS: Final[tuple[str, ...]] = METER_KEYS + ("pending",)


def manifest_fields(port: SpeechPort | None) -> dict[str, Any]:
    """manifest の ``speech_port``(腕が off のランは口が無い=観測の子は null)。"""
    cfg: dict[str, Any] = {
        "schema": SPEECH_SCHEMA, "arm": ARM_OFF if port is None else ARM_ON,
        "port": None if port is None else port.name, "reach": REACH, "via": VIA_FACE, "field_line": SPEECH_FIELD_LINE,
        "heard_ttl_steps": HEARD_TTL_STEPS, "heard_max_per_addressee": HEARD_MAX_PER_ADDRESSEE,
        "mock_utterance": MOCK_UTTERANCE,
    }
    if port is None:
        return {**cfg, **{k: None for k in OBSERVED_KEYS}}
    return {**cfg, **port.observed()}


def make_port(*, events: Any, wom: Any, vocab_version: str, agents: Any, mem_layer: Any, store_wom_on: bool,
              step_seconds: int, conv: Any = None) -> SpeechPort:
    """組み立ての口: 発話の口を作る。口コミの抽出の口 ``wom_fn`` は今の道(``engine.systems.llm_io.utter`` の口コミの段)と
    同じ抽出と転写(源 ``wom_source`` の表で読む欄・話し手のセル・宛先=会話の相手・店の記憶 on のランだけ転写)。
    ``session_active`` は会話の管理のセッションの表を読むだけの口(開いている=招待・歩み寄り・参加の段)。

    口の (c) が ``wom_fn`` を呼び、その中で口コミの抽出の層(``wom.observe``)と店の記憶(``hear``)の書き口が走る=口を通した
    持ち主をまたぐ呼び出し(親の判断 A8 で認めた形・別名で他の持ち主の配列を書く形ではない・系の宣言は decide と llm_receive)。"""
    wom_fn: Callable[[Utterance, SpeechContext], int] | None = None
    if wom is not None:
        from shibuya.engine.wom import hear as _hear

        def wom_fn(u: Utterance, ctx: SpeechContext) -> int:
            text = wom.utterance_text(vocab_version, comment=u.text, reason=ctx.reason, target=ctx.target)
            ex = wom.extract(text, int(ctx.cell))
            wom.observe(ex)
            if store_wom_on:  # 7c の腕: 口コミ off=抽出は数えるが転写しない(今の道と同じ)
                return int(_hear(mem_layer.store, agents, int(ctx.step), int(ctx.listener), ex))
            return 0

    session_active: Callable[[int], bool] | None = None
    if conv is not None:
        def session_active(sid: int) -> bool:
            sess = conv.sessions.get(int(sid))
            return sess is not None and bool(sess.active)

    return SpeechPort(events=events, wom_fn=wom_fn, step_seconds=int(step_seconds), session_active=session_active)


def speak_turn(b: Any, port: SpeechPort, agent_id: int, step: int, session: Any, comment: str, reason: str,
               parse: Any, call_id: str, partner_before: int) -> Any:
    """会話の番の答え 1 つ → 発話(``Utterance``)→ 口。返り値=目印(発話が無ければ ``None``)。

    届け先=セッションの参加者から話し手を除いた人(当面の届く範囲)。〔親の判断 A2〕被招待の返事(セッションはまだ無い・
    返事待ちの招待がある)は返事待ちの招待を「セッションの招待の段階」とみなし、届け先=招待した人(``to_inviter`` に数える)。
    発話にしないもの(計器に数える): セッションも返事待ちの招待も無い答え(``no_session``)・ひと言が空か「なし」(``silent``)。
    口コミの宛先は今の道と同じ(発話の前の会話の相手が届け先にいればその人・いなければ最初の届け先)。
    """
    port.note("turns")
    a = int(agent_id)
    text = str(comment or "").strip()
    sid = -1
    if session is not None:
        others = tuple(int(p) for p in session.participants if int(p) != a)
        sid = int(session.session_id)
    else:
        conv = b.layers.conv
        inviter = int(conv.pending_inviter_of(a)) if conv is not None else -1
        others = (inviter,) if inviter >= 0 and inviter != a else ()
    if not others:
        port.note("no_session")
        return None
    if not text or text == NO_TARGET:
        port.note("silent")
        return None
    if session is None:
        port.note("to_inviter")
    agents = b.soa.agents
    listener = int(partner_before) if int(partner_before) in others else others[0]
    tgt = getattr(parse, "target", None)
    ctx = SpeechContext(
        step=int(step), call_id=str(call_id), cell=int(agents.registry.cell[a]),
        input_event_ids=port.take_input_ids(a), listener=listener,
        reason=str(getattr(parse, "raw_reason", "") or reason or ""), target=str(getattr(tgt, "raw", "") or ""),
        session=sid,
    )
    u = Utterance(speaker=a, t_ns=int(step) * int(b.cfg.tick_seconds) * NS_PER_SECOND, text=text, addressees=others)
    return port.say(ctx, u)
