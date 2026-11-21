"""壁打ちの記録の索引の道具(tools/wallbounce_index.py・11-22 §3-1 の 3)。

見出しの行だけを拾う・ID と題と日付と状態に分ける(分けられない所は空のまま)・行の範囲・索引が最新か。
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _load():
    spec = importlib.util.spec_from_file_location("wallbounce_index", REPO / "tools" / "wallbounce_index.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


W = _load()


def test_split_heading_shapes():
    # 半角の括弧(記録の形)と全角の括弧のどちらでも、最後の括弧だけを日付と状態に分ける
    assert W.split_heading("2-4 会話を同じ世界で回せるか(11-03・題 5 は未決)") == ("2-4", "会話を同じ世界で回せるか", "11-03", "題 5 は未決")
    assert W.split_heading("2-3 列の構造(11-02〜03)") == ("2-3", "列の構造", "11-02〜03", "")
    assert W.split_heading("2-86 改版その 2(憲法の行)・その 3(11-20 夜)") == ("2-86", "改版その 2(憲法の行)・その 3", "11-20", "夜")
    assert W.split_heading("2-9 題(11-04・決定)") == ("2-9", "題", "11-04", "決定")
    # 日付で始まらない括弧・括弧なし・ID なしは、分けずに題へ(推し量らない)
    assert W.split_heading("2-36 4 問目(11-09)と、区切り") == ("2-36", "4 問目(11-09)と、区切り", "", "")
    assert W.split_heading("2-7 題(研究へ)") == ("2-7", "題(研究へ)", "", "")
    assert W.split_heading("題ごとの記録") == ("", "題ごとの記録", "", "")
    assert W.split_heading("1. ユーザーの意図") == ("1", "ユーザーの意図", "", "")


def test_rows_ranges_and_fences():
    text = "\n".join([
        "# 記録",            # 1(深さ 1 は拾わない)
        "",                  # 2
        "## 1. 原則",        # 3
        "- a",               # 4
        "",                  # 5
        "## 2. 題ごと",      # 6
        "### 2-1 最初(11-02)",  # 7
        "- b",               # 8
        "```",               # 9
        "### 囲みの中は拾わない",  # 10
        "```",               # 11
        "",                  # 12
        "### 2-2 次(11-03・決定)",  # 13
        "- c",               # 14
        "",                  # 15
        "---",               # 16
        "## 3. 未決",        # 17
        "- d",               # 18
    ]) + "\n"
    rows = W.rows_of(text)
    got = [(r["depth"], r["id"], r["start"], r["end"]) for r in rows]
    assert got == [(2, "1", 3, 4), (2, "2", 6, 14), (3, "2-1", 7, 11), (3, "2-2", 13, 14), (2, "3", 17, 18)]
    assert rows[3]["date"] == "11-03" and rows[3]["state"] == "決定"
    # CRLF でも同じ
    assert [(r["start"], r["end"]) for r in W.rows_of(text.replace("\n", "\r\n"))] == [(r["start"], r["end"]) for r in rows]


def test_render_and_check_on_a_small_repo(tmp_path: Path, monkeypatch):
    rel = "docs/reference/rec.md"
    (tmp_path / "docs/reference").mkdir(parents=True)
    (tmp_path / rel).write_bytes("# 記録\n\n## 2. 題\n### 2-1 a|b(11-02)\n- x\n".encode("utf-8"))
    monkeypatch.setattr(W, "RECORDS", ((rel, "記録 A", "保管用"),))
    assert W.main(["--check", "--root", str(tmp_path)]) == 1  # まだ無い
    assert W.main(["--root", str(tmp_path)]) == 0
    out = (tmp_path / W.OUT_REL).read_bytes()
    assert b"\r" not in out
    text = out.decode("utf-8")
    assert "| `2-1` | a/b | 11-02 |  | 4〜5 |" in text  # 表を壊す縦棒は置き換える
    assert "決定の見出し 1 本・節の見出し 1 本" in text and "(5 行)" in text
    assert W.main(["--check", "--root", str(tmp_path)]) == 0
    (tmp_path / rel).write_bytes("# 記録\n\n## 2. 題\n### 2-1 a(11-02)\n- x\n### 2-2 b(11-03)\n".encode("utf-8"))
    assert W.main(["--check", "--root", str(tmp_path)]) == 1  # 記録に足したら古い


def test_real_index_is_fresh_and_covers_every_record():
    """リポの索引が最新(記録を置き換えたら作り直す)。記録の決定の見出しの数と、索引の行の数が同じ。"""
    assert W.main(["--check"]) == 0
    index = (REPO / W.OUT_REL).read_text(encoding="utf-8")
    for rel, _name, _status in W.RECORDS:
        rows = W.rows_of((REPO / rel).read_bytes().decode("utf-8-sig"))
        ids = [r["id"] for r in rows if r["depth"] == 3]
        assert ids and len(ids) == len(set(ids)), "決定の ID が重なっている"
        for i in ids:
            assert f"| `{i}` |" in index
