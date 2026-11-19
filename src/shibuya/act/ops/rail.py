"""act.ops.rail — 割る段で ``engine/resolve.py`` を割った割り先(全ファイルの表 §4・名の表は
``tools/pkgmove/map.toml`` の割る行)。

中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の
方針は、主な割り先 ``act/apply.py`` に残した元の docstring を読むこと。
"""

from __future__ import annotations

from typing import Final
import numpy as np
from shibuya.foundation.vocab.agent_codes import Activity, ResultCode
from shibuya.world.model.agent_table import (
    AgentState,
)
from shibuya.world.model.state import World
from shibuya.foundation.vocab.act_codes import EXIT_WALK_FLAG
from shibuya.act.gate import ResolveOutcome, _fail, _ok

__all__ = [
    "BOARD_WAIT_LIMIT_TICKS", "place_at_external", "rail_arrive", "rail_depart", "sync_transit_activity",
]


BOARD_WAIT_LIMIT_TICKS: Final[int] = 30


def _cell_of_node(world, node) -> np.ndarray:
    """ノード → セル(**この tick の最新値**)。

    ``registry.cell`` は ``apply`` の末尾でまとめて貼り直すので、適用の途中では
    「前の tick の値」である。同じ tick に歩いて着いた体を正しく扱うため、位置は
    ``node`` から引く(``world.assets.node_cell`` は静的表)。
    """
    n = np.asarray(node, dtype=np.int64)
    return np.where(n >= 0, world.assets.node_cell[np.maximum(n, 0)], -1).astype(np.int64)


def _platform_table(world, rail) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """``(路線索引, ホームセル, ホームの代表ノード)``——**今日 便のある線だけ**(昇順)。"""
    lines = np.asarray(getattr(rail, "lines_present", ()), dtype=np.int64)
    if lines.size == 0:
        return lines, lines, lines
    cells = np.asarray(rail.line_cell, dtype=np.int64)[lines]
    nodes = np.where(cells >= 0, world.assets.cell_rep_node[np.maximum(cells, 0)], -1)
    nodes = nodes.astype(np.int64)
    keep = (cells >= 0) & (nodes >= 0)
    return lines[keep], cells[keep], nodes[keep]


def _enter_board_queue(agents, world, ids: np.ndarray, tick: int, out: ResolveOutcome) -> None:
    """ホームに立った体を**乗車待ち**にする(D-51 (a))。

    ``board_since`` は**最初に立った tick**を保つ(FIFO の鍵)。ホームでないセルに居る体
    (経路の終端がホームでなかった等)は意図を落とす=待ち行列に幽霊を残さない。
    """
    r = agents.registry
    if ids.size == 0:
        return
    lines, cells, _ = _platform_table(world, out.rail) if out.rail is not None else (
        np.empty(0, np.int64), np.empty(0, np.int64), np.empty(0, np.int64)
    )
    cell_now = _cell_of_node(world, r.node[ids])
    line_here = np.full(ids.size, -1, dtype=np.int64)
    # 逐次ループ宣言(P4): 便のある路線ぶん(≤8)。個体数に比例しない。
    for j in range(lines.size):
        hit = (line_here < 0) & (cell_now == cells[j])
        if hit.any():
            line_here[hit] = lines[j]
    on_plat = line_here >= 0
    if on_plat.any():
        win = ids[on_plat]
        fresh = win[r.board_since[win] < 0]
        r.board_line[win] = line_here[on_plat].astype(r.board_line.dtype)
        r.activity[win] = int(Activity.WAITING)
        r.target_node[win] = -1
        if fresh.size:
            r.board_since[fresh] = int(tick)
            out.n_board_waiting += int(fresh.size)
            if out.rail is not None:
                # 9b: 計画の退出(歩いて乗る体)は LLM の乗車待ちと分けて数える(既定では 0 件)
                pe = _plan_exit_mask(r, fresh)
                out.rail.n_board_waiting += int(fresh.size - pe.sum())
                if pe.any():
                    out.rail.n_board_waiting_plan_exit = int(getattr(out.rail, "n_board_waiting_plan_exit", 0)) + int(pe.sum())
    if (~on_plat).any():
        miss = ids[~on_plat]
        r.board_line[miss] = -1
        r.board_since[miss] = -1


def _apply_board(agents, world, aid, tgt, tick, out, schedule) -> None:
    """乗車(行動契約書 §2.1 + 運用設計書 §2.6 + **D-51 意図の保持**)。

    契約書の前提条件は「同一セルに停車中・運賃≦残高orIC・**定員に空き**」。D-51
    (2026-09-10・ユーザー決定 (c))で、この前提の**最初の 1 つ**を「満たすまで世界が運ぶ」
    に広げた(**判断は 1 回・実行は世界**=MATSim の計画実行と同じ形。意味の拡張は
    実装計画書 §8 の「D-51 乗車の意図保持」節に登録。設計書本文は書き換えていない)。

    - ホームに居る → **乗車待ち**(``board_line``/``board_since``)に入る。実際に乗せるのは
      ``_serve_board_queue``(停車中の列車へ FIFO)。
    - ホーム以外に居る → 最寄りの(**行ける**)ホームへ ``target_node`` を張って歩き出す。
      到着は ``_apply_engine_step`` が拾い、そのまま待ち行列へ入る。
    - 乗車中・域外滞在(``transit_state != 0``)→ ``NO_TRAIN``(従来どおり)。
    - 行けるホームが 1 つも無い → ``NO_TRAIN``(契約書 §2.1 の 3 語に**新語を足さない**。
      内訳は ``rail.counters()['board_unreachable']`` に出す)。

    Note:
        逐次ループ宣言(P4): **便のある路線ぶん**のループ 2 本(≤8×2)。個体数に比例しない。
    """
    r = agents.registry
    if aid.size == 0:
        return
    rail = out.rail
    if rail is None or not bool(getattr(rail, "active", False)):
        _fail(agents, aid, ResultCode.NO_TRAIN, tick, out)  # C2 互換(列車が無い世界)
        return
    rail.n_board_intent += int(aid.size)
    can_try = r.transit_state[aid] == 0
    _fail(agents, aid[~can_try], ResultCode.NO_TRAIN, tick, out)
    aid = aid[can_try]
    if aid.size == 0:
        return
    lines, cells, nodes = _platform_table(world, rail)
    if lines.size == 0:
        rail.n_board_unreachable += int(aid.size)
        _fail(agents, aid, ResultCode.NO_TRAIN, tick, out)
        return
    node_now = r.node[aid].astype(np.int64)
    cell_now = _cell_of_node(world, node_now)

    # ---- ① すでにホームに居る → 待ち行列へ ----
    on_plat = np.zeros(aid.size, dtype=bool)
    # 逐次ループ宣言: 便のある路線ぶん(≤8)
    for j in range(lines.size):
        on_plat |= cell_now == cells[j]
    if on_plat.any():
        ids = aid[on_plat]
        _enter_board_queue(agents, world, ids, tick, out)
        _ok(agents, ids, tick, out)

    # ---- ② ホーム以外 → 最寄りの行けるホームへ(意図の保持) ----
    rest = aid[~on_plat]
    if rest.size == 0:
        return
    rnode = node_now[~on_plat]
    xy = world.assets.node_xy[np.maximum(rnode, 0)].astype(np.float64)
    pxy = world.assets.node_xy[nodes].astype(np.float64)
    # 直線距離の昇順(同距離は**路線索引の昇順**=決定論)。経路長ではない=expedient。
    d2 = ((xy[:, None, :] - pxy[None, :, :]) ** 2).sum(axis=2)
    order = np.argsort(d2, axis=1, kind="stable")
    pick = np.full(rest.size, -1, dtype=np.int64)
    dest = np.full(rest.size, -1, dtype=np.int64)
    todo = np.arange(rest.size, dtype=np.int64)
    # 逐次ループ宣言: 路線ぶん(≤8)。近い順に「経路があるか」を見て最初に通ったものを採る。
    for rank in range(lines.size):
        if todo.size == 0:
            break
        cand = order[todo, rank]
        dn = nodes[cand]
        nxt = np.asarray(world.graph.route_next_node(rnode[todo], dn), dtype=np.int64)
        good = (nxt >= 0) | (dn == rnode[todo])
        if good.any():
            pick[todo[good]] = lines[cand[good]]
            dest[todo[good]] = dn[good]
        todo = todo[~good]
    got = pick >= 0
    if got.any():
        ids = rest[got]
        r.board_line[ids] = pick[got].astype(r.board_line.dtype)
        r.board_since[ids] = -1  # まだホームに立っていない(待ち時間は数えない)
        dest_got = dest[got]
        same = dest_got == rnode[got]
        walk = ids[~same]
        if walk.size:
            r.activity[walk] = int(Activity.MOVING)
            r.target_node[walk] = dest_got[~same].astype(r.target_node.dtype)
            rail.n_board_walking += int(walk.size)
            if out.defect_fixes:
                # 〔11-03 M11〕満席の列に並んでいた体がホームへ歩き出した=列を離れる(失敗は書かない)
                left = walk[r.queue_poi[walk] >= 0]
                if left.size:
                    r.queue_poi[left] = -1
                    r.queue_since[left] = -1
                    out.n_queue_left_by_board += int(left.size)
        if same.any():
            _enter_board_queue(agents, world, ids[same], tick, out)
        _ok(agents, ids, tick, out)
    if (~got).any():
        lost = rest[~got]
        rail.n_board_unreachable += int(lost.size)
        _fail(agents, lost, ResultCode.NO_TRAIN, tick, out)


def _serve_board_queue(agents, world, tick: int, out: ResolveOutcome) -> None:
    """停車中の列車へ待ち行列から乗せる + 待ちの打ち切り(D-51 (a)(d))。

    順序は ``board_since`` 昇順 → ``agent_id`` 昇順の **FIFO**(決定論)。受容は従来どおり
    ``rail.accept_quota``(§2.6 の混雑率→受容率)。乗れなかった体は**待ち続ける**
    (``TRAIN_FULL`` を「直前の結果」に書くだけ)。運賃を払えない体は意図を落とす
    (待ち続けても払えないため=``FARE_SHORT``)。

    同じホームセルに複数の便が停まっている tick では、**先頭の便で 1 回だけ試す**
    (満員で断られた体は同じ tick の次の便には乗らない=D-51 前の ``_apply_board`` と同じ
    規約・expedient)。渋谷の混雑率は全線 200% 未満なので乗り残し自体が通常 0。

    Note:
        逐次ループ宣言(P4): **この tick に停車中の列車数**ぶんのループ 1 本
        (路線 8 × 方向 2 = 高々 16 級)。個体数には比例しない。
    """
    r = agents.registry
    rail = out.rail
    if rail is None or not bool(getattr(rail, "active", False)):
        return
    # 全個体を走るのはこの 1 本だけ(以降は「意図を持つ体」だけの小さい添字で回す)
    held = np.flatnonzero(r.board_line >= 0)
    if held.size == 0:
        return
    waiting = held[(r.board_since[held] >= 0) & (r.transit_state[held] == 0)]
    trains = np.asarray(rail.trains_at_platform(int(tick)), dtype=np.int64)
    if waiting.size and trains.size:
        cell = _cell_of_node(world, r.node[waiting])
        plat = np.asarray(rail.platform_cell, dtype=np.int64)[trains]
        fare = int(rail.fare_yen)
        served = np.zeros(waiting.size, dtype=bool)
        boarded: list[tuple[int, np.ndarray]] = []
        full: list[np.ndarray] = []
        poor: list[np.ndarray] = []
        # 逐次ループ宣言: 停車中の列車ぶん(≤ 路線×方向)
        for k in range(trains.size):
            here = np.flatnonzero((~served) & (cell == plat[k]))
            if here.size == 0:
                continue
            served[here] = True
            ids = waiting[here]
            ids = ids[np.lexsort((ids, r.board_since[ids].astype(np.int64)))]  # FIFO
            pay_ok = (r.money[ids].astype(np.int64) >= fare) | _plan_exit_mask(r, ids)  # 9b: 計画の退出は免除
            poor.append(ids[~pay_ok])
            ids = ids[pay_ok]
            if ids.size == 0:
                continue
            quota = int(rail.accept_quota(int(trains[k]), int(ids.size)))
            boarded.append((int(trains[k]), ids[:quota]))
            full.append(ids[quota:])
        for arr in poor:
            if arr.size:
                r.board_line[arr] = -1
                r.board_since[arr] = -1
                r.activity[arr] = int(Activity.IDLE)
                _fail(agents, arr, ResultCode.FARE_SHORT, tick, out)
        for arr in full:
            if arr.size:  # 乗れなかった体は**待ち続ける**(意図を落とさない)
                _fail(agents, arr, ResultCode.TRAIN_FULL, tick, out)
        _board_riders(agents, world, [(t, a) for t, a in boarded if a.size], tick, out)

    # ---- 打ち切り(列車が来ない時間帯・深夜の 0 本に対応) ----
    bl = r.board_line[held] >= 0  # 乗れた体はここで落ちている
    bs = r.board_since[held].astype(np.int64)
    stale = held[bl & (bs >= 0) & (int(tick) - bs >= BOARD_WAIT_LIMIT_TICKS)]
    if stale.size:
        r.board_line[stale] = -1
        r.board_since[stale] = -1
        r.activity[stale] = np.where(
            r.activity[stale] == int(Activity.WAITING), int(Activity.IDLE), r.activity[stale]
        ).astype(r.activity.dtype)
        out.n_board_timeout += int(stale.size)
        rail.n_board_timeout += int(stale.size)
        _fail(agents, stale, ResultCode.NO_TRAIN, tick, out)
    # ---- 宙に浮いた意図の掃除 ----
    # 不変条件: 意図を持つ体は「ホームへ歩いている(MOVING)」か「ホームで待っている
    # (board_since≥0)」のどちらか。会話に引き込まれる等**自分の行動以外**で歩みが
    # 止まった体はここで意図を落とす(待ち行列に幽霊を残さない)。失敗は返さない
    # (本人は何も試みていない)。
    inert = held[bl & (bs < 0) & (r.activity[held] != int(Activity.MOVING))]
    if inert.size:
        r.board_line[inert] = -1
        r.board_since[inert] = -1
        rail.n_board_dropped += int(inert.size)


def _plan_exit_mask(r, ids: np.ndarray) -> np.ndarray:
    """9b(第302 Q119 (b)): 計画の退出で歩いて乗る体(``plan_flags`` の ``EXIT_WALK_FLAG``)。欄が無ければ全部 False。"""
    if "plan_flags" not in r.arrays or ids.size == 0:
        return np.zeros(ids.size, dtype=bool)
    return (r.plan_flags[ids].astype(np.int64) & EXIT_WALK_FLAG) != 0


def _board_riders(agents, world, boarded, tick: int, out: ResolveOutcome) -> None:
    """乗車の確定(運賃の金の脚 → 状態遷移 → 列車 SoA)。``boarded`` = ``[(便, 個体列), …]``。

    9b(第302 Q119 (b)): **計画の退出で歩いて乗る体は運賃を払わない**(即時の退出・到着と同じ=計画由来の
    移動は所持金を動かさない)。LLM の乗車は従来どおり払う。成立は ``boarded_plan_exit`` に分けて数える。
    """
    if not boarded:
        return
    r = agents.registry
    fare = int(out.rail.fare_yen)
    riders = np.concatenate([a for _, a in boarded]).astype(np.int64)
    train_of = np.concatenate([np.full(a.size, t, dtype=np.int64) for t, a in boarded])
    plan = _plan_exit_mask(r, riders)
    payers, pay_train = riders[~plan], train_of[~plan]
    free, free_train = riders[plan], train_of[plan]
    led = out.ledger
    if payers.size and led is not None and led.money is not None:
        # 運賃 = 世帯 → 外界(持ち出し=sink)。鉄道事業者は第1陣の6部門に無い(§2.1)ので
        # 許された部門対(H,W)/科目「持ち出し」に載せる=**科目の意味の拡張は台帳側の宣言事項**。
        status = np.asarray(out.rail.pay_fares(led.money, payers, fare, int(tick)))
        ok = status == 0
        if not ok.all():
            _fail(agents, payers[~ok], ResultCode.FARE_SHORT, tick, out)
            out.n_ledger_rejected += int((~ok).sum())
            payers, pay_train = payers[ok], pay_train[ok]
    elif payers.size:
        r.money[payers] = (r.money[payers].astype(np.int64) - fare).astype(np.int32)
    out.fare_paid += int(fare) * int(payers.size)
    if free.size:
        riders = np.concatenate([payers, free]) if payers.size else free
        train_of = np.concatenate([pay_train, free_train]) if payers.size else free_train
    else:
        riders, train_of = payers, pay_train
    if riders.size == 0:
        return
    r.activity[riders] = int(Activity.RIDING)
    r.transit_state[riders] = 1
    r.transit_ref[riders] = train_of.astype(np.int32)
    r.node[riders] = -1  # ホームを離れて車内へ(セルは apply の末尾で -1 になる)
    r.target_node[riders] = -1
    r.poi_ref[riders] = -1
    r.queue_poi[riders] = -1
    r.board_line[riders] = -1  # 意図は成立して消える
    r.board_since[riders] = -1
    out.n_boarded += int(riders.size)
    out.rail.n_boarded_from_queue += int(riders.size - free.size)
    if free.size:
        out.rail.n_boarded_plan_exit = int(getattr(out.rail, "n_boarded_plan_exit", 0)) + int(free.size)
    out.rail.on_board(train_of)
    _ok(agents, riders, tick, out)


def _apply_alight(agents, world, aid, tgt, tick, out, schedule) -> None:
    """降車(行動契約書 §2.1): 前提=「乗車中・当該駅に停車」・失敗=「その駅には止まらない」。"""
    r = agents.registry
    if aid.size == 0:
        return
    if out.rail is None:
        _fail(agents, aid, ResultCode.NO_STOP, tick, out)
        return
    riding = r.transit_state[aid] == 1
    train = r.transit_ref[aid].astype(np.int64)
    stops = np.zeros(aid.size, dtype=bool)
    if riding.any():
        stops[riding] = np.asarray(
            out.rail.is_at_platform(train[riding], int(tick)), dtype=bool
        )
    _fail(agents, aid[~stops], ResultCode.NO_STOP, tick, out)
    win = aid[stops]
    if win.size == 0:
        return
    cell = np.asarray(out.rail.platform_cell, dtype=np.int64)[train[stops]]
    r.activity[win] = int(Activity.IDLE)
    r.transit_state[win] = 0
    out.rail.on_alight(train[stops])
    r.transit_ref[win] = -1
    r.node[win] = world.assets.cell_rep_node[cell].astype(r.node.dtype)
    r.target_node[win] = -1
    out.n_alighted += int(win.size)
    _ok(agents, win, tick, out)


def place_at_external(agents: AgentState, agent_ids, external_ref) -> None:
    """域外ノードに個体を置く(U10 §1.1「域外は方面別の外界ノード」・ランの最初)。

    位置は持たない(``cell=node=-1``)。``transit_state=2`` が「域外滞在」の唯一の印。
    """
    a = np.asarray(agent_ids, dtype=np.int64).ravel()
    if a.size == 0:
        return
    ref = np.asarray(external_ref, dtype=np.int64).ravel()
    with agents.writable():
        r = agents.registry
        r.transit_state[a] = 2
        r.transit_ref[a] = ref.astype(np.int32)
        r.cell[a] = -1
        r.node[a] = -1
        r.target_node[a] = -1
        r.activity[a] = int(Activity.WAITING)
        r.board_line[a] = -1  # 域外へ出る体は乗車の意図を持たない(D-51)
        r.board_since[a] = -1


def rail_arrive(agents: AgentState, world: World, agent_ids, cells) -> None:
    """列車の到着で域外ノードの個体をホームのセルへ降ろす(域外→bbox)。"""
    a = np.asarray(agent_ids, dtype=np.int64).ravel()
    if a.size == 0:
        return
    c = np.asarray(cells, dtype=np.int64).ravel()
    with agents.writable():
        r = agents.registry
        r.transit_state[a] = 0
        r.transit_ref[a] = -1
        r.node[a] = world.assets.cell_rep_node[c].astype(r.node.dtype)
        r.cell[a] = c.astype(r.cell.dtype)
        r.band[a] = world.assets.cell_band[c].astype(r.band.dtype)
        r.xy[a] = world.assets.node_xy[r.node[a]]
        r.activity[a] = int(Activity.IDLE)
        r.target_node[a] = -1


def rail_depart(agents: AgentState, agent_ids, external_ref) -> None:
    """列車の発車で乗客を域外ノードへ運び出す(bbox→域外)。"""
    a = np.asarray(agent_ids, dtype=np.int64).ravel()
    if a.size == 0:
        return
    ref = np.asarray(external_ref, dtype=np.int64).ravel()
    with agents.writable():
        r = agents.registry
        r.transit_state[a] = 2
        r.transit_ref[a] = ref.astype(np.int32)
        r.cell[a] = -1
        r.node[a] = -1
        r.target_node[a] = -1
        r.activity[a] = int(Activity.WAITING)


def sync_transit_activity(agents: AgentState) -> None:
    """``transit_state`` を正として ``activity`` を整える(乗車中=``RIDING``)。

    「待機」「休憩」「退去」は**失敗しない行動**(契約書 §2.1)なので車内でも通り、
    ``activity`` を上書きしてしまう。乗客の同定は ``transit_state`` が持つので世界は壊れないが、
    観測に出る ``activity`` が実態とずれるため毎 tick 貼り直す(ベクトル1本)。
    """
    with agents.writable():
        r = agents.registry
        riding = r.transit_state == 1
        if riding.any():
            r.activity[riding] = int(Activity.RIDING)
