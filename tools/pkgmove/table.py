# -*- coding: utf-8 -*-
"""全ファイルの表を読み、対応表 TOML(今の道 → 新しい道)を書く・読む。保留の一覧はここだけに置く。

- 表: ``docs/reference/package-map-final-2026-11-09-files.md`` の §3(1 ファイル 1 行・327 行)。
- 行の種類(``kind``):
    ``move``  置き場が変わり割らないファイル(段 4 で移す)。``empty_head`` は新しい頭を空にする行(表の「(空にする)」)。
    ``empty`` 置き場は同じで、頭を空にする行(``economy/__init__.py``・``world/__init__.py``)。
    ``split`` 割るファイル(段 3・段 4 では割らない。表にある割り先の一覧を記録だけする)。
    ``delete`` 消す頭(``agents/__init__.py``・``census/__init__.py``)。
    ``keep``  置き場を変えないもの(build と根の頭)。
- 段(``stage``): ``move``・``empty`` は包みの名、``delete`` は ``delete``。段 4 の小さな段の順は :data:`STAGES`。
- 保留(:data:`HELD`): ユーザーか親の判断待ちの問いに関わる行。道具はこの行を動かすことを断る。
"""
from __future__ import annotations

import hashlib
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, Iterable

TABLE_REL: Final[str] = "docs/reference/package-map-final-2026-11-09-files.md"
MAP_REL: Final[str] = "tools/pkgmove/map.toml"
MAP_SCHEMA: Final[str] = "shibuya.tools/pkgmove/map/1"

#: 段 4 の小さな段の順(計画 §7-4 の段 4 の行)。最後の ``delete`` は消す 2 本。
STAGES: Final[tuple[str, ...]] = (
    "foundation", "world", "economy", "act", "mind", "society", "interim_bundles", "runtime", "experiments",
    "validation", "delete",
)

#: 保留の行(今の道 → 理由)。**保留の一覧はここだけ**(README に写す)。道具はこの行を動かさない(名指しで動かそうとすれば断る)。
HELD: Final[dict[str, str]] = {
    "engine/contact/deliver.py": "問い 1 連絡の器 4 本の置き場(本文 §8-1 の 1=今 society に置くか一時の区分に置くか)",
    "engine/contact/calls.py": "問い 1 連絡の器 4 本の置き場(本文 §8-1 の 1)",
    "engine/contact/chat_state.py": "問い 1 連絡の器 4 本の置き場(本文 §8-1 の 1)",
    "engine/contact/tools.py": "問い 1 連絡の器 4 本の置き場(本文 §8-1 の 1)",
    "engine/resolve.py": "問い 2 apply_detection の割り先(本文 §8-1 の 2=act に置く・2 つに割る・mind/ops.py に置く)",
    "engine/run.py": "問い 6 python -m shibuya.engine.run の入口(本文 §8-1 の 6=移すか消すかが決まっていない)",
    "engine/removed_switches.py": "行 224a 置き場は段 4 の前に親が確かめる(move-346 の記録 §7-2 の (3))",
}

_ROW_RE = re.compile(
    r"^\| (?P<num>\d+[a-z]?) \| `(?P<old>[^`]+)` \| (?P<pkg>[^|]+?) \| (?P<new>.+?) \| (?P<split>いいえ|割る[^|]*?) \| "
    r"(?P<why>.*) \| (?P<src>[^|]+?) \| (?P<rec>[^|]+?) \|$")
_CODE_SPAN_RE = re.compile(r"`([^`]+)`")


@dataclass(frozen=True)
class Row:
    """表の 1 行(道筋は ``src/shibuya`` からの相対・``/`` 区切り)。"""

    num: str
    old: str
    package: str
    kind: str
    new: str = ""
    stage: str = ""
    empty_head: bool = False
    split_to: tuple[str, ...] = ()
    held: str = ""

    @property
    def is_head(self) -> bool:
        return self.old.endswith("__init__.py")


@dataclass
class MapDoc:
    """対応表 TOML の中身。"""

    rows: list[Row]
    source: str = TABLE_REL
    source_sha256: str = ""
    stages: tuple[str, ...] = STAGES
    meta: dict = field(default_factory=dict)

    def by_old(self) -> dict[str, Row]:
        return {r.old: r for r in self.rows}


def parse_table(text: str) -> list[Row]:
    """表の §3 の行を読む(行の数と道筋の重なりを確かめる)。"""
    rows: list[Row] = []
    seen: set[str] = set()
    for line in text.splitlines():
        m = _ROW_RE.match(line)
        if not m:
            continue
        old = m["old"]
        if old in seen:
            raise ValueError(f"表に同じ道筋が 2 行ある: {old}")
        seen.add(old)
        pkg = m["pkg"].strip()
        new_col = m["new"]
        spans = _CODE_SPAN_RE.findall(new_col)
        held = HELD.get(old, "")
        if m["split"].startswith("割る"):
            rows.append(Row(m["num"], old, pkg, "split", new=spans[0] if spans else "", split_to=tuple(spans),
                            held=held))
            continue
        if pkg == "消す":
            rows.append(Row(m["num"], old, pkg, "delete", stage="delete", held=held))
            continue
        if not spans:
            raise ValueError(f"新しい置き場が読めない: {old} {new_col!r}")
        new = spans[0]
        empty = "(空にする)" in new_col
        if pkg == "build" or new == old:
            kind = "empty" if (empty and new == old) else "keep"
            rows.append(Row(m["num"], old, pkg, kind, new=new, stage=pkg if kind == "empty" else "",
                            empty_head=empty, held=held))
            continue
        rows.append(Row(m["num"], old, pkg, "move", new=new, stage=pkg, empty_head=empty, held=held))
    missing = sorted(set(HELD) - seen)
    if missing:
        raise ValueError(f"保留の一覧の行が表に無い: {missing}")
    return rows


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ------------------------------------------------------------------ TOML の書き手(標準ライブラリの tomllib は読むだけ)
def _q(s: str) -> str:
    """TOML の基本の文字列(``"`` と ``\\`` と制御文字だけを逃がす)。"""
    out = []
    for ch in s:
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ord(ch) < 0x20 or ch == "\x7f":
            out.append(f"\\u{ord(ch):04x}")
        else:
            out.append(ch)
    return '"' + "".join(out) + '"'


def _arr(xs: Iterable[str]) -> str:
    return "[" + ", ".join(_q(x) for x in xs) + "]"


def render_map(rows: list[Row], source_sha256: str) -> str:
    """対応表 TOML の文(行の順は表の順)。"""
    head = [
        "# 移す段 3 の対応表(道具 tools/pkgmove/cli.py map が全ファイルの表から作る。手で書かない)。",
        "# 道筋は src/shibuya からの相対。kind: move=移す(empty_head=新しい頭を空に)・empty=同じ置き場で頭を空に・",
        "# split=割る(段 3・段 4 では割らない。split_to は表の割り先の記録だけ)・delete=消す頭・keep=置き場を変えない。",
        "# held がある行は保留(道具は動かさない)。",
        f"schema = {_q(MAP_SCHEMA)}",
        f"source = {_q(TABLE_REL)}",
        f"source_sha256 = {_q(source_sha256)}",
        f"stages = {_arr(STAGES)}",
        "",
    ]
    body: list[str] = []
    for r in rows:
        body.append("[[row]]")
        body.append(f"num = {_q(r.num)}")
        body.append(f"old = {_q(r.old)}")
        body.append(f"package = {_q(r.package)}")
        body.append(f"kind = {_q(r.kind)}")
        if r.new:
            body.append(f"new = {_q(r.new)}")
        if r.stage:
            body.append(f"stage = {_q(r.stage)}")
        if r.empty_head:
            body.append("empty_head = true")
        if r.split_to:
            body.append(f"split_to = {_arr(r.split_to)}")
        if r.held:
            body.append(f"held = {_q(r.held)}")
        body.append("")
    return "\n".join(head + body)


def build_map_text(repo: Path) -> str:
    text = (repo / TABLE_REL).read_text(encoding="utf-8")
    return render_map(parse_table(text), sha256_text(text))


def load_map(path: Path) -> MapDoc:
    """対応表 TOML を読む(保留の一覧が道具の一覧と同じかも確かめる)。"""
    doc = tomllib.loads(path.read_text(encoding="utf-8"))
    if doc.get("schema") != MAP_SCHEMA:
        raise ValueError(f"対応表の schema が違う: {doc.get('schema')!r}")
    rows = [Row(num=r["num"], old=r["old"], package=r["package"], kind=r["kind"], new=r.get("new", ""),
                stage=r.get("stage", ""), empty_head=bool(r.get("empty_head", False)),
                split_to=tuple(r.get("split_to", ())), held=r.get("held", "")) for r in doc.get("row", [])]
    held = {r.old: r.held for r in rows if r.held}
    if held != HELD:
        raise ValueError("対応表の保留の行が道具の保留の一覧(table.HELD)と違う(cli.py map で作り直す)")
    return MapDoc(rows=rows, source=doc.get("source", ""), source_sha256=doc.get("source_sha256", ""),
                  stages=tuple(doc.get("stages", STAGES)), meta={k: v for k, v in doc.items() if k != "row"})
