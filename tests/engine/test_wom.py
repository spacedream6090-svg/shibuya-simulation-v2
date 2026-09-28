"""D-120 7b: **会話からの店の抽出**(N3 (a)・口コミ=伝聞の書き手・第297)のテスト。

正典: ``docs/design/v2-store-memory-implementation-agenda.md`` §2(段 7b の 1〜6)。
見るもの: (a) 合成テープ=店名+評価語の文 20 本が 20/20 で照合・誤照合 0(チェーン名 2 本=話し手に近い順・
接尾辞つき 2 本・無関係の語 4 本=0 件)・向きの表 (b) 正規化 v0・境界・店らしき語 (c) 聞き手(宛先)の店の行
だけが増える・出どころ=伝聞・精度 +重み × 1/4 (d) ラン: 既定は抽出しない・店の記憶 on でも挙動は同じ・
mock は店名を書かない=0 件・名を話す LLM なら宛先の行が増える (e) 7a の小修正 Q77(並ぶの成功は向き 0)。
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import numpy as np
import pytest

from shibuya.agents.state import STORE_MEMORY_FIELDS, AgentState, ResultCode
from shibuya.engine import memory as M
from shibuya.engine import store_memory as SM
from shibuya.engine import wom as W

SRC = Path("src/shibuya")

# ---- 合成の辞書(POI 索引 → 名・cat・セル)。セル間の距離は |i−j| × 100 m ----
NAMES = [
    "一蘭 渋谷店",            # 0 空白つきの支店 → 「一蘭」でも引ける
    "ビーフキッチン渋谷店",    # 1 支店の接尾辞 → 「ビーフキッチン」
    "スターバックス",          # 2 チェーン(セル 0)
    "スターバックス",          # 3 チェーン(セル 2)
    "スターバックス",          # 4 チェーン(セル 3)
    "松屋",                    # 5 2 字
    "一番",                    # 6 2 字(「一番近い」では引かない)
    "ライフ",                  # 7 カタカナ(「ライフスタイル」では引かない)
    "cafe cafe",               # 8 英字
    "渋谷区役所",              # 9 店ではない(office)=辞書に入れない
    "コメダ珈琲店",            # 10 接尾辞「店」→「コメダ珈琲」
    "富士そば",                # 11
    "ドトールコーヒーショップ",  # 12
    "天狗",                    # 13
    "カフェ・ベローチェ",      # 14
]
CATS = ["food"] * len(NAMES)
CATS[9] = "office"
CELLS = np.array([0, 0, 0, 2, 3, 1, 1, 1, 2, 1, 2, 3, 0, 1, 2])
DIST = (np.abs(np.arange(4)[:, None] - np.arange(4)[None, :]) * 100).astype(np.uint16)


def ex() -> W.WomExtractor:
    return W.WomExtractor(NAMES, CATS, CELLS, DIST)


#: 合成テープ(店名+評価語の文 20 本)=(文, 話し手のセル, 期待する POI, 期待する向き)。
TAPE_20 = [
    ("一蘭 渋谷店のラーメンがおいしかった", 0, 0, 1),
    ("一蘭は混んでいた", 0, 0, -1),                         # 接尾辞つき(空白の支店を外した名)
    ("ビーフキッチンがおすすめ", 0, 1, 1),                   # 接尾辞つき(渋谷店を外した名)
    ("ビーフキッチン渋谷店は高すぎ", 0, 1, -1),
    ("スターバックスが良かった", 2, 3, 1),                   # チェーン: セル 2 の話し手 → セル 2 の店
    ("スターバックスは売り切れだった", 3, 4, -1),            # チェーン: セル 3 の話し手 → セル 3 の店
    ("松屋で食べた、安かった", 1, 5, 1),
    ("松屋はまずい", 1, 5, -1),
    ("cafe cafeで休んだ、快適", 2, 8, 1),
    ("CAFE CAFEは閉まっていた", 2, 8, -1),                   # 全角/大文字の正規化
    ("コメダ珈琲で満足", 2, 10, 1),
    ("コメダ珈琲店がひどかった", 2, 10, -1),
    ("富士そばがうまい", 3, 11, 1),
    ("富士そばは待たされた", 3, 11, -1),
    ("ドトールコーヒーショップが最高", 0, 12, 1),
    ("ドトールコーヒーショップは満席", 0, 12, -1),
    ("天狗で飲んだ、楽しかった", 1, 13, 1),
    ("天狗はうるさい", 1, 13, -1),
    ("カフェ・ベローチェが好き", 2, 14, 1),
    ("カフェ・ベローチェは最悪", 2, 14, -1),
]
#: 無関係の語 4 本(店の名に見える部分があっても引かない)。
UNRELATED_4 = [
    "一番近いところへ行きたい",
    "ライフスタイルが大事",
    "食事の必要性が高い",
    "渋谷区役所に行った",
]


# ================================================================= (a) 合成テープ
def test_synthetic_tape_matches_20_of_20_and_unrelated_0():
    e = ex()
    got = []
    for text, cell, want_poi, want_v in TAPE_20:
        r = e.extract(W.normalize_v0(text), cell)
        e.observe(r)
        got.append((r.pois, r.valence))
        assert r.pois == (want_poi,), (text, r)
        assert r.valence == want_v, (text, r)
    assert sum(1 for p, _ in got if p) == 20
    for text in UNRELATED_4:
        r = e.extract(W.normalize_v0(text), 1)
        e.observe(r)
        assert r.pois == () and r.valence == 0, (text, r)
    s = e.summary(NAMES)
    assert s["counts"]["utterances"] == 24 and s["counts"]["wom_extracted"] == 20
    assert s["counts"]["wom_with_valence"] == 20
    assert s["counts"]["wom_valence+1"] == 10 and s["counts"]["wom_valence-1"] == 10


def test_chain_names_pick_the_store_nearest_to_the_speaker():
    e = ex()
    assert e.extract(W.normalize_v0("スターバックス"), 0).pois == (2,)
    assert e.extract(W.normalize_v0("スターバックス"), 2).pois == (3,)
    assert e.extract(W.normalize_v0("スターバックス"), 3).pois == (4,)
    assert e.extract(W.normalize_v0("スターバックス"), -1).pois == (2,)  # 範囲外は索引の小さい方


def test_valence_needs_a_store_and_mixed_words_cancel():
    e = ex()
    assert e.extract(W.normalize_v0("おいしかった"), 0).valence == 0          # 店が無ければ向きは付けない
    assert e.extract(W.normalize_v0("松屋、安かったけどまずい"), 1).valence == 0  # +1 と −1 で 0
    assert e.extract(W.normalize_v0("松屋に行った"), 1).valence == 0         # 知っているだけ
    assert e.extract(W.normalize_v0("松屋はおいしくなかった"), 1).valence == -1  # 否定形は −1(最長一致)


# ================================================================= (b) 正規化・境界・店らしき語
def test_normalize_and_boundaries_and_store_like_words():
    assert W.normalize_v0("ＣＡＦＥ　Ｃａｆｅ ") == "cafecafe"
    e = ex()
    assert e.extract(W.normalize_v0("天下一品が閉まっていた"), 0).unmatched == ()   # 「〜屋/店…」で終わらない
    r = e.extract(W.normalize_v0("大勝軒が良かった、ラーメン屋より"), 0)
    assert r.pois == () and r.unmatched == ("大勝軒",)                                 # 総称「ラーメン屋」は数えない
    r = e.extract(W.normalize_v0("松屋と日高屋に行った"), 1)
    assert r.pois == (5,) and r.unmatched == ("日高屋",)
    assert "渋谷区役所" not in e.keys and "一蘭" in e.keys and "コメダ珈琲" in e.keys
    assert W.WOM_TEXT_FIELDS == {"v1": ("comment",), "v2": ("comment",), "v3": ("reason", "target")}
    assert e.utterance_text("v3", comment="x", reason="松屋が良かった", target="なし") == "松屋が良かった"
    assert e.utterance_text("v2", comment="一蘭おすすめ", reason="松屋", target="天狗") == "一蘭おすすめ"


def test_words_inside_a_store_name_are_not_valence_words():
    e = W.WomExtractor(["満足屋", "人気ラーメン"], ["food", "food"], np.array([0, 0]), DIST)
    assert e.extract(W.normalize_v0("満足屋に行った"), 0).valence == 0
    assert e.extract(W.normalize_v0("人気ラーメンはまずい"), 0).valence == -1


def test_person_refs_and_digit_only_names_do_not_match():
    e = W.WomExtractor(["526", "松屋"], ["food", "food"], np.array([0, 0]), DIST)
    assert "526" not in e.keys
    assert e.extract(W.normalize_v0("会話への応答|P-526"), 0).pois == ()
    r = e.extract(W.normalize_v0("カテゴリ飲食店と10時開店の松屋"), 0)
    assert r.pois == (1,) and r.unmatched == ()  # 「X+総称」は店らしき語に数えない


# ================================================================= (c) 聞き手の行
def table(n: int = 3) -> AgentState:
    a = AgentState(n, memory_columns=True, memory_n=32, store_memory_columns=True)
    with a.writable():
        a.cell[:] = 1
    return a


def test_hear_writes_only_the_listener_row_as_word_of_mouth():
    a = table()
    lay = M.MemoryLayer(3, 32, minutes_per_tick=1.0)
    st = lay.enable_store()
    r = ex().extract(W.normalize_v0("松屋がおいしかった"), 1)
    assert W.hear(st, a, 10, 2, r) == 1
    assert (a.sm_poi[0] == -1).all() and (a.sm_poi[1] == -1).all()   # 話し手(0)・第三者(1)は書かない
    j = int(np.flatnonzero(a.sm_poi[2] == 5)[0])
    assert int(a.sm_source[2, j]) == SM.STORE_SOURCE_BIT["wom"]
    assert float(a.sm_precision[2, j]) == pytest.approx(0.25) and float(a.sm_valence[2, j]) == pytest.approx(0.25)
    assert st.stats["events:wom"] == 1 and st.stats["events:wom:valence+1"] == 1
    W.hear(st, a, 11, 2, r, weight=0.5)                                  # 非宛先の重み(本段では使わない)
    assert float(a.sm_precision[2, j]) == pytest.approx(0.375)
    assert W.hear(st, a, 12, -1, r) == 0 and W.hear(None, a, 12, 2, r) == 0


def test_queue_success_is_valence_zero_q77():
    a = table()
    lay = M.MemoryLayer(3, 32, minutes_per_tick=1.0)
    lay.enable_store()
    ok = int(ResultCode.OK)
    lay.record(a, 5, np.array([0, 0]), np.array([M.EVENT_KINDS["queue"], M.EVENT_KINDS["buy"]]),
               np.array([-1, -1]), np.array([7, 7]), np.array([ok, ok]), np.array([1, 1]))
    j = int(np.flatnonzero(a.sm_poi[0] == 7)[0])
    assert float(a.sm_valence[0, j]) == 1.0 and float(a.sm_precision[0, j]) == 2.0  # 並ぶ 0+購入 +1
    assert lay.store.stats["events:self:valence0"] == 1 and lay.store.stats["events:self:valence+1"] == 1


# ================================================================= (d) ラン
class _TalkingLLM:
    """会話の呼(wake_class 0)の理由欄に店名と評価語を書く mock の包み(テスト用)。"""

    def __init__(self, inner, name: str) -> None:
        self.inner = inner
        self.name = name

    def complete(self, request):
        r = self.inner.complete(request)
        if int(request.wake_class) != 0:
            return r
        lines = [f"理由: {self.name}がおいしかった" if ln.startswith("理由:") else ln
                 for ln in r.text.splitlines()]
        return dataclasses.replace(r, text="\n".join(lines))


WORLD = "data/world/v2"


def _real_world_or_skip() -> None:
    from shibuya.world.assets import assets_available

    if not assets_available(WORLD):
        pytest.skip("W 資産(data/world/v2)が無い=会話の起きる世界が無い")


def test_default_has_no_wom_and_mock_extracts_nothing():
    _real_world_or_skip()
    from shibuya import cli

    kw = dict(n_agents=300, seed=1, world_dir=WORLD, vocab_version="v3")  # 会話の起きる規模(mock)
    off = cli.run(**kw)
    assert off.run_manifest_fields()["wom"] == {}
    mem = cli.run(memory="on", **kw)
    assert mem.run_manifest_fields()["wom"] == {}
    mp = pytest.MonkeyPatch()
    mp.setattr(AgentState, "state_hash", lambda self: self.registry.state_hash(exclude=STORE_MEMORY_FIELDS))
    try:
        on = cli.run(memory="on", store_memory="on", **kw)
    finally:
        mp.undo()
    assert on.final_hash == mem.final_hash and on.llm_calls == mem.llm_calls
    w = on.run_manifest_fields()["wom"]
    assert w["counts"].get("utterances", 0) > 0 and w["counts"].get("wom_extracted", 0) == 0
    assert w["store_rows_with_wom"] == 0


def test_a_talking_llm_writes_word_of_mouth_rows_for_listeners_only():
    _real_world_or_skip()
    from shibuya import cli
    from shibuya.engine.run import _default_mock

    kw = dict(n_agents=300, seed=1, world_dir=WORLD, vocab_version="v3", memory="on")
    base = cli.run(llm=_TalkingLLM(_default_mock(1, "v3"), "スターバックス"), **kw)
    mp = pytest.MonkeyPatch()
    mp.setattr(AgentState, "state_hash", lambda self: self.registry.state_hash(exclude=STORE_MEMORY_FIELDS))
    try:
        on = cli.run(llm=_TalkingLLM(_default_mock(1, "v3"), "スターバックス"), store_memory="on", **kw)
    finally:
        mp.undo()
    assert on.final_hash == base.final_hash and on.llm_calls == base.llm_calls  # 書くだけ
    w = on.run_manifest_fields()["wom"]
    assert w["counts"]["wom_extracted"] == w["counts"]["utterances"] > 0
    assert w["counts"]["wom_valence+1"] == w["counts"]["wom_extracted"]
    assert set(w["top_pois"]) == {"スターバックス"} and w["store_rows_with_wom"] > 0
    r = on.agents.registry
    from shibuya.world.state import World

    names = World.load_or_synthetic(WORLD).assets.poi_name
    wom_rows = (r.sm_source & SM.STORE_SOURCE_BIT["wom"]) > 0
    pois = set(r.sm_poi[wom_rows].tolist())
    assert {str(names[j]) for j in pois} == {"スターバックス"}                   # チェーンの近い 1 件ずつ
    assert w["store_events_wom"] == w["counts"]["wom_extracted"]            # 1 発話=宛先 1 人に 1 件
    assert np.all(r.sm_valence[wom_rows] > 0)


def test_extraction_is_per_call_string_work():
    """P4: 抽出は呼ごとの文字列処理(体数に比例するループを書かない)=宣言が本文にある。"""
    src = (SRC / "engine/wom.py").read_text(encoding="utf-8")
    assert "逐次ループ宣言" in src and "呼数比例" in src
