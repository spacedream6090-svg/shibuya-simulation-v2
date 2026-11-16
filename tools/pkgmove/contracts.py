# -*- coding: utf-8 -*-
"""段ごとの import の決まり(pyproject の ``[tool.importlinter]`` の節)を、元のファイル ``contracts.toml`` と木の今の形から作る
(親の決定=brief_contracts・2026-11-11・仮採用)。

- ``old_only_through`` の段まで(今は foundation): 今の 5 つの決まり(``[[old]]``)をそのまま。
- その後の段: 計画 §6-4 の新しい決まり(``[[rule]]``)を、その段の木で**最終の名に在るモジュール**だけで言う。単位(層の語と
  build)は、その包みが木に在り、包みの下のモジュール(頭を除く)が全部最終の名のときだけ使う。まだ移っていないファイル
  (古い包みに残る分)は新しい決まりの外。言えない単位・決まりは報告の ``not_expressed`` に出す。
- 古い決まりは、名が木に無いか、名の意味が変わった(ほかの置き場からファイルが入った)名を外して残す。外した名と、残らなかった
  契約は報告の ``dropped_old`` に出す(黙って弱めない)。
- 計画 §6-4 の表の 28 本は、その段の木の今の名に引き直し(割るファイルはまだ古い置き場=今の名)、両側のモジュールが木に在る
  物だけを、当たる決まりの契約の ``ignore_imports`` に載せる。
- 木の当たっている行が、渡した段と食い違えば断る(段の名の取り違えを防ぐ)。
- 〔段 4 の残り・返事その 8 §1-6 の 7・3〕計画 §6-6 の 2 つの決まりは、``from_stage`` の段から入れる(一時の区分を読めるのは
  runtime と interfaces だけ=interim_bundles の段から・runtime の核は中身を読まない=delete の段から)。§6-6 の表の辺は
  ``[[ignore_66]]``(28 本と同じ扱い=その段の木の今の名に引き直し、両側と辺が在る物だけを載せる)。
- 報告に例外(ignore)の数を出す: 延べの行(``ignore_lines``)・重なりを除いた辺(``ignore_unique``)・重なりを除いた辺の
  「消える段」ごとの数(``ignore_gone_at``)。〔検収 中-1〕載せる条件は「両側と辺が在る」だけなので、何も止めていない例外も
  載る(一覧は計画の 28 本と「消える段」の注を保つために変えない)。``cli.py contracts --out``(か ``--probe``)は、効いている
  例外(外すと契約が broken になる行と辺)の数を ``ignore_effective`` に足す(:func:`effective_ignores`)。
"""
from __future__ import annotations

import ast
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from pkgmove import move as MV
from pkgmove.model import SRC_PREFIX, Index, Tree, mod_of, resolve_from, rel_of_mod
from pkgmove.table import MapDoc

CONTRACTS_REL = "tools/pkgmove/contracts.toml"
SECTION_MARK = "# ---- 層契約"


class ContractsError(ValueError):
    """木の形が段と合わない・pyproject の節の形が読めない。"""


@dataclass
class Spec:
    root: str
    old_only_through: str
    stage_order: tuple[str, ...]
    layers: list[str]
    side: list[str]
    rules: list[dict]
    old: list[dict]
    ignores: list[dict]
    extras: list[dict] = field(default_factory=list)
    ignores66: list[dict] = field(default_factory=list)
    #: 〔割る段 5a・親の裁定 Q3〕割る段で出る辺(``appears_with`` の割る行を当てた木から載せる)。
    ignores_split: list[dict] = field(default_factory=list)
    #: 〔割る段 5a・検収 高-1〕割る行を当てて弱まってよい決まり(計画どおりのもの)。:func:`weakened` が使う。
    split_weakens: list[dict] = field(default_factory=list)

    @property
    def units(self) -> list[str]:
        """層の語と横の包み(上から)。"""
        out: list[str] = []
        for lay in self.layers:
            out += [x.strip() for x in lay.split("|")]
        return out + list(self.side)


def load_spec(path: Path) -> Spec:
    d = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    return Spec(root=d["root_package"], old_only_through=d["old_only_through"], stage_order=tuple(d["stage_order"]),
                layers=list(d["layers"]), side=list(d.get("side", [])), rules=list(d["rule"]), old=list(d["old"]),
                ignores=list(d["ignore"]), extras=list(d.get("extra_ignore", [])),
                ignores66=list(d.get("ignore_66", [])), ignores_split=list(d.get("ignore_split", [])),
                split_weakens=list(d.get("split_weakens", [])))


def _why_names(why: str) -> set[str] | None:
    """言えない理由が名の並び(「…もの: a, b」)なら、その名の集合。ほかの形なら ``None``。"""
    head, sep, tail = why.partition("もの: ")
    if not sep:
        return None
    return {x.strip() for x in tail.split(",") if x.strip()}


def _loaded_ignores(rep: dict) -> set[str]:
    """載せた例外の行(表の名と番号=今の名に引き直す前の行の名)。割る段の表(``[[ignore_split]]``)は除く(本ごとの宣言)。"""
    out: set[str] = set()
    for key in ("ignores", "ignores_66"):
        out |= {f"{key}#{r['num']}" for r in rep.get(key, []) if "skipped" not in r}
    out |= {f"extra_ignores#{r['importer']} -> {r['imported']}" for r in rep.get("extra_ignores", []) if "skipped" not in r}
    return out


def weakened(spec: Spec, split_old: str, before: dict, after: dict) -> dict:
    """〔割る段 5a・検収 高-1・再検収 低-1〕割る行 ``split_old`` を当てる前と後の報告(:func:`build` の 2 つ目)を比べ、決まりが
    弱まった所を出す。比べるもの:

    - ``not_expressed`` に増えた (決まり, 名)=言えなくなった単位・決まり。前から言えない (決まり, 名) でも、理由が名の並び
      (「元の側の名のうち木で言えないもの: …」)なら、並びに増えた名。
    - ``dropped_old`` に増えた (契約, 名)=古い決まりから外れた名・丸ごと外れた古い決まり。
    - ``uncovered`` に増えたモジュール=どの決まりの元の側にも入らなくなったモジュール。
    - ``late_allowed`` に増えた (決まり, モジュール)=まだ移っていないので読んでよい側に足した読み手。
    - 載せた例外の行の増え(28 本・§6-6・表の外の表。``[[ignore_split]]`` はその本の宣言なので除く)。

    ``[[split_weakens]]`` のその割る行の宣言(``old_names_gone``=古い決まりから外れてよい名・``contracts_gone``=丸ごと外れて
    よい古い決まり・``not_expressed``=言えなくなってよい「決まり|名」・``other``=ほかの項の文字列そのもの)に当たるものは
    ``declared``、ほかは ``undeclared``(割る道具が止める)。宣言のうち当たらなかったものは ``unused``(報告だけ)。"""
    decl = [w for w in spec.split_weakens if w["split"] == split_old]
    names_ok = {n for w in decl for n in w.get("old_names_gone", [])}
    contracts_ok = {c for w in decl for c in w.get("contracts_gone", [])}
    ne_ok = {x for w in decl for x in w.get("not_expressed", [])}
    other_ok = {x for w in decl for x in w.get("other", [])}
    out: dict = {"declared": [], "undeclared": [], "unused": []}
    used: set[str] = set()

    def put(text: str, key: str | None, ok: bool) -> None:
        (out["declared"] if ok else out["undeclared"]).append(text)
        if ok and key is not None:
            used.add(key)

    ne_b = {(str(x["rule"]), x["name"]): x["why"] for x in before["not_expressed"]}
    ne_a = {(str(x["rule"]), x["name"]): x["why"] for x in after["not_expressed"]}
    for (r, n), why in sorted(ne_a.items()):
        key = f"{r}|{n}"
        if (r, n) not in ne_b:
            put(f"言えなくなった: {key}", key, key in ne_ok)
            continue
        wb, wa = _why_names(ne_b[(r, n)]), _why_names(why)
        if wb is not None and wa is not None and wa - wb:
            text = f"言えない名が増えた: {key}: {', '.join(sorted(wa - wb))}"
            put(text, text, text in other_ok)
    do_b = {(x["contract"], x["name"]) for x in before["dropped_old"]}
    for c, n in sorted({(x["contract"], x["name"]) for x in after["dropped_old"]} - do_b):
        ok = (n == "(契約)" and c in contracts_ok) or (n != "(契約)" and n in names_ok)
        put(f"古い決まりから外れた: {c} の {n}", c if n == "(契約)" else n, ok)
    for m in sorted(set(after.get("uncovered", [])) - set(before.get("uncovered", []))):
        text = f"どの決まりも見なくなった: {m}"
        put(text, text, text in other_ok)
    late_b = {(str(x["rule"]), m) for x in before.get("late_allowed", []) for m in x["modules"]}
    for r, m in sorted({(str(x["rule"]), m) for x in after.get("late_allowed", []) for m in x["modules"]} - late_b):
        text = f"読んでよい側に足した読み手が増えた: 決まり {r} の {m}"
        put(text, text, text in other_ok)
    for row in sorted(_loaded_ignores(after) - _loaded_ignores(before)):
        text = f"載せた例外が増えた: {row}"
        put(text, text, text in other_ok)
    out["unused"] = sorted((names_ok | contracts_ok | ne_ok | other_ok) - used)
    out["contracts_before"] = {"old": before["n_old"], "new": before["n_new"]}
    out["contracts_after"] = {"old": after["n_old"], "new": after["n_new"]}
    return out


@dataclass
class TreeView:
    """木の今の形: モジュールの集合・今の名 → 最終の名・ほかの置き場から入ったファイル(古い名, 新しい名)。"""

    modules: set[str]
    packages: set[str]
    final_of: dict[str, str]
    moved_in: list[tuple[str, str]]
    fallbacks: list[str] = field(default_factory=list)

    def under(self, name: str) -> list[str]:
        return [m for m in self.modules if m == name or m.startswith(name + ".")]

    def is_final(self, m: str) -> bool:
        return self.final_of.get(m) == m


def view(tree: Tree, mapdoc: MapDoc) -> TreeView:
    ix = Index(tree)
    final_of: dict[str, str] = {}
    moved_in: list[tuple[str, str]] = []
    for r in mapdoc.rows:
        if not r.old.endswith(".py") or r.kind == "delete":
            continue
        new = r.new or r.old
        if r.is_head:
            # 〔割る段 5a・検収 高-1〕頭を割る行(llm/__init__.py): 中身が割り先へ出た後(元の頭が無いか 0 バイト)は、主な割り先が
            # 最終の名。前は頭の行を全部飛ばし、主な割り先が最終の名にならず、その単位(foundation)と決まりが黙って言えなくなった
            if (r.kind == "split" and new != r.old and tree.exists(SRC_PREFIX + new)
                    and not tree.files.get(SRC_PREFIX + r.old)):
                final_of[mod_of(new)] = mod_of(new)
                moved_in.append((mod_of(r.old), mod_of(new)))
            continue
        if tree.exists(SRC_PREFIX + new) and (new == r.old or not tree.exists(SRC_PREFIX + r.old)):
            final_of[mod_of(new)] = mod_of(new)
            if new != r.old:
                moved_in.append((mod_of(r.old), mod_of(new)))
        elif tree.exists(SRC_PREFIX + r.old):
            final_of[mod_of(r.old)] = mod_of(new)
    return TreeView(modules=set(ix.mods), packages=set(ix.packages), final_of=final_of, moved_in=moved_in)


def check_stage(tree: Tree, mapdoc: MapDoc, spec: Spec, stage: str) -> list[str]:
    """木の当たっている行が「段の順で ``stage`` まで」と同じか(保留の行を除く)。"""
    if stage not in spec.stage_order:
        raise ContractsError(f"段の名が違う: {stage}(段は {', '.join(spec.stage_order)})")
    k = spec.stage_order.index(stage)
    errs: list[str] = []
    for r in mapdoc.rows:
        if r.kind not in ("move", "empty", "delete") or r.held or r.split_from:  # 〔割る段 5a〕割り先の行は段の行でない
            continue
        want = spec.stage_order.index(r.stage) <= k
        try:
            got = MV._row_state(tree, r) == "already"
        except MV.Refused as e:
            errs.append(f"行 {r.num}: {e}")
            continue
        if want != got:
            errs.append(f"行 {r.num} {r.old}(段 {r.stage}): {'当たっていない' if want else '当たっている'}")
    return errs


def _name_ok(v: TreeView, root: str, p: str) -> bool:
    """名(``shibuya.`` を除く)が木に在り最終の名か(モジュールなら最終の名・包みなら頭を除く中身が全部最終の名)。"""
    name = f"{root}.{p}"
    return (name in v.modules and v.is_final(name)) or (name in v.packages and _unit_ok(v, root, p)[0])


def _unit_ok(v: TreeView, root: str, unit: str) -> tuple[bool, str]:
    name = f"{root}.{unit}"
    if name not in v.modules:
        return False, "木に無い"
    body = [m for m in v.under(name) if m not in v.packages]
    if not body:
        return False, "中身のモジュールが無い"
    old = sorted(m for m in body if not v.is_final(m))
    if old:
        return False, f"最終の名でないモジュールがある({old[0]} ほか {len(old)})"
    return True, ""


def _translate(v: TreeView, mapdoc: MapDoc, final: str) -> str | None:
    """最終の名(計画の 28 本の名)→ 今の木の名。割るファイルの既定の割り先は、割る前は古い置き場。"""
    for cur, fin in v.final_of.items():
        if fin == final:
            return cur
    for r in mapdoc.rows:  # 既定の割り先でない割り先の名(例 act.commit)=割る前は古い置き場
        if r.kind == "split" and final in {mod_of(x) for x in r.split_to} and mod_of(r.old) in v.modules:
            v.fallbacks.append(f"{final} → {mod_of(r.old)}(割り先の一覧から・既定の割り先は {mod_of(r.new)})")
            return mod_of(r.old)
    return None


def _old_name_state(v: TreeView, root: str, p: str) -> str:
    name = f"{root}.{p}"
    if name not in v.modules:
        return "木に無い"
    if any(n == name or n.startswith(name + ".") for o, n in v.moved_in if not (o == name or o.startswith(name + "."))):
        return "名の意味が変わった(ほかの置き場からファイルが入った)"
    return ""


def has_edge(tree: Tree, v: TreeView, importer: str, imported: str) -> bool:
    """木で ``importer`` が ``imported`` を読む import の文が在るか(関数の中を含む・相対も解く)。"""
    path = SRC_PREFIX + rel_of_mod(importer, package=importer in v.packages)
    text = tree.files.get(path)
    if text is None:
        return False
    pkg = importer if importer in v.packages else importer.rpartition(".")[0]
    for n in ast.walk(ast.parse(text)):
        if isinstance(n, ast.ImportFrom):
            m = resolve_from(pkg, n)
            if m == imported or any(f"{m}.{a.name}" == imported for a in n.names):
                return True
        elif isinstance(n, ast.Import):
            if any(a.name == imported or a.name.startswith(imported + ".") for a in n.names):
                return True
    return False


def build(spec: Spec, mapdoc: MapDoc, tree: Tree, stage: str) -> tuple[list[dict], dict]:
    """(契約の一覧=pyproject の [[tool.importlinter.contracts]] の形, 報告)。"""
    errs = check_stage(tree, mapdoc, spec, stage)
    if errs:
        raise ContractsError(f"木の当たっている行が段 {stage} と食い違う({len(errs)}): " + "; ".join(errs[:5]))
    v = view(tree, mapdoc)
    root = spec.root
    rep: dict = {"stage": stage, "dropped_old": [], "not_expressed": [], "ignores": [], "fallbacks": []}
    contracts: list[dict] = []
    old_only = spec.stage_order.index(stage) <= spec.stage_order.index(spec.old_only_through)
    # ---- 古い決まり
    for oc in spec.old:
        if old_only:
            contracts.append(_old_contract(root, oc, oc.get("layers"), oc.get("source"), oc.get("forbidden")))
            continue
        keep = lambda names: [x for x in names if not _drop(v, root, oc, x, rep)]  # noqa: E731
        if oc["type"] == "layers":
            lays = []
            for lay in oc["layers"]:
                toks = keep([x.strip() for x in lay.split("|")])
                if toks:
                    lays.append(" | ".join(toks))
            if len(lays) < 2:
                rep["dropped_old"].append({"contract": oc["name"], "name": "(契約)", "why": "残る層が 2 つ未満"})
                continue
            contracts.append(_old_contract(root, oc, lays, None, None))
        else:
            src, fb = keep(oc["source"]), keep(oc["forbidden"])
            if not src or not fb:
                rep["dropped_old"].append({"contract": oc["name"], "name": "(契約)",
                                           "why": "元の側か禁じる側が空になった"})
                continue
            contracts.append(_old_contract(root, oc, None, src, fb))
    rep["n_old"] = len(contracts)
    if old_only:
        rep["n_new"] = 0
        rep["uncovered"] = uncovered(contracts, v, root)
        rep.update(ignore_counts(contracts, rep))
        return contracts, rep
    # ---- 新しい決まり
    ok: dict[str, bool] = {}
    for u in spec.units:
        good, why = _unit_ok(v, root, u)
        ok[u] = good
        if not good:
            rep["not_expressed"].append({"rule": "単位", "name": u, "why": why})
    ign_by_rule: dict[int, list[str]] = {}
    rep["ignores_66"] = []
    for key, table in (("ignores", spec.ignores), ("ignores_66", spec.ignores66)):  # 計画 §6-4 の 28 本と §6-6 の表
        for g in table:
            a, b = _translate(v, mapdoc, f"{root}.{g['importer']}"), _translate(v, mapdoc, f"{root}.{g['imported']}")
            row = {"num": g["num"], "importer": a, "imported": b, "gone_at": g["gone_at"], "rules": g["rules"]}
            if a is None or b is None or a not in v.modules or b not in v.modules:
                row["skipped"] = "片側のモジュールが木に無い"
                rep[key].append(row)
                continue
            if not has_edge(tree, v, a, b):
                row["skipped"] = "辺が無い"
                rep[key].append(row)
                continue
            rep[key].append(row)
            for rid in g["rules"]:
                ign_by_rule.setdefault(int(rid), []).append(f"{a} -> {b}")
    rep["extra_ignores"] = []
    for g in spec.extras:  # 計画の表の外の辺(名は今の木の名)
        a, b = f"{root}.{g['importer']}", f"{root}.{g['imported']}"
        row = {"importer": a, "imported": b, "rules": g["rules"], "note": g["note"], "gone_at": g.get("gone_at", "")}
        if a not in v.modules or b not in v.modules or not has_edge(tree, v, a, b):
            row["skipped"] = "片側のモジュールか辺が木に無い"
        else:
            for rid in g["rules"]:
                ign_by_rule.setdefault(int(rid), []).append(f"{a} -> {b}")
        rep["extra_ignores"].append(row)
    rep["ignores_split"] = []
    if spec.ignores_split:  # 〔割る段 5a・親の裁定 Q3〕appears_with の割る行を当てた木から載せる
        from pkgmove import split as SP

        by = mapdoc.by_old()
        for g in spec.ignores_split:
            row = {"num": g["num"], "importer": None, "imported": None, "gone_at": g["gone_at"], "rules": g["rules"],
                   "appears_with": g["appears_with"]}
            sr = by.get(g["appears_with"])
            if sr is None:  # 対応表にその割る行が無い(見本の表)=載せない
                row["skipped"] = "対応表に割る行が無い"
                rep["ignores_split"].append(row)
                continue
            if sr.kind != "split":
                raise ContractsError(f"[[ignore_split]] の appears_with が割る行でない: {g['appears_with']}")
            if not SP.is_done(tree, sr):
                row["skipped"] = "割る行がまだ当たっていない"
                rep["ignores_split"].append(row)
                continue
            a, b = _translate(v, mapdoc, f"{root}.{g['importer']}"), _translate(v, mapdoc, f"{root}.{g['imported']}")
            row.update(importer=a, imported=b)
            if a is None or b is None or a not in v.modules or b not in v.modules or not has_edge(tree, v, a, b):
                row["skipped"] = "片側のモジュールか辺が木に無い"
            else:
                for rid in g["rules"]:
                    ign_by_rule.setdefault(int(rid), []).append(f"{a} -> {b}")
            rep["ignores_split"].append(row)
    rep["fallbacks"] = sorted(set(v.fallbacks))
    units = spec.units
    n_new = 0
    k = spec.stage_order.index(stage)
    for rule in spec.rules:
        fs = rule.get("from_stage")
        if fs and k < spec.stage_order.index(fs):  # 〔§6-6〕その段からの決まり
            rep["not_expressed"].append({"rule": rule["id"], "name": rule["name"], "why": f"段 {fs} から入れる"})
            continue
        c = _new_contract(spec, rule, ok, units, v, root, rep)
        if c is None:
            continue
        ig = sorted(set(ign_by_rule.get(int(rule["id"]), [])))
        if ig:
            c["ignore_imports"] = ig
        contracts.append(c)
        n_new += 1
    rep["n_new"] = n_new
    rep["uncovered"] = uncovered(contracts, v, root)
    rep.update(ignore_counts(contracts, rep))
    return contracts, rep


def _gone_by_edge(rep: dict) -> dict[str, set[str]]:
    gone: dict[str, set[str]] = {}
    for row in [*rep.get("ignores", []), *rep.get("ignores_66", []), *rep.get("extra_ignores", []),
                *rep.get("ignores_split", [])]:
        if row.get("skipped"):
            continue
        gone.setdefault(f"{row['importer']} -> {row['imported']}", set()).add(row.get("gone_at") or "(注なし)")
    return gone


def _count_gone(edges, gone: dict[str, set[str]]) -> dict[str, int]:
    by: dict[str, int] = {}
    for e in edges:
        g = "・".join(sorted(gone.get(e, {"(注なし)"})))
        by[g] = by.get(g, 0) + 1
    return dict(sorted(by.items()))


def ignore_counts(contracts: list[dict], rep: dict) -> dict:
    """例外(ignore)の数(返事その 8 §1-12 の 3): 延べの行・重なりを除いた辺・重なりを除いた辺の「消える段」ごとの数。
    消える段は、辺を載せた元の行(計画 §6-4 の 28 本・§6-6 の表・表の外の辺)の注から引く(1 つの辺に違う注があれば ``・`` で
    つなぐ)。載せる条件は「両側が木に在り辺が在る」だけなので、何も止めていない例外も数に入る(効いている数は
    :func:`effective_ignores`)。"""
    lines = [x for c in contracts for x in c.get("ignore_imports", [])]
    uniq = sorted(set(lines))
    return {"ignore_lines": len(lines), "ignore_unique": len(uniq), "ignore_gone_at": _count_gone(uniq, _gone_by_edge(rep))}


def effective_ignores(root: Path, spec: Spec, contracts: list[dict], rep: dict) -> dict:
    """〔検収 中-1〕効いている例外の数: 例外の行を 1 本ずつ外すと、その契約が broken になる行(延べ)と、どれかの契約で効く辺
    (重なりを除く)・消える段ごとの数。木を変えずに、子のプロセスでメモリの中で回す(:mod:`pkgmove.ignoreprobe`)。"""
    import json
    import os
    import subprocess
    import sys

    payload = {"root_package": spec.root, "session": {"include_external_packages": False}, "contracts": contracts}
    env = {k: v for k, v in os.environ.items() if k.upper() != "PYTHONPATH"}
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, str(Path(__file__).with_name("ignoreprobe.py")), str(root), "-"],
                       input=json.dumps(payload, ensure_ascii=False).encode("utf-8"), capture_output=True, env=env)
    if r.returncode != 0:
        raise ContractsError("効いている例外の確かめが落ちた: " + r.stderr.decode("utf-8", "replace")[-800:])
    out = json.loads(r.stdout.decode("utf-8"))
    eff = sorted({d["edge"] for d in out["detail"] if d["effective"]})
    return {"lines": out["effective_lines"], "unique": out["effective_unique"],
            "gone_at": _count_gone(eff, _gone_by_edge(rep)), "not_effective": out["not_effective"],
            "base_kept": out["base_kept"], "broken": out["broken"], "jointly_kept": out["jointly_kept"],
            "detail": out["detail"]}


def uncovered(contracts: list[dict], v: TreeView, root: str) -> list[str]:
    """どの契約の元の側(層の名・``source_modules``)にも入らないランの側のモジュール(頭・根・build を除く)。そのモジュールから
    出る辺は、覆われたモジュールを通る連なりのほかは、どの決まりも見ない(検収 第 3 回 L-2)。"""
    names: set[str] = set()
    for c in contracts:
        for lay in c.get("layers", []):
            names |= {x.strip() for x in lay.split("|")}
        names |= set(c.get("source_modules", []))
    side = f"{root}.build"
    return sorted(m for m in v.modules if m not in v.packages and m != root and not (m == side or m.startswith(side + "."))
                  and not any(m == n or m.startswith(n + ".") for n in names))


def _drop(v: TreeView, root: str, oc: dict, name: str, rep: dict) -> bool:
    why = _old_name_state(v, root, name)
    if why:
        rep["dropped_old"].append({"contract": oc["name"], "name": name, "why": why})
        return True
    return False


def _old_contract(root: str, oc: dict, layers, source, forbidden) -> dict:
    q = lambda xs: [f"{root}.{x}" for x in xs]  # noqa: E731
    if oc["type"] == "layers":
        return {"name": oc["name"], "type": "layers",
                "layers": [" | ".join(f"{root}.{t.strip()}" for t in lay.split("|")) for lay in layers]}
    return {"name": oc["name"], "type": "forbidden", "source_modules": q(source), "forbidden_modules": q(forbidden)}


def _new_contract(spec: Spec, rule: dict, ok: dict[str, bool], units: list[str], v: TreeView, root: str,
                  rep: dict) -> dict | None:
    name = f"〔段 4 の途中の決まり〕{rule['name']}"
    say = lambda why: rep["not_expressed"].append({"rule": rule["id"], "name": rule["name"], "why": why})  # noqa: E731
    q = lambda xs: [f"{root}.{x}" for x in xs]  # noqa: E731
    t = rule["type"]
    if t == "layers":
        lays = []
        for lay in spec.layers:
            toks = [x.strip() for x in lay.split("|") if ok.get(x.strip())]
            if toks:
                lays.append(" | ".join(f"{root}.{x}" for x in toks))
        if len(lays) < 2:
            say("言える層が 2 つ未満")
            return None
        return {"name": name, "type": "layers", "layers": lays}
    if t == "forbidden":
        if "source_all_except" in rule:
            src = [u for u in units if ok[u] and u not in rule["source_all_except"]]
        elif "source_names" in rule:  # 〔§6-6 の 2〕単位でないモジュールと包みの名(runtime の核)
            src = [p for p in rule["source_names"] if _name_ok(v, root, p)]
            miss = [p for p in rule["source_names"] if p not in src]
            if miss:
                say(f"元の側の名のうち木で言えないもの: {', '.join(miss)}")
        else:
            src = [u for u in rule["source"] if ok.get(u)]
        if "forbidden_all_except" in rule:
            fb = [u for u in units if ok[u] and u not in rule["forbidden_all_except"]]
        else:
            fb = [u for u in rule["forbidden"] if ok.get(u)]
        if not src or not fb:
            say("元の側か禁じる側が木で言えない(まだ移っていない)")
            return None
        c = {"name": name, "type": "forbidden", "source_modules": q(src), "forbidden_modules": q(fb)}
        if rule.get("allow_indirect_imports"):  # 直の辺だけを見る(§6-6 の 2=計画は直の辺で数えた)
            c["allow_indirect_imports"] = True
        return c
    if t == "protected":
        prot = [p for p in rule["protected"] if _name_ok(v, root, p)]
        allowed = q([u for u in rule["allowed"] if ok.get(u)])
        if not prot:
            say("守る側のモジュールが木に無い(割る段の後)")
            return None
        # まだ移っていない読み手(古い置き場のモジュール)は、最終の置き場が読んでよい側なら読んでよい側に足す(移していない
        # ことだけで落とさない=新しい決まりの外。最終の置き場が読んでよくない側なら、移した後も当たる=落とす)
        late = sorted(m for m, fin in v.final_of.items() if m != fin
                      and any(fin == f"{root}.{u}" or fin.startswith(f"{root}.{u}.") for u in rule["allowed"]))
        if late:
            rep.setdefault("late_allowed", []).append({"rule": rule["id"], "modules": late})
        return {"name": name, "type": "protected", "protected_modules": q(prot), "allowed_importers": allowed + late}
    raise ContractsError(f"決まりの型が読めない: {t}")


# ------------------------------------------------------------------ pyproject の節
def _q(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def render(spec: Spec, stage: str, contracts: list[dict]) -> str:
    out = [f"{SECTION_MARK}(段 4 の段 {stage} の木の決まり。元は {CONTRACTS_REL}・"
           f"`python tools/pkgmove/cli.py contracts --stage {stage}` が作る。手で直さない)----",
           "[tool.importlinter]", f"root_package = {_q(spec.root)}", "include_external_packages = false"]
    for c in contracts:
        out += ["", "[[tool.importlinter.contracts]]", f"name = {_q(c['name'])}", f"type = {_q(c['type'])}"]
        for key in ("layers", "source_modules", "forbidden_modules", "protected_modules", "allowed_importers",
                    "ignore_imports"):
            if key in c:
                out.append(f"{key} = [")
                out += [f"  {_q(x)}," for x in c[key]]
                out.append("]")
        if "allow_indirect_imports" in c:
            out.append(f"allow_indirect_imports = {'true' if c['allow_indirect_imports'] else 'false'}")
    return "\n".join(out) + "\n"


def split_pyproject(text: str) -> tuple[str, str]:
    """(節の前, 節)。節は「# ---- 層契約」の行(無ければ ``[tool.importlinter]`` の行)から終わりまで。後ろに別の表があれば断る。"""
    lines = text.splitlines(keepends=True)
    try:
        k = next(i for i, x in enumerate(lines) if x.strip() == "[tool.importlinter]")
    except StopIteration:
        raise ContractsError("pyproject に [tool.importlinter] が無い") from None
    if k > 0 and lines[k - 1].startswith(SECTION_MARK):
        k -= 1
    for x in lines[k:]:
        s = x.strip()
        if s.startswith("[") and s not in ("[tool.importlinter]", "[[tool.importlinter.contracts]]"):
            raise ContractsError(f"[tool.importlinter] の後ろに別の表がある: {s}")
    return "".join(lines[:k]), "".join(lines[k:])


def section_dict(text: str) -> dict:
    return tomllib.loads(text).get("tool", {}).get("importlinter", {})


def same_section(a: str, b: str) -> bool:
    """節の中身(名・型・名の並び)が同じか(書き方の違いは見ない)。"""
    da, db = section_dict(a), section_dict(b)

    def norm(d: dict) -> dict:
        d = dict(d)
        d["contracts"] = [{k: v for k, v in c.items()} for c in d.get("contracts", [])]
        return d
    return norm(da) == norm(db)


def old_contracts(spec: Spec) -> list[dict]:
    """今の 5 つの決まり(移す前と old_only_through の段まで)の契約。"""
    return [_old_contract(spec.root, oc, oc.get("layers"), oc.get("source"), oc.get("forbidden")) for oc in spec.old]


def stage_of(tree: Tree, mapdoc: MapDoc, spec: Spec) -> str | None:
    """木の段: どの段の行も当たっていなければ ``""``・段の順で ``S`` までが当たっていれば ``S``・どちらでもなければ ``None``。"""
    if all(MV._row_state(tree, r) == "apply" for r in mapdoc.rows
           if r.kind in ("move", "empty", "delete") and not r.held and not r.split_from):
        return ""
    for s in spec.stage_order:
        if not check_stage(tree, mapdoc, spec, s):
            return s
    return None
