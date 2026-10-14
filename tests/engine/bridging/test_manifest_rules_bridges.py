"""第 1 期 1-4: manifest の ``bridges_count``・``rules_version``・``run_kind``・``bridges_version``(CP10・CP5-5・TM9・
口の約束 1-4・検収 L1・M2)。

- 欄がある(一番上の鍵の末尾=凍結の表 ``tests/engine/time/manifest_keys_frozen.json``)・値が台帳と表に一致・節は設定。
- 日次の記録(TM9 の行)にも ``bridges_count`` と ``rules_version``(``events`` の前・既存の鍵の順は変えない)。
- ``run_kind`` の規則(今は 1 つ・``cli.run`` が決める=検収 M2): 試験の中 → ``test`` / CLI の既定と違う腕の引数を
  渡した → ``arm`` / ほか → ``reproduction``(反実仮想は 3-3)。``run_day`` を直に呼ぶランは null(決めていない)。
  ``run_day`` の引数には入れない(設定の指紋と状態のファイルは変わらない)。``cli.run`` を直に呼ぶ byte-check・10e・C7
  の道具の腕の構成も ``arm`` になる。
- 欄の値を変えても final・呼数は同じ(manifest は final に入らない)。
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from shibuya import cli
from shibuya.core.time_consts import STEPS_PER_DAY
from shibuya.engine import manifest_sections as MS
from shibuya.engine import run_kind as RK
from shibuya.engine.bridging import ledger as BR
from shibuya.engine.rules import table as RT
from shibuya.engine.run import run_day

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TOP = json.loads((HERE.parent / "time" / "manifest_keys_frozen.json").read_text(encoding="utf-8"))["keys"]
EV_FROZEN = json.loads((HERE.parent / "events" / "manifest_events_keys_frozen.json").read_text(encoding="utf-8"))
R14 = ["rules_version", "run_kind", "bridges_version"]


@pytest.fixture(scope="module")
def two_days():
    return run_day(n_agents=40, seed=4, n_cells=9, ticks=STEPS_PER_DAY, sim_days=2, budget=40.0, vocab_version="v3",
                   checkpoint_every=360, processes=False, renderer="stub")


# ================================================================= manifest の欄
def test_the_fields_are_at_the_end_and_frozen(two_days):
    keys = list(two_days.run_manifest_fields())
    # 1-9 が末尾に economy、1-2 がその後ろに percept、1-5 がその後ろに rights、1-8 J0 がその後ろに decision_port、1-7 が
    # その後ろに tools、1-8b がその後ろに speech_port、2-2 がその後ろに proximity を足した(T0 の TM9 → 1-4 の 3 欄 → 1-9 →
    # 1-2 → 1-5 → 1-8 → 1-7 → 1-8b → 2-2)=1-4 の 3 欄は末尾の 7 つ前までの続きの並び
    assert keys == TOP and keys[-10:-7] == R14 and keys[-11] == "bridges_count"
    assert keys[-7:] == ["economy", "percept", "rights", "decision_port", "tools", "speech_port", "proximity"]


def test_values_match_the_ledger_and_the_table(two_days):
    m = two_days.run_manifest_fields()
    assert m["bridges_count"] == BR.default_ledger().count() == len(BR.default_ledger().active()) > 0
    assert m["rules_version"] == RT.default_rules().sha == RT.canonical_sha(
        json.loads(RT.default_path().read_text(encoding="utf-8")))
    assert m["bridges_version"] == BR.default_ledger().sha == BR.canonical_sha(
        json.loads(BR.default_path().read_text(encoding="utf-8")))
    assert m["run_kind"] is None  # run_day を直に呼んだ=決めていない(検収 M2)


def test_sections_are_config():
    for k in ("bridges_count", "rules_version", "run_kind", "bridges_version"):
        assert MS.section_of(k) == MS.CONFIG


def test_daily_records_carry_the_count_and_the_version_before_events(two_days):
    daily = two_days.run_manifest_fields()["daily"]
    assert len(daily) == 2
    for d in daily:
        keys = list(d)
        assert [k for k in keys if k in EV_FROZEN["daily_keys_before_1_3"]] == EV_FROZEN["daily_keys_before_1_3"]
        # 1-9 が 1-4 の 2 欄の後ろ(events の前)に economy を足した
        assert keys[-4:] == ["bridges_count", "rules_version", "economy", "events"]
        assert d["bridges_count"] == BR.default_ledger().count()
        assert d["rules_version"] == RT.default_rules().sha


def test_missing_files_give_null_with_a_warning(monkeypatch, tmp_path):
    """台帳と表の無い写し(``git archive`` で src だけ取った木)では欄は null(ランは止めない)。"""
    monkeypatch.setattr(BR, "default_path", lambda: tmp_path / "none.json")
    monkeypatch.setattr(RT, "default_path", lambda: tmp_path / "none.json")
    BR.default_ledger.cache_clear()
    RT.default_rules.cache_clear()
    try:
        with pytest.warns(RuntimeWarning):
            assert BR.bridges_count() is None
        with pytest.warns(RuntimeWarning):
            assert BR.bridges_version() is None
        with pytest.warns(RuntimeWarning):
            assert RT.rules_version() is None
    finally:
        BR.default_ledger.cache_clear()
        RT.default_rules.cache_clear()


def test_the_fields_do_not_feed_the_final_hash(monkeypatch):
    base = run_day(n_agents=20, seed=1, n_cells=9, ticks=240, checkpoint_every=60, processes=False, renderer="stub")
    monkeypatch.setattr(BR, "bridges_count", lambda: 999)
    monkeypatch.setattr(BR, "bridges_version", lambda: "f" * 16)
    monkeypatch.setattr(RT, "rules_version", lambda: "0" * 16)
    moved = run_day(n_agents=20, seed=1, n_cells=9, ticks=240, checkpoint_every=60, processes=False, renderer="stub")
    mm = moved.run_manifest_fields()
    assert (mm["bridges_count"], mm["rules_version"], mm["bridges_version"]) == (999, "0" * 16, "f" * 16)
    assert (moved.final_hash, moved.llm_calls) == (base.final_hash, base.llm_calls)


# ================================================================= run_kind の規則
def test_the_rule_test_over_arm_over_reproduction(monkeypatch):
    assert RK.RUN_KINDS == ("reproduction", "counterfactual", "arm", "test")
    assert RK.decide(arms_on=False, testing=False) == "reproduction"
    assert RK.decide(arms_on=True, testing=False) == "arm"
    assert RK.decide(arms_on=True, testing=True) == RK.decide(arms_on=False, testing=True) == "test"
    assert RK.in_test() and RK.decide(arms_on=False) == "test"
    assert RK.resolve(None) is None and RK.resolve("counterfactual") == "counterfactual"
    monkeypatch.delenv(RK.PYTEST_ENV, raising=False)
    assert not RK.in_test() and RK.decide(arms_on=False) == "reproduction"
    with pytest.raises(ValueError):
        RK.check("experiment")


def _cli_run_view(kw: dict) -> dict:
    """``cli.run`` が ``run_arms`` に渡す形(既定の倍率・母集団・資本・空腹のモデル)。"""
    kw = dict(kw)
    kw.setdefault("hunger_model", cli.CLI_DEFAULT_HUNGER_MODEL)
    return {**kw, "budget": kw.pop("budget", None), "l4_scale": float(cli.CLI_DEFAULT_L4_SCALE),
            "use_population": True, "store_capital_yen": None}


class _Stub:
    fleet_fields: dict = {}

    def summary(self) -> str:
        return "(stub)"


def test_the_cli_default_is_not_an_arm(monkeypatch):
    """``main`` の既定の引数(``parse_args([])``)を ``run`` で受け取ると、腕は 1 つも無い=``arm_baseline`` は CLI の既定と
    同じ(``on``/``off`` と真偽の書き方の違いはそろえる)。"""
    seen: dict = {}
    monkeypatch.setattr(cli, "run", lambda **kw: (seen.update(kw), _Stub())[1])
    assert cli.main(["--world", "__no_such_dir__"]) == 0
    view = {k: v for k, v in seen.items() if k not in ("n_agents", "seed", "world_dir", "n_cells", "ticks",
                                                       "checkpoint_every", "population_seed", "environment_seed")}
    view["budget"] = None
    assert cli.run_arms(view) == ()
    assert cli.NON_ARM_RUN_KWARGS <= set(cli.arm_baseline()) | {"world_dir", "n_cells"}  # 古い名が残っていない


def _wave2_configs() -> dict:
    p = ROOT / "docs" / "bench" / "analysis" / "wave2-2026-09-30" / "wave2_bytecheck.py"
    spec = importlib.util.spec_from_file_location("wave2_bytecheck_r14", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["wave2_bytecheck_r14"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod.configs()


def test_tool_configs_that_call_cli_run_are_arms():
    """byte-check(10e・19 構成)と 10f の manifest の道具が ``cli.run`` に渡す構成: 既定 v3 だけが再現・ほかは腕(検収 M2)。
    C7 の ``salt_runs`` の再開の引数(``stop_at_tick``・``state_out``・``resume_from``)は腕でない。"""
    kinds = {name: bool(cli.run_arms(_cli_run_view(kw))) for name, kw in _wave2_configs().items()}
    assert len(kinds) == 19
    assert [n for n, arm in kinds.items() if not arm] == ["w6_v3_default"]
    assert cli.run_arms(_cli_run_view({"vocab_version": "v3", "stop_at_tick": 100, "state_out": "x",
                                       "resume_from": "y", "sim_days": 2})) == ()
    assert cli.run_arms(_cli_run_view({"vocab_version": "v3", "memory": "on"})) == ("memory",)
    assert cli.run_arms(_cli_run_view({})) == ("vocab_version",)  # ライブラリの既定 v1=CLI の既定 v3 と違う


def test_cli_main_and_cli_run_decide_the_kind(monkeypatch):
    """``main`` は ``run`` の決め方を使う。試験の中は ``test``・外では既定=再現・腕=arm。"""
    seen: list = []
    real = cli.run

    def spy(**kw):  # noqa: ANN003, ANN202
        res = real(**kw)
        seen.append(res.run_kind)
        return res

    monkeypatch.setattr(cli, "run", spy)
    base = ["--agents", "20", "--world", "__no_such_dir__", "--cells", "9", "--ticks", "30"]
    assert cli.main(base) == 0
    monkeypatch.delenv(RK.PYTEST_ENV, raising=False)
    assert cli.main(base) == 0 and cli.main([*base, "--memory", "on"]) == 0
    assert seen == ["test", "reproduction", "arm"]


def test_cli_run_puts_the_kind_on_the_result_and_not_in_the_fingerprint(monkeypatch):
    kw = dict(n_agents=20, seed=1, world_dir=None, n_cells=9, ticks=30, checkpoint_every=10, vocab_version="v3")
    a = cli.run(**kw)
    assert a.run_kind == "test" and a.run_manifest_fields()["run_kind"] == "test"
    monkeypatch.delenv(RK.PYTEST_ENV, raising=False)
    b = cli.run(**kw)
    c = cli.run(**kw, memory="on")
    d = cli.run(**kw, run_kind="counterfactual")
    assert (b.run_kind, c.run_kind, d.run_kind) == ("reproduction", "arm", "counterfactual")
    assert a.final_hash == b.final_hash == d.final_hash  # 種類は記録だけ
    with pytest.raises(ValueError):
        cli.run(**kw, run_kind="what-if")
