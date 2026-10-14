"""engine.decision.layer — 候補の口 J0 の腕と層(1 呼の判断を口に通す・候補の源の計器・判断の出来事)(第 1 期 1-8)。

腕(切替口): ``--decision-port {legacy,port}``(環境変数 ``SHIBUYA_DECISION_PORT``・:func:`set_arm`)。既定 ``legacy``=今の道
(層を作らない=final・テープ・manifest の既存の欄は不変)。``port`` で、判断の系(``engine.systems.decide``)の 1 呼を
「前半(知覚の事実まで=``LLMBridge.begin``)→ 候補(``engine.decision.sources``)→ 口(``DecisionPort.choose``)→ 後半
(``LLMBridge.finish``=口の後ろの今の道)」にし、口が選んだ候補の行為のコードを適用する(mock と古典は同じ鍵・同じ答えから
同じ番号=今と同じ行為)。腕は組み立てのときに読む。結果を変えないので設定の指紋には入れない(記憶の器の腕と同じ扱い)。
腕の名は manifest の ``decision_port.arm`` に出る。

層(``DecisionLayer``・状態台帳の行 ``J0``=軸 1 diag・軸 2 discardable=どちらのハッシュにも状態のファイルにも入らない):

- 計器(``meter``): 判断の数・遅れて届く答え(再生の到着待ち・繰り延べ)の数・艦隊の道の呼(J0 は口を通さない)・提示した候補の
  源の分布・選んだ候補の源の分布・「その他」の数と割合・選んだ提示の番号の分布(位置の偏りの記録=R-108 §3-1 (i))・候補の数
  の分布・今の道と違うコードを適用した数(``mismatch``=同値の計器・J0 は 0)・判断の出来事の行の数。
- 判断の出来事(1-3 の出来事の記録): 口が選んだ行為ごとに 1 行(``who``=体・``what``=``行為:<語>``・``where``=セル・
  ``cause``=``LlmCall(call_id, 候補の元の出来事 id)``)。候補の源の記録=口の約束 1-8 の約束 (3)。語彙 v1/v2 の語のうち
  出来事の語彙表(v3 の行為 12 語)に無い語(降車・待機・休憩)と「その他」は書かず数える(``events_unlogged``)。
- 周りが示すできること(``affordance_words``): 場所の種類と営業時間から機械的に作る(下の expedient)。刻みごとの営業中の
  店の表を持つ(``_aff_*``=刻みの中で作り直す控え)。

逐次ループ宣言(P4): ``decide_one`` は 1 呼=候補の数ぶん(≤ 20)。``affordance_words`` は刻みに 1 回の POI の数の配列演算と
1 呼の語彙の語の数ぶん。新しい逐次ループは無い(呼数ぶんのループは decide の宣言 2 のまま)。

expedient(周りが示すできること=1-7 の道具の台帳で外す)
- 移動=いつでも(歩ける面)・乗車=路線のホームのセル・購入=セルに営業中の飲食店でない店・食事=セルに営業中の飲食店・並ぶ=
  セルに営業中の店・会話=知覚の事実に見えた人がいる・就寝=自宅のセル・断る=招待がある(場所の種類と営業時間と知覚から
  機械的に作る仮の源)。
"""

from __future__ import annotations

import dataclasses
import os
from typing import Any, Final, Mapping, Sequence

import numpy as np

from shibuya.engine.decision.port import (
    ALL_SOURCES,
    OTHER_ID,
    OTHER_SHARE_BASIS,
    OTHER_SHARE_DEFAULT,
    PORT_SCHEMA,
    SOURCE_VOCAB,
    SOURCES,
    DecisionContext,
    DecisionPort,
)
from shibuya.engine.decision.sources import build_candidates, memory_kind_words
from shibuya.engine.events import vocab as V

__all__ = [
    "ARM_LEGACY", "ARM_PORT", "ARMS", "arm", "set_arm", "DecisionLayer", "manifest_fields", "METER_KEYS",
    "OBSERVED_KEYS", "CONFIG_KEYS", "DECISION_EVENT_ROWS_PER_AGENT_DAY",
]

ARM_LEGACY: Final[str] = "legacy"
ARM_PORT: Final[str] = "port"
ARMS: Final[tuple[str, ...]] = (ARM_LEGACY, ARM_PORT)
_ARM: str = os.environ.get("SHIBUYA_DECISION_PORT", ARM_LEGACY).strip().lower() or ARM_LEGACY
if _ARM not in ARMS:
    raise ValueError(f"SHIBUYA_DECISION_PORT は {ARMS} のどれか(いま {_ARM!r})")


def arm() -> str:
    """いまの腕(``legacy``=既定・``port``=候補の口)。組み立てのときに読む。"""
    return _ARM


def set_arm(name: str) -> None:
    """腕を選ぶ(CLI ``--decision-port``・試験の切替口)。組み立ての時に読む(ランの途中で変えても、そのランは変わらない)。"""
    global _ARM
    if str(name) not in ARMS:
        raise ValueError(f"--decision-port は {ARMS} のどれか(いま {name!r})")
    _ARM = str(name)


#: manifest の ``decision_port`` の設定の子と観測の子(``engine.manifest_sections`` の混ざった辞書)。
CONFIG_KEYS: Final[tuple[str, ...]] = (
    "schema", "arm", "port", "sources", "bridge_source", "other_share_default", "other_share_basis")
OBSERVED_KEYS: Final[tuple[str, ...]] = (
    "decisions", "late", "fleet_legacy", "presented_by_source", "chosen_by_source", "other", "other_ratio",
    "chosen_number", "n_candidates", "mismatch", "events", "events_unlogged")
#: 計器の数の鍵(``meter`` の中の整数)。分布は別の dict。
METER_KEYS: Final[tuple[str, ...]] = (
    "decisions", "late", "fleet_legacy", "other", "mismatch", "events", "events_unlogged")



#: 〔検収 L2〕腕 port の判断の出来事の行の数(1 判断 1 行)=mock・既定 v3・5,000 体・1 日の実測 65,597 判断 ÷ 5,000 体
#: (古典+記憶+関係は 21.3=記録 j0/README.md §4)。成長の宣言(``EventLog.growth_declaration``)に渡す値。
DECISION_EVENT_ROWS_PER_AGENT_DAY: Final[float] = 13.1


def _empty_meter() -> dict[str, Any]:
    return {**{k: 0 for k in METER_KEYS}, "presented_by_source": {s: 0 for s in ALL_SOURCES},
            "chosen_by_source": {**{s: 0 for s in ALL_SOURCES}, OTHER_ID: 0}, "chosen_number": {},
            "n_candidates": {}}


def manifest_fields(layer: "DecisionLayer | None") -> dict[str, Any]:
    """manifest の ``decision_port``(腕が legacy のランは層が無い=観測の子は null)。"""
    cfg: dict[str, Any] = {
        "schema": PORT_SCHEMA, "arm": ARM_LEGACY if layer is None else layer.arm,
        "port": None if layer is None else layer.port.name, "sources": list(SOURCES), "bridge_source": SOURCE_VOCAB,
        "other_share_default": OTHER_SHARE_DEFAULT, "other_share_basis": OTHER_SHARE_BASIS,
    }
    if layer is None:
        return {**cfg, **{k: None for k in OBSERVED_KEYS}}
    return {**cfg, **layer.observed()}


class DecisionLayer:
    """候補の口の層(腕 ``port`` のランだけ組み立てが作る=``Layers.decision``)。

    Args:
        port: 口の実装(``engine.decision.ports``)。
        vocab: 候補にする語彙の語(その版の横断語=``llm.contract.cross_action_words``)。
        continue_word: 続ける候補の語(その版の安全弁の語)。
        word_of_code: 行動コード → 語(``engine.llm_bridge.ACTION_WORD_BY_CODE``)。
        events: 出来事の記録(``engine.events.log.EventLog``・無ければ書かない)。
        world: 世界(POI の置き場・営業時間・飲食店の印=読むだけ)。
        home_cell: 体ごとの自宅のセル(無ければ -1)。
        station_cells: 路線のホームのセル。
    """

    def __init__(
        self,
        *,
        port: DecisionPort,
        vocab: Sequence[str],
        continue_word: str,
        word_of_code: Mapping[int, str],
        events: Any = None,
        world: Any = None,
        home_cell: Any = None,
        station_cells: Any = None,
    ) -> None:
        from shibuya.engine.events.log import CANDIDATE_SOURCES

        if tuple(ALL_SOURCES) != tuple(CANDIDATE_SOURCES):  # 検収 M1: 原因の列の源の番号と口の源の並びを 1 つに
            raise RuntimeError(f"口の源 {ALL_SOURCES} と出来事の原因の源 {CANDIDATE_SOURCES} が違う")
        self.arm = ARM_PORT
        self.port = port
        self.vocab = tuple(vocab)
        self.continue_word = str(continue_word)
        self.word_of_code = dict(word_of_code)
        self.kind_words = dict(memory_kind_words(self.word_of_code))
        self.events = events
        self.event_words = frozenset(w for w in self.vocab if f"{V.FAMILY_ACT}:{w}" in V.VOCAB_CODES)
        self.world = world
        n_cells = int(getattr(world, "n_cells", 0)) if world is not None else 0
        self.n_cells = n_cells
        self._poi_cell = (np.asarray(world.pois.cell, dtype=np.int64) if world is not None
                          else np.zeros(0, dtype=np.int64))
        self._eatery = (np.asarray(world.eatery_mask, dtype=bool) if world is not None
                        else np.zeros(0, dtype=bool))
        self._station = np.zeros(n_cells, dtype=bool)
        if station_cells is not None:
            sc = np.asarray(station_cells, dtype=np.int64).ravel()
            sc = sc[(sc >= 0) & (sc < n_cells)]
            self._station[sc] = True
        self._home_cell = (np.asarray(home_cell, dtype=np.int64) if home_cell is not None
                           else np.zeros(0, dtype=np.int64))
        #: 計器(状態台帳の行 J0・軸 1 diag・軸 2 discardable)。
        self.meter: dict[str, Any] = _empty_meter()
        #: 刻みごとの営業中の店の控え(刻みの番号・セルの bool 3 本=店・飲食店・飲食店でない店)。
        self._aff_step = -1
        self._aff_any = np.zeros(n_cells, dtype=bool)
        self._aff_eatery = np.zeros(n_cells, dtype=bool)
        self._aff_shop = np.zeros(n_cells, dtype=bool)

    # ------------------------------------------------------------------ 周りが示すできること(1-7 までのつなぎ)
    def _open_cells(self, step: int) -> None:
        if self._aff_step == int(step) or self.world is None or self.n_cells == 0:
            return
        is_open = np.asarray(self.world.open_mask(int(step)), dtype=bool)
        pc = self._poi_cell
        ok = is_open & (pc >= 0) & (pc < self.n_cells)
        eat = ok & self._eatery
        for col, m in ((self._aff_any, ok), (self._aff_eatery, eat), (self._aff_shop, ok & ~eat)):
            col[:] = False
            col[pc[m]] = True
        self._aff_step = int(step)

    def affordance_words(self, ctx: DecisionContext, vocab: Sequence[str]) -> tuple[str, ...]:
        """その体のセルと刻みで、周りが示す「できること」の語(語彙の順)。読むだけ(営業中の控えだけ作り直す)。"""
        c = int(ctx.cell)
        inside = 0 <= c < self.n_cells
        if inside:
            self._open_cells(ctx.step)
        p = ctx.percept
        seen = bool(getattr(p, "seen_people", ()) or ()) if p is not None else False
        a = int(ctx.agent_id)
        home = int(self._home_cell[a]) if 0 <= a < self._home_cell.size else -1
        ok = {
            "移動": True,
            "乗車": inside and bool(self._station[c]),
            "購入": inside and bool(self._aff_shop[c]),
            "食事": inside and bool(self._aff_eatery[c]),
            "並ぶ": inside and bool(self._aff_any[c]),
            "会話": seen,
            "就寝": home >= 0 and home == c,
            "断る": int(ctx.inviter) >= 0,
        }
        return tuple(w for w in vocab if ok.get(w, False))

    # ------------------------------------------------------------------ 計器(manifest の観測の子)
    def observed(self) -> dict[str, Any]:
        """manifest の ``decision_port`` の観測の子(``OBSERVED_KEYS`` の順)。"""
        m = self.meter
        n = int(m["decisions"])
        return {
            "decisions": n, "late": int(m["late"]), "fleet_legacy": int(m["fleet_legacy"]),
            "presented_by_source": dict(m["presented_by_source"]), "chosen_by_source": dict(m["chosen_by_source"]),
            "other": int(m["other"]), "other_ratio": (round(int(m["other"]) / n, 6) if n else None),
            "chosen_number": {k: int(v) for k, v in sorted(m["chosen_number"].items(), key=lambda kv: int(kv[0]))},
            "n_candidates": {k: int(v) for k, v in sorted(m["n_candidates"].items(), key=lambda kv: int(kv[0]))},
            "mismatch": int(m["mismatch"]), "events": int(m["events"]), "events_unlogged": int(m["events_unlogged"]),
        }

    # ------------------------------------------------------------------ 1 呼
    def decide_one(
        self,
        bridge: Any,
        agent_id: int,
        step: int,
        wake_class: int,
        condition: int,
        *,
        cell: int,
        activity: int,
        hunger: int,
        last_action: int,
        inviter: int,
        t_ns: int,
    ) -> tuple[Any, Any]:
        """1 呼の判断を口に通す。``(BridgeResult, Percept)`` を返す(結果の行為のコードは口が選んだ候補のコード)。

        遅れて届く答え(再生の繰り延べ・後の刻みに届く応答)は今の道の結果のまま返す(到着の刻みで今の道が適用する=J0 は
        口のコードを当てない・``late`` に数える)。
        """
        start = bridge.begin(int(agent_id), int(step), int(wake_class), int(condition), cell=int(cell),
                             activity=int(activity), hunger=int(hunger), last_action=int(last_action),
                             inviter=int(inviter))
        p = start.percept
        mem = getattr(p, "memories", None) if p is not None else None
        ctx = DecisionContext(
            agent_id=int(agent_id), step=int(step), t_ns=int(t_ns), wake_class=int(wake_class),
            condition=int(condition), cell=int(cell), call_id=f"{int(step)}:{int(agent_id)}:{int(wake_class)}",
            percept=p, prediction=None, memory=None if mem is None else tuple(mem), tools=None,
            inviter=int(inviter), last_action=int(last_action), request=start,
        )
        cands = build_candidates(ctx, vocab=self.vocab, continue_word=self.continue_word,
                                 word_of_code=self.word_of_code, kind_words=self.kind_words,
                                 affordance_words=self.affordance_words)
        choice = self.port.choose(ctx, cands)
        res = choice.backend
        m = self.meter
        if bool(res.deferred) or int(res.observed_tick) > int(step):
            m["late"] += 1
            return res, p
        if choice.is_other or choice.kind not in self.vocab:
            code = int(res.action_code)
        else:
            code = int(bridge.code_of_word(choice.kind))
        m["decisions"] += 1
        for c in cands:  # 逐次ループ宣言: 候補の数ぶん
            m["presented_by_source"][c.source] += 1
        n = len(cands)
        kn, kc = str(n), str(choice.number)
        m["n_candidates"][kn] = m["n_candidates"].get(kn, 0) + 1
        m["chosen_number"][kc] = m["chosen_number"].get(kc, 0) + 1
        if choice.is_other:
            m["other"] += 1
            m["chosen_by_source"][OTHER_ID] += 1
        else:
            src = next(c.source for c in cands if c.id == choice.candidate_id)
            m["chosen_by_source"][src] += 1
        if code != int(res.action_code):
            m["mismatch"] += 1
            res = dataclasses.replace(res, action_code=code)
        self._write_event(ctx, choice, cands)
        return res, p

    def event_growth(self) -> Any:
        """〔検収 L2〕腕 port のランの出来事の記録の成長の宣言(判断の出来事の行を足した ``EventLog.growth_declaration``)。"""
        if self.events is None:
            return None
        return self.events.growth_declaration(decision_rows_per_agent_day=DECISION_EVENT_ROWS_PER_AGENT_DAY)

    def note_fleet_calls(self, n: int) -> None:
        """艦隊の道の呼(J0 は口を通さない=今の道のまま)を数える。"""
        self.meter["fleet_legacy"] += int(n)

    def _write_event(self, ctx: DecisionContext, choice: Any, cands: Sequence[Any]) -> None:
        log = self.events
        if log is None or not log.enabled:
            return
        if choice.is_other or choice.kind not in self.event_words:
            self.meter["events_unlogged"] += 1
            return
        from shibuya.engine.events.log import Event, LlmCall

        seen: dict[tuple[int, int], None] = {}
        src = None
        for c in cands:  # 逐次ループ宣言: 候補の数ぶん(元の出来事 id を候補の並びで重ねずに)
            for eid in c.basis:
                seen.setdefault(eid, None)
            if c.id == choice.candidate_id:
                src = c.source
        # 検収 M1: 選んだ候補の源と提示の番号を判断ごとに原因に残す(口の約束 1-8 の約束 (3))
        log.append(Event(t_ns=log.now_ns, who=int(ctx.agent_id), what=V.word(V.FAMILY_ACT, choice.kind),
                         where=("cell", int(ctx.cell)) if int(ctx.cell) >= 0 else None,
                         cause=LlmCall(ctx.call_id, tuple(seen), source=src, number=int(choice.number))))
        self.meter["events"] += 1
