"""10f 第 3 段: 保存の形式 npz+json(K23 (a))。

既知の答え(アジェンダ §4 の T6):

- npz+json で書いて読み、``resume == straight``(10d の試験 ``tests/engine/test_resume_10d.py`` の全部)が全点一致する。
  本書は形式そのものの試験: 印の往復(型・挿入順・同一性・numpy のスカラーの型・Generator の続き)・
  ``np.load(allow_pickle=False)`` で読み pickle を開かない・許可の外のクラス名と object の配列を拒む・台帳の宣言と
  突き合わせる・旧の pickle も読める(警告)・同じオブジェクトを 2 か所から指す値の同一性・大きさ 1.1 MB 以下
  (5,000 体)と書きと読みの時間。
"""

from __future__ import annotations

import collections
import io
import json
import pickle
import time
import warnings
from pathlib import Path

import numpy as np
import pytest

from shibuya import cli
from shibuya.engine import resume as RS
from shibuya.engine import state_codec as SC
from shibuya.engine import state_ledger as SL
from shibuya.engine.run import run_day

WORLD_DIR = Path("data/world/v2")
real_data = pytest.mark.skipif(not (WORLD_DIR / "w17_schedule.parquet").exists(), reason="実世界資産が無い")
TPD = 1_440
SMALL = dict(n_agents=60, seed=1, n_cells=16, ticks=TPD, sim_days=2, checkpoint_every=60, vocab_version="v3",
             memory="on", relations="on")


def _roundtrip(v):
    return SC.loads(SC.dumps(v))


# ================================================================= 印の往復
def test_marks_roundtrip_types_order_and_values():
    from shibuya.engine.conversation import ConvState, PendingInvite, Session
    from shibuya.llm.contract import Target, TargetKind

    od = collections.OrderedDict([(3, "c"), (1, "a"), (2, "b")])
    cnt = collections.Counter({"x": 2, "y": 1})
    dd = collections.defaultdict(int, {(1, 2): 3})
    doc = {
        "t": (1, "a", (2, 3)), "s": {3, 1, 2}, "fz": frozenset({"b", "a"}), "d_int": {5: 1, 2: 2, 9: 3},
        "d_tuple": {(1, 2): 3.5, (0, 9): -1}, "od": od, "cnt": cnt, "dd": dd,
        "dq": collections.deque([1, 2, 3], maxlen=5), "f32": np.float32(0.1), "i64": np.int64(-7),
        "u8": np.uint8(250), "b": np.bool_(True), "nan": float("nan"), "inf": float("-inf"), "big": 2 ** 70,
        "str_mark_key": {"__t": "普通の辞書の鍵が印と同じ名前"}, "enum": TargetKind.CELL,
        "target": Target(kind=TargetKind.PERSON, raw="P-3", person_id=3),
        "session": Session(session_id=1, participants=[1, 2], cell=4, state=ConvState.PARTICIPATING, opened_tick=9,
                           calls={1: 2}),
        "invite": PendingInvite(inviter=1, invitee=2, tick=3, cell=4, expires_tick=5),
        "arr2d": np.arange(12, dtype=np.int16).reshape(3, 4), "empty": np.zeros(0, dtype=np.float64),
        "none": None, "list": [1, [2, [3]]],
    }
    got = _roundtrip(doc)
    assert list(got) == list(doc)
    assert got["t"] == (1, "a", (2, 3)) and type(got["t"][2]) is tuple
    assert got["s"] == {1, 2, 3} and type(got["s"]) is set and type(got["fz"]) is frozenset
    assert list(got["d_int"]) == [5, 2, 9] and list(got["d_tuple"]) == [(1, 2), (0, 9)]  # 挿入順
    assert type(got["od"]) is collections.OrderedDict and list(got["od"].items()) == list(od.items())
    assert type(got["cnt"]) is collections.Counter and got["cnt"] == cnt
    assert type(got["dd"]) is collections.defaultdict and got["dd"].default_factory is int and got["dd"][(9, 9)] == 0
    assert type(got["dq"]) is collections.deque and got["dq"].maxlen == 5 and list(got["dq"]) == [1, 2, 3]
    for k in ("f32", "i64", "u8", "b"):
        assert type(got[k]) is type(doc[k]) and got[k] == doc[k], k
    assert np.float32(got["f32"]) * np.float32(3) == np.float32(0.1) * np.float32(3)  # float32 の演算のまま
    assert np.isnan(got["nan"]) and got["inf"] == float("-inf") and got["big"] == 2 ** 70
    assert got["str_mark_key"] == {"__t": "普通の辞書の鍵が印と同じ名前"}
    assert got["enum"] is TargetKind.CELL and got["target"] == doc["target"] and type(got["target"]) is Target
    assert got["session"] == doc["session"] and got["session"].state is ConvState.PARTICIPATING
    assert got["invite"] == doc["invite"]
    assert got["arr2d"].dtype == np.int16 and np.array_equal(got["arr2d"], doc["arr2d"])
    assert got["empty"].shape == (0,) and got["none"] is None and got["list"] == [1, [2, [3]]]


def test_generator_state_continues_the_same_draws():
    from shibuya.core.rng import stream

    g = stream(1, "test.codec", 5)
    g.random(7)
    got = _roundtrip({"g": g})["g"]
    assert type(got.bit_generator).__name__ == "Philox"
    assert np.array_equal(got.random(10), g.random(10))


def test_shared_objects_keep_their_identity():
    """同じオブジェクトを 2 か所から指す値(凍結した Target・配列・list)は 1 つのまま戻る(pickle と同じ)。"""
    from shibuya.llm.contract import Target, TargetKind

    t = Target(kind=TargetKind.CELL, raw="C-1", cell_id="C-1", cell_index=1)
    arr = np.arange(5, dtype=np.int64)
    lst = [1, 2]
    doc = {"pending": [(1, t), (2, t), (3, t)], "close": {"flow": arr}, "daily": [arr, arr.copy()],
           "a": lst, "b": {"x": lst}}
    got = _roundtrip(doc)
    ts = [p[1] for p in got["pending"]]
    assert ts[0] is ts[1] is ts[2] and ts[0] == t
    assert got["close"]["flow"] is got["daily"][0] and got["daily"][1] is not got["daily"][0]
    assert got["a"] is got["b"]["x"]


def test_unwritable_values_are_refused_with_the_place():
    class Foo:
        pass

    with pytest.raises(TypeError, match="直列化の書き手が無い型.*場所: /items/x"):
        SC.dumps({"items": {"x": [Foo()]}})
    with pytest.raises(TypeError, match="object の配列"):
        SC.dumps({"a": np.array([1, "x"], dtype=object)})


# ================================================================= 読むだけでコードが動かない
def _npz(arrays: dict, meta: dict, *, allow_pickle_write: bool = False) -> bytes:
    buf = io.BytesIO()
    m = json.dumps(meta).encode("utf-8")
    np.savez(buf, **arrays, meta=np.frombuffer(m, dtype=np.uint8), allow_pickle=allow_pickle_write)
    return buf.getvalue()


def test_reader_uses_allow_pickle_false_and_never_unpickles(monkeypatch):
    seen = []
    orig_load = np.load

    def load(*a, **k):
        seen.append(k.get("allow_pickle"))
        return orig_load(*a, **k)

    def boom(*a, **k):
        raise AssertionError("pickle を開いた")

    monkeypatch.setattr(SC.np, "load", load)
    monkeypatch.setattr(pickle, "loads", boom)
    monkeypatch.setattr(pickle, "load", boom)
    monkeypatch.setattr(pickle, "Unpickler", boom)
    got = SC.loads(SC.dumps({"x": np.arange(3), "y": {1: (2, 3)}}))
    assert seen == [False] and got["y"] == {1: (2, 3)}


def test_object_arrays_in_the_npz_are_refused():
    data = _npz({"a0": np.array([{"x": 1}], dtype=object)}, {"codec": SC.CODEC, "doc": {"__nd": "a0"}},
                allow_pickle_write=True)
    with pytest.raises(SC.StateFormatError, match="object|pickle|配列"):
        SC.loads(data)


@pytest.mark.parametrize("bad,msg", [
    ({"__o": "os.system", "e": "echo"}, "許可の表に無いクラス名"),
    ({"__o": "subprocess.Popen", "f": {"args": "x"}}, "許可の表に無いクラス名"),
    ({"__o": "builtins.eval", "a": ["1"]}, "許可の表に無いクラス名"),
    ({"__g": 1, "bg": "Evil", "state": {}}, "ビット生成器"),
    ({"__d": [], "c": "UserDict"}, "辞書の型"),
    ({"__d": [], "c": "defaultdict", "df": "print"}, "defaultdict"),
    ({"__nd": "a9"}, "配列の参照"),
    ({"__t": [1], "__s": [2]}, "印が 2 つ"),
    ({"__r": 3}, "定義の前"),
    ({"__ns": "O", "v": 1}, "dtype"),
    ({"__o": "shibuya.llm.contract.TargetKind", "e": 999}, "Enum の値"),
    ({"__o": "shibuya.engine.conversation.PendingInvite", "f": {"inviter": 1}}, "欄の集合"),
    # U3: 余分な欄・__ で始まる名前・dataclass でない値のクラスの余分な欄
    ({"__o": "shibuya.engine.conversation.PendingInvite",
      "f": {"inviter": 1, "invitee": 2, "tick": 3, "cell": 4, "expires_tick": 5, "origin": -1, "evil": 1}}, "欄の集合"),
    ({"__o": "shibuya.engine.conversation.PendingInvite",
      "f": {"inviter": 1, "invitee": 2, "tick": 3, "cell": 4, "expires_tick": 5, "origin": -1, "__dict__": {"x": 1}}},
     "__ で始まる"),
    ({"__o": "shibuya.engine.conversation.PendingInvite", "f": {"__eq__": 1}}, "__ で始まる"),
    ({"__o": "shibuya.perception.p_notice.EventBudget",
      "f": {"cap": 1, "tick": None, "used": 0, "counters": None, "zzz": 1}}, "欄の集合"),
    # U4: 桁あふれ・ビット生成器の状態の形・Enum の型(どれも StateFormatError)
    ({"__ns": "|i1", "v": 1000}, "組み立てられない|OverflowError"),
    ({"__g": 1, "bg": "MT19937", "state": {"bit_generator": "MT19937", "state": {"key": [1, 2], "pos": 0}}},
     "ビット生成器の状態|組み立てられない"),
    ({"__o": "shibuya.llm.contract.TargetKind", "e": {"__t": [1]}}, "Enum の値|組み立てられない"),
], ids=["os.system", "Popen", "eval", "bitgen", "dict_type", "factory", "array_ref", "two_marks", "ref", "ns_object",
        "enum_value", "dataclass_fields", "extra_field", "dunder_dict", "dunder_eq", "value_class_extra",
        "ns_overflow", "mt_state", "enum_type"])
def test_unknown_classes_and_marks_are_refused(monkeypatch, bad, msg):
    import importlib

    imported = []
    orig = importlib.import_module

    def spy(name, *a, **k):
        imported.append(name)
        return orig(name, *a, **k)

    monkeypatch.setattr(importlib, "import_module", spy)
    data = _npz({}, {"codec": SC.CODEC, "doc": {"x": bad}})
    with pytest.raises(SC.StateFormatError, match=msg):
        SC.loads(data)
    assert not ({"os", "subprocess", "builtins"} & set(imported))  # 許可の外のモジュールは import もしない


def test_broken_meta_and_nan_constants_are_refused():
    with pytest.raises(SC.StateFormatError, match="npz"):
        SC.loads(b"\x80\x04not a zip")
    buf = io.BytesIO()
    np.savez(buf, meta=np.frombuffer(b'{"codec": "' + SC.CODEC.encode() + b'", "doc": NaN}', dtype=np.uint8))
    with pytest.raises(SC.StateFormatError, match="JSON の外"):
        SC.loads(buf.getvalue())
    with pytest.raises(SC.StateFormatError, match="形式の版"):
        SC.loads(_npz({}, {"codec": "other", "doc": 1}))
    with pytest.raises(SC.StateFormatError, match="指されない配列"):
        SC.loads(_npz({"a0": np.arange(2)}, {"codec": SC.CODEC, "doc": 1}))


def test_allowed_class_table_is_importable_and_has_no_custom_pickling():
    import dataclasses
    import enum

    for name, form in SC.ALLOWED_CLASSES.items():
        cls = SC.allowed_class(name)
        assert form in ("object", "tuple", "enum")
        assert (form == "enum") == issubclass(cls, enum.Enum), name
        if form == "tuple":
            assert issubclass(cls, tuple), name
        if form == "object":
            for hook in ("__reduce__", "__reduce_ex__", "__getstate__", "__setstate__", "__getnewargs__"):
                assert hook not in cls.__dict__, (name, hook)
            assert dataclasses.is_dataclass(cls) or name in {
                "shibuya.engine.scheduler.DeferralQueue", "shibuya.perception.p_notice.EventBudget"}, name


# ================================================================= 状態のファイル(npz+json)と台帳の宣言
@pytest.fixture(scope="module")
def mid_state(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("mid")
    straight = run_day(**SMALL)
    a = run_day(state_out=tmp / "st", stop_at_tick=750, **SMALL)
    return straight, tmp / "st" / a.resume["state_files"][-1]["file"]


def test_state_file_is_npz_and_resume_equals_straight(mid_state, monkeypatch, tmp_path):
    straight, path = mid_state
    assert path.suffix == ".npz" and path.read_bytes()[:4] == SC.ZIP_MAGIC
    side = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
    assert side["file"]["format"] == RS.STATE_FORMAT and side["file"]["bytes"] == path.stat().st_size

    def boom(*a, **k):
        raise AssertionError("pickle を開いた")

    monkeypatch.setattr(pickle, "loads", boom)
    b = run_day(resume_from=path, **SMALL)
    H = lambda r: [(c.tick, c.combined, c.behavior_hash, c.full_hash) for c in r.checkpoints if c.tick >= 750]  # noqa
    assert H(b) == H(straight) and b.resume["finished"]


def _rewrite(path: Path, tmp: Path, edit) -> Path:
    bundle = RS.read_state(path)
    edit(bundle)
    out = tmp / path.name
    RS.write_state(out, bundle)
    return out


def test_bundle_is_checked_against_the_ledger(mid_state, tmp_path):
    _straight, path = mid_state

    def wrong_dtype(b):
        b.soa["agents"]["money"] = b.soa["agents"]["money"].astype(np.int64)

    def wrong_width(b):
        b.soa["agents"]["refractory_until"] = b.soa["agents"]["refractory_until"][:, :5].copy()

    def short_column(b):
        b.soa["agents"]["cell"] = b.soa["agents"]["cell"][:-1].copy()

    def discardable_column(b):
        b.soa["agents"]["plan_cursor"] = np.zeros(len(b.soa["agents"]["cell"]), dtype=np.int16)

    def missing_item(b):
        b.items.pop(next(iter(b.items)))

    for i, (edit, msg) in enumerate([(wrong_dtype, "台帳の宣言"), (wrong_width, "台帳の宣言"), (short_column, "長さ"),
                                     (discardable_column, "捨ててよい"), (missing_item, "道筋")]):
        out = _rewrite(path, tmp_path / f"e{i}", edit)
        with pytest.raises(ValueError, match=msg):
            RS.read_state(out)


def test_item_kinds_are_checked_before_restoring(mid_state, tmp_path):
    """戻す前に今の値の型と突き合わせる(辞書が list に化けた・配列の dtype が違う)。辞書の鍵の型は、今の値に鍵が
    あるときだけ比べる(再開の新しいインスタンスの辞書は空が多い=下の単体の試験で見る)。"""
    _straight, path = mid_state

    cases = [
        ("conv._refusal_until", lambda v: list(v.items()), "型"),
        ("runner.crowd.queue_action", lambda v: v.astype(np.int64), "型"),
    ]
    for i, (p, f, msg) in enumerate(cases):
        def edit(b, p=p, f=f):
            b.items[p] = f(b.items[p])

        out = _rewrite(path, tmp_path / f"k{i}", edit)
        RS.read_state(out)  # 形の検査は通る(型は今の値と比べて初めて分かる)
        with pytest.raises(ValueError, match=msg):
            run_day(resume_from=out, **SMALL)


def test_check_item_kinds_ignores_none_and_numbers():
    from shibuya.engine.state_hashes import resolve_item  # noqa: F401 - 道筋の引き方は同じ

    class O:
        pass

    o = O()
    o.a, o.b, o.c, o.d = None, 0, np.zeros(3, np.int64), {1: 2}
    owners = {"x": o}
    items = {"x.a": np.zeros(2), "x.b": 2.5, "x.c": np.ones(5, np.int64), "x.d": {}}
    RS.check_item_kinds(owners, items)
    with pytest.raises(ValueError, match="型"):
        RS.check_item_kinds(owners, dict(items, **{"x.c": np.ones(5, np.int32)}))
    with pytest.raises(ValueError, match="鍵の型"):
        RS.check_item_kinds(owners, dict(items, **{"x.d": {"1": 2}}))


# ================================================================= 旧の pickle(10e まで・切替口つきだけ)
def test_legacy_pickle_still_reads_with_a_warning(mid_state, tmp_path):
    straight, path = mid_state
    bundle = RS.read_state(path)
    old = tmp_path / RS.STATE_NAME_PICKLE.format(T=750)
    RS.write_state_pickle(old, bundle)
    assert old.read_bytes().startswith(RS.MAGIC + b" " + RS.STATE_FORMAT_PICKLE.encode())
    with pytest.raises(SC.StateFormatError, match="pickle の形式"):  # U1: 切替口が無ければ開かない
        RS.read_state(old)
    with pytest.raises(SC.StateFormatError, match="pickle の形式"):
        run_day(resume_from=old, **SMALL)
    with pytest.warns(RS.LegacyStateFormatWarning):
        got = RS.read_state(old, allow_legacy_pickle=True)
    assert got.header["format"] == RS.STATE_FORMAT_PICKLE and set(got.items) == set(bundle.items)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RS.LegacyStateFormatWarning)
        b = run_day(resume_from=old, resume_legacy_pickle=True, **SMALL)
    H = lambda r: [(c.tick, c.combined, c.behavior_hash, c.full_hash) for c in r.checkpoints if c.tick >= 750]  # noqa
    assert H(b) == H(straight)
    # 旧の形式も壊れたものは開かない(先頭の行の sha256)
    data = old.read_bytes()
    broken = tmp_path / "x" / old.name
    broken.parent.mkdir()
    broken.write_bytes(data[:-1] + bytes([data[-1] ^ 1]))
    broken.with_suffix(".json").write_bytes(old.with_suffix(".json").read_bytes())
    with pytest.raises(ValueError, match="sha256"):
        RS.read_state(broken, allow_legacy_pickle=True)


class _Evil:
    """開くと印のファイルを作る pickle の中身(検収 U1 の再現)。"""

    def __init__(self, marker: str) -> None:
        self.marker = marker

    def __reduce__(self):
        return (open, (self.marker, "w"))


def _evil_state(path: Path, marker: Path, *, magic: bool = True) -> None:
    """10d の形の先頭の行(sha256 は中身から計算)とラン ID の合う写しを添えた、悪い pickle の状態のファイル。"""
    import hashlib

    payload = pickle.dumps({"header": {"run_id": "run-evil"}, "x": _Evil(str(marker))}, protocol=5)
    head = b" ".join([RS.MAGIC, RS.STATE_FORMAT_PICKLE.encode("ascii"), b"run-evil",
                      hashlib.sha256(payload).hexdigest().encode("ascii"), str(len(payload)).encode("ascii")]) + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((head if magic else b"") + payload)
    path.with_suffix(".json").write_text(json.dumps({"run_id": "run-evil"}), encoding="utf-8")


@pytest.mark.parametrize("name,magic,allow", [
    ("state-T00000750.npz", True, False),   # 検収役の再現(名前は .npz)
    ("state-T00000750.npz", True, True),    # 切替口があっても .pkl でなければ開かない
    ("state-T00000750.pkl", True, False),   # .pkl でも切替口が無ければ開かない
    ("state-T00000750.npz", False, True),   # 先頭の行の無い生の pickle
    ("state-T00000750.pkl", False, False),
], ids=["npz_name", "npz_name_with_switch", "pkl_without_switch", "raw_pickle_with_switch", "raw_pickle_pkl"])
def test_u1_pickle_is_never_opened_without_the_switch_and_pkl(tmp_path, monkeypatch, name, magic, allow):
    marker = tmp_path / "marker"
    path = tmp_path / "st" / name
    _evil_state(path, marker, magic=magic)

    def boom(*a, **k):
        raise AssertionError("pickle を開いた")

    monkeypatch.setattr(pickle, "loads", boom)
    with pytest.raises(SC.StateFormatError):
        RS.read_state(path, allow_legacy_pickle=allow)
    if not allow:
        with pytest.raises(SC.StateFormatError):
            run_day(resume_from=path, n_agents=20, seed=1, n_cells=9, ticks=TPD, sim_days=2)
    assert not marker.exists()


def test_u1_cli_flag_for_the_legacy_pickle():
    import argparse

    from shibuya.engine.run import add_calendar_args, calendar_kwargs_from_args

    ap = argparse.ArgumentParser()
    add_calendar_args(ap)
    assert "resume_legacy_pickle" not in calendar_kwargs_from_args(ap.parse_args(["--resume-from", "x.pkl"]))
    got = calendar_kwargs_from_args(ap.parse_args(["--resume-from", "x.pkl", "--resume-legacy-pickle"]))
    assert got["resume_legacy_pickle"] is True and "resume_legacy_pickle" in RS.FINGERPRINT_SKIP


_HEAD_CHILD = r"""
import sys
from shibuya.engine.run import run_day
import shibuya
assert "head_src" in shibuya.__file__, shibuya.__file__
run_day(state_out=sys.argv[1], stop_at_tick=750, n_agents=60, seed=1, n_cells=16, ticks=1440, sim_days=2,
        checkpoint_every=60, vocab_version="v3", memory="on", relations="on")
"""
#: 10d の pickle を書いた最後の commit(10f 第 3 段の前)。10e で旧の読み口と一緒にこの試験を消す。
LEGACY_COMMIT = "129da80"


def test_u1_resume_from_a_pkl_written_by_the_pickle_commit(tmp_path):
    """``129da80``(第 3 段の前の HEAD)の写しの src で書いた ``.pkl`` から、切替口つきで再開すると通しと全点一致する。
    切替口が無ければ開かない。"""
    import os
    import shutil
    import subprocess
    import sys
    import tarfile

    root = Path(__file__).resolve().parents[2]
    if shutil.which("git") is None:
        pytest.skip("git が無い")
    r = subprocess.run(["git", "-C", str(root), "archive", "--format=tar", LEGACY_COMMIT, "src", "docs/bench/anchors",
                        "docs/design/v2-budget-declaration.md"], capture_output=True)
    if r.returncode != 0:
        pytest.skip(f"commit {LEGACY_COMMIT} が無い")
    head = tmp_path / "head_src"
    with tarfile.open(fileobj=io.BytesIO(r.stdout)) as tf:
        tf.extractall(head, filter="data")
    (head / "data" / "calendar").mkdir(parents=True)
    shutil.copy(root / "data" / "calendar" / "syukujitsu.csv", head / "data" / "calendar" / "syukujitsu.csv")
    out = tmp_path / "st"
    env = dict(os.environ, PYTHONPATH=str(head / "src"), PYTHONIOENCODING="utf-8")
    c = subprocess.run([sys.executable, "-c", _HEAD_CHILD, str(out)], cwd=str(root), env=env, capture_output=True,
                       text=True, encoding="utf-8", timeout=600)
    assert c.returncode == 0, c.stderr[-2000:]
    pkl = next(out.glob("state-T*.pkl"))
    assert pkl.read_bytes().startswith(RS.MAGIC)
    with pytest.raises(SC.StateFormatError):
        run_day(resume_from=pkl, **SMALL)
    straight = run_day(**SMALL)
    with pytest.warns(RS.LegacyStateFormatWarning):
        b = run_day(resume_from=pkl, resume_legacy_pickle=True, **SMALL)
    H = lambda r_: [(x.tick, x.combined, x.behavior_hash, x.full_hash) for x in r_.checkpoints if x.tick >= 750]  # noqa
    assert H(b) == H(straight) and len(H(b)) > 30


# ================================================================= U4: 部品の宣言と展開した後の大きさ
def test_u4_member_checks_and_size_cap(monkeypatch):
    import zipfile

    def zip_of(members: dict[str, bytes]) -> bytes:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            for n, b in members.items():
                zf.writestr(n, b)
        return buf.getvalue()

    meta = io.BytesIO()
    np.save(meta, np.frombuffer(json.dumps({"codec": SC.CODEC, "doc": 1}).encode(), dtype=np.uint8))
    # npy でない部品
    with pytest.raises(SC.StateFormatError, match="npy でない"):
        SC.loads(zip_of({"meta.npy": meta.getvalue(), "evil.txt": b"x"}))
    # npy の見出しが巨大な形を宣言する(中身は小さい)=確保する前に止める
    big = io.BytesIO()
    np.lib.format.write_array_header_1_0(big, {"descr": "<f8", "fortran_order": False, "shape": (10 ** 12,)})
    with pytest.raises(SC.StateFormatError, match="見出しの形と大きさ"):
        SC.loads(zip_of({"meta.npy": meta.getvalue(), "a0.npy": big.getvalue() + b"\0" * 16}))
    # 深すぎる JSON(RecursionError も StateFormatError に)
    deep = io.BytesIO()
    np.save(deep, np.frombuffer(("[" * 100_000 + "]" * 100_000).encode(), dtype=np.uint8))
    with pytest.raises(SC.StateFormatError):
        SC.loads(zip_of({"meta.npy": deep.getvalue()}))
    # 展開した後の大きさの上限
    data = SC.dumps({"a": np.zeros(10_000)})
    monkeypatch.setattr(SC, "MAX_UNCOMPRESSED_BYTES", 50_000)
    with pytest.raises(SC.StateFormatError, match="上限"):
        SC.loads(data)


def test_u3_value_class_fields_match_the_class():
    """U3: dataclass でない値のクラスの欄の一覧が、クラスの属性(AST の ``self.x = …``)と同じ。"""
    from shibuya.engine import state_ledger_ast as SA

    root = Path(__file__).resolve().parents[2] / "src" / "shibuya"
    for name, fields in SC.CLASS_FIELDS.items():
        mod, _, cls = name.rpartition(".")
        rel = mod.removeprefix("shibuya.").replace(".", "/") + ".py"
        assert set(SA.class_attrs(root, rel, cls)) == set(fields), name
    for name, form in SC.ALLOWED_CLASSES.items():
        if form == "object":
            assert SC.declared_fields(SC.allowed_class(name)), name


# ================================================================= 実物の状態の同一性(日の境目・世界資産)
def _shared_paths(doc) -> dict[frozenset, int]:
    """2 か所以上から指す可変の値・配列・許可したクラスの値 → 道筋の組(id は使わず道筋で比べる)。"""
    seen: dict[int, list[str]] = collections.defaultdict(list)
    keep = []

    def walk(v, path):
        if isinstance(v, (str, int, float, bool, type(None), np.generic)) or isinstance(v, __import__("enum").Enum):
            return
        shareable = isinstance(v, (list, dict, set, np.ndarray)) or SC.ALLOWED_CLASSES.get(SC.qualname(v)) == "object"
        if shareable:
            keep.append(v)
            first = id(v) not in seen
            seen[id(v)].append(path)
            if not first:
                return
        if isinstance(v, dict):
            for k, x in v.items():
                walk(x, f"{path}[{k!r}]")
        elif isinstance(v, (list, tuple, set, frozenset)):
            for i, x in enumerate(v):
                walk(x, f"{path}[{i}]")
        elif SC.ALLOWED_CLASSES.get(SC.qualname(v)) == "object":
            for k, x in SC._object_state(v).items():
                walk(x, f"{path}.{k}")

    walk(doc, "")
    return {frozenset(p): len(p) for p in seen.values() if len(p) >= 2}


@real_data
def test_real_state_keeps_shared_identity_and_roundtrips(tmp_path, monkeypatch):
    got: dict = {}
    orig = RS.write_state

    def spy(path, bundle):
        got["bundle"] = bundle
        return orig(path, bundle)

    monkeypatch.setattr(RS, "write_state", spy)
    kw = dict(n_agents=300, seed=1, world_dir=str(WORLD_DIR), sim_days=2, vocab_version="v3", activity=True,
              checkpoint_every=360)
    a = cli.run(state_out=tmp_path / "st", stop_at_tick=TPD, **kw)
    path = tmp_path / "st" / a.resume["state_files"][-1]["file"]
    b0 = got["bundle"]
    b1 = RS.read_state(path)
    want = _shared_paths({"soa": b0.soa, "items": b0.items, "inflight": b0.inflight})
    have = _shared_paths({"soa": b1.soa, "items": b1.items, "inflight": b1.inflight})
    assert want == have and want  # 同じ組が同じように共有される
    flow = [p for p in want if any("_last_close" in x for x in p)]
    assert flow, "金の台帳の _last_close.flow と _flow_daily[0] の共有が見つからない"
    # 値も同じ(full-hash の直列化で比べる)
    from shibuya.engine.state_hashes import to_state

    for p in b0.items:
        assert to_state(b1.items[p]) == to_state(b0.items[p]), p


# ================================================================= 大きさと時間(5,000 体)
@real_data
@pytest.mark.slow
def test_size_and_time_5000(tmp_path, monkeypatch):
    """既定 v3・5,000 体・seed 1・テープつき・2 日のランを T=1440 で止めた状態: 1.1 MB 以下。pickle と比べる。"""
    got: dict = {}
    orig = RS.write_state

    def spy(path, bundle):
        got["bundle"] = bundle
        return orig(path, bundle)

    monkeypatch.setattr(RS, "write_state", spy)
    kw = dict(n_agents=5000, seed=1, world_dir=str(WORLD_DIR), sim_days=2, vocab_version="v3", activity=True)
    a = cli.run(state_out=tmp_path / "st", stop_at_tick=TPD, tape_path=tmp_path / "tape", **kw)
    f = a.resume["state_files"][-1]
    path = tmp_path / "st" / f["file"]
    size = path.stat().st_size
    assert size <= 1_100_000, size
    bundle = got["bundle"]
    t = time.perf_counter()
    RS.write_state(tmp_path / "w" / "x.npz", bundle)
    t_write = time.perf_counter() - t
    t = time.perf_counter()
    RS.read_state(tmp_path / "w" / "x.npz")
    t_read = time.perf_counter() - t
    n_old = RS.write_state_pickle(tmp_path / "p" / "x.pkl", bundle)
    print(json.dumps({"npz_bytes": size, "pickle_bytes": n_old, "ratio": round(size / n_old, 3),
                      "write_s": round(t_write, 3), "read_s": round(t_read, 3)}))
    assert size < 0.35 * n_old
    assert t_write < 5.0 and t_read < 5.0  # 日に 1 回(予算の目安は 10e で再宣言)
    assert SL.LEDGER_VERSION == bundle.header["ledger_version"]
