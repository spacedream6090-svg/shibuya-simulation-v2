"""第 1 期 1-5(口の約束 1-5 の約束 (1)): 権限で止める検査が今の既定で当たった回数を 19 構成で数える。

数えるもの(関数を包んで数えるだけ=結果は変えない): 開閉店の口 ``resolve.request_open_close`` の権利の無い行
(HEAD では ``NO_PERMISSION`` を書いて止めていた行)・判断の応答が役割語だった回数(HEAD では「権限検査待ち」で待機に
落としていた)・群・規範の計器の ``no_permission``・1-5 の記録の ``行為:許可のない行動`` の行と manifest の
``rights.unauthorized``。

- 生きた数え: byte-check と同じ 19 構成(``wave2_bytecheck.configs()``)を小さく回す(mock/古典・200 体・seed 1・1 日)。
  18 構成は ``slow``(約 70 秒)・既定 v3 の 1 構成は軽い版として ``slow`` の外(検収 L9)。
- 記録の数え: 道具 ``r15/tools/count_no_permission.py`` が 5,000 体で数えた表(``r15/no_permission_r15.json``)。

**0 でなければ落とさず ▲ の印を出す**(口の約束 1-5〔決定〕: ▲ として第 2 期へ・縮める部分は腕。警告
``NoPermissionHit`` を出して記録に書く)。0 なら ◎(縮めた範囲は記録 r15/README.md §4)。
"""

from __future__ import annotations

import importlib.util
import json
import sys
import warnings
from collections import Counter
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[3]
WAVE2 = ROOT / "docs" / "bench" / "analysis" / "wave2-2026-09-30" / "wave2_bytecheck.py"
RECORD = ROOT / "docs" / "bench" / "analysis" / "wallbounce-1012" / "r15" / "no_permission_r15.json"
WHAT = "行為:許可のない行動"


class NoPermissionHit(UserWarning):
    """▲ の印: 今の既定で権限の検査が当たった(縮めると結果が動く=第 2 期へ)。"""


def _configs() -> dict:
    spec = importlib.util.spec_from_file_location("wave2_bytecheck_r15", WAVE2)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["wave2_bytecheck_r15"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod.configs()


CONFIGS = _configs()
#: ``slow`` の外に残す 1 構成(既定 v3)。
LIGHT = "w6_v3_default"


def test_the_nineteen_configs():
    assert len(CONFIGS) == 19


def _mark(name: str, hits: dict[str, int]) -> None:
    if any(hits.values()):
        warnings.warn(f"▲ {name}: 権限の検査が当たった {hits}(縮める部分は腕に=記録へ)", NoPermissionHit)


@pytest.mark.requires_data("world_v2")
@pytest.mark.parametrize("name", [
    pytest.param(n, marks=() if n == LIGHT else pytest.mark.slow) for n in CONFIGS])
def test_live_count_is_zero_or_marked(name, monkeypatch):
    """19 構成の生きた数え(約 70 秒=``slow``・検収 L9)。既定 v3 の 1 構成だけは ``slow`` の外(軽い版)。"""
    from shibuya import cli
    from shibuya.engine import llm_bridge as LB
    from shibuya.engine import resolve as R

    cnt: Counter[str] = Counter()
    orig_roc, orig_call = R.request_open_close, LB.LLMBridge.call

    def roc(agents, world, agent_ids, poi_ids, want_open, tick, *a, **kw):  # noqa: ANN001
        perm = kw.get("permitted")
        ids = np.asarray(agent_ids).ravel()
        ok = np.zeros(ids.size, dtype=bool) if perm is None else np.asarray(perm, dtype=bool).ravel()
        cnt["open_close_rows"] += int(ids.size)
        cnt["open_close_not_permitted"] += int((~ok).sum())
        return orig_roc(agents, world, agent_ids, poi_ids, want_open, tick, *a, **kw)

    def call(self, *a, **kw):  # noqa: ANN001
        res = orig_call(self, *a, **kw)
        cnt["bridge_calls"] += 1
        cnt["role_actions"] += int(bool(res.role_action))
        return res

    monkeypatch.setattr(R, "request_open_close", roc)
    monkeypatch.setattr(LB.LLMBridge, "call", call)
    res = cli.run(n_agents=200, seed=1, world_dir="data/world/v2", **CONFIGS[name])
    man = res.run_manifest_fields()
    rw = man["group_norms"]["role_words"]
    hits = {"open_close_not_permitted": cnt["open_close_not_permitted"], "role_actions": cnt["role_actions"],
            "norm_meter_no_permission": int(rw["no_permission"]),
            "events_unauthorized": int(res.event_log.what_counts().get(WHAT, 0)),
            "manifest_open_close": int(man["rights"]["unauthorized"]["open_close"]),
            "manifest_role_unauthorized": int(man["rights"]["unauthorized"]["role_action_unauthorized"])}
    _mark(name, hits)
    # 数えた所が生きている: 開閉の過程は回った(200 体では担当が現場に居る回が少なく、開閉の口を通らない構成がある=
    # 口を通った行は 5,000 体の記録の表で見る)・判断の口は呼ばれた
    assert res.runner.opening.n_events > 0 and cnt["bridge_calls"] > 0
    assert hits["events_unauthorized"] == hits["manifest_open_close"]  # 記録と manifest の数が合う


def test_recorded_count_on_five_thousand_bodies():
    """道具で数えた 5,000 体の表(HEAD の側=止める検査・作業木の側=記録に替えた後)。0 でなければ ▲ の印。"""
    doc = json.loads(RECORD.read_text(encoding="utf-8"))
    assert set(doc["rows"]) == set(CONFIGS) and doc["agents"] == 5_000 and doc["seed"] == 1
    tot = doc["totals"]
    for name, row in doc["rows"].items():
        assert "error_a" not in row and "error_b" not in row, name
        assert row["final_same"] is True, name  # 数えた 2 つの側の final が同じ(記録に替えても結果は不変)
        assert row["head_open_close_rows"] > 0, name  # 5,000 体では開閉の口を通っている(数えた所が生きている)
        _mark(name, {k: int(row[k] or 0) for k in ("head_open_close_not_permitted_rows", "head_bridge_role_actions",
                                                     "head_norm_meter_no_permission", "r15_events_unauthorized")})
    assert set(tot) >= {"head_open_close_not_permitted_rows", "head_bridge_role_actions",
                        "head_norm_meter_no_permission", "r15_events_unauthorized"}


def test_negative_a_hit_is_marked_but_not_failed():
    """▲ の印の負の対照: 当たりが 1 つでもあれば警告(落とさない)・0 なら何も出ない。"""
    with pytest.warns(NoPermissionHit, match="▲ x"):
        _mark("x", {"open_close_not_permitted": 1, "role_actions": 0})
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        _mark("x", {"open_close_not_permitted": 0, "role_actions": 0})
