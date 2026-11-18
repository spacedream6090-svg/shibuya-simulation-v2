"""移す段 2-2〜2-5(返事その 7 §4-2・計画 docs/reference/package-map-final-2026-11-09.md §7-3): 下ごしらえ(結果は変えない)。

- 2-2 根の道を 1 か所に: ランの側(build の外)で ``__file__`` を使うのは ``core/paths.py`` だけ。読み手が求める道は前と
  同じ(リポの根・包みの根・錨・台帳・表・宣言表・知覚の契約書)。
- 2-3 書きの許可の一覧の形: ``allow.index`` はファイルの一覧(``RESOLVE_FILES``)を読む。段 2 では 1 本で、閉包は
  前と同じ(凍結の表との突き合わせは ``tests/engine/systems/`` の試験)。関数の名がファイルをまたいで重なれば止める。
  ``static_check`` の resolve と系の包みの名はモジュールの ``__name__`` から作る。
- 2-4 乱数の検査の道: ``rng_audit`` の ``core.rng`` の名は ``core.rng.__name__`` から作る(置き場を動かしても呼び手を
  見落とさない=試験の中で名を替えて確かめる)。
- 2-5 世界カタログの包みの名: ``importlib.resources`` に渡す包みの名は ``__package__`` から作る。
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path
from types import SimpleNamespace

import pytest

import shibuya
from shibuya.foundation import budget as BU
from shibuya.foundation import paths as P
from shibuya.foundation import rng as RNG
from shibuya.mind.judge import classical as CL
from shibuya.world.body import energy as EN
from shibuya.runtime.state import resume as RS
from shibuya.validation.static import rng_audit as RA
from shibuya.foundation.decl import bridging as BL
from shibuya.validation.static import bridging_scan as BS
from shibuya.world.facts.rules import table as RT
from shibuya.runtime.systems import allow as AL
from shibuya.validation.static import system_static_check as SC
from shibuya.world.ledger import world_catalog as WC
from shibuya.world.ledger import constitution as CO
from tests import _places as PL

PKG = Path(shibuya.__file__).resolve().parent
ROOT = PKG.parents[1]


# ================================================================= 2-2
def test_only_core_paths_reads_dunder_file_on_the_run_side():
    users = []
    for p in sorted(PKG.rglob("*.py")):
        rel = p.relative_to(PKG).as_posix()
        if rel.startswith("build/"):
            continue
        tree = ast.parse(p.read_text(encoding="utf-8"))
        if any(isinstance(n, ast.Name) and n.id == "__file__" for n in ast.walk(tree)):
            users.append(rel)
    assert users == ["foundation/paths.py"]


def test_roots_are_the_same_paths_as_before():
    assert P.PACKAGE_ROOT == PKG
    assert P.REPO_ROOT == ROOT
    assert (P.REPO_ROOT / "pyproject.toml").is_file()
    assert P.resolve_repo_path("docs/x.md") == ROOT / "docs" / "x.md"
    assert P.resolve_repo_path(ROOT / "a.txt") == ROOT / "a.txt"
    assert P.module_dir(SC.__name__) == Path(SC.__file__).resolve().parent
    assert P.module_dir(BU.__name__) == Path(BU.__file__).resolve().parent


def test_readers_resolve_the_same_files_as_before():
    assert BL.default_path() == ROOT / "docs" / "design" / "bridging-ledger.json"
    assert RT.default_path() == ROOT / "docs" / "design" / "rules-table.json"
    assert CL.ACTIVITY_PRIOR_PATH == ROOT / "docs" / "bench" / "anchors" / "ssb2021_activity_prior_v0.json"
    assert EN.ANCHORS_BUILD_PATH.parent == ROOT / "docs" / "bench" / "anchors"
    assert AL.src_root() == PKG
    assert SC.source_root() == Path(SC.__file__).resolve().parent
    assert RS._repo_root() == ROOT
    assert BU._repo_root() == ROOT
    assert CO._repo_root(CO.PERCEPTION_CONTRACT_RELPATH) == ROOT
    decls = BS.scan_package()
    assert decls and all(d.path.startswith("src/shibuya/") for d in decls if d.form != BS.FORM_FALLBACK)


def test_find_upward_walks_from_the_start_directory(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("x", encoding="utf-8")
    deep = tmp_path / "s" / "t"
    deep.mkdir(parents=True)
    assert P.find_upward("docs/a.md", deep) == tmp_path
    (deep / "docs").mkdir()
    (deep / "docs" / "a.md").write_text("y", encoding="utf-8")
    assert P.find_upward("docs/a.md", deep) == deep  # 始めのディレクトリ自身も見る(前の「ファイルの親から」と同じ)
    with pytest.raises(FileNotFoundError, match="上位を探索"):
        P.find_upward("docs/none.md", deep)


# ================================================================= 2-3
def test_resolve_files_list_reads_the_resolve_module():
    """〔割る段 6 の S6-G0・親の裁定 R1〕前は字面の 1 本(``engine/resolve.py``)とモジュールの ``__file__`` を比べた。今は書き手の
    一覧の全部のファイルが在り・重ならず、索引の関数の集合=一覧の全部のファイルの頂上の関数(割る前は 1 本=前と同じ比べ)。"""
    files = [AL.src_root() / rel for rel in AL.RESOLVE_FILES]
    assert files and len(set(AL.RESOLVE_FILES)) == len(AL.RESOLVE_FILES) and all(p.is_file() for p in files)
    names = [n.name for p in files for n in ast.parse(p.read_text(encoding="utf-8")).body
             if isinstance(n, ast.FunctionDef)]
    assert len(names) == len(set(names))
    assert AL.index().funcs == frozenset(names) and "apply" in names
    # 〔S6-G0 の検収 中-1〕一覧のどのファイルも、索引の関数を 1 つ以上定義する(本数に依らない)。凍結した関数の集合
    # (``tests/engine/systems/resolve_index_frozen.json``)と合わせて、一覧は「凍結した関数を定義するファイル」に固定される
    # (関数を持たないファイルはここで、索引に無い関数を持つファイルは凍結の表で落ちる)
    assert _writer_files_without_index_functions(AL.RESOLVE_FILES, AL.index().funcs) == []


def _writer_files_without_index_functions(rels, funcs) -> list[str]:  # noqa: ANN001
    """書き手の一覧のうち、索引の関数(``funcs``)を 1 つも頂上で定義しないファイル。"""
    out = []
    for rel in rels:
        tree = ast.parse((AL.src_root() / rel).read_text(encoding="utf-8"))
        if not {n.name for n in tree.body if isinstance(n, ast.FunctionDef)} & set(funcs):
            out.append(rel)
    return out


def test_negative_a_stray_file_in_the_writer_list_is_seen(monkeypatch):
    """〔S6-G0 の検収 中-1〕負の対照(メモリの中で一覧を差し替える): 頂上の関数を持たないファイル(``economy/tax_deposit.py``=
    クラスだけ)をまぎれさせると、上の確かめが落ちる。索引に無い関数だけを持つファイル(``foundation/write_guard.py``)を
    まぎれさせると、索引の関数が増えて凍結の表との比べが落ちる(一覧の外で作った索引の関数とは重ならない)。"""
    from tests.engine.systems import test_resolve_index_frozen as RI

    real = tuple(AL.RESOLVE_FILES)
    frozen = RI.load_frozen()
    real_funcs = AL.index().funcs
    assert _writer_files_without_index_functions(("foundation/write_guard.py",), real_funcs) == [
        "foundation/write_guard.py"]
    for stray, word in (("economy/tax_deposit.py", "no_funcs"), ("foundation/write_guard.py", "frozen")):
        monkeypatch.setattr(AL, "RESOLVE_FILES", (*real, stray))
        AL.index.cache_clear()
        try:
            ix = AL.index()
            missing = _writer_files_without_index_functions(AL.RESOLVE_FILES, ix.funcs)
            diff = RI.diff(RI.normalize(ix), frozen)
        finally:
            monkeypatch.undo()
            AL.index.cache_clear()
        if word == "no_funcs":
            assert missing == [stray], missing
        else:
            assert missing == [] and diff and any(x.startswith("funcs") for x in diff), diff


#: 書き手の一覧(試験が一覧を差し替える前の値=偽の木へ写す本物のファイル)。
_REAL_WRITERS: tuple[str, ...] = tuple(AL.RESOLVE_FILES)


def _fake_writers(root: Path) -> tuple[str, ...]:
    """書き手の一覧の全部のファイルを偽の木へ同じ道で写す(割る前は 1 本)。"""
    for rel in _REAL_WRITERS:
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text((AL.src_root() / rel).read_text(encoding="utf-8"), encoding="utf-8")
    (root / "engine").mkdir(parents=True, exist_ok=True)
    return _REAL_WRITERS


def test_index_refuses_a_function_name_split_across_files(tmp_path, monkeypatch):
    root = tmp_path / "shibuya"
    rels = _fake_writers(root)
    name = sorted(AL.index().funcs)[0]  # 書き手のファイルに在る関数の名(偽の割り先に同じ名を置く)
    (root / "engine" / "resolve_part.py").write_text(f"def {name}():\n    pass\n", encoding="utf-8")
    monkeypatch.setattr(AL, "RESOLVE_FILES", (*rels, "engine/resolve_part.py"))
    AL.index.cache_clear()
    try:
        with pytest.raises(ValueError, match="関数の名がファイルをまたいで重なる"):
            AL.index(str(root))
    finally:
        AL.index.cache_clear()


def _split_tree(tmp_path: Path, part: str) -> Path:
    """resolve.py と、割った先のふりのファイル 1 本と、``declared_columns`` が読むファイルを置いた木(``src/shibuya`` の形)。"""
    from shibuya.runtime.state import ledger_ast as A

    root = tmp_path / "shibuya"
    _fake_writers(root)
    (root / "engine" / "resolve_part.py").write_text(part, encoding="utf-8")
    for rel in A.DECL_FILES.values():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text((PKG / rel).read_text(encoding="utf-8"), encoding="utf-8")
    return root


def test_index_refuses_a_table_name_split_across_files_and_merges_distinct_ones(tmp_path, monkeypatch):
    """〔検収 L2〕頂上の表の名(関数を指す代入)がファイルをまたいで重なれば止める。重ならなければ 2 本を 1 つの閉包にする。"""
    ref = AL.index().tables["_APPLY"]
    monkeypatch.setattr(AL, "RESOLVE_FILES", (*_REAL_WRITERS, "engine/resolve_part.py"))
    AL.index.cache_clear()
    try:
        bad = _split_tree(tmp_path / "bad", "def _part_helper():\n    pass\n\n\n_APPLY = {1: _part_helper}\n")
        with pytest.raises(ValueError, match="頂上の表の名がファイルをまたいで重なる"):
            AL.index(str(bad))
        good = _split_tree(tmp_path / "good", "def _part_helper():\n    pass\n\n\n_PART = {1: _part_helper}\n")
        idx = AL.index(str(good))
        assert "_part_helper" in idx.funcs and idx.tables["_PART"] == {"_part_helper"}
        assert idx.tables["_APPLY"] == ref
    finally:
        AL.index.cache_clear()


def test_static_check_names_come_from_the_modules():
    # 〔割る段 6 の S6-A〕resolve のモジュールの名は、allow.RESOLVE_FILES から作る名の集合。割る前は 1 つ(=前と同じ範囲)
    assert SC.RESOLVE_MODULES == frozenset(
        shibuya.__name__ + "." + rel[:-3].replace("/", ".") for rel in AL.RESOLVE_FILES)
    assert len(SC.RESOLVE_MODULES) == len(AL.RESOLVE_FILES) >= 1
    # resolve の口 ``apply`` を定義するモジュール(割る前は resolve・割った後は主な割り先)
    home = next(m for m in sorted(SC.RESOLVE_MODULES) if getattr(getattr(importlib.import_module(m), "apply", None),
                                                                   "__module__", "") == m)
    RV = importlib.import_module(home)
    # 系の包みの名は、系の包みで定義したモジュール(allow)の包みから作る(〔段 4 の下ごしらえ・親の決定 3〕包みの頭を読まない)
    assert SC._SYSTEMS_PREFIX == AL.__name__.rpartition(".")[0] + "."
    # 〔割る段 6 の S6-A〕前は名の親と葉の字面(``_RESOLVE_PARENT``・``_RESOLVE_LEAF``)を比べた。今は集合で引く形を動かして確かめる:
    # 親の包みから葉を読む・モジュールを別名で import・口の名を素の import・頂上の別名と口を拾い、ほかのモジュールは拾わない
    parent, leaf = RV.__name__.rsplit(".", 1)
    systems = AL.__name__.rpartition(".")[0]
    fdef = ast.parse(f"def f():\n    from {parent} import {leaf} as X\n    import {RV.__name__} as Z\n"
                     f"    from {RV.__name__} import apply as y\n    from {systems} import allow as W\n").body[0]
    mods, funcs = SC._resolve_names(SimpleNamespace(R=RV, ap=RV.apply, A=AL), fdef)
    assert mods == {"R", "X", "Z"} and funcs == {"ap": "apply", "y": "apply"}
    text = Path(SC.__file__).read_text(encoding="utf-8")
    consts = {n.value for n in ast.walk(ast.parse(text)) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    # 〔段 4 の下ごしらえ・親の裁定 L-7〕前は字面の startswith("shibuya.engine")。名は、静的の検査が名を引くモジュール(resolve)の
    # 元の包み(engine)にあったモジュールの今の名から作る(移す前の木では "shibuya.engine" と同じ範囲)
    # 〔割る段 6 の S6-G0・親の裁定 Q10〕範囲の手がかりは、元の置き場が engine の、割らずに移したモジュール(前は resolve=割る段 6
    # で包み engine が無くなる。付け替えの前と後で範囲は同じ)。resolve の口を持つモジュールはその範囲に在る
    from shibuya.act import intent as ENGINE

    engine = PL.names_from(ENGINE)
    assert engine.heads and home in engine.leaves and SC.__name__ in engine.leaves
    assert not {c for c in consts if c.startswith(engine.prefixes())}, "道の文字列が残っている"


# ================================================================= 2-4
def test_rng_audit_names_come_from_the_rng_module():
    assert RA.RNG_MODULE == RNG.__name__
    assert RA._RNG_TAIL == RNG.__name__.partition(".")[2]
    text = Path(RA.__file__).read_text(encoding="utf-8")
    consts = {n.value for n in ast.walk(ast.parse(text)) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    assert not {"core.rng", "shibuya.foundation.rng", "core", "rng"} & consts


@pytest.mark.parametrize("moved", [None, "shibuya.foundation.rng"])
def test_rng_aliases_follow_the_module_name(monkeypatch, moved):
    """置き場を替えたふり(名だけ替える)でも、3 つの import の形の呼び手を見つける。"""
    name = moved or RNG.__name__
    if moved:
        tail = name.partition(".")[2]
        monkeypatch.setattr(RA, "RNG_MODULE", name)
        monkeypatch.setattr(RA, "_RNG_TAIL", tail)
        monkeypatch.setattr(RA, "_RNG_PARENT_TAIL", tail.rpartition(".")[0])
        monkeypatch.setattr(RA, "_RNG_LEAF", tail.rpartition(".")[2])
    parent, _, leaf = name.rpartition(".")
    code = (f"from {name} import stream as _s\n"
            f"from {parent} import {leaf} as R\n"
            f"import {name} as X\n")
    names, mods = RA._rng_aliases(ast.parse(code))
    assert names == {"_s": "stream"}
    assert mods == {"R", "X"}


# ================================================================= 2-5
def test_world_catalog_package_name_comes_from_the_module():
    assert WC._RESOURCE_PACKAGE == WC.__name__.rpartition(".")[0]
    cat = WC.load_world_catalog()
    WC.verify_frozen(cat)
    text = Path(WC.__file__).read_text(encoding="utf-8")
    consts = {n.value for n in ast.walk(ast.parse(text)) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    # 〔段 4 の下ごしらえ・親の裁定 L-7〕包みの名は字面で持たずモジュールの __name__ から(前は "shibuya.manifest")
    assert WC.__name__.rpartition(".")[0] not in consts
