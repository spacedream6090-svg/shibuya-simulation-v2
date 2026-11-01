# -*- coding: utf-8 -*-
"""add_pattern_columns_1101 — パターン台帳に「採点する系」と ``burned`` の 2 列を足す(第340 段 2 の 2)。

決定: 回答 11-01 §3(パターン台帳の各行に「採点する系」、較正に使った錨に ``burned``)・§4(初期化に使った法則は
``burned``)・指示書 11-01 段 2 の 2。

- 足す表: §1 階層 A〜G・§9(先頭の列が ``ID``/``行``)と §10-1・§10-2(先頭の列が ``データ``)。**既存のセルは変えない**
  (行の末尾に 2 つのセルを足すだけ)。§10-3 は表でない(箇条)ので列を足せない=記録の README に書いた。
- **冪等**: 見出しに「採点する系」がすでにある表は触らない(何度回しても同じ)。本体の版の上で回せる(並走の段との
  rebase のため)。
- 「採点する系」: §1・§9 の行は行の ID 自身と照合値の出典の系(``SOURCES``=``data:<id>``・分かる行だけ)を「・」で並べる
  (破棄行は「—(破棄)」)。§10-1 の行は「何の検証か」の欄の括弧の中
  (括弧が無ければ欄の文・「全体」で始まる欄はそのまま)。§10-2 の行は手で書いた(``_S10_2``)。
- ``burned`` の語: ``burned(…)``=較正・初期化に使った=検証から外す/``外す(…)``=一時的に検証から外す/
  ``要確認(…)``=印だけ(突き合わせでは外さない)/``—``=外さない。突き合わせ(``world.processes.circularity``)は
  ``burned`` と ``外す`` で始まる行だけを例外にする。

使い方: ``python tools/ledger/add_pattern_columns_1101.py [台帳の道筋]``(既定 ``docs/design/v2-pattern-ledger.md``)。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT = ROOT / "docs" / "design" / "v2-pattern-ledger.md"
COL_SCORING = "採点する系"
COL_BURNED = "burned"

#: 行 ID → burned の値(書いていない行は「—」)。指示書 段 2 の 2 と発注の指定=F1〜F3(burned)・D5′(外さない側)・
#: W3(体の式ができるまで外す=回答 11-01 §3)・E5(要確認のまま印だけ)。それ以外の「要確認」は行の split・用途・
#: 区分の欄が較正・生成・初期化に使ったと書いている行(実装役が読んで付けた印=突き合わせでは外さない)。
BURNED: dict[str, str] = {
    "F1": "burned(較正=split 欄・初期化=回答 11-01 §4)",
    "F2": "burned(較正=split 欄・初期化=回答 11-01 §4)",
    "F3": "burned(較正=split 欄・初期化=回答 11-01 §4)",
    "W3": "外す(W3 は錨に残す・体の式ができるまで検証から外す=回答 11-01 §3)",
    "D11′": "burned(生成に使用=用途欄・初期化=回答 11-01 §4)",
    "D5′": "—(較正→検証へ=回答 11-01 §8・§10-1)",
    "E5": "要確認(較正に使用=split 欄・回答 11-01 §3 の疑い)",
    "A5": "要確認(NHK 2020 の側は較正=split 欄)",
    "E1": "要確認(較正→holdout の二相=split 欄)",
    "D12′": "要確認(W10 の較正=用途欄)",
    "AD2": "要確認(事前分布に使用=区分欄)",
    "W1": "要確認(帯はモデルの定数から作った自己整合=用途欄)",
    "W6": "要確認(U10 の生成用か=区分欄)",
}

#: 行 ID → 照合値の出典の系(``data:<id>``=drives_from と同じ語。〔検収 中-1〕「採点する系」に行の ID と併記する)。
#: D5 は D5′ が一次化(§9 D5′ の行)なので同じ調査。A4〜A7 は社会生活基本調査(A5 は NHK も)。D6・D7・D11′ は東京 PT 第 6 回
#: (2018)。D12′ は都環境局 R5 の沿道騒音(W10 の残差の照合に使用)。D1′・D4′ は渋谷区オープンデータの KDDI。
SOURCES: dict[str, str] = {
    "A4": "data:ssb", "A5": "data:ssb・data:nhk_time_use", "A6": "data:ssb", "A7": "data:ssb",
    "D5": "data:road_census_r3", "D5′": "data:road_census_r3", "D12′": "data:tokyo_noise_r5",
    "D6": "data:pt2018", "D7": "data:pt2018", "D11′": "data:pt2018",
    "D1′": "data:kddi_la", "D4′": "data:kddi_la",
}

#: §10-2 の行(先頭のセルの頭の語 → (採点する系, burned))。
_S10_2: tuple[tuple[str, str, str], ...] = (
    ("パーソントリップ調査", "検証に残す部分の欄(c-2 の 0240〜0243 の集中量・b-4)", "一部 burned(構築・較正に使う部分=2 列目)"),
    ("自動車の起終点調査", "D5′(内側の区間)", "一部 burned(外側の区間=較正)"),
    ("社会生活基本調査", "検証に残す部分の欄(使っていない表)", "一部 burned(使っている表=2 列目)"),
    ("人流のデータ", "D1′・D4′・K5", "—(構築に使わない=2 列目)"),
    ("train-media.net", "未決", "未決(構築か検証かを先に決める=2 列目)"),
)

_SEP = re.compile(r"^\|[\s:|-]+\|$")
_STRIKE = re.compile(r"^~~.+~~$")


def _cells(line: str) -> list[str]:
    s = line.strip()
    return [c.strip() for c in s[1:-1].split("|")]


def _append(line: str, a: str, b: str) -> str:
    return line.rstrip() + f" {a} | {b} |"


def _s10_1_scoring(what: str) -> str:
    if what.startswith("全体"):
        return what
    m = re.findall(r"[((]([^()()]+)[))]", what)
    return m[0] if m else what


def transform(text: str) -> tuple[str, int]:
    """台帳の文を変換する。戻り値=(新しい文, 列を足した表の数)。"""
    lines = text.split("\n")
    out: list[str] = []
    section = ""
    i = 0
    n_tables = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("## ") or line.startswith("### "):
            section = line
        is_row = line.strip().startswith("|") and line.strip().endswith("|")
        if not is_row:
            out.append(line)
            i += 1
            continue
        head = _cells(line)
        kind = ""
        if head[0] in ("ID", "行") and not section.startswith("## 2."):
            kind = "id"
        elif head[0] == "データ" and ("10-1" in section or "10-2" in section):
            kind = "s10_1" if "10-1" in section else "s10_2"
        if not kind or COL_SCORING in head:
            # 表の頭でない・足す表でない・すでに足した表=そのまま(表の終わりまで写す)
            while i < len(lines) and lines[i].strip().startswith("|"):
                out.append(lines[i])
                i += 1
            continue
        n_tables += 1
        out.append(_append(line, COL_SCORING, COL_BURNED))
        i += 1
        while i < len(lines) and lines[i].strip().startswith("|"):
            row = lines[i]
            cells = _cells(row)
            if _SEP.match(row.strip()):
                out.append(row.rstrip() + " --- | --- |")
            elif kind == "id":
                rid = cells[0]
                if _STRIKE.match(rid):
                    out.append(_append(row, "—(破棄)", "—(破棄)"))
                else:
                    scoring = f"{rid}・{SOURCES[rid]}" if rid in SOURCES else rid
                    out.append(_append(row, scoring, BURNED.get(rid, "—")))
            elif kind == "s10_1":
                out.append(_append(row, _s10_1_scoring(cells[1]), "—(検証専用)"))
            else:
                hit = [(s, b) for k, s, b in _S10_2 if cells[0].startswith(k)]
                if len(hit) != 1:
                    raise ValueError(f"§10-2 の行が表に無い: {cells[0][:30]!r}")
                out.append(_append(row, hit[0][0], hit[0][1]))
            i += 1
    return "\n".join(out), n_tables


def main(argv: list[str]) -> int:
    path = Path(argv[1]) if len(argv) > 1 else DEFAULT
    raw = path.read_bytes()
    if b"\r" in raw:
        raise SystemExit("台帳に CR がある(LF の版で回す)")
    new, n = transform(raw.decode("utf-8"))
    path.write_bytes(new.encode("utf-8"))
    print(f"列を足した表 {n}(0=すでに足してある)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
