"""S46: nav1 の道の線の控えが結果に作用しないことの試験(控えの有り無しで返る線が 1 バイトも違わない)。

正: 返事その 8(``docs/design/prompt-2026-11-16-reply8.md``)§3 の S46 の行・§6-1 の 7/壁打ちの記録 2-60
(``docs/reference/wallbounce-record-2026-11-02_05.md``)。記録は ``docs/bench/analysis/count-347/s46-path-cache.md``。

**控え**: :class:`NavSpace` の ``_shape_cache``。鍵=(出発点の x・y を float32 に丸めたバイト・階・行き先の W1 の節・曲がる
重みの float64 のバイト)→ 線(``RouteGeom`` か、引けなければ None)。上限は ``_shape_cache_cap``(5 万件)で、溢れたら入れた
順の古いものから 1 件捨てる(当たっても順は変えない)。道の重み(接続口の重み・上り 1 m の重み)は組み立てのときに固定され、
道の計算も同じ丸めた出発点で引く。だから控えを返しても計算し直しても同じ線になる、というのが「作用しない」の中身。この試験は
それを、同じ問い合わせの列を控えの有りと無しに当て、返る線の全欄(``dataclasses.fields`` で欄を引く=欄が増えても比べ漏らさ
ない)を dtype・形・バイトで突き合わせて確かめる。

**「無し」の作り方**(src は変えない。今のコードでできる 3 つの方法を読んで選んだ):

- 控えの上限を 0 にする: 使えない。捨てる行 ``if len(cache) >= cap: cache.pop(next(iter(cache)))`` が空の控えでも走り、
  ``next(iter({}))`` が StopIteration で止まる(本番の世界の面で試して確かめた)。
- 控えを通らない内側の関数(``NavPlanner.plan``)を直に呼ぶ: 鍵を作る所と float32 への丸め(``float(np.float32(ox))``)を
  飛ばすので、控えの有り無しのほかの違いが混ざる。丸めを手で同じにして(``float(np.float32(x))`` を渡す)、**問い合わせの
  順を逆にした 3 本目の照合**としてだけ使う(道の計算が呼ぶ順=作業の配列の前の中身に依らないことの確かめ)。
- **選んだ方法**: ``_shape`` を呼ぶ前に毎回 ``_shape_cache.clear()`` する(:func:`without_cache`)。鍵の作り方・丸め・
  計器・道の計算は同じ道を通り、控えだけが毎回空になる。インスタンスの ``_shape`` を包むので、``ensure_routes`` からの呼び
  でも効く。

**確かめること**:

1. 合成の小さな面(data 不要・CI で必ず回る): ``_shape`` の段で、控え有り=控え無し=順を逆にした直の計算。丸めると同じ鍵に
   なる別の float64 の出発点の組を入れる(控えでは 1 つの鍵=計算でも同じ丸め)。引けない問い合わせ(None)も入れる。
2. 合成の面で ``ensure_routes`` の段(体ごとの時間を載せた線=置き場の点・階・時間・接続口・向き・節)も 1 バイト一致
   (人ごとの曲がる重みの腕 ``person`` で、重みの違う鍵を混ぜる)。
3. 控えが溢れる場合(上限を 3 にする): 古い順に捨てられ(捨てた鍵を引き直す)、線は控え無しと 1 バイト一致。
4. data が在るときだけ(印 ``requires_data``): 本番の世界の面(``data/world/v2`` の ``nav1_*``)で 1 と 3 と同じ確かめ。

**条件(記録 2-60)**: 本人の判断で道を選ぶようになったとき・混み具合で重みが変わるようになったときは、控えの鍵にそれを
入れるか、控えを捨てる。この試験が確かめるのは「重みが組み立てのときに固定」の間の一致だけ(重みや選び方を変える口は
試験の中で動かしていない)。その 2 つのどちらかを入れる版では、この試験が通っても控えが作用しないことの確かめにならない。

**確かめていないこと**: 座標の丸め(float32)そのものが道を変えるか(丸めは控えの鍵と道の計算の両方に掛かる=控えの
有り無しでは差が出ない。記録で別に数える)/標準のラン(5,000 体・1 日)は鍵が 5 万件に届かず、捨てる行は通らない
(溢れの場合は 3 の小さな上限でだけ確かめる)/再開で置き場を引き直す道(``tests/engine/space/test_nav1_units.py``
の ``test_resume_replans_the_same_route`` が確かめる)。

逐次ループ宣言: なし(試験)。
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from shibuya.world.model import navmesh as NV
from shibuya.world.model.space import nav1 as N
from tests import _data_ids as D
from tests.build_space import synth as SY

#: 問い合わせの列を作る乱数の seed(試験の材料だけ)。
QUERY_SEED = 20261116


# ------------------------------------------------------------------ 道具
def route_bytes(r):
    """線の全欄 → 比べる値(配列は名・dtype・形・バイト/そのほかは名・型・repr)。None は None。"""
    if r is None:
        return None
    out = []
    for f in dataclasses.fields(r):
        v = getattr(r, f.name)
        if isinstance(v, np.ndarray):
            out.append((f.name, v.dtype.str, v.shape, v.tobytes()))
        else:
            out.append((f.name, type(v).__name__, repr(v)))
    return tuple(out)


def without_cache(space):
    """``space`` の控えを毎回空にする(``_shape`` を呼ぶ前に ``_shape_cache.clear()``・同じ道を通る)。"""
    inner = space._shape

    def shape(ox, oy, ofi, target, turn_w):
        space._shape_cache.clear()
        return inner(ox, oy, ofi, target, turn_w)

    space._shape = shape
    return space


def key32(q) -> tuple:
    """問い合わせ (x, y, 階, 行き先, 曲がる重み) → 控えの鍵と同じ形(出発点を float32 に丸める)。"""
    x, y, fi, tgt, tw = q
    return (np.float32(x).tobytes(), np.float32(y).tobytes(), int(fi), int(tgt), np.float64(tw).tobytes())


def via_shape(space, seq, *, cap_watch: int | None = None):
    """問い合わせの列を ``_shape`` に順に当てた線の並び。``cap_watch`` なら控えの大きさが上限を超えないことも見る。"""
    out = []
    for x, y, fi, tgt, tw in seq:
        out.append(route_bytes(space._shape(x, y, fi, tgt, tw)))
        if cap_watch is not None:
            assert len(space._shape_cache) <= cap_watch
    return out


def direct_reversed(space, seq):
    """控えを通らず ``NavPlanner.plan`` を直に、列の逆の順で呼ぶ(丸めは ``_shape`` と同じにする)。並びは列の順に戻す。"""
    out = [None] * len(seq)
    for i in range(len(seq) - 1, -1, -1):
        x, y, fi, tgt, tw = seq[i]
        r = space.planner.plan(float(np.float32(x)), float(np.float32(y)), int(fi), int(tgt), turn_w=float(tw),
                               climb_w=space.climb_w)
        out[i] = route_bytes(r)
    return out


def make_sequence(origins, n_nodes, turn_ws, rng, *, per_origin=2, repeat=3, bad_targets=(-1,)):
    """出発点ごとに行き先を ``per_origin`` 個と曲がる重みを引いた問い合わせ(引けない行き先も混ぜる)を ``repeat`` 回並べて
    混ぜた列と、重ならない問い合わせの一覧。丸めると同じ鍵になる組を作るため、問い合わせの 1/4 には出発点の x だけを
    float64 で 1 つずらした双子を足す(float32 に丸めると元と同じ値)。"""
    distinct = []
    for k, (x, y, fi) in enumerate(origins):
        tg = rng.choice(n_nodes, size=per_origin, replace=False).tolist()
        if k % 7 == 0:
            tg.append(int(bad_targets[k % len(bad_targets)]))  # 引けない(None を控える)
        for t in tg:
            distinct.append((x, y, int(fi), int(t), float(turn_ws[int(rng.integers(len(turn_ws)))])))
    distinct += [(float(np.nextafter(q[0], np.inf)), *q[1:]) for q in distinct[: max(1, len(distinct) // 4)]]
    seq = [distinct[i] for i in rng.permutation(np.repeat(np.arange(len(distinct)), repeat))]
    return seq, distinct


def check_cache_is_inert(make_space, seq, distinct, *, small_cap=3):
    """控え有り=控え無し=逆順の直の計算(1 バイト)と、控えが溢れる場合の一致。返り値は計器の数(確かめに使う)。"""
    keys = {key32(q) for q in distinct}
    # 前提: 丸めると同じ鍵になる、別の float64 の出発点の組が列に在る
    assert len(keys) < len(set(distinct))
    assert any(q[3] < 0 for q in distinct)  # 引けない問い合わせ(None)が在る

    on = make_space()
    got_on = via_shape(on, seq)
    off = without_cache(make_space())
    got_off = via_shape(off, seq)
    got_direct = direct_reversed(make_space(), seq)

    assert got_on == got_off
    assert got_off == got_direct
    assert any(r is None for r in got_on) and any(r is not None for r in got_on)
    # 控えが効いていた(当たりがある)・無しの側は毎回計算した
    assert on.nav_meter.routes_planned == len(keys)
    assert on.nav_meter.routes_from_cache == len(seq) - len(keys) > 0
    assert off.nav_meter.routes_from_cache == 0 and off.nav_meter.routes_planned == len(seq)

    # 控えが溢れる場合: 上限を小さくして古い順に捨てさせる
    small = make_space()
    small._shape_cache_cap = small_cap
    got_small = via_shape(small, seq, cap_watch=small_cap)
    assert got_small == got_off
    assert small.nav_meter.routes_planned > len(keys)  # 捨てた鍵を引き直した
    return {"keys": len(keys), "queries": len(seq), "planned_small_cap": small.nav_meter.routes_planned}


# ------------------------------------------------------------------ 合成の小さな面(data 不要)
@pytest.fixture(scope="module")
def synth_world(tmp_path_factory):
    out, _ = SY.build_synth(tmp_path_factory.mktemp("nav1_route_cache"))
    return out, NV.load_navmesh(out)


def _synth_space(synth_world, n_agents=64, turn_weight_mode="fixed"):
    out, mesh = synth_world
    return N.NavSpace(mesh, SY.fake_assets(), world_dir=out, seed=1, n_agents=n_agents, tick_seconds=60,
                      turn_weight_mode=turn_weight_mode)


def _synth_origins(mesh, rng, n_random=24):
    """合成の面の出発点: W1 の節の面の上の点の全部と、帯の中の乱数の点(float64)。"""
    gfi = int(mesh.anchor_fi[0])
    dfi = int(mesh.anchor_fi[3])
    # synth.py の帯(地上の横と縦の帯・島・デッキ)の内側
    rects = [(gfi, 5.0, 10.0, 150.0, 14.0), (gfi, 146.0, 10.0, 150.0, 150.0), (gfi, 5.0, 100.0, 20.0, 110.0),
             (dfi, 20.0, 16.0, 120.0, 19.0)]
    pts = [(float(mesh.anchor_x[k]), float(mesh.anchor_y[k]), int(mesh.anchor_fi[k])) for k in range(mesh.anchor_x.size)]
    for _ in range(n_random):
        fi, x0, y0, x1, y1 = rects[int(rng.integers(len(rects)))]
        pts.append((float(rng.uniform(x0 + 0.3, x1 - 0.3)), float(rng.uniform(y0 + 0.3, y1 - 0.3)), fi))
    return pts


def test_cache_on_and_off_give_byte_identical_lines_on_the_synthetic_mesh(synth_world):
    _out, mesh = synth_world
    rng = np.random.default_rng(QUERY_SEED)
    n_nodes = int(mesh.anchor_x.size)
    turn_ws = [N.TURN_WEIGHT_M, 0.0, *N.turn_weights("person", 1, 3).tolist()]
    seq, distinct = make_sequence(_synth_origins(mesh, rng), n_nodes, turn_ws, rng, bad_targets=(-1, n_nodes))
    got = check_cache_is_inert(lambda: _synth_space(synth_world), seq, distinct)
    assert got["queries"] > 2 * got["keys"]


def test_cache_on_and_off_give_byte_identical_timed_routes_through_ensure_routes(synth_world):
    """``ensure_routes`` の段: 体ごとに時間を載せた線(置き場の 7 欄)と返り値が、控えの有り無しで 1 バイト一致。"""
    _out, mesh = synth_world
    rng = np.random.default_rng(QUERY_SEED + 1)
    n_agents = 64
    on = _synth_space(synth_world, n_agents, "person")
    off = without_cache(_synth_space(synth_world, n_agents, "person"))
    assert np.unique(on.turn_w).size > 1  # 人ごとに違う重み=鍵の 5 つ目が動く
    origins = _synth_origins(mesh, rng, n_random=8)
    n_nodes = int(mesh.anchor_x.size)
    pool_cols = ("x", "y", "fi", "t", "link", "ldir", "node")
    batches = 0
    for _round in range(3):
        for start in range(0, n_agents, 16):
            aid = np.arange(start, start + 16)
            o = [origins[int(k)] for k in rng.integers(len(origins), size=aid.size)]
            x = np.array([p[0] for p in o])
            y = np.array([p[1] for p in o])
            fi = np.array([p[2] for p in o], dtype=np.int8)
            tgt = rng.integers(n_nodes, size=aid.size)
            args = (aid, x, y, fi, tgt, np.full(aid.size, -1), np.zeros(aid.size), np.zeros(aid.size),
                    np.zeros(aid.size, dtype=np.int8))
            res_on = on.ensure_routes(*args)
            res_off = off.ensure_routes(*args)
            for a, b in zip(res_on, res_off):
                assert a.dtype == b.dtype and a.tobytes() == b.tobytes()
            for ag in aid.tolist():
                assert on.pool.has(ag) == off.pool.has(ag)
                if not on.pool.has(ag):
                    continue
                s1, n1 = int(on.pool.r_start[ag]), int(on.pool.r_len[ag])
                s2, n2 = int(off.pool.r_start[ag]), int(off.pool.r_len[ag])
                assert n1 == n2
                for c in pool_cols:
                    assert getattr(on.pool, c)[s1:s1 + n1].tobytes() == getattr(off.pool, c)[s2:s2 + n2].tobytes()
            batches += 1
    assert batches == 12
    assert on.nav_meter.routes_from_cache > 0 and off.nav_meter.routes_from_cache == 0
    assert on.nav_meter.routes_planned < off.nav_meter.routes_planned


def test_cache_overflow_drops_the_oldest_and_keeps_the_lines(synth_world):
    """上限 3 の控えに 4 つの鍵を入れると最初の鍵が捨てられ、それを引き直した線は最初の線と 1 バイト一致。"""
    _out, mesh = synth_world
    space = _synth_space(synth_world)
    space._shape_cache_cap = 3
    o = (float(mesh.anchor_x[0]), float(mesh.anchor_y[0]), int(mesh.anchor_fi[0]))
    qs = [(*o, t, N.TURN_WEIGHT_M) for t in (1, 2, 4, 6)]
    first = [route_bytes(space._shape(*q)) for q in qs]
    assert list(space._shape_cache) == [key32(q) for q in qs[1:]]  # 最初の鍵(いちばん古い)が捨てられた
    planned = space.nav_meter.routes_planned
    again = route_bytes(space._shape(*qs[0]))
    assert space.nav_meter.routes_planned == planned + 1  # 控えに無いので引き直した
    assert again == first[0]
    assert list(space._shape_cache) == [key32(q) for q in (*qs[2:], qs[0])]
    assert all(r is not None for r in first)


# ------------------------------------------------------------------ 本番の世界の面(data が在るときだけ)
REAL_IDS = ("world_v2", *(f"world_v2:{f}" for f in (NV.NAV1_META, *NV.NAV1_FILES)))


@pytest.fixture(scope="module")
def real_world():
    from shibuya.world.assets import load_assets

    world = D.ROOTS["world_v2"]
    return world, load_assets(world), NV.load_navmesh(world)


@pytest.mark.requires_data(*REAL_IDS)
def test_cache_on_and_off_give_byte_identical_lines_on_the_real_mesh(real_world):
    world, assets, mesh = real_world
    rng = np.random.default_rng(QUERY_SEED + 2)
    on_surface = np.flatnonzero(np.asarray(mesh.anchor_fi) >= 0)
    n_nodes = int(mesh.anchor_x.size)
    picks = rng.choice(on_surface, size=150, replace=False)
    origins = []
    for k, nd in enumerate(picks.tolist()):
        x, y, fi = float(mesh.anchor_x[nd]), float(mesh.anchor_y[nd]), int(mesh.anchor_fi[nd])
        if k % 3 == 0:  # 節の点から少し離した点(面の外なら 5 m 以内の面へ寄せるか、引けない)
            x += float(rng.uniform(-2.0, 2.0))
            y += float(rng.uniform(-2.0, 2.0))
        origins.append((x, y, fi))
    turn_ws = [N.TURN_WEIGHT_M, *N.turn_weights("person", 1, 4).tolist()]
    seq, distinct = make_sequence(origins, n_nodes, turn_ws, rng, bad_targets=(-1, n_nodes))

    def make():
        return N.NavSpace(mesh, assets, world_dir=world, seed=1, n_agents=16, tick_seconds=60)

    got = check_cache_is_inert(make, seq, distinct, small_cap=16)
    assert got["keys"] >= 300
