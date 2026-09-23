"""W17 プロンプト生成: 決定論・fleet_gen 形式・seed=hash(agent)・種別別テンプレ・シャード。

対応する仕様行
- §1 W17「呼数=体数」・§0-8「温度と seed を固定」
- D-W17 (i)「モデル=T1(8B INT8)全件・温度 0.7・seed=hash(agent)」(ii)「プロンプト=種別別
  テンプレ凍結(SHA)」(iv)「予算=I1」
- 行動契約書 §2.1「活動表の語は行動語彙へ写像できること」
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from shibuya.build.sched import vocab as V
from shibuya.build.sched import w17_schedule as W17

from .conftest import AGENTS


# ---------------------------------------------------------------- 語彙と契約書の整合
def test_activity_words_map_into_action_contract():
    """活動語 12 は全て行動契約書 §2.1 の「種別横断12語」へ写像できる。"""
    assert len(V.ACTIVITY_WORDS) == 12
    assert len(V.PLACE_WORDS) == 12
    assert set(V.ACTIVITY_TO_ACTION) == set(V.ACTIVITY_WORDS)
    assert set(V.ACTIVITY_TO_ACTION.values()) <= set(V.ACTION_WORDS)
    assert len(V.ACTIVITY_TO_WAKE) == len(V.ACTIVITY_WORDS)


def test_wake_conditions_match_perception_contract():
    """``ACTIVITY_TO_WAKE`` は知覚契約書 §6 の計画境界 4 行(``WakeCondition``)と一致。"""
    from shibuya.agents.state import WakeCondition

    assert V.WAKE_PLAN_SLEEPING == int(WakeCondition.PLAN_SLEEPING)
    assert V.WAKE_PLAN_WORKING == int(WakeCondition.PLAN_WORKING)
    assert V.WAKE_PLAN_GENERAL == int(WakeCondition.PLAN_GENERAL)
    assert V.WAKE_PLAN_TRANSIT == int(WakeCondition.PLAN_TRANSIT)
    assert set(V.ACTIVITY_TO_WAKE) <= {
        int(WakeCondition.PLAN_SLEEPING), int(WakeCondition.PLAN_WORKING),
        int(WakeCondition.PLAN_GENERAL), int(WakeCondition.PLAN_TRANSIT),
    }


# ---------------------------------------------------------------- 決定論
def test_prompts_are_deterministic(world_dir: Path, data_dir: Path):
    """同じ入力から 2 回作って SHA が一致する(§0-1 決定論)。"""
    a = W17.build_prompts(world_dir, data_dir)
    b = W17.build_prompts(world_dir, data_dir)
    assert W17.prompts_sha256(a) == W17.prompts_sha256(b)
    assert [p.id for p in a] == [str(r[0]) for r in AGENTS]


def test_call_count_equals_agent_count(world_dir: Path, data_dir: Path):
    """呼数=体数(repeat 1)。"""
    prompts = W17.build_prompts(world_dir, data_dir)
    assert len(prompts) * W17.REPEAT == len(AGENTS)


def test_prompt_fields_match_fleet_gen_format(world_dir: Path, data_dir: Path):
    """``tools/gen/fleet_gen.py`` が読む欄が揃っている(温度 0.7・repeat 1・thinking false)。"""
    p = W17.build_prompts(world_dir, data_dir)[0].to_json()
    assert set(p) >= {"id", "system", "user", "max_tokens", "temperature", "seed", "repeat"}
    assert p["temperature"] == 0.7
    assert p["repeat"] == 1
    assert p["thinking"] is False
    assert p["max_tokens"] == W17.MAX_TOKENS


# ---------------------------------------------------------------- seed=hash(agent)
def test_seed_is_deterministic_and_matches_prompt(world_dir: Path, data_dir: Path):
    for p in W17.build_prompts(world_dir, data_dir):
        assert p.seed == W17.agent_seed(int(p.id))
        assert 0 <= p.seed < W17.SEED_MOD


def test_seed_is_unique_over_population_scale():
    """39 万体規模で seed が衝突しない(2^53 剰余=衝突期待値 1e-5 件未満)。"""
    seeds = {W17.agent_seed(i) for i in range(400_000)}
    assert len(seeds) == 400_000


@settings(max_examples=200, deadline=None)
@given(st.integers(min_value=0, max_value=10_000_000))
def test_seed_hypothesis_range(agent_id: int):
    s = W17.agent_seed(agent_id)
    assert 0 <= s < W17.SEED_MOD
    assert s == W17.agent_seed(agent_id)


# ---------------------------------------------------------------- 種別別テンプレ
def test_system_templates_are_frozen_per_kind():
    """種別ごとに system が違い、共通部が先頭にある(prefix キャッシュが効く形)。"""
    shas = W17.system_sha256()
    assert len(shas) == 9
    assert len(set(shas.values())) == 9
    for k in range(9):
        assert W17.system_prompt(k).startswith(W17.SYSTEM_COMMON)


def test_system_states_the_format_and_vocabulary():
    """**日見出し形**の書式・例・語彙・規則が system に書かれている。"""
    sysmsg = W17.SYSTEM_COMMON
    assert "曜日の見出し行" in sysmsg and "活動行" in sysmsg
    assert "<開始HHMM>-<終了HHMM> <活動語> <場所語>" in sysmsg
    for d in range(7):  # 例と見出しの説明に d0..d6 が出る
        assert f"d{d}" in sysmsg
    assert "0900-1800 勤務 職場" in sysmsg  # 例(日見出し形の 3 列)
    for w in V.ACTIVITY_WORDS:
        assert w in sysmsg
    for w in V.PLACE_WORDS:
        assert w in sysmsg
    assert "表以外は何も書かない" in sysmsg and "行末に空白を置かない" in sysmsg
    assert f"{W17.LINES_PER_DAY_MIN}行から{W17.LINES_PER_DAY_MAX}行" in sysmsg


def test_user_prompt_carries_the_facts(world_dir: Path, data_dir: Path):
    prompts = {p.id: p.user for p in W17.build_prompts(world_dir, data_dir)}
    assert "年金生活者" in prompts["0"] and W17.NO_DUTY_LINE in prompts["0"]
    assert "勤務: 渋谷 月火水木金 0900-1800" in prompts["1"]
    assert "自宅: 域外(川崎・多摩方面)" in prompts["2"]
    assert "通学: 小学校 渋谷 月火水木金" in prompts["3"]
    assert "来訪日:" in prompts["4"] and "目的: 買い物" in prompts["4"]
    assert "夜勤" in prompts["2"]  # 職業「深夜スタッフ」→ 夜勤窓
    assert "指令" in prompts["7"]  # 素材の無い体は種別名で埋める(「無職」と書かない)


def test_every_prompt_has_exactly_one_plan_line(world_dir: Path, data_dir: Path):
    """**勤務・通学・来訪のどれか 1 行が必ず入る**(第1回パイロットの退化への対処)。

    「勤務・通学: なし」が出るのは**無職の体だけ**。
    """
    facts = W17.build_facts(world_dir, data_dir)
    for i, p in enumerate(W17.build_prompts(world_dir, data_dir, facts=facts)):
        hit = [
            ln for ln in p.user.splitlines()
            if ln.startswith(("勤務: ", "通学: ", "来訪日: ")) or ln == W17.NO_DUTY_LINE
        ]
        assert len(hit) == 1, f"id={p.id}: {p.user}"
        if hit[0] == W17.NO_DUTY_LINE:
            occ = facts.pool.col("occupation")[i]
            assert occ in W17.NON_WORKING_OCCUPATIONS, f"無職でないのに『なし』: {occ}"
            assert int(facts.duty_activity[i]) == -1
            assert int(facts.visit_days[i]) == 0
        else:
            assert int(facts.duty_activity[i]) >= 0 or int(facts.visit_days[i]) != 0


def test_residents_without_a_seat_get_an_outside_workplace(world_dir: Path, data_dir: Path):
    """勤務席の無い住民は**域外勤務**として facts に入る(パイロット id=11 の再発防止)。"""
    facts = W17.build_facts(world_dir, data_dir)
    idx = {int(a): i for i, a in enumerate(facts.agent_id)}
    i = idx[2]  # 域外常住の通勤者(渋谷の職場)
    assert not bool(facts.duty_outside[i])
    j = idx[8]  # 学齢の住民(渋谷の学校)
    assert facts.duty_activity[j] == V.ACT_SCHOOL and facts.duty_stage[j] == "小学校"


def test_school_age_agents_always_get_a_school_line(world_dir: Path, data_dir: Path):
    """15 歳未満は学校セルが無くても通学として書く。"""
    facts = W17.build_facts(world_dir, data_dir)
    for i in range(facts.n):
        if int(facts.age[i]) < W17.SCHOOL_AGE_MAX and int(facts.visit_days[i]) == 0:
            assert int(facts.duty_activity[i]) == V.ACT_SCHOOL
            assert facts.duty_stage[i] in W17.SCHOOL_WINDOW


def test_prompt_tokens_within_budget(world_dir: Path, data_dir: Path):
    """入力トークン(共有 prefix 込み)の平均が目標以下(§1 予算・報告値)。"""
    prompts = W17.build_prompts(world_dir, data_dir)
    toks = [W17.estimate_tokens(p.system) + W17.estimate_tokens(p.user) for p in prompts]
    assert max(toks) <= W17.PROMPT_TOKEN_TARGET
    assert sum(toks) / len(toks) <= W17.PROMPT_TOKEN_TARGET


# ---------------------------------------------------------------- シャード
@pytest.mark.parametrize("n_shards", [1, 2, 3, 4])
def test_shards_partition_the_population(world_dir: Path, data_dir: Path, n_shards: int):
    facts = W17.build_facts(world_dir, data_dir)
    ids: list[str] = []
    for s in range(n_shards):
        ids += [p.id for p in W17.build_prompts(world_dir, data_dir, shard=s,
                                                n_shards=n_shards, facts=facts)]
    assert sorted(ids, key=int) == sorted((str(r[0]) for r in AGENTS), key=int)
    assert len(ids) == len(set(ids))


def test_shard_bounds_are_checked(world_dir: Path, data_dir: Path):
    facts = W17.build_facts(world_dir, data_dir)
    with pytest.raises(ValueError):
        list(W17.iter_prompts(facts, shard=3, n_shards=3))


def test_write_prompts_streams_jsonl(world_dir: Path, data_dir: Path, tmp_path: Path):
    facts = W17.build_facts(world_dir, data_dir)
    rec = W17.write_prompts(tmp_path, facts)
    assert rec["rows"] == len(AGENTS)
    assert rec["path"] == W17.PROMPTS_NAME
    lines = (tmp_path / W17.PROMPTS_NAME).read_text(encoding="utf-8").splitlines()
    assert len(lines) == len(AGENTS)
    rec2 = W17.write_prompts(tmp_path, facts, shard=1, n_shards=4)
    assert rec2["path"] == "w17_prompts.1of4.jsonl"


# ---------------------------------------------------------------- 個体の事実
def test_facts_windows_by_kind(world_dir: Path, data_dir: Path):
    f = W17.build_facts(world_dir, data_dir)
    idx = {int(a): i for i, a in enumerate(f.agent_id)}
    assert f.duty_activity[idx[0]] == -1  # 非就業
    assert (f.work_open[idx[1]], f.work_close[idx[1]]) == (540, 1080)
    assert f.work_close[idx[2]] > 1440  # 夜勤(翌日へ跨ぐ)
    assert f.duty_activity[idx[3]] == V.ACT_SCHOOL
    assert f.visit_days[idx[4]] != 0 and bin(int(f.visit_days[idx[4]])).count("1") == 1
    assert bin(int(f.work_days[idx[6]])).count("1") == 5  # 乗務員=毎日−交代2日
    # 定期来街(visit_cadence="weekly")= seed から 2 曜日
    assert bin(int(f.visit_days[idx[9]])).count("1") == 2


def test_regular_visitor_school_day_cadence(tmp_path: Path):
    """``visit_cadence == "school_day"`` の定期来街者は平日 5 日になる。"""
    from .conftest import POIS, _expand, _write, write_pool, write_population

    world = tmp_path / "w"
    world.mkdir()
    write_population(world, [(0, 6, 3, 9, 1, -1, -1, -1, 1, 3, 0)])
    _write(world / "w6_poi.parquet",
           {"poi_id": [p[0] for p in POIS], "cat": [p[1] for p in POIS],
            "subcat": [p[2] for p in POIS]})
    _write(world / "w7_plan_spec.parquet",
           {"poi_id": [p[0] for p in POIS], "content": [_expand(p[3]) for p in POIS]})
    _write(world / "w12_generation_weights.parquet",
           {"node_id": ["n"], "purpose": ["私事"], "hour": [11], "weight": [1.0]})
    data = tmp_path / "d"
    write_pool(data / "persona_pool_v2")
    f = W17.build_facts(world, data)
    assert int(f.visit_days[0]) == 0b0011111


# ================================================================= 構造化出力(regex)
def _week_text(days: dict[int, list[tuple[int, int, int, int]]]) -> str:
    """``{曜日: [(start, end, act, place), …]}`` → 日見出し形の本文(7 日ぶんの見出し)。"""
    return V.format_schedule(
        [V.Act(d, s, e, a, p) for d, rows in days.items() for (s, e, a, p) in rows]
    )


def _uniform_week(n_lines: int, place: int = V.PLACE_HOME, act: int = V.ACT_REST) -> str:
    rows = [(60 * j, 60 * j + 30, act, place) for j in range(n_lines)]
    return _week_text({d: rows for d in range(7)})


@pytest.fixture()
def facts(world_dir: Path, data_dir: Path) -> W17.AgentFacts:
    return W17.build_facts(world_dir, data_dir)


def _row(facts: W17.AgentFacts, agent_id: int) -> int:
    import numpy as np

    return int(np.flatnonzero(facts.agent_id == agent_id)[0])


def test_place_set_drops_facts_the_agent_does_not_have(facts):
    """事実にない場所語は regex から外す(固有名詞検査の代わりの構造検査)。"""
    resident = W17.place_set(facts, _row(facts, 0))  # 無職の住民
    assert "域外" not in resident and "職場" not in resident and "学校" not in resident
    worker = W17.place_set(facts, _row(facts, 1))  # 区内勤務の住民
    assert "職場" in worker and "域外" not in worker
    commuter = W17.place_set(facts, _row(facts, 2))  # 域外常住の通勤者
    assert "域外" in commuter and "職場" in commuter
    student = W17.place_set(facts, _row(facts, 3))  # 通学者(渋谷の学校)
    assert "学校" in student and "域外" in student and "職場" not in student
    visitor = W17.place_set(facts, _row(facts, 4))  # 来街者
    assert "域外" in visitor
    for i in range(facts.n):  # 常に許す 9 語
        got = W17.place_set(facts, i)
        for w in ("自宅", "駅", "飲食店", "物販店", "公園", "娯楽施設", "宿泊施設",
                  "医療施設", "路上"):
            assert w in got


@pytest.mark.parametrize("agent_id", [0, 1, 2, 3, 6, 7, 8])
def test_regex_accepts_four_and_five_lines_per_day(facts, agent_id: int):
    """陽性: 各日 4-5 行 × 7 日はマッチする(末尾改行の有無どちらも)。"""
    rx = W17.prompt_regex(facts, _row(facts, agent_id))
    for n in (4, 5):
        text = _uniform_week(n)
        assert re.fullmatch(rx, text), f"{agent_id}: {n} 行が通らない"
        assert re.fullmatch(rx, text + "\n"), "末尾改行つきが通らない"


@pytest.mark.parametrize("agent_id", [0, 1, 2, 3, 6, 7, 8])
@pytest.mark.parametrize("n", [0, 1, 3, 6, 12])
def test_regex_rejects_wrong_line_counts(facts, agent_id: int, n: int):
    """陰性: 1 日 3 行以下・6 行以上は通らない(第2回パイロットの 12 行/日を封じる)。"""
    rx = W17.prompt_regex(facts, _row(facts, agent_id))
    assert re.fullmatch(rx, _uniform_week(n)) is None


def test_regex_rejects_a_missing_day(facts):
    rx = W17.prompt_regex(facts, _row(facts, 1))
    text = _uniform_week(4)
    broken = "\n".join(ln for ln in text.split("\n") if ln != "d3")
    assert re.fullmatch(rx, broken) is None


def test_regex_rejects_trailing_space_and_old_format(facts):
    rx = W17.prompt_regex(facts, _row(facts, 1))
    assert re.fullmatch(rx, _uniform_week(4).replace(" 自宅", " 自宅 ")) is None
    assert re.fullmatch(rx, V.format_schedule_flat(
        [V.Act(d, 60 * j, 60 * j + 30, V.ACT_REST, V.PLACE_HOME)
         for d in range(7) for j in range(4)]
    )) is None


def test_regex_rejects_places_the_agent_cannot_have(facts):
    """無職の住民は「域外」を書けない(第2回パイロットで全活動が域外になった)。"""
    rx = W17.prompt_regex(facts, _row(facts, 0))
    assert re.fullmatch(rx, _uniform_week(4)) is not None
    assert re.fullmatch(rx, _uniform_week(4, place=V.PLACE_OUTSIDE)) is None
    assert re.fullmatch(rx, _uniform_week(4, place=V.PLACE_WORK)) is None
    assert re.fullmatch(rx, _uniform_week(4, place=V.PLACE_SCHOOL)) is None


def test_regex_rejects_out_of_vocabulary_words(facts):
    rx = W17.prompt_regex(facts, _row(facts, 1))
    assert re.fullmatch(rx, _uniform_week(4).replace("休憩", "瞑想")) is None
    assert re.fullmatch(rx, _uniform_week(4).replace("自宅", "オフィス")) is None


def test_regex_for_visitors_allows_only_the_visit_days(facts):
    """来街者は**来訪日だけ活動行**・他の日は見出しだけ。"""
    import numpy as np

    row = _row(facts, 4)
    rx = W17.prompt_regex(facts, row)
    visit = int(facts.visit_days[row])
    days = [d for d in range(7) if (visit >> d) & 1]
    rows = [(600, 630, V.ACT_RIDE, V.PLACE_STATION),
            (630, 780, V.ACT_SHOP, V.PLACE_SHOP),
            (780, 840, V.ACT_MEAL, V.PLACE_FOOD),
            (840, 900, V.ACT_RIDE, V.PLACE_OUTSIDE)]
    assert re.fullmatch(rx, _week_text({d: rows for d in days})) is not None
    # 来訪日でない日に書いたら不合格
    other = (days[0] + 1) % 7
    assert re.fullmatch(rx, _week_text({d: rows for d in days + [other]})) is None
    # 来訪日を空にしたら不合格
    assert re.fullmatch(rx, _week_text({})) is None
    assert np.all(np.isin(days, np.arange(7)))


def test_every_prompt_carries_a_regex(world_dir: Path, data_dir: Path):
    for p in W17.build_prompts(world_dir, data_dir):
        body = p.to_json()
        assert body["regex"] == p.regex and p.regex
        assert re.compile(p.regex)  # Python の re でコンパイルできる
        assert body["max_tokens"] == W17.MAX_TOKENS == 600


def test_regex_summary_is_deterministic(facts):
    a = W17.regex_summary(facts)
    b = W17.regex_summary(facts)
    assert a == b
    assert a["n_distinct"] >= 1
    assert set(a["by_kind"]) <= set(W17.KIND_NAMES)
    for v in a["by_kind"].values():
        assert len(v["sha256"]) == 64 and v["chars"] > 0
