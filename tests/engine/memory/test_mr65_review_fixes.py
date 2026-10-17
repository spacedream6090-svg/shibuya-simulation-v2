"""第 6 期 6-5 の独立検収(mr65/review.md)の直しの試験(L1・L3・L4・M3・L7・CueState の守り)。

- L1: 腕の名と埋め込みのモデルの名と版は manifest の設定の節(``memory_summary.mr65_arms``)と設定の指紋(``memory_mr65``)に
  入る(既定の腕のランには出ない=負の対照)。再開で埋め込みのモデルの取り違えと腕の取り違えを止める(負の対照=同じ腕なら
  再開できて通しと同じ)。
- L3: 人も記憶の腕の関係の読み口は、相手だけ要る読み口で強さを計算しない・A だけ要る読み口で見覚えの強さを計算しない
  (結果は前の作り=両方計算と同じ)。
- L4: ``memory_m1.PARAMS`` の中の表も読み取り専用・manifest の写しは普通の dict(書き換えても表は変わらない)。
- M3: 状態台帳の行 M0 の注(腕 m1・memory では器の行が挙動を決める=既定化で軸を改める)・軸は前のまま。
- L7: つなぎの台帳の本段の行の段の名は回答 10-12 の 6-2 の表の名(M4=個人差・M5=同席と浅い痕跡)。
- ``CueState`` の守り(付け替え・消去・新しい欄)。
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from shibuya.core.time_consts import NS_PER_SECOND
from shibuya.engine import memory_m1 as M1
from shibuya.engine import state_ledger as SL
from shibuya.engine.memory_store import LegacyEvent, MemoryStore
from shibuya.engine.run import run_day

from tests.engine.memory._mr65 import KW, arms

S = NS_PER_SECOND
ROOT = Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------- L1
def _head(d: Path) -> dict:
    return json.loads(next(d.glob("state-T*.json")).read_text(encoding="utf-8"))


def test_arms_enter_the_config_section_and_the_fingerprint(tmp_path):
    from shibuya.engine import manifest_sections as MSEC

    kw = dict(KW, ticks=240)
    with arms("events", model="m1", cue="embed", embed_model="ngram-test"):
        a = run_day(state_out=tmp_path / "a", stop_at_tick=120, **kw)
    man = a.run_manifest_fields()
    cfg = man["memory_summary"]["mr65_arms"]
    assert cfg == {"model": "m1", "cue": "embed", "people": "table", "grain": "each", "embed_model": "ngram-test",
                   "embed_identity": "ngram-test:crc32-char-1..3gram/256"}
    assert MSEC.section_of("memory_summary.mr65_arms.embed_identity") == MSEC.CONFIG
    assert MSEC.unlisted_in_mixed(man) == []
    assert _head(tmp_path / "a")["fingerprint"][M1.FP_KEY] == cfg
    # 人も記憶の腕は行の上限も入る
    assert M1.config_of(M1.MemoryArms("m1", "id", "memory", "ruri-v3-30m", "each"),
                        row_caps={"episode": 256, "person": 256, "shop": 256})["row_caps"]["shop"] == 256
    # Ruri は重みの sha256 で同定する(版の固定)
    ruri = M1.config_of(M1.MemoryArms("m0", "embed", "table", "ruri-v3-130m", "each"))
    assert ruri["embed_identity"].startswith("cl-nagoya/ruri-v3-130m@e3114c6e") and "sha256=1c342581" in ruri["embed_identity"]
    # 負の対照: 既定の腕(器だけ)は欄も指紋の鍵も無い
    with arms("events"):
        b = run_day(state_out=tmp_path / "b", stop_at_tick=120, **kw)
    assert "mr65_arms" not in b.run_manifest_fields()["memory_summary"]
    assert M1.FP_KEY not in _head(tmp_path / "b")["fingerprint"]
    assert M1.config_of(M1.arms()) == {}


def test_resume_refuses_another_embed_model_or_another_arm(tmp_path):
    kw = dict(KW, ticks=240)
    with arms("events", cue="embed", embed_model="ngram-test"):
        a = run_day(state_out=tmp_path / "a", stop_at_tick=120, **kw)
    f = tmp_path / "a" / a.resume["state_files"][-1]["file"]
    # 埋め込みのモデルの取り違え(行 M0C の _vec は hash_skip=前は今のモデルで作り直して黙って通った)=指紋で止める
    with arms("events", cue="embed", embed_model="ruri-v3-30m"):
        with pytest.raises(ValueError, match="再開の設定が親と違う"):
            run_day(resume_from=f, **kw)
    with arms("events", model="m1", cue="embed", embed_model="ngram-test"):
        with pytest.raises(ValueError, match="再開の設定が親と違う"):
            run_day(resume_from=f, **kw)
    with arms("events"):
        with pytest.raises(ValueError, match="再開の設定が親と違う"):
            run_day(resume_from=f, **kw)
    # 負の対照: 同じ腕は再開できる=通しと同じ final
    with arms("events", cue="embed", embed_model="ngram-test"):
        straight = run_day(**kw)
        b = run_day(resume_from=f, **kw)
    assert b.final_hash == straight.final_hash


# ---------------------------------------------------------------- L3
def _people_store() -> MemoryStore:
    import shibuya.engine.memory_store as MS

    ms = MS.MemoryStore(4, 4, step_seconds=60, minutes_per_step=1.0)
    ms.enable_arms(m1=M1.M1State(4, 16, tau=M1.tau_from_m0(-2.0), seed=1), uncapped=True)
    for a, p, t in ((0, 1, 60), (0, 2, 120), (0, 1, 180), (1, 0, 60), (2, 3, 600)):
        ms.remember(a, LegacyEvent(t * S, M1.PERSON_KIND, p, 5, 0, 1), 0, "legacy")
    return ms


def test_people_readers_compute_each_strength_once(monkeypatch):
    from shibuya.engine.relations_people import PeopleRelationLayer

    ms = _people_store()
    layer = PeopleRelationLayer(4, 50, store=ms)
    ids = np.arange(4)
    full = ms.people_rows(ids, 900 * ms.ns_per_step)  # 前の作り=両方計算(刻み 900 の時刻)
    calls = {"A": 0, "fam": 0}
    orig = M1.M1State.strength

    def count(self, *a, familiar=False, **k):
        calls["fam" if familiar else "A"] += 1
        return orig(self, *a, familiar=familiar, **k)

    monkeypatch.setattr(M1.M1State, "strength", count)
    p = layer._partner_rows(None, ids)
    assert calls == {"A": 0, "fam": 0}  # 相手だけ=強さを計算しない
    A = layer.activation(None, ids, 900)
    assert calls == {"A": 1, "fam": 0}  # A だけ(前は見覚えの A も計算した)
    np.testing.assert_array_equal(p, full[0])
    np.testing.assert_array_equal(A, full[2])
    e = layer.edges(None, 0, 900)
    assert calls["fam"] == 0 and sorted(e.partner.tolist()) == sorted(full[0][0][full[2][0] >= ms.m1.tau].tolist())
    rec = layer.recognized(None, 0, [1, 2, 3], 900)
    assert calls["fam"] == 1 and rec.tolist()[:2] == [True, True] and not rec[2]


# ---------------------------------------------------------------- L4
def test_params_tables_are_read_only_and_the_summary_is_a_plain_copy():
    with pytest.raises(TypeError):
        M1.PARAMS["kinds"]["episode"]["d"] = 0.9  # type: ignore[index]
    with pytest.raises(TypeError):
        M1.PARAMS["kinds"]["new"] = {}  # type: ignore[index]
    st = M1.M1State(2, 4, tau=-3.0, seed=1)
    got = st.summary(np.zeros(4, dtype=bool))["params"]
    json.dumps(got)  # manifest に出せる(普通の dict)
    got["kinds"]["episode"]["d"] = 0.9
    assert M1.PARAMS["kinds"]["episode"]["d"] == M1.D_ACTR


# ---------------------------------------------------------------- CueState の守り(検収 低)
def test_cue_state_guards():
    from shibuya.engine.memory_embed import CueState, NgramEmbedder

    cs = CueState(NgramEmbedder())
    for name, val in (("_heard", {}), ("_own", {}), ("_vec", {}), ("_qcache", {}), ("embedder", NgramEmbedder()),
                      ("model", "ruri-v3-30m"), ("dim", 512)):
        with pytest.raises(AttributeError):
            setattr(cs, name, val)
    for name in ("_vec", "_heard", "embedder"):
        with pytest.raises(AttributeError):
            delattr(cs, name)
    with pytest.raises(AttributeError):
        cs.extra = 1  # type: ignore[attr-defined]
    # 負の対照: 書く口(器の中から呼ぶ)は通る
    cs.note_own(0, "理由")
    cs.embed_rows([3], ["要旨"])
    assert cs.text_for(0, False) == "理由" and 3 in cs._vec


# ---------------------------------------------------------------- M3
def test_ledger_m0_note_declares_the_arm_runs_and_keeps_the_axes():
    r = SL.row("M0")
    assert (r.behavior, r.restore) == (SL.NO, SL.DERIVABLE) and set(r.hash_skip) == set(r.items)
    assert "検収 M3" in r.note and "--memory-model m1" in r.note and "--memory-people memory" in r.note
    assert "既定化" in r.note and "behavior-hash に入れる" in r.note
    s = SL.row("M0S")
    assert (s.behavior, s.restore, s.arm) == (SL.BEHAVIOR, SL.REQUIRED, "memory-people")


# ---------------------------------------------------------------- L7
def test_bridge_ids_use_the_stage_names_of_answer_6_2():
    doc = json.loads((ROOT / "docs" / "design" / "bridging-ledger.json").read_text(encoding="utf-8"))
    ids = [r["id"] for r in doc["bridges"] if str(r["id"]).startswith("DOC-mr65-")]
    assert len(ids) == len(set(ids)) == 17
    by_stage: dict[str, set[str]] = {}
    for i in ids:
        tag = i.split("-")[2]
        by_stage.setdefault(tag if tag in ("m1", "m2", "m3", "m4", "m5") else "-", set()).add(i)
    # 6-2 の表: M4=個人差(忘れる速さの 15%)・M5=同席と浅い痕跡
    assert by_stage["m4"] == {"DOC-mr65-m4-rate-variation"}
    assert by_stage["m5"] == {"DOC-mr65-m5-trace-window"}
    assert {"DOC-mr65-m1-recognition", "DOC-mr65-m1-people-initial", "DOC-mr65-m1-people-limits",
            "DOC-mr65-m1-row-caps", "DOC-mr65-m1-shop-uncapped"} <= by_stage["m1"]
    rows = {r["id"]: r for r in doc["bridges"]}
    # 発注の名(M4=思い浮かぶ/見覚え・M5=人も記憶)は why に書く
    assert "発注の M4" in rows["DOC-mr65-m1-recognition"]["why"]
    assert "発注の M5" in rows["DOC-mr65-m1-people-initial"]["why"]
    seed_row = rows["DOC-mr65-m4-rate-variation"]
    assert "母集団の seed" in seed_row["what"] and "src/shibuya/engine/systems/build.py" in seed_row["code_at"]
    assert "src/shibuya/cli.py" not in seed_row["code_at"]
