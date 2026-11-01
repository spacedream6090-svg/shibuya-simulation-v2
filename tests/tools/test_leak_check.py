# -*- coding: utf-8 -*-
"""tools/instruments/leak_check(回答 11-01 §6・段 1 の 4 の漏洩の検査の器)の試験。

- 問いの集合: 書いてあるファイルが作り直しと同じ・件数(型 ① 20+10・型 ② 21 対 42 行・型 ④ 2)・時点の前後・
  対の 2 行の違いは名だけ・候補 3〜6・対象ごとに 5 場面以上・ブロックの並び・検証側の語を含まない・架空名は
  片仮名 3 音の無意味語(検収 M3)・実在の形を借りた架空の出来事が無い(L5)。
- 採点の既知の答え: JSD・1 位・名の確率・符号の検定・分布の読み(対数確率・下限・番号の正規化・本文)・型 ① の分類
  (「知らない」の言い回し 18 例=H1・否定と同意の言い回し=M1・「原因不明」の誤爆なし=L7)と具体名・other を除く率・
  型 ④ の正規化・最長共通部分列・完全一致・Glasserman & Lin 型の成績の差。
- 通し(mock): 3 型が cli で通る・参照が無いときは「未投入」・絶対の道筋が出ない・digest が同じ(L1)・台帳の 1 行に
  モデル名と版(Q3)・モデルの違う記録はまとめない。
- 既知の当て口: 名を見ない当て口で JSD 0・名を好む当て口で名の向きが正・参照を写す当て口で guided の完全一致 1・
  出所の混ざった対は別の集計(M2)。
- 入力: 実在の出来事の md5・md5 を渡してファイルが無いと止まる(M4)・前後は日で決まる(M5)・when の形(L6)・
  f で始まる id を拒む・封印とパターン台帳の道筋は開く前に落ちる(L8)・締め切りで前後を分ける(Q2)。
- cli の引数の検査(L2・型に関係の無い引数も rc 2)。英語の断りと英語の具体名の印(N1)・日本語の断りの追加(N2)・
  出来事の行があれば has(N5)・架空名はブランドの語だけを置き換える(N3)。vLLM: 送る形・API key はヘッダだけ・HTTP の失敗・思考の段を落とす・port の範囲。
- 守り: 禁じた語の名を使わない(keyword 引数・except の名・global/nonlocal も=L3・植えた名で落ちる負の対照つき)。
"""
from __future__ import annotations

import ast
import hashlib
import json
import math
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_INSTR = ROOT / "tools" / "instruments"
if str(_INSTR) not in sys.path:
    sys.path.insert(0, str(_INSTR))

import leak_check  # noqa: E402
from leak_check import backends as BK  # noqa: E402
from leak_check import cli as C  # noqa: E402
from leak_check import run as R  # noqa: E402
from leak_check import score as SC  # noqa: E402
from leak_check import sets as S  # noqa: E402
from read_guard import SealedPathError  # noqa: E402

PKG = ROOT / "tools" / "instruments" / "leak_check"
BANNED_WORDS = ("op" + "en", "t" + "ick")


# ---------------------------------------------------------------------- 問いの集合
def test_sets_on_disk_match_builders():
    for name, fn in S.BUILDERS.items():
        rows, md5 = S.load_set(name)
        assert rows == fn(), name
        assert md5 == S.lf_md5(S.to_jsonl(fn())), name


def test_type1_counts_and_sides():
    dates = S.build_type1_dates()
    assert len(dates) == 20
    assert sum(r["side"] == "pre" for r in dates) == 10 and sum(r["side"] == "post" for r in dates) == 10
    assert all((r["days_from_world"] < 0) == (r["side"] == "pre") for r in dates)
    assert len({r["qid"] for r in dates}) == 20 and len({r["date"] for r in dates}) == 20
    ev = S.build_type1_events()
    assert len(ev) == 10 and all(r["kind"] == "fictional" for r in ev)
    assert sum(r["side"] == "pre" for r in ev) == 5 and sum(r["side"] == "post" for r in ev) == 5
    assert S.side_of("2026-07") == "post" and S.side_of("2026-06") == "pre"
    assert S.side_of("2026-07-01") == "pre" and S.side_of("2026-07-14") == "post"
    with pytest.raises(ValueError):
        S.side_of(leak_check.WORLD_DATE)


def test_fictional_events_do_not_borrow_real_forms():
    texts = {eid: t for eid, _, t in S.FICTIONAL_EVENTS}
    assert "ハチ公" not in texts["f02"] and "ホーム" not in texts["f04"]  # 検収 L5 で差し替え
    assert not any("移設" in t or "移され" in t for t in texts.values())


def test_type2_pairs_differ_only_by_name():
    rows = S.build_type2()
    assert len(rows) == 42
    by: dict[str, dict[str, dict]] = {}
    for r in rows:
        by.setdefault(r["pair_id"], {})[r["variant"]] = r
    assert len(by) == 21
    groups: dict[str, int] = {}
    for pid, v in by.items():
        real, fict = v["real"], v["fictional"]
        groups[real["target_group"]] = groups.get(real["target_group"], 0) + 1
        _, rn, fn = S.TARGETS[real["target"]]
        assert real["name"] == rn and fict["name"] == fn
        assert 3 <= len(real["candidates"]) <= 6
        assert [c["id"] for c in real["candidates"]] == [c["id"] for c in fict["candidates"]]
        assert fict["input_text"].replace(fn, rn) == real["input_text"]
        assert [c["text"].replace(fn, rn) for c in fict["candidates"]] == [c["text"] for c in real["candidates"]]
        assert fn not in real["prompt"] and rn not in fict["prompt"]
        assert real["input_text"] != fict["input_text"]  # 名が場面の文に出る
        assert [c["mentions_name"] for c in real["candidates"]] == [c["mentions_name"] for c in fict["candidates"]]
        for c in real["candidates"]:
            assert c["mentions_name"] == (rn in c["text"])
        assert S.block_sequence(real["input_text"])[0] == "B1"
        for key in ("sid", "lang", "input_text", "input_missing", "facts", "strata"):  # dm_eval の行の形
            assert key in real
    assert groups == {"scramble_square": 5, "miyashita_park": 5, "halloween": 5, "shop": 6}


def test_fictional_names_keep_structure_and_swap_brand_only():
    fakes = [v[2] for v in S.TARGETS.values()]
    assert len(set(fakes)) == len(fakes)
    for key, (kind, real, swaps) in S.BRAND_SWAPS.items():
        fake = S.TARGETS[key][2]
        rest_real, rest_fake = real, fake
        for brand, word in swaps:  # ブランドの語だけが片仮名 3 音の無意味語に替わる(検収 N3)
            assert re.fullmatch(r"[ァ-ヶ]{3}", word), word
            assert real.count(brand) == 1 and brand not in fake and fake.count(word) == 1
            rest_real, rest_fake = rest_real.replace(brand, "□"), rest_fake.replace(word, "□")
        assert rest_real == rest_fake, key  # 構造の語(渋谷・の・店・本店・スクエア・PARK)は同じ
    assert S.TARGETS["shop_parco"][2] == "渋谷ソミラ" and S.TARGETS["shop_donki"][2] == "ネカリ渋谷本店"
    assert S.TARGETS["scramble_square"][2] == "渋谷ヨスリスクエア" and S.TARGETS["miyashita_park"][2] == "ルモテ PARK"
    for f in fakes:
        assert sum(f in g for g in fakes) == 1  # ほかの架空名の一部でない(置き換えの往復が壊れない)
    with pytest.raises(ValueError):
        S.fictional_name("渋谷渋谷", (("渋谷", "ソミラ"),))


def test_block_sequence_rules():
    assert S.block_sequence("[B1 a] x\n[B2 b] y\n[B2 c] z\n[B4b d] w") == ["B1", "B2", "B4b"]
    with pytest.raises(ValueError):
        S.block_sequence("[B3 a] x\n[B1 b] y")
    with pytest.raises(ValueError):
        S.block_sequence("[B1 a] x\n[B2 b] y\n[B1 c] z")
    with pytest.raises(ValueError):
        S.block_sequence("頭なし")


def test_type4_templates_have_no_reference_text():
    rows = S.build_type4()
    assert [r["template_id"] for r in rows] == ["guided", "general"]
    assert "{name}" in rows[0]["template"] and "{name}" not in rows[1]["template"]
    assert all("{prefix}" in r["template"] for r in rows)


def test_sets_carry_no_validation_side_words():
    words = ("validation", "holdout", "kddi", "jinryu", "boundary_counts", "anchors", "封印")
    for name in S.SET_NAMES:
        raw = (S.SETS_DIR / name).read_bytes().decode("utf-8").lower()
        assert not any(w in raw for w in words), name
    for p in sorted(PKG.glob("*.py")):  # 文字列の定数(説明の文を除く)に検証側の錨のファイルの名を持たない
        tree = ast.parse(p.read_text(encoding="utf-8"))
        docs = {id(n.body[0].value) for n in ast.walk(tree)
                if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body
                and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant)}
        consts = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)
                  and id(n) not in docs]
        assert not any("anchors_v0" in c or "anchors.json" in c for c in consts), p.name


# ---------------------------------------------------------------------- 採点の既知の答え
def test_distribution_tools_known_values():
    assert SC.jsd([0.5, 0.5], [0.5, 0.5]) == 0.0
    assert math.isclose(SC.jsd([1.0, 0.0], [0.0, 1.0]), 1.0)
    assert SC.top1([0.2, 0.4, 0.4]) == 2
    assert SC.name_mass([0.1, 0.6, 0.3], [False, True, True]) == pytest.approx(0.9)
    assert SC.name_mass([0.5, 0.5], [False, False]) is None
    assert SC.sign_test_p(5, 0) == pytest.approx(0.0625)
    assert SC.sign_test_p(3, 3) == 1.0
    assert SC.sign_test_p(0, 0) is None
    d = SC.choice_distribution("", {" 1": math.log(0.3), "1": math.log(0.1), "2": math.log(0.4), "x": 0.0}, 3)
    assert d["source"] == "logprobs" and d["p"] == pytest.approx([0.5, 0.5, 0.0]) and d["fallback"] is None
    assert d["coverage"] == pytest.approx(0.8)
    t = SC.choice_distribution("答えは ３ です", None, 4)
    assert t["source"] == "text" and t["p"] == [0.0, 0.0, 1.0, 0.0] and t["fallback"] == "no_logprobs"
    assert SC.choice_distribution("7", None, 4) is None
    assert SC.choice_distribution("なし", None, 4) is None


def test_choice_distribution_floor_and_token_forms():
    # 番号のトークンの形(「1.」「 2)」「３」)を取りこぼさない(検収 M2 (b))
    assert [SC.token_number(t) for t in ("1.", " 2)", "３", "4、", "x1", "12", "一")] == [1, 2, 3, 4, None, 12, None]
    d = SC.choice_distribution("", {"1.": math.log(0.5), "2": math.log(0.3)}, 3)
    assert d["p"] == pytest.approx([0.625, 0.375, 0.0])
    # 番号に乗った確率が下限より小さければ本文の答えで(検収 M2 (a))
    low = {"1": math.log(1e-4), "x": math.log(0.9)}
    f = SC.choice_distribution("3", low, 3)
    assert f["source"] == "text" and f["p"] == [0.0, 0.0, 1.0] and f["fallback"] == "below_floor"
    assert f["coverage"] == pytest.approx(1e-4)
    g = SC.choice_distribution("3", low, 3, min_mass=1e-5)
    assert g["source"] == "logprobs" and g["p"] == [1.0, 0.0, 0.0]


def test_summarize_pairs_known_values():
    pairs = [{"jsd": 0.0, "top1_same": True, "name_shift": 0.2, "coverage_real": 1.0, "coverage_fictional": 0.5},
             {"jsd": 1.0, "top1_same": False, "name_shift": -0.1, "coverage_real": None, "coverage_fictional": None},
             {"jsd": None, "top1_same": None, "name_shift": None}]
    s = SC.summarize_pairs(pairs)
    assert s["n_pairs"] == 3 and s["n_scored"] == 2
    assert s["jsd_mean"] == 0.5 and s["jsd_median"] == 0.5 and s["top1_agree"] == 0.5
    assert s["name_shift_mean"] == pytest.approx(0.05) and (s["name_shift_pos"], s["name_shift_neg"]) == (1, 1)
    assert s["coverage_mean"] == 0.75


#: 検収 H1 の 14 例+丁寧語の変種(どれも「知らない」=unknown)。
UNKNOWN_EXAMPLES = (
    "特に大きな出来事はありませんでした。", "特に出来事はありませんでした", "その日の出来事は存じ上げません。",
    "その日付の情報は持ち合わせていません。", "分かりかねます", "わかりかねます", "お答えできません。",
    "未来の日付のため、お答えできません。", "記録は見つかりません。", "思い当たりません。", "把握しておりません。",
    "データがありません", "記憶にありません", "I'm sorry, I don\u2019t know.",
    "I don't have information about that date.", "I'm not aware of any events.", "存じておりません",
    "承知しておりません", "お答えいたしかねます", "確認できておりません", "分からない", "「分からない」",
    "その日の情報はありません。", "不明です",
)


def test_type1_unknown_phrasings():
    for t in UNKNOWN_EXAMPLES:
        assert SC.classify_dates(t) == "unknown", t
        assert SC.event_lines(t, "unknown") == []  # 具体名の判定は unknown に掛けない
    assert SC.has_unknown("I DON\u2019T KNOW")


def test_type1_classifiers():
    assert SC.classify_dates("ある\n渋谷で催しがあった") == "has"
    assert SC.classify_dates("渋谷で祭りがあった") == "has"
    assert SC.classify_dates("渋谷で原因不明の停電があった") == "has"  # 「不明」の誤爆なし(L7)
    assert SC.classify_dates("あるかどうかは分かりません") == "unknown"
    assert SC.classify_dates("うーん") == "other"
    assert SC.classify_dates("") == "other"
    assert SC.classify_events("はい\n知っています") == "agree"
    for t in ("ハイ", "Yes, I know.", "はい、そうです", "知っています"):
        assert SC.classify_events(t) == "agree", t
    for t in ("いいえ", "No.", "聞いたことがありません。", "そのような事実はありません。", "起きていません。",
              "存在しません。", "そのような出来事はありませんでした"):
        assert SC.classify_events(t) == "deny", t
    for t in ("分からない", "存じ上げません。", "記憶にありません"):
        assert SC.classify_events(t) == "unknown", t
    assert SC.classify_events("聞いたことがあるような") == "other"
    assert SC.event_lines("ある\nA\nB", "has") == ["A", "B"]
    assert SC.event_lines("渋谷で祭り", "has") == ["渋谷で祭り"]
    assert SC.event_lines("いいえ\n聞いたことがない", "deny") == ["聞いたことがない"]


#: 検収 N1 の英語の断り(どれも unknown)。
EN_UNKNOWN_EXAMPLES = (
    "I cannot provide information about that date.", "I don't have information about events on that day.",
    "I'm not aware of any events in Shibuya on that date.", "There is no record of events on that date.",
    "I can't verify what happened on that date.", "I have no knowledge of events on that date.",
    "I'm unable to provide details about that date.", "Sorry, I do not know.",
    "That date is in the future, so I cannot answer.", "Nothing notable happened, as far as I can tell. I cannot confirm.",
)


def test_type1_english_refusals_and_marks():
    for t in EN_UNKNOWN_EXAMPLES:
        assert SC.classify_dates(t) == "unknown", t
        assert SC.event_lines(t, "unknown") == []
    assert len(EN_UNKNOWN_EXAMPLES) == 10
    assert SC.classify_dates("A Halloween parade was held in Shibuya.") == "has"
    assert SC.classify_dates("Crowds gathered at the crossing.") == "has"
    # 英語の印は大文字の固有名・月名・数字つきの地名だけ(ふつうの語は印にしない)
    assert not SC.has_specific_name("I cannot provide information about that date.")
    assert not SC.has_specific_name("There was an event in Shibuya, Tokyo.")
    assert SC.has_specific_name("Traffic stopped on Route 246.")
    assert SC.has_specific_name("On October 31 people gathered.")
    assert SC.has_specific_name("The Halloween crowd was large.")
    assert SC.has_specific_name("Ｈａｌｌｏｗｅｅｎ")


def test_type1_more_japanese_refusals_and_denials():
    for t in ("その日については情報を持っていません", "特定の出来事は記録されていません", "その日に関する知識がありません",
              "その日はまだ来ていません", "思いつきません", "特に目立った出来事は報じられていません"):
        assert SC.classify_dates(t) == "unknown", t
    for t in ("それは事実ではありません", "誤りです", "Nope", "nope, that did not happen"):
        assert SC.classify_events(t) == "deny", t


def test_type1_event_line_wins_over_hedge():
    t = "ハロウィンのイベントがあったと思いますが、詳細は分かりません"
    assert SC.classify_dates(t) == "has"  # 出来事の行があれば、断りを添えても has(検収 N5)
    assert SC.event_lines(t, "has") == [t]
    assert SC.classify_dates("その日は何も起きていません") == "unknown"  # 否定の節は出来事の行にしない
    assert SC.classify_dates("ある\nパレードがあった") == "has"


def test_summarize_type1_with_and_without_other():
    items = [{"cls": "agree", "specific": False}, {"cls": "deny", "specific": True},
             {"cls": "other", "specific": False}, {"cls": "agree", "specific": False}]
    s = SC.summarize_type1(items, ("agree", "deny", "unknown", "other"))
    assert s["n"] == 4 and s["n_excl_other"] == 3
    assert s["agree_rate"] == 0.5 and s["agree_rate_excl_other"] == pytest.approx(2 / 3)
    assert s["other_rate"] == 0.25 and "other_rate_excl_other" not in s and s["specific_rate"] == 0.25


def test_specific_name_marks():
    given = "2026年10月31日に東京の渋谷で起きた出来事"
    assert SC.has_specific_name("ハロウィンで交差点が混んだ", given)
    assert SC.has_specific_name("「渋谷灯籠」が開かれた", given)
    assert SC.has_specific_name("SHIBUYA SKY が混んだ", given)
    assert SC.has_specific_name("宮下公園で集会があった", given)
    assert not SC.has_specific_name("渋谷駅で大きなイベントがあった", given)  # 渋谷駅=問いから言える・イベント=一般語
    assert not SC.has_specific_name("渋谷で人が集まった", given)
    assert not SC.has_specific_name("ハチ公像が移された", "出来事: ハチ公像が移された")  # 問いの文の語は数えない


def test_recall_tools_known_values():
    assert SC.normalize_text("Ａ b、 C。") == "abc"
    assert SC.lcs_len("abcde", "ace") == 3 and SC.lcs_len("", "a") == 0
    assert SC.longest_common_substring("xxabcdyy", "zabcdz") == 4
    assert SC.exact_match("渋谷の、街は  広い。そして", "渋谷の街は広い")
    assert not SC.exact_match("渋谷", "")
    full = SC.recall_scores("あいうえおかきくけこ", "あいうえおかきくけこ")
    assert full["exact"] and full["lcs_recall"] == 1.0 and full["lcs_f1"] == 1.0
    none = SC.recall_scores("さしすせそ", "あいうえお")
    assert not none["exact"] and none["lcs_recall"] == 0.0 and none["lcs_f1"] == 0.0 and not none["partial"]
    ref = "あ" * 10 + "い" * 15
    half = SC.recall_scores("あ" * 10 + "う" * 15, ref)
    assert half["lcs_recall"] == pytest.approx(10 / 25) and not half["partial"]
    long_sub = SC.recall_scores("ん" + ref[:21], ref)
    assert long_sub["partial"] and not long_sub["exact"]


def test_performance_gap_known_values():
    assert SC.performance_gap({"a": [1, 0]}, {"a": [0, 1]}, None)["gap"] is None
    g = SC.performance_gap({"a": [1.0, 0.0]}, {"a": [0.5, 0.5]}, {"a": [1.0, 0.0]})
    assert g["status"] == "測った" and g["jsd_real"] == 0.0 and g["gap"] < 0  # 実名で人に近い


# ---------------------------------------------------------------------- 通し(mock)
def _cli(tmp_path: Path, t: int, *extra: str) -> dict:
    out = tmp_path / f"out{t}"
    assert C.main(["run", "--type", str(t), "--backend", "mock", "--out-dir", str(out), *extra]) == 0
    raw = (out / C.RESULT_NAME).read_text(encoding="utf-8")
    md = (out / C.TABLE_NAME).read_text(encoding="utf-8")
    for text in (raw, md):
        assert not C.ABS_PATH.search(text)
        assert str(tmp_path) not in text and str(Path.home()) not in text
    return json.loads(raw)


def test_cli_mock_three_types(tmp_path):
    none_ev = str(tmp_path / "absent_real.jsonl")
    none_ref = str(tmp_path / "absent_refs.jsonl")
    r1 = _cli(tmp_path, 1, "--real-events", none_ev)
    assert r1["inputs"]["real_events"]["status"] == R.NOT_LOADED
    assert r1["metrics"]["a_dates"]["pre"]["n"] == 10 and r1["metrics"]["a_dates"]["post"]["n"] == 10
    assert r1["metrics"]["b_events"]["fictional"]["all"]["n"] == 10
    assert r1["metrics"]["real_agree_rate"] == R.NOT_LOADED
    assert r1["metrics"]["real_minus_fictional_agree"] == R.NOT_LOADED
    assert r1["metrics"]["a_dates"]["by_cutoff"] is None
    assert r1["n_calls"] == 30 and "未投入" in r1["ledger_rule9"]["line"]
    r2 = _cli(tmp_path, 2)
    m2 = r2["metrics"]
    assert m2["primary_source"] == "logprobs" and m2["by_source"]["logprobs"]["n_pairs"] == 21
    assert m2["by_source"]["text"]["n_pairs"] == 0 and m2["by_source"]["mixed"]["n_pairs"] == 0
    assert set(m2["by_group"]) == {"scramble_square", "miyashita_park", "halloween", "shop"}
    assert m2["performance_gap"]["gap"] is None
    r4 = _cli(tmp_path, 4, "--recall-refs", none_ref)
    assert r4["metrics"]["status"] == R.NOT_LOADED and r4["ledger_rule9"]["parts"]["type4"] == "型④ 未投入"
    for r in (r1, r2, r4):
        assert r["schema"] == leak_check.SCHEMA and r["ledger_rule9"]["line"].startswith("疑い(モデル mock@mock-1): ")
        assert r["not_in_scope"].startswith("③")
        assert r["digest"] == R.digest_of(r)
    merged = R.merge_ledger([r1, r2, r4])
    assert merged["line"].startswith("疑い(モデル mock@mock-1): ")
    assert "型① 時点後" in merged["line"] and "型② [logprobs] JSD" in merged["line"] and "型④ 未投入" in merged["line"]
    assert "未測" not in merged["line"]
    other = dict(r2, ledger_rule9=dict(r2["ledger_rule9"], model="qwen3-8b@x"))
    with pytest.raises(ValueError):
        R.merge_ledger([r1, other])


def test_cli_summary(tmp_path, capsys):
    r1 = _cli(tmp_path, 1, "--real-events", str(tmp_path / "x.jsonl"))
    r2 = _cli(tmp_path, 2)
    assert r1 and r2
    capsys.readouterr()
    assert C.main(["summary", str(tmp_path / "out1" / C.RESULT_NAME), str(tmp_path / "out2" / C.RESULT_NAME)]) == 0
    line = capsys.readouterr().out.strip()
    assert line.startswith("疑い(モデル mock@mock-1): 型① ") and "型④ 未測" in line


def test_result_has_no_response_text(tmp_path):
    r = _cli(tmp_path, 1, "--real-events", str(tmp_path / "x.jsonl"))
    raw = json.dumps(r, ensure_ascii=False)
    for reply in BK.MockBackend.DATES_REPLIES + BK.MockBackend.EVENTS_REPLIES:
        for ln in reply.split("\n")[1:]:
            assert ln not in raw
    assert "出来事を挙げてください" not in raw


def test_mock_is_deterministic_and_digest_excludes_time(tmp_path):
    a = R.run_type2(BK.MockBackend("s"))
    b = R.run_type2(BK.MockBackend("s"))
    assert a["items"] == b["items"] and a["metrics"] == b["metrics"] and a["digest"] == b["digest"]
    assert "wall_s" in a and R.digest_of(dict(a, wall_s=999.0)) == a["digest"]  # 時間は digest の外(L1)
    c = R.run_type2(BK.MockBackend("other"))
    assert c["items"] != a["items"] and c["digest"] != a["digest"]


# ---------------------------------------------------------------------- 既知の当て口
def _cand_lines(prompt: str) -> list[str]:
    return [ln for ln in prompt.split("\n") if ln[:1].isdigit() and ". " in ln[:4]]


class _Fixed(BK.Backend):
    """名を見ない当て口: いつも番号 1 に 0.7・残りに均等。"""

    name = "fixed"

    def complete(self, prompt, *, kind, max_tokens, want_logprobs=False):
        k = len(_cand_lines(prompt))
        p = [0.7] + [0.3 / (k - 1)] * (k - 1)
        return BK.Reply("1", {str(i + 1): math.log(x) for i, x in enumerate(p)})


class _NameLover(BK.Backend):
    """名を好む当て口: 実名を含む候補に重みを寄せる(架空名は見分けない)。"""

    name = "name_lover"

    def complete(self, prompt, *, kind, max_tokens, want_logprobs=False):
        reals = [v[1] for v in S.TARGETS.values()]
        w = [5.0 if any(n in ln for n in reals) else 1.0 for ln in _cand_lines(prompt)]
        s = sum(w)
        return BK.Reply("1", {str(i + 1): math.log(x / s) for i, x in enumerate(w)})


class _HalfText(BK.Backend):
    """実名版だけ対数確率を返し、架空名版は本文だけ(出所の混ざった対を作る)。"""

    name = "half_text"

    def complete(self, prompt, *, kind, max_tokens, want_logprobs=False):
        reals = [v[1] for v in S.TARGETS.values()]
        if any(n in prompt for n in reals):
            return BK.Reply("1", {"1": math.log(0.6), "2": math.log(0.4)})
        return BK.Reply("2", None)


def test_type2_name_blind_backend_gives_zero():
    r = R.run_type2(_Fixed())
    m = r["metrics"]["by_source"]["logprobs"]
    assert m["jsd_mean"] == 0.0 and m["top1_agree"] == 1.0
    assert m["name_shift_mean"] == pytest.approx(0.0) and m["name_shift_pos"] == 0 and m["name_shift_neg"] == 0


def test_type2_name_loving_backend_shifts_toward_name():
    r = R.run_type2(_NameLover())
    m = r["metrics"]["by_source"]["logprobs"]
    assert m["jsd_mean"] > 0 and m["name_shift_mean"] > 0 and m["name_shift_neg"] == 0
    assert m["name_shift_pos"] == m["name_shift_n"] == 20  # 名を含む候補の無い 1 対(halloween-03)を除く
    assert m["name_shift_sign_p"] < 0.001
    assert "名の向き +" in r["ledger_rule9"]["parts"]["type2"]


def test_type2_mixed_sources_are_kept_apart():
    r = R.run_type2(_HalfText())
    m = r["metrics"]
    assert m["by_source"]["mixed"]["n_pairs"] == 21
    assert m["by_source"]["logprobs"]["n_pairs"] == 0 and m["by_source"]["text"]["n_pairs"] == 0
    assert m["primary_source"] is None and r["ledger_rule9"]["parts"]["type2"] == "型② 読めた対なし"
    assert m["performance_gap"]["n"] == 0
    assert all(p["source"] == "mixed" for p in r["items"])


def test_type2_below_floor_counted():
    class Low(BK.Backend):
        name = "low"

        def complete(self, prompt, *, kind, max_tokens, want_logprobs=False):
            return BK.Reply("2", {"1": math.log(1e-5), "x": math.log(0.99)})

    r = R.run_type2(Low(), limit=2)
    assert r["metrics"]["n_below_floor_variants"] == 4 and r["metrics"]["by_source"]["text"]["n_pairs"] == 2
    assert r["items"][0]["fallback_real"] == "below_floor"
    r2 = R.run_type2(Low(), limit=2, min_mass=1e-6)
    assert r2["metrics"]["n_below_floor_variants"] == 0 and r2["metrics"]["by_source"]["logprobs"]["n_pairs"] == 2


class _Copier(BK.Backend):
    """参照を写す当て口: guided の問いにだけ参照の続きを返す。"""

    name = "copier"

    def __init__(self, conts):
        self.conts = conts

    def complete(self, prompt, *, kind, max_tokens, want_logprobs=False):
        if "元の文章のとおりに" in prompt:
            for prefix, cont in self.conts:
                if prefix in prompt:
                    return BK.Reply(cont)
        return BK.Reply("まったく別の文。")


def test_type4_with_refs_known_answers(tmp_path):
    text = "これは試験のための架空の文章であり、どの公刊物にも載っていない。" * 6
    refs = tmp_path / "refs.jsonl"
    refs.write_bytes((json.dumps({"id": "x1", "name": "試験の文", "text": text}, ensure_ascii=False) + "\n"
                      + json.dumps({"id": "x2", "name": "別の文", "prefix": "あいうえお", "continuation": "かきくけこ"},
                                   ensure_ascii=False) + "\n").encode("utf-8"))
    conts = [(text[:64], text[64:192]), ("あいうえお", "かきくけこ")]
    r = R.run_type4(_Copier(conts), recall_refs=refs)
    m = r["metrics"]
    assert m["status"] == "測った" and r["inputs"]["recall_refs"]["status"] == R.LOADED
    assert m["by_template"]["guided"]["exact_rate"] == 1.0 and m["by_template"]["general"]["exact_rate"] == 0.0
    assert m["guided_minus_general"]["pos"] == 2 and m["guided_minus_general"]["lcs_recall_mean"] > 0.5
    assert r["inputs"]["recall_refs"]["md5"] == hashlib.md5(refs.read_bytes()).hexdigest()
    raw = json.dumps(r, ensure_ascii=False)
    assert "どの公刊物にも" not in raw and "かきくけこ" not in raw  # 参照の文を写さない
    assert r["ledger_rule9"]["parts"]["type4"].startswith("型④ 最長共通部分列の率 guided 1.00")


# ---------------------------------------------------------------------- 入力
def _real_file(tmp_path: Path, rows, name: str = "real.jsonl") -> Path:
    p = tmp_path / name
    p.write_bytes("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode("utf-8"))
    return p


def test_type1_real_events_mixed_and_md5(tmp_path):
    p = _real_file(tmp_path, [{"id": "r01", "when": "2020-07", "text": "試験の実在の欄 1"},
                              {"id": "r02", "when": "2026-08-01", "text": "試験の実在の欄 2"}])
    md5 = hashlib.md5(p.read_bytes()).hexdigest()
    r = R.run_type1(BK.MockBackend(), real_events=p, expected_md5=md5)
    info = r["inputs"]["real_events"]
    assert info["status"] == R.LOADED and info["md5"] == md5 and info["md5_match"] is True and info["n"] == 2
    b = r["metrics"]["b_events"]["real"]
    assert b["all"]["n"] == 2 and b["pre"]["n"] == 1 and b["post"]["n"] == 1
    disc = r["metrics"]["real_minus_fictional_agree"]
    fa = r["metrics"]["b_events"]["fictional"]["all"]["agree_rate"]
    assert disc["agree_rate"] == pytest.approx(b["all"]["agree_rate"] - fa)
    assert "agree_rate_excl_other" in disc
    kinds = [i["kind"] for i in r["items"]["b_events"]]
    assert kinds.count("real") == 2 and kinds.count("fictional") == 10
    assert "試験の実在の欄" not in json.dumps(r, ensure_ascii=False)
    with pytest.raises(R.InputMismatch):
        R.run_type1(BK.MockBackend(), real_events=p, expected_md5="0" * 32)


def test_type1_real_event_side_by_day(tmp_path):
    p = _real_file(tmp_path, [{"id": "r01", "when": "2026-07-01", "text": "x"},
                              {"id": "r02", "when": "2026-07", "text": "y"},
                              {"id": "r03", "when": "2026-07-20", "text": "z"}])
    r = R.run_type1(BK.MockBackend(), real_events=p)
    sides = {i["qid"]: i["side"] for i in r["items"]["b_events"] if i["kind"] == "real"}
    assert sides == {"t1b-r01": "pre", "t1b-r02": "post", "t1b-r03": "post"}  # 日付まであれば日で(M5)
    q = _real_file(tmp_path, [{"id": "r01", "when": leak_check.WORLD_DATE, "text": "x"}], "q.jsonl")
    with pytest.raises(R.InputMismatch):
        R.run_type1(BK.MockBackend(), real_events=q)


def test_expect_md5_with_missing_file_stops(tmp_path, capsys):
    missing = tmp_path / "missing.jsonl"
    with pytest.raises(R.InputMismatch):
        R.run_type1(BK.MockBackend(), real_events=missing, expected_md5="0" * 32)
    with pytest.raises(R.InputMismatch):
        R.run_type4(BK.MockBackend(), recall_refs=missing, expected_md5="0" * 32)
    out = tmp_path / "o"
    rc = C.main(["run", "--type", "1", "--backend", "mock", "--out-dir", str(out), "--real-events", str(missing),
                 "--expect-md5", "0" * 32])
    assert rc == 1 and not (out / C.RESULT_NAME).exists()
    assert "無い" in capsys.readouterr().err


def test_type1_mix_order_depends_on_seed(tmp_path):
    p = _real_file(tmp_path, [{"id": f"r{i:02d}", "when": "2021-01", "text": f"欄 {i}"} for i in range(5)])
    a = [i["qid"] for i in R.run_type1(BK.MockBackend(), real_events=p, seed="a")["items"]["b_events"]]
    b = [i["qid"] for i in R.run_type1(BK.MockBackend(), real_events=p, seed="b")["items"]["b_events"]]
    assert sorted(a) == sorted(b) and a != b


def test_type1_rejects_bad_real_rows(tmp_path):
    bad_rows = [
        [{"id": "f01", "when": "2020-07", "text": "x"}],     # f で始まる id
        [{"id": "r1", "when": "2020", "text": "x"}],         # 年だけ
        [{"id": "r1", "when": "2020-13", "text": "x"}],      # 月が 13(L6)
        [{"id": "r1", "when": "2021-02-30", "text": "x"}],   # 暦に無い日(L6)
        [{"id": "r1", "when": "令和2年7月", "text": "x"}],    # 数字でない形(L6)
        [{"id": "r1", "when": "2020-7", "text": "x"}],       # 月が 1 桁
        [{"id": "r1", "when": "2020-07", "text": ""}],       # 文が空
        [{"id": "r1", "when": "2020-07", "text": "x"}, {"id": "r1", "when": "2020-08", "text": "y"}],  # 重複
    ]
    for i, rows in enumerate(bad_rows):
        p = _real_file(tmp_path, rows, f"bad{i}.jsonl")
        with pytest.raises(R.InputMismatch):
            R.run_type1(BK.MockBackend(), real_events=p)


def test_model_cutoff_splits_sides(tmp_path):
    r = R.run_type1(BK.MockBackend(), real_events=tmp_path / "none.jsonl", model_cutoff="2025-06")
    a = r["metrics"]["a_dates"]["by_cutoff"]
    assert a["pre"]["before_cutoff"]["n"] == 5 and a["pre"]["after_cutoff"]["n"] == 5  # 2025-07-13 以後の 5 件
    assert a["post"]["before_cutoff"]["n"] == 0 and a["post"]["after_cutoff"]["n"] == 10
    fb = r["metrics"]["b_events"]["fictional"]["by_cutoff"]
    assert fb["pre"]["before_cutoff"]["n"] == 5 and fb["pre"]["after_cutoff"]["n"] == 0  # f01〜f05 は 2025-05 まで
    assert fb["post"]["after_cutoff"]["n"] == 5
    assert r["metrics"]["model_cutoff"] == "2025-06" and "締め切り 2025-06" in r["ledger_rule9"]["line"]
    assert R.cutoff_side("2025-06-30", "2025-06") == "before_cutoff"
    assert R.cutoff_side("2025-07", "2025-06") == "after_cutoff"
    assert R.cutoff_side("2025-06", "2025-06-15") == "after_cutoff"
    assert R.cutoff_side("2025-06-15", "2025-06-15") == "before_cutoff"
    with pytest.raises(R.InputMismatch):
        R.run_type1(BK.MockBackend(), real_events=tmp_path / "none.jsonl", model_cutoff="2025-99")


def test_sealed_and_ledger_paths_refused_before_reading(tmp_path):
    p = tmp_path / ("jin" + "ryu") / "real.jsonl"  # 存在しない=開く前に落ちることを見る
    with pytest.raises(SealedPathError):
        R.run_type1(BK.MockBackend(), real_events=p)
    with pytest.raises(SealedPathError):
        R.run_type4(BK.MockBackend(), recall_refs=tmp_path / "x_validation_anchors_v0.json")
    with pytest.raises(SealedPathError):
        R.run_type4(BK.MockBackend(), recall_refs=ROOT / "docs" / "design" / "v2-pattern-ledger.md")  # L8


def test_abs_path_check():
    for bad in ("C:\\Users\\x", "c:/x", "/Users/someone", "/home/someone", "\\\\server\\share\\"):
        with pytest.raises(C.AbsolutePathInRecord):
            C.check_no_abs_path(bad)
    C.check_no_abs_path('{"url": "http://127.0.0.1:8000/v1/chat/completions", "file": "real_events.jsonl"}')


def test_cli_argument_checks(tmp_path, capsys):
    base = ["run", "--backend", "mock", "--out-dir", str(tmp_path / "o")]
    bad = [
        ["--type", "2", "--limit", "0"], ["--type", "2", "--limit", "-1"],
        ["--type", "4", "--prefix-chars", "-5"], ["--type", "4", "--cont-chars", "0"],
        ["--type", "2", "--port", "99999"], ["--type", "2", "--port", "0"], ["--type", "2", "--min-mass", "0"],
        ["--type", "1", "--model-cutoff", "2025-13"],
        # 型に関係の無い引数(L2 の残り)
        ["--type", "2", "--expect-md5", "0" * 32], ["--type", "2", "--real-events", "x.jsonl"],
        ["--type", "2", "--recall-refs", "x.jsonl"], ["--type", "2", "--seed", "a"],
        ["--type", "4", "--model-cutoff", "2025-06"], ["--type", "4", "--min-mass", "0.1"],
        ["--type", "1", "--min-mass", "0.1"], ["--type", "1", "--recall-refs", "x.jsonl"],
        ["--type", "1", "--prefix-chars", "10"], ["--type", "2", "--cont-chars", "10"],
    ]
    for extra in bad:
        with pytest.raises(SystemExit) as e:
            C.main(base + extra)
        assert e.value.code == 2, extra
    with pytest.raises(SystemExit) as e:
        C.main(["run", "--type", "2", "--backend", "vllm", "--out-dir", str(tmp_path / "o")])
    assert e.value.code == 2 and "--model" in capsys.readouterr().err
    assert not (tmp_path / "o").exists()


# ---------------------------------------------------------------------- vLLM(transport を差し替え)
class _Transport:
    def __init__(self, status=200, content="2", logprobs=True):
        self.calls = []
        self.status = status
        self.content = content
        self.logprobs = logprobs

    def __call__(self, host, port, path, body, headers, timeout):
        self.calls.append({"host": host, "port": port, "path": path, "body": json.loads(body.decode("utf-8")),
                           "headers": dict(headers)})
        choice = {"message": {"content": self.content}}
        if self.logprobs:
            choice["logprobs"] = {"content": [{"token": "2", "logprob": -0.1, "top_logprobs": [
                {"token": "2", "logprob": math.log(0.6)}, {"token": "1", "logprob": math.log(0.3)},
                {"token": "x", "logprob": math.log(0.1)}]}]}
        return self.status, json.dumps({"choices": [choice]}).encode("utf-8")


def test_vllm_payload_and_headers(monkeypatch):
    monkeypatch.setenv("LEAK_TEST_KEY", "dummy-not-a-key")
    tr = _Transport(content="<think>考え</think>2")
    be = BK.VllmBackend("qwen3-8b", port=8123, key_env="LEAK_TEST_KEY", transport=tr, model_version="rev-a")
    rep = be.complete("問い", kind="choice", max_tokens=4, want_logprobs=True)
    assert rep.text == "2" and rep.top_logprobs["2"] == pytest.approx(math.log(0.6))
    c = tr.calls[0]
    assert c["host"] == "127.0.0.1" and c["port"] == 8123 and c["path"] == "/v1/chat/completions"
    body = c["body"]
    assert body["model"] == "qwen3-8b" and body["temperature"] == 0.0 and body["max_tokens"] == 4
    assert body["chat_template_kwargs"] == {"enable_thinking": False}
    assert body["logprobs"] is True and body["top_logprobs"] == BK.TOP_LOGPROBS
    assert c["headers"]["Authorization"] == "Bearer dummy-not-a-key"
    d = be.describe()
    assert d["api_key_set"] is True and "dummy-not-a-key" not in json.dumps(d)
    assert R.model_label(d) == "qwen3-8b@rev-a"
    be.complete("問い", kind="dates", max_tokens=8)
    assert "logprobs" not in tr.calls[1]["body"]


def test_vllm_without_key_and_failures(monkeypatch):
    monkeypatch.delenv("LEAK_TEST_KEY", raising=False)
    tr = _Transport()
    be = BK.VllmBackend("m", key_env="LEAK_TEST_KEY", transport=tr)
    be.complete("q", kind="events", max_tokens=8)
    assert "Authorization" not in tr.calls[0]["headers"]
    assert R.model_label(be.describe()) == "m@" + R.NO_VERSION
    with pytest.raises(BK.BackendError):
        BK.VllmBackend("m", transport=_Transport(status=500)).complete("q", kind="events", max_tokens=8)

    def broken(*a):
        return 200, b"not json"

    with pytest.raises(BK.BackendError):
        BK.VllmBackend("m", transport=broken).complete("q", kind="events", max_tokens=8)

    def down(*a):
        raise ConnectionRefusedError("x")

    with pytest.raises(BK.BackendError):
        BK.VllmBackend("m", transport=down).complete("q", kind="events", max_tokens=8)
    with pytest.raises(ValueError):
        BK.VllmBackend("")
    with pytest.raises(ValueError):
        BK.VllmBackend("m", port=70000)


def test_vllm_type2_through_transport(tmp_path):
    tr = _Transport()
    r = R.run_type2(BK.VllmBackend("m", transport=tr), limit=3)
    m = r["metrics"]["by_source"]["logprobs"]
    assert m["n_pairs"] == 3 and m["jsd_mean"] == 0.0 and m["coverage_mean"] == pytest.approx(0.9)
    assert len(tr.calls) == 6 and all(c["host"] == "127.0.0.1" for c in tr.calls)
    assert r["items"][0]["source"] == "logprobs"
    C.write_outputs(r, tmp_path / "v")
    assert not C.ABS_PATH.search((tmp_path / "v" / C.RESULT_NAME).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------- 守り
def _banned_identifiers(source: str) -> list[str]:
    """名(関数・クラス・引数・名前・属性・import の別名・keyword 引数・except の名・global/nonlocal)のうち禁じた語を含む物。"""
    found = []
    for node in ast.walk(ast.parse(source)):
        names: list[str] = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.append(node.name)
        elif isinstance(node, ast.Name):
            names.append(node.id)
        elif isinstance(node, ast.Attribute):
            names.append(node.attr)
        elif isinstance(node, ast.arg):
            names.append(node.arg)
        elif isinstance(node, ast.alias):
            names.append(node.asname or node.name)
        elif isinstance(node, ast.keyword) and node.arg:
            names.append(node.arg)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            names.append(node.name)
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            names.extend(node.names)
        found += [n for n in names if any(w in n.lower() for w in BANNED_WORDS)]
    return found


def test_identifier_names_avoid_banned_words():
    files = sorted(PKG.glob("*.py"))
    bad = {p.name: _banned_identifiers(p.read_text(encoding="utf-8")) for p in files}
    assert len(bad) == 6 and all(v == [] for v in bad.values()), bad
    assert _banned_identifiers(Path(__file__).read_text(encoding="utf-8")) == []


def test_identifier_check_catches_planted_names():
    src = (PKG / "score.py").read_text(encoding="utf-8")
    o, t = "op" + "en", "t" + "ick"
    planted = src + (
        f"\n\ndef {o}_gate({t}_count):\n    return {t}_count\n"
        f"\n\ndef g():\n    global {o}_flag\n    try:\n        f(x=1, {t}_kw=2)\n"
        f"    except ValueError as {o}_err:\n        pass\n"
        f"\n\ndef h():\n    {t}_v = 0\n\n    def i():\n        nonlocal {t}_v\n"
    )
    found = _banned_identifiers(planted)
    for name in (f"{o}_gate", f"{t}_count", f"{o}_flag", f"{t}_kw", f"{o}_err", f"{t}_v"):
        assert name in found, name
    assert _banned_identifiers(src) == []
