"""AB7-OPEN-INTENT(自由意図の腕)の切替口 — 描画側(``docs/design/v2-open-intent-arm-spec.md``)。

見るもの(仕様書 §4 の受入 (a)(b))
(a) ``intent_mode="open"`` で ``OUTPUT_SPEC_OPEN`` が選ばれ **B0 の SHA が変わる**
    (=切替が効く)。レンダラの描画バイト・``prompt_hash`` も動く/
(b) **既定は 1 バイトも動かない**: ``b0_sha256("vocab")`` が現行値・``template_sha256()`` が
    161fe181…・参照場面の ``prompt_hash`` が bb23f7c6…(⑥ の golden と同じ場面)/
(c) 腕の差は **``行動:`` の 1 行だけ**(理由・対象・ひと言・2 行形・JSON 禁止は同文)。

**mock では行動は変わらない**(MockLLM はプロンプト本文を読まない=C6 実測)。この腕で
動くのは描画バイトだけで、行動差は実 LLM でしか出ない。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.agents.state import AgentKind, AgentState
from shibuya.perception import templates as T
from shibuya.perception.renderer import Renderer
from shibuya.world.state import World

#: 凍結テンプレの SHA(``tests/perception/test_templates.py`` と**同じ値**)。
FROZEN_TEMPLATE_SHA256 = "161fe181bc325f003d874fb5c91e6142c01449fb09ac5f8b377b715a945608de"
#: 既定(vocab)の B0 本文そのものの SHA。**腕の切替が効いたかの指紋**。
B0_SHA256_VOCAB = "2b4bfc8a6da16ec73cbd3db8c68656150d2becd08100efa8816ad649e478339c"
#: 参照場面の指紋(``test_ablation6_signage.GOLDEN_FIXED_PROMPT_HASH`` と**同じ場面・同じ値**)。
GOLDEN_FIXED_PROMPT_HASH = "bb23f7c69a82460b6820292404eb640b722ed0c7aa7a545afc9e09c697d8a5c5"


def scene(*, intent_mode: str = T.DEFAULT_INTENT_MODE, n: int = 12, n_cells: int = 9):
    """``test_ablation6_signage.scene`` と同じ合成場面(乱数の引き方まで同じ)。"""
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
    r = Renderer(w, a, seed=13, intent_mode=intent_mode)
    r.prepare_tick(750)
    return r, r.render(0, tick=750, wake_reason=3)


# ------------------------------------------------------- (a) 切替が効く(B0 の SHA が動く)
def test_open_mode_changes_the_b0_sha256():
    """``b0_system("open")`` は別の本文=別の SHA(=腕が空振りしていない)。"""
    assert T.b0_system("open") == T.B0_SYSTEM_OPEN
    assert T.b0_system("open") != T.b0_system("vocab")
    assert T.b0_sha256("open") != T.b0_sha256("vocab")
    assert T.b0_sha256("open") != B0_SHA256_VOCAB


def test_renderer_open_mode_changes_the_rendered_bytes():
    """レンダラ経由でも切替が効く(B0 ブロックと prompt_hash が動く)。"""
    _, vocab = scene(intent_mode="vocab")
    _, open_ = scene(intent_mode="open")
    assert vocab.blocks["B0"] != open_.blocks["B0"]
    assert vocab.text != open_.text
    assert vocab.prompt_hash != open_.prompt_hash


def test_only_the_action_line_differs_between_the_arms():
    """腕の差は ``行動:`` の 1 行だけ(理由・対象・ひと言・2 行形・JSON 禁止は同文)。"""
    a = T.B0_SYSTEM.splitlines()
    b = T.B0_SYSTEM_OPEN.splitlines()
    assert len(a) == len(b)
    diff = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    assert len(diff) == 1, [(a[i], b[i]) for i in diff]
    assert a[diff[0]].startswith("行動:") and b[diff[0]].startswith("行動:")
    assert "10字以内の動詞句" in b[diff[0]]
    for w in T.ACTION_WORDS_12:
        assert w not in b[diff[0]], f"open 腕の行動行に語彙 {w} が漏れている"


def test_open_mode_hides_the_whitelist_but_keeps_the_target_field():
    """語彙は見せない/**対象欄の制約は残す**(効果を閉じるのはエンジンの仕事・仕様書 §2)。"""
    assert " / ".join(T.ACTION_WORDS_12) in T.OUTPUT_SPEC
    assert " / ".join(T.ACTION_WORDS_12) not in T.OUTPUT_SPEC_OPEN
    # ``行動:`` 断片の後ろ(対象・ひと言)は**同じ 1 本の行の末尾**=逐語で一致する。
    tail_vocab = T.OUTPUT_SPEC[T.OUTPUT_SPEC.index("対象:"):]
    tail_open = T.OUTPUT_SPEC_OPEN[T.OUTPUT_SPEC_OPEN.index("対象:"):]
    assert tail_vocab.startswith("対象: <セルID") and tail_vocab == tail_open
    # ``行動:`` より前(出力規約の頭 3 行)も逐語で一致する。
    assert T.OUTPUT_SPEC.split("行動:")[0] == T.OUTPUT_SPEC_OPEN.split("行動:")[0]


# ------------------------------------------------------- (b) 既定は 1 バイトも動かない
def test_default_intent_mode_is_vocab():
    assert T.DEFAULT_INTENT_MODE == "vocab" == T.INTENT_MODES[0]
    assert T.INTENT_MODES == ("vocab", "open")


def test_default_path_keeps_the_frozen_hashes():
    """既定の B0 は ``TEMPLATES["B0.system"]`` と**同一オブジェクト**=凍結 SHA は動かない。"""
    assert T.b0_system() is T.TEMPLATES["B0.system"]
    assert T.b0_system("vocab") is T.TEMPLATES["B0.system"]
    assert T.b0_sha256("vocab") == B0_SHA256_VOCAB
    assert T.b0_sha256() == B0_SHA256_VOCAB
    assert T.template_sha256() == FROZEN_TEMPLATE_SHA256


def test_default_renderer_bytes_do_not_move():
    """参照場面の描画バイト(⑥ の golden と同じ場面)は AB7 の導入で動かない。"""
    r, out = scene()
    assert r.intent_mode == "vocab"
    assert Renderer(r.world, r.agents).intent_mode == "vocab"
    assert out.prompt_hash == GOLDEN_FIXED_PROMPT_HASH


# ------------------------------------------------------- 入口の検査
@pytest.mark.parametrize("bad", ["", "OPEN", "free", "vocab ", None, 0])
def test_unknown_intent_mode_is_refused(bad):
    with pytest.raises(ValueError):
        T.check_intent_mode(bad)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        scene(intent_mode=bad)  # type: ignore[arg-type]
