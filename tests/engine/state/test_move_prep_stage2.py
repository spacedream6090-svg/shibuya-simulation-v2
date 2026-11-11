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
from pathlib import Path

import pytest

import shibuya
from shibuya.foundation import budget as BU
from shibuya.foundation import paths as P
from shibuya.foundation import rng as RNG
from shibuya.mind.judge import classical as CL
from shibuya.world.body import energy as EN
from shibuya.engine import resolve as RV
from shibuya.engine import resume as RS
from shibuya.engine import rng_audit as RA
from shibuya.foundation.decl import bridging as BL
from shibuya.engine.bridging import scan as BS
from shibuya.world.facts.rules import table as RT
from shibuya.engine.systems import allow as AL
from shibuya.engine.systems import static_check as SC
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
    assert AL.RESOLVE_FILES == ("engine/resolve.py",)
    assert [(AL.src_root() / rel).resolve() for rel in AL.RESOLVE_FILES] == [Path(RV.__file__).resolve()]
    idx = AL.index()
    tree = ast.parse(Path(RV.__file__).read_text(encoding="utf-8"))
    assert idx.funcs == frozenset(n.name for n in tree.body if isinstance(n, ast.FunctionDef))


def test_index_refuses_a_function_name_split_across_files(tmp_path, monkeypatch):
    root = tmp_path / "shibuya"
    (root / "engine").mkdir(parents=True)
    src = Path(RV.__file__).read_text(encoding="utf-8")
    (root / "engine" / "resolve.py").write_text(src, encoding="utf-8")
    (root / "engine" / "resolve_part.py").write_text("def apply_detection():\n    pass\n", encoding="utf-8")
    monkeypatch.setattr(AL, "RESOLVE_FILES", ("engine/resolve.py", "engine/resolve_part.py"))
    AL.index.cache_clear()
    try:
        with pytest.raises(ValueError, match="関数の名がファイルをまたいで重なる"):
            AL.index(str(root))
    finally:
        AL.index.cache_clear()


def _split_tree(tmp_path: Path, part: str) -> Path:
    """resolve.py と、割った先のふりのファイル 1 本と、``declared_columns`` が読むファイルを置いた木(``src/shibuya`` の形)。"""
    from shibuya.engine import state_ledger_ast as A

    root = tmp_path / "shibuya"
    (root / "engine").mkdir(parents=True)
    (root / "engine" / "resolve.py").write_text(Path(RV.__file__).read_text(encoding="utf-8"), encoding="utf-8")
    (root / "engine" / "resolve_part.py").write_text(part, encoding="utf-8")
    for rel in A.DECL_FILES.values():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text((PKG / rel).read_text(encoding="utf-8"), encoding="utf-8")
    return root


def test_index_refuses_a_table_name_split_across_files_and_merges_distinct_ones(tmp_path, monkeypatch):
    """〔検収 L2〕頂上の表の名(関数を指す代入)がファイルをまたいで重なれば止める。重ならなければ 2 本を 1 つの閉包にする。"""
    ref = AL.index().tables["_APPLY"]
    monkeypatch.setattr(AL, "RESOLVE_FILES", ("engine/resolve.py", "engine/resolve_part.py"))
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
    assert SC.RESOLVE_MODULE == RV.__name__
    # 系の包みの名は、系の包みで定義したモジュール(allow)の包みから作る(〔段 4 の下ごしらえ・親の決定 3〕包みの頭を読まない)
    assert SC._SYSTEMS_PREFIX == AL.__name__.rpartition(".")[0] + "."
    assert (SC._RESOLVE_PARENT, SC._RESOLVE_LEAF) == tuple(RV.__name__.rsplit(".", 1))
    text = Path(SC.__file__).read_text(encoding="utf-8")
    consts = {n.value for n in ast.walk(ast.parse(text)) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    # 〔段 4 の下ごしらえ・親の裁定 L-7〕前は字面の startswith("shibuya.engine")。名は、静的の検査が名を引くモジュール(resolve)の
    # 元の包み(engine)にあったモジュールの今の名から作る(移す前の木では "shibuya.engine" と同じ範囲)
    engine = PL.names_from(RV)
    assert engine.heads and RV.__name__ in engine.leaves and SC.__name__ in engine.leaves
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
