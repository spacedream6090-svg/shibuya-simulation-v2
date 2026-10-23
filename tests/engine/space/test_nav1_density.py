"""段 5-1b 抽出のランの密度の推定の 3 案(腕 ``SHIBUYA_NAV1_DENSITY {cell,neighborhood,unscaled}``)の試験。

正: 段 1 の記録 ``docs/bench/analysis/spatial-2026-10/sp1/README.md`` §4-5(H1・M4-b)/段 5-1b の発注(第 1 段階)。

- 3 案の式(合成の面で手計算と一致)。どの案も分子=面の上に居て建物の中でない体・Fruin の段の境と Kladek の式は同じ。
- 近傍の表: 歩ける面が辺か角で接するセルだけ・違う階の升は比べない・W2 の 8 近傍で同じ層のものだけ。
- 抽出の割合 1(全数のラン)では cell=unscaled。
- 〔第 2 段階・版上げ 4 回目〕既定は neighborhood・案の切替は legacy の結果を動かさない・manifest に案の名・nav1 の腕は run の種類を
  arm にする・変化検出と描画の B4 の密度の段は nav1 では world.cells.density_stage から。
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pytest

from shibuya.engine.geometry import kladek_speed_factor
from shibuya.engine.space import nav1 as N
from shibuya.world import navmesh as NV
from shibuya.world.navmesh import navmesh_available
from shibuya.world.state import DENSITY_STAGE_EDGES_PER_M2
from tests.build_space import synth as SY

SCALE = 0.01


@pytest.fixture(scope="module")
def synth_mesh():
    with tempfile.TemporaryDirectory() as td:
        out, _ = SY.build_synth(Path(td))
        mesh = NV.load_navmesh(out)
        spaces = {mode: N.NavSpace(mesh, SY.fake_assets(), world_dir=out, seed=1, n_agents=10, tick_seconds=60,
                                   population_scale=SCALE, density_mode=mode) for mode in N.DENSITY_MODES}
        yield mesh, spaces


# ------------------------------------------------------------------ 腕
def test_modes_default_and_environment(monkeypatch):
    assert N.DENSITY_MODES == ("cell", "neighborhood", "unscaled") and N.DEFAULT_DENSITY_MODE == "neighborhood"
    assert N.DENSITY_NEIGHBOR_RINGS == 1
    monkeypatch.delenv("SHIBUYA_NAV1_DENSITY", raising=False)
    assert N.density_arm() == "neighborhood" and not N.arms_on()
    for mode in N.DENSITY_MODES:
        monkeypatch.setenv("SHIBUYA_NAV1_DENSITY", mode.upper())
        assert N.density_arm() == mode
        assert N.arms_on() == (mode != "neighborhood")  # 既定でない推定は腕(ランの種類 arm)
    monkeypatch.setenv("SHIBUYA_NAV1_DENSITY", "smooth")
    with pytest.raises(ValueError):
        N.density_arm()
    with pytest.raises(ValueError):
        N.check_density_mode("cells")


# ------------------------------------------------------------------ 近傍の表
def _hand_mesh():
    """升 50 m・セル 100 m(2 × 2)・3 階(どれも層 0)。

    階 0: 行 0 の升 0(セル 0)・行 1 の升 1(セル 0)・行 2 の升 2(セル 3)=升 1 と升 2 は角で接する → (0, 3)・
          行 3 の升 0(セル 2)は行 2 の升 2 と 1 升あく → 接しない。
    階 1: 行 0 の升 3(セル 1)・行 1 の升 2(セル 1)=同じセル。階 0 の行 1 の升 1(セル 0)と横に並ぶが階が違う → 入らない。
    階 2: 行 0 の升 1〜2(セル 0 とセル 1 にまたがるラン)→ (0, 1)。
    """
    cix = np.array([0, 1, 0, 1])
    ciy = np.array([0, 0, 1, 1])
    cb = np.zeros(4, dtype=np.int8)
    lut, cx0, cy0 = NV.cell_lookup_table(cix, ciy, cb)
    row_base = np.array([0, 5, 8], dtype=np.int64)
    row_ptr = np.array([0, 1, 2, 3, 4, 4, 5, 6, 6, 7], dtype=np.int64)
    run_x0 = np.array([0, 1, 2, 0, 3, 2, 1], dtype=np.int32)
    run_x1 = np.array([1, 2, 3, 1, 4, 3, 3], dtype=np.int32)
    floor_band = np.zeros(3, dtype=np.int8)
    floor_ox = np.zeros(3)
    floor_oy = np.zeros(3)
    floor_ny = np.array([4, 2, 1], dtype=np.int64)
    touch = N.cell_contacts(lut, cx0, cy0, 100.0, row_base, row_ptr, run_x0, run_x1, floor_band, floor_ox, floor_oy,
                            floor_ny, 50.0, 4)
    return touch, cix, ciy, cb


def test_cell_contacts_edges_and_corners_on_the_same_floor_only():
    touch, *_ = _hand_mesh()
    got = {tuple(p) for p in np.argwhere(touch).tolist()}
    assert got == {(0, 3), (3, 0), (0, 1), (1, 0)}
    assert np.array_equal(touch, touch.T) and not touch.diagonal().any()


def test_neighborhood_pairs_keep_w2_8_neighbours_of_the_same_band():
    # セル 0 (0,0,地上)・1 (1,0,地上)・2 (3,0,地上)=8 近傍でない・3 (0,0,デッキ)=層が違う
    cix = np.array([0, 1, 3, 0])
    ciy = np.zeros(4, dtype=np.int64)
    cb = np.array([0, 0, 0, 1], dtype=np.int8)
    touch = np.zeros((4, 4), dtype=np.uint8)
    for a, b in ((0, 1), (0, 2), (0, 3)):
        touch[a, b] = touch[b, a] = 1
    src, dst, info = N.neighborhood_pairs(touch, cix, ciy, cb)
    pairs = set(zip(src.tolist(), dst.tolist()))
    assert pairs == {(0, 0), (1, 1), (2, 2), (3, 3), (0, 1), (1, 0)}
    assert info["pairs"] == 1 and info["dropped_other_band"] == 1 and info["dropped_not_w2_neighbor"] == 1
    assert info["rings"] == 1 and info["degree_max"] == 1


def test_synth_neighbours_follow_the_surface(synth_mesh):
    # 合成の面: 地上の横の帯がセル 0–1、縦の帯がセル 1–3、島へのつなぎの帯がセル 0–2 をつなぐ。デッキ(セル 4)の面は
    # x ≥ 100 でデッキのセルが無く地上のセル 1 に倒れる=層が違うので入らない(数だけ)
    _mesh, spaces = synth_mesh
    sp = spaces["neighborhood"]
    pairs = {(a, b) for a, b in zip(sp.density_nb_src.tolist(), sp.density_nb_dst.tolist()) if a != b}
    assert pairs == {(0, 1), (1, 0), (1, 3), (3, 1), (0, 2), (2, 0)}
    assert sp.density_nb_info["dropped_other_band"] == 1
    assert spaces["cell"].density_nb_info is None and spaces["unscaled"].density_nb_info is None


# ------------------------------------------------------------------ 3 案の式
def test_three_estimators_match_the_hand_calculation(synth_mesh):
    _mesh, spaces = synth_mesh
    a = spaces["cell"].walkable_area_m2
    d = np.array([3.0, 1.0, 0.0, 2.0, 4.0])
    nb = {0: (0, 1, 2), 1: (1, 0, 3), 2: (2, 0), 3: (3, 1), 4: (4,)}
    want = {
        "cell": d / (a * SCALE),
        "unscaled": d / a,
        "neighborhood": np.array([sum(d[j] for j in nb[c]) / (sum(a[j] for j in nb[c]) * SCALE) for c in range(5)]),
    }
    for mode, sp in spaces.items():
        got = sp.per_m2(d)
        assert np.allclose(got, want[mode], rtol=1e-12), mode
        # 段と Kladek はどの案も同じ境と式に人/m² を渡すだけ
        stage = np.searchsorted(np.asarray(DENSITY_STAGE_EDGES_PER_M2), want[mode], side="right")
        assert np.array_equal(sp.density_stage(d), stage.astype(np.uint8)), mode
        cells = np.array([0, 1, 2, 3, 4, -1])
        fac = sp.kladek_factor(cells, d)
        assert np.allclose(fac[:5], kladek_speed_factor(want[mode])) and fac[5] == 1.0, mode
    # 近傍は小さい面の升の量子化を抑える向き: 体 1 つの段がセルだけより低いか同じ
    one = np.array([0.0, 0.0, 1.0, 0.0, 0.0])
    assert spaces["neighborhood"].density_stage(one)[2] <= spaces["cell"].density_stage(one)[2]


def test_cell_is_the_stage_1_formula_bit_for_bit(synth_mesh):
    _mesh, spaces = synth_mesh
    sp = spaces["cell"]
    d = np.array([5.0, 0.0, 2.0, 7.0, 1.0])
    assert np.array_equal(sp.per_m2(d), d / sp.density_area_m2)
    assert np.allclose(sp.density_area_m2, sp.walkable_area_m2 * SCALE)


def test_scale_one_makes_cell_equal_unscaled():
    # 39 万体(全数)のランは抽出の割合が 1=population_total と体の数が同じ → cell と unscaled は同じ値
    with tempfile.TemporaryDirectory() as td:
        out, _ = SY.build_synth(Path(td))
        mesh = NV.load_navmesh(out)
        n = 345_858
        sp = {m: N.NavSpace(mesh, SY.fake_assets(), world_dir=out, seed=1, n_agents=10, tick_seconds=60,
                            population_scale=float(n) / float(n), density_mode=m) for m in ("cell", "unscaled")}
        d = np.array([40.0, 900.0, 3.0, 0.0, 250.0])
        assert sp["cell"].population_scale == 1.0
        assert np.array_equal(sp["cell"].per_m2(d), sp["unscaled"].per_m2(d))
        assert np.array_equal(sp["cell"].density_stage(d), sp["unscaled"].density_stage(d))
        cells = np.arange(5)
        assert np.array_equal(sp["cell"].kladek_factor(cells, d), sp["unscaled"].kladek_factor(cells, d))


def test_default_is_neighborhood_and_manifest_names_the_estimator(synth_mesh):
    mesh, spaces = synth_mesh
    with tempfile.TemporaryDirectory() as td:
        out, _ = SY.build_synth(Path(td))
        sp = N.NavSpace(NV.load_navmesh(out), SY.fake_assets(), world_dir=out, seed=1, n_agents=10, tick_seconds=60)
    assert sp.density_mode == "neighborhood" and sp.density_nb_info["pairs"] == 3
    for mode, s in spaces.items():
        nm = s.manifest_fields()["navmesh"]
        assert nm["density_mode"] == mode
        assert (nm["density_neighborhood"] is None) == (mode != "neighborhood")
    info = spaces["neighborhood"].manifest_fields()["navmesh"]["density_neighborhood"]
    assert info["pairs"] == 3 and info["cells_with_neighbors"] == 4 and info["rings"] == 1
    with pytest.raises(ValueError):
        N.NavSpace(mesh, SY.fake_assets(), world_dir=None, seed=1, n_agents=10, tick_seconds=60, density_mode="x")


# ------------------------------------------------------------------ 本物の世界(資産のある所だけ)
STAGE = Path("data/world/v2_stage_5-1")
needs_stage = pytest.mark.skipif(not navmesh_available(STAGE), reason="組んだ資産 v2_stage_5-1 が無い")
KW = dict(n_agents=150, seed=1, ticks=240, vocab_version="v3", activity=True)


@needs_stage
def test_arm_reaches_the_run_and_does_not_move_legacy(monkeypatch):
    from shibuya import cli

    monkeypatch.delenv("SHIBUYA_NAV1_DENSITY", raising=False)
    monkeypatch.delenv("SHIBUYA_SPACE", raising=False)
    base_legacy = cli.run(world_dir=str(STAGE), space="legacy", **KW)
    base = cli.run(world_dir=str(STAGE), **KW)
    m = base.run_manifest_fields()
    assert m["space"]["effective"] == "nav1" and m["space"]["navmesh"]["density_mode"] == "neighborhood"
    assert m["space"]["navmesh"]["density_neighborhood"]["pairs"] > 0
    for mode in ("cell", "unscaled"):
        monkeypatch.setenv("SHIBUYA_NAV1_DENSITY", mode)
        # 旧値の再現(legacy)のランは腕で動かない
        assert cli.run(world_dir=str(STAGE), space="legacy", **KW).final_hash == base_legacy.final_hash, mode
        res = cli.run(world_dir=str(STAGE), **KW)
        nm = res.run_manifest_fields()["space"]["navmesh"]
        assert nm["density_mode"] == mode and nm["density_neighborhood"] is None
    monkeypatch.setenv("SHIBUYA_NAV1_DENSITY", "neighborhood")
    assert cli.run(world_dir=str(STAGE), **KW).final_hash == base.final_hash


def test_b4_density_stage_comes_from_the_nav_stage_only_when_asked():
    """変化検出の B4 の密度の段: los_stage を渡せばそれ(nav1)・渡さなければ density ÷ 歩ける面積(legacy)。"""
    from types import SimpleNamespace

    from shibuya.engine import change_detect as CD

    dens = np.array([0.0, 50.0, 400.0])
    world = SimpleNamespace(n_cells=3, cells=SimpleNamespace(density=dens),
                            noise_stage_for_tick=lambda t: np.zeros(3, dtype=np.uint8))
    legacy = CD.b4_block_raw(world, 0, walkable_area_m2=np.array([100.0, 100.0, 100.0]))
    nav = CD.b4_block_raw(world, 0, walkable_area_m2=np.array([100.0, 100.0, 100.0]),
                          los_stage=np.array([5, 0, 1], dtype=np.uint8))
    assert legacy[:, 0].tolist() == [0, 2, 5] and nav[:, 0].tolist() == [5, 0, 1]
    assert np.array_equal(legacy[:, 1:], nav[:, 1:])
    det = CD.ChangeDetector(4, 3, walkable_area_m2=np.full(3, 100.0))
    assert det.los_from_stage is False
