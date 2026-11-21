# -*- coding: utf-8 -*-
"""tools/ci/check_lock.py(入っている版がロックと同じかを CI で確かめる・第348・返事その 9 §1 の 13)の試験。

- 偽の ``pip freeze`` の文で: 同じ=0・足りない・余る・版が違う=1(違いの行に名が出る)。
- 環境の印: Linux では ``colorama; sys_platform == "win32"`` の行を数えない・Windows では数える。名は正規化して比べる。
- ロックの形の誤り(``>=``・同じ名の重なり)=2。頭の行(``# pip==``・``# python==``)と入っている版が違う・行が無い=1。
- 本物のロック: 48 本・pyproject の直の依存(本体と dev)を全部含み下限を満たす・ci.yml の pip と Python の版が頭の行と同じ。
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest
from packaging.requirements import Requirement

ROOT = Path(__file__).resolve().parents[2]
CI_YML = ROOT / ".github" / "workflows" / "ci.yml"


def _load():
    spec = importlib.util.spec_from_file_location("_check_lock_under_test", ROOT / "tools" / "ci" / "check_lock.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


L = _load()

LINUX = {"sys_platform": "linux", "platform_system": "Linux", "os_name": "posix"}
WIN = {"sys_platform": "win32", "platform_system": "Windows", "os_name": "nt"}

LOCK_TEXT = """# 試験の偽のロック
# pip==26.2.1
# python==3.12.10
numpy==2.5.3
PyYAML==6.0.3
typing_extensions==4.16.0
colorama==0.4.6; sys_platform == "win32"
"""
FREEZE_SAME = "numpy==2.5.3\npyyaml==6.0.3\ntyping-extensions==4.16.0\n"


def _run(tmp_path: Path, freeze: str, *, lock: str = LOCK_TEXT, env=None, pip="26.2.1", py="3.12.10",
         capsys=None) -> tuple[int, str]:
    p = tmp_path / "lock.txt"
    p.write_text(lock, encoding="utf-8")
    code = L.main(["--lock", str(p)], freeze_text=freeze, pip_version=pip, python_version=py,
                  env=LINUX if env is None else env)
    out = capsys.readouterr().out if capsys is not None else ""
    return code, out


def test_same_is_0(tmp_path: Path, capsys):
    code, out = _run(tmp_path, FREEZE_SAME, capsys=capsys)
    assert code == 0, out
    assert "→ 同じ" in out and "colorama" in out  # 印で外れた行の名が出る


def test_missing_is_1(tmp_path: Path, capsys):
    code, out = _run(tmp_path, "numpy==2.5.3\npyyaml==6.0.3\n", capsys=capsys)
    assert code == 1, out
    assert "足りない(ロックにあるのに入っていない): typing_extensions==4.16.0" in out


def test_extra_is_1(tmp_path: Path, capsys):
    code, out = _run(tmp_path, FREEZE_SAME + "requests==2.0.0\n", capsys=capsys)
    assert code == 1, out
    assert "余る(入っているのにロックに無い): requests==2.0.0" in out


def test_other_version_is_1(tmp_path: Path, capsys):
    code, out = _run(tmp_path, FREEZE_SAME.replace("numpy==2.5.3", "numpy==2.6.0"), capsys=capsys)
    assert code == 1, out
    assert "版が違う: numpy: ロック 2.5.3・入っている 2.6.0" in out


def test_marker_line_counts_only_where_it_applies(tmp_path: Path, capsys):
    code, out = _run(tmp_path, FREEZE_SAME, env=WIN, capsys=capsys)  # Windows では colorama が要る
    assert code == 1 and "colorama==0.4.6" in out, out
    code, out = _run(tmp_path, FREEZE_SAME + "colorama==0.4.6\n", env=WIN, capsys=capsys)
    assert code == 0, out
    code, out = _run(tmp_path, FREEZE_SAME + "colorama==0.4.6\n", env=LINUX, capsys=capsys)  # Linux では余る
    assert code == 1 and "余る" in out, out


def test_editable_and_comment_lines_in_freeze_are_skipped():
    got = L.parse_freeze("# 注\n-e git+https://example.invalid/x.git@abc#egg=x\nNumPy==2.5.3\nfoo @ file:///x/foo.whl\n")
    assert got == {"numpy": "2.5.3", "foo": "@ file:///x/foo.whl"}


@pytest.mark.parametrize("bad", ["numpy>=2.1\n", "numpy==2.5.3\nNumPy==2.5.3\n", "numpy\n", "# pip==1\n# pip==2\n"])
def test_bad_lock_is_2(tmp_path: Path, capsys, bad):
    code, out = _run(tmp_path, FREEZE_SAME, lock=bad, capsys=capsys)
    assert code == 2, out


def test_head_lines_are_checked(tmp_path: Path, capsys):
    code, out = _run(tmp_path, FREEZE_SAME, pip="25.0.1", capsys=capsys)
    assert code == 1 and "頭の行と違う: pip: ロック 26.2.1・今 25.0.1" in out, out
    code, out = _run(tmp_path, FREEZE_SAME, py="3.12.16", capsys=capsys)
    assert code == 1 and "python: ロック 3.12.10・今 3.12.16" in out, out
    code, out = _run(tmp_path, FREEZE_SAME, lock=LOCK_TEXT.replace("# python==3.12.10\n", ""), capsys=capsys)
    assert code == 1 and "`# python==…` の行が無い" in out, out


# ================================================================== 本物のロック
def _real_lock():
    return L.parse_lock((ROOT / "requirements-lock.txt").read_text(encoding="utf-8"))


def test_real_lock_has_the_48_and_the_head_lines():
    lock = _real_lock()
    assert len(lock.lines) == 48
    assert set(lock.head) == {"pip", "python"}
    assert [ln.name for ln in lock.lines if ln.marker] == ["colorama"]
    assert L.compare(lock, {L.normalize(ln.name): ln.version for ln in lock.lines}, env=WIN)["missing"] == []


def test_real_lock_covers_the_direct_dependencies_of_pyproject():
    """pyproject.toml の直の依存(本体と dev)は全部ロックにあり、版が宣言(下限・固定)を満たす。"""
    import tomllib

    proj = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    pinned = {L.normalize(ln.name): ln.version for ln in _real_lock().lines}
    reqs = [Requirement(r) for r in [*proj["dependencies"], *proj["optional-dependencies"]["dev"]]]
    bad = []
    for r in reqs:
        v = pinned.get(L.normalize(r.name))
        if v is None or not r.specifier.contains(v, prereleases=True):
            bad.append(f"{r}: ロック {v}")
    assert not bad, "\n" + "\n".join(bad)


def test_ci_yml_uses_the_pip_and_python_of_the_lock_head():
    """ci.yml の 3 つの仕事の pip と Python の版は、ロックの頭の行と同じ(片方だけ上げると落ちる)。"""
    head = _real_lock().head
    text = CI_YML.read_text(encoding="utf-8")
    pips = re.findall(r"python -m pip install pip==(\S+)", text)
    pys = re.findall(r"python-version:\s*\"([^\"]+)\"", text)
    assert len(pips) == 3 and len(pys) == 3, f"pip {pips}・python {pys}"
    assert set(pips) == {head["pip"]} and set(pys) == {head["python"]}, f"pip {pips}・python {pys}・頭 {head}"
    assert text.count("python -m pip install -r requirements-lock.txt") == 3
    assert text.count("python tools/ci/check_lock.py") == 3
