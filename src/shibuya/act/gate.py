"""act.gate — 割る段で ``engine/resolve.py`` を割った割り先(全ファイルの表 §4・名の表は
``tools/pkgmove/map.toml`` の割る行)。

中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の
方針は、主な割り先 ``act/apply.py`` に残した元の docstring を読むこと。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import numpy as np
from shibuya.foundation.vocab.agent_codes import ResultCode
from shibuya.world.model.agent_table import (
    AgentState,
)
from shibuya.world.model.geometry import EdgeGeometry
from shibuya.foundation.ports.ledger import LedgerBundle

__all__ = [
    "ResolveOutcome",
]


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
    #: 顕著行為(``engine.processes.salient.SalientProcess``)。``None`` なら通報は記録のみ(C2 互換)。
    salient: object | None = None
    #: D-113 ②: 通報の前提検査の切替口(False=従来どおり必ず成功=第266 以前の挙動)。
    report_precondition: bool = True
    #: 通報が前提を満たして成立した件数 / 知覚済みの事象が無く失敗した件数。
    n_report_ok: int = 0
    n_report_no_event: int = 0
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
    #: D-113 ③: 満席の列から席へ入れた件数 / 閉店で列を解散した件数。
    n_served_from_queue: int = 0
    n_queue_closed: int = 0
    #: D-113 ③: 列を捌くかの切替口(False=第267 以前の挙動=誰も捌かない)。
    queue_service: bool = True
    #: ホテル客室在庫(``engine.processes.civic.HotelProcess``)。``None`` なら就寝は自宅のみ。
    hotel: object | None = None
    #: ホテルで就寝した件数(§7.2 ホテル客室在庫)。
    n_hotel_sleep: int = 0
    #: **就寝地へ着いて寝た**件数(D-62 (a) の意図保持ぶん。就寝境界で即座に寝た件数は
    #: ``begin_planned_sleep`` の戻り値で数える=あちらは ``apply`` の外で走る)。
    n_planned_sleep: int = 0
    #: **語彙 v2「食事」が成立した件数**(v1 のランでは常に 0)。
    n_meals: int = 0
    #: 食事で店舗へ移った金額[円](``revenue_delta`` の内数)。
    meal_yen: int = 0
    #: 同じ店への買い手が棚の合計を超えて、支払いの前に OUT_OF_STOCK にした件数(第288 の欠陥修正)。
    n_buy_over_stock: int = 0
    #: 4 段目(M13 訪問): 購入/食事の**成立した行**(体, POI)を控えるか(``--familiarity on`` だけ)。
    #: 控えるだけで世界は変えない=既定 False では 1 行も通らない。
    track_visits: bool = False
    visit_agents: list = field(default_factory=list)
    visit_pois: list = field(default_factory=list)
    #: 6 段目 6a(記憶の記録): エンジン継続で**着いた**体を控えるか(``--memory on`` だけ)。
    #: 控えるだけで世界は変えない=既定 False では 1 行も通らない。
    track_events: bool = False
    arrived_agents: list = field(default_factory=list)
    #: 5 段目 5a(D-118): エネルギー収支の層(``engine.energy.EnergyLayer``)。``None``=空腹 v1
    #: (購入/食事で −4)=**1 分岐も通らない**。渡すと食事=時間帯の比 × EER・軽食/飲料=比 × EER。
    energy: Any = None
    #: 段 2b: 移動の失敗の内訳(対象不正=行き先が解決できない / 経路なし)。
    n_move_bad_target: int = 0
    n_move_unreachable: int = 0
    #: **C9 辺上の連続位置**(``engine.geometry.EdgeGeometry``)。``None``=現行の 1 tick=1 ノード。
    geometry: EdgeGeometry | None = None
    #: この tick の**ホップ反復**の回数(edge モードの P4 実測=逐次ループの実際の深さ。
    #: 上限は ``geometry.MAX_HOPS_PER_TICK``)。
    n_hops: int = 0
    #: 密度が Kladek の詰め込み密度(5.4 人/m²)以上で**歩けなかった**体の延べ数
    #: (edge モードの診断・通常は 0。絶対吸収状態の監視点)。
    n_jammed: int = 0
    # ---- C9b 対象と注意(G3/G4/G7)。既定(``None``/False)では 1 分岐も通らない ----
    #: この tick に LLM が言った**焦点の要求**(``(n_agents,)`` int64・``-1``=なし)。
    #: ``engine.run`` が組んで渡す**読むだけ**の配列。``agents.focus_target`` と同じ符号。
    focus_request: np.ndarray | None = None
    #: 会話の距離判定を使うか(G7)。``True``= ``TALK_OPEN_METERS`` の実距離・
    #: ``False``(既定)= 同一セル代理(C3 からの expedient)。
    talk_by_distance: bool = False
    #: 「近づく」が立った件数(移動の対象が人/オブジェクトだった件数)。
    n_approach: int = 0
    #: 「近づく」が対象に届いた件数(到達 ≤ ``APPROACH_DONE_M``)。
    n_approach_done: int = 0
    #: 「近づく」が着いたのに対象が居なかった件数(``TARGET_GONE``)。
    n_target_gone: int = 0
    #: 注意の焦点を**取得**した件数(G4)。
    n_focus: int = 0
    #: 注意の焦点が**消えた**件数(寿命切れ + 喪失距離超過)。
    n_focus_lost: int = 0
    #: **実距離**で成立した会話招待の件数(G7・node/同一セル代理のランでは 0)。
    n_talk_by_distance: int = 0
    #: 〔第 2 期 2-2 段 11a〕腕 ``--proximity distance`` の判定の規則(``engine.proximity.ProximityRule``)。``None``
    #: (既定の腕 cell)では 1 分岐も通らない。会話の開始の判定を「同じ層・距離 ≤ d、または同じ B5 の単位」にする。
    proximity: Any = None
    #: 語彙 v3「並ぶ」を食事/購入へ委譲した件数(第275 #2)。v1/v2 では 0。
    n_queue_to_eat: int = 0
    n_queue_to_buy: int = 0
    #: 9a(D-112 ④): 退去の効果=所属解除の件数(退去の総数・在店を解いた・列を離れた・会話中だった)。
    n_leave: int = 0
    n_leave_indoor: int = 0
    n_leave_queue: int = 0
    n_leave_conversing: int = 0
    #: 退去した**会話中の**体(``engine.run`` が会話マネージャの終了経路=CLOSING で閉じる)。
    leave_conversing: list = field(default_factory=list)
    #: 〔第 2 期 2-4 V3〕移動の意図で歩き出した体の在席の印を解く(ランは常に True・False=部品の単体試験の基準の口)。
    seat_release_walk: bool = False
    #: 〔第 2 期 2-4 V3〕歩き出しで解いた在席の印の数(診断)。
    n_seat_released_walk: int = 0
    #: 〔11-03 §3〕棚卸し B の欠陥の直し(ランは常に True・False=部品の単体試験の基準の口=〔第346〕切替口は消した)。本モジュールで
    #: 効くのは M11(移動・乗車で列を離れる・店のセルに居ない体を列から外す)と M28(列の支払いの確かめを ``_payable`` に)。
    defect_fixes: bool = False
    #: 〔11-03 M11〕移動で歩き出して列を離れた数 / 乗車でホームへ歩き出して列を離れた数 / 列を捌く前に店のセルに居なかった数
    #: (最後の 1 本は本来 0 のはず=移動と乗車の外で動いた体)。旧道では 0。
    n_queue_left_by_move: int = 0
    n_queue_left_by_board: int = 0
    n_queue_dropped_away: int = 0
    #: 〔11-03 M28〕列の確かめで、現金だけなら外れたが口座で払えたので列に残った数(旧道では 0)。
    n_queue_payable_not_cash: int = 0

    def add_result(self, code: int, n: int) -> None:
        if n:
            self.per_result[int(code)] = self.per_result.get(int(code), 0) + int(n)


# ---------------------------------------------------------------- 行動語ごとの適用
def _ok(agents: AgentState, aid: np.ndarray, tick: int, out: ResolveOutcome) -> None:
    r = agents.registry
    r.last_result[aid] = int(ResultCode.OK)
    r.last_result_tick[aid] = int(tick)
    out.add_result(ResultCode.OK, int(aid.size))


def _fail(
    agents: AgentState, aid: np.ndarray, code: ResultCode, tick: int, out: ResolveOutcome
) -> None:
    if aid.size == 0:
        return
    r = agents.registry
    r.last_result[aid] = int(code)
    r.last_result_tick[aid] = int(tick)
    out.add_result(code, int(aid.size))
