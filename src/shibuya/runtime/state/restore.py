"""runtime.state.restore — 割る段で ``engine/resolve.py`` を割った割り先(全ファイルの表 §4・名の表は
``tools/pkgmove/map.toml`` の割る行)。

中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の
方針は、主な割り先 ``act/apply.py`` に残した元の docstring を読むこと。
"""

from __future__ import annotations

import dataclasses
from typing import Any, Mapping
import numpy as np
from shibuya.world.model.agent_table import (
    AgentState,
)
from shibuya.world.model.state import World


# ---------------------------------------------------------------- 10d 再開の書き手(状態を戻す)
def restore_soa(agents: AgentState, world: World, pstate: Any,
                soa: Mapping[str, Mapping[str, np.ndarray]]) -> int:
    """10d: 保存した SoA の列(``engine.resume.collect_soa`` の形)を戻す。返り値=戻した列の数。

    戻す列の集合は状態台帳の軸 2 が ``discardable`` でない列(full-hash と同じ範囲)。保存の側と今の側で
    列の集合・形・型が 1 つでも違えば止める(構成の取り違え=黙って一部だけ戻さない)。値は配列の中身を
    書き換える(配列そのものは替えない=世帯の現金を共有する金の台帳の行もそのまま同じ値になる)。
    """
    from shibuya.runtime.state import ledger as SL

    targets: dict[str, tuple[Any, Any]] = {
        "agents": (agents, agents.registry),
        "cells": (world, world.cells),
        "pois": (world, world.pois),
        "perception": (pstate, None if pstate is None else pstate.registry),
    }
    n = 0
    for place in ("agents", "cells", "pois", "perception"):
        owner, reg = targets[place]
        want = set() if reg is None else {c for c in reg.arrays if c not in SL.full_excluded(place)}
        got = set(soa.get(place, {}))
        if want != got:
            raise ValueError(
                f"保存した SoA の列が今の構成と違う({place}: 足りない {sorted(want - got)[:5]}・"
                f"余分 {sorted(got - want)[:5]})"
            )
        if reg is None:
            continue
        with owner.writable():
            for name, src in soa[place].items():
                dst = reg.field(name)
                src = np.asarray(src)
                if dst.shape != src.shape or dst.dtype != src.dtype:
                    raise ValueError(
                        f"保存した SoA の列の形か型が違う({place}.{name}: 今 {dst.dtype}{dst.shape}・"
                        f"保存 {src.dtype}{src.shape})"
                    )
                dst[...] = src
                n += 1
    return n


def _restore_array_into(dst: np.ndarray, src: np.ndarray) -> None:
    """配列の中身を書き換える(読み取り専用の台帳の配列も、書く間だけ書き込みを許す)。"""
    if not dst.dtype.hasobject and dst.tobytes() == src.tobytes():
        return  # 同じ値(世帯の現金=agents.money と共有する行は SoA を戻した時点で同じ)
    was = bool(dst.flags.writeable)
    if not was:
        try:
            dst.flags.writeable = True
        except ValueError as e:  # 書き込めない土台を持つビュー
            raise ValueError(f"読み取り専用の配列を戻せない: {e}") from None
    try:
        dst[...] = src
    finally:
        if not was:
            dst.flags.writeable = False


def _restore_value(cur: Any, saved: Any) -> tuple[bool, Any]:
    """``cur`` の中身を ``saved`` にする。返り値=(``cur`` をそのまま使えたか, 使う値)。

    配列(同じ形と型)・辞書・リスト・集合・deque は**中身を入れ替える**(同じ物を別の持ち主が指していても
    そろう: 金の台帳の行と ``agents.money``・``run_day`` の局所のリスト など)。辞書は保存の順に入れ直す(挿入順が
    挙動を決める行=O8・O39)。それ以外の値(整数・組・dataclass・Generator など)は保存の値に差し替える。
    """
    from collections import deque

    if isinstance(cur, np.ndarray) and isinstance(saved, np.ndarray):
        if cur.shape == saved.shape and cur.dtype == saved.dtype:
            _restore_array_into(cur, saved)
            return True, cur
        return False, saved
    if isinstance(cur, dict) and isinstance(saved, dict) and type(cur) is type(saved):
        new: dict[Any, Any] = {}
        for k, v in saved.items():
            if k in cur:
                same, val = _restore_value(cur[k], v)
                new[k] = cur[k] if same else val
            else:
                new[k] = v
        cur.clear()
        for k, v in new.items():  # 保存の順(挿入順)
            cur[k] = v
        return True, cur
    if isinstance(cur, list) and isinstance(saved, list) and type(cur) is type(saved):
        out = []
        for i, v in enumerate(saved):
            if i < len(cur):
                same, val = _restore_value(cur[i], v)
                out.append(cur[i] if same else val)
            else:
                out.append(v)
        cur[:] = out
        return True, cur
    if isinstance(cur, (set, deque)) and type(cur) is type(saved):
        cur.clear()
        if isinstance(cur, set):
            cur.update(saved)
        else:
            cur.extend(saved)
        return True, cur
    return False, saved


def restore_items(owners: Mapping[str, Any], items: Mapping[str, Any]) -> int:
    """10d: 保存した外の状態(``engine.resume.collect_items`` の形)を持ち主の属性へ戻す。返り値=戻した数。

    道筋の集合が今の台帳の ``full_items`` と違えば止める。「持ち主が無い(腕が立っていない)」の印は、今の側も
    無いときだけ通す(片方だけ無い=構成の取り違え)。〔第 1 期 1-8b〕腕の行は今の側で持ち主の居る行だけ道筋に足す
    (``SL.arm_items``)=保存と今で腕が違えば道筋の集合の食い違いで止まる。
    """
    from shibuya.runtime.state import ledger as SL
    from shibuya.runtime.state.resume import ABSENT_MARK
    from shibuya.runtime.state.hashes import _ABSENT, resolve_item

    paths = [p for _k, p in SL.full_items() + SL.arm_items(owners, behavior=False)]
    if set(paths) != set(items):
        raise ValueError(
            f"保存した外の状態の道筋が今の台帳と違う(足りない {sorted(set(paths) - set(items))[:5]}・"
            f"余分 {sorted(set(items) - set(paths))[:5]})"
        )
    n = 0
    for path in paths:
        saved = items[path]
        cur = resolve_item(owners, path)
        if isinstance(saved, str) and saved == ABSENT_MARK:
            if cur is not _ABSENT:
                raise ValueError(f"保存では持ち主が無いが今はある: {path}(構成が違う)")
            continue
        if cur is _ABSENT:
            raise ValueError(f"保存では値があるが今は持ち主が無い: {path}(構成が違う)")
        head, _, attr = path.rpartition(".")
        parent = resolve_item(owners, head) if "." in head else owners[head]
        same, val = _restore_value(cur, saved)
        if not same:
            try:
                setattr(parent, attr, val)
            except (AttributeError, dataclasses.FrozenInstanceError) as e:
                raise ValueError(f"外の状態を戻せない: {path}({e})") from None
        n += 1
    return n
