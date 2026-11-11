# -*- coding: utf-8 -*-
"""許可の一覧: 道具が文字列を書き換えてよい (ファイル, 記号)。ここに無い文字列の定数は 1 つも書き換えない。

- (b-src) :data:`SRC_TABLES`: 計画 ``docs/reference/package-map-final-2026-11-09.md`` §7-5 で「段 3 の道具で直す」とした
  ランの側の道の表。規則は ``exact``=文字列の全体が移すファイルの今の道(``src/shibuya`` からの相対)なら新しい道へ。点の名
  (乱数の用途名 ``engine.processes.rail`` など)・理由の文・``basis`` の文は書き換えない。
- (b-tests/tools) ``allow_tests_tools.toml``: tests と tools の道の文字列・``/`` の結合・点の道・子のプロセスに渡すコードの
  import の文を持つ (ファイル, 記号)。``cli.py allow`` が走査で作る(``--check`` で今の木との食い違いを見る)。規則は
  ``paths``(:mod:`pkgmove.strings`)。
- (c) :data:`CLASS_IDS_TABLE`: 固定の表の鍵だけ(:mod:`pkgmove.classids`)。
- (d) :data:`LEDGER_PATHS_TABLE`: つなぎの台帳の道の対応の表(``engine/bridging/ledger_paths.py``)。移したファイルの
  「今の道 → 台帳の道」を書き足す(:mod:`pkgmove.ledgerpaths`・親の決定 1=案 (b))。
- (a) の範囲の追加 :data:`RECORD_TOOLS`: tests が道で読む docs の記録の道具(親の決定 7)。import の文だけを書き換える。
  一覧は :func:`scan_record_tools` の走査と同じでなければならない(試験)。
- 記号の決め方は :func:`pkgmove.model.symbol_map`(頂上の関数・クラス・メソッド・代入の左辺の名)。
"""
from __future__ import annotations

import ast
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Iterable

from pkgmove.table import _arr, _q

ALLOW_TT_REL: Final[str] = "tools/pkgmove/allow_tests_tools.toml"
ALLOW_TT_SCHEMA: Final[str] = "shibuya.tools/pkgmove/allow-tests-tools/1"

#: (b-src) ランの側の道の表(ファイルは今の道=``src/shibuya`` からの相対・記号・何の表か)。規則は ``exact``。
SRC_TABLES: Final[tuple[tuple[str, str, str], ...]] = (
    ("engine/state_ledger.py", "OWNER_CLASSES", "外の状態の持ち主のクラスの置き場(試験が AST で突き合わせる)"),
    ("engine/state_ledger.py", "OWNER_ALT_CLASSES", "同じ道筋に入る別のクラスの置き場"),
    ("engine/state_ledger.py", "_ALLOW_BAND", "列の読みの許可の置き場(AstAllow の 1 つ目)"),
    ("engine/state_ledger.py", "_ALLOW_B4", "同上"),
    ("engine/state_ledger.py", "_ALLOW_REVENUE", "同上"),
    ("engine/state_ledger.py", "_ALLOW_ENERGY_BALANCE", "同上"),
    ("engine/state_ledger.py", "_ALLOW_HEADING", "同上"),
    ("engine/state_ledger.py", "_ALLOW_TASK", "同上"),
    ("engine/state_ledger_ast.py", "DECL_FILES", "SoA の列の宣言の置き場"),
    ("engine/state_ledger_ast.py", "UNRESOLVED_ALLOW", "解決できない読みの許可の置き場"),
    ("engine/state_ledger_ast.py", "RESULT_FILES", "ランの結果を組み立てる置き場"),
    ("engine/state_ledger_ast.py", "GENERIC_FILES", "直列化・ハッシュ・保存と戻しの書き手の置き場"),
    ("engine/state_ledger_ast.py", "DIAG_EXITS", "診断の出口の関数の置き場"),
    ("engine/state_ledger_ast.py", "EXT_AST_ALLOW", "外の状態の場所ごとの許可の置き場"),
    ("engine/state_ledger_ast.py", "ext_reason", "関数の中の 1 か所(resolve の戻しの書き手)"),
    ("engine/rng_audit.py", "SAFE_SITES", "静的に安全な乱数の呼び手の置き場(用途名は変えない)"),
    ("engine/rng_audit.py", "UNDETERMINED_SITES", "静的に決まらない呼び手の置き場(用途名は変えない)"),
    ("engine/rng_audit.py", "scan_sites", "関数の中の 1 か所(乱数のモジュールそのものを外す)"),
    # 〔親の決定 2〕構築の側が凍結の JSON を書く先の既定(``src/shibuya/…`` の形=規則 exact は頭の ``src/shibuya/`` も読む)
    ("build/catalog_freeze.py", "CATALOG_JSON_RELPATH", "構築の側が世界カタログの凍結の JSON を書く先(JSON が動けば一緒に動く)"),
)
#: (c) 固定の表(ファイル・記号)。鍵だけを書き換える。
CLASS_IDS_TABLE: Final[tuple[str, str]] = ("engine/class_ids.py", "CLASS_IDS")
#: (d) つなぎの台帳の道の対応の表(ファイル・記号)。道具が移したファイルの行を書き足す。
LEDGER_PATHS_TABLE: Final[tuple[str, str]] = ("engine/bridging/ledger_paths.py", "LEDGER_PATHS")
#: (a) の範囲に足す docs の記録の道具(tests が道で読むもの・リポの根からの道筋)。import の文だけを書き換える(親の決定 7)。
#: :func:`scan_record_tools` の走査と同じ(試験 ``test_record_tools_list_matches_the_scan_of_tests``)。
RECORD_TOOLS: Final[tuple[str, ...]] = (
    "docs/bench/analysis/c10-relations-2026-09-28/rel8b_measure.py",
    "docs/bench/analysis/wallbounce-1003/10d/first_diff.py",
    "docs/bench/analysis/wallbounce-1012/10e/byte_check_10e.py",
    "docs/bench/analysis/wallbounce-1012/md23/tools/multiday_md23.py",
    "docs/bench/analysis/wallbounce-1012/pop41/tools/stage_pop41.py",
    "docs/bench/analysis/wallbounce-1012/pop41b/tools/stage_pop41b.py",
    "docs/bench/analysis/wallbounce-1012/pop43/tools/activate_pop43.py",
    "docs/bench/analysis/wallbounce-1012/refr20b/tools/measure_refractory.py",
    "docs/bench/analysis/wallbounce-1012/tt23c/tools/activate_tt23c.py",
    "docs/bench/analysis/wallbounce-1012/vb24/tools/activate_vb24.py",
    "docs/bench/analysis/wave2-2026-09-30/wave2_bytecheck.py",
)
_DOCS_PY = re.compile(r"(?:^|/)(docs/[\w./-]+\.py)$")


def scan_record_tools(files: dict[str, str], exists) -> dict[str, list[str]]:
    """tests の Python(``files`` の ``tests/`` の下)が道で読む docs の ``.py``: 道 → 読む試験。拾う形は ``/`` の結合
    (``ROOT / "docs" / … / "x.py"``)と、全体が ``docs/….py`` の文字列(``Path("docs/….py")``)。``exists`` で在るものだけ。"""
    out: dict[str, set[str]] = {}
    for path, text in files.items():
        if not path.startswith("tests/"):
            continue
        for n in ast.walk(ast.parse(text)):
            cand = None
            if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div):
                ops: list[ast.expr] = []
                cur: ast.expr = n
                while isinstance(cur, ast.BinOp) and isinstance(cur.op, ast.Div):
                    ops.append(cur.right)
                    cur = cur.left
                ops.append(cur)
                strs = [x.value for x in reversed(ops) if isinstance(x, ast.Constant) and isinstance(x.value, str)]
                m = _DOCS_PY.search("/".join(strs))
                cand = m.group(1) if m else None
            elif isinstance(n, ast.Constant) and isinstance(n.value, str):
                m = re.fullmatch(r"(?:\./)?(docs/[\w./-]+\.py)", n.value)
                cand = m.group(1) if m else None
            if cand and exists(cand):
                out.setdefault(cand, set()).add(path)
    return {k: sorted(v) for k, v in sorted(out.items())}


@dataclass(frozen=True)
class Site:
    """許可の一覧の 1 行(リポの根からの道筋・記号・規則)。"""

    path: str
    symbol: str
    rule: str


def src_sites(locate) -> list[Site]:
    """(b-src) の行を、今の木の置き場で(``locate``=今の道 → 木の道筋。移した後の木でも引ける)。"""
    return [Site(locate(f), sym, "exact") for f, sym, _ in SRC_TABLES]


def load_tests_tools(repo: Path) -> list[Site]:
    p = repo / ALLOW_TT_REL
    if not p.is_file():
        return []
    doc = tomllib.loads(p.read_text(encoding="utf-8"))
    if doc.get("schema") != ALLOW_TT_SCHEMA:
        raise ValueError(f"{ALLOW_TT_REL} の schema が違う")
    return [Site(s["file"], sym, "paths") for s in doc.get("site", []) for sym in s["symbols"]]


def render_tests_tools(sites: Iterable[tuple[str, str]], note: str) -> str:
    by: dict[str, list[str]] = {}
    for f, sym in sorted(set(sites)):
        by.setdefault(f, []).append(sym)
    lines = [
        "# 移す段 3 の許可の一覧(tests と tools)。道具 tools/pkgmove/cli.py allow が走査で作る(手で書かない)。",
        "# この (ファイル, 記号) の中の道の文字列・/ の結合・点の道・コードの文字列の import の文だけを書き換える。",
        f"schema = {_q(ALLOW_TT_SCHEMA)}",
        f"note = {_q(note)}",
        "",
    ]
    for f, syms in by.items():
        lines += ["[[site]]", f"file = {_q(f)}", f"symbols = {_arr(syms)}", ""]
    return "\n".join(lines)
