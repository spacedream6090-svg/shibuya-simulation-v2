"""元の置き場の規則の写し 2 か所が同じ答えを返すこと(再検収 第 3 回 5 の (2))。

``tests/_places.origins_from`` と ``tools/c8/c8lib.src_origins`` は、同じ規則(対応表 ``tools/pkgmove/map.toml`` を確かめて、
今の道 → 元の道)の写し。tools は tests を読まないので写しのまま置き(どちらも範囲を新しい包みへ移すまでの物)、ここで
**今の木で対応が完全に一致すること・同じ作った木と表で同じ答えを返すこと・空や古い表でどちらも止まること**を固定する。

逐次ループ宣言: なし。
"""

from __future__ import annotations

import pytest

from tests import _places as PL

HEAD = f'schema = "{PL.MAP_SCHEMA}"\n'


def _row(old: str, kind: str, new: str | None = None) -> str:
    return f'\n[[row]]\nold = "{old}"\nkind = "{kind}"\n' + (f'new = "{new}"\n' if new is not None else "")


#: 作った木と同じ答えを返すはずの表(keep・move・移す前の置き場に在ったとしたらの道の move・中身のある頭の keep)。
GOOD = (HEAD + _row("a.py", "keep", "a.py") + _row("x.py", "move", "sub/x.py") + _row("hd/__init__.py", "keep", "hd/__init__.py")
        + _row("before/y.py", "move", "y_new.py"))

#: どちらも止まるはずの表(空・形の名が違う・読めない・行の鍵が違う・move に new が無い・1 行欠けた=古い)と、それぞれの
#: 止まった理由(``tests/_places`` の文・``c8lib`` の文)。〔再検収 L-10〕理由まで見る(別の確かめで止まっても通さない)。
BAD = {
    "empty": (HEAD + "row = []\n", "行が無い", "形の名か行が違う"),
    "schema": ('schema = "other/1"\n' + GOOD[len(HEAD):], "形の名が違う", "形の名か行が違う"),
    "unreadable": ("row = [\n", "読めない", "読めない"),
    "keys": (GOOD.replace('\nold = "a.py"', '\nsrc = "a.py"'), "old か kind が無い", "old か kind が無い"),
    "move_without_new": (GOOD.replace('kind = "move"\nnew = "sub/x.py"\n', 'kind = "move"\n'), "new が無い", "new が無い"),
    "stale": (GOOD.replace(_row("before/y.py", "move", "y_new.py"), ""), r"対応表に無い.*y_new\.py",
              r"対応表に無いファイル.*y_new\.py"),
}


@pytest.fixture()
def tree(tmp_path):
    pkg = tmp_path / "pkg"
    for rel, text in {"a.py": "A = 1\n", "sub/x.py": "X = 1\n", "sub/__init__.py": "", "hd/__init__.py": '"""頭。"""\n',
                      "y_new.py": "Y = 1\n"}.items():
        (pkg / rel).parent.mkdir(parents=True, exist_ok=True)
        (pkg / rel).write_text(text, encoding="utf-8")
    return pkg


def _c8(c8lib, tmp_path, text, pkg):
    mp = tmp_path / "map.toml"
    mp.write_text(text, encoding="utf-8")
    return c8lib.src_origins(mp, pkg)


def test_both_copies_give_the_same_answer_on_the_current_tree(c8lib):
    got = c8lib.src_origins()
    assert got == PL.origins_from(PL.MAP.read_text(encoding="utf-8"), PL.PKG) == PL.origins()
    assert len(got) > 300


def test_both_copies_share_the_schema_and_the_help(c8lib):
    assert c8lib.PLACES_MAP_SCHEMA == PL.MAP_SCHEMA
    assert c8lib.PLACES_ADD_ROW_HELP == PL.ADD_ROW_HELP
    assert c8lib.SRC_PKG.resolve() == PL.PKG.resolve() and c8lib.PLACES_MAP.resolve() == PL.MAP.resolve()


def test_both_copies_give_the_same_answer_on_a_made_tree(c8lib, tmp_path, tree):
    want = {"a.py": "a.py", "hd/__init__.py": "hd/__init__.py", "sub/__init__.py": "sub/__init__.py",
            "sub/x.py": "x.py", "y_new.py": "before/y.py"}
    assert PL.origins_from(GOOD, tree) == want
    assert _c8(c8lib, tmp_path, GOOD, tree) == want
    # 移した行の古い道にまだファイルが在れば、元の置き場は今の道(どちらも同じ)
    (tree / "x.py").write_text("X0 = 1\n", encoding="utf-8")
    assert PL.origins_from(GOOD, tree) == _c8(c8lib, tmp_path, GOOD, tree)
    assert PL.origins_from(GOOD, tree)["sub/x.py"] == "sub/x.py" and PL.origins_from(GOOD, tree)["x.py"] == "x.py"


@pytest.mark.parametrize("case", sorted(BAD))
def test_both_copies_stop_on_the_same_bad_maps(c8lib, tmp_path, tree, case):
    text, why_places, why_c8 = BAD[case]
    if case == "move_without_new":
        # 〔再検収 L-10〕古い道のファイルだけを置く(new の無い move の行を読み飛ばしても、ほかの確かめでは止まらない木)
        (tree / "sub" / "x.py").unlink()
        (tree / "x.py").write_text("X = 1\n", encoding="utf-8")
        good_without_x = GOOD.replace(_row("x.py", "move", "sub/x.py"), _row("x.py", "keep", "x.py"))
        assert PL.origins_from(good_without_x, tree) == _c8(c8lib, tmp_path, good_without_x, tree)
    with pytest.raises(PL.PlacesMapError, match=why_places):
        PL.origins_from(text, tree)
    with pytest.raises(RuntimeError, match=why_c8):
        _c8(c8lib, tmp_path, text, tree)


def test_both_copies_stop_on_a_file_without_a_row(c8lib, tmp_path, tree):
    """表に無いファイル(中身のある新しい頭・新しいファイル)はどちらも止まり、0 バイトの新しい頭はどちらも受ける。"""
    (tree / "new_pkg").mkdir()
    (tree / "new_pkg" / "__init__.py").write_bytes(b"")
    assert PL.origins_from(GOOD, tree) == _c8(c8lib, tmp_path, GOOD, tree)
    (tree / "new_pkg" / "__init__.py").write_text('"""頭。"""\n', encoding="utf-8")
    with pytest.raises(PL.PlacesMapError, match="new_pkg/__init__.py"):
        PL.origins_from(GOOD, tree)
    with pytest.raises(RuntimeError, match="new_pkg/__init__.py"):
        _c8(c8lib, tmp_path, GOOD, tree)
