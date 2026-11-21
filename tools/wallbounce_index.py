"""壁打ちの記録の索引を作る(11-22 §3-1 の 3)。1 行 1 決定(ID・題・日付・状態・行の範囲)。

記録(``docs/reference/wallbounce-record-*.md``)は長い(1 本で 250 KB を超える)。決定を引くたびに全文を読まずに
済むよう、見出しの行だけを拾って ``docs/reference/wallbounce-index.md`` を作る。読む側は、この索引で行の範囲を
確かめてから、その範囲だけを開く。

- 拾うのは見出しの行だけ(``## `` と ``### ``)。本文の中身は索引に写さない。
- ``### 2-88 題(11-22・記録と決定)`` の形は、ID=``2-88``・題・最後の括弧の中の「日付」と「状態」に分ける。
  括弧が無い・日付で始まらない見出しは、題にそのまま置き、日付と状態は空にする(推し量らない)。
- 行の範囲は、その見出しの行から、次の見出し(同じ深さか浅いもの)の前の行まで。
- 新しい記録ができたら ``RECORDS`` に 1 行足して回す。``--check`` は、書かずに「最新か」だけを見る(違えば exit 1)。

手で編集しない(作り直すと消える)。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_REL = "docs/reference/wallbounce-index.md"

# (ファイル, 記録の名, 状態)。保管用=もう足さない記録。新しい記録は下に足す。
RECORDS: tuple[tuple[str, str, str], ...] = (
    ("docs/reference/wallbounce-record-2026-11-02_05.md", "記録 1(2026-11-02〜11-22・2-1〜2-88)", "保管用(11-22 §0。これ以上足さない)"),
)

_HEAD = re.compile(r"^(#{2,3})\s+(.*\S)\s*$")
_ID = re.compile(r"^(\d+(?:-\d+)*)[\.\s]\s*(.*)$")
# 最後の括弧(全角)。中が「日付」で始まるものだけを日付と状態に分ける
_TAIL = re.compile(r"^(.*?)\s*[\x28\uff08]([^\x28\x29\uff08\uff09]*)[\x29\uff09]\s*$")  # 最後の括弧(半角 x28/x29 と全角 uff08/uff09 のどちらでも)
_DATE = re.compile(r"^(\d{1,2}-\d{1,2}(?:[〜~、・]\d{1,2}(?:-\d{1,2})?)*)(?:[・\s]+(.*))?$")


def split_heading(text: str) -> tuple[str, str, str, str]:
    """見出しの文字列 → (ID, 題, 日付, 状態)。分けられない所は空のまま(推し量らない)。"""
    ident, rest = "", text
    m = _ID.match(text)
    if m:
        ident, rest = m.group(1), m.group(2)
    title, date, state = rest, "", ""
    t = _TAIL.match(rest)
    if t:
        d = _DATE.match(t.group(2).strip())
        if d:
            title, date, state = t.group(1), d.group(1), (d.group(2) or "").strip()
    return ident, title.strip(), date, state


def rows_of(text: str) -> list[dict[str, object]]:
    """記録の本文 → 見出しごとの行(深さ・ID・題・日付・状態・始まりと終わりの行)。コードの囲みの中は拾わない。"""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    heads: list[tuple[int, int, str]] = []
    fenced = False
    for i, line in enumerate(lines, start=1):
        if line.startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        m = _HEAD.match(line)
        if m:
            heads.append((i, len(m.group(1)), m.group(2)))
    out: list[dict[str, object]] = []
    for k, (start, depth, head) in enumerate(heads):
        end = len(lines)
        for nxt_start, nxt_depth, _ in heads[k + 1:]:
            if nxt_depth <= depth:
                end = nxt_start - 1
                break
        while end > start and lines[end - 1].strip() in ("", "---"):
            end -= 1
        ident, title, date, state = split_heading(head)
        out.append({"depth": depth, "id": ident, "title": title, "date": date, "state": state, "start": start, "end": end})
    return out


def _cell(s: object) -> str:
    return str(s).replace("|", "/").replace("\n", " ")


def render(root: Path = ROOT) -> str:
    parts = [
        "# 壁打ちの記録の索引(自動生成・手で編集しない)",
        "",
        "`python tools/wallbounce_index.py` が作る(11-22 §3-1 の 3)。決定の正は記録の本文。ここは、どの決定が記録の",
        "何行目にあるかの索引だけを持つ。記録を読むときは、この表で行の範囲を確かめて、その範囲だけを開く(全文を読まない)。",
        "",
        "- 「日付」「状態」は、見出しの最後の括弧の中をそのまま分けたもの(空は、見出しに書かれていない)。",
        "- 行の範囲は、見出しの行から次の見出しの前まで。",
        "",
    ]
    for rel, name, status in RECORDS:
        text = (root / rel).read_bytes().decode("utf-8-sig")
        rows = rows_of(text)
        n_lines = len(text.replace("\r\n", "\n").split("\n")) - (1 if text.endswith("\n") else 0)
        decisions = [r for r in rows if r["depth"] == 3]
        parts += [
            f"## {name}",
            "",
            f"- ファイル: [{Path(rel).name}]({Path(rel).name})({n_lines} 行)",
            f"- 状態: {status}",
            f"- 決定の見出し {len(decisions)} 本・節の見出し {len(rows) - len(decisions)} 本",
            "",
            "| ID | 題 | 日付 | 状態 | 行 |",
            "|---|---|---|---|---|",
        ]
        for r in rows:
            ident = f"`{r['id']}`" if r["id"] else ""
            title = _cell(r["title"])
            if r["depth"] == 2:
                ident, title = (f"**§{r['id']}**" if r["id"] else "**節**"), f"**{title}**"
            parts.append(f"| {ident} | {title} | {_cell(r['date'])} | {_cell(r['state'])} | {r['start']}〜{r['end']} |")
        parts.append("")
    return "\n".join(parts).rstrip("\n") + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--check", action="store_true", help="書かずに、索引が最新かだけを見る(違えば exit 1)")
    ap.add_argument("--root", type=Path, default=ROOT, help="リポの根(試験用)")
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")
    text = render(args.root)
    out = args.root / OUT_REL
    cur = out.read_bytes().decode("utf-8").replace("\r\n", "\n") if out.is_file() else None
    if args.check:
        if cur != text:
            print(f"[wallbounce_index] 索引が古い。`python tools/wallbounce_index.py` で作り直す({OUT_REL})", file=sys.stderr)
            return 1
        print("[wallbounce_index] 最新")
        return 0
    out.write_bytes(text.encode("utf-8"))
    print(f"[wallbounce_index] wrote {OUT_REL}({text.count(chr(10))} 行)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
