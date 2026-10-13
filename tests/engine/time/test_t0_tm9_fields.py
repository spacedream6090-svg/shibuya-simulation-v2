"""第 1 期 1-1 時計 T0(TM9・GPU 無しの欄・10f と一体): manifest と日次の記録に「判断モデルと LLM を分けた呼び出し数」
「時計の種類と幅」「つなぎの台帳の数」を足した。欄が増えるだけ(既存の欄の名・順・値は変えない)。

- manifest の一番上の鍵(順も)は ``manifest_keys_frozen.json`` と同じ(``writes_soa_frozen.json`` と同じ凍結の方式。
  欄を足したら理由を記録に書いて更新する)。TM9 の 4 つは T0 の時点の末尾(1-4 でその後ろに ``rules_version``・
  ``run_kind``・``bridges_version`` を足した=TM9 の 4 つは続きの並びのまま)。
- 判断モデルはまだ無い=0。LLM は発射数(``llm_calls_total`` と同じ)。日次の LLM はこのランの中で数えた分の日ごとの差。
- つなぎの台帳は 1-4 で入った=件数(T0 では ``None``。1-4 の試験は ``tests/engine/bridging/``)。
- TM9 の欄は状態に入らない(final・behavior-hash は manifest を読まない)ことは byte-check 19 構成で HEAD と同じ final を
  確かめた(記録 ``docs/bench/analysis/wallbounce-1012/t0/``)。ここでは「欄の値を変えても final が同じ」を見る。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from shibuya.core import time_consts as TC
from shibuya.engine import manifest_sections as MS
from shibuya.engine.bridging import ledger as BR
from shibuya.engine.run import run_day

FROZEN = Path(__file__).with_name("manifest_keys_frozen.json")
TM9 = ("calls_by_model", "clock_kind", "step_seconds", "bridges_count")


def _run(**kw):
    base = dict(n_agents=200, seed=2, ticks=1440, sim_days=2, checkpoint_every=720, n_cells=25, processes=False,
                conversations=True, renderer="stub")
    base.update(kw)
    return run_day(**base)


@pytest.fixture(scope="module")
def two_days():
    return _run()


def test_manifest_keys_match_the_frozen_list(two_days):
    keys = list(two_days.run_manifest_fields())
    frozen = json.loads(FROZEN.read_text(encoding="utf-8"))["keys"]
    assert keys == frozen
    i = keys.index(TM9[0])
    assert keys[i:i + len(TM9)] == list(TM9)  # 列追加のみ(T0 の末尾=続きの並び。1-4 の欄はその後ろ)
    # 1-4 の 3 欄の後ろに 1-9 の economy(金の生ログの輪と transfer の計器)・その後ろに 1-2 の percept(知覚の事実の
    # 計器)=列追加のみ(末尾)
    assert keys[i + len(TM9):] == ["rules_version", "run_kind", "bridges_version", "economy", "percept"]


def test_manifest_tm9_values(two_days):
    m = two_days.run_manifest_fields()
    assert m["llm_calls_total"] > 0
    assert m["calls_by_model"] == {"judge_model": 0, "llm": m["llm_calls_total"]}
    assert m["clock_kind"] == TC.CLOCK_KIND == "steps"
    assert m["step_seconds"] == m["tick_seconds"] == TC.STEP_SECONDS
    assert m["bridges_count"] == BR.default_ledger().count() > 0  # 1-4 で null から件数に


def test_sections_of_tm9_fields():
    assert MS.section_of("clock_kind") == MS.section_of("step_seconds") == MS.section_of("bridges_count") == MS.CONFIG
    assert MS.section_of("calls_by_model") == MS.section_of("calls_by_model.llm") == MS.OBSERVED


def test_daily_records_have_tm9_and_the_days_add_up(two_days):
    m = two_days.run_manifest_fields()
    daily = m["daily"]
    assert [d["day"] for d in daily] == [0, 1]
    for d in daily:
        assert d["clock_kind"] == "steps" and d["step_seconds"] == 60
        assert d["bridges_count"] == BR.default_ledger().count()  # 1-4 で null から件数に
        assert d["calls_by_model"]["judge_model"] == 0 and d["calls_by_model"]["llm"] >= 0
    assert sum(d["calls_by_model"]["llm"] for d in daily) == m["llm_calls_total"]
    assert all(d["calls_by_model"]["llm"] > 0 for d in daily)


def test_daily_llm_calls_match_the_per_step_diagnostics(two_days):
    """日次の LLM の数=診断の行の ``calls`` の日ごとの和(別の数え方と突き合わせる)。"""
    import numpy as np

    c = two_days.column("calls").astype(np.int64)
    per_day = [int(c[: TC.STEPS_PER_DAY].sum()), int(c[TC.STEPS_PER_DAY:].sum())]
    assert per_day == [d["calls_by_model"]["llm"] for d in two_days.run_manifest_fields()["daily"]]


def test_resume_mid_day_counts_only_this_run(tmp_path, two_days):
    """再開したランの日次の LLM は再開した時刻からの分。止めたランの残り+再開したランの分=通しの 2 日目。"""
    st = tmp_path / "st"
    stop = TC.STEPS_PER_DAY + 300
    a = _run(stop_at_tick=stop, state_out=str(st))
    pkl = sorted(st.glob("state-T*.npz"))[-1]
    b = _run(resume_from=str(pkl))
    da, db = a.run_manifest_fields()["daily"], b.run_manifest_fields()["daily"]
    straight = two_days.run_manifest_fields()["daily"]
    assert [d["day"] for d in da] == [0] and [d["day"] for d in db] == [1]
    assert da[0]["calls_by_model"] == straight[0]["calls_by_model"]
    assert db[0]["calls_by_model"]["llm"] == b.llm_calls
    assert (a.llm_calls - da[0]["calls_by_model"]["llm"]) + db[0]["calls_by_model"]["llm"] == \
        straight[1]["calls_by_model"]["llm"]
    assert b.final_hash == two_days.final_hash


def test_tm9_fields_do_not_feed_the_final_hash(monkeypatch):
    """欄の値(時計の種類)を変えても final と呼数は同じ(TM9 の欄は記録だけ)。"""
    from shibuya.engine import run as RUN
    from shibuya.engine.systems import state_io as SIO

    base = _run(sim_days=1, ticks=300, checkpoint_every=100)
    monkeypatch.setattr(RUN, "CLOCK_KIND", "other")
    monkeypatch.setattr(SIO, "CLOCK_KIND", "other")
    moved = _run(sim_days=1, ticks=300, checkpoint_every=100)
    assert moved.run_manifest_fields()["clock_kind"] == "other"
    assert (moved.final_hash, moved.llm_calls) == (base.final_hash, base.llm_calls)
