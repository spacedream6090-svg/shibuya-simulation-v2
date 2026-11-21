"""割る段 6 の S6-A: 変化検出の書き戻し ``apply_detection`` を 2 つの関数(``write_b4_hash``=世界の欄 ``cells.b4_hash``・
``write_intero_stages``=心の欄 ``<var>_stage``)に割っても、書いた列と凍結の旗が前と同じ(親の決め事 2 の ①②・段 6 の後も残す)。

- ① 割る前の形の関数(土台 ``bde381e`` の ``engine/resolve.py`` の ``apply_detection``)を試験の中に写して置き、同じ作りの
  世界と体の 2 つの写しに、前の形と新しい 2 つ(b4 → 段の順=呼び手 ``runtime/systems/perceive.py`` と同じ)を別々に当てて、
  ``world.state_hash()``・``agents.state_hash()``・凍結の旗(書き込みの旗が元に戻ること)を比べる。場合= 跨ぎが多い・跨ぎ
  0 件・変わったセル 0 件・両方 0 件・系 ``detect`` の書きの許可の中・凍結していない写し・検出と書き戻しを繰り返す(印の体
  だけの版 ``step_scope`` ありとなし)。負の対照: 2 つのうち片方だけを当てると違う。
- ② AST の比べ: 新しい 2 つの関数の ``with`` の中の文の ``ast.dump`` が、前の形の ``with`` の中の 2 つの文と同じ。関数の
  今の字面は ``inspect.getsource`` で読む(割る段で置き場が変わっても同じことを確かめる)。

逐次ループ宣言: なし(試験)。
"""

from __future__ import annotations

import ast
import dataclasses
import inspect

import numpy as np
import pytest

# 〔割る段 6 の S6-G0〕別名 R を割り先ごとに分けた(R=act/ops/detect_writes・R_MIND=mind/ops。割る前は全部 resolve)
from shibuya.act.ops import detect_writes as R
from shibuya.mind import ops as R_MIND
from shibuya.foundation import write_guard as WG
from shibuya.foundation.vocab.agent_codes import INTERO_VARS
from shibuya.mind.system1 import change_detect as CD
from shibuya.runtime.clocks import step_scope as SS
from shibuya.runtime.systems.table import SPECS
from shibuya.world.model.agent_table import AgentState
from shibuya.world.model.state import World


def _apply_detection_bde381e(agents, world, result):  # noqa: ANN001, ANN202
    """割る前の形(土台 ``bde381e`` の ``engine/resolve.py`` の ``apply_detection``。本体は字面のまま写した)。"""
    with agents.writable(), world.writable():
        if result.changed_cells.size:
            world.cells.b4_hash[result.changed_cells] = result.changed_b4_hash
        for crossing in result.crossings:
            if crossing.agent_id.size:
                agents.registry.field(crossing.stage_field)[crossing.agent_id] = (
                    crossing.new_stage.astype(np.int8)
                )


def _split(agents, world, result) -> None:  # noqa: ANN001
    """新しい 2 つ(呼び手と同じ順=b4 → 段)。"""
    R.write_b4_hash(world, result)
    R_MIND.write_intero_stages(agents, result)


def _agents(n: int, seed: int) -> AgentState:
    """``tests/engine/clock/test_tm3_step_scope.py`` と同じ作り(値と合わない段も混ぜる=多段の跨ぎを含む)。"""
    a = AgentState(n)
    rng = np.random.default_rng(seed)
    for f in ("hunger", "fatigue", "thermal"):
        a.registry.field(f)[:] = rng.integers(0, 11, size=n)
    for _v, sf in INTERO_VARS:
        a.registry.field(sf)[:] = rng.integers(0, 4, size=n)
    return a


def _pair(seed: int, *, frozen: bool = True, n: int = 2000, cells: int = 9) -> list[tuple[World, AgentState]]:
    out = []
    for _ in range(2):
        w, a = World.synthetic(n_cells=cells, seed=seed), _agents(n, seed)
        if frozen:
            w.freeze()
            a.freeze()
        out.append((w, a))
    return out


def _state(w: World, a: AgentState) -> tuple:
    flags = (w.frozen, a.frozen,
             tuple(bool(x.flags.writeable) for reg in (w.cells, w.pois) for x in reg.arrays.values()),
             tuple(bool(x.flags.writeable) for x in a.registry.arrays.values()))
    return w.state_hash(), a.state_hash(), flags


def _detect_spec():
    return SPECS["detect"]


def _both(pair, res, *, new=_split, permit: bool = False) -> tuple[tuple, tuple]:  # noqa: ANN001
    (wa, aa), (wb, ab) = pair
    spec = _detect_spec()
    for fn, (w, a) in ((_apply_detection_bde381e, (wa, aa)), (new, (wb, ab))):
        if permit:
            with WG.system_scope(spec.name, spec.writes.soa, None):
                fn(a, w, res)
        else:
            fn(a, w, res)
    return _state(wa, aa), _state(wb, ab)


def _empty_crossings(res: CD.DetectResult) -> CD.DetectResult:
    return dataclasses.replace(res, crossings=tuple(
        dataclasses.replace(c, agent_id=c.agent_id[:0], new_stage=c.new_stage[:0]) for c in res.crossings))


def _no_cells(res: CD.DetectResult) -> CD.DetectResult:
    return dataclasses.replace(res, changed_cells=res.changed_cells[:0], changed_b4_hash=res.changed_b4_hash[:0])


def _first(pair) -> CD.DetectResult:  # noqa: ANN001
    w, a = pair[0]
    return CD.ChangeDetector(a.n, w.n_cells).detect(w, a, 0)


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_the_first_detection_has_changed_cells_and_many_crossings(seed):
    """場合が空回りしないこと: 最初の検出は変わったセルと跨ぎ(多い)の両方を持つ(比べる試験の種の全部で)。"""
    res = _first(_pair(seed))
    assert res.changed_cells.size > 0
    assert sum(int(c.agent_id.size) for c in res.crossings) > 500


@pytest.mark.parametrize("seed", [1, 2, 3])
@pytest.mark.parametrize("case", ["many", "no_crossings", "no_cells", "neither"])
@pytest.mark.parametrize("permit", [False, True])
def test_split_writes_equal_the_pre_split_form(seed, case, permit):
    pair = _pair(seed)
    res = _first(pair)
    res = {"many": res, "no_crossings": _empty_crossings(res), "no_cells": _no_cells(res),
           "neither": _no_cells(_empty_crossings(res))}[case]
    before = _state(*pair[0])
    old, new = _both(pair, res, permit=permit)
    assert old == new
    assert old[2] == before[2], "凍結の旗が元に戻らない"
    if case == "neither":
        assert old[:2] == before[:2]  # 何も書かない


def test_split_writes_equal_the_pre_split_form_on_unfrozen_copies():
    """凍結していない写し(``writable`` が旗に触らない枝)でも同じ。"""
    pair = _pair(4, frozen=False)
    old, new = _both(pair, _first(pair))
    assert old == new and not old[2][0] and not old[2][1]


@pytest.mark.parametrize("use_scope", [False, True])
def test_repeated_detection_and_write_back_stay_equal(use_scope):
    """検出と書き戻しを繰り返す(値を乱数で少し動かす)。印の体だけの版(``step_scope``)ありとなし。毎回、2 つの写しの
    ハッシュと凍結の旗が同じ。跨ぎ 0 件の回も含む。"""
    pair = _pair(5, n=600, cells=4)
    dets = [CD.ChangeDetector(a.n, w.n_cells) for w, a in pair]
    scs = [SS.StepScope(a.n) for _w, a in pair]
    rng = np.random.default_rng(11)
    n_zero = 0
    for t in range(30):
        k = rng.integers(0, pair[0][1].n, size=0 if t >= 25 else int(rng.integers(0, 30)))  # 終わりの 5 回は動かさない
        vals = {f: rng.integers(0, 11, size=k.size) for f in ("hunger", "fatigue", "thermal")}
        results = []
        for (w, a), det, sc, fn in zip(pair, dets, scs, (_apply_detection_bde381e, _split)):
            with a.writable():
                for f, v in vals.items():
                    a.registry.field(f)[k] = v
            res = sc.detect(det, w, a, t) if use_scope else det.detect(w, a, t)
            fn(a, w, res)
            if use_scope:
                sc.after_detection(a, res)
            results.append(res)
        n_zero += all(c.agent_id.size == 0 for c in results[0].crossings)
        assert _state(*pair[0]) == _state(*pair[1]), t
    assert n_zero > 0, "跨ぎ 0 件の回が無い(場合が空回り)"


@pytest.mark.parametrize("only", ["write_b4_hash", "write_intero_stages"])
def test_negative_one_of_the_two_alone_differs(only):
    """負の対照: 2 つのうち片方だけを当てると、前の形と違う(① の比べが効いている)。"""
    pair = _pair(1)
    res = _first(pair)

    def one(agents, world, result):  # noqa: ANN001, ANN202
        if only == "write_b4_hash":
            R.write_b4_hash(world, result)
        else:
            R_MIND.write_intero_stages(agents, result)

    old, new = _both(pair, res, new=one)
    assert old != new
    assert (old[0] == new[0]) is (only == "write_b4_hash") and (old[1] == new[1]) is (only == "write_intero_stages")


def _with_body(fn) -> tuple[list[ast.stmt], list[str]]:  # noqa: ANN001
    """関数の唯一の ``with`` の中の文と、``with`` の項(``ast.dump``)。"""
    fdef = ast.parse(inspect.getsource(fn)).body[0]
    assert isinstance(fdef, ast.FunctionDef)
    withs = [s for s in fdef.body if isinstance(s, ast.With)]
    assert len(withs) == 1, fn.__name__
    return withs[0].body, [ast.dump(i) for i in withs[0].items]


def test_the_with_bodies_are_the_pre_split_statements():
    """② AST の比べ: 新しい 2 つの ``with`` の中の文=前の形の ``with`` の中の 2 つの文(字下げのほかは同じ)。``with`` の項は
    前の 2 つ(``agents.writable()``・``world.writable()``)を 1 つずつ。引数の名と並び。"""
    old_body, old_items = _with_body(_apply_detection_bde381e)
    b4_body, b4_items = _with_body(R.write_b4_hash)
    st_body, st_items = _with_body(R_MIND.write_intero_stages)
    assert [ast.dump(s) for s in b4_body + st_body] == [ast.dump(s) for s in old_body]
    assert len(old_body) == 2 and sorted(b4_items + st_items) == sorted(old_items)
    assert b4_items == [ast.dump(ast.parse("with world.writable(): pass").body[0].items[0])]
    assert list(inspect.signature(R.write_b4_hash).parameters) == ["world", "result"]
    assert list(inspect.signature(R_MIND.write_intero_stages).parameters) == ["agents", "result"]


def test_the_detect_system_still_writes_the_four_columns():
    """③ の手がかり: 系 ``detect`` の書きの集合は 4 列のまま(凍結の表との比べは ``test_d2_writes_soa_matches_the_frozen_table``)。"""
    assert set(_detect_spec().writes.soa) == {"cells.b4_hash", "agents.fatigue_stage", "agents.hunger_stage",
                                              "agents.thermal_stage"}
