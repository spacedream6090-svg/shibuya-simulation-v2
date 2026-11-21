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
- ``advance_body`` の**エネルギー収支**(5 段目 5a・``energy`` を渡したランだけ): 毎 tick の消費と
  語の段の写しは配列演算だけ(逐次ループの新設なし)。``initialize_energy`` の体の定数の抽選は
  ``engine.energy.EnergyModel.draw_bodies`` の宣言(起動時 1 回・体数ぶん)。〔第 3 期 3-5〕値は体の層
  ``engine.body``(``BodyModel.step``・``initial``)が返し、本モジュールは書くだけ(体の層の逐次ループ宣言は
  ``engine.body.schedule``=予約の腕 reserve だけ・相異なる予約の刻みの数ぶん)。
- ``AgentState.freeze/thaw``: フィールド数ぶん(宣言済み)。

expedient(本モジュール分)
- 移動の幾何は ``apply(..., geometry=...)`` で選ぶ。``None`` は **1 tick=1 ノード**(``world.graph`` の宣言と同じ)、
  ``EdgeGeometry`` は辺上の連続位置+希望速度+Kladek 減速(C9・``engine.geometry``)、ナビメッシュの空間
  (``engine.space.nav1``・CLI の既定の空間の腕 nav1=第 5 期 空間の段 1)は面の上の位置と経路。群衆物理(押し合い)は
  どれも持たない。なお ``initialize`` は幾何を取らないので **tick 0 の ``density_stage`` だけは人/セルの段**
  (ほかの幾何でも)。tick 0 の ``apply`` 末尾で幾何の段へ貼り替わる
  ——tick 0 は全員が自宅で就寝中なので影響は無いが、黙って一本化しないために書いておく。
- 行為の効果の内受容(``_apply_rest`` と v1 の購入・食事): 休憩で疲労−3、購入と食事で空腹−4。値は自前(契約書に
  無い)。〔第 3 期 3-5〕体の自然変動(30 刻みごとの空腹+1・疲労+1・就寝中の疲労−2・休みの回復)は本人の体の層
  ``engine.body``(``rules.BODY_EXPEDIENTS``)へ移した。
- 断るは状態を変えない(記録のみ=契約書の効果先が未実装)。通報は **D-113 ②(第267)** で前提「当該事象を知覚済み」を検査する(``_apply_report``・効果先は未実装のまま)。手伝いは
  「相手が援助要求状態」を持たないので必ず失敗(``BAD_TARGET``)。
- 乗車・降車は鉄道の過程(``rail``=``engine.processes.rail``)を渡したランだけ成立しうる(乗車の意図の保持=D-51・
  停車中の列車へ FIFO)。渡さないラン(C2 互換)は乗車が必ず ``NO_TRAIN``、降車が契約書どおり ``NO_STOP``。
- 会話は resolve では招待の成否と活動の欄(``CONVERSING``・``talk_partner``)を書くだけ。セッション(発話ブロック・
  終了判定)は ``engine.conversation``、記憶への転写は記憶の層が持つ。
- 日次内省(T2)は resolve では「就寝で発火」を**数えるだけ**(``n_reflections``=診断の行)。

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
from typing import Any, Final, Mapping
import numpy as np
from shibuya.foundation.vocab.agent_codes import INTENT_NONE, Activity, ResultCode
from shibuya.world.model.agent_table import (
    AgentState,
)
from shibuya.world.model.geometry import EdgeGeometry
from shibuya.foundation.ports.ledger import LedgerBundle
from shibuya.foundation.vocab.act_codes import (
    ACT_ALIGHT,
    ACT_BOARD,
    ACT_BUY,
    ACT_EAT,
    ACT_HELP,
    ACT_LEAVE,
    ACT_MOVE,
    ACT_NONE,
    ACT_QUEUE,
    ACT_REFUSE,
    ACT_REPORT,
    ACT_REST,
    ACT_SLEEP,
    ACT_TALK,
    ACT_WAIT,
    ENGINE_STEP,
)
from shibuya.act.commit import (
    IntentBatch,
)
from shibuya.foundation.vocab.actions import DEFAULT_VOCAB_VERSION, check_vocab_version
from shibuya.world.model.state import World
from shibuya.act.gate import ResolveOutcome, _fail, _ok
from shibuya.act.ops.focus import _advance_focus
from shibuya.act.ops.rail import _apply_alight, _apply_board, _serve_board_queue
from shibuya.act.ops.shop import (
    _apply_buy,
    _apply_eat,
    _apply_queue,
    _apply_wait,
    _serve_poi_queue,
    _stage2_note_calls,
    _stage2_withdraw,
)
from shibuya.act.ops.move import _apply_engine_step, _apply_move, _is_nav, _nav_positions, _nav_stop
from shibuya.act.ops.talk import _apply_leave, _apply_talk
from shibuya.act.ops.intent_writes import _clear_intent_fields, intent_kept_by

__all__ = [
    "REST_FATIGUE_RELIEF", "EAT_DWELL_MINUTES", "apply",
]


# 〔第 3 期 3-5〕体の自然変動の値(周期・就寝と休みの回復)は本人の体の層 ``engine.body.rules`` に移した(上の import が
# 同じ名で写して出す=読み手の import は変えない)。行為の効果(休憩・購入・食事)の値はここに残す。
REST_FATIGUE_RELIEF: Final[int] = 3
#: 食事の所要時間[分](**expedient**・契約行 ``llm.contract._SPEC_EAT`` の宣言値)。
#: **専用タイマーは置いていない**: 在店は購入と同じ在席機構(``poi_ref``/``poi_since``)で
#: 表し、解除は既存の回転率(``engine.processes.crowd.DWELL_MAX_TICKS`` = 30 分)に従う。
#: 20 分ちょうどで解く口を作るには per-tick の新しい走査が要る(P4 宣言が必要)ので、
#: **作るかどうかは親/ユーザーの判断待ち**=いまは宣言値としてだけ持つ。
#: 〔11-03 棚卸し B §4-1〕実装はこう: この値はどこからも読まれない(席は crowd の 30 刻みで解く)。宣言はこう: 食事の
#: 所要時間 20 分(契約行 ``_SPEC_EAT``)。値を合わせるかは仕分け待ち(11-03 §2)。
EAT_DWELL_MINUTES: Final[int] = 20

#: 乗車待ちの打ち切り[tick](**expedient**・D-51 登録簿 §8)。
#: ホームで待ち始めてからこれだけ経っても列車が来なければ意図を消し「列車なし」を返す
#: (個体は次の起床で判断し直す)。値の根拠(答申 §3-1 行 4-7・親一次確認):
#: 渋谷の運転間隔は全線 2.2〜5.0 分・待ち時間 = 間隔の半分 → 最大 5 分の **6 倍**を上限に採る。
#: メトロ 3 線は **1〜4 時台の運行が 0 本**なので「待っても来ない時間帯」が実在する
#: (打ち切りが無いと、その時間帯にホームへ来た体が始発まで待ち続けて動かなくなる)。
#: D-113 ②(第267): 通報の前提「当該事象を知覚済み」の窓[tick]。事象の行が B4 に出た tick から
#: 応答の適用までの遅れは t_apply = 起床 + δ_perc + δ_think(運用設計書 §2.4)で、最長レーン
#: L3(300 s)= 5 tick(mock/L1 は 1 tick)。レーン表からの導出値=感度腕の対象ではない。
REPORT_WINDOW_TICKS: Final[int] = 5

#: 乗車の意図(``board_line``)を**保つ**行動(これ以外を選んだら意図は落ちる)。
#: 乗車=張り直し / 待機=ホームで待ち続ける / エンジン継続=ホームへ歩いている途中。
#: **語彙 v3 の「なし」**(待機の代替)も待ち続けに数える(v1/v2 では 25 は来ない=不変)。
#: 〔11-03 棚卸し B §4-1・B5〕実装はこう: ホームへ**歩いている途中**で待機・なしを選ぶと ``_apply_wait`` が歩みを止め
#: (WAITING)、意図は ``_serve_board_queue`` の「宙に浮いた意図の掃除」で消える(保たれるのはホームで待っている体だけ)。
#: 宣言はこう: 待機・なしで意図を保つ。どちらに合わせるかは仕分け待ち(11-03 §2)。
_BOARD_KEEP_ACTIONS: Final[tuple[int, ...]] = (ACT_BOARD, ACT_WAIT, ENGINE_STEP, ACT_NONE)

#: 就寝の意図(``sleep_pending``)を**保つ**行動(これ以外を選んだら意図は落ちる・D-62)。
#: 就寝=張り直し / エンジン継続=就寝地へ歩いている途中。
#: 〔11-03 棚卸し B §4-1・B5〕実装はこう: なし・待機を選ぶと就寝の意図は落ちる。宣言はこう: 親決定 Q20「なし・待機は新しい
#: 行為が無い=意図を保つ」(段 2c の意図 ``INTENT_KEEP_ACTIONS`` には効く)。就寝の意図に広げるかは仕分け待ち(11-03 §2)。
_SLEEP_KEEP_ACTIONS: Final[tuple[int, ...]] = (ACT_SLEEP, ENGINE_STEP)


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
    salient: object | None = None,
    report_precondition: bool = True,
    queue_service: bool = True,
    vocab_version: str = DEFAULT_VOCAB_VERSION,
    geometry: EdgeGeometry | None = None,
    focus_request: np.ndarray | None = None,
    talk_by_distance: bool = False,
    track_visits: bool = False,
    energy: Any = None,
    track_events: bool = False,
    proximity: Any = None,
    seat_release_walk: bool = False,
    defect_fixes: bool = False,
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
        salient: 顕著行為(``engine.processes.salient.SalientProcess``)。**D-113 ②**: 通報は
            ``event_seen_tick``(自分のセルの B4 に事象の行が出た最後の tick)が直近
            ``REPORT_WINDOW_TICKS`` 以内のときだけ成立し、それ以外は ``BAD_TARGET``。
            ``None``(過程 OFF・C2 互換)では従来どおり記録のみで必ず成功。
        report_precondition: 上の検査の切替口(既定 True)。``False`` は第266 以前の挙動。
        queue_service: **D-113 ③** 満席で並んだ体を、席が空いた分だけ並んだ順に席へ入れて
            並んだときの行動(購入/食事)を完了させる(既定 True・``_serve_poi_queue``)。
            ``False`` は第267 以前の挙動(誰も捌かず 15 tick で ``INTERRUPTED``)。
        vocab_version: 行動語彙の版(D-71 §3 F)。``"v2"`` で「食事」の分岐が増える。
            既定 ``"v1"`` は ``_APPLY``(13 分岐)をそのまま回す=**1 バイトも変わらない**。
        geometry: **C9 G1 (b) 辺上の連続位置**(``engine.geometry.EdgeGeometry``)。
            ``None``(既定=``geometry="node"``)は現行の 1 tick=1 ノードで
            **1 バイトも変わらない**。渡すと ① エンジン継続が「希望速度 × Kladek 減速 ×
            60 s」の距離だけ辺上を進む ② ``xy`` が両端ノードの線形補間になる
            ③ セル/層が近い方の端点から決まる ④ 密度段が人/m² の Fruin LOS 段になる。
        focus_request: **C9b G3/G4 対象の要求**(``(n_agents,)`` int64・``-1``=なし・
            ``≥0``=個体 id・``≤-2``=``-2-poi_id``)。移動なら「近づく」の相手、待機なら
            「見る」の注意の焦点。``None``(既定)では**1 分岐も通らない**。
            書き込み先は ``agents.focus_target`` / ``focus_ttl``(``attention_columns`` の
            ランだけ存在する欄)で、欄が無いランでは要求は**黙って捨てる**のではなく
            「近づく」の目的ノードにだけ効く(焦点は持てないので ``TARGET_GONE`` も出ない)。
        talk_by_distance: **C9b G7**。``True`` で会話の成立判定が「同一セル代理」から
            ``TALK_OPEN_METERS``(2 m)の実距離になる。``False``(既定)は現行のまま。
        seat_release_walk: 〔第 2 期 2-4 V3〕``True`` で移動の意図(``_apply_move``)で歩き出した体の在席の印
            (``poi_ref``/``poi_since``)を解く(ランは常に ``True``=``engine.seat_release`` の walk)。``False``(この関数の
            既定=直に呼ぶ部品の単体試験の基準の口・〔第346〕ランの切替口 legacy は消した)は 2-4 より前の挙動(退去・乗車・
            滞在の上限でしか解かない)。
        defect_fixes: 〔11-03 §3〕``True`` で棚卸し B の M11・M28 を直した道(ランは常に ``True``):
            移動(``_apply_move``)で歩き出した体と、乗車(``_apply_board``)でホームへ歩き出した体は満席の列を離れる
            (失敗は書かない)・列を捌く(``_serve_poi_queue``)前に店のセルに居ない体を列から外す・列の支払いの確かめを
            ``_payable``(現金か口座)にする。``False``(この関数の既定=直に呼ぶ部品の単体試験の基準の口・〔第346〕ランの
            切替口 legacy は消した)は版上げの前の挙動。
        proximity: 〔第 2 期 2-2 段 11a〕腕 ``--proximity distance`` の判定の規則(``engine.proximity.ProximityRule``)。
            渡すと会話の開始の判定が「舞台の中・同じ層・距離 ≤ d、または同じ B5 の単位」になる(``talk_by_distance``
            より強い)。``None``(既定)は 1 分岐も通らない。
        track_visits: **4 段目(M13 訪問)**。``True`` で購入/食事の成立した行(体, POI)を
            ``ResolveOutcome.visit_agents``/``visit_pois`` に控える(``engine.familiarity`` が読む)。
            控えるだけ=世界は変えない。
        energy: **5 段目 5a 体のエネルギー収支**(``engine.energy.EnergyLayer``)。``None``(既定)は
            空腹 v1(購入/食事で ``hunger`` −4)=**1 バイトも変わらない**。渡すと食事の成立で
            ``since_meal_kcal=0``・収支に時間帯の比 × EER、飲食系の購入で軽食/飲料の比 × EER を
            差し引き、``hunger`` を語の段の写しに書き直す(アジェンダ §1-3)。

    Returns:
        ``ResolveOutcome``。
    """
    ver = check_vocab_version(vocab_version)
    apply_table = _APPLY_BY_VOCAB[ver]
    out = ResolveOutcome(
        tick=int(tick),
        n_confirmed=len(plan_confirmed),
        n_losers=len(losers),
        ledger=ledger,
        rail=rail,
        crowd=crowd,
        hotel=hotel,
        salient=salient,
        report_precondition=bool(report_precondition),
        queue_service=bool(queue_service),
        geometry=geometry,
        focus_request=(
            None if focus_request is None else np.asarray(focus_request, dtype=np.int64)
        ),
        talk_by_distance=bool(talk_by_distance),
        track_visits=bool(track_visits),
        energy=energy,
        track_events=bool(track_events),
        proximity=proximity,
        seat_release_walk=bool(seat_release_walk),
        defect_fixes=bool(defect_fixes),
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
            # 段 2c: 意図(``intent_action``)も同じ形。**保つ**のはエンジン継続・なし・待機・行き先が
            # 同じ移動(親決定 Q20)。世界に触れる行為(着いて実行した意図の行為そのものを含む)と
            # 行き先の変わる移動は意図を消す(実行の成否は ``engine.intent`` が ``last_result`` から数える)。
            held = np.flatnonzero(r.intent_action[aid] != INTENT_NONE)
            if held.size:
                kept = intent_kept_by(agents, world, aid[held], code[held], tgt[held])
                if not bool(kept.all()):
                    _clear_intent_fields(r, aid[held[~kept]])

        # ---- 〔第 2 期 2-1・検収 A1〕経済の段階 2 の腕(既定 off=通らない): 金に触れる行為の呼の id を台帳に控える ----
        # (列の捌き・購入・食事より前=この刻みの答えの支払いと原因に使う)
        _stage2_note_calls(plan_confirmed, out)

        # ---- D-113 ③ 満席の列の捌き(第268): 席が空いた分だけ並んだ順に入れる ----
        # **新しい意図の適用より前**に置く: 先に並んでいた体が空席を取り、この tick に来た
        # 買い手は ``admitted_this_tick`` 越しにその後ろへ並ぶ(FIFO)。
        _serve_poi_queue(agents, world, tick, out)

        # ---- C9 edge: 新しい行動を選んだ体は**辺から降りて近い端点に立つ** ----
        # 以降の適用関数は全て「体はノードに居る」前提で ``node`` からセル・経路を引く
        # (``_cell_of_node`` / ``_apply_move`` / ``_apply_buy`` …)。ここで 1 回だけ吸着すれば
        # 個々の適用関数に幾何を配らなくて済む。エンジン継続(移動の続き)は対象外。
        if _is_nav(geometry) and code.size:
            # 第 5 期 段 1(nav1): 新しい行動を選んだ体は**その場に止まる**(吸着の瞬間移動をしない)・経路を捨てる
            _nav_stop(agents, geometry, aid[code != ENGINE_STEP])
        elif geometry is not None and code.size:
            act = aid[code != ENGINE_STEP]
            if act.size:
                act = act[r.path_next_node[act] >= 0]
            if act.size:
                nd, nx, s, eid = geometry.snap_to_nearest_node(
                    r.node[act], r.path_next_node[act], r.edge_s[act], r.edge_id[act]
                )
                r.node[act] = nd.astype(np.int32)
                r.path_next_node[act] = nx.astype(np.int32)
                r.edge_s[act] = s
                r.edge_id[act] = eid.astype(np.int32)

        # 逐次ループ宣言: 行動語ぶん(v1=13 分岐 / v2=14 分岐)。個体数には比例しない。
        for action in _ACTION_ORDER_BY_VOCAB[ver]:
            sel = np.flatnonzero(code == action)
            if sel.size == 0:
                continue
            out.per_action[int(action)] = out.per_action.get(int(action), 0) + int(sel.size)
            if action != ENGINE_STEP:
                # 「直前に**試みた**行動」= B6 の主語(成功・失敗を問わず書く)。
                # エンジン継続は新しく試みた行動ではない(移動の続き)ので書かない。
                r.last_action[aid[sel]] = np.int8(action)
            apply_table[action](agents, world, aid[sel], tgt[sel], tick, out, schedule)

        # 落選者(行動契約書 §2「落選者には失敗の意味論」)
        if len(losers):
            la = losers.agent_id.astype(np.int64)
            lc = losers.action_code.astype(np.int64)
            keep = lc != ENGINE_STEP
            if keep.any():
                r.last_action[la[keep]] = lc[keep].astype(np.int8)
            r.last_result[la] = int(ResultCode.LOST_ARBITRATION)
            r.last_result_tick[la] = int(tick)
            # 段 2c: 落選した体の意図も消す(着いて実行した行為が席を取れなかった=失敗の一種)
            held = la[keep]
            held = held[r.intent_action[held] != INTENT_NONE]
            if held.size:
                _clear_intent_fields(r, held)
            out.add_result(ResultCode.LOST_ARBITRATION, int(la.size))

        # ---- 〔第 2 期 2-1〕経済の段階 2 の腕(既定 off=通らない): この刻みに判断した体の引き出し(本人の判断の副の行為) ----
        if code.size:
            _acted = code != ENGINE_STEP
            _stage2_withdraw(
                agents, aid[_acted], tick, out,
                call_ids=None if plan_confirmed.call_id is None else plan_confirmed.call_id[_acted],
                flags=None if plan_confirmed.s2_flags is None else plan_confirmed.s2_flags[_acted],
            )

        # ---- D-51 乗車待ちの捌き(停車中の列車へ FIFO・打ち切り) ----
        # **行動語の適用の後・位置確定の前**に置く: この tick にホームへ着いた体(エンジン継続)と
        # この tick に乗車を選んだ体を同じ列車に乗せるため。
        _serve_board_queue(agents, world, tick, out)

        # ---- 位置の確定と密度(予算行 P2 の測定対象) ----
        t0 = time.perf_counter()
        c0 = time.thread_time()
        if geometry is None:
            node = r.node.astype(np.int64)
            valid = node >= 0
            new_cell = np.where(valid, world.assets.node_cell[np.maximum(node, 0)], -1)
            r.cell[:] = new_cell.astype(np.int32)
            r.band[:] = np.where(
                valid, world.assets.node_band[np.maximum(node, 0)], 0
            ).astype(np.int8)
            r.xy[:] = world.assets.node_xy[np.maximum(node, 0)]
            world.cells.density[:] = world.compute_density(r.cell)
            world.cells.density_stage[:] = world.density_stage()
        elif _is_nav(geometry):
            # 第 5 期 段 1(nav1): 位置は (xy, 階)・セルは面から導く・移動の外で node が変わった体は節の点へ
            _nav_positions(agents, world, geometry)
            world.cells.density[:] = world.compute_density(r.cell)
            # 〔段 1 の検収 M4 (a)〕密度の段の分子は面の上に居て建物の中でない体だけ
            world.cells.density_stage[:] = geometry.density_stage(geometry.surface_counts(r))
        else:
            # C9 edge: 辺に乗っていてよいのは「移動中かつ目的あり」の体だけ。
            # 乗車・降車・外界配置などで ``node`` を直に書き換えた体はここで降ろす
            # (書き換えの度に幾何を配らないための単一の掃除点)。
            off = np.flatnonzero(
                (r.path_next_node >= 0)
                & ((r.activity != int(Activity.MOVING)) | (r.target_node < 0))
            )
            if off.size:
                nd, nx, s, eid = geometry.snap_to_nearest_node(
                    r.node[off], r.path_next_node[off], r.edge_s[off], r.edge_id[off]
                )
                r.node[off] = nd.astype(np.int32)
                r.path_next_node[off] = nx.astype(np.int32)
                r.edge_s[off] = s
                r.edge_id[off] = eid.astype(np.int32)
            cell, band, xy = geometry.positions(
                r.node, r.path_next_node, r.edge_s, r.edge_id
            )
            r.cell[:] = cell
            r.band[:] = band
            r.xy[:] = xy
            world.cells.density[:] = world.compute_density(r.cell)
            world.cells.density_stage[:] = geometry.density_stage(world.cells.density)
        # C9b G4: 注意の焦点の寿命と喪失距離(**位置を貼り直した後**=同 tick の最新座標で測る)
        _advance_focus(agents, world, out)
        world.cells.open_count[:] = world.open_count_per_cell(tick)
        out.movement_seconds = time.perf_counter() - t0
        out.movement_cpu_seconds = time.thread_time() - c0
    return out


def _apply_record_only(agents, world, aid, tgt, tick, out, schedule) -> None:
    """断る: C2 では状態を変えない(効果先が未実装=記録のみ)。失敗しない。"""
    _ok(agents, aid, tick, out)


def _apply_report(agents, world, aid, tgt, tick, out, schedule) -> None:
    """通報(D-113 ②・第267): 前提「当該事象を知覚済み」(行動契約書 §2.1)を検査する。

    知覚済み = 直近 ``REPORT_WINDOW_TICKS`` tick 以内に、自分のセルの B4 に顕著行為の行が
    載った(``SalientProcess.event_seen_tick``)。満たさなければ ``BAD_TARGET``(通報すべき
    事象が無い)。効果先(事象レコードに通報 1 件 → 検知確率)は未実装のまま=成立しても
    状態は変えない。``out.salient`` が無い(過程 OFF・C2 互換)か切替口 OFF なら従来どおり
    必ず成功。逐次ループ宣言(P4): なし(ベクトル判定)。
    """
    s = out.salient
    seen_arr = getattr(s, "event_seen_tick", None) if s is not None else None
    if not out.report_precondition or seen_arr is None:
        _ok(agents, aid, tick, out)
        out.n_report_ok += int(aid.size)
        return
    seen = np.asarray(seen_arr, dtype=np.int64)[aid]
    fresh = (seen >= 0) & (int(tick) - seen <= REPORT_WINDOW_TICKS)
    if fresh.any():
        _ok(agents, aid[fresh], tick, out)
    _fail(agents, aid[~fresh], ResultCode.BAD_TARGET, tick, out)
    out.n_report_ok += int(fresh.sum())
    out.n_report_no_event += int((~fresh).sum())


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


_APPLY: Final[dict[int, object]] = {
    ENGINE_STEP: _apply_engine_step,
    ACT_MOVE: _apply_move,
    ACT_BOARD: _apply_board,
    ACT_ALIGHT: _apply_alight,
    ACT_BUY: _apply_buy,
    ACT_WAIT: _apply_wait,
    ACT_TALK: _apply_talk,
    ACT_LEAVE: _apply_leave,
    ACT_REPORT: _apply_report,
    ACT_HELP: _apply_help,
    ACT_REFUSE: _apply_record_only,
    ACT_REST: _apply_rest,
    ACT_SLEEP: _apply_sleep,
}

assert len(_APPLY) == 13, "行動語 12 + エンジン継続 1"

#: **語彙 v2** の適用表(v1 の 13 分岐 + 食事)。``_APPLY`` は**そのまま**=v1 の検査も
#: ``tests/engine/test_parser_contract.py`` の「12 語 + エンジン継続 = 13 分岐」も動かない。
_APPLY_V2: Final[dict[int, object]] = {**_APPLY, ACT_EAT: _apply_eat}
assert len(_APPLY_V2) == 14, "語彙 v2 = 13 分岐 + 食事"

#: **語彙 v3** の適用表(二層・D-116 C): 待機・休憩・降車の分岐を**持たない**(コード 4/10/2 は
#: 欠番=v3 のエンジンには来ない)・食事・**並ぶ**(22=食事/購入へ委譲)・**なし**(25=旧 待機と
#: 同じ適用関数=時間経過だけ・失敗しない)。``_APPLY``/``_APPLY_V2`` は**そのまま**。
_APPLY_V3: Final[dict[int, object]] = {
    ENGINE_STEP: _apply_engine_step,
    ACT_MOVE: _apply_move,
    ACT_BOARD: _apply_board,
    ACT_BUY: _apply_buy,
    ACT_NONE: _apply_wait,
    ACT_TALK: _apply_talk,
    ACT_LEAVE: _apply_leave,
    ACT_REPORT: _apply_report,
    ACT_HELP: _apply_help,
    ACT_REFUSE: _apply_record_only,
    ACT_SLEEP: _apply_sleep,
    ACT_EAT: _apply_eat,
    ACT_QUEUE: _apply_queue,
}
assert len(_APPLY_V3) == 13, "語彙 v3 = 横断 11 語 + なし + エンジン継続"

#: 語彙版 → 適用表。
_APPLY_BY_VOCAB: Final[Mapping[str, dict[int, object]]] = {
    "v1": _APPLY, "v2": _APPLY_V2, "v3": _APPLY_V3,
}

#: 語彙版 → ``apply`` が回す行動の**順序**(決定論のため固定・v2 は末尾に食事を足すだけ)。
_ACTION_ORDER_V1: Final[tuple[int, ...]] = (
    ENGINE_STEP, ACT_MOVE, ACT_BOARD, ACT_ALIGHT, ACT_BUY, ACT_WAIT, ACT_TALK,
    ACT_LEAVE, ACT_REPORT, ACT_HELP, ACT_REFUSE, ACT_REST, ACT_SLEEP,
)
#: 語彙 v3 の順序(v1 の並びから 降車/休憩 を抜き、待機の位置に なし を置き、末尾に 食事・並ぶ)。
_ACTION_ORDER_V3: Final[tuple[int, ...]] = (
    ENGINE_STEP, ACT_MOVE, ACT_BOARD, ACT_BUY, ACT_NONE, ACT_TALK,
    ACT_LEAVE, ACT_REPORT, ACT_HELP, ACT_REFUSE, ACT_SLEEP, ACT_EAT, ACT_QUEUE,
)
_ACTION_ORDER_BY_VOCAB: Final[Mapping[str, tuple[int, ...]]] = {
    "v1": _ACTION_ORDER_V1,
    "v2": _ACTION_ORDER_V1 + (ACT_EAT,),
    "v3": _ACTION_ORDER_V3,
}
assert set(_ACTION_ORDER_V3) == set(_APPLY_V3)
