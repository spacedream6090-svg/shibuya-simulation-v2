# -*- coding: utf-8 -*-
"""封印の語の表 2 つを、語を出さずに個数だけで比べる(11-16 §1-6 の 5)。

比べる表:
- ``tools/instruments/read_guard.py`` の ``SEALED_TOKENS``(計器が読んではいけない道の語)
- ``shibuya.build.audit.w19_freeze`` の ``HOLDOUT_TOKENS``(構築の封の検査の語)

出すのは数だけ: それぞれの個数・共通の個数・片方にだけある個数・集合として同じか・
片方の語がもう片方の語を含む組の数(字面は違うが同じ層を指していそうな組の目安)。
**語そのものは、画面にも記録にも出さない。** 例外の文にも語を入れない。

    python tools/instruments/sealed_tokens_compare.py [--json <記録の置き場>]

終了コード: 0=集合として同じ・1=違う・2=誤り(表が読めない)。
同じなら 1 つにまとめてよい。違ったらまとめずに止まり、個数だけを報告する(壁打ちで決める)。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Sequence

SCHEMA = "shibuya.tools/instruments/sealed_tokens_compare/1"
ROOT = Path(__file__).resolve().parents[2]


def _load_read_guard_tokens() -> tuple[str, ...]:
    spec = importlib.util.spec_from_file_location("_read_guard_for_compare", Path(__file__).with_name("read_guard.py"))
    if spec is None or spec.loader is None:
        raise RuntimeError("read_guard を読めない")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return tuple(str(t) for t in mod.SEALED_TOKENS)


def _load_w19_tokens() -> tuple[str, ...]:
    src = str(ROOT / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    from shibuya.build.audit import w19_freeze

    return tuple(str(t) for t in w19_freeze.HOLDOUT_TOKENS)


def compare(a: Sequence[str], b: Sequence[str]) -> dict[str, Any]:
    """2 つの語の表を比べて、数だけの辞書を返す(語は入れない)。"""
    sa, sb = set(a), set(b)
    la, lb = {t.lower() for t in sa}, {t.lower() for t in sb}
    only_a, only_b = la - lb, lb - la
    # 片方にだけある語のうち、もう片方の語を含むか含まれる語の数(字面は違うが重なっていそうな目安)
    a_overlaps = sum(1 for t in only_a if any(t in u or u in t for u in lb))
    b_overlaps = sum(1 for t in only_b if any(t in u or u in t for u in la))
    return {
        "schema": SCHEMA,
        "n_a": len(a),
        "n_a_unique": len(sa),
        "n_b": len(b),
        "n_b_unique": len(sb),
        "common": len(sa & sb),
        "only_a": len(sa - sb),
        "only_b": len(sb - sa),
        "same_set": sa == sb,
        "same_order": tuple(a) == tuple(b),
        "same_set_casefold": la == lb,
        "only_a_overlapping_b": a_overlaps,
        "only_b_overlapping_a": b_overlaps,
    }


def render(r: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"read_guard.SEALED_TOKENS: {r['n_a']} 語(重なりを除いて {r['n_a_unique']})",
            f"w19_freeze.HOLDOUT_TOKENS: {r['n_b']} 語(重なりを除いて {r['n_b_unique']})",
            f"共通 {r['common']}・read_guard にだけ {r['only_a']}・w19_freeze にだけ {r['only_b']}",
            f"集合として同じ: {'はい' if r['same_set'] else 'いいえ'}(並びも同じ: {'はい' if r['same_order'] else 'いいえ'}・"
            f"大文字小文字をそろえて同じ: {'はい' if r['same_set_casefold'] else 'いいえ'})",
            f"片方にだけある語のうち、もう片方の語と字面が重なるもの: read_guard の側 {r['only_a_overlapping_b']}・"
            f"w19_freeze の側 {r['only_b_overlapping_a']}",
        ]
    )


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="封印の語の表 2 つを個数だけで比べる(語は出さない)")
    ap.add_argument("--json", default=None, help="数だけの記録の JSON の置き場")
    ns = ap.parse_args(argv)
    try:
        a, b = _load_read_guard_tokens(), _load_w19_tokens()
    except Exception as e:  # 例外の文に語が入らないよう、型の名だけを出す
        print(f"[sealed_tokens_compare] 誤り: 表を読めない({type(e).__name__})", file=sys.stderr)
        return 2
    r = compare(a, b)
    print(render(r))
    if ns.json:
        out = Path(ns.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(r, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if r["same_set"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
