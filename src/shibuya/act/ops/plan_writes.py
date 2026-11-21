"""act.ops.plan_writes — 割る段で ``engine/resolve.py`` を割った割り先(全ファイルの表 §4・名の表は
``tools/pkgmove/map.toml`` の割る行)。

中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の
方針は、主な割り先 ``act/apply.py`` に残した元の docstring を読むこと。
"""

from __future__ import annotations

from typing import Any
import numpy as np
from shibuya.foundation.vocab.agent_codes import Activity
from shibuya.world.model.agent_table import (
    AgentState,
)
from shibuya.world.model.state import World
from shibuya.act.ops.rail import _cell_of_node, _platform_table

__all__ = [
    "set_plan_state", "begin_planned_sleep", "wake_from_plan", "begin_exit_walk", "begin_walk_to",
    "clear_board_intent",
]


def set_plan_state(
    agents: AgentState,
    agent_id=None,
    *,
    flags=None,
    flags_set: int | None = None,
    flags_clear: int | None = None,
) -> None:
    """``plan_flags``(D-66 計画実行層の欄)への**唯一の書き込み口**(〔第330・RET〕K15 で ``plan_activity`` を消した)。

    欄は ``AgentState(plan_columns=True)`` のランにしか無い(帰無腕は欄ごと無い)ので、
    **欄が無ければ黙って何もしない**=帰無腕・既存テストは 1 バイトも動かない。

    Args:
        agents: 個体状態。
        agent_id: 書く体(``None``=全体に一括代入)。
        flags: ``plan_flags`` をそのまま置き換える値。
        flags_set / flags_clear: 立てる/落とすビット(``FLAG_*``)。

    Note:
        書くのは「計画の写し」であって世界状態ではないが、SoA への書き込みは
        ``resolve`` 以外から行わない規律(運用設計書 §2.2)に合わせてここに置く。
    """
    r = agents.registry
    if "plan_flags" not in r.arrays:
        return
    a = None if agent_id is None else np.asarray(agent_id, dtype=np.int64).ravel()
    if a is not None and a.size == 0:
        return
    with agents.writable():
        if flags is not None:
            v = np.asarray(flags, dtype=np.int8)
            if a is None:
                r.plan_flags[:] = v
            else:
                r.plan_flags[a] = v
        if flags_set:
            if a is None:
                r.plan_flags[:] = (r.plan_flags | np.int8(flags_set)).astype(np.int8)
            else:
                r.plan_flags[a] = (r.plan_flags[a] | np.int8(flags_set)).astype(np.int8)
        if flags_clear:
            mask = ~np.int8(int(flags_clear))  # int8 の補数=落とすビットだけ 0
            if a is None:
                r.plan_flags[:] = (r.plan_flags & mask).astype(np.int8)
            else:
                r.plan_flags[a] = (r.plan_flags[a] & mask).astype(np.int8)


def begin_planned_sleep(
    agents: AgentState,
    world: World,
    agent_id,
    target_cell,
    tick: int,
    *,
    schedule=None,
) -> tuple[int, int, int]:
    """**就寝境界に達した体を寝かせる**(D-62 (a)「就寝は計画の実行」・2026-09-10 決定)。

    正典・位置づけ
    - 週次表(W17)の就寝境界は、その個体自身が LLM で作った計画の一部。**判断は済んで
      いる**ので、境界での実行にもう一度 LLM を呼ばない(D-51 乗車の意図保持と同じ
      「判断1回・実行は世界」)。呼び出し側(``engine.run``)は、この境界の体を
      起床候補から**外す**。
    - 就寝地=その活動の ``target_cell``(未解決 ``-1`` なら ``schedule.home_cell``)。

    規則(3 通り)
    1. 就寝地のセルに**居る** → ``activity=SLEEPING``(``target_node``/乗車の意図を落とす)。
    2. 居ない・経路がある → 就寝地へ ``target_node`` を張って歩き出し ``sleep_pending=1``。
       着いた時点で ``_apply_engine_step`` が寝かせる。
    3. 居ない・経路がない / 乗車中・域外滞在 / 会話中 → **何もしない**(起きたまま)。

    expedient(登録簿 §8 D-62)
    - 3 の「乗車中・域外滞在」を触らないのは ``transit_state`` が乗客の保存則の分母だから
      (車内で寝る状態を作らない=第2陣)。「会話中」を触らないのは、片側だけ
      ``CONVERSING`` が残る事故を作らないため(D-56 の例外③と同じ理由)。
    - 2 で歩いている間は**起きている**(``MOVING``)。現実の「帰って寝る」は移動が先なので
      境界の時刻ちょうどに寝ないのは正しいが、経路が長いと就寝が遅れる。

    Returns:
        計数の辞書 ``{slept, walking, riding, outside, conversing, asleep, unreachable}``
        (``slept + walking + それ以外の合計 = 体数``)。**触らなかった理由を数える**のは、
        「その日はもう就寝境界が来ない=起きたままになる」体の量を報告するため。
        内訳は ``transit_state`` を先に見る(乗車中 → 域外 → 在圏の中で 会話中/就寝済/
        セルが無い・経路が無い)ので、**域外の体は ``unreachable`` ではなく ``outside``**
        に入る(2026-09-11・D-66)。
    """
    zero = {
        "slept": 0, "walking": 0, "riding": 0, "outside": 0,
        "conversing": 0, "asleep": 0, "unreachable": 0,
    }
    a = np.asarray(agent_id, dtype=np.int64).ravel()
    if a.size == 0:
        return zero
    r = agents.registry
    cell = np.asarray(target_cell, dtype=np.int64).ravel()
    if cell.size != a.size:
        raise ValueError(f"就寝地の長さが体数と違う({cell.size} != {a.size})")
    if schedule is not None:
        home = np.asarray(schedule.home_cell, dtype=np.int64)[a]
        cell = np.where(cell >= 0, cell, home)
    n_at = n_walk = 0
    with agents.writable():
        ok_cell = (cell >= 0) & (cell < world.n_cells)
        st = r.transit_state[a]
        act0 = r.activity[a]
        free = (
            ok_cell
            & (st == 0)
            & (act0 != int(Activity.CONVERSING))
            & (act0 != int(Activity.SLEEPING))
        )
        # **触らなかった理由は 3 値(``transit_state``)を先に見る**(2026-09-11・D-66 の指摘):
        # 旧実装は ``ok_cell`` を全ての内訳に掛けていたので、就寝地セルの無い**域外の体**が
        # ``outside`` ではなく ``unreachable`` に落ちていた(計画実行層のランで 域外常住者の
        # ``home_cell < 0`` が効き、既定腕の「行けない」が 5,976 件に膨らんだ)。
        # ``unreachable`` は「**在圏**なのに就寝地のセルが無い/経路が無い」体だけにする。
        # 内訳の合計は従来どおり体数に一致し、``free``(実際に寝かせる体)は 1 ビットも変えない。
        in_area = st == 0
        zero["riding"] = int(np.count_nonzero(st == 1))
        zero["outside"] = int(np.count_nonzero(st == 2))
        zero["conversing"] = int(
            np.count_nonzero(in_area & (act0 == int(Activity.CONVERSING)))
        )
        zero["asleep"] = int(np.count_nonzero(in_area & (act0 == int(Activity.SLEEPING))))
        zero["unreachable"] = int(
            np.count_nonzero(
                in_area
                & (act0 != int(Activity.CONVERSING))
                & (act0 != int(Activity.SLEEPING))
                & ~ok_cell
            )
        )
        at = free & (r.cell[a].astype(np.int64) == cell)
        here = a[at]
        if here.size:
            r.activity[here] = int(Activity.SLEEPING)
            r.target_node[here] = -1
            r.sleep_pending[here] = 0
            r.board_line[here] = -1  # 乗車の意図は落ちる(幽霊を残さない)
            r.board_since[here] = -1
            n_at = int(here.size)
        far = np.flatnonzero(free & ~at)
        if far.size:
            ids = a[far]
            dest = np.asarray(world.assets.cell_rep_node, dtype=np.int64)[cell[far]]
            nxt = np.asarray(world.graph.route_next_node(r.node[ids], dest), dtype=np.int64)
            same = dest == r.node[ids].astype(np.int64)
            good = (nxt >= 0) | same
            # ノードは就寝地でもセルが違う(=表現ノードに居る)体は、その場で寝かせる
            arrive = ids[good & same]
            if arrive.size:
                r.activity[arrive] = int(Activity.SLEEPING)
                r.target_node[arrive] = -1
                r.sleep_pending[arrive] = 0
                r.board_line[arrive] = -1
                r.board_since[arrive] = -1
                n_at += int(arrive.size)
            walk = ids[good & ~same]
            if walk.size:
                r.activity[walk] = int(Activity.MOVING)
                r.target_node[walk] = dest[good & ~same].astype(r.target_node.dtype)
                r.sleep_pending[walk] = 1
                r.board_line[walk] = -1
                r.board_since[walk] = -1
                n_walk = int(walk.size)
            # 経路が無くて就寝地へ行けない体(行き止まり)も「触らなかった」側に数える
            zero["unreachable"] += int(np.count_nonzero(~good))
    zero["slept"] = n_at
    zero["walking"] = n_walk
    return zero


def wake_from_plan(agents: AgentState, agent_id) -> int:
    """**非就寝の計画境界に達した体を起こす**(D-62 (a) の対称形)。

    起床は「次の計画境界(``PLAN_WORKING``/``PLAN_GENERAL``/``PLAN_TRANSIT``)か顕著行為」
    (ユーザー決定 (a))。境界で起こしてから LLM に判断させる——**呼が繰り延べ・抑止で
    落ちても起きる**(現実の起床は呼ばれ方に依存しない)。就寝の意図(``sleep_pending``)も
    ここで落ちる。

    Returns:
        ``SLEEPING`` から起こした体数。
    """
    a = np.asarray(agent_id, dtype=np.int64).ravel()
    if a.size == 0:
        return 0
    with agents.writable():
        r = agents.registry
        woke = a[r.activity[a] == int(Activity.SLEEPING)]
        if woke.size:
            r.activity[woke] = int(Activity.IDLE)
        drop = a[r.sleep_pending[a] != 0]
        if drop.size:
            r.sleep_pending[drop] = 0
    return int(woke.size)


def begin_exit_walk(agents: AgentState, world: World, rail: Any, agent_ids, lines, tick: int
                    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """**9a 退出を歩かせる**(D-115 ①): 計画の退出の体に**その体の路線のホーム**への乗車の意図を立てる。

    D-51 の乗車の意図(``board_line``)と同じ形=ホームに居れば乗車待ちへ・居なければそのホームの代表
    ノードへ ``target_node`` を張って歩かせる(着けば ``_apply_engine_step`` が待ち行列へ入れ、
    ``_serve_board_queue`` が受容関数 ``accept_quota`` を通して乗せる)。行き先は**最寄りでなく**
    ``lines``(その体の路線)のホーム。

    Returns:
        入力と同じ並びの 3 つの bool マスク ``(歩き出した, ホームで待ちに入った, 立てられなかった)``
        (立てられない=その線に今日の便が無い・ホームのセルが無い・経路なし)。
    Note:
        逐次ループ宣言(P4): なし(便のある路線の表への ``searchsorted`` と経路の配列問い合わせ)。
    """
    a = np.asarray(agent_ids, dtype=np.int64).ravel()
    ln = np.asarray(lines, dtype=np.int64).ravel()
    none = np.zeros(a.size, dtype=bool)
    if a.size == 0:
        return none, none, none
    if rail is None or not bool(getattr(rail, "active", False)):
        return none, none, ~none
    plines, pcells, pnodes = _platform_table(world, rail)
    if plines.size == 0:
        return none, none, ~none
    pos = np.searchsorted(plines, ln)
    pos_c = np.minimum(pos, plines.size - 1)
    has = (ln >= 0) & (plines[pos_c] == ln)
    with agents.writable():
        r = agents.registry
        node_now = r.node[a].astype(np.int64)
        dest = np.where(has, pnodes[pos_c], -1)
        cell_now = _cell_of_node(world, np.maximum(node_now, 0))
        at_plat = has & (node_now >= 0) & (cell_now == pcells[pos_c])
        need = has & ~at_plat & (node_now >= 0)
        route_ok = np.zeros(a.size, dtype=bool)
        if need.any():
            nxt = np.asarray(world.graph.route_next_node(node_now[need], dest[need]), dtype=np.int64)
            route_ok[np.flatnonzero(need)] = (nxt >= 0) | (dest[need] == node_now[need])
        wait = a[at_plat]
        walk = a[route_ok]
        if wait.size:
            r.board_line[wait] = ln[at_plat].astype(r.board_line.dtype)
            r.board_since[wait] = int(tick)
            r.activity[wait] = int(Activity.WAITING)
            r.target_node[wait] = -1
            if hasattr(rail, "n_board_waiting_plan_exit"):  # 9b: LLM の乗車待ちと分けて数える
                rail.n_board_waiting_plan_exit += int(wait.size)
        if walk.size:
            r.board_line[walk] = ln[route_ok].astype(r.board_line.dtype)
            r.board_since[walk] = -1  # まだホームに立っていない
            same = dest[route_ok] == node_now[route_ok]
            go = walk[~same]
            r.activity[go] = int(Activity.MOVING)
            r.target_node[go] = dest[route_ok][~same].astype(r.target_node.dtype)
            here = walk[same]
            if here.size:  # 代表ノードに居るがセルの判定が外れた体(起きない想定)=その場で待ち
                r.board_since[here] = int(tick)
                r.activity[here] = int(Activity.WAITING)
                r.target_node[here] = -1
    return route_ok, at_plat, ~(at_plat | route_ok)


def begin_walk_to(agents: AgentState, world: World, agent_ids, cells
                  ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """〔第 6 期 6-2 カレンダー 1b〕本人が決めた行き先のセルへ歩き出す(体の基本動作「歩く」=決定 10-12 §1-4 D1)。

    行き先はセルの代表ノード(``cell_rep_node``)。在圏(``transit_state == 0``)で会話中でない体だけ歩かせる
    (``activity=MOVING``・``target_node``=行き先・乗車と就寝の意図は落とす=``begin_planned_sleep`` の歩きの枝と同じ形=
    着いた後の世界の続きは ``_apply_engine_step``)。いつ・どこへは本人の判断(``engine.calendar_self``)が決める。

    Returns:
        入力と同じ並びの 4 つの bool マスク ``(歩き出した, もう着いている, 会話中=始められない, 歩けない)``
        (歩けない=在圏でない・セルが無い・経路が無い)。
    Note:
        逐次ループ宣言(P4): なし(経路の配列問い合わせ 1 回)。
    """
    a = np.asarray(agent_ids, dtype=np.int64).ravel()
    c = np.asarray(cells, dtype=np.int64).ravel()
    none = np.zeros(a.size, dtype=bool)
    if a.size == 0:
        return none, none, none, none
    if c.size != a.size:
        raise ValueError(f"行き先の長さが体数と違う({c.size} != {a.size})")
    with agents.writable():
        r = agents.registry
        inside = np.asarray(r.transit_state)[a] == 0
        act0 = np.asarray(r.activity)[a]
        ok_cell = (c >= 0) & (c < world.n_cells)
        busy = inside & ok_cell & (act0 == int(Activity.CONVERSING))
        free = inside & ok_cell & ~busy
        dest = np.full(a.size, -1, dtype=np.int64)
        dest[ok_cell] = np.asarray(world.assets.cell_rep_node, dtype=np.int64)[c[ok_cell]]
        node = np.asarray(r.node, dtype=np.int64)[a]
        here = free & (node == dest) & (dest >= 0)
        need = free & ~here & (dest >= 0) & (node >= 0)
        good = np.zeros(a.size, dtype=bool)
        if need.any():
            nxt = np.asarray(world.graph.route_next_node(node[need], dest[need]), dtype=np.int64)
            good[np.flatnonzero(need)] = nxt >= 0
        walk = a[good]
        if walk.size:
            r.activity[walk] = int(Activity.MOVING)
            r.target_node[walk] = dest[good].astype(r.target_node.dtype)
            r.board_line[walk] = -1
            r.board_since[walk] = -1
            r.sleep_pending[walk] = 0
    fail = ~(good | here | busy)
    return good, here, busy, fail


def clear_board_intent(agents: AgentState, agent_ids) -> None:
    """乗車の意図(``board_line``/``board_since``)を落とす(9a: 計画の退出を即時に切り替えた体)。"""
    a = np.asarray(agent_ids, dtype=np.int64).ravel()
    if a.size == 0:
        return
    with agents.writable():
        r = agents.registry
        r.board_line[a] = -1
        r.board_since[a] = -1
