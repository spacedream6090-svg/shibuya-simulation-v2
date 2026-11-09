"""移す段 1(固定の表): ``src/shibuya/engine/class_ids.py`` と凍結の JSON を src の AST から作る道具(冪等)。

    python docs/bench/analysis/move-346/tools/gen_class_ids.py            # 書く
    python docs/bench/analysis/move-346/tools/gen_class_ids.py --check    # 今のファイルが作り直しと同じか(違えば 1)

- 正: 返事その 7 §4-2 の 3・計画 ``docs/reference/package-map-final-2026-11-09.md`` §7-1。記録
  ``docs/bench/analysis/move-346/README.md``。
- 集めるもの: ``src/shibuya`` の ``build/`` を除く全部の ``.py`` の全部のクラス(AST の ``ClassDef``。入れ子のクラスは
  ``外.内``・関数の中のクラスは ``関数.<locals>.クラス`` の形=Python の ``__qualname__`` と同じ)。鍵は
  「モジュール.クラス名」(``__init__.py`` はパッケージの名)。
- 自分の置き場で凍結の名を宣言するクラス(クラスの本体の ``CLASS_ID = "…"``=:data:`DECLARED_ATTR`)は表に載せない。
  今は CP12 の実験の条件の型 1 つ(型の名を ``engine/events/log.py`` と ``engine/experiment/gate.py`` の外の src に文字列で
  書けない=表に書けない。検収 M1)。``class_id`` は表の次にこの宣言を読む。
- 値(凍結の名)は足すだけで変えない: 今の ``class_ids.py`` に載っている鍵は今の値を引き継ぎ、新しい鍵は値=鍵で足す。
  消えたクラスの行は落とす(落とした鍵は標準出力に出す)。段 1 では全部の値=鍵。
- 書くもの: ``src/shibuya/engine/class_ids.py``(表と ``class_id``・``class_path``)と
  ``tests/engine/state/class_ids_frozen.json``(凍結の名 → ``__qualname__`` の写像=検収 M3。宣言の分を含む)。
- 確かめ: 関数の中でないクラスは、モジュールを import して ``__module__`` と ``__qualname__`` が鍵と同じか、宣言の値が
  AST と同じかを見る(違えば止める)。関数の中のクラスは import では引けないので AST の名だけ(数を標準出力に出す)。
- 段 4 では移す道具がこの表の鍵だけを書き換える(値は変えない)。この道具は鍵=今の置き場で作り直す
  (値は今のファイルから引き継ぐ)ので、段 4 の後も ``--check`` で表と src のずれを見られる。
"""
from __future__ import annotations

import argparse
import ast
import importlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
SRC = REPO / "src"
PKG = SRC / "shibuya"
OUT_PY = PKG / "engine" / "class_ids.py"
OUT_JSON = REPO / "tests" / "engine" / "state" / "class_ids_frozen.json"
SKIP_TOP = ("build",)
#: 自分の置き場で凍結の名を宣言するクラスの属性の名(``class_ids.DECLARED_ATTR`` と同じ)。
DECLARED_ATTR = "CLASS_ID"

JSON_SCHEMA = "shibuya.tests/move/class-ids-frozen/2"
JSON_NOTE = (
    "クラスの凍結の名 → __qualname__(src/shibuya/engine/class_ids.py の CLASS_IDS の値と、自分の置き場で CLASS_ID を宣言する"
    "クラスの値)。移す段 1(返事その 7 §4-2 の 3・計画 docs/reference/package-map-final-2026-11-09.md §7-1・検収 M3)。"
    "値はハッシュ・状態のファイル・設定の指紋・系ごとの指紋に入る文字列なので変えない。クラスを足したら表と一緒にここにも"
    "足す(道具 docs/bench/analysis/move-346/tools/gen_class_ids.py)。クラスを消したら両方から消す。"
)

HEAD = '''"""engine.class_ids — クラスの名の固定の表(移す段 1・返事その 7 §4-2 の 3)。

クラスの「モジュール.クラス名」は、ハッシュ(``engine.state_hashes`` の Enum・dataclass・名前つきの組・値のクラス)・
状態のファイル(``engine.state_codec`` の ``__o``)・設定の指紋(``engine.resume._canon``)・系ごとの指紋
(``engine.systems.probe`` の ``plain`` と外の状態の digest)に入る。置き場を動かすと名が変わり final が変わるので、名は
本表から引く。

- 鍵=今の「モジュール.クラス名」、値=凍結の名(上の 4 か所に入る文字列)。段 1 では鍵と値が同じ。移す道具が鍵だけを
  書き換え、値は変えない。
- 表は src(``build/`` を除く)の全部のクラス(関数の中のクラスを含む)。表に書けないクラス(CP12 の実験の条件の型=名を
  ``engine/events/log.py`` と ``engine/experiment/gate.py`` の外に文字列で書けない)は、自分の置き場でクラスの属性
  :data:`DECLARED_ATTR` に凍結の名を宣言し、:func:`class_id` が表の次に読む。手で書かない: 道具
  ``docs/bench/analysis/move-346/tools/gen_class_ids.py`` が AST から作る(試験 ``tests/engine/state/test_class_ids.py``
  が src と表と凍結の JSON を突き合わせる)。
- 表にも宣言にも無い ``shibuya`` の型(構築の段 ``shibuya.build`` を除く)は ``TypeError`` で止める(後から足した
  クラスを黙って今の名で流さない=検収 M2)。``shibuya`` の外の型(numpy・標準ライブラリ・試験の中のクラス)と構築の段の
  型は今の名をそのまま返す。

時間の方針: 本モジュールは時刻を持たない。逐次ループ宣言: なし(表を 1 回作るだけ)。
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Final, Mapping

__all__ = ["CLASS_IDS", "DECLARED_ATTR", "class_id", "class_path"]

#: 自分の置き場で凍結の名を宣言するクラスの属性の名(クラスの本体に ``CLASS_ID = "…"``。継いだ属性は読まない)。
DECLARED_ATTR: Final[str] = "CLASS_ID"
#: 表で守る包みの頭と、表に載せない構築の段の頭(包みの根の名から作る)。
_ROOT: Final[str] = __name__.partition(".")[0] + "."
_BUILD: Final[str] = _ROOT + "build."

#: クラスの名の固定の表。鍵=今の「モジュール.クラス名」、値=凍結の名(ハッシュ・状態のファイル・設定の指紋に入る文字列)。
#: 段 1 では鍵と値が同じ。移す道具が鍵だけを書き換え、値は変えない。
CLASS_IDS: Final[Mapping[str, str]] = MappingProxyType({
'''

TAIL = '''})
#: 凍結の名 → 今の「モジュール.クラス名」(状態のファイルを読むときに import する先)。
_PATH_OF: Final[Mapping[str, str]] = MappingProxyType({v: k for k, v in CLASS_IDS.items()})


def class_id(t: type) -> str:
    """型の凍結の名。表 → クラスの宣言(:data:`DECLARED_ATTR`)の順に引く。どちらにも無い ``shibuya`` の型は止める。"""
    name = f"{t.__module__}.{t.__qualname__}"
    got = CLASS_IDS.get(name)
    if got is not None:
        return got
    declared = t.__dict__.get(DECLARED_ATTR)
    if isinstance(declared, str):
        return declared
    if name.startswith(_ROOT) and not name.startswith(_BUILD):
        return _unknown(name)
    return name


def _unknown(name: str) -> str:
    """表にも宣言にも無い ``shibuya`` の型(試験が差し替えて数える口)。"""
    raise TypeError(f"class_ids: 表に無い shibuya の型 {name}(道具 docs/bench/analysis/move-346/tools/gen_class_ids.py "
                    "で表を作り直す)")


def class_path(frozen: str) -> str:
    """凍結の名 → 今の「モジュール.クラス名」(状態のファイルを読むときに import する先。表に無い名はそのまま)。"""
    return _PATH_OF.get(frozen, frozen)
'''


def module_name(p: Path) -> str:
    parts = list(p.relative_to(SRC).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def class_defs(tree: ast.AST) -> list[tuple[str, ast.ClassDef]]:
    """モジュールの中の全部のクラスの (``__qualname__``, 定義)(出てくる順)。"""
    out: list[tuple[str, ast.ClassDef]] = []

    def visit(node: ast.AST, prefix: str) -> None:
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, ast.ClassDef):
                q = f"{prefix}{ch.name}"
                out.append((q, ch))
                visit(ch, q + ".")
            elif isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef)):
                visit(ch, f"{prefix}{ch.name}.<locals>.")
            elif isinstance(ch, ast.Lambda):
                visit(ch, f"{prefix}<lambda>.<locals>.")
            else:
                visit(ch, prefix)

    visit(tree, "")
    return out


def declared_value(cls: ast.ClassDef) -> str | None:
    """クラスの本体の ``CLASS_ID = "…"``(注釈つきを含む)の値。"""
    for st in cls.body:
        tgt = st.target if isinstance(st, ast.AnnAssign) else (st.targets[0] if isinstance(st, ast.Assign)
                                                                 and len(st.targets) == 1 else None)
        if (isinstance(tgt, ast.Name) and tgt.id == DECLARED_ATTR and isinstance(st.value, ast.Constant)
                and isinstance(st.value.value, str)):
            return st.value.value
    return None


def collect() -> tuple[dict[str, str], dict[str, str], int]:
    """src(build を除く)の全部のクラス: (名 → ``__qualname__``, 宣言するクラスの名 → 凍結の名, クラスを持つファイルの数)。"""
    quals: dict[str, str] = {}
    declared: dict[str, str] = {}
    n_files = 0
    for p in sorted(PKG.rglob("*.py")):
        if p.relative_to(PKG).parts[0] in SKIP_TOP:
            continue
        mod = module_name(p)
        tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        found = class_defs(tree)
        n_files += bool(found)
        for q, node in found:
            name = f"{mod}.{q}"
            if name in quals:
                raise SystemExit(f"同じ名のクラスが 2 つある(表の鍵が重なる): {name}")
            quals[name] = q
            d = declared_value(node)
            if d is not None:
                declared[name] = d
    return dict(sorted(quals.items())), declared, n_files


def verify_runtime(quals: dict[str, str], declared: dict[str, str]) -> tuple[int, int]:
    """関数の中でないクラスを import して、名が鍵と同じか・宣言の値が AST と同じかを見る。(確かめた数, 関数の中の数)。"""
    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))
    checked = local = 0
    mods = sorted({module_name(p) for p in PKG.rglob("*.py") if p.relative_to(PKG).parts[0] not in SKIP_TOP},
                  key=len, reverse=True)
    for name in quals:
        if ".<locals>." in name:
            local += 1
            continue
        mod = next(m for m in mods if name.startswith(m + "."))
        obj = importlib.import_module(mod)
        for part in name[len(mod) + 1:].split("."):
            obj = getattr(obj, part)
        got = f"{obj.__module__}.{obj.__qualname__}"
        if not isinstance(obj, type) or got != name:
            raise SystemExit(f"AST の名と import した型の名が違う: {name} → {got}")
        if name in declared and obj.__dict__.get(DECLARED_ATTR) != declared[name]:
            raise SystemExit(f"宣言の値が AST と違う: {name}")
        checked += 1
    return checked, local


def current_values() -> dict[str, str]:
    """今の ``class_ids.py`` の表(無ければ空)。"""
    if not OUT_PY.is_file():
        return {}
    tree = ast.parse(OUT_PY.read_text(encoding="utf-8"))
    for n in tree.body:
        tgt = n.target if isinstance(n, ast.AnnAssign) else (n.targets[0] if isinstance(n, ast.Assign) else None)
        if isinstance(tgt, ast.Name) and tgt.id == "CLASS_IDS":
            d = n.value.args[0] if isinstance(n.value, ast.Call) else n.value
            return {ast.literal_eval(k): ast.literal_eval(v) for k, v in zip(d.keys, d.values)}
    raise SystemExit("class_ids.py に CLASS_IDS が無い")


def render(table: dict[str, str], frozen_to_qual: dict[str, str]) -> tuple[str, str]:
    lines = [f"    {json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)},\n" for k, v in table.items()]
    py = HEAD + "".join(lines) + TAIL
    js = json.dumps({"schema": JSON_SCHEMA, "note": JSON_NOTE, "names": dict(sorted(frozen_to_qual.items()))},
                    ensure_ascii=False, indent=1) + "\n"
    return py, js


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="書かずに、今のファイルが作り直しと同じかを見る")
    ap.add_argument("--no-import", action="store_true", help="import の確かめを飛ばす")
    a = ap.parse_args(argv)
    quals, declared, n_files = collect()
    names = [n for n in quals if n not in declared]
    old = current_values()
    table = {k: old.get(k, k) for k in names}
    dropped = sorted(set(old) - set(names))
    frozen_to_qual: dict[str, str] = {}
    for k, v in [*table.items(), *declared.items()]:
        if v in frozen_to_qual:
            raise SystemExit(f"凍結の名が重なる(1 対 1 でない): {v}")
        if not v.endswith("." + quals[k]):
            raise SystemExit(f"凍結の名の末尾がクラスの __qualname__ と違う: {k} → {v}")
        frozen_to_qual[v] = quals[k]
    if not a.no_import:
        checked, local = verify_runtime(quals, declared)
        print(f"import で確かめた {checked}・関数の中のクラス(AST の名だけ){local}")
    py, js = render(table, frozen_to_qual)
    print(f"クラス {len(quals)}(表 {len(table)}・置き場で宣言 {len(declared)})・クラスを持つファイル {n_files}・"
          f"新しい鍵 {len(set(names) - set(old))}・落とした鍵 {len(dropped)} {dropped}")
    if a.check:
        same = (OUT_PY.is_file() and OUT_PY.read_text(encoding="utf-8") == py
                and OUT_JSON.is_file() and OUT_JSON.read_text(encoding="utf-8") == js)
        print("同じ" if same else "違う(作り直しが要る)")
        return 0 if same else 1
    OUT_PY.write_text(py, encoding="utf-8", newline="\n")
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(js, encoding="utf-8", newline="\n")
    print(f"書いた: {OUT_PY.relative_to(REPO).as_posix()}・{OUT_JSON.relative_to(REPO).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
