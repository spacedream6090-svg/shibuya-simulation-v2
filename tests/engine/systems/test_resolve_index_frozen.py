"""書きの許可の索引(``runtime.systems.allow.index``)の固定(割る段 6 の S6-G0・計画 §5-3・親の裁定 Q4)。

``allow.index()`` は、書きの閉包を読む resolve のファイル(``allow.RESOLVE_FILES``)を AST で読み、関数ごとの直接の書き・辺(名の
参照)・頂上の表・帳簿の口の呼び出し・局所の別名の書きを作る。段 6 で ``engine/resolve.py`` を割ると ``RESOLVE_FILES`` は書き手の
15 本になる。割る前と後で、この索引が同じことを固定の表 ``resolve_index_frozen.json`` と比べて確かめる(S6-A の後の木で作った)。

正規化(行の番号は入れない・ファイルの本数に依らない):

- 関数の集合・関数ごとの直接の書き(空の関数は落とす)・辺(呼ぶ関数の集合。空の行は落とす)・頂上の表(表の名 → 関数の集合)・
  帳簿の口の (関数, 口)・別名の書きの (関数, 別名)。
- 裁定 Q4(``RESOLVE_FILES`` は書き手だけ=書かないファイル ``foundation/write_guard.py`` は入れない)のため、割った後は
  ``_require_thawed``(凍結の確かめ・書かない)が関数の集合と辺から外れる。外すのは :data:`EXCLUDED` の 1 つだけ(試験で固定)。

今の表の作り方: ``python -m tests.engine.systems.test_resolve_index_frozen``(``PYTHONPATH=src``・リポの根で)が今の正規化を
JSON で出す。表を直すのは、書きの閉包を変える決定の後だけ(割る段は 1 バイト不変=表は変わらない)。

逐次ループ宣言: なし(試験)。
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from shibuya.runtime.systems import allow as AL
from tests import _places as _PL

FROZEN_PATH = Path(__file__).with_name("resolve_index_frozen.json")
SCHEMA = "shibuya.tests/resolve-index/1"
#: 割った後に書き手の一覧から外れる、書かない関数(裁定 Q4)。外すのはこの 1 つだけ。
EXCLUDED: frozenset[str] = frozenset({"_require_thawed"})


def normalize(ix: AL.ResolveIndex) -> dict:
    """索引 → 比べる形(行の番号なし・``EXCLUDED`` を外す・空の行を落とす・並べた)。"""
    funcs = sorted(ix.funcs - EXCLUDED)
    direct = {f: sorted(v) for f, v in sorted(ix.direct.items()) if f not in EXCLUDED and v}
    calls = {f: sorted(v - EXCLUDED) for f, v in sorted(ix.calls.items()) if f not in EXCLUDED and v - EXCLUDED}
    tables = {t: sorted(v - EXCLUDED) for t, v in sorted(ix.tables.items()) if v - EXCLUDED}
    return {
        "schema": SCHEMA,
        "excluded": sorted(EXCLUDED),
        "funcs": funcs,
        "direct": direct,
        "calls": calls,
        "tables": tables,
        "transfer_callers": sorted({f"{f}:{p}" for f, _ln, p in ix.transfer_callers if f not in EXCLUDED}),
        "alias_writes": sorted({f"{f}:{a}" for f, _ln, a in ix.alias_hits if f not in EXCLUDED}),
    }


def diff(now: dict, frozen: dict) -> list[str]:
    """欄ごとの違い(空なら同じ)。"""
    out: list[str] = []
    for k in sorted(set(now) | set(frozen)):
        a, b = now.get(k), frozen.get(k)
        if a == b:
            continue
        if isinstance(a, dict) and isinstance(b, dict):
            for key in sorted(set(a) | set(b)):
                if a.get(key) != b.get(key):
                    out.append(f"{k}[{key}]: 表 {b.get(key)} → 今 {a.get(key)}")
        elif isinstance(a, list) and isinstance(b, list):
            out.append(f"{k}: 表だけ {sorted(set(b) - set(a))} 今だけ {sorted(set(a) - set(b))}")
        else:
            out.append(f"{k}: 表 {b!r} → 今 {a!r}")
    return out


def load_frozen() -> dict:
    doc = json.loads(FROZEN_PATH.read_text(encoding="utf-8"))
    assert doc.get("schema") == SCHEMA, doc.get("schema")
    return doc


@pytest.fixture(scope="module")
def frozen() -> dict:
    return load_frozen()


def test_the_index_matches_the_frozen_table(frozen):
    """今の索引(正規化)=固定の表。割る前(``RESOLVE_FILES`` が 1 本)も割った後(15 本)も同じ。"""
    now = normalize(AL.index())
    assert not diff(now, frozen), "\n".join(diff(now, frozen))
    assert len(now["funcs"]) > 100 and now["direct"] and now["calls"] and now["tables"]
    assert now["transfer_callers"] and now["alias_writes"]


def test_only_require_thawed_is_excluded_and_it_writes_nothing(monkeypatch):
    """外すのは ``_require_thawed`` の 1 つだけ。外す関数は書かない(外しても書きの閉包は同じ)・どの表にも載らない。

    〔S6-G0 の検収 低-2〕割った後は外す関数が書き手の一覧の外のファイル(``foundation/write_guard.py``)へ行き、一覧から作る索引に
    入らない(索引を通した確かめは空回りする)。そこで、外す関数を定義する今のファイルを対応表から引き(見つからなければ落ちる)、
    そのファイルだけを一時の一覧にした索引で、書きと辺が無いことを確かめる(割る前は ``engine/resolve.py``=今の索引と同じ)。"""
    assert EXCLUDED == frozenset({"_require_thawed"})
    ix = AL.index()
    for f in EXCLUDED:
        assert not ix.direct.get(f), f
        assert not ix.calls.get(f), f
        assert not any(f in v for v in ix.tables.values()), f
    if EXCLUDED <= ix.funcs:  # 割る前: resolve の中に在り、書く関数から呼ばれる(外すと辺だけが減る)
        assert any(EXCLUDED & v for v in ix.calls.values())
    for f in sorted(EXCLUDED):
        (home,) = _PL.split_files("engine/resolve.py", (f,))
        monkeypatch.setattr(AL, "RESOLVE_FILES", (home,))
        AL.index.cache_clear()
        try:
            own = AL.index()
        finally:
            monkeypatch.undo()
            AL.index.cache_clear()
        assert f in own.funcs, (home, f)
        assert not own.direct.get(f) and not own.calls.get(f), (home, f, own.direct.get(f), own.calls.get(f))


def test_the_closures_of_every_system_are_the_same_without_the_excluded_edges():
    """``EXCLUDED`` への辺を外しても、系ごとの書きの閉包(``writes_for_ops``)は同じ(外す関数は書かない)。"""
    from shibuya.runtime.systems.table import SYSTEMS

    ix = AL.index()
    cut = dataclasses.replace(ix, calls={f: v - EXCLUDED for f, v in ix.calls.items()},
                              tables={t: v - EXCLUDED for t, v in ix.tables.items()})
    for spec in SYSTEMS:
        assert AL.writes_for_ops(spec.resolve_ops, ix) == AL.writes_for_ops(spec.resolve_ops, cut), spec.name


@pytest.mark.parametrize("mutate,word", [
    # 関数を 1 つ消す
    (lambda ix: dataclasses.replace(ix, funcs=ix.funcs - {"apply"}), "funcs"),
    # 書きを 1 つ足す
    (lambda ix: dataclasses.replace(ix, direct={**ix.direct, "apply": ix.direct.get("apply", frozenset())
                                                 | {"agents.money_for_test"}}), "direct[apply]"),
    # 辺を 1 つ消す
    (lambda ix: dataclasses.replace(ix, calls={f: (v - {sorted(v)[0]} if f == "apply" else v)
                                               for f, v in ix.calls.items()}), "calls[apply]"),
])
def test_negative_a_changed_index_is_seen(frozen, mutate, word):
    """負の対照: 関数を 1 つ消す・書きを 1 つ足す・辺を 1 つ消すと、表との違いに出る。"""
    got = diff(normalize(mutate(AL.index())), frozen)
    assert got and any(x.startswith(word) for x in got), got


if __name__ == "__main__":  # 今の正規化を出す(表を作る・直すとき)
    print(json.dumps(normalize(AL.index()), ensure_ascii=False, indent=1))
