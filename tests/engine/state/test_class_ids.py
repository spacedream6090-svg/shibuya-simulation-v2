"""移す段 1(返事その 7 §4-2 の 3・計画 docs/reference/package-map-final-2026-11-09.md §7-1): クラスの名の固定の表。

クラスの「モジュール.クラス名」はハッシュ・状態のファイル・設定の指紋・系ごとの指紋に入る。ファイルを動かすと名が
変わり final が変わる(案 K の実測)。だから名は ``engine.class_ids`` の表から引く。ここで確かめること:

1. 網羅: src(build を除く)の全部のクラス(AST)の名が、表の鍵の集合と同じ(載せない CP12 の型 1 つを除く。その型が
   ハッシュにも状態のファイルにも入らないことも確かめる)。
2. 凍結: 表の値の集合が凍結の JSON と同じ(値は変えない。クラスを足したら両方に足す)。
3. 1 対 1: 値が重ならない・``class_path`` が鍵に戻る・許可の表の型が今の名に戻る。
4. 入口: 4 ファイルの 5 つの関数が ``class_id``・``class_path`` を通り、``__module__`` と ``__qualname__`` を
   連ねる式が残っていない。
5. 動かしたふり: 試験の中で 3 つの型(dataclass・Enum・値のクラス)の ``__module__`` を書き換え、表の鍵をそれに
   合わせると、値の直列化(ハッシュ)・状態のファイル・設定の指紋・系ごとの指紋と、短いランの全 checkpoint・状態の
   ファイル・再開が、書き換える前と同じ。表を合わせないと変わる(負の対照)。
6. 往復: 許可の表の全部の名が ``allowed_class`` で組み立てられる。

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

from shibuya.core.types import EventClass
from shibuya.engine import class_ids as CI
from shibuya.engine import resume as RS
from shibuya.engine import state_codec as SC
from shibuya.engine import state_hashes as SH
from shibuya.engine import state_ledger as SL
from shibuya.engine.arbiter import WakeCandidates
from shibuya.engine.events import log as EV
from shibuya.engine.class_ids import CLASS_IDS, class_id, class_path
from shibuya.engine.run import run_day
from shibuya.engine.scheduler import DeferralQueue
from shibuya.engine.systems import probe as PR

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
PKG = SRC / "shibuya"
FROZEN = Path(__file__).with_name("class_ids_frozen.json")
#: 入口の 4 ファイル(src/shibuya からの道筋)と、表を通る関数(関数の名 → 呼ぶはずの名)。
ENTRY_FILES: dict[str, dict[str, set[str]]] = {
    "engine/state_hashes.py": {"_qual": {"class_id"}},
    "engine/state_codec.py": {"qualname": {"class_id"}, "allowed_class": {"class_path", "qualname"}},
    "engine/resume.py": {"_canon": {"class_id"}},
    "engine/systems/probe.py": {"plain": {"class_id"}},
}


# ================================================================= AST の集め方(道具と別に書く=2 つの実装の突き合わせ)
def _module_name(p: Path) -> str:
    parts = list(p.relative_to(SRC).with_suffix("").parts)
    return ".".join(parts[:-1] if parts[-1] == "__init__" else parts)


def _qualnames(node: ast.AST, prefix: str = "") -> list[str]:
    out: list[str] = []
    for ch in ast.iter_child_nodes(node):
        if isinstance(ch, ast.ClassDef):
            out.append(prefix + ch.name)
            out += _qualnames(ch, f"{prefix}{ch.name}.")
        elif isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out += _qualnames(ch, f"{prefix}{ch.name}.<locals>.")
        elif isinstance(ch, ast.Lambda):
            out += _qualnames(ch, f"{prefix}<lambda>.<locals>.")
        else:
            out += _qualnames(ch, prefix)
    return out


def src_classes() -> list[str]:
    names: list[str] = []
    for p in sorted(PKG.rglob("*.py")):
        if p.relative_to(PKG).parts[0] == "build":
            continue
        tree = ast.parse(p.read_text(encoding="utf-8"))
        names += [f"{_module_name(p)}.{q}" for q in _qualnames(tree)]
    return names


# ================================================================= 1 網羅
#: 表に載せないクラス(道具の ``EXCLUDE`` と同じ)。CP12: 実験の条件の型の名は src の 2 か所の外に文字列で書けない
#: (``tests/engine/events/test_e_cause_three_kinds.py``)。値はハッシュにも状態のファイルにも入らない(下の試験)。
EXCLUDED = {f"{EV.__name__}.Experiment"}


def test_table_keys_are_exactly_the_classes_in_src():
    found = src_classes()
    assert len(found) == len(set(found)), "同じ名のクラスが 2 つある"
    assert EXCLUDED <= set(found), "載せないクラスの名が src に無い(一覧を直す)"
    found = [n for n in found if n not in EXCLUDED]
    missing = sorted(set(found) - set(CLASS_IDS))
    extra = sorted(set(CLASS_IDS) - set(found))
    assert not missing and not extra, (
        f"表に無いクラス {missing[:5]}・src に無い鍵 {extra[:5]}"
        "(道具 docs/bench/analysis/move-346/tools/gen_class_ids.py で作り直す)")


def test_excluded_classes_never_reach_a_hash_or_the_state_file():
    """載せないクラスは今の名を返す。持つ行(出来事の記録 E・実験の層 X)は軸 1 diag・軸 2 discardable(ハッシュにも状態の
    ファイルにも入らない)で、許可の表・値のクラスにも無い=置き場を動かしても final と状態のファイルは変わらない。"""
    assert class_id(EV.Experiment) == f"{EV.__name__}.Experiment"
    assert not EXCLUDED & {*SC.ALLOWED_CLASSES, *SH.VALUE_CLASSES, *SC.CLASS_FIELDS}
    holders = [r for r in SL.external_rows()
               if any(i.startswith("events._cz_experiments") or i.startswith("experiment.") for i in r.items)]
    assert {r.key for r in holders} == {"E", "X"}
    assert all(r.behavior == SL.DIAG and r.restore == SL.DISCARDABLE for r in holders)


# ================================================================= 2 凍結
def test_values_match_the_frozen_json():
    doc = json.loads(FROZEN.read_text(encoding="utf-8"))
    names = doc["names"]
    assert names == sorted(set(names)), "凍結の JSON は重なりなしの昇順"
    assert set(CLASS_IDS.values()) == set(names)


# ================================================================= 3 1 対 1
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
    vals = list(CLASS_IDS.values())
    assert len(vals) == len(set(vals)), "凍結の名が重なる"
    for k, v in CLASS_IDS.items():
        assert class_path(v) == k
        assert CI._PATH_OF[v] == k
    for name, t in _allowed_types().items():
        assert class_id(t) == name
        assert class_path(class_id(t)) == f"{t.__module__}.{t.__qualname__}"
    # 表に無い型は今の名をそのまま
    assert class_id(np.ndarray) == "numpy.ndarray"
    assert class_path("numpy.ndarray") == "numpy.ndarray"


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


# ================================================================= 5 動かしたふり
MOVED = (WakeCandidates, EventClass, DeferralQueue)


def _pretend_moved(monkeypatch: pytest.MonkeyPatch, *, table: bool = True,
                   classes: tuple[type, ...] = MOVED) -> dict[str, str]:
    """型の ``__module__`` を試験の中だけ別の置き場に書き換える。``table`` なら表の鍵も合わせる。旧 → 新の名。"""
    ids = dict(CI.CLASS_IDS)
    moved: dict[str, str] = {}
    for cls in classes:
        old = f"{cls.__module__}.{cls.__qualname__}"
        new_mod = "shibuya._moved_for_test." + cls.__module__.rpartition(".")[2]
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
    assert b"shibuya.engine.arbiter.WakeCandidates" in before[0]
    with monkeypatch.context() as m:
        moved = _pretend_moved(m)
        assert class_id(WakeCandidates) == "shibuya.engine.arbiter.WakeCandidates"
        assert class_path("shibuya.engine.arbiter.WakeCandidates") == moved["shibuya.engine.arbiter.WakeCandidates"]
        assert _unit_bytes() == before
    # 負の対照: 表を合わせないと名が変わる(ハッシュ・指紋が動く・状態のファイルは許可の表に無い名で書けない)
    with monkeypatch.context() as m:
        _pretend_moved(m, table=False)
        doc = _sample()
        assert SH.to_state(doc) != before[0]
        with pytest.raises(TypeError, match="直列化の書き手が無い型"):
            SC.dumps(doc)
        assert RS._canon({"x": doc["wake"]}) != before[3]
        assert PR.plain(DeferralQueue.__new__(DeferralQueue)) != before[4]


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
    with monkeypatch.context() as m:  # 負の対照: 表を合わせないと behavior-hash(final)と full-hash が動く
        _pretend_moved(m, table=False, classes=(WakeCandidates, EventClass))
        a = run_day(sim_days=2, **RUN_KW)
        got = [(c.tick, c.behavior_hash, c.full_hash) for c in a.checkpoints if c.tick < STOP]
        want = [(h[0], h[2], h[3]) for h in before[0] if h[0] < STOP]
        assert [g[0] for g in got] == [w[0] for w in want]
        assert all(g[1] != w[1] and g[2] != w[2] for g, w in zip(got, want))
    with monkeypatch.context() as m:  # 負の対照: 値のクラスは表を合わせないと直列化の書き手が無い(黙って通さない)
        _pretend_moved(m, table=False, classes=(DeferralQueue,))
        with pytest.raises(TypeError, match="直列化の書き手が無い型"):
            run_day(sim_days=2, **RUN_KW)


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
