"""renderer: golden テスト(§2.4 ⑧ バイト一致・決定論・予算・5分丸め・ハッシュ三役)。

(a) 同セル同5分帯同種別の2体で B0-B4b がバイト一致 / (b) 個体欄の変更は B5・B6 しか動かさない /
(c) 決定論(同入力→同 prompt_hash) / (d) 1,000 描画で予算内 / (e) template_sha256 の釘付け
(``test_templates.py``) / (f) 12:31 と 12:34 で B3 一致 / (g) B2 への ``P-12`` 混入を検出 /
(h) 命令文除去(``test_attention.py``) / (i) p_notice 検算表(``test_p_notice.py``) /
(j) 実データがあれば 100 体描画で予算と ⑧ を検査。
"""

from __future__ import annotations

import time
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pytest

from shibuya.agents.state import Activity, AgentKind, AgentState, ResultCode
from shibuya.perception import hashes as H
from shibuya.perception import templates as T
from shibuya.perception.renderer import (
    DEFAULT_START_DATETIME,
    PerceptionAssets,
    Renderer,
)
from shibuya.world.state import World

DATA_DIR = Path("data/world/v2")
SHARED_BLOCKS = ("B0", "B1", "B2", "B3", "B4", "B4b")


def build(n_agents: int = 200, n_cells: int = 16, seed: int = 1):
    """合成世界+個体(全員 来街者・同一セルに複数体)。"""
    w = World.synthetic(n_cells=n_cells, seed=seed)
    a = AgentState(n_agents)
    g = np.random.default_rng(seed)
    a.cell[:] = g.integers(0, n_cells, size=n_agents)
    a.xy[:] = g.uniform(0.0, 100.0, size=(n_agents, 2))
    a.kind[:] = AgentKind.VISITOR
    a.money[:] = g.integers(0, 8_000, size=n_agents)
    a.hunger[:] = g.integers(0, 11, size=n_agents)
    a.fatigue[:] = g.integers(0, 11, size=n_agents)
    a.thermal[:] = g.integers(0, 11, size=n_agents)
    a.holdings[:] = g.integers(0, 2, size=n_agents)
    a.activity[:] = g.integers(0, 8, size=n_agents)
    a.last_result[:] = g.integers(0, 18, size=n_agents)
    a.last_result_tick[:] = 1
    w.cells.density[:] = w.compute_density(a.cell)
    return w, a


# ---------------------------------------------------------------- (a)
def test_a_same_cell_same_band_same_kind_gives_identical_shared_bytes():
    """§2.4 ⑧「同セル・同時間帯の2体で B0-B4 のバイト差分がゼロ」。

    **解決した曖昧点**: B1=種別なので検査は (セル, 5分帯, **種別**) の3つ組で行う。
    """
    w, a = build()
    with a.writable():
        a.cell[0] = a.cell[1] = 3
    r = Renderer(w, a, seed=7)
    x = r.render(0, tick=760, wake_reason=3)
    y = r.render(1, tick=760, wake_reason=3)
    for b in SHARED_BLOCKS:
        assert x.blocks[b] == y.blocks[b], b
    assert x.shared_static_bytes() == y.shared_static_bytes()
    assert {b: x.block_hashes[b] for b in SHARED_BLOCKS} == {
        b: y.block_hashes[b] for b in SHARED_BLOCKS
    }


def test_a2_different_kind_changes_only_b1():
    """種別が違えば B1 だけ動く(B2-B4b は変わらない)。"""
    w, a = build()
    with a.writable():
        a.cell[0] = a.cell[1] = 3
        a.kind[1] = AgentKind.WORKER
    r = Renderer(w, a, seed=7)
    x, y = r.render(0, 760, 3), r.render(1, 760, 3)
    assert x.blocks["B1"] != y.blocks["B1"]
    for b in ("B0", "B2", "B3", "B4", "B4b"):
        assert x.blocks[b] == y.blocks[b], b


# ---------------------------------------------------------------- (b)
def test_b_individual_field_change_moves_only_b5_b6():
    w, a = build()
    with a.writable():
        a.cell[0] = 3
        a.money[0] = 1_200
        a.hunger[0] = 8
    r = Renderer(w, a, seed=7)
    before = r.render(0, 760, 3)
    with a.writable():
        a.money[0] = 9_999
    r.prepare_tick(760)
    after = r.render(0, 760, 3)
    for b in SHARED_BLOCKS:
        assert before.blocks[b] == after.blocks[b], b
    assert before.blocks["B5"] != after.blocks["B5"]
    assert before.prompt_hash != after.prompt_hash


def test_b2_wake_reason_and_result_move_only_b6():
    w, a = build()
    r = Renderer(w, a, seed=7)
    x = r.render(0, 760, wake_reason=3, last_result=int(ResultCode.MONEY_SHORT))
    y = r.render(0, 760, wake_reason=7, last_result=int(ResultCode.CLOSED))
    for b in (*SHARED_BLOCKS, "B5"):
        assert x.blocks[b] == y.blocks[b], b
    assert x.blocks["B6"] != y.blocks["B6"]


# ---------------------------------------------------------------- (c)
def test_c_rendering_is_deterministic():
    w1, a1 = build()
    w2, a2 = build()
    r1, r2 = Renderer(w1, a1, seed=7), Renderer(w2, a2, seed=7)
    for i in (0, 5, 42, 199):
        x, y = r1.render(i, 760, 3), r2.render(i, 760, 3)
        assert x.prompt_hash == y.prompt_hash
        assert x.text == y.text
        assert x.prefix_key == y.prefix_key
        assert x.block_hashes == y.block_hashes


def test_c2_prompt_hash_is_blake3_of_the_concatenated_blocks():
    from shibuya.core.hashing import blake3_hex

    w, a = build()
    out = Renderer(w, a, seed=7).render(0, 760, 3)
    assert out.prompt_hash == blake3_hex(
        b"\n".join(out.blocks[b] for b in T.BLOCK_IDS)
    )
    # prefix 鍵は共有 prefix(B0-B4b)のみ=知覚契約 §5(層2指摘で修正)
    shared_ids = [b for b in T.BLOCK_IDS if b not in ("B5", "B6")]
    assert out.prefix_key == H.prefix_key(
        [out.block_hashes[b] for b in shared_ids], shared_ids
    )
    # 個体ブロックだけ変えても prefix 鍵は不変(共有 prefix の役)
    b2 = Renderer(w, a, seed=7).render(0, 760, 7)
    assert b2.prefix_key == out.prefix_key


# ---------------------------------------------------------------- (d)
def test_d_1000_random_renders_stay_within_budgets(capsys):
    w, a = build(n_agents=1_000, n_cells=32, seed=3)
    r = Renderer(w, a, seed=11)
    g = np.random.default_rng(5)
    ticks = g.integers(0, 1_440, size=1_000)
    worst_block: dict[str, int] = {b: 0 for b in T.BLOCK_IDS}
    worst_group: dict[str, int] = {k: 0 for k in T.GROUP_TOKEN_BUDGET}
    t0 = time.perf_counter()
    for i in range(1_000):
        out = r.render(i, int(ticks[i]), wake_reason=int(i % 11))
        for b, v in out.tokens_est.items():
            worst_block[b] = max(worst_block[b], v)
        for k, v in out.group_tokens.items():
            worst_group[k] = max(worst_group[k], v)
        assert out.within_group_budgets()
    ms = (time.perf_counter() - t0) / 1_000 * 1_000
    with capsys.disabled():
        print(
            f"\n[renderer] 1,000描画 平均 {ms:.4f} ms/描画・"
            f"キャッシュ命中率 {r.cache_hit_rate:.3f}\n"
            f"           最大 tok/ブロック {worst_block}\n"
            f"           最大 tok/グループ {worst_group} (上限 {dict(T.GROUP_TOKEN_BUDGET)})"
        )
    # B0 以外はブロック単体の予算にも収まる(B0 の超過は既知・test_templates 参照)
    for b, v in worst_block.items():
        if b == "B0":
            continue
        assert v <= T.BLOCK_TOKEN_BUDGET[b], (b, v)
    assert ms <= 1.0, f"1 描画あたり {ms:.4f} ms(予算 1 ms)"


# ---------------------------------------------------------------- (f)
def test_f_five_minute_rounding_gives_identical_b3():
    """§2.4 ⑨: 12:31 と 12:34 は同じ B3(丸め幅 5 分)。12:35 は別。"""
    w, a = build()
    r = Renderer(w, a, seed=7)
    t1231 = 12 * 60 + 31
    t1234 = 12 * 60 + 34
    t1235 = 12 * 60 + 35
    assert r.render(0, t1231, 3).blocks["B3"] == r.render(0, t1234, 3).blocks["B3"]
    assert r.render(0, t1231, 3).blocks["B3"] != r.render(0, t1235, 3).blocks["B3"]
    assert "12時30分" in r.render(0, t1234, 3).blocks["B3"].decode("utf-8")


# ---------------------------------------------------------------- (g)
def test_g_guard_catches_a_planted_person_id_in_b2():
    """§2.4 ⑧ の機械検査: B2 に ``P-12`` を仕込むと描画が例外で落ちる。"""
    from shibuya.perception.normalize import AgentDependentWordError

    w, a = build()
    assets = PerceptionAssets.synthetic(w)
    names = list(assets.poi_name)
    names[0] = "P-12"
    poisoned = replace(assets, poi_name=tuple(names))
    r = Renderer(w, a, assets=poisoned, seed=7)
    with a.writable():
        a.cell[0] = 0
    with pytest.raises(AgentDependentWordError):
        r.render(0, 760, 3)


# ---------------------------------------------------------------- ハッシュ三役
def test_field_hash_unchanged_implies_b4_bytes_unchanged():
    """欄ハッシュが同じ ⇒ 描画 B4 バイトも同じ(dormant 抑止が取りこぼさない条件)。"""
    w, a = build(n_agents=400, n_cells=32, seed=4)
    r = Renderer(w, a, seed=7)
    seen: dict[int, bytes] = {}
    g = np.random.default_rng(9)
    for tick in range(0, 1_440, 37):
        with w.writable():
            w.cells.density[:] = g.integers(0, 900, size=w.n_cells)
        r.prepare_tick(tick)
        tc = r._tickc
        for cell in range(w.n_cells):
            fh = int(tc.b4_field_hash[cell])
            body = r._b4(cell, tc, [])
            if fh in seen:
                assert seen[fh] == body, f"欄ハッシュ衝突で B4 バイトが違う(cell={cell})"
            else:
                seen[fh] = body
    assert len(seen) > 3


def test_dormant_suppression_uses_the_block_hash():
    w, a = build()
    r = Renderer(w, a, seed=7)
    first = r.render(0, 760, 3)
    second = r.render(0, 760, 3)
    prev = first.block_hashes["B2"]
    assert H.should_resend(None, prev) is True
    assert H.should_resend(prev, second.block_hashes["B2"]) is False


def test_cache_hit_rate_is_high_on_repeated_cells(capsys):
    w, a = build(n_agents=500, n_cells=16, seed=2)
    r = Renderer(w, a, seed=7)
    for i in range(500):
        r.render(i, 760, 3)
    with capsys.disabled():
        print(f"\n[cache] hit_rate={r.cache_hit_rate:.3f} {r.report()}")
    assert r.cache_hit_rate > 0.95


# ---------------------------------------------------------------- 内容の契約
def test_blocks_are_in_contract_order_and_text_matches():
    w, a = build()
    out = Renderer(w, a, seed=7).render(0, 760, 3)
    assert tuple(out.blocks) == T.BLOCK_IDS
    assert out.text == "\n".join(out.blocks[b].decode("utf-8") for b in T.BLOCK_IDS)


def test_interoception_only_shows_threshold_crossings():
    w, a = build()
    with a.writable():
        a.hunger[0], a.fatigue[0], a.thermal[0] = 0, 0, 0
        a.hunger[1], a.fatigue[1], a.thermal[1] = 9, 0, 0
    r = Renderer(w, a, seed=7)
    calm = r.render(0, 760, 3).blocks["B5"].decode("utf-8")
    hungry = r.render(1, 760, 3).blocks["B5"].decode("utf-8")
    assert "体調に変わりはありません" in calm
    assert "空腹は9で閾値を超えています" in hungry
    assert "体力" not in hungry.split("\n")[0]


def test_b6_carries_reason_observation_and_three_options():
    """R4 §6「直前の結果」= 失敗理由 + 観測値 + いま可能な行動 3 語。"""
    w, a = build()
    with a.writable():
        a.cell[0] = 0
        a.money[0] = 100
        a.activity[0] = Activity.SHOPPING
    r = Renderer(w, a, seed=7)
    b6 = r.render(
        0, 760, wake_reason=3, last_result=int(ResultCode.MONEY_SHORT), last_action="購入"
    ).blocks["B6"].decode("utf-8")
    assert "直前の購入は所持金不足で失敗しました" in b6
    assert "所持金100円" in b6
    options = b6.split("いま可能: ")[1].split("。")[0]
    assert len(options.split("、")) == 3
    assert "待機" in options  # 失敗しない行動を必ず含む
    assert "[B6 問い] いま何をしますか。" in b6


def test_b6_reports_success_and_absence():
    w, a = build()
    with a.writable():
        a.last_result_tick[0] = -1
    r = Renderer(w, a, seed=7)
    assert "直前の結果はありません" in r.render(0, 760, 3).blocks["B6"].decode("utf-8")
    ok = r.render(1, 760, 3, last_result=int(ResultCode.OK)).blocks["B6"].decode("utf-8")
    assert "成功しました" in ok


def test_nearby_persons_decay_with_density():
    """人物④「k=密度で逓減(疎3/中2/密1)」。"""
    w, a = build(n_agents=400, n_cells=4, seed=6)
    with a.writable():
        a.cell[:] = 0
    r = Renderer(w, a, seed=7)
    with w.writable():
        w.cells.density[:] = 0
        w.cells.density[0] = 10  # 疎(LOS A)
    r.prepare_tick(760)
    sparse = r.render(0, 760, 3).blocks["B5"].decode("utf-8")
    with w.writable():
        w.cells.density[0] = 5_000  # 密(LOS F)
    r.prepare_tick(760)
    dense = r.render(0, 760, 3).blocks["B5"].decode("utf-8")
    assert sparse.count("P-") == 3
    assert dense.count("P-") == 1


def test_acquaintances_are_always_listed():
    """人物④「知人は常に掲載」。"""
    w, a = build(n_agents=50, n_cells=2, seed=8)
    with a.writable():
        a.cell[:] = 0
        a.xy[0] = (0.0, 0.0)
        a.xy[49] = (95.0, 95.0)  # 一番遠い
    r = Renderer(w, a, seed=7, acquaintances={0: [49]})
    with w.writable():
        w.cells.density[0] = 5_000  # 密 → k=1
    r.prepare_tick(760)
    b5 = r.render(0, 760, 3).blocks["B5"].decode("utf-8")
    assert "P-49(知人)" in b5


def test_watched_by_renders_the_fixed_empty_phrase():
    w, a = build()
    r = Renderer(w, a, seed=7)
    assert "見ている人はいません" in r.render(0, 760, 3).blocks["B5"].decode("utf-8")
    watched = np.zeros(len(a), dtype=np.int32)
    watched[0] = 2
    r2 = Renderer(w, a, seed=7, watched_by=watched)
    assert "見ている人が2人います" in r2.render(0, 760, 3).blocks["B5"].decode("utf-8")


def test_salient_events_reach_b4_and_change_its_hash():
    w, a = build()
    r = Renderer(w, a, seed=7)
    r.prepare_tick(760)
    quiet = r.render(0, 760, 3)
    cell = int(a.cell[0])
    r.prepare_tick(760, salient_events={cell: ["人が倒れています", "警察官が来ています"]})
    loud = r.render(0, 760, 3)
    assert "目につく出来事はありません" in quiet.blocks["B4"].decode("utf-8")
    assert "人が倒れています" in loud.blocks["B4"].decode("utf-8")
    assert quiet.block_hashes["B4"] != loud.block_hashes["B4"]


def test_signage_is_feature_tagged_and_imperative_free():
    """§1 条6: 世界内テキストは素性タグつき・命令文除去済み。"""
    w, a = build()
    b2 = Renderer(w, a, seed=7).render(0, 760, 3).blocks["B2"].decode("utf-8")
    assert "〔素性: 店頭表示・命令文除去済〕" in b2
    for bad in ("ください", "しろ", "せよ"):
        assert bad not in b2.split("[B2 看板]")[1].split("\n")[0]


def test_clock_fn_is_injectable():
    w, a = build()
    r = Renderer(w, a, seed=7, clock_fn=lambda t: datetime(2026, 8, 1, 3, 7))
    b3 = r.render(0, 0, 3).blocks["B3"].decode("utf-8")
    assert "3時05分" in b3
    assert DEFAULT_START_DATETIME == datetime(2026, 7, 28, 0, 0)


def test_out_of_world_agent_renders_the_fixed_empty_phrases():
    w, a = build()
    with a.writable():
        a.cell[0] = -1
    out = Renderer(w, a, seed=7).render(0, 760, 3)
    assert "見えるもの: なし" in out.blocks["B2"].decode("utf-8")
    assert out.within_group_budgets()


# ---------------------------------------------------------------- (j) 実データ
@pytest.mark.skipif(
    not (DATA_DIR / "w8_t1_cell.parquet").exists(), reason="data/world/v2 が無い"
)
def test_j_real_world_render_100_agents(capsys):
    """実資産(520 セル)で 100 体描画 → 予算・⑧・キャッシュ命中率を検査する。"""
    from shibuya.perception.normalize import assert_no_agent_dependent_words

    w = World.load(DATA_DIR)
    assets = PerceptionAssets.load(DATA_DIR, w)
    n = 100
    a = AgentState(n)
    g = np.random.default_rng(3)
    a.cell[:] = g.integers(0, w.n_cells, size=n)
    a.kind[:] = g.integers(0, 4, size=n)
    a.xy[:] = w.assets.cell_centroid[a.cell] + g.uniform(-40, 40, size=(n, 2))
    a.money[:] = g.integers(0, 20_000, size=n)
    a.hunger[:] = g.integers(0, 11, size=n)
    a.fatigue[:] = g.integers(0, 11, size=n)
    a.thermal[:] = g.integers(0, 11, size=n)
    a.activity[:] = g.integers(0, 8, size=n)
    a.last_result[:] = g.integers(0, 18, size=n)
    a.last_result_tick[:] = 1
    w.cells.density[:] = g.integers(0, 3_000, size=w.n_cells)

    r = Renderer(w, a, assets=assets, seed=13)
    t0 = time.perf_counter()
    worst = {k: 0 for k in T.GROUP_TOKEN_BUDGET}
    for i in range(n):
        out = r.render(i, tick=12 * 60 + 30, wake_reason=int(i % 11))
        assert out.within_group_budgets(), out.group_tokens
        assert_no_agent_dependent_words(out.shared_static_bytes().decode("utf-8"))
        for k, v in out.group_tokens.items():
            worst[k] = max(worst[k], v)
    ms = (time.perf_counter() - t0) / n * 1_000
    sample = r.render(0, 12 * 60 + 30, 3).text.split("\n")
    with capsys.disabled():
        print(
            f"\n[実データ] cells={w.n_cells} poi={w.n_poi} "
            f"{ms:.4f} ms/描画・hit_rate={r.cache_hit_rate:.3f}\n"
            f"           最大 tok/グループ {worst}\n"
            + "\n".join("           " + s for s in sample[21:])
        )
    assert ms <= 2.0


@pytest.mark.skipif(
    not (DATA_DIR / "w8_t1_cell.parquet").exists(), reason="data/world/v2 が無い"
)
def test_j2_real_assets_carry_names_noise_and_weather():
    w = World.load(DATA_DIR)
    assets = PerceptionAssets.load(DATA_DIR, w)
    assert assets.n_cells == w.n_cells
    assert any(assets.visible_poi)
    assert any(assets.visible_landmark)
    assert assets.walkable_area_m2.min() > 0
    assert set(np.unique(assets.noise_stage_day)) <= {0, 1, 2, 3}
    weather = assets.weather(datetime(2026, 7, 28, 12, 0))
    assert weather[0] in T.WEATHER_WORDS and weather[1] in T.DAYLIGHT_WORDS
    # 表に無い日付でも決定論的に落ちる
    assert assets.weather(datetime(2020, 1, 1, 12, 0)) == assets.weather(
        datetime(2019, 5, 5, 12, 0)
    )
