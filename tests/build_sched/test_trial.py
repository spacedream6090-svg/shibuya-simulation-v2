"""D-68 下見(``build.sched.trial``): 層化・seed 決定論・逆関数法・文法・報告の機械検査。

対応する仕様行
- ``docs/design/v2-d68-pilot-design.md`` §1(5 腕)・§2(P1 の勤務窓投入)・§3(P2 の 2 段)・
  §4(標本 2,000 体の層化と seed 規約)・§6(ゲート再定義)・§7 リスク 8(ファイル名)・
  §8 決定項 2/3/9/10/12。
- ``docs/design/v2-plan-executor-design.md`` §9(ブロック形式・``block_kind``)。
- **本番 W17 を変えていない**ことも機械検査する(``user_prompt`` が下見専用欄を読まない)。
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pytest

from shibuya.build.sched import pool_facts as PF
from shibuya.build.sched import trial as T
from shibuya.build.sched import vocab as V
from shibuya.build.sched import w17_schedule as W17

from .conftest import write_pool, write_population

# ---------------------------------------------------------------- 合成の世界(下見用)
#: 雇用形態を全種類そろえた 6 層(``L2`` に並べる)。
_EMPS = ("正規", "非正規", "役員", "自営業主", "家族従業者", "非就業")


def _pool_rows(n: int) -> list[dict]:
    rows: list[dict] = []
    for i in range(n):
        rows.append({
            "id": f"L2_{i}", "age": 30 + (i % 30), "gender": "男" if i % 2 else "女",
            "occupation": "会社員", "name": f"標本{i:03d}", "rank": "一般",
            "industry_major": "情報通信業", "employment": _EMPS[i % len(_EMPS)],
            # 3 体に 1 体は ``arrival_lead_min`` が欠測(既定 30 分に落ちる)
            **({} if i % 3 == 0 else {"arrival_lead_min": 10 + (i % 100)}),
            "shift_pattern": {"open": "09:00", "close": "18:00", "days": "mon-fri",
                              "rotates": False},
            "work_days": "mon-fri", "bedtime_min": 1380, "sleep_steps": 42,
            "residence_line": "川崎・多摩方面", "commute_mode": "rail",
        })
    return rows


N_BODIES = 60


@pytest.fixture()
def trial_world(world_dir: Path, tmp_path: Path) -> tuple[Path, Path]:
    """通勤者 ``N_BODIES`` 体(雇用形態が全種類)の世界+プール。"""
    agents = [
        # (agent_id, kind, purpose, age, sex, home, work, school, dir, layer, index)
        (i, 0, 0, 30 + (i % 30), i % 2, -1, 2, -1, 3, 2, i)
        for i in range(N_BODIES)
    ]
    write_population(world_dir, agents)
    data = tmp_path / "trialdata"
    write_pool(data / "persona_pool_v2", {"L2": _pool_rows(N_BODIES)})
    return world_dir, data


@pytest.fixture()
def anchor() -> dict:
    """本物のアンカー台帳(``docs/bench/anchors/commute_time_dist_r3.json``)。"""
    p = T.anchor_path()
    if not p.exists():  # pragma: no cover - 台帳が無い環境
        pytest.skip(f"{p} が無い(--build-anchor で作る)")
    return T.load_anchor(p)


def _facts(trial_world) -> W17.AgentFacts:
    world, data = trial_world
    return W17.build_facts(world, data)


# ================================================================= 1. 標本(§4)
def test_sample_is_stratified_and_identical_across_arms(world_dir: Path, data_dir: Path):
    """層化の体数は設計書 §4 の表どおり・**全腕で同じ体**(対応のある比較)。"""
    f = W17.build_facts(world_dir, data_dir)
    rows = T.sample_rows(f, {k: 1 for k in T.TRIAL_N_PER_KIND})
    assert rows.size == 9  # 9 種別 × 1
    for name in ("p0b", "p1a", "p1b", "p2"):
        assert np.array_equal(T.sample_rows(f, {k: 1 for k in T.TRIAL_N_PER_KIND}), rows), name
    # 設計書 §4 の表の合計は 2,000
    assert sum(T.TRIAL_N_PER_KIND.values()) == 2_000
    # 32B 比較腕は 2,000 体の**入れ子**(先頭)= 200 体
    big = T.sample_rows(f, {k: 2 for k in T.TRIAL_N_PER_KIND})
    small = T.sample_rows(f, {k: 2 for k in T.TRIAL_N_PER_KIND}, total=9)
    assert set(small.tolist()) <= set(big.tolist())


def test_sample_and_windows_are_deterministic(trial_world, anchor: dict):
    """seed 決定論: 2 回引いて標本も勤務窓も**バイト同値**。"""
    f = _facts(trial_world)
    r1 = T.sample_rows(f, {0: N_BODIES})
    r2 = T.sample_rows(f, {0: N_BODIES})
    assert np.array_equal(r1, r2)
    a = T.draw_windows(f, anchor, rows=r1)
    b = T.draw_windows(f, anchor, rows=r2)
    assert np.array_equal(a.depart, b.depart)
    assert np.array_equal(a.arrive, b.arrive)
    assert np.array_equal(a.duty_open, b.duty_open)
    assert np.array_equal(a.duty_close, b.duty_close)
    assert np.array_equal(a.work_days, b.work_days)
    assert a.row == b.row and a.counters == b.counters


# ================================================================= 2. 逆関数法(§2-2)
def test_inverse_cdf_is_monotone_and_uniform_within_bin():
    """累積は単調・ビン内は 15 分一様(端も含む)。"""
    bt = T.BinTable(
        start=np.array([0, 15, 30]), width=np.array([15, 15, 15]),
        cdf=np.array([0.2, 0.5, 1.0]), actor_rate=1.0,
    )
    us = np.linspace(0.0, 1.0, 2001)[:-1]
    got = np.asarray([T.inverse_sample(bt, float(u)) for u in us])
    assert np.all(np.diff(got) >= 0)          # 単調
    assert got.min() == 0 and got.max() == 44  # 範囲は [0, 45)
    # ビン内一様: ビン 0(構成比 0.2)の中の 15 個の分がほぼ均等に出る
    inbin = got[got < 15]
    counts = np.bincount(inbin, minlength=15)
    assert counts.min() > 0
    assert counts.max() - counts.min() <= 2
    # ビンごとの出現比が構成比に一致
    share = np.asarray([(got < 15).mean(), ((got >= 15) & (got < 30)).mean(), (got >= 30).mean()])
    assert np.allclose(share, [0.2, 0.3, 0.5], atol=0.002)


def test_real_anchor_reproduces_research_quantiles(anchor: dict):
    """アンカー台帳が答申 §6-3 の分位(正規 6:15/7:30/9:00)を再現する。"""
    bt = T._bin_table(anchor["depart"], "正規の職員・従業員")
    assert abs(bt.actor_rate - 0.891) < 1e-9
    assert abs(float(bt.cdf[-1]) - 1.0) < 1e-9
    assert np.all(np.diff(bt.cdf) >= -1e-12)

    def q(t: float) -> int:
        return int(bt.start[int(np.searchsorted(bt.cdf, t))])

    assert (q(0.10), q(0.50), q(0.90)) == (6 * 60 + 15, 7 * 60 + 30, 9 * 60)
    ret = T._bin_table(anchor["return"], "正規の職員・従業員")
    assert int(ret.start[int(np.searchsorted(ret.cdf, 0.5))]) == 19 * 60


def test_employment_mix_weights_sum_to_one(anchor: dict):
    """決定項 2: 非正規の按分(パート/アルバイト/契約/嘱託/派遣)と自営業主 28:72 の重み和=1。"""
    mix = anchor["employment_mix"]
    assert set(mix["非正規"]) == {"パート", "アルバイト", "契約社員", "嘱託", "派遣社員"}
    assert abs(sum(mix["非正規"].values()) - 1.0) < 1e-6
    assert set(mix["自営業主"]) == {"雇人のある業主", "雇人のない業主"}
    assert abs(sum(mix["自営業主"].values()) - 1.0) < 1e-6
    assert abs(mix["自営業主"]["雇人のある業主"] - 0.28) < 0.01  # 28:72
    assert mix["非就業"] == {}
    for emp, names in T.EMPLOYMENT_MIX.items():
        assert set(mix[emp]) == set(names)
    # 逆関数法で引いた行は必ず表に載る
    for emp in ("正規", "非正規", "自営業主"):
        for u in (0.0, 0.33, 0.99):
            assert T.employment_row(anchor, emp, u) in anchor["depart"]["rows"]


# ================================================================= 3. 勤務窓(§2-3/4/5)
def test_duty_open_is_depart_plus_lead_and_length_clipped(trial_world, anchor: dict):
    """始業=出勤+``arrival_lead_min``(欠損は 30 分)・勤務長は [4h, 12h]。"""
    f = _facts(trial_world)
    rows = T.sample_rows(f, {0: N_BODIES})
    t = T.draw_windows(f, anchor, rows=rows)
    drawn = np.flatnonzero(t.duty_open >= 0)
    assert drawn.size > 0
    assert np.array_equal(t.duty_open[drawn], t.depart[drawn] + t.lead[drawn])
    length = t.duty_close[drawn] - t.duty_open[drawn]
    assert length.min() >= T.WORK_LEN_MIN_MIN
    assert length.max() <= T.WORK_LEN_MAX_MIN
    assert t.counters["work_len_clipped"] > 0
    # 欠損 lead は既定 30 分(プールの 3 体に 1 体)
    assert t.counters["lead_default"] > 0
    default_rows = [i for i in drawn if int(f.pool.arrival_lead_min[i]) <= 0]
    assert all(int(t.lead[i]) == T.LEAD_DEFAULT_MIN for i in default_rows)
    # 非就業は窓を引かない(決定項 1)
    for i in range(f.n):
        if f.pool.col("employment")[i] == "非就業":
            assert int(t.duty_open[i]) == -1


def test_absent_days_follow_actor_rate(anchor: dict):
    """§2-5: 欠勤は第31表の行動者率で曜日ごとに引く(大標本で ±2pt)。"""
    rate = T._bin_table(anchor["depart"], "正規の職員・従業員").actor_rate
    n = 20_000
    u = np.asarray([T.u01("absent:0", i) for i in range(n)])
    present = float((u < rate).mean())
    assert abs(present - rate) <= 0.02
    # 曜日ごとに独立(同じ体でも曜日が違えば別の乱数)
    u1 = np.asarray([T.u01("absent:1", i) for i in range(2_000)])
    assert not np.array_equal(u[:2_000], u1)
    # ドメインが違えば別系列(出勤・帰宅・雇用形態)
    for dom in ("depart", "return", "employment"):
        assert T.u01(dom, 7) != T.u01("absent:0", 7)


def test_windows_are_not_drawn_for_students_and_visitors(world_dir: Path, data_dir: Path,
                                                         anchor: dict):
    """通学者・来街者・非就業は窓を引かない(通学は本番のまま)。"""
    f = W17.build_facts(world_dir, data_dir)
    rows = T.sample_rows(f, {k: 2 for k in T.TRIAL_N_PER_KIND})
    t = T.draw_windows(f, anchor, rows=rows)
    for i in rows:
        i = int(i)
        if int(f.duty_activity[i]) != V.ACT_WORK:
            assert int(t.duty_open[i]) == -1, f"row {i} は勤務ではないのに窓を引いた"
    # 宿泊客は訪日だけ(決定項 12・expedient)
    from shibuya.build.pop.w16_population import KIND_FOREIGN_VISITOR

    for i in rows:
        i = int(i)
        assert bool(t.stay[i]) == (int(f.kind[i]) == KIND_FOREIGN_VISITOR)


# ================================================================= 4. 文法(§3)
def _p2_spec_and_facts(trial_world, anchor):
    f = _facts(trial_world)
    rows = T.sample_rows(f, {0: 4})
    t = T.draw_windows(f, anchor, rows=rows)
    return T.ARMS["p2"], f, t, int(rows[0])


def test_block_regex_allows_3_to_10_lines_and_bans_night_prep(trial_world, anchor: dict):
    """ブロック形式 regex: 行は ``{3,10}``・**0〜3 時台の 支度/乗車 はマッチしない**。"""
    spec, f, t, i = _p2_spec_and_facts(trial_world, anchor)
    rx = re.compile(T.block_regex(spec, f, t, i).replace("\\n", "\n"))

    def day(lines: list[str]) -> str:
        return "\n".join(f"d{d}\n" + "\n".join(lines) for d in range(V.N_DAYS))

    ok3 = ["0000-0800 3 就寝 自宅", "0800-1800 2 勤務 職場", "1800-2400 4 移動 駅"]
    assert rx.fullmatch(day(ok3)) is not None
    ok10 = (["0000-0100 3 就寝 自宅"]
            + [f"{h:02d}00-{h + 1:02d}00 2 休憩 飲食店" for h in range(1, 9)]
            + ["0900-2400 2 勤務 職場"])
    assert len(ok10) == 10 and rx.fullmatch(day(ok10)) is not None
    # 2 行は少なすぎ / 11 行は多すぎ
    assert rx.fullmatch(day(ok3[:2])) is None
    assert rx.fullmatch(day(ok10 + ["2300-2400 3 就寝 自宅"])) is None
    # 深夜(0〜3 時台)に 支度 / 乗車 を置いた日はマッチしない
    for act in T.NIGHT_BAN_ACTS:
        bad = ["0000-0230 3 就寝 自宅", f"0230-0300 2 {act} 駅", "0300-2400 2 勤務 職場"]
        assert rx.fullmatch(day(bad)) is None, act
    # 4 時以降の同じ活動語は通る
    fine = ["0000-0430 3 就寝 自宅", "0430-0500 2 支度 駅", "0500-2400 2 勤務 職場"]
    assert rx.fullmatch(day(fine)) is not None
    # 端点は文法で固定(0000 始まり・2400 終わり)
    assert rx.fullmatch(day(["0030-0800 3 就寝 自宅", "0800-1800 2 勤務 職場",
                             "1800-2400 4 移動 駅"])) is None
    assert rx.fullmatch(day(["0000-0800 3 就寝 自宅", "0800-1800 2 勤務 職場",
                             "1800-2300 4 移動 駅"])) is None


def test_mock_block_text_matches_its_own_regex(trial_world, anchor: dict):
    """モック応答は自分の文法を満たす(= 文法が満たせる形であることの存在証明)。"""
    spec, f, t, _ = _p2_spec_and_facts(trial_world, anchor)
    rows = T.sample_rows(f, {0: 8})
    t = T.draw_windows(f, anchor, rows=rows)
    for r in rows:
        i = int(r)
        rx = re.compile(T.block_regex(spec, f, t, i).replace("\\n", "\n"))
        assert rx.fullmatch(T.mock_text(spec, f, t, i)) is not None, i


def test_current_format_regex_line_bounds_per_arm(trial_world, anchor: dict):
    """P1a は本番どおり ``{4,5}``・P1b は ``{3,10}``(文法を緩めた腕だけ活動数が動く)。"""
    f = _facts(trial_world)
    rows = T.sample_rows(f, {0: 2})
    t = T.draw_windows(f, anchor, rows=rows)
    i = int(rows[0])
    assert "{4,5}" in T.arm_regex(T.ARMS["p1a"], f, t, i)
    assert "{3,10}" in T.arm_regex(T.ARMS["p1b"], f, t, i)
    assert T.arm_regex(T.ARMS["p0b"], f, t, i) == W17.prompt_regex(f, i)


# ---------------------------------------------------------------- P2′(p2p)
def test_p2p_grammar_has_no_block_kind_and_uses_the_current_parser(trial_world, anchor: dict):
    """P2′: 行は現行 W17 と同じ 3 列・区分の列は文法にも例示にも無い・パーサは ``V.parse_text``。"""
    spec = T.ARMS["p2p"]
    assert spec.kind_col is False and spec.block is True and spec.stage == 2
    f = _facts(trial_world)
    rows = T.sample_rows(f, {0: 6})
    t = T.draw_windows(f, anchor, rows=rows)
    i = int(rows[0])
    rx = re.compile(T.block_regex(spec, f, t, i).replace("\\n", "\n"))

    def day(lines: list[str]) -> str:
        return "\n".join(f"d{d}\n" + "\n".join(lines) for d in range(V.N_DAYS))

    ok = ["0000-0807 就寝 自宅", "0807-1738 勤務 職場", "1738-2400 移動 駅"]
    assert rx.fullmatch(day(ok)) is not None
    # 区分の列を書いた行は**文法から外れている**
    assert rx.fullmatch(day(["0000-0807 3 就寝 自宅", "0807-1738 2 勤務 職場",
                             "1738-2400 4 移動 駅"])) is None
    # 残した制約: {3,10} 行・0000/2400 の端点・深夜の 支度/乗車 禁止
    assert rx.fullmatch(day(ok[:2])) is None
    assert rx.fullmatch(day(["0030-0807 就寝 自宅", "0807-1738 勤務 職場",
                             "1738-2400 移動 駅"])) is None
    assert rx.fullmatch(day(["0000-0807 就寝 自宅", "0807-1738 勤務 職場",
                             "1738-2300 移動 駅"])) is None
    for act in T.NIGHT_BAN_ACTS:
        assert rx.fullmatch(day(["0000-0230 就寝 自宅", f"0230-0300 {act} 駅",
                                 "0300-2400 勤務 職場"])) is None, act
    # system と例示にも区分が無い(P2 には有る=P2 は不変)
    sys_p2p = T.arm_system(spec, f, t, i)
    assert "区分" not in sys_p2p and "0000-0652 就寝 自宅" in sys_p2p
    assert "区分" in T.arm_system(T.ARMS["p2"], f, t, i)
    # モックは自分の文法を満たし、**現行パーサ**でそのまま読める
    for r in rows:
        j = int(r)
        text = T.mock_text(spec, f, t, j)
        rxj = re.compile(T.block_regex(spec, f, t, j).replace("\\n", "\n"))
        assert rxj.fullmatch(text) is not None, j
        acts, bad = V.parse_text(text)
        assert acts and not [k for k in bad if k in V.FAILURE_REASONS]
    # 区分はエンジンが導く(矛盾を作らない)
    blocks, _ = T._to_blocks(spec, T.mock_text(spec, f, t, i), int(f.home_cell[i]) >= 0)
    for b in blocks:
        assert T.block_kind_conflict(b.block_kind, b.activity, b.place,
                                     int(f.home_cell[i]) >= 0) == ""


def test_p2p_max_tokens_is_1536_and_p2_stays_1024(trial_world, anchor: dict):
    """P2′ の生成上限は 1,536(P2 の 1,024 で 65% が切断)。P2 は不変。"""
    assert T.ARMS["p2p"].max_tokens == T.BLOCK_MAX_TOKENS_P2P == 1_536
    assert T.ARMS["p2"].max_tokens == T.BLOCK_MAX_TOKENS == 1_024
    f = _facts(trial_world)
    rows = T.sample_rows(f, {0: 3})
    t = T.draw_windows(f, anchor, rows=rows)
    p = T.arm_prompt_of(T.ARMS["p2p"], f, t, int(rows[0]))
    assert p.to_json()["max_tokens"] == 1_536
    assert T.arm_prompt_of(T.ARMS["p2"], f, t, int(rows[0])).to_json()["max_tokens"] == 1_024


def test_p2p_states_time_fidelity_in_system_and_user(trial_world, anchor: dict):
    """P2′ の system と user の**両方**に時刻の忠実さの指示が入る(P2 には入らない)。"""
    f = _facts(trial_world)
    rows = T.sample_rows(f, {0: N_BODIES})
    t = T.draw_windows(f, anchor, rows=rows)
    i = [int(r) for r in rows if int(t.duty_open[int(r)]) >= 0][0]
    for part in ("事実行の出勤時刻・帰宅時刻は分までそのまま使う",
                 "家を出る移動の行の開始=出勤時刻", "帰宅の移動の行の終了=帰宅時刻",
                 "00 分・30 分に丸めない"):
        assert part in T.TIME_FIDELITY_LINE, part
    sys_p2p = T.arm_system(T.ARMS["p2p"], f, t, i)
    user_p2p = T.arm_user(T.ARMS["p2p"], f, t, i, identity="きょうも同じ流れです。")
    assert T.TIME_FIDELITY_LINE in sys_p2p
    assert T.TIME_FIDELITY_LINE in user_p2p
    assert T.TIME_FIDELITY_LINE not in T.arm_system(T.ARMS["p2"], f, t, i)
    assert T.TIME_FIDELITY_LINE not in T.arm_user(T.ARMS["p2"], f, t, i, identity="同じ流れです。")
    # 事実行の出勤/帰宅は分単位のまま載っている(丸めない指示の対象)
    assert f"出勤: {W17._hm(int(t.depart[i]))}" in user_p2p
    # 段1 は P2 と同一= p2 の段1 応答をそのまま再利用できる
    st1 = T.ARMS["p2"].__class__(**{**T.ARMS["p2"].__dict__, "stage": 1})
    st1p = T.ARMS["p2p"].__class__(**{**T.ARMS["p2p"].__dict__, "stage": 1})
    assert T.arm_system(st1, f, t, i) == T.arm_system(st1p, f, t, i)


# ---------------------------------------------------------------- 本番 W17 v2(1 日)
def _prod(trial_world, anchor, *, days: int = 1):
    f = _facts(trial_world)
    rows = T.production_rows(f)
    t = T.draw_windows(f, anchor, rows=rows)
    return T.production_spec(days=days), f, t, rows


def test_v2_one_day_grammar_and_max_tokens(trial_world, anchor: dict):
    """1 日モード: 文法・例示・指示が d0 だけ・``max_tokens`` は 320(切断 0 を保つ)。"""
    spec, f, t, rows = _prod(trial_world, anchor)
    assert (spec.days, spec.kind_col, spec.stage) == (1, False, 2)
    assert spec.max_tokens == T.BLOCK_MAX_TOKENS_P2P_1DAY == 320
    sys1 = T.arm_system(spec, f, t, 0)
    for token in ("d1", "d6", "1週間"):
        assert token not in sys1, token
    for token in ("d0", "月曜日1日", "就寝", "0時台から3時台", T.TIME_FIDELITY_LINE):
        assert token in sys1, token
    assert "月曜日1日" in T.arm_user(spec, f, t, 0, identity="いつもどおりです。")
    rx = re.compile(T.block_regex(spec, f, t, 0).replace("\\n", "\n"))
    ok = ["0000-0807 就寝 自宅", "0807-1738 勤務 職場", "1738-2400 移動 駅"]
    assert rx.fullmatch("d0\n" + "\n".join(ok)) is not None
    assert rx.fullmatch("d0\n" + "\n".join(ok) + "\nd1\n" + "\n".join(ok)) is None  # 2 日は不可
    assert rx.fullmatch(day_block := "d0\n0000-0230 就寝 自宅\n0230-0300 支度 自宅\n"
                        "0300-2400 勤務 職場") is None and day_block  # 深夜禁止は据置
    assert rx.fullmatch("d0\n" + "\n".join(ok[:2])) is None                         # {3,10}
    # モックも 1 日だけ・自分の文法を満たす
    text = T.mock_text(spec, f, t, 0)
    assert text.count("d0") == 1 and "d1" not in text
    assert rx.fullmatch(text) is not None


def test_v2_production_writes_one_row_per_agent_with_safe_names(trial_world, anchor: dict,
                                                                tmp_path: Path):
    """本番は**層化なし・行数=体数**・名前は本番 glob に当たらない・隔離先が強制される。"""
    world, _ = trial_world
    spec, f, t, rows = _prod(trial_world, anchor)
    assert rows.size == f.n and np.array_equal(rows, np.arange(f.n))
    out = tmp_path / "w17v2"
    r1 = T.write_production_prompts(out, spec, f, t, rows, stage=1)
    ids = {str(int(a)): "いつもどおりの一日です。" * 5 for a in f.agent_id}
    r2 = T.write_production_prompts(out, spec, f, t, rows, stage=2, identities=ids)
    assert r1["rows"] == r2["rows"] == f.n
    assert (r1["name"], r2["name"]) == (T.V2_STAGE1_PROMPTS, T.V2_STAGE2_PROMPTS)
    assert r2["n_identity_injected"] == f.n and r1["max_tokens"] == T.IDENTITY_MAX_TOKENS
    assert T.files_avoid_production_globs([p.name for p in out.rglob("*")]) == []
    assert r1["prompts_sha256"] != r2["prompts_sha256"]
    # 1 行の形は本番 fleet_gen と同じ(id/system/user/max_tokens/temperature/seed/repeat)
    row = json.loads(open(out / T.V2_STAGE2_PROMPTS, encoding="utf-8").readline())
    assert set(row) >= {"id", "system", "user", "max_tokens", "temperature", "seed",
                        "repeat", "thinking", "regex"}
    assert row["max_tokens"] == 320
    # 隔離の強制: 出力先が world_dir と同じなら拒否
    with pytest.raises(RuntimeError):
        T.assert_isolated(world, world)
    assert T.assert_isolated(out, world) == out.resolve()


def test_v2_ingest_adopts_raking_zero_and_reports_twelve(trial_world, anchor: dict,
                                                         tmp_path: Path):
    """raking は 12% と 0% の両方を計算し、**採用は 0%**(エンジン由来の修正 0)。"""
    world, _ = trial_world
    spec, f, t, rows = _prod(trial_world, anchor)
    out = tmp_path / "w17v2"
    resp = T.write_mock_responses(out, spec, f, t, rows)
    rep, cols = T.ingest_production(world, spec, f, t, rows, [resp])
    body = rep.to_json()
    assert set(body["raking"]) == {"0.12", "0.00", "adopted"}
    assert body["raking"]["adopted"] == "0.00"
    assert body["raking"]["0.00"]["n_moved"] == 0
    assert body["modified"]["engine"]["rate"] == 0.0
    # 採用が 0% = parquet の開始分は raking 前と同じ(12% の結果を書き込んでいない)
    assert cols["day"].max() == 0 and cols["day"].min() == 0       # 1 日だけ
    assert cols["agent_id"].size == rep.n_kept
    assert body["diversity"]["M4a_acts_per_agent_day"]["n"] == f.n
    assert "M6" in body["diversity"] and "測れない" in body["diversity"]["M6"]
    # header / gates / parquet を隔離先へ
    res = T.write_production(out, Path(world), Path(trial_world[1]), spec, f, rep, cols,
                             [], [resp], time_fact_repair=False)
    assert res.stage_version == "2.0.0"
    assert (out / "w17_schedule.parquet").exists() and (out / "W17.header.json").exists()
    assert (out / "w17_gates.json").exists()
    assert not (Path(world) / "w17v2_stage1_prompts.jsonl").exists()
    names = {g.name for g in res.gates}
    assert {"parse_fail_rate", "coverage_ge_0999_rate", "M3b_depart_proxy",
            "M4a_acts_per_agent_day", "jsd_max_raking_0", "jsd_max_raking_12",
            "M6_measurable"} <= names
    import pyarrow.parquet as pq

    assert pq.read_table(out / "w17_schedule.parquet").schema.names == list(T.PROD_SCHEMA.names)


def test_v2_time_fact_repair_switch(trial_world, anchor: dict, tmp_path: Path):
    """``--time-fact-repair``: 既定オフは**一致率を数えるだけ**・オンで行を動かして計数。"""
    world, _ = trial_world
    spec, f, t, rows = _prod(trial_world, anchor)
    out = tmp_path / "w17v2"
    # モックは移動行を窓(始業/終業)に合わせるので、出勤/帰宅の**時刻そのもの**とはずれる
    resp = T.write_mock_responses(out, spec, f, t, rows)
    off, _ = T.ingest_production(world, spec, f, t, rows, [resp], time_fact_repair=False)
    on, cols_on = T.ingest_production(world, spec, f, t, rows, [resp], time_fact_repair=True)
    a, b = off.to_json()["time_fact"], on.to_json()["time_fact"]
    assert a["time_fact_depart_rows"] > 0 and a["time_fact_depart_rows"] == b["time_fact_depart_rows"]
    assert "time_fact_moved_rows" not in a          # オフでは 1 行も動かさない
    assert b["time_fact_moved_rows"] > 0            # オンでは動かす
    assert a["dev_min"]["n"] > 0 and a["depart_match_rate"] < 1.0
    assert b["dev_min"]["mean"] > 0
    # オンにしても被覆は落ちない(端を一緒に動かして切れ目を作らない)
    assert on.to_json()["checks"]["coverage_mean"] == 1.0


def test_v2_promote_backs_up_the_old_assets(tmp_path: Path):
    """``--promote``: 旧版を ``w17v1_backup/`` へ退避してからコピーする。"""
    world = tmp_path / "world"
    src = world / T.V2_DIR
    src.mkdir(parents=True)
    (world / "w17_schedule.parquet").write_bytes(b"OLD-parquet")
    (world / "W17.header.json").write_bytes(b'{"stage_version": "1.2.0"}')
    (src / "w17_schedule.parquet").write_bytes(b"NEW-parquet")
    (src / "W17.header.json").write_bytes(b'{"stage_version": "2.0.0"}')
    (src / "w17_gates.json").write_bytes(b"{}")
    rec = T.promote(src, world)
    assert set(rec["promoted"]) == {"w17_schedule.parquet", "W17.header.json", "w17_gates.json"}
    assert set(rec["backed_up"]) == {"w17_schedule.parquet", "W17.header.json"}
    backup = world / T.V2_BACKUP_DIR
    assert (backup / "w17_schedule.parquet").read_bytes() == b"OLD-parquet"
    assert (world / "w17_schedule.parquet").read_bytes() == b"NEW-parquet"
    assert b"2.0.0" in (world / "W17.header.json").read_bytes()


def test_v2_gate_thresholds_and_one_day_notes(trial_world, anchor: dict, tmp_path: Path):
    """v2 のゲート: parse 失敗 <0.02・被覆 ≥0.999 は合否・多様性と JSD は報告のみ。"""
    world, _ = trial_world
    spec, f, t, rows = _prod(trial_world, anchor)
    out = tmp_path / "w17v2"
    resp = T.write_mock_responses(out, spec, f, t, rows)
    rep, cols = T.ingest_production(world, spec, f, t, rows, [resp])
    res = T.write_production(out, Path(world), Path(trial_world[1]), spec, f, rep, cols,
                             [], [resp], time_fact_repair=False)
    g = {x.name: x.to_json() for x in res.gates}
    assert (T.V2_GATE_PARSE_FAIL, T.V2_GATE_COVERAGE) == (0.02, 0.999)
    assert g["parse_fail_rate"]["expected"] == "< 0.02" and g["parse_fail_rate"]["pass"]
    assert g["coverage_ge_0999_rate"]["expected"] == ">= 0.999" and g["coverage_ge_0999_rate"]["pass"]
    for report_only in ("M3b_depart_proxy", "M4a_acts_per_agent_day", "jsd_max_raking_0",
                        "jsd_max_raking_12", "llm_modified_rate", "has_sleep_rate",
                        "night_violation_day_rate"):
        assert g[report_only]["expected"] is None, report_only
        assert g[report_only]["pass"] is True
    assert g["M6_measurable"]["value"] is False  # 1 日なので測れない
    assert res.all_passed
    assert any("1 日モード" in e for e in res.expedients)
    assert any("採用は 0%" in e for e in res.expedients)


# ================================================================= 5. ブロック形式パーサ
def test_parse_blocks_finds_gap_sleep_and_kind_conflict():
    """パーサ: 切れ目・就寝・``block_kind`` の矛盾を拾う(壊れた行はその行だけ捨てる)。"""
    text = "\n".join((
        "d0",
        "0000-0700 3 就寝 自宅",
        "0800-1800 2 勤務 職場",     # 0700-0800 が切れ目
        "1800-2400 1 休憩 自宅",
        "これは表ではない",
    ))
    blocks, bad = T.parse_blocks(text)
    assert [b.block_kind for b in blocks] == [3, 2, 1]
    assert bad == {"format": 1}
    assert blocks[0].activity == V.ACT_SLEEP
    # 切れ目の検出(隣接の end != 次の start)
    gaps = sum(1 for a, b in zip(blocks, blocks[1:]) if a.end != b.start)
    assert gaps == 1
    # 日をまたぐ行は 2 件に割る(V.parse_line と同規約)
    over, _ = T.parse_blocks("d6\n2300-0700 3 就寝 自宅")
    assert [(b.day, b.start, b.end) for b in over] == [(6, 1380, 1440), (0, 0, 420)]
    # 同義語表で直した印は失敗率に数えない
    fixed, bad2 = T.parse_blocks("d0\n0000-0700 3 睡眠 家")
    assert len(fixed) == 1 and bad2 == {"fix_activity": 1, "fix_place": 1}


def test_block_kind_conflicts_and_derivation():
    """``block_kind`` と 活動語/場所語 の矛盾検出・現行形式からの派生写像。"""
    assert T.block_kind_conflict(T.BK_SLEEP, V.ACT_SLEEP, V.PLACE_HOME, True) == ""
    assert T.block_kind_conflict(T.BK_HOME, V.ACT_SLEEP, V.PLACE_HOME, True) == "sleep_kind"
    assert T.block_kind_conflict(T.BK_INAREA, V.ACT_MOVE, V.PLACE_STATION, True) == "move_kind"
    assert T.block_kind_conflict(T.BK_HOME, V.ACT_REST, V.PLACE_HOME, False) == "home_kind"
    assert T.block_kind_conflict(T.BK_INAREA, V.ACT_REST, V.PLACE_OUTSIDE, True) == "inarea_kind"
    # 域外居住者の自宅は block_kind=0(計画実行層設計書 §9 制約④)
    assert T.block_kind_conflict(T.BK_OUTSIDE, V.ACT_REST, V.PLACE_HOME, False) == ""
    assert T.block_kind_conflict(T.BK_INAREA, V.ACT_REST, V.PLACE_HOME, False) == "home_outside"
    # 派生写像は矛盾を作らない
    for act in range(len(V.ACTIVITY_WORDS)):
        for place in range(len(V.PLACE_WORDS)):
            for home_in in (True, False):
                bk = T.derive_block_kind(act, place, home_in)
                assert T.block_kind_conflict(bk, act, place, home_in) == ""


# ================================================================= 6. 腕と prompts_sha
def test_prompts_sha_differs_per_arm_and_reproduces(trial_world, anchor: dict):
    """腕ごとに ``prompts_sha256`` が違い、同じ腕は 2 回で一致する(改版の検出器)。"""
    f = _facts(trial_world)
    rows = T.sample_rows(f, {0: 8})
    t = T.draw_windows(f, anchor, rows=rows)
    sha: dict[str, str] = {}
    for name in ("p0b", "p1a", "p1b", "p2"):
        spec = T.ARMS[name]
        a = W17.prompts_sha256(T.arm_prompts(spec, f, t, rows))
        b = W17.prompts_sha256(T.arm_prompts(spec, f, t, rows))
        assert a == b, name
        sha[name] = a
    assert len(set(sha.values())) == 4
    # P2-32B は P2 と**同じ文面・同じ seed**(モデルだけ替える=--model-tag)
    sub = T.sample_rows(f, {0: 8}, total=4)
    p2 = {p.id: p for p in T.arm_prompts(T.ARMS["p2"], f, t, rows)}
    for p in T.arm_prompts(T.ARMS["p2_32b"], f, t, sub):
        assert p.to_json() == p2[p.id].to_json()
    # P0b は本番と**同一の文面**・seed だけ違う(§1 フロアの定義)
    i = int(rows[0])
    p0b = T.arm_prompt_of(T.ARMS["p0b"], f, t, i)
    assert p0b.system == W17.system_prompt(int(f.kind[i]))
    assert p0b.user == W17.user_prompt(f, i)
    assert p0b.seed != W17.agent_seed(int(f.agent_id[i]))


def test_p1_system_changes_only_fewshot_times_and_line_rule(trial_world, anchor: dict):
    """P1 の system は本番テンプレから**例示の時刻と行数規則だけ**が違う。"""
    f = _facts(trial_world)
    rows = T.sample_rows(f, {0: 2})
    t = T.draw_windows(f, anchor, rows=rows)
    i = int(rows[0])
    base = W17.system_prompt(int(f.kind[i]))
    p1a = T.arm_system(T.ARMS["p1a"], f, t, i)
    assert p1a != base
    restored = p1a
    for old, new in zip(T._FEWSHOT_ROUND, T._FEWSHOT_ODD):
        restored = restored.replace(new, old)
    assert restored == base  # P1a は行数規則を変えていない
    # 例示の時刻は :00 で終わらない(これ自体が :00 80% を教えないため)
    for line in T._FEWSHOT_ODD:
        a, _, b = line.split(" ")[0].partition("-")
        assert not (a.endswith("00") and b.endswith("00"))
    p1b = T.arm_system(T.ARMS["p1b"], f, t, i)
    assert "3行から10行" in p1b and "4行から5行" in p1a


def test_p1_user_adds_employment_and_own_times(trial_world, anchor: dict):
    """P1 の事実行に雇用形態と自分の出勤/帰宅 HH:MM(分単位)が載る(§1)。"""
    f = _facts(trial_world)
    rows = T.sample_rows(f, {0: N_BODIES})
    t = T.draw_windows(f, anchor, rows=rows)
    drawn = [int(r) for r in rows if int(t.duty_open[int(r)]) >= 0]
    assert drawn
    i = drawn[0]
    user = T.arm_user(T.ARMS["p1a"], f, t, i)
    assert "雇用形態: " in user
    assert f"出勤: {W17._hm(int(t.depart[i]))}" in user
    assert f"帰宅: {W17._hm(int(t.arrive[i]))}" in user
    assert W17._hm(int(t.duty_open[i])) in user and W17._hm(int(t.duty_close[i])) in user
    # 分単位= 丸めていない体が実際にいる
    assert any(int(t.depart[int(r)]) % 15 != 0 for r in rows if int(t.depart[int(r)]) >= 0)
    # P2 段1 は面接形式(名前+質問 3 つ・性格や好みは聞かない)
    q = T.arm_user(T.ARMS["p2"].__class__(**{**T.ARMS["p2"].__dict__, "stage": 1}), f, t, i)
    assert "名前: " in q
    for question in T.IDENTITY_QUESTIONS:
        assert question in q
    for banned in ("性格", "価値観", "趣味", "好み"):
        assert banned not in q


# ================================================================= 7. ファイル名(§7 リスク 8)
def test_output_names_avoid_production_globs(trial_world, anchor: dict, tmp_path: Path):
    """下見の出力名が本番 glob(``w17_responses*`` / ``w17_prompts*``)に**当たらない**。"""
    f = _facts(trial_world)
    rows = T.sample_rows(f, {0: 4})
    t = T.draw_windows(f, anchor, rows=rows)
    out = tmp_path / "trials"
    names: list[str] = []
    for name in ("p0b", "p1a", "p1b", "p2"):
        spec = T.ARMS[name]
        rec = T.write_arm_prompts(out, spec, f, t, rows)
        names.append(rec["name"])
        names.append(T.write_mock_responses(out, spec, f, t, rows).name)
        names.append(T.trial_file(name, "schedule.parquet"))
        names.append(T.trial_file(name, "report.json"))
    names.append(T.trial_file("p2", "prompts.jsonl", stage=2))
    assert T.files_avoid_production_globs(names) == []
    # 実際にディスクへ出た全ファイルも検査する
    on_disk = [p.name for p in out.rglob("*") if p.is_file()]
    assert on_disk
    assert T.files_avoid_production_globs(on_disk) == []
    # 逆側(検査器が本当に当たりを見つける)
    assert T.files_avoid_production_globs(
        ["w17_responses.0of8.jsonl", "w17_prompts.jsonl", "w17_schedule.parquet"]
    ) == ["w17_responses.0of8.jsonl", "w17_prompts.jsonl", "w17_schedule.parquet"]


# ================================================================= 8. 取り込みと報告
def test_report_splits_modified_rate_by_origin(trial_world, anchor: dict, tmp_path: Path):
    """決定項 10: 修正率を **LLM 由来**(パース失敗・検査落ち)と**エンジン由来**に分ける。"""
    world, _ = trial_world
    f = _facts(trial_world)
    rows = T.sample_rows(f, {0: 12})
    t = T.draw_windows(f, anchor, rows=rows)
    out = tmp_path / "trials"
    spec = T.ARMS["p1b"]
    resp = T.write_mock_responses(out, spec, f, t, rows)
    # 1 体だけ壊した応答を足す(パース失敗と深夜違反を作る)
    broken = out / spec.name / "broken.jsonl"
    aid = str(int(f.agent_id[int(rows[0])]))
    text = "d0\n0230-0300 支度 自宅\n0300-0800 就寝 自宅\nこれは行ではない\n" + \
        "\n".join(f"d{d}\n0000-0700 就寝 自宅\n0700-0800 支度 自宅\n"
                  f"0800-1800 勤務 職場\n1800-1900 食事 飲食店" for d in range(1, 7))
    broken.write_text(json.dumps({"id": aid, "text": text, "completion_tokens": 300},
                                 ensure_ascii=False) + "\n", encoding="utf-8")
    rep = T.ingest_arm(world, out, spec, f, t, rows, [resp, broken])
    body = rep.to_json()
    llm, engine = body["modified"]["llm"], body["modified"]["engine"]
    assert llm["n_parse_failed"] == 1          # 「これは行ではない」
    assert llm["n_check_failed"] >= 1          # 0230 の 支度
    assert body["checks"]["night_violations"] >= 1
    assert 0.0 < llm["rate"] < 1.0
    assert engine["repair_n_modified"] == 0    # 下見は修復しない
    assert engine["rake_n_moved"] >= 0
    assert llm["rate"] != engine["rate"] or llm["n_check_failed"] == engine["rake_n_moved"]
    # 決定項 9: raking は 12% と 0% の両方
    assert set(body["raking"]) == {"0.12", "0.00"}
    assert body["raking"]["0.00"]["n_moved"] == 0
    assert body["raking"]["0.00"]["jsd_before"] == body["raking"]["0.00"]["jsd_after"]
    # 報告の全欄が出る
    for key in ("parse", "checks", "modified", "raking", "completion_tokens",
                "window_counters", "outputs", "inputs"):
        assert key in body, key
    for key in ("coverage_mean", "has_sleep_rate", "lines_per_day", "duty_window_dev_min",
                "block_kind_conflicts", "night_violation_rate"):
        assert key in body["checks"], key


def test_p0b_also_reports_a_repaired_variant(trial_world, anchor: dict, tmp_path: Path):
    """P0b だけは本番の ``repair`` を通した版も出す(= 前値と同じ土俵)。"""
    world, _ = trial_world
    f = _facts(trial_world)
    rows = T.sample_rows(f, {0: 8})
    t = T.draw_windows(f, anchor, rows=rows)
    out = tmp_path / "trials"
    spec = T.ARMS["p0b"]
    resp = T.write_mock_responses(out, spec, f, t, rows)
    rep = T.ingest_arm(world, out, spec, f, t, rows, [resp])
    body = rep.to_json()
    assert "repair_rules" in body["modified"]["engine"]
    names = [o["name"] for o in body["outputs"]]
    assert T.trial_file("p0b", "schedule.parquet") in names
    assert T.trial_file("p0b", "repaired_schedule.parquet") in names
    assert T.files_avoid_production_globs(names) == []


def test_trial_parquet_has_weekly_columns_plus_block_kind(trial_world, anchor: dict,
                                                          tmp_path: Path):
    """下見 parquet は ``agents.weekly._COLUMNS`` をそのまま含み(物差しが読める)+``block_kind``/``arm``。"""
    import pyarrow.parquet as pq

    from shibuya.agents.weekly import _COLUMNS

    world, _ = trial_world
    f = _facts(trial_world)
    rows = T.sample_rows(f, {0: 6})
    t = T.draw_windows(f, anchor, rows=rows)
    out = tmp_path / "trials"
    spec = T.ARMS["p2"]
    resp = T.write_mock_responses(out, spec, f, t, rows)
    T.ingest_arm(world, out, spec, f, t, rows, [resp])
    path = out / spec.name / T.trial_file("p2", "schedule.parquet")
    table = pq.read_table(path)
    assert set(_COLUMNS) <= set(table.schema.names)
    assert {"block_kind", "arm"} <= set(table.schema.names)
    assert table.schema.names == list(T.TRIAL_SCHEMA.names)
    aid = np.asarray(table.column("agent_id").to_numpy(zero_copy_only=False), dtype=np.int64)
    day = np.asarray(table.column("day").to_numpy(zero_copy_only=False), dtype=np.int64)
    # ``load_weekly`` が要求する (agent_id, day) 昇順
    assert not np.any((aid[1:] < aid[:-1]) | ((aid[1:] == aid[:-1]) & (day[1:] < day[:-1])))
    assert set(table.column("arm").to_pylist()) == {"p2"}


# ================================================================= 9. 段1 の検査(§3)
def test_identity_check_catches_the_four_bans():
    """段1: 字数 200〜420 と禁止 4 つ(固有名詞・数字・箇条書き・挨拶の定型)。"""
    good = "あ" * 250
    assert T.check_identity(good, "事実行") == []
    assert "chars" in T.check_identity("あ" * 10, "事実行")
    assert "chars" in T.check_identity("あ" * 500, "事実行")
    assert "proper_noun" in T.check_identity(good + "スターバックス", "事実行")
    assert "proper_noun" not in T.check_identity(good + "スターバックス", "スターバックス")
    assert "number" in T.check_identity(good + "7時に出ます", "事実行")
    assert "number" not in T.check_identity(good + "7時に出ます", "出勤: 7時")
    assert "bullet" in T.check_identity(good + "\n- ひとつ", "事実行")
    assert "greeting" in T.check_identity("こんにちは。" + good, "事実行")


def test_identity_char_floor_is_80(tmp_path: Path):
    """親判断(2026-09-11): 字数下限は**80 字**(失敗を弾く目的)・上限 420 は据置。"""
    assert (T.IDENTITY_CHARS_MIN, T.IDENTITY_CHARS_MAX) == (80, 420)
    assert "chars" in T.check_identity("あ" * 79, "事実行")
    assert T.check_identity("あ" * 80, "事実行") == []
    assert T.check_identity("あ" * 420, "事実行") == []
    assert "chars" in T.check_identity("あ" * 421, "事実行")
    # ``_load_identities`` は**事実行の要らない検査だけ**を掛ける(固有名詞・数字は段1 report 側)
    assert T.IDENTITY_FACTFREE_REASONS == {"chars", "bullet", "greeting"}
    path = tmp_path / "stage1.jsonl"
    rows = [("1", "あ" * 80), ("2", "あ" * 79), ("3", "あ" * 200 + "スターバックスで7時"),
            ("4", "あ" * 200 + "\n- 箇条書き"), ("5", "こんにちは。" + "あ" * 200)]
    path.write_text("\n".join(
        json.dumps({"id": i, "text": t}, ensure_ascii=False) for i, t in rows
    ) + "\n", encoding="utf-8")
    got = T._load_identities(path)
    assert got["1"] and not got["2"]          # 80 字は通る・79 字は空
    assert got["3"]                           # 固有名詞・数字はここでは弾かない
    assert not got["4"] and not got["5"]      # 箇条書き・挨拶は弾く


# ================================================================= 10. 本番の不変
def test_production_prompt_does_not_read_trial_only_fields(world_dir: Path, data_dir: Path):
    """``pool_facts`` に足した下見専用欄を**本番 W17 の user プロンプトは読まない**。"""
    assert set(PF.TRIAL_ONLY_FIELDS) <= set(PF._STR_FIELDS)
    f = W17.build_facts(world_dir, data_dir)
    # 下見専用欄の値を書き換えても本番プロンプトのバイトは変わらない
    before = W17.prompts_sha256(W17.build_prompts(world_dir, data_dir, facts=f))
    for name in PF.TRIAL_ONLY_FIELDS:
        f.pool.text[name] = ["書き換えた" for _ in f.pool.text[name]]
    f.pool.arrival_lead_min[:] = 999
    after = W17.prompts_sha256(W17.build_prompts(world_dir, data_dir, facts=f))
    assert before == after
    # 本番のパイロット名も下見の glob 検査に載せてある
    assert T.files_avoid_production_globs([W17.PILOT_PROMPTS_NAME]) == [W17.PILOT_PROMPTS_NAME]
