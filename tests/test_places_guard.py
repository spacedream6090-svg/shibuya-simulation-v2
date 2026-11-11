"""``tests/_places.py`` の対応表の確かめ(検収 M-2)と、解けない名の扱い(検収 L-1)。

``tests/_places.py`` は、移す前と移した後の木で「元の置き場」を引くために道具の対応表 ``tools/pkgmove/map.toml`` を読む。
空や古い表を黙って受けると、層の試験の範囲が黙って縮む(検収の P03・P05)。表を読む所 ``origins_from`` が、形の名・行の
有無・行の鍵と、**今の木の ``.py`` が表の ``old`` か ``move`` の ``new`` に必ず在ること**を確かめて止めることを、負の対照で
確かめる。

逐次ループ宣言: なし。
"""

from __future__ import annotations

import pytest

from shibuya import cli
from tests import _places as PL

GOOD_HEAD = f'schema = "{PL.MAP_SCHEMA}"\n'


def _real_map() -> str:
    return PL.MAP.read_text(encoding="utf-8")


def test_the_real_map_explains_the_current_tree():
    got = PL.origins_from(_real_map(), PL.PKG)
    assert got == PL.origins()
    files = sorted(p.relative_to(PL.PKG).as_posix() for p in PL.PKG.rglob("*.py") if "__pycache__" not in p.parts)
    assert sorted(got) == files and len(files) > 300


@pytest.mark.parametrize("text,word", [
    (GOOD_HEAD + "row = []\n", "行が無い"),
    ('schema = "other/1"\n' + "row = []\n", "形の名"),
    ("row = [\n", "読めない"),
])
def test_an_empty_or_foreign_map_stops(text, word):
    with pytest.raises(PL.PlacesMapError, match=word):
        PL.origins_from(text, PL.PKG)


def test_a_map_with_renamed_row_keys_stops():
    text = _real_map().replace("\nold = ", "\nsrc = ")
    assert text != _real_map()
    with pytest.raises(PL.PlacesMapError, match="old か kind"):
        PL.origins_from(text, PL.PKG)


def test_a_map_missing_one_row_stops():
    """1 行欠けた(古い)表: 今の木にある ``cli.py`` の行を抜くと、``cli.py`` が表に無いファイルとして止まる。"""
    rel = PL.rel_of(cli)
    blocks = _real_map().split("\n[[row]]\n")
    keep = [b for b in blocks if f'\nold = "{rel}"\n' not in f"\n{b}\n"]
    assert len(keep) == len(blocks) - 1
    with pytest.raises(PL.PlacesMapError, match=rel):
        PL.origins_from("\n[[row]]\n".join(keep), PL.PKG)


def test_a_fake_tree_maps_moves_and_allows_only_empty_new_heads(tmp_path):
    pkg = tmp_path / "pkg"
    (pkg / "sub").mkdir(parents=True)
    (pkg / "a.py").write_text("A = 1\n", encoding="utf-8")
    (pkg / "sub" / "x.py").write_text("X = 1\n", encoding="utf-8")
    (pkg / "sub" / "__init__.py").write_bytes(b"")
    text = (GOOD_HEAD + '[[row]]\nold = "a.py"\nkind = "keep"\nnew = "a.py"\n\n'
            '[[row]]\nold = "x.py"\nkind = "move"\nnew = "sub/x.py"\n')
    assert PL.origins_from(text, pkg) == {"a.py": "a.py", "sub/__init__.py": "sub/__init__.py", "sub/x.py": "x.py"}
    (pkg / "sub" / "__init__.py").write_text('"""頭。"""\n', encoding="utf-8")  # 中身のある頭は表に要る
    with pytest.raises(PL.PlacesMapError, match="sub/__init__.py"):
        PL.origins_from(text, pkg)
    (pkg / "sub" / "__init__.py").write_bytes(b"")
    (pkg / "b.py").write_text("B = 1\n", encoding="utf-8")  # 表に無いファイル
    with pytest.raises(PL.PlacesMapError, match="b.py"):
        PL.origins_from(text, pkg)


def test_unresolvable_shibuya_names_are_hits():
    """検収 L-1: 木のどのモジュールにも包みにも解けない ``shibuya.`` の名は、層の試験の違反(``Names.hits``)。"""
    name = f"{PL.PKG.name}.{cli.__name__.rpartition('.')[2]}_zz_future"
    assert PL.unknown(name) and not PL.unknown(cli.__name__) and not PL.unknown(PL.PKG.name)
    empty = PL.Names(frozenset(), frozenset())
    assert empty.hits(name) and not empty.hits(cli.__name__) and not empty.has(name)
