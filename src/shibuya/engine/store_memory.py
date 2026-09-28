"""engine.store_memory — **店の評価の記憶**(D-120 7a・N1 (a)・N2 (i)(iii)・N4 (a)・N5 (a)・第296)。

正典: ``docs/design/v2-store-memory-implementation-agenda.md`` §1(段 7a の 1〜7)・§4。上位=
``docs/design/v2-memory-wom-internet-draft.md`` §1(1-1 錨・1-2 案・1-5 N1〜N8=ユーザー決定 全部 (a))。
入れ物は記憶 第 1 段と同じ(``engine.memory.MemoryLayer`` が持つ・腕でだけ確保・書き手は resolve・
A の近似)。**本段では誰も読まない**(7c で選び手と B5 が読む)。M17 の潜在的な親しみの接続と
ネット(D-121)は含めない(出どころ「ネット」のビットと σ の枠だけ予約)。

表(``AgentState(store_memory_columns=True)`` のランだけ確保・``--store-memory on``)
    体ごとに M 行(:data:`STORE_MEMORY_N`=32・感度 16/64)。1 行=``sm_poi`` i32(POI 索引・−1=空行)・
    ``sm_valence`` f32(Σ 精度 × 向き)・``sm_precision`` f32(Σ 1/σ²)・``sm_first`` i32(最初の tick=
    A の起点)・``sm_last`` i32(最後の tick)・``sm_n`` u16(更新回数=A の n)・``sm_source`` u8(出どころの
    ビットの和: 1 自分/2 伝聞/4 看板/8 ネット)=**実 23 B/行**(アジェンダ §1-1 の「19 B」は ``sm_last`` を
    数え落とし=問い)→ **宣言 24 B/行 → 768 B/体**(詰め物 1 B は予算の側)。同じ POI は 1 行に統合。

書き手(:meth:`StoreMemory.on_episodes`=``MemoryLayer.record`` がエピソードを書いた直後に同じ配列で呼ぶ)
    (i) **自分の訪問**(N2 (a)): エピソードの kind=購入/食事/並ぶ・object=POI(≥0)→ 同じ POI の行へ
        向き=結果コードから(``OK`` +1(**並ぶの成功は 0**=第296 Q77・続く購入/食事の成功と合わせて 1 回の
        訪問で +1 を 2 回得ない)・``OUT_OF_STOCK``/``CLOSED``/``LOST_ARBITRATION``/``TOO_FAR`` −1・
        それ以外 0)・出どころ=自分。LLM に評価を書かせない(M10)。統合(同じ鍵の反復)のエピソードも
        1 回の証拠として足す(訪問ごとに 1 件)。
    (iii) **看板**(修正 1 の二本立て): 記憶の表に「看板の初見」のエピソード(kind=11)が立ったときだけ・
        向き 0(知っているだけ)・出どころ=看板。p_see の通過そのもの(#56 の露出=潜在)は書かない。
    (ii) 伝聞=7b・(iv) ネット=D-121(ビットの予約だけ)。

精度(N4 (a)・宣言・expedient)
    σ 自分 1・伝聞 2・看板 4・ネット 2(:data:`STORE_SIGMA`)→ 1 件ごとに ``precision += 1/σ²``・
    ``valence += (1/σ²) × 向き``。読むときの向き=``sign(valence)``・確からしさ=``precision``。
    感度腕は ``--store-sigma '<json>'``(σ の値で渡す: 1:1:1:1 / 1:4:16:4 …)。

減衰(N5 (a))::

    actr(既定): A = ln(n/(1−d)) − d·ln(L+1)   L=(tick − sm_first)×分/tick・d=0.5(#56/#60 と同じ近似)

    想起できる店=``A ≥ τ``(τ は記憶の想起と同じ ``MemoryLayer.tau``=``RECALL_TAU`` −2.0=宣言)。
    感度腕の口(``--store-decay``・宣言・問い):
      ga      : A = ln(0.995)×(tick − sm_last)の時間(GA の recency 0.995^h を対数で=同じ τ で切る・n は使わない)
      citysim : A は actr と同じ(店の存在は忘れない側は ACT-R)・向きの強さが中立へ回帰=書くときに
                ``valence ← valence × exp(−0.03 × 前回からの日数)`` してから足す・読むときも同じ係数を掛ける

満杯で新しい店 → 店の行の score(A + 0.5 × min(4, precision)=アジェンダ §3-3 の形・宣言)が最小の行を
落とす(同点は行番号の小さい方)。記憶のエピソードの追い出しで店の行は消さない(宣言・問い (g))。

逐次ループ宣言(P4)
    1. :meth:`StoreMemory.write`: 体あたりの店の事象の件数の最大ぶん(同じ体の 2 件目を次の回へ)。
    2. :meth:`StoreMemory.summary`: 出どころの組の数ぶん(≤ 16)・ランの終わりに 1 回。
    体数に比例する Python ループは無い。
"""

from __future__ import annotations

import json
import math
from collections import Counter
from typing import Any, Final, Mapping, NamedTuple

import numpy as np

from shibuya.agents.state import STORE_MEMORY_EMPTY, ResultCode
from shibuya.engine import resolve as R
from shibuya.engine.memory import EVENT_KINDS

__all__ = [
    "STORE_MEMORY_N",
    "STORE_MEMORY_MODES",
    "STORE_MEMORY_ROW_BYTES_ACTUAL",
    "STORE_MEMORY_ROW_BYTES_DECLARED",
    "STORE_SOURCES",
    "STORE_SOURCE_BIT",
    "STORE_SIGMA",
    "STORE_DECAY_MODES",
    "DEFAULT_STORE_DECAY",
    "GA_RECENCY_PER_HOUR",
    "CITYSIM_LAMBDA_PER_DAY",
    "STORE_VALENCE_NEGATIVE",
    "STORE_SCORE_W_P",
    "STORE_SCORE_P_CAP",
    "check_store_sigma",
    "check_store_decay",
    "valence_of_result",
    "StoreRows",
    "StoreMemory",
]

#: 体あたりの行数(N1 (a)・宣言・感度 16/64)。
STORE_MEMORY_N: Final[int] = 32
STORE_MEMORY_MODES: Final[tuple[str, ...]] = ("off", "on")
#: 1 行の実バイト(4+4+4+4+4+2+1)と宣言バイト(詰め物 1 B は予算の側)。
STORE_MEMORY_ROW_BYTES_ACTUAL: Final[int] = 23
STORE_MEMORY_ROW_BYTES_DECLARED: Final[int] = 24
#: 出どころ(N4)とビット(``sm_source`` はビットの和=どこから知ったかの集合)。
STORE_SOURCES: Final[tuple[str, ...]] = ("self", "wom", "signage", "net")
STORE_SOURCE_BIT: Final[dict[str, int]] = {"self": 1, "wom": 2, "signage": 4, "net": 8}
#: 出どころ別の雑音 σ(N4 (a)・順序は錨 自分 < 伝聞 < 看板・比は宣言 expedient)。
STORE_SIGMA: Final[dict[str, float]] = {"self": 1.0, "wom": 2.0, "signage": 4.0, "net": 2.0}
#: 減衰の形(N5: 既定 actr・他は感度腕の口)。
STORE_DECAY_MODES: Final[tuple[str, ...]] = ("actr", "ga", "citysim")
DEFAULT_STORE_DECAY: Final[str] = "actr"
#: GA の recency(0.995/時・半減 5.8 日=R-49 §4 ✓)と CitySim の中立回帰(λ=0.03/日・半減 22.8 日 ✓)。
GA_RECENCY_PER_HOUR: Final[float] = 0.995
CITYSIM_LAMBDA_PER_DAY: Final[float] = 0.03
#: 自分の訪問で向き −1 にする結果(アジェンダ §1-2)。``OK`` は +1・それ以外は 0。
STORE_VALENCE_NEGATIVE: Final[tuple[int, ...]] = (
    int(ResultCode.OUT_OF_STOCK), int(ResultCode.CLOSED), int(ResultCode.LOST_ARBITRATION),
    int(ResultCode.TOO_FAR),
)
#: 店の行の score=A + w_p × min(cap, precision)(追い出しの順・7c の想起で競わせる形=宣言)。
STORE_SCORE_W_P: Final[float] = 0.5
STORE_SCORE_P_CAP: Final[float] = 4.0
#: 自分の訪問の書き手が拾うエピソードの種類(``engine.memory.EVENT_KINDS`` の buy/eat/queue)と看板。
_KINDS_SELF: Final[tuple[int, ...]] = (EVENT_KINDS["buy"], EVENT_KINDS["eat"], EVENT_KINDS["queue"])
_KIND_SIGNAGE: Final[int] = EVENT_KINDS["signage"]
_KIND_QUEUE: Final[int] = EVENT_KINDS["queue"]
_VALENCE_LABEL: Final[dict[int, str]] = {1: "+1", 0: "0", -1: "-1"}
#: POI 索引の上限(人の符号 1<<30|id と場所 −(cell+2) を POI と取り違えない)。
_POI_MAX: Final[int] = 1 << 30


def check_store_sigma(value: "Mapping[str, float] | str | None") -> dict[str, float]:
    """出どころ別の σ の表を検査して、全部の鍵を持つ辞書で返す(欠けた鍵は既定値)。

    ``value`` は辞書か JSON 文字列(CLI ``--store-sigma``)か ``None``(既定=:data:`STORE_SIGMA`)。

    Example:
        >>> check_store_sigma('{"signage": 16}')["signage"], check_store_sigma(None)["wom"]
        (16.0, 2.0)
    """
    if value is None:
        return dict(STORE_SIGMA)
    raw = json.loads(value) if isinstance(value, str) else dict(value)
    if not isinstance(raw, dict):
        raise ValueError("store_sigma は {出どころ: σ} の辞書")
    unknown = sorted(set(raw) - set(STORE_SOURCES))
    if unknown:
        raise ValueError(f"store_sigma の鍵は {STORE_SOURCES} のどれか(未知 {unknown})")
    out = dict(STORE_SIGMA)
    for k, v in raw.items():
        x = float(v)
        if not (math.isfinite(x) and x > 0.0):
            raise ValueError(f"store_sigma の σ は正の有限値(いま {k}={v!r})")
        out[k] = x
    return out


def check_store_decay(value: str) -> str:
    """減衰の形を検査して返す(:data:`STORE_DECAY_MODES` のどれか)。"""
    m = str(value)
    if m not in STORE_DECAY_MODES:
        raise ValueError(f"store_decay は {STORE_DECAY_MODES} のどれか(いま {value!r})")
    return m


def valence_of_result(result: np.ndarray) -> np.ndarray:
    """結果コード → 向き(``OK`` +1・:data:`STORE_VALENCE_NEGATIVE` −1・それ以外 0)。"""
    r = np.asarray(result, dtype=np.int64)
    v = np.zeros(r.size, dtype=np.int64)
    v[r == int(ResultCode.OK)] = 1
    v[np.isin(r, STORE_VALENCE_NEGATIVE)] = -1
    return v


class StoreRows(NamedTuple):
    """1 体の店の評価の行(空でない行だけ・行番号の順)。本段では誰も読まない(7c の読み口)。"""

    row: np.ndarray        # 行番号
    poi: np.ndarray        # POI 索引
    valence: np.ndarray    # 読むときの向きの強さ(Σ 精度 × 向き・citysim は回帰を掛けた値)
    sign: np.ndarray       # 向き −1/0/+1(sign(valence))
    precision: np.ndarray  # 確からしさ(Σ 1/σ²)
    A: np.ndarray          # 基底活性(減衰の形に従う)
    recallable: np.ndarray  # A ≥ τ
    source: np.ndarray     # 出どころのビットの和
    n: np.ndarray          # 更新回数


def _q(x: np.ndarray) -> dict[str, float]:
    x = np.asarray(x, dtype=np.float64)
    if x.size == 0:
        return {}
    return {p: round(float(np.percentile(x, float(p[1:]))), 4)
            for p in ("p0", "p10", "p50", "p90", "p99", "p100")} | {"mean": round(float(x.mean()), 4)}


def _source_label(bits: int) -> str:
    names = [s for s in STORE_SOURCES if int(bits) & STORE_SOURCE_BIT[s]]
    return "+".join(names) if names else "none"


class StoreMemory:
    """店の評価の記憶の書き手と読み口(``MemoryLayer`` が持つ・``--store-memory on`` のランだけ)。"""

    def __init__(self, n_agents: int, n_rows: int = STORE_MEMORY_N, *, minutes_per_tick: float = 1.0,
                 d: float = 0.5, sigma: "Mapping[str, float] | str | None" = None,
                 decay: str = DEFAULT_STORE_DECAY) -> None:
        self.n = int(n_agents)
        self.n_rows = int(n_rows)
        if self.n_rows < 1:
            raise ValueError(f"store_memory_n は 1 以上(いま {n_rows})")
        self.minutes_per_tick = float(minutes_per_tick)
        self.d = float(d)
        self.sigma = check_store_sigma(sigma)
        self.decay = check_store_decay(decay)
        #: 出どころ → 1 件の精度 1/σ²。
        self.weight: dict[str, float] = {k: 1.0 / (v * v) for k, v in self.sigma.items()}
        self.stats: Counter = Counter()

    # ------------------------------------------------------------------ 書き手
    def on_episodes(self, agents: Any, tick: int, a: np.ndarray, kind: np.ndarray, obj: np.ndarray,
                    result: np.ndarray) -> None:
        """記憶のエピソードの配列(``MemoryLayer.record`` が書いた順)→ 店の評価の行へ(配列演算)。"""
        a = np.asarray(a, dtype=np.int64)
        if a.size == 0:
            return
        kind = np.asarray(kind, dtype=np.int64)
        obj = np.asarray(obj, dtype=np.int64)
        result = np.asarray(result, dtype=np.int64)
        is_poi = (obj >= 0) & (obj < _POI_MAX)
        own = np.isin(kind, _KINDS_SELF) & is_poi
        sign = (kind == _KIND_SIGNAGE) & is_poi
        self.stats["episodes_shop_without_poi"] += int(np.count_nonzero(np.isin(kind, _KINDS_SELF) & ~is_poi))
        pick = own | sign
        if not bool(pick.any()):
            return
        src = np.where(own[pick], STORE_SOURCE_BIT["self"], STORE_SOURCE_BIT["signage"])
        # 第296 Q77: 並ぶの成功は向き 0(精度は足す)
        v_all = valence_of_result(result)
        v_all[(kind == _KIND_QUEUE) & (result == int(ResultCode.OK))] = 0
        val = np.where(own[pick], v_all[pick], 0)
        if bool(own.any()):
            vo = v_all[own]
            self.stats["events:self"] += int(own.sum())
            for v, c in Counter(vo.tolist()).items():  # 向きの数ぶん(≤ 3)
                self.stats[f"events:self:valence{_VALENCE_LABEL[int(v)]}"] += int(c)
            for code, c in Counter(result[own].tolist()).items():  # 結果コードの数ぶん
                self.stats[f"events:self:{ResultCode(int(code)).name}"] += int(c)
        if bool(sign.any()):
            self.stats["events:signage"] += int(sign.sum())
        self.write(agents, tick, a[pick], obj[pick], val, src)

    def write(self, agents: Any, tick: int, a: np.ndarray, poi: np.ndarray, valence: np.ndarray,
              source_bit: np.ndarray, scale: float = 1.0) -> np.ndarray:
        """(体, 店, 向き, 出どころのビット)の配列 → 行(体ごとに 1 件ずつの回に分ける)→ 各件の行番号。

        ``scale`` は 1 件の精度 1/σ² に掛ける係数(7b の聞き手への転写の重み=宛先 1.0・非宛先 0.5・傍受 0.2)。
        """
        a = np.asarray(a, dtype=np.int64)
        out = np.full(a.size, -1, dtype=np.int64)
        if a.size == 0:
            return out
        poi = np.asarray(poi, dtype=np.int64)
        valence = np.asarray(valence, dtype=np.int64)
        source_bit = np.asarray(source_bit, dtype=np.int64)
        w = np.zeros(a.size, dtype=np.float64)
        for name, bit in STORE_SOURCE_BIT.items():  # 出どころの数ぶん(4)
            w[source_bit == bit] = self.weight[name]
        w *= float(scale)
        order = np.lexsort((np.arange(a.size), a))
        sa = a[order]
        starts = np.flatnonzero(np.concatenate(([True], sa[1:] != sa[:-1])))
        rank = np.empty(a.size, dtype=np.int64)
        rank[order] = np.arange(a.size) - np.repeat(starts, np.diff(np.append(starts, a.size)))
        # 逐次ループ宣言 1: 体あたりの店の事象の件数の最大ぶん
        for rnd in range(int(rank.max()) + 1):
            sel = np.flatnonzero(rank == rnd)
            out[sel] = self._write_round(agents, tick, a[sel], poi[sel], valence[sel], w[sel],
                                         source_bit[sel])
        return out

    def _write_round(self, agents: Any, tick: int, a: np.ndarray, poi: np.ndarray, valence: np.ndarray,
                     w: np.ndarray, bit: np.ndarray) -> np.ndarray:
        r = agents.registry
        rows = r.sm_poi[a].astype(np.int64)
        hit = rows == poi[:, None]
        found = hit.any(axis=1)
        slot = np.where(found, np.argmax(hit, axis=1), -1)
        empty = rows == STORE_MEMORY_EMPTY
        new = ~found
        has_empty = empty.any(axis=1)
        slot = np.where(new & has_empty, np.argmax(empty, axis=1), slot)
        evict = new & ~has_empty
        if bool(evict.any()):
            s = self.scores(agents, a[evict], tick)
            slot[evict] = np.argmin(s, axis=1)  # 同点は行番号の小さい方
            self.stats["evictions"] += int(np.count_nonzero(evict))
        old_v = r.sm_valence[a, slot].astype(np.float64)
        old_p = r.sm_precision[a, slot].astype(np.float64)
        old_n = r.sm_n[a, slot].astype(np.int64)
        old_first = r.sm_first[a, slot].astype(np.int64)
        old_last = r.sm_last[a, slot].astype(np.int64)
        old_src = r.sm_source[a, slot].astype(np.int64)
        if self.decay == "citysim":  # 中立への回帰(前回から今回までの日数ぶん)
            days = np.maximum(0.0, (int(tick) - old_last) * self.minutes_per_tick / 1_440.0)
            old_v = old_v * np.exp(-CITYSIM_LAMBDA_PER_DAY * days)
        v = np.where(found, old_v, 0.0) + w * valence
        p = np.where(found, old_p, 0.0) + w
        n = np.where(found, np.minimum(old_n + 1, 65_535), 1)
        first = np.where(found, old_first, int(tick))
        src = np.where(found, old_src | bit, bit)
        R.write_store_memory(agents, a, slot, poi, v, p, first, np.full(a.size, int(tick)), n, src)
        self.stats["merged"] += int(np.count_nonzero(found))
        self.stats["new_rows"] += int(np.count_nonzero(new))
        self.stats["source_added"] += int(np.count_nonzero(found & ((old_src & bit) == 0)))
        return slot

    # ------------------------------------------------------------------ 読み口
    def activation(self, agents: Any, agent_ids: np.ndarray, tick: int) -> np.ndarray:
        """体の配列 → ``(体, M)`` の A(減衰の形に従う・空行は −inf)。"""
        r = agents.registry
        a = np.asarray(agent_ids, dtype=np.int64)
        empty = r.sm_poi[a] == STORE_MEMORY_EMPTY
        if self.decay == "ga":
            hours = np.maximum(0.0, (int(tick) - r.sm_last[a].astype(np.float64))
                               * self.minutes_per_tick / 60.0)
            A = hours * math.log(GA_RECENCY_PER_HOUR)
        else:
            nn = r.sm_n[a].astype(np.float64)
            L = np.maximum(0.0, (int(tick) - r.sm_first[a].astype(np.float64)) * self.minutes_per_tick)
            with np.errstate(divide="ignore"):
                A = np.log(nn / (1.0 - self.d)) - self.d * np.log(L + 1.0)
        return np.where(empty, -np.inf, A)

    def valence_now(self, agents: Any, agent_ids: np.ndarray, tick: int) -> np.ndarray:
        """体の配列 → ``(体, M)`` の読むときの向きの強さ(citysim は中立への回帰を掛ける)。"""
        r = agents.registry
        a = np.asarray(agent_ids, dtype=np.int64)
        v = r.sm_valence[a].astype(np.float64)
        if self.decay == "citysim":
            days = np.maximum(0.0, (int(tick) - r.sm_last[a].astype(np.float64))
                              * self.minutes_per_tick / 1_440.0)
            v = v * np.exp(-CITYSIM_LAMBDA_PER_DAY * days)
        return v

    def scores(self, agents: Any, agent_ids: np.ndarray, tick: int) -> np.ndarray:
        """店の行の score=A + 0.5 × min(4, precision)(追い出しの順・空行は −inf)。"""
        r = agents.registry
        a = np.asarray(agent_ids, dtype=np.int64)
        A = self.activation(agents, a, tick)
        p = np.minimum(STORE_SCORE_P_CAP, r.sm_precision[a].astype(np.float64))
        return A + STORE_SCORE_W_P * p

    def rows(self, agents: Any, agent_id: int, tick: int, tau: float) -> StoreRows:
        """1 体の空でない行(行番号の順)→ :class:`StoreRows`。"""
        r = agents.registry
        i = int(agent_id)
        used = np.flatnonzero(r.sm_poi[i] != STORE_MEMORY_EMPTY)
        A = self.activation(agents, np.asarray([i]), tick)[0][used]
        v = self.valence_now(agents, np.asarray([i]), tick)[0][used]
        return StoreRows(
            row=used, poi=r.sm_poi[i][used].astype(np.int64), valence=v,
            sign=np.sign(v).astype(np.int64), precision=r.sm_precision[i][used].astype(np.float64),
            A=A, recallable=A >= float(tau), source=r.sm_source[i][used].astype(np.int64),
            n=r.sm_n[i][used].astype(np.int64),
        )

    def known(self, agents: Any, agent_ids: np.ndarray, tick: int, tau: float,
              poi_mask: np.ndarray | None = None, min_sign: int | None = None) -> np.ndarray:
        """体の配列 → ``(体, M)`` の想起できる店(A ≥ τ)の POI 索引(それ以外は −1)。

        ``poi_mask``(POI の数の bool)で店を絞る(カテゴリ・営業中・到達可能=7c)。``min_sign`` で向きの
        下限(例: 0=向き ≥ 0)。配列演算だけ(P4)。
        """
        r = agents.registry
        a = np.asarray(agent_ids, dtype=np.int64)
        poi = r.sm_poi[a].astype(np.int64)
        ok = (poi != STORE_MEMORY_EMPTY) & (self.activation(agents, a, tick) >= float(tau))
        if poi_mask is not None:
            m = np.asarray(poi_mask, dtype=bool)
            inside = (poi >= 0) & (poi < m.size)
            ok &= inside & m[np.where(inside, poi, 0)]
        if min_sign is not None:
            ok &= np.sign(self.valence_now(agents, a, tick)) >= int(min_sign)
        return np.where(ok, poi, -1)

    # ------------------------------------------------------------------ 監査
    def summary(self, agents: Any, tick: int, tau: float) -> dict[str, Any]:
        """manifest ``store_memory_summary``: 行数/体・出どころ別・向き・精度・統合の回数・A。"""
        r = agents.registry
        all_ids = np.arange(self.n, dtype=np.int64)
        used = r.sm_poi != STORE_MEMORY_EMPTY
        rows_per = used.sum(axis=1)
        A = self.activation(agents, all_ids, tick)
        v = self.valence_now(agents, all_ids, tick)
        sign = np.sign(v)
        src = r.sm_source.astype(np.int64)
        prec = r.sm_precision.astype(np.float64)
        rec = used & (A >= float(tau))
        by_source: dict[str, dict[str, int]] = {}
        for bits in sorted(set(src[used].tolist())):  # 逐次ループ宣言 2: 出どころの組の数ぶん(≤ 16)
            m = used & (src == bits)
            by_source[_source_label(int(bits))] = {
                "rows": int(m.sum()), "valence+1": int((m & (sign > 0)).sum()),
                "valence0": int((m & (sign == 0)).sum()), "valence-1": int((m & (sign < 0)).sum()),
                "recallable": int((m & rec).sum()),
            }
        pois = r.sm_poi[used].astype(np.int64)
        per_poi = np.bincount(pois, minlength=1) if pois.size else np.zeros(1, dtype=np.int64)
        top = np.argsort(-per_poi, kind="stable")[:10]
        return {
            "n_rows": int(self.n_rows),
            "sigma": {k: float(self.sigma[k]) for k in STORE_SOURCES},
            "precision_per_event": {k: round(self.weight[k], 6) for k in STORE_SOURCES},
            "decay": self.decay, "tau": float(tau), "d": float(self.d),
            "row_bytes_actual": STORE_MEMORY_ROW_BYTES_ACTUAL,
            "row_bytes_declared": STORE_MEMORY_ROW_BYTES_DECLARED,
            "counts": {k: int(v_) for k, v_ in sorted(self.stats.items())},
            "rows_used_per_agent": _q(rows_per),
            "rows_used_total": int(used.sum()),
            "full_agents": int(np.count_nonzero(rows_per == self.n_rows)),
            "agents_with_rows": int(np.count_nonzero(rows_per > 0)),
            "rows_by_source": by_source,
            "rows_with_source_bit": {s: int((used & ((src & STORE_SOURCE_BIT[s]) > 0)).sum())
                                     for s in STORE_SOURCES},
            "valence_sign": {"+1": int((used & (sign > 0)).sum()), "0": int((used & (sign == 0)).sum()),
                             "-1": int((used & (sign < 0)).sum())},
            "precision": _q(prec[used]),
            "n_per_row": _q(r.sm_n[used]),
            "A": _q(A[used]),
            "recallable_rows": int(rec.sum()),
            "recallable_rows_per_agent": _q(rec.sum(axis=1)),
            "recallable_share": round(float(rec.sum()) / max(1, int(used.sum())), 4),
            "distinct_pois_known": int(np.count_nonzero(per_poi)),
            "top_pois_by_agents": {str(int(j)): int(per_poi[j]) for j in top.tolist() if per_poi[j] > 0},
        }
