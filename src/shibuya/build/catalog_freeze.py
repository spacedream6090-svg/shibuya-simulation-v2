"""世界カタログ(docs/design/v2-world-catalog.md)の凍結器。

世界被覆指標の**分母**は凍結された Markdown の表そのもの。本スクリプトはその表を
そのまま抜き出して SHA を取り、実行時に読める JSON へ落とす(オフライン build 工程)。

凍結 SHA の規則(v0.2 の凍結時と**同一**でなければならない)::

    tbl = re.search(r"\\| # \\| 型 \\|.*?\\n\\n", md_text, re.S).group(0)
    sha16 = hashlib.sha256(tbl.encode("utf-8")).hexdigest()[:16]

すなわち「見出し行から最初の空行まで(空行の改行を含む)」の UTF-8 バイト列の
sha256 先頭16桁。v0.2 = ``34f9fa9d316587be``。

読み込みは必ず ``open(..., encoding="utf-8", newline="")`` で行う(改行変換を無効化し、
``\\n\\n`` の一致をファイルの実バイトに対して取るため。リポジトリ内のファイルは LF)。

層契約: shibuya.build は shibuya.manifest を import してよいが、実行時に build が
import されることはない(import-linter で強制)。本モジュールは標準ライブラリのみ使う。

使い方::

    python -m shibuya.build.catalog_freeze
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

__all__ = [
    "CATALOG_MD_RELPATH",
    "CATALOG_JSON_RELPATH",
    "SHA_RULE",
    "TABLE_RE",
    "extract_catalog_table",
    "catalog_sha16",
    "parse_catalog_rows",
    "freeze",
    "main",
]

CATALOG_MD_RELPATH = "docs/design/v2-world-catalog.md"
CATALOG_JSON_RELPATH = "src/shibuya/manifest/frozen/world_catalog_v0_2.json"

SHA_RULE = "sha256(utf-8 of table from header row to first blank line)[:16]"

#: 凍結時と同一の抽出正規表現。**変更禁止**(変えると SHA が動く)。
TABLE_RE = re.compile(r"\| # \| 型 \|.*?\n\n", re.S)


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / CATALOG_MD_RELPATH).is_file():
            return parent
    raise FileNotFoundError(
        f"{CATALOG_MD_RELPATH} が見つからない({here} から上位を探索)。"
    )


def _read_md(md_path: Path) -> str:
    """改行変換を無効化して UTF-8 で読む(SHA 規則の前提)。"""
    with Path(md_path).open(encoding="utf-8", newline="") as fh:
        return fh.read()


def extract_catalog_table(md_text: str) -> str:
    """カタログ本表(見出し行〜最初の空行まで)を生のまま切り出す。

    Raises:
        ValueError: 表が見つからない。
    """
    m = TABLE_RE.search(md_text)
    if m is None:
        raise ValueError("世界カタログの本表(`| # | 型 |` で始まる表)が見つからない")
    return m.group(0)


def catalog_sha16(table: str) -> str:
    """凍結 SHA(sha256 先頭16桁)。"""
    return hashlib.sha256(table.encode("utf-8")).hexdigest()[:16]


def parse_catalog_rows(table: str) -> list[dict[str, str]]:
    """本表を行の辞書リストへ。キーは見出し行の9列名、値はセルを strip したもの。

    Raises:
        ValueError: 見出し行が読めない / データ行の列数が見出しと合わない。
    """
    lines = [ln for ln in table.split("\n") if ln.strip()]
    if not lines:
        raise ValueError("空の表")

    def cells(line: str) -> list[str]:
        inner = line.strip()
        return [c.strip() for c in inner[1:-1].split("|")]

    columns = cells(lines[0])
    if len(columns) < 2 or columns[0] != "#":
        raise ValueError(f"見出し行が想定外: {lines[0]!r}")

    rows: list[dict[str, str]] = []
    for line in lines[2:]:  # [0]=見出し行・[1]=区切り行
        values = cells(line)
        if len(values) != len(columns):
            raise ValueError(
                f"列数不一致({len(values)} != {len(columns)}): {line!r}"
            )
        rows.append(dict(zip(columns, values, strict=True)))
    return rows


def freeze(md_path: str | Path, out_json_path: str | Path, version: str = "v0.2") -> dict:
    """Markdown から凍結 JSON を生成して書き出し、その内容を返す。

    Args:
        md_path: 世界カタログ Markdown。
        out_json_path: 出力 JSON。親ディレクトリは無ければ作る。
        version: カタログ版(既定 ``v0.2``)。

    Returns:
        書き出した JSON と同じ内容の dict。
    """
    table = extract_catalog_table(_read_md(Path(md_path)))
    rows = parse_catalog_rows(table)
    columns = list(rows[0].keys()) if rows else []
    payload = {
        "version": version,
        "sha16": catalog_sha16(table),
        "n_classes": len(rows),
        "columns": columns,
        "rows": rows,
        "source": CATALOG_MD_RELPATH,
        "rule": SHA_RULE,
    }
    out = Path(out_json_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=False) + "\n"
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return payload


def main(argv: list[str] | None = None) -> int:
    root = _repo_root()
    ap = argparse.ArgumentParser(
        prog="python -m shibuya.build.catalog_freeze",
        description="世界カタログ(分母)を凍結 JSON へ落とす",
    )
    ap.add_argument("--md", type=Path, default=root / CATALOG_MD_RELPATH)
    ap.add_argument("--out", type=Path, default=root / CATALOG_JSON_RELPATH)
    ap.add_argument("--version", default="v0.2")
    args = ap.parse_args(argv)

    payload = freeze(args.md, args.out, version=args.version)
    print(
        f"{args.out}: version={payload['version']} "
        f"sha16={payload['sha16']} n_classes={payload['n_classes']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
