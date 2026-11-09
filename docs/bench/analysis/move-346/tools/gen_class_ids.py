"""移す段 1(固定の表): ``src/shibuya/engine/class_ids.py`` と凍結の JSON を src の AST から作る道具(冪等)。

    python docs/bench/analysis/move-346/tools/gen_class_ids.py            # 書く
    python docs/bench/analysis/move-346/tools/gen_class_ids.py --check    # 今のファイルが作り直しと同じか(違えば 1)

- 正: 返事その 7 §4-2 の 3・計画 ``docs/reference/package-map-final-2026-11-09.md`` §7-1。記録
  ``docs/bench/analysis/move-346/README.md``。
- 集めるもの: ``src/shibuya`` の ``build/`` を除く全部の ``.py`` の全部のクラス(AST の ``ClassDef``。入れ子のクラスは
  ``外.内``・関数の中のクラスは ``関数.<locals>.クラス`` の形=Python の ``__qualname__`` と同じ)。鍵は
  「モジュール.クラス名」(``__init__.py`` はパッケージの名)。
- 載せないクラス: :data:`EXCLUDE`(名と理由)。今は CP12 の実験の条件の型 1 つ(src に名を文字列で書けない・値はハッシュにも
  状態のファイルにも入らない)。一覧の名が src に無ければ止める。
- 値(凍結の名)は足すだけで変えない: 今の ``class_ids.py`` に載っている鍵は今の値を引き継ぎ、新しい鍵は値=鍵で足す。
  消えたクラスの行は落とす(落とした鍵は標準出力に出す)。段 1 では全部の値=鍵。
- 書くもの: ``src/shibuya/engine/class_ids.py``(表と ``class_id``・``class_path``)と
  ``tests/engine/state/class_ids_frozen.json``(値の一覧)。
- 確かめ: 関数の中でないクラスは、モジュールを import して ``__module__`` と ``__qualname__`` が鍵と同じかを見る
  (違えば止める)。関数の中のクラスは import では引けないので AST の名だけ(数を標準出力に出す)。
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
#: 表に載せないクラス(名 → 理由)。載せないクラスの ``class_id`` は今の名をそのまま返す。
EXCLUDE: dict[str, str] = {
    "shibuya.engine.events.log.Experiment": (
        "CP12(第 1 期 1-3): 実験の条件の型の名は engine/events/log.py と engine/experiment/gate.py の外の src に文字列で"
        "書けない(tests/engine/events/test_e_cause_three_kinds.py)。値はハッシュにも状態のファイルにも入らない(持つ行は"
        "状態台帳の E と X=軸 1 diag・軸 2 discardable)ので、置き場を動かしても final は変わらない"),
}

JSON_SCHEMA = "shibuya.tests/move/class-ids-frozen/1"
JSON_NOTE = (
    "クラスの凍結の名(src/shibuya/engine/class_ids.py の CLASS_IDS の値の集合・昇順)。移す段 1(返事その 7 §4-2 の 3・"
    "計画 docs/reference/package-map-final-2026-11-09.md §7-1)。値はハッシュ・状態のファイル・設定の指紋に入る文字列なので"
    "変えない。クラスを足したら表と一緒にここにも足す(道具 docs/bench/analysis/move-346/tools/gen_class_ids.py)。"
    "クラスを消したら両方から消す。"
)

HEAD = '''"""engine.class_ids — クラスの名の固定の表(移す段 1・返事その 7 §4-2 の 3)。

クラスの「モジュール.クラス名」は、ハッシュ(``engine.state_hashes`` の Enum・dataclass・名前つきの組・値のクラス)・
状態のファイル(``engine.state_codec`` の ``__o``)・設定の指紋(``engine.resume._canon``)・系ごとの指紋
(``engine.systems.probe.plain``)に入る。置き場を動かすと名が変わり final が変わるので、名は本表から引く。

- 鍵=今の「モジュール.クラス名」、値=凍結の名(上の 4 か所に入る文字列)。段 1 では鍵と値が同じ。移す道具が鍵だけを
  書き換え、値は変えない。
- 表は src(``build/`` を除く)の全部のクラス(関数の中のクラスを含む)。載せないのは CP12 の実験の条件の型 1 つだけ
  (``engine/events/log.py`` と ``engine/experiment/gate.py`` の外に名を文字列で書けない。値はハッシュにも状態のファイルにも
  入らない=今の名をそのまま返す)。手で書かない: 道具
  ``docs/bench/analysis/move-346/tools/gen_class_ids.py`` が AST から作る(試験 ``tests/engine/state/test_class_ids.py``
  が src と表と凍結の JSON を突き合わせる)。
- 表に無い型(numpy・標準ライブラリ・試験の中のクラス)は今の名をそのまま返す。

時間の方針: 本モジュールは時刻を持たない。逐次ループ宣言: なし(表を 1 回作るだけ)。
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Final, Mapping

__all__ = ["CLASS_IDS", "class_id", "class_path"]

#: クラスの名の固定の表。鍵=今の「モジュール.クラス名」、値=凍結の名(ハッシュ・状態のファイル・設定の指紋に入る文字列)。
#: 段 1 では鍵と値が同じ。移す道具が鍵だけを書き換え、値は変えない。
CLASS_IDS: Final[Mapping[str, str]] = MappingProxyType({
'''

TAIL = '''})
#: 凍結の名 → 今の「モジュール.クラス名」(状態のファイルを読むときに import する先)。
_PATH_OF: Final[Mapping[str, str]] = MappingProxyType({v: k for k, v in CLASS_IDS.items()})


def class_id(t: type) -> str:
    """型の凍結の名(表に無い型は今の「モジュール.クラス名」)。"""
    name = f"{t.__module__}.{t.__qualname__}"
    return CLASS_IDS.get(name, name)


def class_path(frozen: str) -> str:
    """凍結の名 → 今の「モジュール.クラス名」(状態のファイルを読むときに import する先。表に無い名はそのまま)。"""
    return _PATH_OF.get(frozen, frozen)
'''


def module_name(p: Path) -> str:
    parts = list(p.relative_to(SRC).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def class_qualnames(tree: ast.AST) -> list[str]:
    """モジュールの中の全部のクラスの ``__qualname__``(出てくる順)。"""
    out: list[str] = []

    def visit(node: ast.AST, prefix: str) -> None:
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, ast.ClassDef):
                q = f"{prefix}{ch.name}"
                out.append(q)
                visit(ch, q + ".")
            elif isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef)):
                visit(ch, f"{prefix}{ch.name}.<locals>.")
            elif isinstance(ch, ast.Lambda):
                visit(ch, f"{prefix}<lambda>.<locals>.")
            else:
                visit(ch, prefix)

    visit(tree, "")
    return out


def collect() -> tuple[list[str], int]:
    """src(build を除く)の全部のクラスの「モジュール.クラス名」(昇順)と、クラスを持つファイルの数。"""
    names: list[str] = []
    n_files = 0
    for p in sorted(PKG.rglob("*.py")):
        if p.relative_to(PKG).parts[0] in SKIP_TOP:
            continue
        mod = module_name(p)
        tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        found = [f"{mod}.{q}" for q in class_qualnames(tree)]
        n_files += bool(found)
        names += found
    if len(names) != len(set(names)):
        raise SystemExit("同じ名のクラスが 2 つある(表の鍵が重なる)")
    stale = sorted(set(EXCLUDE) - set(names))
    if stale:
        raise SystemExit(f"載せないクラスの一覧に src に無い名がある: {stale}")
    return sorted(set(names) - set(EXCLUDE)), n_files


def verify_runtime(names: list[str]) -> tuple[int, int]:
    """関数の中でないクラスを import して、``__module__``・``__qualname__`` が鍵と同じかを見る。(確かめた数, 関数の中の数)。"""
    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))
    checked = local = 0
    mods = sorted({m for m in {module_name(p) for p in PKG.rglob("*.py")
                               if p.relative_to(PKG).parts[0] not in SKIP_TOP}}, key=len, reverse=True)
    for name in names:
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


def render(table: dict[str, str]) -> tuple[str, str]:
    lines = [f"    {json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)},\n" for k, v in table.items()]
    py = HEAD + "".join(lines) + TAIL
    js = json.dumps({"schema": JSON_SCHEMA, "note": JSON_NOTE, "names": sorted(table.values())},
                    ensure_ascii=False, indent=1) + "\n"
    return py, js


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="書かずに、今のファイルが作り直しと同じかを見る")
    ap.add_argument("--no-import", action="store_true", help="import の確かめを飛ばす")
    a = ap.parse_args(argv)
    names, n_files = collect()
    old = current_values()
    table = {k: old.get(k, k) for k in names}
    dropped = sorted(set(old) - set(names))
    if len(set(table.values())) != len(table):
        raise SystemExit("凍結の名が重なる(1 対 1 でない)")
    if not a.no_import:
        checked, local = verify_runtime(names)
        print(f"import で確かめた {checked}・関数の中のクラス(AST の名だけ){local}")
    py, js = render(table)
    print(f"クラス {len(table)}・クラスを持つファイル {n_files}・"
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
