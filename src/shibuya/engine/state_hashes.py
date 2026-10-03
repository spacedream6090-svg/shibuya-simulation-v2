"""behavior-hash と full-hash(10b・A2・A3)。表は ``engine.state_ledger`` だけから読む。

- **final(今の ``Checkpoint.combined``)は定義を変えない**。本モジュールは checkpoint の記録と manifest に
  2 本の値を**足すだけ**(テープ・final には混ぜない)。
- **behavior-hash** = 今の ``combined`` と同じ組み立てで、agents と world の SoA だけ
  ``Registry.state_hash(exclude=軸 1 が no/diag の列)`` に替え、末尾に外の状態のうち軸 1 が behavior の行の
  digest を足したもの(10b-2)。``state_hash`` の見出しに列の数が入らない
  ので「除外して計算」と「宣言から消して計算」は同じバイト列になる(材料 §2-3)=10e で死蔵の列を消して
  behavior-hash を既定に切り替えた後の final は、10b で記録した behavior-hash と一致するはず(T2)。
  計算の形は (a)=2 本を別々に計算(列ごとの digest で 1 回に束ねる (b) は 10e で)。
- **full-hash** = SoA の全列のうち軸 2 が ``discardable`` でない列(agents・cells・pois・知覚)+母集団と予定表の
  同定+外の状態のうち軸 2 が ``required``・``derivable``・``unknown`` の行の属性(台帳の宣言順に ``to_state`` で
  直列化)。行の属性の持ち主は ``run_day`` が checkpoint のたびに組む ``owners`` の辞書からたどる。
  途中の持ち主が ``None``(腕が立っていない)なら「無い」の印だけを入れる。

``to_state`` の直列化(実行役の自前の構成=**未リサーチ(expedient)**): 型の印 1 字+長さ+中身。numpy の配列は
dtype・形・生バイト、辞書は鍵の直列化の昇順、集合は要素の直列化の昇順、dataclass と NamedTuple は宣言順の
欄、``np.random.Generator`` は ``bit_generator.state``。知らない型は ``TypeError``(黙って飛ばさない)。
"""

from __future__ import annotations

import dataclasses
import enum
import numbers
import struct
from collections import OrderedDict, deque
from collections.abc import Mapping
from typing import Any, Final

import blake3 as _blake3
import numpy as np

from shibuya.core.hashing import blake3_hex
from shibuya.engine import state_ledger as SL

FULL_HEADER: Final[bytes] = b"shibuya.engine.state_hashes/full/v1"
_SEP: Final[bytes] = b"\x1f"
_LEN = struct.Struct("<Q")
#: ``vars()`` で欄を並べてよい値のクラス(``__dict__`` を持つが dataclass でないもの)。
#: ここに無いクラスは ``TypeError``=外の状態の書き出し漏れを黙って通さない。
VALUE_CLASSES: Final[frozenset[str]] = frozenset({
    "shibuya.engine.arbiter.WakeCandidates",
    "shibuya.engine.scheduler.DeferralQueue",
    "shibuya.perception.p_notice.EventBudget",
})


class _Feed:
    """ハッシュに流しながらバイト数を数える。"""

    __slots__ = ("h", "n")

    def __init__(self, h: Any) -> None:
        self.h = h
        self.n = 0

    def w(self, b: bytes | memoryview) -> None:
        self.h.update(b)
        self.n += len(b)


class _Buf:
    __slots__ = ("parts", "n")

    def __init__(self) -> None:
        self.parts: list[bytes] = []
        self.n = 0

    def w(self, b: bytes | memoryview) -> None:
        bb = bytes(b)
        self.parts.append(bb)
        self.n += len(bb)

    def value(self) -> bytes:
        return b"".join(self.parts)


def _qual(obj: Any) -> str:
    t = type(obj)
    return f"{t.__module__}.{t.__qualname__}"


def _str(f: Any, tag: bytes, s: str) -> None:
    b = s.encode("utf-8")
    f.w(tag + _LEN.pack(len(b)) + b)


def _is_int(x: Any) -> bool:
    """整数か(Python の int と numpy の整数。``bool``・``np.bool_`` は除く=検収 2-4)。"""
    return isinstance(x, numbers.Integral) and not isinstance(x, (bool, np.bool_))


def _feed_int_table(f: Any, v: Mapping, ordered: bool = False) -> bool:
    """鍵が整数(か同じ長さの整数の組)・値が整数だけの辞書を numpy の配列 2 本で流す(速い道)。

    会話の管理の ``_refusal_until`` などの形(``{(体, 体): tick}``)。整数は Python の int と numpy の整数を
    同じに扱う(``{1: 2}`` と ``{np.int64(1): np.int64(2)}`` は同じバイト列)。``ordered`` でなければ鍵の昇順に
    並べるので挿入順に依らない。``ordered`` なら挿入順のまま(印 ``U``)。当てはまらなければ ``False`` を返して
    普通の辞書の道へ回す(``bool``・浮動小数・int64 に収まらない整数)。直列化の中身が決まれば道も決まる=決定論。
    """
    n = len(v)
    if n == 0:
        return False
    k0 = next(iter(v))
    w = len(k0) if type(k0) is tuple else (0 if _is_int(k0) else -1)
    if w < 0 or w > 8:
        return False
    for k, x in v.items():
        if not _is_int(x):
            return False
        if w == 0:
            if not _is_int(k):
                return False
        elif type(k) is not tuple or len(k) != w or not all(_is_int(e) for e in k):
            return False
    try:
        if w == 0:
            keys = np.array([int(k) for k in v.keys()], dtype=np.int64).reshape(n, 1)
        else:
            keys = np.array([[int(e) for e in k] for k in v.keys()], dtype=np.int64).reshape(n, w)
        vals = np.array([int(x) for x in v.values()], dtype=np.int64)
    except OverflowError:
        return False
    if ordered:
        f.w(b"U" + _LEN.pack(w) + _LEN.pack(n))
    else:
        order = np.lexsort(keys.T[::-1])
        keys, vals = keys[order], vals[order]
        f.w(b"Q" + _LEN.pack(w) + _LEN.pack(n))
    f.w(np.ascontiguousarray(keys).reshape(-1).view(np.uint8).data)
    f.w(np.ascontiguousarray(vals).reshape(-1).view(np.uint8).data)
    return True


def _feed(f: Any, v: Any, depth: int = 0, ordered: bool = False) -> None:
    """値を流す。``ordered`` は台帳の行の ``ordered`` の印(入れ子の辞書にも引き継ぐ)。"""
    if depth > 64:
        raise TypeError("to_state: 入れ子が深すぎる(循環の疑い)")
    if v is None:
        f.w(b"N")
    elif isinstance(v, (bool, np.bool_)):
        f.w(b"B1" if bool(v) else b"B0")
    elif isinstance(v, enum.Enum):
        _str(f, b"E", _qual(v))
        _feed(f, v.value, depth + 1, ordered)
    elif isinstance(v, (int, np.integer)):
        _str(f, b"I", str(int(v)))
    elif isinstance(v, (float, np.floating)):
        _str(f, b"F", float(v).hex())
    elif isinstance(v, str):
        _str(f, b"S", v)
    elif isinstance(v, (bytes, bytearray, memoryview)):
        b = bytes(v)
        f.w(b"Y" + _LEN.pack(len(b)) + b)
    elif isinstance(v, np.ndarray):
        _str(f, b"A", f"{v.dtype.str}|{v.shape}")
        if v.dtype.hasobject:
            for x in v.reshape(-1).tolist():
                _feed(f, x, depth + 1, ordered)
        else:
            raw = np.ascontiguousarray(v).reshape(-1).view(np.uint8)
            f.w(_LEN.pack(int(raw.size)))
            if raw.size:
                f.w(raw.data)
    elif isinstance(v, np.random.Generator):
        f.w(b"G")
        _feed(f, v.bit_generator.state, depth + 1, ordered)
    elif dataclasses.is_dataclass(v) and not isinstance(v, type):
        flds = dataclasses.fields(v)
        _str(f, b"D", _qual(v))
        f.w(_LEN.pack(len(flds)))
        for fl in flds:
            _str(f, b"K", fl.name)
            _feed(f, getattr(v, fl.name), depth + 1, ordered)
    elif isinstance(v, tuple) and hasattr(v, "_fields"):
        _str(f, b"P", _qual(v))
        f.w(_LEN.pack(len(v)))
        for name, x in zip(v._fields, v):
            _str(f, b"K", name)
            _feed(f, x, depth + 1, ordered)
    elif isinstance(v, (list, tuple, deque)):
        f.w((b"T" if isinstance(v, tuple) else b"L") + _LEN.pack(len(v)))
        for x in v:
            _feed(f, x, depth + 1, ordered)
    elif isinstance(v, Mapping) and _feed_int_table(f, v, ordered or isinstance(v, OrderedDict)):
        pass
    elif isinstance(v, Mapping) and (ordered or isinstance(v, OrderedDict)):
        # 挿入順のまま(台帳の行の ordered の印・OrderedDict)。印 W で順に依らない直列化と区別する
        f.w(b"W" + _LEN.pack(len(v)))
        for k, x in v.items():
            f.w(to_state(k))
            _feed(f, x, depth + 1, ordered)
    elif isinstance(v, Mapping):
        items = []
        for k, x in v.items():
            items.append((to_state(k), x))
        items.sort(key=lambda kv: kv[0])
        f.w(b"M" + _LEN.pack(len(items)))
        for kb, x in items:
            f.w(kb)
            _feed(f, x, depth + 1, ordered)
    elif isinstance(v, (set, frozenset)):
        elems = sorted(to_state(x) for x in v)
        f.w(b"Z" + _LEN.pack(len(elems)))
        for e in elems:
            f.w(e)
    elif _qual(v) in VALUE_CLASSES:
        d = vars(v)
        _str(f, b"O", _qual(v))
        f.w(_LEN.pack(len(d)))
        for k in sorted(d):
            _str(f, b"K", k)
            _feed(f, d[k], depth + 1, ordered)
    else:
        raise TypeError(f"to_state: 直列化の書き手が無い型 {_qual(v)}")


def to_state(value: Any, *, ordered: bool = False) -> bytes:
    """値を決定論のバイト列にする(外の状態の直列化の書き手)。``ordered`` は辞書の挿入順を保つ。"""
    b = _Buf()
    _feed(b, value, 0, ordered)
    return b.value()


# ---------------------------------------------------------------- behavior-hash
def _world_hash(world: Any, exclude_cells: frozenset[str], exclude_pois: frozenset[str]) -> str:
    """``World.state_hash`` と同じ組み立て(除外つき)。"""
    return blake3_hex(
        (world.cells.state_hash(exclude=exclude_cells) + "\x1f"
         + world.pois.state_hash(exclude=exclude_pois)).encode("utf-8")
    )


def behavior_hash(agents: Any, world: Any, population_hash: str, schedule_hash: str,
                  activity_hash: str, owners: Mapping[str, Any], *,
                  memo: dict[str, tuple[bytes, int]] | None = None) -> str:
    """behavior-hash。

    ``Checkpoint.combined`` と同じ組み立て(SoA は軸 1 が behavior の列だけ)の末尾に、外の状態のうち
    軸 1 が behavior の行の digest(``external_digest(owners, SL.behavior_items())``)を 1 つ足したもの
    (10b-2・親の答え 3=A2 (b) は外の状態にも当てはまる)。
    """
    parts = [
        agents.registry.state_hash(exclude=SL.behavior_excluded("agents")),
        _world_hash(world, SL.behavior_excluded("cells"), SL.behavior_excluded("pois")),
        population_hash,
        schedule_hash,
    ]
    if activity_hash:
        parts.append(activity_hash)
    parts.append(external_digest(owners, SL.behavior_items(), memo=memo)[0])
    return blake3_hex("\x1f".join(parts).encode("utf-8"))


# ---------------------------------------------------------------- full-hash
_ABSENT = object()
#: 行の鍵 → ``ordered`` の印(台帳から 1 回だけ作る)。
_ORDERED: Final[dict[str, bool]] = {r.key: r.ordered for r in SL.external_rows()}


def resolve_item(owners: Mapping[str, Any], path: str) -> Any:
    """``"runner.salient.rng"`` → 値。途中の持ち主が ``None`` なら ``_ABSENT``。

    根の鍵が ``owners`` に無いのは配線の誤り(``KeyError``)。持ち主が居るのに属性が無いのは
    台帳と実装の食い違い(``AttributeError``)=どちらも黙って飛ばさない。
    """
    head, *rest = path.split(".")
    obj = owners[head]
    for i, name in enumerate(rest):
        if obj is None:
            return _ABSENT
        obj = getattr(obj, name)
    if obj is None and not rest:
        return _ABSENT
    return obj


def item_digest(owners: Mapping[str, Any], key: str, path: str) -> tuple[bytes, int]:
    """属性 1 本の digest(32 B)と直列化のバイト数(「無い」は印 1 B)。行の ``ordered`` の印を見る。"""
    v = resolve_item(owners, path)
    if v is _ABSENT:
        return b"-", 1
    f = _Feed(_blake3.blake3())
    try:
        _feed(f, v, 0, _ORDERED.get(key, False))
    except TypeError as e:
        raise TypeError(f"{key} {path}: {e}") from None
    return f.h.digest(), f.n


def external_digest(owners: Mapping[str, Any], items: tuple[tuple[str, str], ...] | None = None, *,
                    memo: dict[str, tuple[bytes, int]] | None = None) -> tuple[str, dict[str, int]]:
    """外の状態の digest と、行ごとの直列化のバイト数(``items`` の既定=full に入る行)。

    属性ごとに digest を取り(``item_digest``)、``行の鍵:道筋`` と並べて束ねる。``memo`` を渡すと同じ checkpoint の
    behavior-hash と full-hash で同じ属性を 2 度直列化しない(値は同じ=結果は変わらない)。
    """
    h = _blake3.blake3()
    sizes: dict[str, int] = {}
    for key, path in (SL.full_items() if items is None else items):
        if memo is not None and path in memo:
            d, n = memo[path]
        else:
            d, n = item_digest(owners, key, path)
            if memo is not None:
                memo[path] = (d, n)
        tag = f"{key}:{path}".encode("utf-8")
        h.update(b"R" + _LEN.pack(len(tag)) + tag + _LEN.pack(len(d)) + d)
        sizes[key] = sizes.get(key, 0) + n
    return h.hexdigest(), sizes


def full_hash(agents: Any, world: Any, pstate: Any, population_hash: str, schedule_hash: str,
              owners: Mapping[str, Any], *, memo: dict[str, tuple[bytes, int]] | None = None
              ) -> tuple[str, dict[str, int]]:
    """full-hash と、外の状態の行ごとのバイト数(``sizes``・記録用)。"""
    ext, sizes = external_digest(owners, memo=memo)
    h = _blake3.blake3()
    h.update(FULL_HEADER + _SEP)
    h.update(agents.registry.state_hash(exclude=SL.full_excluded("agents")).encode("ascii") + _SEP)
    h.update(world.cells.state_hash(exclude=SL.full_excluded("cells")).encode("ascii") + _SEP)
    h.update(world.pois.state_hash(exclude=SL.full_excluded("pois")).encode("ascii") + _SEP)
    if pstate is None:
        h.update(b"perception:-" + _SEP)
    else:
        h.update(pstate.registry.state_hash(exclude=SL.full_excluded("perception")).encode("ascii") + _SEP)
    h.update(population_hash.encode("utf-8") + _SEP)
    h.update(schedule_hash.encode("utf-8") + _SEP)
    h.update(ext.encode("ascii"))
    return h.hexdigest(), sizes


# ---------------------------------------------------------------- 10d: 食い違いの場所を探す道具の材料
def component_digests(agents: Any, world: Any, pstate: Any, owners: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    """列ごと(``置き場.列名``)と外の状態の道筋ごと(``行の鍵:道筋``)の digest(16 進 32 字)。読むだけ。

    full-hash に入る範囲(SoA は軸 2 が ``discardable`` でない列・外の状態は ``full_items``)。2 本のランの
    checkpoint を突き合わせて、最初に食い違う tick と列・持ち主の行を出す(``10d/first_diff.py``)。
    """
    soa: dict[str, str] = {}
    for place, reg in (("agents", agents.registry), ("cells", world.cells), ("pois", world.pois),
                       ("perception", None if pstate is None else pstate.registry)):
        if reg is None:
            continue
        skip = SL.full_excluded(place)
        for name, arr in reg.arrays.items():
            if name in skip:
                continue
            soa[f"{place}.{name}"] = _blake3.blake3(to_state(np.asarray(arr))).hexdigest()[:32]
    items: dict[str, str] = {}
    for key, path in SL.full_items():
        d, _n = item_digest(owners, key, path)
        items[f"{key}:{path}"] = d.hex()[:32]
    return {"soa": soa, "items": items}
