"""engine.bridging.scan — コードの expedient の宣言を AST で数える(第 1 期 1-4・つなぎの台帳との 1 対 1)。

数える形は 6 つ(発注の 3 形・親の補足+第 4〜6 形=親の判断 第334・検収 M1):

| 形 | ``form`` | 中身 |
|---|---|---|
| A | ``conf`` | キーワード引数 ``conf="expedient"``・代入 ``conf = "expedient"``(属性 ``x.conf`` も)・辞書 ``{"conf": "expedient"}`` |
| B | ``expedients`` | build の ``StageResult(expedients=[...])`` の要素 1 つずつ・``x.expedients.append(...)``/``extend``/``+=``・
  モジュールの表 ``EXPEDIENTS``/``*_EXPEDIENTS``(``expedients=list(EXPEDIENTS)`` はこの表を数える=二重に数えない) |
| C | ``docstring`` | モジュール・クラス・関数の docstring の行頭が ``expedient:`` の段落(空行まで) |
| D | ``heading`` | モジュール・クラス・関数の docstring の、1 行まるごとが ``expedient(…)`` の見出し(例「expedient(本モジュール分)」)。
  **見出し 1 つで 1 件**(下の項は数えて ``items`` に持つ=空行までの ``- `` で始まる行の数)。行の途中で折り返して
  行頭に来ただけの ``expedient(…)…。`` は見出しでない(行が閉じかっこで終わらない) |
| E | ``process`` | 世界過程と PlanSpec の宣言=呼び出しの引数に ``mechanism=False`` と ``repayment_due=`` の両方がある
  もの(``world/processes/first_batch.py`` の ``WorldProcess(...)``・``PlanSpec(...)``)。1 つの呼び出しで 1 件。鍵は
  ``id=`` の値 |
| F | ``fallback`` | 世界の台帳の「conf 宣言つきフォールバック台帳」(``WorldRegistry.fallback_ledger()``=executor が
  engine_rule の行)を**実行して読む**(AST ではない)。1 行で 1 件。鍵は ``<subject_id>|<plan_spec_id>`` |

各宣言の同定の文字列 ``declared_in`` は ``<リポの根からの道筋>#<形>:<中身の sha256 の先頭 8 桁>``(同じ中身が同じ
ファイルの同じ形に 2 回あれば ``.2`` を足す)。中身は、文字列ならその文字列、f 文字列や式なら ``ast.unparse`` の
文字列、名前なら同じファイルの 1 回だけの代入の右辺(文字列ならその文字列)、見出しは見出しの行の文。中身を書き換える
と同定が変わる=台帳の行も直す(試験が落ちて知らせる)。見出しの下の項の数が変わったら台帳の ``what`` の項数を直す
(試験が見る)。E と F は鍵そのもの(``…#process:<id>``・``…#fallback:<subject>|<plan>``)。

数えないもの(記録 r14/README.md §4-3 の表に件数だけ出す): ``#`` の注の中の expedient・``未リサーチ(expedient)`` の
注記・成長の宣言と状態の欄の ``mechanism=False``(``repayment_due`` の無いもの)・``tag="expedient"`` の契約の行・
行頭でない ``(expedient: …)``。1 対 1 は 6 形の中だけ。

逐次ループ宣言: なし(試験と道具が 1 回呼ぶだけ・ランの中では呼ばない)。
"""

from __future__ import annotations

import ast
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

__all__ = [
    "FORMS", "FORM_CONF", "FORM_EXPEDIENTS", "FORM_DOCSTRING", "FORM_HEADING", "FORM_PROCESS", "FORM_FALLBACK",
    "Declaration", "declared_in_of", "scan_source", "scan_tree", "scan_package", "count_by_form",
    "fallback_declarations", "FALLBACK_PATH",
]

FORM_CONF = "conf"
FORM_EXPEDIENTS = "expedients"
FORM_DOCSTRING = "docstring"
FORM_HEADING = "heading"
FORM_PROCESS = "process"
FORM_FALLBACK = "fallback"
FORMS: tuple[str, ...] = (FORM_CONF, FORM_EXPEDIENTS, FORM_DOCSTRING, FORM_HEADING, FORM_PROCESS, FORM_FALLBACK)
#: 鍵をそのまま ``declared_in`` に書く形(sha にしない)。
_PLAIN_KEY_FORMS = frozenset({FORM_PROCESS, FORM_FALLBACK})
#: F の宣言の置き場(``WorldRegistry.fallback_ledger`` のあるファイル)。
FALLBACK_PATH = "src/shibuya/world/processes/registry.py"

#: モジュールの表の名(``EXPEDIENTS``・``WEATHER_EXPEDIENTS`` など)。
_TABLE_NAME = re.compile(r"^(?:[A-Z0-9_]*_)?EXPEDIENTS$")
#: docstring の段落の頭(半角と全角のコロン)。
_DOC_HEAD = re.compile(r"^expedient\s*[:：]")
#: docstring の見出し(1 行まるごと ``expedient(…)``・閉じかっこで終わる・後ろのコロンは許す)。
_DOC_HEADING = re.compile(r"^expedient\s*[(（].*[)）]\s*[:：]?$")
_EXPEDIENT = "expedient"


@dataclass(frozen=True, slots=True)
class Declaration:
    """コードの expedient の宣言 1 つ(``items`` は見出しの形のときだけ=見出しの下の項の数)。"""

    form: str
    path: str
    line: int
    text: str
    declared_in: str
    items: int = 0

    def as_dict(self) -> dict[str, object]:
        return {"form": self.form, "path": self.path, "line": self.line, "text": self.text,
                "declared_in": self.declared_in, "items": self.items}


def declared_in_of(path: str, form: str, text: str, nth: int = 1) -> str:
    """宣言の同定の文字列(台帳の ``declared_in`` と同じ形)。"""
    key = text if form in _PLAIN_KEY_FORMS else hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]
    return f"{path}#{form}:{key}" + (f".{nth}" if nth > 1 else "")


def _is_expedient_const(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant) and node.value == _EXPEDIENT:
        return True
    return isinstance(node, ast.Attribute) and node.attr.upper() == "EXPEDIENT"


def _text_of(node: ast.AST, assigns: dict[str, list[ast.AST]]) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name) and len(assigns.get(node.id, ())) == 1:
        return _text_of(assigns[node.id][0], {})
    return ast.unparse(node)


def _target_names(stmt: ast.AST) -> Iterator[tuple[str, ast.AST]]:
    if isinstance(stmt, ast.Assign):
        for t in stmt.targets:
            if isinstance(t, ast.Name):
                yield t.id, stmt.value
    elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name) and stmt.value is not None:
        yield stmt.target.id, stmt.value


def _elements(node: ast.AST) -> list[ast.AST] | None:
    if isinstance(node, (ast.List, ast.Tuple)):
        return list(node.elts)
    return None


def _refers_to_table(node: ast.AST, tables: set[str]) -> bool:
    """``EXPEDIENTS``・``list(EXPEDIENTS)``・``tuple(X_EXPEDIENTS)`` の形か。"""
    if isinstance(node, ast.Name):
        return node.id in tables
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("list", "tuple"):
        return len(node.args) == 1 and _refers_to_table(node.args[0], tables)
    return False


def _docstring_paragraphs(doc: str) -> list[tuple[int, str]]:
    """docstring の中の ``expedient:`` の段落(行番号は docstring の中の 0 起点)。"""
    lines = doc.splitlines()
    out: list[tuple[int, str]] = []
    i = 0
    while i < len(lines):
        if _DOC_HEAD.match(lines[i].strip()):
            j = i
            para: list[str] = []
            while j < len(lines) and lines[j].strip():
                para.append(lines[j].strip())
                j += 1
            out.append((i, "\n".join(para)))
            i = j
        else:
            i += 1
    return out


def _docstring_headings(doc: str) -> list[tuple[int, str, int]]:
    """docstring の中の ``expedient(…)`` の見出し(行番号は docstring の中の 0 起点・見出しの文・下の項の数)。"""
    lines = doc.splitlines()
    out: list[tuple[int, str, int]] = []
    for i, line in enumerate(lines):
        head = line.strip()
        if not _DOC_HEADING.match(head):
            continue
        items = 0
        for nxt in lines[i + 1:]:
            s = nxt.strip()
            if not s:
                break
            items += s.startswith("- ")
        out.append((i, head, items))
    return out


def scan_source(source: str, path: str) -> list[Declaration]:
    """1 つのファイルの宣言(``path`` はリポの根からの道筋=``declared_in`` に入る)。"""
    tree = ast.parse(source)
    # 名前 → 代入の右辺(ファイルの中のどこでも=名前の中身を引くため)
    assigns: dict[str, list[ast.AST]] = {}
    for node in ast.walk(tree):
        for name, value in _target_names(node):
            assigns.setdefault(name, []).append(value)
    tables = {n for n, vs in assigns.items()
              if _TABLE_NAME.match(n) and len(vs) == 1 and _elements(vs[0]) is not None}
    raw: list[tuple] = []  # (形, 行, 中身) か見出しは (形, 行, 中身, 項の数)

    # ---- B: モジュールの表 ----
    for stmt in tree.body:
        for name, value in _target_names(stmt):
            if name in tables:
                for e in _elements(value) or []:
                    raw.append((FORM_EXPEDIENTS, getattr(e, "lineno", stmt.lineno), _text_of(e, assigns)))

    for node in ast.walk(tree):
        # ---- B: expedients=[...] ----
        if isinstance(node, ast.keyword) and node.arg == FORM_EXPEDIENTS:
            if _refers_to_table(node.value, tables):
                continue
            elts = _elements(node.value)
            for e in (elts if elts is not None else [node.value]):
                raw.append((FORM_EXPEDIENTS, e.lineno, _text_of(e, assigns)))
        # ---- B: x.expedients.append(...)/extend(...) ----
        elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
              and node.func.attr in ("append", "extend") and isinstance(node.func.value, ast.Attribute)
              and node.func.value.attr == FORM_EXPEDIENTS and node.args):
            arg = node.args[0]
            if node.func.attr == "extend" and _elements(arg) is not None:
                for e in _elements(arg) or []:
                    raw.append((FORM_EXPEDIENTS, e.lineno, _text_of(e, assigns)))
            elif not _refers_to_table(arg, tables):
                raw.append((FORM_EXPEDIENTS, node.lineno, _text_of(arg, assigns)))
        # ---- B: x.expedients += [...] ----
        elif (isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Attribute)
              and node.target.attr == FORM_EXPEDIENTS):
            for e in (_elements(node.value) or [node.value]):
                if not _refers_to_table(e, tables):
                    raw.append((FORM_EXPEDIENTS, e.lineno, _text_of(e, assigns)))
        # ---- A: conf="expedient"・E: mechanism=False と repayment_due= の宣言 ----
        elif isinstance(node, ast.Call):
            kws = {kw.arg: kw.value for kw in node.keywords if kw.arg}
            for kw in node.keywords:
                if kw.arg == FORM_CONF and _is_expedient_const(kw.value):
                    raw.append((FORM_CONF, node.lineno, ast.unparse(node)))
            mech = kws.get("mechanism")
            if isinstance(mech, ast.Constant) and mech.value is False and "repayment_due" in kws:
                ident = kws.get("id")
                key = ident.value if isinstance(ident, ast.Constant) and isinstance(ident.value, str) \
                    else f"{ast.unparse(node.func)}@{node.lineno}"
                raw.append((FORM_PROCESS, node.lineno, key))
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if node.value is not None and _is_expedient_const(node.value) and any(
                    (isinstance(t, ast.Name) and t.id == FORM_CONF)
                    or (isinstance(t, ast.Attribute) and t.attr == FORM_CONF) for t in targets):
                raw.append((FORM_CONF, node.lineno, ast.unparse(node)))
        if isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values):
                if isinstance(k, ast.Constant) and k.value == FORM_CONF and v is not None and _is_expedient_const(v):
                    raw.append((FORM_CONF, node.lineno, ast.unparse(node)))
        # ---- C: docstring の段落 ----
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node, clean=True)
            if doc:
                first = node.body[0].lineno if node.body else 1
                for off, para in _docstring_paragraphs(doc):
                    raw.append((FORM_DOCSTRING, first + off, para))
                # ---- D: docstring の見出し(第 4 形・見出し 1 つで 1 件) ----
                for off, head, items in _docstring_headings(doc):
                    raw.append((FORM_HEADING, first + off, head, items))

    out: list[Declaration] = []
    seen: dict[tuple[str, str], int] = {}
    for r in sorted(raw, key=lambda r: (r[1], FORMS.index(r[0]), r[2])):
        form, line, text = r[0], r[1], r[2]
        items = int(r[3]) if len(r) > 3 else 0
        k = (form, text)
        seen[k] = seen.get(k, 0) + 1
        out.append(Declaration(form, path, int(line), text, declared_in_of(path, form, text, seen[k]), items))
    return out


def scan_tree(root: Path, *, rel_to: Path | None = None) -> list[Declaration]:
    """``root`` の下の ``*.py`` を全部見る(道筋は ``rel_to`` からの posix の相対=既定は ``root`` の親の親)。"""
    root = Path(root)
    base = Path(rel_to) if rel_to is not None else root.parent.parent
    out: list[Declaration] = []
    for p in sorted(root.rglob("*.py")):
        if "__pycache__" in p.parts:
            continue
        rel = p.relative_to(base).as_posix()
        out.extend(scan_source(p.read_text(encoding="utf-8"), rel))
    return out


def fallback_declarations(rows: Iterable[object] | None = None) -> list[Declaration]:
    """F: フォールバック台帳の行(``rows`` を省くと ``first_batch.build_registry().fallback_ledger()`` を実行して読む)。

    行は ``subject_id`` と ``plan_spec_id`` を持つ物(``world.processes.relations.FallbackRow``)。
    """
    if rows is None:
        from shibuya.world.processes import first_batch as _FB

        rows = _FB.build_registry().fallback_ledger()
    import inspect

    from shibuya.world.processes.registry import WorldRegistry

    line = int(inspect.getsourcelines(WorldRegistry.fallback_ledger)[1])
    out: list[Declaration] = []
    seen: dict[str, int] = {}
    for r in rows:
        key = f"{getattr(r, 'subject_id')}|{getattr(r, 'plan_spec_id')}"
        seen[key] = seen.get(key, 0) + 1
        out.append(Declaration(FORM_FALLBACK, FALLBACK_PATH, line, key,
                               declared_in_of(FALLBACK_PATH, FORM_FALLBACK, key, seen[key])))
    return out


def scan_package() -> list[Declaration]:
    """このパッケージ(``src/shibuya``)の宣言(A〜E は AST・F はフォールバック台帳を実行して読む)。道筋は
    ``src/shibuya/...``。"""
    pkg = Path(__file__).resolve().parents[2]
    return scan_tree(pkg, rel_to=pkg.parent.parent) + fallback_declarations()


def count_by_form(decls: Iterable[Declaration]) -> dict[str, int]:
    """形ごとの件数(6 形とも鍵を持つ)。"""
    out = {f: 0 for f in FORMS}
    for d in decls:
        out[d.form] += 1
    return out
