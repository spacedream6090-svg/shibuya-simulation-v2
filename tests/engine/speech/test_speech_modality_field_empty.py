"""第 1 期 1-8b 発話の口: 将来の音声・表情(VRM)の欄 ``modality`` は空(受入の試験 ``test_speech_modality_field_empty``)。

決定 10-13b §1 1-5(将来の音声と表情にも同じ口)。欄は用意し、値は空(None)で始める=値を作る段で足す。口が書いた発話の
写しでも空・ランの中の発話でも空(未読の列は本文と話し手だけを持つ)。
"""

from __future__ import annotations

import dataclasses

import pytest

from shibuya.engine.events.log import EventLog
from shibuya.engine.speech import port as P

from tests.engine.speech._s8b import run_small


def test_the_field_exists_and_starts_empty():
    names = [f.name for f in dataclasses.fields(P.Utterance)]
    assert names[-1] == "modality"
    u = P.Utterance(speaker=1, t_ns=0, text="やあ", addressees=(2,))
    assert u.modality is None
    assert dataclasses.replace(u, event_id=(0, 0)).modality is None


@pytest.mark.parametrize("value", ["voice", {"vrm": "smile"}, 0, ()])
def test_a_value_is_refused_until_a_stage_adds_it(value):
    with pytest.raises(ValueError, match="modality"):
        P.Utterance(speaker=1, t_ns=0, text="やあ", addressees=(2,), modality=value)


def test_said_utterances_keep_the_field_empty():
    seen: list[P.Utterance] = []
    port = P.SpeechPort(events=EventLog(), wom_fn=lambda u, ctx: seen.append(u) or 0)
    port.say(P.SpeechContext(step=3, call_id="3:1:0"), P.Utterance(speaker=1, t_ns=180 * 10**9, text="やあ",
                                                                   addressees=(2,)))
    assert len(seen) == 1 and seen[0].modality is None and seen[0].event_id is not None


def test_in_a_run_every_said_utterance_has_an_empty_modality():
    seen: list[P.Utterance] = []
    real = P.SpeechPort.say

    def spy(self, ctx, utterance):  # noqa: ANN001
        seen.append(utterance)
        return real(self, ctx, utterance)

    P.SpeechPort.say = spy  # type: ignore[method-assign]
    try:
        res = run_small("on")
    finally:
        P.SpeechPort.say = real  # type: ignore[method-assign]
    assert seen and all(u.modality is None for u in seen)
    assert res.run_manifest_fields()["speech_port"]["said"] == len(seen)
