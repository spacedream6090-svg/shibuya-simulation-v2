"""語彙 v2 の描画側 — B0 の出力規約に 13 語目「食事」が載る(D-71 §3 E/F)。

見るもの(``tests/perception/test_intent_mode_open.py`` と同じ書き方)
(b) **既定は 1 バイトも動かない**: ``template_sha256()`` が 161fe181…・``b0_sha256("vocab")``
    が 2b4bfc8a…・参照場面の ``prompt_hash`` が bb23f7c6…(⑥ の golden と同じ場面)/
(c) 腕の差は **``行動:`` の 1 行だけ**(理由・対象・ひと言・2 行形・JSON 禁止は同文)/
(d) ``intent_mode``(3 腕)× ``vocab_version``(2 版)の **6 通りが全て成立**する。
    ``open`` は語彙を見せないので v1/v2 で B0 が**同一**(差は段0 辞書とエンジン側)。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.agents.state import AgentKind, AgentState
from shibuya.llm.contract import ACTION_VOCAB_13, ALL_ACTION_WORDS
from shibuya.perception import templates as T
from shibuya.perception.renderer import Renderer
from shibuya.world.state import World

#: 凍結テンプレの SHA(``tests/perception/test_templates.py`` と**同じ値**)。
FROZEN_TEMPLATE_SHA256 = "161fe181bc325f003d874fb5c91e6142c01449fb09ac5f8b377b715a945608de"
#: 既定(vocab × v1)の B0 本文の SHA。
B0_SHA256_VOCAB_V1 = "2b4bfc8a6da16ec73cbd3db8c68656150d2becd08100efa8816ad649e478339c"
#: **語彙 v2 の凍結値**(2026-09-17 に凍結。13 語の並びか文面を変えたら必ずここが動く)。
B0_SHA256_VOCAB_V2 = "9b4f75d497bc26f68d4115fc217a46bd1465a7aa971aea6db93dca6244b229ee"
#: 同(hint 腕 × 語彙 v2)。
B0_SHA256_HINT_V2 = "124ba1a77641c1f8c2b39bed45a3c44ccf4353f58dbd593bfb9f348cf5bc3afe"
#: 参照場面の指紋(``test_ablation6_signage.GOLDEN_FIXED_PROMPT_HASH`` と同じ場面・同じ値)。
GOLDEN_FIXED_PROMPT_HASH = "bb23f7c69a82460b6820292404eb640b722ed0c7aa7a545afc9e09c697d8a5c5"


def scene(*, intent_mode: str = "vocab", vocab_version: str = "v1", n: int = 12, n_cells: int = 9):
    """``test_intent_mode_open.scene`` と同じ合成場面(乱数の引き方まで同じ)。"""
    w = World.synthetic(n_cells=n_cells, seed=2)
    a = AgentState(n)
    g = np.random.default_rng(11)
    with a.writable():
        a.cell[:] = g.integers(0, n_cells, size=n)
        a.xy[:] = g.uniform(0.0, 80.0, size=(n, 2))
        a.kind[:] = AgentKind.VISITOR
        a.money[:] = 5_000
        a.hunger[:] = 6
        a.last_result_tick[:] = 1
    w.cells.density[:] = w.compute_density(a.cell)
    r = Renderer(w, a, seed=13, intent_mode=intent_mode, vocab_version=vocab_version)
    r.prepare_tick(750)
    return r, r.render(0, tick=750, wake_reason=3)


# ------------------------------------------------------- (b) 既定は 1 バイトも動かない
def test_the_default_bytes_are_frozen():
    assert T.template_sha256() == FROZEN_TEMPLATE_SHA256
    assert T.b0_sha256() == T.b0_sha256("vocab") == B0_SHA256_VOCAB_V1
    assert T.b0_sha256("vocab", "v1") == B0_SHA256_VOCAB_V1
    assert T.b0_system("vocab", "v1") is T.TEMPLATES["B0.system"]
    assert T.DEFAULT_VOCAB_VERSION == "v1" and T.VOCAB_VERSIONS == ("v1", "v2")


def test_the_reference_scene_prompt_hash_is_unchanged():
    _, rendered = scene()
    assert rendered.prompt_hash == GOLDEN_FIXED_PROMPT_HASH


def test_the_thirteen_word_list_matches_the_contract():
    """層契約で二重定義になっている 13 語の並びが ``llm.contract`` と一致する。"""
    assert T.ACTION_WORDS_13 == ACTION_VOCAB_13 == T.ACTION_WORDS_12 + ("食事",)
    assert T.ACTION_WORDS_12 == ALL_ACTION_WORDS[:12]


# ------------------------------------------------------- (a) 切替が効く
def test_v2_changes_the_b0_and_shows_the_new_word():
    assert T.b0_system("vocab", "v2") == T.B0_SYSTEM_V2
    assert T.b0_sha256("vocab", "v2") == B0_SHA256_VOCAB_V2 != B0_SHA256_VOCAB_V1
    assert "食事" in T.B0_SYSTEM_V2 and "食事" not in T.B0_SYSTEM
    for word in T.ACTION_WORDS_12:  # 12 語は 1 つも落ちていない
        assert word in T.B0_SYSTEM_V2


def test_hint_arm_freezes_its_v2_hash():
    assert T.b0_sha256("hint", "v2") == B0_SHA256_HINT_V2
    assert "食事" in T.B0_SYSTEM_HINT_V2


def test_renderer_v2_changes_the_rendered_bytes():
    _, v1 = scene(vocab_version="v1")
    _, v2 = scene(vocab_version="v2")
    assert v1.blocks["B0"] != v2.blocks["B0"]
    assert v1.text != v2.text and v1.prompt_hash != v2.prompt_hash
    # B0 以外のブロックは 1 バイトも動かない(差は出力規約の 1 行だけ)
    for bid in ("B1", "B2", "B3", "B4", "B4b", "B5", "B6"):
        assert v1.blocks[bid] == v2.blocks[bid]


# ------------------------------------------------------- (c) 差は「行動:」の 1 行だけ
@pytest.mark.parametrize("mode", ["vocab", "hint"])
def test_only_the_action_line_differs_between_the_vocab_versions(mode):
    a = T.b0_system(mode, "v1").splitlines()
    b = T.b0_system(mode, "v2").splitlines()
    assert len(a) == len(b)
    diff = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    assert len(diff) == 1, [(a[i], b[i]) for i in diff]
    assert a[diff[0]].startswith("行動:") and b[diff[0]].startswith("行動:")


def test_open_arm_is_identical_across_vocab_versions():
    """open 腕は語彙を見せない=v1/v2 で B0 は**同一オブジェクト**(差は接地の側だけ)。"""
    assert T.b0_system("open", "v2") is T.b0_system("open", "v1")
    assert T.b0_sha256("open", "v2") == T.b0_sha256("open", "v1")


# ------------------------------------------------------- (d) 3 腕 × 2 版の全組み合わせ
@pytest.mark.parametrize("mode", list(T.INTENT_MODES))
@pytest.mark.parametrize("ver", list(T.VOCAB_VERSIONS))
def test_every_arm_and_version_combination_renders(mode, ver):
    body = T.b0_system(mode, ver)
    assert body.startswith("あなたは渋谷の街にいる一人の人物です。")
    assert "出力規約:" in body and "理由: <40字以内・1文>" in body
    assert "対象: <セルID / 物のカテゴリ / 人ID / なし>" in body
    _, rendered = scene(intent_mode=mode, vocab_version=ver)
    assert rendered.text and rendered.prompt_hash
    assert ("食事" in body) is (ver == "v2" and mode != "open")


def test_unknown_vocab_version_is_refused():
    with pytest.raises(ValueError):
        T.b0_system("vocab", "v3")
    with pytest.raises(ValueError):
        T.check_vocab_version("v0")
