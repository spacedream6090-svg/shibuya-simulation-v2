# -*- coding: utf-8 -*-
"""fix_pattern_rows_1102 — パターン台帳の D5′ と E5 の行を検証の側へ移す(11-02r/§1 #6・第341 段 2)。

決定: 指示書 11-02 返事その 2 §1 #6「車=D5′ は検証へ移し『今は入力と重なるので採点できない(burned)』と宣言。E5 は検証
(今は代打の出力が入るので既知の循環として宣言)」。〔検収 中-2・親の判断〕出典を分ける: E5 が検証で既知の循環であることは
ユーザーの決定(11-02r §1 #6)。外す段「配送の入荷が店の発注と配達員の行動になる段」は親の案(第342)=PENDING §2 の 3 の
``delivery_inbound`` と同じ段(ユーザーの決定の文には外す段が無い=宣言の ``basis`` は inferred)。

- 直すセル(列の名で引く=列の並びに依らない): D5′(§9 の表)の「用途」「区分」「burned」・E5(§1 階層 E の表)の「split案」
  「区分」「burned」。**数値は変えない**(照合値・出典・実数の列は触らない)。
- §5 集計の「較正に使ってよいのは … E5 …」の行の末尾に、E5 を検証へ移した注を 1 回だけ足す(訂正の伝播)。
- **冪等**: 直した後の文と同じなら何もしない(何度回しても同じ)。直す前の文でも直した後の文でもないセルに当たったら
  止める(並走の段が同じセルを変えた=手で突き合わせる)。
- 突き合わせ(``world.processes.circularity``): D5′ の ``burned`` は ``burned`` で始まる=例外の側。E5 の ``burned`` は
  「既知の循環」で始まる=警告の側(宣言は ``circularity.KNOWN_CIRCULARITIES``)。

使い方: ``python tools/ledger/fix_pattern_rows_1102.py [台帳の道筋]``(既定 ``docs/design/v2-pattern-ledger.md``)。
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT = ROOT / "docs" / "design" / "v2-pattern-ledger.md"

#: (行 ID, 列の名) → (直す前, 直した後)。〔検収 中-2〕前の版の「直した後」の文は ``SUPERSEDED`` に置き、直す前の文と同じに扱う。
CELLS: dict[tuple[str, str], tuple[str, str]] = {
    ("D5′", "用途"): ("断面交通の較正", "断面交通の検証(今は入力と重なるので採点できない=burned・11-02r §1 #6)"),
    ("D5′", "区分"): ("錨(較正→検証へ)", "錨(検証・今は burned=11-02r §1 #6)"),
    ("D5′", "burned"): (
        "—(較正→検証へ=回答 11-01 §8・§10-1)",
        "burned(今は入力と重なるので採点できない=駆動の値と照合の値が同じ道路交通センサス R3 の行・11-02r §1 #6・"
        "回答 11-01 §8・§10-1。断面の区間を分けたら内側の区間で採点する=§10-2 の自動車の行)"),
    ("E5", "split案"): ("**較正**", "holdout(検証へ=11-02r §1 #6)"),
    ("E5", "区分"): ("錨(要確認・較正に使用)", "錨(検証・既知の循環=11-02r §1 #6)"),
    ("E5", "burned"): (
        "要確認(較正に使用=split 欄・回答 11-01 §3 の疑い)",
        "既知の循環(補充の代打と納品の入力の出力が E5 に入る=contributes。11-02r §1 #6=E5 は検証・既知の循環(ユーザー"
        "決定)。外す段: 配送の入荷が店の発注と配達員の行動になる段=親の案(第342)=PENDING §2 の 3 の delivery_inbound と"
        "同じ段)"),
}
#: 前の版で書いた「直した後」の文(直す前と同じに扱う=冪等のまま書き換える)。
SUPERSEDED: dict[tuple[str, str], tuple[str, ...]] = {
    ("E5", "burned"): (
        "既知の循環(補充の代打と納品の入力の出力が E5 に入る=contributes・外す段: 配送の入荷が店の発注と配達員の行動に"
        "なる段=11-02r §1 #6)",),
}

#: §5 集計の行(頭の語 → 末尾に足す注)。
SUMMARY_HEAD = "- holdout非接触の誓約: 較正に使ってよいのはA5(NHK側)・E1(初期投入)・E5・F1-3のみ。"
SUMMARY_NOTE = "〔11-02r §1 #6〕E5 は検証へ移した(較正には使わない・今は既知の循環として宣言=§1 階層 E の E5 の行)。"


def _cells(line: str) -> list[str]:
    s = line.strip()
    return [c.strip() for c in s[1:-1].split("|")]


def transform(text: str) -> tuple[str, int]:
    """台帳の文を変換する。戻り値=(新しい文, 直したセルと行の数)。"""
    lines = text.split("\n")
    head: list[str] | None = None
    n = 0
    seen: set[tuple[str, str]] = set()
    for i, line in enumerate(lines):
        st = line.strip()
        if not (st.startswith("|") and st.endswith("|")):
            head = None
            if line.startswith(SUMMARY_HEAD) and SUMMARY_NOTE not in line:
                lines[i] = line.rstrip() + SUMMARY_NOTE
                n += 1
            continue
        cells = _cells(line)
        if cells and cells[0] in ("ID", "行"):
            head = cells
            continue
        if head is None or set(st) <= set("|-: "):
            continue
        rid = cells[0]
        want = {col: v for (r, col), v in CELLS.items() if r == rid}
        if not want:
            continue
        parts = line.split("|")  # parts[j + 1] がセル j(ほかのセルの空白は触らない)
        changed = False
        for col, (before, after) in want.items():
            if col not in head:
                raise ValueError(f"{rid}: 列 {col!r} の無い表")
            j = head.index(col)
            seen.add((rid, col))
            if cells[j] == after:
                continue
            if cells[j] != before and cells[j] not in SUPERSEDED.get((rid, col), ()):
                raise ValueError(f"{rid}/{col}: 直す前の文と違う(並走の段が変えた?): {cells[j][:40]!r}")
            parts[j + 1] = f" {after} "
            changed = True
            n += 1
        if changed:
            lines[i] = "|".join(parts)
    missing = set(CELLS) - seen
    if missing:
        raise ValueError(f"台帳に無いセル: {sorted(missing)}")
    return "\n".join(lines), n


def main(argv: list[str]) -> int:
    path = Path(argv[1]) if len(argv) > 1 else DEFAULT
    raw = path.read_bytes()
    if b"\r" in raw:
        raise SystemExit("台帳に CR がある(LF の版で回す)")
    new, n = transform(raw.decode("utf-8"))
    path.write_bytes(new.encode("utf-8"))
    print(f"直したセルと行 {n}(0=すでに直してある)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
