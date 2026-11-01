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
