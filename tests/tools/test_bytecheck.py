# -*- coding: utf-8 -*-
"""tools/bytecheck(byte-check の道具・11-09 §2 の 4)の試験。data も長いランも要らない単体だけ(CI の ci-1 で回る)。

- 構成の表: 19 構成が前の道具(``wave2_bytecheck.configs()``)と同じ並びと引数・記録 ``v30a.json`` の構成と同じ・
  組 parent4 と arms(腕 on の 7 変数=記録 ``v30a_arms.json`` の env)・比べる 25 欄が ``byte_check_10e`` と同じ・
  ``one`` の出す欄が ``byte_check_10e.cmd_one`` の欄を全部含む(AST で比べる)。
- 切替口の環境変数: src が読む ``SHIBUYA_`` の名はすべて記録の一覧(値を残す/名だけ残す)のどちらかに載る。
- compare の判定: 全部同じ=0・動いた欄=1・ランの誤り・構成の欠け・読んだ src の違い・開いたファイルの問題=2・
  古い記録(新しい欄が無い)も比べられる・JSON に絶対パスが無い・誤りの文の道筋を伏せる。
- 写す追跡ファイルの一覧: src の AST の走査で見つかる ``docs``・``tools``・``tests`` の道筋はすべて一覧(写す/写さない)に載る・
  リポの根を求めるファイルの集合が宣言と同じ・一覧の写すファイルが追跡されている・走査の型(鎖・tuple・f 文字列・
  joinpath・名を通した結合・引用の文の切り落とし)と負の対照(一覧に無い道筋を見つける)。
- git archive の写しと写しの木の不足の検査(data は無い=DATA_READS だけが足りない)。
- つなぎを外す関数はつなぎでない道筋(中身のあるディレクトリ・空のディレクトリ・ファイル)を消さない・つなぎだけを外し
  先の中身は残る。
- run は作業の置き場が空でない・呼び手の環境に SHIBUYA_ の変数がある・commit が無い、で何も作らずに 2 で止まる。
"""
from __future__ import annotations

import ast
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG_DIR = ROOT / "tools" / "bytecheck"
SRC = ROOT / "src"
OLD_10E = ROOT / "docs" / "bench" / "analysis" / "wallbounce-1012" / "10e" / "byte_check_10e.py"
OLD_WAVE2 = ROOT / "docs" / "bench" / "analysis" / "wave2-2026-09-30" / "wave2_bytecheck.py"
V30A = ROOT / "docs" / "bench" / "analysis" / "v3-2026-11" / "v30a" / "bytecheck"


_TOOLS = ROOT / "tools"
if str(_TOOLS) not in sys.path:  # 末尾に足す(tools の下の名が入れた包みを隠さないように)
    sys.path.append(str(_TOOLS))

from bytecheck import check as K  # noqa: E402
from bytecheck import cli as CLI  # noqa: E402
from bytecheck import configs as C  # noqa: E402
from bytecheck import tree as T  # noqa: E402


def _load_file(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def old10e():
    return _load_file(OLD_10E, "byte_check_10e_for_bytecheck_test")


@pytest.fixture(scope="module")
def wave2():
    return _load_file(OLD_WAVE2, "wave2_bytecheck_for_bytecheck_test")


# ================================================================== 構成の表
def test_all19_is_the_old_table(wave2):
    old = wave2.configs()
    new = C.configs()
    assert len(new) == 19
    assert list(new) == list(old)  # 並びも同じ
    assert new == old
    assert list(C.set_configs("all19")) == list(old)


def test_all19_matches_the_v30a_record():
    doc = json.loads((V30A / "v30a.json").read_text(encoding="utf-8"))
    assert list(doc["runs"]) == list(C.set_configs("all19"))


def test_parent4_and_arms_sets():
    assert C.set_configs("parent4") == ("w6_v3_default", "v3_mem_store", "v3_classical", "v3_classical_mem_rel")
    assert set(C.set_configs("parent4")) <= set(C.configs())
    arms = json.loads((V30A / "v30a_arms.json").read_text(encoding="utf-8"))
    assert list(C.set_configs("arms")) == list(arms["runs"])
    assert C.set_env("arms") == arms["env"]
    assert len(C.set_env("arms")) == 7
    assert C.set_env("all19") == {} and C.set_env("parent4") == {}
    with pytest.raises(KeyError):
        C.set_configs("no_such_set")


def test_compare_keys_are_the_25_of_10e(old10e):
    assert len(C.COMPARE_KEYS) == 25
    assert tuple(C.COMPARE_KEYS) == tuple(old10e.COMPARE_KEYS)


def _one_dict_keys(path: Path, func: str) -> set[str]:
    """``func`` の中の ``print(json.dumps({...}))`` の dict の鍵(AST)。"""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == func)
    for n in ast.walk(fn):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "dumps"
                and n.args and isinstance(n.args[0], ast.Dict)):
            return {k.value for k in n.args[0].keys if isinstance(k, ast.Constant)}
    raise AssertionError(f"{func} に json.dumps の dict が無い")


def test_one_emits_every_field_of_10e():
    old = _one_dict_keys(OLD_10E, "cmd_one")
    new = _one_dict_keys(PKG_DIR / "check.py", "cmd_one")
    assert old <= new, sorted(old - new)
    assert set(C.COMPARE_KEYS) <= new
    assert {"src_as_expected", "tree_reads", "foreign_reads"} <= new


def test_hash_functions_are_the_old_ones(old10e, wave2):
    obj = {"b": [1, 2], "a": {"y": 1, "x": "字"}}
    assert K._h_sorted(obj) == old10e._h(obj)
    assert K._h_plain(obj) == wave2._h(obj)
    assert K._h_sorted(obj) != K._h_plain(obj)  # 鍵の並べ方が違う=取り違えると欄が動く


# ================================================================== 切替口の環境変数
def test_switch_env_keeps_the_old_list_except_the_path_one(old10e):
    old = set(old10e.SWITCH_ENV)
    assert old - set(C.SWITCH_ENV) == {"SHIBUYA_CALENDAR_W20"}  # 値が道筋=名だけ残す側へ
    assert "SHIBUYA_CALENDAR_W20" in C.HIDDEN_ENV
    assert not set(C.SWITCH_ENV) & set(C.HIDDEN_ENV)


def test_every_shibuya_env_in_src_is_listed():
    names: set[str] = set()
    for p in SRC.rglob("*.py"):
        names |= set(re.findall(r"[\"'](SHIBUYA_[A-Z0-9_]+)[\"']", p.read_text(encoding="utf-8")))
    assert names, "src に SHIBUYA_ の名が 1 つも無い(走査が壊れた)"
    missing = names - set(C.SWITCH_ENV) - set(C.HIDDEN_ENV)
    assert not missing, f"configs.SWITCH_ENV(値を残す)か HIDDEN_ENV(名だけ)に足すこと: {sorted(missing)}"


def test_switch_env_records_values_and_hidden_names_only():
    env = {"SHIBUYA_CONTACT": "c1", "SHIBUYA_CALENDAR_W20": "C:/x/y.parquet", "SHIBUYA_BUDGET_MD": "/abs/b.md",
           "PATH": "x"}
    assert C.switch_env(env) == {"SHIBUYA_CONTACT": "c1"}
    assert C.hidden_env_names(env) == ["SHIBUYA_BUDGET_MD", "SHIBUYA_CALENDAR_W20"]


# ================================================================== compare
def _row(name: str, **over):
    r = {"config": name, "final": "f" * 16, "calls": 10, "blocks_rows": 3, "blocks_sha": "b", "calls_rows": 10,
         "calls_column_names": ["call_id"], "calls_columns_sha": {"call_id": "c"}, "action_usage_total": 5,
         "action_usage_sha": "a", "calls_by_condition": {"x": 1}, "salient_events": 0, "collapse": 0, "noticed": 0,
         "dispatches": 0, "arrived": 0, "mean_delay_min": 0.0, "meals": 1, "behavior_last": "h", "full_last": "g",
         "end_of_day": {}, "start_sim_datetime": "s", "replay_date": "r", "calendar_weekday": "w",
         "rng_scheme": "philox", "frozen_sources": {"a.parquet": "md5"}, "wall_s": 1.0, "src_as_expected": True}
    r.update(over)
    return r


def _side(rows, **over):
    d = {"label": "x", "set": "all19", "kw": {}, "src": "写し", "commit": "", "env": {}, "env_hidden": [],
         "tree_reads": [], "tree_reads_unlisted": [], "tree_reads_absent": [], "foreign_reads": [],
         "runs": {r["config"]: r for r in rows}}
    d.update(over)
    return d


def test_compare_same_is_0_and_wall_clock_is_not_compared():
    a = _side([_row("c1"), _row("c2")])
    b = _side([_row("c1", wall_s=99.0), _row("c2", run_wall_s=5.0, tape_bytes={"x": 1})])
    doc, code = K.compare_docs(a, b)
    assert code == 0
    assert doc["summary"]["all_same"] == 2 and doc["summary"]["result"] == "同じ"
    assert all(r["moved"] == {} and len(r["same"]) == 25 for r in doc["rows"].values())


def test_compare_moved_is_1_and_names_the_field():
    doc, code = K.compare_docs(_side([_row("c1"), _row("c2")]), _side([_row("c1"), _row("c2", final="0" * 16, calls=11)]))
    assert code == 1
    assert set(doc["rows"]["c2"]["moved"]) == {"final", "calls"}
    assert doc["rows"]["c2"]["moved"]["calls"] == {"a": 10, "b": 11}
    assert doc["rows"]["c2"]["calls_delta"] == 1
    assert doc["summary"]["final_same"] == 1


@pytest.mark.parametrize("b_over,rows_b", [
    ({}, [_row("c1", error="Traceback")]),  # ランの誤り
    ({}, []),  # 構成の欠け
    ({}, [_row("c1", src_as_expected=False)]),  # 違う src を読んだ
    ({"tree_reads_unlisted": ["docs/new.json"]}, [_row("c1")]),
    ({"tree_reads_absent": ["docs/design/rules-table.json"]}, [_row("c1")]),
    ({"foreign_reads": ["docs/design/rules-table.json"]}, [_row("c1")]),
])
def test_compare_errors_are_2_even_when_values_match(b_over, rows_b):
    _, code = K.compare_docs(_side([_row("c1")]), _side(rows_b, **b_over))
    assert code == 2


def test_compare_moved_and_error_is_2():
    _, code = K.compare_docs(_side([_row("c1"), _row("c2")]), _side([_row("c1", final="0"), _row("c2", error="x")]))
    assert code == 2


def test_compare_reads_old_records_without_new_fields():
    a = json.loads((V30A / "base_2160272.json").read_text(encoding="utf-8"))
    b = json.loads((V30A / "v30a.json").read_text(encoding="utf-8"))
    doc, code = K.compare_docs(a, b)
    assert code == 0 and doc["summary"]["all_same"] == 19


def test_compare_json_has_no_absolute_path(tmp_path: Path):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text(json.dumps(_side([_row("c1")])), encoding="utf-8")
    b.write_text(json.dumps(_side([_row("c1", final="1" * 16)])), encoding="utf-8")
    out = tmp_path / "cmp.json"
    assert K.compare(a=a, b=b, out=out, note="n") == 1
    text = out.read_text(encoding="utf-8")
    for p in (tmp_path, ROOT, Path.home()):
        for v in {str(p), str(p).replace("\\", "/"), str(p).replace("\\", "\\\\")}:
            assert v not in text
    assert not re.search(r"[A-Za-z]:[\\/]", text)


def test_mask_paths_hides_repo_tree_home_and_python(tmp_path: Path):
    tree = tmp_path / "tree"
    raw = (f'File "{tree / "src" / "shibuya" / "x.py"}", line 3\n'
           f'File "{ROOT / "tools" / "bytecheck" / "check.py"}"\n'
           f'{str(Path.home()).replace(os.sep, "/")}/other\n{sys.prefix}{os.sep}Lib')
    masked = K.mask_paths(raw, K._mask_roots((tree, "<tree>")))
    assert "<tree>" in masked and "<repo>" in masked and "<python>" in masked
    for p in (tree, ROOT, Path.home(), Path(sys.prefix)):
        assert str(p) not in masked and str(p).replace("\\", "/") not in masked


# ================================================================== 写す追跡ファイルの一覧(src の走査と照らす)
@pytest.fixture(scope="module")
def refs():
    return T.scan_path_refs(SRC)


def test_every_tracked_path_in_src_is_classified(refs):
    bad = T.unclassified_refs(refs)
    assert not bad, ("src に現れた docs・tools・tests の道筋が tree.TRACKED_READS(写す)にも NOT_COPIED(写さない・理由つき)"
                     f"にも無い。エンジンが開くなら TRACKED_READS へ: {bad}")


def test_listed_files_are_really_referenced_in_src(refs):
    found = T.tracked_refs(refs)
    assert set(T.TRACKED_READS) <= found, sorted(set(T.TRACKED_READS) - found)
    assert set(T.NOT_COPIED) <= found, sorted(set(T.NOT_COPIED) - found)  # 古い行を残さない
    data_found = {r.path for r in refs if r.path.startswith("data/")}
    assert set(T.DATA_READS) <= data_found, sorted(set(T.DATA_READS) - data_found)
    assert not set(T.TRACKED_READS) & set(T.NOT_COPIED)


def test_engine_anchor_files_are_in_the_list(refs):
    # 10e の docstring の決め方(RELPATH と錨の grep)で見つかるものが写す一覧に入る
    must = {"docs/design/rules-table.json", "docs/design/bridging-ledger.json", "docs/design/v2-budget-declaration.md",
            "docs/design/v2-perception-contract.md", "docs/design/v2-pattern-ledger.md",
            "docs/bench/anchors/hunger_energy_build_anchors_v0.json",
            "docs/bench/anchors/hunger_energy_validation_anchors_v0.json",
            "docs/bench/anchors/ssb2021_activity_prior_v0.json"}
    assert must <= set(T.TRACKED_READS)
    engine_anchors = {r.path for r in refs if r.path.endswith("_anchors_v0.json") and not r.file.startswith("shibuya/build/")}
    assert engine_anchors <= set(T.TRACKED_READS)


def test_head_tree_files_cover_the_old_list(old10e):
    assert set(old10e.HEAD_TREE_FILES) <= set(T.HEAD_TREE_FILES)


def test_root_reader_files_are_declared():
    found = T.scan_root_anchors(SRC)
    assert set(found) == set(T.ROOT_READERS), (
        f"リポの根を求めるファイルが変わった。tree.ROOT_READERS に何を読むかを書き、読むものを TRACKED_READS か "
        f"NOT_COPIED に載せること: 足りない {sorted(set(found) - set(T.ROOT_READERS))}・古い "
        f"{sorted(set(T.ROOT_READERS) - set(found))}")


def test_listed_tracked_files_exist_and_are_tracked():
    for rel in T.TRACKED_READS:
        assert (ROOT / rel).is_file(), rel
    r = subprocess.run(["git", "-C", str(ROOT), "ls-files", "--", *T.TRACKED_READS], capture_output=True, text=True)
    if r.returncode != 0:
        pytest.skip("git が無い")
    assert set(r.stdout.split()) == set(T.TRACKED_READS)


def test_archive_paths():
    p = T.archive_paths(["docs/x.json", "src"])
    assert p[0] == "src" and p.count("src") == 1
    assert set(T.TRACKED_READS) <= set(p) and "docs/x.json" in p
    assert not any(x.startswith("data") for x in p)  # data は写さない(つなぎ)


SYNTH = '''
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
_DIR = ROOT / "docs" / "bench" / "anchors"
NAME = "foo_v0.json"
SEG = ("..", "docs", "x", "y.json")
A = _DIR / "a_v0.json"
B = ROOT.joinpath(*("docs", "j"), NAME)
C = f"docs/f/{NAME}"
D = "docs/design/cited.md §2-3・ほか"
E = "tools/t.py"
F = "data/d.csv"
G = "docsify/not_a_path"
H = Path("tests", "fixtures", "z.csv")
def f(root):
    return root / "docs" / "deep" / NAME
'''


def test_scanner_patterns(tmp_path: Path):
    pkg = tmp_path / "src" / "shibuya" / "engine"
    pkg.mkdir(parents=True)
    (pkg / "m.py").write_text(SYNTH, encoding="utf-8")
    got = {r.path for r in T.scan_path_refs(tmp_path / "src")}
    assert {"docs/bench/anchors", "docs/x/y.json", "docs/bench/anchors/a_v0.json", "docs/j/foo_v0.json",
            "docs/f/{}", "docs/design/cited.md", "tools/t.py", "data/d.csv", "tests/fixtures/z.csv",
            "docs/deep/foo_v0.json"} <= got
    assert not any(p.startswith("docsify") for p in got)
    anchors = T.scan_root_anchors(tmp_path / "src")
    assert list(anchors) == ["shibuya/engine/m.py"]


def test_scanner_negative_control_finds_an_unlisted_read(tmp_path: Path):
    pkg = tmp_path / "src" / "shibuya"
    pkg.mkdir(parents=True)
    (pkg / "x.py").write_text('P = "docs/design/rules-table.json"\nQ = "docs/design/new-table.json"\n', encoding="utf-8")
    bad = T.unclassified_refs(T.scan_path_refs(tmp_path / "src"))
    assert list(bad) == ["docs/design/new-table.json"]
    # parents[k] が根に届かないものは数えない・届くものは数える
    (pkg / "y.py").write_text("from pathlib import Path\nA = Path(__file__).parents[1]\n", encoding="utf-8")
    (pkg / "z.py").write_text("from pathlib import Path\nA = Path(__file__).parents[2]\n", encoding="utf-8")
    assert set(T.scan_root_anchors(tmp_path / "src")) == {"shibuya/z.py"}


# ================================================================== 写しの木
def test_git_archive_copy_and_tree_missing(tmp_path: Path):
    if subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True).returncode != 0:
        pytest.skip("git が無い")
    commit = T.resolve_commit(ROOT, "HEAD")
    paths = [*T.TRACKED_READS, "src/shibuya/__init__.py"]
    have, lack = T.paths_in_commit(ROOT, commit, [*paths, "docs/no/such/file.json"])
    assert lack == ["docs/no/such/file.json"] and have == paths
    dest = tmp_path / "tree"
    T.git_archive(ROOT, commit, have, dest)
    for rel in paths:
        assert (dest / rel).is_file(), rel
    assert T.tree_missing(dest) == list(T.DATA_READS)  # data のつなぎが無い=data だけ足りない
    assert not (dest / "docs" / "bench" / "anchors" / "presence_anchors_v0.json").exists()  # 錨は一覧の分だけ
    with pytest.raises(ValueError):
        T.resolve_commit(ROOT, "no-such-rev-zzz")


def test_classify_reads(tmp_path: Path):
    (tmp_path / "docs" / "design").mkdir(parents=True)
    (tmp_path / "docs" / "design" / "rules-table.json").write_text("{}", encoding="utf-8")
    got = T.classify_reads(["docs/design/rules-table.json", "docs/design/bridging-ledger.json", "docs/zz.md"], tmp_path)
    assert got == {"unlisted": ["docs/zz.md"], "absent": ["docs/design/bridging-ledger.json", "docs/zz.md"]}


def test_opened_outside(tmp_path: Path):
    root = tmp_path / "r"
    tool = root / "tools" / "bytecheck"
    opened = [str(root / "src" / "shibuya" / "a.py"), str(root / "data" / "w" / "x.parquet"),
              str(root / "docs" / "design" / "rules-table.json"), str(tool / "check.py"),
              str(tmp_path / "elsewhere.txt"), str(root / "tests" / "t.json"), str(root)]
    got = K.opened_outside(opened, root, skip_tops=("src", "data"), skip_dirs=[tool])
    assert got == ["docs/design/rules-table.json", "tests/t.json"]


def test_audit_hook_records_opens():
    before = set(K._OPENED)
    K._audit("open", ("some/relative/file.txt", "r", 0))
    K._audit("open", (3, "r", 0))  # fd は記録しない
    K._audit("os.listdir", ("x",))
    assert set(K._OPENED) - before == {"some/relative/file.txt"}
    K._OPENED.discard("some/relative/file.txt")


# ================================================================== つなぎを外す
def test_remove_link_refuses_a_real_directory_and_keeps_its_content(tmp_path: Path):
    d = tmp_path / "data"
    d.mkdir()
    (d / "keep.txt").write_text("中身", encoding="utf-8")
    with pytest.raises(T.NotALinkError):
        T.remove_link(d)
    assert (d / "keep.txt").read_text(encoding="utf-8") == "中身"
    e = tmp_path / "empty"
    e.mkdir()
    with pytest.raises(T.NotALinkError):
        T.remove_link(e)
    assert e.is_dir()  # 空のディレクトリも消さない
    f = tmp_path / "file.txt"
    f.write_text("x", encoding="utf-8")
    with pytest.raises(T.NotALinkError):
        T.remove_link(f)
    assert f.is_file()
    with pytest.raises(T.NotALinkError):
        T.remove_link(tmp_path / "no_such")


def test_place_and_remove_link_keeps_the_target(tmp_path: Path):
    target = tmp_path / "real_data"
    (target / "sub").mkdir(parents=True)
    (target / "sub" / "keep.txt").write_text("中身", encoding="utf-8")
    tree = tmp_path / "tree"
    tree.mkdir()
    try:
        link = T.place_data_link(tree, target)
    except OSError as e:  # 記号のリンクを作れない環境(権限)
        pytest.skip(f"つなぎを作れない: {e}")
    assert T.is_link(link)
    assert (link / "sub" / "keep.txt").read_text(encoding="utf-8") == "中身"
    with pytest.raises(FileExistsError):
        T.place_data_link(tree, target)
    T.remove_link(link)
    assert not link.exists() and not T.is_link(link)
    assert (target / "sub" / "keep.txt").read_text(encoding="utf-8") == "中身"  # 先の中身は残る
    with pytest.raises(FileNotFoundError):
        T.place_data_link(tree, tmp_path / "no_such_target")


# ================================================================== run と side の手前の止まり方
@pytest.fixture()
def clean_env(monkeypatch):
    for k in list(os.environ):
        if k.startswith("SHIBUYA_"):
            monkeypatch.delenv(k)


def test_run_refuses_a_non_empty_work_dir(tmp_path: Path, clean_env):
    work = tmp_path / "w"
    work.mkdir()
    (work / "left.txt").write_text("前のラン", encoding="utf-8")
    code = K.run(work=work, out_dir=tmp_path / "out")
    assert code == 2
    assert sorted(p.name for p in work.iterdir()) == ["left.txt"]  # 何も作らず・何も消さない
    assert not (tmp_path / "out").exists()


def test_run_refuses_stray_env_and_bad_commit(tmp_path: Path, clean_env, monkeypatch):
    monkeypatch.setenv("SHIBUYA_CONTACT", "c1")
    assert K.run(work=tmp_path / "w1", out_dir=tmp_path / "o1") == 2
    assert not (tmp_path / "w1").exists()
    monkeypatch.delenv("SHIBUYA_CONTACT")
    monkeypatch.setenv("SHIBUYA_FLEET_API_KEY", "k")  # 鍵は mock のランに効かない=止めない側
    assert K.stray_env(dict(os.environ)) == []
    assert K.run(work=tmp_path / "w2", out_dir=tmp_path / "o2", base="no-such-rev-zzz") == 2
    assert not (tmp_path / "w2").exists()
    assert K.run(work=tmp_path / "w3", out_dir=tmp_path / "o3", only="no_such_config") == 2


def test_side_stops_on_an_incomplete_tree_without_running(tmp_path: Path):
    (tmp_path / "src" / "shibuya").mkdir(parents=True)
    code = K.side(label="x", scratch=tmp_path / "s", out=tmp_path / "x.json", src=tmp_path / "src")
    assert code == 2
    assert not (tmp_path / "x.json").exists() and not (tmp_path / "s").exists()


def test_cli_exit_codes(tmp_path: Path):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text(json.dumps(_side([_row("c1")])), encoding="utf-8")
    b.write_text(json.dumps(_side([_row("c1")])), encoding="utf-8")
    assert CLI.main(["compare", "--a", str(a), "--b", str(b), "--out", str(tmp_path / "c.json")]) == 0
    b.write_text(json.dumps(_side([_row("c1", meals=2)])), encoding="utf-8")
    assert CLI.main(["compare", "--a", str(a), "--b", str(b), "--out", str(tmp_path / "c.json")]) == 1
    assert CLI.main(["compare", "--a", str(a), "--b", str(tmp_path / "none.json"), "--out", str(tmp_path / "c.json")]) == 2
    with pytest.raises(SystemExit) as e:
        CLI.main(["run", "--work", "w", "--out-dir", "o", "--set", "no_such_set"])
    assert e.value.code == 2


def test_package_metadata_reads_are_not_foreign():
    """第346 親: 本体から回したときの editable の名札の読みは「道具のリポを開いた」に数えない。"""
    got = K.drop_package_metadata([
        "src/shibuya_sim.egg-info/METADATA",
        "src/shibuya_sim.egg-info/entry_points.txt",
        "x/foo-1.0.dist-info/RECORD",
        "src/shibuya/engine/run.py",
        "docs/design/rules-table.json",
    ])
    assert got == ["src/shibuya/engine/run.py", "docs/design/rules-table.json"]

