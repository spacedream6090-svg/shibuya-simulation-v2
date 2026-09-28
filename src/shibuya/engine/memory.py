"""engine.memory — 記憶 第 1 段の **記録**(6 段目 6a・D-95・記憶アジェンダ v1 M1〜M4・M13・M16・修正 1・第294)。

正典: ``docs/design/v2-memory-stage1-implementation-agenda.md`` §1(段 6a の 1〜9)・§4。上位=
``docs/design/v2-memory-agenda.md`` v1(M1〜M16 の決定と修正 1・2・4)。事実=
``docs/research/v2-r48-own-code-memory-range-return.md`` §B1(記憶は無い・会話の本文は捨てている)。
#56 の ``engine.familiarity``(親しみの表)と同じ流儀(腕でだけ確保・書き手は resolve・A の近似)。

本段は**記録と読み口だけ**(誰も読まない=想起と B5 の記憶行は 6b)。

表(``AgentState(memory_columns=True)`` のランだけ確保・``--memory on``)
    体ごとに N 行(:data:`MEMORY_N`=128・M2・感度 64/256)。1 行=``mem_kind`` u8(事象の種類=
    :data:`EVENT_KINDS`・0=空行)・``mem_tick`` i32(最初)・``mem_last`` i32(最後)・``mem_cell`` i32・
    ``mem_partner`` i32(体 id・−1)・``mem_object`` i32(#56 と同じ符号化=POI ≥0 / 場所 −(cell+2) /
    人 1<<30|id / −1。会話の行では**店 ID**=会話を始めたときの在席 POI・無ければ −1=M1 の決定)・
    ``mem_result`` u8(``ResultCode``)・``mem_importance`` u8・``mem_n`` u16(同じ鍵の反復=A の n)=
    **実 25 B/行**(宣言は 32 B/行=詰め物 7 B は予算の側に置く=配列は確保しない)。

会話の要旨(M1 (b))
    SoA の外(``MemoryLayer.gist[(体, 行)]``)。体あたり上限 :data:`GIST_PER_AGENT`=16 件(古い順に
    落とす)・:data:`GIST_CHARS`=40 字=**自分の発話の「ひと言」欄の先頭 40 字**(その会話で最初の
    空でない ひと言)。相手の発話は持たない。

書き手(:meth:`MemoryLayer.after_tick`・tick の Phase C と活動層・意図の層の後・親しみの表の前)
    (a) **行動の成否**: その tick に結果(``last_result_tick == tick``)が書かれた体の ``last_action`` ×
        ``last_result``(:data:`ACTION_KIND`)。移動の成功は「着いた」(エンジン継続の到着)だけ・会話の
        成功は (b) の会話の行だけ(二重にしない)。
    (b) **会話**: 開いたセッションの参加者ごとに 1 行(相手・店 ID)。発話ごとに ``mem_n``+1。
    (c) **気づき**: その tick の顕著行為に気づいた体(``SalientProcess.events[].noticed``)に 1 行
        (object=事象のセルの場所=顕著行為に主の体 id は無い=宣言)。
    (d) **強い看板**(修正 1 の二本立て): p_see を通って B2 に看板行が載った (体, POI) のうち **初見**
        (親しみの表にその POI の行が無い・表が無いランは記憶の表に看板の行が無い)だけ。
    (e) 記録しない(宣言): 内受容の跨ぎ・範囲外の食事・p_see の通過(露出=#56)・移動の各 tick・
        移動の開始・「なし」・待機/休憩/退去/断る。
    統合=同じ鍵(kind・partner・object・result)は新しい行を作らず ``mem_n``+1・``mem_last`` 更新。

importance 固定表(M3 (b)): 失敗 3・会話 2・成功 1・気づき 1・強い看板 1・初回(その鍵の最初の行)+1・
上限 4(:data:`IMPORTANCE`)。

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
"""

from __future__ import annotations

from collections import Counter, OrderedDict
from typing import Any, Final, Sequence

import numpy as np

from shibuya.agents.state import ResultCode
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
        imp = np.where(found, r.mem_importance[a, slot].astype(np.int64),
                       importance_of(kind, result, np.ones(a.size, dtype=bool)))
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
                       comment: str) -> None:
        """発話 1 回(``conv.utterance`` の戻りのセッション)→ 会話の行の ``mem_n``+1・最初の要旨。"""
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
            if "fam_thing" in r.arrays:
                known = (r.fam_thing[sa].astype(np.int64) == sp[:, None]).any(axis=1)
                self.stats["signage_first_sight_rule:familiarity"] += 1
            else:
                known = ((r.mem_kind[sa].astype(np.int64) == EVENT_KINDS["signage"])
                         & (r.mem_object[sa].astype(np.int64) == sp[:, None])).any(axis=1)
                self.stats["signage_first_sight_rule:memory"] += 1
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
        return {
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

    def gist_bytes(self) -> int:
        """要旨の実バイト(UTF-8)。"""
        return int(sum(len(v.encode("utf-8")) for v in self.gist.values()))

