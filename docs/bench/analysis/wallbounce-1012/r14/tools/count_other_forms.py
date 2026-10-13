"""1-4: 最初の 3 形(scan.py)の外の expedient の書き方を数える作業用の道具(記録 r14/README.md の §4-3 の表)。

使い方(リポの根で): ``python docs/bench/analysis/wallbounce-1012/r14/tools/count_other_forms.py``

- docstring の行頭が ``expedient(`` の行(**ゆるい数え方**=行頭だけを見る)。数・ファイルの数・下の箇条(``- `` で
  始まる行)の数。〔第 4 形を足した後の注〕scan.py の第 4 形は「1 行まるごとが ``expedient(…)``(閉じかっこで終わる)」
  の見出しだけを数えるので、ここの数より 1 つ少ない(``engine/arbiter.py`` の項の中で折り返して行頭に来た
  ``expedient(感度試験必須)」と明記)。`` は見出しでない)。
- docstring の中の ``未リサーチ(expedient)`` の注記・行頭でない ``(expedient: …)``・``mechanism=False``(状態の欄)・
  ``tag="expedient"``(契約の行)の数(ソースの文字列で数える)。
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
PKG = ROOT / "src" / "shibuya"
HEAD = re.compile(r"^expedient\s*[(（]")


def main() -> int:
    heads = files = bullets = 0
    per_file: dict[str, list[int]] = {}
    for p in sorted(PKG.rglob("*.py")):
        tree = ast.parse(p.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            doc = ast.get_docstring(node, clean=True) or ""
            lines = doc.splitlines()
            for i, line in enumerate(lines):
                if HEAD.match(line.strip()):
                    n = 0
                    for nxt in lines[i + 1:]:
                        s = nxt.strip()
                        if not s:
                            break
                        n += s.startswith("- ")
                    rel = p.relative_to(ROOT).as_posix()
                    per_file.setdefault(rel, []).append(n)
                    heads += 1
                    bullets += n
    files = len(per_file)
    srcs = {p.relative_to(PKG).as_posix(): p.read_text(encoding="utf-8") for p in PKG.rglob("*.py")
            if "__pycache__" not in p.parts}
    text = "\n".join(srcs.values())
    # 〔検収 M1 の後〕expedient を含む行の内訳(engine/bridging/ を除く): # で始まる注・そのほか
    lines = [ln.strip() for rel, s in srcs.items() if not rel.startswith("engine/bridging/") for ln in s.splitlines()
             if "expedient" in ln]
    mech = {rel: s.count("mechanism=False") for rel, s in srcs.items() if "mechanism=False" in s}
    out = {
        "docstring_expedient_paren_heads": heads, "files": files, "bullets_under_heads": bullets,
        "mirisachi_expedient_notes": text.count("未リサーチ(expedient)"),
        "inline_expedient_colon": len(re.findall(r"[(（]expedient[:：]", text)),
        "mechanism_false": text.count("mechanism=False"),
        "mechanism_false_by_file": dict(sorted(mech.items())),
        "tag_expedient": text.count('tag="expedient"'),
        "lines_with_expedient": len(lines),
        "lines_with_expedient_comment": sum(1 for ln in lines if ln.startswith("#")),
        "files_with_expedient": sum(1 for rel, s in srcs.items()
                                    if "expedient" in s and not rel.startswith("engine/bridging/")),
        "per_file": per_file,
    }
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
