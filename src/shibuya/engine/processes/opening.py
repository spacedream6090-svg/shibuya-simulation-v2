"""engine.processes.opening — 営業時間 PlanSpec と役割行動「開閉店」(D-R2-5 第1陣の 6 行目)。

正典
- 世界過程設計書 §1 **D-R2-1**: 「**営業時間**: 層2が正(店主エージェントが開け閉めする)。
  センサス由来の営業時間表は C 類でなく**計画データ**として保持し、**conf 宣言つき
  フォールバック**に使える。Phase 2 最小骨格では一時的にフォールバック側で動かす段階案を採用」。
- 同 §2: 「**『フォールバック』の正体**は PlanSpec が世界過程に変わることではなく、
  この ``executor`` の切り替え」。台帳側は ``first_batch._OPENING``(conf 0.5・
  ``AB-OPENING-EXECUTOR``)と ``PLAN_SPECS['plan.opening_hours']``。
- 行動契約書 §2.2: 「**開閉店** | 従業者(権限) | 管理権限 | **PlanSpec(営業時間)の実績確定** |
  権限なし | mechanism」。
- 世界データ構築仕様書 **D-W8**: 3 段(法規上限ハードキャップ → カテゴリ既定 → OSM 実取得)。
  W7 の ``src`` 欄の実測は ``category_default`` 1,801 / ``osm_opening_hours`` 477 /
  ``chain_default`` 59(= 被覆 22.9%)。

実装
    W7 の ``content``(曜日 × 区間[分]・``end`` は 1440 超=日跨ぎ)を **(POI × 1440) の
    開閉行列**に畳んで起動時に 1 回だけ作り、5 分刻みで
    ``world.pois.open_now``(``World.open_mask`` の上書き欄)へ書く。
    ``executor`` は行ごとに切り替わる:
      - 担当従業者が**その POI のセルに居る** → 役割行動(``executor=llm_agent``)。
        ``ActualLog`` に ``SCHEDULED``。
      - 居ない → **engine_rule フォールバック**(conf 0.5)。``ActualLog`` に ``REPLACEMENT``
        (「予定は実現したが実行主体が代替」の意味で使う=expedient)。
    これで PlanSpec の遵守率(``ActualLog`` の SCHEDULED 率)が「どれだけ層2で回せたか」を測る。

expedient(本モジュール分)
- 担当従業者の割り当て(``kind=従業者`` を POI へ決定論で丸振り)。組織台帳(W6 org)との
  対応は C5(母集団合成)待ち。
- 日跨ぎ区間の畳み方: ``end>1440`` は同じ日の ``end-1440`` へ回す(1 日周期とみなす)。
- ``REPLACEMENT`` を「代替実行主体」の意味で使う(GTFS-RT の原義は代替便)。
- 5 分刻み(正規化規約⑨と同じ刻み。契約書は開閉の評価間隔を与えていない)。
"""

from __future__ import annotations

from typing import Final

import numpy as np

from shibuya.agents.state import AgentKind, AgentState
from shibuya.engine import resolve as R
from shibuya.world.assets import ProcessAssets
from shibuya.world.processes.records import DEVIATION_CODES, DeviationVocab
from shibuya.world.state import World

__all__ = ["STEP_MINUTES", "MINUTES_PER_DAY", "OpeningProcess"]

#: 開閉を評価する刻み[分](正規化規約⑨と同じ)。
STEP_MINUTES: Final[int] = 5
MINUTES_PER_DAY: Final[int] = 1_440

_CODE_SCHEDULED: Final[int] = DEVIATION_CODES[DeviationVocab.SCHEDULED]
_CODE_REPLACEMENT: Final[int] = DEVIATION_CODES[DeviationVocab.REPLACEMENT]


def build_open_matrix(
    n_poi: int,
    plan_poi: np.ndarray,
    plan_day: np.ndarray,
    plan_start: np.ndarray,
    plan_end: np.ndarray,
    weekday: int,
) -> np.ndarray:
    """W7 の区間 → ``(n_poi, 1440)`` の開閉行列(日跨ぎは同じ日へ巻き戻す)。

    Args:
        n_poi: POI 数。
        plan_poi / plan_day / plan_start / plan_end: W7 の区間列(``day`` は 0=月)。
        weekday: 対象の曜日(0=月)。

    Returns:
        bool 行列。``[j, m]`` = POI j が分 m に営業しているか。

    Note:
        逐次ループ宣言(P4): **当日の区間数**(≈2,300)ぶんのループ 1 本。**起動時 1 回**で
        tick には比例しない(1 日 1 回の再構築でも 1,440 tick に対して O(1))。
    """
    out = np.zeros((int(n_poi), MINUTES_PER_DAY), dtype=bool)
    if plan_poi is None or plan_poi.size == 0:
        return out
    sel = np.flatnonzero(np.asarray(plan_day, dtype=np.int64) == int(weekday) % 7)
    # 逐次ループ宣言: 当日の区間ぶん
    for k in sel.tolist():
        j = int(plan_poi[k])
        s = int(plan_start[k])
        e = int(plan_end[k])
        if j < 0 or j >= n_poi or e <= s:
            continue
        s = max(0, s)
        if e <= MINUTES_PER_DAY:
            out[j, s:e] = True
        else:
            out[j, s:MINUTES_PER_DAY] = True
            out[j, 0 : min(MINUTES_PER_DAY, e - MINUTES_PER_DAY)] = True
    return out


class OpeningProcess:
    """営業時間 PlanSpec の実績確定(役割行動 + conf 宣言つきフォールバック)。

    Attributes:
        n_role_actions: 担当従業者が現場に居て実行した開閉の件数。
        n_fallback: engine_rule フォールバックで開閉した件数(**返済対象**)。
    """

    process_ids: Final[tuple[str, ...]] = ("store_opening",)
    ablation_id: Final[str] = "AB-OPENING-EXECUTOR"
    plan_spec_id: Final[str] = "plan.opening_hours"

    def __init__(
        self,
        world: World,
        agents: AgentState,
        passets: ProcessAssets,
        *,
        day_index: int = 0,
        tick_seconds: int = 60,
        actual_log=None,
    ) -> None:
        self.world = world
        self.agents = agents
        self.assets = passets
        self.day_index = int(day_index)
        self.tick_seconds = int(tick_seconds)
        self.log = actual_log
        self.n_role_actions = 0
        self.n_fallback = 0
        self.n_events = 0
        self.open_matrix = build_open_matrix(
            world.n_poi,
            passets.plan_poi,
            passets.plan_day,
            passets.plan_start,
            passets.plan_end,
            self.day_index,
        ) if passets.has_plan_spec else np.zeros((0, 0), dtype=bool)
        self.staff_of_poi = self._assign_staff()

    @property
    def active(self) -> bool:
        """W7 PlanSpec を持っているか(合成世界では False=C2 の 10:00-22:00 既定に任せる)。"""
        return self.open_matrix.size > 0

    # ------------------------------------------------------------------ 従業者の割り当て
    def _assign_staff(self) -> np.ndarray:
        """POI → 担当従業者(``kind=従業者`` を決定論で丸振り・expedient)。-1=担当なし。"""
        out = np.full(self.world.n_poi, -1, dtype=np.int64)
        if self.world.n_poi == 0:
            return out
        workers = np.flatnonzero(
            self.agents.registry.field("kind") == int(AgentKind.WORKER)
        ).astype(np.int64)
        if workers.size == 0:
            return out
        out[:] = workers[np.arange(self.world.n_poi) % workers.size]
        return out

    def has_permission(self, agent_ids, poi_ids) -> np.ndarray:
        """行動契約書 §2.2 の権限検査: 「その POI の担当従業者」かつ「同一セル」。"""
        a = np.asarray(agent_ids, dtype=np.int64)
        p = np.asarray(poi_ids, dtype=np.int64)
        ok = (a >= 0) & (a < self.agents.n) & (p >= 0) & (p < self.world.n_poi)
        out = np.zeros(a.shape, dtype=bool)
        if not ok.any():
            return out
        is_staff = self.staff_of_poi[p[ok]] == a[ok]
        kind_ok = self.agents.registry.field("kind")[a[ok]] == int(AgentKind.WORKER)
        same_cell = self.agents.registry.cell[a[ok]] == self.world.pois.cell[p[ok]]
        out[ok] = is_staff & kind_ok & same_cell
        return out

    # ------------------------------------------------------------------ 1 tick
    def step(self, tick: int) -> None:
        if not self.active:
            return
        minute = int(int(tick) * self.tick_seconds // 60) % MINUTES_PER_DAY
        if minute % STEP_MINUTES:
            return
        desired = self.open_matrix[:, minute]
        now = self.world.pois.open_now
        changed = np.flatnonzero((now < 0) | ((now > 0) != desired))
        if changed.size == 0:
            return
        staff = self.staff_of_poi[changed]
        present = np.zeros(changed.size, dtype=bool)
        ok = staff >= 0
        if ok.any():
            present[ok] = (
                self.agents.registry.cell[staff[ok]] == self.world.pois.cell[changed[ok]]
            )
        want = desired[changed].astype(np.int8)
        by_staff = changed[present]
        if by_staff.size:
            R.request_open_close(
                self.agents,
                self.world,
                self.staff_of_poi[by_staff],
                by_staff,
                desired[by_staff],
                int(tick),
                permitted=np.ones(by_staff.size, dtype=bool),
            )
            self.n_role_actions += int(by_staff.size)
        fallback = changed[~present]
        if fallback.size:
            # conf 宣言つきフォールバック(§1 末尾の台帳行 = executor=engine_rule)
            R.set_open_flags(self.world, want[~present], indices=fallback)
            self.n_fallback += int(fallback.size)
        self.n_events += int(changed.size)
        if self.log is not None:
            codes = np.where(present, _CODE_SCHEDULED, _CODE_REPLACEMENT).astype(np.int8)
            self.log.append_many(
                self.process_ids[0],
                changed.astype(np.int64),
                np.full(changed.size, int(tick), dtype=np.int64),
                codes,
            )

    # ------------------------------------------------------------------ 診断
    def counters(self) -> dict[str, float]:
        n_open = int(np.count_nonzero(self.world.pois.open_now > 0)) if self.active else 0
        return {
            "events": float(self.n_events),
            "role_actions": float(self.n_role_actions),
            "fallback": float(self.n_fallback),
            "open_now": float(n_open),
            "staffed_pois": float(int(np.count_nonzero(self.staff_of_poi >= 0))),
        }

    def summary(self) -> str:
        if not self.active:
            return "営業時間: W7 PlanSpec 無し(C2 の既定 10:00-22:00 に任せる)"
        share = self.n_fallback / max(1, self.n_events)
        return (
            f"営業時間: 開閉 {self.n_events:,} 件 / 役割行動 {self.n_role_actions:,} ・"
            f"フォールバック {self.n_fallback:,} ({share:.1%}・conf 0.5) / "
            f"営業中 {int(np.count_nonzero(self.world.pois.open_now > 0)):,} POI"
        )
