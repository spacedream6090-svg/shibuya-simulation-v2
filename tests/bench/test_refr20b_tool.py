# -*- coding: utf-8 -*-
"""第 2 期 2-0b の道具 ``docs/bench/analysis/wallbounce-1012/refr20b/tools/measure_refractory.py`` の試験(data 不要)。

- ``--refractory-scale`` の 11 個の並び: ``cli.parse_refractory_scale`` が 11 条件とも FACTOR=0 で受け付け、実効の
  不応期表が全部 0 分になる(腕 Ck は k 番目だけ 0・ほかは §6 の表のまま)。
- FACTOR=0 の意味の既知の答え: 1 刻み前に呼んだ体の候補は、既定の表では不応期で抑止され(会話ターンの 0 分を除く)、
  腕 B の表では 1 件も抑止されない(アービタの純関数 ``arbitrate`` で直に見る)。
- 合成の manifest 3 本(A・B・C8)から表を作る: 倍率と順位が決定的(入力の並びを入れ替えても JSON が同じ)。
- 11 本の C の順位の同点は条件の番号順。外挿の算術(既知の答え)。Markdown が書ける。
実データのランは入れない(道具を手で回す=記録 README)。
"""
from __future__ import annotations

import importlib.util
import json
import random
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "docs" / "bench" / "analysis" / "wallbounce-1012" / "refr20b" / "tools" / "measure_refractory.py"


def _load():
    name = "measure_refractory_refr20b_test"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, TOOL)
    m = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def M():
    return _load()


# ---------------------------------------------------------------- 腕の作り方
def test_eleven_flags_are_accepted_by_parse_refractory_scale(M):
    from shibuya import cli
    from shibuya.agents.state import N_WAKE_CONDITIONS, REFRACTORY_MINUTES, WakeCondition
    from shibuya.engine import resolve as R

    conds = M.conditions()
    assert conds == tuple(WakeCondition(i).name for i in range(N_WAKE_CONDITIONS))
    assert len(conds) == 11 and "ACTIVITY_EXPIRY" not in conds  # 不応期表の外は含まない

    items = M.scale_items("B")
    assert items == [f"{c}=0" for c in conds]
    flags = M.cli_flags("B")
    assert len(flags) == 22
    assert flags[0::2] == ["--refractory-scale"] * 11 and flags[1::2] == items

    parsed = cli.parse_refractory_scale(items)
    assert list(parsed) == list(conds)  # 11 条件とも受け付けた(未知の名で落ちない)
    assert all(v == 0.0 for v in parsed.values())
    assert [int(x) for x in R.refractory_ticks(parsed)] == [0] * 11
    assert M.effective_minutes("B") == [0] * 11
    assert M.effective_minutes("A") == list(REFRACTORY_MINUTES)
    assert M.scale_items("A") == [] and M.cli_flags("A") == []

    for k, c in enumerate(conds, start=1):
        arm = f"C{k}"
        assert M.arm_condition(arm) == c
        assert cli.parse_refractory_scale(M.scale_items(arm)) == {c: 0.0}
        want = list(REFRACTORY_MINUTES)
        want[k - 1] = 0
        assert M.effective_minutes(arm) == want


def test_arm_names_and_plan(M):
    assert M.arm_names() == ("A", "B", *(f"C{k}" for k in range(1, 12)))
    todo = M.plan()
    # 3 構成 × seed 1 × 13 腕 + w6_v3_default の seed 2・3 × 13 腕
    assert len(todo) == 3 * 13 + 2 * 13
    assert len(set(todo)) == len(todo)
    assert {s for c, a, s in todo if c != "w6_v3_default"} == {1}
    assert {s for c, a, s in todo if c == "w6_v3_default"} == {1, 2, 3}
    with pytest.raises(ValueError):
        M.arm_condition("C12")
    with pytest.raises(ValueError):
        M.arm_condition("Z")


def test_factor_zero_means_no_suppression_in_the_arbiter(M):
    """既知の答え: 1 刻み前に条件 i で呼んだ体 i が、いま同じ条件 i で起きる。"""
    from shibuya.agents.state import WAKE_CONDITION_CLASS
    from shibuya.engine import resolve as R
    from shibuya.engine.arbiter import WakeCandidates, arbitrate

    n = 11
    tick = 100
    cand = WakeCandidates(
        np.arange(n, dtype=np.int64),
        np.arange(n, dtype=np.int8),
        np.asarray([int(WAKE_CONDITION_CLASS[i]) for i in range(n)], dtype=np.int64),
        np.full(n, tick, dtype=np.int64),
    )

    def n_suppressed(table) -> int:
        ru = np.zeros((n, n), dtype=np.int32)
        for i in range(n):
            ru[i, i] = (tick - 1) + int(table[i])  # set_refractory と同じ式(until = 呼んだ刻み + 表)
        d = arbitrate(cand, tick, float(n), b"refr20b", refractory_until=ru)
        return len(d.suppressed)

    assert n_suppressed(R.refractory_ticks(None)) == 10  # 会話ターン(0 分)だけ通る
    assert n_suppressed(R.refractory_ticks(M.scale_dict("B"))) == 0


# ---------------------------------------------------------------- 合成の manifest → 表
def _manifest(calls_by_condition: dict[str, int], scale: dict[str, float]) -> dict:
    total = int(sum(calls_by_condition.values()))
    return {
        "policy": "mock",
        "run_kind": "arm" if scale else "reproduction",
        "refractory_scale": dict(scale),
        "calls_by_model": {"judge_model": 0, "llm": total},
        "calls_by_condition": dict(calls_by_condition),
        "daily": [{"calls_by_model": {"judge_model": 0, "llm": total}}],
    }


def _obs(total: int, final: str, suppressed: int) -> dict:
    return {
        "llm_calls": total, "final": final, "n_agents": 5_000,
        "arbiter": {"suppressed": {"CONVERSATION": 0, "PLAN_BOUNDARY": suppressed, "INDIVIDUAL": 0, "CELL": 0}},
        "sleep_suppressed": 7, "outside_suppressed": 3, "candidates": total * 2, "merged": 11,
        "conversation_sessions": 5, "conversations_diag": 9, "calls_by_hour": [total // 24] * 24,
    }


def _cbc(M, **kw) -> dict[str, int]:
    base = {c: 0 for c in (*M.conditions(), "ACTIVITY_EXPIRY")}
    base.update(kw)
    return base


def _three_rows(M) -> list[dict]:
    a_cbc = _cbc(M, CONVERSATION_TURN=100, PLAN_GENERAL=300, INTEROCEPTION=600)  # 1,000
    b_cbc = _cbc(M, CONVERSATION_TURN=150, PLAN_GENERAL=900, INTEROCEPTION=1_450)  # 2,500
    c8_cbc = dict(a_cbc)  # 近接入替は候補が出ない=A と同じ
    rows = []
    for arm, cbc, final, sup in (("A", a_cbc, "aaaa", 40), ("B", b_cbc, "bbbb", 0), ("C8", c8_cbc, "aaaa", 40)):
        scale = M.scale_dict(arm)
        total = int(sum(cbc.values()))
        rows.append(M.row_from_manifest(_manifest(cbc, scale), _obs(total, final, sup),
                                        config="w6_v3_default", arm=arm, seed=1, kw={"vocab_version": "v3"}, wall_s=1.0))
    return rows


def test_table_from_three_synthetic_manifests_is_deterministic(M):
    rows = _three_rows(M)
    t = M.build_table(rows)
    assert len(t["groups"]) == 1
    g = t["groups"][0]
    assert g["A"]["calls"] == 1_000 and g["B"]["calls"] == 2_500
    assert g["ratio_B"] == 2.5
    assert g["delta_B"] == 1_500
    assert g["by_condition_delta_B"]["PLAN_GENERAL"] == 600
    assert g["by_condition_delta_B"]["INTEROCEPTION"] == 850
    assert g["A"]["split_k2"] == {"judge_model": 900, "llm": 100}
    assert g["B"]["split_k2"] == {"judge_model": 2_350, "llm": 150}
    assert g["A"]["calls_by_model"] == {"judge_model": 0, "llm": 1_000}
    assert g["A"]["suppressed"] == 40 and g["B"]["suppressed"] == 0
    assert [(e["arm"], e["delta"], e["rank"], e["same_final_as_A"]) for e in g["C"]] == [("C8", 0, 1, True)]
    assert "interaction" not in g  # C が 11 本そろわないと足し算の差は出さない
    # 行の中身(manifest から読んだ欄)
    rb = [r for r in rows if r["arm"] == "B"][0]
    assert rb["refractory_flags"] == M.cli_flags("B")
    assert set(rb["refractory_scale"]) == set(M.conditions())
    assert rb["calls_by_model_daily"] == [{"judge_model": 0, "llm": 2_500}]
    # 並びを入れ替えても同じ表
    want = json.dumps(t, ensure_ascii=False, sort_keys=True)
    for s in range(5):
        shuffled = list(rows)
        random.Random(s).shuffle(shuffled)
        assert json.dumps(M.build_table(shuffled), ensure_ascii=False, sort_keys=True) == want


def test_rank_of_eleven_c_arms_breaks_ties_by_condition_index(M):
    conds = M.conditions()
    a_cbc = _cbc(M, PLAN_GENERAL=1_000)
    rows = [M.row_from_manifest(_manifest(a_cbc, {}), _obs(1_000, "aaaa", 10), config="v3_mem_rel", arm="A", seed=1)]
    # 増分: INTEROCEPTION +300・PLAN_TRANSIT +300(同点)・CELL_BLOCK +50・ほか 0
    inc = {"INTEROCEPTION": 300, "PLAN_TRANSIT": 300, "CELL_BLOCK": 50}
    for k, c in enumerate(conds, start=1):
        cbc = dict(a_cbc)
        cbc[c] = cbc.get(c, 0) + inc.get(c, 0)
        total = int(sum(cbc.values()))
        rows.append(M.row_from_manifest(_manifest(cbc, M.scale_dict(f"C{k}")), _obs(total, "aaaa" if c not in inc else f"c{k}", 10),
                                        config="v3_mem_rel", arm=f"C{k}", seed=1))
    b_cbc = dict(a_cbc)
    b_cbc["INTEROCEPTION"] = 400
    b_cbc["PLAN_TRANSIT"] = 400
    b_cbc["CELL_BLOCK"] = 80
    rows.append(M.row_from_manifest(_manifest(b_cbc, M.scale_dict("B")), _obs(int(sum(b_cbc.values())), "bbbb", 0),
                                    config="v3_mem_rel", arm="B", seed=1))
    g = M.build_table(rows)["groups"][0]
    order = [e["condition"] for e in g["C"]]
    # PLAN_TRANSIT(番号 4)が INTEROCEPTION(番号 5)より先・0 の 8 本は番号順
    assert order[:3] == ["PLAN_TRANSIT", "INTEROCEPTION", "CELL_BLOCK"]
    assert order[3:] == [c for c in conds if c not in inc]
    assert [e["rank"] for e in g["C"]] == list(range(1, 12))
    assert g["sum_C_delta"] == 650
    assert g["delta_B"] == 880
    assert g["interaction"] == 230
    assert g["ratio_B"] == round(1_880 / 1_000, 4)


def test_seed_spread(M):
    rows = []
    for seed, b_total in ((1, 2_000), (2, 3_000), (3, 2_500)):
        rows.append(M.row_from_manifest(_manifest(_cbc(M, PLAN_GENERAL=1_000), {}), _obs(1_000, "a", 1),
                                        config="w6_v3_default", arm="A", seed=seed))
        rows.append(M.row_from_manifest(_manifest(_cbc(M, PLAN_GENERAL=b_total), M.scale_dict("B")), _obs(b_total, "b", 0),
                                        config="w6_v3_default", arm="B", seed=seed))
    sp = M.build_table(rows)["seed_spread"]["w6_v3_default"]
    assert sp["seeds"] == [1, 2, 3]
    assert sp["ratio_B"] == [2.0, 3.0, 2.5]
    assert (sp["ratio_B_min"], sp["ratio_B_max"], sp["ratio_B_mean"]) == (2.0, 3.0, 2.5)


def test_compare_rows_finds_only_real_differences(M):
    a = _three_rows(M)
    b = [dict(r) for r in _three_rows(M)]
    for r in b:
        r["wall_s"] = 99.0  # 壁時計は比べない
    assert M.compare_rows(a, b) == {"n_common": 3, "n_same": 3, "keys": list(M.SAME_KEYS), "differ": {},
                                    "only_a": 0, "only_b": 0}
    b[1]["final"] = "zzzz"
    b[1]["calls"] += 1
    got = M.compare_rows(a, b)
    assert got["n_same"] == 2
    assert got["differ"] == {"w6_v3_default/B/s1": ["final", "calls"]}


def test_activity_gate_count_is_carried_into_the_row_and_table(M):
    obs = _obs(1_000, "aaaa", 1)
    obs["activity_counters"] = {"cell_block_suppressed": 123, "activity_set": 9}
    r = M.row_from_manifest(_manifest(_cbc(M, PLAN_GENERAL=1_000), {}), obs, config="w6_v3_default", arm="A", seed=1)
    assert r["activity_cell_block_suppressed"] == 123
    assert r["activity_counters"] == {"cell_block_suppressed": 123, "activity_set": 9}
    assert M.build_table([r])["groups"][0]["A"]["activity_cell_block_suppressed"] == 123
    r0 = M.row_from_manifest(_manifest(_cbc(M), {}), _obs(0, "a", 0), config="w6_v1_default", arm="A", seed=1)
    assert r0["activity_cell_block_suppressed"] == 0  # 活動層の無い構成(v1)は 0


# ---------------------------------------------------------------- 追記(活動層の門・体数・表の外の門)
def _ab_rows(M, config: str, a_cbc: dict, b_cbc: dict, *, n: int = 5_000, gate=(0, 0)) -> list[dict]:
    out = []
    for arm, cbc, g in (("A", a_cbc, gate[0]), ("B", b_cbc, gate[1])):
        total = int(sum(cbc.values()))
        obs = _obs(total, arm.lower() * 4, 0)
        obs["n_agents"] = n
        obs["activity_counters"] = {"cell_block_suppressed": g}
        out.append(M.row_from_manifest(_manifest(cbc, M.scale_dict(arm)), obs, config=config, arm=arm, seed=1))
    return out


def test_activity_gate_and_scale_check_from_synthetic_rows(M):
    on = _ab_rows(M, "w6_v3_default", _cbc(M, INTEROCEPTION=800, CELL_BLOCK=200), _cbc(M, INTEROCEPTION=1_000, CELL_BLOCK=300),
                  gate=(5_000, 6_000))  # 1,000 → 1,300(1.3 倍・場所の変化 +100)
    off = _ab_rows(M, "w6_v3_activity_off", _cbc(M, INTEROCEPTION=800, CELL_BLOCK=400),
                   _cbc(M, INTEROCEPTION=1_000, CELL_BLOCK=2_000))  # 1,200 → 3,000(2.5 倍・場所の変化 +1,600)
    big = _ab_rows(M, "w6_v3_default", _cbc(M, INTEROCEPTION=3_200, CELL_BLOCK=800),
                   _cbc(M, INTEROCEPTION=4_000, CELL_BLOCK=1_400), n=20_000)  # 4,000 → 5,400(1.35 倍)
    t = M.build_table([*on, *off, *big])
    # 体数ごとに別の群(5,000 体の群に 20,000 体の行が混ざらない)
    assert [(g["config"], g["n_agents"]) for g in t["groups"]] == [
        ("w6_v3_default", 5_000), ("w6_v3_default", 20_000), ("w6_v3_activity_off", 5_000)]
    ag = t["activity_gate"]
    assert (ag["on"]["ratio_B"], ag["off"]["ratio_B"]) == (1.3, 2.5)
    assert ag["ratio_B_diff_off_minus_on"] == 1.2
    assert ag["ratio_B_ratio_off_over_on"] == round(2.5 / 1.3, 4)
    assert ag["calls_A_diff_on_minus_off_by_condition"] == {"CELL_BLOCK": -200}
    assert "層ごと off" in ag["note"]
    assert (ag["on"]["cell_block_delta_B"], ag["off"]["cell_block_delta_B"]) == (100, 1_600)
    assert ag["cell_block_delta_B_diff_off_minus_on"] == 1_500
    assert ag["on"]["cell_block_share_of_delta_B"] == round(100 / 300, 4)
    assert (ag["on"]["activity_gate_suppressed_A"], ag["on"]["activity_gate_suppressed_B"]) == (5_000, 6_000)
    (sc,) = t["scale_check"]
    assert (sc["n_base"], sc["n"], sc["ratio_B_base"], sc["ratio_B"]) == (5_000, 20_000, 1.3, 1.35)
    assert sc["ratio_B_diff"] == 0.05
    assert sc["ratio_B_rel_diff"] == round(1.35 / 1.3 - 1.0, 4)
    assert (sc["per_agent_day_A_base"], sc["per_agent_day_A"]) == (0.2, 0.2)
    assert sc["per_agent_delta_B_by_condition"] == {"INTEROCEPTION": 0.04, "CELL_BLOCK": 0.03}
    # seed の幅は 5,000 体の群だけ(seed 1 本しか無いので出ない)
    assert "w6_v3_default" not in t["seed_spread"]
    assert M.row_name("w6_v3_default", "A", 1, 20_000) == "w6_v3_default__A__s1__n20000.json"
    assert M.row_name("w6_v3_default", "A", 1) == "w6_v3_default__A__s1.json"


def test_gates_outside_table_symbols_are_defined_in_their_files(M):
    """表の外の門の一覧: 名と出典だけ・出典は「ファイル+記号」(行番号なし)・その記号の定義がファイルに実在する。"""
    import re

    assert len(M.GATES_OUTSIDE_TABLE) >= 5
    for g in M.GATES_OUTSIDE_TABLE:
        assert set(g) == {"name", "source"}
        assert not re.search(r"\.py:\d", g["source"])  # 行番号を書かない(並行の段の変更でずれる)
        refs = M.gate_refs(g)
        assert refs
        for path, sym in refs:
            assert re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", sym), sym
            text = (ROOT / path).read_text(encoding="utf-8")
            assert M.symbol_defined(text, sym), (path, sym)
    # 負の対照: 無い記号・使うだけで定義の無い名は通らない
    assert not M.symbol_defined("x = REL_ACQ_PAIR_REFRACTORY_MIN + 1\n", "REL_ACQ_PAIR_REFRACTORY_MIN")
    assert M.symbol_defined("REL_ACQ_PAIR_REFRACTORY_MIN: Final[int] = 60\n", "REL_ACQ_PAIR_REFRACTORY_MIN")
    assert M.symbol_defined("    def merged_total(self) -> int:\n", "merged_total")
    assert M.gate_refs({"name": "x", "source": "src/a.py FOO(注・注)・BAR"}) == [("src/a.py", "FOO"), ("src/a.py", "BAR")]
    assert len(M.GATES_OUTSIDE_TABLE) == 8
    names = " ".join(g["name"] for g in M.GATES_OUTSIDE_TABLE)
    for word in ("活動層", "D-56", "D-66", "合流", "招待", "意図の保持", "D-62"):
        assert word in names


# ---------------------------------------------------------------- 外挿・出力
def test_extrapolate_known_answer(M):
    e = M.extrapolate(2.5, 5_000, n_full=390_000, n_sample=5_000, days=7, conv_share_B=0.1)
    assert e["base_full_per_day"] == 390_000
    assert e["B_full_per_day"] == 975_000
    assert e["B_full_per_week"] == 6_825_000
    assert e["split_k2_per_day"] == {"judge_model": 877_500, "llm": 97_500}
    assert e["per_agent_day_A"] == 1.0 and e["per_agent_day_B"] == 2.5


def test_write_outputs_writes_json_and_markdown_without_absolute_paths(M, tmp_path):
    rows = _three_rows(M)
    doc = M.write_outputs(rows, tmp_path)
    js = (tmp_path / "refractory_calls.json").read_text(encoding="utf-8")
    md = (tmp_path / "refractory_calls.md").read_text(encoding="utf-8")
    assert json.loads(js)["table"]["groups"][0]["ratio_B"] == 2.5
    assert "**2.5**" in md
    assert "C8" in md and "PROXIMITY_SWAP" in md
    ref = doc["extrapolation"]["reference"]
    assert ref["n_full"] == 390_067  # 10e の budget_10e.json
    assert ref["calls_5000"]["w6_v3_default"] == 65_597  # 10e の ret.json(§締め-1 の ACT の行)
    e = doc["extrapolation"]["by_config"]["w6_v3_default"]
    assert e["base_full_per_day"] == round(65_597 * 390_067 / 5_000)
    assert e["B_full_per_day"] == round(65_597 * 390_067 / 5_000 * 2.5)
    gates = json.loads(js)["gates_outside_table"]
    assert gates == [dict(g) for g in M.GATES_OUTSIDE_TABLE]
    assert "不応期の表の外の門" in md
    for text in (js, md):
        assert str(ROOT) not in text and str(tmp_path) not in text
        assert ":\\" not in text and "C:/" not in text
