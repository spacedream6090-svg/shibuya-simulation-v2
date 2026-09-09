"""場面抽出(指標B の事前登録)の純関数 — **モックテープ / モック記録**で検査。

正典: 知覚契約書 §8「制約種ごとにn≥50(5種=250場面)+「答えが決まる場面」100場面」。
抽出の規則そのものは自前(expedient)なので、**分類表が正典と 1 対 1 であること**を
機械で固定する(``agents.state.RESULT_TEXT`` と ``perception.templates`` の文面)。
"""

from __future__ import annotations

import json

import pytest

from shibuya.agents.state import RESULT_TEXT, ResultCode
from shibuya.engine.tape import TapeRow, TapeWriter
from shibuya.perception import templates as T


# ---------------------------------------------------------------- 表が正典と一致する
def test_failure_word_table_is_one_to_one_with_result_text(c6lib):
    canonical = {
        code.name.lower(): RESULT_TEXT[int(code)]
        for code in ResultCode
        if int(code) != int(ResultCode.OK)
    }
    assert c6lib.FAILURE_WORD_BY_KIND == canonical
    assert len(c6lib.FAILURE_KIND_BY_WORD) == len(canonical)


def test_preregistered_kinds_are_the_declared_five(c6lib):
    assert c6lib.CONSTRAINT_KINDS == (
        "closed", "money_short", "train_full", "unreachable", "refused",
    )
    assert all(k in c6lib.FAILURE_WORD_BY_KIND for k in c6lib.CONSTRAINT_KINDS)
    assert c6lib.METRIC_B_PER_KIND == 50 and c6lib.METRIC_B_DETERMINED == 100


def test_plan_boundary_reason_snippets_come_from_the_template(c6lib):
    for snippet in c6lib.PLAN_BOUNDARY_REASONS:
        assert any(snippet in line for line in T.WAKE_REASON_TEXT), snippet


# ---------------------------------------------------------------- 分類(純関数)
def _prompt(*, fail: str | None = None, intero: str | None = None, wake: str = "") -> str:
    lines = ["[B1 種別] あなたは来街者です。", "[B3 時刻] 現在時刻は12時40分です。"]
    lines.append(
        T.TEMPLATES["B5.intero"].format(items=intero)
        if intero
        else T.TEMPLATES["B5.intero_empty"]
    )
    lines.append(
        T.TEMPLATES["B6.wake"].format(reason=wake or T.WAKE_REASON_TEXT[3])
    )
    if fail:
        lines.append(
            T.TEMPLATES["B6.result_fail"].format(
                action="購入", why=fail, observed="", options="移動・待機・休憩"
            )
        )
    else:
        lines.append(T.TEMPLATES["B6.result_none"])
    return "\n".join(lines)


@pytest.mark.parametrize(
    "kind,word",
    [("closed", "営業時間外"), ("money_short", "所持金不足"), ("train_full", "満員"),
     ("unreachable", "到達不能"), ("refused", "断られた"), ("bad_target", "対象を特定できない")],
)
def test_classify_scene_reads_the_failure_reason(c6lib, kind, word):
    c, determined, drivers = c6lib.classify_scene(_prompt(fail=word))
    assert c == kind
    assert determined and "last_failure" in drivers


def test_classify_scene_finds_the_interoception_driver(c6lib):
    c, determined, drivers = c6lib.classify_scene(_prompt(intero="空腹は8で閾値を超えています。"))
    assert c == "" and determined and drivers == ("intero",)


def test_classify_scene_finds_the_plan_boundary_driver(c6lib):
    c, determined, drivers = c6lib.classify_scene(_prompt(wake=T.WAKE_REASON_TEXT[2]))
    assert determined and "plan_boundary" in drivers


def test_classify_scene_returns_plain_for_a_scene_without_drivers(c6lib):
    c, determined, drivers = c6lib.classify_scene(_prompt())
    assert c == "" and not determined and drivers == ()


def test_unknown_failure_word_is_not_forced_into_a_kind(c6lib):
    c, determined, drivers = c6lib.classify_scene(_prompt(fail="宇宙線"))
    assert c == "" and determined and drivers == ("last_failure",)


# ---------------------------------------------------------------- モックテープからの抽出
def _write_mock_tape(path, rows):
    with TapeWriter(path) as w:
        for i, (agent, tick, wake_class, prompt, response) in enumerate(rows):
            bid = w.intern_block(prompt)
            w.append(
                TapeRow(
                    call_id=f"c{i}",
                    agent_id=agent,
                    tick=tick,
                    wake_class=wake_class,
                    prompt_hash=f"ph{i}",
                    block_ids=(bid,),
                    params_hash="pa",
                    response=response,
                )
            )
    return path


def test_scenes_from_a_mock_tape(c6lib, tmp_path):
    rows = [
        (1, 0, 3, _prompt(fail="営業時間外"), "理由: 閉まっている\n行動: 移動 対象: なし ひと言: なし"),
        (2, 1, 3, _prompt(intero="空腹は9で閾値を超えています。"), "理由: 空腹\n行動: 購入 対象: 弁当 ひと言: なし"),
        (3, 2, 3, _prompt(), "理由: なんとなく\n行動: 待機 対象: なし ひと言: なし"),
    ]
    scenes = c6lib.scenes_from_tape(_write_mock_tape(tmp_path / "tape", rows))
    assert [s.constraint for s in scenes] == ["closed", "", ""]
    assert [s.determined for s in scenes] == [True, True, False]
    assert all(not s.partial for s in scenes)  # モックは B6 を含む
    assert scenes[0].response.startswith("理由: ")


def test_real_tape_blocks_lack_the_individual_sections(c6lib, tmp_path):
    """実ランのテープは共有ブロックだけ = ``partial=True``(再呼に使えない印)。"""
    shared_only = "[B1 種別] あなたは来街者です。\n[B4 密度] 歩行者密度は段階Aです。人の流れは滞留気味です。"
    scenes = c6lib.scenes_from_tape(
        _write_mock_tape(tmp_path / "t2", [(1, 0, 3, shared_only, "行動: 待機")])
    )
    assert scenes[0].partial and scenes[0].constraint == "" and not scenes[0].determined


# ---------------------------------------------------------------- 在庫と抽出
def _scene(c6lib, i, kind, determined=True):
    return c6lib.Scene(
        agent_id=i, tick=i, wake_class=3, prompt="", constraint=kind,
        determined=determined, prompt_hash=f"h{i}",
    )


def test_inventory_reports_shortfall_against_the_preregistration(c6lib):
    scenes = [_scene(c6lib, i, "closed") for i in range(60)]
    scenes += [_scene(c6lib, 1000 + i, "", True) for i in range(120)]
    inv = c6lib.scene_inventory(scenes)
    assert inv["per_kind"]["closed"] == 60
    assert inv["shortfall_per_kind"] == {"money_short": 50, "train_full": 50, "refused": 50, "unreachable": 50}
    assert inv["n_determined"] == 180 and inv["determined_shortfall"] == 0
    assert not inv["ok"]
    assert inv["per_failure_kind_all"] == {"closed": 60}


def test_inventory_is_ok_when_all_five_kinds_are_stocked(c6lib):
    scenes = [
        _scene(c6lib, i * 10 + j, k)
        for j, k in enumerate(c6lib.CONSTRAINT_KINDS)
        for i in range(50)
    ]
    scenes += [_scene(c6lib, 90_000 + i, "", True) for i in range(100)]
    inv = c6lib.scene_inventory(scenes)
    assert inv["ok"], inv


def test_selection_is_deterministic_and_disjoint(c6lib):
    scenes = [
        _scene(c6lib, i * 10 + j, k)
        for j, k in enumerate(c6lib.CONSTRAINT_KINDS)
        for i in range(80)
    ]
    scenes += [_scene(c6lib, 90_000 + i, "", True) for i in range(300)]
    a = c6lib.select_metric_b_scenes(scenes)
    b = c6lib.select_metric_b_scenes(list(reversed(scenes)))
    assert {k: [s.key for s in v] for k, v in a.items()} == {
        k: [s.key for s in v] for k, v in b.items()
    }
    assert all(len(a[k]) == 50 for k in c6lib.CONSTRAINT_KINDS)
    assert len(a["determined"]) == 100
    keys = [s.key for v in a.values() for s in v]
    assert len(keys) == len(set(keys)), "同じ場面を 2 枠で採ってはいけない"


def test_selection_can_be_restricted_to_other_kinds(c6lib):
    scenes = [_scene(c6lib, i, "bad_target") for i in range(70)]
    picked = c6lib.select_metric_b_scenes(scenes, kinds=("bad_target",))
    assert len(picked["bad_target"]) == 50
    inv = c6lib.scene_inventory(scenes, kinds=("bad_target",))
    assert inv["shortfall_per_kind"] == {}


# ---------------------------------------------------------------- 記録クライアント
class _StubLLM:
    def complete(self, request):
        from shibuya.llm import LLMResponse

        return LLMResponse(text=f"理由: r{request.agent_id}\n行動: 待機 対象: なし ひと言: なし")


def test_recording_llm_captures_full_prompts(c6lib, tmp_path):
    from shibuya.llm import LLMRequest

    rec = c6lib.RecordingLLM(_StubLLM())
    for i in range(3):
        rec.complete(LLMRequest(agent_id=i, tick=i * 2, wake_class=3, prompt=_prompt(fail="満員")))
    assert rec.calls == [(0, 0), (1, 2), (2, 4)]
    path = rec.dump(tmp_path / "scenes.jsonl")
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 3 and "[B6 結果]" in rows[0]["prompt"]
    scenes = c6lib.scenes_from_jsonl(path)
    assert [s.constraint for s in scenes] == ["train_full"] * 3
