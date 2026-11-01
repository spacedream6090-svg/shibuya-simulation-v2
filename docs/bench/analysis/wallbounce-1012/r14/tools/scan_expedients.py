"""1-4: ``src/shibuya`` の expedient の宣言を 4 つの形で数える作業用の道具(記録 r14/README.md の表の元)。

形:
  A ``conf="expedient"``(キーワード引数・代入)
  B ``expedients=[...]``(build の ``StageResult(expedients=...)`` のキーワード引数。要素の文字列を 1 件ずつ)
  C docstring の ``expedient:`` の段落(モジュール・クラス・関数の docstring の行頭が ``expedient:``)
  D docstring の ``expedient(…)`` の見出し(1 行まるごと・見出し単位で 1 件・下の項の数を持つ)

使い方(リポの根で): ``python docs/bench/analysis/wallbounce-1012/r14/tools/scan_expedients.py [--json]``
正の実装は ``src/shibuya/engine/bridging/scan.py``(試験が使う)。この道具はそれを呼んで表に直すだけ。
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT / "src"))

from shibuya.engine.bridging import scan as S  # noqa: E402


def main(argv: list[str]) -> int:
    decls = S.scan_tree(ROOT / "src" / "shibuya")
    by_form = Counter(d.form for d in decls)
    by_file = Counter((d.form, d.path) for d in decls)
    if "--json" in argv:
        print(json.dumps([d.as_dict() for d in decls], ensure_ascii=False, indent=1))
        return 0
    print("form counts:", dict(sorted(by_form.items())))
    for (form, path), n in sorted(by_file.items()):
        print(f"{form}\t{n}\t{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
