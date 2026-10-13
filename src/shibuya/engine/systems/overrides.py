"""engine.systems.overrides — 試験の負の対照のための宣言の差し替え(第 1 期 1-0・草案 §3-1 の T1〜T3)。**試験のときだけ**。

``drop_soa("decide", "agents.refractory_until")`` のように、ある系の書く SoA の列(閉包)から 1 列を外した宣言で
``table.SYSTEMS``・``table.SPECS`` を一時的に差し替える(``with`` の間だけ)。外した列をその系が書けば、段 A の検査
(解除口が許可の列だけを解く・ufunc.at の配列ごとの検査・台帳の旗の検査)が書いた行で ``ValueError`` を投げる。

逐次ループ宣言: なし。
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import replace
from typing import Iterator

from shibuya.engine.systems import table as _TB

__all__ = ["drop_soa", "drop_scratch", "drop_path", "replace_spec", "wrap_fn"]


@contextmanager
def replace_spec(name: str, **writes_changes: frozenset[str]) -> Iterator[None]:
    """系 ``name`` の ``writes`` の欄を差し替えた宣言で回す(``SYSTEMS`` と ``SPECS`` の両方)。"""
    old = _TB.SPECS[name]
    new = replace(old, writes=replace(old.writes, **writes_changes))
    systems, specs = _TB.SYSTEMS, dict(_TB.SPECS)
    _TB.SYSTEMS = tuple(new if s.name == name else s for s in systems)
    _TB.SPECS[name] = new
    try:
        yield
    finally:
        _TB.SYSTEMS = systems
        _TB.SPECS.clear()
        _TB.SPECS.update(specs)


@contextmanager
def drop_soa(name: str, key: str) -> Iterator[None]:
    old = _TB.SPECS[name].writes.soa
    if key not in old:
        raise KeyError(f"{key} は {name} の書く列(閉包)に無い=外しても負の対照にならない")
    with replace_spec(name, soa=frozenset(old - {key})):
        yield


@contextmanager
def drop_scratch(name: str, field: str) -> Iterator[None]:
    old = _TB.SPECS[name].writes.scratch
    if field not in old:
        raise KeyError(f"{field} は {name} の書く scratch に無い")
    with replace_spec(name, scratch=frozenset(old - {field})):
        yield


@contextmanager
def drop_path(name: str, pattern: str) -> Iterator[None]:
    old = _TB.SPECS[name].writes.paths
    if pattern not in old:
        raise KeyError(f"{pattern} は {name} の書く道筋に無い")
    with replace_spec(name, paths=frozenset(old - {pattern})):
        yield


@contextmanager
def wrap_fn(name: str, inject, *, when: str = "before", T: int = 0) -> Iterator[dict]:
    """系 ``name`` の関数を包み、T 以後の最初の 1 回だけ ``inject(ctx, b)`` を前か後に呼ぶ(段 FIX の負の対照)。
    ``inject`` は宣言の外の書きをわざとする関数。返り値の辞書の ``n`` に差し込んだ回数が入る。"""
    old = _TB.SPECS[name]
    base = old.fn
    done = {"n": 0}

    def fn(ctx, b):  # noqa: ANN001, ANN202
        due = (ctx is None or ctx.T >= T) and not done["n"]
        if due and when == "before":
            done["n"] += bool(inject(ctx, b))
        out = base(ctx, b)
        if due and when == "after" and not done["n"]:
            done["n"] += bool(inject(ctx, b))
        return out

    new = replace(old, fn=fn)
    systems, specs = _TB.SYSTEMS, dict(_TB.SPECS)
    _TB.SYSTEMS = tuple(new if s.name == name else s for s in systems)
    _TB.SPECS[name] = new
    try:
        yield done
    finally:
        _TB.SYSTEMS = systems
        _TB.SPECS.clear()
        _TB.SPECS.update(specs)
