# -*- coding: utf-8 -*-
"""封印の語の表 2 つを 1 つにまとめた語で、2 つの守りを空回しし、新しく当たる数だけを数える(11-20 §1 の 3・§5-5)。

2 つの守り:
- 読みの守り ``tools/instruments/read_guard.py`` の ``deny_hit``(道筋に語があれば落とす。表は ``SEALED_TOKENS``)
- 構築の封の守り ``shibuya.build.audit.w19_freeze`` の ``scan_build_sources``(構築のソースに語があれば挙げる。表は ``HOLDOUT_TOKENS``)

空回しのしかた:
- 構築の封の守りは、本物の関数を、表だけをまとめた語に差し替えて呼ぶ(走査の範囲と除く物は本物のまま)。
  今の表で当たる組(ファイル・語)を引いた残りが「新しく当たる数」。
- 読みの守りは、道筋を見る守りなので、リポにある道筋の全部を母数にする。母数は 2 つ=git が追跡するファイルと、
  ``data/`` の下のファイルの名(名だけを並べる。中は開かない)。今の表で当たらず、まとめた語で当たる道筋の数が「新しく当たる数」。
  計器の段の表(``GAUGE_DENY_TOKENS``=封印の語+計器だけの語)でも同じ数を出す。

出すのは数だけ: **語・ファイルの名・道筋は、画面にも記録にも出さない。** 例外の文にも入れない。

    python tools/instruments/sealed_tokens_dryrun.py [--json <記録の置き場>]

終了コード: 0=新しく当たる数が両方の守りで 0(まとめてよい)・1=どちらかで 1 つ以上(まとめずに止まり、数だけを報告する)・
2=誤り(表や木が読めない)。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence

SCHEMA = "shibuya.tools/instruments/sealed_tokens_dryrun/1"
ROOT = Path(__file__).resolve().parents[2]


def _load_read_guard() -> Any:
    name = "_read_guard_for_dryrun"
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name("read_guard.py"))
    if spec is None or spec.loader is None:
        raise RuntimeError("read_guard を読めない")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_w19() -> Any:
    src = str(ROOT / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    from shibuya.build.audit import w19_freeze

    return w19_freeze


def merged(a: Sequence[str], b: Sequence[str]) -> tuple[str, ...]:
    """2 つの表をまとめた語(並びは a の後に、a に無い b)。大文字と小文字の違いは別の語として残す。"""
    seen = set(a)
    return tuple(a) + tuple(t for t in b if t not in seen)


def path_hit(path: str, tokens: Sequence[str]) -> bool:
    """読みの守りと同じ当たり方(小文字にそろえた道筋に、小文字にそろえた語が入っているか)。ファイルには触らない。"""
    form = path.replace("\\", "/").lower()
    return any(t.lower() in form for t in tokens)


def count_new_path_hits(paths: Iterable[str], current: Sequence[str], union: Sequence[str]) -> dict[str, int]:
    """道筋の母数で、今の表・まとめた語のそれぞれで当たる数と、新しく当たる数。"""
    n = n_cur = n_uni = n_new = 0
    for p in paths:
        n += 1
        c = path_hit(p, current)
        u = path_hit(p, union)
        n_cur += int(c)
        n_uni += int(u)
        n_new += int(u and not c)
    return {"n_paths": n, "n_hit_current": n_cur, "n_hit_merged": n_uni, "n_new": n_new}


def _tracked_paths(root: Path) -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=str(root), capture_output=True, check=True).stdout
    return [p for p in out.decode("utf-8", errors="replace").split("\0") if p]


def _data_names(root: Path) -> list[str]:
    """``data/`` の下のファイルの名(相対の道筋)。名だけを並べ、中は開かない。無ければ空。"""
    base = root / "data"
    if not base.is_dir():
        return []
    names: list[str] = []
    for dirpath, _dirnames, filenames in os.walk(base):
        rel = os.path.relpath(dirpath, root).replace("\\", "/")
        names.extend(f"{rel}/{f}" for f in filenames)
    return names


def build_scan_new(w19: Any, union: Sequence[str]) -> dict[str, int]:
    """構築の封の守りを、表だけを差し替えて呼ぶ。今の表との差(新しく当たるファイルの数と、ファイルと語の組の数)。"""
    build_root = Path(w19.__file__).resolve().parents[1]
    saved = w19.HOLDOUT_TOKENS
    cur = w19.scan_build_sources(build_root)
    try:
        w19.HOLDOUT_TOKENS = tuple(union)
        uni = w19.scan_build_sources(build_root)
    finally:
        w19.HOLDOUT_TOKENS = saved
    cur_pairs = {(f, t) for f, toks in cur.items() for t in toks}
    uni_pairs = {(f, t) for f, toks in uni.items() for t in toks}
    return {
        "n_files_hit_current": len(cur),
        "n_files_hit_merged": len(uni),
        "n_new_files": len(set(uni) - set(cur)),
        "n_pairs_current": len(cur_pairs),
        "n_pairs_merged": len(uni_pairs),
        "n_new_pairs": len(uni_pairs - cur_pairs),
    }


def dryrun(root: Path = ROOT) -> dict[str, Any]:
    rg, w19 = _load_read_guard(), _load_w19()
    sealed = tuple(str(t) for t in rg.SEALED_TOKENS)
    gauge = tuple(str(t) for t in rg.GAUGE_DENY_TOKENS)
    holdout = tuple(str(t) for t in w19.HOLDOUT_TOKENS)
    union = merged(sealed, holdout)
    union_gauge = merged(gauge, holdout)
    tracked = _tracked_paths(root)
    data = _data_names(root)
    read = {
        "tracked_sealed": count_new_path_hits(tracked, sealed, union),
        "tracked_gauge": count_new_path_hits(tracked, gauge, union_gauge),
        "data_sealed": count_new_path_hits(data, sealed, union),
        "data_gauge": count_new_path_hits(data, gauge, union_gauge),
    }
    build = build_scan_new(w19, union)
    n_new_read = read["tracked_sealed"]["n_new"] + read["data_sealed"]["n_new"]
    n_new_build = build["n_new_pairs"]
    return {
        "schema": SCHEMA,
        "n_sealed": len(sealed),
        "n_holdout": len(holdout),
        "n_merged": len(union),
        "data_present": bool(data),
        "read_guard": read,
        "build_scan": build,
        "n_new_read_guard": n_new_read,
        "n_new_build_scan": n_new_build,
        "mergeable": n_new_read == 0 and n_new_build == 0,
    }


def render(r: dict[str, Any]) -> str:
    rd, b = r["read_guard"], r["build_scan"]
    return "\n".join(
        [
            f"語の数: 読みの守り {r['n_sealed']}・構築の封の守り {r['n_holdout']}・まとめた語 {r['n_merged']}",
            f"読みの守り(追跡するファイル {rd['tracked_sealed']['n_paths']} 本): 今 {rd['tracked_sealed']['n_hit_current']}"
            f"・まとめた語 {rd['tracked_sealed']['n_hit_merged']}・新しく当たる {rd['tracked_sealed']['n_new']}"
            f"(計器の段の表では 新しく当たる {rd['tracked_gauge']['n_new']})",
            f"読みの守り(data の下の名 {rd['data_sealed']['n_paths']} 本・data がある={r['data_present']}): 今 {rd['data_sealed']['n_hit_current']}"
            f"・まとめた語 {rd['data_sealed']['n_hit_merged']}・新しく当たる {rd['data_sealed']['n_new']}"
            f"(計器の段の表では 新しく当たる {rd['data_gauge']['n_new']})",
            f"構築の封の守り: 今 当たるファイル {b['n_files_hit_current']}・組 {b['n_pairs_current']}"
            f"/まとめた語 ファイル {b['n_files_hit_merged']}・組 {b['n_pairs_merged']}"
            f"/新しく当たる ファイル {b['n_new_files']}・組 {b['n_new_pairs']}",
            f"新しく当たる数: 読みの守り {r['n_new_read_guard']}・構築の封の守り {r['n_new_build_scan']}"
            f" → {'まとめてよい(0 と 0)' if r['mergeable'] else 'まとめずに止まる(数だけを報告する)'}",
        ]
    )


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="封印の語の表をまとめた語で 2 つの守りを空回しし、新しく当たる数だけを出す")
    ap.add_argument("--json", default=None, help="記録の JSON の置き場(数だけを書く)")
    ns = ap.parse_args(argv)
    try:
        r = dryrun()
    except Exception as e:  # 例外の文に語や道筋が入らないよう、型の名だけを出す
        print(f"[sealed_tokens_dryrun] 誤り: {type(e).__name__}", file=sys.stderr)
        return 2
    print(render(r))
    if ns.json:
        out = Path(ns.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        # バイトで書く(Windows でも改行を LF のままにする)
        out.write_bytes((json.dumps(r, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    return 0 if r["mergeable"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
