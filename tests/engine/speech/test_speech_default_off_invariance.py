"""第 1 期 1-8b 発話の口: 既定 off で結果不変(口の約束 1-8b の約束 (1)(5)・受入の試験 ``test_speech_default_off_invariance``)。

- byte-check 19 構成(既定 off・5,000 体・seed 1・1 日・テープつき・``10e/byte_check_10e.py``): 本体 HEAD の src と作業木の
  src で全構成・全欄が同じ(記録 ``docs/bench/analysis/wallbounce-1012/s8b/byte_check_s8b.json``)。
- 既定 off のラン(合成の世界): 口が無い(``layers.speech`` は None・manifest の観測の子は null)・プロンプトに発話の行も出力の欄の
  指示も無い・応答に ひと言 が無い・出来事ログに ``行為:発話`` が無い・状態台帳の腕の行はハッシュにも状態のファイルにも
  入らない(``arm_items`` が空=印も入らない)・設定の指紋に ``speech_port`` が無い。
- mock と古典の方策は、出力の欄の指示の無いプロンプトでは 1-8b の前と同じ文(乱数も同じ)。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from shibuya.core.time_consts import STEPS_PER_DAY
from shibuya.engine import resume as RS
from shibuya.engine import state_ledger as SL
from shibuya.engine.speech import layer as SPL
from shibuya.llm import LLMRequest
from shibuya.llm.contract import SPEECH_FIELD_LINE, append_comment, format_two_line_v3
from shibuya.llm.mock import MOCK_UTTERANCE, MockLLM
from tests.engine.speech._s8b import run_small, tape_rows

ROOT = Path(__file__).resolve().parents[3]
RECORD = ROOT / "docs" / "bench" / "analysis" / "wallbounce-1012" / "s8b" / "byte_check_s8b.json"
#: byte-check の比べる欄(``10e/byte_check_10e.py`` の ``COMPARE_KEYS``)。
COMPARE_KEYS = ("final", "calls", "blocks_rows", "blocks_sha", "calls_rows", "calls_column_names", "calls_columns_sha",
                "action_usage_total", "action_usage_sha", "calls_by_condition", "salient_events", "collapse",
                "noticed", "dispatches", "arrived", "mean_delay_min", "meals", "behavior_last", "full_last",
                "end_of_day", "start_sim_datetime", "replay_date", "calendar_weekday", "rng_scheme", "frozen_sources")


def test_byte_check_19_configurations_are_unchanged_with_the_default_arm():
    doc = json.loads(RECORD.read_text(encoding="utf-8"))
    assert doc["a"]["label"] == "head" and doc["b"]["label"] == "s8b"
    assert tuple(doc["keys"]) == COMPARE_KEYS
    rows = doc["rows"]
    assert len(rows) == 19
    for name, r in rows.items():
        assert "moved" in r, (name, r)
        assert r["moved"] == {} and tuple(r["same"]) == COMPARE_KEYS, name


def test_default_arm_is_off():
    assert SPL.ARM_OFF == "off" and SPL.arm() == "off"  # 試験の環境(SHIBUYA_SPEECH_PORT を立てない)の既定


def test_an_off_run_has_no_port_no_lines_and_no_arm_rows(tmp_path):
    res = run_small("off", tape=tmp_path / "tape")
    m = res.run_manifest_fields()["speech_port"]
    assert m["arm"] == "off" and m["port"] is None and all(m[k] is None for k in SPL.OBSERVED_KEYS)
    assert getattr(res, "speech_layer", "missing") is None
    rows = tape_rows(tmp_path / "tape")
    assert rows and all("[B6 発話]" not in r["b6"] and SPEECH_FIELD_LINE not in r["b6"] for r in rows)
    assert all("ひと言" not in r["response"] for r in rows)
    assert not any(e.what == "行為:発話" for e in res.event_log.events())
    assert SL.arm_items({"speech": None}, behavior=True) == () == SL.arm_items({"speech": None}, behavior=False)


def test_off_state_files_and_fingerprint_have_no_speech_paths(tmp_path):
    kw = dict(n_agents=60, ticks=STEPS_PER_DAY, sim_days=2, checkpoint_every=360)
    run_small("off", state_out=str(tmp_path), stop_at_tick=STEPS_PER_DAY, **kw)
    bundle = RS.read_state(next(tmp_path.glob("state-T*.npz")))
    assert list(bundle.items) == [p for _k, p in SL.full_items()]  # 前の版と同じ道筋の並び(腕の行は入らない)
    assert not any(p.startswith("speech.") for p in bundle.items)
    assert "speech_port" not in bundle.header["fingerprint"]


@pytest.mark.parametrize("form,vocab", [("v3", ("移動", "会話", "なし")), ("v1", ("移動", "待機", "会話"))])
def test_mock_text_is_unchanged_without_the_field_line(form, vocab):
    mock = MockLLM(7, vocab=vocab, form=form)
    for a in range(0, 60, 7):
        for t in (0, 13, 700):
            plain = mock.render(LLMRequest(agent_id=a, tick=t, wake_class=0, prompt="[B6 問い] いま何をしますか。"))
            asked = mock.render(LLMRequest(agent_id=a, tick=t, wake_class=0, prompt="x\n" + SPEECH_FIELD_LINE))
            if form == "v3":
                assert asked == append_comment(plain, MOCK_UTTERANCE)
                assert plain.count("\n") == 1 and "ひと言" not in plain
            else:
                assert asked == plain  # v1 の形は元から ひと言 を書く(指示を読まない)


def test_classical_text_is_unchanged_without_the_field_line():
    from shibuya.engine import classical as CL

    req = LLMRequest(agent_id=1, tick=3, wake_class=0, prompt="[B6 問い] いま何をしますか。")
    text = format_two_line_v3("r", "なし", "なし", "休む", "30分")
    assert CL._with_speech(text, req) == text
    req2 = LLMRequest(agent_id=1, tick=3, wake_class=0, prompt=SPEECH_FIELD_LINE)
    assert CL._with_speech(text, req2) == append_comment(text, MOCK_UTTERANCE)
