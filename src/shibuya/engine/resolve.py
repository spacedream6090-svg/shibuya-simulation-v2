"""engine.resolve — **世界状態への唯一の書き込み口**(二相コミットの Phase C)。

正典
- 運用設計書 §2.2: 「Phase C (commit・単一書き手): **engine.resolve が確定分だけ適用**。
  落選者には失敗の意味論(行動契約書 §2/§6)」「**atomic 演算による直接更新は禁止**」。
- 行動契約書 冒頭: 「世界状態の書き込み口はエンジンの resolve 一本(AI Town 同型)。
  無効行動は本人に『無効』と返す(Concordia 同型)。**効果はエンジンでのみ適用**。」
- 行動契約書 §2.1 の 12 語の前提条件・効果・失敗の意味論(下の ``_apply_*`` が 1 対 1)。
- 行動契約書 §2「共通の必須事項: ①効果は resolve でのみ適用 ②購入・乗車は保存則対象
  ③失敗しない行動が常に1つ以上(待機)」。
- 世界過程設計書 §4 原則2: 「LLM の出力は『意図』まで。結果はエンジンが確定(resolve 分離)」。
- 予算宣言表 **P2**: 「物理フレーム ≤5 ms/フレーム@5千体」。C2 の「フレーム」=
  ``advance_movement``(next-hop 1 歩)+ ``np.bincount`` による密度再計算。

**書き込み禁止の機械強制**
    ``AgentState`` / ``World`` の配列は ``freeze()`` で ``writeable=False`` になる。
    ``with state.writable():`` を書いてよいのは**本ファイルだけ**
    (``tests/engine/test_two_phase.py::test_only_resolve_writes`` が
    ``src/shibuya`` 全体を grep して強制)。

逐次ループ宣言(P4)
- ``apply``: **行動語ぶんのループ**(12 語+エンジン継続=13 分岐)。個体数に比例するループなし。
- ``AgentState.freeze/thaw``: フィールド数ぶん(宣言済み)。

expedient(本モジュール分)
- 移動は **1 tick=1 ノード**(``world.graph`` の宣言と同じ)。実速度・群衆物理は U15(C4 以降)。
- 内受容の自然変動(``advance_body``): 30 tick ごとに空腹+1・疲労+1、休憩で疲労−3、
  購入で空腹−4、就寝中は疲労−2。世界過程(C4)が入るまでの**駆動源**。
  値は自前(契約書に無い)。
- 通報・断るは C2 では状態を変えない(記録のみ=契約書の効果先が未実装)。手伝いは
  「相手が援助要求状態」を持たないので必ず失敗(``BAD_TARGET``)。
- 乗車は**列車が無い**ので必ず ``NO_TRAIN``、降車は契約書どおり ``NO_STOP``(その駅には止まらない)(列車は C4・§2.6 の混雑率受容関数もそこ)。
- 会話は**セッションレコードを作るだけ**(発話ブロック・終了判定・記憶転写は C3/C4)。
- 日次内省(T2)は「就寝で発火」を**記録するだけ**(実際の内省呼は C3)。

**C4 の結線(台帳)**
- ``ledger``(``engine.ledger_api.LedgerBundle``)を注入すると、購入の
  **金は ``MoneyLedger.purchase_many``・物は ``GoodsLedger.sell_many``** を通る
  (境界・経済設計書 §2.3「transfer 単一API・残高の直接代入は静的に禁止」/
  世界過程設計書 §7.1「move_goods 単一API・在庫の直接代入は静的禁止」)。
  注入しなければ C2 と同じ直接更新の経路に落ちる(既存テストの互換)。
- 世帯の現金は ``agents.money`` **そのもの**(台帳は写しを持たない)。したがって台帳への
  書き込みも ``with agents.writable()`` の中でしか成立しない=書き込み口は resolve 1本のまま。
- ``world.pois.stock`` は物の台帳の**写し**。真値は棚(SKU 別)にあり、resolve が書き戻す。
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Final

import numpy as np

from shibuya.agents.state import (
    N_WAKE_CONDITIONS,
    REFRACTORY_MINUTES,
    Activity,
    AgentState,
    ResultCode,
)
from shibuya.engine.change_detect import DetectResult
from shibuya.engine.ledger_api import LedgerBundle
from shibuya.engine.commit import (
    ACT_ALIGHT,
    ACT_BOARD,
    ACT_BUY,
    ACT_HELP,
    ACT_LEAVE,
    ACT_MOVE,
    ACT_REFUSE,
    ACT_REPORT,
    ACT_REST,
    ACT_SLEEP,
    ACT_TALK,
    ACT_WAIT,
    ENGINE_STEP,
    IntentBatch,
)
from shibuya.world.state import World

__all__ = [
    "revert_conversation",
    "BODY_TICK_PERIOD",
    "REST_FATIGUE_RELIEF",
    "BUY_HUNGER_RELIEF",
    "SLEEP_FATIGUE_RELIEF",
    "ResolveOutcome",
    "initialize",
    "apply_detection",
    "apply",
    "set_refractory",
    "advance_body",
    "restock",
    "collect_waste",
    "consume",
]

#: 内受容の自然変動の周期[tick](expedient)。
BODY_TICK_PERIOD: Final[int] = 30
REST_FATIGUE_RELIEF: Final[int] = 3
BUY_HUNGER_RELIEF: Final[int] = 4
SLEEP_FATIGUE_RELIEF: Final[int] = 2

_REFRACTORY_TICKS: Final[np.ndarray] = np.asarray(REFRACTORY_MINUTES, dtype=np.int32)


def _require_thawed(*states: object) -> None:
    """``ufunc.at`` を撃つ前の**穴埋めガード**(層2レビュー指摘・C3 結線で追加)。

    NumPy の ``np.add.at`` / ``np.maximum.at`` は **``flags.writeable=False`` を見ない**
    (`ufunc.at` は buffer protocol を経由せずに書く)。つまり ``freeze()`` だけでは
    「resolve 以外からの一括加算」を止められない。そこで ``AgentState``/``World`` が持つ
    ``_frozen`` フラグ(``frozen`` プロパティ)を**明示的に**検査する。

    Raises:
        ValueError: 凍結中の状態へ ``ufunc.at`` を撃とうとした(=書き込み窓の外)。

    Note:
        静的側の相方は ``tests/engine/test_add_at_guard.py``
        (``world.``/``agents.`` 由来の配列への ``np.<ufunc>.at`` は resolve.py にしか書けない)。
    """
    for s in states:
        if bool(getattr(s, "frozen", False)):
            raise ValueError(
                "凍結中の状態へ ufunc.at(np.add.at 等)を撃とうとした。"
                "書き込みは resolve の writable() 窓の中だけ(運用設計書 §2.2)"
            )


@dataclass
class ResolveOutcome:
    """Phase C の結果(診断行の素材)。"""

    tick: int
    n_confirmed: int = 0
    n_losers: int = 0
    n_moved: int = 0
    n_arrived: int = 0
    n_purchases: int = 0
    revenue_delta: int = 0
    n_conversations: int = 0
    n_reflections: int = 0
    per_action: dict[int, int] = field(default_factory=dict)
    per_result: dict[int, int] = field(default_factory=dict)
    #: 移動+密度更新の壁時計[秒](予算行 P2)。
    movement_seconds: float = 0.0
    #: この tick で使う台帳(``apply`` が入れる**呼びごとの文脈**。行動語の適用関数へ
    #: 引数を1本増やさずに渡すための欄=注入点は ``apply(..., ledger=...)`` の1か所だけ)。
    ledger: LedgerBundle | None = None
    #: 台帳が金の脚を却下した件数(診断行・通常は 0)。
    n_ledger_rejected: int = 0

    def add_result(self, code: int, n: int) -> None:
        if n:
            self.per_result[int(code)] = self.per_result.get(int(code), 0) + int(n)


# ---------------------------------------------------------------- 初期化
def initialize(
    agents: AgentState,
    world: World,
    schedule,
    *,
    day_index: int = 0,
    ledger: LedgerBundle | None = None,
) -> None:
    """個体を自宅セルに置き、所持金・種別・内受容の初期段を設定する(**ランの最初に1回**)。

    ここも書き込みなので resolve に置く(``run.py`` は初期化後に ``freeze()`` する)。

    ``ledger`` を渡した場合、初期財布は**直接代入ではなく外界からの transfer**で入れる
    (境界・経済設計書 §2.3 ex nihilo 禁止)。金額は同じなので状態ハッシュは変わらない。
    """
    from shibuya.engine.change_detect import INTERO_UP_EDGES

    n = agents.n
    with agents.writable(), world.writable():
        home = np.asarray(schedule.home_cell, dtype=np.int64)[:n]
        agents.registry.cell[:] = home
        agents.registry.node[:] = world.assets.cell_rep_node[home]
        agents.registry.band[:] = world.assets.cell_band[home]
        agents.registry.xy[:] = world.assets.node_xy[agents.registry.node]
        agents.registry.field("kind")[:] = np.asarray(schedule.kind)[:n]
        money0 = np.asarray(schedule.initial_money, dtype=np.int64)[:n]
        if ledger is not None and ledger.money is not None:
            # 台帳経路: 外界 → 世帯の transfer(来街者持込)で入れる(残高の直接代入をしない)
            agents.registry.money[:] = 0
            ledger.money.endow_households(money0, 0)
        else:
            agents.registry.money[:] = money0
        agents.registry.activity[:] = int(Activity.SLEEPING)
        agents.registry.hunger[:] = 2
        agents.registry.fatigue[:] = 2
        agents.registry.thermal[:] = 5
        for value_field, stage_field in (
            ("hunger", "hunger_stage"),
            ("fatigue", "fatigue_stage"),
            ("thermal", "thermal_stage"),
        ):
            v = agents.registry.field(value_field)
            stage = np.zeros(n, dtype=np.int8)
            for e in INTERO_UP_EDGES:
                stage += (v >= e).astype(np.int8)
            agents.registry.field(stage_field)[:] = stage
        world.cells.density[:] = world.compute_density(agents.registry.cell)
        world.cells.density_stage[:] = world.density_stage()
        world.cells.open_count[:] = world.open_count_per_cell(0)


# ---------------------------------------------------------------- 変化検出の書き戻し
def apply_detection(agents: AgentState, world: World, result: DetectResult) -> None:
    """``change_detect`` が返した新しい B4 ハッシュと内受容段を書き込む。"""
    with agents.writable(), world.writable():
        if result.changed_cells.size:
            world.cells.b4_hash[result.changed_cells] = result.changed_b4_hash
        for crossing in result.crossings:
            if crossing.agent_id.size:
                agents.registry.field(crossing.stage_field)[crossing.agent_id] = (
                    crossing.new_stage.astype(np.int8)
                )


# ---------------------------------------------------------------- 不応期
def set_refractory(agents: AgentState, agent_id, condition, tick: int) -> None:
    """呼んだ個体×条件の不応期タイマーを張る(知覚契約書 §6 運用規定②)。"""
    a = np.asarray(agent_id, dtype=np.int64)
    if a.size == 0:
        return
    c = np.asarray(condition, dtype=np.int64)
    until = (int(tick) + _REFRACTORY_TICKS[c]).astype(np.int32)
    with agents.writable():
        _require_thawed(agents)
        cur = agents.registry.refractory_until
        np.maximum.at(cur, (a, c), until)


# ---------------------------------------------------------------- 身体の自然変動
def advance_body(agents: AgentState, tick: int) -> None:
    """内受容 3 変数の自然変動(**C4 の世界過程が入るまでの駆動源**・expedient)。"""
    if int(tick) % BODY_TICK_PERIOD:
        return
    with agents.writable():
        r = agents.registry
        r.hunger[:] = np.minimum(r.hunger.astype(np.int16) + 1, 10).astype(np.uint8)
        r.fatigue[:] = np.minimum(r.fatigue.astype(np.int16) + 1, 10).astype(np.uint8)
        sleeping = r.activity == int(Activity.SLEEPING)
        if sleeping.any():
            r.fatigue[sleeping] = np.maximum(
                r.fatigue[sleeping].astype(np.int16) - SLEEP_FATIGUE_RELIEF, 0
            ).astype(np.uint8)


# ---------------------------------------------------------------- Phase C 本体
def apply(
    plan_confirmed: IntentBatch,
    losers: IntentBatch,
    agents: AgentState,
    world: World,
    tick: int,
    *,
    schedule=None,
    ledger: LedgerBundle | None = None,
) -> ResolveOutcome:
    """Phase C: 確定した intent だけを世界へ適用する(**唯一の書き手**)。

    Args:
        plan_confirmed: Phase B が確定した intent。
        losers: Phase B の落選者(``LOST_ARBITRATION`` を返す)。
        agents / world: 書き込み対象。
        tick: 現在 tick。
        schedule: mock 日課(就寝可否の判定に自宅セルを使う)。
        ledger: 金/物の台帳(``None`` なら C2 と同じ直接更新の経路)。

    Returns:
        ``ResolveOutcome``。
    """
    out = ResolveOutcome(
        tick=int(tick), n_confirmed=len(plan_confirmed), n_losers=len(losers), ledger=ledger
    )
    r = agents.registry
    with agents.writable(), world.writable():
        code = plan_confirmed.action_code.astype(np.int64)
        aid = plan_confirmed.agent_id.astype(np.int64)
        tgt = plan_confirmed.target_id.astype(np.int64)

        # 逐次ループ宣言: 行動語ぶん(13 分岐)。個体数には比例しない。
        for action in (
            ENGINE_STEP, ACT_MOVE, ACT_BOARD, ACT_ALIGHT, ACT_BUY, ACT_WAIT, ACT_TALK,
            ACT_LEAVE, ACT_REPORT, ACT_HELP, ACT_REFUSE, ACT_REST, ACT_SLEEP,
        ):
            sel = np.flatnonzero(code == action)
            if sel.size == 0:
                continue
            out.per_action[int(action)] = out.per_action.get(int(action), 0) + int(sel.size)
            if action != ENGINE_STEP:
                # 「直前に**試みた**行動」= B6 の主語(成功・失敗を問わず書く)。
                # エンジン継続は新しく試みた行動ではない(移動の続き)ので書かない。
                r.last_action[aid[sel]] = np.int8(action)
            _APPLY[action](agents, world, aid[sel], tgt[sel], tick, out, schedule)

        # 落選者(行動契約書 §2「落選者には失敗の意味論」)
        if len(losers):
            la = losers.agent_id.astype(np.int64)
            lc = losers.action_code.astype(np.int64)
            keep = lc != ENGINE_STEP
            if keep.any():
                r.last_action[la[keep]] = lc[keep].astype(np.int8)
            r.last_result[la] = int(ResultCode.LOST_ARBITRATION)
            r.last_result_tick[la] = int(tick)
            r.fail_streak[la] = np.minimum(r.fail_streak[la].astype(np.int16) + 1, 255).astype(
                np.uint8
            )
            out.add_result(ResultCode.LOST_ARBITRATION, int(la.size))

        # ---- 位置の確定と密度(予算行 P2 の測定対象) ----
        t0 = time.perf_counter()
        node = r.node.astype(np.int64)
        valid = node >= 0
        new_cell = np.where(valid, world.assets.node_cell[np.maximum(node, 0)], -1)
        r.cell[:] = new_cell.astype(np.int32)
        r.band[:] = np.where(valid, world.assets.node_band[np.maximum(node, 0)], 0).astype(np.int8)
        r.xy[:] = world.assets.node_xy[np.maximum(node, 0)]
        world.cells.density[:] = world.compute_density(r.cell)
        world.cells.density_stage[:] = world.density_stage()
        world.cells.open_count[:] = world.open_count_per_cell(tick)
        out.movement_seconds = time.perf_counter() - t0
    return out


# ---------------------------------------------------------------- 行動語ごとの適用
def _ok(agents: AgentState, aid: np.ndarray, tick: int, out: ResolveOutcome) -> None:
    r = agents.registry
    r.last_result[aid] = int(ResultCode.OK)
    r.last_result_tick[aid] = int(tick)
    r.fail_streak[aid] = 0
    out.add_result(ResultCode.OK, int(aid.size))


def _fail(
    agents: AgentState, aid: np.ndarray, code: ResultCode, tick: int, out: ResolveOutcome
) -> None:
    if aid.size == 0:
        return
    r = agents.registry
    r.last_result[aid] = int(code)
    r.last_result_tick[aid] = int(tick)
    r.fail_streak[aid] = np.minimum(r.fail_streak[aid].astype(np.int16) + 1, 255).astype(np.uint8)
    out.add_result(code, int(aid.size))


def _apply_engine_step(agents, world, aid, tgt, tick, out, schedule) -> None:
    """エンジン継続: next-hop に沿って 1 ノード進む。"""
    r = agents.registry
    new_node, arrived = world.graph.step_once(r.node[aid], tgt)
    stuck = (new_node.astype(np.int64) == r.node[aid].astype(np.int64)) & (~arrived)
    r.node[aid] = new_node
    out.n_moved += int(aid.size)
    if arrived.any():
        done = aid[arrived]
        r.activity[done] = int(Activity.IDLE)
        r.target_node[done] = -1
        out.n_arrived += int(done.size)
    if stuck.any():
        _fail(agents, aid[stuck], ResultCode.UNREACHABLE, tick, out)
        r.activity[aid[stuck]] = int(Activity.IDLE)
        r.target_node[aid[stuck]] = -1


def _apply_move(agents, world, aid, tgt, tick, out, schedule) -> None:
    """移動(行動契約書 §2.1): 経路が存在 → 位置は経路上へ。到達不能は失敗。"""
    r = agents.registry
    ok_cell = (tgt >= 0) & (tgt < world.n_cells)
    safe = np.clip(tgt, 0, world.n_cells - 1)
    dest_node = np.where(ok_cell, world.assets.cell_rep_node[safe], -1)
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
        _ok(agents, g, tick, out)
    _fail(agents, aid[~good], ResultCode.UNREACHABLE, tick, out)


def _apply_no_train(agents, world, aid, tgt, tick, out, schedule) -> None:
    """乗車: C2 に列車が無いので必ず「列車なし」(行動契約書 §2.1・C4 で実装)。"""
    _fail(agents, aid, ResultCode.NO_TRAIN, tick, out)


def _apply_no_stop(agents, world, aid, tgt, tick, out, schedule) -> None:
    """降車: 行動契約書 §2.1 の失敗語は「その駅には止まらない」(NO_STOP)。C2 では乗車中の個体が
    存在しないため常にこの失敗になる(列車は C4)。"""
    _fail(agents, aid, ResultCode.NO_STOP, tick, out)


def _apply_buy(agents, world, aid, tgt, tick, out, schedule) -> None:
    """購入: 営業中・在庫>0・所持金≧価格 → 在庫−1・所持金−価格・所持+1・**売上+同額**。

    台帳(``out.ledger``)があるときは金=``purchase_many``・物=``sell_many`` を通し、
    ``world.pois.stock`` は棚(真値)の写しとして書き戻す。
    """
    r = agents.registry
    led = out.ledger
    has_target = (tgt >= 0) & (tgt < world.n_poi)
    poi = np.clip(tgt, 0, max(0, world.n_poi - 1))
    open_mask = world.open_mask(tick)
    is_open = has_target & open_mask[poi]
    price = world.pois.price[poi].astype(np.int64)
    in_stock = is_open & (world.pois.stock[poi] > 0)
    if led is not None and led.goods is not None and in_stock.any():
        in_stock = in_stock & led.goods.can_sell(poi)  # 棚(SKU 別)が真値
    can_pay = in_stock & (r.money[aid].astype(np.int64) >= price)

    _fail(agents, aid[~has_target], ResultCode.BAD_TARGET, tick, out)
    _fail(agents, aid[has_target & ~is_open], ResultCode.CLOSED, tick, out)
    _fail(agents, aid[is_open & ~in_stock], ResultCode.OUT_OF_STOCK, tick, out)
    _fail(agents, aid[in_stock & ~can_pay], ResultCode.MONEY_SHORT, tick, out)

    win = np.flatnonzero(can_pay)
    if win.size == 0:
        return
    buyers = aid[win]
    bought = poi[win]
    paid = price[win]
    if led is not None and led.money is not None:
        status = led.money.purchase_many(buyers, bought, paid, tick)
        ok = np.asarray(status) == 0
        if not ok.all():
            _fail(agents, buyers[~ok], ResultCode.MONEY_SHORT, tick, out)
            out.n_ledger_rejected += int((~ok).sum())
            buyers, bought, paid = buyers[ok], bought[ok], paid[ok]
            if buyers.size == 0:
                return
    else:
        r.money[buyers] = (r.money[buyers].astype(np.int64) - paid).astype(np.int32)
    if led is not None and led.goods is not None:
        sold = np.asarray(led.goods.sell_many(bought, tick))
        if not sold.all():  # can_sell 済みなので通常は起きない(防御)
            _fail(agents, buyers[~sold], ResultCode.OUT_OF_STOCK, tick, out)
            out.n_ledger_rejected += int((~sold).sum())
            buyers, bought, paid = buyers[sold], bought[sold], paid[sold]
            if buyers.size == 0:
                return
        world.pois.stock[bought] = led.goods.aggregate_stock(bought).astype(
            world.pois.stock.dtype
        )
    else:
        _require_thawed(world)
        np.add.at(world.pois.stock, bought, -1)
    _require_thawed(world)
    np.add.at(world.pois.revenue, bought, paid)
    r.holdings[buyers] = np.minimum(r.holdings[buyers].astype(np.int16) + 1, 255).astype(np.uint8)
    r.hunger[buyers] = np.maximum(
        r.hunger[buyers].astype(np.int16) - BUY_HUNGER_RELIEF, 0
    ).astype(np.uint8)
    r.activity[buyers] = int(Activity.SHOPPING)
    out.n_purchases += int(win.size)
    out.revenue_delta += int(paid.sum())
    _ok(agents, buyers, tick, out)


def _apply_wait(agents, world, aid, tgt, tick, out, schedule) -> None:
    """待機: **常に可能=安全弁**(失敗しない)。"""
    agents.registry.activity[aid] = int(Activity.WAITING)
    _ok(agents, aid, tick, out)


def revert_conversation(agents, agent_ids: np.ndarray) -> None:
    """招待が不応答/ゲート却下だったとき、resolve が CONVERSING にした招待側を IDLE へ戻す。

    行動契約書 §3「不応答は『無視された』イベント(呼を消費しない)」。層2レビュー(C3)の指摘:
    resolve が先に CONVERSING を書き、ConversationManager.invite が後で None を返すため
    セッション無しの CONVERSING が残っていた。世界状態への書き込みは resolve のみ(本関数はその内側)。
    """
    ids = np.asarray(agent_ids, dtype=np.int64)
    if ids.size == 0:
        return
    with agents.writable():
        r = agents.registry
        r.activity[ids] = int(Activity.IDLE)
        r.talk_partner[ids] = -1


def _apply_talk(agents, world, aid, tgt, tick, out, schedule) -> None:
    """会話: 同一セル・相手 idle・自分でない → セッション生成(C2 は**記録だけ**)。"""
    r = agents.registry
    has = (tgt >= 0) & (tgt < agents.n) & (tgt != aid)
    partner = np.clip(tgt, 0, max(0, agents.n - 1))
    same_cell = has & (r.cell[aid] == r.cell[partner]) & (r.cell[aid] >= 0)
    idle = same_cell & (r.activity[partner] == int(Activity.IDLE))
    _fail(agents, aid[~has], ResultCode.BAD_TARGET, tick, out)
    _fail(agents, aid[has & ~same_cell], ResultCode.PARTNER_GONE, tick, out)
    _fail(agents, aid[same_cell & ~idle], ResultCode.PARTNER_BUSY, tick, out)
    win = np.flatnonzero(idle)
    if win.size == 0:
        return
    speakers = aid[win]
    r.activity[speakers] = int(Activity.CONVERSING)
    r.talk_partner[speakers] = partner[win].astype(np.int32)
    out.n_conversations += int(win.size)
    _ok(agents, speakers, tick, out)


def _apply_leave(agents, world, aid, tgt, tick, out, schedule) -> None:
    """退去: 所属解除(**失敗しない**)。"""
    r = agents.registry
    r.activity[aid] = int(Activity.IDLE)
    r.talk_partner[aid] = -1
    _ok(agents, aid, tick, out)


def _apply_record_only(agents, world, aid, tgt, tick, out, schedule) -> None:
    """通報・断る: C2 では状態を変えない(効果先が未実装=記録のみ)。失敗しない。"""
    _ok(agents, aid, tick, out)


def _apply_help(agents, world, aid, tgt, tick, out, schedule) -> None:
    """手伝い: 「相手が援助要求状態」を C2 は持たないので必ず失敗(契約書の失敗の意味論)。"""
    _fail(agents, aid, ResultCode.BAD_TARGET, tick, out)


def _apply_rest(agents, world, aid, tgt, tick, out, schedule) -> None:
    """休憩: 内受容 3 変数の回復(**失敗しない**)。"""
    r = agents.registry
    r.activity[aid] = int(Activity.RESTING)
    r.fatigue[aid] = np.maximum(
        r.fatigue[aid].astype(np.int16) - REST_FATIGUE_RELIEF, 0
    ).astype(np.uint8)
    _ok(agents, aid, tick, out)


def _apply_sleep(agents, world, aid, tgt, tick, out, schedule) -> None:
    """就寝: 当該セルが就寝可(mock=自宅セル)→ 睡眠状態 + **T2 日次内省の発火を記録**。"""
    r = agents.registry
    if schedule is not None:
        home = np.asarray(schedule.home_cell, dtype=np.int64)[aid]
        ok = (tgt >= 0) & (tgt < world.n_cells) & (tgt == home) & (
            r.cell[aid].astype(np.int64) == home
        )
    else:
        ok = (tgt >= 0) & (tgt < world.n_cells) & (r.cell[aid].astype(np.int64) == tgt)
    _fail(agents, aid[~ok], ResultCode.NO_BED, tick, out)
    win = aid[ok]
    if win.size == 0:
        return
    r.activity[win] = int(Activity.SLEEPING)
    r.target_node[win] = -1
    out.n_reflections += int(win.size)
    _ok(agents, win, tick, out)


# ---------------------------------------------------------------- 物の操作(U-Goods・§7.2)
def restock(
    world: World,
    ledger: LedgerBundle,
    stores: np.ndarray,
    qty: np.ndarray,
    tick: int,
    *,
    slot: np.ndarray | None = None,
) -> np.ndarray:
    """店舗補充・納品(外界→棚)。代金は域外仕入(店舗→外界)で払う。

    起動するのは店員・納品ドライバーの行動(C4-subH)。ここは**世界への書き戻し口**として
    ``world.pois.stock``(棚の写し)を更新する役だけを持つ。

    Returns:
        行ごとの成否 bool。
    """
    if ledger.goods is None:
        raise ValueError("物の台帳が注入されていない")
    s = np.asarray(stores, dtype=np.int64).ravel()
    ok = ledger.goods.restock_many(s, qty, tick, money=ledger.money, slot=slot)
    with world.writable():
        touched = s[np.asarray(ok)]
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
            _require_thawed(agents)
            np.add.at(holdings, a[ok], (-q[ok]).astype(holdings.dtype))
    return ok


def collect_waste(
    world: World, ledger: LedgerBundle, stores: np.ndarray | None, tick: int
) -> float:
    """廃棄物収集(店舗の廃棄ビン→bbox 外)。搬出質量[g]を返す(棚は動かない)。"""
    if ledger.goods is None:
        raise ValueError("物の台帳が注入されていない")
    return float(ledger.goods.collect_waste(stores, tick))


_APPLY: Final[dict[int, object]] = {
    ENGINE_STEP: _apply_engine_step,
    ACT_MOVE: _apply_move,
    ACT_BOARD: _apply_no_train,
    ACT_ALIGHT: _apply_no_stop,
    ACT_BUY: _apply_buy,
    ACT_WAIT: _apply_wait,
    ACT_TALK: _apply_talk,
    ACT_LEAVE: _apply_leave,
    ACT_REPORT: _apply_record_only,
    ACT_HELP: _apply_help,
    ACT_REFUSE: _apply_record_only,
    ACT_REST: _apply_rest,
    ACT_SLEEP: _apply_sleep,
}

assert len(_APPLY) == 13, "行動語 12 + エンジン継続 1"
assert _REFRACTORY_TICKS.size == N_WAKE_CONDITIONS
