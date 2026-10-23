"""engine.rights.ledger — 権利台帳の器(第 1 期 1-5・CP4・CP3)。

口の約束 1-5(``docs/design/v2-foundation-contracts-2026-10-13.md``)・決定 10-12 §4-5 CP4(1 行=誰が・何に・どんな権利
(所有・賃借・雇用・許可)・いつからいつまで・相手・出どころ・原因=5W1H)・§1-4(権利に反する行動は止めずに
「許可のない行動」として記録する=CP3)。

- ``Right``(凍結): ``holder``(体か組織=``(種類, 番号)``)・``object``(店(POI)・区画・組織・住まい)・``kind``
  (``own``=所有・``lease``=賃借・``employ``=雇用・``licence``=許可)・``since_ns``/``until_ns``(``SimTime``。開いた
  区間は ``None``=「開始前から」「終わりなし」)・``counterparty``(相手・空欄は ``None``)・``source``(出どころ=W16 の
  列名・区のオープンデータの名・宣言)・``cause``(1-3 の ``Event.id``=``(t_ns, seq)``。初期状態は ``None``)。
- ``Rights``: 列ごとの配列(SoA)。**書く口は ``grant(right)`` と ``revoke(right_id, t_ns, cause)`` の 2 つだけ**。
  中身(列 ``_r_*``・行の数・出どころの表)は名を変えた slot 1 つ(``_Rights__st`` の ``_Store``)にあり、列を書くのは 2 つの
  口が呼ぶ ``_write``・列の差し替えは ``_grow`` だけ。書く形(代入・``fill``/``put`` などのメソッド・``np.copyto`` などの
  関数・``ufunc.at``・``out=``・局所の別名・``setattr``/``object.__setattr__``/``vars()``/``__dict__``)を台帳の中と src
  全体で AST で見る(``tests/engine/rights/rights_writers.py``=1-9 の ``money_writers`` と同じ広さ)。属性の付け替えと
  消去は ``AttributeError``(``object.__setattr__`` も名の無い属性は置けない=``__slots__``)。読み口は値か写しを返す。
  読み口は ``holds(holder, kind, object, t_ns)``・``holders_of(object, kind, t_ns)`` と、配列で引く
  ``holds_each``・``holder_table``(開閉の過程が担当の表を作る)・``tally``・``right``。
- 番号の空間(``ENTITY_KINDS``): ``agent``=体(ランの SoA の番号)・``org``=組織(W6 の組織台帳の番号=W16 の
  ``org_id``)・``store``=店(POI の番号の店の主体=お金の台帳の店舗の口座と同じ索引)・``parcel``=区画・
  ``dwelling``=住まい。
- 権利の種類ごとに取れる物の種類は閉じた表 ``OBJECTS_OF_KIND``(MappingProxyType)。
- 〔第 4 期 4-2・Q3=PENDING 仮-40〕権利の種類に ``credit``(信用の契約=5 つ目・object は信用の器 ``economy.credit.CreditBook``
  の行=番号の空間 ``credit_contract``・R-118 §4)、物の種類に ``road_segment``(道路の区間=道路の使用と占用の許可)・
  ``signboard``(看板=屋外広告物の許可)を足した(どれも行は 0 で始める=道路と看板は空間の段=第 5 期・信用は借りる判断の段)。
  閉じた表の所有に店を足した(``own → store``=W21b の店の持ち主の行 286 が閉じた表の中になる=``in_closed_table`` の列は
  世界の作り直しまで偽のまま)。許可は店・道路の区間・看板に取れる。番号の空間と種類は末尾に足した=前からの列のコードは不変。

1-5 では権利を変える行動は無い(``grant`` を呼ぶのは世界の組み立てだけ・``revoke`` の呼び手は無い=決定 CP4「権利を
変える行動は経済の段に合わせて有効にする」)。台帳は状態台帳の除外の一覧で「導出」(開閉の過程の ``rights``=SoA の
種別・W16・POI の数から作る・再開では作り直す)。権利が行動で変わる段(2-1)で状態の行にする。

先例(R-113 §5): 権利を行で持つエージェントの実装は見つからない。Dwarf Fortress の司法(止めずに事件にする)
の形だけを借りた(コードは写していない)。

**未リサーチ(expedient)**: 列の型と幅(1 行 ``ROW_BYTES``=72 B)・番号の空間の 5 つ・区間の端の表し方(``None`` は列では
int64 の最小/最大)。

逐次ループ宣言: ``grant``・``revoke`` は 1 行=定数時間(列の倍化は償却)。``holders_of`` は行の数の配列演算と当たった
行ぶんのループ。``holds_each``・``holder_table``・``tally`` は配列演算。
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from types import MappingProxyType
from typing import Any, Final, Iterator, Mapping

import numpy as np

from shibuya.core.types import SimTime

__all__ = [
    "AGENT", "ORG", "STORE", "PARCEL", "DWELLING", "ROAD_SEGMENT", "SIGNBOARD", "CREDIT_CONTRACT", "ENTITY_KINDS",
    "HOLDER_KINDS", "OBJECT_KINDS",
    "OWN", "LEASE", "EMPLOY", "LICENCE", "CREDIT", "KINDS", "KIND_WORDS", "OBJECTS_OF_KIND",
    "Ref", "EventId", "Right", "RIGHT_FIELDS", "Rights", "ROW_BYTES",
]

AGENT: Final[str] = "agent"
ORG: Final[str] = "org"
STORE: Final[str] = "store"
PARCEL: Final[str] = "parcel"
DWELLING: Final[str] = "dwelling"
#: 〔第 4 期 4-2・Q3〕道路の区間(道路の使用と占用の許可の対象)・看板(屋外広告物の許可の対象)・信用の契約(信用の器の行)。
ROAD_SEGMENT: Final[str] = "road_segment"
SIGNBOARD: Final[str] = "signboard"
CREDIT_CONTRACT: Final[str] = "credit_contract"
#: 番号の空間(並びが列のコード・〔4-2〕末尾に 3 つ足した=前の 5 つのコードは不変)。
ENTITY_KINDS: Final[tuple[str, ...]] = (AGENT, ORG, STORE, PARCEL, DWELLING, ROAD_SEGMENT, SIGNBOARD, CREDIT_CONTRACT)
#: 権利を持てるもの(体か組織=口の約束 1-5。店は POI の番号の店の主体=組織の 1 つ)。相手(``counterparty``)も同じ。
HOLDER_KINDS: Final[tuple[str, ...]] = (AGENT, ORG, STORE)
#: 権利の対象になるもの(店(POI)・区画・組織・住まい=口の約束 1-5)。
OBJECT_KINDS: Final[tuple[str, ...]] = (ORG, STORE, PARCEL, DWELLING, ROAD_SEGMENT, SIGNBOARD, CREDIT_CONTRACT)

OWN: Final[str] = "own"
LEASE: Final[str] = "lease"
EMPLOY: Final[str] = "employ"
LICENCE: Final[str] = "licence"
#: 〔第 4 期 4-2・Q3〕信用の契約(借り手=体か組織・object=信用の器の行・相手=貸す側=体のない外の組織=空欄)。
CREDIT: Final[str] = "credit"
#: 権利の種類(並びが列のコード・〔4-2〕末尾に credit)。
KINDS: Final[tuple[str, ...]] = (OWN, LEASE, EMPLOY, LICENCE, CREDIT)
KIND_WORDS: Final[Mapping[str, str]] = MappingProxyType({OWN: "所有", LEASE: "賃借", EMPLOY: "雇用", LICENCE: "許可",
                                                         CREDIT: "信用"})
#: 権利の種類ごとに取れる物の種類(閉じた表・〔4-2〕所有に店・許可に道路の区間と看板・信用に信用の契約)。
OBJECTS_OF_KIND: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType({
    OWN: (PARCEL, DWELLING, STORE),
    LEASE: (PARCEL, DWELLING),
    EMPLOY: (ORG, STORE),
    LICENCE: (STORE, ROAD_SEGMENT, SIGNBOARD),
    CREDIT: (CREDIT_CONTRACT,),
})
_ENTITY_CODES: Final[Mapping[str, int]] = MappingProxyType({k: i for i, k in enumerate(ENTITY_KINDS)})
_KIND_CODES: Final[Mapping[str, int]] = MappingProxyType({k: i for i, k in enumerate(KINDS)})

#: ``(番号の空間, 番号)``。
Ref = tuple[str, int]
#: 1-3 の出来事の id ``(t_ns, seq)``。
EventId = tuple[int, int]

_NONE_LO: Final[int] = int(np.iinfo(np.int64).min)
_NONE_HI: Final[int] = int(np.iinfo(np.int64).max)
#: ``holds_each`` が組を 1 つの整数にする幅(番号はこれ未満)。
_ID_LIMIT: Final[int] = 1 << 31


def _is_int(x: Any) -> bool:
    return isinstance(x, (int, np.integer)) and not isinstance(x, (bool, np.bool_))


def _ref(x: Any, allowed: tuple[str, ...], name: str) -> Ref:
    if not (isinstance(x, tuple) and len(x) == 2 and x[0] in allowed and _is_int(x[1]) and 0 <= int(x[1]) < _ID_LIMIT):
        raise ValueError(f"{name} は (種類, 番号) の組(種類は {allowed}・番号は 0 以上 2^31 未満)(いま {x!r})")
    return (str(x[0]), int(x[1]))


def _time(x: Any, name: str, *, none_ok: bool) -> int | None:
    if x is None and none_ok:
        return None
    if not _is_int(x) or int(x) < 0 or int(x) >= _NONE_HI:
        raise ValueError(f"{name} は 0 以上の整数(ナノ秒・SimTime){'か None' if none_ok else ''}(いま {x!r})")
    return int(x)


def _event_id(x: Any, name: str) -> EventId | None:
    if x is None:
        return None
    if not (isinstance(x, tuple) and len(x) == 2 and _is_int(x[0]) and _is_int(x[1]) and int(x[0]) >= 0
            and int(x[1]) >= 0):
        raise ValueError(f"{name} は 1-3 の出来事の id (t_ns, seq) か None(いま {x!r})")
    return (int(x[0]), int(x[1]))


def _kind(x: Any) -> str:
    if x not in _KIND_CODES:
        raise ValueError(f"権利の種類は {KINDS} のどれか(いま {x!r})")
    return str(x)


# ================================================================ 1 行
@dataclass(frozen=True, slots=True, kw_only=True)
class Right:
    """権利台帳の 1 行(凍結)。欄の名と順は口の約束 1-5。"""

    holder: Ref
    object: Ref
    kind: str
    since_ns: SimTime | None = None
    until_ns: SimTime | None = None
    counterparty: Ref | None = None
    source: str
    cause: EventId | None = None

    def __post_init__(self) -> None:
        kind = _kind(self.kind)
        object.__setattr__(self, "holder", _ref(self.holder, HOLDER_KINDS, "Right.holder"))
        object.__setattr__(self, "object", _ref(self.object, OBJECTS_OF_KIND[kind], f"Right.object({kind})"))
        if self.holder == self.object:
            raise ValueError("Right.holder と Right.object が同じ")
        since = _time(self.since_ns, "Right.since_ns", none_ok=True)
        until = _time(self.until_ns, "Right.until_ns", none_ok=True)
        if since is not None and until is not None and not since < until:
            raise ValueError(f"Right.since_ns < Right.until_ns(いま {since}・{until})")
        object.__setattr__(self, "since_ns", since)
        object.__setattr__(self, "until_ns", until)
        if self.counterparty is not None:
            object.__setattr__(self, "counterparty", _ref(self.counterparty, HOLDER_KINDS, "Right.counterparty"))
        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError("Right.source は空でない文字列(出どころ)")
        object.__setattr__(self, "cause", _event_id(self.cause, "Right.cause"))


#: ``Right`` の欄の名と順(口の約束 1-5)。
RIGHT_FIELDS: Final[tuple[str, ...]] = tuple(f.name for f in fields(Right))


# ================================================================ 台帳(列ごとの配列)
#: 列(属性の名・型・空の値)。``ROW_BYTES`` はこの和。
_COLS: Final[tuple[tuple[str, Any, int], ...]] = (
    ("_r_holder_kind", np.int8, -1),
    ("_r_holder_id", np.int64, -1),
    ("_r_object_kind", np.int8, -1),
    ("_r_object_id", np.int64, -1),
    ("_r_kind", np.int8, -1),
    ("_r_since", np.int64, _NONE_LO),
    ("_r_until", np.int64, _NONE_HI),
    ("_r_cp_kind", np.int8, -1),
    ("_r_cp_id", np.int64, -1),
    ("_r_source", np.int32, -1),
    ("_r_cause_t", np.int64, -1),
    ("_r_cause_seq", np.int32, -1),
    ("_r_end_t", np.int64, -1),
    ("_r_end_seq", np.int32, -1),
)
ROW_BYTES: Final[int] = int(sum(np.dtype(t).itemsize for _n, t, _f in _COLS))
_COL_NAMES: Final[tuple[str, ...]] = tuple(n for n, _t, _f in _COLS)


class _Store:
    """台帳の中身(列・行の数・出どころの表)。``Rights`` の名を変えた slot ``_Rights__st`` だけが持つ。

    この置き場の外から触らない(``_Rights__st``・``_Store``・列の名 ``_r_*`` を src の中で書かない=試験の AST)。書くのは
    ``Rights`` の ``__init__``・``grant``・``revoke`` が呼ぶ ``_write``・``_grow`` だけ(同じ試験)。
    """

    __slots__ = _COL_NAMES + ("n", "sources", "source_codes")

    def __init__(self, capacity: int) -> None:
        for name, t, f in _COLS:
            setattr(self, name, np.full(int(capacity), f, dtype=t))
        self.n = 0
        #: 出どころの名の表(列には番号)。足すのは ``grant`` だけ。
        self.sources: tuple[str, ...] = ()
        self.source_codes: Mapping[str, int] = MappingProxyType({})


class Rights:
    """権利台帳(列ごとの配列)。書く口は ``grant`` と ``revoke`` の 2 つだけ。

    中身は名を変えた slot 1 つ(``_Rights__st`` の ``_Store``)にある。``Rights`` は ``__slots__`` だけで ``__dict__`` を
    持たないので、``object.__setattr__(rights, "_n", 0)`` や ``object.__setattr__(rights, "_r_kind", …)`` は実行時に
    ``AttributeError`` で止まる(名の無い属性は置けない)。止められないのは名を変えた slot の名を知って触る形
    (``object.__setattr__(rights, "_Rights__st", …)``・``rights._Rights__st.n = 0``)だけ=Python の限界。src の中では
    試験の AST(``tests/engine/rights/rights_writers.py``)が止める。

    Args:
        capacity: 最初の列の長さ(足りなくなったら倍に)。
    """

    __slots__ = ("__st",)

    def __init__(self, *, capacity: int = 256) -> None:
        if int(capacity) <= 0:
            raise ValueError("capacity は正")
        object.__setattr__(self, "_Rights__st", _Store(int(capacity)))

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"Rights の書く口は grant と revoke だけ({name} は書けない)")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"Rights の書く口は grant と revoke だけ({name} は消せない)")

    # ------------------------------------------------------------------ 書く口(2 つ)
    def grant(self, right: Right) -> int:
        """権利を 1 行足し、行の番号(``right_id``)を返す。**書く口の 1 つ目**。"""
        if type(right) is not Right:
            raise TypeError(f"Rights.grant は Right だけを受け取る(いま {type(right)!r})")
        store = self.__st
        i = store.n
        if i >= store._r_kind.size:
            self._grow(i + 1)
        src = store.source_codes.get(right.source)
        if src is None:
            src = len(store.sources)
            store.sources = store.sources + (right.source,)
            store.source_codes = MappingProxyType({s: k for k, s in enumerate(store.sources)})
        cp = right.counterparty
        cause = right.cause
        self._write(i, {
            "_r_holder_kind": _ENTITY_CODES[right.holder[0]], "_r_holder_id": right.holder[1],
            "_r_object_kind": _ENTITY_CODES[right.object[0]], "_r_object_id": right.object[1],
            "_r_kind": _KIND_CODES[right.kind],
            "_r_since": _NONE_LO if right.since_ns is None else right.since_ns,
            "_r_until": _NONE_HI if right.until_ns is None else right.until_ns,
            "_r_cp_kind": -1 if cp is None else _ENTITY_CODES[cp[0]], "_r_cp_id": -1 if cp is None else cp[1],
            "_r_source": src,
            "_r_cause_t": -1 if cause is None else cause[0], "_r_cause_seq": -1 if cause is None else cause[1],
        })
        store.n = i + 1
        return i

    def revoke(self, right_id: int, t_ns: SimTime, cause: EventId | None) -> None:
        """行 ``right_id`` の権利を時刻 ``t_ns`` で終える(``until_ns`` を置く)。**書く口の 2 つ目**。

        終わっている行・始まる前の時刻は ``ValueError``。``cause`` は終わらせた出来事の id(``ended_by`` で読める)。
        """
        store = self.__st
        if not _is_int(right_id) or not 0 <= int(right_id) < store.n:
            raise IndexError(f"権利の行 {right_id!r} は無い(行は {store.n})")
        i = int(right_id)
        t = _time(t_ns, "revoke の t_ns", none_ok=False)
        c = _event_id(cause, "revoke の cause")
        if int(store._r_until[i]) != _NONE_HI:
            raise ValueError(f"権利の行 {i} はもう終わっている(until_ns={int(store._r_until[i])})")
        if not int(store._r_since[i]) < t:
            raise ValueError(f"権利の行 {i} は始まる前({int(store._r_since[i])})に終われない(t_ns={t})")
        self._write(i, {"_r_until": t, "_r_end_t": -1 if c is None else c[0], "_r_end_seq": -1 if c is None else c[1]})

    # ------------------------------------------------------------------ 内部(列を書くのは _write・差し替えは _grow だけ)
    def _write(self, i: int, values: Mapping[str, int]) -> None:
        """行 ``i`` の列を書く(呼ぶのは ``grant`` と ``revoke`` だけ=試験の AST)。"""
        store = self.__st
        for name, v in values.items():
            if name not in _COL_NAMES:
                raise KeyError(name)
            getattr(store, name)[i] = v

    def _grow(self, need: int) -> None:
        store = self.__st
        cap = max(store._r_kind.size * 2, int(need))
        for name, t, f in _COLS:
            new = np.full(cap, f, dtype=t)
            new[: store.n] = getattr(store, name)[: store.n]
            setattr(store, name, new)

    # ------------------------------------------------------------------ 読む口
    def __len__(self) -> int:
        return self.__st.n

    @property
    def nbytes(self) -> int:
        """行の列のバイト(``行数 × ROW_BYTES``)。"""
        return self.__st.n * ROW_BYTES

    def sources(self) -> tuple[str, ...]:
        """出どころの名(足した順)。"""
        return self.__st.sources

    def right(self, right_id: int) -> Right:
        """行 ``right_id`` を ``Right`` に戻す(``until_ns`` は ``revoke`` の後の値)。"""
        if not _is_int(right_id) or not 0 <= int(right_id) < self.__st.n:
            raise IndexError(right_id)
        i = int(right_id)
        since, until = int(self.__st._r_since[i]), int(self.__st._r_until[i])
        cpk = int(self.__st._r_cp_kind[i])
        ct = int(self.__st._r_cause_t[i])
        return Right(
            holder=(ENTITY_KINDS[int(self.__st._r_holder_kind[i])], int(self.__st._r_holder_id[i])),
            object=(ENTITY_KINDS[int(self.__st._r_object_kind[i])], int(self.__st._r_object_id[i])),
            kind=KINDS[int(self.__st._r_kind[i])],
            since_ns=None if since == _NONE_LO else since, until_ns=None if until == _NONE_HI else until,
            counterparty=None if cpk < 0 else (ENTITY_KINDS[cpk], int(self.__st._r_cp_id[i])),
            source=self.__st.sources[int(self.__st._r_source[i])],
            cause=None if ct < 0 else (ct, int(self.__st._r_cause_seq[i])),
        )

    def __iter__(self) -> Iterator[Right]:
        for i in range(self.__st.n):
            yield self.right(i)

    def ended_by(self, right_id: int) -> EventId | None:
        """行 ``right_id`` を終わらせた出来事の id(終わっていない・原因なしは ``None``)。"""
        self.right(right_id)
        t = int(self.__st._r_end_t[int(right_id)])
        return None if t < 0 else (t, int(self.__st._r_end_seq[int(right_id)]))

    def _active(self, t_ns: Any) -> np.ndarray:
        t = _time(t_ns, "t_ns", none_ok=False)
        n = self.__st.n
        return (self.__st._r_since[:n] <= t) & (t < self.__st._r_until[:n])

    def _rows(self, kind: str, t_ns: Any) -> np.ndarray:
        n = self.__st.n
        return self._active(t_ns) & (self.__st._r_kind[:n] == _KIND_CODES[_kind(kind)])

    def holds(self, holder: Ref, kind: str, object: Ref, t_ns: SimTime) -> bool:  # noqa: A002
        """``holder`` が時刻 ``t_ns`` に ``object`` への ``kind`` の権利を持つか(口の約束 1-5 の読み口)。"""
        h = _ref(holder, ENTITY_KINDS, "holder")
        o = _ref(object, ENTITY_KINDS, "object")
        n = self.__st.n
        m = (self._rows(kind, t_ns) & (self.__st._r_holder_kind[:n] == _ENTITY_CODES[h[0]]) & (self.__st._r_holder_id[:n] == h[1])
             & (self.__st._r_object_kind[:n] == _ENTITY_CODES[o[0]]) & (self.__st._r_object_id[:n] == o[1]))
        return bool(m.any())

    def holds_any(self, holder: Ref, kind: str, t_ns: SimTime) -> bool:
        """``holder`` が時刻 ``t_ns`` に ``kind`` の権利を 1 つでも持つか(物を問わない)。"""
        h = _ref(holder, ENTITY_KINDS, "holder")
        n = self.__st.n
        m = self._rows(kind, t_ns) & (self.__st._r_holder_kind[:n] == _ENTITY_CODES[h[0]]) & (self.__st._r_holder_id[:n] == h[1])
        return bool(m.any())

    def holders_of(self, object: Ref, kind: str, t_ns: SimTime) -> tuple[Ref, ...]:  # noqa: A002
        """時刻 ``t_ns`` に ``object`` への ``kind`` の権利を持つもの(行の順)。"""
        o = _ref(object, ENTITY_KINDS, "object")
        n = self.__st.n
        rows = np.flatnonzero(self._rows(kind, t_ns) & (self.__st._r_object_kind[:n] == _ENTITY_CODES[o[0]])
                              & (self.__st._r_object_id[:n] == o[1]))
        # 逐次ループ: 当たった行ぶん
        return tuple((ENTITY_KINDS[int(self.__st._r_holder_kind[i])], int(self.__st._r_holder_id[i])) for i in rows.tolist())

    def _pair_rows(self, kind: str, holder_kind: str, object_kind: str, t_ns: Any) -> np.ndarray:
        if holder_kind not in _ENTITY_CODES or object_kind not in _ENTITY_CODES:
            raise ValueError(f"番号の空間は {ENTITY_KINDS} のどれか(いま {holder_kind!r}・{object_kind!r})")
        n = self.__st.n
        return np.flatnonzero(self._rows(kind, t_ns) & (self.__st._r_holder_kind[:n] == _ENTITY_CODES[holder_kind])
                              & (self.__st._r_object_kind[:n] == _ENTITY_CODES[object_kind]))

    def holds_each(self, holder_ids: Any, object_ids: Any, *, kind: str, holder_kind: str, object_kind: str,
                   t_ns: SimTime) -> np.ndarray:
        """行ごとの ``holds``(``holder_ids[i]`` が ``object_ids[i]`` への権利を持つか)。番号が負の行は偽。"""
        h = np.asarray(holder_ids, dtype=np.int64).ravel()
        o = np.asarray(object_ids, dtype=np.int64).ravel()
        if h.shape != o.shape:
            raise ValueError("holder_ids と object_ids の長さが違う")
        rows = self._pair_rows(kind, holder_kind, object_kind, t_ns)
        out = np.zeros(h.size, dtype=bool)
        ok = (h >= 0) & (h < _ID_LIMIT) & (o >= 0) & (o < _ID_LIMIT)
        if rows.size == 0 or not ok.any():
            return out
        have = self.__st._r_holder_id[rows] * _ID_LIMIT + self.__st._r_object_id[rows]
        out[ok] = np.isin(h[ok] * _ID_LIMIT + o[ok], have)
        return out

    def holder_table(self, n_objects: int, *, kind: str, holder_kind: str, object_kind: str,
                     t_ns: SimTime) -> np.ndarray:
        """物の番号 0..``n_objects``−1 → 時刻 ``t_ns`` に ``kind`` の権利を持つものの番号(複数なら最初の行・無ければ −1)。"""
        out = np.full(int(n_objects), -1, dtype=np.int64)
        rows = self._pair_rows(kind, holder_kind, object_kind, t_ns)
        if rows.size == 0 or out.size == 0:
            return out
        obj = self.__st._r_object_id[rows]
        inside = obj < out.size
        obj, hid = obj[inside], self.__st._r_holder_id[rows][inside]
        uniq, first = np.unique(obj, return_index=True)
        out[uniq] = hid[first]
        return out

    def pairs(self, kind: str, holder_kind: str, object_kind: str, t_ns: SimTime) -> tuple[np.ndarray, np.ndarray]:
        """〔第 2 期 2-1〕時刻 ``t_ns`` に ``kind`` の権利の (持つものの番号, 物の番号) の組(行の順・写し)。読むだけ。

        経済の段階 2 の賃金(雇用の行の体 → 雇用主)が読む。
        """
        rows = self._pair_rows(kind, holder_kind, object_kind, t_ns)
        return (self.__st._r_holder_id[rows].astype(np.int64), self.__st._r_object_id[rows].astype(np.int64))

    def tally(self) -> dict[str, Any]:
        """行の数と分布(manifest の ``rights`` の中身=計器)。種類は 5 つとも出す(0 も)。"""
        n = self.__st.n

        def dist(col: np.ndarray, names: tuple[str, ...]) -> dict[str, int]:
            c = np.bincount(col[:n].astype(np.int64), minlength=len(names)) if n else np.zeros(len(names), np.int64)
            return {names[k]: int(c[k]) for k in range(len(names))}

        by_src = np.bincount(self.__st._r_source[:n].astype(np.int64), minlength=len(self.__st.sources)) if n else ()
        return {
            "rows": int(n),
            "with_until": int(np.count_nonzero(self.__st._r_until[:n] != _NONE_HI)),  # 終わりの時刻がある行
            "by_kind": dist(self.__st._r_kind, KINDS),
            "by_holder_kind": {k: v for k, v in dist(self.__st._r_holder_kind, ENTITY_KINDS).items() if k in HOLDER_KINDS},
            "by_object_kind": {k: v for k, v in dist(self.__st._r_object_kind, ENTITY_KINDS).items() if k in OBJECT_KINDS},
            "by_source": {s: int(by_src[k]) for k, s in enumerate(self.__st.sources)},
            "bytes": int(self.nbytes),
        }
