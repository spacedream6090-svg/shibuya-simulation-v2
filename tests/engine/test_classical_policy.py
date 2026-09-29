"""5 段目 5b: System 1.5=古典的選択モデル(D-119 L1〜L8・第292)のテスト。

正典: ``docs/design/v2-energy-classical-implementation-agenda.md`` §2・草案
``docs/design/v2-hunger-choice-attention-draft.md`` §2-2・§2-6・§1-3 K6 (i)。
錨は追跡ファイル ``docs/bench/anchors/ssb2021_activity_prior_v0.json`` だけを読む(data/ は読まない)。
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import numpy as np
import pytest

from shibuya.agents.state import Activity, AgentKind, AgentState, WakeCondition
from shibuya.engine import chooser as CH
from shibuya.engine import classical as CL
from shibuya.llm import LLMRequest
from shibuya.llm import parse_two_line
from shibuya.llm.contract import format_two_line_v3
from shibuya.world.state import World

DOC, MD5 = CL.load_activity_prior()
SRC = Path("src/shibuya")
CJK = re.compile(r"[぀-ヿ㐀-鿿]")


# ================================================================= 錨
def test_prior_anchor_is_numbers_and_codes_only():
    body = dict(DOC)
    attribution = body.pop("attribution")
    assert attribution == ["「令和3年社会生活基本調査結果」(総務省統計局)を加工して作成"]
    assert not CJK.search(json.dumps(body, ensure_ascii=False)), "錨の本体に和文がある"
    assert tuple(DOC["activity_codes"]) == CL.SSB_ACTIVITY_CODES
    assert "03" not in DOC["activity_codes"] and DOC["excluded_activity_codes"] == ["03"]
    assert set(DOC["tables"]) == {"weekday", "saturday", "sunday"}
    assert set(DOC["tables"]["weekday"]) == {"00", "03"}
    assert set(DOC["tables"]["saturday"]) == {"03"} and set(DOC["tables"]["sunday"]) == {"03"}
    for day, src in DOC["sources"].items():
        assert re.fullmatch(r"[0-9a-f]{32}", src["md5"]), day
    st = DOC["tables"]["weekday"]["03"]["1-1"]["04"]  # 関東・男・有業・30〜34 歳
    assert st["sample"] == 334 and st["pop_k"] == 1113
    rates = np.asarray(st["rates"])
    assert rates.shape == (19, 96) and rates.min() >= 0
    # 00:00 の睡眠 69.30%(原表 xlsx 行 16404 の値を % × 100 の整数で)・年齢総数の行は 79.11%
    assert rates[0, 0] == 6930
    assert DOC["tables"]["weekday"]["03"]["1-1"]["00"]["rates"][0][0] == 7911


def test_prior_row_is_a_distribution_with_declared_fallbacks():
    pr = CL.ActivityPrior(DOC, "weekday", "kanto")
    p = pr.row(0, True, 32, 48)  # 男・有業・32 歳・12:00
    assert p.shape == (19,) and abs(p.sum() - 1.0) < 1e-12
    assert CL.SSB_ACTIVITY_CODES[int(np.argmax(p))] == "05"  # 仕事
    # 15 歳未満は 15〜19 歳の行・性別不明は男女の平均
    np.testing.assert_allclose(pr.row(0, False, 9, 40), pr.row(0, False, 16, 40))
    both = pr.rates[0, 1, pr.age_index(np.array([40]))[0], :, 40] + pr.rates[1, 1, pr.age_index(np.array([40]))[0], :, 40]
    np.testing.assert_allclose(pr.row(-1, False, 40, 40), both / both.sum())
    with pytest.raises(ValueError):
        CL.ActivityPrior(DOC, "saturday", "national")  # 全国の土日は錨に無い(宣言)


def test_zero_sample_stratum_falls_back_to_the_age_total_row():
    pr = CL.ActivityPrior(DOC, "weekday", "kanto")
    ai = int(pr.age_index(np.array([30]))[0])
    pr.sample[0, 0, ai] = 0
    np.testing.assert_allclose(pr.row(0, True, 30, 50),
                               pr.rates[0, 0, 0, :, 50] / pr.rates[0, 0, 0, :, 50].sum())


def test_day_kind_follows_the_day_index():
    assert [CL.day_kind_of(d) for d in range(8)] == (
        ["weekday"] * 5 + ["saturday", "sunday", "weekday"]
    )


def test_ipf_constants_return_the_population_marginal_to_the_prior():
    g = np.random.default_rng(3)
    p0 = g.dirichlet(np.ones(19), size=50)
    m = g.uniform(0.2, 3.0, size=(50, 19))
    c = CL.ipf_constants(p0, m)
    np.testing.assert_allclose((p0 * m * c).sum(axis=0), p0.sum(axis=0), rtol=1e-12)
    np.testing.assert_allclose(CL.ipf_constants(p0, np.ones_like(m)), np.ones(19))


# ================================================================= 店選び(L3/L8)
def _ctx(hunger, money=5000, price=(900, 900, 900), visits=(), food=True, vis=(9, 5, 1)):
    return CH.ChoiceContext(0, 0, 0, 0, 24, "none", "", hunger,
                            visibility=np.asarray(vis), distance_m=np.zeros(len(vis)),
                            price=np.asarray(price), money=money,
                            visits=np.asarray(visits, dtype=np.int64), food=food)


def test_aspiration_moves_with_the_hunger_word():
    ch = CH.ClassicalChooser(p_h=0.5, tau=1.0)
    cands = np.array([10, 11, 12])
    # 空腹(8)=予算内だけ・とても空腹(10)=条件なし(最初に見えた店を含む)
    p_hungry = ch.probs(cands, _ctx(8, money=1000, price=(1500, 900, 900)))
    assert p_hungry[0] == 0.0 and abs(p_hungry.sum() - 1.0) < 1e-12
    p_very = ch.probs(cands, _ctx(10, money=1000, price=(1500, 900, 900)))
    assert p_very[0] > p_very[1] > p_very[2] > 0.0
    # 予算内の店が無ければ願望水準を下げる(宣言)
    p_none = ch.probs(cands, _ctx(8, money=100))
    assert abs(p_none.sum() - 1.0) < 1e-12 and ch.stats["aspiration_lowered"] == 1
    # 食事以外は予算だけ(空腹の語は見ない)
    p_buy = ch.probs(cands, _ctx(10, money=1000, price=(1500, 900, 900), food=False))
    assert p_buy[0] == 0.0


def test_rank_jitter_tau_and_habit():
    cands = np.array([10, 11, 12])
    sharp = CH.ClassicalChooser(p_h=0.5, tau=0.05).probs(cands, _ctx(8))
    assert sharp[0] > 0.999
    flat = CH.ClassicalChooser(p_h=0.5, tau=1e6).probs(cands, _ctx(8))
    np.testing.assert_allclose(flat, [1 / 3] * 3, atol=1e-5)
    base = CH.ClassicalChooser(p_h=0.5, tau=1.0).probs(cands, _ctx(8))
    habit = CH.ClassicalChooser(p_h=0.5, tau=1.0).probs(cands, _ctx(8, visits=(0, 0, 3)))
    np.testing.assert_allclose(habit, 0.5 * base + np.array([0.0, 0.0, 0.5]))
    # 親しみの表が無い(visits 空)=習慣の項を飛ばす
    np.testing.assert_allclose(CH.ClassicalChooser().probs(cands, _ctx(8, visits=())), base)


def test_hunger_stage_reads_both_models():
    assert [CH.hunger_stage_of(v) for v in (1, 5, 8, 10)] == [0, 1, 2, 3]  # energy の写し
    assert [CH.hunger_stage_of(v) for v in (0, 3, 4, 6, 7, 8, 9)] == [0, 0, 1, 1, 2, 2, 3]  # v1


def test_make_chooser_knows_classical():
    assert "classical" in CH.CHOOSER_NAMES
    c = CH.make_chooser("classical", p_h=0.25, tau=2.0)
    assert isinstance(c, CH.ClassicalChooser) and (c.p_h, c.tau) == (0.25, 2.0)


# ================================================================= 方策(食事の門・対応表 v0)
def _bound(n=4, hunger=(8, 8, 8, 8), boundary=((), ())):
    w = World.synthetic(n_cells=9, seed=1)
    a = AgentState(n)
    with a.writable():
        a.cell[:] = 0
        a.hunger[:] = hunger
        a.age[:] = 30
        a.sex[:] = 0
        a.kind[:] = AgentKind.VISITOR
        a.activity[:] = int(Activity.IDLE)
    pol = CL.ClassicalPolicy(seed=1, prior=CL.ActivityPrior(DOC, "weekday", "kanto"), prior_md5=MD5)
    pol.bind(agents=a, world=w, home_cell=np.full(n, 1), work_cell=np.full(n, 2),
             school_cell=np.full(n, -1), has_work=np.zeros(n, dtype=bool),
             boundary_agent=np.asarray(boundary[0], dtype=np.int64),
             boundary_tick=np.asarray(boundary[1], dtype=np.int64))
    return pol, a, w


def test_meal_gate_combines_word_calendar_and_surroundings():
    pol, a, w = _bound(hunger=(1, 5, 8, 10))
    eatery_here = bool(pol._cell_has_eatery[0])
    surround = 1.0 if eatery_here else CL.MEAL_NO_EATERY_FACTOR
    got = [pol.meal_probability(i, 720)[0] for i in range(4)]
    want = [min(1.0, x * surround) for x in CL.MEAL_WORD_P]
    np.testing.assert_allclose(got, want)
    # 次の予定まで 30 分未満なら ×0.3
    pol2, _a, _w = _bound(hunger=(8, 8, 8, 8), boundary=((2,), (730,)))
    assert pol2.meal_probability(2, 720)[0] == pytest.approx(0.6 * surround * CL.MEAL_CALENDAR_FACTOR)
    assert pol2.meal_probability(2, 731)[0] == pytest.approx(0.6 * surround)  # 境界を過ぎた


def test_responses_parse_as_v3_and_are_deterministic():
    pol, a, w = _bound()
    req = LLMRequest(agent_id=1, tick=720, wake_class=1, prompt="")
    t1 = pol.render(req)
    t2 = pol.render(req)
    assert t1 == t2
    parsed = parse_two_line(t1, "v3")
    assert parsed.format_ok and parsed.action is not None


def test_activity_map_v0_location_rules():
    pol, a, w = _bound()
    # 睡眠: 自宅に居れば 就寝・自宅が範囲内で別のセルなら 移動 自宅・自宅が範囲外ならその場で休む
    assert pol._respond("01", 0, 1, "", -1)[1:3] == ("就寝", "なし")
    assert pol._respond("01", 0, 0, "", -1)[1:] == ("移動", "自宅", "帰宅", "到着")
    pol.home_cell[0] = -1
    assert pol._respond("01", 0, 0, "", -1)[1:3] == ("なし", "なし")
    # 仕事: 勤め先が無い(来街者)はその場 / 勤め先があって居なければ 移動 職場
    assert pol._respond("05", 1, 0, "", -1)[1] == "なし"
    pol.has_work[1] = True
    assert pol._respond("05", 1, 0, "", -1)[1:3] == ("移動", "職場")
    # 交際(第2波 §2A 項 3-1): 既定 acquaintance=近接行の知人だけ(関係の腕が無い=知人が居ない → なし 待つ)
    prompt = "[B5 近接] 近くの人物: P-3(来街者)、P-0(来街者)。"
    assert pol.social == "acquaintance"
    assert pol._respond("18", 3, 0, prompt, -1)[1:4] == ("なし", "なし", "待つ")
    # 旧 near_first: B5 の近接行の最初の人(自分を除く)・見えなければ なし
    pol.social = "near_first"
    assert pol._respond("18", 3, 0, prompt, -1)[1:3] == ("会話", "P-0")
    assert pol._respond("18", 3, 0, "", -1)[1] == "なし"
    # 買い物は 物販店(候補の絞り込みと選び手へ)
    assert pol._respond("10", 0, 0, "", -1)[1:3] == ("購入", "物販店")
    for code in CL.SSB_ACTIVITY_CODES:
        text = format_two_line_v3(
            *pol._respond(code, 2, 0, prompt, -1)
        )
        assert parse_two_line(text, "v3").format_ok, code


def test_conversation_turn_replies_to_the_inviter():
    pol, a, w = _bound()
    pol.set_call(1, int(WakeCondition.CONVERSATION_TURN), inviter=3)
    text = pol.render(LLMRequest(agent_id=1, tick=720, wake_class=1, prompt=""))
    assert "行動: 会話 対象: P-3" in text


# ================================================================= ラン
def test_run_day_classical_arm_and_layers():
    from shibuya.engine.run import run_day

    kw = dict(n_agents=60, seed=2, ticks=180, vocab_version="v3")
    mock = run_day(**kw)
    cl = run_day(policy="classical", chooser="classical", **kw)
    assert mock.policy == "mock" and mock.classical == {}
    m = cl.run_manifest_fields()
    assert m["policy"] == "classical" and m["classical"]["prior"]["anchors_md5"] == MD5
    layers = m["decision_layers"]
    assert layers["totals"]["system2"] == 0
    assert layers["totals"]["system1_5"] == int(cl.llm_calls)
    assert mock.decision_layers["totals"]["system1_5"] == 0
    assert mock.decision_layers["totals"]["system2"] == int(mock.llm_calls)
    assert cl.parse_error_rate == 0.0
    assert m["chooser_stats"]["name"] == "classical"
    with pytest.raises(ValueError):
        run_day(policy="classical", n_agents=10, ticks=5)  # 語彙 v1
    with pytest.raises(ValueError):
        run_day(policy="classical", llm=object(), **{**kw, "ticks": 5})
    with pytest.raises(ValueError):
        run_day(policy="gpt", **{**kw, "ticks": 5})


def test_default_run_does_not_touch_the_rich_context():
    """既定の選び手 nearest では価格・訪問回数を組まない(既定 checkpoint 不変の構造上の担保)。"""
    from shibuya.engine.poi_target import TargetResolver

    w = World.synthetic(n_cells=9, seed=1)
    res = TargetResolver(world=w, chooser=CH.make_chooser("nearest"), seed=1)
    assert res._rich is False and res._rich_fields(None, 0, np.zeros(0, dtype=np.int64), True) == {}


def test_cli_exposes_the_5b_flags():
    from shibuya import cli

    ap = cli.build_parser() if hasattr(cli, "build_parser") else None
    src = (SRC / "cli.py").read_text(encoding="utf-8")
    for flag in ("--policy", "--activity-region", "--classical-habit-p", "--classical-tau", "--classical-social"):
        assert flag in src
    del ap


# ================================================================= P4
_PER_CALL = {
    "engine/classical.py": ("render", "complete", "meal_probability", "activity_probs",
                            "_respond", "_next_plan_minutes", "_eating_by_cell", "ipf_constants"),
    "engine/chooser.py": ("probs",),
}


def test_per_call_paths_have_no_python_loops_over_agents():
    offenders = []
    for rel, names in _PER_CALL.items():
        tree = ast.parse((SRC / rel).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in names:
                for sub in ast.walk(node):
                    if isinstance(sub, (ast.For, ast.While)):
                        offenders.append(f"{rel}:{node.name}:{sub.lineno}")
    assert not offenders, offenders
    assert "逐次ループ宣言" in (SRC / "engine/classical.py").read_text(encoding="utf-8")
