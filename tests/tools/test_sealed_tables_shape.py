"""封印の語の表 2 つの「数」と「重なり」を固定する(11-22 §1 の 3)。

2 つの表(読みの守り ``tools/instruments/read_guard.py`` の ``SEALED_TOKENS`` と、構築の封の守り
``shibuya.build.audit.w19_freeze`` の ``HOLDOUT_TOKENS``)は、1 つにまとめない(まとめると構築の封の守りで新しく 11 組が
当たり、当たった語と場所を誰かが読む必要が出る=読まずに別のまま残す、がユーザーの決定)。

別のまま残す代わりに、表の数か重なりが変わったら、この試験が落ちて気づけるようにする。**語は出さない**: 比べるのは数だけで、
語の集まりは助けの関数の中に閉じる(失敗の表示にも、``--showlocals`` の表示にも語が出ない)。

数が変わったとき: 表に語を足した・消したのが意図どおりなら、下の ``EXPECTED`` を直す。併せて
``python tools/instruments/sealed_tokens_dryrun.py`` を回し、新しく当たる数を報告に書く(語は書かない)。
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

#: (読みの守りの表の語の数, 構築の封の守りの表の語の数, 2 つの表に共通の語の数, 計器の段の表の語の数, 計器だけの語の数)
#: 2026-11-21 の空回しの記録(docs/bench/analysis/sealed-tokens-348/dryrun.json)と同じ値。
EXPECTED = (12, 3, 1, 25, 13)


def _counts() -> tuple[int, int, int, int, int]:
    """数だけを返す(語の集まりは、この関数の外に出さない)。"""
    spec = importlib.util.spec_from_file_location("_sealed_dryrun_for_shape", REPO / "tools" / "instruments" / "sealed_tokens_dryrun.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    try:
        spec.loader.exec_module(mod)
        rg = mod._load_read_guard()
        w19 = mod._load_w19()
        sealed = tuple(str(t) for t in rg.SEALED_TOKENS)
        gauge = tuple(str(t) for t in rg.GAUGE_DENY_TOKENS)
        holdout = tuple(str(t) for t in w19.HOLDOUT_TOKENS)
        both = len(sealed) + len(holdout) - len(mod.merged(sealed, holdout))
        return (len(set(sealed)), len(set(holdout)), both, len(set(gauge)), len(set(gauge) - set(sealed)))
    finally:
        sys.modules.pop(spec.name, None)


def test_two_sealed_tables_keep_their_sizes_and_overlap():
    got = _counts()
    assert got == EXPECTED, (
        "封印の語の表の数か重なりが変わった(読みの守り・構築の封の守り・共通・計器の段・計器だけ)。"
        "意図した変更なら EXPECTED を直し、tools/instruments/sealed_tokens_dryrun.py の数を報告に書く(語は書かない)"
    )


def test_counts_helper_returns_numbers_only():
    """助けの関数が返すのは数だけ(語が戻り値に混ざると、失敗の表示に出る)。"""
    got = _counts()
    assert len(got) == len(EXPECTED) and all(type(x) is int for x in got)
