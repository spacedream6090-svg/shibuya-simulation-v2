"""第 6 期 6-3 時計の段 T2: 会話の時計(``engine.speech_clock``・腕 ``--talk-clock mora``)の試験。

- モーラ数の規則(例文で既知の数)・言語の判定(英語などは欄だけ)。
- 話す速さの分布(R-111 §3 の錨=平均 6.62 モーラ/秒・話者の範囲 5.05〜8.06・決定的=同じ鍵で同じ値・d2(18)=3.640)。
- 揺れの CV(0.42)・相手による差(知らない相手 +9.6%)。
- 考える時間を二重に数えない(負の対照=TM2 の L4 を足した形と違う)。
- 会話の中は時刻順で持ち越す(窓の待ち行列で次の番を処理の中で作る形)・負の対照(同じ会話を 1 つの束にまとめると止まる)。
- 違う会話どうしはバッチ(同じ時刻の発言は 1 つの束)・上限の安全装置が記録を残す・C1 の口の形。
- 腕 mora は世界を変えない(final・呼数・checkpoint が既定と同じ)・設定の指紋・2 日と再開・manifest の節。
- 世界資産 5,000 体 1 日(slow): 会話の長さの分布が出る(既定の表との差=記録 tm234/README.md §T2)。
"""

from __future__ import annotations

import ast
import contextlib
import math
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from shibuya import cli
from shibuya.core.time_consts import NS_PER_SECOND, STEP_SECONDS, STEPS_PER_DAY
from shibuya.engine import batching as BA
from shibuya.engine import manifest_sections as MS
from shibuya.engine import resume as RS
from shibuya.engine import speech_clock as TC
from shibuya.engine.llm_bridge import LANE_SECONDS
from shibuya.engine.speech.port import mora_count

ROOT = Path(__file__).resolve().parents[3]
real_data = pytest.mark.requires_data("world_v2:w17_schedule.parquet")
WORLD = dict(seed=1, world_dir="data/world/v2")


@contextlib.contextmanager
def talk(name: str):
    prev = TC.arm()
    TC.set_arm(name)
    try:
        yield
    finally:
        TC.set_arm(prev)


def _session(sid: int, *people: int):
    return SimpleNamespace(session_id=sid, participants=list(people), calls={p: 1 for p in people},
                           opened_tick=0, closed_tick=3)


def _clock_on_queue(width_s: int = STEP_SECONDS, **kw):
    q = BA.WindowQueue(width_s=width_s, start_ns=0)
    c = TC.TalkClock(rate_seed=1, jitter_seed=1, **kw)
    return q, c


# ================================================================= モーラ数の規則・言語
@pytest.mark.parametrize("text,n", [
    ("こんにちは", 5), ("きょう", 2), ("がっこう", 4), ("コーヒー", 4), ("東京", 4), ("それじゃ、また。", 5),
    ("ちょうどいい", 5), ("少し急ごう", 7), ("また後で", 5),
])
def test_mora_rule_known_counts(text, n):
    """本当のモーラ数(読みで数えた数)と規則の出力が合う例。"""
    assert mora_count(text) == n
    assert TC.language_of(text) == TC.LANG_JA


@pytest.mark.parametrize("text,rule,true", [
    ("混んでいるな", 7, 6), ("今日", 4, 2), ("一緒に行こう", 9, 7), ("渋谷駅", 6, 5),
])
def test_mora_rule_known_misses_of_the_kanji_two_mora_approximation(text, rule, true):
    """〔検収 L3〕漢字 1 字 2 拍の近似(1-8b の読みの規則=仮採用 1)が外れる例: 規則の出力と本当の数を分けて固定する
    (読みの辞書に替えるまでの宣言=記録 §12-1 の 1)。"""
    assert mora_count(text) == rule != true


def test_language_of_other_and_none():
    assert TC.language_of("hello world") == TC.LANG_OTHER
    assert TC.language_of("") == TC.LANG_NONE and TC.language_of("、。!") == TC.LANG_NONE


# ================================================================= 話す速さ(R-111 §3 の錨)
def test_anchor_values_are_the_r111_copies():
    """写し検査の形: 錨の値と出典(R-111 §3-2 の表・R-73 §4-2)。"""
    assert (TC.MORA_LEN_MEAN_S, TC.MORA_LEN_FAST_S, TC.MORA_LEN_SLOW_S, TC.N_SPEAKERS) == (0.151, 0.124, 0.198, 18)
    assert round(1 / TC.MORA_LEN_MEAN_S, 2) == 6.62 and round(1 / TC.MORA_LEN_FAST_S, 2) == 8.06
    assert round(1 / TC.MORA_LEN_SLOW_S, 2) == 5.05
    assert (TC.WITHIN_CV, TC.WITHIN_CV_PHRASE) == (0.42, 0.28)
    assert TC.FAMILIAR_FASTER == (0.109, 0.083)
    assert round(214 / 193 - 1, 3) == 0.109 and round(247 / 228 - 1, 3) == 0.083  # Yuan 2006 表 2 の再計算
    assert (TC.GAP_MEAN_MS, TC.GAP_MEDIAN_MS, TC.GAP_NS) == (7, 0, 7_000_000)
    assert TC.SIGMA_BETWEEN == pytest.approx(math.log(0.198 / 0.124) / 3.640)
    assert TC.SIGMA_WITHIN == pytest.approx(math.sqrt(math.log(1 + 0.42 ** 2)))
    assert set(TC.ANCHORS) >= {"mora_len_mean_s", "mora_len_fast_s", "mora_len_slow_s", "within_cv",
                               "familiar_faster", "gap_mean_ms", "d2_n18"}


def test_d2_constant_is_the_expected_range_of_18_normals():
    rng = np.random.default_rng(12345)
    x = rng.standard_normal((40_000, TC.N_SPEAKERS))
    assert float((x.max(axis=1) - x.min(axis=1)).mean()) == pytest.approx(TC.D2_N18, abs=0.02)


def test_person_rate_distribution_mean_range_and_determinism():
    rates = np.array([1.0 / TC.person_mora_len_s(7, a) for a in range(20_000)])
    assert rates.min() >= 1 / TC.MORA_LEN_SLOW_S - 1e-9 and rates.max() <= 1 / TC.MORA_LEN_FAST_S + 1e-9
    assert 6.45 <= rates.mean() <= 6.85  # 平均 6.62 モーラ/秒(切った対数正規の平均は少し上)
    logs = np.log(1.0 / rates)
    assert 0.08 <= logs.std() <= TC.SIGMA_BETWEEN  # 切ったので幅は σ より小さい
    assert TC.person_mora_len_s(7, 123) == TC.person_mora_len_s(7, 123)  # 同じ鍵で同じ値(状態を持たない)
    assert TC.person_mora_len_s(7, 123) != TC.person_mora_len_s(8, 123)  # 母集団の seed で変わる


def test_within_speaker_jitter_has_mean_one_and_cv_042_and_is_keyed_by_the_event():
    j = np.array([TC.utterance_jitter(3, s % 97, s * 1_000_003, s % 13) for s in range(30_000)])
    assert j.mean() == pytest.approx(1.0, abs=0.01)
    assert (j.std() / j.mean()) == pytest.approx(TC.WITHIN_CV, abs=0.02)
    a = TC.utterance_jitter(3, 5, 60 * NS_PER_SECOND, 2)
    assert a == TC.utterance_jitter(3, 5, 60 * NS_PER_SECOND, 2)
    assert a != TC.utterance_jitter(3, 5, 120 * NS_PER_SECOND, 2)  # 時刻(TM7 (d))
    assert a != TC.utterance_jitter(3, 5, 60 * NS_PER_SECOND, 3)  # 会話(中身)


def test_partner_term_familiar_vs_stranger():
    base = TC.SpeechTiming.duration_ns(10, 0.15, 1.0, True)
    assert base == round(10 * 0.15 * NS_PER_SECOND)
    assert TC.SpeechTiming.duration_ns(10, 0.15, 1.0, None) == base  # 欄だけ(関係の層が無い)=倍率 1
    assert TC.SpeechTiming.duration_ns(10, 0.15, 1.0, False) == round(base * (1 + TC.FAMILIAR_DELTA))
    assert TC.FAMILIAR_DELTA == pytest.approx(0.096)


def test_partner_term_reads_the_relation_layer_live_edges():
    rel = SimpleNamespace(acquaintances=lambda agents, a, step: np.array([5], dtype=np.int64))
    q, c = _clock_on_queue(rel_layer=rel)
    c.attach(TC.QueueRouter(q))
    q.register(TC.KIND_TALK, "talk", c.on_dispatch, rank=TC.RANK_TALK)
    c.on_turn(object(), 1, 0, _session(1, 1, 5), "こんにちは")
    c.on_turn(object(), 2, 0, _session(2, 2, 6), "こんにちは")
    m = c._tc_meter
    assert (m["familiar"], m["unfamiliar"], m["familiar_unknown"]) == (1, 1, 0)


# ================================================================= 考える時間を二重に数えない
def test_think_time_is_not_added_to_the_gap():
    q, c = _clock_on_queue()
    c.attach(TC.QueueRouter(q))
    q.register(TC.KIND_TALK, "talk", c.on_dispatch, rank=TC.RANK_TALK)
    c.on_turn(None, 1, 0, _session(9, 1, 2), "こんにちは")
    first, nxt, end = c._tc_line[9][:3]
    assert nxt - end == TC.GAP_NS == 7_000_000
    assert "TM2" in TC.THINK_TIME_COUNTED_BY
    tree = ast.parse((ROOT / "src" / "shibuya" / "engine" / "speech_clock.py").read_text(encoding="utf-8"))
    names = {a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) for a in n.names}
    mods = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    assert "shibuya.engine.llm_bridge" not in mods and "LANE_SECONDS" not in names


def _gap_of_a_new_conversation() -> int:
    q, c = _clock_on_queue()
    c.attach(TC.QueueRouter(q))
    q.register(TC.KIND_TALK, "talk", c.on_dispatch, rank=TC.RANK_TALK)
    c.on_turn(None, 1, 0, _session(9, 1, 2), "こんにちは")
    _first, nxt, end = c._tc_line[9][:3]
    return int(nxt - end)


def test_negative_control_adding_the_think_time_is_caught(monkeypatch):
    """〔検収 L2〕負の対照: 間に TM2 の考える時間(今の表の会話応答 L4 0.2 秒)を足す欠陥を植えると、間の検査が落ちる。"""
    assert _gap_of_a_new_conversation() == TC.GAP_NS
    l4 = int(LANE_SECONDS["L4"] * NS_PER_SECOND)
    monkeypatch.setattr(TC.SpeechTiming, "gap_ns", staticmethod(lambda: TC.GAP_NS + l4))
    got = _gap_of_a_new_conversation()
    assert got == TC.GAP_NS + l4 and got != TC.GAP_NS  # 植えた欠陥を間の検査が捕まえる


# ================================================================= 時刻順・持ち越し・バッチ・上限(窓の待ち行列で)
def _chain_run(width_s: int, turns: int, cap: int = TC.DEFAULT_CAP_PER_WINDOW, n_sessions: int = 2):
    """刻みの事象 1 つで会話 n 本の最初の番を作り、発言の事象を処理する中で同じ会話の次の番を作る(版上げの形)。"""
    q, c = _clock_on_queue(width_s=width_s, cap_per_window=cap)
    c.attach(TC.QueueRouter(q))
    sessions = {s: _session(s, 10 * s, 10 * s + 1) for s in range(1, n_sessions + 1)}
    made: dict[int, int] = {s: 0 for s in sessions}
    order: list[tuple[int, int]] = []

    def on_talk(t_ns, agents, seqs):
        rows = [c._tc_pending[int(x)] for x in seqs.tolist() if int(x) in c._tc_pending]
        c.on_dispatch(t_ns, agents, seqs)
        for row in rows:
            if any(r is row for r in c._tc_pending.values()):
                continue  # 上限で次の窓へ持ち越した発言=まだ処理していない(次の番は作らない)
            sid = int(row[0])
            order.append((int(t_ns), sid))
            if made[sid] < turns:
                made[sid] += 1
                spk = sessions[sid].participants[made[sid] % 2]
                # 次の番は処理した発言の終わりに作る(版上げの形)
                c.on_turn(None, spk, 0, sessions[sid], "こんにちは", made_ns=int(row[2]) + int(row[3]))

    def on_step(t_ns, agents, seqs):
        for sid, sess in sessions.items():
            made[sid] += 1
            c.on_turn(None, sess.participants[0], 0, sess, "こんにちは", made_ns=int(t_ns))

    q.register(BA.KIND_STEP, "step", on_step)
    q.register(TC.KIND_TALK, "talk", on_talk, rank=TC.RANK_TALK)
    q.schedule(0, BA.WORLD, BA.KIND_STEP)
    for _ in range(50):
        if not q.pending:
            break
        q.run_window()
    return c, order


def test_in_window_turns_run_in_time_order_and_carry_to_the_next_window():
    c, order = _chain_run(width_s=STEP_SECONDS, turns=6)
    times = [t for t, _ in order]
    assert times == sorted(times)  # 時刻順に順番に回す
    for sid in (1, 2):
        mine = [t for t, s in order if s == sid]
        assert len(mine) == 6 and all(b > a for a, b in zip(mine, mine[1:]))  # 同じ会話は前の発言の後
        line = c._tc_line[sid]
        assert line[3] == 6  # 6 発言(会話の時計=始まり・次・終わり)
    m = c._tc_meter
    assert m["utterances"] == 12 and m["carried"] == 0 and m["ahead"] == 10 and m["cap_hits"] == 0
    # 幅 1 秒: 発言(約 0.75 秒)の事象は窓をまたぐ=次の窓へ持ち越す(処理の時刻は同じ)
    c1, order1 = _chain_run(width_s=1, turns=6)
    assert order1 == order
    assert c1._tc_meter["utterances"] == 12


def test_different_conversations_are_batched_in_one_dispatch():
    c, order = _chain_run(width_s=STEP_SECONDS, turns=2, n_sessions=3)
    m = c._tc_meter
    assert m["batch_max"] == 3  # 3 本の会話の最初の発言は同じ時刻(刻みの頭)=1 つの束
    assert m["dispatches"] >= 2 and m["batch_sum"] == m["utterances"] == 6
    assert order[:3] == [(0, 1), (0, 2), (0, 3)]  # 束の中は体の番号の順(=会話の順)


def test_negative_control_batching_inside_one_conversation_is_refused():
    """同じ会話の 2 つの番を 1 回で作る(=1 回の LLM に会話をまとめて書かせる形)と止まる(会話が遅れているとき)。"""
    q, c = _clock_on_queue()
    c.attach(TC.QueueRouter(q))
    s = _session(4, 1, 2)

    def on_step(t_ns, agents, seqs):
        if t_ns == 2 * STEP_SECONDS * NS_PER_SECOND:  # 3 回目の刻み: 会話 4 の番を 2 つまとめて作る
            c.on_turn(None, 1, 2, s, "こんにちは")
            c.on_turn(None, 2, 2, s, "こんにちは")
        elif t_ns == 0:
            c.on_turn(None, 1, 0, s, "こんにちは")
        if t_ns < 2 * STEP_SECONDS * NS_PER_SECOND:
            q.schedule(t_ns + STEP_SECONDS * NS_PER_SECOND, BA.WORLD, BA.KIND_STEP)

    q.register(BA.KIND_STEP, "step", on_step)
    q.register(TC.KIND_TALK, "talk", c.on_dispatch, rank=TC.RANK_TALK)
    q.schedule(0, BA.WORLD, BA.KIND_STEP)
    q.run_window()
    q.run_window()
    with pytest.raises(RuntimeError, match="同じ時刻にまとめて作った"):
        q.run_window()


def test_m3_two_turns_of_a_conversation_that_is_not_late_are_refused():
    """〔検収 M3〕遅れていない会話(始まりの刻み)で同じ刻みに 2 番を植えても止まる(持ち越しの有無によらない検査)。"""
    q, c = _clock_on_queue()
    c.attach(TC.QueueRouter(q))
    q.register(TC.KIND_TALK, "talk", c.on_dispatch, rank=TC.RANK_TALK)
    s = _session(5, 1, 2)
    c.on_turn(None, 1, 0, s, "こんにちは")
    assert c._tc_meter["carried"] == 0  # 遅れていない
    with pytest.raises(RuntimeError, match="同じ時刻にまとめて作った"):
        c.on_turn(None, 2, 0, s, "こんにちは")
    # 違う刻み(次の番)なら通る
    assert c.on_turn(None, 2, 1, s, "こんにちは") is not None


def test_the_dispatch_check_also_refuses_one_conversation_in_one_batch():
    """束の検査(規則 7)も残る: 同じ会話の発言を同じ時刻の束に入れると処理で止まる(持ち主の中を白箱で植える)。"""
    q, c = _clock_on_queue()
    router = TC.QueueRouter(q)
    c.attach(router)
    q.register(TC.KIND_TALK, "talk", c.on_dispatch, rank=TC.RANK_TALK)
    pend = TC._OG.hidden(c)["pending"]
    for spk in (1, 2):
        seq = int(router.schedule(5 * NS_PER_SECOND, spk, TC.KIND_TALK)[0])
        pend[seq] = (7, spk, 5 * NS_PER_SECOND, NS_PER_SECOND, 5, (3 - spk,), 0)
    with pytest.raises(RuntimeError, match="1 つの会話の中の発言を同じ束"):
        q.run_window()


def test_m2_talk_clock_refuses_writes_from_outside():
    """〔検収 M2〕負の対照: 外から欄を書く・消す・中身を書くと止まる。``ANCHORS`` の値は書けない(組)。"""
    q, c = _clock_on_queue()
    c.attach(TC.QueueRouter(q))
    q.register(TC.KIND_TALK, "talk", c.on_dispatch, rank=TC.RANK_TALK)
    c.on_turn(None, 1, 0, _session(1, 1, 2), "こんにちは")
    for name, value in (("_tc_meter", {}), ("_tc_line", {}), ("_tc_rate", {}), ("_tc_router", None), ("cap", 1),
                        ("brand_new", 1)):
        with pytest.raises(AttributeError):
            setattr(c, name, value)
    with pytest.raises(AttributeError):
        del c._tc_meter
    with pytest.raises(TypeError):
        c._tc_meter["turns"] = 99
    with pytest.raises(TypeError):
        c._tc_meter["hist"]["utterance_s"] = ()
    with pytest.raises(TypeError):
        c._tc_line[1] = (0,) * 8
    with pytest.raises(TypeError):
        c._tc_pending[0] = ()
    with pytest.raises(TypeError):
        c._tc_rate[1] = 0.1
    with pytest.raises((TypeError, AttributeError)):
        TC.ANCHORS["familiar_faster"]["value"].append(0.5)
    assert isinstance(TC.ANCHORS["familiar_faster"]["value"], tuple)
    assert c._tc_meter["turns"] == 1  # 持ち主の書く口では書ける


def test_cap_is_a_safety_and_leaves_a_record():
    c, order = _chain_run(width_s=STEP_SECONDS, turns=8, cap=3, n_sessions=1)
    m = c._tc_meter
    assert m["cap_hits"] >= 1  # 当たったら持ち越して数える(止めない)
    assert m["utterances"] == 8  # 全部いつかは処理される
    assert max(t for t, _ in order) >= STEP_SECONDS * NS_PER_SECOND  # 上限の後は次の窓


def test_late_turns_are_carried_with_the_lag():
    q, c = _clock_on_queue()
    c.attach(TC.QueueRouter(q))
    s = _session(1, 1, 2)
    step_ns = STEP_SECONDS * NS_PER_SECOND

    def on_step(t_ns, agents, seqs):
        T = t_ns // step_ns
        c.on_turn(None, 1 + T % 2, int(T), s, "こんにちは")
        if T < 2:
            q.schedule(t_ns + step_ns, BA.WORLD, BA.KIND_STEP)

    q.register(BA.KIND_STEP, "step", on_step)
    q.register(TC.KIND_TALK, "talk", c.on_dispatch, rank=TC.RANK_TALK)
    q.schedule(0, BA.WORLD, BA.KIND_STEP)
    for _ in range(4):
        q.run_window()
    m = c._tc_meter
    assert m["utterances"] == 3 and m["carried"] == 2  # 会話の番は刻みに 1 回=2 番目からは時計より遅い=持ち越し
    assert 0 < m["lag_ns_max"] < 2 * step_ns
    line = c._tc_line[1]
    assert line[2] - line[0] < 5 * NS_PER_SECOND  # 会話の中の時計は 3 発言で数秒(刻み 3 つ=180 秒ではない)


# ================================================================= C1 の口・腕・manifest
def test_c1_chat_port_shape_is_blank():
    assert TC.ChatTiming.typing_ns(1, "やあ") is None and TC.ChatTiming.read_gap_ns(1, "やあ") is None
    assert TC.MODALITIES == ("対面", "チャット") and set(TC.TIMINGS) == set(TC.MODALITIES)
    q, c = _clock_on_queue()
    c.attach(TC.QueueRouter(q))
    q.register(TC.KIND_TALK, "talk", c.on_dispatch, rank=TC.RANK_TALK)
    assert c.on_turn(None, 1, 0, _session(1, 1, 2), "やあ", modality=TC.MODALITY_CHAT) is None
    assert c._tc_meter["chat_blank"] == 1 and not c._tc_pending
    with pytest.raises(ValueError):
        c.on_turn(None, 1, 0, _session(1, 1, 2), "やあ", modality="電話")


def test_silent_other_language_and_no_session_are_counted():
    q, c = _clock_on_queue()
    c.attach(TC.QueueRouter(q))
    q.register(TC.KIND_TALK, "talk", c.on_dispatch, rank=TC.RANK_TALK)
    assert c.on_turn(None, 1, 0, None, "こんにちは") is None
    assert c.on_turn(None, 1, 0, _session(1, 1, 2), "なし") is None
    assert c.on_turn(None, 1, 0, _session(1, 1, 2), "") is None
    seq = c.on_turn(None, 1, 0, _session(2, 1, 2), "hello")
    assert seq is not None and c._tc_pending[seq][3] == STEP_SECONDS * NS_PER_SECOND  # 欄だけ=今の表(刻み 1 つ)
    m = c._tc_meter
    assert (m["no_session"], m["silent"], m["lang_other"], m["turns"]) == (1, 2, 1, 4)


def test_no_router_is_an_error():
    c = TC.TalkClock(rate_seed=1, jitter_seed=1)
    with pytest.raises(RuntimeError, match="口が無い"):
        c.on_turn(None, 1, 0, _session(1, 1, 2), "こんにちは")


def test_manifest_keys_match_the_sections_table():
    assert TC.manifest_fields(None) is None
    q, c = _clock_on_queue()
    m = TC.manifest_fields(c)
    assert tuple(m) == TC.CONFIG_KEYS + TC.OBSERVED_KEYS
    for k in TC.CONFIG_KEYS:
        assert MS.section_of(f"talk_clock.{k}") == MS.CONFIG, k
    for k in TC.OBSERVED_KEYS:
        assert MS.section_of(f"talk_clock.{k}") == MS.OBSERVED, k


def test_arm_plumbing():
    assert TC.arm() == TC.DEFAULT_ARM == "table" and TC.is_default()
    with pytest.raises(ValueError):
        TC.set_arm("syllable")
    with talk("mora"):
        assert TC.arm() == "mora" and not TC.is_default()
        assert TC.make(pop_seed=1, seed=1, step_s=STEP_SECONDS, rel_layer=None) is not None
    assert TC.make(pop_seed=1, seed=1, step_s=STEP_SECONDS, rel_layer=None) is None


def test_a_bad_environment_arm_fails_at_import():
    env = dict(os.environ, PYTHONIOENCODING="utf-8", **{TC.ENV: "bogus"})
    r = subprocess.run([sys.executable, "-c", "import shibuya.engine.speech_clock"], capture_output=True, text=True,
                       encoding="utf-8", env=env, timeout=120)
    assert r.returncode != 0 and TC.ENV in r.stderr


# ================================================================= 世界資産(腕 mora は世界を変えない)
def _hashes(res):  # noqa: ANN001
    return (res.final_hash, int(res.llm_calls), [(c.tick, c.behavior_hash, c.full_hash) for c in res.checkpoints])


@real_data
def test_mora_does_not_change_the_world_and_counts_conversations():
    kw = dict(n_agents=1000, vocab_version="v1", memory="on", relations="on", **WORLD)
    base = cli.run(**kw)
    with talk("mora"):
        arm = cli.run(**kw)
    assert _hashes(arm) == _hashes(base)
    mb, ma = base.run_manifest_fields(), arm.run_manifest_fields()
    assert "talk_clock" not in mb and ma["talk_clock"]["arm"] == "mora"
    t = ma["talk_clock"]
    assert t["utterances"] > 0 and t["conversations"] > 0 and t["pending_at_end"] == 0
    assert t["familiar"] + t["unfamiliar"] == t["utterances"] - t["lang_other"]  # 関係の層があるランは欄だけが 0
    assert 0 < t["mean_conv_tm3_s"] < t["mean_conv_table_s"]  # 会話の中の時計は今の表(1 番=刻み 1 つ)より短い
    assert sum(t["hist"]["utterance_s"]) == t["utterances"]
    assert sum(t["hist"]["conv_table_s"]) == t["conversations"]
    assert 5.0 <= t["person_rate_min"] <= t["person_rate_mean"] <= t["person_rate_max"] <= 8.07


def test_two_days_and_resume_with_mora_match_the_straight_default(tmp_path):
    """〔検収 L4〕会話の番のある構成(合成の世界・語彙 v1・150 体)で 2 日と日の境目・2 日目の途中からの再開=通し。"""
    kw = dict(n_agents=150, seed=1, world_dir=None, n_cells=9, ticks=STEPS_PER_DAY, checkpoint_every=360,
              vocab_version="v1")
    run_day = cli.run

    straight = run_day(sim_days=2, **kw)
    with talk("mora"):
        straight_m = run_day(sim_days=2, **kw)
        day = run_day(state_out=tmp_path / "d", stop_at_tick=STEPS_PER_DAY, sim_days=2, **kw)
        mid = run_day(state_out=tmp_path / "m", stop_at_tick=STEPS_PER_DAY + 371, sim_days=2, **kw)
        r_day = run_day(resume_from=tmp_path / "d" / day.resume["state_files"][-1]["file"], sim_days=2, **kw)
        r_mid = run_day(resume_from=tmp_path / "m" / mid.resume["state_files"][-1]["file"], sim_days=2, **kw)
    assert straight_m.final_hash == straight.final_hash
    assert r_day.final_hash == r_mid.final_hash == straight.final_hash
    t = straight_m.run_manifest_fields()["talk_clock"]
    assert t["utterances"] > 0 and t["conversations"] > 0  # 空振りでない
    assert r_mid.run_manifest_fields()["talk_clock"]["turns"] > 0
    hd = RS.read_state(tmp_path / "d" / day.resume["state_files"][-1]["file"]).header["fingerprint"]
    assert hd[TC.FP_KEY] == "mora"
    with pytest.raises(ValueError, match="設定が親と違う"):  # 腕の違う再開は設定の指紋で止まる
        run_day(resume_from=tmp_path / "m" / mid.resume["state_files"][-1]["file"], sim_days=2, **kw)


@real_data
@pytest.mark.slow
def test_mora_5000_one_day_gives_the_conversation_length_distribution():
    """発注: 腕 mora で 5,000 体 1 日が回り、会話の長さの分布が出る(既定の表との差は記録 tm234/README.md §T2)。"""
    with talk("mora"):
        res = cli.run(n_agents=5000, vocab_version="v1", **WORLD)
    t = res.run_manifest_fields()["talk_clock"]
    assert t["conversations"] > 50 and t["utterances"] > 100
    assert sum(t["hist"]["conv_tm3_s"]) == t["conversations"] == sum(t["hist"]["conv_table_s"])
    assert t["mean_conv_tm3_s"] < t["mean_conv_table_s"]
    assert 4.0 <= t["mean_rate_mora_per_s"] <= 9.0
