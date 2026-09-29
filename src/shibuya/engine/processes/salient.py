"""engine.processes.salient — 顕著行為(人物③)と ``p_notice`` の結線。

正典
- 知覚契約書 §3 チャネル仕様表 行「人物③」: 「**顕著な行為(倒れる・叫び・警察)** / 源=
  層2の行動 / **B4(到達分)** / 到達は ``p_notice``(§3.1 の 2 段ヒル型)」。
- 同 §3.1: 一次検出 TTPF(Sandia)+ 社会伝播(Milgram)・**打ち切り 80 m**・
  **顕著イベント上限 200/tick**・ablation **A0-A4**・追加状態 2 byte/体(M12)。
- 同 §4 段2: 「顕著行為 **上位1-2**」= ``channels.B4.salient`` の ``max_items=2``(レンダラ側)。
- 同 §6 起床条件 (i): 「所属セルの B4 ハッシュ変化(密度段階の跨ぎ・騒音段階・構造物・
  **顕著行為の到達**)」→ 気づいた個体を ``WakeCondition.CELL_BLOCK`` で起こす。
- 世界過程設計書 §7.2 ``public_service_dispatch``「出動そのものが到達チャネルを持つ」。

**80 m の近傍をセル隣接で代用する(expedient・親指示どおり)**
    §3.1 の打ち切りは 80 m(±1 リング=9 セル)。C4 では**同一セル+4 近傍**(十字)を候補に採る。
    セルは 100 m 角なので十字の外接は概ね ±100 m で、9 セル(3×3)より**狭い側**=候補を
    取りこぼす向きに保守的。厳密距離は ``p_notice`` が候補ごとに引き直す(80 m 打ち切りは
    ``notice_event`` の中で効く)ので、**過大に届くことはない**。

**B5 の「気づいたこと」行は作らない(親指示との差分・黙って埋めない)**
    親指示は「気づいた個体に B5 の個体行 `気づいたこと: <事象>` を足す」。ところが
    テンプレ v1 は **凍結**(``template_sha256 = 161fe181…``・``tests/perception/test_templates.py``
    が釘付け)で、B5 に顕著行為の行が無い。テンプレを足せば凍結ハッシュが動く=改版
    (delta+感度試験)であり、本サブの編集範囲外(``perception/templates.py`` は不可)。
    加えて契約書 §3 の人物③は届き先を **B4** と書いており、B5 ではない。
    よって C4 では:
      - **文面**は B4(セル共有=規約⑧)に載る「目につく出来事」1 行。
      - **個体差**は「気づいたか(p_notice)」= **起床するかどうか**に出る(§6 (i))。
    「気づいた個体だけに文が見える」形にするには B5 行の新設(=テンプレ改版)が要る。
    **親の判断待ち**として報告する。

expedient(本モジュール分)
- 「倒れる」の発生率 = **10,000 体あたり 3.0 件/日**(出典なし。東京消防庁の出場件数
  935,373 件/年(台帳 W3)を都人口で割ると 10,000 人・日あたり ≈ 1.8 件だが、
  救急要請と「路上で倒れる」は同義でないので、同じ桁の丸い値を置いた)。
- 事象の座標 = そのセルの代表ノード座標。
- ``task_flag``: 会話中=``TALKING``・それ以外=``FREE``(歩きスマホは C4 では立てない)。
- ``density_class``: セル密度段(``density_stage``)を 疎/中/密 の 3 値へ畳む(境界 2 と 4)。
- 夜間 = 日の入-日の出(``EnvironmentProcess`` が持つ昼夜)。無ければ 18:00-06:00。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final, Sequence

import numpy as np

from shibuya.agents.state import Activity, AgentState, WakeCondition
from shibuya.core.rng import stream
from shibuya.engine import resolve as R
from shibuya.perception import attention as AT
from shibuya.perception import p_notice as PN
from shibuya.perception.state import PerceptionState, heading_from_vector
from shibuya.world.state import World

__all__ = [
    "COLLAPSE_PER_10K_PER_DAY",
    "ABLATION_IDS",
    "ablation_name",
    "check_d50_scale",
    "SalientEvent",
    "SalientProcess",
]

#: 「倒れる」の発生率[件/10,000体/日](expedient)。
COLLAPSE_PER_10K_PER_DAY: Final[float] = 3.0
#: ablation の id(``AB-PNOTICE-A0`` … ``A4``。A4=完成形=既定)。
ABLATION_IDS: Final[tuple[str, ...]] = tuple(f"AB-PNOTICE-A{k}" for k in range(5))

#: 事象クラス別の d50[m](§3.1 は既定 40 m。クラス別の値は空欄=expedient)。
D50_BY_KIND: Final[dict[str, float]] = {
    "collapse": 40.0,
    "police": 45.0,
    "broadcast": 60.0,
}
#: 事象クラス別の文言(命令文なし・世界内テキスト)。
TEXT_BY_KIND: Final[dict[str, str]] = {
    "collapse": "人が倒れている",
    "police": "救急・警察の隊が到着している",
    "broadcast": "",  # PressProcess が素性タグつきの本文を作る
}
#: 顕著性順位づけ(§4 段2)の素材(サイズ[m]・動き・逸脱度・コントラスト)=expedient。
SALIENCY_BY_KIND: Final[dict[str, tuple[float, float, float, float]]] = {
    "collapse": (1.8, 0.2, 0.9, 0.6),
    "police": (2.5, 0.8, 0.7, 0.8),
    "broadcast": (3.0, 0.1, 0.4, 0.5),
}


@dataclass
class SalientEvent:
    """1 件の顕著行為。"""

    kind: str
    cell: int
    xy: tuple[float, float]
    text: str
    moving: bool = False
    #: 気づいた個体(``p_notice`` の結果)。
    noticed: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=np.int64))


class SalientProcess:
    """顕著行為の生成・``p_notice`` による到達判定・B4 行の組み立て。

    Attributes:
        events: この tick の事象。
        cell_lines: ``{セル: (行, …)}``(``Renderer.prepare_tick(salient_events=…)`` へ)。
        noticed_agents: この tick に気づいた個体(起床候補 (i) の素)。
    """

    process_ids: Final[tuple[str, ...]] = ()  # 台帳行は事象を出す各過程が持つ
    ablation_id: Final[str] = ABLATION_IDS[4]

    def __init__(
        self,
        world: World,
        agents: AgentState,
        *,
        master_seed: int | str = 1,
        day_index: int = 0,
        tick_seconds: int = 60,
        dispatch=None,
        press=None,
        environment=None,
        ablation: PN.Ablation | int | str = PN.Ablation.A4_SOCIAL,
        rate_per_10k_per_day: float | None = None,
        d50_scale: float = 1.0,
    ) -> None:
        self.world = world
        self.agents = agents
        self.tick_seconds = int(tick_seconds)
        self.master_seed = master_seed
        self.day_index = int(day_index)
        self.dispatch = dispatch
        self.press = press
        self.environment = environment
        self.ablation = _as_ablation(ablation)
        # ablation ②(知覚契約書 §8 第1陣 ②「p_notice の d50 を 0.5×/2×」)。既定 1.0 =
        # §3.1 の値そのもの(``PNoticeParams`` の既定と ``D50_BY_KIND`` の表)=バイト不変。
        # 打ち切り ``cutoff_m``(80 m)は**動かさない**(§3.1 の別の expedient なので
        # この腕では固定。2.0× のとき d50=80 m=打ち切りと同値になる点は報告に書く)。
        self.d50_scale = check_d50_scale(d50_scale)
        self.params = PN.PNoticeParams(
            ablation=self.ablation, d50_m=PN.D50_DEFAULT_M * self.d50_scale
        )
        #: 事象クラス別 d50[m]の**実効表**(既定 = ``D50_BY_KIND`` そのもの)。
        self.d50_by_kind: dict[str, float] = (
            dict(D50_BY_KIND)
            if self.d50_scale == 1.0
            else {k: v * self.d50_scale for k, v in D50_BY_KIND.items()}
        )
        self.budget = PN.EventBudget()
        self.pstate = PerceptionState(agents.n)
        self.pstate.freeze()
        self.rate = float(
            COLLAPSE_PER_10K_PER_DAY if rate_per_10k_per_day is None
            else rate_per_10k_per_day
        )
        self.rng = stream(master_seed, "world.salient", int(day_index))
        self.events: list[SalientEvent] = []
        self.cell_lines: dict[int, tuple[str, ...]] = {}
        self.noticed_agents = np.zeros(0, dtype=np.int64)
        #: D-113 ②(第267): 体ごとに「顕著行為の行が自分のセルの B4 に載った最後の tick」(−1=未)。
        #: 通報の前提「当該事象を知覚済み」の検査に使う。B4 は**セル単位**の行なので、事象の
        #: セルに居た全員(=観測に行が出た全員)を知覚済みとする(``p_notice`` は起床の到達判定)。
        self.event_seen_tick = np.full(agents.n, -1, dtype=np.int32)
        self.n_events = 0
        self.n_noticed = 0
        self.n_collapse = 0
        self.n_over_cap = 0
        self.n_broadcast_lines = 0
        self._neighbours = _cross_neighbours(world)
        self._cell_index_tick = -1
        self._order = np.zeros(0, dtype=np.int64)
        self._start = np.zeros(world.n_cells + 1, dtype=np.int64)

    @property
    def active(self) -> bool:
        return self.world.n_cells > 0 and self.agents.n > 0

    # ------------------------------------------------------------------ 1 tick
    def step(self, tick: int) -> None:
        self.events = []
        self.cell_lines = {}
        self.noticed_agents = np.zeros(0, dtype=np.int64)
        if not self.active:
            return
        self.budget.start_tick(int(tick))

        raw: list[SalientEvent] = []
        raw += self._collapse_events(int(tick))
        raw += self._dispatch_events(int(tick))
        # 報道・公式発信は**人物③ではない**(放送=構成上その場の全員へ届く)。
        # ``p_notice``(顕著行為の到達)も 200/tick の顕著イベント予算も通さず、
        # B4 の行としてだけ載せる。個体差は注意ゲート段2(上位1-2)で付く。
        # 起床は「セルの B4 ハッシュが変わる」= 起床条件 (i) が自然に拾う。
        broadcasts = self._broadcast_events(int(tick))
        self.events += broadcasts
        self.n_broadcast_lines += len(broadcasts)
        if not raw:
            self.cell_lines = self._build_cell_lines()
            return

        # 候補索引と M12 の 2 byte/体は**事象がある tick だけ**貼り直す
        # (毎 tick 5,000 体ぶんの向き計算をすると 0.45 s/日を無駄に使う。
        #  事象の直前に作るので値は同じ=描画・判定とずれない)。
        self._index_cells()
        self._update_notice_state()

        night = self._is_night(int(tick))
        density_class = _density_class(self.world)
        heading = np.asarray(self.pstate.heading)
        task = np.asarray(self.pstate.task_flag)
        xy = np.asarray(self.agents.registry.xy, dtype=np.float64)
        already = np.zeros(self.agents.n, dtype=bool)
        noticed_any: list[np.ndarray] = []

        # 逐次ループ宣言(P4): **事象数**ぶん(``EventBudget`` が 200/tick で切る)。
        # 個体数には比例しない(候補の抽出も判定もベクトル)。
        for ev_id, ev in enumerate(raw):
            if not self.budget.admit(int(tick)):
                self.n_over_cap += 1
                continue
            cand = self._candidates(ev.cell)
            self.events.append(ev)
            self.n_events += 1
            self._mark_seen(int(ev.cell), int(tick))
            if cand.size == 0:
                continue
            res = PN.notice_event(
                event_xy=ev.xy,
                agent_xy=xy[cand],
                heading_u8=heading[cand],
                task_flag=task[cand],
                density_class=density_class[np.clip(
                    np.asarray(self.agents.registry.cell, dtype=np.int64)[cand], 0,
                    self.world.n_cells - 1,
                )],
                night=night,
                moving=ev.moving,
                d50_m=self.d50_by_kind.get(ev.kind),
                seed=self.master_seed,
                event_id=ev_id,
                tick=int(tick),
                params=self.params,
                already_noticed=already[cand],
                counters=self.budget.counters,
            )
            got = cand[res.noticed_ids()]
            ev.noticed = got
            if got.size:
                already[got] = True
                noticed_any.append(got)

        if noticed_any:
            self.noticed_agents = np.unique(np.concatenate(noticed_any))
            self.n_noticed += int(self.noticed_agents.size)
        self.cell_lines = self._build_cell_lines()

    # ------------------------------------------------------------------ 知覚済み(D-113 ②)
    def _mark_seen(self, cell: int, tick: int) -> None:
        """事象のセルに居る全員の ``event_seen_tick`` を ``tick`` に(B4 の行が出た体)。

        ``_index_cells`` は事象のある tick の先頭で貼り直されているので同じ並びを使う。
        逐次ループ宣言(P4): なし(セル 1 つのスライス代入)。
        """
        if not (0 <= int(cell) < self.world.n_cells):
            return
        occ = self._order[self._start[int(cell)] : self._start[int(cell) + 1]]
        if occ.size:
            self.event_seen_tick[occ] = np.int32(tick)

    def event_seen_within(self, agent_ids: np.ndarray, tick: int, window: int) -> np.ndarray:
        """``agent_ids`` が直近 ``window`` tick 以内に事象の行を見たか(bool 配列)。"""
        seen = self.event_seen_tick[np.asarray(agent_ids, dtype=np.int64)].astype(np.int64)
        return (seen >= 0) & (int(tick) - seen <= int(window))

    # ------------------------------------------------------------------ 起床候補
    def wake_candidates(self, tick: int):
        """起床条件 (i)「顕著行為の到達」(``WakeCondition.CELL_BLOCK``)。

        Returns:
            ``(agent_id, condition, class_rank)`` の 3 本(``engine.run`` が
            アービタへ渡す=**呼は必ず予算の中を通る**)。
        """
        a = self.noticed_agents
        if a.size == 0:
            return (
                np.empty(0, dtype=np.int64),
                np.empty(0, dtype=np.int8),
                np.empty(0, dtype=np.int64),
            )
        from shibuya.agents.state import WAKE_CONDITION_CLASS

        cond = int(WakeCondition.CELL_BLOCK)
        return (
            a.astype(np.int64),
            np.full(a.size, cond, dtype=np.int8),
            np.full(a.size, int(WAKE_CONDITION_CLASS[cond]), dtype=np.int64),
        )

    # ------------------------------------------------------------------ 事象の源
    def _collapse_events(self, tick: int) -> list[SalientEvent]:
        per_tick = (
            self.rate * (self.agents.n / 10_000.0) / (86_400.0 / max(1, self.tick_seconds))
        )
        n = int(self.rng.poisson(max(0.0, per_tick)))
        if n <= 0:
            return []
        inside = np.flatnonzero(np.asarray(self.agents.registry.cell) >= 0)
        if inside.size == 0:
            return []
        who = self.rng.choice(inside, size=min(n, inside.size), replace=False)
        out: list[SalientEvent] = []
        for a in np.atleast_1d(who):  # 逐次: 事象数ぶん(≈0-1/tick)
            cell = int(self.agents.registry.cell[int(a)])
            xy = np.asarray(self.agents.registry.xy, dtype=np.float64)[int(a)]
            out.append(
                SalientEvent("collapse", cell, (float(xy[0]), float(xy[1])),
                             TEXT_BY_KIND["collapse"])
            )
            self.n_collapse += 1
            if self.dispatch is not None:
                self.dispatch.request(tick, cell, (float(xy[0]), float(xy[1])))
        return out

    def _dispatch_events(self, tick: int) -> list[SalientEvent]:
        if self.dispatch is None:
            return []
        return [
            SalientEvent("police", int(cell), (float(x), float(y)),
                         TEXT_BY_KIND["police"], moving=True)
            for cell, x, y in self.dispatch.arrivals(tick)
        ]

    def _broadcast_events(self, tick: int) -> list[SalientEvent]:
        if self.press is None or not self.press.due(tick):
            return []
        rep = np.asarray(self.world.assets.cell_rep_node, dtype=np.int64)
        node_xy = np.asarray(self.world.assets.node_xy, dtype=np.float64)
        # 在席者のいるセルだけに出す(無人セルへ出しても誰にも届かず、
        # ``EventBudget`` の 200/tick を食い潰すだけ=expedient の実装上の絞り込み)
        live = np.flatnonzero(np.asarray(self.world.cells.density) > 0)
        out: list[SalientEvent] = []
        for c in live.tolist():  # 逐次: 在席セル数ぶん・1 日 3 回だけ
            j = int(rep[c]) if 0 <= c < rep.size else 0
            xy = node_xy[max(0, j)]
            out.append(
                SalientEvent("broadcast", int(c), (float(xy[0]), float(xy[1])), self.press.line)
            )
        return out

    # ------------------------------------------------------------------ B4 行
    def _build_cell_lines(self) -> dict[int, tuple[str, ...]]:
        """セル → B4「目につく出来事」の行(§4 段2 で上位 ``BUDGET_SALIENT`` へ絞る)。"""
        by_cell: dict[int, list[AT.SalientItem]] = {}
        for k, ev in enumerate(self.events):
            if not ev.text:
                continue
            size, motion, dev, contrast = SALIENCY_BY_KIND.get(ev.kind, (1.0, 0.0, 0.0, 0.5))
            by_cell.setdefault(int(ev.cell), []).append(
                AT.SalientItem(
                    item_id=f"{ev.kind}:{k:04d}",
                    text=ev.text,
                    size_m=size,
                    distance_m=25.0,  # セル代表距離(expedient)
                    contrast=contrast,
                    motion=motion,
                    deviance=dev,
                )
            )
        out: dict[int, tuple[str, ...]] = {}
        for cell, items in by_cell.items():  # 逐次: 事象のあるセル数ぶん
            ranked, _ = AT.rank_by_saliency(items)
            kept = AT.apply_budget(ranked, AT.BUDGET_SALIENT)
            if kept:
                out[cell] = tuple(it.text for it in kept)
        return out

    # ------------------------------------------------------------------ 補助
    def _index_cells(self) -> None:
        cell = np.asarray(self.agents.registry.cell, dtype=np.int64)
        n = self.world.n_cells
        valid = (cell >= 0) & (cell < n)
        order = np.argsort(np.where(valid, cell, n), kind="stable")
        sorted_cell = np.where(valid, cell, n)[order]
        self._order = order
        self._start = np.searchsorted(sorted_cell, np.arange(n + 1), side="left")

    def _candidates(self, cell: int) -> np.ndarray:
        """同一セル+4 近傍の在席者(80 m 打ち切りの候補集合・expedient)。"""
        if not (0 <= int(cell) < self.world.n_cells):
            return np.zeros(0, dtype=np.int64)
        cells = [int(cell)] + [int(c) for c in self._neighbours[int(cell)] if c >= 0]
        parts = [self._order[self._start[c] : self._start[c + 1]] for c in cells]
        parts = [p for p in parts if p.size]
        return np.concatenate(parts) if parts else np.zeros(0, dtype=np.int64)

    def _update_notice_state(self) -> None:
        """M12 の 2 byte/体(向き・課題従事)を貼り直す(**書き込みは resolve 経由**)。"""
        r = self.agents.registry
        node_xy = np.asarray(self.world.assets.node_xy, dtype=np.float64)
        tgt = np.asarray(r.target_node, dtype=np.int64)
        xy = np.asarray(r.xy, dtype=np.float64)
        dst = node_xy[np.maximum(tgt, 0)]
        dx = np.where(tgt >= 0, dst[:, 0] - xy[:, 0], 1.0)
        dy = np.where(tgt >= 0, dst[:, 1] - xy[:, 1], 0.0)
        heading = heading_from_vector(dx, dy)
        act = np.asarray(r.activity)
        task = np.where(
            act == int(Activity.CONVERSING), int(PN.TaskLoad.TALKING), int(PN.TaskLoad.FREE)
        ).astype(np.uint8)
        R.set_notice_state(self.pstate, heading, task)

    def _is_night(self, tick: int) -> bool:
        env = self.environment
        if env is not None and hasattr(env, "is_night"):
            try:
                return bool(env.is_night(int(tick)))
            except Exception:  # pragma: no cover - 環境過程が休んでいるとき
                pass
        minute = int(int(tick) * self.tick_seconds // 60) % 1_440
        return minute >= 18 * 60 or minute < 6 * 60

    # ------------------------------------------------------------------ 診断
    def counters(self) -> dict[str, float]:
        c = self.budget.counters.as_dict()
        return {
            "events": float(self.n_events),
            "collapse": float(self.n_collapse),
            "noticed": float(self.n_noticed),
            "over_cap": float(self.n_over_cap),
            "candidates": float(c["candidates"]),
            "noticed_primary": float(c["noticed_primary"]),
            "noticed_social": float(c["noticed_social"]),
            "broadcast_lines": float(self.n_broadcast_lines),
            "ablation": float(int(self.ablation)),
            "d50_scale": float(self.d50_scale),
        }

    def summary(self) -> str:
        return (
            f"顕著行為: 事象 {self.n_events:,}(倒れる {self.n_collapse:,}・上限超 "
            f"{self.n_over_cap:,}) / 気づいた延べ {self.n_noticed:,} / 放送行 "
            f"{self.n_broadcast_lines:,} / "
            f"ablation {self.ablation.name}(80m 近傍=同セル+4近傍=expedient)"
            + (f" / d50 ×{self.d50_scale:g}" if self.d50_scale != 1.0 else "")
        )


# ---------------------------------------------------------------- モジュール関数
def ablation_name(value: PN.Ablation | int | str) -> str:
    """``p_notice`` の ablation → ``"A0"``…``"A4"``(manifest の同定欄・§3.1)。

    ``PN.Ablation``・``0``-``4``・``"A2"``・``"AB-PNOTICE-A2"`` のどれでも受ける。
    """
    return f"A{int(_as_ablation(value))}"


def check_d50_scale(value: float) -> float:
    """``d50_scale`` の検査(ablation ②)。正の有限値だけ許す。"""
    v = float(value)
    if not np.isfinite(v) or v <= 0.0:
        raise ValueError(f"d50_scale は正の有限値(いま {value!r})")
    return v


def _as_ablation(value: PN.Ablation | int | str) -> PN.Ablation:
    if isinstance(value, PN.Ablation):
        return value
    if isinstance(value, str):
        name = value.strip().upper()
        if name.startswith("AB-PNOTICE-"):
            name = name[len("AB-PNOTICE-") :]
        if name and name[0] == "A" and name[1:].isdigit():
            return PN.Ablation(int(name[1:]))
        raise ValueError(f"未知の p_notice ablation: {value!r}(A0-A4 / AB-PNOTICE-A0-A4)")
    return PN.Ablation(int(value))


def _density_class(world: World) -> np.ndarray:
    """セル密度段(``World.density_stage``)→ ``p_notice`` の 疎/中/密(境界 2/4=expedient)。"""
    stage = np.asarray(world.cells.density_stage, dtype=np.int64)
    return np.clip(np.searchsorted(np.asarray([2, 4]), stage, side="right"), 0, 2).astype(
        np.int64
    )


def _cross_neighbours(world: World) -> np.ndarray:
    """セル → 4 近傍(十字)の索引 ``(n_cells, 4)``。無い方向は -1。

    Note:
        逐次ループ宣言(P4): 方向数(4)ぶんのループ 1 本。**起動時 1 回**。
    """
    n = world.n_cells
    out = np.full((n, 4), -1, dtype=np.int64)
    if n == 0:
        return out
    ix = np.asarray(world.assets.cell_ix, dtype=np.int64)
    iy = np.asarray(world.assets.cell_iy, dtype=np.int64)
    band = np.asarray(world.assets.cell_band, dtype=np.int64)
    key = (ix + 1_000_000) * 8_000_000 + (iy + 1_000_000) * 4 + (band + 1)
    order = np.argsort(key, kind="stable")
    sorted_key = key[order]
    for d, (dx, dy) in enumerate(((1, 0), (-1, 0), (0, 1), (0, -1))):
        want = (ix + dx + 1_000_000) * 8_000_000 + (iy + dy + 1_000_000) * 4 + (band + 1)
        pos = np.clip(np.searchsorted(sorted_key, want), 0, sorted_key.size - 1)
        hit = sorted_key[pos] == want
        out[hit, d] = order[pos][hit]
    return out


def build_salient_feed(events: Sequence[SalientEvent]) -> dict[int, tuple[str, ...]]:
    """``SalientEvent`` の列 → ``Renderer.prepare_tick(salient_events=…)`` の形。"""
    out: dict[int, list[str]] = {}
    for ev in events:
        if ev.text:
            out.setdefault(int(ev.cell), []).append(ev.text)
    return {k: tuple(v) for k, v in out.items()}
