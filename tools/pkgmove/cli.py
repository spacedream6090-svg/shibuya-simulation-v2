# -*- coding: utf-8 -*-
"""移す段 3 の道具の入口。使い方は ``tools/pkgmove/README.md``。

    python tools/pkgmove/cli.py map [--check]                 # 全ファイルの表 → tools/pkgmove/map.toml
    python tools/pkgmove/cli.py allow [--check]               # tests と tools の許可の一覧 → tools/pkgmove/allow_tests_tools.toml
    python tools/pkgmove/cli.py move --stage foundation [--tree <木>] [--out-dir <置き場>]           # 書かない(既定)
    python tools/pkgmove/cli.py move --stage foundation --apply --tree <木> [--out-dir <置き場>]    # 書く

終了コード: 0=できた(書かない実行では差分と報告だけ)・1=守りが止めた(凍結の値が変わる・許可の一覧の外が変わる・鍵の取り違え・
import の文が結ぶ名が変わる・``--check`` の食い違い)・2=断った(保留の行の名指し・本体の作業木への ``--apply`` か報告の置き場・
使い方の誤り)・3=書いた後の import の確かめが落ちた(木は書いたまま=写しの木か git で戻せる作業木で回す)。

    python tools/pkgmove/cli.py importcheck --tree <木> [--out <JSON>]   # 全モジュールを 1 本ずつ最初から import
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    _here = os.path.normcase(os.path.abspath(os.path.dirname(__file__)))
    sys.path[:] = [p for p in sys.path if os.path.normcase(os.path.abspath(p or os.curdir)) != _here]
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from pkgmove import allow as AL  # noqa: E402
from pkgmove import guard as G  # noqa: E402
from pkgmove import importcheck as IC  # noqa: E402
from pkgmove import move as MV  # noqa: E402
from pkgmove import strings as ST  # noqa: E402
from pkgmove.model import Tree, area_of, is_self, parse, symbols_of  # noqa: E402
from pkgmove.table import MAP_REL, STAGES, build_map_text, load_map  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
EXIT_OK, EXIT_STOP, EXIT_REFUSE, EXIT_IMPORT = 0, 1, 2, 3


def _git_marker(path: Path) -> Path | None:
    """``path`` とその親で最初に見つかる ``.git``(ディレクトリかファイル)。無ければ ``None``(git の外)。"""
    p = Path(os.path.realpath(path))
    for d in (p, *p.parents):
        g = d / ".git"
        if g.exists():
            return g
    return None


def is_main_worktree(path: Path) -> bool:
    """``path`` が git の本体の作業木(か、その中)なら ``True``=書かない。

    断る側に倒す(検収 M-2): ``path`` とその親に ``.git`` が 1 つも無いときだけ「git の外」(``False``)。見つかった ``.git`` が
    ディレクトリなら本体(``True``)。ファイル(``git worktree add`` の作業木・submodule)なら git に ``--git-dir`` と
    ``--git-common-dir`` を聞き、違えばほかの作業木(``False``)。git が失敗したら ``True``。呼び手の ``GIT_DIR`` などの
    環境変数は外して聞く(左右されない)。
    """
    marker = _git_marker(path)
    if marker is None:
        return False
    if marker.is_dir():
        return True
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    try:
        r = subprocess.run(["git", "-C", str(path if Path(path).exists() else marker.parent), "rev-parse",
                            "--path-format=absolute", "--git-dir", "--git-common-dir"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    except OSError:
        return True
    lines = [x.strip() for x in r.stdout.splitlines() if x.strip()]
    if r.returncode != 0 or len(lines) < 2:
        return True
    nc = lambda p: os.path.normcase(os.path.realpath(p))  # noqa: E731
    return nc(lines[0]) == nc(lines[1])


def cmd_map(a: argparse.Namespace) -> int:
    text = build_map_text(REPO)
    out = REPO / MAP_REL
    if a.check:
        same = out.is_file() and out.read_text(encoding="utf-8") == text
        print("同じ" if same else "違う(cli.py map で作り直す)")
        return EXIT_OK if same else EXIT_STOP
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    doc = load_map(out)
    kinds: dict[str, int] = {}
    for r in doc.rows:
        kinds[r.kind] = kinds.get(r.kind, 0) + 1
    print(f"書いた: {MAP_REL}(行 {len(doc.rows)}・{kinds}・保留 {sum(1 for r in doc.rows if r.held)})")
    return EXIT_OK


def scan_allow(tree: Tree) -> tuple[list[tuple[str, str]], ST.StrStats]:
    """tests と tools の走査: 段 4 の全段(保留を除く)で道の文字列の書き換えが起きる (ファイル, 記号)。"""
    import ast

    mapdoc = load_map(REPO / MAP_REL)
    rows, _held = MV.select_rows(mapdoc, STAGES)
    rows = [r for r in rows if MV._row_state(tree, r) == "apply"]
    frozen = G.Frozen.load(lambda rel: (REPO / rel).read_text(encoding="utf-8"))
    ctx, relmap = MV.make_ctx(tree, rows, frozen)
    rules = ST.PathRules(relmap=relmap)
    stats = ST.StrStats()
    for p in sorted(tree.files):
        if area_of(p) not in ("tests", "tools") or is_self(p):
            continue
        text = tree.files[p]
        try:
            t = parse(text)
        except SyntaxError:
            continue
        ST.rewrite_file_strings(ctx, rules, p, text, t, symbols_of(text), {}, stats, scan_all=True)
    return sorted(stats.sites), stats


def cmd_allow(a: argparse.Namespace) -> int:
    tree = Tree.load(REPO)
    sites, stats = scan_allow(tree)
    note = ("段 4 の全段(保留の行を除く)の対応で、tests と tools の文字列の定数に道の書き換えが起きる記号。"
            "触らなかったもの(日本語の文・凍結の名・f 文字列・字面に当てられないもの)は move の報告に出る。")
    text = AL.render_tests_tools(sites, note)
    out = REPO / AL.ALLOW_TT_REL
    if a.check:
        same = out.is_file() and out.read_text(encoding="utf-8") == text
        print("同じ" if same else "違う(cli.py allow で作り直す)")
        return EXIT_OK if same else EXIT_STOP
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"書いた: {AL.ALLOW_TT_REL}(記号 {len(sites)}・ファイル {len({f for f, _ in sites})}・"
          f"書き換え {dict(stats.rewritten)}・触らなかった {len(stats.skipped)})")
    return EXIT_OK


def cmd_move(a: argparse.Namespace) -> int:
    stages = STAGES if a.stage == "all" else tuple(s.strip() for s in a.stage.split(",") if s.strip())
    if a.apply and not a.tree:
        print("--apply には --tree が要る(書く置き場を名指す)", file=sys.stderr)
        return EXIT_REFUSE
    root = Path(a.tree).resolve() if a.tree else REPO
    if a.apply and is_main_worktree(root):
        print(f"本体の作業木(か、その中)へは書かない: {root}(段 4 で使う作業木は親が決める)", file=sys.stderr)
        return EXIT_REFUSE
    if a.out_dir and is_main_worktree(Path(a.out_dir)):
        print(f"報告の置き場が本体の作業木(か、その中)にある: {a.out_dir}(木の外か、ほかの作業木に置く)", file=sys.stderr)
        return EXIT_REFUSE
    if not (root / "src" / "shibuya").is_dir():
        print(f"木に src/shibuya が無い: {root}", file=sys.stderr)
        return EXIT_REFUSE
    mapdoc = load_map(REPO / MAP_REL)
    tree = Tree.load(root, extra=AL.RECORD_TOOLS)
    frozen = G.Frozen.load(lambda rel: (root / rel).read_text(encoding="utf-8"))
    ledger = root / MV.LEDGER_REL
    try:
        plan = MV.make_plan(tree, mapdoc, stages, only=a.only or (), allow_tt=AL.load_tests_tools(REPO), frozen=frozen,
                            ledger_text=ledger.read_text(encoding="utf-8") if ledger.is_file() else None)
    except MV.Refused as e:
        print(f"断った: {e}", file=sys.stderr)
        return EXIT_REFUSE
    except MV.Stopped as e:
        print("守りが止めた(書いていない):", *e.errors, sep="\n  ", file=sys.stderr)
        return EXIT_STOP
    rep = MV.report(plan)
    tag = "all" if a.stage == "all" else "_".join(stages)
    if a.out_dir:
        od = Path(a.out_dir)
        od.mkdir(parents=True, exist_ok=True)
        (od / f"pkgmove_{tag}_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n",
                                                       encoding="utf-8", newline="\n")
        (od / f"pkgmove_{tag}.diff").write_text(MV.unified_diff(plan), encoding="utf-8", newline="\n")
    summary = {k: rep[k] for k in ("stages", "rows_applied", "rows_applied_by_kind", "file_moves", "import_statements",
                                   "import_files", "import_via_head", "import_via_package", "import_split_statements", "path_strings",
                                   "class_id_keys", "class_ids_resorted", "changed_files", "untouched_count",
                                   "untouched_broad_constants", "bridging_ledger", "guards")}
    summary["refused_held"] = [r["old"] for r in rep["refused_held"]]
    summary["rows_already"] = len(rep["rows_already"])
    summary["created_heads"] = len(rep["created_heads"])
    summary["emptied_heads"] = len(rep["emptied_heads"])
    summary["deleted"] = len(rep["deleted"])
    summary["skipped_in_allowlist"] = len(rep["skipped_in_allowlist"])
    summary["warnings"] = len(rep["warnings"])
    summary["dropped_reexports"] = {k: len(v) for k, v in rep["dropped_reexports"].items()}
    summary["dropped_all"] = {k: len(v) for k, v in rep["dropped_all"].items()}
    summary["ledger_paths_added"] = rep["ledger_paths_added"]
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    if a.apply:
        pruned = MV.apply(plan, root)
        print(f"書いた: {root.name}(ファイル {len(plan.changed) + len(plan.file_moves)}・移した {len(plan.file_moves)})")
        print(f"消した古いディレクトリ(__pycache__ のほかに何も無い): {len(pruned)}", *pruned, sep="\n  ")
        doc = IC.check(root, jobs=a.import_jobs, gone=MV.gone_packages(mapdoc, root))
        doc["removed_cache_only_dirs"] = pruned
        if a.out_dir:
            (Path(a.out_dir) / f"pkgmove_{tag}_imports.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n",
                                                                       encoding="utf-8", newline="\n")
        print(IC.summary(doc))
        if not IC.ok(doc):
            print("書いた後の import の確かめが落ちた(木は書いたまま=写しの木か git で戻せる作業木で回すこと):",
                  *list(doc["bad"].items())[:10], sep="\n  ", file=sys.stderr)
            return EXIT_IMPORT
    else:
        print("書いていない(dry-run)。書くのは --apply --tree <置き場> のときだけ")
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("map", help="全ファイルの表から対応表 TOML を作る")
    sp.add_argument("--check", action="store_true", help="書かずに、今の TOML が作り直しと同じかを見る")
    sp = sub.add_parser("allow", help="tests と tools の許可の一覧を走査で作る")
    sp.add_argument("--check", action="store_true")
    sp = sub.add_parser("move", help="段を移す(既定は書かずに差分と報告だけ)")
    sp.add_argument("--stage", required=True, help=f"段の名({', '.join(STAGES)})かコンマ区切りか all")
    sp.add_argument("--only", action="append", help="今の道筋(src/shibuya からの相対)で行を名指す(何回でも)")
    sp.add_argument("--tree", default="", help="木の根(既定は道具のリポ)。--apply のときは要る")
    sp.add_argument("--out-dir", default="", help="報告の JSON と差分を書く置き場(木の外)")
    sp.add_argument("--apply", action="store_true", help="木へ書く(本体の作業木は断る)。書いた後に import の確かめを回す")
    sp.add_argument("--import-jobs", type=int, default=4, help="書いた後の import の確かめの並べる数(既定 4)")
    sp = sub.add_parser("importcheck", help="木の src/shibuya の全モジュールを 1 本ずつ新しく import できるか")
    sp.add_argument("--tree", required=True)
    sp.add_argument("--out", default="", help="結果の JSON を書く道(木の外)")
    sp.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args(argv)
    return {"map": cmd_map, "allow": cmd_allow, "move": cmd_move, "importcheck": cmd_importcheck}[a.cmd](a)


def cmd_importcheck(a: argparse.Namespace) -> int:
    root = Path(a.tree).resolve()
    if not (root / "src" / "shibuya").is_dir():
        print(f"木に src/shibuya が無い: {root}", file=sys.stderr)
        return EXIT_REFUSE
    if a.out and is_main_worktree(Path(a.out)):
        print(f"結果の置き場が本体の作業木(か、その中)にある: {a.out}(木の外か、ほかの作業木に置く)", file=sys.stderr)
        return EXIT_REFUSE
    doc = IC.check(root, jobs=a.jobs, gone=MV.gone_packages(load_map(REPO / MAP_REL), root))
    if a.out:
        Path(a.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(IC.summary(doc))
    for m, e in list(doc["bad"].items())[:20]:
        print(f"  {m}: {e[:300]}")
    return EXIT_OK if IC.ok(doc) else EXIT_IMPORT


if __name__ == "__main__":
    sys.exit(main())
