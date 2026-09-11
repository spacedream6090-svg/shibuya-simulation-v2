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
from typing import Any, Final, Mapping

import numpy as np

from shibuya.agents.state import (
    N_WAKE_CONDITIONS,
    REFRACTORY_MINUTES,
    Activity,
    AgentState,
    ResultCode,
    WakeCondition,
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
    "set_conversing",
    "BODY_TICK_PERIOD",
    "BOARD_WAIT_LIMIT_TICKS",
    "REST_FATIGUE_RELIEF",
    "BUY_HUNGER_RELIEF",
    "SLEEP_FATIGUE_RELIEF",
    "ResolveOutcome",
    "initialize",
    "set_initial_activity",
    "set_plan_state",
    "begin_planned_sleep",
    "wake_from_plan",
    "apply_detection",
    "apply",
    "set_refractory",
    "clear_refractory",
    "refractory_ticks",
    "wake_condition_index",
    "normalized_refractory_scale",
    "advance_body",
    "restock",
    "discard_to_bin",
    "collect_waste",
    "consume",
    # ---- C4(世界過程 第1陣)の書き戻し口 ----
    "set_thermal",
    "set_notice_state",
    "set_open_flags",
    "place_at_external",
    "rail_arrive",
    "rail_depart",
    "sync_transit_activity",
    "release_indoor",
    "balk_queue",
    "request_open_close",
]

#: 内受容の自然変動の周期[tick](expedient)。
BODY_TICK_PERIOD: Final[int] = 30
REST_FATIGUE_RELIEF: Final[int] = 3
BUY_HUNGER_RELIEF: Final[int] = 4
SLEEP_FATIGUE_RELIEF: Final[int] = 2

#: 物の台帳の払い出しスロットを回す最大回数(``_apply_buy`` の注記・expedient)。
_SELL_SLOT_RETRIES: Final[int] = 8

#: 乗車待ちの打ち切り[tick](**expedient**・D-51 登録簿 §8)。
#: ホームで待ち始めてからこれだけ経っても列車が来なければ意図を消し「列車なし」を返す
#: (個体は次の起床で判断し直す)。値の根拠(答申 §3-1 行 4-7・親一次確認):
#: 渋谷の運転間隔は全線 2.2〜5.0 分・待ち時間 = 間隔の半分 → 最大 5 分の **6 倍**を上限に採る。
#: メトロ 3 線は **1〜4 時台の運行が 0 本**なので「待っても来ない時間帯」が実在する
#: (打ち切りが無いと、その時間帯にホームへ来た体が始発まで待ち続けて動かなくなる)。
BOARD_WAIT_LIMIT_TICKS: Final[int] = 30

#: 乗車の意図(``board_line``)を**保つ**行動(これ以外を選んだら意図は落ちる)。
#: 乗車=張り直し / 待機=ホームで待ち続ける / エンジン継続=ホームへ歩いている途中。
_BOARD_KEEP_ACTIONS: Final[tuple[int, ...]] = (ACT_BOARD, ACT_WAIT, ENGINE_STEP)

#: 就寝の意図(``sleep_pending``)を**保つ**行動(これ以外を選んだら意図は落ちる・D-62)。
#: 就寝=張り直し / エンジン継続=就寝地へ歩いている途中。
_SLEEP_KEEP_ACTIONS: Final[tuple[int, ...]] = (ACT_SLEEP, ENGINE_STEP)

_REFRACTORY_TICKS: Final[np.ndarray] = np.asarray(REFRACTORY_MINUTES, dtype=np.int32)
_REFRACTORY_TICKS.flags.writeable = False


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
    #: 「位置確定+密度」区間の**このスレッドの CPU 時間**[秒](``time.thread_time``)。
    #: ``movement_seconds``(壁時計)との差=**GIL 待ち/デスケジュール**。艦隊ランで
    #: P2(≤5 ms/フレーム)を割ったとき、仕事が増えたのか待たされたのかを 1 本で切り分ける
    #: (実装計画書 §4「httpx イベントループと numba 計算の干渉。出たら別プロセスへ」の測定点)。
    movement_cpu_seconds: float = 0.0
    #: この tick で使う台帳(``apply`` が入れる**呼びごとの文脈**。行動語の適用関数へ
    #: 引数を1本増やさずに渡すための欄=注入点は ``apply(..., ledger=...)`` の1か所だけ)。
    ledger: LedgerBundle | None = None
    #: 台帳が金の脚を却下した件数(診断行・通常は 0)。
    n_ledger_rejected: int = 0
    #: 鉄道運行(``engine.processes.rail.RailProcess``)。``None`` なら乗車は ``NO_TRAIN``(C2 互換)。
    rail: object | None = None
    #: 混雑場(``engine.processes.crowd.CrowdProcess``)。``None`` なら屋内占有を見ない(C2 互換)。
    crowd: object | None = None
    #: 乗車が成立した件数。
    n_boarded: int = 0
    #: 降車が成立した件数。
    n_alighted: int = 0
    #: 乗車待ちの行列に**新しく入った**件数(D-51・ホームに立った延べ人数)。
    n_board_waiting: int = 0
    #: 待ちの打ち切り件数(D-51・``BOARD_WAIT_LIMIT_TICKS`` 超過で意図を落とした)。
    n_board_timeout: int = 0
    #: 支払われた運賃の合計[円](保存則: Σmoney+Σrevenue+Σ運賃 が不変)。
    fare_paid: int = 0
    #: 満席で待ち行列へ入った件数(購入の「待ち時間」コスト・行動契約書 §2.1)。
    n_queued: int = 0
    #: ホテル客室在庫(``engine.processes.civic.HotelProcess``)。``None`` なら就寝は自宅のみ。
    hotel: object | None = None
    #: ホテルで就寝した件数(§7.2 ホテル客室在庫)。
    n_hotel_sleep: int = 0
    #: **就寝地へ着いて寝た**件数(D-62 (a) の意図保持ぶん。就寝境界で即座に寝た件数は
    #: ``begin_planned_sleep`` の戻り値で数える=あちらは ``apply`` の外で走る)。
    n_planned_sleep: int = 0

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
        # I6 −1 ガード(D-66): 域外居住者は ``home_cell < 0`` のまま来る(計画実行層が
        # 起動直後に ``place_at_external`` で外へ置く)。**セル表を −1 で索引しない**。
        # 全員が ``home_cell >= 0`` のラン(帰無腕・mock・合成世界)では 1 バイトも変わらない。
        has_home = home >= 0
        safe = np.where(has_home, home, 0)
        agents.registry.cell[:] = np.where(has_home, home, -1)
        node = np.where(has_home, world.assets.cell_rep_node[safe], -1)
        agents.registry.node[:] = node
        agents.registry.band[:] = np.where(has_home, world.assets.cell_band[safe], 0)
        agents.registry.xy[:] = np.where(
            has_home[:, None], world.assets.node_xy[np.maximum(node, 0)], 0.0
        )
        agents.registry.field("kind")[:] = np.asarray(schedule.kind)[:n]
        # W16 母集団を載せたランだけ年齢・性別が入る(mock は既定値 0 / −1 のまま)
        if getattr(schedule, "age", None) is not None:
            agents.registry.field("age")[:] = np.asarray(schedule.age)[:n]
        if getattr(schedule, "sex", None) is not None:
            agents.registry.field("sex")[:] = np.asarray(schedule.sex)[:n]
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


def set_initial_activity(agents: AgentState, activity) -> int:
    """tick 0 の ``activity`` を**計画(W17)の 0:00 時点の活動**から立てる(D-62 (b))。

    ``initialize`` は全員を ``SLEEPING`` に置く(週次表を持たない合成世界/mock 日課の
    既定=**従来どおり**)。週次表があるランだけ、この関数で 0:00 の活動から立て直す
    (``agents.weekly.WeeklySchedule.initial_activity``)。

    ``transit_state != 0``(域外滞在・乗車中)の個体は**触らない**——域外居住者は
    ``place_at_external`` が ``WAITING`` を立てており、3 値(乗客の保存則の分母)と
    ``activity`` の整合はそちらが正(D-62 の決定文「rail の事前割当の整合を保つ」)。

    Args:
        activity: 形 ``(n,)`` の ``Activity`` 値(``int8``)。

    Returns:
        実際に書いた体数。
    """
    act = np.asarray(activity, dtype=np.int8).ravel()
    with agents.writable():
        r = agents.registry
        if act.size != r.activity.size:
            raise ValueError(f"初期活動の長さが体数と違う({act.size} != {r.activity.size})")
        free = r.transit_state == 0
        r.activity[free] = act[free]
    return int(np.count_nonzero(free))


def set_plan_state(
    agents: AgentState,
    agent_id=None,
    *,
    activity=None,
    flags=None,
    flags_set: int | None = None,
    flags_clear: int | None = None,
) -> None:
    """``plan_activity`` / ``plan_flags``(D-66 計画実行層の 2 欄)への**唯一の書き込み口**。

    欄は ``AgentState(plan_columns=True)`` のランにしか無い(帰無腕は欄ごと無い)ので、
    **欄が無ければ黙って何もしない**=帰無腕・既存テストは 1 バイトも動かない。

    Args:
        agents: 個体状態。
        agent_id: 書く体(``None``=全体に一括代入)。
        activity: ``ACTIVITY_WORDS`` の索引(``agent_id`` と同じ長さかスカラー)。
        flags: ``plan_flags`` をそのまま置き換える値。
        flags_set / flags_clear: 立てる/落とすビット(``FLAG_*``)。

    Note:
        書くのは「計画の写し」であって世界状態ではないが、SoA への書き込みは
        ``resolve`` 以外から行わない規律(運用設計書 §2.2)に合わせてここに置く。
    """
    r = agents.registry
    if "plan_activity" not in r.arrays:
        return
    a = None if agent_id is None else np.asarray(agent_id, dtype=np.int64).ravel()
    if a is not None and a.size == 0:
        return
    with agents.writable():
        if activity is not None:
            v = np.asarray(activity, dtype=np.int8)
            if a is None:
                r.plan_activity[:] = v
            else:
                r.plan_activity[a] = v
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
    until = (int(tick) + tab[c]).astype(np.int32)
    with agents.writable():
        _require_thawed(agents)
        cur = agents.registry.refractory_until
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
    with agents.writable():
        _require_thawed(agents)
        agents.registry.refractory_until[a, c] = 0


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
    rail: object | None = None,
    crowd: object | None = None,
    hotel: object | None = None,
) -> ResolveOutcome:
    """Phase C: 確定した intent だけを世界へ適用する(**唯一の書き手**)。

    Args:
        plan_confirmed: Phase B が確定した intent。
        losers: Phase B の落選者(``LOST_ARBITRATION`` を返す)。
        agents / world: 書き込み対象。
        tick: 現在 tick。
        schedule: mock 日課(就寝可否の判定に自宅セルを使う)。
        ledger: 金/物の台帳(``None`` なら C2 と同じ直接更新の経路)。
        rail: 鉄道運行(C4 世界過程)。``None`` なら乗車=``NO_TRAIN``・降車=``NO_STOP``。
        crowd: 混雑場(C4 世界過程)。``None`` なら屋内占有・待ち行列を見ない。
        hotel: ホテル客室在庫(C4 世界過程)。``has_bed(agent_ids, cells)`` を持つものを渡すと、
            チェックイン済みの来街者は**自宅でなくても就寝できる**(§7.2 ホテル客室在庫)。

    Returns:
        ``ResolveOutcome``。
    """
    out = ResolveOutcome(
        tick=int(tick),
        n_confirmed=len(plan_confirmed),
        n_losers=len(losers),
        ledger=ledger,
        rail=rail,
        crowd=crowd,
        hotel=hotel,
    )
    r = agents.registry
    with agents.writable(), world.writable():
        code = plan_confirmed.action_code.astype(np.int64)
        aid = plan_confirmed.agent_id.astype(np.int64)
        tgt = plan_confirmed.target_id.astype(np.int64)

        # D-51: 乗車の意図を持ったまま**別の行動**を選んだ体は、その時点で意図を落とす
        # (ホームへ歩いている途中で気が変わった=待ち行列に幽霊を残さない)。
        if code.size:
            other = ~np.isin(code, _BOARD_KEEP_ACTIONS)
            if other.any():
                drop = aid[other]
                drop = drop[r.board_line[drop] >= 0]
                if drop.size:
                    r.board_line[drop] = -1
                    r.board_since[drop] = -1
            # D-62: 就寝の意図も同じ(就寝地へ歩く途中で**別の行動**を選んだら意図は落ちる)。
            other_sleep = ~np.isin(code, _SLEEP_KEEP_ACTIONS)
            if other_sleep.any():
                drop = aid[other_sleep]
                drop = drop[r.sleep_pending[drop] != 0]
                if drop.size:
                    r.sleep_pending[drop] = 0

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

        # ---- D-51 乗車待ちの捌き(停車中の列車へ FIFO・打ち切り) ----
        # **行動語の適用の後・位置確定の前**に置く: この tick にホームへ着いた体(エンジン継続)と
        # この tick に乗車を選んだ体を同じ列車に乗せるため。
        _serve_board_queue(agents, world, tick, out)

        # ---- 位置の確定と密度(予算行 P2 の測定対象) ----
        t0 = time.perf_counter()
        c0 = time.thread_time()
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
        out.movement_cpu_seconds = time.thread_time() - c0
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
    if stuck.any():
        _fail(agents, aid[stuck], ResultCode.UNREACHABLE, tick, out)
        r.activity[aid[stuck]] = int(Activity.IDLE)
        r.target_node[aid[stuck]] = -1
        # 行き止まりでホームへ着けない体は乗車の意図も落とす(幽霊を残さない)
        r.board_line[aid[stuck]] = -1
        r.board_since[aid[stuck]] = -1
        r.sleep_pending[aid[stuck]] = 0  # D-62: 就寝地へ着けない体も同じ(起きたまま)


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
                out.rail.n_board_waiting += int(fresh.size)
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
            pay_ok = r.money[ids].astype(np.int64) >= fare
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


def _board_riders(agents, world, boarded, tick: int, out: ResolveOutcome) -> None:
    """乗車の確定(運賃の金の脚 → 状態遷移 → 列車 SoA)。``boarded`` = ``[(便, 個体列), …]``。"""
    if not boarded:
        return
    r = agents.registry
    fare = int(out.rail.fare_yen)
    riders = np.concatenate([a for _, a in boarded]).astype(np.int64)
    train_of = np.concatenate([np.full(a.size, t, dtype=np.int64) for t, a in boarded])
    led = out.ledger
    if led is not None and led.money is not None:
        # 運賃 = 世帯 → 外界(持ち出し=sink)。鉄道事業者は第1陣の6部門に無い(§2.1)ので
        # 許された部門対(H,W)/科目「持ち出し」に載せる=**科目の意味の拡張は台帳側の宣言事項**。
        status = np.asarray(out.rail.pay_fares(led.money, riders, fare, int(tick)))
        ok = status == 0
        if not ok.all():
            _fail(agents, riders[~ok], ResultCode.FARE_SHORT, tick, out)
            out.n_ledger_rejected += int((~ok).sum())
            riders, train_of = riders[ok], train_of[ok]
            if riders.size == 0:
                return
    else:
        r.money[riders] = (r.money[riders].astype(np.int64) - fare).astype(np.int32)
    out.fare_paid += int(fare) * int(riders.size)
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
    out.rail.n_boarded_from_queue += int(riders.size)
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

    # ---- 屋内占有(16行表 行2・容量 c の M/M/c 近似): 満席なら待ち行列へ ----
    if out.crowd is not None and can_pay.any():
        room = np.zeros(aid.size, dtype=bool)
        sel = np.flatnonzero(can_pay)
        room[sel] = np.asarray(out.crowd.can_admit(poi[sel]), dtype=bool)
        queued = aid[can_pay & ~room]
        if queued.size:
            # 契約書 §2.1「購入」のコスト欄「価格・**待ち時間**」= 満席時は並ぶ(失敗ではない)
            r.activity[queued] = int(Activity.WAITING)
            r.queue_poi[queued] = poi[can_pay & ~room].astype(np.int32)
            r.queue_since[queued] = int(tick)
            out.n_queued += int(queued.size)
            _ok(agents, queued, tick, out)
        can_pay = can_pay & room

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
        # ``GoodsLedger.sell_many`` は「**最初の非空スロット**」からしか払い出さない
        # (``_first_nonempty_slot``)。同一 tick に同一 POI へ複数人が来ると、先頭スロットの
        # 残りを超えた行は他スロットに在庫があっても失敗する。``can_sell`` は棚の**合計**で
        # 判定しているので、これは台帳側の粒度の食い違い(economy は本サブの読み取り専用領域)。
        # ここで**失敗行だけを次のスロットへ回す**ことで ``can_sell`` の意味に合わせる。
        # 逐次ループ宣言(P4): **スロット数**ぶん(≤8)。購入行数には比例しない。
        sold = np.zeros(bought.size, dtype=bool)
        pending = np.arange(bought.size, dtype=np.int64)
        for _ in range(_SELL_SLOT_RETRIES):
            if pending.size == 0:
                break
            got = np.asarray(led.goods.sell_many(bought[pending], tick), dtype=bool)
            sold[pending[got]] = True
            pending = pending[~got]
            if not got.any():
                break  # 進捗なし = 本当に在庫切れ
        if not sold.all():
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
    if out.crowd is not None:
        # 在席の登録(屋内占有の集約=人物②「行列・人だかり」の素)
        r.poi_ref[buyers] = bought.astype(np.int32)
        r.poi_since[buyers] = int(tick)
        r.queue_poi[buyers] = -1
        out.crowd.on_admit(bought)
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


def set_conversing(agents: AgentState, inviters, invitees) -> None:
    """会話成立時に**両側**を CONVERSING にする(C6・09-09)。

    C3/C4 は招待側だけを CONVERSING にしていた(被招待側の離脱をセルで検出する回避策)。
    C6 で被招待側が**自分の呼で承諾する**ようになったので、成立した時点で両側を
    セッション参加状態にする(行動契約書 §3「終了はエンジン」=両側の解放も
    ``engine.run`` の ``conv.step`` が行う)。世界状態への書き込みは resolve のみ。
    """
    a = np.asarray(inviters, dtype=np.int64)
    b = np.asarray(invitees, dtype=np.int64)
    if a.size == 0:
        return
    with agents.writable():
        _require_thawed(agents)
        r = agents.registry
        r.activity[a] = int(Activity.CONVERSING)
        r.activity[b] = int(Activity.CONVERSING)
        r.talk_partner[a] = b.astype(np.int32)
        r.talk_partner[b] = a.astype(np.int32)


#: 声をかけられない相手の状態(C6・09-09)。
#: **会話中**=行動契約書 §2.1 の失敗「相手が会話中」(``PARTNER_BUSY``)。
#: **就寝中**=声をかけても応答できない(起床(ii) の被招待で起こす対象にしない)。
#: C3 は「相手が **IDLE** であること」を要求していたが、それだと移動中・待機中・
#: 買い物中の相手に声をかけられず、C6 の 1 日ランで会話が 1 件も成立しなかった
#: (**expedient**: 「話しかけられる状態」の正典は無い。ablation 対象)。
_UNADDRESSABLE: Final[tuple[int, ...]] = (int(Activity.CONVERSING), int(Activity.SLEEPING))


def _apply_talk(agents, world, aid, tgt, tick, out, schedule) -> None:
    """会話: 同一セル・相手が応答可能・自分でない → 招待成立(成否は被招待の呼が決める)。"""
    r = agents.registry
    has = (tgt >= 0) & (tgt < agents.n) & (tgt != aid)
    partner = np.clip(tgt, 0, max(0, agents.n - 1))
    same_cell = has & (r.cell[aid] == r.cell[partner]) & (r.cell[aid] >= 0)
    pact = r.activity[partner]
    addressable = same_cell & ~np.isin(pact, _UNADDRESSABLE)
    idle = addressable
    _fail(agents, aid[~has], ResultCode.BAD_TARGET, tick, out)
    _fail(agents, aid[has & ~same_cell], ResultCode.PARTNER_GONE, tick, out)
    _fail(agents, aid[same_cell & ~addressable], ResultCode.PARTNER_BUSY, tick, out)
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
    # ホテル客室(§7.2): チェックイン済みの来街者は自宅でなくても寝られる。
    # 満室でチェックインできなかった個体はここへ来ても ``NO_BED``(契約書 §2.1 の失敗語彙)。
    n_hotel = 0
    if out.hotel is not None and (~ok).any():
        bed = np.zeros(aid.size, dtype=bool)
        rest = np.flatnonzero(~ok)
        bed[rest] = np.asarray(
            out.hotel.has_bed(aid[rest], r.cell[aid[rest]].astype(np.int64)), dtype=bool
        )
        n_hotel = int(np.count_nonzero(bed))
        ok = ok | bed
    out.n_hotel_sleep += n_hotel
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


# ---------------------------------------------------------------- C4: 世界過程の書き戻し口
# 世界過程設計書 §3 実装原則3「世界状態への書き込み口は1本(答申原則5=resolve 経由)。
# **世界過程も例外にしない**」。``engine/processes/*`` は状態を直接触らず、以下の口だけを呼ぶ。
def set_thermal(agents: AgentState, thermal) -> None:
    """体感温度(内受容3変数の1本)を一括代入する(知覚契約書 §3 内受容・日陰係数0.86)。

    Args:
        agents: 個体状態。
        thermal: ``(n,)`` の 0-10 値(呼び出し側で丸め・クリップ済み)。
    """
    v = np.asarray(thermal)
    with agents.writable():
        agents.registry.thermal[:] = np.clip(v, 0, 10).astype(np.uint8)


def set_notice_state(pstate, heading, task_flag, indices=None) -> None:
    """知覚側 SoA(M12: 向き量子化+課題従事フラグ)を書く(**書き込み口は resolve 一本**)。

    ``perception.state.PerceptionState`` は ``agents``/``world`` と同じ凍結規律を持ち、
    ``writable()`` を呼んでよいのは本ファイルだけ(``tests/engine/test_two_phase.py``)。
    p_notice(知覚契約書 §3.1)の ``m_ecc``/``m_load`` はこの 2 byte/体を読む。

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


def release_indoor(agents: AgentState, agent_ids) -> None:
    """在席の解除(回転率=滞在上限・16行表 行2 の expedient)。"""
    a = np.asarray(agent_ids, dtype=np.int64).ravel()
    if a.size == 0:
        return
    with agents.writable():
        r = agents.registry
        r.poi_ref[a] = -1
        r.poi_since[a] = -1
        r.activity[a] = np.where(
            r.activity[a] == int(Activity.SHOPPING), int(Activity.IDLE), r.activity[a]
        ).astype(r.activity.dtype)


def balk_queue(agents: AgentState, agent_ids, tick: int) -> None:
    """待ち行列からの離脱(離脱閾値・``INTERRUPTED``=「途中打ち切り(混雑・閉鎖)」)。"""
    a = np.asarray(agent_ids, dtype=np.int64).ravel()
    if a.size == 0:
        return
    with agents.writable():
        r = agents.registry
        r.queue_poi[a] = -1
        r.queue_since[a] = -1
        r.activity[a] = int(Activity.IDLE)
        r.last_result[a] = int(ResultCode.INTERRUPTED)
        r.last_result_tick[a] = int(tick)
        r.fail_streak[a] = np.minimum(r.fail_streak[a].astype(np.int16) + 1, 255).astype(np.uint8)


def request_open_close(
    agents: AgentState,
    world: World,
    agent_ids,
    poi_ids,
    want_open,
    tick: int,
    *,
    permitted=None,
) -> np.ndarray:
    """役割行動「開閉店」(行動契約書 §2.2)。権限=当該 POI の担当従業者だけ。

    Args:
        agents / world: 状態。
        agent_ids: 行為者。
        poi_ids: 対象 POI。
        want_open: 開けるなら True。
        tick: 現在 tick。
        permitted: 行ごとの権限 bool(``None`` なら全て権限なし=``NO_PERMISSION``)。

    Returns:
        行ごとの ``ResultCode``(0=OK / 14=権限なし)。

    Note:
        効果は PlanSpec の**実績確定**(``ActualLog``)であり、フラグの反映もここで行う。
        契約書は失敗の意味論を「権限なし」の 1 つだけ与えている。
    """
    a = np.asarray(agent_ids, dtype=np.int64).ravel()
    p = np.asarray(poi_ids, dtype=np.int64).ravel()
    w = np.asarray(want_open, dtype=bool).ravel()
    out_code = np.full(a.size, int(ResultCode.NO_PERMISSION), dtype=np.int64)
    if a.size == 0:
        return out_code
    ok = (
        np.zeros(a.size, dtype=bool) if permitted is None else np.asarray(permitted, dtype=bool)
    )
    with agents.writable(), world.writable():
        r = agents.registry
        if ok.any():
            world.pois.open_now[p[ok]] = w[ok].astype(np.int8)
            out_code[ok] = int(ResultCode.OK)
            r.last_result[a[ok]] = int(ResultCode.OK)
            r.fail_streak[a[ok]] = 0
        if (~ok).any():
            r.last_result[a[~ok]] = int(ResultCode.NO_PERMISSION)
        r.last_result_tick[a] = int(tick)
    return out_code


_APPLY: Final[dict[int, object]] = {
    ENGINE_STEP: _apply_engine_step,
    ACT_MOVE: _apply_move,
    ACT_BOARD: _apply_board,
    ACT_ALIGHT: _apply_alight,
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
