"""第 1 期 1-8b 発話の口: 未読の列と計器を書くのは口だけ(検収 低3・静的な検査)。

共通の道具 ``tests/engine/ast_writers.py``(1-7 で入った書く口の AST の道具)で、``inbox``・``meter``・``_last_input`` の中身の
書き・差し替え(``setattr`` などを含む)を ``src/shibuya`` の全部から集め、``engine/speech/port.py`` の ``SpeechPort`` の口
(``__init__``・``say``・``take_heard``・``report_shown``・``take_input_ids``・``note``)の外に無いことを見る。道具の数える形の外
(辞書と list のメソッド ``setdefault``・``append``・``pop``・``clear``・``update`` など)は、ここで足した小さな走査で同じく見る。
負の対照: 外の場所に書きを植えると見つかる。

名の衝突: ``meter`` は 1-8 J0 の ``DecisionLayer.meter``・1-9 の ``TransferMeter``(``ledger.money.meter``)にもある=それぞれの
持ち主の置き場の中の書きは 1-8b の対象の外(持ち主の置き場で分ける)。
"""

from __future__ import annotations

import ast
from pathlib import Path

from tests.engine.ast_writers import UNKNOWN, scan_writes

SRC = Path(__file__).resolve().parents[3] / "src" / "shibuya"
PORT = "engine/speech/port.py"
#: 〔1-3 の (1) の直し〕口の目印 → 記録の id の診断の表(S8E)と渡した発話の控え(S8M)も同じく口だけが書く。
COLS = frozenset({"inbox", "meter", "_last_input", "_mark_event_of", "_heard_taken"})
#: 口の中だけで書いてよい(持ち主のメソッド)。
ALLOWED = frozenset({"SpeechPort.__init__", "SpeechPort.say", "SpeechPort._write", "SpeechPort.take_heard",
                     "SpeechPort.report_shown", "SpeechPort.event_ids", "SpeechPort._forget_mark",
                     "SpeechPort.take_input_ids", "SpeechPort.note", "SpeechPort.__setattr__", "SpeechPort.__delattr__"})
#: 同じ名の欄を持つ別の持ち主の置き場(1-8b の対象の外)。
OTHER_OWNERS = frozenset({"engine/decision/layer.py", "economy/ops.py", "economy/ledger.py"})
DICT_MUTATORS = frozenset({"setdefault", "append", "pop", "popitem", "clear", "update", "extend", "insert", "remove",
                           "__setitem__", "__delitem__"})


class _Methods(ast.NodeVisitor):
    """``X.<列>.<変えるメソッド>(...)`` を集める(関数の限定名・列・行)。"""

    def __init__(self) -> None:
        self.stack: list[str] = []
        self.out: list[tuple[str, str, int]] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]

    def visit_Delete(self, node: ast.Delete) -> None:
        for t in node.targets:  # ``del X.<列>[...]``
            if isinstance(t, ast.Subscript) and isinstance(t.value, ast.Attribute) and t.value.attr in COLS:
                self.out.append((".".join(self.stack[:2]) or "<module>", t.value.attr, node.lineno))
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        f = node.func
        if isinstance(f, ast.Attribute) and f.attr in DICT_MUTATORS and isinstance(f.value, ast.Attribute) \
                and f.value.attr in COLS:
            self.out.append((".".join(self.stack[:2]) or "<module>", f.value.attr, node.lineno))
        self.generic_visit(node)


def _violations(rel: str, text: str) -> list[str]:
    if rel in OTHER_OWNERS:
        return []
    bad: list[str] = []
    in_port = rel == PORT
    for w in scan_writes(text, lambda n: n in COLS):
        if w.name == UNKNOWN and not in_port:
            continue  # 名の分からない書きは各段の道具が見る(口の置き場の中だけを見る)
        if not (in_port and w.func in ALLOWED):
            bad.append(f"{rel}:{w.line} [{w.func}] {w.kind} {w.name} ({w.form})")
    v = _Methods()
    v.visit(ast.parse(text))
    for func, col, line in v.out:
        if not (in_port and func in ALLOWED):
            bad.append(f"{rel}:{line} [{func}] method {col}")
    return bad


def test_only_the_port_writes_the_queue_and_the_meter():
    bad: list[str] = []
    for p in sorted(SRC.rglob("*.py")):
        rel = p.relative_to(SRC).as_posix()
        bad += _violations(rel, p.read_text(encoding="utf-8"))
    assert bad == [], "\n".join(bad)


def test_the_port_itself_has_writes_that_the_scan_sees():
    text = (SRC / PORT).read_text(encoding="utf-8")
    funcs = {w.func for w in scan_writes(text, lambda n: n in COLS)}
    v = _Methods()
    v.visit(ast.parse(text))
    funcs |= {f for f, _c, _l in v.out}
    assert {"SpeechPort.say", "SpeechPort.take_heard", "SpeechPort.report_shown"} <= funcs


def test_negative_control_planted_writes_are_found():
    planted = (
        "def f(port, a):\n"
        "    port.inbox[a] = []\n"
        "    port.meter['said'] += 1\n"
        "    port.inbox.setdefault(a, []).append(1)\n"
        "    port._last_input.pop(a, None)\n"
        "    del port.inbox[a]\n"
    )
    bad = _violations("engine/speech/layer.py", planted)
    assert {int(b.split(":")[1].split(" ")[0]) for b in bad} == {2, 3, 4, 5, 6}, bad
    assert _violations("engine/speech/layer.py", "def g(port):\n    return port.observed()\n") == []
