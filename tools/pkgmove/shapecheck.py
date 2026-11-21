# -*- coding: utf-8 -*-
"""〔割る段 7 の G0-道具・E1・親の決め事 2〕形の変更の照合: 1 つのファイルの中で 1 つのクラスを 3 つ(枠と基底 2 つ)に分けた
「前」と「後」を、字面と AST で比べ、挙動を変えていないことを確かめる(読むだけ・何も書かない)。

案 A1(親の裁定 Q1・Q2・Q3・Q9): ``Renderer`` を、世界の側 ``PerceptScene``・気づく側 ``SignageNotice``・枠
``Renderer(PerceptScene, SignageNotice)`` に分ける。``__init__`` は世界の側の文を ``PerceptScene.__init__`` へ・心の側の文は
``Renderer.__init__`` に残し、世界の側を先に呼ぶ。クラスの名は :class:`Shape` で渡せる(既定は :data:`A1`)。

確かめる項目(どれか 1 つでも違えば違い=``cli.py shapecheck`` は終了コード 1):

⓪ 台本の前提(:data:`PREMISES`): 前と後のソースで数えて、どれも 0。0 でなければ「前提が崩れた=この台本の照合は、この形を
   守れない」と名指しで止める。
① クラスの外の頂上の文: 前と後で並びも AST も字面も同じ(後に足した基底 2 つのクラスのほか)。**足した import は既定で 0**
   (足す・消す・並べ替えるは違い。足すことを許す文は ``allow_imports``=``--allow-import`` で 1 つずつ名指しする)。基底 2 つは
   枠のクラスの直前に、世界の側・気づく側の順で並ぶ(=元の枠の直前の文の後。計画 §4-5)。
② 前の枠のメソッド(``__init__`` を除く): 後の 3 つのクラスのどれか**ちょうど 1 つ**に在り、AST(docstring・デコレータ・既定の
   引数・注釈を含む)も字面も同じ。後のクラスに前に無いメソッドが無い(世界の側の ``__init__`` のほか)。枠のクラスの docstring・
   デコレータは同じ。枠の基底は ``(世界の側, 気づく側)`` の順・基底 2 つは基底もデコレータも持たない。
③ ``__init__``: 世界の側の ``__init__`` の文と、枠の ``__init__`` の文(基底を呼ぶ 1 文を除く)を合わせた多重集合が、前の
   ``__init__`` の文と同じ(AST と字面)。それぞれの並びは前の並びの部分列。足してよいのは :data:`ALLOWED_ADDITION` の 1 文だけ。
   〔検収の後の直し 中-1〕局所の名(引数の書き換えを含む)を書く文と、前の並びでその後に読む文は、同じ側に在る。世界の側の文が使う
   枠の引数は、世界の側の ``__init__`` の引数に在り、世界の側の ``__init__`` の引数は世界の側の文が使う物だけ。世界の側の
   ``__init__`` はデコレータも ``async`` も持たない。気づく側は ``__init__`` を持たない。
④ 枠の ``__init__`` の引数(名・順・既定の値・注釈・キーワード専用か)・戻り値の注釈・デコレータ・docstring が前と同じ。
⑤ MRO で引ける名(3 つのクラスの本体で結ぶ名の和)が前の枠の名と同じ。基底どうしに同じ名が無い・枠と基底で同じ名は世界の側の
   ``__init__`` だけ(MRO の順に頼る名 0)。
⑥ ``self.x`` に書く属性の名の集合が前と同じ(``__init__`` と、ほかのメソッドの分を分けて比べる)。
⑦ 2 つの側が互いの属性を読まない(親の裁定 Q2 の条件 ①・文どおり両向きとも): 世界の側の ``__init__`` の文が、枠の
   ``__init__`` の側だけで書く属性を読まない・逆も。
⑧ 文字列とバイト列の定数の多重集合が前と後で同じ(後の基底 2 つのクラスと世界の側の ``__init__`` の docstring=新しい docstring は
   除く)。
⑨ 〔検収の後の直し 中-3〕注(``tokenize`` の注): 前の注が、後に同じ字面で在り、付く文が同じ(行の途中の注はその行の文・行の
   全部の注は次に始まる文に付く・次の文が無ければ末尾)。後にだけ在る注は、基底 2 つのクラスの頭(クラスの行の直上か、docstring の
   後の最初の文の前)でだけ許す(出す)。節の区切りの注(:data:`SECTION_RE`)は、付く文を問わず字面の数で比べ、重ねてよい(宣言どおり
   の違いとして数つきで出す)・落とすのは違い。

宣言どおりの違い(親の裁定 Q2 と、節の区切りの注=親の決め・止めない・黙って通さない): :data:`DECLARED` の 3 つ。

台本の前提(:data:`PREMISES`・前と後のソースで数えて 0。今の renderer.py ではどれも 0): 引数の無い ``super()``・``__class__`` の
読み・名前のマングリング(``__x``=2 つの下線で始まり 2 つの下線で終わらない名)が 3 つのクラスの中に無い/``__init__`` の中で
``self`` のメソッドを呼ばない・``hasattr``/``getattr``/``setattr``/``delattr``(self, …)・``vars(self)``・``self.__dict__`` を
使わない・``self`` をほかの呼び出しへ渡さない(基底を呼ぶ 1 文のほか)/``__init__`` で同じ属性を 2 つの文が書かない(2 つの側が同じ
属性を書くことも)/クラスの本体の文はメソッドと docstring だけ/同じ名の def がクラスに 2 つ無い/頂上で同じ名を 2 回結ばない。

台本が見ない物(ほかの確かめで受ける): 実行の挙動の全体(byte-check と範囲の全体の試験)・計画の分け方(どの文とメソッドを
どちらの側に置くか=G-R2 の記録で ``method_table`` と ``counts`` を人が突き合わせる)・``__qualname__`` の変化・固定の表と凍結の
JSON・差し替えの「外すと落ちる」・性能・空行。

後に基底 2 つのクラスが無いときは「形の変更ではない(クラスが 1 つのまま)」と答える(``cli.py`` は終了コード 2=使い方の誤り。
「同じ」とは言わない)。前か後が文法の誤りのときも使い方の誤り(2)。:func:`plan_counts` は、形を変える前の 1 つのファイルから、
計画の分け方(:data:`A1_WORLD_ATTRS` と全ファイルの表 §4 のメソッドの割り先)で数を出す(G-R2 の発注に使う数)。

逐次ループ宣言: なし(道具=1 つのファイルの AST と字句を数回なめるだけ・ランの中では動かない)。
"""
from __future__ import annotations

import ast
import io
import re
import subprocess
import tokenize
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Shape:
    """分け方のクラスの名: 枠・世界の側の基底(``__init__`` を持ち、枠が先に呼ぶ)・気づく側の基底(``__init__`` を持たない)。"""

    frame: str = "Renderer"
    world: str = "PerceptScene"
    notice: str = "SignageNotice"

    @property
    def bases(self) -> tuple[str, str]:
        return (self.world, self.notice)


#: 案 A1(親の裁定 Q1・Q9)。
A1 = Shape()

#: 宣言どおりの違い(親の裁定 Q2 の 2 つと、節の区切りの注を重ねる=親の決め)。止めない・出す。
DECLARED: tuple[str, str, str] = ("引数の誤りが 2 つ以上のときに先に出る例外", "属性の辞書の並び", "節の区切りの注を重ねた")

#: ③ で足してよい文(名指し): 枠の ``__init__`` の docstring の直後に、世界の側の基底の ``__init__`` を 1 回呼ぶ式の文
#: ``<世界の側>.__init__(self, <位置の引数>, <名の引数>=<同じ名>)``。引数は枠の ``__init__`` の引数を同じ名で渡すだけ(世界の側の
#: ``__init__`` の引数を全部・位置は位置で同じ順・キーワード専用は名で)。``super()`` で呼ぶ形・ほかの式・2 回目は許さない。
ALLOWED_ADDITION = "<世界の側>.__init__(self, <位置の引数>, <名の引数>=<同じ名>)"

#: ⑨ 節の区切りの注(字面の数で比べ、重ねてよい)。
SECTION_RE = re.compile(r"^#\s*-{10,}")

#: ⓪ 台本の前提(前と後で数えて、どれも 0 であること)。
PREMISES: tuple[str, ...] = (
    "引数の無い super()", "__class__ の読み", "名前のマングリング", "__init__ の中の self のメソッドの呼び出し",
    "__init__ の中の hasattr/getattr/setattr/delattr(self)・vars(self)・self.__dict__", "__init__ の中で self をほかへ渡す呼び出し",
    "__init__ で同じ属性を書く文が 2 つ以上", "2 つの側が同じ属性を書く", "クラスの本体の文(メソッドと docstring のほか)",
    "同じ名の def が 1 つのクラスに 2 つ", "頂上で同じ名を 2 回結ぶ")

#: 〔計画 §4-2・親の裁定 Q2〕``__init__`` で世界の側に置く文が書く属性(30)。書く属性がこの中だけの文(何も書かない文を含む)を
#: 世界の側、ほかを心の側と数える(:func:`plan_counts`=形を変える前の数え。照合 :func:`check` は後のファイルの置き場を正とする)。
A1_WORLD_ATTRS: frozenset[str] = frozenset({
    "world", "agents", "assets", "clock_fn", "acquaintances", "watched_by", "signage_enabled", "memory_recall",
    "near_tiebreak", "near_order", "near_order_ties", "_near_salt64", "near_tie_breaks", "near_tie_candidates", "_tickc",
    "_focus_target", "acquaintance_fn", "session_partner_fn", "_acq_cache", "_b3_cache", "named_closed_lookup",
    "weather_date_fn", "weather_words_fn", "weather_words_key_fn", "weather_env", "day_kind_fn", "named_closed_notes",
    "signage_exposures", "heard_fn", "contact_fn"})
#: 〔親の裁定 Q1〕全ファイルの表 §4 の割り先 → 側(ほかの割り先は枠)。〔裁定 Q4〕``Renderer.render`` は表の割り先(bridge)でなく枠。
A1_DESTS: dict[str, str] = {"world/model/percept_scene.py": "world", "mind/percept/notice.py": "notice"}
TABLE_REL = "docs/reference/package-map-final-2026-11-09-files.md"


class ShapeError(Exception):
    """読めない・使い方の誤り(文法の誤り・クラスが無い・前に基底が既に在る など)。"""


# ------------------------------------------------------------------ 読む
def read_source(spec: str, repo: Path) -> str:
    """``spec`` がファイルの道ならその中身、``<commit>:<道>`` なら git の blob(``git -C repo show``)。木を写さずに前を読む口。"""
    p = Path(spec)
    if p.is_file():
        return p.read_text(encoding="utf-8")
    if ":" in spec and not re.match(r"^[A-Za-z]:[\\/]", spec):
        r = subprocess.run(["git", "-C", str(repo), "show", spec], capture_output=True)
        if r.returncode != 0:
            raise ShapeError(f"git の blob を読めない: {spec}({r.stderr.decode('utf-8', 'replace').strip()})")
        return r.stdout.decode("utf-8")
    raise ShapeError(f"ファイルが無い: {spec}")


def _parse(text: str, which: str) -> ast.Module:
    try:
        return ast.parse(text)
    except SyntaxError as e:
        raise ShapeError(f"{which}のソースが文法の誤り(行 {e.lineno}: {e.msg})") from e


def _start(node: ast.AST) -> int:
    return min([node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])])


def _seg(lines: list[str], node: ast.AST) -> str:
    """文の字面(最初のデコレータの行から終わりの行まで・行の単位)。"""
    return "".join(lines[_start(node) - 1: node.end_lineno])


def _is_doc(st: ast.stmt) -> bool:
    return isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant) and isinstance(st.value.value, str)


def _split_doc(body: list[ast.stmt]) -> tuple[ast.stmt | None, list[ast.stmt]]:
    return (body[0], body[1:]) if body and _is_doc(body[0]) else (None, list(body))


def _classes(tree: ast.Module) -> dict[str, ast.ClassDef]:
    return {s.name: s for s in tree.body if isinstance(s, ast.ClassDef)}


def _funcs(cls: ast.ClassDef) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    return {m.name: m for m in cls.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))}


def _bound(cls: ast.ClassDef) -> set[str]:
    """クラスの本体で結ぶ名(メソッド・入れ子のクラス・代入の左辺)=インスタンスから MRO で引ける名。"""
    out: set[str] = set()
    for st in cls.body:
        if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(st.name)
        elif isinstance(st, ast.Assign):
            out |= {n.id for t in st.targets for n in ast.walk(t) if isinstance(n, ast.Name)}
        elif isinstance(st, ast.AnnAssign) and isinstance(st.target, ast.Name):
            out.add(st.target.id)
    return out


def _self_attrs(nodes: list[ast.AST], ctx: type) -> set[str]:
    """``self.x`` を ``ctx``(Store=書く・Load=読む)で使う名(``setattr``/``getattr(self, "x")`` の字面の名も)。書くは del も。"""
    want = (ast.Store, ast.Del) if ctx is ast.Store else (ast.Load,)
    out: set[str] = set()
    for node in nodes:
        for x in ast.walk(node):
            if isinstance(x, ast.Attribute) and isinstance(x.value, ast.Name) and x.value.id == "self" and \
                    isinstance(x.ctx, want):
                out.add(x.attr)
            if (isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and len(x.args) >= 2
                    and isinstance(x.args[0], ast.Name) and x.args[0].id == "self" and isinstance(x.args[1], ast.Constant)
                    and isinstance(x.args[1].value, str)):
                if (ctx is ast.Store and x.func.id in ("setattr", "delattr")) or (ctx is ast.Load and x.func.id == "getattr"):
                    out.add(x.args[1].value)
    return out


def _first_writes(stmts: list[ast.stmt]) -> list[str]:
    """文の並びで ``self.x`` に初めて書く属性の並び(属性の辞書の並びの見立て)。"""
    out: list[str] = []
    for st in stmts:
        for x in ast.walk(st):
            if isinstance(x, ast.Attribute) and isinstance(x.value, ast.Name) and x.value.id == "self" and \
                    isinstance(x.ctx, ast.Store) and x.attr not in out:
                out.append(x.attr)
    return out


def _is_subsequence(sub: list[str], seq: list[str]) -> bool:
    it = iter(seq)
    return all(any(x == y for y in it) for x in sub)


def _str_consts(tree: ast.AST, skip: set[int]) -> Counter:
    return Counter((type(n.value).__name__, n.value) for n in ast.walk(tree)
                   if isinstance(n, ast.Constant) and isinstance(n.value, (str, bytes)) and id(n) not in skip)


class _LocalRW(ast.NodeVisitor):
    """〔検収の後の直し 中-1〕文が関数の有効範囲で書く名と読む名(入れ子の有効範囲=ラムダ・内包・入れ子の def とクラスの中で
    結ぶ名は除く。入れ子の中から外の名を読むのは読む名に数える)。"""

    def __init__(self) -> None:
        self.w: set[str] = set()
        self.r: set[str] = set()
        self.shadow: list[set[str]] = []

    def visit_Name(self, n: ast.Name) -> None:
        if isinstance(n.ctx, ast.Load):
            if not any(n.id in s for s in self.shadow):
                self.r.add(n.id)
        elif self.shadow:
            self.shadow[-1].add(n.id)
        else:
            self.w.add(n.id)

    @staticmethod
    def _args(a: ast.arguments) -> set[str]:
        return {x.arg for x in [*a.posonlyargs, *a.args, *a.kwonlyargs, a.vararg, a.kwarg] if x is not None}

    def visit_Lambda(self, n: ast.Lambda) -> None:
        for d in [*n.args.defaults, *[d for d in n.args.kw_defaults if d is not None]]:
            self.visit(d)
        self.shadow.append(self._args(n.args))
        self.visit(n.body)
        self.shadow.pop()

    def visit_FunctionDef(self, n: ast.FunctionDef) -> None:  # 入れ子の def(名は外で結ぶ)
        for d in [*n.decorator_list, *n.args.defaults, *[d for d in n.args.kw_defaults if d is not None]]:
            self.visit(d)
        (self.shadow[-1] if self.shadow else self.w).add(n.name)
        self.shadow.append(self._args(n.args))
        for b in n.body:
            self.visit(b)
        self.shadow.pop()

    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]

    def visit_ClassDef(self, n: ast.ClassDef) -> None:
        for d in [*n.decorator_list, *n.bases, *[k.value for k in n.keywords]]:
            self.visit(d)
        (self.shadow[-1] if self.shadow else self.w).add(n.name)
        self.shadow.append(set())
        for b in n.body:
            self.visit(b)
        self.shadow.pop()

    def _comp(self, n: ast.AST, elts: list[ast.AST]) -> None:
        gens = n.generators  # type: ignore[attr-defined]
        self.visit(gens[0].iter)
        self.shadow.append(set())
        for k, g in enumerate(gens):
            self.visit(g.target)
            if k:
                self.visit(g.iter)
            for c in g.ifs:
                self.visit(c)
        for e in elts:
            self.visit(e)
        self.shadow.pop()

    def visit_ListComp(self, n: ast.ListComp) -> None:
        self._comp(n, [n.elt])

    def visit_SetComp(self, n: ast.SetComp) -> None:
        self._comp(n, [n.elt])

    def visit_GeneratorExp(self, n: ast.GeneratorExp) -> None:
        self._comp(n, [n.elt])

    def visit_DictComp(self, n: ast.DictComp) -> None:
        self._comp(n, [n.key, n.value])


def _local_rw(st: ast.stmt) -> tuple[set[str], set[str]]:
    v = _LocalRW()
    v.visit(st)
    return v.w, v.r


def _arg_names(a: ast.arguments) -> list[str]:
    return [x.arg for x in [*a.posonlyargs, *a.args, *a.kwonlyargs, a.vararg, a.kwarg] if x is not None]


# ------------------------------------------------------------------ 照合
@dataclass
class Result:
    """照合の結果。``checks`` は項目 → 違いの文(空=同じ)。"""

    kind: str = "形の変更"
    checks: dict[str, list[str]] = field(default_factory=dict)
    method_table: dict[str, str] = field(default_factory=dict)
    declared: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    counts: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.kind == "形の変更" and not any(self.checks.values())

    def as_dict(self) -> dict:
        return {"kind": self.kind, "ok": self.ok, "checks": self.checks, "method_table": self.method_table,
                "declared": self.declared, "notes": self.notes, "counts": self.counts}


#: 項目の名(並びは報告の並び)。
ITEMS: tuple[str, ...] = ("⓪ 台本の前提", "① 頂上の文", "② メソッド", "③ __init__ の文", "④ 枠の __init__ の口",
                          "⑤ MRO で引ける名", "⑥ 書く属性", "⑦ 互いの属性を読まない", "⑧ 文字列の定数", "⑨ 注")


def _base_call(st: ast.stmt, shape: Shape) -> ast.Call | None:
    """``<世界の側>.__init__(…)`` の式の文なら、その呼び出し。"""
    if isinstance(st, ast.Expr) and isinstance(st.value, ast.Call):
        f = st.value.func
        if isinstance(f, ast.Attribute) and f.attr == "__init__" and isinstance(f.value, ast.Name) and f.value.id == shape.world:
            return st.value
    return None


def _check_base_call(call: ast.Call, wi: ast.FunctionDef, fi: ast.FunctionDef) -> list[str]:
    """基底を呼ぶ 1 文が :data:`ALLOWED_ADDITION` の形か(世界の側の引数を全部・同じ名で・位置は同じ順=1 対 1)。"""
    errs: list[str] = []
    wa = wi.args
    if wa.vararg or wa.kwarg or wa.posonlyargs:
        errs.append("世界の側の __init__ が *args・**kwargs・位置専用の引数を持つ(受け渡しを名で確かめられない)")
    if wa.defaults or any(d is not None for d in wa.kw_defaults):
        errs.append("世界の側の __init__ の引数が既定の値を持つ(基底を呼ぶ文が全部を渡す形=既定の値は要らない)")
    wpos = [a.arg for a in wa.args]
    wkw = [a.arg for a in wa.kwonlyargs]
    fparams = set(_arg_names(fi.args))
    if not wpos or wpos[0] != "self":
        errs.append("世界の側の __init__ の最初の引数が self でない")
    pos = [a.id if isinstance(a, ast.Name) else None for a in call.args]
    if pos != wpos:
        errs.append(f"基底を呼ぶ文の位置の引数 {pos} が世界の側の __init__ の位置の引数 {wpos} と同じ名・同じ順でない")
    kws = {k.arg: (k.value.id if isinstance(k.value, ast.Name) else None) for k in call.keywords}
    if set(kws) != set(wkw) or any(k != v for k, v in kws.items()):
        errs.append(f"基底を呼ぶ文の名の引数 {kws} が世界の側の __init__ のキーワード専用の引数 {wkw} を同じ名で渡す形でない")
    stray = sorted({x for x in [*pos[1:], *kws.values()] if x is not None} - fparams)
    if stray:
        errs.append(f"基底を呼ぶ文が枠の __init__ の引数でない名 {stray} を渡す")
    return errs


def check(before: str, after: str, shape: Shape = A1, allow_imports: tuple[str, ...] = ()) -> Result:
    """前と後の字面を照合する(:class:`Result`)。文法の誤り・前に基底が在るなどは :class:`ShapeError`。``allow_imports`` は
    後に足してよい import の文(``ast.unparse`` の字面・1 つずつ・既定は無し=足した import は 0)。"""
    tb, ta = _parse(before, "前"), _parse(after, "後")
    lb, la = before.splitlines(keepends=True), after.splitlines(keepends=True)
    cb, ca = _classes(tb), _classes(ta)
    res = Result(checks={k: [] for k in ITEMS})
    if shape.frame not in cb:
        raise ShapeError(f"前にクラス {shape.frame} が無い")
    if any(b in cb for b in shape.bases):
        raise ShapeError(f"前に基底のクラス {[b for b in shape.bases if b in cb]} が既に在る(形を変える前のファイルでない)")
    if shape.frame not in ca:
        raise ShapeError(f"後にクラス {shape.frame} が無い")
    res.counts = _counts_before(tb, shape)
    if not any(b in ca for b in shape.bases):
        res.kind = "形の変更ではない(クラスが 1 つのまま)"
        if before == after:
            res.notes.append("前と後の字面が同じ")
        return res
    missing = [b for b in shape.bases if b not in ca]
    if missing:
        res.checks["② メソッド"].append(f"後に基底のクラス {missing} が無い")
        return res
    F0, F, W, N = cb[shape.frame], ca[shape.frame], ca[shape.world], ca[shape.notice]
    after_cls = {shape.world: W, shape.notice: N, shape.frame: F}
    new_ids = {id(W), id(N)}
    _premises(tb, ta, F0, after_cls, shape, res)
    _top(tb, ta, lb, la, shape, new_ids, allow_imports, res)
    _methods(F0, after_cls, lb, la, shape, res)
    _init(F0, F, W, N, lb, la, shape, res)
    _mro(F0, after_cls, shape, res)
    # ⑧ 文字列の定数(新しい docstring を除く)
    skip: set[int] = set()
    for c in (W, N):
        d, _rest = _split_doc(c.body)
        if d is not None:
            skip.add(id(d.value))
    wi = _funcs(W).get("__init__")
    if wi is not None:
        d, _rest = _split_doc(wi.body)
        if d is not None:
            skip.add(id(d.value))
    sb, sa = _str_consts(tb, set()), _str_consts(ta, skip)
    if sb != sa:
        lost = sorted((sb - sa).elements(), key=repr)[:10]
        extra = sorted((sa - sb).elements(), key=repr)[:10]
        res.checks["⑧ 文字列の定数"].append(f"文字列とバイト列の定数の多重集合が違う(前にだけ {lost}・後にだけ {extra})")
    _comments(before, after, tb, ta, W, N, res)
    return res


# ------------------------------------------------------------------ ⓪ 台本の前提
def _top_bindings(tree: ast.Module) -> Counter:
    """頂上の文(頂上の if・try・with・for・while の中を含む・def とクラスの中は除く)が結ぶ名の数。"""
    out: Counter = Counter()

    def visit(stmts: list[ast.stmt]) -> None:
        for st in stmts:
            if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                out[st.name] += 1
            elif isinstance(st, (ast.Import, ast.ImportFrom)):
                if isinstance(st, ast.ImportFrom) and st.module == "__future__":
                    continue
                for a in st.names:
                    out[a.asname or a.name.split(".")[0]] += 1
            elif isinstance(st, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                tgts = st.targets if isinstance(st, ast.Assign) else [st.target]
                for t in tgts:
                    for n in ast.walk(t):
                        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
                            out[n.id] += 1
            elif isinstance(st, (ast.If, ast.Try, ast.With, ast.For, ast.While)):
                for blk in ("body", "orelse", "finalbody"):
                    visit(getattr(st, blk, []))
                for h in getattr(st, "handlers", []):
                    visit(h.body)
    visit(tree.body)
    return out


def _mangled(name: str) -> bool:
    return name.startswith("__") and not name.endswith("__")


def _premise_counts(classes: list[ast.ClassDef], inits: list[list[ast.stmt]], skip_ids: set[int],
                    tree: ast.Module) -> dict[str, list[str]]:
    """前提ごとの当たり(行と名)。``inits`` は ``__init__`` の本体の文の並び(前は 1 つ・後は世界の側と枠の 2 つ)。"""
    hits: dict[str, list[str]] = {p: [] for p in PREMISES}
    for c in classes:
        for x in ast.walk(c):
            if isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id == "super" and not x.args \
                    and not x.keywords:
                hits[PREMISES[0]].append(f"{c.name} 行 {x.lineno}")
            if isinstance(x, ast.Name) and x.id == "__class__":
                hits[PREMISES[1]].append(f"{c.name} 行 {x.lineno}")
            if isinstance(x, ast.Attribute) and _mangled(x.attr):
                hits[PREMISES[2]].append(f"{c.name} 行 {x.lineno} .{x.attr}")
            if isinstance(x, ast.Name) and _mangled(x.id):
                hits[PREMISES[2]].append(f"{c.name} 行 {x.lineno} {x.id}")
            if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef)) and _mangled(x.name):
                hits[PREMISES[2]].append(f"{c.name} 行 {x.lineno} def {x.name}")
        _d, body = _split_doc(c.body)
        for st in body:
            if not isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef)):
                hits[PREMISES[8]].append(f"{c.name} 行 {st.lineno}")
        names = Counter(st.name for st in body if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef)))
        hits[PREMISES[9]] += [f"{c.name}.{n} × {k}" for n, k in names.items() if k > 1]
    writers: Counter = Counter()
    side_attrs: list[set[str]] = []
    for stmts in inits:
        side: set[str] = set()
        for st in stmts:
            if id(st) in skip_ids:
                continue
            w = _self_attrs([st], ast.Store)
            writers.update(w)
            side |= w
            for x in ast.walk(st):
                if isinstance(x, ast.Call):
                    f = x.func
                    if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id == "self":
                        hits[PREMISES[3]].append(f"行 {x.lineno} self.{f.attr}()")
                    if isinstance(f, ast.Name) and f.id in ("hasattr", "getattr", "setattr", "delattr", "vars") and \
                            x.args and isinstance(x.args[0], ast.Name) and x.args[0].id == "self":
                        hits[PREMISES[4]].append(f"行 {x.lineno} {f.id}(self…)")
                    if any(isinstance(a, ast.Name) and a.id == "self" for a in [*x.args, *[k.value for k in x.keywords]]):
                        hits[PREMISES[5]].append(f"行 {x.lineno}")
                if isinstance(x, ast.Attribute) and x.attr == "__dict__" and isinstance(x.value, ast.Name) and \
                        x.value.id == "self":
                    hits[PREMISES[4]].append(f"行 {x.lineno} self.__dict__")
        side_attrs.append(side)
    hits[PREMISES[6]] += sorted(a for a, k in writers.items() if k > 1)
    if len(side_attrs) == 2:
        hits[PREMISES[7]] += sorted(side_attrs[0] & side_attrs[1])
    hits[PREMISES[10]] += sorted(n for n, k in _top_bindings(tree).items() if k > 1)
    return hits


def _premises(tb: ast.Module, ta: ast.Module, F0: ast.ClassDef, after_cls: dict[str, ast.ClassDef], shape: Shape,
              res: Result) -> None:
    """⓪ 台本の前提(前と後で 0)。"""
    bi = _funcs(F0).get("__init__")
    b_inits = [_split_doc(bi.body)[1]] if bi is not None else []
    a_inits: list[list[ast.stmt]] = []
    skip: set[int] = set()
    for c in (shape.world, shape.frame):
        f = _funcs(after_cls[c]).get("__init__")
        if f is not None:
            body = _split_doc(f.body)[1]
            if c == shape.frame:
                skip |= {id(st) for st in body if _base_call(st, shape) is not None}
            a_inits.append(body)
    for tag, hits in (("前", _premise_counts([F0], b_inits, set(), tb)),
                      ("後", _premise_counts(list(after_cls.values()), a_inits, skip, ta))):
        for p, xs in hits.items():
            if xs:
                res.checks["⓪ 台本の前提"].append(f"前提が崩れた(この台本の照合は、この形を守れない): {p} が{tag}に "
                                                  f"{len(xs)}({xs[:5]})")


# ------------------------------------------------------------------ ① 頂上の文
def _top(tb: ast.Module, ta: ast.Module, lb: list[str], la: list[str], shape: Shape, new_ids: set[int],
         allow_imports: tuple[str, ...], res: Result) -> None:
    """① クラスの外の頂上の文(足した import は既定で 0)と、基底 2 つの置き場。"""
    errs = res.checks["① 頂上の文"]

    def seq(tree: ast.Module, lines: list[str], skip: set[int]) -> list[tuple[str, str]]:
        out = []
        for st in tree.body:
            if id(st) in skip:
                continue
            if isinstance(st, ast.ClassDef) and st.name == shape.frame:
                out.append(("<枠>", "<枠>"))
            else:
                out.append((ast.dump(st), _seg(lines, st)))
        return out

    allowed = list(allow_imports)
    added: list[ast.stmt] = []
    for s in ta.body:
        if isinstance(s, (ast.Import, ast.ImportFrom)) and ast.unparse(s) in allowed:
            allowed.remove(ast.unparse(s))
            added.append(s)
    if added:
        res.notes.append(f"名指しで許した、足した import: {[ast.unparse(s) for s in added]}")
    if allowed:
        errs.append(f"許すと名指しした import {allowed} が後に無い")
    a_seq = seq(ta, la, new_ids | {id(s) for s in added})
    b_seq = seq(tb, lb, set())
    bd, ad = [d for d, _t in b_seq], [d for d, _t in a_seq]
    if ad != bd:
        i = next((k for k in range(min(len(bd), len(ad))) if bd[k] != ad[k]), min(len(bd), len(ad)))
        errs.append(f"クラスの外の頂上の文の並びか AST が違う(前 {len(bd)} 文・後 {len(ad)} 文・最初の違いは {i + 1} 文目。"
                    f"import を足す・消す・並べ替えるのも違い)")
    elif [t for _d, t in a_seq] != [t for _d, t in b_seq]:
        k = next(k for k in range(len(a_seq)) if a_seq[k][1] != b_seq[k][1])
        errs.append(f"クラスの外の頂上の文の字面が違う({k + 1} 文目)")
    # 基底 2 つの置き場: 枠の直前に、世界の側・気づく側の順(=元の枠の直前の文の後)
    names = [s.name if isinstance(s, ast.ClassDef) else None for s in ta.body]
    i_w, i_n, i_f = (names.index(n) for n in (shape.world, shape.notice, shape.frame))
    if not (i_n == i_f - 1 and i_w == i_f - 2):
        errs.append(f"基底 2 つが枠 {shape.frame} の直前に {shape.world}・{shape.notice} の順で並んでいない(頂上の位置 "
                    f"{shape.world} {i_w + 1}・{shape.notice} {i_n + 1}・{shape.frame} {i_f + 1})")


# ------------------------------------------------------------------ ② メソッド
def _methods(F0: ast.ClassDef, after_cls: dict[str, ast.ClassDef], lb: list[str], la: list[str], shape: Shape,
             res: Result) -> None:
    """② メソッド(と、メソッドでない本体の文・枠のクラスの頭)。"""
    errs = res.checks["② メソッド"]
    bm = _funcs(F0)
    am = {c: _funcs(n) for c, n in after_cls.items()}
    for name, m in bm.items():
        if name == "__init__":
            continue
        where = [c for c in am if name in am[c]]
        if len(where) != 1:
            errs.append(f"メソッド {name}: 後のクラス {where} に在る(ちょうど 1 つでない)")
            continue
        res.method_table[name] = where[0]
        n = am[where[0]][name]
        if ast.dump(n) != ast.dump(m):
            errs.append(f"メソッド {name}({where[0]}): AST が違う")
        elif _seg(la, n) != _seg(lb, m):
            errs.append(f"メソッド {name}({where[0]}): 字面が違う")
    for c, fs in am.items():
        extra = sorted(set(fs) - set(bm) - ({"__init__"} if c == shape.world else set()))
        if extra:
            errs.append(f"{c}: 前に無いメソッド {extra}")

    def others(cls: ast.ClassDef) -> Counter:
        _d, rest = _split_doc(cls.body)
        return Counter(ast.dump(s) for s in rest if not isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef)))
    ob = others(F0)
    oa = sum((others(n) for n in after_cls.values()), Counter())
    if ob != oa:
        errs.append(f"メソッドでないクラスの本体の文が違う(前にだけ {sum((ob - oa).values())}・後にだけ {sum((oa - ob).values())})")
    F = after_cls[shape.frame]
    db, _r = _split_doc(F0.body)
    da, _r2 = _split_doc(F.body)
    if (db is None) != (da is None) or (db is not None and (ast.dump(db) != ast.dump(da) or _seg(lb, db) != _seg(la, da))):
        errs.append(f"{shape.frame} のクラスの docstring が違う")
    if [ast.dump(d) for d in F0.decorator_list] != [ast.dump(d) for d in F.decorator_list] or \
            [ast.dump(k) for k in F0.keywords] != [ast.dump(k) for k in F.keywords]:
        errs.append(f"{shape.frame} のクラスのデコレータかキーワードが違う")
    if F0.bases:
        errs.append(f"前の {shape.frame} が基底を持つ(形の変更の前提の外)")
    if [b.id if isinstance(b, ast.Name) else ast.dump(b) for b in F.bases] != list(shape.bases):
        errs.append(f"後の {shape.frame} の基底が {list(shape.bases)} の順でない")
    for c in shape.bases:
        n = after_cls[c]
        if n.bases or n.keywords or n.decorator_list:
            errs.append(f"基底のクラス {c} が基底・キーワード・デコレータを持つ")


# ------------------------------------------------------------------ ③ ④ ⑥ ⑦
def _init(F0: ast.ClassDef, F: ast.ClassDef, W: ast.ClassDef, N: ast.ClassDef, lb: list[str], la: list[str],
          shape: Shape, res: Result) -> None:
    """③ ④ ⑥ ⑦ と、宣言どおりの違い。"""
    e3, e4, e6, e7 = (res.checks[k] for k in ("③ __init__ の文", "④ 枠の __init__ の口", "⑥ 書く属性",
                                              "⑦ 互いの属性を読まない"))
    bi = _funcs(F0).get("__init__")
    fi = _funcs(F).get("__init__")
    wi = _funcs(W).get("__init__")
    if bi is None or fi is None or wi is None:
        e3.append(f"__init__ が無い(前 {bi is not None}・枠 {fi is not None}・世界の側 {wi is not None})")
        return
    if "__init__" in _funcs(N):
        e3.append(f"気づく側 {shape.notice} が __init__ を持つ(呼ばれない)")
    if wi.decorator_list or not isinstance(wi, ast.FunctionDef):
        e3.append(f"世界の側 {shape.world}.__init__ がデコレータか async を持つ")
    b_doc, b_body = _split_doc(bi.body)
    f_doc, f_body = _split_doc(fi.body)
    _w_doc, w_body = _split_doc(wi.body)
    # ④ 枠の __init__ の口
    if ast.dump(bi.args) != ast.dump(fi.args):
        e4.append("枠の __init__ の引数(名・順・既定の値・注釈・キーワード専用か)が違う")
    rb = ast.dump(bi.returns) if bi.returns is not None else None
    ra = ast.dump(fi.returns) if fi.returns is not None else None
    if rb != ra:
        e4.append("枠の __init__ の戻り値の注釈が違う")
    if [ast.dump(d) for d in bi.decorator_list] != [ast.dump(d) for d in fi.decorator_list] or \
            type(bi) is not type(fi):
        e4.append("枠の __init__ のデコレータか種類(async)が違う")
    if (b_doc is None) != (f_doc is None) or (b_doc is not None and (ast.dump(b_doc) != ast.dump(f_doc)
                                                                    or _seg(lb, b_doc) != _seg(la, f_doc))):
        e4.append("枠の __init__ の docstring が違う")
    # ③ 基底を呼ぶ 1 文と、文の多重集合・部分列
    calls = [k for k, st in enumerate(f_body) if _base_call(st, shape) is not None]
    sup = [st for st in f_body if any(isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id == "super"
                                      for x in ast.walk(st))]
    if sup:
        e3.append("枠の __init__ が super() を使う(足してよい文の形の外)")
    if calls != [0]:
        e3.append(f"基底を呼ぶ文 {ALLOWED_ADDITION} が枠の __init__ の docstring の直後に 1 回だけ在る形でない(在る位置 {calls})")
        rest = [st for k, st in enumerate(f_body) if k not in calls]
    else:
        e3 += _check_base_call(_base_call(f_body[0], shape), wi, fi)  # type: ignore[arg-type]
        rest = f_body[1:]
    key = lambda lines, st: (ast.dump(st), _seg(lines, st))  # noqa: E731
    bk = [key(lb, s) for s in b_body]
    wk = [key(la, s) for s in w_body]
    fk = [key(la, s) for s in rest]
    if Counter(d for d, _t in bk) != Counter(d for d, _t in wk) + Counter(d for d, _t in fk):
        cb_, ca_ = Counter(d for d, _t in bk), Counter(d for d, _t in wk) + Counter(d for d, _t in fk)
        e3.append(f"__init__ の文の多重集合の AST が違う(前にだけ {sum((cb_ - ca_).values())}・後にだけ "
                  f"{sum((ca_ - cb_).values())})")
    elif Counter(bk) != Counter(wk) + Counter(fk):
        e3.append("__init__ の文の字面が違う(AST は同じ)")
    bd = [d for d, _t in bk]
    if not _is_subsequence([d for d, _t in wk], bd):
        e3.append(f"世界の側 {shape.world}.__init__ の文の並びが前の並びの部分列でない(順を入れ替えた)")
    if not _is_subsequence([d for d, _t in fk], bd):
        e3.append(f"枠の {shape.frame}.__init__ の文の並びが前の並びの部分列でない(順を入れ替えた)")
    # 前の文ごとの側(後の置き場から)
    pool: dict[str, list[str]] = {}
    for d, _t in wk:
        pool.setdefault(d, []).append("世界")
    for d, _t in fk:
        pool.setdefault(d, []).append("枠")
    order = [pool[d].pop(0) if pool.get(d) else "?" for d in bd]
    # 〔中-1〕(a) 局所の名を書く文と、前の並びでその後に読む文は同じ側
    rw = [_local_rw(s) for s in b_body]
    for j, (_wj, rj) in enumerate(rw):
        for k in range(j):
            shared = sorted(rw[k][0] & rj)
            if shared and order[k] != order[j] and "?" not in (order[k], order[j]):
                e3.append(f"局所の名 {shared} を書く文(前の {k + 1} 文目・{order[k]}の側)と読む文(前の {j + 1} 文目・"
                          f"{order[j]}の側)が別の側に在る")
    # 〔中-1〕(b) 世界の側の文が使う枠の引数と、世界の側の口の引数が同じ
    fparams = set(_arg_names(fi.args)) - {"self"}
    w_used: set[str] = set()
    for st in w_body:
        w_, r_ = _local_rw(st)
        w_used |= (w_ | r_) & fparams
    wparams = set(_arg_names(wi.args)) - {"self"}
    if w_used - wparams:
        e3.append(f"世界の側の文が使う枠の引数 {sorted(w_used - wparams)} を、世界の側の口 {shape.world}.__init__ が受けない")
    if wparams - w_used:
        e3.append(f"世界の側の口 {shape.world}.__init__ の引数 {sorted(wparams - w_used)} を、世界の側の文が使わない")
    # ⑥ 書く属性(__init__ とほか)
    init_b = _self_attrs(b_body, ast.Store)
    init_a = _self_attrs(w_body, ast.Store) | _self_attrs(rest, ast.Store)
    if init_b != init_a:
        e6.append(f"__init__ で書く属性が違う(前にだけ {sorted(init_b - init_a)}・後にだけ {sorted(init_a - init_b)})")
    oth_b = _self_attrs([m for n, m in _funcs(F0).items() if n != "__init__"], ast.Store)
    oth_a = _self_attrs([m for c in (F, W, N) for n, m in _funcs(c).items() if n != "__init__"], ast.Store)
    if oth_b != oth_a:
        e6.append(f"ほかのメソッドで書く属性が違う(前にだけ {sorted(oth_b - oth_a)}・後にだけ {sorted(oth_a - oth_b)})")
    # ⑦ 互いの属性を読まない(裁定 Q2 の文どおり両向き)
    ww, fw = _self_attrs(w_body, ast.Store), _self_attrs(rest, ast.Store)
    wr = _self_attrs(w_body, ast.Load) & (fw - ww)
    fr = _self_attrs(rest, ast.Load) & (ww - fw)
    if wr:
        e7.append(f"世界の側 {shape.world}.__init__ の文が枠の側の属性 {sorted(wr)} を読む")
    if fr:
        e7.append(f"枠の側 {shape.frame}.__init__ の文が世界の側の属性 {sorted(fr)} を読む")
    res.counts.update({"world_init": len(w_body), "frame_init": len(rest), "attrs_init": len(init_a),
                       "world_init_params": len(wparams)})
    # 宣言どおりの違い(止めない)
    switches = sum(1 for k in range(1, len(order)) if order[k] != order[k - 1])
    checks_b = [ast.unparse(s).split("\n")[0][:80] for s in b_body if _raises_or_checks(s)]
    if switches > 1:
        res.declared.append(f"{DECLARED[0]}: __init__ の文の並びが変わった(前は 2 つの側が {switches} 回入れ替わる・後は "
                            f"{shape.world} の側が先)。誤りを出しうる文(前の並び・raise・check_*・parse を呼ぶ文だけを拾う="
                            f"全部ではない): {checks_b}")
    fb = _first_writes(b_body)
    fa = _first_writes(w_body) + [x for x in _first_writes(rest) if x not in _first_writes(w_body)]
    if fb != fa:
        moved = sum(1 for k in range(min(len(fb), len(fa))) if fb[k] != fa[k])
        res.declared.append(f"{DECLARED[1]}: __init__ で初めて書く属性の並びが変わった(属性 {len(fb)} のうち位置の違う {moved})")


def _raises_or_checks(st: ast.stmt) -> bool:
    """引数の誤りを出しうる文(``raise``・``check_*``・``parse`` を呼ぶ)。"""
    for x in ast.walk(st):
        if isinstance(x, ast.Raise):
            return True
        if isinstance(x, ast.Call):
            f = x.func
            name = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
            if name.startswith("check_") or name == "parse":
                return True
    return False


# ------------------------------------------------------------------ ⑤
def _mro(F0: ast.ClassDef, after_cls: dict[str, ast.ClassDef], shape: Shape, res: Result) -> None:
    """⑤ MRO で引ける名・基底どうしと枠との同じ名。"""
    errs = res.checks["⑤ MRO で引ける名"]
    nb = _bound(F0)
    names = {c: _bound(n) for c, n in after_cls.items()}
    na = set().union(*names.values())
    if nb != na:
        errs.append(f"MRO で引ける名が違う(前にだけ {sorted(nb - na)}・後にだけ {sorted(na - nb)})")
    both = names[shape.world] & names[shape.notice]
    if both:
        errs.append(f"基底どうしに同じ名 {sorted(both)}(MRO の順に頼る名)")
    fw = (names[shape.frame] & names[shape.world]) - {"__init__"}
    fn = names[shape.frame] & names[shape.notice]
    if fw or fn:
        errs.append(f"枠と基底に同じ名 {sorted(fw | fn)}(枠が基底を隠す=MRO の順に頼る名)")
    res.counts["base_same_names"] = len(both)


# ------------------------------------------------------------------ ⑨ 注
def _comment_list(text: str) -> list[tuple[int, str, bool]]:
    """注(行・前後の空白を落とした字面・行の途中の注か)。"""
    out: list[tuple[int, str, bool]] = []
    lines = text.splitlines()
    for tok in tokenize.generate_tokens(io.StringIO(text).readline):
        if tok.type == tokenize.COMMENT:
            row, col = tok.start
            out.append((row, tok.string.strip(), bool(lines[row - 1][:col].strip())))
    return out


def _stmt_key(st: ast.stmt) -> tuple:
    if isinstance(st, ast.ClassDef):
        return ("class", st.name)
    if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return ("def", st.name)
    return ("stmt", ast.dump(st))


def _attach(tree: ast.Module, comments: list[tuple[int, str, bool]]) -> list[tuple[str, tuple, int]]:
    """注ごとの (字面, 付く文の鍵, 行)。行の途中の注はその行を含む最も内の文・行の全部の注は次に始まる文(同じ行に始まる文が
    2 つ以上なら外の文)・次の文が無ければ末尾。"""
    stmts = [n for n in ast.walk(tree) if isinstance(n, ast.stmt)]
    starts = sorted(stmts, key=lambda s: (_start(s), -s.end_lineno))
    out: list[tuple[str, tuple, int]] = []
    for row, text, inline in comments:
        if inline:
            inner = [s for s in stmts if _start(s) <= row <= s.end_lineno]
            st = max(inner, key=lambda s: (_start(s), -s.end_lineno)) if inner else None
        else:
            st = next((s for s in starts if _start(s) > row), None)
        out.append((text, _stmt_key(st) if st is not None else ("end",), row))
    return out


def _comments(before: str, after: str, tb: ast.Module, ta: ast.Module, W: ast.ClassDef, N: ast.ClassDef,
              res: Result) -> None:
    """⑨ 注: 前の注が後に同じ字面で在り、付く文が同じ。後にだけ在る注は基底 2 つの頭でだけ許す。節の区切りは字面の数で。"""
    errs = res.checks["⑨ 注"]
    cb, ca = _attach(tb, _comment_list(before)), _attach(ta, _comment_list(after))
    sec_b = Counter(t for t, _k, _r in cb if SECTION_RE.match(t))
    sec_a = Counter(t for t, _k, _r in ca if SECTION_RE.match(t))
    lost = sec_b - sec_a
    if lost:
        errs.append(f"節の区切りの注を落とした {sorted(lost.elements())[:5]}")
    more = sec_a - sec_b
    if more:
        res.declared.append(f"{DECLARED[2]}: {sum(more.values())} 行({sorted(more.elements())[:5]})")
    pool: dict[tuple, list[int]] = {}
    for t, k, r in ca:
        if not SECTION_RE.match(t):
            pool.setdefault((t, k), []).append(r)
    missing = []
    for t, k, r in cb:
        if SECTION_RE.match(t):
            continue
        if pool.get((t, k)):
            pool[(t, k)].pop(0)
        else:
            missing.append((r, t, k))
    if missing:
        errs.append(f"前の注が後に同じ字面で無いか、付く文が違う {len(missing)}(前の行 {[m[0] for m in missing[:8]]}・"
                    f"{[m[1][:30] for m in missing[:3]]})")
    # 後にだけ在る注: 基底 2 つの頭(クラスの行の直上=クラスに付く注か、docstring の後の最初の文の前)だけ許す
    heads = []
    for c in (W, N):
        _d, rest = _split_doc(c.body)
        first = _start(rest[0]) if rest else c.end_lineno + 1
        heads.append((c.name, _start(c), first))
    allowed, bad = [], []
    for (t, k), rows in pool.items():
        for r in rows:
            in_head = any(k == ("class", name) or lo <= r < first for name, lo, first in heads)
            (allowed if in_head else bad).append((r, t))
    if bad:
        errs.append(f"後にだけ在る注 {len(bad)}(基底の頭のほか・後の行 {[b[0] for b in sorted(bad)[:8]]}・"
                    f"{[b[1][:30] for b in sorted(bad)[:3]]})")
    if allowed:
        res.notes.append(f"基底の頭に足した注 {len(allowed)}: {[a[1][:40] for a in sorted(allowed)]}")


def _counts_before(tb: ast.Module, shape: Shape) -> dict:
    """前の枠の数(メソッド・``__init__`` の文・``__init__`` で書く属性)。"""
    F0 = _classes(tb)[shape.frame]
    bi = _funcs(F0).get("__init__")
    body = _split_doc(bi.body)[1] if bi is not None else []
    return {"methods": len(_funcs(F0)), "init_statements": len(body), "attrs_init_before": len(_self_attrs(body, ast.Store))}


# ------------------------------------------------------------------ 計画の数え(形を変える前の 1 つのファイルから)
def table_method_sides(table_text: str, src_rel: str, shape: Shape = A1) -> dict[str, str]:
    """全ファイルの表 §4 の ``src_rel`` の節から、``<枠か基底>.<メソッド>`` の割り先を側(world・notice・frame)にして返す
    (:data:`A1_DESTS` に無い割り先は枠。〔裁定 Q4〕表に無い名は呼ぶ側が枠と数える)。"""
    m = re.search(r"^### 4-\d+ `" + re.escape(src_rel) + r"`\n(.*?)(?=^### |\Z)", table_text, re.S | re.M)
    if m is None:
        raise ShapeError(f"全ファイルの表 §4 に {src_rel} の節が無い")
    prefixes = tuple(c + "." for c in (shape.frame, *shape.bases))
    out: dict[str, str] = {}
    for row in m.group(1).splitlines():
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if len(cells) < 4 or not cells[0].startswith("`"):
            continue
        dest = cells[0].strip("`")
        side = A1_DESTS.get(dest, "frame")
        for name in re.findall(r"`([^`]+)`", re.sub(r"〔.*?〕", "", cells[3])):
            if name.startswith(prefixes):
                out[name.split(".", 1)[1]] = side
    return out


def plan_counts(text: str, sides: dict[str, str], world_attrs: frozenset[str] = A1_WORLD_ATTRS,
                shape: Shape = A1) -> dict:
    """形を変える前の 1 つのファイルから、計画の分け方の数を出す: 世界の側と心の側の ``__init__`` の文・``__init__`` で書く属性・
    メソッド・側ごとのメソッド・基底どうしの同じ名・2 つの側が互いの属性を読むか・世界の側の ``__init__`` が使う引数。表から読んだ
    名がソースのメソッドに無い・世界の側か気づく側のメソッドが表から 1 つも読めないときは :class:`ShapeError`(黙って数えない)。"""
    tb = _parse(text, "前")
    cls = _classes(tb)
    if shape.frame not in cls or any(b in cls for b in shape.bases):
        raise ShapeError("形を変える前のファイルでない(枠が無いか、基底が既に在る)")
    F0 = cls[shape.frame]
    fs = _funcs(F0)
    stray = sorted(set(sides) - set(fs))
    if stray:
        raise ShapeError(f"全ファイルの表 §4 から読んだ名 {stray[:8]} がソースの {shape.frame} のメソッドに無い(表の名が変わった?)")
    for need in ("world", "notice"):
        if need not in set(sides.values()):
            raise ShapeError(f"全ファイルの表 §4 から {need} の側のメソッドを 1 つも読めない(表の名が変わった?)")
    _d, body = _split_doc(fs["__init__"].body)
    world = [s for s in body if _self_attrs([s], ast.Store) <= world_attrs]
    mind = [s for s in body if s not in world]
    ww, mw = _self_attrs(world, ast.Store), _self_attrs(mind, ast.Store)
    side_of = {n: sides.get(n, "frame") for n in fs if n != "__init__"}
    by = Counter(side_of.values())
    names_w = {n for n, s in side_of.items() if s == "world"} | {"__init__"}
    names_n = {n for n, s in side_of.items() if s == "notice"}
    params = [a for a in _arg_names(fs["__init__"].args) if a != "self"]
    used: set[str] = set()
    for s in world:
        w_, r_ = _local_rw(s)
        used |= w_ | r_
    return {
        "methods": len(fs), "init_statements": len(body), "world_init": len(world), "frame_init": len(mind),
        "attrs_init": len(_self_attrs(body, ast.Store)), "world_attrs": len(ww), "frame_attrs": len(mw),
        "methods_by_side": {"world": by.get("world", 0), "notice": by.get("notice", 0), "frame": by.get("frame", 0) + 1},
        "base_same_names": len(names_w & names_n),
        "world_reads_frame_attrs": sorted(_self_attrs(world, ast.Load) & (mw - ww)),
        "frame_reads_world_attrs": sorted(_self_attrs(mind, ast.Load) & (ww - mw)),
        "world_init_params": [p for p in params if p in used],
    }


def render_text(res: Result) -> str:
    """人が読む文。"""
    out = [f"形: {res.kind}"]
    if res.kind == "形の変更":
        for k in ITEMS:
            v = res.checks.get(k, [])
            out.append(f"{k}: {'同じ' if not v else '違う'}")
            out += [f"    {x}" for x in v]
        by = Counter(res.method_table.values())
        out.append(f"メソッドの置き場: {dict(sorted(by.items()))}(__init__ を除く {len(res.method_table)})")
    out += [f"宣言どおりの違い: {x}" for x in res.declared] or ["宣言どおりの違い: 無し"]
    out += [f"見張り: {x}" for x in res.notes]
    out.append(f"数: {res.counts}")
    out.append("照合: 同じ" if res.ok else ("照合: 形の変更ではない" if res.kind != "形の変更" else "照合: 違う"))
    return "\n".join(out)
