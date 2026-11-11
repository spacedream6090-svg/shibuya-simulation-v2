# -*- coding: utf-8 -*-
"""tools/repo_guide(段 3 ファイルのカード・11-05/§3-1 の 1)の試験。

合成のリポを tmp に作ってカードの中身を確かめる / 2 回作って同じバイト / ``--check`` が差を見つける /
data の中のファイルを開かない(監査フックで確かめる・負の対照つき)/ 伏せる語 / git の一覧。
本物のリポについては、AST で読んだ台帳と書きの許可を実物の import と比べ(道具は import しない実物の規則の写しなので)、
公開の関数・import・環境変数を別の読み方(実物の import と行の正規表現)と突き合わせ、素の import の辺が落ちていないことを確かめる。
"""
from __future__ import annotations

import ast
import base64
import importlib
import importlib.util
import inspect
import os
import re
import shutil
import subprocess
import sys
import types
import warnings
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
TOOL_DIR = REPO / "tools" / "repo_guide"
BUILD = TOOL_DIR / "build.py"
CARDS = "docs/reference/repo-guide/cards"
SECRET_WORD = "SENTINELWORD"
PATH_WORD = "ANOTHERSENTINEL"
DATA_CONTENT = "番兵: この中身がカードに出たら data を読んだことになる"


def _b64(s: str) -> str:
    return base64.b64encode(s.encode("utf-8")).decode("ascii")


LEDGER_SRC = '''"""台帳の見本。"""
from dataclasses import dataclass
from typing import Final
BEHAVIOR: Final[str] = "behavior"
NO: Final[str] = "no"
REQUIRED: Final[str] = "required"
DISCARDABLE: Final[str] = "discardable"
EXTERNAL: Final[str] = "external"
@dataclass(frozen=True)
class LedgerRow:
    key: str
    name: str
    place: str
    behavior: str
    restore: str
    dead: bool = False
    items: tuple = ()
    arm: str = ""
def _s(place, name, dtype, behavior, restore, *, dead=False):
    return LedgerRow(key=f"{place}.{name}", name=name, place=place, behavior=behavior, restore=restore, dead=dead)
def _o(n, name, where, behavior, restore, items, *, note=""):
    return LedgerRow(key=f"O{n}", name=name, place=EXTERNAL, behavior=behavior, restore=restore, items=tuple(items))
B, N_ = BEHAVIOR, NO
R_, X_ = REQUIRED, DISCARDABLE
_SOA = (
    _s("agents", "cell", "i4", B, R_),
    _s("agents", "money", "i8", B, R_),
    _s("cells", "b4", "u1", N_, X_, dead=True),
)
_EXT = (
    _o(10, "層の十番", "layer.py:14", N_, X_, ("layer.n_ten",)),
    _o(1, "層の中身", "layer.py:12", B, R_, ("layer.value", "layer.child.deep")),
    _o(2, "層の計数 x[i](y)", "layer.py:13", N_, X_, tuple(f"layer.{a}" for a in ("n_a", "n_b"))),
    _o(3, "局所の値", "run.py:1", B, R_, ("run_day.pending",)),
    LedgerRow(key="ARM1", name="腕の行", place=EXTERNAL, behavior=B, restore=R_, items=("layer.armed",), arm="my_arm"),
    LedgerRow(key="P", name="道筋のない行", place=EXTERNAL, behavior=N_, restore=X_),
)
LEDGER = _SOA + _EXT
OWNER_CLASSES: Final[dict] = {
    "layer": ("engine/layer.py", "Layer"),
    "layer.child": ("engine/layer.py", "Child"),
}
OWNER_ALT_CLASSES: Final[dict] = {"layer": (("engine/layer_alt.py", "AltLayer"),)}
'''

LEDGER_AST_SRC = '''"""見本。"""
DECL_FILES = {"agents": "agents/state.py", "world": "world/state.py", "perception": "perception/state.py"}
WRITE_FUNCS = frozenset({"copyto", "put", "place", "putmask"})
'''

ALLOW_SRC = '''"""見本。"""
from types import MappingProxyType
ALIAS_WRITES = {"hidden_write": (("agents.money",), "別名の根拠")}
TRANSFER_WRITES = ("agents.money",)
TRANSFER_PORTS_HOUSEHOLD = MappingProxyType({"pay_fares": "運賃"})
'''

RESOLVE_SRC = '''"""見本。"""
def move(agents):
    """セルを書く。"""
    agents.cell[0] = 1
    _helper(agents)
def _helper(agents):
    agents.money[0] = 2
def pay(agents, ledger):
    ledger.pay_fares(agents)
def hidden_write(agents):
    pass
def read_only(agents):
    return agents.cell[0]
def write_cells(cells):
    cells.b4[0] = 1
'''

TABLE_SRC = '''"""見本。"""
from shibuya.engine.systems import mover as _MV
from shibuya.engine.systems.spec import make
def _build_fn(ctx, b):
    raise RuntimeError
SYSTEMS = (
    make("build", "組み立て", "run_head", _build_fn, resolve_ops="hidden_write write_cells"),
    make("mover", "体", "tick", _MV.sys_mover, resolve_ops="move read_only",
         paths="O1:layer.* "
               "ARM1:layer.armed",
         scratch_w="scr_a", tally="count_a", when="always", calls_llm="send"),
)
'''

LAYER_SRC = '''# -*- coding: utf-8 -*-
"""engine.layer — 見本の層の 1 段目
折り返しの続き arr[i](x) と ``keep[i](x)``。

2 段目はカードに出ない。
"""
import os

from shibuya.engine import resolve as RV
from shibuya.engine.systems.mover import sys_mover

ENV_NAME = "MY_NAMED_ENV"
_MD = os.environ.get(ENV_NAME)
_DIRECT = os.getenv("MY_DIRECT_ENV")


class Layer:
    """層の本体。

    2 行目は出ない。
    """


def public_fn():
    """公開の関数の 1 行目 f[0](1)。

    2 行目は出ない。
    """


def _private_fn():
    """出ない。"""


def undocumented():
    pass


if COND:
    def in_if():
        """if の中。"""
else:
    def in_else():
        pass
try:
    def in_try():
        pass
except ImportError:
    def in_except():
        pass
finally:
    def in_finally():
        pass
with ctx():
    def in_with():
        pass


def outer():
    def nested_fn():
        pass


# 決定の ID: 11-01/A1-2・10-13b・10-25 §2-5・R-126・R-9・D-74・第 345・第 1000
# 段と層の前の番号: 第340 段 2・第170 層2
# 接頭につながる項目の番号: 11-01 §1 #7・#8〜#12・R-126 §1-4(#46・第 345 #2・10-13b/K3 #5・R-9 #3・D-74 #4
# つながらない項目の番号: routing #74・第 345 親の決め #99・#77
# 拾わないもの: 2026-10-12・第 1 期・第 2 波・第 31 表・第 346 部・第 12 の・第 347-1 表・K15
# 接頭の中の ID を別に拾わない: 10-12/D-9
_COLOR = "#333"
'''

TOOL_SRC = '''"""見本の道具。"""
import argparse
import os
import sys
from os import environ, getenv

import sibling_mod

FLAG_NAME = "--const-flag"
HELP_TEXT = "定数の説明 g[0](1)"
ENV_ARM = "SHIBUYA_MY_ARM"
E = os.environ


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--flag", action="store_true", help="旗の説明")
    ap.add_argument("target")
    ap.add_argument(*NAMES)
    ap.add_argument(FLAG_NAME, help=HELP_TEXT)
    ap.add_argument("--dyn", help=f"動的な {FLAG_NAME}")
    sub = ap.add_subparsers()
    sub.add_parser("run-it")
    name = sys.argv[1]
    print(environ["ENV_A"], getenv("ENV_B"), os.environ.pop("ENV_C"), "ENV_D" in os.environ, os.environ.get(name))
    print(E.get("ENV_VIA_ALIAS"))
    return dict(os.environ)
'''

LOOP_PATHS_SRC = '''"""sys.path に足す色々な形。"""
import os
import sys
from pathlib import Path

_HERE = Path(os.path.abspath(__file__)).parent
TOOLS = _HERE.parent
REPO_ROOT = TOOLS.parent
for _p in (str(TOOLS / "loop_a"), str(TOOLS / "loop_b")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
for sub in ("tools/loop_c",):
    sys.path.append(str(REPO_ROOT / sub))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "via_parent"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "via_parents"))
sys.path.insert(0, str(Path(__file__).resolve().parent / "via_resolve"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "via_join"))
sys.path.insert(0, UNKNOWN_CALL())
sys.path.insert(0, helper_arg)

import in_loop_a
import in_loop_b
import in_loop_c
import in_parent
import in_parents
import in_resolve
import in_join
'''


def _write(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(text.encode("utf-8"))


def _guide_paths(guide) -> dict[str, str]:
    """道具が道で読むファイル(``guide_permits`` の定数)。〔段 4 の下ごしらえ〕見本の木は本物の src の置き場ではなく、道具が読む形で
    作る: 道具が道で読む 5 本はその定数から、ほかは同じ根(``SRC``)の下に f 文字列で置く(前は本物の道と同じ字面で、移す道具が
    一部だけを新しい置き場へ書き換えて、道具の定数・見本の台帳の ``DECL_FILES`` と食い違った)。"""
    return {k: getattr(guide.P, k) for k in ("SRC", "LEDGER_FILE", "LEDGER_AST_FILE", "TABLE_FILE", "ALLOW_FILE",
                                             "RESOLVE_FILE")}


@pytest.fixture()
def repo(tmp_path: Path, guide) -> Path:
    root = tmp_path / "synth"
    GUIDE = _guide_paths(guide)
    S = GUIDE["SRC"]
    files = {
        f"{S}/__init__.py": '"""根。"""\n',
        f"{S}/agents/state.py": 'r.declare("cell", 1)\nr.declare("money", 1)\n',
        f"{S}/world/state.py": 'cells.declare("b4", 1)\n',
        f"{S}/perception/state.py": "",
        f"{S}/engine/__init__.py": "",
        GUIDE["LEDGER_FILE"]: LEDGER_SRC,
        GUIDE["LEDGER_AST_FILE"]: LEDGER_AST_SRC,
        GUIDE["RESOLVE_FILE"]: RESOLVE_SRC,
        f"{S}/engine/layer.py": LAYER_SRC,
        f"{S}/engine/layer_alt.py": '"""別のクラス。"""\nclass AltLayer:\n    pass\n',
        f"{S}/engine/uses_layer.py": "from shibuya.engine.layer import public_fn\n",
        f"{S}/engine/rel_user.py": ("from . import layer\nfrom .uses_layer import public_fn\n"
                                    "from ..agents import state\nfrom .systems import mover\n"),
        f"{S}/engine/dyn_user.py": 'import importlib\nM = importlib.import_module("shibuya.engine.layer")\n',
        f"{S}/engine/systems/__init__.py": "",
        GUIDE["ALLOW_FILE"]: ALLOW_SRC,
        GUIDE["TABLE_FILE"]: TABLE_SRC,
        f"{S}/engine/systems/mover.py": '"""系の見本。"""\ndef sys_mover(b):\n    """動く。"""\n',
        "tests/__init__.py": "",
        "tests/test_layer.py": "from shibuya.engine import layer\n",
        "tests/sub/conftest.py": 'import sys\nsys.path.insert(0, str(ROOT / "tools" / "pack"))\n',
        "tests/sub/test_bare.py": "import packed\n",
        "tests/test_by_path.py": ('TOOL = REPO / "tools" / "mytool.py"\nSRC = ROOT / "engine" / "resolve.py"\n'
                                  'J = REPO.joinpath("tools", "joined.py")\n'),
        "tests/test_doc_only.py": '"""tools/only_doc.py"""\n',
        "tests/test_prepend.py": ('def test_x(monkeypatch):\n    monkeypatch.syspath_prepend(ROOT / "tools" / "prep")\n'
                                  "    import in_prep\n"),
        "tools/mytool.py": TOOL_SRC,
        "tools/sibling_mod.py": '"""ascii line one\nascii line two\n\n続き。"""\n',
        "tools/only_doc.py": '"""docstring で指されるだけ。"""\n',
        "tools/joined.py": '"""joinpath で指される。"""\n',
        "tools/pack/packed.py": '"""sys.path で読まれる。"""\n',
        "tools/prep/in_prep.py": '"""syspath_prepend で読まれる。"""\n',
        "tools/deep/loop_paths.py": LOOP_PATHS_SRC,  # 深い所に置く=__file__ から読まないと正しい道筋にならない
        "tools/loop_a/in_loop_a.py": "",
        "tools/loop_b/in_loop_b.py": "",
        "tools/loop_c/in_loop_c.py": "",
        "tools/via_parent/in_parent.py": "",
        "tools/via_parents/in_parents.py": "",
        "tools/deep/via_resolve/in_resolve.py": "",
        "tools/via_join/in_join.py": "",
        "tools/uses_lib.py": "import path_lib\nimport in_trans\n",
        "tools/path_lib.py": 'import sys\nsys.path.insert(0, str(_R / "tools" / "trans"))\n',
        "tools/trans/in_trans.py": "",
        "tools/instr/pkg/__init__.py": 'import sys\nsys.path.insert(0, str(_R / "tools" / "instr" / "side"))\n',
        "tools/instr/pkg/mod.py": "import pkg\nimport in_side\n",
        "tools/instr/pkg/mod2.py": "import in_side\n",  # 自分のパッケージの名を書かなくても __init__ は先に走る
        "tools/instr/side/in_side.py": "",
        "tools/no_way.py": "import lonely_mod\nimport json\n",
        "tools/elsewhere/lonely_mod.py": "",
        "tools/elsewhere/json.py": "",  # 標準ライブラリと同じ名のファイル
        "tools/decision_index.py": 'DOCS = (("10-13b", "a.md", "x"), ("10-25", "b.md", "x"), ("11-01", "c.md", "x"), ("10-12", "d.md", "x"))\n',
        "tools/scan_secrets.py": f'_B64 = "{_b64(SECRET_WORD)}"\n',
        "tools/commit_check.py": f'_BAD_PATH_B64 = "{_b64(PATH_WORD)}"  # 検出\n',
        "tools/fixture.json": "{}\n",
        "docs/README.md": "```\n# 囲みの中は見出しでない\n```\n\n本文\n\n## 最初の見出し\n",
        "docs/design/a.md": "# 設計 A [外](b.md)\n",
        "docs/design/no_heading.md": "見出しなし\n",
        "docs/design/pic.png": "x",
        "data/README.md": DATA_CONTENT,
        "data/jinryu/sealed.csv": DATA_CONTENT,
        "data/jinryu/sub/deep/too_deep.csv": DATA_CONTENT,
        "data/odpt_rt/held/x.bin": DATA_CONTENT,
    }
    for rel, text in files.items():
        _write(root, rel, text)
    return root


def _run(root: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONUTF8": "1"}
    return subprocess.run([sys.executable, str(BUILD), "--root", str(root), *args], capture_output=True,
                          encoding="utf-8", env=env)


def _card(root: Path, d: str) -> str:
    return (root / CARDS / d / "README.md").read_bytes().decode("utf-8")


def _block(card: str, name: str) -> str:
    """カードの中の 1 ファイルの節。"""
    head = f"## [{name}]("
    assert head in card, name
    return card.split(head, 1)[1].split("\n## [", 1)[0]


def _guide_block(root: Path, rel: str) -> str:
    """道具が道で読むファイル(``guide_permits`` の定数=リポの根からの道)の節。〔段 4 の下ごしらえ〕カードの置き場とファイルの名は
    定数から作る(移した後は定数が新しい置き場を指す)。"""
    d, _, name = rel.rpartition("/")
    return _block(_card(root, d), name)


def _snapshot(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted((root / CARDS).rglob("*")) if p.is_file()}


@pytest.fixture(scope="module")
def guide():
    """build.py を読み込んだモジュール(``guide.F``・``guide.P``・``guide.R`` が部品)。"""
    sys.path.insert(0, str(TOOL_DIR))
    try:
        spec = importlib.util.spec_from_file_location("repo_guide_build", BUILD)
        m = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(m)
        return m
    finally:
        sys.path.remove(str(TOOL_DIR))


# ---------------------------------------------------------------- 中身
def test_card_contents_summary_public_imports_callers_tests(repo: Path):
    cp = _run(repo)
    assert cp.returncode == 0, cp.stderr + cp.stdout
    b = _block(_card(repo, "src/shibuya/engine"), "layer.py")
    assert "engine.layer — 見本の層の 1 段目折り返しの続き" in b  # 最初の段落・折り返しは 1 行に戻す
    assert "2 段目はカードに出ない" not in b
    assert "`Layer`(クラス): 層の本体。" in b
    assert "`public_fn`(関数): 公開の関数の 1 行目" in b
    assert "`undocumented`(関数)" in b
    assert "_private_fn" not in b
    assert "2 行目は出ない" not in b
    assert "import している内部モジュール: `shibuya.engine.resolve`・`shibuya.engine.systems.mover`" in b
    assert "- 呼び手: `shibuya.engine.dyn_user`・`shibuya.engine.rel_user`・`shibuya.engine.uses_layer`" in b
    assert "- 読む試験: `tests/test_layer.py`" in b
    assert "環境変数: `MY_DIRECT_ENV`・`MY_NAMED_ENV`" in b  # 文字列と頂上の定数


def test_ascii_lines_join_with_a_space(repo: Path):
    _run(repo)
    assert "ascii line one ascii line two" in _block(_card(repo, "tools"), "sibling_mod.py")


def test_public_inside_if_try_with_but_not_nested(repo: Path):
    _run(repo)
    b = _block(_card(repo, "src/shibuya/engine"), "layer.py")
    assert "`in_if`(関数): if の中。" in b
    for name in ("in_else", "in_try", "in_except", "in_finally", "in_with"):
        assert f"`{name}`(関数)" in b, name
    assert "nested_fn" not in b


def test_relative_imports_and_import_module(repo: Path):
    _run(repo)
    r = _block(_card(repo, "src/shibuya/engine"), "rel_user.py")
    assert ("import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.layer`・"
            "`shibuya.engine.systems.mover`・`shibuya.engine.uses_layer`") in r
    assert "`shibuya.engine.layer`" in _block(_card(repo, "src/shibuya/engine"), "dyn_user.py")  # import_module


def _ids_of(block: str) -> list[str]:
    line = next(x for x in block.split("\n") if x.startswith("- 決定の ID"))
    return line.removeprefix("- 決定の ID: ").split("・")


def test_decision_ids_rules(repo: Path):
    _run(repo)
    ids = _ids_of(_block(_card(repo, "src/shibuya/engine"), "layer.py"))
    assert ids == [
        "10-12/D-9", "10-13b", "10-13b/K3", "10-13b/K3 #5", "10-25/§2-5", "11-01/A1-2", "11-01/§1",
        "11-01/§1 #7", "11-01/§1 #8", "11-01/§1 #12",
        "R-9", "R-9 #3", "R-126", "R-126 §1-4 #46",  # 数の順(文字列の順なら R-126 が先)
        "D-74", "D-74 #4",
        "第 170", "第 340", "第 345", "第 345 #2", "第 1000",
    ]  # 第 346 部・第 12・第 347-1 表・つながらない #N(#74・#99・#77・#333)は無い


def test_decision_ids_without_prefix_list(repo: Path):
    (repo / "tools/decision_index.py").unlink()
    assert _run(repo).returncode == 0
    ids = _ids_of(_block(_card(repo, "src/shibuya/engine"), "layer.py"))
    assert "R-126 §1-4 #46" in ids and "第 345 #2" in ids
    assert "10-13b" not in ids


def test_decision_sort_key_breaks_ties_by_text(guide):
    key = guide.F.decision_sort_key
    assert key("11-01/a1") != key("11-01/a01")  # 数の順では同じ重み
    assert sorted(["11-01/a1", "11-01/a01"], key=key) == sorted(["11-01/a01", "11-01/a1"], key=key)


def test_ledger_rows_and_owner(repo: Path, guide):
    _run(repo)
    b = _block(_card(repo, "src/shibuya/engine"), "layer.py")
    assert "持ち主 `layer`(`Layer`)" in b
    assert "持ち主 `layer.child`(`Child`)" in b  # 最も長い前方で引く
    assert "`O1` 層の中身(挙動 behavior・復元 required) 道筋 `layer.value` 書ける系: mover" in b
    assert "`O1` 層の中身(挙動 behavior・復元 required) 道筋 `layer.child.deep` 書ける系: mover" in b
    assert "`O2` 層の計数 x[i]\\(y)(挙動 no・復元 discardable) 道筋 `layer.n_a`・`layer.n_b` 書ける系: (宣言なし)" in b  # 内包の道筋も読む
    assert "`ARM1` 腕の行(挙動 behavior・復元 required・腕 my_arm)" in b
    assert b.index("`O2` ") < b.index("`O10` ")  # 鍵は数の順(宣言の順でも文字列の順でもない)
    assert "layer.py:12" not in b  # 行番号を含む根拠の欄は載せない
    # SoA の持ち主は宣言のファイル
    a = _block(_card(repo, "src/shibuya/agents"), "state.py")
    assert "`agents.cell` cell(挙動 behavior・復元 required) 書ける系: mover" in a
    assert "`agents.money` money(挙動 behavior・復元 required) 書ける系: build・mover" in a
    w = _block(_card(repo, "src/shibuya/world"), "state.py")
    assert "`cells.b4` b4(挙動 no・復元 discardable・死蔵) 書ける系: build" in w  # 置き場は式の文字列で決める
    # 別のクラス・持ち主を引けない行
    alt = _block(_card(repo, "src/shibuya/engine"), "layer_alt.py")
    assert "持ち主 `layer` の別のクラス `AltLayer`(行は `shibuya.engine.layer` のカードを見る)" in alt
    led = _guide_block(repo, _guide_paths(guide)["LEDGER_FILE"])
    assert "持ち主を引けない行" in led and "`O3` 局所の値" in led and "`P` 道筋のない行" in led


def test_write_permits_from_table(repo: Path, guide):
    _run(repo)
    files = _guide_paths(guide)
    m = _block(_card(repo, "src/shibuya/engine/systems"), "mover.py")
    assert "系 `mover`(群 体・時 `tick`・立つ条件 `always`・LLM `send`・関数 `sys_mover`)" in m
    assert "呼んでよい resolve の口: `move`・`read_only`" in m
    assert "書いてよい SoA の列(閉包): `agents.cell`・`agents.money`" in m  # move → _helper の閉包
    assert "書いてよい外の道筋: `ARM1:layer.armed`・`O1:layer.*`" in m
    assert "書く scratch: `scr_a`" in m and "書く計数: `count_a`" in m
    t = _guide_block(repo, files["TABLE_FILE"])
    assert "系 `build`(群 組み立て・時 `run_head`・関数 `_build_fn`)" in t
    assert "書いてよい SoA の列(閉包): `agents.money`・`cells.b4`" in t  # ALIAS_WRITES
    r = _guide_block(repo, files["RESOLVE_FILE"])
    assert "`move`: 直接の書き `agents.cell` 口として持つ系: mover" in r
    assert "`pay`: 直接の書き `agents.money`" in r  # 帳簿の口
    assert "`read_only`: 直接の書き (なし) 口として持つ系: mover" in r


def test_cli_and_env_of_a_tool(repo: Path):
    _run(repo)
    b = _block(_card(repo, "tools"), "mytool.py")
    assert "`--flag`: 旗の説明" in b
    assert "  - `target`" in b
    assert "サブコマンド `run-it`" in b
    assert "名前を読めない呼び出し 1 か所" in b  # add_argument(*NAMES)
    assert "`sys.argv` を直接読む" in b
    assert "`--const-flag`: 定数の説明" in b  # 旗も help も頂上の定数から読む
    assert "`--dyn`: (help を読めない)" in b  # 定数でない help には印
    assert ("環境変数: `ENV_A`・`ENV_B`・`ENV_C`・`ENV_D`・`ENV_VIA_ALIAS`・`SHIBUYA_MY_ARM`・"
            "名前を読めない所 1 か所・`os.environ` をまるごと使う") in b  # x = os.environ の別名・SHIBUYA_ の文字列
    assert "import している内部モジュール: `tools/sibling_mod.py`" in b  # 同じディレクトリの素の名前
    assert "その他のファイル: `fixture.json`" in _card(repo, "tools")


def test_tests_by_path_and_syspath_of_conftest(repo: Path):
    _run(repo)
    tools_card = _card(repo, "tools")
    assert "読む試験(道筋で): `tests/test_by_path.py`" in _block(tools_card, "mytool.py")
    assert "読む試験(道筋で): `tests/test_by_path.py`" in _block(tools_card, "joined.py")  # joinpath
    res = _block(_card(repo, "src/shibuya/engine"), "resolve.py")
    assert "`tests/test_by_path.py`" in res  # src/shibuya/ を省いた道筋
    assert "読む試験" not in _block(tools_card, "only_doc.py")  # docstring の道筋は数えない
    packed = _block(_card(repo, "tools/pack"), "packed.py")
    assert "読む試験: `tests/sub/test_bare.py`" in packed  # 祖先の conftest が sys.path に足す
    assert "読む試験: `tests/test_prepend.py`" in _block(_card(repo, "tools/prep"), "in_prep.py")  # syspath_prepend


def test_syspath_forms_are_read_and_unread_ones_are_counted(repo: Path):
    _run(repo)
    for d, name in (("loop_a", "in_loop_a"), ("loop_b", "in_loop_b"), ("loop_c", "in_loop_c"), ("via_parent", "in_parent"),
                    ("via_parents", "in_parents"), ("deep/via_resolve", "in_resolve"), ("via_join", "in_join")):
        assert "- 呼び手: `tools/deep/loop_paths.py`" in _block(_card(repo, f"tools/{d}"), f"{name}.py"), name
    lp = _block(_card(repo, "tools/deep"), "loop_paths.py")
    assert "`sys.path` に足す先を読めない所 2 か所" in lp  # UNKNOWN_CALL() と helper_arg
    assert "読めない所" not in _block(_card(repo, "tools"), "path_lib.py")
    assert "`tools/deep/loop_paths.py`: `sys.path` に足す先を読めない所 2 か所" in (repo / CARDS / "README.md").read_text(encoding="utf-8")


def test_syspath_added_by_an_imported_module_and_by_package_init(repo: Path):
    _run(repo)
    assert "- 呼び手: `tools/uses_lib.py`" in _block(_card(repo, "tools/trans"), "in_trans.py")  # path_lib が足す
    m = _block(_card(repo, "tools/instr/pkg"), "mod.py")
    # パッケージの外側から自分のパッケージの名で読め、__init__ が足す所も探す
    assert "import している内部モジュール: `tools/instr/pkg/__init__.py`・`tools/instr/side/in_side.py`" in m
    assert "解けない素の import" not in m
    m2 = _block(_card(repo, "tools/instr/pkg"), "mod2.py")
    assert "import している内部モジュール: `tools/instr/side/in_side.py`" in m2  # 囲むパッケージの __init__ が足す所


def test_unresolved_bare_import_gets_a_mark(repo: Path):
    _run(repo)
    b = _block(_card(repo, "tools"), "no_way.py")
    assert "解けない素の import: `lonely_mod`(同じ名のファイル `tools/elsewhere/lonely_mod.py` が 1 つある)" in b
    assert "json" not in b  # 標準ライブラリの名は数えない
    assert "呼び手" not in _block(_card(repo, "tools/elsewhere"), "lonely_mod.py")
    assert "`tools/no_way.py`: 解けない素の import `lonely_mod`" in (repo / CARDS / "README.md").read_text(encoding="utf-8")


def test_subdirs_are_sorted(repo: Path):
    _run(repo)
    head = next(x for x in _card(repo, "src/shibuya").split("\n") if x.startswith("下のディレクトリ"))
    # 〔段 4 の下ごしらえ〕見本の木の下のディレクトリは、道具が道で読むファイルの置き場(定数=移した後は新しい置き場)で変わる。
    # 期待は見本の木のディレクトリそのもの(並べて全部)。移す前の木では前の字面 agents・engine・perception・world と同じ
    want = sorted(d.name for d in (repo / "src" / "shibuya").iterdir() if d.is_dir())
    assert {"agents", "engine", "perception", "world"} <= set(want)
    assert re.findall(r"\[(\w+)\]", head) == want


def test_link_shapes_in_text_are_escaped(repo: Path):
    _run(repo)
    b = _block(_card(repo, "src/shibuya/engine"), "layer.py")
    assert "arr[i]\\(x)" in b and "``keep[i](x)``" in b  # コードの囲みの中はそのまま
    assert "`public_fn`(関数): 公開の関数の 1 行目 f[0]\\(1)" in b
    assert "`--const-flag`: 定数の説明 g[0]\\(1)" in _block(_card(repo, "tools"), "mytool.py")
    assert "設計 A [外]\\(b.md)" in (repo / CARDS / "docs.md").read_text(encoding="utf-8")


def test_docs_index_and_entry_readme(repo: Path):
    _run(repo)
    docs = (repo / CARDS / "docs.md").read_text(encoding="utf-8")
    assert "## docs/design(3 本)" in docs
    assert "(../../../design/a.md): 設計 A" in docs
    assert "no_heading.md](../../../design/no_heading.md): (見出しなし)" in docs
    assert "README.md](../../../README.md): 最初の見出し" in docs
    assert "pic.png" not in docs
    readme = (repo / CARDS / "README.md").read_text(encoding="utf-8")
    assert "[src/shibuya/engine](src/shibuya/engine/README.md)" in readme
    assert "[docs の索引](docs.md)" in readme and "[data の一覧](data.md)" in readme
    assert "読み方の規則" in readme
    assert "サブコマンド" in readme and "区別しない" in readme  # 旗にサブコマンドの区別が無いことの宣言
    assert "台帳の番号" not in readme


def test_unparsable_file_is_reported_not_guessed(repo: Path):
    _write(repo, "tools/broken.py", "def (:\n")
    cp = _run(repo)
    assert cp.returncode == 0, cp.stderr
    assert "**読めなかった**: 構文を読めない" in _block(_card(repo, "tools"), "broken.py")
    assert "`tools/broken.py`: 構文を読めない" in (repo / CARDS / "README.md").read_text(encoding="utf-8")


def test_missing_ledger_is_reported(repo: Path, guide):
    GUIDE = _guide_paths(guide)
    (repo / GUIDE["LEDGER_FILE"]).unlink()
    (repo / GUIDE["TABLE_FILE"]).unlink()
    cp = _run(repo)
    assert cp.returncode == 0, cp.stderr
    text = (repo / CARDS / "README.md").read_text(encoding="utf-8")
    # 〔段 4 の下ごしらえ〕期待の字面は道具の定数から作る(移した後は台帳のファイルの名が変わる)。移す前の木では前の字面
    # 「state_ledger.py が無い」「table.py が無い」と同じ
    assert f"{GUIDE['LEDGER_FILE']} が無い" in text and f"{GUIDE['TABLE_FILE']} が無い" in text


# ---------------------------------------------------------------- 決定的
def test_two_builds_same_bytes_lf_no_abs_paths(repo: Path):
    _run(repo)
    first = _snapshot(repo)
    assert first
    cp = _run(repo)
    assert cp.returncode == 0
    assert _snapshot(repo) == first
    for rel, data in first.items():
        assert b"\r" not in data, rel
        text = data.decode("utf-8")
        assert repo.name not in text and str(repo.parent) not in text, rel


def test_crlf_source_gives_same_cards(repo: Path):
    _run(repo)
    before = _snapshot(repo)
    for rel in ("src/shibuya/engine/layer.py", "tools/mytool.py"):
        p = repo / rel
        p.write_bytes(p.read_bytes().replace(b"\n", b"\r\n"))
    assert _run(repo).returncode == 0
    assert _snapshot(repo) == before
    # カード自身が CRLF でも --check は同じと見る
    p = repo / CARDS / "tools" / "README.md"
    p.write_bytes(p.read_bytes().replace(b"\n", b"\r\n"))
    assert _run(repo, "--check").returncode == 0


# ---------------------------------------------------------------- --check
def test_check_finds_differences(repo: Path):
    _run(repo)
    assert _run(repo, "--check").returncode == 0
    # docstring を変える
    p = repo / "tools/mytool.py"
    keep = p.read_bytes()
    p.write_bytes(keep.replace("見本の道具".encode(), "変えた道具".encode()))
    cp = _run(repo, "--check")
    assert cp.returncode == 1 and f"違う: {CARDS}/tools/README.md" in cp.stdout
    p.write_bytes(keep)
    assert _run(repo, "--check").returncode == 0
    # 試験の import を足すと、読まれる側のカードも変わる
    t = repo / "tests/test_layer.py"
    t.write_bytes(t.read_bytes() + b"from tools import mytool\n")
    cp = _run(repo, "--check")
    assert cp.returncode == 1 and f"違う: {CARDS}/tools/README.md" in cp.stdout and f"違う: {CARDS}/tests/README.md" in cp.stdout
    _run(repo)
    # カードが無い・余計なカード
    (repo / CARDS / "tools/pack/README.md").unlink()
    extra = repo / CARDS / "src/gone/README.md"
    extra.parent.mkdir(parents=True)
    extra.write_bytes(b"x\n")
    cp = _run(repo, "--check")
    assert cp.returncode == 1
    assert f"無い: {CARDS}/tools/pack/README.md" in cp.stdout and f"余計: {CARDS}/src/gone/README.md" in cp.stdout
    # 作り直せば余計なカードも消える
    _run(repo)
    assert not extra.exists()
    assert _run(repo, "--check").returncode == 0


def test_check_ignores_docs_data_and_entry_readme(repo: Path):
    _run(repo)
    _write(repo, "docs/new.md", "# 新しい文書\n")
    _write(repo, "data/new_dir/x.bin", "x")
    (repo / CARDS / "README.md").write_bytes(b"changed\n")
    (repo / CARDS / "docs.md").unlink()
    (repo / CARDS / "data.md").unlink()
    assert _run(repo, "--check").returncode == 0
    assert not (repo / CARDS / "docs.md").exists()  # --check は書かない


def test_no_data_dir_keeps_old_list_and_readme_does_not_change(repo: Path):
    _run(repo)
    before = (repo / CARDS / "data.md").read_bytes()
    readme = (repo / CARDS / "README.md").read_bytes()
    assert "data が無い".encode() not in readme
    shutil.rmtree(repo / "data")
    assert _run(repo, "--check").returncode == 0
    assert _run(repo).returncode == 0
    assert (repo / CARDS / "data.md").read_bytes() == before  # data の無い機械で一覧を消さない
    assert (repo / CARDS / "README.md").read_bytes() == readme  # README に data の状態を書かない


# ---------------------------------------------------------------- data
_DRIVER = r"""
import os, runpy, sys
build, root, mode = sys.argv[1:4]
data = os.path.normcase(os.path.abspath(os.path.join(root, "data")))
def under(a):
    if isinstance(a, int) or a is None:
        return False
    try:
        p = os.path.normcase(os.path.abspath(os.fsdecode(a)))
    except TypeError:
        return False
    return p == data or p.startswith(data + os.sep)
def hook(ev, args):
    if ev == "open" and under(args[0]) and not os.path.isdir(args[0]):
        os.write(2, b"OPENED-IN-DATA")
        os._exit(3)
    if mode == "check" and ev in ("os.scandir", "os.listdir") and under(args[0]):
        os.write(2, b"LISTED-DATA")
        os._exit(4)
sys.addaudithook(hook)
if mode == "control":
    with open(os.path.join(root, "data", "README.md"), "rb") as f:
        f.read()
sys.path.insert(0, os.path.dirname(build))
sys.argv = [build, "--root", root] + (["--check"] if mode == "check" else [])
runpy.run_path(build, run_name="__main__")
"""


def _driver(root: Path, mode: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-c", _DRIVER, str(BUILD), str(root), mode], capture_output=True,
                          encoding="utf-8", env={**os.environ, "PYTHONUTF8": "1"})


def test_data_files_are_never_read(repo: Path):
    # 負の対照: data の中を読めば監査フックが止める
    control = _driver(repo, "control")
    assert control.returncode == 3 and "OPENED-IN-DATA" in control.stderr
    cp = _driver(repo, "build")
    assert cp.returncode == 0, cp.stderr
    data_md = (repo / CARDS / "data.md").read_text(encoding="utf-8")
    assert "`data/jinryu`" in data_md and "`data/jinryu/sub`" in data_md and "`data/odpt_rt/held`" in data_md
    assert "deep" not in data_md  # 深さは 2 段まで
    assert "sealed.csv" not in data_md and "README.md" not in data_md and "x.bin" not in data_md  # ディレクトリだけ
    for text in _snapshot(repo).values():
        assert DATA_CONTENT.encode("utf-8") not in text
    # 大きさは下の全部の合計(深さ 3 段より下を含む)
    one = len(DATA_CONTENT.encode("utf-8"))
    assert f"| `data/jinryu` | {one * 2} B |" in data_md
    assert f"| `data/jinryu/sub` | {one} B |" in data_md
    assert f"| `data` | {one * 4} B |" in data_md


def test_check_does_not_even_list_data(repo: Path):
    _run(repo)
    cp = _driver(repo, "check")
    assert cp.returncode == 0, cp.stderr


def test_data_size_uses_units(repo: Path):
    _write(repo, "data/big/x.bin", "x" * 2048)
    _run(repo)
    assert "| `data/big` | 2.0 KB |" in (repo / CARDS / "data.md").read_text(encoding="utf-8")


class _FakeEntry:
    """``os.DirEntry`` の代わり(リンクと stat の失敗を作る)。"""

    def __init__(self, name: str, path: str, *, link: bool = False, junction: bool = False, directory: bool = False,
                 size: int = 0, stat_fails: bool = False) -> None:
        self.name, self.path, self._link, self._junction = name, path, link, junction
        self._dir, self._size, self._stat_fails = directory, size, stat_fails

    def is_symlink(self) -> bool:
        return self._link

    def is_junction(self) -> bool:
        return self._junction

    def is_dir(self, *, follow_symlinks: bool = True) -> bool:
        if self._link or self._junction:
            return follow_symlinks
        return self._dir

    def stat(self, *, follow_symlinks: bool = True):
        if self._stat_fails:
            raise PermissionError(self.name)
        return types.SimpleNamespace(st_size=self._size)


class _FakeScan:
    def __init__(self, entries: list) -> None:
        self._entries = entries

    def __enter__(self):
        return iter(self._entries)

    def __exit__(self, *exc) -> bool:
        return False


def test_links_in_data_are_not_followed_or_sized(repo: Path, guide, monkeypatch):
    real = os.scandir
    base = str(repo / "data" / "jinryu")
    outside = os.path.join(base, "__link_target__")

    def fake(path):
        if str(path) == outside:
            return _FakeScan([_FakeEntry("huge.bin", os.path.join(outside, "huge.bin"), size=10**9)])
        if str(path) == base:
            with real(path) as it:
                entries = list(it)
            return _FakeScan(entries + [_FakeEntry("sym", outside, link=True, size=10**9),
                                        _FakeEntry("jun", outside, junction=True, size=10**9)])
        return real(path)

    monkeypatch.setattr(guide.os, "scandir", fake)
    rows, problems = guide.data_rows(repo)
    d = dict(rows)
    one = len(DATA_CONTENT.encode("utf-8"))
    assert d["data/jinryu"] == one * 2  # リンクの先も、リンクそのものの大きさも足さない
    assert d["data/jinryu/sym"] is None and d["data/jinryu/jun"] is None  # 一覧には「リンク」として名前だけ
    assert problems == []


def test_problems_stop_at_the_listed_dir_and_hide_deep_names(repo: Path, guide, monkeypatch):
    real = os.scandir
    deep = str(repo / "data" / "jinryu" / "sub" / "deep")
    held = str(repo / "data" / "odpt_rt" / "held")

    def fake(path):
        if str(path) == deep:
            return _FakeScan([_FakeEntry("hidden_name.csv", os.path.join(deep, "hidden_name.csv"), stat_fails=True)])
        if str(path) == held:
            raise PermissionError(path)
        return real(path)

    monkeypatch.setattr(guide.os, "scandir", fake)
    rows, problems = guide.data_rows(repo)
    assert problems == ["data", "data/jinryu", "data/jinryu/sub", "data/odpt_rt", "data/odpt_rt/held"]
    text = guide.R.render_data_index(rows, problems)
    assert "hidden_name" not in text and "deep" not in text


# ---------------------------------------------------------------- 伏せる語
def test_masks_words_of_both_checkers(repo: Path):
    _write(repo, "tools/leaky.py", f'"""説明に {SECRET_WORD} と {PATH_WORD} がある。"""\n')
    _write(repo, "docs/leaky.md", f"# 見出しの {SECRET_WORD}\n")
    cp = _run(repo)
    assert cp.returncode == 0, cp.stderr
    assert "伏せた語 3 件" in cp.stdout
    assert "説明に 〔伏〕 と 〔伏〕 がある。" in _block(_card(repo, "tools"), "leaky.py")
    assert "見出しの 〔伏〕" in (repo / CARDS / "docs.md").read_text(encoding="utf-8")
    for rel, data in _snapshot(repo).items():
        assert SECRET_WORD.encode() not in data and PATH_WORD.encode() not in data, rel
    assert _run(repo, "--check").returncode == 0  # 比べる側も同じ伏せ方


# ---------------------------------------------------------------- git の一覧
def test_git_listing_includes_untracked_and_reports_them(repo: Path, guide):
    if shutil.which("git") is None:
        pytest.skip("git が無い")
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    _write(repo, ".gitignore", "tools/ignored/\n")
    _write(repo, "tools/ignored/secret_scratch.py", '"""無視される。"""\n')
    subprocess.run(["git", "-C", str(repo), "add", "src", "tests", "tools"], check=True)  # tmp の合成のリポの索引だけ
    _write(repo, "tools/untracked_one.py", '"""未追跡でも載る。"""\n')
    cp = _run(repo)
    assert cp.returncode == 0, cp.stderr
    assert "未追跡 1 本を含む" in cp.stdout and "未追跡: tools/untracked_one.py" in cp.stdout
    tools_card = _card(repo, "tools")
    assert "untracked_one.py" in tools_card  # --others は残す(新しいファイルを見落とさない)
    assert "ignored" not in tools_card and not (repo / CARDS / "tools/ignored").exists()
    check = _run(repo, "--check")
    assert check.returncode == 0 and "未追跡 1 本を含む" in check.stdout and "未追跡: tools/untracked_one.py" in check.stdout
    # 一覧は sort 済み(git の出力の順に頼らない)
    listed = guide.list_files(repo, ("tools",))
    assert listed == sorted(listed) and "tools/untracked_one.py" in listed
    # 全部を追跡に入れれば知らせない
    subprocess.run(["git", "-C", str(repo), "add", "tools"], check=True)
    assert "未追跡" not in _run(repo, "--check").stdout


# ---------------------------------------------------------------- 本物のリポ: AST で読んだものと実物の import を比べる
@pytest.fixture(scope="module")
def real_code(guide):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # 対象のコードの SyntaxWarning
        return guide.CodeCards(REPO)


@pytest.fixture(scope="module")
def real_blocks(guide, real_code) -> dict[str, str]:
    """本物のリポのファイル → カードの節。"""
    cards = real_code.render()
    out: dict[str, str] = {}
    for d, card in real_code.dirs.items():
        text = cards[guide.R.card_path(d)]
        for rel in card.py_files:
            out[rel] = _block(text, rel.rsplit("/", 1)[-1])
    return out


def test_real_ledger_rows_match_import(real_code):
    from shibuya.engine import state_ledger as SL

    permits = real_code.permits
    assert permits.problems == []
    got = {r.key: (r.name, r.place, r.behavior, r.restore, r.arm, r.dead, r.items) for r in permits.rows}
    want = {r.key: (r.name, r.place, r.behavior, r.restore, r.arm, r.dead, r.items) for r in SL.LEDGER}
    assert got == want
    assert {k: (f"src/shibuya/{v[0]}", v[1]) for k, v in SL.OWNER_CLASSES.items()} == permits.owners
    assert {k: tuple((f"src/shibuya/{a}", b) for a, b in v) for k, v in SL.OWNER_ALT_CLASSES.items()} == permits.alts


def test_real_write_permits_match_import(real_code):
    from shibuya.engine.systems import allow as AL
    from shibuya.engine.systems import spec as SP
    from shibuya.engine.systems.table import SPECS, SYSTEMS

    permits = real_code.permits
    assert [s.name for s in permits.systems] == [s.name for s in SYSTEMS]
    for mine in permits.systems:
        spec = SPECS[mine.name]
        assert mine.group == spec.group and mine.timing == spec.timing and mine.when == spec.when
        assert mine.calls_llm == spec.calls_llm
        assert set(mine.resolve_ops) == set(spec.resolve_ops)
        assert set(mine.soa) == set(spec.writes.soa), mine.name
        assert set(mine.paths) == set(spec.writes.paths), mine.name
        assert set(mine.scratch) == set(spec.writes.scratch), mine.name
        assert set(mine.buffers) == set(spec.writes.buffers), mine.name
        assert set(mine.tally) == set(spec.writes.tally), mine.name
        assert (mine.fn_name, mine.fn_file) == (spec.fn.__name__, "src/" + spec.fn.__module__.replace(".", "/") + ".py"), mine.name
    ix = AL.index()
    assert {k: set(v) for k, v in permits.direct.items()} == {k: set(v) for k, v in ix.direct.items()}
    # 外の道筋の照合も実物の規則と同じ
    for r in permits.rows:
        for item in r.items:
            key = f"{r.key}:{item}"
            want = {s.name for s in SYSTEMS if SP.path_allowed(key, s.writes.paths)}
            assert permits.writers_of_item(r.key, item) == want, key


def _public_in_card(block: str) -> set[str]:
    return set(re.findall(r"^  - `(\w+)`\((?:関数|クラス)\)", block, flags=re.M))


def test_real_public_names_match_import(real_blocks):
    """公開の関数とクラス: カードと、実物を import した ``vars()`` を比べる(軽いモジュールの全部)。"""
    from shibuya.foundation import time_consts as CORE
    from shibuya.engine.systems import table as SYSTEMS

    from tests import _places as PL

    # 〔段 4 の下ごしらえ〕前は字面のディレクトリ src/shibuya/core/・src/shibuya/engine/systems/ の前方一致。元の置き場が
    # その 2 つの包みのファイルを対応表で引く(段 4 で core は無くなり、systems は別の包みへ移る)
    scope = {f"src/shibuya/{r}" for r in PL.rels_from(CORE, SYSTEMS)}
    checked = 0
    for rel in sorted(real_blocks):
        if rel not in scope or rel.endswith("__init__.py"):
            continue
        name = rel.removeprefix("src/").removesuffix(".py").replace("/", ".")
        mod = importlib.import_module(name)
        want = {n for n, o in vars(mod).items()
                if not n.startswith("_")
                and (inspect.isfunction(o) or inspect.isclass(o) or hasattr(o, "__wrapped__"))  # lru_cache で包んだ関数も入れる
                and getattr(o, "__module__", None) == name and getattr(o, "__name__", None) == n}
        assert want == _public_in_card(real_blocks[rel]), rel
        checked += 1
    assert checked >= 20


def _string_lines(tree: ast.Module) -> set[int]:
    """複数行の文字列の行(行の正規表現で読むときに外す)。"""
    lines: set[int] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.end_lineno != n.lineno:
            lines.update(range(n.lineno, n.end_lineno + 1))
    return lines


_LINE_IMPORT = re.compile(r"^\s*(?:from\s+(shibuya(?:\.\w+)*)\s+import\b|import\s+(shibuya(?:\.\w+)*))")
_LINE_ENV = re.compile(r"""os\.(?:environ\.get\(|getenv\(|environ\[)\s*["']([A-Z][A-Z0-9_]*)["']""")


def test_real_imports_and_env_match_line_regex(real_blocks):
    """import と環境変数: カードと、行の正規表現(AST を使わない別の読み方)を比べる(本物の全ファイル)。"""
    n_imports = n_env = 0
    for rel, block in sorted(real_blocks.items()):
        raw = (REPO / rel).read_bytes().decode("utf-8-sig").replace("\r\n", "\n")
        try:
            skip = _string_lines(ast.parse(raw))
        except SyntaxError:
            continue
        imp_line = next((x for x in block.split("\n") if x.startswith("- import している内部モジュール")), "")
        env_line = next((x for x in block.split("\n") if x.startswith("- 環境変数")), "")
        for i, line in enumerate(raw.split("\n"), 1):
            if i in skip:
                continue
            m = _LINE_IMPORT.match(line)
            if m:
                mod = m.group(1) or m.group(2)
                path = "src/" + mod.replace(".", "/")
                if f"{path}.py" in real_blocks or f"{path}/__init__.py" in real_blocks:
                    assert re.search(r"`" + re.escape(mod) + r"[.`]", imp_line), (rel, mod)
                    n_imports += 1
            code = line.split("#", 1)[0]
            if rel.startswith("tests/"):
                continue  # 試験は文字列の中に書くことがある
            for name in _LINE_ENV.findall(code):
                assert f"`{name}`" in env_line, (rel, name)
                n_env += 1
    assert n_imports > 1000 and n_env > 20


def test_real_bare_imports_are_resolved_or_marked(real_code, real_blocks):
    """tests と tools に同じ名が 1 つだけある素の import は、解けるか、カードに印が付く(H1 の再発の守り)。"""
    by_name: dict[str, list[str]] = {}
    for rel in real_code.py_files:
        if rel.startswith(("tests/", "tools/")):
            stem = rel.rsplit("/", 1)[-1].removesuffix(".py")
            if stem == "__init__":
                stem = rel.rsplit("/", 2)[-2]
            if stem != "conftest":
                by_name.setdefault(stem, []).append(rel)
    n = 0
    for rel in real_code.py_files:
        if not rel.startswith(("tests/", "tools/")):
            continue
        raw = (REPO / rel).read_bytes().decode("utf-8-sig").replace("\r\n", "\n")
        try:
            tree = ast.parse(raw)
        except SyntaxError:
            continue
        tops: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                tops.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                tops.add(node.module.split(".")[0])
        for top in sorted(tops):
            found = by_name.get(top, [])
            if top in sys.stdlib_module_names or top in ("tests", "tools") or len(found) != 1 or found[0] == rel:
                continue  # tests と tools の名はリポの根から解く
            target = found[0]
            edges = real_code.edges.imports.get(rel, set())
            resolved = target in edges or (target.endswith("/__init__.py") and any(
                e.startswith(target.removesuffix("__init__.py")) for e in edges))
            block = real_blocks[rel]
            marked = "解けない素の import" in block or "`sys.path` に足す先を読めない所" in block
            assert resolved or marked, (rel, top, target)
            n += 1
    assert n > 100


def test_real_known_edges_of_syspath_forms(real_code):
    """検収で落ちていた辺(ループの変数・``.parent.parent``・``parents[1]``・``ROOT / sub``)。"""
    importers = real_code.edges.importers
    assert "tools/c7/c7lib.py" in importers["tools/c6/c6lib.py"]  # for _p in (…): sys.path.insert(0, _p)
    assert {"tools/instruments/dm_eval/situations.py", "tools/instruments/leak_check/run.py",
            "tools/spatial/las_pointcloud_agg.py", "tests/tools/test_seal_split_337.py"} <= importers["tools/instruments/read_guard.py"]
    assert "tests/c7/test_attr_arms.py" in importers["tools/c7/attr_arms.py"]
    assert importers["tools/c8/ensemble.py"]
    assert "tools/realworld_fetch/rw_fetch_daily.py" in importers["tools/realworld_fetch/cli.py"]  # parents[1]
    assert "tests/tools/test_dm_eval.py" in importers["tools/instruments/dm_eval/__init__.py"]
    assert importers["tools/instruments/leak_check/__init__.py"]


def test_real_cards_have_no_link_shapes_in_text(real_code):
    span = re.compile(r"``.+?``|`[^`]*`")
    for path, text in real_code.render().items():
        for line in text.split("\n"):
            if line.startswith(("## [", "下のディレクトリ")):
                continue
            assert "](" not in span.sub("", line), (path, line[:120])


def test_real_item_numbers_are_attached_to_a_head(real_code):
    """``#N`` は接頭につながる形だけ(単独の ``#N`` は載せない)。"""
    n_attached = 0
    for f in real_code.facts.values():
        for i in f.decision_ids:
            assert not i.startswith("#"), (f.rel, i)
            n_attached += " #" in i
    assert n_attached > 30
    assert "第 275 #7" in real_code.facts["tests/llm/test_contract.py"].decision_ids
