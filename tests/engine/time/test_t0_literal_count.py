"""第 1 期 1-1 時計 T0: ``src/shibuya`` に時間の直書きが残っていない(AST で数える・残すものは allow の表に理由つき)。

数える形(発注の ``1440``・``86400``・``// 60``・``* 60``・``/ 60``・``% 1440`` に、同じ置き換えをした ``3600`` と
``% 60``・``24`` の演算を足した):

- 数値のリテラル ``1440``・``86400``・``3600``(``1_440``・``1440.0`` など書き方と int/float を問わない)。
- 二項演算と累算代入 ``//``・``*``・``/``・``%`` で、どちらかの項がリテラル ``60`` か ``24``(``60.0``・``24.0`` を含む)。

定数を定義する ``core/time_consts.py`` もほかと同じに数える(定義は名の積で書いてあり、当たる行は無い)。
allow の表 ``time_literal_allow.json`` は ``{"相対パス:行": "理由"}``(行は当たった式の行)。表の行が当たりを失ったら
落とす(古い行を残さない)。
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src" / "shibuya"
ALLOW = Path(__file__).with_name("time_literal_allow.json")

LITERALS = {1440, 86400, 3600}
OPERANDS = {60, 24}
OPS = {ast.FloorDiv: "//", ast.Mult: "*", ast.Div: "/", ast.Mod: "%"}


def _num(n: ast.AST) -> bool:
    return isinstance(n, ast.Constant) and type(n.value) in (int, float)


def scan_source(text: str) -> list[tuple[int, str]]:
    """``(行, 種類)`` の一覧。種類は ``lit 1440`` や ``// 60`` の形。"""
    out = []
    for node in ast.walk(ast.parse(text)):
        if _num(node) and node.value in LITERALS:
            out.append((node.lineno, f"lit {int(node.value)}"))
        if isinstance(node, (ast.BinOp, ast.AugAssign)) and type(node.op) in OPS:
            sides = [node.value] if isinstance(node, ast.AugAssign) else [node.left, node.right]
            for s in sides:
                if _num(s) and s.value in OPERANDS:
                    out.append((node.lineno, f"{OPS[type(node.op)]} {int(s.value)}"))
    return sorted(out)


def scan_tree(root: Path = SRC, base: Path = ROOT) -> dict[str, list[str]]:
    """``{"相対パス:行": [種類, …]}``(``base`` からの相対パス)。"""
    hits: dict[str, list[str]] = {}
    for p in sorted(root.rglob("*.py")):
        rel = p.relative_to(base).as_posix()
        for ln, kind in scan_source(p.read_text(encoding="utf-8")):
            hits.setdefault(f"{rel}:{ln}", []).append(kind)
    return hits


def test_no_time_literals_outside_the_allow_table():
    allow = json.loads(ALLOW.read_text(encoding="utf-8"))
    hits = scan_tree()
    outside = {k: v for k, v in hits.items() if k not in allow}
    assert outside == {}, f"時間の直書き(core.time_consts の名に置き換えるか、allow の表に理由つきで載せる): {outside}"


def test_allow_table_has_reasons_and_no_stale_rows():
    allow = json.loads(ALLOW.read_text(encoding="utf-8"))
    hits = scan_tree()
    assert all(isinstance(v, str) and v.strip() for v in allow.values()), allow
    stale = sorted(set(allow) - set(hits))
    assert stale == [], f"allow の表の行が当たりを失った(表から消す): {stale}"


def test_negative_control_detects_every_form(tmp_path):
    """負の対照: 仮のファイルに直書きを置くと、形ごとに見つかる(数え方が空回りしていない)。"""
    src = (
        "a = 1440\n"
        "b = 1_440.0\n"
        "c = 86_400 // w\n"
        "d = x // 60\n"
        "e = h * 60 + m\n"
        "f = s / 60.0\n"
        "g = t % 1440\n"
        "h = 60 % k\n"
        "i = [0] * 24\n"
        "j = 3_600.0\n"
        "k //= 60\n"
        "s = '1440 // 60'\n"  # 文字列の中は数えない
        "n = 60\n"  # 演算の項でない 60 は数えない
        "o = y + 60\n"  # 足し算は数えない
    )
    got = scan_source(src)
    want = [(1, "lit 1440"), (2, "lit 1440"), (3, "lit 86400"), (4, "// 60"), (5, "* 60"), (6, "/ 60"),
            (7, "lit 1440"), (8, "% 60"), (9, "* 24"), (10, "lit 3600"), (11, "// 60")]
    assert got == sorted(want), got
    d = tmp_path / "pkg"
    d.mkdir()
    (d / "m.py").write_text(src, encoding="utf-8")
    hits = scan_tree(d, base=tmp_path)
    assert sorted(hits) == sorted(f"pkg/m.py:{i}" for i in range(1, 12)), hits
    assert hits["pkg/m.py:7"] == ["lit 1440"]  # ``% 1440`` はリテラルの 1440 として見つかる


def test_time_consts_module_itself_has_no_hits():
    assert scan_source((SRC / "core" / "time_consts.py").read_text(encoding="utf-8")) == []
