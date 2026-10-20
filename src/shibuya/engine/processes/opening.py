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

〔第 1 期 1-5〕担当従業者の表 ``staff_of_poi`` は権利台帳(``engine.rights``)の ``employ`` の行(体 → 店)から読む。
台帳はこの過程が持ち(``rights``・最初の中身は ``engine.rights.initial.build_initial``)、再開では戻した SoA から作り
直す。開閉店を権利の無い体が行っても止めない(``resolve.request_open_close`` が権利の無い行を返し、この過程が出来事の
記録へ ``行為:許可のない行動`` を書いて数える=CP3・記録の口は ActualLog の ``event_sink`` から引く)。

expedient(本モジュール分)
- 担当従業者の割り当て(``kind=従業者`` を POI へ決定論で丸振り)。規則は権利台帳の組み立て
  (``engine.rights.initial``)へ移し、ここは台帳の ``employ`` の行から読む。組織台帳(W6 org)との対応は無い。
- 日跨ぎ区間の畳み方: ``end>1440`` は同じ日の ``end-1440`` へ回す(1 日周期とみなす)。
- ``REPLACEMENT`` を「代替実行主体」の意味で使う(GTFS-RT の原義は代替便)。
- 5 分刻み(正規化規約⑨と同じ刻み。契約書は開閉の評価間隔を与えていない)。
"""

from __future__ import annotations

from typing import Final

import numpy as np

from shibuya.agents.state import AgentKind, AgentState
from shibuya.core.types import t_sim_ns
from shibuya.engine import resolve as R
from shibuya.engine.calendar import OPENING_ROW_PH
from shibuya.engine.rights import initial as _RI
from shibuya.engine.rights import record as _RR
from shibuya.engine.rights.ledger import AGENT, EMPLOY, STORE
from shibuya.world.assets import ProcessAssets
from shibuya.world.processes.records import DEVIATION_CODES, DeviationVocab
from shibuya.world.state import World
from shibuya.core.time_consts import MINUTES_PER_DAY, SECONDS_PER_MINUTE

__all__ = ["STEP_MINUTES", "MINUTES_PER_DAY", "OpeningProcess"]

#: 開閉を評価する刻み[分](正規化規約⑨と同じ)。
STEP_MINUTES: Final[int] = 5

_CODE_SCHEDULED: Final[int] = DEVIATION_CODES[DeviationVocab.SCHEDULED]
_CODE_REPLACEMENT: Final[int] = DEVIATION_CODES[DeviationVocab.REPLACEMENT]


#: 〔第330・10e E3〕W7 の祝日の行(暦の口の ``opening_row`` が祝日に返す値)。
PH_ROW: Final[int] = OPENING_ROW_PH
#: 祝日の行の無い店が祝日に使う行(日曜=10a の「祝日は土休扱い」・expedient・未リサーチ)。
PH_FALLBACK_ROW: Final[int] = 6


def rows_of_day(plan_poi: np.ndarray, plan_day: np.ndarray, row: int,
                ph_poi: np.ndarray | None = None) -> np.ndarray:
    """その日の行(曜日 0〜6・祝日 ``PH_ROW``)に当たる W7 の区間の真偽の列。

    〔第330・10e E3〕祝日の行は、W7 に祝日の規則(``PH``)を持つ店(``ph_poi``)はその行・持たない店は日曜の行。
    曜日 0〜6 は今と同じ(``plan_day == row % 7``)。
    """
    day = np.asarray(plan_day, dtype=np.int64)
    if int(row) != PH_ROW:
        return day == int(row) % 7
    poi = np.asarray(plan_poi, dtype=np.int64)
    has_ph = np.isin(poi, np.asarray(ph_poi if ph_poi is not None else (), dtype=np.int64))
    return np.where(has_ph, day == PH_ROW, day == PH_FALLBACK_ROW)


def build_open_matrix(
    n_poi: int,
    plan_poi: np.ndarray,
    plan_day: np.ndarray,
    plan_start: np.ndarray,
    plan_end: np.ndarray,
    weekday: int,
    ph_poi: np.ndarray | None = None,
) -> np.ndarray:
    """W7 の区間 → ``(n_poi, 1440)`` の開閉行列(日跨ぎは同じ日へ巻き戻す)。

    Args:
        n_poi: POI 数。
        plan_poi / plan_day / plan_start / plan_end: W7 の区間列(``day`` は 0=月・7=祝日の行)。
        weekday: 対象の曜日(0=月)。〔第330〕``PH_ROW``(7)は祝日の行(``rows_of_day``)。
        ph_poi: 祝日の規則を持つ店(``ProcessAssets.plan_ph_poi``)。

    Returns:
        bool 行列。``[j, m]`` = POI j が分 m に営業しているか。

    Note:
        逐次ループ宣言(P4): **当日の区間数**(≈2,300)ぶんのループ 1 本。**起動時 1 回**で
        tick には比例しない(1 日 1 回の再構築でも 1,440 tick に対して O(1))。
    """
    out = np.zeros((int(n_poi), MINUTES_PER_DAY), dtype=bool)
    if plan_poi is None or plan_poi.size == 0:
        return out
    sel = np.flatnonzero(rows_of_day(plan_poi, plan_day, int(weekday), ph_poi))
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
        rights: 〔1-5〕権利台帳(``engine.rights.ledger.Rights``・SoA の種別・W16 の ``org_id``・POI の数から作る導出)。
        n_unauthorized: 〔1-5〕権利の無い体が開閉した件数(止めずに出来事の記録へ書いた行=計器・状態台帳の O73)。
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
        org_of_agent=None,
        initial_rights=None,
    ) -> None:
        self.world = world
        self.agents = agents
        self.assets = passets
        #: 〔1-5〕体 → W16 の ``org_id``(権利台帳の (a) 雇用の行の材料・``None``=母集団の無いラン)。
        self.org_of_agent = None if org_of_agent is None else np.asarray(org_of_agent, dtype=np.int64).copy()
        #: 〔第 4 期 4-3 段 10〕差し替えの世界の初期の行(``engine.rights.initial.InitialRows``=店の担当と住まい・読むだけ)。
        #: ``None``=今の口(担当は丸振り・住まいは 0 行)。
        self.initial_rights = initial_rights
        self.n_unauthorized = 0
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
            passets.plan_ph_poi,
        ) if passets.has_plan_spec else np.zeros((0, 0), dtype=bool)
        self.rights = self._build_rights()
        self.staff_of_poi = self._staff_from_rights()

    @property
    def active(self) -> bool:
        """W7 PlanSpec を持っているか(合成世界では False=C2 の 10:00-22:00 既定に任せる)。"""
        return self.open_matrix.size > 0

    # ------------------------------------------------------------------ 従業者の割り当て(1-5: 権利台帳から読む)
    def _build_rights(self):
        """〔1-5〕権利台帳の最初の中身を今の SoA の種別から作る(``engine.rights.initial.build_initial``)。"""
        return _RI.build_initial(self.agents.registry.field("kind"), self.world.n_poi, self.org_of_agent,
                                 rows=self.initial_rights)

    def _staff_from_rights(self) -> np.ndarray:
        """〔1-5〕POI → 担当従業者を権利台帳の ``employ`` の行(体 → 店)から読む。-1=担当なし。

        台帳の行は開始前から終わりなし(ラン中に権利を変える行動は無い=2-1 の段)なので、時刻 0 で読む。
        """
        return _RI.staff_of_poi(self.rights, self.world.n_poi, 0)

    def _record_unauthorized(self, agent_ids, poi_ids) -> None:
        """〔1-5〕権利の無い体の開閉(旗は確定した=行動は起きた)を出来事の記録へ書いて数える。"""
        self.n_unauthorized += _RR.record_unauthorized(_RR.events_of(self.log), agent_ids, poi_ids)

    def unauthorized_tally(self) -> dict[str, int]:
        """〔1-5〕manifest の ``rights.unauthorized`` の開閉の分(この過程の持ち物の数え)。"""
        return {"open_close": int(self.n_unauthorized)}

    def relay_day(self, weekday: int) -> None:
        """10d(親の答え 5): 日の頭でその日の曜日の行(W7)の開閉行列を作り直す(暦の口の ``table_weekday(日)``)。"""
        self.day_index = int(weekday)
        if self.open_matrix.size:
            self.open_matrix = build_open_matrix(
                self.world.n_poi,
                self.assets.plan_poi,
                self.assets.plan_day,
                self.assets.plan_start,
                self.assets.plan_end,
                self.day_index,
                self.assets.plan_ph_poi,
            )

    def set_plan_rows(self, pois, minutes) -> None:
        """〔第 3 期 3-3〕申込書の決定(L1 営業時間の変更・休業)=対象の店の営業時間の表の行を差し替える。

        呼ぶのは申込書の効かせる口(``engine.experiment.apply``)だけ。開け閉めそのものは ``step`` が担当の従業者に行わせる
        (居なければ今の conf 宣言つきのつなぎ)=エンジンは決定を表に入れるだけ(決定 10-12 §1-1 CP6)。``minutes`` は 1 日の
        分の真偽の列。表は日の頭で W7 から張り直す(``relay_day``)ので、口が日ごとに当て直す。
        """
        if self.open_matrix.size:
            self.open_matrix[np.asarray(pois, dtype=np.int64), :] = np.asarray(minutes, dtype=bool)

    def restore_plan_rows(self, pois) -> None:
        """〔第 3 期 3-3〕対象の店の行をその日の W7 の行に戻す(申込書の終わり・``engine.experiment.apply`` だけが呼ぶ)。"""
        if not self.open_matrix.size:
            return
        p = np.asarray(pois, dtype=np.int64)
        a = self.assets
        sel = np.isin(np.asarray(a.plan_poi), p)
        fresh = build_open_matrix(self.world.n_poi, np.asarray(a.plan_poi)[sel], np.asarray(a.plan_day)[sel],
                                  np.asarray(a.plan_start)[sel], np.asarray(a.plan_end)[sel], self.day_index,
                                  a.plan_ph_poi)
        self.open_matrix[p, :] = fresh[p, :]

    def rebuild_derived(self) -> None:
        """10d: SoA の ``kind`` から作る担当従業者の表を今の SoA から作り直す(再開で SoA を戻した後)。

        配列は差し替えずに中身を書き換える(補充の過程が同じ配列を持つ)。〔1-5〕権利台帳も今の SoA から作り直し、
        表は台帳から読む。
        """
        self.rights = self._build_rights()
        got = self._staff_from_rights()
        if self.staff_of_poi.shape == got.shape:
            self.staff_of_poi[...] = got
        else:
            self.staff_of_poi = got

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
        minute = int(int(tick) * self.tick_seconds // SECONDS_PER_MINUTE) % MINUTES_PER_DAY
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
            actors = self.staff_of_poi[by_staff]
            R.request_open_close(
                self.agents,
                self.world,
                actors,
                by_staff,
                desired[by_staff],
                int(tick),
                # 1-5: 権利は権利台帳に聞く(担当の表は台帳から読んだ=全部 真)。無い行も止めずに記録の口へ
                permitted=self.rights.holds_each(
                    actors, by_staff, kind=EMPLOY, holder_kind=AGENT, object_kind=STORE,
                    t_ns=t_sim_ns(int(tick), tick_seconds=self.tick_seconds)),
                on_unauthorized=self._record_unauthorized,
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
