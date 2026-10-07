"""10f 第 1 段: 環境の欄(K26 (a)+(1))・manifest の設定と観測の分離(K22 (a))・O75 の見直し・検収の直し(N1〜N9)。

- T1: 別々のプロセスで 2 回回して、書かれたファイル(manifest の JSON・状態の見出し・``run_meta.json``)の ``env_id`` と
  final が一致・環境の欄を抜いた manifest も一致。
- ``env_id`` を manifest・状態のファイルの見出し・テープの ``run_meta.json`` の 3 か所に同じ値で書く。
- 登録の無い環境では golden と比べず A/A だけ。そのとき警告を出す(黙って通さない=検収 N2)。
- ``seed_exchangeability`` は設定の節だけを比べる。混ざった辞書は葉まで表に載る(検収 N3)。
- 再開と再生で、元を書いた環境の ``platform_id`` が違えば警告を 1 行(§8 の 6)。
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import warnings
from pathlib import Path

import pytest

from shibuya.core.hashing import blake3_hex
from shibuya.engine import manifest_sections as MS
from shibuya.engine import resume as RS
from shibuya.engine import state_ledger as SL
from shibuya.engine.run import run_day
from shibuya.engine.tape import RUN_META_FILENAME, read_run_meta
from tests import golden_env as GE

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "c7"))
import seed_exchangeability as sx  # noqa: E402

WORLD = ROOT / "data" / "world" / "v2"
NEW_KEYS = ("env_id", "environment", "manifest_sections")
#: 10f 第 2 段(K21 (a))で末尾に足した欄。
STAGE2_KEYS = ("population_seed", "environment_seed")
PLATFORM_KEYS = {"python", "python_implementation", "numpy", "numba", "llvmlite", "blake3", "os", "os_release",
                 "os_version", "machine", "cpu", "numpy_simd", "deps", "deps_sha256", "deps_count"}
#: 設定の節の道筋の一覧の sha256(環境に依らない golden=検収 N3 の 3)。節を変えたら理由を記録に書いて更新する。
#: 10f 第 2 段: ``population_seed``(K21 (a)の母集団の seed・設定)を足した(前の値 170e1c30…)。
#: 10f 第 2 段の直し(S1): ``environment_seed``(環境の seed・設定)を足した(前の値 3fe95edb…)。
CONFIG_PATHS_SHA256 = "457d86667edc617a5a398711fe5c2cbbcf39d7ece54fb6eaec74fb8fe2312f58"
world_assets = pytest.mark.skipif(not (WORLD / "w2_cells.parquet").exists(), reason="実世界資産 data/world/v2 が無い")


def _small(**kw):
    base = dict(n_agents=20, n_cells=9, ticks=30, seed=1, renderer="stub")
    base.update(kw)
    return run_day(**base)


def _canon_id(v):
    return blake3_hex(json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))[:16]


# ================================================================= 環境の欄
def test_environment_fields_shape_and_ids():
    e = RS.environment_fields()
    assert e["schema"] == RS.ENV_SCHEMA
    assert set(e) == {"schema", "platform", "runtime", "code", "platform_id", "env_id"}
    assert set(e["platform"]) == PLATFORM_KEYS
    assert set(e["runtime"]) == {"numba_threads", "numba_threads_env"}
    assert set(e["code"]) == {"git_commit", "git_dirty", "git_diff_sha256"}
    body = {k: e[k] for k in ("schema", "platform", "runtime", "code")}
    assert e["env_id"] == _canon_id(body)
    assert e["platform_id"] == _canon_id({k: e["platform"][k] for k in RS.PLATFORM_ID_KEYS})
    assert set(RS.PLATFORM_ID_KEYS) == PLATFORM_KEYS - {"deps", "deps_sha256", "deps_count"}
    # 依存の一覧の写し(検収 N4): 昇順・「名前==版」・sha256 と本数が一覧から計算し直せる
    deps = e["platform"]["deps"]
    assert deps == sorted(set(deps)) and all("==" in d for d in deps)
    body_txt = "\n".join(deps) + "\n"
    assert e["platform"]["deps_sha256"] == "sha256:" + hashlib.sha256(body_txt.encode("utf-8")).hexdigest()
    assert e["platform"]["deps_count"] == len(deps) > 0
    # 毎回新しい写し(呼び手が書き換えても次の値は変わらない)
    e["platform"]["python"] = "x"
    e["platform"]["deps"].append("zzz==1")
    again = RS.environment_fields()
    assert again["platform"]["python"] != "x" and "zzz==1" not in again["platform"]["deps"]
    assert RS.platform_fields() == RS.environment_fields()
    import platform

    node = platform.node()
    if node:
        assert node not in json.dumps(RS.environment_fields(), ensure_ascii=False)


def test_missing_git_gives_empty_values_and_keeps_the_fields(monkeypatch):
    def boom(*a, **k):
        raise FileNotFoundError("git")

    monkeypatch.setattr(subprocess, "run", boom)
    assert RS._git_state() == {"git_commit": "", "git_dirty": None, "git_diff_sha256": ""}


def test_git_values_only_when_the_toplevel_is_the_package_root(monkeypatch):
    """検収 N7: 写しが別のリポの中にあるとき外の commit を拾わない(toplevel が根と違えば空)。"""
    real = RS._git_state()
    monkeypatch.setattr(RS, "_repo_root", lambda: ROOT / "src")  # リポの中のサブディレクトリ=toplevel が違う
    assert RS._git_state() == {"git_commit": "", "git_dirty": None, "git_diff_sha256": ""}
    if real["git_commit"]:
        assert len(real["git_commit"]) == 40
        assert (real["git_diff_sha256"] != "") == bool(real["git_dirty"])


def test_git_commands_take_no_optional_locks_and_ignore_untracked(monkeypatch):
    """検収 N6・N7: すべての git の呼び出しに --no-optional-locks・status は追跡ファイルだけ。"""
    seen: list[list[str]] = []
    real_run = subprocess.run

    def spy(cmd, *a, **k):
        seen.append(list(cmd))
        return real_run(cmd, *a, **k)

    monkeypatch.setattr(subprocess, "run", spy)
    RS._git_state()
    if not seen:
        pytest.skip("git が無い")
    assert all(c[:2] == ["git", "--no-optional-locks"] for c in seen)
    st = [c for c in seen if "status" in c]
    assert not st or "--untracked-files=no" in st[0]


def test_platform_id_ignores_commit_threads_and_dependency_versions(monkeypatch):
    """golden の行の鍵(platform_id)は commit・dirty・スレッド数・依存の一覧で動かない。env_id は動く(検収 N2)。"""
    base = RS.environment_fields()
    monkeypatch.setattr(RS, "_git_state", lambda: {"git_commit": "0" * 40, "git_dirty": False, "git_diff_sha256": ""})
    monkeypatch.setattr(RS, "_numba_threads", lambda: 1)
    real_deps = RS._deps_list
    monkeypatch.setattr(RS, "_deps_list", lambda: sorted(real_deps() + ["pytest==99.0"]))  # 検収役の再現 a2
    try:
        other = RS.environment_fields(refresh=True)
        assert other["platform_id"] == base["platform_id"]
        assert other["env_id"] != base["env_id"]
        assert other["platform"]["deps_count"] == base["platform"]["deps_count"] + 1
    finally:
        monkeypatch.undo()
        RS.environment_fields(refresh=True)
    assert RS.environment_fields()["env_id"] == base["env_id"]


def test_env_id_is_the_same_in_the_three_places(tmp_path):
    """manifest・状態のファイルの見出し・テープの run_meta.json の 3 か所が同じ env_id(同じプロセス)。"""
    res = _small(ticks=1440, sim_days=2, stop_at_tick=1440, tape_path=str(tmp_path / "tape"),
                 state_out=str(tmp_path / "st"))
    m = res.run_manifest_fields()
    side = json.loads(next((tmp_path / "st").glob("state-T*.json")).read_text(encoding="utf-8"))
    bundle = RS.read_state(next((tmp_path / "st").glob("state-T*.npz")))
    meta = read_run_meta(tmp_path / "tape")
    want = RS.environment_fields()["env_id"]
    assert m["env_id"] == side["env_id"] == bundle.header["env_id"] == meta["env_id"] == want
    assert m["environment"] == side["platform"] == bundle.header["platform"] == meta["environment"]
    # 検収 N9: manifest の環境の欄は深い写し(書き換えても結果の側は動かない)
    m["environment"]["platform"]["numpy"] = "0.0"
    assert res.run_manifest_fields()["environment"]["platform"]["numpy"] != "0.0"


_T1_CHILD = r"""
import json, sys
from pathlib import Path
from shibuya import cli
from shibuya.engine.run import run_day
out = Path(sys.argv[1])
r = run_day(n_agents=20, n_cells=9, ticks=1440, sim_days=2, stop_at_tick=1440, seed=1, renderer="stub",
            tape_path=str(out / "tape"), state_out=str(out / "st"))
(out / "checkpoints.json").write_text(json.dumps(cli.checkpoints_payload(r), ensure_ascii=False, default=str),
                                      encoding="utf-8")
"""


def test_t1_two_processes_write_the_same_env_id_and_final_to_the_files(tmp_path):
    """T1(検収 N9): 別々のプロセスで 2 回回し、書かれたファイルを読んで比べる。"""
    docs = []
    for i in (1, 2):
        out = tmp_path / f"p{i}"
        out.mkdir()
        r = subprocess.run([sys.executable, "-c", _T1_CHILD, str(out)], cwd=str(ROOT), capture_output=True,
                           text=True, encoding="utf-8")
        assert r.returncode == 0, r.stderr[-2000:]
        ck = json.loads((out / "checkpoints.json").read_text(encoding="utf-8"))
        head = json.loads(next((out / "st").glob("state-T*.json")).read_text(encoding="utf-8"))
        meta = json.loads((out / "tape" / RUN_META_FILENAME).read_text(encoding="utf-8"))
        assert ck["manifest"]["env_id"] == head["env_id"] == meta["env_id"]
        docs.append((ck, head, meta))
    (c1, h1, _), (c2, h2, _) = docs
    assert c1["manifest"]["env_id"] == c2["manifest"]["env_id"] == RS.environment_fields()["env_id"]
    assert c1["final_hash"] == c2["final_hash"] and h1["hashes"] == h2["hashes"]
    # resume はラン ID(実行ごとに一意・10d 検収 L6)と秒を持つので除く
    drop = lambda m: {k: v for k, v in m.items() if k not in NEW_KEYS + ("resume",)}  # noqa: E731
    assert drop(c1["manifest"]) == drop(c2["manifest"])
    assert c1["manifest"]["resume"]["run_id"] != c2["manifest"]["resume"]["run_id"]
    assert list(c1["manifest"])[-5:] == list(NEW_KEYS + STAGE2_KEYS)  # 列追加のみ(末尾に 3 つ+第 2 段の 2 つ)


# ================================================================= 再開・再生で環境の違いを警告(§8 の 6)
def test_resume_from_another_environment_warns_once_and_keeps_going(tmp_path):
    st = tmp_path / "st"
    _small(ticks=1440, sim_days=2, stop_at_tick=1440, state_out=str(st), checkpoint_every=360)
    pkl = next(st.glob("state-T*.npz"))
    with warnings.catch_warnings():
        warnings.simplefilter("error", RS.EnvironmentMismatchWarning)  # 同じ環境では出ない
        same = _small(ticks=1440, sim_days=2, resume_from=str(pkl), checkpoint_every=360)
    bundle = RS.read_state(pkl)  # 10f: npz+json(K23 (a))
    bundle.header["platform"]["platform_id"] = "f" * 16  # 別の環境で書いたことにする(写しと sha256 も書き直す)
    other = tmp_path / "other" / pkl.name
    RS.write_state(other, bundle)
    with pytest.warns(RS.EnvironmentMismatchWarning, match="ffffffffffffffff") as got:
        moved = _small(ticks=1440, sim_days=2, resume_from=str(other), checkpoint_every=360)
    assert len([w for w in got if issubclass(w.category, RS.EnvironmentMismatchWarning)]) == 1
    assert moved.final_hash == same.final_hash  # 挙動は変えない


def test_replay_of_a_tape_from_another_environment_warns_once(tmp_path):
    from tests.engine.processes.test_rng_scheme_10c import _rec, _rep

    rec = _rec(tmp_path, "t")
    with warnings.catch_warnings():
        warnings.simplefilter("error", RS.EnvironmentMismatchWarning)
        assert _rep(tmp_path, "t").final_hash == rec.final_hash
    meta_p = tmp_path / "t" / RUN_META_FILENAME
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    meta["environment"]["platform_id"] = "e" * 16
    meta_p.write_text(json.dumps(meta) + "\n", encoding="utf-8")
    with pytest.warns(RS.EnvironmentMismatchWarning, match="eeeeeeeeeeeeeeee") as got:
        rep = _rep(tmp_path, "t")
    assert len([w for w in got if issubclass(w.category, RS.EnvironmentMismatchWarning)]) == 1
    assert rep.final_hash == rec.final_hash
    # 10f より前のテープ(環境の欄が無い)は何も言わない
    meta.pop("environment")
    meta_p.write_text(json.dumps(meta) + "\n", encoding="utf-8")
    with warnings.catch_warnings():
        warnings.simplefilter("error", RS.EnvironmentMismatchWarning)
        _rep(tmp_path, "t")


# ================================================================= golden の行(検収 N2)
def test_unregistered_environment_warns_and_falls_back_to_aa(monkeypatch, capsys):
    table = {GE.PLATFORM_10F: ("final", 1)}
    monkeypatch.setattr(GE, "platform_id", lambda: "0000000000000000")
    monkeypatch.setattr(GE, "_ANNOUNCED", {})
    with pytest.warns(GE.GoldenUnregisteredWarning, match="0000000000000000"):
        assert GE.row(table) is None
    err = capsys.readouterr().err
    assert "未登録" in err and "0000000000000000" in err
    GE.announce_once()
    assert capsys.readouterr().err == ""  # 1 回だけ
    n = {"runs": 0}

    def run():
        n["runs"] += 1
        return ("same", 7)

    with pytest.warns(GE.GoldenUnregisteredWarning):
        assert GE.assert_aa(run, lambda r: r) == ("same", 7) and n["runs"] == 2
    vals = iter([("a", 1), ("b", 1)])
    with pytest.warns(GE.GoldenUnregisteredWarning), pytest.raises(AssertionError, match="A/A が一致しない"):
        GE.assert_aa(lambda: next(vals), lambda r: r)
    monkeypatch.setattr(GE, "platform_id", lambda: GE.PLATFORM_10F)
    with warnings.catch_warnings():
        warnings.simplefilter("error", GE.GoldenUnregisteredWarning)
        assert GE.row(table) == ("final", 1)


def test_removing_a_bit_relevant_field_makes_the_golden_check_loud(monkeypatch):
    """検収役の再現 a1(platform から cpu を抜く): platform_id が変わり、golden の行の取り出しが警告を出す。"""
    import platform as _pf

    base = RS.environment_fields()["platform_id"]
    monkeypatch.setattr(_pf, "processor", lambda: "")
    try:
        assert RS.environment_fields(refresh=True)["platform_id"] != base
        with pytest.warns(GE.GoldenUnregisteredWarning):
            assert GE.row({GE.PLATFORM_10F: 1}) is None
    finally:
        monkeypatch.undo()
        RS.environment_fields(refresh=True)
    assert RS.environment_fields()["platform_id"] == base


def test_golden_tables_are_keyed_by_platform_and_values_unchanged():
    from tests.engine import test_classical_social as TCS
    from tests.engine import test_presence_derive_v2 as TPD
    from tests.engine import test_presence_executor as TPE
    from tests.engine import test_relations_tenure as TRT
    from tests.perception import test_near_tiebreak as TNT

    assert GE.platform_id() in GE.REGISTERED, "この環境は golden に未登録(記録の機械と違う)"
    for t in (TPE.W17_GOLDEN_BY_ENV, TPD.REAL_GOLDEN_BY_ENV, TRT.REL_ON_5000_GOLDEN_BY_ENV,
              TNT.CLASSICAL_1500_GOLDEN_BY_ENV, TCS.CLASSICAL_1500_GOLDEN_ACQ_BY_ENV):
        assert set(t) == {GE.PLATFORM_10F}
    g = TPE.W17_GOLDEN_BY_ENV[GE.PLATFORM_10F]["3113e9ba7abb"]
    assert (g["v3_default_final"], g["v3_default_llm_calls"]) == ("993276d5e5bb5cbe", 69_978)
    assert (g["null_arm_final"], g["null_arm_llm_calls"]) == ("72cb9cd52982da74", 100_439)
    assert TRT.REL_ON_5000_GOLDEN_BY_ENV[GE.PLATFORM_10F]["v2"] == ("40409ebed834126b", 72_930)


# ================================================================= manifest の節(K22 (a)・検収 N1・N3)
def _payload(res, run_id):
    from shibuya import cli

    return json.loads(json.dumps(cli.checkpoints_payload(res, run_id=run_id), default=str))


def test_every_top_level_manifest_field_has_a_section():
    m = _small().run_manifest_fields()
    missing = [k for k in m if k not in MS.PATHS]
    assert missing == [], f"節の決まっていない manifest の欄(engine/manifest_sections.py に足す): {missing}"
    assert set(MS.PATHS.values()) <= set(MS.SECTION_VALUES)
    assert m["manifest_sections"] == MS.sections_table()
    assert MS.section_of("env_id") == MS.ENVIRONMENT and MS.section_of("rng_scheme") == MS.CONFIG
    assert MS.section_of("energy.counts.meals_in_area") == MS.OBSERVED
    assert MS.section_of("energy.mets.sleep.code") == MS.CONFIG
    assert MS.section_of("state_hashes.ledger_version") == MS.CONFIG
    assert MS.section_of("state_hashes.behavior_hash") == MS.OBSERVED
    assert MS.section_of("no_such_field") is None
    parts = MS.split(m)
    assert parts["unlisted"] == {} and set(parts["environment"]) == {"env_id", "environment"}


def test_relations_init_is_observed_with_constant_leaves_as_config():
    """検収 N1: 関係の初期化は観測(群の数・候補の対・壁時計は seed で動く)。定数の葉だけ設定。"""
    assert MS.section_of("relations.init") == MS.OBSERVED
    for k in ("groups.work", "candidate_pairs", "edges_before_tau", "dropped_by_tau", "init_seconds_nondeterministic",
              "reason"):
        assert MS.section_of(f"relations.init.{k}") == MS.OBSERVED, k
    for k in ("density", "k", "slot_minutes", "tiebreak", "tenure_weeks", "tenure_hash", "w17_single_day"):
        assert MS.section_of(f"relations.init.{k}") == MS.CONFIG, k
    assert MS.section_of("relations.wall_seconds_nondeterministic.detect") == MS.OBSERVED


def test_config_paths_are_frozen():
    """検収 N3 の 3: 設定の節の道筋の一覧を golden で固定(設定 → 観測の黙った付け替えを捕まえる)。"""
    body = "\n".join(MS.config_paths()) + "\n"
    assert hashlib.sha256(body.encode("utf-8")).hexdigest() == CONFIG_PATHS_SHA256, (
        "設定の節の道筋が変わった。理由を記録に書いて CONFIG_PATHS_SHA256 を更新する", MS.config_paths())


def test_mixed_dict_leaves_are_all_listed_synthetic():
    """検収 N3: 混ざった辞書の下の葉はどれも表の子の道筋に当たる(合成世界・全腕・2 日)。"""
    m = _small(ticks=1440, sim_days=2, vocab_version="v3", memory="on", relations="on", store_memory="on",
               familiarity="on", n_agents=40).run_manifest_fields()
    assert MS.unlisted_in_mixed(m) == []
    # わざと新しい鍵を足すと捕まる
    m["energy"]["brand_new_cfg"] = 1
    m["relations"]["init"]["new_param"] = "x"
    assert MS.unlisted_in_mixed(m) == ["energy.brand_new_cfg", "relations.init.new_param"]


@world_assets
def test_mixed_dict_leaves_are_all_listed_world():
    from shibuya import cli

    W = str(WORLD)
    for kw in (dict(vocab_version="v3", memory="on", relations="on", store_memory="on", familiarity="on",
                    home_meal="plan", meal_sleep_defer="on", hunger_words="all", ticks=600),
               dict(vocab_version="v3", policy="classical", chooser="classical", ticks=600),
               dict(vocab_version="v2", geometry="edge", ticks=300)):
        m = cli.run(n_agents=300, seed=1, world_dir=W, **kw).run_manifest_fields()
        assert MS.unlisted_in_mixed(m) == [], kw


@world_assets
def test_seed_exchangeability_passes_for_v3_seeds_and_fails_on_a_config_change():
    """既定 v3 の seed 1 と 2 は交換可能(観測の欄の差は数えるだけ)。設定の欄を変えると落ちる。"""
    from shibuya import cli

    kw = dict(n_agents=300, world_dir=str(WORLD), vocab_version="v3", activity=True, ticks=240)
    d1 = _payload(cli.run(seed=1, **kw), "s1")
    d2 = _payload(cli.run(seed=2, **kw), "s2")
    r = sx.compare([d1, d2], ["s1", "s2"])
    assert r["mode"] == "sections" and r["exchangeable"] is True, r["diff_unexplained"]
    assert r["diff_observed_count"] > 0 and r["unlisted"] == [] and r["environment_warning"] is False
    d3 = _payload(cli.run(seed=2, attendance_rate=0.8, **kw), "s3")
    r3 = sx.compare([d1, d3], ["s1", "s3"])
    assert r3["exchangeable"] is False
    assert "manifest.attendance_rate" in {u["key"] for u in r3["diff_unexplained"]}
    old = [{**d, "manifest": {k: v for k, v in d["manifest"].items() if k not in NEW_KEYS}} for d in (d1, d2)]
    rl = sx.compare(old, ["s1", "s2"])
    assert rl["mode"] == "legacy" and rl["exchangeable"] is False


@pytest.mark.slow
@world_assets
def test_relations_on_5000_seeds_are_exchangeable_and_config_leaves_do_not_move():
    """検収 N1・N3 の 2: 関係の初期化が実際に走る構成(mock 5,000 体・記憶+関係)の seed 1/2。

    交換可能で、設定の節の葉は全部一致する(10f の第 1 段の表では relations.init の 9 欄で落ちた)。
    """
    from shibuya import cli

    kw = dict(n_agents=5000, world_dir=str(WORLD), vocab_version="v3", memory="on", relations="on")
    d1 = _payload(cli.run(seed=1, **kw), "s1")
    d2 = _payload(cli.run(seed=2, **kw), "s2")
    assert d1["manifest"]["relations"]["init"]["groups"], "関係の初期化が空=試験にならない"
    assert MS.unlisted_in_mixed(d1["manifest"]) == [] and MS.unlisted_in_mixed(d2["manifest"]) == []
    r = sx.compare([d1, d2], ["s1", "s2"])
    assert r["exchangeable"] is True, r["diff_unexplained"]
    f1, f2 = sx.flatten(d1["manifest"]), sx.flatten(d2["manifest"])
    cfg = [k for k in set(f1) | set(f2) if MS.section_of(k) == MS.CONFIG]
    assert len(cfg) > 100
    # 10f 第 2 段(K21 (a)): 母集団の seed は省略すると seed と同じ値=seed とともに違う(許容の差)。ほかの設定の葉は全部一致
    assert (f1["population_seed"], f2["population_seed"]) == (1, 2) and r["population_seed_varies"] is True
    assert (f1["environment_seed"], f2["environment_seed"]) == (1, 2) and r["environment_seed_varies"] is True
    subs = ("population_seed", "environment_seed")
    assert [k for k in sorted(cfg) if f1.get(k) != f2.get(k) and k not in subs] == []
    assert sum(1 for k in set(f1) | set(f2) if MS.section_of(k) == MS.OBSERVED and f1.get(k) != f2.get(k)) > 0


def test_seed_exchangeability_sections_mode_on_synthetic_runs():
    """合成世界: 観測の欄だけ違う manifest は PASS・設定の欄を変えると FAIL・環境の欄の差は警告だけ。"""
    d1 = _payload(_small(seed=1), "s1")
    d2 = _payload(_small(seed=2), "s2")
    r = sx.compare([d1, d2], ["s1", "s2"])
    assert r["mode"] == "sections" and r["exchangeable"] is True, r["diff_unexplained"]
    d2o = json.loads(json.dumps(d2))
    d2o["manifest"]["llm_calls_total"] = 10 ** 9
    d2o["manifest"]["action_usage"] = {"x": 1}
    ro = sx.compare([d1, d2o], ["s1", "s2"])
    assert ro["exchangeable"] is True and "manifest.llm_calls_total" in ro["diff_observed"]
    for key, val in (("rng_scheme", "counter"), ("memory_n", 7), ("l4_scale", 3.0), ("attendance_rate", 0.5)):
        d2c = json.loads(json.dumps(d2))
        d2c["manifest"][key] = val
        rc = sx.compare([d1, d2c], ["s1", "s2"])
        assert rc["exchangeable"] is False and [u["key"] for u in rc["diff_unexplained"]] == [f"manifest.{key}"]
    for parent, key in (("state_hashes", "ledger_version"), ("energy", "rate"), ("intent", "max_ticks")):
        d2m = json.loads(json.dumps(d2))
        d2m["manifest"].setdefault(parent, {})[key] = "changed"
        assert sx.compare([d1, d2m], ["s1", "s2"])["exchangeable"] is False, (parent, key)
    d2e = json.loads(json.dumps(d2))
    d2e["manifest"]["env_id"] = "ffffffffffffffff"
    d2e["manifest"]["environment"]["platform"]["numpy"] = "0.0"
    re_ = sx.compare([d1, d2e], ["s1", "s2"])
    assert re_["exchangeable"] is True and re_["environment_warning"] is True
    assert {e["key"] for e in re_["diff_environment"]} == {"manifest.env_id", "manifest.environment.platform.numpy"}
    d2u = json.loads(json.dumps(d2))
    d2u["manifest"]["brand_new"] = 1
    ru = sx.compare([d1, d2u], ["s1", "s2"])
    assert ru["exchangeable"] is False and ru["unlisted"] == ["brand_new"]


# ================================================================= 小さな直し(§2-6)
def test_o75_split_flow_dir8_and_coherence_are_diag():
    """O75 の flow_dir8・coherence は src に読み手が無い → O95(diag)。描画が読む flow は O75(behavior)に残る。"""
    assert SL.LEDGER_VERSION == "state-ledger/10f"
    o75, o95 = SL.row("O75"), SL.row("O95")
    assert o75.behavior == SL.BEHAVIOR and "runner.crowd.flow" in o75.items
    assert not ({"runner.crowd.flow_dir8", "runner.crowd.coherence"} & set(o75.items))
    assert o95.behavior == SL.DIAG and set(o95.items) == {"runner.crowd.flow_dir8", "runner.crowd.coherence"}
    assert o95.restore == o75.restore
    beh = {p for _k, p in SL.behavior_items()}
    full = {p for _k, p in SL.full_items()}
    assert "runner.crowd.flow_dir8" not in beh and "runner.crowd.flow_dir8" in full
    hits = [p for p in (ROOT / "src" / "shibuya").rglob("*.py")
            if p.name not in ("crowd.py", "state_ledger.py")
            and ("flow_dir8" in p.read_text(encoding="utf-8") or ".coherence" in p.read_text(encoding="utf-8"))]
    assert hits == []
