# -*- coding: utf-8 -*-
"""段を選んで計画を作り(書き換えた後の木を手元で作る)、守りを通し、報告と差分を出す。``--apply`` のときだけ木へ書く。

計画の手順
    1. 木を読む(``src/shibuya`` の全部と ``tests``・``tools`` の ``.py``)。道具そのもの(``tools/pkgmove/``)と道具の試験は
       書き換えない。
    2. 選んだ段の行(``move``・``empty``・``delete``)を、木の今の形で 3 つに分ける: これから当てる行・もう当たっている行
       (古い道が無く新しい道がある=2 回目)・保留の行(当てない=断った行として報告)。
    3. import の文(全部の Python)・許可の一覧の記号の中の道の文字列・固定の表の鍵を書き換える。
    4. ファイルを新しい道へ移す。頭の行は新しい頭を空にし、古い頭は古いディレクトリにファイルが残るなら空にして残し、残らなければ
       消す。新しいディレクトリで頭の無いものには空の頭を足す。
    5. 守り(:mod:`pkgmove.guard`)。1 つでも当たれば :class:`Stopped`(書かない)。
    6. ``--apply`` のとき(:func:`apply`): 書き、``__pycache__`` のほかに何も無い古いディレクトリを消す(検収 L-a)。

頭から除いた再輸出の名は、その頭の ``__all__`` からも除く(許可の一覧の (e)=親の裁定 review3 の 2)。
"""
from __future__ import annotations

import ast
import difflib
import json
import os
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from pkgmove import allow as AL
from pkgmove import classids as CI
from pkgmove import guard as G
from pkgmove import imports as IM
from pkgmove import ledgerpaths as LPT
from pkgmove import strings as ST
from pkgmove.model import (SRC_PREFIX, Ctx, Edit, Index, Tree, apply_edits, area_of, is_self, mod_of, parse,
                           symbols_of)
from pkgmove.table import STAGES, MapDoc, Row

LEDGER_REL = "docs/design/bridging-ledger.json"

#: 計画 §7-4 の段 4 の見積もり(直す import の文 src / build / tests / tools と、再輸出の頭を通るもの)。
PLAN_ESTIMATE = {"statements": {"src": 855, "build": 38, "tests": 1378, "tools": 52},
                 "files": {"src": 179, "build": 30, "tests": 349, "tools": 28},
                 "via_head": {"src": 10, "build": 14, "tests": 40, "tools": 3}}


class Refused(Exception):
    """断った(保留の行の名指し・道具の使い方)。終了コード 2。"""


class Stopped(Exception):
    """守りが止めた(書かない)。終了コード 1。"""

    def __init__(self, errors: list[str]) -> None:
        super().__init__("; ".join(errors[:5]))
        self.errors = errors


@dataclass
class Plan:
    stages: tuple[str, ...]
    before: Tree
    after: Tree
    file_moves: dict[str, str] = field(default_factory=dict)
    rows_applied: list[Row] = field(default_factory=list)
    rows_already: list[Row] = field(default_factory=list)
    refused: list[Row] = field(default_factory=list)
    created_heads: list[str] = field(default_factory=list)
    emptied_heads: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)
    changed: dict[str, list[Edit]] = field(default_factory=dict)
    import_stats: dict[str, IM.ImportStats] = field(default_factory=dict)
    import_files: Counter = field(default_factory=Counter)
    str_stats: ST.StrStats = field(default_factory=ST.StrStats)
    class_keys: int = 0
    class_resorted: bool = False
    untouched: list[dict] = field(default_factory=list)
    untouched_broad: dict[str, int] = field(default_factory=dict)
    ledger: dict = field(default_factory=dict)
    guards: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    #: 頭の再輸出を除いた名(頭の道筋 → 名)。
    dropped_reexports: dict[str, list[str]] = field(default_factory=dict)
    #: 〔親の裁定 review3 の 2〕頭の ``__all__`` から除いた名(頭の道筋 → 名)=許可の一覧の (e)。
    dropped_all: dict[str, list[str]] = field(default_factory=dict)
    #: (d) 台帳の道の対応の表に足した行の数。
    ledger_paths_added: int = 0
    ledger_text: str | None = None


def locate(tree: Tree, mapdoc: MapDoc, rel: str) -> str:
    """今の道(``src/shibuya`` からの相対)のファイルの、木の中の道筋(移した後なら新しい道)。"""
    p = SRC_PREFIX + rel
    if p in tree.files:
        return p
    row = mapdoc.by_old().get(rel)
    if row is not None and row.kind == "move" and (SRC_PREFIX + row.new) in tree.files:
        return SRC_PREFIX + row.new
    return p


def select_rows(mapdoc: MapDoc, stages: Iterable[str], only: Iterable[str] = ()) -> tuple[list[Row], list[Row]]:
    """(当てる候補の行, 保留で断る行)。``only`` で保留の行を名指せば :class:`Refused`。"""
    st = tuple(stages)
    bad = [s for s in st if s not in STAGES]
    if bad:
        raise Refused(f"段の名が違う: {bad}(段は {', '.join(STAGES)} か all)")
    only = tuple(only)
    by = mapdoc.by_old()
    for o in only:
        r = by.get(o)
        if r is None:
            raise Refused(f"表に無い道筋: {o}")
        if r.held:
            raise Refused(f"保留の行は動かさない: {o}({r.held})")
        if r.kind not in ("move", "empty", "delete"):
            raise Refused(f"動かす行でない: {o}(kind={r.kind})")
    rows = [r for r in mapdoc.rows if r.kind in ("move", "empty", "delete")
            and ((r.old in only) if only else (r.stage in st))]
    return [r for r in rows if not r.held], [r for r in rows if r.held]


def _row_state(tree: Tree, r: Row) -> str:
    """``apply``(当てる)・``already``(当たっている)。食い違いは :class:`Refused`。"""
    old = SRC_PREFIX + r.old
    new = SRC_PREFIX + r.new if r.new else ""
    has_old = tree.exists(old)
    has_new = bool(new) and tree.exists(new)
    if r.kind == "move" and not r.is_head:
        if has_old and not has_new:
            return "apply"
        if has_new and not has_old:
            return "already"
        raise Refused(f"行 {r.num} {r.old}: 古い道と新しい道が{'どちらもある' if has_old else 'どちらも無い'}")
    if r.kind == "move":  # 頭
        if not r.empty_head:
            raise Refused(f"行 {r.num} {r.old}: 頭を移す行に「(空にする)」が無い(扱いが決まっていない)")
        if has_new and tree.files.get(new) != "" :
            raise Refused(f"行 {r.num} {r.new}: 新しい頭が空でない")
        if not has_old:
            return "already" if has_new else _raise(f"行 {r.num} {r.old}: 古い頭も新しい頭も無い")
        return "already" if (tree.files[old] == "" and has_new) else "apply"
    if r.kind == "empty":
        if not has_old:
            raise Refused(f"行 {r.num} {r.old}: 頭が無い")
        return "already" if tree.files[old] == "" else "apply"
    # delete
    if not has_old:
        return "already"
    return "already" if tree.files[old] == "" else "apply"


def _raise(msg: str) -> str:
    raise Refused(msg)


def make_ctx(tree: Tree, rows: list[Row], frozen: G.Frozen | None) -> tuple[Ctx, dict[str, str]]:
    """書き換えの材料と、移すファイルの道(``src/shibuya`` からの相対の古い → 新しい)。"""
    modmap: dict[str, str] = {}
    relmap: dict[str, str] = {}
    heads: set[str] = set()
    for r in rows:
        if r.kind == "move":
            relmap[r.old] = r.new
            if r.old.endswith(".py"):
                modmap[mod_of(r.old)] = mod_of(r.new)
        if r.is_head and (r.kind in ("empty", "delete") or (r.kind == "move" and r.empty_head)):
            heads.add(mod_of(r.old))
    toks = frozenset(frozen.id_tokens()) if frozen is not None else frozenset()
    return Ctx(index=Index(tree), modmap=modmap, heads_changed=heads, frozen_tokens=toks), relmap


def make_plan(tree: Tree, mapdoc: MapDoc, stages: Iterable[str], *, only: Iterable[str] = (),
              allow_tt: list[AL.Site] | None = None, frozen: G.Frozen | None = None, keyfn=None,
              extra_sites: Iterable[AL.Site] = (), ledger_text: str | None = None) -> Plan:
    """計画(書き換えた後の木)を作り、守りを通す(当たれば :class:`Stopped`)。``extra_sites``・``keyfn`` は試験の口。"""
    stages = tuple(stages)
    cand, refused = select_rows(mapdoc, stages, only)
    plan = Plan(stages=stages, before=tree, after=tree.copy(), refused=refused)
    rows: list[Row] = []
    for r in cand:
        (rows if _row_state(tree, r) == "apply" else plan.rows_already).append(r)
    plan.rows_applied = rows
    dests = Counter(r.new for r in rows if r.kind == "move")
    dup = sorted(d for d, n in dests.items() if n > 1)
    if dup:
        raise Refused(f"対応表の行き先が重なる: {dup}")
    ctx, relmap = make_ctx(tree, rows, frozen)
    rules = ST.PathRules(relmap=relmap)
    head_paths = {SRC_PREFIX + r.old for r in rows if r.is_head}
    # 許可の一覧(木の今の道筋で)
    sites = [*AL.src_sites(lambda f: locate(tree, mapdoc, f)), *(allow_tt or []), *extra_sites]
    rule_of: dict[str, dict[str, str]] = {}
    for s in sites:
        rule_of.setdefault(s.path, {})[s.symbol] = s.rule
    class_path = locate(tree, mapdoc, AL.CLASS_IDS_TABLE[0])
    lp_path = locate(tree, mapdoc, AL.LEDGER_PATHS_TABLE[0])
    allowed = {(s.path, s.symbol) for s in sites} | {(class_path, AL.CLASS_IDS_TABLE[1]),
                                                     (lp_path, AL.LEDGER_PATHS_TABLE[1])}
    lp_moves = {SRC_PREFIX + r.old: SRC_PREFIX + r.new for r in rows
                if r.kind == "move" and not r.is_head and r.old.endswith(".py")}
    # 1) 書き換え
    for p in sorted(tree.files):
        if is_self(p) or p in head_paths:
            continue
        text = tree.files[p]
        try:
            t = parse(text)
        except SyntaxError as e:
            plan.warnings.append(f"{p}: 構文の誤りで読めない({e.msg})=触らない")
            continue
        syms = symbols_of(text)
        area = area_of(p)
        stt = plan.import_stats.setdefault(area, IM.ImportStats())
        n0 = stt.statements
        edits = IM.rewrite_file(ctx, p, text, t, syms, stt)
        hd, dropped, hw = IM.head_drops(ctx, p, text, t)
        if hd:
            ae, all_removed, aw = IM.all_drops(p, text, t, dropped)
            hd = hd + ae
            hw = hw + aw
            spans = [(e.start, e.end) for e in hd]
            edits = [e for e in edits if not any(a <= e.start < b for a, b in spans)] + hd
            plan.dropped_reexports[p] = dropped
            if all_removed:
                plan.dropped_all[p] = all_removed
        plan.warnings += hw
        if stt.statements > n0:
            plan.import_files[area] += 1
        if p in rule_of:
            edits += ST.rewrite_file_strings(ctx, rules, p, text, t, syms, rule_of[p], plan.str_stats)
        new = apply_edits(text, edits) if edits else text
        if p == class_path and ctx.modmap:
            if frozen is None:
                raise Stopped(["固定の表の鍵を書き換えるには凍結の JSON が要る"])
            try:
                new2, cres = CI.rewrite(new, ctx.modmap, frozen.class_qual, keyfn=keyfn)
            except CI.ClassIdError as e:
                raise Stopped([f"固定の表の鍵の守り: {e}"]) from e
            plan.class_keys = cres.rewritten
            plan.class_resorted = cres.resorted
            if new2 != new:
                edits += [Edit(0, 0, "", "class_key", "CLASS_IDS", f"鍵 {cres.rewritten}")]
            new = new2
        if p == lp_path and lp_moves:
            try:
                new3, nadd = LPT.rewrite(new, lp_moves)
            except LPT.LedgerPathsError as e:
                raise Stopped([f"台帳の道の対応の表: {e}"]) from e
            plan.ledger_paths_added = nadd
            if new3 != new:
                edits += [Edit(0, 0, "", "ledger_path", "LEDGER_PATHS", f"行 {nadd}")]
            new = new3
        if new != text:
            plan.after.files[p] = new
            plan.changed[p] = edits
    for area, stt in plan.import_stats.items():
        plan.warnings += stt.warnings
    # 2) 移す・頭
    moved: dict[str, str] = {}
    for r in rows:
        if r.kind != "move":
            continue
        o, n = SRC_PREFIX + r.old, SRC_PREFIX + r.new
        if r.is_head:
            plan.after.files[n] = ""
            continue
        if o in plan.after.files:
            plan.after.files[n] = plan.after.files.pop(o)
        else:
            plan.after.blobs[n] = plan.after.blobs.pop(o)
        moved[o] = n
    plan.file_moves = dict(moved)
    remaining = {*plan.after.files, *plan.after.blobs}
    for r in rows:
        if not r.is_head:
            continue
        o = SRC_PREFIX + r.old
        d = o.rsplit("/", 1)[0] + "/"
        others = [x for x in remaining if x.startswith(d) and x != o]
        if r.kind == "move":
            plan.created_heads.append(SRC_PREFIX + r.new)
        if r.kind == "empty" or others:
            plan.after.files[o] = ""
            plan.emptied_heads.append(o)
        else:
            plan.after.files.pop(o, None)
            plan.deleted.append(o)
    # 前の段で空にして残した古い頭: この段で古いディレクトリの最後のファイルが出たら消す(段を順に当てても、まとめて当てても
    # 同じ木になるように)
    by_old = mapdoc.by_old()
    changed_heads = {SRC_PREFIX + r.old for r in rows if r.is_head}
    for d in sorted({o.rsplit("/", 1)[0] + "/" for o in moved}, key=len, reverse=True):
        h = d + "__init__.py"
        row = by_old.get(h[len(SRC_PREFIX):])
        if h in changed_heads or row is None or row.kind not in ("move", "delete") or plan.after.files.get(h) != "":
            continue
        if any(x.startswith(d) and x != h for x in [*plan.after.files, *plan.after.blobs]):
            continue
        plan.after.files.pop(h)
        plan.deleted.append(h)
    for n in list(moved.values()) + list(plan.created_heads):
        parts = n[len(SRC_PREFIX):].split("/")[:-1]
        for i in range(1, len(parts) + 1):
            h = SRC_PREFIX + "/".join(parts[:i]) + "/__init__.py"
            if h not in plan.after.files:
                plan.after.files[h] = ""
                plan.created_heads.append(h)
    plan.created_heads = sorted(set(plan.created_heads))
    # 3) 報告の材料
    _untouched(plan, ctx, rules, tree, allowed)
    plan.ledger = ledger_rows(ledger_text, relmap)
    # 4) 守り
    plan.ledger_text = ledger_text
    if frozen is not None:
        allowed_all = allowed | {(h, "__all__") for h in plan.dropped_all}  # (e) 頭の __all__(除いた名だけ=守りで確かめる)
        _guards(plan, mapdoc, frozen, allowed_all, class_path, head_paths | set(plan.deleted), lp_path)
    return plan


def _untouched(plan: Plan, ctx: Ctx, rules: ST.PathRules, tree: Tree, allowed: set[tuple[str, str]]) -> None:
    broad: Counter = Counter()
    for p in sorted(tree.files):
        if is_self(p):
            continue
        t = parse(tree.files[p])
        syms = symbols_of(tree.files[p])
        skip = {s for (f, s) in allowed if f == p}
        rows, n = ST.untouched_in_file(ctx, rules, p, tree.files[p], t, syms, skip)
        plan.untouched += rows
        broad[area_of(p)] += n
    plan.untouched_broad = dict(broad)


def ledger_rows(text: str | None, relmap: dict[str, str]) -> dict:
    """つなぎの台帳の ``declared_in``(``src/shibuya/…``)のうち、移すファイルを指す行(書き換えない=報告だけ)。"""
    if text is None:
        return {}
    doc = json.loads(text)
    rows = doc.get("bridges", [])
    with_src = [r for r in rows if str(r.get("declared_in", "")).startswith(SRC_PREFIX)]
    hit = []
    for r in with_src:
        rel = str(r["declared_in"])[len(SRC_PREFIX):].split("#", 1)[0]
        if rel in relmap:
            hit.append({"id": r.get("id"), "declared_in": r["declared_in"], "status": r.get("status"),
                        "new": SRC_PREFIX + relmap[rel] + "#" + str(r["declared_in"]).split("#", 1)[1]
                        if "#" in str(r["declared_in"]) else SRC_PREFIX + relmap[rel]})
    return {"rows_total": len(rows), "rows_src": len(with_src), "rows_moving": len(hit),
            "rows_moving_active": sum(1 for h in hit if h["status"] == "active"), "moving": hit}


def _guards(plan: Plan, mapdoc: MapDoc, frozen: G.Frozen, allowed_before: set[tuple[str, str]], class_path: str,
            head_paths: set[str], lp_path: str = "") -> None:
    errs: list[str] = []
    before, after = plan.before, plan.after
    pre = G.check_names(before, frozen) + G.check_class_ids(before, frozen, class_path)
    if pre:
        raise Stopped(["移す前の木が凍結と既に違う(凍結の JSON か木を確かめる): " + "; ".join(pre)])
    pre_all = G.check_head_all(before)
    if pre_all:
        raise Stopped(["移す前の木の頭の __all__ に結ばれない名がある(前の道具で当てた木か): " + "; ".join(pre_all)])
    errs += G.check_names(after, frozen)
    plan.guards["names_frozen"] = "同じ" if not errs else "違う"
    class_after = plan.file_moves.get(class_path, class_path)
    e2 = G.check_class_ids(after, frozen, class_after)
    plan.guards["class_ids"] = "同じ" if not e2 else "違う"
    errs += e2
    kinds = frozen.shaped_kinds()
    paths = {r.old for r in plan.rows_applied if r.kind == "move"} | {r.new for r in plan.rows_applied if r.kind == "move"}
    skip_values = paths | {SRC_PREFIX + x for x in paths}
    cb = G.shaped_counts(before, kinds, skip_values, class_path)
    ca = G.shaped_counts(after, kinds, skip_values, class_after)
    d3 = {k: (cb[k], ca[k]) for k in kinds if cb[k] != ca[k]}
    plan.guards["shaped_74"] = f"同じ({len(kinds)} 種・前の出てくる数の和 {sum(cb.values())})" if not d3 else f"違う {d3}"
    if d3:
        errs.append(f"道の形の名(74 種)の出てくる数が変わった: {d3}")
    skip_files = set(head_paths) | {p for p in before.files if is_self(p)}
    e4 = G.check_outside(before, after, plan.file_moves, allowed_before, skip_files, frozen.id_tokens(),
                         {(class_path, AL.CLASS_IDS_TABLE[1]), (lp_path, AL.LEDGER_PATHS_TABLE[1])})
    lp_after = plan.file_moves.get(lp_path, lp_path)
    if lp_after in after.files:
        e5 = LPT.check(LPT.table_of(after.files[lp_after]), lambda q: q in after.files or q in after.blobs,
                       plan.ledger_text)
        plan.guards["ledger_paths"] = "同じ(台帳の道は全部、表を通して今のファイルに届く)" if not e5 else f"違う {len(e5)}"
        errs += e5
    plan.guards["outside_allowlist"] = "同じ" if not e4 else f"違う {len(e4)}"
    e6 = G.check_bound_names(before, after, plan.file_moves, skip_files, plan.dropped_reexports)
    plan.guards["import_names"] = "同じ(import の文が結ぶ名)" if not e6 else f"違う {len(e6)}"
    errs += e6
    errs += e4
    # (e) 頭の __all__: 空にしない頭の名は全部結ばれている・除いた頭では「前の __all__ から除いた名を抜いたもの」と同じ
    e7 = G.check_head_all(after)
    for h, names in plan.dropped_all.items():
        q = plan.file_moves.get(h, h)
        b_all = G.head_all_names(before.files[h]) or []
        a_all = G.head_all_names(after.files.get(q, "")) or []
        if [x for x in b_all if x not in set(names)] != a_all or not set(names) <= set(plan.dropped_reexports.get(h, [])):
            e7.append(f"頭の __all__ が除いた再輸出の名のほかで変わった: {h}")
    n_all = sum(len(v) for v in plan.dropped_all.values())
    plan.guards["head_all"] = f"同じ(頭の __all__ は結ばれた名だけ・除いた名 {n_all})" if not e7 else f"違う {len(e7)}"
    errs += e7
    for h in head_paths:
        try:
            t = parse(before.files[h])
        except SyntaxError:
            continue
        defs = [n for n in t.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
        if defs:
            errs.append(f"空にする頭に定義がある: {h} {[d.name for d in defs][:5]}")
        # 〔検収 L-f〕import・docstring・__all__ のほかの文(代入・if・try ほか)も止める(空にすると消える)
        others = [n for n in t.body if not isinstance(n, (ast.Import, ast.ImportFrom, ast.FunctionDef,
                                                          ast.AsyncFunctionDef, ast.ClassDef))
                  and not _is_docstring(n) and not _is_all_assign(n)]
        if others:
            errs.append(f"空にする頭に import・docstring・__all__ のほかの文がある: {h} "
                        f"{[f'{type(n).__name__}@{n.lineno}' for n in others][:5]}")
    if errs:
        raise Stopped(errs)


def _is_docstring(n: ast.stmt) -> bool:
    return isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str)


def _is_all_assign(n: ast.stmt) -> bool:
    tgts = n.targets if isinstance(n, ast.Assign) else [n.target] if isinstance(n, (ast.AugAssign, ast.AnnAssign)) else []
    return bool(tgts) and all(isinstance(x, ast.Name) and x.id == "__all__" for x in tgts)


# ------------------------------------------------------------------ 報告・差分・書く
def report(plan: Plan) -> dict:
    st = {a: s.statements for a, s in plan.import_stats.items()}
    vh = {a: s.via_head for a, s in plan.import_stats.items()}
    sp = {a: s.split for a, s in plan.import_stats.items()}
    vp = {a: s.via_package for a, s in plan.import_stats.items()}
    untouched_by: Counter = Counter((u["file"].split("/")[0] if not u["file"].startswith(SRC_PREFIX) else area_of(u["file"]), u["kind"]) for u in plan.untouched)
    return {
        "stages": list(plan.stages),
        "rows_applied": len(plan.rows_applied),
        "rows_applied_by_kind": dict(Counter(r.kind for r in plan.rows_applied)),
        "rows_already": [r.old for r in plan.rows_already],
        "refused_held": [{"num": r.num, "old": r.old, "held": r.held} for r in plan.refused],
        "file_moves": len(plan.file_moves),
        "created_heads": plan.created_heads,
        "emptied_heads": sorted(plan.emptied_heads),
        "deleted": sorted(plan.deleted),
        "import_statements": {a: st.get(a, 0) for a in ("src", "build", "tests", "tools", "docs")},
        "import_files": {a: plan.import_files.get(a, 0) for a in ("src", "build", "tests", "tools")},
        "import_via_head": {a: vh.get(a, 0) for a in ("src", "build", "tests", "tools")},
        "import_split_statements": {a: sp.get(a, 0) for a in ("src", "build", "tests", "tools")},
        "import_via_package": {a: vp.get(a, 0) for a in ("src", "build", "tests", "tools")},
        "plan_estimate_stage4": PLAN_ESTIMATE,
        "path_strings": dict(plan.str_stats.rewritten),
        "path_string_sites": len(plan.str_stats.sites),
        "path_string_sites_by_file": sorted({f"{f}::{s}" for (f, s) in plan.str_stats.sites}),
        "dropped_reexports": plan.dropped_reexports,
        "dropped_all": plan.dropped_all,
        "ledger_paths_added": plan.ledger_paths_added,
        "class_id_keys": plan.class_keys,
        "class_ids_resorted": plan.class_resorted,
        "changed_files": len(plan.changed),
        "untouched_count": dict(sorted((f"{a}:{k}", v) for (a, k), v in untouched_by.items())),
        "untouched_broad_constants": plan.untouched_broad,
        "skipped_in_allowlist": plan.str_stats.skipped,
        "bridging_ledger": {k: v for k, v in plan.ledger.items() if k != "moving"},
        "bridging_ledger_moving": plan.ledger.get("moving", []),
        "guards": plan.guards,
        "warnings": plan.warnings,
        "untouched": plan.untouched,
    }


def unified_diff(plan: Plan) -> str:
    out: list[str] = []
    b, a = plan.before, plan.after
    inv = {v: k for k, v in plan.file_moves.items()}
    paths = sorted(set(b.files) | set(a.files))
    for p in paths:
        if p in plan.file_moves:
            continue
        old_p = inv.get(p, p)
        old = b.files.get(old_p)
        new = a.files.get(p)
        if old == new and old_p == p:
            continue
        ol = (old or "").splitlines(keepends=True)
        nl = (new or "").splitlines(keepends=True)
        fa = f"a/{old_p}" if old is not None else "/dev/null"
        fb = f"b/{p}" if new is not None else "/dev/null"
        if old_p != p and old == new:
            out.append(f"rename {old_p} → {p}(中身は同じ)\n")
            continue
        out += difflib.unified_diff(ol, nl, fa, fb, n=1)
        if out and not out[-1].endswith("\n"):
            out.append("\n")
    for o in sorted(set(b.files) - set(a.files) - set(plan.file_moves)):
        out.append(f"delete {o}\n")
    for o, n in sorted(plan.file_moves.items()):
        if o in b.blobs:
            out.append(f"rename {o} → {n}(バイト列)\n")
    return "".join(out)


def apply(plan: Plan, root: Path) -> list[str]:
    """書き換えた後の木を ``root`` へ書く(書く・移す・消すのは計画にあるファイルだけ)。終わりに、``src/shibuya`` の下の
    「``__pycache__`` のほかに何も無いディレクトリ」を消す(:func:`prune_cache_only_dirs`)。戻り値=消したディレクトリ。"""
    b, a = plan.before, plan.after
    for p, text in a.files.items():
        if b.files.get(p) == text:
            continue
        dst = root / p
        dst.parent.mkdir(parents=True, exist_ok=True)
        with open(dst, "w", encoding="utf-8", newline="") as f:
            f.write(text)
    for p, data in a.blobs.items():
        if b.blobs.get(p) != data:
            dst = root / p
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(data)
    for p in [*plan.file_moves, *plan.deleted]:
        if p not in a.files and p not in a.blobs:
            (root / p).unlink()
    for p in sorted({str(Path(x).parent) for x in [*plan.file_moves, *plan.deleted]}, key=len, reverse=True):
        d = root / p
        while d != root and d.is_dir() and not any(d.iterdir()):
            os.rmdir(d)
            d = d.parent
    return prune_cache_only_dirs(root)


def _cache_only(d: Path) -> bool:
    """``d`` の中が ``__pycache__`` のディレクトリ(つなぎでない)と空のディレクトリだけ(ほかのファイルが 1 つも無い)。"""
    for x in d.iterdir():
        if x.is_symlink() or (hasattr(x, "is_junction") and x.is_junction()):
            return False
        if x.is_dir() and (x.name == "__pycache__" or _cache_only(x)):
            continue
        return False
    return True


def prune_cache_only_dirs(root: Path) -> list[str]:
    """〔検収 L-a〕``root/src/shibuya`` の下で、``__pycache__`` のほかに何も無いディレクトリ(移した後の古い包みの残り)を
    ``__pycache__`` ごと消す。残すと名前空間の包みとして import できてしまう(同じ木に段を重ねて当てると、前の段の import の
    確かめが作った ``__pycache__`` が残る)。``src/shibuya`` そのものと、つなぎ(シンボリックリンク・junction)は消さない。
    戻り値=消したディレクトリ(``root`` からの道筋・深い順)。"""
    import shutil

    base = Path(root) / "src" / "shibuya"
    removed: list[str] = []
    if not base.is_dir():
        return removed

    def walk(d: Path) -> None:
        for x in sorted(d.iterdir()):
            if (x.is_dir() and not x.is_symlink() and not (hasattr(x, "is_junction") and x.is_junction())
                    and x.name != "__pycache__"):
                walk(x)
        if d != base and d.is_dir() and _cache_only(d):
            shutil.rmtree(d)
            removed.append(d.relative_to(root).as_posix())

    walk(base)
    return removed


def gone_packages(mapdoc: MapDoc, root: Path) -> list[str]:
    """対応表の頭の行(古い ``__init__.py``)のうち、木に頭がもう無い包みの名(移して無くなった包み)。import の確かめが、
    これらが名前空間の包みとして import できないことを見る(検収 L-a)。"""
    return sorted({mod_of(r.old) for r in mapdoc.rows if r.is_head and not (Path(root) / SRC_PREFIX / r.old).exists()})
