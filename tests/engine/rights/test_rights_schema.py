"""第 1 期 1-5 権利台帳の器(CP4): ``Right`` の欄・凍結・書く口は ``grant``/``revoke`` の 2 つだけ・``__setattr__`` の守り。

口の約束 1-5: ``Right``(holder・object・kind=所有/賃借/雇用/許可・since_ns/until_ns・counterparty・source・cause=1-3 の
``Event.id``)・読み口 ``Rights.holds(holder, kind, object, t)``。負の対照(書く口の外からの書き・欄の付け替え)を植えて
検査が落ちることも見る。
"""

from __future__ import annotations

import dataclasses
from pathlib import Path
from types import MappingProxyType

import numpy as np
import pytest

from shibuya.engine.rights import ledger as L

from . import rights_writers as RW

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src" / "shibuya"
LEDGER_PY = SRC / "engine" / "rights" / "ledger.py"


def _r(**kw):
    base = dict(holder=("agent", 1), object=("store", 2), kind="employ", source="試験")
    base.update(kw)
    return L.Right(**base)


# ================================================================= 欄と表
def test_fields_follow_the_contract():
    assert L.RIGHT_FIELDS == ("holder", "object", "kind", "since_ns", "until_ns", "counterparty", "source", "cause")
    assert L.KINDS == ("own", "lease", "employ", "licence")
    assert dict(L.KIND_WORDS) == {"own": "所有", "lease": "賃借", "employ": "雇用", "licence": "許可"}
    assert L.HOLDER_KINDS == ("agent", "org", "store")
    assert L.OBJECT_KINDS == ("org", "store", "parcel", "dwelling")
    assert set(L.OBJECTS_OF_KIND) == set(L.KINDS)
    assert all(set(v) <= set(L.OBJECT_KINDS) for v in L.OBJECTS_OF_KIND.values())
    assert L.ROW_BYTES == 72


@pytest.mark.parametrize("table", [L.KIND_WORDS, L.OBJECTS_OF_KIND])
def test_tables_are_read_only(table):
    assert isinstance(table, MappingProxyType)
    with pytest.raises(TypeError):
        table["own"] = ("store",)  # type: ignore[index]


def test_right_is_frozen_and_slotted():
    r = _r()
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.kind = "own"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.object = ("store", 9)  # type: ignore[misc]
    assert not hasattr(r, "__dict__")
    assert r.since_ns is None and r.until_ns is None and r.counterparty is None and r.cause is None


@pytest.mark.parametrize("kw, msg", [
    ({"holder": ("parcel", 1)}, "holder"),                    # 区画は権利を持てない
    ({"holder": ("agent", -1)}, "holder"),
    ({"holder": ("agent", True)}, "holder"),                  # bool は番号でない
    ({"holder": ["agent", 1]}, "holder"),                     # 組でない
    ({"object": ("parcel", 2)}, "object"),                    # 雇用の物は組織か店
    ({"kind": "licence", "object": ("org", 2)}, "object"),    # 許可の物は店だけ
    ({"kind": "rent"}, "種類"),
    ({"since_ns": 5, "until_ns": 5}, "since_ns"),
    ({"since_ns": -1}, "since_ns"),
    ({"until_ns": 1.5}, "until_ns"),
    ({"source": ""}, "source"),
    ({"source": None}, "source"),
    ({"cause": (1,)}, "cause"),
    ({"cause": (-1, 0)}, "cause"),
    ({"counterparty": ("dwelling", 1)}, "counterparty"),
    ({"holder": ("store", 2), "object": ("store", 2)}, "同じ"),
])
def test_bad_rights_are_refused(kw, msg):
    with pytest.raises(ValueError, match=msg):
        _r(**kw)


def test_values_are_normalised():
    r = _r(holder=("agent", np.int64(3)), since_ns=np.int64(10), cause=(np.int64(7), np.int32(1)))
    assert r.holder == ("agent", 3) and type(r.holder[1]) is int
    assert r.since_ns == 10 and type(r.since_ns) is int and r.cause == (7, 1)


# ================================================================= 書く口と読み口
def test_grant_round_trips_every_value():
    rows = [
        _r(),
        _r(holder=("store", 2), object=("parcel", 2), kind="lease", since_ns=100, until_ns=900,
           counterparty=("org", 4), source="区画", cause=(100, 3)),
        _r(holder=("org", 7), object=("dwelling", 11), kind="own", source="住まい"),
        _r(holder=("store", 5), object=("store", 6), kind="licence", source="許可", since_ns=0),
    ]
    led = L.Rights(capacity=1)  # 倍化を通す
    ids = [led.grant(r) for r in rows]
    assert ids == [0, 1, 2, 3] and len(led) == 4 and led.nbytes == 4 * L.ROW_BYTES
    assert [led.right(i) for i in ids] == rows                       # 値まで同じ
    assert list(led) == rows
    assert led.sources() == ("試験", "区画", "住まい", "許可")
    c = led.tally()
    assert c["rows"] == 4 and c["with_until"] == 1
    assert c["by_kind"] == {"own": 1, "lease": 1, "employ": 1, "licence": 1}
    assert c["by_holder_kind"] == {"agent": 1, "org": 1, "store": 2}
    assert c["by_object_kind"] == {"org": 0, "store": 2, "parcel": 1, "dwelling": 1}
    assert c["by_source"] == {"試験": 1, "区画": 1, "住まい": 1, "許可": 1}


def test_holds_and_holders_of_follow_the_time_window():
    led = L.Rights()
    led.grant(_r(holder=("store", 2), object=("parcel", 2), kind="lease", since_ns=100, until_ns=200, source="x"))
    led.grant(_r(holder=("agent", 1), object=("store", 2)))
    led.grant(_r(holder=("agent", 3), object=("store", 2)))
    lease = (("store", 2), "lease", ("parcel", 2))
    assert [led.holds(*lease, t) for t in (99, 100, 199, 200)] == [False, True, True, False]
    assert led.holds(("agent", 1), "employ", ("store", 2), 0)
    assert not led.holds(("agent", 1), "lease", ("store", 2), 0)        # 種類が違う
    assert not led.holds(("agent", 2), "employ", ("store", 2), 0)       # 持ち主が違う
    assert led.holders_of(("store", 2), "employ", 0) == (("agent", 1), ("agent", 3))
    assert led.holds_any(("agent", 3), "employ", 0) and not led.holds_any(("agent", 4), "employ", 0)
    got = led.holds_each([1, 3, 2, -1], [2, 2, 2, 2], kind="employ", holder_kind="agent", object_kind="store", t_ns=0)
    assert got.tolist() == [True, True, False, False]
    tab = led.holder_table(4, kind="employ", holder_kind="agent", object_kind="store", t_ns=0)
    assert tab.tolist() == [-1, -1, 1, -1]                               # 複数なら最初の行
    with pytest.raises(ValueError):
        led.holds(("agent", 1), "employ", ("store", 2), -1)


def test_revoke_ends_a_right_once():
    led = L.Rights()
    i = led.grant(_r(since_ns=10))
    with pytest.raises(ValueError, match="始まる前"):
        led.revoke(i, 10, None)
    led.revoke(i, 50, (50, 2))
    assert led.right(i).until_ns == 50 and led.ended_by(i) == (50, 2)
    assert led.holds(("agent", 1), "employ", ("store", 2), 49) and not led.holds(("agent", 1), "employ", ("store", 2), 50)
    assert led.tally()["with_until"] == 1
    with pytest.raises(ValueError, match="もう終わっている"):
        led.revoke(i, 60, None)
    with pytest.raises(IndexError):
        led.revoke(5, 60, None)
    with pytest.raises(ValueError):
        led.revoke(i, -1, None)


def test_grant_takes_only_a_right():
    led = L.Rights()
    with pytest.raises(TypeError):
        led.grant({"holder": ("agent", 1)})  # type: ignore[arg-type]

    class Fake:
        holder = ("agent", 1)

    with pytest.raises(TypeError):
        led.grant(Fake())  # type: ignore[arg-type]
    assert len(led) == 0


# ================================================================= __setattr__ と __delattr__ の守り(負の対照つき)
@pytest.mark.parametrize("name", ["_r_kind", "_n", "_sources", "new_attr", "grant"])
def test_attributes_cannot_be_rebound_or_deleted(name):
    led = L.Rights()
    led.grant(_r())
    before = led.right(0)
    with pytest.raises(AttributeError):
        setattr(led, name, np.zeros(3))
    with pytest.raises(AttributeError):
        delattr(led, name)
    assert led.right(0) == before and len(led) == 1


def test_readers_hand_out_copies():
    led = L.Rights()
    led.grant(_r())
    tab = led.holder_table(3, kind="employ", holder_kind="agent", object_kind="store", t_ns=0)
    tab[:] = 99
    got = led.holds_each([1], [2], kind="employ", holder_kind="agent", object_kind="store", t_ns=0)
    got[:] = False
    assert led.holder_table(3, kind="employ", holder_kind="agent", object_kind="store", t_ns=0).tolist() == [-1, -1, 1]
    assert led.holds(("agent", 1), "employ", ("store", 2), 0)


# ================================================================= 実行時の守り(object.__setattr__ も止まる・限界つき)
@pytest.mark.parametrize("name", ["_n", "_r_kind", "_sources", "_source_codes", "new_attr"])
def test_object_setattr_cannot_place_internal_names(name):
    """``Rights`` は ``__slots__`` だけ(``__dict__`` なし)=名の無い属性は ``object.__setattr__`` でも置けない(検収 M1)。"""
    led = L.Rights()
    led.grant(_r())
    with pytest.raises(AttributeError):
        object.__setattr__(led, name, 0)
    with pytest.raises(AttributeError):
        getattr(led, name)
    with pytest.raises(TypeError):
        vars(led)
    assert not hasattr(led, "__dict__") and type(led).__slots__ == ("__st",)
    assert len(led) == 1 and led.right(0) == _r()


def test_the_runtime_limit_is_the_mangled_slot():
    """限界(記録 r15/README.md): 名を変えた slot の名を知って ``object.__setattr__`` で触る形は実行時に止まらない
    (Python の限界)。src の中では AST(``rights_writers.outside_touches``)が止める。"""
    led = L.Rights()
    led.grant(_r())
    object.__setattr__(led, "_Rights__st", object.__getattribute__(led, "_Rights__st"))  # 止まらない(同じ物を置き直す)
    assert len(led) == 1
    planted = "object.__setattr__(rights, '_Rights__st', None)\n"
    assert RW.outside_touches(planted, "planted.py") != []


# ================================================================= 書く口は 2 つだけ(AST・1-9 と同じ広さ・負の対照つき)
def test_only_two_write_ports_inside_the_ledger():
    src = LEDGER_PY.read_text(encoding="utf-8")
    assert RW.ledger_violations(src) == []
    writes = RW.ledger_writes(src)
    # 正の対照: 決めた所には書きが実際にある(検査が空振りしていない)
    assert {(w.func, w.kind) for w in writes} >= {
        ("Rights._write", "content"), ("Rights._grow", "replace"), ("Rights.grant", "replace"),
        ("Rights.__init__", "replace"), ("_Store.__init__", "replace"), ("Rights.grant", "call"),
        ("Rights.revoke", "call")}


def test_nothing_outside_touches_the_ledger():
    offenders: list[str] = []
    for rel, text in RW.iter_sources(SRC, LEDGER_PY):
        offenders += RW.outside_touches(text, rel)
    assert offenders == []


_ANCHOR = "    # ------------------------------------------------------------------ 読む口\n"


@pytest.mark.parametrize("planted", [
    "    def reset(self):\n        self.__st._r_kind[0] = 1\n",                                 # 添字への代入
    "    def bump(self):\n        self.__st.n = 0\n",                                          # 行の数の差し替え
    "    def again(self):\n        self._write(0, {'_r_kind': 1})\n",                         # _write を別の口から
    "    def more(self):\n        self._grow(10)\n",
    # 検収 M1 で捕まらなかった形(1-9 と同じ広さにした)
    "    def f1(self):\n        self.__st._r_kind.fill(0)\n",                                  # .fill
    "    def f2(self):\n        np.copyto(self.__st._r_until, 0)\n",                           # np.copyto
    "    def f3(self):\n        self.__st._r_holder_id.put([0], [1])\n",                       # .put
    "    def f4(self):\n        np.add.at(self.__st._r_since, [0], 1)\n",                      # ufunc.at
    "    def f5(self):\n        col = self.__st._r_kind\n        col[0] = 3\n",                # 局所の別名
    "    def f6(self):\n        c = getattr(self.__st, '_r_kind')\n        c[:] = 0\n",        # getattr の別名
    "    def f7(self):\n        np.add(self.__st._r_kind, 1, out=self.__st._r_kind)\n",        # out=
    "    def f8(self):\n        object.__setattr__(self, '_Rights__st', None)\n",             # slot の差し替え
    "    def f9(self):\n        st = self.__st\n        for c in st._r_kind:\n            c += 1\n",  # for の別名
])
def test_negative_a_third_write_port_is_caught(planted):
    src = LEDGER_PY.read_text(encoding="utf-8")
    assert _ANCHOR in src
    assert RW.ledger_violations(src.replace(_ANCHOR, planted + "\n" + _ANCHOR, 1)) != []


@pytest.mark.parametrize("planted", [
    "rights._r_kind[0] = 2\n",
    "x = self.rights._r_since\n",
    "self.rights._write(0, {})\n",
    "led = runner.rights\nled._grow(5)\n",
    "getattr(rights, '_r_until')[0] = 0\n",
    # 検収 M1 で捕まらなかった形
    "object.__setattr__(rights, '_n', 0)\n",                                     # 外からの object.__setattr__
    "getattr(rights, '_r' + '_kind')[0] = 1\n",                                  # 名を組み立てる getattr
    "for n in ledger._COL_NAMES:\n    getattr(st, n)[0] = 0\n",                  # _COL_NAMES を回す getattr
    "from shibuya.engine.rights.ledger import _COL_NAMES\n",
    "getattr(rights, f'_r_{name}')[0] = 0\n",                                    # f 文字列の名
    "rights._Rights__st.n = 0\n",                                                # 名を変えた slot
    "setattr(rights, '_Rights__st', None)\n",
    "vars(rights)['_n'] = 0\n",
])
def test_negative_outside_writes_are_caught(planted):
    assert RW.outside_touches(planted, "planted.py") != []
