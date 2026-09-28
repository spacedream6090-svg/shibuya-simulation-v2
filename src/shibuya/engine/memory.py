"""engine.memory — 記憶 第 1 段の **記録**(6 段目 6a・D-95・記憶アジェンダ v1 M1〜M4・M13・M16・修正 1・第294)。

正典: ``docs/design/v2-memory-stage1-implementation-agenda.md`` §1(段 6a の 1〜9)・§4。上位=
``docs/design/v2-memory-agenda.md`` v1(M1〜M16 の決定と修正 1・2・4)。事実=
``docs/research/v2-r48-own-code-memory-range-return.md`` §B1(記憶は無い・会話の本文は捨てている)。
#56 の ``engine.familiarity``(親しみの表)と同じ流儀(腕でだけ確保・書き手は resolve・A の近似)。

6a=**記録と読み口**・**6b=想起**(:meth:`MemoryLayer.recall` → 描画の B5「記憶」行・第295)。
D-120 7a〜7c: 店の評価の記憶(``engine.store_memory``・:meth:`MemoryLayer.enable_store`)を同じ入れ物に持ち、
7c で想起の k の内側に店の行をエピソードと同じ score 順で競わせる(B5 の店の項・テンプレ v1.3・第298)。

表(``AgentState(memory_columns=True)`` のランだけ確保・``--memory on``)
    体ごとに N 行(:data:`MEMORY_N`=128・M2・感度 64/256)。1 行=``mem_kind`` u8(事象の種類=
    :data:`EVENT_KINDS`・0=空行)・``mem_tick`` i32(最初)・``mem_last`` i32(最後)・``mem_cell`` i32・
    ``mem_partner`` i32(体 id・−1)・``mem_object`` i32(#56 と同じ符号化=POI ≥0 / 場所 −(cell+2) /
    人 1<<30|id / −1。会話の行では**店 ID**=会話を始めたときの在席 POI・無ければ −1=M1 の決定)・
    ``mem_result`` u8(``ResultCode``)・``mem_importance`` u8・``mem_n`` u16(同じ鍵の反復=A の n)=
    **実 25 B/行**(宣言は 32 B/行=詰め物 7 B は予算の側に置く=配列は確保しない)。

会話の要旨(M1 (b))
    SoA の外(``MemoryLayer.gist[(体, 行)]``)。体あたり上限 :data:`GIST_PER_AGENT`=16 件(古い順に
    落とす)・:data:`GIST_CHARS`=40 字=その会話で自分が最初に書いた**空でない「ひと言」**、ひと言が
    無ければ(語彙 v3 の 5 ラベルには無い)**理由欄**の先頭 40 字(**第294 の親の暫定・Q57**)。
    相手の発話は持たない。

書き手(:meth:`MemoryLayer.after_tick`・tick の Phase C と活動層・意図の層の後・親しみの表の前)
    (a) **行動の成否**: その tick に結果(``last_result_tick == tick``)が書かれた体の ``last_action`` ×
        ``last_result``(:data:`ACTION_KIND`)。移動の成功は「着いた」(エンジン継続の到着)だけ・会話の
        成功は (b) の会話の行だけ(二重にしない)。
    (b) **会話**: 開いたセッションの参加者ごとに 1 行(相手・店 ID)。発話ごとに ``mem_n``+1。
    (c) **気づき**: その tick の顕著行為に気づいた体(``SalientProcess.events[].noticed``)に 1 行
        (object=事象のセルの場所=顕著行為に主の体 id は無い=宣言)。
    (d) **強い看板**(修正 1 の二本立て): p_see を通って B2 に看板行が載った (体, POI) のうち **初見**
        (**記憶の表**にその POI の看板の行が無い=描画による露出=意識的な初見。親しみの表の「入った回」
        は潜在なので判定に使わない=``--familiarity on`` でも同じ判定・**第294 の決め Q58**)だけ。
    (e) 記録しない(宣言): 内受容の跨ぎ・範囲外の食事・p_see の通過(露出=#56)・移動の各 tick・
        移動の開始・「なし」・待機/休憩/退去/断る。
    統合=同じ鍵(kind・partner・object・result)は新しい行を作らず ``mem_n``+1・``mem_last`` 更新。

importance 固定表(M3 (b)): 失敗 3・会話 2・成功 1・気づき 1・強い看板 1・初回(その鍵の最初の行)+1・
上限 4(:data:`IMPORTANCE`)。**統合(同じ鍵の反復)では「初回 +1」を外して base に戻す**(第294 の決め
Q56=「初回 > 反復」を表のとおりにする)。

想起(6b・M4 (a)+修正 2・M5 (a)・M6 (a)・M16 (a))
    クエリ q=起床の級(``WAKE_CONDITION_CLASS``)+現在セル+相手(会話の招待者・会話の相手・人の意図)+
    対象(POI の意図・在席・列の POI)+直前の結果(``last_action`` の種類 × ``last_result``)。**ID 一致**
    (相手 ∨ 対象 ∨ セル ∨ 直前の結果と同じ種類・結果)で候補を絞り、``A ≥ τ`` の行だけを score の降順に
    k 件(会話 :data:`RECALL_K_CONVERSATION`=3・それ以外 :data:`RECALL_K_OTHER`=2=計画境界・満了・
    個体・セル=修正 2)。候補が k 未満なら ``A ≥ τ`` の全行から score 順で補う(宣言)。埋め込みは無し。
    τ=:data:`RECALL_TAU`(**−2.0**=第295 親決定: n=1 の出来事を 3.6 時間・n=2 を 14.5 時間・翌日に残るのは n≥3=「今日のうち」の窓。実装役の仮置き −1.0 は 29 分で消えて B5 直近と重なるため退けた。感度 −1.5/−2.5)。

A と score(M2・M6 (a))::

    A = ln(n / (1 − d)) − d · ln(L + 1)      (d=0.5・L=(tick − mem_tick)×分/tick・#56 と同じ近似)
    score = w_r · A + w_i · importance        (w_r=1.0・w_i=0.5=宣言・w_v=0=埋め込み無し)

忘却(M2 (b)): 満杯で新しい鍵が来たら score 最小の行を落とす(同点は行番号の小さい方・``evictions``)。
訪問カウンタは #56 の表を正とする(記憶からも数えられるが二重にしない=宣言)。

逐次ループ宣言(P4)
    1. :meth:`MemoryLayer.after_tick`: 体あたりのその tick の事象の件数の最大ぶん(回)× 配列演算。
       体数に比例する Python ループは無い(結果の走査は ``last_result_tick == tick`` の配列比較)。
    2. 会話: その tick に開いたセッションの数ぶん・発話の数ぶん(≤ 1 tick の呼数)。
    3. 気づき: その tick の顕著行為の件数ぶん(``EventBudget`` が 200/tick で切る)。
    4. 看板の初見: その tick の看板の露出の件数ぶん(描画 1 回につき高々 1 件)。
    5. :meth:`MemoryLayer.recall`: なし(1 呼につき 1 体の N 行の配列演算)。7c(D-120)の店の行つき
       (``_recall_with_store``)は並べ替えた候補(≤ N+32)を k 件で止まるまで見る(同じ店の重なりを飛ばす)。
    6. :meth:`MemoryLayer.summary`(K-2/K-5 の計器): 行のある体の数ぶん(ランの終わりに 1 回)。
"""

from __future__ import annotations

from collections import Counter, OrderedDict
from typing import Any, Final, NamedTuple, Sequence

import numpy as np

from shibuya.agents.state import WAKE_CONDITION_CLASS, IntentKind, ResultCode, WakeCondition
from shibuya.core.types import EventClass
from shibuya.engine import resolve as R
from shibuya.engine.familiarity import place_thing

__all__ = [
    "MEMORY_N",
    "MEMORY_MODES",
    "MEMORY_D",
    "MEMORY_W_R",
    "MEMORY_W_I",
    "MEMORY_ROW_BYTES_DECLARED",
    "GIST_PER_AGENT",
    "GIST_CHARS",
    "EVENT_KINDS",
    "KIND_NAMES",
    "ACTION_KIND",
    "IMPORTANCE",
    "IMPORTANCE_MAX",
    "importance_of",
    "activation_rows",
    "RECALL_TAU",
    "RECALL_K_CONVERSATION",
    "RECALL_K_OTHER",
    "K5_FAILURES",
    "RecallItem",
    "STORE_ITEM_KIND",
    "STORE_RECALL_SCOPES",
    "MemoryLayer",
]

#: 体あたりの行数(M2・宣言・感度 64/256)。
MEMORY_N: Final[int] = 128
MEMORY_MODES: Final[tuple[str, ...]] = ("off", "on")
#: 減衰(既決・認知設計 §4)。
MEMORY_D: Final[float] = 0.5
#: score の重み(宣言・感度腕)。w_v=0(埋め込み無し=M6 (a))。
MEMORY_W_R: Final[float] = 1.0
MEMORY_W_I: Final[float] = 0.5
#: 1 行の宣言バイト(実 25 B・詰め物 7 B は予算の側=アジェンダ §1-1 の「32 B に揃える」)。
MEMORY_ROW_BYTES_DECLARED: Final[int] = 32
#: 会話の要旨(M1 (b))。
GIST_PER_AGENT: Final[int] = 16
GIST_CHARS: Final[int] = 40
#: 想起の入口の名(``WakeCondition`` の符号 → 名・計数の鍵)と q の定数(呼ごとに作らない)。
_ENTRANCE_NAMES: Final[tuple[str, ...]] = tuple(w.name for w in sorted(WakeCondition, key=int))
_COND_TURN: Final[int] = int(WakeCondition.CONVERSATION_TURN)
_INTENT_PERSON: Final[int] = int(IntentKind.PERSON)
_INTENT_POI: Final[tuple[int, int]] = (int(IntentKind.POI_NAMED), int(IntentKind.POI_CATEGORY))
#: 想起の閾値 τ(M16 (a)・宣言の仮置き・感度 −0.5/−2.0/−2.5)。A の単位は分(L=分)。
RECALL_TAU: Final[float] = -2.0
#: 想起の件数(M4 (a)+修正 2): 会話 3・それ以外(計画境界・満了・個体・セル)2。
RECALL_K_CONVERSATION: Final[int] = 3
RECALL_K_OTHER: Final[int] = 2
#: 7c(D-120): 想起した店の評価の行の種類(エピソードの ``EVENT_KINDS`` の外)。
STORE_ITEM_KIND: Final[int] = 12
#: 7c: 店の行を B5 の想起の候補にする入口(all=全入口・conversation=会話だけ=感度腕)。
STORE_RECALL_SCOPES: Final[tuple[str, ...]] = ("all", "conversation")
#: 7c: 想起で POI が重なる事象(店の行と同じ店のエピソード=先に選んだ方だけ載せる)。
_SHOP_OBJ_KINDS: Final[tuple[int, ...]] = (1, 2, 3, 11)
#: K-5(失敗の回避・修正 4)で「失敗の記憶」とする結果。
K5_FAILURES: Final[tuple[int, ...]] = (
    int(ResultCode.REFUSED), int(ResultCode.CLOSED), int(ResultCode.OUT_OF_STOCK),
    int(ResultCode.TRAIN_FULL), int(ResultCode.PARTNER_BUSY),
)

#: **EVENT_KINDS v0**(宣言・実装役の起草=問いで返す)。0 は空行。
EVENT_KINDS: Final[dict[str, int]] = {
    "buy": 1,        # 購入
    "eat": 2,        # 食事
    "queue": 3,      # 並ぶ(列に入った・並んだ先で成立したら buy/eat)
    "move": 4,       # 移動(着いた=成功・到達不能/対象不正/遠すぎ=失敗。開始は記録しない)
    "board": 5,      # 乗車
    "sleep": 6,      # 就寝(行為として選んだもの。計画の就寝=エンジンの実行は記録しない)
    "talk": 7,       # 会話(成功=会話の行・失敗=断られた/相手が会話中/去った …)
    "report": 8,     # 通報
    "help": 9,       # 手伝い
    "notice": 10,    # 気づき(顕著行為)
    "signage": 11,   # 強い看板(初見)
}
KIND_NAMES: Final[dict[int, str]] = {v: k for k, v in EVENT_KINDS.items()}
_EMPTY: Final[int] = 0


def _action_kind_table() -> dict[int, int]:
    from shibuya.engine import commit as C

    return {
        int(C.ACT_BUY): EVENT_KINDS["buy"],
        int(C.ACT_EAT): EVENT_KINDS["eat"],
        int(C.ACT_QUEUE): EVENT_KINDS["queue"],
        int(C.ACT_MOVE): EVENT_KINDS["move"],
        int(C.ACT_BOARD): EVENT_KINDS["board"],
        int(C.ACT_SLEEP): EVENT_KINDS["sleep"],
        int(C.ACT_TALK): EVENT_KINDS["talk"],
        int(C.ACT_REPORT): EVENT_KINDS["report"],
        int(C.ACT_HELP): EVENT_KINDS["help"],
    }


#: 行動コード → 事象の種類(``last_action`` を読む)。載っていない行動は記録しない。
ACTION_KIND: Final[dict[int, int]] = _action_kind_table()

#: importance 固定表(M3 (b)・宣言): 失敗 3・会話 2・成功 1・気づき 1・強い看板 1・初回 +1・上限 4。
IMPORTANCE: Final[dict[str, int]] = {
    "failure": 3, "talk": 2, "success": 1, "notice": 1, "signage": 1, "first_bonus": 1,
}
IMPORTANCE_MAX: Final[int] = 4


def importance_of(kind: np.ndarray, result: np.ndarray, first: np.ndarray) -> np.ndarray:
    """事象 → importance(固定表・配列演算)。"""
    k = np.asarray(kind, dtype=np.int64)
    res = np.asarray(result, dtype=np.int64)
    base = np.full(k.size, IMPORTANCE["success"], dtype=np.int64)
    base[k == EVENT_KINDS["talk"]] = IMPORTANCE["talk"]
    base[k == EVENT_KINDS["notice"]] = IMPORTANCE["notice"]
    base[k == EVENT_KINDS["signage"]] = IMPORTANCE["signage"]
    base[res != int(ResultCode.OK)] = IMPORTANCE["failure"]
    base += np.asarray(first, dtype=bool).astype(np.int64) * IMPORTANCE["first_bonus"]
    return np.minimum(base, IMPORTANCE_MAX)


class RecallItem(NamedTuple):
    """想起した 1 行(描画の材料=``perception.renderer`` が文にする)。

    7c(D-120): 店の評価の行は ``kind=STORE_ITEM_KIND``・``row=N+店の行``(テープの ``recalled_rows`` で
    N 以上は店の行)・``obj``=POI・``valence``=向き(−1/0/+1)・``source``=出どころのビット。
    """

    row: int
    last_tick: int
    kind: int
    partner: int
    obj: int
    result: int
    cell: int
    gist: str
    valence: int = 0
    source: int = 0


def activation_rows(n: np.ndarray, first_tick: np.ndarray, tick: int, minutes_per_tick: float,
                    d: float = MEMORY_D) -> np.ndarray:
    """A = ln(n/(1−d)) − d·ln(L+1)(L=(tick − first)×分/tick・#56 と同じ近似)。n=0 の行は −inf。"""
    nn = np.asarray(n, dtype=np.float64)
    L = np.maximum(0.0, (int(tick) - np.asarray(first_tick, dtype=np.float64)) * float(minutes_per_tick))
    with np.errstate(divide="ignore"):
        return np.log(nn / (1.0 - float(d))) - float(d) * np.log(L + 1.0)


class MemoryLayer:
    """記憶の表の書き手と読み口(記録だけ・本段では誰も読まない)。"""

    def __init__(self, n_agents: int, n_rows: int = MEMORY_N, *, minutes_per_tick: float = 1.0,
                 d: float = MEMORY_D, w_r: float = MEMORY_W_R, w_i: float = MEMORY_W_I) -> None:
        self.n = int(n_agents)
        self.n_rows = int(n_rows)
        self.minutes_per_tick = float(minutes_per_tick)
        self.d = float(d)
        self.w_r = float(w_r)
        self.w_i = float(w_i)
        self.stats: Counter = Counter()
        #: 会話の要旨 (体, 行) → 40 字(体あたり 16 件まで・古い順に落とす)。
        self.gist: dict[tuple[int, int], str] = {}
        self._gist_order: dict[int, "OrderedDict[int, None]"] = {}
        #: (体, セッション id) → (相手, 店 ID)=発話で会話の行を引く鍵。
        self._session_key: dict[tuple[int, int], tuple[int, int]] = {}
        self._gist_done: set[tuple[int, int]] = set()
        self._next_session = 0
        self._target = np.full(self.n, -1, dtype=np.int64)  # その tick の intent の対象(散らす先)
        #: 想起の閾値 τ(``--memory-tau``)。
        self.tau = float(RECALL_TAU)
        #: 想起の計数(入口別・τ で切った行・補った件数)。
        self.recall_stats: Counter = Counter()
        #: D-120 7a: 店の評価の記憶(``--store-memory on`` のランだけ・:meth:`enable_store`)。
        self.store: Any = None

    def enable_store(self, n_rows: int | None = None, *, sigma: Any = None,
                     decay: str | None = None, signage: bool = True, poi_cell: Any = None,
                     recall_scope: str = "all") -> Any:
        """店の評価の記憶(``engine.store_memory.StoreMemory``)を持たせる(D-120 7a)。

        書き手はエピソードの書き手(:meth:`record`)に乗る=記憶の表と同じ回・同じ配列。想起できる店の
        τ は記憶の想起と同じ :attr:`tau`(宣言)。
        """
        from shibuya.engine.store_memory import DEFAULT_STORE_DECAY, STORE_MEMORY_N, StoreMemory

        self.store = StoreMemory(
            self.n, STORE_MEMORY_N if n_rows is None else int(n_rows),
            minutes_per_tick=self.minutes_per_tick, d=self.d, sigma=sigma,
            decay=DEFAULT_STORE_DECAY if decay is None else decay, signage=signage, poi_cell=poi_cell,
        )
        if str(recall_scope) not in STORE_RECALL_SCOPES:
            raise ValueError(f"store_recall_scope は {STORE_RECALL_SCOPES} のどれか(いま {recall_scope!r})")
        #: 7c: B5 の想起で店の行を候補にする入口(all=全入口・conversation=会話だけ=感度腕)。
        self.store_recall_scope = str(recall_scope)
        return self.store

    def store_rows(self, agents: Any, agent_id: int, tick: int) -> Any:
        """1 体の店の評価の行(``StoreRows``: poi・向き・精度・A・想起できるか)。7c の読み口。"""
        if self.store is None:
            raise RuntimeError("店の評価の記憶は --store-memory on のランだけ")
        return self.store.rows(agents, agent_id, tick, self.tau)

    def known_stores(self, agents: Any, agent_ids: np.ndarray, tick: int,
                     mask: np.ndarray | None = None, min_sign: int | None = None) -> np.ndarray:
        """体の配列 → ``(体, M)`` の想起できる店(A ≥ τ・``mask`` の店・向き ≥ ``min_sign``)の POI(他は −1)。"""
        if self.store is None:
            raise RuntimeError("店の評価の記憶は --store-memory on のランだけ")
        return self.store.known(agents, agent_ids, tick, self.tau, mask, min_sign)

    # ------------------------------------------------------------------ 読み口
    def scores(self, agents: Any, agent_ids: np.ndarray, tick: int) -> np.ndarray:
        """体の配列 → ``(体, N)`` の score(空行は −inf)。"""
        r = agents.registry
        a = np.asarray(agent_ids, dtype=np.int64)
        A = activation_rows(r.mem_n[a], r.mem_tick[a], tick, self.minutes_per_tick, self.d)
        s = self.w_r * A + self.w_i * r.mem_importance[a].astype(np.float64)
        s[r.mem_kind[a] == _EMPTY] = -np.inf
        return s.astype(np.float32)

    def top(self, agents: Any, agent_id: int, k: int, tick: int,
            mask: np.ndarray | None = None) -> np.ndarray:
        """1 体の score の上位 k 行(``mask`` で候補を絞る・空行は除く)→ 行番号の配列。"""
        s = self.scores(agents, np.asarray([int(agent_id)]), tick)[0].astype(np.float64)
        if mask is not None:
            s = np.where(np.asarray(mask, dtype=bool), s, -np.inf)
        order = np.argsort(-s, kind="stable")
        return order[np.isfinite(s[order])][: int(k)]

    # ------------------------------------------------------------------ 想起(6b)
    def recall(self, agents: Any, agent_id: int, tick: int, condition: int,
               inviter: int = -1) -> list[RecallItem]:
        """1 呼の想起(M4 (a)+修正 2・M5 (a)・M16 (a))→ 行(score の降順)。本段の描画が読む。

        1 体の N 行に対する配列演算だけ(体数に比例した逐次ループなし=P4)。
        """
        i = int(agent_id)
        r = agents.registry
        f = r.field
        kind = f("mem_kind")[i]
        used = kind != _EMPTY
        cond = int(condition)
        ok_cond = 0 <= cond < len(WAKE_CONDITION_CLASS)
        cls = WAKE_CONDITION_CLASS[cond] if ok_cond else EventClass.INDIVIDUAL
        conversation = cls == EventClass.CONVERSATION or cond == _COND_TURN
        k = RECALL_K_CONVERSATION if conversation else RECALL_K_OTHER
        entrance = _ENTRANCE_NAMES[cond] if 0 <= cond < len(_ENTRANCE_NAMES) else "UNKNOWN"
        rs = self.recall_stats
        rs["calls"] += 1
        rs["calls:" + entrance] += 1
        store_on = self.store is not None and (
            getattr(self, "store_recall_scope", "all") == "all" or conversation)
        s_used = (np.flatnonzero(agents.registry.sm_poi[i] >= 0) if store_on
                  else np.zeros(0, dtype=np.int64))
        if not bool(used.any()) and s_used.size == 0:
            rs["calls_empty_table"] += 1
            return []
        A = activation_rows(f("mem_n")[i], f("mem_tick")[i], tick, self.minutes_per_tick, self.d)
        score = self.w_r * A + self.w_i * f("mem_importance")[i]
        # ---- q ----
        q_cell = int(f("cell")[i])
        q_partner = int(inviter) if int(inviter) >= 0 else int(f("talk_partner")[i])
        has_intent = "intent_kind" in r
        ik = int(f("intent_kind")[i]) if has_intent else 0
        it = int(f("intent_target")[i]) if has_intent else -1
        if q_partner < 0 and ik == _INTENT_PERSON:
            q_partner = it
        if ik in _INTENT_POI:
            q_obj = it
        elif int(f("poi_ref")[i]) >= 0:
            q_obj = int(f("poi_ref")[i])
        else:
            q_obj = int(f("queue_poi")[i])
        q_kind = ACTION_KIND.get(int(f("last_action")[i]), 0)
        q_result = int(f("last_result")[i])
        m_obj = f("mem_object")[i]
        match = np.zeros(kind.size, dtype=bool)
        if q_partner >= 0:
            match |= f("mem_partner")[i] == q_partner
        if q_obj >= 0:
            match |= m_obj == q_obj
        if q_cell >= 0:
            match |= (f("mem_cell")[i] == q_cell) | (m_obj == int(place_thing(q_cell)))
        if q_kind > 0 and 0 <= q_result <= 255:
            match |= (kind == q_kind) & (f("mem_result")[i] == q_result)
        match &= used
        live = used & (A >= self.tau)
        rs["rows_candidate"] += int(np.count_nonzero(match))
        rs["rows_candidate_below_tau"] += int(np.count_nonzero(match & ~live))
        rs["rows_used"] += int(np.count_nonzero(used))
        rs["rows_used_below_tau"] += int(np.count_nonzero(used & ~live))
        if store_on:
            return self._recall_with_store(agents, i, tick, k, entrance, score, match, live, s_used,
                                           q_obj, q_cell)
        cand = np.flatnonzero(match & live)
        cand = cand[np.lexsort((cand, -score[cand]))][:k]
        picked = list(cand.tolist())
        if len(picked) < k:
            rest = np.flatnonzero(live & ~match)
            rest = rest[np.lexsort((rest, -score[rest]))][: k - len(picked)]
            if rest.size:
                rs["filled_rows"] += int(rest.size)
                rs["calls_filled"] += 1
            picked += rest.tolist()
        rs["recalled_rows"] += len(picked)
        rs["recalled_rows:" + entrance] += len(picked)
        if not picked:
            rs["calls_zero"] += 1
            return []
        last, part, res, cel = f("mem_last")[i], f("mem_partner")[i], f("mem_result")[i], f("mem_cell")[i]
        out = [
            RecallItem(
                row=int(j), last_tick=int(last[j]), kind=int(kind[j]), partner=int(part[j]),
                obj=int(m_obj[j]), result=int(res[j]), cell=int(cel[j]),
                gist=self.gist.get((i, int(j)), ""),
            )
            for j in picked  # 高々 k(≤ 3)
        ]
        for it_ in out:
            rs["recalled_kind:" + str(KIND_NAMES.get(it_.kind, it_.kind))] += 1
        return out

    def _recall_with_store(self, agents: Any, i: int, tick: int, k: int, entrance: str,
                           score: np.ndarray, match: np.ndarray, live: np.ndarray, s_used: np.ndarray,
                           q_obj: int, q_cell: int) -> list[RecallItem]:
        """7c: エピソードと店の評価の行を**同じ score 順**に競わせて k 件(店の行の score=A+0.5×min(4, 精度))。

        店の行の一致=店が q の対象(POI)か店のセルが現在セル。一致した行(両方)→ score 順 → 足りなければ
        残り(両方)から score 順(``A ≥ τ`` の行だけ)。同じ店のエピソード(購入/食事/並ぶ/看板)と店の行は
        先に選んだ方だけ載せる(宣言)。配列演算だけ(≤ N+32 行)。
        """
        from shibuya.engine.store_memory import STORE_SCORE_P_CAP, STORE_SCORE_W_P

        rs = self.recall_stats
        f = agents.registry.field
        st = self.store
        sA = st.activation(agents, np.asarray([i]), tick)[0][s_used]
        s_poi = f("sm_poi")[i][s_used].astype(np.int64)
        s_prec = f("sm_precision")[i][s_used].astype(np.float64)
        s_score = sA + STORE_SCORE_W_P * np.minimum(STORE_SCORE_P_CAP, s_prec)
        s_live = sA >= self.tau
        s_match = np.zeros(s_used.size, dtype=bool)
        if q_obj >= 0:
            s_match |= s_poi == q_obj
        if q_cell >= 0 and st.poi_cell is not None:
            inside = (s_poi >= 0) & (s_poi < st.poi_cell.size)
            s_match |= inside & (st.poi_cell[np.where(inside, s_poi, 0)] == q_cell)
        rs["store_rows_candidate"] += int(np.count_nonzero(s_match))
        rs["store_rows_used"] += int(s_used.size)
        rs["store_rows_used_below_tau"] += int(np.count_nonzero(~s_live))
        m_obj = f("mem_object")[i].astype(np.int64)
        kind = f("mem_kind")[i].astype(np.int64)
        shop_like = ((kind >= 1) & (kind <= 3)) | (kind == 11)  # _SHOP_OBJ_KINDS(購入/食事/並ぶ/看板)
        ep_key = np.where(shop_like & (m_obj >= 0), m_obj, -1)

        def pool(ep_mask: np.ndarray, st_mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
            """(種類 0=エピソード/1=店, 行) を score の降順 → 種類 → 行 の順に(配列演算)。"""
            e = np.flatnonzero(ep_mask)
            s = np.flatnonzero(st_mask)
            sc_ = np.concatenate([score[e], s_score[s]])
            ty = np.concatenate([np.zeros(e.size, dtype=np.int64), np.ones(s.size, dtype=np.int64)])
            ix = np.concatenate([e, s]).astype(np.int64)
            order = np.lexsort((ix, ty, -sc_))
            return ty[order], ix[order]

        picked: list[tuple[int, int]] = []
        keys: set[int] = set()
        n_match = 0
        for (tys, ixs), is_fill in ((pool(match & live, s_match & s_live), False),
                                    (pool(live & ~match, s_live & ~s_match), True)):
            for typ, j in zip(tys.tolist(), ixs.tolist()):  # 逐次: k 件で止まる(同じ店の重なりは飛ばす)
                if len(picked) >= k:
                    break
                key = int(ep_key[j]) if typ == 0 else int(s_poi[j])
                if key >= 0 and key in keys:
                    rs["store_dedup_skipped"] += 1
                    continue
                picked.append((typ, j))
                if key >= 0:
                    keys.add(key)
                if is_fill:
                    rs["filled_rows"] += 1
                else:
                    n_match += 1
        if len(picked) > n_match:
            rs["calls_filled"] += 1
        rs["recalled_rows"] += len(picked)
        rs["recalled_rows:" + entrance] += len(picked)
        if not picked:
            rs["calls_zero"] += 1
            return []
        last, part, res, cel = f("mem_last")[i], f("mem_partner")[i], f("mem_result")[i], f("mem_cell")[i]
        s_last = f("sm_last")[i]
        s_src = f("sm_source")[i]
        s_sign = (np.sign(st.valence_now(agents, np.asarray([i]), tick)[0]).astype(np.int64)
                  if any(typ == 1 for typ, _ in picked) else None)
        out: list[RecallItem] = []
        for typ, j in picked:  # 高々 k(≤ 3)
            if typ == 0:
                out.append(RecallItem(
                    row=int(j), last_tick=int(last[j]), kind=int(kind[j]), partner=int(part[j]),
                    obj=int(m_obj[j]), result=int(res[j]), cell=int(cel[j]),
                    gist=self.gist.get((i, int(j)), ""),
                ))
                rs["recalled_kind:" + str(KIND_NAMES.get(int(kind[j]), int(kind[j])))] += 1
            else:
                row = int(s_used[j])
                pc = (int(st.poi_cell[s_poi[j]]) if st.poi_cell is not None
                      and 0 <= s_poi[j] < st.poi_cell.size else -1)
                out.append(RecallItem(
                    row=self.n_rows + row, last_tick=int(s_last[row]), kind=STORE_ITEM_KIND, partner=-1,
                    obj=int(s_poi[j]), result=0, cell=pc, gist="", valence=int(s_sign[row]),
                    source=int(s_src[row]),
                ))
                rs["recalled_kind:store"] += 1
        return out

    # ------------------------------------------------------------------ 書き手の本体
    def _write(self, agents: Any, tick: int, a: np.ndarray, kind: np.ndarray, partner: np.ndarray,
               obj: np.ndarray, result: np.ndarray, cell: np.ndarray) -> np.ndarray:
        """1 体 1 件の事象を統合/新規/追い出しで 1 行に書く(配列演算)→ 書いた行番号。"""
        r = agents.registry
        rk = r.mem_kind[a].astype(np.int64)
        hit = ((rk == kind[:, None]) & (r.mem_partner[a].astype(np.int64) == partner[:, None])
               & (r.mem_object[a].astype(np.int64) == obj[:, None])
               & (r.mem_result[a].astype(np.int64) == result[:, None]) & (rk != _EMPTY))
        found = hit.any(axis=1)
        slot = np.where(found, np.argmax(hit, axis=1), -1)
        empty = rk == _EMPTY
        new = ~found
        has_empty = empty.any(axis=1)
        use_empty = new & has_empty
        slot = np.where(use_empty, np.argmax(empty, axis=1), slot)
        evict = new & ~has_empty
        if bool(evict.any()):
            s = self.scores(agents, a[evict], tick).astype(np.float64)
            slot[evict] = np.argmin(s, axis=1)  # 同点は行番号の小さい方
            self.stats["evictions"] += int(np.count_nonzero(evict))
            for x, y in zip(a[evict].tolist(), slot[evict].tolist()):  # 追い出した行の要旨を消す
                self._drop_gist(int(x), int(y))
        old_n = r.mem_n[a, slot].astype(np.int64)
        n = np.where(found, np.minimum(old_n + 1, 65_535), 1)
        first_tick = np.where(found, r.mem_tick[a, slot].astype(np.int64), int(tick))
        # 第294 Q56: 統合(同じ鍵の反復)は「初回 +1」を外して base に戻す・新しい行は初回 +1
        imp = importance_of(kind, result, ~found)
        R.write_memory(agents, a, slot, kind, first_tick, np.full(a.size, int(tick)), cell, partner,
                       obj, result, imp, n)
        self.stats["merged"] += int(np.count_nonzero(found))
        self.stats["new_rows"] += int(np.count_nonzero(new))
        return slot

    def record(self, agents: Any, tick: int, a: np.ndarray, kind: np.ndarray, partner: np.ndarray,
               obj: np.ndarray, result: np.ndarray, cell: np.ndarray) -> np.ndarray:
        """事象の配列 → 表へ(体ごとに 1 件ずつの回に分ける)→ 各事象の行番号(入力の並び)。"""
        a = np.asarray(a, dtype=np.int64)
        out = np.full(a.size, -1, dtype=np.int64)
        if a.size == 0:
            return out
        kind = np.asarray(kind, dtype=np.int64)
        partner = np.asarray(partner, dtype=np.int64)
        obj = np.asarray(obj, dtype=np.int64)
        result = np.asarray(result, dtype=np.int64)
        cell = np.asarray(cell, dtype=np.int64)
        for k, c in Counter(kind.tolist()).items():  # 種類の数ぶん(≤ 11)
            self.stats[f"events:{KIND_NAMES.get(int(k), k)}"] += int(c)
        fail = result != int(ResultCode.OK)
        if bool(fail.any()):
            for code, c in Counter(result[fail].tolist()).items():  # 結果コードの数ぶん
                self.stats[f"failures:{ResultCode(int(code)).name}"] += int(c)
        order = np.lexsort((np.arange(a.size), a))
        sa = a[order]
        starts = np.flatnonzero(np.concatenate(([True], sa[1:] != sa[:-1])))
        rank = np.empty(a.size, dtype=np.int64)
        rank[order] = np.arange(a.size) - np.repeat(starts, np.diff(np.append(starts, a.size)))
        # 逐次ループ宣言 1: 体あたりの事象の件数の最大ぶん
        for rnd in range(int(rank.max()) + 1):
            sel = np.flatnonzero(rank == rnd)
            out[sel] = self._write(agents, tick, a[sel], kind[sel], partner[sel], obj[sel],
                                   result[sel], cell[sel])
        if self.store is not None:  # D-120 7a: 同じエピソードの配列から店の評価の行へ
            self.store.on_episodes(agents, tick, a, kind, obj, result)
        return out

    # ------------------------------------------------------------------ 会話の要旨
    def _drop_gist(self, agent: int, row: int) -> None:
        if self.gist.pop((agent, row), None) is not None:
            self._gist_order.get(agent, OrderedDict()).pop(row, None)

    def _put_gist(self, agent: int, row: int, text: str) -> None:
        od = self._gist_order.setdefault(agent, OrderedDict())
        od.pop(row, None)
        od[row] = None
        self.gist[(agent, row)] = text
        while len(od) > GIST_PER_AGENT:  # 体あたり 16 件まで(古い順に落とす)
            old, _ = od.popitem(last=False)
            self.gist.pop((agent, old), None)
            self.stats["gist_dropped"] += 1

    def note_utterance(self, agents: Any, agent_id: int, tick: int, session: Any,
                       comment: str, reason: str = "") -> None:
        """発話 1 回(``conv.utterance`` の戻りのセッション)→ 会話の行の ``mem_n``+1・最初の要旨。

        要旨の源(第294 の親の暫定・Q57): 空でない「ひと言」(v1/v2)・無ければ理由欄(v3)。
        """
        if session is None:
            return
        key = self._session_key.get((int(agent_id), int(session.session_id)))
        if key is None:
            return
        partner, shop = key
        rows = self.record(agents, tick, np.asarray([int(agent_id)]),
                           np.asarray([EVENT_KINDS["talk"]]), np.asarray([partner]),
                           np.asarray([shop]), np.asarray([int(ResultCode.OK)]),
                           np.asarray([int(agents.registry.cell[int(agent_id)])]))
        self.stats["utterances"] += 1
        text = str(comment or "").strip()
        sk = (int(agent_id), int(session.session_id))
        if not text or text == "なし":
            self.stats["utterances_without_comment"] += 1
            text = str(reason or "").strip()
            if text:
                self.stats["gist_source:reason"] += 1
        else:
            self.stats["gist_source:comment"] += 1
        if not text or text == "なし":
            return
        if sk in self._gist_done:
            return
        self._gist_done.add(sk)
        self._put_gist(int(agent_id), int(rows[0]), text[:GIST_CHARS])
        self.stats["gists"] += 1

    # ------------------------------------------------------------------ 1 tick の記録
    def after_tick(
        self,
        agents: Any,
        tick: int,
        *,
        applied: Sequence[tuple[np.ndarray, np.ndarray]] = (),
        visits: tuple[Sequence[np.ndarray], Sequence[np.ndarray]] | None = None,
        arrived: Sequence[np.ndarray] = (),
        conv: Any = None,
        salient_events: Sequence[Any] = (),
        signage: Sequence[tuple[int, int]] | None = None,
    ) -> None:
        """この tick の事象を記録する(Phase C・活動層・意図の層の後・親しみの表の前に 1 回)。

        Args:
            applied: この tick に適用した intent の ``(体, 対象)`` の組(確定と落選)。対象は行動語で
                意味が変わる(POI / セル / 相手)。
            visits: 購入/食事の成立した ``(体, POI)``(``ResolveOutcome.visit_agents/visit_pois``)。
            arrived: エンジン継続で**着いた**体(``ResolveOutcome.arrived_agents``)。
            conv: 会話の管理(この tick に開いたセッションを読む)。
            salient_events: この tick の顕著行為(``.cell``・``.noticed``)。
            signage: p_see を通って B2 に看板行が載った ``(体, POI)``(``Renderer.signage_exposures``)。
        """
        from shibuya.engine import commit as C

        t = int(tick)
        r = agents.registry
        cell_now = np.asarray(r.cell, dtype=np.int64)
        parts: list[tuple[np.ndarray, ...]] = []
        # ---- (a) 行動の成否(その tick に結果が書かれた体) ----
        touched: list[np.ndarray] = []
        for ag, tg in applied:  # 確定と落選の 2 本
            ag = np.asarray(ag, dtype=np.int64)
            if ag.size:
                self._target[ag] = np.asarray(tg, dtype=np.int64)
                touched.append(ag)
        ids = np.flatnonzero(np.asarray(r.last_result_tick) == t)
        if ids.size:
            act = np.asarray(r.last_action, dtype=np.int64)[ids]
            res = np.asarray(r.last_result, dtype=np.int64)[ids]
            kind = np.fromiter((ACTION_KIND.get(int(x), 0) for x in act.tolist()),
                               dtype=np.int64, count=ids.size)  # 結果の書かれた体の数ぶん
            ok = res == int(ResultCode.OK)
            keep = (kind > 0) & ~(ok & ((kind == EVENT_KINDS["move"]) | (kind == EVENT_KINDS["talk"])))
            ids, kind, res = ids[keep], kind[keep], res[keep]
            tgt = self._target[ids]
            partner = np.full(ids.size, -1, dtype=np.int64)
            obj = np.full(ids.size, -1, dtype=np.int64)
            shop = np.isin(kind, (EVENT_KINDS["buy"], EVENT_KINDS["eat"], EVENT_KINDS["queue"]))
            poi_ref = np.asarray(r.poi_ref, dtype=np.int64)[ids]
            queue_poi = np.asarray(r.queue_poi, dtype=np.int64)[ids]
            obj[shop] = np.where(tgt[shop] >= 0, tgt[shop],
                                 np.where(poi_ref[shop] >= 0, poi_ref[shop], queue_poi[shop]))
            mv = kind == EVENT_KINDS["move"]
            obj[mv] = np.where(tgt[mv] >= 0, place_thing(np.maximum(tgt[mv], 0)), -1)
            tk = kind == EVENT_KINDS["talk"]
            partner[tk] = tgt[tk]
            obj[tk] = np.where(poi_ref[tk] >= 0, poi_ref[tk], -1)
            hp = kind == EVENT_KINDS["help"]
            partner[hp] = tgt[hp]
            here = np.isin(kind, (EVENT_KINDS["sleep"], EVENT_KINDS["report"]))
            obj[here] = np.where(cell_now[ids[here]] >= 0,
                                 place_thing(np.maximum(cell_now[ids[here]], 0)), -1)
            if visits is not None and len(visits[0]):  # 成立した行の店は訪問の控えが正
                va = np.concatenate([np.asarray(x, dtype=np.int64) for x in visits[0]])
                vp = np.concatenate([np.asarray(x, dtype=np.int64) for x in visits[1]])
                self._target[va] = vp
                sv = shop & (res == int(ResultCode.OK))
                obj[sv] = np.where(self._target[ids[sv]] >= 0, self._target[ids[sv]], obj[sv])
                touched.append(va)
            parts.append((ids, kind, partner, obj, res, cell_now[ids]))
        for ag in touched:
            self._target[ag] = -1
        # ---- (a′) 移動の到着 ----
        if arrived:
            arr = np.unique(np.concatenate([np.asarray(x, dtype=np.int64) for x in arrived]))
            arr = arr[cell_now[arr] >= 0]
            if arr.size:
                parts.append((arr, np.full(arr.size, EVENT_KINDS["move"]), np.full(arr.size, -1),
                              place_thing(cell_now[arr]), np.full(arr.size, int(ResultCode.OK)),
                              cell_now[arr]))
        # ---- (b) 会話: この tick に開いたセッションの参加者ごとに 1 行 ----
        if conv is not None:
            upto = int(getattr(conv, "n_opened", 0))
            for sid in range(self._next_session, upto):  # 逐次ループ宣言 2: 開いたセッションの数ぶん
                s = conv.sessions.get(sid)
                if s is None:
                    continue
                ps = [int(p) for p in s.participants]
                for p in ps:
                    other = next((q for q in ps if q != p), -1)
                    ref = int(r.poi_ref[p])
                    shop_id = ref if ref >= 0 else -1
                    self._session_key[(p, int(sid))] = (other, shop_id)
                    parts.append((np.asarray([p]), np.asarray([EVENT_KINDS["talk"]]),
                                  np.asarray([other]), np.asarray([shop_id]),
                                  np.asarray([int(ResultCode.OK)]), np.asarray([int(cell_now[p])])))
                self.stats["sessions"] += 1
            self._next_session = upto
        # ---- (c) 気づき ----
        for ev in salient_events:  # 逐次ループ宣言 3: 顕著行為の件数ぶん
            got = np.asarray(getattr(ev, "noticed", ()), dtype=np.int64)
            if got.size:
                c = int(getattr(ev, "cell", -1))
                parts.append((got, np.full(got.size, EVENT_KINDS["notice"]), np.full(got.size, -1),
                              np.full(got.size, place_thing(np.asarray([max(c, 0)]))[0] if c >= 0 else -1),
                              np.full(got.size, int(ResultCode.OK)), np.full(got.size, c)))
        # ---- (d) 強い看板=初見だけ ----
        if signage:
            pairs = sorted(set((int(x), int(y)) for x, y in signage))  # 逐次ループ宣言 4: 露出の件数ぶん
            sa = np.fromiter((x for x, _ in pairs), dtype=np.int64, count=len(pairs))
            sp = np.fromiter((y for _, y in pairs), dtype=np.int64, count=len(pairs))
            self.stats["signage_exposures_seen"] += int(sa.size)
            # 第294 Q58: 記憶の表で判定(描画による露出=意識的な初見・親しみの表は使わない)
            known = ((r.mem_kind[sa].astype(np.int64) == EVENT_KINDS["signage"])
                     & (r.mem_object[sa].astype(np.int64) == sp[:, None])).any(axis=1)
            first = ~known
            if bool(first.any()):
                fa, fp = sa[first], sp[first]
                parts.append((fa, np.full(fa.size, EVENT_KINDS["signage"]), np.full(fa.size, -1), fp,
                              np.full(fa.size, int(ResultCode.OK)), cell_now[fa]))
        if not parts:
            return
        cat = [np.concatenate([np.asarray(p[j], dtype=np.int64) for p in parts]) for j in range(6)]
        self.record(agents, t, *cat)

    # ------------------------------------------------------------------ 監査
    def summary(self, agents: Any, tick: int) -> dict[str, Any]:
        """manifest ``memory``: 件数・行の使用・種類の内訳・A と importance の分布・要旨。"""
        r = agents.registry
        used = r.mem_kind != _EMPTY
        rows_per = used.sum(axis=1)
        A = activation_rows(r.mem_n, r.mem_tick, tick, self.minutes_per_tick, self.d)

        def q(x: np.ndarray) -> dict[str, float]:
            x = np.asarray(x, dtype=np.float64)
            if x.size == 0:
                return {}
            return {p: round(float(np.percentile(x, float(p[1:]))), 4)
                    for p in ("p0", "p10", "p50", "p90", "p99", "p100")} | {"mean": round(float(x.mean()), 4)}

        kinds = r.mem_kind[used].astype(np.int64)
        res = r.mem_result[used].astype(np.int64)
        rs = {k: int(v) for k, v in sorted(self.recall_stats.items())}
        calls = max(1, rs.get("calls", 0))
        recall = {
            "tau": float(self.tau),
            "k_conversation": RECALL_K_CONVERSATION, "k_other": RECALL_K_OTHER,
            "counts": rs,
            "recalled_rows_per_call": round(rs.get("recalled_rows", 0) / calls, 4),
            # 呼の 3 分け: 表が空(まだ何も記録していない)/ 表はあるが 0 件(τ で全部切れた)/ 1 件以上
            "empty_table_share": round(rs.get("calls_empty_table", 0) / calls, 4),
            "zero_recall_share": round(rs.get("calls_zero", 0) / calls, 4),
            "recalled_call_share": round(
                (rs.get("calls", 0) - rs.get("calls_empty_table", 0) - rs.get("calls_zero", 0)) / calls, 4),
            "filled_call_share": round(rs.get("calls_filled", 0) / calls, 4),
            "candidate_below_tau_share": round(
                rs.get("rows_candidate_below_tau", 0) / max(1, rs.get("rows_candidate", 0)), 4),
            "used_below_tau_share": round(
                rs.get("rows_used_below_tau", 0) / max(1, rs.get("rows_used", 0)), 4),
        }
        return {
            "recall": recall,
            "k2_motif_repeats": self._k2(agents),
            "k5_failure_avoidance": self._k5(agents),
            "n_rows": int(self.n_rows),
            "d": float(self.d), "w_r": float(self.w_r), "w_i": float(self.w_i),
            "row_bytes_actual": 25, "row_bytes_declared": int(MEMORY_ROW_BYTES_DECLARED),
            "counts": {k: int(v) for k, v in sorted(self.stats.items())},
            "rows_used_per_agent": q(rows_per),
            "full_agents": int(np.count_nonzero(rows_per == self.n_rows)),
            "agents_with_rows": int(np.count_nonzero(rows_per > 0)),
            "rows_by_kind": {KIND_NAMES.get(int(k), str(k)): int(v)
                             for k, v in sorted(Counter(kinds.tolist()).items())},
            "failure_rows_by_result": {ResultCode(int(k)).name: int(v)
                                       for k, v in sorted(Counter(res[res != 0].tolist()).items())},
            "importance": {str(k): int(v) for k, v in sorted(
                Counter(r.mem_importance[used].astype(np.int64).tolist()).items())},
            "n_per_row": q(r.mem_n[used]),
            "A": q(A[used]),
            "A_by_kind": {KIND_NAMES.get(int(k), str(k)): q(A[used][kinds == k])
                          for k in sorted(set(kinds.tolist()))},
            "score": q((self.w_r * A + self.w_i * r.mem_importance.astype(np.float64))[used]),
            "gists": int(len(self.gist)),
            "gist_agents": int(len(self._gist_order)),
        }

    def _k2(self, agents: Any) -> dict[str, Any]:
        """K-2 の材料: 同じ鍵の再出現(Σ(n−1))と、同じ件数を種類ごとの鍵の母集団から一様に引いた期待。"""
        r = agents.registry
        used = r.mem_kind != _EMPTY
        out: dict[str, Any] = {}
        obs_all = 0.0
        exp_all = 0.0
        for kd in sorted(set(r.mem_kind[used].astype(np.int64).tolist())):  # 種類の数ぶん(≤ 11)
            m = used & (r.mem_kind == kd)
            keys = np.stack([r.mem_partner[m].astype(np.int64), r.mem_object[m].astype(np.int64),
                             r.mem_result[m].astype(np.int64)], axis=1)
            U = int(np.unique(keys, axis=0).shape[0])
            e = (r.mem_n.astype(np.int64) * m).sum(axis=1)
            d = m.sum(axis=1)
            obs = float((e - d).sum())
            ee = e[e > 0].astype(np.float64)
            exp = float((ee - U * (1.0 - (1.0 - 1.0 / max(U, 1)) ** ee)).sum()) if U > 0 else 0.0
            out[KIND_NAMES.get(int(kd), str(kd))] = {
                "events": int(e.sum()), "rows": int(d.sum()), "key_universe": U,
                "repeats": int(obs), "repeats_expected_uniform": round(exp, 2),
                "ratio": round(obs / exp, 3) if exp > 0 else None,
            }
            obs_all += obs
            exp_all += exp
        out["all"] = {"repeats": int(obs_all), "repeats_expected_uniform": round(exp_all, 2),
                      "ratio": round(obs_all / exp_all, 3) if exp_all > 0 else None,
                      "gate_k2": ">= 10x (M15 (c)・判定は複数日+実 LLM の後)"}
        return out

    def _k5(self, agents: Any) -> dict[str, Any]:
        """K-5(失敗の回避・修正 4)の計器: 失敗の記憶(REFUSED/CLOSED/OUT_OF_STOCK/TRAIN_FULL/PARTNER_BUSY)
        がある相手/対象への**再訪**(同じ相手か対象の行で、その失敗より後の tick に最後の出来事があるもの。
        同じ失敗の反復=n>1 も再訪・相手も対象も無い行はセルで照合)の件数と率を、成功の記憶(購入・食事・
        並ぶ・会話・乗車の成功)と並べる。"""
        r = agents.registry
        used = r.mem_kind != _EMPTY
        shop_like = np.isin(r.mem_kind, (EVENT_KINDS["buy"], EVENT_KINDS["eat"], EVENT_KINDS["queue"],
                                          EVENT_KINDS["talk"], EVENT_KINDS["board"]))
        fail = used & np.isin(r.mem_result, K5_FAILURES)
        succ = used & shop_like & (r.mem_result == int(ResultCode.OK))
        counts = {"fail": [0, 0], "success": [0, 0]}
        by_result: Counter = Counter()
        by_result_rev: Counter = Counter()
        rows_any = np.flatnonzero((fail | succ).any(axis=1))
        for a in rows_any.tolist():  # 逐次ループ宣言 6: 行のある体の数ぶん(ランの終わりに 1 回)
            part = r.mem_partner[a].astype(np.int64)
            obj = r.mem_object[a].astype(np.int64)
            cel = r.mem_cell[a].astype(np.int64)
            first = r.mem_tick[a].astype(np.int64)
            last = r.mem_last[a].astype(np.int64)
            n = r.mem_n[a].astype(np.int64)
            for label, mask in (("fail", fail[a]), ("success", succ[a])):
                for j in np.flatnonzero(mask).tolist():
                    # 相手 > 対象 > セル(相手も対象も無い行はその場所)
                    tgt_same = ((part == part[j]) if part[j] >= 0
                                else (obj == obj[j]) if obj[j] != -1 else (cel == cel[j]))
                    later = tgt_same & used[a] & (last > first[j])
                    later[j] = n[j] > 1
                    rev = bool(later.any())
                    counts[label][0] += 1
                    counts[label][1] += int(rev)
                    if label == "fail":
                        name = ResultCode(int(r.mem_result[a, j])).name
                        by_result[name] += 1
                        by_result_rev[name] += int(rev)
        rate = {k: (round(v[1] / v[0], 4) if v[0] else None) for k, v in counts.items()}
        return {
            "failure_memories": counts["fail"][0], "failure_revisits": counts["fail"][1],
            "failure_revisit_rate": rate["fail"],
            "success_memories": counts["success"][0], "success_revisits": counts["success"][1],
            "success_revisit_rate": rate["success"],
            "failure_by_result": {k: {"memories": v, "revisits": by_result_rev[k]}
                                  for k, v in sorted(by_result.items())},
            "gate_k5": "failure_revisit_rate < success_revisit_rate (M15 修正 4・判定は複数日+実 LLM の後)",
        }

    def gist_bytes(self) -> int:
        """要旨の実バイト(UTF-8)。"""
        return int(sum(len(v.encode("utf-8")) for v in self.gist.values()))

