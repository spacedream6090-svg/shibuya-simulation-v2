# -*- coding: utf-8 -*-
"""tools/instruments/dm_eval(第 6 期 6-1 判断モデルの評価の器・GPU の前の分)の試験。

- 状況の読み口: 合成の 10 件 → 短い版/長い版=``engine.decision.port.compose`` と同じ文・共通部分が前・長さの腕・
  B5/B6 がある合成で人ごとの部分の分け方・数字の計器・ブロックの分け方の往復。
- 候補の口: DM-0 の 5 つの源(続ける・経験=テープの前の呼・できること・よく考える・語彙の残り)・並びの入れ替えが
  種で決まる・巡回の位置。テープの前の呼の読み(合成の parquet・版 1 と版 2)。
- 採点の器: 既知の値(JSD 0 と 1・順位相関 1 と −1・エントロピーの式・迷いの差)・驚きの語の読み口・分布の検査。
- 位置の偏りの対照: mock・古典・テープ=1 位が変わる率 0・番号 1 の正の対照・1 位が変わる率の式・符号反転の検定
  =``tools/c7/salt_compare.sign_flip_p`` と同じ値・PBS の帰無の床の既知の値。
- 厳密モード: mock と古典で一致・状態を持つ当て口は並びを変えると落ちる(負の対照)・口だけの当て口は空欄・当て口は
  作った後に欄を付け替えられない(負の対照=採点の中で付け替える当て口は落ちる)・錨の率と追加の測りの欄は読み取り専用。
- 表の形: 列の名・順位の列が無い・宣言の順・空の欄の 2 つの印・テープの行の「構成上 0」の注と脚注・Markdown と JSON。
- 守り: 封印の道筋は開く前に落ちる・評価セットとテープの md5 の食い違いで止まる・禁じた語の名を使わない(植えた名で
  落ちる負の対照つき)。
- 実データ(1-10 の 340 件と状況のあるテープ 32 本): 1 回通して digest が記録の golden と同じ・テープ 32 本の md5 が
  1-10 の記録と同じ・``cli.main --no-tape-experience`` の通し。
"""
from __future__ import annotations

import ast
import itertools
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
_INSTR = ROOT / "tools" / "instruments"
if str(_INSTR) not in sys.path:
    sys.path.insert(0, str(_INSTR))

import dm_eval  # noqa: E402
from dm_eval import bias as B  # noqa: E402
from dm_eval import cli as C  # noqa: E402
from dm_eval import judge as J  # noqa: E402
from dm_eval import situations as S  # noqa: E402
from dm_eval import table as T  # noqa: E402
from shibuya.core.time_consts import HOURS_PER_DAY, MINUTES_PER_HOUR, SECONDS_PER_HOUR  # noqa: E402
from shibuya.engine.decision.port import OTHER_ID, SURPRISE_WORDS, Candidate, compose  # noqa: E402


PKG = _INSTR / "dm_eval"
RECORD = ROOT / "docs" / "bench" / "analysis" / "wallbounce-1012" / "dm61" / "result.json"

# ---------------------------------------------------------------------- 合成の状況(個人の行でない)
B0_SYN = "[合成の前置き] あなたは街にいる一人の人物です。観測に書かれていないことは知りません。"
KINDS = ("居住者", "通勤者", "従業者", "来街者", "指令")


def _syn(i: int, *, b5: str | None = None, b6: str | None = None, out_word: str = "移動") -> S.Situation:
    hour, minute = (7 + i) % HOURS_PER_DAY, (i * 7) % MINUTES_PER_HOUR
    lines = [
        f"[B1 種別] あなたは{KINDS[i % 5]}です。",
        "[B2 場所] 現在地は駅前の広場(地上)です。",
        "[B2 可視] 見えるもの: 店、駅の改札。",
        f"[B3 時刻] 現在時刻は{hour}時{minute}分です。",
        "[B4 密度] 歩行者密度は段階Aです。",
        "[B4b 近景] 25メートル以内: なし。",
    ]
    blocks = {"B0": B0_SYN, **S.split_blocks("\n".join(lines))}
    if b5 is not None:
        blocks["B5"] = b5
    if b6 is not None:
        blocks["B6"] = b6
    return S.Situation(
        sid=f"syn-{i:04d}", blocks=blocks, facts={"hour": hour, "minute": minute, "station_word_or_band": i % 2 == 0,
                                                  "shop_word": i % 3 == 0},
        strata={"kind": KINDS[i % 5]}, agent_id=100 + i, step=600 + i, wake_class=i % 4, call_id=f"{600 + i}:{100 + i}:1",
        tape="tape/syn", tape_output=f"理由: 合成\n行動: {out_word} 対象: なし ひと言: なし",
    )


SYN = tuple(_syn(i, out_word=("移動", "購入", "待機", "乗車", "休憩")[i % 5]) for i in range(10))


def _presented(sit: S.Situation, seed: str = "t") -> tuple[Candidate, ...]:
    return S.orders(S.candidates_for(sit), sit.sid, n_orders=1, seed=seed)[0]


# ---------------------------------------------------------------------- 状況の読み口
def test_split_blocks_roundtrip_and_order():
    text = "[B1 種別] あ\n[B2 場所] い\n[B2 可視] う\n続きの行\n[B3 時刻] え\n[B4 密度] お\n[B4b 近景] か"
    blocks = S.split_blocks(text)
    assert list(blocks) == ["B1", "B2", "B3", "B4", "B4b"]
    assert blocks["B2"] == "[B2 場所] い\n[B2 可視] う\n続きの行"
    assert "\n".join(blocks[b] for b in S.BLOCK_ORDER if b in blocks) == text
    with pytest.raises(ValueError):
        S.split_blocks("[B3 時刻] え\n[B1 種別] あ")
    with pytest.raises(ValueError):
        S.split_blocks("[B1 種別] あ\n[B2 場所] い\n[B1 種別] また")
    with pytest.raises(ValueError):
        S.split_blocks("頭の無い行")


@pytest.mark.parametrize("arm", tuple(S.LENGTH_ARMS))
def test_render_is_compose_with_common_part_first(arm):
    for sit in SYN:
        pres = _presented(sit)
        blocks = S.arm_blocks(sit, arm)
        short = S.render(sit, pres, length="short", arm=arm)
        long_ = S.render(sit, pres, length="long", arm=arm)
        assert short.text == compose(blocks, pres, length="short")
        assert long_.text == compose(blocks, pres, length="long")
        common = S.common_text(blocks)
        assert short.text.startswith(common) and long_.text.startswith(common)
        assert short.text[:len(common)].encode("utf-8") == long_.text[:len(common)].encode("utf-8")
        # 材料に人ごとの部分が無い=短い版と長い版の差は長い版の末尾の指示だけ
        assert long_.text.startswith(short.text + "\n") and long_.text.count("\n") == short.text.count("\n") + 1
        assert ("B0" in blocks) == (arm == "t1000") and short.text.startswith(B0_SYN) == (arm == "t1000")
        assert short.tokens is None and short.target_tokens == S.LENGTH_ARMS[arm]
        assert short.budget_chars == round(S.LENGTH_ARMS[arm] * S.CHARS_PER_TOKEN)
        assert short.over_budget == (short.chars > short.budget_chars) and short.chars == len(short.text)


def test_render_individual_blocks_short_b6_long_b5_b6():
    sit = _syn(0, b5="[B5 体] 空腹は少しです。", b6="[B6 起床] 予定の時刻です。")
    pres = _presented(sit)
    short = S.render(sit, pres, length="short", arm="t1000").text
    long_ = S.render(sit, pres, length="long", arm="t1000").text
    assert "[B6 起床]" in short and "[B5 体]" not in short
    assert "[B5 体]" in long_ and "[B6 起床]" in long_
    common = S.common_text(S.arm_blocks(sit, "t1000"))
    assert short.startswith(common + "\n[B6") and long_.startswith(common + "\n[B5")
    assert S.situation_text(S.arm_blocks(sit, "t1000"), "long").endswith("[B6 起床] 予定の時刻です。")


def test_numbers_outside_money_time():
    f = S.numbers_outside_money_time
    assert f("現在時刻は20時35分です。") == 0
    assert f("24時間営業しています。") == 0
    assert f("過料は5万円です。¥300 と 120円。") == 0
    assert f("25メートル以内") == 1
    assert f("現在地はセルg3_9_GL") == 2
    assert f("65デシベル帯・段階A") == 1
    assert f("[B4b 近景] 25メートル以内: なし。\n[B1 種別] あなたは来街者です。") == 1  # ブロックの印は数えない
    # 提示の番号(C-2 の番号で返す形)は数えない=状況の部分だけ
    sit = SYN[0]
    r = S.render(sit, _presented(sit), length="short", arm="t300")
    assert r.numbers_outside_money_time == f(S.situation_text(S.arm_blocks(sit, "t300"), "short"))


def test_situation_language_fields_are_declared_blank():
    assert all(s.lang == "ja" and s.first_language is None and s.missing == ("B5", "B6") for s in SYN)


# ---------------------------------------------------------------------- 候補の口
def test_candidates_come_from_the_five_sources():
    sit = _syn(0)  # 駅の手がかり あり・店の手がかり あり
    cands = S.candidates_for(sit, ("購入", "移動", "購入"))
    assert len(cands) == 13 and len({c.id for c in cands}) == 13
    by = {c.kind: c.source for c in cands}
    assert by["待機"] == "continue"
    assert by["購入"] == "experience" and by["移動"] == "experience"
    assert by["乗車"] == "affordance"
    assert by["よく考える"] == "deliberate" and cands[-1].kind == "よく考える"
    assert {c.source for c in cands} == {"continue", "experience", "affordance", "vocab", "deliberate"}
    assert "plan" not in {c.source for c in cands}  # B6 が無い=空欄
    assert all(c.number is None for c in cands)
    assert set(by) - {"よく考える"} == set(S.VOCAB)
    plain = S.candidates_for(_syn(1))  # 手がかり なし=できることは移動だけ
    assert [c.kind for c in plain if c.source == "affordance"] == ["移動"]


def test_orders_are_deterministic_and_cyclic():
    cands = S.candidates_for(SYN[3], ("移動",))
    a = S.orders(cands, SYN[3].sid, n_orders=4, seed="s1")
    b = S.orders(cands, SYN[3].sid, n_orders=4, seed="s1")
    assert [[(c.id, c.number) for c in o] for o in a] == [[(c.id, c.number) for c in o] for o in b]
    others = [S.orders(cands, SYN[3].sid, n_orders=1, seed=f"s{k}")[0] for k in range(2, 8)]
    assert any([c.id for c in o] != [c.id for c in a[0]] for o in others)
    assert S.rotation_offsets(13, 4) == (0, 3, 6, 9) and S.rotation_offsets(13, 13) == tuple(range(13))
    base = [c.id for c in a[0]]
    for o, r in zip(a, S.rotation_offsets(13, 4)):
        assert [c.id for c in o] == base[r:] + base[:r]
        assert [c.number for c in o] == list(range(1, 14))
    with pytest.raises(ValueError):
        S.rotation_offsets(13, 14)


def _write_tape(path: Path, rows: list[dict], *, with_deferred: bool) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    cols = {"agent_id": pa.array([r["a"] for r in rows], pa.int32()),
            "tick": pa.array([r["t"] for r in rows], pa.int64()),
            "response": pa.array([r["resp"] for r in rows], pa.string())}
    if with_deferred:
        cols["deferred"] = pa.array([r.get("d", 0) for r in rows], pa.int8())
    path.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.table(cols), str(path / "calls.parquet"), row_group_size=3)


def _resp(w: str) -> str:
    return f"理由: 合成\n行動: {w} 対象: なし ひと言: なし"


@pytest.mark.parametrize("with_deferred", [False, True])
def test_tape_experience_reads_prior_calls_newest_first(tmp_path, with_deferred):
    rows = [
        {"a": 7, "t": 10, "resp": _resp("移動")},
        {"a": 8, "t": 11, "resp": _resp("就寝")},  # 別の体
        {"a": 7, "t": 20, "resp": _resp("購入")},
        {"a": 7, "t": 30, "resp": "", "d": 1},  # 繰り延べ(応答が空)
        {"a": 7, "t": 40, "resp": _resp("休憩")},
        {"a": 7, "t": 45, "resp": "壊れた応答"},  # 語彙の外
        {"a": 7, "t": 50, "resp": _resp("乗車")},  # 状況と同じ刻み=含めない
        {"a": 7, "t": 60, "resp": _resp("会話")},  # 後=含めない
    ]
    _write_tape(tmp_path / "tape" / "x", rows, with_deferred=with_deferred)
    sit = S.Situation(sid="x1", blocks={"B1": "[B1 種別] 合成"}, agent_id=7, step=50, tape="tape/x")
    got = S.tape_experience([sit], root=tmp_path)
    assert got == {"x1": ("休憩", "購入", "移動")}
    assert S.tape_experience([sit], root=tmp_path, k=1) == {"x1": ("休憩",)}


# ---------------------------------------------------------------------- 採点の器
def test_known_values_jsd_spearman_entropy():
    p = {"a": 0.5, "b": 0.3, "c": 0.2}
    assert J.jsd(p, p) == pytest.approx(0.0, abs=1e-15)
    assert J.jsd({"a": 1.0}, {"b": 1.0}) == pytest.approx(1.0)
    assert J.spearman(p, p) == pytest.approx(1.0)
    assert J.spearman(p, {"a": 0.2, "b": 0.3, "c": 0.5}) == pytest.approx(-1.0)
    assert J.spearman(p, {"a": 1 / 3, "b": 1 / 3, "c": 1 / 3}) is None
    h = J.hesitation(p)
    assert h.margin == pytest.approx(0.2)
    assert h.entropy == pytest.approx(-sum(v * math.log(v) for v in p.values()))
    u = J.hesitation({k: 0.25 for k in "wxyz"})
    assert u.margin == pytest.approx(0.0) and u.entropy == pytest.approx(math.log(4))
    assert J.top1({"b": 0.4, "a": 0.4, "c": 0.2}) == "a"  # 同点は id の順(番号の順でない)


def test_agreement_is_zero_distance_against_itself():
    kinds = {s.sid: {**{c.id: c.kind for c in S.candidates_for(s)}, OTHER_ID: OTHER_ID} for s in SYN}
    cl = J.ClassicalScorer()
    d = {s.sid: cl.score(s, _presented(s)) for s in SYN}
    ag = J.agreement(d, d, kinds)
    assert ag["jsd_mean"] == pytest.approx(0.0, abs=1e-12) and ag["top1_agree"] == 1.0
    assert ag["marginal_jsd"] == pytest.approx(0.0, abs=1e-12) and ag["spearman_mean"] == pytest.approx(1.0)


def test_surprise_reader():
    for i, w in enumerate(SURPRISE_WORDS):
        assert J.surprise_of(w) == i and J.surprise_of(f" {w}。") == i
    assert J.surprise_of("少し") is None and J.surprise_of(None) is None and J.surprise_of("とても") is None


def test_normalize_checks():
    pres = _presented(SYN[0])
    with pytest.raises(ValueError):
        J.normalize({"no-such": 1.0}, pres)
    with pytest.raises(ValueError):
        J.normalize({pres[0].id: -1.0, pres[1].id: 2.0}, pres)
    with pytest.raises(ValueError):
        J.normalize({pres[0].id: 0.0}, pres)
    d = J.normalize({pres[0].id: 2.0, OTHER_ID: 2.0}, pres)
    assert d[pres[0].id] == 0.5 and d[OTHER_ID] == 0.5 and sum(d.values()) == pytest.approx(1.0)
    assert list(d)[:-1] == [c.id for c in pres]


def test_scorers_return_distributions():
    pres = _presented(SYN[1])
    for sc in (J.MockScorer(), J.ClassicalScorer(), J.TapeScorer()):
        d = sc.score(SYN[1], pres)
        assert sum(d.values()) == pytest.approx(1.0) and all(v >= 0 for v in d.values())
    assert J.TapeScorer().score(SYN[1], pres)[next(c.id for c in pres if c.kind == "購入")] == 1.0
    weird = S.Situation(sid="w", blocks={"B1": "[B1 種別] 合成"}, tape_output="意味の無い文")
    assert J.TapeScorer().score(weird, _presented(weird))[OTHER_ID] == 1.0
    cl = J.ClassicalScorer()
    wp = cl.word_probs(SYN[1])
    assert set(wp) <= set(S.VOCAB) and sum(wp.values()) == pytest.approx(1.0)
    slot = (SYN[1].facts["hour"] * MINUTES_PER_HOUR + SYN[1].facts["minute"]) // cl.slot_minutes
    raw = cl.prior.rates[0, 0, 0, :, slot] + cl.prior.rates[1, 0, 0, :, slot]  # 通勤者=有業・性は平均・年齢は総数
    np.testing.assert_allclose(cl.activity_probs("通勤者", slot), raw / raw.sum())


def test_model_ports_are_ports_only():
    pres = _presented(SYN[0])
    for sc in (J.ClefScorer("flash"), J.ClefScorer("full"), J.KevScorer(), J.SokudanScorer(), J.GScorer()):
        assert sc.implemented is False and sc.reads_text is True
        with pytest.raises(J.ScorerUnavailable):
            sc.score(SYN[0], pres, text="文")
        assert J.strict_check(lambda sc=sc: sc, [(SYN[0], pres, None)])["status"] == "GPU の後(S6)"
    assert set(J.SokudanScorer.meta["extra_measures"]) == {
        "long_input_t300_t1000", "synthetic_training_data_effect", "non_japanese_first_language"}
    assert all(v is None for v in J.SokudanScorer.meta["extra_measures"].values())
    assert J.HUMAN_FIELDS["human_match"] is None


def test_gpu_hours_formula_values_blank_until_measured():
    assert J.gpu_hours_per_sim_day(None) is None
    assert J.gpu_hours_per_sim_day(0.5) == pytest.approx(64_528 * 0.5 / SECONDS_PER_HOUR)
    assert J.gpu_hours_per_sim_day(0.5, scale_to_agents=390_067, n_gpus=8) == pytest.approx(
        64_528 * (390_067 / 5_000) * 0.5 / SECONDS_PER_HOUR / 8)
    f = J.speed_fields(J.SokudanScorer(), None)
    assert f["tokens_in"] is None and f["gpu_hours_per_sim_day"] is None and f["gpu_sec_per_call"] is None


# ---------------------------------------------------------------------- 位置の偏りの対照
def _orders_all(n_orders: int = 4):
    return {s.sid: S.orders(S.candidates_for(s), s.sid, n_orders=n_orders, seed="t") for s in SYN}


@pytest.mark.parametrize("make", [J.MockScorer, J.ClassicalScorer, J.TapeScorer])
def test_content_only_scorers_have_zero_position_bias(make):
    recs, _ = B.score_orders(make(), SYN, _orders_all(), arm="t300")
    pb = B.position_bias(recs)
    assert pb["top1_change_rate"] == 0.0 and pb["top1_change_pairwise"] == 0.0 and pb["self_consistency_2"] == 1.0
    assert pb["n_orders"] == [4] and pb["number1_test"]["method"] == "exact"


def test_first_number_control_is_detected():
    recs, _ = B.score_orders(J.FirstNumberControl(), SYN, _orders_all(), arm="t300")
    pb = B.position_bias(recs)
    assert pb["top1_change_rate"] == 1.0 and pb["number1_rate"] == 1.0 and pb["self_consistency_2"] == 0.0
    assert pb["pbs_by_n"]["13"]["pbs"] == pytest.approx(math.sqrt(1 - 1 / 13))
    assert pb["number1_test"]["p"] == pytest.approx(2 / 2 ** 10)  # 両側・全部の組=下限 2/2^n




class _HalfPositional(J.Scorer):
    """sid の番号が偶数なら番号 1(位置)・奇数なら中身(古典)を選ぶ=1 位が変わる率は 0.5 のはず。"""

    name = "half"

    def __init__(self) -> None:
        self.cl = J.ClassicalScorer()
        super().__init__()

    def _score(self, situation, candidates, text):
        if int(situation.sid[-1]) % 2 == 0:
            return {min(candidates, key=lambda c: c.number).id: 1.0}
        return self.cl._score(situation, candidates, text)


def test_change_rate_formula():
    recs, _ = B.score_orders(_HalfPositional(), SYN, _orders_all(), arm="t300")
    pb = B.position_bias(recs)
    assert pb["top1_change_rate"] == 0.5
    # 対ごと: 位置で選ぶ状況は C(4,2)=6 対が全部違う(巡回の先頭は 4 通りとも違う)・中身で選ぶ状況は 0
    assert pb["top1_change_pairwise"] == pytest.approx(0.5)
    tops = {sid: [J.top1(d) for _p, d in r] for sid, r in recs.items()}
    hand = np.mean([any(a != b for a, b in itertools.combinations(t, 2)) for t in tops.values()])
    assert pb["top1_change_rate"] == pytest.approx(hand)


def test_sign_flip_is_salt_compare_formula():
    recs, _ = B.score_orders(_HalfPositional(), SYN, _orders_all(), arm="t300")
    pb = B.position_bias(recs)
    d = []
    for sid in sorted(recs):
        r = recs[sid]
        nums = [next(c.number for c in pres if c.id == J.top1(dist)) for pres, dist in r]
        d.append(sum(1 for k in nums if k == 1) / len(nums) - 1 / 13)
    ref = B.salt_compare().sign_flip_p(np.asarray(d), "two-sided")
    assert pb["number1_test"]["p"] == ref["p"] and pb["number1_test"]["mean_d"] == pytest.approx(np.mean(d))


def test_pbs_null_floor_known_values():
    full = B.pbs_null_floor(50, 13, tuple(range(13)), reps=200)  # 全部の位置を巡回=位置の分布は一様そのもの
    assert full["mean"] == pytest.approx(0.0, abs=1e-12) and full["p95"] == pytest.approx(0.0, abs=1e-12)
    one = B.pbs_null_floor(1, 13, (0,), reps=50)  # 1 件 1 通り=いつも 1 か所に全部
    assert one["p05"] == pytest.approx(math.sqrt(1 - 1 / 13)) and one["p95"] == pytest.approx(math.sqrt(1 - 1 / 13))
    a = B.pbs_null_floor(340, 13, (0, 3, 6, 9), reps=2_000)
    b = B.pbs_null_floor(340, 13, (0, 3, 6, 9), reps=2_000)
    assert a == b and 0.0 < a["p05"] < a["mean"] < a["p95"] < 0.1  # 決定的・床は 0 より上


def test_tape_fixed_order_is_record_only():
    t = B.tape_fixed_order(SYN)
    assert t["order"] == list(S.VOCAB) and sum(t["counts"]) + t["other"] == len(SYN)
    assert t["counts"][0] == 2 and t["position1_rate"] == pytest.approx(0.2)


# ---------------------------------------------------------------------- 厳密モード(DM9)
def test_strict_mode_mock_and_classical_identical():
    items = [(s, o, None) for s in SYN for o in _orders_all()[s.sid]]
    for make in (J.MockScorer, J.ClassicalScorer, J.TapeScorer):
        r = J.strict_check(make, items)
        assert r["identical_repeat"] is True and r["identical_reordered"] is True
        assert r["max_abs_diff_reordered"] == 0.0 and r["n_items"] == len(items)


class _Stateful(J.Scorer):
    """呼んだ回数で重みが変わる(まとめ方に左右される)=厳密モードの負の対照(数は箱の中=欄は付け替えない)。"""

    name = "stateful"

    def __init__(self) -> None:
        self.calls = [0]
        super().__init__()

    def _score(self, situation, candidates, text):
        self.calls[0] += 1
        return {c.id: 1.0 + (self.calls[0] % 3 == 0) * (c.number == 1) for c in candidates}


def test_strict_mode_catches_order_dependence():
    items = [(s, _presented(s), None) for s in SYN]
    r = J.strict_check(_Stateful, items)
    assert r["identical_repeat"] is True and r["identical_reordered"] is False


class _Rebinding(J.Scorer):
    """作った後に欄を付け替える当て口(守りの負の対照)。"""

    name = "rebinding"

    def _score(self, situation, candidates, text):
        self.last = situation.sid  # 閉じた後の付け替え=落ちるはず
        return {candidates[0].id: 1.0}


def test_scorers_are_frozen_after_construction():
    sc = J.MockScorer()
    with pytest.raises(AttributeError):
        sc.seed = "other"
    with pytest.raises(AttributeError):
        del sc.seed
    with pytest.raises(AttributeError):  # 負の対照: 採点の中で欄を付け替える当て口は落ちる
        _Rebinding().score(SYN[0], _presented(SYN[0]))
    with pytest.raises(TypeError):
        J.SokudanScorer.meta["extra_measures"]["long_input_t300_t1000"] = 1.0
    cl = J.ClassicalScorer()
    assert not cl.prior.rates.flags.writeable and not cl.prior.sample.flags.writeable
    with pytest.raises(ValueError):
        cl.prior.rates[0, 0, 0, 0, 0] = 1.0
    json.dumps(J.SokudanScorer().describe(), ensure_ascii=False)  # 読み取り専用の写像も JSON に書ける


# ---------------------------------------------------------------------- 表の形と通し
@pytest.fixture(scope="module")
def syn_result():
    return C.evaluate(SYN, {s.sid: ("移動",) for s in SYN[:4]}, seed="t", n_orders=4)


def test_table_shape_and_no_ranking(syn_result):
    rows = syn_result["table"]["rows"]
    names = [d.name for d in J.scorer_registry()]
    assert len(rows) == len(names) * len(S.LENGTH_ARMS)
    assert [r["scorer"] for r in rows] == [n for n in names for _a in S.LENGTH_ARMS]  # 宣言の順(指標で並べない)
    assert all(tuple(r) == T.COLUMN_KEYS for r in rows)
    keys = {k.lower() for k in T.COLUMN_KEYS}
    heads = {h for _k, h in T.COLUMNS}
    assert not keys & {"rank", "ranking", "order", "順位"} and "順位" not in heads and "rank" not in heads
    for col in ("jsd_vs_classical", "self_consistency_2", "pbs", "margin_mean", "entropy_mean", "surprise",
                "human_match", "wall_s_per_item", "tokens_in", "gpu_hours_per_sim_day", "lang", "first_language", "arm"):
        assert col in T.COLUMN_KEYS
    stub = [r for r in rows if not r["implemented"]]
    assert stub and all(r["pbs"] is None and r["gpu_hours_per_sim_day"] is None for r in stub)
    assert all(r["human_match"] is None and r["first_language"] is None and r["tokens_in"] is None for r in rows)
    md = T.to_markdown(rows)
    assert md.splitlines()[0] == "| " + " | ".join(h for _k, h in T.COLUMNS) + " |" and "空欄" not in md
    doc = json.loads(T.to_json(rows))
    assert [c["key"] for c in doc["columns"]] == list(T.COLUMN_KEYS) and len(doc["rows"]) == len(rows)
    assert doc["blank"] == T.blanks_of(rows) == syn_result["table"]["blank"]


def test_blank_cells_carry_two_kinds_of_marks(syn_result):
    rows = syn_result["table"]["rows"]
    for r, bl in zip(rows, T.blanks_of(rows)):
        assert set(bl) == {k for k in T.COLUMN_KEYS if k != "notes" and r[k] is None}
        assert all(v == T.BLANK_GPU or v.startswith("該当なし(") for v in bl.values())
        if not r["implemented"]:
            metric = ("jsd_vs_classical", "self_consistency_2", "pbs", "margin_mean", "wall_s_per_item", "tokens_in",
                      "gpu_hours_per_sim_day")
            assert all(bl[k] == T.BLANK_GPU for k in metric)
        assert bl["jsd_vs_g"] == T.BLANK_GPU and bl["human_match"] == T.BLANK_VALIDATION
    by = {(r["scorer"], r["arm"]): bl for r, bl in zip(rows, T.blanks_of(rows))}
    assert by[("classical", "t300")]["jsd_vs_classical"] == T.BLANK_SELF
    assert by[("tape", "t300")]["jsd_vs_tape"] == by[("tape", "t300")]["top1_agree_vs_tape"] == T.BLANK_SELF
    assert by[("mock", "t300")]["gpu_hours_per_sim_day"] == T.BLANK_NO_GPU
    md = T.to_markdown(rows)
    assert T.BLANK_GPU in md and T.BLANK_SELF in md


def test_order_blind_tape_rows_say_bias_is_zero_by_construction(syn_result):
    rows = syn_result["table"]["rows"]
    tape = [r for r in rows if r["scorer"] == "tape"]
    assert tape and all(r["notes"].startswith("位置の偏りの列は構成上 0") for r in tape)
    assert all("位置と中身が重なり" in r["notes"] for r in tape)
    assert all(not (r["notes"] or "").startswith("位置の偏りの列は構成上 0") for r in rows if r["scorer"] != "tape")
    foot = syn_result["table"]["footnotes"]
    assert any(f.startswith("PBS の帰無の床") for f in foot) and any("構成上 0" in f for f in foot)
    fl = syn_result["pbs_null_floor"]["13"]
    assert fl["n_situations"] == len(SYN) and fl["offsets"] == [0, 3, 6, 9]
    md = T.to_markdown(rows, footnotes=foot)
    assert "PBS の帰無の床" in md and md.count("位置の偏りの列は構成上 0") >= 3


def test_evaluate_is_deterministic(syn_result):
    again = C.evaluate(SYN, {s.sid: ("移動",) for s in SYN[:4]}, seed="t", n_orders=4)
    assert again["digest"] == syn_result["digest"]
    other = C.evaluate(SYN, {s.sid: ("移動",) for s in SYN[:4]}, seed="u", n_orders=4)
    assert other["digest"] != syn_result["digest"]
    by = {e["describe"]["name"]: e for e in syn_result["scorers"]}
    for name in ("mock", "classical", "tape"):
        t300, t1000 = by[name]["by_arm"]["t300"], by[name]["by_arm"]["t1000"]
        assert t300["position_bias"] == t1000["position_bias"] and t1000["same_as_arm"] == "t300"
        assert t300["position_bias"]["top1_change_rate"] == 0.0
    assert syn_result["controls"]["first_number"]["position_bias"]["number1_rate"] == 1.0
    assert syn_result["experience"] == {"situations_with_experience": 4, "words_total": 4}
    assert [s["identical_reordered"] for s in syn_result["strict"][:3]] == [True, True, True]


def test_write_outputs_refuses_overwrite(tmp_path, syn_result):
    md5s = C.write_outputs(syn_result, tmp_path)
    assert set(md5s) == {"result.json", "table.md", "table.json"}
    assert b"\r" not in (tmp_path / "result.json").read_bytes()
    with pytest.raises(FileExistsError):
        C.write_outputs(syn_result, tmp_path)
    C.write_outputs(syn_result, tmp_path, overwrite=True)


def _write_evalset(d: Path) -> None:
    rows = [{"sid": "f-0001", "input_text": "[B1 種別] あなたは来街者です。\n[B3 時刻] 現在時刻は9時00分です。",
             "b0_id": "b0x", "lang": "ja", "output": "理由: 合成\n行動: 移動 対象: なし ひと言: なし"}]
    d.mkdir(parents=True, exist_ok=True)
    (d / S.SITUATIONS_NAME).write_bytes(("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
                                        .encode("utf-8"))
    (d / S.SUMMARY_NAME).write_bytes(json.dumps({"b0_texts": {"b0x": "[合成] 前置き"}, "tapes": []},
                                                ensure_ascii=False).encode("utf-8"))


def test_md5_mismatch_stops_reading(tmp_path):
    _write_evalset(tmp_path)
    with pytest.raises(ValueError, match="md5"):
        S.load_situations(tmp_path)
    sits = S.load_situations(tmp_path, verify_md5=False)  # 照らさなければ読める(合成の写し)
    assert [s.sid for s in sits] == ["f-0001"] and sits[0].blocks["B0"] == "[合成] 前置き"


def test_tape_md5_mismatch_is_reported(tmp_path):
    _write_evalset(tmp_path / "ev")
    _write_tape(tmp_path / "tape" / "x", [{"a": 1, "t": 1, "resp": _resp("移動")}], with_deferred=False)
    sit = S.Situation(sid="x1", blocks={"B1": "[B1 種別] 合成"}, agent_id=1, step=2, tape="tape/x")
    r = S.verify_tape_md5([sit], root=tmp_path, directory=tmp_path / "ev")  # 表に無いテープ=食い違い
    assert r == {"n": 1, "ok": False, "mismatch": ["tape/x"], "basis": r["basis"]}


# ---------------------------------------------------------------------- 守り
def test_sealed_paths_fail_before_reading(tmp_path):
    from read_guard import SealedPathError

    for p in ("data/realworld_live/odpt_rt/x.json", "data/kddi_la/x.csv", "data/shibuya_jinryu/a.csv",
              "docs/bench/c7/holdout/x.json", "data/x/boundary_counts.json"):
        with pytest.raises(SealedPathError):
            S._read_bytes(ROOT / p)
    with pytest.raises(S.EvalsetMissing):
        S.load_situations(tmp_path)


BANNED_WORDS = ("open", "tick")


def _banned_identifiers(source: str) -> list[str]:
    """名(関数・クラス・引数・名前・属性・import の別名)のうち、禁じた語を含む物。文字列と注は見ない。"""
    found = []
    for node in ast.walk(ast.parse(source)):
        names: list[str] = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.append(node.name)
        elif isinstance(node, ast.Name):
            names.append(node.id)
        elif isinstance(node, ast.Attribute):
            names.append(node.attr)
        elif isinstance(node, ast.arg):
            names.append(node.arg)
        elif isinstance(node, ast.alias):
            names.append(node.asname or node.name)
        found += [n for n in names if any(w in n.lower() for w in BANNED_WORDS)]
    return found


def test_identifier_names_avoid_banned_words():
    bad = {p.name: _banned_identifiers(p.read_text(encoding="utf-8")) for p in sorted(PKG.glob("*.py"))}
    assert len(bad) == 6 and all(v == [] for v in bad.values()), bad


def test_identifier_check_catches_planted_names():
    src = (PKG / "judge.py").read_text(encoding="utf-8")
    planted = src + "\n\ndef " + "op" + "en_gate(t" + "ick_count):\n    return t" + "ick_count\n"
    found = _banned_identifiers(planted)
    assert "op" + "en_gate" in found and "t" + "ick_count" in found  # 負の対照: 植えた名は見つかる
    assert _banned_identifiers(src) == []


# ---------------------------------------------------------------------- 実データ(1-10 の 340 件)
@pytest.mark.requires_data("evalset", "server_retrieval", "tape")
def test_real_evalset_once_matches_recorded_golden():
    sits = S.load_situations()
    assert len(sits) == S.N_SITUATIONS
    for s in sits:
        assert all(b in s.blocks for b in ("B0", "B1", "B2", "B3", "B4", "B4b")) and s.lang == "ja"
    exp = S.tape_experience(sits)
    res = C.evaluate(sits, exp)
    assert res["candidates"]["n_candidates"] == {"13": S.N_SITUATIONS}
    by = {e["describe"]["name"]: e for e in res["scorers"]}
    for name in ("mock", "classical", "tape"):
        pb = by[name]["by_arm"]["t300"]["position_bias"]
        assert pb["top1_change_rate"] == 0.0 and pb["self_consistency_2"] == 1.0
    assert res["controls"]["first_number"]["position_bias"]["number1_rate"] == 1.0
    assert all(s["identical_reordered"] for s in res["strict"] if s["status"] == "検査済み")
    rec = json.loads(RECORD.read_text(encoding="utf-8"))
    assert res["digest"] == rec["digest"]


@pytest.mark.requires_data("evalset", "server_retrieval", "tape")
def test_real_tapes_match_the_recorded_md5():
    sits = S.load_situations()
    r = S.verify_tape_md5(sits)
    assert r["n"] == 32 and r["ok"] is True and r["mismatch"] == []


@pytest.mark.requires_data("evalset")
def test_cli_main_without_tape_experience(tmp_path, capsys):
    assert C.main(["run", "--out-dir", str(tmp_path / "out"), "--no-tape-experience"]) == 0
    out = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    doc = json.loads((tmp_path / "out" / "result.json").read_text(encoding="utf-8"))
    assert doc["inputs"]["tape_experience"] is False and doc["inputs"]["tapes_md5"] is None
    assert doc["experience"] == {"situations_with_experience": 0, "words_total": 0}
    assert doc["digest"] == out["digest"] != json.loads(RECORD.read_text(encoding="utf-8"))["digest"]
    assert {p.name for p in (tmp_path / "out").iterdir()} == {"result.json", "table.md", "table.json"}
    with pytest.raises(FileExistsError):
        C.main(["run", "--out-dir", str(tmp_path / "out"), "--no-tape-experience"])


# ====================================================================== 〔11-01 段 1 の 3〕消費の場面・当て口の口・比べの列
import hashlib  # noqa: E402
import re  # noqa: E402
import shutil  # noqa: E402
from types import SimpleNamespace  # noqa: E402

from dm_eval import backends as BK  # noqa: E402
from shibuya.engine.decision.port import ALL_SOURCES, OTHER_TEXT  # noqa: E402
from dm_eval.backends import base as BB  # noqa: E402
from dm_eval.backends import hf as BH  # noqa: E402
from dm_eval.backends import vllm as BV  # noqa: E402

SCENES = S.CONSUMPTION_SCENES
RECORD_1101 = ROOT / "docs" / "bench" / "analysis" / "dm-eval-11-01" / "consumption" / "result.json"
#: 1-10 の記録の形の表の列(11-01 の前=消さないことの検査)。
OLD_COLUMN_KEYS = (
    "scorer", "role", "implemented", "lang", "first_language", "arm", "jsd_vs_classical", "spearman_vs_classical",
    "jsd_vs_tape", "top1_agree_vs_tape", "jsd_vs_g", "self_consistency_2", "top1_change_rate", "number1_rate", "pbs",
    "number1_p", "margin_mean", "entropy_mean", "surprise", "other_rate", "human_match", "wall_s_per_item", "tokens_in",
    "gpu_hours_per_sim_day", "notes",
)
NEW_COLUMN_KEYS = ("form", "top1_agree_vs_g", "determinism_rate", "determinism_repeats", "breakdown_rate", "vram_gb",
                   "qty_mean", "qty_agree_vs_g", "qty_absdiff_vs_g")
#: 1-10 の層の鍵(消費の場面も同じ鍵=〔検収 低 3〕)。
EVALSET_STRATA_KEYS = {"heat", "kind", "scene", "time_band", "wake"}
#: 実在の店名・施設名・地名・催し(場面に出さない=漏洩の検査と分ける)。
REAL_NAMES = ("渋谷", "原宿", "表参道", "新宿", "恵比寿", "代官山", "スクランブル", "MIYASHITA", "宮下", "ハロウィン",
              "ヒカリエ", "パルコ", "PARCO", "セブン", "ローソン", "ファミリーマート", "ファミマ", "スターバックス",
              "マクドナルド", "ユニクロ", "無印", "ドン・キホーテ", "東急", "西武", "109", "ストリーム", "キャスト", "マツキヨ")


@pytest.fixture(scope="module")
def scenes():
    return S.load_scene_file(SCENES)


# ---------------------------------------------------------------------- 場面の読みと md5
def test_consumption_scenes_md5_and_counts(scenes):
    assert len(scenes.situations) == 44 and len(scenes.situations) >= 40
    assert scenes.by_point() == {p: 11 for p in S.DECISION_POINTS}
    assert all(v >= 10 for v in scenes.by_point().values())
    md5_file = S.read_md5_list(SCENES.with_name("consumption_v1.md5").read_bytes())
    assert md5_file == dict(scenes.md5) and set(md5_file) == {"consumption_v1.jsonl", "consumption_v1.b0.json"}
    assert md5_file["consumption_v1.jsonl"] == hashlib.md5(SCENES.read_bytes()).hexdigest()
    for name in md5_file:  # LF・UTF-8
        raw = SCENES.with_name(name).read_bytes()
        assert b"\r" not in raw and raw.decode("utf-8")


def test_make_consumption_v1_reproduces_the_shipped_files(tmp_path, capsys):
    import importlib.util

    path = PKG / "scenes" / "make_consumption_v1.py"
    spec = importlib.util.spec_from_file_location("dm_eval_make_consumption_v1", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    files = mod.render_files()
    assert files == mod.render_files()  # 決定的
    assert set(files) == {"consumption_v1.jsonl", "consumption_v1.b0.json", "consumption_v1.md5"}
    for name, raw in files.items():  # 同梱の 3 本とバイトで同じ(jsonl が正・スクリプトは再現用)
        assert raw == (PKG / "scenes" / name).read_bytes(), name
    want = {n: hashlib.md5(files[n]).hexdigest() for n in ("consumption_v1.jsonl", "consumption_v1.b0.json")}
    assert S.read_md5_list(files["consumption_v1.md5"]) == want
    assert mod.main([str(tmp_path / "o")]) == 0 and mod.main([]) == 2
    assert {p.name: p.read_bytes() for p in (tmp_path / "o").iterdir()} == files
    src = path.read_text(encoding="utf-8")
    assert _banned_identifiers(src) == [] and "C:\\" not in src and "/Users/" not in src
    capsys.readouterr()


def test_consumption_scene_md5_mismatch_stops_reading(tmp_path):
    for name in ("consumption_v1.jsonl", "consumption_v1.b0.json", "consumption_v1.md5"):
        shutil.copyfile(SCENES.with_name(name), tmp_path / name)
    p = tmp_path / "consumption_v1.jsonl"
    p.write_bytes(p.read_bytes().replace("おにぎり".encode("utf-8"), "おむすび".encode("utf-8"), 1))
    with pytest.raises(ValueError, match="md5"):
        S.load_scene_file(p)
    assert len(S.load_scene_file(p, verify_md5=False).situations) == 44  # 照らさなければ読める(写しの試し)
    with pytest.raises(S.EvalsetMissing):
        S.load_scene_file(tmp_path / "none.jsonl")


def _scene_row(**over):
    row = {"sid": "t-1", "point": "buy_or_skip", "lang": "ja", "b0_id": "b", "input_text": "[B1 種別] あなたは来街者です。",
           "facts": {"hour": 9, "minute": 0}, "strata": {"kind": "来街者"},
           "candidates": [{"id": "buy", "kind": "購入", "text": "買う", "source": "affordance", "qty": 1},
                          {"id": "skip", "kind": "buy_skip", "text": "見送る", "source": "continue"}]}
    row.update(over)
    return row


def _write_scene(d: Path, rows: list[dict]) -> Path:
    d.mkdir(parents=True, exist_ok=True)
    p = d / "x.jsonl"
    p.write_bytes(("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n").encode("utf-8"))
    (d / "x.b0.json").write_bytes(json.dumps({"b0_texts": {"b": "[合成] 前置き"}}).encode("utf-8"))
    return p


def test_scene_loader_rejects_bad_rows(tmp_path):
    ok = S.load_scene_file(_write_scene(tmp_path / "ok", [_scene_row()]), verify_md5=False)
    assert [c.id for c in ok.candidates["t-1"]] == ["buy", "skip"] and ok.fields["t-1"]["buy"] == {"qty": 1}
    assert all(c.number is None for c in ok.candidates["t-1"]) and ok.situations[0].blocks["B0"] == "[合成] 前置き"
    bad = [
        _scene_row(point="no_such_point"),
        _scene_row(candidates=[{"id": "a", "kind": "購入", "text": "買う", "source": "affordance"}] * 2),
        _scene_row(candidates=[{"id": "a", "kind": "購入", "text": "買う", "source": "affordance", "color": "red"}]),
        _scene_row(candidates=[{"id": "a", "kind": "購入", "text": "買う", "source": "affordance", "qty": 0}]),
        _scene_row(candidates=[{"id": "a", "kind": "購入", "text": "買う", "source": "no_such_source"}]),
        _scene_row(candidates=[]),
    ]
    for i, row in enumerate(bad):
        with pytest.raises(ValueError):
            S.load_scene_file(_write_scene(tmp_path / f"b{i}", [row]), verify_md5=False)
    with pytest.raises(ValueError):  # 場面の id の重なり
        S.load_scene_file(_write_scene(tmp_path / "dup", [_scene_row(), _scene_row()]), verify_md5=False)
    with pytest.raises(ValueError):
        S.read_md5_list(b"not-a-md5 x.jsonl\n")


def test_consumption_scenes_shape_and_new_words(scenes):
    from shibuya.llm.contract import cross_action_words

    v3 = set(cross_action_words(S.CONSUMPTION_VOCAB_VERSION))
    words_by_point = {p: set() for p in S.DECISION_POINTS}
    for s in scenes.situations:
        point = scenes.points[s.sid]
        assert s.sid.startswith(f"cons-v1-{point}-") and s.lang == "ja" and s.missing == ("B5",)
        assert tuple(b for b in S.BLOCK_ORDER if b in s.blocks) == ("B0", "B1", "B2", "B3", "B4", "B4b", "B6")
        assert s.facts["decision_point"] == point and s.tape_output == ""
        assert set(s.strata) == EVALSET_STRATA_KEYS  # 1-10 と同じ鍵
        lo = (s.facts["hour"] // 4) * 4
        assert s.strata["time_band"] == f"{lo:02d}-{lo + 3:02d}"  # 1-10 と同じ区切り
        assert f"[B3 時刻] 現在時刻は{s.facts['hour']}時{s.facts['minute']}分です。" in s.blocks["B3"]
        b6 = s.blocks["B6"]
        assert f"所持金は{s.facts['money_yen']}円です。" in b6 and f"[B6 体] {s.facts['hunger']}" in b6
        cs = scenes.candidates[s.sid]
        assert len(cs) == 6 and len({c.id for c in cs}) == 6 and cs[-1].kind == "よく考える"
        assert {c.source for c in cs} <= set(ALL_SOURCES)
        kinds = {c.kind for c in cs}
        assert kinds <= v3 | set(S.CONSUMPTION_WORDS) | {"よく考える"} and "待機" not in kinds  # 語彙 v3
        for c in cs:
            if c.kind in S.CONSUMPTION_WORDS:
                assert c.text.startswith(S.CONSUMPTION_WORD_LABELS[c.kind] + "(")  # 表示は routing §5 の語
        words_by_point[point] |= kinds
        f = scenes.fields[s.sid]
        for cid, fv in f.items():
            assert set(fv) <= set(S.CANDIDATE_FIELD_KEYS)
            if "price_yen" in fv:
                assert fv["price_yen"] > 0 and fv["price_yen"] % 50 == 0  # 丸い仮の値
        for it in s.facts["items"]:
            assert it["price_yen"] % 50 == 0
        assert s.facts["money_yen"] % 100 == 0
        if point == "what_how_many":
            qty = sorted(fv["qty"] for fv in f.values() if "qty" in fv and fv.get("item") == s.facts["items"][0]["name"])
            assert len(qty) == 3 and len(set(qty)) == 3 and qty == sorted(s.facts["qty_options"])
            assert all(isinstance(q, int) and q >= 1 for q in qty)
    assert {"購入", "buy_skip"} <= words_by_point["buy_or_skip"]
    assert {"購入", "buy_skip"} <= words_by_point["what_how_many"]
    assert "price_skip" in words_by_point["price_skip"]
    assert {"revisit", "no_revisit"} <= words_by_point["revisit"]
    assert set(S.CONSUMPTION_WORDS) <= set().union(*words_by_point.values())
    assert not set(S.CONSUMPTION_WORDS) & (set(S.VOCAB) | v3)  # 語彙の外の語・電車の「見送る」とぶつからない名
    assert "見送る" not in set().union(*words_by_point.values())
    raw = SCENES.read_bytes().decode("utf-8")
    assert '"tick"' not in raw and "[B5" not in raw


def test_consumption_scenes_use_no_real_names():
    texts = [SCENES.read_bytes().decode("utf-8"), SCENES.with_name("consumption_v1.b0.json").read_bytes().decode("utf-8")]
    for name in REAL_NAMES:
        assert all(name not in t for t in texts), name


def test_consumption_render_short_and_long(scenes):
    s = scenes.situations[0]
    pres = S.orders(scenes.candidates[s.sid], s.sid, n_orders=1, seed="t")[0]
    short = S.render(s, pres, length="short", arm="t1000").text
    long_ = S.render(s, pres, length="long", arm="t1000").text
    assert short == compose(S.arm_blocks(s, "t1000"), pres, length="short")
    assert "[B6 起床]" in short and "[B6 所持] 所持金は" in short and "[B6 体]" in short  # 判断の事実は短い版に入る
    assert long_.startswith(short + "\n") and "[B5" not in long_  # 長い版=短い版+指示
    assert "7. その他" in short and "1. " in short  # 6 候補+その他
    for sc_ in scenes.situations:  # 全 44 件: 所持金・体・事情は短い版に入る
        p = S.orders(scenes.candidates[sc_.sid], sc_.sid, n_orders=1, seed="t")[0]
        txt = S.render(sc_, p, length="short", arm="t300").text
        assert "所持金は" in txt and "[B6 体]" in txt
        if "[B6 事情]" in S.render(sc_, p, length="long", arm="t300").text:
            assert "[B6 事情]" in txt


# ---------------------------------------------------------------------- 偽の口
_OPT = re.compile(r"^(\d+)\. (.*)$")


def _options_of(prompt: str) -> dict[str, str]:
    return {m.group(1): m.group(2) for m in (_OPT.match(ln) for ln in prompt.split("\n")) if m}


def _h(text: str) -> float:
    return -(int(hashlib.md5(text.encode("utf-8")).hexdigest()[:6], 16) % 997) / 100.0


class _ContentBackend(BB.ChoiceBackend):
    """中身だけで決まる偽の口: 番号の文字列は文の提示の行から見せ方の文に戻してから hash で logprob。"""

    name = "fake_content"
    uses_gpu = True

    def continuation_logprobs(self, prompt, continuations):
        opts = _options_of(prompt)
        out = []
        for c in continuations:
            body = opts.get(c, c)
            out.append(tuple(_h(body + str(i)) for i in range(1 + len(body) % 3)))  # トークンの数も中身で決める
        return out


class _PositionalBackend(BB.ChoiceBackend):
    """番号の小さい物ほど高い偽の口(位置の偏りの正の対照)。"""

    name = "fake_positional"

    def continuation_logprobs(self, prompt, continuations):
        return [(-float(c),) if c.isdigit() else (-1.0,) for c in continuations]


class _NoisyBackend(BB.ChoiceBackend):
    """呼ぶたびに値が揺れる偽の口(決定論の検査の負の対照)。"""

    name = "fake_noisy"

    def __init__(self):
        self.calls = [0]

    def continuation_logprobs(self, prompt, continuations):
        self.calls[0] += 1
        return [(_h(c) + 0.001 * (self.calls[0] % 5),) for c in continuations]


class _FreeText(BB.FreeTextBackend):
    """状況の文の時刻で答えを変える偽の自由記述: 分が 0 か 5 で終わる状況は候補に当たらない文。"""

    name = "fake_free"

    def generate(self, prompt):
        m = re.search(r"現在時刻は(\d+)時(\d+)分", prompt)
        if m and int(m.group(2)) % 5 == 0:
            return "うーん、よく分からない気分です。"
        return "理由: 合成の答え\n2"


def test_softmax_and_forms():
    d = BB.softmax_dist({"a": math.log(0.2), "b": math.log(0.6), "c": float("-inf"), "d": math.log(0.2)})
    assert d["b"] == pytest.approx(0.6) and d["c"] == 0.0 and sum(d.values()) == pytest.approx(1.0)
    with pytest.raises(BB.BackendError):
        BB.softmax_dist({"a": float("-inf")})
    with pytest.raises(BB.BackendError):
        BB.softmax_dist({"a": float("nan")})
    pres = _presented(SYN[0])
    num = BB.FORMS["choice_number"].continuations(pres)
    assert [c for _i, c in num] == [str(k) for k in range(1, 15)] and num[-1][0] == OTHER_ID
    txt = BB.FORMS["score_text_sum"].continuations(pres)
    assert [c for _i, c in txt][:-1] == [c.text for c in sorted(pres, key=lambda c: c.number)]
    assert txt[-1] == (OTHER_ID, OTHER_TEXT)
    no_other = BB.ChoiceForm("x", BB.FORM_CHOICE, "number", "sum", include_other=False, suffix="\n")
    assert [c for _i, c in no_other.continuations(pres)][0] == "1\n" and len(no_other.continuations(pres)) == 13
    assert BB.FORMS["score_text_mean"].reduce_lps((-1.0, -3.0)) == -2.0
    assert BB.FORMS["score_text_sum"].reduce_lps((-1.0, -3.0)) == -4.0
    assert BB.FORMS["choice_number_first"].reduce_lps((-1.0, -3.0)) == -1.0
    for bad in (dict(form="Noul"), dict(target="kind"), dict(reduce="max"), dict(wrap="xml")):
        kw = dict(name="b", form=BB.FORM_CHOICE, target="number", reduce="sum")
        kw.update(bad)
        with pytest.raises(ValueError):
            BB.ChoiceForm(**kw)
    with pytest.raises(ValueError):  # 番号の無い候補
        BB.FORMS["choice_number"].continuations(S.candidates_for(SYN[0]))
    assert BB.wrap_prompt("文", "plain") == "文\n"
    w = BB.wrap_prompt("文", "chatml_nothink")
    assert w.startswith("<|im_start|>user\n文<|im_end|>") and w.endswith("<think>\n\n</think>\n\n")
    assert set(BB.FORMS) == {"choice_number", "choice_number_first", "score_text_sum", "score_text_mean"}
    assert {f.form for f in BB.FORMS.values()} == {BB.FORM_CHOICE, BB.FORM_SCORE}


def test_logprob_scorer_distribution_shape_and_determinism():
    for form in BB.FORMS:
        sc = BB.LogprobChoiceScorer(_ContentBackend(), form)
        assert sc.implemented and sc.reads_text and sc.uses_gpu and sc.form in (BB.FORM_CHOICE, BB.FORM_SCORE)
        for s in SYN[:3]:
            pres = _presented(s)
            text = S.render(s, pres, length="short", arm="t300").text
            d = sc.score(s, pres, text=text)
            assert set(d) == {c.id for c in pres} | {OTHER_ID} and sum(d.values()) == pytest.approx(1.0)
            assert all(v >= 0 for v in d.values())
            assert J.dist_digest([d]) == J.dist_digest([sc.score(s, pres, text=text)])
        with pytest.raises(ValueError):
            sc.score(SYN[0], _presented(SYN[0]), text=None)  # 文の要る当て口
        with pytest.raises(AttributeError):
            sc.backend = _PositionalBackend()  # 作った後に付け替えない
    first = BB.LogprobChoiceScorer(_PositionalBackend(), "choice_number_first")
    pres = _presented(SYN[0])
    d = first.score(SYN[0], pres, text=S.render(SYN[0], pres, length="short", arm="t300").text)
    assert J.top1(d) == next(c.id for c in pres if c.number == 1)
    json.dumps(BB.LogprobChoiceScorer(_ContentBackend()).describe(), ensure_ascii=False)


def _orders_of(sits, cands=None, n_orders=4):
    return {s.sid: S.orders(cands[s.sid] if cands else S.candidates_for(s), s.sid, n_orders=n_orders, seed="t")
            for s in sits}


def test_backend_scorers_position_bias_content_vs_positional(scenes):
    sits = scenes.situations
    ords = _orders_of(sits, scenes.candidates)
    content, _ = B.score_orders(BB.LogprobChoiceScorer(_ContentBackend(), "choice_number"), sits, ords, arm="t300")
    pb = B.position_bias(content)
    assert pb["top1_change_rate"] == 0.0 and pb["self_consistency_2"] == 1.0  # 中身だけ=位置の偏りなし
    posi, _ = B.score_orders(BB.LogprobChoiceScorer(_PositionalBackend(), "choice_number"), sits, ords, arm="t300")
    pp = B.position_bias(posi)
    assert pp["number1_rate"] == 1.0 and pp["top1_change_rate"] == 1.0  # 正の対照
    assert pp["pbs_by_n"]["6"]["pbs"] == pytest.approx(math.sqrt(1 - 1 / 6))


def test_free_text_matcher_on_consumption_answers(scenes):
    def pres_of(sid):
        return S.orders(scenes.candidates[sid], sid, n_orders=1, seed="t")[0]

    m = BB.match_free_text
    p = pres_of("cons-v1-what_how_many-01")
    assert m("クロワッサンを2つ買います。", p) == "a2" and m("食パンを1つ買った", p) == "b1"
    assert m("クロワッサン 2 個にします", p) is None  # 空白入りの数は番号でない
    assert m("1位は食パン", p) is None  # 順位は番号でない
    assert m("今回は見送ります", p) == "skip"
    p = pres_of("cons-v1-price_skip-05")
    assert m("高いのでやめます", p) == "price_skip" and m("安いほうを買います", p) == "cheaper"
    assert m("別の店で探します", p) == "elsewhere"
    p = pres_of("cons-v1-revisit-01")
    assert m("また来ます", p) == "again" and m("もう行かない", p) == "not_again" and m("また行きます", p) == "again"
    assert m("次は別の店にします", p) == "not_again" and m("少し休みます", p) == "wait"
    p = pres_of("cons-v1-buy_or_skip-01")
    assert m("おにぎりを買います", p) == "buy" and m("店員に尋ねます", p) == "ask"
    assert m("もう少し見て回ります", p) == "look" and m("よく考えます", p) == "deliberate"
    assert m("何も思いつかない気分です", p) is None
    assert {"買います", "買った", "買って"} <= BB.verb_forms("買う") and "探します" in BB.verb_forms("探す")
    assert {"来ます", "来た"} <= BB.verb_forms("来る") and "行きません" in BB.verb_forms("行かない")
    assert "やめます" in BB.verb_forms("やめる")


def test_free_text_negative_answers_do_not_hit_the_opposite_candidate(scenes):
    def pres_of(sid):
        return S.orders(scenes.candidates[sid], sid, n_orders=1, seed="t")[0]

    m = BB.match_free_text
    rv = pres_of("cons-v1-revisit-01")
    assert m("もう来ない", rv) == "not_again"  # 前は again(また行く)に当たった
    assert m("この店には来ないと思う", rv) == "not_again"
    assert m("また来ます", rv) == "again"
    by = pres_of("cons-v1-buy_or_skip-01")
    assert m("買いません", by) == "skip" and m("買いません", by) != "buy"
    assert m("おにぎりは買わない", by) == "skip" and m("おにぎりを買います", by) == "buy"
    assert m("店員には尋ねない", by) is None  # 対応する否定の候補が無い否定=破綻
    assert m("買いません", pres_of("cons-v1-price_skip-05")) == "price_skip"
    assert m("迷わずに安いほうを買います", pres_of("cons-v1-price_skip-05")) == "cheaper"  # 肯定の側
    assert m("買いません", rv) is None  # 否定の候補はあるが対応しない(revisit の場面に購入は無い)
    for w, neg in (("来る", "来ない"), ("する", "しない"), ("買う", "買いません"), ("やめる", "やめませんでした")):
        assert neg not in BB.verb_forms(w) and neg in BB.negative_forms(w)  # 肯定の形に否定を入れない
    assert BB.negative_forms("行かない") == frozenset()


def test_free_text_kanji_numbers(scenes):
    m = BB.match_free_text
    p = S.orders(scenes.candidates["cons-v1-what_how_many-01"], "cons-v1-what_how_many-01", n_orders=1, seed="t")[0]
    assert m("クロワッサンを二つ買います", p) == "a2"
    p3 = S.orders(scenes.candidates["cons-v1-what_how_many-03"], "cons-v1-what_how_many-03", n_orders=1, seed="t")[0]
    assert m("りんごを三個買います", p3) == "a3"
    assert BB.kanji_number("二十三") == 23 and BB.kanji_number("十") == 10 and BB.kanji_number("一緒") is None
    assert BB.normalize_text("二つと 三個、一緒") == "2つと3つ、一緒"  # 助数詞の前だけ読む


def test_free_text_matcher():
    pres = _presented(SYN[0])  # 13 候補+その他=14
    by_num = {c.number: c.id for c in pres}
    m = BB.match_free_text
    assert m("理由: 合成\n3", pres) == by_num[3]
    assert m("300円なので 5", pres) == by_num[5]
    assert m("答えは１２です", pres) == by_num[12]  # 全角の数字
    assert m("14", pres) == OTHER_ID and m("その他(自由に書く)", pres) == OTHER_ID
    assert m("2つ買うことにします", pres) is None  # 数量の数は番号に読まない
    assert m("99", pres) is None and m("", pres) is None and m("気分が乗らない", pres) is None
    one = next(c for c in pres if c.kind == "就寝")
    assert m(f"今日は{one.text}", pres) == one.id
    assert m("就寝 にする", pres) == one.id  # 語がちょうど 1 つの候補に当たる
    two = [c for c in pres if c.source == "vocab" and c.text == c.kind][:2]
    assert len(two) == 2 and m(f"行動: {two[0].text} か {two[1].text}", pres) is None  # 2 つに当たる=当たらない


def test_free_text_scorer_trace_and_breakdown_rate():
    sc = BB.FreeTextScorer(_FreeText())
    assert sc.form == BB.FORM_NOUL and sc.prompt_length == "long" and sc.reads_text
    for s in SYN:
        pres = _presented(s)
        d = sc.score(s, pres, text=S.render(s, pres, length="long", arm="t300").text)
        assert sum(d.values()) == pytest.approx(1.0) and max(d.values()) == 1.0
    want = sum(1 for s in SYN if s.facts["minute"] % 5 == 0)
    t = sc.trace_summary()
    assert t["n"] == len(SYN) and t["breakdown"] == want and t["breakdown_rate"] == pytest.approx(want / len(SYN))
    assert t["other_explicit"] == 0  # 破綻は明示の「その他」に数えない(2 回数えない)
    sc.trace_reset()
    assert sc.trace_summary()["n"] == 0 and sc.trace_summary()["breakdown_rate"] is None


class _OtherFree(BB.FreeTextBackend):
    name = "fake_other"

    def generate(self, prompt):
        return "その他(自由に書く)"


def test_free_text_explicit_other_is_not_breakdown():
    sc = BB.FreeTextScorer(_OtherFree())
    for s in SYN[:3]:
        pres = _presented(s)
        assert sc.score(s, pres, text="文")[OTHER_ID] == 1.0
    t = sc.trace_summary()
    assert t["breakdown"] == 0 and t["other_explicit"] == 3 and t["other_explicit_rate"] == 1.0


class _LowMass(BB.ChoiceBackend):
    """候補の確率の和が下限より小さい偽の口(logprob の形の破綻)。"""

    name = "fake_low"

    def continuation_logprobs(self, prompt, continuations):
        return [(-20.0,) for _c in continuations]


class _Boundary(BB.ChoiceBackend):
    name = "fake_boundary"

    def continuation_logprobs(self, prompt, continuations):
        raise BB.TokenBoundaryError("合成の不一致")


def test_logprob_breakdown_low_mass_and_boundary():
    pres = _presented(SYN[0])
    low = BB.LogprobChoiceScorer(_LowMass(), "choice_number")
    d = low.score(SYN[0], pres, text="文")
    assert sum(d.values()) == pytest.approx(1.0)  # 分布は作るが破綻に数える
    t = low.trace_summary()
    assert t["breakdown"] == 1 and t["low_mass"] == 1 and t["mass_floor"] == BB.MASS_FLOOR == 1e-3
    ok = BB.LogprobChoiceScorer(_PositionalBackend(), "choice_number")
    ok.score(SYN[0], pres, text="文")
    assert ok.trace_summary()["breakdown"] == 0 and ok.trace_summary()["mass_median"] > 1e-3
    bd = BB.LogprobChoiceScorer(_Boundary(), "choice_number")
    with pytest.raises(J.ScoreFailed):
        bd.score(SYN[0], pres, text="文")
    assert bd.trace_summary()["boundary"] == 1 and bd.trace_summary()["breakdown_rate"] == 1.0
    assert issubclass(BB.BackendError, J.ScoreFailed) and issubclass(BB.BackendUnavailable, J.ScoreFailed)


class _Flaky(J.Scorer):
    """呼ぶたびに重みが変わる当て口(箱の中の数=欄は付け替えない)=決定論の検査の負の対照。"""

    name = "flaky"

    def __init__(self) -> None:
        self.calls = [0]
        super().__init__()

    def _score(self, situation, candidates, text):
        self.calls[0] += 1
        return {c.id: 1.0 + 0.01 * ((self.calls[0] + int(c.number or 0)) % 3) for c in candidates}


def test_determinism_check_repeats():
    items = [(s, _presented(s), None) for s in SYN]
    r = J.determinism_check(J.MockScorer, items)
    assert r["n_repeats"] == J.DETERMINISM_REPEATS == 32 and r["item_agree_rate"] == 1.0
    assert r["top1_agree_rate"] == 1.0 and r["n_items"] == len(SYN) and r["seeds_needed"] is None
    f = J.determinism_check(_Flaky, items, repeats=5)
    assert f["item_agree_rate"] == 0.0 and f["distinct_max"] > 1 and f["n_repeats"] == 5
    g = J.determinism_check(J.GScorer, items)
    assert g["status"] == "GPU の後(S6)" and g["item_agree_rate"] is None
    with pytest.raises(ValueError):
        J.determinism_check(J.MockScorer, items, repeats=1)
    s32 = J.strict_check(J.MockScorer, items, repeats=32)
    assert s32["identical_repeat"] is True and s32["identical_reordered"] is True
    assert set(s32) == set(J.strict_check(J.MockScorer, items))  # 回数を変えても欄の形は同じ
    with pytest.raises(ValueError):
        J.strict_check(J.MockScorer, items, repeats=1)
    noisy_sc = BB.LogprobChoiceScorer(_NoisyBackend(), "choice_number")
    texts = [(s, p, S.render(s, p, length="short", arm="t300").text) for s, p, _t in items]
    nd = J.determinism_check(lambda: noisy_sc, texts, repeats=6)
    assert nd["item_agree_rate"] < 1.0


def _g_factories(free=False):
    fx = list(C.default_factories())
    fx[3] = lambda: BB.LogprobChoiceScorer(_ContentBackend(), "choice_number", name="g_fake", role=J.ROLE_BASELINE)
    if free:
        fx.append(lambda: BB.FreeTextScorer(_FreeText(), name="noul_fake"))
    return tuple(fx)


@pytest.fixture(scope="module")
def g_result():
    return C.evaluate(SYN, {s.sid: ("移動",) for s in SYN[:4]}, seed="t", n_orders=4,
                      scorer_factories=_g_factories(free=True), g_name="g_fake", determinism_repeats=4)


def test_compare_section_is_outside_the_golden_digest(syn_result):
    again = C.evaluate(SYN, {s.sid: ("移動",) for s in SYN[:4]}, seed="t", n_orders=4, determinism_repeats=3)
    assert again["digest"] == syn_result["digest"] and again["compare_digest"] != syn_result["compare_digest"]
    off = C.evaluate(SYN, {s.sid: ("移動",) for s in SYN[:4]}, seed="t", n_orders=4, compare=False)
    assert off["digest"] == syn_result["digest"] and "compare" not in off
    cmp = syn_result["compare"]
    assert cmp["schema"] == C.COMPARE_SCHEMA and cmp["determinism_repeats"] == 32 and cmp["material"] == "evalset"
    assert cmp["g_reference"] == "g_first_token" and cmp["g_status"] == "GPU の後(S6)"
    assert cmp["scorers"]["mock"]["determinism"]["item_agree_rate"] == 1.0
    assert cmp["scorers"]["kev_9b"]["determinism"]["status"] == "GPU の後(S6)"
    assert all(v["vram_gb"] is None for v in cmp["scorers"].values())
    assert cmp["scorers"]["mock"]["failures"]["t300"] == {"n": 0, "items": []}
    assert syn_result["scene_set"] == "evalset" and syn_result["material"] == "evalset"
    tagged = C.evaluate(SYN, {s.sid: ("移動",) for s in SYN[:4]}, seed="t", n_orders=4, scene_set="both",
                        determinism_repeats=2)
    assert tagged["scene_set"] == "both" and tagged["digest"] == syn_result["digest"]  # SCHEMA と digest は据え置き
    assert syn_result["schema"] == dm_eval.SCHEMA


def test_table_new_columns_and_old_columns_kept(syn_result):
    assert T.COLUMN_KEYS == OLD_COLUMN_KEYS + NEW_COLUMN_KEYS  # 既存の列の位置を変えず、新しい列は末尾
    assert dict(T.COLUMNS)["wall_s_per_item"] == "1 件の壁時計(秒・CPU)"  # 見出しも元のまま
    rows = syn_result["table"]["rows"]
    by = {(r["scorer"], r["arm"]): r for r in rows}
    bl = {(r["scorer"], r["arm"]): b for r, b in zip(rows, T.blanks_of(rows))}
    m = by[("mock", "t300")]
    assert m["form"] == "規則" and m["determinism_rate"] == 1.0 and m["determinism_repeats"] == 32
    assert by[("tape", "t300")]["form"] == "記録"
    assert bl[("mock", "t300")]["vram_gb"] == T.BLANK_NO_GPU
    assert bl[("mock", "t300")]["breakdown_rate"] == T.BLANK_NOT_MODEL
    assert bl[("mock", "t300")]["top1_agree_vs_g"] == T.BLANK_GPU
    assert all(bl[("mock", "t300")][c] == T.BLANK_NO_QTY for c in T.QTY_COLUMNS)  # 1-10 に数の候補は無い
    k = bl[("kev_9b", "t300")]
    assert all(k[c] == T.BLANK_GPU for c in NEW_COLUMN_KEYS)
    foot = syn_result["table"]["footnotes"]
    assert any(f.startswith("分布の広がり") for f in foot) and any(f.startswith("決定論=同一入力 32 回") for f in foot)


def test_evaluate_with_g_reference_and_free_text(g_result):
    rows = g_result["table"]["rows"]
    by = {(r["scorer"], r["arm"]): r for r in rows}
    bl = {(r["scorer"], r["arm"]): b for r, b in zip(rows, T.blanks_of(rows))}
    assert g_result["compare"]["g_status"] == "検査済み"
    for arm in S.LENGTH_ARMS:
        m = by[("mock", arm)]
        assert m["jsd_vs_g"] is not None and 0.0 <= m["jsd_vs_g"] <= 1.0 and m["top1_agree_vs_g"] is not None
        g = by[("g_fake", arm)]
        assert g["form"] == BB.FORM_CHOICE and bl[("g_fake", arm)]["jsd_vs_g"] == T.BLANK_SELF
        assert bl[("g_fake", arm)]["vram_gb"] == T.BLANK_GPU and bl[("g_fake", arm)]["tokens_in"] == T.BLANK_GPU
        assert g["top1_change_rate"] == 0.0  # 中身だけで決まる偽の (G)
        n = by[("noul_fake", arm)]
        want = sum(1 for s in SYN if s.facts["minute"] % 5 == 0) / len(SYN)
        assert n["form"] == BB.FORM_NOUL and n["breakdown_rate"] == pytest.approx(want)
        assert n["other_rate"] == 0.0  # Noul の行のその他の率=明示の「その他」だけ(破綻を入れない)
        assert "壁時計は GPU の口の実測" in n["notes"]
        assert g["breakdown_rate"] is not None and 0.0 <= g["breakdown_rate"] <= 1.0
    e = {x["describe"]["name"]: x for x in g_result["scorers"]}
    assert e["mock"]["by_arm"]["t300"]["agreement_vs_g"]["n"] == len(SYN)
    assert e["g_fake"]["by_arm"]["t300"]["agreement_vs_g"] is None
    assert e["g_fake"]["by_arm"]["t300"]["speed"]["wall_clock_device"] == "GPU"
    st = {x["name"]: x for x in g_result["strict"]}
    assert st["g_fake"]["identical_repeat"] is True and st["g_fake"]["identical_reordered"] is True
    assert g_result["compare"]["scorers"]["noul_fake"]["determinism"]["item_agree_rate"] == 1.0


def test_classical_scorer_splits_same_kind_mass_and_ignores_order(scenes):
    cl = J.ClassicalScorer(vocab_version=S.CONSUMPTION_VOCAB_VERSION)
    assert "なし" in cl.words and "待機" not in cl.words
    assert J.ClassicalScorer().words == tuple(J.ClassicalScorer(vocab_version=S.VOCAB_VERSION).words)
    changed = 0
    for s in scenes.situations:
        ords = S.orders(scenes.candidates[s.sid], s.sid, n_orders=4, seed="t")
        ds = [cl.score(s, p) for p in ords]
        changed += any(d != ds[0] for d in ds[1:])
        buys = [c.id for c in ords[0] if c.kind == "購入"]
        if len(buys) > 1:
            assert len({ds[0][b] for b in buys}) == 1  # 同じ語の候補は等分
    assert changed == 0  # 並びで分布が変わらない(前は 44 件中 20 件で変わった)


class _FailSome(BB.ChoiceBackend):
    """分が 0 か 5 で終わる状況だけ口の後ろが落ちる偽の口(失敗を場面ごとに記録する試験)。"""

    name = "fake_fail"

    def continuation_logprobs(self, prompt, continuations):
        m = re.search(r"現在時刻は(\d+)時(\d+)分", prompt)
        if m and int(m.group(2)) % 5 == 0:
            raise BB.BackendError("合成の失敗")
        return [(_h(c),) for c in continuations]


def test_backend_failures_are_recorded_per_scene_and_do_not_stop_the_run():
    fx = list(C.default_factories())
    fx.append(lambda: BB.LogprobChoiceScorer(_FailSome(), "choice_number", name="fails"))
    res = C.evaluate(SYN, None, seed="t", n_orders=4, scorer_factories=fx, determinism_repeats=2)
    want = sorted(s.sid for s in SYN if s.facts["minute"] % 5 == 0)
    f = res["compare"]["scorers"]["fails"]["failures"]["t300"]
    assert f["n"] == len(want) and sorted(x["sid"] for x in f["items"]) == want
    assert all(x["error"] == "BackendError" and x["message"] == "parse" for x in f["items"])
    assert "合成の失敗" not in json.dumps(res, ensure_ascii=False)  # 例外の文は記録に写さない
    e = {x["describe"]["name"]: x for x in res["scorers"]}
    assert e["fails"]["by_arm"]["t300"]["position_bias"]["n_situations"] == len(SYN) - len(want)
    st = {x["name"]: x for x in res["strict"]}
    assert st["fails"]["status"] == "失敗" and res["compare"]["scorers"]["fails"]["determinism"]["status"] == "失敗"
    assert st["fails"]["message"] == "parse" and set(J.failure_record(BB.TokenBoundaryError("x"))) == {"error", "message"}
    assert J.failure_record(BB.TokenBoundaryError("入力の文")) == {"error": "TokenBoundaryError", "message": "boundary"}
    row = next(r for r in res["table"]["rows"] if r["scorer"] == "fails")
    assert f"失敗 {len(want)} 場面" in row["notes"]
    with pytest.raises(J.ScoreFailed):  # 箱を渡さなければ今のまま上がる
        B.score_orders(fx[-1](), SYN, _orders_of(SYN), arm="t300")


def test_qty_measures_on_what_how_many(scenes):
    fx = [f for i, f in enumerate(C.default_factories()) if i != 2]
    fx[0] = lambda: J.MockScorer("dm61-mock")
    fx[2] = lambda: BB.LogprobChoiceScorer(_ContentBackend(), "choice_number", name="g_fake", role=J.ROLE_BASELINE)
    res = C.evaluate(scenes.situations, None, candidates=scenes.candidates, material="consumption",
                     points=scenes.points, scorer_factories=fx, g_name="g_fake", determinism_repeats=2,
                     vocab_version=S.CONSUMPTION_VOCAB_VERSION, fields=scenes.fields)
    q = res["compare"]["scorers"]["mock"]["qty"]["t300"]
    assert q["n"] == 11 and 1.0 <= q["qty_mean"] <= 6.0 and q["agree_vs_g"] is not None
    assert 0.0 <= q["agree_vs_g"] <= 1.0 and q["absdiff_vs_g"] >= 0.0
    gq = res["compare"]["scorers"]["g_fake"]["qty"]["t300"]
    assert gq["agree_vs_g"] is None and gq["qty_mean"] is not None
    rows = {(r["scorer"], r["arm"]): r for r in res["table"]["rows"]}
    bl = {(r["scorer"], r["arm"]): b for r, b in zip(res["table"]["rows"], T.blanks_of(res["table"]["rows"]))}
    assert rows[("mock", "t300")]["qty_mean"] == pytest.approx(q["qty_mean"])
    assert rows[("mock", "t300")]["qty_agree_vs_g"] == pytest.approx(q["agree_vs_g"])
    assert bl[("g_fake", "t300")]["qty_agree_vs_g"] == T.BLANK_SELF
    # 手で: 期待値の式
    d = {"a1": 0.5, "a2": 0.25, "x": 0.25}
    hand = C.qty_measures({"s": d}, {"s": {"a1": {"qty": 1}, "a2": {"qty": 3}}})
    assert hand["qty_mean"] == pytest.approx((0.5 * 1 + 0.25 * 3) / 0.75) and hand["agree_vs_g"] is None
    assert C.qty_measures({"s": d}, {"s": {"a1": {"qty": 1}, "x": {"qty": 1}}})["n"] == 0  # 数が 1 通り=数えない


def test_evaluate_consumption_scenes(scenes):
    fx = [f for i, f in enumerate(C.default_factories()) if i != 2]  # テープを外す
    fx.append(lambda: BB.LogprobChoiceScorer(_ContentBackend(), "score_text_mean", name="fake_score"))
    res = C.evaluate(scenes.situations, None, candidates=scenes.candidates, material="consumption",
                     points=scenes.points, scorer_factories=fx, determinism_repeats=3)
    assert res["material"] == "consumption" and res["scene_set"] == "consumption"
    assert res["n_situations"] == 44 and res["candidates"]["n_candidates"] == {"6": 44}
    assert res["tape_fixed_order"] is None and res["limits"] == list(C.CONSUMPTION_LIMITS)
    assert res["compare"]["by_point"] == {p: 11 for p in S.DECISION_POINTS} and res["compare"]["material"] == "consumption"
    assert res["table"]["missing_refs"] == ["tape"]
    rows = res["table"]["rows"]
    assert "tape" not in {r["scorer"] for r in rows}
    bl = {(r["scorer"], r["arm"]): b for r, b in zip(rows, T.blanks_of(rows, missing_refs=["tape"]))}
    assert bl[("mock", "t300")]["jsd_vs_tape"] == T.BLANK_NO_REF
    by = {(r["scorer"], r["arm"]): r for r in rows}
    assert by[("fake_score", "t300")]["top1_change_rate"] == 0.0 and by[("fake_score", "t300")]["form"] == "Score"
    assert res["controls"]["first_number"]["position_bias"]["number1_rate"] == 1.0
    assert not any("構成上 0" in f for f in res["table"]["footnotes"])
    with pytest.raises(ValueError):
        C.evaluate(scenes.situations, None, candidates=scenes.candidates, material="other")


# ---------------------------------------------------------------------- (b) vLLM の口(HTTP は偽の接続)
def _fake_http(monkeypatch, responder, status=200):
    calls = []

    class _Resp:
        def __init__(self, body):
            self.status = status
            self._body = body

        def read(self):
            return self._body

    class _Conn:
        def __init__(self, host, port, timeout=None):
            self.host, self.port, self.timeout = host, port, timeout
            calls.append(self)

        def request(self, method, path, body=None, headers=None):
            self.method, self.path, self.headers = method, path, dict(headers or {})
            self.payload = json.loads(body.decode("utf-8"))

        def getresponse(self):
            return _Resp(json.dumps(responder(self.payload), ensure_ascii=False).encode("utf-8"))

        def close(self):
            self.closed = True

    monkeypatch.setattr(BV.http.client, "HTTPConnection", _Conn)
    return calls


PROMPT = "合成の文\n答え: "


def _char_lp(ch: str) -> float:
    return -((ord(ch) % 7) + 1) / 10.0


def _echo_responder(base, merge=False):
    def resp(payload):
        prompts = payload["prompt"] if isinstance(payload["prompt"], list) else [payload["prompt"]]
        choices = []
        for i, full in enumerate(prompts):
            cont = full[len(base):]
            if merge:  # 文の末尾と候補の頭が 1 トークンに結合した
                toks = [base[:-1], base[-1] + cont[:1]] + list(cont[1:])
            else:
                toks = [base] + list(cont)
            offs, pos = [], 0
            for t in toks:
                offs.append(pos)
                pos += len(t)
            lps = [None] + [_char_lp(t[-1]) for t in toks[1:]]
            choices.append({"index": i, "text": "x",
                            "logprobs": {"tokens": toks + ["x"], "token_logprobs": lps + [-9.0],
                                         "text_offset": offs + [len(full)], "top_logprobs": None}})
        return {"choices": list(reversed(choices))}  # 並びは index で戻す
    return resp


def test_vllm_echo_mode_slices_and_headers(monkeypatch):
    assert BV.VLLMLogprobScorer("m").mode == "prompt_logprobs" and BV.MODES[0] == "prompt_logprobs"  # 既定
    monkeypatch.setenv("DM_EVAL_VLLM_API_KEY", "fake-token-for-test")
    calls = _fake_http(monkeypatch, _echo_responder(PROMPT))
    vb = BV.VLLMLogprobScorer("org/Model-8B", port=8123, mode="echo")
    got = vb.continuation_logprobs(PROMPT, ["12", "3"])
    assert got == [(_char_lp("1"), _char_lp("2")), (_char_lp("3"),)]
    c = calls[0]
    assert c.host == "127.0.0.1" and c.port == 8123 and c.method == "POST" and c.path == "/v1/completions"
    assert c.headers["Authorization"] == "Bearer fake-token-for-test"
    assert c.payload["echo"] is True and c.payload["logprobs"] == 1 and c.payload["max_tokens"] == 1
    assert c.payload["prompt"] == [PROMPT + "12", PROMPT + "3"] and c.payload["temperature"] == 0.0
    assert "fake-token-for-test" not in json.dumps(vb.describe(), ensure_ascii=False)
    assert vb.describe()["host"] == "127.0.0.1" and vb.uses_gpu is True
    unbatched = BV.VLLMLogprobScorer("org/Model-8B", batch=False, mode="echo")
    assert unbatched.continuation_logprobs(PROMPT, ["12", "3"]) == got and len(calls) == 3
    monkeypatch.delenv("DM_EVAL_VLLM_API_KEY")
    vb.continuation_logprobs(PROMPT, ["1"])
    assert "Authorization" not in calls[-1].headers  # key が無ければヘッダを付けない


def test_vllm_token_boundary_and_http_errors(monkeypatch):
    monkeypatch.setenv("DM_EVAL_VLLM_API_KEY", "fake-token-for-test")
    _fake_http(monkeypatch, _echo_responder(PROMPT, merge=True))
    with pytest.raises(BB.TokenBoundaryError):
        BV.VLLMLogprobScorer("m", mode="echo").continuation_logprobs(PROMPT, ["12"])

    def shifted(payload):  # 位置は合うが字面が違う(日本語の文の途中のずれの模型)=黙って使わない
        out = _echo_responder(PROMPT)(payload)
        for ch in out["choices"]:
            ch["logprobs"]["tokens"][1] = "?"
        return out

    _fake_http(monkeypatch, shifted)
    with pytest.raises(BB.TokenBoundaryError, match="字面"):
        BV.VLLMLogprobScorer("m", mode="echo").continuation_logprobs(PROMPT, ["12"])

    def pl_bad(payload):
        return {"choices": [{"index": i, "text": "x", "prompt_logprobs": [None, {"1": {
            "logprob": -0.1, "decoded_token": full[:-1]}}, {"2": {"logprob": -0.2, "decoded_token": "Z"}}]}
            for i, full in enumerate(payload["prompt"])]}

    _fake_http(monkeypatch, pl_bad)
    with pytest.raises(BB.TokenBoundaryError):
        BV.VLLMLogprobScorer("m").continuation_logprobs(PROMPT, ["1"])
    sc = BB.LogprobChoiceScorer(BV.VLLMLogprobScorer("m"), "choice_number")
    with pytest.raises(J.ScoreFailed):
        sc.score(SYN[0], _presented(SYN[0]), text="文")
    assert sc.trace_summary()["boundary"] == 1  # 破綻に数える
    _fake_http(monkeypatch, lambda p: {"error": "boom"}, status=500)
    with pytest.raises(BB.BackendError) as ei:
        BV.VLLMLogprobScorer("m").continuation_logprobs(PROMPT, ["1"])
    assert "500" in str(ei.value) and "fake-token-for-test" not in str(ei.value) and "boom" not in str(ei.value)
    assert isinstance(ei.value, BV.BackendHTTPError) and ei.value.category == "http"

    class _Slow:
        def __init__(self, *a, **k):
            pass

        def request(self, *a, **k):
            pass

        def getresponse(self):
            raise TimeoutError("合成の時間切れ")

        def close(self):
            pass

    monkeypatch.setattr(BV.http.client, "HTTPConnection", _Slow)
    with pytest.raises(BB.BackendTimeout) as et:
        BV.VLLMLogprobScorer("m").continuation_logprobs(PROMPT, ["1"])
    assert J.failure_record(et.value) == {"error": "BackendTimeout", "message": "timeout"}
    _fake_http(monkeypatch, lambda p: {"choices": []})
    with pytest.raises(BB.BackendError):
        BV.VLLMLogprobScorer("m").continuation_logprobs(PROMPT, ["1"])
    for bad in (dict(host="0.0.0.0"), dict(host="localhost"), dict(port=0), dict(port=True), dict(mode="x")):
        with pytest.raises(ValueError):
            BV.VLLMLogprobScorer("m", **bad)
    with pytest.raises(ValueError):
        BV.VLLMLogprobScorer(" ")


def test_vllm_prompt_logprobs_first_token_and_generate(monkeypatch):
    def pl_resp(payload):
        out = []
        for i, full in enumerate(payload["prompt"]):
            cont = full[len(PROMPT):]
            toks = [PROMPT[:2], PROMPT[2:]] + list(cont)
            pl = [None] + [{str(100 + k): {"logprob": _char_lp(t[-1]), "rank": 1, "decoded_token": t}}
                           for k, t in enumerate(toks[1:])]
            out.append({"index": i, "text": "x", "prompt_logprobs": pl})
        return {"choices": out}

    calls = _fake_http(monkeypatch, pl_resp)
    vb = BV.VLLMLogprobScorer("m", mode="prompt_logprobs")
    assert vb.continuation_logprobs(PROMPT, ["12", "7"]) == [(_char_lp("1"), _char_lp("2")), (_char_lp("7"),)]
    assert calls[0].payload["prompt_logprobs"] == 0 and "echo" not in calls[0].payload
    calls = _fake_http(monkeypatch, lambda p: {"choices": [{"index": 0, "text": "", "logprobs": {
        "top_logprobs": [{"3": math.log(0.3), " 3": math.log(0.1), "1": math.log(0.5)}]}}]})
    ft = vb.first_token_logprobs(PROMPT, ["1", "3", "9"])
    assert ft[0] == pytest.approx(math.log(0.5)) and ft[1] == pytest.approx(math.log(0.4)) and ft[2] == float("-inf")
    assert calls[0].payload["logprobs"] == 20 and calls[0].payload["prompt"] == PROMPT
    _fake_http(monkeypatch, lambda p: {"choices": [{"index": 0, "text": "理由\n2"}]})
    assert vb.generate(PROMPT) == "理由\n2"
    sc = vb.scorer("choice_number_first", name="g_m", role=J.ROLE_BASELINE)
    assert sc.name == "g_m" and sc.role == J.ROLE_BASELINE and sc.form == BB.FORM_CHOICE


# ---------------------------------------------------------------------- (a) HF の口(import は遅延・計算は numpy)
def test_hf_backend_lazy_import_and_logits_math(monkeypatch):
    hb = BH.HFCausalChoiceScorer("weights/some-model", device="cuda")
    assert hb.name == "hf:some-model" and hb.uses_gpu and hb._loaded is None
    d = hb.describe()
    assert d["trust_remote_code"] is False and d["use_safetensors"] is True and d["local_files_only"] is True
    assert BH.HFCausalChoiceScorer("w", device="cpu").uses_gpu is False
    with pytest.raises(ValueError):
        BH.HFCausalChoiceScorer("w", dtype="int4")
    monkeypatch.setitem(sys.modules, "transformers", None)  # 本体の venv に無い場合と同じ
    with pytest.raises(BB.BackendUnavailable):
        hb.continuation_logprobs("文", ["1"])
    rows = np.array([[0.0, 1.0, 2.0], [3.0, 0.0, 0.0]])
    got = BH.continuation_logprobs_from_logits(rows, [2, 0])
    ref0 = 2.0 - math.log(math.exp(0) + math.exp(1) + math.exp(2))
    ref1 = 3.0 - math.log(math.exp(3) + 2.0)
    assert got == pytest.approx((ref0, ref1))
    assert np.allclose(np.exp(BH.log_softmax_rows(rows)).sum(axis=1), 1.0)
    with pytest.raises(ValueError):
        BH.continuation_logprobs_from_logits(rows, [1])
    sc = hb.scorer("score_text_sum")
    assert isinstance(sc, BB.LogprobChoiceScorer) and sc.form == BB.FORM_SCORE and sc.uses_gpu


def test_backends_package_lazy_names():
    assert BK.HFCausalChoiceScorer is BH.HFCausalChoiceScorer and BK.VLLMLogprobScorer is BV.VLLMLogprobScorer
    with pytest.raises(AttributeError):
        BK.no_such_name  # noqa: B018


def test_backend_identifier_names_avoid_banned_words():
    files = sorted((PKG / "backends").glob("*.py"))
    assert {p.name for p in files} == {"__init__.py", "base.py", "hf.py", "vllm.py"}
    bad = {p.name: _banned_identifiers(p.read_text(encoding="utf-8")) for p in files}
    assert all(v == [] for v in bad.values()), bad
    for p in files + sorted(PKG.glob("*.py")):  # 絶対パス・ホームの道筋を書かない
        src = p.read_text(encoding="utf-8")
        assert "C:\\" not in src and "/Users/" not in src and "\\Users\\" not in src, p.name


# ---------------------------------------------------------------------- cli の口
def _ns(**kw):
    base = dict(mock_seed="dm61-mock", vllm_model=None, vllm_port=8000, vllm_mode="prompt_logprobs",
                vllm_form="choice_number", vllm_api_key_env="DM_EVAL_VLLM_API_KEY", hf_model=None,
                hf_form="choice_number", hf_device="cuda", hf_name=None, length="short")
    base.update(kw)
    return SimpleNamespace(**base)


def test_model_factories_without_network(monkeypatch):
    def refuse(*a, **k):
        raise AssertionError("作るときに接続しない")

    monkeypatch.setattr(BV.http.client, "HTTPConnection", refuse)
    fx, g = C.model_factories(_ns(), material="evalset")
    assert g == "g_first_token" and [f().name for f in fx] == [s.name for s in J.scorer_registry()]
    fx, g = C.model_factories(_ns(), material="consumption")
    assert "tape" not in [f().name for f in fx]
    assert "なし" in next(f() for f in fx if f().name == "classical").words  # 消費の場面の古典は語彙 v3
    fx, g = C.model_factories(_ns(vllm_model="Qwen/Qwen3-8B-AWQ", hf_model="weights/OpenJev-0.8B"),
                              material="consumption")
    names = [f().name for f in fx]
    assert g == "g_qwen3_8b_awq" and g in names and "g_first_token" not in names and names[-1] == "hf_openjev_0_8b"
    made = [f() for f in fx]
    gs = made[names.index(g)]
    assert gs.implemented and gs.role == J.ROLE_BASELINE and gs.uses_gpu and gs.form == BB.FORM_CHOICE
    assert fx[names.index(g)]().backend is gs.backend  # 重み(口の後ろ)は共有
    assert gs.prompt_length == "short" and made[-1].prompt_length == "short"
    fx, g = C.model_factories(_ns(vllm_model="Qwen/Qwen3-8B-AWQ", hf_model="w/x", length="long"), material="evalset")
    made = {f().name: f() for f in fx}
    assert made[g].prompt_length == "long" and made["hf_x"].prompt_length == "long"  # --length は両方の口に効く
    assert made[g].backend.mode == "prompt_logprobs"


def test_cli_main_consumption(tmp_path, capsys):
    assert C.main(["run", "--out-dir", str(tmp_path / "c"), "--scenes", "consumption", "--determinism-repeats", "3"]) == 0
    out = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    doc = json.loads((tmp_path / "c" / "result.json").read_text(encoding="utf-8"))
    assert doc["inputs"]["n_scenes"] == 44 and doc["inputs"]["by_point"] == {p: 11 for p in S.DECISION_POINTS}
    assert doc["inputs"]["scenes"] == "tools/instruments/dm_eval/scenes/consumption_v1.jsonl"
    assert doc["digest"] == out["digest"] and doc["compare_digest"] == out["compare_digest"]
    assert doc["compare"]["determinism_repeats"] == 3
    assert {p.name for p in (tmp_path / "c").iterdir()} == {"result.json", "table.md", "table.json"}
    md = (tmp_path / "c" / "table.md").read_text(encoding="utf-8")
    assert T.BLANK_NO_REF in md and "推論の形" in md
    raw = (tmp_path / "c" / "result.json").read_bytes()
    assert b"\r" not in raw and str(tmp_path).encode("utf-8") not in raw
    sc = S.load_scene_file()
    again = C.evaluate(sc.situations, None, candidates=sc.candidates, material="consumption", points=sc.points,
                       scorer_factories=C.model_factories(_ns(), material="consumption")[0], determinism_repeats=3,
                       vocab_version=S.CONSUMPTION_VOCAB_VERSION, fields=sc.fields)
    assert doc["scene_set"] == "consumption" and doc["material"] == "consumption"
    assert doc["params"]["vocab_version"] == "v3"
    assert again["digest"] == doc["digest"]  # 決定的
    rec = json.loads(RECORD_1101.read_text(encoding="utf-8"))  # 記録の golden(CPU の当て口だけ)
    assert rec["digest"] == doc["digest"] and rec["inputs"]["scenes_md5"] == doc["inputs"]["scenes_md5"]
    assert rec["compare"]["determinism_repeats"] == 32


@pytest.mark.requires_data("evalset")
def test_cli_main_both(tmp_path, capsys):
    assert C.main(["run", "--out-dir", str(tmp_path / "b"), "--scenes", "both", "--no-tape-experience",
                   "--determinism-repeats", "2", "--determinism-limit", "20"]) == 0
    out = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert set(out) == {"evalset", "consumption"}
    assert {p.name for p in (tmp_path / "b").iterdir()} == {"evalset", "consumption"}
    ev = json.loads((tmp_path / "b" / "evalset" / "result.json").read_text(encoding="utf-8"))
    assert ev["n_situations"] == S.N_SITUATIONS and ev["compare"]["determinism_items"] == 20
    no_tape = json.loads((tmp_path / "b" / "evalset" / "result.json").read_text(encoding="utf-8"))["digest"]
    assert no_tape == out["evalset"]["digest"]
