"""10f の材料(AST の検査を外の状態に広げる): 状態台帳の外の状態の行が指す属性の「読み手」を AST で数え、
読み方の形で分類する(src は読むだけ・試作の検査ではなく見積りのための計数)。

読み方の形(実行役の自前の分類=未リサーチ(expedient)):
- ``self_owner``     : 持ち主のクラスの中の ``self.x`` の読み(``self.x[...]``・``self.x.get(..)``・``for .. in self.x`` を含む)
- ``self_other``     : 別のクラスの中の ``self.x``(同じ名前の別物=名前の衝突)
- ``attr_other``     : ``obj.x``(受け手が self でない)。関数の中の入れ子の関数・lambda の中なら ``closure`` の印も付ける
- ``getattr_lit``    : ``getattr(obj, "x"[, 既定])``
- ``getattr_dyn``    : ``getattr(obj, 変数)``(どの属性か静的に決まらない)
- ``generic``        : 直列化・ハッシュ・保存・戻しの書き手(``engine/state_hashes.py``・``engine/resume.py``・
                       ``engine/state_ledger*.py``・``engine/resolve.py`` の ``restore_*``)
- ``local``          : 持ち主が ``run_day`` の局所変数の行(``run_day.pending`` など)=属性ではなく名前の読み
書き(代入の左辺・``self.x[...] =``・``self.x += ..`` の左辺)は読みに数えない。``self.x += ..`` の右辺は自己更新。

出すもの: 行ごと・属性ごとの形の数、10d で漏れた 14+1 項目の形、軸 1 が no/diag の属性の「持ち主の外の読み」
(今の SoA の検査と同じ規則を当てたときの違反の候補=誤検出の見込み)、軸 1 が behavior なのに読みが 0 の属性、
同じ属性名を持つクラスの数(衝突)、走査の時間。

使い方::

    python docs/bench/analysis/wallbounce-1006/scripts/10f/ext_readers_ast.py --out <json>
"""

from __future__ import annotations

import argparse
import ast
import collections
import json
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
SRC = REPO / "src" / "shibuya"
GENERIC_FILES = {"engine/state_hashes.py", "engine/resume.py", "engine/state_ledger.py", "engine/state_ledger_ast.py"}
LEAKED_10D = [
    "presence._pulled_in_today", "classical._ipf_cache", "conv.n_opened",
    "ledger.money._snap", "ledger.money._flow_daily", "ledger.money._raw_pos", "ledger.money._raw_head",
    "ledger.money._day_marks", "ledger.money.n_raw_dropped", "ledger.money.n_transfers",
    "ledger.goods._dl_pos", "ledger.goods._dl_head", "ledger.goods._dl_marks", "ledger.goods.n_delivery_dropped",
    "poi_resolver.named_closed",
]


def _class_assigns(trees: dict[str, ast.Module]) -> dict[str, set[str]]:
    """属性名 → それを ``self.x = ..`` で持つクラス(``path:Class``)の集合。"""
    out: dict[str, set[str]] = collections.defaultdict(set)
    for rel, tree in trees.items():
        for c in ast.walk(tree):
            if not isinstance(c, ast.ClassDef):
                continue
            for n in ast.walk(c):
                tgs = []
                if isinstance(n, ast.Assign):
                    tgs = n.targets
                elif isinstance(n, (ast.AnnAssign, ast.AugAssign)):
                    tgs = [n.target]
                for t in tgs:
                    while isinstance(t, ast.Subscript):
                        t = t.value
                    if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self":
                        out[t.attr].add(f"{rel}:{c.name}")
            for s in c.body:
                if isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name):
                    out[s.target.id].add(f"{rel}:{c.name}")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    import sys

    sys.path.insert(0, str(REPO / "src"))
    from shibuya.engine import state_ledger as SL

    t0 = time.perf_counter()
    files = [p for p in sorted(SRC.rglob("*.py")) if "build" not in p.relative_to(SRC).parts]
    trees = {p.relative_to(SRC).as_posix(): ast.parse(p.read_text(encoding="utf-8")) for p in files}
    t_parse = time.perf_counter() - t0

    # 属性 → (持ち主, 行, 軸 1, 軸 2)
    attr_rows: dict[str, list[dict]] = collections.defaultdict(list)
    local_rows: list[dict] = []
    for r in SL.external_rows():
        for it in r.items:
            if it in SL.OWNER_CLASSES:
                continue
            owner, attr = it.rsplit(".", 1)
            rec = {"path": it, "owner": owner, "row": r.key, "behavior": r.behavior, "restore": r.restore}
            if owner in SL.OWNER_CLASSES:
                attr_rows[attr].append(rec)
            else:
                local_rows.append(rec)
    owner_cls = {}
    for owner, (rel, cls) in SL.OWNER_CLASSES.items():
        owner_cls.setdefault(owner, set()).add(f"{rel}:{cls}")
        for rel2, cls2 in SL.OWNER_ALT_CLASSES.get(owner, ()):
            owner_cls[owner].add(f"{rel2}:{cls2}")
    names = set(attr_rows)
    assigns = _class_assigns(trees)

    sites: dict[str, list[dict]] = collections.defaultdict(list)
    dyn_getattr: list[str] = []
    t1 = time.perf_counter()
    for rel, tree in trees.items():
        par: dict[ast.AST, ast.AST] = {}
        for n in ast.walk(tree):
            for ch in ast.iter_child_nodes(n):
                par[ch] = n

        def ctx(node: ast.AST) -> tuple[str | None, str | None, bool]:
            cls = fn = None
            depth_fn = 0
            p = par.get(node)
            while p is not None:
                if isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                    depth_fn += 1
                    if fn is None and not isinstance(p, ast.Lambda):
                        fn = p.name
                if isinstance(p, ast.ClassDef) and cls is None:
                    cls = p.name
                p = par.get(p)
            return cls, fn, depth_fn >= 2

        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "getattr" and len(n.args) >= 2:
                k = n.args[1]
                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                    if k.value in names:
                        cls, fn, clo = ctx(n)
                        sites[k.value].append({"site": f"{rel}:{n.lineno}", "form": "getattr_lit", "class": cls,
                                               "func": fn, "closure": clo, "recv": ast.unparse(n.args[0])})
                else:
                    dyn_getattr.append(f"{rel}:{n.lineno}")
                continue
            if not isinstance(n, ast.Attribute) or n.attr not in names:
                continue
            if not isinstance(n.ctx, ast.Load):
                continue
            # 書き: self.x[...] = / self.x[...] += / del
            p = par.get(n)
            if isinstance(p, ast.Subscript) and p.value is n and not isinstance(p.ctx, ast.Load):
                continue
            # 自己更新の右辺(self.x = self.x + ..)は数えるが印を付ける
            st = p
            while st is not None and not isinstance(st, ast.stmt):
                st = par.get(st)
            self_upd = False
            if isinstance(st, (ast.Assign, ast.AugAssign)):
                tg = st.targets[0] if isinstance(st, ast.Assign) else st.target
                while isinstance(tg, ast.Subscript):
                    tg = tg.value
                if isinstance(tg, ast.Attribute) and tg.attr == n.attr and ast.unparse(tg.value) == ast.unparse(n.value):
                    self_upd = True
            cls, fn, clo = ctx(n)
            recv = ast.unparse(n.value)
            if rel in GENERIC_FILES or (rel == "engine/resolve.py" and (fn or "").startswith("restore")):
                form = "generic"
            elif recv == "self":
                rows = attr_rows[n.attr]
                own = any(f"{rel}:{cls}" in owner_cls.get(r["owner"], set()) for r in rows)
                form = "self_owner" if own else "self_other"
            else:
                form = "attr_other"
            sites[n.attr].append({"site": f"{rel}:{n.lineno}", "form": form, "class": cls, "func": fn,
                                  "closure": clo, "recv": recv[:60], "self_update": self_upd})
    t_scan = time.perf_counter() - t1

    per_attr = {}
    for attr, rows in sorted(attr_rows.items()):
        ss = sites.get(attr, [])
        forms = collections.Counter(s["form"] for s in ss if not s.get("self_update"))
        per_attr[attr] = {
            "rows": [f'{r["row"]}:{r["path"]}({r["behavior"]}/{r["restore"]})' for r in rows],
            "classes_assigning_same_name": len(assigns.get(attr, ())),
            "forms": dict(forms),
            "closure_reads": sum(1 for s in ss if s["closure"] and not s.get("self_update")),
            "self_update_only_reads": sum(1 for s in ss if s.get("self_update")),
        }

    leaked = {}
    for path in LEAKED_10D:
        owner, attr = path.rsplit(".", 1)
        ss = [s for s in sites.get(attr, []) if not s.get("self_update")]
        leaked[path] = {
            "forms": dict(collections.Counter(s["form"] for s in ss)),
            "closure": sum(1 for s in ss if s["closure"]),
            "outside_owner": [s["site"] + " " + s["form"] + (" closure" if s["closure"] else "")
                              for s in ss if s["form"] in ("attr_other", "getattr_lit", "self_other")],
            "same_name_classes": len(assigns.get(attr, ())),
        }

    # 軸 1 が no/diag の属性の「持ち主の外の読み」(SoA の規則 2 を当てたときの違反の候補)
    nd_viol = {}
    for attr, rows in attr_rows.items():
        if all(r["behavior"] in (SL.NO, SL.DIAG) for r in rows):
            ss = [s for s in sites.get(attr, []) if s["form"] in ("attr_other", "getattr_lit", "self_other")
                  and not s.get("self_update")]
            if ss:
                nd_viol[attr] = [s["site"] + " " + s["form"] for s in ss][:8]
    # 軸 1 が behavior なのに読みが 0(generic を除く)
    beh_zero = []
    for attr, rows in attr_rows.items():
        if any(r["behavior"] == SL.BEHAVIOR for r in rows):
            ss = [s for s in sites.get(attr, []) if s["form"] != "generic" and not s.get("self_update")]
            if not ss:
                beh_zero.append(attr)
    form_total = collections.Counter()
    for attr in attr_rows:
        for s in sites.get(attr, []):
            if not s.get("self_update"):
                form_total[s["form"]] += 1
    collide = {a: len(assigns.get(a, ())) for a in attr_rows if len(assigns.get(a, ())) >= 2}
    out = {
        "schema": "10f/ext_readers_ast/1",
        "files": len(files),
        "parse_s": round(t_parse, 3),
        "scan_s": round(t_scan, 3),
        "n_external_attrs": len(attr_rows),
        "n_local_rows": len(local_rows),
        "local_rows": [r["path"] for r in local_rows],
        "read_sites_by_form": dict(form_total),
        "getattr_dynamic_sites": len(dyn_getattr),
        "attrs_with_same_name_in_2plus_classes": len(collide),
        "collision_examples": dict(sorted(collide.items(), key=lambda kv: -kv[1])[:20]),
        "no_diag_attrs_read_outside_owner": nd_viol,
        "behavior_attrs_with_zero_readers": sorted(beh_zero),
        "leaked_10d": leaked,
        "per_attr": per_attr,
    }
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: out[k] for k in ("files", "parse_s", "scan_s", "n_external_attrs", "n_local_rows",
                                          "read_sites_by_form", "getattr_dynamic_sites",
                                          "attrs_with_same_name_in_2plus_classes")}, ensure_ascii=False))
    print("no/diag read outside owner:", len(nd_viol))
    for k, v in nd_viol.items():
        print("  ", k, v[:3])
    print("behavior zero readers:", beh_zero)
    for k, v in leaked.items():
        print("LEAK", k, v)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
