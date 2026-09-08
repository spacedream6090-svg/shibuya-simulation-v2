"""B4 の「安い変化検出器」と「描画バイト」の関係を測る診断テスト+**結線後のゲート**。

契約書 §2.2/§5 は「B2/B4 の**バイト列ハッシュ**=キャッシュキー=変化検出器=dormant 再送抑止」
と言う(三役=1本)。C2 の ``engine.change_detect`` は**構造化欄**(密度段8値・騒音段・営業中POI数)
の xxh64 を安い検出器として持ち、C3 の描画は**別の欄**(LOS 6段・騒音段・流れ・顕著行為)に依存した。
両者が一致していないと「起床条件(i) が発火しないのに B4 の文面が変わる」= dormant 抑止の取りこぼしが
起きる。本テストは

  1. C2 の欄(密度段8値・騒音段・営業中POI数)の**取りこぼし件数を測って印字**し(記録・報告用)、
  2. C3 の結線後に engine が読む欄(``hashes.b4_field_row``)では取りこぼしが **0** であること、
  3. 逆向き(欄ハッシュが変われば描画バイトも必ず変わる)も **0** であること

を機械検査する(engine は import しない=層契約。engine 側からの同じ検査は
``tests/engine/test_renderer_wiring.py`` にある)。
"""

from __future__ import annotations

import numpy as np

from shibuya.agents.state import AgentState
from shibuya.perception import hashes as H
from shibuya.perception import normalize as N
from shibuya.perception import templates as T
from shibuya.perception.renderer import Renderer
from shibuya.world.state import DENSITY_STAGE_EDGES, World


def _setup(n_cells: int = 64, seed: int = 2):
    w = World.synthetic(n_cells=n_cells, seed=seed)
    a = AgentState(n_cells)
    a.cell[:] = np.arange(n_cells)
    return w, a, Renderer(w, a, seed=1)


def _c2_style_rows(w: World, tick: int) -> np.ndarray:
    """C2(結線前)の欄: 密度段8値・騒音段・営業中POI数 —— **world だけ**から作る。"""
    return np.stack(
        [
            w.density_stage().astype(np.int32),
            np.asarray(w.cells.noise_stage, dtype=np.int32),
            w.open_count_per_cell(tick).astype(np.int32),
        ],
        axis=1,
    )


def _c3_style_rows(w: World, r: Renderer, tick: int) -> np.ndarray:
    """C3(結線後)の欄: ``engine.change_detect.b4_block_raw`` と同じ作り方を知覚側の
    部品だけで再現する(LOS 6段・騒音段・流れ・顕著行為ダイジェスト)。"""
    per_m2 = np.asarray(w.cells.density, dtype=np.float64) / np.maximum(
        r.assets.walkable_area_m2, 1.0
    )
    los = N.peg_stage_array(per_m2, T.DENSITY_LOS_EDGES_PER_M2)
    ns = r.assets.noise_stage_for_tick(r.clock_fn(int(tick)))
    zeros = np.zeros(w.n_cells, dtype=np.int32)
    return H.b4_field_row(los, ns, zeros, zeros)


def _sweep(rows_fn, ticks=range(0, 600, 10), n_cells: int = 64):
    """密度をランダムに動かしながら「欄ハッシュ変化」と「描画バイト変化」を突き合わせる。"""
    w, a, r = _setup(n_cells)
    g = np.random.default_rng(0)
    prev_hash: np.ndarray | None = None
    prev_bytes: list[bytes] | None = None
    missed = over = changes = 0
    for tick in ticks:
        with w.writable():
            w.cells.density[:] = g.integers(0, 4_000, size=w.n_cells)
        r.prepare_tick(tick)
        tc = r._tickc
        h = H.field_row_hashes(rows_fn(w, r, tick))
        body = [r._b4(c, tc, []) for c in range(w.n_cells)]
        if prev_hash is not None:
            hash_changed = h != prev_hash
            byte_changed = np.array(
                [body[c] != prev_bytes[c] for c in range(w.n_cells)]
            )
            changes += int(byte_changed.sum())
            missed += int((byte_changed & ~hash_changed).sum())
            over += int((~byte_changed & hash_changed).sum())
        prev_hash, prev_bytes = h, body
    return changes, missed, over


def test_c2_field_row_missed_almost_half_of_the_rendered_changes(capsys):
    """記録: C2 の欄(密度段8値)で見ると LOS の跨ぎを取りこぼす件数(結線の根拠)。"""
    changes, missed, over = _sweep(lambda w, r, t: _c2_style_rows(w, t))
    with capsys.disabled():
        print(
            f"\n[B4 検出器のずれ・C2 の欄] 描画バイト変化 {changes} 件のうち "
            f"欄ハッシュで検出できない取りこぼし {missed} 件({missed / max(1, changes):.1%})・"
            f"逆に欄だけが変わる過検出 {over} 件"
            f"(密度段の刻み {DENSITY_STAGE_EDGES} は人/セル・LOS は人/m²)"
        )
    assert changes > 0
    assert missed > 0, "この行は『ずれがあった』という記録。0 になったら C2 の欄が変わっている"


def test_c3_field_row_misses_nothing_and_never_over_detects(capsys):
    """ゲート: 結線後の欄(``hashes.b4_field_row``)は描画バイト変化を**1件も落とさない**。

    逆向き(欄ハッシュが変われば描画バイトも変わる)も 0 でなければならない。
    ここが成り立っているので「起床条件(i)=B4 ハッシュ変化」と「文面が変わる」が同値になる。
    """
    changes, missed, over = _sweep(_c3_style_rows)
    with capsys.disabled():
        print(
            f"\n[B4 検出器のずれ・C3 結線後の欄] 描画バイト変化 {changes} 件・"
            f"取りこぼし {missed} 件・過検出 {over} 件"
        )
    assert changes > 0
    assert missed == 0, "起床条件(i) が鳴らないのに B4 の文面が変わっている"
    assert over == 0, (
        "欄ハッシュが変わったのに文面が変わらない(過検出=無駄な起床)。"
        "顕著行為ダイジェストが入ると切り詰めで同文になりうるので、その時はここを緩める"
    )


def test_perception_field_hash_is_a_true_refinement():
    """知覚側の欄ハッシュは描画バイトの refinement(欄が同じ ⇒ バイトも同じ)。"""
    w, a, r = _setup()
    g = np.random.default_rng(1)
    seen: dict[int, bytes] = {}
    for tick in range(0, 600, 10):
        with w.writable():
            w.cells.density[:] = g.integers(0, 4_000, size=w.n_cells)
        r.prepare_tick(tick)
        tc = r._tickc
        for c in range(w.n_cells):
            fh = int(tc.b4_field_hash[c])
            body = r._b4(c, tc, [])
            assert seen.setdefault(fh, body) == body


def test_prepare_tick_publishes_the_rows_the_engine_hashes():
    """``Renderer.b4_field_rows`` が ``prepare_tick`` の欄そのもの(engine が読む 1 本)。"""
    w, a, r = _setup()
    r.prepare_tick(600)
    rows = r.b4_field_rows
    assert rows.shape == (w.n_cells, 4) and rows.dtype == np.int32
    assert np.array_equal(H.field_row_hashes(rows), r._tickc.b4_field_hash)
