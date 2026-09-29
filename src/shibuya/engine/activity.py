"""engine.activity — 行為と活動の二層の**活動層**(二層の実装 段 2・D-116・第276)。

正典
- ``docs/design/v2-two-layer-implementation-agenda.md`` §2(段 2 の決め)+ §6(段 1 の問いへの
  親の決め・第275)。草案 ``docs/design/v2-action-activity-two-layer-draft.md`` §4-4。
- 活動 = 世界を変えない時間の使い方(自由文 10 字+持続の上限)。エンジンが活動に対して持つのは
  (i) 体の位置(「あたり」=近傍を歩き回る)(ii) 持続(``activity_until``・満了入口)
  (iii) 観測への表示(同セルの B4b に 1 行)の 3 つだけ。契約行・裁定・辞書写像は持たない。

本モジュールの役割
- **値を決めるだけ**で、世界状態への書き込みは ``engine.resolve``(``set_activity`` /
  ``set_activity_until`` / ``advance_body``)が唯一の書き手(運用設計書 §2.2 Phase C)。
- Python 側の状態 = 体ごとの**活動の文**(``text``)と「まで」の型(``until_kind``・到着/相手の
  事象で満了させるために要る)。両方とも ``state_hash`` で checkpoint に混ぜる。
  アジェンダ §2 は置き場所を ``RunState.activity_text`` と書いたが、``engine.run`` に RunState は
  無いので**本クラスの ``text``** に置いた(expedient・§5)。

逐次ループ宣言(P4)
1. ``ActivityLayer.after_resolve``: この tick に適用した**応答の数**ぶん(≤ 1 tick の呼数)。
   「次の予定」の引き当てと文の intern だけ。
2. ``ActivityLayer.settle_events``: 「相手」待ちの体のうち持続中の数ぶん(会話状態の問い合わせ)。
3. ``ActivityLayer.cell_rows``: この tick に表示できる (セル, 活動文) の組の数ぶん(≤ 活動中の体数)。
4. ``ActivityLayer.state_hash``: 体数ぶん(checkpoint のときだけ・文の digest はキャッシュ)。
5. ``_wander_neighbors``: 起動時 1 回のセル数ぶん(セル × セルの比較は配列演算)。

expedient(本モジュール分・アジェンダ §5 に行)
- 活動の種別の割り当て(移動=目的地つき・移動+あたり=あたり・乗車=目的地つき・購入/食事/並ぶ=
  在店・就寝=活動なし・それ以外=その場)。
- 「あたり」の候補=**同じ層**で格子の Chebyshev 距離 ≤ 2 のセル(自分のセルを除く・代表ノード
  あり)。候補が無ければその場(自分のセル)。
- 「まで」の解決の細部(分→tick は切り上げ・全ての型に上限 480 分・最短 1 tick・時刻は tick 0 を
  00:00 とする約束=``calls_by_hour`` と同じ・「次の予定」は計画境界の表=W17 か mock 日課)。
- 行為が失敗し活動が「なし」の体は**次の tick に満了**(=即時に考え直す)。
- 表示できない活動文(なし・空・個体依存語・省略記法の語を含む)は B4b に出さない。
"""

from __future__ import annotations

import hashlib
import math
from typing import Any, Final, Mapping, NamedTuple, Sequence

import numpy as np

from shibuya.agents.state import (
    ACTIVITY_UNTIL_NONE,
    WAKE_CONDITION_CLASS,
    Activity,
    ActivityKind,
    ResultCode,
    WakeCondition,
)
from shibuya.core.hashing import wander_key_array
from shibuya.engine import commit as C
from shibuya.engine import resolve as R
from shibuya.llm.contract import (
    NO_TARGET,
    UNTIL_DEFAULT_MINUTES,
    UNTIL_MAX_MINUTES,
    UntilKind,
)
from shibuya.perception import normalize as PN

__all__ = [
    "WANDER_RADIUS_CELLS",
    "PARTNER_MAX_MINUTES",
    "MINUTES_PER_DAY",
    "ActivityPayload",
    "payload_of",
    "activity_kind_of",
    "displayable_activity",
    "ActivityLayer",
]

#: 「あたり」の半径[セル](格子の Chebyshev 距離・アジェンダ §2・expedient・感度腕 1/2/4)。
WANDER_RADIUS_CELLS: Final[int] = 2
#: 「まで: 相手」の上限[分](待ちぼうけの打ち切り・アジェンダ §2・expedient)。
PARTNER_MAX_MINUTES: Final[int] = 60
#: 1 日の分(時刻 HH:MM の解決に使う)。
MINUTES_PER_DAY: Final[int] = 1_440


class ActivityPayload(NamedTuple):
    """1 応答ぶんの活動(パーサ v3 の欄を運ぶだけ)。"""

    text: str
    until_kind: int
    until_value: int
    wander: bool


def payload_of(res: Any) -> ActivityPayload | None:
    """``BridgeResult``/艦隊の ``Outcome`` → 活動(語彙 v3 の応答だけ・それ以外は ``None``)。"""
    parse = getattr(res, "parse", None)
    until = getattr(parse, "until", None)
    if until is None:
        return None
    target = getattr(res, "target", None)
    return ActivityPayload(
        text=str(getattr(parse, "activity", "") or NO_TARGET),
        until_kind=int(until.kind),
        until_value=int(until.value),
        wander=bool(getattr(target, "wander", False)),
    )


def activity_kind_of(code: np.ndarray, wander: np.ndarray) -> np.ndarray:
    """行動コード(と「あたり」の印)→ ``ActivityKind``(expedient・モジュール注記)。"""
    c = np.asarray(code, dtype=np.int64)
    w = np.asarray(wander, dtype=bool)
    kind = np.full(c.size, int(ActivityKind.IN_PLACE), dtype=np.int64)
    move = c == C.ACT_MOVE
    kind[move] = int(ActivityKind.MOVE_TO)
    kind[move & w] = int(ActivityKind.WANDER)
    kind[c == C.ACT_BOARD] = int(ActivityKind.MOVE_TO)
    kind[np.isin(c, (C.ACT_BUY, C.ACT_EAT, C.ACT_QUEUE))] = int(ActivityKind.IN_SHOP)
    kind[c == C.ACT_SLEEP] = int(ActivityKind.NONE)
    return kind


def displayable_activity(text: str) -> bool:
    """B4b に出せる活動文か(なし・空・§2.4 ⑧ の個体依存語・⑥ の省略記法を含む文は出さない)。"""
    t = PN.canonical_whitespace(str(text)).strip()
    if not t or t == NO_TARGET:
        return False
    if any(p.search(t) for _, p in PN.AGENT_DEPENDENT_PATTERNS):
        return False
    if any(a in t for a in PN.ABBREVIATIONS):
        return False
    return "\n" not in t


def _wander_neighbors(assets: Any, radius: int) -> tuple[np.ndarray, np.ndarray]:
    """セル → 「あたり」の候補セル(CSR: ``start``(n+1)・``cells``)。起動時 1 回。"""
    ix = np.asarray(assets.cell_ix, dtype=np.int64)
    iy = np.asarray(assets.cell_iy, dtype=np.int64)
    band = np.asarray(assets.cell_band, dtype=np.int64)
    rep = np.asarray(assets.cell_rep_node, dtype=np.int64)
    n = ix.size
    near = (
        (np.abs(ix[:, None] - ix[None, :]) <= radius)
        & (np.abs(iy[:, None] - iy[None, :]) <= radius)
        & (band[:, None] == band[None, :])
        & (rep[None, :] >= 0)
    )
    np.fill_diagonal(near, False)
    counts = near.sum(axis=1).astype(np.int64)
    start = np.zeros(n + 1, dtype=np.int64)
    np.cumsum(counts, out=start[1:])
    cells = np.nonzero(near)[1].astype(np.int64)  # 行優先=セル順・列は昇順
    return start, cells


class ActivityLayer:
    """活動層(``engine.run`` が ``vocab_version="v3"`` かつ ``activity=True`` のときだけ作る)。

    Args:
        n_agents: 体数。
        world: 世界(``assets`` のセル格子を読む)。
        run_salt: ラン塩(「あたり」の抽選)。
        tick_seconds: 1 tick の秒数(分→tick の換算)。
        boundary_agent / boundary_tick: 計画境界の表(W17 か mock 日課・「次の予定」の引き当て)。
    """

    def __init__(
        self,
        n_agents: int,
        world: Any,
        run_salt: bytes,
        *,
        tick_seconds: int = 60,
        boundary_agent: np.ndarray | None = None,
        boundary_tick: np.ndarray | None = None,
    ) -> None:
        self.n = int(n_agents)
        self.salt = bytes(run_salt)
        self.minutes_per_tick = float(tick_seconds) / 60.0
        self.text: list[str] = [NO_TARGET] * self.n
        self.until_kind = np.zeros(self.n, dtype=np.int8)
        #: 表示用の文の intern(0 = 出さない文)。
        self._text_ids: dict[str, int] = {}
        self._texts: list[str] = [""]
        self.text_id = np.zeros(self.n, dtype=np.int64)
        self._digest_cache: dict[str, bytes] = {}
        self._nbr_start, self._nbr_cells = _wander_neighbors(world.assets, WANDER_RADIUS_CELLS)
        ba = np.asarray(boundary_agent if boundary_agent is not None else [], dtype=np.int64)
        bt = np.asarray(boundary_tick if boundary_tick is not None else [], dtype=np.int64)
        order = np.lexsort((bt, ba)) if ba.size else np.zeros(0, dtype=np.int64)
        self._bt_agent = ba[order]
        self._bt_tick = bt[order]
        self._bt_start = np.searchsorted(self._bt_agent, np.arange(self.n + 1), side="left")
        # ---- 計数(manifest・summary の素材) ----
        self.n_set = 0
        self.n_expiry_candidates = 0
        self.n_cell_suppressed = 0
        self.n_arrival_expired = 0
        self.n_partner_expired = 0
        self.n_fail_immediate = 0
        #: 9a: 退去(活動欄「なし」)で次の tick に満了させた件数。切替口(``engine.run`` が退去の効果と揃える)。
        self.n_leave_expired = 0
        self.leave_effect = True
        self.n_wander_steps = 0
        self.n_wander_bad = 0
        self.n_intent_moves = 0
        self.kind_counts = np.zeros(len(ActivityKind), dtype=np.int64)

    # ------------------------------------------------------------------ 換算
    def _ticks(self, minutes: np.ndarray) -> np.ndarray:
        """分 → tick(切り上げ)。"""
        m = np.asarray(minutes, dtype=np.float64)
        return np.ceil(m / self.minutes_per_tick).astype(np.int64)

    def _next_boundary(self, agent: int, tick: int) -> int:
        """体の次の計画境界の tick(無ければ −1)。"""
        lo, hi = int(self._bt_start[agent]), int(self._bt_start[agent + 1])
        if hi <= lo:
            return -1
        k = lo + int(np.searchsorted(self._bt_tick[lo:hi], int(tick), side="right"))
        return int(self._bt_tick[k]) if k < hi else -1

    def resolve_until(
        self, agent_id: np.ndarray, until_kind: np.ndarray, until_value: np.ndarray, tick: int
    ) -> np.ndarray:
        """「まで」→ ``activity_until``(tick)。上限 ``UNTIL_MAX_MINUTES``・最短 1 tick。"""
        a = np.asarray(agent_id, dtype=np.int64)
        k = np.asarray(until_kind, dtype=np.int64)
        v = np.asarray(until_value, dtype=np.int64)
        t = int(tick)
        cap = t + int(self._ticks(np.asarray([UNTIL_MAX_MINUTES]))[0])
        out = np.full(a.size, t + int(self._ticks(np.asarray([UNTIL_DEFAULT_MINUTES]))[0]))
        mins = k == int(UntilKind.MINUTES)
        out[mins] = t + self._ticks(v[mins])
        default = k == int(UntilKind.DEFAULT)
        out[default] = t + self._ticks(v[default])
        out[k == int(UntilKind.ARRIVAL)] = cap  # 到着の事象で満了(settle_events)
        out[k == int(UntilKind.PARTNER)] = t + int(
            self._ticks(np.asarray([PARTNER_MAX_MINUTES]))[0]
        )
        clock = np.flatnonzero(k == int(UntilKind.CLOCK))
        if clock.size:
            now_min = int(math.floor(t * self.minutes_per_tick)) % MINUTES_PER_DAY
            delta = (v[clock] - now_min) % MINUTES_PER_DAY
            delta = np.where(delta == 0, MINUTES_PER_DAY, delta)  # 同じ時刻=過去=翌日
            out[clock] = t + self._ticks(delta)
        # 逐次ループ宣言1: 「次の予定」の応答の数ぶん
        for j in np.flatnonzero(k == int(UntilKind.NEXT_SCHEDULE)):
            nb = self._next_boundary(int(a[j]), t)
            if nb > t:
                out[j] = nb
        return np.clip(out, t + 1, cap)

    # ------------------------------------------------------------------ 応答の適用後
    def _intern(self, text: str) -> int:
        tid = self._text_ids.get(text)
        if tid is None:
            tid = len(self._texts) if displayable_activity(text) else 0
            if tid:
                self._texts.append(PN.canonical_whitespace(text).strip())
            self._text_ids[text] = tid
        return tid

    def after_resolve(
        self,
        agents: Any,
        tick: int,
        agent_id: Sequence[int],
        action_code: Sequence[int],
        payloads: Sequence[ActivityPayload | None],
    ) -> int:
        """この tick に適用した応答の活動を書く(``resolve.set_activity`` 経由)。

        行為の成否(``last_result``)は ``resolve.apply`` の**後**に読む: 失敗し活動が「なし」の
        体は次の tick に満了(即時に考え直す)。同じ体の応答が 2 件あれば**後**を採る。

        Returns:
            書いた体の数。
        """
        rows: dict[int, tuple[int, ActivityPayload]] = {}
        # 逐次ループ宣言1: 応答の数ぶん
        for a, code, p in zip(agent_id, action_code, payloads):
            if p is None:
                continue
            rows[int(a)] = (int(code), p)
        if not rows:
            return 0
        ids = np.fromiter(rows.keys(), dtype=np.int64, count=len(rows))
        codes = np.fromiter((c for c, _ in rows.values()), dtype=np.int64, count=len(rows))
        pls = [p for _, p in rows.values()]
        wander = np.fromiter((p.wander for p in pls), dtype=bool, count=len(pls))
        ukind = np.fromiter((p.until_kind for p in pls), dtype=np.int64, count=len(pls))
        uval = np.fromiter((p.until_value for p in pls), dtype=np.int64, count=len(pls))
        kind = activity_kind_of(codes, wander)
        until = self.resolve_until(ids, ukind, uval, tick)
        # 行為が失敗し活動が「なし」=次の tick に満了(即時に考え直す・アジェンダ §2)
        reg = agents.registry
        failed = (reg.last_result_tick[ids] == int(tick)) & (
            reg.last_result[ids] != int(ResultCode.OK)
        )
        no_text = np.fromiter((p.text == NO_TARGET for p in pls), dtype=bool, count=len(pls))
        now = failed & no_text
        until = np.where(now, int(tick) + 1, until)
        self.n_fail_immediate += int(np.count_nonzero(now))
        # 9a(D-112 ④): 退去=所属を解いて活動が終わる。活動欄が「なし」なら次の tick に満了(考え直す)
        leave_now = (codes == C.ACT_LEAVE) & no_text & ~now & bool(self.leave_effect)
        if bool(leave_now.any()):
            until = np.where(leave_now, int(tick) + 1, until)
            self.n_leave_expired += int(np.count_nonzero(leave_now))
        # 就寝=活動なし(睡眠は計画の実行が持つ・D-62)
        none_kind = kind == int(ActivityKind.NONE)
        until = np.where(none_kind, ACTIVITY_UNTIL_NONE, until)
        R.set_activity(agents, ids, until, kind)
        for j, a in enumerate(ids.tolist()):
            p = pls[j]
            self.text[a] = p.text
            self.until_kind[a] = np.int8(p.until_kind)
            self.text_id[a] = self._intern(p.text)
        self.n_set += int(ids.size)
        np.add.at(self.kind_counts, kind, 1)
        return int(ids.size)

    def force_arrival(
        self, agents: Any, agent_id: Sequence[int], tick: int, *, count: bool = True
    ) -> None:
        """段 2c: 意図を立てた体の活動を**目的地つき移動・到着まで**にする(``after_resolve`` の後)。

        応答の行為(購入など)で ``after_resolve`` が付けた種別(在店など)を上書きする。持続の
        上限は ``UNTIL_MAX_MINUTES``(到着の事象で満了=``settle_events``)。活動の文は応答のまま
        (歩いている間も B4b に出る)。種別の設定件数は上書きしたぶんを付け替える。
        """
        ids = np.asarray(agent_id, dtype=np.int64)
        if ids.size == 0:
            return
        t = int(tick)
        cap = t + int(self._ticks(np.asarray([UNTIL_MAX_MINUTES]))[0])
        prev = np.asarray(agents.registry.activity_kind)[ids].astype(np.int64)
        R.set_activity(
            agents, ids, np.full(ids.size, cap, dtype=np.int64),
            np.full(ids.size, int(ActivityKind.MOVE_TO), dtype=np.int64),
        )
        self.until_kind[ids] = np.int8(int(UntilKind.ARRIVAL))
        np.subtract.at(self.kind_counts, prev, 1)
        self.kind_counts[int(ActivityKind.MOVE_TO)] += int(ids.size)
        if count:
            self.n_intent_moves += int(ids.size)

    def settle_events(self, agents: Any, tick: int, conv: Any | None = None) -> None:
        """到着・会話成立で満了させる(次の tick に満了入口へ)。``resolve.apply`` と会話の後。"""
        reg = agents.registry
        t = int(tick)
        live = np.asarray(reg.activity_until) > t + 1
        if not bool(live.any()):
            return
        uk = self.until_kind
        act = np.asarray(reg.activity)
        arrived = (
            live
            & (uk == int(UntilKind.ARRIVAL))
            & (act != int(Activity.MOVING))
            & (act != int(Activity.RIDING))
        )
        idx = np.flatnonzero(arrived)
        if idx.size:
            R.set_activity_until(agents, idx, t + 1)
            self.n_arrival_expired += int(idx.size)
        if conv is not None:
            wait = np.flatnonzero(live & (uk == int(UntilKind.PARTNER)))
            # 逐次ループ宣言2: 「相手」待ちで持続中の体の数ぶん
            met = [int(a) for a in wait.tolist() if conv.is_busy(int(a))]
            if met:
                R.set_activity_until(agents, np.asarray(met, dtype=np.int64), t + 1)
                self.n_partner_expired += len(met)

    # ------------------------------------------------------------------ 起床
    def expiry_candidates(self, agents: Any, tick: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """満了入口の起床候補 ``(agent, condition, class_rank)``(``activity_until == tick``)。"""
        a = np.flatnonzero(np.asarray(agents.registry.activity_until) == int(tick)).astype(np.int64)
        self.n_expiry_candidates += int(a.size)
        cond = np.full(a.size, int(WakeCondition.ACTIVITY_EXPIRY), dtype=np.int8)
        cls = np.full(
            a.size, int(WAKE_CONDITION_CLASS[int(WakeCondition.ACTIVITY_EXPIRY)]), dtype=np.int64
        )
        return a, cond, cls

    def suppress_cell_block(
        self, agents: Any, tick: int, agent: np.ndarray, cond: np.ndarray, cls: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """活動中(``activity_until > tick``)の体の**場所の変化(CELL_BLOCK)**候補を落とす。"""
        if agent.size == 0:
            return agent, cond, cls
        au = np.asarray(agents.registry.activity_until)
        drop = (np.asarray(cond, dtype=np.int64) == int(WakeCondition.CELL_BLOCK)) & (
            au[np.asarray(agent, dtype=np.int64)] > int(tick)
        )
        if not bool(drop.any()):
            return agent, cond, cls
        self.n_cell_suppressed += int(np.count_nonzero(drop))
        keep = ~drop
        return agent[keep], cond[keep], cls[keep]

    # ------------------------------------------------------------------ 「あたり」
    def wander_destinations(
        self, agent_id: np.ndarray, cell: np.ndarray, tick: int
    ) -> np.ndarray:
        """「あたり」の行き先セル(半径 2 セル・run_salt の決定論)。域外は ``WANDER_BAD_TARGET``。"""
        a = np.asarray(agent_id, dtype=np.int64)
        c = np.asarray(cell, dtype=np.int64)
        out = np.full(a.size, C.WANDER_BAD_TARGET, dtype=np.int64)
        ok = (c >= 0) & (c < self._nbr_start.size - 1)
        if not bool(ok.any()):
            self.n_wander_bad += int(a.size)
            return out
        keys = wander_key_array(self.salt, int(tick), a[ok])
        cs = c[ok]
        start = self._nbr_start[cs]
        cnt = self._nbr_start[cs + 1] - start
        pick = start + (keys % np.maximum(cnt, 1).astype(np.uint64)).astype(np.int64)
        safe = np.clip(pick, 0, max(0, self._nbr_cells.size - 1))
        dest = np.where(cnt > 0, self._nbr_cells[safe] if self._nbr_cells.size else cs, cs)
        out[ok] = dest
        self.n_wander_bad += int(np.count_nonzero(~ok))
        return out

    def wander_intents(
        self, agents: Any, tick: int, exclude: np.ndarray | None = None
    ) -> "C.IntentBatch":
        """「あたり」で**着いた**体の次の行き先(Phase A のエンジン側 intent=行動は 移動)。"""
        reg = agents.registry
        t = int(tick)
        mask = (
            (np.asarray(reg.activity_kind) == int(ActivityKind.WANDER))
            & (np.asarray(reg.activity_until) > t)
            & (np.asarray(reg.activity) == int(Activity.IDLE))
            & (np.asarray(reg.transit_state) == 0)
            & (np.asarray(reg.cell) >= 0)
        )
        if exclude is not None and np.asarray(exclude).size:
            mask[np.asarray(exclude, dtype=np.int64)] = False
        ids = np.flatnonzero(mask).astype(np.int64)
        if ids.size == 0:
            return C.IntentBatch.empty()
        dest = self.wander_destinations(ids, np.asarray(reg.cell)[ids], t)
        self.n_wander_steps += int(ids.size)
        return C.IntentBatch(
            agent_id=ids,
            action_code=np.full(ids.size, C.ACT_MOVE, dtype=np.int8),
            target_id=dest.astype(np.int32),
            resource_id=np.full(ids.size, -1, dtype=np.int32),
            t_notice_ns=np.full(ids.size, C.tick_start_ns(t), dtype=np.int64),
        )

    # ------------------------------------------------------------------ 表示(B4b)
    def cell_rows(
        self, agents: Any, tick: int, top_k: int = 2
    ) -> Mapping[int, tuple[tuple[str, int], ...]]:
        """セル → 表示する活動 ``((文, 人数), …)``(上位 ``top_k``・人数降順 → 文字列順)。

        同セルの**全員**(自分を含む)で数える=同セルの 2 体で B4b がバイト一致(規約⑧)。
        """
        reg = agents.registry
        cell = np.asarray(reg.cell, dtype=np.int64)
        ids = np.flatnonzero(
            (np.asarray(reg.activity_until) > int(tick)) & (cell >= 0) & (self.text_id > 0)
        )
        if ids.size == 0:
            return {}
        width = len(self._texts) + 1
        key = cell[ids] * width + self.text_id[ids]
        uniq, counts = np.unique(key, return_counts=True)
        per_cell: dict[int, list[tuple[int, str]]] = {}
        # 逐次ループ宣言3: (セル, 文) の組の数ぶん
        for k, n in zip(uniq.tolist(), counts.tolist()):
            c, tid = divmod(int(k), width)
            per_cell.setdefault(c, []).append((-int(n), self._texts[tid]))
        out: dict[int, tuple[tuple[str, int], ...]] = {}
        for c, items in per_cell.items():
            items.sort()
            out[c] = tuple((txt, -neg) for neg, txt in items[:top_k])
        return out

    # ------------------------------------------------------------------ 監査
    def state_hash(self) -> str:
        """活動の文(体順に sha256 を連結)+「まで」の型 → sha256(checkpoint に混ぜる)。"""
        h = hashlib.sha256()
        cache = self._digest_cache
        # 逐次ループ宣言4: 体数ぶん(checkpoint のときだけ)
        for t in self.text:
            d = cache.get(t)
            if d is None:
                d = hashlib.sha256(t.encode("utf-8")).digest()
                cache[t] = d
            h.update(d)
        h.update(self.until_kind.tobytes())
        return h.hexdigest()

    def kind_distribution(self) -> dict[str, int]:
        """活動の種別ごとの**設定件数**(ラン通算)。"""
        return {k.name.lower(): int(self.kind_counts[int(k)]) for k in ActivityKind}

    def counters(self) -> dict[str, int]:
        return {
            "activity_set": int(self.n_set),
            "expiry_candidates": int(self.n_expiry_candidates),
            "cell_block_suppressed": int(self.n_cell_suppressed),
            "arrival_expired": int(self.n_arrival_expired),
            "partner_expired": int(self.n_partner_expired),
            "fail_immediate": int(self.n_fail_immediate),
            "leave_expired": int(self.n_leave_expired),
            "wander_steps": int(self.n_wander_steps),
            "wander_bad_target": int(self.n_wander_bad),
            "intent_moves": int(self.n_intent_moves),
            "distinct_texts": int(len(self._text_ids)),
        }
