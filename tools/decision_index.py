#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""決定の ID の索引を自動生成する(回答 10-13b §1 1-7 案 B・CLAUDE.md §6)。

決定の正は原文(指示書・回答)。計画・PENDING・STATUS・devlog・IMPLEMENTED には中身を写さず
``<日付の接頭>/<ID>`` のリンクだけを書く。本道具は原文の見出しと ID(``CA1``・``K3``・``S1``・``§4-2`` など)を
拾って ``docs/design/decision-id-index.md`` に一覧にし、同じ ID が複数の原文にある衝突(``C1`` など)を別節に出す。

  python tools/decision_index.py            # 生成(上書き)
  python tools/decision_index.py --check    # 生成物が最新かを確かめる(違えば exit 1)

拾い方は機械的(見出し・太字の ID・表の先頭の欄・箇条書きの頭)。意味は原文で読む。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "docs" / "design"
OUT = DESIGN / "decision-id-index.md"

#: 原文(決定の正)と接頭。接頭は「月-日」+区別の 1 字(p=計画への回答・b=同日 2 本目・d=判断待ちへの決定)。
DOCS: tuple[tuple[str, str, str], ...] = (
    ("09-24d", "v2-decisions-for-user-2026-09-24.md", "判断待ちへの決定 09-24"),
    ("09-25", "v2-wallbounce-decisions-2026-09-25.md", "壁打ちの決定 09-25"),
    ("09-29d", "v2-decisions-for-user-2026-09-29.md", "判断待ちへの決定 09-29"),
    ("09-30", "v2-wallbounce-decisions-2026-09-30.md", "壁打ちの決定 09-30"),
    ("10-03", "v2-wallbounce-decisions-2026-10-03.md", "指示書 10-03"),
    ("10-06", "v2-wallbounce-decisions-2026-10-06.md", "指示書 10-06"),
    ("10-12", "v2-wallbounce-decisions-2026-10-12.md", "指示書 10-12"),
    ("10-12p", "v2-plan-answers-2026-10-12.md", "実装の計画への回答 10-12"),
    ("10-12b", "v2-answers-2026-10-12b.md", "回答 10-12b"),
    ("10-13", "v2-answers-2026-10-13.md", "回答 10-13(第330 への答え)"),
    ("10-13b", "v2-answers-2026-10-13b.md", "回答 10-13b(第332 への答え・自律運転の規則)"),
    ("10-25", "v2-answers-2026-10-25.md", "回答 10-25(第338 への答え・壁打ち 10-23〜25 の決定・仮決定・研究の題)"),
    ("11-01", "v2-answers-2026-11-01.md", "回答 11-01(A1=知見の切り分けの原則・判断の置き場 112 件・判断モデル・検証の規模)"),
    ("11-01p", "prompt-2026-11-01.md", "指示書 11-01(実装の限定の再開=段 0〜3・5・研究 R-I〜R-K・D4 の材料)"),
    ("11-01g", "prompt-2026-11-01-5070.md", "指示書 11-01 5070(検証の準備=許可・安全の規則・完了の条件)"),
    ("11-02", "prompt-2026-11-02-research.md", "指示書 11-02 研究と取得(第 340 への返事 その 1=点群 raw・D1b・駐輪場・天神・R-129・presence)"),
    ("11-02r", "prompt-2026-11-02-reply2.md", "指示書 11-02 返事その 2(11 件の判断・段 4 の差し替え=v3 事象駆動の核・A2 組織の判断・段の優先)"),
    ("11-03", "prompt-2026-11-03-reply3.md", "指示書 11-03 返事その 3(答申の訂正・挙動の棚卸し 164 件の仕分け・欠陥の修正・v3 の仮決定 題 1〜2・v3-0a・計測・研究 6 本)"),
    ("11-04", "prompt-2026-11-04-reply4.md", "指示書 11-04 返事その 4(取得を断られたら名乗りを変えない規則・v3-0a 案 A・仕分けの区分の直し・題 9-1 心のモジュールの内外の仮決定・研究 2 本)"),
    ("11-04b", "prompt-2026-11-04-reply4b.md", "指示書 11-04 返事その 4 の追補(題 9-1 の追加・題 9-4 L4 の予算・題 9-2 の方針・研究 3 本・第 2 世代の費用の訂正)"),
    ("11-04c", "prompt-2026-11-04-reply5.md", "指示書 11-04 返事その 5(A2-1・T1・物の実体化・第 344 の判断への答え=仕分けの採用と経路の範囲と封印の層・PLATEAU の応募)"),
    ("11-05", "prompt-2026-11-05-reply6.md", "指示書 11-05 返事その 6(CLAUDE.md §2-2 の改訂・題 9-3a〜d・9-5・6・10 の仮決定・整理の段・仕様書 v0・包みの案・研究 3 本・順)"),
)

_HEAD = re.compile(r"^(#{1,4})\s+(.*)$")
_HEAD_NUM = re.compile(r"^(?:§\s*)?(\d+(?:-\d+)*)[\.\s]")
_ID = re.compile(r"(?<![A-Za-z0-9/§])(§?[A-Z]{1,3}-?\d{1,3}[a-z]?(?:-\d{1,2})?)(?![A-Za-z0-9])")
_BOLD_ID = re.compile(r"\*\*(§?[A-Z]{1,3}-?\d{1,3}[a-z]?(?:-\d{1,2})?)\*\*")
_CELL_ID = re.compile(r"^\|\s*\**(§?[A-Z]{1,3}-?\d{1,3}[a-z]?(?:-\d{1,2})?)\**\s*\|")
_BULLET_ID = re.compile(r"^\s*(?:[-*]|\d+\.)\s+\**(§?[A-Z]{1,3}-?\d{1,3}[a-z]?(?:-\d{1,2})?)\**[\s:：]")
_SEC_ID = re.compile(r"^\|\s*\**(\d+-\d+(?:-\d+)?)\b")  # 回答の表の「1-2 比べ方」のような節の番号(先頭の欄の頭)


def _clean(text: str, n: int = 60) -> str:
    t = re.sub(r"[`*]", "", text).strip()
    t = t.replace("|", "／")
    return t if len(t) <= n else t[: n - 1] + "…"


def scan(path: Path) -> tuple[list[tuple[int, str, str]], list[tuple[str, int, str]]]:
    """戻り値 = (見出し [(行, 番号, 文), …], ID [(ID, 行, 文の先頭), …])。"""
    heads: list[tuple[int, str, str]] = []
    ids: list[tuple[str, int, str]] = []
    seen: set[tuple[str, int]] = set()
    text = path.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
    in_code = False
    for i, line in enumerate(text.split("\n"), start=1):
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = _HEAD.match(line)
        if m:
            body = m.group(2).strip()
            mn = _HEAD_NUM.match(body)
            num = mn.group(1) if mn else ""
            heads.append((i, num, _clean(body, 80)))
            continue
        found: list[str] = []
        mc = _CELL_ID.match(line)
        if mc:
            found.append(mc.group(1))
        ms = _SEC_ID.match(line)
        if ms:
            found.append("§" + ms.group(1))
        mb = _BULLET_ID.match(line)
        if mb:
            found.append(mb.group(1))
        found += _BOLD_ID.findall(line)
        for tok in found:
            key = (tok, i)
            if key in seen:
                continue
            seen.add(key)
            ids.append((tok, i, _clean(line, 70)))
    return heads, ids


def render() -> str:
    out: list[str] = []
    out.append("# 決定の ID の索引(自動生成・手で編集しない)")
    out.append("")
    out.append("`python tools/decision_index.py` が原文(指示書・回答)の見出しと ID を拾って作る(回答 10-13b §1 1-7 案 B・CLAUDE.md §6)。")
    out.append("引き方は `<接頭>/<ID>`(例 `10-12/CA1`・`10-13b/§0-2`・`10-12p/2-0`)。同じ ID が複数の原文にあるものは末尾の「衝突」に出す=必ず接頭つきで引く。中身は原文で読む(本書には写さない)。")
    out.append("")
    out.append("| 接頭 | 原文 | 見出し | ID |")
    out.append("|---|---|---|---|")
    per_doc: list[tuple[str, str, str, list, list]] = []
    for prefix, fname, label in DOCS:
        p = DESIGN / fname
        if not p.exists():
            per_doc.append((prefix, fname, label, [], []))
            out.append(f"| `{prefix}` | {label}(**無い**: {fname}) | — | — |")
            continue
        heads, ids = scan(p)
        per_doc.append((prefix, fname, label, heads, ids))
        out.append(f"| `{prefix}` | [{label}]({fname}) | {len(heads)} | {len(ids)} |")
    out.append("")
    collisions: dict[str, list[str]] = {}
    for prefix, fname, label, heads, ids in per_doc:
        if not heads and not ids:
            continue
        out.append(f"## `{prefix}` {label}([{fname}]({fname}))")
        out.append("")
        out.append("| ID | 行 | 見出し・文の先頭 |")
        out.append("|---|---|---|")
        for line, num, body in heads:
            tag = f"`{prefix}/§{num}`" if num else "(番号なし)"
            out.append(f"| {tag} | {line} | {body} |")
        for tok, line, body in ids:
            out.append(f"| `{prefix}/{tok}` | {line} | {body} |")
            collisions.setdefault(tok, [])
            if prefix not in collisions[tok]:
                collisions[tok].append(prefix)
        out.append("")
    dup = {k: v for k, v in collisions.items() if len(v) >= 2}
    out.append("## 衝突(同じ ID が複数の原文にある=接頭なしで引かない)")
    out.append("")
    if not dup:
        out.append("なし")
    else:
        out.append("| ID | 原文(接頭) |")
        out.append("|---|---|")
        for tok in sorted(dup, key=lambda k: (len(k), k)):
            out.append(f"| `{tok}` | {', '.join('`' + p + '`' for p in dup[tok])} |")
    out.append("")
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="生成物が最新かを確かめるだけ(違えば exit 1)")
    args = ap.parse_args(argv)
    text = render()
    if args.check:
        cur = OUT.read_bytes().replace(b"\r\n", b"\n").decode("utf-8") if OUT.exists() else ""
        if cur != text:
            print(f"[decision_index] {OUT.relative_to(ROOT).as_posix()} が古い。`python tools/decision_index.py` で作り直す", file=sys.stderr)
            return 1
        print("[decision_index] 最新")
        return 0
    OUT.write_bytes(text.encode("utf-8"))
    n_lines = text.count("\n")
    print(f"[decision_index] wrote {OUT.relative_to(ROOT).as_posix()} ({n_lines} 行)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
