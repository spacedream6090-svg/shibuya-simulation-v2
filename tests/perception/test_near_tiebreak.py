"""小さいもの①(第300 Q107): B5 近接行の**距離の同点**を run_salt の決定論ハッシュで撹拌する。
第 2 批①(第304 Q130): 近接行の**並び**を距離の昇順に(同点は同じ鍵の順)。

Q107 の検査は並びを旧(``near_order="id"``)に固定して「載る人」だけを見る。Q130 の検査は下の節。

- ``id``(旧)= C7 のベクトル化前の実装と同じ(``test_nearby_vectorized`` の基準)=旧 golden。
- ``hash``(既定)= k 人目の距離より近い人は全員・同点の人から足りない分を撹拌鍵の小さい順に。
  **文面と並び(id 昇順)は変えない**。同点が境に無い描画は両方で同じ。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.agents.state import AgentKind, AgentState
from shibuya.perception.renderer import (
    DEFAULT_NEAR_TIEBREAK,
    NEAR_TIEBREAKS,
    Renderer,
    check_near_tiebreak,
    near_tie_keys,
    near_tie_salt64,
)
from shibuya.world.state import World

from tests import golden_env as GE

from .test_nearby_vectorized import _reference_nearby_items, crowd


def tied_crowd(n: int = 200, *, near: str = "hash", seed: int = 7, same_xy: bool = True, salt: bytes | None = None,
               order: str = "id"):
    """1 セルに n 体が**同じ座標**(同じノード)=全員が同点。"""
    w = World.synthetic(n_cells=4, seed=3)
    a = AgentState(n)
    with a.writable():
        a.cell[:] = 0
        a.xy[:] = 50.0 if same_xy else np.random.default_rng(5).uniform(0.0, 100.0, size=(n, 2))
        a.kind[:] = AgentKind.VISITOR
        a.money[:] = 3_000
        a.hunger[:] = 6
        a.last_result_tick[:] = 1
    w.cells.density[:] = w.compute_density(a.cell)
    r = Renderer(w, a, seed=seed, near_tiebreak=near, near_salt=salt, near_order=order)
    r.prepare_tick(600)
    return r, a


def _ids(items):
    return [int(t.split("(")[0].split("-")[1]) for t, _ in items]


def test_modes_and_default():
    assert NEAR_TIEBREAKS == ("hash", "id") and DEFAULT_NEAR_TIEBREAK == "hash"
    assert check_near_tiebreak("id") == "id"
    with pytest.raises(ValueError):
        check_near_tiebreak("random")


def test_id_mode_is_the_previous_implementation_even_with_ties():
    r, a = tied_crowd(near="id")
    tc = r._tickc
    for i in range(a.n):
        assert r._nearby_items(i, 0, tc) == _reference_nearby_items(r, i, 0, tc)
    assert r.near_tie_breaks == 0


def test_hash_mode_mixes_who_is_seen_but_keeps_text_and_order():
    r, a = tied_crowd(near="hash")
    tc = r._tickc
    old_ids = []
    new_ids = []
    for i in range(a.n):
        got = r._nearby_items(i, 0, tc)
        ref = _reference_nearby_items(r, i, 0, tc)
        assert len(got) == len(ref)
        assert all(t.endswith("(未知)") and t.startswith("P-") for t, _ in got)   # 文面の形は同じ
        assert _ids(got) == sorted(_ids(got))                                     # 並びは id 昇順のまま
        assert [d for _, d in got] == [d for _, d in ref]                         # 同点=距離は同じ
        old_ids += _ids(ref)
        new_ids += _ids(got)
    assert r.near_tie_breaks == a.n
    # 旧: いつも行番号の小さい k 人(同じ人ばかり)/新: 観る体ごとに散る
    assert len(set(old_ids)) <= 6
    assert len(set(new_ids)) > 0.5 * a.n
    rho = np.corrcoef(np.bincount(new_ids, minlength=a.n), np.arange(a.n))[0, 1]
    assert abs(rho) < 0.2


def test_hash_mode_equals_id_when_no_tie_sits_on_the_boundary():
    """連続座標(同点なし)では両モードの出力がビットまで同じ(=同点の無いランは不変)。"""
    for mode in ("fixed", "ranking"):
        r_h, a = crowd(n=300, friends=True, mode=mode)
        assert r_h.near_tiebreak == "hash"
        tc = r_h._tickc
        for i in range(a.n):
            got = r_h._nearby_items(i, int(a.cell[i]), tc)
            ref = _reference_nearby_items(r_h, i, int(a.cell[i]), tc)
            assert [t for t, _ in got] == [t for t, _ in ref]
            assert [np.float64(d).tobytes() for _, d in got] == [np.float64(d).tobytes() for _, d in ref]
        assert r_h.near_tie_breaks == 0


def test_strictly_nearer_people_always_stay_in():
    """k 人目より近い人は撹拌に関係なく全員載る(同点の中からだけ選ぶ)。"""
    r, a = tied_crowd(n=40, near="hash")
    with a.writable():  # 観る体 0 と体 5 だけを 0.4 m ずらす=体 0 から見て体 5 は 0 m・残り 38 体は 0.4 m で同点
        a.xy[5] = (50.0, 50.4)
        a.xy[0] = (50.0, 50.4)
    r2 = Renderer(r.world, a, seed=7, near_tiebreak="hash")
    r2.prepare_tick(600)
    for seed_salt in (b"\x01" * 16, b"\x02" * 16, b"\x03" * 16):
        r3 = Renderer(r.world, a, seed=7, near_tiebreak="hash", near_salt=seed_salt)
        r3.prepare_tick(600)
        assert 5 in _ids(r3._nearby_items(0, 0, r3._tickc))  # 一番近い人は salt に依らず必ず載る
    assert 5 in _ids(r2._nearby_items(0, 0, r2._tickc))


def test_keys_are_deterministic_per_observer_and_salt():
    s1 = near_tie_salt64(b"\x01" * 16)
    s2 = near_tie_salt64(b"\x02" * 16)
    ids = np.arange(1_000)
    k1 = near_tie_keys(s1, 3, ids)
    assert k1.dtype == np.uint64 and np.array_equal(k1, near_tie_keys(s1, 3, ids))
    assert not np.array_equal(np.argsort(k1), np.argsort(near_tie_keys(s1, 4, ids)))   # 観る体で順が変わる
    assert not np.array_equal(np.argsort(k1), np.argsort(near_tie_keys(s2, 3, ids)))   # salt で順が変わる
    rank = np.argsort(np.argsort(k1))
    assert abs(np.corrcoef(rank, ids)[0, 1]) < 0.1


def test_default_salt_is_the_run_salt_of_the_seed():
    from shibuya.engine.run import run_salt_for

    r, _a = tied_crowd(seed=11)
    assert r._near_salt64 == near_tie_salt64(run_salt_for(11))
    r2, _ = tied_crowd(seed=11, salt=run_salt_for(12))
    assert r2._near_salt64 != r._near_salt64


def test_cli_has_no_near_tiebreak_flag():
    from shibuya import cli
    from shibuya.engine import run as RUN

    # 〔第 4 期 4-3 版上げ 3 回目の第 2 部〕ランの口の切替口 --near-tiebreak(id=旧挙動)は消した=CLI・run_day に無い
    # (知覚の部品 Renderer の引数は単体試験の基準の口として残す=この表の上の試験)
    src = open(cli.__file__, encoding="utf-8").read()
    assert '"--near-tiebreak"' not in src and '"--near-tiebreak"' not in open(RUN.__file__, encoding="utf-8").read()
    with pytest.raises(TypeError):
        RUN.run_day(n_agents=10, ticks=2, near_tiebreak="id")
    with pytest.raises(SystemExit):
        cli.main(["--near-tiebreak", "id"])


#: classical 1,500 体・seed 1・v3(実世界資産)の final。
#: ``hash``(既定)= 第304 Q130 の距離順+Q107 の同点撹拌 / ``hash_order_id`` = 第304(3c86b6b)の既定=並びは行番号の
#: 昇順(Q130 の前)/ ``classical_tie_id`` = 両方 id = HEAD bb44474 の既定と同じ(Q107 の前=旧 golden)。
#: 第2波 §2A 項 3-1: 3 本とも**交際の相手の旧規則**(``classical_social="near_first"``=近接行の最初の人)の値。
#: 既定(``acquaintance``)の値は ``CLASSICAL_1500_GOLDEN_ACQ``。
#: 10f(K26 (1)): 一番外側の鍵は環境の ``platform_id``(``tests/golden_env.py``)。行の無い環境では A/A だけ。値は 10f の前のまま。
#: 〔改訂(第330・RET)〕前の 3 本は 10e より前の final の定義・乱数・世界の資産・暦の値(hash 91732f34…/26,869・
#: hash_order_id e0a6f3f9…/26,845・classical_tie_id 803f0441…/26,753=ACT の commit で切替口を通して再現できた)。
#: 旧値を再現する切替口を消したので、今の値(final=behavior-hash)に張り替えた。
CLASSICAL_1500_GOLDEN_BY_ENV = {GE.PLATFORM_10F: {
    # 〔第 4 期 4-3 段 10・版上げ 3 回目〕差し替えの世界(W16 を W21 に)で動いた(前 hash f5aebb9a03f141b6…941ee1 / 25_414・
    # hash_order_id 91f9a601124e81dc…074e70 / 25_443・classical_tie_id edd9d6c8067f2da3…32db1a / 25_329=記録 pop43)
    # 〔小さな版上げ・meal_w17〕前 hash 4b3db260…e153f / 25_335・hash_order_id c2a7d482…1cfe2 / 25_284・classical_tie_id 0a1ce7b6…c58de / 25_307
    # (--meal-default validation で戻る)
    "hash": ("fbe9456439ec195d72bfe2b0a68d5d6e1ea4ebd53236cf9f544dc0e50c6c27a1", 26_053),  # 〔2-4 V1〕前 87492778f4582d8fa067757d32b1953516997c92494089ab124840aaaa765bdb / 25_890  # 〔2-4 V2〕前 26b748695ffbf7f928f57352d9169fea630f12ca86efc13af383693411e0c578 / 25_638  # 〔2-4 V3〕前 e313dfaace60e42505a25a5b9f6a530e0e291dcd426260dea26f2f1a86c0da86 / 25_363  # 〔2-4 V4〕前 e4185ac9f6901403328403d6591c8cd43857a24de2938b3f2158e82a50e9ee3d
    # 〔第 4 期 4-3 版上げ 3 回目の第 2 部〕ランの口の切替口(--near-order id・--near-tiebreak id)を消したので hash_order_id
    # (c234caf7f39dea5e / 26,061)と classical_tie_id(c609c5d2b7e99205 / 26,120)の 2 行は消した(再現は安定版のタグ)
}}
#: 今の環境の行(無ければ ``None``=A/A だけ)。
CLASSICAL_1500_GOLDEN = GE.row(CLASSICAL_1500_GOLDEN_BY_ENV)


@pytest.mark.requires_data("world_v2:w2_cells.parquet")
def test_classical_checkpoint_with_the_default_hash_order():
    from pathlib import Path

    from shibuya import cli

    world = Path("data/world/v2")
    # 〔改訂(第330・RET)〕前は 3 本とも 10e より前の値を切替口(hash full・rng stateful・旧資産・暦)で再現した=今の値に
    kw = dict(n_agents=1500, seed=1, world_dir=str(world), vocab_version="v3", policy="classical",
              chooser="classical", classical_social="near_first")
    new = cli.run(**kw)
    if CLASSICAL_1500_GOLDEN is None:  # 10f: golden の行の無い環境は A/A だけ(既定の hash の 1 本)
        GE.assert_aa(lambda: cli.run(**kw), lambda r: (r.final_hash, int(r.llm_calls)), first=new)
        return
    assert (new.final_hash, int(new.llm_calls)) == CLASSICAL_1500_GOLDEN["hash"]
    m = new.run_manifest_fields()["near_tiebreak"]
    # 〔第 2 部〕設定の欄 mode・order(切替口の値)は消した=観測の欄だけ
    assert set(m) == {"ties_broken", "tie_candidates", "order_ties"} and m["ties_broken"] > 0 and m["order_ties"] > 0


# ---------------------------------------------------------------- 第304 Q130: 近接行の並び=距離順
def _dist(items):
    return [d for _, d in items]


def test_near_order_modes_and_default():
    from shibuya.perception.renderer import DEFAULT_NEAR_ORDER, NEAR_ORDERS, check_near_order

    assert NEAR_ORDERS == ("distance", "id") and DEFAULT_NEAR_ORDER == "distance"
    assert check_near_order("id") == "id"
    with pytest.raises(ValueError):
        check_near_order("random")
    r, _a = tied_crowd(order="distance")
    assert r.near_order == "distance"
    assert Renderer(r.world, r.agents).near_order == "distance"


def test_distance_order_sorts_by_distance_and_keeps_text_and_members():
    """連続座標の混雑世界: 距離順は旧(id 順)と**同じ人・同じ文面・同じ距離**を並べ替えただけ。"""
    for mode in ("fixed", "ranking"):
        r_d, a = crowd(n=300, friends=True, mode=mode, near_order="distance")
        tc = r_d._tickc
        n_multi = 0
        for i in range(a.n):
            got = r_d._nearby_items(i, int(a.cell[i]), tc)
            ref = _reference_nearby_items(r_d, i, int(a.cell[i]), tc)
            assert sorted(got) == sorted(ref)                      # 載る人・文面・距離は同じ
            assert _dist(got) == sorted(_dist(got))                # 距離の昇順
            n_multi += len(got) >= 2
        assert n_multi > 50


def test_distance_order_breaks_ties_with_the_same_keys_and_keeps_the_focus_first():
    r, a = tied_crowd(n=60, near="hash", order="distance")
    tc = r._tickc
    for i in range(0, a.n, 7):
        got = _ids(r._nearby_items(i, 0, tc))
        key = near_tie_keys(r._near_salt64, i, np.asarray(got, dtype=np.int64))
        assert list(key) == sorted(key)                            # 全員同点 → 鍵の小さい順
    assert r.near_order_ties > 0
    # 焦点(注意の焦点の欄があるラン)は距離に関係なく先頭
    w = World.synthetic(n_cells=4, seed=3)
    b = AgentState(30, attention_columns=True)
    with b.writable():
        b.cell[:] = 0
        b.xy[:] = np.random.default_rng(9).uniform(0.0, 50.0, size=(30, 2))
        b.kind[:] = AgentKind.VISITOR
        b.money[:] = 3_000
        b.last_result_tick[:] = 1
        far = int(np.argmax(((b.xy - b.xy[0]) ** 2).sum(axis=1)))
        b.focus_target[0] = far
    w.cells.density[:] = w.compute_density(b.cell)
    rf = Renderer(w, b, seed=7)
    rf.prepare_tick(600)
    got = rf._nearby_items(0, 0, rf._tickc)
    assert _ids(got)[0] == far and _dist(got)[1:] == sorted(_dist(got)[1:])


def test_id_order_reproduces_the_previous_order():
    r_i, a = crowd(n=300, friends=True, near_order="id")
    tc = r_i._tickc
    for i in range(a.n):
        assert r_i._nearby_items(i, int(a.cell[i]), tc) == _reference_nearby_items(r_i, i, int(a.cell[i]), tc)
    assert r_i.near_order_ties == 0


def test_cli_has_no_near_order_flag():
    from shibuya import cli
    from shibuya.engine import run as RUN

    # 〔第 2 部〕ランの口の切替口 --near-order(id=旧挙動)は消した=CLI・run_day に無い(Renderer の引数は単体試験の口)
    src = open(cli.__file__, encoding="utf-8").read()
    assert '"--near-order"' not in src and '"--near-order"' not in open(RUN.__file__, encoding="utf-8").read()
    with pytest.raises(TypeError):
        RUN.run_day(n_agents=10, ticks=2, near_order="id")
