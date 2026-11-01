"""第 1 期 1-7 CT5: 連絡先の印の欄を書く所を AST で集める道具(試験の補助・src は読むだけ)。

書く形の広さは共通の道具 ``tests/engine/ast_writers.py``(1-5 の ``rights_writers._LedgerScanner`` を引数つきに写した物=
検収 M1)に任せる。ここは列の名と、許す所の表だけを持つ:

- 列=``contact_flags``(公開の読み取り専用の view の property)と ``_contact_flags``(中身=``RelationLayer`` の属性)。
- 中身の書きは ``RelationLayer._write_contacts`` だけ。差し替え(属性の置き)は ``RelationLayer.__init__`` だけ。書く口
  ``_write_contacts`` を呼ぶのは ``seed_initial``・``_reset_slots``・``rebuild_contacts`` だけ。
- 関係の置き場(``engine/relations.py``)の中では、名の分からない書き(``getattr(x, 式)[...] =``)は 0、名の分からない
  差し替え(``setattr`` などの名が式)は実行時の守り ``RelationLayer.__setattr__``・``__delattr__`` の中だけ。

逐次ループ宣言: なし(試験の道具)。
"""

from __future__ import annotations

from pathlib import Path

from tests.engine.ast_writers import UNKNOWN, Write, scan_writes

COLS = frozenset({"contact_flags", "_contact_flags"})
WRITER = "_write_contacts"
REL = "engine/relations.py"

#: 種類ごとに許す所(関数の限定名)。
ALLOWED_CONTENT = frozenset({"RelationLayer._write_contacts"})
ALLOWED_REPLACE = frozenset({"RelationLayer.__init__"})
ALLOWED_CALLERS = frozenset({"RelationLayer.seed_initial", "RelationLayer._reset_slots", "RelationLayer.rebuild_contacts"})
#: 関係の置き場の中で、名の分からない差し替えを許す所(実行時の守り=検収 L1)。
ALLOWED_UNKNOWN_REPLACE = frozenset({"RelationLayer.__setattr__", "RelationLayer.__delattr__"})


def is_col(name: str) -> bool:
    return name in COLS


def scan_source(text: str) -> list[Write]:
    return scan_writes(text, is_col, call_names=frozenset({WRITER}))


def violations(rel: str, text: str) -> list[str]:
    """``rel``(``src/shibuya`` からの道筋)の中の、許す所の外の書き。"""
    out: list[str] = []
    in_rel = rel == REL
    for w in scan_source(text):
        tag = f"{rel}:{w.line} [{w.func}] {w.kind} {w.name} ({w.form})"
        if w.kind == "call":
            if w.func not in ALLOWED_CALLERS or not in_rel:
                out.append(tag)
        elif w.name == UNKNOWN:
            # 名の分からない書きは、関係の置き場の中だけを見る(外の物の名の分からない書きは別の物=各段の道具が見る)
            if in_rel and not (w.kind == "replace" and w.func in ALLOWED_UNKNOWN_REPLACE):
                out.append(tag)
        elif w.kind == "content":
            if w.func not in ALLOWED_CONTENT or not in_rel:
                out.append(tag)
        elif w.kind == "replace":
            if w.func not in ALLOWED_REPLACE or not in_rel:
                out.append(tag)
    return out


def scan_tree(root: Path) -> tuple[list[Write], list[str]]:
    """src の全部: (関係の置き場の書きの全部, 許す所の外の書き)。"""
    root = Path(root)
    rel_writes: list[Write] = []
    bad: list[str] = []
    for p in sorted(root.rglob("*.py")):
        rel = p.relative_to(root).as_posix()
        text = p.read_text(encoding="utf-8")
        if rel == REL:
            rel_writes = scan_source(text)
        bad += violations(rel, text)
    return rel_writes, bad
