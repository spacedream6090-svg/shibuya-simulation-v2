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
                ignores=list(d["ignore"]), extras=list(d.get("extra_ignore", [])))


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
        if not r.old.endswith(".py") or r.is_head or r.kind == "delete":
            continue
        new = r.new or r.old
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
        if r.kind not in ("move", "empty", "delete") or r.held:
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
        return contracts, rep
    # ---- 新しい決まり
    ok: dict[str, bool] = {}
    for u in spec.units:
        good, why = _unit_ok(v, root, u)
        ok[u] = good
        if not good:
            rep["not_expressed"].append({"rule": "単位", "name": u, "why": why})
    ign_by_rule: dict[int, list[str]] = {}
    for g in spec.ignores:
        a, b = _translate(v, mapdoc, f"{root}.{g['importer']}"), _translate(v, mapdoc, f"{root}.{g['imported']}")
        row = {"num": g["num"], "importer": a, "imported": b, "gone_at": g["gone_at"], "rules": g["rules"]}
        if a is None or b is None or a not in v.modules or b not in v.modules:
            row["skipped"] = "片側のモジュールが木に無い"
            rep["ignores"].append(row)
            continue
        if not has_edge(tree, v, a, b):
            row["skipped"] = "辺が無い"
            rep["ignores"].append(row)
            continue
        rep["ignores"].append(row)
        for rid in g["rules"]:
            ign_by_rule.setdefault(int(rid), []).append(f"{a} -> {b}")
    rep["extra_ignores"] = []
    for g in spec.extras:  # 計画の表の外の辺(名は今の木の名)
        a, b = f"{root}.{g['importer']}", f"{root}.{g['imported']}"
        row = {"importer": a, "imported": b, "rules": g["rules"], "note": g["note"]}
        if a not in v.modules or b not in v.modules or not has_edge(tree, v, a, b):
            row["skipped"] = "片側のモジュールか辺が木に無い"
        else:
            for rid in g["rules"]:
                ign_by_rule.setdefault(int(rid), []).append(f"{a} -> {b}")
        rep["extra_ignores"].append(row)
    rep["fallbacks"] = sorted(set(v.fallbacks))
    units = spec.units
    n_new = 0
    for rule in spec.rules:
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
    return contracts, rep


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
        else:
            src = [u for u in rule["source"] if ok.get(u)]
        if "forbidden_all_except" in rule:
            fb = [u for u in units if ok[u] and u not in rule["forbidden_all_except"]]
        else:
            fb = [u for u in rule["forbidden"] if ok.get(u)]
        if not src or not fb:
            say("元の側か禁じる側が木で言えない(まだ移っていない)")
            return None
        return {"name": name, "type": "forbidden", "source_modules": q(src), "forbidden_modules": q(fb)}
    if t == "protected":
        prot = [p for p in rule["protected"] if f"{root}.{p}" in v.modules and v.is_final(f"{root}.{p}")
                or (f"{root}.{p}" in v.packages and _unit_ok(v, root, p)[0])]
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
           if r.kind in ("move", "empty", "delete") and not r.held):
        return ""
    for s in spec.stage_order:
        if not check_stage(tree, mapdoc, spec, s):
            return s
    return None
