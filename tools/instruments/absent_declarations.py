# -*- coding: utf-8 -*-
"""absent_declarations — 「無いと宣言」の一覧を Markdown に出す計器(第340 段 2 の 6・回答 11-01 §10-3)。

決定: 回答 11-01 §10-3「口がまだ無い判断 13 件は、口ができるまで『無い』と宣言し、宣言の一覧を版上げごとに出す」・
指示書 11-01 段 2 の 6(一覧を版上げごとに出す計器に。納品=入力・発注=店の初期の予定として宣言)。

出すもの(``render``): §1 主体が居ない過程・§2 「無い」ではなく入力/初期の予定として宣言したもの・§3 口がまだ無い判断
(13 件+補足)・§4 入力の宣言(回答 11-01 §1 の型=代理している未構築の層・内生化の条件)・§5 件数と中身の指紋
(宣言の JSON の sha256 の先頭 16 桁=版上げの前後で比べる)。宣言の正は ``src/shibuya/world/processes/absent.py`` と
``inputs.py``(本計器は読むだけ・ランを回さない)。

使い方: ``python tools/instruments/absent_declarations.py [--out 出力.md]``(既定は標準出力)。

逐次ループ宣言: なし(宣言の数=数十)。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Iterable

REPO = Path(__file__).resolve().parents[2]
if str(REPO / "src") not in sys.path:  # pragma: no cover - 実行時の経路(宣言は world の側)
    sys.path.insert(0, str(REPO / "src"))

from shibuya.world.processes import absent as AB  # noqa: E402
from shibuya.world.processes import inputs as INP  # noqa: E402

__all__ = ["fingerprint", "render", "main"]


def _cell(s: str) -> str:
    return (s or "—").replace("|", "/").replace("\n", " ")


def _rows(nums: Iterable[int]) -> str:
    n = list(nums)
    return "・".join(f"#{x}" for x in n) if n else "§1-9"


def _stopped(a: object) -> str:
    return "止めた" if getattr(a, "engine_stopped") else "まだ動く"


def fingerprint() -> str:
    """宣言の中身の指紋(absent と inputs の as_dict を正規化した JSON の sha256 の先頭 16 桁)。"""
    payload = {
        "absent": [a.as_dict() for a in AB.ABSENCES],
        "inputs": [d.as_dict() for d in INP.INPUTS],
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def render() -> str:
    out: list[str] = [
        "# 「無いと宣言」の一覧(計器 tools/instruments/absent_declarations.py の出力)",
        "",
        "宣言の正: `src/shibuya/world/processes/absent.py`・`inputs.py`。文案は routing §3(`docs/reference/"
        "decision-routing-2026-11-01.md`)の写し。版上げごとに出して §5 の指紋を前の版と比べる。",
        "",
        "## §1 主体が居ない過程(無いと宣言)",
        "",
        "| 過程 | 行 | 宣言の文 | 外す段 | 段 | いまのエンジン | 止めた | 検証に残す錨 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for a in AB.NO_ACTOR:
        out.append(f"| {a.subject} | {_rows(a.routing_rows)} | {_cell(a.statement)} | {_cell(a.remove_at)} | {a.stage} | "
                   f"{_cell(a.engine_now)} | {_stopped(a)} | {_cell('・'.join(a.keeps_anchor))} |")
    out += [
        "",
        "## §2 「無い」ではなく入力・初期の予定として宣言したもの",
        "",
        "| 過程 | 宣言の形 | 宣言の文 | 外す段 | いまのエンジン |",
        "|---|---|---|---|---|",
    ]
    kinds = {"input": "入力", "initial_plan": "初期の予定"}
    for a in AB.REPLACED:
        out.append(f"| {a.subject} | {kinds[a.kind]} | {_cell(a.statement)} | {_cell(a.remove_at)} | "
                   f"{_cell(a.engine_now)} |")
    out += [
        "",
        "## §3 口がまだ無い判断(口ができるまで無い)と率の規則を外して無いにするもの(回答 11-01 §2)",
        "",
        "| 判断 | 行 | 宣言の文 | 外す段 | 段 | いまのエンジン | 止めた |",
        "|---|---|---|---|---|---|---|",
    ]
    for a in AB.NO_PORT + AB.RATE_REMOVED:
        out.append(f"| {a.subject} | {_rows(a.routing_rows)} | {_cell(a.statement)} | {_cell(a.remove_at)} | {a.stage} | "
                   f"{_cell(a.engine_now)} | {_stopped(a)} |")
    out += ["", "補足(回答 11-01 §10-3 の 13 件の外・routing §3-2 と §10-1 が同じ形で書くもの):", ""]
    for a in AB.NO_PORT_EXTRA:
        out.append(f"- {a.subject}({_rows(a.routing_rows)}): {a.statement}")
    out += [
        "",
        "## §4 入力の宣言(回答 11-01 §1 の型)",
        "",
        "| id | 変数 | 状態 | 出典 | 代理している未構築の層 | 内生化の条件 | 結ぶ過程 |",
        "|---|---|---|---|---|---|---|",
    ]
    st = {"filled": "埋めた", "fields_only": "欄だけ"}
    for d in INP.INPUTS:
        out.append(f"| `{d.id}` | {_cell(d.name)} | {st[d.status]} | {_cell(d.source)} | {_cell(d.proxies_layer)} | "
                   f"{_cell(d.endogenize_when)} | {_cell(d.world_process_id)} |")
    n_actor, n_rep, n_port, n_extra = len(AB.NO_ACTOR), len(AB.REPLACED), len(AB.NO_PORT), len(AB.NO_PORT_EXTRA)
    n_rate = len(AB.RATE_REMOVED)
    n_stop = sum(1 for a in AB.ABSENCES if a.engine_stopped)
    n_fill = sum(1 for d in INP.INPUTS if d.status == "filled")
    out += [
        "",
        "## §5 件数と指紋",
        "",
        f"- 主体が居ない過程 {n_actor}・入力/初期の予定 {n_rep}・口が無い判断 {n_port}・率を外すもの {n_rate}"
        f"(+補足 {n_extra})=宣言 {len(AB.ABSENCES)}",
        f"- エンジンがもう動かしていない(止めた=循環の検査の例外になる){n_stop}・まだ動く {len(AB.ABSENCES) - n_stop}",
        f"- 入力の宣言 {len(INP.INPUTS)}(埋めた {n_fill}・欄だけ {len(INP.INPUTS) - n_fill})",
        f"- 指紋 `{fingerprint()}`",
        "",
    ]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--out", type=Path, default=None, help="出力の Markdown(既定は標準出力)")
    a = ap.parse_args(argv)
    text = render()
    if a.out is None:
        sys.stdout.write(text)
    else:
        a.out.write_bytes(text.encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
