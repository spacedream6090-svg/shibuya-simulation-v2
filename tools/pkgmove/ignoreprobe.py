# -*- coding: utf-8 -*-
"""効いている例外(ignore)の確かめ(検収 中-1・親の裁定 2026-11-16)。木を変えずに、メモリの中で回す。

    python tools/pkgmove/ignoreprobe.py <木の根> <契約の JSON か ->   # 結果の JSON を標準出力へ(- は標準入力から読む)

- 木の ``src`` の包みから import のグラフを 1 回だけ作り(grimp・キャッシュを書かない)、渡した契約(pyproject の
  ``[[tool.importlinter.contracts]]`` の形)を import-linter の契約のクラスで回す。lint-imports の CLI と同じクラス・同じ設定の読み方。
- 基準: 全部の契約が kept か。
- 各契約の例外の行を 1 本ずつ外して、その契約だけを回す。外すと broken になる行を「効いている」とする(延べの行)。辺は、どれかの
  契約で効いていれば「効いている」(重なりを除く)。
- 効いていない行を全部まとめて外しても全契約が kept か(``jointly_kept``)。2 本のどちらか 1 本で足りる連なりのように、1 本ずつ
  では見えない例外があれば False になる。
- 子のプロセスで回す(``cli.py contracts`` が呼ぶ)。木の ``src`` を ``sys.path`` の先頭に置き、読んだ包みが木のものかを確かめる。
"""
from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path

if __name__ == "__main__":  # 道具の置き場(tools/pkgmove)の名が import-linter の名を隠さないように外す
    _here = os.path.normcase(os.path.abspath(os.path.dirname(__file__)))
    sys.path[:] = [p for p in sys.path if os.path.normcase(os.path.abspath(p or os.curdir)) != _here]


def probe(root: Path, root_package: str, session: dict, contracts: list[dict]) -> dict:
    sys.path.insert(0, str(Path(root) / "src"))
    import importlib.util

    import grimp
    from importlinter import configuration
    from importlinter.contracts.forbidden import ForbiddenContract
    from importlinter.contracts.layers import LayersContract
    from importlinter.contracts.protected import ProtectedContract

    spec = importlib.util.find_spec(root_package)
    origin = Path(spec.origin).resolve() if spec and spec.origin else None
    if origin is None or Path(root).resolve() / "src" not in origin.parents:
        raise RuntimeError(f"読んだ {root_package} が木の src でない: {origin}")
    configuration.configure()
    cls = {"forbidden": ForbiddenContract, "layers": LayersContract, "protected": ProtectedContract}
    sess = {k: (str(v) if isinstance(v, bool) else v) for k, v in session.items()}
    sess["root_packages"] = [root_package]
    graph = grimp.build_graph(root_package, include_external_packages=str(session.get("include_external_packages"))
                              in ("True", "true"), exclude_type_checking_imports=str(
                                  session.get("exclude_type_checking_imports")) in ("True", "true"), cache_dir=None)

    def kept(opts: dict) -> bool:
        o = {k: (str(v) if isinstance(v, bool) else v) for k, v in opts.items()}
        if not o.get("ignore_imports"):
            o.pop("ignore_imports", None)
        c = cls[o["type"]](name=o["name"], session_options=sess, contract_options=o)
        return c.check(copy.deepcopy(graph), verbose=False).kept

    base = {c["name"]: kept(c) for c in contracts}
    lines: list[dict] = []
    for c in contracts:
        ig = list(c.get("ignore_imports", []))
        for x in ig:
            lines.append({"contract": c["name"], "edge": x,
                          "effective": not kept({**c, "ignore_imports": [y for y in ig if y != x]})})
    eff_edges = sorted({d["edge"] for d in lines if d["effective"]})
    all_edges = sorted({d["edge"] for d in lines})
    jointly = all(kept({**c, "ignore_imports": [y for y in c.get("ignore_imports", [])
                                                if any(d["contract"] == c["name"] and d["edge"] == y and d["effective"]
                                                       for d in lines)]})
                  for c in contracts)
    return {"base_kept": all(base.values()), "broken": sorted(k for k, v in base.items() if not v),
            "lines": len(lines), "effective_lines": sum(d["effective"] for d in lines),
            "unique": len(all_edges), "effective_unique": len(eff_edges),
            "not_effective": sorted(set(all_edges) - set(eff_edges)), "jointly_kept": jointly, "detail": lines}


def main(argv: list[str]) -> int:
    root = Path(argv[1])
    raw = sys.stdin.buffer.read().decode("utf-8") if argv[2] == "-" else Path(argv[2]).read_text(encoding="utf-8")
    doc = json.loads(raw)
    out = probe(root, doc["root_package"], doc.get("session", {}), doc["contracts"])
    sys.stdout.write(json.dumps(out, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
