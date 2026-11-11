"""移す段 1(返事その 7 §4-2 の 3・計画 docs/reference/package-map-final-2026-11-09.md §7-1): クラスの名の固定の表。

クラスの「モジュール.クラス名」はハッシュ・状態のファイル・設定の指紋・系ごとの指紋に入る。ファイルを動かすと名が
変わり final が変わる(案 K の実測)。だから名は ``engine.class_ids`` の表(と、表に書けないクラスの置き場の宣言)から
引く。ここで確かめること:

1. 網羅: src(build を除く)の全部のクラス(AST)の名が、表の鍵と「置き場で宣言するクラス」の和と同じ。
2. 凍結: 凍結の JSON(凍結の名 → ``__qualname__``)が表の値と宣言の値と同じで、どの行も値の末尾が鍵のクラスの
   ``__qualname__``(値どうしの入れ替えを落とす=検収 M3)。
3. 1 対 1: 値が重ならない・``class_path`` が鍵に戻る・許可の表の型が今の名に戻る。表にも宣言にも無い ``shibuya`` の型は
   止め、``shibuya`` の外と構築の段の型は今の名のまま(検収 M2)。
4. 入口: 4 ファイルの 5 つの関数が ``class_id``・``class_path`` を通り、``__module__`` と ``__qualname__`` を
   連ねる式が残っていない。``allowed_class`` の名の確かめに振る舞いの負の対照(検収 M6)。
5. 動かしたふり: 試験の中で 3 つの型(dataclass・Enum・値のクラス)の ``__module__`` を書き換え、表の鍵をそれに
   合わせると、値の直列化(ハッシュ)・状態のファイル・設定の指紋・系ごとの指紋と、短いランの全 checkpoint・状態の
   ファイル・再開が、書き換える前と同じ。表を合わせないと止まるか変わる(負の対照)。CP12 の実験の条件の型は置き場の
   宣言で、系ごとの指紋の外の状態の digest の経路でも名が変わらない(検収 M1)。
6. 往復: 許可の表の全部の名が ``allowed_class`` で組み立てられる。
7. 既定のラン・止めて再開・系ごとの指紋(probe)で、表に無い ``shibuya`` の型は 0 件(検収 M2)。

表は道具 ``docs/bench/analysis/move-346/tools/gen_class_ids.py`` で作る(手で書かない)。
"""

from __future__ import annotations

import ast
import io
import json
import re
import sys
import types
from pathlib import Path
from types import MappingProxyType

import numpy as np
import pytest

from shibuya.foundation.types import EventClass
from shibuya.engine import class_ids as CI
from shibuya.engine import resume as RS
from shibuya.engine import state_codec as SC
from shibuya.engine import state_hashes as SH
from shibuya.engine.arbiter import WakeCandidates
from shibuya.engine.class_ids import CLASS_IDS, class_id, class_path
from shibuya.foundation.journal import log as EV
from shibuya.foundation.ports import experiment_gate as GATE
from shibuya.engine.run import run_day
from shibuya.foundation.queues.scheduler import DeferralQueue
from shibuya.engine.systems import probe as PR

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
PKG = SRC / "shibuya"
FROZEN = json.loads(Path(__file__).with_name("class_ids_frozen.json").read_text(encoding="utf-8"))["names"]
#: 入口の 4 ファイル(src/shibuya からの道筋)と、表を通る関数(関数の名 → 呼ぶはずの名)。
ENTRY_FILES: dict[str, dict[str, set[str]]] = {
    "engine/state_hashes.py": {"_qual": {"class_id"}},
    "engine/state_codec.py": {"qualname": {"class_id"}, "allowed_class": {"class_path", "qualname"}},
    "engine/resume.py": {"_canon": {"class_id"}},
    "engine/systems/probe.py": {"plain": {"class_id"}},
}
#: CP12 の実験の条件の型の凍結の名(試験は src の外なので書いてよい)。
EXP_ID = "shibuya.engine.events.log.Experiment"
#: 同じ型の今の置き場(「モジュール.クラス名」)。凍結の名と分けて、型の ``__module__`` から作る(段 4 で置き場が動いても
#: 凍結の名は変わらない=凍結の名を置き場として使わない)。
EXP_PATH = f"{EV.Experiment.__module__}.{EV.Experiment.__qualname__}"


# ================================================================= AST の集め方(道具と別に書く=2 つの実装の突き合わせ)
def _module_name(p: Path) -> str:
    parts = list(p.relative_to(SRC).with_suffix("").parts)
    return ".".join(parts[:-1] if parts[-1] == "__init__" else parts)


def _classes(node: ast.AST, prefix: str = "") -> list[tuple[str, ast.ClassDef]]:
    out: list[tuple[str, ast.ClassDef]] = []
    for ch in ast.iter_child_nodes(node):
        if isinstance(ch, ast.ClassDef):
            out.append((prefix + ch.name, ch))
            out += _classes(ch, f"{prefix}{ch.name}.")
        elif isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out += _classes(ch, f"{prefix}{ch.name}.<locals>.")
        elif isinstance(ch, ast.Lambda):
            out += _classes(ch, f"{prefix}<lambda>.<locals>.")
        else:
            out += _classes(ch, prefix)
    return out


def _declares(cls: ast.ClassDef) -> bool:
    return any(isinstance(st, (ast.Assign, ast.AnnAssign))
               and any(isinstance(t, ast.Name) and t.id == CI.DECLARED_ATTR
                       for t in (st.targets if isinstance(st, ast.Assign) else [st.target]))
               for st in cls.body)


def src_classes() -> tuple[dict[str, str], set[str]]:
    """(「モジュール.クラス名」→ ``__qualname__``, 置き場で凍結の名を宣言するクラスの名)。"""
    quals: dict[str, str] = {}
    declared: set[str] = set()
    for p in sorted(PKG.rglob("*.py")):
        if p.relative_to(PKG).parts[0] == "build":
            continue
        for q, node in _classes(ast.parse(p.read_text(encoding="utf-8"))):
            name = f"{_module_name(p)}.{q}"
            assert name not in quals, f"同じ名のクラスが 2 つある {name}"
            quals[name] = q
            if _declares(node):
                declared.add(name)
    return quals, declared


QUALS, DECLARED = src_classes()


# ================================================================= 1 網羅
def test_table_keys_and_declarations_are_exactly_the_classes_in_src():
    assert DECLARED == {EXP_PATH}, "置き場で宣言するクラスは CP12 の型だけのはず(増やすなら理由を記録に書く)"
    missing = sorted(set(QUALS) - set(CLASS_IDS) - DECLARED)
    extra = sorted(set(CLASS_IDS) - set(QUALS))
    both = sorted(set(CLASS_IDS) & DECLARED)
    assert not missing and not extra and not both, (
        f"表に無いクラス {missing[:5]}・src に無い鍵 {extra[:5]}・表と宣言の両方 {both}"
        "(道具 docs/bench/analysis/move-346/tools/gen_class_ids.py で作り直す)")


# ================================================================= 2 凍結
def test_frozen_json_maps_each_value_to_the_qualname_of_its_class():
    assert list(FROZEN) == sorted(FROZEN), "凍結の JSON は凍結の名の昇順"
    want = {v: QUALS[k] for k, v in CLASS_IDS.items()}
    want[EV.Experiment.CLASS_ID] = QUALS[EXP_PATH]
    assert FROZEN == want
    for k, v in CLASS_IDS.items():  # 値の末尾が鍵のクラスの __qualname__(値どうしの入れ替えを落とす=検収 M3)
        assert v.endswith("." + QUALS[k]), (k, v)


def test_swapping_two_values_is_caught():
    """突然変異(``ActivityKind`` と ``AgentKind`` の値の入れ替え)を、名の集合でなく写像が落とす。"""
    # 凍結の名から今の置き場(表の鍵)を引く(段 4・段 5 で置き場が動いても同じ 2 つの型)
    a, b = class_path("shibuya.agents.state.ActivityKind"), class_path("shibuya.agents.state.AgentKind")
    ids = dict(CLASS_IDS)
    ids[a], ids[b] = ids[b], ids[a]
    assert set(ids.values()) == set(CLASS_IDS.values())  # 名の集合では同じ
    assert {v: QUALS[k] for k, v in ids.items()} != {v: QUALS[k] for k, v in CLASS_IDS.items()}
    assert not ids[a].endswith("." + QUALS[a])


# ================================================================= 3 1 対 1・表に無い型
def _allowed_types() -> dict[str, type]:
    """許可の表(状態のファイル)・値のクラス(ハッシュ)・欄の一覧の名 → 型(import して引く)。"""
    out: dict[str, type] = {}
    for name in {*SC.ALLOWED_CLASSES, *SH.VALUE_CLASSES, *SC.CLASS_FIELDS}:
        out[name] = SC.allowed_class(name) if name in SC.ALLOWED_CLASSES else _import(class_path(name))
    return out


def _import(path: str) -> type:
    import importlib

    mod, _, attr = path.rpartition(".")
    return getattr(importlib.import_module(mod), attr)


def test_one_to_one_and_back_to_the_current_name():
    vals = [*CLASS_IDS.values(), EV.Experiment.CLASS_ID]
    assert len(vals) == len(set(vals)), "凍結の名が重なる"
    for k, v in CLASS_IDS.items():
        assert class_path(v) == k
        assert CI._PATH_OF[v] == k
    for name, t in _allowed_types().items():
        assert class_id(t) == name
        assert class_path(class_id(t)) == f"{t.__module__}.{t.__qualname__}"


def test_unknown_shibuya_types_stop_and_others_keep_their_names():
    late = type("Late", (), {"__module__": "shibuya.engine.late"})  # 後から type() で足したふり
    with pytest.raises(TypeError, match="表に無い shibuya の型 shibuya.engine.late.Late"):
        class_id(late)
    with pytest.raises(TypeError, match="表に無い"):
        SH.to_state(type("NT", (tuple,), {"__module__": "shibuya.x", "_fields": ("a",)})((1,)))
    assert class_id(np.ndarray) == "numpy.ndarray"
    assert class_path("numpy.ndarray") == "numpy.ndarray"
    local = type("Local", (), {})  # 試験の中のクラス
    assert class_id(local) == f"{__name__}.Local"
    built = type("B", (), {"__module__": "shibuya.build.sched.trial"})  # 構築の段(表に載せない・動かさない)
    assert class_id(built) == "shibuya.build.sched.trial.B"
    assert class_id(type("N", (), {"__module__": "x.y", CI.DECLARED_ATTR: 1})) == "x.y.N"  # 宣言は文字列だけを読む
    base = type("Base", (), {"__module__": "x.y", CI.DECLARED_ATTR: "frozen.Base"})
    assert class_id(base) == "frozen.Base"
    assert class_id(type("Sub", (base,), {"__module__": "x.y"})) == "x.y.Sub"  # 継いだ宣言は読まない


# ================================================================= 4 入口
def _has_module_qualname_chain(tree: ast.AST) -> list[int]:
    """``__module__`` と ``__qualname__`` を 1 つの式(f 文字列・``+``・``%``・``format``)で連ねる所の行。"""
    lines = []
    for n in ast.walk(tree):
        if isinstance(n, (ast.JoinedStr, ast.BinOp, ast.Call)):
            attrs = {a.attr for a in ast.walk(n) if isinstance(a, ast.Attribute)}
            if {"__module__", "__qualname__"} <= attrs:
                lines.append(n.lineno)
    return lines


def test_entry_functions_go_through_the_table():
    for rel, funcs in ENTRY_FILES.items():
        tree = ast.parse((PKG / rel).read_text(encoding="utf-8"))
        assert not _has_module_qualname_chain(tree), f"{rel}: __module__ と __qualname__ を連ねる式が残っている"
        defs = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
        for fname, need in funcs.items():
            called = {c.func.id for c in ast.walk(defs[fname])
                      if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)}
            assert need <= called, f"{rel}:{fname} が {sorted(need - called)} を呼ばない"
    # 名を連ねるのは表の 1 か所だけ
    ci = ast.parse((PKG / "engine" / "class_ids.py").read_text(encoding="utf-8"))
    assert len(_has_module_qualname_chain(ci)) == 1


def test_allowed_class_refuses_a_path_that_points_to_another_class(monkeypatch):
    """検収 M6: 凍結の名の import 先(``_PATH_OF``)が別のクラスを指せば ``StateFormatError`` で止まる。"""
    name = "shibuya.engine.arbiter.WakeCandidates"  # 凍結の名
    other = class_path("shibuya.engine.scheduler.DeferralQueue")  # 別のクラスの今の置き場(凍結の名から引く)
    assert other == f"{DeferralQueue.__module__}.{DeferralQueue.__qualname__}"
    paths = dict(CI._PATH_OF)
    paths[name] = other
    monkeypatch.setattr(CI, "_PATH_OF", MappingProxyType(paths))
    monkeypatch.setattr(SC, "_CLASS_CACHE", {})
    with pytest.raises(SC.StateFormatError, match="許可の表の名前がクラスを指さない"):
        SC.allowed_class(name)
    with pytest.raises(SC.StateFormatError):  # 状態のファイルの読みでも止まる
        SC.loads(SC.dumps({"w": _sample()["wake"]}))


# ================================================================= 5 動かしたふり
MOVED = (WakeCandidates, EventClass, DeferralQueue)


def _pretend_moved(monkeypatch: pytest.MonkeyPatch, *, table: bool = True, classes: tuple[type, ...] = MOVED,
                   head: str = "shibuya._moved_for_test.") -> dict[str, str]:
    """型の ``__module__`` を試験の中だけ別の置き場(``head`` の下)に書き換える。``table`` なら表の鍵も合わせる。旧 → 新の名。"""
    ids = dict(CI.CLASS_IDS)
    moved: dict[str, str] = {}
    for cls in classes:
        old = f"{cls.__module__}.{cls.__qualname__}"
        new_mod = head + cls.__module__.rpartition(".")[2]
        fake = sys.modules.get(new_mod) or types.ModuleType(new_mod)
        setattr(fake, cls.__name__, cls)
        monkeypatch.setitem(sys.modules, new_mod, fake)
        monkeypatch.setattr(cls, "__module__", new_mod)
        new = f"{new_mod}.{cls.__qualname__}"
        moved[old] = new
        if table:
            ids[new] = ids.pop(old)
    monkeypatch.setattr(CI, "CLASS_IDS", MappingProxyType(ids))
    monkeypatch.setattr(CI, "_PATH_OF", MappingProxyType({v: k for k, v in ids.items()}))
    monkeypatch.setattr(SC, "_CLASS_CACHE", {})
    return moved


def _sample() -> dict:
    wc = WakeCandidates(agent_id=np.arange(3, dtype=np.int64), condition=np.zeros(3, dtype=np.int8),
                        class_rank=np.full(3, int(EventClass.CELL), dtype=np.int64),
                        since_tick=np.zeros(3, dtype=np.int64))
    return {"wake": wc, "cls": EventClass.CONVERSATION, "list": [EventClass.CELL, wc]}


def _unit_bytes() -> tuple:
    doc = _sample()
    raw = SC.dumps(doc)
    meta = np.load(io.BytesIO(raw), allow_pickle=False)["meta"].tobytes()
    back = SC.loads(raw)
    assert type(back["wake"]) is WakeCandidates and back["cls"] is EventClass.CONVERSATION
    dq = DeferralQueue.__new__(DeferralQueue)
    return (SH.to_state(doc), meta, SH.to_state(back), RS._canon({"x": doc["wake"]}),
            PR.plain(dq), PR.plain(doc))


def test_pretend_move_keeps_hash_state_file_and_fingerprint_bytes(monkeypatch):
    before = _unit_bytes()
    assert b"shibuya.engine.arbiter.WakeCandidates" in before[0]  # 凍結の名がバイトに入る
    place = class_path("shibuya.engine.arbiter.WakeCandidates")  # 動かしたふりの前の今の置き場
    with monkeypatch.context() as m:
        moved = _pretend_moved(m)
        assert class_id(WakeCandidates) == "shibuya.engine.arbiter.WakeCandidates"
        assert class_path("shibuya.engine.arbiter.WakeCandidates") == moved[place]
        assert _unit_bytes() == before
    with monkeypatch.context() as m:  # 負の対照 1: 表を合わせない shibuya の置き場=表に無い型で止まる
        _pretend_moved(m, table=False)
        doc = _sample()
        for f in (SH.to_state, SC.dumps, lambda d: RS._canon({"x": d["wake"]})):
            with pytest.raises(TypeError, match="表に無い"):
                f(doc)
    with monkeypatch.context() as m:  # 負の対照 2: shibuya の外へ動かしたふり=名が変わりハッシュと指紋が動く
        _pretend_moved(m, table=False, head="moved_outside_for_test.")
        doc = _sample()
        assert SH.to_state(doc) != before[0]
        assert RS._canon({"x": doc["wake"]}) != before[3]
        assert PR.plain(DeferralQueue.__new__(DeferralQueue)) != before[4]


def _experiment_log() -> EV.EventLog:
    log = EV.EventLog()
    GATE.admit(log, "cond-A", what="過程:opening", who="engine", origin="実験")
    assert len(log._cz_experiments) == 1
    return log


def _probe_snap(log: EV.EventLog) -> str:
    """系ごとの指紋の外の状態の digest(``probe.snapshot`` の ``ext`` の行 E の ``events._cz_experiments``)。"""
    view = PR.View(agents=None, world=None, pstate=None, owners={"events": log}, tally={}, result=None)
    return PR.snapshot(view, families=("ext",))["E:events._cz_experiments"]


def _probe_ext(log: EV.EventLog) -> tuple[str, tuple[bytes, int]]:
    """``probe.snapshot`` の値と、その下の ``item_digest``(=probe が呼ぶ口)。"""
    return _probe_snap(log), SH.item_digest({"events": log}, "E", "events._cz_experiments")


def test_cp12_type_keeps_its_frozen_name_on_the_probe_path(monkeypatch):
    """検収 M1: 実験の条件の型は表に書けない(CP12)ので置き場で凍結の名を宣言する。probe の外の状態の digest の経路
    (行 E の ``events._cz_experiments``)でも、置き場を動かしたふりで値が変わらない。"""
    assert ("E", "events._cz_experiments") in PR._ext_rows()
    assert EV.Experiment.__dict__[CI.DECLARED_ATTR] == EXP_ID == class_id(EV.Experiment)
    log = _experiment_log()
    assert EXP_ID.encode() in SH.to_state(log._cz_experiments)  # 名がバイトに入る
    before = _probe_ext(log)
    assert not before[0].startswith(("X:", "ERR:")), before[0]  # 代わりの digest でなく item_digest の値
    with monkeypatch.context() as m:  # 動かしたふり(置き場の名だけ替える)=宣言の名なので同じ
        m.setattr(EV.Experiment, "__module__", "shibuya._moved_for_test.log")
        assert _probe_ext(log) == before
    with monkeypatch.context() as m:  # 負の対照 1: 宣言を外すと shibuya の型は止まる(probe は代わりの digest に落ちる)
        m.setattr(EV.Experiment, "__module__", "shibuya._moved_for_test.log")
        m.delattr(EV.Experiment, CI.DECLARED_ATTR)
        with pytest.raises(TypeError, match="表に無い"):
            SH.item_digest({"events": log}, "E", "events._cz_experiments")
        assert _probe_snap(log).startswith("X:")
    with monkeypatch.context() as m:  # 負の対照 2: 宣言を外して shibuya の外へ=名が変わり digest が動く
        m.setattr(EV.Experiment, "__module__", "moved_outside_for_test.log")
        m.delattr(EV.Experiment, CI.DECLARED_ATTR)
        assert _probe_ext(log) != before


RUN_KW = dict(n_agents=30, seed=1, n_cells=9, ticks=1440, checkpoint_every=360)
STOP = 750


def _run_bytes(tmp: Path) -> tuple:
    """止める → 状態のファイル → 再開。全 checkpoint の 3 つのハッシュ・状態のファイルの中身・見出しの指紋。"""
    a = run_day(state_out=tmp / "s", stop_at_tick=STOP, sim_days=2, **RUN_KW)
    f = a.resume["state_files"][-1]
    raw = (tmp / "s" / f["file"]).read_bytes()
    z = np.load(io.BytesIO(raw), allow_pickle=False)
    parts = {k: z[k].tobytes() for k in sorted(z.files)}
    meta = json.loads(parts["meta"])
    del meta["doc"]["header"]["run_id"]  # ランごとに違う ID(同じランを 2 回回しても違う=比べない)
    parts["meta"] = json.dumps(meta, ensure_ascii=False, sort_keys=True).encode("utf-8")
    head = json.loads((tmp / "s" / f["file"]).with_suffix(".json").read_text(encoding="utf-8"))
    b = run_day(resume_from=tmp / "s" / f["file"], sim_days=2, **RUN_KW)
    hashes = [(c.tick, c.combined, c.behavior_hash, c.full_hash) for c in (*a.checkpoints, *b.checkpoints)]
    return hashes, parts, head.get("fingerprint"), b.final_hash


def test_pretend_move_keeps_a_short_run_and_resume(tmp_path, monkeypatch):
    before = _run_bytes(tmp_path / "a")
    meta = before[1]["meta"].decode("utf-8")
    seen = set(re.findall(r'"__o": "([^"]+)"', meta))
    assert {"shibuya.engine.arbiter.WakeCandidates", "shibuya.core.types.EventClass",
            "shibuya.engine.scheduler.DeferralQueue"} <= seen, "動かす 3 つの型が状態のファイルに流れていない"
    with monkeypatch.context() as m:
        _pretend_moved(m)
        assert _run_bytes(tmp_path / "b") == before
    with monkeypatch.context() as m:  # 負の対照 1: 表を合わせない shibuya の置き場=ランが止まる
        _pretend_moved(m, table=False)
        with pytest.raises(TypeError, match="表に無い"):
            run_day(sim_days=2, **RUN_KW)
    with monkeypatch.context() as m:  # 負の対照 2: shibuya の外へ=behavior-hash(final)と full-hash が動く
        _pretend_moved(m, table=False, classes=(WakeCandidates, EventClass), head="moved_outside_for_test.")
        a = run_day(sim_days=2, **RUN_KW)
        got = [(c.tick, c.behavior_hash, c.full_hash) for c in a.checkpoints if c.tick < STOP]
        want = [(h[0], h[2], h[3]) for h in before[0] if h[0] < STOP]
        assert [g[0] for g in got] == [w[0] for w in want]
        assert all(g[1] != w[1] and g[2] != w[2] for g, w in zip(got, want))


# ================================================================= 6 往復
def test_every_allowed_class_name_is_rebuilt(monkeypatch):
    monkeypatch.setattr(SC, "_CLASS_CACHE", {})
    assert len(SC.ALLOWED_CLASSES) == 17
    for name in SC.ALLOWED_CLASSES:
        t = SC.allowed_class(name)
        assert isinstance(t, type) and class_id(t) == name and SC.qualname(t) == name
        assert name in CLASS_IDS.values()
    for name in (*SH.VALUE_CLASSES, *SC.CLASS_FIELDS):
        assert name in CLASS_IDS.values()


# ================================================================= 7 既定のラン・再開・probe で表に無い型は 0 件
def test_default_run_resume_and_probe_meet_no_unknown_shibuya_type(tmp_path, monkeypatch):
    """検収 M2: 止める口を数える口に替えて、既定のラン(止めて再開)と系ごとの指紋つきのランを回す=表に無い型 0 件。"""
    seen: list[str] = []
    monkeypatch.setattr(CI, "_unknown", lambda name: seen.append(name) or name)
    _run_bytes(tmp_path / "r")
    pr = PR.Probe(check=None, ticks=frozenset(range(0, 240, 7)) | {59, 60, 119, 120, 179, 180})
    monkeypatch.setattr(PR, "ACTIVE", pr)
    run_day(n_agents=60, seed=1, n_cells=9, ticks=240, checkpoint_every=60, vocab_version="v3")
    monkeypatch.setattr(PR, "ACTIVE", None)
    assert pr.n_snap > 0
    assert sorted(set(seen)) == []
