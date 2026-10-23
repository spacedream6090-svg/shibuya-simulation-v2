"""engine.owner_guard — 外の状態の持ち主の実行時の守り(第 6 期 6-3 検収 M2・3-2 の ``WindowQueue`` と同じ形を共通の口に)。

- :func:`writing` の中だけ欄を書ける(``__setattr__`` は :func:`guarded_setattr` を呼ぶ)。入れ子可(外側の状態に戻る)。
  :func:`closed` は書ける間に外のコード(処理の関数)を呼ぶときに閉じる口。
- 中身を持つ欄(辞書)は :func:`hidden` に置いた辞書を持ち主の中で書き、欄には読み取り専用の写し(``MappingProxyType``)を
  置く=外から ``x._meter["k"] = …`` は ``TypeError``。配列は書けない印(``setflags(write=False)``)を付けて置き、持ち主の書く口が
  新しい配列に置き換える。
- 残る穴(3-2 と同じ限界): :data:`_HIDDEN` を外から直に引く書き・配列の印を外から外す書き(どちらも持ち主の外の意図した改変)。

逐次ループ宣言: なし。
"""

from __future__ import annotations

import contextlib
import weakref
from typing import Any, Iterator

__all__ = ["writing", "closed", "guarded_setattr", "guarded_delattr", "hidden", "frozen_array"]

#: 書いている途中の持ち主の物の番号(書く口の自分の文の間だけ入る)。
_WRITING: set[int] = set()
#: 持ち主 → 中身を書く辞書(持ち主の欄には読み取り専用の写しを置く)。
_HIDDEN: "weakref.WeakKeyDictionary[Any, dict[str, Any]]" = weakref.WeakKeyDictionary()


@contextlib.contextmanager
def writing(obj: Any) -> Iterator[None]:
    """``obj`` の欄を書ける間(入れ子可)。"""
    k = id(obj)
    was = k in _WRITING
    _WRITING.add(k)
    try:
        yield
    finally:
        if not was:
            _WRITING.discard(k)


@contextlib.contextmanager
def closed(obj: Any) -> Iterator[None]:
    """``obj`` の欄を書けない間(書く口の中から外のコード=処理の関数を呼ぶ間)。"""
    k = id(obj)
    was = k in _WRITING
    _WRITING.discard(k)
    try:
        yield
    finally:
        if was:
            _WRITING.add(k)


def guarded_setattr(obj: Any, name: str, value: Any, what: str) -> None:
    if id(obj) not in _WRITING:
        raise AttributeError(f"{what}の欄 {name} は外から書けない(書く口は持ち主のメソッドだけ)")
    object.__setattr__(obj, name, value)


def guarded_delattr(obj: Any, name: str, what: str) -> None:
    raise AttributeError(f"{what}の欄 {name} は消せない")


def hidden(obj: Any) -> dict[str, Any]:
    """持ち主の中身を書く辞書(無ければ作る)。持ち主の書く口の中だけで使う。"""
    d = _HIDDEN.get(obj)
    if d is None:
        d = {}
        _HIDDEN[obj] = d
    return d


def frozen_array(a: Any) -> Any:
    """配列に書けない印を付けて返す(持ち主が新しい配列で置き換える)。"""
    a.setflags(write=False)
    return a
