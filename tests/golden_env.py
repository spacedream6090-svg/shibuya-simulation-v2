"""golden を環境ごとの行で持つための小道具(10f・K26 (1))。

golden の辞書は ``{platform_id: 値}`` の行で持つ。``platform_id`` は ``engine.resume.environment_fields()`` の
``platform`` のうち結果のビットに効きうる欄(``engine.resume.PLATFORM_ID_KEYS``=Python と実装・numpy・numba・
llvmlite・blake3 の版・OS と版・machine・CPU と numpy の命令セット)だけの ID。git の commit・dirty・スレッド数・
依存の一覧(pytest などの版)は含めない(含めるとコミットや無関係な版上げのたびに行が外れる)。

- 今の環境の行があれば、その値と比べる。
- 行が無い環境(別の機械・numpy などの版が違う)では golden とは比べず、**同じ設定で 2 回回して一致する(A/A)**
  ことだけを確かめる(設計書 再開と決定論 §1「同一プラットフォームの値と比べるか、同 salt 2 回の一致で検査する」)。
  そのとき **黙って通さない**: ``GoldenUnregisteredWarning`` を出し(pytest の要約に残る)、登録の有無を標準エラーに
  1 回だけ書く(10f 検収 N2)。fail にはしない(K26 (1) の約束)。新しい環境の行は、A/A を通した値を人が見て足す。

ここに登録した行の値は 10f より前の golden の値そのもの(値は 1 つも変えていない)。
"""

from __future__ import annotations

import sys
import warnings
from typing import Any, Callable, Mapping, TypeVar

from shibuya.engine.resume import environment_fields

#: 10f で登録した環境(Windows 11・x86-64・Python 3.12.10・numpy 2.5.3・numba 0.67.0・llvmlite 0.49.0・
#: blake3 1.0.9)。golden の 5 つの辞書と T7 の直書きの行の鍵。
PLATFORM_10F = "43cd89305417b52e"
#: 登録した環境の一覧(行の鍵の候補)。
REGISTERED: tuple[str, ...] = (PLATFORM_10F,)

T = TypeVar("T")


class GoldenUnregisteredWarning(UserWarning):
    """今の環境が golden に登録されていない(golden とは比べず A/A だけを確かめた)。"""


_ANNOUNCED: dict[str, bool] = {}


def platform_id() -> str:
    """今の環境の ``platform_id``。"""
    return str(environment_fields()["platform_id"])


def announce_once() -> bool:
    """登録の有無を標準エラーに 1 回だけ書く(プロセスごと)。返り値=登録されているか。"""
    pid = platform_id()
    registered = pid in REGISTERED
    if pid not in _ANNOUNCED:
        _ANNOUNCED[pid] = registered
        msg = ("golden: この環境は登録済み" if registered
               else "golden: この環境は未登録=golden とは比べず A/A だけ")
        print(f"[tests.golden_env] {msg}(platform_id={pid}・登録={','.join(REGISTERED)})", file=sys.stderr)
    return registered


def warn_unregistered(what: str) -> None:
    """未登録の環境で golden の比較を飛ばしたことを警告する(pytest の要約に出る)。"""
    announce_once()
    warnings.warn(GoldenUnregisteredWarning(
        f"golden 未登録の環境(platform_id={platform_id()}・登録={','.join(REGISTERED)}): {what} は golden と"
        "比べず A/A だけを確かめた。値を確かめて tests/golden_env.py と golden の表に行を足すこと"), stacklevel=2)


def row(table: Mapping[str, T]) -> T | None:
    """``{platform_id: 値}`` の表から今の環境の行(無ければ ``None``=未登録の警告を出す)。"""
    announce_once()
    got = table.get(platform_id())
    if got is None:
        warn_unregistered("golden の表の行")
    return got


def assert_aa(run: Callable[[], Any], key: Callable[[Any], Any], *, first: Any = None) -> Any:
    """golden の行が無い環境の検査: 同じ設定で 2 回回し、``key`` の値が一致することを確かめる。1 回目の結果を返す。

    ``first`` に回し済みの 1 回目を渡せば、回すのはもう 1 回だけ。呼ぶたびに未登録の警告を出す。
    """
    warn_unregistered("A/A")
    a = run() if first is None else first
    b = run()
    ka, kb = key(a), key(b)
    assert ka == kb, f"A/A が一致しない(環境 {platform_id()} には golden の行が無い): {ka!r} != {kb!r}"
    return a
