"""段 2a(D-114 (a)): 選択器の口 ``Chooser.probs``・候補の絞り込み・落選の理由・manifest。

正典: ``docs/design/v2-intent-chooser-implementation-agenda.md`` §1。
"""

from __future__ import annotations

import dataclasses
from collections import Counter
from pathlib import Path

import numpy as np
import pytest

from shibuya.agents.state import AgentState, ResultCode
from shibuya.engine import resolve as R
from shibuya.engine.chooser import (
    CHOOSER_NAMES,
    ChoiceContext,
    Chooser,
    NearestChooser,
    check_chooser,
    draw_index,
    entropy_bits,
    make_chooser,
)
from shibuya.engine.poi_target import (
    BUYABLE_CATS,
    CATEGORY_WORDS,
    GENERIC_WORDS,
    POI_TARGET_MODES,
    check_poi_target,
    KIND_CATEGORY,
    KIND_NAMED,
    KIND_NONE,
    TargetResolver,
    resolution_summary,
)
from shibuya.engine.run import run_day
from shibuya.llm.contract import parse_target
from shibuya.world.state import World

WORLD_DIR = Path("data/world/v2")
NOON = 720


def _ctx(vis, dist) -> ChoiceContext:
    return ChoiceContext(0, 0, 0, 0, 3, KIND_NONE, "", 0,
                         visibility=np.asarray(vis), distance_m=np.asarray(dist, dtype=float))


# ------------------------------------------------------------------ 口の契約
def test_nearest_chooser_is_a_chooser_and_returns_a_one_hot_distribution():
    ch = make_chooser("nearest")
    assert isinstance(ch, Chooser) and ch.name == "nearest"
    p = ch.probs(np.array([4, 2, 9]), _ctx([1, 1, 1], [0, 0, 0]))
    assert p.shape == (3,) and p.sum() == pytest.approx(1.0)
    assert sorted(p.tolist()) == [0.0, 0.0, 1.0]
    assert ch.probs(np.zeros(0, dtype=np.int64), _ctx([], [])).shape == (0,)


def test_nearest_order_is_distance_then_visibility_then_poi_index():
    ch = NearestChooser()
    # 距離が最優先(遠い方は可視が大きくても負ける)
    assert ch.probs(np.array([1, 2]), _ctx([100, 1], [50, 0])).tolist() == [0.0, 1.0]
    # 同じ距離なら可視(視点数)の降順
    assert ch.probs(np.array([1, 2, 3]), _ctx([5, 9, 7], [0, 0, 0])).tolist() == [0.0, 1.0, 0.0]
    # 可視も同じなら POI 索引の昇順
    assert ch.probs(np.array([8, 3, 5]), _ctx([2, 2, 2], [0, 0, 0])).tolist() == [0.0, 1.0, 0.0]


def test_draw_is_deterministic_and_follows_the_distribution():
    p = np.array([0.5, 0.5])
    assert draw_index(p, 1, 100, 7) == draw_index(p, 1, 100, 7)
    picks = Counter(draw_index(p, 1, 100, a) for a in range(400))
    assert set(picks) == {0, 1} and min(picks.values()) > 120
    assert draw_index(np.array([0.0, 0.0, 1.0]), 1, 5, 5) == 2  # one-hot も抽選を通る
    assert draw_index(np.zeros(0), 1, 5, 5) == -1
    with pytest.raises(ValueError):
        draw_index(np.zeros(2), 1, 5, 5)


def test_entropy_and_names():
    assert entropy_bits(np.array([0.0, 1.0])) == pytest.approx(0.0)
    assert entropy_bits(np.array([0.5, 0.5])) == pytest.approx(1.0)
    # 5 段目 5b(D-119): classical(古典的選択モデルの店選び)を足した。既定は nearest のまま
    assert CHOOSER_NAMES == ("nearest", "classical")
    with pytest.raises(ValueError):
        check_chooser("huff")


# ------------------------------------------------------------------ 合成の小さな世界
def _world(cells, cats, names, *, open_from=None, open_to=None, subcats=None, stock=None, vis=None):
    base = World.synthetic(n_cells=4, seed=1).assets
    n = base.n_poi
    assert len(cells) == n
    a = dataclasses.replace(
        base,
        poi_cell=np.asarray(cells, dtype=np.int32),
        poi_cat=tuple(cats),
        poi_name=tuple(names),
        poi_subcat=tuple(subcats) if subcats is not None else ("",) * n,
        poi_open_from=np.asarray(open_from if open_from is not None else [0] * n, dtype=np.int16),
        poi_open_to=np.asarray(open_to if open_to is not None else [1440] * n, dtype=np.int16),
    )
    w = World(a)
    if stock is not None:
        w.pois.stock[:] = np.asarray(stock, dtype=np.int32)
    w._poi_visibility = np.asarray(vis if vis is not None else [0] * n, dtype=np.int32)
    return w


def _agents(cells) -> AgentState:
    ag = AgentState(len(cells))
    ag.registry.cell[:] = np.asarray(cells)
    ag.registry.node[:] = 0
    return ag


# 8 POI: セル 0 に 0..3、セル 1 に 4..5、セル 2 に 6、セル 3 に 7
CELLS = [0, 0, 0, 0, 1, 1, 2, 3]
CATS = ["shop", "food", "food", "shop", "food", "nightlife", "shop", "office"]
NAMES = ["スターバックス", "カフェ・ベローチェ", "おむすび権米衛", "コンビニX", "スターバックス",
         "バーY", "書店Z", "事務所W"]
SUBS = ["", "", "", "convenience", "", "", "books", ""]


def _resolve(w, agent_cells, codes, targets, eat, buy_like, tick=NOON):
    ag = _agents(agent_cells)
    res = TargetResolver(world=w, chooser=NearestChooser(), seed=1)
    tg = [None if t is None else parse_target(t) for t in targets]
    out = res.resolve(ag, tick, np.arange(len(agent_cells)), np.asarray(codes), tg,
                      is_eat=np.asarray(eat), is_buy_like=np.asarray(buy_like))
    return out, res, ag


def test_classify_order_category_word_before_names():
    w = _world(CELLS, CATS, NAMES, subcats=SUBS)
    r = TargetResolver(world=w, chooser=NearestChooser(), seed=1)
    assert r.classify(None)[0] == KIND_NONE
    assert r.classify(parse_target("なし"))[0] == KIND_NONE
    assert r.classify(parse_target("g0_0_GL"))[0] == KIND_NONE          # セル ID は なし扱い(段 2a)
    k, _t, named, word = r.classify(parse_target("カフェ"))                # 「カフェ」はカテゴリ語
    assert (k, named, word) == (KIND_CATEGORY, (), "カフェ")
    assert r.classify(parse_target("スターバックス"))[:3] == (KIND_NAMED, "スターバックス", (0, 4))
    assert r.classify(parse_target("おむすび権米衛の店頭"))[2] == (2,)    # 接尾辞を剥がす
    assert r.classify(parse_target("権米衛"))[2] == (2,)                  # 入力 ⊂ 名
    assert r.classify(parse_target("近くの飲食店"))[::3] == (KIND_CATEGORY, "飲食店")  # 語を含む
    assert r.classify(parse_target("shop0006"))[:3] == (KIND_NAMED, "shop0006", (6,))
    assert r.classify(parse_target("food0006"))[0] == KIND_NONE           # cat が合わない
    assert r.classify(parse_target("目的物"))[0] == KIND_NONE


def test_none_skips_the_closed_lowest_id_and_picks_the_most_visible_open_poi():
    # セル 0: POI 0 は閉店(従来の最小 id)。開いている 1..3 のうち可視最大は 3
    w = _world(CELLS, CATS, NAMES, open_from=[900, 0, 0, 0, 0, 0, 0, 0],
               vis=[99, 5, 7, 8, 0, 0, 0, 0])
    out, res, _ = _resolve(w, [0], [R.ACT_BUY], [None], [False], [True])
    assert out.tolist() == [3]
    assert res.stats["resolved:none"] == 1


def test_eat_candidates_are_eateries_and_other_reasons_are_split():
    w = _world(CELLS, CATS, NAMES, open_from=[0, 900, 0, 0, 900, 0, 0, 0],
               stock=[0, 5, 5, 0, 5, 5, 0, 5], vis=[0, 3, 2, 0, 0, 0, 0, 0], subcats=SUBS)
    agents_cells = [0, 1, 3, 2, 0]
    codes = [R.ACT_EAT, R.ACT_EAT, R.ACT_EAT, R.ACT_BUY, R.ACT_BUY]
    eat = [True, True, True, False, False]
    buy = [False, False, False, True, True]
    out, res, ag = _resolve(w, agents_cells, codes, [None, None, None, None, "コンビニ"], eat, buy)
    # 体0: セル0 の飲食店 1(閉店)・2(開)→ 2
    assert out[0] == 2
    # 体1: セル1 の飲食店 4 は閉店 → 閉店の代表 4(resolve が CLOSED を付ける)
    assert out[1] == 4 and res.stats["no_candidate:closed"] == 1
    # 体2: セル3 に飲食店なし → -1(NOT_IN_EATERY)
    assert out[2] == -1 and res.stats["no_candidate:not_in_eatery"] == 1
    # 体3: セル2 の 6 は開いているが在庫 0 → 在庫切れの代表 6
    assert out[3] == 6
    # 体4: 「コンビニ」= subcat convenience の 3 だけ・在庫 0 → 在庫切れの代表 3
    assert out[4] == 3 and res.stats["no_candidate:out_of_stock"] == 2
    summ = resolution_summary(res.stats, res.entropy_sum)
    assert summ["iii_none"] == 1 and summ["iv_no_candidate"]["out_of_stock"] == 2


def test_named_in_cell_is_the_only_candidate_and_out_of_cell_fails():
    w = _world(CELLS, CATS, NAMES, vis=[0, 50, 0, 0, 0, 0, 0, 0])
    # セル 0 で「スターバックス」= POI 0(可視が小さくても名指しが勝つ)
    out, res, _ = _resolve(w, [0, 2], [R.ACT_BUY, R.ACT_BUY], ["スターバックス", "スターバックス"],
                           [False, False], [True, True])
    assert out[0] == 0 and res.stats["resolved:named"] == 1
    # セル 2 にスターバックスは無い → 段 2c までは失敗(-1)
    assert out[1] == -1 and res.stats["no_candidate:named_out_of_cell"] == 1


def test_category_filters_by_w6_cat_and_bad_target_when_nothing_matches():
    w = _world(CELLS, CATS, NAMES, subcats=SUBS)
    out, res, _ = _resolve(w, [0, 3], [R.ACT_BUY, R.ACT_BUY], ["飲食店", "飲食店"],
                           [False, False], [True, True])
    assert out[0] in (1, 2)          # food だけ
    assert out[1] == -1 and res.stats["no_candidate:bad_target"] == 1  # セル3 は office だけ


def test_the_representative_targets_produce_the_split_result_codes():
    """候補 0 の代表(閉店/在庫切れ)と -1 が、resolve の既存の判定で理由どおりの結果コードになる。"""
    w = _world(CELLS, CATS, NAMES, open_from=[900] * 8, stock=[0] * 8)
    ag = _agents([0, 0, 3])
    out = R.ResolveOutcome(tick=NOON)
    R._apply_buy(ag, w, np.array([0]), np.array([3]), NOON, out, None)     # 閉店の代表
    R._apply_eat(ag, w, np.array([1]), np.array([-1]), NOON, out, None)    # 飲食店なし
    R._apply_buy(ag, w, np.array([2]), np.array([-1]), NOON, out, None)    # 対象なし
    assert ag.registry.last_result[:3].tolist() == [
        int(ResultCode.CLOSED), int(ResultCode.NOT_IN_EATERY), int(ResultCode.BAD_TARGET)
    ]


# ------------------------------------------------------------------ run_day / manifest
def test_run_day_records_chooser_and_target_resolution_in_the_manifest():
    res = run_day(n_agents=40, seed=1, ticks=30, renderer="stub", vocab_version="v2",
                  checkpoint_every=30)
    m = res.run_manifest_fields()
    assert m["chooser"] == "nearest"
    tr = m["target_resolution"]
    # 段 2c(第288)で v_intent(意図にした行)と named_out_of_cell_detail が足された
    assert set(tr) == {"i_named", "ii_category", "iii_none", "iv_no_candidate", "attempts",
                       "iv_by_kind", "chooser_entropy_mean_bits", "v_intent",
                       "named_out_of_cell_detail"}
    assert m["poi_target"] == "candidates"
    assert set(tr["iv_no_candidate"]) == {"bad_target", "not_in_eatery", "closed",
                                          "out_of_stock", "named_out_of_cell"}
    with pytest.raises(ValueError):
        run_day(n_agents=10, seed=1, ticks=2, renderer="stub", chooser="huff")


def test_buyable_cats_are_the_shop_like_cats_q12():
    """親決定 Q12: 購入/並ぶの候補=店舗系 cat だけ(学校・事務所・教会などでの購入を消す)。"""
    assert BUYABLE_CATS == {"food", "shop", "nightlife", "service", "leisure", "cinema", "attraction"}
    excluded = {"office", "hotel", "school", "landmark", "hall", "education"}
    assert not (BUYABLE_CATS & excluded)
    # 合成世界の 3 種(コンビニ/飲食/物販)は作りからして店=購入の候補(実資産の cat とは重ならない)
    from shibuya.engine.poi_target import SYNTHETIC_BUYABLE_CATS
    from shibuya.world.assets import SYNTHETIC_POI_CATS

    assert SYNTHETIC_BUYABLE_CATS == set(SYNTHETIC_POI_CATS)
    assert not (SYNTHETIC_BUYABLE_CATS & (BUYABLE_CATS | excluded))
    # セル 3 は office だけ → 購入の候補 0(対象なし)・食事でもない
    w = _world(CELLS, CATS, NAMES, subcats=SUBS)
    out, res, _ = _resolve(w, [3], [R.ACT_BUY], [None], [False], [True])
    assert out.tolist() == [-1] and res.stats["no_candidate:bad_target"] == 1
    # 名指しでも店舗系でない POI は購入の候補にならない
    out, res, _ = _resolve(w, [3], [R.ACT_BUY], ["事務所W"], [False], [True])
    assert out.tolist() == [-1] and res.stats["no_candidate_by_kind:named:bad_target"] == 1


def test_generic_words_read_as_none_q11():
    """対応表 v0(Q11): 「店」「店舗」「ショップ」「お店」は なし(「〇〇ショップ」の名指しにしない)。"""
    names = list(NAMES)
    names[1] = "カメラショップ"
    w = _world(CELLS, CATS, names, subcats=SUBS)
    r = TargetResolver(world=w, chooser=NearestChooser(), seed=1)
    assert GENERIC_WORDS == {"店", "店舗", "ショップ", "お店"}
    for word in GENERIC_WORDS:
        assert r.classify(parse_target(word))[0] == KIND_NONE, word
    assert r.classify(parse_target("カメラショップ"))[0] == KIND_NAMED
    assert len(CATEGORY_WORDS) == 59


def test_poi_target_switch_values_q13():
    assert POI_TARGET_MODES == ("candidates", "legacy")
    with pytest.raises(ValueError):
        check_poi_target("min_id")
    res = run_day(n_agents=20, seed=1, ticks=10, renderer="stub", poi_target="legacy",
                  checkpoint_every=10)
    assert res.run_manifest_fields()["poi_target"] == "legacy"
    assert res.target_resolution == {}


@pytest.mark.skipif(not (WORLD_DIR / "w17_schedule.parquet").exists(), reason="実世界資産が無い")
def test_poi_target_legacy_reproduces_the_pre_2a_checkpoints_q13(monkeypatch):
    """親決定 Q13: ``--poi-target legacy`` で段 2a 前の checkpoint(02bd0312・b4ad8140)を再現する。

    段 2c(第288)で意図の 4 欄(+10 B/体)が既定で確保され、全 checkpoint が欄のぶん動いた。
    ``legacy`` では意図の層が働かない(欄を確保するだけ)ので、**欄を混ぜないハッシュ**
    (``Registry.state_hash(exclude=INTENT_FIELDS)``)で旧値がそのまま出る=挙動は 1 バイトも
    変わっていない。欄を混ぜた新しい値: v3 ``b3287fa8e93305a5`` / 帰無腕 ``e1c182cbb064aa8b``。
    """
    from shibuya.agents.state import INTENT_FIELDS, AgentState
    from shibuya.cli import run as cli_run

    monkeypatch.setattr(
        AgentState, "state_hash",
        lambda self: self.registry.state_hash(exclude=INTENT_FIELDS),
    )
    # 3 段目(第289): CLI/cli.run の既定が無制限になったので旧挙動の上限(l4_scale=1.0)を明示する
    # 5 段目 5a(第291): cli.run の空腹の既定が energy になったので旧規則(hunger_model="v1")を明示する
    v3 = cli_run(n_agents=5_000, seed=1, world_dir=str(WORLD_DIR), vocab_version="v3",
                 poi_target="legacy", l4_scale=1.0, hunger_model="v1")
    assert v3.final_hash.startswith("02bd03126d5f41cb") and int(v3.llm_calls) == 36_460
    null = cli_run(n_agents=5_000, seed=1, world_dir=str(WORLD_DIR), plan_executor=False,
                   report_precondition=False, poi_target="legacy", l4_scale=1.0,
                   hunger_model="v1")
    assert null.final_hash.startswith("b4ad8140fe4176db") and int(null.llm_calls) == 41_072


def test_category_table_uses_known_w6_values_only():
    from shibuya.build.geo import poi_class as PC

    cats = {"food", "shop", "nightlife", "office", "service", "hotel", "school", "landmark",
            "leisure", "hall", "attraction", "cinema", "education"}
    for word, c, s in CATEGORY_WORDS:
        assert c <= cats, word
        assert s <= set(PC.SUBCAT_TOPCAT), word


@pytest.mark.skipif(not (WORLD_DIR / "w8_t1_cell.parquet").exists(), reason="実世界資産が無い")
def test_poi_visibility_is_read_from_w8_on_the_real_world():
    w = World.load_or_synthetic(WORLD_DIR, n_cells=139, seed=1)
    v = w.poi_visibility
    assert v.shape == (w.n_poi,) and int((v > 0).sum()) == 2_309
    assert int(World.synthetic(n_cells=16, seed=1).poi_visibility.sum()) == 0
