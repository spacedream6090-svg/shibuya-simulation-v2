"""第 1 期 1-2 知覚の分離: 「状態 → Percept → 文」の描画が 1-2 の前の描画とバイト一致(口の約束 1-2 の約束 (1))。

比べる相手は本体 HEAD ``136fdbb`` の ``renderer.py`` のバイトそのままの写し(``head_renderer_136fdbb.py``・sha256 は
``scenes.HEAD_RENDERER_SHA256``)。同じ世界・個体・資産・設定・口を持つ「双子」を作り、同じ刻みの同じ前計算の材料
(``prepare_tick`` の引数)と同じ描画の引数で描かせて、本文・ブロック・指紋・トークン・切り詰め・想起の列・知人の列を比べる。

(A) 合成の場面 13 種(固定枠・単一ランキング・看板の注視 p_see(1-2 で活動の乗数は消した=HEAD の双子は乗数の表が既定の
    全部 1.0)・広告ゼロ・語彙 v3 と活動の行・空腹の語・
    近接の並びと同点・注意の焦点・想起と意図と被招待と閉店の 1 句と知人と会話の参加者・天気の実日・役割語と自由意図・
    行列と顕著な出来事・被注視の人数)× 4 刻み × 全員(起床の理由・直前の結果・直前の行動・招待者を振る)。計数(命中・
    切り詰め・意図・想起・閉店・注視の抽選・近接の同点)も双子と同じ。
(B) byte-check の 19 構成(``wave2_bytecheck.configs()``)× 代表の刻み(朝・昼・夕の 3 つの窓=各構成 3 刻み以上で描画が
    ある)で、ランの中の描画を全部双子と比べる(世界資産が要る=``requires_data("world_v2")``)。5,000 体・1 日の全部の
    呼の一致は byte-check(テープの ``prompt_hash`` の列の sha)が見る(記録 p12/README.md)。

〔段 5-1b 検収 L5〕nav1 のランは前計算に ``los_stage``(密度の段)を渡す。HEAD の双子の口には無いので、双子には同じ段を写して B4 の欄と
指紋を今の ``perception.hashes`` で作り直す=この 2 欄(``b4_field_rows``・``b4_field_hash``)は双子と独立には比べていない(文・ブロック・
指紋・トークンほか残りの欄は比べている)。
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from shibuya.agents.state import Activity, ActivityKind, IntentKind, ResultCode, WakeCondition
from shibuya.engine.memory import RecallItem
from shibuya.perception import renderer as R
from tests.perception.facts.scenes import build, head_module, twin

ROOT = Path(__file__).resolve().parents[3]
#: 朝・昼・夕・翌日(刻み % 3 が 1・0・2・0=前計算の材料の顕著な出来事と行列の人数が刻みで変わる)。
TICKS = (481, 750, 1142, 1500)
COUNTERS = ("cache_hits", "cache_misses", "renders", "truncation_count", "intent_lines", "intent_lines_over_budget",
            "memory_lines", "memory_items", "memory_items_dropped_for_budget", "memory_items_dropped_for_channel",
            "memory_lines_over_budget", "named_closed_notes", "signage_gate_draws", "signage_gate_shown",
            "near_order_ties", "near_tie_breaks", "near_tie_candidates")


def same_rendered(x: Any, y: Any) -> list[str]:
    """2 つの描画の結果で違う欄の名(空なら同じ)。"""
    bad = []
    for k in ("text", "prompt_hash", "prefix_key", "tokens_est", "group_tokens", "truncations", "recalled_rows",
              "recalled_first_tick", "recalled_kind", "recalled_object", "acquaintance_ids", "agent_id", "tick"):
        if getattr(x, k) != getattr(y, k):
            bad.append(k)
    if dict(x.blocks) != dict(y.blocks) or list(x.blocks) != list(y.blocks):
        bad.append("blocks")
    if dict(x.block_hashes) != dict(y.block_hashes):
        bad.append("block_hashes")
    return bad


def recall_for(head: Any, out: Any) -> None:
    """双子の想起の口=1-2 の側が引いた行をそのまま返す(想起の計数を 2 回にしない)。"""
    m = out.percept.memories
    head.memory_recall = (lambda *_a, _m=m: list(_m)) if m is not None else None


# ================================================================= (A) 合成の場面
def _memories(i: int, t: int, c: int, inv: int) -> list[RecallItem]:
    if i % 3 == 0:
        return []
    return [
        RecallItem(row=i % 7, last_tick=t - 30, kind=7, partner=(i + 1) % 50, obj=-1, result=0, cell=2,
                   gist="駅前の店の話をした", first_tick=t - 90),
        RecallItem(row=8 + i % 3, last_tick=-1, kind=3, partner=-1, obj=1, result=int(ResultCode.CLOSED), cell=1,
                   gist="", first_tick=t - 400),
        RecallItem(row=20, last_tick=t - 5, kind=12, partner=-1, obj=0, result=0, cell=0, gist="", valence=1,
                   source=1, first_tick=t - 600),
    ][: 1 + i % 3]


def _setup_rich(r: R.Renderer, a: Any) -> None:
    r.memory_recall = _memories
    r.acquaintance_fn = lambda i, t: [(i + 1) % a.n, (i + 2) % a.n, -5, a.n + 3]
    r.session_partner_fn = lambda i: [(i + 3) % a.n] if i % 2 else []
    closed = {i: (1, 1, 600) for i in range(a.n) if i % 5 == 0}
    r.named_closed_lookup = lambda i: closed.get(int(i))
    with a.writable():
        for i in range(a.n):
            a.intent_action[i] = (3, 24, 22, 5, 11, -1, 99)[i % 7]
            a.intent_kind[i] = (int(IntentKind.POI_NAMED), int(IntentKind.POI_CATEGORY), int(IntentKind.PERSON),
                                int(IntentKind.BED), int(IntentKind.NONE), int(IntentKind.POI_NAMED),
                                int(IntentKind.POI_NAMED))[i % 7]
            a.intent_target[i] = (1, 2, 4, 0, 0, 999, 1)[i % 7]
        a.last_result[0:40:5] = int(ResultCode.CLOSED)


def _setup_v3(r: R.Renderer, a: Any) -> None:
    with a.writable():
        a.activity_kind[:] = np.arange(a.n) % 5
        a.activity[a.activity_kind == int(ActivityKind.IN_PLACE)] = int(Activity.CONVERSING)


def _setup_focus(r: R.Renderer, a: Any) -> None:
    with a.writable():
        a.focus_target[:] = (np.arange(a.n) + 1) % a.n
        a.focus_target[::4] = -1


def _setup_weather(r: R.Renderer, a: Any) -> None:
    r.weather_date_fn = lambda: "2026-07-29"


SCENES: dict[str, tuple[dict, dict, Any]] = {
    # 名: (描画の設定, 個体の欄, 用意)
    "default": ({}, {}, None),
    "ranking": ({"budget_mode": "ranking"}, {}, None),
    "ranking_rich": ({"budget_mode": "ranking", "acquaintances": {0: (1, 2), 5: (6,)}}, {}, _setup_rich),
    "p_see_gate": ({"signage_p_see": 0.3}, {"activity_columns": True}, _setup_v3),
    "signage_off": ({"signage_enabled": False}, {}, None),
    "v3_activity": ({"vocab_version": "v3"}, {"activity_columns": True}, _setup_v3),
    "hunger_words_all": ({"hunger_words": "all"}, {"energy_columns": True}, None),
    "hunger_words_hungry": ({}, {"energy_columns": True}, None),
    "near_id": ({"near_order": "id", "near_tiebreak": "id"}, {}, None),
    "focus": ({}, {"attention_columns": True}, _setup_focus),
    "rich": ({"acquaintances": {0: (1, 2, 3), 7: (8,)}, "watched_by": np.arange(120) % 3}, {}, _setup_rich),
    "weather_date": ({}, {}, _setup_weather),
    "role_open_v1": ({"role_words": True, "intent_mode": "open", "vocab_version": "v1"}, {}, None),
}


def _prepare_kwargs(t: int, w: Any) -> dict:
    """前計算の材料(行列・活動の行・顕著な出来事・流れ)。刻みで中身を変える。"""
    n = w.n_cells
    k = t % 3
    return {
        "queues": [(0, "物販0000", 3 + k), (1, "コンビニ0001", 7), (2, "店の名", 0)],
        "activity_rows": {0: (("歩いている", 4), ("話している", 2)), 3: (("待っている", 1 + k),)},
        "salient_events": {1: ("[顕著] 人だかりができている。",), 2: ()} if k else None,
        "flow": (np.arange(n) + k) % 3,
    }


def _calls(i: int, t: int):
    reasons = (3, 5, int(WakeCondition.CONVERSATION_TURN), "予定の時刻になりました。",
               int(WakeCondition.ACTIVITY_EXPIRY), 99)
    results = (None, None, int(ResultCode.MONEY_SHORT), int(ResultCode.CLOSED), int(ResultCode.FARE_SHORT),
               int(ResultCode.OK), int(ResultCode.NO_TRAIN))
    return dict(
        wake_reason=reasons[(i + t) % len(reasons)],
        last_result=results[(i * 7 + t) % len(results)],
        last_action=(None, "移動", "")[i % 3],
        inviter=(None, None, -1, (i + 5) % 120)[i % 4],
    )


@pytest.mark.parametrize("name", sorted(SCENES))
def test_synthetic_scenes_render_the_same_bytes_as_head(name):
    rkw, akw, setup = SCENES[name]
    w, a = build(n_agents=120, n_cells=9, seed=11, **akw)
    r = R.Renderer(w, a, seed=7, **rkw)
    if setup is not None:
        setup(r, a)
    h = twin(r)
    n = 0
    for t in TICKS:
        kw = _prepare_kwargs(t, w)
        r.prepare_tick(t, **kw)
        h.prepare_tick(t, **kw)
        for i in range(a.n):
            c = _calls(i, t)
            out = r.render(i, tick=t, **c)
            recall_for(h, out)
            ho = h.render(i, tick=t, **c)
            assert same_rendered(out, ho) == [], (name, t, i, c, out.text, ho.text)
            assert r.draw(out.percept) == out.text  # 描き方の口(同じ Percept → 同じ文)
            n += 1
    assert n == len(TICKS) * a.n
    # draw で 1 回ずつ多く描いたぶん、描画の数と命中の計数は 2 倍側にずれる=計数は draw の前の双子で見る(下)
    assert r.renders == 2 * h.renders


@pytest.mark.parametrize("name", sorted(SCENES))
def test_counters_match_head(name):
    """描画の計数(診断の行 O84)も 1-2 の前と同じ(draw を呼ばずに比べる)。"""
    rkw, akw, setup = SCENES[name]
    w, a = build(n_agents=120, n_cells=9, seed=12, **akw)
    r = R.Renderer(w, a, seed=7, **rkw)
    if setup is not None:
        setup(r, a)
    h = twin(r)
    for t in TICKS[:3]:
        kw = _prepare_kwargs(t, w)
        r.prepare_tick(t, **kw)
        h.prepare_tick(t, **kw)
        for i in range(0, a.n, 2):
            c = _calls(i, t)
            out = r.render(i, tick=t, **c)
            recall_for(h, out)
            h.render(i, tick=t, **c)
    got = {k: getattr(r, k) for k in COUNTERS}
    want = {k: getattr(h, k) for k in COUNTERS}
    assert got == want
    assert r.memory_line_tokens == h.memory_line_tokens
    assert r.report() == h.report()


def test_negative_control_one_byte_change_is_caught(monkeypatch):
    """負の対照: 描き方を 1 文字だけ変えると双子との比べで落ちる(比べが恒真でない)。"""
    w, a = build(n_agents=60, seed=15)
    r = R.Renderer(w, a, seed=7)
    h = twin(r)
    orig = R.near_person_text
    monkeypatch.setattr(R, "near_person_text", lambda sp: orig(sp).replace("P-", "Q-"))
    r.prepare_tick(750)
    h.prepare_tick(750)
    bad = [same_rendered(r.render(i, tick=750), h.render(i, tick=750)) for i in range(a.n)]
    assert any("text" in b and "blocks" in b for b in bad)


def test_render_without_prepare_and_out_of_area_cells():
    """``prepare_tick`` を呼ばずに描く道(``render`` が自分で前計算する)と、セルの外の体も同じ。"""
    w, a = build(n_agents=40, seed=13)
    with a.writable():
        a.cell[5] = -1
        a.cell[6] = w.n_cells + 4
    for mode in ("fixed", "ranking"):
        r = R.Renderer(w, a, seed=3, budget_mode=mode)
        h = twin(r)
        for t in (100, 101, 900):
            for i in (0, 5, 6, 7):
                out = r.render(i, tick=t)
                ho = h.render(i, tick=t)
                assert same_rendered(out, ho) == [], (mode, t, i)
        assert r.render(5, tick=900).percept.scene.in_area is False


def test_a_percept_from_another_step_is_refused():
    """刻みの外で残らない(1-2 の約束 (3)): 前の刻みの Percept は描かない。"""
    w, a = build(n_agents=20, seed=14)
    r = R.Renderer(w, a, seed=3)
    p = r.render(0, tick=600).percept
    assert r.draw(p) == r.render(0, tick=600).text
    r.prepare_tick(601)
    with pytest.raises(ValueError, match="刻み"):
        r.render_percept(p)


# ================================================================= (B) byte-check の 19 構成 × 代表の刻み
#: 代表の刻み(朝・昼・夕の窓)。ランはその最後の窓の終わりまで回し、**全部の刻みの描画**を双子と比べる(双子の
#: キャッシュを 1-2 の側と同じ温まり方にする=キャッシュの外れで足される切り詰めの記録まで同じにするため)。窓は
#: 「各構成 3 刻み以上で描画がある」ことの確かめに使う。
WINDOWS = ((420, 432), (720, 732), (1020, 1032))
N_AGENTS = 300


def _wave2_configs() -> dict[str, dict]:
    path = ROOT / "docs" / "bench" / "analysis" / "wave2-2026-09-30" / "wave2_bytecheck.py"
    spec = importlib.util.spec_from_file_location("_p12_wave2_bytecheck", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_p12_wave2_bytecheck"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod.configs()


def _shadow(monkeypatch: pytest.MonkeyPatch) -> dict:
    """1-2 の描画の ``prepare_tick``・``render`` に HEAD の双子を付ける(ランの最初の前計算から全部の刻み)。"""
    head_module()
    twins: dict[int, Any] = {}
    stats: dict[str, Any] = {"n": 0, "ticks": set(), "bad": [], "pairs": []}
    orig_prep, orig_render = R.Renderer.prepare_tick, R.Renderer.render

    def prep(self, tick, **kw):  # noqa: ANN001
        orig_prep(self, tick, **kw)
        if id(self) not in twins:
            twins[id(self)] = twin(self)
            stats["pairs"].append((self, twins[id(self)]))
        # 〔段 5-1b〕nav1 のランは密度の段(los_stage)を材料として渡す(HEAD の双子の口には無い)=双子には同じ段を写して
        # B4 の欄を同じ式で作り直す(描画の比べは「同じ材料 → 同じ文」のまま)
        los = kw.get("los_stage")
        h = twins[id(self)]
        h.prepare_tick(tick, **{k: v for k, v in kw.items() if k != "los_stage"})
        if los is not None:
            import dataclasses as _dc

            from shibuya.perception import hashes as _H

            tc = h._tickc
            ls = np.asarray(los, dtype=np.uint8).copy()
            rows = _H.b4_field_row(ls, tc.noise_stage, tc.flow, tc.salient_digest)
            h._tickc = _dc.replace(tc, los_stage=ls, b4_field_rows=rows, b4_field_hash=_H.field_row_hashes(rows))

    def render(self, agent_id, tick, wake_reason=3, last_result=None, last_action=None, inviter=None):  # noqa: ANN001
        out = orig_render(self, agent_id, tick, wake_reason, last_result, last_action, inviter)
        h = twins[id(self)]
        assert h._tickc.tick == int(tick)  # 双子も同じ材料で前計算した
        recall_for(h, out)
        ho = h.render(agent_id, tick, wake_reason=wake_reason, last_result=last_result,
                      last_action=last_action, inviter=inviter)
        bad = same_rendered(out, ho)
        if bad:
            stats["bad"].append((int(tick), int(agent_id), bad))
        stats["n"] += 1
        stats["ticks"].add(int(tick))
        return out

    monkeypatch.setattr(R.Renderer, "prepare_tick", prep)
    monkeypatch.setattr(R.Renderer, "render", render)
    return stats


CONFIG_NAMES = sorted(
    ("w6_v3_default", "w6_v3_activity_off", "w6_v1_default", "w6_v1_derive_v2_1", "w6_v2", "w6_v1_edge", "w6_v2_edge",
     "w6_v1_edge_plateau", "w6_old_v1_default", "w6_old_v1_derive_v2_1", "w6_old_v2", "w6_old_v1_edge",
     "w6_old_v2_edge", "w6_old_v1_edge_plateau", "w6_golden_null_arm", "v3_mem_store", "v3_mem_rel", "v3_classical",
     "v3_classical_mem_rel")
)


@pytest.mark.requires_data("world_v2")
def test_the_19_configs_are_the_byte_check_set():
    assert sorted(_wave2_configs()) == CONFIG_NAMES


@pytest.mark.requires_data("world_v2")
@pytest.mark.parametrize("config", CONFIG_NAMES)
def test_19_configs_render_the_same_bytes_as_head(config, monkeypatch, tmp_path):
    from shibuya import cli

    from shibuya.engine import proximity as P

    kw = dict(_wave2_configs()[config])
    stats = _shadow(monkeypatch)
    # 〔第 2 期 2-4 V2〕近接の既定は distance になった。比べる相手(HEAD 136fdbb の描画の写し)は B5 の近接行の
    # distance の道(2-2 の _nearby_people_distance)を持たない=1-2 の分離の一致は切替口 cell の道で見る(前と同じ比べ)
    monkeypatch.setattr(P, "_ARM", P.MODE_CELL)
    cli.run(n_agents=N_AGENTS, seed=1, world_dir=str(ROOT / "data" / "world" / "v2"), ticks=WINDOWS[-1][1],
            tape_path=tmp_path / "tape", **kw)
    assert stats["bad"] == [], stats["bad"][:5]
    assert len(stats["pairs"]) == 1
    r, h = stats["pairs"][0]
    assert {k: getattr(r, k) for k in COUNTERS} == {k: getattr(h, k) for k in COUNTERS}  # 診断の計数も同じ
    windows_hit = {lo for lo, hi in WINDOWS for t in stats["ticks"] if lo <= t < hi}
    assert len(stats["ticks"]) >= 3 and len(windows_hit) == len(WINDOWS), (config, sorted(stats["ticks"]))
    assert stats["n"] >= 3
