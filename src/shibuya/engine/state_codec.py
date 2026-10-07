"""状態のファイルの直列化 npz+json(10f・K23 (a))。読むだけでコードが動く経路を持たない。

形: 1 つの npz(``np.savez_compressed``)の中に、配列 ``a0``・``a1``・… と、``meta``(UTF-8 の JSON を uint8 の配列に
したもの)。JSON は値の木で、JSON だけでは表せない値に**印**を付ける。印は 1 つの辞書の鍵で、辞書の中に印の鍵が
1 つでもあれば印の辞書(普通の辞書は印の鍵を持たないときだけ JSON の辞書のまま書く)。

=========  ======================================================================
印         意味
=========  ======================================================================
``__t``    タプル(``[要素…]``)
``__s``    集合(``[要素…]``・要素の正準の JSON の昇順)。``"fz": 1`` なら frozenset
``__d``    鍵が文字列でない辞書・辞書の子クラス(``[[鍵, 値]…]``・**挿入順**)。``"c"`` は
           ``OrderedDict``・``Counter``・``defaultdict``(``"df"`` は既定の値の作り手の名前)
``__o``    許可したクラス(``ALLOWED_CLASSES``)の値。``"f"`` = 属性の辞書(dataclass・値のクラス)・
           ``"a"`` = 要素の list(NamedTuple・タプルの子クラス)・``"e"`` = 値(Enum)
``__nd``   配列の参照(npz の中の名前)。同じ配列を 2 か所から指すときは同じ名前(同一性を保つ)
``__g``    ``np.random.Generator``(``"bg"`` = ビット生成器の名前・``"state"`` = ``bit_generator.state``)
``__ns``   numpy のスカラー(``"v"`` は整数・真偽・浮動小数は ``float.hex``)。型を保つ(np.float32 の演算が変わらない)
``__f``    有限でない浮動小数(``float.hex``)。JSON の外の値(NaN・Infinity)を書かない
``__q``    ``collections.deque``(``"m"`` = maxlen)
``__r``    同じ可変の値を 2 か所以上から指す(最初の 1 回は ``"v"`` に中身・2 回目からは番号だけ)
=========  ======================================================================

印の ``__t``〜``__g`` はアジェンダ §2 の 5 の名前。``__ns``・``__f``・``__q``・``__r`` は実行役が足したもの
(**未リサーチ(expedient)**: numpy のスカラーの型・有限でない浮動小数・deque・同一性を落とさないため)。

**読み**: ``np.load(allow_pickle=False)``(object の配列は numpy が拒む=pickle を開かない)と、許可したクラスの表
(``ALLOWED_CLASSES``)だけで組み立てる。表に無いクラス名・知らない印・object の配列は ``StateFormatError``。
クラスの組み立ては ``cls.__new__(cls)`` に属性を置く形(``__init__``・``__post_init__``・``__setstate__`` を呼ばない)。
Enum は ``cls(値)``・NamedTuple は ``cls._make``。
"""

from __future__ import annotations

import collections
import dataclasses
import enum
import importlib
import io
import json
import math
from typing import Any, Final

import numpy as np

CODEC: Final[str] = "shibuya.engine.state_codec/v1"
MARKS: Final[frozenset[str]] = frozenset(
    {"__t", "__s", "__d", "__o", "__nd", "__g", "__ns", "__f", "__q", "__r"})
#: npz の中の JSON の名前(配列の名前 ``a<n>`` とぶつからない)。
META_KEY: Final[str] = "meta"

#: 組み立ててよいクラス(``モジュール.クラス名`` → 形)。形は ``object``(属性の辞書)・``tuple``(要素の list)・
#: ``enum``。ここに無いクラスは書けず、読めない。足すときは中身(``__getstate__`` などの独自の直列化が無いこと)を
#: 確かめる(``tests/engine/test_state_codec_10f.py`` が表の全部を検査する)。
ALLOWED_CLASSES: Final[dict[str, str]] = {
    # 計画実行層・活動・意図(日の境目の run_day.pending・intent_layer._payload)
    "shibuya.engine.activity.ActivityPayload": "tuple",
    "shibuya.llm.contract.Target": "object",
    "shibuya.llm.contract.TargetKind": "enum",
    "shibuya.engine.presence.PlanBlocks": "object",
    # アービタ・繰り延べ
    "shibuya.engine.arbiter.WakeCandidates": "object",
    "shibuya.engine.scheduler.DeferralQueue": "object",
    "shibuya.core.types.EventClass": "enum",
    "shibuya.agents.state.WakeCondition": "enum",
    # 顕著行為の予算
    "shibuya.perception.p_notice.EventBudget": "object",
    "shibuya.perception.p_notice.Counters": "object",
    # 金と物の台帳
    "shibuya.economy.ledger.DayClose": "object",
    "shibuya.economy.goods.GoodsRef": "tuple",
    # 鉄道の帰りの便(runner.rail._inbound)
    "shibuya.agents.weekly.InboundStarts": "object",
    # 会話(日の途中)
    "shibuya.engine.conversation.Session": "object",
    "shibuya.engine.conversation.PendingInvite": "object",
    "shibuya.engine.conversation.ConvState": "enum",
    # 艦隊の未着の呼
    "shibuya.llm.fleet.LLMCall": "object",
}
#: dataclass でない値のクラスの欄の一覧(``__dict__`` の鍵の集合と一致すること。10f 第 3 段の検収 U3)。
#: dataclass は ``dataclasses.fields`` の集合と一致すること。
CLASS_FIELDS: Final[dict[str, frozenset[str]]] = {
    "shibuya.engine.scheduler.DeferralQueue": frozenset({
        "classes", "_index", "_agents", "_reasons", "_since", "_reason_codes", "_reason_names", "_counters"}),
    "shibuya.perception.p_notice.EventBudget": frozenset({"cap", "tick", "used", "counters"}),
}


def declared_fields(cls: type) -> frozenset[str]:
    """許可したクラス(``object`` の形)の欄の集合。dataclass は ``fields``・ほかは ``CLASS_FIELDS``。"""
    if dataclasses.is_dataclass(cls):
        return frozenset(f.name for f in dataclasses.fields(cls))
    name = qualname(cls)
    if name not in CLASS_FIELDS:
        raise StateFormatError(f"{name}: 欄の一覧が CLASS_FIELDS に無い")
    return CLASS_FIELDS[name]


#: 展開した後の大きさの上限(npz の中の全部の部品の宣言の合計・バイト)。39 万体の見込み(pickle 336 MB・
#: 非圧縮の npz+json 約 347 MB=10f の材料 §5-3)の約 6 倍。**未リサーチ(expedient)**・10e の予算の再宣言で見直す。
MAX_UNCOMPRESSED_BYTES: Final[int] = 2 * 1024 ** 3
#: meta(JSON)の部品の上限(バイト)。
MAX_META_BYTES: Final[int] = 512 * 1024 ** 2

#: ``__g`` で組み立ててよいビット生成器(種 0 で作ってから状態を置く=OS の乱数を引かない)。
ALLOWED_BIT_GENERATORS: Final[tuple[str, ...]] = ("Philox", "PCG64", "PCG64DXSM", "MT19937", "SFC64")
#: ``__d`` の ``"c"`` で組み立ててよい辞書の子クラスと、``defaultdict`` の既定の値の作り手。
ALLOWED_DICTS: Final[dict[str, type]] = {
    "OrderedDict": collections.OrderedDict, "Counter": collections.Counter,
    "defaultdict": collections.defaultdict,
}
ALLOWED_FACTORIES: Final[dict[str, Any]] = {"int": int, "float": float, "list": list, "dict": dict, "set": set,
                                            "None": None}


class StateFormatError(ValueError):
    """状態のファイルの中身が形式・許可の表・台帳の宣言に合わない(読まない)。"""


def qualname(obj_or_cls: Any) -> str:
    t = obj_or_cls if isinstance(obj_or_cls, type) else type(obj_or_cls)
    return f"{t.__module__}.{t.__qualname__}"


_CLASS_CACHE: dict[str, type] = {}


def allowed_class(name: str) -> type:
    """許可の表の名前 → クラス(表に無ければ ``StateFormatError``)。import するのは表に書いたモジュールだけ。"""
    if name not in ALLOWED_CLASSES:
        raise StateFormatError(f"許可の表に無いクラス名: {name!r}")
    if name not in _CLASS_CACHE:
        mod, _, attr = name.rpartition(".")
        obj: Any = importlib.import_module(mod)
        obj = getattr(obj, attr)
        if not isinstance(obj, type) or qualname(obj) != name:
            raise StateFormatError(f"許可の表の名前がクラスを指さない: {name!r}")
        _CLASS_CACHE[name] = obj
    return _CLASS_CACHE[name]


def _form_of(v: Any) -> str | None:
    """許可したクラスの値なら形(``object``・``tuple``・``enum``)。"""
    return ALLOWED_CLASSES.get(qualname(v))


def _object_state(v: Any) -> dict[str, Any]:
    """属性の辞書(``__dict__`` と、全部の祖先の ``__slots__``)。pickle の既定と同じ範囲。"""
    out: dict[str, Any] = dict(vars(v)) if hasattr(v, "__dict__") else {}
    for cls in type(v).__mro__:
        sl = cls.__dict__.get("__slots__", ())
        for s in ((sl,) if isinstance(sl, str) else sl):
            if s in ("__dict__", "__weakref__") or s in out:
                continue
            if hasattr(v, s):
                out[s] = getattr(v, s)
    return out


def _canon(x: Any) -> str:
    return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


_SHAREABLE = (list, dict, set, collections.deque, np.random.Generator)


def _is_shareable(v: Any) -> bool:
    if isinstance(v, _SHAREABLE):
        return True
    form = _form_of(v)
    return form == "object"


class Encoder:
    """値の木 → (JSON にできる木, 配列の辞書)。"""

    def __init__(self) -> None:
        self.arrays: dict[str, np.ndarray] = {}
        self._arr_name: dict[int, str] = {}
        self._keep: list[Any] = []          # id の使い回しを防ぐ(数えている間・書いている間は生かす)
        self._count: dict[int, int] = {}
        self._ref: dict[int, int] = {}
        self._gstate: dict[int, Any] = {}
        self._stack: set[int] = set()
        self._noshare = 0

    # ---- 1 回目: 可変の値を何か所から指すか数える
    def _walk(self, v: Any, depth: int = 0) -> None:
        if depth > 200:
            raise TypeError("state_codec: 入れ子が深すぎる(循環の疑い)")
        if isinstance(v, np.ndarray) or v is None or isinstance(v, (bool, int, float, str, np.generic, enum.Enum)):
            return
        if _is_shareable(v):
            i = id(v)
            self._keep.append(v)
            self._count[i] = self._count.get(i, 0) + 1
            if self._count[i] > 1:
                return
        for ch in self._children(v):
            self._walk(ch, depth + 1)

    def _children(self, v: Any) -> list[Any]:
        if isinstance(v, np.random.Generator):
            st = self._gstate.get(id(v))
            if st is None:
                st = v.bit_generator.state
                self._gstate[id(v)] = st
                self._keep.append(st)
            return [st]
        if isinstance(v, dict):
            return [x for kv in v.items() for x in kv]
        if isinstance(v, (list, tuple, set, frozenset, collections.deque)):
            return list(v)
        if _form_of(v) == "object":
            return list(_object_state(v).values())
        return []

    def encode_root(self, v: Any) -> Any:
        self._walk(v)
        return self.enc(v)

    # ---- 2 回目: 書く
    def _array(self, a: np.ndarray) -> dict[str, str]:
        if a.dtype.hasobject:
            raise TypeError(f"state_codec: object の配列は書かない(dtype {a.dtype})")
        i = id(a)
        name = self._arr_name.get(i)
        if name is None:
            name = f"a{len(self.arrays)}"
            self.arrays[name] = a
            self._arr_name[i] = name
            self._keep.append(a)
        return {"__nd": name}

    def enc(self, v: Any) -> Any:
        if not _is_shareable(v):
            return self._enc(v)
        i = id(v)
        if i in self._stack:
            raise TypeError(f"state_codec: 循環した値 {qualname(v)}")
        if self._noshare == 0 and self._count.get(i, 0) > 1:
            if i in self._ref:
                return {"__r": self._ref[i]}
            n = len(self._ref)
            self._ref[i] = n
            self._stack.add(i)
            try:
                return {"__r": n, "v": self._enc(v)}
            finally:
                self._stack.discard(i)
        self._stack.add(i)
        try:
            return self._enc(v)
        finally:
            self._stack.discard(i)

    def _enc_hashable(self, v: Any) -> Any:
        """集合の要素と辞書の鍵(並べ替えると定義と参照の順が崩れるので ``__r`` を使わない=中身の写しで書く)。"""
        self._noshare += 1
        try:
            return self.enc(v)
        finally:
            self._noshare -= 1

    def _enc(self, v: Any) -> Any:  # noqa: C901 - 型の分岐を 1 か所に
        if v is None or type(v) in (bool, str):
            return v
        form = _form_of(v)
        if isinstance(v, enum.Enum):
            if form != "enum":
                raise TypeError(f"state_codec: 許可の表に無い Enum {qualname(v)}")
            return {"__o": qualname(v), "e": self.enc(v.value)}
        if type(v) is int:
            return v
        if type(v) is float:
            return v if math.isfinite(v) else {"__f": v.hex()}
        if isinstance(v, np.generic):
            if isinstance(v, np.bool_):
                val: Any = bool(v)
            elif isinstance(v, np.integer):
                val = int(v)
            elif isinstance(v, np.floating):
                val = float(v).hex()
            else:
                raise TypeError(f"state_codec: 書けない numpy のスカラー {v.dtype}")
            return {"__ns": v.dtype.str, "v": val}
        if isinstance(v, np.ndarray):
            return self._array(v)
        if isinstance(v, np.random.Generator):
            name = type(v.bit_generator).__name__
            if name not in ALLOWED_BIT_GENERATORS:
                raise TypeError(f"state_codec: 許可していないビット生成器 {name}")
            st = self._gstate.get(id(v))
            if st is None:
                st = v.bit_generator.state
                self._keep.append(st)
            return {"__g": 1, "bg": name, "state": self.enc(st)}
        if form == "tuple":
            return {"__o": qualname(v), "a": [self.enc(x) for x in v]}
        if form == "object":
            st = _object_state(v)
            need = declared_fields(type(v))
            if set(st) != need:
                raise TypeError(f"state_codec: {qualname(v)} の属性が宣言と違う(足りない {sorted(need - set(st))[:5]}・"
                                f"余分 {sorted(set(st) - need)[:5]})")
            return {"__o": qualname(v), "f": {str(k): self.enc(x) for k, x in st.items()}}
        if type(v) is tuple:
            return {"__t": [self.enc(x) for x in v]}
        if type(v) is list:
            return [self.enc(x) for x in v]
        if type(v) in (set, frozenset):
            elems = sorted((self._enc_hashable(x) for x in v), key=_canon)
            out: dict[str, Any] = {"__s": elems}
            if type(v) is frozenset:
                out["fz"] = 1
            return out
        if type(v) is collections.deque:
            return {"__q": [self.enc(x) for x in v], "m": v.maxlen}
        if isinstance(v, dict):
            t = type(v)
            if t is dict and all(type(k) is str for k in v) and not (MARKS & set(v)):
                return {k: self.enc(x) for k, x in v.items()}
            out = {"__d": [[self._enc_hashable(k), self.enc(x)] for k, x in v.items()]}
            if t is not dict:
                cname = t.__name__
                if ALLOWED_DICTS.get(cname) is not t:
                    raise TypeError(f"state_codec: 許可していない辞書の型 {qualname(v)}")
                out["c"] = cname
                if t is collections.defaultdict:
                    fac = v.default_factory  # type: ignore[attr-defined]
                    fname = "None" if fac is None else getattr(fac, "__name__", "")
                    if ALLOWED_FACTORIES.get(fname, object()) is not fac:
                        raise TypeError(f"state_codec: 許可していない defaultdict の作り手 {fac!r}")
                    out["df"] = fname
            return out
        raise TypeError(f"state_codec: 直列化の書き手が無い型 {qualname(v)}")


class Decoder:
    """(JSON の木, 配列の読み口) → 値の木。許可の表の外は ``StateFormatError``。"""

    def __init__(self, arrays: Any, names: set[str]) -> None:
        self._arrays = arrays
        self._names = names
        self._got: dict[str, np.ndarray] = {}
        self._refs: dict[int, Any] = {}
        self.used: set[str] = set()

    def _array(self, name: Any) -> np.ndarray:
        if not isinstance(name, str) or name not in self._names or name == META_KEY:
            raise StateFormatError(f"配列の参照が npz に無い: {name!r}")
        if name not in self._got:
            a = self._arrays[name]  # allow_pickle=False: object の配列は numpy が ValueError で拒む
            if not isinstance(a, np.ndarray) or a.dtype.hasobject:
                raise StateFormatError(f"配列 {name} が数の配列でない")
            self._got[name] = a
            self.used.add(name)
        return self._got[name]

    def dec(self, v: Any, depth: int = 0) -> Any:  # noqa: C901
        if depth > 400:
            raise StateFormatError("入れ子が深すぎる")
        if v is None or isinstance(v, (bool, int, float, str)):
            return v
        if isinstance(v, list):
            return [self.dec(x, depth + 1) for x in v]
        if not isinstance(v, dict):
            raise StateFormatError(f"JSON の値の型が違う: {type(v).__name__}")
        marks = MARKS & set(v)
        if not marks:
            return {k: self.dec(x, depth + 1) for k, x in v.items()}
        if len(marks) != 1:
            raise StateFormatError(f"印が 2 つ以上ある: {sorted(marks)}")
        m = next(iter(marks))
        d = depth + 1
        if m == "__r":
            n = v["__r"]
            if not isinstance(n, int) or isinstance(n, bool):
                raise StateFormatError("__r の番号が整数でない")
            if "v" in v:
                if n in self._refs:
                    raise StateFormatError(f"__r {n} が 2 回定義された")
                val = self.dec(v["v"], d)
                self._refs[n] = val
                return val
            if n not in self._refs:
                raise StateFormatError(f"__r {n} が定義の前に使われた")
            return self._refs[n]
        if m == "__nd":
            return self._array(v["__nd"])
        if m == "__t":
            return tuple(self.dec(x, d) for x in _as_list(v["__t"]))
        if m == "__s":
            elems = [self.dec(x, d) for x in _as_list(v["__s"])]
            try:
                return frozenset(elems) if v.get("fz") == 1 else set(elems)
            except TypeError as e:
                raise StateFormatError(f"集合の要素がハッシュできない: {e}") from None
        if m == "__q":
            maxlen = v.get("m")
            if maxlen is not None and (not isinstance(maxlen, int) or isinstance(maxlen, bool) or maxlen < 0):
                raise StateFormatError("deque の maxlen が違う")
            return collections.deque((self.dec(x, d) for x in _as_list(v["__q"])), maxlen)
        if m == "__f":
            s = v["__f"]
            if not isinstance(s, str):
                raise StateFormatError("__f が文字列でない")
            return float.fromhex(s)
        if m == "__ns":
            try:
                dt = np.dtype(str(v["__ns"]))
            except TypeError as e:
                raise StateFormatError(f"__ns の dtype が違う: {e}") from None
            if dt.kind not in "biuf" or dt.hasobject:
                raise StateFormatError(f"__ns に数でない dtype: {dt}")
            raw = v.get("v")
            if dt.kind == "f":
                if not isinstance(raw, str):
                    raise StateFormatError("__ns の浮動小数は hex の文字列")
                return dt.type(float.fromhex(raw))
            if not isinstance(raw, (int, bool)):
                raise StateFormatError("__ns の整数・真偽の値が違う")
            return dt.type(raw)
        if m == "__g":
            name = v.get("bg")
            if name not in ALLOWED_BIT_GENERATORS:
                raise StateFormatError(f"許可していないビット生成器: {name!r}")
            st = self.dec(v.get("state"), d)
            bg = getattr(np.random, name)(0)
            try:
                bg.state = st
            except (TypeError, ValueError, KeyError) as e:
                raise StateFormatError(f"ビット生成器の状態を置けない: {e}") from None
            return np.random.Generator(bg)
        if m == "__d":
            pairs = _as_list(v["__d"])
            cname = v.get("c")
            if cname is None:
                out: dict[Any, Any] = {}
            elif cname in ALLOWED_DICTS:
                if cname == "defaultdict":
                    fname = v.get("df")
                    if fname not in ALLOWED_FACTORIES:
                        raise StateFormatError(f"許可していない defaultdict の作り手: {fname!r}")
                    out = collections.defaultdict(ALLOWED_FACTORIES[fname])
                else:
                    out = ALLOWED_DICTS[cname]()
            else:
                raise StateFormatError(f"許可していない辞書の型: {cname!r}")
            for kv in pairs:
                if not isinstance(kv, list) or len(kv) != 2:
                    raise StateFormatError("__d の要素は [鍵, 値]")
                k = self.dec(kv[0], d)
                try:
                    out[k] = self.dec(kv[1], d)
                except TypeError as e:
                    raise StateFormatError(f"辞書の鍵がハッシュできない: {e}") from None
            return out
        # __o
        name = v["__o"]
        if not isinstance(name, str):
            raise StateFormatError("__o のクラス名が文字列でない")
        cls = allowed_class(name)
        form = ALLOWED_CLASSES[name]
        if form == "enum":
            if "e" not in v:
                raise StateFormatError(f"{name}: Enum の値が無い")
            try:
                return cls(self.dec(v["e"], d))
            except ValueError as e:
                raise StateFormatError(f"{name}: Enum の値が違う: {e}") from None
        if form == "tuple":
            vals = [self.dec(x, d) for x in _as_list(v.get("a"))]
            try:
                return cls._make(vals) if hasattr(cls, "_make") else cls(*vals)
            except TypeError as e:
                raise StateFormatError(f"{name}: 要素の数が違う: {e}") from None
        fields = v.get("f")
        if not isinstance(fields, dict):
            raise StateFormatError(f"{name}: 属性の辞書が無い")
        bad = [k for k in fields if not k.isidentifier() or k.startswith("__")]
        if bad:
            raise StateFormatError(f"{name}: 属性の名前が違う {bad[:3]!r}(識別子でない・__ で始まる)")
        need = declared_fields(cls)
        if set(fields) != need:
            raise StateFormatError(f"{name}: 欄の集合が宣言と違う(足りない {sorted(need - set(fields))[:5]}・"
                                   f"余分 {sorted(set(fields) - need)[:5]})")
        obj = cls.__new__(cls)
        for k, x in fields.items():
            object.__setattr__(obj, k, self.dec(x, d))
        return obj


def _reject_constant(c: str) -> Any:
    raise StateFormatError(f"JSON の外の値(NaN・Infinity)は読まない: {c}")


def _as_list(x: Any) -> list[Any]:
    if not isinstance(x, list):
        raise StateFormatError("印の中身が list でない")
    return x


def dumps(doc: Any) -> bytes:
    """値の木 → npz のバイト列(圧縮)。"""
    enc = Encoder()
    try:
        tree = enc.encode_root(doc)
    except TypeError as e:
        raise TypeError(f"{e}(場所: {_locate(doc)})") from None
    meta = json.dumps({"codec": CODEC, "doc": tree}, ensure_ascii=False, allow_nan=False,
                      separators=(",", ":")).encode("utf-8")
    buf = io.BytesIO()
    arrays = dict(enc.arrays)
    arrays[META_KEY] = np.frombuffer(meta, dtype=np.uint8)
    np.savez_compressed(buf, **arrays)
    return buf.getvalue()


def _locate(doc: Any, prefix: str = "", seen: set[int] | None = None) -> str:
    """書けない値の場所(書けなかったときだけ・辞書と list をたどって最初に書けない子の道筋)。循環はたどらない。"""
    seen = set() if seen is None else seen
    if id(doc) in seen or len(seen) > 10_000:
        return prefix or "/"
    seen.add(id(doc))
    kids: list[tuple[str, Any]] = []
    if isinstance(doc, dict):
        kids = [(f"{prefix}/{k}", x) for k, x in doc.items()]
    elif isinstance(doc, (list, tuple)):
        kids = [(f"{prefix}[{i}]", x) for i, x in enumerate(doc)]
    for path, x in kids:
        if id(x) in seen:
            return path
        try:
            Encoder().encode_root(x)
        except TypeError:
            return _locate(x, path, seen)
    return prefix or "/"


ZIP_MAGIC: Final[bytes] = b"PK\x03\x04"


def _check_members(npz: Any) -> None:
    """npz の部品の宣言を、開く前に検査する(展開した後の大きさの上限・npy の見出しの形と部品の大きさの一致・object
    の dtype)。npy の見出しが巨大な形を宣言すると、numpy は読む前にその大きさの配列を確保するため(U4)。"""
    zf = npz.zip
    total = 0
    for info in zf.infolist():
        total += int(info.file_size)
        if total > MAX_UNCOMPRESSED_BYTES:
            raise StateFormatError(f"展開した後の大きさが上限 {MAX_UNCOMPRESSED_BYTES} B を超える")
        if not info.filename.endswith(".npy"):
            raise StateFormatError(f"npz の中に npy でない部品がある: {info.filename!r}")
        if info.filename == META_KEY + ".npy" and info.file_size > MAX_META_BYTES:
            raise StateFormatError(f"meta が上限 {MAX_META_BYTES} B を超える")
        with zf.open(info) as f:
            version = np.lib.format.read_magic(f)
            if version == (1, 0):
                shape, _fortran, dtype = np.lib.format.read_array_header_1_0(f)
            elif version in ((2, 0), (3, 0)):
                shape, _fortran, dtype = np.lib.format.read_array_header_2_0(f)
            else:
                raise StateFormatError(f"npy の版が違う: {version}")
            header_len = f.tell()
        if dtype.hasobject:
            raise StateFormatError(f"部品 {info.filename} が object の dtype")
        count = 1
        for n in shape:
            count *= int(n)
        if header_len + count * dtype.itemsize != int(info.file_size):
            raise StateFormatError(f"部品 {info.filename} の npy の見出しの形と大きさが合わない")


def loads(data: bytes) -> Any:
    """npz のバイト列 → 値の木。``np.load(allow_pickle=False)`` と許可したクラスの表だけで組み立てる。

    拒否は全部 ``StateFormatError``(組み立ての部分は広く包む=ここで動くのは許可したクラスと numpy の中だけ)。
    """
    if not data.startswith(ZIP_MAGIC):
        raise StateFormatError("npz(zip)の印が無い")
    try:
        npz = np.load(io.BytesIO(data), allow_pickle=False)
    except Exception as e:  # noqa: BLE001 - 壊れた zip・npy の見出し
        raise StateFormatError(f"npz を開けない: {e}") from None
    try:
        with npz:
            return _loads_npz(npz)
    except StateFormatError:
        raise
    except Exception as e:  # noqa: BLE001 - 桁あふれ・深すぎる入れ子・壊れた部品など(U4)
        raise StateFormatError(f"状態のファイルを組み立てられない({type(e).__name__}: {e})") from None


def _loads_npz(npz: Any) -> Any:
    _check_members(npz)
    names = set(npz.files)
    if META_KEY not in names:
        raise StateFormatError("npz に meta が無い")
    raw = npz[META_KEY]
    if raw.dtype != np.uint8 or raw.ndim != 1:
        raise StateFormatError("meta が uint8 の 1 次元の配列でない")
    try:
        meta = json.loads(raw.tobytes().decode("utf-8"), parse_constant=_reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise StateFormatError(f"meta の JSON が壊れている: {e}") from None
    if not isinstance(meta, dict) or meta.get("codec") != CODEC:
        raise StateFormatError(f"meta の形式の版が違う: {meta.get('codec') if isinstance(meta, dict) else None!r}")
    dec = Decoder(npz, names)
    doc = dec.dec(meta.get("doc"))
    extra = names - dec.used - {META_KEY}
    if extra:
        raise StateFormatError(f"どこからも指されない配列が npz にある: {sorted(extra)[:5]}")
    return doc
