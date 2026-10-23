"""第 6 期 6-5 記憶 M2: 手がかり(既定=その場の手がかり=ID の一致・腕 ``--memory-cue embed``=意味の手がかり)。

- 既定(id): 意味の手がかりの状態を作らない・埋め込みを計算しない(埋め込みの口を落とす口に替えても既定のランは通る)。
  ID の一致の想起が M0 と同じことは 1-6 の同値の試験(``test_m0_recall_equivalence.py``)が見る。
- 腕 embed(試験用の代わり ``ngram-test``=文字の n-gram・意味ではない=経路の試験): 小さな合成で、手がかりの文に近い要旨の
  行が上に来る・一致は cos ≥ COS_MATCH・手がかりの文が無ければ一致 0・要旨を落とすと埋め込みも落ちる。
- 手がかりの文の選び(MR2 問い 4): 会話中=相手の直前の発言・ほか=本人の直前の理由。
- Ruri-v3(30m/130m): 版の固定(commit・重みの sha256・大きさ・Apache-2.0)・重みが置き場に無ければ ``EmbedUnavailable``
  (本段では取得していない=転送先が許可の一覧の外)。重みがあるときだけ「近い文が上に来る」を Ruri で見る(skip)。
- 合成の世界のラン(腕 embed・ngram-test): 通る・計器が出る・決定的(2 回で同じ final とテープの列)。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from shibuya.core.time_consts import NS_PER_SECOND
from shibuya.engine import memory_embed as ME
from shibuya.engine.memory_store import Cue, LegacyEvent, MemoryStore
from shibuya.engine.run import run_day
from shibuya.engine.tape import Tape

from tests.engine.memory._mr65 import KW, arms, mr65

S = NS_PER_SECOND
ROOT = Path(__file__).resolve().parents[3]


def _store(rows: int = 8) -> MemoryStore:
    ms = MemoryStore(2, rows, step_seconds=60, minutes_per_step=1.0)
    ms.enable_arms(cue=ME.CueState(ME.NgramEmbedder()))
    return ms


def test_ngram_embedder_is_deterministic_and_normalized():
    e = ME.NgramEmbedder()
    a = e.encode(["駅前のカフェでコーヒー", "公園で散歩"], query=False)
    b = e.encode(["駅前のカフェでコーヒー", "公園で散歩"], query=False)
    assert a.dtype == np.float32 and a.shape == (2, 256) and np.array_equal(a, b)
    assert np.allclose(np.linalg.norm(a, axis=1), 1.0, atol=1e-6)


def test_close_gist_ranks_first_with_the_semantic_cue():
    ms = _store()
    texts = ["公園で犬の散歩をした", "駅前のカフェでコーヒーを飲んだ", "書店で雑誌を買った"]
    for j, t in enumerate(texts):  # 3 件の会話の要旨(種類 7=会話・相手 j+1)
        ms.remember(0, LegacyEvent(600 * S, 7, j + 1, -1, 0, 1), 2, "legacy", annotation=[t])
    assert len(ms.cue._vec) == 3
    v = ms.recall(0, 660 * S, 3, cue=Cue(), cue_text="カフェでコーヒーを飲む")
    assert v and v[0].annotation == texts[1]
    # 一致は cos ≥ COS_MATCH(ID の手がかりは使わない=意味の手がかりだけの腕)
    assert ms.last_recall.rows_candidate == 1
    # 手がかりの文が無ければ一致 0(score の順の補いだけ)
    ms.recall(0, 660 * S, 3, cue=Cue(partner=1), cue_text=None)
    assert ms.last_recall.rows_candidate == 0
    s = ms.cue.summary()["counts"]
    assert s["recalls_with_cue"] == 1 and s["recalls_without_cue"] == 1


def test_dropping_a_note_drops_its_vector():
    ms = _store(rows=2)
    ms.remember(0, LegacyEvent(60 * S, 7, 1, -1, 0, 1), 2, "legacy", annotation=["一つ目"])
    ms.remember(0, LegacyEvent(120 * S, 7, 2, -1, 0, 1), 2, "legacy", annotation=["二つ目"])
    assert len(ms.cue._vec) == 2
    ms.remember(0, LegacyEvent(180 * S, 7, 3, -1, 0, 1), 2, "legacy", annotation=["三つ目"])  # 追い出し
    assert len(ms.cue._vec) == 2 and set(ms._ms_note) == set(ms.cue._vec)


def test_cue_text_choice_in_and_out_of_conversation():
    c = ME.CueState(ME.NgramEmbedder())
    c.note_own(1, "昼ご飯を食べたい")
    c.note_heard([1], "新しい店ができたよ")
    assert c.text_for(1, True) == "新しい店ができたよ"
    assert c.text_for(1, False) == "昼ご飯を食べたい"
    assert c.text_for(2, True) is None
    c.note_own(2, "なし")
    assert c.text_for(2, False) is None


def test_ruri_pins_and_missing_weights():
    for name, pin in ME.RURI_PINS.items():
        assert pin.repo == f"cl-nagoya/{name}" and len(pin.revision) == 40 and len(pin.safetensors_sha256) == 64
        assert pin.license == "apache-2.0" and pin.dim in (256, 512)
    with pytest.raises(ME.EmbedUnavailable, match="取得していない"):
        ME.make_embedder("ruri-v3-30m", root=ROOT / "_no_such_models_dir")
    with pytest.raises(ValueError):
        ME.RuriEmbedder("ruri-v3-1b")
    assert isinstance(ME.make_embedder("ngram-test"), ME.NgramEmbedder)


@pytest.mark.skipif(not any((ROOT / ME.MODEL_ROOT / f"{n}@{p.revision}" / "model.safetensors").exists()
                            for n, p in ME.RURI_PINS.items()), reason="Ruri の重みが置き場に無い(本段では未取得)")
def test_ruri_close_sentence_ranks_first():  # pragma: no cover - 重みがあるときだけ
    for name, pin in ME.RURI_PINS.items():
        if not (ROOT / ME.MODEL_ROOT / f"{name}@{pin.revision}" / "model.safetensors").exists():
            continue
        e = ME.make_embedder(name, root=ROOT / ME.MODEL_ROOT)
        docs = e.encode(["公園で犬の散歩をした", "駅前の喫茶店でコーヒーを飲んだ", "書店で雑誌を買った"], query=False)
        q = e.encode(["カフェで珈琲"], query=True)[0]
        assert int(np.argmax(docs @ q)) == 1


def test_default_cue_computes_no_embedding(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("既定の腕で埋め込みを計算した")

    monkeypatch.setattr(ME.NgramEmbedder, "encode", boom)
    with arms("events"):
        r = run_day(**KW)
    assert "mr65" not in r.run_manifest_fields()["memory_summary"]["memory_store"]


def test_embed_arm_run_is_deterministic(tmp_path):
    with arms("events", cue="embed", embed_model="ngram-test"):
        a = run_day(tape_path=tmp_path / "a", **KW)
        b = run_day(tape_path=tmp_path / "b", **KW)
    assert a.final_hash == b.final_hash
    ta, tb = Tape(tmp_path / "a"), Tape(tmp_path / "b")
    for col in ("recalled_rows", "b5_text"):
        assert list(ta.column(col)) == list(tb.column(col))
    m = mr65(a)
    assert m["arms"]["cue"] == "embed" and m["cue"]["model"] == "ngram-test"
    assert m["cue"]["counts"]["recalls_with_cue"] + m["cue"]["counts"]["recalls_without_cue"] > 0
