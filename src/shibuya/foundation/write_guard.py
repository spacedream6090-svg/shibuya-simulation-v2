"""engine.systems.guard — 系を呼ぶ間だけ置く書きの許可(第 1 期 1-0・草案 §2-6 の A ①・C)。

- SoA: ``core.write_permit.scope(spec.writes.soa)``(解除口が許可の列だけを解く)。
- scratch: ``SCRATCH_PERMIT``(``TickScratch.__setattr__`` が見る=段 C)。buffers: ``BUFFERS_PERMIT``
  (``Buffers.__setattr__`` が見る=段 C・段 FIX で足した)。``None`` は制限なし。
- 許可を外す口(``write_permit.scope``・``set_enabled``・``system_scope``)を呼んでよい置き場と、許可の大域を書き換えて
  よい置き場は試験 ``tests/engine/systems/test_fix_guards.py`` が静的に固定する(段 FIX・検収 L2・L11)。
- 切替口: ``core.write_permit.set_enabled(False)``(か環境変数 ``SHIBUYA_WRITE_GUARD=off``)で SoA と scratch の両方を外す。
- 〔第 1 期 1-3〕出来事の記録(``engine.events.log.EventLog.append``)の書きも同じ形で見る: ``PATHS_PERMIT`` に系の
  ``writes.paths`` を置き、``events_write_allowed()`` が「いまの系は ``E:events.*`` を宣言したか」を返す(段 C と同じ
  実行時の検査・切替口も同じ)。段 B(試験のときの全欄の差)は今までどおり別に見る。

逐次ループ宣言: なし(系 1 回あたり定数回の代入)。
"""

from __future__ import annotations

import fnmatch
from contextlib import contextmanager
from typing import Iterator

from shibuya.foundation import write_permit as _WP
import numpy as np

__all__ = ["CURRENT", "SCRATCH_PERMIT", "BUFFERS_PERMIT", "PATHS_PERMIT", "system_scope", "events_write_allowed",
           "EVENTS_PATH"]

#: いま回している系の名(記録と誤りの文の材料・``None``=系の外)。
CURRENT: str | None = None
#: いまの系が書いてよい scratch の欄(``None``=制限なし)。
SCRATCH_PERMIT: frozenset[str] | None = None
#: いまの系が差し替えてよい buffers の欄(``None``=制限なし)。
BUFFERS_PERMIT: frozenset[str] | None = None
#: 〔1-3〕いまの系の書く外の道筋の宣言(``writes.paths``・``None``=制限なし)。出来事の記録の書きの検査が見る。
PATHS_PERMIT: frozenset[str] | None = None
#: 出来事の記録の道筋の代表(状態台帳の行 ``E`` の属性の 1 つ。宣言 ``E:events.*`` がこれに当たれば書いてよい)。
EVENTS_PATH: str = "E:events._ev_t_ns"


@contextmanager
def system_scope(name: str, soa: frozenset[str] | None, scratch: frozenset[str] | None,
                 buffers: frozenset[str] | None = None, paths: frozenset[str] | None = None) -> Iterator[None]:
    """系 ``name`` を呼ぶ間だけ SoA・scratch・buffers・外の道筋(1-3)の許可を置く(出るときに前の値へ戻す)。"""
    global CURRENT, SCRATCH_PERMIT, BUFFERS_PERMIT, PATHS_PERMIT
    prev = (CURRENT, SCRATCH_PERMIT, BUFFERS_PERMIT, PATHS_PERMIT)
    CURRENT = name
    if _WP.enabled():
        SCRATCH_PERMIT = None if scratch is None else frozenset(scratch)
        BUFFERS_PERMIT = None if buffers is None else frozenset(buffers)
        PATHS_PERMIT = None if paths is None else frozenset(paths)
    try:
        with _WP.scope(soa):
            yield
    finally:
        CURRENT, SCRATCH_PERMIT, BUFFERS_PERMIT, PATHS_PERMIT = prev


def events_write_allowed() -> bool:
    """〔1-3〕いまの系が出来事の記録を書いてよいか(系の外・切替口で外したとき=制限なし=真)。"""
    p = PATHS_PERMIT
    if p is None:
        return True
    return EVENTS_PATH in p or any(fnmatch.fnmatchcase(EVENTS_PATH, x) for x in p if "*" in x)


def _require_thawed(*states: object) -> None:
    """``ufunc.at`` を撃つ前の**穴埋めガード**(層2レビュー指摘・C3 結線で追加)。

    NumPy の ``np.add.at`` / ``np.maximum.at`` は **``flags.writeable=False`` を見ない**
    (`ufunc.at` は buffer protocol を経由せずに書く)。つまり ``freeze()`` だけでは
    「resolve 以外からの一括加算」を止められない。そこで ``AgentState``/``World`` が持つ
    ``_frozen`` フラグ(``frozen`` プロパティ)を**明示的に**検査する。

    Raises:
        ValueError: 凍結中の状態へ ``ufunc.at`` を撃とうとした(=書き込み窓の外)。

    1-0 段 A(草案 §2-6 の A ②・K1): 系ごとの許可(``core.write_permit``)では解除口が許可の列だけを解くので、
    状態の物の ``frozen`` だけでは宣言の外の列への ``ufunc.at`` を止められない。引数に**書く配列そのもの**も渡し、
    配列ごとに ``flags.writeable`` を見る(``economy/ops.py`` の ``transfer``=旧 ``_apply_cash`` と同じ形)。配列は numpy の配列、
    状態の物は ``frozen`` を持つ物として見分ける。

    Note:
        静的側の相方は ``tests/engine/test_add_at_guard.py``
        (``world.``/``agents.`` 由来の配列への ``np.<ufunc>.at`` は resolve.py にしか書けない・直前の
        ``_require_thawed`` が書く配列を引数に持つ)。
    """
    for s in states:
        if isinstance(s, np.ndarray):
            if not s.flags.writeable:
                raise ValueError(
                    "読み取り専用の列へ ufunc.at(np.add.at 等)を撃とうとした。"
                    "この系の書く列の宣言の外(1-0 段 A・草案 §2-6)か、書き込み窓の外"
                )
        elif bool(getattr(s, "frozen", False)):
            raise ValueError(
                "凍結中の状態へ ufunc.at(np.add.at 等)を撃とうとした。"
                "書き込みは resolve の writable() 窓の中だけ(運用設計書 §2.2)"
            )
