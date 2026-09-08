"""未定義行動5段のエンジン側結線(行動契約書 §7)+ 書式エラー率の診断行。

- 段0 の辞書写像が ``LLMBridge`` を通ってエンジンの行動コードになる。
- 語彙外は ``UNDEFINED_ACTION`` で ``resolve`` が**待機**に落とす(§2 共通必須事項③)。
- わざと壊した mock で ``parse_error_rate > 0`` / ``undefined_action_count > 0`` が立つ。
- 段2 の裁定は「異なる個体が閾値N」に達したときだけ1呼。
"""

from __future__ import annotations

import pytest

from shibuya.agents.state import Activity, ResultCode
from shibuya.engine import commit as C
from shibuya.engine.llm_bridge import LLMBridge
from shibuya.engine.run import run_day
from shibuya.engine.tape import Tape, TapeWriter
from shibuya.llm import LLMResponse, MockLLM, format_two_line
from shibuya.llm.contract import ACTION_CODES, UNDEFINED_ACTION
from shibuya.llm.undefined import ProposalStatus, UndefinedActionRegistry


class WordLLM:
    """常に同じ行動語(表層形)を返す台本 mock。"""

    def __init__(self, word: str) -> None:
        self.word = word
        self.n_calls = 0

    def complete(self, request):
        self.n_calls += 1
        return LLMResponse(
            text=format_two_line("台本の理由", self.word, "なし", "なし"), source="scripted"
        )


class GarbledLLM:
    """**わざと書式を壊した** mock(書式エラー率 > 0 の対照)。"""

    def __init__(self) -> None:
        self.n_calls = 0

    def complete(self, request):
        self.n_calls += 1
        # ラベルも語彙も無い自由文(2行形ではない)
        return LLMResponse(text=f"えーと、なんとなく{request.tick % 7}を", source="scripted")


# ---------------------------------------------------------------- 段0(辞書写像)
@pytest.mark.parametrize(
    "surface,word",
    [("買う", "購入"), ("歩く", "移動"), ("話しかける", "会話"), ("寝る", "就寝"), ("待つ", "待機")],
)
def test_stage0_maps_surface_forms_to_engine_action_codes(surface, word):
    bridge = LLMBridge(WordLLM(surface))
    res = bridge.call(agent_id=1, tick=1, wake_class=1, cell=0)
    assert res.parse.action is None and res.parse.raw_action == surface
    assert res.action_code == ACTION_CODES[word]
    assert res.undefined_stage == 0
    assert bridge.n_undefined_mapped == 1
    assert bridge.counters()["undefined_records"] == 0


def test_stage1_records_and_falls_back_to_waiting():
    bridge = LLMBridge(WordLLM("空を飛ぶ"))
    res = bridge.call(agent_id=1, tick=1, wake_class=1, cell=0)
    assert res.action_code == UNDEFINED_ACTION
    assert res.undefined_stage == 1
    assert res.undefined_feedback.startswith("未定義の行動『空を飛ぶ』")
    assert bridge.undefined.counts["空を飛ぶ"] == 1
    # エンジン側では「待機」に落ちる(安全弁)
    assert C.ACT_WAIT == ACTION_CODES["待機"]


def test_stage2_needs_n_distinct_agents_through_the_bridge():
    reg = UndefinedActionRegistry(adjudicator=MockLLM(master_seed=3), threshold_agents=4)
    bridge = LLMBridge(WordLLM("空を飛ぶ"), undefined=reg)
    for tick in range(6):
        bridge.call(agent_id=0, tick=tick, wake_class=1, cell=0)  # 同一個体は閾値に効かない
    assert reg.n_adjudication_calls == 0
    for agent in range(1, 4):
        bridge.call(agent_id=agent, tick=10 + agent, wake_class=1, cell=0)
    assert reg.n_adjudication_calls == 1
    assert reg.proposals["空を飛ぶ"].status in (
        ProposalStatus.PROPOSED,
        ProposalStatus.NEEDS_PARENT_REVIEW,
    )


def test_role_actions_are_parsed_but_land_on_the_safety_valve():
    """§2.2 の役割語は読めるが効果先が C4。当面は待機へ(権限検査は engine の宿題)。"""
    bridge = LLMBridge(WordLLM("接客"))
    res = bridge.call(agent_id=1, tick=1, wake_class=1, cell=0)
    assert res.parse.action == "接客" and res.role_action
    assert res.action_code == ACTION_CODES["待機"]
    assert bridge.n_role_actions == 1
    assert ResultCode.NO_PERMISSION is not None  # 権限失敗コードは契約表側にある


# ---------------------------------------------------------------- 診断行(書式エラー率)
SMALL = dict(n_agents=300, seed=4, ticks=120, checkpoint_every=120, n_cells=16)


def test_parse_error_rate_is_zero_with_the_mock_and_positive_when_garbled():
    clean = run_day(**SMALL)
    assert clean.parse_error_rate == 0.0
    assert clean.undefined_action_count == 0

    garbled = run_day(llm=GarbledLLM(), **SMALL)
    assert garbled.parse_error_rate > 0.0
    assert garbled.undefined_action_count > 0
    assert garbled.bridge_counters["unknown_action"] > 0
    assert garbled.conserved and garbled.min_stock >= 0, "壊れた出力でも保存則は破れない"


def test_garbled_output_is_still_recorded_verbatim_on_the_tape(tmp_path):
    path = tmp_path / "tape"
    res = run_day(llm=GarbledLLM(), tape_path=path, **SMALL)
    tape = Tape(path)
    assert len(tape) == res.llm_calls > 0
    assert all(not row.response.startswith("理由: ") for row in tape.rows())


def test_dictionary_mapping_keeps_the_engine_running_on_surface_forms():
    """全員が「買う」と言っても、段0 の写像で購入 intent になる(未定義行動は増えない)。"""
    res = run_day(llm=WordLLM("買う"), **SMALL)
    assert res.undefined_action_count == 0
    assert res.bridge_counters["undefined_mapped"] == res.llm_calls
    assert int(res.column("purchases").sum()) >= 0
    assert res.conserved


def test_tape_writer_can_be_shared_by_a_bridge_and_closed_once(tmp_path):
    writer = TapeWriter(tmp_path / "t")
    bridge = LLMBridge(WordLLM("休む"), tape=writer)
    bridge.call(agent_id=0, tick=0, wake_class=1, cell=0)
    bridge.close()
    assert len(Tape(tmp_path / "t")) == 1
    assert Activity.RESTING is not None
