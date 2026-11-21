"""mind.ops — 割る段で ``engine/resolve.py`` を割った割り先(全ファイルの表 §4・名の表は
``tools/pkgmove/map.toml`` の割る行)。

中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の
方針は、主な割り先 ``act/apply.py`` に残した元の docstring を読むこと。
"""

from __future__ import annotations

from typing import Any, Mapping
import numpy as np
from shibuya.foundation.vocab.agent_codes import N_WAKE_CONDITIONS, REFRACTORY_MINUTES, WakeCondition
from shibuya.world.model.agent_table import (
    AgentState,
)
from shibuya.mind.system1.change_detect import DetectResult
from shibuya.foundation.vocab.agent_codes import _REFRACTORY_TICKS
from shibuya.foundation.write_guard import _require_thawed

__all__ = [
    "write_intero_stages", "set_refractory", "clear_refractory", "write_familiarity", "write_memory",
    "write_store_memory", "write_relations", "refractory_ticks", "wake_condition_index",
    "normalized_refractory_scale",
]


def wake_condition_index(key: WakeCondition | int | str) -> int:
    """``refractory_scale`` の鍵 → ``WakeCondition`` の列番号。

    ``WakeCondition``・``int``・条件名(``"PROXIMITY_SWAP"``・大小文字と前後空白は無視)を
    受ける。**日本語の行名は受けない**(表の 11 行と 1 対 1 の対応が崩れるため)。
    """
    if isinstance(key, WakeCondition):
        return int(key)
    if isinstance(key, (int, np.integer)) and not isinstance(key, bool):
        idx = int(key)
    else:
        name = str(key).strip().upper().replace("-", "_")
        try:
            idx = int(WakeCondition[name])
        except KeyError:
            raise ValueError(
                f"未知の起床条件: {key!r}(§6 の 11 行 = {[c.name for c in WakeCondition]})"
            ) from None
    if not 0 <= idx < N_WAKE_CONDITIONS:
        raise ValueError(f"起床条件の列番号は 0..{N_WAKE_CONDITIONS - 1}(いま {key!r})")
    return idx


def refractory_ticks(scale: Mapping[Any, float] | None = None) -> np.ndarray:
    """**ランの実効不応期表**[tick](知覚契約書 §6 の 11 行)。

    ablation ③(§8 第1陣 ③「近接入替の不応期 15 分 ±50%」)の切替口。モジュール定数を
    ``import`` 時に焼くのをやめ、``run_day`` が 1 本組んで ``set_refractory`` に渡す。

    Args:
        scale: ``{起床条件: 倍率}``。``None`` / 空 dict なら **§6 の表そのもの**
            (``_REFRACTORY_TICKS`` を**そのまま**返す=既定でバイト不変)。鍵は
            ``WakeCondition``・列番号・条件名のどれでもよい(``wake_condition_index``)。

    Returns:
        ``(11,)`` int32(書き込み禁止)。tick_seconds=60 なので分=tick。

    expedient(自前規約・設計書に丸めの規定は無い)
        表は**分の整数**なので、倍率をかけた値は ``floor(x + 0.5)``(half-up)で丸める。
        15 分 ×0.5 = 7.5 → **8 分**・15 分 ×1.5 = 22.5 → **23 分**。
        倍率 0 は「床なし」(会話ターンと同じ 0 分)として許す。

    Raises:
        ValueError: 未知の起床条件・負/非有限の倍率。
    """
    if not scale:
        return _REFRACTORY_TICKS
    base = np.asarray(REFRACTORY_MINUTES, dtype=np.float64)
    for key, factor in dict(scale).items():
        f = float(factor)
        if not np.isfinite(f) or f < 0.0:
            raise ValueError(f"不応期の倍率は 0 以上の有限値(いま {key!r}={factor!r})")
        base[wake_condition_index(key)] *= f
    out = np.floor(base + 0.5).astype(np.int32)
    out.flags.writeable = False
    return out


def normalized_refractory_scale(scale: Mapping[Any, float] | None = None) -> dict[str, float]:
    """``refractory_scale`` を manifest 欄用に正規化する(``{条件名: 倍率}``・名前昇順)。"""
    if not scale:
        return {}
    return {
        WakeCondition(wake_condition_index(k)).name: float(v)
        for k, v in sorted(
            dict(scale).items(), key=lambda kv: WakeCondition(wake_condition_index(kv[0])).name
        )
    }


def write_intero_stages(agents: AgentState, result: DetectResult) -> None:
    """``change_detect`` が返した内受容段を書き込む(心の欄 ``fatigue_stage``・``hunger_stage``・``thermal_stage``)。"""
    with agents.writable():
        for crossing in result.crossings:
            if crossing.agent_id.size:
                agents.registry.field(crossing.stage_field)[crossing.agent_id] = (
                    crossing.new_stage.astype(np.int8)
                )


# ---------------------------------------------------------------- 不応期
def set_refractory(
    agents: AgentState, agent_id, condition, tick: int, table: np.ndarray | None = None
) -> None:
    """呼んだ個体×条件の不応期タイマーを張る(知覚契約書 §6 運用規定②)。

    Args:
        table: **ランの実効不応期表**[tick](``refractory_ticks``)。``None`` なら §6 の表
            そのもの(=既定でバイト不変)。ablation ③ はここに振った表を渡す。
    """
    a = np.asarray(agent_id, dtype=np.int64)
    if a.size == 0:
        return
    c = np.asarray(condition, dtype=np.int64)
    tab = _REFRACTORY_TICKS if table is None else np.asarray(table, dtype=np.int32)
    if tab.shape != (N_WAKE_CONDITIONS,):
        raise ValueError(f"不応期表は ({N_WAKE_CONDITIONS},) int32(いま {tab.shape})")
    # 二層の段 2: 活動の満了(``ACTIVITY_EXPIRY``)は不応期表の外=タイマーを張らない。
    # v1/v2 のランでは表の外の条件が来ない=この分岐は 1 行も通らない(バイト不変)。
    in_table = c < N_WAKE_CONDITIONS
    if not bool(np.all(in_table)):
        a, c = a[in_table], c[in_table]
        if a.size == 0:
            return
    until = (int(tick) + tab[c]).astype(np.int32)
    with agents.writable():
        cur = agents.registry.refractory_until
        _require_thawed(agents, cur)
        np.maximum.at(cur, (a, c), until)


def clear_refractory(agents: AgentState, agent_id, condition) -> None:
    """呼んだ個体×条件の不応期タイマーを**戻す**(艦隊の繰り延べ=「呼が成立しなかった」)。

    正典
    - 憲法1(打ち切り禁止)+実装計画書 §7「タイムアウト/キュー満杯=**繰り延べ**(破棄禁止)」。
      不応期は「**呼んだ**から次はしばらく呼ばない」という節約規則(知覚契約書 §6 運用規定②)で
      あって、「答えが返らなかった呼」に対する抑止ではない。答えが返らなかった呼を次 tick へ
      再投入するとき不応期が立ったままだと ``suppressed`` に落ちて**呼が消える**。

    expedient(自前規約)
    - 戻し方は ``refractory_until[agent, condition] = 0``(=どの tick でも起床可)。
      ``set_refractory`` は ``np.maximum.at`` で伸ばすだけなので、同じ (個体, 条件) に別の
      呼が張った不応期があってもここで一緒に消える。実運用では「その (個体, 条件) の最後の呼
      =いま繰り延べになった呼」なので実害はないが、**一般には過剰に戻す**ことを明記する。
    """
    a = np.asarray(agent_id, dtype=np.int64)
    if a.size == 0:
        return
    c = np.asarray(condition, dtype=np.int64)
    in_table = c < N_WAKE_CONDITIONS  # 活動の満了は不応期表の外(タイマーが無い)
    if not bool(np.all(in_table)):
        a, c = a[in_table], c[in_table]
        if a.size == 0:
            return
    with agents.writable():
        _require_thawed(agents)
        agents.registry.refractory_until[a, c] = 0


def write_familiarity(
    agents: AgentState, agent_id, slot, thing, first, last, visits, exposures
) -> None:
    """**親しみの表の行を書く**(4 段目・値と行の選び方は ``engine.familiarity`` が決める)。

    Args:
        agent_id / slot: 体と行(同じ組が 2 度来ない=呼び出し側が 1 体 1 行に畳む)。
        thing / first / last / visits / exposures: その行の新しい値(統合・新規・追い出しの後)。

    ``familiarity_columns`` の無いラン(既定)では呼ばれない。逐次ループ宣言: なし(配列演算)。
    """
    a = np.asarray(agent_id, dtype=np.int64)
    if a.size == 0:
        return
    s = np.asarray(slot, dtype=np.int64)
    with agents.writable():
        _require_thawed(agents)
        r = agents.registry
        r.fam_thing[a, s] = np.asarray(thing, dtype=np.int64).astype(np.int32)
        r.fam_first[a, s] = np.asarray(first, dtype=np.int64).astype(np.int32)
        r.fam_last[a, s] = np.asarray(last, dtype=np.int64).astype(np.int32)
        r.fam_visits[a, s] = np.asarray(visits, dtype=np.int64).astype(np.uint16)
        r.fam_exposures[a, s] = np.asarray(exposures, dtype=np.int64).astype(np.uint16)


def write_memory(
    agents: AgentState, agent_id, slot, kind, first, last, cell, partner, obj, result,
    importance, n,
) -> None:
    """**記憶の表の行を書く**(6 段目 6a・値と行の選び方は ``engine.memory`` が決める)。

    同じ (体, 行) の組は 2 度来ない(呼び出し側が 1 体 1 件の回に分ける)。``memory_columns`` の
    無いラン(既定)では呼ばれない。逐次ループ宣言: なし(配列演算)。
    """
    a = np.asarray(agent_id, dtype=np.int64)
    if a.size == 0:
        return
    s = np.asarray(slot, dtype=np.int64)
    with agents.writable():
        _require_thawed(agents)
        r = agents.registry
        r.mem_kind[a, s] = np.asarray(kind, dtype=np.int64).astype(np.uint8)
        r.mem_tick[a, s] = np.asarray(first, dtype=np.int64).astype(np.int32)
        r.mem_last[a, s] = np.asarray(last, dtype=np.int64).astype(np.int32)
        r.mem_cell[a, s] = np.asarray(cell, dtype=np.int64).astype(np.int32)
        r.mem_partner[a, s] = np.asarray(partner, dtype=np.int64).astype(np.int32)
        r.mem_object[a, s] = np.asarray(obj, dtype=np.int64).astype(np.int32)
        r.mem_result[a, s] = np.asarray(result, dtype=np.int64).astype(np.uint8)
        r.mem_importance[a, s] = np.asarray(importance, dtype=np.int64).astype(np.uint8)
        r.mem_n[a, s] = np.asarray(n, dtype=np.int64).astype(np.uint16)


def write_store_memory(
    agents: AgentState, agent_id, slot, poi, valence, precision, first, last, n, source,
) -> None:
    """**店の評価の記憶の行を書く**(D-120 7a・値と行の選び方は ``engine.memory`` が決める)。

    同じ (体, 行) の組は 2 度来ない(呼び出し側が 1 体 1 件の回に分ける)。``store_memory_columns``
    の無いラン(既定)では呼ばれない。逐次ループ宣言: なし(配列演算)。
    """
    a = np.asarray(agent_id, dtype=np.int64)
    if a.size == 0:
        return
    s = np.asarray(slot, dtype=np.int64)
    with agents.writable():
        _require_thawed(agents)
        r = agents.registry
        r.sm_poi[a, s] = np.asarray(poi, dtype=np.int64).astype(np.int32)
        r.sm_valence[a, s] = np.asarray(valence, dtype=np.float64).astype(np.float32)
        r.sm_precision[a, s] = np.asarray(precision, dtype=np.float64).astype(np.float32)
        r.sm_first[a, s] = np.asarray(first, dtype=np.int64).astype(np.int32)
        r.sm_last[a, s] = np.asarray(last, dtype=np.int64).astype(np.int32)
        r.sm_n[a, s] = np.asarray(n, dtype=np.int64).astype(np.uint16)
        r.sm_source[a, s] = np.asarray(source, dtype=np.int64).astype(np.uint8)


def write_relations(agents: AgentState, agent_id, slot, partner, kind, sign, first, last, n) -> None:
    """**関係辺を書く**(C10 8a・値と辺の選び方は ``engine.relations`` が決める)。

    同じ (体, 辺) の組は 2 度来ない(呼び出し側が 1 体 1 件の回に分ける)。``relation_columns`` の
    無いラン(既定)では呼ばれない。逐次ループ宣言: なし(配列演算)。
    """
    a = np.asarray(agent_id, dtype=np.int64)
    if a.size == 0:
        return
    s = np.asarray(slot, dtype=np.int64)
    with agents.writable():
        _require_thawed(agents)
        r = agents.registry
        r.rel_partner[a, s] = np.asarray(partner, dtype=np.int64).astype(np.int32)
        r.rel_kind[a, s] = np.asarray(kind, dtype=np.int64).astype(np.uint8)
        r.rel_sign[a, s] = np.clip(np.asarray(sign, dtype=np.int64), -127, 127).astype(np.int8)
        r.rel_first[a, s] = np.asarray(first, dtype=np.int64).astype(np.int32)
        r.rel_last[a, s] = np.asarray(last, dtype=np.int64).astype(np.int32)
        r.rel_n[a, s] = np.asarray(n, dtype=np.int64).astype(np.uint16)
