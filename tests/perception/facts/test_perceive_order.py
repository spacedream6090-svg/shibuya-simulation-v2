"""〔割る段 7 の G0・親の決め事 1・裁定 Q17〕``Renderer.perceive`` の副作用の順を、割る前の木で作った固定の値と完全一致で比べる。

割る段 7 は ``perception/renderer.py`` を割り、``perceive`` を基底のクラスへ移す。そのとき文の順(=口を呼ぶ順・計数の順・乱数を
引く順)が黙って変わらないことを、ここで固定する。

記録するもの(1 本の出来事の列): 口の呼び(``clock_fn``・``day_kind_fn``・``named_closed_lookup``・``weather_date_fn``
または ``weather_words_key_fn``・``weather_words_fn``・``acquaintance_fn``・``session_partner_fn``・近接の腕の ``nv.aware``・
``memory_recall``・``heard_fn``・``heard_seen_fn``・``contact_fn``)・露出の控え(``signage_exposures`` への追記)・前計算の始めと
終わり・区切り(``perceive`` の始めと終わり・描く側の終わり)。各の出来事に、その時までに作った乱数の流れの数と、前の出来事から
変わった計数の値を添える。最後に乱数の流れの列(用途名・カウンタ)も比べる。

比べ方: (a) 列の全体を固定の値と完全一致 (b) 1 回の ``perceive`` の中で、口の呼びが今の順(docstring の 6 段=看板の注視の
抽選と計数 → 露出の控え → 閉店の 1 句 → B3 の命中の計数と天気 → 近接の同点の計数 → 想起、を含む)の部分列 (c) 乱数の流れの列。
docstring に無い副作用(前計算・場面の控え・近接の口 3 つ・知人の控え・発話の口・連絡の口)も (a) で固定する。知人の控え
(``_acq_cache``)は、知人の口(``acquaintance_fn``=``--relations on`` のランだけ)が無いときにだけ通る道で、構成 ``near_table``
で固定する(知人の口を外す=既定のランの道。既定のランは知人表を渡さない=表は空なので、ここでは知人のある表を渡して控えの中身を動かす)。

構成: ``fixed``(固定枠)・``ranking``(単一ランキング)・``near``(近接の腕=口の順がセルの道と逆)・``calendar``(天気の規則)・
``near_table``(近接の腕で、知人の口と気づいた印の口を外す=既定のランの道。知人のある表を渡す。〔検収の中-1〕)。
固定の値は ``docs/bench/analysis/split7-347/tools/make_perceive_order.py`` が作る(この試験は比べるだけ)。割る段 7 の G-S まで
固定の値を変えない(変える必要が出たら止まって報告=裁定 Q17)。
"""

from __future__ import annotations

import ast
import functools
import inspect
import json
import sys
import textwrap
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from shibuya.foundation.text import templates as T
from shibuya.foundation.vocab.agent_codes import IntentKind, ResultCode, WakeCondition
from shibuya.mind.memory.memory import RecallItem
from shibuya.mind.percept.draw import Renderer
from shibuya.validation.static.rng_audit import StreamRecorder
from shibuya.world.model.proximity import NearView, ProximityLayer, ProximityRule
from tests.perception.facts.scenes import build

FROZEN = Path(__file__).with_name("perceive_order_frozen.json")
SCHEMA = "shibuya.tests/perceive-order/1"
CONFIGS = ("fixed", "ranking", "near", "calendar", "near_table")
N_AGENTS, N_CELLS, SEED = 24, 4, 21
TICKS = (600, 601)
START = datetime(2026, 7, 28, 0, 0)
#: 出来事ごとに見る描画の計数(変わった値だけを出来事に添える)。
COUNTERS = ("signage_gate_draws", "signage_gate_shown", "named_closed_notes", "cache_hits", "cache_misses",
            "near_order_ties", "near_tie_breaks", "near_tie_candidates", "intent_lines", "intent_lines_over_budget",
            "memory_lines", "memory_items", "memory_items_dropped_for_budget", "memory_items_dropped_for_channel",
            "memory_lines_over_budget", "speech_lines", "speech_lines_over_budget", "contact_lines",
            "contact_lines_over_budget", "contact_unnoticed_renders", "renders", "truncation_count")
#: 1 回の ``perceive`` の中の口の呼びの順(今の順)。同じ値の口どうしの順は (a) が固定する(近接の 3 つは道で順が逆)。
RANK = {"prepare_start": 0, "clock_fn": 0, "day_kind_fn": 0, "prepare_end": 0, "exposure": 1, "named_closed_lookup": 2,
        "weather_date_fn": 3, "weather_words_key_fn": 3, "weather_words_fn": 3, "acquaintance_fn": 4,
        "session_partner_fn": 4, "aware": 4, "memory_recall": 5, "heard_fn": 6, "contact_fn": 7}
#: 構成ごとに、列に少なくとも 1 回は出るはずの出来事(確かめが空回りしない)。
MUST = {
    "fixed": {"prepare_start", "clock_fn", "day_kind_fn", "exposure", "named_closed_lookup", "weather_date_fn",
              "acquaintance_fn", "session_partner_fn", "memory_recall", "heard_fn", "heard_seen_fn", "contact_fn"},
    "near": {"aware", "acquaintance_fn", "session_partner_fn"},
    "calendar": {"weather_words_key_fn", "weather_words_fn"},
    "near_table": {"session_partner_fn", "memory_recall", "heard_fn", "contact_fn"},
}
MUST["ranking"] = MUST["fixed"]
#: 構成 ``near_table`` の知人表(口の無いランの道=``Renderer(acquaintances=…)``。3 体に 1 体は知人なし)。
ACQ_TABLE = {i: ((i + 1) % N_AGENTS, (i + 2) % N_AGENTS) for i in range(N_AGENTS) if i % 3}
#: 負の対照: ``perceive`` の 2 文を入れ替える(計画 §3-5 の 2 組)。
SWAPS = ("wake_time", "recall_heard")


class _Log:
    """出来事の列(``[種類, 中身, 乱数の流れの数, 前の出来事から変わった計数]``)。"""

    def __init__(self, rec: StreamRecorder) -> None:
        self.rec = rec
        self.r: Any = None
        self.events: list[list[Any]] = []
        self.prev: dict[str, int] = {}

    def _snap(self) -> dict[str, int]:
        r = self.r
        if r is None:
            return {}
        tc = r._tickc
        s = {k: int(getattr(r, k)) for k in COUNTERS}
        s.update(scenes=len(tc.scenes), time_views=len(tc.time_views), heard=len(tc.heard),
                 heard_reported=len(tc.heard_reported), b3_cache=len(r._b3_cache), acq_cache=len(r._acq_cache),
                 exposures=len(r.signage_exposures or ()))
        return s

    def add(self, kind: str, *detail: Any) -> None:
        now = self._snap()
        delta = {k: v for k, v in sorted(now.items()) if self.prev.get(k, 0) != v}
        self.prev = now
        self.events.append([kind, list(detail), len(self.rec.made), delta])


class _Exposures(list):
    """露出の控え(追記を出来事にする)。"""

    def __init__(self, log: _Log) -> None:
        super().__init__()
        self.log = log

    def append(self, item: Any) -> None:  # noqa: D401
        super().append(item)
        self.log.add("exposure", int(item[0]), int(item[1]))


def _memories(i: int, t: int) -> list[RecallItem]:
    if i % 3 == 0:
        return []
    return [
        RecallItem(row=i % 7, last_tick=t - 30, kind=7, partner=(i + 1) % N_AGENTS, obj=-1, result=0, cell=2,
                   gist="駅前の店の話をした", first_tick=t - 90),
        RecallItem(row=8 + i % 3, last_tick=-1, kind=3, partner=-1, obj=1, result=int(ResultCode.CLOSED), cell=1,
                   gist="", first_tick=t - 400),
    ][: 1 + i % 2]


def _calls(i: int, t: int) -> dict[str, Any]:
    reasons = (3, 5, int(WakeCondition.CONVERSATION_TURN), "予定の時刻になりました。", 99)
    results = (None, int(ResultCode.MONEY_SHORT), int(ResultCode.CLOSED), int(ResultCode.OK), None)
    return dict(wake_reason=reasons[(i + t) % len(reasons)], last_result=results[(i * 3 + t) % len(results)],
                last_action=(None, "移動", "")[i % 3], inviter=(None, None, -1, (i + 5) % N_AGENTS)[i % 4])


def _prepare_kwargs(t: int, n_cells: int) -> dict[str, Any]:
    k = t % 3
    return {
        "queues": [(0, "物販0000", 3 + k), (1, "コンビニ0001", 7)],
        "activity_rows": {0: (("歩いている", 4), ("話している", 2)), 2: (("待っている", 1 + k),)},
        "salient_events": {1: ("[顕著] 人だかりができている。",)} if k else None,
        "flow": (np.arange(n_cells) + k) % 3,
    }


def _setup_agents(a: Any) -> None:
    with a.writable():
        for i in range(a.n):
            a.intent_action[i] = (3, 24, 22, -1)[i % 4]
            a.intent_kind[i] = (int(IntentKind.POI_NAMED), int(IntentKind.POI_CATEGORY), int(IntentKind.PERSON),
                                int(IntentKind.NONE))[i % 4]
            a.intent_target[i] = (1, 2, 4, 0)[i % 4]
        a.last_result[0::5] = int(ResultCode.CLOSED)
        a.last_result_tick[0::5] = 1


def _install_hooks(r: Any, log: _Log, cfg: str, n: int) -> None:
    def named_closed_lookup(i: int) -> Any:
        log.add("named_closed_lookup", int(i))
        return (1, 1, 600) if int(i) % 5 == 0 else None

    def acquaintance_fn(i: int, t: int) -> list[int]:
        log.add("acquaintance_fn", int(i), int(t))
        return [(i + 1) % n, (i + 2) % n]

    def session_partner_fn(i: int) -> list[int]:
        log.add("session_partner_fn", int(i))
        return [(i + 3) % n] if i % 2 else []

    def memory_recall(i: int, t: int, cond: int, inv: int) -> list[RecallItem]:
        log.add("memory_recall", int(i), int(t), int(cond), int(inv))
        return _memories(int(i), int(t))

    def heard_fn(i: int, t: int) -> list[tuple[tuple[int, int], int, str]]:
        log.add("heard_fn", int(i), int(t))
        return [((int(t), int(i)), (i + 1) % n, "こんにちは")] if i % 4 == 1 else []

    def heard_seen_fn(i: int, shown: Any, empty: int, n_drop: int) -> None:
        log.add("heard_seen_fn", int(i), [list(e) for e in shown], int(empty), int(n_drop))

    def contact_fn(p: Any) -> Any:
        log.add("contact_fn", int(p.agent_id))
        return p

    r.named_closed_lookup = named_closed_lookup
    r.acquaintance_fn = acquaintance_fn
    r.session_partner_fn = session_partner_fn
    r.memory_recall = memory_recall
    r.heard_fn = heard_fn
    r.heard_seen_fn = heard_seen_fn
    r.contact_fn = contact_fn
    r.signage_exposures = _Exposures(log)
    if cfg == "calendar":
        def weather_words_key_fn(when: datetime) -> tuple[str, int]:
            log.add("weather_words_key_fn", when.isoformat())
            return ("2026-07-29", int(when.hour))

        def weather_words_fn(when: datetime) -> tuple[str, str, str]:
            log.add("weather_words_fn", when.isoformat())
            return (T.WEATHER_WORDS[2], T.DAYLIGHT_WORDS[1], T.HEAT_STAGE_WORDS[1])

        r.weather_words_key_fn = weather_words_key_fn
        r.weather_words_fn = weather_words_fn
    else:
        def weather_date_fn() -> str:
            log.add("weather_date_fn")
            return "2026-07-29"

        r.weather_date_fn = weather_date_fn
    # 区切り(インスタンスの属性で包む=メソッドの名で呼ぶ・割った後も同じ形で動く)
    perceive, prepare, draw = r.perceive, r.prepare_tick, r._render_percept

    def perceive_w(agent_id: int, step: int, *a: Any, **k: Any) -> Any:
        log.add("perceive_start", int(agent_id), int(step))
        p = perceive(agent_id, step, *a, **k)
        log.add("perceive_end", int(agent_id))
        return p

    def prepare_w(tick: int, **k: Any) -> Any:
        log.add("prepare_start", int(tick), sorted(k))
        out = prepare(tick, **k)
        log.add("prepare_end", int(tick))
        return out

    def draw_w(p: Any, *a: Any) -> Any:
        out = draw(p, *a)
        log.add("draw_end", int(p.agent_id))
        return out

    r.perceive, r.prepare_tick, r._render_percept = perceive_w, prepare_w, draw_w


@functools.cache
def record(cfg: str, cls: type = Renderer) -> dict[str, Any]:
    """構成 ``cfg`` を ``cls``(既定は ``Renderer``・負の対照は子クラス)で回した出来事の列と乱数の流れの列。"""
    w, a = build(n_agents=N_AGENTS, n_cells=N_CELLS, seed=SEED)
    _setup_agents(a)
    with StreamRecorder() as rec:
        log = _Log(rec)

        def clock_fn(t: int) -> datetime:
            log.add("clock_fn", int(t))
            return START + timedelta(minutes=int(t))

        def day_kind_fn(t: int) -> str:
            log.add("day_kind_fn", int(t))
            return "平日"

        table = {"acquaintances": ACQ_TABLE} if cfg == "near_table" else {}
        r = cls(w, a, clock_fn=clock_fn, seed=7, signage_p_see=0.5, day_kind_fn=day_kind_fn,
                budget_mode="ranking" if cfg == "ranking" else "fixed", **table)
        log.r = r
        _install_hooks(r, log, cfg, int(a.n))
        if cfg == "near_table":  # 〔検収の中-1〕既定のランの道: 知人の口が無い=知人表から引いて控える(_acq_cache)
            r.acquaintance_fn = None
        layer = ProximityLayer(ProximityRule()) if cfg in ("near", "near_table") else None

        def aware(i: int, ids: Any, step: int) -> np.ndarray:
            ids = np.asarray(ids, dtype=np.int64)
            log.add("aware", int(i), [int(x) for x in ids], int(step))
            return ids % 2 == 0

        for t in TICKS:
            kw = _prepare_kwargs(t, w.n_cells)
            if layer is not None:
                # 既定のランは関係の層の気づいた印が無い(marks=None)=near_table は aware を渡さない
                kw["near"] = NearView(layer.rule, layer.build_index(a), aware if cfg == "near" else None)
            if t == TICKS[0] or layer is not None:  # 2 刻み目は(近接の腕のほか)perceive・render が自分で前計算する道
                r.prepare_tick(t, **kw)
            for i in range(int(a.n)):
                c = _calls(i, t)
                if (i + t) % 2 == 0:
                    log.add("render_call", i, t)
                    r.render(i, tick=t, **c)
                else:
                    log.add("perceive_call", i, t)
                    p = r.perceive(i, t, **c)
                    r.render_percept(p)
            log.add("tick_end", t)
        streams = [[str(d), [int(x) for x in ctr]] for d, ctr, _c0, _bg in rec.made]
    return {"events": log.events, "streams": streams}


def order_violations(events: list[list[Any]]) -> list[str]:
    """1 回の ``perceive`` の中で、口の呼びが :data:`RANK` の順でない所と、看板の抽選より前の露出の控え(空なら順のとおり)。"""
    bad: list[str] = []
    span: list[tuple[str, int]] | None = None
    for k, ev in enumerate(events):
        kind = ev[0]
        if kind == "perceive_start":
            span = []
        elif kind == "perceive_end":
            ranks = [RANK[x] for x, _k in span or []]
            if ranks != sorted(ranks):
                bad.append(f"出来事 {k}: {[x for x, _k in span or []]}")
            span = None
        elif span is not None and kind in RANK:
            span.append((kind, k))
            if kind == "exposure" and not {"signage_gate_draws", "signage_gate_shown"} <= set(ev[3]):
                bad.append(f"出来事 {k}: 露出の控えの前に看板の抽選と計数が無い")
    return bad


def swapped_class(swap: str) -> type:
    """``Renderer.perceive`` の 2 文を入れ替えた子クラス(メソッドの名で作る=割った後も、定義のモジュールで同じ形に作れる)。"""
    fn = Renderer.perceive
    tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
    body = tree.body[0].body

    def find(pred: Any) -> int:
        hits = [k for k, st in enumerate(body) if pred(ast.unparse(st))]
        assert len(hits) == 1, (swap, hits)
        return hits[0]

    if swap == "wake_time":
        x, y = find(lambda s: s.startswith("wake = self._wake_view(")), find(lambda s: s.startswith("tv = self._time_view("))
    elif swap == "recall_heard":
        x = find(lambda s: s.startswith("if self.memory_recall is not None"))
        y = find(lambda s: s.startswith("if self.heard_fn is not None"))
    else:
        raise ValueError(swap)
    body[x], body[y] = body[y], body[x]
    ns = dict(vars(sys.modules[fn.__module__]))
    exec(compile(tree, f"<{swap}>", "exec"), ns)  # noqa: S102
    return type(f"Swapped_{swap}", (Renderer,), {"perceive": ns["perceive"]})


@functools.cache
def _frozen() -> dict[str, Any]:
    return json.loads(FROZEN.read_text(encoding="utf-8"))


# ================================================================= 試験
def test_the_frozen_values_are_for_this_setup():
    doc = _frozen()
    assert doc["schema"] == SCHEMA and sorted(doc["configs"]) == sorted(CONFIGS)
    assert (doc["n_agents"], doc["n_cells"], doc["seed"], doc["ticks"]) == (N_AGENTS, N_CELLS, SEED, list(TICKS))


@pytest.mark.parametrize("cfg", CONFIGS)
def test_the_events_match_the_frozen_values(cfg):
    """(a) 出来事の列の全体と (c) 乱数の流れの列が、割る前の木で作った固定の値と完全一致。"""
    got, want = record(cfg), _frozen()["configs"][cfg]
    assert len(got["events"]) == len(want["events"])
    for k, (g, wv) in enumerate(zip(got["events"], want["events"])):
        assert g == wv, (cfg, k, g, wv)
    assert got["streams"] == want["streams"]


@pytest.mark.parametrize("cfg", CONFIGS)
def test_each_perceive_keeps_the_order(cfg):
    """(b) 1 回の ``perceive`` の中の口の呼びが今の順の部分列(docstring の 6 段を含む)・確かめが空回りしない。"""
    got = record(cfg)
    assert order_violations(got["events"]) == []
    kinds = {ev[0] for ev in got["events"]}
    assert MUST.get(cfg, set()) <= kinds, sorted(MUST.get(cfg, set()) - kinds)
    assert got["streams"], "看板の注視の抽選が 1 本も引かれていない"


def test_the_two_near_paths_call_the_hooks_in_opposite_orders():
    """見つかったこと(直さずに固定する): セルの道は知人 → 会話の参加者、近接の腕の道は会話の参加者 → 知人 → 気づいた印。"""

    def near_orders(events: list[list[Any]]) -> set[tuple[str, ...]]:
        out, span = set(), None
        for ev in events:
            if ev[0] == "perceive_start":
                span = []
            elif ev[0] == "perceive_end":
                out.add(tuple(span or ()))
                span = None
            elif span is not None and ev[0] in ("acquaintance_fn", "session_partner_fn", "aware"):
                span.append(ev[0])
        return out

    assert near_orders(record("fixed")["events"]) == {("acquaintance_fn", "session_partner_fn")}
    near = near_orders(record("near")["events"])
    assert ("session_partner_fn", "acquaintance_fn", "aware") in near
    assert all(o[:2] == ("session_partner_fn", "acquaintance_fn") for o in near), near


@pytest.mark.parametrize("cfg", ("fixed", "near_table"))
@pytest.mark.parametrize("swap", SWAPS)
def test_negative_swapped_statements_are_caught(swap, cfg):
    """負の対照: ``perceive`` の 2 文を入れ替えた子クラスを同じ構成で回すと、(a) の完全一致が違い、(b) の順の確かめが落ちる
    (固定枠と、知人表の道=〔検収の中-1〕の両方)。"""
    got = record(cfg, swapped_class(swap))
    assert got["events"] != _frozen()["configs"][cfg]["events"]
    assert order_violations(got["events"]) != []


def acq_cache_by_tick(events: list[list[Any]]) -> dict[int, int]:
    """刻みの終わりの知人の控え(``_acq_cache``)の数(出来事に添えた変わった計数を前から積む)。"""
    now, out = 0, {}
    for ev in events:
        now = int(ev[3].get("acq_cache", now))
        if ev[0] == "tick_end":
            out[int(ev[1][0])] = now
    return out


def test_the_table_path_fills_and_reuses_the_acquaintance_cache():
    """〔検収の中-1〕構成 ``near_table``(既定のランの道)で、知人の控え ``_acq_cache`` が実際に動く: 1 刻み目で 0 → 正の数、
    2 刻み目は同じ体の控えを使い回す(数が増えない)。知人の口は呼ばれない。口つきの 4 構成では控えは動かない(道が違う)。"""
    ev = record("near_table")["events"]
    assert "acquaintance_fn" not in {e[0] for e in ev}
    by = acq_cache_by_tick(ev)
    assert by[TICKS[0]] > 0 and by[TICKS[1]] == by[TICKS[0]], by
    for cfg in ("fixed", "ranking", "near", "calendar"):
        assert acq_cache_by_tick(record(cfg)["events"]) == {t: 0 for t in TICKS}, cfg


def _no_acq_cache_class() -> type:
    """負の対照の子クラス: 知人表を毎回引き、控え(``_acq_cache``)に書かない(メソッドの名で差し替える=割った後も同じ形)。"""

    def _acquaintances_of(self: Any, i: int, tick: int = -1) -> tuple[frozenset[int], np.ndarray]:
        names = frozenset(int(x) for x in self.acquaintances.get(i, ()))
        return names, np.fromiter(sorted(names), dtype=np.int64, count=len(names))

    return type("NoAcqCache", (Renderer,), {"_acquaintances_of": _acquaintances_of})


def test_negative_skipping_the_acquaintance_cache_is_caught():
    """〔検収の中-1〕負の対照: 知人の控えを使わない子クラスを ``near_table`` で回すと、(a) の完全一致が違い、上の控えの確かめが
    落ちる形になる(控えの数が 0 のまま)。"""
    got = record("near_table", _no_acq_cache_class())
    assert got["events"] != _frozen()["configs"]["near_table"]["events"]
    assert acq_cache_by_tick(got["events"])[TICKS[0]] == 0
