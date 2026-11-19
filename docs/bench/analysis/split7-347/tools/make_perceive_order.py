# -*- coding: utf-8 -*-
"""〔割る段 7 の G0・裁定 Q17〕副作用の順の固定の値 ``tests/perception/facts/perceive_order_frozen.json`` を作る台本。

試験 ``tests/perception/facts/test_perceive_order.py`` の記録の道(``record``)を 5 つの構成で回し、出来事の列と乱数の流れの
列を JSON に書く。何度回しても同じバイトを出す(鍵の並びを固定・1 出来事 1 行・絶対の道を書かない)。割る前の木で作り、
割る段 7 の G-S まで作り直さない(作り直す必要が出たら止まって報告=裁定 Q17)。

    python -B docs/bench/analysis/split7-347/tools/make_perceive_order.py [--out <道>] [--check]

``--out`` を省くと試験の隣の JSON に書く。``--check`` は書かずに、今の JSON と同じバイトかだけを見る(違えば終了コード 1)。
作業木の根で、``PYTHONPATH`` に作業木の ``src`` と根を入れて回す。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.perception.facts import test_perceive_order as PO  # noqa: E402

NOTE = ("割る段 7 の G0 で、割る前の木の Renderer.perceive の副作用の順を記録した固定の値(作る台本 "
        "docs/bench/analysis/split7-347/tools/make_perceive_order.py)。出来事=[種類, 中身, 乱数の流れの数, "
        "前の出来事から変わった計数]。G-S まで作り直さない(裁定 Q17)。")


def _dumps(x: object) -> str:
    return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def render_doc() -> str:
    lines = ["{", f'"schema":{_dumps(PO.SCHEMA)},', f'"note":{_dumps(NOTE)},', f'"n_agents":{PO.N_AGENTS},',
             f'"n_cells":{PO.N_CELLS},', f'"seed":{PO.SEED},', f'"ticks":{_dumps(list(PO.TICKS))},', '"configs":{']
    for ci, cfg in enumerate(PO.CONFIGS):
        got = PO.record(cfg)
        lines.append(f'{_dumps(cfg)}:{{"events":[')
        ev = got["events"]
        for k, e in enumerate(ev):
            lines.append(_dumps(e) + ("," if k < len(ev) - 1 else ""))
        lines.append('],"streams":[')
        st = got["streams"]
        for k, s in enumerate(st):
            lines.append(_dumps(s) + ("," if k < len(st) - 1 else ""))
        lines.append("]}" + ("," if ci < len(PO.CONFIGS) - 1 else ""))
    lines += ["}", "}"]
    text = "\n".join(lines) + "\n"
    json.loads(text)  # 正しい JSON か
    return text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(PO.FROZEN))
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    text = render_doc()
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    out = Path(a.out)
    if a.check:
        same = out.is_file() and out.read_bytes() == text.encode("utf-8")
        print(("同じ" if same else "違う") + f" sha256={sha}")
        return 0 if same else 1
    out.write_bytes(text.encode("utf-8"))
    print(f"書いた sha256={sha} 出来事={sum(len(PO.record(c)['events']) for c in PO.CONFIGS)} 行={text.count(chr(10))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
