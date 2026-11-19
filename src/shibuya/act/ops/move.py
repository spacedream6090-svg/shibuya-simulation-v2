"""act.ops.move — 割る段で ``engine/resolve.py`` を割った割り先(全ファイルの表 §4・名の表は
``tools/pkgmove/map.toml`` の割る行)。

中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の
方針は、主な割り先 ``act/apply.py`` に残した元の docstring を読むこと。
"""

from __future__ import annotations

from typing import Any, Final
import numpy as np
from shibuya.foundation.vocab.agent_codes import FOCUS_NONE, Activity, ResultCode
from shibuya.world.model.agent_table import (
    AgentState,
)
from shibuya.foundation.vocab.act_codes import WANDER_BAD_TARGET
from shibuya.world.model.state import World
from shibuya.act.gate import ResolveOutcome, _fail, _ok
from shibuya.act.ops.focus import _clear_focus, _focus_xy, _set_focus
from shibuya.act.ops.rail import _enter_board_queue

__all__ = [
    "APPROACH_DONE_M",
]


# ---------------------------------------------------------------- C9b 対象と注意(G3/G4/G7)
#
# 正典: ``docs/design/v2-c9-geometry-agenda.md`` §1 **G3**(近づく=移動の対象が人/物)・
# **G4**(見る=待機の対象=注意の焦点)・**G7**(会話距離)+ §4 改訂(UE AI Perception の
# Sight/Lose Sight と Max Age を**構造として**借りる=``docs/research/lit/
# gameeng__unreal_ai-perception.md``「★借りる」1・2)。
#
# **値はすべて expedient**(UE のページに既定値は載っていない=lit メモ「数値を使うなら別の
# 出所が要る」)。唯一 ``TALK_OPEN_METERS`` だけは 2 m に外部の裏づけがある
# (Sorokowska 2017 見知らぬ人 1.35 m・**日本は含まれない**=親未確認・§4 改訂)。

#: 「近づく」が到達したとみなす距離[m](**expedient**)。
APPROACH_DONE_M: Final[float] = 2.0


# ---------------------------------------------------------------- 第 5 期 空間の段 1(nav1)
def _is_nav(geometry: Any) -> bool:
    """位置幾何がナビメッシュの移動(``engine.space.nav1.NavSpace``)か。"""
    return bool(getattr(geometry, "is_nav", False))


def _nav_stop(agents: AgentState, nav: Any, act: np.ndarray) -> None:
    """新しい行動を選んだ体のうち経路の途中の体: その場に止まり(位置は変えない)、経路を捨て、node を面の上の点に最も
    近い W1 の節にする(行為の適用関数が node を見るため・つなぎ=``engine.space.nav1.NAV1_EXPEDIENTS`` の 4)。"""
    r = agents.registry
    act = np.asarray(act, dtype=np.int64)
    if act.size == 0:
        return
    sel = act[r.nav_tgt[act] >= 0]
    if sel.size == 0:
        return
    nav.drop(sel)
    r.nav_tgt[sel] = -1
    r.nav_t[sel] = 0.0
    r.nav_wait[sel] = -1
    # 域外・車内の体(node < 0)は面の上に居ない=node を書き換えない(位置の確定が経路と階を片づける)
    on = sel[(r.nav_fi[sel] >= 0) & (r.node[sel] >= 0)]
    if on.size:
        # スロープの中(線の上=面の外)で止まった体は同じ階の面の最も近い点へ(〔段 1 の検収 L3〕面の外に居ない)
        sx, sy = nav.onto_surface(r.xy[on, 0], r.xy[on, 1], r.nav_fi[on])
        r.xy[on, 0] = sx.astype(np.float32)
        r.xy[on, 1] = sy.astype(np.float32)
        nd = nav.nearest_nodes(r.xy[on, 0], r.xy[on, 1], r.nav_fi[on])
        r.node[on] = nd.astype(np.int32)
        r.nav_node[on] = nd.astype(np.int32)
    nav.nav_meter.stops_mid_route += int(sel.size)


def _nav_step(agents: AgentState, world: World, aid: np.ndarray, tgt: np.ndarray, tick: int,
              out: ResolveOutcome, nav: Any) -> tuple[np.ndarray, np.ndarray]:
    """エンジン継続(nav1): 経路を(要れば)引き、1 刻みぶん面の上を進む。返り値 ``(arrived, stuck)``。

    逐次ループ宣言(P4): 経路の要る体の数ぶん(``NavSpace.ensure_routes``)と、移動中の体の numba のループ。
    """
    r = agents.registry
    aid = np.asarray(aid, dtype=np.int64)
    tgt = np.asarray(tgt, dtype=np.int64)
    arrived = np.zeros(aid.size, dtype=bool)
    stuck = np.zeros(aid.size, dtype=bool)
    if aid.size == 0:
        return arrived, stuck
    changed, nox, noy, nof, ok = nav.ensure_routes(
        aid, r.xy[aid, 0], r.xy[aid, 1], r.nav_fi[aid], tgt, r.nav_tgt[aid], r.nav_ox[aid], r.nav_oy[aid],
        r.nav_of[aid])
    r.nav_ox[aid] = nox
    r.nav_oy[aid] = noy
    r.nav_of[aid] = nof
    r.nav_t[aid] = np.where(changed, 0.0, r.nav_t[aid]).astype(np.float32)
    r.nav_wait[aid] = np.where(changed, -1, r.nav_wait[aid]).astype(np.int32)
    r.nav_tgt[aid] = np.where(ok, tgt, -1).astype(np.int32)
    stuck[~ok] = True
    okq = np.flatnonzero(ok)
    go = aid[okq]
    if go.size:
        # 〔段 1 の検収 M4 (a)〕混み具合=面の上に居て建物の中でない体の数(刻みの頭の状態から=再開でも同じ)
        fac = nav.kladek_factor(r.cell[go], nav.surface_counts(r))
        n_jam = int(np.count_nonzero(fac <= 0.0))
        out.n_jammed += n_jam
        nav.nav_meter.jammed_agent_steps += n_jam
        res = nav.advance(go, r.nav_t[go], fac, r.nav_wait[go], int(tick))
        r.nav_t[go] = res["t"].astype(np.float32)
        r.nav_wait[go] = res["wait"].astype(np.int32)
        r.xy[go, 0] = res["x"].astype(np.float32)
        r.xy[go, 1] = res["y"].astype(np.float32)
        r.nav_fi[go] = res["fi"].astype(np.int8)
        passed = res["node"] >= 0
        if passed.any():
            r.node[go[passed]] = res["node"][passed].astype(np.int32)
            r.nav_node[go[passed]] = res["node"][passed].astype(np.int32)
        arr = np.asarray(res["arrived"], dtype=bool)
        arrived[okq[arr]] = True
        done = go[arr]
        if done.size:
            r.node[done] = tgt[okq[arr]].astype(np.int32)
            r.nav_node[done] = r.node[done]
            nav.trip_done(done)
            r.nav_tgt[done] = -1
            r.nav_t[done] = 0.0
            r.nav_wait[done] = -1
    if stuck.any():
        bad = aid[stuck]
        nav.drop(bad)
        r.nav_wait[bad] = -1
    return arrived, stuck


def _nav_positions(agents: AgentState, world: World, nav: Any) -> None:
    """位置の確定(nav1): 経路の外れた体の掃除・移動の外で node が変わった体を節の点へ・(xy, 階) → セル・層。"""
    r = agents.registry
    stale = np.flatnonzero((r.nav_tgt >= 0) & ((r.activity != int(Activity.MOVING)) | (r.target_node < 0)
                                                | (r.node < 0)))
    if stale.size:
        nav.drop(stale)
        r.nav_tgt[stale] = -1
        r.nav_t[stale] = 0.0
        r.nav_wait[stale] = -1
        st_on = stale[r.nav_fi[stale] >= 0]
        if st_on.size:  # スロープの中で経路の外れた体も面の上の点へ(〔段 1 の検収 L3〕)
            sx, sy = nav.onto_surface(r.xy[st_on, 0], r.xy[st_on, 1], r.nav_fi[st_on])
            r.xy[st_on, 0] = sx.astype(np.float32)
            r.xy[st_on, 1] = sy.astype(np.float32)
    ext = np.flatnonzero((r.node != r.nav_node) & (r.nav_tgt < 0))
    if ext.size:
        nd = r.node[ext].astype(np.int64)
        on = ext[nd >= 0]
        if on.size:
            x, y, f = nav.anchor_of(r.node[on])
            r.xy[on, 0] = x.astype(np.float32)
            r.xy[on, 1] = y.astype(np.float32)
            r.nav_fi[on] = f
            nav.nav_meter.placed_at_anchor += int(on.size)
        off = ext[nd < 0]
        if off.size:
            r.nav_fi[off] = -1
        r.nav_node[ext] = r.node[ext]
    cell, band = nav.cells(r.xy[:, 0], r.xy[:, 1], r.nav_fi)
    cell = np.where(r.node >= 0, cell, -1).astype(np.int32)
    r.cell[:] = cell
    r.band[:] = np.where(cell >= 0, band, 0).astype(np.int8)


def nav_place(agents: AgentState, world: World, nav: Any) -> None:
    """ランの頭(nav1): 体を節の点へ置き、セルと層を面から導く(初期化と域外の配置の後に 1 回・再開では呼ばない)。"""
    with agents.writable(), world.writable():
        _nav_positions(agents, world, nav)
        world.cells.density[:] = world.compute_density(agents.registry.cell)
        world.cells.density_stage[:] = nav.density_stage(nav.surface_counts(agents.registry))


def _apply_engine_step(agents, world, aid, tgt, tick, out, schedule) -> None:
    """エンジン継続: next-hop に沿って 1 ノード進む(edge 幾何では**辺上を距離で**進む)。

    逐次ループ宣言(P4): node 幾何=なし。edge 幾何=ホップ数ぶん(≤32・
    ``engine.geometry.EdgeGeometry.advance``)。**走査するのは移動中の体だけ**
    (``engine.commit.engine_continuations`` が ``activity==MOVING and target_node>=0``
    で選んだ集合がそのまま ``aid``)。
    """
    r = agents.registry
    geom = out.geometry
    if geom is None:
        new_node, arrived = world.graph.step_once(r.node[aid], tgt)
        stuck = (new_node.astype(np.int64) == r.node[aid].astype(np.int64)) & (~arrived)
        r.node[aid] = new_node
    elif _is_nav(geom):
        arrived, stuck = _nav_step(agents, world, aid, tgt, tick, out, geom)
    else:
        budget = geom.tick_budget_m(aid, r.cell[aid], world.cells.density)
        out.n_jammed += int(np.count_nonzero(budget <= 0.0))
        nd, nx, s, eid, arrived, stuck, n_hops = geom.advance(
            node=r.node[aid],
            next_node=r.path_next_node[aid],
            edge_s=r.edge_s[aid],
            edge_id=r.edge_id[aid],
            target=tgt,
            budget_m=budget,
            route=world.graph.route_next_node,
        )
        r.node[aid] = nd.astype(np.int32)
        r.path_next_node[aid] = nx.astype(np.int32)
        r.edge_s[aid] = s
        r.edge_id[aid] = eid.astype(np.int32)
        out.n_hops += int(n_hops)
    out.n_moved += int(aid.size)
    if arrived.any():
        done = aid[arrived]
        r.activity[done] = int(Activity.IDLE)
        r.target_node[done] = -1
        out.n_arrived += int(done.size)
        if out.track_events:  # 6a: 着いた体(記憶の「移動の到着」)。控えるだけ
            out.arrived_agents.append(np.asarray(done, dtype=np.int64).copy())
        # D-51: ホームへ向かっていた体は着いた時点で**待ち行列へ**(判断は 1 回・実行は世界)
        want = done[r.board_line[done] >= 0]
        if want.size:
            _enter_board_queue(agents, world, want, tick, out)
        # D-62: 就寝地へ向かっていた体は着いた時点で**寝る**(同じ形。意図は排他=
        # ``begin_planned_sleep`` が ``board_line`` を落とし、乗車を選べば ``sleep_pending``
        # が落ちるので、同じ体が両方を持つことはない)。
        nap = done[r.sleep_pending[done] != 0]
        if nap.size:
            r.activity[nap] = int(Activity.SLEEPING)
            r.target_node[nap] = -1
            r.sleep_pending[nap] = 0
            out.n_planned_sleep += int(nap.size)
        # C9b G3/G11: 「近づく」で歩いていた体が着いた。対象がまだ ``APPROACH_DONE_M`` に
        # 居れば到達・居なければ ``TARGET_GONE``(=**最後に見た位置まで来たが居なかった**)。
        _settle_approach(agents, world, done, tick, out)
    if stuck.any():
        _fail(agents, aid[stuck], ResultCode.UNREACHABLE, tick, out)
        r.activity[aid[stuck]] = int(Activity.IDLE)
        r.target_node[aid[stuck]] = -1
        # 行き止まりでホームへ着けない体は乗車の意図も落とす(幽霊を残さない)
        r.board_line[aid[stuck]] = -1
        r.board_since[aid[stuck]] = -1
        r.sleep_pending[aid[stuck]] = 0  # D-62: 就寝地へ着けない体も同じ(起きたまま)


def _settle_approach(agents, world, done, tick, out) -> None:
    """「近づく」で歩いた体の**到着の判定**(C9b G3/G11)。

    着いた先は「対象を最後に見た位置に最も近いノード」。そこで対象までの距離を測り、
    ``APPROACH_DONE_M`` 以内なら到達(焦点は残す)、外なら ``TARGET_GONE``+焦点を落とす。
    UE AI Perception の ``Auto Success Range from Last Seen Location`` 型の猶予を
    「最後に見た位置まで歩く」という形で入れている(§4 改訂 G11)。

    焦点の欄が無いラン(``attention_columns=False``)では**何もしない**。

    逐次ループ宣言(P4): なし。
    """
    if not getattr(agents, "attention_columns", False) or done.size == 0:
        return
    r = agents.registry
    code = r.focus_target[done].astype(np.int64)
    sel = done[code != FOCUS_NONE]
    if sel.size == 0:
        return
    code = r.focus_target[sel].astype(np.int64)
    xy, present = _focus_xy(agents, world, code)
    node = np.asarray(r.node, dtype=np.int64)[sel]
    here = np.asarray(world.assets.node_xy, dtype=np.float64)[np.maximum(node, 0)]
    d = np.sqrt(((here - xy) ** 2).sum(axis=1))
    near = present & (d <= APPROACH_DONE_M) & (node >= 0)
    out.n_approach_done += int(np.count_nonzero(near))
    gone = sel[~near]
    if gone.size:
        r.focus_target[gone] = np.int32(FOCUS_NONE)
        r.focus_ttl[gone] = np.uint8(0)
        out.n_target_gone += int(gone.size)
        _fail(agents, gone, ResultCode.TARGET_GONE, tick, out)


def _apply_move(agents, world, aid, tgt, tick, out, schedule) -> None:
    """移動(行動契約書 §2.1): 経路が存在 → 位置は経路上へ。到達不能は失敗。

    **C9b G3「近づく」**: ``out.focus_request`` に対象(人/目印 POI)が入っている体は、
    行き先ノードを**セル代表ノードではなく対象に最も近いノード**にする(動詞は足さない=
    「移動の対象が人/オブジェクト」)。対象のノードが取れなければ ``UNREACHABLE``。
    """
    r = agents.registry
    # 二層の段 2: 「対象: あたり」を解決できなかった体(域外)は**対象不正**。
    # v1/v2 では行き先に ``WANDER_BAD_TARGET`` が立たない=この分岐は 1 行も通らない。
    bad = tgt == WANDER_BAD_TARGET
    if bool(np.any(bad)):
        _fail(agents, aid[bad], ResultCode.BAD_TARGET, tick, out)
        out.n_move_bad_target += int(np.count_nonzero(bad))
        aid, tgt = aid[~bad], tgt[~bad]
        if aid.size == 0:
            return
    ok_cell = (tgt >= 0) & (tgt < world.n_cells)
    safe = np.clip(tgt, 0, world.n_cells - 1)
    dest_node = np.where(ok_cell, world.assets.cell_rep_node[safe], -1)
    if out.focus_request is not None:
        dest_node = _approach_dest_node(agents, world, aid, dest_node, out)
        ok_cell = ok_cell & (dest_node >= 0)
    nxt = world.graph.route_next_node(r.node[aid], dest_node)
    same = dest_node == r.node[aid].astype(np.int64)
    good = ok_cell & ((nxt >= 0) | same)
    if good.any():
        g = aid[good]
        # 既に行き先ノードに居るなら移動せず idle(到着済み)
        r.activity[g] = np.where(
            same[good], int(Activity.IDLE), int(Activity.MOVING)
        ).astype(np.int8)
        r.target_node[g] = np.where(same[good], -1, dest_node[good]).astype(np.int32)
        if out.seat_release_walk:
            # 〔第 2 期 2-4 V3〕歩き出した体(行き先のノードへ向かう=MOVING)の在席の印を解く=店の席が空く
            # (2-2 の探り=在席 × 刻みの 4.3% が店のセルの外)。到着済み(same)の体は動かないので解かない。
            walker = g[~same[good]]
            seated = walker[r.poi_ref[walker] >= 0]
            if seated.size:
                r.poi_ref[seated] = -1
                r.poi_since[seated] = -1
                out.n_seat_released_walk += int(seated.size)
        if out.defect_fixes:
            # 〔11-03 M11〕満席の列に並んでいた体が歩き出した(新しい行為が通った)=列を離れる。失敗は書かない
            # (``INTERRUPTED`` ではない)。旧道では列に残り、席が空けば離れた所で購入・食事が成立していた。
            left = g[~same[good]]
            left = left[r.queue_poi[left] >= 0]
            if left.size:
                r.queue_poi[left] = -1
                r.queue_since[left] = -1
                out.n_queue_left_by_move += int(left.size)
        # 「近づく」の対象を**焦点として保持**する(着いたときに居るかを見る=``TARGET_GONE``)。
        # 距離は問わない(遠くの目印に近づくのは正当)=``require_near=False``。
        _set_focus(agents, world, g, tick, out, require_near=False)
        _ok(agents, g, tick, out)
    _clear_focus(agents, aid[~good])  # 行けなかった体に焦点だけ残さない
    _fail(agents, aid[~good], ResultCode.UNREACHABLE, tick, out)
    out.n_move_unreachable += int(np.count_nonzero(~good))


def _approach_dest_node(agents, world, aid, dest_node, out) -> np.ndarray:
    """「近づく」の行き先ノード(**対象に最も近いノード**)へ差し替える(C9b G3)。

    - 対象が**人**: 辺上に居るなら近い方の端点(``EdgeGeometry.snap_to_nearest_node``
      の第1返値=C9a の表引きをそのまま使う)。node 幾何なら ``node`` そのもの。
    - 対象が**目印 POI**: W6 の ``poi_node``(セル内で POI に最も近いノード・資産の前計算)。
    - 対象が取れない: ``-1`` を返す=呼び出し側が ``UNREACHABLE``。

    ``out.focus_request`` が ``None``(既定)なら**引数をそのまま返す**。

    逐次ループ宣言(P4): なし(配列演算のみ)。
    """
    req = out.focus_request
    if req is None:
        return dest_node
    f = req[aid]
    is_p = f >= 0
    is_q = f <= -2
    if not bool(np.any(is_p | is_q)):
        return dest_node
    r = agents.registry
    geom = out.geometry
    person = np.clip(f, 0, max(0, int(agents.n) - 1))
    if geom is None or _is_nav(geom):
        pn = r.node[person].astype(np.int64)
    else:
        pn, _nx, _s, _e = geom.snap_to_nearest_node(
            r.node[person], r.path_next_node[person], r.edge_s[person], r.edge_id[person]
        )
        pn = np.asarray(pn, dtype=np.int64)
    poi = np.clip(-2 - f, 0, max(0, int(world.n_poi) - 1))
    qn = np.asarray(world.assets.poi_node, dtype=np.int64)[poi]
    out.n_approach += int(np.count_nonzero(is_p | is_q))
    return np.where(is_p, pn, np.where(is_q, qn, dest_node))
