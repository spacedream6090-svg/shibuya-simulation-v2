# -*- coding: utf-8 -*-
"""commit の前の確認: 「入れるはずのファイル」の一覧とステージの中身を突き合わせる(第330・CLAUDE.md §7)。

第329 の事故: 段ごとの commit で、一覧ファイルの改行が CRLF だったため bash の変数展開で各パスの末尾に
``\\r`` が付き、``git add`` が末尾の 1 本にしか効かず、4 commit が試験 1 本ずつになった。本道具は

  1. 一覧ファイルの改行(CRLF/LF)・前後の空白・BOM を正規化して読む
  2. ``git diff --cached --name-only``(消したファイルを含む)と**集合として**比べる
  3. 足りない/余計なパスがあれば 1 行ずつ出して exit 1(commit を止める)
  4. ついでに、ステージした追加/変更ファイルの中に記録してはいけない道筋(絶対パス・ユーザー名・サーバー名)が
     無いかを検査する(``--no-path-check`` で省略可)

使い方:
  python tools/commit_check.py --expect <一覧ファイル>        # 一覧とステージを突き合わせる
  python tools/commit_check.py --expect-paths a.py b.md ...   # 一覧を引数で渡す
  python tools/commit_check.py --list                         # ステージの一覧を LF で出す(一覧ファイルの元に)
  python tools/commit_check.py --paths-only                   # 道筋の検査だけ

pre-commit から: 環境変数 ``COMMIT_EXPECT`` に一覧ファイルの道筋があれば、同じ検査を行う(``.githooks/pre-commit``)。
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

# 記録に書いてはいけない道筋の型(CLAUDE.md §7・記録のパスはマスクしてから commit)。検出パターンの正は本ファイル。
_BAD_PATH_B64 = "Z3B1LXN2LTAwMnwvaG9tZS9bYS16X11bYS16MC05X10qL3zloZrmnKx8VXNlcnNbXFwvXVteXFwvIF0rW1xcL11EZXNrdG9w"  # 検出パターン(自己 HIT を避けるため base64。中身=絶対パス・ユーザー名・サーバー名の型)
_BAD_PATH = re.compile(__import__("base64").b64decode(_BAD_PATH_B64).decode("utf-8"))
_PATH_CHECK_SUFFIX = {".md", ".json", ".txt", ".py", ".yaml", ".yml", ".toml", ".csv", ".jsonl", ".sh", ".ps1"}


def _git(*args: str) -> str:
    out = subprocess.run(["git", *args], capture_output=True, check=True)
    return out.stdout.decode("utf-8", errors="replace")


def staged_paths() -> set[str]:
    """ステージの全部(追加・変更・削除・改名の両側)。NUL 区切りで読み、空白入りでも分裂しない。"""
    raw = subprocess.run(["git", "diff", "--cached", "--name-only", "-z"], capture_output=True, check=True).stdout
    return {p.decode("utf-8", errors="replace") for p in raw.split(b"\0") if p}


def normalize_lines(text: str) -> list[str]:
    """CRLF/LF/CR・BOM・前後の空白を正規化。``#`` で始まる行と空行は無視。"""
    text = text.lstrip("﻿")
    rows = []
    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        rows.append(line.replace("\\", "/"))
    return rows


def read_expect(path: Path) -> list[str]:
    return normalize_lines(path.read_bytes().decode("utf-8", errors="replace"))


def compare(expected: list[str], staged: set[str]) -> tuple[list[str], list[str], list[str]]:
    """(足りない=一覧にあるがステージに無い, 余計=ステージにあるが一覧に無い, 一覧の重複)"""
    seen: set[str] = set()
    dup = [p for p in expected if p in seen or seen.add(p)]  # type: ignore[func-returns-value]
    exp = set(expected)
    missing = sorted(exp - staged)
    extra = sorted(staged - exp)
    return missing, extra, sorted(set(dup))


def path_check(paths: set[str]) -> list[str]:
    """ステージした追加/変更ファイルの中身に記録してはいけない道筋があれば ``path:行:中身`` を返す。"""
    hits: list[str] = []
    raw = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=AM", "-z"], capture_output=True, check=True
    ).stdout
    for p in (x.decode("utf-8", errors="replace") for x in raw.split(b"\0") if x):
        if Path(p).suffix.lower() not in _PATH_CHECK_SUFFIX:
            continue
        if p == "tools/commit_check.py" or p == "tools/scan_secrets.py":
            continue  # 検出パターンそのものを持つ
        try:
            blob = subprocess.run(["git", "show", f":{p}"], capture_output=True, check=True).stdout
        except subprocess.CalledProcessError:
            continue
        for i, line in enumerate(blob.decode("utf-8", errors="replace").split("\n"), 1):
            if _BAD_PATH.search(line):
                hits.append(f"{p}:{i}: {line.strip()[:120]}")
    return hits


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--expect", type=Path, default=None, help="入れるはずのファイルの一覧(1 行 1 パス・改行は何でもよい)")
    ap.add_argument("--expect-paths", nargs="*", default=None, help="一覧を引数で渡す")
    ap.add_argument("--list", action="store_true", help="ステージの一覧を LF で標準出力に出す")
    ap.add_argument("--paths-only", action="store_true", help="道筋の検査だけ")
    ap.add_argument("--no-path-check", action="store_true", help="道筋の検査を省く")
    a = ap.parse_args(argv)

    staged = staged_paths()
    if a.list:
        sys.stdout.buffer.write(("\n".join(sorted(staged)) + "\n").encode("utf-8"))
        return 0

    rc = 0
    if not a.paths_only:
        expected: list[str] | None = None
        if a.expect is not None:
            expected = read_expect(a.expect)
        elif a.expect_paths is not None:
            expected = normalize_lines("\n".join(a.expect_paths))
        elif os.environ.get("COMMIT_EXPECT"):
            expected = read_expect(Path(os.environ["COMMIT_EXPECT"]))
        if expected is None:
            print("commit_check: 一覧が無い(--expect/--expect-paths/COMMIT_EXPECT)。ステージ %d 本。" % len(staged))
            print("  一覧を作るなら: python tools/commit_check.py --list > <一覧>")
            rc = 2
        else:
            missing, extra, dup = compare(expected, staged)
            print(f"commit_check: 一覧 {len(set(expected))} 本 / ステージ {len(staged)} 本")
            for p in missing:
                print(f"  MISSING(一覧にあるがステージに無い): {p}")
            for p in extra:
                print(f"  EXTRA(ステージにあるが一覧に無い): {p}")
            for p in dup:
                print(f"  DUP(一覧の重複): {p}")
            if missing or extra:
                rc = 1
            else:
                print("  OK: 一覧とステージが一致")
    if not a.no_path_check:
        hits = path_check(staged)
        for h in hits:
            print(f"  PATH HIT: {h}")
        if hits:
            rc = 1
        else:
            print("  OK: 記録してはいけない道筋なし")
    if rc:
        print("commit_check: 中止(exit %d)" % rc)
    return rc


if __name__ == "__main__":
    sys.exit(main())
