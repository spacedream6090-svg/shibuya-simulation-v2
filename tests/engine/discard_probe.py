"""10f(K24 (a)): 軸 2 の実行時の検査「捨てて同じか」の道具(試験だけが使う・src は変えない)。

通しのランの途中の tick T の頭(``resolve.advance_body`` の手前)で、状態台帳の軸 2 が ``discardable`` の外の状態の
属性を、**ランの最初の tick の頭の値**(持ち主を作り、配線と初期化を終えた後・まだ 1 tick も回していない値)に戻して
続ける。T から後の checkpoint
(final=``combined``・behavior-hash・full-hash)・tick ごとの呼数・診断の行・日の締めが通しと同じなら、捨ててよいという
判定が今のランでは当たっている。違えば「discardable の判定が誤り」(10d で再開の試験が見つけた 14 項目の形)。

再開の試験(10d)との違い: 保存と読み込みをしない(戻す値は同じプロセスの中の写し)。required・derivable・unknown の
行には触らない(再開の試験が見る)。SoA の discardable の列は全部が死蔵(書き手も読み手も無い=10b の AST が見る)
なので触らない。

実行役の自前の構成(**未リサーチ(expedient)**):

- 「新しいインスタンスの値」は、ランの最初の tick の頭の値で近似する。再開のランの新しいインスタンスは、作った後の
  配線(``bind``・``enable_*`` など)を通るが日の頭の初期化(``initialize`` など)を通らない。最初の tick の頭の値は
  初期化の分の計数を含む(差は計数だけの見込み=推測)。``__init__`` の直後の値では、配線で鍵を張る辞書(会話の
  ``origin_counts``)が空に戻ってランが止まった(試した結果)ので使わない。その時点で無い属性は戻せない
  (``absent_after_init`` に出す)。
- 値の写し: 配列は ``copy``、数・文字列と、それだけを入れた容器は ``deepcopy``、それ以外(関数・他の
  オブジェクトへの参照)はそのまま(``kept_reference`` に出す)。
- 持ち主のオブジェクトは、checkpoint の full-hash に渡る ``owners`` を写して引く(``checkpoint_every=1`` が要る)。
"""

from __future__ import annotations

import collections
import copy
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

import numpy as np

from shibuya.engine import resolve as R
from shibuya.engine import run as RUN
from shibuya.engine import state_ledger as SL
from shibuya.engine.state_hashes import _ABSENT, resolve_item


def discardable_paths() -> tuple[str, ...]:
    """台帳の外の状態の行のうち軸 2 が ``discardable`` の属性の道筋(``run_day`` の局所の行と持ち主の丸ごとを除く)。"""
    out: list[str] = []
    for r in SL.external_rows():
        if r.restore != SL.DISCARDABLE:
            continue
        for it in r.items:
            if it in SL.OWNER_CLASSES:
                continue
            owner = it.rsplit(".", 1)[0]
            if owner in SL.OWNER_CLASSES:
                out.append(it)
    return tuple(out)


def _plain(v: Any, depth: int = 0) -> bool:
    if depth > 8:
        return False
    if v is None or isinstance(v, (bool, int, float, str, np.generic, np.ndarray)):
        return True
    if isinstance(v, (list, tuple, set, frozenset, collections.deque)):
        return all(_plain(x, depth + 1) for x in v)
    if isinstance(v, dict):
        return all(_plain(k, depth + 1) and _plain(x, depth + 1) for k, x in v.items())
    return False


def _fresh_copy(v: Any) -> tuple[Any, bool]:
    """(写し, 写せたか)。写せない値(関数・参照)はそのまま返す。"""
    if isinstance(v, np.ndarray):
        return v.copy(), True
    if _plain(v):
        return copy.deepcopy(v), True
    return v, False


@dataclass
class DiscardReport:
    T: int
    paths: tuple[str, ...]
    reset: list[str] = field(default_factory=list)
    absent_owner: list[str] = field(default_factory=list)
    absent_after_init: list[str] = field(default_factory=list)
    kept_reference: list[str] = field(default_factory=list)
    no_snapshot: list[str] = field(default_factory=list)
    fired: bool = False


def _owner_class_objs() -> dict[str, list[type]]:
    import importlib

    out: dict[str, list[type]] = {}
    for owner, (rel, cls) in SL.OWNER_CLASSES.items():
        pairs = [(rel, cls)] + list(SL.OWNER_ALT_CLASSES.get(owner, ()))
        for rel2, cls2 in pairs:
            mod = importlib.import_module("shibuya." + rel2[:-3].replace("/", "."))
            out.setdefault(owner, []).append(getattr(mod, cls2))
    return out


def install(monkeypatch: Any, T: int, paths: Iterable[str] | None = None) -> DiscardReport:
    """``monkeypatch`` で計器を入れる(戻すのは ``monkeypatch`` の後始末)。返す報告はランの後に読む。"""
    paths_t = tuple(discardable_paths() if paths is None else paths)
    rep = DiscardReport(T=int(T), paths=paths_t)
    by_owner: dict[str, list[str]] = collections.defaultdict(list)
    for p in paths_t:
        owner, attr = p.rsplit(".", 1)
        by_owner[owner].append(attr)
    classes = _owner_class_objs()
    attrs_of_class: dict[type, set[str]] = collections.defaultdict(set)
    for owner, attrs in by_owner.items():
        for c in classes.get(owner, []):
            attrs_of_class[c] |= set(attrs)
    snaps: dict[int, dict[str, tuple[Any, bool]]] = {}
    made: list[Any] = []   # 作ったインスタンス(id の使い回しを防ぐため生かす)

    def wrap(cls: type) -> Callable[..., None]:
        orig = cls.__init__

        def init(self: Any, *a: Any, **k: Any) -> None:
            orig(self, *a, **k)
            made.append(self)

        return init

    def attrs_of_class_of(obj: Any) -> set[str]:
        out: set[str] = set()
        for c in type(obj).__mro__:
            out |= attrs_of_class.get(c, set())
        return out

    def snapshot_all() -> None:
        for obj in made:
            snaps[id(obj)] = {n: _fresh_copy(getattr(obj, n)) for n in attrs_of_class_of(obj) if hasattr(obj, n)}

    for c in attrs_of_class:
        monkeypatch.setattr(c, "__init__", wrap(c))

    owners_box: dict[str, Any] = {}
    orig_full = RUN.full_state_hash

    def full_spy(agents, world, pstate, ph, sh, owners, *a, **k):  # noqa: ANN001
        owners_box["owners"] = owners
        return orig_full(agents, world, pstate, ph, sh, owners, *a, **k)

    monkeypatch.setattr(RUN, "full_state_hash", full_spy)
    orig_ab = R.advance_body

    started: list[bool] = []

    def advance_body(agents, tick, *a, **k):  # noqa: ANN001
        if not started:  # ランの最初の tick の頭: 戻す値を写す
            started.append(True)
            snapshot_all()
        if int(tick) == rep.T and not rep.fired:
            rep.fired = True
            owners = owners_box.get("owners")
            if owners is None:
                raise RuntimeError("discard_probe: checkpoint の owners が無い(checkpoint_every=1 で回す)")
            for p in paths_t:
                head, attr = p.rsplit(".", 1)
                obj = resolve_item(owners, head) if "." in head else owners.get(head)
                if obj is None or obj is _ABSENT:
                    rep.absent_owner.append(p)
                    continue
                snap = snaps.get(id(obj))
                if snap is None:
                    rep.no_snapshot.append(p)
                    continue
                if attr not in snap:
                    rep.absent_after_init.append(p)
                    continue
                val, ok = snap[attr]
                if not ok:
                    rep.kept_reference.append(p)
                new, _ = _fresh_copy(val)
                object.__setattr__(obj, attr, new)
                rep.reset.append(p)
        return orig_ab(agents, tick, *a, **k)

    monkeypatch.setattr(R, "advance_body", advance_body)
    return rep


# ---------------------------------------------------------------- 比べ方
def hashes(res: Any, from_T: int) -> list[tuple[int, str, str, str]]:
    return [(c.tick, c.combined, c.behavior_hash, c.full_hash) for c in res.checkpoints if c.tick >= from_T]


def calls(res: Any, from_T: int) -> dict[int, int]:
    t = res.column("tick").astype(np.int64)
    c = res.column("calls").astype(np.int64)
    return {int(a): int(b) for a, b in zip(t.tolist(), c.tolist()) if int(a) >= from_T}


def diag(res: Any, from_T: int) -> dict[int, tuple[int, ...]]:
    return {int(r[0]): tuple(int(x) for x in r) for r in res.diagnostics.tolist() if int(r[0]) >= from_T}


def daily(res: Any, from_T: int) -> list[tuple[Any, ...]]:
    import json

    return [(r["day"], r.get("state_hashes_end_of_day", {}).get("behavior_hash"),
             r.get("state_hashes_end_of_day", {}).get("full_hash"),
             json.dumps(r.get("census_row", {}), sort_keys=True, default=str), json.dumps(r["bodies"]))
            for r in res.daily if int(r["end_T"]) > from_T]


def differences(straight: Any, probed: Any, T: int) -> dict[str, Any]:
    """T から後の食い違い(空なら同じ)。最初に食い違った checkpoint の tick と、どのハッシュかを出す。"""
    out: dict[str, Any] = {}
    a, b = hashes(straight, T), hashes(probed, T)
    if [x[0] for x in a] != [x[0] for x in b]:
        out["checkpoint_ticks"] = "違う"
    bad = [(x[0], x[1] != y[1], x[2] != y[2], x[3] != y[3]) for x, y in zip(a, b) if x != y]
    if bad:
        out["first_checkpoint"] = {"tick": bad[0][0], "final": bad[0][1], "behavior": bad[0][2], "full": bad[0][3]}
        out["n_checkpoints"] = len(bad)
    if calls(straight, T) != calls(probed, T):
        out["calls"] = True
    if diag(straight, T) != diag(probed, T):
        out["diag"] = sorted(t for t, r in diag(straight, T).items() if diag(probed, T).get(t) != r)[:5]
    if daily(straight, T) != daily(probed, T):
        out["daily"] = True
    if int(straight.llm_calls) != int(probed.llm_calls):
        out["llm_calls"] = (int(straight.llm_calls), int(probed.llm_calls))
    return out
