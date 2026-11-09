# -*- coding: utf-8 -*-
"""bytecheck.tree — 基準の commit の写しの木を作る(git archive)・data へのつなぎを置いて外す・写すファイルの一覧と src の走査。

写すファイルの決め方(``byte_check_10e.py`` の docstring の手順を道具にした)
    エンジンは ``src`` の外の追跡ファイルをリポの根から読む(``Path(__file__).parents[k]``・``resolve_repo_path``・
    ``_repo_root`` と ``*_RELPATH`` の定数)。写しの木にそれが無いと、規則の表が空になる・錨が無い・宣言の表が無い、などで
    final が基準と違って見える(2-3c の検収 L4)。そこで:

    1. :data:`TRACKED_READS` = エンジンが開く ``src`` の外の追跡ファイル(git archive で写す)。
    2. :data:`DATA_READS` = エンジンが data から読むもの(写しの木の ``data`` を本体の data へのつなぎにして見せる。
       有無だけを確かめる=中を開かない)。
    3. :data:`NOT_COPIED` = src に道筋の文字列として現れるが写さないもの(引用の文字列・構築側・19 構成が使わない腕)。
    4. :data:`ROOT_READERS` = src の中でリポの根を求めるファイル(何を読むか)。

    取りこぼしの防ぎ方は 2 段: (a) :func:`scan_path_refs` が src の AST から道筋の文字列(``"docs/…"``・
    ``root / "docs" / …``・``("docs", "bench", …)``・f 文字列・定数の名を通した結合)を集め、試験が「``docs``・``tools``・
    ``tests`` の道筋はすべて 1 か 3 に載る」と「:func:`scan_root_anchors` の見つけたファイルが 4 と同じ」を確かめる。
    (b) ランでは ``one`` が監査フックで開いたファイルを記録し、side が「一覧に無い追跡ファイルを開いた」「写しの木に無い
    ファイルを開こうとした」を誤りにする(:func:`classify_reads`)。

つなぎ(junction)
    :func:`place_data_link` が写しの木の ``data`` を本体の data へのつなぎにし、:func:`remove_link` が**つなぎだけ**を外す。
    外す前につなぎ(か記号のリンク)であることを確かめ、そうでなければ何もせず誤りにする(中を消さない)。Windows では
    作るのは ``_winapi.CreateJunction``・外すのは ``os.rmdir``(つなぎそのものだけ=中に入らない。cmd を通さない=検収 L7)、
    それ以外では記号のリンクと ``os.unlink``。

走査が見つけない形(宣言): 別のモジュールから import した名を通した結合(``from x import BASE`` → ``BASE / "a.json"``)。
ランの監査フック(``check.sort_reads``)が開いたファイルで拾う。
"""

from __future__ import annotations

import ast
import hashlib
import os
import re
import subprocess
import sys
import tarfile
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Iterable

#: エンジンが開く ``src`` の外の追跡ファイル(リポの根からの道筋 → 読む所)。git archive で写しの木へ写す。
TRACKED_READS: Final[dict[str, str]] = {
    "docs/design/rules-table.json": "engine/rules/table.py TABLE_RELPATH(無いと規則の表が空=rules_version が null)",
    "docs/design/bridging-ledger.json": "engine/bridging/ledger.py LEDGER_RELPATH・world/processes/circularity.py",
    "docs/design/v2-budget-declaration.md": "core/budget.py BUDGET_MD_RELPATH(リポの根を上へ探す)",
    "docs/design/v2-perception-contract.md": "world/processes/constitution.py PERCEPTION_CONTRACT_RELPATH",
    "docs/design/v2-pattern-ledger.md": "world/processes/constitution.py PATTERN_LEDGER_RELPATH・circularity.py",
    "docs/bench/anchors/hunger_energy_build_anchors_v0.json": "engine/energy.py ANCHORS_BUILD_PATH",
    "docs/bench/anchors/hunger_energy_validation_anchors_v0.json": "engine/energy.py ANCHORS_VALIDATION_PATH",
    "docs/bench/anchors/ssb2021_activity_prior_v0.json": "engine/classical.py(活動の事前分布)",
}

#: エンジンが data から読むもの(写しの木の data のつなぎで見える。有無だけを確かめる)。
DATA_READS: Final[tuple[str, ...]] = (
    "data/calendar/syukujitsu.csv",  # engine/calendar.py DEFAULT_HOLIDAY_CSV
    "data/realworld/osm/poi_tags_overpass_20260928.json",  # engine/economy_stage2.py OSM_TAGS_RELPATH
    "data/realworld/osm/poi_opening_hours_overpass_20260907.json",  # engine/economy_stage2.py OSM_HOURS_RELPATH
    "data/persona_pool_v2",  # engine/economy_stage2.py PERSONA_POOL_RELPATH(賃金の腕 occupation)
    "data/research_cache/pop41b/derived",  # economy/wages.py DERIVED_RELDIR(賃金構造の表の写し)
)

#: 写しの木にそろえるもの(side が有無を確かめる・``byte_check_10e.HEAD_TREE_FILES`` と同じ役)。
HEAD_TREE_FILES: Final[tuple[str, ...]] = tuple(TRACKED_READS) + DATA_READS

#: src に道筋として現れるが写さないもの(道筋 → 理由)。``{}`` は f 文字列・未知の部品の差し込み。
NOT_COPIED: Final[dict[str, str]] = {
    "docs/bench/anchors": "道筋の部品(energy.py の _ANCHORS_DIR・build/sched/trial.py の ANCHOR_DIR)。開くファイルは TRACKED_READS に個別に載せる",
    "docs/bench/anchors/{}": "energy.py が manifest に書く錨の名の文字列(開くのは TRACKED_READS の 2 本)",
    "docs/bench/anchors/commute_time_dist_r3.json": "構築側(build/sched/trial.py の anchor_path)。エンジンは開かない(byte_check_10e の docstring)",
    "docs/bench/pt_shibuya/pt6_summary_core0241.json": "構築側(build/field/w12_external_nodes.py・build/pop/w16_population.py)",
    "docs/design/v2-world-catalog.md": "構築側(build/catalog_freeze.py)",
    "docs/data-license-ledger.md": "引用の文字列(world/processes/inputs.py の出典の欄)。開かない",
    "docs/design/v2-answers-2026-11-01.md": "引用の文字列(world/processes/inputs.py)。開かない",
    "docs/reference/decision-routing-2026-11-01.md": "引用の文字列(world/processes/absent.py・inputs.py)。開かない",
    "docs/design/v2-boundary-economy-design.md": "引用の文字列(world/processes/inputs.py)。開かない",
    "docs/design/v2-wallbounce-decisions-2026-10-12.md": "引用の文字列(world/processes/inputs.py)。開かない",
    "docs/design/prompt-2026-11-01.md": "引用の文字列(world/processes/inputs.py)。開かない",
    "tools/instruments/warmup_gauge.py": "manifest に書く計器の名(engine/experiment/warmup.py)。開かない",
    "docs": "接頭辞の文字列(engine/bridging/ledger.py の _DOC_PREFIX=台帳の行の出典の形の検査)。開かない",
}

#: src の中でリポの根を求めるファイル(src からの道筋 → 何を読むか)。:func:`scan_root_anchors` と同じ集合でなければならない。
ROOT_READERS: Final[dict[str, str]] = {
    "shibuya/build/catalog_freeze.py": "構築側: docs/design/v2-world-catalog.md(NOT_COPIED)",
    "shibuya/build/pop/w21_apply.py": "構築側: docs/design/rules-table.json(TRACKED_READS)",
    "shibuya/build/sched/trial.py": "構築側: docs/bench/anchors/commute_time_dist_r3.json(NOT_COPIED)",
    "shibuya/build/sched/w20_calendar_1a.py": "構築側: docs/design/rules-table.json(TRACKED_READS)",
    "shibuya/core/budget.py": "docs/design/v2-budget-declaration.md(TRACKED_READS)",
    "shibuya/core/paths.py": "リポの根と包みの根の定義(移す段 2-2)。読むものは呼び手の行",
    "shibuya/economy/wages.py": "data/research_cache/pop41b/derived(DATA_READS)",
    "shibuya/engine/bridging/ledger.py": "docs/design/bridging-ledger.json(TRACKED_READS)",
    "shibuya/engine/calendar.py": "resolve_repo_path の呼び(定義は core/paths.py)・data/calendar/syukujitsu.csv(DATA_READS)",
    "shibuya/engine/classical.py": "docs/bench/anchors/ssb2021_activity_prior_v0.json(TRACKED_READS)",
    "shibuya/engine/economy_stage2.py": "data/realworld/osm の 2 本・data/persona_pool_v2(DATA_READS)",
    "shibuya/engine/energy.py": "docs/bench/anchors の 2 本(TRACKED_READS)",
    "shibuya/engine/resume.py": "渡された相対の道筋の同定(path_identity)と .git の commit(写しの木はリポの外=空の値)",
    "shibuya/engine/rules/table.py": "docs/design/rules-table.json(TRACKED_READS)",
    "shibuya/world/processes/circularity.py": "docs/design/bridging-ledger.json・v2-pattern-ledger.md(TRACKED_READS)",
    "shibuya/world/processes/constitution.py": "docs/design/v2-perception-contract.md・v2-pattern-ledger.md(TRACKED_READS)",
}

#: 追跡ファイルの最上位のディレクトリ(src の外)。``data`` は追跡しない(つなぎで見せる)。
TRACKED_TOPS: Final[tuple[str, ...]] = ("docs", "tools", "tests")
_TOPS: Final[tuple[str, ...]] = TRACKED_TOPS + ("data",)
_HOLE: Final[str] = "{}"


@dataclass(frozen=True)
class PathRef:
    """src に現れた、リポの根からの道筋の文字列 1 つ。"""

    path: str  # posix・末尾の / なし・差し込みは ``{}``
    file: str  # src からの道筋(posix)
    line: int


#: 道筋の文字列の頭(``docs/…`` など)。後ろの引用の文(``§2-3`` や空白の後)は切る。
_LEAD_RE: Final[re.Pattern[str]] = re.compile(r"(?:docs|data|tools|tests)(?:/[\w.\-{}@+]*)*", re.ASCII)
#: 書式の差し込み(``%s``・``%(name)s``・``{name}``)。``{}`` にそろえる(検収 L2: ``"docs/x/%s.json" % …``)。
_FMT_RE: Final[re.Pattern[str]] = re.compile(r"%(?:\([^)]*\))?[-#0 +]*\d*(?:\.\d+)?[sdifr]|\{[^{}]*\}")


def norm_text(text: str) -> str:
    """道筋の文字列の書き方をそろえる(``\\`` を ``/`` に・頭の ``./`` を外す・書式の差し込みを ``{}`` に)。"""
    t = text.replace("\\", "/")
    while t.startswith("./"):
        t = t[2:]
    return _FMT_RE.sub(_HOLE, t)


def _starts_top(text: str) -> bool:
    return any(text.startswith(t + "/") for t in _TOPS)


def lead_path(text: str) -> str | None:
    """文字列の頭の道筋(``docs``・``data``・``tools``・``tests`` で始まるもの)。無ければ None。"""
    text = norm_text(text)
    m = _LEAD_RE.match(text)
    if m is None:
        return None
    rest = text[m.end():]
    if rest and not (rest[0].isspace() or rest[0] in "(（§、,;:"):  # ``docsify`` など語の途中で切れたもの
        return None
    return _norm([m.group(0)])


def _is_top(seg: str) -> bool:
    return seg in _TOPS or any(seg.startswith(t + "/") for t in _TOPS)


def _norm(segs: Iterable[str]) -> str:
    parts: list[str] = []
    for s in segs:
        parts.extend(p for p in s.split("/") if p)
    return "/".join(parts)


def _fstring(node: ast.JoinedStr) -> str:
    return "".join(v.value if isinstance(v, ast.Constant) and isinstance(v.value, str) else _HOLE for v in node.values)


@dataclass
class _Symbols:
    """モジュールの頭の代入: 道筋になる名(``paths``)と、ただの文字列の定数(``consts``=鎖の部品にだけ使う)。"""

    paths: dict[str, str]
    consts: dict[str, str]


class _PathVisitor(ast.NodeVisitor):
    def __init__(self, rel: str, symbols: _Symbols) -> None:
        self.rel, self.symbols = rel, symbols
        self.refs: list[PathRef] = []

    def _add(self, path: str | None, node: ast.AST) -> None:
        if path:
            self.refs.append(PathRef(path, self.rel, getattr(node, "lineno", 0)))

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, str) and _starts_top(norm_text(node.value)):
            self._add(lead_path(node.value), node)

    def visit_JoinedStr(self, node: ast.JoinedStr) -> None:
        text = _fstring(node)
        if _starts_top(norm_text(text)):
            self._add(lead_path(text), node)
        for v in node.values:  # 差し込みの式の中も見る
            if isinstance(v, ast.FormattedValue):
                self.visit(v.value)

    def visit_Tuple(self, node: ast.Tuple) -> None:
        self._add(tuple_path(node), node)
        self.generic_visit(node)

    def visit_List(self, node: ast.List) -> None:  # 検収 L2: ``PARTS = ["docs", …]``
        self._add(tuple_path(node), node)
        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp) -> None:
        if isinstance(node.op, ast.Add):  # 検収 L2: ``"docs/" + NAME``・``root + "docs/x.json"``
            leaves = _add_leaves(node)
            self._add(concat_path([_segment(x, self.symbols) for x in leaves]), node)
            for leaf in leaves:
                if isinstance(leaf, ast.JoinedStr):
                    for v in leaf.values:
                        if isinstance(v, ast.FormattedValue):
                            self.visit(v.value)
                elif not isinstance(leaf, (ast.Constant, ast.Name)):
                    self.visit(leaf)
            return
        if isinstance(node.op, ast.Div):
            leaves = _div_leaves(node)
            self._add(chain_path([_segment(x, self.symbols) for x in leaves]), node)
            for leaf in leaves:  # 鎖の葉のうち式(呼び出しなど)の中は見る(葉の文字列は鎖として数えた)
                if not isinstance(leaf, (ast.Constant, ast.Name, ast.JoinedStr)):
                    self.visit(leaf)
            return
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        segs = _call_segments(node, self.symbols)
        if segs is not None:
            self._add(chain_path(segs), node)
        self.generic_visit(node)


def tuple_path(node: ast.Tuple | ast.List) -> str | None:
    """文字列の定数だけの tuple か list(``("..", "docs", "bench", …)``)を道筋にする(先頭の ``..`` は飛ばす)。"""
    vals = [e.value for e in node.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
    if not vals or len(vals) != len(node.elts):
        return None
    while vals and vals[0] == "..":
        vals = vals[1:]
    return _norm(vals) if vals and vals[0] in _TOPS else None


def _div_leaves(node: ast.AST) -> list[ast.AST]:
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return _div_leaves(node.left) + _div_leaves(node.right)
    return [node]


def _add_leaves(node: ast.AST) -> list[ast.AST]:
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _add_leaves(node.left) + _add_leaves(node.right)
    return [node]


def _segment(leaf: ast.AST, symbols: _Symbols) -> str | None:
    """鎖の部品 1 つ(文字列の定数・f 文字列・道筋の名・文字列の定数の名・``Path("docs")``)。分からなければ None。"""
    if isinstance(leaf, ast.Constant) and isinstance(leaf.value, str):
        return leaf.value
    if isinstance(leaf, ast.JoinedStr):
        return _fstring(leaf)
    if isinstance(leaf, ast.Name):
        return symbols.paths.get(leaf.id, symbols.consts.get(leaf.id))
    if isinstance(leaf, ast.Starred) and isinstance(leaf.value, ast.Name):
        return symbols.paths.get(leaf.value.id)
    if isinstance(leaf, ast.Starred) and isinstance(leaf.value, (ast.Tuple, ast.List)):
        vals = [e.value for e in leaf.value.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
        return "/".join(vals) if vals and len(vals) == len(leaf.value.elts) else None
    if isinstance(leaf, ast.Call):  # 検収 L2: ``Path("docs") / "design" / …``
        segs = _call_segments(leaf, symbols)
        if segs is not None and any(s is not None for s in segs):
            return "/".join(s if s is not None else _HOLE for s in segs)
    return None


def _dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_dotted(node.value)}.{node.attr}"
    return ""


def _call_segments(node: ast.Call, symbols: _Symbols) -> list[str | None] | None:
    """``x.joinpath(a, *T, b)``・``Path(a, b)``・``os.path.join(a, b)``・``"/".join([a, b])`` の部品(それ以外は None)。"""
    f = node.func
    if isinstance(f, ast.Attribute) and f.attr == "joinpath":
        return [_segment(f.value, symbols), *(_segment(a, symbols) for a in node.args)]
    if isinstance(f, ast.Attribute) and f.attr == "join":  # 検収 L2
        if (isinstance(f.value, ast.Constant) and f.value.value in ("/", "\\") and len(node.args) == 1
                and isinstance(node.args[0], (ast.List, ast.Tuple))):
            return [_segment(e, symbols) for e in node.args[0].elts]
        if _dotted(f.value) in ("os.path", "path", "posixpath", "ntpath"):
            return [_segment(a, symbols) for a in node.args]
        return None
    name = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else ""
    if name in ("Path", "PurePath", "PurePosixPath") and node.args:
        return [_segment(a, symbols) for a in node.args]
    return None


def chain_path(segs: list[str | None]) -> str | None:
    """``/`` の鎖の部品から道筋を作る(最初の ``docs``・``data``・``tools``・``tests`` から。後の未知の部品は ``{}``)。"""
    for i, s in enumerate(segs):
        if s is not None and _is_top(norm_text(s)):
            head = lead_path(s) or norm_text(s)
            return _norm([head, *(norm_text(x) if x is not None else _HOLE for x in segs[i + 1:])])
    return None


def concat_path(parts: list[str | None]) -> str | None:
    """``+`` でつないだ文字列の部品から道筋を作る(最初に ``docs/`` などで始まる部品から。未知の部品は ``{}``)。"""
    for i, s in enumerate(parts):
        if s is not None and _starts_top(norm_text(s)):
            return lead_path("".join(x if x is not None else _HOLE for x in parts[i:]))
    return None


def _module_symbols(tree: ast.Module) -> _Symbols:
    """モジュールの頭の代入で、値が道筋になる名と、ただの文字列の定数の名。"""
    sym = _Symbols({}, {})
    for st in tree.body:
        targets: list[ast.expr] = []
        value: ast.expr | None = None
        if isinstance(st, ast.Assign):
            targets, value = list(st.targets), st.value
        elif isinstance(st, ast.AnnAssign) and st.value is not None:
            targets, value = [st.target], st.value
        names = [t.id for t in targets if isinstance(t, ast.Name)]
        if not names or value is None:
            continue
        path: str | None = None
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            path = lead_path(value.value) if _is_top(value.value) else None
            if path is None:
                for n in names:
                    sym.consts[n] = value.value
        elif isinstance(value, ast.BinOp) and isinstance(value.op, ast.Div):
            path = chain_path([_segment(x, sym) for x in _div_leaves(value)])
        elif isinstance(value, ast.BinOp) and isinstance(value.op, ast.Add):
            path = concat_path([_segment(x, sym) for x in _add_leaves(value)])
        elif isinstance(value, (ast.Tuple, ast.List)):
            path = tuple_path(value)
        elif isinstance(value, ast.Call):
            segs = _call_segments(value, sym)
            path = chain_path(segs) if segs is not None else None
        if path:
            for n in names:
                sym.paths[n] = path
    return sym


def _py_files(src_dir: Path) -> list[Path]:
    return sorted(p for p in src_dir.rglob("*.py") if "__pycache__" not in p.parts)


def scan_path_refs(src_dir: str | Path) -> list[PathRef]:
    """src の全 ``.py`` から、リポの根からの道筋の文字列を集める(AST だけ=import しない)。"""
    src = Path(src_dir)
    refs: list[PathRef] = []
    for p in _py_files(src):
        tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        v = _PathVisitor(p.relative_to(src).as_posix(), _module_symbols(tree))
        v.visit(tree)
        refs.extend(v.refs)
    return sorted(set(refs), key=lambda r: (r.path, r.file, r.line))


def tracked_refs(refs: Iterable[PathRef]) -> set[str]:
    """道筋のうち追跡ファイルの側(``docs``・``tools``・``tests``)のもの。"""
    return {r.path for r in refs if r.path.split("/")[0] in TRACKED_TOPS}


def unclassified_refs(refs: Iterable[PathRef]) -> dict[str, list[str]]:
    """追跡ファイルの側の道筋のうち、:data:`TRACKED_READS` にも :data:`NOT_COPIED` にも無いもの(道筋 → 現れた所)。"""
    out: dict[str, list[str]] = {}
    for r in refs:
        if r.path.split("/")[0] in TRACKED_TOPS and r.path not in TRACKED_READS and r.path not in NOT_COPIED:
            out.setdefault(r.path, []).append(f"{r.file}:{r.line}")
    return out


def scan_root_anchors(src_dir: str | Path) -> dict[str, list[int]]:
    """src の中でリポの根を求めるファイル(src からの道筋 → 行)。

    数えるもの: ``….parents[k]`` で k がそのファイルからリポの根に届く数(``src/a/b.py`` なら 3)・``….parents`` を
    上へ辿る for・``resolve_repo_path(…)``・``_repo_root(…)`` の呼び出し・``REPO_ROOT`` の名。
    """
    src = Path(src_dir)
    out: dict[str, list[int]] = {}
    for p in _py_files(src):
        rel = p.relative_to(src)
        depth = len(rel.parts) + 1  # src/ の 1 段を足す=リポの根からの部品の数
        tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        lines: set[int] = set()
        for node in ast.walk(tree):
            if (isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute)
                    and node.value.attr == "parents" and isinstance(node.slice, ast.Constant)
                    and isinstance(node.slice.value, int) and node.slice.value >= depth - 1):
                lines.add(node.lineno)
            elif isinstance(node, ast.For) and isinstance(node.iter, ast.Attribute) and node.iter.attr == "parents":
                lines.add(node.lineno)
            elif isinstance(node, ast.Call):
                f = node.func
                name = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else ""
                if name in ("resolve_repo_path", "_repo_root"):
                    lines.add(node.lineno)
            elif isinstance(node, ast.Name) and node.id == "REPO_ROOT":
                lines.add(node.lineno)
        if lines:
            out[rel.as_posix()] = sorted(lines)
    return out


def tree_missing(root: str | Path, files: Iterable[str] = HEAD_TREE_FILES) -> list[str]:
    """写しの木(``src`` の親)に足りないもの。"""
    r = Path(root)
    return [rel for rel in files if not (r / rel).exists()]


# ------------------------------------------------------------------ 開いたファイルの仕分け(ランの記録から)
def classify_reads(reads: Iterable[str], root: str | Path, *, listed: Iterable[str] = TRACKED_READS) -> dict[str, list[str]]:
    """ランで開いた ``src`` の外の追跡ファイル(リポの根からの道筋)を仕分ける。

    - ``unlisted``: :data:`TRACKED_READS` に無い(写しの一覧に足す=足さないと基準の写しの木に無い)。
    - ``absent``: 写しの木に無い(開こうとして無かった=写しの取りこぼし)。
    """
    r = Path(root)
    lst = set(listed)
    rs = sorted(set(reads))
    return {"unlisted": [x for x in rs if x not in lst], "absent": [x for x in rs if not (r / x).exists()]}


# ------------------------------------------------------------------ git archive
def git(repo: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    """``git -C repo …``(出力はバイト)。"""
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True)


def resolve_commit(repo: Path, rev: str) -> str:
    """``rev`` の commit の全桁。無ければ ``ValueError``。"""
    r = git(repo, "rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}")
    if r.returncode != 0:
        raise ValueError(f"commit が無い: {rev}")
    return r.stdout.decode("ascii").strip()


def paths_in_commit(repo: Path, commit: str, paths: Iterable[str]) -> tuple[list[str], list[str]]:
    """``paths`` のうち commit にあるもの・無いもの(``git ls-tree``)。"""
    have: list[str] = []
    lack: list[str] = []
    for p in paths:
        r = git(repo, "ls-tree", "--name-only", commit, "--", p)
        (have if r.returncode == 0 and r.stdout.strip() else lack).append(p)
    return have, lack


def archive_paths(extra: Iterable[str] = ()) -> list[str]:
    """写しの木へ git archive で写す道筋(``src``+:data:`TRACKED_READS`+``extra``・重なりを除く)。"""
    out = ["src", *TRACKED_READS]
    for e in extra:
        if e not in out:
            out.append(e)
    return out


def git_archive(repo: Path, commit: str, paths: Iterable[str], dest: Path) -> None:
    """commit の ``paths`` を ``dest`` へ展開する(``git archive`` の tar を Python の tarfile で読む・data の filter)。"""
    dest.mkdir(parents=True, exist_ok=False)
    proc = subprocess.Popen(["git", "-C", str(repo), "archive", "--format=tar", commit, "--", *paths],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdout is not None
    try:
        with tarfile.open(fileobj=proc.stdout, mode="r|") as tf:
            tf.extractall(dest, filter="data")
    finally:
        proc.stdout.close()
        err = proc.stderr.read() if proc.stderr is not None else b""
        code = proc.wait()
    if code != 0:
        raise RuntimeError(f"git archive が失敗した(終了コード {code}): {err.decode('utf-8', 'replace')[-500:]}")


# ------------------------------------------------------------------ data へのつなぎ
def is_link(path: str | Path) -> bool:
    """つなぎ(junction)か記号のリンクか。"""
    p = Path(path)
    return p.is_junction() or p.is_symlink()


class NotALinkError(RuntimeError):
    """外そうとした道筋がつなぎでない(何もしていない)。"""


def _make_junction(target: Path, link: Path) -> None:
    """Windows のつなぎ(junction)を作る(``_winapi.CreateJunction``=cmd を通さない・検収 L7。無い Python では ``mklink /J``)。"""
    try:
        import _winapi  # noqa: PLC0415 - Windows だけ

        make = _winapi.CreateJunction
    except (ImportError, AttributeError):
        r = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], capture_output=True)
        if r.returncode != 0:
            raise RuntimeError(f"つなぎを作れなかった: {r.stderr.decode('cp932', 'replace')[-300:]}") from None
        return
    make(str(target), str(link))


def place_data_link(tree_root: Path, target: Path) -> Path:
    """``tree_root/data`` を ``target`` へのつなぎにする(Windows は junction・それ以外は記号のリンク)。"""
    link = tree_root / "data"
    if link.exists() or is_link(link):
        raise FileExistsError(f"写しの木に data が既にある: {link}")
    tgt = Path(os.path.realpath(target))
    if not tgt.is_dir():
        raise FileNotFoundError(f"つなぎの先が無い: {target}")
    if os.name == "nt":
        _make_junction(tgt, link)
        if not link.is_junction():
            raise RuntimeError(f"つなぎを作れなかった: {link}")
    else:
        os.symlink(tgt, link, target_is_directory=True)
    return link


def remove_link(path: str | Path) -> None:
    """つなぎ(か記号のリンク)だけを外す。つなぎでなければ :class:`NotALinkError`(何も消さない)。

    Windows は ``os.rmdir``(つなぎそのものを外す=先の中に入らない・cmd を通さない=検収 L7)・それ以外は ``os.unlink``。
    外した後に道筋が残っていれば ``RuntimeError``。
    """
    p = Path(path)
    if not is_link(p):
        raise NotALinkError(f"つなぎでない(外さない): {p}")
    if os.name == "nt":
        os.rmdir(p)
    else:
        os.unlink(p)
    if p.exists() or is_link(p):
        raise RuntimeError(f"つなぎが残っている: {p}")


def in_git_worktree(path: str | Path) -> bool:
    """``path``(無ければ在る一番近い親)が git の作業木の中か(検収 M4: 写しの木が作業木の中にあると、根を上へ辿る読み口が
    作業木の docs を読む)。git が無ければ False。"""
    p = Path(os.path.abspath(str(path)))
    while not p.exists() and p != p.parent:
        p = p.parent
    try:
        r = subprocess.run(["git", "-C", str(p), "rev-parse", "--is-inside-work-tree"], capture_output=True)
    except OSError:
        return False
    return r.returncode == 0 and r.stdout.strip() == b"true"


def src_files_digest(src_dir: str | Path, rels: Iterable[str]) -> dict[str, str | None]:
    """``src_dir`` の下のファイル(``src_dir`` からの posix の道筋)のバイトの sha256 の頭 16 桁(無ければ None)。

    ``one`` が読んだ ``shibuya`` のモジュールの digest(``src_files``)と同じ作り方。run が基準の側の digest を写しの木と
    照らす(検収 M1)。"""
    s = Path(src_dir)
    out: dict[str, str | None] = {}
    for rel in rels:
        f = s / rel
        out[rel] = hashlib.sha256(f.read_bytes()).hexdigest()[:16] if f.is_file() else None
    return out


def python_prefixes() -> tuple[str, ...]:
    """Python の置き場(開いたファイルの記録から外す)。"""
    return tuple(sorted({os.path.normcase(os.path.abspath(x)) for x in (sys.prefix, sys.base_prefix, sys.exec_prefix)}))
