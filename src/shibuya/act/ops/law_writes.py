"""act.ops.law_writes — 割る段で ``engine/resolve.py`` を割った割り先(全ファイルの表 §4・名の表は
``tools/pkgmove/map.toml`` の割る行)。

中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の
方針は、主な割り先 ``act/apply.py`` に残した元の docstring を読むこと。
"""

from __future__ import annotations

from typing import Any
import numpy as np
from shibuya.foundation.vocab.agent_codes import ResultCode
from shibuya.world.model.agent_table import (
    AgentState,
)
from shibuya.foundation.ports.ledger import LedgerBundle
from shibuya.world.model.state import World
from shibuya.foundation.write_guard import _require_thawed

__all__ = [
    "restock", "discard_to_bin", "collect_waste", "consume", "set_thermal", "set_notice_state", "set_open_flags",
    "request_open_close",
]


# ---------------------------------------------------------------- 物の操作(U-Goods・§7.2)
def restock(
    world: World,
    ledger: LedgerBundle,
    stores: np.ndarray,
    qty: np.ndarray,
    tick: int,
    *,
    slot: np.ndarray | None = None,
    cause: Any = None,
) -> np.ndarray:
    """店舗補充・納品(外界→棚)。代金は域外仕入(店舗→外界)で払う。

    起動するのは店員・納品ドライバーの行動(C4-subH)。ここは**世界への書き戻し口**として
    ``world.pois.stock``(棚の写し)を更新する役だけを持つ。〔第 1 期 1-9〕``cause``(1-3 の原因)は代金の
    移動(基本操作 ``economy.ops.transfer``)に渡す(出来事を書き、金と物の台帳の行に id の目印を付ける)。

    Returns:
        行ごとの成否 bool。
    """
    if ledger.goods is None:
        raise ValueError("物の台帳が注入されていない")
    s = np.asarray(stores, dtype=np.int64).ravel()
    kw = {} if cause is None else {"cause": cause}
    ok = ledger.goods.restock_many(s, qty, tick, money=ledger.money, slot=slot, **kw)
    with world.writable():
        touched = s[np.asarray(ok)]
        if touched.size:
            world.pois.stock[touched] = ledger.goods.aggregate_stock(touched).astype(
                world.pois.stock.dtype
            )
    return ok


def discard_to_bin(
    world: World,
    ledger: LedgerBundle,
    stores: np.ndarray,
    qty: np.ndarray,
    tick: int,
    *,
    slot: np.ndarray | None = None,
) -> np.ndarray:
    """売れ残りを廃棄ビンへ(棚→ビン)。**棚が減るので写しの書き戻しが要る**。

    世界過程設計書 §7.1 の C 類排出(店舗側)。搬出(ビン→bbox 外)は ``collect_waste``。

    Returns:
        行ごとの成否 bool。
    """
    if ledger.goods is None:
        raise ValueError("物の台帳が注入されていない")
    s = np.asarray(stores, dtype=np.int64).ravel()
    ok = np.asarray(ledger.goods.to_bin_many(s, qty, tick, slot), dtype=bool)
    with world.writable():
        touched = s[ok]
        if touched.size:
            world.pois.stock[touched] = ledger.goods.aggregate_stock(touched).astype(
                world.pois.stock.dtype
            )
    return ok


def consume(
    agents: AgentState,
    ledger: LedgerBundle,
    agent_id: np.ndarray,
    sku: np.ndarray,
    qty: np.ndarray,
    tick: int,
) -> np.ndarray:
    """消費(世帯の所持 → sink)。個体側は ``holdings``(個数)、SKU 別は台帳側の合計。

    設計書 §7.1「SKU別在庫は店舗POI側に置き**個体M1には載せない**」に従い、
    「誰が何を持っているか」は持たない——個体は個数だけ、SKU 別は全世帯合計だけ。
    """
    if ledger.goods is None:
        raise ValueError("物の台帳が注入されていない")
    a = np.asarray(agent_id, dtype=np.int64).ravel()
    q = np.asarray(qty, dtype=np.int64).ravel()
    with agents.writable():
        holdings = agents.registry.holdings
        have = holdings[a].astype(np.int64) >= q
        ok = np.asarray(ledger.goods.consume_many(sku, np.where(have, q, 0), tick))
        if ok.any():
            _require_thawed(agents, holdings)
            np.add.at(holdings, a[ok], (-q[ok]).astype(holdings.dtype))
    return ok


def collect_waste(
    world: World, ledger: LedgerBundle, stores: np.ndarray | None, tick: int
) -> float:
    """廃棄物収集(店舗の廃棄ビン→bbox 外)。搬出質量[g]を返す(棚は動かない)。"""
    if ledger.goods is None:
        raise ValueError("物の台帳が注入されていない")
    return float(ledger.goods.collect_waste(stores, tick))


# ---------------------------------------------------------------- C4: 世界過程の書き戻し口
# 世界過程設計書 §3 実装原則3「世界状態への書き込み口は1本(答申原則5=resolve 経由)。
# **世界過程も例外にしない**」。``engine/processes/*`` は状態を直接触らず、以下の口だけを呼ぶ。
def set_thermal(agents: AgentState, thermal, indices=None) -> None:
    """体感温度(内受容3変数の1本)を一括代入する(知覚契約書 §3 内受容・日陰係数0.86)。

    Args:
        agents: 個体状態。
        thermal: ``(n,)`` の 0-10 値(呼び出し側で丸め・クリップ済み)。
        indices: 〔第 3 期 3-5〕書く体(``None``=全員=前と同じ)。TM5 の予約の腕(``engine.body``)は値の変わりうる体だけを
            渡す(``thermal`` は同じ並び)。
    """
    v = np.asarray(thermal)
    with agents.writable():
        if indices is None:
            agents.registry.thermal[:] = np.clip(v, 0, 10).astype(np.uint8)
        else:
            agents.registry.thermal[np.asarray(indices, dtype=np.int64)] = np.clip(v, 0, 10).astype(np.uint8)


def set_notice_state(pstate, heading, task_flag, indices=None) -> None:
    """知覚側 SoA(M12: 向き量子化+課題従事フラグ)を書く(**書き込み口は resolve 一本**)。

    ``perception.state.PerceptionState`` は ``agents``/``world`` と同じ凍結規律を持ち、
    ``writable()`` を呼んでよいのは本ファイルだけ(``tests/engine/test_two_phase.py``)。
    p_notice(知覚契約書 §3.1)の ``m_ecc`` は向きを読む。課題従事フラグは受けるだけ(〔第 1 期 1-2〕負荷の係数 ``m_load`` は
    消した=確率に効かない)。

    Args:
        pstate: ``PerceptionState``(型は import しない=engine→perception の依存を増やさない)。
        heading: 量子化した向き(0..15)。
        task_flag: ``perception.p_notice.TaskLoad``。
        indices: 書く行(``None`` なら全行)。
    """
    h = np.asarray(heading, dtype=np.uint8)
    t = np.asarray(task_flag, dtype=np.uint8)
    with pstate.writable():
        if indices is None:
            pstate.heading[:] = h
            pstate.task_flag[:] = t
        else:
            idx = np.asarray(indices, dtype=np.int64)
            if idx.size:
                pstate.heading[idx] = h
                pstate.task_flag[idx] = t


def set_open_flags(world: World, open_now, indices=None) -> None:
    """POI の営業フラグ上書き欄を書く(-1=上書きなし / 0=閉 / 1=開)。

    Args:
        world: 世界。
        open_now: 全 POI ぶんの値、または ``indices`` と同じ長さの値。
        indices: 書く行(``None`` なら全行)。
    """
    v = np.asarray(open_now, dtype=np.int8)
    with world.writable():
        if indices is None:
            world.pois.open_now[:] = v
        else:
            idx = np.asarray(indices, dtype=np.int64)
            if idx.size:
                world.pois.open_now[idx] = v


def request_open_close(
    agents: AgentState,
    world: World,
    agent_ids,
    poi_ids,
    want_open,
    tick: int,
    *,
    permitted=None,
    on_unauthorized=None,
) -> np.ndarray:
    """役割行動「開閉店」(行動契約書 §2.2)。権利=当該 POI の担当従業者(権利台帳の ``employ`` の行)。

    〔第 1 期 1-5・CP3・決定 10-12 §1-4〕**権利の無い行も止めない**: 効果(開閉のフラグ)は権利のある行と同じに確定し、
    結果も ``OK``(行動は起きた)。権利の無い行は ``on_unauthorized(agent_ids, poi_ids)`` に渡す(呼び手の過程が出来事の
    記録へ「許可のない行動」として書く=``engine.rights.record.record_unauthorized``。印は出来事の記録にだけ=検収 L2)。
    止めるのは物理と機械の決まった動きだけ(現場に居るかは呼び手の過程が見る)。今の既定(19 構成)で権利の無い行は
    0 回(1-5 の数え)=結果は変わらない。

    Args:
        agents / world: 状態。
        agent_ids: 行為者。
        poi_ids: 対象 POI。
        want_open: 開けるなら True。
        tick: 現在 tick。
        permitted: 行ごとの権利 bool(``None`` なら全て権利なし)。
        on_unauthorized: 権利の無い行の記録の口(``None`` なら記録しない)。

    Returns:
        行ごとの ``ResultCode``(全部 0=OK。権利の有無は結果に出さない)。

    Note:
        効果は PlanSpec の**実績確定**(``ActualLog``)であり、フラグの反映もここで行う。
    """
    a = np.asarray(agent_ids, dtype=np.int64).ravel()
    p = np.asarray(poi_ids, dtype=np.int64).ravel()
    w = np.asarray(want_open, dtype=bool).ravel()
    out_code = np.full(a.size, int(ResultCode.OK), dtype=np.int64)
    if a.size == 0:
        return out_code
    ok = (
        np.zeros(a.size, dtype=bool) if permitted is None else np.asarray(permitted, dtype=bool)
    )
    with agents.writable(), world.writable():
        r = agents.registry
        world.pois.open_now[p] = w.astype(np.int8)  # 1-5: 権利の無い行も止めない(CP3)
        r.last_result[a] = int(ResultCode.OK)  # 1-5 検収 L2: 行動は起きた=OK(許可のない印は出来事の記録にだけ)
        r.last_result_tick[a] = int(tick)
    if (~ok).any() and on_unauthorized is not None:
        on_unauthorized(a[~ok], p[~ok])
    return out_code
