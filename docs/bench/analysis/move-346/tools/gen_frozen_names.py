"""移す段 2-1: 名前を変えてはいけない文字列を src の AST から集めて JSON に凍結する道具。

    python docs/bench/analysis/move-346/tools/gen_frozen_names.py            # 凍結の JSON が無ければ書く
    python docs/bench/analysis/move-346/tools/gen_frozen_names.py --check    # 今の src から作り直したものと同じか

- 正: 返事その 7 §4-2 の 3・計画 ``docs/reference/package-map-final-2026-11-09.md`` §7-2。記録
  ``docs/bench/analysis/move-346/README.md``。書くのは ``tests/engine/state/names_frozen.json``
  (形は ``tests/engine/time/manifest_keys_frozen.json`` と同じ=``schema``・``note``・中身。道と行の番号は鍵にしない)。
- 集めるもの(docstring の文字列は数えない):
  1. ``rng_domains``: 乱数の領域の名の 3 つの表(``POPULATION_RNG_DOMAINS``・``ENVIRONMENT_RNG_DOMAINS``・
     ``MOTION_RNG_DOMAINS``)の鍵(src の ``build/`` の外の頂上の代入から名で探す)。
  2. ``rng_domains_path_shaped``: 1 の鍵のうち、今のモジュールの道と同じ形のもの(``shibuya.`` を頭に足すと、2 部品
     以上の頭が src のモジュールか包みになる)。``rng_domain_suffixes``: そのうち 2 つを組み立てる接尾の文字列
     (``llm.mock`` の ``_MOVE_TARGET_DOMAIN_SUFFIX``・``_SHOP_TARGET_DOMAIN_SUFFIX`` の値)。
  3. ``version_ids``: src の全部(build を含む)の文字列とバイト列の定数のうち ``shibuya.<点の名>/`` で始まるもの
     (版の ID・形式の名)。多重集合(同じ値が 2 か所なら 2 つ)。
  4. ``hash_headers``: src の全部(build を含む)のバイト列の定数のうち ``shibuya.`` で始まるもの(ハッシュと指紋の
     見出し)。多重集合。
  5. ``other_path_shaped``: 道と同じ形のほかの名(計画の 2 つ=manifest の節の名 ``economy.stage2``・
     ``shibuya.cache_salt``)と、この役が見つけた塩の語 ``\\x1fengine``(``engine.run.run_salt_for`` と
     ``perception.renderer`` の近接の同点の塩=包みの名 ``engine`` と同じ語がハッシュに入る)。
- 2 と 5 は「今の src に値がある」だけを試験が確かめる(道によらない)。1・3・4 は集めた集合(多重集合)が凍結と同じかを
  確かめる。凍結は 1 回だけ書く(JSON があれば ``--force`` が無い限り書かない)。``--check`` は今の src から作り直して
  比べる(2 は段 4 の後は道の形でなくなるので比べない)。
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
SRC = REPO / "src"
PKG = SRC / "shibuya"
OUT = REPO / "tests" / "engine" / "state" / "names_frozen.json"
TABLES = ("POPULATION_RNG_DOMAINS", "ENVIRONMENT_RNG_DOMAINS", "MOTION_RNG_DOMAINS")
SUFFIX_NAMES = ("_MOVE_TARGET_DOMAIN_SUFFIX", "_SHOP_TARGET_DOMAIN_SUFFIX")
OTHER = ("economy.stage2", "shibuya.cache_salt", "\x1fengine")
VERSION_RE = re.compile(r"^shibuya\.[A-Za-z0-9_.]+/")
VERSION_RE_B = re.compile(rb"^shibuya\.[A-Za-z0-9_.]+/")
SCHEMA = "shibuya.tests/move/names-frozen/1"
NOTE = (
    "名前を変えてはいけない文字列(移す段 2-1・返事その 7 §4-2 の 3・計画 docs/reference/package-map-final-2026-11-09.md "
    "§7-2)。見た目はモジュールの道だが中身は ID(乱数の領域の名・版の ID・ハッシュと指紋の見出し・manifest の節の名・"
    "塩)。移す道具はこれらを書き換えない。作り方は docs/bench/analysis/move-346/tools/gen_frozen_names.py(記録 "
    "docs/bench/analysis/move-346/README.md)。バイト列は UTF-8 で読んだ文字列で書き、version_ids は [\"b\", 値] と "
    "[\"s\", 値] の組。値を変えたら理由を記録に書いて更新する。"
)


def module_name(p: Path) -> str:
    parts = list(p.relative_to(SRC).with_suffix("").parts)
    return ".".join(parts[:-1] if parts[-1] == "__init__" else parts)


def docstring_ids(tree: ast.AST) -> set[int]:
    out: set[int] = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and n.body:
            b0 = n.body[0]
            if isinstance(b0, ast.Expr) and isinstance(b0.value, ast.Constant) and isinstance(b0.value.value, str):
                out.add(id(b0.value))
    return out


def files(build: bool) -> list[Path]:
    return [p for p in sorted(PKG.rglob("*.py")) if build or p.relative_to(PKG).parts[0] != "build"]


def constants(paths: list[Path]) -> list[str | bytes]:
    out: list[str | bytes] = []
    for p in paths:
        tree = ast.parse(p.read_text(encoding="utf-8"))
        ds = docstring_ids(tree)
        out += [n.value for n in ast.walk(tree)
                if isinstance(n, ast.Constant) and isinstance(n.value, (str, bytes)) and id(n) not in ds]
    return out


def table_keys(paths: list[Path], name: str) -> list[str]:
    found: list[list[str]] = []
    for p in paths:
        for n in ast.parse(p.read_text(encoding="utf-8")).body:
            tgt = n.target if isinstance(n, ast.AnnAssign) else (n.targets[0] if isinstance(n, ast.Assign) else None)
            if isinstance(tgt, ast.Name) and tgt.id == name:
                d = n.value.args[0] if isinstance(n.value, ast.Call) else n.value
                assert isinstance(d, ast.Dict), name
                found.append([ast.literal_eval(k) for k in d.keys])
    if len(found) != 1:
        raise SystemExit(f"{name} の定義が {len(found)} 個")
    return sorted(found[0])


def suffix_values(paths: list[Path]) -> list[str]:
    out: dict[str, str] = {}
    for p in paths:
        for n in ast.parse(p.read_text(encoding="utf-8")).body:
            tgt = n.target if isinstance(n, ast.AnnAssign) else (n.targets[0] if isinstance(n, ast.Assign) else None)
            if isinstance(tgt, ast.Name) and tgt.id in SUFFIX_NAMES:
                out[tgt.id] = ast.literal_eval(n.value)
    if set(out) != set(SUFFIX_NAMES):
        raise SystemExit(f"接尾の定数が足りない {sorted(set(SUFFIX_NAMES) - set(out))}")
    return sorted(out.values())


def build_doc() -> dict:
    run_side = files(build=False)
    every = files(build=True)
    mods = {module_name(p) for p in every}
    tables = {t: table_keys(run_side, t) for t in TABLES}
    keys = sorted({k for v in tables.values() for k in v})

    def path_shaped(k: str) -> bool:
        parts = ("shibuya." + k).split(".")
        return any(".".join(parts[:i]) in mods for i in range(3, len(parts) + 1))

    shaped = [k for k in keys if path_shaped(k)]
    consts_all = constants(every)
    consts_run = constants(run_side)
    vids = sorted([["b", c.decode("utf-8")] if isinstance(c, bytes) else ["s", c] for c in consts_all
                   if (VERSION_RE_B if isinstance(c, bytes) else VERSION_RE).match(c)])
    heads = sorted(c.decode("utf-8") for c in consts_all if isinstance(c, bytes) and c.startswith(b"shibuya."))
    for v in OTHER:
        if v not in consts_run:
            raise SystemExit(f"ほかの名 {v!r} が src に無い")
    return {"schema": SCHEMA, "note": NOTE, "rng_domains": tables, "rng_domains_path_shaped": shaped,
            "rng_domain_suffixes": suffix_values(run_side), "version_ids": vids, "hash_headers": heads,
            "other_path_shaped": sorted(OTHER)}


def summary(doc: dict) -> str:
    t = doc["rng_domains"]
    vb = sum(1 for k, _ in doc["version_ids"] if k == "b")
    return (f"乱数の領域の名 {sum(len(v) for v in t.values())}({'・'.join(f'{k} {len(v)}' for k, v in t.items())})・"
            f"道の形 {len(doc['rng_domains_path_shaped'])}・接尾 {len(doc['rng_domain_suffixes'])}・"
            f"版の ID {len(doc['version_ids'])}(文字列 {len(doc['version_ids']) - vb}・バイト列 {vb})・"
            f"見出し {len(doc['hash_headers'])}・ほかの名 {len(doc['other_path_shaped'])}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--force", action="store_true", help="凍結の JSON があっても書き直す")
    a = ap.parse_args(argv)
    doc = build_doc()
    print(summary(doc))
    text = json.dumps(doc, ensure_ascii=False, indent=1) + "\n"
    if a.check:
        old = json.loads(OUT.read_text(encoding="utf-8"))
        bad = [k for k in doc if k != "rng_domains_path_shaped" and doc[k] != old.get(k)]
        print("同じ" if not bad else f"違う: {bad}")
        return 0 if not bad else 1
    if OUT.is_file() and not a.force:
        print(f"凍結の JSON がある(書かない): {OUT.relative_to(REPO).as_posix()}")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"書いた: {OUT.relative_to(REPO).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
