# -*- coding: utf-8 -*-
"""木の ``src/shibuya`` の全モジュールを、1 本ずつ最初から import できるかの確かめ(検収 M-1・親の裁定)。

- 子のプロセス(``jobs`` 本)に、モジュールの名を分けて渡す。子は 1 つ読むたびに ``shibuya`` のモジュールを
  ``sys.modules`` から外す=どのモジュールも「最初に読まれる」形で確かめる(循環の import は読む順で落ちたり落ちなかったり
  するので、全部を最初に読む)。
- ``src/shibuya/cli.py`` があれば ``python -m shibuya.cli --help`` も回す。
- ``PYTHONPATH`` は木の ``src`` だけ(venv の editable の道が本体を指していても、木の src を読む)。読んだ ``shibuya`` の
  ``__file__`` を結果に残し、木の ``src`` でなければ落ちたと数える(取り違えの防ぎ)。
- 段 4 の各段の ``move --apply`` の後に必ず回す(``cli.py move --apply`` が自分で回す。単独では ``cli.py importcheck``)。
- 〔検収 L-a〕移して無くなった包み(``gone``=対応表の頭の行のうち木に頭が無いもの)が、名前空間の包みとして import できない
  (``importlib.util.find_spec`` が ``None``)ことも見る(``__pycache__`` だけを持つ古いディレクトリが残ると import できてしまう)。
"""
from __future__ import annotations

import concurrent.futures as cf
import json
import os
import subprocess
import sys
from pathlib import Path

_WORKER = r'''
import importlib, json, sys, warnings
warnings.simplefilter("ignore")
mods = json.loads(sys.argv[1])
out = {}
for m in mods:
    for k in [k for k in sys.modules if k == "shibuya" or k.startswith("shibuya.")]:
        del sys.modules[k]
    try:
        importlib.import_module(m)
    except BaseException as e:  # noqa: BLE001
        out[m] = f"{type(e).__name__}: {e}"
print(json.dumps(out, ensure_ascii=False))
'''

_GONE = r'''
import importlib.util, json, os, sys
src = sys.argv[2]
out = {}
for m in json.loads(sys.argv[1]):
    try:
        spec = importlib.util.find_spec(m)
    except (ImportError, ValueError):
        spec = None
    if spec is not None:
        locs = [os.path.relpath(x, src).replace(os.sep, "/") for x in (spec.submodule_search_locations or [])]
        out["<名前空間> " + m] = f"移して無くなった包みが import できる(名前空間の包み・{locs[:2]})"
print(json.dumps(out, ensure_ascii=False))
'''


def modules(src: Path) -> list[str]:
    out: list[str] = []
    for p in sorted((src / "shibuya").rglob("*.py")):
        if "__pycache__" in p.parts:
            continue
        parts = list(p.relative_to(src).with_suffix("").parts)
        if parts[-1] == "__init__":
            parts = parts[:-1]
        out.append(".".join(parts))
    return out


def _env(src: Path) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env["PYTHONPATH"] = str(src)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONHASHSEED"] = "0"
    return env


def _chunk(src: Path, mods: list[str]) -> dict[str, str]:
    r = subprocess.run([sys.executable, "-c", _WORKER, json.dumps(mods)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=_env(src), cwd=str(src.parent))
    if r.returncode != 0 or not r.stdout.strip():
        return {m: f"子のプロセスが落ちた: {r.stderr[-500:]}" for m in mods}
    return json.loads(r.stdout.strip().splitlines()[-1])


def check(root: Path, jobs: int = 4, gone: list[str] | tuple[str, ...] = ()) -> dict:
    """結果: ``n``(モジュールの数)・``bad``(名 → 誤り)・``cli_help_exit``(cli が無ければ ``None``)・``cli_help_err``・
    ``gone``(確かめた無くなった包みの数)。"""
    src = Path(root) / "src"
    mods = modules(src)
    jobs = max(1, min(int(jobs), len(mods) or 1))
    bad: dict[str, str] = {}
    with cf.ThreadPoolExecutor(max_workers=jobs) as ex:
        for d in ex.map(lambda c: _chunk(src, c), [mods[i::jobs] for i in range(jobs)]):
            bad.update(d)
    if gone:
        r1 = subprocess.run([sys.executable, "-c", _GONE, json.dumps(list(gone)), str(src)], capture_output=True, text=True,
                            encoding="utf-8", errors="replace", env=_env(src), cwd=str(src.parent))
        if r1.returncode != 0 or not r1.stdout.strip():
            bad["<名前空間>"] = f"子のプロセスが落ちた: {r1.stderr[-500:]}"
        else:
            bad.update(json.loads(r1.stdout.strip().splitlines()[-1]))
    # どの木の shibuya を読んだか(editable の本体の src を読んでいないか=取り違えの防ぎ)
    r0 = subprocess.run([sys.executable, "-c", "import shibuya; print(shibuya.__file__)"], capture_output=True, text=True,
                        encoding="utf-8", errors="replace", env=_env(src), cwd=str(src.parent))
    shibuya_file = r0.stdout.strip()
    if os.path.normcase(os.path.realpath(shibuya_file)) != os.path.normcase(os.path.realpath(src / "shibuya" / "__init__.py")):
        bad["<shibuya>"] = f"木の src でない shibuya を読んだ: {shibuya_file or r0.stderr[-300:]}"
    cli_exit = None
    err = ""
    if (src / "shibuya" / "cli.py").is_file():
        r = subprocess.run([sys.executable, "-m", "shibuya.cli", "--help"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=_env(src), cwd=str(root))
        cli_exit = r.returncode
        err = r.stderr[-1500:] if r.returncode else ""
    return {"n": len(mods), "bad": dict(sorted(bad.items())), "cli_help_exit": cli_exit, "cli_help_err": err,
            "shibuya_file": shibuya_file, "gone": len(gone)}


def ok(doc: dict) -> bool:
    return not doc["bad"] and doc["cli_help_exit"] in (0, None)


def summary(doc: dict) -> str:
    cli = "無し" if doc["cli_help_exit"] is None else f"終了コード {doc['cli_help_exit']}"
    return (f"import の確かめ: モジュール {doc['n']}・落ちた {len(doc['bad'])}・python -m shibuya.cli --help {cli}・"
            f"無くなった包み {doc.get('gone', 0)}・読んだ shibuya {doc.get('shibuya_file', '?')}")
