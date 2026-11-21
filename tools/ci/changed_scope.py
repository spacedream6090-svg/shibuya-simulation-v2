"""変えたファイルの範囲から、どの試験を回すかを決める(11-22 §3-2 の 1・5)。標準ライブラリだけ(CI で依存を入れる前に回す)。

    python tools/ci/changed_scope.py --base <commit> [--head <commit>]      # git diff の名前の一覧から
    python tools/ci/changed_scope.py --paths a.md src/x.py                   # 道筋を直に渡す
    python tools/ci/changed_scope.py --base <commit> --github-output         # CI: $GITHUB_OUTPUT に書く

決めること:

- ``heavy``: 重い組(engine)を回すか。変えたファイルが全部「文書」なら回さない。1 本でも文書でなければ回す。
- ``run_affecting``: ランの結果に効きうるか(byte-check を回す合図)。``src/`` の下・ランが実行時に開く文書・依存の固定。

「文書」= リポの根の ``*.md`` と ``docs/`` の下の ``*.md``。ただし、ランが実行時に開く文書は文書に数えない(変われば重い組も
回す)。その一覧の正は ``tools/bytecheck/tree.py`` の ``TRACKED_READS``(開きうる 8 本。20 構成のランが実際に開くのは
そのうち 5 本=規則の表・つなぎの台帳・予算の宣言・空腹の構築側の錨・活動の事前分布)。``docs/`` の下でも ``*.md`` でない
ファイル(JSON・CSV・台本)は、試験や道具が読むので文書に数えない(控えめな側)。

分からないとき(基準の commit が無い・git が失敗した)は、重い組を回す側に倒す。
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Sequence

ROOT = Path(__file__).resolve().parents[2]
TREE_REL = "tools/bytecheck/tree.py"
SHARDS_REL = "tools/ci/test_shards.json"
#: ランの結果に効きうる、src の外のファイル(依存の固定と包みの定義)。
RUN_FILES: tuple[str, ...] = ("pyproject.toml", "requirements-lock.txt")
ZERO_SHA = "0" * 40


def runtime_docs(root: Path = ROOT) -> tuple[str, ...]:
    """ランが実行時に開きうる追跡ファイル(``tools/bytecheck/tree.py`` の ``TRACKED_READS`` の鍵)。"""
    spec = importlib.util.spec_from_file_location("_bytecheck_tree_for_scope", root / TREE_REL)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"{TREE_REL} が読めない")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # dataclass が自分の module を引くため
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.modules.pop(spec.name, None)
    return tuple(mod.TRACKED_READS)


def heavy_groups(root: Path = ROOT) -> list[str]:
    """重い組の名(``tools/ci/test_shards.json`` の ``weight`` が ``heavy`` の組)。文書だけの変更では回さない。"""
    import json

    doc = json.loads((root / SHARDS_REL).read_text(encoding="utf-8"))
    return [g for g, b in doc["groups"].items() if isinstance(b, dict) and b.get("weight", "light") == "heavy"]


def _norm(path: str) -> str:
    p = path.strip().replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    return p


def is_document(path: str, runtime: Iterable[str]) -> bool:
    """文書だけの変更に数えてよい 1 本か。"""
    p = _norm(path)
    if not p.lower().endswith(".md") or p in set(runtime):
        return False
    return "/" not in p or p.startswith("docs/")


def affects_runs(path: str, runtime: Iterable[str]) -> bool:
    p = _norm(path)
    return p.startswith("src/") or p in set(runtime) or p in RUN_FILES


def classify(paths: Sequence[str], runtime: Iterable[str]) -> dict[str, object]:
    """道筋の一覧 → 判定。空の一覧は「分からない」として重い側。"""
    rt = tuple(runtime)
    ps = [_norm(p) for p in paths if _norm(p)]
    non_docs = [p for p in ps if not is_document(p, rt)]
    run_hits = [p for p in ps if affects_runs(p, rt)]
    return {
        "files": len(ps),
        "docs_only": bool(ps) and not non_docs,
        "heavy": (not ps) or bool(non_docs),
        "run_affecting": bool(run_hits),
        "non_docs": non_docs,
        "run_hits": run_hits,
    }


def changed_paths(base: str, head: str, root: Path = ROOT) -> list[str] | None:
    """``git diff --name-only base head``。失敗・基準なしは None(=分からない)。"""
    if not base or base == ZERO_SHA:
        return None
    cp = subprocess.run(["git", "-C", str(root), "diff", "--name-only", "-z", base, head], capture_output=True)
    if cp.returncode != 0:
        return None
    return [x.decode("utf-8", errors="replace") for x in cp.stdout.split(b"\0") if x]


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--base", default="", help="比べる基準の commit(PR の土台・push の前の頭)")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--paths", nargs="*", default=None, help="道筋を直に渡す(git を使わない)")
    ap.add_argument("--github-output", action="store_true",
                    help="$GITHUB_OUTPUT に heavy・run_affecting・skip_groups(回さない組の名・空白区切り)を書く")
    ap.add_argument("--root", type=Path, default=ROOT)
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")
    rt = runtime_docs(args.root)
    paths = list(args.paths) if args.paths is not None else changed_paths(args.base, args.head, args.root)
    if paths is None:
        res: dict[str, object] = {"files": 0, "docs_only": False, "heavy": True, "run_affecting": True,
                                  "non_docs": [], "run_hits": [], "unknown": True}
        print("[changed_scope] 基準の commit から差分が取れない=重い組も回す(分からないときは回す側)")
    else:
        res = classify(paths, rt)
        print(f"[changed_scope] 変えたファイル {res['files']} 本・文書だけ={res['docs_only']}"
              f"・重い組を回す={res['heavy']}・ランに効きうる={res['run_affecting']}")
        for p in list(res["non_docs"])[:20]:  # type: ignore[arg-type]
            print(f"  文書でない: {p}")
        for p in list(res["run_hits"])[:20]:  # type: ignore[arg-type]
            print(f"  ランに効きうる: {p}")
    if args.github_output:
        out = os.environ.get("GITHUB_OUTPUT")
        if not out:
            print("[changed_scope] GITHUB_OUTPUT が無い", file=sys.stderr)
            return 2
        with open(out, "a", encoding="utf-8", newline="\n") as f:
            f.write(f"heavy={'true' if res['heavy'] else 'false'}\n")
            f.write(f"run_affecting={'true' if res['run_affecting'] else 'false'}\n")
            skip = [] if res["heavy"] else heavy_groups(args.root)
            f.write(f"skip_groups={' '.join(skip)}\n")
            print(f"[changed_scope] 回さない組: {' '.join(skip) if skip else 'なし'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
