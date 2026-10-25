"""10b の記録: 状態台帳の表・AST の検査の結果(列ごとの読み手の数と許可の根拠)・台帳に載っていない属性の一覧。

使い方(リポのルートで): ``python ledger_record.py <出力の置き場>``

出すもの(どれも絶対パスを書かない。パスは ``src/shibuya`` からの相対):

- ``state_ledger_table.json``: 163 行(``engine.state_ledger.LEDGER`` をそのまま)。
- ``state_ledger_ast.json``: SoA 98 列の strict/loose の読み手の数と場所・許可(``ast_allow``)の根拠・
  解決できない ``field(変数)`` の場所と許可・``check`` の結果(空=合格)。
- ``ledger_uncovered_attrs.json``: 持ち主のクラスの属性の網羅の検査(``state_ledger_ast.coverage``)の結果と、
  明示の除外の一覧(分類と理由)。10b-2 からは未カバー 0 が合格。
"""

from __future__ import annotations

import ast
import dataclasses
import json
import sys
from pathlib import Path

from shibuya.engine import state_ledger as SL
from shibuya.engine import state_ledger_ast as SA

SRC = Path("src/shibuya")

OWNER_CLASSES = SL.OWNER_CLASSES


def _class_attrs(rel: str, cls: str) -> list[str]:
    tree = ast.parse((SRC / rel).read_text(encoding="utf-8"))
    c = next(n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == cls)
    out: list[str] = []
    for n in ast.walk(c):
        tg = [n.target] if isinstance(n, (ast.AnnAssign, ast.AugAssign)) else (
            n.targets if isinstance(n, ast.Assign) else [])
        for x in tg:
            for y in ast.walk(x):
                if (isinstance(y, ast.Attribute) and isinstance(y.value, ast.Name) and y.value.id == "self"
                        and y.attr not in out):
                    out.append(y.attr)
    for s in c.body:
        if isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name) and s.target.id not in out:
            out.append(s.target.id)
    return out


def main(argv: list[str]) -> int:
    dst = Path(argv[1])
    dst.mkdir(parents=True, exist_ok=True)
    rows = [dataclasses.asdict(r) for r in SL.LEDGER]
    (dst / "state_ledger_table.json").write_text(
        json.dumps({"ledger_version": SL.LEDGER_VERSION, "counts": SL.counts(), "rows": rows},
                   ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")

    res = SA.scan(SRC)
    cols = {}
    for r in SL.LEDGER:
        if not r.is_soa:
            continue
        cols[r.key] = {
            "behavior": r.behavior, "restore": r.restore, "dead": r.dead,
            "strict": len(res.strict.get(r.name, [])), "loose": len(res.loose.get(r.name, [])),
            "strict_sites": sorted({str(s) for s in res.strict.get(r.name, [])})[:30],
            "allow": [{"path": a.path, "contains": a.contains, "reason": a.reason} for a in r.ast_allow],
        }
    doc = {
        "files": res.files,
        "check": SA.check(res),
        "unresolved": [{"site": str(s), "allowed_by": (SA._allowed(s, SA.UNRESOLVED_ALLOW) or SL.AstAllow("", "", "")).reason}
                       for s in res.unresolved],
        "columns": cols,
    }
    (dst / "state_ledger_ast.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n",
                                               encoding="utf-8", newline="\n")

    uncovered, problems = SA.coverage(SRC)
    excl = [{"owner": x.owner, "kind": x.kind, "reason": x.reason, "attrs": list(x.attrs)} for x in SL.EXCLUDED]
    unc = {
        "note": "10b-2: 持ち主のクラスの属性は台帳の行か除外の一覧に必ず載る(uncovered と problems が空=合格)",
        "owner_classes": {k: {"file": v[0], "class": v[1], "n_attrs": len(SA.class_attrs(SRC, *v))}
                          for k, v in OWNER_CLASSES.items()},
        "uncovered": uncovered, "problems": problems,
        "excluded_entries": len(SL.EXCLUDED), "excluded_attrs": sum(len(x.attrs) for x in SL.EXCLUDED),
        "excluded_by_kind": {k: sum(len(x.attrs) for x in SL.EXCLUDED if x.kind == k) for k in SL.EXCLUDE_KINDS},
        "excluded": excl,
    }
    (dst / "ledger_uncovered_attrs.json").write_text(json.dumps(unc, ensure_ascii=False, indent=1) + chr(10),
                                                     encoding="utf-8", newline=chr(10))
    print("check", doc["check"], "unresolved", len(doc["unresolved"]),
          "uncovered", sum(len(v) for v in uncovered.values()), "problems", len(problems))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
