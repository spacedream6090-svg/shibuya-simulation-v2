"""移す段 2-1(返事その 7 §4-2 の 3・計画 docs/reference/package-map-final-2026-11-09.md §7-2): 名前を変えてはいけない文字列。

見た目はモジュールの道だが中身は ID の文字列(乱数の領域の名・版の ID・ハッシュと指紋の見出し・manifest の節の名・
塩)を ``names_frozen.json`` に凍結した。移す道具が機械で書き換えると乱数の列やハッシュが変わるので、src の AST を見て
同じことを確かめる(道と行の番号は鍵にしない=ファイルを動かしても通る)。

- 乱数の領域の名の 3 つの表の鍵の集合・版の ID の多重集合・ハッシュの見出しの多重集合は、集めたものが凍結と同じ。
- 道の形の乱数の領域の名・接尾・ほかの名は、値が src(build の外)の定数にあること(道によらず値で引く)。

凍結の作り方は ``docs/bench/analysis/move-346/tools/gen_frozen_names.py``(ここは別の実装で集める)。
"""

from __future__ import annotations

import ast
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PKG = ROOT / "src" / "shibuya"
FROZEN = json.loads(Path(__file__).with_name("names_frozen.json").read_text(encoding="utf-8"))
ID_STR = re.compile(r"^shibuya\.[A-Za-z0-9_.]+/")
ID_BYTES = re.compile(rb"^shibuya\.[A-Za-z0-9_.]+/")


def _sources(with_build: bool) -> list[ast.Module]:
    return [ast.parse(p.read_text(encoding="utf-8")) for p in sorted(PKG.rglob("*.py"))
            if with_build or p.relative_to(PKG).parts[0] != "build"]


def _literals(trees: list[ast.Module]) -> list[str | bytes]:
    """文字列とバイト列の定数(docstring を除く)。"""
    out: list[str | bytes] = []
    for tree in trees:
        doc = set()
        for n in ast.walk(tree):
            body = getattr(n, "body", None)
            if (isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and body
                    and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant)):
                doc.add(id(body[0].value))
        out += [n.value for n in ast.walk(tree)
                if isinstance(n, ast.Constant) and isinstance(n.value, (str, bytes)) and id(n) not in doc]
    return out


def _top_dict_keys(trees: list[ast.Module], name: str) -> list[list[str]]:
    found = []
    for tree in trees:
        for n in tree.body:
            targets = n.targets if isinstance(n, ast.Assign) else [n.target] if isinstance(n, ast.AnnAssign) else []
            if any(isinstance(t, ast.Name) and t.id == name for t in targets) and isinstance(n.value, ast.Dict):
                found.append([k.value for k in n.value.keys if isinstance(k, ast.Constant)])
    return found


RUN_SIDE = _sources(with_build=False)
EVERY = _sources(with_build=True)
RUN_LITERALS = set(_literals(RUN_SIDE))


def test_frozen_file_has_the_declared_shape():
    assert FROZEN["schema"] == "shibuya.tests/move/names-frozen/1"
    assert set(FROZEN) == {"schema", "note", "rng_domains", "rng_domains_path_shaped", "rng_domain_suffixes",
                           "version_ids", "hash_headers", "other_path_shaped"}
    assert sum(len(v) for v in FROZEN["rng_domains"].values()) == 41  # 計画の 42 から第346 で conversation.invite を消した


def test_rng_domain_tables_keep_their_keys():
    for name, keys in FROZEN["rng_domains"].items():
        found = _top_dict_keys(RUN_SIDE, name)
        assert len(found) == 1, f"{name} の定義が {len(found)} 個"
        assert sorted(found[0]) == keys, f"{name} の鍵が凍結と違う(乱数の領域の名は変えない)"


def test_path_shaped_rng_domains_are_kept_by_value():
    keys = {k for v in FROZEN["rng_domains"].values() for k in v}
    suffixes = FROZEN["rng_domain_suffixes"]
    assert set(suffixes) <= RUN_LITERALS, "接尾の文字列が src に無い"
    for name in FROZEN["rng_domains_path_shaped"]:
        assert name in keys, f"{name} が乱数の領域の名の表に無い"
        literal = name in RUN_LITERALS
        composed = any(name.endswith(s) and name[: -len(s)] in RUN_LITERALS for s in suffixes)
        assert literal or composed, f"{name} を定数(か定数+接尾)として持つ所が src に無い"


def test_version_ids_are_the_frozen_multiset():
    got = sorted(["b", c.decode("utf-8")] if isinstance(c, bytes) else ["s", c] for c in _literals(EVERY)
                 if (ID_BYTES if isinstance(c, bytes) else ID_STR).match(c))
    want = FROZEN["version_ids"]
    assert Counter(map(tuple, got)) == Counter(map(tuple, want)), (
        f"版の ID が変わった: 足りない {sorted(set(map(tuple, want)) - set(map(tuple, got)))[:5]}・"
        f"新しい {sorted(set(map(tuple, got)) - set(map(tuple, want)))[:5]}(足したら理由を記録に書いて更新する)")


def test_hash_headers_are_the_frozen_multiset():
    got = sorted(c.decode("utf-8") for c in _literals(EVERY) if isinstance(c, bytes) and c.startswith(b"shibuya."))
    assert got == FROZEN["hash_headers"]


def test_other_path_shaped_names_are_kept_by_value():
    missing = [v for v in FROZEN["other_path_shaped"] if v not in RUN_LITERALS]
    assert not missing, f"道と同じ形の名が src から消えた(書き換えた?): {missing}"
