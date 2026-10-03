"""第2波 §2A 項 2: **初期辺の在職期間のハッシュの修正**(Q111 の解析で見つかった欠陥)のテスト。

事実(記録 ``docs/bench/analysis/q111-capacity-2026-09-30/`` §5): 在職期間の U=``_pair_mix(min 元 id, max 元 id)``、
同点の相手の順=``_pair_mix(元 id_u, 元 id_v)`` の昇順。元 id_u < 元 id_v の辺では 2 つが同じ値になり、同点の多い
組で在職期間の短い相手ほど選ばれた。v2(既定)は U を同点の順と独立な混ぜ合わせにした。v1 は旧の再現用。

見るもの: (a) v1 は旧の式そのもの・v2 は向きのない組で対称 (b) 合成の大組織(全員同点)で v1 は短い在職に寄り、v2 は
一様(2 週未満 ≈ 1/12)(c) 大量の組で U と同点の順のハッシュの順位相関 ≈ 0 (d) 全母集団の初期網で種別 × 向きの
どれでも 2 週未満が 8.3% ± 1 ポイント・順位相関 < 0.01・対称・τ の再逆算が宣言値 (e) 切替口(run/CLI・既定 τ)。
"""

from __future__ import annotations

import math
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from shibuya.agents.weekly import WeeklySchedule
from shibuya.engine import relations as RL

SRC = Path("src/shibuya")
WORLD = "data/world/v2"
UNIFORM = 1.0 / 12.0  # 在職 1〜13 週の一様で 2 週未満の割合


def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    ra = np.argsort(np.argsort(a, kind="stable"), kind="stable").astype(np.float64)
    rb = np.argsort(np.argsort(b, kind="stable"), kind="stable").astype(np.float64)
    ra -= ra.mean()
    rb -= rb.mean()
    return float((ra * rb).sum() / math.sqrt((ra * ra).sum() * (rb * rb).sum()))


def _weekly_same_day(n: int, row: tuple[int, int, int]) -> WeeklySchedule:
    counts = np.zeros(n * 7, dtype=np.int64)
    counts[::7] = 1
    off = np.zeros(n * 7 + 1, dtype=np.int64)
    np.cumsum(counts, out=off[1:])
    s, e, c = row
    return WeeklySchedule(None, np.arange(n, dtype=np.int64), off, np.full(n, s, dtype=np.int16),
                          np.full(n, e, dtype=np.int16), np.zeros(n, dtype=np.int8), np.ones(n, dtype=np.int8),
                          np.full(n, c, dtype=np.int32), np.zeros(n, dtype=np.int16))


# ================================================================= (a) 式
def test_v1_is_the_old_formula_and_v2_is_symmetric():
    rng = np.random.default_rng(0)
    u = rng.integers(0, 400_000, 5_000)
    v = rng.integers(0, 400_000, 5_000)
    old = (RL._pair_mix(np.minimum(u, v), np.maximum(u, v)) >> np.uint64(11)).astype(np.float64) / float(1 << 53)
    assert np.array_equal(RL._tenure_unit(u, v, "v1"), old)                          # 旧の式そのもの
    lt = u < v
    tie = (RL._pair_mix(u, v) >> np.uint64(11)).astype(np.float64) / float(1 << 53)
    assert np.array_equal(RL._tenure_unit(u, v, "v1")[lt], tie[lt])                 # 欠陥: 同点の順と同じ値
    for ver in ("v1", "v2"):
        assert np.array_equal(RL._tenure_weeks(u, v, 13.0, ver), RL._tenure_weeks(v, u, 13.0, ver))  # 向きなし
        t = RL._tenure_weeks(u, v, 13.0, ver)
        assert float(t.min()) >= 1.0 and float(t.max()) < 13.0
    assert not np.array_equal(RL._tenure_unit(u, v, "v2"), RL._tenure_unit(u, v, "v1"))
    assert RL._tenure_weeks(u[:3], v[:3], 13.0).tolist() == RL._tenure_weeks(u[:3], v[:3], 13.0, "v2").tolist()
    with pytest.raises(ValueError):
        RL._tenure_unit(u, v, "v3")


# ================================================================= (b) 合成の大組織(全員同点)
def test_all_tied_organisation_bias_is_gone_with_v2():
    """200 人・同じ日課(全員同点)・k 15: v1 は同点の順=在職の短い順に選ぶ(元 id_u < 元 id_v の辺で 2 週未満が
    大半)/ v2 は向きに依らず ≈ 1/12(3,000 辺・二項の標準誤差 0.005 → 許容 ±0.03)。"""
    g = 200
    w = _weekly_same_day(g, (540, 1080, 5))
    p = SimpleNamespace(n=g, household_id=np.full(g, -1), org_id=np.full(g, 3), school_cell=np.full(g, -1))
    got = {}
    for ver in ("v1", "v2"):
        init = RL.initial_edges(p, w, g, tau=None, tenure_hash=ver)
        assert init.u.size == g * RL.REL_K and init.audit["tenure_hash"] == ver
        T = -init.first.astype(np.float64) / 10080.0
        lt = init.u < init.v  # 合成は元 id=行番号
        got[ver] = (float((T[lt] < 2).mean()), float((T[~lt] < 2).mean()), init)
    assert got["v1"][0] > 0.5                                             # 旧: 短い在職に寄る
    for share in got["v2"][:2]:
        assert share == pytest.approx(UNIFORM, abs=0.03)
    # 網(誰と誰が結ばれるか)は版で変わらない=在職期間は選び方に入らない
    assert np.array_equal(got["v1"][2].u, got["v2"][2].u) and np.array_equal(got["v1"][2].v, got["v2"][2].v)


# ================================================================= (c) 順位相関
def test_tenure_u_is_rank_independent_of_the_tie_hash():
    rng = np.random.default_rng(1)
    u = rng.integers(0, 400_000, 300_000)
    v = rng.integers(0, 400_000, 300_000)
    tie = RL._pair_mix(u, v).astype(np.float64)
    lt = u < v
    assert _spearman(RL._tenure_unit(u, v, "v1")[lt], tie[lt]) == pytest.approx(1.0)
    assert abs(_spearman(RL._tenure_unit(u, v, "v2"), tie)) < 0.01
    assert abs(_spearman(RL._tenure_unit(u, v, "v2")[lt], tie[lt])) < 0.01
    # 連番の組(大組織の元 id)でも一様
    a = np.repeat(np.arange(600), 600)
    b = np.tile(np.arange(600), 600)
    ok = a != b
    unit = RL._tenure_unit(a[ok], b[ok], "v2")
    assert float((unit < 1 / 12).mean()) == pytest.approx(UNIFORM, abs=0.005)
    assert abs(_spearman(unit, RL._pair_mix(a[ok], b[ok]).astype(np.float64))) < 0.01


# ================================================================= (d) 全母集団
def test_full_population_initial_net_is_uniform_in_every_kind_and_direction():
    """全 390,067 体(W16+W17)。v2: 種別(世帯/職場/学校)× 向き(元 id の大小)のどれでも在職 2 週未満が
    8.3% ± 1 ポイント・U と同点の順のハッシュの順位相関 < 0.01・u→v と v→u で同じ・τ の再逆算(8b′ と同じ手順=
    ラン開始時の 15 番目の辺の A の中央値を小数 3 桁で切り下げ)が :data:`REL_TAU_V2`。v1 は同じ網で偏る(旧の事実)。"""
    from shibuya.world.assets import assets_available

    if not assets_available(WORLD):
        pytest.skip("W 資産(data/world/v2)が無い")
    from shibuya.agents.population import load_population
    from shibuya.agents.weekly import load_weekly

    pop = load_population(WORLD, n=None, seed=1)
    w = load_weekly(WORLD).restrict_to(pop.source_agent_id)
    m = int(pop.n)
    init = RL.initial_edges(pop, w, m, tau=None)                      # 既定 v2
    assert init.audit["tenure_hash"] == "v2"
    src = np.asarray(pop.source_agent_id, dtype=np.int64)
    su, sv = src[init.u], src[init.v]
    T = -init.first.astype(np.float64) / 10080.0
    T1 = RL._tenure_weeks(su, sv, RL.REL_TENURE_WEEKS, "v1")          # 同じ網で旧の在職期間
    for k in (1, 2, 3):
        for msk in (su < sv, su > sv):
            s = (init.kind == k) & msk
            assert s.sum() > 1000
            assert float((T[s] < 2).mean()) == pytest.approx(UNIFORM, abs=0.01), (k, float((T[s] < 2).mean()))
    for k in (2, 3):                                                   # 旧: 元 id_u < 元 id_v の職場/学校が偏る
        s = (init.kind == k) & (su < sv)
        assert float((T1[s] < 2).mean()) > 0.2
    assert abs(_spearman(RL._tenure_unit(su, sv, "v2"), RL._pair_mix(su, sv).astype(np.float64))) < 0.01
    assert np.array_equal(RL._tenure_weeks(su, sv, 13.0), RL._tenure_weeks(sv, su, 13.0))
    A0 = RL._activation(init.n, init.first, 0, 1.0, RL.REL_D)
    tau = float(RL.tau_from_edges(init.u, A0, m)["tau"])
    assert math.floor(tau * 1000.0) / 1000.0 == RL.REL_TAU_V2


# ================================================================= (e) 切替口
def test_switch_is_checked_and_on_the_cli_and_sets_the_default_tau():
    from shibuya.engine.run import run_day

    with pytest.raises(ValueError):
        run_day(n_agents=10, ticks=2, memory="on", relations="on", rel_tenure_hash="v3")
    text = (SRC / "cli.py").read_text(encoding="utf-8")
    assert '"--rel-tenure-hash"' in text and "rel_tenure_hash=str(args.rel_tenure_hash)" in text
    assert RL.check_rel_tenure_hash("v1") == "v1" and RL.REL_TENURE_HASHES == ("v2", "v1")
    from shibuya.world.assets import assets_available

    if not assets_available(WORLD):
        pytest.skip("W 資産(data/world/v2)が無い")
    from shibuya import cli

    kw = dict(n_agents=300, seed=1, world_dir=WORLD, vocab_version="v3", memory="on", relations="on", ticks=30)
    for ver, tau in (("v2", RL.REL_TAU_V2), ("v1", RL.REL_TAU_V1)):
        s = cli.run(rel_tenure_hash=ver, **kw).run_manifest_fields()["relations"]
        assert s["tau"] == tau and s["init"]["tenure_hash"] == ver
    s = cli.run(rel_tenure_hash="v1", rel_tau=-2.0, **kw).run_manifest_fields()["relations"]
    assert s["tau"] == -2.0                                            # 明示の τ が優先


#: 関係 on の腕の final(mock 5,000 体・seed 1・v3・記憶 on・関係 on・CLI 既定=energy)。v1=HEAD b4c8b1c の値
#: (旧の再現)・v2=修正後(既定)。記録 ``docs/bench/analysis/wave2-2026-09-30/`` §2A-0。
REL_ON_5000_GOLDEN = {
    "v1": ("e4f84d1d176e6ec0", 72_940),
    "v2": ("40409ebed834126b", 72_930),
}


def test_relations_on_arm_golden_old_and_new():
    from shibuya.world.assets import assets_available

    if not assets_available(WORLD):
        pytest.skip("W 資産(data/world/v2)が無い")
    from shibuya import cli

    kw = dict(n_agents=5000, seed=1, world_dir=WORLD, vocab_version="v3", memory="on", relations="on")
    for ver, (final, calls) in REL_ON_5000_GOLDEN.items():
        r = cli.run(rel_tenure_hash=ver, **kw)
        assert (r.final_hash[:16], int(r.llm_calls)) == (final, calls), ver
