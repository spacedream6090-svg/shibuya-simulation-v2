"""engine.systems.probe — 系ごとの全欄の差(段 B)と系ごとの指紋(草案 §2-6 の B・§2-7)。**試験のときだけ**。

系の境目ごとに全欄の digest を取り、直前の境目からの差を**いま終わった系**に帰属させる(宣言の外の書きも書いた系の
指紋に出る=草案 §2-7〔改訂 K5〕)。欄の族:

- ``soa``: SoA の全列(agents・cells・pois・知覚。台帳の軸 2 を問わない=``discardable`` も含む)。鍵 ``agents.cell``。
- ``ext``: 外の状態の全道筋(状態台帳の外の状態の行の ``items`` の全部・``state_hashes.item_digest`` の道筋の単位。
  行は割らない=草案 §0-2 の親の決め)。鍵 ``O39:conv.sessions``。
- ``stats``: 診断の積算(``RunStats`` の欄と ``RunResult`` の欄=呼数を含む。壁時計の欄は除く)。鍵 ``stats.<名>``。
- ``buffers``: 使い回すバッファ(``focus_request``)。鍵 ``buffers.<名>``。

指紋: 系ごとに ``fp[系] = blake3(fp[系] ‖ T ‖ 変わった欄と後の digest の並び)``(変わった欄が無い境目は鎖に足さない)。
2 本のランの ``entries``(T・系・変わった欄の digest)を並べて「最初に食い違った (T, 系, 欄)」を出す(``first_diff``)。
HEAD の基準は、同じ ``snapshot`` を ``sys.monitoring`` で HEAD の ``run_day`` の系の先頭の行に張って取る
(``docs/bench/analysis/wallbounce-1012/run-day-decomp/head_probe.py``)。

**checkpoint_detail と first_diff(10d)の延長にしなかった理由**: checkpoint_detail は checkpoint の時刻だけ・full-hash の
範囲(``discardable`` の列と軸 1 の外の行を落とす)なので、系の境目ごと・全欄の差には足りない。digest の取り方
(``item_digest``)は同じものを使う。

逐次ループ宣言: 系の境目の数ぶん × 欄の数(試験のときだけ・既定のランでは 1 行も通らない)。
"""

from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

import blake3 as _blake3
import numpy as np

__all__ = ["View", "Probe", "snapshot", "first_diff", "RESULT_SKIP", "STATS_NAMES"]

#: 診断の積算(``RunStats`` の欄の名=HEAD の ``run_day`` の局所の名と同じ)。
STATS_NAMES: tuple[str, ...] = (
    "layer_counts", "sleep_counts", "awake_sum", "awake_ticks", "calls_by_cond", "per_action_total",
    "leave_counts", "talk_stats", "n_undefined_total", "n_fleet_reinjected", "n_fleet_resent",
    "n_outside_calls", "geometry_hops", "geometry_jammed", "leave_closed", "peak_pending",
    "peak_intents", "peak_backlog", "prev_sessions", "prev_tape_misses", "intero_cross",
    "diag_rows", "daily_records", "day_heads", "occ_ticks",
    # 〔段 FIX・検収 §1 の 7〕HEAD との比べ(probe_compare.json)の後に足した欄(state_files は壁時計の秒を外して digest)
    "occ_counts", "occ_kind", "occ_transit", "ledger_growth", "state_files", "frozen_sources_map",
)
#: 外の状態の道筋のうち値が壁時計のもの(変わったことは記録するが、指紋には値を入れない=2 本のランで揃わない)。
NONDET_PATHS: frozenset[str] = frozenset({
    "O73:runner.phase_seconds", "O34:norm_meter.seconds", "O34:norm_meter.tick_ms_max", "O19:rel_layer.wall",
    "O19:rel_layer.init_audit",
})
#: ``RunResult`` の欄のうち指紋に入れないもの(壁時計・大きな物の参照・機械の欄)。
RESULT_SKIP: frozenset[str] = frozenset({
    "phase_seconds", "wall_seconds", "checkpoint_seconds", "process_seconds", "resume", "runner",
    "undefined_registry", "agents", "world", "schedule", "ledger", "env_fields", "relations", "group_norms",
    "checkpoint_details", "diagnostics",
})


@dataclass
class View:
    """snapshot の材料(HEAD の局所からでも箱からでも同じ形に組む)。"""

    agents: Any
    world: Any
    pstate: Any
    owners: Mapping[str, Any]
    #: 診断の積算(名は ``stats`` を避けた=外の状態の行の属性の名と衝突する)
    tally: Mapping[str, Any]
    result: Any
    buffers: Mapping[str, Any] = field(default_factory=dict)
    scratch: Mapping[str, Any] = field(default_factory=dict)


def _hx(b: bytes) -> str:
    return _blake3.blake3(b).hexdigest()[:24]


def _arr_digest(arr: Any) -> str:
    a = np.ascontiguousarray(np.asarray(arr))
    return _hx(a.view(np.uint8).reshape(-1).tobytes() if a.size else b"") + f"{a.dtype.str}{a.shape}"


def plain(v: Any, depth: int = 0, objs: bool = False, refs: frozenset[int] = frozenset()) -> Any:
    """比べるための素の値(配列は digest・辞書は鍵の repr の順・dataclass は欄・知らない物は型の名だけ)。

    ``objs=True``(段 FIX・scratch と digest できない外の道筋の代わり): 根の知らない物は中身(``__dict__``・``__slots__``)を
    たどり、入れ子の知らない物と関数は型の名と物の番号(``id``=1 本のランの中で差し替えを見る)にする(dataclass・
    配列・辞書・列は今までどおり中身)。``refs``(物の番号の集合=外の状態の持ち主・SoA)に入る入れ子の物は dataclass でも
    同一性だけ(``outcome.energy`` のような持ち主への参照の先の変化を scratch の書きと取り違えない。中身は持ち主の道筋の族で
    見る)。HEAD との比べの既定の digest は変えない。
    """
    if depth > 12:
        return "<deep>"
    if objs and depth > 0 and id(v) in refs:
        return ("ref", type(v).__qualname__, id(v))
    if v is None or isinstance(v, (bool, int, float, str, bytes)):
        return v
    if isinstance(v, np.generic):
        return v.item()
    if isinstance(v, np.ndarray):
        return ("nd", _arr_digest(v))
    if isinstance(v, Mapping):
        return sorted(((repr(k), plain(x, depth + 1, objs, refs)) for k, x in v.items()), key=lambda kv: kv[0])
    if isinstance(v, (list, tuple)):
        return [plain(x, depth + 1, objs, refs) for x in v]
    if isinstance(v, (set, frozenset)):
        return sorted((plain(x, depth + 1, objs, refs) for x in v), key=repr)
    if dataclasses.is_dataclass(v) and not isinstance(v, type):
        return (type(v).__qualname__, [(f.name, plain(getattr(v, f.name, None), depth + 1, objs, refs))
                                        for f in dataclasses.fields(v)])
    if objs:
        import functools
        import inspect

        if inspect.isroutine(v) or isinstance(v, (functools.partial, type)):
            return ("fn", getattr(v, "__qualname__", type(v).__qualname__), id(v))
        if depth > 0:
            # 入れ子の物(dataclass でない=層・世界過程・ログの物)は同一性だけ(物の番号)。中身は持ち主の道筋(外の
            # 道筋の族)で見る=``outcome.crowd`` のような参照の先の変化を scratch の書きと取り違えない
            return ("ref", type(v).__qualname__, id(v))
        if hasattr(v, "__dict__"):
            return (type(v).__qualname__, plain({k: x for k, x in vars(v).items()}, depth + 1, objs, refs))
        slots = [s for c in type(v).__mro__ for s in getattr(c, "__slots__", ())]
        if slots:
            return (type(v).__qualname__, [(s, plain(getattr(v, s, None), depth + 1, objs, refs)) for s in slots])
    return ("obj", type(v).__module__ + "." + type(v).__qualname__)


def _digest_value(v: Any, objs: bool = False, refs: frozenset[int] = frozenset()) -> str:
    return _hx(repr(plain(v, 0, objs, refs)).encode("utf-8"))


def _result_digest(res: Any) -> str:
    if res is None:
        return "-"
    vals = []
    for f in dataclasses.fields(res):
        if f.name in RESULT_SKIP:
            continue
        v = getattr(res, f.name, None)
        if f.name == "checkpoints":
            v = [(int(c.tick), c.behavior_hash, c.full_hash) for c in v]
        vals.append((f.name, plain(v)))
    return _hx(repr(vals).encode("utf-8"))


_EXT_ROWS: list[tuple[str, str]] | None = None


def _ext_rows() -> list[tuple[str, str]]:
    global _EXT_ROWS
    if _EXT_ROWS is None:
        from shibuya.engine import state_ledger as SL

        _EXT_ROWS = [(r.key, p) for r in SL.external_rows() for p in r.items]
    return _EXT_ROWS


def snapshot(view: View, *, families: Iterable[str] = ("soa", "ext", "stats", "buffers")) -> dict[str, str]:
    """全欄の digest(読むだけ・乱数を引かない・状態を書かない)。"""
    from shibuya.engine import state_hashes as SH

    fam = set(families)
    out: dict[str, str] = {}
    # 持ち主(外の状態の根)と SoA の物の番号=objs の digest で入れ子に出たら同一性だけにする(段 FIX)
    refs = frozenset(id(o) for o in (*view.owners.values(), view.agents, view.world, view.pstate) if o is not None)
    if "soa" in fam:
        regs = (("agents", view.agents.registry), ("cells", view.world.cells), ("pois", view.world.pois),
                ("perception", None if view.pstate is None else view.pstate.registry))
        for place, reg in regs:
            if reg is None:
                continue
            for name, arr in reg.arrays.items():
                out[f"{place}.{name}"] = _arr_digest(arr)
    if "ext" in fam:
        for key, path in _ext_rows():
            try:
                d, _n = SH.item_digest(view.owners, key, path)
                out[f"{key}:{path}"] = d.hex()[:24]
            except Exception as e:  # noqa: BLE001 — 状態の直列化の書き手が無い型(関数・ログの物)など
                # 〔段 FIX・検収 §1 の 8〕代わりに中身をたどる digest(関数は名と物の番号)。持ち主に属性が無い
                # (腕で立たない)ときだけ ``ERR`` のまま(値が変わらない=見えない道筋は記録の限界の表)
                try:
                    v = SH.resolve_item(view.owners, path)
                    out[f"{key}:{path}"] = "X:" + _digest_value(v, objs=True, refs=refs)
                except Exception:  # noqa: BLE001
                    out[f"{key}:{path}"] = f"ERR:{type(e).__name__}"
    if "stats" in fam:
        for nm in STATS_NAMES:
            if nm in view.tally:
                v = view.tally[nm]
                if nm == "diag_rows":
                    v = (len(v), v[-1] if v else None)
                elif nm == "state_files":
                    v = [{k: x for k, x in f.items() if k != "seconds"} for f in v]
                out[f"stats.{nm}"] = _digest_value(v)
        out["stats.result"] = _result_digest(view.result)
    if "buffers" in fam:
        for nm, v in view.buffers.items():
            out[f"buffers.{nm}"] = _digest_value(v)
    if "scratch" in fam:
        # 〔段 FIX・検収 §1 の 2〕中身(配列・dataclass・物の属性)まで digest=宣言の外の系がその場で書き換えると変わる
        for nm, v in view.scratch.items():
            out[f"scratch.{nm}"] = _digest_value(v, objs=True, refs=refs)
    return out


@dataclass
class Probe:
    """系の境目ごとに snapshot を取り、差を直前の系へ帰属させる(段 B・指紋)。

    ``check``: ``(系名, 欄の鍵) → 宣言の中か`` を返す関数(``None`` なら宣言との突き合わせをしない=HEAD の基準取り)。
    ``ticks``: snapshot を取る T の集合(``None``=全部)。ランの終わりの系(T が無い)はいつも取る。
    """

    check: Callable[[str, str], bool] | None = None
    ticks: frozenset[int] | None = None
    families: tuple[str, ...] = ("soa", "ext", "stats", "buffers")
    entries: list[tuple[int, str, str, tuple[str, ...]]] = field(default_factory=list)
    fp: dict[str, str] = field(default_factory=dict)
    violations: list[tuple[int, str, str]] = field(default_factory=list)
    n_snap: int = 0
    _last: tuple[int, str, dict[str, str]] | None = None

    def wants(self, T: int | None) -> bool:
        return T is None or self.ticks is None or int(T) in self.ticks

    def point(self, name: str, T: int | None, view: View) -> None:
        """系 ``name`` の始まり(T はその刻み・ランの終わりは None)。直前の境目からの差を直前の系に帰属させる。"""
        if not self.wants(T):
            self._last = None
            return
        snap = snapshot(view, families=self.families)
        self.n_snap += 1
        if self._last is not None:
            t_prev, prev, before = self._last
            self._attribute(t_prev, prev, before, snap)
        self._last = (-1 if T is None else int(T), name, snap)

    def end(self, view: View) -> None:
        """ランの終わり(最後の系の差を閉じる)。"""
        self.point("END", None, view)
        self._last = None

    def _attribute(self, T: int, name: str, before: Mapping[str, str], after: Mapping[str, str]) -> None:
        # 壁時計の道筋は変わったかどうか自体が揃わない(最大値の更新など)ので、指紋と記録の鍵から外す
        changed = tuple(sorted(k for k, v in after.items() if before.get(k) != v and k not in NONDET_PATHS))
        if not changed:
            return
        body = repr([(k, after[k]) for k in changed]).encode("utf-8")
        h = _blake3.blake3()
        h.update(bytes.fromhex(self.fp.get(name, "00" * 16)))
        h.update(str(T).encode("ascii") + b"\x1f" + body)
        self.fp[name] = h.hexdigest()[:32]
        self.entries.append((T, name, _hx(body), changed))
        if self.check is not None:
            for k in changed:
                if not self.check(name, k):
                    self.violations.append((T, name, k))

    def to_json(self) -> dict[str, Any]:
        return {"fp": dict(sorted(self.fp.items())), "n_snapshots": self.n_snap,
                "entries": [[t, s, d, list(c)] for t, s, d, c in self.entries],
                "violations": [list(v) for v in self.violations]}


def first_diff(a: Mapping[str, Any], b: Mapping[str, Any]) -> dict[str, Any] | None:
    """2 本の ``Probe.to_json()`` の entries を並べて、最初に食い違った (T, 系, 欄) を返す(同じなら ``None``)。"""
    ea, eb = a["entries"], b["entries"]
    for i in range(max(len(ea), len(eb))):
        x = ea[i] if i < len(ea) else None
        y = eb[i] if i < len(eb) else None
        if x is None or y is None or x[0] != y[0] or x[1] != y[1] or x[2] != y[2]:
            out: dict[str, Any] = {"index": i, "a": x[:2] if x else None, "b": y[:2] if y else None}
            if x is not None and y is not None and x[:2] == y[:2]:
                out["keys_only_a"] = sorted(set(x[3]) - set(y[3]))
                out["keys_only_b"] = sorted(set(y[3]) - set(x[3]))
                out["keys_both"] = sorted(set(x[3]) & set(y[3]))
            return out
    return None


def save(probe: Probe, path: str | Path, **meta: Any) -> None:
    doc = {"format": "shibuya.engine.systems.probe/1", **meta, **probe.to_json()}
    Path(path).write_text(json.dumps(doc, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


#: 試験のときだけ置く(``None``=既定=測らない)。進行役と ``run_day`` の境目がこれを見る。
ACTIVE: Probe | None = None


def view_of(box: Any) -> View:
    """箱から snapshot の材料を組む(HEAD の局所から組む ``probe_run._head_view`` と同じ形)。"""
    from shibuya.engine.systems import state_io as SIO

    return View(agents=box.soa.agents, world=box.soa.world, pstate=SIO.pst_now(box), owners=SIO.hash_owners(box),
                tally=box.tally_view(), result=box.runstats.result,
                buffers={"focus_request": box.buffers.focus_request},
                scratch=box.scratch.as_dict())  # 段 FIX: families に "scratch" があるときだけ digest する


def at(name: str, T: int | None, box: Any) -> None:
    """系 ``name`` の始まりの境目(試験のときだけ snapshot を取る・既定のランでは何もしない)。"""
    pr = ACTIVE
    if pr is None:
        return
    if name == "END":
        pr.end(view_of(box))
    elif pr.wants(T):
        pr.point(name, T, view_of(box))
    else:
        pr._last = None
