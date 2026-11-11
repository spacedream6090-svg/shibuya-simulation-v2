# -*- coding: utf-8 -*-
"""tools/bytecheck(byte-check の道具・11-09 §2 の 4)の試験。data も長いランも要らない(CI の ci-1 で回る)。

- 構成の表: 19 構成が前の道具(``wave2_bytecheck.configs()``)と同じ並びと引数・記録 ``v30a.json`` の構成と同じ・
  組 parent4 と arms(腕 on の 7 変数=記録 ``v30a_arms.json`` の env)・比べる 25 欄が ``byte_check_10e`` と同じ・
  ``one`` の出す欄が ``byte_check_10e.cmd_one`` の欄と新しい欄(``fields.NEW_KEYS``)を全部含む(AST で比べる)。
- 切替口の環境変数: src が読む ``SHIBUYA_`` の名はすべて記録の一覧(値を残す/名だけ残す)のどちらかに載る。
- compare の判定: 全部同じ=0・動いた欄=1・ランの誤り・構成の欠け・構成が 0・25 欄の欠け・条件の違い・読んだ src の違い・
  開いたファイルの問題=2・古い記録(新しい欄が無い)は「比べていない」と注を付ける(strict なら 2)・正準の JSON で比べる
  (NaN は同じ・0 と 0.0 は違う)・JSON に絶対パスが無い・誤りの文の道筋を伏せる。
- 第346 の検収 H1 の欄(``fields``): 比べない欄の一覧の固定・欄ごとのハッシュ・スキーマ・テープのファイル・checkpoint。
- 偽のエンジン(一時の木の ``shibuya`` パッケージ=data も実のランも要らない)で ``one``・``side`` を本当に回す: 環境の欄と
  壁時計の欄だけが違う 2 回は 0・テープの型(int64)・スキーマの見出し・manifest の欄(v5x)・run_meta の欄・途中の
  checkpoint・テープのファイルの増え・final が動くと 1 で、動いた欄の名が出る・読んだファイルの仕分け(一覧に無い・
  道具のリポ・写しの木の上の階・外)と ``--extra-path``・``src_as_expected``・``PYTHONHASHSEED``・読んだ src の digest。
- run の配線(side を差し替える): 基準の側に写しの src・比べる側に渡した src・同じ印(nonce)と ``--extra-path`` を渡す・
  side の誤り・前のランの JSON・digest の食い違いで 2・作業の置き場が git の作業木の中なら断る。
- 写す追跡ファイルの一覧: src の AST の走査で見つかる ``docs``・``tools``・``tests`` の道筋はすべて一覧(写す/写さない)に載る・
  リポの根を求めるファイルの集合が宣言と同じ・一覧の写すファイルが追跡されている・走査の型(鎖・tuple・list・f 文字列・
  joinpath・os.path.join・``"/".join``・``+`` の結合・``%`` の書式・``\\``・``./``・名を通した結合・引用の文の切り落とし)と
  負の対照(一覧に無い道筋を見つける)。
- git archive の写しと写しの木の不足の検査(data は無い=DATA_READS だけが足りない)。
- つなぎを外す関数はつなぎでない道筋(中身のあるディレクトリ・空のディレクトリ・ファイル)を消さない・つなぎだけを外し
  先の中身は残る・cmd を通さない。
- run は作業の置き場が空でない・呼び手の環境に SHIBUYA_ の変数がある・commit が無い・``--kw`` が JSON の辞書でない、で
  何も作らずに 2 で止まる。
"""
from __future__ import annotations

import ast
import contextlib
import dataclasses
import hashlib
import importlib.util
import json
import math
import os
import re
import subprocess
import sys
import types
from pathlib import Path
from types import SimpleNamespace

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
from bytecheck import fields as F  # noqa: E402
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


@contextlib.contextmanager
def _env(**values: str):
    """環境変数を一時に置く(空の値は外す)。"""
    keep = {k: os.environ.get(k) for k in values}
    try:
        for k, v in values.items():
            if v:
                os.environ[k] = v
            else:
                os.environ.pop(k, None)
        yield
    finally:
        for k, v in keep.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


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


def test_one_emits_every_field_of_10e_and_the_new_ones():
    old = _one_dict_keys(OLD_10E, "cmd_one")
    new = _one_dict_keys(PKG_DIR / "check.py", "cmd_one")
    assert old <= new, sorted(old - new)
    assert set(C.COMPARE_KEYS) <= new
    assert set(F.NEW_KEYS) <= new, sorted(set(F.NEW_KEYS) - new)
    assert {"src_as_expected", "tree_reads", "foreign_reads", "outside_reads", "outside_above_tree", "src_files",
            "src_loaded_outside", "manifest_scalars", "run_meta_scalars"} <= new


def test_hash_functions_are_the_old_ones(old10e, wave2):
    obj = {"b": [1, 2], "a": {"y": 1, "x": "字"}}
    assert K._h_sorted(obj) == old10e._h(obj)
    assert K._h_plain(obj) == wave2._h(obj)
    assert K._h_sorted(obj) != K._h_plain(obj)  # 鍵の並べ方が違う=取り違えると欄が動く


# ================================================================== 切替口の環境変数
def test_switch_env_keeps_the_old_list_except_the_path_one_and_the_removed(old10e):
    old = set(old10e.SWITCH_ENV)
    # 値が道筋=名だけ残す側へ・〔第346〕消した切替口=REMOVED_ENV へ
    assert old - set(C.SWITCH_ENV) == {"SHIBUYA_CALENDAR_W20"} | (old & set(C.REMOVED_ENV))
    assert "SHIBUYA_CALENDAR_W20" in C.HIDDEN_ENV
    assert not set(C.SWITCH_ENV) & set(C.HIDDEN_ENV)
    assert not set(C.REMOVED_ENV) & (set(C.SWITCH_ENV) | set(C.HIDDEN_ENV))


def test_removed_env_names_still_appear_in_src_as_the_stop():
    """〔第346〕消した切替口の名は src に残る(与えると読み込みで止める文)=SWITCH_ENV に戻さない。"""
    text = "\n".join(p.read_text(encoding="utf-8") for p in SRC.rglob("*.py"))
    for name in C.REMOVED_ENV:
        assert f'"{name}"' in text, name
    assert C.switch_env({name: "x" for name in C.REMOVED_ENV}) == {}
    assert C.hidden_env_names({name: "x" for name in C.REMOVED_ENV}) == sorted(C.REMOVED_ENV)


def test_every_shibuya_env_in_src_is_listed():
    names: set[str] = set()
    for p in SRC.rglob("*.py"):
        names |= set(re.findall(r"[\"'](SHIBUYA_[A-Z0-9_]+)[\"']", p.read_text(encoding="utf-8")))
    assert names, "src に SHIBUYA_ の名が 1 つも無い(走査が壊れた)"
    missing = names - set(C.SWITCH_ENV) - set(C.HIDDEN_ENV) - set(C.REMOVED_ENV)
    assert not missing, f"configs.SWITCH_ENV(値を残す)か HIDDEN_ENV(名だけ)に足すこと: {sorted(missing)}"


def test_switch_env_records_values_and_hidden_names_only():
    env = {"SHIBUYA_CONTACT": "c1", "SHIBUYA_CALENDAR_W20": "C:/x/y.parquet", "SHIBUYA_BUDGET_MD": "/abs/b.md",
           "PATH": "x"}
    assert C.switch_env(env) == {"SHIBUYA_CONTACT": "c1"}
    assert C.hidden_env_names(env) == ["SHIBUYA_BUDGET_MD", "SHIBUYA_CALENDAR_W20"]


# ================================================================== 第346 検収 H1 の欄(fields)
def test_new_keys_and_skip_lists_are_pinned():
    """比べるものと比べない欄の一覧を固定する(足す・外すは README とこの試験を一緒に直す)。"""
    assert F.NEW_KEYS == ("tape_files", "tape_sha256", "calls_schema", "blocks_schema",
                          "manifest_sha", "manifest_fields_sha", "manifest_skipped",
                          "run_meta_sha", "run_meta_fields_sha", "run_meta_skipped",
                          "checkpoints", "n_checkpoints")
    assert not set(F.NEW_KEYS) & set(C.COMPARE_KEYS)
    assert set(F.MANIFEST_SKIP) == {"env_id", "environment.code", "environment.env_id", "resume.read_seconds",
                                    "resume.restore_seconds"}
    assert set(F.RUN_META_SKIP) == {"env_id", "environment.code", "environment.env_id"}
    assert F.SKIP_SUFFIXES == ("_nondeterministic",)
    assert set(F.SUFFIX_EXEMPT) == {"manifest_sections"} and all(F.SUFFIX_EXEMPT.values())
    assert F.TAPE_FIELDWISE == ("run_meta.json",)
    assert all(F.MANIFEST_SKIP.values()) and all(F.RUN_META_SKIP.values())  # 理由が書いてある
    assert K.TREE_SKIP_TOPS == ("src", "data", ".git", ".venv", "venv")
    assert K.FOREIGN_SKIP_TOPS == ("data", ".git", ".venv", "venv")
    assert K.ABOVE_TOPS == ("docs", "tools", "tests", "src", "data")
    assert K.CONDITION_KEYS == ("set", "kw", "agents", "seed", "world", "env", "env_hidden", "drop_behavior_item",
                                "multiset_items", "pythonhashseed")
    assert K.PYTHONHASHSEED == "0"


def test_readme_names_every_compared_and_skipped_field():
    text = (PKG_DIR / "README.md").read_text(encoding="utf-8")
    for k in (*C.COMPARE_KEYS, *F.NEW_KEYS, *F.MANIFEST_SKIP, *F.RUN_META_SKIP, *F.SKIP_SUFFIXES, *F.SUFFIX_EXEMPT):
        assert f"`{k}`" in text, k
    assert "1 バイトも動かない" not in text  # 比べるものの一覧と合わない言い方を残さない


MAN = {"env_id": "e1", "environment": {"code": {"git_commit": "abc", "git_dirty": False}, "env_id": "e1",
                                       "platform": {"python": "3.12"}},
       "resume": {"read_seconds": 0.5, "restore_seconds": 0.0, "finished": True},
       "relations": {"wall_seconds_nondeterministic": {"x": 1.0}, "init": {"init_seconds_nondeterministic": 2.0, "n": 3}},
       "daily": [{"step_scope": {"detect_seconds_nondeterministic": 0.1, "marked_share": 0.5}}],
       "manifest_sections": {"paths": {"relations.wall_seconds_nondeterministic": "observed"}},
       "synonym_table_version": "undefined-synonyms-v5", "l4_scale": 0.0, "process_ids": ["a", "b"]}


def test_strip_skipped_removes_only_the_named_fields():
    stripped, gone = F.strip_skipped(MAN, F.MANIFEST_SKIP)
    assert gone == sorted(["env_id", "environment.code", "environment.env_id", "resume.read_seconds",
                           "resume.restore_seconds", "relations.wall_seconds_nondeterministic",
                           "relations.init.init_seconds_nondeterministic",
                           "daily[0].step_scope.detect_seconds_nondeterministic"])
    assert stripped["environment"] == {"platform": {"python": "3.12"}}  # 機械と依存の版は比べる
    assert stripped["resume"] == {"finished": True}
    assert stripped["relations"] == {"init": {"n": 3}}
    assert stripped["daily"] == [{"step_scope": {"marked_share": 0.5}}]
    assert stripped["manifest_sections"] == MAN["manifest_sections"]  # 節の表の行は壁時計でない=比べる
    assert MAN["resume"]["read_seconds"] == 0.5  # 元は変えない


def _changed(path: tuple, value):
    m = json.loads(json.dumps(MAN))
    d = m
    for p in path[:-1]:
        d = d[p]
    d[path[-1]] = value
    return m


def test_field_digest_ignores_only_the_skipped_fields():
    base = F.field_digest(MAN, F.MANIFEST_SKIP)
    for path, value in ((("env_id",), "e2"), (("environment", "code", "git_commit"), "def"),
                        (("resume", "read_seconds"), 9.9), (("relations", "wall_seconds_nondeterministic"), {"x": 7.0})):
        assert F.field_digest(_changed(path, value), F.MANIFEST_SKIP)["sha"] == base["sha"], path
    for path, value, field in ((("synonym_table_version",), "undefined-synonyms-v5x", "synonym_table_version"),
                               (("l4_scale",), 0, "l4_scale"),  # 0.0 → 0(型の違い)
                               (("environment", "platform", "python"), "3.13", "environment"),
                               (("resume", "finished"), False, "resume"),
                               (("relations", "init", "n"), 4, "relations")):
        got = F.field_digest(_changed(path, value), F.MANIFEST_SKIP)
        assert got["sha"] != base["sha"], path
        assert [k for k in got["fields"] if got["fields"][k] != base["fields"][k]] == [field], path
    assert base["scalars"]["synonym_table_version"] == "undefined-synonyms-v5"
    assert "relations" not in base["scalars"]  # 辞書は値を出さない(ハッシュだけ)
    extra = dict(MAN, new_field=1)
    got = F.field_digest(extra, F.MANIFEST_SKIP)
    assert set(got["fields"]) - set(base["fields"]) == {"new_field"} and got["sha"] != base["sha"]


def test_same_value_is_canonical_json():
    assert F.same_value({"a": 1, "b": 2}, {"b": 2, "a": 1})  # 辞書の並びは見ない
    assert F.same_value(float("nan"), float("nan"))  # 検収 L6
    assert F.same_value({"x": [float("nan")]}, json.loads(json.dumps({"x": [float("nan")]})))
    assert not F.same_value(0, 0.0) and not F.same_value(True, 1)  # 型の違いは違い
    assert not F.same_value([1, 2], [2, 1])


def test_arrow_schema_sees_types_nullability_and_metadata():
    pa = pytest.importorskip("pyarrow")
    t32 = pa.schema([pa.field("tokens", pa.int32(), nullable=False)])
    t64 = pa.schema([pa.field("tokens", pa.int64(), nullable=False)])
    tnull = pa.schema([pa.field("tokens", pa.int32(), nullable=True)])
    tmeta = t32.with_metadata({"shibuya.tape.schema": "shibuya.tape/5"})
    got = {k: F.arrow_schema(s) for k, s in (("32", t32), ("64", t64), ("null", tnull), ("meta", tmeta))}
    assert got["32"] == {"fields": ["tokens:int32:not null"], "metadata": {}}
    assert len({json.dumps(v, sort_keys=True) for v in got.values()}) == 4
    assert F.arrow_schema(t32.with_metadata({b"ARROW:schema": b"zz"})) == got["32"]  # 塊は除く(バイトは sha が見る)


def test_tape_files_and_sha256(tmp_path: Path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "calls.parquet").write_bytes(b"c")
    (tmp_path / "blocks.parquet").write_bytes(b"b")
    (tmp_path / "run_meta.json").write_text("{}", encoding="utf-8")
    (tmp_path / "sub" / "x.bin").write_bytes(b"x")
    assert F.tape_files(tmp_path) == ["blocks.parquet", "calls.parquet", "run_meta.json", "sub/x.bin"]
    sha = F.tape_sha256(tmp_path)
    assert sha == {"blocks.parquet": hashlib.sha256(b"b").hexdigest(), "calls.parquet": hashlib.sha256(b"c").hexdigest(),
                   "sub/x.bin": hashlib.sha256(b"x").hexdigest()}  # run_meta.json は欄ごとに比べる


@dataclasses.dataclass(frozen=True)
class _Point:
    step: int
    behavior_hash: str
    full_hash: str = ""


def test_checkpoint_rows_keep_every_field():
    got = F.checkpoint_rows([_Point(0, "h0", "f0"), SimpleNamespace(step=1, behavior_hash="h1")])
    assert got == [{"step": 0, "behavior_hash": "h0", "full_hash": "f0"}, {"step": 1, "behavior_hash": "h1"}]


def test_diff_and_named_moves():
    assert F.diff({"a": 1, "b": 2}, {"a": 1, "b": 3, "c": 4}) == {"keys": {"b": {"a": 2, "b": 3},
                                                                           "c": {"a": "(無い)", "b": 4}}}
    assert F.diff([1, 2], [1, 3, 4]) == {"len": [2, 3], "items": {"1": {"a": 2, "b": 3}, "2": {"a": "(無い)", "b": 4}}}
    assert F.diff("x", "y") == {"a": "x", "b": "y"}
    ra = {"manifest_fields_sha": {"s": "1", "d": "x"}, "manifest_scalars": {"s": "v5"}}
    rb = {"manifest_fields_sha": {"s": "2", "d": "y", "n": "z"}, "manifest_scalars": {"s": "v5x"}}
    assert F.named_moves(ra, rb, "manifest") == {"s": {"a": "v5", "b": "v5x"}, "d": {"a": "x", "b": "y"},
                                                 "n": {"a": "(無い)", "b": "z"}}


# ================================================================== compare
def _row(name: str, **over):
    r = {"config": name, "final": "f" * 16, "calls": 10, "blocks_rows": 3, "blocks_sha": "b", "calls_rows": 10,
         "calls_column_names": ["call_id"], "calls_columns_sha": {"call_id": "c"}, "action_usage_total": 5,
         "action_usage_sha": "a", "calls_by_condition": {"x": 1}, "salient_events": 0, "collapse": 0, "noticed": 0,
         "dispatches": 0, "arrived": 0, "mean_delay_min": 0.0, "meals": 1, "behavior_last": "h", "full_last": "g",
         "end_of_day": {}, "start_sim_datetime": "s", "replay_date": "r", "calendar_weekday": "w",
         "rng_scheme": "philox", "frozen_sources": {"a.parquet": "md5"}, "wall_s": 1.0, "src_as_expected": True,
         # 新しい欄(fields.NEW_KEYS)
         "tape_files": ["blocks.parquet", "calls.parquet", "run_meta.json"],
         "tape_sha256": {"blocks.parquet": "1" * 64, "calls.parquet": "2" * 64},
         "calls_schema": {"fields": ["call_id:string:not null"], "metadata": {"shibuya.tape.schema": "shibuya.tape/4"}},
         "blocks_schema": {"fields": ["tokens:int32:not null"], "metadata": {}},
         "manifest_sha": "m" * 64, "manifest_fields_sha": {"synonym_table_version": "s1", "daily": "d1"},
         "manifest_scalars": {"synonym_table_version": "undefined-synonyms-v5"}, "manifest_skipped": ["env_id"],
         "run_meta_sha": "r" * 64, "run_meta_fields_sha": {"rng_layout": "l1"}, "run_meta_scalars": {"rng_layout": "10e"},
         "run_meta_skipped": ["env_id"], "checkpoints": [{"step": 0, "behavior_hash": "h0"}, {"step": 1, "behavior_hash": "h"}],
         "n_checkpoints": 2}
    r.update(over)
    return r


def _side(rows, **over):
    d = {"label": "x", "set": "all19", "kw": {}, "src": "写し", "commit": "", "env": {}, "env_hidden": [],
         "agents": 5000, "seed": 1, "world": "data/world/v2", "pythonhashseed": "0", "drop_behavior_item": "",
         "multiset_items": "", "tree_reads": [], "tree_reads_unlisted": [], "tree_reads_absent": [], "foreign_reads": [],
         "runs": {r["config"]: r for r in rows}}
    d.update(over)
    return d


def test_compare_same_is_0_and_wall_clock_is_not_compared():
    a = _side([_row("c1"), _row("c2")])
    b = _side([_row("c1", wall_s=99.0), _row("c2", run_wall_s=5.0, tape_bytes={"x": 1}, checkpoint_s=[9.0])])
    doc, code = K.compare_docs(a, b)
    assert code == 0
    assert doc["summary"]["all_same"] == 2 and doc["summary"]["result"] == "同じ"
    assert all(r["moved"] == {} and len(r["same"]) == 25 + len(F.NEW_KEYS) for r in doc["rows"].values())


def test_compare_moved_is_1_and_names_the_field():
    doc, code = K.compare_docs(_side([_row("c1"), _row("c2")]), _side([_row("c1"), _row("c2", final="0" * 16, calls=11)]))
    assert code == 1
    assert set(doc["rows"]["c2"]["moved"]) == {"final", "calls"}
    assert doc["rows"]["c2"]["moved"]["calls"] == {"a": 10, "b": 11}
    assert doc["rows"]["c2"]["calls_delta"] == 1
    assert doc["summary"]["final_same"] == 1


#: 新しい欄ごとの「動いた」値(_row の値からの変え方)。
NEW_KEY_CHANGES = {
    "tape_files": ["blocks.parquet", "calls.parquet", "extra.bin", "run_meta.json"],
    "tape_sha256": {"blocks.parquet": "3" * 64, "calls.parquet": "2" * 64},
    "calls_schema": {"fields": ["call_id:large_string:not null"], "metadata": {"shibuya.tape.schema": "shibuya.tape/4"}},
    "blocks_schema": {"fields": ["tokens:int64:not null"], "metadata": {}},
    "manifest_sha": "n" * 64,
    "manifest_fields_sha": {"synonym_table_version": "s2", "daily": "d1"},
    "manifest_skipped": ["env_id", "relations.wall_seconds_nondeterministic"],
    "run_meta_sha": "q" * 64,
    "run_meta_fields_sha": {"rng_layout": "l2"},
    "run_meta_skipped": [],
    "checkpoints": [{"step": 0, "behavior_hash": "h0x"}, {"step": 1, "behavior_hash": "h"}],
    "n_checkpoints": 3,
}


def test_new_key_changes_cover_every_new_key():
    assert set(NEW_KEY_CHANGES) == set(F.NEW_KEYS)


@pytest.mark.parametrize("key", F.NEW_KEYS)
def test_compare_each_new_key_moves(key):
    va, vb = _row("c1")[key], NEW_KEY_CHANGES[key]
    assert not F.same_value(va, vb)
    doc, code = K.compare_docs(_side([_row("c1")]), _side([_row("c1", **{key: vb})]))
    assert code == 1, key
    assert list(doc["rows"]["c1"]["moved"]) == [key]
    doc, code = K.compare_docs(_side([_row("c1")]), _side([{k: v for k, v in _row("c1").items() if k != key}]))
    assert code == 0 and doc["rows"]["c1"]["not_compared"] == [key]  # 片側の記録に無い=比べていない(同じとは数えない)
    assert doc["summary"]["all_same"] == 0 and doc["summary"]["same_partial"] == 1


def test_compare_manifest_and_run_meta_name_the_moved_fields(capsys, tmp_path: Path):
    b_row = _row("c1", manifest_sha="n" * 64, manifest_fields_sha={"synonym_table_version": "s2", "daily": "d1"},
                 manifest_scalars={"synonym_table_version": "undefined-synonyms-v5x"},
                 run_meta_sha="q" * 64, run_meta_fields_sha={"rng_layout": "l2"}, run_meta_scalars={"rng_layout": "10f"})
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text(json.dumps(_side([_row("c1")])), encoding="utf-8")
    b.write_text(json.dumps(_side([b_row])), encoding="utf-8")
    assert K.compare(a=a, b=b, out=tmp_path / "c.json") == 1
    doc = json.loads((tmp_path / "c.json").read_text(encoding="utf-8"))
    row = doc["rows"]["c1"]
    assert row["manifest_moved"] == {"synonym_table_version": {"a": "undefined-synonyms-v5",
                                                               "b": "undefined-synonyms-v5x"}}
    assert row["run_meta_moved"] == {"rng_layout": {"a": "10e", "b": "10f"}}
    assert row["moved"]["manifest_fields_sha"] == {"keys": {"synonym_table_version": {"a": "s1", "b": "s2"}}}
    out = capsys.readouterr().out
    assert "synonym_table_version" in out and "rng_layout" in out


@pytest.mark.parametrize("b_over,rows_b", [
    ({}, [_row("c1", error="Traceback")]),  # ランの誤り
    ({}, []),  # 構成の欠け
    ({}, [_row("c1", src_as_expected=False)]),  # 違う src を読んだ
    ({"tree_reads_unlisted": ["docs/new.json"]}, [_row("c1")]),
    ({"tree_reads_absent": ["docs/design/rules-table.json"]}, [_row("c1")]),
    ({"foreign_reads": ["docs/design/rules-table.json"]}, [_row("c1")]),
    ({"outside_above_tree": ["<abs>/bc/docs/design/v2-budget-declaration.md"]}, [_row("c1")]),
    ({"src_loaded_outside": ["shibuya.engine.run"]}, [_row("c1")]),
    ({"src_files_conflict": ["shibuya/cli.py"]}, [_row("c1")]),
])
def test_compare_errors_are_2_even_when_values_match(b_over, rows_b):
    _, code = K.compare_docs(_side([_row("c1")]), _side(rows_b, **b_over))
    assert code == 2


def test_compare_moved_and_error_is_2():
    _, code = K.compare_docs(_side([_row("c1"), _row("c2")]), _side([_row("c1", final="0"), _row("c2", error="x")]))
    assert code == 2


def test_compare_config_only_in_b_is_2():
    doc, code = K.compare_docs(_side([_row("c1")]), _side([_row("c1"), _row("c2")]))
    assert code == 2 and doc["rows"]["c2"] == {"missing_in": "a"}
    assert doc["summary"]["errors"] == 1


def test_compare_with_no_configs_is_2():
    """検収 M3: 構成が 0 のまま「同じ」を返さない。"""
    for a, b in (({}, {}), ({"runs": {}}, {"runs": {}}), (_side([]), _side([]))):
        doc, code = K.compare_docs(a, b)
        assert code == 2 and doc["summary"]["configs"] == 0
        assert any("構成が 0" in c for c in doc["checks"]["compare"])


def test_compare_lacking_25_keys_is_2():
    """検収 M3: 25 欄が両側とも欠けた行・片側だけ欠けた行は誤り。"""
    doc, code = K.compare_docs({"runs": {"c": {"config": "c"}}}, {"runs": {"c": {"config": "c"}}})
    assert code == 2 and "lacking_keys" in doc["rows"]["c"]
    short = _row("c1")
    del short["meals"]
    doc, code = K.compare_docs(_side([_row("c1")]), _side([short]))
    assert code == 2 and doc["rows"]["c1"]["lacking_keys"] == {"a": [], "b": ["meals"]}


@pytest.mark.parametrize("key,va,vb", [
    ("agents", 5000, 10), ("seed", 1, 2), ("set", "all19", "arms"), ("env", {}, {"SHIBUYA_CONTACT": "c1"}),
    ("kw", {}, {"x": 1}), ("world", "data/world/v2", "data/world/v1"), ("drop_behavior_item", "", "agents.pos"),
    ("multiset_items", "", "a.b"), ("pythonhashseed", "0", "1"), ("env_hidden", [], ["SHIBUYA_BUDGET_MD"]),
])
def test_compare_condition_mismatch_is_2(key, va, vb):
    """検収 M3: 体数・seed・組・切替口・引数・世界・ハッシュを弱める口・PYTHONHASHSEED が違えば値が同じでも誤り。"""
    doc, code = K.compare_docs(_side([_row("c1")], **{key: va}), _side([_row("c1")], **{key: vb}))
    assert code == 2
    assert any(key in c for c in doc["checks"]["conditions"])


def test_compare_ignores_the_fleet_key_in_hidden_env():
    _, code = K.compare_docs(_side([_row("c1")]), _side([_row("c1")], env_hidden=["SHIBUYA_FLEET_API_KEY"]))
    assert code == 0


def test_compare_nan_is_same_and_type_change_moves():
    """検収 L6: NaN は「動いた」にしない。0 と 0.0 は違う値。"""
    doc, code = K.compare_docs(_side([_row("c1", mean_delay_min=float("nan"))]),
                               json.loads(json.dumps(_side([_row("c1", mean_delay_min=float("nan"))]))))
    assert code == 0
    doc, code = K.compare_docs(_side([_row("c1", mean_delay_min=0.0)]), _side([_row("c1", mean_delay_min=0)]))
    assert code == 1 and list(doc["rows"]["c1"]["moved"]) == ["mean_delay_min"]


def test_compare_reads_old_records_without_new_fields():
    """古い記録(新しい欄が無い)は 25 欄を比べて 0。新しい欄は「比べていない」と注を付け、同じとは数えない。strict なら 2。"""
    a = json.loads((V30A / "base_2160272.json").read_text(encoding="utf-8"))
    b = json.loads((V30A / "v30a.json").read_text(encoding="utf-8"))
    doc, code = K.compare_docs(a, b)
    s = doc["summary"]
    assert code == 0 and s["all_same"] == 0 and s["same_partial"] == 19
    assert set(s["not_compared"]) == set(F.NEW_KEYS) - {"n_checkpoints"}  # n_checkpoints は古い記録にもある
    assert all(n == 19 for n in s["not_compared"].values())
    assert "比べていない" in s["result"]
    assert {"set", "world", "pythonhashseed", "env_hidden"} <= set(s["conditions_not_compared"])
    assert all(len(r["same"]) == 26 for r in doc["rows"].values())  # 25 欄+n_checkpoints
    _, code = K.compare_docs(a, b, strict=True)
    assert code == 2


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


@pytest.mark.skipif(os.name != "nt", reason="大文字小文字を区別しない道筋は Windows だけ")
def test_mask_paths_ignores_case_on_windows(tmp_path: Path):
    tree = tmp_path / "Tree"
    raw = str(tree / "src" / "x.py").swapcase()
    masked = K.mask_paths(raw, [(tree, "<tree>")])
    assert masked.startswith("<tree>") and str(tree).lower() not in masked.lower()


def test_tree_label_and_mask_outside(tmp_path: Path):
    """検収 L8: 比べる側(道具のリポ)の誤りの文は <repo>。外の道筋は <abs>/… にしてドライブを出さない。"""
    assert K.tree_label(ROOT) == "<repo>" and K.tree_label(tmp_path) == "<tree>"
    got = K.mask_outside([str(tmp_path / "w" / "a.txt"), os.path.abspath(os.sep + "zz_elsewhere" + os.sep + "b.txt")],
                         [(tmp_path, "<tmp>")])
    assert got == ["<abs>/zz_elsewhere/b.txt", "<tmp>/w/a.txt"]


# ================================================================== 開いたファイルの仕分け
def test_sort_reads(tmp_path: Path):
    """検収 M1(M08・M16)・M4: 写しの木の追跡ファイル・道具のリポ(src も)・写しの木の上の階・外を仕分ける。"""
    work = tmp_path / "w"
    tree = work / "tree"
    repo = tmp_path / "repo"
    py = tmp_path / "py"
    seen = [tree / "src" / "shibuya" / "a.py", tree / "data" / "w" / "x.parquet", tree / "docs" / "design" / "r.json",
            tree / ".git" / "HEAD", repo / "src" / "shibuya" / "engine" / "run.py", repo / "docs" / "y.json",
            repo / "data" / "z.csv", repo / "src" / "shibuya_sim.egg-info" / "METADATA", repo / "tools" / "t.py",
            work / "docs" / "design" / "b.md", work / "tapes" / "t" / "calls.parquet", tmp_path / "elsewhere.txt",
            py / "Lib" / "json" / "__init__.py"]
    got = K.sort_reads([str(p) for p in seen], tree_root=tree, repo=repo, skip_dirs=[repo / "tools", py, work / "tapes"])
    assert got["tree_reads"] == ["docs/design/r.json"]
    assert got["foreign"] == ["docs/y.json", "src/shibuya/engine/run.py"]
    assert got["outside"] == sorted([os.path.abspath(work / "docs" / "design" / "b.md"),
                                     os.path.abspath(tmp_path / "elsewhere.txt")])
    assert got["above"] == [os.path.abspath(work / "docs" / "design" / "b.md")]
    same = K.sort_reads([str(p) for p in seen], tree_root=repo, repo=repo, skip_dirs=[py])
    assert same["foreign"] == []  # 比べる側(読む src の親が道具のリポ)は foreign を数えない
    assert same["tree_reads"] == ["docs/y.json", "tools/t.py"]


def test_classify_reads(tmp_path: Path):
    (tmp_path / "docs" / "design").mkdir(parents=True)
    (tmp_path / "docs" / "design" / "rules-table.json").write_text("{}", encoding="utf-8")
    got = T.classify_reads(["docs/design/rules-table.json", "docs/design/bridging-ledger.json", "docs/zz.md"], tmp_path)
    assert got == {"unlisted": ["docs/zz.md"], "absent": ["docs/design/bridging-ledger.json", "docs/zz.md"]}
    extra = T.classify_reads(["docs/zz.md"], tmp_path, listed=[*T.TRACKED_READS, "docs/zz.md"])
    assert extra["unlisted"] == []  # --extra-path で足したもの(検収 M2)


def test_opened_outside(tmp_path: Path):
    root = tmp_path / "r"
    tool = root / "tools" / "bytecheck"
    seen = [str(root / "src" / "shibuya" / "a.py"), str(root / "data" / "w" / "x.parquet"),
            str(root / "docs" / "design" / "rules-table.json"), str(tool / "check.py"),
            str(tmp_path / "elsewhere.txt"), str(root / "tests" / "t.json"), str(root)]
    got = K.opened_outside(seen, root, skip_tops=("src", "data"), skip_dirs=[tool])
    assert got == ["docs/design/rules-table.json", "tests/t.json"]


def test_audit_hook_records_opens():
    before = set(K._OPENED)
    K._audit("open", ("some/relative/file.txt", "r", 0))
    K._audit("open", (3, "r", 0))  # fd は記録しない
    K._audit("os.listdir", ("x",))
    assert set(K._OPENED) - before == {"some/relative/file.txt"}
    K._OPENED.discard("some/relative/file.txt")


def test_loaded_src_files_and_digest(tmp_path: Path, monkeypatch):
    src = tmp_path / "src"
    (src / "shibuya").mkdir(parents=True)
    (src / "shibuya" / "__init__.py").write_bytes(b"# x\n")
    other = tmp_path / "other.py"
    other.write_bytes(b"# y\n")
    mod = types.ModuleType("shibuya")
    mod.__file__ = str(src / "shibuya" / "__init__.py")
    stray = types.ModuleType("shibuya.zz_stray")
    stray.__file__ = str(other)
    monkeypatch.setitem(sys.modules, "shibuya", mod)
    monkeypatch.setitem(sys.modules, "shibuya.zz_stray", stray)
    files, outside = K.loaded_src_files(src)
    want = hashlib.sha256(b"# x\n").hexdigest()[:16]
    assert files == {"shibuya/__init__.py": want}
    assert "shibuya.zz_stray" in outside
    assert T.src_files_digest(src, ["shibuya/__init__.py", "shibuya/none.py"]) == {"shibuya/__init__.py": want,
                                                                                  "shibuya/none.py": None}


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

#: 検収 L2 の走査の穴(``scan_gaps.py`` の形)。別のモジュールから import した名は見つけない(宣言・ランの記録で拾う)。
SYNTH_GAPS = {
    "os_path_join": ('import os\nROOT = "x"\nP = os.path.join(ROOT, "docs", "design", "new-a.json")\n',
                     "docs/design/new-a.json"),
    "path_single_then_div": ('from pathlib import Path\nP = Path("docs") / "design" / "new-b.json"\n',
                             "docs/design/new-b.json"),
    "concat_plus": ('NAME = "new-c.json"\nP = "docs/design/" + NAME\n', "docs/design/new-c.json"),
    "concat_plus_dir": ('P = "docs/" + "design/new-d.json"\n', "docs/design/new-d.json"),
    "format_call": ('P = "docs/design/{}.json".format("new-e")\n', "docs/design/{}.json"),
    "percent": ('P = "docs/design/%s.json" % "new-f"\n', "docs/design/{}.json"),
    "slash_join": ('P = "/".join(["docs", "design", "new-g.json"])\n', "docs/design/new-g.json"),
    "list_parts": ('from pathlib import Path\nPARTS = ["docs", "design", "new-h.json"]\nP = Path(*PARTS)\n',
                   "docs/design/new-h.json"),
    "backslash": ('P = "docs\\\\design\\\\new-m.json"\n', "docs/design/new-m.json"),
    "dot_slash": ('P = "./docs/design/new-n.json"\n', "docs/design/new-n.json"),
    "root_plus": ('def f(root):\n    return root + "docs/design/new-o.json"\n', "docs/design/new-o.json"),
}


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


@pytest.mark.parametrize("name", sorted(SYNTH_GAPS))
def test_scanner_finds_the_l2_forms(tmp_path: Path, name):
    code, want = SYNTH_GAPS[name]
    pkg = tmp_path / "src" / "shibuya"
    pkg.mkdir(parents=True)
    (pkg / "m.py").write_text(code, encoding="utf-8")
    bad = T.unclassified_refs(T.scan_path_refs(tmp_path / "src"))
    assert want in bad, (name, bad)


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


def test_root_scanner_counts_the_paths_helpers(tmp_path: Path):
    """〔移す段 2-2・検収 M5〕``core/paths.py`` の手伝い(``find_upward``・``module_dir``・``PACKAGE_ROOT``)で根を読む読み手も
    数える(突然変異: 手伝いで ``docs`` を読む関数を足すと見つかる)。

    〔段 4 の下ごしらえ〕試験の木の根の道のモジュールの置き場と import の文は、今の置き場(モジュールの ``__name__``)から
    組み立てる(前は字面で、移す道具がファイルの道と import の文だけを書き換え、ディレクトリの名が残って食い違った)。"""
    from shibuya.core import paths as PATHS

    mod = PATHS.__name__
    pkg_name, _, leaf = mod.rpartition(".")
    paths_rel = mod.partition(".")[2].replace(".", "/") + ".py"
    pkg = tmp_path / "src" / "shibuya"
    files = {
        paths_rel: "from pathlib import Path\nREPO_ROOT = Path(__file__).parents[3]\n",
        "a.py": (f"from {mod} import find_upward, module_dir\n"
                 "def f():\n    return find_upward('docs/x.md', module_dir(__name__))\n"),
        "b.py": (f"from {mod} import PACKAGE_ROOT\n"
                 "def g():\n    return PACKAGE_ROOT.parent.parent / 'docs' / 'x.md'\n"),
        "c.py": f"from {pkg_name} import {leaf} as P\ndef h():\n    return P.REPO_ROOT / 'docs'\n",
        "d.py": "def k(start):\n    for p in (start, *start.parents):\n        pass\n",
        "e.py": "X = 1\n",
    }
    for rel, text in files.items():
        (pkg / rel).parent.mkdir(parents=True, exist_ok=True)
        (pkg / rel).write_text(text, encoding="utf-8")
    assert paths_rel.count("/") == 1  # 根の道のモジュールは包みの 1 段下(REPO_ROOT が parents[3] で届く深さ)
    assert set(T.scan_root_anchors(tmp_path / "src")) == {
        f"shibuya/{paths_rel}", "shibuya/a.py", "shibuya/b.py", "shibuya/c.py", "shibuya/d.py"}


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


def test_place_and_remove_link_keeps_the_target(tmp_path: Path, monkeypatch):
    target = tmp_path / "real_data"
    (target / "sub").mkdir(parents=True)
    (target / "sub" / "keep.txt").write_text("中身", encoding="utf-8")
    tree = tmp_path / "tree"
    tree.mkdir()
    real_run = subprocess.run

    def no_cmd(args, *a, **k):  # 検収 L7: つなぎを置く・外すのに cmd を通さない
        assert not (args and str(args[0]).lower() == "cmd"), args
        return real_run(args, *a, **k)

    monkeypatch.setattr(T.subprocess, "run", no_cmd)
    try:
        link = T.place_data_link(tree, target)
    except OSError as e:  # 記号のリンクを作れない環境(権限)
        pytest.skip(f"つなぎを作れない: {e}")
    assert T.is_link(link)
    assert (link / "sub" / "keep.txt").read_text(encoding="utf-8") == "中身"
    with pytest.raises(FileExistsError, match="既にある"):  # 道具の検査が先に止める(OS の誤りより前・文で分かる)
        T.place_data_link(tree, target)
    T.remove_link(link)
    assert not link.exists() and not T.is_link(link)
    assert (target / "sub" / "keep.txt").read_text(encoding="utf-8") == "中身"  # 先の中身は残る
    with pytest.raises(FileNotFoundError):
        T.place_data_link(tree, tmp_path / "no_such_target")


# ================================================================== 偽のエンジンで one と side を回す
FAKE_CLI = '''"""試験用の偽のエンジン(tests/tools/test_bytecheck.py が一時の木に置く)。FAKE_VARIANT で出力を変える。"""
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


@dataclass(frozen=True)
class Point:
    step: int
    behavior_hash: str
    full_hash: str


def _env_id():
    return os.environ.get("FAKE_ENV_ID", "e0")


class Result:
    def __init__(self, variant):
        self.variant = variant
        self.final_hash = ("b" if "final" in variant else "a") * 64
        self.llm_calls = 3
        self.process_counters = {"salient.collapse": 0, "dispatch.arrived": 0, "dispatch.mean_delay_min": 0.0}
        self.checkpoints = [Point(0, "m1" if "mid" in variant else "m0", "f0"), Point(1, "h1", "g1")]
        self.action_usage = {"歩く": 2}
        self.calls_by_condition = {"X": 3}
        self.replay_date = "2026-07-13"
        self.salient_events = 0
        self.noticed = 0
        self.dispatches = 0
        self.meals = 1
        self.state_hashes_end_of_day = {"behavior_hash": "e"}
        self.full_hash_bytes = {"r": 1}
        self.checkpoint_seconds = [time.perf_counter() % 1]
        self.phase_seconds = {"checkpoint": 0.1}
        self.wall_seconds = time.perf_counter() % 7

    def run_manifest_fields(self):
        return {"rng_scheme": "counter", "hash_scheme": "behavior", "start_sim_datetime": "2026-07-13T00:00:00",
                "replay_date": "2026-07-13", "calendar": {"calendar_weekday": "real"}, "frozen_sources": {"a": "1"},
                "synonym_table_version": "undefined-synonyms-v5x" if "syn" in self.variant else "undefined-synonyms-v5",
                "env_id": _env_id(),
                "environment": {"code": {"git_commit": _env_id()}, "env_id": _env_id(), "platform": {"python": "3"}},
                "resume": {"read_seconds": time.perf_counter(), "restore_seconds": 0.0, "finished": True},
                "relations": {"wall_seconds_nondeterministic": {"x": time.perf_counter()}, "n": 1},
                "hashseed": os.environ.get("PYTHONHASHSEED", ""), "weather": "w"}


def run(n_agents, seed, world_dir, tape_path, **kw):
    variant = set(os.environ.get("FAKE_VARIANT", "").split(","))
    tape = Path(tape_path)
    tape.mkdir(parents=True, exist_ok=True)
    tokens = pa.int64() if "tokens64" in variant else pa.int32()
    blocks = pa.table({"block_id": pa.array(["b0", "b1"]), "text": pa.array(["一", "二"]),
                       "tokens": pa.array([1, 2], tokens)})
    pq.write_table(blocks, tape / "blocks.parquet")
    calls = pa.table({"call_id": pa.array(["c0", "c1", "c2"]), "agent_id": pa.array([1, 2, 3], pa.int32())})
    calls = calls.replace_schema_metadata({"shibuya.tape.schema": "shibuya.tape/5" if "schema" in variant
                                           else "shibuya.tape/4"})
    pq.write_table(calls, tape / "calls.parquet")
    meta = {"response_delay": 1, "rng_scheme": "counter", "rng_layout": "10f" if "meta" in variant else "10e",
            "env_id": _env_id(), "environment": {"code": {"git_commit": _env_id()}, "env_id": _env_id()}}
    (tape / "run_meta.json").write_text(json.dumps(meta, sort_keys=True), encoding="utf-8")
    if "extra_file" in variant:
        (tape / "extra.json").write_text("{}", encoding="utf-8")
    for p in os.environ.get("FAKE_READS", "").split(os.pathsep):
        if p:
            Path(p).read_bytes()
    return Result(variant)
'''


def _write_fake_tree(tree: Path) -> None:
    pkg = tree / "src" / "shibuya"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text('"""偽のエンジン。"""\n', encoding="utf-8")
    (pkg / "cli.py").write_text(FAKE_CLI, encoding="utf-8")
    for rel in T.HEAD_TREE_FILES:
        p = tree / rel
        if Path(rel).suffix:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("{}", encoding="utf-8")
        else:
            p.mkdir(parents=True, exist_ok=True)
    (tree / "docs" / "zz.md").write_text("一覧に無い", encoding="utf-8")
    (tree / "docs" / "bench" / "anchors" / "hunger_energy_anchors_v0.json").write_text("{}", encoding="utf-8")


@pytest.fixture(scope="module")
def fake(tmp_path_factory):
    pytest.importorskip("pyarrow")
    base = tmp_path_factory.mktemp("bcfake")
    tree = base / "tree"
    _write_fake_tree(tree)
    (base / "docs" / "design").mkdir(parents=True)
    (base / "docs" / "design" / "above.md").write_text("上の階", encoding="utf-8")
    (base / "elsewhere").mkdir()
    (base / "elsewhere" / "x.txt").write_text("外", encoding="utf-8")
    cache: dict[str, tuple[int, dict]] = {}

    def run_side(tag: str, *, variant: str = "", env_id: str = "e0", reads=(), extra_paths=()):
        if tag not in cache:
            out = base / f"{tag}.json"
            with _env(FAKE_VARIANT=variant, FAKE_ENV_ID=env_id, FAKE_READS=os.pathsep.join(str(p) for p in reads),
                      PYTHONHASHSEED="123"):
                code = K.side(label=tag, scratch=base / "s", out=out, src=tree / "src", only="w6_v3_default", jobs=1,
                              world="no/such/world", agents=3, extra_paths=extra_paths)
            cache[tag] = (code, json.loads(out.read_text(encoding="utf-8")) if out.is_file() else {})
        return cache[tag]

    return SimpleNamespace(base=base, tree=tree, run_side=run_side)


def test_fake_side_runs_with_the_given_src(fake):
    code, doc = fake.run_side("a")
    assert code == 0, doc
    row = doc["runs"]["w6_v3_default"]
    assert row["src_as_expected"] is True and doc["src"] == "写し"
    assert doc["pythonhashseed"] == "0"  # 呼び手の値(123)でなく決まった値を両側に置く(検収 L1)
    assert row["manifest_scalars"]["hashseed"] == "0"  # ランの中で本当にその値
    assert doc["tool"] == K.TOOL_ID
    assert "src_files" not in row and row["src_files_n"] == 2
    files = ["shibuya/__init__.py", "shibuya/cli.py"]
    assert doc["src_files"] == T.src_files_digest(fake.tree / "src", files)
    assert row["final"] == "a" * 16 and row["final_full"] == "a" * 64
    assert row["blocks_sha"] == K._h_plain({"block_id": ["b0", "b1"], "text": ["一", "二"], "tokens": [1, 2]})
    assert row["calls_columns_sha"] == {"call_id": K._h_plain(["c0", "c1", "c2"]), "agent_id": K._h_plain([1, 2, 3])}
    tape = fake.base / "s" / "a_w6_v3_default"
    assert row["tape_files"] == ["blocks.parquet", "calls.parquet", "run_meta.json"]
    assert row["tape_sha256"] == {n: hashlib.sha256((tape / n).read_bytes()).hexdigest()
                                  for n in ("blocks.parquet", "calls.parquet")}
    assert row["blocks_schema"]["fields"] == ["block_id:string:null", "text:string:null", "tokens:int32:null"]
    assert row["calls_schema"]["metadata"] == {"shibuya.tape.schema": "shibuya.tape/4"}
    assert row["manifest_skipped"] == sorted(["env_id", "environment.code", "environment.env_id", "resume.read_seconds",
                                              "resume.restore_seconds", "relations.wall_seconds_nondeterministic"])
    assert row["run_meta_skipped"] == ["env_id", "environment.code", "environment.env_id"]
    assert row["checkpoints"] == [{"step": 0, "behavior_hash": "m0", "full_hash": "f0"},
                                  {"step": 1, "behavior_hash": "h1", "full_hash": "g1"}]
    assert row["n_checkpoints"] == 2 and row["behavior_last"] == "h1"
    assert doc["tree_reads"] == [] and doc["foreign_reads"] == [] and doc["outside_above_tree"] == []
    text = json.dumps(doc, ensure_ascii=False)
    assert not re.search(r"[A-Za-z]:[\\/]", text), "side の JSON に絶対パス"


def test_fake_two_runs_differing_only_in_skipped_fields_are_same(fake):
    _, a = fake.run_side("a")
    code, b = fake.run_side("b", env_id="e1")  # git の commit・env_id・壁時計の秒だけが違う
    assert code == 0
    doc, cmp_code = K.compare_docs(a, b, strict=True)
    assert cmp_code == 0, doc["rows"]
    assert doc["summary"]["all_same"] == 1


@pytest.mark.parametrize("variant,moved", [
    ("tokens64", {"tape_sha256", "blocks_schema"}),  # 検収 H1 の再現 1(blocks_sha は値の list で同じ)
    ("schema", {"tape_sha256", "calls_schema"}),
    ("syn", {"manifest_sha", "manifest_fields_sha"}),  # 検収 H1 の再現 2(manifest の synonym_table_version)
    ("meta", {"run_meta_sha", "run_meta_fields_sha"}),
    ("mid", {"checkpoints"}),  # 途中の checkpoint(最後は同じ)
    ("extra_file", {"tape_files", "tape_sha256"}),
    ("final", {"final"}),
])
def test_fake_variant_moves_exactly_the_expected_fields(fake, variant, moved):
    _, a = fake.run_side("a")
    code, b = fake.run_side(variant, variant=variant, env_id="e1")
    assert code == 0
    doc, cmp_code = K.compare_docs(a, b, strict=True)
    assert cmp_code == 1
    row = doc["rows"]["w6_v3_default"]
    assert set(row["moved"]) == moved
    if variant == "syn":
        assert row["manifest_moved"] == {"synonym_table_version": {"a": "undefined-synonyms-v5",
                                                                   "b": "undefined-synonyms-v5x"}}
    if variant == "meta":
        assert row["run_meta_moved"] == {"rng_layout": {"a": "10e", "b": "10f"}}
    if variant == "mid":
        assert list(row["moved"]["checkpoints"]["items"]) == ["0"]
    if variant == "tokens64":
        assert list(row["moved"]["tape_sha256"]["keys"]) == ["blocks.parquet"]


def test_fake_read_of_an_unlisted_tracked_file_is_an_error(fake):
    code, doc = fake.run_side("unlisted", reads=[fake.tree / "docs" / "zz.md"])
    assert code == 2 and doc["tree_reads_unlisted"] == ["docs/zz.md"]


def test_fake_extra_path_is_listed_and_outside_reads_are_recorded(fake):
    """検収 M2: --extra-path で足したファイルは一覧に無いと数えない。検収 M4: 外で開いたファイルは記録する(誤りにしない)。"""
    rel = "docs/bench/anchors/hunger_energy_anchors_v0.json"
    code, doc = fake.run_side("extra", reads=[fake.tree / rel, fake.base / "elsewhere" / "x.txt"], extra_paths=[rel])
    assert code == 0, doc
    assert doc["tree_reads"] == [rel] and doc["tree_reads_unlisted"] == [] and doc["extra_paths"] == [rel]
    assert any(x.endswith("elsewhere/x.txt") for x in doc["outside_reads"]), doc["outside_reads"]
    assert not any(re.match(r"[A-Za-z]:", x) for x in doc["outside_reads"])


def test_fake_read_in_the_tool_repo_is_foreign(fake):
    code, doc = fake.run_side("foreign", reads=[ROOT / "src" / "shibuya" / "__init__.py"])
    assert code == 2 and doc["foreign_reads"] == ["src/shibuya/__init__.py"]


def test_fake_read_above_the_tree_is_an_error(fake):
    code, doc = fake.run_side("above", reads=[fake.base / "docs" / "design" / "above.md"])
    assert code == 2 and len(doc["outside_above_tree"]) == 1
    assert doc["outside_above_tree"][0].endswith("docs/design/above.md")


def test_fake_one_reports_a_src_other_than_expected(fake, tmp_path: Path):
    env = dict(os.environ, PYTHONPATH=str(fake.tree / "src"), PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, str(PKG_DIR / "cli.py"), "one", "--config", "w6_v3_default", "--world", "x",
                        "--agents", "3", "--tape", str(tmp_path / "t"), "--expect-src", str(tmp_path / "other_src")],
                       capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(ROOT))
    assert r.returncode == 0, r.stderr[-2000:]
    row = json.loads(r.stdout.strip().splitlines()[-1])
    assert row["src_as_expected"] is False and row["src_is_worktree"] is False
    assert sorted(row["src_files"]) == ["shibuya/__init__.py", "shibuya/cli.py"]
    assert row["src_loaded_outside"] == []


# ================================================================== run の配線(side を差し替える)
@pytest.fixture()
def clean_env(monkeypatch):
    for k in list(os.environ):
        if k.startswith("SHIBUYA_"):
            monkeypatch.delenv(k)


class _CopyReached(AssertionError):
    """止まるはずの run が写しの手前を越えた(試験の中で本物の写し・つなぎ・ランに進ませない)。"""


@pytest.fixture()
def stop_before_copy(monkeypatch):
    """断るはずの run が先へ進んだら、写しの木もつなぎも作らずに落とす(壊れた道具でもリポや data に触れない)。"""

    def reached(*a, **k):  # noqa: ANN002, ANN003
        raise _CopyReached("run が写しの手前で止まらなかった")

    for mod, name in ((T, "paths_in_commit"), (T, "git_archive"), (T, "place_data_link"), (K, "side")):
        monkeypatch.setattr(mod, name, reached)


def _fake_archive(repo, commit, paths, dest):  # noqa: ANN001 - git archive の代わり(小さな写しの木)
    (dest / "src" / "shibuya").mkdir(parents=True)
    (dest / "src" / "shibuya" / "__init__.py").write_text('"""写し。"""\n', encoding="utf-8")


def _recording_side(calls: list, *, codes=None, skip_write=(), bad_digest=(), drop_key=""):
    """side の代わり: 渡された引数を記録し、渡された src を読んだように side の JSON を書く。"""

    def fake_side(**kw):
        calls.append(kw)
        tag = "base" if len(calls) == 1 else "work"
        src_dir = Path(kw["src"]).resolve() if str(kw["src"]) else (ROOT / "src").resolve()
        files = T.src_files_digest(src_dir, ["shibuya/__init__.py"])
        if tag in bad_digest:
            files = {k: "0" * 16 for k in files}
        rows = [_row(n) for n in kw["only"].split(",")]
        if drop_key and tag == "work":
            rows = [{k: v for k, v in r.items() if k != drop_key} for r in rows]
        doc = _side(rows, src="作業木" if src_dir == (ROOT / "src").resolve() else "写し",
                    nonce=kw["nonce"], set=kw["set_name"], src_files=files, extra_paths=list(kw["extra_paths"]))
        if tag not in skip_write:
            Path(kw["out"]).write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        return (codes or {}).get(tag, 0)

    return fake_side


@pytest.fixture()
def wired(tmp_path: Path, monkeypatch, clean_env):
    if subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True).returncode != 0:
        pytest.skip("git が無い")
    data = tmp_path / "data"
    data.mkdir()
    monkeypatch.setattr(K, "DATA_DIR", data)
    monkeypatch.setattr(T, "git_archive", _fake_archive)
    return tmp_path


def test_run_gives_the_tree_src_to_base_and_the_given_src_to_work(wired, monkeypatch):
    calls: list = []
    monkeypatch.setattr(K, "side", _recording_side(calls))
    code = K.run(work=wired / "w", out_dir=wired / "o", only="w6_v3_default", extra_paths=["docs/x.json"])
    assert code == 0
    base, work = calls
    assert Path(base["src"]) == wired / "w" / "tree" / "src"  # 検収 M1(M11)
    assert str(work["src"]) == ""  # 既定=作業木の src
    assert base["nonce"] == work["nonce"] and len(base["nonce"]) == 32
    assert base["extra_paths"] == work["extra_paths"] == ["docs/x.json"]  # 検収 M2
    assert base["commit"] == T.resolve_commit(ROOT, "HEAD") and work["commit"].startswith(base["commit"])
    assert not (wired / "w" / "tree" / "data").exists()  # つなぎを外した
    cmp_doc = json.loads(next((wired / "o").glob("*_compare_*.json")).read_text(encoding="utf-8"))
    assert cmp_doc["summary"]["exit_code"] == 0 and cmp_doc["checks"]["run"] == []


def test_run_is_2_when_a_side_failed_even_if_values_match(wired, monkeypatch):
    calls: list = []
    monkeypatch.setattr(K, "side", _recording_side(calls, codes={"base": 2}))
    assert K.run(work=wired / "w", out_dir=wired / "o", only="w6_v3_default") == 2  # 検収 M1(M22)
    cmp_doc = json.loads(next((wired / "o").glob("*_compare_*.json")).read_text(encoding="utf-8"))
    assert any("side が誤り" in c for c in cmp_doc["checks"]["run"])


def test_run_does_not_compare_a_json_from_an_earlier_run(wired, monkeypatch):
    """検収 L5: side が JSON を書かずに戻ったとき、置き場に残った前のランの JSON と比べない。"""
    out = wired / "o"
    out.mkdir()
    short = T.resolve_commit(ROOT, "HEAD")[:7]
    (out / "all19_only_work.json").write_text(json.dumps(_side([_row("w6_v3_default")], nonce="old")), encoding="utf-8")
    calls: list = []
    monkeypatch.setattr(K, "side", _recording_side(calls, skip_write=("work",)))
    assert K.run(work=wired / "w", out_dir=out, only="w6_v3_default") == 2
    assert not (out / f"all19_only_compare_base_{short}_vs_work.json").exists()


@pytest.mark.parametrize("bad", ["base", "work"])
def test_run_checks_the_src_digest_against_the_files(wired, monkeypatch, bad):
    """検収 M1: 基準の側が読んだ src の digest が写しの木と違えば(比べる側も同じく)2。"""
    calls: list = []
    monkeypatch.setattr(K, "side", _recording_side(calls, bad_digest=(bad,)))
    assert K.run(work=wired / "w", out_dir=wired / "o", only="w6_v3_default") == 2
    cmp_doc = json.loads(next((wired / "o").glob("*_compare_*.json")).read_text(encoding="utf-8"))
    assert any("digest" in c or "違う" in c for c in cmp_doc["checks"]["run"])


def test_run_is_strict_about_missing_new_fields(wired, monkeypatch):
    """run は両側を今の道具で回す=新しい欄が無ければ「比べていない」で済ませず 2(compare は strict)。"""
    calls: list = []
    monkeypatch.setattr(K, "side", _recording_side(calls, drop_key="checkpoints"))
    assert K.run(work=wired / "w", out_dir=wired / "o", only="w6_v3_default") == 2
    cmp_doc = json.loads(next((wired / "o").glob("*_compare_*.json")).read_text(encoding="utf-8"))
    assert any("checkpoints" in c for c in cmp_doc["checks"]["compare"])


def test_run_checks_that_base_read_the_copy(wired, monkeypatch):
    calls: list = []
    rec = _recording_side(calls)

    def base_reads_worktree(**kw):  # 基準の側に作業木の src を渡した(検収 M11 の形)
        if not calls:
            kw = dict(kw, src="")
        return rec(**kw)

    monkeypatch.setattr(K, "side", base_reads_worktree)
    assert K.run(work=wired / "w", out_dir=wired / "o", only="w6_v3_default") == 2


def test_run_refuses_a_work_dir_inside_a_git_worktree(tmp_path: Path, clean_env, stop_before_copy):
    """検収 M4: 写しの木が作業木の中にあると、根を上へ辿る読み口が作業木の docs を読む=断る。"""
    inside = ROOT / "zz_bytecheck_work_should_not_exist"
    assert K.run(work=inside, out_dir=tmp_path / "o") == 2
    assert not inside.exists() and not (tmp_path / "o").exists()
    repo = tmp_path / "g"
    if subprocess.run(["git", "init", "-q", str(repo)], capture_output=True).returncode != 0:
        pytest.skip("git が無い")
    assert T.in_git_worktree(repo / "a" / "b") and not T.in_git_worktree(tmp_path / "plain")
    assert K.run(work=repo / "w", out_dir=tmp_path / "o2") == 2
    assert not (repo / "w").exists()


def test_worktree_commit_marks_dirty_tracked_reads(monkeypatch):
    """検収 M1(M17)・L9: 作業木の src なら HEAD・src の外のエンジンが読む追跡ファイルの変更も +dirty に数える。"""
    head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True)
    if head.returncode != 0:
        pytest.skip("git が無い")
    got = K.worktree_commit()
    assert got in (head.stdout.strip(), head.stdout.strip() + "+dirty")
    assert K.worktree_commit(ROOT / "docs") == ""
    seen: list = []
    real_git = T.git

    def spy(repo, *args):  # noqa: ANN001
        seen.append(args)
        return real_git(repo, *args)

    monkeypatch.setattr(T, "git", spy)
    K.worktree_commit(extra_paths=["docs/x.json"])
    status = next(a for a in seen if a[0] == "status")
    assert {"src", "docs/design/rules-table.json", "docs/x.json"} <= set(status)


# ================================================================== run と side の手前の止まり方
def test_run_refuses_a_non_empty_work_dir(tmp_path: Path, clean_env, stop_before_copy):
    work = tmp_path / "w"
    work.mkdir()
    (work / "left.txt").write_text("前のラン", encoding="utf-8")
    code = K.run(work=work, out_dir=tmp_path / "out")
    assert code == 2
    assert sorted(p.name for p in work.iterdir()) == ["left.txt"]  # 何も作らず・何も消さない
    assert not (tmp_path / "out").exists()


def test_run_refuses_stray_env_bad_commit_and_bad_kw(tmp_path: Path, clean_env, stop_before_copy, monkeypatch):
    monkeypatch.setenv("SHIBUYA_CONTACT", "c1")
    assert K.run(work=tmp_path / "w1", out_dir=tmp_path / "o1") == 2
    assert not (tmp_path / "w1").exists()
    monkeypatch.delenv("SHIBUYA_CONTACT")
    monkeypatch.setenv("SHIBUYA_FLEET_API_KEY", "k")  # 鍵は mock のランに効かない=止めない側
    assert K.stray_env(dict(os.environ)) == []
    assert K.run(work=tmp_path / "w2", out_dir=tmp_path / "o2", base="no-such-rev-zzz") == 2
    assert not (tmp_path / "w2").exists()
    assert K.run(work=tmp_path / "w3", out_dir=tmp_path / "o3", only="no_such_config") == 2
    for bad in ("{bad", "[1]"):  # 検収 L3: ランの前に止める
        assert K.run(work=tmp_path / "w4", out_dir=tmp_path / "o4", kw=bad) == 2
        assert not (tmp_path / "w4").exists()
    with pytest.raises(ValueError):
        K.parse_kw("{bad")
    assert K.parse_kw("") == {} and K.parse_kw('{"a": 1}') == {"a": 1}


def test_side_stops_on_an_incomplete_tree_or_bad_kw_without_running(tmp_path: Path):
    (tmp_path / "src" / "shibuya").mkdir(parents=True)
    code = K.side(label="x", scratch=tmp_path / "s", out=tmp_path / "x.json", src=tmp_path / "src")
    assert code == 2
    assert not (tmp_path / "x.json").exists() and not (tmp_path / "s").exists()
    code = K.side(label="x", scratch=tmp_path / "s", out=tmp_path / "x.json", src=tmp_path / "src", kw="{bad",
                  allow_incomplete_tree=True)
    assert code == 2 and not (tmp_path / "x.json").exists()


def test_cli_exit_codes(tmp_path: Path):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text(json.dumps(_side([_row("c1")])), encoding="utf-8")
    b.write_text(json.dumps(_side([_row("c1")])), encoding="utf-8")
    assert CLI.main(["compare", "--a", str(a), "--b", str(b), "--out", str(tmp_path / "c.json")]) == 0
    b.write_text(json.dumps(_side([_row("c1", meals=2)])), encoding="utf-8")
    assert CLI.main(["compare", "--a", str(a), "--b", str(b), "--out", str(tmp_path / "c.json")]) == 1
    assert CLI.main(["compare", "--a", str(a), "--b", str(tmp_path / "none.json"), "--out", str(tmp_path / "c.json")]) == 2
    old = {k: v for k, v in _row("c1").items() if k not in F.NEW_KEYS}
    a.write_text(json.dumps(_side([old])), encoding="utf-8")
    b.write_text(json.dumps(_side([old])), encoding="utf-8")
    assert CLI.main(["compare", "--a", str(a), "--b", str(b), "--out", str(tmp_path / "c.json")]) == 0
    assert CLI.main(["compare", "--a", str(a), "--b", str(b), "--out", str(tmp_path / "c.json"), "--strict"]) == 2
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


def test_nan_survives_the_side_json_round_trip():
    assert math.isnan(json.loads(json.dumps({"x": float("nan")}))["x"])
