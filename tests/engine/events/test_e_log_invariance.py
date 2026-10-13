"""第 1 期 1-3 出来事の記録: 記録の有無で結果が変わらない(口の約束 1-3 の約束 (1)・受入の試験 ``test_e_log_invariance``)。

- 合成の世界(data 無し): 記録 on/off で final・呼数・checkpoint の 3 本のハッシュ・日の締めの後の 2 本・状態のファイルの
  full-hash・manifest の既存の欄(日次の記録の ``events`` の欄を除く全部)が同じ。2 日のランも。
- 世界資産の 19 構成(data あり・``slow``=毎晩): byte-check の 19 構成(``wave2_bytecheck.configs()``)を 300 体で記録
  on/off に回し、final と呼数が同じ。5,000 体の 19 構成は byte-check の道具で回した(記録
  ``docs/bench/analysis/wallbounce-1012/e13/byte_check_e13.json``)。
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from shibuya.core.time_consts import STEPS_PER_DAY
from shibuya.engine.events import log as EV
from shibuya.engine.run import run_day

ROOT = Path(__file__).resolve().parents[3]
KW = dict(n_agents=80, seed=1, n_cells=9, ticks=720, budget=80.0, sleep_suppression=False, vocab_version="v3",
          memory="on", relations="on", rel_copresent="on", store_memory="on", checkpoint_every=60)
#: 環境の欄(git の commit・汚れ・env_id)・壁時計の欄・ランごとに違う印(run_id=実行の時刻とプロセス番号を混ぜる)と
#: 状態のファイルのバイト(見出しに run_id が入る=圧縮した大きさが揺れる)は比べない。ファイルの中身は full-hash で比べる。
SKIP_LEAVES = ("env_id", "environment", "wall", "seconds", "phase", "checkpoint_s", "run_id", "state_files")


def _run(flag: bool, fn=run_day, **kw):
    prev = EV.enabled()
    EV.set_enabled(flag)
    try:
        return fn(**kw)
    finally:
        EV.set_enabled(prev)


def _flat(x, path=""):
    if isinstance(x, dict):
        out = {}
        for k, v in x.items():
            out.update(_flat(v, f"{path}.{k}" if path else str(k)))
        return out
    if isinstance(x, list):
        out = {}
        for i, v in enumerate(x):
            out.update(_flat(v, f"{path}[{i}]"))
        return out
    return {path: x}


def _manifest_without_events(res):
    flat = _flat(res.run_manifest_fields())
    return {k: v for k, v in flat.items()
            if ".events." not in k and not k.endswith(".events") and not any(s in k for s in SKIP_LEAVES)}


def _same(a, b):
    assert a.final_hash == b.final_hash
    assert a.llm_calls == b.llm_calls
    assert [(c.tick, c.behavior_hash, c.full_hash) for c in a.checkpoints] == \
        [(c.tick, c.behavior_hash, c.full_hash) for c in b.checkpoints]
    assert a.state_hashes_end_of_day == b.state_hashes_end_of_day
    assert _manifest_without_events(a) == _manifest_without_events(b)


def test_on_and_off_give_the_same_results():
    on, off = _run(True, **KW), _run(False, **KW)
    _same(on, off)
    assert len(on.event_log) > 0 and len(off.event_log) == 0
    d_on, d_off = on.run_manifest_fields()["daily"][-1]["events"], off.run_manifest_fields()["daily"][-1]["events"]
    assert d_on["on"] is True and d_on["rows"] == len(on.event_log) and sum(d_on["by_what"].values()) == d_on["rows"]
    assert d_off == {"on": False, "rows": 0, "bytes": 0, "by_what": {}, "by_cause": {}, "live_rows": 0,
                     "live_bytes": 0, "evicted": 0}


def test_two_days_and_state_files_are_the_same(tmp_path):
    kw = dict(KW, ticks=STEPS_PER_DAY, sim_days=2, checkpoint_every=240)
    on = _run(True, state_out=tmp_path / "on", **kw)
    off = _run(False, state_out=tmp_path / "off", **kw)
    _same(on, off)
    fa = [(f["T"], f["full_hash"]) for f in on.resume["state_files"]]
    fb = [(f["T"], f["full_hash"]) for f in off.resume["state_files"]]
    assert fa == fb and len(fa) >= 2
    daily = on.run_manifest_fields()["daily"]
    assert [d["events"]["on"] for d in daily] == [True, True]
    assert sum(d["events"]["rows"] for d in daily) == on.event_log.n_appended


def _wave2():
    path = ROOT / "docs" / "bench" / "analysis" / "wave2-2026-09-30" / "wave2_bytecheck.py"
    spec = importlib.util.spec_from_file_location("wave2_bytecheck_e13", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["wave2_bytecheck_e13"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


@pytest.mark.slow
@pytest.mark.requires_data("world_v2:w17_schedule.parquet")
def test_nineteen_configs_on_and_off_give_the_same_final():
    from shibuya import cli

    cfgs = _wave2().configs()
    assert len(cfgs) == 19
    for name, kw in cfgs.items():
        on = _run(True, fn=cli.run, n_agents=300, seed=1, world_dir="data/world/v2", **kw)
        off = _run(False, fn=cli.run, n_agents=300, seed=1, world_dir="data/world/v2", **kw)
        assert (on.final_hash, on.llm_calls) == (off.final_hash, off.llm_calls), name
        assert len(on.event_log) > 0 and len(off.event_log) == 0, name
