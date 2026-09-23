"""C9b 対象と注意(G3/G4/G5/G6/G7)の検収。

正典
- ``docs/design/v2-c9-geometry-agenda.md`` §1 **G3**(近づく=移動の対象が人/物)・
  **G4**(見る=待機の対象=注意の焦点)・**G5**(対象ヒント=辞書 v4)・
  **G6 (a)**(目印 68 を affordance に昇格・固有名を POI へ解決)・**G7**(会話距離)・
  **G11**(``UNREACHABLE`` / ``TARGET_GONE``)+ §4 改訂(焦点の寿命・喪失距離>取得距離・
  会話の成立距離と離脱距離を分ける)・§5 決定(2026-09-17 ユーザー「推奨どおり」)。
- ``docs/research/lit/gameeng__unreal_ai-perception.md``「★借りる」1(Sight/Lose Sight)・
  2(Max Age)。**数値は公式ページに無い=v2 側の expedient**。
- ``docs/design/v2-synonym-policy-v0.md`` §4-2「対象の損失 17 行」。

検査する 8 点(親の指示)
  (i) 既定 4 種の腕でバイト不変(欄も診断も増えない) / (ii) 辞書 v4 の写像 /
  (iii) 固有名 → POI 解決 / (iv) 近づく(到達・TARGET_GONE・UNREACHABLE) /
  (v) 焦点(設定・寿命・喪失距離) / (vi) 会話の成立/離脱のヒステリシス /
  (vii) T2-c 再生一致(edge+v2) / (viii) P2 の実測が宣言内。
"""

from __future__ import annotations

import dataclasses
import time
from pathlib import Path

import numpy as np
import pytest

from shibuya.agents.state import (
    FOCUS_NONE,
    Activity,
    AgentState,
    ResultCode,
    focus_code_for_poi,
)
from shibuya.engine import commit as C
from shibuya.engine import resolve as R
from shibuya.engine.conversation import ConversationManager
from shibuya.engine.geometry import EdgeGeometry
from shibuya.engine.run import run_day
from shibuya.llm.contract import TargetKind, parse_target, resolve_landmark
from shibuya.llm.undefined import (
    SYNONYM_TABLE_VERSION,
    SYNONYMS,
    TARGET_HINT_WORDS,
    map_synonym,
    synonym_table,
    synonym_table_version,
    target_hints,
)
from shibuya.world.state import LANDMARK_CATS, World

#: 小さい合成世界のラン(C9a の検収と同じ形・体が実際に歩き出すまで回す)。
SMALL = dict(n_agents=200, seed=1, ticks=600, checkpoint_every=200, n_cells=25)


class BoomLLM:
    """再生モードで**呼ばれたら落ちる** LLM(テープ外 0 の陽性対照)。"""

    def generate(self, *a, **k):  # pragma: no cover - 呼ばれないことが検査
        raise AssertionError("リプレイで実 LLM が呼ばれた")


# ================================================================ (i) 既定の腕は不変
@pytest.mark.parametrize(
    "arm",
    [
        {},
        {"vocab_version": "v2"},
        {"geometry": "edge"},
    ],
)
def test_default_arms_have_no_attention_columns_and_no_new_counters(arm):
    """既定の 3 腕(node/v1・node/v2・edge/v1)は C9b の欄も診断も持たない。

    本番の 4 種 checkpoint(既定 / ``--derive-rule v2.1`` / ``--vocab-version v2`` /
    ``--geometry edge``)が 1 バイトも動かないことの構造的な根拠=
    **``attention_columns`` が立たない**(SoA の宣言列が増えないので ``state_hash`` が動かない)。
    """
    res = run_day(**SMALL, **arm)
    assert res.attention is False
    assert res.run_manifest_fields()["attention"] is False
    assert (res.n_approach, res.n_focus, res.n_talk_by_distance) == (0, 0, 0)
    assert "対象と注意" not in res.summary()


def test_attention_arm_needs_both_edge_and_v2():
    """腕は ``geometry="edge"`` **かつ** ``vocab_version="v2"`` の積でだけ立つ。"""
    assert run_day(**SMALL, geometry="edge", vocab_version="v2").attention is True
    assert run_day(**SMALL, geometry="edge").attention is False
    assert run_day(**SMALL, vocab_version="v2").attention is False


def test_attention_columns_cost_five_bytes_per_agent():
    """``focus_target`` int32 + ``focus_ttl`` uint8 = **5 B/体**(宣言どおり)。"""
    base = AgentState(64, edge_columns=True)
    withf = AgentState(64, edge_columns=True, attention_columns=True)
    assert withf.registry.actual_bytes_per_entity - base.registry.actual_bytes_per_entity == 5
    assert base.state_hash() != withf.state_hash()  # 欄が増えれば hash は動く
    with pytest.raises(AttributeError):
        _ = base.focus_target
    assert int(withf.focus_target[0]) == FOCUS_NONE and int(withf.focus_ttl[0]) == 0


def test_v1_dictionary_and_version_are_untouched():
    """語彙 v1 の段0 辞書・版・対象ヒント表は**同一オブジェクト**のまま。"""
    assert synonym_table("v1") is SYNONYMS
    assert synonym_table_version("v1") == SYNONYM_TABLE_VERSION == "undefined-synonyms-v2"
    assert dict(target_hints("v1")) == {"帰る": "home", "帰宅": "home", "戻る": "home"}


# ================================================================ (ii) 辞書 v4 の写像
@pytest.mark.parametrize(
    "surface,word,hint",
    [
        ("帰る", "移動", "home"),
        ("帰宅", "移動", "home"),
        ("通勤", "移動", "work"),
        ("出勤", "移動", "work"),
        ("出社", "移動", "work"),
        ("通学", "移動", "school"),
        ("登校", "移動", "school"),
        ("探す", "移動", "category"),
        ("探索", "移動", "category"),
        ("近づく", "移動", "approach"),
        ("近寄る", "移動", "approach"),
        ("見る", "待機", "look"),
        ("眺める", "待機", "look"),
        ("観察", "待機", "look"),
        ("見物", "待機", "look"),
    ],
)
def test_dictionary_v4_maps_word_and_hint(surface, word, hint):
    assert map_synonym(surface, vocab_version="v2") == (word, hint)


def test_dictionary_v4_only_applies_to_vocab_v2():
    """語彙 v1 では写像先もヒントも現行のまま(「近づく」「見る」は未定義のまま)。"""
    assert map_synonym("近づく") == (None, "")
    assert map_synonym("見る") == (None, "")
    assert map_synonym("通勤") == ("移動", "")
    assert synonym_table_version("v2") == "undefined-synonyms-v4"


def test_longest_match_still_wins_over_the_new_two_character_row():
    """新しい 2 字の行(``見る``)が既存の長い表層を食わない(最長一致)。"""
    assert map_synonym("様子を見る", vocab_version="v2") == ("待機", "")
    assert map_synonym("見回る", vocab_version="v2") == ("移動", "")
    assert map_synonym("見学", vocab_version="v2") == ("待機", "")


def test_hint_words_and_engine_codes_are_one_to_one():
    """ヒントの語(llm)と索引(engine)が 1 対 1(二重定義の機械検査)。"""
    assert TARGET_HINT_WORDS[C.TARGET_HINT_NONE] == ""
    assert TARGET_HINT_WORDS[C.TARGET_HINT_APPROACH] == "approach"
    assert set(target_hints("v2").values()) <= set(TARGET_HINT_WORDS)
    assert C.target_hint_code("見たことのない印") == C.TARGET_HINT_NONE


# ================================================================ (iii) 固有名 → POI
def _world_with_landmark(name: str = "忠犬ハチ公像") -> World:
    """合成世界の POI 0 を「目印」にした世界(実資産が無い環境でも回る)。"""
    w = World.synthetic(n_cells=9, seed=1)
    cats = list(w.assets.poi_cat)
    names = [""] * len(cats)
    cats[0] = LANDMARK_CATS[0]
    names[0] = name
    w.assets = dataclasses.replace(  # type: ignore[misc]
        w.assets, poi_cat=tuple(cats), poi_name=tuple(names)
    )
    return w


def test_landmark_mask_and_name_table():
    w = _world_with_landmark()
    assert bool(w.landmark_mask[0]) and not bool(w.landmark_mask[1])
    assert w.landmark_targets() == {"忠犬ハチ公像": 0}
    assert w.landmark_targets() is w.landmark_targets()  # 遅延キャッシュ(1 回だけ作る)


def test_parse_target_resolves_a_proper_name_to_a_poi():
    table = _world_with_landmark().landmark_targets()
    got = parse_target("ハチ公像", table)
    assert got.kind is TargetKind.ITEM_CATEGORY  # **型は増やさない**(店 ID 枠の再利用)
    assert got.poi_id == 0 and got.category == "ハチ公像"
    # 表を渡さなければ現行どおり(``poi_id`` は付かない)
    assert parse_target("ハチ公像").poi_id is None
    # 駅名の判定は目印より**先**=表を渡しても動かない
    assert parse_target("渋谷駅", table).kind is TargetKind.STATION_OR_VEHICLE


def test_landmark_resolution_order_prefers_the_tightest_name():
    table = {"忠犬ハチ公像": 2, "ハチ公口": 5, "ハチ公口自転車等駐輪場": 9}
    assert resolve_landmark("忠犬ハチ公像", table) == 2          # 完全一致
    assert resolve_landmark("忠犬ハチ公像の前", table) == 2       # 名 ⊂ 入力(最長)
    assert resolve_landmark("ハチ公", table) == 5                # 入力 ⊂ 名(最短)
    assert resolve_landmark("公", table) is None                 # 1 字は引かない
    assert resolve_landmark("ハチ公", None) is None


@pytest.mark.skipif(
    not (Path("data/world/v2") / "w6_poi.parquet").exists(), reason="実世界資産が無い"
)
def test_real_assets_have_the_68_landmarks_and_resolve_hachiko():
    """実資産(W6): landmark 56 + attraction 12 = 68 件・「ハチ公像」→ 忠犬ハチ公像。"""
    w = World.load("data/world/v2")
    assert int(w.landmark_mask.sum()) == 68
    table = w.landmark_targets()
    pid = parse_target("ハチ公像", table).poi_id
    assert pid is not None and w.assets.poi_name[pid] == "忠犬ハチ公像"


# ================================================================ 近づく/焦点の土台
def _edge_world(n_agents: int = 6):
    """辺上の連続位置+注意の欄を持つ小さな世界(``resolve.apply`` を直接叩く)。"""
    world = World.synthetic(n_cells=9, seed=1)
    agents = AgentState(n_agents, edge_columns=True, attention_columns=True)
    geom = EdgeGeometry(world.assets, seed=1, n_agents=n_agents)
    with agents.writable():
        r = agents.registry
        r.node[:] = 0
        r.cell[:] = world.assets.node_cell[0]
        r.band[:] = world.assets.node_band[0]
        r.xy[:] = world.assets.node_xy[0]
        r.activity[:] = int(Activity.IDLE)
    agents.freeze()
    world.freeze()
    return world, agents, geom


def _batch(agent_ids, action, targets):
    n = len(agent_ids)
    return C.IntentBatch(
        agent_id=np.asarray(agent_ids, dtype=np.int64),
        action_code=np.full(n, action, dtype=np.int8),
        target_id=np.asarray(targets, dtype=np.int32),
        resource_id=np.full(n, -1, dtype=np.int32),
        t_notice_ns=np.zeros(n, dtype=np.int64),
    )


def _place(agents, world, agent_id, node):
    with agents.writable():
        r = agents.registry
        r.node[agent_id] = node
        r.cell[agent_id] = world.assets.node_cell[node]
        r.band[agent_id] = world.assets.node_band[node]
        r.xy[agent_id] = world.assets.node_xy[node]
        r.path_next_node[agent_id] = -1
        r.edge_id[agent_id] = -1
        r.edge_s[agent_id] = 0.0


# ================================================================ (iv) 近づく(G3/G11)
def test_approach_walks_to_the_node_nearest_the_target_and_arrives():
    """「近づく」= 移動の対象が人。目的ノードは**対象に最も近いノード**。"""
    world, agents, geom = _edge_world()
    target_node = 4
    _place(agents, world, 1, target_node)
    focus = np.full(agents.n, FOCUS_NONE, dtype=np.int64)
    focus[0] = 1  # 個体 0 が個体 1 に近づく
    dest_cell = int(world.assets.node_cell[target_node])
    out = R.apply(
        _batch([0], C.ACT_MOVE, [dest_cell]), C.IntentBatch.empty(),
        agents, world, 0, geometry=geom, focus_request=focus,
    )
    assert out.n_approach == 1
    assert int(agents.registry.target_node[0]) == target_node  # 代表ノードではなく対象のノード
    assert int(agents.registry.focus_target[0]) == 1
    # 歩き切るまでエンジン継続を回す
    for tick in range(1, 40):
        cont = C.engine_continuations(agents, C.ResourceSpace(world.n_poi, agents.n, world.n_cells), tick)
        if len(cont) == 0:
            break
        out = R.apply(cont, C.IntentBatch.empty(), agents, world, tick,
                      geometry=geom, focus_request=None)
    assert int(agents.registry.node[0]) == target_node
    assert out.n_approach_done == 1 and out.n_target_gone == 0
    assert int(agents.registry.last_result[0]) != int(ResultCode.TARGET_GONE)


def test_approach_reports_target_gone_when_nobody_is_there_on_arrival():
    """最後に見た位置へ着いても対象が居なければ ``TARGET_GONE``(§4 改訂 G11)。"""
    world, agents, geom = _edge_world()
    target_node = 4
    _place(agents, world, 1, target_node)
    focus = np.full(agents.n, FOCUS_NONE, dtype=np.int64)
    focus[0] = 1
    dest_cell = int(world.assets.node_cell[target_node])
    R.apply(_batch([0], C.ACT_MOVE, [dest_cell]), C.IntentBatch.empty(),
            agents, world, 0, geometry=geom, focus_request=focus)
    _place(agents, world, 1, 8)  # 対象は別のノードへ行ってしまった
    out = None
    space = C.ResourceSpace(world.n_poi, agents.n, world.n_cells)
    for tick in range(1, 40):
        cont = C.engine_continuations(agents, space, tick)
        if len(cont) == 0:
            break
        out = R.apply(cont, C.IntentBatch.empty(), agents, world, tick,
                      geometry=geom, focus_request=None)
    assert out is not None and out.n_target_gone == 1 and out.n_approach_done == 0
    assert int(agents.registry.last_result[0]) == int(ResultCode.TARGET_GONE)
    assert int(agents.registry.focus_target[0]) == FOCUS_NONE  # 焦点も落ちる


def test_approach_to_an_unreachable_target_fails_with_unreachable():
    """対象のセル/ノードが取れない(場外の相手)= ``UNREACHABLE``。"""
    world, agents, geom = _edge_world()
    with agents.writable():
        agents.registry.node[1] = -1  # 場外
        agents.registry.cell[1] = -1
    focus = np.full(agents.n, FOCUS_NONE, dtype=np.int64)
    focus[0] = 1
    out = R.apply(_batch([0], C.ACT_MOVE, [-1]), C.IntentBatch.empty(),
                  agents, world, 0, geometry=geom, focus_request=focus)
    assert out.per_result.get(int(ResultCode.UNREACHABLE), 0) == 1
    assert int(agents.registry.last_result[0]) == int(ResultCode.UNREACHABLE)


def test_approach_to_a_landmark_poi_uses_the_poi_node():
    world, agents, geom = _edge_world()
    poi = 3
    focus = np.full(agents.n, FOCUS_NONE, dtype=np.int64)
    focus[0] = int(focus_code_for_poi(poi))
    dest_cell = int(world.assets.poi_cell[poi])
    out = R.apply(_batch([0], C.ACT_MOVE, [dest_cell]), C.IntentBatch.empty(),
                  agents, world, 0, geometry=geom, focus_request=focus)
    assert out.n_approach == 1
    want = int(world.assets.poi_node[poi])
    assert int(agents.registry.target_node[0]) in (want, -1)
    assert int(agents.registry.focus_target[0]) == int(focus_code_for_poi(poi))


# ================================================================ (v) 注意の焦点(G4)
def test_look_sets_the_focus_when_the_target_is_within_the_acquire_radius():
    world, agents, geom = _edge_world()
    _place(agents, world, 1, 0)  # 同じノード=距離 0
    focus = np.full(agents.n, FOCUS_NONE, dtype=np.int64)
    focus[0] = 1
    out = R.apply(_batch([0], C.ACT_WAIT, [-1]), C.IntentBatch.empty(),
                  agents, world, 0, geometry=geom, focus_request=focus)
    assert out.n_focus == 1
    assert int(agents.registry.focus_target[0]) == 1
    assert int(agents.registry.focus_ttl[0]) == R.FOCUS_TTL_TICKS - 1  # 同 tick に 1 減る
    assert int(agents.registry.last_result[0]) == int(ResultCode.OK)  # 待機は失敗しない


def test_look_beyond_the_acquire_radius_does_not_set_a_focus_but_still_succeeds():
    world, agents, geom = _edge_world()
    far = int(np.argmax(np.linalg.norm(
        np.asarray(world.assets.node_xy) - np.asarray(world.assets.node_xy[0]), axis=1
    )))
    _place(agents, world, 1, far)
    assert float(np.linalg.norm(
        world.assets.node_xy[far] - world.assets.node_xy[0]
    )) > R.FOCUS_ACQUIRE_M
    focus = np.full(agents.n, FOCUS_NONE, dtype=np.int64)
    focus[0] = 1
    out = R.apply(_batch([0], C.ACT_WAIT, [-1]), C.IntentBatch.empty(),
                  agents, world, 0, geometry=geom, focus_request=focus)
    assert out.n_focus == 0
    assert int(agents.registry.focus_target[0]) == FOCUS_NONE
    assert int(agents.registry.last_result[0]) == int(ResultCode.OK)


def test_focus_expires_after_its_max_age():
    """寿命(UE ``Max Age`` 型)で焦点が消える。"""
    world, agents, geom = _edge_world()
    _place(agents, world, 1, 0)
    focus = np.full(agents.n, FOCUS_NONE, dtype=np.int64)
    focus[0] = 1
    R.apply(_batch([0], C.ACT_WAIT, [-1]), C.IntentBatch.empty(),
            agents, world, 0, geometry=geom, focus_request=focus)
    out = None
    for tick in range(1, R.FOCUS_TTL_TICKS + 2):
        out = R.apply(C.IntentBatch.empty(), C.IntentBatch.empty(), agents, world, tick,
                      geometry=geom, focus_request=None)
        if int(agents.registry.focus_target[0]) == FOCUS_NONE:
            break
    assert int(agents.registry.focus_target[0]) == FOCUS_NONE
    assert out is not None and out.n_focus_lost == 1
    assert tick == R.FOCUS_TTL_TICKS - 1  # 取得の tick で 1 減っているぶん早い


def test_focus_is_lost_beyond_the_lose_radius_which_is_wider_than_acquire():
    """喪失距離 > 取得距離(Sight / Lose Sight 型のヒステリシス)。"""
    assert R.FOCUS_LOSE_M > R.FOCUS_ACQUIRE_M
    world, agents, geom = _edge_world()
    _place(agents, world, 1, 0)
    focus = np.full(agents.n, FOCUS_NONE, dtype=np.int64)
    focus[0] = 1
    R.apply(_batch([0], C.ACT_WAIT, [-1]), C.IntentBatch.empty(),
            agents, world, 0, geometry=geom, focus_request=focus)
    assert int(agents.registry.focus_target[0]) == 1
    # ``apply`` は末尾で ``xy`` をノード/辺から貼り直すので、距離の検査は
    # ``_advance_focus`` を**直接**叩く(貼り直しに消されない)。
    base = np.asarray(world.assets.node_xy[0], dtype=np.float32)
    out = R.ResolveOutcome(tick=1)
    with agents.writable():
        # 取得半径の外・喪失半径の内 → まだ焦点は残る
        agents.registry.xy[1] = base + np.float32(
            [(R.FOCUS_ACQUIRE_M + R.FOCUS_LOSE_M) / 2.0, 0.0]
        )
        R._advance_focus(agents, world, out)
    assert int(agents.registry.focus_target[0]) == 1 and out.n_focus_lost == 0
    out = R.ResolveOutcome(tick=2)
    with agents.writable():
        # 喪失半径の外 → 落ちる
        agents.registry.xy[1] = base + np.float32([R.FOCUS_LOSE_M + 10.0, 0.0])
        R._advance_focus(agents, world, out)
    assert int(agents.registry.focus_target[0]) == FOCUS_NONE and out.n_focus_lost == 1


def test_renderer_puts_the_focus_person_first_in_b5():
    """B5(個体ブロック)は焦点の人物を先頭に置く。**B2 は共有ブロックなので触らない**。"""
    from shibuya.perception.renderer import PerceptionAssets, Renderer

    world = World.synthetic(n_cells=9, seed=1)
    agents = AgentState(6, attention_columns=True)
    with agents.writable():
        r = agents.registry
        r.cell[:] = 0
        r.node[:] = 0
        r.xy[:] = 0.0
        for j in range(6):
            r.xy[j] = (float(j), 0.0)  # 距離 = id
    agents.freeze()
    world.freeze()
    assets = PerceptionAssets.synthetic(world)
    plain = Renderer(world, agents, assets).render(0, 0).blocks["B5"].decode("utf-8")
    with agents.writable():
        agents.registry.focus_target[0] = 4  # 一番遠い相手を焦点にする
    focused = Renderer(world, agents, assets).render(0, 0).blocks["B5"].decode("utf-8")
    line = [x for x in focused.splitlines() if x.startswith("[B5 近接]")][0]
    assert line.split("近くの人物: ")[1].startswith("P-4")
    assert plain != focused
    # 焦点の無いラン(欄が無い)では 1 バイトも変わらない
    plain_agents = AgentState(6)
    with plain_agents.writable():
        pr = plain_agents.registry
        pr.cell[:] = 0
        pr.node[:] = 0
        for j in range(6):
            pr.xy[j] = (float(j), 0.0)
    plain_agents.freeze()
    same = Renderer(world, plain_agents, assets).render(0, 0).blocks["B5"].decode("utf-8")
    assert same == plain


# ================================================================ (vi) 会話距離(G7)
def test_talk_open_and_leave_distances_form_a_hysteresis():
    assert R.TALK_OPEN_METERS == 2.0 and R.TALK_LEAVE_METERS == 3.0
    assert R.TALK_LEAVE_METERS > R.TALK_OPEN_METERS


def test_talk_within_reach_needs_same_cell_and_two_meters():
    world, agents, _geom = _edge_world(4)
    a = np.array([0, 0], dtype=np.int64)
    b = np.array([1, 2], dtype=np.int64)
    here = np.asarray(agents.registry.xy[0], dtype=np.float64)
    with agents.writable():
        agents.registry.xy[1] = here + (1.0, 0.0)   # 1 m
        agents.registry.xy[2] = here + (2.5, 0.0)   # 2.5 m
    assert list(R.talk_within_reach(agents, a, b, by_distance=False)) == [True, True]
    assert list(R.talk_within_reach(agents, a, b, by_distance=True)) == [True, False]
    with agents.writable():
        agents.registry.cell[1] = 7  # セルが違えば距離が近くても届かない(層をまたがない)
    assert list(R.talk_within_reach(agents, a, b, by_distance=True)) == [False, False]


def test_apply_talk_rejects_a_partner_beyond_the_open_distance():
    world, agents, geom = _edge_world(4)
    with agents.writable():
        agents.registry.xy[1] = np.asarray(agents.registry.xy[0]) + (5.0, 0.0)
    out = R.apply(_batch([0], C.ACT_TALK, [1]), C.IntentBatch.empty(), agents, world, 0,
                  geometry=geom, talk_by_distance=True)
    assert out.n_conversations == 0 and out.n_talk_by_distance == 0
    assert int(agents.registry.last_result[0]) == int(ResultCode.PARTNER_GONE)
    # 同じ配置でも同一セル代理(既定)なら成立する=腕の差であることの確認
    world2, agents2, geom2 = _edge_world(4)
    with agents2.writable():
        agents2.registry.xy[1] = np.asarray(agents2.registry.xy[0]) + (5.0, 0.0)
    out2 = R.apply(_batch([0], C.ACT_TALK, [1]), C.IntentBatch.empty(), agents2, world2, 0,
                   geometry=geom2)
    assert out2.n_conversations == 1 and out2.n_talk_by_distance == 0


def test_conversation_closes_only_past_the_leave_distance():
    conv = ConversationManager(master_seed=1, walk_over_ticks=0)
    s = conv.invite(0, 1, tick=0, cell=3, same_cell=True, partner_idle=True, answered=True)
    assert s is not None
    conv.step(1)  # INVITED → PARTICIPATING
    xy = np.zeros((4, 2), dtype=np.float64)
    xy[1] = (R.TALK_OPEN_METERS + 0.5, 0.0)  # 成立距離より遠いが離脱距離の内
    conv.utterance(0, 2)
    assert conv.step(2, xy=xy, leave_distance_m=R.TALK_LEAVE_METERS) == []
    assert conv.sessions[s.session_id].close_reason == ""
    xy[1] = (R.TALK_LEAVE_METERS + 0.5, 0.0)
    conv.step(3, xy=xy, leave_distance_m=R.TALK_LEAVE_METERS)
    assert conv.sessions[s.session_id].close_reason == "left_cell"


# ================================================================ (vii) T2-c 再生
def test_attention_arm_tape_replays_bit_for_bit(tmp_path):
    """edge + 語彙 v2 で録ったテープの再生が checkpoint 列まで一致・テープ外 0。"""
    path = tmp_path / "tape_c9b"
    kw = dict(geometry="edge", vocab_version="v2")
    rec = run_day(tape_path=path, **SMALL, **kw)
    rep = run_day(mode="replay", replay=path, llm=BoomLLM(), **SMALL, **kw)
    assert rep.final_hash == rec.final_hash
    assert [c.combined for c in rep.checkpoints] == [c.combined for c in rec.checkpoints]
    assert rep.tape_miss_count == 0


def test_attention_arm_is_deterministic_and_differs_from_the_edge_arm():
    a = run_day(**SMALL, geometry="edge", vocab_version="v2")
    b = run_day(**SMALL, geometry="edge", vocab_version="v2")
    assert a.final_hash == b.final_hash
    assert a.final_hash != run_day(**SMALL, geometry="edge").final_hash
    assert a.conserved


# ================================================================ (viii) P2 の実測
def test_focus_upkeep_stays_inside_the_p2_budget():
    """焦点の寿命・喪失距離の毎 tick 更新が P2(≤5 ms/フレーム@5 千体)を食わない。

    C9a の P2 宣言(≤300 ms/tick@40 万体)に対し、ここで測るのは**追加分**
    (``_advance_focus`` 1 本)。40 万体ぶんを 1 本の配列演算で回して 1 tick の実測を出す。
    """
    n = 400_000
    world = World.synthetic(n_cells=139, seed=1)
    agents = AgentState(n, edge_columns=True, attention_columns=True)
    rng = np.random.default_rng(7)
    with agents.writable():
        r = agents.registry
        r.node[:] = rng.integers(0, world.n_nodes, n)
        r.cell[:] = world.assets.node_cell[r.node]
        r.xy[:] = world.assets.node_xy[r.node]
        r.focus_target[:] = rng.integers(0, n, n)
        r.focus_ttl[:] = R.FOCUS_TTL_TICKS
    out = R.ResolveOutcome(tick=0)
    best = float("inf")
    for _ in range(3):
        with agents.writable():
            agents.registry.focus_ttl[:] = R.FOCUS_TTL_TICKS
            t0 = time.perf_counter()
            R._advance_focus(agents, world, out)
            best = min(best, (time.perf_counter() - t0) * 1e3)
    assert best < 300.0, f"焦点の更新だけで {best:.1f} ms/tick(P2 宣言 300 ms@40 万体)"
    print(f"[C9b P2] 焦点の更新 {best:.1f} ms/tick @{n:,} 体")


# ================================================================ ヒント → 行き先(G5)
def _hint_intent(agents, world, hint, *, person=-1, poi=-1, home=7, work=3, school=5):
    """1 体ぶんの「移動」intent を対象ヒント付きで組む。"""
    n = agents.n
    return C.intents_from_responses(
        agents, world, C.ResourceSpace(world.n_poi, n, world.n_cells), 0,
        np.array([0], dtype=np.int64), np.zeros(1, dtype=np.int64),
        np.array([C.ACT_MOVE], dtype=np.int64),
        home_cell=np.full(n, home, dtype=np.int64),
        work_cell=np.full(n, work, dtype=np.int64),
        school_cell=np.full(n, school, dtype=np.int64),
        target_person=np.array([person], dtype=np.int64),
        target_hint=np.array([hint], dtype=np.int64),
        target_poi=np.array([poi], dtype=np.int64),
    )


def test_engine_resolves_home_work_school_hints_to_the_w16_cells():
    """「帰宅」「通勤」「通学」の行き先を**エンジンが**拠点セルに解決する(G5)。"""
    world, agents, _geom = _edge_world(4)
    assert int(_hint_intent(agents, world, C.TARGET_HINT_HOME).target_id[0]) == 7
    assert int(_hint_intent(agents, world, C.TARGET_HINT_WORK).target_id[0]) == 3
    assert int(_hint_intent(agents, world, C.TARGET_HINT_SCHOOL).target_id[0]) == 5
    # 学校を持たない体(``-1``)はヒントが効かず現行の行き先のまま
    n = agents.n
    got = C.intents_from_responses(
        agents, world, C.ResourceSpace(world.n_poi, n, world.n_cells), 0,
        np.array([0], dtype=np.int64), np.zeros(1, dtype=np.int64),
        np.array([C.ACT_MOVE], dtype=np.int64),
        home_cell=np.full(n, 7, dtype=np.int64), work_cell=np.full(n, 3, dtype=np.int64),
        school_cell=np.full(n, -1, dtype=np.int64),
        target_hint=np.array([C.TARGET_HINT_SCHOOL], dtype=np.int64),
    )
    assert int(got.target_id[0]) == 3  # いま自宅に居るので職場(現行の既定)


def test_no_hint_means_the_current_destination_rule():
    """ヒントを渡さなければ**1 バイトも変わらない**(職場/自宅の現行規則)。"""
    world, agents, _geom = _edge_world(4)
    n = agents.n
    base = C.intents_from_responses(
        agents, world, C.ResourceSpace(world.n_poi, n, world.n_cells), 0,
        np.array([0], dtype=np.int64), np.zeros(1, dtype=np.int64),
        np.array([C.ACT_MOVE], dtype=np.int64),
        home_cell=np.full(n, 7, dtype=np.int64), work_cell=np.full(n, 3, dtype=np.int64),
    )
    none_hint = _hint_intent(agents, world, C.TARGET_HINT_NONE)
    assert int(base.target_id[0]) == int(none_hint.target_id[0]) == 3


def test_approach_hint_targets_the_cell_of_the_person_or_landmark():
    world, agents, _geom = _edge_world(4)
    _place(agents, world, 1, 4)
    want = int(world.assets.node_cell[4])
    got = _hint_intent(agents, world, C.TARGET_HINT_APPROACH, person=1)
    assert int(got.target_id[0]) == want
    poi = 3
    got = _hint_intent(agents, world, C.TARGET_HINT_APPROACH, poi=poi)
    assert int(got.target_id[0]) == int(world.assets.poi_cell[poi])
    # 対象が取れなければ -1 → ``_apply_move`` が ``UNREACHABLE``
    assert int(_hint_intent(agents, world, C.TARGET_HINT_APPROACH).target_id[0]) == -1


def test_focus_codes_only_fire_for_approach_and_look():
    hints = np.array(
        [C.TARGET_HINT_NONE, C.TARGET_HINT_HOME, C.TARGET_HINT_APPROACH, C.TARGET_HINT_LOOK],
        dtype=np.int64,
    )
    person = np.array([2, 2, 2, -1], dtype=np.int64)
    poi = np.array([-1, -1, -1, 6], dtype=np.int64)
    got = C.focus_codes(hints, person, poi, n_agents=8)
    assert list(got) == [FOCUS_NONE, FOCUS_NONE, 2, int(focus_code_for_poi(6))]


def test_landmark_cats_are_shared_between_world_and_renderer():
    """目印の集合は**世界側と知覚側で同じ 1 本**(二重定義を作らない)。"""
    from shibuya.perception import renderer as PR

    assert LANDMARK_CATS == ("landmark", "attraction")
    assert PR.LANDMARK_CATS is LANDMARK_CATS
