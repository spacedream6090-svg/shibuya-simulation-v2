"""元の置き場で範囲を決める道具(試験の補助・段 4=コードの区分の移動の下ごしらえ)。

段 4 では src のファイルが別の包みへ移る(対応表 ``tools/pkgmove/map.toml``=全ファイルの表から作った「今の道 → 新しい道」)。
「包み X のモジュール」「包み X を読まない」を確かめる試験が包みの名やディレクトリを字面で持つと、移した後に空回りする
(ディレクトリが空になり、走査するファイルが減る)か、黙って別の確かめに変わる(包みの名は中のファイルが 2 つ以上の包みへ
分かれるので、行き先が 1 つに決まらない=移す道具は包みの名を書き換えない)。

ここでは範囲を「移す前に包み X にあったモジュール」(元の置き場)で決め、今の名と今のファイルを対応表で引く。

- 包みは、その包みにある(あった)モジュールを 1 つ import して渡す(:func:`origin_dir`)。包みの名を字面で持たない。
- 木にあるほうの道を使う: 移す前の木では古い道、移した後の木では新しい道(段の途中でも同じ)。新しい道にファイルがあり、
  古い道にファイルが無ければ、そのファイルの元の置き場は古い道。それ以外のファイルは今の道がそのまま元の置き場
  (古い置き場に空にして残した頭・段 4 で足す空の頭・表に無いファイル)。
- 移す前の木では、元の置き場=今の置き場なので、どの関数も前の字面の確かめと同じ範囲を返す。

逐次ループ宣言: なし(試験の補助)。
"""

from __future__ import annotations

import ast
import tomllib
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "src" / "shibuya"
MAP = ROOT / "tools" / "pkgmove" / "map.toml"


def module_of(rel: str) -> str:
    """``src/shibuya`` からの道 → モジュールの名(``__init__.py`` は包みの名)。"""
    parts = rel.removesuffix(".py").split("/")
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join([PKG.name, *parts])


#: 対応表の形の名(``tools/pkgmove/table.py`` の ``MAP_SCHEMA`` と同じ。違えば読まずに止める)。
MAP_SCHEMA = "shibuya.tools/pkgmove/map/1"


#: 表に行を足す手順(``PlacesMapError`` の文に添える)。〔再検収 M-4〕段 4 の終わりに範囲を新しい包みへ移すまでは、新しい
#: ファイルの行を move の形で書く決まり(道が変わらない行で載せると、元の置き場で決める範囲から黙って外れる)。〔L-8・L-9〕
#: 道が変わらない行=move でない行(keep・split・delete・empty)と old と new が同じ move の行・old は偽らない。
#: ``tools/c8/c8lib.py`` の ``PLACES_ADD_ROW_HELP`` と同じ文(``tests/c8/test_places_rule_copies.py`` が確かめる)。
ADD_ROW_HELP = (
    "src にファイルを足したら、全ファイルの表 docs/reference/package-map-final-2026-11-09-files.md に行を足し、"
    "python tools/pkgmove/cli.py map で tools/pkgmove/map.toml を作り直す(手で書かない)。"
    "段 4 の終わりに範囲を新しい包みへ移すまでは、新しいファイルの行は move の形で書く"
    "(old=移す前の置き場に在ったとしたらの道=どの範囲の守りを受けるかを決める道・new=今の道)。"
    "old は範囲を決める道なので偽らない(そのファイルが受けるはずの範囲の外の置き場=例えば build を書かない)。"
    "道が変わらない行(keep・split・delete・empty か、old と new が同じ move)は、移す前から在って動かない置き場"
    "(build・economy の直下など)に足すときだけにし、tests/test_places_guard.py の固定の一覧にも足す")


class PlacesMapError(AssertionError):
    """対応表が今の木を説明しない(空・形が違う・古い)。試験を黙って通さず落とす(検収 M-2)。

    〔再検収 M-3〕落ちるのは元の置き場を使う試験だけ(試験のモジュールの読み込みの時点では表を引かない=範囲の試験の全体の収集は
    止まらない)。"""


def origins_from(map_text: str, pkg: Path) -> dict[str, str]:
    """対応表の中身と包みの根 → 今の木の全部の ``.py``(``pkg`` からの道)→ 元の道。

    〔検収 M-2〕表を確かめてから使う: 形の名が :data:`MAP_SCHEMA`・行が空でない・どの行にも ``old`` と ``kind`` があり、
    ``move`` の行には ``new`` がある。さらに **今の木の ``.py`` は、表の ``old`` か ``move`` の ``new`` のどちらかに必ず在る**
    (どちらにも無くてよいのは 0 バイトの ``__init__.py``=段 4 で足す空の頭だけ)。外れたら :class:`PlacesMapError`
    (空や古い表で範囲が黙って縮むのを止める)。
    """
    try:
        doc = tomllib.loads(map_text)
    except tomllib.TOMLDecodeError as e:
        raise PlacesMapError(f"対応表を読めない: {e}") from e
    if doc.get("schema") != MAP_SCHEMA:
        raise PlacesMapError(f"対応表の形の名が違う: {doc.get('schema')!r}(想定 {MAP_SCHEMA!r})")
    rows = doc.get("row")
    if not isinstance(rows, list) or not rows:
        raise PlacesMapError("対応表に行が無い")
    olds: set[str] = set()
    moved: dict[str, str] = {}
    for i, r in enumerate(rows):
        if not isinstance(r, dict) or not isinstance(r.get("old"), str) or not isinstance(r.get("kind"), str):
            raise PlacesMapError(f"対応表の {i} 行目に old か kind が無い: {r!r}")
        olds.add(r["old"])
        if r["kind"] == "move":
            if not isinstance(r.get("new"), str):
                raise PlacesMapError(f"対応表の {i} 行目(move)に new が無い: {r!r}")
            if r["old"].endswith(".py"):
                moved[r["new"]] = r["old"]
    out: dict[str, str] = {}
    unknown: list[str] = []
    for p in sorted(pkg.rglob("*.py")):
        if "__pycache__" in p.parts:
            continue
        rel = p.relative_to(pkg).as_posix()
        if rel not in olds and rel not in moved and not (p.name == "__init__.py" and p.stat().st_size == 0):
            unknown.append(rel)
        old = moved.get(rel)
        out[rel] = old if old is not None and not (pkg / old).is_file() else rel
    if unknown:
        raise PlacesMapError(f"対応表に無い(old にも move の new にも無い)ファイル {len(unknown)} 本: {unknown[:10]}"
                             f"(表が古いか空。{ADD_ROW_HELP})")
    return out


@cache
def origins() -> dict[str, str]:
    """今の木の全部の ``.py``(``src/shibuya`` からの道)→ 元の道(:func:`origins_from` で表を確かめてから)。"""
    return origins_from(MAP.read_text(encoding="utf-8"), PKG)


def rel_of(mod: ModuleType) -> str:
    """モジュールの今の道(``src/shibuya`` からの相対)。"""
    return Path(mod.__file__).resolve().relative_to(PKG.resolve()).as_posix()


def origin_of(rel: str) -> str:
    """今の道 → 元の道。"""
    return origins()[rel]


def current_index(org: dict[str, str]) -> dict[str, str]:
    """「今の道 → 元の道」から「元の道 → 今の道」の索引を作る。〔再検収 L-7〕2 つの今のファイルが同じ元の道を持てば止める
    (どちらを返すかが決まらない)。"""
    back = {v: k for k, v in org.items()}
    assert len(back) == len(org), f"元の道が重なる今のファイルがある: {sorted(o for o in back if list(org.values()).count(o) > 1)}"
    return back


def current_of(old: str) -> str:
    """元の道 → 今の道(``.py`` だけ。移す前の木では同じ道。今の木に無い元の道は ``KeyError``)。src の宣言の文などが元の道で
    書くファイルを、今の木で引くのに使う。"""
    return current_index(origins())[old]


def declared_path_now(rel: str, org: dict[str, str] | None = None, pkg: Path | None = None) -> str:
    """src の宣言の文が書く ``.py`` の道(``src/shibuya`` からの相対)→ 今の木の道。

    〔再検収 L-6〕**表の元の道として引ければ今の道へ。引けなければ、その道が今の木に在るか**の順で引く(段 4 の後に新しい道で
    書いた宣言も通る。元の道を先に引くので、移したファイルの古い道に別のファイルが在っても、元のファイルを指す)。どちらでも
    なければ ``KeyError``。``org``・``pkg`` は既定で今の木(試験が作った索引と木を渡すため)。"""
    org = origins() if org is None else org
    pkg = PKG if pkg is None else pkg
    back = current_index(org)
    if rel in back:
        return back[rel]
    if (pkg / rel).is_file():
        return rel
    raise KeyError(rel)


def origin_dir(mod: ModuleType) -> str:
    """モジュールの元の置き場のディレクトリ(``src/shibuya`` からの相対・末尾に ``/``。根なら空)。"""
    d = origin_of(rel_of(mod)).rpartition("/")[0]
    return d + "/" if d else ""


def rels_from(*mods: ModuleType, recursive: bool = True) -> list[str]:
    """元の置き場が ``mods`` の元のディレクトリ(``recursive`` なら下の包みも)にある、今のファイルの道(並べたもの)。"""
    dirs = {origin_dir(m) for m in mods}
    assert "" not in dirs, "根のモジュールは包みの代わりにならない(module_names を使う)"
    out = []
    for rel, old in origins().items():
        d = old.rpartition("/")[0] + "/"
        if any(d == x or (recursive and d.startswith(x)) for x in dirs):
            out.append(rel)
    return sorted(out)


def files_from(*mods: ModuleType, recursive: bool = True) -> list[Path]:
    """:func:`rels_from` の今のファイル。"""
    return [PKG / r for r in rels_from(*mods, recursive=recursive)]


@dataclass(frozen=True)
class Names:
    """モジュールの名の集まり。頭(包み)は名の一致だけ、頭でないモジュールは中の名(``mod.名``)も含む。"""

    heads: frozenset[str]
    leaves: frozenset[str]

    def __or__(self, other: "Names") -> "Names":
        return Names(self.heads | other.heads, self.leaves | other.leaves)

    def has(self, name: str) -> bool:
        return name in self.heads or name in self.leaves or any(name.startswith(m + ".") for m in self.leaves)

    def hits(self, name: str) -> bool:
        """層の試験の違反: :meth:`has` か、木のどのモジュールにも包みにも解けない ``shibuya.`` の名(:func:`unknown`)。

        〔検収 L-1〕前の字面の前方一致は、無いモジュールの名(``shibuya.economy.zz_future``)も拾っていた。元の置き場で引く
        と、無い名はどの包みにも入らないので、強い側(違反)に倒す。"""
        return self.has(name) or unknown(name)

    def prefixes(self) -> tuple[str, ...]:
        """前の字面の ``startswith`` の代わり(文字列の定数に名の前の部分が残っていないかを見る)。"""
        return tuple(sorted(self.heads | self.leaves))


def names_from(*mods: ModuleType, recursive: bool = True) -> Names:
    """元の置き場が ``mods`` の元のディレクトリにある、今のモジュールの名。"""
    rels = rels_from(*mods, recursive=recursive)
    return Names(frozenset(module_of(r) for r in rels if r.endswith("__init__.py")),
                 frozenset(module_of(r) for r in rels if not r.endswith("__init__.py")))


def module_names(*mods: ModuleType) -> Names:
    """モジュールそのものの名(包みの代わりでなく 1 本ずつ)。"""
    return Names(frozenset(), frozenset(m.__name__ for m in mods))


@cache
def tree_modules() -> frozenset[str]:
    """今の木の全部のモジュールの名(包みの頭を含む)。"""
    return frozenset(module_of(r) for r in origins())


def unknown(name: str) -> bool:
    """``shibuya.`` で始まるのに、木のどのモジュールにも包みにも解けない名(:func:`imported` が返す名に使う)。"""
    return name.startswith(PKG.name + ".") and name not in tree_modules()


@cache
def _rel_by_module() -> dict[str, str]:
    return {module_of(r): r for r in origins()}


def origin_module(name: str) -> str:
    """今のモジュールの名 → 元の置き場のモジュールの名(木に無い名=``shibuya`` の外など はそのまま)。"""
    rel = _rel_by_module().get(name)
    return module_of(origin_of(rel)) if rel is not None else name


def imported(node: ast.AST) -> list[str]:
    """import の文が読むモジュール: ``import a.b`` は ``a.b``。``from P import c`` は、``P.c`` が木のモジュール(子の
    モジュールか子の包み)なら ``P.c``、そうでなければ ``P``(``P`` の中の名を読む)。相対の import は数えない。

    〔段 4〕``from <新しい包み> import <移したモジュール>`` の形では、新しい包みの頭(空の頭)ではなく、読む子のモジュールで
    元の置き場を引く。移す前の木では、前の「``node.module`` の前方一致」と同じ範囲か、それより広い(``from shibuya import X``
    の ``X`` も見る)。"""
    if isinstance(node, ast.Import):
        return [a.name for a in node.names]
    if isinstance(node, ast.ImportFrom) and node.module and not node.level:
        mods = tree_modules()
        return [f"{node.module}.{a.name}" if f"{node.module}.{a.name}" in mods else node.module for a in node.names]
    return []
