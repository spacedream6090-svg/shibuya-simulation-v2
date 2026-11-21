"""〔割る段 7 の G0-道具・E1・親の決め事 2〕形の変更の照合の台本(``tools/pkgmove/shapecheck.py``・``cli.py shapecheck``)の試験。

- 見本のソース(小さな ``Renderer``=メソッド 3・``__init__`` の文 10 が 2 つの側に分かれる・局所の名の組・注・節の区切り)で、
  正しい形の変更は通る(宣言どおりの違いは出る・止めない)。
- 植えた変異で落ちる(1 つずつ・落ちる項目を名指し)。〔検収の後の直し〕検収役の「台本は同じ・挙動は違う」の形(局所の名の組・
  世界の側の口の引数・足した import・注・super()・__class__・マングリング・台本の前提・世界の側の __init__ のデコレータと async・
  基底の置き場・同じ名の def)を足した。
- 本物の renderer.py(段 7 の G-R1 の後の commit ``dc496d7`` の blob に止めた=G-R2 は ``dc496d7`` の後の renderer.py から始まる):
  前=後は「形の変更ではない」(cli は終了コード 2・同じとは言わない)。計画の数を台本が数える。計画の分け方で作った A1 の形
  (文を前の注ごと動かす)は ⓪〜⑨ とも同じで、変異(本文 1 字・``near_salt`` の 2 文を 2 つの側に分ける・世界の側の口の引数を
  漏らす)を植えると落ちる。git が無い・commit が無いところでは本物の分は飛ばす(環境変数 ``CI`` が在れば飛ばさずに落とす)。
"""
from __future__ import annotations

import ast
import os
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_TOOLS = ROOT / "tools"
if str(_TOOLS) not in sys.path:  # 末尾に足す(tools の下の名が入れた包みを隠さないように)
    sys.path.append(str(_TOOLS))

from pkgmove import shapecheck as SC  # noqa: E402

CLI_PY = ROOT / "tools" / "pkgmove" / "cli.py"
#: 本物の renderer.py と全ファイルの表を読む commit(段 7 の G-R1 の後=G-R2 の前の renderer.py)。
PIN = "dc496d7"
RENDERER = "src/shibuya/perception/renderer.py"
SEP_W = "    # ------------------------------------------------------------ 世界の側\n"
SEP_N = "    # ------------------------------------------------------------ 気づく側\n"

BEFORE = '''"""mod — 形の変更の照合の見本。"""

from __future__ import annotations

import math

X = "x"
Z = 3


def helper(v):
    return v


#: 枠の注。
class Renderer:
    """枠。"""

    def __init__(self, world, agents, seed=1, *, mode="a", near=None):
        """作る。"""
        #: 世界
        self.world = world
        self.mode = mode  # 心の側の口
        self.agents = agents
        self.wid = id(self.world)
        #: 数
        self.count = 0
        self.half = self.count // 2
        if near is None:
            near = 0
        self.near = near
        if seed < 0:
            raise ValueError("seed")
        self.seed = seed

''' + SEP_W + '''    def perceive(self):
        """世界の側。"""
        return self.world, self.agents, self.near, math.pi

''' + SEP_N + '''    def _sign(self):
        return "sign"

    def draw(self):
        self.count += 1  # 数える
        return f"{self.mode}:{self.count}:{X}"


Y = b"y"
'''

PS = '''class PerceptScene:
    """世界の側。"""

    def __init__(self, world, agents, *, near):
        """世界の側の欄。"""
        #: 世界
        self.world = world
        self.agents = agents
        self.wid = id(self.world)
        if near is None:
            near = 0
        self.near = near

''' + SEP_W + '''    def perceive(self):
        """世界の側。"""
        return self.world, self.agents, self.near, math.pi
'''

SN = '''class SignageNotice:
    """気づく側。"""

''' + SEP_N + '''    def _sign(self):
        return "sign"
'''

HEAD = '''"""mod — 形の変更の照合の見本。"""

from __future__ import annotations

import math

X = "x"
Z = 3


def helper(v):
    return v


'''

FRAME = '''#: 枠の注。
class Renderer(PerceptScene, SignageNotice):
    """枠。"""

    def __init__(self, world, agents, seed=1, *, mode="a", near=None):
        """作る。"""
        PerceptScene.__init__(self, world, agents, near=near)
        self.mode = mode  # 心の側の口
        #: 数
        self.count = 0
        self.half = self.count // 2
        if seed < 0:
            raise ValueError("seed")
        self.seed = seed

    def draw(self):
        self.count += 1  # 数える
        return f"{self.mode}:{self.count}:{X}"


Y = b"y"
'''

AFTER = HEAD + PS + "\n\n" + SN + "\n\n" + FRAME
_M = "PerceptScene.__init__(self, world, agents, near=near)\n"
_WSIG = "    def __init__(self, world, agents, *, near):\n"
_NEAR_IF = "        if near is None:\n            near = 0\n"


def _sub(text: str, old: str, new: str) -> str:
    assert text.count(old) == 1, (old, text.count(old))
    return text.replace(old, new)


def _failing(res: SC.Result) -> list[str]:
    return [k for k, v in res.checks.items() if v]


def run_cli(*args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run([sys.executable, str(CLI_PY), *args], capture_output=True, text=True, encoding="utf-8",
                          errors="replace", env=env, cwd=str(ROOT))


# ------------------------------------------------------------------ 見本
def test_a_correct_shape_change_passes_and_names_the_declared_differences():
    """正しい形の変更は ⓪〜⑨ とも「同じ」。メソッドの置き場の表が出る。宣言どおりの違い 2 つ(先に出る例外・属性の辞書の並び)は
    止めずに中身つきで出る(誤りを出しうる文の一覧が全部でない旨も)。"""
    res = SC.check(BEFORE, AFTER)
    assert res.kind == "形の変更" and res.ok, SC.render_text(res)
    assert res.method_table == {"perceive": "PerceptScene", "_sign": "SignageNotice", "draw": "Renderer"}
    assert len(res.declared) == 2 and res.declared[0].startswith(SC.DECLARED[0]) and res.declared[1].startswith(SC.DECLARED[1])
    assert "if seed < 0:" in res.declared[0] and "全部ではない" in res.declared[0], res.declared
    assert res.counts["world_init"] == 5 and res.counts["frame_init"] == 5 and res.counts["world_init_params"] == 3
    assert res.counts["base_same_names"] == 0 and "照合: 同じ" in SC.render_text(res)
    assert list(res.checks) == list(SC.ITEMS) and len(SC.ITEMS) == 10


def test_an_unchanged_file_is_not_called_a_shape_change():
    """前=後(クラスが 1 つのまま)は「形の変更ではない」(ok でない・同じとは言わない)。前に基底が既に在る・枠が無い・文法の誤りは
    使い方の誤り。"""
    res = SC.check(BEFORE, BEFORE)
    assert res.kind == "形の変更ではない(クラスが 1 つのまま)" and not res.ok and "前と後の字面が同じ" in res.notes
    with pytest.raises(SC.ShapeError, match="基底のクラス"):
        SC.check(AFTER, AFTER)
    with pytest.raises(SC.ShapeError, match="クラス Renderer が無い"):
        SC.check(BEFORE.replace("class Renderer:", "class Other:"), AFTER)
    with pytest.raises(SC.ShapeError, match="後のソースが文法の誤り"):
        SC.check(BEFORE, AFTER.replace("def draw(self):", "def draw(self)"))


def _both(old: str, new: str):
    """前と後の両方に同じ書き換えを当てる(台本の前提の変異=前でも後でも数える)。"""
    return (lambda t: _sub(t, old, new), lambda t: _sub(t, old, new))


#: 植えた変異(名 → (前を変える関数か None, 後を変える関数, 落ちる項目))。
MUTATIONS = {
    # ---- 前からの 18
    "メソッドの本文を 1 字変える": (None, lambda t: _sub(t, "self.near, math.pi", "self.nea, math.pi"), "② メソッド"),
    "メソッドを 2 つのクラスに重ねる": (None, lambda t: _sub(t, SEP_W, '    def _sign(self):\n        return "sign"\n\n' + SEP_W),
                                       "② メソッド"),
    "メソッドを落とす": (None, lambda t: _sub(t, '    def draw(self):\n        self.count += 1  # 数える\n        return f"{self.mode}:'
                                              '{self.count}:{X}"\n', ""), "② メソッド"),
    "__init__ の文の順を入れ替える": (None, lambda t: _sub(t, "        self.mode = mode  # 心の側の口\n        #: 数\n        "
                                                           "self.count = 0\n", "        #: 数\n        self.count = 0\n"
                                                           "        self.mode = mode  # 心の側の口\n"), "③ __init__ の文"),
    "__init__ の文を 1 つ落とす": (None, lambda t: _sub(t, "        self.half = self.count // 2\n", ""), "③ __init__ の文"),
    "__init__ の文を 1 つ足す": (None, lambda t: _sub(t, "        self.seed = seed\n", "        self.seed = seed\n        self.extra = 1\n"),
                              "③ __init__ の文"),
    "基底の 2 つに同じ名のメソッドを置く": (None, lambda t: _sub(_sub(t, SEP_N, "    def shared(self):\n        return 1\n\n" + SEP_N),
                                                                  SEP_W, "    def shared(self):\n        return 1\n\n" + SEP_W),
                                          "⑤ MRO で引ける名"),
    "属性の名を変える": (None, lambda t: t.replace("self.count", "self.cnt"), "⑥ 書く属性"),
    "世界の側が心の側の属性を読む": (None, lambda t: _sub(_sub(t, "        self.half = self.count // 2\n", ""),
                                                         "        self.wid = id(self.world)\n",
                                                         "        self.wid = id(self.world)\n        self.half = self.count // 2\n"),
                                      "⑦ 互いの属性を読まない"),
    "心の側が世界の側の属性を読む": (None, lambda t: _sub(_sub(t, "        self.wid = id(self.world)\n", ""),
                                                         "        self.mode = mode  # 心の側の口\n",
                                                         "        self.mode = mode  # 心の側の口\n        self.wid = id(self.world)\n"),
                                      "⑦ 互いの属性を読まない"),
    "文字列の定数を 1 字変える": (None, lambda t: _sub(t, 'return "sign"', 'return "sigm"'), "⑧ 文字列の定数"),
    "Renderer.__init__ の引数の既定の値を変える": (None, lambda t: _sub(t, "seed=1, *,", "seed=2, *,"), "④ 枠の __init__ の口"),
    "クラスの外の頂上の文を変える": (None, lambda t: _sub(t, "Z = 3\n", "Z = 4\n"), "① 頂上の文"),
    "基底を呼ぶ文を super() にする": (None, lambda t: _sub(t, _M, "super().__init__(world, agents, near=near)\n"), "③ __init__ の文"),
    "基底を呼ぶ文が引数を 1 つ渡さない": (None, lambda t: _sub(t, _M, "PerceptScene.__init__(self, world, agents)\n"),
                                           "③ __init__ の文"),
    "気づく側に __init__ を置く": (None, lambda t: _sub(t, SEP_N, "    def __init__(self):\n        pass\n\n" + SEP_N), "③ __init__ の文"),
    "枠の基底の順を入れ替える": (None, lambda t: _sub(t, "class Renderer(PerceptScene, SignageNotice):",
                                                     "class Renderer(SignageNotice, PerceptScene):"), "② メソッド"),
    "メソッドの中の注を変える(字面だけ)": (None, lambda t: _sub(t, "# 数える", "# 数えた"), "② メソッド"),
    # ---- 〔検収の後の直し 中-1〕局所の名の組・世界の側の口の引数
    "局所の名を書く文を枠へ(読む文は世界の側)": (None, lambda t: _sub(_sub(t, _NEAR_IF, ""), "        if seed < 0:\n",
                                                                    _NEAR_IF + "        if seed < 0:\n"), "③ __init__ の文"),
    "局所の名を読む文を枠へ(書く文は世界の側)": (None, lambda t: _sub(_sub(t, "        self.near = near\n", ""), "        if seed < 0:\n",
                                                                    "        self.near = near\n        if seed < 0:\n"),
                                                 "③ __init__ の文"),
    "世界の側の口が、世界の側の文の使う引数を受けない": (None, lambda t: _sub(_sub(t, _WSIG, "    def __init__(self, world, agents):\n"),
                                                                        _M, "PerceptScene.__init__(self, world, agents)\n"),
                                                         "③ __init__ の文"),
    "世界の側の口に、世界の側の文が使わない引数": (None, lambda t: _sub(_sub(t, _WSIG,
                                                                          "    def __init__(self, world, agents, seed, *, near):\n"),
                                                                     _M, "PerceptScene.__init__(self, world, agents, seed, near=near)\n"),
                                                  "③ __init__ の文"),
    "世界の側の口の引数に既定の値": (None, lambda t: _sub(t, _WSIG, "    def __init__(self, world, agents, *, near=None):\n"),
                                     "③ __init__ の文"),
    # ---- 〔中-2〕足した import(既定で 0)
    "足した import が組み込みの名を隠す": (None, lambda t: _sub(t, "import math\n", "import math\nfrom builtins import id as len\n"),
                                           "① 頂上の文"),
    "足した import が頂上の名を隠す": (None, lambda t: _sub(t, "import math\n", "import math\nfrom math import floor as helper\n"),
                                       "① 頂上の文"),
    "注釈にだけ要る import を足す(名指しなし)": (None, lambda t: _sub(t, "import math\n", "import math\nfrom typing import Any\n"),
                                                 "① 頂上の文"),
    # ---- 〔中-3〕⑨ 注
    "__init__ の文の前の注を落とす": (None, lambda t: _sub(t, "        #: 数\n", ""), "⑨ 注"),
    "注をずらす(別の文に付く)": (None, lambda t: _sub(_sub(t, "        #: 数\n", ""), "        self.half = self.count // 2\n",
                                                     "        #: 数\n        self.half = self.count // 2\n"), "⑨ 注"),
    "注の字面を変える": (None, lambda t: _sub(t, "#: 世界\n", "#: 世界の\n"), "⑨ 注"),
    "後にだけ在る注(基底の頭のほか)": (None, lambda t: _sub(t, "        self.seed = seed\n", "        # 足した\n        self.seed = seed\n"),
                                        "⑨ 注"),
    "節の区切りの注を落とす": (None, lambda t: _sub(t, SEP_N, ""), "⑨ 注"),
    "枠の上の注を基底の上へずらす": (None, lambda t: _sub(_sub(t, "#: 枠の注。\n", ""), "class PerceptScene:",
                                                         "#: 枠の注。\nclass PerceptScene:"), "⑨ 注"),
    "行の途中の注を落とす": (None, lambda t: _sub(t, "  # 心の側の口", ""), "⑨ 注"),
    # ---- 〔安い低〕世界の側の __init__ のデコレータ・async・基底の置き場
    "世界の側の __init__ にデコレータ": (None, lambda t: _sub(t, _WSIG, "    @helper\n" + _WSIG), "③ __init__ の文"),
    "世界の側の __init__ を async に": (None, lambda t: _sub(t, _WSIG, _WSIG.replace("def ", "async def ")), "③ __init__ の文"),
    "基底 2 つの順を入れ替えて置く": (None, lambda t: HEAD + SN + "\n\n" + PS + "\n\n" + FRAME, "① 頂上の文"),
    # ---- 〔安い低〕台本の前提(前と後の両方に植える=前でも後でも数える)
    "前提: 引数の無い super()": (*_both('        return "sign"\n', '        _ = super()\n        return "sign"\n'), "⓪ 台本の前提"),
    "前提: __class__ の読み": (*_both('        return "sign"\n', '        _ = __class__\n        return "sign"\n'), "⓪ 台本の前提"),
    "前提: 名前のマングリング": (*_both("        self.count += 1  # 数える\n", "        self.count += 1  # 数える\n        self.__s = 1\n"),
                              "⓪ 台本の前提"),
    "前提: __init__ の中の self のメソッドの呼び出し": (*_both("        self.seed = seed\n",
                                                             "        self.seed = seed\n        self.label = self.draw()\n"),
                                                        "⓪ 台本の前提"),
    "前提: __init__ の中の hasattr(self)": (*_both("        self.seed = seed\n",
                                                   '        self.seed = seed\n        self.has = hasattr(self, "mode")\n'),
                                              "⓪ 台本の前提"),
    "前提: __init__ の中で self をほかへ渡す": (*_both("        self.seed = seed\n", "        self.seed = seed\n        self.ref = helper(self)\n"),
                                                  "⓪ 台本の前提"),
    "前提: 同じ属性を 2 回書く": (*_both("        self.seed = seed\n", "        self.seed = seed\n        self.count = 2\n"), "⓪ 台本の前提"),
    "前提: クラスの本体の文": (*_both('    """枠。"""\n', '    """枠。"""\n\n    KIND = 1\n'), "⓪ 台本の前提"),
    "前提: 同じ名の def が 2 つ": (*_both('        return f"{self.mode}:{self.count}:{X}"\n',
                                          '        return f"{self.mode}:{self.count}:{X}"\n\n    def draw(self):\n        return 0\n'),
                                    "⓪ 台本の前提"),
    "前提: 頂上で 2 回結ぶ名": (*_both("Z = 3\n", 'Z = 3\nX = "x"\n'), "⓪ 台本の前提"),
}


@pytest.mark.parametrize("name", list(MUTATIONS))
def test_each_planted_mutation_is_caught(name):
    """植えた変異は 1 つずつ落ちる(照合が ok でない・名指しの項目が違う)。"""
    fb, fa, item = MUTATIONS[name]
    before = fb(BEFORE) if fb else BEFORE
    after = fa(AFTER)
    ast.parse(before)
    ast.parse(after)
    res = SC.check(before, after)
    assert res.kind == "形の変更" and not res.ok, (name, SC.render_text(res))
    assert item in _failing(res), (name, _failing(res), res.checks)


def test_the_mutations_change_the_sample():
    """負の対照の負の対照: 変異の関数は見本の字面に当たる(空回りしない)=どれも後の字面を変える(前提の変異は前も変える)。"""
    for name, (fb, fa, _item) in MUTATIONS.items():
        assert fa(AFTER) != AFTER, name
        if fb is not None:
            assert fb(BEFORE) != BEFORE, name


def test_allowed_additions_section_separators_heads_and_named_imports():
    """止めずに出す物: 節の区切りの注を重ねる(宣言どおりの違い 3 つ目・数つき)・基底の頭に新しい注(見張りの欄)・名指しで許した
    import(見張りの欄)。名指しした import が後に無ければ違い。"""
    dup = _sub(AFTER, '    def draw(self):\n', SEP_W + '    def draw(self):\n')
    res = SC.check(BEFORE, dup)
    assert res.ok and any(x.startswith(SC.DECLARED[2]) and "1 行" in x for x in res.declared), SC.render_text(res)
    heads = _sub(_sub(AFTER, "class PerceptScene:", "#: 世界の側の基底。\nclass PerceptScene:"), '    """気づく側。"""\n',
                 '    """気づく側。"""\n\n    # 気づく側の頭の注\n')
    res = SC.check(BEFORE, heads)
    assert res.ok and any("基底の頭に足した注 2" in x for x in res.notes), SC.render_text(res)
    imp = _sub(AFTER, "import math\n", "import math\nfrom typing import Any\n")
    res = SC.check(BEFORE, imp, allow_imports=("from typing import Any",))
    assert res.ok and any("from typing import Any" in x for x in res.notes), SC.render_text(res)
    res = SC.check(BEFORE, AFTER, allow_imports=("from typing import Any",))
    assert "① 頂上の文" in _failing(res) and any("後に無い" in x for x in res.checks["① 頂上の文"])


def test_plan_counts_refuses_a_table_that_does_not_match_the_source():
    """``plan_counts`` は、表から読んだ名がソースのメソッドに無い・世界の側か気づく側のメソッドが表から読めないときは止める
    (黙って誤った数を出さない)。"""
    table = ("### 4-1 `mod.py`\n\n| 割り先 | 行数 | クラス | 関数・メソッド | 定数 |\n|---|---:|---|---|---|\n"
             "| `world/model/percept_scene.py` | 1 | なし | `Renderer.perceive` | なし |\n"
             "| `mind/percept/notice.py` | 1 | なし | `Renderer._sign` | なし |\n")
    sides = SC.table_method_sides(table, "mod.py")
    assert sides == {"perceive": "world", "_sign": "notice"}
    c = SC.plan_counts(BEFORE, sides, world_attrs=frozenset({"world", "agents", "wid", "near"}))
    # 何も書かない文(if near … と if seed … の 2 つ)は計画の数えでは世界の側(照合は後の置き場を正とする)
    assert (c["world_init"], c["frame_init"], c["methods_by_side"]) == (6, 4, {"world": 1, "notice": 1, "frame": 2}), c
    with pytest.raises(SC.ShapeError, match="ソースの Renderer のメソッドに無い"):
        SC.plan_counts(BEFORE, {**sides, "gone": "world"})
    with pytest.raises(SC.ShapeError, match="notice の側のメソッドを 1 つも読めない"):
        SC.plan_counts(BEFORE, {"perceive": "world"})
    renamed = table.replace("`Renderer.perceive`", "`PerceptScene.perceive`")
    assert SC.table_method_sides(renamed, "mod.py") == sides  # 基底の名で書かれた表も読む


def test_cli_shapecheck_exit_codes(tmp_path):
    """``cli.py shapecheck``: 同じ=0・違う=1・形の変更ではない=2・後が無い=2・文法の誤り=2・``--allow-import``・``--json``。"""
    b, a, bad, broken, imp = (tmp_path / f"{n}.py" for n in ("before", "after", "bad", "broken", "imp"))
    b.write_text(BEFORE, encoding="utf-8")
    a.write_text(AFTER, encoding="utf-8")
    bad.write_text(MUTATIONS["メソッドを落とす"][1](AFTER), encoding="utf-8")
    broken.write_text(AFTER.replace("def draw(self):", "def draw(self)"), encoding="utf-8")
    imp.write_text(_sub(AFTER, "import math\n", "import math\nfrom typing import Any\n"), encoding="utf-8")
    out = tmp_path / "res.json"
    r = run_cli("shapecheck", "--before", str(b), "--after", str(a), "--json", str(out))
    assert r.returncode == 0 and "照合: 同じ" in r.stdout, (r.stdout, r.stderr)
    assert '"ok": true' in out.read_text(encoding="utf-8")
    r = run_cli("shapecheck", "--before", str(b), "--after", str(bad))
    assert r.returncode == 1 and "照合: 違う" in r.stdout, (r.stdout, r.stderr)
    r = run_cli("shapecheck", "--before", str(b), "--after", str(b))
    assert r.returncode == 2 and "形の変更ではない" in r.stdout, (r.stdout, r.stderr)
    r = run_cli("shapecheck", "--before", str(b))
    assert r.returncode == 2 and "--after が要る" in r.stderr
    r = run_cli("shapecheck", "--before", str(b), "--after", str(broken))
    assert r.returncode == 2 and "文法の誤り" in r.stderr, (r.stdout, r.stderr)
    r = run_cli("shapecheck", "--before", str(b), "--after", str(imp))
    assert r.returncode == 1, (r.stdout, r.stderr)
    r = run_cli("shapecheck", "--before", str(b), "--after", str(imp), "--allow-import", "from typing import Any")
    assert r.returncode == 0, (r.stdout, r.stderr)


# ------------------------------------------------------------------ 本物の renderer.py(commit に止めた blob)
def _blob(path: str) -> str | None:
    git = shutil.which("git")
    if git is None or not (ROOT / ".git").exists():
        return None
    r = subprocess.run([git, "-C", str(ROOT), "show", f"{PIN}:{path}"], capture_output=True)
    return r.stdout.decode("utf-8") if r.returncode == 0 else None


@pytest.fixture(scope="module")
def real() -> tuple[str, str]:
    text, table = _blob(RENDERER), _blob(SC.TABLE_REL)
    if text is None or table is None:
        why = f"git か commit {PIN} が無い(git の外か浅い写し)"
        if os.environ.get("CI"):  # 〔検収の後の直し 低-6〕CI では飛ばさずに落とす
            pytest.fail(f"CI で本物の renderer.py を読めない: {why}")
        pytest.skip(why)
    return text, table


def _build_a1(text: str, sides: dict[str, str], *, to_frame=lambda st: False, drop_param: str = "") -> str:
    """計画の分け方(``A1_WORLD_ATTRS``・表のメソッドの割り先)で、renderer.py の中で形を変えた字面を作る(試験の中だけ・文は前の
    注と空行ごと動かす)。``to_frame`` が真の文は枠の側へ・``drop_param`` は世界の側の口と呼ぶ文から外す(変異)。"""
    tree = ast.parse(text)
    lines = text.splitlines(keepends=True)
    R = next(s for s in tree.body if isinstance(s, ast.ClassDef) and s.name == "Renderer")
    prev_end = tree.body[tree.body.index(R) - 1].end_lineno
    doc = R.body[0]

    def spans(body, first):
        out, prev = [], first
        for st in body:
            out.append((st, "".join(lines[prev: st.end_lineno])))
            prev = st.end_lineno
        return out

    msp = {st.name: s for st, s in spans(R.body[1:], doc.end_lineno) if isinstance(st, ast.FunctionDef)}
    init = next(m for m in R.body if isinstance(m, ast.FunctionDef) and m.name == "__init__")
    idoc = init.body[0]
    head = "".join(lines[init.lineno - 1: idoc.lineno - 1])
    world, mind = [], []
    for st, s in spans(init.body[1:], idoc.end_lineno):
        wr = {n.attr for n in ast.walk(st) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)
              and n.value.id == "self" and isinstance(n.ctx, ast.Store)}
        (world if wr <= SC.A1_WORLD_ATTRS and not to_frame(st) else mind).append(s)
    pos = [a.arg for a in init.args.args if a.arg != "self"]
    used = {n.id for s in world for n in ast.walk(ast.parse("if 1:\n" + s)) if isinstance(n, ast.Name)}
    wp = [a.arg for a in [*init.args.args, *init.args.kwonlyargs] if a.arg != "self" and a.arg in used and a.arg != drop_param]
    sig = ", ".join(["self", *[p for p in wp if p in pos]]) + ", *, " + ", ".join(p for p in wp if p not in pos)
    call = "        PerceptScene.__init__(self, " + ", ".join([*(p for p in wp if p in pos),
                                                              *(f"{p}={p}" for p in wp if p not in pos)]) + ")\n"
    names = [m.name for m in R.body if isinstance(m, ast.FunctionDef) and m.name != "__init__"]
    pick = lambda side: [msp[n] for n in names if sides.get(n, "frame") == side]  # noqa: E731
    ps = ["class PerceptScene:\n", '    """世界の側。"""\n', "\n", f"    def __init__({sig}) -> None:\n",
          '        """世界の側の欄。"""\n', *world, *pick("world"), "\n\n"]
    sn = ["class SignageNotice:\n", '    """気づく側。"""\n', *pick("notice"), "\n\n"]
    rn = ["class Renderer(PerceptScene, SignageNotice):\n", "".join(lines[doc.lineno - 1: doc.end_lineno]), head,
          "".join(lines[idoc.lineno - 1: idoc.end_lineno]), call, *mind, *pick("frame")]
    return ("".join(lines[:prev_end]) + "\n\n" + "".join(ps) + "".join(sn).rstrip("\n") + "\n"
            + "".join(lines[prev_end: R.lineno - 1]) + "".join(rn) + "".join(lines[R.end_lineno:]))


def test_real_renderer_counts_match_the_retake(real):
    """G-R1 の後の renderer.py(形を変える前)から、計画の分け方の数を台本が数える: メソッド 63・__init__ の文 68=世界の側 31・
    心の側 37・__init__ で書く属性 67・側ごとのメソッド 24・2・37(枠は __init__ と render を含む)・基底どうしの同じ名 0・2 つの
    側は互いの属性を読まない・世界の側の __init__ の引数 12(G-R2 の発注に使う数)。前=後は「形の変更ではない」。"""
    text, table = real
    c = SC.plan_counts(text, SC.table_method_sides(table, "perception/renderer.py"))
    assert (c["methods"], c["init_statements"], c["world_init"], c["frame_init"], c["attrs_init"]) == (63, 68, 31, 37, 67), c
    assert c["methods_by_side"] == {"world": 24, "notice": 2, "frame": 37} and c["base_same_names"] == 0, c
    assert c["world_reads_frame_attrs"] == [] and c["frame_reads_world_attrs"] == []
    assert len(c["world_init_params"]) == 12, c["world_init_params"]
    res = SC.check(text, text)
    assert res.kind == "形の変更ではない(クラスが 1 つのまま)" and not res.ok


def _is_near_salt_default(st: ast.stmt) -> bool:
    return isinstance(st, ast.If) and "near_salt is None" in ast.unparse(st.test)


def _writes_near_salt64(st: ast.stmt) -> bool:
    return any(isinstance(n, ast.Attribute) and n.attr == "_near_salt64" and isinstance(n.ctx, ast.Store) for n in ast.walk(st))


def test_real_renderer_a1_shape_passes_and_planted_changes_fail(real):
    """計画の分け方で作った A1 の形(文を前の注ごと動かす)は ⓪〜⑨ とも「同じ」・宣言どおりの違い 2 つ(入れ替わり 21・位置の
    違う属性 60)・メソッドの置き場 24・2・36。変異は落ちる: メソッドの本文を 1 字(② だけ)・``near_salt`` の既定の文だけを枠へ・
    ``_near_salt64`` を書く文だけを枠へ(③ 局所の名の組)・世界の側の口から ``near_order`` を漏らす(③ 口の引数)。"""
    text, table = real
    sides = SC.table_method_sides(table, "perception/renderer.py")
    after = _build_a1(text, sides)
    res = SC.check(text, after)
    assert res.ok, SC.render_text(res)
    assert dict(Counter(res.method_table.values())) == {"PerceptScene": 24, "SignageNotice": 2, "Renderer": 36}
    assert len(res.declared) == 2 and "21 回入れ替わる" in res.declared[0] and "位置の違う 60" in res.declared[1], res.declared
    assert (res.counts["world_init"], res.counts["frame_init"], res.counts["world_init_params"]) == (31, 37, 12)
    i = after.index("    def perceive(")
    j = after.index("self.agents", i)
    bad = after[:j] + "self.agentz" + after[j + len("self.agents"):]
    assert _failing(SC.check(text, bad)) == ["② メソッド"]
    for name, kw in (("near_salt の既定の文を枠へ", {"to_frame": _is_near_salt_default}),
                     ("_near_salt64 を書く文を枠へ", {"to_frame": _writes_near_salt64})):
        r = SC.check(text, _build_a1(text, sides, **kw))
        assert "③ __init__ の文" in _failing(r) and any("局所の名 ['near_salt']" in x for x in r.checks["③ __init__ の文"]), \
            (name, r.checks)
    r = SC.check(text, _build_a1(text, sides, drop_param="near_order"))
    assert any("near_order" in x and "受けない" in x for x in r.checks["③ __init__ の文"]), r.checks


def test_cli_reads_the_before_from_a_git_blob(real):
    """``--before <commit>:<道>`` で木を写さずに前を読む(前=後の blob は形の変更ではない=終了コード 2)。``--plan-counts`` は
    ``--table <commit>:<道>`` で表も止めて数を出す(0)。読めない blob は 2。"""
    r = run_cli("shapecheck", "--before", f"{PIN}:{RENDERER}", "--after", f"{PIN}:{RENDERER}")
    assert r.returncode == 2 and "形の変更ではない" in r.stdout, (r.stdout, r.stderr)
    r = run_cli("shapecheck", "--before", f"{PIN}:{RENDERER}", "--plan-counts", "--table", f"{PIN}:{SC.TABLE_REL}")
    assert r.returncode == 0 and '"world_init": 31' in r.stdout and '"frame_init": 37' in r.stdout, (r.stdout, r.stderr)
    r = run_cli("shapecheck", "--before", "no_such_commit_zz:src/x.py", "--after", f"{PIN}:{RENDERER}")
    assert r.returncode == 2 and "読めない" in r.stderr
