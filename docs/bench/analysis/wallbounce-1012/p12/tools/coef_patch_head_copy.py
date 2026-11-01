"""1-2 の〔決定〕「係数を消すと既定の結果が動くかを最初に測る」の道具(作業用)。

HEAD の src の写し(``git archive <HEAD> src … | tar -x``)の中の 2 か所を「係数を 1.0 にした」形に書き換える:

1. ``perception/p_notice.py`` の ``M_LOAD = (1.0, 0.46, 1.0)`` → ``(1.0, 1.0, 1.0)``(歩きスマホの負荷を掛けない)
2. ``perception/renderer.py`` の ``check_p_see_activity`` が表を検査せず全部 1.0 を返す(看板の注視の活動の乗数を掛けない)

書き換えた写しで byte-check の ``side`` を回し、HEAD の ``side`` と ``compare`` する(使い方は記録 ``p12/README.md`` §4)。
写しの中の文字列がちょうど 1 か所ずつ当たらなければ止める(版がずれた写しを黙って測らない)。絶対パスは書かない。

使い方(リポの根で): ``python docs/bench/analysis/wallbounce-1012/p12/tools/coef_patch_head_copy.py <写しの src の親>``
"""

from __future__ import annotations

import sys
from pathlib import Path

PATCHES = (
    ("src/shibuya/perception/p_notice.py",
     "M_LOAD: Final[tuple[float, float, float]] = (1.0, 0.46, 1.0)",
     "M_LOAD: Final[tuple[float, float, float]] = (1.0, 1.0, 1.0)"),
    ("src/shibuya/perception/renderer.py",
     "    out = dict(P_SEE_BY_ACTIVITY)\n    for k, v in raw.items():",
     "    out = dict(P_SEE_BY_ACTIVITY)\n    return out  # measurement: coefficient removed (all 1.0)\n"
     "    for k, v in raw.items():"),
)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print(__doc__)
        return 2
    root = Path(args[0])
    for rel, old, new in PATCHES:
        p = root / rel
        s = p.read_text(encoding="utf-8")
        n = s.count(old)
        if n != 1:
            raise SystemExit(f"{rel}: 当たりが {n} か所(1 か所のはず)")
        p.write_text(s.replace(old, new), encoding="utf-8", newline="")
        print(f"patched {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
