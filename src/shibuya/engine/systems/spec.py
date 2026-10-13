"""engine.systems.spec — 系の宣言の口(第 1 期 1-0・草案 §2-5)。未リサーチ(expedient)の名と形。

- ``Access``: 読む欄・書く欄の集合。``soa``=状態台帳の SoA の鍵(``"agents.cell"``)・``paths``=外の状態の
  ``鍵:道筋``(``"O39:conv.sessions"``・末尾の ``*`` で持ち主の道筋の前方一致=``"O55:runner.traffic.*"``。行は割らない)・
  ``scratch``=``TickScratch`` の欄・``buffers``=``Buffers`` の欄・``tally``=``RunStats`` の欄(診断。名は ``stats`` を
  避けた=外の状態の行の属性の名と衝突する)・``box``=箱の属性の参照(``"layers.conv"``・``"cfg.tick_seconds"``・読む欄の
  AST の検査 D③ の材料)。
- ``SystemSpec``: 名・群(名札)・timing(草案の slot・``tick``・``day_head``・``day_end``・``run_head``・``run_end``)・fn・reads・writes・
  resolve_ops(呼んでよい resolve の口=手で書く表)・calls_llm(``""``・``send``・``receive``・``drain``)・when(立つ条件の名)・
  origin(元の区間)。**``writes.soa`` は ``resolve_ops`` の静的な閉包から機械で作る**(``make``・手で書かない=草案 §2-5
  〔親の決め〕)。

逐次ループ宣言: なし。
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field, replace
from typing import Any, Callable

from shibuya.engine.systems import allow as AL

__all__ = ["Access", "SystemSpec", "make", "path_allowed", "TIMINGS"]

TIMINGS: tuple[str, ...] = ("run_head", "day_head", "tick", "day_end", "run_end")


@dataclass(frozen=True)
class Access:
    soa: frozenset[str] = frozenset()
    paths: frozenset[str] = frozenset()
    scratch: frozenset[str] = frozenset()
    buffers: frozenset[str] = frozenset()
    tally: frozenset[str] = frozenset()
    box: frozenset[str] = frozenset()


@dataclass(frozen=True)
class SystemSpec:
    name: str
    group: str
    #: 草案の ``slot``(名の衝突=外の状態の行 O29 の ``energy.out_of_area.slot`` を避けた)
    timing: str
    fn: Callable[..., Any] | None
    reads: Access
    writes: Access
    resolve_ops: frozenset[str]
    calls_llm: str = ""
    when: str = ""
    origin: str = ""
    #: 手で書いた ``writes.soa``(``None``=閉包だけ)。閉包と食い違えば試験で落とす(D ②)。
    soa_declared: frozenset[str] | None = field(default=None, compare=False)


def _fs(x: Any) -> frozenset[str]:
    if isinstance(x, str):
        return frozenset(x.split())
    return frozenset(x or ())


def make(name: str, group: str, timing: str, fn: Callable[..., Any] | None, *, resolve_ops: Any = (),
         reads: Any = (), paths: Any = (), scratch_w: Any = (), scratch_r: Any = (), buffers_w: Any = (),
         buffers_r: Any = (), tally: Any = (), calls_llm: str = "", when: str = "", origin: str = "") -> SystemSpec:
    """宣言を 1 つ作る(``writes.soa`` は ``resolve_ops`` の閉包)。文字列は空白で区切った名の並び。"""
    ops = _fs(resolve_ops)
    soa = AL.writes_for_ops(ops)
    return SystemSpec(
        name=name, group=group, timing=timing, fn=fn,
        reads=Access(scratch=_fs(scratch_r), buffers=_fs(buffers_r), box=_fs(reads)),
        writes=Access(soa=soa, paths=_fs(paths), scratch=_fs(scratch_w), buffers=_fs(buffers_w), tally=_fs(tally)),
        resolve_ops=ops, calls_llm=calls_llm, when=when, origin=origin,
    )


def with_fn(spec: SystemSpec, fn: Callable[..., Any]) -> SystemSpec:
    return replace(spec, fn=fn)


def path_allowed(key: str, patterns: frozenset[str]) -> bool:
    """外の状態の鍵 ``"O39:conv.sessions"`` が宣言の道筋(前方一致の ``*`` を含む)に入るか。"""
    if key in patterns:
        return True
    return any(fnmatch.fnmatchcase(key, p) for p in patterns if "*" in p)
