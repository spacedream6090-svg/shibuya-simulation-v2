# -*- coding: utf-8 -*-
"""10f 第 2 段: 母集団の seed と動きの seed の分離(K21 (a))と、salt の道具の回す役(T3 の CRN の健全性)。

- 省略時は今と同じ(final・manifest・設定の指紋)。byte-check 19 構成は記録(README)で別に確かめる。
- 乱数の用途名ごとに、どちらの seed から鍵を作ったかを ``core.rng.derive_key`` を包んで数える(表の網羅)。
- 母集団の seed だけ変えると W16 の抽出が変わり、動きの流れは同じ seed のまま。動きの seed だけ変えると母集団
  (体の属性の配列)と環境(気象の実日・大きな催し・道路工事)が同じ。環境の seed だけ変えると催しと工事が変わり、
  体の属性と動きの流れの鍵は同じ(10f 第 2 段の直し S1)。
- T3: 回す役(``tools/c7/salt_runs.py``)の 2 段の探し方の最初の食い違いの tick が、毎 tick で通しに回した 2 本を
  ``first_diff.py`` で比べた tick と一致・T0 前の behavior-hash・A/A・入力の一致。
"""
from __future__ import annotations

import ast
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from shibuya import cli
from shibuya.core import rng as RNG
from shibuya.engine import geometry as GEO
from shibuya.engine import resume as RS
from shibuya.engine import run as RUN

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "c7"))
import salt_compare as sc  # noqa: E402

WORLD = ROOT / "data" / "world" / "v2"
world_assets = pytest.mark.skipif(not (WORLD / "w2_cells.parquet").exists(), reason="実世界資産 data/world/v2 が無い")
NO_WORLD = "data/world/__none__"  # 無い置き場=合成小世界(139 セル)


def _fd():
    spec = importlib.util.spec_from_file_location(
        "first_diff_10d_t3", ROOT / "docs" / "bench" / "analysis" / "wallbounce-1003" / "10d" / "first_diff.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# ---------------------------------------------------------------- 表の網羅(静的)
#: 用途名を持たない呼び出し(``self.domain`` は既定の定数)。値は ``test_dynamic_domains_match_the_defaults`` で
#: 実物の既定と突き合わせる(検収 S3-1 の 4: 手書きの表が既定の変更を追わない穴)。
_DYNAMIC = {
    "self.domain": {"conversation.invite", "llm.mock"},
    "self.domain + _MOVE_TARGET_DOMAIN_SUFFIX": {"llm.mock.move_target"},
    "self.domain + _SHOP_TARGET_DOMAIN_SUFFIX": {"llm.mock.out_of_cell_target"},
}
_IGNORE = {"seed.check", "/v1/chat/completions"}  # 型の検査だけ・httpx の stream
#: 変数の用途名をそのまま渡す呼び出しを許す場所(再検収 T4: ``core.rng`` の中の ``philox``・``stream`` だけ)。
_PASSTHROUGH_OK = {"?domain": {"core/rng.py"}}
_RNG_FUNCS = ("stream", "philox", "derive_key")
_RNG_MODULES = ("shibuya.core.rng", "core.rng", "rng")


def _rng_aliases(tree: ast.AST) -> tuple[dict[str, str], set[str]]:
    """``from shibuya.core.rng import stream as _s`` の別名(名前 → 本来の名前)と、``import … rng as R`` の名前。"""
    names: dict[str, str] = {f: f for f in _RNG_FUNCS}
    mods: set[str] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[-1] == "rng":
            for a in n.names:
                if a.name in _RNG_FUNCS:
                    names[a.asname or a.name] = a.name
        elif isinstance(n, ast.ImportFrom) and (n.module or "").endswith("core"):
            for a in n.names:
                if a.name == "rng":
                    mods.add(a.asname or a.name)
        elif isinstance(n, ast.Import):
            for a in n.names:
                if a.name.endswith("core.rng"):
                    mods.add(a.asname or a.name)
    return names, mods


def _domains_in_src() -> dict[str, list[str]]:
    root = ROOT / "src" / "shibuya"
    found: dict[str, list[str]] = {}
    for p in root.rglob("*.py"):
        if "build" in p.relative_to(root).parts:
            continue  # 世界データの構築(固定の seed・ランの中から import されない)
        tree = ast.parse(p.read_text(encoding="utf-8"))
        consts = {}
        for n in ast.walk(tree):
            if isinstance(n, (ast.Assign, ast.AnnAssign)):
                tg = n.targets[0] if isinstance(n, ast.Assign) else n.target
                if isinstance(tg, ast.Name) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
                    consts[tg.id] = n.value.value
        names, mods = _rng_aliases(tree)
        for n in ast.walk(tree):
            if not isinstance(n, ast.Call):
                continue
            f = n.func
            if isinstance(f, ast.Name):
                fname = names.get(f.id, "")
            elif isinstance(f, ast.Attribute):
                fname = f.attr if f.attr in _RNG_FUNCS else ""
            else:
                fname = ""
            if not fname:
                continue
            # 用途名は 2 番目の引数か、名前つきの ``domain=``(検収 S3-1 の 2)
            a = n.args[1] if len(n.args) >= 2 else next((k.value for k in n.keywords if k.arg == "domain"), None)
            if a is None:
                if fname == "stream" and isinstance(f, ast.Attribute):
                    continue  # httpx の ``client.stream("POST", …)`` など(引数の形が違う)
                keys = {f"?{fname}:引数なし"}
            elif isinstance(a, ast.Constant):
                keys = {str(a.value)}
            elif isinstance(a, ast.Name):
                keys = {consts.get(a.id, "?" + a.id)}
            else:
                keys = _DYNAMIC.get(ast.unparse(a), {"?" + ast.unparse(a)})
            for k in keys:
                found.setdefault(k, []).append(f"{p.relative_to(root).as_posix()}:{n.lineno}")
    return found


def test_every_rng_domain_in_src_is_classified():
    found = _domains_in_src()
    tables = (RUN.POPULATION_RNG_DOMAINS, RUN.ENVIRONMENT_RNG_DOMAINS, RUN.MOTION_RNG_DOMAINS)
    table = set().union(*tables)
    assert sum(len(t) for t in tables) == len(table)  # 1 つの用途名は 1 つの表だけ
    for k, files in _PASSTHROUGH_OK.items():  # 用途名を変数で受け渡すのは core.rng の中だけ
        assert {loc.rsplit(":", 1)[0] for loc in found.get(k, [])} <= files, (k, found.get(k))
    missing = sorted(k for k in found if k not in table and k not in _IGNORE and k not in _PASSTHROUGH_OK)
    assert missing == [], ("母集団/環境/動きの表に無い乱数の用途名(新しい流れは表に載せる)", {k: found[k] for k in missing})
    stale = sorted(k for k in table if k not in found)
    assert stale == [], ("src に無い用途名が表に残っている", stale)
    # S1(ユーザー決定 2026-10-07): 環境の側は 3 つ・配送は動きの側(つなぎ)
    assert set(RUN.ENVIRONMENT_RNG_DOMAINS) == {"engine.processes.environment", "world.large_event", "world.road_works"}
    assert "world.delivery_inbound" in RUN.MOTION_RNG_DOMAINS and "つなぎ" in RUN.MOTION_RNG_DOMAINS["world.delivery_inbound"]


def test_static_scan_catches_aliases_and_keyword_domains():
    """検収 S3-1 の 1・2: 別名の import と名前つきの ``domain=`` を拾う(わざと書いた断片で)。"""
    snippet = (
        "from shibuya.core.rng import stream as _s, philox\n"
        "from shibuya.core import rng as R\n"
        "def f(seed):\n"
        "    _s(seed, 'x.alias').random()\n"
        "    philox(seed, domain='x.keyword')\n"
        "    R.stream(seed, 'x.module')\n"
        "def g(seed, domain):\n"
        "    _s(seed, domain)\n"
    )
    tree = ast.parse(snippet)
    names, mods = _rng_aliases(tree)
    assert names["_s"] == "stream" and "R" in mods
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        fake = Path(d) / "src" / "shibuya"
        fake.mkdir(parents=True)
        (fake / "m.py").write_text(snippet, encoding="utf-8")
        global ROOT
        old = ROOT
        try:
            ROOT = Path(d)
            got = _domains_in_src()
        finally:
            ROOT = old
    assert {"x.alias", "x.keyword", "x.module"} <= set(got)
    # 再検収 T4: core.rng の外で用途名を変数で受け渡すと、許す場所(core/rng.py)の外として見える
    assert {loc.rsplit(":", 1)[0] for loc in got["?domain"]} == {"m.py"}
    assert not ({loc.rsplit(":", 1)[0] for loc in got["?domain"]} <= _PASSTHROUGH_OK["?domain"])


def test_dynamic_domains_match_the_defaults():
    """検収 S3-1 の 4: ``self.domain`` の手書きの対応を、実物の既定の値と突き合わせる。"""
    from shibuya.engine.conversation import ConversationManager
    from shibuya.llm import mock as MOCK
    from shibuya.llm.mock import MockLLM

    assert {ConversationManager(1).domain, MockLLM(master_seed=1).domain} == _DYNAMIC["self.domain"]
    assert {MockLLM(master_seed=1).domain + MOCK._MOVE_TARGET_DOMAIN_SUFFIX} == _DYNAMIC[
        "self.domain + _MOVE_TARGET_DOMAIN_SUFFIX"]
    assert {MockLLM(master_seed=1).domain + MOCK._SHOP_TARGET_DOMAIN_SUFFIX} == _DYNAMIC[
        "self.domain + _SHOP_TARGET_DOMAIN_SUFFIX"]


#: seed を引数に持つ関数の中のハッシュ(blake3・xxh64)の呼び出し(検収 S3-1 の 3)。用途名を持たない乱数はここに出る。
#: 値は ``MOTION_SALTS`` の鍵か、乱数でない理由。新しい場所が出たら分類を決めてここに足す。
_HASH_SITES = {
    ("engine/run.py", "run_salt_for"): "run_salt",
    ("perception/renderer.py", "__init__"): "run_salt",  # near_salt を渡さないときの run_salt の写し(run_day は渡す)
    ("engine/presence.py", "attendance_draw"): "attendance",
    ("llm/fleet.py", "seed_for"): "fleet.call_seed",
    ("core/rng.py", "derive_key"): "core.rng の鍵の導出そのもの",
    ("core/hashing.py", "xxh64"): "汎用のハッシュ(引数の名前が seed)",
    ("core/hashing.py", "xxh64_array"): "汎用のハッシュ(引数の名前が seed)",
    ("perception/hashes.py", "block_hash"): "汎用のハッシュ(引数の名前が seed)",
    ("engine/processes/environment.py", "select_day"): "層の名前を数にするだけ(乱数は core.rng の環境の流れ)",
    ("engine/run.py", "run_day"): "状態のハッシュ(seed を入れない)",
}
_HASH_FUNCS = {"blake3", "blake3_hex", "blake3_u64", "xxh64", "xxh64_intdigest", "xxh3_64"}


def test_seeded_hash_sites_are_classified():
    root = ROOT / "src" / "shibuya"
    found = set()
    for p in root.rglob("*.py"):
        if "build" in p.relative_to(root).parts:
            continue
        tree = ast.parse(p.read_text(encoding="utf-8"))
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            params = [a.arg for a in fn.args.args + fn.args.kwonlyargs]
            seedy = any("seed" in a for a in params)
            for n in ast.walk(fn):
                if not isinstance(n, ast.Call):
                    continue
                f = n.func
                name = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
                if name in _HASH_FUNCS and (seedy or "seed" in ast.unparse(n)):
                    found.add((p.relative_to(root).as_posix(), fn.name))
    assert found == set(_HASH_SITES), ("seed の近くのハッシュの場所が変わった。乱数なら MOTION_SALTS などに分類する",
                                       sorted(found ^ set(_HASH_SITES)))
    salts = {v for v in _HASH_SITES.values() if v in RUN.MOTION_SALTS}
    assert salts == set(RUN.MOTION_SALTS)


# ---------------------------------------------------------------- 実行時: どの seed で鍵を作ったか
def _record_keys(monkeypatch) -> list[tuple[object, str]]:
    seen: list[tuple[object, str]] = []
    orig = RNG.derive_key

    def rec(master_seed, domain):
        seen.append((master_seed, str(domain)))
        return orig(master_seed, domain)

    monkeypatch.setattr(RNG, "derive_key", rec)
    monkeypatch.setattr(GEO, "derive_key", rec)
    return seen


def _check_split(seen, seed, pop_seed, env_seed):
    by: dict[str, set] = {}
    for s, d in seen:
        by.setdefault(d, set()).add(s)
    bad = {}
    for d, seeds in by.items():
        if d in RUN.POPULATION_RNG_DOMAINS:
            want = pop_seed
        elif d in RUN.ENVIRONMENT_RNG_DOMAINS:
            want = env_seed
        elif d in RUN.MOTION_RNG_DOMAINS:
            want = seed
        elif d == "seed.check":
            continue
        else:
            bad[d] = ("表に無い", seeds)
            continue
        if seeds != {want}:
            bad[d] = (want, seeds)
    assert bad == {}, bad
    return set(by)


def test_population_and_motion_streams_use_their_own_seed_synthetic(monkeypatch):
    seen = _record_keys(monkeypatch)
    cli.run(n_agents=60, seed=3, population_seed=7, environment_seed=11, world_dir=NO_WORLD, n_cells=30, ticks=240,
            checkpoint_every=60, salient_rate_per_10k=3000.0, rng_scheme="counter")
    used = _check_split(seen, 3, 7, 11)
    assert {"world.synthetic", "agent.schedule", "llm.mock"} <= used


@world_assets
@pytest.mark.parametrize("kw", [
    {"vocab_version": "v3", "activity": True},                                   # 既定 v3
    {"plan_executor": False, "report_precondition": False},                      # 帰無(域外居住の抽選)
    {"vocab_version": "v1", "geometry": "edge"},                                 # 希望歩行速度
])
def test_population_and_motion_streams_use_their_own_seed_world(monkeypatch, kw):
    seen = _record_keys(monkeypatch)
    cli.run(n_agents=300, seed=3, population_seed=7, environment_seed=11, world_dir=str(WORLD), ticks=240,
            checkpoint_every=60, **kw)
    used = _check_split(seen, 3, 7, 11)
    assert {"wallet.initial", "agent.schedule", "engine.processes.environment", "world.large_event",
            "world.road_works", "world.delivery_inbound"} <= used
    assert used & {"w16.sample.reserved", "w16.sample.stratum"}  # 300 体は定員先取り層だけで足りる
    if kw.get("plan_executor") is False:
        assert "engine.processes.rail" in used
    if kw.get("geometry") == "edge":
        assert "geometry.desired_speed" in used
    if kw.get("activity"):
        assert {"body.weight", "body.eer"} <= used


# ---------------------------------------------------------------- 省略時は今と同じ
def test_omitted_population_and_environment_seed_is_the_same_run():
    kw = dict(n_agents=80, world_dir=NO_WORLD, n_cells=30, ticks=240, checkpoint_every=60)
    a = cli.run(seed=2, **kw)
    b = cli.run(seed=2, population_seed=2, environment_seed=2, **kw)
    assert a.final_hash == b.final_hash and a.llm_calls == b.llm_calls
    ma, mb = a.run_manifest_fields(), b.run_manifest_fields()
    assert ma["population_seed"] == 2 and ma["environment_seed"] == 2 and ma == mb
    c = cli.run(seed=2, population_seed=5, **kw)
    assert c.final_hash != a.final_hash and c.run_manifest_fields()["population_seed"] == 5


def test_fingerprint_unchanged_by_default_and_carries_different_sub_seeds(tmp_path):
    kw = dict(n_agents=40, world_dir=NO_WORLD, n_cells=20, ticks=1440, checkpoint_every=360)
    heads = {}
    for name, extra in (("omit", {}), ("same", {"population_seed": 1, "environment_seed": 1}),
                        ("pop", {"population_seed": 9}), ("env", {"environment_seed": 8})):
        d = tmp_path / name
        cli.run(seed=1, state_out=str(d), stop_at_tick=120, **kw, **extra)
        heads[name] = json.loads(next(d.glob("state-T*.json")).read_text(encoding="utf-8"))["fingerprint"]
    assert "population_seed" not in heads["omit"] and "environment_seed" not in heads["omit"]
    assert heads["omit"] == heads["same"]
    assert RS.fingerprint_diff(heads["omit"], heads["pop"]) == ["population_seed"]
    assert RS.fingerprint_diff(heads["omit"], heads["env"]) == ["environment_seed"] and heads["env"]["environment_seed"] == 8


def test_bad_sub_seeds_are_refused():
    for bad in (True, -1, ""):
        for k in ("population_seed", "environment_seed"):
            with pytest.raises((TypeError, ValueError)):
                cli.run(n_agents=10, seed=1, world_dir=NO_WORLD, n_cells=10, ticks=10, **{k: bad})


# ---------------------------------------------------------------- 母集団だけ・環境だけ・動きだけを変える
#: 体の属性: 日課(母集団の素性を含む)の欄と、SoA の体の定数の列。
_SCHED = ("home_cell", "work_cell", "leisure_cell", "school_cell", "kind", "age", "sex", "direction_node",
          "initial_money", "base_ticks", "weekend_ticks")
_SOA = ("kind", "age", "sex", "weight_kg", "eer_kcal")


def _bodies(res):
    out = {f"schedule.{c}": np.asarray(getattr(res.schedule, c)).copy() for c in _SCHED
           if getattr(res.schedule, c, None) is not None}
    arr = res.agents.registry.arrays
    out.update({f"soa.{c}": np.asarray(arr[c]).copy() for c in _SOA if c in arr})
    return out


def _env(res):
    """環境の側の値: 気象の再生実日と層・大きな催しの会場・道路工事の辺。"""
    ru = res.runner
    m = res.run_manifest_fields()
    return {"replay_date": m["replay_date"], "start": m["start_sim_datetime"], "stratum": ru.environment.stratum,
            "venue": ru.large_event.venue_cells.tolist(), "works": ru.road_works.planned_edges.tolist()}


@world_assets
def test_motion_seed_only_keeps_the_population_and_environment():
    kw = dict(n_agents=300, world_dir=str(WORLD), ticks=120, checkpoint_every=60, vocab_version="v3", activity=True)
    a = cli.run(seed=1, population_seed=1, environment_seed=1, **kw)
    b = cli.run(seed=2, population_seed=1, environment_seed=1, **kw)     # 動きの seed だけ
    c = cli.run(seed=1, population_seed=2, environment_seed=1, **kw)     # 母集団の seed だけ
    ba, bb, bc = _bodies(a), _bodies(b), _bodies(c)
    assert set(ba) >= {"schedule.home_cell", "schedule.age", "soa.age", "soa.weight_kg", "soa.eer_kcal"}
    for k in ba:
        assert np.array_equal(ba[k], bb[k]), k  # 動きの seed だけ → 体の属性の配列が一致
    assert a.checkpoints[0].population_hash == b.checkpoints[0].population_hash
    assert a.checkpoints[0].schedule_hash == b.checkpoints[0].schedule_hash
    assert _env(a) == _env(b)  # 動きの seed だけ → 気象・催し・工事が同じ
    assert a.final_hash != b.final_hash  # 動きは違う
    # 母集団の seed だけ → W16 の抽出が変わる(動きの流れの鍵は seed=1 のまま=上の記録の試験)・環境は同じ
    assert a.checkpoints[0].population_hash != c.checkpoints[0].population_hash
    assert not np.array_equal(ba["schedule.home_cell"], bc["schedule.home_cell"])
    assert not np.array_equal(ba["soa.weight_kg"], bc["soa.weight_kg"])
    assert _env(a) == _env(c)
    assert RUN.run_salt_for(1) == RUN.run_salt_for(a.seed) == RUN.run_salt_for(c.seed)


@world_assets
def test_environment_seed_only_changes_weather_events_and_works(monkeypatch):
    """S1: 環境の seed だけ変えると、大きな催しの会場と工事の辺が変わり、体の属性と動きの流れの鍵は同じ。

    気象の再生実日: 既定のランは影のある日に絞る(W9 は 1 再生日ぶん)ので、世界資産では実日は 1 日に決まる。
    そこで実日の選び方は、同じ過程を影の絞りを外して作り、環境の seed で実日が変わることを別に確かめる。
    """
    from shibuya.engine.processes.environment import EnvironmentProcess

    kw = dict(n_agents=300, world_dir=str(WORLD), ticks=120, checkpoint_every=60, vocab_version="v3", activity=True)
    seen = _record_keys(monkeypatch)
    a = cli.run(seed=1, population_seed=1, environment_seed=1, **kw)
    n_a = len(seen)
    d = cli.run(seed=1, population_seed=1, environment_seed=2, **kw)  # 環境の seed だけ
    ea, ed = _env(a), _env(d)
    assert ea["venue"] != ed["venue"] and ea["works"] != ed["works"]
    ba, bd = _bodies(a), _bodies(d)
    for k in ba:
        assert np.array_equal(ba[k], bd[k]), k
    # 動きの流れの鍵: 環境の側以外の用途名は 2 本とも同じ seed の組で作った
    skip = set(RUN.ENVIRONMENT_RNG_DOMAINS) | {"seed.check"}
    motion_a = {(s, dm) for s, dm in seen[:n_a] if dm not in skip}
    motion_d = {(s, dm) for s, dm in seen[n_a:] if dm not in skip}
    assert motion_a == motion_d
    assert {s for s, dm in seen[n_a:] if dm in RUN.ENVIRONMENT_RNG_DOMAINS} == {2}
    assert a.runner.environment.master_seed == 1 and d.runner.environment.master_seed == 2
    days = {EnvironmentProcess(a.world, a.agents, a.runner.assets, master_seed=e, prefer_shadow_days=False).replay_date
            for e in range(1, 7)}
    assert len(days) > 1  # 環境の seed で実日が変わる


# ---------------------------------------------------------------- T3: 回す役と CRN の健全性
def test_t3_runner_first_diff_matches_first_diff_py_and_crn_checks(tmp_path):
    arms = {"base": {}, "sal": {"salient_rate_per_10k": 100.0}}
    out = tmp_path / "runs.json"
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "c7" / "salt_runs.py"), "plan", "--arms", json.dumps(arms),
                        "--base", "base", "--arm", "sal", "--salts", "1,2", "--population-seed", "1", "--agents", "200",
                        "--world", NO_WORLD, "--scratch", str(tmp_path), "--out", str(out), "--aa", "--first-diff",
                        "--jobs", "2"], cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr[-3000:]
    index = json.loads(out.read_text(encoding="utf-8"))
    assert all("/" not in x["checkpoints"] and "\\" not in x["checkpoints"] for x in index["runs"])
    payloads = {x["checkpoints"]: json.loads((tmp_path / x["checkpoints"]).read_text(encoding="utf-8"))
                for x in index["runs"]}
    fd = _fd()
    for s in (1, 2):
        # 毎 tick で通しに回した 2 本を first_diff.py で比べた tick(独立の答え)
        dumps = []
        for name in ("base", "sal"):
            res = cli.run(n_agents=200, seed=s, population_seed=1, world_dir=NO_WORLD, checkpoint_every=1, **arms[name])
            dumps.append(fd.dump(res, tmp_path / f"straight_{name}_{s}.json"))
        want = fd.compare(dumps[0], [dumps[1]], from_T=0)["first_mismatch"]["tick"]
        got = index["first_diff_fine"][str(s)]
        assert got["first_tick"] == want, (s, got, want)
        assert got["interval"][0] <= want <= got["interval"][1]
        # T0 前の behavior-hash: T0 = 最初の食い違いなら一致・それより後の T0 なら落ちる(通しの毎 tick の 2 本で)
        a_doc = {"checkpoints": [{"tick": c[0], "behavior_hash": c[2]} for c in dumps[0]["checkpoints"]]}
        b_doc = {"checkpoints": [{"tick": c[0], "behavior_hash": c[2]} for c in dumps[1]["checkpoints"]]}
        assert sc.pre_t0_match(a_doc, b_doc, want)["ok"] is True
        bad = sc.pre_t0_match(a_doc, b_doc, want + 60)
        assert bad["ok"] is False and bad["first_bad_tick"] == want
    crn = sc.crn_health(index, payloads)
    assert crn["input_match"]["ok"] is True and crn["input_match"]["population_fixed"] is True
    assert crn["aa"] and all(x["ok"] for x in crn["aa"])  # A/A が一致
    assert crn["ok"] is True and crn["status"] == "ok"
    assert index["environment_mode"] == "fixed" and crn["input_match"]["environment_fixed"] is True
    # salient_rate_per_10k は manifest の設定の節に載っていない腕=報告に出る(落とさない)
    assert crn["input_match"]["arm_keys_unseen"] == ["salient_rate_per_10k"]
    spec = {"alpha": 0.05, "primary": {"id": "calls", "path": "manifest.llm_calls_total"}}
    rep = sc.report(index, payloads, spec)
    assert rep["analysis"]["metrics"]["calls"]["status"] == sc.DESCRIPTIVE  # 2 対


def test_runner_environment_modes(tmp_path):
    """S1: 回す役の ``--environment-mode``。fixed は環境の seed が全部同じ(省略=母集団の seed)・salt は salt と同じ。"""
    arms = {"base": {}, "sal": {"salient_rate_per_10k": 100.0}}
    idx = {}
    for mode in ("fixed", "salt"):
        d = tmp_path / mode
        out = tmp_path / f"runs_{mode}.json"
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "c7" / "salt_runs.py"), "plan", "--arms", json.dumps(arms),
                            "--base", "base", "--arm", "sal", "--salts", "2,3", "--population-seed", "1",
                            "--environment-mode", mode, "--agents", "60", "--world", NO_WORLD, "--scratch", str(d),
                            "--out", str(out), "--jobs", "2"], cwd=str(ROOT), capture_output=True, text=True,
                           encoding="utf-8")
        assert r.returncode == 0, r.stderr[-3000:]
        index = json.loads(out.read_text(encoding="utf-8"))
        pay = {x["checkpoints"]: json.loads((d / x["checkpoints"]).read_text(encoding="utf-8")) for x in index["runs"]}
        envs = {x["salt"]: pay[x["checkpoints"]]["manifest"]["environment_seed"] for x in index["runs"]}
        crn = sc.crn_health(index, pay)
        idx[mode] = (index, envs, crn)
    index, envs, crn = idx["fixed"]
    assert index["environment_seed"] == 1 and set(envs.values()) == {1} and crn["input_match"]["ok"] is True
    assert crn["status"] == sc.UNCHECKED  # A/A を回していない=未検査(検収 S2)
    index, envs, crn = idx["salt"]
    assert index["environment_seed"] is None and envs == {2: 2, 3: 3}
    assert crn["input_match"]["ok"] is True and crn["input_match"]["environment_fixed"] is False
    # 置き場が空でなければ止める(検収 S3-6)
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "c7" / "salt_runs.py"), "plan", "--arms", json.dumps(arms),
                        "--base", "base", "--arm", "sal", "--salts", "2", "--agents", "20", "--world", NO_WORLD,
                        "--scratch", str(tmp_path / "fixed"), "--out", str(tmp_path / "again.json")],
                       cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8",
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    assert r.returncode == 2 and "空でない" in (r.stderr or "")
    assert not (tmp_path / "again.json").exists()


def _large_event_venue(world, agents, env, day):
    from shibuya.engine.processes.civic import LargeEventProcess

    return LargeEventProcess(world, agents, master_seed=env, day_index=day).venue_cells


@world_assets
def test_road_works_day_key_with_nonzero_day_index():
    """再検収 T1: ``day_index`` が 0 でないランで、0 日目の工事の辺はその日の鍵(``day_index``)と環境の seed で引く。

    HEAD と同じ規則(``RoadWorksProcess(day_index=day_key)``)。直す前は鍵が 0 になっていた(byte-check の 19 構成は
    全部 day_index=0 なので捕まえられなかった)。大きな催しの会場も同じ形で確かめる。
    """
    from shibuya.engine.processes.logistics import RoadWorksProcess

    kw = dict(n_agents=300, world_dir=str(WORLD), ticks=30, checkpoint_every=0)  # 合成世界の資産には工事の辺が無い
    for env, day in ((1, 3), (5, 3), (5, 2)):
        r = cli.run(seed=1, environment_seed=env, day_index=day, **kw)
        rw = r.runner.road_works
        want = RoadWorksProcess(r.world, r.runner.assets, master_seed=env, day_index=day).planned_edges
        key0 = RoadWorksProcess(r.world, r.runner.assets, master_seed=env, day_index=0).planned_edges
        assert rw.planned_edges.size > 0
        assert np.array_equal(rw.planned_edges, want), (env, day)
        assert not np.array_equal(want, key0)  # 鍵 0 と区別できる例であること
        assert np.array_equal(r.runner.large_event.venue_cells, _large_event_venue(r.world, r.agents, env, day))


def test_runner_refuses_seed_args_in_arms(tmp_path):
    """再検収 T5: 腕の引数に seed の 3 つを書くと、理由を出して止める。"""
    for k in ("seed", "population_seed", "environment_seed"):
        arms = {"base": {}, "arm": {k: 2}}
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "c7" / "salt_runs.py"), "plan", "--arms",
                            json.dumps(arms), "--base", "base", "--arm", "arm", "--salts", "1", "--agents", "10",
                            "--world", NO_WORLD, "--scratch", str(tmp_path / k), "--out", str(tmp_path / f"{k}.json")],
                           cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8",
                           env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        assert r.returncode != 0 and k in (r.stderr or "")
        assert not (tmp_path / k).exists()
