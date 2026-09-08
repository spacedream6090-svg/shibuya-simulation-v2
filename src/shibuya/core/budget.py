"""予算宣言表(docs/design/v2-budget-declaration.md)の読み取り器。

正典は Markdown 側(人間が delta 方式で改版する)。本モジュールは**読むだけ**で、
数値をコード側に複製しない(CLAUDE.md §4「性能予算・バイト予算を宣言しテストでゲート」の
機械可読な入口)。

層契約: shibuya.core は他の shibuya パッケージを一切 import しない(標準ライブラリのみ)。

対象: 宣言表 §1〜§5 の表(見出し行 `| # | 項目 | 宣言値(仮) | 根拠 | 改訂条件 |`)。
§6(ハードウェアプロファイル)以降は別形式のため読まない。
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "BudgetRow",
    "BUDGET_MD_RELPATH",
    "ENV_BUDGET_MD",
    "load_budget_table",
    "budget_by_id",
    "parse_limit",
]

BUDGET_MD_RELPATH = "docs/design/v2-budget-declaration.md"
ENV_BUDGET_MD = "SHIBUYA_BUDGET_MD"

#: 表の見出し行のセル(この行の次の区切り行以降がデータ行)。
_HEADER_CELLS = ("#", "項目", "宣言値(仮)", "根拠", "改訂条件")

#: 節見出し `## 1. …` 〜 `## 5. …` のみを対象にし、`## 6.` で打ち切る。
_SECTION_RE = re.compile(r"^##\s+(\d+)\.\s*(.*)$")

#: 行 id。W=壁時計 / P=物理・エンジン / M=メモリ / L=LLM・GPU / S=ストレージ。
#: I=初期化予算(I1・2026-09-07 新設)は §4 の表に同居しているため許容する。
_ID_RE = re.compile(r"^[WPMLSI]\d+$")

#: 区切り行 `|---|---|…|`
_SEPARATOR_RE = re.compile(r"^\|[\s:|-]+\|$")


@dataclass(frozen=True)
class BudgetRow:
    """予算宣言表の1行。セルは Markdown の生文字列のまま(前後空白のみ除去)。

    Attributes:
        id: 行 id(例 ``M8``)。
        category: id の頭文字(``W``/``P``/``M``/``L``/``S``/``I``)。
        item: 「項目」セル。
        declared: 「宣言値(仮)」セル(生 Markdown)。
        rationale: 「根拠」セル。
        revision: 「改訂条件」セル(空のことがある: M2-M6)。
        section: 属する節見出し(例 ``3. メモリ(バイト)予算``)。
    """

    id: str
    category: str
    item: str
    declared: str
    rationale: str
    revision: str
    section: str


def _repo_root() -> Path:
    """このファイルから上へ辿り、宣言表を含むディレクトリを探す。"""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / BUDGET_MD_RELPATH).is_file():
            return parent
    raise FileNotFoundError(
        f"{BUDGET_MD_RELPATH} が見つからない({here} から上位を探索)。"
        f"環境変数 {ENV_BUDGET_MD} で明示指定できる。"
    )


def _default_path() -> Path:
    override = os.environ.get(ENV_BUDGET_MD)
    if override:
        return Path(override)
    return _repo_root() / BUDGET_MD_RELPATH


def _split_row(line: str) -> list[str]:
    """``| a | b |`` → ``['a', 'b']``。セル内 ``|`` は宣言表に存在しない(前提)。"""
    inner = line.strip()
    if not inner.startswith("|") or not inner.endswith("|"):
        return []
    return [cell.strip() for cell in inner[1:-1].split("|")]


def load_budget_table(path: str | Path | None = None) -> tuple[BudgetRow, ...]:
    r"""宣言表 §1〜§5 の全行を、Markdown 上の出現順で返す。

    Args:
        path: Markdown のパス。None なら環境変数 ``SHIBUYA_BUDGET_MD``、
            それも無ければリポジトリルートの ``docs/design/v2-budget-declaration.md``。

    Returns:
        ``BudgetRow`` のタプル。

    Raises:
        ValueError: id が ``^[WPMLSI]\d+$`` に一致しない / id が重複する /
            表のセル数が5でない / 1行も読めなかった。
        FileNotFoundError: 既定パスの探索に失敗した。
    """
    md_path = Path(path) if path is not None else _default_path()
    with md_path.open(encoding="utf-8", newline="") as fh:
        text = fh.read()

    rows: list[BudgetRow] = []
    section = ""
    in_table = False

    for lineno, raw in enumerate(text.split("\n"), start=1):
        line = raw.rstrip()

        m = _SECTION_RE.match(line)
        if m:
            if int(m.group(1)) >= 6:
                break  # §6 ハードウェアプロファイル以降は対象外
            section = line.lstrip("# ").strip()
            in_table = False
            continue

        if not section or not line.startswith("|"):
            in_table = False
            continue

        if _SEPARATOR_RE.match(line):
            continue

        cells = _split_row(line)
        if tuple(cells) == _HEADER_CELLS:
            in_table = True
            continue
        if not in_table:
            continue

        if len(cells) != len(_HEADER_CELLS):
            raise ValueError(
                f"{md_path}:{lineno}: 表のセル数が {len(cells)}"
                f"(期待 {len(_HEADER_CELLS)}): {line!r}"
            )

        row_id = cells[0]
        if not _ID_RE.match(row_id):
            raise ValueError(f"{md_path}:{lineno}: 不正な予算行 id: {row_id!r}")
        rows.append(
            BudgetRow(
                id=row_id,
                category=row_id[0],
                item=cells[1],
                declared=cells[2],
                rationale=cells[3],
                revision=cells[4],
                section=section,
            )
        )

    if not rows:
        raise ValueError(f"{md_path}: 予算行が1つも読めなかった")

    seen: set[str] = set()
    dupes: list[str] = []
    for row in rows:
        if row.id in seen:
            dupes.append(row.id)
        seen.add(row.id)
    if dupes:
        raise ValueError(f"{md_path}: 予算行 id が重複: {sorted(set(dupes))}")

    return tuple(rows)


def budget_by_id(rows: tuple[BudgetRow, ...]) -> dict[str, BudgetRow]:
    """``id`` → 行 の索引を作る。"""
    return {r.id: r for r in rows}


#: 単位の切れ目とみなす文字(best-effort)。``/`` ``／`` は単位内に残す
#: (「GB/シミュ日」「イベント/秒」「ms/フレーム」)。
_UNIT_STOP = "\\s、。・()()「」『』【】=＝+＋→*,,::;;"
_LIMIT_RE = re.compile(
    r"(?P<cmp>[≤≥<>])\s*"
    r"(?P<num>\d+(?:,\d{3})*(?:\.\d+)?)\s*"
    r"(?P<mult>万|億)?\s*"
    r"(?P<unit>[^" + _UNIT_STOP + r"]*)"
)

_MULTIPLIER: dict[str | None, float] = {None: 1.0, "万": 1e4, "億": 1e8}


def parse_limit(declared: str) -> tuple[float, str] | None:
    """宣言値セルから数値上限を **best-effort** で1つ取り出す。

    規則(単純・文書化済み。正典はあくまで Markdown の文面):

    1. 太字 ``**…**`` の中身を出現順に候補にし、最後にセル全体を候補に加える。
    2. 候補の中で最初に現れる「比較記号(``≤ ≥ < >``)+ 数値 + 任意の万/億 + 単位」を採る。
       数値は3桁区切り ``1,300`` を許す。比較記号を伴わない数値は採らない
       (delta 記述中の日付・型番を拾わないため)。
    3. 単位は区切り文字(空白・括弧・読点・中黒・鉤括弧など)の手前まで。``/`` ``%`` は含む。

    Args:
        declared: ``BudgetRow.declared``(生 Markdown)。

    Returns:
        ``(数値, 単位)``。例 ``**≤24GB**`` → ``(24.0, "GB")``、
        ``**≥10万イベント/秒**`` → ``(100000.0, "イベント/秒")``、
        ``**≤50ms/フレーム**`` → ``(50.0, "ms/フレーム")``。
        比較記号つきの数値が見つからなければ ``None``。

    Note:
        宣言表のセルは delta 方式で自然文が混ざる(旧値→新値の併記など)。
        本関数は表示・突き合わせの補助であり、CI ゲートの判定根拠にする場合は
        対象行の文面を人が確認すること。
    """
    candidates = [m.group(1) for m in re.finditer(r"\*\*(.+?)\*\*", declared, re.S)]
    candidates.append(declared)
    for cand in candidates:
        m = _LIMIT_RE.search(cand)
        if m is None:
            continue
        value = float(m.group("num").replace(",", "")) * _MULTIPLIER[m.group("mult")]
        return value, m.group("unit").strip()
    return None
